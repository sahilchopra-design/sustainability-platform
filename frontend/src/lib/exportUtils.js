/**
 * Universal Export Utility for all modules
 * Provides PDF and Excel export functionality
 */

import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const exportApi = axios.create({
  baseURL: `${API_URL}/api/v1/exports`,
  responseType: 'blob',
});

/**
 * Download a blob as a file
 */
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Get file extension from format
 */
const getExtension = (format) => format === 'excel' ? 'xlsx' : 'pdf';

/**
 * Export portfolio analytics report
 */
export const exportPortfolioAnalytics = async (portfolioId, format = 'pdf', reportType = 'executive') => {
  const response = await exportApi.get(
    `/portfolio-analytics/${portfolioId}?format=${format}&report_type=${reportType}`
  );
  const filename = `portfolio_analytics_${portfolioId.slice(0, 8)}.${getExtension(format)}`;
  downloadFile(response.data, filename);
  return response;
};

/**
 * Export sustainability assessment
 */
export const exportSustainabilityAssessment = async (data, format = 'pdf', assessmentType = 'breeam') => {
  const response = await exportApi.post(
    `/sustainability/assessment?format=${format}&assessment_type=${assessmentType}`,
    data
  );
  const filename = `${assessmentType}_assessment.${getExtension(format)}`;
  downloadFile(response.data, filename);
  return response;
};

/**
 * Export stranded assets analysis
 */
export const exportStrandedAssets = async (data, format = 'pdf') => {
  const response = await exportApi.post(
    `/stranded-assets/analysis?format=${format}`,
    data
  );
  const filename = `stranded_asset_analysis.${getExtension(format)}`;
  downloadFile(response.data, filename);
  return response;
};

/**
 * Export scenario analysis/comparison
 */
export const exportScenarioAnalysis = async (data, format = 'pdf') => {
  const response = await exportApi.post(
    `/scenario-analysis/comparison?format=${format}`,
    data
  );
  const filename = `scenario_comparison.${getExtension(format)}`;
  downloadFile(response.data, filename);
  return response;
};

/**
 * Export nature risk assessment
 */
export const exportNatureRisk = async (data, format = 'pdf') => {
  const response = await exportApi.post(
    `/nature-risk/assessment?format=${format}`,
    data
  );
  const filename = `nature_risk_assessment.${getExtension(format)}`;
  downloadFile(response.data, filename);
  return response;
};

/**
 * Export real estate valuation
 */
export const exportValuation = async (data, format = 'pdf', valuationType = 'dcf') => {
  const response = await exportApi.post(
    `/valuation/analysis?format=${format}&valuation_type=${valuationType}`,
    data
  );
  const filename = `${valuationType}_valuation.${getExtension(format)}`;
  downloadFile(response.data, filename);
  return response;
};

/**
 * Export carbon calculation
 */
export const exportCarbonCalculation = async (data, format = 'pdf') => {
  const response = await exportApi.post(
    `/carbon/calculation?format=${format}`,
    data
  );
  const filename = `carbon_calculation.${getExtension(format)}`;
  downloadFile(response.data, filename);
  return response;
};

export default {
  downloadFile,
  exportPortfolioAnalytics,
  exportSustainabilityAssessment,
  exportStrandedAssets,
  exportScenarioAnalysis,
  exportNatureRisk,
  exportValuation,
  exportCarbonCalculation,
};
