/**
 * APRA CPG 229 Climate Change Financial Risks Panel
 * Prudential Practice Guide CPG 229 (November 2021)
 * Applicable to: ADIs (CPS 220), General Insurers (GPS 220), Life Insurers (LPS 220),
 *                Private Health Insurers (HPS 310), RSE Licensees (SPS 220).
 */
import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
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
  { v: 'adi', l: 'Authorised Deposit-taking Institution (ADI) — CPS 220' },
  { v: 'general_insurer', l: 'General Insurer — GPS 220' },
  { v: 'life_insurer', l: 'Life Insurer — LPS 220' },
  { v: 'phi', l: 'Private Health Insurer — HPS 310' },
  { v: 'rse', l: 'RSE Licensee (Super Fund) — SPS 220' },
];

const CPG229_DOMAINS = [
  {
    id: 'governance', label: 'Governance', icon: 'GOV',
    color: 'border-blue-500/20 bg-blue-500/[0.04]',
    ref: 'CPG 229 §§14–25',
    items: [
      { id: 'gov_board', label: 'Board oversight: climate risk identified as material risk category' },
      { id: 'gov_board_skills', label: 'Board skills/capabilities assessed for climate literacy' },
      { id: 'gov_mgmt', label: 'Senior management climate risk ownership and reporting lines' },
      { id: 'gov_policy', label: 'Climate risk policy / framework approved by Board' },
      { id: 'gov_appetite', label: 'Climate risk appetite statement integrated into RAS' },
    ],
  },
  {
    id: 'risk_mgmt', label: 'Risk Management', icon: 'RISK',
    color: 'border-purple-500/20 bg-purple-500/[0.04]',
    ref: 'CPG 229 §§26–46',
    items: [
      { id: 'rm_identify', label: 'Physical climate risks identified and assessed (acute and chronic)' },
      { id: 'rm_transition', label: 'Transition risks identified (policy, technology, market, reputation)' },
      { id: 'rm_liability', label: 'Liability risks considered (litigation, disclosure obligations)' },
      { id: 'rm_strategic', label: 'Strategic climate risks factored into business planning (2030+ horizons)' },
      { id: 'rm_concentration', label: 'Climate-related concentration risk assessed (geographic, sector)' },
      { id: 'rm_monitor', label: 'Ongoing climate risk monitoring mechanisms established' },
    ],
  },
  {
    id: 'scenario', label: 'Scenario Analysis', icon: 'SCEN',
    color: 'border-cyan-500/20 bg-cyan-500/[0.04]',
    ref: 'CPG 229 §§47–63',
    items: [
      { id: 'sc_framework', label: 'Scenario analysis framework established (at least 2 scenarios: <2°C and 3°C+)' },
      { id: 'sc_physical', label: 'Physical risk scenario analysis completed (acute + chronic risks quantified)' },
      { id: 'sc_transition', label: 'Transition risk scenario analysis completed (carbon price pathways)' },
      { id: 'sc_financial', label: 'Financial impacts quantified under scenarios (P&L, capital, liquidity effects)' },
      { id: 'sc_horizons', label: 'Scenarios cover short (3yr), medium (10yr) and long (30yr+) horizons' },
      { id: 'sc_cva', label: 'APRA 2023 Climate Vulnerability Assessment (CVA) methodology applied' },
    ],
  },
  {
    id: 'disclosure', label: 'Disclosure', icon: 'DISC',
    color: 'border-emerald-500/20 bg-emerald-500/[0.04]',
    ref: 'CPG 229 §§64–70',
    items: [
      { id: 'disc_tcfd', label: 'TCFD-aligned public disclosure in annual report (4 pillars)' },
      { id: 'disc_metrics', label: 'Key climate metrics disclosed (GHG, financed emissions, exposure)' },
      { id: 'disc_targets', label: 'Climate targets disclosed with progress reporting' },
      { id: 'disc_apra', label: 'APRA regulatory reporting — climate risk data submitted as requested' },
    ],
  },
];

const MATURITY = [
  { v: 0, l: '0 — Not Addressed' },
  { v: 1, l: '1 — Initial / Exploratory' },
  { v: 2, l: '2 — Developing' },
  { v: 3, l: '3 — Embedded' },
  { v: 4, l: '4 — Advanced / Leading' },
];

const maturityColor = (m) =>
  m >= 3 ? 'text-emerald-400' : m >= 2 ? 'text-amber-400' : m >= 1 ? 'text-blue-300' : 'text-red-500';

/* ── Component ────────────────────────────────────────────────────────────── */
export default function ApraCpg229Panel() {
  const [entityType, setEntityType] = useState('adi');
  const [disclosures, setDisclosures] = useState(() => {
    const init = {};
    CPG229_DOMAINS.flatMap(d => d.items).forEach(i => { init[i.id] = { maturity: 0, notes: '' }; });
    return init;
  });
  const [cvaCompleted, setCvaCompleted] = useState(false);
  const [stressTestScore, setStressTestScore] = useState('');
  const [result, setResult] = useState(null);

  const set = (id, k, v) => setDisclosures(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));

  const compute = () => {
    const domainScores = CPG229_DOMAINS.map(domain => {
      const avg = domain.items.reduce((s, i) => s + (disclosures[i.id]?.maturity || 0), 0) / domain.items.length;
      return { domain: domain.label, score: parseFloat(avg.toFixed(2)), icon: domain.icon };
    });
    const overall = domainScores.reduce((s, d) => s + d.score, 0) / domainScores.length;
    const gaps = CPG229_DOMAINS.flatMap(domain =>
      domain.items
        .filter(i => (disclosures[i.id]?.maturity || 0) < 3)
        .map(i => ({ domain: domain.label, label: i.label, maturity: disclosures[i.id]?.maturity || 0 }))
    );
    setResult({ overall: parseFloat(overall.toFixed(2)), domainScores, gaps });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="APRA CPG 229 (Nov 2021)" color="bg-amber-500/10 text-amber-700" />
        <Badge label="CPS/GPS/LPS 220 Risk Management" color="bg-blue-400/10 text-blue-300" />
        <Badge label="Climate Vulnerability Assessment 2023" color="bg-purple-400/10 text-purple-300" />
        <Badge label="TCFD-Aligned Disclosure" color="bg-cyan-400/10 text-cyan-300" />
      </div>

      <Card
        title="APRA CPG 229 — Climate Risk Readiness Assessment"
        subtitle="Score your entity against APRA's climate change financial risk guidance across 4 domains: Governance, Risk Management, Scenario Analysis, Disclosure."
      >
        {/* Entity Setup */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-white/60 mb-1">APRA-Regulated Entity Type</label>
            <select
              className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={entityType} onChange={e => setEntityType(e.target.value)}
            >
              {ENTITY_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-3 p-3 bg-amber-500/[0.06] border border-amber-500/10 rounded-lg">
              <input type="checkbox" id="cva" checked={cvaCompleted} onChange={e => setCvaCompleted(e.target.checked)}
                className="accent-amber-400" />
              <label htmlFor="cva" className="text-xs text-amber-400 font-medium cursor-pointer">
                APRA CVA 2023 completed
              </label>
            </div>
            <div>
              <label className="block text-xs text-white/40 mb-1">Stress Test Capital Impact (%)</label>
              <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={stressTestScore} onChange={e => setStressTestScore(e.target.value)} placeholder="e.g. 2.5" />
            </div>
          </div>
        </div>

        {/* Domain Scoring */}
        <div className="space-y-5">
          {CPG229_DOMAINS.map(domain => (
            <div key={domain.id} className={`border rounded-xl p-4 ${domain.color}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-white/80">{domain.label}</h3>
                <Badge label={domain.ref} color="bg-white/[0.06] text-white/40" />
              </div>
              <div className="space-y-2">
                {domain.items.map(item => (
                  <div key={item.id} className="bg-[#0d1424] rounded-lg p-3 border border-white/[0.04]">
                    <p className="text-xs text-white/60 mb-2">{item.label}</p>
                    <div className="flex items-center gap-3">
                      <select
                        className="border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none w-52"
                        value={disclosures[item.id]?.maturity || 0}
                        onChange={e => set(item.id, 'maturity', parseInt(e.target.value))}
                      >
                        {MATURITY.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                      </select>
                      <input
                        className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/40 focus:outline-none"
                        placeholder="Evidence / owner / target date"
                        value={disclosures[item.id]?.notes || ''}
                        onChange={e => set(item.id, 'notes', e.target.value)}
                      />
                      <span className={`text-sm font-bold w-5 text-center ${maturityColor(disclosures[item.id]?.maturity || 0)}`}>
                        {disclosures[item.id]?.maturity || 0}
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
            Generate APRA CPG 229 Assessment
          </button>
        </div>
      </Card>

      {result && (
        <div className="space-y-6">
          {/* KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="col-span-2 md:col-span-1 bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-400/10 rounded-xl p-5 text-center">
              <p className="text-xs text-amber-200/60 mb-1">Overall CPG 229 Score</p>
              <p className="text-3xl font-bold text-white">{result.overall.toFixed(1)}<span className="text-lg text-white/40">/4</span></p>
              <p className="text-xs text-amber-200/60 mt-1">
                {result.overall >= 3 ? 'Advanced' : result.overall >= 2 ? 'Developing' : 'Initial'}
              </p>
            </div>
            {result.domainScores.map((d, i) => (
              <div key={i} className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
                <p className="text-xs text-white/40 mb-1">{d.domain}</p>
                <p className={`text-xl font-bold ${d.score >= 3 ? 'text-emerald-400' : d.score >= 2 ? 'text-amber-400' : 'text-red-500'}`}>
                  {d.score.toFixed(1)}<span className="text-xs text-white/30">/4</span>
                </p>
              </div>
            ))}
          </div>

          {/* Radar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Domain Scores — Radar View">
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={result.domainScores}>
                  <PolarGrid stroke="#ffffff10" />
                  <PolarAngleAxis dataKey="domain" tick={{ fontSize: 10, fill: '#ffffff60' }} />
                  <PolarRadiusAxis domain={[0, 4]} tick={{ fontSize: 8, fill: '#ffffff40' }} />
                  <Radar name="Score" dataKey="score" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Domain Scores vs Target (4.0 = Advanced)">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={result.domainScores}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="domain" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                  <YAxis domain={[0, 4]} ticks={[0,1,2,3,4]} tick={{ fontSize: 9, fill: '#ffffff60' }} />
                  <Tooltip contentStyle={{ background: '#0d1424', border: '1px solid #ffffff10', borderRadius: 8 }} formatter={v => [`${v}/4`]} />
                  <Bar dataKey="score" name="Score" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Gaps */}
          {result.gaps.length > 0 && (
            <Card title={`CPG 229 Gaps — ${result.gaps.length} items below maturity 3`}>
              <div className="space-y-2">
                {result.gaps.map((g, i) => (
                  <div key={i} className="flex items-start gap-3 p-2.5 border border-amber-200 bg-amber-500/10 rounded-lg">
                    <Badge label={g.domain} color="bg-amber-500/20 text-amber-700" />
                    <span className="text-xs text-amber-700 flex-1">{g.label}</span>
                    <span className={`text-xs font-bold ${maturityColor(g.maturity)}`}>{g.maturity}/4</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* CVA Status */}
          <div className={`p-4 rounded-xl border ${cvaCompleted ? 'border-emerald-500/20 bg-emerald-500/[0.04]' : 'border-amber-200 bg-amber-500/10'}`}>
            <p className="text-xs font-semibold text-white/70 mb-1">APRA 2023 Climate Vulnerability Assessment (CVA)</p>
            <p className="text-xs text-white/40">
              {cvaCompleted
                ? 'CVA completed. Capital adequacy under climate stress scenarios evaluated.'
                : 'CVA not yet completed. APRA expects all regulated entities to conduct CVA using APRA-specified methodology (3 scenarios: orderly transition, disorderly transition, hot house world).'}
            </p>
            {stressTestScore && (
              <p className="text-xs text-amber-400 mt-1 font-medium">
                Stress Test Capital Impact: {stressTestScore}% of RWA / capital base
              </p>
            )}
          </div>
        </div>
      )}

      {/* Methodology */}
      <Card title="Methodology Reference" className="border-white/[0.03]">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-white/50">
          <div><span className="font-semibold text-white/70">Guidance:</span> APRA CPG 229 (November 2021)</div>
          <div><span className="font-semibold text-white/70">Applicable:</span> ADIs, Insurers, RSE Licensees</div>
          <div><span className="font-semibold text-white/70">CVA:</span> APRA Climate Vulnerability Assessment 2023</div>
          <div><span className="font-semibold text-white/70">Scenarios:</span> NGFS + APRA-specified (3 scenarios)</div>
          <div><span className="font-semibold text-white/70">Disclosure:</span> TCFD-aligned, recommended from FY2023</div>
          <div><span className="font-semibold text-white/70">Risk Types:</span> Physical, Transition, Liability, Strategic</div>
        </div>
      </Card>
    </div>
  );
}
