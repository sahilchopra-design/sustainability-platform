import toast from 'react-hot-toast'
import type {
  DataSource, DataSourceCreate, SourceField, SourceFieldCreate,
  ApplicationKpi, KpiFinderResult, KpiMapping,
  ReferenceData, QueryResponse,
  SyncJob, SyncTriggerResponse,
  Assessment, ConnectionTestResult,
  AnalyticsOverview, MappingCoverage,
} from '@/types'

const BASE = '/api/v1'

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const msg = err.detail || 'Request failed'
    toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// ── Sources ──────────────────────────────────────────────────────────────────

export const sourcesApi = {
  list(params?: {
    status?: string
    category?: string
    priority?: string
    search?: string
    batch?: number
    limit?: number
    offset?: number
  }): Promise<DataSource[]> {
    const q = new URLSearchParams()
    if (params?.status) q.set('status', params.status)
    if (params?.category) q.set('category', params.category)
    if (params?.priority) q.set('priority', params.priority)
    if (params?.search) q.set('search', params.search)
    if (params?.batch) q.set('batch', String(params.batch))
    if (params?.limit) q.set('limit', String(params.limit))
    if (params?.offset) q.set('offset', String(params.offset))
    return request<DataSource[]>(`/sources?${q}`)
  },

  get(id: string): Promise<DataSource> {
    return request<DataSource>(`/sources/${id}`)
  },

  create(data: DataSourceCreate): Promise<DataSource> {
    return request<DataSource>('/sources', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update(id: string, data: Partial<DataSourceCreate>): Promise<DataSource> {
    return request<DataSource>(`/sources/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  delete(id: string): Promise<void> {
    return request<void>(`/sources/${id}`, { method: 'DELETE' })
  },

  testConnection(id: string): Promise<ConnectionTestResult> {
    return request<ConnectionTestResult>(`/sources/${id}/test-connection`, {
      method: 'POST',
    })
  },

  refresh(id: string): Promise<SyncTriggerResponse> {
    return request<SyncTriggerResponse>(`/sources/${id}/refresh`, {
      method: 'POST',
    })
  },

  getFields(id: string): Promise<SourceField[]> {
    return request<SourceField[]>(`/sources/${id}/fields`)
  },

  addField(id: string, data: Omit<SourceField, 'id' | 'created_at'>): Promise<SourceField> {
    return request<SourceField>(`/sources/${id}/fields`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  getSyncHistory(id: string, limit = 20): Promise<SyncJob[]> {
    return request<SyncJob[]>(`/sources/${id}/sync-history?limit=${limit}`)
  },

  getAssessment(id: string): Promise<Assessment> {
    return request<Assessment>(`/sources/${id}/assessment`)
  },

  triggerAssessment(id: string): Promise<Assessment> {
    return request<Assessment>(`/sources/${id}/assess`, { method: 'POST' })
  },
}


// ── KPIs ─────────────────────────────────────────────────────────────────────

export const kpisApi = {
  list(params?: { category?: string; search?: string; limit?: number }): Promise<ApplicationKpi[]> {
    const q = new URLSearchParams()
    if (params?.category) q.set('category', params.category)
    if (params?.search) q.set('search', params.search)
    if (params?.limit) q.set('limit', String(params.limit))
    return request<ApplicationKpi[]>(`/kpis?${q}`)
  },

  search(query: string): Promise<KpiFinderResult[]> {
    return request<KpiFinderResult[]>(`/kpis/search?q=${encodeURIComponent(query)}`)
  },

  get(id: string): Promise<ApplicationKpi> {
    return request<ApplicationKpi>(`/kpis/${id}`)
  },

  create(data: Omit<ApplicationKpi, 'id' | 'created_at' | 'updated_at'>): Promise<ApplicationKpi> {
    return request<ApplicationKpi>('/kpis', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update(id: string, data: Partial<ApplicationKpi>): Promise<ApplicationKpi> {
    return request<ApplicationKpi>(`/kpis/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  delete(id: string): Promise<void> {
    return request<void>(`/kpis/${id}`, { method: 'DELETE' })
  },

  getMappings(id: string): Promise<KpiMapping[]> {
    return request<KpiMapping[]>(`/kpis/${id}/mappings`)
  },

  getCategories(): Promise<Record<string, number>> {
    return request<Record<string, number>>('/kpis/categories')
  },
}


// ── Mappings ─────────────────────────────────────────────────────────────────

export const mappingsApi = {
  list(params?: {
    kpi_id?: string
    source_id?: string
    is_current?: boolean
    limit?: number
  }): Promise<KpiMapping[]> {
    const q = new URLSearchParams()
    if (params?.kpi_id) q.set('kpi_id', params.kpi_id)
    if (params?.source_id) q.set('source_id', params.source_id)
    if (params?.is_current !== undefined) q.set('is_current', String(params.is_current))
    if (params?.limit) q.set('limit', String(params.limit))
    return request<KpiMapping[]>(`/mappings?${q}`)
  },

  create(data: Omit<KpiMapping, 'id' | 'version' | 'is_current' | 'created_at'>): Promise<KpiMapping> {
    return request<KpiMapping>('/mappings', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update(id: string, data: Partial<KpiMapping>): Promise<KpiMapping> {
    return request<KpiMapping>(`/mappings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  delete(id: string): Promise<void> {
    return request<void>(`/mappings/${id}`, { method: 'DELETE' })
  },

  getHistory(id: string): Promise<KpiMapping[]> {
    return request<KpiMapping[]>(`/mappings/${id}/history`)
  },

  bulkUpload(file: File): Promise<{ created: number; errors: string[] }> {
    const fd = new FormData()
    fd.append('file', file)
    return fetch(`${BASE}/mappings/bulk-upload`, {
      method: 'POST',
      body: fd,
    }).then(r => r.json())
  },
}


// ── Queries ──────────────────────────────────────────────────────────────────

export interface QueryFilter {
  kpi_names?: string[]
  entity_names?: string[]
  entity_types?: string[]
  source_ids?: string[]
  geographies?: string[]
  sectors?: string[]
  date_from?: string
  date_to?: string
  data_quality?: string[]
  min_confidence?: number
  period?: string
  limit?: number
  offset?: number
}

export const queriesApi = {
  execute(filter: QueryFilter): Promise<QueryResponse> {
    return request<QueryResponse>('/queries/execute', {
      method: 'POST',
      body: JSON.stringify(filter),
    })
  },

  natural(text: string, limit = 100): Promise<QueryResponse> {
    return request<QueryResponse>('/queries/nl', {
      method: 'POST',
      body: JSON.stringify({ text, limit }),
    })
  },

  export(filter: QueryFilter, format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    return fetch(`${BASE}/queries/export?format=${format}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filter),
    }).then(r => r.blob())
  },

  listSaved(): Promise<Array<{
    id: string; name: string; description?: string;
    query_payload: QueryFilter; nl_text?: string;
    tags?: string[]; run_count: number; created_at: string
  }>> {
    return request('/queries/saved')
  },

  saveQuery(data: {
    name: string; description?: string
    query_payload: QueryFilter; nl_text?: string
    tags?: string[]; is_public?: boolean
  }) {
    return request('/queries/saved', { method: 'POST', body: JSON.stringify(data) })
  },

  runSaved(id: string): Promise<QueryResponse> {
    return request<QueryResponse>(`/queries/saved/${id}/run`, { method: 'POST' })
  },
}


// ── Sync ─────────────────────────────────────────────────────────────────────

export const syncApi = {
  listJobs(params?: {
    source_id?: string
    status?: string
    triggered_by?: string
    limit?: number
  }): Promise<SyncJob[]> {
    const q = new URLSearchParams()
    if (params?.source_id) q.set('source_id', params.source_id)
    if (params?.status) q.set('status', params.status)
    if (params?.triggered_by) q.set('triggered_by', params.triggered_by)
    if (params?.limit) q.set('limit', String(params.limit))
    return request<SyncJob[]>(`/sync/jobs?${q}`)
  },

  getJob(id: string): Promise<SyncJob> {
    return request<SyncJob>(`/sync/jobs/${id}`)
  },

  getStats(): Promise<{
    total_jobs: number
    success_jobs: number
    failed_jobs: number
    running_jobs: number
    syncs_24h: number
    failed_24h: number
    total_rows_ingested: number
  }> {
    return request('/sync/stats')
  },
}


// ── Analytics ────────────────────────────────────────────────────────────────

export const analyticsApi = {
  getOverview(): Promise<AnalyticsOverview> {
    return request<AnalyticsOverview>('/analytics/overview')
  },

  getCoverage(): Promise<MappingCoverage[]> {
    return request<MappingCoverage[]>('/analytics/coverage')
  },

  getTopKpis(): Promise<Array<{ name: string; count: number }>> {
    return request('/analytics/top-kpis')
  },

  getTopSources(): Promise<Array<{ name: string; count: number }>> {
    return request('/analytics/top-sources')
  },

  getUnmappedKpis(): Promise<ApplicationKpi[]> {
    return request('/analytics/unmapped-kpis')
  },

  getDataQuality(): Promise<{
    actual: number; estimated: number; proxy: number
    actual_pct: number; estimated_pct: number; proxy_pct: number
  }> {
    return request('/analytics/data-quality')
  },
}
