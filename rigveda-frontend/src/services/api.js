import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchEntities = async () => {
  try {
    const response = await api.get('/entities/');
    return response.data;
  } catch (error) {
    console.error('Error fetching entities:', error);
    throw error;
  }
};

export const fetchEntityDetails = async (entityId) => {
  try {
    const response = await api.get(`/entities/${entityId}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching entity details:', error);
    throw error;
  }
};

export const fetchEntityRelationships = async (entityId) => {
  try {
    const response = await api.get(`/entities/${entityId}/relationships/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching relationships:', error);
    throw error;
  }
};

export const searchEntities = async (query) => {
  try {
    const response = await api.post('/entities/search/', { query });
    return response.data;
  } catch (error) {
    console.error('Error searching entities:', error);
    throw error;
  }
};

export const fetchStats = async () => {
  try {
    const response = await api.get('/stats/');
    return response.data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw error;
  }
};

export default api;
