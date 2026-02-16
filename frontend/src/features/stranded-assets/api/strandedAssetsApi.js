import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const api = axios.create({
  baseURL: `${API_URL}/api/v1/stranded-assets`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const getDashboardKPIs = async () => {
  const response = await api.get('/dashboard');
  return response.data;
};

// Reserves
export const getReserves = async (params = {}) => {
  const response = await api.get('/reserves', { params });
  return response.data;
};

export const getReserveById = async (id) => {
  const response = await api.get(`/reserves/${id}`);
  return response.data;
};

export const createReserve = async (data) => {
  const response = await api.post('/reserves', data);
  return response.data;
};

// Power Plants
export const getPowerPlants = async (params = {}) => {
  const response = await api.get('/power-plants', { params });
  return response.data;
};

export const getPowerPlantById = async (id) => {
  const response = await api.get(`/power-plants/${id}`);
  return response.data;
};

export const createPowerPlant = async (data) => {
  const response = await api.post('/power-plants', data);
  return response.data;
};

// Infrastructure
export const getInfrastructure = async (params = {}) => {
  const response = await api.get('/infrastructure', { params });
  return response.data;
};

export const getInfrastructureById = async (id) => {
  const response = await api.get(`/infrastructure/${id}`);
  return response.data;
};

export const createInfrastructure = async (data) => {
  const response = await api.post('/infrastructure', data);
  return response.data;
};

// Calculations
export const calculateReserveImpairment = async (data) => {
  const response = await api.post('/calculate/reserve-impairment', data);
  return response.data;
};

export const calculatePowerPlantValuation = async (data) => {
  const response = await api.post('/calculate/power-plant-valuation', data);
  return response.data;
};

export const calculateInfrastructureValuation = async (data) => {
  const response = await api.post('/calculate/infrastructure-valuation', data);
  return response.data;
};

// Technology Disruption
export const getTechnologyDisruption = async (metricType, params = {}) => {
  const response = await api.get(`/technology-disruption/${metricType}`, { params });
  return response.data;
};

// Transition Pathways
export const getTransitionPathways = async (params = {}) => {
  const response = await api.get('/transition-pathways', { params });
  return response.data;
};

export const getTransitionPathwayById = async (id) => {
  const response = await api.get(`/transition-pathways/${id}`);
  return response.data;
};

// Scenario Comparison
export const runScenarioComparison = async (data) => {
  const response = await api.post('/scenario-comparison', data);
  return response.data;
};

// Critical Assets
export const getCriticalAssets = async (params = {}) => {
  const response = await api.get('/critical-assets', { params });
  return response.data;
};

// Portfolio Analysis
export const runPortfolioAnalysis = async (data) => {
  const response = await api.post('/portfolio-analysis', data);
  return response.data;
};

// Map Data
export const getMapData = async (params = {}) => {
  const response = await api.get('/map-data', { params });
  return response.data;
};

// Scenarios
export const getScenarios = async () => {
  const response = await api.get('/scenarios');
  return response.data;
};

export const getScenarioById = async (id) => {
  const response = await api.get(`/scenarios/${id}`);
  return response.data;
};

export default {
  getDashboardKPIs,
  getReserves,
  getReserveById,
  createReserve,
  getPowerPlants,
  getPowerPlantById,
  createPowerPlant,
  getInfrastructure,
  getInfrastructureById,
  createInfrastructure,
  calculateReserveImpairment,
  calculatePowerPlantValuation,
  calculateInfrastructureValuation,
  getTechnologyDisruption,
  getTransitionPathways,
  getTransitionPathwayById,
  runScenarioComparison,
  getCriticalAssets,
  runPortfolioAnalysis,
  getMapData,
  getScenarios,
  getScenarioById,
};
