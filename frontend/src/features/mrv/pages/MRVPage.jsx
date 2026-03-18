import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-black">{value}</div>{sub&&<div className="text-xs text-emerald-600 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{children}</div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}/></div>);
const Sel = ({label,children,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>);

const TABS = ['MRV Tier Assessment','Data Quality Scoring','Satellite Coverage','Verification Readiness','Improvement Plan'];
const COLORS = ['#059669','#10b981','#34d399','#6ee7b7','#a7f3d0','#d1fae5'];
const seed = 73;
const rng = (i,s=seed) => Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280;

// ---------- MRV Tier Assessment ----------
function TierTab() {
  const [facility, setFacility] = useState('Industrial Plant');
  const [caps, setCaps] = useState({ cems: false, iot: false, satellite: false, manual: true, ai: false, thirdParty: false });
  const [result, setResult] = useState(null);

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/mrv/tier-assessment', { facility, capabilities: caps });
      setResult(r.data);
    } catch {
      const cnt = Object.values(caps).filter(Boolean).length;
      const tier = cnt <= 1 ? 1 : cnt === 2 ? 2 : cnt === 3 ? 3 : cnt === 4 ? 4 : 5;
      setResult({
        tier,
        score: Math.round(tier * 18 + rng(1) * 8),
        roadmap: [
          'Deploy IoT continuous sensors at major emission points',
          'Integrate CEMS for combustion sources ≥10 MW',
          'Subscribe to satellite SAR/thermal verification layer',
          'Implement AI-assisted anomaly detection pipeline',
          'Obtain ISO 14064-3 verification by accredited auditor',
        ].slice(0, 6 - tier),
      });
    }
  }, [facility, caps]);

  const tierColors = ['','bg-red-100 border-red-400','bg-orange-100 border-orange-400','bg-amber-100 border-amber-400','bg-lime-100 border-lime-400','bg-emerald-100 border-emerald-400'];

  return (
    <div>
      <Section title="Facility & Capability Inputs">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <Sel label="Facility Type" value={facility} onChange={e=>setFacility(e.target.value)}>
            {['Industrial Plant','Power Station','Commercial Building','Landfill','Agriculture Site','Refinery','Data Centre'].map(o=><option key={o}>{o}</option>)}
          </Sel>
        </div>
        <div className="mb-4">
          <p className="text-xs text-gray-600 mb-2">Measurement Capabilities (select all that apply)</p>
          <div className="flex flex-wrap gap-3">
            {[['cems','CEMS'],['iot','IoT Sensors'],['satellite','Satellite'],['manual','Manual Surveys'],['ai','AI Analysis'],['thirdParty','3rd-Party Audit']].map(([k,l])=>(
              <label key={k} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={caps[k]} onChange={e=>setCaps(prev=>({...prev,[k]:e.target.checked}))} className="accent-emerald-600" />
                {l}
              </label>
            ))}
          </div>
        </div>
        <Btn onClick={run}>Assess MRV Tier</Btn>
      </Section>
      {result && (
        <>
          <Section title="MRV Tier Result">
            <div className="flex gap-3 items-center mb-4">
              {[1,2,3,4,5].map(t=>(
                <div key={t} className={`flex-1 rounded-lg border-2 p-3 text-center transition-all ${t===result.tier?tierColors[t]+' scale-105':'bg-gray-50 border-gray-200'}`}>
                  <div className="text-lg font-bold text-black">Tier {t}</div>
                  <div className="text-xs text-gray-500">{['Basic Manual','Improved','Good Practice','Advanced','Digital MRV'][t-1]}</div>
                </div>
              ))}
            </div>
            <Row>
              <KpiCard label="Tier Achieved" value={`Tier ${result.tier}/5`} sub="ISO 14064-3 aligned" />
              <KpiCard label="Readiness Score" value={`${result.score}/100`} sub="Capability composite" />
            </Row>
          </Section>
          {result.roadmap && result.roadmap.length > 0 && (
            <Section title="Upgrade Roadmap">
              <ol className="space-y-2">
                {result.roadmap.map((step,i)=>(
                  <li key={i} className="flex items-start gap-3 text-sm text-gray-700">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center text-xs">{i+1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

// ---------- Data Quality Scoring ----------
function DataQualityTab() {
  const [scope1, setScope1] = useState('2500');
  const [scope2, setScope2] = useState('1800');
  const [scope3, setScope3] = useState('8500');
  const [ipccTier, setIpccTier] = useState('Tier 2');
  const [result, setResult] = useState(null);

  const cdpData = [
    { module: 'GHG Accounting', score: Math.round(70+rng(10)*25) },
    { module: 'Scope 1 Accuracy', score: Math.round(65+rng(11)*30) },
    { module: 'Scope 2 Method', score: Math.round(75+rng(12)*20) },
    { module: 'Scope 3 Coverage', score: Math.round(50+rng(13)*35) },
    { module: 'Verification', score: Math.round(60+rng(14)*30) },
    { module: 'CDSB ISAE3410', score: Math.round(55+rng(15)*35) },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/mrv/data-quality', { scope1, scope2, scope3, ipccTier });
      setResult(r.data);
    } catch {
      const tierBonus = {'Tier 1':0,'Tier 2':0.8,'Tier 3':1.6}[ipccTier]||0;
      setResult({
        dqs: Math.min(5, parseFloat((2.2+tierBonus+rng(20)*0.8).toFixed(1))),
        anomalyScore: (5+rng(21)*25).toFixed(0),
        coverage: (72+rng(22)*20).toFixed(0),
      });
    }
  }, [scope1, scope2, scope3, ipccTier]);

  const dqsColor = v => v>=4?'text-emerald-600':v>=3?'text-amber-600':'text-red-600';

  return (
    <div>
      <Section title="Emission Source Inputs">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Scope 1 (tCO2e)" type="number" value={scope1} onChange={e=>setScope1(e.target.value)} />
          <Inp label="Scope 2 (tCO2e)" type="number" value={scope2} onChange={e=>setScope2(e.target.value)} />
          <Inp label="Scope 3 (tCO2e)" type="number" value={scope3} onChange={e=>setScope3(e.target.value)} />
          <Sel label="IPCC Tier" value={ipccTier} onChange={e=>setIpccTier(e.target.value)}>
            {['Tier 1','Tier 2','Tier 3'].map(o=><option key={o}>{o}</option>)}
          </Sel>
        </div>
        <Btn onClick={run}>Score Data Quality</Btn>
      </Section>
      {result && (
        <Row>
          <KpiCard label="DQS Score" value={<span className={dqsColor(result.dqs)}>{result.dqs}/5</span>} sub="PCAF-style quality score" />
          <KpiCard label="Anomaly Risk" value={`${result.anomalyScore}%`} sub="AI detection flag rate" />
          <KpiCard label="Data Coverage" value={`${result.coverage}%`} sub="Of material sources" />
          <KpiCard label="IPCC Method" value={ipccTier} sub="Activity-based calculation" />
        </Row>
      )}
      <Section title="CDP CDSB Compliance Scores">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={cdpData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="module" tick={{fontSize:11}} />
            <YAxis domain={[0,100]} unit="%" />
            <Tooltip formatter={v=>`${v}%`} />
            <Bar dataKey="score" name="Score" fill="#059669">
              {cdpData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- Satellite Coverage ----------
function SatelliteTab() {
  const [lat, setLat] = useState('51.5');
  const [lng, setLng] = useState('-0.1');
  const [facilitySize, setFacilitySize] = useState('5');
  const [result, setResult] = useState(null);

  const satellites = [
    { sat: 'TROPOMI/S-5P', detect: 18, revisit: 1, cost: 'Free', status: 'Operational' },
    { sat: 'GHGSat-C2', detect: 0.1, revisit: 5, cost: '$$$', status: 'Commercial' },
    { sat: 'Sentinel-5P', detect: 50, revisit: 1, cost: 'Free', status: 'Operational' },
    { sat: 'CarbonMapper', detect: 25, revisit: 7, cost: '$$', status: 'Operational' },
    { sat: 'MethaneSAT', detect: 1, revisit: 7, cost: 'Research', status: 'Operational' },
  ];

  const detectionData = satellites.map(s=>({ name: s.sat.split('/')[0], limit: s.detect }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/mrv/satellite-coverage', { lat, lng, facilitySize });
      setResult(r.data);
    } catch {
      setResult({ coverage: (75+rng(30)*20).toFixed(0), bestSat: 'GHGSat-C2', plume: rng(31)>0.4 });
    }
  }, [lat, lng, facilitySize]);

  return (
    <div>
      <Section title="Facility Location & Size">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Latitude" type="number" value={lat} onChange={e=>setLat(e.target.value)} />
          <Inp label="Longitude" type="number" value={lng} onChange={e=>setLng(e.target.value)} />
          <Inp label="Facility Size (ha)" type="number" value={facilitySize} onChange={e=>setFacilitySize(e.target.value)} />
          <div className="flex items-end"><Btn onClick={run}>Check Coverage</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Satellite Coverage" value={`${result.coverage}%`} sub="Area observable" />
          <KpiCard label="Best Fit Satellite" value={result.bestSat} sub="Optimal for facility size" />
          <KpiCard label="Plume Detectable" value={result.plume?'Yes':'Marginal'} sub="At current facility scale" />
          <KpiCard label="Revisit Frequency" value="1–7 days" sub="Across constellation" />
        </Row>
      )}
      <Section title="Satellite Detection Limit Comparison (tCH4/hr)">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={detectionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{fontSize:11}} />
            <YAxis unit="t/hr" />
            <Tooltip formatter={v=>`${v} t/hr`} />
            <Bar dataKey="limit" name="Detection Limit" fill="#059669">
              {detectionData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Satellite Constellation Reference">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Satellite','Detection Limit (t/hr)','Revisit (days)','Cost Tier','Status'].map(h=><th key={h} className="border border-gray-200 px-3 py-2 text-left font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{satellites.map((r,i)=><tr key={i} className="hover:bg-gray-50"><td className="border border-gray-200 px-3 py-2 font-medium">{r.sat}</td><td className="border border-gray-200 px-3 py-2">{r.detect}</td><td className="border border-gray-200 px-3 py-2">{r.revisit}</td><td className="border border-gray-200 px-3 py-2">{r.cost}</td><td className="border border-gray-200 px-3 py-2"><span className="px-2 py-0.5 rounded-full text-xs bg-emerald-100 text-emerald-700">{r.status}</span></td></tr>)}</tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ---------- Verification Readiness ----------
function VerificationTab() {
  const [standard, setStandard] = useState('ISO 14064-3');
  const [assurance, setAssurance] = useState('limited');
  const [result, setResult] = useState(null);

  const criteria = [
    { name: 'Boundary Definition', weight: 15 },
    { name: 'Quantification Method', weight: 20 },
    { name: 'Data Management', weight: 20 },
    { name: 'Internal Controls', weight: 15 },
    { name: 'Documentation', weight: 15 },
    { name: 'Materiality Assessment', weight: 15 },
  ];

  const readinessData = criteria.map((c,i)=>({
    criterion: c.name,
    score: Math.round(50+rng(i+40)*45),
    threshold: assurance==='reasonable' ? 80 : 65,
  }));

  const verifiers = [
    { org: 'Bureau Veritas', accred: 'ISO 17021', scope: 'GHG, ISAE 3410', region: 'Global' },
    { org: 'SGS Group', accred: 'ISO 14065', scope: 'GHG, ISO 14064-3', region: 'Global' },
    { org: 'DNV', accred: 'ISO 17021', scope: 'ISSA 5000, ISAE 3410', region: 'Global' },
    { org: 'EY', accred: 'IAASB', scope: 'ISAE 3000/3410, CSRD Art.26a', region: 'Global' },
    { org: 'KPMG', accred: 'IAASB', scope: 'ISAE 3000, ISSA 5000', region: 'Global' },
  ];

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/mrv/verification-readiness', { standard, assurance });
      setResult(r.data);
    } catch {
      const avg = readinessData.reduce((a,b)=>a+b.score,0)/readinessData.length;
      setResult({
        overallScore: avg.toFixed(0),
        gaps: readinessData.filter(d=>d.score<d.threshold).map(d=>d.criterion),
      });
    }
  }, [standard, assurance]);

  return (
    <div>
      <Section title="Verification Configuration">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <Sel label="Standard" value={standard} onChange={e=>setStandard(e.target.value)}>
            {['ISO 14064-3','ISAE 3410','ISSA 5000','CSRD Art.26a','GHG Protocol'].map(o=><option key={o}>{o}</option>)}
          </Sel>
          <Sel label="Assurance Level" value={assurance} onChange={e=>setAssurance(e.target.value)}>
            <option value="limited">Limited</option>
            <option value="reasonable">Reasonable</option>
          </Sel>
          <div className="flex items-end"><Btn onClick={run}>Assess Readiness</Btn></div>
        </div>
      </Section>
      {result && (
        <>
          <Row>
            <KpiCard label="Overall Readiness" value={`${result.overallScore}/100`} sub={`${assurance.charAt(0).toUpperCase()+assurance.slice(1)} assurance`} />
            <KpiCard label="Gaps Identified" value={result.gaps.length} sub="Criteria below threshold" />
            <KpiCard label="Standard" value={standard} sub="Target verification framework" />
            <KpiCard label="Readiness Status" value={result.overallScore>=75?'Ready':'Needs Work'} sub="Vs threshold" />
          </Row>
          {result.gaps.length > 0 && (
            <Section title="Gap Items">
              <ul className="space-y-1">
                {result.gaps.map((g,i)=><li key={i} className="flex items-center gap-2 text-sm text-red-700"><span className="text-red-500">&#9888;</span>{g} — below {assurance==='reasonable'?80:65}% threshold</li>)}
              </ul>
            </Section>
          )}
        </>
      )}
      <Section title="Readiness by Criterion">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={readinessData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="criterion" tick={{fontSize:10}} />
            <YAxis domain={[0,100]} unit="%" />
            <Tooltip formatter={v=>`${v}%`} />
            <Legend />
            <Bar dataKey="score" name="Score" fill="#059669" />
            <Bar dataKey="threshold" name="Threshold" fill="#6ee7b7" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Qualified Verifier Organisations">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Organisation','Accreditation','Scope','Coverage'].map(h=><th key={h} className="border border-gray-200 px-3 py-2 text-left font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{verifiers.map((v,i)=><tr key={i} className="hover:bg-gray-50"><td className="border border-gray-200 px-3 py-2 font-medium">{v.org}</td><td className="border border-gray-200 px-3 py-2">{v.accred}</td><td className="border border-gray-200 px-3 py-2">{v.scope}</td><td className="border border-gray-200 px-3 py-2">{v.region}</td></tr>)}</tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ---------- Improvement Plan ----------
function ImprovementTab() {
  const [currentTier, setCurrentTier] = useState('2');
  const [targetTier, setTargetTier] = useState('4');
  const [budget, setBudget] = useState('500');
  const [result, setResult] = useState(null);

  const investmentData = Array.from({length:36},(_,i)=>({
    month: `M${i+1}`,
    cumulative: parseFloat(((i+1)/36 * parseFloat(budget) * (0.6 + rng(i+50)*0.8)).toFixed(0)),
    planned: parseFloat(((i+1)/36 * parseFloat(budget)).toFixed(0)),
  }));

  const techOptions = [
    { tech: 'IoT Continuous Monitoring', cost: 80, timeline: '3 months', tier: '3+', roi: '2.8x' },
    { tech: 'CEMS Installation', cost: 150, timeline: '6 months', tier: '3+', roi: '2.1x' },
    { tech: 'Satellite Subscription', cost: 45, timeline: '1 month', tier: '4+', roi: '3.5x' },
    { tech: 'AI Anomaly Detection', cost: 60, timeline: '2 months', tier: '4+', roi: '4.2x' },
    { tech: 'Digital Twin Platform', cost: 200, timeline: '12 months', tier: '5', roi: '1.9x' },
  ];

  const roiData = techOptions.map(t=>({ name: t.tech.split(' ').slice(0,2).join(' '), roi: parseFloat(t.roi) }));

  const run = useCallback(async () => {
    try {
      const r = await axios.post('/api/v1/mrv/improvement-plan', { currentTier, targetTier, budget });
      setResult(r.data);
    } catch {
      const delta = parseInt(targetTier) - parseInt(currentTier);
      setResult({
        totalCost: Math.round(delta * 120 + rng(60)*80),
        duration: delta * 8,
        emissionReduction: (delta * 12 + rng(61)*5).toFixed(1),
      });
    }
  }, [currentTier, targetTier, budget]);

  return (
    <div>
      <Section title="Improvement Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Current Tier" value={currentTier} onChange={e=>setCurrentTier(e.target.value)}>
            {['1','2','3','4'].map(o=><option key={o} value={o}>Tier {o}</option>)}
          </Sel>
          <Sel label="Target Tier" value={targetTier} onChange={e=>setTargetTier(e.target.value)}>
            {['2','3','4','5'].map(o=><option key={o} value={o}>Tier {o}</option>)}
          </Sel>
          <Inp label="Budget (USD k)" type="number" value={budget} onChange={e=>setBudget(e.target.value)} />
          <div className="flex items-end"><Btn onClick={run}>Generate Plan</Btn></div>
        </div>
      </Section>
      {result && (
        <Row>
          <KpiCard label="Est. Total Cost" value={`$${result.totalCost}k`} sub="Implementation budget" />
          <KpiCard label="Timeline" value={`${result.duration} months`} sub="Tier {currentTier}→{targetTier}" />
          <KpiCard label="Data Quality Gain" value={`+${result.emissionReduction}%`} sub="Accuracy improvement" />
          <KpiCard label="Target Tier" value={`Tier ${targetTier}/5`} sub="MRV capability" />
        </Row>
      )}
      <Section title="Cumulative Investment Timeline (36 months)">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={investmentData.filter((_,i)=>i%3===0)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" tick={{fontSize:10}} />
            <YAxis unit="k" />
            <Tooltip formatter={v=>`$${v}k`} />
            <Legend />
            <Area type="monotone" dataKey="planned" name="Planned" stroke="#059669" fill="#d1fae5" strokeDasharray="5 5" />
            <Area type="monotone" dataKey="cumulative" name="Actual" stroke="#10b981" fill="#a7f3d0" />
          </AreaChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Technology Options & ROI">
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm border-collapse">
            <thead><tr className="bg-gray-50">{['Technology','Cost ($k)','Timeline','Min Tier','ROI'].map(h=><th key={h} className="border border-gray-200 px-3 py-2 text-left font-medium text-gray-700">{h}</th>)}</tr></thead>
            <tbody>{techOptions.map((t,i)=><tr key={i} className="hover:bg-gray-50"><td className="border border-gray-200 px-3 py-2 font-medium">{t.tech}</td><td className="border border-gray-200 px-3 py-2">{t.cost}</td><td className="border border-gray-200 px-3 py-2">{t.timeline}</td><td className="border border-gray-200 px-3 py-2">{t.tier}</td><td className="border border-gray-200 px-3 py-2 text-emerald-600 font-semibold">{t.roi}</td></tr>)}</tbody>
          </table>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={roiData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{fontSize:10}} />
            <YAxis unit="x" />
            <Tooltip formatter={v=>`${v}x`} />
            <Bar dataKey="roi" name="ROI" fill="#059669">
              {roiData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ---------- Main ----------
export default function MRVPage() {
  const [tab, setTab] = useState(0);
  const panels = [<TierTab/>,<DataQualityTab/>,<SatelliteTab/>,<VerificationTab/>,<ImprovementTab/>];
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Climate Data &amp; MRV Infrastructure</h1>
          <p className="text-sm text-gray-500 mt-1">ISO 14064-3:2019 · CDP CDSB · TROPOMI Satellite · GHGSat · IPCC AR6 Uncertainty · AI-Assisted Quality · Digital MRV Tiers 1–5 · ISAE 3410</p>
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
