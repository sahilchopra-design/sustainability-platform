"""
API Routes: Green Premium + Tenant ESG
=======================================
POST /api/v1/green-premium/assess          — Green premium / brown discount analysis
POST /api/v1/green-premium/tenant-esg      — Tenant ESG profiling
GET  /api/v1/green-premium/reference-data  — Premium/discount reference tables
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.green_premium_engine import (
    GreenPremiumEngine,
    PropertyGreenInput,
    GREEN_RENT_PREMIUM,
    EPC_CAP_RATE_ADJUSTMENT_BPS,
    EPC_RENT_DISCOUNT,
)
from services.tenant_esg_tracker import (
    TenantESGTracker,
    TenantInput,
    PropertyTenantInput,
    GreenLeaseClause,
    CLAUSE_WEIGHTS,
    SECTOR_BENCHMARKS,
)

router = APIRouter(prefix="/api/v1/green-premium", tags=["Green Premium & Tenant ESG"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PropertyGreenInputModel(BaseModel):
    property_id: str
    name: str
    epc_rating: str = Field(..., pattern=r"^(A\+|A|B|C|D|E|F|G)$")
    base_rent_per_m2: float = Field(..., gt=0)
    floor_area_m2: float = Field(..., gt=0)
    market_value: float = Field(..., gt=0)
    base_cap_rate_pct: float = Field(..., gt=0, le=20)
    noi: float = Field(..., gt=0)
    certifications: dict[str, str] = Field(default_factory=dict)
    country: str = "GB"
    property_type: str = "office"


class GreenPremiumRequest(BaseModel):
    properties: list[PropertyGreenInputModel] = Field(..., min_length=1, max_length=500)


class TenantInputModel(BaseModel):
    tenant_id: str
    name: str
    sector: str
    leased_area_m2: float = Field(..., gt=0)
    annual_rent_eur: float = Field(..., ge=0)
    headcount: int = Field(default=0, ge=0)
    scope1_tco2e: float = Field(default=0, ge=0)
    scope2_tco2e: float = Field(default=0, ge=0)
    green_lease_clauses: list[str] = Field(default_factory=list)
    energy_data_reported: bool = False
    has_science_based_target: bool = False
    has_net_zero_commitment: bool = False
    lease_expiry_year: Optional[int] = None


class PropertyTenantInputModel(BaseModel):
    property_id: str
    name: str
    total_lettable_area_m2: float = Field(..., gt=0)
    tenants: list[TenantInputModel] = Field(..., min_length=1)
    epc_rating: str = "C"
    country: str = "GB"


class TenantESGRequest(BaseModel):
    properties: list[PropertyTenantInputModel] = Field(..., min_length=1, max_length=200)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_green_input(m: PropertyGreenInputModel) -> PropertyGreenInput:
    return PropertyGreenInput(
        property_id=m.property_id, name=m.name, epc_rating=m.epc_rating,
        base_rent_per_m2=m.base_rent_per_m2, floor_area_m2=m.floor_area_m2,
        market_value=m.market_value, base_cap_rate_pct=m.base_cap_rate_pct,
        noi=m.noi, certifications=m.certifications,
        country=m.country, property_type=m.property_type,
    )


def _to_tenant(m: TenantInputModel) -> TenantInput:
    return TenantInput(
        tenant_id=m.tenant_id, name=m.name, sector=m.sector,
        leased_area_m2=m.leased_area_m2, annual_rent_eur=m.annual_rent_eur,
        headcount=m.headcount, scope1_tco2e=m.scope1_tco2e,
        scope2_tco2e=m.scope2_tco2e, green_lease_clauses=m.green_lease_clauses,
        energy_data_reported=m.energy_data_reported,
        has_science_based_target=m.has_science_based_target,
        has_net_zero_commitment=m.has_net_zero_commitment,
        lease_expiry_year=m.lease_expiry_year,
    )


def _to_property_tenant(m: PropertyTenantInputModel) -> PropertyTenantInput:
    return PropertyTenantInput(
        property_id=m.property_id, name=m.name,
        total_lettable_area_m2=m.total_lettable_area_m2,
        tenants=[_to_tenant(t) for t in m.tenants],
        epc_rating=m.epc_rating, country=m.country,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_cert(c) -> dict:
    return {
        "scheme": c.scheme, "level": c.level,
        "rent_premium_pct": c.rent_premium_pct,
        "rent_premium_eur_m2": c.rent_premium_eur_m2,
        "annual_premium_eur": c.annual_premium_eur,
    }


def _ser_green_prop(r) -> dict:
    return {
        "property_id": r.property_id, "name": r.name,
        "epc_rating": r.epc_rating, "is_green": r.is_green, "is_brown": r.is_brown,
        "certification_premiums": [_ser_cert(c) for c in r.certification_premiums],
        "total_cert_premium_pct": r.total_cert_premium_pct,
        "total_cert_premium_eur_m2": r.total_cert_premium_eur_m2,
        "epc_rent_adjustment_pct": r.epc_rent_adjustment_pct,
        "epc_cap_rate_adjustment_bps": r.epc_cap_rate_adjustment_bps,
        "brown_vacancy_months": r.brown_vacancy_months,
        "base_rent_per_m2": r.base_rent_per_m2,
        "green_adjusted_rent_per_m2": r.green_adjusted_rent_per_m2,
        "net_rent_change_pct": r.net_rent_change_pct,
        "base_market_value": r.base_market_value,
        "green_adjusted_value": r.green_adjusted_value,
        "value_impact_eur": r.value_impact_eur,
        "value_impact_pct": r.value_impact_pct,
        "annual_void_cost_eur": r.annual_void_cost_eur,
    }


def _ser_tenant_profile(p) -> dict:
    return {
        "tenant_id": p.tenant_id, "name": p.name, "sector": p.sector,
        "leased_area_m2": p.leased_area_m2,
        "carbon_intensity_per_employee": p.carbon_intensity_per_employee,
        "carbon_intensity_per_m2": p.carbon_intensity_per_m2,
        "sector_benchmark_per_employee": p.sector_benchmark_per_employee,
        "vs_benchmark_pct": p.vs_benchmark_pct,
        "green_lease_score": p.green_lease_score,
        "green_lease_clause_count": p.green_lease_clause_count,
        "green_lease_clause_coverage": p.green_lease_clause_coverage,
        "energy_data_reported": p.energy_data_reported,
        "has_science_based_target": p.has_science_based_target,
        "has_net_zero_commitment": p.has_net_zero_commitment,
        "tenant_esg_score": p.tenant_esg_score,
    }


def _ser_property_tenant(r) -> dict:
    return {
        "property_id": r.property_id, "name": r.name,
        "total_lettable_area_m2": r.total_lettable_area_m2,
        "occupied_area_m2": r.occupied_area_m2,
        "occupancy_rate_pct": r.occupancy_rate_pct,
        "tenant_count": r.tenant_count,
        "green_lease_coverage_pct": r.green_lease_coverage_pct,
        "avg_green_lease_score": r.avg_green_lease_score,
        "clause_coverage": r.clause_coverage,
        "total_scope1_tco2e": r.total_scope1_tco2e,
        "total_scope2_tco2e": r.total_scope2_tco2e,
        "total_tenant_emissions_tco2e": r.total_tenant_emissions_tco2e,
        "carbon_intensity_per_m2": r.carbon_intensity_per_m2,
        "energy_data_reporting_pct": r.energy_data_reporting_pct,
        "sbt_coverage_pct": r.sbt_coverage_pct,
        "net_zero_coverage_pct": r.net_zero_coverage_pct,
        "property_tenant_esg_score": r.property_tenant_esg_score,
        "tenant_profiles": [_ser_tenant_profile(p) for p in r.tenant_profiles],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_green_premium(req: GreenPremiumRequest):
    """Assess green premium / brown discount across a portfolio."""
    engine = GreenPremiumEngine()
    inputs = [_to_green_input(p) for p in req.properties]
    result = engine.assess_portfolio(inputs)
    return {
        "total_properties": result.total_properties,
        "green_count": result.green_count,
        "neutral_count": result.neutral_count,
        "brown_count": result.brown_count,
        "green_pct": result.green_pct,
        "brown_pct": result.brown_pct,
        "total_base_rent": result.total_base_rent,
        "total_green_adjusted_rent": result.total_green_adjusted_rent,
        "portfolio_rent_uplift_pct": result.portfolio_rent_uplift_pct,
        "total_base_value": result.total_base_value,
        "total_green_adjusted_value": result.total_green_adjusted_value,
        "portfolio_value_impact_eur": result.portfolio_value_impact_eur,
        "portfolio_value_impact_pct": result.portfolio_value_impact_pct,
        "total_annual_void_cost": result.total_annual_void_cost,
        "wavg_cert_premium_pct": result.wavg_cert_premium_pct,
        "wavg_epc_adjustment_pct": result.wavg_epc_adjustment_pct,
        "wavg_cap_rate_shift_bps": result.wavg_cap_rate_shift_bps,
        "property_results": [_ser_green_prop(r) for r in result.property_results],
    }


@router.post("/tenant-esg")
def assess_tenant_esg(req: TenantESGRequest):
    """Assess tenant ESG profiles across properties."""
    tracker = TenantESGTracker()
    inputs = [_to_property_tenant(p) for p in req.properties]
    result = tracker.assess_portfolio(inputs)
    return {
        "total_properties": result.total_properties,
        "total_tenants": result.total_tenants,
        "total_occupied_area_m2": result.total_occupied_area_m2,
        "avg_occupancy_rate_pct": result.avg_occupancy_rate_pct,
        "portfolio_green_lease_coverage_pct": result.portfolio_green_lease_coverage_pct,
        "portfolio_avg_green_lease_score": result.portfolio_avg_green_lease_score,
        "portfolio_clause_coverage": result.portfolio_clause_coverage,
        "total_tenant_emissions_tco2e": result.total_tenant_emissions_tco2e,
        "portfolio_carbon_intensity_per_m2": result.portfolio_carbon_intensity_per_m2,
        "portfolio_energy_reporting_pct": result.portfolio_energy_reporting_pct,
        "portfolio_sbt_coverage_pct": result.portfolio_sbt_coverage_pct,
        "portfolio_net_zero_coverage_pct": result.portfolio_net_zero_coverage_pct,
        "portfolio_tenant_esg_score": result.portfolio_tenant_esg_score,
        "property_results": [_ser_property_tenant(r) for r in result.property_results],
    }


@router.get("/reference-data")
def get_reference_data():
    """Return green premium / brown discount reference tables."""
    return {
        "green_rent_premium_by_certification": GREEN_RENT_PREMIUM,
        "epc_cap_rate_adjustment_bps": EPC_CAP_RATE_ADJUSTMENT_BPS,
        "epc_rent_discount_pct": EPC_RENT_DISCOUNT,
        "green_lease_clauses": [c.value for c in GreenLeaseClause],
        "green_lease_clause_weights": CLAUSE_WEIGHTS,
        "sector_carbon_benchmarks_tco2e_per_employee": SECTOR_BENCHMARKS,
    }
