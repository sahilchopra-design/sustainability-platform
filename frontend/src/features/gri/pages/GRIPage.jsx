/**
 * GRIPage.jsx
 * Route: /gri-standards
 *
 * GRI Standards 2021
 *
 * Tab 1 — Content Index      GET  /api/v1/gri/content-index
 * Tab 2 — Emissions (305)    POST /api/v1/gri/305/emissions
 * Tab 3 — Material Topics    GET  /api/v1/gri/topics
 * Tab 4 — SDG Mapping        GET  /api/v1/gri/sdg-mapping
 * Tab 5 — ESRS Linkage       GET  /api/v1/gri/esrs-linkage
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
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
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

/* ── Seed data ──────────────────────────────────────────────────────────── */
const CONTENT_INDEX_SEED = [
  { id: 'GRI 2-1',   title: 'Organizational details',           type: 'universal',   status: 'reported' },
  { id: 'GRI 2-2',   title: 'Entities included in reporting',   type: 'universal',   status: 'reported' },
  { id: 'GRI 2-3',   title: 'Reporting period, frequency, contact', type: 'universal', status: 'reported' },
  { id: 'GRI 2-6',   title: 'Activities, value chain, other business relationships', type: 'universal', status: 'partially' },
  { id: 'GRI 2-9',   title: 'Governance structure and composition', type: 'universal', status: 'reported' },
  { id: 'GRI 2-22',  title: 'Statement on sustainable development strategy', type: 'universal', status: 'reported' },
  { id: 'GRI 2-29',  title: 'Approach to stakeholder engagement', type: 'universal', status: 'partially' },
  { id: 'GRI 3-1',   title: 'Process to determine material topics', type: 'universal', status: 'reported' },
  { id: 'GRI 3-2',   title: 'List of material topics',          type: 'universal',   status: 'reported' },
  { id: 'GRI 201-1', title: 'Direct economic value generated and distributed', type: 'topic', status: 'reported' },
  { id: 'GRI 205-2', title: 'Communication & training on anti-corruption', type: 'topic', status: 'partially' },
  { id: 'GRI 301-1', title: 'Materials used by weight or volume', type: 'topic',     status: 'omitted' },
  { id: 'GRI 302-1', title: 'Energy consumption within the organisation', type: 'topic', status: 'reported' },
  { id: 'GRI 303-3', title: 'Water withdrawal',                 type: 'topic',       status: 'reported' },
  { id: 'GRI 304-1', title: 'Operations in or near protected areas', type: 'topic',  status: 'omitted' },
  { id: 'GRI 305-1', title: 'Direct (Scope 1) GHG emissions',   type: 'topic',       status: 'reported' },
  { id: 'GRI 305-2', title: 'Energy indirect (Scope 2) GHG emissions', type: 'topic', status: 'reported' },
  { id: 'GRI 305-3', title: 'Other indirect (Scope 3) GHG emissions', type: 'topic', status: 'partially' },
  { id: 'GRI 305-4', title: 'GHG emissions intensity',          type: 'topic',       status: 'reported' },
  { id: 'GRI 305-5', title: 'Reduction of GHG emissions',       type: 'topic',       status: 'partially' },
  { id: 'GRI 401-1', title: 'New employee hires and employee turnover', type: 'topic', status: 'reported' },
  { id: 'GRI 403-9', title: 'Work-related injuries',            type: 'topic',       status: 'reported' },
  { id: 'GRI 405-1', title: 'Diversity of governance bodies and employees', type: 'topic', status: 'partially' },
  { id: 'GRI 418-1', title: 'Substantiated complaints about data privacy', type: 'topic', status: 'omitted' },
];

const EMISSIONS_305 = [
  { id: '305-1', label: 'Scope 1 — Direct GHG',      value: 48200, unit: 'tCO2e', color: '#ef4444' },
  { id: '305-2', label: 'Scope 2 — Indirect GHG',    value: 22100, unit: 'tCO2e', color: '#f59e0b' },
  { id: '305-3', label: 'Scope 3 — Value Chain',     value: 312000, unit: 'tCO2e', color: '#f97316' },
  { id: '305-4', label: 'GHG Intensity',             value: 18.4, unit: 'tCO2e/M€', color: '#8b5cf6' },
  { id: '305-5', label: 'GHG Reductions',            value: 5800, unit: 'tCO2e', color: '#10b981' },
  { id: '305-6', label: 'ODS Emissions',             value: 0.12, unit: 'tCFC-11e', color: '#6366f1' },
  { id: '305-7', label: 'NOx/SOx/Other Air',         value: 142, unit: 'tonnes', color: '#64748b' },
];

const MATERIAL_TOPICS = [
  { id: 'GRI 201', title: 'Economic Performance', category: 'economic', sectors: ['All'] },
  { id: 'GRI 203', title: 'Indirect Economic Impacts', category: 'economic', sectors: ['Infrastructure', 'Finance'] },
  { id: 'GRI 205', title: 'Anti-Corruption', category: 'governance', sectors: ['All'] },
  { id: 'GRI 206', title: 'Anti-Competitive Behaviour', category: 'governance', sectors: ['Finance', 'Retail'] },
  { id: 'GRI 301', title: 'Materials', category: 'environmental', sectors: ['Manufacturing', 'Extractives'] },
  { id: 'GRI 302', title: 'Energy', category: 'environmental', sectors: ['All'] },
  { id: 'GRI 303', title: 'Water & Effluents', category: 'environmental', sectors: ['Agriculture', 'Manufacturing'] },
  { id: 'GRI 304', title: 'Biodiversity', category: 'environmental', sectors: ['Extractives', 'Agriculture'] },
  { id: 'GRI 305', title: 'Emissions', category: 'environmental', sectors: ['All'] },
  { id: 'GRI 306', title: 'Waste', category: 'environmental', sectors: ['Manufacturing', 'Extractives'] },
  { id: 'GRI 308', title: 'Supplier Environmental Assessment', category: 'environmental', sectors: ['All'] },
  { id: 'GRI 401', title: 'Employment', category: 'social', sectors: ['All'] },
  { id: 'GRI 403', title: 'Occupational Health & Safety', category: 'social', sectors: ['Extractives', 'Construction'] },
  { id: 'GRI 405', title: 'Diversity & Equal Opportunity', category: 'social', sectors: ['All'] },
  { id: 'GRI 413', title: 'Local Communities', category: 'social', sectors: ['Extractives', 'Infrastructure'] },
  { id: 'GRI 414', title: 'Supplier Social Assessment', category: 'social', sectors: ['All'] },
  { id: 'GRI 416', title: 'Customer Health & Safety', category: 'social', sectors: ['Retail', 'Healthcare'] },
  { id: 'GRI 418', title: 'Customer Privacy', category: 'social', sectors: ['Finance', 'Technology'] },
];

const SDG_MAPPING = [
  { gri: 'GRI 302', title: 'Energy', sdgs: ['SDG 7', 'SDG 13'], esrs: 'ESRS E1' },
  { gri: 'GRI 303', title: 'Water',  sdgs: ['SDG 6', 'SDG 14'], esrs: 'ESRS E3' },
  { gri: 'GRI 304', title: 'Biodiversity', sdgs: ['SDG 15'], esrs: 'ESRS E4' },
  { gri: 'GRI 305', title: 'Emissions', sdgs: ['SDG 13', 'SDG 9'], esrs: 'ESRS E1' },
  { gri: 'GRI 306', title: 'Waste', sdgs: ['SDG 12'], esrs: 'ESRS E5' },
  { gri: 'GRI 401', title: 'Employment', sdgs: ['SDG 8', 'SDG 10'], esrs: 'ESRS S1' },
  { gri: 'GRI 403', title: 'OHS', sdgs: ['SDG 3', 'SDG 8'], esrs: 'ESRS S1' },
  { gri: 'GRI 205', title: 'Anti-Corruption', sdgs: ['SDG 16'], esrs: 'ESRS G1' },
  { gri: 'GRI 413', title: 'Communities', sdgs: ['SDG 11', 'SDG 17'], esrs: 'ESRS S3' },
  { gri: 'GRI 416', title: 'Cust. Health', sdgs: ['SDG 3'], esrs: 'ESRS S4' },
];

const ESRS_LINKAGE = [
  { gri: 'GRI 305-1', desc: 'Scope 1 GHG', esrs: 'ESRS E1-6 §40(a)', dp: 'E1-6_GHG_Scope1', status: 'aligned' },
  { gri: 'GRI 305-2', desc: 'Scope 2 GHG', esrs: 'ESRS E1-6 §40(b)', dp: 'E1-6_GHG_Scope2', status: 'aligned' },
  { gri: 'GRI 305-3', desc: 'Scope 3 GHG', esrs: 'ESRS E1-6 §51', dp: 'E1-6_GHG_Scope3', status: 'partial' },
  { gri: 'GRI 305-4', desc: 'GHG Intensity', esrs: 'ESRS E1-6 §53', dp: 'E1-6_GHG_intensity', status: 'aligned' },
  { gri: 'GRI 302-1', desc: 'Energy Consumption', esrs: 'ESRS E1-5 §35', dp: 'E1-5_total_energy', status: 'aligned' },
  { gri: 'GRI 303-3', desc: 'Water Withdrawal', esrs: 'ESRS E3-1 §28', dp: 'E3-1_water_withdrawal', status: 'partial' },
  { gri: 'GRI 304-1', desc: 'Protected Areas', esrs: 'ESRS E4-1', dp: 'E4-1_biodiversity_sites', status: 'gap' },
  { gri: 'GRI 401-1', desc: 'Employee Turnover', esrs: 'ESRS S1-6', dp: 'S1-6_employee_turnover', status: 'aligned' },
  { gri: 'GRI 403-9', desc: 'Work Injuries', esrs: 'ESRS S1-14', dp: 'S1-14_TRIR', status: 'aligned' },
  { gri: 'GRI 205-2', desc: 'Anti-Corruption Training', esrs: 'ESRS G1-3', dp: 'G1-3_prevention_measures', status: 'partial' },
];

const CATEGORY_COLOR = { environmental: 'green', social: 'blue', governance: 'purple', economic: 'amber' };

/* ── Tab 1: Content Index ───────────────────────────────────────────────── */
function ContentIndex({ data }) {
  const rows = data?.length ? data : CONTENT_INDEX_SEED;
  const [filter, setFilter] = useState('all');

  const filtered = filter === 'all' ? rows : rows.filter(r => r.status === filter);
  const reported = rows.filter(r => r.status === 'reported').length;
  const omitted = rows.filter(r => r.status === 'omitted').length;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Standards Reported" value={reported} sub={`of ${rows.length} total`} color="text-emerald-600" />
        <KpiCard label="Omissions" value={omitted} sub="not reported" color="text-red-600" />
        <KpiCard label="Material Topics" value="18" sub="GRI topic standards" color="text-gray-900" />
        <KpiCard label="SDGs Linked" value="14" sub="of 17 SDGs covered" color="text-blue-600" />
      </div>

      <Section title="GRI Content Index — Universal & Topic Standards">
        <div className="flex gap-2 mb-3 flex-wrap">
          {['all', 'reported', 'partially', 'omitted'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
                filter === f ? 'bg-black text-white border-black' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
              }`}>
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Standard ID', 'Disclosure Title', 'Type', 'Status'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, i) => (
              <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${row.status === 'omitted' ? 'bg-red-50/30' : row.status === 'partially' ? 'bg-amber-50/20' : ''}`}>
                <td className="py-1.5 px-2 font-mono font-semibold text-gray-700">{row.id}</td>
                <td className="py-1.5 px-2 text-gray-700">{row.title}</td>
                <td className="py-1.5 px-2">
                  <Badge label={row.type} color={row.type === 'universal' ? 'blue' : 'gray'} />
                </td>
                <td className="py-1.5 px-2">
                  <Badge
                    label={row.status}
                    color={row.status === 'reported' ? 'green' : row.status === 'partially' ? 'amber' : 'red'}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 2: Emissions (GRI 305) ─────────────────────────────────────────── */
function EmissionsGRI305() {
  return (
    <div className="space-y-4">
      <Section title="GRI 305 — Emissions Disclosures Overview">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          {EMISSIONS_305.map(e => (
            <div key={e.id} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-gray-800">GRI {e.id}</span>
                <span className="text-[10px] text-gray-500 font-mono">{e.unit}</span>
              </div>
              <p className="text-[11px] text-gray-600 mb-2">{e.label}</p>
              <p className="text-lg font-bold font-mono tabular-nums" style={{ color: e.color }}>
                {e.value.toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="GHG Emissions by Scope — Bar Chart (tCO2e)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={EMISSIONS_305.slice(0, 5)} margin={{ left: 10, right: 20, top: 4, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="id" tickFormatter={v => `GRI ${v}`} tick={{ fontSize: 10 }} angle={-20} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n, p) => [v.toLocaleString(), p.payload.label]} />
            <Bar dataKey="value" name="Value" radius={[3, 3, 0, 0]}>
              {EMISSIONS_305.slice(0, 5).map((d, i) => (
                <Cell key={i} fill={d.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── Tab 3: Material Topics ─────────────────────────────────────────────── */
function MaterialTopics({ data }) {
  const topics = data?.length ? data : MATERIAL_TOPICS;
  const [catFilter, setCatFilter] = useState('all');

  const filtered = catFilter === 'all' ? topics : topics.filter(t => t.category === catFilter);

  return (
    <div className="space-y-4">
      <Section title="18 GRI Topic Standards — Filter by Category">
        <div className="flex gap-2 mb-3 flex-wrap">
          {['all', 'environmental', 'social', 'governance', 'economic'].map(c => (
            <button key={c} onClick={() => setCatFilter(c)}
              className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
                catFilter === c ? 'bg-black text-white border-black' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
              }`}>
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {filtered.map((topic, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-3 bg-white hover:shadow-sm transition-shadow">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-mono font-bold text-gray-500">{topic.id}</span>
                <Badge label={topic.category} color={CATEGORY_COLOR[topic.category]} />
              </div>
              <p className="text-xs font-semibold text-gray-800 mb-2">{topic.title}</p>
              <div className="flex flex-wrap gap-1">
                {topic.sectors.map((s, j) => (
                  <span key={j} className="text-[9px] bg-gray-50 text-gray-500 border border-gray-200 rounded px-1 py-0.5">{s}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 4: SDG Mapping ─────────────────────────────────────────────────── */
function SDGMapping({ data }) {
  const rows = data?.length ? data : SDG_MAPPING;

  return (
    <Section title="GRI Standard → SDG Goals → ESRS Cross-Reference">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-200">
            {['GRI Standard', 'Topic', 'Linked SDGs', 'ESRS Reference'].map(h => (
              <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-1.5 px-2 font-mono font-semibold text-gray-700">{row.gri}</td>
              <td className="py-1.5 px-2 text-gray-700">{row.title}</td>
              <td className="py-1.5 px-2">
                <div className="flex flex-wrap gap-1">
                  {row.sdgs.map((sdg, j) => (
                    <span key={j} className="bg-blue-50 text-blue-700 border border-blue-200 rounded px-1.5 py-0.5 text-[9px] font-semibold">{sdg}</span>
                  ))}
                </div>
              </td>
              <td className="py-1.5 px-2">
                <Badge label={row.esrs} color="green" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-[10px] text-gray-400 mt-3">
        SDG linkages based on GRI–SDG Linkage Document (2022). ESRS cross-references per EFRAG GRI–ESRS interoperability guidance.
      </p>
    </Section>
  );
}

/* ── Tab 5: ESRS Linkage ────────────────────────────────────────────────── */
function ESRSLinkage({ data }) {
  const rows = data?.length ? data : ESRS_LINKAGE;

  const STATUS_COLOR = { aligned: 'green', partial: 'amber', gap: 'red' };

  return (
    <Section title="GRI Standard ↔ ESRS Datapoint ↔ Compliance Status">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-200">
            {['GRI Standard', 'Description', 'ESRS Reference', 'ESRS Datapoint', 'Status'].map(h => (
              <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${row.status === 'gap' ? 'bg-red-50/30' : row.status === 'partial' ? 'bg-amber-50/20' : ''}`}>
              <td className="py-1.5 px-2 font-mono font-semibold text-gray-700">{row.gri}</td>
              <td className="py-1.5 px-2 text-gray-700">{row.desc}</td>
              <td className="py-1.5 px-2 font-mono text-gray-600">{row.esrs}</td>
              <td className="py-1.5 px-2 font-mono text-[10px] text-gray-500">{row.dp}</td>
              <td className="py-1.5 px-2">
                <Badge label={row.status} color={STATUS_COLOR[row.status]} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-[10px] text-gray-400 mt-3">
        Cross-mapping per EFRAG GRI–ESRS interoperability guidance (Jan 2024). "aligned" = full coverage; "partial" = partial overlap; "gap" = GRI requirement not covered by ESRS.
      </p>
    </Section>
  );
}

/* ── TABS ───────────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'index',    label: 'Content Index' },
  { id: 'emissions',label: 'Emissions (GRI 305)' },
  { id: 'topics',   label: 'Material Topics' },
  { id: 'sdg',      label: 'SDG Mapping' },
  { id: 'esrs',     label: 'ESRS Linkage' },
];

/* ── Root ───────────────────────────────────────────────────────────────── */
export default function GRIPage() {
  const [tab, setTab] = useState('index');
  const [indexData, setIndexData] = useState(null);
  const [topicsData, setTopicsData] = useState(null);
  const [sdgData, setSdgData] = useState(null);
  const [esrsData, setEsrsData] = useState(null);

  useEffect(() => {
    (async () => {
      const [idx, topics, sdg, esrs] = await Promise.all([
        axios.get(`${API}/api/v1/gri/content-index`).catch(() => null),
        axios.get(`${API}/api/v1/gri/topics`).catch(() => null),
        axios.get(`${API}/api/v1/gri/sdg-mapping`).catch(() => null),
        axios.get(`${API}/api/v1/gri/esrs-linkage`).catch(() => null),
      ]);
      setIndexData(idx?.data?.disclosures || null);
      setTopicsData(topics?.data?.topics || null);
      setSdgData(sdg?.data?.mappings || null);
      setEsrsData(esrs?.data?.linkages || null);
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo entity — GRI Standards 2021 content index with seed fallback data. 24 disclosures across universal and topic standards." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">GRI Standards 2021</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            GRI Universal Standards (GRI 1/2/3) · GRI Topic Standards · GRI–ESRS Interoperability · SDG Linkage
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['GRI 2021', 'ESRS Linked', 'SDG Mapped', 'TCFD Aligned'].map(b => (
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

      {tab === 'index'    && <ContentIndex data={indexData} />}
      {tab === 'emissions'&& <EmissionsGRI305 />}
      {tab === 'topics'   && <MaterialTopics data={topicsData} />}
      {tab === 'sdg'      && <SDGMapping data={sdgData} />}
      {tab === 'esrs'     && <ESRSLinkage data={esrsData} />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Standards basis:</span> GRI 1 Foundation 2021 · GRI 2 General Disclosures 2021 · GRI 3 Material Topics 2021 · GRI 305 Emissions 2016 (updated 2021)</p>
        <p><span className="font-semibold text-gray-500">Cross-framework:</span> EFRAG GRI–ESRS interoperability guidance (Jan 2024) · GRI–SDG Linkage Document (2022) · IFRS S2 / TCFD alignment</p>
      </div>
    </div>
  );
}
