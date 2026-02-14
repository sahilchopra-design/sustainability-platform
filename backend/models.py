from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, Field
from enum import Enum


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


class Scenario(str, Enum):
    ORDERLY = "Orderly"
    DISORDERLY = "Disorderly"
    HOT_HOUSE = "Hot house world"


class Company(BaseModel):
    """Company information embedded in assets"""
    name: str
    sector: Sector
    subsector: Optional[str] = None


class Asset(BaseModel):
    """Individual asset within a portfolio"""
    id: str
    asset_type: AssetType
    company: Company
    exposure: float  # Exposure at Default (EAD)
    market_value: float
    base_pd: float  # Probability of Default
    base_lgd: float  # Loss Given Default
    rating: str
    maturity_years: int


class Portfolio(Document):
    """Portfolio containing multiple assets"""
    name: str
    description: Optional[str] = None
    assets: List[Asset] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "portfolios"
        indexes = ["name", "created_at"]


class ScenarioSeries(Document):
    """Climate scenario time-series data"""
    year: int
    scenario: str
    model: str
    region: str
    variable: str
    unit: str
    value: float
    source_version: str

    class Settings:
        name = "scenario_series"
        indexes = [
            "scenario",
            "variable",
            "year",
            ("scenario", "variable", "region", "year"),
        ]


class RatingMigration(BaseModel):
    upgrades: int = 0
    downgrades: int = 0
    stable: int = 0


class ScenarioResult(BaseModel):
    """Results for a specific scenario and horizon"""
    scenario: str
    horizon: int
    expected_loss: float
    expected_loss_pct: float
    risk_adjusted_return: float
    avg_pd_change_pct: float
    rating_migrations: RatingMigration
    var_95: float
    concentration_hhi: float
    total_exposure: float


class AnalysisRun(Document):
    """Scenario analysis run and results"""
    portfolio_id: str
    portfolio_name: str
    scenarios: List[str]
    horizons: List[int]
    results: List[ScenarioResult]
    status: str = "completed"  # pending, running, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Settings:
        name = "analysis_runs"
        indexes = ["portfolio_id", "created_at", "status"]
