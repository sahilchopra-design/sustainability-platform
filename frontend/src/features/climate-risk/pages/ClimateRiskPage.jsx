/**
 * Climate Risk Engine — Physical / Transition / Integrated Assessment
 *
 * Standards: EBA GL/2025/01 (ESG Risk Management), TCFD, NGFS Phase 5,
 *            ISSB S2, CSRD ESRS E1, EBA Pillar 3 ESG disclosures
 *
 * Tabs:
 *  1. Physical Risk    — HEV framework, acute + chronic hazards, CVaR
 *  2. Transition Risk  — NACE/CPRS, carbon pricing, stranded assets, NGFS
 *  3. Integrated View  — Combined score, nature amplifier, TCFD breakdown
 *  4. Methodology Mgr  — Template library, lifecycle, config editor
 *  5. Assessment Runner— Batch runs, portfolio aggregate, delta reports
 *  6. Regulatory       — TCFD / EBA Pillar 3 / ISSB S2 / CSRD ESRS E1
 */
import React, { useState, useCallback, useEffect } from "react";
import { usePersonaDefaults } from '../../../context/PersonaContext';
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar, LineChart, Line
} from "recharts";
import {
  Thermometer, Wind, Droplets, Flame, AlertTriangle, CheckCircle,
  RefreshCw, ChevronDown, ChevronUp, Play, Plus, Trash2, Copy,
  FileText, Settings, List, Activity, TrendingUp, TrendingDown,
  Zap, Globe, Shield, BookOpen, Info
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt2 = (v) => v == null ? "—" : Number(v).toFixed(2);
const fmt0 = (v) => v == null ? "—" : Number(v).toFixed(0);
const fmtM = (v) => {
  if (v == null) return "—";
  if (Math.abs(v) >= 1e9) return `€${(v / 1e9).toFixed(2)}bn`;
  if (Math.abs(v) >= 1e6) return `€${(v / 1e6).toFixed(2)}m`;
  if (Math.abs(v) >= 1e3) return `€${(v / 1e3).toFixed(1)}k`;
  return `€${v.toFixed(0)}`;
};

const SCENARIOS = ["net_zero_2050", "below_2c", "divergent_nz", "delayed_transition", "ndcs", "current_policies"];
const SCENARIO_LABELS = {
  net_zero_2050: "Net Zero 2050", below_2c: "Below 2°C", divergent_nz: "Divergent NZ",
  delayed_transition: "Delayed Transition", ndcs: "NDCs", current_policies: "Current Policies"
};
const HORIZONS = [5, 10, 20, 30];
const NACE_SECTORS = [
  "A01", "A02", "B05", "C10", "C20", "C24", "C29", "D35", "E36",
  "F41", "G46", "H49", "H51", "I55", "J62", "K64", "L68", "M71", "N77"
];
const SCORE_COLOR = (v) => {
  if (v == null) return "#6b7280";
  if (v >= 75) return "#ef4444";
  if (v >= 50) return "#f59e0b";
  if (v >= 25) return "#eab308";
  return "#10b981";
};

// ── Shared UI ─────────────────────────────────────────────────────────────────

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

function ScoreBar({ label, value, max = 100 }) {
  const pct = Math.min(100, (value / max) * 100);
  const col = SCORE_COLOR(value);
  return (
    <div className="flex items-center gap-2 mb-1.5">
      <span className="text-[11px] text-gray-500 w-36 truncate shrink-0">{label}</span>
      <div className="flex-1 bg-gray-50 rounded-full h-1.5 overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: col }} />
      </div>
      <span className="text-[11px] font-mono text-gray-600 w-8 text-right">{fmt0(value)}</span>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    running: "bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse",
    completed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    failed: "bg-red-500/10 text-red-400 border-red-500/20",
    cancelled: "bg-gray-50 text-gray-500 border-black/10",
    DRAFT: "bg-gray-50 text-gray-500 border-black/10",
    PUBLISHED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    RETIRED: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    ARCHIVED: "bg-gray-50 text-gray-400 border-black/10",
  };
  return (
    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${map[status] || map.DRAFT}`}>
      {status}
    </span>
  );
}

function ErrBox({ msg }) {
  if (!msg) return null;
  return (
    <div className="bg-red-500/10 border border-red-500/20 rounded p-3 text-[11px] text-red-400 mb-3 flex items-start gap-2">
      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
      {msg}
    </div>
  );
}

function Spinner() {
  return <div className="w-4 h-4 border-2 border-gray-300 border-t-cyan-400 rounded-full animate-spin" />;
}

function InputRow({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <label className="text-[11px] text-gray-500 w-36 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Input({ value, onChange, type = "text", placeholder, className = "" }) {
  return (
    <input
      type={type} value={value} onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className={`w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800 placeholder-gray-400
        focus:outline-none focus:border-blue-500 ${className}`}
    />
  );
}

function Select({ value, onChange, options, className = "" }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className={`w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800
        focus:outline-none focus:border-blue-500 ${className}`}>
      {options.map(o => (
        <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>
      ))}
    </select>
  );
}

function Btn({ onClick, disabled, children, variant = "primary", size = "sm" }) {
  const base = "flex items-center gap-1.5 rounded font-medium transition-all focus:outline-none";
  const sz = size === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";
  const v = {
    primary: "bg-gray-200 text-gray-800 border border-gray-300 hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed",
    secondary: "bg-gray-50 text-gray-500 border border-black/10 hover:bg-white/8 hover:text-gray-700",
    danger: "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20",
  };
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${sz} ${v[variant]}`}>
      {children}
    </button>
  );
}

// ── Tab 1: Physical Risk Assessment ──────────────────────────────────────────

const DEFAULT_PHYSICAL = {
  entity_id: "ENT-001", entity_name: "Demo Asset", entity_type: "asset",
  sector_nace: "D35", latitude: 51.5, longitude: -0.12,
  asset_value_eur: 50000000, flood_zone: false,
  scenario: "net_zero_2050", time_horizon: 10,
};

const HAZARD_COLORS = {
  riverine_flood: "#3b82f6", coastal_flood: "#06b6d4", tropical_cyclone: "#8b5cf6",
  extreme_heat: "#f97316", wildfire: "#ef4444", drought: "#eab308",
  sea_level_rise: "#22d3ee", extreme_precipitation: "#6366f1",
};

function PhysicalRiskTab() {
  const d = usePersonaDefaults('climate_risk');
  const [form, setForm] = useState({
    ...DEFAULT_PHYSICAL,
    ...(d.entity_id ? {
      entity_id: d.entity_id,
      entity_name: d.entity_name || DEFAULT_PHYSICAL.entity_name,
      entity_type: d.entity_type || DEFAULT_PHYSICAL.entity_type,
      sector_nace: d.sector_nace || DEFAULT_PHYSICAL.sector_nace,
      latitude: d.latitude !== undefined ? d.latitude : DEFAULT_PHYSICAL.latitude,
      longitude: d.longitude !== undefined ? d.longitude : DEFAULT_PHYSICAL.longitude,
      asset_value_eur: d.asset_value_eur || DEFAULT_PHYSICAL.asset_value_eur,
      flood_zone: d.flood_zone !== undefined ? d.flood_zone : DEFAULT_PHYSICAL.flood_zone,
      scenario: d.scenario || DEFAULT_PHYSICAL.scenario,
      time_horizon: d.time_horizon || DEFAULT_PHYSICAL.time_horizon,
    } : {}),
  });
  useEffect(() => {
    if (d.entity_id) setForm(p => ({
      ...p,
      entity_id: d.entity_id,
      entity_name: d.entity_name || p.entity_name,
      sector_nace: d.sector_nace || p.sector_nace,
      latitude: d.latitude !== undefined ? d.latitude : p.latitude,
      longitude: d.longitude !== undefined ? d.longitude : p.longitude,
      asset_value_eur: d.asset_value_eur || p.asset_value_eur,
      scenario: d.scenario || p.scenario,
    }));
  }, [d.entity_id]); // eslint-disable-line
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (v) => setForm(p => ({ ...p, [k]: v }));

  const run = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/climate-risk/physical/assess`, {
        entities: [{ ...form, asset_value_eur: +form.asset_value_eur, latitude: +form.latitude, longitude: +form.longitude }],
        scenarios: [form.scenario],
        time_horizons: [+form.time_horizon],
      });
      setResult(data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  const hazardBars = result?.results?.[0]?.hazard_scores
    ? Object.entries(result.results[0].hazard_scores).map(([k, v]) => ({
        name: k.replace(/_/g, " "), score: +(v.hazard_score ?? 0).toFixed(1),
        fill: HAZARD_COLORS[k] || "#6366f1"
      }))
    : [];

  const r0 = result?.results?.[0];

  return (
    <div>
      <Section title="Entity & Location" defaultOpen accent="bg-blue-500">
        <div className="grid grid-cols-2 gap-x-6">
          <InputRow label="Entity ID"><Input value={form.entity_id} onChange={set("entity_id")} /></InputRow>
          <InputRow label="Entity Name"><Input value={form.entity_name} onChange={set("entity_name")} /></InputRow>
          <InputRow label="NACE Sector">
            <Select value={form.sector_nace} onChange={set("sector_nace")} options={NACE_SECTORS} />
          </InputRow>
          <InputRow label="Entity Type">
            <Select value={form.entity_type} onChange={set("entity_type")}
              options={["asset", "security", "fund", "portfolio", "counterparty"]} />
          </InputRow>
          <InputRow label="Latitude"><Input type="number" value={form.latitude} onChange={set("latitude")} /></InputRow>
          <InputRow label="Longitude"><Input type="number" value={form.longitude} onChange={set("longitude")} /></InputRow>
          <InputRow label="Asset Value (EUR)"><Input type="number" value={form.asset_value_eur} onChange={set("asset_value_eur")} /></InputRow>
        </div>
      </Section>

      <Section title="Assessment Parameters" defaultOpen accent="bg-blue-600">
        <div className="grid grid-cols-2 gap-x-6">
          <InputRow label="Scenario">
            <Select value={form.scenario} onChange={set("scenario")}
              options={SCENARIOS.map(s => ({ value: s, label: SCENARIO_LABELS[s] }))} />
          </InputRow>
          <InputRow label="Time Horizon (yrs)">
            <Select value={form.time_horizon} onChange={set("time_horizon")}
              options={HORIZONS.map(h => ({ value: h, label: `${h} years` }))} />
          </InputRow>
        </div>
        <div className="flex justify-end mt-2">
          <Btn onClick={run} disabled={loading}>
            {loading ? <Spinner /> : <Play className="h-3.5 w-3.5" />}
            {loading ? "Running…" : "Run Physical Assessment"}
          </Btn>
        </div>
      </Section>

      <ErrBox msg={error} />

      {r0 && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <KpiCard label="Composite Physical" value={fmt2(r0.composite_score)} sub="0–100 scale"
              color={`font-mono text-xl`} />
            <KpiCard label="Acute Score" value={fmt2(r0.acute_score)} sub="Flood / Cyclone / Fire" />
            <KpiCard label="Chronic Score" value={fmt2(r0.chronic_score)} sub="Heat / Sea-level / Drought" />
            <KpiCard label="CVaR (95%)" value={fmtM(r0.cvar_eur)} sub="Expected tail loss" />
          </div>

          {hazardBars.length > 0 && (
            <Section title="Hazard-Level Decomposition" defaultOpen={false}>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={hazardBars} margin={{ top: 4, right: 8, bottom: 24, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#ffffff40" }} angle={-30} textAnchor="end" />
                  <YAxis tick={{ fontSize: 9, fill: "#ffffff40" }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #ffffff10", fontSize: 11 }} />
                  <Bar dataKey="score" radius={[3, 3, 0, 0]}>
                    {hazardBars.map((e, i) => <Cell key={i} fill={e.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          <Section title="Hazard Scores (detail)" defaultOpen={false}>
            {Object.entries(r0.hazard_scores || {}).map(([k, v]) => (
              <ScoreBar key={k} label={k.replace(/_/g, " ")} value={v.hazard_score ?? 0} />
            ))}
          </Section>
        </>
      )}
    </div>
  );
}

// ── Tab 2: Transition Risk Assessment ────────────────────────────────────────

const DEFAULT_TRANSITION = {
  entity_id: "ENT-001", entity_name: "Demo Entity", entity_type: "asset",
  sector_nace: "D35", annual_revenue_eur: 100000000, carbon_intensity_tco2_eur: 0.25,
  capex_green_pct: 15, scenario: "net_zero_2050", time_horizon: 10,
};

const TCFD_CATS = ["policy_legal", "technology", "market", "reputation"];
const TCFD_COLORS = { policy_legal: "#ef4444", technology: "#3b82f6", market: "#f59e0b", reputation: "#8b5cf6" };

function TransitionRiskTab() {
  const d = usePersonaDefaults('climate_risk');
  const [form, setForm] = useState({
    ...DEFAULT_TRANSITION,
    ...(d.entity_id ? {
      entity_id: d.entity_id,
      entity_name: d.entity_name || DEFAULT_TRANSITION.entity_name,
      entity_type: d.entity_type || DEFAULT_TRANSITION.entity_type,
      sector_nace: d.sector_nace || DEFAULT_TRANSITION.sector_nace,
      annual_revenue_eur: d.annual_revenue_eur || DEFAULT_TRANSITION.annual_revenue_eur,
      carbon_intensity_tco2_eur: d.carbon_intensity_tco2_eur || DEFAULT_TRANSITION.carbon_intensity_tco2_eur,
      capex_green_pct: d.capex_green_pct || DEFAULT_TRANSITION.capex_green_pct,
      scenario: d.scenario || DEFAULT_TRANSITION.scenario,
      time_horizon: d.time_horizon || DEFAULT_TRANSITION.time_horizon,
    } : {}),
  });
  useEffect(() => {
    if (d.entity_id) setForm(p => ({
      ...p,
      entity_id: d.entity_id,
      entity_name: d.entity_name || p.entity_name,
      sector_nace: d.sector_nace || p.sector_nace,
      annual_revenue_eur: d.annual_revenue_eur || p.annual_revenue_eur,
      carbon_intensity_tco2_eur: d.carbon_intensity_tco2_eur || p.carbon_intensity_tco2_eur,
      capex_green_pct: d.capex_green_pct || p.capex_green_pct,
      scenario: d.scenario || p.scenario,
    }));
  }, [d.entity_id]); // eslint-disable-line
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (v) => setForm(p => ({ ...p, [k]: v }));

  const run = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/climate-risk/transition/assess`, {
        entities: [{
          ...form,
          annual_revenue_eur: +form.annual_revenue_eur,
          carbon_intensity_tco2_eur: +form.carbon_intensity_tco2_eur,
          capex_green_pct: +form.capex_green_pct,
        }],
        scenarios: [form.scenario],
        time_horizons: [+form.time_horizon],
      });
      setResult(data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  const r0 = result?.results?.[0];

  const radarData = TCFD_CATS.map(cat => ({
    category: cat.replace("_", " "),
    score: +(r0?.tcfd_scores?.[cat] ?? 0).toFixed(1),
    fullMark: 100,
  }));

  return (
    <div>
      <Section title="Entity Details" defaultOpen accent="bg-orange-500">
        <div className="grid grid-cols-2 gap-x-6">
          <InputRow label="Entity ID"><Input value={form.entity_id} onChange={set("entity_id")} /></InputRow>
          <InputRow label="Entity Name"><Input value={form.entity_name} onChange={set("entity_name")} /></InputRow>
          <InputRow label="NACE Sector">
            <Select value={form.sector_nace} onChange={set("sector_nace")} options={NACE_SECTORS} />
          </InputRow>
          <InputRow label="Entity Type">
            <Select value={form.entity_type} onChange={set("entity_type")}
              options={["asset", "security", "fund", "portfolio", "counterparty"]} />
          </InputRow>
          <InputRow label="Annual Revenue (EUR)"><Input type="number" value={form.annual_revenue_eur} onChange={set("annual_revenue_eur")} /></InputRow>
          <InputRow label="Carbon Intensity (tCO₂/€)"><Input type="number" value={form.carbon_intensity_tco2_eur} onChange={set("carbon_intensity_tco2_eur")} step="0.01" /></InputRow>
          <InputRow label="Green CapEx (%)"><Input type="number" value={form.capex_green_pct} onChange={set("capex_green_pct")} /></InputRow>
        </div>
      </Section>

      <Section title="Scenario Parameters" defaultOpen accent="bg-amber-500">
        <div className="grid grid-cols-2 gap-x-6">
          <InputRow label="Scenario">
            <Select value={form.scenario} onChange={set("scenario")}
              options={SCENARIOS.map(s => ({ value: s, label: SCENARIO_LABELS[s] }))} />
          </InputRow>
          <InputRow label="Time Horizon (yrs)">
            <Select value={form.time_horizon} onChange={set("time_horizon")}
              options={HORIZONS.map(h => ({ value: h, label: `${h} years` }))} />
          </InputRow>
        </div>
        <div className="flex justify-end mt-2">
          <Btn onClick={run} disabled={loading}>
            {loading ? <Spinner /> : <Play className="h-3.5 w-3.5" />}
            {loading ? "Running…" : "Run Transition Assessment"}
          </Btn>
        </div>
      </Section>

      <ErrBox msg={error} />

      {r0 && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <KpiCard label="Composite Transition" value={fmt2(r0.composite_score)} sub="0–100 scale" />
            <KpiCard label="CPRS Category" value={r0.sector_classification || "—"} sub="NACE→CPRS mapping" />
            <KpiCard label="Carbon Cost" value={fmtM(r0.carbon_cost_eur)} sub="Forward scenario" />
            <KpiCard label="Alignment Gap" value={r0.alignment_gap_pct != null ? `${fmt2(r0.alignment_gap_pct)}%` : "—"} sub="vs. Paris target" />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <Section title="TCFD Risk Radar" defaultOpen>
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#ffffff0a" />
                  <PolarAngleAxis dataKey="category" tick={{ fontSize: 9, fill: "#ffffff50" }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 8, fill: "#ffffff30" }} />
                  <Radar name="Score" dataKey="score" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} />
                </RadarChart>
              </ResponsiveContainer>
            </Section>

            <Section title="TCFD Category Scores" defaultOpen>
              {TCFD_CATS.map(cat => (
                <ScoreBar key={cat} label={cat.replace("_", " ")} value={r0.tcfd_scores?.[cat] ?? 0} />
              ))}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <ScoreBar label="Stranded Asset Risk" value={r0.stranded_asset_score ?? 0} />
                <ScoreBar label="Scenario Stress Score" value={r0.scenario_stress_score ?? 0} />
              </div>
            </Section>
          </div>
        </>
      )}
    </div>
  );
}

// ── Tab 3: Integrated Risk View ───────────────────────────────────────────────

function IntegratedRiskTab() {
  const [physScore, setPhysScore] = useState("32.5");
  const [transScore, setTransScore] = useState("45.0");
  const [sector, setSector] = useState("D35");
  const [scenario, setScenario] = useState("net_zero_2050");
  const [horizon, setHorizon] = useState(10);
  const [methodId, setMethodId] = useState("");
  const [methods, setMethods] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/climate-risk/methodologies?status=PUBLISHED`)
      .then(({ data }) => setMethods(data.items || []))
      .catch(() => {});
  }, []);

  const run = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/climate-risk/integrated/assess`, {
        entities: [{
          entity_id: "ENT-001", entity_type: "asset",
          sector_nace: sector,
          physical_score: +physScore, transition_score: +transScore,
        }],
        scenarios: [scenario],
        time_horizons: [+horizon],
        methodology_id: methodId || undefined,
      });
      setResult(data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  const r0 = result?.results?.[0];
  const breakdownBars = r0 ? [
    { name: "Physical", score: +(r0.physical_contribution ?? 0).toFixed(1), fill: "#3b82f6" },
    { name: "Transition", score: +(r0.transition_contribution ?? 0).toFixed(1), fill: "#f59e0b" },
    { name: "Nature Amp.", score: +(r0.nature_amplifier_delta ?? 0).toFixed(1), fill: "#10b981" },
  ] : [];

  return (
    <div>
      <Section title="Score Inputs" defaultOpen accent="bg-emerald-500">
        <div className="grid grid-cols-2 gap-x-6">
          <InputRow label="Physical Score (0–100)"><Input type="number" value={physScore} onChange={setPhysScore} /></InputRow>
          <InputRow label="Transition Score (0–100)"><Input type="number" value={transScore} onChange={setTransScore} /></InputRow>
          <InputRow label="NACE Sector">
            <Select value={sector} onChange={setSector} options={NACE_SECTORS} />
          </InputRow>
          <InputRow label="Methodology">
            <Select value={methodId} onChange={setMethodId}
              options={[{ value: "", label: "— Default —" }, ...methods.map(m => ({ value: m.id, label: m.name }))]} />
          </InputRow>
          <InputRow label="Scenario">
            <Select value={scenario} onChange={setScenario}
              options={SCENARIOS.map(s => ({ value: s, label: SCENARIO_LABELS[s] }))} />
          </InputRow>
          <InputRow label="Time Horizon (yrs)">
            <Select value={horizon} onChange={v => setHorizon(+v)}
              options={HORIZONS.map(h => ({ value: h, label: `${h} years` }))} />
          </InputRow>
        </div>
        <div className="flex justify-end mt-2">
          <Btn onClick={run} disabled={loading}>
            {loading ? <Spinner /> : <Activity className="h-3.5 w-3.5" />}
            {loading ? "Integrating…" : "Compute Integrated Score"}
          </Btn>
        </div>
      </Section>

      <ErrBox msg={error} />

      {r0 && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <KpiCard label="Integrated Score" value={fmt2(r0.integrated_score)} sub="Composite 0–100" />
            <KpiCard label="Risk Category" value={r0.risk_category || "—"} sub="LOW / MEDIUM / HIGH / CRITICAL" />
            <KpiCard label="Nature Amplifier" value={r0.nature_amplifier != null ? `×${fmt2(r0.nature_amplifier)}` : "—"}
              sub="ENCORE biodiversity factor" color="text-emerald-300" />
            <KpiCard label="Scenario" value={SCENARIO_LABELS[scenario] || scenario} sub={`${horizon}yr horizon`} />
          </div>

          <Section title="Score Decomposition" defaultOpen>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={breakdownBars} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 9, fill: "#ffffff40" }} domain={[0, 100]} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#ffffff50" }} />
                <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #ffffff10", fontSize: 11 }} />
                <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                  {breakdownBars.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Section>

          {r0.recommendations?.length > 0 && (
            <Section title="Recommendations" defaultOpen={false}>
              {r0.recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-2 mb-2 text-[11px] text-gray-600">
                  <CheckCircle className="h-3.5 w-3.5 text-gray-700 shrink-0 mt-0.5" />
                  {rec}
                </div>
              ))}
            </Section>
          )}
        </>
      )}
    </div>
  );
}

// ── Tab 4: Methodology Manager ────────────────────────────────────────────────

function MethodologyTab() {
  const [methods, setMethods] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [mRes, tRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/climate-risk/methodologies`),
        axios.get(`${API_BASE}/api/v1/climate-risk/templates`),
      ]);
      setMethods(mRes.data.items || []);
      setTemplates(tRes.data || []);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const lifecycle = async (action, id) => {
    setActionMsg(null);
    try {
      await axios.post(`${API_BASE}/api/v1/climate-risk/methodologies/${id}/${action}`);
      setActionMsg(`${action} successful`);
      load();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    }
  };

  const cloneFromTemplate = async (templateName) => {
    try {
      await axios.post(`${API_BASE}/api/v1/climate-risk/methodologies/from-template`, { template_name: templateName, name: `Copy of ${templateName}` });
      setActionMsg("Created from template");
      load();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    }
  };

  return (
    <div>
      <ErrBox msg={error} />
      {actionMsg && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded p-3 text-[11px] text-emerald-400 mb-3 flex items-center gap-2">
          <CheckCircle className="h-3.5 w-3.5" />{actionMsg}
        </div>
      )}

      <Section title={`Methodology Library (${methods.length})`} defaultOpen accent="bg-violet-500">
        <div className="flex justify-between items-center mb-3">
          <span className="text-[10px] text-gray-500">EBA GL/2025/01 — lifecycle: DRAFT → PUBLISHED → RETIRED → ARCHIVED</span>
          <Btn onClick={load} variant="secondary" disabled={loading}>
            {loading ? <Spinner /> : <RefreshCw className="h-3.5 w-3.5" />} Refresh
          </Btn>
        </div>

        {methods.length === 0 && !loading && (
          <p className="text-[11px] text-gray-400 py-4 text-center">No methodologies yet — create from a template below</p>
        )}

        <div className="space-y-2">
          {methods.map(m => (
            <div key={m.id}
              onClick={() => setSelected(selected?.id === m.id ? null : m)}
              className={`border rounded-lg p-3 cursor-pointer transition-all ${selected?.id === m.id ? 'border-gray-300 bg-gray-50' : 'border-gray-200 hover:border-black/10'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Settings className="h-3.5 w-3.5 text-gray-500" />
                  <span className="text-xs font-medium text-gray-700">{m.name}</span>
                  <StatusBadge status={m.status} />
                  <span className="text-[9px] text-gray-400 font-mono">v{m.version}</span>
                </div>
                <div className="flex items-center gap-1">
                  {m.status === "DRAFT" && (
                    <Btn onClick={e => { e.stopPropagation(); lifecycle("publish", m.id); }} size="sm" variant="primary">
                      <CheckCircle className="h-3 w-3" /> Publish
                    </Btn>
                  )}
                  {m.status === "PUBLISHED" && (
                    <Btn onClick={e => { e.stopPropagation(); lifecycle("retire", m.id); }} size="sm" variant="secondary">
                      Retire
                    </Btn>
                  )}
                  <Btn onClick={e => { e.stopPropagation(); lifecycle("clone", m.id); }} size="sm" variant="secondary">
                    <Copy className="h-3 w-3" /> Clone
                  </Btn>
                </div>
              </div>
              {selected?.id === m.id && (
                <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-3 gap-3 text-[10px]">
                  <div><span className="text-gray-500">ID: </span><span className="font-mono text-gray-500">{m.id}</span></div>
                  <div><span className="text-gray-500">Sectors: </span><span className="text-gray-500">{(m.target_sectors || []).join(", ") || "All"}</span></div>
                  <div><span className="text-gray-500">Created by: </span><span className="text-gray-500">{m.created_by}</span></div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>

      <Section title={`Template Library (${templates.length})`} defaultOpen={false} accent="bg-gray-800">
        <p className="text-[10px] text-gray-500 mb-3">Read-only pre-calibrated templates. Clone to create an editable copy.</p>
        <div className="grid grid-cols-2 gap-2">
          {templates.map(t => (
            <div key={t.template_name} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-700">{t.name}</span>
                <Btn onClick={() => cloneFromTemplate(t.template_name)} size="sm" variant="secondary">
                  <Copy className="h-3 w-3" /> Use
                </Btn>
              </div>
              <p className="text-[10px] text-gray-500 line-clamp-2">{t.description}</p>
              <div className="flex gap-1 mt-1.5 flex-wrap">
                {(t.target_sectors || []).slice(0, 4).map(s => (
                  <span key={s} className="text-[8px] font-mono bg-gray-50 text-gray-500 px-1 py-0.5 rounded">{s}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ── Tab 5: Assessment Runner ──────────────────────────────────────────────────

const DEFAULT_ENTITY = { entity_id: "ENT-001", entity_name: "Portfolio A", entity_type: "portfolio" };

function AssessmentRunnerTab() {
  const [methodId, setMethodId] = useState("");
  const [methods, setMethods] = useState([]);
  const [entities, setEntities] = useState([{ ...DEFAULT_ENTITY }]);
  const [scenarios, setScenarios] = useState(["net_zero_2050", "delayed_transition"]);
  const [horizons, setHorizons] = useState([10, 20]);
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [runDetail, setRunDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/climate-risk/methodologies?status=PUBLISHED`)
      .then(({ data }) => setMethods(data.items || []))
      .catch(() => {});
    loadRuns();
  }, []);

  const loadRuns = async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/api/v1/climate-risk/assessments?limit=20`);
      setRuns(data.items || []);
    } catch { setRuns([]); }
  };

  const startRun = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/climate-risk/assessments/run`, {
        methodology_id: methodId || undefined,
        entities, scenarios, time_horizons: horizons,
        scope: "full_hierarchy",
      });
      await loadRuns();
      setSelectedRun(data.run_id);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  const fetchDetail = async (runId) => {
    try {
      const { data } = await axios.get(`${API_BASE}/api/v1/climate-risk/assessments/${runId}`);
      setRunDetail(data);
    } catch (e) {
      setRunDetail(null);
    }
  };

  const toggleHorizon = (h) => setHorizons(prev => prev.includes(h) ? prev.filter(x => x !== h) : [...prev, h]);
  const toggleScenario = (s) => setScenarios(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);

  return (
    <div>
      <Section title="Run Configuration" defaultOpen accent="bg-blue-600">
        <div className="grid grid-cols-2 gap-x-6 mb-3">
          <InputRow label="Methodology">
            <Select value={methodId} onChange={setMethodId}
              options={[{ value: "", label: "— Default —" }, ...methods.map(m => ({ value: m.id, label: m.name }))]} />
          </InputRow>
        </div>

        <div className="mb-3">
          <label className="text-[10px] text-gray-500 uppercase tracking-wider mb-2 block">Scenarios</label>
          <div className="flex flex-wrap gap-2">
            {SCENARIOS.map(s => (
              <button key={s} onClick={() => toggleScenario(s)}
                className={`text-[10px] px-2.5 py-1 rounded border transition-all ${
                  scenarios.includes(s)
                    ? "bg-gray-200 border-gray-300 text-gray-800"
                    : "bg-gray-50 border-black/10 text-gray-500 hover:text-gray-600"
                }`}>{SCENARIO_LABELS[s]}</button>
            ))}
          </div>
        </div>

        <div className="mb-3">
          <label className="text-[10px] text-gray-500 uppercase tracking-wider mb-2 block">Time Horizons</label>
          <div className="flex gap-2">
            {HORIZONS.map(h => (
              <button key={h} onClick={() => toggleHorizon(h)}
                className={`text-[10px] px-3 py-1 rounded border transition-all ${
                  horizons.includes(h)
                    ? "bg-gray-200 border-gray-300 text-gray-800"
                    : "bg-gray-50 border-black/10 text-gray-500 hover:text-gray-600"
                }`}>{h}yr</button>
            ))}
          </div>
        </div>

        <div className="mb-3">
          <div className="flex items-center justify-between mb-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Target Entities</label>
            <Btn onClick={() => setEntities(p => [...p, { entity_id: `ENT-${String(p.length + 1).padStart(3, "0")}`, entity_name: "", entity_type: "asset" }])} size="sm" variant="secondary">
              <Plus className="h-3 w-3" /> Add
            </Btn>
          </div>
          {entities.map((e, i) => (
            <div key={i} className="flex items-center gap-2 mb-1.5">
              <Input value={e.entity_id} onChange={v => setEntities(p => p.map((x, j) => j === i ? { ...x, entity_id: v } : x))} placeholder="ID" className="w-24" />
              <Input value={e.entity_name} onChange={v => setEntities(p => p.map((x, j) => j === i ? { ...x, entity_name: v } : x))} placeholder="Name" />
              <Select value={e.entity_type} onChange={v => setEntities(p => p.map((x, j) => j === i ? { ...x, entity_type: v } : x))}
                options={["portfolio", "fund", "asset", "security", "counterparty"]} className="w-36" />
              <button onClick={() => setEntities(p => p.filter((_, j) => j !== i))}
                className="text-red-400/40 hover:text-red-400 transition-colors">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>

        <div className="flex justify-end mt-2">
          <Btn onClick={startRun} disabled={loading || entities.length === 0 || scenarios.length === 0 || horizons.length === 0}>
            {loading ? <Spinner /> : <Play className="h-3.5 w-3.5" />}
            {loading ? "Launching…" : "Launch Assessment Run"}
          </Btn>
        </div>
      </Section>

      <ErrBox msg={error} />

      <Section title={`Previous Runs (${runs.length})`} defaultOpen={false} accent="bg-gray-500">
        <div className="flex justify-end mb-3">
          <Btn onClick={loadRuns} variant="secondary" size="sm"><RefreshCw className="h-3.5 w-3.5" /> Refresh</Btn>
        </div>
        {runs.length === 0 && <p className="text-[11px] text-gray-400 text-center py-4">No runs yet</p>}
        <div className="space-y-2">
          {runs.map(r => (
            <div key={r.id} className={`border rounded-lg p-3 cursor-pointer transition-all ${selectedRun === r.id ? "border-gray-300 bg-gray-50" : "border-gray-200 hover:border-black/10"}`}
              onClick={() => { setSelectedRun(r.id); fetchDetail(r.id); }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-gray-500">{r.id?.slice(0, 8)}</span>
                  <StatusBadge status={r.status} />
                  <span className="text-[10px] text-gray-500">{r.entity_count} entities × {r.scenario_count} scenarios × {r.horizon_count} horizons</span>
                </div>
                <span className="text-[10px] text-gray-400">{r.started_at ? new Date(r.started_at).toLocaleString() : "—"}</span>
              </div>
              {selectedRun === r.id && runDetail?.portfolio_aggregate && (
                <div className="mt-3 grid grid-cols-3 gap-3">
                  <KpiCard label="Avg Integrated Score" value={fmt2(runDetail.portfolio_aggregate.avg_integrated_score)} />
                  <KpiCard label="Worst Scenario" value={runDetail.portfolio_aggregate.worst_scenario || "—"} />
                  <KpiCard label="Duration" value={runDetail.duration_seconds ? `${fmt2(runDetail.duration_seconds)}s` : "—"} />
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ── Tab 6: Regulatory Reports ─────────────────────────────────────────────────

const REPORT_TYPES = [
  { value: "tcfd_four_pillar", label: "TCFD — Four Pillars", icon: BookOpen },
  { value: "eba_pillar3", label: "EBA Pillar 3 ESG (GL/2022/03)", icon: Shield },
  { value: "issb_s2", label: "ISSB S2 — Climate Disclosures", icon: Globe },
  { value: "csrd_esrs_e1", label: "CSRD ESRS E1 — Climate Change", icon: Zap },
  { value: "internal_summary", label: "Internal Risk Summary", icon: FileText },
];

function RegulatoryReportsTab() {
  const [reportType, setReportType] = useState("tcfd_four_pillar");
  const [runId, setRunId] = useState("");
  const [entityId, setEntityId] = useState("");
  const [scenario, setScenario] = useState("net_zero_2050");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API_BASE}/api/v1/climate-risk/reports/generate`, {
        report_type: reportType,
        run_id: runId || undefined,
        entity_id: entityId || undefined,
        scenario,
      });
      setResult(data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  const selType = REPORT_TYPES.find(r => r.value === reportType);

  return (
    <div>
      <Section title="Report Configuration" defaultOpen accent="bg-teal-500">
        <div className="grid grid-cols-2 gap-2 mb-4">
          {REPORT_TYPES.map(rt => {
            const Icon = rt.icon;
            return (
              <button key={rt.value} onClick={() => setReportType(rt.value)}
                className={`flex items-center gap-2 p-2.5 rounded-lg border text-left transition-all ${
                  reportType === rt.value
                    ? "bg-gray-100 border-gray-300 text-gray-800"
                    : "border-gray-200 text-gray-500 hover:border-black/10 hover:text-gray-700"
                }`}>
                <Icon className="h-4 w-4 shrink-0" />
                <span className="text-[11px] font-medium">{rt.label}</span>
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-2 gap-x-6">
          <InputRow label="Assessment Run ID">
            <Input value={runId} onChange={setRunId} placeholder="run-xxxxxxxx (optional)" />
          </InputRow>
          <InputRow label="Entity ID (optional)">
            <Input value={entityId} onChange={setEntityId} placeholder="ENT-001" />
          </InputRow>
          <InputRow label="Primary Scenario">
            <Select value={scenario} onChange={setScenario}
              options={SCENARIOS.map(s => ({ value: s, label: SCENARIO_LABELS[s] }))} />
          </InputRow>
        </div>

        <div className="flex justify-end mt-2">
          <Btn onClick={generate} disabled={loading}>
            {loading ? <Spinner /> : <FileText className="h-3.5 w-3.5" />}
            {loading ? "Generating…" : `Generate ${selType?.label || "Report"}`}
          </Btn>
        </div>
      </Section>

      <ErrBox msg={error} />

      {result && (
        <Section title="Generated Report" defaultOpen accent="bg-teal-500">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-[10px] font-mono text-gray-500">Generated:</span>
            <span className="text-[10px] text-gray-500">{new Date(result.generated_at || Date.now()).toLocaleString()}</span>
            {result.report_type && <StatusBadge status={result.report_type.toUpperCase()} />}
          </div>

          {result.sections?.map((sec, i) => (
            <div key={i} className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
                <span className="text-[11px] font-semibold text-gray-700">{sec.title || `Section ${i + 1}`}</span>
              </div>
              <div className="p-3 space-y-1">
                {typeof sec.content === "string"
                  ? <p className="text-[11px] text-gray-500 leading-relaxed whitespace-pre-wrap">{sec.content}</p>
                  : Object.entries(sec.content || {}).map(([k, v]) => (
                    <div key={k} className="flex gap-2 text-[11px]">
                      <span className="text-gray-500 w-40 shrink-0">{k.replace(/_/g, " ")}</span>
                      <span className="text-gray-600">{String(v)}</span>
                    </div>
                  ))
                }
              </div>
            </div>
          ))}

          {result.summary && (
            <div className="bg-white border border-black/10 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">Executive Summary</p>
              <p className="text-[11px] text-gray-500 leading-relaxed">{result.summary}</p>
            </div>
          )}
        </Section>
      )}
    </div>
  );
}

// ── Main Page Component ───────────────────────────────────────────────────────

const TABS = [
  { id: "physical",    label: "Physical Risk",       icon: Droplets },
  { id: "transition",  label: "Transition Risk",     icon: TrendingUp },
  { id: "integrated",  label: "Integrated View",     icon: Activity },
  { id: "methodology", label: "Methodology Mgr",     icon: Settings },
  { id: "runner",      label: "Assessment Runner",   icon: Play },
  { id: "regulatory",  label: "Regulatory Reports",  icon: FileText },
];

export default function ClimateRiskPage() {
  const [activeTab, setActiveTab] = useState("physical");

  return (
    <div className="p-4 max-w-[1200px] mx-auto">
      {/* Page header */}
      <div className="mb-5">
        <div className="flex items-center gap-2 mb-1">
          <Thermometer className="h-5 w-5 text-gray-700" />
          <h1 className="text-base font-semibold text-gray-900">Climate Risk Engine</h1>
          <span className="text-[9px] font-mono font-bold bg-gray-100 border border-gray-200 text-gray-700 px-1.5 py-0.5 rounded">NEW</span>
        </div>
        <p className="text-[11px] text-gray-500">
          Physical (HEV) · Transition (NACE/CPRS/NGFS P5) · Integrated · EBA GL/2025/01 · TCFD · ISSB S2 · CSRD ESRS E1
        </p>
      </div>

      {/* Tab strip */}
      <div className="flex gap-1 mb-5 border-b border-gray-200 pb-0">
        {TABS.map(tab => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs rounded-t transition-all relative ${
                activeTab === tab.id
                  ? "text-gray-800 bg-gray-50 border-b-2 border-[#164E8A]"
                  : "text-gray-500 hover:text-gray-600 hover:bg-gray-50"
              }`}>
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {activeTab === "physical"    && <PhysicalRiskTab />}
      {activeTab === "transition"  && <TransitionRiskTab />}
      {activeTab === "integrated"  && <IntegratedRiskTab />}
      {activeTab === "methodology" && <MethodologyTab />}
      {activeTab === "runner"      && <AssessmentRunnerTab />}
      {activeTab === "regulatory"  && <RegulatoryReportsTab />}
    </div>
  );
}
