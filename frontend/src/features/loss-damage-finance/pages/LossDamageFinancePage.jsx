/**
 * LossDamageFinancePage.jsx  —  E70
 * Route: /loss-damage-finance
 * Tabs: FRLD Eligibility | Parametric Insurance Design | WIM Access Assessment | L&D Gap Analysis | L&D Portfolio
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const API = 'http://localhost:8001/api/v1/loss-damage';
const COLORS = ['#059669','#0891b2','#d97706','#6366f1','#dc2626','#0d9488','#7c3aed','#ea580c'];

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

const TABS = ['FRLD Eligibility','Parametric Insurance Design','WIM Access Assessment','L&D Gap Analysis','L&D Portfolio'];
const LOSS_COUNTRIES = ['Bangladesh','Barbados','Fiji','Grenada','Kenya','Malawi','Maldives','Mozambique','Nepal','Pakistan','Philippines','Solomon Islands','Tuvalu','Vanuatu','Zambia'];
const LOSS_EVENT_TYPES = ['cyclone','flood','drought','sea level rise','slow onset','compound'];
const TRIGGER_INDICES = ['wind speed','rainfall','temperature','sea level','drought','flood depth'];
const PAYOUT_STRUCTURES = ['binary','linear','step'];
const WIM_FUNCTIONS = ['risk knowledge','retention & transfer','rehabilitation'];
const ACCESS_TIERS = ['SIDS','LDC','Developing'];

// ── Tab 1: FRLD Eligibility ────────────────────────────────────────────────
function FRLDEligibility() {
  const [form, setForm] = useState({ country:'Fiji', event_type:'cyclone', economic_loss:'2500000000', non_economic_loss:'Displacement of 50,000 households, loss of cultural heritage sites' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    frld_score: parseFloat((0.55+r(1)*0.42).toFixed(2)),
    access_tier: ACCESS_TIERS[Math.floor(r(2)*3)],
    indicative_allocation: Math.round(parseFloat(form.economic_loss||'2.5e9') * (0.05+r(3)*0.15)),
    v20_member: r(4) > 0.3,
    chart_data: LOSS_COUNTRIES.slice(0,10).map((c,i)=>({
      country: c.slice(0,6),
      score: parseFloat((0.4+r(i+10)*0.55).toFixed(2)),
      event: LOSS_EVENT_TYPES[i%LOSS_EVENT_TYPES.length],
    })),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/frld-eligibility`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="FRLD Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Sel label="Country" options={LOSS_COUNTRIES} value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
          <Sel label="Loss Event Type" options={LOSS_EVENT_TYPES} value={form.event_type} onChange={e=>setForm({...form,event_type:e.target.value})}/>
          <Inp label="Economic Loss (USD)" value={form.economic_loss} onChange={e=>setForm({...form,economic_loss:e.target.value})}/>
          <Inp label="Non-Economic Loss Description" value={form.non_economic_loss} onChange={e=>setForm({...form,non_economic_loss:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Assessing…':'Assess FRLD Eligibility'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="FRLD Eligibility Score" value={d.frld_score} sub="Fund for Resp. & Loss & Damage" color="emerald"/>
        <KpiCard label="Access Tier" value={d.access_tier} sub="Eligibility classification" color="emerald"/>
        <KpiCard label="Indicative Allocation" value={`$${(d.indicative_allocation/1e6).toFixed(0)}M`} sub="Estimated FRLD allocation" color="emerald"/>
        <KpiCard label="V20 Member" value={d.v20_member?'Yes':'No'} sub="Vulnerable 20 Group" color={d.v20_member?'emerald':'red'}/>
      </div>
      <Section title="FRLD Eligibility Scores by Country/Event Type">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={d.chart_data} margin={{bottom:40}}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="country" tick={{fontSize:10}} angle={-30} textAnchor="end"/>
            <YAxis domain={[0,1]} tick={{fontSize:11}}/>
            <Tooltip formatter={(v,n,p)=>[v,'FRLD Score']}/>
            <Bar dataKey="score" radius={[4,4,0,0]} name="FRLD Score">
              {d.chart_data.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2: Parametric Insurance Design ────────────────────────────────────
function ParametricInsuranceDesign() {
  const [form, setForm] = useState({ country:'Philippines', trigger_index:'wind speed', trigger_threshold:'130', payout_structure:'linear' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const threshold = parseFloat(form.trigger_threshold) || 130;
  const fallback = {
    max_payout: Math.round(50e6 + r(1)*200e6),
    annual_premium: Math.round(2e6 + r(2)*8e6),
    basis_risk: parseFloat((0.15+r(3)*0.4).toFixed(2)),
    coverage_ratio: Math.round(60+r(4)*35),
    payout_curve: Array.from({length:20},(_,i)=>{
      const v = threshold * 0.5 + i*(threshold*1.5/19);
      let payout = 0;
      if (form.payout_structure==='binary') payout = v>=threshold ? 100 : 0;
      else if (form.payout_structure==='linear') payout = Math.min(100, Math.max(0, (v-threshold*0.8)/(threshold*0.4)*100));
      else payout = v<threshold*0.8 ? 0 : v<threshold ? 25 : v<threshold*1.2 ? 75 : 100;
      return { trigger_value: parseFloat(v.toFixed(1)), payout_pct: parseFloat(payout.toFixed(1)) };
    }),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/parametric-design`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Insurance Design Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Sel label="Country" options={LOSS_COUNTRIES} value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
          <Sel label="Trigger Index" options={TRIGGER_INDICES} value={form.trigger_index} onChange={e=>setForm({...form,trigger_index:e.target.value})}/>
          <Inp label="Trigger Threshold" value={form.trigger_threshold} onChange={e=>setForm({...form,trigger_threshold:e.target.value})}/>
          <Sel label="Payout Structure" options={PAYOUT_STRUCTURES} value={form.payout_structure} onChange={e=>setForm({...form,payout_structure:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Designing…':'Design Policy'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Max Payout" value={`$${(d.max_payout/1e6).toFixed(0)}M`} sub="Maximum trigger payout" color="emerald"/>
        <KpiCard label="Annual Premium" value={`$${(d.annual_premium/1e6).toFixed(1)}M`} sub="Annual cost of coverage" color="emerald"/>
        <KpiCard label="Basis Risk Score" value={d.basis_risk} sub="Mismatch risk 0–1" color="red"/>
        <KpiCard label="Coverage Ratio" value={`${d.coverage_ratio}%`} sub="Losses covered by policy" color="emerald"/>
      </div>
      <Section title="Payout Curve vs Trigger Index Value">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={d.payout_curve}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="trigger_value" tick={{fontSize:10}} label={{value:'Trigger Value',position:'insideBottom',offset:-5,fontSize:11}}/>
            <YAxis domain={[0,100]} tick={{fontSize:11}} label={{value:'Payout %',angle:-90,position:'insideLeft',fontSize:11}}/>
            <Tooltip formatter={v=>[`${v}%`,'Payout']}/>
            <Line type="monotone" dataKey="payout_pct" stroke="#059669" strokeWidth={2.5} dot={false} name="Payout (%)"/>
          </LineChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 3: WIM Access Assessment ──────────────────────────────────────────
function WIMAccessAssessment() {
  const [form, setForm] = useState({ country:'Vanuatu', wim_function:'risk knowledge' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const fallback = {
    wim_score: parseFloat((0.4+r(1)*0.55).toFixed(2)),
    santiago_eligible: r(2) > 0.35,
    ta_priority: ['high','medium','low'][Math.floor(r(3)*3)],
    knowledge_platform: r(4) > 0.3,
    radar: [
      {axis:'Risk Knowledge',score:parseFloat((0.4+r(5)*0.55).toFixed(2))},
      {axis:'Risk Reduction',score:parseFloat((0.35+r(6)*0.6).toFixed(2))},
      {axis:'Risk Retention',score:parseFloat((0.3+r(7)*0.65).toFixed(2))},
      {axis:'Risk Transfer',score:parseFloat((0.4+r(8)*0.55).toFixed(2))},
      {axis:'Rehabilitation',score:parseFloat((0.25+r(9)*0.7).toFixed(2))},
      {axis:'Capacity Building',score:parseFloat((0.35+r(10)*0.6).toFixed(2))},
    ],
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/wim-access`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="WIM Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Sel label="Country" options={LOSS_COUNTRIES} value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
          <Sel label="WIM Function Focus" options={WIM_FUNCTIONS} value={form.wim_function} onChange={e=>setForm({...form,wim_function:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Assessing…':'Assess WIM Access'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="WIM Access Score" value={d.wim_score} sub="Warsaw Mechanism access" color="emerald"/>
        <KpiCard label="Santiago Network" value={d.santiago_eligible?'Eligible':'Ineligible'} sub="Technical assistance network" color={d.santiago_eligible?'emerald':'red'}/>
        <KpiCard label="TA Priority" value={d.ta_priority.toUpperCase()} sub="Technical assistance priority" color={d.ta_priority==='high'?'red':d.ta_priority==='medium'?'emerald':'emerald'}/>
        <KpiCard label="Knowledge Platform" value={d.knowledge_platform?'Active':'Pending'} sub="WIM Knowledge Platform access" color={d.knowledge_platform?'emerald':'red'}/>
      </div>
      <Section title="WIM 6-Function Assessment Radar">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={d.radar}>
            <PolarGrid stroke="#e5e7eb"/>
            <PolarAngleAxis dataKey="axis" tick={{fontSize:11}}/>
            <PolarRadiusAxis domain={[0,1]} tick={{fontSize:9}}/>
            <Radar name={form.country} dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.25}/>
            <Tooltip formatter={v=>[v,'WIM Score']}/>
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 4: L&D Gap Analysis ────────────────────────────────────────────────
function LDGapAnalysis() {
  const [form, setForm] = useState({ country:'Bangladesh', total_loss:'15000000000', insurance_pct:'8', govt_budget:'500000000' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.country || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const totalLoss = parseFloat(form.total_loss||'15e9');
  const insPct = parseFloat(form.insurance_pct||'8')/100;
  const govtBudget = parseFloat(form.govt_budget||'5e8');
  const insured = Math.round(totalLoss * insPct);
  const frld_eligible = Math.round(totalLoss * (0.05+r(1)*0.1));
  const residual = Math.round(totalLoss - insured - frld_eligible - govtBudget);
  const fallback = {
    total_ld: totalLoss,
    insured,
    frld_eligible,
    residual: Math.max(0, residual),
    stacked_data: LOSS_COUNTRIES.slice(0,10).map((c,i)=>{
      const loss = Math.round(1e9 + r(i+5)*20e9);
      const ins_share = Math.round(loss * (0.03+r(i+20)*0.15));
      const frld_share = Math.round(loss * (0.03+r(i+30)*0.1));
      const govt_share = Math.round(loss * (0.02+r(i+40)*0.08));
      const residual_share = loss - ins_share - frld_share - govt_share;
      return { country: c.slice(0,7), insured: ins_share/1e9, frld: frld_share/1e9, govt: govt_share/1e9, residual: Math.max(0,residual_share)/1e9 };
    }),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/ld-gap-analysis`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;
  function fmtB(n) { return `$${(n/1e9).toFixed(1)}B`; }

  return (
    <div>
      <Section title="Gap Analysis Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Sel label="Country" options={LOSS_COUNTRIES} value={form.country} onChange={e=>setForm({...form,country:e.target.value})}/>
          <Inp label="Total Economic Loss (USD)" value={form.total_loss} onChange={e=>setForm({...form,total_loss:e.target.value})}/>
          <Inp label="Insurance Coverage (%)" value={form.insurance_pct} onChange={e=>setForm({...form,insurance_pct:e.target.value})}/>
          <Inp label="Govt Budget Allocation (USD)" value={form.govt_budget} onChange={e=>setForm({...form,govt_budget:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Analysing…':'Analyse Gap'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total L&D" value={fmtB(d.total_ld)} sub="Total economic loss" color="red"/>
        <KpiCard label="Insurance Covered" value={fmtB(d.insured)} sub="Indemnity payout" color="emerald"/>
        <KpiCard label="FRLD Eligible" value={fmtB(d.frld_eligible)} sub="Fund allocation estimate" color="emerald"/>
        <KpiCard label="Residual Gap" value={fmtB(d.residual)} sub="Uncovered losses" color="red"/>
      </div>
      <Section title="Stacked L&D Gap — Insured vs FRLD vs Govt vs Residual (USD Bn)">
        <ResponsiveContainer width="100%" height={270}>
          <BarChart data={d.stacked_data} margin={{bottom:30}}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="country" tick={{fontSize:10}} angle={-30} textAnchor="end"/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`$${v.toFixed(1)}B`]}/>
            <Legend/>
            <Bar dataKey="insured" stackId="a" fill="#059669" name="Insured"/>
            <Bar dataKey="frld" stackId="a" fill="#0891b2" name="FRLD"/>
            <Bar dataKey="govt" stackId="a" fill="#d97706" name="Govt"/>
            <Bar dataKey="residual" stackId="a" fill="#dc2626" name="Residual Gap"/>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 5: L&D Portfolio ───────────────────────────────────────────────────
function LDPortfolio() {
  const [form, setForm] = useState({ portfolio:'Climate Vulnerability Fund' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.portfolio || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const REGIONS = ['Pacific','Caribbean','Africa','Asia','Other'];
  const fallback = {
    portfolio_exposure: 42.3e9,
    v20_concentration: Math.round(45+r(1)*40),
    parametric_coverage: Math.round(25+r(2)*45),
    frld_coverage: Math.round(15+r(3)*35),
    cumulative: REGIONS.map((reg,i)=>({ region: reg, exposure: parseFloat((2+r(i+5)*18).toFixed(1)) })),
    loss_breakdown: [
      {name:'Economic',value:Math.round(40+r(10)*25)},
      {name:'Non-Economic',value:Math.round(20+r(11)*20)},
      {name:'Slow Onset',value:Math.round(15+r(12)*25)},
    ],
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/ld-portfolio`, form);
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
        <KpiCard label="Portfolio L&D Exposure" value={`$${(d.portfolio_exposure/1e9).toFixed(1)}B`} sub="Total exposure at risk" color="red"/>
        <KpiCard label="V20 Concentration" value={`${d.v20_concentration}%`} sub="Vulnerable 20 share" color="red"/>
        <KpiCard label="Parametric Coverage" value={`${d.parametric_coverage}%`} sub="Parametric insurance ratio" color="emerald"/>
        <KpiCard label="FRLD Coverage" value={`${d.frld_coverage}%`} sub="FRLD fund coverage ratio" color="emerald"/>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <Section title="Cumulative L&D Exposure by Region (USD Bn)">
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={d.cumulative}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
              <XAxis dataKey="region" tick={{fontSize:11}}/>
              <YAxis tick={{fontSize:11}}/>
              <Tooltip formatter={v=>[`$${v}B`,'Exposure']}/>
              <Area type="monotone" dataKey="exposure" stroke="#059669" fill="#d1fae5" name="Exposure ($Bn)"/>
            </AreaChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Loss Type Breakdown">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={d.loss_breakdown} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({name,value})=>`${name}: ${value}%`}>
                {d.loss_breakdown.map((_,i)=><Cell key={i} fill={COLORS[i]}/>)}
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
export default function LossDamageFinancePage() {
  const [activeTab, setActiveTab] = useState(0);
  const panels = [FRLDEligibility, ParametricInsuranceDesign, WIMAccessAssessment, LDGapAnalysis, LDPortfolio];
  const Panel = panels[activeTab];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Loss & Damage Finance</h1>
          <p className="text-sm text-gray-500 mt-1">FRLD eligibility · Parametric insurance · WIM access · L&D gap analysis · Portfolio analytics</p>
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
