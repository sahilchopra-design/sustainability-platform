import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-black">{value}</div>{sub&&<div className="text-xs text-emerald-600 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{children}</div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}/></div>);
const Sel = ({label,children,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>);

const seed = 77;
const rng = (i, s = seed) => Math.abs(Math.sin(i * 9301 + s * 49297) * 233280) % 233280 / 233280;

const TABS = ['Natural Capital Assessment', 'Ecosystem Service Valuation', 'Dependency Scoring', 'Disclosure Completeness', 'Nature Balance Sheet'];

const ECOSYSTEM_TYPES = ['tropical forest','temperate forest','wetland','grassland','mangrove','coral reef','freshwater','agricultural land','urban green','coastal'];
const SECTORS_20 = ['Agriculture','Banking','Chemicals','Construction','Energy','Food & Beverage','Forestry','Healthcare','Insurance','Manufacturing','Mining','Pharma','Real Estate','Retail','Shipping','Technology','Textiles','Tourism','Transport','Utilities'];
const SERVICES_PROVISIONING = ['Food production','Freshwater supply','Timber & fibre','Genetic resources'];
const SERVICES_REGULATING = ['Climate regulation','Water purification','Flood attenuation','Pollination','Air quality'];
const SERVICES_CULTURAL = ['Recreation & tourism','Aesthetic values','Spiritual & cultural','Research & education'];
const REPORTING_STANDARDS = ['TNFD v1.0','SEEA EA 2021','GRI 304','CSRD ESRS E4'];
const SEEA_COLORS = ['#059669','#10b981','#34d399','#6ee7b7','#d1fae5'];

// ── Tab 1: Natural Capital Assessment ─────────────────────────────────────────
function Tab1() {
  const [ecoType, setEcoType] = useState('tropical forest');
  const [extent, setExtent] = useState('50000');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const conditionScore = result?.condition || +(rng(0, seed + 1) * 40 + 55).toFixed(1);
  const monetaryValue = result?.monetary_value || Math.round(rng(1, seed + 1) * 500 + 200);

  const depImpactData = [
    { name: 'Water regulation', dependency: 85, impact: 35 },
    { name: 'Carbon sequestration', dependency: 92, impact: 28 },
    { name: 'Biodiversity habitat', dependency: 78, impact: 45 },
    { name: 'Soil formation', dependency: 65, impact: 22 },
    { name: 'Flood attenuation', dependency: 70, impact: 30 },
  ].map((d, i) => ({ ...d, dependency: Math.round(rng(i, seed + 2) * 30 + 60), impact: Math.round(rng(i, seed + 3) * 30 + 20) }));

  const seeaAccountTypes = { 'tropical forest': 'EA-C: Ecosystem Condition', 'wetland': 'EA-E: Ecosystem Extent', 'agricultural land': 'EA-S: Ecosystem Services', 'coral reef': 'EA-D: Ecosystem Degradation' };
  const accountBadge = seeaAccountTypes[ecoType] || 'EA-C: Ecosystem Condition';

  const handleAssess = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/nature-capital/assess', { ecosystem_type: ecoType, extent_ha: parseFloat(extent) });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [ecoType, extent]);

  return (
    <div>
      <Section title="Assessment Parameters">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Sel label="Ecosystem Type" value={ecoType} onChange={e => setEcoType(e.target.value)}>
            {ECOSYSTEM_TYPES.map(t => <option key={t}>{t}</option>)}
          </Sel>
          <Inp label="Extent (hectares)" value={extent} onChange={e => setExtent(e.target.value)} type="number" />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-600">SEEA EA Account Type</label>
            <div className="mt-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded text-sm font-medium text-emerald-800">{accountBadge}</div>
          </div>
        </div>
        <Btn onClick={handleAssess} disabled={loading}>{loading ? 'Assessing…' : 'Assess Natural Capital'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Condition Score" value={`${conditionScore.toFixed(1)}/100`} sub="SEEA EA 2021 condition index" />
        <KpiCard label="Monetary Value" value={`$${monetaryValue}M/yr`} sub="TEEB ecosystem services value" />
        <KpiCard label="Ecosystem Extent" value={`${parseInt(extent).toLocaleString()} ha`} sub="Under assessment" />
        <KpiCard label="TNFD Status" value={conditionScore > 70 ? 'Low Risk' : conditionScore > 50 ? 'Medium Risk' : 'High Risk'} sub="Nature-related risk tier" />
      </Row>
      <Section title="TNFD Dependency / Impact Scores">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={depImpactData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-15} textAnchor="end" height={50} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Bar dataKey="dependency" fill="#059669" name="Dependency Score" />
            <Bar dataKey="impact" fill="#ef4444" name="Impact Score" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2: Ecosystem Service Valuation ────────────────────────────────────────
function Tab2() {
  const [selectedServices, setSelectedServices] = useState(['Food production','Climate regulation','Recreation & tourism']);
  const [extent, setExtent] = useState('25000');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const allServices = [...SERVICES_PROVISIONING, ...SERVICES_REGULATING, ...SERVICES_CULTURAL];
  const toggle = s => setSelectedServices(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);

  const valuationData = [
    { category: 'Provisioning', value: Math.round(rng(0, seed + 10) * 150 + 80) },
    { category: 'Regulating', value: Math.round(rng(1, seed + 10) * 200 + 120) },
    { category: 'Cultural', value: Math.round(rng(2, seed + 10) * 80 + 30) },
  ];

  const totalVal = valuationData.reduce((s, d) => s + d.value, 0);

  const confidenceTable = [
    { service: 'Food production', method: 'Market price', value: Math.round(rng(3, seed + 10) * 40 + 30), confidence: 'High' },
    { service: 'Climate regulation', method: 'Social cost of carbon', value: Math.round(rng(4, seed + 10) * 80 + 50), confidence: 'Medium' },
    { service: 'Water purification', method: 'Replacement cost', value: Math.round(rng(5, seed + 10) * 50 + 25), confidence: 'Medium' },
    { service: 'Recreation', method: 'Travel cost / CVM', value: Math.round(rng(6, seed + 10) * 30 + 15), confidence: 'Low' },
  ];

  const handleValuate = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/nature-capital/valuate-services', { services: selectedServices, extent_ha: parseFloat(extent) });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [selectedServices, extent]);

  return (
    <div>
      <Section title="Service Selection">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-600 mb-2 block">Ecosystem Services</label>
            <div className="flex flex-wrap gap-1">
              {allServices.map(s => (
                <button key={s} onClick={() => toggle(s)} className={`px-2 py-1 rounded text-xs border ${selectedServices.includes(s) ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-600 border-gray-300'}`}>{s}</button>
              ))}
            </div>
          </div>
          <Inp label="Extent (hectares)" value={extent} onChange={e => setExtent(e.target.value)} type="number" />
        </div>
        <Btn onClick={handleValuate} disabled={loading}>{loading ? 'Valuating…' : 'Valuate Services'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Total Annual Value" value={`$${totalVal}M/yr`} sub="WAVES methodology" />
        <KpiCard label="Provisioning" value={`$${valuationData[0].value}M/yr`} sub="Food, water, timber" />
        <KpiCard label="Regulating" value={`$${valuationData[1].value}M/yr`} sub="Climate, water, pollination" />
        <KpiCard label="Cultural" value={`$${valuationData[2].value}M/yr`} sub="Recreation, aesthetic" />
      </Row>
      <Section title="Annual Flow Values by Category ($M/yr)">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={valuationData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip formatter={v => `$${v}M/yr`} />
            <Bar dataKey="value" fill="#059669" name="Annual Value" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Confidence Interval Table">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>{['Service','Valuation Method','Value ($M/yr)','Confidence'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
          </thead>
          <tbody>
            {confidenceTable.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-2">{row.service}</td>
                <td className="px-3 py-2 text-gray-600">{row.method}</td>
                <td className="px-3 py-2 font-mono">${row.value}M</td>
                <td className="px-3 py-2"><span className={`px-2 py-0.5 rounded text-xs font-medium ${row.confidence === 'High' ? 'bg-green-100 text-green-700' : row.confidence === 'Medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>{row.confidence}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Tab 3: Dependency Scoring ──────────────────────────────────────────────────
function Tab3() {
  const [sector, setSector] = useState('Agriculture');
  const [operations, setOperations] = useState('Primary crop production operations in water-stressed regions');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const ENCORE_ROWS = ['Freshwater','Soil','Air','Climate','Biodiversity'];
  const ENCORE_COLS = ['Direct use','Indirect use','Soil quality','Water quality','Erosion ctrl'];
  const encoreMatrix = ENCORE_ROWS.map((row, ri) => ({
    row, values: ENCORE_COLS.map((col, ci) => Math.round(rng(ri * 5 + ci, seed + 20) * 5) + 1),
  }));

  const revenueAtRisk = Math.round(rng(7, seed + 20) * 40 + 15);
  const criticalDeps = ['Surface water abstraction', 'Soil fertility & micro-organisms', 'Climate regulation & rainfall patterns', 'Pollination services (wild bees)', 'Flood & erosion control'];

  const handleScore = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/nature-capital/dependency-score', { sector, operations });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [sector, operations]);

  const cellColor = v => v >= 4 ? 'bg-red-200 text-red-800' : v >= 3 ? 'bg-orange-100 text-orange-700' : v >= 2 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700';

  return (
    <div>
      <Section title="Configuration">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <Sel label="Sector" value={sector} onChange={e => setSector(e.target.value)}>
            {SECTORS_20.map(s => <option key={s}>{s}</option>)}
          </Sel>
          <Inp label="Operations Description" value={operations} onChange={e => setOperations(e.target.value)} />
        </div>
        <Btn onClick={handleScore} disabled={loading}>{loading ? 'Scoring…' : 'Score Dependencies'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Revenue at Risk" value={`${revenueAtRisk}%`} sub="Nature dependency exposure" />
        <KpiCard label="Critical Dependencies" value={criticalDeps.length} sub="TNFD LEAP Step A" />
        <KpiCard label="TNFD Step A" value="Complete" sub="Locate — business activities" />
        <KpiCard label="ENCORE Score" value="High" sub="Material dependency identified" />
      </Row>
      <Section title="ENCORE Dependency Matrix (1=Low → 5=High)">
        <div className="overflow-auto">
          <table className="min-w-full text-xs border border-gray-200 rounded">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-2 py-2 text-left font-medium text-gray-600">Asset</th>
                {ENCORE_COLS.map(c => <th key={c} className="px-2 py-2 text-center font-medium text-gray-600">{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {encoreMatrix.map(row => (
                <tr key={row.row} className="border-t border-gray-100">
                  <td className="px-2 py-2 font-medium">{row.row}</td>
                  {row.values.map((v, ci) => <td key={ci} className={`px-2 py-2 text-center font-bold rounded ${cellColor(v)}`}>{v}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
      <Section title="Critical Dependencies">
        <ul className="space-y-2">
          {criticalDeps.map((d, i) => (
            <li key={i} className="flex items-center gap-2 text-sm p-2 bg-red-50 border border-red-100 rounded">
              <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
              {d}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

// ── Tab 4: Disclosure Completeness ────────────────────────────────────────────
function Tab4() {
  const [standard, setStandard] = useState('TNFD v1.0');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const tnfdItems = [
    'Governance of nature-related risks','Strategy — nature-related risks and opportunities','Risk management processes',
    'Metrics and targets — nature dependencies','Metrics and targets — nature impacts','Metrics and targets — nature risks',
    'Metrics and targets — nature opportunities','Direct operations — locations in sensitive areas',
    'Upstream supply chain assessment','Downstream value chain assessment','Nature-positive transition plan',
    'Scenario analysis — nature risk','Stakeholder engagement','Verification and assurance',
  ].map((item, i) => ({ item, complete: rng(i, seed + 30) > 0.35 }));

  const completenessScore = Math.round(tnfdItems.filter(i => i.complete).length / tnfdItems.length * 100);

  const gbfSubElements = [
    { id: 'a', description: 'Assess dependencies and impacts on biodiversity', status: 'Complete' },
    { id: 'b', description: 'Assess nature-related risks and opportunities', status: 'Partial' },
    { id: 'c', description: 'Set measurable targets for nature-positive transition', status: 'Partial' },
    { id: 'd', description: 'Report transparently on progress against targets', status: 'Not started' },
    { id: 'e', description: 'Consider supply chain biodiversity impacts', status: 'Partial' },
    { id: 'f', description: 'Monitor and verify biodiversity performance', status: 'Not started' },
  ];

  const handleScore = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/nature-capital/disclosure-score', { standard });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [standard]);

  const barData = tnfdItems.map((item, i) => ({ name: `M${i + 1}`, score: item.complete ? Math.round(rng(i, seed + 31) * 30 + 70) : Math.round(rng(i, seed + 32) * 40) }));
  const statusColor = s => s === 'Complete' ? 'bg-green-100 text-green-700' : s === 'Partial' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700';

  return (
    <div>
      <Section title="Reporting Standard">
        <div className="flex gap-4 mb-4">
          <Sel label="Standard" value={standard} onChange={e => setStandard(e.target.value)}>
            {REPORTING_STANDARDS.map(s => <option key={s}>{s}</option>)}
          </Sel>
        </div>
        <Btn onClick={handleScore} disabled={loading}>{loading ? 'Scoring…' : 'Score Disclosure'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Completeness Score" value={`${completenessScore}%`} sub={`${standard} framework`} />
        <KpiCard label="Metrics Complete" value={tnfdItems.filter(i => i.complete).length} sub={`of ${tnfdItems.length} TNFD metrics`} />
        <KpiCard label="Gaps Identified" value={tnfdItems.filter(i => !i.complete).length} sub="Require disclosure" />
        <KpiCard label="GBF Target 15" value="Partial" sub="6 sub-elements assessed" />
      </Row>
      <Section title="TNFD 14-Metric Completeness">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="score" fill="#059669" name="Completeness %" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="CBD GBF Target 15 Sub-Elements">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>{['Sub-element','Description','Status'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
          </thead>
          <tbody>
            {gbfSubElements.map(row => (
              <tr key={row.id} className="border-t border-gray-100">
                <td className="px-3 py-2 font-mono font-bold text-emerald-700">{row.id}</td>
                <td className="px-3 py-2">{row.description}</td>
                <td className="px-3 py-2"><span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(row.status)}`}>{row.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Tab 5: Nature Balance Sheet ────────────────────────────────────────────────
function Tab5() {
  const [assetCount, setAssetCount] = useState('12');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const seeaTable = [
    { item: 'Opening stock (2020)', value: 2840, note: 'SEEA EA extent account' },
    { item: 'Additions — restoration', value: 125, note: 'Afforestation & rewilding' },
    { item: 'Additions — natural growth', value: 68, note: 'Net primary productivity' },
    { item: 'Depletions — harvest/extraction', value: -142, note: 'Timber, water abstraction' },
    { item: 'Degradation — pollution', value: -89, note: 'Air, water, soil contamination' },
    { item: 'Closing stock (2024)', value: 2802, note: 'Net ecosystem capital' },
  ].map((row, i) => ({ ...row, value: Math.round(rng(i, seed + 40) * 200 + row.value * 0.9) }));

  const serviceFlowData = [2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2030].map((year, i) => ({
    year,
    provisioning: Math.round(rng(i, seed + 41) * 50 + 180),
    regulating: Math.round(rng(i, seed + 42) * 60 + 220),
    cultural: Math.round(rng(i, seed + 43) * 30 + 80),
  }));

  const integratedPL = Math.round(rng(8, seed + 40) * 200 + 150);

  const handleSheet = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/nature-capital/balance-sheet', { asset_count: parseInt(assetCount) });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [assetCount]);

  return (
    <div>
      <Section title="Configuration">
        <div className="flex gap-4 mb-4">
          <Inp label="Number of Natural Capital Assets" value={assetCount} onChange={e => setAssetCount(e.target.value)} type="number" />
        </div>
        <Btn onClick={handleSheet} disabled={loading}>{loading ? 'Generating…' : 'Generate Balance Sheet'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Integrated P&L Impact" value={`$${integratedPL}M`} sub="Nature-adjusted profit" />
        <KpiCard label="Assets Assessed" value={assetCount} sub="Natural capital assets" />
        <KpiCard label="Net Capital Change" value={`-${Math.round(rng(9, seed + 40) * 5 + 1)}%`} sub="2020→2024 trend" />
        <KpiCard label="Ecosystem Services" value="$482M/yr" sub="Total annual service flows" />
      </Row>
      <Section title="SEEA EA Account (Nature Capital Stock, $M)">
        <div className="overflow-auto">
          <table className="min-w-full text-sm border border-gray-200 rounded">
            <thead className="bg-gray-50">
              <tr>{['Account Item','Value ($M)','Notes'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
            </thead>
            <tbody>
              {seeaTable.map((row, i) => (
                <tr key={i} className={`border-t border-gray-100 ${i === 0 || i === seeaTable.length - 1 ? 'bg-emerald-50 font-semibold' : ''}`}>
                  <td className="px-3 py-2">{row.item}</td>
                  <td className={`px-3 py-2 font-mono ${row.value < 0 ? 'text-red-600' : 'text-emerald-700'}`}>{row.value < 0 ? `-$${Math.abs(row.value)}M` : `$${row.value}M`}</td>
                  <td className="px-3 py-2 text-gray-500 text-xs">{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
      <Section title="Ecosystem Service Flows 2020–2030 ($M/yr)">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={serviceFlowData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="provisioning" stackId="1" stroke="#059669" fill="#d1fae5" name="Provisioning" />
            <Area type="monotone" dataKey="regulating" stackId="1" stroke="#0284c7" fill="#bae6fd" name="Regulating" />
            <Area type="monotone" dataKey="cultural" stackId="1" stroke="#7c3aed" fill="#ede9fe" name="Cultural" />
          </AreaChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function NatureCapitalPage() {
  const [activeTab, setActiveTab] = useState(0);
  const tabComponents = [Tab1, Tab2, Tab3, Tab4, Tab5];
  const ActiveComp = tabComponents[activeTab];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Nature Capital Accounting</h1>
          <p className="text-sm text-gray-500 mt-1">SEEA EA 2021 · TNFD v1.0 · ENCORE Ecosystem Services · TEEB Biome Values · WAVES · CBD GBF Target 15 · E77</p>
        </div>
        <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200 pb-2">
          {TABS.map((tab, i) => (
            <button key={i} onClick={() => setActiveTab(i)} className={`px-4 py-2 rounded-t text-sm font-medium transition-colors ${activeTab === i ? 'bg-emerald-600 text-white' : 'bg-white text-gray-600 hover:bg-emerald-50 border border-gray-200'}`}>{tab}</button>
          ))}
        </div>
        <ActiveComp />
      </div>
    </div>
  );
}
