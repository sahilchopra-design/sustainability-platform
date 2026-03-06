import React, { useState, useEffect, useRef, useCallback } from 'react';
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
import UnifiedValuationPage from './features/valuation/pages/UnifiedValuationPage';
import SustainabilityPage from './features/sustainability/pages/SustainabilityPage';
import ScenarioAnalysisPage from './features/scenarios/pages/ScenarioAnalysisPage';
import PortfolioAnalyticsPage from './features/portfolio-analytics/pages/PortfolioAnalyticsPage';
import FinancialRiskPage from './features/financial-risk/pages/FinancialRiskPage';
import RealEstateAssessmentPage from './features/real-estate/pages/RealEstateAssessmentPage';
import SupplyChainPage from './features/supply-chain/pages/SupplyChainPage';
import SectorAssessmentsPage from './features/supply-chain/pages/SectorAssessmentsPage';
import RegulatoryPage from './features/regulatory/pages/RegulatoryPage';
import InteractiveDashboard from './pages/InteractiveDashboard';
import PortfolioHealthPage from './features/portfolio-health/pages/PortfolioHealthPage';
import GlidepathTrackerPage from './features/glidepath/GlidepathTrackerPage';
import PeerBenchmarkPage from './features/regulatory/pages/PeerBenchmarkPage';
import AnalystPortfoliosPage from './features/portfolio-analytics/AnalystPortfoliosPage';
import CompanyProfilesPage from './features/company-profiles/CompanyProfilesPage';
import DataIntakeDashboard from './features/data-intake/pages/DataIntakeDashboard';
import LoanPortfolioUpload from './features/data-intake/pages/LoanPortfolioUpload';
import CounterpartyEmissionsWizard from './features/data-intake/pages/CounterpartyEmissionsWizard';
import RealEstateEUIUpload from './features/data-intake/pages/RealEstateEUIUpload';
import ShippingFleetUpload from './features/data-intake/pages/ShippingFleetUpload';
import SteelBorrowersEntry from './features/data-intake/pages/SteelBorrowersEntry';
import ProjectFinanceIntake from './features/data-intake/pages/ProjectFinanceIntake';
import InternalConfigPage from './features/data-intake/pages/InternalConfigPage';
import EngagementTrackerPage from './features/financial-risk/pages/EngagementTrackerPage';
import MonteCarloPage from './features/risk/MonteCarloPage';
import ScenarioBuilderPage from './features/scenario-builder/pages/ScenarioBuilderPage';
import ScenarioGalleryPage from './features/scenario-builder/pages/ScenarioGalleryPage';
import AsiaRegulatoryPage from './pages/AsiaRegulatoryPage';
import ChinaTradePage from './pages/ChinaTradePage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

// ─── Nav structure ────────────────────────────────────────────────────────────

const NAV_GROUPS = [
  {
    label: 'Pulse',
    items: [
      { to: '/portfolio-health',   icon: 'activity',      label: 'Portfolio Health',      badge: 'NEW' },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { to: '/interactive',        icon: 'bar-chart',     label: 'Interactive Analytics', badge: 'LIVE' },
      { to: '/',                   icon: 'layout',        label: 'Overview Dashboard',   end: true },
      { to: '/impact',             icon: 'target',        label: 'Impact Calculator' },
      { to: '/portfolio-analytics',icon: 'pie-chart',     label: 'Portfolio Analytics' },
      { to: '/analyst-portfolios', icon: 'briefcase',     label: 'Analyst Workbench',    badge: 'NEW' },
      { to: '/glidepath-tracker',  icon: 'trending-up',   label: 'Glidepath Tracker',    badge: 'NEW' },
      { to: '/scenario-analysis',  icon: 'calculator',    label: 'Scenario Analysis' },
      { to: '/sub-analysis',       icon: 'microscope',    label: 'Sub-Parameter' },
    ],
  },
  {
    label: 'ESG Modules',
    items: [
      { to: '/carbon',             icon: 'leaf',          label: 'Carbon Credits' },
      { to: '/nature-risk',        icon: 'tree',          label: 'Nature Risk (TNFD)' },
      { to: '/stranded-assets',    icon: 'trending-down', label: 'Stranded Assets' },
      { to: '/valuation',          icon: 'building',      label: 'Asset Valuation' },
      { to: '/sustainability',     icon: 'award',         label: 'Sustainability (GRESB)' },
      { to: '/cbam',               icon: 'globe',         label: 'CBAM Calculator' },
    ],
  },
  {
    label: 'Risk & Sector',
    items: [
      { to: '/monte-carlo',             icon: 'cpu',       label: 'Monte Carlo Simulation',   badge: 'NEW' },
      { to: '/financial-risk',          icon: 'shield',    label: 'Financial Risk (ECL/PCAF)' },
      { to: '/real-estate-assessment',  icon: 'home',      label: 'Real Estate (RICS/CRREM)' },
      { to: '/supply-chain',            icon: 'truck',     label: 'Supply Chain Scope 3' },
      { to: '/sector-assessments',      icon: 'server',    label: 'Sector Assessments' },
      { to: '/engagement-tracker',      icon: 'users',     label: 'Engagement Tracker',       badge: 'NEW' },
    ],
  },
  {
    label: 'Regulatory',
    items: [
      { to: '/regulatory',        icon: 'file-text',  label: 'Regulatory Reporting',  badge: 'SFDR·CSRD·ISSB' },
      { to: '/asia-regulatory',   icon: 'globe',      label: 'Asia Regulatory',        badge: 'BRSR·HKMA·CBI' },
      { to: '/peer-benchmark',    icon: 'users',       label: 'Peer Benchmark',         badge: 'NEW' },
      { to: '/company-profiles',  icon: 'building',    label: 'Company Profiles',        badge: 'NEW' },
    ],
  },
  {
    label: 'Scenarios & Data',
    items: [
      { to: '/scenario-gallery',     icon: 'layers',       label: 'Scenario Gallery',    badge: 'NEW' },
      { to: '/scenario-builder-v2',  icon: 'wrench',       label: 'Scenario Builder v2', badge: 'NEW' },
      { to: '/browser',       icon: 'search',       label: 'Scenario Browser' },
      { to: '/data-hub',      icon: 'database',     label: 'Data Hub' },
      { to: '/ngfs',          icon: 'globe',        label: 'NGFS Catalog' },
      { to: '/comparison',    icon: 'git-compare',  label: 'Comparison' },
      { to: '/custom-builder',icon: 'wrench',       label: 'Custom Builder' },
    ],
  },
  {
    label: 'Portfolio',
    items: [
      { to: '/portfolios',        icon: 'briefcase', label: 'Portfolios' },
      { to: '/portfolio-manager', icon: 'upload',    label: 'Upload & Edit' },
      { to: '/analysis',          icon: 'bar-chart', label: 'Run Analysis' },
    ],
  },
  {
    label: 'Data Intake',
    items: [
      { to: '/data-intake',                icon: 'database',   label: 'Overview',              badge: 'NEW' },
      { to: '/data-intake/portfolio',      icon: 'upload',     label: 'Loan Portfolio' },
      { to: '/data-intake/counterparty',   icon: 'users',      label: 'Counterparty Emissions' },
      { to: '/data-intake/real-estate',    icon: 'home',       label: 'Real Estate EUI' },
      { to: '/data-intake/shipping-fleet', icon: 'anchor',     label: 'Shipping Fleet' },
      { to: '/data-intake/steel-borrowers',icon: 'tool',       label: 'Steel Borrowers' },
      { to: '/data-intake/project-finance',icon: 'zap',        label: 'Project Finance' },
      { to: '/data-intake/internal-config',icon: 'settings',   label: 'Internal Config' },
    ],
  },
  {
    label: 'China Trade',
    items: [
      { to: '/china-trade', icon: 'globe', label: 'China Trade Platform', badge: 'CBAM·CETS·ESG' },
    ],
  },
];

// ─── Auth callback ────────────────────────────────────────────────────────────

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

  return (
    <div className="flex items-center justify-center h-screen bg-[#060c18] text-cyan-400 font-mono text-sm">
      <div className="flex items-center gap-3">
        <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        Authenticating…
      </div>
    </div>
  );
}

// ─── Route title map ──────────────────────────────────────────────────────────

const ROUTE_TITLES = {
  '/':                      'Overview Dashboard',
  '/interactive':           'Interactive Analytics',
  '/portfolios':            'Portfolios',
  '/analysis':              'Run Analysis',
  '/scenario-data':         'Scenario Data',
  '/scenario-builder':      'Scenario Builder',
  '/data-hub':              'Data Hub',
  '/browser':               'Scenario Browser',
  '/comparison':            'Comparison',
  '/impact':                'Impact Calculator',
  '/portfolio-manager':     'Portfolio Manager',
  '/alerts':                'Alerts',
  '/ngfs':                  'NGFS Catalog',
  '/custom-builder':        'Custom Builder',
  '/sub-analysis':          'Sub-Parameter Analysis',
  '/cbam':                  'CBAM Calculator',
  '/carbon':                'Carbon Credits',
  '/nature-risk':           'Nature Risk (TNFD)',
  '/stranded-assets':       'Stranded Assets',
  '/valuation':             'Asset Valuation',
  '/sustainability':        'Sustainability',
  '/scenario-analysis':     'Scenario Analysis',
  '/portfolio-analytics':   'Portfolio Analytics',
  '/financial-risk':        'Financial Risk — ECL / PCAF',
  '/real-estate-assessment':'Real Estate Assessment (RICS / CRREM)',
  '/supply-chain':          'Supply Chain — Scope 3',
  '/sector-assessments':    'Sector Assessments',
  '/regulatory':            'Regulatory Reporting',
  '/peer-benchmark':        'Peer Benchmark Gap Assessment',
  '/analyst-portfolios':    'Analyst Portfolio Workbench',
  '/company-profiles':      'Company Profiles',
  '/glidepath-tracker':     'Glidepath Tracker',
  '/engagement-tracker':    'Engagement Tracker',
  '/monte-carlo':           'Monte Carlo Simulation — P5/P25/P50/P75/P95',
  '/scenario-builder-v2':  'Scenario Builder v2 — NGFS Phase IV',
  '/scenario-gallery':     'Scenario Gallery',
  '/asia-regulatory':      'Asia-Pacific Regulatory Frameworks',
  '/china-trade':          'China Trade & Sustainability Platform',
};

// ─── Backend health hook ──────────────────────────────────────────────────────

function useBackendHealth() {
  const [status, setStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  useEffect(() => {
    let cancelled = false;
    const check = () => {
      fetch(`${API_URL}/api/health`, { signal: AbortSignal.timeout(3000) })
        .then(r => { if (!cancelled) setStatus(r.ok ? 'online' : 'offline'); })
        .catch(() => { if (!cancelled) setStatus('offline'); });
    };
    check();
    const id = setInterval(check, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);
  return status;
}

// ─── Top header ───────────────────────────────────────────────────────────────

function TopHeader({ user, onLogout, sidebarOpen, onToggleSidebar }) {
  const location = useLocation();
  const navigate = useNavigate();
  const backendStatus = useBackendHealth();
  const title = ROUTE_TITLES[location.pathname] || 'Analytics Platform';

  return (
    <header className="h-11 bg-[#070d1a] border-b border-white/[0.06] flex items-center px-3 gap-3 shrink-0 z-10">
      {/* Sidebar toggle */}
      <button
        onClick={onToggleSidebar}
        className="text-white/40 hover:text-white/80 transition-colors p-1 rounded hover:bg-white/5"
        title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round"
            d={sidebarOpen
              ? 'M4 6h16M4 12h16M4 18h16'
              : 'M4 6h16M4 12h16M4 18h16'} />
        </svg>
      </button>

      {/* Page title */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-xs text-white/30">A2 Intelligence</span>
        <span className="text-white/20 text-xs">/</span>
        <span className="text-xs font-medium text-white/80 truncate">{title}</span>
      </div>

      <div className="flex-1" />

      {/* Backend status */}
      <div className="flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${
          backendStatus === 'online'   ? 'bg-emerald-400 shadow-[0_0_4px_#34d399]' :
          backendStatus === 'offline'  ? 'bg-red-400' :
          'bg-amber-400 animate-pulse'
        }`} />
        <span className="text-[10px] text-white/30 font-mono">
          {backendStatus === 'online' ? 'API LIVE' : backendStatus === 'offline' ? 'API OFFLINE' : 'CONNECTING'}
        </span>
      </div>

      <div className="w-px h-4 bg-white/10" />

      {/* Current date */}
      <span className="text-[10px] text-white/25 font-mono tabular-nums hidden sm:block">
        {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
      </span>

      <div className="w-px h-4 bg-white/10" />

      {/* User avatar + logout */}
      <div className="flex items-center gap-2">
        {user?.picture ? (
          <img src={user.picture} alt="" className="w-6 h-6 rounded-full ring-1 ring-white/10" />
        ) : (
          <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center text-[10px] font-medium text-cyan-300 ring-1 ring-cyan-500/30">
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
        )}
        <span className="text-[11px] text-white/50 hidden md:block truncate max-w-[120px]">{user?.name}</span>
        <button
          onClick={onLogout}
          title="Sign out"
          className="text-white/25 hover:text-white/60 transition-colors p-1 rounded hover:bg-white/5"
          data-testid="logout-btn"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </header>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

function Sidebar({ open, user }) {
  return (
    <aside className={`bg-[#060c18] flex flex-col shrink-0 border-r border-white/[0.06] transition-all duration-200 ${
      open ? 'w-56' : 'w-12'
    }`}>
      {/* Brand */}
      <div className={`h-11 border-b border-white/[0.06] flex items-center shrink-0 ${open ? 'px-3 gap-2.5' : 'justify-center'}`}>
        <div className="w-6 h-6 rounded bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
          <svg className="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
        {open && (
          <div className="min-w-0">
            <p className="text-[12px] font-semibold text-white/90 tracking-tight leading-none">A2 Intelligence</p>
            <p className="text-[9px] text-cyan-400/50 mt-0.5">by AA Impact Inc.</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-2 space-y-3 px-1.5 scrollbar-none">
        {NAV_GROUPS.map(group => (
          <NavGroup key={group.label} label={group.label} open={open}>
            {group.items.map(item => (
              <SideLink key={item.to} {...item} sidebarOpen={open} />
            ))}
          </NavGroup>
        ))}
      </nav>

      {/* Footer */}
      {open && (
        <div className="p-2 border-t border-white/[0.06] shrink-0">
          <div className="flex items-center gap-1.5">
            <img src="/aa-impact-logo.jpg" alt="AA Impact" className="h-4 w-4 rounded object-cover opacity-60" />
            <span className="text-[9px] text-white/20">AA Impact Inc. © 2025</span>
          </div>
        </div>
      )}
    </aside>
  );
}

function NavGroup({ label, open, children }) {
  if (!open) {
    return <div className="space-y-0.5">{children}</div>;
  }
  return (
    <div>
      <p className="text-[9px] font-semibold text-white/20 uppercase tracking-[0.12em] mb-1 px-1.5 truncate">{label}</p>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

function SideLink({ to, icon, label, end, badge, sidebarOpen }) {
  const d = ICON_MAP[icon] || ICON_MAP.layout;
  return (
    <NavLink
      to={to}
      end={end}
      title={!sidebarOpen ? label : undefined}
      className={({ isActive }) =>
        `flex items-center rounded transition-all group relative ${
          sidebarOpen ? 'gap-2 px-2 py-1.5' : 'justify-center px-0 py-2'
        } ${
          isActive
            ? 'bg-cyan-500/10 text-cyan-300'
            : 'text-white/45 hover:text-white/80 hover:bg-white/[0.04]'
        }`
      }
      data-testid={`nav-${to.replace('/', '') || 'dashboard'}`}
    >
      <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d={d} />
      </svg>
      {sidebarOpen && (
        <>
          <span className="text-[12px] truncate flex-1">{label}</span>
          {badge && (
            <span className="text-[8px] font-mono font-bold text-cyan-400/60 bg-cyan-400/10 px-1 py-0.5 rounded shrink-0 leading-none">
              {badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

// ─── Main app router ──────────────────────────────────────────────────────────

function AppRouter() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [isCallback, setIsCallback] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.hash?.includes('session_id=')) {
      setIsCallback(true);
      setChecking(false);
      return;
    }
    const token = localStorage.getItem('session_token');
    if (!token) { setChecking(false); return; }

    // Dev bypass token — skip backend validation in development builds
    if (token === 'dev-bypass-local' && process.env.NODE_ENV === 'development') {
      setUser({ name: 'Developer', email: 'dev@local', role: 'admin', picture: null });
      setChecking(false);
      return;
    }

    fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => { setUser(data); setChecking(false); })
      .catch(() => { localStorage.removeItem('session_token'); setChecking(false); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = useCallback(async () => {
    const token = localStorage.getItem('session_token');
    await fetch(`${API_URL}/api/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    }).catch(() => {});
    localStorage.removeItem('session_token');
    setUser(null);
  }, []);

  if (isCallback) return <AuthCallback onAuth={setUser} />;

  if (checking) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#060c18] text-white/30 font-mono text-xs">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
          Loading platform…
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onAuth={(data) => setUser(data)} />;
  }

  return (
    <div className="flex h-screen bg-[#060c18] overflow-hidden">
      <Sidebar open={sidebarOpen} user={user} />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopHeader
          user={user}
          onLogout={handleLogout}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(v => !v)}
        />

        {/* Page content */}
        <main className="flex-1 overflow-auto bg-[#080e1c]">
          <Routes>
            <Route path="/"                        element={<Dashboard />} />
            <Route path="/portfolios"              element={<Portfolios />} />
            <Route path="/portfolios/:id"          element={<PortfolioDetail />} />
            <Route path="/analysis"                element={<Analysis />} />
            <Route path="/results/:runId"          element={<Results />} />
            <Route path="/scenario-data"           element={<ScenarioData />} />
            <Route path="/scenario-builder"        element={<ScenarioBuilder />} />
            <Route path="/data-hub"                element={<DataHub />} />
            <Route path="/browser"                 element={<ScenarioBrowserPage />} />
            <Route path="/comparison"              element={<ComparisonPage />} />
            <Route path="/impact"                  element={<ImpactCalculatorPage />} />
            <Route path="/portfolio-manager"       element={<PortfolioManagerPage />} />
            <Route path="/alerts"                  element={<AlertsPage />} />
            <Route path="/ngfs"                    element={<NGFSScenariosPage />} />
            <Route path="/custom-builder"          element={<CustomBuilderPage />} />
            <Route path="/sub-analysis"            element={<SubAnalysisPage />} />
            <Route path="/cbam"                    element={<CBAMPage />} />
            <Route path="/carbon"                  element={<CarbonDashboard />} />
            <Route path="/nature-risk"             element={<NatureRiskPage />} />
            <Route path="/stranded-assets"         element={<StrandedAssetsPage />} />
            <Route path="/valuation"               element={<UnifiedValuationPage />} />
            <Route path="/sustainability"          element={<SustainabilityPage />} />
            <Route path="/scenario-analysis"       element={<ScenarioAnalysisPage />} />
            <Route path="/portfolio-analytics"     element={<PortfolioAnalyticsPage />} />
            <Route path="/financial-risk"          element={<FinancialRiskPage />} />
            <Route path="/real-estate-assessment"  element={<RealEstateAssessmentPage />} />
            <Route path="/supply-chain"            element={<SupplyChainPage />} />
            <Route path="/sector-assessments"      element={<SectorAssessmentsPage />} />
            <Route path="/regulatory"              element={<RegulatoryPage />} />
            <Route path="/interactive"             element={<InteractiveDashboard />} />
            <Route path="/portfolio-health"        element={<PortfolioHealthPage />} />
            <Route path="/glidepath-tracker"       element={<GlidepathTrackerPage />} />
            <Route path="/peer-benchmark"          element={<PeerBenchmarkPage />} />
            <Route path="/analyst-portfolios"      element={<AnalystPortfoliosPage />} />
            <Route path="/company-profiles"        element={<CompanyProfilesPage />} />
            {/* Category C — Data Intake */}
            <Route path="/data-intake"                element={<DataIntakeDashboard />} />
            <Route path="/data-intake/portfolio"      element={<LoanPortfolioUpload />} />
            <Route path="/data-intake/counterparty"   element={<CounterpartyEmissionsWizard />} />
            <Route path="/data-intake/real-estate"    element={<RealEstateEUIUpload />} />
            <Route path="/data-intake/shipping-fleet" element={<ShippingFleetUpload />} />
            <Route path="/data-intake/steel-borrowers" element={<SteelBorrowersEntry />} />
            <Route path="/data-intake/project-finance" element={<ProjectFinanceIntake />} />
            <Route path="/data-intake/internal-config" element={<InternalConfigPage />} />
            {/* Category D — Engagement Tracker */}
            <Route path="/engagement-tracker"          element={<EngagementTrackerPage />} />
            {/* P2 — Monte Carlo Simulation */}
            <Route path="/monte-carlo"                 element={<MonteCarloPage />} />
            {/* Scenario Builder v2 — NGFS Phase IV */}
            <Route path="/scenario-builder-v2"        element={<ScenarioBuilderPage />} />
            <Route path="/scenario-gallery"           element={<ScenarioGalleryPage />} />
            {/* Asia Regulatory — BRSR / HKMA / BoJ / ASEAN / PBoC / CBI */}
            <Route path="/asia-regulatory"            element={<AsiaRegulatoryPage />} />
            {/* China Trade Platform — standalone module */}
            <Route path="/china-trade"                element={<ChinaTradePage />} />
          </Routes>
        </main>
      </div>
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

// ─── Icon map ─────────────────────────────────────────────────────────────────

const ICON_MAP = {
  activity:      'M22 12h-4l-3 9L9 3l-3 9H2',
  layout:        'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z',
  target:        'M12 2a10 10 0 100 20 10 10 0 000-20zm0 4a6 6 0 100 12 6 6 0 000-12zm0 4a2 2 0 100 4 2 2 0 000-4z',
  microscope:    'M9 2v6h2V2H9zm-1 8a4 4 0 108 0H8zm-4 8h16v2H4v-2z',
  search:        'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  database:      'M4 7v10c0 2 3.6 4 8 4s8-2 8-4V7M4 7c0 2 3.6 4 8 4s8-2 8-4M4 7c0-2 3.6-4 8-4s8 2 8 4',
  globe:         'M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2a15 15 0 014 10 15 15 0 01-4 10 15 15 0 01-4-10A15 15 0 0112 2z',
  'git-compare': 'M18 21a3 3 0 100-6 3 3 0 000 6zM6 9a3 3 0 100-6 3 3 0 000 6zm12 3V9a3 3 0 00-3-3h-4M6 15v-3',
  wrench:        'M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z',
  briefcase:     'M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2',
  upload:        'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12',
  'bar-chart':   'M18 20V10M12 20V4M6 20v-6',
  bell:          'M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0',
  layers:        'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  archive:       'M21 8v13H3V8M1 3h22v5H1zM10 12h4',
  leaf:          'M11 20A7 7 0 019.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10zM2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12',
  tree:          'M12 22v-7m0 0c-3.5 0-6-2.5-6-6 0-2 1-4 3-5.5C10 2.5 11 2 12 2s2 .5 3 1.5c2 1.5 3 3.5 3 5.5 0 3.5-2.5 6-6 6z',
  'trending-down':'M23 18l-9.5-9.5-5 5L1 6M17 18h6v-6',
  'trending-up':  'M23 6l-9.5 9.5-5-5L1 18M17 6h6v6',
  building:      'M3 21h18M5 21V7l8-4v18M19 21V11l-6-4M9 9v.01M9 12v.01M9 15v.01M9 18v.01',
  award:         'M12 15l-2 5-1.5-4-4.5 1.5L6 13 2 11l4-2L4 4.5 8.5 6 10 2l2 5 2-5 1.5 4 4.5-1.5L18 9l4 2-4 2 2 4.5-4.5-1.5L14 20l-2-5z',
  calculator:    'M4 2h16a2 2 0 012 2v16a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2zm3 4h10M7 10h2M7 14h2M7 18h2M15 10h2M15 14h2M15 18h2M11 10h2M11 14h2M11 18h2',
  cpu:           'M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18',
  'pie-chart':   'M21.21 15.89A10 10 0 118 2.83M22 12A10 10 0 0012 2v10z',
  shield:        'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  home:          'M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9zM9 22V12h6v10',
  truck:         'M1 3h15v13H1V3zM16 8h4l3 3v5h-7V8zM5.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM18.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3z',
  server:        'M2 2h20v8H2V2zm0 12h20v8H2v-8zm5 4h.01M5 6h.01',
  'file-text':   'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zM14 2v6h6M16 13H8M16 17H8M10 9H8',
  users:         'M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zm8 4a3 3 0 100-6 3 3 0 000 6zm3 2v-1a3 3 0 00-3-3h-1',
};

export default App;
