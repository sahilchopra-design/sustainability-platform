"""
Pydantic schemas for Sustainability Frameworks Integration Module
Analyzes value impact of green building certifications: GRESB, LEED, BREEAM, etc.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


# ============ Enums ============

class CertificationType(str, Enum):
    GRESB = "gresb"
    LEED = "leed"
    BREEAM = "breeam"
    ENERGY_STAR = "energy_star"
    WELL = "well"
    FITWEL = "fitwel"
    GREEN_GLOBES = "green_globes"
    NABERS = "nabers"
    CASBEE = "casbee"
    HQE = "hqe"


class LEEDLevel(str, Enum):
    CERTIFIED = "certified"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class BREEAMLevel(str, Enum):
    PASS = "pass"
    GOOD = "good"
    VERY_GOOD = "very_good"
    EXCELLENT = "excellent"
    OUTSTANDING = "outstanding"


class GRESBRating(str, Enum):
    ONE_STAR = "1_star"
    TWO_STAR = "2_star"
    THREE_STAR = "3_star"
    FOUR_STAR = "4_star"
    FIVE_STAR = "5_star"


class EnergyStarLevel(str, Enum):
    CERTIFIED = "certified"  # Score >= 75


class PropertySector(str, Enum):
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    MULTIFAMILY = "multifamily"
    HOTEL = "hotel"
    HEALTHCARE = "healthcare"
    DATA_CENTER = "data_center"
    MIXED_USE = "mixed_use"


class Region(str, Enum):
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    MIDDLE_EAST = "middle_east"
    LATIN_AMERICA = "latin_america"
    AFRICA = "africa"


# ============ Certification Schemas ============

class CertificationBase(BaseModel):
    certification_type: CertificationType
    property_id: Optional[UUID] = None
    property_name: Optional[str] = None
    property_sector: PropertySector
    region: Region = Region.NORTH_AMERICA
    
    # Certification details
    certification_level: Optional[str] = None
    score: Optional[Decimal] = Field(None, ge=0, le=100)
    certification_date: Optional[date] = None
    expiration_date: Optional[date] = None
    version: Optional[str] = None
    
    # Property metrics
    gross_floor_area_m2: Optional[Decimal] = Field(None, ge=0)
    year_built: Optional[int] = Field(None, ge=1800, le=2100)
    current_value: Optional[Decimal] = Field(None, ge=0)
    noi: Optional[Decimal] = Field(None, ge=0)


class CertificationCreate(CertificationBase):
    pass


class CertificationResponse(CertificationBase):
    id: UUID
    value_premium_percent: Optional[Decimal] = None
    rent_premium_percent: Optional[Decimal] = None
    estimated_value_impact: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CertificationListResponse(BaseModel):
    items: List[CertificationResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============ GRESB Specific Schemas ============

class GRESBComponentScore(BaseModel):
    management: Decimal = Field(0, ge=0, le=30)
    policy: Decimal = Field(0, ge=0, le=12)
    risk_management: Decimal = Field(0, ge=0, le=14)
    stakeholder_engagement: Decimal = Field(0, ge=0, le=14)
    performance_indicators: Decimal = Field(0, ge=0, le=30)


class GRESBAssessmentRequest(BaseModel):
    portfolio_id: Optional[UUID] = None
    portfolio_name: str = Field(..., max_length=255)
    entity_type: str = "standing_investments"  # standing_investments or development
    region: Region = Region.NORTH_AMERICA
    sector_allocation: Dict[str, Decimal] = Field(default_factory=dict)  # sector -> percentage
    
    # Component scores
    component_scores: GRESBComponentScore
    
    # Property metrics
    total_aum: Decimal = Field(..., ge=0)
    num_assets: int = Field(..., ge=1)
    avg_year_built: Optional[int] = None
    
    # Optional: historical data for trend
    prior_year_score: Optional[Decimal] = Field(None, ge=0, le=100)
    prior_year_rating: Optional[GRESBRating] = None


class GRESBBenchmark(BaseModel):
    peer_group: str
    peer_avg_score: Decimal
    percentile_rank: int
    num_peers: int
    top_quartile_threshold: Decimal
    bottom_quartile_threshold: Decimal


class GRESBAssessmentResult(BaseModel):
    total_score: Decimal
    star_rating: GRESBRating
    component_scores: GRESBComponentScore
    management_score: Decimal
    performance_score: Decimal
    
    # Benchmarking
    benchmark: GRESBBenchmark
    percentile_rank: int
    
    # Value Impact Analysis
    estimated_rent_premium_percent: Decimal
    estimated_value_premium_percent: Decimal
    estimated_value_impact: Decimal
    cap_rate_compression_bps: Decimal
    
    # Improvement analysis
    score_to_next_star: Optional[Decimal] = None
    improvement_recommendations: List[str] = []
    priority_areas: List[Dict[str, Any]] = []
    
    # Trend
    yoy_score_change: Optional[Decimal] = None
    yoy_rating_change: Optional[str] = None


# ============ LEED Assessment Schemas ============

class LEEDCategoryScore(BaseModel):
    integrative_process: int = Field(0, ge=0, le=1)
    location_transportation: int = Field(0, ge=0, le=16)
    sustainable_sites: int = Field(0, ge=0, le=10)
    water_efficiency: int = Field(0, ge=0, le=11)
    energy_atmosphere: int = Field(0, ge=0, le=33)
    materials_resources: int = Field(0, ge=0, le=13)
    indoor_environmental_quality: int = Field(0, ge=0, le=16)
    innovation: int = Field(0, ge=0, le=6)
    regional_priority: int = Field(0, ge=0, le=4)


class LEEDAssessmentRequest(BaseModel):
    property_id: Optional[UUID] = None
    property_name: str
    property_sector: PropertySector
    region: Region = Region.NORTH_AMERICA
    leed_version: str = "v4.1"  # v4, v4.1
    project_type: str = "bd+c"  # bd+c, id+c, o+m
    
    # Category scores
    category_scores: LEEDCategoryScore
    
    # Property metrics
    gross_floor_area_m2: Decimal = Field(..., ge=0)
    year_built: Optional[int] = None
    current_value: Optional[Decimal] = Field(None, ge=0)
    annual_rent_income: Optional[Decimal] = Field(None, ge=0)


class LEEDAssessmentResult(BaseModel):
    total_points: int
    certification_level: LEEDLevel
    category_breakdown: LEEDCategoryScore
    
    # Points analysis
    points_to_next_level: Optional[int] = None
    max_achievable_points: int
    
    # Value Impact
    estimated_rent_premium_percent: Decimal
    estimated_value_premium_percent: Decimal
    estimated_value_impact: Optional[Decimal] = None
    estimated_rent_premium: Optional[Decimal] = None
    
    # Category performance
    strongest_categories: List[str]
    weakest_categories: List[str]
    improvement_potential: Dict[str, int]
    
    # Market comparison
    market_avg_points: int
    percentile_in_market: int


# ============ BREEAM Assessment Schemas ============

class BREEAMCategoryScore(BaseModel):
    management: Decimal = Field(0, ge=0, le=100)
    health_wellbeing: Decimal = Field(0, ge=0, le=100)
    energy: Decimal = Field(0, ge=0, le=100)
    transport: Decimal = Field(0, ge=0, le=100)
    water: Decimal = Field(0, ge=0, le=100)
    materials: Decimal = Field(0, ge=0, le=100)
    waste: Decimal = Field(0, ge=0, le=100)
    land_use_ecology: Decimal = Field(0, ge=0, le=100)
    pollution: Decimal = Field(0, ge=0, le=100)
    innovation: Decimal = Field(0, ge=0, le=100)


class BREEAMWeights(BaseModel):
    """BREEAM category weightings (vary by scheme)"""
    management: Decimal = Decimal("0.12")
    health_wellbeing: Decimal = Decimal("0.15")
    energy: Decimal = Decimal("0.19")
    transport: Decimal = Decimal("0.08")
    water: Decimal = Decimal("0.06")
    materials: Decimal = Decimal("0.125")
    waste: Decimal = Decimal("0.075")
    land_use_ecology: Decimal = Decimal("0.10")
    pollution: Decimal = Decimal("0.10")
    innovation: Decimal = Decimal("0.10")


class BREEAMAssessmentRequest(BaseModel):
    property_id: Optional[UUID] = None
    property_name: str
    property_sector: PropertySector
    region: Region = Region.EUROPE
    breeam_scheme: str = "new_construction"  # new_construction, in_use, refurbishment
    
    # Category scores (0-100 per category)
    category_scores: BREEAMCategoryScore
    weights: BREEAMWeights = BREEAMWeights()
    
    # Property metrics
    gross_floor_area_m2: Decimal = Field(..., ge=0)
    year_built: Optional[int] = None
    current_value: Optional[Decimal] = Field(None, ge=0)
    annual_rent_income: Optional[Decimal] = Field(None, ge=0)


class BREEAMAssessmentResult(BaseModel):
    weighted_score: Decimal
    rating: BREEAMLevel
    category_weighted_scores: Dict[str, Decimal]
    
    # Score to next level
    points_to_next_level: Optional[Decimal] = None
    
    # Value Impact
    estimated_rent_premium_percent: Decimal
    estimated_value_premium_percent: Decimal
    estimated_value_impact: Optional[Decimal] = None
    
    # Category analysis
    highest_performing: List[str]
    improvement_priorities: List[Dict[str, Any]]
    
    # Benchmarking
    percentile_rank: int
    regional_avg_score: Decimal


# ============ Value Impact Analysis Schemas ============

class CertificationValueImpactRequest(BaseModel):
    certification_type: CertificationType
    certification_level: str
    property_sector: PropertySector
    region: Region = Region.NORTH_AMERICA
    
    # Property financials
    current_value: Decimal = Field(..., ge=0)
    current_noi: Optional[Decimal] = Field(None, ge=0)
    current_cap_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    gross_floor_area_sf: Optional[Decimal] = Field(None, ge=0)
    current_rent_psf: Optional[Decimal] = Field(None, ge=0)
    
    # Optional: uncertified comparison
    compare_to_uncertified: bool = True


class CertificationValueImpactResult(BaseModel):
    certification_type: CertificationType
    certification_level: str
    
    # Premium estimates (from research data)
    rent_premium_percent: Decimal
    rent_premium_range: Dict[str, Decimal]  # low, mid, high
    value_premium_percent: Decimal
    value_premium_range: Dict[str, Decimal]
    
    # Estimated impacts
    estimated_rent_premium_psf: Optional[Decimal] = None
    estimated_annual_rent_increase: Optional[Decimal] = None
    estimated_value_increase: Decimal
    cap_rate_compression_bps: Decimal
    
    # Operating benefits
    estimated_operating_cost_savings_percent: Decimal
    estimated_annual_cost_savings: Optional[Decimal] = None
    
    # Market data
    source_studies: List[str]
    data_reliability: str  # high, medium, low
    regional_adjustment: Decimal


# ============ Portfolio Sustainability Analysis ============

class PortfolioSustainabilityRequest(BaseModel):
    portfolio_id: Optional[UUID] = None
    portfolio_name: str
    assets: List[Dict[str, Any]]  # List of assets with certification info
    total_aum: Decimal = Field(..., ge=0)


class PortfolioSustainabilityResult(BaseModel):
    portfolio_name: str
    total_assets: int
    
    # Coverage
    certified_assets: int
    certified_percentage: Decimal
    uncertified_assets: int
    
    # By certification type
    certifications_by_type: Dict[str, int]
    avg_scores_by_type: Dict[str, Decimal]
    
    # Value impact
    total_estimated_value_premium: Decimal
    avg_value_premium_percent: Decimal
    total_estimated_rent_premium: Decimal
    
    # Portfolio GRESB-style metrics
    portfolio_sustainability_score: Decimal
    portfolio_rating: str
    
    # Improvement opportunity
    uncertified_value: Decimal
    potential_value_uplift: Decimal
    
    recommendations: List[str]


# ============ Benchmark Data Schemas ============

class CertificationBenchmarkData(BaseModel):
    certification_type: CertificationType
    property_sector: PropertySector
    region: Region
    
    # Premiums (from academic/industry research)
    avg_rent_premium_percent: Decimal
    rent_premium_range_low: Decimal
    rent_premium_range_high: Decimal
    avg_value_premium_percent: Decimal
    value_premium_range_low: Decimal
    value_premium_range_high: Decimal
    
    # Additional metrics
    avg_cap_rate_compression_bps: Decimal
    avg_operating_cost_savings_percent: Decimal
    avg_occupancy_premium_pct: Decimal
    
    # Source
    data_source: str
    last_updated: date
    sample_size: Optional[int] = None


class BenchmarkListResponse(BaseModel):
    items: List[CertificationBenchmarkData]
    total: int


# ============ Dashboard Schemas ============

class SustainabilityDashboardKPIs(BaseModel):
    total_certified_properties: int
    total_uncertified_properties: int
    certification_coverage_percent: Decimal
    
    # By type
    by_certification_type: Dict[str, int]
    by_level: Dict[str, int]
    
    # Value metrics
    total_certified_value: Decimal
    avg_value_premium_captured: Decimal
    potential_value_uplift: Decimal
    
    # Scores
    avg_gresb_score: Optional[Decimal] = None
    avg_leed_points: Optional[int] = None
    avg_breeam_score: Optional[Decimal] = None
    
    # Trends
    certifications_this_year: int
    certifications_expiring_soon: int


# ============ Comparison Tool Schemas ============

class CertificationComparisonRequest(BaseModel):
    property_sector: PropertySector
    region: Region
    certifications_to_compare: List[CertificationType]
    property_value: Optional[Decimal] = None


class CertificationComparisonResult(BaseModel):
    property_sector: PropertySector
    region: Region
    
    comparisons: List[Dict[str, Any]]
    # Each comparison includes:
    # - certification_type
    # - typical_cost_to_certify
    # - avg_rent_premium
    # - avg_value_premium
    # - roi_estimate
    # - time_to_certify_months
    # - difficulty_rating
    
    recommended_certification: CertificationType
    recommendation_reasoning: List[str]
