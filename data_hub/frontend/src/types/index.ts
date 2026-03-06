// ── Enums ────────────────────────────────────────────────────────────────────

export type SourceStatus = 'active' | 'configuring' | 'planned' | 'paused' | 'error'
export type Priority = 'P0' | 'P1' | 'P2'
export type Utility = 'benchmarking' | 'referencing' | 'approximation' | 'supplementary'
export type SyncStatus = 'pending' | 'running' | 'success' | 'failed' | 'skipped'
export type DataQuality = 'actual' | 'estimated' | 'proxy'


// ── Data Source ──────────────────────────────────────────────────────────────

export interface DataSource {
  id: string
  name: string
  category?: string
  sub_category?: string
  description?: string
  rationale?: string
  access_type?: string
  base_url?: string
  key_endpoints?: string
  auth_method?: string
  auth_detail?: string
  auth_signup_url?: string
  sample_request?: string
  sdk_library?: string
  docs_url?: string
  integration_notes?: string
  response_format?: string
  credentials?: Record<string, unknown>
  cost?: string
  rate_limit?: string
  rate_limit_detail?: string
  data_format?: string
  update_freq?: string
  geographic?: string
  quality_rating?: string
  batch?: number
  status: SourceStatus
  priority?: Priority
  utility?: Utility
  assessment_score?: number
  skip_assessment?: boolean
  sync_enabled?: boolean
  sync_schedule?: string
  last_synced_at?: string
  last_sync_status?: string
  last_sync_error?: string
  est_rows_month?: number
  est_gb_month?: number
  created_at: string
  updated_at?: string
  mapped_kpi_count?: number
  sync_job_count?: number
}

export interface DataSourceCreate {
  name: string
  category?: string
  sub_category?: string
  description?: string
  rationale?: string
  access_type?: string
  base_url?: string
  key_endpoints?: string
  auth_method?: string
  auth_detail?: string
  auth_signup_url?: string
  docs_url?: string
  integration_notes?: string
  cost?: string
  update_freq?: string
  geographic?: string
  quality_rating?: string
  batch?: number
  status?: SourceStatus
  sync_enabled?: boolean
}


// ── Source Field ─────────────────────────────────────────────────────────────

export interface SourceField {
  id: string
  source_id: string
  field_name: string
  field_path?: string
  data_type?: string
  description?: string
  unit?: string
  sample_values?: unknown[]
  is_primary_key?: boolean
  is_nullable?: boolean
  created_at: string
}


// ── KPI ──────────────────────────────────────────────────────────────────────

export interface ApplicationKpi {
  id: string
  name: string
  slug: string
  category?: string
  sub_category?: string
  description?: string
  unit?: string
  data_type?: string
  target_modules?: string[]
  tags?: string[]
  is_required?: boolean
  created_at: string
  updated_at?: string
  primary_sources?: string[]
  mapping_count?: number
}

export interface KpiFinderResult {
  kpi: ApplicationKpi
  primary_sources: string[]
  fallback_sources: string[]
  mapping_status: 'mapped' | 'partial' | 'unmapped'
  approximation_method?: string
  consuming_modules: string[]
}


// ── Mapping ──────────────────────────────────────────────────────────────────

export interface KpiMapping {
  id: string
  kpi_id: string
  source_id: string
  source_field_id?: string
  priority_order: number
  is_active: boolean
  transform_formula?: string
  unit_from?: string
  unit_to?: string
  approximation_method?: string
  approximation_assumption?: string
  confidence_score?: number
  version: number
  is_current: boolean
  replaced_by_id?: string
  change_note?: string
  created_by?: string
  created_at: string
  kpi_name?: string
  source_name?: string
  source_field_name?: string
}


// ── Reference Data ────────────────────────────────────────────────────────────

export interface ReferenceData {
  id: string
  entity_name?: string
  entity_id?: string
  entity_type?: string
  kpi_name?: string
  value?: string
  value_numeric?: number
  unit?: string
  date?: string
  period?: string
  geography?: string
  sector?: string
  source_name?: string
  source_field?: string
  data_quality?: DataQuality
  confidence_score?: number
  approximation_method?: string
  transform_applied?: string
  ingested_at?: string
}

export interface QueryResponse {
  results: ReferenceData[]
  total: number
  execution_ms: number
  sources_used: string[]
  filters_applied: Record<string, unknown>
}


// ── Sync Job ─────────────────────────────────────────────────────────────────

export interface SyncJob {
  id: string
  source_id: string
  source_name?: string
  triggered_by: string
  status: SyncStatus
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  rows_fetched: number
  rows_inserted: number
  rows_updated: number
  rows_skipped: number
  rows_failed: number
  error_message?: string
  created_at: string
}

export interface SyncTriggerResponse {
  job_id: string
  source_id: string
  source_name: string
  status: string
  message: string
}


// ── Assessment ────────────────────────────────────────────────────────────────

export interface UtilityDimensions {
  primary: Utility
  tangential: Utility
  complementary_role?: string
  supplementary_role?: string
  use_case_tags?: string[]
}

export interface Assessment {
  id: string
  source_id: string
  source_name?: string
  total_score?: number
  quality_score?: number
  cost_score?: number
  access_score?: number
  freshness_score?: number
  coverage_score?: number
  integration_effort_score?: number
  priority?: Priority
  utility?: Utility
  utility_dimensions?: UtilityDimensions
  value_description?: string
  key_datapoints?: string[]
  target_modules?: string[]
  fallback_sources?: Array<{ source: string; method: string; assumption: string }>
  assessed_by: string
  notes?: string
  created_at: string
}

export interface ConnectionTestResult {
  source_id: string
  source_name: string
  success: boolean
  status_code?: number
  response_time_ms?: number
  error?: string
  sample_data?: unknown
}


// ── Analytics ────────────────────────────────────────────────────────────────

export interface AnalyticsOverview {
  total_sources: number
  active_sources: number
  error_sources: number
  paused_sources: number
  planned_sources: number
  configuring_sources: number
  total_kpis: number
  mapped_kpis: number
  unmapped_kpis: number
  mapping_coverage_pct: number
  total_reference_rows: number
  p0_sources: number
  p1_sources: number
  p2_sources: number
  last_sync_24h: number
  failed_syncs_24h: number
}

export interface MappingCoverage {
  kpi_id: string
  kpi_name: string
  category: string
  primary_mapped: boolean
  fallback_count: number
  modules: string[]
  coverage_status: 'full' | 'partial' | 'unmapped'
}


// ── Pagination ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
