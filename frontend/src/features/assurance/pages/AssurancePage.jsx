/**
 * AssurancePage.jsx
 * Route: /assurance-readiness
 *
 * Assurance Readiness Dashboard — E10
 *
 * Tab 1 — Readiness Overview   POST /api/v1/assurance-readiness/assess
 * Tab 2 — Criteria Detail      (from assess result)
 * Tab 3 — Standards Coverage   GET  /api/v1/assurance-readiness/ref/standards
 * Tab 4 — CSRD Timeline        GET  /api/v1/assurance-readiness/ref/csrd-timeline
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
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
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
    gray:   'bg-gray-50   text-gray-600   border-gray-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

/* ── Demo entity payload ────────────────────────────────────────────────── */
const DEMO_PAYLOAD = {
  entity: {
    entity_id: 'DEMO_ENTITY_001',
    entity_name: 'Demo Financial Group',
    reporting_framework: 'CSRD_ESRS',
    assurance_standard_target: 'ISSA5000',
    target_assurance_level: 'limited',
    csrd_wave: 1,
    reporting_year: '2025',
    has_scope1_scope2_data: true,
    has_scope3_data: true,
    has_ghg_methodology: true,
    has_pcaf_dqs: true,
    has_eu_taxonomy_assessment: true,
    has_taxonomy_tsc_evidence: false,
    has_esrs2_general: true,
    has_double_materiality: true,
    has_material_esrs_dps: false,
    has_esrs_disclosure_index: false,
    has_sfdr_pai_14: true,
    has_sfdr_annex_templates: false,
    has_audit_log: false,
    has_data_lineage: false,
    has_icsr_controls: false,
    has_management_signoff: true,
    has_error_correction_procedure: false,
    has_reporting_boundary_defined: true,
    has_value_chain_scope: false,
    has_assurance_provider: false,
    has_prior_period_comparison: true,
    has_transition_plan_with_targets: true,
    has_third_party_data_documented: true,
  },
};

/* ── Seed fallback ──────────────────────────────────────────────────────── */
function genSeedData() {
  const domains = [
    { domain: 'D1', label: 'Data Governance', score: 55 },
    { domain: 'D2', label: 'GHG Methodology', score: 78 },
    { domain: 'D3', label: 'EU Taxonomy',      score: 62 },
    { domain: 'D4', label: 'ESRS Coverage',    score: 45 },
    { domain: 'D5', label: 'SFDR',             score: 58 },
    { domain: 'D6', label: 'Controls',         score: 30 },
    { domain: 'D7', label: 'Materiality',      score: 70 },
    { domain: 'D8', label: 'Completeness',     score: 52 },
  ];

  const criteria = [
    { criterion_id: 'C01', title: 'Scope 1 & 2 data available',               domain: 'D2', status: 'met',      weight: 8,  blocking: false },
    { criterion_id: 'C02', title: 'Scope 3 data available',                   domain: 'D2', status: 'met',      weight: 7,  blocking: false },
    { criterion_id: 'C03', title: 'GHG methodology documented',               domain: 'D2', status: 'met',      weight: 9,  blocking: true  },
    { criterion_id: 'C04', title: 'PCAF DQS assigned',                        domain: 'D2', status: 'met',      weight: 6,  blocking: false },
    { criterion_id: 'C05', title: 'EU Taxonomy assessment complete',           domain: 'D3', status: 'met',      weight: 8,  blocking: false },
    { criterion_id: 'C06', title: 'Taxonomy TSC evidence provided',           domain: 'D3', status: 'not_met',  weight: 9,  blocking: true  },
    { criterion_id: 'C07', title: 'ESRS2 general disclosures populated',      domain: 'D4', status: 'met',      weight: 7,  blocking: false },
    { criterion_id: 'C08', title: 'Double materiality assessment done',       domain: 'D7', status: 'met',      weight: 10, blocking: true  },
    { criterion_id: 'C09', title: 'Material ESRS DPs identified',             domain: 'D4', status: 'not_met',  weight: 9,  blocking: true  },
    { criterion_id: 'C10', title: 'Disclosure index published',               domain: 'D4', status: 'not_met',  weight: 6,  blocking: false },
    { criterion_id: 'C11', title: 'SFDR PAI 14 indicators populated',        domain: 'D5', status: 'met',      weight: 7,  blocking: false },
    { criterion_id: 'C12', title: 'SFDR Annex templates completed',           domain: 'D5', status: 'not_met',  weight: 6,  blocking: false },
    { criterion_id: 'C13', title: 'Audit log in place',                       domain: 'D1', status: 'not_met',  weight: 8,  blocking: true  },
    { criterion_id: 'C14', title: 'Data lineage documented',                  domain: 'D1', status: 'not_met',  weight: 7,  blocking: true  },
    { criterion_id: 'C15', title: 'ICSR controls framework established',      domain: 'D6', status: 'not_met',  weight: 9,  blocking: true  },
    { criterion_id: 'C16', title: 'Management sign-off obtained',             domain: 'D6', status: 'met',      weight: 8,  blocking: true  },
    { criterion_id: 'C17', title: 'Error correction procedure defined',       domain: 'D6', status: 'not_met',  weight: 6,  blocking: false },
    { criterion_id: 'C18', title: 'Reporting boundary defined',               domain: 'D8', status: 'met',      weight: 7,  blocking: false },
    { criterion_id: 'C19', title: 'Value chain scope defined',                domain: 'D8', status: 'not_met',  weight: 6,  blocking: false },
    { criterion_id: 'C20', title: 'Assurance provider engaged',               domain: 'D6', status: 'not_met',  weight: 8,  blocking: true  },
    { criterion_id: 'C21', title: 'Prior period comparison available',        domain: 'D8', status: 'met',      weight: 5,  blocking: false },
    { criterion_id: 'C22', title: 'Transition plan with targets documented',  domain: 'D7', status: 'met',      weight: 7,  blocking: false },
    { criterion_id: 'C23', title: 'Third-party data sources documented',      domain: 'D1', status: 'met',      weight: 6,  blocking: false },
    { criterion_id: 'C24', title: 'Data quality indicators applied',          domain: 'D1', status: 'partial',  weight: 6,  blocking: false },
    { criterion_id: 'C25', title: 'Peer benchmarking conducted',              domain: 'D8', status: 'partial',  weight: 4,  blocking: false },
    { criterion_id: 'C26', title: 'Independent review of materiality',        domain: 'D7', status: 'not_met',  weight: 7,  blocking: false },
  ];

  const blockingGaps = criteria.filter(c => c.status !== 'met' && c.blocking).length;
  const metCount = criteria.filter(c => c.status === 'met').length;
  const score = Math.round((metCount / criteria.length) * 100);
  const tier = score >= 80 ? 'Ready' : score >= 60 ? 'Substantial' : score >= 40 ? 'Developing' : 'Early Stage';

  return {
    overall_score_pct: score,
    readiness_tier: tier,
    blocking_gaps: blockingGaps,
    est_remediation_weeks: blockingGaps * 3 + 4,
    domain_scores: domains,
    criteria,
  };
}

/* ── Tab 1: Readiness Overview ──────────────────────────────────────────── */
function ReadinessOverview({ result }) {
  if (!result) return <p className="text-xs text-gray-400 py-8 text-center">Loading…</p>;

  const domains = result.domain_scores || [];
  const radarData = domains.map(d => ({ subject: d.label, score: d.score, fullMark: 100 }));
  const sortedDomains = [...domains].sort((a, b) => a.score - b.score);

  const tierColor = {
    'Ready': 'text-emerald-600',
    'Substantial': 'text-blue-600',
    'Developing': 'text-amber-600',
    'Early Stage': 'text-red-600',
  }[result.readiness_tier] || 'text-gray-700';

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Overall Score" value={`${result.overall_score_pct}%`}
          sub="Weighted assurance readiness"
          color={result.overall_score_pct >= 80 ? 'text-emerald-600' : result.overall_score_pct >= 60 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Readiness Tier" value={result.readiness_tier}
          sub="ISSA 5000 classification" color={tierColor} />
        <KpiCard label="Blocking Gaps" value={result.blocking_gaps}
          sub="Must-fix before engagement"
          color={result.blocking_gaps === 0 ? 'text-emerald-600' : result.blocking_gaps <= 3 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Est. Remediation" value={`${result.est_remediation_weeks}w`}
          sub="Weeks to assurance-ready" color="text-gray-700" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Domain Scores — Radar">
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
              <PolarGrid stroke="rgba(0,0,0,0.08)" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} tickCount={4} />
              <Radar name="Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.25} strokeWidth={2} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
            </RadarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Domain Scores — Ranked">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={sortedDomains} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
              <YAxis dataKey="label" type="category" tick={{ fontSize: 10 }} width={90} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
              <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                {sortedDomains.map((d, i) => (
                  <Cell key={i} fill={d.score >= 80 ? '#10b981' : d.score >= 60 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 2: Criteria Detail ─────────────────────────────────────────────── */
function CriteriaDetail({ result }) {
  const [domainFilter, setDomainFilter] = useState('all');
  const criteria = result?.criteria || genSeedData().criteria;
  const domains = [...new Set(criteria.map(c => c.domain))];

  const filtered = domainFilter === 'all' ? criteria : criteria.filter(c => c.domain === domainFilter);

  const STATUS_COLOR = {
    met:     'green',
    partial: 'amber',
    not_met: 'red',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="text-xs text-gray-500">Filter by domain:</label>
        <select value={domainFilter} onChange={e => setDomainFilter(e.target.value)}
          className="bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-blue-500">
          <option value="all">All Domains</option>
          {domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <span className="text-xs text-gray-400">{filtered.length} criteria shown</span>
      </div>

      <Section title="Assurance Criteria Assessment">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['ID', 'Title', 'Domain', 'Status', 'Weight', 'Blocking'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => {
              const isBlockingGap = c.blocking && c.status !== 'met';
              return (
                <tr key={c.criterion_id}
                  className={`border-b border-gray-100 hover:brightness-95 ${isBlockingGap ? 'bg-red-50' : ''}`}>
                  <td className="py-1.5 px-2 font-mono text-gray-500">{c.criterion_id}</td>
                  <td className="py-1.5 px-2 text-gray-700 max-w-[220px]">{c.title}</td>
                  <td className="py-1.5 px-2 font-mono text-gray-500">{c.domain}</td>
                  <td className="py-1.5 px-2">
                    <Badge
                      label={c.status === 'not_met' ? 'Not Met' : c.status === 'partial' ? 'Partial' : 'Met'}
                      color={STATUS_COLOR[c.status] || 'gray'}
                    />
                  </td>
                  <td className="py-1.5 px-2 font-mono text-gray-600">{c.weight}</td>
                  <td className="py-1.5 px-2">
                    {c.blocking && <Badge label="Blocking" color={isBlockingGap ? 'red' : 'green'} />}
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

/* ── Tab 3: Standards Coverage ──────────────────────────────────────────── */
const SEED_STANDARDS = [
  { id: 'ISAE3000', name: 'ISAE 3000 (Revised)', scope: 'Non-financial assured information', coverage_pct: 62, wave: 'Wave 1+' },
  { id: 'ISAE3410', name: 'ISAE 3410',           scope: 'GHG statement assurance',           coverage_pct: 74, wave: 'Wave 1+' },
  { id: 'ISSA5000', name: 'ISSA 5000',           scope: 'Sustainability assurance (IAASB)',  coverage_pct: 58, wave: 'Wave 2+' },
  { id: 'CSRD_ART26A', name: 'CSRD Art. 26a',   scope: 'Limited assurance mandate',         coverage_pct: 55, wave: 'Wave 1' },
];

function StandardsCoverage({ standardsData }) {
  const standards = standardsData?.length ? standardsData : SEED_STANDARDS;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {standards.map(s => (
        <div key={s.id} className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-sm text-gray-800">{s.name}</span>
            <Badge label={s.wave} color="blue" />
          </div>
          <p className="text-xs text-gray-500 mb-3">{s.scope}</p>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">Coverage</span>
            <span className="text-xs font-mono font-semibold text-gray-700">{s.coverage_pct}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${s.coverage_pct >= 80 ? 'bg-emerald-500' : s.coverage_pct >= 60 ? 'bg-amber-500' : 'bg-red-500'}`}
              style={{ width: `${s.coverage_pct}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Tab 4: CSRD Timeline ───────────────────────────────────────────────── */
const SEED_TIMELINE = [
  { wave: 'Wave 1', label: 'Large PIEs (>500 employees)',       first_reporting_year: 2025, entity_count: '~50,000 EU entities',  note: 'FY2024 reports' },
  { wave: 'Wave 2', label: 'Other Large Companies',             first_reporting_year: 2026, entity_count: '~15,000 EU entities',  note: 'FY2025 reports' },
  { wave: 'Wave 3', label: 'Listed SMEs + small non-listed',    first_reporting_year: 2027, entity_count: '~3,500 EU entities',   note: 'FY2026 reports, opt-out available' },
  { wave: 'Wave 4', label: 'Non-EU companies (turnover >€150M)',first_reporting_year: 2029, entity_count: 'Global MNCs with EU footprint', note: 'FY2028 reports' },
];

function CSRDTimeline({ timelineData }) {
  const waves = timelineData?.length ? timelineData : SEED_TIMELINE;
  const WAVE_COLOR = ['bg-red-50 border-red-200', 'bg-amber-50 border-amber-200', 'bg-blue-50 border-blue-200', 'bg-purple-50 border-purple-200'];

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500">CSRD Directive (EU) 2022/2464 — phased mandatory sustainability reporting &amp; assurance obligations</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {waves.map((w, i) => (
          <div key={w.wave} className={`border rounded-lg p-4 ${WAVE_COLOR[i] || 'bg-gray-50 border-gray-200'}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-sm text-gray-800">{w.wave}</span>
              <span className="font-mono font-semibold text-gray-700 text-sm">FY{w.first_reporting_year - 1}</span>
            </div>
            <p className="text-xs font-medium text-gray-700 mb-1">{w.label}</p>
            <p className="text-[11px] text-gray-500 mb-2">{w.entity_count}</p>
            <p className="text-[10px] text-gray-400 italic">{w.note}</p>
            <div className="mt-2 pt-2 border-t border-current/10 flex items-center gap-2">
              <span className="text-[10px] text-gray-500">First report deadline:</span>
              <span className="text-[10px] font-semibold text-gray-700">{w.first_reporting_year}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <p className="text-xs font-semibold text-gray-700 mb-2">Assurance Phase-in (CSRD Art. 26a)</p>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Period', 'Assurance Level', 'Standard', 'Notes'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ['2025–2028', 'Limited', 'ISAE 3000 / ISSA 5000', 'Mandatory for Wave 1'],
              ['2028+',     'Limited → Reasonable', 'ISSA 5000 (targeted)', 'Commission review by 2028'],
              ['TBD',       'Reasonable', 'ISSA 5000 Full', 'If feasibility confirmed'],
            ].map(([period, level, std, note]) => (
              <tr key={period} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 font-mono text-gray-600">{period}</td>
                <td className="py-1.5 px-2 text-gray-700">{level}</td>
                <td className="py-1.5 px-2 text-gray-500">{std}</td>
                <td className="py-1.5 px-2 text-gray-400">{note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── TABS config ────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'overview',   label: 'Readiness Overview' },
  { id: 'criteria',   label: 'Criteria Detail' },
  { id: 'standards',  label: 'Standards Coverage' },
  { id: 'timeline',   label: 'CSRD Timeline' },
];

/* ── Root component ─────────────────────────────────────────────────────── */
export default function AssurancePage() {
  const [tab, setTab] = useState('overview');
  const [result, setResult] = useState(null);
  const [standards, setStandards] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const seed = useMemo(() => genSeedData(), []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [assess, std, tl] = await Promise.all([
          axios.post(`${API}/api/v1/assurance-readiness/assess`, DEMO_PAYLOAD).catch(() => null),
          axios.get(`${API}/api/v1/assurance-readiness/ref/standards`).catch(() => null),
          axios.get(`${API}/api/v1/assurance-readiness/ref/csrd-timeline`).catch(() => null),
        ]);
        setResult(assess?.data || seed);
        setStandards(std?.data?.standards || null);
        setTimeline(tl?.data?.waves || null);
      } catch {
        setResult(seed);
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo entity — ISSA 5000 / ISAE 3000 assurance readiness with seed fallback." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Assurance Readiness Dashboard</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            ISSA 5000 · ISAE 3000 / 3410 · CSRD Art. 26a — Limited assurance gap analysis
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['ISSA 5000', 'ISAE 3000', 'CSRD Art.26a', 'E10'].map(b => (
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

      {loading && tab === 'overview' && (
        <div className="text-xs text-gray-400 py-8 text-center flex items-center justify-center gap-2">
          <div className="w-3 h-3 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
          Running assurance readiness assessment…
        </div>
      )}

      {(!loading || tab !== 'overview') && (
        <>
          {tab === 'overview'  && <ReadinessOverview result={result} />}
          {tab === 'criteria'  && <CriteriaDetail result={result} />}
          {tab === 'standards' && <StandardsCoverage standardsData={standards} />}
          {tab === 'timeline'  && <CSRDTimeline timelineData={timeline} />}
        </>
      )}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Assurance standards:</span> ISSA 5000 (IAASB 2024) · ISAE 3000 (Revised) · ISAE 3410 GHG · CSRD Art. 26a limited assurance mandate</p>
        <p><span className="font-semibold text-gray-500">Readiness tiers:</span> Ready ≥80% · Substantial ≥60% · Developing ≥40% · Early Stage &lt;40%</p>
      </div>
    </div>
  );
}
