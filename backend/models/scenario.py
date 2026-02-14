"""
Scenario models for climate scenario analysis.

Supports NGFS data integration, versioning, and approval workflows.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from backend.db.base import Base


class ScenarioSource(str, enum.Enum):
    """Source of scenario data."""
    NGFS = "ngfs"
    CUSTOM = "custom"
    HYBRID = "hybrid"


class ScenarioApprovalStatus(str, enum.Enum):
    """Approval status for scenarios."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class NGFSScenarioType(str, enum.Enum):
    """NGFS scenario types."""
    NET_ZERO_2050 = "net_zero_2050"
    DELAYED_TRANSITION = "delayed_transition"
    BELOW_2C = "below_2c"
    NATIONALLY_DETERMINED_CONTRIBUTIONS = "ndc"
    CURRENT_POLICIES = "current_policies"
    FRAGMENTED_WORLD = "fragmented_world"


class Scenario(Base):
    """Climate scenario for risk analysis."""
    
    __tablename__ = "scenarios"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Source information
    source = Column(SQLEnum(ScenarioSource), nullable=False, default=ScenarioSource.CUSTOM)
    ngfs_scenario_type = Column(SQLEnum(NGFSScenarioType), nullable=True)
    ngfs_version = Column(String(50), nullable=True)  # e.g., "Phase IV"
    base_scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)  # For forks
    
    # Approval workflow
    approval_status = Column(SQLEnum(ScenarioApprovalStatus), default=ScenarioApprovalStatus.DRAFT, nullable=False)
    submitted_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Version tracking
    current_version = Column(Integer, default=1, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    
    # Scenario parameters (JSON)
    parameters = Column(JSON, nullable=False, default=dict)
    # Structure: {
    #   "carbon_price": {"2025": 50, "2030": 100, "2050": 300},  # USD/tCO2
    #   "temperature_pathway": {"2025": 1.2, "2030": 1.5, "2050": 1.8},  # °C
    #   "gdp_impact": {"2025": -0.5, "2030": -1.2, "2050": -2.5},  # % change
    #   "sectoral_multipliers": {"energy": 1.5, "transport": 1.2, "agriculture": 1.3},
    #   "physical_risk": {"flood": 1.2, "drought": 1.1, "heatwave": 1.15}
    # }
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    versions = relationship("ScenarioVersion", back_populates="scenario", cascade="all, delete-orphan")
    impact_previews = relationship("ScenarioImpactPreview", back_populates="scenario", cascade="all, delete-orphan")
    base_scenario = relationship("Scenario", remote_side=[id], backref="forks")


class ScenarioVersion(Base):
    """Version history for scenarios."""
    
    __tablename__ = "scenario_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    
    # Snapshot of parameters at this version
    parameters = Column(JSON, nullable=False)
    
    # Change tracking
    change_summary = Column(Text, nullable=True)  # Human-readable summary
    changed_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    scenario = relationship("Scenario", back_populates="versions")


class ScenarioImpactPreview(Base):
    """Preview of scenario impact on a portfolio."""
    
    __tablename__ = "scenario_impact_previews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Impact summary (JSON)
    impact_summary = Column(JSON, nullable=False)
    # Structure: {
    #   "total_exposure": 1000000000,
    #   "baseline_expected_loss": 50000000,
    #   "scenario_expected_loss": 75000000,
    #   "expected_loss_change": 25000000,
    #   "expected_loss_change_pct": 50.0,
    #   "by_sector": {
    #     "energy": {"baseline_el": 20000000, "scenario_el": 35000000, "change_pct": 75.0},
    #     "transport": {"baseline_el": 15000000, "scenario_el": 20000000, "change_pct": 33.3}
    #   },
    #   "by_rating": {...},
    #   "top_impacted_holdings": [{"counterparty": "X", "change_pct": 120}]
    # }
    
    # Calculation metadata
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    calculation_version = Column(String(50), default="1.0", nullable=False)
    
    # Relationships
    scenario = relationship("Scenario", back_populates="impact_previews")
    # portfolio relationship defined in portfolios model


class NGFSDataSource(Base):
    """NGFS data source metadata and sync status."""
    
    __tablename__ = "ngfs_data_sources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)  # e.g., "NGFS Phase IV"
    url = Column(String(512), nullable=False)  # Download URL
    version = Column(String(50), nullable=False)  # e.g., "4.0"
    release_date = Column(DateTime(timezone=True), nullable=True)
    
    # Sync status
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(50), default="pending")  # pending, success, failed
    last_sync_error = Column(Text, nullable=True)
    sync_count = Column(Integer, default=0)
    
    # Data metadata
    scenario_count = Column(Integer, default=0)
    data_hash = Column(String(64), nullable=True)  # SHA256 for change detection
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
