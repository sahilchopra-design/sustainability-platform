/**
 * Universal Export Utility for all modules
 * Provides PDF and Excel export functionality.
 * When the backend is unavailable, falls back to a client-side JSON download
 * so the export action always succeeds in demo/offline mode.
 */

import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const exportApi = axios.create({
  baseURL: `${API_URL}/api/v1/exports`,
  responseType: 'blob',
});

/**
 * Fallback: download data as JSON when the backend export API is unreachable.
 */
function fallbackJsonDownload(data, filenameBase) {
  const content = JSON.stringify({ ...data, _exportMode: 'offline_fallback', exportDate: new Date().toISOString() }, null, 2);
  const blob = new Blob([content], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${filenameBase}_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Wrap an export API call with an offline fallback.
 */
async function withFallback(apiFn, fallbackData, filenameBase) {
  try {
    return await apiFn();
  } catch (err) {
    const isNetworkError = !err.response;
    if (isNetworkError) {
      fallbackJsonDownload(fallbackData, filenameBase);
      return { _fallback: true };
    }
    throw err;
  }
}

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
  return withFallback(
    async () => {
      const response = await exportApi.get(`/portfolio-analytics/${portfolioId}?format=${format}&report_type=${reportType}`);
      downloadFile(response.data, `portfolio_analytics_${portfolioId.slice(0, 8)}.${getExtension(format)}`);
      return response;
    },
    { portfolioId, format, reportType },
    'portfolio_analytics'
  );
};

/**
 * Export sustainability assessment
 */
export const exportSustainabilityAssessment = async (data, format = 'pdf', assessmentType = 'breeam') => {
  return withFallback(
    async () => {
      const response = await exportApi.post(`/sustainability/assessment?format=${format}&assessment_type=${assessmentType}`, data);
      downloadFile(response.data, `${assessmentType}_assessment.${getExtension(format)}`);
      return response;
    },
    data,
    `${assessmentType}_assessment`
  );
};

/**
 * Export stranded assets analysis
 */
export const exportStrandedAssets = async (data, format = 'pdf') => {
  return withFallback(
    async () => {
      const response = await exportApi.post(`/stranded-assets/analysis?format=${format}`, data);
      downloadFile(response.data, `stranded_asset_analysis.${getExtension(format)}`);
      return response;
    },
    data,
    'stranded_asset_analysis'
  );
};

/**
 * Export scenario analysis/comparison
 */
export const exportScenarioAnalysis = async (data, format = 'pdf') => {
  return withFallback(
    async () => {
      const response = await exportApi.post(`/scenario-analysis/comparison?format=${format}`, data);
      downloadFile(response.data, `scenario_comparison.${getExtension(format)}`);
      return response;
    },
    data,
    'scenario_comparison'
  );
};

/**
 * Export nature risk assessment
 */
export const exportNatureRisk = async (data, format = 'pdf') => {
  return withFallback(
    async () => {
      const response = await exportApi.post(`/nature-risk/assessment?format=${format}`, data);
      downloadFile(response.data, `nature_risk_assessment.${getExtension(format)}`);
      return response;
    },
    data,
    'nature_risk_assessment'
  );
};

/**
 * Export real estate valuation
 */
export const exportValuation = async (data, format = 'pdf', valuationType = 'dcf') => {
  return withFallback(
    async () => {
      const response = await exportApi.post(`/valuation/analysis?format=${format}&valuation_type=${valuationType}`, data);
      downloadFile(response.data, `${valuationType}_valuation.${getExtension(format)}`);
      return response;
    },
    data,
    `${valuationType}_valuation`
  );
};

/**
 * Export carbon calculation
 */
export const exportCarbonCalculation = async (data, format = 'pdf') => {
  return withFallback(
    async () => {
      const response = await exportApi.post(`/carbon/calculation?format=${format}`, data);
      downloadFile(response.data, `carbon_calculation.${getExtension(format)}`);
      return response;
    },
    data,
    'carbon_calculation'
  );
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
