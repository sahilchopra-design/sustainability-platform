"""
Renewable Project Finance + PPA Risk API
==========================================
Endpoints for wind/solar yield assessment, LCOE, project finance,
and PPA risk scoring.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.renewable_project_engine import (
    RenewableProjectEngine,
    TURBINE_CLASSES,
    WIND_RESOURCE_REGIONS,
    SOLAR_GHI_DATA,
    SOLAR_DEFAULTS,
)
from services.ppa_risk_scorer import (
    PPARiskScorer,
    CREDIT_SCORES,
    PRICE_STRUCTURE_SCORES,
    TENOR_RISK,
    CURTAILMENT_RISK,
    REGULATORY_RISK,
    PPA_RISK_WEIGHTS,
)

router = APIRouter(prefix="/api/v1/renewable-ppa", tags=["Renewable & PPA"])

_engine = RenewableProjectEngine()
_ppa = PPARiskScorer()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class WindYieldRequest(BaseModel):
    turbine_class: str = "onshore_2mw"
    region: str = "northern_europe_onshore"
    num_turbines: int = Field(10, ge=1, le=500)
    wake_loss_pct: float = Field(8.0, ge=0, le=30)
    availability_pct: float = Field(97.0, ge=50, le=100)


class SolarYieldRequest(BaseModel):
    country: str = "DE"
    capacity_kwp: float = Field(1000, ge=1)
    performance_ratio: float = Field(0.0, ge=0, le=1)
    degradation_pct_yr: float = Field(0.0, ge=0, le=5)


class LCOERequest(BaseModel):
    technology: str = "wind"
    total_capex_eur: float = Field(ge=0)
    annual_opex_eur: float = Field(ge=0)
    annual_generation_mwh: float = Field(gt=0)
    wacc_pct: float = Field(6.0, ge=0, le=25)
    lifetime_years: int = Field(25, ge=1, le=50)
    degradation_pct_yr: float = Field(0.0, ge=0, le=5)


class ProjectAssessRequest(BaseModel):
    project_name: str
    technology: str  # "wind" | "solar"
    # Wind
    turbine_class: str = "onshore_2mw"
    region: str = "northern_europe_onshore"
    num_turbines: int = Field(10, ge=1, le=500)
    # Solar
    country: str = "DE"
    capacity_kwp: float = Field(0, ge=0)
    # Common
    ppa_price_eur_mwh: float = Field(60.0, ge=0)
    carbon_price_eur_tonne: float = Field(80.0, ge=0)
    grid_ef_tco2_mwh: float = Field(0.4, ge=0)
    wacc_pct: float = Field(6.0, ge=0, le=25)
    capex_override_eur: float = Field(0, ge=0)
    opex_override_eur_yr: float = Field(0, ge=0)


class PPARiskRequest(BaseModel):
    ppa_id: str
    project_name: str
    offtaker_name: str
    offtaker_credit_rating: str = "unrated"
    price_structure: str = "fixed"
    ppa_price_eur_mwh: float = Field(60.0, ge=0)
    tenor_years: float = Field(10.0, ge=0)
    curtailment_risk: str = "low"
    regulatory_risk: str = "stable"
    volume_hedged_pct: float = Field(100.0, ge=0, le=100)
    merchant_exposure_pct: float = Field(0.0, ge=0, le=100)
    subsidy_dependence_pct: float = Field(0.0, ge=0, le=100)


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _serialise_wind(r) -> dict:
    return {
        "turbine_class": r.turbine_class,
        "turbine_name": r.turbine_name,
        "region": r.region,
        "capacity_mw": r.capacity_mw,
        "num_turbines": r.num_turbines,
        "total_capacity_mw": r.total_capacity_mw,
        "weibull_k": r.weibull_k,
        "weibull_lambda": r.weibull_lambda,
        "mean_wind_speed_ms": r.mean_wind_speed_ms,
        "capacity_factor_pct": r.capacity_factor_pct,
        "p50_generation_mwh": r.p50_generation_mwh,
        "p75_generation_mwh": r.p75_generation_mwh,
        "p90_generation_mwh": r.p90_generation_mwh,
        "equivalent_full_load_hours": r.equivalent_full_load_hours,
        "wake_loss_pct": r.wake_loss_pct,
        "availability_pct": r.availability_pct,
    }


def _serialise_solar(r) -> dict:
    return {
        "country": r.country,
        "country_label": r.country_label,
        "capacity_kwp": r.capacity_kwp,
        "ghi_kwh_m2_yr": r.ghi_kwh_m2_yr,
        "performance_ratio": r.performance_ratio,
        "degradation_pct_yr": r.degradation_pct_yr,
        "p50_generation_mwh_yr1": r.p50_generation_mwh_yr1,
        "p75_generation_mwh_yr1": r.p75_generation_mwh_yr1,
        "p90_generation_mwh_yr1": r.p90_generation_mwh_yr1,
        "p50_lifetime_avg_mwh": r.p50_lifetime_avg_mwh,
        "capacity_factor_pct": r.capacity_factor_pct,
        "specific_yield_kwh_kwp": r.specific_yield_kwh_kwp,
    }


def _serialise_lcoe(r) -> dict:
    return {
        "technology": r.technology,
        "total_capex_eur": r.total_capex_eur,
        "annual_opex_eur": r.annual_opex_eur,
        "annual_generation_mwh": r.annual_generation_mwh,
        "wacc_pct": r.wacc_pct,
        "lifetime_years": r.lifetime_years,
        "crf": r.crf,
        "lcoe_eur_mwh": r.lcoe_eur_mwh,
        "lcoe_with_degradation_eur_mwh": r.lcoe_with_degradation_eur_mwh,
    }


def _serialise_project(r) -> dict:
    return {
        "project_name": r.project_name,
        "technology": r.technology,
        "yield_result": r.yield_result,
        "lcoe": _serialise_lcoe(r.lcoe),
        "irr_pct": r.irr_pct,
        "irr_with_carbon_pct": r.irr_with_carbon_pct,
        "npv_eur": r.npv_eur,
        "npv_with_carbon_eur": r.npv_with_carbon_eur,
        "payback_years": r.payback_years,
        "total_capex_eur": r.total_capex_eur,
        "annual_revenue_eur": r.annual_revenue_eur,
        "annual_opex_eur": r.annual_opex_eur,
        "carbon_revenue_eur_yr": r.carbon_revenue_eur_yr,
        "co2_avoided_tonnes_yr": r.co2_avoided_tonnes_yr,
        "lifetime_co2_avoided_tonnes": r.lifetime_co2_avoided_tonnes,
    }


def _serialise_ppa(r) -> dict:
    return {
        "ppa_id": r.ppa_id,
        "project_name": r.project_name,
        "offtaker_name": r.offtaker_name,
        "dimension_scores": [
            {
                "dimension": d.dimension,
                "label": d.label,
                "raw_score": d.raw_score,
                "weight": d.weight,
                "weighted_score": d.weighted_score,
                "risk_level": d.risk_level,
            }
            for d in r.dimension_scores
        ],
        "composite_score": r.composite_score,
        "risk_band": r.risk_band,
        "risk_factors": r.risk_factors,
        "mitigation_suggestions": r.mitigation_suggestions,
        "bankability_rating": r.bankability_rating,
    }


# ---------------------------------------------------------------------------
# Endpoints — Renewable Project Finance
# ---------------------------------------------------------------------------

@router.post("/wind-yield", summary="Wind energy yield (P50/P75/P90)")
def wind_yield(req: WindYieldRequest):
    res = _engine.wind_yield(
        turbine_class=req.turbine_class,
        region=req.region,
        num_turbines=req.num_turbines,
        wake_loss_pct=req.wake_loss_pct,
        availability_pct=req.availability_pct,
    )
    return _serialise_wind(res)


@router.post("/solar-yield", summary="Solar energy yield (P50/P75/P90)")
def solar_yield(req: SolarYieldRequest):
    res = _engine.solar_yield(
        country=req.country,
        capacity_kwp=req.capacity_kwp,
        performance_ratio=req.performance_ratio,
        degradation_pct_yr=req.degradation_pct_yr,
    )
    return _serialise_solar(res)


@router.post("/lcoe", summary="Levelised Cost of Energy")
def lcoe(req: LCOERequest):
    res = _engine.lcoe(
        technology=req.technology,
        total_capex_eur=req.total_capex_eur,
        annual_opex_eur=req.annual_opex_eur,
        annual_generation_mwh=req.annual_generation_mwh,
        wacc_pct=req.wacc_pct,
        lifetime_years=req.lifetime_years,
        degradation_pct_yr=req.degradation_pct_yr,
    )
    return _serialise_lcoe(res)


@router.post("/project-assess", summary="Full project finance (IRR/NPV/LCOE)")
def project_assess(req: ProjectAssessRequest):
    res = _engine.assess_project(
        project_name=req.project_name,
        technology=req.technology,
        turbine_class=req.turbine_class,
        region=req.region,
        num_turbines=req.num_turbines,
        country=req.country,
        capacity_kwp=req.capacity_kwp,
        ppa_price_eur_mwh=req.ppa_price_eur_mwh,
        carbon_price_eur_tonne=req.carbon_price_eur_tonne,
        grid_ef_tco2_mwh=req.grid_ef_tco2_mwh,
        wacc_pct=req.wacc_pct,
        capex_override_eur=req.capex_override_eur,
        opex_override_eur_yr=req.opex_override_eur_yr,
    )
    return _serialise_project(res)


# ---------------------------------------------------------------------------
# Endpoints — PPA Risk Scoring
# ---------------------------------------------------------------------------

@router.post("/ppa-risk", summary="PPA risk score (5 dimensions + bankability)")
def ppa_risk(req: PPARiskRequest):
    from services.ppa_risk_scorer import PPAInput

    inp = PPAInput(
        ppa_id=req.ppa_id,
        project_name=req.project_name,
        offtaker_name=req.offtaker_name,
        offtaker_credit_rating=req.offtaker_credit_rating,
        price_structure=req.price_structure,
        ppa_price_eur_mwh=req.ppa_price_eur_mwh,
        tenor_years=req.tenor_years,
        curtailment_risk=req.curtailment_risk,
        regulatory_risk=req.regulatory_risk,
        volume_hedged_pct=req.volume_hedged_pct,
        merchant_exposure_pct=req.merchant_exposure_pct,
        subsidy_dependence_pct=req.subsidy_dependence_pct,
    )
    res = _ppa.score_ppa(inp)
    return _serialise_ppa(res)


# ---------------------------------------------------------------------------
# Endpoints — Reference Data
# ---------------------------------------------------------------------------

@router.get("/ref/turbine-classes", summary="Available turbine classes")
def ref_turbine_classes():
    return _engine.get_turbine_classes()


@router.get("/ref/wind-regions", summary="Wind resource regions (Weibull params)")
def ref_wind_regions():
    return _engine.get_wind_regions()


@router.get("/ref/solar-ghi", summary="Solar GHI data by country")
def ref_solar_ghi():
    return _engine.get_solar_ghi_data()


@router.get("/ref/solar-defaults", summary="Solar system default parameters")
def ref_solar_defaults():
    return SOLAR_DEFAULTS


@router.get("/ref/credit-ratings", summary="PPA counterparty credit scores")
def ref_credit_ratings():
    return _ppa.get_credit_ratings()


@router.get("/ref/price-structures", summary="PPA price structure scores")
def ref_price_structures():
    return _ppa.get_price_structures()


@router.get("/ref/ppa-risk-weights", summary="PPA risk dimension weights")
def ref_ppa_risk_weights():
    return PPA_RISK_WEIGHTS


@router.get("/ref/curtailment-risk", summary="Curtailment risk levels")
def ref_curtailment_risk():
    return CURTAILMENT_RISK


@router.get("/ref/regulatory-risk", summary="Regulatory risk levels")
def ref_regulatory_risk():
    return REGULATORY_RISK
