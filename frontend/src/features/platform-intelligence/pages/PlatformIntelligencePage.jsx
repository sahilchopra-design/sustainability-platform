/**
 * Platform Intelligence Page
 *
 * Tabbed interface for three platform infrastructure engines:
 *  1. Data Lineage & Quality  — /api/v1/lineage
 *  2. Entity 360              — /api/v1/entity360
 *  3. Regulatory Report Compiler — /api/v1/regulatory-reports
 *
 * Route: /platform-intelligence
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadialBarChart, RadialBar, PieChart, Pie, Cell,
} from "recharts";
import {
  Network, Search, FileText, Activity, AlertTriangle, CheckCircle,
  ChevronDown, ChevronUp, Database, Shield, Clock, Layers, Building2,
  Globe, BarChart3, RefreshCw, Send, ArrowRight, XCircle, Info,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt1 = (v) => (v == null ? "\u2014" : Number(v).toFixed(1));
const fmt0 = (v) => (v == null ? "\u2014" : Number(v).toFixed(0));
const pct = (v) => (v == null ? "\u2014" : `${(Number(v) * 100).toFixed(1)}%`);

const SEV_COLOR = { critical: "#ef4444", high: "#f59e0b", medium: "#eab308", low: "#10b981" };
const STATUS_COLOR = { healthy: "#10b981", degraded: "#f59e0b", offline: "#ef4444", unknown: "#6b7280" };
const FRAMEWORKS = ["CSRD", "SFDR", "EU_TAXONOMY", "ISSB", "CBAM"];
const REPORT_TYPES = ["CSRD", "SFDR", "TCFD", "ISSB", "SEC", "GRI", "BRSR"];
const DEGRADATION_TYPES = ["data_unavailable", "quality_degraded", "delayed"];
const SEVERITIES = ["low", "medium", "high", "critical"];

/* ── Shared UI ────────────────────────────────────────────────────────────── */

function Section({ title, children, defaultOpen = true, icon: Icon }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 text-gray-500" />}
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
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-semibold font-mono tabular-nums ${color || "text-gray-900"}`}>{value}</p>
      {sub && <p className="text-[11px] text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-7 h-7 border-2 border-black border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function ErrorBox({ message }) {
  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
      <XCircle className="h-4 w-4 shrink-0" /> {message}
    </div>
  );
}

function Badge({ text, color }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border"
      style={{ background: `${color}15`, color, borderColor: `${color}30` }}>
      {text}
    </span>
  );
}

function TabPill({ tabs, active, onChange }) {
  return (
    <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap">
      {tabs.map((t) => (
        <button key={t.id} onClick={() => onChange(t.id)}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
            active === t.id ? "bg-gray-100 text-gray-700 border border-gray-300" : "text-gray-500 hover:text-gray-600"
          }`}>
          {t.icon && <t.icon className="h-3.5 w-3.5" />}
          {t.label}
        </button>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 1 — DATA LINEAGE & QUALITY
   ═══════════════════════════════════════════════════════════════════════════ */

function DataLineagePanel() {
  const [health, setHealth] = useState(null);
  const [gaps, setGaps] = useState([]);
  const [bridges, setBridges] = useState([]);
  const [coverage, setCoverage] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [framework, setFramework] = useState("CSRD");
  const [lineage, setLineage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Impact analysis state
  const [impactModule, setImpactModule] = useState("");
  const [degradationType, setDegradationType] = useState("data_unavailable");
  const [severity, setSeverity] = useState("medium");
  const [impactResult, setImpactResult] = useState(null);
  const [impactLoading, setImpactLoading] = useState(false);
  const [modules, setModules] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [hRes, gRes, bRes, cRes, aRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/lineage/platform-health`),
        axios.get(`${API_BASE}/api/v1/lineage/reference-data-gaps`),
        axios.get(`${API_BASE}/api/v1/lineage/bridge-health`),
        axios.get(`${API_BASE}/api/v1/lineage/module-coverage`),
        axios.get(`${API_BASE}/api/v1/lineage/audit-events`),
      ]);
      setHealth(hRes.data);
      setGaps(gRes.data?.gaps || gRes.data || []);
      setBridges(bRes.data?.bridges || bRes.data || []);
      setCoverage(cRes.data?.modules || cRes.data || []);
      setAuditEvents(aRes.data?.events || aRes.data || []);
      // Build module list from coverage
      const mods = (cRes.data?.modules || cRes.data || []).map((m) => m.module_name || m.name).filter(Boolean);
      setModules(mods);
      if (mods.length && !impactModule) setImpactModule(mods[0]);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { load(); }, [load]);

  // Regulatory lineage
  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/lineage/regulatory-lineage/${framework}`)
      .then((r) => setLineage(r.data))
      .catch(() => setLineage(null));
  }, [framework]);

  const runImpact = async () => {
    setImpactLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/lineage/impact-analysis`, {
        module_name: impactModule, degradation_type: degradationType, severity,
      });
      setImpactResult(res.data);
    } catch (e) {
      setImpactResult({ error: e.response?.data?.detail || e.message });
    } finally {
      setImpactLoading(false);
    }
  };

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const h = health || {};
  const bcbs = h.bcbs_239_score ?? h.bcbs239_compliance ?? 0;
  const completeness = h.completeness ?? h.data_completeness ?? 0;
  const quality = h.quality_score ?? h.overall_quality ?? 0;
  const moduleCount = h.module_count ?? h.total_modules ?? 0;

  const gaugeData = [{ name: "BCBS 239", value: bcbs, fill: bcbs >= 70 ? "#10b981" : bcbs >= 40 ? "#f59e0b" : "#ef4444" }];

  return (
    <div className="space-y-4">
      {/* Platform Health KPIs */}
      <Section title="Platform Health Dashboard" icon={Activity} defaultOpen>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <KpiCard label="BCBS 239 Compliance" value={`${fmt1(bcbs)}%`} color={bcbs >= 70 ? "text-emerald-400" : "text-amber-400"} sub="Data governance score" />
          <KpiCard label="Completeness" value={pct(completeness)} color="text-gray-700" sub="Cross-module coverage" />
          <KpiCard label="Quality Score" value={fmt1(quality)} color="text-violet-400" sub="DQS-weighted" />
          <KpiCard label="Module Count" value={fmt0(moduleCount)} color="text-gray-900" sub="Registered modules" />
        </div>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="85%" data={gaugeData} startAngle={180} endAngle={0}>
              <RadialBar dataKey="value" cornerRadius={6} background={{ fill: "rgba(255,255,255,0.04)" }} />
              <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff" }} />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      {/* Reference Data Gaps */}
      <Section title="Reference Data Gaps" icon={AlertTriangle} defaultOpen={false}>
        {gaps.length === 0 ? <p className="text-xs text-gray-500">No reference data gaps found.</p> : (
          <div className="overflow-x-auto"><table className="w-full text-xs">
            <thead><tr className="text-gray-500 border-b border-gray-200">
              <th className="text-left pb-2 pr-4">Dataset</th><th className="text-left pb-2 pr-4">Source</th>
              <th className="text-left pb-2 pr-4">Severity</th><th className="text-left pb-2">Affected Modules</th>
            </tr></thead>
            <tbody>{gaps.map((g, i) => (
              <tr key={i} className="border-b border-gray-100">
                <td className="py-2 pr-4 text-gray-700">{g.dataset || g.name}</td>
                <td className="py-2 pr-4 text-gray-500">{g.source || "\u2014"}</td>
                <td className="py-2 pr-4"><Badge text={g.severity || "medium"} color={SEV_COLOR[g.severity] || SEV_COLOR.medium} /></td>
                <td className="py-2 text-gray-500">{(g.affected_modules || []).join(", ") || "\u2014"}</td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </Section>

      {/* Bridge Health */}
      <Section title="Bridge Health Checks" icon={Network} defaultOpen={false}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {bridges.map((b, i) => {
            const icon = (b.status === "healthy" || b.status === "active") ? <CheckCircle className="h-4 w-4 text-emerald-400" />
              : b.status === "degraded" ? <AlertTriangle className="h-4 w-4 text-amber-400" /> : <XCircle className="h-4 w-4 text-red-400" />;
            return (
              <div key={i} className="bg-white border border-gray-200 rounded-lg p-3 flex items-start gap-3">
                <div className="mt-0.5">{icon}</div>
                <div>
                  <p className="text-sm text-gray-800 font-medium">{b.bridge_name || b.name}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{b.description || b.bridge_id || ""}</p>
                  <Badge text={b.status || "unknown"} color={STATUS_COLOR[b.status] || STATUS_COLOR.unknown} />
                </div>
              </div>);
          })}
          {bridges.length === 0 && <p className="text-xs text-gray-500 col-span-3">No bridge data.</p>}
        </div>
      </Section>

      {/* Module Coverage */}
      <Section title="Module Coverage" icon={Layers} defaultOpen={false}>
        {coverage.length === 0 ? <p className="text-xs text-gray-500">No module coverage data.</p> : (
          <div className="overflow-x-auto"><table className="w-full text-xs">
            <thead><tr className="text-gray-500 border-b border-gray-200">
              <th className="text-left pb-2 pr-4">Module</th><th className="text-left pb-2 pr-4">Inputs</th>
              <th className="text-left pb-2 pr-4">Outputs</th><th className="text-left pb-2 pr-4">Quality</th><th className="text-left pb-2">Status</th>
            </tr></thead>
            <tbody>{coverage.slice(0, 30).map((m, i) => (
              <tr key={i} className="border-b border-gray-100">
                <td className="py-1.5 pr-4 text-gray-700 font-medium">{m.module_name || m.name}</td>
                <td className="py-1.5 pr-4 text-gray-500 font-mono">{m.input_count ?? m.inputs ?? "\u2014"}</td>
                <td className="py-1.5 pr-4 text-gray-500 font-mono">{m.output_count ?? m.outputs ?? "\u2014"}</td>
                <td className="py-1.5 pr-4 text-gray-500 font-mono">{m.quality_score != null ? fmt1(m.quality_score) : "\u2014"}</td>
                <td className="py-1.5"><Badge text={m.status || "active"} color={STATUS_COLOR[m.status] || "#10b981"} /></td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </Section>

      {/* Regulatory Lineage */}
      <Section title="Regulatory Lineage Trace" icon={Shield} defaultOpen={false}>
        <div className="flex items-center gap-3 mb-4">
          <label className="text-xs text-gray-500">Framework:</label>
          <select value={framework} onChange={(e) => setFramework(e.target.value)}
            className="bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-blue-500">
            {FRAMEWORKS.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>
        {lineage ? (<div className="space-y-2">
          <p className="text-xs text-gray-500 mb-2">Modules feeding into <span className="text-gray-700 font-medium">{framework}</span>:</p>
          {(lineage.source_modules || lineage.modules || []).map((mod, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <ArrowRight className="h-3 w-3 text-gray-500" />
              <span className="text-gray-600">{mod.module_name || mod.name || mod}</span>
              {mod.data_points && <span className="text-gray-500 ml-2">({mod.data_points} data points)</span>}
            </div>
          ))}
          {(lineage.source_modules || lineage.modules || []).length === 0 && <p className="text-xs text-gray-500">No lineage data for this framework.</p>}
        </div>) : <p className="text-xs text-gray-500">Loading lineage...</p>}
      </Section>

      {/* Audit Events */}
      <Section title="Recent Audit Events" icon={Clock} defaultOpen={false}>
        {auditEvents.length === 0 ? <p className="text-xs text-gray-500">No audit events recorded.</p> : (
          <div className="overflow-x-auto"><table className="w-full text-xs">
            <thead><tr className="text-gray-500 border-b border-gray-200">
              <th className="text-left pb-2 pr-4">Timestamp</th><th className="text-left pb-2 pr-4">Module</th>
              <th className="text-left pb-2 pr-4">Action</th><th className="text-left pb-2">Severity</th>
            </tr></thead>
            <tbody>{auditEvents.slice(0, 20).map((ev, i) => (
              <tr key={i} className="border-b border-gray-100">
                <td className="py-1.5 pr-4 text-gray-500 font-mono">{ev.timestamp || ev.created_at || "\u2014"}</td>
                <td className="py-1.5 pr-4 text-gray-700">{ev.module || ev.module_name}</td>
                <td className="py-1.5 pr-4 text-gray-500">{ev.action || ev.event_type}</td>
                <td className="py-1.5"><Badge text={ev.severity || "info"} color={SEV_COLOR[ev.severity] || "#6b7280"} /></td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </Section>

      {/* Impact Analysis */}
      <Section title="Impact Analysis (What-If)" icon={Layers}>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4">
          <div>
            <label className="text-[10px] text-gray-500 uppercase mb-1 block">Module</label>
            <select value={impactModule} onChange={(e) => setImpactModule(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-blue-500">
              {modules.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase mb-1 block">Degradation</label>
            <select value={degradationType} onChange={(e) => setDegradationType(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-blue-500">
              {DEGRADATION_TYPES.map((d) => <option key={d} value={d}>{d.replace(/_/g, " ")}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase mb-1 block">Severity</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-blue-500">
              {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={runImpact} disabled={impactLoading || !impactModule}
              className="w-full bg-gray-100 hover:bg-gray-300 text-gray-700 border border-gray-300 rounded-md px-4 py-1.5 text-xs font-medium transition-colors disabled:opacity-40 flex items-center justify-center gap-1.5">
              {impactLoading ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
              Analyse
            </button>
          </div>
        </div>
        {impactResult && !impactResult.error && (
          <div className="space-y-3">
            <p className="text-xs text-gray-500">Downstream impact from <span className="text-gray-700">{impactModule}</span> degradation:</p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-500 border-b border-gray-200">
                    <th className="text-left pb-2 pr-4">Affected Module</th>
                    <th className="text-left pb-2 pr-4">Impact</th>
                    <th className="text-left pb-2">Regulatory Output</th>
                  </tr>
                </thead>
                <tbody>
                  {(impactResult.downstream_impacts || impactResult.affected_modules || []).map((d, i) => (
                    <tr key={i} className="border-b border-gray-100">
                      <td className="py-1.5 pr-4 text-gray-700">{d.module_name || d.module || d.name}</td>
                      <td className="py-1.5 pr-4"><Badge text={d.impact_level || d.severity || "medium"} color={SEV_COLOR[d.impact_level || d.severity] || SEV_COLOR.medium} /></td>
                      <td className="py-1.5 text-gray-500">{(d.regulatory_outputs || []).join(", ") || "\u2014"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {impactResult?.error && <ErrorBox message={impactResult.error} />}
      </Section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 2 — ENTITY 360
   ═══════════════════════════════════════════════════════════════════════════ */

function Entity360Panel() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [error, setError] = useState(null);

  // Search-as-you-type with debounce
  useEffect(() => {
    if (query.length < 2) { setResults([]); return; }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await axios.get(`${API_BASE}/api/v1/entity360/search`, { params: { q: query } });
        setResults(res.data?.entities || res.data || []);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [query]);

  // Load profile
  const loadProfile = useCallback(async (id) => {
    setSelectedId(id);
    setProfileLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/v1/entity360/${id}/profile`);
      setProfile(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  }, []);

  const p = profile || {};
  const info = p.company_info || p.entity || {};
  const matrix = p.cross_module_availability || p.module_availability || [];
  const metrics = p.key_metrics || p.metrics_summary || [];
  const timeline = p.assessment_timeline || p.timeline || [];

  // Module availability chart data
  const availChart = matrix.map((m) => ({
    name: (m.module_name || m.module || "").replace(/_/g, " ").slice(0, 18),
    available: m.has_data ? 1 : 0,
    fill: m.has_data ? "#10b981" : "rgba(255,255,255,0.06)",
  }));

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search entities by name, LEI, or sector..."
          className="w-full bg-white border border-gray-300 rounded-lg pl-9 pr-4 py-2.5 text-sm text-gray-800 placeholder-black/25 focus:outline-none focus:border-blue-500 transition-colors" />
        {searching && <RefreshCw className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-700 animate-spin" />}
      </div>

      {/* Search Results */}
      {results.length > 0 && !selectedId && (
        <div className="bg-white border border-gray-200 rounded-lg max-h-56 overflow-y-auto">
          {results.map((ent, i) => (
            <button key={ent.entity_id || ent.id || i} onClick={() => loadProfile(ent.entity_id || ent.id)}
              className="w-full text-left px-4 py-2.5 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0">
              <p className="text-sm text-gray-800 font-medium">{ent.name || ent.entity_name}</p>
              <p className="text-[10px] text-gray-500">{ent.sector || ""} {ent.country ? ` \u00b7 ${ent.country}` : ""} {ent.lei ? ` \u00b7 LEI: ${ent.lei}` : ""}</p>
            </button>
          ))}
        </div>
      )}
      {profileLoading && <Spinner />}
      {error && <ErrorBox message={error} />}

      {profile && !profileLoading && (
        <>
          {/* Company Info Card */}
          <Section title="Company Information" icon={Building2}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KpiCard label="Entity Name" value={info.name || info.entity_name || "\u2014"} color="text-gray-900" />
              <KpiCard label="LEI" value={info.lei || "\u2014"} color="text-gray-700" sub="Legal Entity Identifier" />
              <KpiCard label="Sector" value={info.sector || info.nace_sector || "\u2014"} color="text-violet-400" />
              <KpiCard label="Country" value={info.country || info.jurisdiction || "\u2014"} color="text-emerald-400" />
            </div>
          </Section>

          {/* Cross-Module Availability */}
          <Section title="Cross-Module Data Availability" icon={Database} defaultOpen>
            {availChart.length > 0 ? (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={availChart} layout="vertical" margin={{ left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis type="number" domain={[0, 1]} tick={false} axisLine={false} />
                    <YAxis dataKey="name" type="category" width={130} tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} axisLine={false} />
                    <Bar dataKey="available" radius={[0, 4, 4, 0]} barSize={14}>
                      {availChart.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                    </Bar>
                    <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff", fontSize: 11 }}
                      formatter={(v) => v === 1 ? "Available" : "No data"} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : <p className="text-xs text-gray-500">No module availability data.</p>}
          </Section>
          {/* Key Metrics */}
          <Section title="Key Metrics Summary" icon={BarChart3} defaultOpen={false}>
            {metrics.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {metrics.map((m, i) => (
                  <KpiCard key={i} label={m.metric_name || m.label || m.name} value={m.value != null ? (typeof m.value === "number" ? fmt1(m.value) : m.value) : "\u2014"} sub={m.module || m.source || ""} />
                ))}
              </div>
            ) : <p className="text-xs text-gray-500">No aggregated metrics available for this entity.</p>}
          </Section>
          {/* Assessment Timeline */}
          <Section title="Assessment Timeline" icon={Clock} defaultOpen={false}>
            {timeline.length > 0 ? (
              <div className="space-y-2">
                {timeline.slice(0, 15).map((t, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs border-b border-gray-100 pb-2">
                    <span className="text-gray-500 font-mono w-36 shrink-0">{t.date || t.timestamp || t.run_date}</span>
                    <span className="text-gray-600">{t.module || t.analysis_type}</span>
                    <span className="text-gray-500 ml-auto">{t.status || t.result || ""}</span>
                  </div>
                ))}
              </div>
            ) : <p className="text-xs text-gray-500">No assessment history.</p>}
          </Section>

          <button onClick={() => { setSelectedId(null); setProfile(null); setQuery(""); }}
            className="text-xs text-gray-700 hover:underline flex items-center gap-1 mt-2">
            <ArrowRight className="h-3 w-3 rotate-180" /> Back to search
          </button>
        </>
      )}

      {!profile && !profileLoading && !error && results.length === 0 && query.length < 2 && (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400">
          <Globe className="h-12 w-12 mb-3" /><p className="text-sm">Search for an entity to view its unified 360 profile</p>
        </div>)}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 3 — REGULATORY REPORT COMPILER
   ═══════════════════════════════════════════════════════════════════════════ */

function ReportCompilerPanel() {
  const [templates, setTemplates] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Compile form
  const [entityName, setEntityName] = useState("");
  const [reportType, setReportType] = useState("CSRD");
  const [reportingYear, setReportingYear] = useState(new Date().getFullYear());
  const [sections, setSections] = useState([]);
  const [availableSections, setAvailableSections] = useState([]);
  const [compileResult, setCompileResult] = useState(null);
  const [compiling, setCompiling] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [tRes, rRes] = await Promise.all([
          axios.get(`${API_BASE}/api/v1/regulatory-reports/templates`),
          axios.get(`${API_BASE}/api/v1/regulatory-reports/recent`),
        ]);
        setTemplates(tRes.data?.templates || tRes.data || []);
        setRecent(rRes.data?.reports || rRes.data || []);
      } catch (e) {
        setError(e.response?.data?.detail || e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Update available sections when report type changes
  useEffect(() => {
    const tpl = templates.find((t) => (t.report_type || t.type || t.name) === reportType);
    const secs = tpl?.sections || tpl?.available_sections || [];
    setAvailableSections(secs);
    setSections(secs.map((s) => s.id || s.section_id || s.name || s));
  }, [reportType, templates]);

  const toggleSection = (id) => {
    setSections((prev) => prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]);
  };

  const compile = async () => {
    if (!entityName.trim()) return;
    setCompiling(true);
    setCompileResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/regulatory-reports/compile`, {
        entity_name: entityName, report_type: reportType, reporting_year: reportingYear,
        sections_to_include: sections,
      });
      setCompileResult(res.data);
    } catch (e) {
      setCompileResult({ error: e.response?.data?.detail || e.message });
    } finally {
      setCompiling(false);
    }
  };

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const cr = compileResult || {};
  const reportSections = cr.sections || cr.report_sections || [];
  const overallComplete = cr.overall_completeness ?? cr.completeness_pct;
  const exportReady = cr.export_readiness ?? cr.readiness_score;

  // Completeness pie data
  const pieData = overallComplete != null ? [
    { name: "Complete", value: overallComplete, fill: "#10b981" },
    { name: "Remaining", value: 100 - overallComplete, fill: "rgba(255,255,255,0.06)" },
  ] : [];

  return (
    <div className="space-y-4">
      {/* Templates Catalog */}
      <Section title="Report Template Catalog" icon={FileText} defaultOpen={false}>
        {templates.length === 0 ? <p className="text-xs text-gray-500">No templates available.</p> : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {templates.map((t, i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-lg p-3">
                <p className="text-sm text-gray-800 font-medium">{t.report_type || t.type || t.name}</p>
                <p className="text-[10px] text-gray-500 mt-1">{t.description || `${(t.sections || []).length} sections`}</p>
                <div className="flex gap-1.5 mt-2 flex-wrap">
                  {(t.frameworks || []).map((f, j) => <Badge key={j} text={f} color="#6366f1" />)}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Compile Form */}
      <Section title="Compile Regulatory Report" icon={Layers}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <div>
            <label className="text-[10px] text-gray-500 uppercase mb-1 block">Entity Name</label>
            <input value={entityName} onChange={(e) => setEntityName(e.target.value)} placeholder="e.g. Acme Corp"
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 placeholder-gray-400 focus:outline-none focus:border-blue-500" />
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase mb-1 block">Report Type</label>
            <select value={reportType} onChange={(e) => setReportType(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-blue-500">
              {REPORT_TYPES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-gray-500 uppercase mb-1 block">Reporting Year</label>
            <input type="number" value={reportingYear} onChange={(e) => setReportingYear(Number(e.target.value))}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:border-blue-500" />
          </div>
        </div>

        {/* Section multi-select */}
        {availableSections.length > 0 && (
          <div className="mb-4">
            <label className="text-[10px] text-gray-500 uppercase mb-2 block">Sections to Include</label>
            <div className="flex flex-wrap gap-2">
              {availableSections.map((s, i) => {
                const id = s.id || s.section_id || s.name || s;
                const label = s.title || s.name || s;
                const selected = sections.includes(id);
                return (
                  <button key={i} onClick={() => toggleSection(id)}
                    className={`px-3 py-1 rounded-md text-[11px] border transition-colors ${
                      selected ? "bg-gray-100 text-gray-700 border-gray-300" : "bg-white text-gray-500 border-gray-200 hover:text-gray-600"
                    }`}>
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <button onClick={compile} disabled={compiling || !entityName.trim()}
          className="bg-gray-100 hover:bg-gray-300 text-gray-700 border border-gray-300 rounded-md px-5 py-2 text-xs font-medium transition-colors disabled:opacity-40 flex items-center gap-1.5">
          {compiling ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
          Compile Report
        </button>
      </Section>

      {/* Compile Results */}
      {compileResult && !compileResult.error && (
        <Section title="Compilation Result" icon={CheckCircle}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <KpiCard label="Report Type" value={cr.report_type || reportType} color="text-violet-400" />
            <KpiCard label="Completeness" value={overallComplete != null ? `${fmt0(overallComplete)}%` : "\u2014"} color={overallComplete >= 70 ? "text-emerald-400" : "text-amber-400"} />
            <KpiCard label="Export Readiness" value={exportReady != null ? `${fmt0(exportReady)}%` : "\u2014"} color="text-gray-700" />
            <KpiCard label="Sections" value={reportSections.length} color="text-gray-900" />
          </div>

          {/* Completeness pie */}
          {pieData.length > 0 && (
            <div className="h-40 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" cx="50%" cy="50%" innerRadius={40} outerRadius={60} paddingAngle={2}>
                    {pieData.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#fff", fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          {/* Section breakdown */}
          {reportSections.length > 0 && (
            <div className="overflow-x-auto"><table className="w-full text-xs">
              <thead><tr className="text-gray-500 border-b border-gray-200">
                <th className="text-left pb-2 pr-4">Section</th><th className="text-left pb-2 pr-4">Completeness</th>
                <th className="text-left pb-2 pr-4">Data Source</th><th className="text-left pb-2">Gaps</th>
              </tr></thead>
              <tbody>{reportSections.map((s, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-1.5 pr-4 text-gray-700 font-medium">{s.section_name || s.title || s.name}</td>
                  <td className="py-1.5 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-50 rounded-full h-1.5 overflow-hidden max-w-[80px]">
                        <div className="h-full rounded-full" style={{ width: `${s.completeness ?? s.completeness_pct ?? 0}%`, background: (s.completeness ?? s.completeness_pct ?? 0) >= 70 ? "#10b981" : "#f59e0b" }} />
                      </div>
                      <span className="text-gray-500 font-mono">{fmt0(s.completeness ?? s.completeness_pct ?? 0)}%</span>
                    </div>
                  </td>
                  <td className="py-1.5 pr-4 text-gray-500">{s.data_source || s.source_module || "\u2014"}</td>
                  <td className="py-1.5 text-gray-500">{s.gaps_count ?? (s.gaps || []).length ?? 0}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </Section>
      )}
      {compileResult?.error && <ErrorBox message={compileResult.error} />}

      {/* Recently Compiled Reports */}
      <Section title="Recently Compiled Reports" icon={Clock} defaultOpen={false}>
        {recent.length === 0 ? <p className="text-xs text-gray-500">No recent compilations.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="text-gray-500 border-b border-gray-200">
                <th className="text-left pb-2 pr-4">Entity</th><th className="text-left pb-2 pr-4">Type</th>
                <th className="text-left pb-2 pr-4">Year</th><th className="text-left pb-2 pr-4">Completeness</th><th className="text-left pb-2">Status</th>
              </tr></thead>
              <tbody>
                {recent.slice(0, 10).map((r, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-1.5 pr-4 text-gray-700">{r.entity_name || r.entity}</td>
                    <td className="py-1.5 pr-4 text-gray-500">{r.report_type || r.type}</td>
                    <td className="py-1.5 pr-4 text-gray-500 font-mono">{r.reporting_year || r.year}</td>
                    <td className="py-1.5 pr-4 text-gray-500 font-mono">{r.completeness != null ? `${fmt0(r.completeness)}%` : "\u2014"}</td>
                    <td className="py-1.5"><Badge text={r.status || "completed"} color={STATUS_COLOR[r.status] || "#10b981"} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════════════════ */

const PAGE_TABS = [
  { id: "lineage", label: "Data Lineage & Quality", icon: Network },
  { id: "entity360", label: "Entity 360", icon: Globe },
  { id: "reports", label: "Report Compiler", icon: FileText },
];

export default function PlatformIntelligencePage() {
  const [tab, setTab] = useState("lineage");

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Activity className="h-6 w-6 text-gray-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Platform Intelligence</h1>
              <p className="text-gray-500 text-sm">Data lineage, entity resolution & regulatory report compilation</p>
            </div>
          </div>
          <div className="flex gap-2 mt-3 flex-wrap">
            <Badge text="BCBS 239" color="#06b6d4" />
            <Badge text="DQS Quality" color="#8b5cf6" />
            <Badge text="Cross-Module" color="#10b981" />
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="mb-6">
          <TabPill tabs={PAGE_TABS} active={tab} onChange={setTab} />
        </div>

        {/* Tab Content */}
        {tab === "lineage" && <DataLineagePanel />}
        {tab === "entity360" && <Entity360Panel />}
        {tab === "reports" && <ReportCompilerPanel />}
      </div>
    </div>
  );
}
