"""Pydantic v2 schemas for Portfolio Scenario Analysis API"""

# Stranded Assets
from .stranded_assets import (
    # Enums
    ReserveType,
    ReserveCategory,
    PlantTechnology,
    InfrastructureType,
    RiskCategory as StrandedRiskCategory,
    OfftakeType,
    RepurposingType,
    AssetType as StrandedAssetType,
    # Fossil Fuel Reserve
    FossilFuelReserveCreate,
    FossilFuelReserveUpdate,
    FossilFuelReserveResponse,
    FossilFuelReserveListResponse,
    # Power Plant
    PowerPlantCreate,
    PowerPlantUpdate,
    PowerPlantResponse,
    PowerPlantListResponse,
    # Infrastructure
    InfrastructureAssetCreate,
    InfrastructureAssetUpdate,
    InfrastructureAssetResponse,
    InfrastructureAssetListResponse,
    # Calculations
    ReserveImpairmentRequest,
    ReserveImpairmentResult,
    ReserveImpairmentResponse,
    PowerPlantValuationRequest,
    PowerPlantValuationResult,
    PowerPlantValuationResponse,
    InfrastructureValuationRequest,
    InfrastructureValuationResult,
    InfrastructureValuationResponse,
    StrandedAssetCalculationCreate,
    StrandedAssetCalculationResponse,
    # Technology & Pathways
    TechnologyDisruptionMetricCreate,
    TechnologyDisruptionMetricResponse,
    TechnologyDisruptionSummary,
    EnergyTransitionPathwayCreate,
    EnergyTransitionPathwayUpdate,
    EnergyTransitionPathwayResponse,
    EnergyTransitionPathwayListResponse,
    # Alerts & Comparison
    CriticalAssetAlert,
    CriticalAssetAlertList,
    ScenarioComparisonRequest as StrandedScenarioComparisonRequest,
    ScenarioComparisonResult as StrandedScenarioComparisonResult,
    ScenarioComparisonResponse as StrandedScenarioComparisonResponse,
    # Dashboard
    StrandedAssetDashboardKPIs,
    PortfolioStrandingAnalysisRequest,
    PortfolioStrandingAnalysisResponse,
)

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
