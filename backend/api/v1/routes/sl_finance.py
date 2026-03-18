"""
API Routes: Sustainability-Linked Finance Engine (E17)
======================================================
POST /api/v1/sl-finance/assess              — Full SLB/SLL principles compliance assessment
POST /api/v1/sl-finance/assess/batch        — Batch: multiple instruments
POST /api/v1/sl-finance/validate-kpi        — Validate a single KPI against SMART criteria
POST /api/v1/sl-finance/calibrate-spt       — Calibrate SPT target value and ambition
GET  /api/v1/sl-finance/ref/kpi-library     — KPI_LIBRARY reference
GET  /api/v1/sl-finance/ref/icma-components — ICMA SLB 5-component framework
GET  /api/v1/sl-finance/ref/lma-components  — LMA SLL 5-component framework
GET  /api/v1/sl-finance/ref/cross-framework — Cross-framework mapping
GET  /api/v1/sl-finance/ref/coupon-guidance — Coupon step-up guidance
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.sl_finance_engine import (
    SLFinanceEngine,
    KPIInput,
    SLBInput,
    KPI_LIBRARY,
    ICMA_SLB_COMPONENTS,
    LMA_SLL_COMPONENTS,
    SL_CROSS_FRAMEWORK,
    COUPON_STEP_UP_GUIDANCE,
)

router = APIRouter(
    prefix="/api/v1/sl-finance",
    tags=["Sustainability-Linked Finance — SLB/SLL Principles"],
)

_ENGINE = SLFinanceEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class KPIInputModel(BaseModel):
    kpi_id: str = Field(..., description="KPI identifier — use /ref/kpi-library for recognised IDs")
    kpi_name: str = Field(..., description="Human-readable KPI name")
    baseline_value: float = Field(..., description="KPI value at baseline year")
    baseline_year: int = Field(..., description="Baseline measurement year")
    target_value: float = Field(..., description="SPT target value")
    target_year: int = Field(..., description="Year by which SPT must be achieved")
    current_value: float = Field(0.0, description="Latest measured KPI value")
    unit: str = Field("", description="Measurement unit (e.g. 'tCO2e/revenue', '%')")
    external_verified: bool = Field(False, description="KPI performance independently verified")
    verification_provider: str = Field("", description="Name of external verification provider")


class SLBInputModel(BaseModel):
    instrument_id: str
    issuer_name: str
    instrument_type: str = Field(
        "slb", description="slb (Sustainability-Linked Bond) | sll (Sustainability-Linked Loan)"
    )
    tenor_years: int = Field(5, ge=1, le=30, description="Instrument tenor in years")
    issuance_amount: float = Field(0.0, description="Issuance/facility amount")
    currency: str = Field("EUR", description="ISO 4217 currency code")
    kpis: List[KPIInputModel] = Field(default_factory=list, description="KPIs with SPT definitions")
    has_spo: bool = Field(False, description="Second Party Opinion obtained at issuance")
    spo_provider: str = Field("", description="SPO provider name")
    coupon_step_up_bps: float = Field(
        25.0, ge=0.0, description="Coupon/margin step-up in basis points if SPTs missed"
    )
    has_annual_reporting: bool = Field(False, description="Annual KPI performance report published")
    has_annual_verification: bool = Field(False, description="Annual external KPI verification in place")


class CalibrateSPTModel(BaseModel):
    kpi_id: str = Field(..., description="KPI identifier from KPI library")
    baseline: float = Field(..., description="Baseline value at baseline_year")
    target_pct_improvement: float = Field(
        ..., gt=0, description="Desired improvement in % (e.g. 30 for 30% reduction)"
    )
    baseline_year: int = Field(..., description="Baseline measurement year")
    target_year: int = Field(..., description="Target achievement year")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_kpi_input(m: KPIInputModel) -> KPIInput:
    return KPIInput(
        kpi_id=m.kpi_id,
        kpi_name=m.kpi_name,
        baseline_value=m.baseline_value,
        baseline_year=m.baseline_year,
        target_value=m.target_value,
        target_year=m.target_year,
        current_value=m.current_value,
        unit=m.unit,
        external_verified=m.external_verified,
        verification_provider=m.verification_provider,
    )


def _to_slb_input(body: SLBInputModel) -> SLBInput:
    return SLBInput(
        instrument_id=body.instrument_id,
        issuer_name=body.issuer_name,
        instrument_type=body.instrument_type,
        tenor_years=body.tenor_years,
        issuance_amount=body.issuance_amount,
        currency=body.currency,
        kpis=[_to_kpi_input(k) for k in body.kpis],
        has_spo=body.has_spo,
        spo_provider=body.spo_provider,
        coupon_step_up_bps=body.coupon_step_up_bps,
        has_annual_reporting=body.has_annual_reporting,
        has_annual_verification=body.has_annual_verification,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Assess SLB/SLL principles compliance")
def assess(body: SLBInputModel) -> Dict[str, Any]:
    """
    Perform a full compliance assessment against ICMA SLB Principles 2023
    (for SLBs) or LMA/APLMA/LSTA SLL Principles 2023 (for SLLs).

    Evaluates all 5 components, SMART KPI criteria, SPT ambition,
    step-up trigger status, and SPO requirement.
    """
    result = _ENGINE.assess(_to_slb_input(body))
    return result.dict()


@router.post("/assess/batch", summary="Batch assess multiple SLB/SLL instruments")
def assess_batch(body: List[SLBInputModel]) -> List[Dict[str, Any]]:
    """
    Assess a portfolio of sustainability-linked instruments in a single call.
    Returns one result per instrument in input order.
    """
    return [_ENGINE.assess(_to_slb_input(b)).dict() for b in body]


@router.post("/validate-kpi", summary="Validate a single KPI against SMART criteria")
def validate_kpi(body: KPIInputModel) -> Dict[str, Any]:
    """
    Validate a single KPI definition: SMART score, SPT trajectory,
    on-track status, and ambition rating (high/medium/low/insufficient).
    """
    kpi = _to_kpi_input(body)
    result = _ENGINE.validate_kpi(kpi)
    return result.dict()


@router.post("/calibrate-spt", summary="Calibrate SPT target value and ambition")
def calibrate_spt(body: CalibrateSPTModel) -> Dict[str, Any]:
    """
    Calculate the target value for a given KPI and improvement percentage,
    compare against sector benchmark, and return ambition rating.
    """
    return _ENGINE.calibrate_spt(
        kpi_id=body.kpi_id,
        baseline=body.baseline,
        target_pct_improvement=body.target_pct_improvement,
        baseline_year=body.baseline_year,
        target_year=body.target_year,
    )


@router.get("/ref/kpi-library", summary="Recognised ICMA/LMA KPI library")
def ref_kpi_library() -> Dict[str, Any]:
    """Return KPI_LIBRARY — 10 widely-recognised KPIs across environmental,
    social, and governance categories with benchmark sources and typical SPT
    improvement percentages."""
    return _ENGINE.get_kpi_library()


@router.get("/ref/icma-components", summary="ICMA SLB 5-component framework")
def ref_icma_components() -> List[Dict[str, Any]]:
    """Return ICMA SLB Principles 2023 — 5 components (KPI Selection,
    SPT Calibration, Bond Characteristics, Reporting, Verification)."""
    return _ENGINE.get_icma_components()


@router.get("/ref/lma-components", summary="LMA SLL 5-component framework")
def ref_lma_components() -> List[Dict[str, Any]]:
    """Return LMA/APLMA/LSTA SLL Principles 2023 — 5 components
    (Sustainability Strategy, SPTs, Documentation, Reporting, Verification)."""
    return _ENGINE.get_lma_components()


@router.get("/ref/cross-framework", summary="Cross-framework mapping (CSRD, SBTi, TCFD, GRI, EU Taxonomy)")
def ref_cross_framework() -> Dict[str, str]:
    """Return cross-framework linkage between SLB/SLL KPI selection and
    CSRD ESRS, SBTi pathways, TCFD scenario analysis, GRI standards, and
    EU Taxonomy."""
    return _ENGINE.get_cross_framework()


@router.get("/ref/coupon-guidance", summary="ICMA coupon step-up guidance")
def ref_coupon_guidance() -> Dict[str, Any]:
    """Return COUPON_STEP_UP_GUIDANCE — typical step-up ranges (12.5–25 bps),
    trigger mechanisms, cure period guidance, and use-of-step-up proceeds."""
    return _ENGINE.get_coupon_guidance()
