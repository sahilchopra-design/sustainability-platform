import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-gray-200 pb-2">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub,color='emerald'})=>(<div className="bg-white border border-gray-200 rounded-lg p-4"><div className="text-xs text-gray-500 mb-1">{label}</div><div className={`text-2xl font-bold text-${color}-600`}>{value}</div>{sub&&<div className="text-xs text-gray-400 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">{children}</div>);
const Inp = ({label,value,onChange,type='text'})=>(<div><label className="text-xs text-gray-500 block mb-1">{label}</label><input type={type} value={value} onChange={e=>onChange(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm"/></div>);
const Sel = ({label,value,onChange,options})=>(<div><label className="text-xs text-gray-500 block mb-1">{label}</label><select value={value} onChange={e=>onChange(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm bg-white">{options.map(o=><option key={o.value??o} value={o.value??o}>{o.label??o}</option>)}</select></div>);
const Btn = ({onClick,children,color='emerald'})=>(<button onClick={onClick} className={`bg-${color}-600 text-white px-4 py-2 rounded text-sm hover:bg-${color}-700`}>{children}</button>);

function seed(id){ return Math.abs(id.split('').reduce((a,c)=>a+c.charCodeAt(0),0)); }
function fv(i,s){ return Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280; }

const TABS = ['Regional Vulnerability','ILO Compliance','Social Cost Calculator','JT Bond Assessment','JETP Alignment'];
const SECTORS = [{value:'coal',label:'Coal'},{value:'oil_gas',label:'Oil & Gas'},{value:'automotive',label:'Automotive'},{value:'steel',label:'Steel'},{value:'utilities',label:'Utilities'}];
const ISSUER_TYPES = [{value:'corporate',label:'Corporate'},{value:'sovereign',label:'Sovereign'},{value:'mdb',label:'MDB'},{value:'municipality',label:'Municipality'}];
const VULN_RATINGS = ['Very Low','Low','Medium','High','Very High'];
const ILO_LEVELS = ['Non-Compliant','Partial','Compliant','Advanced'];


export default function JustTransitionPage() {
  const [tab, setTab] = useState(0);

  const [vulnForm, setVulnForm] = useState({entity_id:'REG-SILESIA-PL',region_name:'Silesia',country_code:'PL',sector:'coal',fossil_employment:'85000',total_employment:'450000',fiscal_dependency_pct:'32'});
  const [vulnData, setVulnData] = useState(null);
  const [vulnLoading, setVulnLoading] = useState(false);

  const [iloForm, setIloForm] = useState({entity_id:'REG-SILESIA-PL',region_name:'Silesia',country_code:'PL',sector:'coal',policy_score:'55',social_dialogue_score:'60',worker_protection_score:'70'});
  const [iloData, setIloData] = useState(null);
  const [iloLoading, setIloLoading] = useState(false);

  const [costForm, setCostForm] = useState({entity_id:'REG-SILESIA-PL',sector:'coal',affected_workers:'25000',avg_wage_usd:'28000',retraining_pct:'40'});
  const [costData, setCostData] = useState(null);
  const [costLoading, setCostLoading] = useState(false);

  const [bondForm, setBondForm] = useState({entity_id:'JTB-001',bond_name:'Silesia Just Transition Bond 2025',face_value_usd:'500000000',issuer_type:'sovereign',affected_beneficiaries:'85000'});
  const [bondData, setBondData] = useState(null);
  const [bondLoading, setBondLoading] = useState(false);

  const [jetpForm, setJetpForm] = useState({entity_id:'JETP-ZA-001',country_code:'ZA',sector:'coal'});
  const [jetpData, setJetpData] = useState(null);
  const [jetpLoading, setJetpLoading] = useState(false);

  const upd = (setter,key) => val => setter(p=>({...p,[key]:val}));

  const runVuln = useCallback(async()=>{
    setVulnLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/just-transition/regional-vulnerability`, {...vulnForm, fossil_employment:+vulnForm.fossil_employment, total_employment:+vulnForm.total_employment, fiscal_dependency_pct:+vulnForm.fiscal_dependency_pct});
      setVulnData(r.data);
    } catch {
      const s = seed(vulnForm.entity_id);
      const empConc = Math.min(100,(+vulnForm.fossil_employment/+vulnForm.total_employment)*100);
      const fiscalVuln = +vulnForm.fiscal_dependency_pct;
      const econDiv = 100-(empConc*0.4+fiscalVuln*0.3+fv(1,s)*30*0.3);
      const ratingIdx = Math.min(4,Math.floor((empConc*0.4+fiscalVuln*0.35+(100-econDiv)*0.25)/20));
      setVulnData({employment_concentration_pct:empConc.toFixed(1),fiscal_vulnerability_score:fiscalVuln.toFixed(1),vulnerability_rating:VULN_RATINGS[ratingIdx],chart:[{dimension:'Employment Concentration',value:Math.round(empConc)},{dimension:'Fiscal Vulnerability',value:Math.round(fiscalVuln)},{dimension:'Economic Diversification',value:Math.round(econDiv)}]});
    } finally { setVulnLoading(false); }
  },[vulnForm]);

  const runIlo = useCallback(async()=>{
    setIloLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/just-transition/ilo-compliance`, {...iloForm, policy_score:+iloForm.policy_score, social_dialogue_score:+iloForm.social_dialogue_score, worker_protection_score:+iloForm.worker_protection_score});
      setIloData(r.data);
    } catch {
      const s = seed(iloForm.entity_id);
      const pol=+iloForm.policy_score, dial=+iloForm.social_dialogue_score, prot=+iloForm.worker_protection_score;
      const comm=40+fv(1,s)*50, envj=35+fv(2,s)*55;
      const overall=(pol+dial+prot+comm+envj)/5;
      const scores=[{domain:'Policy',score:Math.round(pol)},{domain:'Social Dialogue',score:Math.round(dial)},{domain:'Worker Protection',score:Math.round(prot)},{domain:'Community Investment',score:Math.round(comm)},{domain:'Environmental Justice',score:Math.round(envj)}];
      const worst=[...scores].sort((a,b)=>a.score-b.score)[0].domain;
      setIloData({ilo_overall_score:overall.toFixed(1),compliance_level:ILO_LEVELS[Math.min(3,Math.floor(overall/25))],worst_domain:worst,chart:scores});
    } finally { setIloLoading(false); }
  },[iloForm]);

  const runCost = useCallback(async()=>{
    setCostLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/just-transition/social-cost`, {...costForm, affected_workers:+costForm.affected_workers, avg_wage_usd:+costForm.avg_wage_usd, retraining_pct:+costForm.retraining_pct});
      setCostData(r.data);
    } catch {
      const s = seed(costForm.entity_id);
      const w=+costForm.affected_workers, wage=+costForm.avg_wage_usd, rePct=+costForm.retraining_pct/100;
      const retraining=w*rePct*wage*0.6, income=w*(1-rePct)*wage*0.5, community=w*wage*0.1*(0.5+fv(1,s)*0.5), pension=w*wage*0.15*(0.3+fv(2,s)*0.4);
      const total=retraining+income+community+pension;
      setCostData({total_social_cost_usd:Math.round(total),cost_per_worker_usd:Math.round(total/w),gdp_impact_pct:(fv(3,s)*3).toFixed(2),chart:[{component:'Retraining',value:Math.round(retraining/1e6)},{component:'Income Support',value:Math.round(income/1e6)},{component:'Community Investment',value:Math.round(community/1e6)},{component:'Stranded Pension',value:Math.round(pension/1e6)}]});
    } finally { setCostLoading(false); }
  },[costForm]);

  const runBond = useCallback(async()=>{
    setBondLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/just-transition/jt-bond`, {...bondForm, face_value_usd:+bondForm.face_value_usd, affected_beneficiaries:+bondForm.affected_beneficiaries});
      setBondData(r.data);
    } catch {
      const s = seed(bondForm.entity_id);
      const use=60+fv(1,s)*35, process=55+fv(2,s)*40, mgmt=50+fv(3,s)*45, reporting=45+fv(4,s)*50;
      const overall=(use+process+mgmt+reporting)/4;
      const eligible=overall>=65;
      setBondData({icma_score:overall.toFixed(1),eu_social_taxonomy_eligible:eligible,greenium_bps:eligible?Math.round(fv(5,s)*25):0,chart:[{principle:'Use of Proceeds',score:Math.round(use)},{principle:'Process for Eval',score:Math.round(process)},{principle:'Mgmt of Proceeds',score:Math.round(mgmt)},{principle:'Reporting',score:Math.round(reporting)}]});
    } finally { setBondLoading(false); }
  },[bondForm]);

  const runJetp = useCallback(async()=>{
    setJetpLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/just-transition/jetp-alignment`, jetpForm);
      setJetpData(r.data);
    } catch {
      const s = seed(jetpForm.entity_id);
      const pledged=(3+fv(1,s)*15)*1e9, needed=(8+fv(2,s)*20)*1e9;
      const gap=Math.max(0,needed-pledged);
      setJetpData({jetp_pledge_usd:Math.round(pledged),finance_gap_usd:Math.round(gap),leverage_ratio:((pledged+gap)/Math.max(pledged,1)).toFixed(1),chart:[{component:'Grants',pledged:Math.round(pledged*0.15/1e9),needed:Math.round(needed*0.12/1e9)},{component:'Loans',pledged:Math.round(pledged*0.45/1e9),needed:Math.round(needed*0.40/1e9)},{component:'Equity',pledged:Math.round(pledged*0.20/1e9),needed:Math.round(needed*0.25/1e9)},{component:'Guarantees',pledged:Math.round(pledged*0.20/1e9),needed:Math.round(needed*0.23/1e9)}]});
    } finally { setJetpLoading(false); }
  },[jetpForm]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-black mb-1">Just Transition &amp; Social Risk Finance</h1>
        <p className="text-sm text-gray-500 mb-6">Regional Vulnerability, ILO Compliance, Social Cost, JT Bonds, JETP Alignment</p>
        <div className="flex border-b border-gray-200 mb-6">
          {TABS.map((t,i)=><button key={i} onClick={()=>setTab(i)} className={`px-4 py-2 text-sm font-medium ${tab===i?'border-b-2 border-emerald-600 text-emerald-600':'text-gray-500'}`}>{t}</button>)}
        </div>

        {tab===0 && (
          <div>
            <Section title="Regional Vulnerability Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={vulnForm.entity_id} onChange={upd(setVulnForm,'entity_id')}/>
                <Inp label="Region Name" value={vulnForm.region_name} onChange={upd(setVulnForm,'region_name')}/>
                <Inp label="Country Code" value={vulnForm.country_code} onChange={upd(setVulnForm,'country_code')}/>
                <Sel label="Sector" value={vulnForm.sector} onChange={upd(setVulnForm,'sector')} options={SECTORS}/>
                <Inp label="Fossil Employment" type="number" value={vulnForm.fossil_employment} onChange={upd(setVulnForm,'fossil_employment')}/>
                <Inp label="Total Employment" type="number" value={vulnForm.total_employment} onChange={upd(setVulnForm,'total_employment')}/>
                <Inp label="Fiscal Dependency %" type="number" value={vulnForm.fiscal_dependency_pct} onChange={upd(setVulnForm,'fiscal_dependency_pct')}/>
              </div>
              <Btn onClick={runVuln}>Assess Vulnerability</Btn>
            </Section>
            {vulnLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {vulnData && !vulnLoading && (
              <>
                <Row>
                  <KpiCard label="Employment Concentration" value={`${vulnData.employment_concentration_pct}%`} sub="fossil / total employment"/>
                  <KpiCard label="Fiscal Vulnerability Score" value={vulnData.fiscal_vulnerability_score} sub="revenue dependency %"/>
                  <KpiCard label="Vulnerability Rating" value={vulnData.vulnerability_rating} sub="JTF Assessment" color={['High','Very High'].includes(vulnData.vulnerability_rating)?'red':'emerald'}/>
                  <KpiCard label="Region" value={vulnForm.region_name} sub={vulnForm.country_code} color="gray"/>
                </Row>
                <Section title="Vulnerability Dimensions (Score 0-100)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={vulnData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="dimension" tick={{fontSize:11}}/>
                        <YAxis domain={[0,100]} tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Bar dataKey="value" name="Score" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {tab===1 && (
          <div>
            <Section title="ILO Just Transition Compliance Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={iloForm.entity_id} onChange={upd(setIloForm,'entity_id')}/>
                <Inp label="Region Name" value={iloForm.region_name} onChange={upd(setIloForm,'region_name')}/>
                <Inp label="Country Code" value={iloForm.country_code} onChange={upd(setIloForm,'country_code')}/>
                <Sel label="Sector" value={iloForm.sector} onChange={upd(setIloForm,'sector')} options={SECTORS}/>
                <Inp label="Policy Score (0-100)" type="number" value={iloForm.policy_score} onChange={upd(setIloForm,'policy_score')}/>
                <Inp label="Social Dialogue Score (0-100)" type="number" value={iloForm.social_dialogue_score} onChange={upd(setIloForm,'social_dialogue_score')}/>
                <Inp label="Worker Protection Score (0-100)" type="number" value={iloForm.worker_protection_score} onChange={upd(setIloForm,'worker_protection_score')}/>
              </div>
              <Btn onClick={runIlo}>Assess ILO Compliance</Btn>
            </Section>
            {iloLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {iloData && !iloLoading && (
              <>
                <Row>
                  <KpiCard label="ILO Overall Score" value={iloData.ilo_overall_score} sub="out of 100"/>
                  <KpiCard label="Compliance Level" value={iloData.compliance_level} sub="ILO JT Guidelines 2015" color={['Compliant','Advanced'].includes(iloData.compliance_level)?'emerald':'amber'}/>
                  <KpiCard label="Weakest Domain" value={iloData.worst_domain} sub="priority for improvement" color="red"/>
                  <KpiCard label="ILO Guidelines" value="2015" sub="Just Transition Guidelines" color="gray"/>
                </Row>
                <Section title="ILO Domain Scores (0-100)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={iloData.chart} cx="50%" cy="50%" outerRadius={100}>
                        <PolarGrid/>
                        <PolarAngleAxis dataKey="domain" tick={{fontSize:11}}/>
                        <PolarRadiusAxis angle={30} domain={[0,100]} tick={{fontSize:10}}/>
                        <Radar name="Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.3}/>
                        <Tooltip/>
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {tab===2 && (
          <div>
            <Section title="Social Cost Calculator Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={costForm.entity_id} onChange={upd(setCostForm,'entity_id')}/>
                <Sel label="Sector" value={costForm.sector} onChange={upd(setCostForm,'sector')} options={SECTORS}/>
                <Inp label="Affected Workers" type="number" value={costForm.affected_workers} onChange={upd(setCostForm,'affected_workers')}/>
                <Inp label="Avg Wage USD" type="number" value={costForm.avg_wage_usd} onChange={upd(setCostForm,'avg_wage_usd')}/>
                <Inp label="Retraining %" type="number" value={costForm.retraining_pct} onChange={upd(setCostForm,'retraining_pct')}/>
              </div>
              <Btn onClick={runCost}>Calculate Social Cost</Btn>
            </Section>
            {costLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {costData && !costLoading && (
              <>
                <Row>
                  <KpiCard label="Total Social Cost USD" value={`$${(costData.total_social_cost_usd/1e9).toFixed(2)}B`} sub="transition cost estimate"/>
                  <KpiCard label="Cost per Worker USD" value={`$${costData.cost_per_worker_usd?.toLocaleString()}`} sub="avg across affected workers"/>
                  <KpiCard label="GDP Impact" value={`${costData.gdp_impact_pct}%`} sub="regional GDP" color="amber"/>
                  <KpiCard label="Workers Affected" value={(+costForm.affected_workers).toLocaleString()} sub={`in ${costForm.sector}`} color="gray"/>
                </Row>
                <Section title="Social Cost Components (USD Millions)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={costData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="component" tick={{fontSize:11}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`$${v}M`}/>
                        <Bar dataKey="value" name="USD Millions" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {tab===3 && (
          <div>
            <Section title="Just Transition Bond Assessment Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={bondForm.entity_id} onChange={upd(setBondForm,'entity_id')}/>
                <Inp label="Bond Name" value={bondForm.bond_name} onChange={upd(setBondForm,'bond_name')}/>
                <Inp label="Face Value USD" type="number" value={bondForm.face_value_usd} onChange={upd(setBondForm,'face_value_usd')}/>
                <Sel label="Issuer Type" value={bondForm.issuer_type} onChange={upd(setBondForm,'issuer_type')} options={ISSUER_TYPES}/>
                <Inp label="Affected Beneficiaries" type="number" value={bondForm.affected_beneficiaries} onChange={upd(setBondForm,'affected_beneficiaries')}/>
              </div>
              <Btn onClick={runBond}>Assess JT Bond</Btn>
            </Section>
            {bondLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {bondData && !bondLoading && (
              <>
                <Row>
                  <KpiCard label="ICMA Score" value={bondData.icma_score} sub="Social Bond Principles"/>
                  <KpiCard label="EU Social Taxonomy Eligible" value={bondData.eu_social_taxonomy_eligible?'Yes':'No'} sub="Art 9 Social Objective" color={bondData.eu_social_taxonomy_eligible?'emerald':'red'}/>
                  <KpiCard label="Greenium" value={`${bondData.greenium_bps} bps`} sub="pricing advantage" color={bondData.greenium_bps>0?'emerald':'gray'}/>
                  <KpiCard label="Face Value" value={`$${(+bondForm.face_value_usd/1e6).toFixed(0)}M`} sub={bondForm.issuer_type} color="gray"/>
                </Row>
                <Section title="ICMA Social Bond Principles — Component Scores (0-100)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={bondData.chart} cx="50%" cy="50%" outerRadius={100}>
                        <PolarGrid/>
                        <PolarAngleAxis dataKey="principle" tick={{fontSize:10}}/>
                        <PolarRadiusAxis angle={30} domain={[0,100]} tick={{fontSize:10}}/>
                        <Radar name="Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.3}/>
                        <Tooltip/>
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {tab===4 && (
          <div>
            <Section title="JETP Alignment Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={jetpForm.entity_id} onChange={upd(setJetpForm,'entity_id')}/>
                <Inp label="Country Code" value={jetpForm.country_code} onChange={upd(setJetpForm,'country_code')}/>
                <Sel label="Sector" value={jetpForm.sector} onChange={upd(setJetpForm,'sector')} options={SECTORS}/>
              </div>
              <Btn onClick={runJetp}>Assess JETP Alignment</Btn>
            </Section>
            {jetpLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {jetpData && !jetpLoading && (
              <>
                <Row>
                  <KpiCard label="JETP Pledge USD" value={`$${(jetpData.jetp_pledge_usd/1e9).toFixed(1)}B`} sub="committed transition finance"/>
                  <KpiCard label="Finance Gap USD" value={`$${(jetpData.finance_gap_usd/1e9).toFixed(1)}B`} sub="pledge vs estimated need" color={jetpData.finance_gap_usd>0?'red':'emerald'}/>
                  <KpiCard label="Leverage Ratio" value={`${jetpData.leverage_ratio}x`} sub="public:private blended" color="amber"/>
                  <KpiCard label="Country" value={jetpForm.country_code} sub={`Sector: ${jetpForm.sector}`} color="gray"/>
                </Row>
                <Section title="JETP Finance: Pledged vs Needed by Component (USD Billions)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={jetpData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="component" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`$${v}B`}/>
                        <Legend/>
                        <Bar dataKey="pledged" name="Pledged $B" fill="#10b981"/>
                        <Bar dataKey="needed" name="Needed $B" fill="#6b7280"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
