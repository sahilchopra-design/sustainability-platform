import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { store } from './store';
import './App.css';

import Dashboard from './pages/Dashboard';
import Portfolios from './pages/Portfolios';
import PortfolioDetail from './pages/PortfolioDetail';
import Analysis from './pages/Analysis';
import Results from './pages/Results';
import ScenarioData from './pages/ScenarioData';
import ScenarioBuilder from './pages/ScenarioBuilder';
import DataHub from './pages/DataHub';
import ComparisonPage from './pages/ComparisonPage';
import ScenarioBrowserPage from './pages/ScenarioBrowserPage';
import ImpactCalculatorPage from './pages/ImpactCalculatorPage';
import PortfolioManagerPage from './pages/PortfolioManagerPage';
import LoginPage from './pages/LoginPage';
import AlertsPage from './pages/AlertsPage';
import NGFSScenariosPage from './pages/NGFSScenariosPage';
import CustomBuilderPage from './pages/CustomBuilderPage';
import SubAnalysisPage from './pages/SubAnalysisPage';
import CBAMPage from './pages/CBAMPage';
import CarbonDashboard from './features/carbon/pages/CarbonDashboard';
import NatureRiskPage from './features/nature-risk/pages/NatureRiskPage';
import StrandedAssetsPage from './features/stranded-assets/pages/StrandedAssetsPage';
import ValuationPage from './features/valuation/pages/ValuationPage';
import SustainabilityPage from './features/sustainability/pages/SustainabilityPage';
import ScenarioAnalysisPage from './features/scenarios/pages/ScenarioAnalysisPage';
import PortfolioAnalyticsPage from './features/portfolio-analytics/pages/PortfolioAnalyticsPage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

// Auth callback — handles Google OAuth session_id from URL fragment
function AuthCallback({ onAuth }) {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) { navigate('/login'); return; }

    const sessionId = match[1];
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    fetch(`${API_URL}/api/auth/google/session`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ session_id: sessionId }),
    })
      .then(r => { if (!r.ok) throw new Error('Auth failed'); return r.json(); })
      .then(data => {
        localStorage.setItem('session_token', data.session_token);
        onAuth(data);
        navigate('/', { state: { user: data } });
      })
      .catch(() => navigate('/login'));
  }, [navigate, onAuth]);

  return <div className="flex items-center justify-center h-screen text-muted-foreground">Authenticating...</div>;
}

function AppRouter() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [isCallback, setIsCallback] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Check existing session on mount
  useEffect(() => {
    // Check for session_id in URL fragment (Google OAuth callback)
    if (location.hash?.includes('session_id=')) {
      setIsCallback(true);
      setChecking(false);
      return;
    }

    const token = localStorage.getItem('session_token');
    if (!token) { setChecking(false); return; }

    fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => { setUser(data); setChecking(false); })
      .catch(() => { localStorage.removeItem('session_token'); setChecking(false); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isCallback) {
    return <AuthCallback onAuth={setUser} />;
  }

  const handleLogout = async () => {
    const token = localStorage.getItem('session_token');
    await fetch(`${API_URL}/api/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    }).catch(() => {});
    localStorage.removeItem('session_token');
    setUser(null);
  };

  if (checking) {
    return <div className="flex items-center justify-center h-screen text-muted-foreground">Loading...</div>;
  }

  if (!user) {
    return <LoginPage onAuth={(data) => setUser(data)} />;
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-60 bg-[#0f2137] flex flex-col shrink-0">
        {/* Brand Header */}
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <img src="/a2-intelligence-logo.png" alt="A2" className="h-9 w-9 rounded object-contain bg-white/5" />
            <div>
              <h1 className="text-sm font-semibold text-white tracking-tight">A2 Intelligence</h1>
              <p className="text-[10px] text-cyan-300/70">by AA Impact Inc.</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-4 overflow-y-auto">
          {/* Analytics */}
          <NavGroup label="Analytics">
            <SideLink to="/" end icon="layout" label="Dashboard" />
            <SideLink to="/impact" icon="target" label="Impact Calculator" />
            <SideLink to="/sub-analysis" icon="microscope" label="Sub-Parameter" />
            <SideLink to="/cbam" icon="globe" label="CBAM" />
            <SideLink to="/carbon" icon="leaf" label="Carbon Credits" />
            <SideLink to="/nature-risk" icon="tree" label="Nature Risk" />
            <SideLink to="/stranded-assets" icon="trending-down" label="Stranded Assets" />
            <SideLink to="/valuation" icon="building" label="RE Valuation" />
            <SideLink to="/sustainability" icon="award" label="Sustainability" />
            <SideLink to="/scenario-analysis" icon="calculator" label="Scenario Analysis" />
            <SideLink to="/portfolio-analytics" icon="pie-chart" label="Portfolio Analytics" />
          </NavGroup>
          {/* Scenarios */}
          <NavGroup label="Scenarios">
            <SideLink to="/browser" icon="search" label="Scenario Browser" />
            <SideLink to="/data-hub" icon="database" label="Data Hub" />
            <SideLink to="/ngfs" icon="globe" label="NGFS Catalog" />
            <SideLink to="/comparison" icon="git-compare" label="Comparison" />
            <SideLink to="/custom-builder" icon="wrench" label="Custom Builder" />
          </NavGroup>
          {/* Portfolio */}
          <NavGroup label="Portfolio">
            <SideLink to="/portfolios" icon="briefcase" label="Portfolios" />
            <SideLink to="/portfolio-manager" icon="upload" label="Upload & Edit" />
            <SideLink to="/analysis" icon="bar-chart" label="Run Analysis" />
          </NavGroup>
          {/* System */}
          <NavGroup label="System">
            <SideLink to="/alerts" icon="bell" label="Alerts" />
            <SideLink to="/scenario-builder" icon="layers" label="Legacy Builder" />
            <SideLink to="/scenario-data" icon="archive" label="Scenario Data" />
          </NavGroup>
        </nav>
        {/* User footer */}
        <div className="p-3 border-t border-white/10">
          <div className="flex items-center gap-2 mb-2">
            {user.picture ? (
              <img src={user.picture} alt="" className="w-7 h-7 rounded-full" />
            ) : (
              <div className="w-7 h-7 rounded-full bg-cyan-500/20 flex items-center justify-center text-xs font-medium text-cyan-300">
                {user.name?.[0]?.toUpperCase() || 'U'}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white/90 truncate">{user.name}</p>
              <p className="text-[10px] text-white/40 truncate">{user.email}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="text-[10px] text-white/40 hover:text-white/70 transition-colors"
            data-testid="logout-btn">Sign out</button>
          <div className="mt-2 pt-2 border-t border-white/10 flex items-center gap-1.5">
            <img src="/aa-impact-logo.jpg" alt="AA Impact" className="h-5 w-5 rounded object-cover" />
            <span className="text-[9px] text-white/30">AA Impact Inc.</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-[#f8fafc]">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/portfolios" element={<Portfolios />} />
          <Route path="/portfolios/:id" element={<PortfolioDetail />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/results/:runId" element={<Results />} />
          <Route path="/scenario-data" element={<ScenarioData />} />
          <Route path="/scenario-builder" element={<ScenarioBuilder />} />
          <Route path="/data-hub" element={<DataHub />} />
          <Route path="/browser" element={<ScenarioBrowserPage />} />
          <Route path="/comparison" element={<ComparisonPage />} />
          <Route path="/impact" element={<ImpactCalculatorPage />} />
          <Route path="/portfolio-manager" element={<PortfolioManagerPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/ngfs" element={<NGFSScenariosPage />} />
          <Route path="/custom-builder" element={<CustomBuilderPage />} />
          <Route path="/sub-analysis" element={<SubAnalysisPage />} />
          <Route path="/cbam" element={<CBAMPage />} />
          <Route path="/carbon" element={<CarbonDashboard />} />
          <Route path="/nature-risk" element={<NatureRiskPage />} />
          <Route path="/stranded-assets" element={<StrandedAssetsPage />} />
          <Route path="/valuation" element={<ValuationPage />} />
          <Route path="/sustainability" element={<SustainabilityPage />} />
          <Route path="/scenario-analysis" element={<ScenarioAnalysisPage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AppRouter />
        </Router>
      </QueryClientProvider>
    </Provider>
  );
}

/* Nav helpers */
function NavGroup({ label, children }) {
  return (
    <div>
      <p className="text-[10px] font-semibold text-white/30 uppercase tracking-widest mb-1 px-2">{label}</p>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

const ICON_MAP = {
  layout: 'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z',
  target: 'M12 2a10 10 0 100 20 10 10 0 000-20zm0 4a6 6 0 100 12 6 6 0 000-12zm0 4a2 2 0 100 4 2 2 0 000-4z',
  microscope: 'M9 2v6h2V2H9zm-1 8a4 4 0 108 0H8zm-4 8h16v2H4v-2z',
  search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  database: 'M4 7v10c0 2 3.6 4 8 4s8-2 8-4V7M4 7c0 2 3.6 4 8 4s8-2 8-4M4 7c0-2 3.6-4 8-4s8 2 8 4',
  globe: 'M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2a15 15 0 014 10 15 15 0 01-4 10 15 15 0 01-4-10A15 15 0 0112 2z',
  'git-compare': 'M18 21a3 3 0 100-6 3 3 0 000 6zM6 9a3 3 0 100-6 3 3 0 000 6zm12 3V9a3 3 0 00-3-3h-4M6 15v-3',
  wrench: 'M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z',
  briefcase: 'M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2',
  upload: 'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12',
  'bar-chart': 'M18 20V10M12 20V4M6 20v-6',
  bell: 'M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0',
  layers: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  archive: 'M21 8v13H3V8M1 3h22v5H1zM10 12h4',
  leaf: 'M11 20A7 7 0 019.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10zM2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12',
  tree: 'M12 22v-7m0 0c-3.5 0-6-2.5-6-6 0-2 1-4 3-5.5C10 2.5 11 2 12 2s2 .5 3 1.5c2 1.5 3 3.5 3 5.5 0 3.5-2.5 6-6 6z',
  'trending-down': 'M23 18l-9.5-9.5-5 5L1 6M17 18h6v-6',
  building: 'M3 21h18M5 21V7l8-4v18M19 21V11l-6-4M9 9v.01M9 12v.01M9 15v.01M9 18v.01',
  award: 'M12 15l-2 5-1.5-4-4.5 1.5L6 13 2 11l4-2L4 4.5 8.5 6 10 2l2 5 2-5 1.5 4 4.5-1.5L18 9l4 2-4 2 2 4.5-4.5-1.5L14 20l-2-5z',
  calculator: 'M4 2h16a2 2 0 012 2v16a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2zm3 4h10M7 10h2M7 14h2M7 18h2M15 10h2M15 14h2M15 18h2M11 10h2M11 14h2M11 18h2',
};

function SideLink({ to, icon, label, end }) {
  const d = ICON_MAP[icon] || ICON_MAP.layout;
  return (
    <NavLink to={to} end={end}
      className={({ isActive }) =>
        `flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-[13px] transition-all ${
          isActive ? 'bg-cyan-500/15 text-cyan-300 font-medium' : 'text-white/60 hover:text-white/90 hover:bg-white/5'
        }`
      }
      data-testid={`nav-${to.replace('/', '') || 'dashboard'}`}>
      <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d={d} />
      </svg>
      <span>{label}</span>
    </NavLink>
  );
}

export default App;
