"""
API Routes: TCFD Metrics & Targets Disclosure Engine (E13)
===========================================================
POST /api/v1/tcfd-metrics/assess               — Full 11-recommendation TCFD assessment
POST /api/v1/tcfd-metrics/assess/pillar        — Single-pillar assessment
POST /api/v1/tcfd-metrics/assess/batch         — Batch: multiple entities
GET  /api/v1/tcfd-metrics/ref/recommendations  — 11 TCFD recommendation definitions
GET  /api/v1/tcfd-metrics/ref/pillars          — 4 TCFD pillar definitions
GET  /api/v1/tcfd-metrics/ref/sector-supplements — 5 sector supplement definitions
GET  /api/v1/tcfd-metrics/ref/maturity-levels  — 5 maturity level definitions
GET  /api/v1/tcfd-metrics/ref/cross-framework  — TCFD ↔ CSRD / ISSB / CDP / GRI / SEC
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.tcfd_metrics_engine import (
    TCFDMetricsEngine,
    TCFD_RECOMMENDATIONS,
    TCFD_PILLARS,
    SECTOR_SUPPLEMENTS,
    TCFD_MATURITY_LEVELS,
    TCFD_CROSS_FRAMEWORK,
)

router = APIRouter(
    prefix="/api/v1/tcfd-metrics",
    tags=["TCFD — Metrics & Targets Disclosure"],
)

_ENGINE = TCFDMetricsEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class RecommendationInputModel(BaseModel):
    rec_id: str = Field(..., description="G1|G2|S1|S2|S3|RM1|RM2|RM3|MT1|MT2|MT3")
    disclosed: bool = Field(False, description="Whether the recommendation has been disclosed")
    disclosure_quality: str = Field(
        "none",
        description="none | partial | full",
    )
    elements_covered: List[str] = Field(
        default_factory=list,
        description="List of disclosure elements covered (must match TCFD_RECOMMENDATIONS elements)",
    )


class TCFDAssessmentRequest(BaseModel):
    entity_id: str
    entity_name: str
    sector: str = Field(
        "general",
        description=(
            "general | financial_institutions | energy | transport | buildings | agriculture"
        ),
    )
    disclosure_year: int = Field(2025, description="Reporting year of the disclosure")
    recommendations: Dict[str, RecommendationInputModel] = Field(
        default_factory=dict,
        description=(
            "Map of rec_id → RecommendationInputModel. "
            "Omitted recommendations default to not disclosed."
        ),
    )


class PillarAssessmentRequest(BaseModel):
    pillar_id: str = Field(
        ...,
        description="governance | strategy | risk_management | metrics_targets",
    )
    entity_id: str
    entity_name: str
    recommendations: Dict[str, RecommendationInputModel] = Field(
        default_factory=dict,
        description="Map of rec_id → RecommendationInputModel for the pillar's recommendations",
    )


class BatchAssessmentItem(BaseModel):
    entity_id: str
    entity_name: str
    sector: str = "general"
    disclosure_year: int = 2025
    recommendations: Dict[str, RecommendationInputModel] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_rec_inputs(
    recommendations: Dict[str, RecommendationInputModel],
) -> Dict[str, Dict[str, Any]]:
    return {
        rec_id: {
            "disclosed": v.disclosed,
            "disclosure_quality": v.disclosure_quality,
            "elements_covered": v.elements_covered,
        }
        for rec_id, v in recommendations.items()
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Full 11-recommendation TCFD assessment")
def assess(request: TCFDAssessmentRequest) -> Dict[str, Any]:
    """
    Run a full TCFD assessment across all 11 recommendations and 4 pillars.
    Returns pillar scores, overall score, maturity level, blocking gaps, and priority actions.
    """
    rec_inputs = _build_rec_inputs(request.recommendations)
    result = _ENGINE.assess(
        entity_id=request.entity_id,
        entity_name=request.entity_name,
        sector=request.sector,
        disclosure_year=request.disclosure_year,
        recommendation_inputs=rec_inputs,
    )
    return result.to_dict()


@router.post("/assess/pillar", summary="Single TCFD pillar assessment")
def assess_pillar(request: PillarAssessmentRequest) -> Dict[str, Any]:
    """
    Run a TCFD assessment for a single pillar (Governance / Strategy /
    Risk Management / Metrics & Targets).
    """
    rec_inputs = _build_rec_inputs(request.recommendations)
    result = _ENGINE.assess_pillar(
        pillar_id=request.pillar_id,
        entity_id=request.entity_id,
        entity_name=request.entity_name,
        rec_inputs=rec_inputs,
    )
    return result.to_dict()


@router.post("/assess/batch", summary="Batch TCFD assessments for multiple entities")
def assess_batch(requests: List[BatchAssessmentItem]) -> List[Dict[str, Any]]:
    """
    Run full TCFD assessments for multiple entities in a single request.
    """
    results = []
    for item in requests:
        rec_inputs = _build_rec_inputs(item.recommendations)
        result = _ENGINE.assess(
            entity_id=item.entity_id,
            entity_name=item.entity_name,
            sector=item.sector,
            disclosure_year=item.disclosure_year,
            recommendation_inputs=rec_inputs,
        )
        results.append(result.to_dict())
    return results


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/recommendations",
    summary="11 TCFD recommendation definitions with disclosure elements",
)
def ref_recommendations() -> Dict[str, Any]:
    return _ENGINE.get_recommendations()


@router.get(
    "/ref/pillars",
    summary="4 TCFD pillar definitions",
)
def ref_pillars() -> Dict[str, Any]:
    return _ENGINE.get_pillars()


@router.get(
    "/ref/sector-supplements",
    summary="TCFD 2021 Annex — sector supplement additional metrics",
)
def ref_sector_supplements() -> Dict[str, Any]:
    return _ENGINE.get_sector_supplements()


@router.get(
    "/ref/maturity-levels",
    summary="TCFD maturity framework — 5 levels (Initial → Leading)",
)
def ref_maturity_levels() -> Dict[str, Any]:
    return _ENGINE.get_maturity_levels()


@router.get(
    "/ref/cross-framework",
    summary="TCFD ↔ CSRD ESRS E1 / ISSB S2 / CDP / GRI 305 / SEC Reg S-K cross-framework mapping",
)
def ref_cross_framework() -> Dict[str, str]:
    return _ENGINE.get_cross_framework()
