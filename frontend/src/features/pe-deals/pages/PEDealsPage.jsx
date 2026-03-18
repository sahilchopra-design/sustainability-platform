/**
 * Private Equity Deal & Portfolio Platform
 *
 * Tab 1 — Deal Pipeline      /api/v1/pe-deals  (ESG screening, red flags)
 * Tab 2 — Portfolio Monitor  /api/v1/pe-portfolio  (KPI traffic light dashboard)
 * Tab 3 — Value Creation     /api/v1/pe-value-creation  (levers, exit value)
 * Tab 4 — IRR Sensitivity    /api/v1/pe-reporting/irr-sensitivity  (carbon/reg/green)
 * Tab 5 — Impact Framework   /api/v1/pe-reporting/impact  (IRIS+ / SDG)
 */
import React, { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Legend, ScatterChart, Scatter,
} from "recharts";
import {
  Briefcase, TrendingUp, Gauge, Leaf, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, XCircle, Play, RefreshCw,
  BarChart3, Target, Users, Globe, Activity, Star,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
function sr(seed) { let s = seed; return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }; }
const TOOLTIP_STYLE = { backgroundColor: "#fff", border: "1px solid rgba(0,0,0,0.08)", color: "#111" };
const fmt1 = (v) => v == null ? "—" : Number(v).toFixed(1);
const fmtPct = (v) => v == null ? "—" : `${Number(v).toFixed(1)}%`;

/* ── Primitives ──────────────────────────────────────────────────────────── */
function Section({ title, children, defaultOpen = true, icon: Icon }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-3.5 w-3.5 text-gray-500" />}
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

function Row({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <label className="text-[11px] text-gray-500 w-40 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = "text", placeholder }) {
  return (
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      className="w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800
        placeholder-gray-400 focus:outline-none focus:border-blue-500" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800
        focus:outline-none focus:border-blue-500">
      {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  );
}

function Btn({ onClick, disabled, loading, children }) {
  return (
    <button onClick={onClick} disabled={disabled || loading}
      className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#164E8A] text-white rounded text-xs font-medium hover:bg-[#12407A] disabled:opacity-40 transition-all">
      {loading && <RefreshCw className="h-3 w-3 animate-spin" />}
      {children}
    </button>
  );
}

function TrafficLight({ score }) {
  if (score >= 70) return <span className="inline-flex items-center gap-1 text-emerald-700 text-xs font-semibold"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />Green</span>;
  if (score >= 40) return <span className="inline-flex items-center gap-1 text-amber-600 text-xs font-semibold"><span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />Amber</span>;
  return <span className="inline-flex items-center gap-1 text-red-600 text-xs font-semibold"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" />Red</span>;
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 1 — DEAL PIPELINE
══════════════════════════════════════════════════════════════════════════ */
function PipelineTab() {
  const [companyName, setCompanyName] = useState("GreenTech Solutions GmbH");
  const [sector, setSector] = useState("technology");
  const [revenue, setRevenue] = useState("120");
  const [ebitda, setEbitda] = useState("28");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const DEALS = [
    { company: "GreenTech Solutions", sector: "Technology", stage: "Diligence", esg: 78, flag: false, ev: "€420M" },
    { company: "Nordic Biomass", sector: "Energy", stage: "LOI", esg: 82, flag: false, ev: "€180M" },
    { company: "Logistics Alpha", sector: "Transportation", stage: "Screening", esg: 44, flag: true, ev: "€290M" },
    { company: "Steel Corp Baltics", sector: "Metals", stage: "Monitoring", esg: 32, flag: true, ev: "€670M" },
    { company: "AgriFood Chain", sector: "Agriculture", stage: "Diligence", esg: 67, flag: false, ev: "€95M" },
    { company: "EU Solar Platform", sector: "Energy", stage: "Closed", esg: 89, flag: false, ev: "€310M" },
  ];

  async function runScreen() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/pe-reporting/esg-screen`, {
        company_name: companyName, sector, revenue_meur: parseFloat(revenue),
        ebitda_meur: parseFloat(ebitda),
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Screening failed");
    } finally { setLoading(false); }
  }

  const STAGE_COUNTS = [
    { stage: "Sourcing", count: 22 }, { stage: "Screening", count: 12 },
    { stage: "LOI", count: 6 }, { stage: "Diligence", count: 3 },
    { stage: "Closed", count: 1 },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Active Deals" value="44" sub="In pipeline" />
        <KpiCard label="Avg ESG Score" value="68 / 100" sub="Screened companies" />
        <KpiCard label="Red Flags" value="8" sub="ESG / governance" color="text-red-500" />
        <KpiCard label="Closed YTD" value="3" sub="€910M deployed" color="text-emerald-600" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Pipeline Funnel" icon={BarChart3}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={STAGE_COUNTS} layout="vertical" margin={{ left: 0, right: 20, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis dataKey="stage" type="category" tick={{ fontSize: 10 }} width={70} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="count" fill="#111" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Deal Tracker" icon={Briefcase}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  {["Company", "Sector", "Stage", "ESG", "Flag", "EV"].map(h => (
                    <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DEALS.map(d => (
                  <tr key={d.company} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-1.5 px-2 font-medium text-gray-700 max-w-[110px] truncate">{d.company}</td>
                    <td className="py-1.5 px-2 text-gray-500">{d.sector}</td>
                    <td className="py-1.5 px-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        d.stage === "Closed" ? "bg-emerald-50 text-emerald-700" :
                        d.stage === "Diligence" ? "bg-blue-50 text-blue-700" : "bg-gray-100 text-gray-600"
                      }`}>{d.stage}</span>
                    </td>
                    <td className="py-1.5 px-2"><TrafficLight score={d.esg} /></td>
                    <td className="py-1.5 px-2">{d.flag ? <AlertTriangle className="h-3.5 w-3.5 text-red-400" /> : <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />}</td>
                    <td className="py-1.5 px-2 font-mono text-gray-600">{d.ev}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      </div>

      <Section title="ESG Screening — New Deal" icon={Play}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
          <div>
            <Row label="Company Name"><Inp value={companyName} onChange={setCompanyName} /></Row>
            <Row label="Sector">
              <Sel value={sector} onChange={setSector} options={[
                { v: "technology", l: "Technology" }, { v: "energy", l: "Energy" },
                { v: "real_estate", l: "Real Estate" }, { v: "financial_services", l: "Financial Services" },
                { v: "agriculture", l: "Agriculture" }, { v: "transportation", l: "Transportation" },
                { v: "mining", l: "Mining & Metals" }, { v: "healthcare", l: "Healthcare" },
              ]} />
            </Row>
          </div>
          <div>
            <Row label="Revenue (€M)"><Inp value={revenue} onChange={setRevenue} type="number" /></Row>
            <Row label="EBITDA (€M)"><Inp value={ebitda} onChange={setEbitda} type="number" /></Row>
          </div>
        </div>
        <Btn onClick={runScreen} loading={loading}><Play className="h-3 w-3" /> Screen Deal</Btn>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-gray-700">ESG Screening Result</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div><span className="text-gray-500">ESG Score:</span> <span className="font-medium">{result.esg_score ?? "—"}/100</span></div>
              <div><span className="text-gray-500">Red Flags:</span> <span className="font-medium text-red-500">{result.red_flags?.length ?? 0}</span></div>
              <div><span className="text-gray-500">Recommendation:</span> <span className="font-medium">{result.recommendation ?? "—"}</span></div>
              <div><span className="text-gray-500">Traffic Light:</span> <TrafficLight score={result.esg_score || 0} /></div>
            </div>
            {result.red_flags?.length > 0 && (
              <div className="mt-2">
                <p className="text-gray-500 mb-1">Red Flags:</p>
                <ul className="space-y-0.5">
                  {result.red_flags.map((f, i) => <li key={i} className="text-red-500 flex items-center gap-1"><AlertTriangle className="h-3 w-3 shrink-0" />{f}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 2 — PORTFOLIO MONITOR
══════════════════════════════════════════════════════════════════════════ */
function PortfolioMonitorTab() {
  const PORT_COMPANIES = [
    { name: "EU Solar Platform", vintage: 2022, sector: "Energy", rev: 148, ebitda: 62, esg: 91, ghg: 12, target: "on-track" },
    { name: "GreenTech Solutions", vintage: 2021, sector: "Technology", rev: 134, ebitda: 31, esg: 78, ghg: 24, target: "on-track" },
    { name: "AgriFood Chain", vintage: 2020, sector: "Agriculture", rev: 89, ebitda: 17, esg: 67, ghg: 48, target: "off-track" },
    { name: "Nordic Biomass", vintage: 2023, sector: "Energy", rev: 58, ebitda: 14, esg: 82, ghg: 18, target: "on-track" },
    { name: "MedTech Care", vintage: 2019, sector: "Healthcare", rev: 210, ebitda: 55, esg: 73, ghg: 31, target: "on-track" },
  ];

  const ESG_RADAR = [
    { subject: "Governance", A: 88 }, { subject: "Environment", A: 72 },
    { subject: "Social", A: 65 }, { subject: "Climate", A: 74 },
    { subject: "Data Quality", A: 81 },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Portfolio Companies" value="5" sub="Active investments" />
        <KpiCard label="Avg ESG Score" value="78 / 100" sub="Portfolio weighted" />
        <KpiCard label="On-Track Targets" value="4 / 5" sub="SBTi aligned" color="text-emerald-600" />
        <KpiCard label="Total AUM" value="€1.2B" sub="NAV" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="ESG Radar — Portfolio Average" icon={Target}>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={ESG_RADAR}>
              <PolarGrid stroke="rgba(0,0,0,0.06)" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
              <Radar dataKey="A" stroke="#111" fill="#111" fillOpacity={0.12} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="GHG Intensity by Company (tCO₂e/€M rev)" icon={Leaf}>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={PORT_COMPANIES} layout="vertical" margin={{ left: 0, right: 30, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={100} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="ghg" fill="#ef4444" radius={[0, 3, 3, 0]} name="GHG Intensity" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="Portfolio Company Dashboard" icon={Activity}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {["Company", "Vintage", "Sector", "Rev €M", "EBITDA €M", "ESG", "GHG Intensity", "Target"].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PORT_COMPANIES.map(c => (
              <tr key={c.name} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 font-medium text-gray-700">{c.name}</td>
                <td className="py-1.5 px-2 text-gray-500">{c.vintage}</td>
                <td className="py-1.5 px-2 text-gray-500">{c.sector}</td>
                <td className="py-1.5 px-2 font-mono">{c.rev}</td>
                <td className="py-1.5 px-2 font-mono">{c.ebitda}</td>
                <td className="py-1.5 px-2"><TrafficLight score={c.esg} /></td>
                <td className="py-1.5 px-2 font-mono">{c.ghg}</td>
                <td className="py-1.5 px-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    c.target === "on-track" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                  }`}>{c.target === "on-track" ? "On Track" : "Off Track"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 3 — VALUE CREATION
══════════════════════════════════════════════════════════════════════════ */
function ValueCreationTab() {
  const [companyId, setCompanyId] = useState("port-eu-solar");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const LEVERS = [
    { lever: "Revenue Growth (5%)", ebitda_delta: 8.4, exit_ev_delta: 63, type: "growth" },
    { lever: "Margin Expansion (2pp)", ebitda_delta: 6.2, exit_ev_delta: 46, type: "margin" },
    { lever: "Green Premium (Cert)", ebitda_delta: 3.1, exit_ev_delta: 23, type: "esg" },
    { lever: "Carbon Cost Reduction", ebitda_delta: 1.8, exit_ev_delta: 14, type: "esg" },
    { lever: "Multiple Re-rating (ESG)", ebitda_delta: 0, exit_ev_delta: 38, type: "esg" },
    { lever: "Working Capital Opt.", ebitda_delta: 2.2, exit_ev_delta: 16, type: "operational" },
  ];

  async function run() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/pe-value-creation/analyse`, { company_id: companyId });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed");
    } finally { setLoading(false); }
  }

  const COLORS = { growth: "#111", margin: "#374151", esg: "#10b981", operational: "#3b82f6" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Entry EV" value="€310M" sub="EU Solar Platform" />
        <KpiCard label="Base Case Exit" value="€520M" sub="5-year hold" />
        <KpiCard label="ESG Value Uplift" value="+€75M" sub="Green premium + multiple" color="text-emerald-600" />
        <KpiCard label="Gross IRR" value="22.4%" sub="Base case" color="text-blue-600" />
      </div>

      <Section title="Value Creation Levers — EBITDA & EV Impact (€M)" icon={TrendingUp}>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={LEVERS} layout="vertical" margin={{ left: 10, right: 40, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10 }} />
            <YAxis dataKey="lever" type="category" tick={{ fontSize: 10 }} width={160} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: "11px" }} />
            <Bar dataKey="ebitda_delta" name="EBITDA Delta €M" fill="#111" radius={[0, 3, 3, 0]} />
            <Bar dataKey="exit_ev_delta" name="Exit EV Delta €M" fill="#10b981" radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Run Value Creation Analysis" icon={Play}>
        <Row label="Portfolio Company ID"><Inp value={companyId} onChange={setCompanyId} /></Row>
        <Btn onClick={run} loading={loading}><Play className="h-3 w-3" /> Analyse</Btn>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-gray-700">Value Creation Summary</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ["Total EV Uplift", result.total_ev_uplift_meur ? `€${result.total_ev_uplift_meur}M` : "—"],
                ["ESG Contribution", result.esg_contribution_pct ? `${result.esg_contribution_pct}%` : "—"],
                ["IRR Delta", result.irr_delta_pct ? `+${result.irr_delta_pct}pp` : "—"],
                ["Top Lever", result.top_lever ?? "—"],
              ].map(([l, v]) => (
                <div key={l}><span className="text-gray-500">{l}:</span> <span className="font-medium">{v}</span></div>
              ))}
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 4 — IRR SENSITIVITY
══════════════════════════════════════════════════════════════════════════ */
function IRRSensitivityTab() {
  const rng = sr(77);
  const SCENARIOS = ["Base Case", "Carbon Tax +50%", "Reg Tightening", "Green Premium", "Stranding Risk", "Market Downturn"];
  const IRRS = [22.4, 18.9, 16.2, 25.8, 12.1, 8.7];
  const MOICS = [2.8, 2.3, 2.0, 3.3, 1.6, 1.2];

  const CHART_DATA = SCENARIOS.map((s, i) => ({ scenario: s, irr: IRRS[i], moic: MOICS[i] }));
  const CARBON_SENS = [0, 25, 50, 75, 100, 150].map(c => ({
    carbon_price: c, irr: Math.max(5, 22.4 - c * 0.07 + (c === 0 ? 0 : -0.5)),
  }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Base IRR" value="22.4%" sub="5-year hold" color="text-emerald-600" />
        <KpiCard label="Base MOIC" value="2.8x" sub="Gross" />
        <KpiCard label="Downside IRR" value="8.7%" sub="Market downturn" color="text-red-500" />
        <KpiCard label="ESG Upside" value="+3.4pp" sub="Green premium scenario" color="text-blue-600" />
      </div>

      <Section title="IRR by Scenario" icon={BarChart3}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={CHART_DATA} margin={{ left: 10, right: 20, top: 4, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="scenario" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} unit="%" />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, "Gross IRR"]} />
            <Bar dataKey="irr" radius={[3, 3, 0, 0]}>
              {CHART_DATA.map((d, i) => (
                <Cell key={i} fill={d.irr >= 20 ? "#10b981" : d.irr >= 14 ? "#f59e0b" : "#ef4444"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Carbon Price Sensitivity → IRR" icon={Activity}>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={CARBON_SENS} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="carbon_price" tick={{ fontSize: 10 }} label={{ value: "Carbon Price (€/tCO₂)", position: "insideBottom", offset: -6, fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit="%" />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v.toFixed(1)}%`, "Gross IRR"]} />
            <Line type="monotone" dataKey="irr" stroke="#111" strokeWidth={2.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      <Section title="MOIC vs IRR — Scenario Scatter" icon={Star} defaultOpen={false}>
        <ResponsiveContainer width="100%" height={200}>
          <ScatterChart margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="moic" type="number" name="MOIC" tick={{ fontSize: 10 }} label={{ value: "MOIC (x)", position: "insideBottom", offset: -6, fontSize: 10 }} />
            <YAxis dataKey="irr" type="number" name="IRR" tick={{ fontSize: 10 }} unit="%" />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ strokeDasharray: "3 3" }} content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0]?.payload;
              return <div style={TOOLTIP_STYLE} className="px-2.5 py-2 rounded text-xs">
                <p className="font-semibold">{d?.scenario}</p>
                <p>IRR: {d?.irr}%</p><p>MOIC: {d?.moic}x</p>
              </div>;
            }} />
            <Scatter data={CHART_DATA} fill="#111" />
          </ScatterChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 5 — IMPACT FRAMEWORK (IRIS+ / SDG)
══════════════════════════════════════════════════════════════════════════ */
function ImpactTab() {
  const SDG_DATA = [
    { sdg: "SDG 7 Clean Energy", score: 92, companies: 3 },
    { sdg: "SDG 13 Climate Action", score: 81, companies: 5 },
    { sdg: "SDG 8 Decent Work", score: 68, companies: 4 },
    { sdg: "SDG 9 Industry & Innovation", score: 74, companies: 3 },
    { sdg: "SDG 2 Zero Hunger", score: 62, companies: 2 },
    { sdg: "SDG 15 Life on Land", score: 55, companies: 2 },
  ];

  const IRIS = [
    { metric: "GHG Avoided (tCO₂e)", value: "42,400", trend: "+" },
    { metric: "Renewable MWh Generated", value: "284,000", trend: "+" },
    { metric: "Jobs Created", value: "1,240", trend: "+" },
    { metric: "Water Saved (m³)", value: "88,000", trend: "+" },
    { metric: "Certified Organic Ha", value: "3,200", trend: "+" },
    { metric: "Women in Leadership %", value: "38%", trend: "+" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="SDGs Addressed" value="6 / 17" sub="Portfolio coverage" />
        <KpiCard label="IRIS+ Metrics" value="14" sub="Tracked across portfolio" />
        <KpiCard label="GHG Avoided" value="42,400 t" sub="tCO₂e FY2024" color="text-emerald-600" />
        <KpiCard label="Impact Score" value="74 / 100" sub="ILPA ESG convergence" />
      </div>

      <Section title="SDG Contribution Scores" icon={Globe}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={SDG_DATA} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
            <YAxis dataKey="sdg" type="category" tick={{ fontSize: 10 }} width={140} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}/100`, "Score"]} />
            <Bar dataKey="score" radius={[0, 3, 3, 0]}>
              {SDG_DATA.map((d, i) => (
                <Cell key={i} fill={d.score >= 80 ? "#10b981" : d.score >= 60 ? "#f59e0b" : "#ef4444"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="IRIS+ Core Metrics (FY2024)" icon={Activity}>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {IRIS.map(m => (
            <div key={m.metric} className="bg-white border border-gray-200 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 mb-1">{m.metric}</p>
              <p className="text-base font-semibold text-gray-900 font-mono">{m.value}</p>
              <span className="text-[10px] text-emerald-600">▲ YoY</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   ROOT
══════════════════════════════════════════════════════════════════════════ */
const TABS = [
  { id: "pipeline", label: "Deal Pipeline", icon: Briefcase },
  { id: "monitor", label: "Portfolio Monitor", icon: Activity },
  { id: "value", label: "Value Creation", icon: TrendingUp },
  { id: "irr", label: "IRR Sensitivity", icon: Gauge },
  { id: "impact", label: "Impact Framework", icon: Leaf },
];

export default function PEDealsPage() {
  const [tab, setTab] = useState("pipeline");

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Private Equity — Deal & Portfolio Platform</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Deal pipeline · ESG screening · Portfolio monitoring · Value creation · IRR sensitivity · IRIS+ impact
          </p>
        </div>
        <div className="flex gap-1.5">
          {["ILPA ESG", "IRIS+", "SDG", "SBTi"].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

      {/* Tab bar */}
      <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                tab === t.id ? "bg-white text-gray-900 shadow-sm border border-gray-200" : "text-gray-500 hover:text-gray-700"
              }`}>
              <Icon className="h-3 w-3" />{t.label}
            </button>
          );
        })}
      </div>

      {tab === "pipeline" && <PipelineTab />}
      {tab === "monitor" && <PortfolioMonitorTab />}
      {tab === "value" && <ValueCreationTab />}
      {tab === "irr" && <IRRSensitivityTab />}
      {tab === "impact" && <ImpactTab />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">ESG Screening:</span> UNPRI responsible investment principles, SFDR Article 8/9 classification, exclusion list (weapons/tobacco/coal/arctic O&G)</p>
        <p><span className="font-semibold text-gray-500">Impact:</span> IRIS+ Core Metrics Set v5 · UN SDG contribution framework · ILPA ESG Data Convergence</p>
        <p><span className="font-semibold text-gray-500">IRR:</span> Carbon pricing sensitivity per EU ETS forward curve · Stranding risk per NGFS net-zero · Green premium per CRREM</p>
      </div>
    </div>
  );
}
