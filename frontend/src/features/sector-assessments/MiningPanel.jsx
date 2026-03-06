/**
 * Mining & Extractives Climate Risk Panel
 * GISTM 2020 — tailings consequence classification
 * IEA Critical Minerals 2023 — supply concentration (HHI)
 * NGFS Phase 4 — carbon price paths
 * ICMM Water Framework / UNEP FI stranded asset model
 */
import React, { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt = (v, dp = 1) => v == null ? "—" : Number(v).toFixed(dp);
const fmtM = (v, currency = "$") => v == null ? "—" : `${currency}${(Number(v) / 1e6).toFixed(2)}M`;
const fmtPct = (v) => v == null ? "—" : `${(Number(v) * 100).toFixed(1)}%`;

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

const COMMODITIES = [
  { v: "coal", l: "Thermal Coal" }, { v: "copper", l: "Copper" },
  { v: "cobalt", l: "Cobalt" }, { v: "lithium", l: "Lithium" },
  { v: "nickel", l: "Nickel" }, { v: "gold", l: "Gold" },
  { v: "iron_ore", l: "Iron Ore" }, { v: "bauxite", l: "Bauxite" },
  { v: "platinum", l: "Platinum" }, { v: "rare_earth", l: "Rare Earth Elements" },
];
const MINE_TYPES = [
  { v: "open_cut", l: "Open-Cut / Open-Pit" }, { v: "underground", l: "Underground" },
  { v: "placer", l: "Placer" }, { v: "ISL", l: "In-Situ Leaching (ISL)" },
];
const GISTM_CONSEQUENCE = [
  { v: "EXTREME", l: "EXTREME — Major downstream community" },
  { v: "VERY_HIGH", l: "VERY HIGH — Significant downstream impacts" },
  { v: "HIGH", l: "HIGH — Some downstream impacts" },
  { v: "LOW", l: "LOW — Minimal downstream consequences" },
];
const GISTM_COMPLIANCE = [
  { v: "full", l: "Full Compliance (GISTM 2020)" },
  { v: "partial", l: "Partial Compliance" },
  { v: "non_compliant", l: "Non-Compliant" },
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
  entity_name: "Sample Mining Co.",
  commodity: "copper",
  country_code: "CL",
  mine_type: "open_cut",
  annual_production_kt: 120,
  reserve_life_years: 22,
  book_value_usd: 800e6,
  annual_revenue_usd: 450e6,
  tailings_volume_m3: 2e7,
  tailings_consequence_class: "HIGH",
  gistm_compliance_level: "partial",
  water_annual_withdrawal_m3: 5e6,
  water_recycling_rate: 0.55,
  scope1_tco2e: 80000,
  scope2_tco2e: 40000,
  mine_closure_year: 2046,
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

export default function MiningPanel() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/mining/calculate`, form);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Build a risk summary bar chart
  const riskBreakdown = result ? [
    { name: "Tailings", value: result.tailings_annual_failure_prob * 1000 },
    { name: "Water Stress", value: result.water_stress_score * 20 },
    { name: "Carbon Cost", value: Math.min(100, result.carbon_cost_as_pct_revenue * 10) },
    { name: "Stranding", value: result.stranded_asset_risk_pct },
    { name: "Closure Gap", value: Math.min(100, (result.closure_underfunding_usd / Math.max(result.closure_cost_usd, 1)) * 100) },
  ] : [];

  const complianceFlagColor = (flag) => ({
    NON_COMPLIANT: "text-red-400 bg-red-500/10 border-red-500/20",
    PARTIAL: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    COMPLIANT: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  }[flag] || "text-white/60 bg-white/[0.04] border-white/[0.06]");

  const concentrationColor = (s) => ({
    EXTREME: "text-red-400", HIGH: "text-red-400",
    MODERATE: "text-amber-400", LOW: "text-emerald-400",
  }[s] || "text-white/60");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="GISTM 2020" color="bg-red-500/10 text-red-300" />
        <Badge label="IEA Critical Minerals 2023" color="bg-blue-500/10 text-blue-300" />
        <Badge label="NGFS Phase 4 Carbon Price" color="bg-purple-500/10 text-purple-300" />
        <Badge label="ICMM Water Framework" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="UNEP FI Stranded Asset" color="bg-amber-500/10 text-amber-400" />
      </div>

      <Card title="Mining Entity Parameters"
        subtitle="GISTM tailings risk, water intensity, closure cost NPV, critical minerals supply concentration">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Field label="Entity Name">
            <Input value={form.entity_name} onChange={v => set("entity_name", v)} />
          </Field>
          <Field label="Commodity">
            <Sel value={form.commodity} onChange={v => set("commodity", v)} options={COMMODITIES} />
          </Field>
          <Field label="Country (ISO2)">
            <Input value={form.country_code} onChange={v => set("country_code", v.toUpperCase())} />
          </Field>
          <Field label="Mine Type">
            <Sel value={form.mine_type} onChange={v => set("mine_type", v)} options={MINE_TYPES} />
          </Field>
          <Field label="Annual Production (kt)">
            <Input type="number" value={form.annual_production_kt} onChange={v => set("annual_production_kt", v)} />
          </Field>
          <Field label="Reserve Life (years)">
            <Input type="number" value={form.reserve_life_years} onChange={v => set("reserve_life_years", v)} />
          </Field>
          <Field label="Book Value (USD)">
            <Input type="number" value={form.book_value_usd} onChange={v => set("book_value_usd", v)} />
          </Field>
          <Field label="Annual Revenue (USD)">
            <Input type="number" value={form.annual_revenue_usd} onChange={v => set("annual_revenue_usd", v)} />
          </Field>
          <Field label="Mine Closure Year">
            <Input type="number" value={form.mine_closure_year} onChange={v => set("mine_closure_year", v)} />
          </Field>
        </div>

        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Tailings */}
          <Card title="Tailings Parameters" subtitle="GISTM 2020" className="border-red-500/10">
            <div className="space-y-3">
              <Field label="Tailings Volume (m³)">
                <Input type="number" value={form.tailings_volume_m3} onChange={v => set("tailings_volume_m3", v)} />
              </Field>
              <Field label="GISTM Consequence Class">
                <Sel value={form.tailings_consequence_class} onChange={v => set("tailings_consequence_class", v)} options={GISTM_CONSEQUENCE} />
              </Field>
              <Field label="GISTM Compliance Level">
                <Sel value={form.gistm_compliance_level} onChange={v => set("gistm_compliance_level", v)} options={GISTM_COMPLIANCE} />
              </Field>
            </div>
          </Card>

          {/* Water & Emissions */}
          <Card title="Water & Emissions" subtitle="ICMM / Scope 1+2" className="border-blue-500/10">
            <div className="space-y-3">
              <Field label="Annual Water Withdrawal (m³)">
                <Input type="number" value={form.water_annual_withdrawal_m3} onChange={v => set("water_annual_withdrawal_m3", v)} />
              </Field>
              <Field label="Water Recycling Rate (%)" hint="Fraction of water recycled on-site">
                <Input type="number" value={form.water_recycling_rate * 100}
                  onChange={v => set("water_recycling_rate", v / 100)} min="0" max="100" step="1" />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Scope 1 (tCO₂e)">
                  <Input type="number" value={form.scope1_tco2e} onChange={v => set("scope1_tco2e", v)} />
                </Field>
                <Field label="Scope 2 (tCO₂e)">
                  <Input type="number" value={form.scope2_tco2e} onChange={v => set("scope2_tco2e", v)} />
                </Field>
              </div>
            </div>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4">
          <Field label="Climate Scenario">
            <Sel value={form.scenario} onChange={v => set("scenario", v)} options={SCENARIOS} />
          </Field>
          <Field label="Horizon Year">
            <Sel value={form.horizon_year} onChange={v => set("horizon_year", parseInt(v))} options={HORIZONS} />
          </Field>
        </div>

        <div className="mt-6 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-8 py-2.5 rounded-lg transition-colors">
            {loading ? "Analysing…" : "Run Mining Risk Assessment"}
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
                <p className="text-xs text-white/40 mb-1">Overall Mining Climate Risk</p>
                <p className={`text-2xl font-bold ${RISK_COLORS[result.overall_risk_category] || "text-white"}`}>
                  {result.overall_risk_category}
                </p>
                <p className="text-xs text-white/40 mt-1">Composite score: {fmt(result.overall_risk_score)}/100</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-white/40">Stranded Value at Risk</p>
                <p className="text-xl font-bold text-red-400">{fmtM(result.stranded_value_at_risk_usd)}</p>
                <p className="text-[11px] text-white/30">{fmt(result.stranded_asset_risk_pct, 1)}% stranding probability</p>
              </div>
            </div>
          </div>

          {/* KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Tailings Failure Prob."
              value={`${(result.tailings_annual_failure_prob * 1000).toFixed(3)}‰/yr`}
              color={result.tailings_annual_failure_prob > 0.001 ? "text-red-400" : "text-amber-400"}
              sub={`Expected loss: ${fmtM(result.tailings_expected_loss_usd)}`} />
            <StatCard label="Carbon Cost"
              value={fmtM(result.carbon_cost_usd)}
              color={result.carbon_cost_as_pct_revenue > 0.05 ? "text-red-400" : "text-amber-400"}
              sub={`${fmtPct(result.carbon_cost_as_pct_revenue)} of revenue`} />
            <StatCard label="Closure NPV Gap"
              value={fmtM(result.closure_underfunding_usd)}
              color={result.closure_underfunding_usd > 0 ? "text-red-400" : "text-emerald-400"}
              sub={`Closure cost: ${fmtM(result.closure_cost_usd)}`} />
            <StatCard label="Water Stress Score"
              value={fmt(result.water_stress_score, 2)}
              color={result.water_stress_score > 3 ? "text-red-400" : result.water_stress_score > 1.5 ? "text-amber-400" : "text-emerald-400"}
              sub={`Intensity: ${fmt(result.water_intensity_m3_per_kt)} m³/kt`} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {/* GISTM Compliance */}
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
              <p className="text-xs text-white/40 font-medium mb-2">GISTM Compliance</p>
              <div className={`inline-flex items-center px-3 py-1.5 rounded-lg border text-xs font-bold ${complianceFlagColor(result.tailings_compliance_flag)}`}>
                {result.tailings_compliance_flag}
              </div>
            </div>
            {/* Critical Minerals */}
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
              <p className="text-xs text-white/40 font-medium mb-1">Supply Concentration Risk</p>
              <p className={`text-sm font-bold ${concentrationColor(result.supply_concentration_risk)}`}>
                {result.supply_concentration_risk}
              </p>
              <p className="text-[11px] text-white/30 mt-1">HHI: {fmt(result.critical_mineral_hhi, 0)}</p>
            </div>
            {/* Transition Demand */}
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
              <p className="text-xs text-white/40 font-medium mb-1">Transition Demand Exposure</p>
              <p className="text-sm font-bold text-cyan-400">{result.transition_demand_exposure}</p>
              <p className="text-[11px] text-white/30 mt-1">IEA NZE EV/RE demand share</p>
            </div>
          </div>

          {/* Risk Breakdown Chart */}
          <Card title="Risk Dimension Breakdown" subtitle="Normalised 0–100 score per dimension">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={riskBreakdown} layout="vertical" barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => [`${v.toFixed(1)}/100`]} />
                <Bar dataKey="value" name="Risk Score" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Methodology */}
          <Card title="Methodology Reference">
            <div className="space-y-1 text-[11px] text-white/40">
              <p><span className="text-white/60 font-medium">GISTM Tailings:</span> Global Industry Standard on Tailings Management (2020) — consequence class maps to annual failure probability (EXTREME: 5×10⁻⁴, VERY HIGH: 10⁻³, HIGH: 2×10⁻³, LOW: 5×10⁻³). Compliance level adjustment: full −50%, partial ±0%, non_compliant +50%.</p>
              <p><span className="text-white/60 font-medium">Carbon Cost:</span> NGFS Phase 4 (2023) carbon price paths by scenario and year. Scope 1+2 tCO₂e × price = annual carbon cost liability.</p>
              <p><span className="text-white/60 font-medium">Closure Cost:</span> Engineering closure cost estimate × NPV discount to horizon. Underfunding = NPV of unfunded liability relative to book value.</p>
              <p><span className="text-white/60 font-medium">Critical Minerals:</span> IEA Critical Minerals 2023 — HHI supply concentration index per commodity. Transition demand exposure from EV/renewables technology demand share (IEA NZE 2050).</p>
              <p><span className="text-white/60 font-medium">Stranded Asset:</span> Reserve life vs implied regulatory phase-out timeline; residual book value NPV at risk. High scores for thermal coal in OECD regions.</p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
