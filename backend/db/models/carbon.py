"""
Carbon Credits Module - Database Models
Tables for carbon portfolios, projects, methodologies, emission factors, scenarios, and calculations.
Linked to existing portfolios but separate carbon-specific tracking.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON,
    Numeric, UniqueConstraint, Index, Enum
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from db.base import Base


class ProjectType(enum.Enum):
    RENEWABLE_ENERGY = "RENEWABLE_ENERGY"
    FOREST_CONSERVATION = "FOREST_CONSERVATION"
    AFFORESTATION = "AFFORESTATION"
    METHANE_CAPTURE = "METHANE_CAPTURE"
    COOKSTOVES = "COOKSTOVES"
    BLUE_CARBON = "BLUE_CARBON"
    SOIL_CARBON = "SOIL_CARBON"
    DIRECT_AIR_CAPTURE = "DIRECT_AIR_CAPTURE"
    BIOCHAR = "BIOCHAR"
    OTHER = "OTHER"


class CarbonStandard(enum.Enum):
    VCS = "VCS"  # Verified Carbon Standard
    GOLD_STANDARD = "GOLD_STANDARD"
    ACR = "ACR"  # American Carbon Registry
    CAR = "CAR"  # Climate Action Reserve
    CDM = "CDM"  # Clean Development Mechanism
    JCM = "JCM"  # Joint Crediting Mechanism
    CORSIA = "CORSIA"
    OTHER = "OTHER"


class CarbonMethodology(Base):
    """Carbon credit calculation methodologies (e.g., VM0007, AMS-I.D)"""
    __tablename__ = "carbon_methodology"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    standard = Column(String(50), nullable=False, index=True)  # VCS, Gold Standard, etc.
    sector = Column(String(100), nullable=False, index=True)
    subsector = Column(String(100))
    description = Column(Text)
    version = Column(String(20))
    status = Column(String(50), default="active")  # active, deprecated, superseded
    applicable_project_types = Column(JSON, default=list)
    default_parameters = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    projects = relationship("CarbonProject", back_populates="methodology")


class CarbonEmissionFactor(Base):
    """Country/region-specific emission factors"""
    __tablename__ = "carbon_emission_factor"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    country_code = Column(String(3), nullable=False, index=True)
    country_name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    grid_emission_factor = Column(Float)  # tCO2/MWh
    natural_gas_ef = Column(Float)  # tCO2/GJ
    coal_ef = Column(Float)
    oil_ef = Column(Float)
    biomass_ef = Column(Float)
    source = Column(String(255))  # Data source (e.g., IEA, IPCC)
    is_default = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint("country_code", "year", name="uq_emission_factor_country_year"),
    )


class CarbonPortfolio(Base):
    """Carbon credit portfolio - can link to existing climate portfolios"""
    __tablename__ = "carbon_portfolio"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    linked_portfolio_id = Column(String, ForeignKey("portfolios_pg.id", ondelete="SET NULL"), nullable=True)
    owner_id = Column(String, index=True)
    status = Column(String(50), default="active")  # active, archived
    target_annual_credits = Column(Float, default=0)
    budget_usd = Column(Float, default=0)
    vintage_preference = Column(JSON, default=list)  # Preferred vintage years
    quality_minimum = Column(String(10), default="BBB")  # Minimum quality rating
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    
    projects = relationship("CarbonProject", back_populates="portfolio", cascade="all, delete-orphan")
    scenarios = relationship("CarbonScenario", back_populates="portfolio", cascade="all, delete-orphan")
    calculations = relationship("CarbonCalculation", back_populates="portfolio", cascade="all, delete-orphan")


class CarbonProject(Base):
    """Individual carbon credit project"""
    __tablename__ = "carbon_project"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("carbon_portfolio.id", ondelete="CASCADE"), nullable=False, index=True)
    methodology_id = Column(String, ForeignKey("carbon_methodology.id"), nullable=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    project_type = Column(String(50), nullable=False, index=True)
    standard = Column(String(50), nullable=False)  # VCS, Gold Standard, etc.
    registry_id = Column(String(100))  # External registry project ID
    
    # Location
    country_code = Column(String(3), nullable=False, index=True)
    region = Column(String(100))
    coordinates = Column(JSON)  # {lat, lng}
    
    # Credits
    annual_credits = Column(Float, default=0)  # Expected annual tCO2e
    total_credits = Column(Float, default=0)  # Total expected credits
    issued_credits = Column(Float, default=0)  # Already issued
    retired_credits = Column(Float, default=0)  # Already retired
    vintage_start = Column(Integer)  # First crediting year
    vintage_end = Column(Integer)  # Last crediting year
    crediting_period_years = Column(Integer, default=10)
    
    # Quality & Risk
    quality_rating = Column(String(10))  # AAA, AA, A, BBB, BB, B, CCC
    quality_score = Column(Float)  # 0-5 numeric score
    risk_level = Column(String(20))  # Low, Medium, High
    risk_score = Column(Float)  # 0-100
    additionality_score = Column(Float)
    permanence_score = Column(Float)
    co_benefits_score = Column(Float)
    
    # Financial
    price_per_credit_usd = Column(Float)
    total_investment_usd = Column(Float)
    
    # Status
    status = Column(String(50), default="active")  # active, suspended, completed
    verification_status = Column(String(50), default="unverified")  # verified, pending, unverified
    last_verification_date = Column(DateTime(timezone=True))
    
    # Metadata
    sdg_contributions = Column(JSON, default=list)  # List of SDG numbers
    co_benefits = Column(JSON, default=list)
    documents = Column(JSON, default=list)  # Links to documentation
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    
    portfolio = relationship("CarbonPortfolio", back_populates="projects")
    methodology = relationship("CarbonMethodology", back_populates="projects")


class CarbonScenario(Base):
    """Scenario for carbon credit projections"""
    __tablename__ = "carbon_scenario"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("carbon_portfolio.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    
    # Risk adjustments
    permanence_risk_pct = Column(Float, default=10.0)  # % buffer for permanence risk
    delivery_risk_pct = Column(Float, default=5.0)
    regulatory_risk_pct = Column(Float, default=5.0)
    market_risk_pct = Column(Float, default=10.0)
    
    # Price assumptions
    base_carbon_price_usd = Column(Float, default=15.0)
    price_growth_rate_pct = Column(Float, default=5.0)  # Annual growth
    price_volatility_pct = Column(Float, default=20.0)
    
    # Discount rate
    discount_rate_pct = Column(Float, default=8.0)
    
    # Time horizon
    projection_years = Column(Integer, default=10)
    
    parameters = Column(JSON, default=dict)  # Additional custom parameters
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    
    portfolio = relationship("CarbonPortfolio", back_populates="scenarios")


class CarbonCalculation(Base):
    """Results of a carbon credit calculation run"""
    __tablename__ = "carbon_calculation"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("carbon_portfolio.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id = Column(String, ForeignKey("carbon_scenario.id", ondelete="SET NULL"), nullable=True)
    
    calculation_type = Column(String(50), default="standard")  # standard, monte_carlo
    status = Column(String(50), default="completed")  # pending, running, completed, failed
    
    # Input summary
    project_count = Column(Integer, default=0)
    total_input_credits = Column(Float, default=0)
    
    # Results
    total_annual_credits = Column(Float, default=0)
    total_risk_adjusted_credits = Column(Float, default=0)
    portfolio_quality_score = Column(Float)
    portfolio_quality_rating = Column(String(10))
    portfolio_npv_10yr_usd = Column(Float)
    
    # Detailed results
    results_by_project = Column(JSON, default=list)
    results_by_year = Column(JSON, default=list)
    risk_breakdown = Column(JSON, default=dict)
    
    # Monte Carlo specific
    monte_carlo_runs = Column(Integer)
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    
    portfolio = relationship("CarbonPortfolio", back_populates="calculations")


class CarbonReport(Base):
    """Generated carbon reports"""
    __tablename__ = "carbon_report"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("carbon_portfolio.id", ondelete="CASCADE"), nullable=False, index=True)
    calculation_id = Column(String, ForeignKey("carbon_calculation.id", ondelete="SET NULL"), nullable=True)
    
    report_type = Column(String(50), nullable=False)  # summary, detailed, compliance, audit
    format = Column(String(20), default="pdf")  # pdf, xlsx, json
    title = Column(String(255))
    
    # Report content
    content = Column(JSON, default=dict)
    file_path = Column(String(512))
    
    status = Column(String(50), default="completed")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
