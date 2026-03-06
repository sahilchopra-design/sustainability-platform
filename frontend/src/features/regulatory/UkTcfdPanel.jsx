/**
 * UK Mandatory TCFD Panel
 * FCA Policy Statement PS21/23, LR 9.8.6R (premium listed companies),
 * DTR 7.2 (UK PIE >500 employees), Companies Act 2006 s.414CB (strategic reports).
 * Climate-related financial disclosures aligned to TCFD 2023 Recommendations.
 */
import React, { useState } from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function Badge({ label, color = 'bg-[#0d1424]/[0.06] text-white/40' }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}
function Card({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06] ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-white/[0.05]">
          {title && <h2 className="text-sm font-semibold text-white/90">{title}</h2>}
          {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}

/* ── Reference Data ───────────────────────────────────────────────────────── */
const ENTITY_TYPES = [
  { v: 'premium_listed', l: 'Premium Listed (LR 9.8.6R) — Mandatory from 1 Jan 2021' },
  { v: 'standard_listed', l: 'Standard Listed (LR 9.8.7A) — Mandatory from 1 Jan 2022' },
  { v: 'aim', l: 'AIM (AIM Rule 26) — Mandatory for large AIM companies from Jan 2022' },
  { v: 'uk_pie', l: 'UK PIE >500 employees (DTR 7.2 + Companies Act) — From FY2022' },
  { v: 'large_company', l: 'Large UK Company (Companies Act s.414CB) — From FY2022' },
  { v: 'asset_manager', l: 'FCA Asset Manager / Owner (PS21/23) — Mandatory from Jun 2022' },
];

const UK_TCFD_PILLARS = [
  {
    id: 'governance', label: 'Governance', color: 'border-blue-500/20 bg-blue-500/[0.04]',
    elements: [
      {
        id: 'gov_1', code: 'G-A',
        label: "Board's oversight of climate-related risks and opportunities",
        uk_note: 'Describe board committees and processes; LR 9.8.6R requires named responsibility',
      },
      {
        id: 'gov_2', code: 'G-B',
        label: "Management's role in assessing and managing climate-related risks and opportunities",
        uk_note: 'Senior management climate role; sustainability committee if applicable',
      },
    ],
  },
  {
    id: 'strategy', label: 'Strategy', color: 'border-cyan-500/20 bg-cyan-500/[0.04]',
    elements: [
      {
        id: 'str_1', code: 'S-A',
        label: 'Climate-related risks and opportunities over short, medium and long term',
        uk_note: 'Physical and transition risks; time horizons consistent with financial planning',
      },
      {
        id: 'str_2', code: 'S-B',
        label: 'Impact of climate-related risks and opportunities on business, strategy and financial planning',
        uk_note: 'Financial quantification encouraged; cross-reference UK Taxonomy alignment',
      },
      {
        id: 'str_3', code: 'S-C',
        label: 'Resilience of strategy, considering different climate-related scenarios (≥2°C and well-below 2°C)',
        uk_note: 'Scenario analysis mandatory for premium listed; NGFS/IEA NZE scenarios preferred',
      },
    ],
  },
  {
    id: 'risk_mgmt', label: 'Risk Management', color: 'border-purple-500/20 bg-purple-500/[0.04]',
    elements: [
      {
        id: 'rm_1', code: 'R-A',
        label: "Organisation's processes for identifying and assessing climate-related risks",
        uk_note: 'Physical and transition risk taxonomy; severity and likelihood assessments',
      },
      {
        id: 'rm_2', code: 'R-B',
        label: "Organisation's processes for managing climate-related risks",
        uk_note: 'Risk appetite statement; integration with board risk committee',
      },
      {
        id: 'rm_3', code: 'R-C',
        label: 'Integration of climate risk identification and management into overall risk management',
        uk_note: 'ERM integration; ICAAP/ILAAP/ORSA cross-reference for regulated entities',
      },
    ],
  },
  {
    id: 'metrics', label: 'Metrics & Targets', color: 'border-emerald-500/20 bg-emerald-500/[0.04]',
    elements: [
      {
        id: 'mt_1', code: 'M-A',
        label: 'Metrics used to assess climate-related risks and opportunities (Scope 1, 2 and if appropriate 3 GHG)',
        uk_note: 'GHG Protocol alignment; Scope 3 encouraged but comply-or-explain basis',
      },
      {
        id: 'mt_2', code: 'M-B',
        label: 'Scope 1, 2 and 3 GHG emissions and related risks',
        uk_note: 'SECR (Streamlined Energy and Carbon Reporting) provides Scope 1+2 baseline',
      },
      {
        id: 'mt_3', code: 'M-C',
        label: 'Targets used to manage climate-related risks and opportunities and performance against targets',
        uk_note: 'Net zero target (UK mandate: 2050); interim targets aligned to SBTi or UK pathway',
      },
    ],
  },
];

const MATURITY_LEVELS = [
  { v: 0, l: '0 — Not Disclosed' },
  { v: 1, l: '1 — Partial / Exploratory' },
  { v: 2, l: '2 — Developing' },
  { v: 3, l: '3 — Substantially Compliant' },
  { v: 4, l: '4 — Leading Practice' },
];

const maturityColor = (m) =>
  m >= 3 ? 'text-emerald-400' : m >= 2 ? 'text-amber-400' : m >= 1 ? 'text-blue-300' : 'text-red-500';

/* ── Component ────────────────────────────────────────────────────────────── */
export default function UkTcfdPanel() {
  const [entityType, setEntityType] = useState('premium_listed');
  const [disclosures, setDisclosures] = useState(() => {
    const init = {};
    UK_TCFD_PILLARS.flatMap(p => p.elements).forEach(e => { init[e.id] = { maturity: 0, notes: '' }; });
    return init;
  });
  const [result, setResult] = useState(null);

  const set = (id, k, v) => setDisclosures(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));

  const compute = () => {
    const pillarScores = UK_TCFD_PILLARS.map(pillar => {
      const avg = pillar.elements.reduce((s, e) => s + (disclosures[e.id]?.maturity || 0), 0) / pillar.elements.length;
      return { pillar: pillar.label, score: parseFloat(avg.toFixed(2)), maxScore: 4 };
    });
    const overall = pillarScores.reduce((s, p) => s + p.score, 0) / pillarScores.length;

    const gaps = UK_TCFD_PILLARS.flatMap(pillar =>
      pillar.elements
        .filter(e => (disclosures[e.id]?.maturity || 0) < 3)
        .map(e => ({ pillar: pillar.label, code: e.code, label: e.label, maturity: disclosures[e.id]?.maturity || 0, uk_note: e.uk_note }))
    );

    setResult({ overall: parseFloat(overall.toFixed(2)), pillarScores, gaps });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="FCA PS21/23" color="bg-red-500/10 text-red-700" />
        <Badge label="LR 9.8.6R / DTR 7.2" color="bg-blue-400/10 text-blue-300" />
        <Badge label="Companies Act s.414CB" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="TCFD 2023 Recommendations" color="bg-purple-400/10 text-purple-300" />
        <Badge label="UK Green Finance Strategy" color="bg-emerald-400/10 text-emerald-400" />
      </div>

      <Card
        title="UK Mandatory TCFD — Disclosure Readiness"
        subtitle="Score each of the 11 TCFD recommended disclosures (4 pillars, 0–4 maturity). Premium listed companies must comply under LR 9.8.6R from 1 January 2021."
      >
        {/* Entity Setup */}
        <div className="mb-6">
          <label className="block text-xs font-medium text-white/60 mb-1">Entity / Registrant Type</label>
          <select
            className="w-full md:w-1/2 border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
            value={entityType} onChange={e => setEntityType(e.target.value)}
          >
            {ENTITY_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
          </select>
        </div>

        {/* Pillar Scoring */}
        <div className="space-y-5">
          {UK_TCFD_PILLARS.map(pillar => (
            <div key={pillar.id} className={`border rounded-xl p-4 ${pillar.color}`}>
              <h3 className="text-sm font-bold text-white/80 mb-3">{pillar.label}</h3>
              <div className="space-y-3">
                {pillar.elements.map(el => (
                  <div key={el.id} className="bg-[#0d1424] rounded-lg p-3 border border-white/[0.04]">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge label={el.code} color="bg-white/[0.06] text-white/50" />
                        <p className="text-xs text-white/70">{el.label}</p>
                      </div>
                    </div>
                    <p className="text-[10px] text-cyan-300/50 mb-2 italic">{el.uk_note}</p>
                    <div className="flex items-center gap-3">
                      <select
                        className="border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none w-56"
                        value={disclosures[el.id]?.maturity || 0}
                        onChange={e => set(el.id, 'maturity', parseInt(e.target.value))}
                      >
                        {MATURITY_LEVELS.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                      </select>
                      <input
                        className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/40 focus:outline-none"
                        placeholder="Evidence / notes / where disclosed"
                        value={disclosures[el.id]?.notes || ''}
                        onChange={e => set(el.id, 'notes', e.target.value)}
                      />
                      <span className={`text-sm font-bold w-5 text-center ${maturityColor(disclosures[el.id]?.maturity || 0)}`}>
                        {disclosures[el.id]?.maturity || 0}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={compute}
            className="bg-cyan-400 hover:bg-cyan-300 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors"
          >
            Generate UK TCFD Assessment
          </button>
        </div>
      </Card>

      {result && (
        <div className="space-y-6">
          {/* KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="col-span-2 md:col-span-1 bg-gradient-to-br from-red-500/20 to-blue-500/20 border border-red-400/10 rounded-xl p-5 text-center">
              <p className="text-xs text-red-200/60 mb-1">Overall UK TCFD Score</p>
              <p className="text-3xl font-bold text-white">{result.overall.toFixed(1)}<span className="text-lg text-white/40">/4</span></p>
              <p className="text-xs text-red-200/60 mt-1">
                {result.overall >= 3 ? 'Advanced' : result.overall >= 2 ? 'Developing' : 'Initial'}
              </p>
            </div>
            {result.pillarScores.map((p, i) => (
              <div key={i} className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
                <p className="text-xs text-white/40 mb-1">{p.pillar}</p>
                <p className={`text-xl font-bold ${p.score >= 3 ? 'text-emerald-400' : p.score >= 2 ? 'text-amber-400' : 'text-red-500'}`}>
                  {p.score.toFixed(1)}<span className="text-xs text-white/30">/4</span>
                </p>
              </div>
            ))}
          </div>

          {/* Radar chart */}
          <Card title="TCFD Pillar Scores — Radar View">
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={result.pillarScores}>
                <PolarGrid stroke="#ffffff10" />
                <PolarAngleAxis dataKey="pillar" tick={{ fontSize: 10, fill: '#ffffff60' }} />
                <PolarRadiusAxis domain={[0, 4]} tick={{ fontSize: 8, fill: '#ffffff40' }} />
                <Radar name="Score" dataKey="score" stroke="#ef4444" fill="#ef4444" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>

          {/* Gaps */}
          {result.gaps.length > 0 && (
            <Card title={`UK TCFD Disclosure Gaps — ${result.gaps.length} recommendations below maturity 3`}>
              <div className="space-y-2">
                {result.gaps.map((g, i) => (
                  <div key={i} className="border border-amber-200 bg-amber-500/10 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge label={g.code} color="bg-amber-500/20 text-amber-400" />
                      <Badge label={g.pillar} color="bg-white/[0.06] text-white/40" />
                      <span className={`text-xs font-bold ml-auto ${maturityColor(g.maturity)}`}>{g.maturity}/4</span>
                    </div>
                    <p className="text-xs text-amber-700">{g.label}</p>
                    <p className="text-[10px] text-amber-600/70 mt-1 italic">{g.uk_note}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Comply-or-explain bar chart */}
          <Card title="Pillar Scores vs Target (4.0 = Leading Practice)">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={result.pillarScores}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="pillar" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                <YAxis domain={[0, 4]} ticks={[0,1,2,3,4]} tick={{ fontSize: 9, fill: '#ffffff60' }} />
                <Tooltip contentStyle={{ background: '#0d1424', border: '1px solid #ffffff10', borderRadius: 8 }} formatter={v => [`${v}/4`]} />
                <Bar dataKey="score" name="Maturity Score" radius={[4, 4, 0, 0]}>
                  {result.pillarScores.map((p, i) => (
                    <Cell key={i} fill={p.score >= 3 ? '#10b981' : p.score >= 2 ? '#f59e0b' : '#ef4444'} />
                  ))}
                </Bar>
                <Bar dataKey="maxScore" name="Target (4)" fill="#ffffff08" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}

      {/* Methodology */}
      <Card title="Methodology Reference" className="border-white/[0.03]">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-white/50">
          <div><span className="font-semibold text-white/70">Listed:</span> FCA LR 9.8.6R (from 1 Jan 2021)</div>
          <div><span className="font-semibold text-white/70">Asset Mgrs:</span> FCA PS21/23 (from Jun 2022)</div>
          <div><span className="font-semibold text-white/70">Large Co:</span> Companies Act 2006 s.414CB (FY2022)</div>
          <div><span className="font-semibold text-white/70">Framework:</span> TCFD 2023 Recommendations</div>
          <div><span className="font-semibold text-white/70">Scenarios:</span> NGFS, IEA WEO/NZE required</div>
          <div><span className="font-semibold text-white/70">GHG:</span> SECR (Scope 1+2) + Scope 3 encouraged</div>
        </div>
      </Card>
    </div>
  );
}
