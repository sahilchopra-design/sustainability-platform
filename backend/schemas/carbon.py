"""
Pydantic schemas for Carbon Credits API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectTypeEnum(str, Enum):
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


class CarbonStandardEnum(str, Enum):
    VCS = "VCS"
    GOLD_STANDARD = "GOLD_STANDARD"
    ACR = "ACR"
    CAR = "CAR"
    CDM = "CDM"
    JCM = "JCM"
    CORSIA = "CORSIA"
    OTHER = "OTHER"


class RiskLevelEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class QualityRatingEnum(str, Enum):
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"


# ============ Methodology Schemas ============

class MethodologyBase(BaseModel):
    code: str
    name: str
    standard: str
    sector: str
    subsector: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: str = "active"
    applicable_project_types: List[str] = []
    default_parameters: Dict[str, Any] = {}


class MethodologyCreate(MethodologyBase):
    pass


class MethodologyResponse(MethodologyBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Emission Factor Schemas ============

class EmissionFactorBase(BaseModel):
    country_code: str
    country_name: str
    year: int
    grid_emission_factor: Optional[float] = None
    natural_gas_ef: Optional[float] = None
    coal_ef: Optional[float] = None
    oil_ef: Optional[float] = None
    biomass_ef: Optional[float] = None
    source: Optional[str] = None
    is_default: bool = False


class EmissionFactorResponse(EmissionFactorBase):
    id: str

    class Config:
        from_attributes = True


# ============ Portfolio Schemas ============

class CarbonPortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None
    linked_portfolio_id: Optional[str] = None
    target_annual_credits: float = 0
    budget_usd: float = 0
    quality_minimum: str = "BBB"


class CarbonPortfolioCreate(CarbonPortfolioBase):
    pass


class CarbonPortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_annual_credits: Optional[float] = None
    budget_usd: Optional[float] = None
    quality_minimum: Optional[str] = None
    status: Optional[str] = None


class CarbonPortfolioSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    project_count: int = 0
    total_annual_credits: float = 0
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CarbonPortfolioResponse(CarbonPortfolioBase):
    id: str
    owner_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    project_count: int = 0
    total_annual_credits: float = 0

    class Config:
        from_attributes = True


# ============ Project Schemas ============

class ProjectCoordinates(BaseModel):
    lat: float
    lng: float


class CarbonProjectBase(BaseModel):
    name: str
    project_type: str
    standard: str
    registry_id: Optional[str] = None
    country_code: str
    region: Optional[str] = None
    coordinates: Optional[ProjectCoordinates] = None
    annual_credits: float = 0
    total_credits: float = 0
    vintage_start: Optional[int] = None
    vintage_end: Optional[int] = None
    crediting_period_years: int = 10
    quality_rating: Optional[str] = None
    quality_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    price_per_credit_usd: Optional[float] = None
    total_investment_usd: Optional[float] = None
    sdg_contributions: List[int] = []
    co_benefits: List[str] = []


class CarbonProjectCreate(CarbonProjectBase):
    portfolio_id: str
    methodology_id: Optional[str] = None


class CarbonProjectUpdate(BaseModel):
    name: Optional[str] = None
    project_type: Optional[str] = None
    standard: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    coordinates: Optional[ProjectCoordinates] = None
    annual_credits: Optional[float] = None
    quality_rating: Optional[str] = None
    quality_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    price_per_credit_usd: Optional[float] = None
    status: Optional[str] = None
    verification_status: Optional[str] = None


class CarbonProjectResponse(CarbonProjectBase):
    id: str
    portfolio_id: str
    methodology_id: Optional[str]
    issued_credits: float = 0
    retired_credits: float = 0
    additionality_score: Optional[float]
    permanence_score: Optional[float]
    co_benefits_score: Optional[float]
    status: str
    verification_status: str
    last_verification_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Scenario Schemas ============

class CarbonScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False
    permanence_risk_pct: float = 10.0
    delivery_risk_pct: float = 5.0
    regulatory_risk_pct: float = 5.0
    market_risk_pct: float = 10.0
    base_carbon_price_usd: float = 15.0
    price_growth_rate_pct: float = 5.0
    price_volatility_pct: float = 20.0
    discount_rate_pct: float = 8.0
    projection_years: int = 10
    parameters: Dict[str, Any] = {}


class CarbonScenarioCreate(CarbonScenarioBase):
    portfolio_id: str


class CarbonScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permanence_risk_pct: Optional[float] = None
    delivery_risk_pct: Optional[float] = None
    regulatory_risk_pct: Optional[float] = None
    market_risk_pct: Optional[float] = None
    base_carbon_price_usd: Optional[float] = None
    price_growth_rate_pct: Optional[float] = None
    discount_rate_pct: Optional[float] = None
    projection_years: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None


class CarbonScenarioResponse(CarbonScenarioBase):
    id: str
    portfolio_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Calculation Schemas ============

class ProjectCalculationInput(BaseModel):
    project_id: str
    annual_credits: Optional[float] = None  # Override project's value
    custom_risk_adjustments: Optional[Dict[str, float]] = None


class CalculationRequest(BaseModel):
    portfolio_id: str
    scenario_id: Optional[str] = None
    calculation_type: str = "standard"  # standard, monte_carlo
    monte_carlo_runs: Optional[int] = 1000
    projects: Optional[List[ProjectCalculationInput]] = None  # If None, use all portfolio projects


class ProjectCalculationResult(BaseModel):
    project_id: str
    project_name: str
    annual_credits: float
    risk_adjusted_credits: float
    risk_discount_pct: float
    quality_score: Optional[float]
    npv_usd: Optional[float]


class YearlyProjection(BaseModel):
    year: int
    base_case: float
    optimistic: float
    pessimistic: float
    risk_adjusted: float


class RiskBreakdown(BaseModel):
    permanence_risk: float
    delivery_risk: float
    regulatory_risk: float
    market_risk: float
    total_risk_pct: float


class CalculationResponse(BaseModel):
    calculation_id: str
    portfolio_id: str
    scenario_id: Optional[str]
    status: str
    calculation_type: str
    
    # Summary
    total_annual_credits: float
    total_risk_adjusted_credits: float
    portfolio_quality_score: Optional[float]
    portfolio_quality_rating: Optional[str]
    portfolio_npv_10yr_usd: Optional[float]
    
    # Details
    project_count: int
    projects: List[ProjectCalculationResult]
    yearly_projections: List[YearlyProjection]
    risk_breakdown: RiskBreakdown
    
    # Monte Carlo results (if applicable)
    confidence_interval_low: Optional[float] = None
    confidence_interval_high: Optional[float] = None
    
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Report Schemas ============

class ReportGenerateRequest(BaseModel):
    portfolio_id: str
    calculation_id: Optional[str] = None
    scenario_id: Optional[str] = None
    report_type: str = "summary"  # summary, detailed, compliance, audit
    format: str = "pdf"  # pdf, xlsx, json
    title: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    portfolio_id: str
    report_type: str
    format: str
    title: Optional[str]
    status: str
    file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Dashboard Schemas ============

class PortfolioDashboardSummary(BaseModel):
    total_annual_credits: float
    total_risk_adjusted_credits: float
    portfolio_quality_score: float
    portfolio_quality_rating: str
    portfolio_npv_10yr_usd: float
    project_count: int
    average_risk_score: float


class RiskHeatMapItem(BaseModel):
    category: str
    score: float
    impact: str  # Low, Medium, High, Critical
    probability: str  # Low, Medium, High


class PortfolioDashboard(BaseModel):
    portfolio_id: str
    portfolio_name: str
    summary: PortfolioDashboardSummary
    projects: List[CarbonProjectResponse]
    yearly_projections: List[YearlyProjection]
    risk_heat_map: List[RiskHeatMapItem]
    geographic_distribution: List[Dict[str, Any]]
