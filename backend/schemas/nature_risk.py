"""
Pydantic schemas for Nature Risk Integration API
Based on TNFD LEAP methodology and NCORE framework
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


# ============ Enums ============

class ScenarioType(str, Enum):
    PHYSICAL = "physical"
    TRANSITION = "transition"
    COMBINED = "combined"


class FrameworkType(str, Enum):
    TNFD = "TNFD"
    NCORE = "NCORE"
    CUSTOM = "custom"


class BiodiversityTrend(str, Enum):
    DECLINE = "decline"
    STABLE = "stable"
    RECOVERY = "recovery"


class PolicyStringency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EntityType(str, Enum):
    COMPANY = "company"
    ASSET = "asset"
    PORTFOLIO = "portfolio"


class RiskRating(str, Enum):
    LOW = "low"
    MEDIUM_LOW = "medium-low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium-high"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LocationType(str, Enum):
    FACILITY = "facility"
    BASIN = "basin"
    WATERSHED = "watershed"
    MINE = "mine"
    POWER_PLANT = "power_plant"
    REFINERY = "refinery"


class WaterSourceType(str, Enum):
    SURFACE = "surface"
    GROUNDWATER = "groundwater"
    RECYCLED = "recycled"
    DESALINATED = "desalinated"
    THIRD_PARTY = "third_party"


class SiteType(str, Enum):
    PROTECTED_AREA = "protected_area"
    KEY_BIODIVERSITY_AREA = "key_biodiversity_area"
    RAMSAR = "ramsar"
    WORLD_HERITAGE = "world_heritage"
    IBA = "iba"
    ALLIANCE_ZERO = "alliance_zero"


class IUCNCategory(str, Enum):
    IA = "Ia"
    IB = "Ib"
    II = "II"
    III = "III"
    IV = "IV"
    V = "V"
    VI = "VI"


class DependencyCriticality(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlignmentStatus(str, Enum):
    ALIGNED = "aligned"
    PARTIAL = "partial"
    NOT_ALIGNED = "not_aligned"
    NOT_APPLICABLE = "not_applicable"


class MetricCategory(str, Enum):
    DRIVER = "driver"
    STATE = "state"
    PRESSURE = "pressure"
    IMPACT = "impact"
    RESPONSE = "response"


# ============ Nested Models ============

class BiomeExposure(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    tropical_forest: bool = False
    temperate_forest: bool = False
    boreal_forest: bool = False
    savanna: bool = False
    grassland: bool = False
    wetland: bool = False
    freshwater: bool = False
    marine: bool = False
    desert: bool = False
    tundra: bool = False
    mountain: bool = False


class DependencyRating(BaseModel):
    ecosystem_service: str
    rating: int = Field(..., ge=1, le=5)
    materiality: str
    justification: Optional[str] = None


class ImpactRating(BaseModel):
    impact_driver: str
    rating: int = Field(..., ge=1, le=5)
    scope: str
    reversibility: str


class PhysicalRiskScores(BaseModel):
    acute: float = Field(..., ge=0, le=5)
    chronic: float = Field(..., ge=0, le=5)
    description: Optional[str] = None


class TransitionRiskScores(BaseModel):
    policy: float = Field(..., ge=0, le=5)
    legal: float = Field(..., ge=0, le=5)
    technology: float = Field(..., ge=0, le=5)
    market: float = Field(..., ge=0, le=5)
    reputation: float = Field(..., ge=0, le=5)


class OpportunityScores(BaseModel):
    resource_efficiency: float = Field(..., ge=0, le=5)
    products_services: float = Field(..., ge=0, le=5)
    markets: float = Field(..., ge=0, le=5)
    resilience: float = Field(..., ge=0, le=5)


# ============ Scenario Models ============

class NatureRiskScenarioBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    scenario_type: ScenarioType
    framework: FrameworkType
    temperature_c: Optional[float] = Field(None, ge=1.0, le=5.0)
    precipitation_change_percent: Optional[float] = None
    biodiversity_trend: Optional[BiodiversityTrend] = None
    policy_stringency: Optional[PolicyStringency] = None
    water_scarcity_index: Optional[float] = Field(None, ge=0, le=5)
    ecosystem_degradation_rate: Optional[float] = Field(None, ge=0, le=1)
    assumptions: Optional[Dict[str, Any]] = None
    is_active: bool = True


class NatureRiskScenarioCreate(NatureRiskScenarioBase):
    created_by: Optional[str] = None


class NatureRiskScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    temperature_c: Optional[float] = None
    precipitation_change_percent: Optional[float] = None
    biodiversity_trend: Optional[BiodiversityTrend] = None
    policy_stringency: Optional[PolicyStringency] = None
    assumptions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class NatureRiskScenarioResponse(NatureRiskScenarioBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ LEAP Assessment Models ============

class LEAPAssessmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_id: str
    entity_type: EntityType
    assessment_name: str = Field(..., min_length=1, max_length=300)
    assessment_date: date
    framework_version: str = Field(default="v1.0")

    # LOCATE phase
    biome_exposure: Optional[BiomeExposure] = None
    ecosystem_dependencies: Optional[List[str]] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    value_chain_exposure: Optional[Dict[str, Any]] = None

    # EVALUATE phase
    dependency_ratings: Optional[List[DependencyRating]] = None
    impact_ratings: Optional[List[ImpactRating]] = None
    materiality_matrix: Optional[Dict[str, Any]] = None

    # ASSESS phase
    physical_risk_scores: Optional[PhysicalRiskScores] = None
    transition_risk_scores: Optional[TransitionRiskScores] = None
    opportunity_scores: Optional[OpportunityScores] = None

    # PREPARE phase
    strategy_response: Optional[Dict[str, Any]] = None
    target_setting: Optional[Dict[str, Any]] = None
    metrics_disclosure: Optional[Dict[str, Any]] = None

    overall_risk_rating: Optional[RiskRating] = None
    confidence_level: Optional[ConfidenceLevel] = ConfidenceLevel.MEDIUM
    next_assessment_date: Optional[date] = None


class LEAPAssessmentCreate(LEAPAssessmentBase):
    assessor_id: Optional[str] = None


class LEAPAssessmentUpdate(BaseModel):
    dependency_ratings: Optional[List[DependencyRating]] = None
    impact_ratings: Optional[List[ImpactRating]] = None
    physical_risk_scores: Optional[PhysicalRiskScores] = None
    transition_risk_scores: Optional[TransitionRiskScores] = None
    strategy_response: Optional[Dict[str, Any]] = None
    overall_risk_rating: Optional[RiskRating] = None
    confidence_level: Optional[ConfidenceLevel] = None


class LEAPAssessmentResponse(LEAPAssessmentBase):
    id: str
    assessor_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ ENCORE Dependency Models ============

class ENCOREDependencyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sector_code: str = Field(..., min_length=1, max_length=20)
    sector_name: str = Field(..., min_length=1, max_length=200)
    subsector_code: Optional[str] = Field(None, max_length=20)
    subsector_name: Optional[str] = Field(None, max_length=200)
    ecosystem_service: str = Field(..., min_length=1, max_length=100)
    dependency_type: str
    dependency_score: Optional[int] = Field(None, ge=1, le=5)
    dependency_description: Optional[str] = None
    data_quality: Optional[str] = None
    source_reference: Optional[str] = Field(None, max_length=500)


class ENCOREDependencyResponse(ENCOREDependencyBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Water Risk Location Models ============

class WaterRiskLocationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_name: str = Field(..., min_length=1, max_length=300)
    location_type: LocationType
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    country_code: str = Field(..., min_length=2, max_length=2)
    watershed_id: Optional[str] = Field(None, max_length=100)
    basin_name: Optional[str] = Field(None, max_length=200)

    # Water risk indicators (Aqueduct)
    baseline_water_stress: Optional[float] = Field(None, ge=0, le=5)
    groundwater_table_decline: Optional[float] = Field(None, ge=0, le=5)
    interannual_variability: Optional[float] = Field(None, ge=0, le=5)
    seasonal_variability: Optional[float] = Field(None, ge=0, le=5)
    drought_risk: Optional[float] = Field(None, ge=0, le=5)
    flood_risk: Optional[float] = Field(None, ge=0, le=5)

    # Projected risks
    projected_water_stress_2030: Optional[float] = Field(None, ge=0, le=5)
    projected_water_stress_2040: Optional[float] = Field(None, ge=0, le=5)
    projected_water_stress_2050: Optional[float] = Field(None, ge=0, le=5)

    # Sector-specific
    annual_water_withdrawal_m3: Optional[float] = Field(None, ge=0)
    water_intensity_m3_unit: Optional[float] = Field(None, ge=0)
    water_source_type: Optional[WaterSourceType] = None

    linked_asset_id: Optional[str] = None
    linked_asset_type: Optional[str] = None


class WaterRiskLocationCreate(WaterRiskLocationBase):
    created_by: Optional[str] = None
    organization_id: Optional[str] = None


class WaterRiskLocationUpdate(BaseModel):
    location_name: Optional[str] = None
    annual_water_withdrawal_m3: Optional[float] = None
    water_intensity_m3_unit: Optional[float] = None
    water_source_type: Optional[WaterSourceType] = None
    projected_water_stress_2030: Optional[float] = None
    projected_water_stress_2040: Optional[float] = None
    projected_water_stress_2050: Optional[float] = None


class WaterRiskLocationResponse(WaterRiskLocationBase):
    id: str
    created_by: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    water_risk_level: Optional[str] = None

    class Config:
        from_attributes = True


# ============ Biodiversity Site Models ============

class BiodiversitySiteBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_name: str = Field(..., min_length=1, max_length=300)
    site_type: SiteType
    designation: Optional[str] = Field(None, max_length=100)
    iucn_category: Optional[IUCNCategory] = None
    country_code: str = Field(..., min_length=2, max_length=2)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    area_km2: Optional[float] = Field(None, ge=0)
    designation_year: Optional[int] = Field(None, ge=1900, le=2100)
    management_effectiveness: Optional[str] = None
    threats: Optional[List[str]] = None
    key_species: Optional[List[str]] = None
    ecosystem_type: Optional[str] = Field(None, max_length=100)
    importance_criteria: Optional[Dict[str, Any]] = None
    data_source: Optional[str] = Field(None, max_length=100)
    source_id: Optional[str] = Field(None, max_length=100)


class BiodiversitySiteResponse(BiodiversitySiteBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Nature Risk Exposure Models (Financial Sector) ============

class NatureRiskExposureBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    portfolio_holding_id: str
    scenario_id: str
    assessment_date: date

    # LEAP scores
    locate_score: Optional[float] = Field(None, ge=0, le=5)
    evaluate_score: Optional[float] = Field(None, ge=0, le=5)
    assess_score: Optional[float] = Field(None, ge=0, le=5)
    prepare_score: Optional[float] = Field(None, ge=0, le=5)

    # Material dependencies
    material_dependencies: Optional[List[str]] = None
    dependency_criticality: Optional[DependencyCriticality] = None

    # Physical risks
    water_stress_exposure: Optional[float] = Field(None, ge=0, le=100)
    flood_exposure: Optional[float] = Field(None, ge=0, le=100)
    drought_exposure: Optional[float] = Field(None, ge=0, le=100)
    ecosystem_degradation_exposure: Optional[float] = Field(None, ge=0, le=100)

    # Transition risks
    water_pricing_risk: Optional[float] = Field(None, ge=0, le=100)
    biodiversity_offset_risk: Optional[float] = Field(None, ge=0, le=100)
    regulatory_compliance_risk: Optional[float] = Field(None, ge=0, le=100)
    reputational_risk: Optional[float] = Field(None, ge=0, le=100)

    # Financial impacts
    capex_increase_percent: Optional[float] = None
    opex_increase_percent: Optional[float] = None
    revenue_at_risk_percent: Optional[float] = Field(None, ge=0, le=100)
    asset_impairment_percent: Optional[float] = Field(None, ge=0, le=100)

    # Collateral impact
    collateral_value_impact_percent: Optional[float] = None
    collateral_haircut_recommendation: Optional[float] = Field(None, ge=0, le=100)

    overall_nature_risk_score: Optional[float] = Field(None, ge=0, le=5)
    risk_tier: Optional[RiskRating] = None


class NatureRiskExposureCreate(NatureRiskExposureBase):
    pass


class NatureRiskExposureResponse(NatureRiskExposureBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Asset Nature Overlap Models ============

class AssetNatureOverlapBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    asset_type: str
    site_id: str
    overlap_area_km2: Optional[float] = Field(None, ge=0)
    overlap_percent: Optional[float] = Field(None, ge=0, le=100)
    buffer_distance_km: Optional[float] = Field(None, ge=0)
    impact_assessment: Optional[Dict[str, Any]] = None
    mitigation_measures: Optional[List[str]] = None


class AssetNatureOverlapResponse(AssetNatureOverlapBase):
    id: str
    calculated_at: datetime

    class Config:
        from_attributes = True


# ============ GBF Alignment Models ============

class GBFAlignmentTargetBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_id: str
    entity_type: EntityType
    target_number: str
    target_description: Optional[str] = None
    alignment_status: AlignmentStatus
    alignment_score: float = Field(..., ge=0, le=100)
    actions_taken: Optional[List[str]] = None
    gaps_identified: Optional[List[str]] = None
    timeline_to_alignment: Optional[str] = Field(None, max_length=100)
    reporting_year: int = Field(..., ge=2020, le=2100)
    verified_by: Optional[str] = Field(None, max_length=200)


class GBFAlignmentTargetResponse(GBFAlignmentTargetBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Nature Risk Metrics Models ============

class NatureRiskMetricBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_id: str
    entity_type: EntityType
    metric_category: MetricCategory
    metric_name: str = Field(..., min_length=1, max_length=200)
    metric_code: Optional[str] = Field(None, max_length=50)
    value: float
    unit: str = Field(..., min_length=1, max_length=50)
    reporting_period: str = Field(..., max_length=20)
    reporting_year: int = Field(..., ge=2000, le=2100)
    geographic_scope: Optional[str] = Field(None, max_length=100)
    methodology: Optional[str] = None
    data_quality: Optional[str] = None
    verification_status: Optional[str] = None
    assurance_provider: Optional[str] = Field(None, max_length=200)


class NatureRiskMetricResponse(NatureRiskMetricBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Request/Response Models for API ============

class LEAPAssessmentRequest(BaseModel):
    entity_id: str
    entity_type: EntityType
    scenario_ids: List[str]
    include_dependencies: bool = True
    include_water_risk: bool = True
    include_biodiversity_overlap: bool = True


class WaterRiskAnalysisRequest(BaseModel):
    location_ids: List[str]
    scenario_ids: List[str]
    include_projections: bool = True
    projection_years: List[int] = Field(default=[2030, 2040, 2050])


class BiodiversityOverlapRequest(BaseModel):
    asset_ids: List[str]
    asset_type: str
    buffer_distance_km: float = Field(default=10, ge=0, le=100)
    site_types: Optional[List[SiteType]] = None


class PortfolioNatureRiskRequest(BaseModel):
    portfolio_id: str
    scenario_ids: List[str]
    include_collateral_impact: bool = True
    include_gbf_alignment: bool = False


class NatureRiskSummaryResponse(BaseModel):
    entity_id: str
    entity_type: EntityType
    overall_risk_score: float
    risk_tier: RiskRating
    key_dependencies: List[str]
    key_risks: List[Dict[str, Any]]
    water_risk_summary: Optional[Dict[str, Any]] = None
    biodiversity_overlap_summary: Optional[Dict[str, Any]] = None
    recommendations: List[str]


class NatureRiskDashboardSummary(BaseModel):
    total_assessments: int = 0
    high_risk_entities: int = 0
    critical_risk_entities: int = 0
    water_risk_exposure: Dict[str, Any] = {}
    biodiversity_overlaps: Dict[str, Any] = {}
    gbf_alignment: Dict[str, Any] = {}
    sector_breakdown: Dict[str, Any] = {}
    trend_data: List[Dict[str, Any]] = []


class BulkImportResponse(BaseModel):
    total_records: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, Any]]
    import_id: str
