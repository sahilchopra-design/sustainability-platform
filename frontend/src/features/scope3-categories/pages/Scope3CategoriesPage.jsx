/**
 * Scope3CategoriesPage.jsx
 * Route: /scope3-categories
 * E21 — Scope 3 Categories Engine (GHG Protocol 2011, SBTi FLAG 2023)
 * Tabs:
 *   1. Materiality Assessment  — material categories list, FLAG flag, SBTi coverage
 *   2. Category Calculator     — per-category dynamic inputs
 *   3. SBTi Coverage           — coverage bar, FLAG vs non-FLAG PieChart
 *   4. Portfolio C15           — investee attribution table + BarChart
 *   5. Reference               — 15-row category table, FLAG sectors, DQS levels
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
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
    <input
      type={type} value={value} min={min} max={max} step={step} placeholder={placeholder}
      onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white"
    />
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
const ALL_CATEGORIES = [
  { id: 'C1',  name: 'Purchased Goods & Services', dir: 'upstream',   methods: ['Spend-based', 'Average-data', 'Supplier-specific'], dqs: 3 },
  { id: 'C2',  name: 'Capital Goods',               dir: 'upstream',   methods: ['Spend-based', 'Average-data'], dqs: 3 },
  { id: 'C3',  name: 'Fuel & Energy (not Scope 1/2)', dir: 'upstream', methods: ['Activity-based', 'Average-data'], dqs: 2 },
  { id: 'C4',  name: 'Upstream Transportation',     dir: 'upstream',   methods: ['Distance-based', 'Spend-based'], dqs: 3 },
  { id: 'C5',  name: 'Waste Generated in Operations', dir: 'upstream', methods: ['Waste-type-specific', 'Average-data'], dqs: 3 },
  { id: 'C6',  name: 'Business Travel',              dir: 'upstream',   methods: ['Distance-based', 'Spend-based'], dqs: 2 },
  { id: 'C7',  name: 'Employee Commuting',           dir: 'upstream',   methods: ['Distance-based', 'Survey-based'], dqs: 4 },
  { id: 'C8',  name: 'Upstream Leased Assets',       dir: 'upstream',   methods: ['Asset-specific', 'Average-data'], dqs: 3 },
  { id: 'C9',  name: 'Downstream Transportation',    dir: 'downstream', methods: ['Distance-based', 'Spend-based'], dqs: 3 },
  { id: 'C10', name: 'Processing of Sold Products',  dir: 'downstream', methods: ['Site-specific', 'Average-data'], dqs: 4 },
  { id: 'C11', name: 'Use of Sold Products',         dir: 'downstream', methods: ['Product-specific', 'Average-data'], dqs: 2 },
  { id: 'C12', name: 'End-of-Life Treatment',        dir: 'downstream', methods: ['Waste-type-specific', 'Recycled-content'], dqs: 4 },
  { id: 'C13', name: 'Downstream Leased Assets',     dir: 'downstream', methods: ['Asset-specific', 'Average-data'], dqs: 3 },
  { id: 'C14', name: 'Franchises',                   dir: 'downstream', methods: ['Franchise-specific', 'Average-data'], dqs: 4 },
  { id: 'C15', name: 'Investments (PCAF)',            dir: 'downstream', methods: ['PCAF Financed Emissions', 'Equity attribution'], dqs: 2 },
];

const NACE_OPTIONS = [
  { value: 'A01', label: 'A01 — Crop & Animal Production' },
  { value: 'B06', label: 'B06 — Crude Oil/Gas Extraction' },
  { value: 'C10', label: 'C10 — Food Manufacturing' },
  { value: 'C20', label: 'C20 — Chemical Manufacturing' },
  { value: 'D35', label: 'D35 — Electricity/Gas Supply' },
  { value: 'F41', label: 'F41 — Construction of Buildings' },
  { value: 'G46', label: 'G46 — Wholesale Trade' },
  { value: 'H49', label: 'H49 — Land Transport' },
  { value: 'I55', label: 'I55 — Accommodation' },
  { value: 'J62', label: 'J62 — IT Services' },
  { value: 'K64', label: 'K64 — Financial Activities' },
  { value: 'L68', label: 'L68 — Real Estate' },
];

const FLAG_NACE = ['A01', 'A02', 'A03', 'B06', 'C10'];

const MATERIAL_SEED = {
  A01: ['C1','C2','C3','C5','C7','C11','C15'],
  B06: ['C1','C3','C4','C5','C11','C15'],
  C10: ['C1','C2','C3','C5','C9','C11','C12','C15'],
  C20: ['C1','C3','C5','C9','C11','C15'],
  D35: ['C1','C3','C4','C11','C15'],
  K64: ['C1','C6','C7','C15'],
};

const SBTI_DATA = [
  { category: 'C1', tco2e: 18400, flag: false },
  { category: 'C3', tco2e: 5200, flag: false },
  { category: 'C5', tco2e: 2100, flag: false },
  { category: 'C7', tco2e: 1400, flag: false },
  { category: 'C11', tco2e: 22800, flag: false },
  { category: 'C15', tco2e: 48000, flag: true },
];

const PORTFOLIO_INVESTEES = [
  { name: 'GreenBuild GmbH',       sector: 'Real Estate', equity_pct: 15, scope3: 8400 },
  { name: 'AgriTech BV',           sector: 'Agriculture', equity_pct: 8,  scope3: 3200 },
  { name: 'EnergyGrid SA',         sector: 'Energy',      equity_pct: 22, scope3: 14600 },
  { name: 'LogiTrans SL',          sector: 'Transport',   equity_pct: 11, scope3: 6800 },
  { name: 'DigitalMfg PLC',        sector: 'Manufacturing', equity_pct: 18, scope3: 9200 },
];

const CAT_INPUTS = {
  C1:  [{ key: 'spend_musd', label: 'Total Spend (M USD)', default: '50' }, { key: 'ef', label: 'Emission Factor (kgCO₂/$)', default: '0.42' }],
  C6:  [{ key: 'km_air', label: 'Air Travel (km)', default: '500000' }, { key: 'km_rail', label: 'Rail Travel (km)', default: '80000' }],
  C7:  [{ key: 'employees', label: 'Headcount', default: '1200' }, { key: 'avg_km', label: 'Avg Daily Commute (km)', default: '22' }],
  C15: [{ key: 'equity_musd', label: 'Equity Investment (M USD)', default: '200' }, { key: 'investee_emissions', label: "Investee Total Emissions (tCO₂e)", default: '45000' }, { key: 'investee_ev', label: 'Investee EV (M USD)', default: '800' }],
};
const DEFAULT_CAT_INPUTS = [
  { key: 'quantity', label: 'Quantity / Activity', default: '1000' },
  { key: 'ef', label: 'Emission Factor (kgCO₂/unit)', default: '2.5' },
];

const DQS_LEVELS = [
  { score: 1, level: 'Primary', desc: 'Verified supplier-specific measured data' },
  { score: 2, level: 'Secondary-high', desc: 'Verified supplier-specific reported data' },
  { score: 3, level: 'Secondary-mid', desc: 'Industry average or spend-based' },
  { score: 4, level: 'Secondary-low', desc: 'Activity-based with generic factors' },
  { score: 5, level: 'Estimated', desc: 'Top-down estimation, low confidence' },
];

const PIE_COLORS = [EM, '#6366f1'];

// ── Component ─────────────────────────────────────────────────────────────
export default function Scope3CategoriesPage() {
  const [tab, setTab] = useState(0);

  // Tab 0
  const [entityName, setEntityName] = useState('Nexus Industrial AG');
  const [naceCode, setNaceCode] = useState('C10');
  const [revenue, setRevenue] = useState('4.2');
  const [headcount, setHeadcount] = useState('3400');
  const [materialResult, setMaterialResult] = useState(null);
  const [matLoading, setMatLoading] = useState(false);
  const [matError, setMatError] = useState('');

  // Tab 1
  const [selCategory, setSelCategory] = useState('C1');
  const [catInputVals, setCatInputVals] = useState({});
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcError, setCalcError] = useState('');

  // Tab 2
  const [sbtiLoading, setSbtiLoading] = useState(false);
  const [sbtiResult, setSbtiResult] = useState(null);
  const [sbtiError, setSbtiError] = useState('');

  // Tab 3
  const [portLoading, setPortLoading] = useState(false);
  const [portError, setPortError] = useState('');

  const isFlag = FLAG_NACE.includes(naceCode);
  const materialCats = MATERIAL_SEED[naceCode] || ['C1','C3','C15'];
  const sbtiTotal = SBTI_DATA.reduce((a, r) => a + r.tco2e, 0);
  const sbtiCoverage = 43;

  const activeCatInputs = CAT_INPUTS[selCategory] || DEFAULT_CAT_INPUTS;

  async function runMateriality() {
    setMatLoading(true); setMatError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/scope3-categories/assess-materiality`, {
        entity_name: entityName, nace_code: naceCode, revenue_bn: revenue, headcount,
      });
      setMaterialResult(data);
    } catch {
      setMatError('API unavailable — showing seed data.');
      setMaterialResult({ material_categories: materialCats, flag_applicable: isFlag, sbti_coverage_pct: sbtiCoverage });
    } finally { setMatLoading(false); }
  }

  async function runCalc() {
    setCalcLoading(true); setCalcError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/scope3-categories/calculate-category`, {
        category: selCategory, inputs: catInputVals,
      });
      setCalcResult(data);
    } catch {
      setCalcError('API unavailable — showing estimate.');
      const inputs = activeCatInputs.map(i => catInputVals[i.key] || i.default);
      const tco2e = Math.round(parseFloat(inputs[0] || 1000) * parseFloat(inputs[1] || 2.5));
      setCalcResult({ tco2e, dqs: ALL_CATEGORIES.find(c => c.id === selCategory)?.dqs || 3, method: activeCatInputs[0]?.label || 'Activity-based' });
    } finally { setCalcLoading(false); }
  }

  async function runSBTi() {
    setSbtiLoading(true); setSbtiError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/scope3-categories/sbti-coverage`, { entity_name: entityName });
      setSbtiResult(data);
    } catch {
      setSbtiError('API unavailable — showing seed data.');
      setSbtiResult({ coverage_pct: sbtiCoverage, total_tco2e: sbtiTotal });
    } finally { setSbtiLoading(false); }
  }

  async function runPort() {
    setPortLoading(true); setPortError('');
    try {
      await axios.post(`${API}/api/v1/scope3-categories/portfolio-scope3`, { entity_name: entityName });
    } catch {
      setPortError('API unavailable — showing seed investees.');
    } finally { setPortLoading(false); }
  }

  const flagTotal = SBTI_DATA.filter(r => r.flag).reduce((a, r) => a + r.tco2e, 0);
  const nonFlagTotal = sbtiTotal - flagTotal;
  const pieSplit = [{ name: 'FLAG (land-use)', value: flagTotal }, { name: 'Non-FLAG', value: nonFlagTotal }];

  const TABS = ['Materiality Assessment', 'Category Calculator', 'SBTi Coverage', 'Portfolio C15', 'Reference'];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-black text-white px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold tracking-tight">Scope 3 Categories Engine</h1>
          <p className="text-xs text-gray-400 mt-0.5">GHG Protocol Corporate Value Chain Standard 2011 · SBTi FLAG 2023</p>
        </div>
        <span className="text-[10px] font-bold px-2 py-1 rounded border border-emerald-500 text-emerald-400">E21</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-6 py-4">
        <KpiCard label="Material Categories" value={materialCats.length} sub={`for ${naceCode}`} accent="green" />
        <KpiCard label="Total Scope 3 (tCO₂e)" value={`${(sbtiTotal / 1000).toFixed(0)}k`} sub="All categories" />
        <KpiCard label="SBTi Coverage" value={`${sbtiCoverage}%`} sub="40% threshold" accent={sbtiCoverage >= 40 ? 'green' : 'red'} badge="SBTi" />
        <KpiCard label="FLAG Applicable" value={isFlag ? 'Yes' : 'No'} sub="Land-use FLAG" accent={isFlag ? 'amber' : 'green'} />
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

        {/* ── Tab 0: Materiality ── */}
        {tab === 0 && (
          <>
            <Section title="Entity Parameters" subtitle="Enter details to assess material Scope 3 categories">
              <Row label="Entity Name"><Inp value={entityName} onChange={setEntityName} type="text" /></Row>
              <Row label="NACE Code"><Sel value={naceCode} onChange={setNaceCode} options={NACE_OPTIONS} /></Row>
              <Row label="Revenue (€bn)"><Inp value={revenue} onChange={setRevenue} type="number" step="0.1" /></Row>
              <Row label="Headcount"><Inp value={headcount} onChange={setHeadcount} type="number" /></Row>
              <Btn onClick={runMateriality} loading={matLoading}>Assess Materiality</Btn>
            </Section>
            {matError && <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded p-3 mb-3">{matError}</div>}
            {materialResult && (
              <Section title="Materiality Results">
                <div className="flex flex-wrap gap-2 mb-4">
                  {ALL_CATEGORIES.map(cat => {
                    const isMat = materialResult.material_categories.includes(cat.id);
                    return (
                      <div key={cat.id} className={`px-3 py-1.5 rounded-lg border text-xs ${isMat ? 'border-emerald-300 bg-emerald-50 text-emerald-700 font-semibold' : 'border-gray-200 text-gray-400'}`}>
                        <span className="font-bold">{cat.id}</span>
                        <span className="ml-1.5 hidden sm:inline">{cat.name.split(' ').slice(0, 2).join(' ')}</span>
                        <span className="ml-1.5 text-[9px]">{cat.dir === 'upstream' ? '↑' : '↓'}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="flex gap-3 flex-wrap">
                  <span className={`px-3 py-1 rounded text-xs font-bold ${materialResult.flag_applicable ? 'bg-amber-100 text-amber-700 border border-amber-300' : 'bg-gray-100 text-gray-500'}`}>
                    FLAG: {materialResult.flag_applicable ? 'Applicable' : 'Not Applicable'}
                  </span>
                  <span className={`px-3 py-1 rounded text-xs font-bold ${materialResult.sbti_coverage_pct >= 40 ? 'bg-emerald-100 text-emerald-700 border border-emerald-300' : 'bg-red-100 text-red-700 border border-red-300'}`}>
                    SBTi Coverage: {materialResult.sbti_coverage_pct}%
                  </span>
                </div>
              </Section>
            )}
          </>
        )}

        {/* ── Tab 1: Category Calculator ── */}
        {tab === 1 && (
          <>
            <Section title="Category Selection" subtitle="Select a Scope 3 category and enter activity data">
              <Row label="Category">
                <Sel value={selCategory} onChange={id => { setSelCategory(id); setCatInputVals({}); setCalcResult(null); }}
                  options={ALL_CATEGORIES.map(c => ({ value: c.id, label: `${c.id} — ${c.name}` }))} />
              </Row>
              {activeCatInputs.map(inp => (
                <Row key={inp.key} label={inp.label}>
                  <Inp value={catInputVals[inp.key] ?? inp.default} onChange={v => setCatInputVals(p => ({ ...p, [inp.key]: v }))} type="number" step="any" />
                </Row>
              ))}
              <Btn onClick={runCalc} loading={calcLoading}>Calculate Emissions</Btn>
              {calcError && <div className="text-xs text-amber-600 mt-2">{calcError}</div>}
            </Section>
            {calcResult && (
              <Section title="Calculation Result">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-emerald-50 text-center">
                    <div className="text-3xl font-bold font-mono text-emerald-700">{calcResult.tco2e?.toLocaleString()}</div>
                    <div className="text-xs text-gray-500 mt-1">tCO₂e</div>
                  </div>
                  <div className="p-4 rounded-xl bg-gray-50 text-center">
                    <div className="text-3xl font-bold font-mono text-gray-700">{calcResult.dqs}</div>
                    <div className="text-xs text-gray-500 mt-1">DQS Score (1=best)</div>
                  </div>
                  <div className="p-4 rounded-xl bg-gray-50 text-center">
                    <div className="text-sm font-bold text-gray-700">{calcResult.method || activeCatInputs[0]?.label}</div>
                    <div className="text-xs text-gray-500 mt-1">Method Used</div>
                  </div>
                </div>
              </Section>
            )}
          </>
        )}

        {/* ── Tab 2: SBTi Coverage ── */}
        {tab === 2 && (
          <>
            <Section title="SBTi Scope 3 Coverage Analysis" subtitle="40% coverage rule: Scope 3 categories included in SBTi target must cover ≥40% of total Scope 3">
              <Btn onClick={runSBTi} loading={sbtiLoading}>Calculate Coverage</Btn>
              {sbtiError && <div className="text-xs text-amber-600 mt-2">{sbtiError}</div>}
            </Section>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Section title="Scope 3 by Category (tCO₂e)">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={SBTI_DATA} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar dataKey="tco2e" name="tCO₂e" fill={EM} radius={[4, 4, 0, 0]}>
                      {SBTI_DATA.map((r, i) => <Cell key={i} fill={r.flag ? '#f59e0b' : EM} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Section>
              <Section title="FLAG vs Non-FLAG Split">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieSplit} dataKey="value" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                      {pieSplit.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-2">
                  <div className="text-xs text-gray-500 mb-1">SBTi 40% Coverage Progress</div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-emerald-500 h-3 rounded-full" style={{ width: `${Math.min(sbtiCoverage, 100)}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>{sbtiCoverage}% covered</span>
                    <span className={sbtiCoverage >= 40 ? 'text-emerald-600 font-semibold' : 'text-red-600 font-semibold'}>{sbtiCoverage >= 40 ? 'Threshold met' : '40% threshold not met'}</span>
                  </div>
                </div>
              </Section>
            </div>
          </>
        )}

        {/* ── Tab 3: Portfolio C15 ── */}
        {tab === 3 && (
          <>
            <Section title="Category 15 — Investments (Scope 3)" subtitle="Attributed Scope 3 emissions from equity portfolio using PCAF methodology">
              <Btn onClick={runPort} loading={portLoading}>Refresh Portfolio Data</Btn>
              {portError && <div className="text-xs text-amber-600 mt-2">{portError}</div>}
            </Section>
            <Section title="Investee Scope 3 Attribution">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={PORTFOLIO_INVESTEES} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="name" tick={{ fontSize: 9 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="scope3" name="Attributed Scope 3 (tCO₂e)" fill={EM} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <table className="w-full text-xs mt-4">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">Investee</th>
                  <th className="text-left py-2 text-gray-500">Sector</th>
                  <th className="text-right py-2 text-gray-500">Equity %</th>
                  <th className="text-right py-2 text-gray-500">Attributed Scope 3 (tCO₂e)</th>
                </tr></thead>
                <tbody>
                  {PORTFOLIO_INVESTEES.map(r => (
                    <tr key={r.name} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-1.5 font-medium">{r.name}</td>
                      <td className="py-1.5 text-gray-500">{r.sector}</td>
                      <td className="py-1.5 text-right font-mono">{r.equity_pct}%</td>
                      <td className="py-1.5 text-right font-mono">{r.scope3.toLocaleString()}</td>
                    </tr>
                  ))}
                  <tr className="font-bold">
                    <td className="py-1.5" colSpan={3}>Total C15</td>
                    <td className="py-1.5 text-right font-mono">{PORTFOLIO_INVESTEES.reduce((a, r) => a + r.scope3, 0).toLocaleString()}</td>
                  </tr>
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* ── Tab 4: Reference ── */}
        {tab === 4 && (
          <>
            <Section title="15 Scope 3 Categories — GHG Protocol 2011">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">ID</th>
                  <th className="text-left py-2 text-gray-500">Category Name</th>
                  <th className="text-left py-2 text-gray-500">Direction</th>
                  <th className="text-left py-2 text-gray-500">Calculation Methods</th>
                  <th className="text-center py-2 text-gray-500">DQS</th>
                </tr></thead>
                <tbody>
                  {ALL_CATEGORIES.map(c => (
                    <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-1.5 font-bold text-emerald-700">{c.id}</td>
                      <td className="py-1.5 font-medium">{c.name}</td>
                      <td className="py-1.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${c.dir === 'upstream' ? 'bg-blue-50 text-blue-700' : 'bg-purple-50 text-purple-700'}`}>{c.dir}</span>
                      </td>
                      <td className="py-1.5 text-gray-500">{c.methods.join(', ')}</td>
                      <td className="py-1.5 text-center font-mono">{c.dqs}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="DQS Quality Levels (PCAF)">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-center py-2 text-gray-500">Score</th>
                  <th className="text-left py-2 text-gray-500">Level</th>
                  <th className="text-left py-2 text-gray-500">Description</th>
                </tr></thead>
                <tbody>
                  {DQS_LEVELS.map(d => (
                    <tr key={d.score} className="border-b border-gray-100">
                      <td className="py-1.5 text-center font-bold font-mono text-emerald-700">{d.score}</td>
                      <td className="py-1.5 font-medium">{d.level}</td>
                      <td className="py-1.5 text-gray-500">{d.desc}</td>
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
