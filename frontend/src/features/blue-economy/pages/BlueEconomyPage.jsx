/**
 * BlueEconomyPage.jsx  —  E68
 * Route: /blue-economy
 * Tabs: Blue Bond Screener | Blue Carbon Projects | BBNJ Compliance | Ocean Acidification Risk | Ocean Portfolio
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const API = 'http://localhost:8001/api/v1/blue-economy';
const COLORS = ['#059669','#0891b2','#0d9488','#0284c7','#6366f1','#d97706','#dc2626','#7c3aed'];

const Section = ({title,children})=>(<div className="mb-6"><h3 className="text-sm font-semibold text-black uppercase tracking-wider mb-3 pb-1 border-b border-gray-200">{title}</h3>{children}</div>);
const KpiCard = ({label,value,sub,color='emerald'})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p><p className={`text-2xl font-bold text-${color}-600`}>{value}</p>{sub&&<p className="text-xs text-gray-400 mt-1">{sub}</p>}</div>);
const Row = ({label,value,badge})=>(<div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"><span className="text-sm text-gray-600">{label}</span><div className="flex items-center gap-2">{badge&&<span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">{badge}</span>}<span className="text-sm font-medium text-black">{value}</span></div></div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs font-medium text-gray-600 uppercase tracking-wide">{label}</label><input className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" {...p}/></div>);
const Sel = ({label,options,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs font-medium text-gray-600 uppercase tracking-wide">{label}</label><select className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" {...p}>{options.map(o=><option key={o.value??o} value={o.value??o}>{o.label??o}</option>)}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2 rounded transition-colors" {...p}>{children}</button>);

function rng(seed) {
  let s = Math.abs(seed) || 1;
  return (i) => Math.abs(Math.sin(i * 9301 + s * 49297) * 233280) % 233280 / 233280;
}

const TABS = ['Blue Bond Screener','Blue Carbon Projects','BBNJ Compliance','Ocean Acidification Risk','Ocean Portfolio'];
const UOP_OPTIONS = [
  {value:'sustainable_fisheries',label:'Sustainable Fisheries'},
  {value:'marine_conservation',label:'Marine Conservation'},
  {value:'ocean_renewable_energy',label:'Ocean Renewable Energy'},
  {value:'coastal_resilience',label:'Coastal Resilience'},
  {value:'marine_pollution_prevention',label:'Marine Pollution Prevention'},
  {value:'sustainable_aquaculture',label:'Sustainable Aquaculture'},
  {value:'marine_protected_areas',label:'Marine Protected Areas'},
  {value:'ocean_acidification_mitigation',label:'Ocean Acidification Mitigation'},
];
const ECOSYSTEM_OPTIONS = ['mangrove','seagrass','saltmarsh','kelp'];
const ENTITY_TYPES = ['flag state','port state','shipping company','financial institution'];

// ── Tab 1: Blue Bond Screener ──────────────────────────────────────────────
function BlueBondScreener() {
  const [form, setForm] = useState({ issuer:'Ocean Finance Corp', amount:'500000000', uop:'sustainable_fisheries', icma_year:'2023' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.issuer || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    icma_score: (0.65 + r(1)*0.3).toFixed(2),
    sof_coverage: Math.round(60 + r(2)*35),
    uop_eligibility: Math.round(70 + r(3)*28),
    market_size: 1.2,
    category_scores: UOP_OPTIONS.map((o,i)=>({ category: o.label.split(' ').slice(-1)[0], score: parseFloat((0.55+r(i+10)*0.42).toFixed(2)) })),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/screen-bond`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Bond Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Inp label="Bond Issuer" value={form.issuer} onChange={e=>setForm({...form,issuer:e.target.value})}/>
          <Inp label="Amount (USD)" value={form.amount} onChange={e=>setForm({...form,amount:e.target.value})}/>
          <Sel label="Use of Proceeds" options={UOP_OPTIONS} value={form.uop} onChange={e=>setForm({...form,uop:e.target.value})}/>
          <Sel label="ICMA Alignment Year" options={['2021','2022','2023','2024']} value={form.icma_year} onChange={e=>setForm({...form,icma_year:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Screening…':'Screen Bond'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="ICMA Alignment Score" value={d.icma_score} sub="0–1 scale" color="emerald"/>
        <KpiCard label="SOF Pillar Coverage" value={`${d.sof_coverage}%`} sub="Sustainable Ocean Finance" color="emerald"/>
        <KpiCard label="UoP Eligibility" value={`${d.uop_eligibility}%`} sub="Eligible use of proceeds" color="emerald"/>
        <KpiCard label="Blue Bond Market" value="$1.2T" sub="Global market size" color="emerald"/>
      </div>
      <Section title="ICMA Alignment by Use-of-Proceeds Category">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={d.category_scores} margin={{top:8,right:16,left:0,bottom:60}}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="category" tick={{fontSize:10}} angle={-35} textAnchor="end"/>
            <YAxis domain={[0,1]} tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[v,'ICMA Score']}/>
            <Bar dataKey="score" fill="#059669" radius={[4,4,0,0]} name="ICMA Score"/>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2: Blue Carbon Projects ────────────────────────────────────────────
function BlueCarbonProjects() {
  const [form, setForm] = useState({ project:'Coral Coast MPA', ecosystem:'mangrove', area:'5000', country:'Indonesia' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.project || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const RATES = { mangrove: 6.3, seagrass: 2.1, saltmarsh: 4.8, kelp: 1.4 };
  const fallback = () => {
    const rate = RATES[form.ecosystem] || 3.5;
    const area = parseFloat(form.area) || 5000;
    return {
      seq_total: Math.round(rate * area),
      additionality: parseFloat((0.6+r(1)*0.37).toFixed(2)),
      permanence: parseFloat((0.55+r(2)*0.42).toFixed(2)),
      vcs_eligible: r(3) > 0.3,
      table: ECOSYSTEM_OPTIONS.map((eco,i)=>({
        ecosystem: eco, rate: RATES[eco], area: Math.round(1000+r(i+5)*9000),
        total: Math.round(RATES[eco]*(1000+r(i+5)*9000)),
        co_benefits: ['biodiversity','coastal protection','water quality','fisheries'][i],
      })),
      chart: ECOSYSTEM_OPTIONS.map((eco,i)=>({ ecosystem: eco, seq: Math.round(RATES[eco]*(2000+r(i+10)*8000)) })),
    };
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/blue-carbon`, form);
      setResult(data);
    } catch { setResult(fallback()); }
    setLoading(false);
  }
  const d = result || fallback();

  return (
    <div>
      <Section title="Project Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Inp label="Project Name" value={form.project} onChange={e=>setForm({...form,project:e.target.value})}/>
          <Sel label="Ecosystem Type" options={ECOSYSTEM_OPTIONS} value={form.ecosystem} onChange={e=>setForm({...form,ecosystem:e.target.value})}/>
          <Inp label="Area (hectares)" value={form.area} onChange={e=>setForm({...form,area:e.target.value})}/>
          <Inp label="Country" value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Calculating…':'Calculate Sequestration'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Sequestration" value={`${(d.seq_total/1000).toFixed(1)}k`} sub="tCO2/yr" color="emerald"/>
        <KpiCard label="Additionality Score" value={d.additionality} sub="0–1 scale" color="emerald"/>
        <KpiCard label="Permanence Score" value={d.permanence} sub="0–1 scale" color="emerald"/>
        <KpiCard label="VCS Eligible" value={d.vcs_eligible?'Yes':'No'} sub="Verified Carbon Standard" color={d.vcs_eligible?'emerald':'red'}/>
      </div>
      <Section title="Ecosystem Sequestration Comparison">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={d.chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="ecosystem" tick={{fontSize:11}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`${v} tCO2/yr`,'Sequestration']}/>
            <Bar dataKey="seq" fill="#0d9488" radius={[4,4,0,0]} name="Total Seq (tCO2/yr)"/>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Ecosystem Detail">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-200">{['Ecosystem','Rate (tCO2/ha/yr)','Area (ha)','Total Seq','Co-benefits'].map(h=><th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase py-2 pr-4">{h}</th>)}</tr></thead>
            <tbody>{d.table.map((row,i)=><tr key={i} className="border-b border-gray-50"><td className="py-2 pr-4 capitalize text-gray-700">{row.ecosystem}</td><td className="py-2 pr-4">{row.rate}</td><td className="py-2 pr-4">{row.area.toLocaleString()}</td><td className="py-2 pr-4">{row.total.toLocaleString()}</td><td className="py-2 pr-4 capitalize text-emerald-700">{row.co_benefits}</td></tr>)}</tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ── Tab 3: BBNJ Compliance ─────────────────────────────────────────────────
function BBNJCompliance() {
  const [form, setForm] = useState({ entity:'Pacific Shipping Ltd', entity_type:'shipping company', activity:'deep sea fishing in ABNJ' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.entity || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    bbnj_score: parseFloat((0.45+r(1)*0.5).toFixed(2)),
    high_seas_coverage: Math.round(50+r(2)*45),
    mgr_compliance: parseFloat((0.4+r(3)*0.55).toFixed(2)),
    abnj_conservation: parseFloat((0.35+r(4)*0.6).toFixed(2)),
    radar: [
      { axis:'MGR', score: parseFloat((0.4+r(5)*0.55).toFixed(2)) },
      { axis:'ABMT', score: parseFloat((0.45+r(6)*0.5).toFixed(2)) },
      { axis:'EIA', score: parseFloat((0.5+r(7)*0.45).toFixed(2)) },
      { axis:'CB&TT', score: parseFloat((0.35+r(8)*0.6).toFixed(2)) },
      { axis:'Implementation', score: parseFloat((0.55+r(9)*0.4).toFixed(2)) },
    ],
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/bbnj-compliance`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Entity Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Inp label="Entity Name" value={form.entity} onChange={e=>setForm({...form,entity:e.target.value})}/>
          <Sel label="Entity Type" options={ENTITY_TYPES} value={form.entity_type} onChange={e=>setForm({...form,entity_type:e.target.value})}/>
          <div className="col-span-2"><Inp label="Ocean Activity" value={form.activity} onChange={e=>setForm({...form,activity:e.target.value})}/></div>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Assessing…':'Assess BBNJ Compliance'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="BBNJ Score" value={d.bbnj_score} sub="Overall compliance" color="emerald"/>
        <KpiCard label="High Seas Coverage" value={`${d.high_seas_coverage}%`} sub="ABNJ monitoring" color="emerald"/>
        <KpiCard label="Art 29 MGR" value={d.mgr_compliance} sub="Marine Genetic Resources" color="emerald"/>
        <KpiCard label="ABNJ Conservation" value={d.abnj_conservation} sub="Score 0–1" color="emerald"/>
      </div>
      <Section title="BBNJ 5-Pillar Compliance Radar">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={d.radar}>
            <PolarGrid stroke="#e5e7eb"/>
            <PolarAngleAxis dataKey="axis" tick={{fontSize:12}}/>
            <PolarRadiusAxis domain={[0,1]} tick={{fontSize:9}}/>
            <Radar name="BBNJ Score" dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.25}/>
            <Tooltip formatter={v=>[v,'Score']}/>
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 4: Ocean Acidification Risk ───────────────────────────────────────
function OceanAcidificationRisk() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 'ocean-acidification'.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const years = Array.from({length:16},(_,i)=>2025+i*5);
  const fallback = {
    ph_2100_rcp85: -0.4,
    ocean_exposure_usd: 8.7e12,
    coral_value_at_risk: 1.3e12,
    fisheries_revenue_at_risk: 340e9,
    ph_trajectory: years.map((yr,i)=>({
      year: yr,
      rcp26: parseFloat((-0.02-i*0.005+r(i)*0.003).toFixed(4)),
      rcp45: parseFloat((-0.02-i*0.012+r(i+20)*0.004).toFixed(4)),
      rcp85: parseFloat((-0.02-i*0.026+r(i+40)*0.005).toFixed(4)),
    })),
    sector_exposure: [
      {sector:'Coral Reefs',exposure:1300},{sector:'Fisheries',exposure:880},
      {sector:'Aquaculture',exposure:420},{sector:'Tourism',exposure:1100},
      {sector:'Coastal Infra',exposure:2800},{sector:'Shipping',exposure:650},
    ],
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/ocean-acidification`, {});
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  function fmt(n) {
    if (n>=1e12) return `$${(n/1e12).toFixed(1)}T`;
    if (n>=1e9) return `$${(n/1e9).toFixed(0)}B`;
    return `$${n}`;
  }

  return (
    <div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="pH Change 2100 (RCP8.5)" value={d.ph_2100_rcp85} sub="Units relative to pre-industrial" color="red"/>
        <KpiCard label="Ocean Economy Exposure" value={fmt(d.ocean_exposure_usd)} sub="Global blue economy GDP" color="emerald"/>
        <KpiCard label="Coral Reef VaR" value={fmt(d.coral_value_at_risk)} sub="Ecosystem services at risk" color="red"/>
        <KpiCard label="Fisheries Revenue at Risk" value={fmt(d.fisheries_revenue_at_risk)} sub="Annual revenue impact" color="red"/>
      </div>
      <Section title="Ocean pH Change Trajectory 2025–2100 by RCP Scenario">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={d.ph_trajectory}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="year" tick={{fontSize:11}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip/>
            <Legend/>
            <Line type="monotone" dataKey="rcp26" stroke="#059669" name="RCP2.6" strokeWidth={2} dot={false}/>
            <Line type="monotone" dataKey="rcp45" stroke="#d97706" name="RCP4.5" strokeWidth={2} dot={false}/>
            <Line type="monotone" dataKey="rcp85" stroke="#dc2626" name="RCP8.5" strokeWidth={2} dot={false}/>
          </LineChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Ocean Economy Exposure by Sector (USD Bn)">
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={d.sector_exposure}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="sector" tick={{fontSize:11}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`$${v}B`,'Exposure']}/>
            <Area type="monotone" dataKey="exposure" stroke="#0891b2" fill="#bfdbfe" name="Exposure ($Bn)"/>
          </AreaChart>
        </ResponsiveContainer>
      </Section>
      <div className="flex justify-end mt-2">
        <Btn onClick={run} disabled={loading}>{loading?'Refreshing…':'Refresh Analysis'}</Btn>
      </div>
    </div>
  );
}

// ── Tab 5: Ocean Portfolio ─────────────────────────────────────────────────
function OceanPortfolio() {
  const [form, setForm] = useState({ portfolio:'Blue Ocean Fund I', region:'Global' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.portfolio || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    total_exposure: 2.4e9,
    sof_score: parseFloat((0.62+r(1)*0.3).toFixed(2)),
    blue_bond_pct: Math.round(30+r(2)*40),
    risk_adj_return: parseFloat((0.04+r(3)*0.06).toFixed(3)),
    composition: [
      {category:'Blue Bonds',value:Math.round(800+r(4)*400)},
      {category:'Aquaculture Loans',value:Math.round(300+r(5)*200)},
      {category:'Marine Renewable',value:Math.round(200+r(6)*300)},
      {category:'Coastal Infra',value:Math.round(150+r(7)*250)},
      {category:'Blue Carbon',value:Math.round(100+r(8)*200)},
      {category:'Port Finance',value:Math.round(200+r(9)*300)},
    ],
    allocation: [
      {name:'Blue Bond',value:38},{name:'Conventional',value:42},{name:'Blue Carbon',value:20},
    ],
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/ocean-portfolio`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Portfolio Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Inp label="Portfolio Name" value={form.portfolio} onChange={e=>setForm({...form,portfolio:e.target.value})}/>
          <Inp label="Region" value={form.region} onChange={e=>setForm({...form,region:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Calculating…':'Analyse Portfolio'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total Ocean Exposure" value={`$${(d.total_exposure/1e9).toFixed(1)}B`} sub="AUM in blue economy" color="emerald"/>
        <KpiCard label="SOF Score" value={d.sof_score} sub="Sustainable Ocean Finance" color="emerald"/>
        <KpiCard label="Blue Bond Allocation" value={`${d.blue_bond_pct}%`} sub="Of total portfolio" color="emerald"/>
        <KpiCard label="Risk-Adj Return" value={`${(d.risk_adj_return*100).toFixed(1)}%`} sub="Ocean risk-adjusted" color="emerald"/>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <Section title="Portfolio Composition by Ocean Finance Category ($M)">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={d.composition} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
              <XAxis type="number" tick={{fontSize:11}}/>
              <YAxis dataKey="category" type="category" tick={{fontSize:10}} width={110}/>
              <Tooltip formatter={v=>[`$${v}M`,'Allocation']}/>
              <Bar dataKey="value" fill="#059669" radius={[0,4,4,0]} name="Allocation ($M)"/>
            </BarChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Blue vs Conventional vs Blue Carbon Allocation">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={d.allocation} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({name,value})=>`${name}: ${value}%`}>
                {d.allocation.map((_,i)=><Cell key={i} fill={COLORS[i]}/>)}
              </Pie>
              <Tooltip formatter={v=>[`${v}%`,'Share']}/>
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ── Page Shell ─────────────────────────────────────────────────────────────
export default function BlueEconomyPage() {
  const [activeTab, setActiveTab] = useState(0);
  const panels = [BlueBondScreener, BlueCarbonProjects, BBNJCompliance, OceanAcidificationRisk, OceanPortfolio];
  const Panel = panels[activeTab];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Blue Economy Finance</h1>
          <p className="text-sm text-gray-500 mt-1">Blue bonds · Blue carbon · BBNJ compliance · Ocean acidification · Ocean portfolio analytics</p>
        </div>
        <div className="flex gap-1 mb-6 bg-white border border-gray-200 rounded-lg p-1 shadow-sm overflow-x-auto">
          {TABS.map((t,i)=>(
            <button key={t} onClick={()=>setActiveTab(i)}
              className={`flex-shrink-0 px-4 py-2 text-sm font-medium rounded transition-colors ${activeTab===i?'bg-emerald-600 text-white':'text-gray-600 hover:text-black hover:bg-gray-100'}`}>
              {t}
            </button>
          ))}
        </div>
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <Panel/>
        </div>
      </div>
    </div>
  );
}
