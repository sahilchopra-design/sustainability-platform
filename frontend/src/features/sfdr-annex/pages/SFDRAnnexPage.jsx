/**
 * SFDRAnnexPage.jsx
 * Route: /sfdr-annex
 *
 * SFDR Annex I-V Disclosure Templates — E9
 *
 * Tab 1 — Annex Generator     POST /api/v1/sfdr-annex/generate/annex-{roman}
 * Tab 2 — PAI Indicators      GET  /api/v1/sfdr-annex/ref/pai-indicators
 * Tab 3 — Template Fields     GET  /api/v1/sfdr-annex/ref/template-fields
 * Tab 4 — Validation          POST /api/v1/sfdr-annex/validate
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

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
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

/* ── Annex definitions ──────────────────────────────────────────────────── */
const ANNEX_OPTIONS = [
  { id: 'i',   roman: 'I',   label: 'Annex I — PAI Statement',          article: 'Art. 4 RTS',   sfdr: 'Entity-level' },
  { id: 'ii',  roman: 'II',  label: 'Annex II — Art. 8 Pre-contractual', article: 'Art. 8',       sfdr: 'Product-level' },
  { id: 'iii', roman: 'III', label: 'Annex III — Art. 8 Periodic',       article: 'Art. 11',      sfdr: 'Product-level' },
  { id: 'iv',  roman: 'IV',  label: 'Annex IV — Art. 9 Pre-contractual', article: 'Art. 9',       sfdr: 'Product-level' },
  { id: 'v',   roman: 'V',   label: 'Annex V — Art. 9 Periodic',         article: 'Art. 11',      sfdr: 'Product-level' },
];

/* ── Demo fund payload ──────────────────────────────────────────────────── */
const DEMO_FUND = {
  fund: {
    fund_id: 'FUND_DEMO_001',
    fund_name: 'European Sustainable Equity Fund',
    legal_entity_identifier: '213800FGJKGOO6O3JZ30',
    isin: 'LU9876543210',
    sfdr_classification: 'art8',
    fund_manager: 'Demo Asset Management',
    total_aum_eur: 850000000,
    proportion_sustainable_investments_pct: 65,
    proportion_taxonomy_aligned_pct: 28,
    environmental_characteristics: ['GHG emission reduction', 'Energy efficiency', 'Circular economy'],
    social_characteristics: ['Labour standards', 'Gender equality'],
    taxonomy_objectives: ['CCM', 'CCA'],
    investment_strategy_description: 'ESG integration + best-in-class selection with exclusions',
    engagement_policy: 'Active ownership: annual AGM engagement, climate resolution voting per NZAMI',
    dnsh_methodology: 'Exclusion of NACE C19/C24 + PAI threshold monitoring',
    data_sources: ['MSCI ESG', 'Sustainalytics', 'Bloomberg Green'],
    data_limitations: 'Estimated data for 15% of portfolio',
    due_diligence_description: 'Quarterly ESG score review + annual sector deep-dives',
    pct_sustainable_environmental: 50,
    pct_sustainable_social: 15,
    pct_taxonomy_aligned_environmental: 28,
    reference_period_start: '2025-01-01',
    reference_period_end: '2025-12-31',
    pai_indicators: [
      { indicator_id: '1',  value: 120.5, coverage_pct: 85, data_source: 'MSCI',           data_quality_score: 2 },
      { indicator_id: '2',  value: 95.2,  coverage_pct: 85, data_source: 'MSCI',           data_quality_score: 2 },
      { indicator_id: '3',  value: 180.0, coverage_pct: 80, data_source: 'Sustainalytics', data_quality_score: 3 },
      { indicator_id: '4',  value: 3.2,   coverage_pct: 90, data_source: 'Sustainalytics', data_quality_score: 2 },
      { indicator_id: '13', value: 22.5,  coverage_pct: 70, data_source: 'Bloomberg',      data_quality_score: 3 },
    ],
    top_investments: [
      { name: 'Vestas Wind Systems',  isin: 'DK0061539921', weight_pct: 4.2, sector: 'Energy',      country: 'DK' },
      { name: 'Orsted',               isin: 'DK0060094928', weight_pct: 3.8, sector: 'Energy',      country: 'DK' },
      { name: 'Schneider Electric',   isin: 'FR0000121972', weight_pct: 3.5, sector: 'Industrials', country: 'FR' },
    ],
  },
};

/* ── Seed fallback for annex result ─────────────────────────────────────── */
function genAnnexSeed(annexId) {
  const sections = {
    i:   [
      { section_id: 'S1', title: 'Statement on PAIs', mandatory: true,  populated: true  },
      { section_id: 'S2', title: 'Description of PAIs', mandatory: true, populated: true  },
      { section_id: 'S3', title: 'Action taken / planned', mandatory: true, populated: true },
      { section_id: 'S4', title: 'Engagement policies', mandatory: true, populated: false },
      { section_id: 'S5', title: 'Reference to international standards', mandatory: false, populated: true },
    ],
    ii:  [
      { section_id: 'S1', title: 'Environmental characteristics',        mandatory: true,  populated: true  },
      { section_id: 'S2', title: 'Social characteristics',               mandatory: true,  populated: true  },
      { section_id: 'S3', title: 'Investment strategy',                  mandatory: true,  populated: true  },
      { section_id: 'S4', title: 'Proportion sustainable investments',   mandatory: true,  populated: true  },
      { section_id: 'S5', title: 'Taxonomy alignment %',                 mandatory: true,  populated: true  },
      { section_id: 'S6', title: 'DNSH methodology',                     mandatory: true,  populated: true  },
      { section_id: 'S7', title: 'Data sources & limitations',           mandatory: true,  populated: true  },
      { section_id: 'S8', title: 'Due diligence',                        mandatory: false, populated: true  },
    ],
    iii: [
      { section_id: 'S1', title: 'Environmental characteristics achieved', mandatory: true, populated: true  },
      { section_id: 'S2', title: 'PAI indicators reported',              mandatory: true,  populated: false },
      { section_id: 'S3', title: 'Taxonomy alignment achieved',          mandatory: true,  populated: true  },
      { section_id: 'S4', title: 'Top investments (top 15)',             mandatory: true,  populated: true  },
      { section_id: 'S5', title: 'Asset allocation',                     mandatory: false, populated: false },
    ],
    iv:  [
      { section_id: 'S1', title: 'Sustainable investment objective',     mandatory: true,  populated: true  },
      { section_id: 'S2', title: 'No significant harm statement',        mandatory: true,  populated: false },
      { section_id: 'S3', title: 'Investment strategy',                  mandatory: true,  populated: true  },
      { section_id: 'S4', title: 'Proportion sustainable investments',   mandatory: true,  populated: true  },
      { section_id: 'S5', title: 'DNSH methodology',                     mandatory: true,  populated: false },
      { section_id: 'S6', title: 'Monitoring of objectives',             mandatory: true,  populated: true  },
    ],
    v:   [
      { section_id: 'S1', title: 'Attainment of sustainable objectives', mandatory: true, populated: true  },
      { section_id: 'S2', title: 'PAI indicators (all 18)',              mandatory: true,  populated: false },
      { section_id: 'S3', title: 'Taxonomy alignment achieved',          mandatory: true,  populated: true  },
      { section_id: 'S4', title: 'Top investments (top 15)',             mandatory: true,  populated: true  },
      { section_id: 'S5', title: 'Comparison to reference benchmark',   mandatory: false, populated: false },
    ],
  };
  const s = sections[annexId] || sections.ii;
  const mandatory = s.filter(x => x.mandatory);
  const populated = s.filter(x => x.populated);
  const mandatoryPopulated = s.filter(x => x.mandatory && x.populated);
  const completeness = Math.round((populated.length / s.length) * 100);
  const paiCoverage = Math.round((DEMO_FUND.fund.pai_indicators.length / 14) * 100);
  return {
    completeness_pct: completeness,
    compliance_status: completeness >= 90 ? 'Compliant' : completeness >= 70 ? 'Partially Compliant' : 'Non-Compliant',
    mandatory_sections_populated: `${mandatoryPopulated.length} / ${mandatory.length}`,
    pai_coverage_pct: paiCoverage,
    sections: s,
  };
}

/* ── Tab 1: Annex Generator ─────────────────────────────────────────────── */
function AnnexGenerator() {
  const [selectedAnnex, setSelectedAnnex] = useState('ii');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const annexDef = ANNEX_OPTIONS.find(a => a.id === selectedAnnex) || ANNEX_OPTIONS[1];

  const seed = useMemo(() => genAnnexSeed(selectedAnnex), [selectedAnnex]);

  async function generate() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/sfdr-annex/generate/annex-${annexDef.roman.toLowerCase()}`, DEMO_FUND);
      setResult(res.data);
    } catch {
      setResult(seed);
    } finally {
      setLoading(false);
    }
  }

  const display = result || seed;

  const complianceColor = {
    'Compliant': 'text-emerald-600',
    'Partially Compliant': 'text-amber-600',
    'Non-Compliant': 'text-red-600',
  }[display.compliance_status] || 'text-gray-700';

  return (
    <div className="space-y-4">
      {/* Annex selector */}
      <Section title="Select Annex Template">
        <div className="flex flex-wrap gap-2">
          {ANNEX_OPTIONS.map(a => (
            <button key={a.id} onClick={() => { setSelectedAnnex(a.id); setResult(null); }}
              className={`px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                selectedAnnex === a.id
                  ? 'bg-black text-white border-black shadow-sm'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-gray-500'
              }`}>
              <div className="font-semibold">{a.roman}</div>
              <div className="text-[10px] mt-0.5 opacity-75">{a.sfdr}</div>
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-3">
          <span className="font-medium text-gray-700">{annexDef.label}</span>
          {' · '}{annexDef.article}
        </p>
        <div className="mt-3">
          <button onClick={generate} disabled={loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded bg-black text-white text-xs font-medium hover:bg-gray-800 disabled:opacity-40 transition-all">
            {loading && <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
            Generate Annex {annexDef.roman}
          </button>
        </div>
      </Section>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Completeness" value={`${display.completeness_pct}%`}
          sub="Sections populated"
          color={display.completeness_pct >= 90 ? 'text-emerald-600' : display.completeness_pct >= 70 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Compliance Status" value={display.compliance_status}
          sub={annexDef.article} color={complianceColor} />
        <KpiCard label="Mandatory Sections" value={display.mandatory_sections_populated}
          sub="Populated / required" color="text-gray-700" />
        <KpiCard label="PAI Coverage" value={`${display.pai_coverage_pct}%`}
          sub="Of 14 mandatory indicators"
          color={display.pai_coverage_pct >= 80 ? 'text-emerald-600' : 'text-amber-600'} />
      </div>

      <Section title={`Sections Completeness — Annex ${annexDef.roman}`}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['ID', 'Section Title', 'Mandatory', 'Populated'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {display.sections?.map(s => (
              <tr key={s.section_id}
                className={`border-b border-gray-100 hover:bg-gray-50 ${!s.populated && s.mandatory ? 'bg-red-50/30' : ''}`}>
                <td className="py-1.5 px-2 font-mono text-gray-500">{s.section_id}</td>
                <td className="py-1.5 px-2 text-gray-700">{s.title}</td>
                <td className="py-1.5 px-2">
                  <Badge label={s.mandatory ? 'Mandatory' : 'Optional'} color={s.mandatory ? 'red' : 'gray'} />
                </td>
                <td className="py-1.5 px-2">
                  <Badge label={s.populated ? 'Yes' : 'No'} color={s.populated ? 'green' : s.mandatory ? 'red' : 'gray'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 2: PAI Indicators ──────────────────────────────────────────────── */
const SEED_PAI = [
  { id: '1',  description: 'GHG emissions (Scope 1, 2, 3)',                 metric: 'tCO₂e / €M invested', mandatory: true  },
  { id: '2',  description: 'Carbon footprint',                              metric: 'tCO₂e / €M invested', mandatory: true  },
  { id: '3',  description: 'GHG intensity of investee companies',          metric: 'tCO₂e / €M revenue',  mandatory: true  },
  { id: '4',  description: 'Exposure to fossil fuel companies',            metric: '% portfolio',          mandatory: true  },
  { id: '5',  description: 'Share of non-renewable energy consumption',    metric: '%',                    mandatory: true  },
  { id: '6',  description: 'Energy consumption intensity',                 metric: 'MWh / €M revenue',    mandatory: true  },
  { id: '7',  description: 'Activities negatively affecting biodiversity', metric: '% portfolio',          mandatory: true  },
  { id: '8',  description: 'Emissions to water',                           metric: 'tonnes',               mandatory: true  },
  { id: '9',  description: 'Hazardous waste ratio',                        metric: 'tonnes / €M revenue',  mandatory: true  },
  { id: '10', description: 'UNGC / OECD MNE violations',                  metric: 'Share in violation',   mandatory: true  },
  { id: '11', description: 'Lack of processes to monitor UNGC / OECD',   metric: '% portfolio',          mandatory: true  },
  { id: '12', description: 'Unadjusted gender pay gap',                   metric: '%',                    mandatory: true  },
  { id: '13', description: 'Board gender diversity',                       metric: '% female board',       mandatory: true  },
  { id: '14', description: 'Exposure to controversial weapons',           metric: '% portfolio',          mandatory: true  },
  { id: 'E1', description: 'Real estate energy consumption intensity',    metric: 'kWh / m²',             mandatory: false },
  { id: 'E2', description: 'Real estate GHG intensity',                   metric: 'kgCO₂e / m²',          mandatory: false },
  { id: 'S1', description: 'Excessive CEO pay ratio',                     metric: 'Ratio',                mandatory: false },
  { id: 'S2', description: 'Lack of supplier CoC',                       metric: '% portfolio',          mandatory: false },
];

function PAIIndicators({ paiData }) {
  const indicators = paiData?.length ? paiData : SEED_PAI;
  const mandatory = indicators.filter(i => i.mandatory);
  const optional  = indicators.filter(i => !i.mandatory);

  function Table({ rows, title }) {
    return (
      <Section title={title}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['ID', 'Description', 'Metric', 'Type'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 font-mono text-gray-500">{r.id}</td>
                <td className="py-1.5 px-2 text-gray-700 max-w-[260px]">{r.description}</td>
                <td className="py-1.5 px-2 text-gray-500 font-mono">{r.metric}</td>
                <td className="py-1.5 px-2">
                  <Badge label={r.mandatory ? 'Mandatory' : 'Optional'} color={r.mandatory ? 'red' : 'gray'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <KpiCard label="Mandatory Indicators" value={mandatory.length} sub="Table 1 — RTS Annex I" color="text-red-600" />
        <KpiCard label="Optional Indicators"  value={optional.length}  sub="Tables 2-3" color="text-gray-600" />
        <KpiCard label="Total PAI Indicators" value={indicators.length} sub="Full RTS Annex I scope" />
      </div>
      <Table rows={mandatory} title="Table 1 — Mandatory PAI Indicators (14)" />
      <Table rows={optional}  title="Tables 2-3 — Optional / Additional Indicators" />
    </div>
  );
}

/* ── Tab 3: Template Fields ─────────────────────────────────────────────── */
const SEED_FIELDS = {
  i:   { mandatory: ['Legal entity name', 'Reference period', 'PAI indicators (14)', 'Actions taken', 'Engagement policies'],                                                                                                optional: ['Reference benchmarks', 'International standards'] },
  ii:  { mandatory: ['Fund name', 'ISIN', 'Fund manager', 'Env. characteristics', 'Social characteristics', 'Investment strategy', 'Proportion sustainable', 'Taxonomy %', 'DNSH methodology', 'Data sources'],           optional: ['Engagement policy', 'Reference benchmark', 'Historical comparison'] },
  iii: { mandatory: ['Fund name', 'ISIN', 'Reporting period', 'Characteristics achieved', 'PAI indicators reported', 'Taxonomy % achieved', 'Top 15 investments'],                                                          optional: ['Asset allocation breakdown', 'Engagement outcomes'] },
  iv:  { mandatory: ['Fund name', 'ISIN', 'Sustainable investment objective', 'DNSH statement', 'Investment strategy', 'Proportion 100% sustainable', 'Monitoring methodology'],                                            optional: ['Carbon reduction pathway', 'Reference index'] },
  v:   { mandatory: ['Fund name', 'ISIN', 'Reporting period', 'Objective attainment evidence', 'All 18 PAI indicators', 'Taxonomy % achieved', 'Top 15 investments'],                                                       optional: ['Comparison to reference benchmark', 'Engagement outcomes'] },
};

function TemplateFields({ fieldsData }) {
  const [openAnnex, setOpenAnnex] = useState('ii');
  const fields = fieldsData || SEED_FIELDS;

  return (
    <div className="space-y-3">
      {ANNEX_OPTIONS.map(a => {
        const isOpen = openAnnex === a.id;
        const f = fields[a.id] || { mandatory: [], optional: [] };
        return (
          <div key={a.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <button onClick={() => setOpenAnnex(isOpen ? '' : a.id)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
              <div>
                <span className="font-medium text-sm text-gray-700">{a.label}</span>
                <span className="ml-2 text-[10px] text-gray-400">{a.article}</span>
              </div>
              <span className="text-gray-400 text-xs">{isOpen ? '▲' : '▼'}</span>
            </button>
            {isOpen && (
              <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] font-semibold text-red-600 uppercase tracking-wider mb-2">
                    Mandatory Fields ({f.mandatory.length})
                  </p>
                  <ul className="space-y-1">
                    {f.mandatory.map((field, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-gray-700">
                        <span className="text-red-400 mt-0.5 shrink-0">•</span>
                        {field}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Optional Fields ({f.optional.length})
                  </p>
                  <ul className="space-y-1">
                    {f.optional.map((field, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-gray-500">
                        <span className="text-gray-300 mt-0.5 shrink-0">•</span>
                        {field}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ── Tab 4: Validation ──────────────────────────────────────────────────── */
function ValidationPanel() {
  const [annexId, setAnnexId] = useState('ii');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const annexDef = ANNEX_OPTIONS.find(a => a.id === annexId) || ANNEX_OPTIONS[1];

  async function validate() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/sfdr-annex/validate`, {
        ...DEMO_FUND,
        annex_type: annexDef.roman,
      });
      setResult(res.data);
    } catch {
      setResult(genAnnexSeed(annexId));
    } finally {
      setLoading(false);
    }
  }

  const completenessColor = result
    ? result.completeness_pct >= 90 ? '#10b981' : result.completeness_pct >= 70 ? '#f59e0b' : '#ef4444'
    : '#d1d5db';

  const missingMandatory = result?.sections?.filter(s => s.mandatory && !s.populated) || [];

  return (
    <div className="space-y-4">
      <Section title="Validate Annex Completeness">
        <div className="flex items-end gap-4 flex-wrap">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Annex Type</label>
            <select value={annexId} onChange={e => { setAnnexId(e.target.value); setResult(null); }}
              className="bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-blue-500">
              {ANNEX_OPTIONS.map(a => <option key={a.id} value={a.id}>{a.roman} — {a.sfdr}</option>)}
            </select>
          </div>
          <button onClick={validate} disabled={loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded bg-black text-white text-xs font-medium hover:bg-gray-800 disabled:opacity-40 transition-all">
            {loading && <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
            Validate {annexDef.roman}
          </button>
        </div>
        <p className="text-[11px] text-gray-400 mt-2">Using demo fund: {DEMO_FUND.fund.fund_name} ({DEMO_FUND.fund.isin})</p>
      </Section>

      {result && (
        <>
          {/* Completeness gauge */}
          <Section title="Completeness Gauge">
            <div className="flex items-center gap-6">
              <div className="relative w-24 h-24">
                <svg viewBox="0 0 36 36" className="w-24 h-24 -rotate-90">
                  <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#f3f4f6" strokeWidth="3" />
                  <circle cx="18" cy="18" r="15.9155" fill="none"
                    stroke={completenessColor} strokeWidth="3"
                    strokeDasharray={`${result.completeness_pct} ${100 - result.completeness_pct}`}
                    strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-base font-bold font-mono" style={{ color: completenessColor }}>
                    {result.completeness_pct}%
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-700">Annex {annexDef.roman} Completeness</p>
                <p className="text-xs text-gray-500">{result.compliance_status}</p>
                <p className="text-xs text-gray-500 mt-1">Mandatory: {result.mandatory_sections_populated}</p>
              </div>
            </div>
          </Section>

          {missingMandatory.length > 0 && (
            <Section title="Missing Mandatory Fields">
              <ul className="space-y-1">
                {missingMandatory.map(s => (
                  <li key={s.section_id} className="flex items-start gap-1.5 text-xs text-red-700">
                    <span className="text-red-400 mt-0.5 shrink-0">✕</span>
                    <span className="font-mono mr-1 text-red-400">{s.section_id}</span>
                    {s.title}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {missingMandatory.length === 0 && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-xs text-emerald-700 flex items-center gap-2">
              <span className="text-emerald-500">✓</span>
              All mandatory sections are populated. Annex {annexDef.roman} is ready for disclosure.
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ── TABS config ────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'generator',  label: 'Annex Generator' },
  { id: 'pai',        label: 'PAI Indicators' },
  { id: 'fields',     label: 'Template Fields' },
  { id: 'validation', label: 'Validation' },
];

/* ── Root component ─────────────────────────────────────────────────────── */
export default function SFDRAnnexPage() {
  const [tab, setTab] = useState('generator');
  const [paiData, setPaiData] = useState(null);
  const [fieldsData, setFieldsData] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [pai, fields] = await Promise.all([
          axios.get(`${API}/api/v1/sfdr-annex/ref/pai-indicators`).catch(() => null),
          axios.get(`${API}/api/v1/sfdr-annex/ref/template-fields`).catch(() => null),
        ]);
        setPaiData(pai?.data?.indicators || null);
        setFieldsData(fields?.data?.fields || null);
      } catch {}
    })();
  }, []);

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo fund — SFDR Annex I-V disclosure template generator with seed fallback data." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">SFDR Annex I-V Disclosure Templates</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Reg (EU) 2019/2088 · RTS (EU) 2022/1288 · Article 4 PAI · Articles 8 &amp; 9 pre-contractual &amp; periodic
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['SFDR', 'Art. 4 PAI', 'Art. 8/9', 'RTS 2022', 'E9'].map(b => (
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

      {tab === 'generator'  && <AnnexGenerator />}
      {tab === 'pai'        && <PAIIndicators paiData={paiData} />}
      {tab === 'fields'     && <TemplateFields fieldsData={fieldsData} />}
      {tab === 'validation' && <ValidationPanel />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Regulatory basis:</span> SFDR Reg (EU) 2019/2088 · RTS (EU) 2022/1288 (Level 2 RTS) · Commission DA (EU) 2023/363 (amendments)</p>
        <p><span className="font-semibold text-gray-500">Annex scope:</span> I PAI entity statement · II/III Art 8 pre-contractual/periodic · IV/V Art 9 pre-contractual/periodic</p>
      </div>
    </div>
  );
}
