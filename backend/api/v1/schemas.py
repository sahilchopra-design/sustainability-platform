"""Pydantic schemas for API v1"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# Enums
class AssetType(str, Enum):
    BOND = "Bond"
    LOAN = "Loan"
    EQUITY = "Equity"


class Sector(str, Enum):
    POWER_GENERATION = "Power Generation"
    OIL_GAS = "Oil & Gas"
    METALS_MINING = "Metals & Mining"
    AUTOMOTIVE = "Automotive"
    AIRLINES = "Airlines"
    REAL_ESTATE = "Real Estate"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Portfolio Schemas
class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class PortfolioBase(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    num_holdings: int = 0
    total_exposure: float = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioDetail(PortfolioBase):
    metrics: Dict[str, Any] = Field(default_factory=dict)


# Asset/Holding Schemas
class HoldingCreate(BaseModel):
    asset_type: AssetType
    company_name: str = Field(..., min_length=1)
    company_sector: Sector
    company_subsector: Optional[str] = None
    exposure: float = Field(..., gt=0)
    market_value: float = Field(..., gt=0)
    base_pd: float = Field(..., ge=0, le=1)
    base_lgd: float = Field(..., ge=0, le=1)
    rating: str
    maturity_years: int = Field(..., gt=0)


class HoldingResponse(BaseModel):
    id: str
    portfolio_id: str
    asset_type: str
    company_name: str
    company_sector: str
    company_subsector: Optional[str] = None
    exposure: float
    market_value: float
    base_pd: float
    base_lgd: float
    rating: str
    maturity_years: int
    
    class Config:
        from_attributes = True


# Counterparty Schemas (Using Portfolio as counterparty for now)
class CounterpartyCreate(PortfolioCreate):
    pass


class CounterpartyUpdate(PortfolioUpdate):
    pass


class CounterpartyResponse(PortfolioBase):
    pass


# Scenario Schemas
class ScenarioSummary(BaseModel):
    name: str
    description: Optional[str] = None
    type: str


class ScenarioDetail(BaseModel):
    scenario: str
    variables: List[str]
    regions: List[str]
    years: List[int]


# Analysis Schemas
class AnalysisRequest(BaseModel):
    portfolio_id: str
    scenarios: List[str] = Field(..., min_length=1)
    horizons: List[int] = Field(..., min_length=1)
    
    @field_validator('horizons')
    @classmethod
    def validate_horizons(cls, v):
        for horizon in v:
            if horizon < 2025 or horizon > 2100:
                raise ValueError('Time horizons must be between 2025 and 2100')
        return sorted(v)


class AnalysisJobResponse(BaseModel):
    job_id: str
    portfolio_id: str
    portfolio_name: str
    scenarios: List[str]
    horizons: List[int]
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class RatingMigration(BaseModel):
    upgrades: int = 0
    downgrades: int = 0
    stable: int = 0


class ScenarioResultResponse(BaseModel):
    scenario: str
    horizon: int
    expected_loss: float
    expected_loss_pct: float
    risk_adjusted_return: float
    avg_pd_change_pct: float
    rating_migrations: Dict[str, int]
    var_95: float
    concentration_hhi: float
    total_exposure: float
    
    class Config:
        from_attributes = True


class AnalysisResultsResponse(BaseModel):
    job_id: str
    portfolio_id: str
    portfolio_name: str
    status: AnalysisStatus
    results: List[ScenarioResultResponse]
    created_at: datetime
    completed_at: Optional[datetime] = None


class CompareRequest(BaseModel):
    portfolio_id: str
    scenario_ids: List[str] = Field(..., min_length=2)
    horizon: int = Field(..., ge=2025, le=2100)


class ComparisonMetric(BaseModel):
    metric_name: str
    values: Dict[str, float]


class CompareResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    horizon: int
    scenarios: List[str]
    comparisons: List[ComparisonMetric]


# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Generic responses
class MessageResponse(BaseModel):
    message: str
    detail: Optional[Dict[str, Any]] = None
