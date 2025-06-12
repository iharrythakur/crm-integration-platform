# CRM Integration Platform

A full-stack web application that provides seamless integration with multiple CRM platforms including HubSpot, Airtable, and Notion. Built with FastAPI, React, and Redis.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-latest-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-latest-green.svg)

## 🌟 Features

- **Multiple CRM Integrations**

  - HubSpot integration for contacts, companies, and deals
  - Airtable integration for bases and tables
  - Notion integration for pages and databases

- **Secure Authentication**

  - OAuth2 implementation for all integrations
  - Secure token storage using Redis
  - Protected API endpoints

- **Modern Tech Stack**
  - FastAPI backend for high-performance APIs
  - React frontend for responsive UI
  - Redis for efficient caching
  - TypeScript for type safety

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- Redis server
- npm or yarn

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/iharryhakur/crm-integration-platform.git
   cd crm-integration-platform
   ```

2. **Backend Setup**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**

   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**
   - Copy `.env.example` to `.env` in the backend directory
   - Update the environment variables with your credentials:
     ```
     HUBSPOT_CLIENT_ID=your_client_id
     HUBSPOT_CLIENT_SECRET=your_client_secret
     AIRTABLE_CLIENT_ID=your_client_id
     AIRTABLE_CLIENT_SECRET=your_client_secret
     NOTION_CLIENT_ID=your_client_id
     NOTION_CLIENT_SECRET=your_client_secret
     REDIS_URL=your_redis_url
     ```

### Running the Application

1. **Start Redis Server**

   ```bash
   redis-server
   ```

2. **Start Backend Server**

   ```bash
   cd backend
   uvicorn main:app --reload
   ```

3. **Start Frontend Development Server**

   ```bash
   cd frontend
   npm start
   ```

4. Access the application at `http://localhost:3000`

## 📚 API Documentation

Once the backend server is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🛠️ Project Structure

```
├── backend/
│   ├── integrations/
│   │   ├── hubspot.py
│   │   ├── airtable.py
│   │   └── notion.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── integrations/
│   │   └── App.js
│   └── package.json
└── README.md
```

## 🔒 Security

- OAuth2 authentication for all integrations
- Secure credential storage in Redis
- CORS protection
- Environment variable management
- Input validation and sanitization

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Author

- Your Name - Harshdeep Singh

## 🙏 Acknowledgments

- FastAPI documentation
- React documentation
- Redis documentation
- HubSpot, Airtable, and Notion API documentation
