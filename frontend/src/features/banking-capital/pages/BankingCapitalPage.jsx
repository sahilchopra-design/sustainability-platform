/**
 * Banking & Capital Engines
 *
 * Tab 1 - Basel III/IV Capital: SA & IRB risk-weights, capital adequacy,
 *         LCR/NSFR liquidity, climate-adjusted buffers, BCBS 239 compliance.
 * Tab 2 - PCAF Data Quality: DQS 1-5 scoring per holding / portfolio,
 *         5-dimension radar, financed emissions, improvement paths.
 * Tab 3 - Model Validation: Backtesting, champion/challenger, lifecycle,
 *         inventory, statistical tests, dashboard KPIs.
 */
import React, { useState, useEffect, useCallback } from "react";
import { usePersonaDefaults } from "../../../context/PersonaContext";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar, PieChart, Pie, LineChart, Line,
} from "recharts";
import {
  Landmark, ShieldCheck, FlaskConical, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, RefreshCw, Play, Plus, Trash2,
  Activity, TrendingUp, Droplets, Gauge, BarChart3, FileText,
  Info, Settings, Database, Layers, ArrowRightLeft,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt2 = (v) => (v == null ? "\u2014" : Number(v).toFixed(2));
const fmt0 = (v) => (v == null ? "\u2014" : Number(v).toFixed(0));
const fmtPct = (v) => (v == null ? "\u2014" : `${Number(v).toFixed(2)}%`);
const fmtBps = (v) => (v == null ? "\u2014" : `${Number(v).toFixed(0)} bps`);

/* ── Shared UI primitives ──────────────────────────────────────────────── */

function Section({ title, children, defaultOpen = true, accent }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
        <div className="flex items-center gap-2">
          {accent && <div className={`w-1 h-4 rounded-full ${accent}`} />}
          <span className="font-medium text-sm text-gray-700">{title}</span>
        </div>
        {open ? <ChevronUp className="h-3.5 w-3.5 text-gray-400" /> : <ChevronDown className="h-3.5 w-3.5 text-gray-400" />}
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
}

function KpiCard({ label, value, sub, color }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono tabular-nums ${color || "text-gray-900"}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function InputRow({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <label className="text-[11px] text-gray-500 w-40 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Input({ value, onChange, type = "text", placeholder, className = "" }) {
  return (
    <input type={type} value={value} onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className={`w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800 placeholder-gray-400
        focus:outline-none focus:border-blue-500 ${className}`} />
  );
}

function Select({ value, onChange, options, className = "" }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className={`w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800
        focus:outline-none focus:border-blue-500 ${className}`}>
      {options.map(o => <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>)}
    </select>
  );
}

function Btn({ onClick, disabled, children, variant = "primary" }) {
  const v = {
    primary: "bg-gray-200 text-gray-800 border border-gray-300 hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed",
    secondary: "bg-gray-50 text-gray-500 border border-black/10 hover:bg-white/8 hover:text-gray-700",
    danger: "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20",
  };
  return (
    <button onClick={onClick} disabled={disabled}
      className={`flex items-center gap-1.5 rounded font-medium px-3 py-1.5 text-xs transition-all focus:outline-none ${v[variant]}`}>
      {children}
    </button>
  );
}

function Spinner() {
  return <div className="w-4 h-4 border-2 border-gray-300 border-t-cyan-400 rounded-full animate-spin" />;
}

function ErrBox({ msg }) {
  if (!msg) return null;
  return (
    <div className="bg-red-500/10 border border-red-500/20 rounded p-3 text-[11px] text-red-400 mb-3 flex items-start gap-2">
      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />{msg}
    </div>
  );
}

function RAGBadge({ status }) {
  const m = {
    green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    red: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  return (
    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${m[status] || m.amber}`}>
      {(status || "").toUpperCase()}
    </span>
  );
}

const CHART_COLORS = ["#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#3b82f6", "#ec4899", "#14b8a6"];

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 1 — Basel III/IV Capital
   ═══════════════════════════════════════════════════════════════════════ */

const EXPOSURE_CLASSES = [
  { value: "sovereign", label: "Sovereign" }, { value: "pse", label: "Public Sector Entities" },
  { value: "mdb", label: "Multilateral Development Banks" }, { value: "institution", label: "Institutions" },
  { value: "corporate", label: "Corporate" }, { value: "retail", label: "Retail" },
  { value: "real_estate", label: "Real Estate" }, { value: "subordinated", label: "Subordinated Debt" },
  { value: "equity", label: "Equity" }, { value: "defaulted", label: "Defaulted Exposures" },
  { value: "covered_bond", label: "Covered Bonds" }, { value: "securitisation", label: "Securitisation" },
  { value: "other", label: "Other Items" },
];

function BaselPanel() {
  const d = usePersonaDefaults('banking_capital');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refData, setRefData] = useState({});
  /* SA form */
  const [saClass, setSaClass] = useState(d.saClass || "corporate");
  const [cqs, setCqs] = useState(d.cqs || "3");
  const [saAmount, setSaAmount] = useState(d.saAmount || "1000000");
  const [saResult, setSaResult] = useState(null);
  /* IRB form */
  const [irbPd, setIrbPd] = useState(d.irbPd || "0.02");
  const [irbLgd, setIrbLgd] = useState(d.irbLgd || "0.45");
  const [irbEad, setIrbEad] = useState(d.irbEad || "5000000");
  const [irbMat, setIrbMat] = useState(d.irbMat || "2.5");
  const [irbClass, setIrbClass] = useState(d.irbClass || "corporate");
  const [irbResult, setIrbResult] = useState(null);
  /* Capital requirement form */
  const [capBase, setCapBase] = useState("cet1");
  const [capClimate, setCapClimate] = useState(true);
  const [capResult, setCapResult] = useState(null);
  /* Liquidity form */
  const [hqla, setHqla] = useState(d.hqla || "800000000");
  const [outflows, setOutflows] = useState(d.outflows || "1000000000");
  const [inflows, setInflows] = useState(d.inflows || "400000000");
  const [asf, setAsf] = useState(d.asf || "900000000");
  const [rsf, setRsf] = useState(d.rsf || "700000000");
  const [liqResult, setLiqResult] = useState(null);

  /* Re-seed form when persona switches */
  useEffect(() => {
    if (d.saClass)   setSaClass(d.saClass);
    if (d.cqs)       setCqs(d.cqs);
    if (d.saAmount)  setSaAmount(d.saAmount);
    if (d.irbPd)     setIrbPd(d.irbPd);
    if (d.irbLgd)    setIrbLgd(d.irbLgd);
    if (d.irbEad)    setIrbEad(d.irbEad);
    if (d.irbMat)    setIrbMat(d.irbMat);
    if (d.irbClass)  setIrbClass(d.irbClass);
    if (d.hqla)      setHqla(d.hqla);
    if (d.outflows)  setOutflows(d.outflows);
    if (d.inflows)   setInflows(d.inflows);
    if (d.asf)       setAsf(d.asf);
    if (d.rsf)       setRsf(d.rsf);
    setSaResult(null); setIrbResult(null); setLiqResult(null); setCapResult(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.saClass, d.irbPd, d.hqla]);

  const loadRef = useCallback(async () => {
    try {
      const endpoints = ["exposure-classes", "sa-risk-weights", "capital-requirements", "capital-buffers", "lcr-parameters", "nsfr-parameters", "climate-adjustments"];
      const results = await Promise.allSettled(endpoints.map(e => axios.get(`${API_BASE}/api/v1/basel-capital/ref/${e}`)));
      const data = {};
      endpoints.forEach((e, i) => { if (results[i].status === "fulfilled") data[e] = results[i].value.data; });
      setRefData(data);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { loadRef(); }, [loadRef]);

  const runSA = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/basel-capital/risk-weight-sa`, {
        exposure_class: saClass, credit_quality_step: Number(cqs), exposure_amount: Number(saAmount),
      });
      setSaResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const runIRB = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/basel-capital/risk-weight-irb`, {
        pd: Number(irbPd), lgd: Number(irbLgd), ead: Number(irbEad), maturity: Number(irbMat), exposure_class: irbClass,
      });
      setIrbResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const runCapital = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/basel-capital/capital-requirement`, {
        exposures: [{ exposure_class: saClass, amount: Number(saAmount), risk_weight: saResult?.risk_weight_pct || 100 }],
        capital_base: capBase,
        buffer_settings: { countercyclical: true, systemic: true, conservation: true },
        climate_adjustments: capClimate,
      });
      setCapResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const runLiquidity = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/basel-capital/liquidity`, {
        hqla_items: [{ type: "level_1", amount: Number(hqla) }],
        outflow_items: [{ type: "retail_stable", amount: Number(outflows) }],
        inflow_items: [{ type: "performing_loans", amount: Number(inflows) }],
        asf_items: [{ type: "tier1_capital", amount: Number(asf) }],
        rsf_items: [{ type: "performing_loans_gt1y", amount: Number(rsf) }],
      });
      setLiqResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  /* RWA waterfall chart data */
  const waterfallData = capResult?.rwa_waterfall || [
    { name: "Credit RWA", value: capResult?.credit_rwa || 0 },
    { name: "Market RWA", value: capResult?.market_rwa || 0 },
    { name: "Op RWA", value: capResult?.operational_rwa || 0 },
    { name: "Climate Adj", value: capResult?.climate_adjustment_rwa || 0 },
    { name: "Total RWA", value: capResult?.total_rwa || 0 },
  ];

  /* Capital ratios chart */
  const ratioData = capResult ? [
    { name: "CET1", ratio: capResult.cet1_ratio || 0, requirement: 4.5 },
    { name: "Tier 1", ratio: capResult.tier1_ratio || 0, requirement: 6.0 },
    { name: "Total Capital", ratio: capResult.total_ratio || 0, requirement: 8.0 },
    { name: "Leverage", ratio: capResult.leverage_ratio || 0, requirement: 3.0 },
  ] : [];

  return (
    <div className="space-y-4">
      <ErrBox msg={error} />

      {/* Reference data */}
      <Section title="Reference Data" defaultOpen={false} accent="bg-blue-400">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] text-gray-500">
          {Object.entries(refData).map(([k, v]) => (
            <div key={k} className="bg-white rounded p-2 border border-gray-200">
              <p className="text-gray-500 uppercase mb-1">{k.replace(/-/g, " ")}</p>
              <p className="text-gray-600 font-mono">{Array.isArray(v) ? `${v.length} items` : typeof v === "object" ? `${Object.keys(v).length} keys` : String(v)}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* SA Risk Weight */}
      <Section title="Standardised Approach (SA) Risk Weight" accent="bg-blue-600">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Exposure Class">
              <Select value={saClass} onChange={setSaClass} options={EXPOSURE_CLASSES} />
            </InputRow>
            <InputRow label="Credit Quality Step">
              <Select value={cqs} onChange={setCqs} options={[1,2,3,4,5,6].map(n => ({ value: String(n), label: `CQS ${n}` }))} />
            </InputRow>
            <InputRow label="Exposure Amount">
              <Input value={saAmount} onChange={setSaAmount} type="number" placeholder="1000000" />
            </InputRow>
            <Btn onClick={runSA} disabled={loading}>{loading ? <Spinner /> : <Play className="h-3 w-3" />} Calculate SA RW</Btn>
          </div>
          {saResult && (
            <div className="grid grid-cols-2 gap-2">
              <KpiCard label="Risk Weight" value={fmtPct(saResult.risk_weight_pct)} color="text-gray-800" />
              <KpiCard label="RWA" value={fmt0(saResult.rwa)} sub="Risk-weighted amount" />
              <KpiCard label="Capital Charge" value={fmt0(saResult.capital_charge)} sub="8% of RWA" />
              <KpiCard label="RAG Status" value={<RAGBadge status={saResult.rag_status || "green"} />} />
            </div>
          )}
        </div>
      </Section>

      {/* IRB Risk Weight */}
      <Section title="IRB Risk Weight (Foundation/Advanced)" accent="bg-purple-400">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Probability of Default">
              <Input value={irbPd} onChange={setIrbPd} type="number" placeholder="0.02" />
            </InputRow>
            <InputRow label="Loss Given Default">
              <Input value={irbLgd} onChange={setIrbLgd} type="number" placeholder="0.45" />
            </InputRow>
            <InputRow label="Exposure at Default">
              <Input value={irbEad} onChange={setIrbEad} type="number" placeholder="5000000" />
            </InputRow>
            <InputRow label="Maturity (years)">
              <Input value={irbMat} onChange={setIrbMat} type="number" placeholder="2.5" />
            </InputRow>
            <InputRow label="Exposure Class">
              <Select value={irbClass} onChange={setIrbClass} options={EXPOSURE_CLASSES} />
            </InputRow>
            <Btn onClick={runIRB} disabled={loading}>{loading ? <Spinner /> : <Play className="h-3 w-3" />} Calculate IRB RW</Btn>
          </div>
          {irbResult && (
            <div className="grid grid-cols-2 gap-2">
              <KpiCard label="IRB Risk Weight" value={fmtPct(irbResult.risk_weight_pct)} color="text-purple-300" />
              <KpiCard label="IRB RWA" value={fmt0(irbResult.rwa)} />
              <KpiCard label="Expected Loss" value={fmt0(irbResult.expected_loss)} sub="PD x LGD x EAD" />
              <KpiCard label="Correlation (R)" value={fmt2(irbResult.correlation)} sub="Asset correlation" />
            </div>
          )}
        </div>
      </Section>

      {/* Capital Requirement */}
      <Section title="Capital Adequacy & Buffers" accent="bg-emerald-400">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Capital Base">
              <Select value={capBase} onChange={setCapBase} options={[
                { value: "cet1", label: "CET1 Capital" }, { value: "tier1", label: "Tier 1 Capital" }, { value: "tier2", label: "Total Capital (T1+T2)" },
              ]} />
            </InputRow>
            <InputRow label="Climate Adjustments">
              <Select value={capClimate ? "yes" : "no"} onChange={v => setCapClimate(v === "yes")}
                options={[{ value: "yes", label: "Enabled" }, { value: "no", label: "Disabled" }]} />
            </InputRow>
            <Btn onClick={runCapital} disabled={loading}>{loading ? <Spinner /> : <Play className="h-3 w-3" />} Run Capital Adequacy</Btn>
          </div>
          {capResult && (
            <div className="grid grid-cols-2 gap-2">
              <KpiCard label="CET1 Ratio" value={fmtPct(capResult.cet1_ratio)} color={capResult.cet1_ratio >= 4.5 ? "text-emerald-400" : "text-red-400"} />
              <KpiCard label="Total Capital Ratio" value={fmtPct(capResult.total_ratio)} />
              <KpiCard label="Leverage Ratio" value={fmtPct(capResult.leverage_ratio)} />
              <KpiCard label="BCBS 239 Score" value={fmt0(capResult.bcbs239_score)} sub="Data aggregation compliance" />
            </div>
          )}
        </div>

        {capResult && ratioData.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {/* RWA Waterfall */}
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">RWA Waterfall</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={waterfallData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: "rgba(255,255,255,0.4)" }} />
                  <YAxis tick={{ fontSize: 9, fill: "rgba(255,255,255,0.4)" }} />
                  <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", fontSize: 11, color: "#fff" }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {waterfallData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Capital Ratios vs Requirements */}
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Capital Ratios vs Requirements</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={ratioData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: "rgba(255,255,255,0.4)" }} />
                  <YAxis tick={{ fontSize: 9, fill: "rgba(255,255,255,0.4)" }} domain={[0, "auto"]} />
                  <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", fontSize: 11, color: "#fff" }} />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <Bar dataKey="ratio" name="Actual" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="requirement" name="Minimum" fill="#ef4444" opacity={0.4} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </Section>

      {/* Liquidity */}
      <Section title="Liquidity (LCR / NSFR)" accent="bg-amber-400">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="HQLA (Level 1)"><Input value={hqla} onChange={setHqla} type="number" /></InputRow>
            <InputRow label="Net Cash Outflows"><Input value={outflows} onChange={setOutflows} type="number" /></InputRow>
            <InputRow label="Cash Inflows"><Input value={inflows} onChange={setInflows} type="number" /></InputRow>
            <InputRow label="Available Stable Funding"><Input value={asf} onChange={setAsf} type="number" /></InputRow>
            <InputRow label="Required Stable Funding"><Input value={rsf} onChange={setRsf} type="number" /></InputRow>
            <Btn onClick={runLiquidity} disabled={loading}>{loading ? <Spinner /> : <Droplets className="h-3 w-3" />} Calculate LCR / NSFR</Btn>
          </div>
          {liqResult && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <KpiCard label="LCR" value={fmtPct(liqResult.lcr)} color={liqResult.lcr >= 100 ? "text-emerald-400" : "text-red-400"} sub="Min 100%" />
                <KpiCard label="NSFR" value={fmtPct(liqResult.nsfr)} color={liqResult.nsfr >= 100 ? "text-emerald-400" : "text-red-400"} sub="Min 100%" />
              </div>
              {/* Gauge-style bars */}
              {[{ label: "LCR", val: liqResult.lcr }, { label: "NSFR", val: liqResult.nsfr }].map(g => (
                <div key={g.label} className="flex items-center gap-2">
                  <span className="text-[11px] text-gray-500 w-12">{g.label}</span>
                  <div className="flex-1 bg-gray-50 rounded-full h-3 overflow-hidden relative">
                    <div className="h-full rounded-full transition-all"
                      style={{ width: `${Math.min(150, g.val || 0)}%`, background: (g.val || 0) >= 100 ? "#10b981" : "#ef4444" }} />
                    <div className="absolute top-0 left-[66.6%] w-px h-full bg-white/20" title="100% min" />
                  </div>
                  <span className="text-[11px] font-mono text-gray-600 w-14 text-right">{fmtPct(g.val)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 2 — PCAF Data Quality
   ═══════════════════════════════════════════════════════════════════════ */

const PCAF_ASSET_CLASSES = [
  { value: "listed_equity", label: "Listed Equity & Corporate Bonds" },
  { value: "business_loans", label: "Business Loans & Unlisted Equity" },
  { value: "project_finance", label: "Project Finance" },
  { value: "commercial_re", label: "Commercial Real Estate" },
  { value: "mortgages", label: "Mortgages" },
  { value: "motor_vehicles", label: "Motor Vehicle Loans" },
];

const DQS_COLORS = { 1: "#10b981", 2: "#06b6d4", 3: "#f59e0b", 4: "#f97316", 5: "#ef4444" };
const DQS_LABELS = { 1: "Audited", 2: "Reported", 3: "Estimated (high)", 4: "Estimated (low)", 5: "Proxy / EEIO" };
const QUALITY_DIMS = ["completeness", "accuracy", "timeliness", "consistency", "granularity"];

function PCAFQualityPanel() {
  const d = usePersonaDefaults('financial_risk');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  /* Single holding form */
  const [holdingId, setHoldingId] = useState("H-001");
  const [assetClass, setAssetClass] = useState("listed_equity");
  const [sector, setSector] = useState("Utilities");
  const [scope1, setScope1] = useState("12000");
  const [scope2, setScope2] = useState("5000");
  const [dataSource, setDataSource] = useState("reported");
  const [holdingResult, setHoldingResult] = useState(null);
  /* Portfolio form */
  const [portfolioResult, setPortfolioResult] = useState(null);
  /* Data quality assessment */
  const [entityName, setEntityName] = useState(d.entityName || "Acme Corp");
  const [dimScores, setDimScores] = useState({ completeness: 3, accuracy: 2, timeliness: 3, consistency: 4, granularity: 3 });
  const [dqResult, setDqResult] = useState(null);

  const scoreHolding = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/pcaf-quality/score-holding`, {
        holding_id: holdingId, asset_class: assetClass, sector,
        emissions_data: { scope1: Number(scope1), scope2: Number(scope2) },
        data_sources: [dataSource],
      });
      setHoldingResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const scorePortfolio = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/pcaf-quality/score-portfolio`, {
        holdings: PCAF_ASSET_CLASSES.map((ac, i) => ({
          asset_class: ac.value, exposure: 10000000 * (i + 1),
          emissions_data: { scope1: 5000 * (6 - i), scope2: 2000 * (6 - i) },
        })),
      });
      setPortfolioResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const assessQuality = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/pcaf-quality/assess-data-quality`, {
        entity_name: entityName, dimension_scores: dimScores,
      });
      setDqResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  /* Radar chart data from dimension scores or result */
  const radarData = QUALITY_DIMS.map(d => ({
    dimension: d.charAt(0).toUpperCase() + d.slice(1),
    score: dqResult?.dimension_scores?.[d] ?? dimScores[d],
    max: 5,
  }));

  /* Portfolio DQS pie */
  const dqsPie = portfolioResult?.dqs_distribution
    ? Object.entries(portfolioResult.dqs_distribution).map(([k, v]) => ({ name: `DQS ${k}`, value: v, fill: DQS_COLORS[k] }))
    : [];

  /* Financed emissions bar */
  const emBar = portfolioResult?.by_asset_class
    ? portfolioResult.by_asset_class.map(a => ({ name: a.asset_class?.replace(/_/g, " ") || a.name, emissions: a.financed_emissions || a.emissions || 0 }))
    : [];

  return (
    <div className="space-y-4">
      <ErrBox msg={error} />

      {/* Score single holding */}
      <Section title="Score Single Holding" accent="bg-blue-600">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Holding ID"><Input value={holdingId} onChange={setHoldingId} /></InputRow>
            <InputRow label="Asset Class"><Select value={assetClass} onChange={setAssetClass} options={PCAF_ASSET_CLASSES} /></InputRow>
            <InputRow label="Sector"><Input value={sector} onChange={setSector} /></InputRow>
            <InputRow label="Scope 1 (tCO2e)"><Input value={scope1} onChange={setScope1} type="number" /></InputRow>
            <InputRow label="Scope 2 (tCO2e)"><Input value={scope2} onChange={setScope2} type="number" /></InputRow>
            <InputRow label="Data Source">
              <Select value={dataSource} onChange={setDataSource}
                options={[{ value: "audited", label: "Audited" }, { value: "reported", label: "Reported" }, { value: "estimated", label: "Estimated" }, { value: "proxy", label: "Proxy/EEIO" }]} />
            </InputRow>
            <Btn onClick={scoreHolding} disabled={loading}>{loading ? <Spinner /> : <Play className="h-3 w-3" />} Score Holding</Btn>
          </div>
          {holdingResult && (
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-lg font-bold`}
                  style={{ background: `${DQS_COLORS[holdingResult.dqs_score] || "#6b7280"}20`, color: DQS_COLORS[holdingResult.dqs_score] }}>
                  {holdingResult.dqs_score}
                </div>
                <div>
                  <p className="text-sm text-gray-800 font-medium">DQS {holdingResult.dqs_score}</p>
                  <p className="text-[10px] text-gray-500">{DQS_LABELS[holdingResult.dqs_score] || "Unknown"}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <KpiCard label="Financed Emissions" value={fmt0(holdingResult.financed_emissions)} sub="tCO2e" />
                <KpiCard label="Confidence" value={fmtPct(holdingResult.confidence)} />
              </div>
              {holdingResult.improvements && (
                <div className="mt-3 bg-white rounded p-3 border border-gray-200">
                  <p className="text-[10px] text-gray-500 uppercase mb-1">Improvement Actions</p>
                  {holdingResult.improvements.map((imp, i) => (
                    <div key={i} className="flex items-start gap-2 mb-1">
                      <CheckCircle className="h-3 w-3 text-emerald-400 mt-0.5 shrink-0" />
                      <span className="text-[11px] text-gray-600">{imp}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </Section>

      {/* Score portfolio */}
      <Section title="Portfolio DQS Distribution" accent="bg-emerald-400">
        <Btn onClick={scorePortfolio} disabled={loading}>{loading ? <Spinner /> : <BarChart3 className="h-3 w-3" />} Score Sample Portfolio</Btn>
        {portfolioResult && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">DQS Distribution</p>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={dqsPie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={{ fontSize: 9, fill: "rgba(255,255,255,0.5)" }}>
                    {dqsPie.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", fontSize: 11, color: "#fff" }} />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Financed Emissions by Asset Class</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={emBar} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis type="number" tick={{ fontSize: 9, fill: "rgba(255,255,255,0.4)" }} />
                  <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 8, fill: "rgba(255,255,255,0.4)" }} />
                  <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", fontSize: 11, color: "#fff" }} />
                  <Bar dataKey="emissions" fill="#06b6d4" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </Section>

      {/* Data quality assessment */}
      <Section title="Data Quality Assessment (5 Dimensions)" accent="bg-purple-400">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Entity Name"><Input value={entityName} onChange={setEntityName} /></InputRow>
            {QUALITY_DIMS.map(d => (
              <InputRow key={d} label={d.charAt(0).toUpperCase() + d.slice(1)}>
                <Select value={String(dimScores[d])} onChange={v => setDimScores(p => ({ ...p, [d]: Number(v) }))}
                  options={[1,2,3,4,5].map(n => ({ value: String(n), label: `${n} - ${DQS_LABELS[n]}` }))} />
              </InputRow>
            ))}
            <Btn onClick={assessQuality} disabled={loading}>{loading ? <Spinner /> : <Play className="h-3 w-3" />} Assess Quality</Btn>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-3">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Dimension Radar</p>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData} outerRadius={70}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 9, fill: "rgba(255,255,255,0.5)" }} />
                <PolarRadiusAxis domain={[0, 5]} tick={{ fontSize: 8, fill: "rgba(255,255,255,0.3)" }} />
                <Radar name="Score" dataKey="score" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.15} />
              </RadarChart>
            </ResponsiveContainer>
            {dqResult && (
              <div className="mt-2 text-center">
                <span className="text-lg font-bold font-mono" style={{ color: DQS_COLORS[dqResult.overall_dqs] }}>
                  DQS {dqResult.overall_dqs}
                </span>
                <p className="text-[10px] text-gray-500">{DQS_LABELS[dqResult.overall_dqs]}</p>
              </div>
            )}
          </div>
        </div>
      </Section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 3 — Model Validation
   ═══════════════════════════════════════════════════════════════════════ */

const LIFECYCLE_STATES = [
  { value: "development", label: "Development", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  { value: "validation", label: "Validation", color: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  { value: "approved", label: "Approved", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
  { value: "production", label: "Production", color: "bg-gray-100 text-gray-700 border-gray-200" },
  { value: "monitoring", label: "Monitoring", color: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  { value: "retired", label: "Retired", color: "bg-gray-50 text-gray-500 border-black/10" },
];

const STAT_TESTS = [
  "Kolmogorov-Smirnov", "Binomial Test", "Traffic Light (Basel)", "Kupiec POF", "Christoffersen CC",
  "Anderson-Darling", "Chi-Squared", "Hosmer-Lemeshow", "Brier Score", "AUC-ROC", "PSI", "Jeffreys Divergence",
];

function ModelValidationPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [catalog, setCatalog] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  /* Backtest form */
  const [btModel, setBtModel] = useState("");
  const [btConf, setBtConf] = useState("0.99");
  const [btResult, setBtResult] = useState(null);
  /* Compare form */
  const [champId, setChampId] = useState("");
  const [challId, setChallId] = useState("");
  const [compareResult, setCompareResult] = useState(null);
  /* Lifecycle transition */
  const [lcModel, setLcModel] = useState("");
  const [lcFrom, setLcFrom] = useState("development");
  const [lcTo, setLcTo] = useState("validation");
  const [lcJustification, setLcJustification] = useState("");
  const [lcResult, setLcResult] = useState(null);

  const loadCatalog = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/api/v1/model-validation/ref/catalog`);
      setCatalog(Array.isArray(data) ? data : data.models || []);
      if (data.length) { setBtModel(data[0].model_id || data[0].id); setChampId(data[0].model_id || data[0].id); }
      if (data.length > 1) setChallId(data[1].model_id || data[1].id);
    } catch { /* silent */ }
  }, []);

  const loadInventory = useCallback(async () => {
    try { const { data } = await axios.get(`${API_BASE}/api/v1/model-validation/inventory`); setInventory(Array.isArray(data) ? data : data.models || []); } catch { /* silent */ }
  }, []);

  const loadDashboard = useCallback(async () => {
    try { const { data } = await axios.get(`${API_BASE}/api/v1/model-validation/dashboard`); setDashboard(data); } catch { /* silent */ }
  }, []);

  useEffect(() => { loadCatalog(); loadInventory(); loadDashboard(); }, [loadCatalog, loadInventory, loadDashboard]);

  const modelOpts = catalog.map(m => ({ value: m.model_id || m.id, label: m.name || m.model_id || m.id }));

  const runBacktest = async () => {
    setLoading(true); setError(null);
    try {
      /* Generate sample actual/predicted arrays */
      const n = 250;
      const actual = Array.from({ length: n }, () => Math.random() < 0.03 ? 1 : 0);
      const predicted = actual.map(a => a === 1 ? 0.02 + Math.random() * 0.06 : Math.random() * 0.03);
      const { data } = await axios.post(`${API_BASE}/api/v1/model-validation/backtest`, {
        model_id: btModel, actual_values: actual, predicted_values: predicted, confidence_level: Number(btConf),
      });
      setBtResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const runCompare = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/model-validation/compare-models`, {
        champion_id: champId, challenger_id: challId,
        test_data: { n_observations: 500, default_rate: 0.03 },
      });
      setCompareResult(data);
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  const transitionLifecycle = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/model-validation/transition-lifecycle`, {
        model_id: lcModel || btModel, from_state: lcFrom, to_state: lcTo, justification: lcJustification,
      });
      setLcResult(data);
      loadInventory();
    } catch (e) { setError(e.response?.data?.detail || e.message); } finally { setLoading(false); }
  };

  /* Traffic light color */
  const tlColor = (status) => {
    if (!status) return "bg-gray-100 text-gray-500";
    const s = status.toLowerCase();
    if (s === "green" || s === "pass") return "bg-emerald-500/10 text-emerald-400";
    if (s === "amber" || s === "warning") return "bg-amber-500/10 text-amber-400";
    return "bg-red-500/10 text-red-400";
  };

  return (
    <div className="space-y-4">
      <ErrBox msg={error} />

      {/* Dashboard KPIs */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <KpiCard label="Total Models" value={dashboard.total_models || 0} />
          <KpiCard label="In Production" value={dashboard.in_production || 0} color="text-gray-800" />
          <KpiCard label="Overdue Validations" value={dashboard.overdue_validations || 0} color={dashboard.overdue_validations > 0 ? "text-red-400" : "text-emerald-400"} />
          <KpiCard label="Compliance %" value={fmtPct(dashboard.compliance_pct)} color="text-emerald-400" />
        </div>
      )}

      {/* Backtest */}
      <Section title="Backtesting" accent="bg-blue-600">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Model">
              <Select value={btModel} onChange={setBtModel} options={modelOpts.length ? modelOpts : [{ value: "", label: "Loading..." }]} />
            </InputRow>
            <InputRow label="Confidence Level">
              <Select value={btConf} onChange={setBtConf} options={["0.95", "0.99", "0.999"].map(v => ({ value: v, label: `${(v * 100).toFixed(1)}%` }))} />
            </InputRow>
            <Btn onClick={runBacktest} disabled={loading}>{loading ? <Spinner /> : <Play className="h-3 w-3" />} Run Backtest (250 obs)</Btn>
          </div>
          {btResult && (
            <div>
              {/* Traffic light */}
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${tlColor(btResult.traffic_light)}`}>
                  {btResult.traffic_light === "green" ? <CheckCircle className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">Traffic Light: {(btResult.traffic_light || "").toUpperCase()}</p>
                  <p className="text-[10px] text-gray-500">Exceptions: {btResult.exceptions ?? "\u2014"} / {btResult.observations ?? 250}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <KpiCard label="Kupiec POF p-value" value={fmt2(btResult.kupiec_pof_pvalue)} />
                <KpiCard label="Brier Score" value={fmt2(btResult.brier_score)} />
              </div>
            </div>
          )}
        </div>

        {/* Statistical tests table */}
        {btResult?.test_results && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead><tr className="border-b border-gray-200">
                <th className="text-left py-2 px-2 text-gray-500 font-medium">Test</th>
                <th className="text-right py-2 px-2 text-gray-500 font-medium">Statistic</th>
                <th className="text-right py-2 px-2 text-gray-500 font-medium">p-value</th>
                <th className="text-center py-2 px-2 text-gray-500 font-medium">Result</th>
              </tr></thead>
              <tbody>
                {(btResult.test_results || []).map((t, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-1.5 px-2 text-gray-600">{t.test_name || STAT_TESTS[i]}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-gray-500">{fmt2(t.statistic)}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-gray-500">{fmt2(t.p_value)}</td>
                    <td className="py-1.5 px-2 text-center">
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${tlColor(t.result)}`}>{(t.result || "").toUpperCase()}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* Champion vs Challenger */}
      <Section title="Champion vs Challenger Comparison" accent="bg-purple-400">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Champion Model">
              <Select value={champId} onChange={setChampId} options={modelOpts.length ? modelOpts : [{ value: "", label: "Loading..." }]} />
            </InputRow>
            <InputRow label="Challenger Model">
              <Select value={challId} onChange={setChallId} options={modelOpts.length ? modelOpts : [{ value: "", label: "Loading..." }]} />
            </InputRow>
            <Btn onClick={runCompare} disabled={loading}>{loading ? <Spinner /> : <ArrowRightLeft className="h-3 w-3" />} Compare Models</Btn>
          </div>
          {compareResult && (
            <div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <KpiCard label="Champion AUC" value={fmt2(compareResult.champion_auc)} color="text-gray-800" />
                <KpiCard label="Challenger AUC" value={fmt2(compareResult.challenger_auc)} color="text-purple-300" />
                <KpiCard label="AUC Delta" value={fmt2(compareResult.auc_delta)} color={compareResult.auc_delta > 0 ? "text-emerald-400" : "text-red-400"} />
                <KpiCard label="Recommendation" value={compareResult.recommendation || "\u2014"} />
              </div>
              {compareResult.metrics && (
                <div className="bg-white rounded-lg border border-gray-200 p-3">
                  <p className="text-[10px] text-gray-500 uppercase mb-2">Metric Comparison</p>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={compareResult.metrics}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="metric" tick={{ fontSize: 8, fill: "rgba(255,255,255,0.4)" }} />
                      <YAxis tick={{ fontSize: 8, fill: "rgba(255,255,255,0.4)" }} />
                      <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", fontSize: 11, color: "#fff" }} />
                      <Legend wrapperStyle={{ fontSize: 10 }} />
                      <Bar dataKey="champion" name="Champion" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="challenger" name="Challenger" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      </Section>

      {/* Lifecycle Transition */}
      <Section title="Model Lifecycle Transition" accent="bg-amber-400">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <InputRow label="Model">
              <Select value={lcModel || btModel} onChange={setLcModel} options={modelOpts.length ? modelOpts : [{ value: "", label: "Loading..." }]} />
            </InputRow>
            <InputRow label="From State">
              <Select value={lcFrom} onChange={setLcFrom} options={LIFECYCLE_STATES} />
            </InputRow>
            <InputRow label="To State">
              <Select value={lcTo} onChange={setLcTo} options={LIFECYCLE_STATES} />
            </InputRow>
            <InputRow label="Justification">
              <Input value={lcJustification} onChange={setLcJustification} placeholder="Reason for transition..." />
            </InputRow>
            <Btn onClick={transitionLifecycle} disabled={loading}>{loading ? <Spinner /> : <ArrowRightLeft className="h-3 w-3" />} Transition</Btn>
          </div>
          <div>
            {/* State machine visualization */}
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Lifecycle State Machine</p>
            <div className="flex flex-wrap gap-1.5">
              {LIFECYCLE_STATES.map((s, i) => (
                <React.Fragment key={s.value}>
                  <span className={`text-[9px] font-mono font-bold px-2 py-1 rounded border ${s.color} ${lcFrom === s.value ? "ring-1 ring-black/20" : ""}`}>
                    {s.label}
                  </span>
                  {i < LIFECYCLE_STATES.length - 1 && <span className="text-gray-400 self-center text-xs">&rarr;</span>}
                </React.Fragment>
              ))}
            </div>
            {lcResult && (
              <div className="mt-3 bg-emerald-500/5 border border-emerald-500/20 rounded p-3 text-[11px] text-emerald-400 flex items-start gap-2">
                <CheckCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                Transition from <span className="font-mono">{lcResult.from_state}</span> to <span className="font-mono">{lcResult.to_state}</span> recorded.
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* Model Inventory Table */}
      <Section title="Model Inventory" defaultOpen={false} accent="bg-blue-400">
        <Btn onClick={loadInventory} variant="secondary"><RefreshCw className="h-3 w-3" /> Refresh</Btn>
        {inventory.length > 0 && (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead><tr className="border-b border-gray-200">
                <th className="text-left py-2 px-2 text-gray-500 font-medium">Model ID</th>
                <th className="text-left py-2 px-2 text-gray-500 font-medium">Name</th>
                <th className="text-left py-2 px-2 text-gray-500 font-medium">Type</th>
                <th className="text-center py-2 px-2 text-gray-500 font-medium">State</th>
                <th className="text-center py-2 px-2 text-gray-500 font-medium">Last Validated</th>
                <th className="text-center py-2 px-2 text-gray-500 font-medium">Next Due</th>
              </tr></thead>
              <tbody>
                {inventory.map((m, i) => {
                  const st = LIFECYCLE_STATES.find(s => s.value === m.state) || LIFECYCLE_STATES[0];
                  return (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-1.5 px-2 font-mono text-gray-500">{m.model_id || m.id}</td>
                      <td className="py-1.5 px-2 text-gray-600">{m.name}</td>
                      <td className="py-1.5 px-2 text-gray-500">{m.type || m.model_type || "\u2014"}</td>
                      <td className="py-1.5 px-2 text-center">
                        <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${st.color}`}>{st.label}</span>
                      </td>
                      <td className="py-1.5 px-2 text-center text-gray-500">{m.last_validated || "\u2014"}</td>
                      <td className="py-1.5 px-2 text-center text-gray-500">{m.next_validation_due || "\u2014"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {inventory.length === 0 && <p className="text-[11px] text-gray-500 mt-2">No models in inventory. Load catalog or run assessments first.</p>}
      </Section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════════════ */

const TABS = [
  { id: "basel", label: "Basel III/IV Capital", icon: Landmark, color: "text-gray-700" },
  { id: "pcaf", label: "PCAF Data Quality", icon: ShieldCheck, color: "text-emerald-400" },
  { id: "validation", label: "Model Validation", icon: FlaskConical, color: "text-purple-400" },
];

export default function BankingCapitalPage() {
  const [activeTab, setActiveTab] = useState("basel");

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Landmark className="h-6 w-6 text-gray-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Banking & Capital Engines</h1>
              <p className="text-gray-500 text-sm">Basel III/IV capital adequacy, PCAF data quality scoring, model validation framework</p>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-100 text-gray-700 border border-gray-200">CRR III / CRD VI</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PCAF Global Standard</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">SR 11-7 / SS1/23</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-1 bg-gray-50 rounded-lg mb-6">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-xs font-medium transition-all flex-1 justify-center
                  ${active ? "bg-[#1a2234] text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-600 hover:bg-gray-50"}`}>
                <Icon className={`h-4 w-4 ${active ? tab.color : ""}`} />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        {activeTab === "basel" && <BaselPanel />}
        {activeTab === "pcaf" && <PCAFQualityPanel />}
        {activeTab === "validation" && <ModelValidationPanel />}
      </div>
    </div>
  );
}
