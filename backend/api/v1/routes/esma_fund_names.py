"""
API Routes: ESMA Fund Names ESG Guidelines Engine (E16)
=======================================================
POST /api/v1/esma-fund-names/assess              — Full fund name compliance assessment
POST /api/v1/esma-fund-names/assess/batch        — Batch: multiple funds
POST /api/v1/esma-fund-names/detect-terms        — Detect ESG terms in a fund name
GET  /api/v1/esma-fund-names/ref/term-categories — ESG_TERM_CATEGORIES reference
GET  /api/v1/esma-fund-names/ref/pab-exclusions  — PAB_EXCLUSIONS reference
GET  /api/v1/esma-fund-names/ref/sfdr-requirements — SFDR_MINIMUM_REQUIREMENTS reference
GET  /api/v1/esma-fund-names/ref/cross-framework  — CROSS_FRAMEWORK reference
GET  /api/v1/esma-fund-names/ref/timeline        — ESMA_TIMELINE reference
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.esma_fund_names_engine import (
    ESMAFundNamesEngine,
    FundNameInput,
    ESG_TERM_CATEGORIES,
    PAB_EXCLUSIONS,
    SFDR_MINIMUM_REQUIREMENTS,
    CROSS_FRAMEWORK,
    ESMA_TIMELINE,
)

router = APIRouter(
    prefix="/api/v1/esma-fund-names",
    tags=["ESMA Fund Names ESG Guidelines — ESMA/2024/249"],
)

_ENGINE = ESMAFundNamesEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class FundNameInputModel(BaseModel):
    fund_id: str
    fund_name: str = Field(..., description="Full fund name as marketed to investors")
    sfdr_classification: str = Field("art_8", description="art_6 | art_8 | art_9")
    esg_investment_pct: float = Field(
        0.0, ge=0.0, le=100.0,
        description="% of fund assets meeting the ESG investment criteria"
    )
    has_pai_exclusions: bool = Field(
        False,
        description="Fund applies PAB exclusion screens (controversial weapons, UNGC, tobacco, fossil fuel, high GHG)"
    )
    has_dnsh_assessment: bool = Field(
        False,
        description="Fund conducts formal DNSH assessment for all investments"
    )
    tracks_paris_benchmark: bool = Field(
        False,
        description="Fund tracks an EU Paris-Aligned Benchmark (required for 'transition' terms)"
    )
    has_real_world_impact_evidence: bool = Field(
        False,
        description="Fund has documented real-world additionality and measurable impact (required for 'impact' terms)"
    )
    excluded_categories: List[str] = Field(
        default_factory=list,
        description="Categories explicitly excluded from the fund (e.g. 'fossil_fuel_exploration')"
    )
    fund_type: str = Field("UCITS", description="UCITS | AIF | ELTIFm | ELTIF")


class DetectTermsModel(BaseModel):
    fund_name: str = Field(..., description="Fund name to analyse for ESG terms")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Assess single fund name ESG compliance")
def assess_fund_name(body: FundNameInputModel) -> Dict[str, Any]:
    """
    Assess whether a fund name using ESG or sustainability-related terms
    meets ESMA/2024/249 Guidelines requirements.

    Returns term detection, threshold check, PAB exclusion compliance,
    DNSH/Paris benchmark checks, overall compliance score and actionable gaps.
    """
    inp = FundNameInput(
        fund_id=body.fund_id,
        fund_name=body.fund_name,
        sfdr_classification=body.sfdr_classification,
        esg_investment_pct=body.esg_investment_pct,
        has_pai_exclusions=body.has_pai_exclusions,
        has_dnsh_assessment=body.has_dnsh_assessment,
        tracks_paris_benchmark=body.tracks_paris_benchmark,
        has_real_world_impact_evidence=body.has_real_world_impact_evidence,
        excluded_categories=body.excluded_categories,
        fund_type=body.fund_type,
    )
    result = _ENGINE.assess_fund_name(inp)
    return result.dict()


@router.post("/assess/batch", summary="Batch assess multiple fund names")
def assess_batch(body: List[FundNameInputModel]) -> List[Dict[str, Any]]:
    """
    Assess a list of fund names in a single call. Returns one result
    per fund in the same order as the input list.
    """
    inputs = [
        FundNameInput(
            fund_id=b.fund_id,
            fund_name=b.fund_name,
            sfdr_classification=b.sfdr_classification,
            esg_investment_pct=b.esg_investment_pct,
            has_pai_exclusions=b.has_pai_exclusions,
            has_dnsh_assessment=b.has_dnsh_assessment,
            tracks_paris_benchmark=b.tracks_paris_benchmark,
            has_real_world_impact_evidence=b.has_real_world_impact_evidence,
            excluded_categories=b.excluded_categories,
            fund_type=b.fund_type,
        )
        for b in body
    ]
    return [r.dict() for r in _ENGINE.batch_assess(inputs)]


@router.post("/detect-terms", summary="Detect ESG/sustainability terms in fund name")
def detect_terms(body: DetectTermsModel) -> Dict[str, Any]:
    """
    Analyse a fund name string and identify which ESG term categories
    are triggered, the derived threshold requirements, and whether Paris
    Benchmark, DNSH, real-world impact, or PAI exclusions are required.
    """
    result = _ENGINE.detect_terms(body.fund_name)
    return {
        "fund_name": body.fund_name,
        "detected_terms": result.detected_terms,
        "term_categories": result.term_categories,
        "highest_requirement_category": result.highest_requirement_category,
        "required_threshold_pct": result.required_threshold_pct,
        "paris_benchmark_required": result.paris_benchmark_required,
        "real_world_impact_required": result.real_world_impact_required,
        "dnsh_required": result.dnsh_required,
        "pai_exclusions_required": result.pai_exclusions_required,
    }


@router.get("/ref/term-categories", summary="ESG term category definitions and thresholds")
def ref_term_categories() -> Dict[str, Any]:
    """Return ESG_TERM_CATEGORIES reference data — all 6 category groups with
    term lists, 80% threshold, and additional requirement flags."""
    return _ENGINE.get_term_categories()


@router.get("/ref/pab-exclusions", summary="Paris-Aligned Benchmark mandatory exclusions")
def ref_pab_exclusions() -> Dict[str, Any]:
    """Return PAB_EXCLUSIONS — 5 mandatory exclusion screens required for
    all ESG/sustainability-named funds per ESMA/2024/249 §28-30."""
    return _ENGINE.get_pab_exclusions()


@router.get("/ref/sfdr-requirements", summary="SFDR Art 8/9 minimum requirements")
def ref_sfdr_requirements() -> Dict[str, Any]:
    """Return SFDR_MINIMUM_REQUIREMENTS — minimum threshold and DNSH
    requirements for Art 8 and Art 9 classified funds."""
    return _ENGINE.get_sfdr_requirements()


@router.get("/ref/cross-framework", summary="Cross-framework mapping (SFDR, EU Taxonomy, MiFID, PRIIPs, PAB)")
def ref_cross_framework() -> Dict[str, Any]:
    """Return cross-framework linkage between ESMA fund names guidelines
    and SFDR, EU Taxonomy, MiFID II, PRIIPs, and PAB Regulation."""
    return _ENGINE.get_cross_framework()


@router.get("/ref/timeline", summary="ESMA/2024/249 regulatory implementation timeline")
def ref_timeline() -> List[Dict[str, str]]:
    """Return ESMA_TIMELINE — key dates from Final Report publication
    through application dates for new and existing funds."""
    return _ENGINE.get_timeline()
