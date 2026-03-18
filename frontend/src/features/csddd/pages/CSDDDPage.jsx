/**
 * CSDDDPage.jsx
 * Route: /csddd
 * Badge: CSDDD·Art6
 *
 * Tab 1 — Scope Assessment      POST /api/v1/csddd/scope-assessment
 * Tab 2 — Adverse Impacts       POST /api/v1/csddd/adverse-impacts
 * Tab 3 — DD Compliance         POST /api/v1/csddd/dd-compliance
 * Tab 4 — Value Chain           POST /api/v1/csddd/value-chain-mapping
 * Tab 5 — Penalties             GET  /api/v1/csddd/ref/penalties
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

const BASE = '/api/v1';
const TOOLTIP_STYLE = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111', fontSize: 11 };

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
    amber:  'bg-amber-50 text-amber-700 border-amber-200',
    red:    'bg-red-50 text-red-700 border-red-200',
    blue:   'bg-blue-50 text-blue-700 border-blue-200',
    gray:   'bg-gray-50 text-gray-600 border-gray-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>;
}

function Inp({ label, value, onChange, type = 'text' }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-emerald-400"
      />
    </div>
  );
}

function Sel({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-emerald-400 bg-white"
      >
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function Btn({ onClick, children, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-4 py-1.5 bg-black text-white text-xs font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors"
    >
      {children}
    </button>
  );
}

/* ── Seed adverse impact data ───────────────────────────────────────────── */
const ADVERSE_IMPACTS_SEED = (() => {
  const rng = mkRng(701);
  return [
    // Human Rights
    { id: 'HR-01', label: 'Child Labour', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-02', label: 'Forced Labour', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-03', label: 'Safe Working Conditions', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-04', label: 'Freedom of Association', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-05', label: 'Adequate Wages', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-06', label: 'Land Rights', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-07', label: 'Non-discrimination', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-08', label: 'Privacy Rights', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-09', label: 'Indigenous Peoples Rights', category: 'HR', severity: Math.round(rng() * 100) },
    { id: 'HR-10', label: 'Access to Remedy', category: 'HR', severity: Math.round(rng() * 100) },
    // Environmental
    { id: 'ENV-01', label: 'GHG Emissions', category: 'ENV', severity: Math.round(rng() * 100) },
    { id: 'ENV-02', label: 'Deforestation', category: 'ENV', severity: Math.round(rng() * 100) },
    { id: 'ENV-03', label: 'Water Depletion', category: 'ENV', severity: Math.round(rng() * 100) },
    { id: 'ENV-04', label: 'Biodiversity Loss', category: 'ENV', severity: Math.round(rng() * 100) },
    { id: 'ENV-05', label: 'Pollution', category: 'ENV', severity: Math.round(rng() * 100) },
    { id: 'ENV-06', label: 'Chemical Use', category: 'ENV', severity: Math.round(rng() * 100) },
    { id: 'ENV-07', label: 'Waste Management', category: 'ENV', severity: Math.round(rng() * 100) },
    { id: 'ENV-08', label: 'Climate Physical Risks', category: 'ENV', severity: Math.round(rng() * 100) },
  ];
})();

/* ── DD Obligations ─────────────────────────────────────────────────────── */
const DD_OBLIGATIONS = [
  { id: 'policy',          label: 'Policy Commitment',         weight: 10 },
  { id: 'identification',  label: 'Impact Identification',     weight: 20 },
  { id: 'prevention',      label: 'Prevention & Cessation',    weight: 20 },
  { id: 'remediation',     label: 'Remediation Provision',     weight: 20 },
  { id: 'rem_provided',    label: 'Remediation Provided',      weight: 10 },
  { id: 'stakeholder',     label: 'Stakeholder Engagement',    weight: 5 },
  { id: 'grievance',       label: 'Grievance Mechanism',       weight: 5 },
  { id: 'monitoring',      label: 'Monitoring & Review',       weight: 5 },
  { id: 'reporting',       label: 'Public Reporting',          weight: 5 },
];

const rngSeed = mkRng(802);
const DD_SCORES_SEED = DD_OBLIGATIONS.map(o => ({
  ...o,
  score: Math.round(40 + rngSeed() * 55),
}));

/* ── Penalties reference data ───────────────────────────────────────────── */
const PENALTIES_REF = [
  { article: 'Art. 20(1)', type: 'Administrative Penalty', maxRate: '5% worldwide turnover', basis: 'Per infringement', timeline: '5-year limitation' },
  { article: 'Art. 22', type: 'Civil Liability', maxRate: 'Full damage compensation', basis: 'Harm to natural/legal persons', timeline: 'National procedural rules' },
  { article: 'Art. 20(2)', type: 'Temporary Exclusion', maxRate: 'Max 12 months public procurement', basis: 'Serious repeated violations', timeline: 'Per competent authority' },
  { article: 'Art. 20(3)', type: 'Confiscation of Revenue', maxRate: 'Revenue from products', basis: 'Infringing products or services', timeline: 'From date of infringement' },
  { article: 'Art. 33', type: 'Periodic Penalty Payment', maxRate: '5% avg daily worldwide turnover', basis: 'Per day of non-compliance', timeline: 'Until compliance restored' },
];

/* ── Tab 1: Scope Assessment ────────────────────────────────────────────── */
const SCOPE_GROUPS = {
  group_1: { label: 'EU Group 1', desc: '>1,000 employees & >€300M net turnover', phase: 2027 },
  group_2: { label: 'EU Group 2', desc: '>250 employees & >€40M net turnover', phase: 2028 },
  group_3: { label: 'EU Group 3', desc: '>10 employees & >€2M net turnover', phase: 2029 },
  non_eu_group_1: { label: 'Non-EU Group 1', desc: '>€300M EU net turnover', phase: 2027 },
  non_eu_group_2: { label: 'Non-EU Group 2', desc: '>€40M EU net turnover (Annex sector)', phase: 2028 },
  non_eu_group_3: { label: 'Non-EU Group 3', desc: '>€2M EU net turnover (Annex sector)', phase: 2029 },
};

function ScopeAssessment() {
  const [form, setForm] = useState({ entity_name: 'Acme Corp', employees: '1200', turnover_eur: '350000000', is_eu: 'true', sector: 'manufacturing' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/csddd/scope-assessment`, form);
      setResult(r.data);
    } catch {
      const emp = Number(form.employees);
      const tur = Number(form.turnover_eur);
      const isEU = form.is_eu === 'true';
      let group = null;
      if (isEU) {
        if (emp > 1000 && tur > 300e6) group = 'group_1';
        else if (emp > 250 && tur > 40e6) group = 'group_2';
        else if (emp > 10 && tur > 2e6) group = 'group_3';
      } else {
        if (tur > 300e6) group = 'non_eu_group_1';
        else if (tur > 40e6) group = 'non_eu_group_2';
        else if (tur > 2e6) group = 'non_eu_group_3';
      }
      setResult({
        scope_group: group,
        phase_in_year: group ? SCOPE_GROUPS[group]?.phase : null,
        in_scope: !!group,
        threshold_met: !!group,
        description: group ? SCOPE_GROUPS[group]?.desc : 'Below threshold — not in scope',
      });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Scope Group" value={result?.scope_group?.replace('_', ' ')?.toUpperCase() || '—'} sub="CSDDD phase group" color="text-blue-600" />
        <KpiCard label="Phase-In Year" value={result?.phase_in_year || '—'} sub="Compliance deadline" />
        <KpiCard label="In Scope" value={result?.in_scope == null ? '—' : result.in_scope ? 'Yes' : 'No'} sub="CSDDD applicability" color={result?.in_scope ? 'text-amber-600' : 'text-emerald-600'} />
        <KpiCard label="Thresholds Met" value={result?.threshold_met == null ? '—' : result.threshold_met ? 'Yes' : 'No'} sub="Employee & turnover" />
      </div>

      <Section title="Art. 2 Scope Assessment — Entity Thresholds">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
          <Inp label="Entity Name" value={form.entity_name} onChange={v => setForm(f => ({ ...f, entity_name: v }))} />
          <Inp label="Employees" value={form.employees} onChange={v => setForm(f => ({ ...f, employees: v }))} type="number" />
          <Inp label="Net Turnover (EUR)" value={form.turnover_eur} onChange={v => setForm(f => ({ ...f, turnover_eur: v }))} type="number" />
          <Sel label="EU Entity?" value={form.is_eu} onChange={v => setForm(f => ({ ...f, is_eu: v }))} options={[
            { value: 'true', label: 'EU — registered in EU member state' },
            { value: 'false', label: 'Non-EU — generating EU turnover' },
          ]} />
          <Sel label="High-Risk Sector" value={form.sector} onChange={v => setForm(f => ({ ...f, sector: v }))} options={[
            { value: 'manufacturing', label: 'Manufacturing' }, { value: 'mining', label: 'Mining & Extractives' },
            { value: 'agriculture', label: 'Agriculture & Food' }, { value: 'textiles', label: 'Textiles & Apparel' },
            { value: 'chemicals', label: 'Chemicals' }, { value: 'construction', label: 'Construction' },
            { value: 'transport', label: 'Transport & Logistics' }, { value: 'other', label: 'Other' },
          ]} />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Assessing…' : 'Run Scope Assessment'}</Btn>
      </Section>

      {result && (
        <Section title="Scope Assessment Result">
          <div className={`p-4 rounded-lg border ${result.in_scope ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}`}>
            <div className="flex items-center gap-3 mb-2">
              <Badge label={result.in_scope ? 'In Scope' : 'Out of Scope'} color={result.in_scope ? 'amber' : 'green'} />
              {result.scope_group && <Badge label={SCOPE_GROUPS[result.scope_group]?.label || result.scope_group} color="blue" />}
              {result.phase_in_year && <Badge label={`Phase-In: ${result.phase_in_year}`} color="gray" />}
            </div>
            <p className="text-xs text-gray-700">{result.description}</p>
          </div>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(SCOPE_GROUPS).map(([key, info]) => (
              <div key={key} className={`p-3 rounded-lg border text-xs ${result.scope_group === key ? 'bg-blue-50 border-blue-300' : 'bg-gray-50 border-gray-200'}`}>
                <p className="font-semibold text-gray-700">{info.label}</p>
                <p className="text-gray-500 mt-0.5">{info.desc}</p>
                <p className="text-gray-400 mt-1 font-mono">Phase-in: {info.phase}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

/* ── Tab 2: Adverse Impacts ─────────────────────────────────────────────── */
function AdverseImpacts() {
  const [impacts, setImpacts] = useState(ADVERSE_IMPACTS_SEED);
  const [form, setForm] = useState({ entity_id: 'ENTITY-001', sector: 'manufacturing', country: 'Germany' });
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/csddd/adverse-impacts`, form);
      if (r.data?.impacts?.length) setImpacts(r.data.impacts);
    } catch {}
    setLoading(false);
  };

  const radarData = impacts.map(i => ({ subject: i.id, value: i.severity }));
  const highPriority = impacts.filter(i => i.severity >= 70);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Adverse Impacts" value={impacts.length} sub="HR + ENV categories" color="text-amber-600" />
        <KpiCard label="High Severity" value={highPriority.length} sub="Score ≥70/100" color="text-red-600" />
        <KpiCard label="HR Impacts" value={impacts.filter(i => i.category === 'HR').length} sub="Human rights" />
        <KpiCard label="ENV Impacts" value={impacts.filter(i => i.category === 'ENV').length} sub="Environmental" />
      </div>

      <Section title="Impact Identification Parameters — Art. 6">
        <div className="grid grid-cols-3 gap-3 mb-3">
          <Inp label="Entity ID" value={form.entity_id} onChange={v => setForm(f => ({ ...f, entity_id: v }))} />
          <Sel label="Sector" value={form.sector} onChange={v => setForm(f => ({ ...f, sector: v }))} options={[
            { value: 'manufacturing', label: 'Manufacturing' }, { value: 'agriculture', label: 'Agriculture' },
            { value: 'textiles', label: 'Textiles' }, { value: 'mining', label: 'Mining' },
          ]} />
          <Inp label="HQ Country" value={form.country} onChange={v => setForm(f => ({ ...f, country: v }))} />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Identifying…' : 'Run Impact Assessment'}</Btn>
      </Section>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Section title="18-Impact Severity Radar (HR-01 to HR-10, ENV-01 to ENV-08)">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
              <PolarGrid stroke="rgba(0,0,0,0.08)" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 8 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 8 }} />
              <Radar dataKey="value" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.25} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Severity Heatmap">
          <div className="space-y-1.5">
            {impacts.map(imp => (
              <div key={imp.id} className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-gray-500 w-12">{imp.id}</span>
                <span className="text-xs text-gray-600 w-40 truncate">{imp.label}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full transition-all ${imp.severity >= 70 ? 'bg-red-500' : imp.severity >= 40 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                    style={{ width: `${imp.severity}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-gray-500 w-8 text-right">{imp.severity}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 3: DD Compliance ───────────────────────────────────────────────── */
function DDCompliance() {
  const [scores, setScores] = useState(DD_SCORES_SEED);
  const [form, setForm] = useState({ entity_id: 'ENTITY-001', assessment_year: '2025' });
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/csddd/dd-compliance`, form);
      if (r.data?.obligations?.length) setScores(r.data.obligations);
    } catch {}
    setLoading(false);
  };

  const overallScore = Math.round(scores.reduce((acc, s) => acc + (s.score * s.weight / 100), 0));
  const status = overallScore >= 75 ? 'Compliant' : overallScore >= 50 ? 'Partial' : 'Non-Compliant';
  const statusColor = overallScore >= 75 ? 'text-emerald-600' : overallScore >= 50 ? 'text-amber-600' : 'text-red-600';

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="DD Score" value={`${overallScore}%`} sub="Weighted obligations" color={statusColor} />
        <KpiCard label="Status" value={status} sub="Arts. 5-13 compliance" color={statusColor} />
        <KpiCard label="Obligations Met" value={scores.filter(s => s.score >= 75).length} sub={`of ${scores.length} total`} color="text-emerald-600" />
        <KpiCard label="Value Chain Gaps" value={scores.filter(s => s.score < 50).length} sub="Critical deficiencies" color="text-red-600" />
      </div>

      <Section title="Assessment Parameters">
        <div className="grid grid-cols-2 gap-3 mb-3">
          <Inp label="Entity ID" value={form.entity_id} onChange={v => setForm(f => ({ ...f, entity_id: v }))} />
          <Inp label="Assessment Year" value={form.assessment_year} onChange={v => setForm(f => ({ ...f, assessment_year: v }))} />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Assessing…' : 'Run DD Compliance Assessment'}</Btn>
      </Section>

      <Section title="9 Weighted Obligations — Arts. 5-13 Progress">
        <div className="space-y-3">
          {scores.map(s => (
            <div key={s.id} className="flex items-center gap-3">
              <span className="text-xs text-gray-700 font-medium w-44 truncate">{s.label}</span>
              <span className="text-[10px] text-gray-400 w-10">{s.weight}%</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all ${s.score >= 75 ? 'bg-emerald-500' : s.score >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                  style={{ width: `${s.score}%` }}
                />
              </div>
              <span className={`text-xs font-mono w-12 text-right ${s.score >= 75 ? 'text-emerald-600' : s.score >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                {s.score}%
              </span>
            </div>
          ))}
        </div>
        <div className={`mt-4 p-3 rounded-lg border ${overallScore >= 75 ? 'bg-emerald-50 border-emerald-200' : overallScore >= 50 ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-600">Overall Weighted Score:</span>
            <span className={`text-2xl font-bold font-mono ${statusColor}`}>{overallScore}%</span>
            <Badge label={status} color={overallScore >= 75 ? 'green' : overallScore >= 50 ? 'amber' : 'red'} />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {overallScore >= 75 ? 'Entity demonstrates adequate DD processes across all obligations.' : overallScore >= 50 ? 'Partial compliance — key obligations require strengthening.' : 'Significant DD gaps identified — immediate remediation required.'}
          </p>
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 4: Value Chain ─────────────────────────────────────────────────── */
const TIER_CONFIG = [
  { tier: 'T1', label: 'Tier 1 Direct Suppliers', weight: 40, color: '#10b981' },
  { tier: 'T2', label: 'Tier 2 Suppliers', weight: 30, color: '#3b82f6' },
  { tier: 'T3+', label: 'Tier 3+ / Upstream', weight: 15, color: '#f59e0b' },
  { tier: 'cascading', label: 'Cascading Requirements', weight: 15, color: '#8b5cf6' },
];

const rngVC = mkRng(901);
const VC_SEED = TIER_CONFIG.map(t => ({
  ...t,
  completeness: Math.round(40 + rngVC() * 55),
  suppliers: Math.ceil(rngVC() * 80 + 10),
  mapped: Math.ceil(rngVC() * 50 + 5),
}));

function ValueChain() {
  const [tiers, setTiers] = useState(VC_SEED);
  const [form, setForm] = useState({ entity_id: 'ENTITY-001', sector: 'manufacturing', include_indirect: 'true' });
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/csddd/value-chain-mapping`, form);
      if (r.data?.tiers?.length) setTiers(r.data.tiers);
    } catch {}
    setLoading(false);
  };

  const overallCompleteness = Math.round(tiers.reduce((acc, t) => acc + t.completeness * t.weight / 100, 0));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Value Chain Completeness" value={`${overallCompleteness}%`} sub="Weighted completeness" color={overallCompleteness >= 70 ? 'text-emerald-600' : 'text-amber-600'} />
        {tiers.slice(0, 3).map(t => (
          <KpiCard key={t.tier} label={t.tier} value={`${t.completeness}%`} sub={`${t.mapped}/${t.suppliers} mapped`} />
        ))}
      </div>

      <Section title="Value Chain Mapping Parameters — Art. 14">
        <div className="grid grid-cols-3 gap-3 mb-3">
          <Inp label="Entity ID" value={form.entity_id} onChange={v => setForm(f => ({ ...f, entity_id: v }))} />
          <Sel label="Sector" value={form.sector} onChange={v => setForm(f => ({ ...f, sector: v }))} options={[
            { value: 'manufacturing', label: 'Manufacturing' }, { value: 'agriculture', label: 'Agriculture' },
            { value: 'textiles', label: 'Textiles' }, { value: 'mining', label: 'Mining' },
          ]} />
          <Sel label="Include Indirect?" value={form.include_indirect} onChange={v => setForm(f => ({ ...f, include_indirect: v }))} options={[
            { value: 'true', label: 'Yes — full value chain' }, { value: 'false', label: 'No — direct only' },
          ]} />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Mapping…' : 'Run Value Chain Mapping'}</Btn>
      </Section>

      <Section title="Tier Completeness Diagram">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={tiers} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="tier" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, 'Completeness']} />
            <Bar dataKey="completeness" radius={[4, 4, 0, 0]} name="Completeness %">
              {tiers.map((d, i) => <Cell key={i} fill={d.color} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-4 space-y-3">
          {tiers.map(t => (
            <div key={t.tier} className="flex items-center gap-3">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: t.color }} />
              <span className="text-xs text-gray-600 w-48">{t.label}</span>
              <span className="text-[10px] text-gray-400 w-10">{t.weight}% wt</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div className="h-2 rounded-full" style={{ width: `${t.completeness}%`, backgroundColor: t.color }} />
              </div>
              <span className="text-xs font-mono text-gray-600 w-10 text-right">{t.completeness}%</span>
              <span className="text-[10px] text-gray-400">{t.mapped}/{t.suppliers}</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 5: Penalties ───────────────────────────────────────────────────── */
function Penalties() {
  const [data, setData] = useState(PENALTIES_REF);

  useEffect(() => {
    axios.get(`${BASE}/csddd/ref/penalties`)
      .then(r => { if (r.data?.penalties?.length) setData(r.data.penalties); })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <KpiCard label="Max Penalty Rate" value="5%" sub="% of worldwide net turnover" color="text-red-600" />
        <KpiCard label="Civil Liability" value="Art. 22" sub="Full damage compensation" color="text-amber-600" />
        <KpiCard label="Limitation Period" value="5 Years" sub="From date of infringement" />
      </div>

      <Section title="Art. 20 & Art. 22 — CSDDD Penalty & Civil Liability Framework">
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-xs text-red-800">
          <strong>Art. 20(1):</strong> Member States shall provide for penalties including fines of up to 5% of the company's net worldwide turnover in the financial year preceding the decision.
          <strong className="ml-2">Art. 22:</strong> Companies shall be civilly liable for damages caused by adverse impacts they could have prevented or mitigated.
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                {['Article', 'Penalty Type', 'Maximum Rate', 'Basis', 'Timeline'].map(h => (
                  <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-2 font-mono font-semibold text-gray-700">{row.article}</td>
                  <td className="py-2 px-2 font-medium text-gray-800">{row.type}</td>
                  <td className="py-2 px-2 text-red-700 font-medium">{row.maxRate}</td>
                  <td className="py-2 px-2 text-gray-600">{row.basis}</td>
                  <td className="py-2 px-2 text-gray-500">{row.timeline}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Cross-Framework Links">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { framework: 'CSRD — ESRS S1/S2/S3', link: 'Own workforce, workers in value chain, affected communities', color: 'bg-blue-50 border-blue-200' },
            { framework: 'UNGP — Pillar II', link: 'Corporate responsibility to respect human rights through DD', color: 'bg-purple-50 border-purple-200' },
            { framework: 'OECD MNE Guidelines — Chapter IV', link: 'Human rights due diligence for multinational enterprises', color: 'bg-amber-50 border-amber-200' },
          ].map(item => (
            <div key={item.framework} className={`p-3 rounded-lg border text-xs ${item.color}`}>
              <p className="font-semibold text-gray-800 mb-1">{item.framework}</p>
              <p className="text-gray-600">{item.link}</p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'scope', label: 'Scope Assessment' },
  { id: 'impacts', label: 'Adverse Impacts' },
  { id: 'dd', label: 'DD Compliance' },
  { id: 'valuechain', label: 'Value Chain' },
  { id: 'penalties', label: 'Penalties' },
];

export default function CSDDDPage() {
  const [tab, setTab] = useState('scope');

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <DemoBanner />
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold text-gray-900">CSDDD Due Diligence</h1>
          <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">CSDDD·Art6</span>
        </div>
        <p className="text-xs text-gray-500">EU Corporate Sustainability Due Diligence Directive (EU) 2024/1760 — scope assessment, adverse impact identification, DD compliance and value chain mapping.</p>
      </div>

      <div className="flex gap-1 mb-5 border-b border-gray-200 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-xs font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${tab === t.id ? 'border-emerald-500 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-800'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'scope'      && <ScopeAssessment />}
      {tab === 'impacts'    && <AdverseImpacts />}
      {tab === 'dd'         && <DDCompliance />}
      {tab === 'valuechain' && <ValueChain />}
      {tab === 'penalties'  && <Penalties />}
    </div>
  );
}
