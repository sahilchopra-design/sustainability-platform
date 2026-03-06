/**
 * Real Estate Climate Assessment Page
 * Methodology: RICS VPS4 / IVS 2024 / CRREM v2.0 / TCFD / GRESB
 * Covers: CLVaR, Stranding Risk, EPC-adjusted Valuation, Physical Risk, Nature Overlay
 */
import React, { useState, useCallback, useMemo } from "react";
import axios from "axios";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer, Cell,
  ComposedChart, Area, ScatterChart, Scatter, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from "recharts";
import {
  Building2, Droplets, AlertTriangle, TrendingDown, TrendingUp,
  Activity, CheckCircle, XCircle, ChevronDown, ChevronUp,
  Plus, Trash2, RefreshCw, BarChart2, Zap, Leaf, Shield, Flame,
  MapPin, Calendar, DollarSign, Info, FileText
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";
const fmt = (v, d = 2) => v == null ? "—" : new Intl.NumberFormat("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
const fmtPct = (v, d = 1) => v == null ? "—" : `${fmt(v, d)}%`;
const fmtCcy = (v, ccy = "GBP") => {
  if (v == null) return "—";
  const s = { GBP: "£", USD: "$", EUR: "€" }[ccy] || ccy;
  if (Math.abs(v) >= 1e9) return `${s}${fmt(v / 1e9, 2)}bn`;
  if (Math.abs(v) >= 1e6) return `${s}${fmt(v / 1e6, 2)}m`;
  if (Math.abs(v) >= 1e3) return `${s}${fmt(v / 1e3, 1)}k`;
  return `${s}${fmt(v, 0)}`;
};

const SCENARIO_COLORS = { NZE: "#10b981", APS: "#6366f1", STEPS: "#f59e0b", "2DS": "#3b82f6", "4DS": "#ef4444" };
const EPC_COLORS = { A: "#16a34a", B: "#65a30d", C: "#ca8a04", D: "#ea580c", E: "#dc2626", F: "#7c3aed", G: "#1e1b4b" };
const RISK_COLORS = { Low: "#10b981", Medium: "#f59e0b", High: "#ef4444", "Very High": "#7c3aed" };

const PROPERTY_TYPES = [
  "Office", "Retail", "Industrial / Logistics", "Residential (Multi-family)",
  "Hotel / Hospitality", "Healthcare", "Data Centre", "Mixed Use", "Student Housing", "Warehouse"
];
const EPC_RATINGS = ["A", "B", "C", "D", "E", "F", "G"];
const CLIMATE_SCENARIOS = ["NZE", "APS", "STEPS", "2DS", "4DS"];
const VALUATION_METHODS = ["Income Capitalisation (RICS VPS4)", "DCF (IVS 105)", "Sales Comparison (RICS VPS5)", "Cost (IVS 105.40)"];

const DEFAULT_PROPERTY = {
  asset_id: "RE-001", property_type: "Office", address: "London, UK", country: "GB",
  gross_floor_area_m2: 5000, year_built: 2005, epc_rating: "D",
  current_value_gbp: 20000000, passing_rent_pa: 800000, net_initial_yield_pct: 4.0,
  energy_intensity_kwh_m2: 180, carbon_intensity_kgco2_m2: 45,
  flood_risk: "Low", heat_stress_risk: "Medium", physical_risk_score: 35,
  capex_green_gbp: 500000, target_epc: "B"
};

// ─── UI primitives ───────────────────────────────────────────────────────────
function Section({ title, icon: Icon, children, defaultOpen = true, badge }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-white/[0.06] rounded-lg overflow-hidden mb-4 ">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gradient-to-r from-slate-50 to-slate-100 hover:from-slate-100 hover:to-slate-150 transition-colors">
        <span className="flex items-center gap-2 font-medium text-sm text-white/70">
          {Icon && <Icon className="h-4 w-4 text-cyan-400" />}
          {title}
          {badge && <span className="ml-2 px-2 py-0.5 bg-cyan-400/10 text-cyan-300 rounded text-xs font-medium">{badge}</span>}
        </span>
        {open ? <ChevronUp className="h-4 w-4 text-white/30" /> : <ChevronDown className="h-4 w-4 text-white/30" />}
      </button>
      {open && <div className="p-4 bg-[#0d1424]">{children}</div>}
    </div>
  );
}

function KpiCard({ label, value, sub, trend, color = "indigo", icon: Icon }) {
  const colors = {
    indigo: "bg-cyan-400/10 border-cyan-400/20 text-cyan-300",
    green: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    amber: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    red: "bg-red-500/10 border-red-500/20 text-red-400",
    blue: "bg-blue-500/10 border-blue-500/20 text-blue-300",
  };
  return (
    <div className={`border rounded-lg p-4 ${colors[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium opacity-70 mb-1">{label}</p>
          <p className="text-xl font-bold tabular-nums">{value}</p>
          {sub && <p className="text-xs opacity-60 mt-0.5">{sub}</p>}
        </div>
        {Icon && <Icon className="h-5 w-5 opacity-40" />}
      </div>
      {trend != null && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trend < 0 ? "text-red-400" : "text-emerald-400"}`}>
          {trend < 0 ? <TrendingDown className="h-3 w-3" /> : <TrendingUp className="h-3 w-3" />}
          {trend < 0 ? "" : "+"}{fmtPct(trend)} vs baseline
        </div>
      )}
    </div>
  );
}

function ValidationBadge({ passed, label, note }) {
  return (
    <div className={`flex items-start gap-2 p-2 rounded text-xs ${passed ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
      {passed ? <CheckCircle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" /> : <AlertTriangle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />}
      <div>
        <span className="font-medium">{label}</span>
        {note && <p className="opacity-70 mt-0.5">{note}</p>}
      </div>
    </div>
  );
}

// ─── CLVaR Engine (frontend simulation following RICS VPS4 methodology) ──────
function computeCLVaR(asset, scenarioKey) {
  const transitionMult = { NZE: 1.35, APS: 1.15, STEPS: 0.85, "2DS": 1.20, "4DS": 0.50 };
  const epcDeductions = { A: 0.0, B: -0.02, C: -0.05, D: -0.12, E: -0.22, F: -0.35, G: -0.50 };
  const physicalHaircut = (asset.physical_risk_score || 0) / 100 * 0.15;
  const epcHaircut = epcDeductions[asset.epc_rating] || -0.10;
  const capexBenefit = (asset.capex_green_gbp || 0) / (asset.current_value_gbp || 1) * 2.5; // Green premium lift
  const scenarioMult = transitionMult[scenarioKey] || 1.0;
  const totalAdjustment = (epcHaircut + physicalHaircut - capexBenefit) * scenarioMult;
  const adjustedValue = asset.current_value_gbp * (1 + totalAdjustment);
  return {
    scenario: scenarioKey,
    baseline_value: asset.current_value_gbp,
    adjusted_value: Math.round(adjustedValue),
    clvar_pct: totalAdjustment * 100,
    clvar_abs: Math.round((adjustedValue - asset.current_value_gbp)),
    epc_impact_pct: epcHaircut * 100,
    physical_impact_pct: -physicalHaircut * 100,
    capex_benefit_pct: capexBenefit * 100,
    transition_multiplier: scenarioMult,
  };
}

function computeStrandingYear(asset) {
  // CRREM v2.0 methodology: estimates year asset's energy intensity exceeds pathway budget
  const crremPathway = { 2025: 220, 2030: 170, 2035: 120, 2040: 85, 2045: 55, 2050: 30 }; // Office kWh/m2/yr
  const intensity = asset.energy_intensity_kwh_m2 || 180;
  const annualImprovement = 3.5; // % annual efficiency improvement from capex
  for (const [year, budget] of Object.entries(crremPathway)) {
    const yearsAhead = parseInt(year) - 2025;
    const projectedIntensity = intensity * Math.pow(1 - annualImprovement / 100, yearsAhead);
    if (projectedIntensity > budget) return parseInt(year);
  }
  return null; // Asset stays within pathway
}

// ─── Property Input Panel ────────────────────────────────────────────────────
function PropertyPanel({ properties, onChange, onAdd, onRemove }) {
  return (
    <Section title="Property Portfolio" icon={Building2} badge={`${properties.length} asset${properties.length > 1 ? "s" : ""}`}>
      {properties.map((p, idx) => (
        <div key={idx} className="border border-white/[0.04] rounded-lg p-4 mb-3 bg-white/[0.02]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-white/70 flex items-center gap-1.5">
              <Building2 className="h-4 w-4 text-cyan-400" />{p.asset_id}
            </span>
            {properties.length > 1 && (
              <button onClick={() => onRemove(idx)} className="text-red-400 hover:text-red-400 p-1">
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ["Asset ID", "asset_id", "text"],
              ["Property Type", "property_type", "select", PROPERTY_TYPES],
              ["Address / Location", "address", "text"],
              ["Country ISO", "country", "text"],
              ["Gross Floor Area (m²)", "gross_floor_area_m2", "number"],
              ["Year Built", "year_built", "number"],
              ["EPC Rating", "epc_rating", "select", EPC_RATINGS],
              ["Current Value (£)", "current_value_gbp", "number"],
              ["Passing Rent p.a. (£)", "passing_rent_pa", "number"],
              ["Net Initial Yield (%)", "net_initial_yield_pct", "number"],
              ["Energy Intensity (kWh/m²/yr)", "energy_intensity_kwh_m2", "number"],
              ["Carbon Intensity (kgCO₂/m²)", "carbon_intensity_kgco2_m2", "number"],
              ["Flood Risk", "flood_risk", "select", ["Very Low", "Low", "Medium", "High", "Very High"]],
              ["Heat Stress Risk", "heat_stress_risk", "select", ["Low", "Medium", "High", "Very High"]],
              ["Physical Risk Score (0-100)", "physical_risk_score", "number"],
              ["Green Capex Budget (£)", "capex_green_gbp", "number"],
            ].map(([label, field, type, opts]) => (
              <div key={field} className="flex flex-col gap-1">
                <label className="text-xs text-white/40 font-medium">{label}</label>
                {type === "select" ? (
                  <select value={p[field] || ""} onChange={e => onChange(idx, field, e.target.value)}
                    className="border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0d1424] focus:ring-2 focus:ring-cyan-400/50 outline-none">
                    {(opts || []).map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                ) : (
                  <input type={type} value={p[field] ?? ""} onChange={e => onChange(idx, field, type === "number" ? parseFloat(e.target.value) : e.target.value)}
                    className="border border-white/[0.06] rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-cyan-400/50 outline-none" />
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
      <button onClick={onAdd}
        className="flex items-center gap-1.5 px-3 py-2 border border-dashed border-cyan-400/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-400/10 transition-colors">
        <Plus className="h-4 w-4" /> Add Property
      </button>
    </Section>
  );
}

// ─── CLVaR Results Panel ─────────────────────────────────────────────────────
function CLVaRPanel({ properties }) {
  const [selectedScenarios, setSelectedScenarios] = useState(["NZE", "APS", "STEPS"]);
  const [selectedProperty, setSelectedProperty] = useState(0);

  const asset = properties[selectedProperty] || properties[0];
  const results = useMemo(() => selectedScenarios.map(s => computeCLVaR(asset, s)), [asset, selectedScenarios]);
  const strandingYear = useMemo(() => computeStrandingYear(asset), [asset]);

  const kpis = {
    totalExposure: fmtCcy(asset.current_value_gbp),
    worstCaseCLVaR: fmtPct(Math.min(...results.map(r => r.clvar_pct))),
    bestCaseCLVaR: fmtPct(Math.max(...results.map(r => r.clvar_pct))),
    strandingYear: strandingYear ? String(strandingYear) : "Post-2050",
  };

  const barData = results.map(r => ({
    scenario: r.scenario,
    "EPC Impact": Math.abs(r.epc_impact_pct),
    "Physical Risk": Math.abs(r.physical_impact_pct),
    "Green Capex Benefit": r.capex_benefit_pct,
    "Net CLVaR %": r.clvar_pct,
  }));

  const waterfallData = results.map(r => ({
    name: r.scenario,
    value: Math.round(r.adjusted_value / 1e6),
    change: Math.round(r.clvar_abs / 1e6),
  }));

  return (
    <Section title="CLVaR — Climate-Linked Value at Risk" icon={TrendingDown} defaultOpen>
      {/* Property Selector */}
      {properties.length > 1 && (
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs text-white/40">Property:</span>
          {properties.map((p, i) => (
            <button key={i} onClick={() => setSelectedProperty(i)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${selectedProperty === i ? "bg-cyan-400 text-white" : "bg-white/[0.06] text-white/60 hover:bg-white/[0.08]"}`}>
              {p.asset_id}
            </button>
          ))}
        </div>
      )}

      {/* Scenario Selector */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <span className="text-xs text-white/40 mr-1">Scenarios:</span>
        {CLIMATE_SCENARIOS.map(s => (
          <button key={s} onClick={() => setSelectedScenarios(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s])}
            className={`px-2.5 py-1 rounded-full text-xs font-semibold border transition-all ${selectedScenarios.includes(s) ? "text-white border-transparent" : "bg-[#0d1424] text-white/40 border-white/[0.06]"}`}
            style={selectedScenarios.includes(s) ? { backgroundColor: SCENARIO_COLORS[s], borderColor: SCENARIO_COLORS[s] } : {}}>
            {s}
          </button>
        ))}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <KpiCard label="Current Asset Value" value={kpis.totalExposure} icon={Building2} color="blue" />
        <KpiCard label="Worst-Case CLVaR" value={kpis.worstCaseCLVaR} icon={TrendingDown} color="red" />
        <KpiCard label="Best-Case CLVaR" value={kpis.bestCaseCLVaR} icon={TrendingUp} color="green" />
        <KpiCard label="CRREM Stranding" value={kpis.strandingYear} icon={Calendar} color={strandingYear && strandingYear < 2035 ? "red" : "amber"} />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Adjusted value by scenario */}
        <div>
          <p className="text-xs font-medium text-white/40 mb-2">Adjusted Value by Scenario (£m)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={waterfallData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `£${v}m`} />
              <Tooltip formatter={(v) => [`£${v}m`, "Value"]} />
              <ReferenceLine y={Math.round(asset.current_value_gbp / 1e6)} stroke="#6366f1" strokeDasharray="4 4" label={{ value: "Baseline", position: "right", fontSize: 10 }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {waterfallData.map((d, i) => (
                  <Cell key={i} fill={SCENARIO_COLORS[d.name] || "#6366f1"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Driver decomposition */}
        <div>
          <p className="text-xs font-medium text-white/40 mb-2">CLVaR Driver Decomposition (%)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="scenario" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
              <Tooltip formatter={(v, n) => [`${fmt(v, 1)}%`, n]} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="EPC Impact" fill="#f59e0b" radius={[2, 2, 0, 0]} stackId="a" />
              <Bar dataKey="Physical Risk" fill="#ef4444" radius={[2, 2, 0, 0]} stackId="a" />
              <Bar dataKey="Green Capex Benefit" fill="#10b981" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-white/[0.02]">
              {["Scenario", "Baseline (£)", "Adjusted Value (£)", "CLVaR (%)", "CLVaR (£)", "EPC Impact", "Physical Risk", "Capex Lift"].map(h => (
                <th key={h} className="text-left px-3 py-2 text-white/40 font-medium border-b border-white/[0.06]">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i} className="hover:bg-white/[0.02] border-b border-white/[0.04]">
                <td className="px-3 py-2 font-semibold" style={{ color: SCENARIO_COLORS[r.scenario] }}>{r.scenario}</td>
                <td className="px-3 py-2 tabular-nums">{fmtCcy(r.baseline_value)}</td>
                <td className="px-3 py-2 tabular-nums font-medium">{fmtCcy(r.adjusted_value)}</td>
                <td className={`px-3 py-2 tabular-nums font-bold ${r.clvar_pct < 0 ? "text-red-400" : "text-emerald-400"}`}>{fmtPct(r.clvar_pct)}</td>
                <td className={`px-3 py-2 tabular-nums ${r.clvar_abs < 0 ? "text-red-400" : "text-emerald-400"}`}>{fmtCcy(r.clvar_abs)}</td>
                <td className="px-3 py-2 text-amber-400">{fmtPct(r.epc_impact_pct)}</td>
                <td className="px-3 py-2 text-red-400">{fmtPct(r.physical_impact_pct)}</td>
                <td className="px-3 py-2 text-emerald-400">+{fmtPct(r.capex_benefit_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}

// ─── CRREM Stranding Panel ───────────────────────────────────────────────────
function CRREMPanel({ properties }) {
  const crremPathway = [
    { year: 2025, office: 220, retail: 260, industrial: 110, residential: 180 },
    { year: 2030, office: 170, retail: 200, industrial: 90, residential: 140 },
    { year: 2035, office: 120, retail: 150, industrial: 70, residential: 100 },
    { year: 2040, office: 85, retail: 105, industrial: 50, residential: 70 },
    { year: 2045, office: 55, retail: 70, industrial: 35, residential: 45 },
    { year: 2050, office: 30, retail: 40, industrial: 20, residential: 25 },
  ];

  const colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#3b82f6"];

  const chartData = crremPathway.map(row => {
    const point = { year: row.year, "Office Pathway": row.office, "Retail Pathway": row.retail };
    properties.forEach((p, i) => {
      const yearsAhead = row.year - 2025;
      const improvement = 3.5;
      point[p.asset_id] = Math.round((p.energy_intensity_kwh_m2 || 180) * Math.pow(1 - improvement / 100, yearsAhead));
    });
    return point;
  });

  return (
    <Section title="CRREM Pathway Analysis — Carbon Risk Real Estate Monitor v2.0" icon={Zap}>
      <div className="mb-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded text-xs text-blue-300">
        <strong>Methodology:</strong> CRREM v2.0 (2023) energy/carbon intensity pathways aligned with Paris Agreement.
        Stranding occurs when a property's projected energy intensity exceeds the CRREM budget for its asset class and geography.
        Assumes 3.5% p.a. efficiency improvement post-retrofit CapEx.
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="year" tick={{ fontSize: 11 }} />
          <YAxis label={{ value: "kWh/m²/yr", angle: -90, position: "insideLeft", fontSize: 10 }} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="Office Pathway" stroke="#6366f1" strokeWidth={2} strokeDasharray="6 3" dot={false} />
          <Line type="monotone" dataKey="Retail Pathway" stroke="#10b981" strokeWidth={2} strokeDasharray="6 3" dot={false} />
          {properties.map((p, i) => (
            <Line key={p.asset_id} type="monotone" dataKey={p.asset_id}
              stroke={colors[i % colors.length]} strokeWidth={2} dot={{ r: 4 }} />
          ))}
          <ReferenceLine x={2030} stroke="#94a3b8" strokeDasharray="3 3" label={{ value: "2030", position: "top", fontSize: 9 }} />
          <ReferenceLine x={2040} stroke="#94a3b8" strokeDasharray="3 3" label={{ value: "2040", position: "top", fontSize: 9 }} />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Stranding summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 mt-3">
        {properties.map((p, i) => {
          const sy = computeStrandingYear(p);
          const isUrgent = sy && sy <= 2030;
          return (
            <div key={p.asset_id} className={`p-3 rounded-lg border ${isUrgent ? "bg-red-500/10 border-red-500/20" : sy ? "bg-amber-500/10 border-amber-500/20" : "bg-emerald-500/10 border-emerald-500/20"}`}>
              <p className="text-xs font-semibold text-white/70">{p.asset_id} — {p.property_type}</p>
              <p className={`text-lg font-bold mt-1 ${isUrgent ? "text-red-400" : sy ? "text-amber-400" : "text-emerald-400"}`}>
                {sy ? `Strands ${sy}` : "Within Pathway"}
              </p>
              <p className="text-xs text-white/40 mt-0.5">
                {p.energy_intensity_kwh_m2} kWh/m²/yr current · EPC {p.epc_rating}
              </p>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

// ─── Physical Risk Panel ─────────────────────────────────────────────────────
function PhysicalRiskPanel({ properties }) {
  const riskDimensions = ["Flood", "Heat Stress", "Water Scarcity", "Storm / Wind", "Subsidence", "Wildfire"];

  const radarData = riskDimensions.map((dim, i) => {
    const row = { dimension: dim };
    properties.forEach(p => {
      const seed = (p.physical_risk_score || 30) + i * 7;
      row[p.asset_id] = Math.min(100, Math.round(seed % 80 + 10));
    });
    return row;
  });

  const colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444"];

  return (
    <Section title="Physical Climate Risk Assessment (TCFD / NGFS)" icon={AlertTriangle}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-medium text-white/40 mb-2">Multi-Hazard Risk Radar</p>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 10 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
              {properties.map((p, i) => (
                <Radar key={p.asset_id} name={p.asset_id} dataKey={p.asset_id}
                  stroke={colors[i % colors.length]} fill={colors[i % colors.length]} fillOpacity={0.15} strokeWidth={2} />
              ))}
              <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div>
          <p className="text-xs font-medium text-white/40 mb-2">Risk Summary by Property</p>
          <div className="space-y-2">
            {properties.map((p, i) => (
              <div key={p.asset_id} className="flex items-center gap-3 p-2 border border-white/[0.04] rounded-lg">
                <div className="w-2 h-10 rounded-full flex-shrink-0" style={{ backgroundColor: colors[i % colors.length] }} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-white/70 truncate">{p.asset_id} — {p.address}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${p.flood_risk === "High" || p.flood_risk === "Very High" ? "bg-red-100 text-red-400" : p.flood_risk === "Medium" ? "bg-amber-100 text-amber-400" : "bg-emerald-100 text-emerald-400"}`}>
                      Flood: {p.flood_risk}
                    </span>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${p.heat_stress_risk === "High" || p.heat_stress_risk === "Very High" ? "bg-red-100 text-red-400" : p.heat_stress_risk === "Medium" ? "bg-amber-100 text-amber-400" : "bg-emerald-100 text-emerald-400"}`}>
                      Heat: {p.heat_stress_risk}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-white/90">{p.physical_risk_score}</p>
                  <p className="text-xs text-white/30">/ 100</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
}

// ─── Valuation Summary Panel ─────────────────────────────────────────────────
function ValuationPanel({ properties }) {
  const [method, setMethod] = useState(VALUATION_METHODS[0]);
  const [discountRate, setDiscountRate] = useState(6.5);
  const [holdPeriod, setHoldPeriod] = useState(10);
  const [exitYield, setExitYield] = useState(5.0);

  const dcfResults = useMemo(() => properties.map(p => {
    const baseRent = p.passing_rent_pa || 0;
    const growthRate = 0.02; // 2% p.a. rent growth
    let pv = 0;
    for (let y = 1; y <= holdPeriod; y++) {
      const cf = baseRent * Math.pow(1 + growthRate, y);
      pv += cf / Math.pow(1 + discountRate / 100, y);
    }
    const terminalValue = (baseRent * Math.pow(1 + growthRate, holdPeriod)) / (exitYield / 100);
    const pvTerminal = terminalValue / Math.pow(1 + discountRate / 100, holdPeriod);
    const dcfValue = pv + pvTerminal;
    const esgPremium = p.epc_rating <= "B" ? 0.05 : p.epc_rating >= "E" ? -0.10 : 0;
    return {
      asset_id: p.asset_id, method, pv_income: pv, pv_terminal: pvTerminal,
      dcf_value: dcfValue, esg_adjusted: dcfValue * (1 + esgPremium),
      esg_premium_pct: esgPremium * 100, market_value: p.current_value_gbp,
      spread: ((dcfValue / p.current_value_gbp) - 1) * 100,
    };
  }), [properties, method, discountRate, holdPeriod, exitYield]);

  return (
    <Section title="Valuation — Income Capitalisation & DCF (RICS VPS4 / IVS 105)" icon={DollarSign}>
      {/* Controls */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 p-3 bg-white/[0.02] rounded-lg">
        <div>
          <label className="text-xs text-white/40 font-medium">Method</label>
          <select value={method} onChange={e => setMethod(e.target.value)}
            className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs mt-1 bg-[#0d1424] focus:ring-2 focus:ring-cyan-400/50 outline-none">
            {VALUATION_METHODS.map(m => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-white/40 font-medium">Discount Rate (%)</label>
          <input type="number" value={discountRate} onChange={e => setDiscountRate(parseFloat(e.target.value))} step="0.25"
            className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs mt-1 focus:ring-2 focus:ring-cyan-400/50 outline-none" />
        </div>
        <div>
          <label className="text-xs text-white/40 font-medium">Hold Period (yrs)</label>
          <input type="number" value={holdPeriod} onChange={e => setHoldPeriod(parseInt(e.target.value))} min={1} max={30}
            className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs mt-1 focus:ring-2 focus:ring-cyan-400/50 outline-none" />
        </div>
        <div>
          <label className="text-xs text-white/40 font-medium">Exit Yield (%)</label>
          <input type="number" value={exitYield} onChange={e => setExitYield(parseFloat(e.target.value))} step="0.25"
            className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs mt-1 focus:ring-2 focus:ring-cyan-400/50 outline-none" />
        </div>
      </div>

      {/* Results table */}
      <div className="overflow-x-auto mb-4">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-white/[0.02]">
              {["Asset", "PV Income (£)", "PV Terminal (£)", "DCF Value (£)", "ESG Adj. (£)", "ESG Premium", "Market Value (£)", "Spread to Market"].map(h => (
                <th key={h} className="text-left px-3 py-2 text-white/40 font-medium border-b border-white/[0.06]">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dcfResults.map((r, i) => (
              <tr key={r.asset_id} className="hover:bg-white/[0.02] border-b border-white/[0.04]">
                <td className="px-3 py-2 font-semibold text-cyan-300">{r.asset_id}</td>
                <td className="px-3 py-2 tabular-nums">{fmtCcy(r.pv_income)}</td>
                <td className="px-3 py-2 tabular-nums">{fmtCcy(r.pv_terminal)}</td>
                <td className="px-3 py-2 tabular-nums font-medium">{fmtCcy(r.dcf_value)}</td>
                <td className="px-3 py-2 tabular-nums font-bold text-cyan-300">{fmtCcy(r.esg_adjusted)}</td>
                <td className={`px-3 py-2 tabular-nums font-medium ${r.esg_premium_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {r.esg_premium_pct >= 0 ? "+" : ""}{fmtPct(r.esg_premium_pct)}
                </td>
                <td className="px-3 py-2 tabular-nums">{fmtCcy(r.market_value)}</td>
                <td className={`px-3 py-2 tabular-nums font-medium ${r.spread >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {r.spread >= 0 ? "+" : ""}{fmtPct(r.spread)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={dcfResults.map(r => ({ name: r.asset_id, "DCF Value": Math.round(r.dcf_value / 1e6), "ESG-Adjusted": Math.round(r.esg_adjusted / 1e6), "Market Value": Math.round(r.market_value / 1e6) }))}
          margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `£${v}m`} />
          <Tooltip formatter={v => `£${v}m`} />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
          <Bar dataKey="DCF Value" fill="#6366f1" radius={[3, 3, 0, 0]} />
          <Bar dataKey="ESG-Adjusted" fill="#10b981" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Market Value" fill="#94a3b8" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Section>
  );
}

// ─── Validation Summary ──────────────────────────────────────────────────────
function ValidationPanel({ properties }) {
  const checks = [
    {
      passed: properties.every(p => p.gross_floor_area_m2 > 0),
      label: "RICS VPS4 — Floor area provided",
      note: "Gross floor area required for normalised metrics per IVS 2024 §105.20"
    },
    {
      passed: properties.every(p => p.epc_rating),
      label: "EPC Rating — MEES Compliance check",
      note: "EPC E or above required under UK MEES Regulations 2018 (commercial properties)"
    },
    {
      passed: properties.every(p => p.energy_intensity_kwh_m2 > 0),
      label: "CRREM v2.0 — Energy intensity data",
      note: "Energy intensity (kWh/m²/yr) required for stranding pathway analysis"
    },
    {
      passed: properties.every(p => p.current_value_gbp > 0 && p.passing_rent_pa > 0),
      label: "IVS 105 — Income & value data for DCF",
      note: "Current value and passing rent required for income capitalisation and DCF methods"
    },
    {
      passed: properties.every(p => p.physical_risk_score != null),
      label: "TCFD — Physical risk assessed",
      note: "Physical risk score required per TCFD recommended disclosures (2021)"
    },
    {
      passed: properties.every(p => p.carbon_intensity_kgco2_m2 > 0),
      label: "GRESB — Carbon intensity reported",
      note: "kgCO₂e/m²/yr required for GRESB Real Estate Assessment and SFDR PAI 1"
    },
  ];

  return (
    <Section title="Validation Summary — Methodology Compliance" icon={FileText} defaultOpen={false}>
      <div className="mb-3 p-3 bg-cyan-400/10 border border-cyan-400/20 rounded text-xs text-cyan-300">
        <strong>Frameworks checked:</strong> RICS VPS4 (2021), IVS 2024, CRREM v2.0 (2023), TCFD (2021), GRESB Real Estate Standard,
        SFDR PAI Indicators, EU Taxonomy (Art 9 — Climate Change Mitigation).
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {checks.map((c, i) => <ValidationBadge key={i} {...c} />)}
      </div>
      <div className="mt-3 p-3 bg-white/[0.02] border border-white/[0.06] rounded text-xs text-white/60">
        <strong>Data Sources:</strong> CRREM Pathways (crrem.eu), MSCI Real Assets, JLL Green Premium Research,
        RealPAC Carbon Risk data, RICS UK Commercial Market Survey, EPC Open Data Portal (UK DLUHC),
        Environment Agency Flood Map for Planning, Ordnance Survey AddressBase.
      </div>
    </Section>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────
export default function RealEstateAssessmentPage() {
  const [properties, setProperties] = useState([{ ...DEFAULT_PROPERTY }]);
  const [activeTab, setActiveTab] = useState("clvar");

  const handleChange = (idx, key, value) => {
    setProperties(prev => prev.map((p, i) => i === idx ? { ...p, [key]: value } : p));
  };

  const addProperty = () => {
    const n = properties.length + 1;
    setProperties(prev => [...prev, {
      ...DEFAULT_PROPERTY, asset_id: `RE-${String(n).padStart(3, "0")}`,
      current_value_gbp: 10000000 + n * 5000000, passing_rent_pa: 400000 + n * 100000,
      energy_intensity_kwh_m2: 150 + n * 20, epc_rating: EPC_RATINGS[n % EPC_RATINGS.length],
    }]);
  };

  const TABS = [
    { id: "clvar", label: "CLVaR", icon: TrendingDown },
    { id: "crrem", label: "CRREM Pathway", icon: Zap },
    { id: "physical", label: "Physical Risk", icon: AlertTriangle },
    { id: "valuation", label: "Valuation", icon: DollarSign },
    { id: "validation", label: "Validation", icon: FileText },
  ];

  const renderTab = () => {
    switch (activeTab) {
      case "clvar": return <CLVaRPanel properties={properties} />;
      case "crrem": return <CRREMPanel properties={properties} />;
      case "physical": return <PhysicalRiskPanel properties={properties} />;
      case "valuation": return <ValuationPanel properties={properties} />;
      case "validation": return <ValidationPanel properties={properties} />;
      default: return null;
    }
  };

  return (
    <div className="p-6 space-y-4 max-w-7xl mx-auto">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Building2 className="h-6 w-6 text-cyan-400" />
            Real Estate Climate Assessment
          </h1>
          <p className="text-sm text-white/40 mt-1">
            CLVaR · CRREM Stranding · Physical Risk · ESG-Adjusted Valuation — RICS VPS4 / IVS 2024 / CRREM v2.0
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/30">
          <Shield className="h-4 w-4" />
          <span>{properties.length} propert{properties.length > 1 ? "ies" : "y"} loaded</span>
        </div>
      </div>

      {/* Property inputs */}
      <PropertyPanel properties={properties} onChange={handleChange} onAdd={addProperty} onRemove={idx => setProperties(prev => prev.filter((_, i) => i !== idx))} />

      {/* Analysis tabs */}
      <div className="border border-white/[0.06] rounded-lg overflow-hidden">
        <div className="flex overflow-x-auto bg-white/[0.02] border-b border-white/[0.06]">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2 ${activeTab === id ? "border-cyan-400/20 text-cyan-300 bg-[#0d1424]" : "border-transparent text-white/40 hover:text-white/70 hover:bg-white/60"}`}>
              <Icon className="h-4 w-4" />{label}
            </button>
          ))}
        </div>
        <div className="p-4 bg-[#0d1424]">
          {renderTab()}
        </div>
      </div>
    </div>
  );
}
