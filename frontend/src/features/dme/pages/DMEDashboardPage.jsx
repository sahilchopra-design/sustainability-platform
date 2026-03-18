/**
 * DME Dashboard -- Dynamic Materiality Engine
 *
 * Tab 1 -- Velocity Monitor    /api/v1/dme-velocity   (entity metric velocity timeseries, regime detection)
 * Tab 2 -- Alert Dashboard     /api/v1/dme-alerts     (4-tier alert system: WATCH/ELEVATED/CRITICAL/EXTREME)
 * Tab 3 -- Contagion Network   /api/v1/dme-contagion  (Hawkes process systemic risk, cascade simulation)
 * Tab 4 -- DMI Scoring         /api/v1/dme-dmi        (Dynamic Materiality Index, PCAF quality, concentration)
 * Tab 5 -- Greenwashing & NLP  /api/v1/dme-greenwashing + /api/v1/dme-nlp-pulse (detection + sentiment)
 * Tab 6 -- Policy Velocity     /api/v1/dme-policy-tracker (regulatory change velocity, jurisdiction comparison)
 */
import React, { useState } from "react";
import axios from "axios";
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  ScatterChart, Scatter, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ReferenceLine,
} from "recharts";
import {
  Activity, AlertTriangle, Network, BarChart3, Shield, ScrollText,
  ChevronDown, ChevronUp, RefreshCw, Play, Gauge, TrendingUp,
  Zap, Eye, Target, Radio, Globe, Scale, Leaf, BellRing,
  CheckCircle, XCircle, AlertCircle, Info, Search, Filter,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";

/* -- Deterministic seed helper ------------------------------------------------ */
function sr(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

/* -- Shared primitives -------------------------------------------------------- */
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
        placeholder-gray-400 focus:outline-none focus:border-emerald-500" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800
        focus:outline-none focus:border-emerald-500">
      {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  );
}

function Btn({ onClick, disabled, loading, children, variant = "primary" }) {
  const base = "inline-flex items-center gap-1.5 px-4 py-2 rounded text-xs font-medium transition-all";
  const styles = variant === "primary"
    ? "bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-40"
    : "bg-gray-100 text-gray-700 hover:bg-gray-800/[0.10] disabled:opacity-40";
  return (
    <button onClick={onClick} disabled={disabled || loading} className={`${base} ${styles}`}>
      {loading && <RefreshCw className="h-3 w-3 animate-spin" />}
      {children}
    </button>
  );
}

const TOOLTIP_STYLE = { backgroundColor: "#fff", border: "1px solid rgba(0,0,0,0.08)", color: "#111" };

/* -- Color constants ---------------------------------------------------------- */
const REGIME_COLORS = { NORMAL: "#10b981", ELEVATED: "#f59e0b", CRITICAL: "#f97316", EXTREME: "#ef4444" };
const TIER_COLORS = { WATCH: "#94a3b8", ELEVATED: "#f59e0b", CRITICAL: "#f97316", EXTREME: "#ef4444" };
const PRIORITY_COLORS = { LOW: "#94a3b8", MEDIUM: "#3b82f6", HIGH: "#f97316", CRITICAL: "#ef4444" };
const PCAF_COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"];
const EMERALD = "#10b981";
const EMERALD_LIGHT = "#34d399";

/* -- Entity / metric reference data ------------------------------------------- */
const ENTITIES = [
  { v: "ent-001", l: "Deutsche Bank AG" },
  { v: "ent-002", l: "Shell PLC" },
  { v: "ent-003", l: "TotalEnergies SE" },
  { v: "ent-004", l: "Glencore PLC" },
  { v: "ent-005", l: "ArcelorMittal SA" },
  { v: "ent-006", l: "HeidelbergCement AG" },
  { v: "ent-007", l: "RWE AG" },
  { v: "ent-008", l: "BP PLC" },
];

const METRIC_KEYS = [
  { v: "carbon_intensity", l: "Carbon Intensity (tCO2/M rev)" },
  { v: "scope1_abs", l: "Scope 1 Absolute (ktCO2e)" },
  { v: "scope3_cat11", l: "Scope 3 Cat 11 -- Use of Sold Products" },
  { v: "water_withdrawal", l: "Water Withdrawal (ML)" },
  { v: "biodiversity_impact", l: "Biodiversity Impact Score" },
  { v: "transition_risk_pd", l: "Transition Risk PD Adjustment" },
];

const SECTORS = ["Energy", "Materials", "Industrials", "Utilities", "Finance", "Real Estate", "Transport", "Agriculture"];
const JURISDICTIONS = ["EU", "US", "UK", "AU", "JP", "SG", "CA", "BR"];

/* ============================================================================
   TAB 1 -- VELOCITY MONITOR
============================================================================ */
function VelocityMonitorPanel() {
  const [entity, setEntity] = useState("ent-001");
  const [metricKey, setMetricKey] = useState("carbon_intensity");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const rng = sr(101 + entity.charCodeAt(4) * 7 + metricKey.length * 13);

  /* Deterministic velocity timeseries */
  const REGIMES = ["NORMAL", "NORMAL", "NORMAL", "ELEVATED", "NORMAL", "NORMAL", "ELEVATED",
    "CRITICAL", "ELEVATED", "NORMAL", "NORMAL", "NORMAL", "ELEVATED", "ELEVATED",
    "CRITICAL", "EXTREME", "CRITICAL", "ELEVATED", "NORMAL", "NORMAL", "NORMAL",
    "NORMAL", "ELEVATED", "NORMAL"];
  const timeseries = [];
  for (let i = 0; i < 24; i++) {
    const raw = (rng() - 0.5) * 4 + Math.sin(i / 3) * 1.5;
    const smoothed = raw * 0.7 + (rng() - 0.5) * 0.6;
    const zScore = (raw - smoothed) / (0.8 + rng() * 0.4);
    timeseries.push({
      month: `2024-${String((i % 12) + 1).padStart(2, "0")}`,
      raw: +raw.toFixed(3),
      smoothed: +smoothed.toFixed(3),
      z_score: +zScore.toFixed(3),
      regime: REGIMES[i],
    });
  }

  const latestRegime = timeseries[timeseries.length - 1].regime;
  const latestZ = timeseries[timeseries.length - 1].z_score;
  const latestVel = timeseries[timeseries.length - 1].raw;
  const accel = timeseries.length >= 2
    ? +(timeseries[timeseries.length - 1].raw - timeseries[timeseries.length - 2].raw).toFixed(3)
    : 0;
  const normalPct = +((timeseries.filter(t => t.regime === "NORMAL").length / timeseries.length) * 100).toFixed(1);

  async function handleFetch() {
    setLoading(true); setError(null);
    try {
      const r = await axios.post(`${API_BASE}/api/v1/dme-velocity`, { entity_id: entity, metric_key: metricKey });
      setResult(r.data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <Section title="Velocity Parameters" icon={Activity}>
        <div className="grid grid-cols-2 gap-4">
          <Row label="Entity"><Sel value={entity} onChange={setEntity} options={ENTITIES} /></Row>
          <Row label="Metric Key"><Sel value={metricKey} onChange={setMetricKey} options={METRIC_KEYS} /></Row>
        </div>
        <div className="mt-3"><Btn onClick={handleFetch} loading={loading}><Play className="h-3 w-3" />Fetch Velocity</Btn></div>
        {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
      </Section>

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Observations" value={timeseries.length} sub="24-month window" />
        <KpiCard label="% in NORMAL" value={`${normalPct}%`} sub="Regime distribution" color={normalPct > 60 ? "text-emerald-600" : "text-amber-600"} />
        <KpiCard label="Latest Velocity" value={latestVel.toFixed(3)} sub="Raw metric velocity" color="text-gray-900" />
        <KpiCard label="Latest Acceleration" value={accel > 0 ? `+${accel}` : String(accel)} sub="Month-over-month delta" color={accel > 0 ? "text-red-500" : "text-emerald-600"} />
      </div>

      {/* Current regime badge */}
      <Section title="Current Regime" icon={Gauge}>
        <div className="flex items-center gap-4">
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold text-white"
            style={{ backgroundColor: REGIME_COLORS[latestRegime] }}>
            {latestRegime}
          </span>
          <div className="text-xs text-gray-600">
            Z-score: <span className="font-mono font-semibold">{latestZ.toFixed(3)}</span>
            {" | "}Threshold: <span className="text-gray-400">ELEVATED &gt; 1.5, CRITICAL &gt; 2.5, EXTREME &gt; 3.5</span>
          </div>
        </div>
      </Section>

      {/* Velocity timeseries chart */}
      <Section title="Velocity Timeseries" icon={TrendingUp}>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={timeseries} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Line type="monotone" dataKey="raw" name="Raw Velocity" stroke="#6b7280" strokeWidth={1.5} dot={false} />
            <Line type="monotone" dataKey="smoothed" name="Smoothed" stroke={EMERALD} strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="z_score" name="Z-Score" stroke="#8b5cf6" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
            <ReferenceLine y={1.5} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "ELEVATED", fontSize: 9, fill: "#f59e0b" }} />
            <ReferenceLine y={2.5} stroke="#f97316" strokeDasharray="3 3" label={{ value: "CRITICAL", fontSize: 9, fill: "#f97316" }} />
            <ReferenceLine y={3.5} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "EXTREME", fontSize: 9, fill: "#ef4444" }} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      {/* Regime heatmap strip */}
      <Section title="Regime Heatmap" icon={BarChart3}>
        <div className="flex gap-0.5">
          {timeseries.map((t, i) => (
            <div key={i} className="flex-1 h-8 rounded-sm relative group cursor-pointer"
              style={{ backgroundColor: REGIME_COLORS[t.regime] }}>
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block
                bg-gray-900 text-white text-[9px] px-2 py-1 rounded whitespace-nowrap z-10">
                {t.month}: {t.regime} (z={t.z_score})
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-4 mt-2">
          {Object.entries(REGIME_COLORS).map(([k, c]) => (
            <div key={k} className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: c }} />
              <span className="text-[10px] text-gray-500">{k}</span>
            </div>
          ))}
        </div>
      </Section>

      {result && (
        <Section title="API Response" icon={Info} defaultOpen={false}>
          <pre className="text-[10px] text-gray-600 bg-gray-50 rounded p-3 overflow-auto max-h-48">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}

/* ============================================================================
   TAB 2 -- ALERT DASHBOARD
============================================================================ */
function AlertDashboardPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const rng = sr(202);

  /* Tier breakdown */
  const TIERS = ["WATCH", "ELEVATED", "CRITICAL", "EXTREME"];
  const tierCounts = TIERS.map(t => ({ tier: t, count: Math.floor(rng() * 30) + 2, fill: TIER_COLORS[t] }));
  const totalAlerts = tierCounts.reduce((s, t) => s + t.count, 0);

  /* Priority distribution */
  const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
  const priorityData = PRIORITIES.map(p => ({ priority: p, count: Math.floor(rng() * 25) + 1, fill: PRIORITY_COLORS[p] }));

  /* Recent alerts table */
  const FACTORS = ["carbon_intensity", "water_stress", "transition_pd", "scope1_abs", "biodiversity_loss", "governance_score"];
  const alerts = [];
  for (let i = 0; i < 15; i++) {
    const tierIdx = Math.min(3, Math.floor(rng() * 4));
    const priIdx = Math.min(3, Math.floor(rng() * 4));
    alerts.push({
      id: `ALR-${1000 + i}`,
      entity: ENTITIES[Math.floor(rng() * ENTITIES.length)].l,
      factor: FACTORS[Math.floor(rng() * FACTORS.length)],
      tier: TIERS[tierIdx],
      priority: PRIORITIES[priIdx],
      priority_score: +(rng() * 100).toFixed(1),
      triggered_at: `2026-03-${String(Math.floor(rng() * 15) + 1).padStart(2, "0")} ${String(Math.floor(rng() * 24)).padStart(2, "0")}:${String(Math.floor(rng() * 60)).padStart(2, "0")}`,
      sla_hours: [4, 8, 24, 72][tierIdx],
      resolved: rng() > 0.6,
    });
  }

  const unresolvedCount = alerts.filter(a => !a.resolved).length;
  const avgPriority = +(alerts.reduce((s, a) => s + a.priority_score, 0) / alerts.length).toFixed(1);
  const avgSLA = +(alerts.reduce((s, a) => s + a.sla_hours, 0) / alerts.length).toFixed(1);
  const slaCompliance = +((alerts.filter(a => a.resolved).length / alerts.length) * 100).toFixed(1);

  async function handleFetch() {
    setLoading(true); setError(null);
    try {
      const r = await axios.get(`${API_BASE}/api/v1/dme-alerts`);
      setResult(r.data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Btn onClick={handleFetch} loading={loading}><RefreshCw className="h-3 w-3" />Refresh Alerts</Btn>
        {error && <p className="text-xs text-red-500 self-center">{error}</p>}
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Total Alerts" value={totalAlerts} sub="Active alert count" />
        <KpiCard label="Unresolved" value={unresolvedCount} sub={`${((unresolvedCount/totalAlerts)*100).toFixed(0)}% open`} color="text-red-500" />
        <KpiCard label="Avg Priority Score" value={avgPriority} sub="0-100 scale" color="text-amber-600" />
        <KpiCard label="SLA Compliance" value={`${slaCompliance}%`} sub={`Avg response ${avgSLA}h`} color={slaCompliance >= 70 ? "text-emerald-600" : "text-red-500"} />
      </div>

      {/* Tier breakdown */}
      <Section title="Tier Breakdown" icon={AlertTriangle}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={tierCounts} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="tier" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="count" name="Alert Count" radius={[4, 4, 0, 0]}>
              {tierCounts.map((t, i) => <Cell key={i} fill={t.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Priority distribution */}
      <Section title="Priority Band Distribution" icon={Target}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={priorityData} layout="vertical" margin={{ top: 5, right: 20, left: 60, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis type="number" tick={{ fontSize: 10 }} />
            <YAxis type="category" dataKey="priority" tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="count" name="Count" radius={[0, 4, 4, 0]}>
              {priorityData.map((p, i) => <Cell key={i} fill={p.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* SLA compliance gauge */}
      <Section title="SLA Compliance Gauge" icon={Gauge}>
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
              <circle cx="50" cy="50" r="40" fill="none" stroke={slaCompliance >= 70 ? EMERALD : "#ef4444"}
                strokeWidth="8" strokeDasharray={`${slaCompliance * 2.51} 251`}
                strokeLinecap="round" transform="rotate(-90 50 50)" />
              <text x="50" y="48" textAnchor="middle" className="text-lg font-bold" fill="#111" fontSize="16">{slaCompliance}%</text>
              <text x="50" y="62" textAnchor="middle" fill="#9ca3af" fontSize="7">SLA met</text>
            </svg>
          </div>
          <div className="text-xs text-gray-500 space-y-1">
            <p>EXTREME alerts: <span className="font-semibold text-red-500">4h SLA</span></p>
            <p>CRITICAL alerts: <span className="font-semibold text-orange-500">8h SLA</span></p>
            <p>ELEVATED alerts: <span className="font-semibold text-amber-500">24h SLA</span></p>
            <p>WATCH alerts: <span className="font-semibold text-gray-600">72h SLA</span></p>
          </div>
        </div>
      </Section>

      {/* Recent alerts table */}
      <Section title="Recent Alerts" icon={BellRing}>
        <div className="overflow-auto max-h-72">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500 text-left">
                <th className="py-2 px-2 font-medium">ID</th>
                <th className="py-2 px-2 font-medium">Entity</th>
                <th className="py-2 px-2 font-medium">Factor</th>
                <th className="py-2 px-2 font-medium">Tier</th>
                <th className="py-2 px-2 font-medium">Priority</th>
                <th className="py-2 px-2 font-medium">Score</th>
                <th className="py-2 px-2 font-medium">Triggered</th>
                <th className="py-2 px-2 font-medium">SLA (h)</th>
                <th className="py-2 px-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-1.5 px-2 font-mono text-gray-400">{a.id}</td>
                  <td className="py-1.5 px-2">{a.entity}</td>
                  <td className="py-1.5 px-2 font-mono text-gray-600">{a.factor}</td>
                  <td className="py-1.5 px-2">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold text-white"
                      style={{ backgroundColor: TIER_COLORS[a.tier] }}>{a.tier}</span>
                  </td>
                  <td className="py-1.5 px-2">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold"
                      style={{ color: PRIORITY_COLORS[a.priority] }}>{a.priority}</span>
                  </td>
                  <td className="py-1.5 px-2 font-mono">{a.priority_score}</td>
                  <td className="py-1.5 px-2 text-gray-500">{a.triggered_at}</td>
                  <td className="py-1.5 px-2 font-mono">{a.sla_hours}</td>
                  <td className="py-1.5 px-2">
                    {a.resolved
                      ? <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                      : <AlertCircle className="h-3.5 w-3.5 text-red-400" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {result && (
        <Section title="API Response" icon={Info} defaultOpen={false}>
          <pre className="text-[10px] text-gray-600 bg-gray-50 rounded p-3 overflow-auto max-h-48">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}

/* ============================================================================
   TAB 3 -- CONTAGION NETWORK
============================================================================ */
function ContagionNetworkPanel() {
  const [seedEntity, setSeedEntity] = useState("ent-002");
  const [severity, setSeverity] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [simResult, setSimResult] = useState(null);

  const rng = sr(303);

  /* Layer intensities */
  const layerData = [
    { layer: "L1 Direct", intensity: +(0.3 + rng() * 0.5).toFixed(3), count: Math.floor(rng() * 8) + 2 },
    { layer: "L2 Indirect", intensity: +(0.15 + rng() * 0.35).toFixed(3), count: Math.floor(rng() * 12) + 5 },
    { layer: "L3 Systemic", intensity: +(0.05 + rng() * 0.2).toFixed(3), count: Math.floor(rng() * 20) + 10 },
  ];
  const radarData = layerData.map(l => ({ subject: l.layer, value: l.intensity, fullMark: 1.0 }));

  /* EL/VaR/ES amplification */
  const ampData = [
    { metric: "Expected Loss", amplification: +(3.5 + rng() * 2).toFixed(2), target: 4.3 },
    { metric: "Value-at-Risk", amplification: +(3.8 + rng() * 2).toFixed(2), target: 4.5 },
    { metric: "Expected Shortfall", amplification: +(2.5 + rng() * 1.5).toFixed(2), target: 3.2 },
  ];

  /* Spectral radius */
  const spectralRadius = +(0.6 + rng() * 0.5).toFixed(4);
  const isStable = spectralRadius < 1.0;

  /* Aggregate intensity */
  const aggIntensity = +(layerData.reduce((s, l) => s + l.intensity, 0)).toFixed(3);
  const entitiesAffected = layerData.reduce((s, l) => s + l.count, 0);

  async function handleFetch() {
    setLoading(true); setError(null);
    try {
      const r = await axios.post(`${API_BASE}/api/v1/dme-contagion`, { entity_id: seedEntity, severity });
      setResult(r.data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  }

  function handleSimulate() {
    const simRng = sr(seedEntity.charCodeAt(4) * 100 + Math.floor(severity * 100));
    const cascadeSteps = [];
    let currentEntities = 1;
    for (let step = 0; step < 8; step++) {
      currentEntities = Math.min(ENTITIES.length, currentEntities + Math.floor(simRng() * 3 * severity));
      const elAmp = +(1.0 + step * severity * (0.8 + simRng() * 0.5)).toFixed(2);
      cascadeSteps.push({ step, entities: currentEntities, el_amplification: elAmp });
    }
    setSimResult(cascadeSteps);
  }

  return (
    <div className="space-y-4">
      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Aggregate Intensity" value={aggIntensity} sub="Sum across layers" color="text-gray-900" />
        <KpiCard label="Spectral Radius" value={spectralRadius} sub={isStable ? "System stable" : "UNSTABLE"} color={isStable ? "text-emerald-600" : "text-red-500"} />
        <KpiCard label="Entities Affected" value={entitiesAffected} sub="Across L1/L2/L3" />
        <KpiCard label="Stability Status" value={isStable ? "STABLE" : "CRITICAL"} sub={`rho = ${spectralRadius}`} color={isStable ? "text-emerald-600" : "text-red-500"} />
      </div>

      {/* Layer intensity radar */}
      <Section title="Layer Intensity Profile" icon={Network}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
                <PolarRadiusAxis angle={30} domain={[0, 1]} tick={{ fontSize: 9 }} />
                <Radar name="Intensity" dataKey="value" stroke={EMERALD} fill={EMERALD} fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2">
            {layerData.map((l, i) => (
              <div key={i} className="flex items-center justify-between border border-gray-100 rounded p-2">
                <span className="text-xs text-gray-600">{l.layer}</span>
                <div className="text-right">
                  <span className="text-sm font-mono font-semibold">{l.intensity}</span>
                  <span className="text-[10px] text-gray-400 ml-2">{l.count} entities</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* EL/VaR/ES amplification */}
      <Section title="Risk Amplification" icon={Zap}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={ampData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="metric" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 7]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="amplification" name="Amplification (x)" fill={EMERALD} radius={[4, 4, 0, 0]} />
            <Bar dataKey="target" name="Target Range" fill="#e5e7eb" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <div className="flex gap-4 mt-2 text-[10px] text-gray-500">
          <span>Target amplifications: EL 4.3x | VaR 4.5x | ES 3.2x</span>
        </div>
      </Section>

      {/* Spectral radius gauge */}
      <Section title="Spectral Radius Gauge" icon={Gauge}>
        <div className="flex items-center gap-6">
          <div className="relative w-28 h-28">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
              <circle cx="50" cy="50" r="40" fill="none"
                stroke={isStable ? EMERALD : "#ef4444"}
                strokeWidth="8" strokeDasharray={`${Math.min(spectralRadius, 1.5) / 1.5 * 251} 251`}
                strokeLinecap="round" transform="rotate(-90 50 50)" />
              <text x="50" y="48" textAnchor="middle" fill="#111" fontSize="14" fontWeight="bold">{spectralRadius}</text>
              <text x="50" y="62" textAnchor="middle" fill="#9ca3af" fontSize="7">{isStable ? "rho < 1" : "rho >= 1"}</text>
            </svg>
          </div>
          <div className="text-xs text-gray-600 space-y-1">
            <p>Spectral radius (rho) measures the largest eigenvalue of the Hawkes branching matrix.</p>
            <p className={isStable ? "text-emerald-600 font-semibold" : "text-red-500 font-semibold"}>
              {isStable ? "System is sub-critical: shocks attenuate over time." : "System is super-critical: contagion will amplify."}
            </p>
          </div>
        </div>
      </Section>

      {/* Cascade simulation */}
      <Section title="Cascade Simulation" icon={Play}>
        <div className="grid grid-cols-3 gap-4 mb-3">
          <Row label="Seed Entity"><Sel value={seedEntity} onChange={setSeedEntity} options={ENTITIES} /></Row>
          <Row label="Severity (0-1)">
            <div className="flex items-center gap-2">
              <input type="range" min={0} max={1} step={0.05} value={severity}
                onChange={e => setSeverity(+e.target.value)}
                className="flex-1 accent-emerald-500" />
              <span className="text-xs font-mono w-8">{severity}</span>
            </div>
          </Row>
          <div className="flex items-end">
            <Btn onClick={handleSimulate}><Play className="h-3 w-3" />Simulate Cascade</Btn>
          </div>
        </div>
        <div className="flex gap-2">
          <Btn onClick={handleFetch} loading={loading} variant="secondary"><RefreshCw className="h-3 w-3" />Call API</Btn>
          {error && <p className="text-xs text-red-500 self-center">{error}</p>}
        </div>

        {simResult && (
          <div className="mt-4">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={simResult} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="step" tick={{ fontSize: 10 }} label={{ value: "Cascade Step", position: "bottom", fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="el_amplification" name="EL Amplification (x)" stroke={EMERALD} fill={EMERALD} fillOpacity={0.15} />
                <Area type="monotone" dataKey="entities" name="Entities Infected" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </Section>

      {result && (
        <Section title="API Response" icon={Info} defaultOpen={false}>
          <pre className="text-[10px] text-gray-600 bg-gray-50 rounded p-3 overflow-auto max-h-48">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}

/* ============================================================================
   TAB 4 -- DMI SCORING
============================================================================ */
function DMIScoringPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const rng = sr(404);

  /* Portfolio DMI score */
  const portfolioDMI = +(55 + rng() * 35).toFixed(1);
  const concentrationPenalty = +(rng() * 15).toFixed(2);
  const weightedPCAF = +(1.5 + rng() * 3).toFixed(2);
  const velocityAdj = +(rng() * 8 - 4).toFixed(2);

  /* Holdings scatter data */
  const holdings = [];
  for (let i = 0; i < 20; i++) {
    holdings.push({
      name: ENTITIES[i % ENTITIES.length].l.split(" ")[0] + (i >= ENTITIES.length ? ` ${i}` : ""),
      esg_score: +(20 + rng() * 70).toFixed(1),
      outstanding: +(5 + rng() * 200).toFixed(1),
      pcaf_quality: Math.min(5, Math.floor(rng() * 5) + 1),
    });
  }

  /* Concentration breakdown */
  const entityHHI = +(500 + rng() * 3000).toFixed(0);
  const sectorHHI = +(800 + rng() * 2500).toFixed(0);
  const geoHHI = +(600 + rng() * 2000).toFixed(0);
  const concData = [
    { dimension: "Entity HHI", hhi: +entityHHI, threshold: 2500 },
    { dimension: "Sector HHI", hhi: +sectorHHI, threshold: 2500 },
    { dimension: "Geographic HHI", hhi: +geoHHI, threshold: 2500 },
  ];

  /* PCAF quality distribution */
  const pcafDist = [1, 2, 3, 4, 5].map(q => ({
    name: `DQS ${q}`,
    value: Math.floor(rng() * 30) + 2,
  }));

  async function handleFetch() {
    setLoading(true); setError(null);
    try {
      const r = await axios.post(`${API_BASE}/api/v1/dme-dmi`, { portfolio_id: "pf-001" });
      setResult(r.data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Btn onClick={handleFetch} loading={loading}><RefreshCw className="h-3 w-3" />Compute DMI</Btn>
        {error && <p className="text-xs text-red-500 self-center">{error}</p>}
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Portfolio DMI" value={portfolioDMI} sub="0-100 composite" color={portfolioDMI >= 70 ? "text-emerald-600" : portfolioDMI >= 50 ? "text-amber-600" : "text-red-500"} />
        <KpiCard label="Concentration Penalty" value={`${concentrationPenalty}%`} sub="HHI-based deduction" color="text-amber-600" />
        <KpiCard label="Weighted PCAF" value={weightedPCAF} sub="Data quality score" color={weightedPCAF <= 2.5 ? "text-emerald-600" : "text-amber-600"} />
        <KpiCard label="Velocity Adj" value={velocityAdj > 0 ? `+${velocityAdj}` : String(velocityAdj)} sub="DME velocity overlay" color={velocityAdj > 0 ? "text-emerald-600" : "text-red-500"} />
      </div>

      {/* DMI Gauge */}
      <Section title="Portfolio DMI Score" icon={Gauge}>
        <div className="flex items-center gap-6">
          <div className="relative w-36 h-36">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" strokeWidth="6" />
              <circle cx="50" cy="50" r="42" fill="none"
                stroke={portfolioDMI >= 70 ? EMERALD : portfolioDMI >= 50 ? "#f59e0b" : "#ef4444"}
                strokeWidth="6" strokeDasharray={`${portfolioDMI * 2.64} 264`}
                strokeLinecap="round" transform="rotate(-90 50 50)" />
              <text x="50" y="46" textAnchor="middle" fill="#111" fontSize="18" fontWeight="bold">{portfolioDMI}</text>
              <text x="50" y="58" textAnchor="middle" fill="#9ca3af" fontSize="7">/ 100</text>
              <text x="50" y="68" textAnchor="middle" fill={portfolioDMI >= 70 ? EMERALD : "#f59e0b"} fontSize="7" fontWeight="600">
                {portfolioDMI >= 70 ? "STRONG" : portfolioDMI >= 50 ? "MODERATE" : "WEAK"}
              </text>
            </svg>
          </div>
          <div className="text-xs text-gray-600 space-y-1">
            <p>DMI integrates ESG quality, PCAF data scores, concentration risk, and velocity adjustments.</p>
            <p>Concentration penalty: <span className="font-mono font-semibold">{concentrationPenalty}%</span></p>
            <p>Velocity adjustment: <span className="font-mono font-semibold">{velocityAdj > 0 ? "+" : ""}{velocityAdj}</span></p>
          </div>
        </div>
      </Section>

      {/* Holdings scatter */}
      <Section title="Holdings Profile" icon={Eye}>
        <ResponsiveContainer width="100%" height={280}>
          <ScatterChart margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis type="number" dataKey="esg_score" name="ESG Score" tick={{ fontSize: 10 }}
              label={{ value: "ESG Score", position: "bottom", fontSize: 10 }} />
            <YAxis type="number" dataKey="outstanding" name="Outstanding (M)" tick={{ fontSize: 10 }}
              label={{ value: "Outstanding (M)", angle: -90, position: "insideLeft", fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ strokeDasharray: "3 3" }}
              formatter={(v, name) => [typeof v === "number" ? v.toFixed(1) : v, name]} />
            <Scatter data={holdings} name="Holdings">
              {holdings.map((h, i) => (
                <Cell key={i} fill={PCAF_COLORS[h.pcaf_quality - 1]} r={4 + h.pcaf_quality * 2} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
        <div className="flex gap-3 mt-2">
          {[1, 2, 3, 4, 5].map(q => (
            <div key={q} className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PCAF_COLORS[q - 1] }} />
              <span className="text-[10px] text-gray-500">DQS {q}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Concentration penalty breakdown */}
      <Section title="Concentration Penalty Breakdown" icon={Scale}>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={concData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="dimension" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 4000]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="hhi" name="HHI" fill={EMERALD} radius={[4, 4, 0, 0]}>
              {concData.map((c, i) => <Cell key={i} fill={c.hhi > c.threshold ? "#ef4444" : EMERALD} />)}
            </Bar>
            <ReferenceLine y={2500} stroke="#ef4444" strokeDasharray="3 3"
              label={{ value: "Concentrated (2500)", fontSize: 9, fill: "#ef4444" }} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* PCAF quality pie */}
      <Section title="PCAF Quality Distribution" icon={BarChart3}>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={pcafDist} dataKey="value" nameKey="name" cx="50%" cy="50%"
              outerRadius={80} innerRadius={40} paddingAngle={2}
              label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              labelLine={{ strokeWidth: 0.5 }}>
              {pcafDist.map((_, i) => <Cell key={i} fill={PCAF_COLORS[i]} />)}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </PieChart>
        </ResponsiveContainer>
      </Section>

      {result && (
        <Section title="API Response" icon={Info} defaultOpen={false}>
          <pre className="text-[10px] text-gray-600 bg-gray-50 rounded p-3 overflow-auto max-h-48">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}

/* ============================================================================
   TAB 5 -- GREENWASHING & NLP
============================================================================ */
function GreenwashingNLPPanel() {
  const [loading, setLoading] = useState(false);
  const [gwResult, setGwResult] = useState(null);
  const [nlpResult, setNlpResult] = useState(null);
  const [error, setError] = useState(null);

  const rng = sr(505);

  /* Divergence timeseries */
  const divergenceData = [];
  let cusum = 0;
  for (let i = 0; i < 24; i++) {
    const marketing = +(40 + rng() * 30 + Math.sin(i / 2) * 10).toFixed(1);
    const operational = +(30 + rng() * 20 + Math.cos(i / 3) * 8).toFixed(1);
    const gap = marketing - operational;
    cusum = Math.max(0, cusum + gap - 5);
    divergenceData.push({
      month: `2024-${String((i % 12) + 1).padStart(2, "0")}`,
      marketing: +marketing,
      operational: +operational,
      cusum: +cusum.toFixed(1),
    });
  }

  /* Detection conditions */
  const velocityOk = rng() > 0.4;
  const accelerationOk = rng() > 0.5;
  const zScoreOk = rng() > 0.3;
  const greenwashSeverity = velocityOk && accelerationOk ? "LOW" : zScoreOk ? "MODERATE" : "HIGH";
  const cusumAlert = cusum > 20;

  /* NLP Pulse data */
  const SOURCE_TIERS = ["Tier 1 (Reuters/Bloomberg)", "Tier 2 (Industry)", "Tier 3 (Social/Alt)", "Tier 4 (Regulatory)"];
  const nlpPulseData = SOURCE_TIERS.map(t => ({
    source: t.split(" (")[0],
    positive: +(rng() * 40).toFixed(1),
    neutral: +(20 + rng() * 30).toFixed(1),
    negative: +(rng() * 35).toFixed(1),
  }));

  const aggregatePulse = +(nlpPulseData.reduce((s, d) => s + d.positive - d.negative, 0) / nlpPulseData.length).toFixed(1);
  const avgCredibility = +(50 + rng() * 40).toFixed(1);

  /* Signal decay curve */
  const decayData = [];
  for (let d = 0; d <= 30; d++) {
    decayData.push({
      day: d,
      signal: +(100 * Math.exp(-d * 0.08) * (1 + rng() * 0.1 - 0.05)).toFixed(2),
    });
  }

  async function handleFetch() {
    setLoading(true); setError(null);
    try {
      const [gw, nlp] = await Promise.all([
        axios.post(`${API_BASE}/api/v1/dme-greenwashing`, { entity_id: "ent-001" }),
        axios.post(`${API_BASE}/api/v1/dme-nlp-pulse`, { entity_id: "ent-001" }),
      ]);
      setGwResult(gw.data);
      setNlpResult(nlp.data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Btn onClick={handleFetch} loading={loading}><Search className="h-3 w-3" />Analyse Greenwashing & NLP</Btn>
        {error && <p className="text-xs text-red-500 self-center">{error}</p>}
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Greenwash Severity" value={greenwashSeverity}
          sub={greenwashSeverity === "LOW" ? "No divergence detected" : "Review recommended"}
          color={greenwashSeverity === "LOW" ? "text-emerald-600" : greenwashSeverity === "MODERATE" ? "text-amber-600" : "text-red-500"} />
        <KpiCard label="CUSUM Alert" value={cusumAlert ? "TRIGGERED" : "CLEAR"}
          sub={`CUSUM = ${cusum.toFixed(1)}`}
          color={cusumAlert ? "text-red-500" : "text-emerald-600"} />
        <KpiCard label="Aggregate Pulse" value={aggregatePulse} sub="Net sentiment score" color={aggregatePulse > 0 ? "text-emerald-600" : "text-red-500"} />
        <KpiCard label="Avg Credibility" value={`${avgCredibility}%`} sub="Source-weighted" color={avgCredibility >= 60 ? "text-emerald-600" : "text-amber-600"} />
      </div>

      {/* Detection condition LEDs */}
      <Section title="Detection Conditions" icon={Radio}>
        <div className="flex gap-6">
          {[
            { label: "Velocity Signal", ok: velocityOk },
            { label: "Acceleration Signal", ok: accelerationOk },
            { label: "Z-Score Signal", ok: zScoreOk },
          ].map((c, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${c.ok ? "bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.6)]" : "bg-red-400 shadow-[0_0_6px_rgba(239,68,68,0.6)]"}`} />
              <span className="text-xs text-gray-600">{c.label}</span>
              <span className={`text-[10px] font-semibold ${c.ok ? "text-emerald-600" : "text-red-500"}`}>
                {c.ok ? "PASS" : "FAIL"}
              </span>
            </div>
          ))}
        </div>
      </Section>

      {/* Divergence timeseries */}
      <Section title="Marketing vs Operational Divergence" icon={Shield}>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={divergenceData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Area type="monotone" dataKey="marketing" name="Marketing Score" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.1} />
            <Area type="monotone" dataKey="operational" name="Operational Score" stroke={EMERALD} fill={EMERALD} fillOpacity={0.15} />
          </AreaChart>
        </ResponsiveContainer>
      </Section>

      {/* CUSUM chart */}
      <Section title="CUSUM Accumulation" icon={TrendingUp}>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={divergenceData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Line type="monotone" dataKey="cusum" name="CUSUM" stroke="#ef4444" strokeWidth={2} dot={false} />
            <ReferenceLine y={20} stroke="#ef4444" strokeDasharray="4 2"
              label={{ value: "Alert Threshold (20)", fontSize: 9, fill: "#ef4444" }} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      {/* NLP Pulse aggregate */}
      <Section title="NLP Pulse by Source Tier" icon={Globe}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={nlpPulseData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="source" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Bar dataKey="positive" name="Positive" stackId="s" fill={EMERALD} />
            <Bar dataKey="neutral" name="Neutral" stackId="s" fill="#94a3b8" />
            <Bar dataKey="negative" name="Negative" stackId="s" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Signal decay curve */}
      <Section title="Signal Decay Curve" icon={Activity}>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={decayData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="day" tick={{ fontSize: 10 }} label={{ value: "Days", position: "bottom", fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} label={{ value: "Signal %", angle: -90, position: "insideLeft", fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Area type="monotone" dataKey="signal" name="Signal Strength" stroke={EMERALD} fill={EMERALD} fillOpacity={0.15} />
          </AreaChart>
        </ResponsiveContainer>
        <p className="text-[10px] text-gray-400 mt-1">Exponential decay (lambda=0.08): half-life approx 8.7 days</p>
      </Section>

      {(gwResult || nlpResult) && (
        <Section title="API Response" icon={Info} defaultOpen={false}>
          <pre className="text-[10px] text-gray-600 bg-gray-50 rounded p-3 overflow-auto max-h-48">
            {JSON.stringify({ greenwashing: gwResult, nlp_pulse: nlpResult }, null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}

/* ============================================================================
   TAB 6 -- POLICY VELOCITY
============================================================================ */
function PolicyVelocityPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const rng = sr(606);

  /* Composite velocity */
  const carbonPriceVel = +(20 + rng() * 60).toFixed(1);
  const regulatoryVel = +(15 + rng() * 55).toFixed(1);
  const enforcementVel = +(10 + rng() * 50).toFixed(1);
  const disclosureVel = +(25 + rng() * 50).toFixed(1);
  const compositeVel = +((carbonPriceVel * 0.3 + regulatoryVel * 0.25 + enforcementVel * 0.2 + disclosureVel * 0.25)).toFixed(1);

  const componentData = [
    { component: "Carbon Price", velocity: carbonPriceVel, weight: "30%", fill: EMERALD },
    { component: "Regulatory Pipeline", velocity: regulatoryVel, weight: "25%", fill: "#3b82f6" },
    { component: "Enforcement", velocity: enforcementVel, weight: "20%", fill: "#f59e0b" },
    { component: "Disclosure", velocity: disclosureVel, weight: "25%", fill: "#8b5cf6" },
  ];

  /* Sector weight radar */
  const sectorRadar = SECTORS.map(s => ({
    sector: s,
    exposure: +(rng() * 80 + 10).toFixed(1),
    velocity: +(rng() * 60 + 20).toFixed(1),
  }));

  /* Jurisdiction comparison */
  const jurisdictionData = JURISDICTIONS.map(j => ({
    jurisdiction: j,
    composite: +(20 + rng() * 70).toFixed(1),
    carbon_price: +(rng() * 80).toFixed(1),
    regulatory: +(rng() * 70).toFixed(1),
    enforcement: +(rng() * 60).toFixed(1),
    disclosure: +(rng() * 75).toFixed(1),
    trend: rng() > 0.5 ? "Accelerating" : "Decelerating",
  }));

  async function handleFetch() {
    setLoading(true); setError(null);
    try {
      const r = await axios.get(`${API_BASE}/api/v1/dme-policy-tracker`);
      setResult(r.data);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Btn onClick={handleFetch} loading={loading}><RefreshCw className="h-3 w-3" />Refresh Policy Data</Btn>
        {error && <p className="text-xs text-red-500 self-center">{error}</p>}
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Composite Velocity" value={compositeVel} sub="Weighted 4-component" color={compositeVel > 50 ? "text-red-500" : "text-emerald-600"} />
        <KpiCard label="Carbon Price Vel" value={carbonPriceVel} sub="30% weight" color="text-gray-900" />
        <KpiCard label="Enforcement Vel" value={enforcementVel} sub="20% weight" color="text-gray-900" />
        <KpiCard label="Disclosure Vel" value={disclosureVel} sub="25% weight" color="text-gray-900" />
      </div>

      {/* Composite velocity gauge */}
      <Section title="Composite Policy Velocity" icon={Gauge}>
        <div className="flex items-center gap-6">
          <div className="relative w-36 h-36">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" strokeWidth="6" />
              <circle cx="50" cy="50" r="42" fill="none"
                stroke={compositeVel <= 35 ? EMERALD : compositeVel <= 60 ? "#f59e0b" : "#ef4444"}
                strokeWidth="6" strokeDasharray={`${compositeVel * 2.64} 264`}
                strokeLinecap="round" transform="rotate(-90 50 50)" />
              <text x="50" y="46" textAnchor="middle" fill="#111" fontSize="18" fontWeight="bold">{compositeVel}</text>
              <text x="50" y="58" textAnchor="middle" fill="#9ca3af" fontSize="7">/ 100</text>
              <text x="50" y="68" textAnchor="middle"
                fill={compositeVel <= 35 ? EMERALD : compositeVel <= 60 ? "#f59e0b" : "#ef4444"}
                fontSize="7" fontWeight="600">
                {compositeVel <= 35 ? "LOW" : compositeVel <= 60 ? "MODERATE" : "HIGH"}
              </text>
            </svg>
          </div>
          <div className="text-xs text-gray-600 space-y-1">
            <p>Composite = Carbon Price (30%) + Regulatory Pipeline (25%) + Enforcement (20%) + Disclosure (25%)</p>
            <p>Higher velocity indicates faster regulatory change, requiring accelerated compliance.</p>
          </div>
        </div>
      </Section>

      {/* Component breakdown */}
      <Section title="4-Component Breakdown" icon={BarChart3}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={componentData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="component" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE}
              formatter={(v, name, props) => [`${v} (weight: ${props.payload.weight})`, name]} />
            <Bar dataKey="velocity" name="Velocity" radius={[4, 4, 0, 0]}>
              {componentData.map((c, i) => <Cell key={i} fill={c.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Sector weight radar */}
      <Section title="Sector Exposure vs Velocity" icon={Target}>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={sectorRadar}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="sector" tick={{ fontSize: 9 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 8 }} />
            <Radar name="Exposure" dataKey="exposure" stroke={EMERALD} fill={EMERALD} fillOpacity={0.15} />
            <Radar name="Policy Velocity" dataKey="velocity" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.1} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </RadarChart>
        </ResponsiveContainer>
      </Section>

      {/* Jurisdiction comparison table */}
      <Section title="Jurisdiction Comparison" icon={Globe}>
        <div className="overflow-auto max-h-72">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500 text-left">
                <th className="py-2 px-2 font-medium">Jurisdiction</th>
                <th className="py-2 px-2 font-medium">Composite</th>
                <th className="py-2 px-2 font-medium">Carbon Price</th>
                <th className="py-2 px-2 font-medium">Regulatory</th>
                <th className="py-2 px-2 font-medium">Enforcement</th>
                <th className="py-2 px-2 font-medium">Disclosure</th>
                <th className="py-2 px-2 font-medium">Trend</th>
              </tr>
            </thead>
            <tbody>
              {jurisdictionData.sort((a, b) => b.composite - a.composite).map((j, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-1.5 px-2 font-semibold">{j.jurisdiction}</td>
                  <td className="py-1.5 px-2 font-mono">
                    <span className={j.composite > 60 ? "text-red-500" : j.composite > 35 ? "text-amber-600" : "text-emerald-600"}>
                      {j.composite}
                    </span>
                  </td>
                  <td className="py-1.5 px-2 font-mono text-gray-600">{j.carbon_price}</td>
                  <td className="py-1.5 px-2 font-mono text-gray-600">{j.regulatory}</td>
                  <td className="py-1.5 px-2 font-mono text-gray-600">{j.enforcement}</td>
                  <td className="py-1.5 px-2 font-mono text-gray-600">{j.disclosure}</td>
                  <td className="py-1.5 px-2">
                    <span className={`text-[10px] font-semibold ${j.trend === "Accelerating" ? "text-red-500" : "text-emerald-600"}`}>
                      {j.trend === "Accelerating" ? "Accel" : "Decel"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {result && (
        <Section title="API Response" icon={Info} defaultOpen={false}>
          <pre className="text-[10px] text-gray-600 bg-gray-50 rounded p-3 overflow-auto max-h-48">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}

/* ============================================================================
   TABS + MAIN COMPONENT
============================================================================ */
const TABS = [
  { id: "velocity", label: "Velocity Monitor", icon: Activity },
  { id: "alerts", label: "Alert Dashboard", icon: AlertTriangle },
  { id: "contagion", label: "Contagion Network", icon: Network },
  { id: "dmi", label: "DMI Scoring", icon: BarChart3 },
  { id: "greenwashing", label: "Greenwashing & NLP", icon: Shield },
  { id: "policy", label: "Policy Velocity", icon: ScrollText },
];

export default function DMEDashboardPage() {
  const [tab, setTab] = useState("velocity");

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">DME Dashboard</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Dynamic Materiality Engine -- Velocity monitoring, alert triage, contagion analysis, materiality scoring, greenwashing detection, policy tracking
          </p>
        </div>
        <div className="flex gap-1.5">
          {["DME v2", "Hawkes", "PCAF", "CUSUM", "NLP"].map(b => (
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
      {tab === "velocity" && <VelocityMonitorPanel />}
      {tab === "alerts" && <AlertDashboardPanel />}
      {tab === "contagion" && <ContagionNetworkPanel />}
      {tab === "dmi" && <DMIScoringPanel />}
      {tab === "greenwashing" && <GreenwashingNLPPanel />}
      {tab === "policy" && <PolicyVelocityPanel />}

      {/* Footer */}
      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Velocity Monitor:</span> Regime detection via Markov-switching z-score thresholds (NORMAL &lt; 1.5, ELEVATED &lt; 2.5, CRITICAL &lt; 3.5, EXTREME &ge; 3.5)</p>
        <p><span className="font-semibold text-gray-500">Alerts:</span> 4-tier alert system (WATCH/ELEVATED/CRITICAL/EXTREME) with SLA-driven triage (4h/8h/24h/72h)</p>
        <p><span className="font-semibold text-gray-500">Contagion:</span> Hawkes process branching matrix; spectral radius &rho; &lt; 1 = sub-critical (stable); cascade simulation via Ogata thinning</p>
        <p><span className="font-semibold text-gray-500">DMI:</span> Dynamic Materiality Index = ESG quality &times; PCAF DQS weighting &minus; concentration penalty (entity/sector/geo HHI) &plusmn; velocity adjustment</p>
        <p><span className="font-semibold text-gray-500">Greenwashing:</span> CUSUM sequential detection on marketing-vs-operational divergence; 3-signal LED (velocity, acceleration, z-score)</p>
        <p><span className="font-semibold text-gray-500">Policy Velocity:</span> Composite = Carbon Price (30%) + Regulatory Pipeline (25%) + Enforcement (20%) + Disclosure (25%); multi-jurisdiction tracking</p>
      </div>
    </div>
  );
}
