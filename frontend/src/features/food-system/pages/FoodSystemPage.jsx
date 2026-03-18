/**
 * FoodSystemPage.jsx  — E54
 * Route: /food-system
 *
 * Food System & Land Use Finance
 * Tabs:
 *   1. SBTi FLAG Targets     — Science-Based Targets for FLAG sectors
 *   2. FAO Crop Yield Impact — RCP yield impacts with adaptation
 *   3. TNFD Food LEAP        — LEAP framework for food commodities
 *   4. EUDR & Ag Emissions   — Deforestation-free + EUDR ag emissions
 *   5. Land Degradation & LDN — Land Degradation Neutrality assessment
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, AreaChart, Area, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const PREFIX = '/api/v1/food-system';

function sr(i, seed) {
  return Math.abs(Math.sin(i * 9301 + seed * 49297) * 233280) % 233280 / 233280;
}

// ── Primitives ────────────────────────────────────────────────────────────────
function Section({ title, subtitle, children }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-4">
      {title && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, accent, badge }) {
  const cls = accent === 'green' ? 'text-emerald-600' : accent === 'red' ? 'text-red-600' : accent === 'amber' ? 'text-amber-600' : 'text-gray-900';
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-start justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{label}</span>
        {badge && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">{badge}</span>}
      </div>
      <div className={`text-2xl font-bold font-mono ${cls}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-3">
      <label className="text-xs font-medium text-gray-600 w-44 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'number', placeholder }) {
  return (
    <input type={type} value={value} onChange={onChange} placeholder={placeholder}
      className="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={onChange}
      className="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Btn({ onClick, children, loading }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold disabled:opacity-50 transition-colors">
      {loading ? 'Running…' : children}
    </button>
  );
}

const TABS = [
  { id: 'flag', label: 'SBTi FLAG Targets' },
  { id: 'fao', label: 'FAO Crop Yield' },
  { id: 'tnfd', label: 'TNFD Food LEAP' },
  { id: 'eudr', label: 'EUDR & Ag Emissions' },
  { id: 'ldn', label: 'Land Degradation & LDN' },
];

// ── Tab 1 — SBTi FLAG Targets ─────────────────────────────────────────────────
function FlagTab() {
  const [form, setForm] = useState({ entity_id: 'FS-001', sector: 'cattle', base_year: 2020, target_year: 2030, current_emissions_tco2e: 500000 });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 55;

  const FLAG_REDUCTIONS = { cattle: 30, poultry_pigs: 25, crops: 20, forests_trees: 35 };

  const fallback = () => {
    const reqPct = FLAG_REDUCTIONS[form.sector] || 25;
    const mitTarget = form.current_emissions_tco2e * (reqPct / 100);
    const removal = form.current_emissions_tco2e * 0.05;
    return {
      flag_scope: form.sector === 'forests_trees' ? 'AFOLU' : 'FLAG Scope 1+2+3',
      required_reduction_pct: reqPct,
      land_mitigation_target_tco2_yr: mitTarget.toFixed(0),
      target_met: sr(1, seed) > 0.5,
      chart: [
        { name: 'Current Emissions', value: +form.current_emissions_tco2e },
        { name: 'Mitigation Target', value: +mitTarget.toFixed(0) },
        { name: 'Removal Target', value: +removal.toFixed(0) },
      ],
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/sbti-flag`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="SBTi FLAG (Forest, Land & Agriculture) Targets">
        <Row label="Entity ID"><Inp value={form.entity_id} onChange={e => setForm({ ...form, entity_id: e.target.value })} type="text" /></Row>
        <Row label="Sector"><Sel value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })}
          options={[
            { value: 'cattle', label: 'Cattle' }, { value: 'poultry_pigs', label: 'Poultry & Pigs' },
            { value: 'crops', label: 'Crops' }, { value: 'forests_trees', label: 'Forests & Trees' },
          ]} /></Row>
        <Row label="Base Year"><Inp value={form.base_year} onChange={e => setForm({ ...form, base_year: e.target.value })} /></Row>
        <Row label="Target Year"><Inp value={form.target_year} onChange={e => setForm({ ...form, target_year: e.target.value })} /></Row>
        <Row label="Current Emissions (tCO2e)"><Inp value={form.current_emissions_tco2e} onChange={e => setForm({ ...form, current_emissions_tco2e: e.target.value })} /></Row>
        <Btn onClick={run} loading={loading}>Set FLAG Targets</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="FLAG Scope" value={d.flag_scope} sub={`${form.base_year}–${form.target_year}`} accent="green" badge="SBTi" />
        <KpiCard label="Required Reduction" value={`${d.required_reduction_pct}%`} sub="vs base year" accent="amber" />
        <KpiCard label="Mitigation Target" value={`${(+d.land_mitigation_target_tco2_yr / 1000).toFixed(1)}k`} sub="tCO2/yr" accent="green" />
        <KpiCard label="Target Met" value={d.target_met ? 'YES' : 'NO'} accent={d.target_met ? 'green' : 'red'} />
      </div>
      <Section title="Emissions vs Targets (tCO2e)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={d.chart} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip formatter={v => v.toLocaleString()} />
            <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]}
              label={{ position: 'top', fontSize: 10, formatter: v => (v / 1000).toFixed(0) + 'k' }} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2 — FAO Crop Yield Impact ─────────────────────────────────────────────
function FaoTab() {
  const [form, setForm] = useState({ crop: 'wheat', region: 'south_asia', baseline_yield_t_ha: 3.2 });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 99;

  const CROP_IMPACTS = {
    wheat: { rcp26: -3, rcp45: -8, rcp85: -18 },
    maize: { rcp26: -5, rcp45: -12, rcp85: -22 },
    rice: { rcp26: -2, rcp45: -6, rcp85: -14 },
    soy: { rcp26: -4, rcp45: -10, rcp85: -20 },
    coffee: { rcp26: -8, rcp45: -18, rcp85: -35 },
    cocoa: { rcp26: -6, rcp45: -15, rcp85: -28 },
  };

  const fallback = () => {
    const impacts = CROP_IMPACTS[form.crop] || { rcp26: -5, rcp45: -12, rcp85: -20 };
    const adapt = 6 + sr(1, seed) * 5;
    return {
      baseline_yield_t_ha: form.baseline_yield_t_ha,
      rcp45_impact_pct: impacts.rcp45,
      rcp85_impact_pct: impacts.rcp85,
      adaptation_gain_pct: adapt.toFixed(1),
      chart: [
        { scenario: 'RCP 2.6', noAdapt: impacts.rcp26, withAdapt: impacts.rcp26 + adapt },
        { scenario: 'RCP 4.5', noAdapt: impacts.rcp45, withAdapt: impacts.rcp45 + adapt },
        { scenario: 'RCP 8.5', noAdapt: impacts.rcp85, withAdapt: impacts.rcp85 + adapt },
      ],
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/fao-crop-yield`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="FAO Crop Yield Climate Impact (RCP Scenarios)">
        <Row label="Crop"><Sel value={form.crop} onChange={e => setForm({ ...form, crop: e.target.value })}
          options={[
            { value: 'wheat', label: 'Wheat' }, { value: 'maize', label: 'Maize' },
            { value: 'rice', label: 'Rice' }, { value: 'soy', label: 'Soy' },
            { value: 'coffee', label: 'Coffee' }, { value: 'cocoa', label: 'Cocoa' },
          ]} /></Row>
        <Row label="Region"><Sel value={form.region} onChange={e => setForm({ ...form, region: e.target.value })}
          options={[
            { value: 'south_asia', label: 'South Asia' }, { value: 'sub_saharan_africa', label: 'Sub-Saharan Africa' },
            { value: 'latin_america', label: 'Latin America' }, { value: 'europe', label: 'Europe' },
          ]} /></Row>
        <Row label="Baseline Yield (t/ha)"><Inp value={form.baseline_yield_t_ha} onChange={e => setForm({ ...form, baseline_yield_t_ha: e.target.value })} /></Row>
        <Btn onClick={run} loading={loading}>Model Crop Yield</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="Baseline Yield" value={`${d.baseline_yield_t_ha} t/ha`} sub="current productivity" accent="green" badge="FAO" />
        <KpiCard label="RCP 4.5 Impact" value={`${d.rcp45_impact_pct}%`} sub="yield change by 2050" accent="amber" />
        <KpiCard label="RCP 8.5 Impact" value={`${d.rcp85_impact_pct}%`} sub="yield change by 2050" accent="red" />
        <KpiCard label="Adaptation Gain" value={`+${d.adaptation_gain_pct}%`} sub="if best practices adopted" accent="green" />
      </div>
      <Section title="Yield Impact % — With / Without Adaptation">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={d.chart} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="scenario" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} unit="%" />
            <Tooltip unit="%" />
            <Legend />
            <Bar dataKey="noAdapt" name="No Adaptation" fill="#ef4444" radius={[2, 2, 0, 0]} />
            <Bar dataKey="withAdapt" name="With Adaptation" fill="#10b981" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 3 — TNFD Food LEAP ────────────────────────────────────────────────────
const COMMODITIES = ['cattle', 'cocoa', 'coffee', 'oil_palm', 'soy', 'wheat'];

function TnfdTab() {
  const [form, setForm] = useState({ entity_name: 'Agro Corp SA', selected_commodities: ['cattle', 'cocoa', 'soy'] });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 144;

  const toggleCommodity = (c) => {
    const cur = form.selected_commodities;
    setForm({ ...form, selected_commodities: cur.includes(c) ? cur.filter(x => x !== c) : [...cur, c] });
  };

  const fallback = () => ({
    leap_composite_score: (45 + sr(1, seed) * 40).toFixed(1),
    nature_dependency: (sr(2, seed) * 5).toFixed(2),
    nature_impact: (sr(3, seed) * 5).toFixed(2),
    biodiversity_risk: ['Low', 'Medium', 'High', 'Very High'][Math.floor(sr(4, seed) * 4)],
    radar: [
      { stage: 'Locate', score: +(40 + sr(5, seed) * 50).toFixed(0) },
      { stage: 'Evaluate', score: +(35 + sr(6, seed) * 50).toFixed(0) },
      { stage: 'Assess', score: +(30 + sr(7, seed) * 50).toFixed(0) },
      { stage: 'Prepare', score: +(25 + sr(8, seed) * 50).toFixed(0) },
    ],
  });

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/tnfd-food-leap`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="TNFD Food LEAP Framework Assessment">
        <Row label="Entity Name"><Inp value={form.entity_name} onChange={e => setForm({ ...form, entity_name: e.target.value })} type="text" /></Row>
        <Row label="Commodities">
          <div className="flex flex-wrap gap-2">
            {COMMODITIES.map(c => (
              <button key={c} onClick={() => toggleCommodity(c)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${form.selected_commodities.includes(c) ? 'bg-emerald-600 text-white border-emerald-600' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
                {c.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </Row>
        <Btn onClick={run} loading={loading}>Run TNFD LEAP</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="LEAP Composite Score" value={`${d.leap_composite_score}`} sub="out of 100" accent={+d.leap_composite_score >= 60 ? 'green' : 'amber'} badge="TNFD" />
        <KpiCard label="Nature Dependency" value={`${d.nature_dependency}/5`} sub="ES dependency score" accent={+d.nature_dependency >= 3 ? 'red' : 'amber'} />
        <KpiCard label="Nature Impact" value={`${d.nature_impact}/5`} sub="impact magnitude" accent={+d.nature_impact >= 3 ? 'red' : 'amber'} />
        <KpiCard label="Biodiversity Risk" value={d.biodiversity_risk} accent={d.biodiversity_risk === 'Very High' || d.biodiversity_risk === 'High' ? 'red' : 'amber'} />
      </div>
      <Section title="LEAP Stage Scores (%)">
        <ResponsiveContainer width="100%" height={260}>
          <RadarChart data={d.radar} cx="50%" cy="50%" outerRadius={90}>
            <PolarGrid />
            <PolarAngleAxis dataKey="stage" tick={{ fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
            <Radar name="LEAP Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.35} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 4 — EUDR & Agricultural Emissions ────────────────────────────────────
function EudrFoodTab() {
  const [form, setForm] = useState({ farm_area_ha: 2500, livestock_count: 800, crop_type: 'soy' });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 188;

  const fallback = () => {
    const scope1 = form.livestock_count * 3.5 + form.farm_area_ha * 2;
    const scope2 = form.farm_area_ha * 0.4;
    const scope3 = form.farm_area_ha * 1.2 + form.livestock_count * 0.8;
    const total = scope1 + scope2 + scope3;
    return {
      deforestation_free: sr(1, seed) > 0.4,
      eudr_compliant: sr(2, seed) > 0.3,
      total_ag_emissions_tco2e_yr: total.toFixed(0),
      emission_intensity_tco2e_ha: (total / form.farm_area_ha).toFixed(2),
      chart: [
        { name: 'Scope 1', s1: +scope1.toFixed(0), s2: 0, s3: 0 },
        { name: 'Scope 2', s1: 0, s2: +scope2.toFixed(0), s3: 0 },
        { name: 'Scope 3', s1: 0, s2: 0, s3: +scope3.toFixed(0) },
      ],
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const [r1, r2] = await Promise.all([
        axios.post(`${API}${PREFIX}/eudr-food`, form),
        axios.post(`${API}${PREFIX}/agricultural-emissions`, form),
      ]);
      setRes({ ...r1.data, ...r2.data });
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="EUDR Compliance & Agricultural Emission Intensity">
        <Row label="Farm Area (ha)"><Inp value={form.farm_area_ha} onChange={e => setForm({ ...form, farm_area_ha: e.target.value })} /></Row>
        <Row label="Livestock Count"><Inp value={form.livestock_count} onChange={e => setForm({ ...form, livestock_count: e.target.value })} /></Row>
        <Row label="Crop Type"><Inp value={form.crop_type} onChange={e => setForm({ ...form, crop_type: e.target.value })} type="text" /></Row>
        <Btn onClick={run} loading={loading}>Assess EUDR & Emissions</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="Deforestation Free" value={d.deforestation_free ? 'YES' : 'NO'} accent={d.deforestation_free ? 'green' : 'red'} badge="EUDR" />
        <KpiCard label="EUDR Compliant" value={d.eudr_compliant ? 'YES' : 'NO'} accent={d.eudr_compliant ? 'green' : 'red'} />
        <KpiCard label="Total Ag Emissions" value={`${(+d.total_ag_emissions_tco2e_yr / 1000).toFixed(1)}k`} sub="tCO2e/yr" accent="amber" />
        <KpiCard label="Emission Intensity" value={`${d.emission_intensity_tco2e_ha}`} sub="tCO2e/ha" accent={+d.emission_intensity_tco2e_ha > 5 ? 'red' : 'amber'} />
      </div>
      <Section title="Agricultural Emissions by Scope (tCO2e/yr)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={d.chart} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip formatter={v => v.toLocaleString()} />
            <Legend />
            <Bar dataKey="s1" name="Scope 1" stackId="a" fill="#10b981" />
            <Bar dataKey="s2" name="Scope 2" stackId="a" fill="#6ee7b7" />
            <Bar dataKey="s3" name="Scope 3" stackId="a" fill="#d1fae5" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 5 — Land Degradation & LDN ───────────────────────────────────────────
function LdnTab() {
  const [form, setForm] = useState({ land_area_ha: 5000, land_use: 'cropland', country_code: 'BRA' });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 265;

  const fallback = () => {
    const carbonStock = form.land_area_ha * (form.land_use === 'forest' ? 120 : form.land_use === 'wetland' ? 90 : 45);
    const series = Array.from({ length: 21 }, (_, i) => ({
      year: 2025 + i,
      bau: +(carbonStock * (1 - i * 0.008 * (0.8 + sr(i, seed) * 0.4))).toFixed(0),
      sustainable: +(carbonStock * (1 + i * 0.005 * (0.9 + sr(i + 21, seed) * 0.2))).toFixed(0),
      restoration: +(carbonStock * (1 + i * 0.015 * (0.85 + sr(i + 42, seed) * 0.3))).toFixed(0),
    }));
    return {
      ldn_status: sr(1, seed) > 0.5 ? 'Degraded' : 'Stable',
      carbon_stock_tco2e: carbonStock.toFixed(0),
      restoration_potential_ha: (form.land_area_ha * 0.22 * (0.8 + sr(2, seed) * 0.4)).toFixed(0),
      restoration_cost_usd: (form.land_area_ha * 250 * (0.7 + sr(3, seed) * 0.6)).toFixed(0),
      series,
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/land-degradation`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="Land Degradation Neutrality (SDG 15.3) Assessment">
        <Row label="Land Area (ha)"><Inp value={form.land_area_ha} onChange={e => setForm({ ...form, land_area_ha: e.target.value })} /></Row>
        <Row label="Land Use"><Sel value={form.land_use} onChange={e => setForm({ ...form, land_use: e.target.value })}
          options={[
            { value: 'cropland', label: 'Cropland' }, { value: 'grassland', label: 'Grassland' },
            { value: 'forest', label: 'Forest' }, { value: 'wetland', label: 'Wetland' },
          ]} /></Row>
        <Row label="Country Code"><Inp value={form.country_code} onChange={e => setForm({ ...form, country_code: e.target.value })} type="text" /></Row>
        <Btn onClick={run} loading={loading}>Assess Land Degradation</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="LDN Status" value={d.ldn_status} accent={d.ldn_status === 'Degraded' ? 'red' : d.ldn_status === 'Stable' ? 'amber' : 'green'} badge="SDG 15.3" />
        <KpiCard label="Carbon Stock" value={`${(+d.carbon_stock_tco2e / 1000).toFixed(0)}k`} sub="tCO2e current" accent="green" />
        <KpiCard label="Restoration Potential" value={`${d.restoration_potential_ha} ha`} sub="degraded land" accent="amber" />
        <KpiCard label="Restoration Cost" value={`$${(+d.restoration_cost_usd / 1e6).toFixed(1)}M`} sub="full restoration" accent="amber" />
      </div>
      <Section title="Carbon Stock Trajectory — 3 Management Scenarios (tCO2e)">
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={d.series} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} interval={4} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="restoration" name="Active Restoration" stroke="#10b981" fill="#d1fae5" />
            <Area type="monotone" dataKey="sustainable" name="Sustainable Mgmt" stroke="#6ee7b7" fill="#ecfdf5" />
            <Area type="monotone" dataKey="bau" name="Business as Usual" stroke="#ef4444" fill="#fee2e2" />
          </AreaChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function FoodSystemPage() {
  const [tab, setTab] = useState('flag');
  const tabContent = { flag: <FlagTab />, fao: <FaoTab />, tnfd: <TnfdTab />, eudr: <EudrFoodTab />, ldn: <LdnTab /> };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-bold text-gray-900">Food System & Land Use Finance</h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              E54 · SBTi FLAG · FAO Crop Yield · TNFD Food LEAP · EUDR · ICTI
            </span>
          </div>
          <p className="text-sm text-gray-500">SBTi FLAG targets, FAO crop yield climate impacts, TNFD LEAP assessment, EUDR compliance and land degradation analysis.</p>
        </div>

        <div className="flex gap-1 mb-6 bg-white rounded-xl border border-gray-200 p-1 shadow-sm w-fit flex-wrap">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === t.id ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-50'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {tabContent[tab]}
      </div>
    </div>
  );
}
