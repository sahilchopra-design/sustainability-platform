import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Briefcase, Users, ShieldOff, FileText, ChevronDown, ChevronUp,
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle, DollarSign,
  BarChart2, Activity, Target,
} from "lucide-react";

const API = process.env.REACT_APP_API_URL || "http://localhost:8001";
const TOOLTIP_STYLE = { backgroundColor: "#fff", border: "1px solid rgba(0,0,0,0.08)", borderRadius: 8, fontSize: 12, color: "#111" };

function sr(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

const TABS = [
  { id: "structure", label: "Fund Structure", icon: Briefcase },
  { id: "lp", label: "LP Analytics", icon: Users },
  { id: "exclusion", label: "Exclusion Screening", icon: ShieldOff },
  { id: "reporting", label: "ILPA Reporting", icon: FileText },
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
  const colors = {
    emerald: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    red: "bg-red-50 text-red-700",
    blue: "bg-blue-50 text-blue-700",
    purple: "bg-purple-50 text-purple-700",
    slate: "bg-gray-50 text-gray-700",
  };
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
// Tab 1: Fund Structure
// ──────────────────────────────────────────────
const FUND_TYPES = ["Buyout", "Growth Equity", "Venture Capital", "Infrastructure", "Real Estate", "Credit", "Hedge Fund", "Fund of Funds"];

function FundStructureTab() {
  const rng = sr(8001);
  const fundData = FUND_TYPES.map(f => {
    const r = sr(f.charCodeAt(0) * 19);
    return {
      type: f,
      aum: +(r() * 8 + 0.5).toFixed(1),
      irr: +(r() * 20 + 8).toFixed(1),
      moic: +(r() * 1.5 + 1.5).toFixed(2),
      dpi: +(r() * 0.8).toFixed(2),
      tvpi: +(r() * 1.2 + 1.3).toFixed(2),
      vintage: 2018 + Math.round(r() * 5),
      esgScore: Math.round(r() * 40 + 50),
    };
  });

  const allocationData = [
    { name: "Buyout", value: 35 },
    { name: "Growth", value: 20 },
    { name: "VC", value: 15 },
    { name: "Infra", value: 12 },
    { name: "Real Estate", value: 10 },
    { name: "Credit", value: 8 },
  ];
  const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899", "#64748b"];

  const rng2 = sr(8002);
  const vintagePerf = [2017, 2018, 2019, 2020, 2021, 2022].map(y => ({
    vintage: y,
    gross_irr: +(rng2() * 12 + 12).toFixed(1),
    net_irr: +(rng2() * 10 + 9).toFixed(1),
    tvpi: +(rng2() * 0.8 + 1.5).toFixed(2),
  }));

  const [form, setForm] = useState({ fund_type: "Buyout", vintage: "2022", target_size_mn: "500", strategy: "esg_tilt" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/fund-management/structure`, form);
      setResult(data);
    } catch {
      setResult({ net_irr_target: 15.2, tvpi_expected: 1.9, dpi_at_exit: 1.4, management_fee_pct: 2.0, carry_pct: 20, hurdle_rate: 8, esg_premium_bps: 35, recommended_structure: "LP/GP Delaware" });
    } finally { setLoading(false); }
  }, [form]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Total AUM Modelled" value="$42B" sub="Across 8 fund types" icon={DollarSign} color="emerald" />
        <KpiCard label="Avg Net IRR" value="16.3%" sub="Buyout vintage 2018-22" icon={TrendingUp} color="blue" />
        <KpiCard label="Avg MOIC" value="2.1x" sub="Realised + unrealised" icon={Target} color="purple" />
        <KpiCard label="Avg ESG Score" value="67/100" sub="ILPA ESG weighted" icon={CheckCircle} color="amber" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Section title="Fund AUM Allocation">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={allocationData} cx="50%" cy="50%" outerRadius={85} dataKey="value" label={({ name, value }) => `${name} ${value}%`} labelLine={false} fontSize={9}>
                {allocationData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v}%`]} />
            </PieChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Vintage Performance (Net IRR)">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={vintagePerf}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="vintage" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 30]} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v}%`]} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="gross_irr" name="Gross IRR" fill="#10b981" />
              <Bar dataKey="net_irr" name="Net IRR" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="Fund Portfolio Table">
        <table className="w-full text-xs">
          <thead><tr className="border-b border-gray-200">
            <th className="text-left py-1.5 text-gray-500 font-medium">Fund Type</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">AUM ($B)</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">IRR</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">MOIC</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">DPI</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">ESG</th>
          </tr></thead>
          <tbody>
            {fundData.map(row => (
              <tr key={row.type} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 font-medium text-gray-800">{row.type}</td>
                <td className="text-right text-gray-700">${row.aum}B</td>
                <td className="text-right text-gray-700">{row.irr}%</td>
                <td className="text-right text-gray-700">{row.moic}x</td>
                <td className="text-right text-gray-700">{row.dpi}x</td>
                <td className="text-right font-semibold" style={{ color: row.esgScore >= 70 ? "#10b981" : row.esgScore >= 55 ? "#f59e0b" : "#ef4444" }}>{row.esgScore}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Structure Optimiser" defaultOpen={false}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Row label="Fund Type"><Sel value={form.fund_type} onChange={v => setForm(f => ({ ...f, fund_type: v }))} options={FUND_TYPES.map(t => ({ value: t, label: t }))} /></Row>
            <Row label="Vintage Year"><Sel value={form.vintage} onChange={v => setForm(f => ({ ...f, vintage: v }))} options={[2020, 2021, 2022, 2023, 2024, 2025].map(y => ({ value: String(y), label: String(y) }))} /></Row>
            <Row label="Target Size ($M)"><Inp value={form.target_size_mn} onChange={v => setForm(f => ({ ...f, target_size_mn: v }))} type="number" /></Row>
            <Row label="ESG Strategy"><Sel value={form.strategy} onChange={v => setForm(f => ({ ...f, strategy: v }))} options={[{ value: "esg_tilt", label: "ESG Tilt" }, { value: "impact", label: "Impact-First" }, { value: "exclusion", label: "Exclusion Only" }, { value: "best_in_class", label: "Best-in-Class" }]} /></Row>
            <div className="mt-3"><Btn onClick={run} loading={loading}>Optimise Structure</Btn></div>
          </div>
          {result && (
            <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-2">
              <div className="font-semibold text-gray-700">Structure Output</div>
              <div className="grid grid-cols-2 gap-1 text-gray-600">
                <span>Net IRR Target: <strong>{result.net_irr_target}%</strong></span>
                <span>TVPI Expected: <strong>{result.tvpi_expected}x</strong></span>
                <span>Mgmt Fee: <strong>{result.management_fee_pct}%</strong></span>
                <span>Carry: <strong>{result.carry_pct}%</strong></span>
                <span>Hurdle Rate: <strong>{result.hurdle_rate}%</strong></span>
                <span>ESG Premium: <strong>{result.esg_premium_bps} bps</strong></span>
              </div>
              <div className="text-gray-500">Structure: <strong className="text-gray-700">{result.recommended_structure}</strong></div>
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

// ──────────────────────────────────────────────
// Tab 2: LP Analytics
// ──────────────────────────────────────────────
function LPAnalyticsTab() {
  const rng = sr(8003);
  const lpTypes = ["Pension Fund", "Sovereign Wealth", "Endowment", "Family Office", "Insurance Co", "Bank", "HNWI", "Fund of Funds"];
  const lpData = lpTypes.map(t => {
    const r = sr(t.charCodeAt(0) * 13);
    return {
      type: t,
      commitment_bn: +(r() * 5 + 0.3).toFixed(2),
      redemption_risk: +(r() * 40 + 5).toFixed(1),
      esg_requirement: r() > 0.65 ? "Mandatory" : r() > 0.35 ? "Preferred" : "Optional",
      concentration: +(r() * 20 + 5).toFixed(1),
    };
  });

  const hhi = sr(8004);
  const hhiData = ["Pension", "SWF", "Endowment", "FoF", "Insurance"].map(t => ({
    type: t,
    hhi: Math.round(hhi() * 1500 + 500),
    benchmark: 1000,
  }));

  const redemptionData = ["Q1 25", "Q2 25", "Q3 25", "Q4 25", "Q1 26", "Q2 26"].map(q => {
    const r = sr(q.charCodeAt(0) * 7);
    return { quarter: q, baseCase: +(r() * 3 + 1).toFixed(1), stressed: +(r() * 6 + 2).toFixed(1) };
  });

  const [form, setForm] = useState({ lp_type: "Pension Fund", commitment_mn: "200", horizon: "10" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/am/lp-analytics`, form);
      setResult(data);
    } catch {
      setResult({ hhi_score: 1250, concentration_risk: "Moderate", liquidity_coverage_ratio: 0.82, redemption_stress_pct: 15, co_investment_capacity_mn: 45, esg_alignment_score: 78 });
    } finally { setLoading(false); }
  }, [form]);

  const ESG_COLORS = { Mandatory: "#10b981", Preferred: "#3b82f6", Optional: "#94a3b8" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Total LP Commitments" value="$28B" sub="Across 8 LP types" icon={Users} color="blue" />
        <KpiCard label="HHI Concentration" value="1,240" sub="Moderate (< 1,500 target)" icon={BarChart2} color="amber" />
        <KpiCard label="ESG Mandatory LPs" value="63%" sub="By committed capital" icon={CheckCircle} color="emerald" />
        <KpiCard label="Redemption Risk" value="12%" sub="Stressed 12m scenario" icon={AlertTriangle} color="red" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Section title="LP Concentration (HHI by Type)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={hhiData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="type" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="hhi" name="HHI Score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Line dataKey="benchmark" name="Target Max" stroke="#ef4444" strokeDasharray="4 2" />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Redemption Stress Scenario ($B)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={redemptionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="quarter" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} unit="B" />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`$${v}B`]} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="baseCase" name="Base Case" fill="#10b981" />
              <Bar dataKey="stressed" name="Stressed" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="LP Registry">
        <table className="w-full text-xs">
          <thead><tr className="border-b border-gray-200">
            <th className="text-left py-1.5 text-gray-500 font-medium">LP Type</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">Commitment ($B)</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">Redemption Risk</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">Concentration</th>
            <th className="text-right py-1.5 text-gray-500 font-medium">ESG Req</th>
          </tr></thead>
          <tbody>
            {lpData.map(row => (
              <tr key={row.type} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 font-medium text-gray-800">{row.type}</td>
                <td className="text-right text-gray-700">${row.commitment_bn}B</td>
                <td className="text-right text-gray-700">{row.redemption_risk}%</td>
                <td className="text-right text-gray-700">{row.concentration}%</td>
                <td className="text-right font-semibold" style={{ color: ESG_COLORS[row.esg_requirement] }}>{row.esg_requirement}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="LP Liquidity Assessment" defaultOpen={false}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Row label="LP Type"><Sel value={form.lp_type} onChange={v => setForm(f => ({ ...f, lp_type: v }))} options={lpTypes.map(t => ({ value: t, label: t }))} /></Row>
            <Row label="Commitment ($M)"><Inp value={form.commitment_mn} onChange={v => setForm(f => ({ ...f, commitment_mn: v }))} type="number" /></Row>
            <Row label="Horizon (years)"><Inp value={form.horizon} onChange={v => setForm(f => ({ ...f, horizon: v }))} type="number" /></Row>
            <div className="mt-3"><Btn onClick={run} loading={loading}>Run LP Analysis</Btn></div>
          </div>
          {result && (
            <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-2">
              <div className="font-semibold text-gray-700">LP Analytics Output</div>
              <div className="grid grid-cols-2 gap-1 text-gray-600">
                <span>HHI Score: <strong>{result.hhi_score}</strong></span>
                <span>Concentration: <strong>{result.concentration_risk}</strong></span>
                <span>LCR: <strong>{result.liquidity_coverage_ratio}</strong></span>
                <span>Redemption Stress: <strong>{result.redemption_stress_pct}%</strong></span>
                <span>Co-Inv Capacity: <strong>${result.co_investment_capacity_mn}M</strong></span>
                <span>ESG Alignment: <strong>{result.esg_alignment_score}/100</strong></span>
              </div>
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

// ──────────────────────────────────────────────
// Tab 3: Exclusion Screening
// ──────────────────────────────────────────────
const SFDR_EXCLUSIONS = [
  { code: "E1", name: "Coal (>30% revenue)", category: "Environmental" },
  { code: "E2", name: "Oil Sands Extraction", category: "Environmental" },
  { code: "E3", name: "Arctic Drilling", category: "Environmental" },
  { code: "E4", name: "Deforestation-linked", category: "Environmental" },
  { code: "S1", name: "Controversial Weapons", category: "Social" },
  { code: "S2", name: "Tobacco (>5% revenue)", category: "Social" },
  { code: "S3", name: "Gambling Operations", category: "Social" },
  { code: "S4", name: "Adult Content", category: "Social" },
  { code: "G1", name: "Severe Governance Failures", category: "Governance" },
  { code: "G2", name: "UN GC Violations", category: "Governance" },
  { code: "G3", name: "Systemic Corruption", category: "Governance" },
];

function ExclusionScreeningTab() {
  const rng = sr(8005);
  const portfolioCompanies = [
    "Alpha Energy Corp", "Beta Mining Ltd", "Gamma Industrials", "Delta Resources",
    "Epsilon Power", "Zeta Materials", "Eta Chemicals", "Theta Logistics",
    "Iota Consumer", "Kappa Finance",
  ].map(name => {
    const r = sr(name.charCodeAt(0) * 37);
    const flags = SFDR_EXCLUSIONS.filter(() => r() > 0.75).slice(0, 3);
    return {
      company: name,
      sector: ["Energy", "Materials", "Industrials", "Utilities", "Consumer"][Math.floor(r() * 5)],
      flags: flags.map(f => f.code),
      status: flags.length > 2 ? "Excluded" : flags.length > 0 ? "Watch" : "Clear",
      esgScore: Math.round(r() * 60 + 30),
      revenue_mn: Math.round(r() * 5000 + 200),
    };
  });

  const exclusionSummary = SFDR_EXCLUSIONS.map(e => ({
    code: e.code,
    name: e.name.length > 20 ? e.name.slice(0, 19) + "…" : e.name,
    fullName: e.name,
    category: e.category,
    flagged: Math.round(rng() * 3),
  }));

  const STATUS_COLORS = { Clear: "#10b981", Watch: "#f59e0b", Excluded: "#ef4444" };

  const [form, setForm] = useState({ company_name: "", revenue_threshold: "5", check_un_gc: true });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/sfdr-exclusion/screen`, form);
      setResult(data);
    } catch {
      setResult({ status: "Watch", flags: ["E1", "G2"], recommendation: "Enhanced Due Diligence Required", sfdr_article: "8", pai_impact: "Principal Adverse Impact detected" });
    } finally { setLoading(false); }
  }, [form]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Portfolio Companies" value={portfolioCompanies.length} sub="Under active monitoring" icon={Briefcase} color="blue" />
        <KpiCard label="Fully Clear" value={portfolioCompanies.filter(c => c.status === "Clear").length} sub="No exclusion flags" icon={CheckCircle} color="emerald" />
        <KpiCard label="On Watch List" value={portfolioCompanies.filter(c => c.status === "Watch").length} sub="1–2 flags, enhanced DD" icon={AlertTriangle} color="amber" />
        <KpiCard label="Excluded" value={portfolioCompanies.filter(c => c.status === "Excluded").length} sub="Hard exclusion criteria met" icon={ShieldOff} color="red" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Section title="Exclusion Flag Frequency">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={exclusionSummary} layout="vertical" margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 10 }} domain={[0, 4]} />
              <YAxis type="category" dataKey="code" tick={{ fontSize: 10 }} width={30} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, _, props) => [v, props.payload.fullName || "Flags"]} />
              <Bar dataKey="flagged" name="Companies Flagged" radius={[0, 4, 4, 0]}>
                {exclusionSummary.map((e, i) => (
                  <Cell key={i} fill={e.category === "Environmental" ? "#10b981" : e.category === "Social" ? "#3b82f6" : "#f59e0b"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-3 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" />Environmental</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-blue-500 inline-block" />Social</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-amber-500 inline-block" />Governance</span>
          </div>
        </Section>

        <Section title="Portfolio Screening Results">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-gray-200">
              <th className="text-left py-1.5 text-gray-500 font-medium">Company</th>
              <th className="text-left py-1.5 text-gray-500 font-medium">Sector</th>
              <th className="text-center py-1.5 text-gray-500 font-medium">Flags</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">ESG</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">Status</th>
            </tr></thead>
            <tbody>
              {portfolioCompanies.map(row => (
                <tr key={row.company} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-1.5 font-medium text-gray-800 text-xs">{row.company.split(" ").slice(0, 2).join(" ")}</td>
                  <td className="text-gray-600 text-xs">{row.sector}</td>
                  <td className="text-center">
                    {row.flags.length > 0
                      ? <span className="text-xs font-mono text-gray-600">{row.flags.join(", ")}</span>
                      : <span className="text-gray-400">—</span>}
                  </td>
                  <td className="text-right text-gray-700">{row.esgScore}</td>
                  <td className="text-right font-semibold text-xs" style={{ color: STATUS_COLORS[row.status] }}>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>

      <Section title="Ad-hoc Exclusion Check" defaultOpen={false}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Row label="Company Name" required><Inp value={form.company_name} onChange={v => setForm(f => ({ ...f, company_name: v }))} placeholder="e.g. Acme Energy Corp" /></Row>
            <Row label="Revenue Threshold (%)"><Inp value={form.revenue_threshold} onChange={v => setForm(f => ({ ...f, revenue_threshold: v }))} type="number" /></Row>
            <Row label="Apply UN GC Screen">
              <select value={form.check_un_gc ? "yes" : "no"} onChange={e => setForm(f => ({ ...f, check_un_gc: e.target.value === "yes" }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500 bg-white">
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </Row>
            <div className="mt-3"><Btn onClick={run} loading={loading}>Run SFDR Screen</Btn></div>
          </div>
          {result && (
            <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-1.5">
              <div className="font-semibold text-gray-700">Screening Result</div>
              <div className="grid grid-cols-2 gap-1 text-gray-600">
                <span>Status: <strong style={{ color: STATUS_COLORS[result.status] }}>{result.status}</strong></span>
                <span>SFDR Article: <strong>Art. {result.sfdr_article}</strong></span>
                <span>Flags: <strong>{result.flags?.join(", ") || "None"}</strong></span>
              </div>
              <div className="text-gray-500">{result.recommendation}</div>
              {result.pai_impact && <div className="text-amber-600 font-medium">{result.pai_impact}</div>}
            </div>
          )}
        </div>
      </Section>
    </div>
  );
}

// ──────────────────────────────────────────────
// Tab 4: ILPA Reporting
// ──────────────────────────────────────────────
function ILPAReportingTab() {
  const rng = sr(8007);
  const quarters = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"];
  const feeData = quarters.map(q => {
    const r = sr(q.charCodeAt(0) * 29);
    return {
      quarter: q,
      managementFee: +(r() * 2 + 3).toFixed(2),
      carry: +(r() * 5 + 0).toFixed(2),
      expenses: +(r() * 1 + 0.5).toFixed(2),
      netDistributable: +(r() * 8 + 2).toFixed(2),
    };
  });

  const esgKpis = [
    { metric: "Weighted Avg Carbon Intensity", value: "142 tCO₂e/$M", trend: "down", change: "-8%" },
    { metric: "Board Gender Diversity", value: "38%", trend: "up", change: "+3pp" },
    { metric: "Employee Health & Safety", value: "2.1 TRIR", trend: "down", change: "-12%" },
    { metric: "Renewable Energy Use", value: "61%", trend: "up", change: "+9pp" },
    { metric: "Supply Chain ESG Coverage", value: "72%", trend: "up", change: "+15pp" },
    { metric: "Living Wage Compliance", value: "89%", trend: "up", change: "+4pp" },
  ];

  const complianceData = [
    { area: "ILPA DDQ 2023", status: "Complete", score: 92 },
    { area: "SFDR Art 9 PAI", status: "Complete", score: 88 },
    { area: "TCFD Disclosures", status: "Partial", score: 71 },
    { area: "UNPRI Reporting", status: "Complete", score: 95 },
    { area: "GHG Protocol Inv", status: "Partial", score: 64 },
    { area: "ILPA ESG Module", status: "Complete", score: 83 },
  ];

  const [form, setForm] = useState({ fund_id: "FUND-001", reporting_period: "Q4 2024", framework: "ILPA" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/pe-reporting/ilpa`, form);
      setResult(data);
    } catch {
      setResult({ report_id: "RPT-2024Q4-001", completeness_pct: 87, outstanding_items: 4, esg_score: 78, carbon_footprint_t: 12450, next_submission: "2025-04-30" });
    } finally { setLoading(false); }
  }, [form]);

  const STATUS_COLORS = { Complete: "#10b981", Partial: "#f59e0b", Outstanding: "#ef4444" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="ILPA Completeness" value="87%" sub="Current period" icon={FileText} color="emerald" />
        <KpiCard label="SFDR Article" value="Art. 9" sub="Dark green fund" icon={CheckCircle} color="blue" />
        <KpiCard label="PAI Indicators" value="14 / 18" sub="Mandatory tracked" icon={Activity} color="purple" />
        <KpiCard label="Pending Items" value="4" sub="Overdue disclosures" icon={AlertTriangle} color="amber" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Section title="Fee & Carry Waterfall ($M)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={feeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="quarter" tick={{ fontSize: 9 }} />
              <YAxis tick={{ fontSize: 10 }} unit="M" />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`$${v}M`]} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="managementFee" name="Mgmt Fee" stackId="a" fill="#3b82f6" />
              <Bar dataKey="carry" name="Carry" stackId="a" fill="#10b981" />
              <Bar dataKey="expenses" name="Expenses" stackId="a" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Framework Compliance Scorecard">
          <div className="space-y-2 mt-1">
            {complianceData.map(row => (
              <div key={row.area} className="flex items-center gap-3 text-xs">
                <span className="text-gray-700 font-medium w-36 flex-shrink-0">{row.area}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div className="h-full rounded-full transition-all"
                    style={{ width: `${row.score}%`, backgroundColor: row.score >= 85 ? "#10b981" : row.score >= 70 ? "#f59e0b" : "#ef4444" }} />
                </div>
                <span className="w-6 text-right text-gray-600 font-semibold">{row.score}</span>
                <span className="w-16 text-right font-semibold" style={{ color: STATUS_COLORS[row.status] }}>{row.status}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>

      <Section title="ESG KPI Dashboard">
        <div className="grid grid-cols-3 gap-3">
          {esgKpis.map(kpi => (
            <div key={kpi.metric} className="bg-gray-50 rounded-lg p-3 text-xs">
              <div className="text-gray-500 mb-1">{kpi.metric}</div>
              <div className="flex items-baseline gap-1.5">
                <span className="font-bold text-gray-900 text-sm">{kpi.value}</span>
                <span className={`font-semibold ${kpi.trend === "up" ? "text-emerald-600" : "text-red-500"}`}>
                  {kpi.change}
                  {kpi.trend === "up" ? <TrendingUp className="h-3 w-3 inline ml-0.5" /> : <TrendingDown className="h-3 w-3 inline ml-0.5" />}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Generate ILPA Report" defaultOpen={false}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Row label="Fund ID"><Inp value={form.fund_id} onChange={v => setForm(f => ({ ...f, fund_id: v }))} /></Row>
            <Row label="Reporting Period"><Sel value={form.reporting_period} onChange={v => setForm(f => ({ ...f, reporting_period: v }))} options={["Q4 2024", "Q3 2024", "Q2 2024", "Q1 2024"].map(q => ({ value: q, label: q }))} /></Row>
            <Row label="Framework"><Sel value={form.framework} onChange={v => setForm(f => ({ ...f, framework: v }))} options={[{ value: "ILPA", label: "ILPA 2023" }, { value: "SFDR", label: "SFDR PAI" }, { value: "UNPRI", label: "PRI Transparency" }, { value: "TCFD", label: "TCFD" }]} /></Row>
            <div className="mt-3"><Btn onClick={run} loading={loading}>Generate Report</Btn></div>
          </div>
          {result && (
            <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-1.5">
              <div className="font-semibold text-gray-700">Report Generated</div>
              <div className="grid grid-cols-2 gap-1 text-gray-600">
                <span>Report ID: <strong>{result.report_id}</strong></span>
                <span>Completeness: <strong>{result.completeness_pct}%</strong></span>
                <span>ESG Score: <strong>{result.esg_score}/100</strong></span>
                <span>GHG Footprint: <strong>{result.carbon_footprint_t?.toLocaleString()} t</strong></span>
                <span>Outstanding: <strong>{result.outstanding_items} items</strong></span>
                <span>Deadline: <strong>{result.next_submission}</strong></span>
              </div>
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
export default function FundManagementPage() {
  const [tab, setTab] = useState("structure");

  const TabContent = {
    structure: <FundStructureTab />,
    lp: <LPAnalyticsTab />,
    exclusion: <ExclusionScreeningTab />,
    reporting: <ILPAReportingTab />,
  };

  return (
    <div className="min-h-screen bg-[#f8f8f6] p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded-full mb-3">
              <Briefcase className="h-3.5 w-3.5 text-blue-600" />
              <span className="text-xs font-medium text-blue-700">Fund Management</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Fund & Asset Management</h1>
            <p className="text-sm text-gray-500 mt-1">LP analytics · ESG exclusion screening · ILPA reporting · Fund structure optimisation</p>
          </div>
          <div className="flex gap-2 text-xs text-gray-500">
            <span className="px-2 py-1 bg-white border border-gray-200 rounded-lg">ILPA 2023</span>
            <span className="px-2 py-1 bg-white border border-gray-200 rounded-lg">SFDR Art 8/9</span>
            <span className="px-2 py-1 bg-white border border-gray-200 rounded-lg">PRI · UNPRI</span>
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
