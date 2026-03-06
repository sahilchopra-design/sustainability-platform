/**
 * Monte Carlo Simulation Page
 * Portfolio-level probabilistic risk distribution (P5/P25/P50/P75/P95)
 * Method: Parameter Uncertainty Monte Carlo — Basel III / NGFS Phase IV / TCFD
 */

import React, { useState, useCallback } from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ReferenceLine, Cell,
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ---------------------------------------------------------------------------
// DEFAULT DEMO PORTFOLIO
// ---------------------------------------------------------------------------

const DEFAULT_ASSETS = [
  {
    id: 'a1', name: 'Royal Dutch Shell', sector: 'Oil & Gas',
    exposure: 45_000_000, baseline_pd: 0.018, lgd: 0.45,
    emission_intensity: 2.10, emissions_trend: 'Stable',
    transition_plan_score: 3, physical_risk_score: 2,
  },
  {
    id: 'a2', name: 'E.ON SE', sector: 'Power Generation',
    exposure: 38_000_000, baseline_pd: 0.012, lgd: 0.40,
    emission_intensity: 1.60, emissions_trend: 'Improving',
    transition_plan_score: 4, physical_risk_score: 3,
  },
  {
    id: 'a3', name: 'Anglo American', sector: 'Metals & Mining',
    exposure: 28_000_000, baseline_pd: 0.025, lgd: 0.50,
    emission_intensity: 1.45, emissions_trend: 'Stable',
    transition_plan_score: 3, physical_risk_score: 3,
  },
  {
    id: 'a4', name: 'Volkswagen AG', sector: 'Automotive',
    exposure: 52_000_000, baseline_pd: 0.014, lgd: 0.42,
    emission_intensity: 1.05, emissions_trend: 'Improving',
    transition_plan_score: 4, physical_risk_score: 2,
  },
  {
    id: 'a5', name: 'British Airways', sector: 'Airlines',
    exposure: 22_000_000, baseline_pd: 0.038, lgd: 0.60,
    emission_intensity: 1.75, emissions_trend: 'Deteriorating',
    transition_plan_score: 2, physical_risk_score: 3,
  },
  {
    id: 'a6', name: 'Canary Wharf RE', sector: 'Real Estate',
    exposure: 35_000_000, baseline_pd: 0.010, lgd: 0.35,
    emission_intensity: 0.58, emissions_trend: 'Improving',
    transition_plan_score: 4, physical_risk_score: 2,
  },
];

const SCENARIOS  = ['Orderly', 'Disorderly', 'Hot house world'];
const HORIZONS   = [2030, 2040, 2050];
const SECTORS    = [
  'Oil & Gas', 'Power Generation', 'Metals & Mining', 'Automotive',
  'Airlines', 'Real Estate', 'Financial Services', 'Technology',
  'Consumer Goods', 'Healthcare', 'Agriculture', 'Chemicals', 'Other',
];
const TRENDS     = ['Improving', 'Stable', 'Deteriorating'];

const SCENARIO_COLOURS = {
  'Orderly':          '#10b981',  // emerald
  'Disorderly':       '#f59e0b',  // amber
  'Hot house world':  '#ef4444',  // red
};

const PERCENTILE_COLOURS = {
  p5:  '#1e3a5f',
  p25: '#164e63',
  p50: '#0e7490',
  p75: '#0891b2',
  p95: '#22d3ee',
};

// ---------------------------------------------------------------------------
// FORMATTERS
// ---------------------------------------------------------------------------
const fmt = (n, dp = 0) =>
  n == null ? '—' : new Intl.NumberFormat('en-GB', { minimumFractionDigits: dp, maximumFractionDigits: dp }).format(n);
const fmtM = (n) => n == null ? '—' : `$${fmt(n / 1_000_000, 2)}M`;
const fmtPct = (n, dp = 2) => n == null ? '—' : `${(n * 100).toFixed(dp)}%`;
const fmtPctDirect = (n, dp = 2) => n == null ? '—' : `${parseFloat(n).toFixed(dp)}%`;

// ---------------------------------------------------------------------------
// CUSTOM TOOLTIP
// ---------------------------------------------------------------------------
function CustomTooltip({ active, payload, label, prefix = '$', dp = 2 }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d1628] border border-white/10 rounded-lg p-3 text-xs shadow-xl">
      <div className="text-white/60 mb-1 font-mono">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2 py-0.5">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-white/50">{p.name}:</span>
          <span className="text-white font-mono">
            {prefix === '$' ? fmtM(p.value) : fmtPctDirect(p.value, dp)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// FAN CHART (AreaChart with percentile bands)
// ---------------------------------------------------------------------------
function FanChart({ data, title, yLabel, prefix = '$' }) {
  if (!data?.length) return null;
  return (
    <div>
      <div className="text-xs text-white/50 mb-3 font-mono">{title}</div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="g5_25" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0e7490" stopOpacity={0.12} />
              <stop offset="100%" stopColor="#0e7490" stopOpacity={0.04} />
            </linearGradient>
            <linearGradient id="g25_75" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0891b2" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#0891b2" stopOpacity={0.10} />
            </linearGradient>
            <linearGradient id="g75_95" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0e7490" stopOpacity={0.12} />
              <stop offset="100%" stopColor="#0e7490" stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="label" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} axisLine={false} tickLine={false}
            tickFormatter={v => prefix === '$' ? `$${(v / 1e6).toFixed(1)}M` : `${v.toFixed(1)}%`} />
          <Tooltip content={<CustomTooltip prefix={prefix} />} />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }} />
          {/* P5-P95 outer band */}
          <Area type="monotone" dataKey="p95" name="P95" stroke={PERCENTILE_COLOURS.p95} strokeWidth={1}
            fill="url(#g75_95)" strokeDasharray="3 3" />
          <Area type="monotone" dataKey="p75" name="P75" stroke={PERCENTILE_COLOURS.p75} strokeWidth={1}
            fill="url(#g25_75)" />
          <Area type="monotone" dataKey="p50" name="P50 (Median)" stroke="#22d3ee" strokeWidth={2}
            fill="none" />
          <Area type="monotone" dataKey="p25" name="P25" stroke={PERCENTILE_COLOURS.p25} strokeWidth={1}
            fill="url(#g5_25)" />
          <Area type="monotone" dataKey="p5"  name="P5"  stroke={PERCENTILE_COLOURS.p5} strokeWidth={1}
            fill="none" strokeDasharray="3 3" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SCENARIO COMPARISON BAR CHART
// ---------------------------------------------------------------------------
function ScenarioComparisonChart({ data, metric, label, prefix = '$' }) {
  const chartData = Object.entries(data || {}).map(([sc, vals]) => ({
    scenario: sc,
    value: vals[metric] || 0,
    fill: SCENARIO_COLOURS[sc] || '#6b7280',
  }));
  return (
    <div>
      <div className="text-xs text-white/50 mb-3 font-mono">{label}</div>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData} barCategoryGap="35%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis dataKey="scenario" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} axisLine={false} tickLine={false}
            tickFormatter={v => prefix === '$' ? `$${(v / 1e6).toFixed(1)}M` : `${(v * 100).toFixed(2)}%`} />
          <Tooltip
            formatter={(v) => prefix === '$' ? [`$${(v / 1e6).toFixed(2)}M`, label] : [`${(v * 100).toFixed(3)}%`, label]}
            contentStyle={{ background: '#0d1628', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
            itemStyle={{ color: '#fff' }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ASSET TABLE (editable)
// ---------------------------------------------------------------------------
function AssetTable({ assets, onChange }) {
  const update = (idx, field, val) => {
    const copy = assets.map((a, i) => i === idx ? { ...a, [field]: val } : a);
    onChange(copy);
  };
  const addRow = () => onChange([
    ...assets,
    {
      id: `a${Date.now()}`, name: 'New Counterparty', sector: 'Other',
      exposure: 10_000_000, baseline_pd: 0.02, lgd: 0.45,
      emission_intensity: 1.0, emissions_trend: 'Stable',
      transition_plan_score: 3, physical_risk_score: 3,
    },
  ]);
  const removeRow = (idx) => onChange(assets.filter((_, i) => i !== idx));

  const inp = (idx, field, type = 'text', step) => (
    <input
      type={type}
      step={step}
      value={assets[idx][field] ?? ''}
      onChange={e => {
        const raw = e.target.value;
        update(idx, field, type === 'number' ? (raw === '' ? '' : Number(raw)) : raw);
      }}
      className="w-full bg-transparent text-white/80 text-xs font-mono outline-none text-right"
    />
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-white/30 font-mono uppercase text-[10px]">
            <th className="text-left py-2 pr-2">Name</th>
            <th className="text-left py-2 pr-2">Sector</th>
            <th className="text-right py-2 pr-2">Exposure</th>
            <th className="text-right py-2 pr-2">PD</th>
            <th className="text-right py-2 pr-2">LGD</th>
            <th className="text-right py-2 pr-2">EI</th>
            <th className="text-center py-2 pr-2">Trend</th>
            <th className="text-center py-2 pr-2">TP</th>
            <th className="text-center py-2 pr-2">PR</th>
            <th className="py-2" />
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {assets.map((a, i) => (
            <tr key={a.id} className="hover:bg-white/[0.02]">
              <td className="py-1.5 pr-2">
                <input value={a.name} onChange={e => update(i, 'name', e.target.value)}
                  className="bg-transparent text-white/80 text-xs outline-none w-36" />
              </td>
              <td className="py-1.5 pr-2">
                <select value={a.sector} onChange={e => update(i, 'sector', e.target.value)}
                  className="bg-[#0d1628] text-white/70 text-xs rounded px-1 outline-none border border-white/10 w-36">
                  {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
              <td className="py-1.5 pr-2 text-right w-28">{inp(i, 'exposure', 'number', 1000000)}</td>
              <td className="py-1.5 pr-2 text-right w-16">{inp(i, 'baseline_pd', 'number', 0.001)}</td>
              <td className="py-1.5 pr-2 text-right w-14">{inp(i, 'lgd', 'number', 0.01)}</td>
              <td className="py-1.5 pr-2 text-right w-14">{inp(i, 'emission_intensity', 'number', 0.1)}</td>
              <td className="py-1.5 pr-2">
                <select value={a.emissions_trend} onChange={e => update(i, 'emissions_trend', e.target.value)}
                  className="bg-[#0d1628] text-white/70 text-xs rounded px-1 outline-none border border-white/10">
                  {TRENDS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </td>
              <td className="py-1.5 pr-2 text-center w-10">{inp(i, 'transition_plan_score', 'number', 1)}</td>
              <td className="py-1.5 pr-2 text-center w-10">{inp(i, 'physical_risk_score', 'number', 1)}</td>
              <td className="py-1.5 pl-1">
                <button onClick={() => removeRow(i)}
                  className="text-white/20 hover:text-red-400 transition-colors text-[10px] font-mono">×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button onClick={addRow}
        className="mt-2 text-[10px] font-mono text-cyan-400/60 hover:text-cyan-300 transition-colors">
        + Add asset
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DISTRIBUTION CARD
// ---------------------------------------------------------------------------
function DistCard({ label, dist, prefix = '$', highlight = false }) {
  if (!dist) return null;
  return (
    <div className={`rounded-xl border p-4 ${highlight ? 'border-cyan-500/30 bg-cyan-500/5' : 'border-white/8 bg-white/[0.02]'}`}>
      <div className="text-[10px] text-white/40 font-mono mb-3">{label}</div>
      <div className="grid grid-cols-5 gap-1 text-center">
        {['p5', 'p25', 'p50', 'p75', 'p95'].map(p => (
          <div key={p}>
            <div className="text-[9px] text-white/30 font-mono mb-1">{p.toUpperCase()}</div>
            <div className={`text-xs font-mono ${p === 'p50' ? 'text-cyan-300 font-bold' : 'text-white/60'}`}>
              {prefix === '$' ? fmtM(dist[p]) : fmtPctDirect(dist[p] * 100)}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-2 pt-2 border-t border-white/5 flex justify-between text-[9px] text-white/30 font-mono">
        <span>Mean: {prefix === '$' ? fmtM(dist.mean) : fmtPctDirect(dist.mean * 100)}</span>
        <span>σ: {prefix === '$' ? fmtM(dist.std_dev) : fmtPctDirect(dist.std_dev * 100)}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// MAIN PAGE
// ---------------------------------------------------------------------------
export default function MonteCarloPage() {
  const [assets, setAssets] = useState(DEFAULT_ASSETS);
  const [scenario, setScenario] = useState('Orderly');
  const [horizon, setHorizon] = useState(2050);
  const [nSims, setNSims] = useState(1000);
  const [pdSigma, setPdSigma] = useState(0.25);
  const [lgdSigma, setLgdSigma] = useState(0.15);
  const [cpSigma, setCpSigma] = useState(0.30);
  const [phSigma, setPhSigma] = useState(0.20);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);
  const [activeTab, setActiveTab] = useState('distributions');

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const body = {
        scenario,
        time_horizon: horizon,
        n_simulations: nSims,
        random_seed: 42,
        compare_scenarios: true,
        uncertainty: {
          pd_sigma: pdSigma,
          lgd_sigma: lgdSigma,
          carbon_price_sigma: cpSigma,
          physical_risk_sigma: phSigma,
          exposure_sigma: 0.08,
        },
        assets: assets.map(a => ({
          ...a,
          baseline_pd: Number(a.baseline_pd),
          lgd: Number(a.lgd),
          exposure: Number(a.exposure),
          emission_intensity: a.emission_intensity != null ? Number(a.emission_intensity) : null,
          transition_plan_score: a.transition_plan_score != null ? Number(a.transition_plan_score) : null,
          physical_risk_score: a.physical_risk_score != null ? Number(a.physical_risk_score) : null,
        })),
      };
      const resp = await fetch(`${API_URL}/api/v1/monte-carlo/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const json = await resp.json();
      setResult(json.data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [assets, scenario, horizon, nSims, pdSigma, lgdSigma, cpSigma, phSigma]);

  // Build fan chart data from scenario comparison
  const fanData = result
    ? SCENARIOS.map(sc => ({
        label: sc,
        p5:  result.distributions?.expected_loss?.p5  ?? 0,
        p25: result.distributions?.expected_loss?.p25 ?? 0,
        p50: result.distributions?.expected_loss?.p50 ?? 0,
        p75: result.distributions?.expected_loss?.p75 ?? 0,
        p95: result.distributions?.expected_loss?.p95 ?? 0,
      }))
    : [];

  // Build per-metric fan chart from scenario_comparison cross-scenario
  const scCompData = result?.scenario_comparison
    ? SCENARIOS.map(sc => ({
        label: sc,
        el:    result.scenario_comparison[sc]?.expected_loss ?? 0,
        var:   result.scenario_comparison[sc]?.portfolio_var_999 ?? 0,
        avgPd: (result.scenario_comparison[sc]?.avg_pd ?? 0) * 100,
        cf:    result.scenario_comparison[sc]?.carbon_cost ?? 0,
      }))
    : [];

  const conv = result?.convergence;
  const dist = result?.distributions;

  // Slider row component
  const SliderRow = ({ label, value, setValue, min = 0.05, max = 0.60, step = 0.01, display }) => (
    <div className="flex items-center gap-3">
      <span className="text-[10px] text-white/40 font-mono w-36 shrink-0">{label}</span>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => setValue(Number(e.target.value))}
        className="flex-1 h-1 appearance-none bg-white/10 rounded-full accent-cyan-400" />
      <span className="text-[10px] text-cyan-400 font-mono w-10 text-right">
        {display || `±${(value * 100).toFixed(0)}%`}
      </span>
    </div>
  );

  const TABS = [
    { id: 'distributions', label: 'Distributions' },
    { id: 'fan_chart',     label: 'Fan Chart' },
    { id: 'scenarios',     label: 'Scenario Compare' },
    { id: 'assets',        label: 'Asset Level' },
    { id: 'convergence',   label: 'Diagnostics' },
  ];

  return (
    <div className="min-h-full bg-[#080e1c] text-white p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-lg font-semibold text-white/90 mb-1">
              Monte Carlo Simulation
            </h1>
            <p className="text-xs text-white/40 max-w-2xl">
              Parameter Uncertainty Monte Carlo — P5/P25/P50/P75/P95 distributions for Expected Loss,
              VaR (Vasicek 99.9%), Carbon Cost, and WACI. Aligned with Basel III Pillar 2,
              NGFS Phase IV, TCFD, and EBA GL/2022/16.
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {['Basel III', 'NGFS Phase IV', 'Vasicek', 'PCAF WACI'].map(b => (
              <span key={b} className="text-[9px] font-mono bg-white/5 border border-white/10 text-white/40 px-2 py-0.5 rounded">
                {b}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-[340px_1fr] gap-6">
        {/* ---- Left: Controls ---- */}
        <div className="space-y-4">
          {/* Simulation parameters */}
          <div className="bg-[#0d1628] rounded-xl border border-white/8 p-4">
            <div className="text-[10px] font-mono text-white/40 uppercase mb-3">Simulation Parameters</div>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-white/40 font-mono block mb-1">Primary Scenario</label>
                <select value={scenario} onChange={e => setScenario(e.target.value)}
                  className="w-full bg-[#0a1220] border border-white/10 text-white/80 text-xs rounded-lg px-3 py-2 outline-none">
                  {SCENARIOS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-white/40 font-mono block mb-1">Time Horizon</label>
                <div className="flex gap-2">
                  {HORIZONS.map(h => (
                    <button key={h} onClick={() => setHorizon(h)}
                      className={`flex-1 text-xs py-1.5 rounded-lg font-mono border transition-all ${
                        horizon === h
                          ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-300'
                          : 'border-white/10 text-white/40 hover:border-white/20'
                      }`}>
                      {h}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-[10px] text-white/40 font-mono block mb-1">
                  Simulations: {fmt(nSims)}
                </label>
                <input type="range" min={100} max={5000} step={100} value={nSims}
                  onChange={e => setNSims(Number(e.target.value))}
                  className="w-full h-1 appearance-none bg-white/10 rounded-full accent-cyan-400" />
                <div className="flex justify-between text-[9px] text-white/20 font-mono mt-0.5">
                  <span>100</span><span>5,000</span>
                </div>
              </div>
            </div>
          </div>

          {/* Uncertainty parameters */}
          <div className="bg-[#0d1628] rounded-xl border border-white/8 p-4">
            <div className="text-[10px] font-mono text-white/40 uppercase mb-3">Uncertainty Parameters</div>
            <div className="space-y-2.5">
              <SliderRow label="PD Uncertainty (σ)" value={pdSigma} setValue={setPdSigma} />
              <SliderRow label="LGD Uncertainty (σ)" value={lgdSigma} setValue={setLgdSigma} max={0.40} />
              <SliderRow label="Carbon Price (σ)" value={cpSigma} setValue={setCpSigma} />
              <SliderRow label="Physical Risk (σ)" value={phSigma} setValue={setPhSigma} />
            </div>
            <div className="mt-3 pt-3 border-t border-white/5 text-[9px] text-white/25 font-mono leading-relaxed">
              Log-normal (multiplicative) for PD, carbon price, physical risk.
              Normal (additive) for LGD.
            </div>
          </div>

          {/* Run button */}
          <button
            onClick={runSimulation}
            disabled={loading || assets.length === 0}
            className={`w-full py-3 rounded-xl font-mono text-sm font-medium transition-all ${
              loading
                ? 'bg-white/5 text-white/30 cursor-wait'
                : 'bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300'
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
                Running {fmt(nSims)} simulations…
              </span>
            ) : `Run Simulation  (N={fmt(nSims)})`}
          </button>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-xs text-red-400 font-mono">
              {error}
            </div>
          )}

          {/* Convergence badge */}
          {conv && (
            <div className={`rounded-xl border p-3 ${
              conv.converged
                ? 'border-emerald-500/20 bg-emerald-500/5'
                : 'border-amber-500/20 bg-amber-500/5'
            }`}>
              <div className="text-[10px] font-mono text-white/40 mb-1.5">Convergence</div>
              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                <div>
                  <div className="text-white/30">R-hat</div>
                  <div className={conv.converged ? 'text-emerald-400' : 'text-amber-400'}>
                    {conv.gelman_rubin_rhat}
                  </div>
                </div>
                <div>
                  <div className="text-white/30">Eff. N</div>
                  <div className="text-white/70">{fmt(conv.effective_n)}</div>
                </div>
              </div>
              <div className={`mt-1.5 text-[9px] font-mono ${conv.converged ? 'text-emerald-400/60' : 'text-amber-400/60'}`}>
                {conv.converged ? 'Converged (R-hat < 1.1)' : 'Not converged — increase N'}
              </div>
            </div>
          )}
        </div>

        {/* ---- Right: Portfolio + Results ---- */}
        <div className="space-y-4">
          {/* Portfolio table */}
          <div className="bg-[#0d1628] rounded-xl border border-white/8 p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-[10px] font-mono text-white/40 uppercase">
                Portfolio ({assets.length} assets · {fmtM(assets.reduce((s, a) => s + Number(a.exposure || 0), 0))} total)
              </div>
              <div className="text-[9px] text-white/20 font-mono">
                EI = emission intensity (tCO2e/unit) · TP = transition plan (1-5) · PR = physical risk (1-5)
              </div>
            </div>
            <AssetTable assets={assets} onChange={setAssets} />
          </div>

          {/* Results */}
          {result && (
            <>
              {/* KPI summary row */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Total Exposure', val: fmtM(result.total_exposure), sub: `${result.n_assets} assets` },
                  { label: 'EL Median (P50)', val: fmtM(dist?.expected_loss?.p50), sub: `P95: ${fmtM(dist?.expected_loss?.p95)}` },
                  { label: 'VaR 99.9% (P50)', val: fmtM(dist?.portfolio_var_999?.p50), sub: `Vasicek ρ=0.30` },
                  { label: 'Avg PD (P50)', val: fmtPct(dist?.avg_pd?.p50), sub: `P95: ${fmtPct(dist?.avg_pd?.p95)}` },
                ].map(k => (
                  <div key={k.label} className="bg-[#0d1628] rounded-xl border border-white/8 p-4">
                    <div className="text-[10px] text-white/40 font-mono mb-1">{k.label}</div>
                    <div className="text-base font-mono font-bold text-white/90">{k.val}</div>
                    <div className="text-[10px] text-white/30 font-mono mt-0.5">{k.sub}</div>
                  </div>
                ))}
              </div>

              {/* Tab nav */}
              <div className="bg-[#0d1628] rounded-xl border border-white/8">
                <div className="flex border-b border-white/8 overflow-x-auto">
                  {TABS.map(t => (
                    <button key={t.id} onClick={() => setActiveTab(t.id)}
                      className={`px-4 py-2.5 text-xs font-mono whitespace-nowrap transition-colors ${
                        activeTab === t.id
                          ? 'text-cyan-300 border-b-2 border-cyan-400 -mb-px'
                          : 'text-white/35 hover:text-white/60'
                      }`}>
                      {t.label}
                    </button>
                  ))}
                </div>

                <div className="p-4">
                  {/* ---- TAB: Distributions ---- */}
                  {activeTab === 'distributions' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <DistCard label="Expected Loss" dist={dist?.expected_loss} highlight />
                        <DistCard label="Portfolio VaR 99.9%" dist={dist?.portfolio_var_999} />
                        <DistCard label="Portfolio VaR 95%" dist={dist?.portfolio_var_95} />
                        <DistCard label="Carbon Cost (USD)" dist={dist?.carbon_cost} />
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <DistCard label="Loss Rate" dist={dist?.loss_rate} prefix="%" />
                        <DistCard label="Avg Adjusted PD" dist={dist?.avg_pd} prefix="%" />
                        <DistCard label="WACI (tCO2e/unit)" dist={dist?.waci} prefix="%" />
                      </div>
                      {dist?.expected_shortfall_95 && (
                        <div className="bg-[#0a1220] rounded-xl border border-amber-500/20 p-4 flex items-center gap-6">
                          <div>
                            <div className="text-[10px] text-white/40 font-mono">Expected Shortfall (CVaR 95%)</div>
                            <div className="text-lg font-mono font-bold text-amber-300">
                              {fmtM(dist.expected_shortfall_95.value)}
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] text-white/40 font-mono">% of Total Exposure</div>
                            <div className="text-lg font-mono font-bold text-white/80">
                              {(dist.expected_shortfall_95.pct_of_exposure * 100).toFixed(2)}%
                            </div>
                          </div>
                          <div className="text-[10px] text-white/25 font-mono">
                            Average EL in worst 5% of {fmt(result.n_simulations)} simulations
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* ---- TAB: Fan Chart ---- */}
                  {activeTab === 'fan_chart' && dist && (
                    <div className="space-y-6">
                      <div className="grid grid-cols-2 gap-6">
                        {/* Build simulation-index fan for EL */}
                        <FanChart
                          title="Expected Loss — Percentile Bands"
                          data={[
                            { label: 'P5',   p5: dist.expected_loss.p5,  p25: dist.expected_loss.p5,  p50: dist.expected_loss.p5,  p75: dist.expected_loss.p5,  p95: dist.expected_loss.p5 },
                            { label: 'P25',  p5: dist.expected_loss.p5,  p25: dist.expected_loss.p25, p50: dist.expected_loss.p25, p75: dist.expected_loss.p25, p95: dist.expected_loss.p25 },
                            { label: 'P50',  p5: dist.expected_loss.p5,  p25: dist.expected_loss.p25, p50: dist.expected_loss.p50, p75: dist.expected_loss.p50, p95: dist.expected_loss.p50 },
                            { label: 'P75',  p5: dist.expected_loss.p5,  p25: dist.expected_loss.p25, p50: dist.expected_loss.p50, p75: dist.expected_loss.p75, p95: dist.expected_loss.p75 },
                            { label: 'P95',  p5: dist.expected_loss.p5,  p25: dist.expected_loss.p25, p50: dist.expected_loss.p50, p75: dist.expected_loss.p75, p95: dist.expected_loss.p95 },
                          ]}
                          prefix="$"
                        />
                        <FanChart
                          title="VaR 99.9% — Percentile Bands"
                          data={[
                            { label: 'P5',  p5: dist.portfolio_var_999.p5,  p25: dist.portfolio_var_999.p5,  p50: dist.portfolio_var_999.p5,  p75: dist.portfolio_var_999.p5,  p95: dist.portfolio_var_999.p5 },
                            { label: 'P25', p5: dist.portfolio_var_999.p5,  p25: dist.portfolio_var_999.p25, p50: dist.portfolio_var_999.p25, p75: dist.portfolio_var_999.p25, p95: dist.portfolio_var_999.p25 },
                            { label: 'P50', p5: dist.portfolio_var_999.p5,  p25: dist.portfolio_var_999.p25, p50: dist.portfolio_var_999.p50, p75: dist.portfolio_var_999.p50, p95: dist.portfolio_var_999.p50 },
                            { label: 'P75', p5: dist.portfolio_var_999.p5,  p25: dist.portfolio_var_999.p25, p50: dist.portfolio_var_999.p50, p75: dist.portfolio_var_999.p75, p95: dist.portfolio_var_999.p75 },
                            { label: 'P95', p5: dist.portfolio_var_999.p5,  p25: dist.portfolio_var_999.p25, p50: dist.portfolio_var_999.p50, p75: dist.portfolio_var_999.p75, p95: dist.portfolio_var_999.p95 },
                          ]}
                          prefix="$"
                        />
                      </div>
                      <div className="text-[10px] text-white/25 font-mono">
                        Fan width represents parameter uncertainty. Wider bands indicate higher sensitivity to carbon price,
                        physical risk amplification, and PD uncertainty assumptions.
                        Median (P50) is the central estimate.
                      </div>
                    </div>
                  )}

                  {/* ---- TAB: Scenario Compare ---- */}
                  {activeTab === 'scenarios' && scCompData.length > 0 && (
                    <div className="space-y-6">
                      <div className="grid grid-cols-2 gap-6">
                        <ScenarioComparisonChart data={result.scenario_comparison} metric="expected_loss"
                          label="Expected Loss by Scenario" />
                        <ScenarioComparisonChart data={result.scenario_comparison} metric="portfolio_var_999"
                          label="VaR 99.9% by Scenario" />
                        <ScenarioComparisonChart data={result.scenario_comparison} metric="carbon_cost"
                          label="Carbon Cost by Scenario" />
                        <ScenarioComparisonChart data={result.scenario_comparison} metric="avg_pd"
                          label="Avg PD by Scenario" prefix="%" />
                      </div>
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-white/30 font-mono uppercase text-[10px]">
                            <th className="text-left py-2 pr-4">Scenario</th>
                            <th className="text-right py-2 pr-4">Exp. Loss</th>
                            <th className="text-right py-2 pr-4">VaR 99.9%</th>
                            <th className="text-right py-2 pr-4">Carbon Cost</th>
                            <th className="text-right py-2 pr-4">Avg PD</th>
                            <th className="text-right py-2">Loss Rate</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {SCENARIOS.map(sc => {
                            const r = result.scenario_comparison?.[sc];
                            if (!r) return null;
                            return (
                              <tr key={sc} className="hover:bg-white/[0.02]">
                                <td className="py-2 pr-4">
                                  <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full"
                                      style={{ background: SCENARIO_COLOURS[sc] }} />
                                    <span className="text-white/70 font-mono">{sc}</span>
                                  </div>
                                </td>
                                <td className="text-right py-2 pr-4 text-white/80 font-mono">{fmtM(r.expected_loss)}</td>
                                <td className="text-right py-2 pr-4 text-white/80 font-mono">{fmtM(r.portfolio_var_999)}</td>
                                <td className="text-right py-2 pr-4 text-white/80 font-mono">{fmtM(r.carbon_cost)}</td>
                                <td className="text-right py-2 pr-4 text-white/80 font-mono">{fmtPct(r.avg_pd)}</td>
                                <td className="text-right py-2 text-white/80 font-mono">{fmtPct(r.loss_rate)}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* ---- TAB: Asset Level ---- */}
                  {activeTab === 'assets' && result.asset_level?.length > 0 && (
                    <div>
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-white/30 font-mono uppercase text-[10px]">
                            <th className="text-left py-2 pr-3">Asset</th>
                            <th className="text-left py-2 pr-3">Sector</th>
                            <th className="text-right py-2 pr-3">Exposure</th>
                            <th className="text-right py-2 pr-3">PD P5</th>
                            <th className="text-right py-2 pr-3">PD P50</th>
                            <th className="text-right py-2 pr-3">PD P95</th>
                            <th className="text-right py-2 pr-3">EL P50</th>
                            <th className="text-right py-2">EL P95</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {result.asset_level.map(a => (
                            <tr key={a.id} className="hover:bg-white/[0.02]">
                              <td className="py-2 pr-3 text-white/80 font-mono text-[11px]">{a.name}</td>
                              <td className="py-2 pr-3 text-white/50 font-mono text-[10px]">{a.sector}</td>
                              <td className="py-2 pr-3 text-right text-white/70 font-mono">{fmtM(a.exposure)}</td>
                              <td className="py-2 pr-3 text-right text-white/50 font-mono">{fmtPct(a.pd?.p5)}</td>
                              <td className="py-2 pr-3 text-right text-cyan-300 font-mono font-medium">{fmtPct(a.pd?.p50)}</td>
                              <td className="py-2 pr-3 text-right text-amber-300 font-mono">{fmtPct(a.pd?.p95)}</td>
                              <td className="py-2 pr-3 text-right text-white/70 font-mono">{fmtM(a.el_p50)}</td>
                              <td className="py-2 text-right text-amber-300/70 font-mono">{fmtM(a.el_p95)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* ---- TAB: Diagnostics ---- */}
                  {activeTab === 'convergence' && (
                    <div className="space-y-4">
                      {/* Methodology */}
                      <div>
                        <div className="text-[10px] text-white/40 font-mono uppercase mb-3">Methodology</div>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          {result.methodology && Object.entries(result.methodology).filter(([k]) =>
                            !['uncertainty_params', 'standards', 'calculation_timestamp'].includes(k)
                          ).map(([k, v]) => (
                            <div key={k} className="bg-[#0a1220] rounded-lg p-3 border border-white/5">
                              <div className="text-[9px] text-white/30 font-mono mb-1">
                                {k.replace(/_/g, ' ').toUpperCase()}
                              </div>
                              <div className="text-white/65 font-mono text-[11px]">{String(v)}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                      {/* Uncertainty params used */}
                      {result.methodology?.uncertainty_params && (
                        <div>
                          <div className="text-[10px] text-white/40 font-mono uppercase mb-3">Uncertainty Parameters Used</div>
                          <div className="grid grid-cols-3 gap-3">
                            {Object.entries(result.methodology.uncertainty_params).map(([k, v]) => (
                              <div key={k} className="bg-[#0a1220] rounded-lg p-3 border border-white/5 text-center">
                                <div className="text-[9px] text-white/30 font-mono mb-1">
                                  {k.replace(/_/g, ' ').toUpperCase()}
                                </div>
                                <div className="text-cyan-300 font-mono text-sm">±{(v * 100).toFixed(0)}%</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Standards */}
                      {result.methodology?.standards && (
                        <div>
                          <div className="text-[10px] text-white/40 font-mono uppercase mb-3">Regulatory Alignment</div>
                          <div className="space-y-1">
                            {result.methodology.standards.map(s => (
                              <div key={s} className="text-[11px] text-white/40 font-mono flex items-center gap-2">
                                <div className="w-1 h-1 rounded-full bg-cyan-500/50" />
                                {s}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      <div className="text-[9px] text-white/20 font-mono">
                        Calculated: {result.calculation_timestamp}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Empty state */}
          {!result && !loading && (
            <div className="bg-[#0d1628] rounded-xl border border-white/8 p-12 text-center">
              <div className="text-white/20 text-xs font-mono mb-2">
                Configure the portfolio and parameters, then run the simulation
              </div>
              <div className="text-white/10 text-[10px] font-mono">
                Default portfolio: {DEFAULT_ASSETS.length} assets across {new Set(DEFAULT_ASSETS.map(a => a.sector)).size} sectors
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
