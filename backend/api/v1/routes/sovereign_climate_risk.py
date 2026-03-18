"""
API Routes: Sovereign Climate Risk Engine
==========================================
POST /api/v1/sovereign-climate-risk/assess              — Single sovereign assessment
POST /api/v1/sovereign-climate-risk/portfolio            — Portfolio-level sovereign assessment
GET  /api/v1/sovereign-climate-risk/ref/profiles         — Sovereign climate risk profiles
GET  /api/v1/sovereign-climate-risk/ref/scenarios        — NGFS climate scenario definitions
GET  /api/v1/sovereign-climate-risk/ref/countries        — Country list with ratings & ND-GAIN
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.sovereign_climate_risk_engine import SovereignClimateRiskEngine

router = APIRouter(prefix="/api/v1/sovereign-climate-risk", tags=["Sovereign Climate Risk"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SovereignAssessRequest(BaseModel):
    country_iso2: str
    scenario: str = "current_policies"
    horizon: str = "2030"
    physical_risk_override: Optional[float] = None
    transition_readiness_override: Optional[float] = None


class HoldingItem(BaseModel):
    country_iso2: str
    exposure_usd: float = Field(0, ge=0)


class PortfolioAssessRequest(BaseModel):
    portfolio_name: str = "Sovereign Portfolio"
    holdings: list[HoldingItem] = []
    scenario: str = "current_policies"
    horizon: str = "2030"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_sovereign(req: SovereignAssessRequest):
    """Climate-adjusted sovereign risk assessment for one country."""
    engine = SovereignClimateRiskEngine()
    r = engine.assess_sovereign(
        country_iso2=req.country_iso2,
        scenario=req.scenario,
        horizon=req.horizon,
        physical_risk_override=req.physical_risk_override,
        transition_readiness_override=req.transition_readiness_override,
    )
    return {
        "country_iso2": r.country_iso2,
        "country_name": r.country_name,
        "assessment_date": r.assessment_date,
        "scenario": r.scenario,
        "horizon": r.horizon,
        "physical_risk_score": r.physical_risk_score,
        "transition_risk_score": r.transition_risk_score,
        "fiscal_vulnerability_score": r.fiscal_vulnerability_score,
        "adaptation_readiness_score": r.adaptation_readiness_score,
        "composite_climate_risk_score": r.composite_climate_risk_score,
        "baseline_rating": r.baseline_rating,
        "climate_adjusted_rating": r.climate_adjusted_rating,
        "notch_adjustment": r.notch_adjustment,
        "climate_spread_delta_bps": r.climate_spread_delta_bps,
        "risk_decomposition": r.risk_decomposition,
        "nd_gain_score": r.nd_gain_score,
        "ndc_ambition_score": r.ndc_ambition_score,
        "notes": r.notes,
    }


@router.post("/portfolio")
def assess_portfolio(req: PortfolioAssessRequest):
    """Portfolio-level sovereign climate risk assessment."""
    engine = SovereignClimateRiskEngine()
    holdings = [{"country_iso2": h.country_iso2, "exposure_usd": h.exposure_usd}
                for h in req.holdings]
    r = engine.assess_portfolio(
        portfolio_name=req.portfolio_name,
        holdings=holdings,
        scenario=req.scenario,
        horizon=req.horizon,
    )
    return {
        "portfolio_name": r.portfolio_name,
        "assessment_date": r.assessment_date,
        "scenario": r.scenario,
        "horizon": r.horizon,
        "total_exposure_usd": r.total_exposure_usd,
        "country_count": r.country_count,
        "weighted_avg_climate_risk": r.weighted_avg_climate_risk,
        "weighted_avg_notch_adjustment": r.weighted_avg_notch_adjustment,
        "weighted_avg_spread_delta_bps": r.weighted_avg_spread_delta_bps,
        "total_climate_var_usd": r.total_climate_var_usd,
        "country_results": r.country_results,
        "risk_tier_distribution": r.risk_tier_distribution,
        "region_breakdown": r.region_breakdown,
    }


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/profiles")
def ref_profiles():
    """Sovereign climate risk profiles (60 countries)."""
    return {"sovereign_profiles": SovereignClimateRiskEngine.get_sovereign_profiles()}


@router.get("/ref/scenarios")
def ref_scenarios():
    """NGFS-based climate scenario definitions."""
    return {"climate_scenarios": SovereignClimateRiskEngine.get_climate_scenarios()}


@router.get("/ref/countries")
def ref_countries():
    """Country list with credit ratings and ND-GAIN scores."""
    return {"countries": SovereignClimateRiskEngine.get_country_list()}
