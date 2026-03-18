import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-black">{value}</div>{sub&&<div className="text-xs text-emerald-600 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{children}</div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}/></div>);
const Sel = ({label,children,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>);

const TABS = ['Lock-In Risk','Capex Transition Plan','Retrofit NPV','Brown-to-Green Portfolio','Decarbonisation Roadmap'];
const COLORS = ['#059669','#10b981','#34d399','#6ee7b7','#f59e0b','#ef4444'];
const seed = 74;
const rng = (i,s=seed) => Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280;

const YEARS = [2024,2026,2028,2030,2032,2034,2036,2038,2040,2042,2044,2046,2048,2050];

// ---------- Lock-In Risk ----------
function LockInTab() {
  const [assetType, setAssetType] = useState('Building');
  const [age, setAge] = useState('15');
  const [result, setResult] = useState(null);

  const crremData = YEARS.map((y,i)=>({
    year: y,
    current: parseFloat((280 - i*8 - rng(i)*5).toFixed(1)),
    pathway: parseFloat((250 - i*14 + rng(i+20)*3).toFixed(1)),
  }));

  const scenarios = ['BAU','1.5°C Orderly','2°C Delayed','3°C Disorderly','Net Zero 2040','Policy Shock'];
  const strandedData = scenarios.map((s,i)=>({
    scenario: s,
    cost: parseFloat((50+rng(i+30)*250).toFixed(0)),
  }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/real-asset-decarb/lock-in-risk', { assetType, age });
      setResult(r.data);
    } catch {
      const ageNum = parseInt(age)||15;
      const lockIn = Math.min(100, Math.round(30 + ageNum*2 + rng(1)*20));
      setResult({
        lockInScore: lockIn,
        strandingYear: 2030 + Math.round(rng(2)*10),
        divergence: (15+rng(3)*25).toFixed(1),
        capexCycle: Math.round(20-ageNum%20),
      });
    }
  }, [assetType, age]);

  return (
    <div>
      <Section title="Asset Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Asset Type" value={assetType} onChange={e=>setAssetType(e.target.value)}>
            {['Building','Industrial','Transport','Power'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Inp label="Asset Age (years)" type="number" value={age} onChange={e=>setAge(e.target.value)} />
          <div className="flex items-end col-span-2"><Btn onClick={run}>Calculate Lock-In Risk</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Lock-In Score" value={`${result.lockInScore}/100`} sub="Carbon lock-in exposure" />
          <KpiCard label="Stranding Year" value={result.strandingYear} sub="CRREM pathway divergence" />
          <KpiCard label="Current Divergence" value={`+${result.divergence} kgCO2/m²`} sub="vs CRREM 1.5°C pathway" />
          <KpiCard label="Next Capex Cycle" value={`${result.capexCycle} yrs`} sub="Retrofit window" />
        </Row>
      )}
      <Section title="CRREM Divergence — Current vs 1.5°C Pathway (kgCO₂/m²)">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={crremData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis unit=" kg" />
            <Tooltip formatter={v=>`${v} kgCO2/m²`} />
            <Legend />
            <Line type="monotone" dataKey="current" name="Current Trajectory" stroke="#ef4444" strokeWidth={2} />
            <Line type="monotone" dataKey="pathway" name="CRREM 1.5°C Pathway" stroke="#059669" strokeWidth={2} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Stranded Cost by Scenario (USD k)">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={strandedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="scenario" tick={{fontSize:10}} />
            <YAxis unit="k" />
            <Tooltip formatter={v=>`$${v}k`} />
            <Bar dataKey="cost" name="Stranded Cost" fill="#059669">
              {strandedData.map((_,i)=><Cell key={i} fill={i>2?'#ef4444':'#059669'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- Capex Transition Plan ----------
function CapexTab() {
  const [targetYear, setTargetYear] = useState('2040');
  const [budget, setBudget] = useState('10');
  const [result, setResult] = useState(null);

  const measures = ['Insulation','HVAC Upgrade','LED Lighting','Solar PV','Fuel Switch','Electrification','CCS','BMS'];
  const abatementData = measures.map((m,i)=>({
    measure: m,
    cost: parseFloat((20+rng(i+10)*180).toFixed(0)),
    reduction: parseFloat((5+rng(i+18)*35).toFixed(0)),
  })).sort((a,b)=>a.cost-b.cost);

  const capexStack = [2025,2028,2030,2035,2040].map((y,i)=>({
    year: y,
    efficiency: Math.round(20+rng(i+30)*30),
    fuelSwitch: Math.round(15+rng(i+35)*25),
    electrification: Math.round(10+rng(i+40)*30),
    ccs: Math.round(5+rng(i+45)*15),
  }));

  const emissionsLine = YEARS.map((y,i)=>({
    year: y,
    baseline: parseFloat((1000-i*10).toFixed(0)),
    withCapex: parseFloat((1000-i*35-rng(i+50)*20).toFixed(0)),
  }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/real-asset-decarb/capex-transition', { targetYear, budget });
      setResult(r.data);
    } catch {
      setResult({
        reductionPct: (40+rng(60)*40).toFixed(0),
        irr: (8+rng(61)*6).toFixed(1),
        payback: (5+rng(62)*8).toFixed(1),
        co2Saved: (250+rng(63)*500).toFixed(0),
      });
    }
  }, [targetYear, budget]);

  return (
    <div>
      <Section title="Transition Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Target Year" value={targetYear} onChange={e=>setTargetYear(e.target.value)}>
            {['2030','2035','2040','2045','2050'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Inp label="Budget (USD M)" type="number" value={budget} onChange={e=>setBudget(e.target.value)} />
          <div className="flex items-end col-span-2"><Btn onClick={run}>Build Capex Plan</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Emission Reduction" value={`${result.reductionPct}%`} sub={`By ${targetYear}`} />
          <KpiCard label="Portfolio IRR" value={`${result.irr}%`} sub="Blended transition return" />
          <KpiCard label="Avg Payback" value={`${result.payback} yrs`} sub="Across measures" />
          <KpiCard label="CO₂ Saved" value={`${result.co2Saved} tCO₂`} sub="Cumulative to target year" />
        </Row>
      )}
      <Section title="Abatement Cost Curve ($/tCO₂e, sorted)">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={abatementData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="measure" tick={{fontSize:10}} />
            <YAxis unit="$/t" />
            <Tooltip formatter={v=>`$${v}/tCO₂e`} />
            <Bar dataKey="cost" name="Abatement Cost" fill="#059669">
              {abatementData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="Capex Stack by Phase (USD M)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={capexStack}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis unit="M" />
              <Tooltip />
              <Legend />
              <Bar dataKey="efficiency" name="Efficiency" stackId="a" fill="#059669" />
              <Bar dataKey="fuelSwitch" name="Fuel Switch" stackId="a" fill="#10b981" />
              <Bar dataKey="electrification" name="Electrification" stackId="a" fill="#34d399" />
              <Bar dataKey="ccs" name="CCS" stackId="a" fill="#6ee7b7" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Cumulative Emissions (tCO₂)">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={emissionsLine}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis unit="t" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="baseline" name="Baseline" stroke="#ef4444" strokeWidth={2} />
              <Line type="monotone" dataKey="withCapex" name="With Capex Plan" stroke="#059669" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ---------- Retrofit NPV ----------
function RetrofitTab() {
  const [buildingType, setBuildingType] = useState('Office');
  const [measures, setMeasures] = useState({ insulation: true, hvac: false, glazing: false, solar: true, led: true, bms: false });
  const [result, setResult] = useState(null);

  const selected = Object.entries(measures).filter(([,v])=>v).map(([k])=>k);
  const measureData = [
    { name:'Insulation', npv:180, payback:7.2, saving:18 },
    { name:'HVAC', npv:240, payback:9.5, saving:25 },
    { name:'Glazing', npv:90, payback:11.0, saving:12 },
    { name:'Solar PV', npv:320, payback:8.2, saving:30 },
    { name:'LED', npv:95, payback:3.1, saving:10 },
    { name:'BMS', npv:160, payback:5.8, saving:20 },
  ].filter(m=>measures[m.name.toLowerCase().replace(' pv','').replace(' ','')]!==undefined);

  const waterfallData = [
    { name:'Baseline Cost', value: 1200, type:'cost' },
    ...selected.map((k,i)=>({ name:k.charAt(0).toUpperCase()+k.slice(1), value:-Math.round(80+rng(i+10)*200), type:'saving' })),
    { name:'Net Present Value', value: selected.reduce((a,_,i)=>a+Math.round(80+rng(i+10)*200),0)-1200, type:'net' },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/real-asset-decarb/retrofit-npv', { buildingType, measures: selected });
      setResult(r.data);
    } catch {
      const cnt = selected.length;
      setResult({
        totalNpv: Math.round(cnt*120+rng(20)*200),
        avgPayback: parseFloat((3+cnt*1.2+rng(21)*2).toFixed(1)),
        energySaving: Math.round(cnt*8+rng(22)*10),
        ghgReduction: Math.round(cnt*15+rng(23)*20),
      });
    }
  }, [buildingType, selected]);

  return (
    <div>
      <Section title="Retrofit Configuration">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <Sel label="Building Type" value={buildingType} onChange={e=>setBuildingType(e.target.value)}>
            {['Office','Retail','Industrial','Residential','Healthcare','Education'].map(o=><option key={o}>{o}</option>)}
          </Sel>
        </div>
        <div className="mb-4">
          <p className="text-xs text-gray-600 mb-2">Retrofit Measures</p>
          <div className="flex flex-wrap gap-3">
            {Object.keys(measures).map(k=>(
              <label key={k} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={measures[k]} onChange={e=>setMeasures(prev=>({...prev,[k]:e.target.checked}))} className="accent-emerald-600" />
                {k.charAt(0).toUpperCase()+k.slice(1)}
              </label>
            ))}
          </div>
        </div>
        <Btn onClick={run}>Calculate Retrofit NPV</Btn>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Total NPV" value={`$${result.totalNpv}k`} sub="Net present value" />
          <KpiCard label="Avg Payback" value={`${result.avgPayback} yrs`} sub="Across selected measures" />
          <KpiCard label="Energy Saving" value={`${result.energySaving}%`} sub="Annual reduction" />
          <KpiCard label="GHG Reduction" value={`${result.ghgReduction} tCO₂`} sub="Annual saving" />
        </Row>
      )}
      <Section title="NPV Waterfall (USD k)">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={waterfallData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{fontSize:10}} />
            <YAxis unit="k" />
            <Tooltip formatter={v=>`$${v}k`} />
            <Bar dataKey="value" name="NPV Component">
              {waterfallData.map((d,i)=><Cell key={i} fill={d.type==='cost'?'#ef4444':d.type==='saving'?'#059669':'#10b981'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Energy Saving % by Measure">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={measureData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{fontSize:10}} />
            <YAxis unit="%" />
            <Tooltip formatter={v=>`${v}%`} />
            <Bar dataKey="saving" name="Energy Saving %" fill="#059669" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- Brown-to-Green Portfolio ----------
function BrownGreenTab() {
  const [portfolioValue, setPortfolioValue] = useState('500');
  const [assetCount, setAssetCount] = useState('45');
  const [scenario, setScenario] = useState('Net Zero 2050');
  const [result, setResult] = useState(null);

  const emissionsPath = YEARS.map((y,i)=>({
    year: y,
    brown: parseFloat((100000-i*3000-rng(i)*2000).toFixed(0)),
    green: parseFloat((100000-i*6500-rng(i+20)*1500).toFixed(0)),
  }));

  const premiumData = ['Grade A','Grade B','Grade C','EPC A','EPC B','BREEAM Outstanding'].map((g,i)=>({
    grade: g,
    premium: parseFloat((2+rng(i+30)*8).toFixed(1)),
  }));

  const strandingLine = YEARS.filter((_,i)=>i%2===0).map((y,i)=>({
    year: y,
    stranded: parseFloat((35-i*2.5-rng(i+40)*2).toFixed(1)),
    withTransition: parseFloat((35-i*4-rng(i+48)*2).toFixed(1)),
  }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/real-asset-decarb/brown-to-green', { portfolioValue, assetCount, scenario });
      setResult(r.data);
    } catch {
      setResult({
        greenPct: Math.round(20+rng(50)*40),
        strandedPct: parseFloat((15+rng(51)*20).toFixed(1)),
        avgPremium: parseFloat((4.5+rng(52)*4).toFixed(1)),
        emissionIntensity: parseFloat((85+rng(53)*60).toFixed(0)),
      });
    }
  }, [portfolioValue, assetCount, scenario]);

  return (
    <div>
      <Section title="Portfolio Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Portfolio Value (USD M)" type="number" value={portfolioValue} onChange={e=>setPortfolioValue(e.target.value)} />
          <Inp label="Asset Count" type="number" value={assetCount} onChange={e=>setAssetCount(e.target.value)} />
          <Sel label="Transition Scenario" value={scenario} onChange={e=>setScenario(e.target.value)}>
            {['Net Zero 2050','1.5°C Orderly','2°C Delayed','Current Policies'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <div className="flex items-end"><Btn onClick={run}>Analyse Portfolio</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Green Assets %" value={`${result.greenPct}%`} sub="EPC A/B or BREEAM rated" />
          <KpiCard label="Stranded Risk" value={`${result.strandedPct}%`} sub="Of portfolio value" />
          <KpiCard label="Avg Green Premium" value={`+${result.avgPremium}%`} sub="vs brown equivalents" />
          <KpiCard label="Emission Intensity" value={`${result.emissionIntensity} kgCO₂/m²`} sub="Portfolio weighted avg" />
        </Row>
      )}
      <Section title="Portfolio Emissions Trajectory 2024–2050 (tCO₂)">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={emissionsPath}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis unit="t" />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="brown" name="No Transition" stroke="#ef4444" fill="#fecaca" />
            <Area type="monotone" dataKey="green" name="With B2G Plan" stroke="#059669" fill="#d1fae5" />
          </AreaChart>
        </ResponsiveContainer>
      </Section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="Green Premium Uplift by Grade (%)">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={premiumData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="grade" tick={{fontSize:10}} />
              <YAxis unit="%" />
              <Tooltip formatter={v=>`+${v}%`} />
              <Bar dataKey="premium" name="Premium" fill="#059669" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Stranded Asset Risk Reduction (% of portfolio)">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={strandingLine}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis unit="%" />
              <Tooltip formatter={v=>`${v}%`} />
              <Legend />
              <Line type="monotone" dataKey="stranded" name="No Action" stroke="#ef4444" strokeWidth={2} />
              <Line type="monotone" dataKey="withTransition" name="With B2G Plan" stroke="#059669" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ---------- Decarbonisation Roadmap ----------
function RoadmapTab() {
  const [assetCount, setAssetCount] = useState('30');
  const [budget, setBudget] = useState('50');
  const [result, setResult] = useState(null);

  const milestones = [2025,2030,2035,2040,2050];
  const milestonesData = milestones.map((y,i)=>({
    year: y,
    target: Math.round(100-i*18-rng(i)*5),
    sbti: Math.round(100-i*22),
  }));

  const priorityTable = Array.from({length:8},(_,i)=>({
    rank: i+1,
    asset: `Asset ${String.fromCharCode(65+i)}`,
    type: ['Office','Industrial','Retail','Warehouse','Hotel','Logistics','School','Hospital'][i],
    costEff: parseFloat((15+rng(i+10)*85).toFixed(0)),
    reduction: Math.round(10+rng(i+18)*40),
    priority: i<3?'High':i<6?'Medium':'Low',
  }));

  const quickWins = [
    'LED lighting retrofit across all assets — payback < 3 years',
    'Building Management System (BMS) upgrade — 15–25% energy saving',
    'Submetering installation for consumption visibility',
    'Green energy procurement switch (Renewable PPAs or I-RECs)',
    'Low-cost insulation improvements to EPC D assets',
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/real-asset-decarb/decarb-roadmap', { assetCount, budget });
      setResult(r.data);
    } catch {
      setResult({
        tcfdScore: Math.round(65+rng(60)*30),
        ifrss2Score: Math.round(60+rng(61)*35),
        highPriority: Math.round(3+rng(62)*5),
        totalReduction: Math.round(30+rng(63)*40),
      });
    }
  }, [assetCount, budget]);

  const priColor = p => p==='High'?'text-red-600 bg-red-50':p==='Medium'?'text-amber-600 bg-amber-50':'text-emerald-600 bg-emerald-50';

  return (
    <div>
      <Section title="Roadmap Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Asset Count" type="number" value={assetCount} onChange={e=>setAssetCount(e.target.value)} />
          <Inp label="Total Budget (USD M)" type="number" value={budget} onChange={e=>setBudget(e.target.value)} />
          <div className="flex items-end col-span-2"><Btn onClick={run}>Generate Roadmap</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="TCFD Alignment" value={`${result.tcfdScore}/100`} sub="Metrics & targets pillar" />
          <KpiCard label="IFRS S2 Alignment" value={`${result.ifrss2Score}/100`} sub="Physical & transition risk" />
          <KpiCard label="High Priority Assets" value={result.highPriority} sub="Immediate action required" />
          <KpiCard label="2030 Reduction Target" value={`${result.totalReduction}%`} sub="vs 2019 baseline" />
        </Row>
      )}
      <Section title="Interim Emission Reduction Targets (% vs baseline)">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={milestonesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis unit="%" domain={[0,105]} />
            <Tooltip formatter={v=>`${v}%`} />
            <Legend />
            <Bar dataKey="target" name="Portfolio Target" fill="#059669" />
            <Bar dataKey="sbti" name="SBTi Pathway" fill="#6ee7b7" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Asset Priority Ranking (by Cost-Effectiveness $/tCO₂e)">
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Rank','Asset','Type','$/tCO₂e','Reduction','Priority'].map(h=><th key={h} className="border border-gray-200 px-3 py-2 text-left font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{priorityTable.map((r,i)=><tr key={i} className="hover:bg-gray-50">
              <td className="border border-gray-200 px-3 py-2 font-bold text-gray-500">{r.rank}</td>
              <td className="border border-gray-200 px-3 py-2 font-medium">{r.asset}</td>
              <td className="border border-gray-200 px-3 py-2">{r.type}</td>
              <td className="border border-gray-200 px-3 py-2">${r.costEff}</td>
              <td className="border border-gray-200 px-3 py-2">{r.reduction}%</td>
              <td className="border border-gray-200 px-3 py-2"><span className={`px-2 py-0.5 rounded text-xs font-semibold ${priColor(r.priority)}`}>{r.priority}</span></td>
            </tr>)}</tbody>
          </table>
        </div>
      </Section>
      <Section title="Quick Wins (No/Low Regret Actions)">
        <ul className="space-y-2">
          {quickWins.map((w,i)=><li key={i} className="flex items-start gap-2 text-sm text-gray-700"><span className="text-emerald-500 font-bold">&#10003;</span>{w}</li>)}
        </ul>
      </Section>
    </div>
  );
}

// ---------- Main ----------
export default function RealAssetDecarbPage() {
  const [tab, setTab] = useState(0);
  const panels = [<LockInTab/>,<CapexTab/>,<RetrofitTab/>,<BrownGreenTab/>,<RoadmapTab/>];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Real Asset Decarbonisation</h1>
          <p className="text-sm text-gray-500 mt-1">CRREM 2.0 Pathways · Lock-In Risk · Capex Transition Planning · Retrofit NPV · Brown-to-Green Portfolio · SBTi Buildings/Industry · Stranded Cost Curves</p>
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
