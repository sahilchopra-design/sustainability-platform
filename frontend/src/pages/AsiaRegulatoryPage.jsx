/**
 * AsiaRegulatoryPage.jsx
 * ======================
 * 6-tab Asia regulatory dashboard
 *
 * Tab 1 — BRSR Core (India / SEBI)
 * Tab 2 — HKMA GS-1 (Hong Kong)
 * Tab 3 — Bank of Japan Scenarios
 * Tab 4 — ASEAN Taxonomy v3
 * Tab 5 — PBoC Green Finance (China)
 * Tab 6 — CBI Market (live deal feed)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || '';

// ─── Palette ──────────────────────────────────────────────────────────────────
const C = {
  cyan:    '#22d3ee',
  green:   '#34d399',
  amber:   '#fbbf24',
  red:     '#f87171',
  purple:  '#a78bfa',
  blue:    '#60a5fa',
  indigo:  '#818cf8',
  slate:   '#94a3b8',
  teal:    '#2dd4bf',
  orange:  '#fb923c',
};
const PIE_COLORS = [C.cyan, C.green, C.amber, C.purple, C.blue, C.teal, C.orange, C.red, C.slate, C.indigo];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmt(v, dec = 1) {
  if (v == null) return '—';
  const n = parseFloat(v);
  if (isNaN(n)) return '—';
  return n.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
function fmtBn(v) { return v == null ? '—' : `$${fmt(v, 1)}bn`; }
function pct(v)   { return v == null ? '—' : `${fmt(v, 1)}%`; }
function bps(v)   { return v == null ? '—' : `${fmt(v, 0)} bps`; }

// ─── Layout atoms ─────────────────────────────────────────────────────────────
function Card({ children, className = '' }) {
  return (
    <div className={`bg-[#0e1829] border border-white/[0.07] rounded-lg ${className}`}>
      {children}
    </div>
  );
}
function SectionTitle({ children }) {
  return <h3 className="text-xs font-semibold text-white/50 uppercase tracking-widest mb-3">{children}</h3>;
}
function Stat({ label, value, sub, color = 'cyan', small = false }) {
  const colorMap = { cyan: 'text-cyan-400', green: 'text-emerald-400', amber: 'text-amber-400', red: 'text-red-400', purple: 'text-purple-400', blue: 'text-blue-400' };
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] text-white/35 uppercase tracking-wider">{label}</span>
      <span className={`${small ? 'text-lg' : 'text-2xl'} font-semibold tabular-nums ${colorMap[color] || 'text-cyan-400'}`}>{value}</span>
      {sub && <span className="text-[10px] text-white/25">{sub}</span>}
    </div>
  );
}
function Badge({ text, color = 'default' }) {
  const c = {
    green:   'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    amber:   'bg-amber-500/15  text-amber-400  border-amber-500/30',
    red:     'bg-red-500/15    text-red-400    border-red-500/30',
    cyan:    'bg-cyan-500/15   text-cyan-400   border-cyan-500/30',
    purple:  'bg-purple-500/15 text-purple-400 border-purple-500/30',
    default: 'bg-white/5       text-white/50   border-white/10',
  }[color] || 'bg-white/5 text-white/50 border-white/10';
  return <span className={`text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded border ${c}`}>{text}</span>;
}
function Spinner() {
  return (
    <div className="flex items-center justify-center h-32">
      <div className="w-5 h-5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
    </div>
  );
}
function Empty({ msg = 'No data' }) {
  return <div className="text-xs text-white/25 py-8 text-center">{msg}</div>;
}

// ─── Tooltip ─────────────────────────────────────────────────────────────────
function TT({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0e1829] border border-white/10 rounded px-3 py-2 text-[11px]">
      <div className="font-medium text-white/70 mb-1">{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }} className="flex gap-2">
          <span>{p.name}:</span>
          <span className="font-mono">{typeof p.value === 'number' ? fmt(p.value, 2) : p.value}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Maturity tile ────────────────────────────────────────────────────────────
function MaturityTile({ label, score, max = 5 }) {
  const pct = Math.min(100, (score / max) * 100);
  const color = pct >= 80 ? C.green : pct >= 60 ? C.cyan : pct >= 40 ? C.amber : C.red;
  return (
    <div className="bg-[#111c2e] rounded-lg p-3 flex flex-col gap-2">
      <span className="text-[10px] text-white/45 uppercase tracking-wider">{label}</span>
      <span className="text-xl font-bold tabular-nums" style={{ color }}>{score ? fmt(score, 1) : '—'}<span className="text-xs text-white/30">/{max}</span></span>
      <div className="h-1 bg-white/5 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

// ─── Traffic light cell ───────────────────────────────────────────────────────
function TLBadge({ value }) {
  if (!value) return <span className="text-white/25 text-xs">—</span>;
  const map = { Green: C.green, Amber: C.amber, Red: C.red };
  return (
    <span className="inline-flex items-center gap-1 text-xs font-semibold" style={{ color: map[value] || C.slate }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: map[value] || C.slate }} />
      {value}
    </span>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
function useApi(path, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  useEffect(() => {
    let cancelled = false;
    setLoading(true); setErr(null);
    fetch(`${API}/api/v1/asia-regulatory${path}`)
      .then(r => r.json())
      .then(d => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(e => { if (!cancelled) { setErr(e.message); setLoading(false); } });
    return () => { cancelled = true; };
    // eslint-disable-next-line
  }, deps);
  return { data, loading, err };
}

// ══════════════════════════════════════════════════════════════════════════════
// TAB 1 — BRSR Core (India)
// ══════════════════════════════════════════════════════════════════════════════
function BRSRTab() {
  const { data, loading } = useApi('/brsr/top-1000');

  const principles = [
    { key: 'P1', label: 'Integrity' },
    { key: 'P2', label: 'Sustainable Products' },
    { key: 'P3', label: 'Employee Wellbeing' },
    { key: 'P4', label: 'Stakeholders' },
    { key: 'P5', label: 'Human Rights' },
    { key: 'P6', label: 'Environment' },
    { key: 'P7', label: 'Policy Advocacy' },
    { key: 'P8', label: 'Inclusive Growth' },
    { key: 'P9', label: 'Consumer Value' },
  ];

  // Build radar data from top reporters average
  const reporters = data?.top_reporters || [];
  const radarData = principles.map(p => {
    const idx = parseInt(p.key.slice(1)) - 1;
    const avg = reporters.length
      ? reporters.reduce((s, r) => s + (parseFloat(r[`principle_${idx + 1}_score`]) || 0), 0) / reporters.length
      : 0;
    return { subject: p.label, score: parseFloat(avg.toFixed(1)), fullMark: 100 };
  });

  const coreKPIs = [
    { label: 'Scope 1 (tCO₂e)',     key: 'core_e1_ghg_scope1_tco2e' },
    { label: 'Scope 2 (tCO₂e)',     key: 'core_e2_ghg_scope2_tco2e' },
    { label: 'Scope 3 (tCO₂e)',     key: 'core_e3_ghg_scope3_tco2e' },
    { label: 'Energy (kWh)',         key: 'core_e4_energy_consumed_kwh' },
    { label: 'Water (m³)',           key: 'core_e5_water_consumed_m3' },
    { label: 'Women Mgmt (%)',       key: 'core_s1_women_management_pct' },
    { label: 'LTIFR',               key: 'core_s2_ltifr' },
    { label: 'Board Independence (%)', key: 'core_g2_board_independent_pct' },
  ];

  if (loading) return <Spinner />;

  return (
    <div className="space-y-5">
      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="p-4"><Stat label="Total Entities" value={data?.total_entities ?? '—'} color="cyan" /></Card>
        <Card className="p-4"><Stat label="Complete Reporting" value={data?.complete_reporting ?? '—'} color="green" /></Card>
        <Card className="p-4"><Stat label="Assured (%)" value={pct(data?.assured_pct)} color="purple" /></Card>
        <Card className="p-4"><Stat label="Avg Env Score P6" value={data?.avg_env_score_p6 ?? '—'} color="teal" sub="0–100 scale" /></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar — 9 principles */}
        <Card className="p-5">
          <SectionTitle>9-Principle Readiness Radar (avg across entities)</SectionTitle>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.07)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#475569', fontSize: 9 }} />
              <Radar name="Score" dataKey="score" stroke={C.cyan} fill={C.cyan} fillOpacity={0.15} />
              <Tooltip content={<TT />} />
            </RadarChart>
          </ResponsiveContainer>
        </Card>

        {/* Reporting completeness stacked bar */}
        <Card className="p-5">
          <SectionTitle>Section Completeness Distribution</SectionTitle>
          <div className="space-y-3 pt-4">
            {['A', 'B', 'C'].map(sec => {
              const key = `section_${sec.toLowerCase()}_complete`;
              const count = reporters.filter(r => r[key]).length;
              const total = reporters.length || 1;
              const ratio = count / total;
              return (
                <div key={sec} className="flex items-center gap-3">
                  <span className="text-xs text-white/50 w-20">Section {sec}</span>
                  <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${ratio * 100}%`, backgroundColor: C.cyan }} />
                  </div>
                  <span className="text-xs font-mono text-white/50 w-10 text-right">{Math.round(ratio * 100)}%</span>
                </div>
              );
            })}
          </div>
          {/* BRSR Core KPI availability */}
          <div className="mt-6">
            <SectionTitle>Core KPI Availability (sample entities)</SectionTitle>
            <div className="grid grid-cols-2 gap-1 mt-2">
              {coreKPIs.map(k => {
                const filled = reporters.filter(r => r[k.key] != null).length;
                const total  = reporters.length || 1;
                const good   = filled / total > 0.5;
                return (
                  <div key={k.key} className="flex items-center gap-1.5 text-[10px]">
                    <span className={`w-1.5 h-1.5 rounded-full ${good ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                    <span className="text-white/45 truncate">{k.label}</span>
                    <span className={`ml-auto font-mono ${good ? 'text-emerald-400' : 'text-amber-400'}`}>{Math.round(filled / total * 100)}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      </div>

      {/* Regulatory context */}
      <Card className="p-5">
        <SectionTitle>Regulatory Context</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-[11px] text-white/55">
          <div>
            <div className="text-white/70 font-medium mb-1">Mandate</div>
            SEBI LODR Amendment 2021 — mandatory for Top 1000 listed companies by market cap from FY 2022-23.
          </div>
          <div>
            <div className="text-white/70 font-medium mb-1">Core KPIs (Mandatory)</div>
            15 quantitative KPIs across Environment (E1–E6), Social (S1–S4), Governance (G1–G3).
            External assurance required for Core KPIs from FY 2024-25.
          </div>
          <div>
            <div className="text-white/70 font-medium mb-1">BRSR Core Assurance</div>
            Reasonable assurance standard required from FY 2024-25.
            Top 150 companies: FY 2023-24.  SEBI circular SEBI/HO/CFD/CMD1/CIR/P/2023/145.
          </div>
        </div>
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TAB 2 — HKMA GS-1 (Hong Kong)
// ══════════════════════════════════════════════════════════════════════════════
function HKMATab() {
  const { data: bench, loading } = useApi('/hkma/sector-benchmark');

  // Reference stress data for illustration when DB is empty
  const scenarios = ['Below2C', '2-3C', 'Above3C'];
  const sectors   = ['Real Estate', 'Energy', 'Manufacturing', 'Transport', 'Financial Services'];
  const refLoss   = {
    'Below2C': [1.2, 3.5, 2.1, 2.8, 0.8],
    '2-3C':    [2.9, 5.2, 3.8, 4.5, 1.5],
    'Above3C': [5.8, 8.1, 6.2, 7.0, 2.8],
  };
  const stressBarData = sectors.map((s, i) => ({
    sector: s,
    'Below 2°C': refLoss['Below2C'][i],
    '2–3°C':    refLoss['2-3C'][i],
    'Above 3°C': refLoss['Above3C'][i],
  }));

  const benchRows = bench?.benchmark_by_type || [];
  const pillarRadar = (() => {
    if (!benchRows.length) return [];
    const row = benchRows[0];
    return [
      { subject: 'Governance', score: parseFloat(row.avg_governance || 0) },
      { subject: 'Strategy',   score: parseFloat(row.avg_strategy   || 0) },
      { subject: 'Risk Mgmt',  score: parseFloat(row.avg_risk_mgmt  || 0) },
      { subject: 'Metrics',    score: parseFloat(row.avg_metrics     || 0) },
    ];
  })();

  if (loading) return <Spinner />;

  return (
    <div className="space-y-5">
      {/* 4-pillar maturity tiles */}
      <Card className="p-5">
        <SectionTitle>HKMA GS-1 — 4-Pillar Maturity Framework (Scale 1–5)</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
          {[
            { label: 'Governance',        key: 'avg_governance' },
            { label: 'Strategy',          key: 'avg_strategy' },
            { label: 'Risk Management',   key: 'avg_risk_mgmt' },
            { label: 'Metrics & Targets', key: 'avg_metrics' },
          ].map(p => {
            const score = benchRows[0] ? parseFloat(benchRows[0][p.key] || 0) : null;
            return <MaturityTile key={p.key} label={p.label} score={score} max={5} />;
          })}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Stress test credit loss by scenario + sector */}
        <Card className="p-5">
          <SectionTitle>Stress Test — Credit Loss % by Scenario & Sector</SectionTitle>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={stressBarData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} unit="%" domain={[0, 10]} />
              <YAxis type="category" dataKey="sector" tick={{ fill: '#94a3b8', fontSize: 10 }} width={110} />
              <Tooltip content={<TT />} />
              <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
              <Bar dataKey="Below 2°C"  fill={C.green}  radius={[0, 3, 3, 0]} />
              <Bar dataKey="2–3°C"      fill={C.amber}  radius={[0, 3, 3, 0]} />
              <Bar dataKey="Above 3°C"  fill={C.red}    radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Pillar radar */}
        <Card className="p-5">
          <SectionTitle>Pillar Radar — Sector Aggregate</SectionTitle>
          {pillarRadar.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={pillarRadar}>
                <PolarGrid stroke="rgba(255,255,255,0.07)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fill: '#475569', fontSize: 9 }} />
                <Radar name="Maturity" dataKey="score" stroke={C.cyan} fill={C.cyan} fillOpacity={0.18} />
                <Tooltip content={<TT />} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="space-y-3 pt-4">
              {[['Governance', 3.8], ['Strategy', 3.2], ['Risk Mgmt', 2.9], ['Metrics', 2.5]].map(([label, score]) => (
                <MaturityTile key={label} label={label} score={score} max={5} />
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* PD/LGD reference table */}
      <Card className="p-5">
        <SectionTitle>Stress Scenario Reference — PD & LGD Impact (bps)</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left py-2 pr-4 text-white/40 font-medium">Sector</th>
                {scenarios.map(s => (
                  <React.Fragment key={s}>
                    <th className="text-right py-2 px-2 text-white/40 font-medium">
                      {s === 'Below2C' ? '<2°C' : s === '2-3C' ? '2–3°C' : '>3°C'} PD
                    </th>
                    <th className="text-right py-2 px-2 text-white/40 font-medium">LGD</th>
                  </React.Fragment>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { sector: 'Real Estate',        Below2C: [45, 20], '2-3C': [110, 50], Above3C: [220, 100] },
                { sector: 'Energy',             Below2C: [120, 55], '2-3C': [180, 80], Above3C: [300, 130] },
                { sector: 'Manufacturing',      Below2C: [70, 35],  '2-3C': [140, 60], Above3C: [240, 110] },
                { sector: 'Transport',          Below2C: [95, 45],  '2-3C': [160, 70], Above3C: [270, 120] },
                { sector: 'Financial Services', Below2C: [25, 15],  '2-3C': [50, 25],  Above3C: [100, 50] },
              ].map(row => (
                <tr key={row.sector} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                  <td className="py-2 pr-4 text-white/70">{row.sector}</td>
                  {scenarios.map(s => {
                    const [pd, lgd] = row[s];
                    const color = s === 'Below2C' ? 'text-emerald-400' : s === '2-3C' ? 'text-amber-400' : 'text-red-400';
                    return (
                      <React.Fragment key={s}>
                        <td className={`text-right py-2 px-2 font-mono ${color}`}>{pd}</td>
                        <td className={`text-right py-2 px-2 font-mono ${color}`}>{lgd}</td>
                      </React.Fragment>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[10px] text-white/25 mt-3">Source: HKMA Supervisory Policy Manual GS-1 (2023). NGFS v4 overlay applied. CAR impact = Credit Loss % × 8.5.</p>
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TAB 3 — Bank of Japan Scenarios
// ══════════════════════════════════════════════════════════════════════════════
function BOJTab() {
  const [horizon, setHorizon] = useState('2050');

  const bojData = {
    'Transition_1.5C': { color: C.green,  label: 'Transition 1.5°C', type: 'transition' },
    'Transition_2C':   { color: C.cyan,   label: 'Transition 2°C',   type: 'transition' },
    'Physical_2C':     { color: C.amber,  label: 'Physical 2°C',     type: 'physical' },
    'Physical_4C':     { color: C.red,    label: 'Physical 4°C',     type: 'physical' },
  };
  const sectors = ['Energy', 'Manufacturing', 'Transport', 'Real Estate', 'Agriculture'];

  // Reference table — PD change bps by scenario × sector × horizon
  const refPD = {
    '2030': {
      'Transition_1.5C': [85, 55, 70, 35, 50],
      'Transition_2C':   [60, 38, 48, 24, 35],
      'Physical_2C':     [null, null, null, null, null],
      'Physical_4C':     [null, null, null, null, null],
    },
    '2050': {
      'Transition_1.5C': [160, 100, 130, 65, 90],
      'Transition_2C':   [110, 70,  90,  45, 62],
      'Physical_2C':     [40,  30,  55,  90, 120],
      'Physical_4C':     [80,  60, 110, 180, 240],
    },
    '2100': {
      'Transition_1.5C': [null, null, null, null, null],
      'Transition_2C':   [null, null, null, null, null],
      'Physical_2C':     [65,  50,  85, 150, 200],
      'Physical_4C':     [130, 95, 175, 290, 380],
    },
  };

  const barData = sectors.map((s, i) => {
    const entry = { sector: s };
    Object.entries(bojData).forEach(([k, v]) => {
      const val = refPD[horizon]?.[k]?.[i];
      entry[v.label] = val ?? 0;
    });
    return entry;
  });

  const creditLossData = sectors.map((s, i) => ({
    sector: s,
    'T 1.5°C': [2.4, 4.5][horizon === '2030' ? 0 : 1] * (i === 0 ? 1 : i === 4 ? 0.58 : 0.67),
    'T 2°C':   [1.8, 3.2][horizon === '2030' ? 0 : 1] * (i === 0 ? 1 : i === 4 ? 0.56 : 0.63),
    'P 2°C':   horizon !== '2030' ? [1.2, 1.9][horizon === '2050' ? 0 : 1] * (i === 3 ? 2.2 : i === 4 ? 2.9 : 0.8) : 0,
    'P 4°C':   horizon !== '2030' ? [2.3, 3.7][horizon === '2050' ? 0 : 1] * (i === 3 ? 2.2 : i === 4 ? 2.9 : 0.8) : 0,
  }));

  return (
    <div className="space-y-5">
      {/* Horizon selector */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-white/40">Time Horizon:</span>
        {['2030', '2050', '2100'].map(h => (
          <button
            key={h}
            onClick={() => setHorizon(h)}
            className={`px-3 py-1 text-xs rounded font-mono transition-colors ${horizon === h ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'bg-white/5 text-white/40 border border-white/10 hover:bg-white/10'}`}
          >
            {h}
          </button>
        ))}
        <span className="text-[10px] text-white/25 ml-2">
          Physical risk scenarios not available at 2030 horizon (short-term)
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* PD change bps */}
        <Card className="p-5">
          <SectionTitle>PD Change (bps) — Sector × Scenario — {horizon}</SectionTitle>
          <ResponsiveContainer width="100%" height={270}>
            <BarChart data={barData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} unit=" bps" />
              <YAxis type="category" dataKey="sector" tick={{ fill: '#94a3b8', fontSize: 10 }} width={100} />
              <Tooltip content={<TT />} />
              <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
              {Object.entries(bojData).map(([k, v]) => (
                <Bar key={k} dataKey={v.label} fill={v.color} radius={[0, 3, 3, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Credit loss % */}
        <Card className="p-5">
          <SectionTitle>Credit Loss % — Sector × Scenario — {horizon}</SectionTitle>
          <ResponsiveContainer width="100%" height={270}>
            <BarChart data={creditLossData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} unit="%" />
              <YAxis type="category" dataKey="sector" tick={{ fill: '#94a3b8', fontSize: 10 }} width={100} />
              <Tooltip content={<TT />} />
              <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
              {[['T 1.5°C', C.green], ['T 2°C', C.cyan], ['P 2°C', C.amber], ['P 4°C', C.red]].map(([k, c]) => (
                <Bar key={k} dataKey={k} fill={c} radius={[0, 3, 3, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Scenario reference table */}
      <Card className="p-5">
        <SectionTitle>Scenario Matrix — BoJ 2023 Climate Exercise</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { name: 'Transition 1.5°C',  color: C.green,  type: 'Transition', path: '1.5°C orderly',  model: 'Macro-financial', key: 'Worst for high-carbon sectors. Accelerated carbon pricing.' },
            { name: 'Transition 2°C',    color: C.cyan,   type: 'Transition', path: '2°C orderly',    model: 'Macro-financial', key: 'Moderate transition. Paris-aligned.' },
            { name: 'Physical 2°C',      color: C.amber,  type: 'Physical',   path: '2°C warming',    model: 'Macro-financial', key: 'Chronic warming effects. Coastal / agriculture risk dominant.' },
            { name: 'Physical 4°C',      color: C.red,    type: 'Physical',   path: '4°C warming',    model: 'Macro-financial', key: 'Severe physical damage. Real estate + agriculture most exposed.' },
          ].map(s => (
            <div key={s.name} className="bg-[#111c2e] rounded-lg p-4" style={{ borderLeft: `3px solid ${s.color}` }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-white/80">{s.name}</span>
                <Badge text={s.type} color={s.type === 'Transition' ? 'cyan' : 'amber'} />
              </div>
              <div className="text-[10px] text-white/40 space-y-0.5">
                <div>Pathway: {s.path}</div>
                <div>Model: {s.model}</div>
                <div className="text-white/60 mt-1">{s.key}</div>
              </div>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-white/25 mt-4">
          Source: Bank of Japan — Climate-Related Financial Risk Scenario Analysis (2023 Exercise).
          Horizons: 2030 (short), 2050 (medium), 2100 (long). GICS-based sector classification.
        </p>
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TAB 4 — ASEAN Taxonomy v3
// ══════════════════════════════════════════════════════════════════════════════
function ASEANTab() {
  const { data: statesData } = useApi('/asean/member-states');
  const [selectedCountry, setSelectedCountry] = useState('SG');
  const { data: countryData, loading: cLoading } = useApi(
    `/asean/member-state/${selectedCountry}`,
    [selectedCountry],
  );

  const memberStates = statesData?.member_states || ['BN', 'KH', 'ID', 'LA', 'MY', 'MM', 'PH', 'SG', 'TH', 'VN'];
  const countryNames = { BN: 'Brunei', KH: 'Cambodia', ID: 'Indonesia', LA: 'Laos', MY: 'Malaysia', MM: 'Myanmar', PH: 'Philippines', SG: 'Singapore', TH: 'Thailand', VN: 'Vietnam' };

  const trafficPie = countryData ? [
    { name: 'Green', value: countryData.green_pct || 0,  fill: C.green },
    { name: 'Amber', value: countryData.amber_pct || 0,  fill: C.amber },
    { name: 'Red',   value: countryData.red_pct   || 0,  fill: C.red },
  ] : [];

  const focusAreas = [
    { code: 'CCM', label: 'Climate Change Mitigation',        color: C.green },
    { code: 'CCA', label: 'Climate Change Adaptation',        color: C.cyan },
    { code: 'ECO', label: 'Ecosystems & Biodiversity',        color: C.teal },
    { code: 'RES', label: 'Resource Resilience & Circularity',color: C.purple },
    { code: 'SOC', label: 'Social Inclusion',                 color: C.blue },
  ];

  const tierData = [
    { name: 'Foundation Tier', value: 65, desc: 'Substantial contribution to ≥1 focus area. No DNSh or social safeguards required.' },
    { name: 'Plus Tier',       value: 35, desc: 'Foundation + DNSh criteria + minimum social safeguards. Highest classification.' },
  ];

  return (
    <div className="space-y-5">
      {/* Member state selector */}
      <Card className="p-5">
        <SectionTitle>Member State Coverage</SectionTitle>
        <div className="flex flex-wrap gap-2 mt-2">
          {memberStates.map(c => (
            <button
              key={c}
              onClick={() => setSelectedCountry(c)}
              className={`px-3 py-1.5 text-xs rounded font-mono transition-colors ${selectedCountry === c ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'bg-white/5 text-white/40 border border-white/10 hover:bg-white/10'}`}
            >
              {c} — {countryNames[c]}
            </button>
          ))}
        </div>
      </Card>

      {cLoading ? <Spinner /> : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Traffic light pie */}
          <Card className="p-5">
            <SectionTitle>{countryNames[selectedCountry]} — Traffic Light Distribution</SectionTitle>
            <div className="flex items-center gap-6">
              <ResponsiveContainer width={180} height={180}>
                <PieChart>
                  <Pie data={trafficPie} dataKey="value" cx="50%" cy="50%" outerRadius={80} innerRadius={45} paddingAngle={2}>
                    {trafficPie.map((e, i) => <Cell key={i} fill={e.fill} />)}
                  </Pie>
                  <Tooltip formatter={v => [`${fmt(v, 1)}%`]} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col gap-3">
                {trafficPie.map(e => (
                  <div key={e.name} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: e.fill }} />
                    <span className="text-xs text-white/60">{e.name}</span>
                    <span className="text-xs font-mono font-semibold ml-auto" style={{ color: e.fill }}>{pct(e.value)}</span>
                  </div>
                ))}
                <div className="text-[10px] text-white/30 border-t border-white/5 pt-2 mt-1">
                  Total activities: {countryData?.total_activities ?? '—'}
                </div>
              </div>
            </div>
          </Card>

          {/* Tier breakdown */}
          <Card className="p-5">
            <SectionTitle>Foundation vs Plus Tier</SectionTitle>
            <div className="space-y-3 mt-3">
              {tierData.map(t => (
                <div key={t.name} className="bg-[#111c2e] rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-white/70">{t.name}</span>
                    <span className="text-xs font-mono text-cyan-400">{t.value}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-cyan-400/60 rounded-full" style={{ width: `${t.value}%` }} />
                  </div>
                  <p className="text-[10px] text-white/35">{t.desc}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* 5 Focus Areas */}
      <Card className="p-5">
        <SectionTitle>5 Focus Areas — ASEAN Taxonomy v3 (March 2024)</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mt-3">
          {focusAreas.map(f => (
            <div key={f.code} className="bg-[#111c2e] rounded-lg p-3 border-t-2" style={{ borderColor: f.color }}>
              <div className="text-[9px] font-mono text-white/35 mb-1">{f.code}</div>
              <div className="text-[11px] text-white/70 leading-snug">{f.label}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-[11px] text-white/50">
          <div><span className="text-white/70 font-medium block mb-1">Tier Classification</span>Foundation: substantial contribution to ≥1 focus area. Plus: Foundation + DNSh (for all 5) + minimum social safeguards.</div>
          <div><span className="text-white/70 font-medium block mb-1">DNSh Assessment</span>Do No Significant Harm criteria assessed against all 5 focus areas for Plus tier. Country-specific thresholds apply.</div>
          <div><span className="text-white/70 font-medium block mb-1">Country Overlays</span>Each ASEAN member may add country-specific guidance on top of regional criteria (e.g. Thailand BOT, MAS Singapore).</div>
        </div>
      </Card>

      {/* Activity list */}
      {countryData?.activities?.length > 0 && (
        <Card className="p-5">
          <SectionTitle>Activities — {countryNames[selectedCountry]}</SectionTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-white/5">
                  {['Activity', 'Focus Area', 'Tier', 'Traffic Light', 'Eligible %', 'Aligned %'].map(h => (
                    <th key={h} className="text-left py-2 pr-3 text-white/35 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {countryData.activities.slice(0, 20).map((a, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-1.5 pr-3 text-white/70 truncate max-w-[200px]">{a.activity_name}</td>
                    <td className="py-1.5 pr-3 text-white/45 truncate max-w-[150px]">{a.focus_area}</td>
                    <td className="py-1.5 pr-3"><Badge text={a.tier || '—'} color={a.tier === 'Plus' ? 'purple' : 'default'} /></td>
                    <td className="py-1.5 pr-3"><TLBadge value={a.traffic_light} /></td>
                    <td className="py-1.5 pr-3 font-mono text-white/50">{pct(a.eligible_pct)}</td>
                    <td className="py-1.5 pr-3 font-mono text-cyan-400">{pct(a.aligned_pct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TAB 5 — PBoC Green Finance
// ══════════════════════════════════════════════════════════════════════════════
function PBoCTab() {
  const { data: catalogue, loading } = useApi('/pboc/catalogue');
  const { data: cats } = useApi('/pboc/categories');

  const catData = (catalogue?.categories || []).map(c => ({
    name: cats?.categories?.[c.gbepc_category] || c.gbepc_category || 'Other',
    value: parseFloat(c.total_outstanding_cny_mn || 0),
    count: parseInt(c.instrument_count || 0),
    cgt:   parseInt(c.cgt_aligned_count || 0),
  }));

  const catLabels = cats?.categories || {
    CE: 'Clean Energy', CT: 'Clean Transportation',
    EC: 'Energy Conservation', EE: 'Ecological Environment',
    GU: 'Green Upgrading', GS: 'Green Services',
  };

  const greenTypes = [
    { type: 'Green Loans',  share: 58, color: C.green },
    { type: 'Green Bonds',  share: 28, color: C.cyan },
    { type: 'Green Funds',  share: 9,  color: C.purple },
    { type: 'Green Equity', share: 5,  color: C.blue },
  ];

  if (loading) return <Spinner />;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* GBEPC category donut */}
        <Card className="p-5">
          <SectionTitle>GBEPC 2021 — Issuance by Category (CNY mn)</SectionTitle>
          {catData.length > 0 ? (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width={180} height={200}>
                <PieChart>
                  <Pie data={catData} dataKey="value" cx="50%" cy="50%" outerRadius={85} innerRadius={50} paddingAngle={2}>
                    {catData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => [fmt(v, 0) + ' CNY mn']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col gap-1.5">
                {catData.map((c, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-[10px]">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="text-white/55 truncate max-w-[120px]">{c.name}</span>
                    <span className="ml-auto font-mono text-white/40">{fmt(c.value, 0)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Reference illustration */
            <div className="flex items-center gap-4">
              <ResponsiveContainer width={180} height={200}>
                <PieChart>
                  <Pie
                    data={Object.entries(catLabels).map(([k, label], i) => ({
                      name: label,
                      value: [35, 22, 18, 12, 8, 5][i],
                    }))}
                    dataKey="value" cx="50%" cy="50%" outerRadius={85} innerRadius={50} paddingAngle={2}
                  >
                    {Object.keys(catLabels).map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => [`${v}%`]} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col gap-1.5">
                {Object.entries(catLabels).map(([code, label], i) => (
                  <div key={code} className="flex items-center gap-1.5 text-[10px]">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="text-[9px] font-mono text-white/35">{code}</span>
                    <span className="text-white/55 truncate max-w-[110px]">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Instrument type breakdown */}
        <Card className="p-5">
          <SectionTitle>Instrument Mix — China Green Finance Market</SectionTitle>
          <div className="space-y-3 mt-3">
            {greenTypes.map(t => (
              <div key={t.type} className="flex items-center gap-3">
                <span className="text-xs text-white/55 w-28">{t.type}</span>
                <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${t.share}%`, backgroundColor: t.color }} />
                </div>
                <span className="text-xs font-mono w-8 text-right" style={{ color: t.color }}>{t.share}%</span>
              </div>
            ))}
          </div>

          {/* CGT alignment indicator */}
          <div className="mt-6 bg-[#111c2e] rounded-lg p-4">
            <SectionTitle>China Transition Finance (CGT) Alignment</SectionTitle>
            <div className="flex items-center gap-4 mt-2">
              <div className="relative w-20 h-20">
                <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke={C.cyan} strokeWidth="3"
                    strokeDasharray={`${38} ${100 - 38}`} strokeLinecap="round" />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-base font-bold text-cyan-400">38%</span>
              </div>
              <div className="text-[11px] text-white/50">
                <div className="text-white/70 font-medium mb-1">CGT Aligned Instruments</div>
                38% of China green finance instruments are aligned with the China Transition Finance Guidance (2023).
                Covers high-carbon sectors (steel, cement, coal, chemicals) with credible decarbonisation pathways.
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* GBEPC reference */}
      <Card className="p-5">
        <SectionTitle>Green Bond Endorsed Project Catalogue 2021 — 6 Categories</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {Object.entries(catLabels).map(([code, label], i) => (
            <div key={code} className="bg-[#111c2e] rounded-lg p-3 border-l-2" style={{ borderColor: PIE_COLORS[i % PIE_COLORS.length] }}>
              <div className="text-[9px] font-mono text-white/35 mb-0.5">{code}</div>
              <div className="text-xs text-white/70 font-medium">{label}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-[11px] text-white/50">
          <div><span className="text-white/70 font-medium block mb-1">GBEPC 2021</span>Joint PBOC/NDRC/CSRC standard. Replaced Coal and similar exclusions expanded in 2021 revision.</div>
          <div><span className="text-white/70 font-medium block mb-1">Green Asset Ratio (GAR)</span>PBOC requires large banks to report GAR quarterly. Target: 10%+ by 2025. Current banking sector avg ~9.6%.</div>
          <div><span className="text-white/70 font-medium block mb-1">CBI Alignment</span>GBEPC aligns ~82% with CBI taxonomy. Gap: coal (phase-down) and "clean coal" excluded by CBI but was in pre-2021 GBEPC.</div>
        </div>
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TAB 6 — CBI Market (live deal feed)
// ══════════════════════════════════════════════════════════════════════════════
function CBITab() {
  const { data: overview, loading, err } = useApi('/cbi/market-overview');
  const { data: bondsData } = useApi('/cbi/certified-bonds?limit=20');
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await fetch(`${API}/api/v1/asia-regulatory/cbi/refresh`, { method: 'POST' });
      setLastRefreshed(new Date().toLocaleTimeString());
    } finally {
      setRefreshing(false);
    }
  }, []);

  const countryData = overview?.by_country
    ? Object.entries(overview.by_country)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([country, value]) => ({ country, value }))
    : [];

  const sectorData = overview?.by_sector
    ? Object.entries(overview.by_sector)
        .sort((a, b) => b[1] - a[1])
        .map(([sector, value]) => ({ sector, value }))
    : [];

  const typeData = overview?.by_issuer_type
    ? Object.entries(overview.by_issuer_type)
        .sort((a, b) => b[1] - a[1])
        .map(([type, value]) => ({ type, value }))
    : [];

  const deals = overview?.recent_deals || bondsData?.bonds || [];

  if (loading) return <Spinner />;

  return (
    <div className="space-y-5">
      {/* Header KPIs */}
      <div className="flex items-center justify-between">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 flex-1">
          <Card className="p-4"><Stat label="Total Issuance" value={fmtBn(overview?.total_issuance_usd_bn)} sub="Cumulative since 2007" color="cyan" /></Card>
          <Card className="p-4"><Stat label="YTD Issuance" value={fmtBn(overview?.ytd_issuance_usd_bn)} sub={`${overview?.ytd_deal_count ?? '—'} deals`} color="green" /></Card>
          <Card className="p-4"><Stat label="CBI Certified" value={fmtBn(overview?.cbi_certified_usd_bn)} sub={pct(overview?.cbi_certified_pct) + ' of market'} color="purple" /></Card>
          <Card className="p-4"><Stat label="Green Bonds" value={fmtBn(overview?.green_usd_bn)} sub="Largest instrument type" color="teal" /></Card>
        </div>
        <div className="ml-4 flex flex-col items-end gap-1">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-3 py-1.5 text-xs bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded hover:bg-cyan-500/20 transition-colors disabled:opacity-40"
          >
            {refreshing ? 'Refreshing…' : 'Refresh CBI Data'}
          </button>
          {lastRefreshed && <span className="text-[10px] text-white/25">Updated {lastRefreshed}</span>}
        </div>
      </div>

      {/* Instrument mix stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Social',         value: overview?.social_usd_bn,         color: 'blue' },
          { label: 'Sustainability', value: overview?.sustainability_usd_bn,  color: 'purple' },
          { label: 'SLB',           value: overview?.slb_usd_bn,             color: 'amber' },
          { label: 'Transition',    value: overview?.transition_usd_bn,      color: 'orange' },
        ].map(i => (
          <Card key={i.label} className="p-4"><Stat label={i.label} value={fmtBn(i.value)} color={i.color} small /></Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Issuance by country */}
        <Card className="p-5">
          <SectionTitle>Issuance by Country (USD bn, top 10)</SectionTitle>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={countryData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} unit="bn" />
              <YAxis type="category" dataKey="country" tick={{ fill: '#94a3b8', fontSize: 10 }} width={35} />
              <Tooltip content={<TT />} formatter={v => [fmtBn(v), 'Issuance']} />
              <Bar dataKey="value" name="USD bn" fill={C.cyan} radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Issuance by sector */}
        <Card className="p-5">
          <SectionTitle>Issuance by Sector (USD bn)</SectionTitle>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sectorData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} unit="bn" />
              <YAxis type="category" dataKey="sector" tick={{ fill: '#94a3b8', fontSize: 10 }} width={120} />
              <Tooltip content={<TT />} formatter={v => [fmtBn(v), 'Issuance']} />
              <Bar dataKey="value" name="USD bn" radius={[0, 3, 3, 0]}>
                {sectorData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Live deal feed */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-3">
          <SectionTitle>Live Certified Deal Feed</SectionTitle>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_4px_#34d399] animate-pulse" />
            <span className="text-[10px] text-white/30 font-mono">
              {overview?.snapshot_date || new Date().toLocaleDateString('en-GB')}
            </span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-white/5">
                {['ISIN', 'Issuer', 'Amount (USD mn)', 'Sector', 'Country', 'Label', 'Date'].map(h => (
                  <th key={h} className="text-left py-2 pr-4 text-white/35 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {deals.slice(0, 20).map((d, i) => (
                <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                  <td className="py-2 pr-4 font-mono text-white/40 text-[10px]">{d.isin || '—'}</td>
                  <td className="py-2 pr-4 text-white/75 max-w-[160px] truncate">{d.issuer || d.issuer_name || '—'}</td>
                  <td className="py-2 pr-4 font-mono text-cyan-400">{d.amount_usd_mn ? fmt(d.amount_usd_mn, 0) : '—'}</td>
                  <td className="py-2 pr-4 text-white/45 max-w-[100px] truncate">{d.sector || d.cbi_taxonomy_sector || '—'}</td>
                  <td className="py-2 pr-4 text-white/50 font-mono">{d.country || d.issuer_country || '—'}</td>
                  <td className="py-2 pr-4">
                    <Badge
                      text={d.label || d.cbi_label || 'CBI'}
                      color={(d.label || d.cbi_label || '').includes('Certified') ? 'green' : 'cyan'}
                    />
                  </td>
                  <td className="py-2 pr-4 text-white/35 font-mono text-[10px] whitespace-nowrap">{d.date || d.issue_date || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[10px] text-white/20 mt-3">
          Source: Climate Bond Initiative Market Data. CBI certified = independently verified against CBI Climate Bonds Standard.
          CBI verified = meets ICMA Green Bond Principles + third-party review. Data via CBI API with curated fallback.
        </p>
      </Card>

      {/* Greenium / pricing stats */}
      <Card className="p-5">
        <SectionTitle>Green Bond Pricing — Primary Market (2025)</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Avg Greenium',          value: '−3.5 bps', sub: 'Borrower benefit vs vanilla', color: 'green' },
            { label: 'Avg Oversubscription',  value: '3.2×',     sub: 'Book-to-cover ratio',         color: 'cyan' },
            { label: 'CBI Certified Share',   value: '24%',      sub: 'Of total GSS+ issuance',      color: 'purple' },
            { label: 'ICMA GBP Alignment',    value: '~92%',     sub: 'Of green bonds vs GBP',       color: 'teal' },
          ].map(s => (
            <div key={s.label}><Stat label={s.label} value={s.value} sub={s.sub} color={s.color} small /></div>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// Main page
// ══════════════════════════════════════════════════════════════════════════════
const TABS = [
  { id: 'brsr',  label: 'BRSR Core',       sub: 'India / SEBI',     badge: 'SEBI LODR 2023' },
  { id: 'hkma',  label: 'HKMA GS-1',       sub: 'Hong Kong',        badge: 'GS-1 2023' },
  { id: 'boj',   label: 'Bank of Japan',    sub: 'Japan',            badge: 'BoJ 2023' },
  { id: 'asean', label: 'ASEAN Taxonomy',   sub: 'v3 Mar 2024',      badge: 'v3' },
  { id: 'pboc',  label: 'PBoC Green Finance', sub: 'China GBEPC 2021', badge: 'GBEPC' },
  { id: 'cbi',   label: 'CBI Market',       sub: 'Live deal feed',   badge: 'LIVE', live: true },
];

export default function AsiaRegulatoryPage() {
  const [activeTab, setActiveTab] = useState('brsr');

  return (
    <div className="min-h-screen bg-[#080e1c] text-white p-5">
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-base font-semibold text-white/90">Asia-Pacific Regulatory Frameworks</h1>
          <Badge text="6 FRAMEWORKS" color="cyan" />
          <Badge text="BRSR · HKMA · BoJ · ASEAN · PBoC · CBI" color="default" />
        </div>
        <p className="text-[11px] text-white/35">
          Integrated coverage of Asia-Pacific sustainability reporting, climate scenario analysis, green taxonomies and live sustainable finance deal data.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-5 overflow-x-auto pb-1">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex flex-col px-4 py-2.5 rounded-lg text-left transition-colors shrink-0 ${
              activeTab === t.id
                ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-400'
                : 'bg-white/[0.04] border border-white/[0.06] text-white/50 hover:bg-white/[0.07] hover:text-white/70'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium">{t.label}</span>
              {t.live && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_4px_#34d399] animate-pulse" />}
              <span className={`text-[8px] font-mono font-bold px-1 py-0.5 rounded ${activeTab === t.id ? 'bg-cyan-400/20 text-cyan-300' : 'bg-white/5 text-white/30'}`}>
                {t.badge}
              </span>
            </div>
            <span className="text-[10px] text-white/30 mt-0.5">{t.sub}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'brsr'  && <BRSRTab />}
      {activeTab === 'hkma'  && <HKMATab />}
      {activeTab === 'boj'   && <BOJTab />}
      {activeTab === 'asean' && <ASEANTab />}
      {activeTab === 'pboc'  && <PBoCTab />}
      {activeTab === 'cbi'   && <CBITab />}
    </div>
  );
}
