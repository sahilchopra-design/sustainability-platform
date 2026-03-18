"""
API Routes: TNFD Nature-Related Disclosures
=============================================
POST /api/v1/tnfd/assess-disclosures       — Full TNFD 14-disclosure compliance assessment
POST /api/v1/tnfd/assess-materiality       — Nature-related double materiality assessment
POST /api/v1/tnfd/assess-leap-readiness    — LEAP methodology readiness scoring
GET  /api/v1/tnfd/ref/recommended-disclosures — TNFD 14 recommended disclosures
GET  /api/v1/tnfd/ref/leap-phases          — TNFD LEAP phases and sub-components
GET  /api/v1/tnfd/ref/ecosystem-services   — ENCORE 21 ecosystem services
GET  /api/v1/tnfd/ref/nature-risk-categories — Nature risk categories (physical/transition/systemic)
GET  /api/v1/tnfd/ref/sector-guidance      — Sector-specific TNFD guidance
GET  /api/v1/tnfd/ref/cross-framework      — TNFD cross-framework mapping (ISSB/ESRS/GRI/CBD)
GET  /api/v1/tnfd/ref/pillar-structure     — Disclosure pillar structure
GET  /api/v1/tnfd/ref/priority-areas       — Priority area identification criteria
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.tnfd_assessment_engine import TNFDAssessmentEngine

router = APIRouter(prefix="/api/v1/tnfd", tags=["TNFD Nature-Related Disclosures"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class TNFDDisclosureRequest(BaseModel):
    entity_name: str
    reporting_year: int = 2025
    disclosure_data: Optional[dict] = None
    sector: Optional[str] = None


class TNFDMaterialityRequest(BaseModel):
    entity_name: str
    reporting_year: int = 2025
    sector: str = "financial_services"
    dependencies: Optional[dict] = None
    impacts: Optional[dict] = None


class TNFDLEAPRequest(BaseModel):
    entity_name: str
    reporting_year: int = 2025
    leap_data: Optional[dict] = None


# ---------------------------------------------------------------------------
# Assessment Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess-disclosures")
def assess_disclosures(req: TNFDDisclosureRequest):
    """Full TNFD 14-disclosure compliance assessment — pillars, LEAP scoring, nature risk profile."""
    engine = TNFDAssessmentEngine()
    r = engine.assess_disclosures(
        entity_name=req.entity_name,
        reporting_year=req.reporting_year,
        disclosure_data=req.disclosure_data,
        sector=req.sector,
    )
    return r.__dict__


@router.post("/assess-materiality")
def assess_materiality(req: TNFDMaterialityRequest):
    """Nature-related double materiality — financial vs impact materiality, ecosystem service priority."""
    engine = TNFDAssessmentEngine()
    r = engine.assess_nature_materiality(
        entity_name=req.entity_name,
        reporting_year=req.reporting_year,
        sector=req.sector,
        dependencies=req.dependencies,
        impacts=req.impacts,
    )
    return r.__dict__


@router.post("/assess-leap-readiness")
def assess_leap_readiness(req: TNFDLEAPRequest):
    """LEAP methodology readiness scoring — per-phase and overall readiness level."""
    engine = TNFDAssessmentEngine()
    return engine.assess_leap_readiness(
        entity_name=req.entity_name,
        reporting_year=req.reporting_year,
        leap_data=req.leap_data,
    )


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/recommended-disclosures")
def ref_recommended_disclosures():
    """TNFD 14 recommended disclosures across 4 pillars."""
    return {"recommended_disclosures": TNFDAssessmentEngine.get_recommended_disclosures()}


@router.get("/ref/leap-phases")
def ref_leap_phases():
    """TNFD LEAP phases (Locate, Evaluate, Assess, Prepare) with sub-components."""
    return {"leap_phases": TNFDAssessmentEngine.get_leap_phases()}


@router.get("/ref/ecosystem-services")
def ref_ecosystem_services():
    """ENCORE 21 ecosystem services classification."""
    return {"ecosystem_services": TNFDAssessmentEngine.get_encore_ecosystem_services()}


@router.get("/ref/nature-risk-categories")
def ref_nature_risk_categories():
    """Nature risk categories: physical, transition, systemic."""
    return {"nature_risk_categories": TNFDAssessmentEngine.get_nature_risk_categories()}


@router.get("/ref/sector-guidance")
def ref_sector_guidance():
    """Sector-specific TNFD guidance with priority nature topics."""
    return {"sector_guidance": TNFDAssessmentEngine.get_sector_guidance()}


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """TNFD cross-framework mapping to ISSB S1, CSRD ESRS E4, GRI 304, CBD GBF Target 15."""
    return {"cross_framework_mapping": TNFDAssessmentEngine.get_cross_framework_map()}


@router.get("/ref/pillar-structure")
def ref_pillar_structure():
    """TNFD disclosure pillar structure (Governance, Strategy, Risk & Impact Mgmt, Metrics & Targets)."""
    return {"pillar_structure": TNFDAssessmentEngine.get_disclosure_pillar_structure()}


@router.get("/ref/priority-areas")
def ref_priority_areas():
    """Priority area identification criteria (KBAs, protected areas, water-stressed regions)."""
    return {"priority_area_criteria": TNFDAssessmentEngine.get_priority_area_criteria()}
