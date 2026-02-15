/**
 * Carbon Redux Selectors
 */

import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectCarbonState = (state) => state.carbon;

export const selectPortfolios = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.portfolios?.items || []
);

export const selectPortfoliosLoading = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.portfolios?.loading || false
);

export const selectCurrentPortfolio = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.currentPortfolio?.data
);

export const selectPortfolioDashboard = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.currentPortfolio?.dashboard
);

export const selectDashboardLoading = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.currentPortfolio?.loading || false
);

export const selectScenarios = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.scenarios?.items || []
);

export const selectActiveScenarioId = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.scenarios?.activeId
);

export const selectActiveScenario = createSelector(
  [selectScenarios, selectActiveScenarioId],
  (scenarios, activeId) => {
    return scenarios.find((s) => s.id === activeId);
  }
);

export const selectCurrentCalculation = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.calculations?.current
);

export const selectCalculationLoading = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.calculations?.loading || false
);

export const selectCalculationError = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.calculations?.error
);

export const selectProjects = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.projects?.items || []
);

// Computed selectors
export const selectPortfolioTotals = createSelector(
  [selectPortfolioDashboard],
  (dashboard) => {
    if (!dashboard) return null;
    
    return {
      totalAnnualCredits: dashboard.summary?.total_annual_credits || 0,
      totalRiskAdjustedCredits: dashboard.summary?.total_risk_adjusted_credits || 0,
      averageQualityScore: dashboard.summary?.portfolio_quality_score || 0,
      totalNpv: dashboard.summary?.portfolio_npv_10yr_usd || 0,
      projectCount: dashboard.summary?.project_count || 0
    };
  }
);

export const selectProjectsByRisk = createSelector(
  [selectPortfolioDashboard],
  (dashboard) => {
    if (!dashboard?.projects) return { low: [], medium: [], high: [] };
    
    return {
      low: dashboard.projects.filter((p) => p.risk_level === 'Low'),
      medium: dashboard.projects.filter((p) => p.risk_level === 'Medium'),
      high: dashboard.projects.filter((p) => p.risk_level === 'High')
    };
  }
);

export const selectCalculationHistory = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.calculations?.history || []
);

export const selectUiState = createSelector(
  [selectCarbonState],
  (carbon) => carbon?.ui || {}
);
