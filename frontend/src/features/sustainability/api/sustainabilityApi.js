/**
 * Sustainability Frameworks API Client
 * Handles GRESB, LEED, BREEAM, and value impact analysis
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const api = axios.create({
  baseURL: `${API_URL}/api/v1/sustainability`,
  headers: { 'Content-Type': 'application/json' },
});

// Dashboard
export const getDashboard = () => api.get('/dashboard');

// Certifications
export const getCertifications = (params) => api.get('/certifications', { params });
export const getCertification = (id) => api.get(`/certifications/${id}`);
export const createCertification = (data) => api.post('/certifications', data);

// GRESB Assessment
export const calculateGRESB = (data) => api.post('/gresb/assess', data);
export const getGRESBBenchmarks = (region) => api.get('/gresb/benchmarks', { params: { region } });

// LEED Assessment
export const calculateLEED = (data) => api.post('/leed/assess', data);
export const getLEEDThresholds = () => api.get('/leed/thresholds');

// BREEAM Assessment
export const calculateBREEAM = (data) => api.post('/breeam/assess', data);
export const getBREEAMWeights = () => api.get('/breeam/weights');

// Value Impact
export const calculateValueImpact = (data) => api.post('/value-impact', data);
export const getBenchmarks = (params) => api.get('/benchmarks', { params });

// Portfolio Analysis
export const analyzePortfolio = (data) => api.post('/portfolio/analyze', data);

// Comparison Tool
export const compareCertifications = (data) => api.post('/compare', data);

// Enums
export const getEnums = () => api.get('/enums');

// Export API (uses different base URL)
const exportApi = axios.create({
  baseURL: `${API_URL}/api/v1/exports`,
  headers: { 'Content-Type': 'application/json' },
  responseType: 'blob',
});

export const exportSustainabilityAssessment = (data, format = 'pdf', assessmentType = 'breeam') => 
  exportApi.post(`/sustainability/assessment?format=${format}&assessment_type=${assessmentType}`, data);

export const exportCertifications = (format = 'excel') => 
  exportApi.get(`/sustainability/certifications?format=${format}`);

// Helper function to trigger download
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default {
  getDashboard,
  getCertifications,
  getCertification,
  createCertification,
  calculateGRESB,
  getGRESBBenchmarks,
  calculateLEED,
  getLEEDThresholds,
  calculateBREEAM,
  getBREEAMWeights,
  calculateValueImpact,
  getBenchmarks,
  analyzePortfolio,
  compareCertifications,
  getEnums,
  exportSustainabilityAssessment,
  exportCertifications,
  downloadFile,
};
