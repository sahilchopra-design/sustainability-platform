/**
 * Sector-Specific ESG Assessments Page
 * Data Centers (PUE/WUE efficiency), Insurance CAT Risk, Power Plant Decarbonisation
 * Agriculture (EUDR/IPCC AR6), Mining (GISTM/IEA Critical Minerals)
 * Standards: EU Green Deal, IEA Net Zero, Lloyd's Realistic Disaster Scenarios, TCFD
 */
import React, { useState } from 'react';
import axios from 'axios';
import ShippingPanel from '../../sector-assessments/ShippingPanel';
import SteelPanel from '../../sector-assessments/SteelPanel';
import ProjectFinancePanel from '../../project-finance/ProjectFinancePanel';
import { BlendedFinancePanel } from '../../project-finance/BlendedFinancePanel';
import { GreenHydrogenPanel } from '../../sector-assessments/GreenHydrogenPanel';
import InsurancePanel from '../../sector-assessments/InsurancePanel';
import AgriculturePanel from '../../sector-assessments/AgriculturePanel';
import MiningPanel from '../../sector-assessments/MiningPanel';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar,
  LineChart, Line,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/* ── Helpers ────────────────────────────────────────────────────────────── */
function Badge({ label, color = 'bg-white/[0.06] text-white/60' }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}
function Card({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06]  ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-white/[0.04]">
          {title && <h2 className="text-sm font-semibold text-white/90">{title}</h2>}
          {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
function StatCard({ label, value, unit, sub, color = 'text-white' }) {
  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06]  p-5">
      <p className="text-xs text-white/40 font-medium mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {value}{unit && <span className="text-sm font-normal text-white/40 ml-1">{unit}</span>}
      </p>
      {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
    </div>
  );
}
function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-white/60 mb-1">{label}</label>
      {children}
      {hint && <p className="text-[10px] text-white/30 mt-0.5">{hint}</p>}
    </div>
  );
}
function Input({ value, onChange, type = 'text', ...rest }) {
  return (
    <input type={type} value={value} onChange={e => onChange(type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
      className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50" {...rest} />
  );
}

/* ── Data Centre Panel ───────────────────────────────────────────────────── */
const GRID_REGIONS = [
  { v: 'UK_NATIONAL', l: 'UK National Grid' },
  { v: 'EU_DE', l: 'Germany (ENTSO-E)' },
  { v: 'EU_FR', l: 'France (ENTSO-E)' },
  { v: 'EU_NL', l: 'Netherlands (ENTSO-E)' },
  { v: 'US_ERCOT', l: 'US ERCOT (Texas)' },
  { v: 'US_WECC', l: 'US WECC (Western)' },
  { v: 'US_SERC', l: 'US SERC (Southeast)' },
  { v: 'APAC_SG', l: 'Singapore' },
  { v: 'APAC_AU_NSW', l: 'Australia NSW' },
];
const COOLING_TYPES = [
  { v: 'air', l: 'Air Cooling' },
  { v: 'liquid', l: 'Direct Liquid Cooling' },
  { v: 'free_cooling', l: 'Free/Economiser Cooling' },
  { v: 'immersion', l: 'Immersion Cooling' },
  { v: 'hybrid', l: 'Hybrid (Air + Liquid)' },
];

function DataCentrePanel() {
  const [form, setForm] = useState({
    facility_id: '', location: '', grid_region: 'UK_NATIONAL', pue: 1.45, wue: null,
    total_it_load_mw: 5.0, annual_energy_consumption_mwh: 43800, renewable_energy_pct: 25,
    has_renewable_ppa: false, cooling_type: 'air',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));
  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try { const { data } = await axios.post(`${API}/api/v1/sector-assessments/data-centre`, form); setResult(data); }
    catch (err) { setError(err?.response?.data?.detail || err.message); }
    finally { setLoading(false); }
  };
  const radarData = result?.efficiency_benchmarks?.map(b => ({
    metric: b.metric.replace(/_/g, ' ').slice(0, 12), score: b.score_0_to_100, avg: 50,
  })) || [];
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="EU Green Deal" color="bg-emerald-500/10 text-emerald-400" />
        <Badge label="IEA Data Centre Efficiency" color="bg-blue-500/10 text-blue-300" />
        <Badge label="ISO/IEC 30134-2 (PUE)" color="bg-white/[0.06] text-white/60" />
        <Badge label="TCFD Physical Risk" color="bg-purple-500/10 text-purple-300" />
      </div>
      <Card title="Data Centre Parameters" subtitle="Facility parameters for ESG efficiency scoring and carbon intensity">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Field label="Facility ID"><Input value={form.facility_id} onChange={v => set('facility_id', v)} placeholder="DC_001" /></Field>
          <Field label="Location"><Input value={form.location} onChange={v => set('location', v)} placeholder="London, UK" /></Field>
          <Field label="Grid Region">
            <select className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.grid_region} onChange={e => set('grid_region', e.target.value)}>
              {GRID_REGIONS.map(g => <option key={g.v} value={g.v}>{g.l}</option>)}
            </select>
          </Field>
          <Field label="PUE" hint="Power Usage Effectiveness (1.0 = perfect; avg ~1.58)">
            <Input type="number" value={form.pue} onChange={v => set('pue', v)} step="0.01" min="1" max="5" />
          </Field>
          <Field label="WUE (L/kWh)" hint="Optional">
            <Input type="number" value={form.wue || ''} onChange={v => set('wue', v || null)} step="0.01" min="0" placeholder="Optional" />
          </Field>
          <Field label="Total IT Load (MW)">
            <Input type="number" value={form.total_it_load_mw} onChange={v => set('total_it_load_mw', v)} step="0.1" min="0" />
          </Field>
          <Field label="Annual Energy (MWh)">
            <Input type="number" value={form.annual_energy_consumption_mwh} onChange={v => set('annual_energy_consumption_mwh', v)} />
          </Field>
          <Field label="Renewable Energy (%)">
            <Input type="number" value={form.renewable_energy_pct} onChange={v => set('renewable_energy_pct', v)} min="0" max="100" />
          </Field>
          <Field label="Cooling Type">
            <select className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.cooling_type} onChange={e => set('cooling_type', e.target.value)}>
              {COOLING_TYPES.map(c => <option key={c.v} value={c.v}>{c.l}</option>)}
            </select>
          </Field>
          <div className="flex items-center gap-3 pt-6">
            <input type="checkbox" id="ppa" className="rounded" checked={form.has_renewable_ppa}
              onChange={e => set('has_renewable_ppa', e.target.checked)} />
            <label htmlFor="ppa" className="text-xs text-white/60 cursor-pointer">Renewable PPA in place</label>
          </div>
        </div>
        <div className="mt-6 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-8 py-2.5 rounded-lg transition-colors">
            {loading ? 'Assessing…' : 'Run Efficiency Assessment'}
          </button>
        </div>
      </Card>
      {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-400">{error}</div>}
      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Efficiency Score" value={`${result.overall_efficiency_score?.toFixed(0)}/100`}
              color={result.overall_efficiency_score > 70 ? 'text-emerald-400' : result.overall_efficiency_score > 40 ? 'text-amber-400' : 'text-red-400'} sub="ISO/IEC 30134" />
            <StatCard label="Carbon Intensity" value={result.carbon_intensity_kgco2_per_mwh_it?.toFixed(1)} unit="kgCO₂/MWh IT"
              color={result.carbon_intensity_kgco2_per_mwh_it < 50 ? 'text-emerald-400' : 'text-amber-400'} />
            <StatCard label="Annual CO₂e" value={(result.annual_co2e_tonnes / 1000).toFixed(0)} unit="ktCO₂e" />
            <StatCard label="Renewable Coverage" value={`${result.renewable_coverage_pct?.toFixed(0)}%`}
              color={result.renewable_coverage_pct > 50 ? 'text-emerald-400' : 'text-amber-400'} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Efficiency Benchmarks vs Industry">
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#f1f5f9" /><PolarAngleAxis dataKey="metric" tick={{ fontSize: 9 }} />
                  <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} name="Your Score" />
                  <Radar dataKey="avg" stroke="#94a3b8" fill="none" strokeDasharray="4 4" name="Industry Avg (50)" /><Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Improvement Targets">
              <div className="space-y-3">
                {result.improvement_targets?.map((t, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-white/[0.02] rounded-lg">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                      t.priority === 'HIGH' ? 'bg-red-100 text-red-400' : t.priority === 'MEDIUM' ? 'bg-amber-100 text-amber-400' : 'bg-emerald-100 text-emerald-400'
                    }`}>{i + 1}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-medium text-white/90">{t.measure}</span>
                        <Badge label={t.priority} color={t.priority === 'HIGH' ? 'bg-red-500/10 text-red-400' : t.priority === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'} />
                      </div>
                      <p className="text-[10px] text-white/40">Reduction: {t.potential_reduction_pct?.toFixed(0)}%{t.payback_years ? ` · Payback: ${t.payback_years?.toFixed(1)}yr` : ''}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── CAT Risk Panel ──────────────────────────────────────────────────────── */
const PERILS_CAT = [
  { v: 'flood', l: 'Flood' }, { v: 'windstorm', l: 'Windstorm' }, { v: 'earthquake', l: 'Earthquake' },
  { v: 'wildfire', l: 'Wildfire' }, { v: 'hail', l: 'Hail' }, { v: 'coastal_surge', l: 'Coastal Surge' }, { v: 'drought', l: 'Drought' },
];
const CLIMATE_SCENARIOS = ['RCP2.6','RCP4.5','RCP8.5','SSP1-2.6','SSP2-4.5','SSP5-8.5'];
const CONSTRUCTION_TYPES = [
  { v: 'masonry', l: 'Masonry' }, { v: 'timber', l: 'Timber Frame' }, { v: 'steel_frame', l: 'Steel Frame' },
  { v: 'reinforced_concrete', l: 'Reinforced Concrete' }, { v: 'prefab', l: 'Prefabricated' },
];

function CATRiskPanel() {
  const [form, setForm] = useState({
    property_id: '', latitude: 51.5, longitude: -0.12, country_iso: 'GB', peril: 'flood',
    property_value_gbp: 5000000, construction_type: 'reinforced_concrete', year_built: 1990,
    return_period_years: [50, 100, 200, 250], climate_scenario: 'RCP4.5',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));
  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try { const { data } = await axios.post(`${API}/api/v1/sector-assessments/cat-risk`, form); setResult(data); }
    catch (err) { setError(err?.response?.data?.detail || err.message); }
    finally { setLoading(false); }
  };
  const lossData = result?.return_period_losses?.map(r => ({
    period: `${r.return_period_years}yr`, loss_gbp: parseFloat((r.expected_loss_gbp / 1000).toFixed(0)),
  })) || [];
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="Lloyd's RDS" color="bg-blue-500/10 text-blue-300" />
        <Badge label="IPCC AR6 Physical Risk" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="TCFD Physical Scenarios" color="bg-purple-500/10 text-purple-300" />
        <Badge label="Solvency II / ICS 2.0" color="bg-amber-500/10 text-amber-400" />
      </div>
      <Card title="Property CAT Risk Parameters" subtitle="Catastrophe risk modelling for TCFD physical risk disclosure">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Field label="Property ID"><Input value={form.property_id} onChange={v => set('property_id', v)} placeholder="PROP_001" /></Field>
          <Field label="Latitude"><Input type="number" value={form.latitude} onChange={v => set('latitude', v)} step="0.0001" /></Field>
          <Field label="Longitude"><Input type="number" value={form.longitude} onChange={v => set('longitude', v)} step="0.0001" /></Field>
          <Field label="Country (ISO2)"><Input value={form.country_iso} onChange={v => set('country_iso', v)} /></Field>
          <Field label="Peril">
            <select className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.peril} onChange={e => set('peril', e.target.value)}>
              {PERILS_CAT.map(p => <option key={p.v} value={p.v}>{p.l}</option>)}
            </select>
          </Field>
          <Field label="Property Value (GBP)"><Input type="number" value={form.property_value_gbp} onChange={v => set('property_value_gbp', v)} /></Field>
          <Field label="Construction Type">
            <select className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.construction_type} onChange={e => set('construction_type', e.target.value)}>
              {CONSTRUCTION_TYPES.map(c => <option key={c.v} value={c.v}>{c.l}</option>)}
            </select>
          </Field>
          <Field label="Year Built"><Input type="number" value={form.year_built} onChange={v => set('year_built', v)} /></Field>
          <Field label="Climate Scenario">
            <select className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.climate_scenario} onChange={e => set('climate_scenario', e.target.value)}>
              {CLIMATE_SCENARIOS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
        </div>
        <div className="mt-6 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-8 py-2.5 rounded-lg transition-colors">
            {loading ? 'Modelling…' : 'Run CAT Risk Model'}
          </button>
        </div>
      </Card>
      {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-400">{error}</div>}
      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Risk Score" value={`${result.risk_score?.toFixed(0)}/100`}
              color={result.risk_score < 30 ? 'text-emerald-400' : result.risk_score < 60 ? 'text-amber-400' : 'text-red-400'} />
            <StatCard label="AAL" value={`£${(result.annual_average_loss_gbp / 1000).toFixed(0)}k`} sub="Annual Average Loss" />
            <StatCard label="1-in-100yr EML" value={`£${((result.return_period_losses?.find(r => r.return_period_years === 100)?.expected_loss_gbp || 0) / 1000).toFixed(0)}k`} />
            <StatCard label="Climate Delta" value={`+${result.climate_change_delta_pct?.toFixed(1)}%`} color="text-amber-400" />
          </div>
          <Card title="Return Period Loss Curve" subtitle="Expected Loss (£k)">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={lossData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="period" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => [`£${v}k`]} />
                <Bar dataKey="loss_gbp" name="Expected Loss (£k)" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ── Power Plant Panel ───────────────────────────────────────────────────── */
const FUEL_TYPES = [
  { v: 'coal', l: 'Coal' }, { v: 'gas_ccgt', l: 'Gas CCGT' }, { v: 'gas_ocgt', l: 'Gas OCGT' },
  { v: 'oil', l: 'Oil' }, { v: 'biomass', l: 'Biomass' }, { v: 'nuclear', l: 'Nuclear' },
  { v: 'wind_onshore', l: 'Wind Onshore' }, { v: 'wind_offshore', l: 'Wind Offshore' },
  { v: 'solar_pv', l: 'Solar PV' }, { v: 'hydro', l: 'Hydro' },
];

function PowerPlantPanel() {
  const [form, setForm] = useState({
    plant_id: '', country_iso: 'GB', fuel_type: 'coal', installed_capacity_mw: 500,
    annual_generation_mwh: 2500000, capacity_factor_pct: 57, year_commissioned: 1985,
    remaining_useful_life_years: 15, carbon_intensity_gco2_per_kwh: 820,
    net_book_value_gbp: 50000000, annual_revenue_gbp: 120000000,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));
  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try { const { data } = await axios.post(`${API}/api/v1/sector-assessments/power-plant-decarbonisation`, form); setResult(data); }
    catch (err) { setError(err?.response?.data?.detail || err.message); }
    finally { setLoading(false); }
  };
  const transitionData = result?.decarbonisation_pathways?.map(p => ({
    year: p.year, baselineCI: form.carbon_intensity_gco2_per_kwh,
    projectedCI: p.carbon_intensity_gco2_per_kwh, netZeroTarget: result.net_zero_target_ci_gco2_per_kwh,
  })) || [];
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="IEA NZE 2050" color="bg-emerald-500/10 text-emerald-400" />
        <Badge label="CRREM Power Sector" color="bg-blue-500/10 text-blue-300" />
        <Badge label="IPCC AR6 WG3" color="bg-purple-500/10 text-purple-300" />
      </div>
      <Card title="Power Plant Parameters" subtitle="Stranded asset risk, decarbonisation trajectory and early retirement economics">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Field label="Plant ID"><Input value={form.plant_id} onChange={v => set('plant_id', v)} placeholder="PLANT_001" /></Field>
          <Field label="Country (ISO2)"><Input value={form.country_iso} onChange={v => set('country_iso', v)} /></Field>
          <Field label="Fuel Type">
            <select className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.fuel_type} onChange={e => set('fuel_type', e.target.value)}>
              {FUEL_TYPES.map(f => <option key={f.v} value={f.v}>{f.l}</option>)}
            </select>
          </Field>
          <Field label="Installed Capacity (MW)"><Input type="number" value={form.installed_capacity_mw} onChange={v => set('installed_capacity_mw', v)} /></Field>
          <Field label="Annual Generation (MWh)"><Input type="number" value={form.annual_generation_mwh} onChange={v => set('annual_generation_mwh', v)} /></Field>
          <Field label="Carbon Intensity (gCO₂/kWh)"><Input type="number" value={form.carbon_intensity_gco2_per_kwh} onChange={v => set('carbon_intensity_gco2_per_kwh', v)} /></Field>
          <Field label="Year Commissioned"><Input type="number" value={form.year_commissioned} onChange={v => set('year_commissioned', v)} /></Field>
          <Field label="Remaining Life (yrs)"><Input type="number" value={form.remaining_useful_life_years} onChange={v => set('remaining_useful_life_years', v)} /></Field>
          <Field label="Net Book Value (GBP)"><Input type="number" value={form.net_book_value_gbp} onChange={v => set('net_book_value_gbp', v)} /></Field>
        </div>
        <div className="mt-6 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-8 py-2.5 rounded-lg transition-colors">
            {loading ? 'Analysing…' : 'Run Decarbonisation Analysis'}
          </button>
        </div>
      </Card>
      {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-400">{error}</div>}
      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Stranded Asset Risk" value={`${result.stranded_asset_risk_score?.toFixed(0)}/100`}
              color={result.stranded_asset_risk_score > 70 ? 'text-red-400' : result.stranded_asset_risk_score > 40 ? 'text-amber-400' : 'text-emerald-400'} />
            <StatCard label="Implied Stranding Year" value={result.implied_stranding_year || 'N/A'} color="text-amber-400" />
            <StatCard label="Stranded Value at Risk" value={`£${(result.stranded_value_at_risk_gbp / 1e6).toFixed(1)}M`} color="text-red-400" />
            <StatCard label="Carbon Cost" value={`£${(result.annual_carbon_cost_gbp / 1e6).toFixed(2)}M/yr`} />
          </div>
          {transitionData.length > 0 && (
            <Card title="Decarbonisation Trajectory" subtitle="gCO₂/kWh vs IEA NZE 2050 pathway">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={transitionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => [`${v} gCO₂/kWh`]} /><Legend />
                  <Line type="monotone" dataKey="baselineCI" stroke="#ef4444" strokeDasharray="5 3" dot={false} name="Baseline CI" />
                  <Line type="monotone" dataKey="projectedCI" stroke="#6366f1" strokeWidth={2} dot={false} name="Projected CI" />
                  <Line type="monotone" dataKey="netZeroTarget" stroke="#10b981" strokeDasharray="4 4" dot={false} name="NZE Target" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Coal Phase-Out Panel ────────────────────────────────────────────────── */
const COAL_CRITERIA = [
  { id: 'no_new_coal', label: 'No new coal mine / power plant approvals since 2021', standard: 'IEA NZE 2050' },
  { id: 'phase_out_timeline', label: 'Phase-out commitment: 2030 (OECD) or 2040 (non-OECD)', standard: 'IPCC AR6 / IEA' },
  { id: 'transition_plan', label: 'Credible transition plan with verified milestones published', standard: 'NZBA / GFANZ' },
  { id: 'just_transition', label: 'Just Transition fund / worker support measures established', standard: 'ILO / OECD' },
  { id: 'revenue_declining', label: 'Thermal coal revenue < 25% of total and declining year-on-year', standard: 'PCAF / SBTi' },
];
function CoalPhaseOutPanel() {
  const [checks, setChecks] = useState(() => Object.fromEntries(COAL_CRITERIA.map(c => [c.id, false])));
  const metCount = Object.values(checks).filter(Boolean).length;
  const total = COAL_CRITERIA.length;
  const rag = metCount === total ? 'GREEN' : metCount >= 3 ? 'AMBER' : 'RED';
  const ragConfig = {
    GREEN: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', label: 'Criteria Met — Coal Phase-Out Aligned' },
    AMBER: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', label: 'Partially Met — Gaps in Phase-Out Commitment' },
    RED: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400', label: 'Below Threshold — Significant Phase-Out Gaps' },
  }[rag];
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="IEA NZE 2050" color="bg-emerald-500/10 text-emerald-400" />
        <Badge label="IPCC AR6 WG3" color="bg-blue-500/10 text-blue-300" />
        <Badge label="NZBA Coal Criteria" color="bg-white/[0.06] text-white/60" />
        <Badge label="GFANZ Phase-Down" color="bg-purple-500/10 text-purple-300" />
      </div>
      <Card title="Coal Phase-Out Criteria Assessment" subtitle="IEA NZE 2050 / IPCC AR6 / NZBA aligned coal phase-down checklist">
        <div className="space-y-3">
          {COAL_CRITERIA.map(c => (
            <div key={c.id} className="flex items-start gap-4 p-4 bg-white/[0.02] rounded-lg hover:bg-white/[0.03] transition-colors">
              <input type="checkbox" id={c.id} checked={checks[c.id]}
                onChange={e => setChecks(prev => ({ ...prev, [c.id]: e.target.checked }))}
                className="mt-0.5 rounded border-white/20 bg-white/[0.04] text-cyan-400 focus:ring-cyan-400/50" />
              <div className="flex-1">
                <label htmlFor={c.id} className="text-sm font-medium text-white/80 cursor-pointer">{c.label}</label>
                <p className="text-[11px] text-white/30 mt-0.5">Standard: {c.standard}</p>
              </div>
              <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${checks[c.id] ? 'bg-emerald-400' : 'bg-white/10'}`} />
            </div>
          ))}
        </div>
      </Card>
      <div className={`rounded-xl border p-5 ${ragConfig.bg} ${ragConfig.border}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-white/40 mb-1">Assessment Result</p>
            <p className={`text-xl font-bold ${ragConfig.text}`}>{ragConfig.label}</p>
            <p className="text-xs text-white/40 mt-1">{metCount} of {total} criteria satisfied</p>
          </div>
          <div className={`text-4xl font-black ${ragConfig.text}`}>{rag}</div>
        </div>
        <div className="mt-3 h-2 bg-white/[0.04] rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-500 ${rag === 'GREEN' ? 'bg-emerald-400' : rag === 'AMBER' ? 'bg-amber-400' : 'bg-red-400'}`}
            style={{ width: `${(metCount / total) * 100}%` }} />
        </div>
      </div>
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────────────────────── */
const PANELS = [
  { id: 'datacentre',    label: 'Data Centre ESG',             sub: 'PUE / WUE / Carbon Intensity' },
  { id: 'catrisk',       label: 'CAT Risk (Property)',          sub: 'Physical Hazard Modelling' },
  { id: 'powerplant',    label: 'Power Plant',                  sub: 'Stranded Asset & Transition' },
  { id: 'coalcheck',     label: 'Coal Phase-Out',               sub: 'IEA NZE / IPCC / NZBA' },
  { id: 'shipping',      label: 'Shipping (IMO CII)',           sub: 'CII / EEXI / AER Rating' },
  { id: 'steel',         label: 'Steel Transition',             sub: 'BF-BOF / EAF Glidepath' },
  { id: 'projectfinance',label: 'Project Finance',              sub: 'DSCR / LLCR / IRR' },
  { id: 'blendedfinance',label: 'Blended Finance',              sub: 'OECD MDB Cascade' },
  { id: 'greenhydrogen', label: 'Green Hydrogen',               sub: 'IRENA / IEA / RFNBO' },
  { id: 'insurance',     label: 'Insurance Climate',            sub: 'Solvency II / CAT / TP' },
  { id: 'agriculture',   label: 'Agriculture Risk',             sub: 'EUDR / IPCC AR6 / Soil' },
  { id: 'mining',        label: 'Mining & Extractives',         sub: 'GISTM / Critical Minerals' },
];

export default function SectorAssessmentsPage() {
  const [activePanel, setActivePanel] = useState('datacentre');

  return (
    <div className="flex flex-col h-full bg-white/[0.02]">
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-8 py-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Sector ESG Assessments</h1>
            <p className="text-sm text-white/40 mt-0.5">
              Technology / Data Centre, Insurance, Energy, Agriculture, Mining &amp; Extractives
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge label="Technology" color="bg-blue-500/10 text-blue-300" />
            <Badge label="Insurance / CAT" color="bg-purple-500/10 text-purple-300" />
            <Badge label="Energy / Power" color="bg-amber-500/10 text-amber-400" />
            <Badge label="Agriculture / EUDR" color="bg-emerald-500/10 text-emerald-400" />
            <Badge label="Mining / Extractives" color="bg-red-500/10 text-red-300" />
          </div>
        </div>
      </div>

      <div className="bg-[#0d1424] border-b border-white/[0.06] px-8 overflow-x-auto">
        <div className="flex gap-0 min-w-max">
          {PANELS.map(p => (
            <button key={p.id} onClick={() => setActivePanel(p.id)}
              className={`px-4 py-3.5 border-b-2 transition-all whitespace-nowrap ${
                activePanel === p.id
                  ? 'border-cyan-400/20 text-cyan-300'
                  : 'border-transparent text-white/40 hover:text-white/70 hover:border-white/[0.08]'
              }`}>
              <span className="text-sm font-semibold block">{p.label}</span>
              <span className="text-[10px] text-white/30">{p.sub}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        {activePanel === 'datacentre'     && <DataCentrePanel />}
        {activePanel === 'catrisk'        && <CATRiskPanel />}
        {activePanel === 'powerplant'     && <PowerPlantPanel />}
        {activePanel === 'coalcheck'      && <CoalPhaseOutPanel />}
        {activePanel === 'shipping'       && <ShippingPanel />}
        {activePanel === 'steel'          && <SteelPanel />}
        {activePanel === 'projectfinance' && <ProjectFinancePanel />}
        {activePanel === 'blendedfinance' && <BlendedFinancePanel />}
        {activePanel === 'greenhydrogen'  && <GreenHydrogenPanel />}
        {activePanel === 'insurance'      && <InsurancePanel />}
        {activePanel === 'agriculture'    && <AgriculturePanel />}
        {activePanel === 'mining'         && <MiningPanel />}
      </div>
    </div>
  );
}
