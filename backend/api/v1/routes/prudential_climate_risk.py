"""
API Routes: Prudential Climate Risk — E45
==========================================
POST /api/v1/prudential-climate-risk/boe-bes            — BOE/PRA BES stress test
POST /api/v1/prudential-climate-risk/ecb-dfast          — ECB DFAST climate stress test
POST /api/v1/prudential-climate-risk/ngfs-v4            — NGFS v4 multi-scenario assessment
POST /api/v1/prudential-climate-risk/icaap-overlay      — ICAAP Pillar 2a/2b overlay
POST /api/v1/prudential-climate-risk/sarp431            — Basel SRP 43.1 categorisation
POST /api/v1/prudential-climate-risk/capital-overlays   — Segment-level capital overlay
POST /api/v1/prudential-climate-risk/full-assessment    — Complete prudential assessment
GET  /api/v1/prudential-climate-risk/ref/ngfs-scenarios      — NGFS v4 scenario details
GET  /api/v1/prudential-climate-risk/ref/boe-bes             — BOE BES round parameters
GET  /api/v1/prudential-climate-risk/ref/sector-risk         — Sector transition/physical risk ratings
GET  /api/v1/prudential-climate-risk/ref/icaap-thresholds    — ICAAP materiality thresholds
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

try:
    from services.prudential_climate_risk_engine import get_engine
    from services.prudential_climate_risk_engine import (
        NGFS_V4_SCENARIOS,
        BOE_BES_ROUNDS,
        ECB_CST_ROUNDS,
        SECTOR_TRANSITION_RISK,
        SECTOR_PHYSICAL_RISK,
        ICAAP_GUIDANCE,
        BASEL_SRP431,
        EBA_SREP_SCORING,
    )
    _engine = get_engine()
except Exception:
    _engine = None
    NGFS_V4_SCENARIOS = {}
    BOE_BES_ROUNDS = {}
    ECB_CST_ROUNDS = {}
    SECTOR_TRANSITION_RISK = {}
    SECTOR_PHYSICAL_RISK = {}
    ICAAP_GUIDANCE = {}
    BASEL_SRP431 = {}
    EBA_SREP_SCORING = {}

router = APIRouter(prefix="/api/v1/prudential-climate-risk", tags=["Prudential Climate Risk"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class BOEBESRequest(BaseModel):
    entity_id: str
    loan_book_segments: list[dict] = Field(default_factory=list)
    market_portfolio: Optional[dict] = None
    institution_type: str = "bank"
    bes_round: str = "BES_2025"

    class Config:
        extra = "allow"


class ECBDFASTRequest(BaseModel):
    entity_id: str
    loan_book_segments: list[dict] = Field(default_factory=list)
    cst_round: str = "CST_2024"

    class Config:
        extra = "allow"


class NGFSV4Request(BaseModel):
    entity_id: str
    portfolio_data: dict = Field(default_factory=dict)
    scenarios: Optional[list[str]] = None

    class Config:
        extra = "allow"


class ICAAPovelayRequest(BaseModel):
    entity_id: str
    stressed_results: dict = Field(default_factory=dict)
    institution_type: str = "bank"

    class Config:
        extra = "allow"


class SARP431Request(BaseModel):
    entity_id: str
    rwa_data: dict = Field(default_factory=dict)
    climate_rwa_impact: float = Field(default=50_000_000, ge=0)

    class Config:
        extra = "allow"


class CapitalOverlaysRequest(BaseModel):
    entity_id: str
    loan_book_segments: list[dict] = Field(default_factory=list)
    scenario: str = "delayed_transition"

    class Config:
        extra = "allow"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    institution_data: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/boe-bes")
def boe_bes(req: BOEBESRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_boe_bes(
        entity_id=req.entity_id,
        loan_book_segments=req.loan_book_segments,
        market_portfolio=req.market_portfolio,
        institution_type=req.institution_type,
        bes_round=req.bes_round,
    )
    return {"status": "success", "data": result}


@router.post("/ecb-dfast")
def ecb_dfast(req: ECBDFASTRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_ecb_dfast(
        entity_id=req.entity_id,
        loan_book_segments=req.loan_book_segments,
        cst_round=req.cst_round,
    )
    return {"status": "success", "data": result}


@router.post("/ngfs-v4")
def ngfs_v4(req: NGFSV4Request):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_ngfs_v4(
        entity_id=req.entity_id,
        portfolio_data=req.portfolio_data,
        scenarios=req.scenarios,
    )
    return {"status": "success", "data": result}


@router.post("/icaap-overlay")
def icaap_overlay(req: ICAAPovelayRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.calculate_icaap_overlay(
        entity_id=req.entity_id,
        stressed_results=req.stressed_results,
        institution_type=req.institution_type,
    )
    return {"status": "success", "data": result}


@router.post("/sarp431")
def sarp431(req: SARP431Request):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_sarp431(
        entity_id=req.entity_id,
        rwa_data=req.rwa_data,
        climate_rwa_impact=req.climate_rwa_impact,
    )
    return {"status": "success", "data": result}


@router.post("/capital-overlays")
def capital_overlays(req: CapitalOverlaysRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.generate_capital_overlays(
        entity_id=req.entity_id,
        loan_book_segments=req.loan_book_segments,
        scenario=req.scenario,
    )
    return {"status": "success", "data": result}


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.generate_full_assessment(
        entity_id=req.entity_id,
        institution_data=req.institution_data,
    )
    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ngfs-scenarios")
def ref_ngfs_scenarios():
    return {
        "status": "success",
        "data": {
            "version": "NGFS Phase IV (June 2023)",
            "scenarios_count": len(NGFS_V4_SCENARIOS),
            "scenarios": NGFS_V4_SCENARIOS,
            "categories": {
                "orderly": "Smooth, early climate policy action; manageable transition risk",
                "disorderly": "Late or divergent action; higher transition risk, lower physical risk",
                "hot_house": "Minimal action; severe physical risk materialises over time",
            },
        },
    }


@router.get("/ref/boe-bes")
def ref_boe_bes():
    return {
        "status": "success",
        "data": {
            "rounds": BOE_BES_ROUNDS,
            "regulatory_reference": "PRA SS3/19 + SS19/23 — Climate-related financial risks",
            "methodology": "30-year exploratory scenario exercise; not pass/fail; no capital floor",
        },
    }


@router.get("/ref/sector-risk")
def ref_sector_risk():
    return {
        "status": "success",
        "data": {
            "transition_risk": SECTOR_TRANSITION_RISK,
            "physical_risk": SECTOR_PHYSICAL_RISK,
            "rating_scale": ["high", "medium", "low", "very_high"],
            "pd_units": "basis points uplift on top of base PD",
        },
    }


@router.get("/ref/icaap-thresholds")
def ref_icaap_thresholds():
    return {
        "status": "success",
        "data": {
            "icaap_guidance": ICAAP_GUIDANCE,
            "basel_srp431": BASEL_SRP431,
            "eba_srep_scoring": EBA_SREP_SCORING,
            "references": [
                "PRA SS3/19 — Enhancing banks' and insurers' approaches to managing climate-related financial risk",
                "PRA SS19/23 — Management of climate-related financial risks (updated 2023)",
                "BCBS SRP 43.1 — Climate-related financial risk supervisory review",
                "EBA/GL/2020/06 — SREP guidelines with climate integration",
            ],
        },
    }
