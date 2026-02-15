/**
 * Carbon Credits API Client
 * Handles all API calls for the carbon module
 */

import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const carbonApi = axios.create({
  baseURL: `${API_URL}/api/v1/carbon`,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor
carbonApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('session_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
carbonApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[Carbon API Error]', error.response?.data);
    return Promise.reject(error);
  }
);

// ============ Methodologies ============

export const fetchMethodologies = async (params) => {
  const response = await carbonApi.get('/methodologies', { params });
  return response.data;
};

// ============ Emission Factors ============

export const fetchEmissionFactors = async (countryCode, year) => {
  const response = await carbonApi.get('/emission-factors', {
    params: { country_code: countryCode, year }
  });
  return response.data;
};

// ============ Portfolios ============

export const fetchPortfolios = async (params = {}) => {
  const response = await carbonApi.get('/portfolios', { params });
  return response.data;
};

export const fetchPortfolio = async (id) => {
  const response = await carbonApi.get(`/portfolios/${id}`);
  return response.data;
};

export const fetchPortfolioDashboard = async (id) => {
  const response = await carbonApi.get(`/portfolios/${id}/dashboard`);
  return response.data;
};

export const createPortfolio = async (data) => {
  const response = await carbonApi.post('/portfolios', data);
  return response.data;
};

export const updatePortfolio = async (id, data) => {
  const response = await carbonApi.put(`/portfolios/${id}`, data);
  return response.data;
};

export const deletePortfolio = async (id) => {
  const response = await carbonApi.delete(`/portfolios/${id}`);
  return response.data;
};

// ============ Projects ============

export const fetchProjects = async (params = {}) => {
  const response = await carbonApi.get('/projects', { params });
  return response.data;
};

export const fetchProject = async (id) => {
  const response = await carbonApi.get(`/projects/${id}`);
  return response.data;
};

export const createProject = async (data) => {
  const response = await carbonApi.post('/projects', data);
  return response.data;
};

export const updateProject = async (id, data) => {
  const response = await carbonApi.put(`/projects/${id}`, data);
  return response.data;
};

export const deleteProject = async (id) => {
  const response = await carbonApi.delete(`/projects/${id}`);
  return response.data;
};

// ============ Scenarios ============

export const fetchScenarios = async (portfolioId) => {
  const response = await carbonApi.get(`/portfolios/${portfolioId}/scenarios`);
  return response.data;
};

export const createScenario = async (portfolioId, data) => {
  const response = await carbonApi.post(`/portfolios/${portfolioId}/scenarios`, data);
  return response.data;
};

export const deleteScenario = async (portfolioId, scenarioId) => {
  const response = await carbonApi.delete(`/portfolios/${portfolioId}/scenarios/${scenarioId}`);
  return response.data;
};

// ============ Calculations ============

export const calculateCarbonCredits = async (request) => {
  const response = await carbonApi.post('/calculate', request);
  return response.data;
};

export const fetchCalculation = async (calculationId) => {
  const response = await carbonApi.get(`/calculations/${calculationId}`);
  return response.data;
};

// ============ Reports ============

export const generateReport = async (params) => {
  const response = await carbonApi.post('/reports/generate', params);
  return response.data;
};

export const downloadReport = async (reportId) => {
  const response = await carbonApi.get(`/reports/${reportId}/download`, {
    responseType: 'blob'
  });
  return response.data;
};

export default carbonApi;
