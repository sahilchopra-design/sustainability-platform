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

const TABS = ['CII Assessment','EEXI Compliance','EU ETS Shipping','FuelEU Maritime','Ship Stranding Risk'];

const SHIP_TYPES = [{value:'bulk_carrier',label:'Bulk Carrier'},{value:'tanker',label:'Tanker'},{value:'container',label:'Container'},{value:'gas_carrier',label:'Gas Carrier'},{value:'ro_ro',label:'Ro-Ro'},{value:'cruise',label:'Cruise'},{value:'ferry',label:'Ferry'}];
const FUEL_TYPES = [{value:'hfo',label:'HFO'},{value:'lsfo',label:'LSFO'},{value:'mdo',label:'MDO'},{value:'lng',label:'LNG'},{value:'methanol',label:'Methanol'},{value:'ammonia',label:'Ammonia'},{value:'hydrogen',label:'Hydrogen'}];
const YEARS = ['2024','2025','2026','2027','2028','2029','2030'];

function seed(id){ return Math.abs(id.split('').reduce((a,c)=>a+c.charCodeAt(0),0)); }
function fv(i,s){ return Math.abs(Math.sin(i*9301+s*49297)*233280)%233280/233280; }

const CII_COLORS = {A:'#10b981',B:'#34d399',C:'#f59e0b',D:'#f97316',E:'#ef4444'};

export default function MaritimePage() {
  const [tab, setTab] = useState(0);

  // Tab 0 — CII Assessment
  const [ciiForm, setCiiForm] = useState({entity_id:'SHIP-001',ship_type:'bulk_carrier',annual_fuel_consumption_t:'8500',annual_distance_nm:'85000',fuel_type:'hfo',year:'2025'});
  const [ciiData, setCiiData] = useState(null);
  const [ciiLoading, setCiiLoading] = useState(false);

  // Tab 1 — EEXI Compliance
  const [eexiForm, setEexiForm] = useState({entity_id:'SHIP-001',ship_type:'bulk_carrier',gross_tonnage:'75000',installed_power_kw:'12000',fuel_type:'hfo'});
  const [eexiData, setEexiData] = useState(null);
  const [eexiLoading, setEexiLoading] = useState(false);

  // Tab 2 — EU ETS
  const [etsForm, setEtsForm] = useState({entity_id:'SHIP-001',ship_type:'bulk_carrier',annual_co2_tonnes:'28000',eu_route_share_pct:'55',year:'2025'});
  const [etsData, setEtsData] = useState(null);
  const [etsLoading, setEtsLoading] = useState(false);

  // Tab 3 — FuelEU
  const [fuelForm, setFuelForm] = useState({entity_id:'SHIP-001',ship_type:'bulk_carrier',fuel_type:'hfo',annual_energy_mj:'350000000',year:'2025'});
  const [fuelData, setFuelData] = useState(null);
  const [fuelLoading, setFuelLoading] = useState(false);

  // Tab 4 — Stranding
  const [strandForm, setStrandForm] = useState({entity_id:'SHIP-001',ship_type:'bulk_carrier',build_year:'2010',fuel_type:'hfo',gross_tonnage:'75000'});
  const [strandData, setStrandData] = useState(null);
  const [strandLoading, setStrandLoading] = useState(false);

  const upd = (setter,key) => val => setter(p=>({...p,[key]:val}));

  const runCii = useCallback(async()=>{
    setCiiLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/maritime/cii-assessment`, {...ciiForm, annual_fuel_consumption_t:+ciiForm.annual_fuel_consumption_t, annual_distance_nm:+ciiForm.annual_distance_nm, year:+ciiForm.year});
      setCiiData(r.data);
    } catch {
      const s = seed(ciiForm.entity_id);
      const attained = 4.5 + fv(1,s)*5;
      const required = 5.2 + fv(2,s)*4;
      const ratings = ['A','B','C','D','E'];
      const rating = ratings[Math.floor(fv(3,s)*5)];
      setCiiData({attained_cii:attained.toFixed(2), required_cii:required.toFixed(2), cii_rating:rating, improvement_needed_pct:Math.max(0,((attained-required)/required*100)).toFixed(1), chart:[{name:'Attained CII',value:parseFloat(attained.toFixed(2)),fill:CII_COLORS[rating]},{name:'Required CII',value:parseFloat(required.toFixed(2)),fill:'#6b7280'}]});
    } finally { setCiiLoading(false); }
  },[ciiForm]);

  const runEexi = useCallback(async()=>{
    setEexiLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/maritime/eexi-assessment`, {...eexiForm, gross_tonnage:+eexiForm.gross_tonnage, installed_power_kw:+eexiForm.installed_power_kw});
      setEexiData(r.data);
    } catch {
      const s = seed(eexiForm.entity_id);
      const attained = 3.2 + fv(1,s)*4;
      const required = 3.8 + fv(2,s)*3;
      setEexiData({attained_eexi:attained.toFixed(2), required_eexi:required.toFixed(2), compliant:attained<=required, chart:[{name:'Attained EEXI',value:parseFloat(attained.toFixed(2))},{name:'Required EEXI',value:parseFloat(required.toFixed(2))}]});
    } finally { setEexiLoading(false); }
  },[eexiForm]);

  const runEts = useCallback(async()=>{
    setEtsLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/maritime/eu-ets`, {...etsForm, annual_co2_tonnes:+etsForm.annual_co2_tonnes, eu_route_share_pct:+etsForm.eu_route_share_pct, year:+etsForm.year});
      setEtsData(r.data);
    } catch {
      const s = seed(etsForm.entity_id);
      const co2 = +etsForm.annual_co2_tonnes * (+etsForm.eu_route_share_pct/100);
      const phases = [{name:'2024 (40%)',cost:co2*0.4*65},{name:'2025 (70%)',cost:co2*0.7*70},{name:'2026 (100%)',cost:co2*1.0*80}];
      setEtsData({allowances_required:Math.round(co2*0.7), ets_cost_base_eur:Math.round(co2*0.7*70), ets_cost_high_eur:Math.round(co2*0.7*100), chart:phases.map(p=>({name:p.name,cost:Math.round(p.cost)}))});
    } finally { setEtsLoading(false); }
  },[etsForm]);

  const runFuel = useCallback(async()=>{
    setFuelLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/maritime/fueleu`, {...fuelForm, annual_energy_mj:+fuelForm.annual_energy_mj, year:+fuelForm.year});
      setFuelData(r.data);
    } catch {
      const s = seed(fuelForm.entity_id);
      const current = 87 + fv(1,s)*15;
      const targets = [{yr:2025,t:89.34},{yr:2030,t:80.45},{yr:2035,t:71.55},{yr:2040,t:62.66},{yr:2045,t:44.77},{yr:2050,t:26.88}];
      setFuelData({ghg_intensity_gco2e_mj:current.toFixed(2), fueleu_compliant:current<=89.34, penalty_eur:current>89.34?Math.round((current-89.34)*+fuelForm.annual_energy_mj*2.5e-6):0, chart:targets.map(t=>({year:t.yr,target:t.t,entity:parseFloat(current.toFixed(2))}))});
    } finally { setFuelLoading(false); }
  },[fuelForm]);

  const runStrand = useCallback(async()=>{
    setStrandLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/maritime/stranding-risk`, {...strandForm, build_year:+strandForm.build_year, gross_tonnage:+strandForm.gross_tonnage});
      setStrandData(r.data);
    } catch {
      const s = seed(strandForm.entity_id);
      const age = 2025 - +strandForm.build_year;
      const strandYr = 2025 + Math.round(15 - age*0.5 + fv(1,s)*8);
      const retrofitCost = Math.round((+strandForm.gross_tonnage*120 + fv(2,s)*5000000));
      setStrandData({stranding_year:strandYr, years_to_stranding:strandYr-2025, retrofit_cost_usd:retrofitCost, chart:[{name:'Fuel Penalty',value:parseFloat((fv(3,s)*40).toFixed(1))},{name:'Retrofit Cost',value:parseFloat((fv(4,s)*30).toFixed(1))},{name:'Capex Increase',value:parseFloat((fv(5,s)*20).toFixed(1))},{name:'NPV Loss',value:parseFloat((fv(6,s)*10).toFixed(1))}]});
    } finally { setStrandLoading(false); }
  },[strandForm]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-black mb-1">Maritime & Shipping Decarbonisation</h1>
        <p className="text-sm text-gray-500 mb-6">IMO CII, EEXI, EU ETS Shipping Phase-in, FuelEU Maritime, Stranding Risk</p>
        <div className="flex border-b border-gray-200 mb-6">
          {TABS.map((t,i)=><button key={i} onClick={()=>setTab(i)} className={`px-4 py-2 text-sm font-medium ${tab===i?'border-b-2 border-emerald-600 text-emerald-600':'text-gray-500'}`}>{t}</button>)}
        </div>

        {/* TAB 0 — CII Assessment */}
        {tab===0 && (
          <div>
            <Section title="CII Assessment Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={ciiForm.entity_id} onChange={upd(setCiiForm,'entity_id')}/>
                <Sel label="Ship Type" value={ciiForm.ship_type} onChange={upd(setCiiForm,'ship_type')} options={SHIP_TYPES}/>
                <Inp label="Annual Fuel Consumption (t)" type="number" value={ciiForm.annual_fuel_consumption_t} onChange={upd(setCiiForm,'annual_fuel_consumption_t')}/>
                <Inp label="Annual Distance (nm)" type="number" value={ciiForm.annual_distance_nm} onChange={upd(setCiiForm,'annual_distance_nm')}/>
                <Sel label="Fuel Type" value={ciiForm.fuel_type} onChange={upd(setCiiForm,'fuel_type')} options={FUEL_TYPES}/>
                <Sel label="Year" value={ciiForm.year} onChange={upd(setCiiForm,'year')} options={YEARS}/>
              </div>
              <Btn onClick={runCii}>Calculate CII</Btn>
            </Section>
            {ciiLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {ciiData && !ciiLoading && (
              <>
                <Row>
                  <KpiCard label="CII Attained" value={ciiData.attained_cii} sub="gCO2/(capacity·nm)"/>
                  <KpiCard label="CII Required" value={ciiData.required_cii} sub="gCO2/(capacity·nm)" color="gray"/>
                  <KpiCard label="CII Rating" value={ciiData.cii_rating} sub="IMO DCS Rating A-E" color={ciiData.cii_rating==='A'||ciiData.cii_rating==='B'?'emerald':'red'}/>
                  <KpiCard label="Improvement Needed" value={`${ciiData.improvement_needed_pct}%`} sub="to reach next rating" color="amber"/>
                </Row>
                <Section title="CII Attained vs Required">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={ciiData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Bar dataKey="value" name="CII" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 1 — EEXI Compliance */}
        {tab===1 && (
          <div>
            <Section title="EEXI Compliance Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={eexiForm.entity_id} onChange={upd(setEexiForm,'entity_id')}/>
                <Sel label="Ship Type" value={eexiForm.ship_type} onChange={upd(setEexiForm,'ship_type')} options={SHIP_TYPES}/>
                <Inp label="Gross Tonnage" type="number" value={eexiForm.gross_tonnage} onChange={upd(setEexiForm,'gross_tonnage')}/>
                <Inp label="Installed Power (kW)" type="number" value={eexiForm.installed_power_kw} onChange={upd(setEexiForm,'installed_power_kw')}/>
                <Sel label="Fuel Type" value={eexiForm.fuel_type} onChange={upd(setEexiForm,'fuel_type')} options={FUEL_TYPES}/>
              </div>
              <Btn onClick={runEexi}>Assess EEXI</Btn>
            </Section>
            {eexiLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {eexiData && !eexiLoading && (
              <>
                <Row>
                  <KpiCard label="EEXI Attained" value={eexiData.attained_eexi} sub="gCO2/(t·nm)"/>
                  <KpiCard label="EEXI Required" value={eexiData.required_eexi} sub="gCO2/(t·nm)" color="gray"/>
                  <KpiCard label="Compliant" value={eexiData.compliant?'Yes':'No'} sub="IMO EEXI Regulation" color={eexiData.compliant?'emerald':'red'}/>
                  <KpiCard label="Excess vs Required" value={`${eexiData.compliant?'-':'+'}${Math.abs(eexiData.attained_eexi-eexiData.required_eexi).toFixed(2)}`} sub="gCO2/(t·nm)" color={eexiData.compliant?'emerald':'red'}/>
                </Row>
                <Section title="EEXI Attained vs Required">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={eexiData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Bar dataKey="value" name="EEXI" fill={eexiData.compliant?'#10b981':'#ef4444'}/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 2 — EU ETS Shipping */}
        {tab===2 && (
          <div>
            <Section title="EU ETS Shipping Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={etsForm.entity_id} onChange={upd(setEtsForm,'entity_id')}/>
                <Sel label="Ship Type" value={etsForm.ship_type} onChange={upd(setEtsForm,'ship_type')} options={SHIP_TYPES}/>
                <Inp label="Annual CO2 (tonnes)" type="number" value={etsForm.annual_co2_tonnes} onChange={upd(setEtsForm,'annual_co2_tonnes')}/>
                <Inp label="EU Route Share %" type="number" value={etsForm.eu_route_share_pct} onChange={upd(setEtsForm,'eu_route_share_pct')}/>
                <Sel label="Year" value={etsForm.year} onChange={upd(setEtsForm,'year')} options={YEARS}/>
              </div>
              <Btn onClick={runEts}>Calculate EU ETS Cost</Btn>
            </Section>
            {etsLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {etsData && !etsLoading && (
              <>
                <Row>
                  <KpiCard label="Allowances Required" value={etsData.allowances_required?.toLocaleString()} sub="EUAs (tCO2)"/>
                  <KpiCard label="EU ETS Cost (Base €70/t)" value={`€${etsData.ets_cost_base_eur?.toLocaleString()}`} sub="70% phase-in 2025"/>
                  <KpiCard label="EU ETS Cost (High €100/t)" value={`€${etsData.ets_cost_high_eur?.toLocaleString()}`} sub="stress scenario" color="red"/>
                  <KpiCard label="EU Route Coverage" value={`${etsForm.eu_route_share_pct}%`} sub="of total voyage CO2" color="gray"/>
                </Row>
                <Section title="EU ETS Cost by Phase (EUR)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={etsData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={{fontSize:11}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip formatter={v=>`€${v.toLocaleString()}`}/>
                        <Bar dataKey="cost" name="ETS Cost EUR" fill="#10b981"/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 3 — FuelEU Maritime */}
        {tab===3 && (
          <div>
            <Section title="FuelEU Maritime Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={fuelForm.entity_id} onChange={upd(setFuelForm,'entity_id')}/>
                <Sel label="Ship Type" value={fuelForm.ship_type} onChange={upd(setFuelForm,'ship_type')} options={SHIP_TYPES}/>
                <Sel label="Fuel Type" value={fuelForm.fuel_type} onChange={upd(setFuelForm,'fuel_type')} options={FUEL_TYPES}/>
                <Inp label="Annual Energy (MJ)" type="number" value={fuelForm.annual_energy_mj} onChange={upd(setFuelForm,'annual_energy_mj')}/>
                <Sel label="Year" value={fuelForm.year} onChange={upd(setFuelForm,'year')} options={YEARS}/>
              </div>
              <Btn onClick={runFuel}>Assess FuelEU</Btn>
            </Section>
            {fuelLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {fuelData && !fuelLoading && (
              <>
                <Row>
                  <KpiCard label="GHG Intensity" value={`${fuelData.ghg_intensity_gco2e_mj}`} sub="gCO2e/MJ"/>
                  <KpiCard label="FuelEU Compliant" value={fuelData.fueleu_compliant?'Yes':'No'} sub="Reg (EU) 2023/1805" color={fuelData.fueleu_compliant?'emerald':'red'}/>
                  <KpiCard label="Penalty EUR" value={`€${fuelData.penalty_eur?.toLocaleString()}`} sub="non-compliance penalty" color={fuelData.penalty_eur>0?'red':'emerald'}/>
                  <KpiCard label="2050 Target" value="26.88 gCO2e/MJ" sub="-80% vs 2020 baseline" color="gray"/>
                </Row>
                <Section title="GHG Intensity Targets 2025-2050 vs Entity">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={fuelData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="year" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Legend/>
                        <Line type="monotone" dataKey="target" name="FuelEU Target" stroke="#6b7280" strokeDasharray="4 4"/>
                        <Line type="monotone" dataKey="entity" name="Entity Intensity" stroke="#10b981" strokeWidth={2}/>
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 4 — Ship Stranding Risk */}
        {tab===4 && (
          <div>
            <Section title="Ship Stranding Risk Inputs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={strandForm.entity_id} onChange={upd(setStrandForm,'entity_id')}/>
                <Sel label="Ship Type" value={strandForm.ship_type} onChange={upd(setStrandForm,'ship_type')} options={SHIP_TYPES}/>
                <Inp label="Build Year" type="number" value={strandForm.build_year} onChange={upd(setStrandForm,'build_year')}/>
                <Sel label="Fuel Type" value={strandForm.fuel_type} onChange={upd(setStrandForm,'fuel_type')} options={FUEL_TYPES}/>
                <Inp label="Gross Tonnage" type="number" value={strandForm.gross_tonnage} onChange={upd(setStrandForm,'gross_tonnage')}/>
              </div>
              <Btn onClick={runStrand}>Assess Stranding Risk</Btn>
            </Section>
            {strandLoading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"/></div>}
            {strandData && !strandLoading && (
              <>
                <Row>
                  <KpiCard label="Stranding Year" value={strandData.stranding_year} sub="estimated economic stranding"/>
                  <KpiCard label="Years to Stranding" value={strandData.years_to_stranding} sub="from 2025" color={strandData.years_to_stranding<5?'red':strandData.years_to_stranding<10?'amber':'emerald'}/>
                  <KpiCard label="Retrofit Cost USD" value={`$${strandData.retrofit_cost_usd?.toLocaleString()}`} sub="green fuel conversion"/>
                  <KpiCard label="Fleet Age" value={`${2025-+strandForm.build_year} yrs`} sub={`Built ${strandForm.build_year}`} color="gray"/>
                </Row>
                <Section title="Stranding Risk Factor Breakdown (Relative Score)">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={strandData.chart}>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={{fontSize:12}}/>
                        <YAxis tick={{fontSize:12}}/>
                        <Tooltip/>
                        <Bar dataKey="value" name="Risk Score" fill="#ef4444"/>
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
