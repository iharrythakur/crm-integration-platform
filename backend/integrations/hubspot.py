# slack.py

from fastapi import Request
import os
import json
import secrets
import base64
from fastapi import HTTPException
import httpx
import asyncio
from fastapi.responses import HTMLResponse
import time
from datetime import datetime
from dotenv import load_dotenv

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from integrations.integration_item import IntegrationItem

# HubSpot OAuth2 Configuration
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = ''

# Required scopes for HubSpot API access
SCOPES = [
    'crm.objects.contacts.read',
    'crm.objects.companies.read',
    'crm.objects.deals.read'
]

load_dotenv()


async def authorize_hubspot(user_id: str, org_id: str) -> str:
    """
    Initiates the HubSpot OAuth2 authorization flow.

    Args:
        user_id (str): The ID of the user initiating the authorization
        org_id (str): The organization ID

    Returns:
        str: The authorization URL to redirect the user to
    """
    # Generate state parameter for security
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = base64.urlsafe_b64encode(
        json.dumps(state_data).encode('utf-8')).decode('utf-8')

    # Store state in Redis for validation during callback
    await add_key_value_redis(
        f'hubspot_state:{org_id}:{user_id}',
        json.dumps(state_data),
        expire=600  # 10 minutes expiration
    )

    # Construct the authorization URL
    auth_url = (
        f'https://app.hubspot.com/oauth/authorize'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&scope={" ".join(SCOPES)}'
        f'&state={encoded_state}'
    )

    return auth_url


async def oauth2callback_hubspot(request: Request):
    """
    Handles the OAuth2 callback from HubSpot.
    Exchanges the authorization code for access tokens and stores them in Redis.

    Args:
        request (Request): The FastAPI request object containing the callback parameters

    Returns:
        HTMLResponse: A response that closes the popup window
    """
    # Check for errors in the callback
    if request.query_params.get('error'):
        raise HTTPException(
            status_code=400,
            detail=f"HubSpot OAuth error: {request.query_params.get('error_description')}"
        )

    # Get the authorization code and state from the callback
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')

    if not code or not encoded_state:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters: code or state"
        )

    # Decode and validate the state
    try:
        state_data = json.loads(base64.urlsafe_b64decode(
            encoded_state).decode('utf-8'))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state parameter: {str(e)}"
        )

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    # Verify the state matches what we stored
    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state or state_data.get('state') != json.loads(saved_state).get('state'):
        raise HTTPException(
            status_code=400,
            detail="State validation failed"
        )

    # Exchange the code for access tokens
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            response.raise_for_status()
            tokens = response.json()

            # Store the tokens in Redis
            await add_key_value_redis(
                f'hubspot_credentials:{org_id}:{user_id}',
                json.dumps(tokens),
                expire=3600  # 1 hour expiration
            )

            # Clean up the state
            await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')

            # Return HTML to close the popup window
            return HTMLResponse(content="""
                <html>
                    <script>
                        window.close();
                    </script>
                </html>
            """)

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code for tokens: {str(e)}"
            )


async def get_hubspot_credentials(user_id: str, org_id: str) -> dict:
    """
    Retrieves HubSpot credentials from Redis and validates them.
    If the access token is expired, attempts to refresh it using the refresh token.

    Args:
        user_id (str): The ID of the user
        org_id (str): The organization ID

    Returns:
        dict: The credentials containing access_token and refresh_token

    Raises:
        HTTPException: If no credentials are found or if token refresh fails
    """
    # Get credentials from Redis
    credentials_json = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials_json:
        raise HTTPException(
            status_code=400,
            detail="No HubSpot credentials found. Please reauthorize the integration."
        )

    credentials = json.loads(credentials_json)

    # Check if access token is expired
    if credentials.get('expires_in') and credentials.get('created_at'):
        current_time = int(time.time())
        if current_time >= credentials['created_at'] + credentials['expires_in']:
            # Access token is expired, try to refresh it
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'https://api.hubapi.com/oauth/v1/token',
                        data={
                            'grant_type': 'refresh_token',
                            'client_id': CLIENT_ID,
                            'client_secret': CLIENT_SECRET,
                            'refresh_token': credentials['refresh_token']
                        },
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded'
                        }
                    )
                    response.raise_for_status()
                    new_tokens = response.json()

                    # Update the credentials with new tokens
                    new_tokens['created_at'] = int(time.time())
                    await add_key_value_redis(
                        f'hubspot_credentials:{org_id}:{user_id}',
                        json.dumps(new_tokens),
                        expire=3600  # 1 hour expiration
                    )

                    return new_tokens

            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to refresh HubSpot token: {str(e)}"
                )

    return credentials


def parse_hubspot_datetime(dt_str):
    if not dt_str:
        return None
    try:
        # Remove 'Z' and parse as UTC
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1]
        # Handle microseconds if present
        if '.' in dt_str:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


async def create_integration_item_metadata_object(item: dict, item_type: str) -> IntegrationItem:
    """
    Creates an IntegrationItem object from a HubSpot CRM item.

    Args:
        item (dict): The HubSpot CRM item data
        item_type (str): The type of item (contact, company, or deal)

    Returns:
        IntegrationItem: Formatted integration item
    """
    item_id = str(item.get('id', ''))
    properties = item.get('properties', {})

    # Example: meaningful display name logic (customize as needed)
    if item_type == 'contact':
        name = f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(
        )
        if not name:
            name = properties.get('email', f"Contact {item_id}")
        email = properties.get('email')
        display_name = f"{name} ({email})" if email else name
    elif item_type == 'company':
        name = properties.get('name', f"Company {item_id}")
        domain = properties.get('domain')
        display_name = f"{name} ({domain})" if domain else name
    elif item_type == 'deal':
        name = properties.get('dealname', f"Deal {item_id}")
        amount = properties.get('amount')
        display_name = f"{name} (${amount})" if amount else name
    else:
        display_name = f"{item_type.capitalize()} {item_id}"

    integration_item = IntegrationItem(
        id=f"{item_id}_{item_type}",
        type=item_type,
        name=display_name,
        creation_time=parse_hubspot_datetime(item.get('createdAt')),
        last_modified_time=parse_hubspot_datetime(item.get('updatedAt')),
        url=None  # or your url logic
    )

    item_dict = integration_item.__dict__
    if item_type == 'contact':
        item_dict['phone'] = properties.get('phone')
        item_dict['email'] = properties.get('email')
    elif item_type == 'company':
        item_dict['phone'] = properties.get('phone')
        item_dict['domain'] = properties.get('domain')
    elif item_type == 'deal':
        item_dict['amount'] = properties.get('amount')
    return item_dict


async def get_items_hubspot(credentials: str) -> list[IntegrationItem]:
    """
    Fetches items from HubSpot CRM and formats them into IntegrationItem objects.

    Args:
        credentials (str): JSON string containing HubSpot credentials

    Returns:
        list[IntegrationItem]: List of formatted integration items

    Raises:
        HTTPException: If API calls fail or credentials are invalid
    """
    try:
        credentials = json.loads(credentials)
        access_token = credentials.get('access_token')

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials: missing access token"
            )

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        integration_items = []

        # Fetch contacts
        async with httpx.AsyncClient() as client:
            # Get contacts
            contacts_response = await client.get(
                'https://api.hubapi.com/crm/v3/objects/contacts',
                headers=headers,
                params={'limit': 100}
            )
            contacts_response.raise_for_status()
            contacts_data = contacts_response.json()

            for contact in contacts_data.get('results', []):
                integration_items.append(
                    await create_integration_item_metadata_object(contact, 'contact')
                )

            # Get companies
            companies_response = await client.get(
                'https://api.hubapi.com/crm/v3/objects/companies',
                headers=headers,
                params={'limit': 100}
            )
            companies_response.raise_for_status()
            companies_data = companies_response.json()

            for company in companies_data.get('results', []):
                integration_items.append(
                    await create_integration_item_metadata_object(company, 'company')
                )

            # Get deals
            deals_response = await client.get(
                'https://api.hubapi.com/crm/v3/objects/deals',
                headers=headers,
                params={'limit': 100}
            )
            deals_response.raise_for_status()
            deals_data = deals_response.json()

            for deal in deals_data.get('results', []):
                integration_items.append(
                    await create_integration_item_metadata_object(deal, 'deal')
                )

        return integration_items

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials format"
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch HubSpot data: {str(e)}"
        )
