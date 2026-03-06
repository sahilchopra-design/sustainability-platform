/**
 * SEC Climate Disclosure Panel
 * SEC Final Rule 33-7211 — Enhancement and Standardization of Climate-Related
 * Disclosures for Investors (March 2024, effective May 2024).
 * Regulation S-K Item 1500-1507 / Regulation S-X Article 14.
 */
import React, { useState } from 'react';
import {
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
const FILER_TYPES = [
  { v: 'laf', l: 'Large Accelerated Filer (LAF)', scope_deadline: 'FY2025', fin_deadline: 'FY2025', scope3: false },
  { v: 'af', l: 'Accelerated Filer (AF)', scope_deadline: 'FY2026', fin_deadline: 'FY2026', scope3: false },
  { v: 'naf', l: 'Non-Accelerated Filer (NAF)', scope_deadline: 'FY2027 (if required)', fin_deadline: 'FY2027 (if required)', scope3: false },
  { v: 'src', l: 'Smaller Reporting Company (SRC)', scope_deadline: 'Phase-in TBD', fin_deadline: 'Phase-in TBD', scope3: false },
];

const SEC_SECTIONS = [
  {
    id: 'governance', label: 'Governance', ref: 'S-K Item 1501',
    color: 'border-blue-500/20 bg-blue-500/[0.04]',
    items: [
      { id: 'gov_board', label: 'Board oversight of climate-related risks & opportunities (committee, frequency, expertise)' },
      { id: 'gov_mgmt', label: "Management's role in assessing and managing climate-related risks (role, process, reporting)" },
    ],
  },
  {
    id: 'strategy', label: 'Strategy', ref: 'S-K Item 1502',
    color: 'border-cyan-500/20 bg-cyan-500/[0.04]',
    items: [
      { id: 'str_risks', label: 'Material physical and transition climate risks identified over short/medium/long term' },
      { id: 'str_effects', label: 'Actual and potential effects on business strategy, financial planning, capital allocation' },
      { id: 'str_resilience', label: 'Resilience of strategy — scenario analysis (if used; otherwise describe how evaluated)' },
      { id: 'str_targets', label: 'Climate-related targets and goals set (if applicable) with progress description' },
    ],
  },
  {
    id: 'risk_mgmt', label: 'Risk Management', ref: 'S-K Item 1503',
    color: 'border-purple-500/20 bg-purple-500/[0.04]',
    items: [
      { id: 'rm_identify', label: 'Processes for identifying and assessing material climate-related risks' },
      { id: 'rm_integration', label: 'Integration of climate risk processes into overall enterprise risk management' },
    ],
  },
  {
    id: 'metrics', label: 'Metrics & Targets', ref: 'S-K Item 1504',
    color: 'border-emerald-500/20 bg-emerald-500/[0.04]',
    items: [
      { id: 'met_scope12', label: 'Scope 1 & 2 GHG emissions (tCO₂e) — mandatory for LAF/AF once material' },
      { id: 'met_intensity', label: 'GHG intensity metric (if used internally to set targets or measure performance)' },
      { id: 'met_carbon_price', label: 'Internal carbon price (USD/tCO₂e) used in planning decisions (if applicable)' },
    ],
  },
  {
    id: 'financials', label: 'Financial Statements', ref: 'S-X Art. 14',
    color: 'border-amber-500/20 bg-amber-500/[0.04]',
    items: [
      { id: 'fin_impacts', label: 'Material financial effects of severe weather / physical risks on P&L, balance sheet (≥1% threshold)' },
      { id: 'fin_transition', label: 'Costs/expenditures for climate transition activities disclosed in financial statements' },
      { id: 'fin_estimates', label: 'Significant estimates and assumptions in financial statements due to climate-related risks' },
    ],
  },
];

const MATURITY = [
  { v: 0, l: '0 — Not Addressed' },
  { v: 1, l: '1 — Initial Planning' },
  { v: 2, l: '2 — In Progress' },
  { v: 3, l: '3 — Substantially Complete' },
  { v: 4, l: '4 — Fully Compliant' },
];

const maturityColor = (m) =>
  m >= 3 ? 'text-emerald-400' : m >= 2 ? 'text-amber-400' : m >= 1 ? 'text-blue-300' : 'text-red-500';

/* ── Component ────────────────────────────────────────────────────────────── */
export default function SecClimatePanel() {
  const [filerType, setFilerType] = useState('laf');
  const [disclosures, setDisclosures] = useState(() => {
    const init = {};
    SEC_SECTIONS.flatMap(s => s.items).forEach(i => { init[i.id] = { maturity: 0, notes: '' }; });
    return init;
  });
  const [scope1, setScope1] = useState('');
  const [scope2Market, setScope2Market] = useState('');
  const [scope2Location, setScope2Location] = useState('');
  const [result, setResult] = useState(null);

  const set = (id, k, v) => setDisclosures(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));

  const compute = () => {
    const allItems = SEC_SECTIONS.flatMap(s => s.items);
    const totalScore = allItems.reduce((s, i) => s + (disclosures[i.id]?.maturity || 0), 0);
    const maxScore = allItems.length * 4;
    const pct = (totalScore / maxScore) * 100;

    const sectionScores = SEC_SECTIONS.map(sec => {
      const score = sec.items.reduce((s, i) => s + (disclosures[i.id]?.maturity || 0), 0) / sec.items.length;
      return { section: sec.label, score: parseFloat(score.toFixed(2)), maxScore: 4 };
    });

    const gaps = SEC_SECTIONS.flatMap(sec =>
      sec.items
        .filter(i => (disclosures[i.id]?.maturity || 0) < 3)
        .map(i => ({ section: sec.label, label: i.label, maturity: disclosures[i.id]?.maturity || 0 }))
    );

    const readinessLabel = pct >= 75 ? 'Substantially Ready' : pct >= 50 ? 'Developing' : 'Initial Stage';
    setResult({ pct: parseFloat(pct.toFixed(1)), sectionScores, gaps, readinessLabel });
  };

  const filer = FILER_TYPES.find(f => f.v === filerType);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="SEC Release 33-7211 (March 2024)" color="bg-blue-400/10 text-blue-300" />
        <Badge label="Reg S-K Items 1500–1507" color="bg-purple-400/10 text-purple-300" />
        <Badge label="Reg S-X Article 14" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="GHG Protocol" color="bg-white/[0.06] text-white/60" />
        <Badge label="Partially Stayed (6th Cir. 2024)" color="bg-amber-500/10 text-amber-700" />
      </div>

      <Card
        title="SEC Climate Disclosure — Readiness Assessment"
        subtitle="Rate compliance readiness across all 5 required disclosure areas. SEC Final Rule 33-7211 (March 2024). Note: Scope 3 GHG disclosures were removed from the final rule."
      >
        {/* Filer Setup */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Registrant Category</label>
            <select
              className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={filerType} onChange={e => setFilerType(e.target.value)}
            >
              {FILER_TYPES.map(f => <option key={f.v} value={f.v}>{f.l}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2 p-3 bg-blue-400/[0.06] rounded-lg border border-blue-400/10">
            <div>
              <p className="text-[10px] text-white/40">Scope 1 & 2 GHG Deadline</p>
              <p className="text-sm font-bold text-blue-300">{filer?.scope_deadline}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 p-3 bg-purple-400/[0.06] rounded-lg border border-purple-400/10">
            <div>
              <p className="text-[10px] text-white/40">Financial Statement Deadline</p>
              <p className="text-sm font-bold text-purple-300">{filer?.fin_deadline}</p>
            </div>
          </div>
        </div>

        {/* GHG Data Entry */}
        <div className="border border-white/[0.06] rounded-xl p-4 mb-6 bg-[#0b1120]">
          <h3 className="text-xs font-bold text-white/60 uppercase tracking-wide mb-3">
            GHG Emissions (Scope 1 & 2 only — Scope 3 not required)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-white/40 mb-1">Scope 1 — Direct Emissions (tCO₂e)</label>
              <input
                type="number"
                className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0d1424] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                value={scope1} onChange={e => setScope1(e.target.value)} placeholder="e.g. 12000"
              />
            </div>
            <div>
              <label className="block text-xs text-white/40 mb-1">Scope 2 Market-Based (tCO₂e)</label>
              <input
                type="number"
                className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0d1424] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                value={scope2Market} onChange={e => setScope2Market(e.target.value)} placeholder="e.g. 8500"
              />
            </div>
            <div>
              <label className="block text-xs text-white/40 mb-1">Scope 2 Location-Based (tCO₂e)</label>
              <input
                type="number"
                className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0d1424] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                value={scope2Location} onChange={e => setScope2Location(e.target.value)} placeholder="e.g. 11000"
              />
            </div>
          </div>
          {(scope1 || scope2Market) && (
            <div className="mt-3 flex gap-4">
              <div className="text-center p-2 bg-blue-400/[0.06] rounded-lg">
                <p className="text-xs font-bold text-blue-300">
                  {(parseFloat(scope1 || 0) + parseFloat(scope2Market || 0)).toLocaleString()} tCO₂e
                </p>
                <p className="text-[10px] text-white/40">Total Scope 1+2 (market)</p>
              </div>
            </div>
          )}
        </div>

        {/* Readiness Scoring */}
        <div className="space-y-4">
          {SEC_SECTIONS.map(sec => (
            <div key={sec.id} className={`border rounded-xl p-4 ${sec.color}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-white/80">{sec.label}</h3>
                <Badge label={sec.ref} color="bg-white/[0.06] text-white/40" />
              </div>
              <div className="space-y-2">
                {sec.items.map(item => (
                  <div key={item.id} className="bg-[#0d1424] rounded-lg p-3 border border-white/[0.04]">
                    <p className="text-xs text-white/60 mb-2">{item.label}</p>
                    <div className="flex items-center gap-3">
                      <select
                        className="border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none w-56"
                        value={disclosures[item.id]?.maturity || 0}
                        onChange={e => set(item.id, 'maturity', parseInt(e.target.value))}
                      >
                        {MATURITY.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                      </select>
                      <input
                        className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/40 focus:outline-none"
                        placeholder="Notes / evidence / owner"
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
            Generate SEC Assessment
          </button>
        </div>
      </Card>

      {result && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="col-span-2 md:col-span-1 bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-400/10 rounded-xl p-5 text-center">
              <p className="text-xs text-blue-200/60 mb-1">Overall Readiness</p>
              <p className="text-3xl font-bold text-white">{result.pct.toFixed(0)}<span className="text-lg text-white/40">%</span></p>
              <p className="text-xs text-blue-200/60 mt-1">{result.readinessLabel}</p>
            </div>
            {result.sectionScores.map((s, i) => (
              <div key={i} className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
                <p className="text-xs text-white/40 mb-1 truncate">{s.section}</p>
                <p className={`text-xl font-bold ${s.score >= 3 ? 'text-emerald-400' : s.score >= 2 ? 'text-amber-400' : 'text-red-500'}`}>
                  {s.score.toFixed(1)}<span className="text-sm font-normal text-white/30">/4</span>
                </p>
              </div>
            ))}
          </div>

          {/* Gap chart */}
          <Card title="Section Readiness vs Target (4.0 = Fully Compliant)">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={result.sectionScores} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
                <XAxis type="number" domain={[0, 4]} ticks={[0,1,2,3,4]} tick={{ fontSize: 9, fill: '#ffffff60' }} />
                <YAxis type="category" dataKey="section" width={120} tick={{ fontSize: 9, fill: '#ffffff60' }} />
                <Tooltip contentStyle={{ background: '#0d1424', border: '1px solid #ffffff10', borderRadius: 8 }} formatter={v => [`${v}/4`]} />
                <Bar dataKey="score" name="Readiness" radius={[0, 4, 4, 0]}>
                  {result.sectionScores.map((s, i) => (
                    <Cell key={i} fill={s.score >= 3 ? '#10b981' : s.score >= 2 ? '#f59e0b' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Gaps */}
          {result.gaps.length > 0 && (
            <Card title={`Compliance Gaps — ${result.gaps.length} item${result.gaps.length > 1 ? 's' : ''} below maturity level 3`}>
              <div className="space-y-2">
                {result.gaps.map((g, i) => (
                  <div key={i} className="flex items-start gap-3 p-2.5 border border-amber-200 bg-amber-500/10 rounded-lg">
                    <Badge label={g.section} color="bg-amber-500/20 text-amber-400" />
                    <span className="text-xs text-amber-700 flex-1">{g.label}</span>
                    <span className={`text-xs font-bold ${maturityColor(g.maturity)}`}>{g.maturity}/4</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Methodology */}
      <Card title="Methodology Reference" className="border-white/[0.03]">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-white/50">
          <div><span className="font-semibold text-white/70">Rule:</span> SEC Release 33-7211 (Mar 2024)</div>
          <div><span className="font-semibold text-white/70">Reg S-K:</span> Items 1500–1507 (climate disclosures)</div>
          <div><span className="font-semibold text-white/70">Reg S-X:</span> Art. 14 (financial statement impacts ≥1%)</div>
          <div><span className="font-semibold text-white/70">GHG Standard:</span> GHG Protocol Corporate Standard</div>
          <div><span className="font-semibold text-white/70">Scope 3:</span> Removed from final rule (proposed only)</div>
          <div><span className="font-semibold text-white/70">Status:</span> Voluntarily stayed pending judicial review (2024)</div>
        </div>
      </Card>
    </div>
  );
}
