/**
 * Green Hydrogen LCOH & Carbon Intensity Panel
 * IRENA Green Hydrogen Cost Reduction 2020
 * IEA Global Hydrogen Review 2023
 * EU Delegated Regulation 2023/1184 (RFNBO)
 * DOE Hydrogen Shot ($1/kg by 2031)
 */
import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, RadialBarChart, RadialBar,
} from "recharts";
import { Zap, Leaf, DollarSign, RefreshCw, Info, CheckCircle, XCircle, AlertTriangle } from "lucide-react";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";
const fmt2 = (v) => v == null ? "—" : Number(v).toFixed(2);
const fmt3 = (v) => v == null ? "—" : Number(v).toFixed(3);
const fmtK = (v) => v == null ? "—" : `${Number(v).toFixed(0)} kt/yr`;

const COLOUR_STYLES = {
  "Green": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  "Green (EU RFNBO)": "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
  "Pink": "bg-pink-500/10 text-pink-400 border-pink-500/20",
  "Blue": "bg-blue-500/10 text-blue-400 border-blue-500/20",
  "Light Blue": "bg-sky-500/10 text-sky-400 border-sky-500/20",
  "Turquoise": "bg-teal-500/10 text-teal-400 border-teal-500/20",
  "Grey": "bg-gray-500/10 text-gray-400 border-gray-500/20",
  "Brown/Black": "bg-amber-700/10 text-amber-700 border-amber-700/20",
  "Low-Carbon": "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  "Grey/High-Carbon Electrolysis": "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

const FEASIBILITY_STYLES = {
  competitive: { bg: "bg-emerald-500/5", border: "border-emerald-500/20", text: "text-emerald-300" },
  developing: { bg: "bg-blue-500/5", border: "border-blue-500/20", text: "text-blue-300" },
  transition: { bg: "bg-amber-500/5", border: "border-amber-500/20", text: "text-amber-300" },
  high_carbon: { bg: "bg-red-500/5", border: "border-red-500/20", text: "text-red-300" },
};

const DEFAULT_FORM = {
  project_name: "Green H2 — NEOM / ACWA Power",
  country: "Saudi Arabia",
  production_pathway: "PEM",
  capacity_mw_electrolyser: 100,
  capacity_factor_pct: 50,
  electricity_source: "dedicated_vre_ppa",
  electricity_price_usd_per_kwh: 0.030,
  electrolyser_capex_usd_per_kw: 800,
  electrolyser_opex_pct_capex: 3.0,
  stack_lifetime_years: 10,
  stack_replacement_cost_pct: 40,
  project_lifetime_years: 20,
  wacc_pct: 7.0,
  water_cost_usd_per_tonne: 3.5,
  water_consumption_l_per_kg_h2: 9.0,
  water_desalination_included: false,
  desalination_cost_usd_per_m3: 0.8,
  compression_storage_usd_per_kg: 0.30,
  transport_mode: "pipeline",
  transport_cost_usd_per_kg: 0.50,
  carbon_price_usd_per_tco2: 85,
  subsidy_usd_per_kg: 0.0,
  ira_45v_eligible: false,
  natural_gas_price_usd_per_mmbtu: 6.0,
  ccs_capex_usd_per_tco2: 80,
  ccs_capture_rate_pct: 90,
};

const PATHWAYS = ["PEM", "Alkaline", "SOEC", "AEM", "SMR_CCS", "SMR_Grey", "Coal_Gasification"];
const ELECTRICITY_SOURCES = [
  ["dedicated_vre_ppa", "Dedicated VRE PPA"],
  ["solar_pv_lcoe", "Solar PV (LCOE)"],
  ["onshore_wind", "Onshore Wind"],
  ["offshore_wind", "Offshore Wind"],
  ["nuclear", "Nuclear"],
  ["hydro", "Hydro"],
  ["grid_eu_avg", "EU Grid Average"],
  ["grid_us_avg", "US Grid Average"],
  ["grid_china", "China Grid Average"],
  ["grid_india", "India Grid Average"],
];

export function GreenHydrogenPanel() {
  const [form, setForm] = useState({ ...DEFAULT_FORM });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isElectrolysis = !["SMR_CCS", "SMR_Grey", "Coal_Gasification"].includes(form.production_pathway);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const compute = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/green-hydrogen/calculate`, form);
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  }, [form]);

  const colourStyle = result ? COLOUR_STYLES[result.colour] || "bg-white/5 text-white/60" : "";
  const fStyle = result ? FEASIBILITY_STYLES[result.feasibility] || FEASIBILITY_STYLES.developing : FEASIBILITY_STYLES.developing;

  // Chart data — LCOH waterfall
  const lcohData = result ? [
    { name: "Electricity", value: +result.lcoh.electricity.toFixed(3), fill: "#6366f1" },
    { name: "Electrolyser Capex", value: +result.lcoh.electrolyser_capex.toFixed(3), fill: "#3b82f6" },
    { name: "Opex", value: +result.lcoh.opex.toFixed(3), fill: "#8b5cf6" },
    { name: "Water", value: +result.lcoh.water.toFixed(3), fill: "#06b6d4" },
    { name: "Compression / Storage", value: +result.lcoh.compression_storage.toFixed(3), fill: "#f59e0b" },
    { name: "Transport", value: +result.lcoh.transport.toFixed(3), fill: "#f97316" },
    { name: "Stack Replacement", value: +result.lcoh.stack_replacement.toFixed(3), fill: "#ef4444" },
  ].filter(d => d.value > 0) : [];

  // Benchmark comparison
  const benchmarkData = result ? [
    { name: "This Project", value: +result.lcoh.after_subsidy.toFixed(2), fill: "#6366f1" },
    { name: "DOE 2031 Target", value: 1.0, fill: "#10b981" },
    { name: "Grey H2 (SMR)", value: 1.5, fill: "#6b7280" },
    { name: "Blue H2 (SMR+CCS)", value: 2.0, fill: "#3b82f6" },
    { name: "Green (MENA 2023)", value: 3.0, fill: "#f59e0b" },
    { name: "Green (Europe 2023)", value: 5.0, fill: "#f97316" },
  ] : [];

  const inputField = (key, label, type = "number", step = "0.1") => (
    <div key={key}>
      <label className="text-xs text-white/40 block mb-1">{label}</label>
      <input type={type} step={step}
        className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
        value={form[key]} onChange={e => set(key, type === "text" ? e.target.value : +e.target.value)} />
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Methodology note */}
      <div className="p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-lg text-xs text-emerald-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>
          LCOH model: IRENA Green Hydrogen Cost Reduction 2020 · IEA Global Hydrogen Review 2023 · EU RFNBO Delegated Reg. 2023/1184
          (threshold: 3.38 kg CO₂/kg H₂) · DOE Hydrogen Shot target: $1/kg by 2031.
          Colour classification per IPHE / IEA / Hydrogen Council convention.
        </span>
      </div>

      {/* Input form + Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Inputs */}
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-white/80">Project Parameters</h3>

          {inputField("project_name", "Project Name", "text")}
          {inputField("country", "Country", "text")}

          <div>
            <label className="text-xs text-white/40 block mb-1">Production Pathway</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.production_pathway} onChange={e => set("production_pathway", e.target.value)}>
              {PATHWAYS.map(p => <option key={p} value={p}>{p.replace(/_/g, " ")}</option>)}
            </select>
          </div>

          {inputField("capacity_mw_electrolyser", "Electrolyser Capacity (MW)", "number", "10")}
          {inputField("capacity_factor_pct", "Capacity Factor (%)", "number", "5")}

          {isElectrolysis && (
            <>
              <div>
                <label className="text-xs text-white/40 block mb-1">Electricity Source</label>
                <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                  value={form.electricity_source} onChange={e => set("electricity_source", e.target.value)}>
                  {ELECTRICITY_SOURCES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              {inputField("electricity_price_usd_per_kwh", "Electricity Price (USD/kWh)", "number", "0.005")}
              {inputField("electrolyser_capex_usd_per_kw", "Electrolyser Capex (USD/kW)", "number", "50")}
              {inputField("electrolyser_opex_pct_capex", "Opex (% of Capex p.a.)", "number", "0.5")}
            </>
          )}

          {!isElectrolysis && form.production_pathway !== "Coal_Gasification" && (
            <>
              {inputField("natural_gas_price_usd_per_mmbtu", "Natural Gas Price (USD/MMBtu)", "number", "0.5")}
              {form.production_pathway === "SMR_CCS" && inputField("ccs_capture_rate_pct", "CCS Capture Rate (%)", "number", "5")}
            </>
          )}

          <h4 className="text-xs font-semibold text-white/40 pt-2">Cost Additions</h4>
          {inputField("compression_storage_usd_per_kg", "Compression / Storage (USD/kg)", "number", "0.05")}
          {inputField("transport_cost_usd_per_kg", "Transport (USD/kg H₂)", "number", "0.1")}
          {inputField("carbon_price_usd_per_tco2", "Carbon Price (USD/tCO₂)", "number", "5")}
          {inputField("subsidy_usd_per_kg", "Government Subsidy (USD/kg)", "number", "0.1")}

          <div className="flex items-center gap-2">
            <input type="checkbox" id="ira_45v" checked={form.ira_45v_eligible}
              onChange={e => set("ira_45v_eligible", e.target.checked)}
              className="w-4 h-4 accent-emerald-500" />
            <label htmlFor="ira_45v" className="text-xs text-white/50">US IRA 45V Credit eligible</label>
          </div>

          <button onClick={compute} disabled={loading}
            className="mt-2 w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded-lg flex items-center justify-center gap-2">
            {loading
              ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Computing…</>
              : <><Zap className="h-3.5 w-3.5" /> Compute LCOH</>
            }
          </button>
          {error && <div className="text-xs text-red-400 mt-1">Error: {error}</div>}
        </div>

        {/* Live results */}
        {result && (
          <div className="space-y-3">
            {/* Colour + Feasibility banner */}
            <div className={`p-3 border rounded-lg text-xs ${fStyle.bg} ${fStyle.border} ${fStyle.text}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold border ${colourStyle}`}>
                  {result.colour} H₂
                </span>
                <span className="font-semibold uppercase">{result.feasibility.replace("_", " ")}</span>
              </div>
              <p>{result.narrative}</p>
            </div>

            {/* KPI cards */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "LCOH (after subsidy)", val: `$${fmt2(result.lcoh.after_subsidy)}/kg`, cls: result.lcoh.after_subsidy <= 2 ? "text-emerald-400" : result.lcoh.after_subsidy <= 4 ? "text-amber-400" : "text-red-400", sub: `Total: $${fmt2(result.lcoh.total)}/kg` },
                { label: "CO₂ Intensity", val: `${fmt3(result.carbon_intensity.kg_co2_per_kg_h2)} kgCO₂/kg`, cls: result.carbon_intensity.kg_co2_per_kg_h2 <= 0.5 ? "text-emerald-400" : result.carbon_intensity.kg_co2_per_kg_h2 <= 3.38 ? "text-amber-400" : "text-red-400", sub: `${result.carbon_intensity.gco2_per_mj} gCO₂/MJ` },
                { label: "Annual Production", val: fmtK(result.production.annual_production_kt), cls: "text-indigo-400", sub: `${(result.production.annual_production_t).toFixed(0)} t H₂/yr` },
                { label: "vs DOE 2031 Target", val: result.benchmarks.vs_doe_target_pct >= 0 ? `+${result.benchmarks.vs_doe_target_pct}%` : `${result.benchmarks.vs_doe_target_pct}%`, cls: result.benchmarks.vs_doe_target_pct <= 0 ? "text-emerald-400" : result.benchmarks.vs_doe_target_pct <= 100 ? "text-amber-400" : "text-red-400", sub: "vs $1/kg DOE target" },
              ].map(({ label, val, cls, sub }) => (
                <div key={label} className="bg-[#0d1424] border border-white/[0.06] rounded-lg p-3">
                  <div className={`text-xl font-bold ${cls}`}>{val}</div>
                  <div className="text-xs text-white/40 mt-0.5">{label}</div>
                  {sub && <div className="text-[11px] text-white/25 mt-0.5">{sub}</div>}
                </div>
              ))}
            </div>

            {/* Certification badges */}
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-lg p-3">
              <div className="text-xs font-semibold text-white/50 mb-2">Certification / Label Eligibility</div>
              <div className="flex flex-wrap gap-2">
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${result.certification.iea_green_eligible ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-white/5 text-white/30 border-white/10"}`}>
                  {result.certification.iea_green_eligible ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                  IEA Green (&lt;0.5 kgCO₂/kg)
                </span>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${result.certification.eu_rfnbo_eligible ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-white/5 text-white/30 border-white/10"}`}>
                  {result.certification.eu_rfnbo_eligible ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                  EU RFNBO (&lt;3.38 kgCO₂/kg)
                </span>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${result.certification.low_carbon_label ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" : "bg-white/5 text-white/30 border-white/10"}`}>
                  {result.certification.low_carbon_label ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                  Low-Carbon (&lt;4 kgCO₂/kg)
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Charts */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* LCOH Waterfall */}
          <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
            <h3 className="text-sm font-semibold text-white/70 mb-3">LCOH Breakdown (USD/kg H₂)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={lcohData} layout="vertical" margin={{ left: 60, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: "#ffffff40" }}
                  tickFormatter={v => `$${v.toFixed(2)}`} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#ffffff50" }} width={110} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1a2234", border: "1px solid #ffffff10", fontSize: 11 }}
                  formatter={v => [`$${Number(v).toFixed(3)}/kg`]} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {lcohData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="text-xs text-white/30 mt-2">
              Total LCOH: <span className="text-white/60 font-medium">${fmt2(result.lcoh.total)}/kg</span>
              {result.lcoh.after_subsidy !== result.lcoh.total && (
                <span> → After subsidy: <span className="text-emerald-400 font-medium">${fmt2(result.lcoh.after_subsidy)}/kg</span></span>
              )}
            </div>
          </div>

          {/* Benchmark comparison */}
          <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
            <h3 className="text-sm font-semibold text-white/70 mb-3">LCOH vs Industry Benchmarks (USD/kg)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={benchmarkData} margin={{ left: 0, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#ffffff40" }} angle={-20} textAnchor="end" height={40} />
                <YAxis tick={{ fontSize: 9, fill: "#ffffff40" }} tickFormatter={v => `$${v}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1a2234", border: "1px solid #ffffff10", fontSize: 11 }}
                  formatter={v => [`$${Number(v).toFixed(2)}/kg`]} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {benchmarkData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Carbon intensity + cost table */}
      {result && (
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4 text-xs">
          <h3 className="text-sm font-semibold text-white/70 mb-3">Carbon Analysis</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              ["CO₂ Intensity (kg/kg H₂)", `${fmt3(result.carbon_intensity.kg_co2_per_kg_h2)}`, result.carbon_intensity.kg_co2_per_kg_h2 <= 0.5 ? "text-emerald-400" : result.carbon_intensity.kg_co2_per_kg_h2 <= 3.38 ? "text-amber-400" : "text-red-400"],
              ["CO₂ Intensity (gCO₂/MJ)", `${result.carbon_intensity.gco2_per_mj}`, "text-white/60"],
              ["Embedded Carbon Cost (USD/kg)", `$${result.carbon_intensity.embedded_carbon_cost_usd_per_kg.toFixed(3)}`, "text-orange-400"],
              ["Abatement Cost vs Grey (USD/tCO₂)", result.carbon_intensity.abatement_cost_vs_grey_usd_per_tco2 != null ? `$${result.carbon_intensity.abatement_cost_vs_grey_usd_per_tco2}/t` : "N/A", result.carbon_intensity.abatement_cost_vs_grey_usd_per_tco2 < 100 ? "text-emerald-400" : "text-amber-400"],
            ].map(([label, val, cls]) => (
              <div key={label}>
                <div className="text-white/30">{label}</div>
                <div className={`text-base font-bold mt-1 ${cls}`}>{val}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Colour guide reference */}
      <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
        <h3 className="text-xs font-semibold text-white/40 mb-3 uppercase tracking-wide">H₂ Colour Classification Reference</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          {[
            ["Green", "Electrolysis + 100% certified RE", "< 0.5 kgCO₂/kg (IEA)"],
            ["Green (EU RFNBO)", "Electrolysis + RE (EU definition)", "< 3.38 kgCO₂/kg"],
            ["Pink", "Electrolysis + nuclear", "~ 0.01 kgCO₂/kg"],
            ["Blue", "SMR + CCS (≥85% capture)", "1.4–2.5 kgCO₂/kg"],
            ["Turquoise", "Methane pyrolysis", "< 1 kgCO₂/kg"],
            ["Grey", "SMR without CCS", "9–12 kgCO₂/kg"],
            ["Brown/Black", "Coal gasification", "18–22 kgCO₂/kg"],
            ["Low-Carbon", "Below 4 kg threshold", "< 4 kgCO₂/kg"],
          ].map(([colour, pathway, threshold]) => (
            <div key={colour} className={`p-2 rounded border text-[11px] ${COLOUR_STYLES[colour] || "bg-white/5 text-white/40 border-white/10"}`}>
              <div className="font-bold mb-0.5">{colour}</div>
              <div className="opacity-70">{pathway}</div>
              <div className="opacity-50 mt-0.5 font-mono">{threshold}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
