"""
ORM model for tracking uploaded CSRD PDF reports.

Mirrors the csrd_report_uploads table created in migration 016.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from datetime import datetime, timezone
import uuid

from db.base import Base


class CsrdReportUpload(Base):
    """Tracks each CSRD PDF report uploaded for ESRS KPI extraction."""
    __tablename__ = "csrd_report_uploads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(512), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(Integer)

    # User-supplied metadata at upload time
    entity_name_override = Column(String(512))
    reporting_year_override = Column(Integer)
    primary_sector = Column(String(64), default="other")
    country_iso = Column(String(3), default="UNK")

    # Linked after successful ingestion
    entity_registry_id = Column(String(36), index=True)

    # Processing status: uploaded | processing | completed | failed
    status = Column(String(32), default="uploaded")

    # Extraction results
    kpis_extracted = Column(Integer, default=0)
    kpis_updated = Column(Integer, default=0)
    gaps_found = Column(Integer, default=0)
    lineage_entries = Column(Integer, default=0)
    extraction_summary = Column(JSON)
    error_message = Column(Text)

    # Audit
    uploaded_by = Column(String(128), default="user")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
