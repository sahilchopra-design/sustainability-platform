"""
API Routes: CSRD Double Materiality Assessment Engine (E102)
============================================================
POST /api/v1/double-materiality/assess              — Full double materiality assessment
POST /api/v1/double-materiality/identify-iros       — IRO identification for a single ESRS topic
POST /api/v1/double-materiality/materiality-matrix  — Generate 2D materiality matrix data
POST /api/v1/double-materiality/check-omissions     — Validate ESRS omission justifications
GET  /api/v1/double-materiality/ref/esrs-topics     — All 10 ESRS topic/sub-topic metadata
GET  /api/v1/double-materiality/ref/nace-materiality — NACE sector x ESRS topic materiality triggers
GET  /api/v1/double-materiality/ref/iro-types       — IRO type definitions
GET  /api/v1/double-materiality/ref/csrd-timeline   — CSRD wave applicability timeline
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.double_materiality_engine import (
    DoubleMaterialityEngine,
    DoubleMaterialityRequest,
    IROIdentificationRequest,
    MaterialityMatrixRequest,
    OmissionCheckRequest,
    CompletenessRequest,
    TopicAssessment,
    IROAssessment,
    ESRS_TOPICS,
    NACE_MATERIALITY_MATRIX,
    IRO_TYPE_DEFINITIONS,
    CSRD_WAVE_TIMELINE,
    STAKEHOLDER_GROUPS,
    ASSURANCE_CRITERIA,
    OMISSION_CRITERIA,
)

router = APIRouter(prefix="/api/v1/double-materiality", tags=["Double Materiality (E102)"])

# ---------------------------------------------------------------------------
# Engine singleton
# ---------------------------------------------------------------------------

_engine: Optional[DoubleMaterialityEngine] = None


def _get_engine() -> DoubleMaterialityEngine:
    global _engine
    if _engine is None:
        _engine = DoubleMaterialityEngine()
    return _engine


# ---------------------------------------------------------------------------
# POST /assess
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Full ESRS 1 double materiality assessment")
def assess_double_materiality(req: DoubleMaterialityRequest) -> Dict[str, Any]:
    """
    Run the full ESRS 1 double materiality assessment for all 10 ESRS topics.

    - Applies company-provided topic assessments where available
    - Falls back to NACE sector materiality baseline for unassessed topics
    - Returns material topics, IRO count, completeness score, assurance readiness
    - Supports CSRD Waves 1-4 with first-year reporting relief flags
    """
    engine = _get_engine()
    return engine.conduct_double_materiality(
        entity_name=req.entity_name,
        nace_sector=req.nace_sector,
        employee_count=req.employee_count,
        reporting_year=req.reporting_year,
        topic_assessments=req.topic_assessments,
        csrd_wave=req.csrd_wave,
    )


# ---------------------------------------------------------------------------
# POST /identify-iros
# ---------------------------------------------------------------------------

@router.post("/identify-iros", summary="IRO identification for a single ESRS topic")
def identify_iros(req: IROIdentificationRequest) -> Dict[str, Any]:
    """
    Structured Impact, Risk and Opportunity (IRO) assessment for a single ESRS topic.

    Scores each IRO on:
    - Impact materiality: impact_scale x scope x irremediability + likelihood weighting
    - Financial materiality: likelihood x magnitude normalised 0-1
    - Applies IRO-type materiality weights (actual vs potential, positive vs negative)
    - Returns quadrant classification, priority tier, and reporting obligation
    """
    engine = _get_engine()
    return engine.identify_iros(
        entity_name=req.entity_name,
        topic=req.topic,
        iro_assessments=req.iro_assessments,
    )


# ---------------------------------------------------------------------------
# POST /materiality-matrix
# ---------------------------------------------------------------------------

@router.post("/materiality-matrix", summary="Generate 2D ESRS materiality matrix")
def generate_materiality_matrix(req: MaterialityMatrixRequest) -> Dict[str, Any]:
    """
    Generate 2D materiality matrix plot data.

    - X axis: financial materiality (0-1)
    - Y axis: impact materiality (0-1)
    - Threshold line at 0.40 (configurable per ESRS 1 para 64)
    - Quadrant classification: Double Material / Impact Only / Financial Only / Not Material
    - Returns all plot points sorted by combined score descending
    """
    engine = _get_engine()
    return engine.generate_materiality_matrix(
        entity_name=req.entity_name,
        topic_scores=req.topic_scores,
    )


# ---------------------------------------------------------------------------
# POST /check-omissions
# ---------------------------------------------------------------------------

@router.post("/check-omissions", summary="Validate ESRS omission justifications")
def check_omissions(req: OmissionCheckRequest) -> Dict[str, Any]:
    """
    Validate omission justifications against ESRS 1 paras 29-35.

    Validates each non-reported topic against:
    - not_applicable (ESRS 1 para 29): no relevant activities
    - immaterial (ESRS 1 para 31): below double materiality threshold
    - proprietary (ESRS 1 para 34): commercially sensitive — cannot apply to mandatory DPs
    - third_party_limitation (ESRS 1 para 35): data not obtainable despite reasonable efforts

    Returns accepted/rejected status with specific issues and warnings per topic.
    """
    engine = _get_engine()
    return engine.check_esrs_omissions(
        entity_name=req.entity_name,
        nace_sector=req.nace_sector,
        topics_not_reported=req.topics_not_reported,
    )


# ---------------------------------------------------------------------------
# POST /completeness
# ---------------------------------------------------------------------------

@router.post("/completeness", summary="Calculate mandatory DP completeness score")
def calculate_completeness(req: CompletenessRequest) -> Dict[str, Any]:
    """
    Calculate completeness of mandatory ESRS data point coverage.

    Returns:
    - DP coverage percentage
    - Topic coverage percentage
    - Assurance readiness tier (not_ready / approaching_limited / limited_assurance_ready / reasonable_assurance_ready)
    - Gap topics not reported
    """
    engine = _get_engine()
    return engine.calculate_completeness_score(
        entity_name=req.entity_name,
        topics_reported=req.topics_reported,
        dps_reported=req.dps_reported,
        dps_mandatory_for_sector=req.dps_mandatory_for_sector,
    )


# ---------------------------------------------------------------------------
# GET /ref/esrs-topics
# ---------------------------------------------------------------------------

@router.get("/ref/esrs-topics", summary="All 10 ESRS topic/sub-topic metadata")
def ref_esrs_topics() -> Dict[str, Any]:
    """
    Full ESRS topic and sub-topic reference data including:
    - DP reference codes (ESRS Appendix B)
    - IG3 technical note
    - Mandatory vs voluntary flag
    - Sector applicability (NACE sections)
    - Typical IRO types
    - Impact and financial materiality thresholds (1-5 scale)
    """
    engine = _get_engine()
    return engine.get_esrs_topic_metadata()


# ---------------------------------------------------------------------------
# GET /ref/nace-materiality
# ---------------------------------------------------------------------------

@router.get("/ref/nace-materiality", summary="NACE sector x ESRS topic materiality triggers")
def ref_nace_materiality() -> Dict[str, Any]:
    """
    Pre-set NACE sector x ESRS topic materiality probability matrix.

    Each NACE section/subsection is mapped to high/medium/low/na materiality signals
    for each of the 10 ESRS topics. Used as baseline when company has not provided
    an explicit assessment for a topic.
    """
    entries: List[Dict] = []
    for nace, topics in NACE_MATERIALITY_MATRIX.items():
        entries.append({"nace_code": nace, "topic_signals": topics})
    return {
        "nace_materiality_matrix": entries,
        "total_nace_codes": len(NACE_MATERIALITY_MATRIX),
        "signal_definitions": {
            "high":   "High materiality probability — typically mandatory disclosure expected",
            "medium": "Medium materiality — sector-dependent; assessment recommended",
            "low":    "Low materiality — unlikely material; brief justification sufficient",
            "na":     "Not applicable — topic area does not apply to this sector",
        },
    }


# ---------------------------------------------------------------------------
# GET /ref/iro-types
# ---------------------------------------------------------------------------

@router.get("/ref/iro-types", summary="IRO type definitions and reporting obligations")
def ref_iro_types() -> Dict[str, Any]:
    """
    IRO (Impact, Risk and Opportunity) type definitions per ESRS 1.

    Includes:
    - ESRS 1 article reference
    - Impact and financial materiality weighting
    - Reporting obligation per type
    """
    return {
        "iro_types": [
            {"iro_type": k, **v}
            for k, v in IRO_TYPE_DEFINITIONS.items()
        ],
        "total_iro_types": len(IRO_TYPE_DEFINITIONS),
        "esrs_ref": "ESRS 1 AR 3 (impacts) + AR 11-12 (financial)",
    }


# ---------------------------------------------------------------------------
# GET /ref/csrd-timeline
# ---------------------------------------------------------------------------

@router.get("/ref/csrd-timeline", summary="CSRD wave applicability timeline")
def ref_csrd_timeline() -> Dict[str, Any]:
    """
    CSRD wave applicability timeline per CSRD Art 5.

    Wave 1: Large PIEs >500 employees — FY2024
    Wave 2: Large non-PIE undertakings — FY2025
    Wave 3: Listed SMEs — FY2026
    Wave 4: Non-EU undertakings with EU nexus >EUR150m — FY2028
    """
    return {
        "csrd_waves": CSRD_WAVE_TIMELINE,
        "total_waves": len(CSRD_WAVE_TIMELINE),
        "directive": "CSRD Directive (EU) 2022/2464",
        "esrs_set": "ESRS Set 1 — Delegated Regulation (EU) 2023/2772",
        "assurance": {
            "wave_1_2": "Limited assurance required from first reporting year",
            "future":   "Reasonable assurance — timeline subject to EC review",
        },
    }


# ---------------------------------------------------------------------------
# GET /ref/stakeholder-groups
# ---------------------------------------------------------------------------

@router.get("/ref/stakeholder-groups", summary="ESRS stakeholder group definitions")
def ref_stakeholder_groups() -> Dict[str, Any]:
    """Six ESRS stakeholder groups with engagement methods and ESRS references."""
    return {
        "stakeholder_groups": STAKEHOLDER_GROUPS,
        "total_groups": len(STAKEHOLDER_GROUPS),
        "esrs_ref": "ESRS 1 paras 20-25",
    }


# ---------------------------------------------------------------------------
# GET /ref/assurance-criteria
# ---------------------------------------------------------------------------

@router.get("/ref/assurance-criteria", summary="Assurance readiness criteria")
def ref_assurance_criteria() -> Dict[str, Any]:
    """Five assurance readiness criteria with limited/reasonable assurance thresholds."""
    return {
        "assurance_criteria": ASSURANCE_CRITERIA,
        "limited_assurance_overall_threshold_pct": 60,
        "reasonable_assurance_overall_threshold_pct": 85,
        "standards": ["ISAE 3000 (Revised)", "ISSA 5000", "CSRD Art 26a"],
    }


# ---------------------------------------------------------------------------
# GET /ref/omission-criteria
# ---------------------------------------------------------------------------

@router.get("/ref/omission-criteria", summary="ESRS omission criteria reference")
def ref_omission_criteria() -> Dict[str, Any]:
    """ESRS 1 paras 29-35 omission criteria with validation rules."""
    return {
        "omission_criteria": [{"criterion_key": k, **v} for k, v in OMISSION_CRITERIA.items()],
        "esrs_ref": "ESRS 1 paras 29-35",
        "note": "Proprietary and third-party-limitation omissions cannot be applied to mandatory ESRS DPs",
    }
