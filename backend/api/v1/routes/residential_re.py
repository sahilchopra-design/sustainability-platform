"""
API Routes: Residential Real Estate
=====================================
POST /api/v1/residential-re/value-property         — Hedonic valuation + EPC/CRREM risk
POST /api/v1/residential-re/mortgage-portfolio      — Mortgage portfolio climate risk
POST /api/v1/residential-re/decarb-pathway          — Affordable housing decarbonisation plan
GET  /api/v1/residential-re/ref/epc-energy          — EPC → energy intensity map
GET  /api/v1/residential-re/ref/mees-timelines      — MEES regulatory timelines by country
GET  /api/v1/residential-re/ref/crrem-pathway       — CRREM 1.5°C residential pathway
GET  /api/v1/residential-re/ref/retrofit-costs      — Retrofit cost matrix by EPC band
GET  /api/v1/residential-re/ref/decarb-measures     — Available decarbonisation measures
GET  /api/v1/residential-re/ref/hedonic-coefficients — Hedonic regression coefficients
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.residential_re_engine import ResidentialRealEstateEngine, ResidentialPropertyInput, MortgagePortfolioInput

router = APIRouter(prefix="/api/v1/residential-re", tags=["Residential Real Estate"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PropertyRequest(BaseModel):
    property_id: str
    property_type: str = Field("single_family", pattern=r"^(single_family|multi_family|social_housing|pbsa)$")
    address: str = ""
    country: str = "GB"
    floor_area_m2: float = Field(70, ge=10)
    bedrooms: int = Field(3, ge=0)
    bathrooms: int = Field(1, ge=0)
    age_years: int = Field(30, ge=0)
    garden_m2: float = Field(0, ge=0)
    parking_spaces: int = Field(0, ge=0)
    epc_rating: str = Field("D", pattern=r"^[A-G]$")
    energy_kwh_m2_yr: float = Field(0, ge=0)
    in_flood_zone: bool = False
    proximity_transport_km: float = Field(1.0, ge=0)
    market_value_eur: float = Field(0, ge=0)
    mortgage_ltv: float = Field(0.75, ge=0, le=1.0)
    mortgage_balance_eur: float = Field(0, ge=0)


class MortgagePortfolioRequest(BaseModel):
    portfolio_id: str
    properties: list[PropertyRequest]
    carbon_price_eur_tco2: float = Field(80, ge=0)
    stress_scenario: str = Field("moderate", pattern=r"^(moderate|severe|extreme)$")


class DecarbPathwayRequest(BaseModel):
    units: list[dict]
    target_epc: str = Field("C", pattern=r"^[A-G]$")
    energy_cost_eur_kwh: float = Field(0.28, ge=0)
    grid_ef_kgco2_kwh: float = Field(0.233, ge=0)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_property(req: PropertyRequest) -> ResidentialPropertyInput:
    return ResidentialPropertyInput(
        property_id=req.property_id,
        property_type=req.property_type,
        address=req.address,
        country=req.country,
        floor_area_m2=req.floor_area_m2,
        bedrooms=req.bedrooms,
        bathrooms=req.bathrooms,
        age_years=req.age_years,
        garden_m2=req.garden_m2,
        parking_spaces=req.parking_spaces,
        epc_rating=req.epc_rating,
        energy_kwh_m2_yr=req.energy_kwh_m2_yr,
        in_flood_zone=req.in_flood_zone,
        proximity_transport_km=req.proximity_transport_km,
        market_value_eur=req.market_value_eur,
        mortgage_ltv=req.mortgage_ltv,
        mortgage_balance_eur=req.mortgage_balance_eur,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/value-property")
def value_property(req: PropertyRequest):
    """Hedonic valuation with EPC premium/discount, CRREM stranding, MEES compliance, climate-adjusted LTV."""
    engine = ResidentialRealEstateEngine()
    inp = _to_property(req)
    r = engine.value_property(inp)
    return {
        "property_id": r.property_id,
        "property_type": r.property_type,
        "hedonic_value_eur": r.hedonic_value_eur,
        "value_per_m2_eur": r.value_per_m2_eur,
        "epc_premium_pct": r.epc_premium_pct,
        "flood_discount_pct": r.flood_discount_pct,
        "current_epc": r.current_epc,
        "energy_intensity_kwh_m2": r.energy_intensity_kwh_m2,
        "crrem_stranding_year": r.crrem_stranding_year,
        "years_to_stranding": r.years_to_stranding,
        "mees_compliant": r.mees_compliant,
        "mees_compliance_year": r.mees_compliance_year,
        "retrofit_cost_to_c_eur": r.retrofit_cost_to_c_eur,
        "retrofit_cost_to_b_eur": r.retrofit_cost_to_b_eur,
        "climate_adjusted_value_eur": r.climate_adjusted_value_eur,
        "climate_ltv": r.climate_ltv,
        "ltv_stress_bps": r.ltv_stress_bps,
        "recommendations": r.recommendations,
    }


@router.post("/mortgage-portfolio")
def assess_mortgage_portfolio(req: MortgagePortfolioRequest):
    """Mortgage portfolio climate risk: EPC distribution, stranding, LTV stress."""
    engine = ResidentialRealEstateEngine()
    props = [_to_property(p) for p in req.properties]
    inp = MortgagePortfolioInput(
        portfolio_id=req.portfolio_id,
        properties=props,
        carbon_price_eur_tco2=req.carbon_price_eur_tco2,
        stress_scenario=req.stress_scenario,
    )
    r = engine.assess_mortgage_portfolio(inp)
    return {
        "portfolio_id": r.portfolio_id,
        "total_properties": r.total_properties,
        "total_mortgage_exposure_eur": r.total_mortgage_exposure_eur,
        "avg_ltv": r.avg_ltv,
        "avg_climate_ltv": r.avg_climate_ltv,
        "ltv_stress_avg_bps": r.ltv_stress_avg_bps,
        "epc_distribution": r.epc_distribution,
        "below_mees_count": r.below_mees_count,
        "below_mees_pct": r.below_mees_pct,
        "stranding_before_2030_count": r.stranding_before_2030_count,
        "stranding_before_2030_pct": r.stranding_before_2030_pct,
        "total_retrofit_cost_to_c_eur": r.total_retrofit_cost_to_c_eur,
        "avg_energy_intensity_kwh_m2": r.avg_energy_intensity_kwh_m2,
        "weighted_avg_epc_band": r.weighted_avg_epc_band,
        "risk_band": r.risk_band,
        "property_results": r.property_results,
    }


@router.post("/decarb-pathway")
def decarb_pathway(req: DecarbPathwayRequest):
    """Affordable housing decarbonisation pathway with measure recommendations."""
    engine = ResidentialRealEstateEngine()
    r = engine.decarb_pathway(
        units=req.units,
        target_epc=req.target_epc,
        energy_cost_eur_kwh=req.energy_cost_eur_kwh,
        grid_ef_kgco2_kwh=req.grid_ef_kgco2_kwh,
    )
    return {
        "total_units": r.total_units,
        "current_avg_energy_kwh_m2": r.current_avg_energy_kwh_m2,
        "target_energy_kwh_m2": r.target_energy_kwh_m2,
        "energy_gap_kwh_m2": r.energy_gap_kwh_m2,
        "recommended_measures": r.recommended_measures,
        "total_capex_eur": r.total_capex_eur,
        "annual_energy_savings_eur": r.annual_energy_savings_eur,
        "payback_years": r.payback_years,
        "co2_reduction_tco2_yr": r.co2_reduction_tco2_yr,
        "units_by_current_epc": r.units_by_current_epc,
        "units_reaching_target": r.units_reaching_target,
        "units_remaining_gap": r.units_remaining_gap,
    }


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/epc-energy")
def ref_epc_energy():
    """EPC rating → estimated energy intensity mapping."""
    return {"epc_energy_map": ResidentialRealEstateEngine().get_epc_energy_map()}


@router.get("/ref/mees-timelines")
def ref_mees_timelines():
    """MEES regulatory timelines by country."""
    return {"mees_timelines": ResidentialRealEstateEngine().get_mees_timelines()}


@router.get("/ref/crrem-pathway")
def ref_crrem_pathway():
    """CRREM 1.5°C residential decarbonisation pathway."""
    return {"crrem_pathway": ResidentialRealEstateEngine().get_crrem_residential_pathway()}


@router.get("/ref/retrofit-costs")
def ref_retrofit_costs():
    """Retrofit cost matrix by EPC band improvement."""
    return {"retrofit_costs": ResidentialRealEstateEngine().get_retrofit_cost_matrix()}


@router.get("/ref/decarb-measures")
def ref_decarb_measures():
    """Available decarbonisation measures for affordable housing."""
    return {"measures": ResidentialRealEstateEngine().get_decarb_measures()}


@router.get("/ref/hedonic-coefficients")
def ref_hedonic_coefficients():
    """Hedonic regression coefficients used in valuation."""
    return {"coefficients": ResidentialRealEstateEngine().get_hedonic_coefficients()}
