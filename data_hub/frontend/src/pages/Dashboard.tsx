import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer,
  Tooltip, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import {
  Database, Layers, GitMerge, RefreshCw,
  TrendingUp, AlertCircle, CheckCircle2, Clock,
  ArrowRight, Activity,
} from 'lucide-react'
import { analyticsApi, syncApi } from '@/lib/api'
import type { AnalyticsOverview, SyncJob } from '@/types'
import Spinner from '@/components/ui/Spinner'
import StatusBadge from '@/components/ui/StatusBadge'
import { fmt, fmtRelative } from '@/lib/utils'

const PALETTE = ['#7c3aed', '#4f46e5', '#06b6d4', '#10b981', '#f59e0b']

export default function Dashboard() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [recentJobs, setRecentJobs] = useState<SyncJob[]>([])
  const [topSources, setTopSources] = useState<Array<{ name: string; count: number }>>([])
  const [dqData, setDqData] = useState<{ actual: number; estimated: number; proxy: number } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsApi.getOverview(),
      syncApi.listJobs({ limit: 8 }),
      analyticsApi.getTopSources(),
      analyticsApi.getDataQuality(),
    ]).then(([ov, jobs, sources, dq]) => {
      setOverview(ov)
      setRecentJobs(jobs)
      setTopSources(sources.slice(0, 8))
      setDqData(dq)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  const statusData = overview ? [
    { name: 'Active', value: overview.active_sources, color: '#10b981' },
    { name: 'Configuring', value: overview.configuring_sources, color: '#06b6d4' },
    { name: 'Planned', value: overview.planned_sources, color: '#475569' },
    { name: 'Paused', value: overview.paused_sources, color: '#f59e0b' },
    { name: 'Error', value: overview.error_sources, color: '#ef4444' },
  ].filter(d => d.value > 0) : []

  const priorityData = overview ? [
    { name: 'P0', value: overview.p0_sources, fill: '#ef4444' },
    { name: 'P1', value: overview.p1_sources, fill: '#f59e0b' },
    { name: 'P2', value: overview.p2_sources, fill: '#475569' },
  ] : []

  const dqChartData = dqData ? [
    { name: 'Actual', value: dqData.actual, fill: '#10b981' },
    { name: 'Estimated', value: dqData.estimated, fill: '#f59e0b' },
    { name: 'Proxy', value: dqData.proxy, fill: '#7c3aed' },
  ] : []

  const stats = [
    {
      icon: Database, label: 'Total Sources', value: fmt(overview?.total_sources),
      sub: `${fmt(overview?.active_sources)} active`,
      color: 'text-hub-primary', bg: 'bg-hub-primary/10',
      link: '/sources',
    },
    {
      icon: Layers, label: 'Total KPIs', value: fmt(overview?.total_kpis),
      sub: `${overview?.mapping_coverage_pct?.toFixed(0)}% mapped`,
      color: 'text-hub-accent', bg: 'bg-hub-accent/10',
      link: '/kpis',
    },
    {
      icon: GitMerge, label: 'Active Mappings', value: fmt(overview?.mapped_kpis),
      sub: `${fmt(overview?.unmapped_kpis)} unmapped`,
      color: 'text-hub-secondary', bg: 'bg-hub-secondary/10',
      link: '/mappings',
    },
    {
      icon: RefreshCw, label: 'Syncs (24h)', value: fmt(overview?.last_sync_24h),
      sub: `${fmt(overview?.failed_syncs_24h)} failed`,
      color: overview?.failed_syncs_24h ? 'text-hub-error' : 'text-hub-success',
      bg: overview?.failed_syncs_24h ? 'bg-hub-error/10' : 'bg-hub-success/10',
      link: '/sync',
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-hub-text-primary">Overview</h1>
        <p className="text-sm text-hub-text-muted mt-0.5">Reference Data Hub — system status and coverage</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map(s => (
          <Link key={s.label} to={s.link} className="stat-card hover:border-hub-muted transition-colors group">
            <div className="flex items-start justify-between">
              <div className={`w-8 h-8 rounded-lg ${s.bg} flex items-center justify-center`}>
                <s.icon size={16} className={s.color} />
              </div>
              <ArrowRight size={14} className="text-hub-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div className="mt-3">
              <div className="text-2xl font-semibold text-hub-text-primary tabular-nums">{s.value}</div>
              <div className="text-xs text-hub-text-muted mt-0.5">{s.label}</div>
              <div className="text-xs text-hub-text-secondary mt-1">{s.sub}</div>
            </div>
          </Link>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Status distribution */}
        <div className="card p-5">
          <div className="section-title">Source Status</div>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%" cy="50%"
                innerRadius={45} outerRadius={65}
                dataKey="value"
                paddingAngle={2}
              >
                {statusData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} stroke="none" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#16162a', border: '1px solid #232340', borderRadius: 8 }}
                itemStyle={{ color: '#e2e8f0', fontSize: 12 }}
                labelStyle={{ color: '#94a3b8' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {statusData.map(d => (
              <div key={d.name} className="flex items-center gap-1.5 text-[11px] text-hub-text-secondary">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: d.color }} />
                {d.name} <span className="font-mono text-hub-text-primary">{d.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Priority distribution */}
        <div className="card p-5">
          <div className="section-title">Priority Distribution</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={priorityData} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" stroke="#232340" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#16162a', border: '1px solid #232340', borderRadius: 8 }}
                itemStyle={{ color: '#e2e8f0', fontSize: 12 }}
                cursor={{ fill: '#232340' }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {priorityData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Data quality */}
        <div className="card p-5">
          <div className="section-title">Data Quality</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={dqChartData} layout="vertical" barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" stroke="#232340" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={60} />
              <Tooltip
                contentStyle={{ background: '#16162a', border: '1px solid #232340', borderRadius: 8 }}
                itemStyle={{ color: '#e2e8f0', fontSize: 12 }}
                cursor={{ fill: '#232340' }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {dqChartData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Top sources by KPI count */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="section-title mb-0">Top Sources by KPI Coverage</div>
            <Link to="/sources" className="text-[11px] text-hub-primary hover:underline flex items-center gap-1">
              View all <ArrowRight size={10} />
            </Link>
          </div>
          <div className="space-y-2">
            {topSources.map((s, i) => (
              <div key={s.name} className="flex items-center gap-3">
                <span className="text-[10px] font-mono text-hub-text-muted w-4 text-right">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] text-hub-text-secondary truncate">{s.name}</div>
                  <div className="mt-0.5 h-1 bg-hub-muted rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: topSources[0] ? `${(s.count / topSources[0].count) * 100}%` : '0%',
                        background: PALETTE[i % PALETTE.length],
                      }}
                    />
                  </div>
                </div>
                <span className="text-[12px] font-mono text-hub-text-primary tabular-nums w-6 text-right">{s.count}</span>
              </div>
            ))}
            {topSources.length === 0 && (
              <p className="text-sm text-hub-text-muted text-center py-4">No mapping data yet</p>
            )}
          </div>
        </div>

        {/* Recent sync jobs */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="section-title mb-0">Recent Sync Jobs</div>
            <Link to="/sync" className="text-[11px] text-hub-primary hover:underline flex items-center gap-1">
              View all <ArrowRight size={10} />
            </Link>
          </div>
          {recentJobs.length === 0 ? (
            <p className="text-sm text-hub-text-muted text-center py-4">No sync jobs yet</p>
          ) : (
            <div className="space-y-1">
              {recentJobs.map(job => (
                <div key={job.id} className="flex items-center gap-3 py-1.5 border-b border-hub-border/50 last:border-0">
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] text-hub-text-primary truncate">{job.source_name || job.source_id}</div>
                    <div className="text-[11px] text-hub-text-muted">{fmtRelative(job.created_at)}</div>
                  </div>
                  <StatusBadge status={job.status} />
                  {job.rows_inserted > 0 && (
                    <span className="text-[11px] font-mono text-hub-text-muted">
                      +{fmt(job.rows_inserted)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Coverage alert */}
      {overview && overview.unmapped_kpis > 0 && (
        <div className="card p-4 flex items-center gap-3 border-hub-warning/30 bg-hub-warning/5">
          <AlertCircle size={16} className="text-hub-warning flex-shrink-0" />
          <div className="flex-1 text-sm text-hub-text-secondary">
            <span className="font-medium text-hub-text-primary">{overview.unmapped_kpis} KPIs</span>
            {' '}have no source mappings. Map them in the{' '}
            <Link to="/mappings" className="text-hub-primary hover:underline">Mapping Studio</Link>.
          </div>
          <Link to="/kpis?filter=unmapped" className="btn-ghost text-hub-warning hover:bg-hub-warning/10 text-xs">
            Review
          </Link>
        </div>
      )}
    </div>
  )
}
