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

  // Actions - Portfolios
  fetchPortfolios: async () => {
    set({ portfolioLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/portfolios`);
      const data = await res.json();
      set({ portfolios: data.portfolios || [], portfolioLoading: false });
    } catch (error) {
      console.error('Failed to fetch portfolios:', error);
      set({ portfolioLoading: false });
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
      const res = await fetch(`${API_URL}/api/portfolios/${portfolioId}`);
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
          numCounterparties: assets.length,
          sectorBreakdown,
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
      const res = await fetch(`${API_URL}/api/portfolios/${portfolioId}`);
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
      console.error('Analysis failed:', error);
      set({ 
        analysisRunning: false, 
        analysisProgress: 0,
        analysisError: error.message 
      });
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
