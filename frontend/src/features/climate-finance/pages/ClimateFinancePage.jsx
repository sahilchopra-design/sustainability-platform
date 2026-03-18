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

const seed = 78;
const rng = (i, s = seed) => Math.abs(Math.sin(i * 9301 + s * 49297) * 233280) % 233280 / 233280;

const TABS = ['Finance Tracking', 'Art 2.1(c) Alignment', 'NCQG Contribution', 'Private Mobilisation', 'CPI Landscape'];

const INST_TYPES = ['Multilateral Development Bank','Bilateral Development Finance','Commercial Bank','Institutional Investor','Export Credit Agency','Philanthropic Foundation','Sovereign Wealth Fund'];
const SCENARIOS = ['1.5°C','2°C','NDC','Current Policies'];
const INSTRUMENTS = ['Guarantees','Equity','Loans','Grants','Green Bonds','Blended Finance'];
const GEOGRAPHIES = ['Global','OECD','Non-OECD','Annex I','Non-Annex I'];
const PIE_COLORS = ['#059669','#10b981','#34d399','#6ee7b7','#d1fae5','#a7f3d0'];

// ── Tab 1: Finance Tracking ───────────────────────────────────────────────────
function Tab1() {
  const [instType, setInstType] = useState('Multilateral Development Bank');
  const [year, setYear] = useState('2023');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const instruments = ['Grants','Concessional loans','Non-concessional loans','Equity','Guarantees','Other'];
  const rioMarkers = [1, 2, 3];
  const barData = instruments.map((inst, i) => ({
    instrument: inst,
    adaptation: Math.round(rng(i, seed + 1) * 3000 + 500),
    mitigation: Math.round(rng(i, seed + 2) * 5000 + 1000),
    crossCutting: Math.round(rng(i, seed + 3) * 2000 + 300),
  }));

  const totalClimate = barData.reduce((s, d) => s + d.adaptation + d.mitigation + d.crossCutting, 0);
  const adaptationTotal = barData.reduce((s, d) => s + d.adaptation, 0);
  const mitigationTotal = barData.reduce((s, d) => s + d.mitigation, 0);

  const pieData = [
    { name: 'Mitigation', value: mitigationTotal },
    { name: 'Adaptation', value: adaptationTotal },
    { name: 'Cross-cutting', value: totalClimate - mitigationTotal - adaptationTotal },
  ];

  const handleTrack = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/climate-finance/track', { institution_type: instType, year: parseInt(year) });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [instType, year]);

  return (
    <div>
      <Section title="Tracking Parameters">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Sel label="Institution Type" value={instType} onChange={e => setInstType(e.target.value)}>
            {INST_TYPES.map(t => <option key={t}>{t}</option>)}
          </Sel>
          <Sel label="Year" value={year} onChange={e => setYear(e.target.value)}>
            {[2019,2020,2021,2022,2023,2024].map(y => <option key={y}>{y}</option>)}
          </Sel>
        </div>
        <Btn onClick={handleTrack} disabled={loading}>{loading ? 'Tracking…' : 'Track Finance'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Total Climate Finance" value={`$${(totalClimate / 1000).toFixed(1)}B`} sub={`${year} OECD CRS tracking`} />
        <KpiCard label="Mitigation Finance" value={`$${(mitigationTotal / 1000).toFixed(1)}B`} sub={`${Math.round(mitigationTotal / totalClimate * 100)}% of total`} />
        <KpiCard label="Adaptation Finance" value={`$${(adaptationTotal / 1000).toFixed(1)}B`} sub={`${Math.round(adaptationTotal / totalClimate * 100)}% of total`} />
        <KpiCard label="$100B Commitment" value="Met" sub="UNFCCC Paris $100bn/yr" />
      </Row>
      <Section title="OECD CRS Rio Markers by Instrument ($M)">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="instrument" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={50} />
            <YAxis />
            <Tooltip formatter={v => `$${v}M`} />
            <Legend />
            <Bar dataKey="mitigation" fill="#059669" name="Mitigation" stackId="a" />
            <Bar dataKey="adaptation" fill="#0284c7" name="Adaptation" stackId="a" />
            <Bar dataKey="crossCutting" fill="#7c3aed" name="Cross-cutting" stackId="a" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Adaptation / Mitigation Split">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
              {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
            </Pie>
            <Tooltip formatter={v => `$${(v / 1000).toFixed(1)}B`} />
          </PieChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2: Art 2.1(c) Alignment ───────────────────────────────────────────────
function Tab2() {
  const [portfolioValue, setPortfolioValue] = useState('500');
  const [scenario, setScenario] = useState('1.5°C');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const alignmentScore = result?.score || Math.round(rng(0, seed + 10) * 40 + 45);
  const parisConsistentPct = result?.paris_pct || +(rng(1, seed + 10) * 30 + 35).toFixed(1);

  const fossilData = [
    { sector: 'Coal mining', exposure: Math.round(rng(0, seed + 11) * 40 + 10) },
    { sector: 'Oil & gas E&P', exposure: Math.round(rng(1, seed + 11) * 80 + 30) },
    { sector: 'Oil refining', exposure: Math.round(rng(2, seed + 11) * 60 + 20) },
    { sector: 'Gas utilities', exposure: Math.round(rng(3, seed + 11) * 50 + 15) },
    { sector: 'Coal power', exposure: Math.round(rng(4, seed + 11) * 45 + 12) },
  ];

  const brownGreenPie = [
    { name: 'Green / Aligned', value: Math.round(rng(5, seed + 11) * 30 + 25) },
    { name: 'Brown / Fossil', value: Math.round(rng(6, seed + 11) * 30 + 20) },
    { name: 'Neutral', value: Math.round(rng(7, seed + 11) * 30 + 40) },
  ];

  const handleAlign = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/climate-finance/article21c-alignment', { portfolio_value: parseFloat(portfolioValue), scenario });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [portfolioValue, scenario]);

  return (
    <div>
      <Section title="Alignment Parameters">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Inp label="Portfolio Value ($B)" value={portfolioValue} onChange={e => setPortfolioValue(e.target.value)} type="number" />
          <Sel label="Paris Scenario" value={scenario} onChange={e => setScenario(e.target.value)}>
            {SCENARIOS.map(s => <option key={s}>{s}</option>)}
          </Sel>
        </div>
        <Btn onClick={handleAlign} disabled={loading}>{loading ? 'Aligning…' : 'Assess Alignment'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Alignment Score" value={`${alignmentScore}/100`} sub={`Art. 2.1(c) Paris Agreement`} />
        <KpiCard label="Paris-Consistent Flows" value={`${parisConsistentPct}%`} sub="of total portfolio flows" />
        <KpiCard label="Portfolio Value" value={`$${portfolioValue}B`} sub="Under assessment" />
        <KpiCard label="Scenario" value={scenario} sub="NGFS alignment pathway" />
      </Row>
      <Section title="Fossil Fuel Exposure ($M)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={fossilData} layout="vertical" margin={{ left: 100 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="sector" tick={{ fontSize: 11 }} />
            <Tooltip formatter={v => `$${v}M`} />
            <Bar dataKey="exposure" fill="#ef4444" name="Exposure ($M)" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Brown vs Green Portfolio Ratio">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={brownGreenPie} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
              {brownGreenPie.map((_, i) => <Cell key={i} fill={[PIE_COLORS[0], '#ef4444', '#9ca3af'][i]} />)}
            </Pie>
            <Tooltip formatter={v => `${v}%`} />
          </PieChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 3: NCQG Contribution ──────────────────────────────────────────────────
function Tab3() {
  const [instType, setInstType] = useState('Multilateral Development Bank');
  const [baseline, setBaseline] = useState('8.5');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const ncqgData = [
    { layer: 'Core ($300B bilateral)', current: 85, target: 300 },
    { layer: 'Broader goal ($1.3T all flows)', current: 780, target: 1300 },
    { layer: 'Adaptation sub-goal ($40B)', current: 24, target: 40 },
    { layer: 'Loss & Damage ($100B)', current: 12, target: 100 },
  ].map((d, i) => ({ ...d, current: Math.round(rng(i, seed + 20) * d.current * 0.4 + d.current * 0.8) }));

  const mobilisationTable = [
    { tier: 'MDB Core', multiplier: 3.2, role: 'Direct financing' },
    { tier: 'DFI Bilateral', multiplier: 2.8, role: 'Concessional lending' },
    { tier: 'Private Mobilised', multiplier: 1.5, role: 'Guarantees & equity' },
    { tier: 'Philanthropic', multiplier: 0.8, role: 'Grant-making' },
  ];

  const gapToGoal = 300 - ncqgData[0].current;
  const tierBadge = baseline > 5 ? 'Tier 1 — Major Contributor' : baseline > 2 ? 'Tier 2 — Significant' : 'Tier 3 — Emerging';

  const handleCalc = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/climate-finance/ncqg-contribution', { institution_type: instType, baseline_finance: parseFloat(baseline) });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [instType, baseline]);

  return (
    <div>
      <Section title="NCQG Parameters">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Sel label="Institution Type" value={instType} onChange={e => setInstType(e.target.value)}>
            {INST_TYPES.map(t => <option key={t}>{t}</option>)}
          </Sel>
          <Inp label="Baseline Finance ($B/yr)" value={baseline} onChange={e => setBaseline(e.target.value)} type="number" step="0.1" />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-600">Contributor Tier</label>
            <div className="mt-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded text-sm font-medium text-emerald-800">{tierBadge}</div>
          </div>
        </div>
        <Btn onClick={handleCalc} disabled={loading}>{loading ? 'Calculating…' : 'Calculate NCQG Contribution'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Gap to $300B Goal" value={`$${gapToGoal}B`} sub="COP29 NCQG core target" />
        <KpiCard label="Your Contribution" value={`$${baseline}B/yr`} sub="Baseline assessment" />
        <KpiCard label="NCQG Goal" value="$300B/yr" sub="COP29 CMA decision" />
        <KpiCard label="Broader Goal" value="$1.3T/yr" sub="All flows — developed → developing" />
      </Row>
      <Section title="NCQG $300B Target Breakdown">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={ncqgData} layout="vertical" margin={{ left: 200 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="layer" tick={{ fontSize: 10 }} />
            <Tooltip formatter={v => `$${v}B`} />
            <Legend />
            <Bar dataKey="current" fill="#059669" name="Current ($B)" />
            <Bar dataKey="target" fill="#e5e7eb" name="Target ($B)" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Mobilisation Multiplier Table">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>{['Contributor Tier','Mobilisation Multiplier','Primary Role'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
          </thead>
          <tbody>
            {mobilisationTable.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-2 font-medium">{row.tier}</td>
                <td className="px-3 py-2 font-mono text-emerald-700">{row.multiplier}x</td>
                <td className="px-3 py-2 text-gray-600">{row.role}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Tab 4: Private Mobilisation ───────────────────────────────────────────────
function Tab4() {
  const [publicFinance, setPublicFinance] = useState('2.5');
  const [selectedInstruments, setSelectedInstruments] = useState(['Guarantees', 'Green Bonds']);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggle = i => setSelectedInstruments(s => s.includes(i) ? s.filter(x => x !== i) : [...s, i]);

  const mobilisationData = INSTRUMENTS.map((inst, i) => ({
    instrument: inst,
    actual: +(rng(i, seed + 30) * 3 + 0.5).toFixed(2),
    benchmark: +(rng(i, seed + 31) * 2.5 + 1.2).toFixed(2),
  }));

  const totalMobilised = Math.round(parseFloat(publicFinance) * (rng(5, seed + 30) * 3 + 2));
  const additionalityScore = Math.round(rng(6, seed + 30) * 30 + 60);

  const tossdTable = [
    { instrument: 'Guarantees', eligible: true, provider: 'MDB / DFI', note: 'Risk mitigation' },
    { instrument: 'Equity', eligible: true, provider: 'DFI', note: 'First-loss tranche' },
    { instrument: 'Concessional loans', eligible: true, provider: 'ODA', note: 'DAC grant equivalent' },
    { instrument: 'Private loans', eligible: false, provider: 'Commercial', note: 'Excluded from TOSSD' },
  ];

  const handleMobilise = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/climate-finance/mobilisation', { public_finance: parseFloat(publicFinance), instruments: selectedInstruments });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [publicFinance, selectedInstruments]);

  return (
    <div>
      <Section title="Mobilisation Parameters">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <Inp label="Public Finance Input ($B)" value={publicFinance} onChange={e => setPublicFinance(e.target.value)} type="number" step="0.1" />
          <div>
            <label className="text-xs text-gray-600 mb-2 block">Instruments</label>
            <div className="flex flex-wrap gap-2">
              {INSTRUMENTS.map(i => (
                <button key={i} onClick={() => toggle(i)} className={`px-2 py-1 rounded text-xs border ${selectedInstruments.includes(i) ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-600 border-gray-300'}`}>{i}</button>
              ))}
            </div>
          </div>
        </div>
        <Btn onClick={handleMobilise} disabled={loading}>{loading ? 'Calculating…' : 'Calculate Mobilisation'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Total Private Mobilised" value={`$${totalMobilised}B`} sub="Estimated private capital" />
        <KpiCard label="Additionality Score" value={`${additionalityScore}/100`} sub="Convergence benchmark alignment" />
        <KpiCard label="Public Finance Input" value={`$${publicFinance}B`} sub="Concessional/public flows" />
        <KpiCard label="Avg Ratio" value={`${(totalMobilised / parseFloat(publicFinance)).toFixed(1)}x`} sub="Private per public $" />
      </Row>
      <Section title="Mobilisation Ratio by Instrument (vs Convergence Benchmarks)">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={mobilisationData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="instrument" tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="actual" fill="#059669" name="Actual Ratio" />
            <Bar dataKey="benchmark" fill="#d1fae5" name="Convergence Benchmark" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="TOSSD Eligibility">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>{['Instrument','TOSSD Eligible','Provider','Note'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
          </thead>
          <tbody>
            {tossdTable.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-2">{row.instrument}</td>
                <td className="px-3 py-2"><span className={`px-2 py-0.5 rounded text-xs font-medium ${row.eligible ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{row.eligible ? 'Yes' : 'No'}</span></td>
                <td className="px-3 py-2 text-gray-600">{row.provider}</td>
                <td className="px-3 py-2 text-gray-500 text-xs">{row.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Tab 5: CPI Landscape ──────────────────────────────────────────────────────
function Tab5() {
  const [yearSel, setYearSel] = useState('2023');
  const [geo, setGeo] = useState('Global');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const cpiData = [
    { year: 2015, actual: 360, needed: 680 }, { year: 2016, actual: 420, needed: 750 },
    { year: 2017, actual: 490, needed: 830 }, { year: 2018, actual: 540, needed: 920 },
    { year: 2019, actual: 620, needed: 1020 }, { year: 2020, actual: 630, needed: 1120 },
    { year: 2021, actual: 750, needed: 1250 }, { year: 2022, actual: 1030, needed: 1380 },
    { year: 2023, actual: 1300, needed: 1500 }, { year: 2024, actual: null, needed: 1650 },
    { year: 2025, actual: null, needed: 1800 }, { year: 2030, actual: null, needed: 2400 },
  ].map((d, i) => ({ ...d, actual: d.actual ? Math.round(d.actual * (0.9 + rng(i, seed + 40) * 0.2)) : null }));

  const instrumentBreakdown = [
    { inst: 'Project finance debt', value: Math.round(rng(0, seed + 41) * 150 + 350) },
    { inst: 'Corporate finance', value: Math.round(rng(1, seed + 41) * 120 + 250) },
    { inst: 'Green bonds', value: Math.round(rng(2, seed + 41) * 100 + 200) },
    { inst: 'Public budget', value: Math.round(rng(3, seed + 41) * 80 + 150) },
    { inst: 'Concessional finance', value: Math.round(rng(4, seed + 41) * 60 + 80) },
  ];

  const hundredBnData = [
    { year: 2016, committed: 58 }, { year: 2017, committed: 71 }, { year: 2018, committed: 79 },
    { year: 2019, committed: 80 }, { year: 2020, committed: 83 }, { year: 2021, committed: 89 },
    { year: 2022, committed: 116 }, { year: 2023, committed: 115 },
  ].map((d, i) => ({ ...d, committed: Math.round(d.committed * (0.9 + rng(i, seed + 42) * 0.2)) }));

  const handleReport = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/climate-finance/report', { year: parseInt(yearSel), geography: geo });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [yearSel, geo]);

  return (
    <div>
      <Section title="CPI Parameters">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Sel label="Year" value={yearSel} onChange={e => setYearSel(e.target.value)}>
            {[2019,2020,2021,2022,2023].map(y => <option key={y}>{y}</option>)}
          </Sel>
          <Sel label="Geography" value={geo} onChange={e => setGeo(e.target.value)}>
            {GEOGRAPHIES.map(g => <option key={g}>{g}</option>)}
          </Sel>
        </div>
        <Btn onClick={handleReport} disabled={loading}>{loading ? 'Loading…' : 'Generate CPI Report'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Total Climate Finance" value="$1.3T" sub={`${yearSel} CPI Global Landscape`} />
        <KpiCard label="Gap to $2.4T Need" value="$1.1T" sub="Annual investment gap" />
        <KpiCard label="Mitigation Share" value="92%" sub="vs 8% adaptation" />
        <KpiCard label="$100B Commitment" value={hundredBnData[hundredBnData.length - 1].committed >= 100 ? 'Met' : 'Not met'} sub="UNFCCC developed country pledge" />
      </Row>
      <Section title="Global Climate Finance vs Need 2015–2030 ($B/yr)">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={cpiData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip formatter={v => v != null ? `$${v}B` : 'Projected'} />
            <Legend />
            <Area type="monotone" dataKey="needed" stroke="#ef4444" fill="#fee2e2" name="Investment Needed" strokeDasharray="5 5" />
            <Area type="monotone" dataKey="actual" stroke="#059669" fill="#d1fae5" name="Actual Finance" />
          </AreaChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Instrument Breakdown ($B)">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={instrumentBreakdown}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="inst" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={50} />
            <YAxis />
            <Tooltip formatter={v => `$${v}B`} />
            <Bar dataKey="value" fill="#0284c7" name="Volume ($B)" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Developed Country $100B Commitment ($B/yr)">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={hundredBnData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis domain={[40, 130]} />
            <Tooltip formatter={v => `$${v}B`} />
            <Line type="monotone" dataKey="committed" stroke="#7c3aed" strokeWidth={2} dot name="Committed ($B)" />
          </LineChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ClimateFinancePage() {
  const [activeTab, setActiveTab] = useState(0);
  const tabComponents = [Tab1, Tab2, Tab3, Tab4, Tab5];
  const ActiveComp = tabComponents[activeTab];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Climate Finance Flows</h1>
          <p className="text-sm text-gray-500 mt-1">OECD CRS Rio Markers · UNFCCC Art 2.1(c) · CPI Global Landscape 2023 · NCQG $300bn/yr COP29 · Private Mobilisation · E78</p>
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
