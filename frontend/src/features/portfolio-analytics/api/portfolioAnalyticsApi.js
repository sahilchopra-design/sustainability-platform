/**
 * Portfolio Analytics API Client
 * Handles all API calls for portfolio aggregation and reporting
 */

const API_URL = process.env.REACT_APP_BACKEND_URL;
const BASE = `${API_URL}/api/v1/portfolio-analytics`;

/**
 * List all portfolios with optional filtering
 */
export async function fetchPortfolios(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', params.page);
  if (params.page_size) searchParams.set('page_size', params.page_size);
  if (params.portfolio_type) searchParams.set('portfolio_type', params.portfolio_type);
  if (params.strategy) searchParams.set('strategy', params.strategy);
  
  const url = `${BASE}/portfolios?${searchParams.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch portfolios');
  return res.json();
}

/**
 * Get single portfolio by ID
 */
export async function fetchPortfolio(portfolioId) {
  const res = await fetch(`${BASE}/portfolios/${portfolioId}`);
  if (!res.ok) throw new Error('Failed to fetch portfolio');
  return res.json();
}

/**
 * Create new portfolio
 */
export async function createPortfolio(data) {
  const res = await fetch(`${BASE}/portfolios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create portfolio');
  return res.json();
}

/**
 * Update portfolio
 */
export async function updatePortfolio(portfolioId, data) {
  const res = await fetch(`${BASE}/portfolios/${portfolioId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update portfolio');
  return res.json();
}

/**
 * Get holdings for a portfolio
 */
export async function fetchHoldings(portfolioId) {
  const res = await fetch(`${BASE}/portfolios/${portfolioId}/holdings`);
  if (!res.ok) throw new Error('Failed to fetch holdings');
  return res.json();
}

/**
 * Get portfolio analytics
 */
export async function fetchAnalytics(portfolioId, params = {}) {
  const searchParams = new URLSearchParams();
  if (params.scenario_id) searchParams.set('scenario_id', params.scenario_id);
  if (params.time_horizon) searchParams.set('time_horizon', params.time_horizon);
  if (params.as_of_date) searchParams.set('as_of_date', params.as_of_date);
  
  const url = `${BASE}/portfolios/${portfolioId}/analytics?${searchParams.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}

/**
 * Compare scenarios for portfolio
 */
export async function compareScenarios(portfolioId, data) {
  const res = await fetch(`${BASE}/portfolios/${portfolioId}/scenarios/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to compare scenarios');
  return res.json();
}

/**
 * Get portfolio dashboard data
 */
export async function fetchDashboard(portfolioId, params = {}) {
  const searchParams = new URLSearchParams();
  if (params.scenario_id) searchParams.set('scenario_id', params.scenario_id);
  if (params.time_horizon) searchParams.set('time_horizon', params.time_horizon);
  
  const url = `${BASE}/portfolios/${portfolioId}/dashboard?${searchParams.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
}

/**
 * Generate report for portfolio
 */
export async function generateReport(portfolioId, data) {
  const res = await fetch(`${BASE}/portfolios/${portfolioId}/reports/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to generate report');
  return res.json();
}

/**
 * Get report by ID
 */
export async function fetchReport(reportId) {
  const res = await fetch(`${BASE}/reports/${reportId}`);
  if (!res.ok) throw new Error('Failed to fetch report');
  return res.json();
}

/**
 * Get available enum values
 */
export async function fetchEnums() {
  const res = await fetch(`${BASE}/enums`);
  if (!res.ok) throw new Error('Failed to fetch enums');
  return res.json();
}

/**
 * Seed sample data
 */
export async function seedSampleData() {
  const res = await fetch(`${BASE}/seed-sample-data`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to seed sample data');
  return res.json();
}


// ── PCAF / WACI — Real Financed Emissions ────────────────────────────────────

/**
 * Trigger a PCAF Standard v2.0 financed emissions calculation.
 * Loads assets from assets_pg, resolves DQS hierarchy, calls PCAFWACIEngine,
 * writes to pcaf_time_series, fires alert engine.
 */
export async function runPCAFCalculation(portfolioId) {
  const res = await fetch(`${BASE}/${portfolioId}/pcaf-run`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'PCAF calculation failed');
  }
  return res.json();
}

/**
 * Get the latest cached PCAF results from pcaf_time_series.
 * Runs engine on-demand if no cache exists.
 */
export async function fetchPCAFResults(portfolioId) {
  const res = await fetch(`${BASE}/${portfolioId}/pcaf-results`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch PCAF results');
  }
  return res.json();
}

/**
 * Get year-by-year WACI vs. glidepath history for sparkline charts.
 */
export async function fetchWACIHistory(portfolioId, years = 10) {
  const res = await fetch(`${BASE}/${portfolioId}/waci-history?years=${years}`);
  if (!res.ok) throw new Error('Failed to fetch WACI history');
  return res.json();
}
