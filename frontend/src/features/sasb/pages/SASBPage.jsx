/**
 * SASBPage.jsx
 * Route: /sasb-industry
 *
 * SASB Industry Standards (SICS)
 *
 * Tab 1 — Industry Metrics     POST /api/v1/sasb/industry-metrics
 * Tab 2 — Materiality Map      POST /api/v1/sasb/materiality-map
 * Tab 3 — Sector Overview      (seed data — 11 SICS sectors)
 * Tab 4 — ISSB S2 Mapping      POST /api/v1/sasb/issb-mapping
 * Tab 5 — Peer Comparison      POST /api/v1/sasb/peer-comparison
 */
import React, { useState, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
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

function Sel({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-gray-400 bg-white"
      >
        {options.map(o => <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>{typeof o === 'string' ? o : o.label}</option>)}
      </select>
    </div>
  );
}

function Btn({ children, onClick, loading }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="px-4 py-2 bg-black text-white text-xs font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors">
      {loading ? 'Loading…' : children}
    </button>
  );
}

/* ── SICS Taxonomy ──────────────────────────────────────────────────────── */
const SICS_SECTORS = [
  {
    sector: 'Extractives & Minerals Processing',
    color: '#ef4444',
    industries: ['Coal Operations', 'Construction Materials', 'Iron & Steel', 'Metals & Mining', 'Oil & Gas — Exploration', 'Oil & Gas — Midstream'],
  },
  {
    sector: 'Financials',
    color: '#3b82f6',
    industries: ['Asset Management & Custody', 'Commercial Banks', 'Consumer Finance', 'Insurance', 'Investment Banking & Brokerage', 'Mortgage Finance'],
  },
  {
    sector: 'Food & Beverage',
    color: '#f59e0b',
    industries: ['Agricultural Products', 'Alcoholic Beverages', 'Food Retailers', 'Meat, Poultry & Dairy', 'Non-Alcoholic Beverages', 'Processed Foods'],
  },
  {
    sector: 'Health Care',
    color: '#10b981',
    industries: ['Biotechnology', 'Drug Retailers', 'Health Care Delivery', 'Health Care Distributors', 'Managed Care', 'Medical Equipment'],
  },
  {
    sector: 'Infrastructure',
    color: '#8b5cf6',
    industries: ['Electric Utilities', 'Engineering & Construction', 'Gas Utilities', 'Home Builders', 'Real Estate', 'Waste Management'],
  },
  {
    sector: 'Resource Transformation',
    color: '#f97316',
    industries: ['Aerospace & Defence', 'Chemicals', 'Containers & Packaging', 'Electrical & Electronic Equipment', 'Industrial Machinery', 'Semiconductors'],
  },
  {
    sector: 'Services',
    color: '#64748b',
    industries: ['Advertising & Marketing', 'Casinos & Gaming', 'Hotels & Lodging', 'Leisure Facilities', 'Media & Entertainment', 'Professional Services'],
  },
  {
    sector: 'Technology & Communications',
    color: '#0ea5e9',
    industries: ['E-Commerce', 'Hardware', 'Internet Media', 'Semiconductors', 'Software & IT Services', 'Telecommunications'],
  },
  {
    sector: 'Transportation',
    color: '#a855f7',
    industries: ['Air Freight', 'Airlines', 'Auto Parts', 'Automobiles', 'Car Rental & Leasing', 'Marine Transportation'],
  },
  {
    sector: 'Consumer Goods',
    color: '#ec4899',
    industries: ['Apparel, Accessories & Footwear', 'Building Products & Furnishings', 'Household & Personal Products', 'Multiline & Specialty Retailers', 'Toys & Sporting Goods'],
  },
  {
    sector: 'Renewable Resources & Alt Energy',
    color: '#22c55e',
    industries: ['Biofuels', 'Forestry Management', 'Fuel Cells & Industrial Batteries', 'Pulp & Paper Products', 'Solar Energy', 'Wind Energy'],
  },
];

/* ── Industry metrics seed ──────────────────────────────────────────────── */
function genMetrics(industry) {
  const seed = industry.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  const rng = mkRng(seed);
  const ESG_CATS = ['Environmental', 'Social', 'Governance'];
  return Array.from({ length: 8 }, (_, i) => ({
    code: `${industry.slice(0, 3).toUpperCase()}-${String(i + 1).padStart(3, '0')}`,
    description: [
      'GHG Emissions — Scope 1 & 2', 'Total Energy Consumed', 'Water Withdrawal',
      'Percentage Recycled Input', 'Employee Safety (TRIR)', 'Gender Pay Ratio',
      'Board Independence %', 'Community Investment $', 'R&D Spend %', 'Revenue from Low-Carbon'
    ][i % 10],
    unit: ['tCO2e', 'GJ', 'm³', '%', 'per 200k hrs', 'ratio', '%', 'M USD', '%', '%'][i % 10],
    category: ESG_CATS[i % 3],
    status: rng() > 0.25 ? 'reported' : rng() > 0.5 ? 'partially' : 'not reported',
    materiality: Math.round(40 + rng() * 55),
  }));
}

/* ── ISSB mapping seed ──────────────────────────────────────────────────── */
const ISSB_MAP_SEED = [
  { sasb: 'EM-EP-110a.1', desc: 'GHG Emissions', ifrs: 'IFRS S2 §21(b)', esrs: 'ESRS E1-6', coverage: 'full' },
  { sasb: 'EM-EP-130a.1', desc: 'Water Management', ifrs: 'IFRS S2 §21(d)', esrs: 'ESRS E3-1', coverage: 'partial' },
  { sasb: 'EM-EP-140a.1', desc: 'Biodiversity Impacts', ifrs: 'IFRS S2 §21(d)', esrs: 'ESRS E4-1', coverage: 'partial' },
  { sasb: 'EM-EP-210a.1', desc: 'Reserves in Sensitive Areas', ifrs: 'IFRS S2 §16(b)', esrs: 'ESRS E4-4', coverage: 'partial' },
  { sasb: 'EM-EP-320a.1', desc: 'Workforce Health & Safety', ifrs: 'IFRS S2 n/a', esrs: 'ESRS S1-14', coverage: 'gap' },
  { sasb: 'FN-CB-410a.1', desc: 'Financed Emissions (Banks)', ifrs: 'IFRS S2 §29(f)', esrs: 'ESRS E1-6 §51', coverage: 'full' },
  { sasb: 'FN-IN-410a.1', desc: 'Insured Emissions', ifrs: 'IFRS S2 §29(g)', esrs: 'ESRS E1-6 §51', coverage: 'partial' },
  { sasb: 'IF-EU-110a.1', desc: 'GHG Emissions (Utilities)', ifrs: 'IFRS S2 §21(b)', esrs: 'ESRS E1-6', coverage: 'full' },
  { sasb: 'IF-EU-420a.1', desc: 'SAIDI / Grid Reliability', ifrs: 'IFRS S2 n/a', esrs: 'n/a', coverage: 'gap' },
  { sasb: 'TC-SI-130a.1', desc: 'Data Privacy (Tech)', ifrs: 'IFRS S2 n/a', esrs: 'ESRS S4-4', coverage: 'partial' },
];

/* ── Peer comparison seed ───────────────────────────────────────────────── */
const PEERS = ['Apex Energy Corp', 'Vertex Industries', 'Solara Group'];
function genPeerData(industry) {
  const seed = industry.split('').reduce((a, c) => a + c.charCodeAt(0), 0) + 42;
  const rng = mkRng(seed);
  const metrics = ['GHG Intensity', 'Energy Use', 'Water Use', 'TRIR', 'Board Diversity'];
  return metrics.map(m => ({
    metric: m,
    [PEERS[0]]: Math.round(40 + rng() * 50),
    [PEERS[1]]: Math.round(40 + rng() * 50),
    [PEERS[2]]: Math.round(40 + rng() * 50),
  }));
}

/* ── Tab 1: Industry Metrics ────────────────────────────────────────────── */
function IndustryMetrics() {
  const allIndustries = SICS_SECTORS.flatMap(s => s.industries.map(i => ({ value: i, label: `${i} (${s.sector})` })));
  const [industry, setIndustry] = useState('Electric Utilities');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const seed = useMemo(() => genMetrics('Electric Utilities'), []);
  const data = result || seed;

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/sasb/industry-metrics`, { industry });
      setResult(res.data?.metrics || genMetrics(industry));
    } catch { setResult(genMetrics(industry)); }
    finally { setLoading(false); }
  }

  const reported = data.filter(r => r.status === 'reported').length;

  return (
    <div className="space-y-4">
      <Section title="Select Industry">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="w-80">
            <Sel label="SICS Industry" value={industry} onChange={setIndustry} options={allIndustries} />
          </div>
          <Btn onClick={handleRun} loading={loading}>Load SASB Metrics</Btn>
        </div>
      </Section>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Industry Metrics" value={data.length} sub={`for ${industry.slice(0, 12)}…`} color="text-gray-900" />
        <KpiCard label="Reported" value={reported} sub={`${Math.round(reported/data.length*100)}% coverage`} color="text-emerald-600" />
        <KpiCard label="Material Topics" value="7" sub="ESG categories" color="text-blue-600" />
        <KpiCard label="Peer Rank" value="2nd" sub="in SICS sector" color="text-amber-600" />
      </div>

      <Section title={`SASB Metrics — ${industry}`}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Code', 'Description', 'Unit', 'Category', 'Materiality', 'Reporting Status'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 font-mono font-semibold text-gray-600 text-[10px]">{row.code}</td>
                <td className="py-1.5 px-2 text-gray-700">{row.description}</td>
                <td className="py-1.5 px-2 font-mono text-gray-500 text-[10px]">{row.unit}</td>
                <td className="py-1.5 px-2">
                  <Badge label={row.category}
                    color={row.category === 'Environmental' ? 'green' : row.category === 'Social' ? 'blue' : 'purple'} />
                </td>
                <td className="py-1.5 px-2">
                  <div className="flex items-center gap-1.5">
                    <div className="w-12 bg-gray-100 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-black" style={{ width: `${row.materiality}%` }} />
                    </div>
                    <span className="font-mono text-[10px]">{row.materiality}</span>
                  </div>
                </td>
                <td className="py-1.5 px-2">
                  <Badge label={row.status}
                    color={row.status === 'reported' ? 'green' : row.status === 'partially' ? 'amber' : 'red'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 2: Materiality Map ─────────────────────────────────────────────── */
function MaterialityMap() {
  const [industry, setIndustry] = useState('Electric Utilities');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const seedData = useMemo(() => {
    const metrics = genMetrics(industry);
    return ['Environmental', 'Social', 'Governance'].map(cat => ({
      category: cat,
      avgMateriality: Math.round(metrics.filter(m => m.category === cat).reduce((a, b) => a + b.materiality, 0) /
        Math.max(1, metrics.filter(m => m.category === cat).length)),
      count: metrics.filter(m => m.category === cat).length,
    }));
  }, [industry]);

  const data = result || seedData;

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/sasb/materiality-map`, { industry });
      setResult(res.data?.categories || null);
    } catch { setResult(seedData); }
    finally { setLoading(false); }
  }

  const metrics = genMetrics(industry);
  const chartData = metrics.map(m => ({ name: m.description.slice(0, 18), score: m.materiality, category: m.category }));

  const CAT_COLOR = { Environmental: '#10b981', Social: '#3b82f6', Governance: '#8b5cf6' };

  return (
    <div className="space-y-4">
      <Section title="Parameters">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="w-64">
            <Sel label="Industry" value={industry} onChange={setIndustry}
              options={SICS_SECTORS.flatMap(s => s.industries)} />
          </div>
          <Btn onClick={handleRun} loading={loading}>Generate Materiality Map</Btn>
        </div>
      </Section>

      <Section title="Metric Materiality by ESG Category — Horizontal Heatmap">
        <ResponsiveContainer width="100%" height={Math.max(200, chartData.length * 28)}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 40, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10 }} domain={[0, 100]} unit="%" />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 9 }} width={130} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, 'Materiality Score']} />
            <Bar dataKey="score" radius={[0, 3, 3, 0]}>
              {chartData.map((d, i) => (
                <Cell key={i} fill={CAT_COLOR[d.category] || '#6b7280'} fillOpacity={0.6 + d.score / 250} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Materiality Summary by Category">
        <div className="grid grid-cols-3 gap-3">
          {data.map((cat, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAT_COLOR[cat.category] }} />
                <span className="text-xs font-semibold text-gray-800">{cat.category}</span>
              </div>
              <p className="text-xl font-bold font-mono">{cat.avgMateriality}%</p>
              <p className="text-[10px] text-gray-500 mt-0.5">avg. materiality · {cat.count} metrics</p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 3: Sector Overview ─────────────────────────────────────────────── */
function SectorOverview() {
  const [expanded, setExpanded] = useState(null);

  return (
    <Section title="SICS Sector Overview — Click to Expand Industry List">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {SICS_SECTORS.map((s, i) => (
          <div key={i}
            className={`border rounded-lg overflow-hidden cursor-pointer transition-all hover:shadow-sm ${expanded === i ? 'border-gray-400' : 'border-gray-200'}`}
            onClick={() => setExpanded(expanded === i ? null : i)}>
            <div className="flex items-center gap-2.5 p-3" style={{ borderLeft: `3px solid ${s.color}` }}>
              <div>
                <p className="text-xs font-semibold text-gray-800">{s.sector}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">{s.industries.length} industries</p>
              </div>
              <div className="ml-auto text-gray-400 text-xs">{expanded === i ? '▲' : '▼'}</div>
            </div>
            {expanded === i && (
              <div className="border-t border-gray-100 p-2.5 bg-gray-50">
                <div className="space-y-1">
                  {s.industries.map((ind, j) => (
                    <div key={j} className="flex items-center gap-1.5">
                      <div className="w-1 h-1 rounded-full bg-gray-400" />
                      <span className="text-[11px] text-gray-700">{ind}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── Tab 4: ISSB S2 Mapping ─────────────────────────────────────────────── */
function ISSBMapping() {
  const [industry, setIndustry] = useState('Electric Utilities');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const data = result || ISSB_MAP_SEED;

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/sasb/issb-mapping`, { industry });
      setResult(res.data?.mappings || null);
    } catch { setResult(ISSB_MAP_SEED); }
    finally { setLoading(false); }
  }

  const fullCoverage = data.filter(r => r.coverage === 'full').length;
  const coveragePct = Math.round(fullCoverage / data.length * 100);

  return (
    <div className="space-y-4">
      <Section title="Parameters">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="w-64">
            <Sel label="Industry" value={industry} onChange={setIndustry}
              options={SICS_SECTORS.flatMap(s => s.industries)} />
          </div>
          <Btn onClick={handleRun} loading={loading}>Load ISSB S2 Mapping</Btn>
        </div>
      </Section>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="ISSB S2 Coverage" value={`${coveragePct}%`} sub="full coverage metrics"
          color={coveragePct >= 70 ? 'text-emerald-600' : coveragePct >= 50 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Full Coverage" value={fullCoverage} sub={`of ${data.length} mapped`} color="text-emerald-600" />
        <KpiCard label="Partial" value={data.filter(r => r.coverage === 'partial').length} sub="partial overlap" color="text-amber-600" />
        <KpiCard label="Gaps" value={data.filter(r => r.coverage === 'gap').length} sub="SASB not in IFRS S2" color="text-red-600" />
      </div>

      <Section title="SASB Metric → IFRS S2 Requirement → ESRS Cross-Reference">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['SASB Metric', 'Description', 'IFRS S2 Reference', 'ESRS Reference', 'Coverage'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${row.coverage === 'gap' ? 'bg-red-50/30' : row.coverage === 'partial' ? 'bg-amber-50/20' : ''}`}>
                <td className="py-1.5 px-2 font-mono text-[10px] font-semibold text-gray-600">{row.sasb}</td>
                <td className="py-1.5 px-2 text-gray-700">{row.desc}</td>
                <td className="py-1.5 px-2 font-mono text-[10px] text-gray-500">{row.ifrs}</td>
                <td className="py-1.5 px-2 font-mono text-[10px] text-gray-500">{row.esrs}</td>
                <td className="py-1.5 px-2">
                  <Badge label={row.coverage}
                    color={row.coverage === 'full' ? 'green' : row.coverage === 'partial' ? 'amber' : 'red'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 5: Peer Comparison ─────────────────────────────────────────────── */
function PeerComparison() {
  const [industry, setIndustry] = useState('Electric Utilities');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const seedData = useMemo(() => genPeerData('Electric Utilities'), []);
  const data = result || seedData;

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/sasb/peer-comparison`, { industry, peers: PEERS });
      setResult(res.data?.comparison || genPeerData(industry));
    } catch { setResult(genPeerData(industry)); }
    finally { setLoading(false); }
  }

  const PEER_COLORS = ['#111', '#10b981', '#9ca3af'];

  return (
    <div className="space-y-4">
      <Section title="Parameters">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="w-64">
            <Sel label="SICS Industry" value={industry} onChange={setIndustry}
              options={SICS_SECTORS.flatMap(s => s.industries)} />
          </div>
          <Btn onClick={handleRun} loading={loading}>Load Peer Comparison</Btn>
        </div>
      </Section>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {PEERS.map((p, i) => (
          <KpiCard key={i} label={`Peer ${i + 1}`} value={p}
            sub={i === 0 ? 'Current entity' : 'Benchmark peer'}
            color={i === 0 ? 'text-gray-900' : i === 1 ? 'text-emerald-600' : 'text-gray-500'} />
        ))}
      </div>

      <Section title="Peer Comparison — Key SASB Metrics (Normalised 0-100)">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ left: 10, right: 20, top: 4, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="metric" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            {PEERS.map((p, i) => (
              <Bar key={p} dataKey={p} fill={PEER_COLORS[i]} radius={[2, 2, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── TABS ───────────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'metrics',    label: 'Industry Metrics' },
  { id: 'materiality',label: 'Materiality Map' },
  { id: 'sectors',    label: 'Sector Overview' },
  { id: 'issb',       label: 'ISSB S2 Mapping' },
  { id: 'peers',      label: 'Peer Comparison' },
];

/* ── Root ───────────────────────────────────────────────────────────────── */
export default function SASBPage() {
  const [tab, setTab] = useState('metrics');

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo entity — SASB SICS Industry Standards with seed fallback data. 20 SICS industries across 11 sectors." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">SASB Industry Standards (SICS)</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Sustainability Accounting Standards Board · 77 industry standards · IFRS S2 aligned · ESRS cross-referenced
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['SASB 2023', 'SICS', 'ISSB S2', 'ESRS'].map(b => (
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

      {tab === 'metrics'    && <IndustryMetrics />}
      {tab === 'materiality'&& <MaterialityMap />}
      {tab === 'sectors'    && <SectorOverview />}
      {tab === 'issb'       && <ISSBMapping />}
      {tab === 'peers'      && <PeerComparison />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Standards basis:</span> SASB Standards 2023 · SICS (Sustainable Industry Classification System) · 77 industry-specific standards across 11 sectors</p>
        <p><span className="font-semibold text-gray-500">Cross-framework:</span> IFRS S1/S2 industry-based disclosure requirements (App B) · EFRAG SASB–ESRS interoperability guidance · GRI topic alignment</p>
      </div>
    </div>
  );
}
