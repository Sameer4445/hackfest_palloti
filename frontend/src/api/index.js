import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const submitApplication = async (data) => {
  const response = await api.post('/predict', data);
  return response.data;
};

export const getHistory = async () => {
  const response = await api.get('/history');
  return response.data;
};

export const getAdminApplications = async () => {
  const response = await api.get('/admin/applications');
  return response.data;
};

export const getAdminStats = async () => {
  const response = await api.get('/admin/stats');
  return response.data;
};

// Auth calls go to /auth (not /api)
const authApi = axios.create({ baseURL: '/auth', headers: { 'Content-Type': 'application/json' } });

export const registerUser = async (data) => {
  const response = await authApi.post('/register', data);
  return response.data;
};

export const loginUser = async (data) => {
  const response = await authApi.post('/login', data);
  return response.data;
};
