import React, { useState, useEffect } from 'react';
import { usePersonaDefaults } from '../../../context/PersonaContext';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import {
  Wind, Sun, Calculator, TrendingUp, FileCheck,
  ChevronRight, AlertTriangle, Zap, DollarSign, Leaf
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
};

const TURBINE_CLASSES = ['I', 'II', 'III', 'S'];
const WIND_REGIONS = ['north_sea', 'baltic', 'north_atlantic', 'mediterranean', 'pacific', 'gulf_of_mexico'];
const SOLAR_COUNTRIES = ['DE', 'ES', 'AU', 'IN', 'US', 'AE'];
const TECHNOLOGIES = ['onshore_wind', 'offshore_wind', 'solar_pv', 'solar_csp'];
const CREDIT_RATINGS = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'B+', 'B'];
const PRICE_STRUCTURES = ['fixed', 'baseload_index', 'pay_as_produced', 'floor_ceiling', 'hybrid'];

const tabs = [
  { label: 'Wind Assessment', icon: Wind },
  { label: 'Solar Assessment', icon: Sun },
  { label: 'LCOE Calculator', icon: Calculator },
  { label: 'Project Finance', icon: TrendingUp },
  { label: 'PPA Risk', icon: FileCheck },
];

function KpiCard({ label, value, sub, color }) {
  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm" style={{ borderColor: COLORS.border }}>
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-bold" style={{ color: color || COLORS.primary }}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm mb-4" style={{ borderColor: COLORS.border }}>
      {title && <h3 className="text-lg font-semibold mb-4" style={{ color: COLORS.primary }}>{title}</h3>}
      {children}
    </div>
  );
}

function Inp({ label, value, onChange, type = 'number', step, min, max, className = '' }) {
  return (
    <div className={`flex flex-col ${className}`}>
      <label className="text-xs text-gray-500 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
        step={step}
        min={min}
        max={max}
        className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
        style={{ borderColor: COLORS.border }}
      />
    </div>
  );
}

function Sel({ label, value, onChange, options, className = '' }) {
  return (
    <div className={`flex flex-col ${className}`}>
      <label className="text-xs text-gray-500 mb-1">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
        style={{ borderColor: COLORS.border }}
      >
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
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-5 py-2 rounded-lg text-white font-medium text-sm transition-opacity hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
      style={{ backgroundColor: bg }}
    >
      {children}
    </button>
  );
}

/* ======== TAB 1: WIND ASSESSMENT ======== */
function WindAssessment() {
  const [form, setForm] = useState({
    turbine_class: 'II',
    region: 'north_sea',
    num_turbines: 50,
    turbine_capacity_mw: 8.0,
    hub_height_m: 120,
    wake_loss_pct: 8.0,
    availability_pct: 95.0,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/renewable-ppa/wind-yield`, form);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  const probData = result ? [
    { name: 'P50', mwh: result.p50_mwh || 0 },
    { name: 'P75', mwh: result.p75_mwh || 0 },
    { name: 'P90', mwh: result.p90_mwh || 0 },
    { name: 'P99', mwh: result.p99_mwh || 0 },
  ] : [];

  return (
    <div className="space-y-4">
      <Section title="Wind Farm Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Turbine Class" value={form.turbine_class} onChange={v => setForm({ ...form, turbine_class: v })} options={TURBINE_CLASSES} />
          <Sel label="Region" value={form.region} onChange={v => setForm({ ...form, region: v })} options={WIND_REGIONS} />
          <Inp label="Number of Turbines" value={form.num_turbines} onChange={v => setForm({ ...form, num_turbines: v })} min={1} />
          <Inp label="Turbine Capacity (MW)" value={form.turbine_capacity_mw} onChange={v => setForm({ ...form, turbine_capacity_mw: v })} step={0.1} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <Inp label="Hub Height (m)" value={form.hub_height_m} onChange={v => setForm({ ...form, hub_height_m: v })} />
          <Inp label="Wake Loss (%)" value={form.wake_loss_pct} onChange={v => setForm({ ...form, wake_loss_pct: v })} step={0.1} />
          <Inp label="Availability (%)" value={form.availability_pct} onChange={v => setForm({ ...form, availability_pct: v })} step={0.1} />
        </div>
        <Btn onClick={run} disabled={loading}><Wind size={16} /> Assess Wind Yield</Btn>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="P50 Generation" value={`${fmt0(result.p50_mwh)} MWh`} sub="50th percentile" color={COLORS.primary} />
            <KpiCard label="P75 Generation" value={`${fmt0(result.p75_mwh)} MWh`} sub="75th percentile" color={COLORS.blue} />
            <KpiCard label="P90 Generation" value={`${fmt0(result.p90_mwh)} MWh`} sub="Bankable case" color={COLORS.accent} />
            <KpiCard label="Capacity Factor" value={fmtPct(result.capacity_factor_pct)} sub="Net of losses" color={COLORS.amber} />
          </div>

          <Section title="Probability Distribution — Annual Generation">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={probData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={v => fmt0(v) + ' MWh'} />
                <Bar dataKey="mwh" name="Generation (MWh)" radius={[4, 4, 0, 0]}>
                  {probData.map((_, i) => (
                    <Cell key={i} fill={[COLORS.primary, COLORS.blue, COLORS.accent, COLORS.teal][i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Section>

          {result.monthly_profile && (
            <Section title="Monthly Wind Profile">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={result.monthly_profile}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="mwh" name="MWh" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          <Section title="Assessment Details">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div><span className="text-gray-500">Gross AEP:</span> <strong>{fmt0(result.gross_aep_mwh)} MWh</strong></div>
              <div><span className="text-gray-500">Wake Loss:</span> <strong>{fmtPct(result.wake_loss_applied)}</strong></div>
              <div><span className="text-gray-500">Availability:</span> <strong>{fmtPct(result.availability_applied)}</strong></div>
              <div><span className="text-gray-500">Wind Speed:</span> <strong>{fmt2(result.mean_wind_speed_ms)} m/s</strong></div>
              <div><span className="text-gray-500">Full Load Hours:</span> <strong>{fmt0(result.full_load_hours)} h</strong></div>
              <div><span className="text-gray-500">Installed Capacity:</span> <strong>{fmt0(result.installed_capacity_mw)} MW</strong></div>
              <div><span className="text-gray-500">Region:</span> <strong>{result.region}</strong></div>
              <div><span className="text-gray-500">Class:</span> <strong>{result.turbine_class}</strong></div>
            </div>
          </Section>
        </>
      )}
    </div>
  );
}

/* ======== TAB 2: SOLAR ASSESSMENT ======== */
function SolarAssessment() {
  const [form, setForm] = useState({
    country: 'ES',
    capacity_kwp: 100000,
    performance_ratio: 0.82,
    degradation_pct_yr: 0.5,
    tilt_deg: 25,
    azimuth_deg: 180,
    tracking: 'fixed',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/renewable-ppa/solar-yield`, form);
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
      <Section title="Solar PV Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Country" value={form.country} onChange={v => setForm({ ...form, country: v })} options={SOLAR_COUNTRIES} />
          <Inp label="Capacity (kWp)" value={form.capacity_kwp} onChange={v => setForm({ ...form, capacity_kwp: v })} />
          <Inp label="Performance Ratio" value={form.performance_ratio} onChange={v => setForm({ ...form, performance_ratio: v })} step={0.01} min={0} max={1} />
          <Inp label="Degradation (%/yr)" value={form.degradation_pct_yr} onChange={v => setForm({ ...form, degradation_pct_yr: v })} step={0.1} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          <Inp label="Tilt (deg)" value={form.tilt_deg} onChange={v => setForm({ ...form, tilt_deg: v })} />
          <Inp label="Azimuth (deg)" value={form.azimuth_deg} onChange={v => setForm({ ...form, azimuth_deg: v })} />
          <Sel label="Tracking" value={form.tracking} onChange={v => setForm({ ...form, tracking: v })} options={['fixed', 'single_axis', 'dual_axis']} />
        </div>
        <Btn onClick={run} disabled={loading}><Sun size={16} /> Assess Solar Yield</Btn>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <KpiCard label="GHI" value={`${fmt0(result.ghi_kwh_m2)} kWh/m2`} sub="Global Horizontal Irradiance" color={COLORS.amber} />
            <KpiCard label="P50 Generation" value={`${fmt0(result.p50_mwh)} MWh`} sub="Expected case" color={COLORS.primary} />
            <KpiCard label="P75 Generation" value={`${fmt0(result.p75_mwh)} MWh`} sub="Conservative" color={COLORS.blue} />
            <KpiCard label="P90 Generation" value={`${fmt0(result.p90_mwh)} MWh`} sub="Bankable" color={COLORS.accent} />
            <KpiCard label="Specific Yield" value={`${fmt0(result.specific_yield_kwh_kwp)} kWh/kWp`} sub="Year 1" color={COLORS.teal} />
          </div>

          {result.monthly_irradiance && (
            <Section title="Monthly Irradiance Profile">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={result.monthly_irradiance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="ghi" name="GHI (kWh/m2)" fill={COLORS.amber} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="generation_mwh" name="Generation (MWh)" fill={COLORS.accent} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          <Section title="Degradation Curve — Lifetime Generation">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={(result.degradation_curve || Array.from({ length: 30 }, (_, i) => ({
                year: i + 1,
                generation_mwh: (result.p50_mwh || 150000) * Math.pow(1 - (form.degradation_pct_yr / 100), i),
              })))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" label={{ value: 'Year', position: 'insideBottom', offset: -5 }} />
                <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={v => fmt0(v) + ' MWh'} />
                <Line type="monotone" dataKey="generation_mwh" name="Annual Generation" stroke={COLORS.primary} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Assessment Details">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div><span className="text-gray-500">Country:</span> <strong>{result.country}</strong></div>
              <div><span className="text-gray-500">PR:</span> <strong>{fmtPct((result.performance_ratio || form.performance_ratio) * 100)}</strong></div>
              <div><span className="text-gray-500">Capacity:</span> <strong>{fmt0(result.capacity_kwp || form.capacity_kwp)} kWp</strong></div>
              <div><span className="text-gray-500">Lifetime:</span> <strong>{result.lifetime_years || 30} years</strong></div>
              <div><span className="text-gray-500">Total Lifetime:</span> <strong>{fmt0(result.total_lifetime_mwh)} MWh</strong></div>
              <div><span className="text-gray-500">CO2 Avoided:</span> <strong>{fmt0(result.co2_avoided_tonnes)} t/yr</strong></div>
            </div>
          </Section>
        </>
      )}
    </div>
  );
}

/* ======== TAB 3: LCOE CALCULATOR ======== */
function LCOECalculator() {
  const d = usePersonaDefaults('energy_finance');
  const [form, setForm] = useState({
    technology:              d.technology    || 'offshore_wind',
    capex_per_kw:            d.capexPerKw    ? Number(d.capexPerKw)    : 1200,
    opex_per_kw_yr:          d.opexPerMwh    ? Number(d.opexPerMwh) * 25 : 40,
    annual_generation_mwh:   d.capacityMW && d.capacityFactor
      ? Math.round(Number(d.capacityMW) * Number(d.capacityFactor) * 8760) : 1500000,
    capacity_mw:             d.capacityMW    ? Number(d.capacityMW)    : 400,
    wacc_pct:                d.wacc          ? Number(d.wacc)          : 6.5,
    lifetime_years:          d.lifetimeYears ? Number(d.lifetimeYears) : 25,
    decommissioning_per_kw:  50,
    grid_connection_per_kw:  150,
  });

  useEffect(() => {
    if (!d.technology) return;
    setForm(f => ({
      ...f,
      technology:            d.technology,
      capex_per_kw:          Number(d.capexPerKw) || f.capex_per_kw,
      capacity_mw:           Number(d.capacityMW) || f.capacity_mw,
      wacc_pct:              Number(d.wacc) || f.wacc_pct,
      lifetime_years:        Number(d.lifetimeYears) || f.lifetime_years,
      annual_generation_mwh: d.capacityMW && d.capacityFactor
        ? Math.round(Number(d.capacityMW) * Number(d.capacityFactor) * 8760)
        : f.annual_generation_mwh,
    }));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.technology]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/renewable-ppa/lcoe`, form);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  const waterfallData = result ? [
    { name: 'CAPEX', value: result.capex_component || 0, fill: COLORS.primary },
    { name: 'OPEX', value: result.opex_component || 0, fill: COLORS.blue },
    { name: 'Grid', value: result.grid_component || 0, fill: COLORS.purple },
    { name: 'Decom', value: result.decom_component || 0, fill: COLORS.amber },
    { name: 'WACC', value: result.wacc_component || 0, fill: COLORS.red },
    { name: 'Total LCOE', value: result.lcoe_eur_mwh || 0, fill: COLORS.accent },
  ] : [];

  return (
    <div className="space-y-4">
      <Section title="LCOE Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Technology" value={form.technology} onChange={v => setForm({ ...form, technology: v })}
            options={TECHNOLOGIES.map(t => ({ value: t, label: t.replace(/_/g, ' ').toUpperCase() }))} />
          <Inp label="CAPEX (EUR/kW)" value={form.capex_per_kw} onChange={v => setForm({ ...form, capex_per_kw: v })} />
          <Inp label="OPEX (EUR/kW/yr)" value={form.opex_per_kw_yr} onChange={v => setForm({ ...form, opex_per_kw_yr: v })} />
          <Inp label="Annual Gen. (MWh)" value={form.annual_generation_mwh} onChange={v => setForm({ ...form, annual_generation_mwh: v })} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Capacity (MW)" value={form.capacity_mw} onChange={v => setForm({ ...form, capacity_mw: v })} />
          <Inp label="WACC (%)" value={form.wacc_pct} onChange={v => setForm({ ...form, wacc_pct: v })} step={0.1} />
          <Inp label="Lifetime (years)" value={form.lifetime_years} onChange={v => setForm({ ...form, lifetime_years: v })} />
          <Inp label="Decom Cost (EUR/kW)" value={form.decommissioning_per_kw} onChange={v => setForm({ ...form, decommissioning_per_kw: v })} />
        </div>
        <Btn onClick={run} disabled={loading}><Calculator size={16} /> Calculate LCOE</Btn>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <KpiCard label="LCOE" value={`EUR ${fmt2(result.lcoe_eur_mwh)}/MWh`} sub={result.technology} color={COLORS.primary} />
            <KpiCard label="Total Lifetime Cost" value={`EUR ${fmt0(result.total_lifetime_cost_eur)}`} sub={`${form.lifetime_years} years`} color={COLORS.blue} />
            <KpiCard label="Cost Competitiveness" value={result.competitiveness_rating || 'N/A'} sub="vs. wholesale price" color={COLORS.accent} />
          </div>

          <Section title="LCOE Waterfall Breakdown">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={waterfallData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'EUR/MWh', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={v => `EUR ${fmt2(v)}/MWh`} />
                <Bar dataKey="value" name="Component" radius={[4, 4, 0, 0]}>
                  {waterfallData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Section>

          {result.benchmark_comparison && (
            <Section title="Technology Benchmark Comparison">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={result.benchmark_comparison} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" label={{ value: 'EUR/MWh', position: 'insideBottom', offset: -5 }} />
                  <YAxis dataKey="technology" type="category" width={120} />
                  <Tooltip formatter={v => `EUR ${fmt2(v)}/MWh`} />
                  <Bar dataKey="lcoe" name="LCOE" fill={COLORS.primary} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ======== TAB 4: PROJECT FINANCE ======== */
function ProjectFinance() {
  const d = usePersonaDefaults('energy_finance');
  const [form, setForm] = useState({
    technology:                  d.technology    || 'offshore_wind',
    capacity_mw:                 d.capacityMW    ? Number(d.capacityMW)    : 400,
    capex_per_kw:                d.capexPerKw    ? Number(d.capexPerKw)    : 1200,
    opex_per_kw_yr:              d.opexPerMwh    ? Number(d.opexPerMwh) * 25 : 40,
    annual_generation_mwh:       d.capacityMW && d.capacityFactor
      ? Math.round(Number(d.capacityMW) * Number(d.capacityFactor) * 8760) : 1500000,
    ppa_price_eur_mwh:           d.ppaPrice      ? Number(d.ppaPrice)      : 65.0,
    wacc_pct:                    d.wacc          ? Number(d.wacc)          : 6.5,
    lifetime_years:              d.lifetimeYears ? Number(d.lifetimeYears) : 25,
    debt_ratio_pct:   70,
    debt_tenor_years: 18,
    debt_rate_pct:    4.5,
    tax_rate_pct:     25,
    grid_emission_factor_kg_mwh: d.gridEf ? Number(d.gridEf) * 1000 : 350,
    carbon_price_eur_t: 90,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/renewable-ppa/project-assess`, form);
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
      <Section title="Project Finance Parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Sel label="Technology" value={form.technology} onChange={v => setForm({ ...form, technology: v })}
            options={TECHNOLOGIES.map(t => ({ value: t, label: t.replace(/_/g, ' ').toUpperCase() }))} />
          <Inp label="Capacity (MW)" value={form.capacity_mw} onChange={v => setForm({ ...form, capacity_mw: v })} />
          <Inp label="CAPEX (EUR/kW)" value={form.capex_per_kw} onChange={v => setForm({ ...form, capex_per_kw: v })} />
          <Inp label="PPA Price (EUR/MWh)" value={form.ppa_price_eur_mwh} onChange={v => setForm({ ...form, ppa_price_eur_mwh: v })} step={0.5} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="WACC (%)" value={form.wacc_pct} onChange={v => setForm({ ...form, wacc_pct: v })} step={0.1} />
          <Inp label="Debt Ratio (%)" value={form.debt_ratio_pct} onChange={v => setForm({ ...form, debt_ratio_pct: v })} />
          <Inp label="Debt Tenor (yrs)" value={form.debt_tenor_years} onChange={v => setForm({ ...form, debt_tenor_years: v })} />
          <Inp label="Debt Rate (%)" value={form.debt_rate_pct} onChange={v => setForm({ ...form, debt_rate_pct: v })} step={0.1} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Annual Gen. (MWh)" value={form.annual_generation_mwh} onChange={v => setForm({ ...form, annual_generation_mwh: v })} />
          <Inp label="OPEX (EUR/kW/yr)" value={form.opex_per_kw_yr} onChange={v => setForm({ ...form, opex_per_kw_yr: v })} />
          <Inp label="Grid EF (kgCO2/MWh)" value={form.grid_emission_factor_kg_mwh} onChange={v => setForm({ ...form, grid_emission_factor_kg_mwh: v })} />
          <Inp label="Carbon Price (EUR/t)" value={form.carbon_price_eur_t} onChange={v => setForm({ ...form, carbon_price_eur_t: v })} />
        </div>
        <Btn onClick={run} disabled={loading}><TrendingUp size={16} /> Assess Project</Btn>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <KpiCard label="Project IRR" value={fmtPct(result.project_irr_pct)} sub="Unlevered" color={COLORS.primary} />
            <KpiCard label="Equity IRR" value={fmtPct(result.equity_irr_pct)} sub="Levered" color={COLORS.accent} />
            <KpiCard label="NPV" value={`EUR ${fmt0(result.npv_eur)}`} sub={`@ ${form.wacc_pct}% WACC`} color={COLORS.blue} />
            <KpiCard label="Payback" value={`${fmt2(result.payback_years)} yrs`} sub="Simple payback" color={COLORS.amber} />
            <KpiCard label="CO2 Avoided" value={`${fmt0(result.co2_avoided_lifetime_t)} t`} sub="Lifetime" color={COLORS.teal} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Total CAPEX" value={`EUR ${fmt0(result.total_capex_eur)}`} sub="Investment" />
            <KpiCard label="Annual Revenue" value={`EUR ${fmt0(result.annual_revenue_eur)}`} sub="From PPA" />
            <KpiCard label="DSCR (Min)" value={fmt2(result.min_dscr)} sub={result.min_dscr >= 1.3 ? 'Bankable' : 'Below threshold'} color={result.min_dscr >= 1.3 ? COLORS.accent : COLORS.red} />
            <KpiCard label="LCOE" value={`EUR ${fmt2(result.lcoe_eur_mwh)}/MWh`} sub="Levelised" />
          </div>

          {result.cashflow_profile && (
            <Section title="Annual Cashflow Profile">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={result.cashflow_profile}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} />
                  <Tooltip formatter={v => `EUR ${fmt0(v)}`} />
                  <Legend />
                  <Bar dataKey="revenue" name="Revenue" fill={COLORS.accent} stackId="a" />
                  <Bar dataKey="opex" name="OPEX" fill={COLORS.amber} stackId="b" />
                  <Bar dataKey="debt_service" name="Debt Service" fill={COLORS.red} stackId="b" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          <Section title="Carbon Impact">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div><span className="text-gray-500">Annual CO2 Avoided:</span> <strong>{fmt0(result.co2_avoided_annual_t)} t</strong></div>
              <div><span className="text-gray-500">Carbon Credit Value:</span> <strong>EUR {fmt0(result.carbon_credit_value_eur)}/yr</strong></div>
              <div><span className="text-gray-500">Abatement Cost:</span> <strong>EUR {fmt2(result.abatement_cost_eur_t)}/tCO2</strong></div>
              <div><span className="text-gray-500">Social Carbon NPV:</span> <strong>EUR {fmt0(result.social_carbon_npv_eur)}</strong></div>
            </div>
          </Section>
        </>
      )}
    </div>
  );
}

/* ======== TAB 5: PPA RISK ======== */
function PPARisk() {
  const [form, setForm] = useState({
    offtaker_name: 'European Industrial Corp',
    offtaker_credit_rating: 'BBB+',
    price_structure: 'fixed',
    ppa_price_eur_mwh: 65.0,
    tenor_years: 15,
    annual_volume_mwh: 1500000,
    curtailment_risk_pct: 5.0,
    hedging_pct: 80.0,
    balancing_cost_eur_mwh: 3.0,
    country: 'DE',
    regulatory_stability_score: 7,
    grid_congestion_risk: 'medium',
    shape_risk_premium_pct: 2.5,
    indexation: 'partial_cpi',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/v1/renewable-ppa/ppa-risk`, form);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []); // eslint-disable-line

  const radarData = result ? [
    { dimension: 'Credit Risk', score: result.credit_risk_score || 0, fullMark: 10 },
    { dimension: 'Volume Risk', score: result.volume_risk_score || 0, fullMark: 10 },
    { dimension: 'Price Risk', score: result.price_risk_score || 0, fullMark: 10 },
    { dimension: 'Regulatory Risk', score: result.regulatory_risk_score || 0, fullMark: 10 },
    { dimension: 'Basis Risk', score: result.basis_risk_score || 0, fullMark: 10 },
  ] : [];

  const bankabilityColor = (rating) => {
    if (!rating) return COLORS.border;
    const r = rating.toLowerCase();
    if (r.includes('high') || r.includes('a')) return COLORS.accent;
    if (r.includes('medium') || r.includes('b')) return COLORS.amber;
    return COLORS.red;
  };

  return (
    <div className="space-y-4">
      <Section title="PPA Offtaker & Terms">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Offtaker Name" value={form.offtaker_name} onChange={v => setForm({ ...form, offtaker_name: v })} type="text" />
          <Sel label="Credit Rating" value={form.offtaker_credit_rating} onChange={v => setForm({ ...form, offtaker_credit_rating: v })} options={CREDIT_RATINGS} />
          <Sel label="Price Structure" value={form.price_structure} onChange={v => setForm({ ...form, price_structure: v })} options={PRICE_STRUCTURES} />
          <Inp label="PPA Price (EUR/MWh)" value={form.ppa_price_eur_mwh} onChange={v => setForm({ ...form, ppa_price_eur_mwh: v })} step={0.5} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Tenor (years)" value={form.tenor_years} onChange={v => setForm({ ...form, tenor_years: v })} />
          <Inp label="Annual Volume (MWh)" value={form.annual_volume_mwh} onChange={v => setForm({ ...form, annual_volume_mwh: v })} />
          <Inp label="Curtailment Risk (%)" value={form.curtailment_risk_pct} onChange={v => setForm({ ...form, curtailment_risk_pct: v })} step={0.5} />
          <Inp label="Hedging (%)" value={form.hedging_pct} onChange={v => setForm({ ...form, hedging_pct: v })} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Inp label="Balancing Cost (EUR/MWh)" value={form.balancing_cost_eur_mwh} onChange={v => setForm({ ...form, balancing_cost_eur_mwh: v })} step={0.5} />
          <Inp label="Regulatory Stability (1-10)" value={form.regulatory_stability_score} onChange={v => setForm({ ...form, regulatory_stability_score: v })} min={1} max={10} />
          <Sel label="Grid Congestion" value={form.grid_congestion_risk} onChange={v => setForm({ ...form, grid_congestion_risk: v })} options={['low', 'medium', 'high']} />
          <Sel label="Indexation" value={form.indexation} onChange={v => setForm({ ...form, indexation: v })} options={['none', 'partial_cpi', 'full_cpi', 'wholesale_linked']} />
        </div>
        <Btn onClick={run} disabled={loading}><FileCheck size={16} /> Assess PPA Risk</Btn>
      </Section>

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4">{error}</div>}

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Overall PPA Risk" value={fmt2(result.overall_risk_score) + ' / 10'} sub="Lower is better" color={COLORS.primary} />
            <KpiCard label="Expected Revenue" value={`EUR ${fmt0(result.expected_annual_revenue_eur)}/yr`} sub="Net of risks" color={COLORS.accent} />
            <KpiCard label="Revenue at Risk" value={`EUR ${fmt0(result.revenue_at_risk_eur)}`} sub="95th pct worst case" color={COLORS.red} />
            <div className="bg-white border rounded-lg p-4 shadow-sm flex flex-col items-center justify-center" style={{ borderColor: COLORS.border }}>
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Bankability</div>
              <div
                className="text-lg font-bold px-4 py-1 rounded-full text-white"
                style={{ backgroundColor: bankabilityColor(result.bankability_rating) }}
              >
                {result.bankability_rating || 'N/A'}
              </div>
              <div className="text-xs text-gray-400 mt-1">Lender assessment</div>
            </div>
          </div>

          <Section title="Risk Radar — 5 Dimensions">
            <ResponsiveContainer width="100%" height={360}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 10 }} />
                <Radar name="Risk Score" dataKey="score" stroke={COLORS.primary} fill={COLORS.primary} fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Risk Breakdown">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b" style={{ borderColor: COLORS.border }}>
                    <th className="pb-2">Dimension</th>
                    <th className="pb-2">Score</th>
                    <th className="pb-2">Assessment</th>
                    <th className="pb-2">Mitigation</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.risk_dimensions || []).map((d, i) => (
                    <tr key={i} className="border-b" style={{ borderColor: COLORS.border }}>
                      <td className="py-2 font-medium">{d.dimension}</td>
                      <td className="py-2">
                        <span className="px-2 py-0.5 rounded text-white text-xs font-medium"
                          style={{ backgroundColor: d.score <= 3 ? COLORS.accent : d.score <= 6 ? COLORS.amber : COLORS.red }}>
                          {fmt2(d.score)}
                        </span>
                      </td>
                      <td className="py-2 text-gray-600">{d.assessment}</td>
                      <td className="py-2 text-gray-500">{d.mitigation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          {result.recommendations && (
            <Section title="Recommendations">
              <ul className="space-y-2">
                {result.recommendations.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <AlertTriangle size={14} className="text-amber-500 mt-0.5 flex-shrink-0" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ======== MAIN PAGE ======== */
export default function EnergyFinancePage() {
  const [tab, setTab] = useState(0);

  const panels = [WindAssessment, SolarAssessment, LCOECalculator, ProjectFinance, PPARisk];
  const Panel = panels[tab];

  return (
    <div className="min-h-screen" style={{ backgroundColor: COLORS.bg }}>
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3 mb-6">
          <Zap size={28} style={{ color: COLORS.primary }} />
          <div>
            <h1 className="text-2xl font-bold" style={{ color: COLORS.primary }}>Renewable Project Finance & PPA Risk</h1>
            <p className="text-sm text-gray-500">Wind/Solar yield assessment, LCOE, project finance and PPA risk analysis</p>
          </div>
        </div>

        <div className="flex gap-1 mb-6 bg-white p-1 rounded-lg border shadow-sm overflow-x-auto" style={{ borderColor: COLORS.border }}>
          {tabs.map((t, i) => {
            const Icon = t.icon;
            return (
              <button
                key={i}
                onClick={() => setTab(i)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                  tab === i ? 'text-white' : 'text-gray-600 hover:bg-gray-50'
                }`}
                style={tab === i ? { backgroundColor: COLORS.primary } : {}}
              >
                <Icon size={16} />
                {t.label}
              </button>
            );
          })}
        </div>

        <Panel />
      </div>
    </div>
  );
}
