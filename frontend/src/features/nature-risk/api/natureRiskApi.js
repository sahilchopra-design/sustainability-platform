/**
 * Nature Risk API Service
 * Handles all API calls for the Nature Risk module
 */

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const natureRiskApi = {
  // Scenarios
  getScenarios: async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${API_URL}/api/v1/nature-risk/scenarios${queryString ? `?${queryString}` : ''}`);
    if (!response.ok) throw new Error('Failed to fetch scenarios');
    return response.json();
  },

  getScenario: async (scenarioId) => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/scenarios/${scenarioId}`);
    if (!response.ok) throw new Error('Failed to fetch scenario');
    return response.json();
  },

  // LEAP Assessments
  calculateLEAPAssessment: async (data) => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/leap-assessments/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to calculate LEAP assessment');
    return response.json();
  },

  // ENCORE
  getENCORESectors: async () => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/encore/sectors`);
    if (!response.ok) throw new Error('Failed to fetch ENCORE sectors');
    return response.json();
  },

  getENCOREDependencies: async (sectorCode) => {
    const url = sectorCode 
      ? `${API_URL}/api/v1/nature-risk/encore/dependencies?sector_code=${sectorCode}`
      : `${API_URL}/api/v1/nature-risk/encore/dependencies`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch ENCORE dependencies');
    return response.json();
  },

  getEcosystemServices: async () => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/encore/ecosystem-services`);
    if (!response.ok) throw new Error('Failed to fetch ecosystem services');
    return response.json();
  },

  // Water Risk
  getWaterRiskLocations: async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${API_URL}/api/v1/nature-risk/water-risk/locations${queryString ? `?${queryString}` : ''}`);
    if (!response.ok) throw new Error('Failed to fetch water risk locations');
    return response.json();
  },

  analyzeWaterRisk: async (data) => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/water-risk/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to analyze water risk');
    return response.json();
  },

  getWaterRiskReport: async (locationId, scenarioId) => {
    const url = scenarioId
      ? `${API_URL}/api/v1/nature-risk/water-risk/locations/${locationId}/risk-report?scenario_id=${scenarioId}`
      : `${API_URL}/api/v1/nature-risk/water-risk/locations/${locationId}/risk-report`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch water risk report');
    return response.json();
  },

  // Biodiversity
  getBiodiversitySites: async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${API_URL}/api/v1/nature-risk/biodiversity/sites${queryString ? `?${queryString}` : ''}`);
    if (!response.ok) throw new Error('Failed to fetch biodiversity sites');
    return response.json();
  },

  calculateBiodiversityOverlaps: async (data) => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/biodiversity/overlaps/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to calculate biodiversity overlaps');
    return response.json();
  },

  // Portfolio
  analyzePortfolioNatureRisk: async (data) => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/portfolio/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to analyze portfolio nature risk');
    return response.json();
  },

  getPortfolioNatureExposure: async (portfolioId, scenarioId) => {
    const url = scenarioId
      ? `${API_URL}/api/v1/nature-risk/portfolio/${portfolioId}/nature-exposure?scenario_id=${scenarioId}`
      : `${API_URL}/api/v1/nature-risk/portfolio/${portfolioId}/nature-exposure`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch portfolio nature exposure');
    return response.json();
  },

  // GBF Alignment
  getGBFTargets: async () => {
    const response = await fetch(`${API_URL}/api/v1/nature-risk/gbf-targets`);
    if (!response.ok) throw new Error('Failed to fetch GBF targets');
    return response.json();
  },

  getGBFAlignment: async (entityType, entityId, reportingYear) => {
    const url = reportingYear
      ? `${API_URL}/api/v1/nature-risk/gbf-alignment/${entityType}/${entityId}?reporting_year=${reportingYear}`
      : `${API_URL}/api/v1/nature-risk/gbf-alignment/${entityType}/${entityId}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch GBF alignment');
    return response.json();
  },

  // Dashboard
  getDashboardSummary: async (portfolioId) => {
    const url = portfolioId
      ? `${API_URL}/api/v1/nature-risk/dashboard/summary?portfolio_id=${portfolioId}`
      : `${API_URL}/api/v1/nature-risk/dashboard/summary`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch dashboard summary');
    return response.json();
  },

  // Reports
  generateTNFDDisclosure: async (entityId, entityType, reportingYear) => {
    const response = await fetch(
      `${API_URL}/api/v1/nature-risk/reports/tnfd-disclosure?entity_id=${entityId}&entity_type=${entityType}&reporting_year=${reportingYear}`,
      { method: 'POST' }
    );
    if (!response.ok) throw new Error('Failed to generate TNFD disclosure');
    return response.json();
  },
};

export default natureRiskApi;
