/**
 * Financial Risk Assessment Page
 * IFRS 9 ECL with Climate Overlay + PCAF Financed Emissions + WACI
 *
 * Standards: EBA GL/2022/16, IFRS 9, PCAF Standard v2.0, SFDR PAI 1-5
 */
import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, LineChart, Line, PieChart, Pie
} from "recharts";
import {
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Shield,
  DollarSign, Leaf, Activity, ChevronDown, ChevronUp, RefreshCw,
  Plus, Trash2, Info, BarChart2, Zap
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt = (v, d = 2) => v == null ? "—" : new Intl.NumberFormat("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
const fmtCcy = (v, ccy = "GBP") => {
  if (v == null) return "—";
  const s = { GBP: "£", USD: "$", EUR: "€" }[ccy] || ccy;
  if (Math.abs(v) >= 1e9) return `${s}${fmt(v / 1e9, 2)}bn`;
  if (Math.abs(v) >= 1e6) return `${s}${fmt(v / 1e6, 2)}m`;
  if (Math.abs(v) >= 1e3) return `${s}${fmt(v / 1e3, 1)}k`;
  return `${s}${fmt(v, 0)}`;
};

const SCENARIO_COLORS = { optimistic: "#10b981", base: "#6366f1", adverse: "#f59e0b", severe: "#ef4444" };
const STAGE_COLORS = { stage1: "#10b981", stage2: "#f59e0b", stage3: "#ef4444" };

const DEFAULT_EXPOSURE = {
  instrument_id: "EXP-001", asset_type: "corporate_loan", sector: "power_generation",
  epc_rating: "D", country_iso: "GB", exposure_ead: 10000000,
  base_pd_pct: 2.0, base_lgd_pct: 40.0, maturity_years: 5,
  current_stage: 1, sector_transition_risk: "medium",
  physical_risk_score: 30.0, flood_risk: "low",
};

function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-white/[0.06] rounded-lg overflow-hidden mb-4 bg-[#0d1424]">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-[#0d1424]/[0.02] hover:bg-[#0d1424]/[0.04] transition-colors">
        <span className="font-medium text-sm text-white/70">{title}</span>
        {open ? <ChevronUp className="h-4 w-4 text-white/30" /> : <ChevronDown className="h-4 w-4 text-white/30" />}
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
}

// ── ECL Climate Assessment Panel ──────────────────────────────────────────
function ECLPanel() {
  const [exposures, setExposures] = useState([{ ...DEFAULT_EXPOSURE }]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("inputs");

  const handleChange = (idx, key, value) => {
    setExposures(prev => prev.map((e, i) => i === idx ? { ...e, [key]: value } : e));
  };

  const addExposure = () => setExposures(prev => [...prev, { ...DEFAULT_EXPOSURE, instrument_id: `EXP-${String(prev.length + 1).padStart(3, "0")}` }]);
  const removeExposure = (idx) => setExposures(prev => prev.filter((_, i) => i !== idx));

  const runECL = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const payload = {
        exposures: exposures.map(e => ({
          ...e,
          exposure_ead: parseFloat(e.exposure_ead) || 0,
          base_pd_pct: parseFloat(e.base_pd_pct) || 0,
          base_lgd_pct: parseFloat(e.base_lgd_pct) || 0,
          maturity_years: parseInt(e.maturity_years) || 5,
          current_stage: parseInt(e.current_stage) || 1,
          physical_risk_score: parseFloat(e.physical_risk_score) || 0,
        })),
      };
      const res = await axios.post(`${API_BASE}/api/v1/ecl/portfolio-ecl`, payload);
      setResult(res.data);
      setActiveTab("results");
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const stageData = result ? [
    { name: "Stage 1", count: result.stage_breakdown?.stage1_count || 0, ecl: result.stage_breakdown?.stage1_ecl || 0, fill: STAGE_COLORS.stage1 },
    { name: "Stage 2", count: result.stage_breakdown?.stage2_count || 0, ecl: result.stage_breakdown?.stage2_ecl || 0, fill: STAGE_COLORS.stage2 },
    { name: "Stage 3", count: result.stage_breakdown?.stage3_count || 0, ecl: result.stage_breakdown?.stage3_ecl || 0, fill: STAGE_COLORS.stage3 },
  ] : [];

  return (
    <div>
      <div className="flex gap-1 border-b border-white/[0.06] mb-4">
        {[["inputs","Inputs"],["results","Results"]].map(([id,l]) => (
          <button key={id} onClick={() => !(!result && id === "results") && setActiveTab(id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 ${activeTab === id ? "border-cyan-400 text-cyan-400" : "border-transparent text-white/30 hover:text-white/60"}`}>
            {l}
          </button>
        ))}
      </div>

      {activeTab === "inputs" && (
        <div className="space-y-4">
          {exposures.map((exp, idx) => (
            <div key={idx} className="border border-white/[0.06] rounded-lg p-4">
              <div className="flex justify-between items-center mb-3">
                <span className="font-medium text-sm text-white/70">Exposure {idx + 1}: {exp.instrument_id}</span>
                {exposures.length > 1 && (
                  <button onClick={() => removeExposure(idx)} className="text-red-400 hover:text-red-600">
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                {[
                  { k: "instrument_id", l: "ID", type: "text" },
                  { k: "asset_type", l: "Asset Type", type: "select", opts: ["corporate_loan","mortgage","sovereign","project_finance","leveraged_loan","revolving_credit","infrastructure"] },
                  { k: "sector", l: "Sector", type: "select", opts: ["power_generation","oil_gas","steel","automotive","airlines","real_estate","agriculture","technology","finance","utilities","mining"] },
                  { k: "country_iso", l: "Country", type: "select", opts: ["GB","US","DE","FR","NL","AU"] },
                  { k: "exposure_ead", l: "EAD (£)", type: "number" },
                  { k: "base_pd_pct", l: "Base PD (%)", type: "number" },
                  { k: "base_lgd_pct", l: "Base LGD (%)", type: "number" },
                  { k: "maturity_years", l: "Maturity (yrs)", type: "number" },
                  { k: "current_stage", l: "IFRS 9 Stage", type: "select", opts: ["1","2","3"] },
                  { k: "sector_transition_risk", l: "Transition Risk", type: "select", opts: ["very_low","low","medium","high","very_high"] },
                  { k: "epc_rating", l: "EPC Rating", type: "select", opts: ["A","B","C","D","E","F","G"] },
                  { k: "physical_risk_score", l: "Physical Risk (0-100)", type: "number" },
                ].map(f => (
                  <div key={f.k}>
                    <label className="block text-xs text-white/40 mb-1">{f.l}</label>
                    {f.type === "select" ? (
                      <select value={exp[f.k] ?? ""} onChange={e => handleChange(idx, f.k, e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-white/[0.06] rounded bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50">
                        {f.opts.map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ) : (
                      <input type={f.type} value={exp[f.k] ?? ""} onChange={e => handleChange(idx, f.k, e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-white/[0.06] rounded bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
          <div className="flex gap-3">
            <button onClick={addExposure} className="flex items-center gap-1.5 px-3 py-1.5 border border-dashed border-white/[0.08] text-white/40 text-sm rounded-lg hover:bg-white/[0.02]">
              <Plus className="h-4 w-4" /> Add Exposure
            </button>
            <button onClick={runECL} disabled={loading}
              className="flex items-center gap-2 px-4 py-1.5 bg-cyan-400 hover:bg-cyan-300 disabled:bg-cyan-400/40 text-[#080e1c] text-white text-sm font-semibold rounded-lg">
              {loading ? <><RefreshCw className="h-4 w-4 animate-spin" />Running…</> : <><Activity className="h-4 w-4" />Run ECL Model</>}
            </button>
          </div>
          {error && <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-600"><AlertTriangle className="h-3 w-3 inline mr-1" />{error}</div>}
        </div>
      )}

      {activeTab === "results" && result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { l: "Total EAD", v: fmtCcy(result.total_ead, "GBP"), icon: DollarSign, color: "text-blue-600" },
              { l: "Baseline ECL", v: fmtCcy(result.baseline_ecl, "GBP"), icon: TrendingDown, color: "text-white/60" },
              { l: "Climate ECL", v: fmtCcy(result.probability_weighted_ecl, "GBP"), icon: AlertTriangle, color: "text-red-500" },
              { l: "Climate Uplift", v: `+${fmt(result.climate_uplift_pct, 1)}%`, icon: TrendingUp, color: "text-orange-500" },
            ].map(m => {
              const Icon = m.icon;
              return (
                <div key={m.l} className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`h-4 w-4 ${m.color}`} />
                    <span className="text-xs text-white/40">{m.l}</span>
                  </div>
                  <div className="text-xl font-bold text-white/90">{m.v}</div>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Stage breakdown */}
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
              <h4 className="text-sm font-semibold text-white/70 mb-3">IFRS 9 Stage Distribution</h4>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={stageData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={v => fmtCcy(v, "GBP")} width={65} />
                  <Tooltip formatter={v => fmtCcy(v, "GBP")} />
                  <Bar dataKey="ecl" name="ECL" radius={[4,4,0,0]}>
                    {stageData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Scenario distribution */}
            {result.scenario_ecl && (
              <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
                <h4 className="text-sm font-semibold text-white/70 mb-3">ECL by Climate Scenario</h4>
                <div className="space-y-3">
                  {Object.entries(result.scenario_ecl).map(([sc, val]) => (
                    <div key={sc}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="capitalize text-white/60">{sc}</span>
                        <span className="font-medium">{fmtCcy(val, "GBP")}</span>
                      </div>
                      <div className="w-full bg-white/[0.06] rounded-full h-2">
                        <div className="h-2 rounded-full transition-all"
                          style={{ width: `${Math.min((val / (result.probability_weighted_ecl || 1)) * 70, 100)}%`, backgroundColor: SCENARIO_COLORS[sc] || "#6366f1" }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Individual results */}
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-white/[0.02] border-b border-white/[0.06]">
              <h4 className="text-sm font-semibold text-white/70">Exposure-Level Results</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-white/[0.02] border-b border-white/[0.06]">
                    {["ID","Sector","Stage","EAD","Base ECL","Climate ECL","Uplift%","SICR"].map(h => (
                      <th key={h} className="text-left px-3 py-2 text-xs font-medium text-white/40">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(result.exposure_results || []).map((r, i) => (
                    <tr key={i} className="hover:bg-white/[0.02]">
                      <td className="px-3 py-2 text-xs text-white/60">{r.instrument_id}</td>
                      <td className="px-3 py-2 text-xs text-white/60 capitalize">{r.sector}</td>
                      <td className="px-3 py-2">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                          r.final_stage === 3 ? "bg-red-100 text-red-700" :
                          r.final_stage === 2 ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"
                        }`}>S{r.final_stage}</span>
                      </td>
                      <td className="px-3 py-2 text-xs font-medium">{fmtCcy(r.ead, "GBP")}</td>
                      <td className="px-3 py-2 text-xs">{fmtCcy(r.baseline_ecl, "GBP")}</td>
                      <td className="px-3 py-2 text-xs font-semibold text-red-600">{fmtCcy(r.climate_weighted_ecl, "GBP")}</td>
                      <td className="px-3 py-2 text-xs text-orange-600">+{fmt(r.climate_uplift_pct, 1)}%</td>
                      <td className="px-3 py-2">
                        {r.sicr_triggered ?
                          <span className="text-xs bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded font-medium">SICR</span> :
                          <span className="text-xs text-white/30">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── PCAF / WACI Panel ─────────────────────────────────────────────────────
function PCaFPanel() {
  const [investees, setInvestees] = useState([
    { company_name: "Tech Corp A", asset_class: "listed_equity", evic_eur: 5000000, investment_value_eur: 500000, scope1_tco2e: 1200, scope2_tco2e: 800, scope3_tco2e: 3000, revenue_eur: 8000000, sector: "technology" },
    { company_name: "Industrial B", asset_class: "corporate_bonds", evic_eur: 2000000, investment_value_eur: 200000, scope1_tco2e: 15000, scope2_tco2e: 5000, scope3_tco2e: 20000, revenue_eur: 3000000, sector: "steel" },
  ]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (idx, key, value) => setInvestees(p => p.map((e, i) => i === idx ? { ...e, [key]: value } : e));
  const addInvestee = () => setInvestees(p => [...p, { company_name: `Investee ${p.length + 1}`, asset_class: "corporate_bonds", evic_eur: 0, investment_value_eur: 0, scope1_tco2e: 0, scope2_tco2e: 0, scope3_tco2e: 0, revenue_eur: 0, sector: "other" }]);
  const removeInvestee = (idx) => setInvestees(p => p.filter((_, i) => i !== idx));

  const runPCAF = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const payload = {
        portfolio_name: "My Portfolio",
        investees: investees.map(e => ({
          ...e,
          evic_eur: parseFloat(e.evic_eur) || 0,
          investment_value_eur: parseFloat(e.investment_value_eur) || 0,
          scope1_tco2e: parseFloat(e.scope1_tco2e) || 0,
          scope2_tco2e: parseFloat(e.scope2_tco2e) || 0,
          scope3_tco2e: parseFloat(e.scope3_tco2e) || 0,
          revenue_eur: parseFloat(e.revenue_eur) || 0,
        })),
      };
      const res = await axios.post(`${API_BASE}/api/v1/pcaf/portfolio-emissions`, payload);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-xs text-blue-700">
        <Info className="h-3.5 w-3.5 inline mr-1" />
        PCAF Standard v2.0 — Attribution factor = Investment Value ÷ EVIC (Equity/Bonds) or Book Value ÷ Outstanding (Loans).
        WACI = Weighted Average Carbon Intensity (tCO₂e / EUR M revenue).
      </div>

      {investees.map((inv, idx) => (
        <div key={idx} className="border border-white/[0.06] rounded-lg p-4">
          <div className="flex justify-between mb-3">
            <span className="font-medium text-sm text-white/70">{inv.company_name}</span>
            {investees.length > 1 && <button onClick={() => removeInvestee(idx)} className="text-red-400 hover:text-red-600"><Trash2 className="h-4 w-4" /></button>}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {[
              { k: "company_name", l: "Company Name", type: "text" },
              { k: "asset_class", l: "Asset Class", type: "select", opts: ["listed_equity","corporate_bonds","business_loans","project_finance","commercial_real_estate","mortgages","sovereign_bonds"] },
              { k: "sector", l: "Sector (GICS)", type: "select", opts: ["energy","utilities","materials","industrials","consumer_discretionary","consumer_staples","healthcare","financials","information_technology","communication","real_estate","steel","automotive","airlines","other"] },
              { k: "evic_eur", l: "EVIC (€)", type: "number" },
              { k: "investment_value_eur", l: "Investment Value (€)", type: "number" },
              { k: "scope1_tco2e", l: "Scope 1 (tCO₂e)", type: "number" },
              { k: "scope2_tco2e", l: "Scope 2 (tCO₂e)", type: "number" },
              { k: "scope3_tco2e", l: "Scope 3 (tCO₂e)", type: "number" },
              { k: "revenue_eur", l: "Revenue (€)", type: "number" },
            ].map(f => (
              <div key={f.k}>
                <label className="block text-xs text-white/40 mb-1">{f.l}</label>
                {f.type === "select" ? (
                  <select value={inv[f.k] ?? ""} onChange={e => handleChange(idx, f.k, e.target.value)}
                    className="w-full px-2 py-1.5 text-sm border border-white/[0.06] rounded bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50">
                    {f.opts.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                ) : (
                  <input type={f.type} value={inv[f.k] ?? ""} onChange={e => handleChange(idx, f.k, e.target.value)}
                    className="w-full px-2 py-1.5 text-sm border border-white/[0.06] rounded bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50" />
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="flex gap-3">
        <button onClick={addInvestee} className="flex items-center gap-1.5 px-3 py-1.5 border border-dashed border-white/[0.08] text-white/40 text-sm rounded-lg hover:bg-white/[0.02]">
          <Plus className="h-4 w-4" /> Add Investee
        </button>
        <button onClick={runPCAF} disabled={loading}
          className="flex items-center gap-2 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white text-sm font-semibold rounded-lg">
          {loading ? <><RefreshCw className="h-4 w-4 animate-spin" />Running…</> : <><Leaf className="h-4 w-4" />Calculate PCAF / WACI</>}
        </button>
      </div>

      {error && <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-600">{error}</div>}

      {result && (
        <div className="space-y-4 mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { l: "Total Financed Emissions", v: `${fmt(result.total_financed_emissions_tco2e / 1000, 1)}k tCO₂e`, color: "text-emerald-600" },
              { l: "WACI", v: `${fmt(result.waci_tco2e_per_eur_m, 1)} t/€M`, color: "text-blue-600" },
              { l: "Temperature Score", v: `${fmt(result.implied_temperature_score_c, 2)}°C`, color: result.implied_temperature_score_c < 2 ? "text-emerald-600" : "text-red-500" },
              { l: "SFDR PAI 1 Coverage", v: `${fmt(result.pai_metrics?.pai_1_coverage_pct, 0)}%`, color: "text-cyan-400" },
            ].map(m => (
              <div key={m.l} className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
                <div className="text-xs text-white/40 mb-1">{m.l}</div>
                <div className={`text-xl font-bold ${m.color}`}>{m.v}</div>
              </div>
            ))}
          </div>
          {result.investee_results && (
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl overflow-hidden">
              <div className="px-4 py-3 bg-white/[0.02] border-b border-white/[0.06] text-sm font-semibold text-white/70">Investee Attribution</div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-white/[0.02] border-b border-white/[0.06]">
                      {["Company","Asset Class","Attribution","Financed Emissions","WACI","Data Quality"].map(h => (
                        <th key={h} className="text-left px-3 py-2 text-xs font-medium text-white/40">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.investee_results.map((r, i) => (
                      <tr key={i} className="hover:bg-white/[0.02]">
                        <td className="px-3 py-2 text-xs font-medium text-white/70">{r.company_name}</td>
                        <td className="px-3 py-2 text-xs text-white/40">{r.asset_class}</td>
                        <td className="px-3 py-2 text-xs">{fmt(r.attribution_factor * 100, 2)}%</td>
                        <td className="px-3 py-2 text-xs font-medium text-emerald-600">{fmt(r.financed_emissions_tco2e, 0)} t</td>
                        <td className="px-3 py-2 text-xs">{fmt(r.waci_contribution_tco2e_eur_m, 1)}</td>
                        <td className="px-3 py-2 text-xs text-white/30">Score {r.pcaf_data_quality_score}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Facilitated Emissions Panel (PCAF Capital Markets — Part C) ──────────
function FacilitatedEmissionsPanel() {
  const [form, setForm] = useState({
    issuer_name: "Green Bond Corp Ltd", instrument_type: "bond",
    transaction_type: "underwriting", underwritten_amount_musd: 50,
    total_issuance_amount_musd: 300, shares_placed_value_musd: "",
    market_cap_musd: "", issuer_scope1_tco2e: 120000,
    issuer_scope2_tco2e: 45000, issuer_scope3_tco2e: "",
    include_scope3: false, data_source_type: "self_reported",
    sector_gics: "Utilities", country_iso2: "GB",
    reporting_year: 2024, green_bond: false,
  });
  const [result, setResult] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sumLoading, setSumLoading] = useState(false);
  const [error, setError] = useState(null);

  const DQS_COLORS = { 1: "text-emerald-500", 2: "text-emerald-400", 3: "text-amber-400", 4: "text-orange-400", 5: "text-red-500" };

  const loadSummary = useCallback(async () => {
    setSumLoading(true);
    try {
      const { data } = await axios.get(`${API_BASE}/api/v1/facilitated-emissions/summary`);
      setSummary(data);
    } catch (e) { /* tolerate empty */ }
    setSumLoading(false);
  }, []);

  const handleCompute = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const payload = { ...form };
      if (payload.instrument_type !== "equity") {
        delete payload.shares_placed_value_musd; delete payload.market_cap_musd;
      } else {
        delete payload.underwritten_amount_musd; delete payload.total_issuance_amount_musd;
      }
      if (!payload.include_scope3) delete payload.issuer_scope3_tco2e;
      Object.keys(payload).forEach(k => payload[k] === "" && delete payload[k]);
      const { data } = await axios.post(`${API_BASE}/api/v1/facilitated-emissions/`, payload);
      setResult(data);
      loadSummary();
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    setLoading(false);
  };

  React.useEffect(() => { loadSummary(); }, [loadSummary]);

  const isEquity = form.instrument_type === "equity";

  return (
    <div className="space-y-6">
      {/* Methodology note */}
      <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-lg text-xs text-indigo-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>PCAF Capital Markets (Part C, 2022). Attribution factor = (underwritten / total issuance) × &#189; for debt; (shares placed / market cap) × &#189; for equity. The &#247;3 factor reflects time-in-year attribution.</span>
      </div>

      {/* Portfolio Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Transactions", val: summary.totals.transaction_count, unit: "" },
            { label: "Total Facilitated", val: fmt(summary.totals.total_facilitated_tco2e / 1000, 1), unit: "kt CO₂e" },
            { label: "Underwritten", val: fmt(summary.totals.total_underwritten_musd, 0), unit: "M USD" },
            { label: "Avg PCAF DQS", val: fmt(summary.totals.avg_pcaf_dqs, 1), unit: "/5" },
          ].map(({ label, val, unit }) => (
            <div key={label} className="bg-[#111827] border border-white/[0.06] rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-white">{val}<span className="text-xs text-white/40 ml-1">{unit}</span></div>
              <div className="text-xs text-white/40 mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Entry Form */}
      <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white/80 mb-4">New Deal Entry</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-white/40 block mb-1">Issuer Name</label>
            <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.issuer_name} onChange={e => setForm(f => ({ ...f, issuer_name: e.target.value }))} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Instrument Type</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.instrument_type} onChange={e => setForm(f => ({ ...f, instrument_type: e.target.value }))}>
              <option value="bond">Bond</option>
              <option value="equity">Equity</option>
              <option value="convertible">Convertible</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Data Source Type</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.data_source_type} onChange={e => setForm(f => ({ ...f, data_source_type: e.target.value }))}>
              {["self_reported","audited_report","direct_measurement","sector_average","estimated"].map(v => (
                <option key={v} value={v}>{v.replace(/_/g," ")}</option>
              ))}
            </select>
          </div>
          {!isEquity && <>
            <div>
              <label className="text-xs text-white/40 block mb-1">Underwritten Amount (M USD)</label>
              <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={form.underwritten_amount_musd} onChange={e => setForm(f => ({ ...f, underwritten_amount_musd: +e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Total Issuance (M USD)</label>
              <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={form.total_issuance_amount_musd} onChange={e => setForm(f => ({ ...f, total_issuance_amount_musd: +e.target.value }))} />
            </div>
          </>}
          {isEquity && <>
            <div>
              <label className="text-xs text-white/40 block mb-1">Shares Placed Value (M USD)</label>
              <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={form.shares_placed_value_musd} onChange={e => setForm(f => ({ ...f, shares_placed_value_musd: +e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Market Cap (M USD)</label>
              <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={form.market_cap_musd} onChange={e => setForm(f => ({ ...f, market_cap_musd: +e.target.value }))} />
            </div>
          </>}
          <div>
            <label className="text-xs text-white/40 block mb-1">Issuer Scope 1 (tCO₂e)</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.issuer_scope1_tco2e} onChange={e => setForm(f => ({ ...f, issuer_scope1_tco2e: +e.target.value }))} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Issuer Scope 2 (tCO₂e)</label>
            <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.issuer_scope2_tco2e} onChange={e => setForm(f => ({ ...f, issuer_scope2_tco2e: +e.target.value }))} />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">Sector (GICS)</label>
            <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={form.sector_gics} onChange={e => setForm(f => ({ ...f, sector_gics: e.target.value }))} />
          </div>
          <div className="flex items-center gap-3 mt-4">
            <label className="text-xs text-white/40">Include Scope 3</label>
            <input type="checkbox" checked={form.include_scope3} onChange={e => setForm(f => ({ ...f, include_scope3: e.target.checked }))} />
            <label className="text-xs text-white/40 ml-4">Green Bond</label>
            <input type="checkbox" checked={form.green_bond} onChange={e => setForm(f => ({ ...f, green_bond: e.target.checked }))} />
          </div>
        </div>
        <button onClick={handleCompute} disabled={loading}
          className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg flex items-center gap-2">
          {loading ? <><RefreshCw className="h-3 w-3 animate-spin" /> Computing…</> : <><Zap className="h-3 w-3" /> Compute PCAF Facilitated Emissions</>}
        </button>
        {error && <div className="mt-2 text-xs text-red-400">Error: {error}</div>}
      </div>

      {/* Result */}
      {result && (
        <div className="bg-[#111827] border border-indigo-500/20 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-indigo-400 mb-3">Computation Result — Ref: {result.transaction_ref}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            {[
              { label: "Attribution Factor", val: `${fmt(result.attribution_factor * 100, 4)}%` },
              { label: "Facilitated tCO₂e", val: fmt(result.facilitated_tco2e, 0) },
              { label: "Scope 1 Facilitated", val: fmt(result.scope1_facilitated, 0) },
              { label: "Scope 2 Facilitated", val: fmt(result.scope2_facilitated, 0) },
            ].map(({ label, val }) => (
              <div key={label} className="bg-indigo-500/5 border border-indigo-500/10 rounded p-3 text-center">
                <div className="text-sm font-bold text-indigo-300">{val}</div>
                <div className="text-xs text-white/40 mt-1">{label}</div>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/30">PCAF DQS:</span>
            <span className={`text-xs font-bold ${DQS_COLORS[result.pcaf_dqs_derived]}`}>{result.pcaf_dqs_derived}/5</span>
            {result.methodology_note && (
              <span className="text-xs text-white/30 ml-4">{result.methodology_note}</span>
            )}
          </div>
        </div>
      )}

      {/* By Instrument breakdown */}
      {summary?.by_instrument?.length > 0 && (
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white/70 mb-3">Portfolio — By Instrument</h3>
          <table className="w-full text-xs">
            <thead><tr className="text-white/30 border-b border-white/[0.06]">
              <th className="text-left py-1 px-2">Instrument</th>
              <th className="text-right py-1 px-2">Deals</th>
              <th className="text-right py-1 px-2">Underwritten (M USD)</th>
              <th className="text-right py-1 px-2">Facilitated (tCO₂e)</th>
            </tr></thead>
            <tbody>
              {summary.by_instrument.map(r => (
                <tr key={r.instrument_type} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                  <td className="py-1.5 px-2 capitalize text-white/70">{r.instrument_type}</td>
                  <td className="py-1.5 px-2 text-right text-white/50">{r.count}</td>
                  <td className="py-1.5 px-2 text-right text-white/50">{fmt(r.underwritten_musd, 0)}</td>
                  <td className="py-1.5 px-2 text-right text-indigo-400 font-medium">{fmt(r.facilitated_tco2e, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── China CBAM Credit Risk Panel ─────────────────────────────────────────
const CT_API_FR = process.env.REACT_APP_API_URL || process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";
const CT_BASE_FR = `${CT_API_FR}/api/v1/china-trade`;

function ChinaCBAMRiskPanel() {
  const [overlay, setOverlay] = React.useState(null);
  const [portfolio, setPortfolio] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    Promise.all([
      fetch(`${CT_BASE_FR}/cross-module/ecl-cbam-overlay`).then(r => r.json()).catch(() => null),
      fetch(`${CT_BASE_FR}/cross-module/portfolio-cbam`).then(r => r.json()).catch(() => null),
    ]).then(([o, p]) => {
      setOverlay(o);
      setPortfolio(p);
      setLoading(false);
    });
  }, []);

  const BAND_COLORS = { Low: "text-emerald-400", Medium: "text-amber-400", High: "text-orange-400", Critical: "text-red-400" };
  const BAND_BG    = { Low: "bg-emerald-500/10", Medium: "bg-amber-500/10", High: "bg-orange-500/10", Critical: "bg-red-500/10" };

  if (loading) return <div className="text-center py-12 text-white/30 text-sm">Loading China CBAM risk data…</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-base font-bold text-white">China CBAM Credit Risk Overlay</h2>
          <p className="text-xs text-white/40 mt-0.5">
            IFRS 9 PD/LGD uplifts derived from Chinese exporter CBAM readiness scores
          </p>
        </div>
        <div className="flex gap-2 flex-wrap text-[10px]">
          {["IFRS 9 §5.5","EU CBAM Art.9","CETS 2024","EBA GL/2022/16"].map(b => (
            <span key={b} className="px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded border border-blue-500/20">{b}</span>
          ))}
        </div>
      </div>

      {/* Key metrics */}
      {overlay && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">CETS Spot</p>
            <p className="text-xl font-bold text-white">€{overlay.cets_price_eur}</p>
            <p className="text-[10px] text-white/30">per tCO2 (CBEEX)</p>
          </div>
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">EU ETS Reference</p>
            <p className="text-xl font-bold text-white">€{overlay.eu_ets_price_eur}</p>
            <p className="text-[10px] text-white/30">per tCO2 (EEX)</p>
          </div>
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">CBAM Arbitrage</p>
            <p className="text-xl font-bold text-amber-400">€{overlay.cbam_arbitrage_eur}</p>
            <p className="text-[10px] text-white/30">Art.9 deduction gap</p>
          </div>
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">Entities Assessed</p>
            <p className="text-xl font-bold text-white">{overlay.total_entities_assessed}</p>
            <p className="text-[10px] text-white/30">Chinese exporters</p>
          </div>
        </div>
      )}

      {/* ECL CBAM Risk Bands */}
      {overlay?.risk_bands && (
        <Section title="IFRS 9 Staging — CBAM Readiness to PD/LGD Uplift Bands" defaultOpen={true}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">Risk Band</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">CBAM Readiness Range</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">PD Uplift (bps)</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">LGD Uplift (bps)</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">IFRS 9 Stage</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">Entities</th>
                  <th className="text-left py-2 text-white/40 font-medium">Description</th>
                </tr>
              </thead>
              <tbody>
                {overlay.risk_bands.map((b, i) => (
                  <tr key={i} className="border-b border-white/[0.02]">
                    <td className="py-2.5 pr-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${BAND_BG[b.risk_band]} ${BAND_COLORS[b.risk_band]}`}>
                        {b.risk_band}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-white/60">{b.cbam_readiness_min}–{b.cbam_readiness_max}</td>
                    <td className={`py-2.5 pr-4 text-right font-bold ${b.pd_uplift_bps > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {b.pd_uplift_bps > 0 ? `+${b.pd_uplift_bps}` : b.pd_uplift_bps}
                    </td>
                    <td className={`py-2.5 pr-4 text-right font-bold ${b.lgd_uplift_bps > 0 ? 'text-orange-400' : 'text-emerald-400'}`}>
                      {b.lgd_uplift_bps > 0 ? `+${b.lgd_uplift_bps}` : b.lgd_uplift_bps}
                    </td>
                    <td className="py-2.5 pr-4 text-white/50 font-mono text-[10px]">{b.ecl_stage}</td>
                    <td className="py-2.5 pr-4 text-right text-white/70 font-bold">{b.entity_count}</td>
                    <td className="py-2.5 text-white/40 text-[10px]">{b.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-white/20 mt-3 pt-2 border-t border-white/[0.04]">
            Methodology: CBAM readiness score (0–100) derived from CETS registration, ESG tier, carbon intensity vs EU benchmark.
            PD/LGD uplifts applied as climate-adjusted overlays per EBA GL/2022/16 § 4.3.
          </p>
        </Section>
      )}

      {/* Portfolio CBAM Sector Roll-up */}
      {portfolio && (
        <Section title="Portfolio CBAM Exposure — Sector Breakdown (EU CBAM Reg. 2023/956 Art.9)" defaultOpen={true}>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
              <p className="text-xs text-white/40 mb-1">Gross CBAM Liability</p>
              <p className="text-xl font-bold text-white">{fmtCcy(portfolio.total_gross_cbam_liability_eur, "EUR")}</p>
              <p className="text-[10px] text-white/30">before Art.9 deduction</p>
            </div>
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
              <p className="text-xs text-white/40 mb-1">CETS Art.9 Deduction</p>
              <p className="text-xl font-bold text-emerald-400">-{fmtCcy(portfolio.art9_cets_deduction_eur, "EUR")}</p>
              <p className="text-[10px] text-white/30">CETS carbon cost credit</p>
            </div>
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
              <p className="text-xs text-white/40 mb-1">Net CBAM Liability</p>
              <p className="text-xl font-bold text-amber-400">{fmtCcy(portfolio.total_net_cbam_liability_eur, "EUR")}</p>
              <p className="text-[10px] text-white/30">ECL credit risk exposure</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">Sector</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">Entities</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">Avg CBAM Readiness</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">Avg Carbon Intensity</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">Gross Liability</th>
                  <th className="text-right py-2 text-white/40 font-medium">Net Liability</th>
                </tr>
              </thead>
              <tbody>
                {(portfolio.sector_breakdown || []).map((s, i) => (
                  <tr key={i} className="border-b border-white/[0.02]">
                    <td className="py-2.5 pr-4 text-white/80 font-medium">{s.sector}</td>
                    <td className="py-2.5 pr-4 text-right text-white/60">{s.entity_count}</td>
                    <td className={`py-2.5 pr-4 text-right font-bold ${
                      s.avg_readiness >= 70 ? 'text-emerald-400' : s.avg_readiness >= 50 ? 'text-amber-400' : 'text-red-400'
                    }`}>{s.avg_readiness ? Number(s.avg_readiness).toFixed(1) : '—'}</td>
                    <td className="py-2.5 pr-4 text-right text-white/60">
                      {s.avg_carbon_intensity ? `${Number(s.avg_carbon_intensity).toFixed(2)} tCO2/t` : '—'}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-white/70">{fmtCcy(s.gross_liability_eur, "EUR")}</td>
                    <td className="py-2.5 text-right text-amber-400 font-bold">{fmtCcy(s.net_liability_eur, "EUR")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-white/20 mt-3 pt-2 border-t border-white/[0.04]">
            Art.9 deduction = CETS carbon cost already paid by Chinese exporter (€{portfolio.cets_price_eur}/tCO2).
            Net liability = residual CBAM obligation after deduction · Full data at <a href="/china-trade" className="text-cyan-400 hover:underline">/china-trade</a>
          </p>
        </Section>
      )}
    </div>
  );
}

// ── Main Financial Risk Page ──────────────────────────────────────────────
export default function FinancialRiskPage() {
  const [section, setSection] = useState("ecl");

  return (
    <div className="min-h-screen bg-white/[0.02]">
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-400/10 rounded-lg"><Shield className="h-6 w-6 text-blue-600" /></div>
          <div>
            <h1 className="text-xl font-bold text-white">Financial Climate Risk</h1>
            <p className="text-sm text-white/40">IFRS 9 ECL · PCAF Financed Emissions · Facilitated Emissions (PCAF Part C) · WACI · SFDR PAI</p>
          </div>
        </div>
        <div className="flex gap-2 mt-4 flex-wrap">
          {["EBA GL/2022/16","IFRS 9","PCAF v2.0","PCAF Part C","SFDR PAI 1-5","TCFD"].map(b => (
            <span key={b} className="text-xs px-2 py-1 bg-blue-500/10 text-blue-700 border border-blue-500/20 rounded-full font-medium">{b}</span>
          ))}
        </div>
      </div>

      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6">
        <div className="flex gap-0">
          {[["ecl","IFRS 9 ECL + Climate"],["pcaf","PCAF / WACI / Temp Score"],["facilitated","Facilitated Emissions (Part C)"],["china_cbam","China CBAM Credit Risk"]].map(([id, l]) => (
            <button key={id} onClick={() => setSection(id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 ${section === id ? "border-blue-500 text-blue-600" : "border-transparent text-white/40 hover:text-white/70"}`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        {section === "ecl" && (
          <Section title="IFRS 9 ECL with Climate Scenario Overlay (EBA GL/2022/16)">
            <ECLPanel />
          </Section>
        )}
        {section === "pcaf" && (
          <Section title="PCAF Financed Emissions & WACI (PCAF Standard v2.0)">
            <PCaFPanel />
          </Section>
        )}
        {section === "facilitated" && (
          <Section title="PCAF Facilitated Emissions — Capital Markets Underwriting (PCAF Part C, 2022)">
            <FacilitatedEmissionsPanel />
          </Section>
        )}
        {section === "china_cbam" && <ChinaCBAMRiskPanel />}
      </div>
    </div>
  );
}
