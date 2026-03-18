"""
API Routes: Climate Transition Plan Assessment Engine
======================================================
POST /api/v1/transition-plan/assess                     — Full transition plan assessment (TPT/GFANZ/IIGCC/CSDDD/ESRS/CDP)
POST /api/v1/transition-plan/assess-targets              — Target credibility assessment (SBTi, Paris alignment)
POST /api/v1/transition-plan/assess-sector-pathway       — Sector pathway alignment (IEA NZE, TPI, SBTi)
POST /api/v1/transition-plan/cross-framework-map         — Map provided data across all 6 frameworks
POST /api/v1/transition-plan/csddd-compliance            — CSDDD Article 22 compliance report
GET  /api/v1/transition-plan/ref/tpt-framework           — TPT 5 elements + sub-elements
GET  /api/v1/transition-plan/ref/gfanz-components        — GFANZ net-zero components (NZBA/NZAOA/NZAMI/NZIA)
GET  /api/v1/transition-plan/ref/iigcc-nzif              — IIGCC NZIF v2.0 implementation steps
GET  /api/v1/transition-plan/ref/csddd-requirements      — CSDDD Article 22 requirements (8 elements)
GET  /api/v1/transition-plan/ref/esrs-e1-disclosures     — CSRD ESRS E1 disclosure requirements (E1-1 to E1-10)
GET  /api/v1/transition-plan/ref/cdp-c4-questions        — CDP C4 targets and performance questions
GET  /api/v1/transition-plan/ref/cross-framework-mapping — Full 50+ datapoint inter-framework mapping
GET  /api/v1/transition-plan/ref/scoring-rubrics         — Scoring rubrics per framework element
GET  /api/v1/transition-plan/ref/sector-pathways         — IEA NZE / TPI / SBTi sector benchmarks
GET  /api/v1/transition-plan/ref/target-validation       — Target validation criteria (SBTi, Paris)
GET  /api/v1/transition-plan/ref/carbon-credit-quality   — Carbon credit quality criteria (ICVCM, Article 6)
GET  /api/v1/transition-plan/ref/regulatory-timeline     — CSDDD / CSRD / CDP phase-in timeline
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.transition_plan_engine import TransitionPlanEngine

router = APIRouter(prefix="/api/v1/transition-plan", tags=["Climate Transition Plan Assessment"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class AssessTransitionPlanRequest(BaseModel):
    entity_name: str
    sector: str = "power"
    reporting_year: int = 2025
    plan_data: dict = Field(default_factory=dict)


class AssessTargetsRequest(BaseModel):
    targets_data: list[dict] = Field(default_factory=list)


class AssessSectorPathwayRequest(BaseModel):
    sector: str = "power"
    current_metrics: dict = Field(default_factory=dict)
    target_year: int = 2030


class CrossFrameworkMapRequest(BaseModel):
    plan_data: dict = Field(default_factory=dict)


class CSDDDComplianceRequest(BaseModel):
    entity_name: str
    plan_data: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess_transition_plan(req: AssessTransitionPlanRequest):
    """Full transition plan assessment against TPT, GFANZ, IIGCC, CSDDD Art 22, CSRD ESRS E1, CDP C4."""
    engine = TransitionPlanEngine()
    r = engine.assess_transition_plan(
        entity_name=req.entity_name,
        sector=req.sector,
        reporting_year=req.reporting_year,
        plan_data=req.plan_data,
    )
    return r.__dict__


@router.post("/assess-targets")
def assess_targets(req: AssessTargetsRequest):
    """Assess target credibility — SBTi validation, Paris alignment, scope coverage."""
    engine = TransitionPlanEngine()
    results = engine.assess_target_credibility(req.targets_data)
    return {"target_assessments": [t.__dict__ for t in results]}


@router.post("/assess-sector-pathway")
def assess_sector_pathway(req: AssessSectorPathwayRequest):
    """Compare entity metrics against IEA NZE / TPI / SBTi sector pathways."""
    engine = TransitionPlanEngine()
    r = engine.assess_sector_pathway(
        sector=req.sector,
        current_metrics=req.current_metrics,
        target_year=req.target_year,
    )
    return r.__dict__


@router.post("/cross-framework-map")
def cross_framework_map(req: CrossFrameworkMapRequest):
    """Map provided plan data across all 6 frameworks — completeness and gap analysis."""
    engine = TransitionPlanEngine()
    return engine.map_cross_framework_datapoints(req.plan_data)


@router.post("/csddd-compliance")
def csddd_compliance(req: CSDDDComplianceRequest):
    """CSDDD Article 22 compliance report with ESRS E1 equivalence mapping."""
    engine = TransitionPlanEngine()
    return engine.generate_csddd_compliance_report(req.plan_data)


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/tpt-framework")
def ref_tpt_framework():
    """TPT Framework — 5 elements, 16+ sub-elements with disclosure IDs."""
    return {"tpt_framework": TransitionPlanEngine.get_tpt_framework()}


@router.get("/ref/gfanz-components")
def ref_gfanz_components():
    """GFANZ net-zero components — NZBA, NZAOA, NZAMI, NZIA specifics."""
    return {"gfanz_components": TransitionPlanEngine.get_gfanz_components()}


@router.get("/ref/iigcc-nzif")
def ref_iigcc_nzif():
    """IIGCC Net Zero Investment Framework v2.0 — implementation steps."""
    return {"iigcc_nzif_steps": TransitionPlanEngine.get_iigcc_nzif_steps()}


@router.get("/ref/csddd-requirements")
def ref_csddd_requirements():
    """CSDDD Article 22 — 8 transition plan requirements + Art 22(2)-(4)."""
    return {"csddd_requirements": TransitionPlanEngine.get_csddd_requirements()}


@router.get("/ref/esrs-e1-disclosures")
def ref_esrs_e1_disclosures():
    """CSRD ESRS E1 — full disclosure requirements E1-1 to E1-10 with datapoint IDs."""
    return {"esrs_e1_disclosures": TransitionPlanEngine.get_esrs_e1_disclosures()}


@router.get("/ref/cdp-c4-questions")
def ref_cdp_c4_questions():
    """CDP Climate Change C4 — targets, performance, and transition plan questions."""
    return {"cdp_c4_questions": TransitionPlanEngine.get_cdp_c4_questions()}


@router.get("/ref/cross-framework-mapping")
def ref_cross_framework_mapping():
    """Full 50+ datapoint inter-framework mapping — TPT/GFANZ/IIGCC/CSDDD/ESRS E1/CDP C4."""
    return {"cross_framework_mapping": TransitionPlanEngine.get_cross_framework_mapping()}


@router.get("/ref/scoring-rubrics")
def ref_scoring_rubrics():
    """Scoring rubrics per framework element (0-100 scale)."""
    return {"scoring_rubrics": TransitionPlanEngine.get_scoring_rubrics()}


@router.get("/ref/sector-pathways")
def ref_sector_pathways():
    """IEA NZE / TPI / SBTi sector decarbonisation pathways."""
    return {"sector_pathways": TransitionPlanEngine.get_sector_pathways()}


@router.get("/ref/target-validation")
def ref_target_validation():
    """Target validation criteria — SBTi, Paris 1.5C alignment rules."""
    return {"target_validation_criteria": TransitionPlanEngine.get_target_validation_criteria()}


@router.get("/ref/carbon-credit-quality")
def ref_carbon_credit_quality():
    """Carbon credit quality criteria — ICVCM CCP, Article 6.4, vintage limits."""
    return {"carbon_credit_quality_criteria": TransitionPlanEngine.get_carbon_credit_quality_criteria()}


@router.get("/ref/regulatory-timeline")
def ref_regulatory_timeline():
    """Regulatory timeline — CSDDD phase-in, CSRD wave 1/2/3, CDP deadlines."""
    return {"regulatory_timeline": TransitionPlanEngine.get_regulatory_timeline()}
