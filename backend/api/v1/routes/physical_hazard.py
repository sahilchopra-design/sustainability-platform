"""
API Routes: Physical Climate Hazard Scoring
===========================================
IPCC AR6 WG2 + JRC Climate Hazard Atlas

POST /api/v1/physical-hazard/score-hazard       — Single hazard scoring
POST /api/v1/physical-hazard/composite-risk     — All-hazard composite score
POST /api/v1/physical-hazard/financial-impact   — Property damage / stranding estimate
POST /api/v1/physical-hazard/crrem-check        — CRREM pathway compliance
POST /api/v1/physical-hazard/full-assessment    — Complete physical hazard assessment
GET  /api/v1/physical-hazard/ref/hazard-profiles   — HAZARD_PROFILES
GET  /api/v1/physical-hazard/ref/country-hazard    — COUNTRY_BASE_HAZARD
GET  /api/v1/physical-hazard/ref/adaptation-measures — ADAPTATION_MEASURES
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.physical_hazard_engine import PhysicalHazardEngine

router = APIRouter(
    prefix="/api/v1/physical-hazard",
    tags=["Physical Climate Hazard — E41"],
)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ScoreHazardRequest(BaseModel):
    entity_id: str
    hazard_type: str = "flood"
    country_code: str = "DE"
    asset_type: str = "office_building"
    climate_scenario: str = "RCP4.5"
    time_horizon: str = "2050"


class CompositeRiskRequest(BaseModel):
    entity_id: str
    country_code: str = "DE"
    asset_type: str = "office_building"
    climate_scenario: str = "RCP4.5"
    time_horizon: str = "2050"
    hazard_scores: dict = Field(
        default={},
        description="Optional pre-computed hazard scores; auto-scored from country profile if empty",
    )


class FinancialImpactRequest(BaseModel):
    entity_id: str
    composite_score: float = Field(50.0, ge=0, le=100)
    asset_type: str = "office_building"
    asset_value_mn: float = Field(50.0, ge=0)


class CRREMCheckRequest(BaseModel):
    entity_id: str
    asset_type: str = "office_building"
    climate_scenario: str = "RCP4.5"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    asset_name: str
    asset_type: str = "office_building"
    country_code: str = "DE"
    climate_scenario: str = "RCP4.5"
    time_horizon: str = "2050"
    asset_value_mn: float = Field(50.0, ge=0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/score-hazard")
def score_hazard(req: ScoreHazardRequest):
    """Score a single physical hazard for an asset in a given country."""
    try:
        engine = PhysicalHazardEngine()
        return engine.score_hazard(
            entity_id=req.entity_id,
            hazard_type=req.hazard_type,
            country_code=req.country_code,
            asset_type=req.asset_type,
            climate_scenario=req.climate_scenario,
            time_horizon=req.time_horizon,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/composite-risk")
def composite_risk(req: CompositeRiskRequest):
    """Compute weighted composite hazard score across all seven hazards."""
    try:
        engine = PhysicalHazardEngine()
        scores = req.hazard_scores
        if not scores:
            # Auto-score each hazard from country profile
            from services.physical_hazard_engine import HAZARD_PROFILES
            for hazard in HAZARD_PROFILES:
                res = engine.score_hazard(
                    entity_id=req.entity_id,
                    hazard_type=hazard,
                    country_code=req.country_code,
                    asset_type=req.asset_type,
                    climate_scenario=req.climate_scenario,
                    time_horizon=req.time_horizon,
                )
                scores[hazard] = res["hazard_score"]
        return engine.compute_composite_risk(entity_id=req.entity_id, hazard_scores=scores)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/financial-impact")
def financial_impact(req: FinancialImpactRequest):
    """Estimate property damage, business interruption and adaptation CAPEX."""
    try:
        engine = PhysicalHazardEngine()
        return engine.estimate_financial_impact(
            entity_id=req.entity_id,
            composite_score=req.composite_score,
            asset_type=req.asset_type,
            asset_value_mn=req.asset_value_mn,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/crrem-check")
def crrem_check(req: CRREMCheckRequest):
    """Check CRREM pathway compliance and estimate stranding year."""
    try:
        engine = PhysicalHazardEngine()
        return engine.check_crrem_alignment(
            entity_id=req.entity_id,
            asset_type=req.asset_type,
            climate_scenario=req.climate_scenario,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Complete physical climate hazard assessment for an asset."""
    try:
        engine = PhysicalHazardEngine()
        return engine.full_assessment(
            entity_id=req.entity_id,
            asset_name=req.asset_name,
            asset_type=req.asset_type,
            country_code=req.country_code,
            climate_scenario=req.climate_scenario,
            time_horizon=req.time_horizon,
            asset_value_mn=req.asset_value_mn,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/hazard-profiles")
def ref_hazard_profiles():
    """Return all seven hazard profiles with intensity metrics and data sources."""
    return PhysicalHazardEngine.get_hazard_profiles()


@router.get("/ref/country-hazard")
def ref_country_hazard():
    """Return country-level base hazard scores."""
    return PhysicalHazardEngine.get_country_base_hazard()


@router.get("/ref/adaptation-measures")
def ref_adaptation_measures():
    """Return recommended adaptation measures per hazard type."""
    return PhysicalHazardEngine.get_adaptation_measures()
