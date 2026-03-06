from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# ── Enums ───────────────────────────────────────────────────────────────────

class SourceStatus(str, Enum):
    active = "active"
    configuring = "configuring"
    planned = "planned"
    paused = "paused"
    error = "error"

class Priority(str, Enum):
    p0 = "P0"
    p1 = "P1"
    p2 = "P2"

class Utility(str, Enum):
    benchmarking = "benchmarking"
    referencing = "referencing"
    approximation = "approximation"
    supplementary = "supplementary"

class DataQuality(str, Enum):
    actual = "actual"
    estimated = "estimated"
    proxy = "proxy"


# ── DataSource ───────────────────────────────────────────────────────────────

class DataSourceBase(BaseModel):
    name: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    rationale: Optional[str] = None
    access_type: Optional[str] = None
    base_url: Optional[str] = None
    key_endpoints: Optional[str] = None
    auth_method: Optional[str] = None
    auth_detail: Optional[str] = None
    auth_signup_url: Optional[str] = None
    sample_request: Optional[str] = None
    sdk_library: Optional[str] = None
    docs_url: Optional[str] = None
    integration_notes: Optional[str] = None
    response_format: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = {}
    cost: Optional[str] = None
    rate_limit: Optional[str] = None
    rate_limit_detail: Optional[str] = None
    data_format: Optional[str] = None
    update_freq: Optional[str] = None
    geographic: Optional[str] = None
    quality_rating: Optional[str] = None
    batch: Optional[int] = None
    status: Optional[str] = "planned"
    priority: Optional[str] = None
    utility: Optional[str] = None
    skip_assessment: Optional[bool] = False
    sync_enabled: Optional[bool] = False
    sync_schedule: Optional[str] = None
    est_rows_month: Optional[int] = None
    est_gb_month: Optional[float] = None

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(DataSourceBase):
    name: Optional[str] = None

class DataSourceOut(DataSourceBase):
    id: str
    assessment_score: Optional[float] = None
    last_synced_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    mapped_kpi_count: Optional[int] = 0
    sync_job_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── SourceField ──────────────────────────────────────────────────────────────

class SourceFieldBase(BaseModel):
    source_id: str
    field_name: str
    field_path: Optional[str] = None
    data_type: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    sample_values: Optional[List[Any]] = None
    is_primary_key: Optional[bool] = False
    is_nullable: Optional[bool] = True

class SourceFieldCreate(SourceFieldBase):
    pass

class SourceFieldOut(SourceFieldBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── ApplicationKpi ───────────────────────────────────────────────────────────

class KpiBase(BaseModel):
    name: str
    slug: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    data_type: Optional[str] = None
    target_modules: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    is_required: Optional[bool] = False

class KpiCreate(KpiBase):
    pass

class KpiUpdate(KpiBase):
    name: Optional[str] = None
    slug: Optional[str] = None

class KpiOut(KpiBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    primary_sources: Optional[List[str]] = []
    mapping_count: Optional[int] = 0

    class Config:
        from_attributes = True

class KpiFinderResult(BaseModel):
    kpi: KpiOut
    primary_sources: List[str]
    fallback_sources: List[str]
    mapping_status: str     # "mapped", "partial", "unmapped"
    approximation_method: Optional[str] = None
    consuming_modules: List[str]


# ── KpiMapping ────────────────────────────────────────────────────────────────

class MappingBase(BaseModel):
    kpi_id: str
    source_id: str
    source_field_id: Optional[str] = None
    priority_order: Optional[int] = 1
    is_active: Optional[bool] = True
    transform_formula: Optional[str] = None
    unit_from: Optional[str] = None
    unit_to: Optional[str] = None
    approximation_method: Optional[str] = None
    approximation_assumption: Optional[str] = None
    confidence_score: Optional[float] = None
    change_note: Optional[str] = None
    created_by: Optional[str] = "system"

class MappingCreate(MappingBase):
    pass

class MappingUpdate(BaseModel):
    source_field_id: Optional[str] = None
    priority_order: Optional[int] = None
    is_active: Optional[bool] = None
    transform_formula: Optional[str] = None
    unit_from: Optional[str] = None
    unit_to: Optional[str] = None
    approximation_method: Optional[str] = None
    approximation_assumption: Optional[str] = None
    confidence_score: Optional[float] = None
    change_note: Optional[str] = None

class MappingOut(MappingBase):
    id: str
    version: int
    is_current: bool
    kpi_name: Optional[str] = None
    source_name: Optional[str] = None
    source_field_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class MappingPreview(BaseModel):
    kpi_name: str
    source_name: str
    field_name: str
    sample_values: Optional[List[Any]] = None
    transform_formula: Optional[str] = None
    transformed_samples: Optional[List[Any]] = None
    confidence_score: Optional[float] = None


# ── ReferenceData ────────────────────────────────────────────────────────────

class ReferenceDataOut(BaseModel):
    id: str
    entity_name: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    kpi_name: Optional[str] = None
    value: Optional[str] = None
    value_numeric: Optional[float] = None
    unit: Optional[str] = None
    date: Optional[datetime] = None
    period: Optional[str] = None
    geography: Optional[str] = None
    sector: Optional[str] = None
    source_name: Optional[str] = None
    source_field: Optional[str] = None
    data_quality: Optional[str] = None
    confidence_score: Optional[float] = None
    approximation_method: Optional[str] = None
    transform_applied: Optional[str] = None
    ingested_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Query ─────────────────────────────────────────────────────────────────────

class QueryFilter(BaseModel):
    kpi_names: Optional[List[str]] = None
    entity_names: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    source_ids: Optional[List[str]] = None
    geographies: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    data_quality: Optional[List[str]] = None
    min_confidence: Optional[float] = None
    period: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0

class NLQueryRequest(BaseModel):
    text: str
    limit: Optional[int] = 100

class QueryResponse(BaseModel):
    results: List[ReferenceDataOut]
    total: int
    execution_ms: int
    sources_used: List[str]
    filters_applied: Dict[str, Any]

class SavedQueryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    query_payload: Dict[str, Any]
    nl_text: Optional[str] = None
    tags: Optional[List[str]] = []
    is_public: Optional[bool] = False
    created_by: Optional[str] = None

class SavedQueryOut(SavedQueryCreate):
    id: str
    run_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── SyncJob ───────────────────────────────────────────────────────────────────

class SyncJobOut(BaseModel):
    id: str
    source_id: str
    source_name: Optional[str] = None
    triggered_by: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    rows_skipped: int
    rows_failed: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SyncTriggerResponse(BaseModel):
    job_id: str
    source_id: str
    source_name: str
    status: str
    message: str


# ── Assessment ────────────────────────────────────────────────────────────────

class UtilityDimensions(BaseModel):
    """Multi-dimensional utility classification for a data source."""
    primary: str                                    # benchmarking | referencing | approximation | supplementary
    tangential: str                                 # secondary analytical role
    complementary_role: Optional[str] = None        # how this source enriches/validates other sources
    supplementary_role: Optional[str] = None        # monitoring/context/verification role
    use_case_tags: Optional[List[str]] = []         # specific named platform use-cases


class AssessmentOut(BaseModel):
    id: str
    source_id: str
    source_name: Optional[str] = None
    total_score: Optional[float] = None
    quality_score: Optional[float] = None
    cost_score: Optional[float] = None
    access_score: Optional[float] = None
    freshness_score: Optional[float] = None
    coverage_score: Optional[float] = None
    integration_effort_score: Optional[float] = None
    priority: Optional[str] = None
    utility: Optional[str] = None
    utility_dimensions: Optional[UtilityDimensions] = None
    value_description: Optional[str] = None
    key_datapoints: Optional[List[str]] = []
    target_modules: Optional[List[str]] = []
    fallback_sources: Optional[List[Dict]] = []
    assessed_by: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Analytics ────────────────────────────────────────────────────────────────

class AnalyticsOverview(BaseModel):
    total_sources: int
    active_sources: int
    error_sources: int
    paused_sources: int
    planned_sources: int
    configuring_sources: int
    total_kpis: int
    mapped_kpis: int
    unmapped_kpis: int
    mapping_coverage_pct: float
    total_reference_rows: int
    p0_sources: int
    p1_sources: int
    p2_sources: int
    last_sync_24h: int
    failed_syncs_24h: int

class MappingCoverage(BaseModel):
    kpi_id: str
    kpi_name: str
    category: str
    primary_mapped: bool
    fallback_count: int
    modules: List[str]
    coverage_status: str    # "full", "partial", "unmapped"

class DataQualityDist(BaseModel):
    actual: int
    estimated: int
    proxy: int
    actual_pct: float
    estimated_pct: float
    proxy_pct: float

class TopItem(BaseModel):
    name: str
    count: int

class ConnectionTestResult(BaseModel):
    source_id: str
    source_name: str
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None
    sample_data: Optional[Any] = None
