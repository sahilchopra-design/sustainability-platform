import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';

import Dashboard from './pages/Dashboard';
import Portfolios from './pages/Portfolios';
import PortfolioDetail from './pages/PortfolioDetail';
import Analysis from './pages/Analysis';
import Results from './pages/Results';
import ScenarioData from './pages/ScenarioData';
import ScenarioBuilder from './pages/ScenarioBuilder';
import UploadPage from './pages/UploadPage';
import ReviewPage from './pages/ReviewPage';
import PortfolioEditPage from './pages/PortfolioEditPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex h-screen bg-background">
          {/* Sidebar */}
          <aside className="w-64 bg-card border-r border-border flex flex-col">
            <div className="p-6 border-b border-border">
              <h1 className="text-lg font-semibold text-foreground">Climate Risk Platform</h1>
              <p className="text-xs text-muted-foreground mt-1">Portfolio Scenario Analysis</p>
            </div>
            <nav className="flex-1 p-4 space-y-1">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted'
                  }`
                }
                data-testid="nav-dashboard"
              >
                <span>🏠</span>
                <span>Dashboard</span>
              </NavLink>
              <NavLink
                to="/portfolios"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted'
                  }`
                }
                data-testid="nav-portfolios"
              >
                <span>📁</span>
                <span>Portfolios</span>
              </NavLink>
              <NavLink
                to="/analysis"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted'
                  }`
                }
                data-testid="nav-analysis"
              >
                <span>📊</span>
                <span>Run Analysis</span>
              </NavLink>
              <NavLink
                to="/scenario-data"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted'
                  }`
                }
                data-testid="nav-scenario-data"
              >
                <span>🌍</span>
                <span>Scenario Data</span>
              </NavLink>
            </nav>
            <div className="p-4 border-t border-border text-xs text-muted-foreground">
              <p>NGFS Phase 5 Scenarios</p>
              <p className="mt-1">© 2026 Climate Risk Intelligence</p>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/portfolios" element={<Portfolios />} />
              <Route path="/portfolios/:id" element={<PortfolioDetail />} />
              <Route path="/portfolios/:portfolioId/edit" element={<PortfolioEditPage />} />
              <Route path="/portfolios/:portfolioId/upload" element={<UploadPage />} />
              <Route path="/portfolios/:portfolioId/upload/:uploadId/review" element={<ReviewPage />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/results/:runId" element={<Results />} />
              <Route path="/scenario-data" element={<ScenarioData />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
