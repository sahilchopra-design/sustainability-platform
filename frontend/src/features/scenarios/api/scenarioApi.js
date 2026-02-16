/**
 * Scenario Analysis API Client
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Dashboard
export const getScenarioDashboard = () => api.get('/api/v1/scenarios/dashboard');

// Scenario Builder
export const buildScenario = (data) => api.post('/api/v1/scenarios/build', data);
export const listScenarios = (params) => api.get('/api/v1/scenarios/list', { params });
export const getScenario = (id) => api.get(`/api/v1/scenarios/${id}`);
export const compareScenarios = (data) => api.post('/api/v1/scenarios/compare', data);
export const batchCreateScenarios = (data) => api.post('/api/v1/scenarios/batch-create', data);

// Templates
export const getTemplates = () => api.get('/api/v1/scenarios/templates/list');
export const applyTemplate = (propertyId, templateName) => 
  api.post(`/api/v1/scenarios/templates/apply?base_property_id=${propertyId}&template_name=${templateName}`);

// Properties
export const getProperties = () => api.get('/api/v1/scenarios/properties');

// Sensitivity Analysis
export const analyzeSensitivity = (data) => api.post('/api/v1/sensitivity/analyze', data);
export const generateTornado = (data) => api.post('/api/v1/sensitivity/tornado', data);
export const generateSpider = (data) => api.post('/api/v1/sensitivity/spider', data);
export const getSensitivityPresets = () => api.get('/api/v1/sensitivity/presets');

// What-If Analysis
export const analyzeWhatIf = (data) => api.post('/api/v1/what-if/analyze', data);
export const getWhatIfParameters = () => api.get('/api/v1/what-if/parameters');

export default {
  getScenarioDashboard,
  buildScenario,
  listScenarios,
  getScenario,
  compareScenarios,
  batchCreateScenarios,
  getTemplates,
  applyTemplate,
  getProperties,
  analyzeSensitivity,
  generateTornado,
  generateSpider,
  getSensitivityPresets,
  analyzeWhatIf,
  getWhatIfParameters,
};
