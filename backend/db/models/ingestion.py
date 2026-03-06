"""
Ingestion ORM models — maps to dh_* tables created by the Data Hub migration.

These tables track external data sources, sync jobs, KPI definitions,
field catalogs, source assessments, KPI mappings, and ingested reference data.
"""

from __future__ import annotations

import enum
import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, String, Text, JSON,
    ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from db.base import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourcePriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"


# ── Data Source Registry ─────────────────────────────────────────────────────

class DhDataSource(Base):
    """
    External data source registry — 103+ sources catalogued with access,
    sync config, quality scores, and cost information.
    """
    __tablename__ = "dh_data_sources"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    sub_category = Column(String)
    description = Column(Text)
    rationale = Column(Text)
    access_type = Column(String)           # api, bulk_download, sdk, scrape
    base_url = Column(Text)
    key_endpoints = Column(Text)
    auth_method = Column(String)           # api_key, oauth, none
    auth_detail = Column(Text)
    auth_signup_url = Column(Text)
    sample_request = Column(Text)
    sdk_library = Column(Text)
    docs_url = Column(Text)
    integration_notes = Column(Text)
    response_format = Column(Text)
    credentials = Column(JSON)
    cost = Column(String)
    rate_limit = Column(String)
    rate_limit_detail = Column(Text)
    data_format = Column(String)
    update_freq = Column(String)
    geographic = Column(String)
    quality_rating = Column(String)
    batch = Column(Integer)
    status = Column(String)
    priority = Column(String)
    utility = Column(String)
    assessment_score = Column(Float)
    skip_assessment = Column(Boolean)
    sync_enabled = Column(Boolean)
    sync_schedule = Column(String)         # cron expression
    last_synced_at = Column(DateTime(timezone=True))
    last_sync_status = Column(String)
    last_sync_error = Column(Text)
    est_rows_month = Column(Integer)
    est_gb_month = Column(Float)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    sync_jobs = relationship("DhSyncJob", back_populates="source", cascade="all, delete-orphan")
    source_fields = relationship("DhSourceField", back_populates="source", cascade="all, delete-orphan")
    assessments = relationship("DhSourceAssessment", back_populates="source", cascade="all, delete-orphan")


# ── Sync Job Tracker ─────────────────────────────────────────────────────────

class DhSyncJob(Base):
    """
    Individual ingestion run — tracks status, row counts, errors, and log output
    for each sync attempt against a data source.
    """
    __tablename__ = "dh_sync_jobs"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_by = Column(String)          # scheduler, manual, api
    status = Column(String, default="pending")
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
    validation_errors = Column(JSON)
    log_output = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_dh_sync_jobs_source_status", "source_id", "status"),
    )

    source = relationship("DhDataSource", back_populates="sync_jobs")


# ── Application KPIs ─────────────────────────────────────────────────────────

class DhApplicationKpi(Base):
    """
    KPI definitions — the canonical list of data points the platform needs.
    Each KPI maps to one or more external source fields via DhKpiMapping.
    """
    __tablename__ = "dh_application_kpis"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    category = Column(String)
    sub_category = Column(String)
    description = Column(Text)
    unit = Column(String)
    data_type = Column(String)             # numeric, text, boolean, json
    target_modules = Column(JSON)          # ["ecl", "pcaf", "carbon"]
    tags = Column(JSON)
    is_required = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    kpi_mappings = relationship("DhKpiMapping", back_populates="kpi", cascade="all, delete-orphan")


# ── Source Field Catalog ─────────────────────────────────────────────────────

class DhSourceField(Base):
    """
    Catalog of available fields from each data source — field name, path,
    type, sample values. Used for KPI mapping.
    """
    __tablename__ = "dh_source_fields"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String, nullable=False)
    field_path = Column(String)            # JSON path or API field reference
    data_type = Column(String)
    description = Column(Text)
    unit = Column(String)
    sample_values = Column(JSON)
    is_primary_key = Column(Boolean)
    is_nullable = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    source = relationship("DhDataSource", back_populates="source_fields")


# ── Source Quality Assessment ────────────────────────────────────────────────

class DhSourceAssessment(Base):
    """
    Quality assessment of a data source — scores on quality, cost, access,
    freshness, coverage, integration effort.
    """
    __tablename__ = "dh_source_assessments"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    total_score = Column(Float)
    quality_score = Column(Float)
    cost_score = Column(Float)
    access_score = Column(Float)
    freshness_score = Column(Float)
    coverage_score = Column(Float)
    integration_effort_score = Column(Float)
    priority = Column(String)
    utility = Column(String)
    value_description = Column(Text)
    key_datapoints = Column(JSON)
    target_modules = Column(JSON)
    fallback_sources = Column(JSON)
    utility_dimensions = Column(JSON)
    assessed_by = Column(String)
    is_current = Column(Boolean)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    source = relationship("DhDataSource", back_populates="assessments")


# ── KPI → Source Mapping ─────────────────────────────────────────────────────

class DhKpiMapping(Base):
    """
    Maps an application KPI to a source field with transformation rules,
    unit conversion, and confidence scoring. Supports versioning.
    """
    __tablename__ = "dh_kpi_mappings"

    id = Column(String, primary_key=True)
    kpi_id = Column(String, ForeignKey("dh_application_kpis.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    source_field_id = Column(String, ForeignKey("dh_source_fields.id", ondelete="SET NULL"))
    priority_order = Column(Integer)       # lower = preferred source
    is_active = Column(Boolean)
    transform_formula = Column(Text)
    unit_from = Column(String)
    unit_to = Column(String)
    approximation_method = Column(String)
    approximation_assumption = Column(Text)
    confidence_score = Column(Float)       # 0.0 - 1.0
    version = Column(Integer)
    is_current = Column(Boolean)
    replaced_by_id = Column(String)
    change_note = Column(Text)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    kpi = relationship("DhApplicationKpi", back_populates="kpi_mappings")


# ── Ingested Reference Data ──────────────────────────────────────────────────

class DhReferenceData(Base):
    """
    Actual ingested data rows — normalized reference data from external sources,
    linked to KPIs and entities. This is the data store for ingested content.
    """
    __tablename__ = "dh_reference_data"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("dh_data_sources.id", ondelete="SET NULL"), index=True)
    kpi_id = Column(String, ForeignKey("dh_application_kpis.id", ondelete="SET NULL"), index=True)
    mapping_id = Column(String, ForeignKey("dh_kpi_mappings.id", ondelete="SET NULL"))
    entity_name = Column(String)
    entity_id = Column(String, index=True)
    entity_type = Column(String)           # company, country, sector, asset
    kpi_name = Column(String)
    value = Column(Text)
    value_numeric = Column(Float)
    unit = Column(String)
    date = Column(DateTime(timezone=True))
    period = Column(String)                # 2024, 2024-Q1, 2024-H1
    geography = Column(String)
    sector = Column(String)
    source_name = Column(String)
    source_field = Column(String)
    data_quality = Column(String)          # reported, estimated, proxy
    confidence_score = Column(Float)
    transform_applied = Column(Text)
    approximation_method = Column(String)
    assumptions = Column(Text)
    sync_job_id = Column(String, ForeignKey("dh_sync_jobs.id", ondelete="SET NULL"))
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_dh_refdata_entity_kpi", "entity_id", "kpi_id"),
        Index("ix_dh_refdata_source_date", "source_id", "date"),
    )


# ── Query Logs ───────────────────────────────────────────────────────────────

class DhQueryLog(Base):
    """Audit log for data hub queries."""
    __tablename__ = "dh_query_logs"

    id = Column(String, primary_key=True)
    query_type = Column(String)
    query_payload = Column(JSON)
    nl_text = Column(Text)
    result_count = Column(Integer)
    execution_ms = Column(Integer)
    sources_used = Column(JSON)
    user_id = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── Saved Queries ────────────────────────────────────────────────────────────

class DhSavedQuery(Base):
    """User-saved data hub queries for reuse."""
    __tablename__ = "dh_saved_queries"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    query_payload = Column(JSON, nullable=False)
    nl_text = Column(Text)
    tags = Column(JSON)
    is_public = Column(Boolean)
    run_count = Column(Integer, default=0)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
