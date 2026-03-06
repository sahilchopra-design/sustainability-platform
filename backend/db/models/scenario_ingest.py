"""
ORM models for ingested scenario + target data:
  - NgfsScenarioData   -> dh_ngfs_scenario_data  (IIASA NGFS Scenario Explorer)
  - SbtiCompany        -> dh_sbti_companies       (SBTi Target Registry)
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from db.base import Base


class NgfsScenarioData(Base):
    """
    Raw NGFS scenario time-series data from the IIASA Scenario Explorer.

    Each row is one (model, scenario, variable, region, year) data-point.
    Variables include carbon price, CO2 emissions, temperature, GDP impact,
    energy mix, etc. across orderly / disorderly / hot-house-world pathways.
    """
    __tablename__ = "dh_ngfs_scenario_data"

    id          = Column(Text, primary_key=True)
    source_id   = Column(Text)  # FK to dh_data_sources (not enforced in ORM)
    model       = Column(Text, nullable=False)
    scenario    = Column(Text, nullable=False)
    variable    = Column(Text, nullable=False)
    region      = Column(Text, nullable=False, default="World")
    year        = Column(Integer, nullable=False)
    value       = Column(Float)
    unit        = Column(Text)
    category    = Column(Text)      # orderly, disorderly, hot_house_world
    phase       = Column(Integer)   # NGFS phase 1, 2, 3, 4
    raw_record  = Column(JSONB)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("model", "scenario", "variable", "region", "year",
                         name="uq_ngfs_data_composite"),
    )


class SbtiCompany(Base):
    """
    SBTi Target Registry — company-level science-based climate targets.

    Tracks commitment status, near-term and long-term targets, scope coverage,
    ambition level (1.5C / well-below-2C / 2C), and net-zero commitments.
    """
    __tablename__ = "dh_sbti_companies"

    id                       = Column(Text, primary_key=True)
    source_id                = Column(Text)
    company_name             = Column(Text, nullable=False)
    isin                     = Column(Text)
    lei                      = Column(Text)
    country                  = Column(Text)
    region                   = Column(Text)
    sector                   = Column(Text)
    industry                 = Column(Text)
    company_type             = Column(Text)          # large, sme
    target_status            = Column(Text)          # committed, targets_set, near_term, etc.
    near_term_target_year    = Column(Integer)
    near_term_scope          = Column(Text)
    near_term_ambition       = Column(Text)          # 1.5C, well_below_2C, 2C
    near_term_base_year      = Column(Integer)
    near_term_base_emissions = Column(Float)
    near_term_target_pct     = Column(Float)
    long_term_target_year    = Column(Integer)
    long_term_scope          = Column(Text)
    long_term_ambition       = Column(Text)
    net_zero_committed       = Column(Boolean, default=False)
    net_zero_year            = Column(Integer)
    date_committed           = Column(Date)
    date_near_term_approved  = Column(Date)
    date_long_term_approved  = Column(Date)
    reason_removed           = Column(Text)
    raw_record               = Column(JSONB)
    ingested_at              = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at               = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                      onupdate=lambda: datetime.now(timezone.utc))
