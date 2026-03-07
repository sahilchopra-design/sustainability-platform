/**
 * Geothermal Energy Project Assessment Panel
 * IRENA Geothermal Power Technology Brief 2024 / IEA World Energy Outlook 2023
 *
 * Computes LCOE, capacity factor, resource viability, induced seismicity risk,
 * NPV, IRR, payback, and Paris-alignment for binary, flash, dry-steam, and EGS plants.
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, RadialBarChart, RadialBar,
} from 'recharts';

const API = 'http://localhost:8001/api/v1/geothermal';

const DEFAULT_FORM = {
  project_name: 'Geothermal Assessment',
  country_iso2: 'IS',
  plant_type: 'binary',
  installed_capacity_mw: 50,
  reservoir_temp_c: 160,
  well_depth_m: 2500,
  number_of_wells: 10,
  drilling_cost_musd_per_well: 5.0,
  surface_plant_cost_musd: 80,
  annual_opex_musd: 6.0,
  capacity_factor_pct: '',
  discount_rate_pct: 8.0,
  project_lifetime_years: 25,
  has_district_heating: false,
  heating_revenue_musd_yr: 0,
  carbon_price_usd_tco2: 50,
  grid_emission_factor_gco2_kwh: 400,
};

const PLANT_LABELS = {
  dry_steam: 'Dry Steam',
  single_flash: 'Single Flash',
  double_flash: 'Double Flash',
  binary: 'Binary (ORC)',
  egs: 'EGS (Enhanced)',
};

const KPI = ({ label, value, sub, accent }) => (
  <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
    <div className={`text-2xl font-bold ${accent || 'text-white'}`}>{value}</div>
    <div className="text-[11px] text-white/40 mt-1">{label}</div>
    {sub && <div className="text-[10px] text-white/25 mt-0.5">{sub}</div>}
  </div>
);

const RISK_COLORS = { low: '#22c55e', medium: '#eab308', high: '#ef4444' };

export function GeothermalPanel() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [plantTypes, setPlantTypes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API}/plant-types`).then(r => setPlantTypes(r.data)).catch(() => {});
  }, []);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const num = (k, v) => set(k, v === '' ? '' : Number(v));

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = { ...form };
      if (payload.capacity_factor_pct === '' || payload.capacity_factor_pct === null) {
        delete payload.capacity_factor_pct;
      } else {
        payload.capacity_factor_pct = Number(payload.capacity_factor_pct);
      }
      const { data } = await axios.post(`${API}/assess`, payload);
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const Field = ({ label, k, type = 'number', opts, step }) => (
    <div>
      <label className="text-[11px] text-white/40 block mb-1">{label}</label>
      {opts ? (
        <select value={form[k]} onChange={e => set(k, e.target.value)}
          className="w-full bg-[#1a2332] border border-white/[0.08] rounded px-2 py-1.5 text-sm text-white">
          {Object.entries(opts).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      ) : type === 'checkbox' ? (
        <input type="checkbox" checked={form[k]} onChange={e => set(k, e.target.checked)}
          className="accent-blue-500" />
      ) : (
        <input type="number" step={step || 'any'} value={form[k]}
          onChange={e => num(k, e.target.value)}
          className="w-full bg-[#1a2332] border border-white/[0.08] rounded px-2 py-1.5 text-sm text-white" />
      )}
    </div>
  );

  // Build benchmark chart data
  const benchData = result?.irena_benchmarks?.map(b => ({
    year: b.year,
    lcoe: b.lcoe_usd_mwh,
    cf: b.capacity_factor_pct,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
        <h2 className="text-xl font-bold text-white">Geothermal Energy Project Assessment</h2>
        <p className="text-xs text-white/40 mt-1">
          IRENA Geothermal Power Technology Brief 2024 / IEA World Energy Outlook 2023
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Project Parameters</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Field label="Project Name" k="project_name" type="text" />
          <Field label="Country (ISO2)" k="country_iso2" type="text" />
          <Field label="Plant Type" k="plant_type" opts={PLANT_LABELS} />
          <Field label="Installed Capacity (MW)" k="installed_capacity_mw" />
          <Field label="Reservoir Temp (C)" k="reservoir_temp_c" />
          <Field label="Well Depth (m)" k="well_depth_m" />
          <Field label="Number of Wells" k="number_of_wells" step={1} />
          <Field label="Drilling Cost (M USD/well)" k="drilling_cost_musd_per_well" />
          <Field label="Surface Plant Cost (M USD)" k="surface_plant_cost_musd" />
          <Field label="Annual OPEX (M USD)" k="annual_opex_musd" />
          <Field label="Capacity Factor % (blank=default)" k="capacity_factor_pct" />
          <Field label="Discount Rate (%)" k="discount_rate_pct" />
          <Field label="Lifetime (years)" k="project_lifetime_years" step={1} />
          <Field label="Carbon Price (USD/tCO2)" k="carbon_price_usd_tco2" />
          <Field label="Grid EF (gCO2/kWh)" k="grid_emission_factor_gco2_kwh" />
          <div>
            <label className="text-[11px] text-white/40 block mb-1">District Heating</label>
            <div className="flex items-center gap-3">
              <input type="checkbox" checked={form.has_district_heating}
                onChange={e => set('has_district_heating', e.target.checked)}
                className="accent-blue-500" />
              <span className="text-xs text-white/50">Enabled</span>
            </div>
          </div>
          {form.has_district_heating && (
            <Field label="Heating Revenue (M USD/yr)" k="heating_revenue_musd_yr" />
          )}
        </div>

        <button onClick={run} disabled={loading}
          className="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-40 transition-colors">
          {loading ? 'Assessing...' : 'Run Assessment'}
        </button>
        {error && <div className="mt-3 text-sm text-red-400">{error}</div>}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* KPI Row 1: Cost & Generation */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPI label="Total CAPEX" value={`$${result.total_capex_musd}M`} sub="Drilling + Surface" />
            <KPI label="LCOE" value={`$${result.lcoe_usd_mwh}/MWh`}
              sub={`IRENA: $${result.irena_lcoe_range.low}-${result.irena_lcoe_range.high}`}
              accent={result.lcoe_usd_mwh <= result.irena_lcoe_range.high ? 'text-green-400' : 'text-red-400'} />
            <KPI label="Annual Generation" value={`${result.annual_generation_gwh} GWh`}
              sub={`CF: ${result.capacity_factor_pct}%`} />
            <KPI label="Lifetime Generation" value={`${result.lifetime_generation_twh} TWh`}
              sub={`${form.project_lifetime_years} years`} />
          </div>

          {/* KPI Row 2: Carbon */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPI label="Plant CO2 Intensity" value={`${result.plant_co2_intensity_gco2_kwh} gCO2/kWh`}
              accent={result.paris_aligned ? 'text-green-400' : 'text-amber-400'}
              sub={result.paris_aligned ? 'Paris-Aligned (<100g)' : 'Not Paris-Aligned'} />
            <KPI label="Annual Avoided" value={`${Math.round(result.annual_avoided_emissions_tco2).toLocaleString()} tCO2`} />
            <KPI label="Lifetime Avoided" value={`${Math.round(result.lifetime_avoided_tco2).toLocaleString()} tCO2`} />
            {result.carbon_abatement_cost_usd_tco2 !== null && (
              <KPI label="Abatement Cost" value={`$${result.carbon_abatement_cost_usd_tco2}/tCO2`} />
            )}
          </div>

          {/* KPI Row 3: Economics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPI label="NPV" value={`$${result.npv_musd}M`}
              accent={result.npv_musd >= 0 ? 'text-green-400' : 'text-red-400'} />
            <KPI label="Equity IRR" value={result.equity_irr_pct !== null ? `${result.equity_irr_pct}%` : 'N/A'}
              accent={result.equity_irr_pct && result.equity_irr_pct > 10 ? 'text-green-400' : 'text-amber-400'} />
            <KPI label="Simple Payback" value={result.simple_payback_years ? `${result.simple_payback_years} yrs` : 'N/A'} />
            <KPI label="Annual Revenue" value={`$${result.annual_revenue_musd}M`} />
          </div>

          {/* Resource & Risk */}
          <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
            <h3 className="text-sm font-semibold text-white/70 mb-4">Resource Viability & Risk</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-[11px] text-white/40 mb-1">Resource Viability</div>
                <div className={`text-lg font-bold ${
                  result.resource_viability === 'High' ? 'text-green-400' :
                  result.resource_viability === 'Medium' ? 'text-amber-400' : 'text-red-400'
                }`}>{result.resource_viability}</div>
              </div>
              <div>
                <div className="text-[11px] text-white/40 mb-1">Temperature Adequacy</div>
                <div className={`text-lg font-bold ${
                  result.temp_adequacy === 'Optimal' ? 'text-green-400' :
                  result.temp_adequacy === 'Adequate' ? 'text-amber-400' : 'text-red-400'
                }`}>{result.temp_adequacy}</div>
                <div className="text-[10px] text-white/30">{form.reservoir_temp_c}C</div>
              </div>
              <div>
                <div className="text-[11px] text-white/40 mb-1">Induced Seismicity Risk</div>
                <div className="text-lg font-bold" style={{ color: RISK_COLORS[result.seismicity_risk] }}>
                  {result.seismicity_risk.toUpperCase()}
                </div>
                <div className="text-[10px] text-white/30">{result.seismicity_note}</div>
              </div>
              <div>
                <div className="text-[11px] text-white/40 mb-1">LCOE vs IRENA</div>
                <div className={`text-sm font-semibold ${
                  result.lcoe_vs_irena.includes('competitive') ? 'text-green-400' :
                  result.lcoe_vs_irena.includes('Within') ? 'text-blue-400' : 'text-red-400'
                }`}>{result.lcoe_vs_irena}</div>
              </div>
            </div>

            {/* District Heating */}
            {result.district_heating_benefit.enabled && (
              <div className="mt-4 pt-4 border-t border-white/[0.06]">
                <div className="text-[11px] text-white/40 mb-1">District Heating Benefit</div>
                <div className="text-sm text-white">
                  Revenue: ${result.district_heating_benefit.annual_revenue_musd}M/yr
                  {result.district_heating_benefit.lcoe_reduction_pct > 0 &&
                    ` | LCOE offset: ${result.district_heating_benefit.lcoe_reduction_pct}%`}
                </div>
              </div>
            )}
          </div>

          {/* IRENA Benchmark Charts */}
          {benchData.length > 0 && (
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
              <h3 className="text-sm font-semibold text-white/70 mb-4">
                IRENA Geothermal Benchmarks (Historical)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="text-[11px] text-white/40 mb-2">LCOE Trend (USD/MWh)</div>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={benchData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                      <XAxis dataKey="year" tick={{ fill: '#ffffff60', fontSize: 10 }} />
                      <YAxis tick={{ fill: '#ffffff60', fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: '#111827', border: '1px solid #ffffff15', borderRadius: 8, fontSize: 11 }} />
                      <Line type="monotone" dataKey="lcoe" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} name="LCOE" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <div className="text-[11px] text-white/40 mb-2">Capacity Factor Trend (%)</div>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={benchData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                      <XAxis dataKey="year" tick={{ fill: '#ffffff60', fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fill: '#ffffff60', fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: '#111827', border: '1px solid #ffffff15', borderRadius: 8, fontSize: 11 }} />
                      <Bar dataKey="cf" fill="#22c55e" radius={[3, 3, 0, 0]} name="Capacity Factor %" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default GeothermalPanel;
