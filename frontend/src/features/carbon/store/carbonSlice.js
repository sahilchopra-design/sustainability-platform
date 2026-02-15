/**
 * Carbon Credits Redux Slice
 * State management for the carbon module
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  fetchPortfolios,
  fetchPortfolioDashboard,
  calculateCarbonCredits
} from '../api/carbonApi';

// Async Thunks
export const loadPortfolios = createAsyncThunk(
  'carbon/loadPortfolios',
  async () => {
    const response = await fetchPortfolios();
    return response;
  }
);

export const loadPortfolioDashboard = createAsyncThunk(
  'carbon/loadPortfolioDashboard',
  async (portfolioId) => {
    const response = await fetchPortfolioDashboard(portfolioId);
    return response;
  }
);

export const runCalculation = createAsyncThunk(
  'carbon/runCalculation',
  async (request) => {
    const response = await calculateCarbonCredits(request);
    return response;
  }
);

// Initial State
const initialState = {
  portfolios: {
    items: [],
    loading: false,
    error: null
  },
  currentPortfolio: {
    data: null,
    dashboard: null,
    loading: false,
    error: null
  },
  projects: {
    items: [],
    loading: false,
    error: null
  },
  scenarios: {
    items: [],
    activeId: null
  },
  calculations: {
    current: null,
    loading: false,
    error: null,
    history: []
  },
  ui: {
    sidebarOpen: true,
    activeView: 'dashboard',
    filters: {
      dateRange: null,
      scenario: null
    }
  }
};

// Slice
const carbonSlice = createSlice({
  name: 'carbon',
  initialState,
  reducers: {
    setActiveView: (state, action) => {
      state.ui.activeView = action.payload;
    },
    setActiveScenario: (state, action) => {
      state.scenarios.activeId = action.payload;
    },
    addScenario: (state, action) => {
      state.scenarios.items.push(action.payload);
    },
    updateScenario: (state, action) => {
      const index = state.scenarios.items.findIndex(
        (s) => s.id === action.payload.id
      );
      if (index !== -1) {
        state.scenarios.items[index] = action.payload;
      }
    },
    deleteScenario: (state, action) => {
      state.scenarios.items = state.scenarios.items.filter(
        (s) => s.id !== action.payload
      );
    },
    setSidebarOpen: (state, action) => {
      state.ui.sidebarOpen = action.payload;
    },
    clearCalculationError: (state) => {
      state.calculations.error = null;
    },
    setCurrentPortfolio: (state, action) => {
      state.currentPortfolio.data = action.payload;
    },
    setScenarios: (state, action) => {
      state.scenarios.items = action.payload;
    },
    setProjects: (state, action) => {
      state.projects.items = action.payload;
    }
  },
  extraReducers: (builder) => {
    // Load Portfolios
    builder.addCase(loadPortfolios.pending, (state) => {
      state.portfolios.loading = true;
      state.portfolios.error = null;
    });
    builder.addCase(loadPortfolios.fulfilled, (state, action) => {
      state.portfolios.items = action.payload;
      state.portfolios.loading = false;
    });
    builder.addCase(loadPortfolios.rejected, (state, action) => {
      state.portfolios.loading = false;
      state.portfolios.error = action.error.message || 'Failed to load portfolios';
    });

    // Load Portfolio Dashboard
    builder.addCase(loadPortfolioDashboard.pending, (state) => {
      state.currentPortfolio.loading = true;
      state.currentPortfolio.error = null;
    });
    builder.addCase(loadPortfolioDashboard.fulfilled, (state, action) => {
      state.currentPortfolio.dashboard = action.payload;
      state.currentPortfolio.loading = false;
    });
    builder.addCase(loadPortfolioDashboard.rejected, (state, action) => {
      state.currentPortfolio.loading = false;
      state.currentPortfolio.error = action.error.message || 'Failed to load dashboard';
    });

    // Run Calculation
    builder.addCase(runCalculation.pending, (state) => {
      state.calculations.loading = true;
      state.calculations.error = null;
    });
    builder.addCase(runCalculation.fulfilled, (state, action) => {
      state.calculations.current = action.payload;
      state.calculations.history.unshift(action.payload);
      state.calculations.loading = false;
    });
    builder.addCase(runCalculation.rejected, (state, action) => {
      state.calculations.loading = false;
      state.calculations.error = action.error.message || 'Calculation failed';
    });
  }
});

export const {
  setActiveView,
  setActiveScenario,
  addScenario,
  updateScenario,
  deleteScenario,
  setSidebarOpen,
  clearCalculationError,
  setCurrentPortfolio,
  setScenarios,
  setProjects
} = carbonSlice.actions;

export default carbonSlice.reducer;
