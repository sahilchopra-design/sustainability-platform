"""
SQLAlchemy models for PostgreSQL.

These models mirror the structure of the current MongoDB/Beanie models
to ensure data compatibility during migration.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, Text, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from db.postgres import Base


# Enums
class AssetTypeEnum(str, enum.Enum):
    BOND = "Bond"
    LOAN = "Loan"
    EQUITY = "Equity"


class SectorEnum(str, enum.Enum):
    POWER_GENERATION = "Power Generation"
    OIL_GAS = "Oil & Gas"
    METALS_MINING = "Metals & Mining"
    AUTOMOTIVE = "Automotive"
    AIRLINES = "Airlines"
    REAL_ESTATE = "Real Estate"


# Models
class Portfolio(Base):
    """Portfolio containing multiple assets"""
    __tablename__ = "portfolios"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    assets = relationship("Asset", back_populates="portfolio", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="portfolio", cascade="all, delete-orphan")
    file_uploads = relationship("FileUpload", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, name={self.name})>"


class Asset(Base):
    """Individual asset within a portfolio"""
    __tablename__ = "assets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Asset details
    asset_type = Column(SQLEnum(AssetTypeEnum), nullable=False)
    
    # Company information (denormalized for simplicity)
    company_name = Column(String, nullable=False)
    company_sector = Column(SQLEnum(SectorEnum), nullable=False, index=True)
    company_subsector = Column(String, nullable=True)
    
    # Financial metrics
    exposure = Column(Float, nullable=False)  # Exposure at Default (EAD)
    market_value = Column(Float, nullable=False)
    base_pd = Column(Float, nullable=False)  # Probability of Default
    base_lgd = Column(Float, nullable=False)  # Loss Given Default
    rating = Column(String, nullable=False)
    maturity_years = Column(Integer, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="assets")
    
    # Indexes
    __table_args__ = (
        Index("ix_assets_portfolio_sector", "portfolio_id", "company_sector"),
    )
    
    def __repr__(self):
        return f"<Asset(id={self.id}, company={self.company_name}, type={self.asset_type})>"


class ScenarioSeries(Base):
    """Climate scenario time-series data"""
    __tablename__ = "scenario_series"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Scenario dimensions
    year = Column(Integer, nullable=False, index=True)
    scenario = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False)
    region = Column(String, nullable=False, index=True)
    variable = Column(String, nullable=False, index=True)
    
    # Data
    unit = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    source_version = Column(String, nullable=False)
    
    # Indexes for common query patterns
    __table_args__ = (
        Index("ix_scenario_lookup", "scenario", "variable", "region", "year"),
        Index("ix_scenario_year", "scenario", "year"),
    )
    
    def __repr__(self):
        return f"<ScenarioSeries(scenario={self.scenario}, year={self.year}, variable={self.variable})>"


class AnalysisRun(Base):
    """Scenario analysis run and results"""
    __tablename__ = "analysis_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_name = Column(String, nullable=False)
    
    # Analysis parameters (stored as JSON arrays)
    scenarios = Column(JSONB, nullable=False)
    horizons = Column(JSONB, nullable=False)
    
    # Status
    status = Column(String, default="completed", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="analysis_runs")
    results = relationship("ScenarioResult", back_populates="analysis_run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisRun(id={self.id}, portfolio={self.portfolio_name}, status={self.status})>"


class ScenarioResult(Base):
    """Results for a specific scenario and horizon"""
    __tablename__ = "scenario_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_run_id = Column(String, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scenario details
    scenario = Column(String, nullable=False, index=True)
    horizon = Column(Integer, nullable=False, index=True)
    
    # Risk metrics
    expected_loss = Column(Float, nullable=False)
    expected_loss_pct = Column(Float, nullable=False)
    risk_adjusted_return = Column(Float, nullable=False)
    avg_pd_change_pct = Column(Float, nullable=False)
    
    # Rating migrations (stored as JSONB)
    rating_migrations = Column(JSONB, nullable=False)
    
    # VaR and concentration
    var_95 = Column(Float, nullable=False)
    concentration_hhi = Column(Float, nullable=False)
    total_exposure = Column(Float, nullable=False)
    
    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="results")
    
    # Indexes
    __table_args__ = (
        Index("ix_results_run_scenario", "analysis_run_id", "scenario", "horizon"),
    )
    
    def __repr__(self):
        return f"<ScenarioResult(scenario={self.scenario}, horizon={self.horizon}, el={self.expected_loss})>"
