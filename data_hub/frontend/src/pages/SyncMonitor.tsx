import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, Play, CheckCircle2, XCircle, Clock, AlertTriangle, Loader2 } from 'lucide-react'
import { syncApi, sourcesApi } from '@/lib/api'
import type { SyncJob, DataSource } from '@/types'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import { fmtDateTime, fmtDuration } from '@/lib/utils'
import toast from 'react-hot-toast'

type StatusFilter = 'all' | 'running' | 'success' | 'failed' | 'pending' | 'skipped'

function SyncStatusIcon({ status }: { status: string }) {
  const map: Record<string, { icon: React.ReactNode; color: string }> = {
    success: { icon: <CheckCircle2 size={13} />, color: 'text-hub-success' },
    failed:  { icon: <XCircle size={13} />,      color: 'text-hub-error' },
    running: { icon: <Loader2 size={13} className="animate-spin" />, color: 'text-hub-accent' },
    pending: { icon: <Clock size={13} />,         color: 'text-hub-text-muted' },
    skipped: { icon: <AlertTriangle size={13} />, color: 'text-hub-warning' },
  }
  const c = map[status] ?? { icon: <Clock size={13} />, color: 'text-hub-text-muted' }
  return <span className={c.color}>{c.icon}</span>
}

function SyncStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    success: 'bg-hub-success/10 text-hub-success',
    failed:  'bg-hub-error/10  text-hub-error',
    running: 'bg-hub-accent/10 text-hub-accent',
    pending: 'bg-hub-muted     text-hub-text-muted',
    skipped: 'bg-hub-warning/10 text-hub-warning',
  }
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded capitalize ${styles[status] ?? styles.pending}`}>
      <SyncStatusIcon status={status} />
      {status}
    </span>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div className="card p-3">
      <div className="section-title">{label}</div>
      <div className={`text-2xl font-semibold font-mono mt-1 ${color ?? 'text-hub-text-primary'}`}>{value.toLocaleString()}</div>
    </div>
  )
}

export default function SyncMonitor() {
  const [jobs, setJobs] = useState<SyncJob[]>([])
  const [sources, setSources] = useState<DataSource[]>([])
  const [stats, setStats] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sourceFilter, setSourceFilter] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [triggering, setTriggering] = useState<string | null>(null)

  const fetchData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const [jobData, statsData, sourceData] = await Promise.all([
        syncApi.listJobs({ limit: 200 }),
        syncApi.getStats(),
        sourcesApi.list({ limit: 200 }),
      ])
      setJobs(jobData)
      setStats(statsData)
      setSources(sourceData)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(() => fetchData(true), 15000)
    return () => clearInterval(interval)
  }, [fetchData])

  const triggerSync = async (sourceId: string) => {
    setTriggering(sourceId)
    try {
      const res = await sourcesApi.refresh(sourceId)
      toast.success(`Sync triggered: ${res.source_name}`)
      await fetchData(true)
    } finally {
      setTriggering(null)
    }
  }

  const filteredJobs = jobs.filter(j => {
    if (statusFilter !== 'all' && j.status !== statusFilter) return false
    if (sourceFilter && !j.source_name?.toLowerCase().includes(sourceFilter.toLowerCase())) return false
    return true
  })

  const activeSources = sources.filter(s => s.sync_enabled)

  return (
    <div className="flex flex-col gap-5 h-full animate-fade-in overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-hub-text-primary">Sync Monitor</h1>
          <p className="text-sm text-hub-text-muted mt-0.5">Track data source synchronisation jobs</p>
        </div>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="btn-ghost text-[12px] flex items-center gap-1.5"
        >
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard label="Total Jobs" value={stats.total ?? 0} />
        <StatCard label="Running" value={stats.running ?? 0} color="text-hub-accent" />
        <StatCard label="Success" value={stats.success ?? 0} color="text-hub-success" />
        <StatCard label="Failed" value={stats.failed ?? 0} color="text-hub-error" />
        <StatCard label="Pending" value={stats.pending ?? 0} />
        <StatCard label="Rows Fetched" value={stats.total_rows_fetched ?? 0} />
      </div>

      {/* Sync-enabled sources */}
      {activeSources.length > 0 && (
        <div className="card p-4">
          <div className="section-title mb-3">Sync-Enabled Sources ({activeSources.length})</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {activeSources.map(s => (
              <div key={s.id} className="flex items-center justify-between gap-2 px-3 py-2 rounded border border-hub-border bg-hub-bg/50">
                <div className="min-w-0">
                  <div className="text-[12px] font-medium text-hub-text-primary truncate">{s.name}</div>
                  <div className="text-[10px] text-hub-text-muted">
                    {s.sync_schedule ?? 'Manual'} · {s.last_sync_status
                      ? <span className={s.last_sync_status === 'success' ? 'text-hub-success' : 'text-hub-error'}>{s.last_sync_status}</span>
                      : 'Never synced'}
                  </div>
                </div>
                <button
                  onClick={() => triggerSync(s.id)}
                  disabled={triggering === s.id}
                  className="flex-shrink-0 p-1.5 rounded text-hub-text-muted hover:text-hub-primary hover:bg-hub-primary/10 transition-colors disabled:opacity-50"
                  title="Trigger sync"
                >
                  {triggering === s.id
                    ? <Loader2 size={13} className="animate-spin text-hub-primary" />
                    : <Play size={13} />}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex gap-1 bg-hub-muted/40 rounded p-0.5">
          {(['all', 'running', 'success', 'failed', 'pending', 'skipped'] as StatusFilter[]).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`text-[11px] px-2.5 py-1 rounded capitalize transition-colors ${
                statusFilter === s ? 'bg-hub-card text-hub-text-primary font-medium' : 'text-hub-text-muted hover:text-hub-text-secondary'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <input
          className="input text-[12px] w-48"
          placeholder="Filter by source..."
          value={sourceFilter}
          onChange={e => setSourceFilter(e.target.value)}
        />
        <span className="text-[11px] text-hub-text-muted ml-auto">
          {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Job list */}
      <div className="card flex-1 overflow-auto">
        {loading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : filteredJobs.length === 0 ? (
          <EmptyState
            icon={<RefreshCw size={22} />}
            title="No sync jobs"
            description={statusFilter !== 'all' ? `No ${statusFilter} jobs found.` : 'No sync jobs recorded yet.'}
          />
        ) : (
          <table className="w-full text-[12px] border-collapse">
            <thead>
              <tr className="bg-hub-muted/50 sticky top-0">
                {['Status', 'Source', 'Triggered By', 'Started', 'Duration', 'Fetched', 'Inserted', 'Updated', 'Failed', ''].map(h => (
                  <th key={h} className="text-left px-3 py-2 text-[11px] font-medium text-hub-text-muted whitespace-nowrap border-b border-hub-border">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-hub-border/40">
              {filteredJobs.map(job => (
                <>
                  <tr
                    key={job.id}
                    className={`hover:bg-hub-muted/20 transition-colors cursor-pointer ${expanded === job.id ? 'bg-hub-muted/20' : ''}`}
                    onClick={() => setExpanded(expanded === job.id ? null : job.id)}
                  >
                    <td className="px-3 py-2.5 whitespace-nowrap"><SyncStatusBadge status={job.status} /></td>
                    <td className="px-3 py-2.5 text-hub-text-primary font-medium max-w-[180px] truncate">{job.source_name ?? job.source_id}</td>
                    <td className="px-3 py-2.5 text-hub-text-muted capitalize">{job.triggered_by}</td>
                    <td className="px-3 py-2.5 text-hub-text-muted whitespace-nowrap">{job.started_at ? fmtDateTime(job.started_at) : '—'}</td>
                    <td className="px-3 py-2.5 font-mono text-hub-text-secondary whitespace-nowrap">
                      {job.duration_seconds != null ? fmtDuration(job.duration_seconds) : '—'}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-hub-text-secondary">{job.rows_fetched.toLocaleString()}</td>
                    <td className="px-3 py-2.5 font-mono text-hub-success">{job.rows_inserted.toLocaleString()}</td>
                    <td className="px-3 py-2.5 font-mono text-hub-accent">{job.rows_updated.toLocaleString()}</td>
                    <td className="px-3 py-2.5 font-mono text-hub-error">{job.rows_failed.toLocaleString()}</td>
                    <td className="px-3 py-2.5">
                      <button
                        onClick={e => { e.stopPropagation(); triggerSync(job.source_id) }}
                        disabled={triggering === job.source_id}
                        title="Re-trigger sync"
                        className="p-1 rounded text-hub-text-muted hover:text-hub-primary hover:bg-hub-primary/10 transition-colors"
                      >
                        {triggering === job.source_id
                          ? <Loader2 size={12} className="animate-spin" />
                          : <Play size={12} />}
                      </button>
                    </td>
                  </tr>

                  {expanded === job.id && (
                    <tr key={`${job.id}-exp`} className="bg-hub-bg/50">
                      <td colSpan={10} className="px-5 py-3">
                        <div className="grid grid-cols-2 gap-4 text-[11px]">
                          <div className="space-y-1.5">
                            <div className="text-[10px] font-medium text-hub-text-muted uppercase tracking-wider mb-2">Job Details</div>
                            <div><span className="text-hub-text-muted">Job ID:</span> <span className="font-mono text-hub-text-secondary">{job.id}</span></div>
                            <div><span className="text-hub-text-muted">Source ID:</span> <span className="font-mono text-hub-text-secondary">{job.source_id}</span></div>
                            <div><span className="text-hub-text-muted">Started:</span> <span className="text-hub-text-secondary">{job.started_at ? fmtDateTime(job.started_at) : '—'}</span></div>
                            <div><span className="text-hub-text-muted">Completed:</span> <span className="text-hub-text-secondary">{job.completed_at ? fmtDateTime(job.completed_at) : '—'}</span></div>
                            <div><span className="text-hub-text-muted">Rows skipped:</span> <span className="font-mono text-hub-text-secondary">{job.rows_skipped.toLocaleString()}</span></div>
                          </div>
                          {job.error_message && (
                            <div className="space-y-1.5">
                              <div className="text-[10px] font-medium text-hub-error uppercase tracking-wider mb-2">Error</div>
                              <pre className="text-[11px] text-hub-error font-mono bg-hub-error/5 rounded p-2 whitespace-pre-wrap max-h-32 overflow-y-auto">
                                {job.error_message}
                              </pre>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
