"""
Carbon Credit Quality & Integrity API routes.
Prefix: /api/v1/carbon-credit-quality
Tags: Carbon Credit Quality
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.carbon_credit_quality_engine import get_engine

router = APIRouter(prefix="/api/v1/carbon-credit-quality", tags=["Carbon Credit Quality"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ScoreProjectRequest(BaseModel):
    entity_id: str
    project_id: str
    project_name: str
    standard: str = Field(..., example="vcs")
    methodology: str = Field(..., example="VM0015")
    project_type: str = Field(..., example="redd_plus")
    vintage_year: int = Field(..., example=2022)
    volume_tco2e: float = Field(..., example=50000.0)


class PortfolioItem(BaseModel):
    project_id: str
    project_name: str
    standard: str = Field(default="vcs")
    methodology: str = Field(default="VM0015")
    project_type: str = Field(default="redd_plus")
    vintage_year: int = Field(default=2022)
    volume_tco2e: float = Field(default=10000.0)


class ScorePortfolioRequest(BaseModel):
    entity_id: str
    portfolio: list[PortfolioItem]


class CheckCCPEligibilityRequest(BaseModel):
    standard: str = Field(..., example="vcs")
    methodology: str = Field(..., example="VM0033")
    project_type: str = Field(..., example="blue_carbon")


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/score-project")
def score_project(req: ScoreProjectRequest) -> dict:
    """
    Score a single carbon credit project for quality and integrity.
    Returns overall quality score (0-100), grade (A-D), ICVCM CCP criteria results,
    CORSIA eligibility, permanence risk, additionality/double-counting risk, and price range.
    """
    try:
        engine = get_engine()
        result = engine.score_project(
            entity_id=req.entity_id,
            project_id=req.project_id,
            project_name=req.project_name,
            standard=req.standard,
            methodology=req.methodology,
            project_type=req.project_type,
            vintage_year=req.vintage_year,
            volume_tco2e=req.volume_tco2e,
        )
        return asdict(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/score-portfolio")
def score_portfolio(req: ScorePortfolioRequest) -> dict:
    """
    Score a portfolio of carbon credits.
    Returns volume-weighted quality score, CCP-labelled volume %, CORSIA eligible %,
    grade distribution, and per-project results.
    """
    try:
        engine = get_engine()
        portfolio_dicts = [item.dict() for item in req.portfolio]
        return engine.score_portfolio(entity_id=req.entity_id, portfolio=portfolio_dicts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/check-ccp-eligibility")
def check_ccp_eligibility(req: CheckCCPEligibilityRequest) -> dict:
    """
    Check whether a carbon credit standard/methodology/type combination is eligible
    for the ICVCM Core Carbon Principles (CCP) label.
    Returns per-criterion pass/fail/partial results and CORSIA eligibility.
    """
    try:
        engine = get_engine()
        return engine.check_ccp_eligibility(
            standard=req.standard,
            methodology=req.methodology,
            project_type=req.project_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/standards")
def ref_standards() -> dict:
    """Reference: Carbon credit standards (VCS, Gold Standard, CDM, Art 6, CCP, Plan Vivo, ACR, CAR)."""
    try:
        return get_engine().ref_standards()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/icvcm-criteria")
def ref_icvcm_criteria() -> list:
    """Reference: 10 ICVCM Core Carbon Principles criteria with assessment levels."""
    try:
        return get_engine().ref_icvcm_criteria()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/methodologies")
def ref_methodologies() -> dict:
    """Reference: 20 carbon project methodologies by type (REDD+, cookstoves, renewable, soil, blue carbon, DAC etc.)."""
    try:
        return get_engine().ref_methodologies()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/corsia-eligibility")
def ref_corsia_eligibility() -> dict:
    """Reference: CORSIA eligible programmes (2024-2026 cycle) and CCP premium recognition."""
    try:
        return get_engine().ref_corsia_eligibility()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/price-benchmarks")
def ref_price_benchmarks() -> dict:
    """Reference: Carbon credit price benchmarks by type (nature removal, tech removal, avoidance) + CCP premium."""
    try:
        return get_engine().ref_price_benchmarks()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
