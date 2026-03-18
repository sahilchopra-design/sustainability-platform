/**
 * EiopaStressPage.jsx
 * Route: /eiopa-stress
 *
 * EIOPA ORSA Climate Stress Test — Solvency II Article 45a
 *
 * Tab 1 — Stress Dashboard    POST /api/v1/eiopa-stress/assess
 * Tab 2 — ORSA Checklist      GET  /api/v1/eiopa-stress/ref/orsa-checklist
 * Tab 3 — Scenarios           GET  /api/v1/eiopa-stress/ref/scenarios
 * Tab 4 — Capital Analysis    (derived from Tab 1 result)
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const TOOLTIP_STYLE = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111' };

/* ── Seed RNG ───────────────────────────────────────────────────────────── */
function mkRng(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

/* ── Shared primitives ──────────────────────────────────────────────────── */
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
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

/* ── Demo insurer payload ───────────────────────────────────────────────── */
const DEMO_PAYLOAD = {
  insurer: {
    entity_id: 'DEMO_INS_001',
    entity_name: 'Demo Insurance Group',
    insurer_type: 'composite',
    total_assets_eur: 25000000000,
    total_tp_eur: 20000000000,
    eligible_own_funds_eur: 3500000000,
    scr_eur: 2200000000,
    mcr_eur: 550000000,
    equity_listed_pct: 18, equity_fossil_fuel_pct: 4,
    re_commercial_pct: 10, re_residential_pct: 5,
    sovereign_bonds_pct: 30, ig_corp_bonds_pct: 22,
    hy_corp_bonds_pct: 6, infrastructure_pct: 4, alternatives_pct: 5,
    annual_natcat_exposure_eur: 80000000,
    annual_premium_eur: 1500000000,
    in_force_sum_assured_eur: 40000000000,
    has_board_climate_oversight: true,
    has_climate_scenario_analysis: true,
    has_long_term_scenarios: false,
    has_natcat_climate_assessment: true,
    has_management_actions_plan: false,
    has_data_quality_disclosure: false,
    has_nca_orsa_submission: true,
    has_double_materiality: false,
  },
};

/* ── Seed fallback data ─────────────────────────────────────────────────── */
function genSeedData() {
  const rng = mkRng(42);
  const scenarios = [
    { id: 'inst_hot_house', label: 'Instantaneous Hot-house', pre: 159, post: 112 },
    { id: 'inst_disorderly', label: 'Instantaneous Disorderly', pre: 159, post: 128 },
    { id: 'lt_net_zero', label: 'LT Net Zero 2050', pre: 159, post: 141 },
    { id: 'lt_delayed', label: 'LT Delayed Transition', pre: 159, post: 135 },
  ];
  const assetShocks = [
    { name: 'Listed Equity', shock: 45 + rng() * 10 },
    { name: 'Fossil Fuel Eq.', shock: 55 + rng() * 12 },
    { name: 'IG Corp Bonds', shock: 8 + rng() * 5 },
    { name: 'HY Corp Bonds', shock: 18 + rng() * 8 },
    { name: 'Comm. Real Est.', shock: 22 + rng() * 10 },
    { name: 'Res. Real Est.', shock: 14 + rng() * 6 },
    { name: 'Infrastructure', shock: 12 + rng() * 5 },
  ];
  return {
    worst_solvency_ratio_pct: 112,
    capital_shortfall_eur: 0,
    resilience_tier: 'Moderate',
    orsa_completeness_pct: 62.5,
    scenarios,
    asset_shocks: assetShocks,
    capital_table: scenarios.map(s => ({
      scenario: s.label,
      pre_scr_eur: 2200,
      post_scr_eur: Math.round(2200 * (1 + rng() * 0.3)),
      pre_funds_eur: 3500,
      post_funds_eur: Math.round(3500 * (0.7 + rng() * 0.2)),
      pre_ratio: s.pre,
      post_ratio: s.post,
      scr_breach: s.post < 100,
    })),
  };
}

/* ── Tab 1: Stress Dashboard ────────────────────────────────────────────── */
function StressDashboard({ result }) {
  if (!result) return <p className="text-xs text-gray-400 py-8 text-center">Loading stress assessment…</p>;

  const scenarioData = result.scenarios || [];
  const assetShocks = result.asset_shocks || [];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Worst Solvency Ratio" value={`${result.worst_solvency_ratio_pct ?? '—'}%`}
          sub="Post-stress minimum"
          color={result.worst_solvency_ratio_pct >= 130 ? 'text-emerald-600' : result.worst_solvency_ratio_pct >= 100 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Capital Shortfall" value={result.capital_shortfall_eur > 0 ? `€${(result.capital_shortfall_eur / 1e6).toFixed(0)}M` : '€0'}
          sub="vs. SCR requirement"
          color={result.capital_shortfall_eur > 0 ? 'text-red-600' : 'text-emerald-600'} />
        <KpiCard label="Resilience Tier" value={result.resilience_tier ?? '—'}
          sub="EIOPA classification"
          color={result.resilience_tier === 'Strong' ? 'text-emerald-600' : result.resilience_tier === 'Moderate' ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="ORSA Completeness" value={`${result.orsa_completeness_pct ?? '—'}%`}
          sub="Art. 45a requirements"
          color={result.orsa_completeness_pct >= 80 ? 'text-emerald-600' : result.orsa_completeness_pct >= 50 ? 'text-amber-600' : 'text-red-600'} />
      </div>

      <Section title="Solvency Ratio: Pre vs Post-Stress by Scenario">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={scenarioData} margin={{ left: 10, right: 20, top: 4, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="label" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 200]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="pre" name="Pre-Stress" fill="#111" radius={[3, 3, 0, 0]} />
            <Bar dataKey="post" name="Post-Stress" radius={[3, 3, 0, 0]}>
              {scenarioData.map((d, i) => (
                <Cell key={i} fill={d.post < 100 ? '#ef4444' : d.post < 130 ? '#f59e0b' : '#10b981'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Asset Shock Breakdown (% value loss)">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={assetShocks} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10 }} unit="%" domain={[0, 70]} />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={90} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Shock']} />
            <Bar dataKey="shock" radius={[0, 3, 3, 0]}>
              {assetShocks.map((d, i) => (
                <Cell key={i} fill={d.shock > 40 ? '#ef4444' : d.shock > 20 ? '#f59e0b' : '#10b981'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── Tab 2: ORSA Checklist ──────────────────────────────────────────────── */
const SEED_CHECKLIST = [
  { ref: 'ORSA-1',  requirement: 'Board climate risk oversight established',              source: 'Art. 45a(1)', met: true },
  { ref: 'ORSA-2',  requirement: 'Climate scenario analysis conducted',                   source: 'Art. 45a(1)', met: true },
  { ref: 'ORSA-3',  requirement: 'Long-term (>30yr) scenarios included',                  source: 'EIOPA 2022', met: false },
  { ref: 'ORSA-4',  requirement: 'NatCat climate adjustment assessed',                     source: 'Art. 45a(2)', met: true },
  { ref: 'ORSA-5',  requirement: 'Management actions plan documented',                     source: 'EIOPA OP', met: false },
  { ref: 'ORSA-6',  requirement: 'Data quality / limitations disclosed',                   source: 'Art. 45a(3)', met: false },
  { ref: 'ORSA-7',  requirement: 'NCA submission made (ORSA report)',                      source: 'Art. 45a(5)', met: true },
  { ref: 'ORSA-8',  requirement: 'Double materiality assessment completed',                source: 'CSRD link',  met: false },
  { ref: 'ORSA-9',  requirement: 'Transition risk quantified in SCR',                      source: 'EIOPA 2022', met: true },
  { ref: 'ORSA-10', requirement: 'Physical risk quantified in SCR',                        source: 'Art. 45a(2)', met: true },
  { ref: 'ORSA-11', requirement: 'Climate metrics disclosed in SFCR',                      source: 'Art. 51',    met: false },
  { ref: 'ORSA-12', requirement: 'Investment strategy aligned with climate scenarios',      source: 'Art. 132',   met: false },
];

function OrsaChecklist({ checklistData }) {
  const items = checklistData?.length ? checklistData : SEED_CHECKLIST;
  const metCount = items.filter(i => i.met).length;
  const pct = Math.round((metCount / items.length) * 100);

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">ORSA Completeness</span>
          <span className="text-sm font-semibold font-mono">{metCount} / {items.length} ({pct}%)</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <Section title="Art. 45a Requirements Checklist">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Ref', 'Requirement', 'EIOPA Source', 'Status'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.ref} className={`border-b border-gray-100 hover:bg-gray-50 ${!item.met ? 'bg-red-50/30' : ''}`}>
                <td className="py-1.5 px-2 font-mono text-gray-500">{item.ref}</td>
                <td className="py-1.5 px-2 text-gray-700">{item.requirement}</td>
                <td className="py-1.5 px-2 text-gray-500">{item.source}</td>
                <td className="py-1.5 px-2">
                  <Badge label={item.met ? 'Met' : 'Not Met'} color={item.met ? 'green' : 'red'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 3: Scenarios ───────────────────────────────────────────────────── */
const SEED_SCENARIOS = [
  {
    id: 'inst_hot_house', label: 'Instantaneous Hot-house World',
    type: 'Physical', horizon: 'Instantaneous',
    equity_shock: 55, bond_spread: 120, re_shock: 30, natcat_mult: 1.8,
    description: 'Sudden repricing assuming no transition — maximum physical risk.',
  },
  {
    id: 'inst_disorderly', label: 'Instantaneous Disorderly Transition',
    type: 'Transition', horizon: 'Instantaneous',
    equity_shock: 45, bond_spread: 80, re_shock: 25, natcat_mult: 1.2,
    description: 'Abrupt late policy action — stranded assets, credit stress.',
  },
  {
    id: 'lt_net_zero', label: 'LT Net Zero 2050',
    type: 'Orderly', horizon: '2050',
    equity_shock: 20, bond_spread: 30, re_shock: 10, natcat_mult: 1.1,
    description: 'Gradual orderly transition aligned with Paris Agreement.',
  },
  {
    id: 'lt_delayed', label: 'LT Delayed Transition',
    type: 'Disorderly', horizon: '2035+',
    equity_shock: 35, bond_spread: 60, re_shock: 20, natcat_mult: 1.4,
    description: 'Policy delayed until mid-2030s then rapidly tightened.',
  },
];

function ScenariosPanel({ scenariosData }) {
  const [selected, setSelected] = useState(null);
  const scenarios = scenariosData?.length ? scenariosData : SEED_SCENARIOS;
  const detail = selected ? scenarios.find(s => s.id === selected) : null;

  const TYPE_COLOR = {
    Physical: 'text-red-600 bg-red-50 border-red-200',
    Transition: 'text-amber-700 bg-amber-50 border-amber-200',
    Orderly: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    Disorderly: 'text-orange-700 bg-orange-50 border-orange-200',
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {scenarios.map(s => (
          <button key={s.id} onClick={() => setSelected(s.id === selected ? null : s.id)}
            className={`text-left p-4 rounded-lg border transition-all ${
              selected === s.id ? 'border-black bg-gray-50 shadow-sm' : 'border-gray-200 bg-white hover:border-gray-400'
            }`}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-medium text-sm text-gray-800">{s.label}</span>
              <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${TYPE_COLOR[s.type] || 'bg-gray-50 text-gray-600 border-gray-200'}`}>
                {s.type}
              </span>
            </div>
            <p className="text-[11px] text-gray-500 mb-2">{s.description}</p>
            <div className="grid grid-cols-4 gap-1 text-[10px]">
              <div className="bg-gray-50 rounded p-1 text-center">
                <p className="text-gray-400">Eq. Shock</p>
                <p className="font-mono font-semibold text-red-600">{s.equity_shock}%</p>
              </div>
              <div className="bg-gray-50 rounded p-1 text-center">
                <p className="text-gray-400">Bond Spread</p>
                <p className="font-mono font-semibold text-amber-700">+{s.bond_spread}bp</p>
              </div>
              <div className="bg-gray-50 rounded p-1 text-center">
                <p className="text-gray-400">RE Shock</p>
                <p className="font-mono font-semibold text-orange-600">{s.re_shock}%</p>
              </div>
              <div className="bg-gray-50 rounded p-1 text-center">
                <p className="text-gray-400">NatCat ×</p>
                <p className="font-mono font-semibold text-purple-600">{s.natcat_mult}×</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {detail && (
        <Section title={`Detailed Shock Parameters: ${detail.label}`}>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            {[
              ['Scenario Type', detail.type],
              ['Time Horizon', detail.horizon],
              ['Equity Shock', `${detail.equity_shock}%`],
              ['Fossil Fuel Eq. Premium', `+${detail.equity_shock + 10}%`],
              ['Bond Spread Widening', `+${detail.bond_spread} bps`],
              ['Real Estate Shock', `${detail.re_shock}%`],
              ['NatCat Multiplier', `${detail.natcat_mult}×`],
              ['Infrastructure Shock', `${Math.round(detail.re_shock * 0.6)}%`],
            ].map(([k, v]) => (
              <div key={k} className="bg-gray-50 rounded p-2">
                <p className="text-gray-400 mb-0.5">{k}</p>
                <p className="font-semibold text-gray-800">{v}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

/* ── Tab 4: Capital Analysis ────────────────────────────────────────────── */
function CapitalAnalysis({ result }) {
  const rows = result?.capital_table || genSeedData().capital_table;

  return (
    <Section title="Capital Position: Pre vs Post-Stress (EUR millions)">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-200">
            {['Scenario', 'Pre SCR (€M)', 'Post SCR (€M)', 'Pre Funds (€M)', 'Post Funds (€M)', 'Pre Ratio', 'Post Ratio', 'SCR Breach'].map(h => (
              <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const rowClass = r.scr_breach
              ? 'bg-red-50'
              : r.post_ratio < 130
              ? 'bg-amber-50/40'
              : 'bg-emerald-50/20';
            return (
              <tr key={i} className={`border-b border-gray-100 hover:brightness-95 ${rowClass}`}>
                <td className="py-1.5 px-2 font-medium text-gray-700 max-w-[140px] truncate">{r.scenario}</td>
                <td className="py-1.5 px-2 font-mono">{r.pre_scr_eur?.toLocaleString()}</td>
                <td className="py-1.5 px-2 font-mono">{r.post_scr_eur?.toLocaleString()}</td>
                <td className="py-1.5 px-2 font-mono">{r.pre_funds_eur?.toLocaleString()}</td>
                <td className="py-1.5 px-2 font-mono">{r.post_funds_eur?.toLocaleString()}</td>
                <td className="py-1.5 px-2 font-mono text-gray-600">{r.pre_ratio}%</td>
                <td className="py-1.5 px-2 font-mono font-semibold">
                  <span className={r.post_ratio < 100 ? 'text-red-600' : r.post_ratio < 130 ? 'text-amber-600' : 'text-emerald-600'}>
                    {r.post_ratio}%
                  </span>
                </td>
                <td className="py-1.5 px-2">
                  <Badge label={r.scr_breach ? 'BREACH' : 'Pass'} color={r.scr_breach ? 'red' : 'green'} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="text-[10px] text-gray-400 mt-3">
        Row shading: red = SCR breach (&lt;100%), amber = warning (100–130%), green = adequate (&gt;150%).
        SCR = Solvency Capital Requirement per Solvency II Art. 101.
      </p>
    </Section>
  );
}

/* ── TABS config ────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'dashboard',  label: 'Stress Dashboard' },
  { id: 'checklist',  label: 'ORSA Checklist' },
  { id: 'scenarios',  label: 'Scenarios' },
  { id: 'capital',    label: 'Capital Analysis' },
];

/* ── Root component ─────────────────────────────────────────────────────── */
export default function EiopaStressPage() {
  const [tab, setTab] = useState('dashboard');
  const [result, setResult] = useState(null);
  const [checklist, setChecklist] = useState(null);
  const [scenarios, setScenarios] = useState(null);
  const [loading, setLoading] = useState(true);
  const seed = useMemo(() => genSeedData(), []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [assess, cl, sc] = await Promise.all([
          axios.post(`${API}/api/v1/eiopa-stress/assess`, DEMO_PAYLOAD).catch(() => null),
          axios.get(`${API}/api/v1/eiopa-stress/ref/orsa-checklist`).catch(() => null),
          axios.get(`${API}/api/v1/eiopa-stress/ref/scenarios`).catch(() => null),
        ]);
        setResult(assess?.data || seed);
        setChecklist(cl?.data?.checklist || null);
        setScenarios(sc?.data?.scenarios || null);
      } catch {
        setResult(seed);
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo insurer — EIOPA Art. 45a ORSA climate stress test with seed fallback data." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">EIOPA ORSA Climate Stress Test</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Solvency II Art. 45a · 4 EIOPA 2022 climate scenarios · Capital adequacy & ORSA checklist
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['Solvency II', 'Art. 45a', 'EIOPA 2022', 'ORSA'].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

      {/* Tab bar */}
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

      {loading && tab === 'dashboard' && (
        <div className="text-xs text-gray-400 py-8 text-center flex items-center justify-center gap-2">
          <div className="w-3 h-3 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
          Running stress assessment…
        </div>
      )}

      {(!loading || tab !== 'dashboard') && (
        <>
          {tab === 'dashboard'  && <StressDashboard result={result} />}
          {tab === 'checklist'  && <OrsaChecklist checklistData={checklist} />}
          {tab === 'scenarios'  && <ScenariosPanel scenariosData={scenarios} />}
          {tab === 'capital'    && <CapitalAnalysis result={result} />}
        </>
      )}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Regulatory basis:</span> Solvency II Art. 45a (IORP II equivalent) · EIOPA Opinion on Climate Change Scenarios in ORSA (Apr 2022) · EIOPA SFCR climate metrics guidance</p>
        <p><span className="font-semibold text-gray-500">Scenarios:</span> Instantaneous hot-house world · Instantaneous disorderly transition · LT net-zero 2050 · LT delayed transition</p>
      </div>
    </div>
  );
}
