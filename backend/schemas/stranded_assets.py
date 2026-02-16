"""
Pydantic schemas for Stranded Asset Module
Energy transition risk assessment for fossil fuel reserves, power plants, and infrastructure
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict, Literal
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


# ============ Enums ============

class ReserveType(str, Enum):
    OIL = "oil"
    GAS = "gas"
    COAL = "coal"


class ReserveCategory(str, Enum):
    PROVEN = "1P"
    PROBABLE = "2P"
    POSSIBLE = "3P"


class PlantTechnology(str, Enum):
    COAL = "coal"
    GAS_CCGT = "gas_ccgt"
    GAS_OCGT = "gas_ocgt"
    NUCLEAR = "nuclear"
    HYDRO = "hydro"
    WIND_ONSHORE = "wind_onshore"
    WIND_OFFSHORE = "wind_offshore"
    SOLAR_PV = "solar_pv"
    SOLAR_CSP = "solar_csp"
    BIOMASS = "biomass"
    GEOTHERMAL = "geothermal"
    BATTERY_STORAGE = "battery_storage"
    PUMPED_HYDRO = "pumped_hydro"


class InfrastructureType(str, Enum):
    PIPELINE_OIL = "pipeline_oil"
    PIPELINE_GAS = "pipeline_gas"
    LNG_TERMINAL = "lng_terminal"
    STORAGE_FACILITY = "storage_facility"
    REFINERY = "refinery"
    PETROCHEMICAL_PLANT = "petrochemical_plant"


class RiskCategory(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OfftakeType(str, Enum):
    MERCHANT = "merchant"
    PPA = "ppa"
    REGULATED = "regulated"


class RepurposingType(str, Enum):
    CCS = "ccs"
    HYDROGEN = "hydrogen"
    STORAGE = "storage"
    RETIREMENT = "retirement"


class AssetType(str, Enum):
    RESERVE = "reserve"
    POWER_PLANT = "power_plant"
    INFRASTRUCTURE = "infrastructure"


# ==================== FOSSIL FUEL RESERVE ====================

class FossilFuelReserveBase(BaseModel):
    asset_name: str = Field(..., max_length=255)
    asset_location: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    reserve_type: ReserveType
    reserve_category: ReserveCategory = ReserveCategory.PROVEN
    proven_reserves_mmBOE: Optional[Decimal] = Field(None, ge=0)
    probable_reserves_mmBOE: Optional[Decimal] = Field(None, ge=0)
    possible_reserves_mmBOE: Optional[Decimal] = Field(None, ge=0)
    breakeven_price_USD: Optional[Decimal] = Field(None, ge=0)
    lifting_cost_USD: Optional[Decimal] = Field(None, ge=0)
    remaining_capex_USD: Optional[Decimal] = Field(None, ge=0)
    carbon_intensity_kgCO2_per_unit: Optional[Decimal] = Field(None, ge=0)
    methane_leakage_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    production_start_year: Optional[int] = Field(None, ge=1900, le=2100)
    expected_depletion_year: Optional[int] = Field(None, ge=1900, le=2100)
    license_expiry_year: Optional[int] = Field(None, ge=1900, le=2100)


class FossilFuelReserveCreate(FossilFuelReserveBase):
    counterparty_id: UUID


class FossilFuelReserveUpdate(BaseModel):
    asset_name: Optional[str] = Field(None, max_length=255)
    asset_location: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    reserve_type: Optional[ReserveType] = None
    reserve_category: Optional[ReserveCategory] = None
    proven_reserves_mmBOE: Optional[Decimal] = Field(None, ge=0)
    probable_reserves_mmBOE: Optional[Decimal] = Field(None, ge=0)
    possible_reserves_mmBOE: Optional[Decimal] = Field(None, ge=0)
    breakeven_price_USD: Optional[Decimal] = Field(None, ge=0)
    lifting_cost_USD: Optional[Decimal] = Field(None, ge=0)
    remaining_capex_USD: Optional[Decimal] = Field(None, ge=0)
    carbon_intensity_kgCO2_per_unit: Optional[Decimal] = Field(None, ge=0)
    methane_leakage_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    production_start_year: Optional[int] = Field(None, ge=1900, le=2100)
    expected_depletion_year: Optional[int] = Field(None, ge=1900, le=2100)
    license_expiry_year: Optional[int] = Field(None, ge=1900, le=2100)
    is_operating: Optional[bool] = None


class FossilFuelReserveResponse(FossilFuelReserveBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    counterparty_id: UUID
    is_operating: bool
    created_at: datetime
    updated_at: datetime


class FossilFuelReserveListResponse(BaseModel):
    items: List[FossilFuelReserveResponse]
    total: int
    page: int
    page_size: int


# ==================== POWER PLANT ====================

class PowerPlantBase(BaseModel):
    plant_name: str = Field(..., max_length=255)
    plant_location: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    country_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}$")
    technology_type: PlantTechnology
    capacity_mw: Decimal = Field(..., gt=0)
    commissioning_year: Optional[int] = Field(None, ge=1900, le=2100)
    original_retirement_year: Optional[int] = Field(None, ge=1900, le=2100)
    technical_lifetime_years: Optional[int] = Field(None, ge=0, le=100)
    capacity_factor_baseline: Optional[Decimal] = Field(None, ge=0, le=1)
    capacity_factor_current: Optional[Decimal] = Field(None, ge=0, le=1)
    heat_rate_btu_kwh: Optional[Decimal] = Field(None, gt=0)
    efficiency_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    co2_intensity_tco2_mwh: Optional[Decimal] = Field(None, ge=0)
    nox_emissions_kg_mwh: Optional[Decimal] = Field(None, ge=0)
    so2_emissions_kg_mwh: Optional[Decimal] = Field(None, ge=0)
    has_ccs: bool = False
    ccs_capacity_mtpa: Optional[Decimal] = Field(None, ge=0)
    fixed_om_cost_usd_kw_year: Optional[Decimal] = Field(None, ge=0)
    variable_om_cost_usd_mwh: Optional[Decimal] = Field(None, ge=0)
    fuel_cost_usd_mmbtu: Optional[Decimal] = Field(None, ge=0)
    fuel_type: Optional[str] = None
    offtake_type: Optional[OfftakeType] = None
    ppa_expiry_year: Optional[int] = Field(None, ge=1900, le=2100)
    ppa_price_usd_mwh: Optional[Decimal] = Field(None, ge=0)
    grid_region: Optional[str] = Field(None, max_length=100)
    grid_carbon_intensity: Optional[Decimal] = Field(None, ge=0)
    repurposing_option: Optional[RepurposingType] = None
    repurposing_cost_usd_mw: Optional[Decimal] = Field(None, ge=0)


class PowerPlantCreate(PowerPlantBase):
    counterparty_id: UUID


class PowerPlantUpdate(BaseModel):
    plant_name: Optional[str] = Field(None, max_length=255)
    plant_location: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    country_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}$")
    technology_type: Optional[PlantTechnology] = None
    capacity_mw: Optional[Decimal] = Field(None, gt=0)
    commissioning_year: Optional[int] = Field(None, ge=1900, le=2100)
    original_retirement_year: Optional[int] = Field(None, ge=1900, le=2100)
    technical_lifetime_years: Optional[int] = Field(None, ge=0, le=100)
    capacity_factor_baseline: Optional[Decimal] = Field(None, ge=0, le=1)
    capacity_factor_current: Optional[Decimal] = Field(None, ge=0, le=1)
    heat_rate_btu_kwh: Optional[Decimal] = Field(None, gt=0)
    efficiency_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    co2_intensity_tco2_mwh: Optional[Decimal] = Field(None, ge=0)
    nox_emissions_kg_mwh: Optional[Decimal] = Field(None, ge=0)
    so2_emissions_kg_mwh: Optional[Decimal] = Field(None, ge=0)
    has_ccs: Optional[bool] = None
    ccs_capacity_mtpa: Optional[Decimal] = Field(None, ge=0)
    fixed_om_cost_usd_kw_year: Optional[Decimal] = Field(None, ge=0)
    variable_om_cost_usd_mwh: Optional[Decimal] = Field(None, ge=0)
    fuel_cost_usd_mmbtu: Optional[Decimal] = Field(None, ge=0)
    fuel_type: Optional[str] = None
    offtake_type: Optional[OfftakeType] = None
    ppa_expiry_year: Optional[int] = Field(None, ge=1900, le=2100)
    ppa_price_usd_mwh: Optional[Decimal] = Field(None, ge=0)
    grid_region: Optional[str] = Field(None, max_length=100)
    grid_carbon_intensity: Optional[Decimal] = Field(None, ge=0)
    repurposing_option: Optional[RepurposingType] = None
    repurposing_cost_usd_mw: Optional[Decimal] = Field(None, ge=0)
    is_operating: Optional[bool] = None


class PowerPlantResponse(PowerPlantBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    counterparty_id: UUID
    is_operating: bool
    created_at: datetime
    updated_at: datetime


class PowerPlantListResponse(BaseModel):
    items: List[PowerPlantResponse]
    total: int
    page: int
    page_size: int


# ==================== INFRASTRUCTURE ASSET ====================

class InfrastructureAssetBase(BaseModel):
    asset_name: str = Field(..., max_length=255)
    asset_type: InfrastructureType
    asset_location: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    country_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}$")
    design_capacity: Optional[str] = Field(None, max_length=100)
    design_capacity_unit: Optional[str] = Field(None, max_length=20)
    current_capacity_utilized: Optional[str] = Field(None, max_length=100)
    utilization_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    commissioning_year: Optional[int] = Field(None, ge=1900, le=2100)
    expected_retirement_year: Optional[int] = Field(None, ge=1900, le=2100)
    remaining_book_value_usd: Optional[Decimal] = Field(None, ge=0)
    replacement_cost_usd: Optional[Decimal] = Field(None, ge=0)
    contract_maturity_profile: Optional[Dict[str, Decimal]] = None  # {2025: 100000, 2026: 80000, ...}
    take_or_pay_exposure_usd: Optional[Decimal] = Field(None, ge=0)
    contracted_volume_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    hydrogen_ready: bool = False
    ammonia_ready: bool = False
    ccs_compatible: bool = False
    regulatory_status: Optional[str] = Field(None, max_length=50)
    environmental_permits: Optional[Dict] = None


class InfrastructureAssetCreate(InfrastructureAssetBase):
    counterparty_id: UUID


class InfrastructureAssetUpdate(BaseModel):
    asset_name: Optional[str] = Field(None, max_length=255)
    asset_type: Optional[InfrastructureType] = None
    asset_location: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    country_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}$")
    design_capacity: Optional[str] = Field(None, max_length=100)
    design_capacity_unit: Optional[str] = Field(None, max_length=20)
    current_capacity_utilized: Optional[str] = Field(None, max_length=100)
    utilization_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    commissioning_year: Optional[int] = Field(None, ge=1900, le=2100)
    expected_retirement_year: Optional[int] = Field(None, ge=1900, le=2100)
    remaining_book_value_usd: Optional[Decimal] = Field(None, ge=0)
    replacement_cost_usd: Optional[Decimal] = Field(None, ge=0)
    contract_maturity_profile: Optional[Dict[str, Decimal]] = None
    take_or_pay_exposure_usd: Optional[Decimal] = Field(None, ge=0)
    contracted_volume_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    hydrogen_ready: Optional[bool] = None
    ammonia_ready: Optional[bool] = None
    ccs_compatible: Optional[bool] = None
    regulatory_status: Optional[str] = Field(None, max_length=50)
    environmental_permits: Optional[Dict] = None
    is_operating: Optional[bool] = None


class InfrastructureAssetResponse(InfrastructureAssetBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    counterparty_id: UUID
    is_operating: bool
    created_at: datetime
    updated_at: datetime


class InfrastructureAssetListResponse(BaseModel):
    items: List[InfrastructureAssetResponse]
    total: int
    page: int
    page_size: int


# ==================== RESERVE IMPAIRMENT CALCULATION ====================

class ReserveImpairmentRequest(BaseModel):
    reserve_ids: List[UUID]
    scenario_id: UUID
    target_years: List[int] = [2030, 2040, 2050]
    discount_rate: Decimal = Field(Decimal("0.08"), ge=0, le=0.5)
    commodity_price_forecast: Optional[Dict[int, Decimal]] = None
    carbon_price_forecast: Optional[Dict[int, Decimal]] = None


class YearlyImpairment(BaseModel):
    year: int
    demand_reduction_percent: Decimal
    commodity_price_usd: Decimal
    carbon_price_usd_tco2: Decimal
    economic_reserves_mmBOE: Decimal
    stranded_volume_mmBOE: Decimal
    stranded_volume_percent: Decimal
    npv_usd: Decimal


class ReserveImpairmentResult(BaseModel):
    reserve_id: UUID
    asset_name: str
    reserve_type: str
    total_reserves_mmBOE: Decimal
    baseline_npv_usd: Decimal
    scenario_npv_usd: Decimal
    npv_impact_percent: Decimal
    total_stranded_percent: Decimal
    total_stranded_value_usd: Decimal
    yearly_impairments: List[YearlyImpairment]
    stranding_risk_score: Decimal
    risk_category: RiskCategory
    key_drivers: List[str]
    recommendations: List[str]


class ReserveImpairmentResponse(BaseModel):
    scenario_id: UUID
    scenario_name: str
    calculation_date: datetime
    results: List[ReserveImpairmentResult]
    portfolio_summary: Dict


# ==================== POWER PLANT VALUATION ====================

class PowerPlantValuationRequest(BaseModel):
    plant_ids: List[UUID]
    scenario_id: UUID
    target_years: List[int] = [2030, 2040, 2050]
    discount_rate: Decimal = Field(Decimal("0.06"), ge=0, le=0.5)
    include_repurposing: bool = True
    wholesale_price_forecast: Optional[Dict[int, Decimal]] = None
    carbon_price_forecast: Optional[Dict[int, Decimal]] = None


class YearlyValuation(BaseModel):
    year: int
    capacity_factor: Decimal
    wholesale_price_usd_mwh: Decimal
    carbon_cost_usd_mwh: Decimal
    revenue_usd: Decimal
    opex_usd: Decimal
    fuel_cost_usd: Decimal
    ebitda_usd: Decimal


class RepurposingOption(BaseModel):
    option_type: str  # ccs, hydrogen, storage, retirement
    capital_cost_usd: Decimal
    annual_savings_usd: Decimal
    payback_years: Decimal
    npv_impact_usd: Decimal
    feasibility_score: Decimal


class PowerPlantValuationResult(BaseModel):
    plant_id: UUID
    plant_name: str
    technology_type: str
    capacity_mw: Decimal
    remaining_life_years: int
    baseline_npv_usd: Decimal
    scenario_npv_usd: Decimal
    npv_impact_percent: Decimal
    optimal_retirement_year: Optional[int]
    early_retirement_npv_usd: Optional[Decimal]
    yearly_valuations: List[YearlyValuation]
    repurposing_options: List[RepurposingOption]
    stranding_risk_score: Decimal
    risk_category: RiskCategory
    recommended_action: str


class PowerPlantValuationResponse(BaseModel):
    scenario_id: UUID
    scenario_name: str
    calculation_date: datetime
    results: List[PowerPlantValuationResult]
    portfolio_summary: Dict


# ==================== INFRASTRUCTURE VALUATION ====================

class InfrastructureValuationRequest(BaseModel):
    asset_ids: List[UUID]
    scenario_id: UUID
    target_years: List[int] = [2030, 2040, 2050]
    discount_rate: Decimal = Field(Decimal("0.07"), ge=0, le=0.5)
    demand_forecast: Optional[Dict[int, Decimal]] = None


class InfrastructureValuationResult(BaseModel):
    asset_id: UUID
    asset_name: str
    asset_type: str
    baseline_npv_usd: Decimal
    scenario_npv_usd: Decimal
    npv_impact_percent: Decimal
    stranded_value_usd: Decimal
    utilization_decline_percent: Decimal
    contract_exposure_at_risk_usd: Decimal
    stranding_risk_score: Decimal
    risk_category: RiskCategory
    transition_readiness: Dict  # {hydrogen_ready, ammonia_ready, ccs_compatible}
    recommended_action: str


class InfrastructureValuationResponse(BaseModel):
    scenario_id: UUID
    scenario_name: str
    calculation_date: datetime
    results: List[InfrastructureValuationResult]
    portfolio_summary: Dict


# ==================== STRANDED ASSET CALCULATION (DB Record) ====================

class StrandedAssetCalculationBase(BaseModel):
    asset_type: AssetType
    asset_id: UUID
    scenario_id: Optional[UUID] = None
    target_year: int = Field(..., ge=2020, le=2100)
    stranded_volume_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    stranded_volume_unit: Optional[str] = Field(None, max_length=20)
    stranded_value_usd: Optional[Decimal] = Field(None, ge=0)
    baseline_npv_usd: Optional[Decimal] = None
    scenario_npv_usd: Optional[Decimal] = None
    npv_impact_percent: Optional[Decimal] = None
    carbon_price_usd_tco2: Optional[Decimal] = Field(None, ge=0)
    commodity_price_usd: Optional[Decimal] = Field(None, ge=0)
    demand_reduction_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    optimal_retirement_year: Optional[int] = Field(None, ge=2020, le=2100)
    early_retirement_value_usd: Optional[Decimal] = None
    stranding_risk_score: Optional[Decimal] = Field(None, ge=0, le=1)
    risk_category: Optional[RiskCategory] = None
    key_assumptions: Optional[Dict] = None
    sensitivity_analysis: Optional[Dict] = None


class StrandedAssetCalculationCreate(StrandedAssetCalculationBase):
    pass


class StrandedAssetCalculationResponse(StrandedAssetCalculationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    calculation_date: datetime


# ==================== TECHNOLOGY DISRUPTION ====================

class TechnologyDisruptionMetricBase(BaseModel):
    metric_type: str = Field(..., max_length=50)
    region: Optional[str] = Field(None, max_length=50)
    country_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}$")
    value: Decimal
    unit: Optional[str] = Field(None, max_length=20)
    scenario_name: Optional[str] = Field(None, max_length=50)
    data_source: Optional[str] = Field(None, max_length=100)
    data_quality: Optional[str] = Field(None, max_length=20)
    is_projection: bool = False


class TechnologyDisruptionMetricCreate(TechnologyDisruptionMetricBase):
    time: datetime


class TechnologyDisruptionMetricResponse(TechnologyDisruptionMetricBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    time: datetime


class TechnologyDisruptionSummary(BaseModel):
    metric_type: str
    region: str
    scenario_name: str
    current_value: Decimal
    current_year: int
    projected_2030: Optional[Decimal] = None
    projected_2040: Optional[Decimal] = None
    projected_2050: Optional[Decimal] = None
    unit: str
    growth_rate_cagr: Optional[Decimal] = None
    chart_data: List[Dict]  # For frontend visualization


# ==================== ENERGY TRANSITION PATHWAY ====================

class EnergyTransitionPathwayBase(BaseModel):
    pathway_name: str = Field(..., max_length=100)
    sector: str = Field(..., max_length=50)  # oil, gas, coal, power
    region: Optional[str] = Field(None, max_length=50)
    country_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}$")
    scenario_id: Optional[UUID] = None
    base_year: int = Field(..., ge=2000, le=2030)
    target_year: int = Field(..., ge=2030, le=2100)
    demand_trajectory: Optional[Dict[str, Decimal]] = None  # {2025: 100, 2030: 85, ...}
    price_trajectory: Optional[Dict[str, Decimal]] = None
    capacity_trajectory: Optional[Dict[str, Decimal]] = None
    peak_demand_year: Optional[int] = Field(None, ge=2020, le=2050)
    net_zero_year: Optional[int] = Field(None, ge=2030, le=2100)
    carbon_price_trajectory: Optional[Dict[str, Decimal]] = None
    policy_assumptions: Optional[Dict] = None
    technology_assumptions: Optional[Dict] = None
    source_document: Optional[str] = Field(None, max_length=255)
    is_active: bool = True


class EnergyTransitionPathwayCreate(EnergyTransitionPathwayBase):
    pass


class EnergyTransitionPathwayUpdate(BaseModel):
    pathway_name: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=50)
    country_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}$")
    scenario_id: Optional[UUID] = None
    base_year: Optional[int] = Field(None, ge=2000, le=2030)
    target_year: Optional[int] = Field(None, ge=2030, le=2100)
    demand_trajectory: Optional[Dict[str, Decimal]] = None
    price_trajectory: Optional[Dict[str, Decimal]] = None
    capacity_trajectory: Optional[Dict[str, Decimal]] = None
    peak_demand_year: Optional[int] = Field(None, ge=2020, le=2050)
    net_zero_year: Optional[int] = Field(None, ge=2030, le=2100)
    carbon_price_trajectory: Optional[Dict[str, Decimal]] = None
    policy_assumptions: Optional[Dict] = None
    technology_assumptions: Optional[Dict] = None
    source_document: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class EnergyTransitionPathwayResponse(EnergyTransitionPathwayBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


class EnergyTransitionPathwayListResponse(BaseModel):
    items: List[EnergyTransitionPathwayResponse]
    total: int


# ==================== CRITICAL ASSETS ALERT ====================

class CriticalAssetAlert(BaseModel):
    alert_id: UUID
    asset_id: UUID
    asset_name: str
    asset_type: AssetType
    counterparty_name: str
    risk_level: RiskCategory
    stranding_risk_score: Decimal
    estimated_impact_usd: Decimal
    time_to_stranding_years: int
    alert_trigger: str
    recommended_action: str
    created_at: datetime
    is_acknowledged: bool = False


class CriticalAssetAlertList(BaseModel):
    alerts: List[CriticalAssetAlert]
    total: int
    critical_count: int
    high_count: int


# ==================== SCENARIO COMPARISON ====================

class ScenarioComparisonRequest(BaseModel):
    asset_ids: List[UUID]
    asset_type: AssetType
    scenario_ids: List[UUID]
    target_year: int = Field(2040, ge=2025, le=2100)


class ScenarioAssetComparison(BaseModel):
    scenario_id: UUID
    scenario_name: str
    npv_usd: Decimal
    stranded_value_usd: Decimal
    stranded_percent: Decimal
    risk_score: Decimal
    risk_category: RiskCategory


class ScenarioComparisonResult(BaseModel):
    asset_id: UUID
    asset_name: str
    asset_type: AssetType
    scenario_comparisons: List[ScenarioAssetComparison]
    best_case_scenario: str
    worst_case_scenario: str
    npv_range_usd: Decimal
    risk_range: Decimal


class ScenarioComparisonResponse(BaseModel):
    target_year: int
    results: List[ScenarioComparisonResult]
    summary: Dict


# ==================== DASHBOARD & PORTFOLIO ====================

class StrandedAssetDashboardKPIs(BaseModel):
    total_assets: int
    total_reserves_count: int
    total_plants_count: int
    total_infrastructure_count: int
    high_risk_assets: int
    critical_risk_assets: int
    total_exposure_usd: Decimal
    stranded_value_at_risk_usd: Decimal
    avg_stranding_risk_score: Decimal
    assets_by_risk_category: Dict[str, int]


class PortfolioStrandingAnalysisRequest(BaseModel):
    portfolio_id: UUID
    scenario_id: UUID
    target_year: int = 2040
    include_reserves: bool = True
    include_plants: bool = True
    include_infrastructure: bool = True


class PortfolioStrandingAnalysisResponse(BaseModel):
    portfolio_id: UUID
    portfolio_name: str
    scenario_id: UUID
    scenario_name: str
    target_year: int
    total_assets_analyzed: int
    total_baseline_npv_usd: Decimal
    total_scenario_npv_usd: Decimal
    total_npv_impact_usd: Decimal
    total_npv_impact_percent: Decimal
    total_stranded_value_usd: Decimal
    avg_stranding_risk_score: Decimal
    risk_distribution: Dict[str, int]
    asset_breakdown: Dict[str, Dict]  # {reserves: {...}, plants: {...}, infrastructure: {...}}
    top_risk_assets: List[Dict]
    recommendations: List[str]
