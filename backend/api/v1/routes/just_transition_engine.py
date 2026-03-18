"""
API Routes: Just Transition & Social Risk — E47
================================================
POST /api/v1/just-transition/ilo-assessment       — ILO JT 5-dimension scoring
POST /api/v1/just-transition/esrs-social          — ESRS S1-S4 scoring
POST /api/v1/just-transition/sec-human-capital    — SEC Item 101(c) assessment
POST /api/v1/just-transition/living-wage          — Anker living wage gap analysis
POST /api/v1/just-transition/worker-displacement  — Displacement modelling
POST /api/v1/just-transition/cbi-jt-finance       — CBI JT Finance eligibility
POST /api/v1/just-transition/stakeholder-mapping  — Stakeholder impact mapping
POST /api/v1/just-transition/full-assessment      — Complete JT assessment
GET  /api/v1/just-transition/ref/ilo-dimensions          — ILO JT 5 dimensions
GET  /api/v1/just-transition/ref/esrs-social-requirements — ESRS S1-S4 DPs
GET  /api/v1/just-transition/ref/living-wage-benchmarks  — Anker benchmarks by country
GET  /api/v1/just-transition/ref/cbi-criteria            — CBI JT 8 criteria
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

try:
    from services.just_transition_engine import get_engine
    from services.just_transition_engine import (
        ILO_JT_DIMENSIONS,
        ESRS_S1_REQUIREMENTS,
        ESRS_S2_REQUIREMENTS,
        ESRS_S3_REQUIREMENTS,
        ESRS_S4_REQUIREMENTS,
        ANKER_LIVING_WAGE_BENCHMARKS,
        CBI_JT_CRITERIA,
        ILO_JT_CLASSIFICATION_THRESHOLDS,
        AUTOMATION_RISK_BY_NACE,
        TRANSITION_DISPLACEMENT_BY_SECTOR,
        SEC_HUMAN_CAPITAL_INDICATORS,
    )
    _engine = get_engine()
except Exception:
    _engine = None
    ILO_JT_DIMENSIONS = {}
    ESRS_S1_REQUIREMENTS = []
    ESRS_S2_REQUIREMENTS = []
    ESRS_S3_REQUIREMENTS = []
    ESRS_S4_REQUIREMENTS = []
    ANKER_LIVING_WAGE_BENCHMARKS = {}
    CBI_JT_CRITERIA = []
    ILO_JT_CLASSIFICATION_THRESHOLDS = {}
    AUTOMATION_RISK_BY_NACE = {}
    TRANSITION_DISPLACEMENT_BY_SECTOR = {}
    SEC_HUMAN_CAPITAL_INDICATORS = []

router = APIRouter(prefix="/api/v1/just-transition", tags=["Just Transition"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ILOAssessmentRequest(BaseModel):
    entity_id: str
    sector: str = "fossil_fuels"
    geography: str = "GB"
    jt_evidence: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


class ESRSSocialRequest(BaseModel):
    entity_id: str
    disclosure_data: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


class SECHumanCapitalRequest(BaseModel):
    entity_id: str
    hc_data: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


class LivingWageRequest(BaseModel):
    entity_id: str
    wage_data: list[dict] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=lambda: ["GB", "DE"])

    class Config:
        extra = "allow"


class WorkerDisplacementRequest(BaseModel):
    entity_id: str
    sector: str = "fossil_fuels"
    workforce_size: int = Field(default=5000, ge=1)
    automation_investment: float = Field(default=10_000_000, ge=0)
    transition_timeline: int = Field(default=10, ge=1, le=30)

    class Config:
        extra = "allow"


class CBIJTFinanceRequest(BaseModel):
    entity_id: str
    project_data: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


class StakeholderMappingRequest(BaseModel):
    entity_id: str
    sector: str = "fossil_fuels"
    geography: str = "GB"
    workforce_size: int = Field(default=5000, ge=1)

    class Config:
        extra = "allow"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    entity_data: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/ilo-assessment")
def ilo_assessment(req: ILOAssessmentRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_ilo_jt(
        entity_id=req.entity_id,
        sector=req.sector,
        geography=req.geography,
        jt_evidence=req.jt_evidence,
    )
    return {"status": "success", "data": result}


@router.post("/esrs-social")
def esrs_social(req: ESRSSocialRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.score_esrs_social(
        entity_id=req.entity_id,
        disclosure_data=req.disclosure_data,
    )
    return {"status": "success", "data": result}


@router.post("/sec-human-capital")
def sec_human_capital(req: SECHumanCapitalRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_sec_human_capital(
        entity_id=req.entity_id,
        hc_data=req.hc_data,
    )
    return {"status": "success", "data": result}


@router.post("/living-wage")
def living_wage(req: LivingWageRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.calculate_living_wage_gap(
        entity_id=req.entity_id,
        wage_data=req.wage_data,
        countries=req.countries,
    )
    return {"status": "success", "data": result}


@router.post("/worker-displacement")
def worker_displacement(req: WorkerDisplacementRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.model_worker_displacement(
        entity_id=req.entity_id,
        sector=req.sector,
        workforce_size=req.workforce_size,
        automation_investment=req.automation_investment,
        transition_timeline=req.transition_timeline,
    )
    return {"status": "success", "data": result}


@router.post("/cbi-jt-finance")
def cbi_jt_finance(req: CBIJTFinanceRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_cbi_jt_finance(
        entity_id=req.entity_id,
        project_data=req.project_data,
    )
    return {"status": "success", "data": result}


@router.post("/stakeholder-mapping")
def stakeholder_mapping(req: StakeholderMappingRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.map_stakeholder_impacts(
        entity_id=req.entity_id,
        sector=req.sector,
        geography=req.geography,
        workforce_size=req.workforce_size,
    )
    return {"status": "success", "data": result}


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.generate_full_assessment(
        entity_id=req.entity_id,
        entity_data=req.entity_data,
    )
    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ilo-dimensions")
def ref_ilo_dimensions():
    return {
        "status": "success",
        "data": {
            "framework": "ILO Guidelines for a Just Transition towards Environmentally Sustainable Economies and Societies (2015)",
            "total_dimensions": len(ILO_JT_DIMENSIONS),
            "dimensions": ILO_JT_DIMENSIONS,
            "classification_thresholds": ILO_JT_CLASSIFICATION_THRESHOLDS,
            "automation_risk_by_nace": AUTOMATION_RISK_BY_NACE,
            "transition_displacement_by_sector": TRANSITION_DISPLACEMENT_BY_SECTOR,
        },
    }


@router.get("/ref/esrs-social-requirements")
def ref_esrs_social_requirements():
    return {
        "status": "success",
        "data": {
            "framework": "CSRD ESRS — Social Standards (EFRAG IG3)",
            "S1": {
                "name": "Own Workforce",
                "requirements_count": len(ESRS_S1_REQUIREMENTS),
                "requirements": ESRS_S1_REQUIREMENTS,
                "mandatory_count": sum(1 for r in ESRS_S1_REQUIREMENTS if r["mandatory_for_all"]),
            },
            "S2": {
                "name": "Workers in the Value Chain",
                "requirements_count": len(ESRS_S2_REQUIREMENTS),
                "requirements": ESRS_S2_REQUIREMENTS,
                "mandatory_count": sum(1 for r in ESRS_S2_REQUIREMENTS if r["mandatory_for_all"]),
            },
            "S3": {
                "name": "Affected Communities",
                "requirements_count": len(ESRS_S3_REQUIREMENTS),
                "requirements": ESRS_S3_REQUIREMENTS,
                "mandatory_count": sum(1 for r in ESRS_S3_REQUIREMENTS if r["mandatory_for_all"]),
            },
            "S4": {
                "name": "Consumers and End-Users",
                "requirements_count": len(ESRS_S4_REQUIREMENTS),
                "requirements": ESRS_S4_REQUIREMENTS,
                "mandatory_count": sum(1 for r in ESRS_S4_REQUIREMENTS if r["mandatory_for_all"]),
            },
            "sec_human_capital_indicators": SEC_HUMAN_CAPITAL_INDICATORS,
        },
    }


@router.get("/ref/living-wage-benchmarks")
def ref_living_wage_benchmarks():
    return {
        "status": "success",
        "data": {
            "source": "Anker Research Institute — Living Wage Benchmarks (2024)",
            "methodology": "Based on cost of a nutritious diet, decent housing, transport, and a small contingency",
            "currency": "USD/month (net)",
            "benchmarks": ANKER_LIVING_WAGE_BENCHMARKS,
            "countries_covered": len(ANKER_LIVING_WAGE_BENCHMARKS),
            "note": "Benchmarks updated annually. Global Living Wage Coalition endorsed methodology.",
        },
    }


@router.get("/ref/cbi-criteria")
def ref_cbi_criteria():
    return {
        "status": "success",
        "data": {
            "standard": "Climate Bonds Initiative — Just Transition Finance Label Criteria (2023)",
            "total_criteria": len(CBI_JT_CRITERIA),
            "eligibility_threshold": "6 of 8 criteria must be met",
            "criteria": CBI_JT_CRITERIA,
            "applicable_instruments": [
                "Green bonds with JT label", "Social bonds", "Sustainability bonds",
                "Project finance (greenfield and brownfield transition projects)",
                "Sovereign and sub-sovereign instruments in transition economies",
            ],
            "url": "https://www.climatebonds.net/standard/just-transition",
        },
    }
