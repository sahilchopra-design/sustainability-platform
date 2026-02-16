/**
 * Real Estate Valuation API Service
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// API client with default config
const api = axios.create({
  baseURL: `${API_URL}/api/v1/valuation`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============ Dashboard ============

export const getDashboardKPIs = async () => {
  const { data } = await api.get('/dashboard');
  return data;
};

// ============ Properties ============

export const listProperties = async (params = {}) => {
  const { data } = await api.get('/properties', { params });
  return data;
};

export const getProperty = async (propertyId) => {
  const { data } = await api.get(`/properties/${propertyId}`);
  return data;
};

export const createProperty = async (propertyData) => {
  const { data } = await api.post('/properties', propertyData);
  return data;
};

// ============ Income Approach ============

export const calculateDirectCapitalization = async (inputs) => {
  const { data } = await api.post('/income/direct-capitalization', inputs);
  return data;
};

export const calculateDCF = async (inputs) => {
  const { data } = await api.post('/income/dcf', inputs);
  return data;
};

// ============ Cost Approach ============

export const calculateReplacementCost = async (inputs) => {
  const { data } = await api.post('/cost/replacement', inputs);
  return data;
};

export const getConstructionCosts = async (params = {}) => {
  const { data } = await api.get('/cost/construction-costs', { params });
  return data;
};

export const getLocationFactors = async () => {
  const { data } = await api.get('/cost/location-factors');
  return data;
};

// ============ Sales Comparison ============

export const calculateSalesComparison = async (inputs) => {
  const { data } = await api.post('/sales-comparison', inputs);
  return data;
};

export const listComparables = async (params = {}) => {
  const { data } = await api.get('/comparables', { params });
  return data;
};

export const getComparable = async (comparableId) => {
  const { data } = await api.get(`/comparables/${comparableId}`);
  return data;
};

export const createComparable = async (comparableData) => {
  const { data } = await api.post('/comparables', comparableData);
  return data;
};

// ============ Comprehensive Valuation ============

export const runComprehensiveValuation = async (inputs) => {
  const { data } = await api.post('/comprehensive', inputs);
  return data;
};

// ============ Market Data ============

export const getMarketCapRates = async (params = {}) => {
  const { data } = await api.get('/market/cap-rates', { params });
  return data;
};

export const getMapData = async (params = {}) => {
  const { data } = await api.get('/map-data', { params });
  return data;
};

export default {
  getDashboardKPIs,
  listProperties,
  getProperty,
  createProperty,
  calculateDirectCapitalization,
  calculateDCF,
  calculateReplacementCost,
  getConstructionCosts,
  getLocationFactors,
  calculateSalesComparison,
  listComparables,
  getComparable,
  createComparable,
  runComprehensiveValuation,
  getMarketCapRates,
  getMapData,
};
