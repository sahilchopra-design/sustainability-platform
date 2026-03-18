/**
 * BiodiversityFinancePage.jsx
 * Route: /biodiversity-finance
 * E23 — Biodiversity Finance Metrics (TNFD v1.0, SBTN, CBD GBF Target 15)
 * Tabs:
 *   1. TNFD Assessment    — 14 core metrics, RadarChart by pillar, maturity level
 *   2. MSA Footprint      — 4 seed land parcels, BarChart by land-use type
 *   3. SBTN Readiness     — 5-step SBTN ladder, readiness score
 *   4. CBD GBF Target 15  — 6 sub-elements, alignment level
 *   5. Reference          — 14 TNFD metrics table, ENCORE services
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const EM = '#10b981';

// ── Primitives ────────────────────────────────────────────────────────────
function Section({ title, subtitle, children, action }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-4">
      {(title || action) && (
        <div className="flex items-start justify-between mb-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, accent, badge }) {
  const accentCls = accent === 'green' ? 'text-emerald-600' : accent === 'red' ? 'text-red-600' : accent === 'amber' ? 'text-amber-600' : 'text-gray-900';
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-start justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{label}</span>
        {badge && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">{badge}</span>}
      </div>
      <div className={`text-2xl font-bold font-mono ${accentCls}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-3">
      <label className="text-xs font-medium text-gray-600 w-44 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'text', min, max, step, placeholder }) {
  return (
    <input type={type} value={value} min={min} max={max} step={step} placeholder={placeholder}
      onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Btn({ onClick, children, loading }) {
  return (
    <button onClick={onClick} disabled={loading}
      className={`px-4 py-2 rounded-lg text-xs font-semibold bg-black text-white hover:bg-gray-800 transition-colors ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}>
      {loading ? 'Running…' : children}
    </button>
  );
}

// ── Static seed data ───────────────────────────────────────────────────────
const TNFD_METRICS = [
  { id: 'B1',  pillar: 'Governance', name: 'Board oversight of nature-related issues', unit: 'Disclosure', scope: 'Entity' },
  { id: 'B2',  pillar: 'Governance', name: 'Nature-related responsibilities in management', unit: 'Disclosure', scope: 'Entity' },
  { id: 'B3',  pillar: 'Governance', name: 'Nature targets in executive remuneration', unit: 'Disclosure', scope: 'Entity' },
  { id: 'S1',  pillar: 'Strategy',   name: 'Location of assets in sensitive areas', unit: '% assets', scope: 'Asset' },
  { id: 'S2',  pillar: 'Strategy',   name: 'Dependency on ecosystem services', unit: 'Score 1-5', scope: 'Entity' },
  { id: 'S3',  pillar: 'Strategy',   name: 'Transition & physical risk scenarios', unit: 'Disclosure', scope: 'Entity' },
  { id: 'RM1', pillar: 'Risk',       name: 'Nature-related risk identification process', unit: 'Disclosure', scope: 'Entity' },
  { id: 'RM2', pillar: 'Risk',       name: 'Integration into enterprise risk management', unit: 'Disclosure', scope: 'Entity' },
  { id: 'RM3', pillar: 'Risk',       name: 'Nature risk material financial impact', unit: 'EUR M', scope: 'Entity' },
  { id: 'M1',  pillar: 'Metrics',    name: 'Land use (total footprint)', unit: 'km²', scope: 'Operations' },
  { id: 'M2',  pillar: 'Metrics',    name: 'MSA footprint (biodiversity impact)', unit: 'MSA·km²', scope: 'Operations' },
  { id: 'M3',  pillar: 'Metrics',    name: 'Water withdrawal in stressed areas', unit: 'Mm³/yr', scope: 'Operations' },
  { id: 'M4',  pillar: 'Metrics',    name: 'Species at risk in operations', unit: 'Count', scope: 'Asset' },
  { id: 'M5',  pillar: 'Metrics',    name: 'Financed land use (FIs)', unit: 'km²', scope: 'Portfolio' },
];

const SECTOR_OPTIONS = [
  { value: 'banking', label: 'Banking & Finance' },
  { value: 'agriculture', label: 'Agriculture & Food' },
  { value: 'forestry', label: 'Forestry & Land Use' },
  { value: 'mining', label: 'Mining & Metals' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'chemicals', label: 'Chemicals & Pharma' },
  { value: 'energy', label: 'Energy & Utilities' },
  { value: 'transport', label: 'Transport & Logistics' },
];

const PILLAR_SCORES_SEED = {
  banking:     { Governance: 68, Strategy: 52, Risk: 61, Metrics: 44 },
  agriculture: { Governance: 55, Strategy: 70, Risk: 58, Metrics: 62 },
  forestry:    { Governance: 61, Strategy: 78, Risk: 72, Metrics: 80 },
  mining:      { Governance: 74, Strategy: 48, Risk: 65, Metrics: 55 },
  real_estate: { Governance: 72, Strategy: 60, Risk: 68, Metrics: 51 },
  chemicals:   { Governance: 65, Strategy: 54, Risk: 70, Metrics: 48 },
  energy:      { Governance: 70, Strategy: 58, Risk: 64, Metrics: 52 },
  transport:   { Governance: 62, Strategy: 50, Risk: 59, Metrics: 43 },
};

const LAND_PARCELS = [
  { id: 'LP1', name: 'Nordic Forest Site',    area: 42.5, land_use: 'plantation', msa: 0.31 },
  { id: 'LP2', name: 'Iberian Cropland',      area: 18.2, land_use: 'cropland',   msa: 0.48 },
  { id: 'LP3', name: 'UK Urban Development',  area: 3.8,  land_use: 'urban',      msa: 0.12 },
  { id: 'LP4', name: 'Brazilian Secondary',   area: 85.0, land_use: 'secondary',  msa: 0.65 },
];

const LAND_USE_OPTIONS = [
  { value: 'primary',     label: 'Primary (pristine) Forest' },
  { value: 'secondary',   label: 'Secondary Vegetation' },
  { value: 'plantation',  label: 'Plantation Forest' },
  { value: 'cropland',    label: 'Cropland' },
  { value: 'urban',       label: 'Urban / Built-up' },
];

const MSA_COEFFICIENTS = { primary: 1.0, secondary: 0.65, plantation: 0.31, cropland: 0.48, urban: 0.12 };

const SBTN_STEPS = [
  { step: 1, name: 'Assess',  desc: 'Identify nature-related dependencies, impacts, risks, and opportunities across operations and value chain' },
  { step: 2, name: 'Interpret & Prioritize', desc: 'Determine priority locations and value chain categories using ENCORE, biodiversity footprint tools' },
  { step: 3, name: 'Measure & Set Targets', desc: 'Set science-based targets for land, freshwater, ocean, and biodiversity' },
  { step: 4, name: 'Act',     desc: 'Develop and implement action plans; engage value chain partners' },
  { step: 5, name: 'Track',   desc: 'Monitor and report on target progress annually; disclose via TNFD' },
];

const CBD_GBF_ELEMENTS = [
  { id: 'a', name: 'Assess nature-related risks & dependencies',          desc: 'TNFD LEAP methodology or equivalent' },
  { id: 'b', name: 'Disclose activities with negative impact on nature',  desc: 'Identify and report on biodiversity impact drivers' },
  { id: 'c', name: 'Monitor biodiversity impact metrics',                 desc: 'MSA, BII, species abundance, habitat area' },
  { id: 'd', name: 'Set reduction targets for biodiversity loss',         desc: 'SBTN-aligned targets with baselines' },
  { id: 'e', name: 'Provide finance to support biodiversity',             desc: 'Biodiversity finance flows to developing countries' },
  { id: 'f', name: 'Report progress towards GBF targets',                desc: 'Annual disclosure in line with Kunming-Montreal GBF' },
];

const ENCORE_SERVICES = [
  { category: 'Provisioning', service: 'Fibres & materials', sectors: ['Forestry', 'Agriculture', 'Textiles'] },
  { category: 'Provisioning', service: 'Freshwater supply', sectors: ['Beverages', 'Food', 'Chemicals'] },
  { category: 'Provisioning', service: 'Genetic materials', sectors: ['Pharma', 'Agriculture', 'Biotech'] },
  { category: 'Regulating', service: 'Climate regulation', sectors: ['All sectors'] },
  { category: 'Regulating', service: 'Flood & storm protection', sectors: ['Real Estate', 'Infrastructure', 'Insurance'] },
  { category: 'Regulating', service: 'Water flow regulation', sectors: ['Energy', 'Agriculture', 'Mining'] },
  { category: 'Regulating', service: 'Soil & sediment retention', sectors: ['Agriculture', 'Construction'] },
  { category: 'Cultural', service: 'Recreation & ecotourism', sectors: ['Tourism', 'Hospitality'] },
];

const SECTOR_MATERIALITY = [
  { sector: 'Banking',      dependency: 3.8, impact: 2.4 },
  { sector: 'Agriculture',  dependency: 8.6, impact: 7.2 },
  { sector: 'Forestry',     dependency: 9.1, impact: 8.4 },
  { sector: 'Mining',       dependency: 5.2, impact: 8.8 },
  { sector: 'Real Estate',  dependency: 4.1, impact: 6.3 },
  { sector: 'Energy',       dependency: 6.4, impact: 5.7 },
];

const BAR_COLORS = ['#10b981', '#6ee7b7', '#34d399', '#059669', '#047857'];

// ── Component ─────────────────────────────────────────────────────────────
export default function BiodiversityFinancePage() {
  const [tab, setTab] = useState(0);

  // Tab 0
  const [entityName, setEntityName] = useState('NatureBank AG');
  const [sector, setSector] = useState('banking');
  const [metricToggles, setMetricToggles] = useState(
    Object.fromEntries(TNFD_METRICS.map(m => [m.id, ['B1','B2','S1','RM1','RM2','M1','M2'].includes(m.id)]))
  );
  const [tnfdResult, setTnfdResult] = useState(null);
  const [tnfdLoading, setTnfdLoading] = useState(false);
  const [tnfdError, setTnfdError] = useState('');

  // Tab 1
  const [parcels, setParcels] = useState(LAND_PARCELS.map(p => ({ ...p })));
  const [msaResult, setMsaResult] = useState(null);
  const [msaLoading, setMsaLoading] = useState(false);
  const [msaError, setMsaError] = useState('');

  // Tab 2
  const [sbtnSteps, setSbtnSteps] = useState({ 1: true, 2: true, 3: false, 4: false, 5: false });
  const [sbtnResult, setSbtnResult] = useState(null);
  const [sbtnLoading, setSbtnLoading] = useState(false);
  const [sbtnError, setSbtnError] = useState('');

  // Tab 3
  const [gbfToggles, setGbfToggles] = useState({ a: true, b: true, c: false, d: false, e: false, f: false });
  const [gbfResult, setGbfResult] = useState(null);
  const [gbfLoading, setGbfLoading] = useState(false);
  const [gbfError, setGbfError] = useState('');

  const disclosedCount = Object.values(metricToggles).filter(Boolean).length;
  const pillarScores = PILLAR_SCORES_SEED[sector] || PILLAR_SCORES_SEED.banking;
  const avgPillar = Math.round(Object.values(pillarScores).reduce((a, b) => a + b, 0) / 4);
  const maturityLevel = avgPillar >= 75 ? 4 : avgPillar >= 60 ? 3 : avgPillar >= 45 ? 2 : 1;
  const maturityLabel = ['', 'Initiating', 'Developing', 'Established', 'Leading'][maturityLevel];

  const totalMSA = parcels.reduce((acc, p) => acc + p.area * (MSA_COEFFICIENTS[p.land_use] || 0.5), 0);

  const sbtnComplete = Object.values(sbtnSteps).filter(Boolean).length;

  const gbfComplete = Object.values(gbfToggles).filter(Boolean).length;
  const gbfAlignment = gbfComplete >= 5 ? 'Aligned' : gbfComplete >= 3 ? 'Progressing' : 'Early Stage';

  const radarData = Object.entries(pillarScores).map(([pillar, score]) => ({ pillar, score }));

  const msaByLandUse = ['primary','secondary','plantation','cropland','urban'].map(lu => ({
    landUse: lu,
    msa: parcels.filter(p => p.land_use === lu).reduce((acc, p) => acc + p.area * (MSA_COEFFICIENTS[lu] || 0.5), 0),
  })).filter(r => r.msa > 0);

  async function runTNFD() {
    setTnfdLoading(true); setTnfdError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/biodiversity-finance/assess-tnfd`, {
        entity_name: entityName, sector, disclosed_metrics: Object.keys(metricToggles).filter(k => metricToggles[k]),
      });
      setTnfdResult(data);
    } catch {
      setTnfdError('API unavailable — showing seed data.');
      setTnfdResult({
        maturity_level: maturityLevel, maturity_label: maturityLabel,
        pillar_scores: pillarScores, disclosed_count: disclosedCount,
        gaps: TNFD_METRICS.filter(m => !metricToggles[m.id]).map(m => m.name).slice(0, 3),
        cbd_gbf_alignment: gbfAlignment,
      });
    } finally { setTnfdLoading(false); }
  }

  async function runMSA() {
    setMsaLoading(true); setMsaError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/biodiversity-finance/msa-footprint`, {
        parcels: parcels.map(p => ({ area_km2: p.area, land_use: p.land_use })),
      });
      setMsaResult(data);
    } catch {
      setMsaError('API unavailable — showing calculated data.');
      setMsaResult({ total_msa_km2: totalMSA.toFixed(2), sector_median: 34.5 });
    } finally { setMsaLoading(false); }
  }

  async function runSBTN() {
    setSbtnLoading(true); setSbtnError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/biodiversity-finance/sbtn-readiness`, {
        entity_name: entityName, completed_steps: Object.keys(sbtnSteps).filter(k => sbtnSteps[k]).map(Number),
      });
      setSbtnResult(data);
    } catch {
      setSbtnError('API unavailable — showing seed data.');
      setSbtnResult({ readiness_score: Math.round(sbtnComplete / 5 * 100), steps_complete: sbtnComplete });
    } finally { setSbtnLoading(false); }
  }

  async function runGBF() {
    setGbfLoading(true); setGbfError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/biodiversity-finance/cbd-gbf-target15`, {
        entity_name: entityName, sub_elements: gbfToggles,
      });
      setGbfResult(data);
    } catch {
      setGbfError('API unavailable — showing seed data.');
      setGbfResult({ alignment: gbfAlignment, complete_count: gbfComplete, transition_finance_pct: 22 });
    } finally { setGbfLoading(false); }
  }

  const TABS = ['TNFD Assessment', 'MSA Footprint', 'SBTN Readiness', 'CBD GBF Target 15', 'Reference'];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-black text-white px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold tracking-tight">Biodiversity Finance Metrics</h1>
          <p className="text-xs text-gray-400 mt-0.5">TNFD v1.0 · SBTN · CBD Kunming-Montreal GBF Target 15</p>
        </div>
        <span className="text-[10px] font-bold px-2 py-1 rounded border border-emerald-500 text-emerald-400">E23</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-6 py-4">
        <KpiCard label="TNFD Maturity" value={`L${maturityLevel}`} sub={maturityLabel} accent={maturityLevel >= 3 ? 'green' : maturityLevel >= 2 ? 'amber' : 'red'} badge="TNFD" />
        <KpiCard label="MSA Footprint km²" value={totalMSA.toFixed(1)} sub="Mean Species Abundance" accent="amber" />
        <KpiCard label="SBTN Steps Complete" value={`${sbtnComplete}/5`} sub="Science-Based Targets" accent={sbtnComplete >= 3 ? 'green' : 'amber'} />
        <KpiCard label="CBD GBF Alignment" value={gbfAlignment} sub={`${gbfComplete}/6 elements`} accent={gbfAlignment === 'Aligned' ? 'green' : gbfAlignment === 'Progressing' ? 'amber' : 'red'} />
      </div>

      <div className="px-6 border-b border-gray-200 bg-white">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${tab === i ? 'border-emerald-500 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >{t}</button>
          ))}
        </div>
      </div>

      <div className="px-6 py-4">

        {/* ── Tab 0: TNFD Assessment ── */}
        {tab === 0 && (
          <>
            <Section title="Entity Configuration">
              <Row label="Entity Name"><Inp value={entityName} onChange={setEntityName} type="text" /></Row>
              <Row label="Sector"><Sel value={sector} onChange={setSector} options={SECTOR_OPTIONS} /></Row>
            </Section>
            <Section title="14 Core Metric Disclosure Toggles" subtitle="Select which TNFD core metrics are currently disclosed">
              {['Governance', 'Strategy', 'Risk', 'Metrics'].map(pillar => (
                <div key={pillar} className="mb-4">
                  <div className="text-xs font-bold text-gray-600 mb-2 uppercase tracking-wider">{pillar}</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {TNFD_METRICS.filter(m => m.pillar === pillar).map(m => (
                      <label key={m.id} className={`flex items-start gap-3 p-2.5 rounded-lg border cursor-pointer ${metricToggles[m.id] ? 'border-emerald-300 bg-emerald-50' : 'border-gray-200 bg-white'}`}>
                        <input type="checkbox" checked={metricToggles[m.id]} onChange={() => setMetricToggles(p => ({ ...p, [m.id]: !p[m.id] }))} className="mt-0.5 accent-emerald-500" />
                        <div>
                          <span className="text-xs font-bold text-emerald-700">{m.id}</span>
                          <span className="text-xs text-gray-600 ml-2">{m.name}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <Btn onClick={runTNFD} loading={tnfdLoading}>Run TNFD Assessment</Btn>
            </Section>
            {tnfdError && <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded p-3 mb-3">{tnfdError}</div>}
            {tnfdResult && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Section title="Pillar Scores — RadarChart">
                  <ResponsiveContainer width="100%" height={220}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#e5e7eb" />
                      <PolarAngleAxis dataKey="pillar" tick={{ fontSize: 11 }} />
                      <Radar name="Score" dataKey="score" stroke={EM} fill={EM} fillOpacity={0.3} />
                    </RadarChart>
                  </ResponsiveContainer>
                </Section>
                <Section title="Assessment Summary">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`text-4xl font-bold font-mono ${maturityLevel >= 3 ? 'text-emerald-600' : maturityLevel >= 2 ? 'text-amber-600' : 'text-red-600'}`}>L{tnfdResult.maturity_level}</div>
                    <div>
                      <div className="text-sm font-bold text-gray-800">{tnfdResult.maturity_label}</div>
                      <div className="text-xs text-gray-500">{tnfdResult.disclosed_count}/14 metrics disclosed</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs text-gray-500">CBD GBF Alignment:</span>
                    <span className={`px-2 py-0.5 text-xs font-bold rounded ${tnfdResult.cbd_gbf_alignment === 'Aligned' ? 'bg-emerald-100 text-emerald-700' : tnfdResult.cbd_gbf_alignment === 'Progressing' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'}`}>{tnfdResult.cbd_gbf_alignment}</span>
                  </div>
                  {tnfdResult.gaps?.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-1">Top Gaps</div>
                      {tnfdResult.gaps.map(g => (
                        <div key={g} className="text-xs text-red-700 bg-red-50 rounded px-3 py-1 mb-1">{g}</div>
                      ))}
                    </div>
                  )}
                </Section>
              </div>
            )}
          </>
        )}

        {/* ── Tab 1: MSA Footprint ── */}
        {tab === 1 && (
          <>
            <Section title="Land Parcel Configuration" subtitle="Enter land areas and use types; MSA coefficient applied automatically">
              <table className="w-full text-xs mb-4">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">Parcel</th>
                  <th className="text-left py-2 text-gray-500">Name</th>
                  <th className="text-right py-2 text-gray-500">Area (km²)</th>
                  <th className="text-left py-2 text-gray-500">Land Use</th>
                  <th className="text-right py-2 text-gray-500">MSA Coeff.</th>
                  <th className="text-right py-2 text-gray-500">MSA·km²</th>
                </tr></thead>
                <tbody>
                  {parcels.map((p, i) => (
                    <tr key={p.id} className="border-b border-gray-100">
                      <td className="py-1.5 font-bold text-emerald-700">{p.id}</td>
                      <td className="py-1.5">{p.name}</td>
                      <td className="py-1.5 text-right">
                        <input type="number" step="0.1" min="0" value={p.area}
                          onChange={e => setParcels(prev => prev.map((pp, ii) => ii === i ? { ...pp, area: parseFloat(e.target.value) || 0 } : pp))}
                          className="w-20 text-xs border border-gray-300 rounded px-2 py-1 text-right" />
                      </td>
                      <td className="py-1.5">
                        <select value={p.land_use}
                          onChange={e => setParcels(prev => prev.map((pp, ii) => ii === i ? { ...pp, land_use: e.target.value } : pp))}
                          className="text-xs border border-gray-300 rounded px-2 py-1">
                          {LAND_USE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                      </td>
                      <td className="py-1.5 text-right font-mono text-gray-500">{MSA_COEFFICIENTS[p.land_use] || 0.5}</td>
                      <td className="py-1.5 text-right font-mono font-bold text-emerald-700">{(p.area * (MSA_COEFFICIENTS[p.land_use] || 0.5)).toFixed(2)}</td>
                    </tr>
                  ))}
                  <tr className="font-bold border-t-2 border-gray-300">
                    <td className="py-2" colSpan={5}>Total MSA Footprint</td>
                    <td className="py-2 text-right font-mono text-emerald-700">{totalMSA.toFixed(2)}</td>
                  </tr>
                </tbody>
              </table>
              <Btn onClick={runMSA} loading={msaLoading}>Calculate MSA Footprint</Btn>
              {msaError && <div className="text-xs text-amber-600 mt-2">{msaError}</div>}
              {msaResult && (
                <div className="flex gap-4 mt-4">
                  <div className="p-4 rounded-xl bg-emerald-50 text-center flex-1">
                    <div className="text-2xl font-bold font-mono text-emerald-700">{msaResult.total_msa_km2}</div>
                    <div className="text-xs text-gray-500 mt-1">Total MSA·km²</div>
                  </div>
                  <div className="p-4 rounded-xl bg-gray-50 text-center flex-1">
                    <div className={`text-2xl font-bold font-mono ${parseFloat(msaResult.total_msa_km2) <= msaResult.sector_median ? 'text-emerald-600' : 'text-red-600'}`}>{msaResult.sector_median}</div>
                    <div className="text-xs text-gray-500 mt-1">Sector Median</div>
                  </div>
                </div>
              )}
            </Section>
            <Section title="MSA by Land Use Type">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={msaByLandUse} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="landUse" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="msa" name="MSA·km²" fill={EM} radius={[4, 4, 0, 0]}>
                    {msaByLandUse.map((_, i) => <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}

        {/* ── Tab 2: SBTN Readiness ── */}
        {tab === 2 && (
          <>
            <Section title="SBTN 5-Step Readiness Ladder" subtitle="Science Based Targets Network — for nature-based target setting">
              <div className="space-y-3 mb-4">
                {SBTN_STEPS.map(s => (
                  <label key={s.step} className={`flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-colors ${sbtnSteps[s.step] ? 'border-emerald-300 bg-emerald-50' : 'border-gray-200 bg-white'}`}>
                    <input type="checkbox" checked={sbtnSteps[s.step]} onChange={() => setSbtnSteps(p => ({ ...p, [s.step]: !p[s.step] }))} className="mt-0.5 accent-emerald-500" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${sbtnSteps[s.step] ? 'bg-emerald-500 text-white' : 'bg-gray-200 text-gray-500'}`}>{s.step}</span>
                        <span className="text-sm font-semibold text-gray-800">{s.name}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{s.desc}</p>
                    </div>
                  </label>
                ))}
              </div>
              <Btn onClick={runSBTN} loading={sbtnLoading}>Assess SBTN Readiness</Btn>
              {sbtnError && <div className="text-xs text-amber-600 mt-2">{sbtnError}</div>}
            </Section>
            {(sbtnResult || sbtnComplete > 0) && (
              <Section title="Readiness Score">
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className={`text-3xl font-bold font-mono ${sbtnComplete >= 3 ? 'text-emerald-600' : 'text-amber-600'}`}>{Math.round(sbtnComplete / 5 * 100)}%</div>
                    <div className="text-xs text-gray-500 mt-1">Readiness Score</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className="text-3xl font-bold font-mono text-gray-700">{sbtnComplete}/5</div>
                    <div className="text-xs text-gray-500 mt-1">Steps Complete</div>
                  </div>
                </div>
                <div className="text-xs font-semibold text-gray-600 mb-1">Target Type Coverage</div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { type: 'No-Net-Loss', met: sbtnComplete >= 2 },
                    { type: 'Net-Gain', met: sbtnComplete >= 4 },
                    { type: 'Species', met: sbtnComplete >= 3 },
                    { type: 'Area', met: sbtnComplete >= 3 },
                    { type: 'Ecosystem', met: sbtnComplete >= 4 },
                  ].map(t => (
                    <span key={t.type} className={`px-2 py-1 text-xs rounded border font-medium ${t.met ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : 'border-gray-200 text-gray-400'}`}>{t.type}</span>
                  ))}
                </div>
              </Section>
            )}
          </>
        )}

        {/* ── Tab 3: CBD GBF Target 15 ── */}
        {tab === 3 && (
          <>
            <Section title="CBD Kunming-Montreal GBF Target 15" subtitle="Business disclosure & assessment of biodiversity impacts, dependencies, and risks">
              <div className="space-y-2 mb-4">
                {CBD_GBF_ELEMENTS.map(el => (
                  <label key={el.id} className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer ${gbfToggles[el.id] ? 'border-emerald-300 bg-emerald-50' : 'border-gray-200 bg-white'}`}>
                    <input type="checkbox" checked={gbfToggles[el.id]} onChange={() => setGbfToggles(p => ({ ...p, [el.id]: !p[el.id] }))} className="mt-0.5 accent-emerald-500" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-emerald-700 uppercase">Sub-element {el.id}</span>
                      </div>
                      <div className="text-xs font-medium text-gray-700">{el.name}</div>
                      <div className="text-xs text-gray-400">{el.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
              <Btn onClick={runGBF} loading={gbfLoading}>Assess GBF Alignment</Btn>
              {gbfError && <div className="text-xs text-amber-600 mt-2">{gbfError}</div>}
            </Section>
            {(gbfResult || gbfComplete >= 0) && (
              <Section title="GBF Assessment Results">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className={`text-xl font-bold ${gbfAlignment === 'Aligned' ? 'text-emerald-600' : gbfAlignment === 'Progressing' ? 'text-amber-600' : 'text-gray-500'}`}>{gbfAlignment}</div>
                    <div className="text-xs text-gray-500 mt-1">Overall Alignment</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className="text-3xl font-bold font-mono text-gray-700">{gbfComplete}/6</div>
                    <div className="text-xs text-gray-500 mt-1">Sub-elements Met</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className="text-3xl font-bold font-mono text-emerald-600">22%</div>
                    <div className="text-xs text-gray-500 mt-1">Transition Finance %</div>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 mb-1">
                  <div className={`h-3 rounded-full ${gbfAlignment === 'Aligned' ? 'bg-emerald-500' : gbfAlignment === 'Progressing' ? 'bg-amber-400' : 'bg-gray-400'}`} style={{ width: `${Math.round(gbfComplete / 6 * 100)}%` }} />
                </div>
                <div className="text-xs text-gray-500">{Math.round(gbfComplete / 6 * 100)}% of Target 15 sub-elements addressed</div>
              </Section>
            )}
          </>
        )}

        {/* ── Tab 4: Reference ── */}
        {tab === 4 && (
          <>
            <Section title="14 TNFD Core Metrics — v1.0 (2023)">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">ID</th>
                  <th className="text-left py-2 text-gray-500">Pillar</th>
                  <th className="text-left py-2 text-gray-500">Metric Name</th>
                  <th className="text-left py-2 text-gray-500">Unit</th>
                  <th className="text-left py-2 text-gray-500">Scope</th>
                </tr></thead>
                <tbody>
                  {TNFD_METRICS.map(m => (
                    <tr key={m.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-1.5 font-bold text-emerald-700">{m.id}</td>
                      <td className="py-1.5"><span className={`px-2 py-0.5 text-[10px] font-bold rounded ${m.pillar === 'Governance' ? 'bg-blue-50 text-blue-700' : m.pillar === 'Strategy' ? 'bg-purple-50 text-purple-700' : m.pillar === 'Risk' ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>{m.pillar}</span></td>
                      <td className="py-1.5">{m.name}</td>
                      <td className="py-1.5 font-mono text-gray-500">{m.unit}</td>
                      <td className="py-1.5 text-gray-400">{m.scope}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Sector Biodiversity Materiality (ENCORE)">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={SECTOR_MATERIALITY} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="sector" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} domain={[0, 10]} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <Bar dataKey="dependency" name="Ecosystem Dependency" fill={EM} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="impact" name="Biodiversity Impact" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="ENCORE Ecosystem Services">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">Category</th>
                  <th className="text-left py-2 text-gray-500">Service</th>
                  <th className="text-left py-2 text-gray-500">Dependent Sectors</th>
                </tr></thead>
                <tbody>
                  {ENCORE_SERVICES.map((r, i) => (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-1.5"><span className={`px-2 py-0.5 text-[10px] font-bold rounded ${r.category === 'Provisioning' ? 'bg-emerald-50 text-emerald-700' : r.category === 'Regulating' ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'}`}>{r.category}</span></td>
                      <td className="py-1.5 font-medium">{r.service}</td>
                      <td className="py-1.5 text-gray-500">{r.sectors.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
