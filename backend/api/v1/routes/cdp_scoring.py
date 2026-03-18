"""
API Routes: CDP Climate & Water Scoring
=========================================
POST /api/v1/cdp/assess-climate            — CDP Climate Change questionnaire assessment
POST /api/v1/cdp/assess-water              — CDP Water Security questionnaire assessment
POST /api/v1/cdp/compare-peers             — Peer comparison against activity group medians
GET  /api/v1/cdp/ref/climate-modules       — CDP Climate Change 15 modules
GET  /api/v1/cdp/ref/water-modules         — CDP Water Security 9 modules
GET  /api/v1/cdp/ref/scoring-methodology   — CDP 4-level scoring methodology
GET  /api/v1/cdp/ref/score-bands           — CDP letter grades (A to D-)
GET  /api/v1/cdp/ref/activity-groups       — CDP 12 activity group classifications
GET  /api/v1/cdp/ref/cross-framework       — CDP cross-framework mapping (TCFD/GRI/ISSB/SASB)
GET  /api/v1/cdp/ref/peer-benchmarks       — Activity group median benchmarks
GET  /api/v1/cdp/ref/module-catalog        — Full module catalog for UI
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.cdp_scoring_engine import CDPScoringEngine

router = APIRouter(prefix="/api/v1/cdp", tags=["CDP Climate & Water Scoring"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CDPClimateRequest(BaseModel):
    entity_name: str
    reporting_year: int = 2025
    activity_group: Optional[str] = None
    responses: Optional[dict] = None


class CDPWaterRequest(BaseModel):
    entity_name: str
    reporting_year: int = 2025
    responses: Optional[dict] = None


class CDPPeerComparisonRequest(BaseModel):
    entity_name: str
    activity_group: str
    entity_score_pct: float


# ---------------------------------------------------------------------------
# Assessment Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess-climate")
def assess_climate(req: CDPClimateRequest):
    """CDP Climate Change questionnaire assessment — 15 modules, 4-level scoring, letter grade."""
    engine = CDPScoringEngine()
    r = engine.assess_climate(
        entity_name=req.entity_name,
        reporting_year=req.reporting_year,
        activity_group=req.activity_group,
        responses=req.responses,
    )
    return r.__dict__


@router.post("/assess-water")
def assess_water(req: CDPWaterRequest):
    """CDP Water Security questionnaire assessment — 9 modules, water risk exposure."""
    engine = CDPScoringEngine()
    r = engine.assess_water(
        entity_name=req.entity_name,
        reporting_year=req.reporting_year,
        responses=req.responses,
    )
    return r.__dict__


@router.post("/compare-peers")
def compare_peers(req: CDPPeerComparisonRequest):
    """Peer comparison against CDP activity group median benchmarks."""
    engine = CDPScoringEngine()
    return engine.compare_to_peers(
        entity_name=req.entity_name,
        activity_group=req.activity_group,
        entity_score_pct=req.entity_score_pct,
    )


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/climate-modules")
def ref_climate_modules():
    """CDP Climate Change questionnaire — 15 modules (C0-C14)."""
    return {"climate_modules": CDPScoringEngine.get_climate_modules()}


@router.get("/ref/water-modules")
def ref_water_modules():
    """CDP Water Security questionnaire — 9 modules (W0-W8)."""
    return {"water_modules": CDPScoringEngine.get_water_modules()}


@router.get("/ref/scoring-methodology")
def ref_scoring_methodology():
    """CDP 4-level scoring methodology (Disclosure, Awareness, Management, Leadership)."""
    return {"scoring_methodology": CDPScoringEngine.get_scoring_methodology()}


@router.get("/ref/score-bands")
def ref_score_bands():
    """CDP letter grade bands (A through D-)."""
    return {"score_bands": CDPScoringEngine.get_score_bands()}


@router.get("/ref/activity-groups")
def ref_activity_groups():
    """CDP 12 activity group classifications."""
    return {"activity_groups": CDPScoringEngine.get_activity_groups()}


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """CDP cross-framework mapping to TCFD, GRI, ISSB S2, SASB."""
    return {"cross_framework_mapping": CDPScoringEngine.get_cross_framework_map()}


@router.get("/ref/peer-benchmarks")
def ref_peer_benchmarks():
    """Activity group median benchmarks for peer comparison."""
    return {"peer_benchmarks": CDPScoringEngine.get_peer_benchmarks()}


@router.get("/ref/module-catalog")
def ref_module_catalog():
    """Full module catalog (climate + water) for UI dropdowns."""
    return {"module_catalog": CDPScoringEngine.get_module_catalog()}
