import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, Plus, RefreshCw, Filter, ChevronDown,
  ExternalLink, Zap, Trash2, TestTube, X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { sourcesApi } from '@/lib/api'
import type { DataSource, SourceStatus, Priority } from '@/types'
import StatusBadge from '@/components/ui/StatusBadge'
import PriorityBadge from '@/components/ui/PriorityBadge'
import UtilityBadge from '@/components/ui/UtilityBadge'
import ScoreBar from '@/components/ui/ScoreBar'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import { fmt, fmtRelative } from '@/lib/utils'

const CATEGORIES = [
  'Financial Data', 'Macro', 'ESG Data', 'ESG Ratings', 'ESG Framework',
  'Regulatory', 'Government', 'Reference', 'Governance', 'News',
  'News & Events', 'Financial News', 'News & Text', 'Social', 'Social Media',
  'Consumer', 'Employment', 'Employee Data', 'Academic', 'Technology',
  'Geopolitical', 'Compliance', 'Search Data',
]

export default function DataSources() {
  const navigate = useNavigate()
  const [sources, setSources] = useState<DataSource[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [refreshingId, setRefreshingId] = useState<string | null>(null)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await sourcesApi.list({
        search: search || undefined,
        status: filterStatus || undefined,
        category: filterCategory || undefined,
        priority: filterPriority || undefined,
        limit: 200,
      })
      setSources(data)
    } finally {
      setLoading(false)
    }
  }, [search, filterStatus, filterCategory, filterPriority])

  useEffect(() => { load() }, [load])

  const handleRefresh = async (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation()
    setRefreshingId(id)
    try {
      const res = await sourcesApi.refresh(id)
      toast.success(`Sync triggered for ${name}`)
    } catch {
      // error handled in api.ts
    } finally {
      setRefreshingId(null)
    }
  }

  const handleTest = async (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation()
    setTestingId(id)
    try {
      const res = await sourcesApi.testConnection(id)
      if (res.success) {
        toast.success(`Connected to ${name} (${res.response_time_ms}ms)`)
      } else {
        toast.error(`Connection failed: ${res.error}`)
      }
    } finally {
      setTestingId(null)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation()
    if (!confirm(`Delete source "${name}"? This cannot be undone.`)) return
    try {
      await sourcesApi.delete(id)
      toast.success('Source deleted')
      setSources(s => s.filter(x => x.id !== id))
    } catch {
      // handled
    }
  }

  const clearFilters = () => {
    setFilterStatus('')
    setFilterCategory('')
    setFilterPriority('')
    setSearch('')
  }

  const hasFilters = filterStatus || filterCategory || filterPriority || search

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-hub-text-primary">Data Sources</h1>
          <p className="text-sm text-hub-text-muted mt-0.5">{fmt(sources.length)} sources</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/sources/new')}>
          <Plus size={15} />
          Add Source
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-hub-text-muted" />
          <input
            className="input pl-9"
            placeholder="Search sources..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-hub-text-muted hover:text-hub-text-primary">
              <X size={12} />
            </button>
          )}
        </div>

        <select className="select w-40" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All statuses</option>
          {['active', 'configuring', 'planned', 'paused', 'error'].map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>

        <select className="select w-44" value={filterCategory} onChange={e => setFilterCategory(e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <select className="select w-32" value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
          <option value="">All priorities</option>
          {['P0', 'P1', 'P2'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>

        {hasFilters && (
          <button onClick={clearFilters} className="btn-ghost text-hub-error hover:bg-hub-error/10 text-xs">
            <X size={12} />
            Clear
          </button>
        )}

        <button onClick={load} className="btn-ghost ml-auto" title="Reload">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="md" /></div>
        ) : sources.length === 0 ? (
          <EmptyState
            title="No sources found"
            description="Try adjusting filters or add a new data source."
            action={<button className="btn-primary" onClick={() => navigate('/sources/new')}><Plus size={14} />Add Source</button>}
          />
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-hub-border">
                {['Name', 'Category', 'Status', 'Priority', 'Utility', 'Score', 'Last Sync', 'KPIs', ''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-hub-text-muted uppercase tracking-wider first:pl-5 last:pr-5 last:text-right whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-hub-border/50">
              {sources.map(s => (
                <tr
                  key={s.id}
                  className="table-row-hover"
                  onClick={() => navigate(`/sources/${s.id}`)}
                >
                  <td className="px-4 py-3 pl-5">
                    <div className="text-sm font-medium text-hub-text-primary leading-tight">{s.name}</div>
                    {s.sub_category && (
                      <div className="text-[11px] text-hub-text-muted">{s.sub_category}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[12px] text-hub-text-secondary">{s.category || '—'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="px-4 py-3">
                    {s.priority ? <PriorityBadge priority={s.priority} /> : <span className="text-hub-text-muted text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    {s.utility ? <UtilityBadge utility={s.utility} compact /> : <span className="text-hub-text-muted text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3 w-28">
                    {s.assessment_score != null ? (
                      <ScoreBar score={s.assessment_score} showValue size="sm" />
                    ) : <span className="text-hub-text-muted text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[12px] text-hub-text-secondary">{fmtRelative(s.last_synced_at)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[12px] font-mono text-hub-text-secondary">{s.mapped_kpi_count ?? 0}</span>
                  </td>
                  <td className="px-4 py-3 pr-5">
                    <div className="flex items-center gap-1 justify-end" onClick={e => e.stopPropagation()}>
                      <button
                        className="btn-ghost p-1.5"
                        title="Test connection"
                        onClick={e => handleTest(e, s.id, s.name)}
                        disabled={testingId === s.id}
                      >
                        {testingId === s.id ? <Spinner size="sm" /> : <TestTube size={13} />}
                      </button>
                      <button
                        className="btn-ghost p-1.5"
                        title="Trigger refresh"
                        onClick={e => handleRefresh(e, s.id, s.name)}
                        disabled={refreshingId === s.id}
                      >
                        {refreshingId === s.id
                          ? <Spinner size="sm" />
                          : <RefreshCw size={13} />
                        }
                      </button>
                      <button
                        className="btn-ghost p-1.5 hover:bg-hub-error/10 hover:text-hub-error"
                        title="Delete"
                        onClick={e => handleDelete(e, s.id, s.name)}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
