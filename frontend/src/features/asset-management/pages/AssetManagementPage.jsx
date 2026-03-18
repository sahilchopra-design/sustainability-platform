/**
 * Asset Management Page
 * Tabbed interface for AM Engine (6 sub-modules) and Factor Overlay Engine (12 overlays).
 * Dark theme: bg-white, border-gray-200, white/70 text.
 */
import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, LineChart, Line, PieChart, Pie, Legend,
} from "recharts";
import {
  ChevronDown, ChevronRight, Loader2, AlertCircle, TrendingUp,
  Thermometer, Shield, BarChart3, PieChart as PieIcon, Layers,
  Sliders, ArrowRightLeft, Building2, Zap, Tractor, Globe2,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";

/* ── Shared helpers ──────────────────────────────────────────────────── */

function KPI({ label, value, sub, color = "text-gray-900" }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-[10px] text-gray-500 mb-1 truncate">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function Section({ title, subtitle, open, onToggle, children }) {
  return (
    <div className="border border-gray-200 rounded-xl bg-white">
      <button onClick={onToggle} className="w-full flex items-center justify-between px-5 py-3.5 text-left">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-[10px] text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        {open ? <ChevronDown className="h-4 w-4 text-gray-500" /> : <ChevronRight className="h-4 w-4 text-gray-500" />}
      </button>
      {open && <div className="px-5 pb-5 border-t border-gray-200 pt-4">{children}</div>}
    </div>
  );
}

function Btn({ onClick, loading, children, className = "" }) {
  return (
    <button
      onClick={onClick} disabled={loading}
      className={`bg-[#164E8A] hover:bg-[#12407A] disabled:opacity-50 text-[#ffffff] text-sm font-semibold px-6 py-2 rounded-lg shadow transition-colors flex items-center gap-2 ${className}`}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}

function ErrorBox({ msg }) {
  if (!msg) return null;
  return (
    <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-400/20 rounded-lg text-xs text-red-300">
      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" /> <span>{msg}</span>
    </div>
  );
}

function Input({ label, value, onChange, type = "text", placeholder = "" }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <input
        type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-[#f5f6f8] text-gray-700 focus:outline-none focus:ring-2 focus:ring-black/50"
      />
    </div>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <select
        value={value} onChange={e => onChange(e.target.value)}
        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-[#f5f6f8] text-gray-700 focus:outline-none focus:ring-2 focus:ring-black/50"
      >
        {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
      </select>
    </div>
  );
}

const CHART_COLORS = ["#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#ec4899", "#3b82f6", "#14b8a6"];
const tooltipStyle = { background: "#ffffff", border: "1px solid #ffffff10", borderRadius: 8, fontSize: 11 };

/* ══════════════════════════════════════════════════════════════════════
   TAB 1 — AM ENGINE PANEL
   ══════════════════════════════════════════════════════════════════════ */

function AMEnginePanel() {
  const [openSections, setOpenSections] = useState({ esg: true });
  const toggle = key => setOpenSections(p => ({ ...p, [key]: !p[key] }));

  /* ── 1. ESG Attribution ────────────────────────────────────────────── */
  const [esgLoading, setEsgLoading] = useState(false);
  const [esgError, setEsgError] = useState("");
  const [esgResult, setEsgResult] = useState(null);
  const [esgBenchmark, setEsgBenchmark] = useState("50");

  const runEsgAttribution = useCallback(async () => {
    setEsgLoading(true); setEsgError("");
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/am/esg-attribution`, {
        holdings: [
          { security_id: "AAPL", name: "Apple", weight_pct: 20, sector: "technology", esg_score: 72, carbon_intensity_tco2e_m: 45, return_pct: 12, benchmark_weight_pct: 15, benchmark_return_pct: 10, rating: "AA" },
          { security_id: "XOM", name: "ExxonMobil", weight_pct: 15, sector: "energy", esg_score: 28, carbon_intensity_tco2e_m: 420, return_pct: 8, benchmark_weight_pct: 18, benchmark_return_pct: 9, rating: "A" },
          { security_id: "MSFT", name: "Microsoft", weight_pct: 25, sector: "technology", esg_score: 80, carbon_intensity_tco2e_m: 30, return_pct: 15, benchmark_weight_pct: 20, benchmark_return_pct: 13, rating: "AAA" },
          { security_id: "JPM", name: "JPMorgan", weight_pct: 20, sector: "financials", esg_score: 55, carbon_intensity_tco2e_m: 90, return_pct: 10, benchmark_weight_pct: 22, benchmark_return_pct: 11, rating: "A" },
          { security_id: "NEE", name: "NextEra Energy", weight_pct: 20, sector: "utilities", esg_score: 68, carbon_intensity_tco2e_m: 110, return_pct: 14, benchmark_weight_pct: 25, benchmark_return_pct: 12, rating: "A" },
        ],
        benchmark_esg_score: parseFloat(esgBenchmark) || 50,
      });
      setEsgResult(data);
    } catch (e) { setEsgError(e.response?.data?.detail || e.message); }
    setEsgLoading(false);
  }, [esgBenchmark]);

  /* ── 2. Paris Alignment ────────────────────────────────────────────── */
  const [parisLoading, setParisLoading] = useState(false);
  const [parisError, setParisError] = useState("");
  const [parisResult, setParisResult] = useState(null);
  const [parisPathway, setParisPathway] = useState("1.5C");

  const runParis = useCallback(async () => {
    setParisLoading(true); setParisError("");
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/am/paris-alignment`, {
        holdings: [
          { security_id: "AAPL", name: "Apple", weight_pct: 25, sector: "technology", esg_score: 72, carbon_intensity_tco2e_m: 45, return_pct: 0, benchmark_weight_pct: 0, benchmark_return_pct: 0, rating: "AA" },
          { security_id: "XOM", name: "ExxonMobil", weight_pct: 20, sector: "energy", esg_score: 28, carbon_intensity_tco2e_m: 420, return_pct: 0, benchmark_weight_pct: 0, benchmark_return_pct: 0, rating: "A" },
          { security_id: "NEE", name: "NextEra", weight_pct: 30, sector: "utilities", esg_score: 68, carbon_intensity_tco2e_m: 110, return_pct: 0, benchmark_weight_pct: 0, benchmark_return_pct: 0, rating: "A" },
          { security_id: "JPM", name: "JPMorgan", weight_pct: 25, sector: "financials", esg_score: 55, carbon_intensity_tco2e_m: 90, return_pct: 0, benchmark_weight_pct: 0, benchmark_return_pct: 0, rating: "A" },
        ],
        target_pathway: parisPathway,
      });
      setParisResult(data);
    } catch (e) { setParisError(e.response?.data?.detail || e.message); }
    setParisLoading(false);
  }, [parisPathway]);

  /* ── 3. Green Bond Screening ───────────────────────────────────────── */
  const [gbLoading, setGbLoading] = useState(false);
  const [gbError, setGbError] = useState("");
  const [gbResult, setGbResult] = useState(null);

  const runGreenBond = useCallback(async () => {
    setGbLoading(true); setGbError("");
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/am/green-bond-screening`, {
        bonds: [
          { bond_id: "GB-001", issuer_name: "EIB", isin: "XS1234567890", rating: "AAA", sector: "development_bank", use_of_proceeds: ["renewable_energy", "energy_efficiency"], taxonomy_aligned_pct: 92, external_review: true, impact_reporting: true, dnsh_assessed: true, coupon_bps: 150, conventional_spread_bps: 180 },
          { bond_id: "GB-002", issuer_name: "Enel", isin: "XS9876543210", rating: "BBB", sector: "utilities", use_of_proceeds: ["renewable_energy"], taxonomy_aligned_pct: 65, external_review: true, impact_reporting: false, dnsh_assessed: false, coupon_bps: 280, conventional_spread_bps: 310 },
          { bond_id: "GB-003", issuer_name: "GreenwashCo", isin: "XS1111111111", rating: "BB", sector: "industrials", use_of_proceeds: ["general_corporate"], taxonomy_aligned_pct: 10, external_review: false, impact_reporting: false, dnsh_assessed: false, coupon_bps: 420, conventional_spread_bps: 400 },
        ],
      });
      setGbResult(data);
    } catch (e) { setGbError(e.response?.data?.detail || e.message); }
    setGbLoading(false);
  }, []);

  /* ── 4. Climate Spreads ────────────────────────────────────────────── */
  const [csLoading, setCsLoading] = useState(false);
  const [csError, setCsError] = useState("");
  const [csResult, setCsResult] = useState(null);
  const [csCarbon, setCsCarbon] = useState("80");

  const runClimateSpreads = useCallback(async () => {
    setCsLoading(true); setCsError("");
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/am/climate-spreads`, {
        issuers: [
          { issuer_id: "ISS-01", name: "Shell", sector: "energy", rating: "A", base_spread_bps: 120, carbon_intensity_tco2e_m: 350, transition_risk_score: 72, revenue_from_fossils_pct: 65, capex_green_pct: 12, sbti_committed: false },
          { issuer_id: "ISS-02", name: "Orsted", sector: "utilities", rating: "BBB", base_spread_bps: 95, carbon_intensity_tco2e_m: 40, transition_risk_score: 15, revenue_from_fossils_pct: 2, capex_green_pct: 85, sbti_committed: true },
          { issuer_id: "ISS-03", name: "ArcelorMittal", sector: "materials", rating: "BBB", base_spread_bps: 180, carbon_intensity_tco2e_m: 520, transition_risk_score: 60, revenue_from_fossils_pct: 0, capex_green_pct: 8, sbti_committed: false },
        ],
        carbon_price_eur: parseFloat(csCarbon) || 80,
        warming_scenario: "2C",
      });
      setCsResult(data);
    } catch (e) { setCsError(e.response?.data?.detail || e.message); }
    setCsLoading(false);
  }, [csCarbon]);

  /* ── 5. LP Analytics ───────────────────────────────────────────────── */
  const [lpLoading, setLpLoading] = useState(false);
  const [lpError, setLpError] = useState("");
  const [lpResult, setLpResult] = useState(null);

  const runLP = useCallback(async () => {
    setLpLoading(true); setLpError("");
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/am/lp-analytics`, {
        fund_aum_eur: 500000000,
        investors: [
          { investor_id: "LP-1", name: "CalPERS", commitment_eur: 150000000, investor_type: "pension", redemption_notice_days: 90, lock_up_remaining_months: 12, historical_redemption_rate: 0.02 },
          { investor_id: "LP-2", name: "Tiger Global", commitment_eur: 100000000, investor_type: "hedge_fund", redemption_notice_days: 30, lock_up_remaining_months: 0, historical_redemption_rate: 0.15 },
          { investor_id: "LP-3", name: "Norway SWF", commitment_eur: 200000000, investor_type: "sovereign_wealth", redemption_notice_days: 180, lock_up_remaining_months: 24, historical_redemption_rate: 0.01 },
          { investor_id: "LP-4", name: "Family Office A", commitment_eur: 50000000, investor_type: "family_office", redemption_notice_days: 60, lock_up_remaining_months: 6, historical_redemption_rate: 0.08 },
        ],
        liquid_assets_pct: 30,
        side_pocket_pct: 5,
      });
      setLpResult(data);
    } catch (e) { setLpError(e.response?.data?.detail || e.message); }
    setLpLoading(false);
  }, []);

  /* ── 6. ESG Optimisation ───────────────────────────────────────────── */
  const [optLoading, setOptLoading] = useState(false);
  const [optError, setOptError] = useState("");
  const [optResult, setOptResult] = useState(null);
  const [optMinESG, setOptMinESG] = useState("40");

  const runOptimise = useCallback(async () => {
    setOptLoading(true); setOptError("");
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/am/optimise`, {
        holdings: [
          { security_id: "AAPL", name: "Apple", weight_pct: 20, sector: "technology", esg_score: 72, carbon_intensity_tco2e_m: 45, return_pct: 12, benchmark_weight_pct: 15, benchmark_return_pct: 10, rating: "AA" },
          { security_id: "XOM", name: "ExxonMobil", weight_pct: 15, sector: "energy", esg_score: 28, carbon_intensity_tco2e_m: 420, return_pct: 8, benchmark_weight_pct: 18, benchmark_return_pct: 9, rating: "A" },
          { security_id: "MSFT", name: "Microsoft", weight_pct: 25, sector: "technology", esg_score: 80, carbon_intensity_tco2e_m: 30, return_pct: 15, benchmark_weight_pct: 20, benchmark_return_pct: 13, rating: "AAA" },
          { security_id: "JPM", name: "JPMorgan", weight_pct: 20, sector: "financials", esg_score: 55, carbon_intensity_tco2e_m: 90, return_pct: 10, benchmark_weight_pct: 22, benchmark_return_pct: 11, rating: "A" },
          { security_id: "NEE", name: "NextEra", weight_pct: 20, sector: "utilities", esg_score: 68, carbon_intensity_tco2e_m: 110, return_pct: 14, benchmark_weight_pct: 25, benchmark_return_pct: 12, rating: "A" },
        ],
        constraints: { min_esg_score: parseFloat(optMinESG) || 40, max_carbon_intensity: 200, excluded_sectors: [], max_single_weight_pct: 30, max_sector_weight_pct: 50, esg_tilt_strength: 0.6 },
        risk_free_rate: 3.5,
      });
      setOptResult(data);
    } catch (e) { setOptError(e.response?.data?.detail || e.message); }
    setOptLoading(false);
  }, [optMinESG]);

  /* ── Render ────────────────────────────────────────────────────────── */
  return (
    <div className="space-y-4">
      {/* 1 — ESG Attribution */}
      <Section title="ESG Attribution" subtitle="Fama-French + ESG factor model, Brinson selection/allocation" open={!!openSections.esg} onToggle={() => toggle("esg")}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Input label="Benchmark ESG Score" value={esgBenchmark} onChange={setEsgBenchmark} type="number" placeholder="50" />
        </div>
        <Btn onClick={runEsgAttribution} loading={esgLoading}>Run ESG Attribution</Btn>
        <ErrorBox msg={esgError} />
        {esgResult && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KPI label="Active Return" value={`${esgResult.active_return_bps?.toFixed(0) ?? "--"} bps`} color="text-gray-700" />
              <KPI label="ESG Quality Contrib." value={`${esgResult.esg_quality_contribution_bps?.toFixed(0) ?? "--"} bps`} color="text-emerald-400" />
              <KPI label="Portfolio ESG" value={esgResult.portfolio_esg_score?.toFixed(1) ?? "--"} color="text-purple-400" />
              <KPI label="Tracking Error" value={`${esgResult.tracking_error_bps?.toFixed(0) ?? "--"} bps`} />
            </div>
            {esgResult.brinson_attribution && (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={esgResult.brinson_attribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                  <XAxis dataKey="sector" tick={{ fontSize: 9, fill: "#ffffff60" }} />
                  <YAxis tick={{ fontSize: 9, fill: "#ffffff60" }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="selection_bps" name="Selection (bps)" fill="#06b6d4" radius={[3,3,0,0]} />
                  <Bar dataKey="allocation_bps" name="Allocation (bps)" fill="#8b5cf6" radius={[3,3,0,0]} />
                  <Legend wrapperStyle={{ fontSize: 10, color: "#ffffff60" }} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </Section>

      {/* 2 — Paris Alignment */}
      <Section title="Paris Alignment" subtitle="PACTA temperature scoring and sector trajectories" open={!!openSections.paris} onToggle={() => toggle("paris")}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Select label="Target Pathway" value={parisPathway} onChange={setParisPathway} options={[{ v: "1.5C", l: "1.5 C" }, { v: "2C", l: "Well Below 2 C" }, { v: "3C", l: "Current Policies ~3 C" }]} />
        </div>
        <Btn onClick={runParis} loading={parisLoading}>Run Paris Alignment</Btn>
        <ErrorBox msg={parisError} />
        {parisResult && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <KPI label="Portfolio Temperature" value={`${parisResult.portfolio_temperature_c?.toFixed(2) ?? "--"} C`} color={parisResult.portfolio_temperature_c <= 1.5 ? "text-emerald-400" : parisResult.portfolio_temperature_c <= 2 ? "text-amber-400" : "text-red-400"} />
              <KPI label="Target" value={`${parisResult.target_temperature_c?.toFixed(1) ?? "--"} C`} color="text-gray-700" />
              <KPI label="Alignment Gap" value={`${parisResult.alignment_gap_c?.toFixed(2) ?? "--"} C`} color="text-amber-400" />
              <KPI label="Aligned Weight" value={`${parisResult.aligned_weight_pct?.toFixed(1) ?? "--"}%`} color="text-emerald-400" />
              <KPI label="WACI" value={`${parisResult.weighted_carbon_intensity?.toFixed(0) ?? "--"} tCO2e/$M`} />
            </div>
            {parisResult.sector_temperatures && (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(parisResult.sector_temperatures).map(([s, t]) => ({ sector: s, temp: t }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                  <XAxis dataKey="sector" tick={{ fontSize: 9, fill: "#ffffff60" }} />
                  <YAxis tick={{ fontSize: 9, fill: "#ffffff60" }} domain={[0, 4]} />
                  <Tooltip contentStyle={tooltipStyle} formatter={v => [`${v.toFixed(2)} C`]} />
                  <Bar dataKey="temp" name="Temperature (C)" radius={[3,3,0,0]}>
                    {Object.values(parisResult.sector_temperatures).map((t, i) => (
                      <Cell key={i} fill={t <= 1.5 ? "#10b981" : t <= 2 ? "#f59e0b" : "#ef4444"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </Section>

      {/* 3 — Green Bond Screening */}
      <Section title="Green Bond Screening" subtitle="ICMA GBS / EU GBS 2023/2631 compliance, greenium, DNSH" open={!!openSections.gb} onToggle={() => toggle("gb")}>
        <Btn onClick={runGreenBond} loading={gbLoading}>Screen Sample Bonds</Btn>
        <ErrorBox msg={gbError} />
        {gbResult && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  {["Bond", "Issuer", "ICMA", "EU GBS", "Greenium (bps)", "DNSH", "Score"].map(h => (
                    <th key={h} className="text-left py-2 px-3 text-gray-500 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {gbResult.map((b, i) => (
                  <tr key={i} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="py-2 px-3 text-gray-700 font-medium">{b.bond_id}</td>
                    <td className="py-2 px-3 text-gray-600">{b.issuer_name}</td>
                    <td className="py-2 px-3">{b.icma_eligible ? <span className="text-emerald-400">Pass</span> : <span className="text-red-400">Fail</span>}</td>
                    <td className="py-2 px-3">{b.eu_gbs_eligible ? <span className="text-emerald-400">Pass</span> : <span className="text-red-400">Fail</span>}</td>
                    <td className="py-2 px-3 text-gray-700 font-bold">{b.greenium_bps?.toFixed(1) ?? "--"}</td>
                    <td className="py-2 px-3">{b.dnsh_pass ? <span className="text-emerald-400">OK</span> : <span className="text-amber-400">N/A</span>}</td>
                    <td className="py-2 px-3 text-gray-800 font-bold">{b.composite_score?.toFixed(0) ?? "--"}/100</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* 4 — Climate Spreads */}
      <Section title="Climate-Adjusted Spreads" subtitle="Transition risk spread delta and migration probability" open={!!openSections.cs} onToggle={() => toggle("cs")}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Input label="Carbon Price (EUR/tCO2e)" value={csCarbon} onChange={setCsCarbon} type="number" placeholder="80" />
        </div>
        <Btn onClick={runClimateSpreads} loading={csLoading}>Calculate Climate Spreads</Btn>
        <ErrorBox msg={csError} />
        {csResult && Array.isArray(csResult) && (
          <div className="mt-4 space-y-4">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={csResult.map(r => ({ name: r.name || r.issuer_id, base: r.base_spread_bps, delta: r.climate_spread_delta_bps, adjusted: r.adjusted_spread_bps }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#ffffff60" }} />
                <YAxis tick={{ fontSize: 9, fill: "#ffffff60" }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="base" name="Base Spread" fill="#3b82f6" radius={[3,3,0,0]} />
                <Bar dataKey="delta" name="Climate Delta" fill="#ef4444" radius={[3,3,0,0]} />
                <Bar dataKey="adjusted" name="Adjusted Spread" fill="#f59e0b" radius={[3,3,0,0]} />
                <Legend wrapperStyle={{ fontSize: 10, color: "#ffffff60" }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Section>

      {/* 5 — LP Analytics */}
      <Section title="LP Analytics" subtitle="HHI concentration, LCR, redemption stress testing" open={!!openSections.lp} onToggle={() => toggle("lp")}>
        <Btn onClick={runLP} loading={lpLoading}>Run LP Analytics</Btn>
        <ErrorBox msg={lpError} />
        {lpResult && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KPI label="HHI Index" value={lpResult.hhi?.toFixed(0) ?? "--"} color={lpResult.hhi > 2500 ? "text-red-400" : lpResult.hhi > 1500 ? "text-amber-400" : "text-emerald-400"} sub={lpResult.hhi > 2500 ? "High concentration" : lpResult.hhi > 1500 ? "Moderate" : "Diversified"} />
              <KPI label="LCR" value={`${(lpResult.lcr_pct ?? lpResult.lcr ?? 0).toFixed(1)}%`} color="text-gray-700" />
              <KPI label="Stress Redemption" value={`${(lpResult.stress_redemption_pct ?? 0).toFixed(1)}%`} color="text-amber-400" />
              <KPI label="Max Single LP" value={`${(lpResult.max_single_lp_pct ?? 0).toFixed(1)}%`} />
            </div>
            {lpResult.investor_details && (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={lpResult.investor_details.map((d, i) => ({ name: d.name, value: d.commitment_eur || d.weight_pct || 0 }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {lpResult.investor_details.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </Section>

      {/* 6 — ESG Optimisation */}
      <Section title="ESG-Constrained Optimisation" subtitle="Mean-variance with ESG tilts, exclusions, efficient frontier" open={!!openSections.opt} onToggle={() => toggle("opt")}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Input label="Min ESG Score" value={optMinESG} onChange={setOptMinESG} type="number" placeholder="40" />
        </div>
        <Btn onClick={runOptimise} loading={optLoading}>Run Optimisation</Btn>
        <ErrorBox msg={optError} />
        {optResult && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KPI label="Optimal Return" value={`${optResult.optimal_return_pct?.toFixed(2) ?? "--"}%`} color="text-emerald-400" />
              <KPI label="Optimal Risk" value={`${optResult.optimal_risk_pct?.toFixed(2) ?? "--"}%`} color="text-amber-400" />
              <KPI label="Sharpe Ratio" value={optResult.sharpe_ratio?.toFixed(2) ?? "--"} color="text-gray-700" />
              <KPI label="Portfolio ESG" value={optResult.portfolio_esg_score?.toFixed(1) ?? "--"} color="text-purple-400" />
            </div>
            {optResult.optimised_holdings && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-200">
                      {["Security", "Original %", "Optimised %", "Change", "ESG"].map(h => (
                        <th key={h} className="text-left py-2 px-3 text-gray-500 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {optResult.optimised_holdings.map((h, i) => (
                      <tr key={i} className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="py-2 px-3 text-gray-700 font-medium">{h.name || h.security_id}</td>
                        <td className="py-2 px-3 text-gray-500">{h.original_weight_pct?.toFixed(1)}%</td>
                        <td className="py-2 px-3 text-gray-800 font-bold">{h.optimised_weight_pct?.toFixed(1)}%</td>
                        <td className={`py-2 px-3 font-bold ${(h.optimised_weight_pct - h.original_weight_pct) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {(h.optimised_weight_pct - h.original_weight_pct) >= 0 ? "+" : ""}{(h.optimised_weight_pct - h.original_weight_pct).toFixed(1)}%
                        </td>
                        <td className="py-2 px-3 text-purple-300">{h.esg_score?.toFixed(0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {optResult.efficient_frontier && (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={optResult.efficient_frontier}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                  <XAxis dataKey="risk_pct" tick={{ fontSize: 9, fill: "#ffffff60" }} label={{ value: "Risk %", position: "insideBottomRight", offset: -5, fontSize: 9, fill: "#ffffff40" }} />
                  <YAxis tick={{ fontSize: 9, fill: "#ffffff60" }} label={{ value: "Return %", angle: -90, position: "insideLeft", fontSize: 9, fill: "#ffffff40" }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line dataKey="return_pct" name="Return %" stroke="#06b6d4" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════
   TAB 2 — FACTOR OVERLAY PANEL
   ══════════════════════════════════════════════════════════════════════ */

const OVERLAY_OPTIONS = [
  { v: "ecl-credit", l: "Bank Credit -- ECL Overlay", icon: Building2, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-001" }, { k: "country_code", l: "Country", d: "US" },
    { k: "sector_nace", l: "NACE Sector", d: "K64" }, { k: "base_pd", l: "Base PD", d: "0.02", t: "number" },
    { k: "base_lgd", l: "Base LGD", d: "0.45", t: "number" }, { k: "base_ead", l: "Base EAD", d: "10000000", t: "number" },
    { k: "scenario", l: "Scenario", d: "current_policies" },
  ]},
  { v: "alm-treasury", l: "Bank Treasury -- ALM Overlay", icon: BarChart3, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-002" }, { k: "country_code", l: "Country", d: "GB" },
    { k: "credit_quality", l: "Credit Quality", d: "investment_grade" }, { k: "base_nim_bps", l: "Base NIM (bps)", d: "180", t: "number" },
    { k: "base_duration_gap", l: "Duration Gap", d: "2.5", t: "number" }, { k: "fx_exposure_pct", l: "FX Exposure %", d: "15", t: "number" },
    { k: "scenario", l: "Scenario", d: "current_policies" },
  ]},
  { v: "regulatory-compliance", l: "Regulatory Compliance", icon: Shield, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-003" }, { k: "jurisdiction", l: "Jurisdiction", d: "EU" },
    { k: "current_gap_count", l: "Current Gaps", d: "12", t: "number" }, { k: "assurance_level", l: "Assurance", d: "medium" },
  ]},
  { v: "insurance-uw", l: "Insurance UW -- P&C Pricing", icon: Shield, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-004" }, { k: "country_code", l: "Country", d: "AU" },
    { k: "biome", l: "Biome", d: "tropical_forest" }, { k: "base_premium", l: "Base Premium", d: "500000", t: "number" },
    { k: "base_loss_ratio", l: "Loss Ratio", d: "0.65", t: "number" },
  ]},
  { v: "insurance-actuarial", l: "Insurance Actuarial -- Life", icon: Layers, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-005" }, { k: "country_code", l: "Country", d: "IN" },
    { k: "air_quality_band", l: "Air Quality", d: "poor" }, { k: "base_mortality_rate", l: "Base Mortality", d: "0.008", t: "number" },
    { k: "migration_pattern", l: "Migration", d: "stable" }, { k: "medical_tech", l: "Medical Tech", d: "baseline" },
  ]},
  { v: "portfolio-management", l: "AM Portfolio Management", icon: TrendingUp, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-006" }, { k: "sector_nace", l: "NACE Sector", d: "C29" },
    { k: "base_return_pct", l: "Base Return %", d: "8.5", t: "number" }, { k: "base_alpha_pct", l: "Base Alpha %", d: "1.2", t: "number" },
  ]},
  { v: "risk-management", l: "AM Risk Management", icon: Sliders, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-007" }, { k: "country_code", l: "Country", d: "DE" },
    { k: "sector_nace", l: "NACE Sector", d: "D35" }, { k: "base_var_pct", l: "Base VaR %", d: "3.5", t: "number" },
    { k: "base_cvar_pct", l: "Base CVaR %", d: "5.2", t: "number" },
  ]},
  { v: "pe-deal", l: "PE Deal Scoring", icon: ArrowRightLeft, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-008" }, { k: "country_code", l: "Country", d: "US" },
    { k: "sector_nace", l: "NACE Sector", d: "J62" }, { k: "base_ev_ebitda", l: "EV/EBITDA", d: "12.5", t: "number" },
    { k: "carbon_reduction_pct", l: "Carbon Reduction %", d: "15", t: "number" },
  ]},
  { v: "real-estate-valuation", l: "Real Estate Valuation", icon: Building2, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-009" }, { k: "country_code", l: "Country", d: "SG" },
    { k: "certification", l: "Certification", d: "LEED_Gold" }, { k: "smart_building_tier", l: "Smart Tier", d: "advanced" },
    { k: "base_value", l: "Base Value", d: "50000000", t: "number" }, { k: "base_noi", l: "Base NOI", d: "3500000", t: "number" },
  ]},
  { v: "energy-strategy", l: "Energy Strategy", icon: Zap, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-010" }, { k: "country_code", l: "Country", d: "NO" },
    { k: "base_generation_gwh", l: "Generation (GWh)", d: "5000", t: "number" }, { k: "base_co2_intensity", l: "CO2 Intensity", d: "350", t: "number" },
    { k: "h2_pathway", l: "H2 Pathway", d: "grey_h2" },
  ]},
  { v: "agriculture-finance", l: "Agriculture Finance", icon: Tractor, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-011" }, { k: "country_code", l: "Country", d: "BR" },
    { k: "certification", l: "Certification", d: "RSPO" }, { k: "base_loan_value", l: "Loan Value", d: "2000000", t: "number" },
    { k: "precision_ag_level", l: "Precision Ag", d: "conventional" },
  ]},
  { v: "trade-advisory", l: "Trade Advisory", icon: Globe2, fields: [
    { k: "entity_id", l: "Entity ID", d: "ENT-012" }, { k: "country_code", l: "Country", d: "CN" },
    { k: "sector_nace", l: "NACE Sector", d: "C20" }, { k: "base_trade_value", l: "Trade Value", d: "8000000", t: "number" },
    { k: "supply_chain_digital_level", l: "SC Digital Level", d: "paper_hybrid" },
  ]},
];

function FactorOverlayPanel() {
  const [selected, setSelected] = useState(OVERLAY_OPTIONS[0].v);
  const [formValues, setFormValues] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const overlayDef = OVERLAY_OPTIONS.find(o => o.v === selected);

  const getVal = (k) => formValues[`${selected}.${k}`] ?? "";
  const setVal = (k, v) => setFormValues(p => ({ ...p, [`${selected}.${k}`]: v }));

  const runOverlay = useCallback(async () => {
    setLoading(true); setError(""); setResult(null);
    const def = OVERLAY_OPTIONS.find(o => o.v === selected);
    const payload = {};
    def.fields.forEach(f => {
      const raw = formValues[`${selected}.${f.k}`] || f.d;
      payload[f.k] = f.t === "number" ? parseFloat(raw) : raw;
    });
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/factor-overlays/${selected}`, payload);
      setResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    setLoading(false);
  }, [selected, formValues]);

  const allFactors = result ? [...(result.esg_factors || []), ...(result.geo_factors || []), ...(result.tech_factors || [])] : [];

  return (
    <div className="space-y-5">
      {/* Overlay selector */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Select Overlay Type</label>
        <select
          value={selected} onChange={e => { setSelected(e.target.value); setResult(null); setError(""); }}
          className="w-full md:w-96 border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-[#f5f6f8] text-gray-700 focus:outline-none focus:ring-2 focus:ring-black/50"
        >
          {OVERLAY_OPTIONS.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
        </select>
      </div>

      {/* Dynamic form */}
      {overlayDef && (
        <div className="border border-gray-200 rounded-xl bg-white p-5">
          <div className="flex items-center gap-2 mb-4">
            {overlayDef.icon && <overlayDef.icon className="h-4 w-4 text-gray-700" />}
            <h3 className="text-sm font-semibold text-gray-900">{overlayDef.l}</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {overlayDef.fields.map(f => (
              <Input key={f.k} label={f.l} value={getVal(f.k)} onChange={v => setVal(f.k, v)} type={f.t || "text"} placeholder={f.d} />
            ))}
          </div>
          <Btn onClick={runOverlay} loading={loading}>Apply Factor Overlay</Btn>
        </div>
      )}

      <ErrorBox msg={error} />

      {/* Results */}
      {result && (
        <div className="space-y-5">
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPI label="Overlay Type" value={result.overlay_type || selected} color="text-gray-700" />
            <KPI label="Composite Adjustment" value={`${((result.composite_adjustment ?? 0) * 100).toFixed(2)}%`} color={(result.composite_adjustment ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"} />
            <KPI label="Confidence" value={`${((result.confidence ?? 0) * 100).toFixed(0)}%`} color="text-purple-400" />
            <KPI label="Factors Applied" value={allFactors.length} />
          </div>

          {/* Base vs Enhanced table */}
          {result.base_metrics && result.enhanced_metrics && (
            <div className="border border-gray-200 rounded-xl bg-white overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900">Base vs Adjusted Comparison</h3>
              </div>
              <div className="p-5 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 text-gray-500 font-medium">Metric</th>
                      <th className="text-right py-2 px-3 text-gray-500 font-medium">Base</th>
                      <th className="text-right py-2 px-3 text-gray-500 font-medium">Adjusted</th>
                      <th className="text-right py-2 px-3 text-gray-500 font-medium">Delta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(result.base_metrics).map(k => {
                      const b = result.base_metrics[k];
                      const e = result.enhanced_metrics[k];
                      const delta = typeof b === "number" && typeof e === "number" ? e - b : null;
                      return (
                        <tr key={k} className="border-b border-gray-200 hover:bg-gray-50">
                          <td className="py-2 px-3 text-gray-600 font-medium">{k.replace(/_/g, " ")}</td>
                          <td className="py-2 px-3 text-right text-gray-500">{typeof b === "number" ? b.toFixed(4) : String(b)}</td>
                          <td className="py-2 px-3 text-right text-gray-800 font-bold">{typeof e === "number" ? e.toFixed(4) : String(e)}</td>
                          <td className={`py-2 px-3 text-right font-bold ${delta !== null ? (delta >= 0 ? "text-emerald-400" : "text-red-400") : "text-gray-500"}`}>
                            {delta !== null ? `${delta >= 0 ? "+" : ""}${delta.toFixed(4)}` : "--"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Factor contribution waterfall */}
          {allFactors.length > 0 && (
            <div className="border border-gray-200 rounded-xl bg-white">
              <div className="px-5 py-3 border-b border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900">Factor Contribution Waterfall</h3>
              </div>
              <div className="p-5">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={allFactors.map(f => ({ name: f.factor_name?.slice(0, 20) || f.factor_type, adj: f.adjustment ?? 0, type: f.factor_type }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                    <XAxis dataKey="name" tick={{ fontSize: 8, fill: "#ffffff50" }} angle={-25} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 9, fill: "#ffffff60" }} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v, n, p) => [`${(v * 100).toFixed(2)}%`, `${p.payload.type} factor`]} />
                    <Bar dataKey="adj" name="Adjustment" radius={[3,3,0,0]}>
                      {allFactors.map((f, i) => (
                        <Cell key={i} fill={f.factor_type === "esg" ? "#10b981" : f.factor_type === "geo" ? "#f59e0b" : "#8b5cf6"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex gap-4 mt-2 text-[10px] text-gray-500">
                  <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" /> ESG</span>
                  <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-amber-500 inline-block" /> Geopolitical</span>
                  <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-purple-500 inline-block" /> Technology</span>
                </div>
              </div>
            </div>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="border border-amber-400/20 rounded-xl bg-amber-500/[0.04] p-4">
              <h4 className="text-xs font-bold text-amber-300 mb-2">Warnings</h4>
              <ul className="space-y-1">
                {result.warnings.map((w, i) => (
                  <li key={i} className="text-xs text-amber-200/70 flex items-start gap-2">
                    <AlertCircle className="h-3 w-3 shrink-0 mt-0.5 text-amber-400" /> {w}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ══════════════════════════════════════════════════════════════════════ */

export default function AssetManagementPage() {
  const [tab, setTab] = useState("am");

  const tabs = [
    { id: "am", label: "AM Engine", icon: TrendingUp, sub: "6 sub-modules" },
    { id: "overlay", label: "Factor Overlay", icon: Layers, sub: "12 overlays" },
  ];

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gray-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-gray-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Asset Management</h1>
              <p className="text-gray-500 text-sm">AM Engine (PACTA, ICMA, Fama-French) and Factor Overlay Engine (31 registries, 12 overlay methods)</p>
            </div>
          </div>
          <div className="flex gap-2 mt-3 flex-wrap">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-50 text-gray-800">PACTA</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-purple-400/10 text-purple-300">ICMA GBS</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-400/10 text-emerald-300">EU GBS 2023/2631</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-400/10 text-amber-300">Fama-French + ESG</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-50 text-gray-500">31 Factor Registries</span>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 p-1 bg-gray-50 rounded-lg mb-6">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium transition-colors ${
                tab === t.id
                  ? "bg-[#1a2234] text-gray-900 shadow"
                  : "text-gray-500 hover:text-gray-600 hover:bg-gray-50"
              }`}
            >
              <t.icon className="h-4 w-4" />
              <span>{t.label}</span>
              <span className="text-[10px] text-gray-500 ml-1 hidden sm:inline">{t.sub}</span>
            </button>
          ))}
        </div>

        {/* Tab content */}
        {tab === "am" && <AMEnginePanel />}
        {tab === "overlay" && <FactorOverlayPanel />}
      </div>
    </div>
  );
}
