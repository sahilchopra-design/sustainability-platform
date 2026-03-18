/**
 * TNFDPage.jsx
 * Route: /tnfd-assessment
 *
 * TNFD Nature Assessment — v1.0 Recommendations
 *
 * Tab 1 — LEAP Assessment          POST /api/v1/tnfd/leap/assess
 * Tab 2 — 14 Disclosures           POST /api/v1/tnfd/disclosures/assess
 * Tab 3 — ENCORE Dependencies      GET  /api/v1/tnfd/encore/dependencies
 * Tab 4 — Nature Impact Metrics    POST /api/v1/tnfd/metrics/assess
 * Tab 5 — Double Materiality       GET  /api/v1/tnfd/double-materiality
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
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
    gray:   'bg-gray-50   text-gray-600   border-gray-200',
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

/* ── Seed data generators ───────────────────────────────────────────────── */
const LEAP_PHASES = [
  {
    id: 'locate',
    label: 'L — Locate',
    color: 'emerald',
    steps: [
      { id: 'L1', label: 'Map business activities to value chain' },
      { id: 'L2', label: 'Identify direct operations & upstream/downstream' },
      { id: 'L3', label: 'Screen for nature-sensitive locations (KBAs, protected areas)' },
      { id: 'L4', label: 'Overlay geospatial data on ecosystem footprint' },
    ],
  },
  {
    id: 'evaluate',
    label: 'E — Evaluate',
    color: 'blue',
    steps: [
      { id: 'E1', label: 'Identify ecosystem services depended upon' },
      { id: 'E2', label: 'Assess dependency severity using ENCORE framework' },
      { id: 'E3', label: 'Quantify operational exposure to ecosystem change' },
      { id: 'E4', label: 'Map value chain ecosystem services dependencies' },
    ],
  },
  {
    id: 'assess',
    label: 'A — Assess',
    color: 'amber',
    steps: [
      { id: 'A1', label: 'Identify material nature-related risks and opportunities' },
      { id: 'A2', label: 'Assess impacts on biodiversity and ecosystem integrity' },
      { id: 'A3', label: 'Quantify financial risk using scenario analysis' },
      { id: 'A4', label: 'Evaluate regulatory and transition risk exposure' },
    ],
  },
  {
    id: 'prepare',
    label: 'P — Prepare',
    color: 'purple',
    steps: [
      { id: 'P1', label: 'Define nature-related targets aligned with GBF' },
      { id: 'P2', label: 'Develop mitigation hierarchy and action plan' },
      { id: 'P3', label: 'Integrate into governance and risk frameworks' },
      { id: 'P4', label: 'Prepare TNFD-aligned disclosure report' },
    ],
  },
];

const PILLARS = [
  {
    id: 'governance',
    label: 'Governance',
    disclosures: [
      { id: 'D1', title: 'Board oversight of nature-related risks & opportunities', status: 'reported', material: true },
      { id: 'D2', title: 'Management role in nature risk assessment and mitigation', status: 'partial', material: true },
    ],
  },
  {
    id: 'strategy',
    label: 'Strategy',
    disclosures: [
      { id: 'D3', title: 'Nature-related risks/opportunities over short, medium, long term', status: 'partial', material: true },
      { id: 'D4', title: 'Impact of nature-related risks on business model & value chain', status: 'not-reported', material: true },
      { id: 'D5', title: 'Strategy resilience to nature-related scenarios', status: 'not-reported', material: false },
      { id: 'D6', title: 'Prioritised areas and activities in nature-sensitive locations', status: 'partial', material: true },
    ],
  },
  {
    id: 'risk',
    label: 'Risk Management',
    disclosures: [
      { id: 'D7', title: 'Process for identifying and assessing nature-related risks', status: 'reported', material: false },
      { id: 'D8', title: 'Process for managing nature-related risks', status: 'partial', material: true },
      { id: 'D9', title: 'Integration of nature risk into overall risk management', status: 'not-reported', material: true },
      { id: 'D10', title: 'Identification of nature-related opportunities', status: 'not-reported', material: false },
    ],
  },
  {
    id: 'metrics',
    label: 'Metrics & Targets',
    disclosures: [
      { id: 'D11', title: 'Metrics used to assess nature-related risks and opportunities', status: 'partial', material: true },
      { id: 'D12', title: 'Metrics measuring nature-related impacts and dependencies', status: 'not-reported', material: true },
      { id: 'D13', title: 'Targets for nature-related risks, impacts, and opportunities', status: 'not-reported', material: true },
      { id: 'D14', title: 'Performance against targets — nature footprint and biodiversity', status: 'not-reported', material: false },
    ],
  },
];

const ENCORE_SERVICES = [
  { service: 'Water regulation', score: 0 },
  { service: 'Pollination', score: 0 },
  { service: 'Flood protection', score: 0 },
  { service: 'Climate regulation', score: 0 },
  { service: 'Soil quality', score: 0 },
  { service: 'Pest control', score: 0 },
  { service: 'Disease control', score: 0 },
  { service: 'Noise reduction', score: 0 },
  { service: 'Air quality', score: 0 },
  { service: 'Fibre/material provision', score: 0 },
  { service: 'Genetic material', score: 0 },
  { service: 'Ground water', score: 0 },
  { service: 'Surface water', score: 0 },
  { service: 'Erosion control', score: 0 },
  { service: 'Habitat maintenance', score: 0 },
  { service: 'Dilution (water)', score: 0 },
  { service: 'Buffering/attenuation', score: 0 },
  { service: 'Solid waste', score: 0 },
  { service: 'Aesthetic value', score: 0 },
  { service: 'Recreation/tourism', score: 0 },
  { service: 'Cultural heritage', score: 0 },
];

const DM_TOPICS = [
  { topic: 'Biodiversity loss', impact: 82, financial: 74 },
  { topic: 'Water scarcity', impact: 71, financial: 68 },
  { topic: 'Deforestation', impact: 77, financial: 55 },
  { topic: 'Soil degradation', impact: 60, financial: 42 },
  { topic: 'Ocean acidification', impact: 45, financial: 30 },
  { topic: 'Invasive species', impact: 38, financial: 28 },
  { topic: 'Pollinator decline', impact: 65, financial: 58 },
  { topic: 'Freshwater ecosystem', impact: 70, financial: 63 },
  { topic: 'Climate-nature nexus', impact: 85, financial: 79 },
  { topic: 'Supply chain nature', impact: 55, financial: 67 },
  { topic: 'Regulatory nature risk', impact: 42, financial: 72 },
  { topic: 'Nature-based solutions', impact: 50, financial: 62 },
];

function genSeedData() {
  const rng = mkRng(97);
  const checked = {};
  LEAP_PHASES.forEach(ph => {
    ph.steps.forEach(st => { checked[st.id] = rng() > 0.45; });
  });
  const encoreScores = ENCORE_SERVICES.map(s => ({
    ...s,
    score: Math.round(20 + rng() * 75),
  }));
  return { checked, encoreScores };
}

/* ── Tab 1: LEAP Assessment ─────────────────────────────────────────────── */
function LeapAssessment({ seedChecked }) {
  const [checked, setChecked] = useState(seedChecked || {});
  const [open, setOpen] = useState({ locate: true, evaluate: false, assess: false, prepare: false });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const phaseCompletion = (ph) => {
    const done = ph.steps.filter(s => checked[s.id]).length;
    return Math.round((done / ph.steps.length) * 100);
  };

  const totalPct = Math.round(
    LEAP_PHASES.reduce((sum, ph) => sum + phaseCompletion(ph), 0) / LEAP_PHASES.length
  );

  const toggle = (id) => setChecked(prev => ({ ...prev, [id]: !prev[id] }));

  const runAssess = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/tnfd/leap/assess`, { checked_steps: checked });
      setResult(res.data);
    } catch {
      setResult({ leap_progress_pct: totalPct, status: 'demo' });
    } finally {
      setLoading(false);
    }
  };

  const COLOR_MAP = { emerald: 'bg-emerald-500', blue: 'bg-blue-500', amber: 'bg-amber-500', purple: 'bg-purple-500' };
  const RING_MAP  = { emerald: 'text-emerald-600', blue: 'text-blue-600', amber: 'text-amber-600', purple: 'text-purple-600' };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {LEAP_PHASES.map(ph => {
          const pct = phaseCompletion(ph);
          return (
            <div key={ph.id} className="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{ph.label}</p>
              <p className={`text-2xl font-bold font-mono ${RING_MAP[ph.color]}`}>{pct}%</p>
              <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2">
                <div className={`h-1.5 rounded-full ${COLOR_MAP[ph.color]}`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall LEAP Progress</span>
          <span className="text-sm font-semibold font-mono">{totalPct}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${totalPct >= 75 ? 'bg-emerald-500' : totalPct >= 40 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${totalPct}%` }}
          />
        </div>
      </div>

      {LEAP_PHASES.map(ph => (
        <div key={ph.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setOpen(prev => ({ ...prev, [ph.id]: !prev[ph.id] }))}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="font-medium text-sm text-gray-800">{ph.label}</span>
              <span className={`text-[10px] font-mono ${RING_MAP[ph.color]}`}>{phaseCompletion(ph)}%</span>
            </div>
            <svg className={`w-4 h-4 text-gray-400 transition-transform ${open[ph.id] ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {open[ph.id] && (
            <div className="px-4 pb-3 border-t border-gray-100">
              {ph.steps.map(st => (
                <label key={st.id} className="flex items-center gap-3 py-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={!!checked[st.id]}
                    onChange={() => toggle(st.id)}
                    className="w-4 h-4 accent-emerald-600 cursor-pointer"
                  />
                  <span className={`text-xs ${checked[st.id] ? 'text-gray-700 line-through text-gray-400' : 'text-gray-700'}`}>
                    <span className="font-mono text-gray-400 mr-1">{st.id}</span>{st.label}
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>
      ))}

      <div className="flex items-center gap-3">
        <button
          onClick={runAssess}
          disabled={loading}
          className="px-4 py-2 bg-black text-white text-xs font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Running…' : 'Run LEAP Assessment'}
        </button>
        {result && (
          <span className="text-xs text-emerald-600 font-medium">
            Assessment complete — LEAP {result.leap_progress_pct ?? totalPct}% progress
          </span>
        )}
      </div>
    </div>
  );
}

/* ── Tab 2: 14 Disclosures ──────────────────────────────────────────────── */
function DisclosuresPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const STATUS_BADGE = {
    'reported':     { label: 'Reported',     color: 'green' },
    'partial':      { label: 'Partial',       color: 'amber' },
    'not-reported': { label: 'Not Reported',  color: 'red' },
  };

  const allDisclosures = PILLARS.flatMap(p => p.disclosures);
  const reported = allDisclosures.filter(d => d.status === 'reported').length;
  const partial  = allDisclosures.filter(d => d.status === 'partial').length;
  const totalReported = result?.disclosures_reported ?? reported;

  const runAssess = async () => {
    setLoading(true);
    try {
      const payload = { disclosures: allDisclosures.map(d => ({ id: d.id, status: d.status })) };
      const res = await axios.post(`${API}/api/v1/tnfd/disclosures/assess`, payload);
      setResult(res.data);
    } catch {
      setResult({ disclosures_reported: reported, disclosures_partial: partial });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <KpiCard label="Fully Reported" value={`${totalReported}/14`}
          color="text-emerald-600" sub="TNFD disclosures" />
        <KpiCard label="Partial" value={`${result?.disclosures_partial ?? partial}/14`}
          color="text-amber-600" sub="Partially disclosed" />
        <KpiCard label="Not Reported" value={`${14 - (result?.disclosures_partial ?? partial) - totalReported}/14`}
          color="text-red-600" sub="Gap to close" />
      </div>

      {PILLARS.map(pillar => (
        <Section key={pillar.id} title={`${pillar.label} Pillar`}>
          <div className="space-y-2">
            {pillar.disclosures.map(d => {
              const badge = STATUS_BADGE[d.status] || { label: d.status, color: 'gray' };
              return (
                <div key={d.id}
                  className={`flex items-start justify-between p-3 rounded-lg border ${
                    d.status === 'reported' ? 'bg-emerald-50/40 border-emerald-100' :
                    d.status === 'partial'  ? 'bg-amber-50/40  border-amber-100'  :
                                             'bg-red-50/30    border-red-100'
                  }`}>
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <span className="font-mono text-[10px] text-gray-400 shrink-0 mt-0.5">{d.id}</span>
                    <span className="text-xs text-gray-700">{d.title}</span>
                  </div>
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    {d.material && <Badge label="Material" color="blue" />}
                    <Badge label={badge.label} color={badge.color} />
                  </div>
                </div>
              );
            })}
          </div>
        </Section>
      ))}

      <button
        onClick={runAssess}
        disabled={loading}
        className="px-4 py-2 bg-black text-white text-xs font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Assessing…' : 'Run Disclosure Assessment'}
      </button>
    </div>
  );
}

/* ── Tab 3: ENCORE Dependencies ─────────────────────────────────────────── */
const NACE_SECTORS = [
  'A01 — Crop & animal production',
  'A02 — Forestry & logging',
  'B05 — Coal mining',
  'C10 — Food manufacturing',
  'D35 — Electricity & gas supply',
  'E36 — Water collection & supply',
  'F41 — Construction of buildings',
  'G46 — Wholesale trade',
];

function ENCOREPanel({ seedScores }) {
  const [sector, setSector] = useState(NACE_SECTORS[0]);
  const [scores, setScores] = useState(seedScores || []);
  const [loading, setLoading] = useState(false);

  const fetchDeps = async (s) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/v1/tnfd/encore/dependencies`, { params: { nace_sector: s } });
      setScores(res.data?.services || seedScores);
    } catch {
      const rng = mkRng(s.charCodeAt(0) * 37 + s.charCodeAt(1));
      setScores(ENCORE_SERVICES.map(sv => ({ ...sv, score: Math.round(15 + rng() * 80) })));
    } finally {
      setLoading(false);
    }
  };

  const radarData = scores.slice(0, 12).map(s => ({ subject: s.service.replace(' regulation', '').replace('/', '/\n'), A: s.score }));

  return (
    <div className="space-y-4">
      <Section title="NACE Sector Selection">
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={sector}
            onChange={e => { setSector(e.target.value); fetchDeps(e.target.value); }}
            className="text-xs border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            {NACE_SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          {loading && <span className="text-xs text-gray-400 flex items-center gap-1.5">
            <div className="w-3 h-3 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
            Loading dependencies…
          </span>}
        </div>
      </Section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Section title="21 ENCORE Ecosystem Service Dependencies">
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(0,0,0,0.07)" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 8, fill: '#6b7280' }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8 }} />
              <Radar name="Dependency Score" dataKey="A" stroke="#10b981" fill="#10b981" fillOpacity={0.25} strokeWidth={1.5} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v}`, 'Dependency']} />
            </RadarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Dependency Score Table">
          <div className="overflow-y-auto max-h-[320px]">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-gray-200">
                  <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Ecosystem Service</th>
                  <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Score</th>
                  <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Level</th>
                </tr>
              </thead>
              <tbody>
                {scores.map((s, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-1.5 px-2 text-gray-700">{s.service}</td>
                    <td className="py-1.5 px-2 font-mono font-semibold">{s.score}</td>
                    <td className="py-1.5 px-2">
                      <Badge
                        label={s.score >= 70 ? 'High' : s.score >= 40 ? 'Medium' : 'Low'}
                        color={s.score >= 70 ? 'red' : s.score >= 40 ? 'amber' : 'green'}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 4: Nature Impact Metrics ───────────────────────────────────────── */
function NatureMetricsPanel() {
  const [form, setForm] = useState({ land_use_ha: 250, water_withdrawal_m3: 18500, species_affected: 12, pollution_incidents: 3 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const Inp = ({ label, field, unit }) => (
    <div>
      <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label} ({unit})</label>
      <input
        type="number"
        value={form[field]}
        onChange={e => setForm(prev => ({ ...prev, [field]: Number(e.target.value) }))}
        className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
      />
    </div>
  );

  const runAssess = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/tnfd/metrics/assess`, form);
      setResult(res.data);
    } catch {
      const rng = mkRng(form.land_use_ha + form.species_affected * 7);
      setResult({
        nature_footprint_score: Math.round(35 + rng() * 50),
        kba_exposure: form.land_use_ha > 200 || form.species_affected > 10,
        dependency_score: Math.round(40 + rng() * 45),
        water_intensity: (form.water_withdrawal_m3 / Math.max(form.land_use_ha, 1)).toFixed(1),
        species_risk_flag: form.species_affected > 8,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Section title="Nature Impact Inputs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Inp label="Land Use" field="land_use_ha" unit="ha" />
          <Inp label="Water Withdrawal" field="water_withdrawal_m3" unit="m³" />
          <Inp label="Species Affected" field="species_affected" unit="count" />
          <Inp label="Pollution Incidents" field="pollution_incidents" unit="count" />
        </div>
        <button
          onClick={runAssess}
          disabled={loading}
          className="mt-4 px-4 py-2 bg-black text-white text-xs font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Calculating…' : 'Calculate Nature Footprint'}
        </button>
      </Section>

      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <KpiCard
              label="Nature Footprint Score"
              value={result.nature_footprint_score}
              sub="0–100 (higher = worse)"
              color={result.nature_footprint_score >= 65 ? 'text-red-600' : result.nature_footprint_score >= 40 ? 'text-amber-600' : 'text-emerald-600'}
            />
            <KpiCard
              label="Dependency Score"
              value={result.dependency_score}
              sub="ENCORE-derived"
              color="text-gray-900"
            />
            <KpiCard
              label="Water Intensity"
              value={`${result.water_intensity} m³/ha`}
              sub="Withdrawal per land unit"
              color="text-blue-600"
            />
          </div>

          <Section title="Risk Flags">
            <div className="flex flex-wrap gap-3">
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${result.kba_exposure ? 'bg-red-50 border-red-200' : 'bg-emerald-50 border-emerald-200'}`}>
                <span className={`text-xs font-medium ${result.kba_exposure ? 'text-red-700' : 'text-emerald-700'}`}>
                  {result.kba_exposure ? 'KBA Exposure: FLAGGED' : 'KBA Exposure: Clear'}
                </span>
              </div>
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${result.species_risk_flag ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}`}>
                <span className={`text-xs font-medium ${result.species_risk_flag ? 'text-amber-700' : 'text-emerald-700'}`}>
                  {result.species_risk_flag ? 'Species Risk: Elevated' : 'Species Risk: Low'}
                </span>
              </div>
            </div>
            <p className="text-[10px] text-gray-400 mt-3">
              KBA = Key Biodiversity Area per IUCN/BirdLife standards. Flags trigger additional TNFD disclosure requirements per Recommendation 3.
            </p>
          </Section>
        </div>
      )}
    </div>
  );
}

/* ── Tab 5: Double Materiality ──────────────────────────────────────────── */
function DoubleMaterialityPanel() {
  const [data, setData] = useState(DM_TOPICS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API}/api/v1/tnfd/double-materiality`)
      .then(res => { if (res.data?.topics) setData(res.data.topics); })
      .catch(() => {});
    setLoading(false);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const materialTopics = data.filter(d => d.impact >= 60 || d.financial >= 60);

  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    const material = payload.impact >= 60 || payload.financial >= 60;
    return (
      <g>
        <circle cx={cx} cy={cy} r={material ? 7 : 5}
          fill={material ? '#10b981' : '#9ca3af'}
          fillOpacity={0.8}
          stroke={material ? '#059669' : '#6b7280'}
          strokeWidth={1}
        />
      </g>
    );
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div style={TOOLTIP_STYLE} className="px-3 py-2 rounded text-xs shadow-sm">
        <p className="font-semibold text-gray-800 mb-1">{d.topic}</p>
        <p className="text-gray-600">Impact materiality: <span className="font-mono font-semibold">{d.impact}</span></p>
        <p className="text-gray-600">Financial materiality: <span className="font-mono font-semibold">{d.financial}</span></p>
        <p className={`mt-1 font-medium ${(d.impact >= 60 || d.financial >= 60) ? 'text-emerald-600' : 'text-gray-400'}`}>
          {(d.impact >= 60 || d.financial >= 60) ? 'Material' : 'Not Material'}
        </p>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <KpiCard label="Material Topics" value={materialTopics.length} sub="Impact or financial material" color="text-emerald-600" />
        <KpiCard label="Dual Material" value={data.filter(d => d.impact >= 60 && d.financial >= 60).length} sub="Both dimensions material" color="text-gray-900" />
        <KpiCard label="Total Topics" value={data.length} sub="TNFD nature topics screened" color="text-gray-500" />
      </div>

      <Section title="Double Materiality Matrix — Impact vs Financial Materiality">
        <div className="relative">
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart margin={{ top: 16, right: 32, bottom: 32, left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
              <XAxis type="number" dataKey="impact" name="Impact Materiality" domain={[0, 100]}
                tick={{ fontSize: 10 }} label={{ value: 'Impact Materiality →', position: 'insideBottom', offset: -12, fontSize: 10, fill: '#9ca3af' }} />
              <YAxis type="number" dataKey="financial" name="Financial Materiality" domain={[0, 100]}
                tick={{ fontSize: 10 }} label={{ value: 'Financial Materiality →', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10, fill: '#9ca3af' }} />
              <Tooltip content={<CustomTooltip />} />
              <Scatter data={data} shape={<CustomDot />} />
            </ScatterChart>
          </ResponsiveContainer>
          {/* Quadrant labels */}
          <div className="absolute top-4 right-10 text-[9px] text-gray-400 font-medium">High Financial</div>
          <div className="absolute bottom-10 left-6 text-[9px] text-gray-400 font-medium">Low Both</div>
        </div>
        <div className="flex gap-4 text-[10px] mt-2">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />Material (impact ≥60 or financial ≥60)</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-gray-400 inline-block" />Not material</span>
        </div>
      </Section>

      <Section title="Material Nature Topics">
        <div className="space-y-1.5">
          {materialTopics.map((d, i) => (
            <div key={i} className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-emerald-50/60 border border-emerald-100">
              <span className="text-xs font-medium text-gray-800">{d.topic}</span>
              <div className="flex gap-3 text-[10px] font-mono">
                <span className="text-gray-500">Impact: <span className="font-semibold text-gray-800">{d.impact}</span></span>
                <span className="text-gray-500">Financial: <span className="font-semibold text-gray-800">{d.financial}</span></span>
              </div>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-gray-400 mt-3">
          Threshold: score ≥ 60 on either dimension triggers material classification per TNFD double materiality guidance (EFRAG-aligned).
        </p>
      </Section>
    </div>
  );
}

/* ── TABS config ────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'leap',     label: 'LEAP Assessment' },
  { id: 'disclosures', label: '14 Disclosures' },
  { id: 'encore',   label: 'ENCORE Dependencies' },
  { id: 'metrics',  label: 'Nature Impact Metrics' },
  { id: 'dm',       label: 'Double Materiality' },
];

/* ── Root component ─────────────────────────────────────────────────────── */
export default function TNFDPage() {
  const [tab, setTab] = useState('leap');
  const seed = useMemo(() => genSeedData(), []);

  const allDisclosures = PILLARS.flatMap(p => p.disclosures);
  const reportedCount = allDisclosures.filter(d => d.status === 'reported').length;
  const materialTopics = DM_TOPICS.filter(d => d.impact >= 60 || d.financial >= 60).length;

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo entity — TNFD v1.0 LEAP assessment with ENCORE ecosystem service dependency scoring and seed fallback data." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">TNFD Nature Assessment</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            TNFD v1.0 · LEAP Framework · 14 Core Disclosures · ENCORE Dependencies · Double Materiality
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['TNFD v1.0', 'LEAP', 'ENCORE', 'GBF', 'ESRS E4'].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

      {/* Top KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard
          label="LEAP Progress"
          value={`${Math.round(
            LEAP_PHASES.reduce((sum, ph) =>
              sum + Math.round((ph.steps.filter(s => seed.checked[s.id]).length / ph.steps.length) * 100), 0
            ) / LEAP_PHASES.length
          )}%`}
          sub="4-phase LEAP completion"
          color="text-emerald-600"
        />
        <KpiCard
          label="Disclosures Reported"
          value={`${reportedCount}/14`}
          sub="TNFD core disclosures"
          color="text-gray-900"
        />
        <KpiCard
          label="Material Nature Topics"
          value={materialTopics}
          sub="Impact or financial material"
          color="text-amber-600"
        />
        <KpiCard
          label="KBA Exposure"
          value="Flagged"
          sub="Key biodiversity area risk"
          color="text-red-600"
        />
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

      {tab === 'leap'         && <LeapAssessment seedChecked={seed.checked} />}
      {tab === 'disclosures'  && <DisclosuresPanel />}
      {tab === 'encore'       && <ENCOREPanel seedScores={seed.encoreScores} />}
      {tab === 'metrics'      && <NatureMetricsPanel />}
      {tab === 'dm'           && <DoubleMaterialityPanel />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Regulatory basis:</span> TNFD Recommendations v1.0 (Sept 2023) · ENCORE v3.0 (UNEP-WCMC) · Global Biodiversity Framework (Kunming-Montreal) · ESRS E4 Biodiversity & Ecosystems · EU Taxonomy DNSH criteria</p>
        <p><span className="font-semibold text-gray-500">Disclosure pillars:</span> Governance (D1-D2) · Strategy (D3-D6) · Risk Management (D7-D10) · Metrics & Targets (D11-D14) · KBA = Key Biodiversity Area (IUCN Red List)</p>
      </div>
    </div>
  );
}
