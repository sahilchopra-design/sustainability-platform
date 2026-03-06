from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, JSON,
    ForeignKey, Enum as SAEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ── Enums ───────────────────────────────────────────────────────────────────

class SourceStatus(str, enum.Enum):
    active = "active"
    configuring = "configuring"
    planned = "planned"
    paused = "paused"
    error = "error"

class AccessType(str, enum.Enum):
    rest_api = "REST API"
    csv_download = "CSV Download"
    web_scrape = "Web Scrape"
    apify = "Apify Scraper"
    python_library = "Python Library"
    oauth_api = "OAuth API"
    s3_download = "S3 Download"
    manual = "Manual"

class Priority(str, enum.Enum):
    p0 = "P0"
    p1 = "P1"
    p2 = "P2"

class Utility(str, enum.Enum):
    benchmarking = "benchmarking"
    referencing = "referencing"
    approximation = "approximation"
    supplementary = "supplementary"

class SyncStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    skipped = "skipped"

class DataQuality(str, enum.Enum):
    actual = "actual"
    estimated = "estimated"
    proxy = "proxy"


# ── Tables ──────────────────────────────────────────────────────────────────

class DataSource(Base):
    __tablename__ = "dh_data_sources"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100))
    sub_category = Column(String(100))
    description = Column(Text)
    rationale = Column(Text)

    # Connection
    access_type = Column(String(50))
    base_url = Column(Text)
    key_endpoints = Column(Text)
    auth_method = Column(String(100))       # "API Key", "OAuth 2.0", "None", etc.
    auth_detail = Column(Text)
    auth_signup_url = Column(Text)
    sample_request = Column(Text)
    sdk_library = Column(Text)
    docs_url = Column(Text)
    integration_notes = Column(Text)
    response_format = Column(Text)

    # Credentials (stored as JSON, encrypted in prod)
    credentials = Column(JSON, default={})  # {"api_key": "...", "client_id": "..."}

    # Metadata
    cost = Column(String(50))
    rate_limit = Column(String(100))
    rate_limit_detail = Column(Text)
    data_format = Column(String(50))
    update_freq = Column(String(50))
    geographic = Column(String(100))
    quality_rating = Column(String(10))     # A+, A, B+, B, etc.
    batch = Column(Integer)

    # Status & assessment
    status = Column(String(20), default="planned")
    priority = Column(String(5))            # P0, P1, P2
    utility = Column(String(50))            # benchmarking, referencing, approximation, supplementary
    assessment_score = Column(Float)
    skip_assessment = Column(Boolean, default=False)

    # Sync config
    sync_enabled = Column(Boolean, default=False)
    sync_schedule = Column(String(50))      # cron expression
    last_synced_at = Column(DateTime(timezone=True))
    last_sync_status = Column(String(20))
    last_sync_error = Column(Text)
    est_rows_month = Column(Integer)
    est_gb_month = Column(Float)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    fields = relationship("SourceField", back_populates="source", cascade="all, delete-orphan")
    assessments = relationship("SourceAssessment", back_populates="source", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="source", cascade="all, delete-orphan")
    kpi_mappings = relationship("KpiMapping", back_populates="source", cascade="all, delete-orphan")


class SourceField(Base):
    __tablename__ = "dh_source_fields"

    id = Column(String, primary_key=True, default=gen_uuid)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(255), nullable=False)
    field_path = Column(String(500))        # JSON path, e.g. "data.emissions.scope1"
    data_type = Column(String(50))          # string, number, date, boolean, array
    description = Column(Text)
    unit = Column(String(100))
    sample_values = Column(JSON)            # list of sample values
    is_primary_key = Column(Boolean, default=False)
    is_nullable = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("DataSource", back_populates="fields")
    __table_args__ = (UniqueConstraint("source_id", "field_name"),)


class ApplicationKpi(Base):
    __tablename__ = "dh_application_kpis"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    category = Column(String(100))          # emissions, financial, risk, esg, regulatory
    sub_category = Column(String(100))
    description = Column(Text)
    unit = Column(String(100))
    data_type = Column(String(50))          # number, string, percentage, rating, boolean
    target_modules = Column(JSON)           # ["portfolio_analytics", "carbon_calculator", ...]
    tags = Column(JSON)                     # ["scope1", "ghg", "carbon", ...]
    is_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    mappings = relationship("KpiMapping", back_populates="kpi", cascade="all, delete-orphan")


class KpiMapping(Base):
    __tablename__ = "dh_kpi_mappings"

    id = Column(String, primary_key=True, default=gen_uuid)
    kpi_id = Column(String, ForeignKey("dh_application_kpis.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False)
    source_field_id = Column(String, ForeignKey("dh_source_fields.id", ondelete="SET NULL"), nullable=True)

    # Priority chain
    priority_order = Column(Integer, default=1)     # 1=primary, 2=fallback1, 3=fallback2
    is_active = Column(Boolean, default=True)

    # Transformation
    transform_formula = Column(Text)        # e.g. "value * 1000" or "value / revenue"
    unit_from = Column(String(50))
    unit_to = Column(String(50))

    # Approximation
    approximation_method = Column(String(100))  # "direct", "peer_average", "sector_proxy", "ratio"
    approximation_assumption = Column(Text)
    confidence_score = Column(Float)        # 0.0–1.0

    # Version tracking (never overwrite)
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    replaced_by_id = Column(String, ForeignKey("dh_kpi_mappings.id"), nullable=True)
    change_note = Column(Text)
    created_by = Column(String(255), default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    kpi = relationship("ApplicationKpi", back_populates="mappings")
    source = relationship("DataSource", back_populates="kpi_mappings")
    source_field = relationship("SourceField")
    __table_args__ = (Index("ix_kpi_mapping_active", "kpi_id", "source_id", "is_current"),)


class ReferenceData(Base):
    __tablename__ = "dh_reference_data"

    id = Column(String, primary_key=True, default=gen_uuid)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="SET NULL"), nullable=True)
    kpi_id = Column(String, ForeignKey("dh_application_kpis.id", ondelete="SET NULL"), nullable=True)
    mapping_id = Column(String, ForeignKey("dh_kpi_mappings.id", ondelete="SET NULL"), nullable=True)

    # Entity
    entity_name = Column(String(500))
    entity_id = Column(String(255))         # LEI, ISIN, ticker, etc.
    entity_type = Column(String(100))       # company, fund, country, sector

    # KPI value
    kpi_name = Column(String(255))
    value = Column(Text)                    # stored as text, typed by data_type
    value_numeric = Column(Float)
    unit = Column(String(100))

    # Provenance
    date = Column(DateTime(timezone=True))
    period = Column(String(50))             # "2024", "Q3-2024", "2024-01", etc.
    geography = Column(String(100))
    sector = Column(String(100))
    source_name = Column(String(255))
    source_field = Column(String(255))

    # Quality
    data_quality = Column(String(20), default="actual")  # actual, estimated, proxy
    confidence_score = Column(Float)
    transform_applied = Column(Text)
    approximation_method = Column(String(100))
    assumptions = Column(Text)

    # Sync provenance
    sync_job_id = Column(String, ForeignKey("dh_sync_jobs.id", ondelete="SET NULL"), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_ref_data_kpi_entity", "kpi_name", "entity_id"),
        Index("ix_ref_data_source", "source_id"),
        Index("ix_ref_data_date", "date"),
    )


class SyncJob(Base):
    __tablename__ = "dh_sync_jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False)
    triggered_by = Column(String(50), default="scheduler")  # "scheduler", "manual", "api"
    status = Column(String(20), default="pending")

    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)

    rows_fetched = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_skipped = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)

    error_message = Column(Text)
    error_detail = Column(JSON)
    validation_errors = Column(JSON)    # null checks, range violations
    log_output = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("DataSource", back_populates="sync_jobs")


class SourceAssessment(Base):
    __tablename__ = "dh_source_assessments"

    id = Column(String, primary_key=True, default=gen_uuid)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False)

    # Scoring breakdown
    total_score = Column(Float)
    quality_score = Column(Float)
    cost_score = Column(Float)
    access_score = Column(Float)
    freshness_score = Column(Float)
    coverage_score = Column(Float)
    integration_effort_score = Column(Float)

    # Classification outputs
    priority = Column(String(5))            # P0, P1, P2
    utility = Column(String(50))
    value_description = Column(Text)
    key_datapoints = Column(JSON)           # ["scope1_tco2e", "carbon_price", ...]
    target_modules = Column(JSON)

    # Fallback chain
    fallback_sources = Column(JSON)         # [{"source": "name", "method": "...", "assumption": "..."}]

    # Multi-dimensional utility classification
    # {primary, tangential, complementary_role, supplementary_role, use_case_tags}
    utility_dimensions = Column(JSON)

    # Meta
    assessed_by = Column(String(50), default="auto")  # "auto" or "manual"
    is_current = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("DataSource", back_populates="assessments")


class QueryLog(Base):
    __tablename__ = "dh_query_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    query_type = Column(String(20))         # "builder", "nl", "saved"
    query_payload = Column(JSON)
    nl_text = Column(Text)

    # Results
    result_count = Column(Integer)
    execution_ms = Column(Integer)
    sources_used = Column(JSON)

    user_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SavedQuery(Base):
    __tablename__ = "dh_saved_queries"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    query_payload = Column(JSON, nullable=False)
    nl_text = Column(Text)
    tags = Column(JSON)
    is_public = Column(Boolean, default=False)
    run_count = Column(Integer, default=0)
    created_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
