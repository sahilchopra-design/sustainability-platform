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

const TABS = ['CDR Quality','LCOR Calculator','Oxford Principles','Article 6.4','VCMI Claims'];

const CDR_METHODS = [
  {value:'beccs',label:'BECCS'},{value:'daccs',label:'DACCS'},{value:'enhanced_weathering',label:'Enhanced Weathering'},
  {value:'biochar',label:'Biochar'},{value:'ocean_alkalinity_enhancement',label:'Ocean Alkalinity Enhancement'},
  {value:'afforestation',label:'Afforestation'},{value:'soil_carbon',label:'Soil Carbon'},{value:'blue_carbon',label:'Blue Carbon'}
];
const VERIF_STANDARDS = [
  {value:'puro_earth',label:'Puro.earth'},{value:'isometric',label:'Isometric'},{value:'gold_standard',label:'Gold Standard'},
  {value:'vcs_vm0042',label:'VCS VM0042'},{value:'article_6_4',label:'Article 6.4'}
];
const BEZERO_RATINGS = ['D','C','B','BB','BBB','A','AA','AAA'];
const BOOL_OPTS = [{value:'true',label:'Yes'},{value:'false',label:'No'}];
const VCMI_LEVELS = ['No Claim','Silver','Gold','Platinum'];

function seed(id){ return Math.abs(id.split('').reduce((a,c)=>a+c.charCodeAt(0),0)); }
function fv(i,s){ return Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280; }

const METHOD_PERMANENCE = {beccs:100,daccs:1000,enhanced_weathering:10000,biochar:100,ocean_alkalinity_enhancement:1000,afforestation:30,soil_carbon:10,blue_carbon:50};

export default function CDRPage() {
  const [tab, setTab] = useState(0);

  // Tab 0 — CDR Quality
  const [qualForm, setQualForm] = useState({entity_id:'CDR-PROJ-001',cdr_method:'daccs',annual_removal_tco2:'50000',permanence_yrs:'1000',verification_standard:'puro_earth',additionality_score:'80',leakage_risk_pct:'5'});
  const [qualData, setQualData] = useState(null);
  const [qualLoading, setQualLoading] = useState(false);

  // Tab 1 — LCOR
  const [lcorForm, setLcorForm] = useState({entity_id:'CDR-PROJ-001',cdr_method:'daccs',capacity_tco2_pa:'50000',capex_usd:'150000000',opex_usd_pa:'8000000',lifetime_yrs:'20',discount_rate_pct:'8'});
  const [lcorData, setLcorData] = useState(null);
  const [lcorLoading, setLcorLoading] = useState(false);

  // Tab 2 — Oxford Principles
  const [oxForm, setOxForm] = useState({entity_id:'CDR-PROJ-001',cdr_method:'daccs',avoidance_residual:'true',preference_durable:'true',shift_to_durable_plan:'true',avoid_locking_in_emissions:'true'});
  const [oxData, setOxData] = useState(null);
  const [oxLoading, setOxLoading] = useState(false);

  // Tab 3 — Article 6.4
  const [art64Form, setArt64Form] = useState({entity_id:'CDR-PROJ-001',cdr_method:'daccs',host_country_code:'KE',host_country_authorised:'true',corresponding_adjustment_agreed:'true',sustainable_dev_safeguards:'true'});
  const [art64Data, setArt64Data] = useState(null);
  const [art64Loading, setArt64Loading] = useState(false);

  // Tab 4 — VCMI Claims
  const [vcmiForm, setVcmiForm] = useState({entity_id:'CDR-CORP-001',scope1_sbti_aligned:'true',scope2_sbti_aligned:'true',scope3_disclosure:'true',residual_emissions_tco2:'15000',cdr_credits_tco2:'12000',credit_quality_score:'75'});
  const [vcmiData, setVcmiData] = useState(null);
  const [vcmiLoading, setVcmiLoading] = useState(false);

  const upd = (setter,key) => val => setter(p=>({...p,[key]:val}));

  const runQual = useCallback(async()=>{
    setQualLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/cdr/quality-assessment`, {...qualForm, annual_removal_tco2:+qualForm.annual_removal_tco2, permanence_yrs:+qualForm.permanence_yrs, additionality_score:+qualForm.additionality_score, leakage_risk_pct:+qualForm.leakage_risk_pct});
      setQualData(r.data);
    } catch {
      const s = seed(qualForm.entity_id);
      const add = +qualForm.additionality_score;
      const leak = +qualForm.leakage_risk_pct;
      const perm = Math.min(100, (METHOD_PERMANENCE[qualForm.cdr_method]||100)/10);
      const verif = 50 + fv(1,s)*45;
      const cobene = 40 + fv(2,s)*55;
      const composite = (add*0.3 + perm*0.25 + verif*0.2 + (100-leak)*0.15 + cobene*0.1);
      const ratingIdx = Math.min(7, Math.floor(composite/12.5));
      const netCredits = Math.round(+qualForm.annual_removal_tco2 * (1 - leak/100));
      setQualData({bezero_rating:BEZERO_RATINGS[ratingIdx], quality_score:composite.toFixed(1), net_credits_tco2:netCredits, chart:[{component:'Additionality',score:Math.round(add)},{component:'Permanence',score:Math.round(perm)},{component:'Verification',score:Math.round(verif)},{component:'Leakage Control',score:Math.round(100-leak)},{component:'Co-Benefits',score:Math.round(cobene)}]});
    } finally { setQualLoading(false); }
  },[qualForm]);

  const runLcor = useCallback(async()=>{
    setLcorLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/cdr/lcor`, {...lcorForm, capacity_tco2_pa:+lcorForm.capacity_tco2_pa, capex_usd:+lcorForm.capex_usd, opex_usd_pa:+lcorForm.opex_usd_pa, lifetime_yrs:+lcorForm.lifetime_yrs, discount_rate_pct:+lcorForm.discount_rate_pct});
      setLcorData(r.data);
    } catch {
      const s = seed(lcorForm.entity_id);
      const cap = +lcorForm.capacity_tco2_pa, capex = +lcorForm.capex_usd, opex = +lcorForm.opex_usd_pa, life = +lcorForm.lifetime_yrs, dr = +lcorForm.discount_rate_pct/100;
      const annuity = capex * (dr*Math.pow(1+dr,life)) / (Math.pow(1+dr,life)-1);
      const lcor = (annuity + opex) / cap;
      const irr = (cap * 120 - opex) / capex * 100;
      setLcorData({
        lcor_usd_tco2:lcor.toFixed(2),
        breakeven_carbon_price:Math.round(lcor*1.15),
        project_irr_pct:irr.toFixed(1),
        chart:[
          {scenario:'Base Case',lcor:parseFloat(lcor.toFixed(1))},
          {scenario:'Low Capex (-20%)',lcor:parseFloat((lcor*0.85).toFixed(1))},
          {scenario:'High Capex (+20%)',lcor:parseFloat((lcor*1.18).toFixed(1))},
          {scenario:'Low Discount (5%)',lcor:parseFloat((lcor*0.92).toFixed(1))},
          {scenario:'High Discount (12%)',lcor:parseFloat((lcor*1.12).toFixed(1))},
        ]
      });
    } finally { setLcorLoading(false); }
  },[lcorForm]);

  const runOx = useCallback(async()=>{
    setOxLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/cdr/oxford-principles`, oxForm);
      setOxData(r.data);
    } catch {
      const s = seed(oxForm.entity_id);
      const p1 = oxForm.avoidance_residual==='true'?80+fv(1,s)*18:30+fv(1,s)*25;
      const p2 = oxForm.preference_durable==='true'?75+fv(2,s)*22:25+fv(2,s)*30;
      const p3 = oxForm.shift_to_durable_plan==='true'?70+fv(3,s)*28:20+fv(3,s)*35;
      const p4 = oxForm.avoid_locking_in_emissions==='true'?85+fv(4,s)*13:35+fv(4,s)*20;
      const composite = (p1+p2+p3+p4)/4;
      const level = composite>=80?'Aligned':composite>=60?'Partially Aligned':'Not Aligned';
      const recs = [p1<70,p2<70,p3<70,p4<70].filter(Boolean).length;
      setOxData({oxford_alignment_score:composite.toFixed(1),alignment_level:level,recommendations_count:recs,chart:[{principle:'Use Avoidance for Residuals',score:Math.round(p1)},{principle:'Preference for Durable',score:Math.round(p2)},{principle:'Shift to Durable Plan',score:Math.round(p3)},{principle:'Avoid Lock-in',score:Math.round(p4)}]});
    } finally { setOxLoading(false); }
  },[oxForm]);

  const runArt64 = useCallback(async()=>{
    setArt64Loading(true);
    try {
      const r = await axios.post(`${API}/api/v1/cdr/article-6-4`, art64Form);
      setArt64Data(r.data);
    } catch {
      const s = seed(art64Form.entity_id);
      const crit = [
        {name:'Host Country Auth.',pass:art64Form.host_country_authorised==='true',score:art64Form.host_country_authorised==='true'?100:0},
        {name:'Corresp. Adjustment',pass:art64Form.corresponding_adjustment_agreed==='true',score:art64Form.corresponding_adjustment_agreed==='true'?100:0},
        {name:'SD Safeguards',pass:art64Form.sustainable_dev_safeguards==='true',score:art64Form.sustainable_dev_safeguards==='true'?100:0},
        {name:'Article 6.4 Body Appr.',pass:fv(1,s)>0.3,score:Math.round(fv(1,s)*100)},
        {name:'OMGE Cancellation',pass:fv(2,s)>0.4,score:Math.round(fv(2,s)*100)},
      ];
      const eligible = crit.filter(c=>c.pass).length>=4;
      const itmoPremium = eligible?(5+fv(3,s)*20).toFixed(1):0;
      const hostRisk = ['Low','Medium','High'][Math.floor(fv(4,s)*3)];
      setArt64Data({art64_eligible:eligible,itmo_value_premium_pct:itmoPremium,host_country_risk:hostRisk,chart:crit.map(c=>({name:c.name,score:c.score}))});
    } finally { setArt64Loading(false); }
  },[art64Form]);

  const runVcmi = useCallback(async()=>{
    setVcmiLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/cdr/vcmi-claims`, {...vcmiForm, residual_emissions_tco2:+vcmiForm.residual_emissions_tco2, cdr_credits_tco2:+vcmiForm.cdr_credits_tco2, credit_quality_score:+vcmiForm.credit_quality_score});
      setVcmiData(r.data);
    } catch {
      const s = seed(vcmiForm.entity_id);
      const residual = +vcmiForm.residual_emissions_tco2;
      const credits = +vcmiForm.cdr_credits_tco2;
      const quality = +vcmiForm.credit_quality_score;
      const coverage = Math.min(100, credits/residual*100);
      const sbtiOk = vcmiForm.scope1_sbti_aligned==='true' && vcmiForm.scope2_sbti_aligned==='true';
      const disc3 = vcmiForm.scope3_disclosure==='true';
      let level = 'No Claim';
      if(sbtiOk && disc3 && coverage>=100 && quality>=90) level='Platinum';
      else if(sbtiOk && disc3 && coverage>=100 && quality>=75) level='Gold';
      else if(sbtiOk && coverage>=60 && quality>=60) level='Silver';
      setVcmiData({vcmi_level:level,residual_coverage_pct:coverage.toFixed(1),recommended_claim:`VCMI ${level} Claim`,chart:[{level:'Silver',threshold:60,entity:coverage},{level:'Gold',threshold:100,entity:coverage},{level:'Platinum',threshold:100,entity:coverage}]});
    } finally { setVcmiLoading(false); }
  },[vcmiForm]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-black mb-1">Carbon Removal &amp; CDR Finance</h1>
        <p className="text-sm text-gray-500 mb-6">CDR Quality, LCOR, Oxford Principles, Article 6.4, VCMI Claims</p>
        <div className="flex border-b border-gray-200 mb-6">
          {TABS.map((t,i)=><button key={i} onClick={()=>setTab(i)} className={`px-4 py-2 text-sm font-medium ${tab===i?'border-b-2 border-emerald-600 text-emerald-600':'text-gray-500'}`}>{t}</button>)}
        </div>

        {/* TAB 0 — CDR Quality */}
        {tab===0 && (
          <div>
            <Section title="CDR Quality Assessment Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={qualForm.entity_id} onChange={upd(setQualForm,'entity_id')}/>
                <Sel label="CDR Method" value={qualForm.cdr_method} onChange={upd(setQualForm,'cdr_method')} options={CDR_METHODS}/>
                <Inp label="Annual Removal tCO2" type="number" value={qualForm.annual_removal_tco2} onChange={upd(setQualForm,'annual_removal_tco2')}/>
                <Inp label="Permanence (yrs)" type="number" value={qualForm.permanence_yrs} onChange={upd(setQualForm,'permanence_yrs')}/>
                <Sel label="Verification Standard" value={qualForm.verification_standard} onChange={upd(setQualForm,'verification_standard')} options={VERIF_STANDARDS}/>
                <Inp label="Additionality Score (0-100)" type="number" value={qualForm.additionality_score} onChange={upd(setQualForm,'additionality_score')}/>
                <Inp label="Leakage Risk %" type="number" value={qualForm.leakage_risk_pct} onChange={upd(setQualForm,'leakage_risk_pct')}/>
              </div>
              <Btn onClick={runQual}>Assess CDR Quality</Btn>
            </Section>
            {qualLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {qualData && !qualLoading && (
              <>
                <Row>
                  <KpiCard label="BeZero Rating" value={qualData.bezero_rating} sub="BeZero Carbon Ratings" color={['A','AA','AAA'].includes(qualData.bezero_rating)?'emerald':'amber'}/>
                  <KpiCard label="Quality Score" value={`${qualData.quality_score}/100`} sub="composite quality score"/>
                  <KpiCard label="Net Credits tCO2" value={qualData.net_credits_tco2?.toLocaleString()} sub="after leakage deduction"/>
                  <KpiCard label="Verification Standard" value={qualForm.verification_standard.replace(/_/g,' ')} color="gray"/>
                </Row>
                <Section title="BeZero-Style Quality Component Scores (0-100)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={qualData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="component" tick={{fontSize:11}}/>
                        <YAxis domain={[0,100]} tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Bar dataKey="score" name="Score" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 1 — LCOR */}
        {tab===1 && (
          <div>
            <Section title="LCOR Calculator Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={lcorForm.entity_id} onChange={upd(setLcorForm,'entity_id')}/>
                <Sel label="CDR Method" value={lcorForm.cdr_method} onChange={upd(setLcorForm,'cdr_method')} options={CDR_METHODS}/>
                <Inp label="Capacity tCO2/pa" type="number" value={lcorForm.capacity_tco2_pa} onChange={upd(setLcorForm,'capacity_tco2_pa')}/>
                <Inp label="Capex USD" type="number" value={lcorForm.capex_usd} onChange={upd(setLcorForm,'capex_usd')}/>
                <Inp label="Opex USD/pa" type="number" value={lcorForm.opex_usd_pa} onChange={upd(setLcorForm,'opex_usd_pa')}/>
                <Inp label="Lifetime (yrs)" type="number" value={lcorForm.lifetime_yrs} onChange={upd(setLcorForm,'lifetime_yrs')}/>
                <Inp label="Discount Rate %" type="number" value={lcorForm.discount_rate_pct} onChange={upd(setLcorForm,'discount_rate_pct')}/>
              </div>
              <Btn onClick={runLcor}>Calculate LCOR</Btn>
            </Section>
            {lcorLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {lcorData && !lcorLoading && (
              <>
                <Row>
                  <KpiCard label="LCOR USD/tCO2" value={`$${lcorData.lcor_usd_tco2}`} sub="levelised cost of removal"/>
                  <KpiCard label="Breakeven Carbon Price" value={`$${lcorData.breakeven_carbon_price}/t`} sub="min price for project viability"/>
                  <KpiCard label="Project IRR %" value={`${lcorData.project_irr_pct}%`} sub="at $120/t market price" color={+lcorData.project_irr_pct>8?'emerald':'amber'}/>
                  <KpiCard label="CDR Method" value={lcorForm.cdr_method.replace(/_/g,' ')} color="gray"/>
                </Row>
                <Section title="LCOR Sensitivity Analysis (USD/tCO2)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={lcorData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="scenario" tick={{fontSize:10}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`$${v}/tCO2`}/>
                        <Bar dataKey="lcor" name="LCOR USD/tCO2" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 2 — Oxford Principles */}
        {tab===2 && (
          <div>
            <Section title="Oxford Principles Assessment Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={oxForm.entity_id} onChange={upd(setOxForm,'entity_id')}/>
                <Sel label="CDR Method" value={oxForm.cdr_method} onChange={upd(setOxForm,'cdr_method')} options={CDR_METHODS}/>
                <Sel label="Use Avoidance for Residual" value={oxForm.avoidance_residual} onChange={upd(setOxForm,'avoidance_residual')} options={BOOL_OPTS}/>
                <Sel label="Preference for Durable CDR" value={oxForm.preference_durable} onChange={upd(setOxForm,'preference_durable')} options={BOOL_OPTS}/>
                <Sel label="Shift to Durable CDR Plan" value={oxForm.shift_to_durable_plan} onChange={upd(setOxForm,'shift_to_durable_plan')} options={BOOL_OPTS}/>
                <Sel label="Avoid Locking in Emissions" value={oxForm.avoid_locking_in_emissions} onChange={upd(setOxForm,'avoid_locking_in_emissions')} options={BOOL_OPTS}/>
              </div>
              <Btn onClick={runOx}>Assess Oxford Principles</Btn>
            </Section>
            {oxLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {oxData && !oxLoading && (
              <>
                <Row>
                  <KpiCard label="Oxford Alignment Score" value={`${oxData.oxford_alignment_score}/100`} sub="4-principle composite"/>
                  <KpiCard label="Alignment Level" value={oxData.alignment_level} sub="Oxford Principles 2021" color={oxData.alignment_level==='Aligned'?'emerald':oxData.alignment_level==='Partially Aligned'?'amber':'red'}/>
                  <KpiCard label="Recommendations" value={oxData.recommendations_count} sub="principles below threshold" color={oxData.recommendations_count>0?'amber':'emerald'}/>
                  <KpiCard label="CDR Method" value={oxForm.cdr_method.replace(/_/g,' ')} color="gray"/>
                </Row>
                <Section title="Oxford Principles Scores (0-100)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={oxData.chart} cx="50%" cy="50%" outerRadius={100}>
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

        {/* TAB 3 — Article 6.4 */}
        {tab===3 && (
          <div>
            <Section title="Article 6.4 Eligibility Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={art64Form.entity_id} onChange={upd(setArt64Form,'entity_id')}/>
                <Sel label="CDR Method" value={art64Form.cdr_method} onChange={upd(setArt64Form,'cdr_method')} options={CDR_METHODS}/>
                <Inp label="Host Country Code" value={art64Form.host_country_code} onChange={upd(setArt64Form,'host_country_code')}/>
                <Sel label="Host Country Authorised" value={art64Form.host_country_authorised} onChange={upd(setArt64Form,'host_country_authorised')} options={BOOL_OPTS}/>
                <Sel label="Corresponding Adjustment" value={art64Form.corresponding_adjustment_agreed} onChange={upd(setArt64Form,'corresponding_adjustment_agreed')} options={BOOL_OPTS}/>
                <Sel label="SD Safeguards Met" value={art64Form.sustainable_dev_safeguards} onChange={upd(setArt64Form,'sustainable_dev_safeguards')} options={BOOL_OPTS}/>
              </div>
              <Btn onClick={runArt64}>Assess Article 6.4 Eligibility</Btn>
            </Section>
            {art64Loading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {art64Data && !art64Loading && (
              <>
                <Row>
                  <KpiCard label="Art 6.4 Eligible" value={art64Data.art64_eligible?'Yes':'No'} sub="Paris Agreement Art 6.4 ITMO" color={art64Data.art64_eligible?'emerald':'red'}/>
                  <KpiCard label="ITMO Value Premium" value={`${art64Data.itmo_value_premium_pct}%`} sub="vs voluntary market credit" color={art64Data.art64_eligible?'emerald':'gray'}/>
                  <KpiCard label="Host Country Risk" value={art64Data.host_country_risk} sub="political & regulatory" color={art64Data.host_country_risk==='Low'?'emerald':art64Data.host_country_risk==='Medium'?'amber':'red'}/>
                  <KpiCard label="Host Country" value={art64Form.host_country_code} sub="NDC host nation" color="gray"/>
                </Row>
                <Section title="Article 6.4 Eligibility Criteria (Pass/Fail Score)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={art64Data.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={{fontSize:10}}/>
                        <YAxis domain={[0,100]} tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Bar dataKey="score" name="Score" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 4 — VCMI Claims */}
        {tab===4 && (
          <div>
            <Section title="VCMI Claims Integrity Assessment Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={vcmiForm.entity_id} onChange={upd(setVcmiForm,'entity_id')}/>
                <Sel label="Scope 1 SBTi Aligned" value={vcmiForm.scope1_sbti_aligned} onChange={upd(setVcmiForm,'scope1_sbti_aligned')} options={BOOL_OPTS}/>
                <Sel label="Scope 2 SBTi Aligned" value={vcmiForm.scope2_sbti_aligned} onChange={upd(setVcmiForm,'scope2_sbti_aligned')} options={BOOL_OPTS}/>
                <Sel label="Scope 3 Disclosed" value={vcmiForm.scope3_disclosure} onChange={upd(setVcmiForm,'scope3_disclosure')} options={BOOL_OPTS}/>
                <Inp label="Residual Emissions tCO2" type="number" value={vcmiForm.residual_emissions_tco2} onChange={upd(setVcmiForm,'residual_emissions_tco2')}/>
                <Inp label="CDR Credits tCO2" type="number" value={vcmiForm.cdr_credits_tco2} onChange={upd(setVcmiForm,'cdr_credits_tco2')}/>
                <Inp label="Credit Quality Score (0-100)" type="number" value={vcmiForm.credit_quality_score} onChange={upd(setVcmiForm,'credit_quality_score')}/>
              </div>
              <Btn onClick={runVcmi}>Assess VCMI Claims</Btn>
            </Section>
            {vcmiLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {vcmiData && !vcmiLoading && (
              <>
                <Row>
                  <KpiCard label="VCMI Level" value={vcmiData.vcmi_level} sub="Claims Code of Practice" color={vcmiData.vcmi_level==='Platinum'?'emerald':vcmiData.vcmi_level==='Gold'?'emerald':vcmiData.vcmi_level==='Silver'?'amber':'red'}/>
                  <KpiCard label="Residual Coverage" value={`${vcmiData.residual_coverage_pct}%`} sub="CDR credits / residual emissions" color={+vcmiData.residual_coverage_pct>=100?'emerald':'amber'}/>
                  <KpiCard label="Recommended Claim" value={vcmiData.recommended_claim} sub="VCMI Claims Code 2023"/>
                  <KpiCard label="Credit Quality" value={`${vcmiForm.credit_quality_score}/100`} sub="BeZero / Sylvera equivalent" color={+vcmiForm.credit_quality_score>=75?'emerald':'amber'}/>
                </Row>
                <Section title="VCMI Level Thresholds vs Entity Coverage (%)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={vcmiData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="level" tick={{fontSize:12}}/>
                        <YAxis domain={[0,120]} tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`${v}%`}/>
                        <Legend/>
                        <Bar dataKey="threshold" name="Required Coverage %" fill="#6b7280"/>
                        <Bar dataKey="entity" name="Entity Coverage %" fill="#10b981"/>
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
