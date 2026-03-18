"""
API Routes: TPT Transition Plan Disclosure Framework Engine
=============================================================
POST /api/v1/tpt-transition-plan/assess                    — Full TPT assessment
POST /api/v1/tpt-transition-plan/score-element             — Score a single TPT element
POST /api/v1/tpt-transition-plan/gap-analysis              — Generate gap analysis
GET  /api/v1/tpt-transition-plan/ref/elements              — TPT 6-element framework
GET  /api/v1/tpt-transition-plan/ref/entity-types          — Supported entity types
GET  /api/v1/tpt-transition-plan/ref/quality-tiers         — Quality tier definitions
GET  /api/v1/tpt-transition-plan/ref/cross-framework       — TCFD/IFRS S2/CSRD cross-reference
GET  /api/v1/tpt-transition-plan/ref/interim-targets-guidance — Interim milestone guidance
"""
from __future__ import annotations

import dataclasses
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.tpt_transition_plan_engine import get_engine, TPTAssessment

router = APIRouter(prefix="/api/v1/tpt-transition-plan", tags=["TPT Transition Plan"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class TPTAssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str = "corporate"
    plan_year: int = Field(2024, ge=2020, le=2030)
    net_zero_target_year: Optional[int] = Field(None, ge=2030, le=2070)
    elements_completed: Optional[list[str]] = None
    interim_targets: Optional[dict] = None
    financed_emissions_trajectory: Optional[list[dict]] = None
    capex_green_pct: float = Field(0.0, ge=0, le=100)


class ScoreElementRequest(BaseModel):
    entity_id: str
    element_id: str
    sub_elements_completed: Optional[list[str]] = None


class GapAnalysisRequest(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str = "corporate"
    plan_year: int = Field(2024, ge=2020, le=2030)
    net_zero_target_year: Optional[int] = None
    elements_completed: Optional[list[str]] = None
    interim_targets: Optional[dict] = None
    capex_green_pct: float = Field(0.0, ge=0, le=100)


# ---------------------------------------------------------------------------
# Assessment Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_tpt(req: TPTAssessRequest):
    """Full TPT Disclosure Framework 2023 assessment — all 6 elements, quality tier, cross-framework alignment."""
    try:
        engine = get_engine()
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            entity_type=req.entity_type,
            plan_year=req.plan_year,
            net_zero_target_year=req.net_zero_target_year,
            elements_completed=req.elements_completed,
            interim_targets=req.interim_targets,
            financed_emissions_trajectory=req.financed_emissions_trajectory,
            capex_green_pct=req.capex_green_pct,
        )
        return {"status": "ok", "result": dataclasses.asdict(result)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/score-element")
def score_element(req: ScoreElementRequest):
    """Score a single TPT element with sub-element completion granularity."""
    try:
        engine = get_engine()
        result = engine.score_element(
            entity_id=req.entity_id,
            element_id=req.element_id,
            sub_elements_completed=req.sub_elements_completed,
        )
        return {"status": "ok", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/gap-analysis")
def gap_analysis(req: GapAnalysisRequest):
    """Generate TPT gap analysis by running assessment and extracting element-level gaps."""
    try:
        engine = get_engine()
        assessment = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            entity_type=req.entity_type,
            plan_year=req.plan_year,
            net_zero_target_year=req.net_zero_target_year,
            elements_completed=req.elements_completed,
            interim_targets=req.interim_targets,
            capex_green_pct=req.capex_green_pct,
        )
        gaps = engine.generate_gap_analysis(req.entity_id, assessment)
        return {
            "status": "ok",
            "result": {
                "entity_id": req.entity_id,
                "overall_score": assessment.overall_score,
                "quality_tier": assessment.quality_tier,
                "gaps": gaps,
                "priority_actions": assessment.priority_actions,
                "tcfd_alignment_pct": assessment.tcfd_alignment_pct,
                "ifrs_s2_alignment_pct": assessment.ifrs_s2_alignment_pct,
                "csrd_esrs_e1_alignment_pct": assessment.csrd_esrs_e1_alignment_pct,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/elements")
def ref_elements():
    """TPT Disclosure Framework — all 6 elements with sub-elements, quality indicators, and references."""
    try:
        return {"status": "ok", "result": get_engine().ref_elements()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/entity-types")
def ref_entity_types():
    """Supported entity types with relevant TPT elements and regulatory triggers."""
    try:
        return {"status": "ok", "result": get_engine().ref_entity_types()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/quality-tiers")
def ref_quality_tiers():
    """TPT quality tiers — initial / developing / advanced / leading with score ranges."""
    try:
        return {"status": "ok", "result": get_engine().ref_quality_tiers()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """Cross-framework mapping: TCFD, IFRS S2, and CSRD ESRS E1 to TPT elements."""
    try:
        return {"status": "ok", "result": get_engine().ref_cross_framework()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/interim-targets-guidance")
def ref_interim_targets_guidance():
    """Interim milestone guidance for 2025, 2030, 2035, 2040, 2050 target years."""
    try:
        return {"status": "ok", "result": get_engine().ref_interim_targets_guidance()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
