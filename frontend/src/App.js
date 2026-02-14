import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppRouter />
      </Router>
    </QueryClientProvider>
  );
}

export default App;
