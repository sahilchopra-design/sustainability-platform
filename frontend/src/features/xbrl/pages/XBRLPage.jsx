/**
 * XBRL & Disclosure Completeness
 *
 * Tab 1 — XBRL Export      /api/v1/xbrl-export  (iXBRL + XBRL XML, ESRS ESEF)
 * Tab 2 — XBRL Ingestion   /api/v1/xbrl-ingestion  (parse incoming filings)
 * Tab 3 — Completeness     /api/v1/disclosure-completeness (per-standard % + traffic light)
 * Tab 4 — Trend Analytics  /api/v1/disclosure-trends  (YoY CAGR, peer percentile)
 */
import React, { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie, LineChart, Line, Legend,
} from "recharts";
import {
  FileCode2, Download, Upload, TrendingUp, ChevronDown, ChevronUp,
  CheckCircle, AlertTriangle, XCircle, Play, RefreshCw, Info,
  FileText, Database, BarChart3, Layers,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";

/* ── Deterministic seed helper ──────────────────────────────────────────── */
function sr(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

/* ── Shared primitives ──────────────────────────────────────────────────── */
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
      <label className="text-[11px] text-gray-500 w-44 shrink-0">{label}</label>
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

function Btn({ onClick, disabled, loading, children, variant = "primary" }) {
  const base = "inline-flex items-center gap-1.5 px-4 py-2 rounded text-xs font-medium transition-all";
  const styles = variant === "primary"
    ? "bg-[#164E8A] text-white hover:bg-[#12407A] disabled:opacity-40"
    : "bg-gray-100 text-gray-700 hover:bg-gray-800/[0.10] disabled:opacity-40";
  return (
    <button onClick={onClick} disabled={disabled || loading} className={`${base} ${styles}`}>
      {loading && <RefreshCw className="h-3 w-3 animate-spin" />}
      {children}
    </button>
  );
}

function RAG({ value }) {
  if (value >= 0.8) return <span className="text-xs font-semibold text-emerald-600">Green</span>;
  if (value >= 0.5) return <span className="text-xs font-semibold text-amber-500">Amber</span>;
  return <span className="text-xs font-semibold text-red-500">Red</span>;
}

const TOOLTIP_STYLE = { backgroundColor: "#fff", border: "1px solid rgba(0,0,0,0.08)", color: "#111" };

/* ══════════════════════════════════════════════════════════════════════════
   TAB 1 — XBRL EXPORT
══════════════════════════════════════════════════════════════════════════ */
function ExportPanel() {
  const [entityId, setEntityId] = useState("ent-001");
  const [standard, setStandard] = useState("esrs");
  const [format, setFormat] = useState("ixbrl");
  const [fiscalYear, setFiscalYear] = useState("2024");
  const [currency, setCurrency] = useState("EUR");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Deterministic static metrics
  const rng = sr(42);
  const COMPLETENESS_BARS = [
    { name: "ESRS E1", pct: 88, mandatory: 34, reported: 30 },
    { name: "ESRS E2", pct: 72, mandatory: 18, reported: 13 },
    { name: "ESRS E3", pct: 65, mandatory: 22, reported: 14 },
    { name: "ESRS E4", pct: 54, mandatory: 28, reported: 15 },
    { name: "ESRS E5", pct: 61, mandatory: 20, reported: 12 },
    { name: "ESRS S1", pct: 79, mandatory: 40, reported: 32 },
    { name: "ESRS G1", pct: 91, mandatory: 12, reported: 11 },
  ];

  async function runExport() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/xbrl-export/generate`, {
        entity_id: entityId, standard, format, fiscal_year: parseInt(fiscalYear), currency,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Export failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Standards Supported" value="8" sub="ESRS · ISSB · GRI · SFDR" />
        <KpiCard label="Total DPs Mapped" value="330+" sub="ESRS IG3 Quantitative" />
        <KpiCard label="Output Formats" value="3" sub="iXBRL · XBRL XML · JSON" />
        <KpiCard label="Avg Tagging Rate" value="94%" sub="Auto-tagged DPs" color="text-emerald-600" />
      </div>

      <Section title="ESRS Disclosure Completeness (Pre-Export)" icon={BarChart3}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={COMPLETENESS_BARS} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={62} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, "Completeness"]} />
            <Bar dataKey="pct" radius={[0, 3, 3, 0]}>
              {COMPLETENESS_BARS.map((d, i) => (
                <Cell key={i} fill={d.pct >= 80 ? "#10b981" : d.pct >= 60 ? "#f59e0b" : "#ef4444"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Generate XBRL Filing" icon={FileCode2}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
          <div>
            <Row label="Entity ID"><Inp value={entityId} onChange={setEntityId} placeholder="ent-001" /></Row>
            <Row label="Reporting Standard">
              <Sel value={standard} onChange={setStandard} options={[
                { v: "esrs", l: "CSRD / ESRS (ESEF)" }, { v: "issb", l: "IFRS S1/S2 (XBRL)" },
                { v: "gri", l: "GRI (Digital Reports)" }, { v: "sfdr", l: "SFDR (ECB taxonomy)" },
              ]} />
            </Row>
            <Row label="Output Format">
              <Sel value={format} onChange={setFormat} options={[
                { v: "ixbrl", l: "iXBRL (Inline XBRL)" }, { v: "xbrl_xml", l: "XBRL XML" }, { v: "json_ld", l: "JSON-LD" },
              ]} />
            </Row>
          </div>
          <div>
            <Row label="Fiscal Year"><Inp value={fiscalYear} onChange={setFiscalYear} type="number" /></Row>
            <Row label="Reporting Currency">
              <Sel value={currency} onChange={setCurrency} options={[
                { v: "EUR", l: "EUR" }, { v: "USD", l: "USD" }, { v: "GBP", l: "GBP" }, { v: "JPY", l: "JPY" },
              ]} />
            </Row>
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <Btn onClick={runExport} loading={loading}>
            <Download className="h-3 w-3" /> Generate Filing
          </Btn>
        </div>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 space-y-2">
            <p className="text-xs font-semibold text-gray-700">Export Result</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div><span className="text-gray-500">Format:</span> <span className="font-medium">{result.format || format.toUpperCase()}</span></div>
              <div><span className="text-gray-500">DPs Tagged:</span> <span className="font-medium">{result.tagged_count || "—"}</span></div>
              <div><span className="text-gray-500">File Size:</span> <span className="font-medium">{result.file_size_kb ? `${result.file_size_kb} KB` : "—"}</span></div>
              <div><span className="text-gray-500">Status:</span> <span className="font-medium text-emerald-600">{result.status || "Generated"}</span></div>
            </div>
            {result.download_url && (
              <a href={result.download_url} className="inline-flex items-center gap-1.5 text-xs text-blue-600 underline mt-2" target="_blank" rel="noreferrer">
                <Download className="h-3 w-3" /> Download Filing
              </a>
            )}
          </div>
        )}
      </Section>

      <Section title="Supported Taxonomies" icon={Layers} defaultOpen={false}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Taxonomy</th>
              <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Version</th>
              <th className="text-left py-1.5 px-2 text-gray-500 font-medium">DPs</th>
              <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["ESRS ESEF", "2024", "330+", "Production"],
              ["IFRS S1/S2", "2023", "180+", "Production"],
              ["GRI Universal", "2021", "120+", "Beta"],
              ["SFDR RTS", "2023 Rev", "64", "Production"],
              ["EU Taxonomy", "2023 DA", "42", "Production"],
              ["SEC Reg S-K", "1501-1505", "30", "Beta"],
              ["BRSR", "2023", "60+", "Beta"],
              ["TCFD", "2023", "11 Rec.", "Production"],
            ].map(([tax, ver, dps, st]) => (
              <tr key={tax} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 font-medium text-gray-700">{tax}</td>
                <td className="py-1.5 px-2 text-gray-500">{ver}</td>
                <td className="py-1.5 px-2 font-mono text-gray-600">{dps}</td>
                <td className="py-1.5 px-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    st === "Production" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                  }`}>{st}</span>
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
   TAB 2 — XBRL INGESTION
══════════════════════════════════════════════════════════════════════════ */
function IngestionPanel() {
  const [filingUrl, setFilingUrl] = useState("");
  const [entityId, setEntityId] = useState("ent-001");
  const [taxonomy, setTaxonomy] = useState("esrs");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const RECENT = [
    { entity: "Rabobank", taxonomy: "ESRS", dps: 142, date: "2025-03-01", status: "Parsed" },
    { entity: "BNP Paribas", taxonomy: "ESRS", dps: 187, date: "2025-03-03", status: "Parsed" },
    { entity: "ING Group", taxonomy: "ESRS", dps: 134, date: "2025-03-05", status: "Parsed" },
    { entity: "Ørsted", taxonomy: "ESRS", dps: 98, date: "2025-03-08", status: "Partial" },
    { entity: "RWE", taxonomy: "ESRS", dps: 109, date: "2025-03-09", status: "Parsed" },
  ];

  async function runIngest() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/xbrl-ingestion/parse`, {
        filing_url: filingUrl || "https://example.com/filing.xbrl",
        entity_id: entityId, taxonomy,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Ingestion failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Filings Parsed" value="847" sub="All-time ingested" />
        <KpiCard label="Entities Tracked" value="112" sub="Active issuers" />
        <KpiCard label="Avg Parse Time" value="2.4s" sub="Per filing" />
        <KpiCard label="Parse Success Rate" value="98.2%" sub="Last 30 days" color="text-emerald-600" />
      </div>

      <Section title="Recent Ingestions" icon={Database}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {["Entity", "Taxonomy", "DPs Extracted", "Date", "Status"].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {RECENT.map((r) => (
              <tr key={r.entity} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 font-medium text-gray-700">{r.entity}</td>
                <td className="py-1.5 px-2 text-gray-500">{r.taxonomy}</td>
                <td className="py-1.5 px-2 font-mono text-gray-600">{r.dps}</td>
                <td className="py-1.5 px-2 text-gray-500">{r.date}</td>
                <td className="py-1.5 px-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    r.status === "Parsed" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                  }`}>{r.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Parse New Filing" icon={Upload}>
        <Row label="Filing URL (XBRL/iXBRL)"><Inp value={filingUrl} onChange={setFilingUrl} placeholder="https://..." /></Row>
        <Row label="Entity ID"><Inp value={entityId} onChange={setEntityId} /></Row>
        <Row label="Taxonomy">
          <Sel value={taxonomy} onChange={setTaxonomy} options={[
            { v: "esrs", l: "ESRS ESEF" }, { v: "issb", l: "IFRS S1/S2" },
            { v: "gri", l: "GRI Digital" }, { v: "sfdr", l: "SFDR RTS" },
          ]} />
        </Row>
        <div className="flex gap-2 mt-3">
          <Btn onClick={runIngest} loading={loading}>
            <Play className="h-3 w-3" /> Parse Filing
          </Btn>
        </div>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-700 mb-2">Parse Result</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              {[
                ["DPs Extracted", result.extracted_count],
                ["Validation Errors", result.validation_errors || 0],
                ["Coverage", result.coverage_pct ? `${(result.coverage_pct * 100).toFixed(0)}%` : "—"],
                ["Status", result.status || "Parsed"],
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
   TAB 3 — DISCLOSURE COMPLETENESS
══════════════════════════════════════════════════════════════════════════ */
function CompletenessPanel() {
  const [entityId, setEntityId] = useState("ent-001");
  const [standard, setStandard] = useState("csrd_esrs");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const rng = sr(99);
  const STANDARDS_DATA = [
    { std: "CSRD ESRS", mandatory: 180, reported: 154, pct: 86, rag: "green" },
    { std: "SFDR PAI", mandatory: 18, reported: 15, pct: 83, rag: "green" },
    { std: "EU Taxonomy", mandatory: 12, reported: 9, pct: 75, rag: "amber" },
    { std: "TCFD", mandatory: 11, reported: 10, pct: 91, rag: "green" },
    { std: "ISSB S1/S2", mandatory: 65, reported: 42, pct: 65, rag: "amber" },
    { std: "GRI Universal", mandatory: 34, reported: 21, pct: 62, rag: "amber" },
    { std: "SASB", mandatory: 28, reported: 14, pct: 50, rag: "red" },
    { std: "SEC Reg S-K", mandatory: 20, reported: 9, pct: 45, rag: "red" },
  ];

  const PIE = [
    { name: "Reported", value: 274 }, { name: "Gap", value: 94 },
  ];

  async function run() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.get(`${API_BASE}/api/v1/disclosure-completeness/${entityId}`, {
        params: { standard },
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed");
    } finally { setLoading(false); }
  }

  const RAG_COLOR = { green: "#10b981", amber: "#f59e0b", red: "#ef4444" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Overall Completeness" value="72%" sub="Across all standards" color="text-amber-600" />
        <KpiCard label="Green RAG" value="3 / 8" sub="Standards fully compliant" />
        <KpiCard label="Mandatory DPs" value="368" sub="Across 8 frameworks" />
        <KpiCard label="Reported DPs" value="274" sub="Documented this period" color="text-emerald-600" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Completeness by Standard" icon={BarChart3}>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={STANDARDS_DATA} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
              <YAxis dataKey="std" type="category" tick={{ fontSize: 10 }} width={80} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, "Completeness"]} />
              <Bar dataKey="pct" radius={[0, 3, 3, 0]}>
                {STANDARDS_DATA.map((d, i) => (
                  <Cell key={i} fill={RAG_COLOR[d.rag]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Reported vs Gap" icon={FileText}>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={PIE} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                dataKey="value" label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                <Cell fill="#10b981" />
                <Cell fill="#ef4444" />
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="Run Completeness Check" icon={Play}>
        <Row label="Entity ID"><Inp value={entityId} onChange={setEntityId} /></Row>
        <Row label="Standard">
          <Sel value={standard} onChange={setStandard} options={[
            { v: "csrd_esrs", l: "CSRD ESRS" }, { v: "sfdr", l: "SFDR PAI" },
            { v: "tcfd", l: "TCFD" }, { v: "issb", l: "ISSB S1/S2" },
            { v: "gri", l: "GRI Universal" }, { v: "sasb", l: "SASB Industry" },
          ]} />
        </Row>
        <Btn onClick={run} loading={loading}><Play className="h-3 w-3" /> Check Completeness</Btn>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-gray-700">Completeness Results</p>
            <div className="grid grid-cols-3 gap-3">
              <div><span className="text-gray-500">Completeness:</span> <span className="font-medium">{result.completeness_pct ? `${(result.completeness_pct * 100).toFixed(0)}%` : "—"}</span></div>
              <div><span className="text-gray-500">Traffic Light:</span> <RAG value={result.completeness_pct || 0} /></div>
              <div><span className="text-gray-500">Gaps:</span> <span className="font-medium">{result.gap_count ?? "—"}</span></div>
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 4 — TREND ANALYTICS
══════════════════════════════════════════════════════════════════════════ */
function TrendPanel() {
  const YEARS = [2020, 2021, 2022, 2023, 2024];
  const TREND_DATA = YEARS.map((y, i) => ({
    year: String(y),
    scope1: [120, 108, 96, 82, 70][i],
    scope2: [45, 38, 30, 22, 14][i],
    scope3: [380, 360, 340, 310, 280][i],
    completeness: [48, 55, 63, 72, 80][i],
  }));

  const PEER_DATA = [
    { name: "Entity", scope1: 70, scope3: 280, completeness: 80 },
    { name: "P25", scope1: 90, scope3: 320, completeness: 65 },
    { name: "P50", scope1: 110, scope3: 370, completeness: 72 },
    { name: "P75", scope1: 145, scope3: 430, completeness: 78 },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Scope 1 CAGR" value="-12.4%" sub="5-year decarbonisation" color="text-emerald-600" />
        <KpiCard label="Scope 3 CAGR" value="-6.0%" sub="5-year value chain" color="text-emerald-600" />
        <KpiCard label="Disclosure CAGR" value="+13.8%" sub="Annual completeness growth" />
        <KpiCard label="Peer Percentile" value="P72" sub="Sector disclosure rank" color="text-blue-600" />
      </div>

      <Section title="GHG Emissions Trend (tCO₂e)" icon={TrendingUp}>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={TREND_DATA} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: "11px" }} />
            <Line type="monotone" dataKey="scope1" stroke="#ef4444" strokeWidth={2} dot={false} name="Scope 1" />
            <Line type="monotone" dataKey="scope2" stroke="#f59e0b" strokeWidth={2} dot={false} name="Scope 2" />
            <Line type="monotone" dataKey="scope3" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Scope 3" />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Disclosure Completeness Growth" icon={BarChart3}>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={TREND_DATA} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, "Completeness"]} />
            <Bar dataKey="completeness" fill="#111" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Peer Benchmarking" icon={BarChart3} defaultOpen={false}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={PEER_DATA} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: "11px" }} />
            <Bar dataKey="scope1" name="Scope 1 (tCO₂e)" fill="#111" />
            <Bar dataKey="completeness" name="Completeness %" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   ROOT
══════════════════════════════════════════════════════════════════════════ */
const TABS = [
  { id: "export", label: "XBRL Export", icon: Download },
  { id: "ingest", label: "XBRL Ingestion", icon: Upload },
  { id: "completeness", label: "Disclosure Completeness", icon: CheckCircle },
  { id: "trends", label: "Trend Analytics", icon: TrendingUp },
];

export default function XBRLPage() {
  const [tab, setTab] = useState("export");
  const active = TABS.find(t => t.id === tab);

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">XBRL & Disclosure Completeness</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Generate regulatory XBRL filings · Parse incoming disclosures · Track per-standard completeness
          </p>
        </div>
        <div className="flex gap-1.5">
          {["ESRS ESEF", "ISSB", "GRI", "SFDR"].map(b => (
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

      {/* Content */}
      {tab === "export" && <ExportPanel />}
      {tab === "ingest" && <IngestionPanel />}
      {tab === "completeness" && <CompletenessPanel />}
      {tab === "trends" && <TrendPanel />}

      {/* Footer */}
      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">XBRL Export:</span> iXBRL + XBRL XML per ESRS ESEF Mandate (Reg (EU) 2019/815 as amended); IFRS XBRL per IASB XBRL taxonomy</p>
        <p><span className="font-semibold text-gray-500">Ingestion:</span> SEC EDGAR XBRL parsing · ESMA ESEF validator integration · GRI Digital Reports JSON-LD</p>
        <p><span className="font-semibold text-gray-500">Completeness:</span> Per-standard mandatory DP coverage · RAG traffic light (≥80% green, ≥50% amber, &lt;50% red)</p>
      </div>
    </div>
  );
}
