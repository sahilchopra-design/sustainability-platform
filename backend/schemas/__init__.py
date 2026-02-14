"""Pydantic v2 schemas for Portfolio Scenario Analysis API"""

# Common
from .common import (
    Sector,
    AssetType,
    ScenarioType,
    EmissionsTrend,
    VelocityTrajectory,
    CurrencyCode,
    PaginationParams,
    DateRangeFilter,
    MonetaryAmount,
    PaginatedResponse,
    APIResponse,
    TimestampMixin
)

# Portfolio
from .portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioSummary,
    PortfolioListResponse,
    PortfolioFilter,
    PortfolioMetrics,
    HoldingCreate,
    HoldingResponse
)

# Counterparty
from .counterparty import (
    CounterpartyCreate,
    CounterpartyUpdate,
    CounterpartyResponse,
    CounterpartySummary,
    CounterpartyListResponse,
    CounterpartyFilter
)

# Scenario - note: scenario.py has been updated with new schema structure for NGFS scenarios
# Importing selected compatible schemas only
from .scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
)

# Analysis
from .analysis import (
    RunScenarioAnalysisRequest,
    ScenarioResultResponse,
    PortfolioMetrics as AnalysisPortfolioMetrics,
    RatingMigration,
    SectorExposure,
    GeographicExposure,
    CounterpartyScenarioDetail,
    ScenarioComparisonRequest,
    ScenarioComparisonResponse
)

__all__ = [
    # Common
    "Sector",
    "AssetType",
    "ScenarioType",
    "EmissionsTrend",
    "VelocityTrajectory",
    "CurrencyCode",
    "PaginationParams",
    "DateRangeFilter",
    "MonetaryAmount",
    "PaginatedResponse",
    "APIResponse",
    "TimestampMixin",
    # Portfolio
    "PortfolioCreate",
    "PortfolioUpdate",
    "PortfolioResponse",
    "PortfolioSummary",
    "PortfolioListResponse",
    "PortfolioFilter",
    "PortfolioMetrics",
    "HoldingCreate",
    "HoldingResponse",
    # Counterparty
    "CounterpartyCreate",
    "CounterpartyUpdate",
    "CounterpartyResponse",
    "CounterpartySummary",
    "CounterpartyListResponse",
    "CounterpartyFilter",
    # Scenario
    "ScenarioCreate",
    "ScenarioUpdate",
    "ScenarioResponse",
    # Analysis
    "RunScenarioAnalysisRequest",
    "ScenarioResultResponse",
    "AnalysisPortfolioMetrics",
    "RatingMigration",
    "SectorExposure",
    "GeographicExposure",
    "CounterpartyScenarioDetail",
    "ScenarioComparisonRequest",
    "ScenarioComparisonResponse",
]
