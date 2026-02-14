"""
NGFS Scenario Module — dedicated PostgreSQL models for all 24 NGFS scenarios.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey,
    Text, Boolean, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from db.base import Base


class NGFSScenario(Base):
    """One of the 24 NGFS scenarios across 3 phases."""
    __tablename__ = "ngfs_scenarios_v2"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    phase = Column(Integer, nullable=False)  # 1, 2, or 3
    phase_year = Column(Integer)  # 2020, 2021, 2023
    category = Column(String(100))  # Orderly, Disorderly, Hot House World
    temperature_target = Column(Float)
    temperature_by_2100 = Column(Float)
    carbon_neutral_year = Column(Integer)
    description = Column(Text)
    key_assumptions = Column(JSON, default=dict)
    policy_implications = Column(Text)
    physical_risk_level = Column(String(50))  # Low, Moderate, High, Very High, Catastrophic
    transition_risk_level = Column(String(50))
    related_scenario_id = Column(String, ForeignKey("ngfs_scenarios_v2.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    parameters = relationship("NGFSScenarioParameter", back_populates="scenario", cascade="all, delete-orphan")
    time_series = relationship("NGFSScenarioTimeSeries", back_populates="scenario", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_ngfs_v2_phase", "phase"),)


class NGFSScenarioParameter(Base):
    """Editable parameter for a scenario."""
    __tablename__ = "ngfs_scenario_parameters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("ngfs_scenarios_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    unit = Column(String(100))
    description = Column(Text)
    category = Column(String(50))  # pricing, emissions, economic, physical, transition
    is_editable = Column(Boolean, default=True)
    min_value = Column(Float)
    max_value = Column(Float)
    default_value = Column(Float)
    step_size = Column(Float)

    scenario = relationship("NGFSScenario", back_populates="parameters")

    __table_args__ = (
        UniqueConstraint("scenario_id", "parameter_name", name="uq_ngfs_param_sc_name"),
    )


class NGFSScenarioTimeSeries(Base):
    """Year-by-year time series data for a scenario parameter."""
    __tablename__ = "ngfs_scenario_timeseries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("ngfs_scenarios_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    is_interpolated = Column(Boolean, default=False)
    data_source = Column(String(100), default="ngfs_official")

    scenario = relationship("NGFSScenario", back_populates="time_series")

    __table_args__ = (
        UniqueConstraint("scenario_id", "parameter_name", "year", name="uq_ngfs_ts_sc_param_yr"),
        Index("ix_ngfs_ts_sc_param", "scenario_id", "parameter_name"),
    )
