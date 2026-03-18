/**
 * PCAFQualityPage.jsx
 * Route: /pcaf-quality
 *
 * PCAF Data Quality Score — DQS Calculator & Portfolio Analytics
 *
 * Tab 1 — DQS Calculator      POST /api/v1/pcaf-quality/dqs/calculate
 * Tab 2 — Portfolio DQS        POST /api/v1/pcaf-quality/portfolio/dqs
 * Tab 3 — SFDR PAI Coverage    POST /api/v1/pcaf-quality/sfdr-pai-coverage
 * Tab 4 — Confidence Bands     GET  /api/v1/pcaf-quality/confidence-bands
 * Tab 5 — Improvement Roadmap  GET  /api/v1/pcaf-quality/improvement-roadmap
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell,
  BarChart, Bar,
  ResponsiveContainer, ReferenceLine,
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

function Inp({ label, type = 'number', value, onChange }) {
  return (
    <div>
      <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(type === 'number' ? Number(e.target.value) : e.target.value)}
        className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
      />
    </div>
  );
}

function Sel({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
      >
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

/* ── DQS badge colour ───────────────────────────────────────────────────── */
function dqsColor(score) {
  if (score === 1) return 'text-emerald-600';
  if (score === 2) return 'text-green-600';
  if (score === 3) return 'text-amber-600';
  if (score === 4) return 'text-orange-600';
  return 'text-red-600';
}

function dqsBadgeColor(score) {
  if (score <= 2) return 'green';
  if (score === 3) return 'amber';
  return 'red';
}

const DQS_PIE_COLORS = ['#10b981', '#34d399', '#f59e0b', '#f97316', '#ef4444'];

/* ── Asset class config ─────────────────────────────────────────────────── */
const ASSET_CLASSES = [
  { id: 'listed_equity',   label: 'Listed Equity' },
  { id: 'corp_bonds',      label: 'Corporate Bonds' },
  { id: 'business_loans',  label: 'Business Loans' },
  { id: 'project_finance', label: 'Project Finance' },
  { id: 'commercial_re',   label: 'Commercial RE' },
  { id: 'mortgages',       label: 'Mortgages' },
];

const ASSET_CLASS_FIELDS = {
  listed_equity:   [
    { key: 'revenue_eur',             label: 'Annual Revenue (€)',    def: 50000000 },
    { key: 'enterprise_value_eur',    label: 'Enterprise Value (€)',  def: 120000000 },
    { key: 'financed_value_eur',      label: 'Financed Value (€)',    def: 8000000 },
    { key: 'pcaf_data_tier',          label: 'PCAF Data Tier (1–5)',  def: 3 },
  ],
  corp_bonds:     [
    { key: 'outstanding_amount_eur',  label: 'Outstanding Amount (€)', def: 25000000 },
    { key: 'total_equity_debt_eur',   label: 'Total Equity + Debt (€)', def: 80000000 },
    { key: 'scope1_tco2e',            label: 'Scope 1 Emissions (tCO₂e)', def: 12400 },
    { key: 'pcaf_data_tier',          label: 'PCAF Data Tier (1–5)',   def: 3 },
  ],
  business_loans: [
    { key: 'outstanding_amount_eur',  label: 'Loan Outstanding (€)',  def: 5000000 },
    { key: 'total_equity_debt_eur',   label: 'Total Equity + Debt (€)', def: 18000000 },
    { key: 'revenue_eur',             label: 'Annual Revenue (€)',    def: 9000000 },
    { key: 'pcaf_data_tier',          label: 'PCAF Data Tier (1–5)',  def: 4 },
  ],
  project_finance: [
    { key: 'loan_amount_eur',         label: 'Loan Amount (€)',       def: 45000000 },
    { key: 'total_project_value_eur', label: 'Total Project Value (€)', def: 120000000 },
    { key: 'annual_emissions_tco2e',  label: 'Annual Emissions (tCO₂e)', def: 28000 },
    { key: 'pcaf_data_tier',          label: 'PCAF Data Tier (1–5)',  def: 2 },
  ],
  commercial_re:  [
    { key: 'outstanding_mortgage_eur', label: 'Outstanding Mortgage (€)', def: 12000000 },
    { key: 'property_value_eur',       label: 'Property Value (€)',     def: 20000000 },
    { key: 'floor_area_m2',            label: 'Floor Area (m²)',         def: 4500 },
    { key: 'pcaf_data_tier',           label: 'PCAF Data Tier (1–5)',   def: 3 },
  ],
  mortgages:      [
    { key: 'outstanding_mortgage_eur', label: 'Outstanding Mortgage (€)', def: 220000 },
    { key: 'property_value_eur',       label: 'Property Value (€)',     def: 380000 },
    { key: 'energy_class',             label: 'EPC Energy Class (A–G)', def: 'C', type: 'text' },
    { key: 'pcaf_data_tier',           label: 'PCAF Data Tier (1–5)',   def: 4 },
  ],
};

/* ── PAI indicators ─────────────────────────────────────────────────────── */
const PAI_INDICATORS = [
  { id: 'PAI-1',  name: 'GHG emissions (Scope 1+2+3)', category: 'Climate', minDqs: 2 },
  { id: 'PAI-2',  name: 'Carbon footprint (tCO₂e/€M)', category: 'Climate', minDqs: 3 },
  { id: 'PAI-3',  name: 'GHG intensity of investee companies', category: 'Climate', minDqs: 3 },
  { id: 'PAI-4',  name: 'Exposure to fossil fuel sector', category: 'Social', minDqs: 4 },
  { id: 'PAI-5',  name: 'Share of non-renewable energy consumption', category: 'Climate', minDqs: 3 },
  { id: 'PAI-6',  name: 'Energy consumption intensity by sector', category: 'Climate', minDqs: 3 },
  { id: 'PAI-7',  name: 'Activities negatively affecting biodiversity', category: 'Biodiversity', minDqs: 2 },
  { id: 'PAI-8',  name: 'Emissions to water', category: 'Water', minDqs: 3 },
  { id: 'PAI-9',  name: 'Hazardous waste ratio', category: 'Waste', minDqs: 3 },
  { id: 'PAI-10', name: 'Violations of UN Global Compact principles', category: 'Social', minDqs: 4 },
  { id: 'PAI-11', name: 'Lack of processes on UNGC/OECD monitoring', category: 'Social', minDqs: 4 },
  { id: 'PAI-12', name: 'Unadjusted gender pay gap', category: 'Social', minDqs: 4 },
  { id: 'PAI-13', name: 'Board gender diversity', category: 'Governance', minDqs: 4 },
  { id: 'PAI-14', name: 'Exposure to controversial weapons', category: 'Social', minDqs: 5 },
];

/* ── Seed data ──────────────────────────────────────────────────────────── */
function genSeedData() {
  const rng = mkRng(55);
  const portfolio = [
    { name: 'TechCorp A', class: 'Listed Equity',   value: 12500000, dqs: 2 },
    { name: 'EnergyBond B', class: 'Corporate Bonds', value: 8000000,  dqs: 3 },
    { name: 'SME Loan C',  class: 'Business Loans',  value: 3200000,  dqs: 4 },
    { name: 'Solar Farm D', class: 'Project Finance', value: 22000000, dqs: 1 },
    { name: 'Retail Park E', class: 'Commercial RE', value: 15000000, dqs: 3 },
    { name: 'Mortgage Pool F', class: 'Mortgages',   value: 4800000,  dqs: 4 },
    { name: 'IndustrialBond G', class: 'Corporate Bonds', value: 6500000, dqs: 3 },
    { name: 'SME Loan H',  class: 'Business Loans',  value: 1800000,  dqs: 5 },
  ];
  const totalValue = portfolio.reduce((s, a) => s + a.value, 0);
  const weightedDqs = portfolio.reduce((s, a) => s + a.dqs * a.value, 0) / totalValue;

  const confidenceBands = [1, 2, 3, 4, 5].map(dqs => ({
    dqs,
    p68_low:  Math.round(100 - dqs * 8 + rng() * 4),
    p68_high: Math.round(100 + dqs * 12 + rng() * 6),
    p95_low:  Math.round(100 - dqs * 16 + rng() * 6),
    p95_high: Math.round(100 + dqs * 22 + rng() * 8),
    p99_low:  Math.round(100 - dqs * 24 + rng() * 8),
    p99_high: Math.round(100 + dqs * 34 + rng() * 10),
  }));

  const dqsDist = [
    { name: 'DQS 1', value: portfolio.filter(a => a.dqs === 1).reduce((s, a) => s + a.value, 0), dqs: 1 },
    { name: 'DQS 2', value: portfolio.filter(a => a.dqs === 2).reduce((s, a) => s + a.value, 0), dqs: 2 },
    { name: 'DQS 3', value: portfolio.filter(a => a.dqs === 3).reduce((s, a) => s + a.value, 0), dqs: 3 },
    { name: 'DQS 4', value: portfolio.filter(a => a.dqs === 4).reduce((s, a) => s + a.value, 0), dqs: 4 },
    { name: 'DQS 5', value: portfolio.filter(a => a.dqs === 5).reduce((s, a) => s + a.value, 0), dqs: 5 },
  ].filter(d => d.value > 0);

  return { portfolio, weightedDqs: weightedDqs.toFixed(2), confidenceBands, dqsDist };
}

/* ── Tab 1: DQS Calculator ──────────────────────────────────────────────── */
function DQSCalculator() {
  const [assetClass, setAssetClass] = useState('listed_equity');
  const [fields, setFields] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const currentFields = ASSET_CLASS_FIELDS[assetClass] || [];

  useEffect(() => {
    const defaults = {};
    currentFields.forEach(f => { defaults[f.key] = f.def; });
    setFields(defaults);
    setResult(null);
  }, [assetClass]); // eslint-disable-line react-hooks/exhaustive-deps

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/pcaf-quality/dqs/calculate`, { asset_class: assetClass, ...fields });
      setResult(res.data);
    } catch {
      const tier = fields.pcaf_data_tier || 3;
      const rng = mkRng(tier * 13 + assetClass.charCodeAt(0));
      const dqs = Math.min(5, Math.max(1, Math.round(tier + (rng() - 0.5))));
      setResult({
        dqs_score: dqs,
        confidence_band_low:  Math.round(80 - dqs * 10 + rng() * 15),
        confidence_band_high: Math.round(120 + dqs * 15 + rng() * 20),
        data_quality_label: ['Verified primary', 'Primary reported', 'Proxy/modelled', 'Estimated sector average', 'Emissions factor fallback'][dqs - 1],
        financed_emissions_tco2e: Math.round(500 + rng() * 15000),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Section title="Asset Class & Inputs">
        <div className="mb-4">
          <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
            {ASSET_CLASSES.map(ac => (
              <button key={ac.id} onClick={() => setAssetClass(ac.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  assetClass === ac.id ? 'bg-white text-gray-900 shadow-sm border border-gray-200' : 'text-gray-500 hover:text-gray-700'
                }`}>
                {ac.label}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {currentFields.map(f => (
            <Inp
              key={f.key}
              label={f.label}
              type={f.type || 'number'}
              value={fields[f.key] ?? f.def}
              onChange={v => setFields(prev => ({ ...prev, [f.key]: v }))}
            />
          ))}
        </div>
        <button
          onClick={calculate}
          disabled={loading}
          className="mt-4 px-4 py-2 bg-black text-white text-xs font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Calculating…' : 'Calculate DQS'}
        </button>
      </Section>

      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-white border border-gray-200 rounded-lg p-3 col-span-2 sm:col-span-1">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">DQS Score</p>
              <p className={`text-4xl font-bold font-mono ${dqsColor(result.dqs_score)}`}>{result.dqs_score}</p>
              <p className="text-[10px] text-gray-400 mt-1">(1 = best, 5 = worst)</p>
            </div>
            <KpiCard label="Confidence Band" value={`${result.confidence_band_low}–${result.confidence_band_high}%`}
              sub="of point estimate" color="text-gray-900" />
            <KpiCard label="Data Quality Level" value={result.data_quality_label} sub="PCAF Tier assessment" />
            <KpiCard label="Financed Emissions" value={`${(result.financed_emissions_tco2e / 1000).toFixed(1)} ktCO₂e`}
              sub="Attribution point estimate" color="text-gray-700" />
          </div>

          <Section title="DQS Score Interpretation">
            <div className="space-y-2">
              {[
                { dqs: 1, label: 'Verified primary data — highest confidence', desc: 'Third-party verified Scope 1+2+3 data from company reports' },
                { dqs: 2, label: 'Primary reported data — high confidence',    desc: 'Company-reported emissions without third-party verification' },
                { dqs: 3, label: 'Proxy / modelled data — moderate',           desc: 'Revenue- or sector-based proxy emissions model' },
                { dqs: 4, label: 'Sector average — lower confidence',          desc: 'NACE sector average emission intensity applied to revenue' },
                { dqs: 5, label: 'Emission factor fallback — lowest',          desc: 'Generic emission factor without company-specific data' },
              ].map(row => (
                <div key={row.dqs} className={`flex items-center gap-3 p-2.5 rounded-lg border ${
                  row.dqs === result.dqs_score ? 'border-black bg-gray-50 shadow-sm' : 'border-gray-100 opacity-60'
                }`}>
                  <span className={`text-lg font-bold font-mono w-6 shrink-0 ${dqsColor(row.dqs)}`}>{row.dqs}</span>
                  <div>
                    <p className="text-xs font-medium text-gray-800">{row.label}</p>
                    <p className="text-[10px] text-gray-500">{row.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}

/* ── Tab 2: Portfolio DQS ───────────────────────────────────────────────── */
function PortfolioDQS({ seed }) {
  const [portfolio, setPortfolio] = useState(seed.portfolio);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const totalValue = portfolio.reduce((s, a) => s + a.value, 0);
  const weightedDqs = portfolio.reduce((s, a) => s + a.dqs * a.value, 0) / (totalValue || 1);

  const run = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/pcaf-quality/portfolio/dqs`, { assets: portfolio });
      setResult(res.data);
    } catch {
      setResult({ weighted_dqs: weightedDqs, distribution: seed.dqsDist });
    } finally {
      setLoading(false);
    }
  };

  const dist = result?.distribution || seed.dqsDist;
  const wDqs = result?.weighted_dqs || weightedDqs;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="bg-white border border-gray-200 rounded-lg p-3">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Portfolio DQS (weighted)</p>
          <p className={`text-3xl font-bold font-mono ${dqsColor(Math.round(wDqs))}`}>{Number(wDqs).toFixed(2)}</p>
          <p className="text-[10px] text-gray-400 mt-0.5">Value-weighted average</p>
        </div>
        <KpiCard label="Total Exposure" value={`€${(totalValue / 1e6).toFixed(1)}M`} sub={`${portfolio.length} assets`} />
        <KpiCard label="Data Quality" value={wDqs <= 2 ? 'High' : wDqs <= 3.5 ? 'Medium' : 'Low'}
          sub="PCAF global standard" color={wDqs <= 2 ? 'text-emerald-600' : wDqs <= 3.5 ? 'text-amber-600' : 'text-red-600'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Section title="Portfolio Table">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  {['Asset', 'Class', 'Value (€)', 'DQS'].map(h => (
                    <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolio.map((a, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-1.5 px-2 font-medium text-gray-700">{a.name}</td>
                    <td className="py-1.5 px-2 text-gray-500">{a.class}</td>
                    <td className="py-1.5 px-2 font-mono">{(a.value / 1e6).toFixed(2)}M</td>
                    <td className="py-1.5 px-2">
                      <span className={`font-mono font-bold ${dqsColor(a.dqs)}`}>{a.dqs}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            onClick={run}
            disabled={loading}
            className="mt-3 px-4 py-2 bg-black text-white text-xs font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Computing…' : 'Calculate Portfolio DQS'}
          </button>
        </Section>

        <Section title="DQS Distribution by Exposure">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={dist} dataKey="value" nameKey="name" cx="50%" cy="50%"
                outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false} fontSize={10}>
                {dist.map((d, i) => (
                  <Cell key={i} fill={DQS_PIE_COLORS[d.dqs - 1] || '#9ca3af'} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`€${(v / 1e6).toFixed(2)}M`, 'Exposure']} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 justify-center mt-2">
            {[1, 2, 3, 4, 5].map(d => (
              <span key={d} className="flex items-center gap-1 text-[10px]">
                <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: DQS_PIE_COLORS[d - 1] }} />
                DQS {d}
              </span>
            ))}
          </div>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 3: SFDR PAI Coverage ───────────────────────────────────────────── */
function SFDRPAICoverage() {
  const [currentDqs, setCurrentDqs] = useState(3);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const covered = PAI_INDICATORS.filter(p => p.minDqs >= currentDqs);
  const coveragePct = Math.round((covered.length / PAI_INDICATORS.length) * 100);

  const run = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/pcaf-quality/sfdr-pai-coverage`, { current_dqs: currentDqs });
      setResult(res.data);
    } catch {
      setResult({ coverage_pct: coveragePct, covered_count: covered.length });
    } finally {
      setLoading(false);
    }
  };

  const pct = result?.coverage_pct ?? coveragePct;

  return (
    <div className="space-y-4">
      <Section title="Current Portfolio DQS Level">
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">Portfolio DQS</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map(d => (
                <button key={d} onClick={() => { setCurrentDqs(d); setResult(null); }}
                  className={`w-10 h-10 rounded-lg text-sm font-bold font-mono border transition-all ${
                    currentDqs === d ? 'bg-black text-white border-black' : `border-gray-200 ${dqsColor(d)} hover:border-gray-400`
                  }`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600">PAI Coverage at DQS {currentDqs}</span>
              <span className="text-sm font-semibold font-mono">{pct}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
          <button
            onClick={run}
            disabled={loading}
            className="px-4 py-2 bg-black text-white text-xs font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Checking…' : 'Check Coverage'}
          </button>
        </div>
      </Section>

      <Section title="PAI Indicators Coverage">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['PAI', 'Indicator', 'Category', 'Min. DQS Required', 'Status'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PAI_INDICATORS.map(p => {
              const isCovered = p.minDqs >= currentDqs;
              return (
                <tr key={p.id} className={`border-b border-gray-100 hover:bg-gray-50 ${!isCovered ? 'opacity-50' : ''}`}>
                  <td className="py-1.5 px-2 font-mono text-gray-500">{p.id}</td>
                  <td className="py-1.5 px-2 text-gray-700">{p.name}</td>
                  <td className="py-1.5 px-2">
                    <Badge label={p.category} color="gray" />
                  </td>
                  <td className="py-1.5 px-2 font-mono font-semibold">
                    <span className={dqsColor(p.minDqs)}>{p.minDqs}</span>
                  </td>
                  <td className="py-1.5 px-2">
                    <Badge label={isCovered ? 'Covered' : 'Gap'} color={isCovered ? 'green' : 'red'} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="text-[10px] text-gray-400 mt-3">
          Coverage = PAI indicators where current DQS ≤ minimum required DQS for that indicator. SFDR RTS Annex I mandatory indicators require DQS 1–3.
        </p>
      </Section>
    </div>
  );
}

/* ── Tab 4: Confidence Bands ────────────────────────────────────────────── */
function ConfidenceBands({ seed }) {
  const [data, setData] = useState(seed.confidenceBands);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    axios.get(`${API}/api/v1/pcaf-quality/confidence-bands`)
      .then(res => { if (res.data?.bands) setData(res.data.bands); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const chartData = data.map(d => ({
    dqs: `DQS ${d.dqs}`,
    p68_range: d.p68_high - d.p68_low,
    p95_range: d.p95_high - d.p95_low,
    p99_range: d.p99_high - d.p99_low,
    p68_low: d.p68_low, p95_low: d.p95_low, p99_low: d.p99_low,
  }));

  return (
    <div className="space-y-4">
      <Section title="Financed Emissions Confidence Intervals by DQS Score">
        <p className="text-xs text-gray-500 mb-4">
          Uncertainty range of financed emissions estimate as % of point estimate. Tighter intervals indicate higher data quality.
        </p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="dqs" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit="%" label={{ value: 'Uncertainty range (%)', angle: -90, position: 'insideLeft', offset: 0, fontSize: 9, fill: '#9ca3af' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v}%`, 'Range']} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="p68_range" name="68% CI range" fill="#10b981" radius={[3, 3, 0, 0]} opacity={0.9} />
            <Bar dataKey="p95_range" name="95% CI range" fill="#f59e0b" radius={[3, 3, 0, 0]} opacity={0.8} />
            <Bar dataKey="p99_range" name="99% CI range" fill="#ef4444" radius={[3, 3, 0, 0]} opacity={0.7} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Confidence Interval Detail Table">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['DQS', '68% CI (±%)', '95% CI (±%)', '99% CI (±%)', 'Confidence Level'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map(d => (
              <tr key={d.dqs} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2"><span className={`font-mono font-bold ${dqsColor(d.dqs)}`}>DQS {d.dqs}</span></td>
                <td className="py-1.5 px-2 font-mono text-gray-700">±{Math.round((d.p68_high - d.p68_low) / 2)}%</td>
                <td className="py-1.5 px-2 font-mono text-gray-700">±{Math.round((d.p95_high - d.p95_low) / 2)}%</td>
                <td className="py-1.5 px-2 font-mono text-gray-700">±{Math.round((d.p99_high - d.p99_low) / 2)}%</td>
                <td className="py-1.5 px-2">
                  <Badge label={d.dqs <= 2 ? 'High' : d.dqs === 3 ? 'Medium' : 'Low'} color={d.dqs <= 2 ? 'green' : d.dqs === 3 ? 'amber' : 'red'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[10px] text-gray-400 mt-3">
          Confidence bands follow PCAF Global Standard v2 (2022) uncertainty methodology. DQS 1 = verified primary data (&lt;5% uncertainty at 68% CI).
        </p>
      </Section>
    </div>
  );
}

/* ── Tab 5: Improvement Roadmap ─────────────────────────────────────────── */
const ROADMAP_STEPS = [
  {
    step: 1,
    fromDqs: 5,
    toDqs: 4,
    title: 'Apply Sector Emission Factors',
    description: 'Replace generic defaults with NACE sector-specific emission intensity factors from EPA, DEFRA, or GHG Protocol sector guidance.',
    actions: [
      'Map all counterparties to NACE sector codes',
      'Source NACE-level emission intensity from EPA/DEFRA',
      'Apply to revenue-based attribution model',
      'Document data sources in DQS registry',
    ],
    effort: 'Low',
    impact: 'DQS 5→4',
  },
  {
    step: 2,
    fromDqs: 4,
    toDqs: 3,
    title: 'Integrate Physical Activity Data',
    description: 'Use company-level physical activity data (kWh consumption, tonne-km, building m²) instead of revenue proxies.',
    actions: [
      'Request energy consumption data from top 20 borrowers',
      'Implement building EPC data integration for RE portfolio',
      'Source fleet data for transport exposures',
      'Validate against PCAF Tier 2 criteria',
    ],
    effort: 'Medium',
    impact: 'DQS 4→3',
  },
  {
    step: 3,
    fromDqs: 3,
    toDqs: 2,
    title: 'Collect Reported Scope 1+2 Emissions',
    description: 'Obtain company-reported Scope 1 and Scope 2 (location-based) GHG emissions from annual reports, CDP, or direct engagement.',
    actions: [
      'Enrol in CDP data partnership for counterparty disclosures',
      'Implement automated scraping from sustainability reports',
      'Engage top 50 counterparties directly for emissions data',
      'Establish Scope 3 methodology for material categories',
    ],
    effort: 'High',
    impact: 'DQS 3→2',
  },
  {
    step: 4,
    fromDqs: 2,
    toDqs: 1,
    title: 'Third-Party Verification',
    description: 'Arrange external assurance of reported emissions data to ISAE 3000/ISO 14064-3 standards.',
    actions: [
      'Commission limited assurance from accredited verifier',
      'Align with ISSA 5000 criteria for reasonable assurance',
      'Implement continuous monitoring via API data feeds',
      'Achieve CDP A-list reporting alignment',
    ],
    effort: 'Very High',
    impact: 'DQS 2→1',
  },
  {
    step: 5,
    fromDqs: 1,
    toDqs: 1,
    title: 'Maintain & Automate',
    description: 'Sustain DQS 1 through automation, real-time data pipelines, and continuous verification processes.',
    actions: [
      'Deploy automated ESG data ingestion pipelines',
      'Integrate with Science Based Targets initiative tracking',
      'Establish annual re-verification schedule',
      'Publish TCFD-aligned financed emissions report',
    ],
    effort: 'Ongoing',
    impact: 'Maintain DQS 1',
  },
];

function ImprovementRoadmap() {
  const [data, setData] = useState(ROADMAP_STEPS);
  const [currentDqs, setCurrentDqs] = useState(3);
  const [targetDqs, setTargetDqs] = useState(1);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    axios.get(`${API}/api/v1/pcaf-quality/improvement-roadmap`, { params: { current_dqs: currentDqs, target_dqs: targetDqs } })
      .then(res => { if (res.data?.steps) setData(res.data.steps); })
      .catch(() => {});
  }, [currentDqs, targetDqs]);

  const relevantSteps = ROADMAP_STEPS.filter(s => s.fromDqs <= currentDqs && s.toDqs >= targetDqs && s.step <= (currentDqs - targetDqs + 1));
  const stepsToShow = relevantSteps.length > 0 ? relevantSteps : ROADMAP_STEPS.slice(0, currentDqs - targetDqs + 1 || 1);

  const EFFORT_COLOR = { Low: 'green', Medium: 'amber', High: 'red', 'Very High': 'red', Ongoing: 'blue' };

  return (
    <div className="space-y-4">
      <Section title="DQS Improvement Path">
        <div className="flex items-center gap-6 flex-wrap">
          <div>
            <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">Current DQS</label>
            <div className="flex gap-2">
              {[2, 3, 4, 5].map(d => (
                <button key={d} onClick={() => setCurrentDqs(d)}
                  className={`w-9 h-9 rounded-lg text-xs font-bold font-mono border transition-all ${
                    currentDqs === d ? 'bg-black text-white border-black' : `border-gray-200 ${dqsColor(d)} hover:border-gray-400`
                  }`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div className="text-2xl text-gray-300">→</div>
          <div>
            <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">Target DQS</label>
            <div className="flex gap-2">
              {[1, 2, 3].map(d => (
                <button key={d} onClick={() => setTargetDqs(Math.min(d, currentDqs - 1))}
                  className={`w-9 h-9 rounded-lg text-xs font-bold font-mono border transition-all ${
                    targetDqs === d ? 'bg-black text-white border-black' : `border-gray-200 ${dqsColor(d)} hover:border-gray-400`
                  }`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg px-4 py-2 border border-gray-200">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">Steps Required</p>
            <p className="text-lg font-bold font-mono text-gray-800">{Math.max(0, currentDqs - targetDqs)}</p>
          </div>
        </div>
      </Section>

      <div className="space-y-3">
        {ROADMAP_STEPS.slice(0, Math.max(0, currentDqs - targetDqs)).map((step, i) => (
          <div key={step.step}
            className={`bg-white border rounded-lg overflow-hidden transition-all ${
              expanded === step.step ? 'border-black shadow-sm' : 'border-gray-200'
            }`}>
            <button
              onClick={() => setExpanded(expanded === step.step ? null : step.step)}
              className="w-full flex items-center gap-4 px-4 py-3 hover:bg-gray-50 transition-colors"
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold font-mono shrink-0 ${
                i === 0 ? 'bg-emerald-100 text-emerald-700 border border-emerald-300' : 'bg-gray-100 text-gray-600 border border-gray-300'
              }`}>
                {i + 1}
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-medium text-gray-800">{step.title}</p>
                <p className="text-[10px] text-gray-500">{step.description.slice(0, 80)}…</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge label={step.impact} color={step.fromDqs > step.toDqs ? 'green' : 'blue'} />
                <Badge label={`Effort: ${step.effort}`} color={EFFORT_COLOR[step.effort] || 'gray'} />
              </div>
            </button>
            {expanded === step.step && (
              <div className="px-4 pb-4 border-t border-gray-100">
                <p className="text-xs text-gray-600 mb-3 mt-3">{step.description}</p>
                <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Action Items</p>
                <ul className="space-y-1.5">
                  {step.actions.map((action, j) => (
                    <li key={j} className="flex items-start gap-2 text-xs text-gray-700">
                      <span className="text-emerald-500 font-bold mt-0.5">✓</span>
                      {action}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        {currentDqs <= targetDqs && (
          <div className="text-center py-6 text-xs text-gray-400">
            Set current DQS higher than target DQS to see improvement steps.
          </div>
        )}
      </div>
    </div>
  );
}

/* ── TABS config ────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'dqs',      label: 'DQS Calculator' },
  { id: 'portfolio', label: 'Portfolio DQS' },
  { id: 'sfdr',     label: 'SFDR PAI Coverage' },
  { id: 'bands',    label: 'Confidence Bands' },
  { id: 'roadmap',  label: 'Improvement Roadmap' },
];

/* ── Root component ─────────────────────────────────────────────────────── */
export default function PCAFQualityPage() {
  const [tab, setTab] = useState('dqs');
  const seed = useMemo(() => genSeedData(), []);

  const totalValue = seed.portfolio.reduce((s, a) => s + a.value, 0);
  const wDqs = seed.portfolio.reduce((s, a) => s + a.dqs * a.value, 0) / totalValue;
  const coveragePct = Math.round((PAI_INDICATORS.filter(p => p.minDqs >= 3).length / PAI_INDICATORS.length) * 100);

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo portfolio — PCAF Global Standard v2 data quality scoring with SFDR PAI coverage analysis and seed fallback data." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">PCAF Data Quality Score</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            PCAF Global Standard v2 · DQS 1–5 · SFDR PAI Coverage · Confidence Bands · Improvement Roadmap
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['PCAF v2', 'DQS', 'SFDR PAI', 'Art. 4 RTS', 'GHG Protocol'].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

      {/* Top KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white border border-gray-200 rounded-lg p-3">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Portfolio DQS (weighted)</p>
          <p className={`text-xl font-semibold font-mono ${dqsColor(Math.round(wDqs))}`}>{Number(wDqs).toFixed(2)}</p>
          <p className="text-[10px] text-gray-500 mt-0.5">Value-weighted average</p>
        </div>
        <KpiCard
          label="Confidence Level"
          value={wDqs <= 2 ? 'High' : wDqs <= 3.5 ? 'Medium' : 'Low'}
          sub="At current DQS"
          color={wDqs <= 2 ? 'text-emerald-600' : wDqs <= 3.5 ? 'text-amber-600' : 'text-red-600'}
        />
        <KpiCard
          label="PAI Coverage"
          value={`${coveragePct}%`}
          sub="SFDR mandatory PAIs"
          color={coveragePct >= 80 ? 'text-emerald-600' : coveragePct >= 50 ? 'text-amber-600' : 'text-red-600'}
        />
        <KpiCard
          label="Data Completeness"
          value={`${Math.round(100 - (wDqs - 1) * 15)}%`}
          sub="Across asset classes"
          color="text-gray-900"
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

      {tab === 'dqs'       && <DQSCalculator />}
      {tab === 'portfolio' && <PortfolioDQS seed={seed} />}
      {tab === 'sfdr'      && <SFDRPAICoverage />}
      {tab === 'bands'     && <ConfidenceBands seed={seed} />}
      {tab === 'roadmap'   && <ImprovementRoadmap />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Regulatory basis:</span> PCAF Global GHG Accounting & Reporting Standard for the Financial Industry v2 (2022) · SFDR RTS (EU) 2022/1288 PAI indicators Annex I · GHG Protocol Corporate Standard</p>
        <p><span className="font-semibold text-gray-500">Asset classes:</span> Listed equity · Corporate bonds · Business loans · Project finance · Commercial RE · Mortgages · DQS 1 = verified primary data, DQS 5 = emission factor fallback</p>
      </div>
    </div>
  );
}
