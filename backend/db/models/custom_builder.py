"""
Custom Scenario Builder models — works with ALL hub scenarios (not just NGFS).
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey,
    Text, Boolean, JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from db.base import Base


class CustomScenario(Base):
    __tablename__ = "custom_scenarios_v2"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    base_scenario_id = Column(String, ForeignKey("hub_scenarios.id", ondelete="SET NULL"))
    user_id = Column(String(255), default="default_user")
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    is_fork = Column(Boolean, default=False)
    forked_from_id = Column(String, ForeignKey("custom_scenarios_v2.id", ondelete="SET NULL"), nullable=True)
    tags = Column(JSON, default=list)
    # Calculated impacts cached
    calculated_impacts = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    customizations = relationship("ParameterCustomization", back_populates="custom_scenario", cascade="all, delete-orphan")
    simulations = relationship("SimulationRun", back_populates="custom_scenario", cascade="all, delete-orphan")


class ParameterCustomization(Base):
    __tablename__ = "parameter_customizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    custom_scenario_id = Column(String, ForeignKey("custom_scenarios_v2.id", ondelete="CASCADE"), nullable=False)
    variable_name = Column(String(255), nullable=False)
    region = Column(String(255), default="World")
    original_values = Column(JSON, default=dict)  # {year: value}
    customized_values = Column(JSON, default=dict)  # {year: value}
    interpolation_method = Column(String(50), default="linear")
    reason = Column(Text)

    custom_scenario = relationship("CustomScenario", back_populates="customizations")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    custom_scenario_id = Column(String, ForeignKey("custom_scenarios_v2.id", ondelete="CASCADE"), nullable=False)
    simulation_type = Column(String(50), default="quick")  # quick, full, monte_carlo
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    iterations = Column(Integer, default=1000)
    time_horizons = Column(JSON, default=list)
    results = Column(JSON, default=dict)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))

    custom_scenario = relationship("CustomScenario", back_populates="simulations")
