"""
API Routes: IFRS S1 General Sustainability Disclosures Engine (E18)
====================================================================
POST /api/v1/ifrs-s1/assess                       — Full 4-pillar IFRS S1 assessment
POST /api/v1/ifrs-s1/assess/pillar                — Assess a single pillar
POST /api/v1/ifrs-s1/assess/batch                 — Batch: multiple entities
GET  /api/v1/ifrs-s1/ref/pillars                  — IFRS_S1_PILLARS reference
GET  /api/v1/ifrs-s1/ref/disclosure-requirements  — IFRS_S1_DISCLOSURE_REQUIREMENTS
GET  /api/v1/ifrs-s1/ref/industry-sasb-mapping    — INDUSTRY_SASB_MAPPING reference
GET  /api/v1/ifrs-s1/ref/cross-framework          — Cross-framework mapping
GET  /api/v1/ifrs-s1/ref/reliefs                  — Transitional reliefs
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.ifrs_s1_engine import (
    IFRSS1Engine,
    S1DisclosureInput,
    S1AssessmentInput,
    IFRS_S1_PILLARS,
    IFRS_S1_DISCLOSURE_REQUIREMENTS,
    INDUSTRY_SASB_MAPPING,
    IFRS_S1_CROSS_FRAMEWORK,
    IFRS_S1_RELIEFS,
)

router = APIRouter(
    prefix="/api/v1/ifrs-s1",
    tags=["IFRS S1 — General Sustainability Disclosures"],
)

_ENGINE = IFRSS1Engine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class S1DisclosureModel(BaseModel):
    requirement_id: str = Field(..., description="IFRS S1 requirement ID (e.g. 'S1.15')")
    disclosed: bool = Field(..., description="Whether the requirement has been addressed")
    disclosure_quality: str = Field(
        "none", description="Quality of disclosure: none | partial | full"
    )
    notes: str = Field("", description="Optional reviewer notes")


class S1AssessmentModel(BaseModel):
    entity_id: str
    entity_name: str
    industry: str = Field(
        "general",
        description=(
            "SASB industry sector: financial_services | energy | real_estate | "
            "technology | healthcare | consumer_goods | industrials | general"
        ),
    )
    reporting_year: int = Field(2025, description="Reporting period year")
    disclosures: Dict[str, S1DisclosureModel] = Field(
        default_factory=dict,
        description="Map of requirement_id → disclosure status; omitted = not disclosed",
    )
    applying_reliefs: List[str] = Field(
        default_factory=list,
        description=(
            "List of transitional relief IDs being applied "
            "(prior_period_comparative | scope3_grace_period | industry_metrics_grace)"
        ),
    )


class PillarAssessmentModel(BaseModel):
    pillar_id: str = Field(
        ...,
        description="Pillar to assess: governance | strategy | risk_management | metrics_targets",
    )
    entity_id: str
    entity_name: str
    disclosures: Dict[str, S1DisclosureModel] = Field(
        default_factory=dict,
        description="Map of requirement_id → disclosure status for this pillar",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_disc_input(m: S1DisclosureModel) -> S1DisclosureInput:
    return S1DisclosureInput(
        requirement_id=m.requirement_id,
        disclosed=m.disclosed,
        disclosure_quality=m.disclosure_quality,
        notes=m.notes,
    )


def _to_assessment_input(body: S1AssessmentModel) -> S1AssessmentInput:
    return S1AssessmentInput(
        entity_id=body.entity_id,
        entity_name=body.entity_name,
        industry=body.industry,
        reporting_year=body.reporting_year,
        disclosures={k: _to_disc_input(v) for k, v in body.disclosures.items()},
        applying_reliefs=body.applying_reliefs,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Full IFRS S1 4-pillar compliance assessment")
def assess(body: S1AssessmentModel) -> Dict[str, Any]:
    """
    Assess an entity's IFRS S1 disclosure completeness across all four pillars:
    Governance, Strategy, Risk Management, and Metrics & Targets.

    Returns pillar-level scores, overall compliance status (threshold 70%),
    blocking gaps, SASB industry codes, priority actions, and cross-framework mapping.
    """
    result = _ENGINE.assess(_to_assessment_input(body))
    return result.dict()


@router.post("/assess/pillar", summary="Assess a single IFRS S1 pillar")
def assess_pillar(body: PillarAssessmentModel) -> Dict[str, Any]:
    """
    Assess a single IFRS S1 pillar in isolation. Useful for iterative
    gap-filling workflows or partial-year reviews.
    """
    disclosures = {k: _to_disc_input(v) for k, v in body.disclosures.items()}
    result = _ENGINE.assess_pillar(
        pillar_id=body.pillar_id,
        entity_id=body.entity_id,
        entity_name=body.entity_name,
        disclosures=disclosures,
    )
    return result.dict()


@router.post("/assess/batch", summary="Batch assess multiple entities")
def assess_batch(body: List[S1AssessmentModel]) -> List[Dict[str, Any]]:
    """
    Assess multiple entities (e.g. subsidiaries in a group) in a single
    API call. Returns one IFRSS1Result per entity in input order.
    """
    return [_ENGINE.assess(_to_assessment_input(b)).dict() for b in body]


@router.get("/ref/pillars", summary="IFRS S1 pillar definitions")
def ref_pillars() -> Dict[str, Any]:
    """Return IFRS_S1_PILLARS — 4 pillars (Governance, Strategy, Risk Management,
    Metrics & Targets) with paragraph references and blocking flags."""
    return _ENGINE.get_pillars()


@router.get("/ref/disclosure-requirements", summary="Individual IFRS S1 disclosure requirements")
def ref_disclosure_requirements() -> Dict[str, Any]:
    """Return IFRS_S1_DISCLOSURE_REQUIREMENTS — 13 key disclosure requirements
    mapped to pillars, with descriptions and blocking flags."""
    return _ENGINE.get_disclosure_requirements()


@router.get("/ref/industry-sasb-mapping", summary="SASB industry codes per sector (S1.38)")
def ref_industry_sasb_mapping() -> Dict[str, List[str]]:
    """Return INDUSTRY_SASB_MAPPING — SASB sector codes by industry (required
    as part of S1.38 ISSB Standards metrics)."""
    return _ENGINE.get_industry_sasb_mapping()


@router.get("/ref/cross-framework", summary="Cross-framework mapping (S2, CSRD, TCFD, GRI, SASB, SEC)")
def ref_cross_framework() -> Dict[str, str]:
    """Return IFRS_S1_CROSS_FRAMEWORK — alignment notes with IFRS S2,
    CSRD ESRS, TCFD, GRI Universal Standards, SASB, and SEC Climate Rule."""
    return _ENGINE.get_cross_framework()


@router.get("/ref/reliefs", summary="IFRS S1 transitional reliefs")
def ref_reliefs() -> Dict[str, Any]:
    """Return IFRS_S1_RELIEFS — three transitional reliefs available in the
    first year of IFRS S1 application (prior period, Scope 3, industry metrics)."""
    return _ENGINE.get_reliefs()
