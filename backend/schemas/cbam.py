"""
CBAM Pydantic v2 schemas — comprehensive validation for all CBAM entities.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class CBAMSector(str, Enum):
    IRON_STEEL = "iron_steel"
    ALUMINUM = "aluminum"
    CEMENT = "cement"
    FERTILIZERS = "fertilizers"
    HYDROGEN = "hydrogen"
    ELECTRICITY = "electricity"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"


class RiskCategory(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class AccreditationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


# ==================== PRODUCT CATEGORY ====================

class CBAMProductCategoryBase(BaseModel):
    cn_code: str = Field(..., pattern=r"^\d{8}$", description="8-digit Combined Nomenclature code")
    hs_code: str = Field(..., pattern=r"^\d{6}$", description="6-digit Harmonized System code")
    sector: CBAMSector
    product_name: str = Field(..., max_length=255)
    default_direct_emissions: Optional[Decimal] = Field(None, ge=0, description="tCO2/tonne product")
    default_indirect_emissions: Optional[Decimal] = Field(None, ge=0, description="tCO2/tonne product")


class CBAMProductCategoryCreate(CBAMProductCategoryBase):
    is_active: bool = True


class CBAMProductCategoryResponse(CBAMProductCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    default_total_emissions: Optional[Decimal] = None
    is_active: bool
    created_at: Optional[datetime] = None


class CBAMProductCategoryUpdate(BaseModel):
    product_name: Optional[str] = Field(None, max_length=255)
    default_direct_emissions: Optional[Decimal] = Field(None, ge=0)
    default_indirect_emissions: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


# ==================== SUPPLIER ====================

class CBAMSupplierBase(BaseModel):
    supplier_name: str = Field(..., max_length=255)
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    has_domestic_carbon_price: bool = False
    domestic_carbon_price: Optional[Decimal] = Field(None, ge=0, description="EUR/tCO2")


class CBAMSupplierCreate(CBAMSupplierBase):
    counterparty_id: Optional[str] = None


class CBAMSupplierResponse(CBAMSupplierBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    verification_status: Optional[str] = "unverified"
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    created_at: Optional[datetime] = None


class CBAMSupplierUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, max_length=255)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    verification_status: Optional[VerificationStatus] = None
    has_domestic_carbon_price: Optional[bool] = None
    domestic_carbon_price: Optional[Decimal] = Field(None, ge=0)


# ==================== EMBEDDED EMISSIONS ====================

class CBAMEmissionsBase(BaseModel):
    supplier_id: str
    product_category_id: str
    reporting_year: int = Field(..., ge=2023, le=2050)
    reporting_quarter: int = Field(1, ge=1, le=4)
    import_volume_tonnes: Decimal = Field(0, ge=0)
    direct_attributed_emissions: Optional[Decimal] = Field(None, ge=0, description="tCO2")
    indirect_attributed_emissions: Optional[Decimal] = Field(None, ge=0, description="tCO2")
    specific_direct_emissions: Optional[Decimal] = Field(None, ge=0, description="tCO2/tonne product")
    specific_indirect_emissions: Optional[Decimal] = Field(None, ge=0, description="tCO2/tonne product")


class CBAMEmissionsCreate(CBAMEmissionsBase):
    use_default_values: bool = False


class CBAMEmissionsResponse(CBAMEmissionsBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    specific_total_emissions: Optional[Decimal] = None
    is_verified: bool = False
    uses_default_values: bool = False


class EmissionsCalculationRequest(BaseModel):
    supplier_id: str
    product_category_id: str
    production_volume_tonnes: Decimal = Field(..., gt=0)
    reporting_year: int = Field(..., ge=2023, le=2050)
    electricity_consumed_mwh: Optional[Decimal] = Field(None, ge=0)
    use_default_values: bool = False


class EmissionsCalculationResult(BaseModel):
    calculation_id: str
    specific_direct_emissions: Decimal
    specific_indirect_emissions: Decimal
    specific_total_emissions: Decimal
    total_embedded_emissions_tco2: Decimal
    uses_default_values: bool
    default_value_markup_applied: Decimal = Decimal("0")


# ==================== COST PROJECTION ====================

class CostProjectionRequest(BaseModel):
    portfolio_id: Optional[str] = None
    scenario_id: Optional[str] = None
    supplier_id: Optional[str] = None
    projection_years: int = Field(5, ge=1, le=30)


class YearlyProjection(BaseModel):
    year: int
    import_volume_tonnes: Decimal
    embedded_emissions_tco2: Decimal
    eu_ets_price_eur: Decimal
    domestic_carbon_credit_eur: Decimal = Decimal("0")
    free_allocation_pct: Decimal = Decimal("0")
    gross_cbam_cost_eur: Decimal
    net_cbam_cost_eur: Decimal
    cost_as_pct_of_revenue: Optional[Decimal] = None


class CostProjectionResult(BaseModel):
    supplier_id: Optional[str] = None
    scenario: str
    total_cbam_cost_eur: Decimal
    yearly_projections: List[YearlyProjection]


class CostCalculationRequest(BaseModel):
    emissions_tco2: Decimal = Field(..., ge=0)
    eu_ets_price: Decimal = Field(..., ge=0, description="EUR/tCO2")
    domestic_carbon_price: Decimal = Field(Decimal("0"), ge=0, description="EUR/tCO2")
    free_allocation_pct: Decimal = Field(Decimal("0"), ge=0, le=100)


class CostCalculationResult(BaseModel):
    gross_cost_eur: Decimal
    domestic_credit_eur: Decimal
    free_allocation_reduction_eur: Decimal
    net_cbam_cost_eur: Decimal


# ==================== SUPPLIER RISK ====================

class SupplierRiskProfile(BaseModel):
    supplier_id: str
    supplier_name: str
    country_code: str
    overall_risk_score: float = Field(..., ge=0, le=1)
    risk_category: str
    has_domestic_carbon_price: bool
    domestic_carbon_price: Optional[float] = None
    emissions_summary: Optional[Dict] = None
    projected_annual_cbam_cost: Optional[float] = None
    alternative_suppliers: Optional[List[str]] = None


# ==================== COMPLIANCE REPORT ====================

class CBAMComplianceReportBase(BaseModel):
    report_year: int = Field(..., ge=2023, le=2050)
    report_quarter: int = Field(..., ge=1, le=4)


class CBAMComplianceReportCreate(CBAMComplianceReportBase):
    portfolio_id: Optional[str] = None
    reporting_entity_id: Optional[str] = None


class CBAMComplianceReportResponse(CBAMComplianceReportBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    submission_status: str = "draft"
    total_imports_tonnes: Optional[float] = None
    total_embedded_emissions: Optional[float] = None
    total_certificate_cost: Optional[float] = None
    compliance_status: Optional[str] = None
    supplier_count: int = 0
    product_count: int = 0
    created_at: Optional[datetime] = None


# ==================== COUNTRY RISK ====================

class CBAMCountryRiskBase(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    country_name: Optional[str] = Field(None, max_length=100)
    has_carbon_pricing: bool = False
    carbon_price_eur: Optional[Decimal] = Field(None, ge=0)
    grid_emission_factor: Optional[Decimal] = Field(None, ge=0, description="tCO2/MWh")
    overall_risk_score: Optional[float] = Field(None, ge=0, le=1)
    risk_category: Optional[str] = None
    default_value_markup: Optional[Decimal] = Field(None, ge=0, le=1)


class CBAMCountryRiskResponse(CBAMCountryRiskBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ==================== CERTIFICATE PRICE ====================

class CBAMCertificatePriceBase(BaseModel):
    price_date: str = Field(..., description="YYYY-MM-DD or YYYY")
    eu_ets_auction_price_eur: Optional[Decimal] = Field(None, ge=0)
    cbam_certificate_price_eur: Optional[Decimal] = Field(None, ge=0)
    scenario_name: Optional[str] = None
    is_projection: bool = False


class CBAMCertificatePriceResponse(CBAMCertificatePriceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ==================== VERIFIER ====================

class CBAMVerifierBase(BaseModel):
    verifier_name: str = Field(..., max_length=255)
    accreditation_body: Optional[str] = Field(None, max_length=100)
    accreditation_number: Optional[str] = Field(None, max_length=50)
    country_code: str = Field(..., min_length=2, max_length=2)
    accredited_sectors: List[str] = []
    accreditation_status: AccreditationStatus = AccreditationStatus.ACTIVE


class CBAMVerifierResponse(CBAMVerifierBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ==================== DASHBOARD / ANALYTICS ====================

class CBAMDashboardResponse(BaseModel):
    total_suppliers: int
    total_products: int
    total_countries: int
    emissions_records: int
    high_risk_suppliers: int
    total_embedded_emissions_tco2: float
    sector_breakdown: Dict[str, int]


class CBAMSectorSummary(BaseModel):
    sector: str
    product_count: int
    avg_direct_emissions: float
    avg_indirect_emissions: float
    avg_total_emissions: float
    total_import_volume: Optional[float] = None


class FreeAllocationSchedule(BaseModel):
    """EU CBAM free allocation phase-out schedule (2026-2034)."""
    schedule: Dict[int, float] = Field(
        description="Year → free allocation percentage",
        default={
            2026: 97.5, 2027: 95.0, 2028: 90.0, 2029: 77.5, 2030: 51.5,
            2031: 39.0, 2032: 26.5, 2033: 14.0, 2034: 0.0,
        },
    )
