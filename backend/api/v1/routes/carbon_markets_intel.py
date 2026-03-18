"""
API Routes: Carbon Markets Intelligence — E46
==============================================
POST /api/v1/carbon-markets-intel/vcmi-claim        — VCMI Claims Code eligibility
POST /api/v1/carbon-markets-intel/icvcm-ccp         — ICVCM CCP assessment
POST /api/v1/carbon-markets-intel/corsia-check      — CORSIA Phase 2 eligibility
POST /api/v1/carbon-markets-intel/article6          — Article 6.2/6.4 assessment
POST /api/v1/carbon-markets-intel/credit-pricing    — Carbon credit pricing model
POST /api/v1/carbon-markets-intel/portfolio-analysis — Full portfolio analytics
POST /api/v1/carbon-markets-intel/full-assessment   — Consolidated assessment
GET  /api/v1/carbon-markets-intel/ref/vcmi-criteria        — VCMI claim level criteria
GET  /api/v1/carbon-markets-intel/ref/icvcm-ccps           — 10 CCPs detail
GET  /api/v1/carbon-markets-intel/ref/corsia-schemes       — Approved CORSIA schemes
GET  /api/v1/carbon-markets-intel/ref/price-benchmarks     — VCM price benchmarks
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

try:
    from services.carbon_markets_intel_engine import get_engine
    from services.carbon_markets_intel_engine import (
        VCMI_CLAIMS_CODE,
        ICVCM_10_CCPS,
        CORSIA_PHASE2_ELIGIBLE_SCHEMES,
        ARTICLE6_BILATERAL_AGREEMENTS,
        CARBON_PRICE_BENCHMARKS,
        CO_BENEFIT_PREMIUMS,
        REGISTRY_METHODOLOGY_TYPES,
    )
    _engine = get_engine()
except Exception:
    _engine = None
    VCMI_CLAIMS_CODE = {}
    ICVCM_10_CCPS = []
    CORSIA_PHASE2_ELIGIBLE_SCHEMES = []
    ARTICLE6_BILATERAL_AGREEMENTS = {}
    CARBON_PRICE_BENCHMARKS = {}
    CO_BENEFIT_PREMIUMS = {}
    REGISTRY_METHODOLOGY_TYPES = {}

router = APIRouter(prefix="/api/v1/carbon-markets-intel", tags=["Carbon Markets Intelligence"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class VCMIClaimRequest(BaseModel):
    entity_id: str
    abatement_pct: float = Field(default=50.0, ge=0, le=100)
    sbti_status: str = "committed"
    scope_coverage: list[str] = Field(default_factory=lambda: ["scope1", "scope2"])
    mitigation_contribution_pct: float = Field(default=0.08, ge=0, le=1)

    class Config:
        extra = "allow"


class ICVCMCCPRequest(BaseModel):
    entity_id: str
    credit_portfolio: list[dict] = Field(default_factory=list)

    class Config:
        extra = "allow"


class CORSIACheckRequest(BaseModel):
    entity_id: str
    credit_records: list[dict] = Field(default_factory=list)

    class Config:
        extra = "allow"


class Article6Request(BaseModel):
    entity_id: str
    credit_records: list[dict] = Field(default_factory=list)
    host_country: str = "GH"

    class Config:
        extra = "allow"


class CreditPricingRequest(BaseModel):
    entity_id: str
    project_type: str = "nature_based"
    vintage_year: int = 2022
    icvcm_pass: bool = True
    co_benefits: list[str] = Field(default_factory=list)
    registry: str = "Verra VCS"

    class Config:
        extra = "allow"


class PortfolioAnalysisRequest(BaseModel):
    entity_id: str
    credit_portfolio: list[dict] = Field(default_factory=list)

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

@router.post("/vcmi-claim")
def vcmi_claim(req: VCMIClaimRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.screen_vcmi_claim(
        entity_id=req.entity_id,
        abatement_pct=req.abatement_pct,
        sbti_status=req.sbti_status,
        scope_coverage=req.scope_coverage,
        mitigation_contribution_pct=req.mitigation_contribution_pct,
    )
    return {"status": "success", "data": result}


@router.post("/icvcm-ccp")
def icvcm_ccp(req: ICVCMCCPRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_icvcm_ccps(
        entity_id=req.entity_id,
        credit_portfolio=req.credit_portfolio,
    )
    return {"status": "success", "data": result}


@router.post("/corsia-check")
def corsia_check(req: CORSIACheckRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.check_corsia_eligibility(
        entity_id=req.entity_id,
        credit_records=req.credit_records,
    )
    return {"status": "success", "data": result}


@router.post("/article6")
def article6(req: Article6Request):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.assess_article6(
        entity_id=req.entity_id,
        credit_records=req.credit_records,
        host_country=req.host_country,
    )
    return {"status": "success", "data": result}


@router.post("/credit-pricing")
def credit_pricing(req: CreditPricingRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.price_credits(
        entity_id=req.entity_id,
        project_type=req.project_type,
        vintage_year=req.vintage_year,
        icvcm_pass=req.icvcm_pass,
        co_benefits=req.co_benefits,
        registry=req.registry,
    )
    return {"status": "success", "data": result}


@router.post("/portfolio-analysis")
def portfolio_analysis(req: PortfolioAnalysisRequest):
    if _engine is None:
        return {"status": "success", "data": {"error": "engine unavailable", "entity_id": req.entity_id}}
    result = _engine.analyse_portfolio(
        entity_id=req.entity_id,
        credit_portfolio=req.credit_portfolio,
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

@router.get("/ref/vcmi-criteria")
def ref_vcmi_criteria():
    return {
        "status": "success",
        "data": {
            "standard": "VCMI Claims Code of Practice v1.0 (2023)",
            "claim_levels": VCMI_CLAIMS_CODE,
            "guidance": "Claims must be paired with near-term SBTi-validated targets and public disclosure",
            "url": "https://vcmintegrity.org/vcmi-claims-code-of-practice/",
        },
    }


@router.get("/ref/icvcm-ccps")
def ref_icvcm_ccps():
    return {
        "status": "success",
        "data": {
            "standard": "ICVCM Core Carbon Principles v2.0 (2023)",
            "total_ccps": len(ICVCM_10_CCPS),
            "ccps": ICVCM_10_CCPS,
            "categories": {
                "governance": "CCPs 1-4: Programme governance, tracking, transparency, verification",
                "emissions_impact": "CCPs 5-8: Additionality, permanence, quantification, no double counting",
                "sustainable_dev": "CCPs 9-10: SD benefits, net zero contribution",
            },
            "url": "https://icvcm.org/the-core-carbon-principles/",
        },
    }


@router.get("/ref/corsia-schemes")
def ref_corsia_schemes():
    return {
        "status": "success",
        "data": {
            "program": "CORSIA Phase 2 (2024-2026) — ICAO Carbon Offsetting and Reduction Scheme",
            "approved_schemes": CORSIA_PHASE2_ELIGIBLE_SCHEMES,
            "approved_count": len(CORSIA_PHASE2_ELIGIBLE_SCHEMES),
            "eligibility_requirements": [
                "Scheme on ICAO CORSIA approved list",
                "Vintage year 2016 or later",
                "Corresponding adjustment confirmed by host country",
                "No double counting with NDC accounting",
            ],
            "phase_2_dates": "2024-01-01 to 2026-12-31",
        },
    }


@router.get("/ref/price-benchmarks")
def ref_price_benchmarks():
    return {
        "status": "success",
        "data": {
            "benchmarks": CARBON_PRICE_BENCHMARKS,
            "co_benefit_premiums_pct": CO_BENEFIT_PREMIUMS,
            "registry_methodologies": REGISTRY_METHODOLOGY_TYPES,
            "currency": "USD/tCO2e",
            "note": "Indicative benchmark prices. Actual transaction prices depend on buyer demand, co-benefits, project vintage, and registry.",
            "source": "Ecosystem Marketplace, MSCI Carbon Markets, Carbon Direct analysis (2024)",
            "bilateral_agreements_tracked": len(ARTICLE6_BILATERAL_AGREEMENTS),
        },
    }
