import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

// Portfolios
export const getPortfolios = () => api.get('/api/pg/portfolios');
export const getPortfolio = (id) => api.get(`/api/pg/portfolios/${id}`);
export const createPortfolio = (data) => api.post('/api/pg/portfolios', data);
export const updatePortfolio = (id, data) => api.put(`/api/pg/portfolios/${id}`, data);
export const deletePortfolio = (id) => api.delete(`/api/pg/portfolios/${id}`);
export const addAssetToPortfolio = (portfolioId, asset) =>
  api.post(`/api/pg/portfolios/${portfolioId}/assets`, { asset });
export const removeAssetFromPortfolio = (portfolioId, assetId) =>
  api.delete(`/api/pg/portfolios/${portfolioId}/assets/${assetId}`);

// Scenario Data
export const getScenarioData = () => api.get('/api/scenario-data');
export const refreshScenarioData = (force = false) =>
  api.post('/api/scenario-data/refresh', { force });

// Analysis
export const runAnalysis = (data) => api.post('/api/analysis/run', data);
export const getAnalysisRuns = (portfolioId = null) => {
  const params = portfolioId ? `?portfolio_id=${portfolioId}` : '';
  return api.get(`/api/analysis/runs${params}`);
};
export const getAnalysisRun = (runId) => api.get(`/api/analysis/runs/${runId}`);
export const deleteAnalysisRun = (runId) => api.delete(`/api/analysis/runs/${runId}`);

// Sample Data
export const generateSampleData = () => api.post('/api/sample-data/generate');
