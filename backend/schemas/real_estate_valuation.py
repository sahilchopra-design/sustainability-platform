"""
Pydantic schemas for Real Estate Valuation Module
Implements three traditional valuation approaches: Income, Cost, and Sales Comparison
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict, Literal, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


# ============ Enums ============

class PropertyType(str, Enum):
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    MULTIFAMILY = "multifamily"
    HOTEL = "hotel"
    SELF_STORAGE = "self_storage"
    HEALTHCARE = "healthcare"
    DATA_CENTER = "data_center"
    MIXED_USE = "mixed_use"


class QualityRating(str, Enum):
    CLASS_A = "class_a"
    CLASS_B = "class_b"
    CLASS_C = "class_c"


class ConditionRating(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class ConstructionType(str, Enum):
    STEEL_FRAME = "steel_frame"
    CONCRETE = "concrete"
    MASONRY = "masonry"
    WOOD_FRAME = "wood_frame"
    PREFABRICATED = "prefabricated"
    MIXED = "mixed"


class IncomeMethod(str, Enum):
    DIRECT_CAPITALIZATION = "direct_capitalization"
    DCF = "dcf"


# ============ Property Schemas ============

class PropertyBase(BaseModel):
    property_name: str = Field(..., max_length=255)
    property_type: PropertyType
    subcategory: Optional[str] = None
    
    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    
    # Physical Characteristics
    year_built: Optional[int] = Field(None, ge=1800, le=2100)
    gross_floor_area_m2: Optional[Decimal] = Field(None, ge=0)
    rentable_area_sf: Optional[Decimal] = Field(None, ge=0)
    land_area_acres: Optional[Decimal] = Field(None, ge=0)
    num_floors: Optional[int] = Field(None, ge=1)
    num_units: Optional[int] = Field(None, ge=1)
    construction_type: Optional[ConstructionType] = None
    quality_rating: Optional[QualityRating] = None
    condition_rating: Optional[ConditionRating] = None
    effective_age: Optional[int] = Field(None, ge=0)
    total_economic_life: Optional[int] = Field(None, ge=1)
    
    # Financial Data
    market_value: Optional[Decimal] = Field(None, ge=0)
    replacement_value: Optional[Decimal] = Field(None, ge=0)
    land_value: Optional[Decimal] = Field(None, ge=0)
    annual_rental_income: Optional[Decimal] = Field(None, ge=0)
    potential_gross_income: Optional[Decimal] = Field(None, ge=0)
    effective_gross_income: Optional[Decimal] = Field(None, ge=0)
    operating_expenses: Optional[Decimal] = Field(None, ge=0)
    noi: Optional[Decimal] = None
    cap_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    
    # Operating Metrics
    vacancy_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    collection_loss_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    expense_ratio: Optional[Decimal] = Field(None, ge=0, le=1)
    
    # Energy & Sustainability
    epc_rating: Optional[str] = None
    epc_score: Optional[Decimal] = None
    energy_intensity_kwh_m2: Optional[Decimal] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    property_name: Optional[str] = None
    property_type: Optional[PropertyType] = None
    subcategory: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    year_built: Optional[int] = None
    gross_floor_area_m2: Optional[Decimal] = None
    rentable_area_sf: Optional[Decimal] = None
    land_area_acres: Optional[Decimal] = None
    num_floors: Optional[int] = None
    num_units: Optional[int] = None
    construction_type: Optional[ConstructionType] = None
    quality_rating: Optional[QualityRating] = None
    condition_rating: Optional[ConditionRating] = None
    effective_age: Optional[int] = None
    total_economic_life: Optional[int] = None
    market_value: Optional[Decimal] = None
    replacement_value: Optional[Decimal] = None
    land_value: Optional[Decimal] = None
    annual_rental_income: Optional[Decimal] = None
    potential_gross_income: Optional[Decimal] = None
    effective_gross_income: Optional[Decimal] = None
    operating_expenses: Optional[Decimal] = None
    noi: Optional[Decimal] = None
    cap_rate: Optional[Decimal] = None
    discount_rate: Optional[Decimal] = None
    vacancy_rate: Optional[Decimal] = None
    collection_loss_rate: Optional[Decimal] = None
    expense_ratio: Optional[Decimal] = None
    epc_rating: Optional[str] = None
    epc_score: Optional[Decimal] = None
    energy_intensity_kwh_m2: Optional[Decimal] = None


class PropertyResponse(PropertyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PropertyListResponse(BaseModel):
    items: List[PropertyResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============ Income Approach Schemas ============

class ExpenseDetails(BaseModel):
    property_taxes: Decimal = Field(0, ge=0)
    insurance: Decimal = Field(0, ge=0)
    utilities: Decimal = Field(0, ge=0)
    maintenance: Decimal = Field(0, ge=0)
    management: Decimal = Field(0, ge=0)
    reserves: Decimal = Field(0, ge=0)
    other: Decimal = Field(0, ge=0)


class DirectCapitalizationRequest(BaseModel):
    property_id: Optional[UUID] = None
    rentable_area_sf: Decimal = Field(..., gt=0)
    market_rent_per_sf: Decimal = Field(..., gt=0)
    other_income: Decimal = Field(0, ge=0)
    vacancy_rate: Decimal = Field(0.05, ge=0, le=1)
    collection_loss_rate: Decimal = Field(0.02, ge=0, le=1)
    operating_expense_ratio: Optional[Decimal] = Field(None, ge=0, le=1)
    cap_rate: Decimal = Field(..., gt=0, le=1)
    expense_details: Optional[ExpenseDetails] = None


class DirectCapitalizationResult(BaseModel):
    pgi: Decimal
    vacancy_loss: Decimal
    collection_loss: Decimal
    egi: Decimal
    operating_expenses: Decimal
    expense_breakdown: Optional[Dict[str, Decimal]] = None
    noi: Decimal
    cap_rate: Decimal
    property_value: Decimal
    value_per_sf: Decimal
    
    # Additional metrics
    expense_ratio: Decimal
    gross_income_multiplier: Decimal
    net_income_multiplier: Decimal


class DCFProjectionYear(BaseModel):
    year: int
    revenue: Decimal
    expenses: Decimal
    noi: Decimal
    debt_service: Decimal
    cfads: Decimal
    cumulative_cash_flow: Decimal


class DCFRequest(BaseModel):
    property_id: Optional[UUID] = None
    projection_years: int = Field(10, ge=1, le=30)
    current_noi: Decimal = Field(..., gt=0)
    revenue_growth_rate: Decimal = Field(0.03, ge=-0.2, le=0.3)
    expense_growth_rate: Decimal = Field(0.02, ge=-0.1, le=0.2)
    inflation_rate: Decimal = Field(0.02, ge=0, le=0.2)
    discount_rate: Decimal = Field(0.08, gt=0, le=0.5)
    terminal_cap_rate: Decimal = Field(0.07, gt=0, le=0.3)
    terminal_growth_rate: Decimal = Field(0.02, ge=0, le=0.1)
    equity_investment: Decimal = Field(..., gt=0)
    debt_service: Decimal = Field(0, ge=0)
    selling_costs_percent: Decimal = Field(0.03, ge=0, le=0.1)


class DCFResult(BaseModel):
    cash_flows: List[DCFProjectionYear]
    terminal_value: Decimal
    terminal_value_present: Decimal
    total_pv_cash_flows: Decimal
    npv: Decimal
    irr: Decimal
    equity_multiple: Decimal
    cash_on_cash_year1: Decimal
    average_cash_on_cash: Decimal
    payback_period_years: Optional[Decimal] = None
    
    # Sensitivity analysis
    sensitivity_cap_rate: Dict[str, Decimal] = {}
    sensitivity_discount_rate: Dict[str, Decimal] = {}


# ============ Cost Approach Schemas ============

class FunctionalDeficiency(BaseModel):
    description: str
    cost_to_cure: Decimal = Field(..., ge=0)


class Superadequacy(BaseModel):
    description: str
    excess_cost: Decimal = Field(..., ge=0)


class ReplacementCostRequest(BaseModel):
    property_id: Optional[UUID] = None
    land_area_acres: Decimal = Field(..., gt=0)
    land_value_per_acre: Decimal = Field(..., gt=0)
    building_area_sf: Decimal = Field(..., gt=0)
    construction_type: ConstructionType
    quality: QualityRating
    location_factor: Decimal = Field(1.0, gt=0, le=3.0)
    effective_age: int = Field(..., ge=0)
    total_economic_life: int = Field(..., ge=1)
    condition_rating: ConditionRating = ConditionRating.GOOD
    functional_deficiencies: List[FunctionalDeficiency] = []
    superadequacies: List[Superadequacy] = []
    external_obsolescence_percent: Decimal = Field(0, ge=0, le=1)


class ReplacementCostResult(BaseModel):
    land_value: Decimal
    
    # Replacement Cost New
    base_cost_per_sf: Decimal
    rcn_before_adjustments: Decimal
    location_factor: Decimal
    rcn: Decimal
    
    # Depreciation breakdown
    age_life_ratio: Decimal
    physical_depreciation: Decimal
    physical_depreciation_percent: Decimal
    
    functional_deficiencies_total: Decimal
    superadequacies_total: Decimal
    functional_obsolescence: Decimal
    
    external_obsolescence: Decimal
    external_obsolescence_percent: Decimal
    
    total_depreciation: Decimal
    total_depreciation_percent: Decimal
    
    # Final values
    depreciated_improvements: Decimal
    property_value: Decimal
    value_per_sf: Decimal


# ============ Sales Comparison Schemas ============

class SubjectProperty(BaseModel):
    property_id: Optional[UUID] = None
    size_sf: Decimal = Field(..., gt=0)
    year_built: int
    quality: QualityRating
    condition: ConditionRating
    location: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class ComparableProperty(BaseModel):
    id: UUID
    sale_price: Decimal = Field(..., gt=0)
    sale_date: date
    size_sf: Decimal = Field(..., gt=0)
    year_built: int
    quality: QualityRating
    condition: ConditionRating
    location: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    occupancy_rate: Optional[Decimal] = None


class SalesComparisonRequest(BaseModel):
    subject_property: SubjectProperty
    comparables: List[ComparableProperty] = Field(..., min_length=1, max_length=10)
    market_appreciation_rate: Decimal = Field(0.005, ge=-0.05, le=0.1)  # Monthly rate


class AdjustmentDetail(BaseModel):
    type: str
    description: str
    amount: Decimal
    percentage: Decimal


class AdjustedComparable(BaseModel):
    comp_id: UUID
    original_sale_price: Decimal
    sale_date: date
    days_since_sale: int
    adjustments: List[AdjustmentDetail]
    total_adjustment: Decimal
    total_adjustment_percent: Decimal
    adjusted_price: Decimal
    adjusted_price_per_sf: Decimal
    weight: Decimal = Field(1.0)


class SalesComparisonResult(BaseModel):
    adjusted_comparables: List[AdjustedComparable]
    
    # Statistical analysis
    mean_adjusted_price: Decimal
    median_adjusted_price: Decimal
    std_dev: Decimal
    coefficient_of_variation: Decimal
    
    # Final values
    reconciled_value: Decimal
    value_per_sf: Decimal
    confidence_range_low: Decimal
    confidence_range_high: Decimal
    confidence_level: str  # high, medium, low
    
    # Adjustment statistics
    avg_gross_adjustment_percent: Decimal
    avg_net_adjustment_percent: Decimal


# ============ Comparable Sales Database Schema ============

class ComparableSaleBase(BaseModel):
    property_type: PropertyType
    address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    
    sale_date: date
    sale_price: Decimal = Field(..., gt=0)
    size_sf: Decimal = Field(..., gt=0)
    
    year_built: Optional[int] = None
    num_units: Optional[int] = None
    occupancy_rate: Optional[Decimal] = None
    quality_rating: Optional[QualityRating] = None
    condition_rating: Optional[ConditionRating] = None
    
    data_source: Optional[str] = None
    verified: bool = False


class ComparableSaleCreate(ComparableSaleBase):
    pass


class ComparableSaleResponse(ComparableSaleBase):
    id: UUID
    price_per_sf: Decimal
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ComparableSaleListResponse(BaseModel):
    items: List[ComparableSaleResponse]
    total: int


# ============ Comprehensive Valuation Schemas ============

class ApproachWeights(BaseModel):
    income: Decimal = Field(0.4, ge=0, le=1)
    cost: Decimal = Field(0.2, ge=0, le=1)
    sales: Decimal = Field(0.4, ge=0, le=1)
    
    @model_validator(mode='after')
    def validate_weights(self):
        total = self.income + self.cost + self.sales
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return self


class ComprehensiveValuationRequest(BaseModel):
    property_id: UUID
    include_income: bool = True
    include_cost: bool = True
    include_sales: bool = True
    income_method: IncomeMethod = IncomeMethod.DIRECT_CAPITALIZATION
    approach_weights: ApproachWeights = ApproachWeights()
    
    # Income approach inputs (optional, will use property defaults if not provided)
    income_inputs: Optional[Dict[str, Any]] = None
    
    # Cost approach inputs
    cost_inputs: Optional[Dict[str, Any]] = None
    
    # Sales comparison inputs
    comparable_ids: Optional[List[UUID]] = None


class ReconciliationResult(BaseModel):
    income_value: Optional[Decimal] = None
    cost_value: Optional[Decimal] = None
    sales_value: Optional[Decimal] = None
    
    income_weight: Decimal
    cost_weight: Decimal
    sales_weight: Decimal
    
    reconciled_value: Decimal
    
    # Reasoning
    approach_reliability: Dict[str, str] = {}
    reconciliation_notes: List[str] = []


class ComprehensiveValuationResult(BaseModel):
    property_id: UUID
    valuation_date: date
    
    income_approach: Optional[DirectCapitalizationResult] = None
    dcf_analysis: Optional[DCFResult] = None
    cost_approach: Optional[ReplacementCostResult] = None
    sales_comparison: Optional[SalesComparisonResult] = None
    
    reconciliation: ReconciliationResult
    
    final_value: Decimal
    value_per_sf: Decimal
    value_range: str
    confidence_level: str


# ============ Valuation History Schema ============

class ValuationBase(BaseModel):
    property_id: UUID
    valuation_date: date
    
    # Income Approach
    income_approach_value: Optional[Decimal] = None
    income_method: Optional[IncomeMethod] = None
    pgi: Optional[Decimal] = None
    egi: Optional[Decimal] = None
    noi: Optional[Decimal] = None
    cap_rate_used: Optional[Decimal] = None
    dcf_npv: Optional[Decimal] = None
    dcf_irr: Optional[Decimal] = None
    
    # Cost Approach
    cost_approach_value: Optional[Decimal] = None
    land_value: Optional[Decimal] = None
    rcn: Optional[Decimal] = None
    physical_depreciation: Optional[Decimal] = None
    functional_obsolescence: Optional[Decimal] = None
    external_obsolescence: Optional[Decimal] = None
    total_depreciation: Optional[Decimal] = None
    depreciated_improvements: Optional[Decimal] = None
    
    # Sales Comparison
    sales_comparison_value: Optional[Decimal] = None
    num_comparables_used: Optional[int] = None
    avg_adjustment_pct: Optional[Decimal] = None
    
    # Reconciliation
    reconciled_base_value: Optional[Decimal] = None
    income_weight: Optional[Decimal] = None
    cost_weight: Optional[Decimal] = None
    sales_weight: Optional[Decimal] = None
    
    # Final Value
    adjusted_value: Optional[Decimal] = None
    value_per_sf: Optional[Decimal] = None
    confidence_range_low: Optional[Decimal] = None
    confidence_range_high: Optional[Decimal] = None


class ValuationCreate(ValuationBase):
    calculation_inputs: Optional[Dict[str, Any]] = None
    calculation_details: Optional[Dict[str, Any]] = None


class ValuationResponse(ValuationBase):
    id: UUID
    calculation_inputs: Optional[Dict[str, Any]] = None
    calculation_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ValuationListResponse(BaseModel):
    items: List[ValuationResponse]
    total: int


# ============ Dashboard & Summary Schemas ============

class ValuationDashboardKPIs(BaseModel):
    total_properties: int
    total_valuations: int
    total_portfolio_value: Decimal
    avg_cap_rate: Decimal
    avg_value_per_sf: Decimal
    properties_by_type: Dict[str, int]
    valuations_by_method: Dict[str, int]
    recent_valuations: List[ValuationResponse]


class MarketCapRates(BaseModel):
    property_type: PropertyType
    quality_class: QualityRating
    market: str
    cap_rate_low: Decimal
    cap_rate_mid: Decimal
    cap_rate_high: Decimal
    as_of_date: date


class ConstructionCosts(BaseModel):
    construction_type: ConstructionType
    quality_class: QualityRating
    region: str
    cost_per_sf_low: Decimal
    cost_per_sf_mid: Decimal
    cost_per_sf_high: Decimal
    as_of_date: date
