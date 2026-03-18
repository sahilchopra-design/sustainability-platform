/**
 * Sovereign Emissions Page
 * Tabbed interface for three engines:
 *   1. Sovereign Climate Risk  (/api/v1/sovereign-climate-risk)
 *   2. Insurance Emissions PCAF Part B (/api/v1/insurance-risk)
 *   3. Agriculture Expanded   (/api/v1/agriculture-engine)
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, RadialBarChart, RadialBar,
} from "recharts";
import {
  Globe, ShieldCheck, Leaf, ChevronDown, ChevronRight, Loader2,
  AlertTriangle, TrendingUp, Bug, Trees,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt = (v, dp = 1) => (v == null ? "\u2014" : Number(v).toFixed(dp));
const fmtEur = (v) => (v == null ? "\u2014" : `\u20AC${(Number(v) / 1e6).toFixed(2)}M`);
const fmtBps = (v) => (v == null ? "\u2014" : `${Number(v).toFixed(1)} bps`);
const fmtPct = (v) => (v == null ? "\u2014" : `${(Number(v)).toFixed(1)}%`);

const PIE_COLORS = ["#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#ec4899"];
const SCENARIOS = [
  { v: "net_zero_2050", l: "Net Zero 2050" },
  { v: "below_2c", l: "Below 2\u00B0C" },
  { v: "delayed_transition", l: "Delayed Transition" },
  { v: "current_policies", l: "Current Policies" },
  { v: "nationally_determined", l: "Nationally Determined" },
];
const TIME_HORIZONS = [{ v: "2030", l: "2030" }, { v: "2050", l: "2050" }];

/* ── Shared UI Primitives ─────────────────────────────────────────────── */
function Badge({ label, color = "bg-gray-50 text-gray-600" }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}
function Card({ title, subtitle, children, className = "" }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-gray-200">
          {title && <h2 className="text-sm font-semibold text-gray-900">{title}</h2>}
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
function StatCard({ label, value, sub, color = "text-gray-900" }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs text-gray-500 font-medium mb-1">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-[11px] text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}
function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
      {hint && <p className="text-[10px] text-gray-500 mt-0.5">{hint}</p>}
    </div>
  );
}
function Input({ value, onChange, type = "text", ...rest }) {
  return (
    <input type={type} value={value}
      onChange={e => onChange(type === "number" ? parseFloat(e.target.value) || 0 : e.target.value)}
      className="w-full border border-gray-200 rounded-lg bg-[#f5f6f8] text-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black/50"
      {...rest} />
  );
}
function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-gray-200 rounded-lg bg-[#f5f6f8] text-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black/50">
      {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  );
}
function Btn({ children, onClick, loading, disabled, variant = "primary" }) {
  const base = "px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 flex items-center gap-2";
  const cls = variant === "primary"
    ? `${base} bg-gray-100 text-gray-800 hover:bg-gray-300 border border-gray-200`
    : `${base} bg-gray-50 text-gray-600 hover:bg-gray-50 border border-gray-200`;
  return <button onClick={onClick} disabled={disabled || loading} className={cls}>{loading && <Loader2 className="w-4 h-4 animate-spin" />}{children}</button>;
}
function ErrorBox({ msg }) {
  if (!msg) return null;
  return <div className="bg-red-500/10 border border-red-400/20 rounded-lg p-3 text-xs text-red-300 flex items-center gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />{msg}</div>;
}
function Collapsible({ title, icon: Icon, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-3 px-5 py-3.5 bg-white hover:bg-gray-50 transition-colors">
        {Icon && <Icon className="w-4 h-4 text-gray-700" />}
        <span className="text-sm font-medium text-gray-800 flex-1 text-left">{title}</span>
        {open ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
      </button>
      {open && <div className="p-5 bg-[#f5f6f8] border-t border-gray-200 space-y-5">{children}</div>}
    </div>
  );
}
function GaugeChart({ value, max = 100, label }) {
  const pct = Math.min(Math.max(value / max, 0), 1);
  const color = pct >= 0.7 ? "#ef4444" : pct >= 0.4 ? "#f59e0b" : "#10b981";
  const data = [{ name: label, value: pct * 100, fill: color }];
  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width={160} height={100}>
        <RadialBarChart cx="50%" cy="100%" innerRadius="70%" outerRadius="100%" startAngle={180} endAngle={0} barSize={12} data={data}>
          <RadialBar background clockWise dataKey="value" cornerRadius={6} />
        </RadialBarChart>
      </ResponsiveContainer>
      <p className="text-lg font-bold text-gray-900 mt-[-8px]">{fmt(value, 0)}<span className="text-xs text-gray-500">/{max}</span></p>
      {label && <p className="text-[11px] text-gray-500 mt-0.5">{label}</p>}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 1: SOVEREIGN CLIMATE RISK
   ══════════════════════════════════════════════════════════════════════════ */
function SovereignPanel() {
  const [countries, setCountries] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [iso, setIso] = useState("");
  const [scenario, setScenario] = useState("net_zero_2050");
  const [horizon, setHorizon] = useState("2030");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Portfolio state
  const [holdings, setHoldings] = useState([{ country_iso: "", exposure_eur: 100000000, duration_years: 5 }]);
  const [pScenario, setPScenario] = useState("net_zero_2050");
  const [pHorizon, setPHorizon] = useState("2030");
  const [pResult, setPResult] = useState(null);
  const [pLoading, setPLoading] = useState(false);
  const [pError, setPError] = useState("");

  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/sovereign-climate-risk/ref/countries`).then(r => setCountries(r.data?.countries || r.data || [])).catch(() => {});
    axios.get(`${API_BASE}/api/v1/sovereign-climate-risk/ref/profiles`).then(r => setProfiles(r.data?.profiles || r.data || [])).catch(() => {});
  }, []);

  const countryOpts = countries.map(c => ({ v: c.iso || c, l: c.name || c }));
  const assess = async () => {
    setLoading(true); setError(""); setResult(null);
    try { const r = await axios.post(`${API_BASE}/api/v1/sovereign-climate-risk/assess`, { country_iso: iso, scenario, time_horizon: parseInt(horizon) }); setResult(r.data); }
    catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };
  const addHolding = () => setHoldings([...holdings, { country_iso: "", exposure_eur: 50000000, duration_years: 5 }]);
  const updateHolding = (i, k, v) => { const h = [...holdings]; h[i] = { ...h[i], [k]: v }; setHoldings(h); };
  const removeHolding = (i) => setHoldings(holdings.filter((_, j) => j !== i));
  const assessPortfolio = async () => {
    setPLoading(true); setPError(""); setPResult(null);
    try { const r = await axios.post(`${API_BASE}/api/v1/sovereign-climate-risk/portfolio`, { holdings, scenario: pScenario, time_horizon: parseInt(pHorizon) }); setPResult(r.data); }
    catch (e) { setPError(e.response?.data?.detail || e.message); } finally { setPLoading(false); }
  };

  const pillarData = result ? [
    { name: "Physical (30%)", score: result.physical_score ?? result.pillar_scores?.physical ?? 0, fill: "#ef4444" },
    { name: "Transition (25%)", score: result.transition_score ?? result.pillar_scores?.transition ?? 0, fill: "#f59e0b" },
    { name: "Fiscal (25%)", score: result.fiscal_score ?? result.pillar_scores?.fiscal ?? 0, fill: "#8b5cf6" },
    { name: "Adaptation (20%)", score: result.adaptation_score ?? result.pillar_scores?.adaptation ?? 0, fill: "#10b981" },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Single Country Assessment */}
      <Card title="Single Sovereign Assessment" subtitle="Climate-adjusted creditworthiness per NGFS scenarios">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <Field label="Country">
            <Sel value={iso} onChange={setIso} options={[{ v: "", l: "Select country..." }, ...countryOpts]} />
          </Field>
          <Field label="Scenario">
            <Sel value={scenario} onChange={setScenario} options={SCENARIOS} />
          </Field>
          <Field label="Time Horizon">
            <Sel value={horizon} onChange={setHorizon} options={TIME_HORIZONS} />
          </Field>
          <div className="flex items-end">
            <Btn onClick={assess} loading={loading} disabled={!iso}>Assess Country</Btn>
          </div>
        </div>
        <ErrorBox msg={error} />
        {result && (
          <div className="mt-5 space-y-5">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <StatCard label="Composite Score" value={fmt(result.composite_score ?? result.composite, 1)} sub="0-100 scale" color={((result.composite_score ?? result.composite) >= 55) ? "text-red-400" : "text-emerald-400"} />
              <StatCard label="S&P Rating" value={result.adjusted_rating ?? result.rating ?? "\u2014"} sub={`Notch adj: ${result.notch_adjustment ?? 0}`} />
              <StatCard label="Spread Delta" value={fmtBps(result.climate_spread_delta_bps ?? result.spread_delta)} color="text-amber-400" />
              <StatCard label="ND-GAIN" value={fmt(result.nd_gain ?? result.country_profile?.nd_gain, 0)} sub="Readiness index" />
              <StatCard label="Region" value={result.region ?? result.country_profile?.region ?? "\u2014"} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <Card title="Composite Score" className="bg-[#f5f6f8]">
                <div className="flex justify-center"><GaugeChart value={result.composite_score ?? result.composite ?? 0} max={100} label="Climate Risk" /></div>
              </Card>
              <Card title="Pillar Breakdown" className="bg-[#f5f6f8]">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={pillarData} layout="vertical" margin={{ left: 90 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis type="number" domain={[0, 10]} tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                    <YAxis dataKey="name" type="category" tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }} width={85} />
                    <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
                    <Bar dataKey="score" radius={[0, 4, 4, 0]}>{pillarData.map((d, i) => <Cell key={i} fill={d.fill} />)}</Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </div>
        )}
      </Card>

      {/* Portfolio Assessment */}
      <Card title="Portfolio Sovereign Assessment" subtitle="Exposure-weighted climate VaR across sovereign holdings">
        <div className="space-y-3 mb-4">
          {holdings.map((h, i) => (
            <div key={i} className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
              <Field label="Country">
                <Sel value={h.country_iso} onChange={v => updateHolding(i, "country_iso", v)} options={[{ v: "", l: "Select..." }, ...countryOpts]} />
              </Field>
              <Field label="Exposure (EUR)">
                <Input type="number" value={h.exposure_eur} onChange={v => updateHolding(i, "exposure_eur", v)} />
              </Field>
              <Field label="Duration (yrs)">
                <Input type="number" value={h.duration_years} onChange={v => updateHolding(i, "duration_years", v)} />
              </Field>
              <div className="flex gap-2">
                {holdings.length > 1 && <Btn variant="ghost" onClick={() => removeHolding(i)}>Remove</Btn>}
              </div>
            </div>
          ))}
          <Btn variant="ghost" onClick={addHolding}>+ Add Holding</Btn>
        </div>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <Field label="Scenario"><Sel value={pScenario} onChange={setPScenario} options={SCENARIOS} /></Field>
          <Field label="Time Horizon"><Sel value={pHorizon} onChange={setPHorizon} options={TIME_HORIZONS} /></Field>
          <div className="flex items-end"><Btn onClick={assessPortfolio} loading={pLoading} disabled={holdings.every(h => !h.country_iso)}>Assess Portfolio</Btn></div>
        </div>
        <ErrorBox msg={pError} />
        {pResult && (
          <div className="mt-5 space-y-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Weighted Composite" value={fmt(pResult.weighted_composite ?? pResult.portfolio_composite, 1)} color="text-gray-700" />
              <StatCard label="Climate VaR" value={fmtEur(pResult.climate_var ?? pResult.portfolio_climate_var)} color="text-red-400" />
              <StatCard label="Avg Spread Delta" value={fmtBps(pResult.avg_spread_delta ?? pResult.weighted_spread_delta)} />
              <StatCard label="Holdings Count" value={pResult.holdings_count ?? pResult.country_results?.length ?? 0} />
            </div>
            {(pResult.country_results || pResult.assessments) && (
              <Card title="Country Heatmap" className="bg-[#f5f6f8]">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="text-gray-500 border-b border-gray-200">
                      <th className="text-left py-2 px-3">Country</th><th className="text-right px-3">Composite</th>
                      <th className="text-right px-3">Rating</th><th className="text-right px-3">Spread (bps)</th>
                      <th className="text-right px-3">Exposure</th><th className="text-right px-3">VaR</th>
                    </tr></thead>
                    <tbody>{(pResult.country_results || pResult.assessments || []).map((c, i) => {
                      const comp = c.composite_score ?? c.composite ?? 0;
                      const bg = comp >= 55 ? "bg-red-500/10" : comp >= 40 ? "bg-amber-500/10" : "bg-emerald-500/10";
                      return (
                        <tr key={i} className={`${bg} border-b border-gray-100`}>
                          <td className="py-2 px-3 text-gray-700">{c.country_iso ?? c.country}</td>
                          <td className="text-right px-3 text-gray-800 font-medium">{fmt(comp, 1)}</td>
                          <td className="text-right px-3 text-gray-600">{c.adjusted_rating ?? c.rating ?? "\u2014"}</td>
                          <td className="text-right px-3 text-amber-400">{fmtBps(c.climate_spread_delta_bps ?? c.spread_delta)}</td>
                          <td className="text-right px-3 text-gray-600">{fmtEur(c.exposure_eur ?? c.exposure)}</td>
                          <td className="text-right px-3 text-red-400">{fmtEur(c.climate_var ?? c.var)}</td>
                        </tr>
                      );
                    })}</tbody>
                  </table>
                </div>
              </Card>
            )}
            {(pResult.scenario_comparison || pResult.country_results) && (
              <Card title="Scenario Comparison" className="bg-[#f5f6f8]">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={pResult.scenario_comparison || (pResult.country_results || []).map(c => ({ name: c.country_iso ?? c.country, composite: c.composite_score ?? c.composite, spread: c.climate_spread_delta_bps ?? c.spread_delta }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} />
                    <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
                    <Legend wrapperStyle={{ fontSize: 11, color: "rgba(255,255,255,0.5)" }} />
                    <Bar dataKey="composite" name="Composite Score" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="spread" name="Spread Delta (bps)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 2: INSURANCE EMISSIONS (PCAF PART B)
   ══════════════════════════════════════════════════════════════════════════ */
function InsuranceEmissionsPanel() {
  const [mode, setMode] = useState("motor");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  // Motor state
  const [motor, setMotor] = useState({ vehicle_count: 200, avg_km: 15000, fuel_type: "diesel", premium_data: { total_premium: 5000000 }, attribution_method: "premium_weighted" });
  // Property state
  const [property, setProperty] = useState({ properties: [{ area_sqm: 5000, epc_rating: "C", location: "DE" }], premium_data: { total_premium: 8000000 } });
  // Commercial state
  const [commercial, setCommercial] = useState({ portfolio: [{ revenue_eur: 50000000, sector: "manufacturing", country: "DE" }], premium_data: { total_premium: 12000000 } });
  // Portfolio state
  const [portfolio, setPortfolio] = useState(null);
  const [pLoading, setPLoading] = useState(false);
  const [pError, setPError] = useState("");

  const LOB_MODES = [
    { v: "motor", l: "Motor (Vehicle Fleet)" },
    { v: "property", l: "Property (Area-Based)" },
    { v: "commercial", l: "Commercial (Revenue-Based)" },
    { v: "portfolio", l: "Combined Portfolio" },
  ];
  const FUEL_TYPES = [{ v: "diesel", l: "Diesel" }, { v: "petrol", l: "Petrol" }, { v: "electric", l: "Electric" }, { v: "hybrid", l: "Hybrid" }, { v: "lpg", l: "LPG" }];
  const EPC_RATINGS = [{ v: "A", l: "A" }, { v: "B", l: "B" }, { v: "C", l: "C" }, { v: "D", l: "D" }, { v: "E", l: "E" }, { v: "F", l: "F" }, { v: "G", l: "G" }];

  const submit = async () => {
    setLoading(true); setError(""); setResult(null);
    try {
      let endpoint, payload;
      if (mode === "motor") { endpoint = "/assess-motor"; payload = motor; }
      else if (mode === "property") { endpoint = "/assess-property"; payload = property; }
      else if (mode === "commercial") { endpoint = "/assess-commercial"; payload = commercial; }
      else { endpoint = "/assess-portfolio"; payload = { motor, property, commercial }; }
      const r = await axios.post(`${API_BASE}/api/v1/insurance-risk${endpoint}`, payload);
      setResult(r.data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const lobBreakdown = result?.lob_breakdown || result?.emissions_by_lob;
  const pieData = lobBreakdown ? Object.entries(lobBreakdown).map(([name, val]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: typeof val === "object" ? (val.insured_emissions ?? val.total ?? 0) : val,
  })) : [];

  return (
    <div className="space-y-6">
      <Card title="PCAF Part B \u2014 Insurance-Associated Emissions" subtitle="Premium-weighted attribution across motor, property, commercial, and life/health LOBs">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-5">
          <p className="text-xs text-gray-500 leading-relaxed">
            <strong className="text-gray-700">Methodology:</strong> PCAF Part B measures insurance-associated emissions using premium-weighted attribution.
            Motor uses vehicle fleet data (km, fuel type). Property uses area-based energy intensity (EPC/EUI). Commercial uses revenue-based emission factors.
            Life/health follows disclosure-only guidance. Data Quality Scores (DQS 1\u20135) indicate reliability.
          </p>
        </div>
        <div className="flex gap-2 mb-5 flex-wrap">
          {LOB_MODES.map(m => (
            <button key={m.v} onClick={() => { setMode(m.v); setResult(null); setError(""); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${mode === m.v ? "bg-gray-100 text-gray-800 border-gray-200" : "bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-50"}`}>
              {m.l}
            </button>
          ))}
        </div>

        {mode === "motor" && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Field label="Vehicle Count"><Input type="number" value={motor.vehicle_count} onChange={v => setMotor({ ...motor, vehicle_count: v })} /></Field>
            <Field label="Avg km/year"><Input type="number" value={motor.avg_km} onChange={v => setMotor({ ...motor, avg_km: v })} /></Field>
            <Field label="Fuel Type"><Sel value={motor.fuel_type} onChange={v => setMotor({ ...motor, fuel_type: v })} options={FUEL_TYPES} /></Field>
            <Field label="Total Premium (EUR)"><Input type="number" value={motor.premium_data.total_premium} onChange={v => setMotor({ ...motor, premium_data: { total_premium: v } })} /></Field>
          </div>
        )}
        {mode === "property" && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Field label="Area (sqm)"><Input type="number" value={property.properties[0].area_sqm} onChange={v => setProperty({ ...property, properties: [{ ...property.properties[0], area_sqm: v }] })} /></Field>
            <Field label="EPC Rating"><Sel value={property.properties[0].epc_rating} onChange={v => setProperty({ ...property, properties: [{ ...property.properties[0], epc_rating: v }] })} options={EPC_RATINGS} /></Field>
            <Field label="Location (ISO)"><Input value={property.properties[0].location} onChange={v => setProperty({ ...property, properties: [{ ...property.properties[0], location: v }] })} /></Field>
            <Field label="Total Premium (EUR)"><Input type="number" value={property.premium_data.total_premium} onChange={v => setProperty({ ...property, premium_data: { total_premium: v } })} /></Field>
          </div>
        )}
        {mode === "commercial" && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Field label="Revenue (EUR)"><Input type="number" value={commercial.portfolio[0].revenue_eur} onChange={v => setCommercial({ ...commercial, portfolio: [{ ...commercial.portfolio[0], revenue_eur: v }] })} /></Field>
            <Field label="Sector"><Input value={commercial.portfolio[0].sector} onChange={v => setCommercial({ ...commercial, portfolio: [{ ...commercial.portfolio[0], sector: v }] })} /></Field>
            <Field label="Country (ISO)"><Input value={commercial.portfolio[0].country} onChange={v => setCommercial({ ...commercial, portfolio: [{ ...commercial.portfolio[0], country: v }] })} /></Field>
            <Field label="Total Premium (EUR)"><Input type="number" value={commercial.premium_data.total_premium} onChange={v => setCommercial({ ...commercial, premium_data: { total_premium: v } })} /></Field>
          </div>
        )}
        {mode === "portfolio" && (
          <p className="text-xs text-gray-500 mb-4">Portfolio mode combines motor, property, and commercial inputs from above. Fill in each LOB tab first, then run combined assessment.</p>
        )}

        <Btn onClick={submit} loading={loading}>Run {mode === "portfolio" ? "Portfolio" : "LOB"} Assessment</Btn>
        <ErrorBox msg={error} />

        {result && (
          <div className="mt-5 space-y-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Total Insured Emissions" value={`${fmt(result.total_insured_emissions ?? result.insured_emissions ?? 0, 0)} tCO\u2082e`} color="text-gray-700" />
              <StatCard label="Intensity" value={`${fmt(result.emission_intensity ?? result.intensity ?? 0, 2)} tCO\u2082e/\u20ACM`} sub="per EUR premium" color="text-amber-400" />
              <StatCard label="Data Quality Score" value={fmt(result.dqs ?? result.data_quality_score ?? 0, 1)} sub="DQS 1-5 (1=best)" color="text-emerald-400" />
              <StatCard label="Attribution Factor" value={fmtPct((result.attribution_factor ?? result.premium_attribution ?? 0) * 100)} />
            </div>
            {pieData.length > 0 && (
              <Card title="Emissions by Line of Business" className="bg-[#f5f6f8]">
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={90} innerRadius={50} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                      {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            )}
            {(result.dqs_by_lob || result.lob_dqs) && (
              <Card title="DQS per LOB" className="bg-[#f5f6f8]">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={Object.entries(result.dqs_by_lob || result.lob_dqs || {}).map(([k, v]) => ({ lob: k, dqs: v }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="lob" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} />
                    <YAxis domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
                    <Bar dataKey="dqs" name="DQS" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 3: AGRICULTURE EXPANDED
   ══════════════════════════════════════════════════════════════════════════ */
function AgricultureExpandedPanel() {
  return (
    <div className="space-y-5">
      <MethaneSection />
      <DiseaseSection />
      <BNGSection />
    </div>
  );
}

/* ── 3A: Methane Intensity ─────────────────────────────────────────────── */
function MethaneSection() {
  const [form, setForm] = useState({ livestock_type: "dairy_cattle", head_count: 500, manure_system: "lagoon", region: "western_europe" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const LIVESTOCK = [{ v: "dairy_cattle", l: "Dairy Cattle" }, { v: "beef_cattle", l: "Beef Cattle" }, { v: "sheep", l: "Sheep" }, { v: "goats", l: "Goats" }, { v: "pigs", l: "Pigs" }, { v: "poultry", l: "Poultry" }];
  const MANURE = [{ v: "lagoon", l: "Lagoon" }, { v: "slurry", l: "Slurry" }, { v: "solid_storage", l: "Solid Storage" }, { v: "daily_spread", l: "Daily Spread" }, { v: "digester", l: "Anaerobic Digester" }, { v: "compost", l: "Compost" }];
  const REGIONS = [{ v: "western_europe", l: "Western Europe" }, { v: "eastern_europe", l: "Eastern Europe" }, { v: "north_america", l: "North America" }, { v: "south_america", l: "South America" }, { v: "south_asia", l: "South Asia" }, { v: "east_asia", l: "East Asia" }, { v: "sub_saharan_africa", l: "Sub-Saharan Africa" }, { v: "oceania", l: "Oceania" }];

  const submit = async () => {
    setLoading(true); setError(""); setResult(null);
    try { const r = await axios.post(`${API_BASE}/api/v1/agriculture-engine/methane-intensity`, form); setResult(r.data); }
    catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const breakdownData = result ? [
    { name: "Enteric CH\u2084", value: result.enteric_ch4_tonnes ?? result.enteric_ch4 ?? 0, fill: "#ef4444" },
    { name: "Manure CH\u2084", value: result.manure_ch4_tonnes ?? result.manure_ch4 ?? 0, fill: "#f59e0b" },
  ] : [];
  const abatementData = (result?.abatement_options || []).map((a, i) => ({
    name: a.option ?? a.name ?? `Option ${i + 1}`,
    reduction: a.reduction_pct ?? a.reduction ?? 0,
    cost: a.cost_per_tco2e ?? a.cost ?? 0,
  }));

  return (
    <Collapsible title="Methane Intensity (IPCC Tier 1)" icon={TrendingUp} defaultOpen>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <Field label="Livestock Type"><Sel value={form.livestock_type} onChange={v => setForm({ ...form, livestock_type: v })} options={LIVESTOCK} /></Field>
        <Field label="Head Count"><Input type="number" value={form.head_count} onChange={v => setForm({ ...form, head_count: v })} /></Field>
        <Field label="Manure System"><Sel value={form.manure_system} onChange={v => setForm({ ...form, manure_system: v })} options={MANURE} /></Field>
        <Field label="Region"><Sel value={form.region} onChange={v => setForm({ ...form, region: v })} options={REGIONS} /></Field>
      </div>
      <Btn onClick={submit} loading={loading}>Calculate Methane Intensity</Btn>
      <ErrorBox msg={error} />
      {result && (
        <div className="mt-5 space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total CO\u2082e" value={`${fmt(result.total_co2e ?? result.gwp100_co2e ?? 0, 0)} t`} color="text-red-400" sub="GWP-100" />
            <StatCard label="Enteric CH\u2084" value={`${fmt(result.enteric_ch4_tonnes ?? result.enteric_ch4 ?? 0, 1)} t`} color="text-amber-400" />
            <StatCard label="Manure CH\u2084" value={`${fmt(result.manure_ch4_tonnes ?? result.manure_ch4 ?? 0, 1)} t`} color="text-purple-400" />
            <StatCard label="Intensity" value={`${fmt(result.intensity_per_head ?? result.per_head ?? 0, 2)} tCO\u2082e/hd`} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Card title="Emissions Breakdown" className="bg-[#f5f6f8]">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={breakdownData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} />
                  <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
                  <Bar dataKey="value" name="CH\u2084 (tonnes)" radius={[4, 4, 0, 0]}>{breakdownData.map((d, i) => <Cell key={i} fill={d.fill} />)}</Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
            {abatementData.length > 0 && (
              <Card title="Abatement Waterfall" className="bg-[#f5f6f8]">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={abatementData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 9 }} angle={-20} textAnchor="end" height={50} />
                    <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="reduction" name="Reduction %" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="cost" name="$/tCO\u2082e" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}
          </div>
        </div>
      )}
    </Collapsible>
  );
}

/* ── 3B: Disease Outbreak Risk ─────────────────────────────────────────── */
function DiseaseSection() {
  const [form, setForm] = useState({ species: "cattle", region: "western_europe", herd_size: 1000, biosecurity_measures: ["fencing", "quarantine"] });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [bioInput, setBioInput] = useState("");

  const SPECIES = [{ v: "cattle", l: "Cattle" }, { v: "poultry", l: "Poultry" }, { v: "pigs", l: "Pigs" }, { v: "sheep", l: "Sheep" }, { v: "goats", l: "Goats" }];
  const REGIONS = [{ v: "western_europe", l: "Western Europe" }, { v: "eastern_europe", l: "Eastern Europe" }, { v: "north_america", l: "North America" }, { v: "south_america", l: "South America" }, { v: "south_asia", l: "South Asia" }, { v: "east_asia", l: "East Asia" }, { v: "sub_saharan_africa", l: "Sub-Saharan Africa" }];

  const addBio = () => { if (bioInput.trim()) { setForm({ ...form, biosecurity_measures: [...form.biosecurity_measures, bioInput.trim()] }); setBioInput(""); } };
  const removeBio = (i) => setForm({ ...form, biosecurity_measures: form.biosecurity_measures.filter((_, j) => j !== i) });

  const submit = async () => {
    setLoading(true); setError(""); setResult(null);
    try { const r = await axios.post(`${API_BASE}/api/v1/agriculture-engine/disease-risk`, form); setResult(r.data); }
    catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const riskMatrix = (result?.disease_profiles || result?.diseases || []).map(d => ({
    name: d.disease ?? d.name,
    probability: d.outbreak_probability ?? d.probability ?? 0,
    severity: d.severity_score ?? d.severity ?? 0,
    climate_adj: d.climate_adjusted_risk ?? d.climate_risk ?? 0,
  }));

  return (
    <Collapsible title="Disease Outbreak Risk (OIE/WOAH)" icon={Bug}>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        <Field label="Species"><Sel value={form.species} onChange={v => setForm({ ...form, species: v })} options={SPECIES} /></Field>
        <Field label="Region"><Sel value={form.region} onChange={v => setForm({ ...form, region: v })} options={REGIONS} /></Field>
        <Field label="Herd Size"><Input type="number" value={form.herd_size} onChange={v => setForm({ ...form, herd_size: v })} /></Field>
      </div>
      <div className="mb-4">
        <Field label="Biosecurity Measures">
          <div className="flex gap-2 flex-wrap mb-2">
            {form.biosecurity_measures.map((b, i) => (
              <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-emerald-500/10 text-emerald-300 text-xs border border-emerald-400/20">
                {b} <button onClick={() => removeBio(i)} className="text-gray-500 hover:text-gray-700">&times;</button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <Input value={bioInput} onChange={setBioInput} placeholder="e.g. vaccination, disinfection..." />
            <Btn variant="ghost" onClick={addBio}>Add</Btn>
          </div>
        </Field>
      </div>
      <Btn onClick={submit} loading={loading}>Assess Disease Risk</Btn>
      <ErrorBox msg={error} />
      {result && (
        <div className="mt-5 space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Overall Risk" value={fmt(result.overall_risk ?? result.composite_risk ?? 0, 1)} sub="0-10 scale" color={((result.overall_risk ?? result.composite_risk ?? 0) >= 6) ? "text-red-400" : "text-emerald-400"} />
            <StatCard label="Biosecurity Score" value={fmt(result.biosecurity_score ?? 0, 1)} sub="0-10 (10=best)" color="text-gray-700" />
            <StatCard label="Climate Amplification" value={`${fmt((result.climate_amplification ?? result.climate_factor ?? 1) * 100, 0)}%`} color="text-amber-400" />
            <StatCard label="Diseases Assessed" value={riskMatrix.length} />
          </div>
          {riskMatrix.length > 0 && (
            <Card title="Risk Matrix Heatmap" className="bg-[#f5f6f8]">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="text-gray-500 border-b border-gray-200">
                    <th className="text-left py-2 px-3">Disease</th><th className="text-right px-3">Probability</th>
                    <th className="text-right px-3">Severity</th><th className="text-right px-3">Climate-Adj Risk</th>
                    <th className="px-3">Level</th>
                  </tr></thead>
                  <tbody>{riskMatrix.map((d, i) => {
                    const risk = d.climate_adj ?? d.probability * d.severity;
                    const level = risk >= 0.6 ? "HIGH" : risk >= 0.3 ? "MEDIUM" : "LOW";
                    const lc = risk >= 0.6 ? "text-red-400 bg-red-500/10" : risk >= 0.3 ? "text-amber-400 bg-amber-500/10" : "text-emerald-400 bg-emerald-500/10";
                    return (
                      <tr key={i} className="border-b border-gray-100">
                        <td className="py-2 px-3 text-gray-700 font-medium">{d.name}</td>
                        <td className="text-right px-3 text-gray-600">{fmtPct(d.probability * 100)}</td>
                        <td className="text-right px-3 text-gray-600">{fmt(d.severity, 1)}</td>
                        <td className="text-right px-3 text-amber-400">{fmtPct(d.climate_adj * 100)}</td>
                        <td className="px-3"><Badge label={level} color={lc} /></td>
                      </tr>
                    );
                  })}</tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}
    </Collapsible>
  );
}

/* ── 3C: Biodiversity Net Gain ─────────────────────────────────────────── */
function BNGSection() {
  const [form, setForm] = useState({
    site_area_ha: 25,
    habitats: [{ type: "grassland", condition: "moderate", area: 10 }, { type: "woodland", condition: "good", area: 8 }],
    proposed_changes: [{ type: "wetland_creation", area: 5, target_condition: "good" }],
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const HAB_TYPES = [{ v: "grassland", l: "Grassland" }, { v: "woodland", l: "Woodland" }, { v: "wetland", l: "Wetland" }, { v: "heathland", l: "Heathland" }, { v: "hedgerow", l: "Hedgerow" }, { v: "arable", l: "Arable" }, { v: "urban", l: "Urban" }, { v: "scrub", l: "Scrub" }];
  const CONDITIONS = [{ v: "poor", l: "Poor" }, { v: "moderate", l: "Moderate" }, { v: "good", l: "Good" }];

  const addHabitat = () => setForm({ ...form, habitats: [...form.habitats, { type: "grassland", condition: "moderate", area: 5 }] });
  const updateHab = (i, k, v) => { const h = [...form.habitats]; h[i] = { ...h[i], [k]: v }; setForm({ ...form, habitats: h }); };
  const removeHab = (i) => setForm({ ...form, habitats: form.habitats.filter((_, j) => j !== i) });
  const addChange = () => setForm({ ...form, proposed_changes: [...form.proposed_changes, { type: "wetland_creation", area: 2, target_condition: "good" }] });
  const updateChange = (i, k, v) => { const c = [...form.proposed_changes]; c[i] = { ...c[i], [k]: v }; setForm({ ...form, proposed_changes: c }); };
  const removeChange = (i) => setForm({ ...form, proposed_changes: form.proposed_changes.filter((_, j) => j !== i) });

  const submit = async () => {
    setLoading(true); setError(""); setResult(null);
    try { const r = await axios.post(`${API_BASE}/api/v1/agriculture-engine/bng-assessment`, form); setResult(r.data); }
    catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const comparisonData = result ? [
    { name: "Before", units: result.habitat_units_before ?? result.baseline_units ?? 0, fill: "#ef4444" },
    { name: "After", units: result.habitat_units_after ?? result.post_units ?? 0, fill: "#10b981" },
  ] : [];
  const bngPct = result ? (result.bng_percentage ?? result.net_gain_pct ?? 0) : 0;

  return (
    <Collapsible title="Biodiversity Net Gain (DEFRA Metric 4.0)" icon={Trees}>
      <Field label="Site Area (ha)">
        <Input type="number" value={form.site_area_ha} onChange={v => setForm({ ...form, site_area_ha: v })} />
      </Field>

      <div className="mt-4">
        <p className="text-xs font-medium text-gray-600 mb-2">Existing Habitats</p>
        {form.habitats.map((h, i) => (
          <div key={i} className="grid grid-cols-4 gap-3 mb-2 items-end">
            <Field label="Type"><Sel value={h.type} onChange={v => updateHab(i, "type", v)} options={HAB_TYPES} /></Field>
            <Field label="Condition"><Sel value={h.condition} onChange={v => updateHab(i, "condition", v)} options={CONDITIONS} /></Field>
            <Field label="Area (ha)"><Input type="number" value={h.area} onChange={v => updateHab(i, "area", v)} /></Field>
            <Btn variant="ghost" onClick={() => removeHab(i)}>Remove</Btn>
          </div>
        ))}
        <Btn variant="ghost" onClick={addHabitat}>+ Add Habitat</Btn>
      </div>

      <div className="mt-4">
        <p className="text-xs font-medium text-gray-600 mb-2">Proposed Changes</p>
        {form.proposed_changes.map((c, i) => (
          <div key={i} className="grid grid-cols-4 gap-3 mb-2 items-end">
            <Field label="Change Type"><Input value={c.type} onChange={v => updateChange(i, "type", v)} /></Field>
            <Field label="Area (ha)"><Input type="number" value={c.area} onChange={v => updateChange(i, "area", v)} /></Field>
            <Field label="Target Condition"><Sel value={c.target_condition} onChange={v => updateChange(i, "target_condition", v)} options={CONDITIONS} /></Field>
            <Btn variant="ghost" onClick={() => removeChange(i)}>Remove</Btn>
          </div>
        ))}
        <Btn variant="ghost" onClick={addChange}>+ Add Change</Btn>
      </div>

      <div className="mt-4"><Btn onClick={submit} loading={loading}>Run BNG Assessment</Btn></div>
      <ErrorBox msg={error} />

      {result && (
        <div className="mt-5 space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Units Before" value={fmt(result.habitat_units_before ?? result.baseline_units ?? 0, 1)} color="text-red-400" />
            <StatCard label="Units After" value={fmt(result.habitat_units_after ?? result.post_units ?? 0, 1)} color="text-emerald-400" />
            <StatCard label="BNG %" value={fmtPct(bngPct)} color={bngPct >= 10 ? "text-emerald-400" : "text-amber-400"} sub={bngPct >= 10 ? "Meets 10% requirement" : "Below 10% threshold"} />
            <StatCard label="Credits Required" value={fmt(result.credit_requirements ?? result.credits_needed ?? 0, 0)} sub="biodiversity units" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Card title="Habitat Unit Comparison" className="bg-[#f5f6f8]">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} />
                  <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
                  <Bar dataKey="units" name="Habitat Units" radius={[4, 4, 0, 0]}>{comparisonData.map((d, i) => <Cell key={i} fill={d.fill} />)}</Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="BNG % Gauge" className="bg-[#f5f6f8]">
              <div className="flex justify-center">
                <GaugeChart value={Math.min(bngPct, 50)} max={50} label={`${fmtPct(bngPct)} net gain`} />
              </div>
              <div className="mt-3 flex justify-center">
                <Badge
                  label={bngPct >= 10 ? "COMPLIANT (\u226510%)" : "NON-COMPLIANT (<10%)"}
                  color={bngPct >= 10 ? "bg-emerald-500/10 text-emerald-300" : "bg-red-500/10 text-red-300"}
                />
              </div>
            </Card>
          </div>
        </div>
      )}
    </Collapsible>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ══════════════════════════════════════════════════════════════════════════ */
const TABS = [
  { id: "sovereign", label: "Sovereign Climate Risk", icon: Globe },
  { id: "insurance", label: "Insurance Emissions", icon: ShieldCheck },
  { id: "agriculture", label: "Agriculture Expanded", icon: Leaf },
];

export default function SovereignEmissionsPage() {
  const [tab, setTab] = useState("sovereign");

  return (
    <div className="min-h-screen bg-[#f5f6f8] text-gray-700 p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Sovereign Emissions &amp; Sector Risk</h1>
        <p className="text-sm text-gray-500 mt-1">
          Sovereign climate creditworthiness, insurance-associated emissions (PCAF Part B), and agriculture expanded analytics.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-white rounded-xl border border-gray-200 p-1">
        {TABS.map(t => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${active
                ? "bg-gray-200 text-gray-800 border border-gray-200 shadow-sm"
                : "text-gray-500 hover:text-gray-600 hover:bg-gray-50 border border-transparent"}`}>
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {tab === "sovereign" && <SovereignPanel />}
      {tab === "insurance" && <InsuranceEmissionsPanel />}
      {tab === "agriculture" && <AgricultureExpandedPanel />}
    </div>
  );
}
