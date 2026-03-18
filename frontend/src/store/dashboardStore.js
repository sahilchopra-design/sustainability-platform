import { create } from 'zustand';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useDashboardStore = create((set, get) => ({
  // Portfolio state
  portfolios: [],
  selectedPortfolio: null,
  portfolioLoading: false,
  
  // Scenario state
  scenarios: [],
  selectedScenarios: [],
  selectedHorizons: [2030, 2040, 2050],
  scenariosLoading: false,
  
  // Analysis state
  analysisRunning: false,
  analysisProgress: 0,
  analysisResults: null,
  analysisError: null,
  
  // Holdings/counterparty state
  holdings: [],
  holdingsLoading: false,
  
  // Metrics state
  metrics: null,
  metricsLoading: false,

  // GAP-003 — Seed-data transparency flags
  // isFallback: true when a calculation call failed and synthetic seed data was returned
  // apiReachable: whether the last health-check / API call succeeded
  isFallback: false,
  apiReachable: false,

  // Actions - Portfolios
  fetchPortfolios: async () => {
    set({ portfolioLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/pg/portfolios`);
      const data = await res.json();
      set({ portfolios: data.portfolios || [], portfolioLoading: false, apiReachable: true });
    } catch (error) {
      console.error('Failed to fetch portfolios:', error);
      set({ portfolioLoading: false, apiReachable: false });
    }
  },

  selectPortfolio: async (portfolio) => {
    set({ selectedPortfolio: portfolio });
    if (portfolio) {
      get().fetchPortfolioMetrics(portfolio.id);
      get().fetchHoldings(portfolio.id);
    }
  },

  // Actions - Scenarios
  fetchScenarios: async () => {
    set({ scenariosLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/scenarios?published_only=true`);
      const data = await res.json();
      set({ scenarios: data || [], scenariosLoading: false });
    } catch (error) {
      console.error('Failed to fetch scenarios:', error);
      set({ scenariosLoading: false });
    }
  },

  toggleScenario: (scenarioId) => {
    const { selectedScenarios } = get();
    if (selectedScenarios.includes(scenarioId)) {
      set({ selectedScenarios: selectedScenarios.filter(id => id !== scenarioId) });
    } else {
      set({ selectedScenarios: [...selectedScenarios, scenarioId] });
    }
  },

  setSelectedScenarios: (scenarioIds) => {
    set({ selectedScenarios: scenarioIds });
  },

  setSelectedHorizons: (horizons) => {
    set({ selectedHorizons: horizons });
  },

  // Actions - Metrics
  fetchPortfolioMetrics: async (portfolioId) => {
    set({ metricsLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/pg/portfolios/${portfolioId}`);
      const data = await res.json();
      
      // Calculate metrics from portfolio data
      const assets = data.assets || [];
      const totalExposure = assets.reduce((sum, a) => sum + (a.exposure || 0), 0);
      const avgPD = assets.length > 0 
        ? assets.reduce((sum, a) => sum + (a.base_pd || 0), 0) / assets.length 
        : 0;
      const avgLGD = assets.length > 0 
        ? assets.reduce((sum, a) => sum + (a.base_lgd || 0), 0) / assets.length 
        : 0;
      const expectedLoss = totalExposure * avgPD * avgLGD;
      
      // Sector breakdown
      const sectorBreakdown = assets.reduce((acc, asset) => {
        const sector = asset.company?.sector || 'Unknown';
        acc[sector] = (acc[sector] || 0) + (asset.exposure || 0);
        return acc;
      }, {});

      // Geographic breakdown
      const geoBreakdown = assets.reduce((acc, asset) => {
        const country = asset.company?.country || 'Unknown';
        acc[country] = (acc[country] || 0) + (asset.exposure || 0);
        return acc;
      }, {});

      // Rating breakdown
      const ratingBreakdown = assets.reduce((acc, asset) => {
        const rating = asset.rating || 'NR';
        acc[rating] = (acc[rating] || 0) + (asset.exposure || 0);
        return acc;
      }, {});

      set({ 
        metrics: {
          totalExposure,
          expectedLoss,
          avgPD: avgPD * 100,
          avgLGD: avgLGD * 100,
          numAssets: assets.length,
          sectorBreakdown,
          geoBreakdown,
          ratingBreakdown,
        },
        metricsLoading: false 
      });
    } catch (error) {
      console.error('Failed to fetch portfolio metrics:', error);
      set({ metricsLoading: false });
    }
  },

  // Actions - Holdings
  fetchHoldings: async (portfolioId) => {
    set({ holdingsLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/pg/portfolios/${portfolioId}`);
      const data = await res.json();
      set({ holdings: data.assets || [], holdingsLoading: false });
    } catch (error) {
      console.error('Failed to fetch holdings:', error);
      set({ holdingsLoading: false });
    }
  },

  // Actions - Analysis
  runAnalysis: async () => {
    const { selectedPortfolio, selectedScenarios, selectedHorizons, scenarios } = get();
    
    if (!selectedPortfolio || selectedScenarios.length === 0) {
      set({ analysisError: 'Please select a portfolio and at least one scenario' });
      return;
    }

    set({ analysisRunning: true, analysisProgress: 0, analysisError: null });

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        set(state => ({
          analysisProgress: Math.min(state.analysisProgress + 10, 90)
        }));
      }, 500);

      // Map scenario IDs to scenario names for the legacy API
      const scenarioNames = selectedScenarios.map(id => {
        const scenario = scenarios.find(s => s.id === id);
        return scenario?.name || 'Unknown';
      });

      const res = await fetch(`${API_URL}/api/analysis/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_id: selectedPortfolio.id,
          scenarios: ['Orderly', 'Disorderly', 'Hot house world'], // Use legacy scenario names
          horizons: selectedHorizons,
        }),
      });

      clearInterval(progressInterval);

      if (!res.ok) {
        throw new Error('Analysis failed');
      }

      const data = await res.json();
      set({ 
        analysisResults: data, 
        analysisRunning: false, 
        analysisProgress: 100 
      });
      
      return data;
    } catch (error) {
      console.error('Analysis failed — using seeded fallback:', error);
      // Backend offline: generate deterministic seeded results so the UI stays functional
      const { selectedPortfolio: p } = get();
      const totalExp = p?.total_exposure || 850_000_000;
      const seedResults = {
        portfolio_id: p?.id || 'demo',
        portfolio_name: p?.name || 'Demo Portfolio',
        total_exposure: totalExp,
        run_date: new Date().toISOString(),
        _fallback: true,
        results: [
          { scenario_name: 'Net Zero 2050', horizon: 2030, portfolio_metrics: { expected_loss: totalExp * 0.031, avg_pd_change: 0.18, capital_charge: totalExp * 0.048 } },
          { scenario_name: 'Net Zero 2050', horizon: 2050, portfolio_metrics: { expected_loss: totalExp * 0.019, avg_pd_change: 0.09, capital_charge: totalExp * 0.031 } },
          { scenario_name: 'Below 2°C', horizon: 2030, portfolio_metrics: { expected_loss: totalExp * 0.044, avg_pd_change: 0.27, capital_charge: totalExp * 0.062 } },
          { scenario_name: 'Below 2°C', horizon: 2050, portfolio_metrics: { expected_loss: totalExp * 0.029, avg_pd_change: 0.14, capital_charge: totalExp * 0.041 } },
          { scenario_name: 'Delayed Transition', horizon: 2030, portfolio_metrics: { expected_loss: totalExp * 0.061, avg_pd_change: 0.43, capital_charge: totalExp * 0.089 } },
          { scenario_name: 'Delayed Transition', horizon: 2050, portfolio_metrics: { expected_loss: totalExp * 0.082, avg_pd_change: 0.58, capital_charge: totalExp * 0.11 } },
          { scenario_name: 'Current Policies', horizon: 2030, portfolio_metrics: { expected_loss: totalExp * 0.078, avg_pd_change: 0.51, capital_charge: totalExp * 0.104 } },
          { scenario_name: 'Current Policies', horizon: 2050, portfolio_metrics: { expected_loss: totalExp * 0.134, avg_pd_change: 0.94, capital_charge: totalExp * 0.168 } },
        ],
        sector_breakdown: {
          'Energy': totalExp * 0.22,
          'Utilities': totalExp * 0.18,
          'Industrials': totalExp * 0.16,
          'Real Estate': totalExp * 0.14,
          'Materials': totalExp * 0.12,
          'Financials': totalExp * 0.10,
          'Other': totalExp * 0.08,
        },
      };
      set({
        analysisResults: seedResults,
        analysisRunning: false,
        analysisProgress: 100,
        analysisError: null,
        isFallback: true,      // GAP-003: signal that seed data is in use
        apiReachable: false,   // GAP-003: API is offline
      });
      return seedResults;
    }
  },

  clearAnalysisResults: () => {
    set({ analysisResults: null, analysisProgress: 0, analysisError: null });
  },

  // Reset
  reset: () => {
    set({
      selectedPortfolio: null,
      selectedScenarios: [],
      analysisResults: null,
      analysisProgress: 0,
      analysisError: null,
      metrics: null,
      holdings: [],
    });
  },
}));
