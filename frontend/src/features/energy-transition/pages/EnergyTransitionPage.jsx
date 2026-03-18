import React, { useState, useEffect } from 'react';
import { usePersonaDefaults } from '../../../context/PersonaContext';
import axios from 'axios';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell
} from 'recharts';
import {
  Factory, TrendingDown, Globe, Flame, Truck,
  ChevronRight, AlertTriangle, Trash2, Plus, Zap
} from 'lucide-react';

const API = process.env.REACT_APP_API_URL || "http://localhost:8001";

const fmt2 = v => Number(v || 0).toFixed(2);
const fmt0 = v => Math.round(v || 0).toLocaleString();
const fmtPct = v => (v || 0).toFixed(1) + '%';

const COLORS = {
  primary: '#164E8A',
  accent: '#059669',
  border: '#E5E7EB',
  bg: '#F9FAFB',
  blue: '#3B82F6',
  amber: '#F59E0B',
  red: '#EF4444',
  purple: '#8B5CF6',
  teal: '#14B8A6',
  coal: '#4B5563',
  gas: '#F59E0B',
  wind: '#3B82F6',
  solar: '#EAB308',
  nuclear: '#8B5CF6',
  hydro: '#06B6D4',
};

const SCENARIOS = [
  { value: 'net_zero_2050', label: 'Net Zero 2050' },
  { value: 'below_2c', label: 'Below 2C' },
  { value: 'delayed_transition', label: 'Delayed Transition' },
  { value: 'current_policies', label: 'Current Policies' },
];

const COUNTRIES = ['DE', 'GB', 'FR', 'US', 'CN', 'IN', 'JP', 'AU', 'BR', 'ZA', 'ES', 'IT', 'PL', 'KR', 'CA'];

const tabs = [
  { label: 'Fleet Transition', icon: Factory },
  { label: 'Grid EF Tracker', icon: Globe },
  { label: 'Avoided Emissions', icon: TrendingDown },
  { label: 'Methane OGMP', icon: Flame },
  { label: 'Scope 3 Cat 11', icon: Truck },
];

function KpiCard({ label, value, sub, color }) {
  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm" style={{ borderColor: '#E5E7EB' }}>
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-bold" style={{ color: color || COLORS.primary }}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm mb-4" style={{ borderColor: '#E5E7EB' }}>
      {title && <h3 className="text-lg font-semibold mb-4" style={{ color: COLORS.primary }}>{title}</h3>}
      {children}
    </div>
  );
}

function Inp({ label, value, onChange, type = 'number', step, min, max, className = '' }) {
  return (
    <div className={`flex flex-col ${className}`}>
      <label className="text-xs text-gray-500 mb-1">{label}</label>
      <input type={type} value={value}
        onChange={e => onChange(type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
        step={step} min={min} max={max}
        className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
        style={{ borderColor: COLORS.border }} />
    </div>
  );
}

function Sel({ label, value, onChange, options, className = '' }) {
  return (
    <div className={`flex flex-col ${className}`}>
      <label className="text-xs text-gray-500 mb-1">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
        style={{ borderColor: COLORS.border }}>
        {options.map(o => {
          const val = typeof o === 'object' ? o.value : o;
          const lbl = typeof o === 'object' ? o.label : o;
          return <option key={val} value={val}>{lbl}</option>;
        })}
      </select>
    </div>
  );
}

function Btn({ onClick, children, disabled, variant = 'primary' }) {
  const bg = variant === 'primary' ? COLORS.primary : COLORS.accent;
  return (
    <button onClick={onClick} disabled={disabled}
      className="px-5 py-2 rounded-lg text-white font-medium text-sm transition-opacity hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
      style={{ backgroundColor: bg }}>
      {children}
    </button>
  );
}

/* ======== TAB 1: FLEET TRANSITION ======== */
const DEFAULT_PLANTS = [
  { id: 1, name: 'Riverside Coal', technology: 'coal', capacity_mw: 500, age_years: 35, annual_emissions_tco2: 1500000, replacement_tech: 'offshore_wind' },
  { id: 2, name: 'Midlands CCGT', technology: 'gas_ccgt', capacity_mw: 400, age_years: 15, annual_emissions_tco2: 450000, replacement_tech: 'solar_pv' },
  { id: 3, name: 'North Wind Farm', technology: 'wind', capacity_mw: 200, age_years: 5, annual_emissions_tco2: 0, replacement_tech: 'wind' },
];

function FleetTransition() {
  const d = usePersonaDefaults('energy_transition');
  const [plants, setPlants] = useState(() => (d.plants && d.plants.length ? d.plants : DEFAULT_PLANTS));
  const [targetYear, setTargetYear] = useState(() => d.targetYear || 2040);
  useEffect(() => {
    if (d.plants && d.plants.length) setPlants(d.plants);
    if (d.targetYear) setTargetYear(d.targetYear);
  }, [d.plants]); // eslint-disable-line
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updatePlant = (id, field, value) => {
    setPlants(ps => ps.map(p => p.id === id ? { ...p, [field]: value } : p));
  };

  const addPlant = () => {
    const id = Math.max(0, ...plants.map(p => p.id)) + 1;
    setPlants([...plants, { id, name: `Plant ${id}`, technology: 'gas_ccgt', capacity_mw: 200, age_years: 10, annual_emissions_tco2: 300000, replacement_tech: 'solar_pv' }]);
  };

  const removePlant = (id) => {
    if (plants.length > 1) setPlants(ps => ps.filter(p => p.id !== id));
  };

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/energy-transition/fleet-transition`, { plants, target_year: targetYear });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  const techOptions = ['coal', 'gas_ccgt', 'gas_ocgt', 'oil', 'wind', 'solar_pv', 'nuclear', 'hydro', 'biomass', 'battery'];
  const replacementOptions = ['offshore_wind', 'onshore_wind', 'solar_pv', 'solar_csp', 'nuclear', 'battery_storage', 'green_hydrogen', 'biomass'];

  return (
    <div className="space-y-4">
      <Section title="Generation Fleet">
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b" style={{ borderColor: COLORS.border }}>
                <th className="pb-2">Name</th>
                <th className="pb-2">Technology</th>
                <th className="pb-2">Capacity (MW)</th>
                <th className="pb-2">Age (yrs)</th>
                <th className="pb-2">Emissions (tCO2/yr)</th>
                <th className="pb-2">Replacement</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {plants.map(p => (
                <tr key={p.id} className="border-b" style={{ borderColor: COLORS.border }}>
                  <td className="py-2"><input type="text" value={p.name} onChange={e => updatePlant(p.id, 'name', e.target.value)} className="border rounded px-2 py-1 text-sm w-full" style={{ borderColor: COLORS.border }} /></td>
                  <td className="py-2"><select value={p.technology} onChange={e => updatePlant(p.id, 'technology', e.target.value)} className="border rounded px-2 py-1 text-sm" style={{ borderColor: COLORS.border }}>{techOptions.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}</select></td>
                  <td className="py-2"><input type="number" value={p.capacity_mw} onChange={e => updatePlant(p.id, 'capacity_mw', parseFloat(e.target.value) || 0)} className="border rounded px-2 py-1 text-sm w-24" style={{ borderColor: COLORS.border }} /></td>
                  <td className="py-2"><input type="number" value={p.age_years} onChange={e => updatePlant(p.id, 'age_years', parseFloat(e.target.value) || 0)} className="border rounded px-2 py-1 text-sm w-20" style={{ borderColor: COLORS.border }} /></td>
                  <td className="py-2"><input type="number" value={p.annual_emissions_tco2} onChange={e => updatePlant(p.id, 'annual_emissions_tco2', parseFloat(e.target.value) || 0)} className="border rounded px-2 py-1 text-sm w-32" style={{ borderColor: COLORS.border }} /></td>
                  <td className="py-2"><select value={p.replacement_tech} onChange={e => updatePlant(p.id, 'replacement_tech', e.target.value)} className="border rounded px-2 py-1 text-sm" style={{ borderColor: COLORS.border }}>{replacementOptions.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}</select></td>
                  <td className="py-2"><button onClick={() => removePlant(p.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center gap-4 mb-4">
          <button onClick={addPlant} className="flex items-center gap-1 text-sm text-blue-600 hover:underline"><Plus size={14} /> Add Plant</button>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-500">Target Year:</label>
            <input type="range" min={2030} max={2050} value={targetYear} onChange={e => setTargetYear(parseInt(e.target.value))} className="w-40" />
            <span className="text-sm font-medium">{targetYear}</span>
          </div>
        </div>
        <Btn onClick={run} disabled={loading}><Factory size={16} /> Run Fleet Transition</Btn>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Current Emissions" value={`${fmt0(result.current_emissions_tco2)} tCO2`} sub="Annual total" color={COLORS.red} />
            <KpiCard label="Target Emissions" value={`${fmt0(result.target_emissions_tco2)} tCO2`} sub={`By ${targetYear}`} color={COLORS.accent} />
            <KpiCard label="Reduction" value={fmtPct(result.reduction_pct)} sub="From baseline" color={COLORS.primary} />
            <KpiCard label="Stranded Value" value={`EUR ${fmt0(result.stranded_value_eur)}`} sub="Premature retirement" color={COLORS.amber} />
          </div>

          {result.emissions_trajectory && (
            <Section title="Emissions Trajectory">
              <ResponsiveContainer width="100%" height={340}>
                <AreaChart data={result.emissions_trajectory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={v => fmt0(v) + ' tCO2'} />
                  <Legend />
                  <Area type="monotone" dataKey="coal" name="Coal" stackId="1" fill={COLORS.coal} stroke={COLORS.coal} />
                  <Area type="monotone" dataKey="gas" name="Gas" stackId="1" fill={COLORS.gas} stroke={COLORS.gas} />
                  <Area type="monotone" dataKey="oil" name="Oil" stackId="1" fill={COLORS.red} stroke={COLORS.red} />
                  <Area type="monotone" dataKey="renewable" name="Renewable" stackId="1" fill={COLORS.accent} stroke={COLORS.accent} />
                </AreaChart>
              </ResponsiveContainer>
            </Section>
          )}

          {result.retirement_timeline && (
            <Section title="Retirement Timeline">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b" style={{ borderColor: COLORS.border }}>
                      <th className="pb-2">Plant</th>
                      <th className="pb-2">Retirement Year</th>
                      <th className="pb-2">Replacement</th>
                      <th className="pb-2">Stranded Cost (EUR)</th>
                      <th className="pb-2">CO2 Saved (t/yr)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.retirement_timeline.map((r, i) => (
                      <tr key={i} className="border-b" style={{ borderColor: COLORS.border }}>
                        <td className="py-2 font-medium">{r.plant_name}</td>
                        <td className="py-2">{r.retirement_year}</td>
                        <td className="py-2">{(r.replacement || '').replace(/_/g, ' ')}</td>
                        <td className="py-2 text-red-600">{fmt0(r.stranded_cost_eur)}</td>
                        <td className="py-2 text-green-600">{fmt0(r.co2_saved_tpa)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ======== TAB 2: GRID EF TRACKER ======== */
function GridEFTracker() {
  const d = usePersonaDefaults('energy_transition');
  const [country, setCountry] = useState(() => d.country || 'DE');
  const [scenario, setScenario] = useState(() => d.scenario || 'net_zero_2050');
  useEffect(() => {
    if (d.country) setCountry(d.country);
    if (d.scenario) setScenario(d.scenario);
  }, [d.country]); // eslint-disable-line
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/energy-transition/grid-ef-projection`, { country, scenario });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  const [allScenarios, setAllScenarios] = useState(null);

  const runAll = async () => {
    setLoading(true);
    setError('');
    try {
      const results = {};
      for (const s of SCENARIOS) {
        const res = await axios.post(`${API}/api/v1/energy-transition/grid-ef-projection`, { country, scenario: s.value });
        results[s.value] = res.data;
      }
      setAllScenarios(results);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const multiLineData = allScenarios ? (() => {
    const years = allScenarios[SCENARIOS[0].value]?.projection?.map(p => p.year) || [];
    return years.map(y => {
      const row = { year: y };
      SCENARIOS.forEach(s => {
        const point = (allScenarios[s.value]?.projection || []).find(p => p.year === y);
        row[s.value] = point?.ef_kg_mwh || 0;
      });
      return row;
    });
  })() : null;

  return (
    <div className="space-y-4">
      <Section title="Grid Emission Factor Projection">
        <div className="flex items-end gap-4 mb-4">
          <Sel label="Country" value={country} onChange={setCountry} options={COUNTRIES} />
          <Sel label="Scenario" value={scenario} onChange={setScenario} options={SCENARIOS} />
          <Btn onClick={run} disabled={loading}><Globe size={16} /> Project</Btn>
          <Btn onClick={runAll} disabled={loading} variant="accent"><Globe size={16} /> All Scenarios</Btn>
        </div>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && !allScenarios && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Current EF (2023)" value={`${fmt0(result.current_ef_kg_mwh)} kg/MWh`} sub={country} color={COLORS.primary} />
            <KpiCard label="2030 EF" value={`${fmt0(result.ef_2030_kg_mwh)} kg/MWh`} sub={scenario.replace(/_/g, ' ')} color={COLORS.blue} />
            <KpiCard label="2050 EF" value={`${fmt0(result.ef_2050_kg_mwh)} kg/MWh`} sub={scenario.replace(/_/g, ' ')} color={COLORS.accent} />
            <KpiCard label="Reduction" value={fmtPct(result.reduction_pct)} sub="2023 to 2050" color={COLORS.teal} />
          </div>

          {result.projection && (
            <Section title={`Grid EF Projection — ${country} (${scenario.replace(/_/g, ' ')})`}>
              <ResponsiveContainer width="100%" height={340}>
                <LineChart data={result.projection}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis label={{ value: 'kg CO2/MWh', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={v => fmt2(v) + ' kg/MWh'} />
                  <Line type="monotone" dataKey="ef_kg_mwh" name="Grid EF" stroke={COLORS.primary} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          )}
        </>
      )}

      {multiLineData && (
        <Section title={`Multi-Scenario Grid EF — ${country}`}>
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={multiLineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis label={{ value: 'kg CO2/MWh', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={v => fmt2(v) + ' kg/MWh'} />
              <Legend />
              <Line type="monotone" dataKey="net_zero_2050" name="Net Zero 2050" stroke={COLORS.accent} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="below_2c" name="Below 2C" stroke={COLORS.blue} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="delayed_transition" name="Delayed Transition" stroke={COLORS.amber} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="current_policies" name="Current Policies" stroke={COLORS.red} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      )}
    </div>
  );
}

/* ======== TAB 3: AVOIDED EMISSIONS ======== */
function AvoidedEmissions() {
  const [form, setForm] = useState({
    country: 'DE',
    annual_generation_mwh: 1500000,
    project_lifetime_years: 25,
    technology: 'offshore_wind',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/energy-transition/avoided-emissions`, form);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  return (
    <div className="space-y-4">
      <Section title="Avoided Emissions Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Country" value={form.country} onChange={v => setForm({ ...form, country: v })} options={COUNTRIES} />
          <Inp label="Annual Generation (MWh)" value={form.annual_generation_mwh} onChange={v => setForm({ ...form, annual_generation_mwh: v })} />
          <Inp label="Lifetime (years)" value={form.project_lifetime_years} onChange={v => setForm({ ...form, project_lifetime_years: v })} />
          <Sel label="Technology" value={form.technology} onChange={v => setForm({ ...form, technology: v })}
            options={['offshore_wind', 'onshore_wind', 'solar_pv', 'solar_csp', 'nuclear', 'hydro']} />
        </div>
        <Btn onClick={run} disabled={loading}><TrendingDown size={16} /> Calculate Avoided Emissions</Btn>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Year 1 Avoided" value={`${fmt0(result.year1_avoided_tco2)} tCO2`} sub="First year" color={COLORS.accent} />
            <KpiCard label="Lifetime Avoided" value={`${fmt0(result.lifetime_avoided_tco2)} tCO2`} sub={`${form.project_lifetime_years} years`} color={COLORS.primary} />
            <KpiCard label="Grid EF Used" value={`${fmt2(result.grid_ef_kg_mwh)} kg/MWh`} sub={form.country} color={COLORS.blue} />
            <KpiCard label="Carbon Value" value={`EUR ${fmt0(result.lifetime_carbon_value_eur)}`} sub="At current prices" color={COLORS.amber} />
          </div>

          {result.annual_avoided && (
            <Section title="Annual Avoided Emissions Trajectory">
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={result.annual_avoided}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={v => fmt0(v) + ' tCO2'} />
                  <Area type="monotone" dataKey="avoided_tco2" name="Avoided Emissions" fill={COLORS.accent} stroke={COLORS.accent} fillOpacity={0.3} />
                  <Area type="monotone" dataKey="cumulative_tco2" name="Cumulative" fill={COLORS.primary} stroke={COLORS.primary} fillOpacity={0.1} />
                </AreaChart>
              </ResponsiveContainer>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ======== TAB 4: METHANE OGMP ======== */
function MethaneOGMP() {
  const [form, setForm] = useState({
    facility_name: 'North Sea Platform Alpha',
    operator: 'EnerCo',
    production_bcm: 2.5,
    ogmp_level: 4,
  });
  const [sources, setSources] = useState([
    { id: 1, source: 'Fugitives', ch4_tonnes: 500 },
    { id: 2, source: 'Venting', ch4_tonnes: 200 },
    { id: 3, source: 'Flaring (incomplete)', ch4_tonnes: 100 },
  ]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateSource = (id, field, value) => {
    setSources(ss => ss.map(s => s.id === id ? { ...s, [field]: value } : s));
  };

  const addSource = () => {
    const id = Math.max(0, ...sources.map(s => s.id)) + 1;
    setSources([...sources, { id, source: 'Other', ch4_tonnes: 50 }]);
  };

  const removeSource = (id) => {
    if (sources.length > 1) setSources(ss => ss.filter(s => s.id !== id));
  };

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/energy-emissions/methane-facility`, { ...form, sources });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  const pieColors = [COLORS.red, COLORS.amber, COLORS.purple, COLORS.blue, COLORS.teal, COLORS.coal];
  const pieData = sources.map(s => ({ name: s.source, value: s.ch4_tonnes }));

  return (
    <div className="space-y-4">
      <Section title="Methane Facility — OGMP 2.0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Facility Name" value={form.facility_name} onChange={v => setForm({ ...form, facility_name: v })} type="text" />
          <Inp label="Operator" value={form.operator} onChange={v => setForm({ ...form, operator: v })} type="text" />
          <Inp label="Production (bcm)" value={form.production_bcm} onChange={v => setForm({ ...form, production_bcm: v })} step={0.1} />
          <Sel label="OGMP Level" value={form.ogmp_level} onChange={v => setForm({ ...form, ogmp_level: parseInt(v) })} options={[1, 2, 3, 4, 5]} />
        </div>
        <h4 className="text-sm font-medium text-gray-600 mb-2">Emission Sources</h4>
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b" style={{ borderColor: COLORS.border }}>
                <th className="pb-2">Source</th>
                <th className="pb-2">CH4 (tonnes/yr)</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {sources.map(s => (
                <tr key={s.id} className="border-b" style={{ borderColor: COLORS.border }}>
                  <td className="py-2"><input type="text" value={s.source} onChange={e => updateSource(s.id, 'source', e.target.value)} className="border rounded px-2 py-1 text-sm w-full" style={{ borderColor: COLORS.border }} /></td>
                  <td className="py-2"><input type="number" value={s.ch4_tonnes} onChange={e => updateSource(s.id, 'ch4_tonnes', parseFloat(e.target.value) || 0)} className="border rounded px-2 py-1 text-sm w-32" style={{ borderColor: COLORS.border }} /></td>
                  <td className="py-2"><button onClick={() => removeSource(s.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex gap-4">
          <button onClick={addSource} className="flex items-center gap-1 text-sm text-blue-600 hover:underline"><Plus size={14} /> Add Source</button>
          <Btn onClick={run} disabled={loading}><Flame size={16} /> Assess Methane</Btn>
        </div>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Total CH4" value={`${fmt0(result.total_ch4_tonnes)} t`} sub="Annual" color={COLORS.red} />
            <KpiCard label="CO2-eq (GWP-100)" value={`${fmt0(result.co2eq_gwp100)} tCO2e`} sub="GWP=28" color={COLORS.amber} />
            <KpiCard label="CO2-eq (GWP-20)" value={`${fmt0(result.co2eq_gwp20)} tCO2e`} sub="GWP=84" color={COLORS.purple} />
            <KpiCard label="Intensity" value={`${fmt2(result.intensity_tch4_per_bcm)} tCH4/bcm`} sub="Methane intensity" color={COLORS.primary} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Section title="Emission Sources">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} dataKey="value">
                    {pieData.map((_, i) => <Cell key={i} fill={pieColors[i % pieColors.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => fmt0(v) + ' tCH4'} />
                </PieChart>
              </ResponsiveContainer>
            </Section>

            <Section title="GWP Comparison">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={[
                  { metric: 'GWP-20 (84)', value: result.co2eq_gwp20 || 0 },
                  { metric: 'GWP-100 (28)', value: result.co2eq_gwp100 || 0 },
                  { metric: 'GWP* (cumulative)', value: result.co2eq_gwp_star || 0 },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={v => fmt0(v) + ' tCO2e'} />
                  <Bar dataKey="value" name="CO2-eq" radius={[4, 4, 0, 0]}>
                    <Cell fill={COLORS.purple} />
                    <Cell fill={COLORS.amber} />
                    <Cell fill={COLORS.primary} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </div>

          {result.abatement_options && (
            <Section title="Abatement Opportunities">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b" style={{ borderColor: COLORS.border }}>
                      <th className="pb-2">Measure</th>
                      <th className="pb-2">Reduction (tCH4)</th>
                      <th className="pb-2">Cost (EUR/t)</th>
                      <th className="pb-2">Payback (yrs)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.abatement_options.map((a, i) => (
                      <tr key={i} className="border-b" style={{ borderColor: COLORS.border }}>
                        <td className="py-2 font-medium">{a.measure}</td>
                        <td className="py-2 text-green-600">{fmt0(a.reduction_tch4)}</td>
                        <td className="py-2">{fmt0(a.cost_eur_per_tonne)}</td>
                        <td className="py-2">{fmt2(a.payback_years)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ======== TAB 5: SCOPE 3 CAT 11 ======== */
function Scope3Cat11() {
  const [fuels, setFuels] = useState([
    { id: 1, fuel: 'natural_gas', volume: 500000, unit: 'm3' },
    { id: 2, fuel: 'crude_oil', volume: 100000, unit: 'barrels' },
  ]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateFuel = (id, field, value) => {
    setFuels(fs => fs.map(f => f.id === id ? { ...f, [field]: value } : f));
  };

  const addFuel = () => {
    const id = Math.max(0, ...fuels.map(f => f.id)) + 1;
    setFuels([...fuels, { id, fuel: 'coal', volume: 10000, unit: 'tonnes' }]);
  };

  const removeFuel = (id) => {
    if (fuels.length > 1) setFuels(fs => fs.filter(f => f.id !== id));
  };

  const fuelOptions = ['natural_gas', 'crude_oil', 'coal', 'lng', 'diesel', 'gasoline', 'jet_fuel', 'lpg', 'heavy_fuel_oil', 'naphtha', 'bitumen'];
  const unitOptions = ['m3', 'barrels', 'tonnes', 'mmbtu', 'kwh', 'litres', 'gallons'];

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/energy-emissions/scope3-cat11`, { fuels });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  const waterfallData = result?.fuel_breakdown ? result.fuel_breakdown.map(f => ({
    name: f.fuel.replace(/_/g, ' '),
    tco2: f.emissions_tco2,
  })) : [];

  return (
    <div className="space-y-4">
      <Section title="Scope 3 Category 11 — Use of Sold Products">
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b" style={{ borderColor: COLORS.border }}>
                <th className="pb-2">Fuel</th>
                <th className="pb-2">Volume</th>
                <th className="pb-2">Unit</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {fuels.map(f => (
                <tr key={f.id} className="border-b" style={{ borderColor: COLORS.border }}>
                  <td className="py-2"><select value={f.fuel} onChange={e => updateFuel(f.id, 'fuel', e.target.value)} className="border rounded px-2 py-1 text-sm" style={{ borderColor: COLORS.border }}>{fuelOptions.map(o => <option key={o} value={o}>{o.replace(/_/g, ' ')}</option>)}</select></td>
                  <td className="py-2"><input type="number" value={f.volume} onChange={e => updateFuel(f.id, 'volume', parseFloat(e.target.value) || 0)} className="border rounded px-2 py-1 text-sm w-32" style={{ borderColor: COLORS.border }} /></td>
                  <td className="py-2"><select value={f.unit} onChange={e => updateFuel(f.id, 'unit', e.target.value)} className="border rounded px-2 py-1 text-sm" style={{ borderColor: COLORS.border }}>{unitOptions.map(o => <option key={o} value={o}>{o}</option>)}</select></td>
                  <td className="py-2"><button onClick={() => removeFuel(f.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex gap-4">
          <button onClick={addFuel} className="flex items-center gap-1 text-sm text-blue-600 hover:underline"><Plus size={14} /> Add Fuel</button>
          <Btn onClick={run} disabled={loading}><Truck size={16} /> Calculate Cat 11</Btn>
        </div>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Total Scope 3 Cat 11" value={`${fmt0(result.total_emissions_tco2)} tCO2`} sub="Use of sold products" color={COLORS.red} />
            <KpiCard label="Fuel Count" value={result.fuel_count || fuels.length} sub="Product lines" color={COLORS.primary} />
            <KpiCard label="Intensity" value={`${fmt2(result.intensity_tco2_per_tj)} tCO2/TJ`} sub="Weighted average" color={COLORS.amber} />
            <KpiCard label="Revenue Intensity" value={`${fmt2(result.revenue_intensity_tco2_per_meur)} tCO2/MEUR`} sub="If revenue provided" color={COLORS.blue} />
          </div>

          {waterfallData.length > 0 && (
            <Section title="Emissions by Fuel — Waterfall">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={waterfallData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={v => fmt0(v) + ' tCO2'} />
                  <Bar dataKey="tco2" name="Emissions" radius={[4, 4, 0, 0]}>
                    {waterfallData.map((_, i) => (
                      <Cell key={i} fill={[COLORS.coal, COLORS.amber, COLORS.red, COLORS.purple, COLORS.blue, COLORS.teal][i % 6]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          {result.fuel_breakdown && (
            <Section title="Detailed Fuel Breakdown">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b" style={{ borderColor: COLORS.border }}>
                      <th className="pb-2">Fuel</th>
                      <th className="pb-2">Volume</th>
                      <th className="pb-2">EF (kgCO2/unit)</th>
                      <th className="pb-2">Emissions (tCO2)</th>
                      <th className="pb-2">Share (%)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.fuel_breakdown.map((f, i) => (
                      <tr key={i} className="border-b" style={{ borderColor: COLORS.border }}>
                        <td className="py-2 font-medium">{(f.fuel || '').replace(/_/g, ' ')}</td>
                        <td className="py-2">{fmt0(f.volume)} {f.unit}</td>
                        <td className="py-2">{fmt2(f.emission_factor)}</td>
                        <td className="py-2 font-medium">{fmt0(f.emissions_tco2)}</td>
                        <td className="py-2">{fmtPct(f.share_pct)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ======== MAIN PAGE ======== */
export default function EnergyTransitionPage() {
  const [tab, setTab] = useState(0);

  const panels = [FleetTransition, GridEFTracker, AvoidedEmissions, MethaneOGMP, Scope3Cat11];
  const Panel = panels[tab];

  return (
    <div className="min-h-screen" style={{ backgroundColor: COLORS.bg }}>
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <Zap size={28} style={{ color: COLORS.primary }} />
          <div>
            <h1 className="text-2xl font-bold" style={{ color: COLORS.primary }}>Energy Transition & Emissions</h1>
            <p className="text-sm text-gray-500">Fleet transition planning, grid EF tracking, methane OGMP, and Scope 3 Cat 11</p>
          </div>
        </div>

        <div className="flex gap-1 mb-6 bg-white p-1 rounded-lg border shadow-sm overflow-x-auto" style={{ borderColor: COLORS.border }}>
          {tabs.map((t, i) => {
            const Icon = t.icon;
            return (
              <button key={i} onClick={() => setTab(i)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${tab === i ? 'text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                style={tab === i ? { backgroundColor: COLORS.primary } : {}}>
                <Icon size={16} /> {t.label}
              </button>
            );
          })}
        </div>

        <Panel />
      </div>
    </div>
  );
}
