/**
 * SovereignDebtClimatePage.jsx  —  E69
 * Route: /sovereign-debt-climate
 * Tabs: CRDC Assessment | Debt-for-Nature Swaps | IMF RST Eligibility | SIDS Vulnerability | Sovereign Portfolio
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const API = 'http://localhost:8001/api/v1/sovereign-debt-climate';
const COLORS = ['#059669','#0891b2','#d97706','#6366f1','#dc2626','#0d9488'];

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

const TABS = ['CRDC Assessment','Debt-for-Nature Swaps','IMF RST Eligibility','SIDS Vulnerability','Sovereign Portfolio'];

const COUNTRIES_15 = ['Bangladesh','Barbados','Belize','Dominican Republic','Ecuador','Fiji','Grenada','Jamaica','Kenya','Maldives','Mozambique','Pakistan','Philippines','Senegal','Zambia'];
const TRIGGER_TYPES = ['cyclone wind','rainfall','temperature','sea level','drought'];
const DN_FRAMEWORKS = ['bilateral','multilateral','commercial','Paris Club'];
const RST_CATEGORIES = ['climate resilience','social protection','energy transition','fiscal reform','debt sustainability'];
const SIDS_LIST = ['Barbados','Belize','Fiji','Grenada','Jamaica','Maldives','Marshall Islands','Palau','Samoa','Tonga','Tuvalu','Vanuatu'];

// ── Tab 1: CRDC Assessment ─────────────────────────────────────────────────
function CRDCAssessment() {
  const [form, setForm] = useState({ country:'Barbados', debt_amount:'2000000000', maturity:'10', trigger:'cyclone wind' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    crdc_eligible: r(1) > 0.25,
    trigger_threshold: form.trigger==='cyclone wind' ? 'Category 3 (≥120 km/h)' : form.trigger==='rainfall' ? '< 25% seasonal normal' : '> 38°C for 14 days',
    deferred_amount: Math.round(parseFloat(form.debt_amount||'2e9') * (0.1 + r(2)*0.15)),
    trigger_prob: parseFloat((0.05+r(3)*0.25).toFixed(3)),
    chart_data: COUNTRIES_15.slice(0,10).map((c,i)=>({ country: c.slice(0,8), deferred: Math.round(200+r(i+10)*1800) })),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/crdc-assessment`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="CRDC Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Sel label="Country" options={COUNTRIES_15} value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
          <Inp label="Debt Amount (USD)" value={form.debt_amount} onChange={e=>setForm({...form,debt_amount:e.target.value})}/>
          <Inp label="Debt Maturity (years)" value={form.maturity} onChange={e=>setForm({...form,maturity:e.target.value})}/>
          <Sel label="Trigger Type" options={TRIGGER_TYPES} value={form.trigger} onChange={e=>setForm({...form,trigger:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Assessing…':'Assess CRDC Eligibility'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="CRDC Eligible" value={d.crdc_eligible?'Yes':'No'} sub="Climate-Resilient Debt Clause" color={d.crdc_eligible?'emerald':'red'}/>
        <KpiCard label="Trigger Threshold" value={d.trigger_threshold} sub="Activation condition" color="emerald"/>
        <KpiCard label="Deferred Amount" value={`$${(d.deferred_amount/1e6).toFixed(0)}M`} sub="Debt service deferred" color="emerald"/>
        <KpiCard label="Trigger Probability" value={`${(d.trigger_prob*100).toFixed(1)}%`} sub="Annual event probability" color="emerald"/>
      </div>
      <Section title="Deferred Amounts by Country (USD M)">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={d.chart_data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="country" tick={{fontSize:10}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`$${v}M`,'Deferred']}/>
            <Bar dataKey="deferred" fill="#059669" radius={[4,4,0,0]} name="Deferred ($M)"/>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2: Debt-for-Nature Swaps ───────────────────────────────────────────
function DebtForNatureSwaps() {
  const [form, setForm] = useState({ country:'Ecuador', debt_face:'3000000000', conservation_ha:'500000', framework:'bilateral' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    swap_discount: parseFloat((0.2+r(1)*0.45).toFixed(3)),
    conservation_value: Math.round(parseFloat(form.conservation_ha||'500000') * (800+r(2)*1200)),
    swap_amount: Math.round(parseFloat(form.debt_face||'3e9') * (0.2+r(1)*0.45)),
    imf_mdb: r(3) > 0.4,
    table: COUNTRIES_15.slice(0,6).map((c,i)=>({
      country: c, debt_face: Math.round(1e9+r(i+5)*5e9),
      discount: parseFloat((0.2+r(i+20)*0.45).toFixed(2)),
      conservation_ha: Math.round(100000+r(i+30)*900000),
      co_benefits: ['marine','forest','wetland','savanna','coral','watershed'][i],
    })),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/debt-for-nature`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Swap Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Sel label="Country" options={COUNTRIES_15} value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
          <Inp label="Debt Face Value (USD)" value={form.debt_face} onChange={e=>setForm({...form,debt_face:e.target.value})}/>
          <Inp label="Conservation Commitment (ha)" value={form.conservation_ha} onChange={e=>setForm({...form,conservation_ha:e.target.value})}/>
          <Sel label="Framework" options={DN_FRAMEWORKS} value={form.framework} onChange={e=>setForm({...form,framework:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Calculating…':'Calculate Swap'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Swap Discount" value={`${(d.swap_discount*100).toFixed(1)}%`} sub="Haircut on face value" color="emerald"/>
        <KpiCard label="Conservation Value" value={`$${(d.conservation_value/1e9).toFixed(2)}B`} sub="Ecosystem services" color="emerald"/>
        <KpiCard label="Swap Amount" value={`$${(d.swap_amount/1e6).toFixed(0)}M`} sub="Swapped at discount" color="emerald"/>
        <KpiCard label="IMF/MDB Involvement" value={d.imf_mdb?'Yes':'No'} sub="Multilateral support" color={d.imf_mdb?'emerald':'red'}/>
      </div>
      <Section title="Debt-for-Nature Swap Comparison">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-200">{['Country','Debt Face (USD)','Discount','Conservation Ha','Co-benefits'].map(h=><th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase py-2 pr-4">{h}</th>)}</tr></thead>
            <tbody>{d.table.map((row,i)=><tr key={i} className="border-b border-gray-50">
              <td className="py-2 pr-4 text-gray-700">{row.country}</td>
              <td className="py-2 pr-4">${(row.debt_face/1e9).toFixed(1)}B</td>
              <td className="py-2 pr-4">{(row.discount*100).toFixed(0)}%</td>
              <td className="py-2 pr-4">{row.conservation_ha.toLocaleString()}</td>
              <td className="py-2 pr-4 capitalize text-emerald-700">{row.co_benefits}</td>
            </tr>)}</tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ── Tab 3: IMF RST Eligibility ─────────────────────────────────────────────
function IMFRSTEligibility() {
  const [form, setForm] = useState({ country:'Kenya', gdp:'110000000000', rst_category:'climate resilience' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    rst_score: parseFloat((0.5+r(1)*0.45).toFixed(2)),
    access_pct_gdp: parseFloat((0.5+r(2)*1.5).toFixed(2)),
    reform_count: Math.round(3+r(3)*5),
    est_allocation: Math.round(parseFloat(form.gdp||'1.1e11') * (0.005+r(4)*0.015)),
    top12: COUNTRIES_15.slice(0,12).map((c,i)=>({ country: c.slice(0,8), score: parseFloat((0.45+r(i+10)*0.5).toFixed(2)) })),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/imf-rst`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="RST Parameters">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <Sel label="Country" options={COUNTRIES_15} value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
          <Inp label="GDP (USD)" value={form.gdp} onChange={e=>setForm({...form,gdp:e.target.value})}/>
          <Sel label="RST Reform Category" options={RST_CATEGORIES} value={form.rst_category} onChange={e=>setForm({...form,rst_category:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Assessing…':'Assess RST Eligibility'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="RST Access Score" value={d.rst_score} sub="0–1 eligibility score" color="emerald"/>
        <KpiCard label="Access Limit" value={`${d.access_pct_gdp}% GDP`} sub="IMF RST access limit" color="emerald"/>
        <KpiCard label="Reform Measures" value={d.reform_count} sub="Required measures" color="emerald"/>
        <KpiCard label="Est. Allocation" value={`$${(d.est_allocation/1e9).toFixed(1)}B`} sub="Estimated RST allocation" color="emerald"/>
      </div>
      <Section title="RST Access Scores — Top 12 Eligible Countries">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={d.top12} margin={{bottom:40}}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="country" tick={{fontSize:10}} angle={-35} textAnchor="end"/>
            <YAxis domain={[0,1]} tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[v,'RST Score']}/>
            <Bar dataKey="score" fill="#0891b2" radius={[4,4,0,0]} name="RST Score"/>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 4: SIDS Vulnerability ──────────────────────────────────────────────
function SIDSVulnerability() {
  const [country, setCountry] = useState('Barbados');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    vulnerability_index: parseFloat((0.5+r(1)*0.45).toFixed(2)),
    inform_risk: parseFloat((3+r(2)*6).toFixed(1)),
    nd_gain: parseFloat((30+r(3)*50).toFixed(1)),
    fiscal_resilience: parseFloat((0.3+r(4)*0.65).toFixed(2)),
    cdpc_eligible: r(5) > 0.35,
    radar: [
      {axis:'Physical Risk',score:parseFloat((0.4+r(6)*0.55).toFixed(2))},
      {axis:'Social Vuln.',score:parseFloat((0.35+r(7)*0.6).toFixed(2))},
      {axis:'Coping Capacity',score:parseFloat((0.3+r(8)*0.65).toFixed(2))},
      {axis:'Fiscal Resilience',score:parseFloat((0.4+r(9)*0.55).toFixed(2))},
      {axis:'NDC Ambition',score:parseFloat((0.3+r(10)*0.65).toFixed(2))},
    ],
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/sids-vulnerability`, { country });
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="SIDS Country Selection">
        <div className="flex items-end gap-4 mb-4">
          <div className="w-64">
            <Sel label="Select SIDS Country" options={SIDS_LIST} value={country} onChange={e=>setCountry(e.target.value)}/>
          </div>
          <Btn onClick={run} disabled={loading}>{loading?'Analysing…':'Analyse Vulnerability'}</Btn>
        </div>
      </Section>
      <div className="grid grid-cols-5 gap-4 mb-6">
        <KpiCard label="Vulnerability Index" value={d.vulnerability_index} sub="Composite 0–1" color="red"/>
        <KpiCard label="INFORM Risk Score" value={d.inform_risk} sub="0–10 scale" color="red"/>
        <KpiCard label="ND-GAIN Score" value={d.nd_gain} sub="Readiness score" color="emerald"/>
        <KpiCard label="Fiscal Resilience" value={d.fiscal_resilience} sub="0–1 score" color="emerald"/>
        <KpiCard label="CDPC Eligible" value={d.cdpc_eligible?'Yes':'No'} sub="Climate Debt Relief" color={d.cdpc_eligible?'emerald':'red'}/>
      </div>
      <Section title="SIDS 5-Axis Vulnerability Assessment">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={d.radar}>
            <PolarGrid stroke="#e5e7eb"/>
            <PolarAngleAxis dataKey="axis" tick={{fontSize:12}}/>
            <PolarRadiusAxis domain={[0,1]} tick={{fontSize:9}}/>
            <Radar name={country} dataKey="score" stroke="#dc2626" fill="#dc2626" fillOpacity={0.2}/>
            <Tooltip formatter={v=>[v,'Score']}/>
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 5: Sovereign Portfolio ─────────────────────────────────────────────
function SovereignPortfolio() {
  const [form, setForm] = useState({ portfolio:'Climate-Linked Sovereign Fund' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.portfolio || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const COUNTRIES_8 = COUNTRIES_15.slice(0,8);
  const fallback = {
    total_exposure: 18.4e9,
    crdc_eligibility_pct: Math.round(45+r(1)*40),
    avg_sids_vulnerability: parseFloat((0.55+r(2)*0.3).toFixed(2)),
    dfn_swap_potential: Math.round(5e9+r(3)*10e9),
    climate_metrics: COUNTRIES_8.map((c,i)=>({ country: c.slice(0,8), crdc: Math.round(300+r(i+5)*1700), dfn: Math.round(100+r(i+20)*900) })),
    score_series: COUNTRIES_8.map((c,i)=>({ country: c.slice(0,8), climate_score: parseFloat((0.4+r(i+30)*0.55).toFixed(2)), conv_rating: parseFloat((0.3+r(i+40)*0.6).toFixed(2)) })),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/sovereign-portfolio`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Portfolio Parameters">
        <div className="flex items-end gap-4 mb-4">
          <div className="flex-1">
            <Inp label="Portfolio Name" value={form.portfolio} onChange={e=>setForm({...form,portfolio:e.target.value})}/>
          </div>
          <Btn onClick={run} disabled={loading}>{loading?'Calculating…':'Analyse Portfolio'}</Btn>
        </div>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total Sovereign Exposure" value={`$${(d.total_exposure/1e9).toFixed(1)}B`} sub="Climate-linked sovereign debt" color="emerald"/>
        <KpiCard label="CRDC Eligibility" value={`${d.crdc_eligibility_pct}%`} sub="Weighted portfolio %" color="emerald"/>
        <KpiCard label="Avg SIDS Vulnerability" value={d.avg_sids_vulnerability} sub="Weighted avg 0–1" color="red"/>
        <KpiCard label="DfN Swap Potential" value={`$${(d.dfn_swap_potential/1e9).toFixed(1)}B`} sub="Total swap pipeline" color="emerald"/>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <Section title="Climate-Linked Debt Metrics by Country ($M)">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={d.climate_metrics}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
              <XAxis dataKey="country" tick={{fontSize:10}}/>
              <YAxis tick={{fontSize:11}}/>
              <Tooltip formatter={v=>[`$${v}M`]}/>
              <Legend/>
              <Bar dataKey="crdc" fill="#059669" name="CRDC ($M)" radius={[4,4,0,0]}/>
              <Bar dataKey="dfn" fill="#0891b2" name="DfN Swap ($M)" radius={[4,4,0,0]}/>
            </BarChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Climate Debt Score vs Conventional Rating">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={d.score_series}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
              <XAxis dataKey="country" tick={{fontSize:10}}/>
              <YAxis domain={[0,1]} tick={{fontSize:11}}/>
              <Tooltip/>
              <Legend/>
              <Line type="monotone" dataKey="climate_score" stroke="#059669" name="Climate Score" strokeWidth={2} dot={{r:4}}/>
              <Line type="monotone" dataKey="conv_rating" stroke="#6366f1" name="Conv. Rating" strokeWidth={2} dot={{r:4}}/>
            </LineChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ── Page Shell ─────────────────────────────────────────────────────────────
export default function SovereignDebtClimatePage() {
  const [activeTab, setActiveTab] = useState(0);
  const panels = [CRDCAssessment, DebtForNatureSwaps, IMFRSTEligibility, SIDSVulnerability, SovereignPortfolio];
  const Panel = panels[activeTab];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Sovereign Debt & Climate Finance</h1>
          <p className="text-sm text-gray-500 mt-1">CRDC clauses · Debt-for-nature swaps · IMF RST · SIDS vulnerability · Sovereign portfolio analytics</p>
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
