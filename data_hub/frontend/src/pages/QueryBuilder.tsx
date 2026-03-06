import { useEffect, useState, useRef } from 'react'
import {
  Database, Play, Download, Save, BookOpen, Sparkles,
  ChevronDown, ChevronUp, X, Clock
} from 'lucide-react'
import { queriesApi, sourcesApi, kpisApi } from '@/lib/api'
import type { QueryFilter, ReferenceData, QueryResponse, DataSource, ApplicationKpi, SavedQuery } from '@/types'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import { fmtDateTime, fmt } from '@/lib/utils'
import toast from 'react-hot-toast'

const QUALITIES = ['actual', 'estimated', 'proxy']
const ENTITY_TYPES = ['company', 'fund', 'country', 'sector', 'property', 'project']

type Tab = 'builder' | 'nl' | 'saved'

function Tag({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 text-[11px] bg-hub-secondary/15 text-hub-secondary px-2 py-0.5 rounded">
      {label}
      <button onClick={onRemove} className="hover:text-hub-error"><X size={9} /></button>
    </span>
  )
}

function MultiSelect({
  options, selected, onChange, placeholder,
}: {
  options: string[]
  selected: string[]
  onChange: (v: string[]) => void
  placeholder: string
}) {
  const [open, setOpen] = useState(false)
  const toggle = (v: string) =>
    onChange(selected.includes(v) ? selected.filter(x => x !== v) : [...selected, v])

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="input text-left flex items-center justify-between w-full"
      >
        <span className={`text-[12px] truncate ${selected.length ? 'text-hub-text-primary' : 'text-hub-text-muted'}`}>
          {selected.length ? selected.join(', ') : placeholder}
        </span>
        <ChevronDown size={13} className="text-hub-text-muted flex-shrink-0" />
      </button>
      {open && (
        <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-hub-card border border-hub-border rounded shadow-lg max-h-48 overflow-y-auto">
          {options.map(opt => (
            <label key={opt} className="flex items-center gap-2 px-3 py-1.5 hover:bg-hub-muted cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(opt)}
                onChange={() => toggle(opt)}
                className="accent-hub-primary w-3 h-3"
              />
              <span className="text-[12px] text-hub-text-secondary">{opt}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  )
}

export default function QueryBuilder() {
  const [tab, setTab] = useState<Tab>('builder')
  const [sources, setSources] = useState<DataSource[]>([])
  const [kpis, setKpis] = useState<ApplicationKpi[]>([])
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [nlText, setNlText] = useState('')
  const [saveOpen, setSaveOpen] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saveDesc, setSaveDesc] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(true)
  const pageRef = useRef(0)

  // Filter state
  const [kpiNames, setKpiNames] = useState<string[]>([])
  const [entityNames, setEntityNames] = useState<string>('')
  const [entityTypes, setEntityTypes] = useState<string[]>([])
  const [sourceIds, setSourceIds] = useState<string[]>([])
  const [dataQuality, setDataQuality] = useState<string[]>([])
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [minConfidence, setMinConfidence] = useState('')
  const [period, setPeriod] = useState('')
  const [limit, setLimit] = useState(100)

  useEffect(() => {
    Promise.all([
      sourcesApi.list({ limit: 200 }),
      kpisApi.list({ limit: 200 }),
      queriesApi.listSaved(),
    ]).then(([s, k, sq]) => {
      setSources(s)
      setKpis(k)
      setSavedQueries(sq)
    })
  }, [])

  const buildFilter = (): QueryFilter => ({
    kpi_names: kpiNames.length ? kpiNames : undefined,
    entity_names: entityNames.trim() ? entityNames.split(',').map(s => s.trim()).filter(Boolean) : undefined,
    entity_types: entityTypes.length ? entityTypes : undefined,
    source_ids: sourceIds.length ? sourceIds : undefined,
    data_quality: dataQuality.length ? dataQuality : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    min_confidence: minConfidence ? parseFloat(minConfidence) : undefined,
    period: period || undefined,
    limit,
    offset: pageRef.current * limit,
  })

  const runQuery = async () => {
    setLoading(true)
    pageRef.current = 0
    try {
      const res = await queriesApi.execute(buildFilter())
      setResult(res)
    } finally {
      setLoading(false)
    }
  }

  const runNL = async () => {
    if (!nlText.trim()) return
    setLoading(true)
    try {
      const res = await queriesApi.natural(nlText)
      setResult(res)
      setTab('builder')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const blob = await queriesApi.export(buildFilter(), format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `query_export_${Date.now()}.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Export failed')
    }
  }

  const handleSave = async () => {
    if (!saveName.trim()) { toast.error('Name required'); return }
    await queriesApi.saveQuery({
      name: saveName,
      description: saveDesc || undefined,
      query_payload: buildFilter(),
      nl_text: nlText || undefined,
    })
    const sq = await queriesApi.listSaved()
    setSavedQueries(sq)
    setSaveOpen(false)
    setSaveName('')
    setSaveDesc('')
    toast.success('Query saved')
  }

  const runSaved = async (q: SavedQuery) => {
    setLoading(true)
    setTab('builder')
    try {
      const res = await queriesApi.runSaved(q.id)
      setResult(res)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setKpiNames([])
    setEntityNames('')
    setEntityTypes([])
    setSourceIds([])
    setDataQuality([])
    setDateFrom('')
    setDateTo('')
    setMinConfidence('')
    setPeriod('')
    setLimit(100)
    setResult(null)
  }

  const kpiOptions = kpis.map(k => k.name)
  const sourceOptions = sources.map(s => s.id)

  return (
    <div className="flex gap-5 h-full animate-fade-in">
      {/* Left: filter panel */}
      <div className="w-72 flex-shrink-0 flex flex-col gap-3">
        <div>
          <h1 className="text-xl font-semibold text-hub-text-primary">Query Builder</h1>
          <p className="text-sm text-hub-text-muted mt-0.5">Query reference data across sources</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-hub-muted/40 rounded p-0.5">
          {(['builder', 'nl', 'saved'] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 text-[11px] py-1 rounded transition-colors capitalize ${
                tab === t ? 'bg-hub-card text-hub-text-primary font-medium' : 'text-hub-text-muted hover:text-hub-text-secondary'
              }`}
            >
              {t === 'nl' ? 'Natural Language' : t === 'saved' ? 'Saved' : 'Builder'}
            </button>
          ))}
        </div>

        {tab === 'builder' && (
          <div className="flex-1 overflow-y-auto space-y-3">
            {/* Filters toggle */}
            <button
              onClick={() => setFiltersOpen(o => !o)}
              className="w-full flex items-center justify-between px-3 py-2 rounded bg-hub-card border border-hub-border text-[12px] text-hub-text-secondary"
            >
              <span>Filters</span>
              {filtersOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>

            {filtersOpen && (
              <div className="card p-3 space-y-3">
                <div>
                  <label className="label">KPI Names</label>
                  <MultiSelect
                    options={kpiOptions}
                    selected={kpiNames}
                    onChange={setKpiNames}
                    placeholder="All KPIs"
                  />
                  {kpiNames.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {kpiNames.map(n => <Tag key={n} label={n} onRemove={() => setKpiNames(kpiNames.filter(x => x !== n))} />)}
                    </div>
                  )}
                </div>

                <div>
                  <label className="label">Entity Names <span className="text-hub-text-muted font-normal">(comma-separated)</span></label>
                  <input
                    className="input text-[12px]"
                    placeholder="Apple Inc, Tesla..."
                    value={entityNames}
                    onChange={e => setEntityNames(e.target.value)}
                  />
                </div>

                <div>
                  <label className="label">Entity Types</label>
                  <MultiSelect
                    options={ENTITY_TYPES}
                    selected={entityTypes}
                    onChange={setEntityTypes}
                    placeholder="All types"
                  />
                </div>

                <div>
                  <label className="label">Sources</label>
                  <MultiSelect
                    options={sourceOptions}
                    selected={sourceIds}
                    onChange={setSourceIds}
                    placeholder="All sources"
                  />
                  {sourceIds.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {sourceIds.map(id => {
                        const name = sources.find(s => s.id === id)?.name ?? id
                        return <Tag key={id} label={name} onRemove={() => setSourceIds(sourceIds.filter(x => x !== id))} />
                      })}
                    </div>
                  )}
                </div>

                <div>
                  <label className="label">Data Quality</label>
                  <MultiSelect
                    options={QUALITIES}
                    selected={dataQuality}
                    onChange={setDataQuality}
                    placeholder="All quality levels"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="label">Date From</label>
                    <input type="date" className="input text-[11px]" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
                  </div>
                  <div>
                    <label className="label">Date To</label>
                    <input type="date" className="input text-[11px]" value={dateTo} onChange={e => setDateTo(e.target.value)} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="label">Period</label>
                    <input className="input text-[12px]" placeholder="2024" value={period} onChange={e => setPeriod(e.target.value)} />
                  </div>
                  <div>
                    <label className="label">Min Confidence</label>
                    <input
                      className="input text-[12px]"
                      type="number" min="0" max="1" step="0.05"
                      placeholder="0.0"
                      value={minConfidence}
                      onChange={e => setMinConfidence(e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <label className="label">Row Limit</label>
                  <select className="select" value={limit} onChange={e => setLimit(Number(e.target.value))}>
                    {[50, 100, 250, 500].map(n => <option key={n} value={n}>{n} rows</option>)}
                  </select>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <button onClick={runQuery} disabled={loading} className="btn-primary flex-1 text-[12px] flex items-center justify-center gap-1.5">
                {loading ? <Spinner /> : <Play size={12} />}
                Run Query
              </button>
              <button onClick={reset} className="btn-ghost text-[12px]"><X size={13} /></button>
            </div>
          </div>
        )}

        {tab === 'nl' && (
          <div className="flex-1 space-y-3">
            <div className="card p-3 space-y-2">
              <label className="label flex items-center gap-1.5"><Sparkles size={12} className="text-hub-primary" />Natural Language Query</label>
              <textarea
                className="input text-[12px] resize-none h-28"
                placeholder={'e.g. "Scope 1 emissions for European energy companies in 2023 with actual data quality"'}
                value={nlText}
                onChange={e => setNlText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) runNL() }}
              />
              <p className="text-[10px] text-hub-text-muted">Cmd+Enter to run</p>
            </div>
            <button onClick={runNL} disabled={loading || !nlText.trim()} className="btn-primary w-full text-[12px] flex items-center justify-center gap-1.5">
              {loading ? <Spinner /> : <Sparkles size={12} />}
              Translate & Run
            </button>
          </div>
        )}

        {tab === 'saved' && (
          <div className="flex-1 overflow-y-auto card divide-y divide-hub-border/50">
            {savedQueries.length === 0 ? (
              <EmptyState icon={<BookOpen size={18} />} title="No saved queries" description="Save a query to reuse it later." />
            ) : savedQueries.map(q => (
              <div key={q.id} className="px-3 py-2.5">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-[12px] font-medium text-hub-text-primary truncate">{q.name}</div>
                    {q.description && <div className="text-[11px] text-hub-text-muted truncate">{q.description}</div>}
                    <div className="flex items-center gap-1.5 mt-1 text-[10px] text-hub-text-muted">
                      <Clock size={9} />
                      <span>{fmtDateTime(q.created_at)}</span>
                      <span>· {q.run_count} runs</span>
                    </div>
                  </div>
                  <button onClick={() => runSaved(q)} className="btn-ghost text-[11px] flex-shrink-0 flex items-center gap-1">
                    <Play size={11} />Run
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: results */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">
        {result ? (
          <>
            {/* Result header */}
            <div className="card p-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 text-[12px]">
                <span className="text-hub-text-primary font-medium">{fmt(result.total)} rows</span>
                <span className="text-hub-text-muted">{result.execution_ms}ms</span>
                {result.sources_used.length > 0 && (
                  <span className="text-hub-text-muted">
                    Sources: <span className="text-hub-text-secondary">{result.sources_used.join(', ')}</span>
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { setSaveOpen(true) }}
                  className="btn-ghost text-[12px] flex items-center gap-1.5"
                >
                  <Save size={12} />Save
                </button>
                <button onClick={() => handleExport('csv')} className="btn-ghost text-[12px] flex items-center gap-1.5">
                  <Download size={12} />CSV
                </button>
                <button onClick={() => handleExport('json')} className="btn-ghost text-[12px] flex items-center gap-1.5">
                  <Download size={12} />JSON
                </button>
              </div>
            </div>

            {/* Save dialog */}
            {saveOpen && (
              <div className="card p-3 border border-hub-primary/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[13px] font-medium text-hub-text-primary">Save Query</span>
                  <button onClick={() => setSaveOpen(false)}><X size={13} className="text-hub-text-muted" /></button>
                </div>
                <input className="input text-[12px]" placeholder="Query name *" value={saveName} onChange={e => setSaveName(e.target.value)} />
                <input className="input text-[12px]" placeholder="Description (optional)" value={saveDesc} onChange={e => setSaveDesc(e.target.value)} />
                <div className="flex justify-end gap-2">
                  <button className="btn-ghost text-[12px]" onClick={() => setSaveOpen(false)}>Cancel</button>
                  <button className="btn-primary text-[12px]" onClick={handleSave}>Save</button>
                </div>
              </div>
            )}

            {/* Data table */}
            <div className="card flex-1 overflow-auto">
              {result.results.length === 0 ? (
                <EmptyState icon={<Database size={22} />} title="No results" description="Try adjusting your filters." />
              ) : (
                <table className="w-full text-[12px] border-collapse">
                  <thead>
                    <tr className="bg-hub-muted/50 sticky top-0">
                      {['Entity', 'KPI', 'Value', 'Unit', 'Period', 'Source', 'Quality', 'Confidence', 'Date'].map(h => (
                        <th key={h} className="text-left px-3 py-2 text-[11px] font-medium text-hub-text-muted whitespace-nowrap border-b border-hub-border">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hub-border/40">
                    {result.results.map((row: ReferenceData) => (
                      <tr key={row.id} className="hover:bg-hub-muted/20 transition-colors">
                        <td className="px-3 py-2 text-hub-text-primary font-medium max-w-[160px] truncate">{row.entity_name ?? '—'}</td>
                        <td className="px-3 py-2 text-hub-text-secondary max-w-[140px] truncate">{row.kpi_name ?? '—'}</td>
                        <td className="px-3 py-2 font-mono text-hub-accent whitespace-nowrap">
                          {row.value_numeric != null
                            ? row.value_numeric.toLocaleString(undefined, { maximumFractionDigits: 4 })
                            : (row.value ?? '—')}
                        </td>
                        <td className="px-3 py-2 text-hub-text-muted font-mono">{row.unit ?? '—'}</td>
                        <td className="px-3 py-2 text-hub-text-secondary">{row.period ?? '—'}</td>
                        <td className="px-3 py-2 text-hub-text-muted max-w-[120px] truncate">{row.source_name ?? '—'}</td>
                        <td className="px-3 py-2">
                          {row.data_quality && (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                              row.data_quality === 'actual' ? 'bg-hub-success/10 text-hub-success' :
                              row.data_quality === 'estimated' ? 'bg-hub-warning/10 text-hub-warning' :
                              'bg-hub-muted text-hub-text-muted'
                            }`}>{row.data_quality}</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-hub-text-muted">
                          {row.confidence_score != null
                            ? <span className={row.confidence_score >= 0.7 ? 'text-hub-success' : 'text-hub-warning'}>{(row.confidence_score * 100).toFixed(0)}%</span>
                            : '—'}
                        </td>
                        <td className="px-3 py-2 text-hub-text-muted whitespace-nowrap">
                          {row.date ? new Date(row.date).toLocaleDateString() : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        ) : (
          <div className="card flex-1 flex items-center justify-center">
            {loading ? (
              <div className="flex flex-col items-center gap-3">
                <Spinner />
                <span className="text-[12px] text-hub-text-muted">Executing query...</span>
              </div>
            ) : (
              <EmptyState
                icon={<Database size={24} />}
                title="Run a query"
                description="Use the Builder or Natural Language tab to query your reference data."
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
