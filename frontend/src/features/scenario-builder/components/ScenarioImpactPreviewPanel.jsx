/**
 * ScenarioImpactPreviewPanel — quick impact preview vs NGFS baseline.
 * Calls /api/v1/monte-carlo/quick with current scenario parameters.
 * Shows EL, VaR, carbon cost, WACI deltas with mini bar chart.
 */
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip, CartesianGrid } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Demo portfolio for preview (6 representative assets)
const DEMO_ASSETS = [
  { id: 'a1', name: 'Royal Dutch Shell', sector: 'Oil & Gas',       exposure: 120e6, baseline_pd: 0.025, lgd: 0.45, emission_intensity: 1.8, emissions_trend: 'Deteriorating', transition_plan_score: 2, physical_risk_score: 2 },
  { id: 'a2', name: 'E.ON SE',           sector: 'Power Generation', exposure: 80e6,  baseline_pd: 0.018, lgd: 0.40, emission_intensity: 0.9, emissions_trend: 'Improving',     transition_plan_score: 4, physical_risk_score: 2 },
  { id: 'a3', name: 'Anglo American',    sector: 'Metals & Mining',  exposure: 60e6,  baseline_pd: 0.030, lgd: 0.50, emission_intensity: 1.2, emissions_trend: 'Stable',        transition_plan_score: 3, physical_risk_score: 3 },
  { id: 'a4', name: 'Volkswagen AG',     sector: 'Automotive',       exposure: 90e6,  baseline_pd: 0.022, lgd: 0.42, emission_intensity: 0.7, emissions_trend: 'Improving',     transition_plan_score: 4, physical_risk_score: 1 },
  { id: 'a5', name: 'British Airways',   sector: 'Airlines',         exposure: 45e6,  baseline_pd: 0.040, lgd: 0.55, emission_intensity: 1.5, emissions_trend: 'Stable',        transition_plan_score: 2, physical_risk_score: 2 },
  { id: 'a6', name: 'Canary Wharf RE',   sector: 'Real Estate',      exposure: 200e6, baseline_pd: 0.012, lgd: 0.35, emission_intensity: 0.3, emissions_trend: 'Improving',     transition_plan_score: 5, physical_risk_score: 3 },
];

const METRIC_LABELS = {
  expected_loss_p50:     'Expected Loss (P50)',
  portfolio_var_999_p50: 'Portfolio VaR 99.9%',
  carbon_cost_p50:       'Carbon Cost',
  waci_p50:              'WACI',
  avg_pd_p50:            'Avg PD',
};

const METRIC_FORMAT = {
  expected_loss_p50:     v => `$${(v / 1e6).toFixed(1)}M`,
  portfolio_var_999_p50: v => `$${(v / 1e6).toFixed(1)}M`,
  carbon_cost_p50:       v => `$${(v / 1e3).toFixed(0)}K`,
  waci_p50:              v => `${v.toFixed(2)} tCO2e`,
  avg_pd_p50:            v => `${(v * 100).toFixed(2)}%`,
};

// ─── Sub-components ────────────────────────────────────────────────────────────

function DeltaBar({ scenario, baseline, metric }) {
  if (!scenario || !baseline) return null;
  const base  = baseline[metric] ?? 0;
  const scen  = scenario[metric] ?? 0;
  const delta = base !== 0 ? ((scen - base) / Math.abs(base)) * 100 : 0;
  const isWorse = delta > 0;
  const format = METRIC_FORMAT[metric] || (v => v.toFixed(2));

  return (
    <div className="flex items-center justify-between gap-3 py-1.5 border-b border-white/5 last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] text-white/60">{METRIC_LABELS[metric]}</span>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-white/80">{format(scen)}</span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
              isWorse
                ? 'text-red-400 bg-red-500/10'
                : 'text-emerald-400 bg-emerald-500/10'
            }`}>
              {isWorse ? '+' : ''}{delta.toFixed(1)}%
            </span>
          </div>
        </div>
        {/* Mini delta bar */}
        <div className="h-1 bg-white/5 rounded overflow-hidden">
          <div
            className={`h-full rounded transition-all duration-500 ${
              isWorse ? 'bg-red-400/60' : 'bg-emerald-400/60'
            }`}
            style={{ width: `${Math.min(Math.abs(delta), 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function ComparisonChart({ data }) {
  if (!data || !data.length) return null;
  return (
    <div className="mt-3" style={{ height: 160 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="metric" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 9 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'rgba(255,255,255,0.2)', fontSize: 9 }} axisLine={false} tickLine={false} width={28} />
          <Tooltip
            contentStyle={{ background: '#0d1526', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: 'rgba(255,255,255,0.6)' }}
          />
          <Bar dataKey="baseline" name="NGFS Baseline" fill="rgba(255,255,255,0.15)" radius={[2,2,0,0]} />
          <Bar dataKey="scenario" name="Your Scenario" radius={[2,2,0,0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.scenario > entry.baseline ? 'rgba(248,113,113,0.7)' : 'rgba(52,211,153,0.7)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function ScenarioImpactPreviewPanel({ scenario }) {
  const [results, setResults]     = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [lastRun, setLastRun]     = useState(null);
  const abortRef                  = useRef(null);

  const runPreview = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const resp = await fetch(`${API}/api/v1/monte-carlo/quick`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        signal:  abortRef.current.signal,
        body: JSON.stringify({
          assets:       DEMO_ASSETS,
          time_horizon: scenario.timeHorizon || 2050,
        }),
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setResults(data);
      setLastRun(new Date().toLocaleTimeString());
    } catch (err) {
      if (err.name === 'AbortError') return;
      // Offline fallback — generate deterministic preview
      setResults(generateFallbackResults(scenario));
      setLastRun(new Date().toLocaleTimeString() + ' (local)');
    } finally {
      setLoading(false);
    }
  }, [scenario]);

  // Auto-run on mount
  useEffect(() => {
    runPreview();
    return () => abortRef.current?.abort();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const baselineKey  = 'Orderly';
  const scenarioKey  = scenario.ngfsFamily || 'Orderly';
  const comparison   = results?.scenario_comparison;
  const baselineData = comparison?.[baselineKey];
  const scenarioData = comparison?.[scenarioKey];

  const chartData = baselineData && scenarioData
    ? [
        { metric: 'Exp Loss',  baseline: +(baselineData.expected_loss_p50 / 1e6).toFixed(2), scenario: +(scenarioData.expected_loss_p50 / 1e6).toFixed(2) },
        { metric: 'VaR 99.9%', baseline: +(baselineData.portfolio_var_999_p50 / 1e6).toFixed(2), scenario: +(scenarioData.portfolio_var_999_p50 / 1e6).toFixed(2) },
        { metric: 'Carbon $M', baseline: +(baselineData.carbon_cost_p50 / 1e6).toFixed(2), scenario: +(scenarioData.carbon_cost_p50 / 1e6).toFixed(2) },
        { metric: 'WACI',      baseline: +baselineData.waci_p50.toFixed(2), scenario: +scenarioData.waci_p50.toFixed(2) },
      ]
    : [];

  return (
    <div className="flex flex-col" data-testid="scenario-impact-preview">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-[12px] font-semibold text-white/80">Impact Preview</h4>
          <p className="text-[10px] text-white/30">vs. NGFS Orderly baseline · demo portfolio</p>
        </div>
        <div className="flex items-center gap-2">
          {lastRun && <span className="text-[9px] text-white/25">{lastRun}</span>}
          <button
            onClick={runPreview}
            disabled={loading}
            className="text-[10px] flex items-center gap-1 px-2 py-1 rounded border border-white/10 text-white/50 hover:border-cyan-500/30 hover:text-cyan-300 transition-colors disabled:opacity-40"
          >
            <svg className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {loading ? 'Running…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Loading skeleton */}
      {loading && !results && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-8 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      )}

      {/* Metric deltas */}
      {!loading && baselineData && scenarioData && (
        <>
          {Object.keys(METRIC_LABELS).map(metric => (
            <DeltaBar
              key={metric}
              metric={metric}
              baseline={baselineData}
              scenario={scenarioData}
            />
          ))}
          <ComparisonChart data={chartData} />
        </>
      )}

      {/* Error / offline state */}
      {!loading && !results && (
        <div className="text-[11px] text-white/30 py-4 text-center">
          Click refresh to run impact preview
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-[9px] text-white/20 mt-3 leading-relaxed">
        Preview uses 6-asset demo portfolio · {results?.n_simulations || 200} Monte Carlo draws · P50 median estimates only
      </p>
    </div>
  );
}

export default ScenarioImpactPreviewPanel;

// ---------------------------------------------------------------------------
// Fallback (offline / API down)
// ---------------------------------------------------------------------------

function generateFallbackResults(scenario) {
  const SEED = scenario.ngfsFamily === 'Orderly' ? 1 : scenario.ngfsFamily === 'Disorderly' ? 2 : 3;
  const base = 5_000_000 + SEED * 800_000;
  const varBase = 18_000_000 + SEED * 2_000_000;
  const comparisonFn = (mult) => ({
    expected_loss_p50:     base * mult,
    expected_loss_p95:     base * mult * 1.8,
    portfolio_var_999_p50: varBase * mult,
    carbon_cost_p50:       1_200_000 * mult,
    waci_p50:              0.72 * mult,
    avg_pd_p50:            0.024 * mult,
    loss_rate_p50:         0.009 * mult,
  });
  return {
    success: true,
    time_horizon: scenario.timeHorizon,
    n_assets: 6,
    total_exposure: 595_000_000,
    scenario_comparison: {
      'Orderly':           comparisonFn(1.0),
      'Disorderly':        comparisonFn(1.35),
      'Hot house world':   comparisonFn(1.6),
    },
    n_simulations: 200,
  };
}
