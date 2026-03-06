/**
 * Agriculture Climate Risk Panel
 * IPCC AR6 WG2 Ch.5 crop yield sensitivity
 * EU Deforestation Regulation 2023/1115 (EUDR) compliance
 * Verra VM0042 / IPCC AR6 WG3 Ch.7 soil carbon
 * WRI AQUEDUCT 3.0 water stress
 */
import React, { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt = (v, dp = 1) => v == null ? "—" : Number(v).toFixed(dp);
const fmtUsd = (v) => v == null ? "—" : `$${(Number(v) / 1e6).toFixed(2)}M`;

function Badge({ label, color = "bg-white/[0.06] text-white/60" }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}
function Card({ title, subtitle, children, className = "" }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06] ${className}`}>
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
function StatCard({ label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
      <p className="text-xs text-white/40 font-medium mb-1">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
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
function Input({ value, onChange, type = "text", ...rest }) {
  return (
    <input type={type} value={value}
      onChange={e => onChange(type === "number" ? parseFloat(e.target.value) || 0 : e.target.value)}
      className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
      {...rest} />
  );
}
function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50">
      {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  );
}

const CROPS = [
  { v: "wheat", l: "Wheat" }, { v: "maize", l: "Maize" }, { v: "rice", l: "Rice" },
  { v: "soy", l: "Soybean" }, { v: "potato", l: "Potato" }, { v: "sugarcane", l: "Sugarcane" },
  { v: "cotton", l: "Cotton" }, { v: "barley", l: "Barley" }, { v: "rapeseed", l: "Rapeseed" },
];
const EUDR_COMMODITIES = [
  { v: "soy", l: "Soy" }, { v: "beef", l: "Beef" }, { v: "palm_oil", l: "Palm Oil" },
  { v: "cocoa", l: "Cocoa" }, { v: "coffee", l: "Coffee" }, { v: "wood", l: "Wood" },
  { v: "rubber", l: "Rubber" },
];
const FARM_TYPES = [
  { v: "arable", l: "Arable / Cropland" }, { v: "mixed", l: "Mixed Farming" },
  { v: "livestock", l: "Livestock / Pasture" }, { v: "horticulture", l: "Horticulture" },
];
const SCENARIOS = [
  { v: "1.5C", l: "1.5°C — Paris-aligned" },
  { v: "2C", l: "2°C — Orderly" },
  { v: "3C", l: "3°C — Disorderly" },
];
const HORIZONS = [
  { v: 2030, l: "2030" }, { v: 2040, l: "2040" }, { v: 2050, l: "2050" },
];

const DEFAULT_FORM = {
  entity_name: "Sample Agri Entity",
  country_code: "BR",
  crop_types: ["soy", "maize"],
  farm_type: "arable",
  total_area_ha: 5000,
  annual_revenue_usd: 8e6,
  eudr_commodities: ["soy"],
  baseline_yield_t_ha: 3.2,
  irrigation_pct: 15,
  water_annual_withdrawal_m3: 500000,
  scenario: "2C",
  horizon_year: 2050,
};

const RISK_COLORS = {
  LOW: "text-emerald-400", MEDIUM: "text-amber-400",
  HIGH: "text-red-400", VERY_HIGH: "text-red-500", CRITICAL: "text-red-600",
};
const RISK_BG = {
  LOW: "bg-emerald-500/10 border-emerald-500/20",
  MEDIUM: "bg-amber-500/10 border-amber-500/20",
  HIGH: "bg-red-500/10 border-red-500/20",
  VERY_HIGH: "bg-red-500/15 border-red-500/30",
  CRITICAL: "bg-red-600/15 border-red-600/30",
};

export default function AgriculturePanel() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const toggleCrop = (crop) =>
    setForm(prev => ({
      ...prev,
      crop_types: prev.crop_types.includes(crop)
        ? prev.crop_types.filter(c => c !== crop)
        : [...prev.crop_types, crop],
    }));

  const toggleEudrCommodity = (c) =>
    setForm(prev => ({
      ...prev,
      eudr_commodities: prev.eudr_commodities.includes(c)
        ? prev.eudr_commodities.filter(x => x !== c)
        : [...prev.eudr_commodities, c],
    }));

  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/agriculture/calculate`, {
        ...form,
        irrigation_pct: form.irrigation_pct / 100,
      });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const yieldChartData = result ? [
    { name: "Baseline", yield: form.baseline_yield_t_ha, fill: "#6366f1" },
    { name: `${form.scenario} ${form.horizon_year}`, yield: result.projected_yield_t_ha, fill: result.yield_change_pct < 0 ? "#ef4444" : "#10b981" },
  ] : [];

  const complianceColor = (score) =>
    score >= 80 ? "text-emerald-400" : score >= 50 ? "text-amber-400" : "text-red-400";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="IPCC AR6 WG2 Ch.5" color="bg-emerald-500/10 text-emerald-400" />
        <Badge label="EUDR 2023/1115" color="bg-blue-500/10 text-blue-300" />
        <Badge label="Verra VM0042 Soil Carbon" color="bg-amber-500/10 text-amber-400" />
        <Badge label="WRI AQUEDUCT 3.0" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="TCFD Physical Risk" color="bg-white/[0.06] text-white/60" />
      </div>

      <Card title="Agriculture Risk Parameters"
        subtitle="Crop yield sensitivity, EUDR compliance, soil carbon, and water stress assessment">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Field label="Entity Name">
            <Input value={form.entity_name} onChange={v => set("entity_name", v)} />
          </Field>
          <Field label="Country (ISO2)">
            <Input value={form.country_code} onChange={v => set("country_code", v.toUpperCase())} />
          </Field>
          <Field label="Farm Type">
            <Sel value={form.farm_type} onChange={v => set("farm_type", v)} options={FARM_TYPES} />
          </Field>
          <Field label="Total Area (ha)">
            <Input type="number" value={form.total_area_ha} onChange={v => set("total_area_ha", v)} />
          </Field>
          <Field label="Annual Revenue (USD)">
            <Input type="number" value={form.annual_revenue_usd} onChange={v => set("annual_revenue_usd", v)} />
          </Field>
          <Field label="Baseline Yield (t/ha)" hint="Current-climate average yield">
            <Input type="number" value={form.baseline_yield_t_ha} onChange={v => set("baseline_yield_t_ha", v)} step="0.1" />
          </Field>
          <Field label="Irrigation Coverage (%)" hint="% of total area with irrigation">
            <Input type="number" value={form.irrigation_pct} onChange={v => set("irrigation_pct", v)} min="0" max="100" />
          </Field>
          <Field label="Annual Water Withdrawal (m³)">
            <Input type="number" value={form.water_annual_withdrawal_m3} onChange={v => set("water_annual_withdrawal_m3", v)} />
          </Field>
          <div className="grid grid-cols-2 gap-2">
            <Field label="Scenario">
              <Sel value={form.scenario} onChange={v => set("scenario", v)} options={SCENARIOS} />
            </Field>
            <Field label="Horizon">
              <Sel value={form.horizon_year} onChange={v => set("horizon_year", parseInt(v))} options={HORIZONS} />
            </Field>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-medium text-white/60 mb-2">Crop Types</p>
            <div className="flex flex-wrap gap-2">
              {CROPS.map(c => (
                <button key={c.v} onClick={() => toggleCrop(c.v)}
                  className={`px-2.5 py-1 rounded text-xs font-medium border transition-all ${
                    form.crop_types.includes(c.v)
                      ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                      : "bg-white/[0.02] border-white/[0.06] text-white/40 hover:text-white/60"
                  }`}>
                  {c.l}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-white/60 mb-2">EUDR In-Scope Commodities</p>
            <div className="flex flex-wrap gap-2">
              {EUDR_COMMODITIES.map(c => (
                <button key={c.v} onClick={() => toggleEudrCommodity(c.v)}
                  className={`px-2.5 py-1 rounded text-xs font-medium border transition-all ${
                    form.eudr_commodities.includes(c.v)
                      ? "bg-amber-500/10 border-amber-500/20 text-amber-300"
                      : "bg-white/[0.02] border-white/[0.06] text-white/40 hover:text-white/60"
                  }`}>
                  {c.l}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-8 py-2.5 rounded-lg transition-colors">
            {loading ? "Assessing…" : "Run Agriculture Risk Assessment"}
          </button>
        </div>
      </Card>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-400">{error}</div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Overall Risk Banner */}
          <div className={`rounded-xl border p-5 ${RISK_BG[result.overall_risk_category] || "bg-white/[0.02] border-white/[0.06]"}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-white/40 mb-1">Overall Agriculture Climate Risk</p>
                <p className={`text-2xl font-bold ${RISK_COLORS[result.overall_risk_category] || "text-white"}`}>
                  {result.overall_risk_category}
                </p>
                <p className="text-xs text-white/40 mt-1">Composite score: {fmt(result.overall_risk_score)}/100</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-white/40">Temperature Delta</p>
                <p className="text-xl font-bold text-amber-400">+{fmt(result.temp_delta_c)}°C</p>
                <p className="text-[11px] text-white/30">{form.scenario} by {form.horizon_year}</p>
              </div>
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Yield Change"
              value={`${result.yield_change_pct > 0 ? "+" : ""}${fmt(result.yield_change_pct)}%`}
              color={result.yield_change_pct >= 0 ? "text-emerald-400" : "text-red-400"}
              sub={`${fmt(result.projected_yield_t_ha, 2)} t/ha projected`} />
            <StatCard label="Revenue Impact"
              value={fmtUsd(result.yield_revenue_impact_usd)}
              color={result.yield_revenue_impact_usd >= 0 ? "text-emerald-400" : "text-red-400"}
              sub="Crop yield income effect" />
            <StatCard label="EUDR Compliance Score"
              value={`${fmt(result.eudr_compliance_score, 0)}/100`}
              color={complianceColor(result.eudr_compliance_score)}
              sub={`${result.eudr_country_risk_tier} country tier`} />
            <StatCard label="Water Stress Index"
              value={fmt(result.water_stress_index, 2)}
              color={result.water_stress_index > 3 ? "text-red-400" : result.water_stress_index > 1.5 ? "text-amber-400" : "text-emerald-400"}
              sub={result.water_stress_category} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <StatCard label="Soil Carbon Seq."
              value={`${fmt(result.soil_carbon_seq_tco2e_yr, 0)} tCO₂e/yr`}
              color="text-emerald-400"
              sub={`Credit value: $${(result.soil_carbon_credit_value_usd / 1000).toFixed(0)}k/yr`} />
            <StatCard label="Water at Risk"
              value={`${(result.water_at_risk_m3_yr / 1000).toFixed(0)} '000 m³/yr`}
              color={result.water_at_risk_m3_yr > 0 ? "text-amber-400" : "text-emerald-400"} />
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
              <p className="text-xs text-white/40 font-medium mb-1">EUDR Deforestation Risk</p>
              <p className={`text-sm font-bold ${
                result.eudr_deforestation_risk === "LOW" ? "text-emerald-400" :
                result.eudr_deforestation_risk === "MEDIUM" ? "text-amber-400" : "text-red-400"
              }`}>{result.eudr_deforestation_risk}</p>
              {result.eudr_high_risk_commodities?.length > 0 && (
                <p className="text-[11px] text-red-300 mt-1">
                  High-risk: {result.eudr_high_risk_commodities.join(", ")}
                </p>
              )}
            </div>
          </div>

          {/* Yield Chart */}
          <Card title="Projected Yield vs Baseline" subtitle="IPCC AR6 WG2 Ch.5 — tonnes per hectare">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={yieldChartData} barSize={60}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 10 }} label={{ value: "t/ha", angle: -90, position: "insideLeft", fontSize: 10 }} />
                <Tooltip formatter={(v) => [`${v.toFixed(2)} t/ha`]} />
                <Bar dataKey="yield" name="Yield (t/ha)" radius={[6, 6, 0, 0]}>
                  {yieldChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Methodology */}
          <Card title="Methodology Reference">
            <div className="space-y-1 text-[11px] text-white/40">
              <p><span className="text-white/60 font-medium">Crop Yield:</span> IPCC AR6 WGII Ch.5 Table 5.2 — mean fractional yield change per 1°C warming for 17 crops. Irrigation adjustment: −40% sensitivity reduction for irrigated area.</p>
              <p><span className="text-white/60 font-medium">EUDR:</span> EU Regulation 2023/1115 — 7 in-scope commodities, 4-point compliance checker (due diligence, operator register, traceability, geo-polygon). Country risk tiers: high (deforestation hotspots), standard, low.</p>
              <p><span className="text-white/60 font-medium">Soil Carbon:</span> Verra VM0042 / IPCC AR6 WG3 Ch.7 — sequestration potential 0.5–3.0 tCO₂e/ha/yr by farm type. Carbon credit price: $15/tCO₂e (2026 voluntary market).</p>
              <p><span className="text-white/60 font-medium">Water Stress:</span> WRI AQUEDUCT 3.0 proxy — withdrawal-to-availability ratio; categories: Low / Medium / High / Extremely High.</p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
