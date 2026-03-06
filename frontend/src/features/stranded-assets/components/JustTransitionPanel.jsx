/**
 * Just Transition Calculator Panel
 * ILO Just Transition Guidelines · IRENA 2023 · World Bank JT Framework
 */
import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, ReferenceLine
} from "recharts";
import {
  Users, TrendingDown, TrendingUp, DollarSign, RefreshCw,
  AlertTriangle, CheckCircle, Info, Leaf
} from "lucide-react";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";
const fmtN = (v, d = 0) => v == null ? "—" : Number(v).toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtM = (v) => v == null ? "—" : `$${(v / 1e6).toFixed(1)}M`;

const FEASIBILITY_COLORS = {
  feasible: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  challenging: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  high_risk: "text-red-400 bg-red-500/10 border-red-500/20",
};

const DEFAULT_INPUT = {
  region_name: "Hunter Valley, Australia",
  country_income_group: "HIC",
  fossil_sector: "coal_mining",
  direct_fossil_jobs: 5000,
  transition_years: 10,
  planned_re_mw: 1500,
  re_technology: "solar_pv",
  planned_ee_mw_equiv: 200,
  planned_grid_mw: 500,
  planned_h2_mw: 0,
  income_support_years: 3,
  retraining_coverage_pct: 0.75,
  community_investment_included: true,
  community_dependency_pct: 0.6,
  just_transition_fund_usd: 0,
};

export function JustTransitionPanel() {
  const [form, setForm] = useState({ ...DEFAULT_INPUT });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const compute = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/just-transition/calculate`, form);
      setResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    setLoading(false);
  }, [form]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  return (
    <div className="space-y-6">
      {/* Methodology Note */}
      <div className="p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg text-xs text-amber-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>ILO Just Transition Guidelines (2015) · IRENA WETO 2023 employment multipliers · World Bank JT Framework social cost benchmarks. Employment multipliers include indirect and induced job effects across the local supply chain.</span>
      </div>

      {/* Input Form */}
      <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white/80 mb-4">Transition Region Parameters</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-white/40 block mb-1">Region Name</label>
            <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.region_name} onChange={e => set("region_name", e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Country Income Group</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.country_income_group} onChange={e => set("country_income_group", e.target.value)}>
              {["HIC", "UMC", "LMC", "LIC"].map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Fossil Sector</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.fossil_sector} onChange={e => set("fossil_sector", e.target.value)}>
              {["coal_mining", "oil_gas", "coal_power", "natural_gas_power", "refinery"].map(v => (
                <option key={v} value={v}>{v.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Direct Fossil Jobs</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.direct_fossil_jobs} onChange={e => set("direct_fossil_jobs", +e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Transition Period (years)</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.transition_years} onChange={e => set("transition_years", +e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Community Dependency (%)</label>
            <input type="number" step="0.05" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.community_dependency_pct} onChange={e => set("community_dependency_pct", +e.target.value)} />
          </div>
        </div>

        <h4 className="text-xs font-semibold text-white/50 mt-4 mb-3">Planned Green Investment</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-white/40 block mb-1">Renewable MW</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.planned_re_mw} onChange={e => set("planned_re_mw", +e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">RE Technology</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.re_technology} onChange={e => set("re_technology", e.target.value)}>
              {["solar_pv", "onshore_wind", "offshore_wind", "hydro", "geothermal"].map(v => (
                <option key={v} value={v}>{v.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">EE MW-Equivalent</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.planned_ee_mw_equiv} onChange={e => set("planned_ee_mw_equiv", +e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Green H2 MW (electrolyser)</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.planned_h2_mw} onChange={e => set("planned_h2_mw", +e.target.value)} />
          </div>
        </div>

        <h4 className="text-xs font-semibold text-white/50 mt-4 mb-3">Social Support Parameters</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-white/40 block mb-1">Income Support (years)</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.income_support_years} onChange={e => set("income_support_years", +e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Retraining Coverage (%)</label>
            <input type="number" step="0.05" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.retraining_coverage_pct} onChange={e => set("retraining_coverage_pct", +e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Existing JT Fund (USD)</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.just_transition_fund_usd} onChange={e => set("just_transition_fund_usd", +e.target.value)} />
          </div>
          <div className="flex items-center gap-3 mt-2">
            <label className="text-xs text-white/40">Include Community Investment</label>
            <input type="checkbox" checked={form.community_investment_included}
              onChange={e => set("community_investment_included", e.target.checked)} />
          </div>
        </div>

        <button onClick={compute} disabled={loading}
          className="mt-4 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium rounded-lg flex items-center gap-2">
          {loading ? <><RefreshCw className="h-3 w-3 animate-spin" /> Computing…</> : <><TrendingDown className="h-3 w-3" /> Compute Just Transition</>}
        </button>
        {error && <div className="mt-2 text-xs text-red-400">Error: {error}</div>}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Feasibility banner */}
          <div className={`p-3 border rounded-lg text-xs ${FEASIBILITY_COLORS[result.feasibility]}`}>
            <span className="font-bold uppercase">{result.feasibility.replace("_", " ")}</span>
            <span className="ml-3 opacity-80">{result.narrative}</span>
          </div>

          {/* KPI grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { icon: TrendingDown, label: "Total Displaced", val: fmtN(result.employment.total_displaced), color: "red" },
              { icon: Leaf, label: "Green Jobs Created", val: fmtN(result.employment.green_jobs_created), color: "green" },
              { icon: Users, label: "Net Employment Delta", val: (result.employment.net_delta >= 0 ? "+" : "") + fmtN(result.employment.net_delta), color: result.employment.net_delta >= 0 ? "green" : "red" },
              { icon: DollarSign, label: "Total JT Cost", val: fmtM(result.social_costs_usd.total), color: "amber" },
            ].map(({ icon: Icon, label, val, color }) => {
              const cls = {
                green: "bg-emerald-500/10 text-emerald-400", red: "bg-red-500/10 text-red-400",
                amber: "bg-amber-500/10 text-amber-400", blue: "bg-blue-500/10 text-blue-400",
              };
              return (
                <div key={label} className="bg-[#111827] border border-white/[0.06] rounded-lg p-3">
                  <div className={`inline-flex p-1.5 rounded mb-2 ${cls[color]}`}><Icon className="h-4 w-4" /></div>
                  <div className={`text-xl font-bold ${cls[color].split(" ")[1]}`}>{val}</div>
                  <div className="text-xs text-white/30 mt-1">{label}</div>
                </div>
              );
            })}
          </div>

          {/* Social cost breakdown */}
          <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
            <h3 className="text-sm font-semibold text-white/70 mb-3">Social Cost Breakdown</h3>
            <div className="grid grid-cols-3 gap-4 text-xs">
              {[
                ["Income Support", result.social_costs_usd.income_support, "text-blue-400"],
                ["Retraining", result.social_costs_usd.retraining, "text-indigo-400"],
                ["Community Investment", result.social_costs_usd.community_investment, "text-purple-400"],
              ].map(([label, val, cls]) => (
                <div key={label} className="text-center">
                  <div className={`text-lg font-bold ${cls}`}>{fmtM(val)}</div>
                  <div className="text-white/30 mt-1">{label}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-white/[0.06] flex justify-between text-xs">
              <span className="text-white/40">Cost per displaced worker</span>
              <span className="text-white/70 font-medium">${fmtN(result.financing.cost_per_worker_usd, 0)}</span>
            </div>
            {result.financing.fund_gap_usd > 0 && (
              <div className="mt-2 flex justify-between text-xs">
                <span className="text-red-400">Financing gap</span>
                <span className="text-red-400 font-medium">{fmtM(result.financing.fund_gap_usd)}</span>
              </div>
            )}
          </div>

          {/* Jobs Ramp Chart */}
          {result.annual_ramp?.length > 0 && (
            <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-3">Employment Transition Ramp</h3>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={result.annual_ramp} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                  <XAxis dataKey="year" tick={{ fontSize: 10, fill: "#ffffff40" }} />
                  <YAxis tick={{ fontSize: 10, fill: "#ffffff40" }} tickFormatter={v => (v / 1000).toFixed(0) + "k"} />
                  <Tooltip contentStyle={{ backgroundColor: "#1a2234", border: "1px solid #ffffff10", fontSize: 11 }}
                    formatter={(v, n) => [fmtN(v), n.replace(/_/g, " ")]} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="cumulative_displaced" stroke="#ef4444" strokeWidth={2} name="Displaced (cumulative)" dot={false} />
                  <Line type="monotone" dataKey="cumulative_green_created" stroke="#10b981" strokeWidth={2} name="Green Jobs (cumulative)" dot={false} />
                  <Line type="monotone" dataKey="net_gap" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 2" name="Jobs Gap" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
