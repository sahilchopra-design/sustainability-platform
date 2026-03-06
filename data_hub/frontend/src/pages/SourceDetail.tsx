import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, RefreshCw, TestTube, Edit3, ExternalLink,
  ChevronRight, Clock, Database, Layers, GitMerge, Shield,
  CheckCircle, XCircle, Zap, Info,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { sourcesApi } from '@/lib/api'
import type { DataSource, Assessment, SyncJob, SourceField } from '@/types'
import StatusBadge from '@/components/ui/StatusBadge'
import PriorityBadge from '@/components/ui/PriorityBadge'
import UtilityBadge from '@/components/ui/UtilityBadge'
import ScoreBar from '@/components/ui/ScoreBar'
import Spinner from '@/components/ui/Spinner'
import { fmt, fmtDateTime, fmtRelative, fmtDuration, truncate } from '@/lib/utils'

type Tab = 'overview' | 'assessment' | 'fields' | 'sync'

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [source, setSource] = useState<DataSource | null>(null)
  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [fields, setFields] = useState<SourceField[]>([])
  const [syncHistory, setSyncHistory] = useState<SyncJob[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [refreshing, setRefreshing] = useState(false)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      sourcesApi.get(id),
      sourcesApi.getAssessment(id).catch(() => null),
      sourcesApi.getFields(id),
      sourcesApi.getSyncHistory(id, 15),
    ]).then(([src, asmt, flds, hist]) => {
      setSource(src)
      setAssessment(asmt)
      setFields(flds)
      setSyncHistory(hist)
    }).finally(() => setLoading(false))
  }, [id])

  const handleRefresh = async () => {
    if (!id || !source) return
    setRefreshing(true)
    try {
      await sourcesApi.refresh(id)
      toast.success('Sync triggered')
    } finally {
      setRefreshing(false)
    }
  }

  const handleTest = async () => {
    if (!id || !source) return
    setTesting(true)
    try {
      const res = await sourcesApi.testConnection(id)
      if (res.success) {
        toast.success(`Connected in ${res.response_time_ms}ms`)
      } else {
        toast.error(`Failed: ${res.error}`)
      }
    } finally {
      setTesting(false)
    }
  }

  if (loading) {
    return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  }

  if (!source) {
    return <div className="text-hub-text-muted text-sm">Source not found.</div>
  }

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'assessment', label: 'Assessment' },
    { id: 'fields', label: 'Fields', count: fields.length },
    { id: 'sync', label: 'Sync History', count: syncHistory.length },
  ]

  const scoreItems = assessment ? [
    { label: 'Quality', value: assessment.quality_score },
    { label: 'Cost', value: assessment.cost_score },
    { label: 'Access', value: assessment.access_score },
    { label: 'Freshness', value: assessment.freshness_score },
    { label: 'Coverage', value: assessment.coverage_score },
    { label: 'Effort', value: assessment.integration_effort_score },
  ] : []

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-hub-text-muted">
        <Link to="/sources" className="hover:text-hub-text-primary flex items-center gap-1">
          <ArrowLeft size={14} />
          Data Sources
        </Link>
        <ChevronRight size={12} />
        <span className="text-hub-text-primary">{source.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-semibold text-hub-text-primary">{source.name}</h1>
            <StatusBadge status={source.status} size="md" />
            {source.priority && <PriorityBadge priority={source.priority} showLabel />}
          </div>
          <p className="text-sm text-hub-text-muted mt-1 leading-relaxed max-w-2xl">
            {source.description || source.rationale || '—'}
          </p>
          <div className="flex items-center gap-4 mt-2">
            {source.category && (
              <span className="text-[12px] text-hub-text-secondary">{source.category}</span>
            )}
            {source.utility && <UtilityBadge utility={source.utility} />}
            {source.batch && (
              <span className="text-[12px] text-hub-text-muted">Batch {source.batch}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {source.docs_url && (
            <a href={source.docs_url} target="_blank" rel="noopener noreferrer" className="btn-ghost">
              <ExternalLink size={14} />
              Docs
            </a>
          )}
          <button onClick={handleTest} disabled={testing} className="btn-secondary">
            {testing ? <Spinner size="sm" /> : <TestTube size={14} />}
            Test
          </button>
          <button onClick={handleRefresh} disabled={refreshing} className="btn-primary">
            {refreshing ? <Spinner size="sm" /> : <RefreshCw size={14} />}
            Sync Now
          </button>
        </div>
      </div>

      {/* Score summary */}
      {assessment && (
        <div className="card p-4 flex items-center gap-6">
          <div className="text-center">
            <div className="text-3xl font-semibold text-hub-text-primary tabular-nums">
              {assessment.total_score?.toFixed(0)}
            </div>
            <div className="text-[11px] text-hub-text-muted">Score / 100</div>
          </div>
          <div className="flex-1 grid grid-cols-3 gap-3">
            {scoreItems.map(s => (
              <ScoreBar key={s.label} label={s.label} score={s.value ?? 0} max={25} showValue size="sm" />
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-hub-border">
        <div className="flex gap-0">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === t.id
                  ? 'border-hub-primary text-hub-primary'
                  : 'border-transparent text-hub-text-muted hover:text-hub-text-secondary'
              }`}
            >
              {t.label}
              {t.count != null && t.count > 0 && (
                <span className="ml-2 text-[11px] bg-hub-muted text-hub-text-muted rounded-full px-1.5 py-0.5">
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-2 gap-6">
          {/* Connection details */}
          <div className="card p-5 space-y-4">
            <div className="section-title">Connection</div>
            <Row label="Access Type" value={source.access_type} />
            <Row label="Base URL" value={source.base_url} mono link />
            <Row label="Auth Method" value={source.auth_method} />
            <Row label="Rate Limit" value={source.rate_limit} />
            <Row label="Data Format" value={source.response_format || source.data_format} />
            {source.key_endpoints && (
              <div>
                <div className="label mb-1.5">Key Endpoints</div>
                <pre className="text-[11px] font-mono text-hub-text-secondary bg-hub-bg rounded p-2 overflow-x-auto whitespace-pre-wrap">
                  {source.key_endpoints}
                </pre>
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="card p-5 space-y-4">
            <div className="section-title">Metadata</div>
            <Row label="Cost" value={source.cost} />
            <Row label="Update Frequency" value={source.update_freq} />
            <Row label="Geographic Coverage" value={source.geographic} />
            <Row label="Quality Rating" value={source.quality_rating} />
            <Row label="Est. Rows/Month" value={source.est_rows_month ? fmt(source.est_rows_month) : undefined} />
            <Row label="Est. GB/Month" value={source.est_gb_month != null ? `${source.est_gb_month.toFixed(2)} GB` : undefined} />
            <Row label="Sync Enabled" value={source.sync_enabled ? 'Yes' : 'No'} />
            <Row label="Sync Schedule" value={source.sync_schedule} mono />
            <Row label="Created" value={fmtDateTime(source.created_at)} />
            <Row label="Last Synced" value={fmtRelative(source.last_synced_at)} />
          </div>

          {/* Integration notes */}
          {source.integration_notes && (
            <div className="card p-5 col-span-2">
              <div className="section-title">Integration Notes</div>
              <p className="text-sm text-hub-text-secondary leading-relaxed">{source.integration_notes}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'assessment' && assessment && (
        <div className="grid grid-cols-2 gap-6">
          {/* Classification */}
          <div className="card p-5 space-y-4">
            <div className="section-title">Classification</div>
            <Row label="Priority" value={<PriorityBadge priority={assessment.priority!} showLabel />} />
            <Row label="Primary Utility" value={assessment.utility ? <UtilityBadge utility={assessment.utility} /> : undefined} />
            {assessment.utility_dimensions && (
              <>
                <Row label="Tangential Utility" value={<UtilityBadge utility={assessment.utility_dimensions.tangential} />} />
                <div>
                  <div className="label mb-1.5">Complementary Role</div>
                  <p className="text-[12px] text-hub-text-secondary leading-relaxed">
                    {assessment.utility_dimensions.complementary_role || '—'}
                  </p>
                </div>
                <div>
                  <div className="label mb-1.5">Supplementary Role</div>
                  <p className="text-[12px] text-hub-text-secondary leading-relaxed">
                    {assessment.utility_dimensions.supplementary_role || '—'}
                  </p>
                </div>
                {assessment.utility_dimensions.use_case_tags && assessment.utility_dimensions.use_case_tags.length > 0 && (
                  <div>
                    <div className="label mb-1.5">Use Case Tags</div>
                    <div className="flex flex-wrap gap-1.5">
                      {assessment.utility_dimensions.use_case_tags.map(t => (
                        <span key={t} className="text-[10px] font-mono bg-hub-muted text-hub-text-secondary px-1.5 py-0.5 rounded">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Modules & datapoints */}
          <div className="card p-5 space-y-4">
            <div className="section-title">Platform Impact</div>
            {assessment.target_modules && assessment.target_modules.length > 0 && (
              <div>
                <div className="label mb-1.5">Target Modules</div>
                <div className="flex flex-wrap gap-1.5">
                  {assessment.target_modules.map(m => (
                    <span key={m} className="text-[11px] bg-hub-secondary/10 text-hub-secondary px-2 py-0.5 rounded">
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {assessment.key_datapoints && assessment.key_datapoints.length > 0 && (
              <div>
                <div className="label mb-1.5">Key Datapoints</div>
                <div className="flex flex-wrap gap-1.5">
                  {assessment.key_datapoints.map(d => (
                    <span key={d} className="text-[10px] font-mono bg-hub-muted text-hub-text-secondary px-1.5 py-0.5 rounded">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {assessment.value_description && (
              <div>
                <div className="label mb-1.5">Assessment Summary</div>
                <p className="text-[12px] text-hub-text-secondary leading-relaxed">{assessment.value_description}</p>
              </div>
            )}
          </div>

          {/* Fallback chain */}
          {assessment.fallback_sources && assessment.fallback_sources.length > 0 && (
            <div className="card p-5 col-span-2">
              <div className="section-title">Fallback Chain</div>
              <div className="space-y-3">
                {assessment.fallback_sources.map((f, i) => (
                  <div key={i} className="flex gap-3 p-3 bg-hub-bg rounded-lg border border-hub-border/50">
                    <div className="text-[11px] font-mono text-hub-text-muted w-4 mt-0.5">{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-hub-text-primary">{f.source}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] bg-hub-muted text-hub-text-secondary px-1.5 py-0.5 rounded font-mono">
                          {f.method}
                        </span>
                      </div>
                      <p className="text-[11px] text-hub-text-muted mt-1 leading-relaxed">{f.assumption}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'assessment' && !assessment && (
        <div className="card p-8 text-center">
          <Info size={20} className="text-hub-text-muted mx-auto mb-2" />
          <p className="text-sm text-hub-text-muted">No assessment yet.</p>
          <button
            className="btn-primary mt-4"
            onClick={async () => {
              const a = await sourcesApi.triggerAssessment(id!)
              setAssessment(a)
              toast.success('Assessment complete')
            }}
          >
            Run Assessment
          </button>
        </div>
      )}

      {activeTab === 'fields' && (
        <div className="card overflow-hidden">
          {fields.length === 0 ? (
            <div className="p-8 text-center text-sm text-hub-text-muted">No fields registered for this source.</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-hub-border">
                  {['Field Name', 'Path', 'Type', 'Unit', 'PK', 'Description'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-hub-text-muted uppercase tracking-wider first:pl-5">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-hub-border/50">
                {fields.map(f => (
                  <tr key={f.id}>
                    <td className="px-4 py-3 pl-5 font-mono text-[12px] text-hub-text-primary">{f.field_name}</td>
                    <td className="px-4 py-3 font-mono text-[11px] text-hub-text-muted">{f.field_path || '—'}</td>
                    <td className="px-4 py-3 text-[12px] text-hub-text-secondary">{f.data_type || '—'}</td>
                    <td className="px-4 py-3 text-[12px] text-hub-text-secondary">{f.unit || '—'}</td>
                    <td className="px-4 py-3">
                      {f.is_primary_key ? <CheckCircle size={13} className="text-hub-success" /> : <span className="text-hub-text-muted text-xs">—</span>}
                    </td>
                    <td className="px-4 py-3 text-[12px] text-hub-text-muted">{truncate(f.description, 60)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'sync' && (
        <div className="card overflow-hidden">
          {syncHistory.length === 0 ? (
            <div className="p-8 text-center text-sm text-hub-text-muted">No sync jobs yet.</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-hub-border">
                  {['Job ID', 'Triggered By', 'Status', 'Started', 'Duration', 'Fetched', 'Inserted', 'Failed', 'Error'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-hub-text-muted uppercase tracking-wider first:pl-5">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-hub-border/50">
                {syncHistory.map(j => (
                  <tr key={j.id}>
                    <td className="px-4 py-3 pl-5 font-mono text-[10px] text-hub-text-muted">{j.id.slice(0, 8)}</td>
                    <td className="px-4 py-3 text-[12px] text-hub-text-secondary capitalize">{j.triggered_by}</td>
                    <td className="px-4 py-3"><StatusBadge status={j.status} /></td>
                    <td className="px-4 py-3 text-[12px] text-hub-text-muted">{fmtRelative(j.started_at)}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-hub-text-secondary">{fmtDuration(j.duration_seconds)}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-hub-text-secondary">{fmt(j.rows_fetched)}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-hub-success">{fmt(j.rows_inserted)}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-hub-error">{fmt(j.rows_failed)}</td>
                    <td className="px-4 py-3 text-[11px] text-hub-error max-w-48 truncate" title={j.error_message}>
                      {j.error_message ? truncate(j.error_message, 40) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

function Row({ label, value, mono = false, link = false }: {
  label: string
  value?: string | number | React.ReactNode
  mono?: boolean
  link?: boolean
}) {
  if (value == null || value === '') return null
  return (
    <div className="flex items-start gap-3">
      <span className="label w-32 flex-shrink-0 pt-0.5">{label}</span>
      {typeof value === 'string' ? (
        link && value.startsWith('http') ? (
          <a href={value} target="_blank" rel="noopener noreferrer"
            className="text-[12px] text-hub-primary hover:underline font-mono break-all leading-relaxed">
            {value}
          </a>
        ) : (
          <span className={`text-[12px] text-hub-text-secondary leading-relaxed ${mono ? 'font-mono' : ''}`}>
            {value}
          </span>
        )
      ) : (
        <div className="flex-1">{value}</div>
      )}
    </div>
  )
}
