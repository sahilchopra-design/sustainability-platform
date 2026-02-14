import { create } from 'zustand';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useBrowserStore = create((set, get) => ({
  // ---- Data ----
  sources: [],
  sourcesLoading: false,
  scenarios: [],
  scenariosTotal: 0,
  scenariosLoading: false,
  stats: null,
  analytics: null,
  temperatureAnalytics: null,
  availableVariables: [],
  favorites: [],

  // ---- Filters ----
  selectedSourceIds: [],
  selectedCategories: [],
  temperatureRange: [1.0, 5.0],
  searchQuery: '',
  sortBy: 'name',  // name, temperature_target, trajectory_count
  viewMode: 'grid', // grid, list

  // ---- Detail drawer ----
  detailScenario: null,
  detailTrajectories: [],
  detailLoading: false,

  // ---- Compare workspace ----
  compareScenarios: [],
  compareData: null,
  compareLoading: false,

  // ---- Sync ----
  syncLogs: [],

  // ============ ACTIONS ============

  // -- Bootstrap --
  init: async () => {
    const s = get();
    await Promise.all([s.fetchSources(), s.fetchScenarios(), s.fetchStats(), s.fetchFavorites()]);
  },

  fetchSources: async () => {
    set({ sourcesLoading: true });
    try {
      const r = await fetch(`${API_URL}/api/v1/data-hub/sources`);
      set({ sources: await r.json(), sourcesLoading: false });
    } catch { set({ sourcesLoading: false }); }
  },

  fetchStats: async () => {
    try {
      const [stats, coverage, temp, vars] = await Promise.all([
        fetch(`${API_URL}/api/v1/data-hub/stats`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/data-hub/analytics/coverage`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/data-hub/analytics/temperature-range`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/data-hub/trajectories/available-variables`).then(r => r.json()),
      ]);
      set({ stats, analytics: coverage, temperatureAnalytics: temp, availableVariables: vars });
    } catch {}
  },

  fetchScenarios: async () => {
    set({ scenariosLoading: true });
    const { selectedSourceIds, selectedCategories, searchQuery } = get();
    try {
      if (searchQuery.trim()) {
        const r = await fetch(`${API_URL}/api/v1/data-hub/scenarios/search`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: searchQuery.trim(),
            source_ids: selectedSourceIds,
            categories: selectedCategories,
            limit: 200, offset: 0,
          }),
        });
        const d = await r.json();
        set({ scenarios: d.scenarios || [], scenariosTotal: d.total || 0, scenariosLoading: false });
      } else {
        const params = new URLSearchParams({ limit: '200', offset: '0' });
        if (selectedSourceIds.length === 1) params.set('source_id', selectedSourceIds[0]);
        if (selectedCategories.length === 1) params.set('category', selectedCategories[0]);
        const r = await fetch(`${API_URL}/api/v1/data-hub/scenarios?${params}`);
        const d = await r.json();
        set({ scenarios: d.scenarios || [], scenariosTotal: d.total || 0, scenariosLoading: false });
      }
    } catch { set({ scenariosLoading: false }); }
  },

  // -- Filters --
  toggleSource: (sourceId) => {
    const cur = get().selectedSourceIds;
    const next = cur.includes(sourceId) ? cur.filter(id => id !== sourceId) : [...cur, sourceId];
    set({ selectedSourceIds: next });
    get().fetchScenarios();
  },
  toggleCategory: (cat) => {
    const cur = get().selectedCategories;
    const next = cur.includes(cat) ? cur.filter(c => c !== cat) : [...cur, cat];
    set({ selectedCategories: next });
    get().fetchScenarios();
  },
  setTemperatureRange: (range) => set({ temperatureRange: range }),
  setSearchQuery: (q) => set({ searchQuery: q }),
  applySearch: () => get().fetchScenarios(),
  setSortBy: (s) => set({ sortBy: s }),
  setViewMode: (m) => set({ viewMode: m }),
  clearFilters: () => {
    set({ selectedSourceIds: [], selectedCategories: [], temperatureRange: [1.0, 5.0], searchQuery: '' });
    get().fetchScenarios();
  },

  // -- Filtered + sorted scenarios --
  getFilteredScenarios: () => {
    const { scenarios, selectedSourceIds, selectedCategories, temperatureRange, sortBy } = get();
    let filtered = [...scenarios];
    if (selectedSourceIds.length > 0)
      filtered = filtered.filter(s => selectedSourceIds.includes(s.source_id));
    if (selectedCategories.length > 0)
      filtered = filtered.filter(s => selectedCategories.includes(s.category));
    const [tMin, tMax] = temperatureRange;
    if (tMin > 1.0 || tMax < 5.0)
      filtered = filtered.filter(s => !s.temperature_target || (s.temperature_target >= tMin && s.temperature_target <= tMax));
    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'temperature_target') return (a.temperature_target || 99) - (b.temperature_target || 99);
      if (sortBy === 'trajectory_count') return (b.trajectory_count || 0) - (a.trajectory_count || 0);
      return (a.display_name || a.name || '').localeCompare(b.display_name || b.name || '');
    });
    return filtered;
  },

  // -- Detail drawer --
  openDetail: async (scenario) => {
    set({ detailScenario: scenario, detailLoading: true, detailTrajectories: [] });
    try {
      const r = await fetch(`${API_URL}/api/v1/data-hub/scenarios/${scenario.id}/trajectories`);
      set({ detailTrajectories: await r.json(), detailLoading: false });
    } catch { set({ detailLoading: false }); }
  },
  closeDetail: () => set({ detailScenario: null, detailTrajectories: [], detailLoading: false }),

  // -- Compare workspace --
  addToCompare: (sc) => {
    const cur = get().compareScenarios;
    if (cur.length >= 10 || cur.some(s => s.id === sc.id)) return;
    set({ compareScenarios: [...cur, sc] });
  },
  removeFromCompare: (id) => set({ compareScenarios: get().compareScenarios.filter(s => s.id !== id) }),
  clearCompare: () => set({ compareScenarios: [], compareData: null }),
  runCompare: async (variables, regions) => {
    const ids = get().compareScenarios.map(s => s.id);
    if (ids.length < 2) return;
    set({ compareLoading: true });
    try {
      const r = await fetch(`${API_URL}/api/v1/analysis/compare`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_ids: ids, variables: variables || [], regions: regions || [] }),
      });
      set({ compareData: await r.json(), compareLoading: false });
    } catch { set({ compareLoading: false }); }
  },

  // -- Favorites --
  fetchFavorites: async () => {
    try {
      const r = await fetch(`${API_URL}/api/v1/data-hub/favorites?user_id=default_user`);
      set({ favorites: await r.json() });
    } catch {}
  },
  toggleFavorite: async (scenarioId) => {
    const favs = get().favorites;
    const existing = favs.find(f => f.scenario_id === scenarioId);
    if (existing) {
      await fetch(`${API_URL}/api/v1/data-hub/favorites/${existing.id}`, { method: 'DELETE' });
    } else {
      await fetch(`${API_URL}/api/v1/data-hub/favorites`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId, user_id: 'default_user' }),
      });
    }
    get().fetchFavorites();
  },
  isFavorite: (scenarioId) => get().favorites.some(f => f.scenario_id === scenarioId),

  // -- Sync --
  syncSource: async (sourceId) => {
    await fetch(`${API_URL}/api/v1/data-hub/sources/${sourceId}/sync`, { method: 'POST' });
    await Promise.all([get().fetchSources(), get().fetchScenarios(), get().fetchStats()]);
  },
  fetchSyncLogs: async () => {
    const r = await fetch(`${API_URL}/api/v1/data-hub/sync-logs`);
    set({ syncLogs: await r.json() });
  },
}));
