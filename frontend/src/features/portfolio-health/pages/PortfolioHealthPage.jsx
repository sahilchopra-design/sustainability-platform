/**
 * Portfolio Health Page — Sustainability Pulse
 *
 * Displays the three WHOOP-style health scores for a selected portfolio,
 * the alert feed, and score trend sparklines.
 *
 * Route: /portfolio-health
 *
 * Data sources:
 *   GET /api/v1/portfolio-health/{id}/scores     → three scores
 *   GET /api/v1/portfolio-health/{id}/alerts     → alert feed
 *   GET /api/v1/portfolio-health/{id}/history    → sparkline data
 *   PATCH /api/v1/portfolio-health/alerts/{id}/read
 *   PATCH /api/v1/portfolio-health/{id}/read-all
 *
 * Polls scores every 60 seconds (low-frequency — not real-time).
 */
import React, { useState, useEffect, useCallback } from 'react';
import { HealthScoreCard } from '../components/HealthScoreCard';
import { AlertFeed } from '../components/AlertFeed';
import { ScoreTrendChart } from '../components/ScoreTrendChart';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';
const POLL_MS = 60_000; // 1 minute

// ── Mini KPI strip ─────────────────────────────────────────────────────────────
function KpiStrip({ label, value, unit, colour }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] text-white/40 uppercase tracking-wider mb-0.5">{label}</span>
      <span className="text-base font-semibold tabular-nums" style={{ color: colour, fontFamily: 'IBM Plex Mono, monospace' }}>
        {value ?? '—'}
        {unit && <span className="text-xs text-white/30 ml-1">{unit}</span>}
      </span>
    </div>
  );
}

// ── Portfolio selector ─────────────────────────────────────────────────────────
function PortfolioSelector({ portfolios, selected, onChange }) {
  return (
    <select
      value={selected || ''}
      onChange={e => onChange(e.target.value)}
      className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-[#38bdf8] transition-colors"
      data-testid="portfolio-health-selector"
    >
      <option value="">Select portfolio…</option>
      {portfolios.map(p => (
        <option key={p.id} value={p.id}>{p.name}</option>
      ))}
    </select>
  );
}

export default function PortfolioHealthPage() {
  const [portfolios, setPortfolios]         = useState([]);
  const [selectedId, setSelectedId]         = useState(null);
  const [scores, setScores]                 = useState(null);
  const [alerts, setAlerts]                 = useState([]);
  const [history, setHistory]               = useState([]);
  const [loadingScores, setLoadingScores]   = useState(false);
  const [loadingAlerts, setLoadingAlerts]   = useState(false);
  const [lastRefresh, setLastRefresh]       = useState(null);
  const [error, setError]                   = useState(null);

  // Load portfolio list on mount
  useEffect(() => {
    fetch(`${API_URL}/api/portfolios`)
      .then(r => r.json())
      .then(data => {
        const list = data.portfolios || [];
        setPortfolios(list);
        if (list.length > 0 && !selectedId) {
          setSelectedId(list[0].id);
        }
      })
      .catch(() => setError('Failed to load portfolios'));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch scores + alerts whenever selectedId changes
  const fetchHealthData = useCallback(async (portfolioId) => {
    if (!portfolioId) return;
    setLoadingScores(true);
    setLoadingAlerts(true);
    setError(null);

    try {
      const [scoresRes, alertsRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/portfolio-health/${portfolioId}/scores`),
        fetch(`${API_URL}/api/v1/portfolio-health/${portfolioId}/alerts?limit=20`),
        fetch(`${API_URL}/api/v1/portfolio-health/${portfolioId}/history?weeks=12`),
      ]);

      if (scoresRes.ok) {
        const data = await scoresRes.json();
        setScores(data);
        setLastRefresh(new Date().toLocaleTimeString());
      } else {
        setError('Health scores unavailable');
      }

      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setAlerts(data.alerts || []);
      }

      if (historyRes.ok) {
        const data = await historyRes.json();
        setHistory(data.history || []);
      }
    } catch (err) {
      setError('Backend connection error');
    } finally {
      setLoadingScores(false);
      setLoadingAlerts(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId) {
      fetchHealthData(selectedId);
    }
  }, [selectedId, fetchHealthData]);

  // Poll every 60 seconds
  useEffect(() => {
    if (!selectedId) return;
    const interval = setInterval(() => fetchHealthData(selectedId), POLL_MS);
    return () => clearInterval(interval);
  }, [selectedId, fetchHealthData]);

  const handleMarkRead = async (alertId) => {
    await fetch(`${API_URL}/api/v1/portfolio-health/alerts/${alertId}/read`, {
      method: 'PATCH',
    });
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, is_read: true } : a));
  };

  const handleMarkAll = async () => {
    if (!selectedId) return;
    await fetch(`${API_URL}/api/v1/portfolio-health/${selectedId}/read-all`, {
      method: 'PATCH',
    });
    setAlerts(prev => prev.map(a => ({ ...a, is_read: true })));
  };

  const handleRefresh = () => {
    if (selectedId) fetchHealthData(selectedId);
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  return (
    <div className="min-h-screen bg-[#080e1c] p-6 space-y-6">
      {/* ── Page header ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1
            className="text-2xl font-bold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Portfolio Health
          </h1>
          <p className="text-sm text-white/40 mt-0.5">
            Continuous sustainability + financial risk monitoring
          </p>
        </div>

        <div className="flex items-center gap-3">
          <PortfolioSelector
            portfolios={portfolios}
            selected={selectedId}
            onChange={setSelectedId}
          />
          <button
            onClick={handleRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 text-xs text-white/60 hover:text-white hover:border-white/20 transition-all"
            data-testid="portfolio-health-refresh"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
            </svg>
            Refresh
          </button>
          {lastRefresh && (
            <span className="text-[10px] text-white/25 tabular-nums">
              Updated {lastRefresh}
            </span>
          )}
        </div>
      </div>

      {/* ── Error banner ──────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* ── No portfolio selected ─────────────────────────────────────────── */}
      {!selectedId && !error && (
        <div className="rounded-xl border border-white/10 bg-white/[0.02] px-8 py-16 text-center">
          <p className="text-white/40 text-sm">
            Select a portfolio above to view health scores
          </p>
        </div>
      )}

      {selectedId && (
        <>
          {/* ── Overall score banner ─────────────────────────────────────── */}
          {scores && (
            <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-6 py-4">
              <div>
                <span className="text-xs text-white/40 uppercase tracking-wider">Overall Score</span>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span
                    className="text-4xl font-bold tabular-nums"
                    style={{
                      fontFamily: "'Space Grotesk', sans-serif",
                      color: scores.overall_score >= 70 ? '#10b981' : scores.overall_score >= 40 ? '#f59e0b' : '#ef4444',
                    }}
                    data-testid="portfolio-health-overall-score"
                  >
                    {scores.overall_score?.toFixed(1)}
                  </span>
                  <span className="text-sm text-white/30">/100</span>
                </div>
              </div>
              <div className="flex items-center gap-8">
                <KpiStrip label="Portfolio" value={scores.portfolio_name} colour="#ffffff" />
                {unreadCount > 0 && (
                  <div className="flex flex-col">
                    <span className="text-[10px] text-white/40 uppercase tracking-wider mb-0.5">Alerts</span>
                    <span className="text-base font-semibold text-[#ef4444] tabular-nums">
                      {unreadCount} unread
                    </span>
                  </div>
                )}
                {!scores.data_available && (
                  <span className="text-xs text-amber-400/70 border border-amber-400/30 rounded px-2 py-0.5">
                    Limited data — run PCAF/ECL first
                  </span>
                )}
              </div>
            </div>
          )}

          {/* ── Three score gauges ───────────────────────────────────────── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <HealthScoreCard
              title="Climate Health"
              score={scores?.climate_health?.value ?? 50}
              rag={scores?.climate_health?.rag ?? 'AMBER'}
              label={scores?.climate_health?.label ?? 'Run PCAF to compute'}
              action={scores?.climate_health?.action}
              actionLink={scores?.climate_health?.action_link ?? '/portfolio-analytics'}
              loading={loadingScores}
            />
            <HealthScoreCard
              title="Financial Resilience"
              score={scores?.financial_resilience?.value ?? 50}
              rag={scores?.financial_resilience?.rag ?? 'AMBER'}
              label={scores?.financial_resilience?.label ?? 'Run ECL assessment to compute'}
              action={scores?.financial_resilience?.action}
              actionLink={scores?.financial_resilience?.action_link ?? '/financial-risk'}
              loading={loadingScores}
            />
            <HealthScoreCard
              title="Transition Readiness"
              score={scores?.transition_readiness?.value ?? 50}
              rag={scores?.transition_readiness?.rag ?? 'AMBER'}
              label={scores?.transition_readiness?.label ?? 'Add SBTi + transition plan data'}
              action={scores?.transition_readiness?.action}
              actionLink={scores?.transition_readiness?.action_link ?? '/regulatory'}
              loading={loadingScores}
            />
          </div>

          {/* ── Score trends + Alert feed ────────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            {/* Trend sparklines (3 cols) */}
            <div className="lg:col-span-3 rounded-xl border border-white/10 bg-white/[0.02] p-5">
              <h2 className="text-sm font-semibold text-white mb-4">Score Trends</h2>
              <div className="space-y-5">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-white/40">Climate Health</span>
                    <span className="text-xs tabular-nums" style={{ color: '#22d3ee' }}>
                      {scores?.climate_health?.value?.toFixed(1) ?? '—'}
                    </span>
                  </div>
                  <ScoreTrendChart data={history} metric="climate_health" colour="#22d3ee" height={56} />
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-white/40">Financial Resilience</span>
                    <span className="text-xs tabular-nums" style={{ color: '#a78bfa' }}>
                      {scores?.financial_resilience?.value?.toFixed(1) ?? '—'}
                    </span>
                  </div>
                  <ScoreTrendChart data={history} metric="financial_resilience" colour="#a78bfa" height={56} />
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-white/40">Transition Readiness</span>
                    <span className="text-xs tabular-nums" style={{ color: '#34d399' }}>
                      {scores?.transition_readiness?.value?.toFixed(1) ?? '—'}
                    </span>
                  </div>
                  <ScoreTrendChart data={history} metric="transition_readiness" colour="#34d399" height={56} />
                </div>
              </div>
              {history.length === 0 && !loadingScores && (
                <p className="text-xs text-white/25 text-center mt-4">
                  Trend data populates after PCAF calculations are run across reporting years
                </p>
              )}
            </div>

            {/* Alert feed (2 cols) */}
            <div className="lg:col-span-2 rounded-xl border border-white/10 bg-white/[0.02] p-5 overflow-y-auto max-h-[480px]">
              <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                Signal Feed
                {unreadCount > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full bg-[#ef4444] text-white text-[10px] font-bold tabular-nums">
                    {unreadCount}
                  </span>
                )}
              </h2>
              <AlertFeed
                alerts={alerts}
                onMarkRead={handleMarkRead}
                onMarkAll={handleMarkAll}
                loading={loadingAlerts}
              />
            </div>
          </div>

          {/* ── Quick Actions ────────────────────────────────────────────── */}
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
            <h2 className="text-sm font-semibold text-white mb-3">Quick Actions</h2>
            <div className="flex flex-wrap gap-3">
              {[
                { label: 'Review glidepath deviations', link: '/glidepath-tracker', colour: '#22d3ee' },
                { label: 'Improve DQS scores', link: '/portfolio-analytics', colour: '#a78bfa' },
                { label: 'Complete engagement updates', link: '/regulatory', colour: '#34d399' },
                { label: 'Run PCAF calculation', link: '/portfolio-analytics', colour: '#f59e0b' },
                { label: 'View ECL stress results', link: '/financial-risk', colour: '#ef4444' },
              ].map(({ label, link, colour }) => (
                <a
                  key={label}
                  href={link}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all hover:opacity-80"
                  style={{ borderColor: `${colour}40`, color: colour, background: `${colour}0d` }}
                >
                  {label} →
                </a>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
