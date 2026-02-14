import { create } from 'zustand';
import { Portfolio, Holding, ChangeLog, PortfolioMetrics, HoldingFilters, HoldingSortConfig } from '../types/portfolio';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

interface PortfolioEditorState {
  // Portfolio data
  portfolio: Portfolio | null;
  holdings: Holding[];
  metrics: PortfolioMetrics | null;
  changeLog: ChangeLog[];
  
  // UI state
  loading: boolean;
  saving: boolean;
  selectedHoldingIds: string[];
  filters: HoldingFilters;
  sortConfig: HoldingSortConfig;
  
  // Modal/drawer state
  showAddModal: boolean;
  showEditDrawer: boolean;
  editingHolding: Holding | null;
  
  // Actions - Portfolio
  loadPortfolio: (portfolioId: string) => Promise<void>;
  updatePortfolio: (updates: Partial<Portfolio>) => Promise<void>;
  
  // Actions - Holdings
  loadHoldings: (portfolioId: string) => Promise<void>;
  addHolding: (holding: Omit<Holding, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateHolding: (holdingId: string, updates: Partial<Holding>) => Promise<void>;
  deleteHolding: (holdingId: string) => Promise<void>;
  bulkUpdateHoldings: (holdingIds: string[], updates: Partial<Holding>) => Promise<void>;
  bulkDeleteHoldings: (holdingIds: string[]) => Promise<void>;
  
  // Actions - Filters & Sort
  setFilters: (filters: Partial<HoldingFilters>) => void;
  setSortConfig: (config: HoldingSortConfig) => void;
  
  // Actions - Selection
  setSelectedHoldingIds: (ids: string[]) => void;
  toggleHoldingSelection: (id: string) => void;
  selectAllHoldings: () => void;
  clearSelection: () => void;
  
  // Actions - Modals
  openAddModal: () => void;
  closeAddModal: () => void;
  openEditDrawer: (holding: Holding) => void;
  closeEditDrawer: () => void;
  
  // Actions - Change Log
  loadChangeLog: (portfolioId: string) => Promise<void>;
  undoChange: (changeId: string) => Promise<void>;
  
  // Actions - Metrics
  refreshMetrics: (portfolioId: string) => Promise<void>;
  
  // Reset
  reset: () => void;
}

export const usePortfolioEditorStore = create<PortfolioEditorState>((set, get) => ({
  // Initial state
  portfolio: null,
  holdings: [],
  metrics: null,
  changeLog: [],
  loading: false,
  saving: false,
  selectedHoldingIds: [],
  filters: {},
  sortConfig: { field: 'counterparty_name', direction: 'asc' },
  showAddModal: false,
  showEditDrawer: false,
  editingHolding: null,
  
  // Portfolio actions
  loadPortfolio: async (portfolioId: string) => {
    set({ loading: true });
    try {
      const response = await axios.get<Portfolio>(`${BACKEND_URL}/api/v1/portfolios/${portfolioId}`);
      set({ portfolio: response.data, loading: false });
    } catch (error: any) {
      set({ loading: false });
      toast.error('Failed to Load Portfolio', {
        description: error.response?.data?.detail || 'Could not load portfolio data',
      });
    }
  },
  
  updatePortfolio: async (updates: Partial<Portfolio>) => {
    const { portfolio } = get();
    if (!portfolio) return;
    
    set({ saving: true });
    try {
      const response = await axios.patch<Portfolio>(
        `${BACKEND_URL}/api/v1/portfolios/${portfolio.id}`,
        updates
      );
      set({ portfolio: response.data, saving: false });
      toast.success('Portfolio Updated', {
        description: 'Portfolio information has been updated successfully',
      });
    } catch (error: any) {
      set({ saving: false });
      toast.error('Update Failed', {
        description: error.response?.data?.detail || 'Could not update portfolio',
      });
    }
  },
  
  // Holdings actions
  loadHoldings: async (portfolioId: string) => {
    set({ loading: true });
    try {
      const response = await axios.get<Holding[]>(
        `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/holdings`
      );
      set({ holdings: response.data, loading: false });
    } catch (error: any) {
      set({ loading: false });
      toast.error('Failed to Load Holdings', {
        description: error.response?.data?.detail || 'Could not load holdings data',
      });
    }
  },
  
  addHolding: async (holding: Omit<Holding, 'id' | 'created_at' | 'updated_at'>) => {
    const { portfolio, holdings } = get();
    if (!portfolio) return;
    
    set({ saving: true });
    try {
      const response = await axios.post<Holding>(
        `${BACKEND_URL}/api/v1/portfolios/${portfolio.id}/holdings`,
        holding
      );
      set({ 
        holdings: [...holdings, response.data],
        saving: false,
        showAddModal: false,
      });
      toast.success('Holding Added', {
        description: `${holding.counterparty_name} added to portfolio`,
      });
      get().refreshMetrics(portfolio.id);
    } catch (error: any) {
      set({ saving: false });
      toast.error('Add Failed', {
        description: error.response?.data?.detail || 'Could not add holding',
      });
    }
  },
  
  updateHolding: async (holdingId: string, updates: Partial<Holding>) => {
    const { portfolio, holdings } = get();
    if (!portfolio) return;
    
    set({ saving: true });
    try {
      const response = await axios.patch<Holding>(
        `${BACKEND_URL}/api/v1/portfolios/${portfolio.id}/holdings/${holdingId}`,
        updates
      );
      set({
        holdings: holdings.map((h) => (h.id === holdingId ? response.data : h)),
        saving: false,
        showEditDrawer: false,
        editingHolding: null,
      });
      toast.success('Holding Updated', {
        description: 'Holding information has been updated',
      });
      get().refreshMetrics(portfolio.id);
    } catch (error: any) {
      set({ saving: false });
      toast.error('Update Failed', {
        description: error.response?.data?.detail || 'Could not update holding',
      });
    }
  },
  
  deleteHolding: async (holdingId: string) => {
    const { portfolio, holdings } = get();
    if (!portfolio) return;
    
    set({ saving: true });
    try {
      await axios.delete(
        `${BACKEND_URL}/api/v1/portfolios/${portfolio.id}/holdings/${holdingId}`
      );
      set({
        holdings: holdings.filter((h) => h.id !== holdingId),
        saving: false,
      });
      toast.success('Holding Deleted', {
        description: 'Holding has been removed from portfolio',
      });
      get().refreshMetrics(portfolio.id);
    } catch (error: any) {
      set({ saving: false });
      toast.error('Delete Failed', {
        description: error.response?.data?.detail || 'Could not delete holding',
      });
    }
  },
  
  bulkUpdateHoldings: async (holdingIds: string[], updates: Partial<Holding>) => {
    const { portfolio, holdings } = get();
    if (!portfolio) return;
    
    set({ saving: true });
    try {
      await axios.post(
        `${BACKEND_URL}/api/v1/portfolios/${portfolio.id}/holdings/bulk-update`,
        { holding_ids: holdingIds, updates }
      );
      
      // Optimistic update
      set({
        holdings: holdings.map((h) => 
          holdingIds.includes(h.id) ? { ...h, ...updates } : h
        ),
        saving: false,
        selectedHoldingIds: [],
      });
      toast.success('Holdings Updated', {
        description: `${holdingIds.length} holdings updated successfully`,
      });
      get().refreshMetrics(portfolio.id);
    } catch (error: any) {
      set({ saving: false });
      toast.error('Bulk Update Failed', {
        description: error.response?.data?.detail || 'Could not update holdings',
      });
    }
  },
  
  bulkDeleteHoldings: async (holdingIds: string[]) => {
    const { portfolio, holdings } = get();
    if (!portfolio) return;
    
    set({ saving: true });
    try {
      await axios.post(
        `${BACKEND_URL}/api/v1/portfolios/${portfolio.id}/holdings/bulk-delete`,
        { holding_ids: holdingIds }
      );
      set({
        holdings: holdings.filter((h) => !holdingIds.includes(h.id)),
        saving: false,
        selectedHoldingIds: [],
      });
      toast.success('Holdings Deleted', {
        description: `${holdingIds.length} holdings removed from portfolio`,
      });
      get().refreshMetrics(portfolio.id);
    } catch (error: any) {
      set({ saving: false });
      toast.error('Bulk Delete Failed', {
        description: error.response?.data?.detail || 'Could not delete holdings',
      });
    }
  },
  
  // Filters & Sort
  setFilters: (filters: Partial<HoldingFilters>) => {
    set((state) => ({ filters: { ...state.filters, ...filters } }));
  },
  
  setSortConfig: (config: HoldingSortConfig) => {
    set({ sortConfig: config });
  },
  
  // Selection
  setSelectedHoldingIds: (ids: string[]) => {
    set({ selectedHoldingIds: ids });
  },
  
  toggleHoldingSelection: (id: string) => {
    set((state) => ({
      selectedHoldingIds: state.selectedHoldingIds.includes(id)
        ? state.selectedHoldingIds.filter((hId) => hId !== id)
        : [...state.selectedHoldingIds, id],
    }));
  },
  
  selectAllHoldings: () => {
    const { holdings } = get();
    set({ selectedHoldingIds: holdings.map((h) => h.id) });
  },
  
  clearSelection: () => {
    set({ selectedHoldingIds: [] });
  },
  
  // Modals
  openAddModal: () => set({ showAddModal: true }),
  closeAddModal: () => set({ showAddModal: false }),
  openEditDrawer: (holding: Holding) => {
    set({ showEditDrawer: true, editingHolding: holding });
  },
  closeEditDrawer: () => {
    set({ showEditDrawer: false, editingHolding: null });
  },
  
  // Change Log
  loadChangeLog: async (portfolioId: string) => {
    try {
      const response = await axios.get<ChangeLog[]>(
        `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/changelog`
      );
      set({ changeLog: response.data });
    } catch (error) {
      console.error('Failed to load change log:', error);
    }
  },
  
  undoChange: async (changeId: string) => {
    const { portfolio } = get();
    if (!portfolio) return;
    
    set({ saving: true });
    try {
      await axios.post(
        `${BACKEND_URL}/api/v1/portfolios/${portfolio.id}/changelog/${changeId}/undo`
      );
      toast.success('Change Undone', {
        description: 'The change has been reverted',
      });
      // Reload data
      get().loadHoldings(portfolio.id);
      get().loadChangeLog(portfolio.id);
      get().refreshMetrics(portfolio.id);
    } catch (error: any) {
      set({ saving: false });
      toast.error('Undo Failed', {
        description: error.response?.data?.detail || 'Could not undo change',
      });
    }
  },
  
  // Metrics
  refreshMetrics: async (portfolioId: string) => {
    try {
      const response = await axios.get<PortfolioMetrics>(
        `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/metrics`
      );
      set({ metrics: response.data });
    } catch (error) {
      console.error('Failed to refresh metrics:', error);
    }
  },
  
  // Reset
  reset: () => {
    set({
      portfolio: null,
      holdings: [],
      metrics: null,
      changeLog: [],
      loading: false,
      saving: false,
      selectedHoldingIds: [],
      filters: {},
      sortConfig: { field: 'counterparty_name', direction: 'asc' },
      showAddModal: false,
      showEditDrawer: false,
      editingHolding: null,
    });
  },
}));

export default usePortfolioEditorStore;