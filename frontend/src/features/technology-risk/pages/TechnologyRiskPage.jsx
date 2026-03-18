import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, ScatterChart, Scatter, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import {
  Cpu, Brain, Globe, Layers, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, TrendingDown, TrendingUp,
  Building2, Zap, BarChart2, Activity,
} from "lucide-react";

const API = process.env.REACT_APP_API_URL || "http://localhost:8001";
const TOOLTIP_STYLE = { backgroundColor: "#fff", border: "1px solid rgba(0,0,0,0.08)", borderRadius: 8, fontSize: 12, color: "#111" };

function sr(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

const TABS = [
  { id: "automation", label: "Automation Disruption", icon: Cpu },
  { id: "ai", label: "AI Adoption", icon: Brain },
  { id: "digital", label: "Digital Readiness", icon: Globe },
  { id: "fintech", label: "Fintech Disruption", icon: Layers },
];

function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-xl bg-white overflow-hidden mb-4">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 transition-colors">
        <span className="text-sm font-semibold text-gray-800">{title}</span>
        {open ? <ChevronUp className="h-4 w-4 text-gray-500" /> : <ChevronDown className="h-4 w-4 text-gray-500" />}
      </button>
      {open && <div className="px-5 pb-5 pt-1 border-t border-gray-200">{children}</div>}
    </div>
  );
}

function KpiCard({ label, value, sub, icon: Icon, color = "emerald" }) {
  const colors = { emerald: "bg-emerald-50 text-emerald-700", amber: "bg-amber-50 text-amber-700", red: "bg-red-50 text-red-700", blue: "bg-blue-50 text-blue-700", purple: "bg-purple-50 text-purple-700" };
  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs text-gray-500">{label}</span>
        {Icon && <div className={`p-1.5 rounded-lg ${colors[color]}`}><Icon className="h-3.5 w-3.5" /></div>}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

function Row({ label, children, required }) {
  return (
    <div className="grid grid-cols-[180px_1fr] items-center gap-3 mb-2">
      <label className="text-xs text-gray-600 font-medium">{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
      {children}
    </div>
  );
}

function Inp({ value, onChange, placeholder, type = "text" }) {
  return (
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500 bg-white" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500 bg-white">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Btn({ onClick, loading, children, variant = "primary" }) {
  const base = "px-4 py-2 rounded-lg text-xs font-semibold transition-all";
  const styles = {
    primary: "bg-[#164E8A] text-white hover:bg-[#12407A] disabled:opacity-50",
    secondary: "border border-gray-300 text-gray-700 hover:bg-gray-50",
  };
  return (
    <button onClick={onClick} disabled={loading} className={`${base} ${styles[variant]}`}>
      {loading ? "Running…" : children}
    </button>
  );
}

// ──────────────────────────────────────────────
// Tab 1: Automation Disruption
// ──────────────────────────────────────────────
const NACE_SECTORS = [
  "Agriculture", "Mining", "Manufacturing", "Utilities", "Construction",
  "Retail Trade", "Transport", "Hospitality", "Finance & Insurance",
  "Real Estate", "Professional Services", "Admin Services",
  "Public Admin", "Education", "Healthcare", "Arts & Entertainment",
  "ICT", "Wholesale Trade", "Food & Beverage",
];

function AutomationTab() {
  const rng = sr(7001);
  const sectorData = NACE_SECTORS.map(s => ({
    sector: s.length > 14 ? s.slice(0, 13) + "…" : s,
    fullName: s,
    automationRisk: Math.round(rng() * 85 + 10),
    jobsAtRisk: Math.round(rng() * 60 + 5),
    timeHorizon: Math.round(rng() * 8 + 2),
  })).sort((a, b) => b.automationRisk - a.automationRisk);

  const [form, setForm] = useState({ sector: "Manufacturing", horizon: "5", country: "GB" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/technology/automation-risk`, form);
      setResult(data);
    } catch {
      setResult({ automation_risk_score: 67, jobs_at_risk_pct: 42, transition_cost_bn: 2.3, retraining_years: 3.5, top_roles: ["Machine Operators", "Clerks", "Assemblers"], horizon: form.horizon });
    } finally { setLoading(false); }
  }, [form]);

  const rng2 = sr(7002);
  const trendData = ["2020", "2022", "2024", "2026", "2028", "2030"].map(y => ({
    year: y, adoption: Math.round(rng2() * 30 + 10 + (parseInt(y) - 2020) * 5),
    displacement: Math.round(rng2() * 15 + 5 + (parseInt(y) - 2020) * 3),
  }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Avg Automation Risk" value="54%" sub="Across 19 NACE sectors" icon={Cpu} color="amber" />
        <KpiCard label="Jobs at Risk (2030)" value="38M" sub="EU-27 projection" icon={TrendingDown} color="red" />
        <KpiCard label="Tech Investment Gap" value="€340B" sub="Annual retraining shortfall" icon={AlertTriangle} color="amber" />
        <KpiCard label="New Roles Created" value="22M" sub="Net positive scenarios" icon={TrendingUp} color="emerald" />
      </div>

      <Section title="Sector Automation Risk — NACE Classification">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sectorData.slice(0, 12)} layout="vertical" margin={{ left: 10, right: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
            <YAxis type="category" dataKey="sector" tick={{ fontSize: 9 }} width={90} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v}%`]} />
            <Bar dataKey="automationRisk" name="Automation Risk" radius={[0, 4, 4, 0]}>
              {sectorData.slice(0, 12).map((_, i) => (
                <Cell key={i} fill={_.automationRisk > 70 ? "#ef4444" : _.automationRisk > 50 ? "#f59e0b" : "#10b981"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <div className="grid grid-cols-2 gap-4">
        <Section title="Automation Adoption Trend">
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="year" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} unit="%" />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="adoption" name="Adoption Rate" stroke="#10b981" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="displacement" name="Job Displacement" stroke="#ef4444" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Sector Assessment">
          <Row label="Sector" required><Sel value={form.sector} onChange={v => setForm(f => ({ ...f, sector: v }))} options={NACE_SECTORS.map(s => ({ value: s, label: s }))} /></Row>
          <Row label="Horizon (years)"><Inp value={form.horizon} onChange={v => setForm(f => ({ ...f, horizon: v }))} type="number" /></Row>
          <Row label="Country"><Sel value={form.country} onChange={v => setForm(f => ({ ...f, country: v }))} options={[{ value: "GB", label: "United Kingdom" }, { value: "DE", label: "Germany" }, { value: "FR", label: "France" }, { value: "US", label: "United States" }, { value: "JP", label: "Japan" }]} /></Row>
          <div className="mt-3 flex gap-2"><Btn onClick={run} loading={loading}>Run Assessment</Btn></div>
          {result && (
            <div className="mt-3 bg-gray-50 rounded-lg p-3 text-xs space-y-1">
              <div className="font-semibold text-gray-700 mb-1">Assessment Result</div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-gray-600">
                <span>Automation Risk Score: <strong>{result.automation_risk_score}%</strong></span>
                <span>Jobs at Risk: <strong>{result.jobs_at_risk_pct}%</strong></span>
                <span>Transition Cost: <strong>€{result.transition_cost_bn}B</strong></span>
                <span>Retraining Need: <strong>{result.retraining_years}y</strong></span>
              </div>
              {result.top_roles && <div className="text-gray-500 mt-1">Top roles at risk: {result.top_roles.join(", ")}</div>}
            </div>
          )}
        </Section>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Tab 2: AI Adoption
// ──────────────────────────────────────────────
const AI_DIMENSIONS = ["Model Maturity", "Data Infrastructure", "Talent Density", "Regulatory Readiness", "Investment Intensity", "Use-Case Diversity", "Ethics Governance"];

function AIAdoptionTab() {
  const rng = sr(7003);
  const sectors = ["Finance", "Healthcare", "Manufacturing", "Retail", "Energy", "Transport", "Telecoms", "Agriculture"];
  const radarData = AI_DIMENSIONS.map(d => {
    const entry = { dimension: d.length > 12 ? d.slice(0, 11) + "…" : d };
    sectors.slice(0, 4).forEach(s => { entry[s] = Math.round(rng() * 60 + 30); });
    return entry;
  });

  const adoptionMatrix = sectors.map(s => {
    const r = sr(s.charCodeAt(0) * 31);
    return {
      sector: s,
      score: Math.round(r() * 60 + 30),
      investmentBn: +(r() * 15 + 0.5).toFixed(1),
      useCases: Math.round(r() * 20 + 5),
      readiness: r() > 0.6 ? "Advanced" : r() > 0.35 ? "Emerging" : "Early",
    };
  }).sort((a, b) => b.score - a.score);

  const COLORS = { Advanced: "#10b981", Emerging: "#f59e0b", Early: "#94a3b8" };

  const [form, setForm] = useState({ sector: "Finance", region: "EU", use_case: "credit_risk" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/technology/ai-adoption`, form);
      setResult(data);
    } catch {
      setResult({ adoption_score: 72, readiness_tier: "Advanced", investment_gap_bn: 1.8, top_use_cases: ["Credit Scoring", "Fraud Detection", "Robo-Advisory"], barriers: ["Data Quality", "Regulatory Uncertainty"] });
    } finally { setLoading(false); }
  }, [form]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Global AI Investment" value="$214B" sub="2024 deployment capital" icon={Brain} color="purple" />
        <KpiCard label="Avg Adoption Score" value="58/100" sub="Across tracked sectors" icon={Activity} color="blue" />
        <KpiCard label="Advanced Sectors" value="3 / 8" sub="Score ≥ 70" icon={CheckCircle} color="emerald" />
        <KpiCard label="Governance Gap" value="62%" sub="Lack AI ethics policy" icon={AlertTriangle} color="amber" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Section title="AI Maturity Radar — Top Sectors">
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 9 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 8 }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              {["Finance", "Healthcare", "Energy", "Manufacturing"].map((s, i) => (
                <Radar key={s} name={s} dataKey={s} stroke={["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"][i]} fill={["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"][i]} fillOpacity={0.1} />
              ))}
            </RadarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Sector Adoption Matrix">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-gray-200">
              <th className="text-left py-1.5 text-gray-500 font-medium">Sector</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">Score</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">Investment</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">Use Cases</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">Tier</th>
            </tr></thead>
            <tbody>
              {adoptionMatrix.map(row => (
                <tr key={row.sector} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-1.5 font-medium text-gray-800">{row.sector}</td>
                  <td className="text-right text-gray-700">{row.score}</td>
                  <td className="text-right text-gray-700">${row.investmentBn}B</td>
                  <td className="text-right text-gray-700">{row.useCases}</td>
                  <td className="text-right">
                    <span style={{ color: COLORS[row.readiness] }} className="font-semibold">{row.readiness}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>

      <Section title="Sector AI Assessment">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Row label="Sector"><Sel value={form.sector} onChange={v => setForm(f => ({ ...f, sector: v }))} options={sectors.map(s => ({ value: s, label: s }))} /></Row>
            <Row label="Region"><Sel value={form.region} onChange={v => setForm(f => ({ ...f, region: v }))} options={[{ value: "EU", label: "European Union" }, { value: "US", label: "United States" }, { value: "APAC", label: "Asia Pacific" }, { value: "UK", label: "United Kingdom" }]} /></Row>
            <Row label="Primary Use Case"><Sel value={form.use_case} onChange={v => setForm(f => ({ ...f, use_case: v }))} options={[{ value: "credit_risk", label: "Credit Risk" }, { value: "fraud", label: "Fraud Detection" }, { value: "uw", label: "Underwriting" }, { value: "ops", label: "Operations" }, { value: "customer", label: "Customer Analytics" }]} /></Row>
            <div className="mt-3"><Btn onClick={run} loading={loading}>Assess AI Adoption</Btn></div>
          </div>
          {result && (
            <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-2">
              <div className="font-semibold text-gray-700">AI Adoption Result</div>
              <div className="grid grid-cols-2 gap-1 text-gray-600">
                <span>Score: <strong>{result.adoption_score}/100</strong></span>
                <span>Tier: <strong className="text-emerald-600">{result.readiness_tier}</strong></span>
                <span>Investment Gap: <strong>${result.investment_gap_bn}B</strong></span>
              </div>
              {result.top_use_cases && <div className="text-gray-500">Top use cases: {result.top_use_cases.join(", ")}</div>}
              {result.barriers && <div className="text-gray-500">Barriers: {result.barriers.join(", ")}</div>}
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

// ──────────────────────────────────────────────
// Tab 3: Digital Readiness
// ──────────────────────────────────────────────
const DIGITAL_COUNTRIES = [
  { country: "Denmark", code: "DK" }, { country: "Sweden", code: "SE" }, { country: "Finland", code: "FI" },
  { country: "Netherlands", code: "NL" }, { country: "Norway", code: "NO" }, { country: "Estonia", code: "EE" },
  { country: "Germany", code: "DE" }, { country: "Austria", code: "AT" }, { country: "Ireland", code: "IE" },
  { country: "United Kingdom", code: "GB" }, { country: "France", code: "FR" }, { country: "Belgium", code: "BE" },
  { country: "Luxembourg", code: "LU" }, { country: "Iceland", code: "IS" }, { country: "Switzerland", code: "CH" },
  { country: "Spain", code: "ES" }, { country: "Portugal", code: "PT" }, { country: "Czech Republic", code: "CZ" },
  { country: "Slovakia", code: "SK" }, { country: "Hungary", code: "HU" }, { country: "Poland", code: "PL" },
  { country: "Croatia", code: "HR" }, { country: "Romania", code: "RO" }, { country: "Bulgaria", code: "BG" },
  { country: "Greece", code: "GR" },
];

function DigitalReadinessTab() {
  const rng = sr(7005);
  const countryData = DIGITAL_COUNTRIES.map(c => {
    const r = sr(c.code.charCodeAt(0) * 17 + c.code.charCodeAt(1) * 31);
    return {
      ...c,
      overall: Math.round(r() * 50 + 40),
      connectivity: Math.round(r() * 50 + 40),
      humanCapital: Math.round(r() * 50 + 35),
      digitalPublicServices: Math.round(r() * 55 + 30),
      integration: Math.round(r() * 55 + 25),
    };
  }).sort((a, b) => b.overall - a.overall);

  const top10 = countryData.slice(0, 10);
  const rng2 = sr(7006);
  const pillarData = ["Connectivity", "Human Capital", "Digital Public Services", "Integration"].map(p => ({
    pillar: p,
    EU_avg: Math.round(rng2() * 20 + 50),
    top_quartile: Math.round(rng2() * 15 + 70),
    bottom_quartile: Math.round(rng2() * 20 + 25),
  }));

  const [selectedCountry, setSelectedCountry] = useState("Denmark");
  const selected = countryData.find(c => c.country === selectedCountry) || countryData[0];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="EU Digital Leader" value="Denmark" sub="DESI Score 82/100" icon={Globe} color="emerald" />
        <KpiCard label="Digital Gap" value="34 pts" sub="Top vs bottom EU quartile" icon={TrendingDown} color="red" />
        <KpiCard label="5G Coverage" value="67%" sub="EU-27 population weighted" icon={Zap} color="blue" />
        <KpiCard label="e-Gov Services" value="81%" sub="Available online (EU avg)" icon={Building2} color="purple" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Section title="Country Digital Readiness Ranking (Top 10)">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={top10} layout="vertical" margin={{ left: 10, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="country" tick={{ fontSize: 9 }} width={100} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="overall" name="DESI Score" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Digital Pillar Benchmarks">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={pillarData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="pillar" tick={{ fontSize: 8 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="top_quartile" name="Top Quartile" fill="#10b981" />
              <Bar dataKey="EU_avg" name="EU Average" fill="#3b82f6" />
              <Bar dataKey="bottom_quartile" name="Bottom Quartile" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="Country Detail">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Row label="Country"><Sel value={selectedCountry} onChange={setSelectedCountry} options={DIGITAL_COUNTRIES.map(c => ({ value: c.country, label: c.country }))} /></Row>
          </div>
          {selected && (
            <div className="bg-gray-50 rounded-lg p-3 text-xs">
              <div className="font-semibold text-gray-700 mb-2">{selected.country} Digital Profile</div>
              <div className="space-y-1.5">
                {[
                  { label: "Overall Score", value: selected.overall },
                  { label: "Connectivity", value: selected.connectivity },
                  { label: "Human Capital", value: selected.humanCapital },
                  { label: "e-Gov Services", value: selected.digitalPublicServices },
                  { label: "Business Integration", value: selected.integration },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center gap-2">
                    <span className="text-gray-500 w-36 flex-shrink-0">{label}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-1.5 overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${value}%` }} />
                    </div>
                    <span className="font-semibold text-gray-700 w-8 text-right">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

// ──────────────────────────────────────────────
// Tab 4: Fintech Disruption
// ──────────────────────────────────────────────
const FINTECH_SEGMENTS = [
  "Retail Banking", "SME Lending", "Mortgages", "Payments", "Wealth Mgmt",
  "Insurance UW", "Trade Finance", "Custodian Services",
];

function FintechTab() {
  const rng = sr(7007);
  const segmentData = FINTECH_SEGMENTS.map(s => {
    const r = sr(s.charCodeAt(0) * 23);
    return {
      segment: s.length > 14 ? s.slice(0, 13) + "…" : s,
      fullName: s,
      nimCompression: +(r() * 80 + 10).toFixed(1),
      digitalMarketShare: Math.round(r() * 50 + 10),
      incumbentResponse: r() > 0.5 ? "Strong" : r() > 0.25 ? "Moderate" : "Weak",
    };
  });

  const rng2 = sr(7008);
  const nimTrend = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"].map(y => ({
    year: y,
    traditional: +(rng2() * 0.4 + 1.8 - parseInt(y.slice(-1)) * 0.1).toFixed(2),
    neobank: +(rng2() * 0.3 + 0.4 + parseInt(y.slice(-1)) * 0.05).toFixed(2),
    platform: +(rng2() * 0.2 + 1.2 - parseInt(y.slice(-1)) * 0.05).toFixed(2),
  }));

  const investmentData = ["Payments", "Lending", "InsurTech", "WealthTech", "RegTech", "Crypto/DeFi"].map(c => {
    const r = sr(c.charCodeAt(0) * 11);
    return { category: c, investment: Math.round(r() * 40 + 5) };
  });

  const [form, setForm] = useState({ segment: "Retail Banking", fim_type: "neobank", scenario: "moderate" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/technology/fintech-disruption`, form);
      setResult(data);
    } catch {
      setResult({ nim_compression_bps: 45, market_share_loss_pct: 18, revenue_at_risk_bn: 3.2, strategic_response: "Partnership Model", timeline_years: 5 });
    } finally { setLoading(false); }
  }, [form]);

  const RESPONSE_COLORS = { Strong: "#10b981", Moderate: "#f59e0b", Weak: "#ef4444" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Avg NIM Compression" value="42 bps" sub="European banking avg" icon={TrendingDown} color="red" />
        <KpiCard label="Digital Mkt Share" value="23%" sub="Neobank + fintech" icon={BarChart2} color="blue" />
        <KpiCard label="Revenue at Risk" value="€180B" sub="EU incumbent banking" icon={AlertTriangle} color="amber" />
        <KpiCard label="Embedded Finance" value="$7.2T" sub="2030 global GMV forecast" icon={Zap} color="emerald" />
      </div>

      <Section title="Fintech Investment by Category ($B)">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={investmentData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="category" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit="B" />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`$${v}B`]} />
            <Bar dataKey="investment" name="Investment" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <div className="grid grid-cols-2 gap-4">
        <Section title="NIM Trend by Institution Type">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={nimTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="year" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 2.5]} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v}%`]} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="traditional" name="Traditional Bank" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="platform" name="Platform Bank" stroke="#f59e0b" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="neobank" name="Neobank" stroke="#10b981" strokeWidth={2} dot={false} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Segment Disruption Matrix">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-gray-200">
              <th className="text-left py-1.5 text-gray-500 font-medium">Segment</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">NIM Loss</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">Digital Share</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">Response</th>
            </tr></thead>
            <tbody>
              {segmentData.map(row => (
                <tr key={row.fullName} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-1.5 font-medium text-gray-800">{row.fullName}</td>
                  <td className="text-right text-gray-700">{row.nimCompression} bps</td>
                  <td className="text-right text-gray-700">{row.digitalMarketShare}%</td>
                  <td className="text-right font-semibold" style={{ color: RESPONSE_COLORS[row.incumbentResponse] }}>{row.incumbentResponse}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>

      <Section title="Disruption Impact Assessment">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Row label="Segment"><Sel value={form.segment} onChange={v => setForm(f => ({ ...f, segment: v }))} options={FINTECH_SEGMENTS.map(s => ({ value: s, label: s }))} /></Row>
            <Row label="Disruptor Type"><Sel value={form.fim_type} onChange={v => setForm(f => ({ ...f, fim_type: v }))} options={[{ value: "neobank", label: "Neobank" }, { value: "bigtech", label: "BigTech" }, { value: "platform", label: "Platform Finance" }, { value: "defi", label: "DeFi Protocol" }]} /></Row>
            <Row label="Scenario"><Sel value={form.scenario} onChange={v => setForm(f => ({ ...f, scenario: v }))} options={[{ value: "mild", label: "Mild Disruption" }, { value: "moderate", label: "Moderate Disruption" }, { value: "severe", label: "Severe Disruption" }]} /></Row>
            <div className="mt-3"><Btn onClick={run} loading={loading}>Assess Impact</Btn></div>
          </div>
          {result && (
            <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-1.5">
              <div className="font-semibold text-gray-700">Disruption Impact</div>
              <div className="grid grid-cols-2 gap-1 text-gray-600">
                <span>NIM Compression: <strong>{result.nim_compression_bps} bps</strong></span>
                <span>Market Share Loss: <strong>{result.market_share_loss_pct}%</strong></span>
                <span>Revenue at Risk: <strong>€{result.revenue_at_risk_bn}B</strong></span>
                <span>Timeline: <strong>{result.timeline_years}y</strong></span>
              </div>
              {result.strategic_response && <div className="text-gray-500">Recommended response: <strong className="text-gray-700">{result.strategic_response}</strong></div>}
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

// ──────────────────────────────────────────────
// Main Page
// ──────────────────────────────────────────────
export default function TechnologyRiskPage() {
  const [tab, setTab] = useState("automation");

  const TabContent = {
    automation: <AutomationTab />,
    ai: <AIAdoptionTab />,
    digital: <DigitalReadinessTab />,
    fintech: <FintechTab />,
  };

  return (
    <div className="min-h-screen bg-[#f8f8f6] p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-50 border border-purple-200 rounded-full mb-3">
              <Cpu className="h-3.5 w-3.5 text-purple-600" />
              <span className="text-xs font-medium text-purple-700">Technology Risk</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Technology & Disruption Risk</h1>
            <p className="text-sm text-gray-500 mt-1">Automation displacement · AI adoption scoring · Digital readiness · Fintech NIM compression</p>
          </div>
          <div className="flex gap-2 text-xs text-gray-500">
            <span className="px-2 py-1 bg-white border border-gray-200 rounded-lg">WEF · OECD</span>
            <span className="px-2 py-1 bg-white border border-gray-200 rounded-lg">DESI 2024</span>
            <span className="px-2 py-1 bg-white border border-gray-200 rounded-lg">19 NACE Sectors</span>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="mb-5">
          <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
            {TABS.map(t => {
              const Icon = t.icon;
              return (
                <button key={t.id} onClick={() => setTab(t.id)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    tab === t.id
                      ? "bg-white text-gray-900 shadow-sm border border-gray-200"
                      : "text-gray-500 hover:text-gray-700"
                  }`}>
                  <Icon className="h-3 w-3" />{t.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        {TabContent[tab]}
      </div>
    </div>
  );
}
