import { useEffect, useState, useRef } from 'react'
import { Link2, ChevronRight, Plus, Trash2, Upload, History, CheckCircle2, AlertCircle, X, Save } from 'lucide-react'
import { kpisApi, mappingsApi, sourcesApi } from '@/lib/api'
import type { ApplicationKpi, KpiMapping, DataSource, SourceField } from '@/types'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import toast from 'react-hot-toast'

function PriorityLabel({ n }: { n: number }) {
  const labels: Record<number, { label: string; color: string }> = {
    1: { label: 'Primary',   color: 'text-hub-success' },
    2: { label: 'Fallback 1', color: 'text-hub-warning' },
    3: { label: 'Fallback 2', color: 'text-hub-text-muted' },
  }
  const c = labels[n] ?? { label: `Priority ${n}`, color: 'text-hub-text-muted' }
  return <span className={`text-[11px] font-medium ${c.color}`}>{c.label}</span>
}

type MappingForm = {
  source_id: string
  source_field_id: string
  priority_order: number
  transform_formula: string
  approximation_method: string
  approximation_assumption: string
  confidence_score: string
  change_note: string
}

const blankForm = (): MappingForm => ({
  source_id: '',
  source_field_id: '',
  priority_order: 1,
  transform_formula: '',
  approximation_method: 'direct',
  approximation_assumption: '',
  confidence_score: '',
  change_note: '',
})

export default function MappingStudio() {
  const [kpis, setKpis] = useState<ApplicationKpi[]>([])
  const [sources, setSources] = useState<DataSource[]>([])
  const [selectedKpi, setSelectedKpi] = useState<ApplicationKpi | null>(null)
  const [mappings, setMappings] = useState<KpiMapping[]>([])
  const [fields, setFields] = useState<SourceField[]>([])
  const [loadingKpis, setLoadingKpis] = useState(true)
  const [loadingMappings, setLoadingMappings] = useState(false)
  const [loadingFields, setLoadingFields] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<MappingForm>(blankForm())
  const [kpiFilter, setKpiFilter] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showHistory, setShowHistory] = useState<string | null>(null)
  const [historyData, setHistoryData] = useState<KpiMapping[]>([])
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    Promise.all([
      kpisApi.list({ limit: 200 }),
      sourcesApi.list({ limit: 200 }),
    ]).then(([k, s]) => {
      setKpis(k)
      setSources(s)
    }).finally(() => setLoadingKpis(false))
  }, [])

  const selectKpi = async (kpi: ApplicationKpi) => {
    setSelectedKpi(kpi)
    setShowForm(false)
    setEditingId(null)
    setForm(blankForm())
    setLoadingMappings(true)
    try {
      const m = await kpisApi.getMappings(kpi.id)
      setMappings(m)
    } finally {
      setLoadingMappings(false)
    }
  }

  const onSourceChange = async (sourceId: string) => {
    setForm(f => ({ ...f, source_id: sourceId, source_field_id: '' }))
    if (!sourceId) { setFields([]); return }
    setLoadingFields(true)
    try {
      const f = await sourcesApi.getFields(sourceId)
      setFields(f)
    } finally {
      setLoadingFields(false)
    }
  }

  const handleSave = async () => {
    if (!selectedKpi) return
    if (!form.source_id) { toast.error('Select a source'); return }
    setSaving(true)
    try {
      const payload = {
        kpi_id: selectedKpi.id,
        source_id: form.source_id,
        source_field_id: form.source_field_id || undefined,
        priority_order: form.priority_order,
        transform_formula: form.transform_formula || undefined,
        approximation_method: form.approximation_method || undefined,
        approximation_assumption: form.approximation_assumption || undefined,
        confidence_score: form.confidence_score ? parseFloat(form.confidence_score) : undefined,
        change_note: form.change_note || undefined,
      }
      if (editingId) {
        await mappingsApi.update(editingId, payload)
        toast.success('Mapping updated')
      } else {
        await mappingsApi.create(payload)
        toast.success('Mapping created')
      }
      const m = await kpisApi.getMappings(selectedKpi.id)
      setMappings(m)
      setShowForm(false)
      setEditingId(null)
      setForm(blankForm())
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!selectedKpi) return
    if (!confirm('Delete this mapping? This action is permanent.')) return
    await mappingsApi.delete(id)
    toast.success('Mapping deleted')
    const m = await kpisApi.getMappings(selectedKpi.id)
    setMappings(m)
  }

  const startEdit = async (mapping: KpiMapping) => {
    setEditingId(mapping.id)
    setForm({
      source_id: mapping.source_id,
      source_field_id: mapping.source_field_id ?? '',
      priority_order: mapping.priority_order ?? 1,
      transform_formula: mapping.transform_formula ?? '',
      approximation_method: mapping.approximation_method ?? 'direct',
      approximation_assumption: mapping.approximation_assumption ?? '',
      confidence_score: mapping.confidence_score != null ? String(mapping.confidence_score) : '',
      change_note: '',
    })
    if (mapping.source_id) {
      setLoadingFields(true)
      try {
        const f = await sourcesApi.getFields(mapping.source_id)
        setFields(f)
      } finally {
        setLoadingFields(false)
      }
    }
    setShowForm(true)
  }

  const loadHistory = async (mappingId: string) => {
    if (showHistory === mappingId) { setShowHistory(null); return }
    const h = await mappingsApi.getHistory(mappingId)
    setHistoryData(h)
    setShowHistory(mappingId)
  }

  const handleBulkUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    const lines = text.split('\n').filter(l => l.trim() && !l.startsWith('kpi_id'))
    let ok = 0, fail = 0
    for (const line of lines) {
      const [kpi_id, source_id, source_field_id, priority_order] = line.split(',').map(s => s.trim())
      try {
        await mappingsApi.create({ kpi_id, source_id, source_field_id: source_field_id || undefined, priority_order: Number(priority_order) || 1 })
        ok++
      } catch { fail++ }
    }
    toast.success(`Bulk upload: ${ok} created, ${fail} failed`)
    if (selectedKpi) {
      const m = await kpisApi.getMappings(selectedKpi.id)
      setMappings(m)
    }
    e.target.value = ''
  }

  const filteredKpis = kpis.filter(k =>
    !kpiFilter || k.name.toLowerCase().includes(kpiFilter.toLowerCase()) || k.category?.toLowerCase().includes(kpiFilter.toLowerCase())
  )

  return (
    <div className="flex gap-5 h-full animate-fade-in">
      {/* Left: KPI list */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-3">
        <div>
          <h1 className="text-xl font-semibold text-hub-text-primary">Mapping Studio</h1>
          <p className="text-sm text-hub-text-muted mt-0.5">Assign data sources to KPIs</p>
        </div>
        <input
          className="input text-[12px]"
          placeholder="Filter KPIs..."
          value={kpiFilter}
          onChange={e => setKpiFilter(e.target.value)}
        />
        <div className="card flex-1 overflow-y-auto">
          {loadingKpis ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : filteredKpis.length === 0 ? (
            <EmptyState icon={<Link2 size={20} />} title="No KPIs" description="No KPIs match your filter." />
          ) : (
            <div className="divide-y divide-hub-border/50">
              {filteredKpis.map(kpi => (
                <button
                  key={kpi.id}
                  onClick={() => selectKpi(kpi)}
                  className={`w-full flex items-center justify-between px-4 py-2.5 text-left transition-colors ${
                    selectedKpi?.id === kpi.id ? 'bg-hub-primary/10' : 'hover:bg-hub-muted/40'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="text-[12px] font-medium text-hub-text-primary truncate">{kpi.name}</div>
                    {kpi.category && (
                      <div className="text-[10px] text-hub-text-muted truncate">{kpi.category}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                    {(kpi.mapping_count ?? 0) > 0 ? (
                      <span className="text-[10px] font-mono text-hub-success">{kpi.mapping_count}</span>
                    ) : (
                      <span className="text-[10px] text-hub-error">0</span>
                    )}
                    <ChevronRight size={11} className={`text-hub-text-muted ${selectedKpi?.id === kpi.id ? 'text-hub-primary' : ''}`} />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: mapping editor */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">
        {!selectedKpi ? (
          <div className="card flex-1 flex items-center justify-center">
            <EmptyState
              icon={<Link2 size={24} />}
              title="Select a KPI"
              description="Choose a KPI from the left panel to view and manage its source mappings."
            />
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="card p-4 flex items-start justify-between gap-4">
              <div>
                <div className="text-[11px] text-hub-text-muted uppercase tracking-wider">{selectedKpi.category}</div>
                <h2 className="text-base font-semibold text-hub-text-primary mt-0.5">{selectedKpi.name}</h2>
                {selectedKpi.description && (
                  <p className="text-[12px] text-hub-text-muted mt-1 max-w-xl">{selectedKpi.description}</p>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleBulkUpload} />
                <button
                  onClick={() => fileRef.current?.click()}
                  className="btn-ghost text-[12px] flex items-center gap-1.5"
                >
                  <Upload size={13} />
                  Bulk CSV
                </button>
                <button
                  onClick={() => { setShowForm(true); setEditingId(null); setForm(blankForm()) }}
                  className="btn-primary text-[12px] flex items-center gap-1.5"
                >
                  <Plus size={13} />
                  Add Mapping
                </button>
              </div>
            </div>

            {/* Add/Edit form */}
            {showForm && (
              <div className="card p-4 space-y-4 border border-hub-primary/30">
                <div className="flex items-center justify-between">
                  <h3 className="text-[13px] font-medium text-hub-text-primary">
                    {editingId ? 'Edit Mapping' : 'New Mapping'}
                  </h3>
                  <button onClick={() => { setShowForm(false); setEditingId(null) }} className="text-hub-text-muted hover:text-hub-text-primary">
                    <X size={14} />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {/* Source */}
                  <div>
                    <label className="label">Data Source *</label>
                    <select
                      className="select"
                      value={form.source_id}
                      onChange={e => onSourceChange(e.target.value)}
                    >
                      <option value="">Select source...</option>
                      {sources.map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Field */}
                  <div>
                    <label className="label">Source Field</label>
                    {loadingFields ? (
                      <div className="flex items-center gap-2 text-[11px] text-hub-text-muted pt-2"><Spinner /><span>Loading fields...</span></div>
                    ) : (
                      <select
                        className="select"
                        value={form.source_field_id}
                        onChange={e => setForm(f => ({ ...f, source_field_id: e.target.value }))}
                        disabled={!form.source_id}
                      >
                        <option value="">Any field / unspecified</option>
                        {fields.map(f => (
                          <option key={f.id} value={f.id}>{f.field_name}{f.data_type ? ` (${f.data_type})` : ''}</option>
                        ))}
                      </select>
                    )}
                  </div>

                  {/* Priority */}
                  <div>
                    <label className="label">Priority Order</label>
                    <select
                      className="select"
                      value={form.priority_order}
                      onChange={e => setForm(f => ({ ...f, priority_order: Number(e.target.value) }))}
                    >
                      <option value={1}>1 — Primary</option>
                      <option value={2}>2 — Fallback 1</option>
                      <option value={3}>3 — Fallback 2</option>
                    </select>
                  </div>

                  {/* Approximation method */}
                  <div>
                    <label className="label">Approximation Method</label>
                    <select
                      className="select"
                      value={form.approximation_method}
                      onChange={e => setForm(f => ({ ...f, approximation_method: e.target.value }))}
                    >
                      <option value="direct">direct</option>
                      <option value="peer_average">peer_average</option>
                      <option value="sector_proxy">sector_proxy</option>
                      <option value="ratio">ratio</option>
                      <option value="regression">regression</option>
                      <option value="interpolation">interpolation</option>
                    </select>
                  </div>

                  {/* Transform formula */}
                  <div className="col-span-2">
                    <label className="label">Transform Formula <span className="text-hub-text-muted font-normal">(optional)</span></label>
                    <input
                      className="input font-mono text-[12px]"
                      placeholder='e.g. value * 1000  or  value / revenue * 100'
                      value={form.transform_formula}
                      onChange={e => setForm(f => ({ ...f, transform_formula: e.target.value }))}
                    />
                  </div>

                  {/* Assumption */}
                  <div className="col-span-2">
                    <label className="label">Approximation Assumption <span className="text-hub-text-muted font-normal">(optional)</span></label>
                    <input
                      className="input text-[12px]"
                      placeholder="Describe the key assumption..."
                      value={form.approximation_assumption}
                      onChange={e => setForm(f => ({ ...f, approximation_assumption: e.target.value }))}
                    />
                  </div>

                  {/* Confidence + Change note */}
                  <div>
                    <label className="label">Confidence Score <span className="text-hub-text-muted font-normal">(0–1)</span></label>
                    <input
                      className="input text-[12px]"
                      type="number" min="0" max="1" step="0.05"
                      placeholder="0.85"
                      value={form.confidence_score}
                      onChange={e => setForm(f => ({ ...f, confidence_score: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="label">Change Note</label>
                    <input
                      className="input text-[12px]"
                      placeholder="Reason for this mapping..."
                      value={form.change_note}
                      onChange={e => setForm(f => ({ ...f, change_note: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2">
                  <button className="btn-ghost text-[12px]" onClick={() => { setShowForm(false); setEditingId(null) }}>
                    Cancel
                  </button>
                  <button className="btn-primary text-[12px] flex items-center gap-1.5" onClick={handleSave} disabled={saving}>
                    {saving ? <Spinner /> : <Save size={13} />}
                    {editingId ? 'Update' : 'Create'} Mapping
                  </button>
                </div>
              </div>
            )}

            {/* Mapping list */}
            <div className="card flex-1 overflow-y-auto">
              {loadingMappings ? (
                <div className="flex justify-center py-12"><Spinner /></div>
              ) : mappings.length === 0 ? (
                <EmptyState
                  icon={<Link2 size={22} />}
                  title="No mappings"
                  description="No source mappings defined for this KPI."
                />
              ) : (
                <div className="divide-y divide-hub-border/50">
                  {mappings
                    .filter(m => m.is_current)
                    .sort((a, b) => (a.priority_order ?? 1) - (b.priority_order ?? 1))
                    .map(mapping => (
                      <div key={mapping.id}>
                        <div className="px-5 py-3.5">
                          <div className="flex items-start gap-3">
                            {/* Priority indicator */}
                            <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full mt-1.5 bg-hub-primary/60" />

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-[13px] font-medium text-hub-text-primary">{mapping.source_name}</span>
                                <PriorityLabel n={mapping.priority_order ?? 1} />
                                {mapping.source_field_name && (
                                  <span className="font-mono text-[11px] text-hub-accent bg-hub-accent/10 px-1.5 py-0.5 rounded">
                                    {mapping.source_field_name}
                                  </span>
                                )}
                                {!mapping.is_active && (
                                  <span className="text-[10px] bg-hub-error/10 text-hub-error px-1.5 py-0.5 rounded">Inactive</span>
                                )}
                              </div>

                              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5">
                                {mapping.approximation_method && (
                                  <span className="text-[11px] text-hub-text-muted">
                                    Method: <span className="font-mono text-hub-text-secondary">{mapping.approximation_method}</span>
                                  </span>
                                )}
                                {mapping.transform_formula && (
                                  <span className="text-[11px] text-hub-text-muted">
                                    Formula: <span className="font-mono text-hub-accent">{mapping.transform_formula}</span>
                                  </span>
                                )}
                                {mapping.confidence_score != null && (
                                  <span className="text-[11px] text-hub-text-muted">
                                    Confidence: <span className={`font-medium ${mapping.confidence_score >= 0.7 ? 'text-hub-success' : 'text-hub-warning'}`}>
                                      {(mapping.confidence_score * 100).toFixed(0)}%
                                    </span>
                                  </span>
                                )}
                                {mapping.version > 1 && (
                                  <span className="text-[11px] text-hub-text-muted">v{mapping.version}</span>
                                )}
                              </div>

                              {mapping.approximation_assumption && (
                                <p className="text-[11px] text-hub-text-muted mt-1 italic">{mapping.approximation_assumption}</p>
                              )}
                            </div>

                            <div className="flex items-center gap-1 flex-shrink-0">
                              <button
                                onClick={() => loadHistory(mapping.id)}
                                title="Version history"
                                className="p-1.5 rounded text-hub-text-muted hover:text-hub-text-primary hover:bg-hub-muted transition-colors"
                              >
                                <History size={13} />
                              </button>
                              <button
                                onClick={() => startEdit(mapping)}
                                className="p-1.5 rounded text-hub-text-muted hover:text-hub-primary hover:bg-hub-primary/10 transition-colors"
                              >
                                <CheckCircle2 size={13} />
                              </button>
                              <button
                                onClick={() => handleDelete(mapping.id)}
                                className="p-1.5 rounded text-hub-text-muted hover:text-hub-error hover:bg-hub-error/10 transition-colors"
                              >
                                <Trash2 size={13} />
                              </button>
                            </div>
                          </div>
                        </div>

                        {/* Version history panel */}
                        {showHistory === mapping.id && (
                          <div className="mx-5 mb-3 rounded border border-hub-border bg-hub-bg/50 p-3 space-y-2">
                            <div className="text-[11px] font-medium text-hub-text-muted uppercase tracking-wider">Version History</div>
                            {historyData.length === 0 ? (
                              <p className="text-[11px] text-hub-text-muted">No history available.</p>
                            ) : historyData.map(h => (
                              <div key={h.id} className="flex items-start gap-2 text-[11px]">
                                <span className="text-hub-text-muted font-mono">v{h.version}</span>
                                <span className="text-hub-text-secondary">{h.source_name}</span>
                                {h.change_note && <span className="text-hub-text-muted italic">— {h.change_note}</span>}
                                <span className="ml-auto text-hub-text-muted">{new Date(h.created_at).toLocaleDateString()}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              )}
            </div>

            {/* Bulk CSV hint */}
            <div className="flex items-center gap-2 text-[11px] text-hub-text-muted px-1">
              <AlertCircle size={11} />
              <span>Bulk CSV format: <span className="font-mono">kpi_id, source_id, source_field_id, priority_order</span></span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
