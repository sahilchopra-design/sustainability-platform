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
  const location = useLocation();
  const navigate = useNavigate();

  // Check for session_id in URL fragment (Google OAuth callback)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback onAuth={setUser} />;
  }

  // Check existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('session_token');
    if (!token) { setChecking(false); return; }

    fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => { setUser(data); setChecking(false); })
      .catch(() => { localStorage.removeItem('session_token'); setChecking(false); });
  }, []);

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
      <aside className="w-64 bg-card border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-lg font-semibold text-foreground">Climate Risk Platform</h1>
          <p className="text-xs text-muted-foreground mt-1">Portfolio Scenario Analysis</p>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {[
            { to: '/', label: 'Dashboard', icon: '🏠', id: 'dashboard', end: true },
            { to: '/portfolios', label: 'Portfolios', icon: '📁', id: 'portfolios' },
            { to: '/analysis', label: 'Run Analysis', icon: '📊', id: 'analysis' },
            { to: '/scenario-data', label: 'Scenario Data', icon: '🌍', id: 'scenario-data' },
            { to: '/scenario-builder', label: 'Scenario Builder', icon: '⚗️', id: 'scenario-builder' },
            { to: '/data-hub', label: 'Data Hub', icon: '🗄️', id: 'data-hub' },
            { to: '/browser', label: 'Scenario Browser', icon: '🔍', id: 'browser' },
            { to: '/comparison', label: 'Comparison', icon: '⚖️', id: 'comparison' },
            { to: '/impact', label: 'Impact Calculator', icon: '🎯', id: 'impact' },
            { to: '/portfolio-manager', label: 'Portfolio Manager', icon: '📋', id: 'portfolio-manager' },
          ].map(item => (
            <NavLink key={item.id} to={item.to} end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive ? 'bg-primary text-primary-foreground' : 'text-foreground hover:bg-muted'
                }`
              }
              data-testid={`nav-${item.id}`}>
              <span>{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-2 mb-2">
            {user.picture ? (
              <img src={user.picture} alt="" className="w-7 h-7 rounded-full" />
            ) : (
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary">
                {user.name?.[0]?.toUpperCase() || 'U'}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">{user.name}</p>
              <p className="text-[10px] text-muted-foreground truncate">{user.email}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            data-testid="logout-btn">Sign out</button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
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
