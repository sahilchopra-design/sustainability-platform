import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-black">{value}</div>{sub&&<div className="text-xs text-emerald-600 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{children}</div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}/></div>);
const Sel = ({label,children,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>);

const TABS = ['Structure Assessment','DFI Standards','Concessional Layers','Mobilisation Metrics','Portfolio View'];
const COLORS = ['#059669','#10b981','#34d399','#6ee7b7','#a7f3d0','#d1fae5'];
const seed = 42;
const rng = (i,s=seed) => Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280;

// ---------- Structure Assessment ----------
function StructureTab() {
  const [instrument, setInstrument] = useState('First Loss');
  const [projectSize, setProjectSize] = useState('50');
  const [mdb, setMdb] = useState('IFC');
  const [result, setResult] = useState(null);

  const trancheData = [
    { name: 'Senior', value: Math.round(40+rng(1)*30) },
    { name: 'Mezzanine', value: Math.round(15+rng(2)*15) },
    { name: 'First-Loss', value: Math.round(8+rng(3)*7) },
    { name: 'Grant', value: Math.round(3+rng(4)*5) },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/blended-finance/structure', { instrument, projectSize, mdb });
      setResult(r.data);
    } catch {
      setResult({
        mobilisationRatio: (2.5 + rng(5)*3).toFixed(2),
        concessionalPct: (15 + rng(6)*20).toFixed(1),
        ifcPsScore: (3.2 + rng(7)*1.5).toFixed(1),
        oecdEligible: rng(8) > 0.3 ? 'Yes' : 'Conditional',
      });
    }
  }, [instrument, projectSize, mdb]);

  return (
    <div>
      <Section title="Instrument Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Instrument Type" value={instrument} onChange={e=>setInstrument(e.target.value)}>
            {['Guarantee','First Loss','Concessional Loan','Technical Assistance','Equity'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Inp label="Project Size (USD M)" type="number" value={projectSize} onChange={e=>setProjectSize(e.target.value)} />
          <Sel label="MDB Partner" value={mdb} onChange={e=>setMdb(e.target.value)}>
            {['IFC','MIGA','EBRD','ADB','AIIB','AfDB'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <div className="flex items-end"><Btn onClick={run}>Assess Structure</Btn></div>
        </div>
      </Section>
      {result && (
        <Section title="Blended Finance KPIs">
          <Row>
            <KpiCard label="Mobilisation Ratio" value={`${result.mobilisationRatio}x`} sub="Private : Concessional" />
            <KpiCard label="Concessional Layer %" value={`${result.concessionalPct}%`} sub="of total capital stack" />
            <KpiCard label="IFC PS Score" value={`${result.ifcPsScore}/5`} sub="E&S Performance Standards" />
            <KpiCard label="OECD DAC Eligibility" value={result.oecdEligible} sub="ODA-eligible" />
          </Row>
        </Section>
      )}
      <Section title="Tranche Waterfall">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={trancheData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis unit="%" />
            <Tooltip formatter={v=>`${v}%`} />
            <Bar dataKey="value" name="Tranche %" fill="#059669">
              {trancheData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- DFI Standards ----------
function DFITab() {
  const [partner, setPartner] = useState('IFC');
  const [category, setCategory] = useState('Renewable Energy');
  const [result, setResult] = useState(null);

  const radarData = [
    { axis: 'Assessment & Mgmt', value: Math.round(60+rng(10)*35) },
    { axis: 'Working Conditions', value: Math.round(55+rng(11)*40) },
    { axis: 'Biodiversity', value: Math.round(50+rng(12)*45) },
    { axis: 'Community Health', value: Math.round(65+rng(13)*30) },
    { axis: 'Land Acquisition', value: Math.round(45+rng(14)*50) },
    { axis: 'Cultural Heritage', value: Math.round(70+rng(15)*25) },
    { axis: 'Indigenous Peoples', value: Math.round(60+rng(16)*35) },
    { axis: 'Workers', value: Math.round(75+rng(17)*20) },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/blended-finance/dfi-standards', { partner, category });
      setResult(r.data);
    } catch {
      setResult({ tier: rng(18) > 0.6 ? 'High' : rng(18) > 0.3 ? 'Medium' : 'Low', score: (65+rng(19)*30).toFixed(0) });
    }
  }, [partner, category]);

  const tierColor = t => t==='High' ? 'bg-red-100 text-red-700' : t==='Medium' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700';

  return (
    <div>
      <Section title="DFI & Project Configuration">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <Sel label="DFI Partner" value={partner} onChange={e=>setPartner(e.target.value)}>
            {['IFC','MIGA','EBRD','ADB','AIIB','AfDB','DEG','Proparco'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Sel label="Project Category" value={category} onChange={e=>setCategory(e.target.value)}>
            {['Renewable Energy','Infrastructure','Agriculture','Healthcare','Education','Financial Services'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <div className="flex items-end"><Btn onClick={run}>Assess DFI Standards</Btn></div>
        </div>
        {result && (
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-gray-600">E&S Risk Tier:</span>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${tierColor(result.tier)}`}>{result.tier}</span>
            <span className="text-sm text-gray-600">Composite Score: <strong>{result.score}/100</strong></span>
          </div>
        )}
      </Section>
      <Section title="IFC Performance Standards Radar (PS 1–8)">
        <ResponsiveContainer width="100%" height={350}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis angle={90} domain={[0,100]} />
            <Radar name="PS Score" dataKey="value" stroke="#059669" fill="#059669" fillOpacity={0.35} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- Concessional Layers ----------
function ConcessionalTab() {
  const [result, setResult] = useState(null);

  const stackData = [
    { tier: 'Deal A', senior: 45, mezzanine: 18, firstLoss: 10, grant: 5 },
    { tier: 'Deal B', senior: 52, mezzanine: 14, firstLoss: 8, grant: 4 },
    { tier: 'Deal C', senior: 38, mezzanine: 22, firstLoss: 12, grant: 7 },
    { tier: 'Deal D', senior: 60, mezzanine: 10, firstLoss: 6, grant: 3 },
  ];

  const investorPie = [
    { name: 'DFI / MDB', value: 35 },
    { name: 'Development Banks', value: 25 },
    { name: 'Commercial Banks', value: 20 },
    { name: 'Impact Funds', value: 12 },
    { name: 'Philanthropic', value: 8 },
  ];

  const returnTable = [
    { tier: 'Senior', returnTarget: '6–8%', risk: 'Low', investors: 'Commercial Banks, Institutional' },
    { tier: 'Mezzanine', returnTarget: '10–14%', risk: 'Medium', investors: 'Impact Funds, Family Offices' },
    { tier: 'First-Loss', returnTarget: '0–4%', risk: 'High', investors: 'DFIs, Foundations' },
    { tier: 'Grant', returnTarget: '0%', risk: 'Concessional', investors: 'Donor Agencies, ODA' },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/blended-finance/concessional-layers');
      setResult(r.data);
    } catch {
      setResult({ loaded: true });
    }
  }, []);

  return (
    <div>
      <div className="flex gap-3 mb-4"><Btn onClick={run}>Load Concessional Analysis</Btn></div>
      <Section title="Capital Stack by Deal (Stacked %)">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stackData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tier" />
            <YAxis unit="%" />
            <Tooltip />
            <Legend />
            <Bar dataKey="senior" name="Senior" stackId="a" fill="#059669" />
            <Bar dataKey="mezzanine" name="Mezzanine" stackId="a" fill="#10b981" />
            <Bar dataKey="firstLoss" name="First-Loss" stackId="a" fill="#34d399" />
            <Bar dataKey="grant" name="Grant" stackId="a" fill="#a7f3d0" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Return Targets by Tranche">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Tranche','Return Target','Risk Level','Target Investors'].map(h=><th key={h} className="border border-gray-200 px-3 py-2 text-left font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{returnTable.map((r,i)=><tr key={i} className="hover:bg-gray-50">{[r.tier,r.returnTarget,r.risk,r.investors].map((v,j)=><td key={j} className="border border-gray-200 px-3 py-2 text-gray-700">{v}</td>)}</tr>)}</tbody>
          </table>
        </div>
      </Section>
      <Section title="Investor Type Distribution">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={investorPie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`}>
              {investorPie.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- Mobilisation Metrics ----------
function MobilisationTab() {
  const [result, setResult] = useState(null);

  const sectors = ['Renewable Energy','Infrastructure','Agriculture','Healthcare','MSME Finance','Climate Adapt.','Clean Water','Affordable Housing'];
  const leverageData = sectors.map((s,i)=>({
    sector: s,
    actual: parseFloat((1.8+rng(i+20)*4).toFixed(2)),
    convergence: parseFloat((2.5+rng(i+28)*2).toFixed(2)),
  }));

  const crowdingData = [
    { year: '2020', crowdIn: 2.1, crowdOut: -0.3 },
    { year: '2021', crowdIn: 2.8, crowdOut: -0.5 },
    { year: '2022', crowdIn: 3.4, crowdOut: -0.4 },
    { year: '2023', crowdIn: 3.9, crowdOut: -0.6 },
    { year: '2024', crowdIn: 4.2, crowdOut: -0.7 },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/blended-finance/mobilisation-metrics');
      setResult(r.data);
    } catch {
      setResult({ additionalityScore: (68+rng(40)*25).toFixed(0) });
    }
  }, []);

  return (
    <div>
      <div className="flex gap-3 mb-4"><Btn onClick={run}>Run Mobilisation Analysis</Btn></div>
      {result && (
        <Row>
          <KpiCard label="Additionality Score" value={`${result.additionalityScore}/100`} sub="Convergence benchmark" />
          <KpiCard label="Avg Leverage Ratio" value={`${(3.2+rng(41)*1.5).toFixed(1)}x`} sub="Private per $1 concessional" />
          <KpiCard label="Blended Finance Deals" value={`${Math.round(12+rng(42)*20)}`} sub="Active portfolio" />
          <KpiCard label="Total Mobilised" value={`$${(450+rng(43)*300).toFixed(0)}M`} sub="USD, 2024" />
        </Row>
      )}
      <Section title="Sector Leverage Ratios vs Convergence Benchmarks">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={leverageData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" unit="x" />
            <YAxis type="category" dataKey="sector" width={130} tick={{fontSize:11}} />
            <Tooltip formatter={v=>`${v}x`} />
            <Legend />
            <Bar dataKey="actual" name="Actual Ratio" fill="#059669" />
            <Bar dataKey="convergence" name="Convergence Benchmark" fill="#34d399" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Crowding-In vs Crowding-Out Effect">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={crowdingData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis unit="x" />
            <Tooltip />
            <Legend />
            <Bar dataKey="crowdIn" name="Crowd-In" fill="#059669" />
            <Bar dataKey="crowdOut" name="Crowd-Out" fill="#f87171" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- Portfolio View ----------
function PortfolioTab() {
  const [result, setResult] = useState(null);

  const scatterData = Array.from({length:16},(_,i)=>({
    risk: parseFloat((20+rng(i+50)*60).toFixed(1)),
    return: parseFloat((4+rng(i+66)*14).toFixed(1)),
    name: `Deal ${i+1}`,
  }));

  const sdgData = [
    {sdg:'SDG 1 No Poverty',value:18},{sdg:'SDG 2 Zero Hunger',value:12},{sdg:'SDG 6 Clean Water',value:15},
    {sdg:'SDG 7 Clean Energy',value:28},{sdg:'SDG 8 Decent Work',value:10},{sdg:'SDG 13 Climate',value:25},
    {sdg:'SDG 17 Partnerships',value:22},
  ];

  const instrumentPie = [
    {name:'Guarantee',value:28},{name:'First Loss',value:22},{name:'Concessional Loan',value:30},
    {name:'Tech Assistance',value:12},{name:'Equity',value:8},
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/blended-finance/portfolio');
      setResult(r.data);
    } catch {
      setResult({
        totalDeals: Math.round(24+rng(80)*12),
        avgIrr: (8.5+rng(81)*4).toFixed(1),
        sdg13Pct: (35+rng(82)*25).toFixed(0),
        totalAum: (1.2+rng(83)*0.8).toFixed(2),
      });
    }
  }, []);

  return (
    <div>
      <div className="flex gap-3 mb-4"><Btn onClick={run}>Load Portfolio</Btn></div>
      {result && (
        <Row>
          <KpiCard label="Active Deals" value={result.totalDeals} sub="Blended finance portfolio" />
          <KpiCard label="Avg Blended IRR" value={`${result.avgIrr}%`} sub="Portfolio weighted" />
          <KpiCard label="SDG 13 Alignment" value={`${result.sdg13Pct}%`} sub="Climate action focus" />
          <KpiCard label="Total AUM" value={`$${result.totalAum}B`} sub="Blended capital deployed" />
        </Row>
      )}
      <Section title="Risk-Return Scatter">
        <ResponsiveContainer width="100%" height={280}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="risk" name="Risk Score" unit="%" label={{value:'Risk Score',position:'insideBottom',offset:-5}} />
            <YAxis dataKey="return" name="IRR" unit="%" label={{value:'IRR %',angle:-90,position:'insideLeft'}} />
            <Tooltip cursor={{strokeDasharray:'3 3'}} />
            <Scatter data={scatterData} fill="#059669" />
          </ScatterChart>
        </ResponsiveContainer>
      </Section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="SDG Alignment (Deal Count)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={sdgData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="sdg" width={120} tick={{fontSize:10}} />
              <Tooltip />
              <Bar dataKey="value" fill="#059669" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Instruments Mix">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={instrumentPie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`}>
                {instrumentPie.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ---------- Main ----------
export default function BlendedFinancePage() {
  const [tab, setTab] = useState(0);
  const panels = [<StructureTab/>,<DFITab/>,<ConcessionalTab/>,<MobilisationTab/>,<PortfolioTab/>];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Blended Finance &amp; DFI Instruments</h1>
          <p className="text-sm text-gray-500 mt-1">IFC Performance Standards · Concessional Layers · First-Loss · Mobilisation Ratios · OECD DAC · Convergence 2023</p>
        </div>
        <div className="flex gap-2 mb-6 border-b border-gray-200 overflow-x-auto">
          {TABS.map((t,i)=>(
            <button key={i} onClick={()=>setTab(i)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors ${tab===i?'border-b-2 border-emerald-600 text-emerald-700':'text-gray-500 hover:text-gray-700'}`}>
              {t}
            </button>
          ))}
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          {panels[tab]}
        </div>
      </div>
    </div>
  );
}
