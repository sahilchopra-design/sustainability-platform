/**
 * ModelValidationPage.jsx
 * Route: /model-validation
 *
 * BCBS 239 Model Validation Framework
 *
 * Tab 1 — Model Registry       GET  /api/v1/model-validation/models
 * Tab 2 — Validation Tests     POST /api/v1/model-validation/validate
 * Tab 3 — Backtesting          POST /api/v1/model-validation/backtest
 * Tab 4 — Champion-Challenger  POST /api/v1/model-validation/champion-challenger
 * Tab 5 — BCBS 239 Compliance  GET  /api/v1/model-validation/bcbs239-compliance
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const TOOLTIP_STYLE = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111' };

function mkRng(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

function Section({ title, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg mb-4">
      <div className="px-4 py-3 border-b border-gray-100">
        <span className="font-medium text-sm text-gray-700">{title}</span>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function KpiCard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function Badge({ label, color }) {
  const cls = {
    green:  'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber:  'bg-amber-50  text-amber-700  border-amber-200',
    red:    'bg-red-50    text-red-700    border-red-200',
    gray:   'bg-gray-50   text-gray-600   border-gray-200',
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

function Sel({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-gray-400 bg-white">
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

function Btn({ children, onClick, loading }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="px-4 py-2 bg-black text-white text-xs font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors">
      {loading ? 'Running…' : children}
    </button>
  );
}

/* ── Seed data ──────────────────────────────────────────────────────────── */
const MODEL_REGISTRY = [
  { id: 'MDL-001', name: 'PD LR Retail',           type: 'credit',  status: 'production',   lastValidated: '2025-11-14', gini: 0.64 },
  { id: 'MDL-002', name: 'PD LR Corporate',         type: 'credit',  status: 'production',   lastValidated: '2025-10-02', gini: 0.71 },
  { id: 'MDL-003', name: 'LGD Downturn Retail',     type: 'credit',  status: 'production',   lastValidated: '2025-09-18', gini: 0.58 },
  { id: 'MDL-004', name: 'LGD Downturn Corporate',  type: 'credit',  status: 'development',  lastValidated: '2025-12-01', gini: 0.61 },
  { id: 'MDL-005', name: 'EAD — Credit Conversion', type: 'credit',  status: 'production',   lastValidated: '2025-08-22', gini: null },
  { id: 'MDL-006', name: 'Market VaR (99%, 10d)',   type: 'market',  status: 'production',   lastValidated: '2025-11-30', gini: null },
  { id: 'MDL-007', name: 'Expected Shortfall',      type: 'market',  status: 'production',   lastValidated: '2025-11-30', gini: null },
  { id: 'MDL-008', name: 'FRTB IMA SA-CVA',         type: 'market',  status: 'development',  lastValidated: '2026-01-10', gini: null },
  { id: 'MDL-009', name: 'Climate PD Overlay',      type: 'climate', status: 'production',   lastValidated: '2025-12-15', gini: 0.55 },
  { id: 'MDL-010', name: 'Physical Risk Score',     type: 'climate', status: 'production',   lastValidated: '2025-12-15', gini: 0.48 },
  { id: 'MDL-011', name: 'Transition Risk Score',   type: 'climate', status: 'development',  lastValidated: '2026-02-01', gini: 0.52 },
  { id: 'MDL-012', name: 'NGFS Scenario Adjuster',  type: 'climate', status: 'production',   lastValidated: '2025-10-10', gini: null },
  { id: 'MDL-013', name: 'OpRisk AMA Loss Model',   type: 'op',      status: 'retired',      lastValidated: '2024-06-30', gini: null },
  { id: 'MDL-014', name: 'OpRisk BIA Overlay',      type: 'op',      status: 'production',   lastValidated: '2025-07-20', gini: null },
  { id: 'MDL-015', name: 'IRRBB ΔNII Model',        type: 'market',  status: 'production',   lastValidated: '2025-09-05', gini: null },
  { id: 'MDL-016', name: 'Liquidity LCR Engine',    type: 'market',  status: 'production',   lastValidated: '2025-08-14', gini: null },
  { id: 'MDL-017', name: 'Macroeconomic Scenario PD', type: 'credit', status: 'development', lastValidated: '2026-03-01', gini: 0.67 },
];

const STAT_TESTS = [
  { test: 'Gini Coefficient', stat: '0.648', pValue: 'n/a', threshold: '>= 0.40', status: 'pass' },
  { test: 'AUC-ROC', stat: '0.824', pValue: 'n/a', threshold: '>= 0.70', status: 'pass' },
  { test: 'Kolmogorov-Smirnov', stat: '0.312', pValue: '0.003', threshold: '>= 0.15', status: 'pass' },
  { test: 'PSI (Population Stability)', stat: '0.089', pValue: 'n/a', threshold: '< 0.10', status: 'warning' },
  { test: 'Binomial Test', stat: '1.84', pValue: '0.066', threshold: 'p > 0.05', status: 'warning' },
  { test: 'Chi-Squared Homogeneity', stat: '12.41', pValue: '0.014', threshold: 'p > 0.01', status: 'pass' },
  { test: 'Spearman Rank Correlation', stat: '0.741', pValue: '< 0.001', threshold: '>= 0.50', status: 'pass' },
  { test: 'Hosmer-Lemeshow', stat: '7.82', pValue: '0.450', threshold: 'p > 0.05', status: 'pass' },
  { test: 'VIF (Variance Inflation Factor)', stat: '2.14', pValue: 'n/a', threshold: '< 5.0', status: 'pass' },
  { test: 'Backtesting — Traffic Light', stat: 'Green', pValue: 'n/a', threshold: '< 5 exceptions', status: 'pass' },
  { test: 'Backtesting — Binomial', stat: '0.94', pValue: '0.347', threshold: 'p > 0.05', status: 'pass' },
  { test: 'PSI — Input Variables', stat: '0.042', pValue: 'n/a', threshold: '< 0.10', status: 'pass' },
];

const BCBS239_PRINCIPLES = [
  { id: 'P1',  principle: 'Data Architecture & IT Infrastructure', score: 78, status: 'adequate' },
  { id: 'P2',  principle: 'Data Accuracy & Integrity', score: 82, status: 'adequate' },
  { id: 'P3',  principle: 'Data Completeness', score: 71, status: 'adequate' },
  { id: 'P4',  principle: 'Data Timeliness', score: 65, status: 'attention' },
  { id: 'P5',  principle: 'Data Adaptability', score: 60, status: 'attention' },
  { id: 'P6',  principle: 'Risk Data Governance', score: 85, status: 'adequate' },
  { id: 'P7',  principle: 'Data Architecture (Model)', score: 74, status: 'adequate' },
  { id: 'P8',  principle: 'Risk Reporting Policies', score: 88, status: 'strong' },
  { id: 'P9',  principle: 'Supervisory Review', score: 70, status: 'adequate' },
  { id: 'P10', principle: 'Remediation & Escalation', score: 55, status: 'attention' },
  { id: 'P11', principle: 'Risk Reporting Practices', score: 80, status: 'adequate' },
];

function genBacktestData(modelId) {
  const seed = modelId.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  const rng = mkRng(seed);
  return Array.from({ length: 24 }, (_, i) => {
    const month = new Date(2024, i, 1).toLocaleDateString('en-GB', { month: 'short', year: '2-digit' });
    const predicted = 0.025 + rng() * 0.015;
    const actual = predicted * (0.8 + rng() * 0.4);
    return { month, predicted: parseFloat(predicted.toFixed(4)), actual: parseFloat(actual.toFixed(4)) };
  });
}

const CHAMPION = { gini: 0.648, auc: 0.824, accuracy: 0.887, brier: 0.041 };
const CHALLENGER = { gini: 0.671, auc: 0.836, accuracy: 0.891, brier: 0.038 };

/* ── Tab 1: Model Registry ──────────────────────────────────────────────── */
function ModelRegistry({ models }) {
  const rows = models?.length ? models : MODEL_REGISTRY;
  const [typeFilter, setTypeFilter] = useState('all');

  const filtered = typeFilter === 'all' ? rows : rows.filter(r => r.type === typeFilter);
  const inProduction = rows.filter(r => r.status === 'production').length;

  const TYPE_COLOR = { credit: 'blue', market: 'amber', climate: 'green', op: 'gray' };
  const STATUS_COLOR = { production: 'green', development: 'amber', retired: 'red' };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Models in Production" value={inProduction} sub={`of ${rows.length} registered`} color="text-emerald-600" />
        <KpiCard label="Tests Passed %" value="83%" sub="last validation cycle" color="text-emerald-600" />
        <KpiCard label="Backtesting Exceptions" value="3" sub="12-month rolling" color="text-amber-600" />
        <KpiCard label="BCBS 239 Score" value="74%" sub="composite compliance" color="text-blue-600" />
      </div>

      <Section title="Model Registry — 17 Registered Models">
        <div className="flex gap-2 mb-3 flex-wrap">
          {['all', 'credit', 'market', 'climate', 'op'].map(f => (
            <button key={f} onClick={() => setTypeFilter(f)}
              className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
                typeFilter === f ? 'bg-black text-white border-black' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
              }`}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Model ID', 'Name', 'Type', 'Status', 'Last Validated', 'Gini'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, i) => (
              <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${row.status === 'retired' ? 'opacity-50' : ''}`}>
                <td className="py-1.5 px-2 font-mono font-bold text-gray-600 text-[10px]">{row.id}</td>
                <td className="py-1.5 px-2 font-medium text-gray-700">{row.name}</td>
                <td className="py-1.5 px-2"><Badge label={row.type} color={TYPE_COLOR[row.type]} /></td>
                <td className="py-1.5 px-2"><Badge label={row.status} color={STATUS_COLOR[row.status]} /></td>
                <td className="py-1.5 px-2 font-mono text-gray-500">{row.lastValidated}</td>
                <td className="py-1.5 px-2 font-mono">{row.gini != null ? row.gini.toFixed(3) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 2: Validation Tests ────────────────────────────────────────────── */
function ValidationTests() {
  const [modelId, setModelId] = useState('MDL-001');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const data = result || STAT_TESTS;
  const passed = data.filter(t => t.status === 'pass').length;
  const passPct = Math.round(passed / data.length * 100);

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/model-validation/validate`, { model_id: modelId });
      setResult(res.data?.tests || null);
    } catch { setResult(STAT_TESTS); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <Section title="Parameters">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="w-48">
            <Sel label="Select Model" value={modelId} onChange={setModelId}
              options={MODEL_REGISTRY.filter(m => m.status !== 'retired').map(m => m.id)} />
          </div>
          <Btn onClick={handleRun} loading={loading}>Run Validation Tests</Btn>
        </div>
      </Section>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Tests Run" value={data.length} sub="statistical tests" color="text-gray-900" />
        <KpiCard label="Passed" value={passed} sub={`${passPct}% pass rate`} color="text-emerald-600" />
        <KpiCard label="Warnings" value={data.filter(t => t.status === 'warning').length} sub="attention required" color="text-amber-600" />
        <KpiCard label="Failed" value={data.filter(t => t.status === 'fail').length} sub="remediation required" color="text-red-600" />
      </div>

      <Section title={`Validation Test Results — Model ${modelId}`}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Test', 'Statistic', 'p-Value', 'Threshold', 'Status'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${row.status === 'fail' ? 'bg-red-50/30' : row.status === 'warning' ? 'bg-amber-50/20' : ''}`}>
                <td className="py-1.5 px-2 font-medium text-gray-700">{row.test}</td>
                <td className="py-1.5 px-2 font-mono font-semibold">{row.stat}</td>
                <td className="py-1.5 px-2 font-mono text-gray-500">{row.pValue}</td>
                <td className="py-1.5 px-2 text-gray-500">{row.threshold}</td>
                <td className="py-1.5 px-2">
                  <Badge label={row.status}
                    color={row.status === 'pass' ? 'green' : row.status === 'warning' ? 'amber' : 'red'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[10px] text-gray-400 mt-3">
          Tests per EBA GL/2017/16 (IRB approach validation) · BCBS d457 (model risk management) · Basel IV model constraints.
        </p>
      </Section>
    </div>
  );
}

/* ── Tab 3: Backtesting ─────────────────────────────────────────────────── */
function Backtesting() {
  const [modelId, setModelId] = useState('MDL-001');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const seedData = useMemo(() => genBacktestData('MDL-001'), []);
  const data = result || seedData;

  const exceptions = data.filter(d => Math.abs(d.actual - d.predicted) / d.predicted > 0.3).length;

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/model-validation/backtest`, { model_id: modelId });
      setResult(res.data?.series || genBacktestData(modelId));
    } catch { setResult(genBacktestData(modelId)); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <Section title="Parameters">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="w-48">
            <Sel label="Select Model" value={modelId} onChange={setModelId}
              options={MODEL_REGISTRY.filter(m => m.status !== 'retired').map(m => m.id)} />
          </div>
          <Btn onClick={handleRun} loading={loading}>Run Backtesting</Btn>
        </div>
      </Section>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Periods Tested" value={data.length} sub="monthly observations" color="text-gray-900" />
        <KpiCard label="Backtesting Exceptions" value={exceptions} sub=">30% deviation" color={exceptions <= 5 ? 'text-emerald-600' : exceptions <= 10 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Traffic Light" value={exceptions <= 4 ? 'Green' : exceptions <= 9 ? 'Amber' : 'Red'}
          sub="Basel BIS zones" color={exceptions <= 4 ? 'text-emerald-600' : exceptions <= 9 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Avg Deviation" value={`${(data.reduce((a, b) => a + Math.abs(b.actual - b.predicted) / b.predicted, 0) / data.length * 100).toFixed(1)}%`}
          sub="mean absolute %" color="text-gray-700" />
      </div>

      <Section title="Backtesting: Predicted vs Actual PD — 24 Months">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ left: 10, right: 20, top: 4, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="month" tick={{ fontSize: 9 }} interval={2} angle={-20} textAnchor="end" />
            <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v * 100).toFixed(1)}%`} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${(v * 100).toFixed(2)}%`]} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Line type="monotone" dataKey="predicted" name="Predicted PD" stroke="#111" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="actual" name="Actual Default Rate" stroke="#10b981" strokeWidth={1.5} dot={{ r: 2 }} strokeDasharray="4 2" />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-[10px] text-gray-400 mt-2">
          Traffic Light thresholds (Basel BIS): Green zone ≤4 exceptions; Amber zone 5-9; Red zone ≥10. Exception = |actual − predicted| / predicted &gt; 30%.
        </p>
      </Section>
    </div>
  );
}

/* ── Tab 4: Champion-Challenger ─────────────────────────────────────────── */
function ChampionChallenger() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const champion = result?.champion || CHAMPION;
  const challenger = result?.challenger || CHALLENGER;

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/model-validation/champion-challenger`, {
        champion_id: 'MDL-001', challenger_id: 'MDL-017',
      });
      setResult(res.data);
    } catch { setResult({ champion: CHAMPION, challenger: CHALLENGER }); }
    finally { setLoading(false); }
  }

  const metrics = [
    { name: 'Gini Coefficient', champion: champion.gini, challenger: challenger.gini, higher: true },
    { name: 'AUC-ROC', champion: champion.auc, challenger: challenger.auc, higher: true },
    { name: 'Accuracy', champion: champion.accuracy, challenger: challenger.accuracy, higher: true },
    { name: 'Brier Score', champion: champion.brier, challenger: challenger.brier, higher: false },
  ];

  const challengerWins = metrics.filter(m => m.higher ? m.challenger > m.champion : m.challenger < m.champion).length;
  const winner = challengerWins >= 3 ? 'Challenger' : 'Champion';

  const chartData = metrics.map(m => ({
    metric: m.name.split(' ')[0],
    Champion: parseFloat((m.champion * 100).toFixed(1)),
    Challenger: parseFloat((m.challenger * 100).toFixed(1)),
  }));

  return (
    <div className="space-y-4">
      <Section title="Champion vs Challenger Configuration">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="border border-gray-200 rounded p-2.5 bg-gray-50">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Champion Model</p>
              <p className="font-semibold text-gray-800">MDL-001 — PD LR Retail</p>
              <p className="text-[10px] text-gray-500 mt-0.5">Production since 2024-Q3</p>
            </div>
            <div className="border border-emerald-200 rounded p-2.5 bg-emerald-50/50">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Challenger Model</p>
              <p className="font-semibold text-gray-800">MDL-017 — Macro Scenario PD</p>
              <p className="text-[10px] text-gray-500 mt-0.5">Development — 2026-Q1</p>
            </div>
          </div>
          <Btn onClick={handleRun} loading={loading}>Run Champion-Challenger</Btn>
        </div>
      </Section>

      <div className="flex gap-3 mb-4">
        <div className={`flex-1 border-2 rounded-lg p-3 text-center ${winner === 'Challenger' ? 'border-emerald-400 bg-emerald-50' : 'border-gray-300 bg-gray-50'}`}>
          <p className="text-[10px] text-gray-500 uppercase tracking-wider">Winner Recommendation</p>
          <p className={`text-2xl font-bold mt-1 ${winner === 'Challenger' ? 'text-emerald-600' : 'text-gray-700'}`}>{winner}</p>
          <p className="text-[10px] text-gray-500 mt-1">{winner === 'Challenger' ? 'Promote to production' : 'Retain current champion'}</p>
        </div>
        <div className="w-40 border border-gray-200 rounded-lg p-3 text-center">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider">Metrics Won</p>
          <p className="text-2xl font-bold font-mono mt-1">{challengerWins}/{metrics.length}</p>
          <p className="text-[10px] text-gray-500 mt-1">Challenger vs Champion</p>
        </div>
      </div>

      <Section title="Metric Comparison — Champion vs Challenger (scaled ×100)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} margin={{ left: 10, right: 20, top: 4, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="metric" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="Champion" fill="#111" radius={[2, 2, 0, 0]} />
            <Bar dataKey="Challenger" fill="#10b981" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Detailed Metric Table">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Metric', 'Champion', 'Challenger', 'Delta', 'Better'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.map((m, i) => {
              const delta = m.higher ? m.challenger - m.champion : m.champion - m.challenger;
              const betterModel = delta > 0 ? 'Challenger' : 'Champion';
              return (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-1.5 px-2 font-medium text-gray-700">{m.name}</td>
                  <td className="py-1.5 px-2 font-mono">{m.champion.toFixed(3)}</td>
                  <td className="py-1.5 px-2 font-mono">{m.challenger.toFixed(3)}</td>
                  <td className={`py-1.5 px-2 font-mono font-semibold ${delta > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {delta > 0 ? '+' : ''}{(Math.abs(m.challenger - m.champion) * (m.higher ? 1 : -1)).toFixed(3)}
                  </td>
                  <td className="py-1.5 px-2">
                    <Badge label={betterModel} color={betterModel === 'Challenger' ? 'green' : 'gray'} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 5: BCBS 239 Compliance ─────────────────────────────────────────── */
function BCBS239Compliance({ data }) {
  const principles = data?.length ? data : BCBS239_PRINCIPLES;
  const avgScore = Math.round(principles.reduce((a, b) => a + b.score, 0) / principles.length);

  const STATUS_COLOR = { strong: 'green', adequate: 'blue', attention: 'amber', breach: 'red' };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="BCBS 239 Score" value={`${avgScore}%`} sub="composite compliance"
          color={avgScore >= 80 ? 'text-emerald-600' : avgScore >= 65 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Strong Principles" value={principles.filter(p => p.status === 'strong').length} sub="score ≥ 85%" color="text-emerald-600" />
        <KpiCard label="Attention Required" value={principles.filter(p => p.status === 'attention').length} sub="score < 65%" color="text-amber-600" />
        <KpiCard label="Breaches" value={principles.filter(p => p.status === 'breach').length} sub="remediation required" color="text-red-600" />
      </div>

      <Section title="BCBS 239 — 11-Principle Compliance Checklist">
        <div className="space-y-2.5">
          {principles.map((p, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="text-[10px] font-mono font-bold text-gray-500 w-6 shrink-0">{p.id}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-700 truncate">{p.principle}</span>
                  <div className="flex items-center gap-2 ml-2 shrink-0">
                    <span className="text-[10px] font-mono font-semibold">{p.score}%</span>
                    <Badge label={p.status} color={STATUS_COLOR[p.status]} />
                  </div>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      p.score >= 85 ? 'bg-emerald-500' : p.score >= 70 ? 'bg-blue-500' : p.score >= 55 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${p.score}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-700">Overall BCBS 239 Compliance</span>
            <span className="text-sm font-bold font-mono">{avgScore}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2 mt-1.5">
            <div className={`h-2 rounded-full ${avgScore >= 80 ? 'bg-emerald-500' : avgScore >= 65 ? 'bg-amber-500' : 'bg-red-500'}`}
              style={{ width: `${avgScore}%` }} />
          </div>
        </div>
      </Section>
    </div>
  );
}

/* ── TABS ───────────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'registry',    label: 'Model Registry' },
  { id: 'tests',       label: 'Validation Tests' },
  { id: 'backtest',    label: 'Backtesting' },
  { id: 'champion',    label: 'Champion-Challenger' },
  { id: 'bcbs239',     label: 'BCBS 239 Compliance' },
];

/* ── Root ───────────────────────────────────────────────────────────────── */
export default function ModelValidationPage() {
  const [tab, setTab] = useState('registry');
  const [modelsData, setModelsData] = useState(null);
  const [bcbsData, setBcbsData] = useState(null);

  useEffect(() => {
    (async () => {
      const [models, bcbs] = await Promise.all([
        axios.get(`${API}/api/v1/model-validation/models`).catch(() => null),
        axios.get(`${API}/api/v1/model-validation/bcbs239-compliance`).catch(() => null),
      ]);
      setModelsData(models?.data?.models || null);
      setBcbsData(bcbs?.data?.principles || null);
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo model inventory — BCBS 239 Model Validation Framework with 17 registered models, 12 statistical tests, seed fallback data." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Model Validation Framework</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            BCBS 239 · EBA GL/2017/16 · 17 registered models · 12 validation tests · Champion-Challenger
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['BCBS 239', 'EBA GL/2017/16', 'SR 11-7', 'Basel IV'].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

      <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              tab === t.id ? 'bg-white text-gray-900 shadow-sm border border-gray-200' : 'text-gray-500 hover:text-gray-700'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'registry' && <ModelRegistry models={modelsData} />}
      {tab === 'tests'    && <ValidationTests />}
      {tab === 'backtest' && <Backtesting />}
      {tab === 'champion' && <ChampionChallenger />}
      {tab === 'bcbs239'  && <BCBS239Compliance data={bcbsData} />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Regulatory basis:</span> BCBS 239 (Jan 2013) — 11 principles for effective risk data aggregation · EBA GL/2017/16 — IRB model validation · SR 11-7 (Federal Reserve) — model risk management guidance</p>
        <p><span className="font-semibold text-gray-500">Tests:</span> Gini · AUC-ROC · KS · PSI · Binomial · Chi-squared · Spearman · Hosmer-Lemeshow · VIF · Backtesting (Traffic Light / Binomial) · Input variable PSI</p>
      </div>
    </div>
  );
}
