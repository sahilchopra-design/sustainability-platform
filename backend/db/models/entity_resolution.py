"""
Entity Resolution ORM models — GLEIF LEI + Sanctions + Screening.

Maps to tables created by Session 8 migration:
  - entity_lei          — Legal Entity Identifiers from GLEIF
  - entity_sanctions    — Consolidated sanctions from OpenSanctions (OFAC/EU/UN)
  - entity_screening_results — Match results from entity screening
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Date, Float, Integer, String, Text, JSON,
    ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from db.base import Base


class EntityLei(Base):
    """Legal Entity Identifier from GLEIF — ISO 17442."""
    __tablename__ = "entity_lei"

    lei = Column(String(20), primary_key=True)
    legal_name = Column(Text, nullable=False)
    legal_name_language = Column(String(10))
    other_names = Column(JSON)
    status = Column(String(30))
    entity_category = Column(String(50))
    legal_form_code = Column(String(10))
    legal_form_name = Column(Text)
    jurisdiction = Column(String(10))
    registered_address = Column(JSON)
    headquarters_address = Column(JSON)
    registration_authority_id = Column(String(50))
    registration_authority_entity_id = Column(String(100))
    entity_creation_date = Column(Date)
    entity_expiration_date = Column(Date)
    # LEI registration metadata
    managing_lou = Column(String(20))
    initial_registration_date = Column(Date)
    last_update_date = Column(Date)
    next_renewal_date = Column(Date)
    registration_status = Column(String(30))
    # Parent/ownership
    direct_parent_lei = Column(String(20))
    ultimate_parent_lei = Column(String(20))
    direct_parent_relationship = Column(String(50))
    ultimate_parent_relationship = Column(String(50))
    # Ingestion metadata
    source_id = Column(String)
    sync_job_id = Column(String)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class EntitySanction(Base):
    """Sanctions entry from OpenSanctions (OFAC SDN, EU FSL, UN SC, etc.)."""
    __tablename__ = "entity_sanctions"

    id = Column(String, primary_key=True)
    schema_type = Column(String(50))
    caption = Column(Text)
    names = Column(JSON)
    birth_date = Column(String(50))
    nationalities = Column(JSON)
    countries = Column(JSON)
    identifiers = Column(JSON)
    addresses = Column(JSON)
    datasets = Column(JSON, nullable=False)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    last_change = Column(DateTime(timezone=True))
    associates = Column(JSON)
    sanction_programs = Column(JSON)
    topics = Column(JSON)
    lei = Column(String(20))
    # Ingestion metadata
    source_id = Column(String)
    sync_job_id = Column(String)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class EntityScreeningResult(Base):
    """Result of screening an entity name against sanctions lists."""
    __tablename__ = "entity_screening_results"

    id = Column(String, primary_key=True)
    entity_name = Column(Text, nullable=False)
    entity_type = Column(String(50))
    entity_identifier = Column(String(100))
    matched_sanction_id = Column(String, ForeignKey("entity_sanctions.id", ondelete="SET NULL"))
    match_score = Column(Float)
    match_method = Column(String(30))
    match_details = Column(JSON)
    screening_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(30), default="pending")
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    portfolio_id = Column(String)
    asset_id = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
