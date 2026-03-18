import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-black">{value}</div>{sub&&<div className="text-xs text-emerald-600 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{children}</div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}/></div>);
const Sel = ({label,children,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>);

const TABS = ['Equator Principles v4','ECA Standards','Supply Chain ESG','Trade Flow Emissions','Green Instrument'];
const COLORS = ['#059669','#10b981','#34d399','#6ee7b7','#a7f3d0','#f59e0b'];
const seed = 75;
const rng = (i,s=seed) => Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280;

// ---------- Equator Principles v4 ----------
function EquatorTab() {
  const [projectType, setProjectType] = useState('Power Plant');
  const [cost, setCost] = useState('120');
  const [country, setCountry] = useState('Indonesia');
  const [result, setResult] = useState(null);

  const highRiskCountries = ['Indonesia','Bangladesh','Nigeria','Pakistan','Colombia','Ethiopia','Vietnam','DRC','Peru','Myanmar'];

  const principlesData = [
    { name: 'P1 Review & Categorisation', score: Math.round(70+rng(1)*25) },
    { name: 'P2 Environmental & Social Assessment', score: Math.round(65+rng(2)*30) },
    { name: 'P3 Applicable Standards', score: Math.round(75+rng(3)*20) },
    { name: 'P4 Environmental & Social Management', score: Math.round(68+rng(4)*28) },
    { name: 'P5 Stakeholder Engagement', score: Math.round(60+rng(5)*35) },
    { name: 'P6 Grievance Mechanism', score: Math.round(55+rng(6)*40) },
    { name: 'P7 Independent Review', score: Math.round(72+rng(7)*23) },
    { name: 'P8 Covenants', score: Math.round(80+rng(8)*15) },
    { name: 'P9 Independent Monitoring', score: Math.round(65+rng(9)*30) },
    { name: 'P10 Reporting & Transparency', score: Math.round(70+rng(10)*25) },
  ];

  const radarData = principlesData.slice(0,8).map(p=>({ axis: `P${p.name.split(' ')[0].replace('P','')}`, value: p.score }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/trade-finance-esg/equator-principles', { projectType, cost, country });
      setResult(r.data);
    } catch {
      const costNum = parseFloat(cost)||120;
      const isHighRisk = highRiskCountries.includes(country);
      const cat = costNum >= 100 && isHighRisk ? 'A' : costNum >= 50 ? 'B' : 'C';
      setResult({
        category: cat,
        esiaRequired: cat !== 'C',
        grievanceMechanism: rng(11) > 0.3,
        overallScore: Math.round(65+rng(12)*30),
      });
    }
  }, [projectType, cost, country]);

  const catColor = c => c==='A'?'bg-red-100 text-red-700 border-red-300':c==='B'?'bg-amber-100 text-amber-700 border-amber-300':'bg-emerald-100 text-emerald-700 border-emerald-300';

  return (
    <div>
      <Section title="Project Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Project Type" value={projectType} onChange={e=>setProjectType(e.target.value)}>
            {['Power Plant','Mining','Infrastructure','Agriculture','Manufacturing','Telecom','Transport'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Inp label="Project Cost (USD M)" type="number" value={cost} onChange={e=>setCost(e.target.value)} />
          <Sel label="Host Country" value={country} onChange={e=>setCountry(e.target.value)}>
            {highRiskCountries.map(o=><option key={o}>{o}</option>)}
          </Sel>
          <div className="flex items-end"><Btn onClick={run}>Assess EP4</Btn></div>
        </div>
      </Section>
      {result && (
        <>
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-gray-600">EP4 Category:</span>
            <span className={`px-4 py-1.5 rounded-full text-lg font-bold border ${catColor(result.category)}`}>Category {result.category}</span>
            <span className={`px-3 py-1 rounded text-sm ${result.esiaRequired?'bg-red-50 text-red-600':'bg-emerald-50 text-emerald-600'}`}>ESIA: {result.esiaRequired?'Required':'Not Required'}</span>
            <span className={`px-3 py-1 rounded text-sm ${result.grievanceMechanism?'bg-emerald-50 text-emerald-600':'bg-red-50 text-red-600'}`}>Grievance Mechanism: {result.grievanceMechanism?'In Place':'Missing'}</span>
          </div>
          <Row>
            <KpiCard label="EP4 Category" value={`Cat ${result.category}`} sub="Equator Principles v4 (2020)" />
            <KpiCard label="Overall EP Score" value={`${result.overallScore}/100`} sub="10 principles composite" />
            <KpiCard label="ESIA Required" value={result.esiaRequired?'Yes':'No'} sub="Environmental & Social Impact" />
            <KpiCard label="Grievance Mechanism" value={result.grievanceMechanism?'Active':'Gap'} sub="EP4 P6 compliance" />
          </Row>
        </>
      )}
      <Section title="10 Equator Principles Compliance Scores">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="axis" tick={{fontSize:11}} />
              <PolarRadiusAxis angle={90} domain={[0,100]} />
              <Radar name="Score" dataKey="value" stroke="#059669" fill="#059669" fillOpacity={0.35} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
          <div className="overflow-y-auto max-h-300">
            <table className="w-full text-xs border-collapse">
              <thead><tr className="bg-gray-50"><th className="border border-gray-200 px-2 py-1 text-left">Principle</th><th className="border border-gray-200 px-2 py-1">Score</th></tr></thead>
              <tbody>{principlesData.map((p,i)=><tr key={i} className="hover:bg-gray-50"><td className="border border-gray-200 px-2 py-1">{p.name}</td><td className={`border border-gray-200 px-2 py-1 text-center font-semibold ${p.score>=75?'text-emerald-600':p.score>=60?'text-amber-600':'text-red-600'}`}>{p.score}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      </Section>
    </div>
  );
}

// ---------- ECA Standards ----------
function ECATab() {
  const [ecaType, setEcaType] = useState('Medium/Long-Term Credit');
  const [sector, setSector] = useState('Renewable Energy');
  const [result, setResult] = useState(null);

  const countries15 = ['DE','FR','IT','ES','NL','BE','AT','FI','PL','CZ','HU','RO','SE','NO','DK'];
  const crcData = countries15.map((c,i)=>({
    country: c,
    crc: Math.min(7, Math.round(rng(i+10)*7)),
  }));

  const premiumTable = [
    { term: '2 years', crc0: '0.12%', crc3: '0.85%', crc5: '1.95%', crc7: '4.20%' },
    { term: '5 years', crc0: '0.28%', crc3: '1.85%', crc5: '3.90%', crc7: '8.50%' },
    { term: '7 years', crc0: '0.40%', crc3: '2.60%', crc5: '5.60%', crc7: '12.20%' },
    { term: '10 years', crc0: '0.55%', crc3: '3.50%', crc5: '7.50%', crc7: '16.80%' },
  ];

  const coalExclusions = ['OECD Common Approaches (June 2022)','Equator Principles EP4 Climate','OECD Arrangement Article 10','ITFA Sustainable Trade Finance Principles'];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/trade-finance-esg/eca-standards', { ecaType, sector });
      setResult(r.data);
    } catch {
      const coaled = sector === 'Coal Mining' || sector === 'Coal Power';
      setResult({
        coalGate: !coaled,
        oecd: rng(20)>0.3?'Eligible':'Conditional',
        commonApproachScore: Math.round(60+rng(21)*35),
      });
    }
  }, [ecaType, sector]);

  return (
    <div>
      <Section title="ECA Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Export Credit Type" value={ecaType} onChange={e=>setEcaType(e.target.value)}>
            {['Medium/Long-Term Credit','Short-Term Credit','Investment Insurance','Bond/Guarantee','Direct Lending'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Sel label="OECD Sector" value={sector} onChange={e=>setSector(e.target.value)}>
            {['Renewable Energy','Infrastructure','Manufacturing','Agriculture','Coal Power','Coal Mining','Transport','Telecom'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <div className="flex items-end col-span-2"><Btn onClick={run}>Assess ECA Standards</Btn></div>
        </div>
      </Section>
      {result && (
        <>
          <div className="flex items-center gap-3 mb-4">
            <span className={`px-4 py-2 rounded-lg font-semibold text-sm ${result.coalGate?'bg-emerald-100 text-emerald-700':'bg-red-100 text-red-700'}`}>
              Coal Sector Gate: {result.coalGate?'PASS':'EXCLUDED'}
            </span>
            <span className="px-3 py-2 rounded-lg text-sm bg-gray-100 text-gray-700">OECD Common Approaches: {result.oecd}</span>
          </div>
          <Row>
            <KpiCard label="Coal Gate" value={result.coalGate?'Pass':'Excluded'} sub="OECD 2022 coal exclusion" />
            <KpiCard label="OECD Eligibility" value={result.oecd} sub="Common Approaches" />
            <KpiCard label="E&S Score" value={`${result.commonApproachScore}/100`} sub="OECD Common Approaches" />
          </Row>
        </>
      )}
      <Section title="Country Risk Classification (CRC 0–7 for EU15)">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={crcData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="country" tick={{fontSize:10}} />
            <YAxis domain={[0,7]} ticks={[0,1,2,3,4,5,6,7]} />
            <Tooltip />
            <Bar dataKey="crc" name="CRC" fill="#059669">
              {crcData.map((d,i)=><Cell key={i} fill={d.crc<=2?'#059669':d.crc<=4?'#f59e0b':'#ef4444'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="OECD Minimum Premium Rates (% per annum)">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Term','CRC 0','CRC 3','CRC 5','CRC 7'].map(h=><th key={h} className="border border-gray-200 px-3 py-2 text-left font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{premiumTable.map((r,i)=><tr key={i} className="hover:bg-gray-50"><td className="border border-gray-200 px-3 py-2 font-medium">{r.term}</td><td className="border border-gray-200 px-3 py-2">{r.crc0}</td><td className="border border-gray-200 px-3 py-2">{r.crc3}</td><td className="border border-gray-200 px-3 py-2">{r.crc5}</td><td className="border border-gray-200 px-3 py-2 text-red-600">{r.crc7}</td></tr>)}</tbody>
          </table>
        </div>
      </Section>
      <Section title="Coal Sector Exclusion Frameworks">
        <ul className="space-y-1">
          {coalExclusions.map((e,i)=><li key={i} className="flex items-center gap-2 text-sm text-gray-700"><span className="text-amber-500">&#9888;</span>{e}</li>)}
        </ul>
      </Section>
    </div>
  );
}

// ---------- Supply Chain ESG ----------
function SupplyChainESGTab() {
  const [supplierCount, setSupplierCount] = useState('120');
  const [category, setCategory] = useState('Electronics');
  const [result, setResult] = useState(null);

  const tierData = ['A','B','C','D','E'].map((t,i)=>({
    tier: `Tier ${t}`,
    suppliers: Math.round((30-i*5+rng(i+10)*20)),
  }));

  const ratchetData = Array.from({length:11},(_,i)=>({
    score: i*10,
    margin: parseFloat((250-i*20+rng(i+20)*10).toFixed(0)),
  }));

  const scope3Data = ['T1 Purchased Goods','T2 Transport','T3 Waste','T4 Business Travel','T5 Employee Commute'].map((c,i)=>({
    category: c,
    emissions: Math.round(500+rng(i+30)*2000),
  }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/trade-finance-esg/supply-chain-esg', { supplierCount, category });
      setResult(r.data);
    } catch {
      setResult({
        avgEsgScore: Math.round(58+rng(40)*25),
        iloScore: Math.round(65+rng(41)*30),
        scope3Cat1: Math.round(8000+rng(42)*15000),
        ddRate: Math.round(45+rng(43)*40),
      });
    }
  }, [supplierCount, category]);

  return (
    <div>
      <Section title="Supply Chain Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Supplier Count" type="number" value={supplierCount} onChange={e=>setSupplierCount(e.target.value)} />
          <Sel label="Product Category" value={category} onChange={e=>setCategory(e.target.value)}>
            {['Electronics','Apparel','Food & Beverage','Chemicals','Metals','Automotive','Pharmaceuticals','Agriculture'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <div className="flex items-end col-span-2"><Btn onClick={run}>Analyse Supply Chain ESG</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Avg ESG Score" value={`${result.avgEsgScore}/100`} sub="Supplier composite" />
          <KpiCard label="ILO Compliance" value={`${result.iloScore}/100`} sub="Labour standards score" />
          <KpiCard label="Scope 3 Cat 1" value={`${(result.scope3Cat1/1000).toFixed(1)}k tCO₂`} sub="Purchased goods & services" />
          <KpiCard label="Due Diligence Rate" value={`${result.ddRate}%`} sub="Suppliers assessed" />
        </Row>
      )}
      <Section title="ESG Tier Distribution (A=Best, E=Worst)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={tierData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tier" />
            <YAxis unit=" suppliers" />
            <Tooltip />
            <Bar dataKey="suppliers" name="Suppliers" fill="#059669">
              {tierData.map((_,i)=><Cell key={i} fill={['#059669','#10b981','#f59e0b','#fb923c','#ef4444'][i]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="Dynamic Discounting Margin Ratchet (ESG Score → bps)">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={ratchetData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="score" unit=" score" />
              <YAxis unit="bps" />
              <Tooltip formatter={v=>`${v}bps`} />
              <Line type="monotone" dataKey="margin" name="Margin" stroke="#059669" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Scope 3 Category Attribution (tCO₂)">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={scope3Data} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit="t" />
              <YAxis type="category" dataKey="category" width={130} tick={{fontSize:10}} />
              <Tooltip />
              <Bar dataKey="emissions" name="Emissions" fill="#059669" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ---------- Trade Flow Emissions ----------
function TradeFlowTab() {
  const [origin, setOrigin] = useState('Shanghai');
  const [destination, setDestination] = useState('Rotterdam');
  const [commodity, setCommodity] = useState('Electronics');
  const [volume, setVolume] = useState('500');
  const [result, setResult] = useState(null);

  const modePie = [
    { name: 'Sea Freight', value: 65 },
    { name: 'Air Freight', value: 8 },
    { name: 'Rail', value: 15 },
    { name: 'Road', value: 12 },
  ];

  const lanes = ['Asia-Europe','Asia-Americas','Europe-Americas','Intra-Asia','Intra-Europe','Middle East-Asia'].map((l,i)=>({
    lane: l,
    cat1: Math.round(200+rng(i+10)*800),
    cat4: Math.round(100+rng(i+16)*400),
  }));

  const efTable = [
    { mode: 'Sea (container)', ef: 8.4, unit: 'gCO₂/tonne-km', source: 'IMO GHG 2023' },
    { mode: 'Air freight', ef: 602, unit: 'gCO₂/tonne-km', source: 'ICAO 2023' },
    { mode: 'Rail (EU avg)', ef: 22, unit: 'gCO₂/tonne-km', source: 'EEA 2023' },
    { mode: 'Road HGV', ef: 75, unit: 'gCO₂/tonne-km', source: 'GLEC 2023' },
    { mode: 'River barge', ef: 31, unit: 'gCO₂/tonne-km', source: 'EEA 2023' },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/trade-finance-esg/trade-flow-emissions', { origin, destination, commodity, volume });
      setResult(r.data);
    } catch {
      setResult({
        totalEmissions: Math.round(parseFloat(volume)*0.8+rng(50)*200),
        cat1: Math.round(parseFloat(volume)*0.5+rng(51)*100),
        cat4: Math.round(parseFloat(volume)*0.3+rng(52)*80),
        emissionFactor: parseFloat((8+rng(53)*60).toFixed(1)),
      });
    }
  }, [origin, destination, commodity, volume]);

  return (
    <div>
      <Section title="Trade Lane Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Origin" value={origin} onChange={e=>setOrigin(e.target.value)}>
            {['Shanghai','Singapore','Dubai','Los Angeles','Hamburg','Mumbai','Osaka','Sydney'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Sel label="Destination" value={destination} onChange={e=>setDestination(e.target.value)}>
            {['Rotterdam','New York','Hamburg','Singapore','Dubai','Felixstowe','Antwerp','Le Havre'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Sel label="Commodity" value={commodity} onChange={e=>setCommodity(e.target.value)}>
            {['Electronics','Textiles','Chemicals','Food','Metals','Plastics','Machinery','Vehicles'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Inp label="Volume (TEU/year)" type="number" value={volume} onChange={e=>setVolume(e.target.value)} />
        </div>
        <Btn onClick={run}>Calculate Trade Emissions</Btn>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Total Emissions" value={`${result.totalEmissions} tCO₂`} sub={`${origin}→${destination}`} />
          <KpiCard label="Scope 3 Cat 1" value={`${result.cat1} tCO₂`} sub="Purchased goods transport" />
          <KpiCard label="Scope 3 Cat 4" value={`${result.cat4} tCO₂`} sub="Upstream transport" />
          <KpiCard label="Avg Emission Factor" value={`${result.emissionFactor} g/t-km`} sub="GLEC framework" />
        </Row>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="Transport Mode Split (% of volume)">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={modePie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`}>
                {modePie.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Scope 3 Cat 1+4 by Trade Lane (tCO₂)">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={lanes}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="lane" tick={{fontSize:9}} />
              <YAxis unit="t" />
              <Tooltip />
              <Legend />
              <Bar dataKey="cat1" name="Cat 1" fill="#059669" />
              <Bar dataKey="cat4" name="Cat 4" fill="#34d399" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>
      <Section title="Emission Factor Reference (GLEC Framework 2023)">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Mode','Emission Factor','Unit','Source'].map(h=><th key={h} className="border border-gray-200 px-3 py-2 text-left font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{efTable.map((r,i)=><tr key={i} className="hover:bg-gray-50"><td className="border border-gray-200 px-3 py-2 font-medium">{r.mode}</td><td className={`border border-gray-200 px-3 py-2 font-semibold ${r.ef<50?'text-emerald-600':r.ef<200?'text-amber-600':'text-red-600'}`}>{r.ef}</td><td className="border border-gray-200 px-3 py-2 text-gray-500 text-xs">{r.unit}</td><td className="border border-gray-200 px-3 py-2 text-gray-500">{r.source}</td></tr>)}</tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ---------- Green Instrument ----------
function GreenInstrumentTab() {
  const [instrument, setInstrument] = useState('Green LC');
  const [useOfProceeds, setUseOfProceeds] = useState('Renewable Energy');
  const [result, setResult] = useState(null);

  const iccData = [
    { principle: 'P1 Use of Proceeds', score: Math.round(75+rng(1)*20) },
    { principle: 'P2 Project Eval & Selection', score: Math.round(70+rng(2)*25) },
    { principle: 'P3 Mgmt of Proceeds', score: Math.round(80+rng(3)*15) },
    { principle: 'P4 Reporting', score: Math.round(65+rng(4)*30) },
    { principle: 'P5 Verification', score: Math.round(60+rng(5)*35) },
    { principle: 'P6 Additionality', score: Math.round(55+rng(6)*40) },
    { principle: 'P7 Greenwashing Prevention', score: Math.round(72+rng(7)*23) },
    { principle: 'P8 Market Integrity', score: Math.round(68+rng(8)*27) },
  ];

  const icmaTable = [
    { req: 'Use of Proceeds Definition', status: rng(10)>0.2?'Aligned':'Partial', icma: 'ICMA GBP 2021' },
    { req: 'Project Selection Process', status: rng(11)>0.25?'Aligned':'Requires Work', icma: 'ICMA GBP 2021' },
    { req: 'Proceeds Management', status: rng(12)>0.2?'Aligned':'Partial', icma: 'ICMA GBP 2021' },
    { req: 'Impact Reporting', status: rng(13)>0.3?'Aligned':'Partial', icma: 'ICMA GBP 2021' },
    { req: 'External Review', status: rng(14)>0.4?'Aligned':'Not Met', icma: 'ICMA GBP 2021' },
    { req: 'Climate Transition Plan', status: rng(15)>0.35?'Aligned':'Partial', icma: 'ICMA CTF 2023' },
  ];

  const pricingData = Array.from({length:10},(_,i)=>({
    score: (i+1)*10,
    conventional: parseFloat((150+rng(i+20)*50).toFixed(0)),
    green: parseFloat((150+rng(i+20)*50-5-i*1.2).toFixed(0)),
  }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/trade-finance-esg/green-instrument', { instrument, useOfProceeds });
      setResult(r.data);
    } catch {
      const avg = iccData.reduce((a,b)=>a+b.score,0)/iccData.length;
      setResult({
        iccScore: avg.toFixed(0),
        pricingBenefit: (5+rng(30)*15).toFixed(1),
        icmaAligned: avg >= 68,
        greenium: (3+rng(31)*12).toFixed(1),
      });
    }
  }, [instrument, useOfProceeds]);

  const statusColor = s => s==='Aligned'?'text-emerald-600 bg-emerald-50':s==='Partial'?'text-amber-600 bg-amber-50':'text-red-600 bg-red-50';

  return (
    <div>
      <Section title="Green Instrument Configuration">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Instrument Type" value={instrument} onChange={e=>setInstrument(e.target.value)}>
            {['Green LC','Green SBLC','Green Trade Loan','SLT Facility','Green Supply Chain Finance'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Sel label="Use of Proceeds" value={useOfProceeds} onChange={e=>setUseOfProceeds(e.target.value)}>
            {['Renewable Energy','Clean Transport','Green Buildings','Water Management','Circular Economy','Biodiversity','Energy Efficiency'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <div className="flex items-end col-span-2"><Btn onClick={run}>Assess Green Instrument</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="ICC STF Score" value={`${result.iccScore}/100`} sub="8 STF principles" />
          <KpiCard label="Pricing Benefit" value={`-${result.pricingBenefit}bps`} sub="vs conventional" />
          <KpiCard label="ICMA Aligned" value={result.icmaAligned?'Yes':'Partial'} sub="GBP/SBP/CLPs" />
          <KpiCard label="Greenium" value={`-${result.greenium}bps`} sub="Market pricing advantage" />
        </Row>
      )}
      <Section title="ICC Sustainable Trade Finance Principles Score">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={iccData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="principle" tick={{fontSize:9}} />
            <YAxis domain={[0,100]} unit="%" />
            <Tooltip formatter={v=>`${v}%`} />
            <Bar dataKey="score" name="Score" fill="#059669">
              {iccData.map((d,i)=><Cell key={i} fill={d.score>=75?'#059669':d.score>=60?'#f59e0b':'#ef4444'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="ICMA Alignment Assessment">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Requirement','Status','Framework'].map(h=><th key={h} className="border border-gray-200 px-2 py-1 text-left text-xs font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{icmaTable.map((r,i)=><tr key={i} className="hover:bg-gray-50"><td className="border border-gray-200 px-2 py-1 text-xs">{r.req}</td><td className="border border-gray-200 px-2 py-1"><span className={`px-1.5 py-0.5 rounded text-xs font-medium ${statusColor(r.status)}`}>{r.status}</span></td><td className="border border-gray-200 px-2 py-1 text-xs text-gray-500">{r.icma}</td></tr>)}</tbody>
          </table>
        </Section>
        <Section title="Pricing Benefit vs ESG Score (bps)">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={pricingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="score" unit=" pts" tick={{fontSize:10}} />
              <YAxis unit="bps" />
              <Tooltip formatter={v=>`${v}bps`} />
              <Legend />
              <Line type="monotone" dataKey="conventional" name="Conventional" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" />
              <Line type="monotone" dataKey="green" name="Green Instrument" stroke="#059669" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ---------- Main ----------
export default function TradeFinanceESGPage() {
  const [tab, setTab] = useState(0);
  const panels = [<EquatorTab/>,<ECATab/>,<SupplyChainESGTab/>,<TradeFlowTab/>,<GreenInstrumentTab/>];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Sustainable Trade Finance</h1>
          <p className="text-sm text-gray-500 mt-1">Equator Principles v4 (2020) · OECD Arrangement on Export Credits · ICC Sustainable Trade Finance Principles 2022 · Supply-Chain ESG Dynamic Discounting · Trade Flow GHG</p>
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
