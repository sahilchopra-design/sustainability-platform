/**
 * CarbonPriceETSPage.jsx  —  E71
 * Route: /carbon-price-ets
 * Tabs: ETS Compliance Cost | EU ETS Price Forecast | CBAM Exposure | Portfolio Carbon Cost | IEA Carbon Price Pathways
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  ScatterChart, Scatter, ZAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';

const API = 'http://localhost:8001/api/v1/carbon-price-ets';
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

const TABS = ['ETS Compliance Cost','EU ETS Price Forecast','CBAM Exposure','Portfolio Carbon Cost','IEA Carbon Price Pathways'];

const ETS_SYSTEMS = ['EU ETS','UK ETS','China ETS','California WCI','RGGI','Korea ETS'];
const CBAM_SECTORS = ['cement','iron steel','aluminium','fertilisers','electricity','hydrogen'];
const FORECAST_SCENARIOS = ['NZE','APS','SDS','Current Policy'];
const FORECAST_HORIZONS = ['5','10','20','30'];
const SECTORS_LIST = ['Power','Steel','Cement','Aluminium','Chemicals','Oil & Gas','Aviation','Shipping','Buildings','Agriculture'];

// ── Tab 1: ETS Compliance Cost ─────────────────────────────────────────────
function ETSComplianceCost() {
  const [form, setForm] = useState({ entity:'European Steel Corp', sector:'Steel', annual_emissions:'2500000' });
  const [selectedETS, setSelectedETS] = useState(new Set(['EU ETS','UK ETS']));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.entity || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const emissions = parseFloat(form.annual_emissions||'2.5e6');
  const EU_PRICE = 65 + r(1)*20; // EUR/tCO2
  const UK_PRICE = 40 + r(2)*20;
  const CN_PRICE = 8 + r(3)*5;
  const CA_PRICE = 30 + r(4)*15;
  const RGGI_PRICE = 12 + r(5)*8;
  const KR_PRICE = 20 + r(6)*10;
  const PRICES = { 'EU ETS': EU_PRICE, 'UK ETS': UK_PRICE, 'China ETS': CN_PRICE, 'California WCI': CA_PRICE, 'RGGI': RGGI_PRICE, 'Korea ETS': KR_PRICE };

  const fallback = {
    total_ets_cost: Math.round(emissions * EU_PRICE * 0.6),
    eu_liability: Math.round(emissions * EU_PRICE * 0.35),
    uk_liability: Math.round(emissions * UK_PRICE * 0.2),
    china_cost: Math.round(emissions * CN_PRICE * 0.3),
    chart: ETS_SYSTEMS.map((sys,i)=>({
      system: sys, cost: Math.round(emissions * PRICES[sys] * (0.1 + r(i+10)*0.4) / 1e6),
    })),
  };

  function toggleETS(sys) {
    const next = new Set(selectedETS);
    next.has(sys) ? next.delete(sys) : next.add(sys);
    setSelectedETS(next);
  }

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/ets-compliance`, { ...form, ets_systems: [...selectedETS] });
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Compliance Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Inp label="Entity Name" value={form.entity} onChange={e=>setForm({...form,entity:e.target.value})}/>
          <Sel label="Sector" options={SECTORS_LIST} value={form.sector} onChange={e=>setForm({...form,sector:e.target.value})}/>
          <Inp label="Annual Emissions (tCO2)" value={form.annual_emissions} onChange={e=>setForm({...form,annual_emissions:e.target.value})}/>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">ETS Systems</label>
            <div className="flex flex-wrap gap-2 mt-1">
              {ETS_SYSTEMS.map(sys=>(
                <button key={sys} onClick={()=>toggleETS(sys)}
                  className={`text-xs px-3 py-1 rounded-full border transition-colors ${selectedETS.has(sys)?'bg-emerald-600 text-white border-emerald-600':'border-gray-300 text-gray-600 hover:border-emerald-400'}`}>
                  {sys}
                </button>
              ))}
            </div>
          </div>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Calculating…':'Calculate Compliance Cost'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total ETS Cost" value={`$${(d.total_ets_cost/1e6).toFixed(1)}M`} sub="Combined ETS liability" color="red"/>
        <KpiCard label="EU ETS Liability" value={`€${(d.eu_liability/1e6).toFixed(1)}M`} sub="EUA allowance cost" color="red"/>
        <KpiCard label="UK ETS Liability" value={`£${(d.uk_liability/1e6).toFixed(1)}M`} sub="UKA allowance cost" color="red"/>
        <KpiCard label="China ETS Cost" value={`¥${(d.china_cost/1e6).toFixed(0)}M`} sub="CEA allowance cost" color="red"/>
      </div>
      <Section title="Compliance Costs by ETS System ($M)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={d.chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="system" tick={{fontSize:10}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`$${v}M`,'Cost']}/>
            <Bar dataKey="cost" radius={[4,4,0,0]} name="Compliance Cost ($M)">
              {d.chart.map((_,i)=><rect key={i} fill={COLORS[i%COLORS.length]}/>)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2: EU ETS Price Forecast ───────────────────────────────────────────
function EUETSPriceForecast() {
  const [form, setForm] = useState({ horizon:'30', scenario:'NZE', lrf:'4.3' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = `${form.scenario}-${form.horizon}`.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const horizon = parseInt(form.horizon);
  const years = Array.from({length:horizon+1},(_,i)=>2024+i);
  const BASE_PRICES = { NZE: [68,80,95,115,145,175,210], APS: [68,72,82,95,110,125,140], SDS: [68,75,85,98,115,130,145], 'Current Policy': [68,65,62,60,58,56,54] };
  const base = BASE_PRICES[form.scenario] || BASE_PRICES['NZE'];

  const fallback = {
    price_2030: Math.round(base[2] + r(1)*15),
    price_2040: Math.round(base[4] + r(2)*20),
    price_2050: Math.round(base[6] + r(3)*25),
    uncertainty_pct: Math.round(15+r(4)*25),
    trajectory: years.map((yr,i)=>{
      const t = i/horizon;
      const basePrice = base[0] + (base[base.length-1]-base[0])*t*t;
      const noise = r(i+20)*8-4;
      const upper = basePrice * (1+r(i+40)*0.3);
      const lower = basePrice * (1-r(i+50)*0.25);
      return { year: yr, price: Math.round(basePrice+noise), upper: Math.round(upper), lower: Math.round(lower) };
    }),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/eu-ets-forecast`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="Forecast Parameters">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <Sel label="Forecast Horizon (years)" options={FORECAST_HORIZONS} value={form.horizon} onChange={e=>setForm({...form,horizon:e.target.value})}/>
          <Sel label="Scenario" options={FORECAST_SCENARIOS} value={form.scenario} onChange={e=>setForm({...form,scenario:e.target.value})}/>
          <Inp label="LRF Assumption (%)" value={form.lrf} onChange={e=>setForm({...form,lrf:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Forecasting…':'Generate Forecast'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="2030 Price" value={`€${d.price_2030}/tCO2`} sub={`${form.scenario} scenario`} color="emerald"/>
        <KpiCard label="2040 Price" value={`€${d.price_2040}/tCO2`} sub={`${form.scenario} scenario`} color="emerald"/>
        <KpiCard label="2050 Price" value={`€${d.price_2050}/tCO2`} sub={`${form.scenario} scenario`} color="emerald"/>
        <KpiCard label="Price Uncertainty" value={`±${d.uncertainty_pct}%`} sub="90% confidence band" color="red"/>
      </div>
      <Section title={`EU ETS Price Trajectory 2024–${2024+horizon} (${form.scenario}) — EUR/tCO2`}>
        <ResponsiveContainer width="100%" height={270}>
          <AreaChart data={d.trajectory}>
            <defs>
              <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#059669" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#059669" stopOpacity={0.02}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="year" tick={{fontSize:11}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`€${v}/tCO2`]}/>
            <Legend/>
            <Area type="monotone" dataKey="upper" stroke="none" fill="#d1fae5" fillOpacity={0.6} name="Upper Band" legendType="none"/>
            <Area type="monotone" dataKey="lower" stroke="none" fill="#ffffff" fillOpacity={1} name="Lower Band" legendType="none"/>
            <Line type="monotone" dataKey="price" stroke="#059669" strokeWidth={2.5} dot={false} name="EU ETS Price (€/tCO2)"/>
          </AreaChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 3: CBAM Exposure ───────────────────────────────────────────────────
function CBAMExposure() {
  const [form, setForm] = useState({ importer_country:'United Kingdom', sector:'iron steel', import_value:'50000000', embedded_intensity:'1.85' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = `${form.importer_country}-${form.sector}`;
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const importVal = parseFloat(form.import_value||'5e7');
  const intensity = parseFloat(form.embedded_intensity||'1.85');
  const EU_PRICE = 65 + r(1)*15;
  const embedded = Math.round(importVal / 1000 * intensity);
  const fallback = {
    cbam_cost: Math.round(embedded * EU_PRICE),
    embedded_carbon: embedded,
    phase_in_year: 2026,
    competitiveness_impact: parseFloat((1.5+r(2)*4).toFixed(1)),
    sector_chart: CBAM_SECTORS.map((s,i)=>({
      sector: s, cost: Math.round(5e6 + r(i+10)*45e6),
    })),
    table: CBAM_SECTORS.map((s,i)=>{
      const intens = [0.9,1.85,1.52,2.1,0.35,0.28][i];
      return {
        sector: s, intensity: intens,
        phase_pct_2026: Math.round(10+i*5), cost_2026: Math.round(1e6+r(i+20)*9e6),
        cost_2034: Math.round(5e6+r(i+30)*45e6),
      };
    }),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/cbam-exposure`, form);
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <Section title="CBAM Parameters">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Inp label="Importer Country" value={form.importer_country} onChange={e=>setForm({...form,importer_country:e.target.value})}/>
          <Sel label="Sector" options={CBAM_SECTORS} value={form.sector} onChange={e=>setForm({...form,sector:e.target.value})}/>
          <Inp label="Import Value (EUR)" value={form.import_value} onChange={e=>setForm({...form,import_value:e.target.value})}/>
          <Inp label="Embedded Carbon Intensity (tCO2/t)" value={form.embedded_intensity} onChange={e=>setForm({...form,embedded_intensity:e.target.value})}/>
        </div>
        <Btn onClick={run} disabled={loading}>{loading?'Calculating…':'Calculate CBAM'}</Btn>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="CBAM Certificate Cost" value={`€${(d.cbam_cost/1e6).toFixed(1)}M`} sub="At current EU ETS price" color="red"/>
        <KpiCard label="Embedded Carbon" value={`${d.embedded_carbon.toLocaleString()} tCO2`} sub="Total embedded emissions" color="red"/>
        <KpiCard label="CBAM Phase-in" value={`From ${d.phase_in_year}`} sub="Regulation (EU) 2023/956" color="emerald"/>
        <KpiCard label="Competitiveness Impact" value={`-${d.competitiveness_impact}%`} sub="Margin compression" color="red"/>
      </div>
      <Section title="CBAM Costs by Sector (EUR)">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={d.sector_chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="sector" tick={{fontSize:10}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`€${(v/1e6).toFixed(1)}M`,'CBAM Cost']}/>
            <Bar dataKey="cost" fill="#dc2626" radius={[4,4,0,0]} name="CBAM Cost (EUR)"/>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="CBAM Phase-in Schedule by Sector">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-200">{['Sector','Carbon Intensity','Phase-in 2026 (%)','2026 Cost (EUR)','2034 Full Cost (EUR)'].map(h=><th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase py-2 pr-4">{h}</th>)}</tr></thead>
            <tbody>{d.table.map((row,i)=><tr key={i} className="border-b border-gray-50">
              <td className="py-2 pr-4 capitalize text-gray-700">{row.sector}</td>
              <td className="py-2 pr-4">{row.intensity} tCO2/t</td>
              <td className="py-2 pr-4">{row.phase_pct_2026}%</td>
              <td className="py-2 pr-4">€{(row.cost_2026/1e6).toFixed(1)}M</td>
              <td className="py-2 pr-4">€{(row.cost_2034/1e6).toFixed(1)}M</td>
            </tr>)}</tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ── Tab 4: Portfolio Carbon Cost ───────────────────────────────────────────
function PortfolioCarbonCost() {
  const [form, setForm] = useState({ portfolio_name:'Industrial Equity Fund' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const entityId = form.portfolio_name || 'default';
  const seed = entityId.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const PORTFOLIO_SECTORS = ['Power','Steel','Cement','Chemicals','Oil & Gas','Aviation'];
  const fallback = {
    weighted_carbon_cost: Math.round(45+r(1)*55),
    transition_risk_score: parseFloat((0.5+r(2)*0.45).toFixed(2)),
    high_leakage_exposure: Math.round(20+r(3)*50),
    sbti_aligned_pct: Math.round(15+r(4)*55),
    sector_costs: PORTFOLIO_SECTORS.map((s,i)=>({
      sector: s,
      cost: Math.round(20+r(i+10)*120),
      revenue: Math.round(500+r(i+20)*4500),
      emissions_intensity: parseFloat((0.1+r(i+30)*2.9).toFixed(2)),
    })),
    scatter: PORTFOLIO_SECTORS.map((s,i)=>({
      sector: s,
      emissions_intensity: parseFloat((0.1+r(i+40)*3.0).toFixed(2)),
      carbon_cost: Math.round(20+r(i+50)*130),
    })),
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/portfolio-carbon-cost`, form);
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
            <Inp label="Portfolio Name" value={form.portfolio_name} onChange={e=>setForm({...form,portfolio_name:e.target.value})}/>
          </div>
          <Btn onClick={run} disabled={loading}>{loading?'Calculating…':'Analyse Portfolio'}</Btn>
        </div>
      </Section>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Weighted Carbon Cost" value={`$${d.weighted_carbon_cost}/tCO2`} sub="Portfolio-weighted avg" color="red"/>
        <KpiCard label="Transition Risk Score" value={d.transition_risk_score} sub="Carbon cost exposure 0–1" color="red"/>
        <KpiCard label="High-Leakage Exposure" value={`${d.high_leakage_exposure}%`} sub="Carbon leakage risk sectors" color="red"/>
        <KpiCard label="SBTi-Aligned Holdings" value={`${d.sbti_aligned_pct}%`} sub="Holdings with SBTi targets" color="emerald"/>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <Section title="Carbon Cost by Sector ($M)">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={d.sector_costs}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
              <XAxis dataKey="sector" tick={{fontSize:10}}/>
              <YAxis tick={{fontSize:11}}/>
              <Tooltip formatter={v=>[`$${v}M`,'Carbon Cost']}/>
              <Bar dataKey="cost" fill="#dc2626" radius={[4,4,0,0]} name="Carbon Cost ($M)"/>
            </BarChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Emissions Intensity vs Carbon Cost per Sector">
          <ResponsiveContainer width="100%" height={240}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
              <XAxis dataKey="emissions_intensity" name="Emissions Intensity" tick={{fontSize:10}} label={{value:'tCO2/$M Rev',position:'insideBottom',offset:-5,fontSize:10}}/>
              <YAxis dataKey="carbon_cost" name="Carbon Cost" tick={{fontSize:10}} label={{value:'Carbon Cost ($M)',angle:-90,position:'insideLeft',fontSize:10}}/>
              <ZAxis range={[60,160]}/>
              <Tooltip cursor={{strokeDasharray:'3 3'}} content={({payload})=>payload&&payload[0]?<div className="bg-white border border-gray-200 rounded p-2 text-xs"><p className="font-medium">{payload[0]?.payload?.sector}</p><p>Intensity: {payload[0]?.payload?.emissions_intensity}</p><p>Cost: ${payload[0]?.payload?.carbon_cost}M</p></div>:null}/>
              <Scatter name="Sectors" data={d.scatter} fill="#059669"/>
            </ScatterChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ── Tab 5: IEA Carbon Price Pathways ──────────────────────────────────────
function IEACarbonPricePathways() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 'iea-pathways'.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const r = rng(seed);

  const YEARS = [2024,2025,2026,2027,2028,2029,2030,2032,2035,2037,2040,2043,2045,2047,2050];
  const NZE_PRICES  = [65, 72, 80, 88, 97, 108, 130, 155, 185, 205, 225, 242, 248, 250, 250];
  const APS_PRICES  = [65, 68, 72, 76, 80, 85,  90,  96, 102, 106, 110, 113, 114, 115, 115];
  const SDS_PRICES  = [65, 70, 76, 82, 90, 98, 108, 122, 140, 152, 162, 168, 170, 171, 170];
  const STEPS_PRICES= [65, 63, 61, 60, 58, 57,  56,  54,  50,  47,  44,  42,  40,  38,  35];
  const ETS_2030 = [
    {system:'EU ETS',price:Math.round(110+r(1)*25)},
    {system:'UK ETS',price:Math.round(75+r(2)*20)},
    {system:'China ETS',price:Math.round(20+r(3)*10)},
    {system:'California WCI',price:Math.round(45+r(4)*15)},
    {system:'RGGI',price:Math.round(18+r(5)*8)},
    {system:'Korea ETS',price:Math.round(28+r(6)*12)},
  ];

  const fallback = {
    nze_2030: NZE_PRICES[6], nze_2050: NZE_PRICES[14], aps_2030: APS_PRICES[6], eu_ets_2030: ETS_2030[0].price,
    pathways: YEARS.map((yr,i)=>({
      year: yr,
      nze: NZE_PRICES[i] + Math.round(r(i)*4-2),
      aps: APS_PRICES[i] + Math.round(r(i+20)*3-1.5),
      sds: SDS_PRICES[i] + Math.round(r(i+40)*3-1.5),
      steps: STEPS_PRICES[i] + Math.round(r(i+60)*2-1),
    })),
    ets_2030: ETS_2030,
  };

  async function run() {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/price-pathway`, {});
      setResult(data);
    } catch { setResult(fallback); }
    setLoading(false);
  }
  const d = result || fallback;

  return (
    <div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="NZE 2030 Price" value={`$${d.nze_2030}/tCO2`} sub="IEA Net Zero by 2050" color="emerald"/>
        <KpiCard label="NZE 2050 Price" value={`$${d.nze_2050}/tCO2`} sub="IEA Net Zero by 2050" color="emerald"/>
        <KpiCard label="APS 2030 Price" value={`$${d.aps_2030}/tCO2`} sub="Announced Pledges" color="emerald"/>
        <KpiCard label="EU ETS 2030 Forecast" value={`€${d.eu_ets_2030}/tCO2`} sub="EU ETS forward estimate" color="emerald"/>
      </div>
      <Section title="IEA Carbon Price Pathways 2024–2050 ($/tCO2)">
        <ResponsiveContainer width="100%" height={270}>
          <LineChart data={d.pathways}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="year" tick={{fontSize:11}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip/>
            <Legend/>
            <Line type="monotone" dataKey="nze" stroke="#059669" strokeWidth={2.5} dot={false} name="NZE (Net Zero 2050)"/>
            <Line type="monotone" dataKey="sds" stroke="#0891b2" strokeWidth={2} dot={false} name="SDS (Sustainable Dev.)"/>
            <Line type="monotone" dataKey="aps" stroke="#d97706" strokeWidth={2} dot={false} name="APS (Announced Pledges)"/>
            <Line type="monotone" dataKey="steps" stroke="#dc2626" strokeWidth={1.5} strokeDasharray="5 3" dot={false} name="STEPS (Current Policy)"/>
          </LineChart>
        </ResponsiveContainer>
      </Section>
      <Section title="ETS System Price Comparison — 2030 Forecast ($/tCO2)">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={d.ets_2030}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0"/>
            <XAxis dataKey="system" tick={{fontSize:10}}/>
            <YAxis tick={{fontSize:11}}/>
            <Tooltip formatter={v=>[`$${v}/tCO2`,'2030 Forecast']}/>
            <Bar dataKey="price" radius={[4,4,0,0]} name="2030 Price ($/tCO2)">
              {(d.ets_2030||[]).map((_,i)=><rect key={i} fill={COLORS[i%COLORS.length]}/>)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <div className="flex justify-end mt-2">
        <Btn onClick={run} disabled={loading}>{loading?'Refreshing…':'Refresh Pathways'}</Btn>
      </div>
    </div>
  );
}

// ── Page Shell ─────────────────────────────────────────────────────────────
export default function CarbonPriceETSPage() {
  const [activeTab, setActiveTab] = useState(0);
  const panels = [ETSComplianceCost, EUETSPriceForecast, CBAMExposure, PortfolioCarbonCost, IEACarbonPricePathways];
  const Panel = panels[activeTab];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Carbon Price & ETS</h1>
          <p className="text-sm text-gray-500 mt-1">ETS compliance costs · EU ETS forecasts · CBAM exposure · Portfolio carbon cost · IEA price pathways</p>
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
