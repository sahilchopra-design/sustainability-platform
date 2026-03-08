"""
API Routes: EPC Transition Risk + Retrofit CapEx Planner
========================================================
POST /api/v1/epc-retrofit/transition-risk     — EPC transition risk scoring (single or portfolio)
POST /api/v1/epc-retrofit/retrofit-plan       — Retrofit CapEx plan (single or portfolio)
GET  /api/v1/epc-retrofit/measure-catalogue   — Available retrofit measures
GET  /api/v1/epc-retrofit/meps-timelines      — MEPS regulatory timelines by country
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

from services.epc_transition_engine import (
    EPCTransitionEngine,
    PropertyEPCInput,
    MEPS_TIMELINES,
)
from services.retrofit_planner import (
    RetrofitPlanner,
    PropertyRetrofitInput,
    MEASURE_CATALOGUE,
    ENERGY_PRICES,
    GRID_FACTORS,
)

router = APIRouter(prefix="/api/v1/epc-retrofit", tags=["EPC Transition & Retrofit"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PropertyEPCInputModel(BaseModel):
    property_id: str
    name: str
    country: str = Field(..., min_length=2, max_length=2)
    epc_rating: str = Field(..., pattern=r"^(A\+|A|B|C|D|E|F|G)$")
    floor_area_m2: float = Field(..., gt=0)
    market_value: float = Field(..., gt=0)
    annual_rent: float = Field(..., ge=0)
    building_age: int = Field(default=2000, ge=1800, le=2026)
    property_type: str = "office"
    is_leased: bool = True


class TransitionRiskRequest(BaseModel):
    properties: list[PropertyEPCInputModel] = Field(..., min_length=1, max_length=500)


class PropertyRetrofitInputModel(BaseModel):
    property_id: str
    name: str
    country: str = Field(..., min_length=2, max_length=2)
    property_type: str = "office"
    floor_area_m2: float = Field(..., gt=0)
    current_epc: str = Field(..., pattern=r"^(A\+|A|B|C|D|E|F|G)$")
    current_energy_intensity_kwh_m2: float = Field(..., gt=0)
    market_value: float = Field(..., gt=0)
    annual_rent: float = Field(..., ge=0)
    target_epc: Optional[str] = Field(None, pattern=r"^(A\+|A|B|C|D|E|F|G)$")
    discount_rate: float = Field(default=0.06, gt=0, le=0.3)
    carbon_price_eur_t: float = Field(default=90.0, ge=0)
    existing_measures: list[str] = Field(default_factory=list)


class RetrofitPlanRequest(BaseModel):
    properties: list[PropertyRetrofitInputModel] = Field(..., min_length=1, max_length=500)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_epc_input(m: PropertyEPCInputModel) -> PropertyEPCInput:
    return PropertyEPCInput(
        property_id=m.property_id,
        name=m.name,
        country=m.country,
        epc_rating=m.epc_rating,
        floor_area_m2=Decimal(str(m.floor_area_m2)),
        market_value=Decimal(str(m.market_value)),
        annual_rent=Decimal(str(m.annual_rent)),
        building_age=m.building_age,
        property_type=m.property_type,
        is_leased=m.is_leased,
    )


def _to_retrofit_input(m: PropertyRetrofitInputModel) -> PropertyRetrofitInput:
    return PropertyRetrofitInput(
        property_id=m.property_id,
        name=m.name,
        country=m.country,
        property_type=m.property_type,
        floor_area_m2=m.floor_area_m2,
        current_epc=m.current_epc,
        current_energy_intensity_kwh_m2=m.current_energy_intensity_kwh_m2,
        market_value=m.market_value,
        annual_rent=m.annual_rent,
        target_epc=m.target_epc,
        discount_rate=m.discount_rate,
        carbon_price_eur_t=m.carbon_price_eur_t,
        existing_measures=m.existing_measures,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _serialise_deadline(d) -> dict:
    return {
        "year": d.year,
        "minimum_epc": d.minimum_epc,
        "scope": d.scope,
        "is_compliant": d.is_compliant,
        "gap_steps": d.gap_steps,
        "years_remaining": d.years_remaining,
        "penalty_eur_m2": d.penalty_eur_m2,
        "annual_penalty_estimate": d.annual_penalty_estimate,
        "stranding_probability": d.stranding_probability,
    }


def _serialise_property_risk(r) -> dict:
    return {
        "property_id": r.property_id,
        "name": r.name,
        "country": r.country,
        "current_epc": r.current_epc,
        "composite_risk_score": r.composite_risk_score,
        "risk_band": r.risk_band,
        "deadlines": [_serialise_deadline(d) for d in r.deadlines],
        "first_non_compliant_year": r.first_non_compliant_year,
        "worst_gap_steps": r.worst_gap_steps,
        "total_annual_penalty_at_risk": r.total_annual_penalty_at_risk,
        "regulatory_certainty": r.regulatory_certainty,
    }


def _serialise_measure(m) -> dict:
    return {
        "measure_id": m.measure_id,
        "name": m.name,
        "category": m.category,
        "capex_total": m.capex_total,
        "capex_per_m2": m.capex_per_m2,
        "annual_energy_saving_kwh": m.annual_energy_saving_kwh,
        "annual_energy_cost_saving": m.annual_energy_cost_saving,
        "annual_carbon_saving_tco2": m.annual_carbon_saving_tco2,
        "annual_carbon_cost_saving": m.annual_carbon_cost_saving,
        "total_annual_saving": m.total_annual_saving,
        "simple_payback_years": m.simple_payback_years,
        "npv": m.npv,
        "irr": m.irr,
        "roi_pct": m.roi_pct,
        "epc_improvement_steps": m.epc_improvement_steps,
        "lifetime_years": m.lifetime_years,
    }


def _serialise_property_plan(p) -> dict:
    return {
        "property_id": p.property_id,
        "name": p.name,
        "current_epc": p.current_epc,
        "target_epc": p.target_epc,
        "projected_epc_after_retrofit": p.projected_epc_after_retrofit,
        "total_capex": p.total_capex,
        "total_annual_saving": p.total_annual_saving,
        "portfolio_payback_years": p.portfolio_payback_years,
        "aggregate_npv": p.aggregate_npv,
        "energy_reduction_pct": p.energy_reduction_pct,
        "carbon_reduction_pct": p.carbon_reduction_pct,
        "green_value_uplift_pct": p.green_value_uplift_pct,
        "green_value_uplift_eur": p.green_value_uplift_eur,
        "measures": [_serialise_measure(m) for m in p.measures],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/transition-risk")
def assess_transition_risk(req: TransitionRiskRequest):
    """Score properties by EPC rating against MEPS regulatory timelines."""
    engine = EPCTransitionEngine()
    inputs = [_to_epc_input(p) for p in req.properties]
    result = engine.assess_portfolio(inputs)
    return {
        "total_properties": result.total_properties,
        "compliant_now_count": result.compliant_now_count,
        "compliant_now_pct": result.compliant_now_pct,
        "at_risk_2030_count": result.at_risk_2030_count,
        "at_risk_2030_pct": result.at_risk_2030_pct,
        "at_risk_2033_count": result.at_risk_2033_count,
        "at_risk_2033_pct": result.at_risk_2033_pct,
        "total_annual_penalty_exposure": result.total_annual_penalty_exposure,
        "avg_composite_score": result.avg_composite_score,
        "risk_distribution": result.risk_distribution,
        "worst_properties": result.worst_properties,
        "gav_at_risk_2030": result.gav_at_risk_2030,
        "gav_at_risk_pct_2030": result.gav_at_risk_pct_2030,
        "property_results": [_serialise_property_risk(r) for r in result.property_results],
    }


@router.post("/retrofit-plan")
def generate_retrofit_plan(req: RetrofitPlanRequest):
    """Generate NPV/payback retrofit CapEx plan."""
    planner = RetrofitPlanner()
    inputs = [_to_retrofit_input(p) for p in req.properties]
    result = planner.plan_portfolio(inputs)
    return {
        "total_properties": result.total_properties,
        "total_capex_required": result.total_capex_required,
        "total_annual_savings": result.total_annual_savings,
        "portfolio_simple_payback": result.portfolio_simple_payback,
        "portfolio_aggregate_npv": result.portfolio_aggregate_npv,
        "avg_energy_reduction_pct": result.avg_energy_reduction_pct,
        "avg_carbon_reduction_pct": result.avg_carbon_reduction_pct,
        "total_green_value_uplift": result.total_green_value_uplift,
        "capex_by_category": result.capex_by_category,
        "top_roi_properties": result.top_roi_properties,
        "property_plans": [_serialise_property_plan(p) for p in result.property_plans],
    }


@router.get("/measure-catalogue")
def get_measure_catalogue():
    """Return available retrofit measures with cost/savings data."""
    return {
        "measures": [
            {
                "measure_id": m.measure_id,
                "name": m.name,
                "category": m.category,
                "capex_eur_m2": m.capex_eur_m2,
                "energy_saving_kwh_m2": m.energy_saving_kwh_m2,
                "carbon_saving_pct": m.carbon_saving_pct,
                "typical_lifetime_years": m.typical_lifetime_years,
                "epc_improvement_steps": m.epc_improvement_steps,
                "applicability": m.applicability,
            }
            for m in MEASURE_CATALOGUE
        ],
        "total_measures": len(MEASURE_CATALOGUE),
    }


@router.get("/meps-timelines")
def get_meps_timelines():
    """Return MEPS regulatory timelines by country."""
    return {
        "timelines": MEPS_TIMELINES,
        "countries": list(MEPS_TIMELINES.keys()),
    }


@router.get("/energy-prices")
def get_energy_prices():
    """Return energy prices and grid emission factors by country."""
    return {
        "energy_prices_eur_kwh": ENERGY_PRICES,
        "grid_emission_factors_kgco2_kwh": GRID_FACTORS,
    }
