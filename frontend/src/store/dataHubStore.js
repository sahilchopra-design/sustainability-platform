import { create } from 'zustand';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useDataHubStore = create((set, get) => ({
  // Sources
  sources: [],
  sourcesLoading: false,
  
  // Scenarios
  scenarios: [],
  scenariosTotal: 0,
  scenariosLoading: false,
  
  // Selected scenario
  selectedScenario: null,
  
  // Trajectories for selected scenario
  trajectories: [],
  trajectoriesLoading: false,
  
  // Filters
  filters: {
    sourceId: null,
    category: null,
    query: '',
  },
  
  // Stats
  stats: null,
  statsLoading: false,

  // Sync logs
  syncLogs: [],

  // Actions
  fetchStats: async () => {
    set({ statsLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/data-hub/stats`);
      const data = await res.json();
      set({ stats: data, statsLoading: false });
    } catch {
      set({ statsLoading: false });
    }
  },

  fetchSources: async () => {
    set({ sourcesLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/data-hub/sources`);
      const data = await res.json();
      set({ sources: data, sourcesLoading: false });
    } catch {
      set({ sourcesLoading: false });
    }
  },

  fetchScenarios: async (sourceId, category, limit = 50, offset = 0) => {
    set({ scenariosLoading: true });
    try {
      const params = new URLSearchParams();
      if (sourceId) params.set('source_id', sourceId);
      if (category) params.set('category', category);
      params.set('limit', limit);
      params.set('offset', offset);
      const res = await fetch(`${API_URL}/api/v1/data-hub/scenarios?${params}`);
      const data = await res.json();
      set({ scenarios: data.scenarios || [], scenariosTotal: data.total || 0, scenariosLoading: false });
    } catch {
      set({ scenariosLoading: false });
    }
  },

  searchScenarios: async (query) => {
    set({ scenariosLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/data-hub/scenarios/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 50, offset: 0 }),
      });
      const data = await res.json();
      set({ scenarios: data.scenarios || [], scenariosTotal: data.total || 0, scenariosLoading: false });
    } catch {
      set({ scenariosLoading: false });
    }
  },

  selectScenario: async (scenario) => {
    set({ selectedScenario: scenario, trajectoriesLoading: true });
    try {
      const res = await fetch(`${API_URL}/api/v1/data-hub/scenarios/${scenario.id}/trajectories`);
      const data = await res.json();
      set({ trajectories: data, trajectoriesLoading: false });
    } catch {
      set({ trajectoriesLoading: false });
    }
  },

  clearSelectedScenario: () => set({ selectedScenario: null, trajectories: [] }),

  setFilters: (filters) => set({ filters }),

  // Analytics
  analytics: null,
  analyticsLoading: false,
  temperatureAnalytics: null,
  availableVariables: [],

  fetchAnalytics: async () => {
    set({ analyticsLoading: true });
    try {
      const [coverage, temp, vars] = await Promise.all([
        fetch(`${API_URL}/api/v1/data-hub/analytics/coverage`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/data-hub/analytics/temperature-range`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/data-hub/trajectories/available-variables`).then(r => r.json()),
      ]);
      set({ analytics: coverage, temperatureAnalytics: temp, availableVariables: vars, analyticsLoading: false });
    } catch {
      set({ analyticsLoading: false });
    }
  },

  seedSources: async () => {
    const res = await fetch(`${API_URL}/api/v1/data-hub/sources/seed`, { method: 'POST' });
    return res.json();
  },

  syncSource: async (sourceId) => {
    const res = await fetch(`${API_URL}/api/v1/data-hub/sources/${sourceId}/sync`, { method: 'POST' });
    return res.json();
  },

  syncAll: async () => {
    const res = await fetch(`${API_URL}/api/v1/data-hub/sync-all`, { method: 'POST' });
    return res.json();
  },

  fetchSyncLogs: async () => {
    const res = await fetch(`${API_URL}/api/v1/data-hub/sync-logs`);
    const data = await res.json();
    set({ syncLogs: data });
  },
}));
