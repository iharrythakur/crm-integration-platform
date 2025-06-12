import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                {loadedData && Array.isArray(loadedData) ? (
                    <TableContainer component={Paper} sx={{ mt: 2 }}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Type</TableCell>
                                    <TableCell>Email</TableCell>
                                    <TableCell>Domain</TableCell>
                                    <TableCell>Amount</TableCell>
                                    <TableCell>Created</TableCell>
                                    <TableCell>Last Modified</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {loadedData.map((item, idx) => (
                                    <TableRow key={item.id || idx}>
                                        <TableCell>{item.name}</TableCell>
                                        <TableCell>{item.type}</TableCell>
                                        <TableCell>{item.type === 'contact' ? item.email || '' : ''}</TableCell>
                                        <TableCell>{item.type === 'company' ? item.domain || '' : ''}</TableCell>
                                        <TableCell>{item.type === 'deal' ? item.amount || '' : ''}</TableCell>
                                        <TableCell>
                                            {item.creation_time
                                                ? new Date(item.creation_time).toLocaleString()
                                                : ''}
                                        </TableCell>
                                        <TableCell>
                                            {item.last_modified_time
                                                ? new Date(item.last_modified_time).toLocaleString()
                                                : ''}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                ) : (
                    <TextField
                        label="Loaded Data"
                        value={loadedData ? JSON.stringify(loadedData, null, 2) : ''}
                        sx={{mt: 2}}
                        InputLabelProps={{ shrink: true }}
                        multiline
                        minRows={6}
                        disabled
                    />
                )}
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{mt: 1}}
                    variant='contained'
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
}
