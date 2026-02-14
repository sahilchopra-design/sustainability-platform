import { create } from 'zustand';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useComparisonStore = create((set, get) => ({
  // Scenario selection
  selectedScenarios: [],
  selectedVariables: [],
  selectedRegions: [],

  // Comparison data
  comparisonData: null,
  comparisonLoading: false,

  // Gap analysis
  gapAnalysis: null,
  gapLoading: false,

  // Consistency
  consistencyChecks: null,
  consistencyLoading: false,

  // Saved comparisons
  savedComparisons: [],

  // Available scenarios for picker
  allScenarios: [],
  allScenariosLoading: false,

  // Available variables
  availableVariables: [],

  // Actions
  fetchAllScenarios: async () => {
    set({ allScenariosLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/data-hub/scenarios?limit=200`);
      const data = await res.json();
      set({ allScenarios: data.scenarios || [], allScenariosLoading: false });
    } catch {
      set({ allScenariosLoading: false });
    }
  },

  fetchAvailableVariables: async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/data-hub/trajectories/available-variables`);
      const data = await res.json();
      set({ availableVariables: data });
    } catch {}
  },

  toggleScenario: (scenario) => {
    const current = get().selectedScenarios;
    const exists = current.find(s => s.id === scenario.id);
    if (exists) {
      set({ selectedScenarios: current.filter(s => s.id !== scenario.id) });
    } else if (current.length < 10) {
      set({ selectedScenarios: [...current, scenario] });
    }
  },

  setSelectedVariables: (vars) => set({ selectedVariables: vars }),
  setSelectedRegions: (regions) => set({ selectedRegions: regions }),

  clearSelection: () => set({ selectedScenarios: [], comparisonData: null, gapAnalysis: null, consistencyChecks: null }),

  runComparison: async () => {
    const { selectedScenarios, selectedVariables, selectedRegions } = get();
    if (selectedScenarios.length < 2) return;
    set({ comparisonLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/analysis/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_ids: selectedScenarios.map(s => s.id),
          variables: selectedVariables,
          regions: selectedRegions.length > 0 ? selectedRegions : [],
        }),
      });
      const data = await res.json();
      set({ comparisonData: data, comparisonLoading: false });
    } catch {
      set({ comparisonLoading: false });
    }
  },

  saveComparison: async (name, description) => {
    const { selectedScenarios, selectedVariables, selectedRegions } = get();
    if (selectedScenarios.length < 2) return null;
    const res = await fetch(`${API_URL}/api/v1/analysis/comparisons`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        description,
        base_scenario_id: selectedScenarios[0].id,
        compare_scenario_ids: selectedScenarios.slice(1).map(s => s.id),
        variable_filter: selectedVariables,
        region_filter: selectedRegions,
      }),
    });
    return res.json();
  },

  runGapAnalysis: async (compId) => {
    set({ gapLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/analysis/comparisons/${compId}/gap-analysis`, { method: 'POST' });
      const data = await res.json();
      set({ gapAnalysis: data.gaps || [], gapLoading: false });
    } catch {
      set({ gapLoading: false });
    }
  },

  runConsistencyCheck: async (scenarioId) => {
    set({ consistencyLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/analysis/scenarios/${scenarioId}/consistency-check`, { method: 'POST' });
      const data = await res.json();
      set({ consistencyChecks: data.checks || [], consistencyLoading: false });
    } catch {
      set({ consistencyLoading: false });
    }
  },

  fetchSavedComparisons: async () => {
    const res = await fetch(`${API_URL}/api/v1/analysis/comparisons`);
    const data = await res.json();
    set({ savedComparisons: data });
  },
}));
