/**
 * Energy Transition Mechanism (ETM) Calculator Panel
 * ADB/AIIB/Citi ETM Framework 2022 — Early coal retirement via blended finance
 */
import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from "recharts";
import { Zap, DollarSign, Leaf, AlertTriangle, RefreshCw, Info, TrendingDown } from "lucide-react";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";
const fmtM = (v, d = 1) => v == null ? "—" : `$${Number(v).toFixed(d)}M`;
const fmtN = (v, d = 0) => v == null ? "—" : Number(v).toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });

const FEASIBILITY_STYLE = {
  viable: { bg: "bg-emerald-500/10", border: "border-emerald-500/20", text: "text-emerald-400" },
  marginal: { bg: "bg-amber-500/10", border: "border-amber-500/20", text: "text-amber-400" },
  unviable: { bg: "bg-red-500/10", border: "border-red-500/20", text: "text-red-400" },
};

const DEFAULT_INPUT = {
  plant_name: "Hazelwood Power Station",
  plant_country: "Australia",
  capacity_mw: 1600,
  remaining_useful_life_years: 15,
  early_retirement_year: 2030,
  current_year: 2024,
  outstanding_debt_usd_m: 800,
  equity_book_value_usd_m: 200,
  offtake_tariff_usd_per_mwh: 65,
  capacity_factor_pct: 60,
  incumbent_wacc_pct: 12,
  etm_refinance_rate_pct: 4.5,
  etm_tranche_pct: 0.6,
  re_replacement_mw: 2000,
  re_capex_usd_per_mw: 800000,
  re_lcoe_usd_per_mwh: 35,
};

export function ETMPanel() {
  const [form, setForm] = useState({ ...DEFAULT_INPUT });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const compute = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/just-transition/etm/calculate`, form);
      setResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    setLoading(false);
  }, [form]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const inputField = (key, label, type = "number", step = "1") => (
    <div key={key}>
      <label className="text-xs text-white/40 block mb-1">{label}</label>
      <input type={type} step={step} className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
        value={form[key]} onChange={e => set(key, type === "text" ? e.target.value : +e.target.value)} />
    </div>
  );

  const packageData = result ? [
    { name: "Debt Buyout", value: result.etm_package_usd_m.debt_buyout, fill: "#6366f1" },
    { name: "Equity Comp", value: result.etm_package_usd_m.equity_compensation, fill: "#8b5cf6" },
    { name: "RE Capex", value: result.etm_package_usd_m.re_replacement_capex, fill: "#10b981" },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Methodology Note */}
      <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-lg text-xs text-indigo-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>ADB/AIIB/Citi Energy Transition Mechanism (ETM) Framework 2022. The ETM SPV purchases outstanding coal plant debt at concessional rates, enabling early retirement. Abatement cost benchmarked against $80/tCO₂ social cost of carbon (World Bank 2023).</span>
      </div>

      {/* Input Form */}
      <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white/80 mb-4">Coal Plant Parameters</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {inputField("plant_name", "Plant Name", "text")}
          {inputField("plant_country", "Country", "text")}
          {inputField("capacity_mw", "Capacity (MW)")}
          {inputField("remaining_useful_life_years", "Remaining Life (years)")}
          {inputField("early_retirement_year", "Target Retirement Year")}
          {inputField("capacity_factor_pct", "Capacity Factor (%)")}
        </div>

        <h4 className="text-xs font-semibold text-white/50 mt-4 mb-3">Financial Structure</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {inputField("outstanding_debt_usd_m", "Outstanding Debt (M USD)")}
          {inputField("equity_book_value_usd_m", "Equity Book Value (M USD)")}
          {inputField("offtake_tariff_usd_per_mwh", "Offtake Tariff (USD/MWh)")}
          {inputField("incumbent_wacc_pct", "Incumbent WACC (%)", "number", "0.5")}
          {inputField("etm_refinance_rate_pct", "ETM Concessional Rate (%)", "number", "0.5")}
          {inputField("etm_tranche_pct", "ETM Debt Tranche (%)", "number", "0.1")}
        </div>

        <h4 className="text-xs font-semibold text-white/50 mt-4 mb-3">RE Replacement</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {inputField("re_replacement_mw", "RE Replacement (MW)")}
          {inputField("re_capex_usd_per_mw", "RE Capex (USD/MW)")}
          {inputField("re_lcoe_usd_per_mwh", "RE LCOE (USD/MWh)")}
        </div>

        <button onClick={compute} disabled={loading}
          className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg flex items-center gap-2">
          {loading ? <><RefreshCw className="h-3 w-3 animate-spin" /> Computing…</> : <><Zap className="h-3 w-3" /> Compute ETM Package</>}
        </button>
        {error && <div className="mt-2 text-xs text-red-400">Error: {error}</div>}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Feasibility banner */}
          {(() => {
            const s = FEASIBILITY_STYLE[result.feasibility] || FEASIBILITY_STYLE.marginal;
            return (
              <div className={`p-3 border rounded-lg text-xs ${s.bg} ${s.border} ${s.text}`}>
                <span className="font-bold uppercase">{result.feasibility}</span>
                <span className="ml-3 opacity-80">{result.narrative}</span>
              </div>
            );
          })()}

          {/* KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Years Early Retirement", val: result.years_early_retirement + " yrs", color: "indigo" },
              { label: "Stranded NPV", val: fmtM(result.stranded_value?.npv_lost_usd_m), color: "red" },
              { label: "Total ETM Cost", val: fmtM(result.etm_package_usd_m?.total), color: "blue" },
              { label: "Avoided CO₂", val: fmtN(result.climate_impact?.avoided_co2_mt, 2) + " Mt", color: "green" },
            ].map(({ label, val, color }) => {
              const clsMap = {
                indigo: "text-indigo-400", red: "text-red-400",
                blue: "text-blue-400", green: "text-emerald-400",
              };
              return (
                <div key={label} className="bg-[#111827] border border-white/[0.06] rounded-lg p-3 text-center">
                  <div className={`text-xl font-bold ${clsMap[color]}`}>{val}</div>
                  <div className="text-xs text-white/30 mt-1">{label}</div>
                </div>
              );
            })}
          </div>

          {/* Package breakdown + Climate */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* ETM Package Waterfall */}
            <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-3">ETM Package Breakdown (M USD)</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={packageData} layout="vertical" margin={{ left: 60, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 10, fill: "#ffffff40" }} tickFormatter={v => `$${v}M`} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#ffffff50" }} width={80} />
                  <Tooltip contentStyle={{ backgroundColor: "#1a2234", border: "1px solid #ffffff10", fontSize: 11 }}
                    formatter={v => [`$${Number(v).toFixed(1)}M`]} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {packageData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Climate Metrics */}
            <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-4">Climate Impact Metrics</h3>
              <div className="space-y-3 text-xs">
                {[
                  ["Avoided CO₂", `${fmtN(result.climate_impact?.avoided_co2_mt, 3)} Mt`, "text-emerald-400"],
                  ["Abatement Cost", `$${fmtN(result.climate_impact?.abatement_cost_usd_per_tco2, 0)}/tCO₂`, result.climate_impact?.abatement_cost_usd_per_tco2 < 80 ? "text-emerald-400" : result.climate_impact?.abatement_cost_usd_per_tco2 < 150 ? "text-amber-400" : "text-red-400"],
                  ["WB SCC Benchmark", "$80/tCO₂", "text-white/40"],
                  ["NPV Saving (vs natural)", fmtM(result.climate_impact?.npv_saving_vs_natural_retirement_usd_m), result.climate_impact?.npv_saving_vs_natural_retirement_usd_m > 0 ? "text-emerald-400" : "text-red-400"],
                  ["Concessional Savings", fmtM(result.etm_package_usd_m?.concessional_savings), "text-indigo-400"],
                ].map(([label, val, cls]) => (
                  <div key={label} className="flex justify-between items-center border-b border-white/[0.04] pb-2">
                    <span className="text-white/40">{label}</span>
                    <span className={`font-medium ${cls}`}>{val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
