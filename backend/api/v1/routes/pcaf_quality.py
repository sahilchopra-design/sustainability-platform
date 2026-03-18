"""
API Routes: PCAF Data Quality Score Engine
============================================
POST /api/v1/pcaf-quality/score-holding        — Score a single holding's data quality (DQS 1-5)
POST /api/v1/pcaf-quality/score-portfolio       — Score full portfolio with DQS distribution + SFDR PAI
POST /api/v1/pcaf-quality/assess-data-quality   — Standalone entity data quality assessment
GET  /api/v1/pcaf-quality/ref/asset-classes     — PCAF 6 asset classes
GET  /api/v1/pcaf-quality/ref/dqs-levels        — DQS 1-5 level definitions
GET  /api/v1/pcaf-quality/ref/quality-dimensions — 5 quality assessment dimensions
GET  /api/v1/pcaf-quality/ref/emission-factors  — Sector emission factors for DQS 4-5 estimation
GET  /api/v1/pcaf-quality/ref/attribution-methods — EVIC, balance-sheet, project, floor-area
GET  /api/v1/pcaf-quality/ref/improvement-paths — DQS improvement roadmap (5→1)
GET  /api/v1/pcaf-quality/ref/cross-framework   — PCAF → SFDR/CSRD/TCFD/ISSB/GRI/EU-Tax/CDP/NZBA
GET  /api/v1/pcaf-quality/ref/benchmarks        — Sector median DQS benchmarks
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.pcaf_quality_engine import PCAFQualityEngine

router = APIRouter(prefix="/api/v1/pcaf-quality", tags=["PCAF Data Quality Scoring"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ScoreHoldingRequest(BaseModel):
    holding_id: str = "H001"
    entity_name: str
    asset_class: str = "listed_equity_corporate_bonds"
    outstanding_amount_eur: float = 1_000_000.0
    reported_emissions: Optional[dict] = None
    revenue_eur: Optional[float] = None
    physical_activity_data: Optional[dict] = None
    data_year: int = 2024
    verification_status: str = "none"


class ScorePortfolioRequest(BaseModel):
    portfolio_id: str = "PF001"
    portfolio_name: str
    reporting_year: int = 2025
    holdings: list[dict] = Field(default_factory=list)


class AssessDataQualityRequest(BaseModel):
    entity_name: str
    reporting_year: int = 2025
    data_inventory: Optional[dict] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/score-holding")
def score_holding(req: ScoreHoldingRequest):
    """Score a single holding's PCAF data quality (DQS 1-5) with financed emissions."""
    engine = PCAFQualityEngine()
    holding = {
        "holding_id": req.holding_id,
        "entity_name": req.entity_name,
        "asset_class": req.asset_class,
        "outstanding_amount_eur": req.outstanding_amount_eur,
        "reported_emissions": req.reported_emissions,
        "revenue_eur": req.revenue_eur,
        "physical_activity_data": req.physical_activity_data,
        "data_year": req.data_year,
        "verification_status": req.verification_status,
    }
    r = engine.score_holding(holding)
    return r.__dict__


@router.post("/score-portfolio")
def score_portfolio(req: ScorePortfolioRequest):
    """Score full portfolio — exposure-weighted DQS, SFDR PAI indicators, improvement roadmap."""
    engine = PCAFQualityEngine()
    portfolio = {
        "portfolio_id": req.portfolio_id,
        "portfolio_name": req.portfolio_name,
        "reporting_year": req.reporting_year,
        "holdings": req.holdings,
    }
    r = engine.score_portfolio(portfolio)
    return r.__dict__


@router.post("/assess-data-quality")
def assess_data_quality(req: AssessDataQualityRequest):
    """Standalone entity data quality assessment across 5 dimensions."""
    engine = PCAFQualityEngine()
    r = engine.assess_data_quality(
        entity_name=req.entity_name,
        reporting_year=req.reporting_year,
        data_inventory=req.data_inventory or {},
    )
    return r.__dict__


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/asset-classes")
def ref_asset_classes():
    """PCAF 6 asset classes with attribution methods."""
    return {"asset_classes": PCAFQualityEngine.get_asset_classes()}


@router.get("/ref/dqs-levels")
def ref_dqs_levels():
    """DQS 1-5 level definitions, data sources, confidence weights."""
    return {"dqs_levels": PCAFQualityEngine.get_dqs_levels()}


@router.get("/ref/quality-dimensions")
def ref_quality_dimensions():
    """5 quality assessment dimensions with weights."""
    return {"quality_dimensions": PCAFQualityEngine.get_quality_dimensions()}


@router.get("/ref/emission-factors")
def ref_emission_factors():
    """Sector emission factors for DQS 4-5 economic activity estimation."""
    return {"emission_factors": PCAFQualityEngine.get_emission_factors()}


@router.get("/ref/attribution-methods")
def ref_attribution_methods():
    """PCAF attribution methods: EVIC, balance-sheet, project, floor-area."""
    return {"attribution_methods": PCAFQualityEngine.get_attribution_methods()}


@router.get("/ref/improvement-paths")
def ref_improvement_paths():
    """DQS improvement roadmap — actions to move from DQS 5→1."""
    return {"improvement_paths": PCAFQualityEngine.get_improvement_paths()}


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """PCAF cross-framework mapping to SFDR/CSRD/TCFD/ISSB/GRI/EU-Tax/CDP/NZBA."""
    return {"cross_framework_map": PCAFQualityEngine.get_cross_framework_map()}


@router.get("/ref/benchmarks")
def ref_benchmarks():
    """Sector median DQS benchmarks (10+ sectors)."""
    return {"benchmarks": PCAFQualityEngine.get_quality_benchmarks()}
