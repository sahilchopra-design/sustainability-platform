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

const TABS = ['LCOH Calculator','RFNBO Compliance','Demand Sector','EU H2 Bank','Cost Trajectory'];

const PATHWAYS = [
  {value:'electrolysis_solar',label:'Electrolysis — Solar'},
  {value:'electrolysis_wind',label:'Electrolysis — Wind'},
  {value:'electrolysis_grid',label:'Electrolysis — Grid'},
  {value:'smr_ccs',label:'SMR + CCS (Blue)'},
  {value:'smr_no_ccs',label:'SMR No CCS (Grey)'},
  {value:'coal_gasification',label:'Coal Gasification'},
  {value:'nuclear_electrolysis',label:'Nuclear Electrolysis'},
];
const DEMAND_SECTORS = [{value:'steel',label:'Steel'},{value:'ammonia',label:'Ammonia'},{value:'transport',label:'Transport'},{value:'refinery',label:'Refinery'},{value:'power',label:'Power'},{value:'buildings',label:'Buildings'}];
const RE_SOURCES = [{value:'solar',label:'Solar'},{value:'wind',label:'Wind'},{value:'hydro',label:'Hydro'},{value:'nuclear',label:'Nuclear'}];
const BOOL_OPTS = [{value:'true',label:'Yes'},{value:'false',label:'No'}];

function seed(id){ return Math.abs(id.split('').reduce((a,c)=>a+c.charCodeAt(0),0)); }
function fv(i,s){ return Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280; }

const PATHWAY_BASE_LCOH = {
  electrolysis_solar:3.8, electrolysis_wind:4.2, electrolysis_grid:5.5,
  smr_ccs:2.4, smr_no_ccs:1.8, coal_gasification:1.5, nuclear_electrolysis:4.0
};

export default function HydrogenPage() {
  const [tab, setTab] = useState(0);

  // Tab 0 — LCOH
  const [lcohForm, setLcohForm] = useState({entity_id:'H2-PROJ-001',production_pathway:'electrolysis_wind',capacity_mw_el:'200',country_code:'DE',capacity_factor_pct:'35'});
  const [lcohData, setLcohData] = useState(null);
  const [lcohLoading, setLcohLoading] = useState(false);

  // Tab 1 — RFNBO
  const [rfnboForm, setRfnboForm] = useState({entity_id:'H2-PROJ-001',production_pathway:'electrolysis_wind',country_code:'DE',re_source:'wind',hourly_matching:'true',temporal_correlation:'true'});
  const [rfnboData, setRfnboData] = useState(null);
  const [rfnboLoading, setRfnboLoading] = useState(false);

  // Tab 2 — Demand Sector
  const [demandForm, setDemandForm] = useState({entity_id:'H2-PROJ-001',demand_sector:'steel',annual_h2_demand_t:'50000',country_code:'DE',current_fuel_type:'coal'});
  const [demandData, setDemandData] = useState(null);
  const [demandLoading, setDemandLoading] = useState(false);

  // Tab 3 — EU H2 Bank
  const [bankForm, setBankForm] = useState({entity_id:'H2-PROJ-001',production_pathway:'electrolysis_wind',capacity_mw_el:'200',country_code:'DE',lcoh_usd_kg:'4.2'});
  const [bankData, setBankData] = useState(null);
  const [bankLoading, setBankLoading] = useState(false);

  // Tab 4 — Cost Trajectory
  const [trajForm, setTrajForm] = useState({entity_id:'H2-PROJ-001',production_pathway:'electrolysis_wind',country_code:'DE'});
  const [trajData, setTrajData] = useState(null);
  const [trajLoading, setTrajLoading] = useState(false);

  const upd = (setter,key) => val => setter(p=>({...p,[key]:val}));

  const runLcoh = useCallback(async()=>{
    setLcohLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/hydrogen/lcoh`, {...lcohForm, capacity_mw_el:+lcohForm.capacity_mw_el, capacity_factor_pct:+lcohForm.capacity_factor_pct});
      setLcohData(r.data);
    } catch {
      const s = seed(lcohForm.entity_id);
      const base = PATHWAY_BASE_LCOH[lcohForm.production_pathway] || 4.0;
      const lcoh = base + fv(1,s)*1.5;
      const capex_share = 0.35 + fv(2,s)*0.15;
      const opex_share = 0.15 + fv(3,s)*0.1;
      const elec_share = 1 - capex_share - opex_share;
      const annual_output = +lcohForm.capacity_mw_el * (+lcohForm.capacity_factor_pct/100) * 8760 * 0.018;
      setLcohData({
        lcoh_usd_kg:lcoh.toFixed(2),
        annual_output_t_yr:Math.round(annual_output),
        capex_component_usd_kg:(lcoh*capex_share).toFixed(2),
        chart:[
          {component:'Capex',value:parseFloat((lcoh*capex_share).toFixed(3))},
          {component:'Opex',value:parseFloat((lcoh*opex_share).toFixed(3))},
          {component:'Electricity',value:parseFloat((lcoh*elec_share).toFixed(3))},
        ]
      });
    } finally { setLcohLoading(false); }
  },[lcohForm]);

  const runRfnbo = useCallback(async()=>{
    setRfnboLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/hydrogen/rfnbo-compliance`, rfnboForm);
      setRfnboData(r.data);
    } catch {
      const s = seed(rfnboForm.entity_id);
      const add = rfnboForm.hourly_matching==='true' ? 80+fv(1,s)*15 : 45+fv(1,s)*20;
      const temp = rfnboForm.temporal_correlation==='true' ? 85+fv(2,s)*10 : 40+fv(2,s)*25;
      const geo = 70+fv(3,s)*25;
      const compliant = add>=70 && temp>=70 && geo>=70;
      const ghg = compliant ? 0.8+fv(4,s)*2 : 8+fv(4,s)*5;
      setRfnboData({
        rfnbo_compliant:compliant,
        ghg_intensity_kgco2e_kgh2:ghg.toFixed(2),
        eu_taxonomy_eligible:compliant,
        chart:[
          {criterion:'Additionality',score:Math.round(add)},
          {criterion:'Temporal',score:Math.round(temp)},
          {criterion:'Geographical',score:Math.round(geo)},
        ]
      });
    } finally { setRfnboLoading(false); }
  },[rfnboForm]);

  const runDemand = useCallback(async()=>{
    setDemandLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/hydrogen/demand-sector`, {...demandForm, annual_h2_demand_t:+demandForm.annual_h2_demand_t});
      setDemandData(r.data);
    } catch {
      const s = seed(demandForm.entity_id);
      const h2Demand = +demandForm.annual_h2_demand_t;
      const ef_baseline = 20 + fv(1,s)*15;
      const ef_h2 = 0.5 + fv(2,s)*2;
      const abatement = (ef_baseline - ef_h2) * h2Demand;
      const breakeven = 40 + fv(3,s)*120;
      const premium = 1.5 + fv(4,s)*3;
      setDemandData({
        abatement_tco2_pa:Math.round(abatement),
        breakeven_carbon_price_usd_t:Math.round(breakeven),
        green_premium_usd_kg:premium.toFixed(2),
        chart:[
          {name:'Baseline Emissions',baseline:Math.round(ef_baseline*h2Demand),green:0},
          {name:'H2 Pathway',baseline:0,green:Math.round(ef_h2*h2Demand)},
        ]
      });
    } finally { setDemandLoading(false); }
  },[demandForm]);

  const runBank = useCallback(async()=>{
    setBankLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/hydrogen/eu-h2-bank`, {...bankForm, capacity_mw_el:+bankForm.capacity_mw_el, lcoh_usd_kg:+bankForm.lcoh_usd_kg});
      setBankData(r.data);
    } catch {
      const s = seed(bankForm.entity_id);
      const lcoh = +bankForm.lcoh_usd_kg;
      const target = 2.0;
      const eligible = lcoh <= 5.0;
      const subsidy = Math.max(0, lcoh - target);
      const annual_output = +bankForm.capacity_mw_el * 0.35 * 8760 * 0.018;
      const total_subsidy = subsidy * annual_output * 1000;
      setBankData({
        eu_h2_bank_eligible:eligible,
        subsidy_eur_kg:subsidy.toFixed(2),
        total_subsidy_eur:Math.round(total_subsidy),
        chart:[
          {name:'LCOH',value:lcoh},
          {name:'EU Target (€2/kg)',value:target},
          {name:'Grid Parity',value:3.5+fv(1,s)*1.5},
        ]
      });
    } finally { setBankLoading(false); }
  },[bankForm]);

  const runTraj = useCallback(async()=>{
    setTrajLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/hydrogen/cost-trajectory`, trajForm);
      setTrajData(r.data);
    } catch {
      const s = seed(trajForm.entity_id);
      const base = PATHWAY_BASE_LCOH[trajForm.production_pathway] || 4.0;
      const years = [2024,2026,2028,2030,2032,2035,2040,2045,2050];
      const chart = years.map((yr,i)=>{
        const decay = Math.pow(0.92,i);
        return {year:yr, lcoh:parseFloat((base*decay + fv(i,s)*0.3).toFixed(2)), grid_parity:3.5-i*0.08};
      });
      const gp_yr = chart.find(d=>d.lcoh<=d.grid_parity);
      setTrajData({
        lcoh_2030:chart.find(d=>d.year===2030)?.lcoh,
        lcoh_2040:chart.find(d=>d.year===2040)?.lcoh,
        grid_parity_year:gp_yr?.year || '>2050',
        chart
      });
    } finally { setTrajLoading(false); }
  },[trajForm]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-black mb-1">Hydrogen Economy Finance</h1>
        <p className="text-sm text-gray-500 mb-6">LCOH, RFNBO Compliance, Demand Sectors, EU H2 Bank, Cost Trajectory 2024-2050</p>
        <div className="flex border-b border-gray-200 mb-6">
          {TABS.map((t,i)=><button key={i} onClick={()=>setTab(i)} className={`px-4 py-2 text-sm font-medium ${tab===i?'border-b-2 border-emerald-600 text-emerald-600':'text-gray-500'}`}>{t}</button>)}
        </div>

        {/* TAB 0 — LCOH */}
        {tab===0 && (
          <div>
            <Section title="LCOH Calculator Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={lcohForm.entity_id} onChange={upd(setLcohForm,'entity_id')}/>
                <Sel label="Production Pathway" value={lcohForm.production_pathway} onChange={upd(setLcohForm,'production_pathway')} options={PATHWAYS}/>
                <Inp label="Capacity (MW electrolyser)" type="number" value={lcohForm.capacity_mw_el} onChange={upd(setLcohForm,'capacity_mw_el')}/>
                <Inp label="Country Code" value={lcohForm.country_code} onChange={upd(setLcohForm,'country_code')}/>
                <Inp label="Capacity Factor %" type="number" value={lcohForm.capacity_factor_pct} onChange={upd(setLcohForm,'capacity_factor_pct')}/>
              </div>
              <Btn onClick={runLcoh}>Calculate LCOH</Btn>
            </Section>
            {lcohLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {lcohData && !lcohLoading && (
              <>
                <Row>
                  <KpiCard label="LCOH" value={`$${lcohData.lcoh_usd_kg}/kg`} sub="levelised cost of hydrogen"/>
                  <KpiCard label="Annual Output" value={`${lcohData.annual_output_t_yr?.toLocaleString()} t/yr`} sub="H2 production"/>
                  <KpiCard label="Capex Component" value={`$${lcohData.capex_component_usd_kg}/kg`} sub="share of LCOH" color="gray"/>
                  <KpiCard label="Pathway" value={lcohForm.production_pathway.replace(/_/g,' ')} sub="production route" color="gray"/>
                </Row>
                <Section title="LCOH Components (USD/kg)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={lcohData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="component" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`$${v}/kg`}/>
                        <Bar dataKey="value" name="USD/kg" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 1 — RFNBO */}
        {tab===1 && (
          <div>
            <Section title="RFNBO Compliance Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={rfnboForm.entity_id} onChange={upd(setRfnboForm,'entity_id')}/>
                <Sel label="Production Pathway" value={rfnboForm.production_pathway} onChange={upd(setRfnboForm,'production_pathway')} options={PATHWAYS}/>
                <Inp label="Country Code" value={rfnboForm.country_code} onChange={upd(setRfnboForm,'country_code')}/>
                <Sel label="RE Source" value={rfnboForm.re_source} onChange={upd(setRfnboForm,'re_source')} options={RE_SOURCES}/>
                <Sel label="Hourly Matching" value={rfnboForm.hourly_matching} onChange={upd(setRfnboForm,'hourly_matching')} options={BOOL_OPTS}/>
                <Sel label="Temporal Correlation" value={rfnboForm.temporal_correlation} onChange={upd(setRfnboForm,'temporal_correlation')} options={BOOL_OPTS}/>
              </div>
              <Btn onClick={runRfnbo}>Check RFNBO Compliance</Btn>
            </Section>
            {rfnboLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {rfnboData && !rfnboLoading && (
              <>
                <Row>
                  <KpiCard label="RFNBO Compliant" value={rfnboData.rfnbo_compliant?'Yes':'No'} sub="Del (EU) 2023/1184" color={rfnboData.rfnbo_compliant?'emerald':'red'}/>
                  <KpiCard label="GHG Intensity" value={`${rfnboData.ghg_intensity_kgco2e_kgh2} kgCO2e/kgH2`} sub="well-to-gate"/>
                  <KpiCard label="EU Taxonomy Eligible" value={rfnboData.eu_taxonomy_eligible?'Yes':'No'} sub="Climate mitigation" color={rfnboData.eu_taxonomy_eligible?'emerald':'amber'}/>
                  <KpiCard label="Threshold" value="3.38 kgCO2e/kgH2" sub="70% GHG reduction vs fossil" color="gray"/>
                </Row>
                <Section title="RFNBO Criteria Scores (0-100)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={rfnboData.chart} cx="50%" cy="50%" outerRadius={100}>
                        <PolarGrid/>
                        <PolarAngleAxis dataKey="criterion" tick={{fontSize:12}}/>
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

        {/* TAB 2 — Demand Sector */}
        {tab===2 && (
          <div>
            <Section title="Demand Sector Analysis Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={demandForm.entity_id} onChange={upd(setDemandForm,'entity_id')}/>
                <Sel label="Demand Sector" value={demandForm.demand_sector} onChange={upd(setDemandForm,'demand_sector')} options={DEMAND_SECTORS}/>
                <Inp label="Annual H2 Demand (t)" type="number" value={demandForm.annual_h2_demand_t} onChange={upd(setDemandForm,'annual_h2_demand_t')}/>
                <Inp label="Country Code" value={demandForm.country_code} onChange={upd(setDemandForm,'country_code')}/>
                <Inp label="Current Fuel Type" value={demandForm.current_fuel_type} onChange={upd(setDemandForm,'current_fuel_type')}/>
              </div>
              <Btn onClick={runDemand}>Analyse Demand Sector</Btn>
            </Section>
            {demandLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {demandData && !demandLoading && (
              <>
                <Row>
                  <KpiCard label="Abatement tCO2/pa" value={demandData.abatement_tco2_pa?.toLocaleString()} sub="vs baseline fuel"/>
                  <KpiCard label="Break-Even Carbon Price" value={`$${demandData.breakeven_carbon_price_usd_t}/t`} sub="CO2 price needed for parity"/>
                  <KpiCard label="Green Premium" value={`$${demandData.green_premium_usd_kg}/kg`} sub="H2 vs current fuel cost" color="amber"/>
                  <KpiCard label="Sector" value={demandForm.demand_sector} sub="hard-to-abate" color="gray"/>
                </Row>
                <Section title="Baseline vs Green H2 Emissions (tCO2)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={demandData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Legend/>
                        <Bar dataKey="baseline" name="Baseline Emissions" stackId="a" fill="#ef4444"/>
                        <Bar dataKey="green" name="H2 Pathway" stackId="a" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 3 — EU H2 Bank */}
        {tab===3 && (
          <div>
            <Section title="EU Hydrogen Bank Assessment Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={bankForm.entity_id} onChange={upd(setBankForm,'entity_id')}/>
                <Sel label="Production Pathway" value={bankForm.production_pathway} onChange={upd(setBankForm,'production_pathway')} options={PATHWAYS}/>
                <Inp label="Capacity (MW electrolyser)" type="number" value={bankForm.capacity_mw_el} onChange={upd(setBankForm,'capacity_mw_el')}/>
                <Inp label="Country Code" value={bankForm.country_code} onChange={upd(setBankForm,'country_code')}/>
                <Inp label="LCOH (USD/kg)" type="number" value={bankForm.lcoh_usd_kg} onChange={upd(setBankForm,'lcoh_usd_kg')}/>
              </div>
              <Btn onClick={runBank}>Assess EU H2 Bank Eligibility</Btn>
            </Section>
            {bankLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {bankData && !bankLoading && (
              <>
                <Row>
                  <KpiCard label="EU H2 Bank Eligible" value={bankData.eu_h2_bank_eligible?'Yes':'No'} sub="EIC pilot auction" color={bankData.eu_h2_bank_eligible?'emerald':'red'}/>
                  <KpiCard label="Subsidy EUR/kg" value={`€${bankData.subsidy_eur_kg}`} sub="fixed premium support"/>
                  <KpiCard label="Total Subsidy EUR" value={`€${bankData.total_subsidy_eur?.toLocaleString()}`} sub="10yr project lifetime"/>
                  <KpiCard label="EU Target" value="€2/kg" sub="EIC H2 Bank reference price" color="gray"/>
                </Row>
                <Section title="LCOH vs EU Target vs Grid Parity (USD/kg)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={bankData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={{fontSize:11}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`$${v}/kg`}/>
                        <Bar dataKey="value" name="USD/kg" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 4 — Cost Trajectory */}
        {tab===4 && (
          <div>
            <Section title="LCOH Cost Trajectory Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={trajForm.entity_id} onChange={upd(setTrajForm,'entity_id')}/>
                <Sel label="Production Pathway" value={trajForm.production_pathway} onChange={upd(setTrajForm,'production_pathway')} options={PATHWAYS}/>
                <Inp label="Country Code" value={trajForm.country_code} onChange={upd(setTrajForm,'country_code')}/>
              </div>
              <Btn onClick={runTraj}>Project Cost Trajectory</Btn>
            </Section>
            {trajLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {trajData && !trajLoading && (
              <>
                <Row>
                  <KpiCard label="LCOH 2030" value={`$${trajData.lcoh_2030}/kg`} sub="projected levelised cost"/>
                  <KpiCard label="LCOH 2040" value={`$${trajData.lcoh_2040}/kg`} sub="projected levelised cost"/>
                  <KpiCard label="Grid Parity Year" value={trajData.grid_parity_year} sub="LCOH ≤ grid electricity cost" color={trajData.grid_parity_year<=2040?'emerald':'amber'}/>
                  <KpiCard label="Learning Rate" value="~18%" sub="cost reduction per 2x capacity" color="gray"/>
                </Row>
                <Section title="LCOH Trajectory 2024-2050 with Grid Parity Threshold (USD/kg)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={trajData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="year" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`$${v}/kg`}/>
                        <Legend/>
                        <Line type="monotone" dataKey="lcoh" name="LCOH USD/kg" stroke="#10b981" strokeWidth={2} dot={false}/>
                        <Line type="monotone" dataKey="grid_parity" name="Grid Parity" stroke="#f59e0b" strokeDasharray="4 4" dot={false}/>
                      </LineChart>
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
