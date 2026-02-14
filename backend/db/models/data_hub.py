"""
Data Hub models for the Universal Scenario Data Hub.

Stores scenario data from 25+ public climate data sources (NGFS, IPCC, IEA, IRENA, etc.)
with normalized trajectories for cross-source comparison.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey,
    Text, Boolean, JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from db.base import Base


class SourceTier(str, enum.Enum):
    TIER_1 = "tier_1"  # NGFS, IPCC, IEA, IRENA
    TIER_2 = "tier_2"  # World Bank, IMF, OECD
    TIER_3 = "tier_3"  # Regional sources
    TIER_4 = "tier_4"  # Sector-specific
    TIER_5 = "tier_5"  # Academic / research
    TIER_6 = "tier_6"  # Other


class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class DataHubSource(Base):
    """A climate scenario data source organization."""

    __tablename__ = "hub_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    short_name = Column(String(50), nullable=False, unique=True)
    organization = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(512))
    api_endpoint = Column(String(512))
    tier = Column(SQLEnum(SourceTier), nullable=False, default=SourceTier.TIER_1)
    logo_url = Column(String(512))
    is_active = Column(Boolean, default=True, nullable=False)
    data_license = Column(String(255))
    coverage_regions = Column(JSON, default=list)
    coverage_variables = Column(JSON, default=list)
    update_frequency = Column(String(100))
    last_synced_at = Column(DateTime(timezone=True))
    scenario_count = Column(Integer, default=0)
    trajectory_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    scenarios = relationship("DataHubScenario", back_populates="source", cascade="all, delete-orphan")
    sync_logs = relationship("DataHubSyncLog", back_populates="source", cascade="all, delete-orphan")


class DataHubScenario(Base):
    """A climate scenario from an external source."""

    __tablename__ = "hub_scenarios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String, ForeignKey("hub_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255))
    name = Column(String(500), nullable=False, index=True)
    display_name = Column(String(500))
    description = Column(Text)
    category = Column(String(100))
    model = Column(String(255))
    version = Column(String(50))
    parameters = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    temperature_target = Column(Float)
    carbon_neutral_year = Column(Integer)
    time_horizon_start = Column(Integer)
    time_horizon_end = Column(Integer)
    regions = Column(JSON, default=list)
    variables = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_hub_scenario_source_ext"),
        Index("ix_hub_scenarios_category", "category"),
    )

    source = relationship("DataHubSource", back_populates="scenarios")
    trajectories = relationship("DataHubTrajectory", back_populates="scenario", cascade="all, delete-orphan")
    favorites = relationship("DataHubFavorite", back_populates="scenario", cascade="all, delete-orphan")


class DataHubTrajectory(Base):
    """A single time-series variable trajectory within a scenario."""

    __tablename__ = "hub_trajectories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("hub_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    variable_name = Column(String(255), nullable=False, index=True)
    variable_code = Column(String(255))
    unit = Column(String(100), nullable=False)
    region = Column(String(255), nullable=False, default="World", index=True)
    sector = Column(String(100))
    time_series = Column(JSON, nullable=False)  # {"2025": 1.2, "2030": 1.5, ...}
    interpolation_method = Column(String(50), default="linear")
    data_quality_score = Column(Integer, default=3)  # 1-5
    metadata_info = Column("metadata_info", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_hub_traj_scenario_var_region", "scenario_id", "variable_name", "region"),
    )

    scenario = relationship("DataHubScenario", back_populates="trajectories")


class DataHubComparison(Base):
    """A saved comparison between scenarios."""

    __tablename__ = "hub_comparisons"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    base_scenario_id = Column(String, ForeignKey("hub_scenarios.id", ondelete="SET NULL"))
    compare_scenario_ids = Column(JSON, default=list)
    variable_filter = Column(JSON, default=list)
    region_filter = Column(JSON, default=list)
    created_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class DataHubSyncLog(Base):
    """Log entry for a data source sync operation."""

    __tablename__ = "hub_sync_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String, ForeignKey("hub_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    sync_type = Column(String(50), default="full")  # full, incremental
    status = Column(SQLEnum(SyncStatus), nullable=False, default=SyncStatus.PENDING)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    scenarios_added = Column(Integer, default=0)
    scenarios_updated = Column(Integer, default=0)
    scenarios_deprecated = Column(Integer, default=0)
    trajectories_added = Column(Integer, default=0)
    error_message = Column(Text)

    source = relationship("DataHubSource", back_populates="sync_logs")


class DataHubFavorite(Base):
    """User bookmark for a scenario."""

    __tablename__ = "hub_favorites"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    scenario_id = Column(String, ForeignKey("hub_scenarios.id", ondelete="CASCADE"), nullable=False)
    folder = Column(String(255), default="default")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "scenario_id", name="uq_hub_fav_user_scenario"),
    )

    scenario = relationship("DataHubScenario", back_populates="favorites")
