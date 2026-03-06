/**
 * Client Engagement Tracker
 * PRI Active Ownership 2.0 · CA100+ · NZBA Phase 2 · TCFD Engagement
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Users, MessageSquare, AlertTriangle, CheckCircle, Clock,
  ChevronDown, ChevronUp, Plus, RefreshCw, Thermometer,
  Target, TrendingDown, Activity, Flag, FileText
} from "lucide-react";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";
const fmt = (v, d = 1) => v == null ? "—" : Number(v).toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });

const THEME_COLORS = {
  net_zero: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  deforestation: "bg-green-500/10 text-green-400 border-green-500/20",
  water: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  governance: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  just_transition: "bg-amber-500/10 text-amber-400 border-amber-500/20",
};
const STATUS_COLORS = {
  active: "text-emerald-400", escalated: "text-red-400",
  closed: "text-white/30", paused: "text-amber-400",
};
const OUTCOME_COLORS = {
  positive: "text-emerald-400", neutral: "text-white/50",
  negative: "text-red-400", pending: "text-amber-400",
};

function KpiCard({ icon: Icon, label, value, sub, color = "blue" }) {
  const colors = {
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    red: "bg-red-500/10 text-red-400 border-red-500/20",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  };
  return (
    <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-1.5 rounded ${colors[color]}`}><Icon className="h-4 w-4" /></div>
        <span className="text-xs text-white/40">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      {sub && <div className="text-xs text-white/30 mt-1">{sub}</div>}
    </div>
  );
}

function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-white/[0.06] rounded-lg overflow-hidden mb-4 bg-[#0d1424]">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.02] transition-colors">
        <span className="font-medium text-sm text-white/70">{title}</span>
        {open ? <ChevronUp className="h-4 w-4 text-white/30" /> : <ChevronDown className="h-4 w-4 text-white/30" />}
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
}

const DEFAULT_ENTITY = {
  entity_name: "", sector_gics: "Energy", country_iso2: "GB",
  engagement_theme: "net_zero", engagement_strategy: "direct",
  priority_tier: 1, ca100_focus: false, nzba_engagement: true,
  engagement_lead: "", baseline_temp_score: 3.2, current_temp_score: 3.0,
};

const DEFAULT_LOG = {
  log_date: new Date().toISOString().split("T")[0],
  interaction_type: "meeting", milestone: "", outcome: "pending",
  next_action: "", participants: "",
};

const DEFAULT_COMMITMENT = {
  commitment_type: "sbti_target", description: "",
  target_year: 2030, target_value: 50, target_unit: "pct_reduction",
  baseline_year: 2019, status: "open", verification_body: "SBTi",
};

export default function EngagementTrackerPage() {
  const [tab, setTab] = useState("dashboard");
  const [entities, setEntities] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [entityDetail, setEntityDetail] = useState(null);

  // Form states
  const [newEntity, setNewEntity] = useState({ ...DEFAULT_ENTITY });
  const [newLog, setNewLog] = useState({ ...DEFAULT_LOG });
  const [newCommitment, setNewCommitment] = useState({ ...DEFAULT_COMMITMENT });
  const [showAddEntity, setShowAddEntity] = useState(false);
  const [showAddLog, setShowAddLog] = useState(false);
  const [showAddCommit, setShowAddCommit] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [entRes, sumRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/engagement/entities`),
        axios.get(`${API_BASE}/api/v1/engagement/summary`),
      ]);
      setEntities(entRes.data);
      setSummary(sumRes.data);
    } catch (e) { /* tolerate empty */ }
    setLoading(false);
  }, []);

  const loadEntityDetail = useCallback(async (id) => {
    const { data } = await axios.get(`${API_BASE}/api/v1/engagement/entities/${id}`);
    setEntityDetail(data);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleAddEntity = async () => {
    setSaving(true); setError(null);
    try {
      await axios.post(`${API_BASE}/api/v1/engagement/entities`, newEntity);
      setShowAddEntity(false); setNewEntity({ ...DEFAULT_ENTITY });
      await loadAll();
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    setSaving(false);
  };

  const handleAddLog = async () => {
    if (!selectedEntity) return;
    setSaving(true); setError(null);
    try {
      await axios.post(`${API_BASE}/api/v1/engagement/log`, { ...newLog, entity_id: selectedEntity.id });
      setShowAddLog(false); setNewLog({ ...DEFAULT_LOG });
      await loadEntityDetail(selectedEntity.id);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    setSaving(false);
  };

  const handleAddCommitment = async () => {
    if (!selectedEntity) return;
    setSaving(true); setError(null);
    try {
      await axios.post(`${API_BASE}/api/v1/engagement/commitments`, { ...newCommitment, entity_id: selectedEntity.id });
      setShowAddCommit(false); setNewCommitment({ ...DEFAULT_COMMITMENT });
      await loadEntityDetail(selectedEntity.id);
    } catch (e) { setError(e.response?.data?.detail || e.message); }
    setSaving(false);
  };

  const selectEntity = async (entity) => {
    setSelectedEntity(entity);
    await loadEntityDetail(entity.id);
    setTab("entity");
  };

  const progressBar = (pct) => (
    <div className="w-full bg-white/[0.08] rounded-full h-1.5">
      <div className="h-1.5 rounded-full bg-gradient-to-r from-blue-600 to-emerald-500 transition-all"
        style={{ width: `${Math.min(pct || 0, 100)}%` }} />
    </div>
  );

  return (
    <div className="min-h-screen bg-white/[0.02]">
      {/* Header */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-lg"><Users className="h-6 w-6 text-emerald-500" /></div>
            <div>
              <h1 className="text-xl font-bold text-white">Client Engagement Tracker</h1>
              <p className="text-sm text-white/40">PRI Active Ownership 2.0 · CA100+ Net Zero Benchmark · NZBA Phase 2 · TCFD</p>
            </div>
          </div>
          <div className="flex gap-2">
            {["PRI AO2.0", "CA100+", "NZBA P2", "TCFD"].map(b => (
              <span key={b} className="text-xs px-2 py-1 bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 rounded-full font-medium">{b}</span>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-0 mt-4">
          {[["dashboard", "Portfolio Dashboard"], ["entities", "Engagement Universe"], ...(selectedEntity ? [["entity", selectedEntity.entity_name]] : [])].map(([id, l]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 ${tab === id ? "border-emerald-500 text-emerald-400" : "border-transparent text-white/40 hover:text-white/70"}`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        {/* ── Dashboard Tab ── */}
        {tab === "dashboard" && summary && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <KpiCard icon={Users} label="Entities Under Engagement" value={summary.totals.entity_count} sub="Active + Escalated" color="blue" />
              <KpiCard icon={Activity} label="Active Dialogues" value={summary.totals.active} color="green" />
              <KpiCard icon={Flag} label="Escalated" value={summary.totals.escalated} sub="Vote / Divestment risk" color="red" />
              <KpiCard icon={Target} label="CA100+ Focus" value={summary.totals.ca100_count} color="amber" />
            </div>

            {/* Temperature Delta */}
            {summary.totals.avg_baseline_temp_c && (
              <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
                <h3 className="text-sm font-semibold text-white/70 mb-4 flex items-center gap-2">
                  <Thermometer className="h-4 w-4 text-amber-400" /> Portfolio Implied Temperature Alignment
                </h3>
                <div className="grid grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-red-400">{fmt(summary.totals.avg_baseline_temp_c, 1)}°C</div>
                    <div className="text-xs text-white/30 mt-1">Baseline (at start)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-amber-400">{fmt(summary.totals.avg_current_temp_c, 1)}°C</div>
                    <div className="text-xs text-white/30 mt-1">Current</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-3xl font-bold ${summary.totals.temp_delta_c < 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {summary.totals.temp_delta_c < 0 ? "" : "+"}{fmt(summary.totals.temp_delta_c, 2)}°C
                    </div>
                    <div className="text-xs text-white/30 mt-1">Engagement Impact</div>
                  </div>
                </div>
              </div>
            )}

            {/* By Theme + Upcoming */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {summary.by_theme.length > 0 && (
                <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-white/70 mb-3">By Engagement Theme</h3>
                  <div className="space-y-2">
                    {summary.by_theme.map(t => (
                      <div key={t.engagement_theme} className="flex items-center gap-3">
                        <span className={`text-xs px-2 py-0.5 rounded border ${THEME_COLORS[t.engagement_theme] || "bg-gray-500/10 text-gray-400 border-gray-500/20"}`}>
                          {t.engagement_theme.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs text-white/40">{t.count} entities</span>
                        <span className="text-xs text-white/30 ml-auto">{fmt(t.avg_progress, 0)}% avg progress</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {summary.upcoming_actions.length > 0 && (
                <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-white/70 mb-3 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-amber-400" /> Upcoming Actions
                  </h3>
                  <div className="space-y-2">
                    {summary.upcoming_actions.slice(0, 6).map((a, i) => (
                      <div key={i} className="flex items-start gap-3 text-xs border-b border-white/[0.04] pb-2">
                        <div className="text-amber-400 font-mono shrink-0">{a.next_action_date}</div>
                        <div>
                          <div className="text-white/70">{a.entity_name}</div>
                          <div className="text-white/30">{a.next_action}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Entity List Tab ── */}
        {tab === "entities" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white/80">Engagement Universe ({entities.length})</h2>
              <button onClick={() => setShowAddEntity(!showAddEntity)}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded-lg flex items-center gap-1.5">
                <Plus className="h-3 w-3" /> Add Entity
              </button>
            </div>

            {/* Add entity form */}
            {showAddEntity && (
              <div className="bg-[#111827] border border-emerald-500/20 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-emerald-400 mb-3">New Engagement Entity</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    ["entity_name", "Entity Name", "text"],
                    ["sector_gics", "Sector (GICS)", "text"],
                    ["country_iso2", "Country ISO2", "text"],
                    ["engagement_lead", "Engagement Lead", "text"],
                    ["baseline_temp_score", "Baseline Temp (°C)", "number"],
                    ["current_temp_score", "Current Temp (°C)", "number"],
                  ].map(([k, label, type]) => (
                    <div key={k}>
                      <label className="text-xs text-white/40 block mb-1">{label}</label>
                      <input type={type} className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                        value={newEntity[k] || ""} onChange={e => setNewEntity(f => ({ ...f, [k]: type === "number" ? +e.target.value : e.target.value }))} />
                    </div>
                  ))}
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Engagement Theme</label>
                    <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newEntity.engagement_theme} onChange={e => setNewEntity(f => ({ ...f, engagement_theme: e.target.value }))}>
                      {["net_zero", "deforestation", "water", "governance", "just_transition"].map(v => (
                        <option key={v} value={v}>{v.replace(/_/g, " ")}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Priority Tier</label>
                    <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newEntity.priority_tier} onChange={e => setNewEntity(f => ({ ...f, priority_tier: +e.target.value }))}>
                      {[1, 2, 3].map(v => <option key={v} value={v}>Tier {v}</option>)}
                    </select>
                  </div>
                  <div className="flex items-center gap-4 mt-4">
                    <label className="text-xs text-white/40">CA100+ Focus</label>
                    <input type="checkbox" checked={newEntity.ca100_focus} onChange={e => setNewEntity(f => ({ ...f, ca100_focus: e.target.checked }))} />
                    <label className="text-xs text-white/40 ml-2">NZBA Engagement</label>
                    <input type="checkbox" checked={newEntity.nzba_engagement} onChange={e => setNewEntity(f => ({ ...f, nzba_engagement: e.target.checked }))} />
                  </div>
                </div>
                {error && <div className="mt-2 text-xs text-red-400">{error}</div>}
                <button onClick={handleAddEntity} disabled={saving}
                  className="mt-3 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded-lg flex items-center gap-2">
                  {saving ? <><RefreshCw className="h-3 w-3 animate-spin" /> Saving…</> : <><Plus className="h-3 w-3" /> Save Entity</>}
                </button>
              </div>
            )}

            {/* Entity table */}
            {loading ? (
              <div className="text-center py-12 text-white/30 text-sm">Loading…</div>
            ) : entities.length === 0 ? (
              <div className="text-center py-12 text-white/30 text-sm">No entities yet. Add one above.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="text-white/30 border-b border-white/[0.06]">
                    <th className="text-left py-2 px-3">Entity</th>
                    <th className="text-left py-2 px-3">Theme</th>
                    <th className="text-left py-2 px-3">Status</th>
                    <th className="text-left py-2 px-3">Tier</th>
                    <th className="text-left py-2 px-3">Progress</th>
                    <th className="text-left py-2 px-3">Temp (°C)</th>
                    <th className="text-left py-2 px-3">Interactions</th>
                    <th className="text-left py-2 px-3">Last Contact</th>
                  </tr></thead>
                  <tbody>
                    {entities.map(e => (
                      <tr key={e.id} onClick={() => selectEntity(e)}
                        className="border-b border-white/[0.04] hover:bg-white/[0.03] cursor-pointer">
                        <td className="py-2 px-3">
                          <div className="font-medium text-white/80">{e.entity_name}</div>
                          <div className="text-white/30">{e.sector_gics} · {e.country_iso2}</div>
                        </td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-0.5 rounded border text-xs ${THEME_COLORS[e.engagement_theme] || "bg-gray-500/10 text-gray-400 border-gray-500/20"}`}>
                            {e.engagement_theme?.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="py-2 px-3">
                          <span className={`font-medium capitalize ${STATUS_COLORS[e.status]}`}>{e.status}</span>
                        </td>
                        <td className="py-2 px-3 text-white/50">T{e.priority_tier}</td>
                        <td className="py-2 px-3 w-24">
                          <div className="mb-1">{fmt(e.overall_progress_pct, 0)}%</div>
                          {progressBar(e.overall_progress_pct)}
                        </td>
                        <td className="py-2 px-3">
                          <div className="text-white/50">{fmt(e.baseline_temp_score, 1)}→{fmt(e.current_temp_score, 1)}°C</div>
                        </td>
                        <td className="py-2 px-3 text-white/40">{e.interaction_count}</td>
                        <td className="py-2 px-3 text-white/30">{e.last_interaction_date || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── Entity Detail Tab ── */}
        {tab === "entity" && entityDetail && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-white/90">{entityDetail.entity?.entity_name}</h2>
                <p className="text-xs text-white/30">{entityDetail.entity?.sector_gics} · {entityDetail.entity?.country_iso2} · Engagement Lead: {entityDetail.entity?.engagement_lead || "—"}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => { setShowAddLog(!showAddLog); setShowAddCommit(false); }}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg flex items-center gap-1.5">
                  <MessageSquare className="h-3 w-3" /> Log Interaction
                </button>
                <button onClick={() => { setShowAddCommit(!showAddCommit); setShowAddLog(false); }}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg flex items-center gap-1.5">
                  <FileText className="h-3 w-3" /> Add Commitment
                </button>
              </div>
            </div>

            {/* Log Interaction form */}
            {showAddLog && (
              <div className="bg-[#111827] border border-blue-500/20 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-blue-400 mb-3">Log Interaction</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Date</label>
                    <input type="date" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newLog.log_date} onChange={e => setNewLog(f => ({ ...f, log_date: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Type</label>
                    <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newLog.interaction_type} onChange={e => setNewLog(f => ({ ...f, interaction_type: e.target.value }))}>
                      {["meeting", "call", "letter", "agm_vote", "proxy_alert", "report_review"].map(v => (
                        <option key={v} value={v}>{v.replace(/_/g, " ")}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Outcome</label>
                    <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newLog.outcome} onChange={e => setNewLog(f => ({ ...f, outcome: e.target.value }))}>
                      {["positive", "neutral", "negative", "pending"].map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-xs text-white/40 block mb-1">Milestone / Key Message</label>
                    <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newLog.milestone} onChange={e => setNewLog(f => ({ ...f, milestone: e.target.value }))}
                      placeholder="e.g. Board committed to setting SBTi-aligned target by Q3 2025" />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Next Action Date</label>
                    <input type="date" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newLog.next_action_date || ""} onChange={e => setNewLog(f => ({ ...f, next_action_date: e.target.value }))} />
                  </div>
                </div>
                {error && <div className="mt-2 text-xs text-red-400">{error}</div>}
                <button onClick={handleAddLog} disabled={saving}
                  className="mt-3 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg flex items-center gap-2">
                  {saving ? <><RefreshCw className="h-3 w-3 animate-spin" /> Saving…</> : "Save Log"}
                </button>
              </div>
            )}

            {/* Add Commitment form */}
            {showAddCommit && (
              <div className="bg-[#111827] border border-indigo-500/20 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-indigo-400 mb-3">Record Commitment</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Commitment Type</label>
                    <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newCommitment.commitment_type} onChange={e => setNewCommitment(f => ({ ...f, commitment_type: e.target.value }))}>
                      {["sbti_target", "net_zero_pledge", "scope3_disclosure", "board_climate", "capex_plan"].map(v => (
                        <option key={v} value={v}>{v.replace(/_/g, " ")}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Target Year</label>
                    <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newCommitment.target_year} onChange={e => setNewCommitment(f => ({ ...f, target_year: +e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Target Value</label>
                    <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newCommitment.target_value} onChange={e => setNewCommitment(f => ({ ...f, target_value: +e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Unit</label>
                    <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newCommitment.target_unit} onChange={e => setNewCommitment(f => ({ ...f, target_unit: e.target.value }))}>
                      {["pct_reduction", "tco2e", "mw", "GBP", "USD"].map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Verification Body</label>
                    <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newCommitment.verification_body} onChange={e => setNewCommitment(f => ({ ...f, verification_body: e.target.value }))} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-xs text-white/40 block mb-1">Description</label>
                    <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                      value={newCommitment.description} onChange={e => setNewCommitment(f => ({ ...f, description: e.target.value }))}
                      placeholder="e.g. 50% absolute Scope 1+2 reduction by 2030 vs 2019 baseline" />
                  </div>
                </div>
                {error && <div className="mt-2 text-xs text-red-400">{error}</div>}
                <button onClick={handleAddCommitment} disabled={saving}
                  className="mt-3 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg flex items-center gap-2">
                  {saving ? <><RefreshCw className="h-3 w-3 animate-spin" /> Saving…</> : "Save Commitment"}
                </button>
              </div>
            )}

            {/* Interaction Log */}
            <Section title={`Interaction Log (${entityDetail.log?.length || 0})`}>
              {entityDetail.log?.length === 0 ? (
                <p className="text-xs text-white/30">No interactions logged yet.</p>
              ) : (
                <div className="space-y-2">
                  {entityDetail.log.map(l => (
                    <div key={l.id} className="border border-white/[0.06] rounded p-3 text-xs">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-white/50 font-mono">{l.log_date}</span>
                        <span className="text-white/40 capitalize">{l.interaction_type?.replace(/_/g, " ")}</span>
                        <span className={`ml-auto font-medium ${OUTCOME_COLORS[l.outcome]}`}>{l.outcome}</span>
                      </div>
                      {l.milestone && <div className="text-white/70">{l.milestone}</div>}
                      {l.next_action && <div className="text-amber-400 mt-1">Next: {l.next_action} {l.next_action_date ? `(${l.next_action_date})` : ""}</div>}
                    </div>
                  ))}
                </div>
              )}
            </Section>

            {/* Commitments */}
            <Section title={`Commitments (${entityDetail.commitments?.length || 0})`}>
              {entityDetail.commitments?.length === 0 ? (
                <p className="text-xs text-white/30">No commitments recorded.</p>
              ) : (
                <div className="space-y-2">
                  {entityDetail.commitments.map(c => (
                    <div key={c.id} className="border border-white/[0.06] rounded p-3 text-xs flex items-start justify-between">
                      <div>
                        <div className="font-medium text-white/80 capitalize">{c.commitment_type?.replace(/_/g, " ")}</div>
                        <div className="text-white/40 mt-1">{c.description}</div>
                        {c.target_year && <div className="text-indigo-400 mt-1">Target: {c.target_value} {c.target_unit} by {c.target_year}</div>}
                      </div>
                      <div className="text-right">
                        <span className={`text-xs font-medium ${c.status === "delivered" ? "text-emerald-400" : c.status === "missed" ? "text-red-400" : "text-amber-400"}`}>{c.status}</span>
                        {c.verified && <div className="text-emerald-400 text-xs mt-1">Verified ✓ {c.verification_body}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Section>

            {/* Escalations */}
            <Section title={`Escalations (${entityDetail.escalations?.length || 0})`} defaultOpen={false}>
              {entityDetail.escalations?.length === 0 ? (
                <p className="text-xs text-white/30">No escalations.</p>
              ) : (
                <div className="space-y-2">
                  {entityDetail.escalations.map(esc => (
                    <div key={esc.id} className="border border-red-500/20 rounded p-3 text-xs bg-red-500/5">
                      <div className="flex items-center gap-2 text-red-400">
                        <AlertTriangle className="h-3 w-3" />
                        <span className="font-medium capitalize">{esc.escalation_type?.replace(/_/g, " ")}</span>
                        <span className="text-white/30 ml-auto">{esc.escalation_date}</span>
                      </div>
                      {esc.trigger_reason && <div className="text-white/50 mt-1">{esc.trigger_reason}</div>}
                      {esc.action_taken && <div className="text-amber-300 mt-1">Action: {esc.action_taken}</div>}
                    </div>
                  ))}
                </div>
              )}
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}
