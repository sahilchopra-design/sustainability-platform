"""
API Routes: Basel III/IV Regulatory Capital Engine
=====================================================
POST /api/v1/basel-capital/risk-weight-sa            — Standardised Approach risk weight lookup
POST /api/v1/basel-capital/risk-weight-irb           — IRB risk weight calculation (PD/LGD/M)
POST /api/v1/basel-capital/capital-requirement       — Full capital requirement calculation
POST /api/v1/basel-capital/liquidity                 — LCR + NSFR liquidity assessment
POST /api/v1/basel-capital/capital-adequacy          — Full capital adequacy dashboard
GET  /api/v1/basel-capital/ref/exposure-classes      — CRR Article 112 exposure classes
GET  /api/v1/basel-capital/ref/sa-risk-weights       — Standardised Approach risk weight tables
GET  /api/v1/basel-capital/ref/irb-parameters        — IRB formula parameters
GET  /api/v1/basel-capital/ref/capital-requirements  — Minimum capital ratios
GET  /api/v1/basel-capital/ref/capital-buffers       — Buffer requirements (CCB, CCyB, G-SIB, D-SIB)
GET  /api/v1/basel-capital/ref/lcr-parameters        — LCR HQLA / outflow parameters
GET  /api/v1/basel-capital/ref/nsfr-parameters       — NSFR ASF / RSF factors
GET  /api/v1/basel-capital/ref/climate-adjustments   — Climate risk capital add-ons (EBA GL/2022/02)
GET  /api/v1/basel-capital/ref/regulatory-frameworks — CRR/CRD/Basel III references
GET  /api/v1/basel-capital/ref/operational-risk      — SMA operational risk parameters
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.basel_capital_engine import BaselCapitalEngine

router = APIRouter(prefix="/api/v1/basel-capital", tags=["Basel III/IV Regulatory Capital"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SAWeightRequest(BaseModel):
    exposure_class: str = "corporates"
    credit_quality_step: int = 0
    secured_by_property: Optional[str] = None


class IRBWeightRequest(BaseModel):
    pd: float = 0.02
    lgd: float = 0.45
    maturity: float = 2.5
    exposure_class: str = "corporates"


class CapitalRequirementRequest(BaseModel):
    entity_name: str
    reporting_date: str = "2025-12-31"
    exposures: list[dict] = Field(default_factory=list)
    capital: dict = Field(default_factory=dict)
    approach: str = "standardised"
    climate_adjusted: bool = True
    buffers: Optional[dict] = None


class LiquidityRequest(BaseModel):
    entity_name: str
    reporting_date: str = "2025-12-31"
    assets: dict = Field(default_factory=dict)
    liabilities: dict = Field(default_factory=dict)


class CapitalAdequacyRequest(BaseModel):
    entity_name: str
    reporting_date: str = "2025-12-31"
    exposures: list[dict] = Field(default_factory=list)
    capital: dict = Field(default_factory=dict)
    assets: dict = Field(default_factory=dict)
    liabilities: dict = Field(default_factory=dict)
    approach: str = "standardised"
    climate_scenarios: Optional[dict] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/risk-weight-sa")
def risk_weight_sa(req: SAWeightRequest):
    """Standardised Approach risk weight lookup per CRR Article 114-134."""
    engine = BaselCapitalEngine()
    rw = engine.calculate_sa_risk_weight(
        exposure_class=req.exposure_class,
        credit_quality_step=req.credit_quality_step,
        secured_by_property=req.secured_by_property,
    )
    return {"exposure_class": req.exposure_class, "credit_quality_step": req.credit_quality_step,
            "risk_weight": rw, "risk_weight_pct": round(rw * 100, 2)}


@router.post("/risk-weight-irb")
def risk_weight_irb(req: IRBWeightRequest):
    """IRB risk weight calculation per CRR Article 153 — PD/LGD/M → K → RW."""
    engine = BaselCapitalEngine()
    rw = engine.calculate_irb_risk_weight(
        pd=req.pd, lgd=req.lgd, maturity=req.maturity,
        exposure_class=req.exposure_class,
    )
    return {"pd": req.pd, "lgd": req.lgd, "maturity": req.maturity,
            "risk_weight": rw, "risk_weight_pct": round(rw * 100, 2)}


@router.post("/capital-requirement")
def capital_requirement(req: CapitalRequirementRequest):
    """Full capital requirement — RWA, capital ratios, regulatory breaches, recommendations."""
    engine = BaselCapitalEngine()
    r = engine.calculate_capital_requirement(
        entity_name=req.entity_name,
        reporting_date=req.reporting_date,
        exposures=req.exposures,
        capital=req.capital,
        approach=req.approach,
        climate_adjusted=req.climate_adjusted,
        buffers=req.buffers,
    )
    return r.__dict__


@router.post("/liquidity")
def liquidity(req: LiquidityRequest):
    """LCR + NSFR liquidity assessment with HQLA composition + stress scenarios."""
    engine = BaselCapitalEngine()
    r = engine.calculate_liquidity(
        entity_name=req.entity_name,
        reporting_date=req.reporting_date,
        assets=req.assets,
        liabilities=req.liabilities,
    )
    return r.__dict__


@router.post("/capital-adequacy")
def capital_adequacy(req: CapitalAdequacyRequest):
    """Full capital adequacy dashboard — capital + liquidity + climate stress + BCBS 239."""
    engine = BaselCapitalEngine()
    r = engine.run_capital_adequacy(
        entity_name=req.entity_name,
        reporting_date=req.reporting_date,
        exposures=req.exposures,
        capital=req.capital,
        assets=req.assets,
        liabilities=req.liabilities,
        approach=req.approach,
        climate_scenarios=req.climate_scenarios,
    )
    # Flatten nested dataclasses
    result = r.__dict__.copy()
    if hasattr(r.capital_requirement, "__dict__"):
        result["capital_requirement"] = r.capital_requirement.__dict__
    if hasattr(r.liquidity, "__dict__"):
        result["liquidity"] = r.liquidity.__dict__
    return result


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/exposure-classes")
def ref_exposure_classes():
    """CRR Article 112 exposure classes with standard risk weights."""
    return {"exposure_classes": BaselCapitalEngine.get_exposure_classes()}


@router.get("/ref/sa-risk-weights")
def ref_sa_risk_weights():
    """Standardised Approach risk weight tables by CQS and exposure class."""
    return {"sa_risk_weights": BaselCapitalEngine.get_sa_risk_weights()}


@router.get("/ref/irb-parameters")
def ref_irb_parameters():
    """IRB formula parameters (asset correlation, maturity adjustment, K formula)."""
    return {"irb_parameters": BaselCapitalEngine.get_irb_parameters()}


@router.get("/ref/capital-requirements")
def ref_capital_requirements():
    """Minimum capital ratios (CET1, Tier 1, Total, Leverage)."""
    return {"capital_requirements": BaselCapitalEngine.get_capital_requirements()}


@router.get("/ref/capital-buffers")
def ref_capital_buffers():
    """Buffer requirements — CCB, CCyB, G-SIB/D-SIB, systemic risk."""
    return {"capital_buffers": BaselCapitalEngine.get_capital_buffers()}


@router.get("/ref/lcr-parameters")
def ref_lcr_parameters():
    """LCR HQLA levels, haircuts, outflow/inflow rates."""
    return {"lcr_parameters": BaselCapitalEngine.get_lcr_parameters()}


@router.get("/ref/nsfr-parameters")
def ref_nsfr_parameters():
    """NSFR Available/Required Stable Funding factors."""
    return {"nsfr_parameters": BaselCapitalEngine.get_nsfr_parameters()}


@router.get("/ref/climate-adjustments")
def ref_climate_adjustments():
    """Climate risk capital add-ons per EBA GL/2022/02."""
    return {"climate_adjustments": BaselCapitalEngine.get_climate_adjustments()}


@router.get("/ref/regulatory-frameworks")
def ref_regulatory_frameworks():
    """Regulatory frameworks — CRR, CRD, Basel III, EBA GL, BCBS 239."""
    return {"regulatory_frameworks": BaselCapitalEngine.get_regulatory_frameworks()}


@router.get("/ref/operational-risk")
def ref_operational_risk():
    """SMA operational risk parameters — BIC, ILM, capital formula."""
    return {"operational_risk": BaselCapitalEngine.get_operational_risk_parameters()}
