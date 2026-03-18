"""
API Routes: Biodiversity Finance v2 — E44
==========================================
POST /api/v1/biodiversity-finance-v2/leap-assessment     — Full TNFD LEAP assessment
POST /api/v1/biodiversity-finance-v2/pbaf-attribution    — PBAF portfolio attribution
POST /api/v1/biodiversity-finance-v2/encore-scoring      — ENCORE ecosystem services scoring
POST /api/v1/biodiversity-finance-v2/msa-footprint       — MSA footprint calculation
POST /api/v1/biodiversity-finance-v2/gbf-alignment       — GBF/COP15 alignment check
POST /api/v1/biodiversity-finance-v2/bng-calculation     — BNG net gain calculation
POST /api/v1/biodiversity-finance-v2/bffi-score          — BFFI portfolio score
POST /api/v1/biodiversity-finance-v2/full-assessment     — Complete assessment
GET  /api/v1/biodiversity-finance-v2/ref/ecosystem-services  — ENCORE services list
GET  /api/v1/biodiversity-finance-v2/ref/gbf-targets         — GBF 23 targets
GET  /api/v1/biodiversity-finance-v2/ref/pbaf-methods        — PBAF methodology descriptions
GET  /api/v1/biodiversity-finance-v2/ref/bng-habitats        — BNG habitat condition multipliers
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

try:
    from services.biodiversity_finance_v2_engine import get_engine
    from services.biodiversity_finance_v2_engine import (
        ENCORE_ECOSYSTEM_SERVICES,
        GBF_TARGETS,
        PBAF_METHODS,
        BNG_HABITAT_CONDITION_MULTIPLIERS,
        MSA_LAND_USE_LOOKUP,
    )
    _engine = get_engine()
except Exception:
    _engine = None
    ENCORE_ECOSYSTEM_SERVICES = {}
    GBF_TARGETS = {}
    PBAF_METHODS = {}
    BNG_HABITAT_CONDITION_MULTIPLIERS = {}
    MSA_LAND_USE_LOOKUP = {}

router = APIRouter(prefix="/api/v1/biodiversity-finance-v2", tags=["Biodiversity Finance v2"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class LEAPAssessmentRequest(BaseModel):
    entity_id: str
    sectors: list[str] = Field(default_factory=lambda: ["A01"])
    locations: list[dict] = Field(default_factory=lambda: [{"lat": 51.5, "lng": -0.1, "country": "GB"}])
    financial_exposure: float = Field(default=100_000_000, ge=0)
    financial_year: int = 2024

    class Config:
        extra = "allow"


class PBAFAttributionRequest(BaseModel):
    entity_id: str
    portfolio_holdings: list[dict] = Field(default_factory=list)
    method: str = "outstanding_amount"

    class Config:
        extra = "allow"


class ENCOREScoringRequest(BaseModel):
    entity_id: str
    nace_sectors: list[str] = Field(default_factory=lambda: ["A01"])
    company_revenue_split: Optional[dict[str, float]] = None

    class Config:
        extra = "allow"


class MSAFootprintRequest(BaseModel):
    entity_id: str
    land_use_data: list[dict] = Field(default_factory=list)

    class Config:
        extra = "allow"


class GBFAlignmentRequest(BaseModel):
    entity_id: str
    portfolio_data: dict = Field(default_factory=dict)
    reporting_year: int = 2024

    class Config:
        extra = "allow"


class BNGCalculationRequest(BaseModel):
    entity_id: str
    pre_development: float = Field(default=10.0, ge=0)
    post_development: float = Field(default=8.0, ge=0)
    habitat_type: str = "grassland"
    condition_before: str = "moderate"
    condition_after: str = "good"

    class Config:
        extra = "allow"


class BFFIScoreRequest(BaseModel):
    entity_id: str
    portfolio_holdings: list[dict] = Field(default_factory=list)

    class Config:
        extra = "allow"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    portfolio_data: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/leap-assessment")
def leap_assessment(req: LEAPAssessmentRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_tnfd_leap(
        entity_id=req.entity_id,
        sectors=req.sectors,
        locations=req.locations,
        financial_exposure=req.financial_exposure,
        financial_year=req.financial_year,
    )
    return {"status": "success", "data": result}


@router.post("/pbaf-attribution")
def pbaf_attribution(req: PBAFAttributionRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.calculate_pbaf_attribution(
        entity_id=req.entity_id,
        portfolio_holdings=req.portfolio_holdings,
        method=req.method,
    )
    return {"status": "success", "data": result}


@router.post("/encore-scoring")
def encore_scoring(req: ENCOREScoringRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.score_encore_services(
        entity_id=req.entity_id,
        nace_sectors=req.nace_sectors,
        company_revenue_split=req.company_revenue_split,
    )
    return {"status": "success", "data": result}


@router.post("/msa-footprint")
def msa_footprint(req: MSAFootprintRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.calculate_msa_footprint(
        entity_id=req.entity_id,
        land_use_data=req.land_use_data,
    )
    return {"status": "success", "data": result}


@router.post("/gbf-alignment")
def gbf_alignment(req: GBFAlignmentRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_gbf_alignment(
        entity_id=req.entity_id,
        portfolio_data=req.portfolio_data,
        reporting_year=req.reporting_year,
    )
    return {"status": "success", "data": result}


@router.post("/bng-calculation")
def bng_calculation(req: BNGCalculationRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.calculate_bng(
        entity_id=req.entity_id,
        pre_development=req.pre_development,
        post_development=req.post_development,
        habitat_type=req.habitat_type,
        condition_before=req.condition_before,
        condition_after=req.condition_after,
    )
    return {"status": "success", "data": result}


@router.post("/bffi-score")
def bffi_score(req: BFFIScoreRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.calculate_bffi(
        entity_id=req.entity_id,
        portfolio_holdings=req.portfolio_holdings,
    )
    return {"status": "success", "data": result}


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.generate_full_assessment(
        entity_id=req.entity_id,
        portfolio_data=req.portfolio_data,
    )
    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ecosystem-services")
def ref_ecosystem_services():
    return {
        "status": "success",
        "data": {
            "total_services": len(ENCORE_ECOSYSTEM_SERVICES),
            "services": {
                svc_id: {
                    "name": svc_id.replace("_", " ").title(),
                    **meta,
                }
                for svc_id, meta in ENCORE_ECOSYSTEM_SERVICES.items()
            },
            "categories": ["regulating", "provisioning", "cultural"],
            "source": "ENCORE — Exploring Natural Capital Opportunities, Risks and Exposure",
        },
    }


@router.get("/ref/gbf-targets")
def ref_gbf_targets():
    return {
        "status": "success",
        "data": {
            "framework": "Kunming-Montreal Global Biodiversity Framework (COP15, Dec 2022)",
            "total_targets": len(GBF_TARGETS),
            "targets": [
                {"target_id": tid, "description": desc}
                for tid, desc in GBF_TARGETS.items()
            ],
            "key_business_targets": ["T01", "T02", "T07", "T10", "T14", "T15", "T19"],
        },
    }


@router.get("/ref/pbaf-methods")
def ref_pbaf_methods():
    return {
        "status": "success",
        "data": {
            "standard": "PBAF Standard v2 (2023) — Portfolio Biodiversity Accounting and Assessment",
            "methods": PBAF_METHODS,
            "guidance": "Select method based on asset class; equity_ownership preferred for listed equity",
        },
    }


@router.get("/ref/bng-habitats")
def ref_bng_habitats():
    return {
        "status": "success",
        "data": {
            "standard": "Natural England Biodiversity Net Gain Metric 4.0 (2023)",
            "condition_multipliers": BNG_HABITAT_CONDITION_MULTIPLIERS,
            "land_use_msa_fractions": MSA_LAND_USE_LOOKUP,
            "mandatory_threshold_pct": 10,
            "legislative_reference": "Environment Act 2021 (UK) — Schedule 14",
        },
    }
