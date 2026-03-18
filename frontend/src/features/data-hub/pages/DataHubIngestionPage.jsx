/**
 * DataHubIngestionPage.jsx
 * Route: /data-hub-ingestion
 *
 * Ingestion Monitor & Data Source Catalog.
 * Tabs:
 *   1. Ingester Status  — All registered ingesters, last run, next run, trigger buttons
 *   2. Sync History     — Job log: source, status, records upserted, duration, errors
 *   3. Source Catalog   — Full registry: tier, category, table, row counts, coverage matrix
 *   4. Scheduler        — APScheduler status, upcoming runs, cron config
 *   5. KPI Mappings     — Cross-module KPI definitions and source-to-platform field mappings
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend,
} from 'recharts';
import {
  Database, RefreshCw, Play, CheckCircle, XCircle, Clock,
  AlertTriangle, Activity, Layers, Link, Calendar, ChevronRight,
  Download, Globe,
} from 'lucide-react';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// ── Seed RNG ──────────────────────────────────────────────────────────────
function seededRand(seed) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 4294967296; };
}

// ── Deterministic fallback data ────────────────────────────────────────────
const FALLBACK_INGESTERS = [
  { source_id: 'gleif_lei', display_name: 'GLEIF LEI Registry', category: 'Entity Resolution', tier: 'tier_1', schedule: '0 2 * * 0', last_run: '2026-03-15T02:00:12Z', next_run: '2026-03-22T02:00:00Z', last_status: 'success', records_last_run: 82450, avg_duration_s: 145 },
  { source_id: 'opensanctions', display_name: 'OpenSanctions Consolidated', category: 'Entity Resolution', tier: 'tier_1', schedule: '0 3 * * *', last_run: '2026-03-16T03:01:44Z', next_run: '2026-03-17T03:00:00Z', last_status: 'success', records_last_run: 12300, avg_duration_s: 62 },
  { source_id: 'climate_trace', display_name: 'Climate TRACE Emissions', category: 'Emissions', tier: 'tier_1', schedule: '0 4 1 * *', last_run: '2026-03-01T04:00:09Z', next_run: '2026-04-01T04:00:00Z', last_status: 'partial', records_last_run: 241000, avg_duration_s: 820 },
  { source_id: 'owid_co2', display_name: 'OWID CO₂ & Energy', category: 'Emissions', tier: 'tier_2', schedule: '0 5 * * 0', last_run: '2026-03-15T05:00:22Z', next_run: '2026-03-22T05:00:00Z', last_status: 'success', records_last_run: 5800, avg_duration_s: 28 },
  { source_id: 'ngfs_scenarios', display_name: 'NGFS Phase V Scenarios', category: 'Scenarios', tier: 'tier_1', schedule: '0 1 1 */3 *', last_run: '2026-03-01T01:00:00Z', next_run: '2026-06-01T01:00:00Z', last_status: 'success', records_last_run: 18420, avg_duration_s: 310 },
  { source_id: 'sbti_companies', display_name: 'SBTi Target Registry', category: 'Targets', tier: 'tier_2', schedule: '0 6 * * 1', last_run: '2026-03-16T06:00:11Z', next_run: '2026-03-23T06:00:00Z', last_status: 'success', records_last_run: 9200, avg_duration_s: 55 },
  { source_id: 'sec_edgar', display_name: 'SEC EDGAR XBRL Filings', category: 'Financial', tier: 'tier_2', schedule: '0 7 * * *', last_run: '2026-03-16T07:01:33Z', next_run: '2026-03-17T07:00:00Z', last_status: 'running', records_last_run: 0, avg_duration_s: 0 },
  { source_id: 'yfinance', display_name: 'Yahoo Finance / EVIC', category: 'Financial', tier: 'tier_2', schedule: '0 8 * * 1-5', last_run: '2026-03-16T08:00:05Z', next_run: '2026-03-17T08:00:00Z', last_status: 'success', records_last_run: 3100, avg_duration_s: 42 },
  { source_id: 'violation_tracker', display_name: 'Violation Tracker', category: 'Controversy', tier: 'tier_3', schedule: '0 9 * * 0', last_run: '2026-03-15T09:00:44Z', next_run: '2026-03-22T09:00:00Z', last_status: 'failed', records_last_run: 0, avg_duration_s: 0 },
  { source_id: 'wdpa_gfw', display_name: 'WDPA + GFW Nature Spatial', category: 'Nature', tier: 'tier_2', schedule: '0 10 1 * *', last_run: '2026-03-01T10:00:00Z', next_run: '2026-04-01T10:00:00Z', last_status: 'success', records_last_run: 341000, avg_duration_s: 1240 },
  { source_id: 'gem_coal', display_name: 'GEM Global Coal Plant Tracker', category: 'Energy', tier: 'tier_3', schedule: '0 11 1 * *', last_run: '2026-03-01T11:00:00Z', next_run: '2026-04-01T11:00:00Z', last_status: 'success', records_last_run: 6700, avg_duration_s: 88 },
  { source_id: 'irena_crrem', display_name: 'IRENA / CRREM / Grid EFs', category: 'Energy', tier: 'tier_2', schedule: '0 12 1 */6 *', last_run: '2026-01-01T12:00:00Z', next_run: '2026-07-01T12:00:00Z', last_status: 'success', records_last_run: 8900, avg_duration_s: 95 },
  { source_id: 'gdelt_controversy', display_name: 'GDELT Controversy Monitor', category: 'Controversy', tier: 'tier_3', schedule: '0 0 * * *', last_run: '2026-03-16T00:00:18Z', next_run: '2026-03-17T00:00:00Z', last_status: 'success', records_last_run: 4200, avg_duration_s: 38 },
];

const FALLBACK_JOBS = Array.from({ length: 20 }, (_, i) => {
  const rng = seededRand(55000 + i);
  const src = FALLBACK_INGESTERS[i % FALLBACK_INGESTERS.length];
  const statuses = ['success', 'success', 'success', 'partial', 'failed'];
  const status = statuses[Math.floor(rng() * statuses.length)];
  const dt = new Date('2026-03-16T12:00:00Z');
  dt.setHours(dt.getHours() - i * 4);
  return {
    id: `job-${i + 1}`,
    source_id: src.source_id,
    source_name: src.display_name,
    status,
    started_at: dt.toISOString(),
    duration_s: status === 'failed' ? Math.floor(rng() * 30 + 5) : Math.floor(rng() * 800 + 20),
    records_upserted: status === 'failed' ? 0 : Math.floor(rng() * 50000 + 100),
    records_failed: status === 'failed' ? Math.floor(rng() * 100) : 0,
    error_message: status === 'failed' ? 'Connection timeout after 30s' : null,
  };
});

const STATUS_CONFIG = {
  success:  { label: 'Success',  bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500', icon: CheckCircle },
  partial:  { label: 'Partial',  bg: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500', icon: AlertTriangle },
  failed:   { label: 'Failed',   bg: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500', icon: XCircle },
  running:  { label: 'Running',  bg: 'bg-blue-50 text-blue-700 border-blue-200', dot: 'bg-blue-500 animate-pulse', icon: RefreshCw },
  pending:  { label: 'Pending',  bg: 'bg-gray-100 text-gray-600 border-gray-200', dot: 'bg-gray-400', icon: Clock },
};

const TIER_COLORS = { tier_1: '#059669', tier_2: '#0284c7', tier_3: '#f59e0b', tier_4: '#8b5cf6' };
const CATEGORY_COLORS = { 'Entity Resolution': '#059669', Emissions: '#ef4444', Scenarios: '#0284c7', Financial: '#8b5cf6', Targets: '#f59e0b', Nature: '#10b981', Energy: '#f97316', Controversy: '#6b7280' };

const TABS = [
  { id: 'status', label: 'Ingester Status', icon: Activity },
  { id: 'jobs', label: 'Sync History', icon: Clock },
  { id: 'catalog', label: 'Source Catalog', icon: Database },
  { id: 'scheduler', label: 'Scheduler', icon: Calendar },
  { id: 'kpis', label: 'KPI Mappings', icon: Link },
];

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${cfg.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

function fmtTs(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }); }
  catch { return iso; }
}

function fmtDur(s) {
  if (!s) return '—';
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

// ── Tab 1: Ingester Status ───────────────────────────────────────────────
function IngesterStatusTab({ ingesters, onTrigger, triggering }) {
  const summary = {
    total: ingesters.length,
    success: ingesters.filter(i => i.last_status === 'success').length,
    failed: ingesters.filter(i => i.last_status === 'failed').length,
    running: ingesters.filter(i => i.last_status === 'running').length,
    partial: ingesters.filter(i => i.last_status === 'partial').length,
  };

  const categoryData = Object.entries(
    ingesters.reduce((acc, i) => { acc[i.category] = (acc[i.category] || 0) + 1; return acc; }, {})
  ).map(([name, value]) => ({ name, value, fill: CATEGORY_COLORS[name] || '#6b7280' }));

  return (
    <div>
      {/* Summary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        {[
          { label: 'Total Ingesters', value: summary.total, accent: '' },
          { label: 'Succeeded', value: summary.success, accent: 'text-emerald-700' },
          { label: 'Running', value: summary.running, accent: 'text-blue-700' },
          { label: 'Partial', value: summary.partial, accent: 'text-amber-700' },
          { label: 'Failed', value: summary.failed, accent: 'text-red-700' },
        ].map(k => (
          <div key={k.label} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">{k.label}</div>
            <div className={`text-2xl font-bold font-mono ${k.accent || 'text-gray-900'}`}>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">All Ingesters</h3>
            <button
              onClick={() => onTrigger('__all__')}
              disabled={triggering === '__all__'}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black text-white text-xs font-semibold hover:bg-gray-800 transition disabled:opacity-60"
            >
              {triggering === '__all__' ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
              Trigger All
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-400 font-semibold">Ingester</th>
                  <th className="text-left py-2 text-gray-400 font-semibold">Category</th>
                  <th className="text-right py-2 text-gray-400 font-semibold">Last Run</th>
                  <th className="text-right py-2 text-gray-400 font-semibold">Records</th>
                  <th className="text-center py-2 text-gray-400 font-semibold">Status</th>
                  <th className="text-center py-2 text-gray-400 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {ingesters.map(ing => (
                  <tr key={ing.source_id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2.5">
                      <div className="font-medium text-gray-800">{ing.display_name}</div>
                      <div className="text-[10px] text-gray-400 font-mono">{ing.source_id}</div>
                    </td>
                    <td className="py-2.5">
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold text-white" style={{ background: CATEGORY_COLORS[ing.category] || '#6b7280' }}>
                        {ing.category}
                      </span>
                    </td>
                    <td className="text-right py-2.5 text-gray-500 font-mono">{fmtTs(ing.last_run)}</td>
                    <td className="text-right py-2.5 font-mono text-gray-700">{(ing.records_last_run || 0).toLocaleString()}</td>
                    <td className="text-center py-2.5"><StatusBadge status={ing.last_status || 'pending'} /></td>
                    <td className="text-center py-2.5">
                      <button
                        onClick={() => onTrigger(ing.source_id)}
                        disabled={triggering === ing.source_id || ing.last_status === 'running'}
                        className="p-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-600 disabled:opacity-40 transition"
                        title="Trigger ingestion"
                      >
                        {triggering === ing.source_id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">By Category</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={categoryData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} dataKey="value" paddingAngle={2}>
                {categoryData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Pie>
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// ── Tab 2: Sync History ──────────────────────────────────────────────────
function SyncHistoryTab({ jobs }) {
  const [filter, setFilter] = useState('all');
  const filtered = filter === 'all' ? jobs : jobs.filter(j => j.status === filter);

  const barData = ['success', 'partial', 'failed'].map(s => ({
    status: s.charAt(0).toUpperCase() + s.slice(1),
    count: jobs.filter(j => j.status === s).length,
    fill: s === 'success' ? '#059669' : s === 'partial' ? '#f59e0b' : '#ef4444',
  }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Last 20 Jobs — Status</h3>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={barData} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="status" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {barData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Job History</h3>
            <div className="flex gap-1">
              {['all', 'success', 'partial', 'failed'].map(s => (
                <button key={s} onClick={() => setFilter(s)}
                  className={`px-2 py-1 rounded text-[10px] font-semibold transition-colors ${filter === s ? 'bg-black text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="overflow-x-auto max-h-72 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-400 font-semibold">Source</th>
                  <th className="text-right py-2 text-gray-400 font-semibold">Started</th>
                  <th className="text-right py-2 text-gray-400 font-semibold">Duration</th>
                  <th className="text-right py-2 text-gray-400 font-semibold">Records</th>
                  <th className="text-center py-2 text-gray-400 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(job => (
                  <tr key={job.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2.5 font-medium text-gray-800">{job.source_name}</td>
                    <td className="text-right py-2.5 text-gray-500 font-mono">{fmtTs(job.started_at)}</td>
                    <td className="text-right py-2.5 font-mono text-gray-700">{fmtDur(job.duration_s)}</td>
                    <td className="text-right py-2.5 font-mono text-gray-700">
                      {job.records_upserted > 0 ? job.records_upserted.toLocaleString() : '—'}
                      {job.records_failed > 0 && <span className="text-red-500 ml-1">({job.records_failed} err)</span>}
                    </td>
                    <td className="text-center py-2.5">
                      <StatusBadge status={job.status} />
                      {job.error_message && <div className="text-[9px] text-red-500 mt-0.5 max-w-xs truncate">{job.error_message}</div>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Tab 3: Source Catalog ────────────────────────────────────────────────
function SourceCatalogTab({ ingesters }) {
  const tiers = [...new Set(ingesters.map(i => i.tier))].sort();
  const categories = [...new Set(ingesters.map(i => i.category))];

  const totalRecords = ingesters.reduce((s, i) => s + (i.records_last_run || 0), 0);

  const byTier = tiers.map(t => ({
    tier: t.replace('tier_', 'T'),
    count: ingesters.filter(i => i.tier === t).length,
    records: ingesters.filter(i => i.tier === t).reduce((s, i) => s + (i.records_last_run || 0), 0),
    fill: TIER_COLORS[t] || '#6b7280',
  }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">Total Sources</div>
          <div className="text-2xl font-bold font-mono text-gray-900">{ingesters.length}</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">Categories</div>
          <div className="text-2xl font-bold font-mono text-gray-900">{categories.length}</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">Total Records (Last Run)</div>
          <div className="text-2xl font-bold font-mono text-emerald-700">{(totalRecords / 1000).toFixed(0)}k</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">Tiers</div>
          <div className="text-2xl font-bold font-mono text-gray-900">{tiers.length}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Records by Tier</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={byTier} barSize={30}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="tier" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10 }} />
              <Tooltip formatter={v => v.toLocaleString() + ' records'} />
              <Bar dataKey="records" radius={[4, 4, 0, 0]}>
                {byTier.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Full Source Registry</h3>
          <div className="overflow-x-auto max-h-72 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-400 font-semibold">Source</th>
                  <th className="text-left py-2 text-gray-400 font-semibold">Category</th>
                  <th className="text-center py-2 text-gray-400 font-semibold">Tier</th>
                  <th className="text-right py-2 text-gray-400 font-semibold">Records</th>
                  <th className="text-right py-2 text-gray-400 font-semibold">Avg Duration</th>
                </tr>
              </thead>
              <tbody>
                {ingesters.map(ing => (
                  <tr key={ing.source_id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2.5">
                      <div className="font-medium text-gray-800">{ing.display_name}</div>
                      <div className="text-[10px] text-gray-400 font-mono">{ing.source_id}</div>
                    </td>
                    <td className="py-2.5">
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold text-white" style={{ background: CATEGORY_COLORS[ing.category] || '#6b7280' }}>
                        {ing.category}
                      </span>
                    </td>
                    <td className="text-center py-2.5">
                      <span className="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold text-white mx-auto" style={{ background: TIER_COLORS[ing.tier] || '#6b7280' }}>
                        {ing.tier?.replace('tier_', 'T')}
                      </span>
                    </td>
                    <td className="text-right py-2.5 font-mono text-gray-700">{(ing.records_last_run || 0).toLocaleString()}</td>
                    <td className="text-right py-2.5 font-mono text-gray-500">{fmtDur(ing.avg_duration_s)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Tab 4: Scheduler ──────────────────────────────────────────────────────
function SchedulerTab({ ingesters }) {
  const upcoming = [...ingesters]
    .filter(i => i.next_run)
    .sort((a, b) => new Date(a.next_run) - new Date(b.next_run))
    .slice(0, 10);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <h3 className="text-sm font-semibold text-gray-900">Scheduler Running</h3>
            <span className="ml-auto text-[10px] text-gray-400">APScheduler v3.10</span>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1.5 border-b border-gray-50"><span className="text-gray-500">Job Store</span><span className="font-mono text-gray-700">SQLAlchemyJobStore (PostgreSQL)</span></div>
            <div className="flex justify-between py-1.5 border-b border-gray-50"><span className="text-gray-500">Executor</span><span className="font-mono text-gray-700">ThreadPoolExecutor (max_workers=5)</span></div>
            <div className="flex justify-between py-1.5 border-b border-gray-50"><span className="text-gray-500">Timezone</span><span className="font-mono text-gray-700">UTC</span></div>
            <div className="flex justify-between py-1.5 border-b border-gray-50"><span className="text-gray-500">Registered Jobs</span><span className="font-mono text-gray-700">{ingesters.length}</span></div>
            <div className="flex justify-between py-1.5"><span className="text-gray-500">Misfire Grace</span><span className="font-mono text-gray-700">60s</span></div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Upcoming Runs</h3>
          <div className="space-y-2">
            {upcoming.map(ing => (
              <div key={ing.source_id} className="flex items-center justify-between p-2.5 rounded-lg bg-gray-50">
                <div>
                  <div className="text-xs font-medium text-gray-800">{ing.display_name}</div>
                  <div className="text-[10px] text-gray-400 font-mono">{ing.schedule}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-gray-700">{fmtTs(ing.next_run)}</div>
                  <StatusBadge status={ing.last_status || 'pending'} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Tab 5: KPI Mappings ───────────────────────────────────────────────────
const SAMPLE_KPIS = [
  { id: 'financed_emissions', name: 'Financed Emissions (tCO₂e)', category: 'Emissions', sources: ['climate_trace', 'owid_co2'], modules: ['PCAF', 'SFDR PAI', 'CSRD ESRS E1'] },
  { id: 'scope1_ghg', name: 'Scope 1 GHG (tCO₂e)', category: 'Emissions', sources: ['sec_edgar', 'climate_trace'], modules: ['Carbon Calculator', 'CBAM', 'EU Taxonomy'] },
  { id: 'carbon_price_usd', name: 'Carbon Price (USD/tCO₂)', category: 'Market Data', sources: ['ngfs_scenarios'], modules: ['Scenario Analysis', 'ECL Climate', 'Factor Overlay'] },
  { id: 'sbti_target_year', name: 'SBTi Target Year', category: 'Targets', sources: ['sbti_companies'], modules: ['PCAF', 'CSRD ESRS E1', 'Transition Plan'] },
  { id: 'lei', name: 'Legal Entity Identifier (LEI)', category: 'Entity', sources: ['gleif_lei'], modules: ['Entity 360', 'PCAF', 'CSRD', 'SFDR'] },
  { id: 'sanctions_flag', name: 'Sanctions Flag', category: 'Entity', sources: ['opensanctions'], modules: ['Entity 360', 'Factor Overlay'] },
  { id: 'evic', name: 'Enterprise Value (EVIC)', category: 'Financial', sources: ['yfinance', 'sec_edgar'], modules: ['PCAF', 'Financed Emissions', 'Factor Overlay'] },
  { id: 'deforestation_risk', name: 'Deforestation Risk Area', category: 'Nature', sources: ['wdpa_gfw'], modules: ['EUDR', 'TNFD', 'Nature Risk'] },
  { id: 'coal_capacity_mw', name: 'Coal Capacity (MW)', category: 'Energy', sources: ['gem_coal'], modules: ['Stranded Assets', 'Transition Risk'] },
  { id: 'grid_emission_factor', name: 'Grid Emission Factor (kgCO₂/kWh)', category: 'Energy', sources: ['irena_crrem'], modules: ['Carbon Calculator', 'Real Estate', 'Energy Transition'] },
];

function KPIMappingsTab() {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Platform KPI Registry</h3>
            <p className="text-xs text-gray-500 mt-0.5">Cross-module data lineage — source → platform KPI → consuming modules</p>
          </div>
          <span className="text-xs font-mono text-gray-500">{SAMPLE_KPIS.length} KPIs</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 text-gray-400 font-semibold">KPI</th>
                <th className="text-left py-2 text-gray-400 font-semibold">Category</th>
                <th className="text-left py-2 text-gray-400 font-semibold">Data Sources</th>
                <th className="text-left py-2 text-gray-400 font-semibold">Consuming Modules</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLE_KPIS.map(kpi => (
                <tr key={kpi.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2.5">
                    <div className="font-medium text-gray-800">{kpi.name}</div>
                    <div className="text-[10px] text-gray-400 font-mono">{kpi.id}</div>
                  </td>
                  <td className="py-2.5">
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold text-white" style={{ background: CATEGORY_COLORS[kpi.category] || '#6b7280' }}>
                      {kpi.category}
                    </span>
                  </td>
                  <td className="py-2.5">
                    <div className="flex flex-wrap gap-1">
                      {kpi.sources.map(s => (
                        <span key={s} className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 text-[9px] font-semibold border border-blue-200">{s}</span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2.5">
                    <div className="flex flex-wrap gap-1">
                      {kpi.modules.map(m => (
                        <span key={m} className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 text-[9px] font-semibold">{m}</span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════════════════════════════
export default function DataHubIngestionPage() {
  const [activeTab, setActiveTab] = useState('status');
  const [ingesters, setIngesters] = useState(FALLBACK_INGESTERS);
  const [jobs, setJobs] = useState(FALLBACK_JOBS);
  const [triggering, setTriggering] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [ingRes, jobRes] = await Promise.allSettled([
        axios.get(`${API}/api/v1/ingestion/ingesters`),
        axios.get(`${API}/api/v1/ingestion/jobs?limit=20`),
      ]);
      if (ingRes.status === 'fulfilled' && ingRes.value.data?.ingesters) {
        setIngesters(ingRes.value.data.ingesters);
      }
      if (jobRes.status === 'fulfilled' && Array.isArray(jobRes.value.data?.jobs)) {
        setJobs(jobRes.value.data.jobs);
      }
    } catch { /* keep fallback */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleTrigger = async (sourceId) => {
    setTriggering(sourceId);
    try {
      if (sourceId === '__all__') {
        await axios.post(`${API}/api/v1/ingestion/trigger-all`, { only_enabled: true, async_mode: true });
      } else {
        await axios.post(`${API}/api/v1/ingestion/trigger`, { source_id: sourceId, async_mode: true });
      }
      setTimeout(fetchData, 2000);
    } catch { /* silent */ }
    finally { setTimeout(() => setTriggering(null), 1500); }
  };

  return (
    <div className="min-h-screen bg-white">
      <DemoBanner message="Ingester status and sync history shown are fallback sample values. Live data will appear once the backend ingestion manager is running and connected." />
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Data Hub — Ingestion Monitor</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {ingesters.length} data sources · {(ingesters.reduce((s, i) => s + (i.records_last_run || 0), 0) / 1000).toFixed(0)}k records last sync
            </p>
          </div>
          <button onClick={fetchData} disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-300 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition disabled:opacity-60">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        <div className="flex gap-1 mt-4 overflow-x-auto">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${active ? 'bg-black text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-6">
        {activeTab === 'status' && <IngesterStatusTab ingesters={ingesters} onTrigger={handleTrigger} triggering={triggering} />}
        {activeTab === 'jobs' && <SyncHistoryTab jobs={jobs} />}
        {activeTab === 'catalog' && <SourceCatalogTab ingesters={ingesters} />}
        {activeTab === 'scheduler' && <SchedulerTab ingesters={ingesters} />}
        {activeTab === 'kpis' && <KPIMappingsTab />}
      </div>
    </div>
  );
}
