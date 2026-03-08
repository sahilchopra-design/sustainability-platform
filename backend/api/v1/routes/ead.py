"""
EAD (Exposure at Default) API Routes

Endpoints for EAD calculation using Basel III/IV Credit Conversion Factors.
Integrates with the ECL engine for full IFRS 9 provisioning workflow.

Router prefix: /api/v1/ead
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from services.ead_calculator import (
    EADCalculator,
    EADInput,
    EADResult,
    EADBatchResult,
    REGULATORY_CCF,
    SHORT_MATURITY_CCF_OVERRIDES,
    SACCR_ALPHA,
    MATURITY_CAPS,
    get_ccf,
    get_maturity_adjustment,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ead", tags=["EAD Calculator"])


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------------------------------------


class EADCalculationRequest(BaseModel):
    """Single exposure EAD calculation request."""
    outstanding_balance: float = Field(..., ge=0, description="Current drawn amount")
    total_commitment: float = Field(..., ge=0, description="Total committed facility amount")
    facility_type: str = Field(
        ...,
        description="Facility type: TERM_LOAN, REVOLVING_CREDIT, UNDRAWN_COMMITMENT, "
                    "UNCONDITIONALLY_CANCELLABLE, TRADE_LETTER_OF_CREDIT, "
                    "STANDBY_LETTER_OF_CREDIT, GUARANTEE, FINANCIAL_GUARANTEE, "
                    "NOTE_ISSUANCE_FACILITY, REPO_STYLE, OTC_DERIVATIVE, "
                    "MARGIN_LENDING, TRANSACTION_CONTINGENCY"
    )
    asset_class: str = Field(
        ...,
        description="Basel asset class: CORPORATE, SME, RETAIL_REVOLVING, "
                    "RETAIL_MORTGAGE, RETAIL_OTHER, SOVEREIGN, BANK, "
                    "SPECIALISED_LENDING, EQUITY"
    )
    remaining_maturity_years: float = Field(2.5, ge=0, le=50, description="Remaining maturity in years")
    sector: str = Field("Corporate", description="Industry sector for climate stress")
    is_short_maturity: bool = Field(False, description="True if original maturity < 1 year")
    derivative_notional: float = Field(0.0, ge=0, description="OTC derivative notional amount")
    derivative_asset_class: str = Field(
        "interest_rate",
        description="SA-CCR derivative class: interest_rate, fx, credit, equity, commodity"
    )
    derivative_maturity_years: float = Field(0.0, ge=0, description="Derivative remaining maturity")
    guarantee_amount: float = Field(0.0, ge=0, description="Guarantee/LC amount")
    apply_climate_stress: bool = Field(True, description="Apply climate drawdown stress overlay")
    climate_scenario: str = Field(
        "base",
        description="Climate scenario: optimistic, base, adverse, severe"
    )
    pd: float = Field(0.01, ge=0, le=1, description="PD for maturity adjustment b(PD) formula")
    use_pd_maturity_adjustment: bool = Field(
        False,
        description="Use full Basel III b(PD) maturity formula instead of simplified"
    )


class EADCalculationResponse(BaseModel):
    """Single exposure EAD calculation response."""
    facility_type: str
    asset_class: str
    outstanding_balance: float
    total_commitment: float
    undrawn_amount: float
    ccf_applied: float
    effective_maturity_years: float
    maturity_adjustment_factor: float
    ead_pre_climate: float
    ead_post_climate: float
    climate_drawdown_stress_pct: float
    contribution_breakdown: Dict[str, float]
    regulatory_ead: float
    methodology_notes: List[str]


class EADBatchRequest(BaseModel):
    """Batch EAD calculation request for a loan book."""
    exposures: List[EADCalculationRequest] = Field(
        ..., min_length=1, max_length=10000,
        description="List of exposures to calculate EAD for"
    )
    climate_scenario: str = Field("base", description="Climate scenario for all exposures")
    apply_climate_stress: bool = Field(True, description="Apply climate drawdown stress")


class EADBatchResponse(BaseModel):
    """Batch EAD calculation response."""
    total_ead: float
    total_on_balance: float
    total_off_balance_ead: float
    weighted_avg_ccf: float
    count: int
    by_asset_class: Dict[str, float]
    by_facility_type: Dict[str, float]
    results: List[EADCalculationResponse]


class CCFTableResponse(BaseModel):
    """CCF lookup table response."""
    ccf_table: Dict[str, Dict[str, float]]
    facility_types: List[str]
    asset_classes: List[str]
    short_maturity_overrides: Dict[str, float]


class CCFLookupResponse(BaseModel):
    """Single CCF lookup response."""
    asset_class: str
    facility_type: str
    ccf: float
    saccr_alpha: float = SACCR_ALPHA
    maturity_caps: Dict[str, float] = Field(default_factory=lambda: dict(MATURITY_CAPS))


class ClimateStressResponse(BaseModel):
    """Climate stress factors response."""
    scenario: str
    scenario_multiplier: float
    available_scenarios: List[str]
    sector_stress_factors: Dict[str, float]


# ---------------------------------------------------------------------------
# HELPER
# ---------------------------------------------------------------------------


def _result_to_response(result: EADResult) -> EADCalculationResponse:
    """Convert EADResult dataclass to response model."""
    cb = result.contribution_breakdown
    return EADCalculationResponse(
        facility_type=result.facility_type,
        asset_class=result.asset_class,
        outstanding_balance=result.outstanding_balance,
        total_commitment=result.total_commitment,
        undrawn_amount=result.undrawn_amount,
        ccf_applied=result.ccf_applied,
        effective_maturity_years=result.effective_maturity_years,
        maturity_adjustment_factor=result.maturity_adjustment_factor,
        ead_pre_climate=result.ead_pre_climate,
        ead_post_climate=result.ead_post_climate,
        climate_drawdown_stress_pct=result.climate_drawdown_stress_pct,
        contribution_breakdown={
            "on_balance_sheet": cb.on_balance_sheet,
            "undrawn_commitment_ead": cb.undrawn_commitment_ead,
            "guarantee_exposure": cb.guarantee_exposure,
            "derivative_addon": cb.derivative_addon,
            "maturity_adjustment": cb.maturity_adjustment,
            "climate_ead_uplift": cb.climate_ead_uplift,
            "total_ead": cb.total_ead,
        },
        regulatory_ead=result.regulatory_ead,
        methodology_notes=result.methodology_notes,
    )


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------


@router.post("/calculate", response_model=EADCalculationResponse)
async def calculate_ead(request: EADCalculationRequest) -> EADCalculationResponse:
    """
    Calculate EAD for a single exposure.

    Applies Basel III/IV CCF based on facility type and asset class,
    with optional climate drawdown stress overlay and PD-based maturity
    adjustment per Basel III Art. 153(1).
    """
    try:
        calc = EADCalculator(climate_scenario=request.climate_scenario)
        result = calc.calculate(
            outstanding_balance=request.outstanding_balance,
            total_commitment=request.total_commitment,
            facility_type=request.facility_type,
            asset_class=request.asset_class,
            remaining_maturity_years=request.remaining_maturity_years,
            sector=request.sector,
            is_short_maturity=request.is_short_maturity,
            derivative_notional=request.derivative_notional,
            derivative_asset_class=request.derivative_asset_class,
            derivative_maturity_years=request.derivative_maturity_years,
            guarantee_amount=request.guarantee_amount,
            apply_climate_stress=request.apply_climate_stress,
            pd=request.pd,
            use_pd_maturity_adjustment=request.use_pd_maturity_adjustment,
        )
        return _result_to_response(result)

    except Exception as e:
        logger.error("EAD calculation failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"EAD calculation failed: {str(e)}")


@router.post("/calculate-batch", response_model=EADBatchResponse)
async def calculate_ead_batch(request: EADBatchRequest) -> EADBatchResponse:
    """
    Batch EAD calculation for a loan book.

    Processes up to 10,000 exposures and returns aggregated stats
    plus individual results.
    """
    try:
        calc = EADCalculator(climate_scenario=request.climate_scenario)

        exposure_dicts = []
        for exp in request.exposures:
            exposure_dicts.append({
                "outstanding_balance": exp.outstanding_balance,
                "total_commitment": exp.total_commitment,
                "facility_type": exp.facility_type,
                "asset_class": exp.asset_class,
                "remaining_maturity_years": exp.remaining_maturity_years,
                "sector": exp.sector,
                "is_short_maturity": exp.is_short_maturity,
                "derivative_notional": exp.derivative_notional,
                "derivative_asset_class": exp.derivative_asset_class,
                "derivative_maturity_years": exp.derivative_maturity_years,
                "guarantee_amount": exp.guarantee_amount,
                "pd": exp.pd,
                "use_pd_maturity_adjustment": exp.use_pd_maturity_adjustment,
            })

        batch_result = calc.calculate_batch(
            exposures=exposure_dicts,
            apply_climate_stress=request.apply_climate_stress,
        )

        return EADBatchResponse(
            total_ead=batch_result.total_ead,
            total_on_balance=batch_result.total_on_balance,
            total_off_balance_ead=batch_result.total_off_balance_ead,
            weighted_avg_ccf=batch_result.weighted_avg_ccf,
            count=batch_result.count,
            by_asset_class=batch_result.by_asset_class,
            by_facility_type=batch_result.by_facility_type,
            results=[_result_to_response(r) for r in batch_result.results],
        )

    except Exception as e:
        logger.error("Batch EAD calculation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Batch EAD calculation failed: {str(e)}"
        )


@router.get("/ccf-matrix", response_model=CCFTableResponse)
async def get_ccf_matrix() -> CCFTableResponse:
    """
    Return the full Basel III/IV CCF lookup table.

    Shows CCF values by facility type and asset class, plus
    short-maturity overrides.
    """
    return CCFTableResponse(
        ccf_table=EADCalculator.get_ccf_table(),
        facility_types=EADCalculator.get_supported_facility_types(),
        asset_classes=EADCalculator.get_supported_asset_classes(),
        short_maturity_overrides=dict(SHORT_MATURITY_CCF_OVERRIDES),
    )


@router.get("/ccf/{asset_class}/{facility_type}", response_model=CCFLookupResponse)
async def get_specific_ccf(
    asset_class: str = Path(..., description="Basel asset class (e.g. CORPORATE)"),
    facility_type: str = Path(..., description="Facility type (e.g. UNDRAWN_COMMITMENT)"),
) -> CCFLookupResponse:
    """
    Return the CCF for a specific asset class and facility type combination.

    Falls back to CORPORATE for the same facility type if the exact combination
    is not found, then to 1.00 (conservative).
    """
    ccf_value = get_ccf(asset_class=asset_class, facility_type=facility_type)
    return CCFLookupResponse(
        asset_class=asset_class,
        facility_type=facility_type,
        ccf=ccf_value,
    )


@router.get("/climate-stress", response_model=ClimateStressResponse)
async def get_climate_stress_factors(
    scenario: str = Query("base", description="Climate scenario")
) -> ClimateStressResponse:
    """
    Return climate drawdown stress factors by sector and scenario.
    """
    calc = EADCalculator(climate_scenario=scenario)
    info = calc.get_scenario_info()

    # Apply scenario multiplier to base factors
    multiplier = info["scenario_multiplier"]
    base_factors = EADCalculator.get_climate_stress_factors()
    scaled_factors = {
        k: round(v * multiplier, 4) for k, v in base_factors.items()
    }

    return ClimateStressResponse(
        scenario=info["climate_scenario"],
        scenario_multiplier=info["scenario_multiplier"],
        available_scenarios=info["available_scenarios"],
        sector_stress_factors=scaled_factors,
    )


@router.get("/facility-types")
async def list_facility_types() -> Dict[str, Any]:
    """List all supported facility types with descriptions."""
    descriptions = {
        "TERM_LOAN": "Fully drawn term loan (on-balance-sheet, CCF=100%)",
        "REVOLVING_CREDIT": "Revolving credit facility with drawn and undrawn portions",
        "UNDRAWN_COMMITMENT": "Committed but undrawn facility (> 1 year maturity)",
        "UNCONDITIONALLY_CANCELLABLE": "Revocable at any time without notice (Basel IV: 10%)",
        "TRADE_LETTER_OF_CREDIT": "Self-liquidating trade letters of credit",
        "STANDBY_LETTER_OF_CREDIT": "Performance or financial standby LCs",
        "GUARANTEE": "Direct credit substitute guarantees",
        "FINANCIAL_GUARANTEE": "Financial guarantee contracts per IFRS 9",
        "NOTE_ISSUANCE_FACILITY": "Note issuance facilities (NIFs) and RUFs",
        "REPO_STYLE": "Repo, reverse repo, securities lending",
        "OTC_DERIVATIVE": "OTC derivative exposure (uses SA-CCR)",
        "MARGIN_LENDING": "Margin lending facilities",
        "TRANSACTION_CONTINGENCY": "Transaction-related contingent items",
    }
    return {
        "facility_types": EADCalculator.get_supported_facility_types(),
        "descriptions": descriptions,
    }


@router.get("/asset-classes")
async def list_asset_classes() -> Dict[str, Any]:
    """List all supported Basel asset classes with descriptions."""
    descriptions = {
        "CORPORATE": "Corporate loans (CRR Art. 122)",
        "SME": "Small/medium enterprise loans (CRR Art. 153(4))",
        "RETAIL_REVOLVING": "Qualifying revolving retail (credit cards, overdrafts)",
        "RETAIL_MORTGAGE": "Residential mortgage loans (CRR Art. 124-125)",
        "RETAIL_OTHER": "Other retail exposures",
        "SOVEREIGN": "Sovereign and central bank exposures (CRR Art. 114)",
        "BANK": "Interbank exposures (CRR Art. 120-121)",
        "SPECIALISED_LENDING": "Project finance, object finance, commodity finance (CRR Art. 153(5))",
        "EQUITY": "Equity exposures (CRR Art. 133)",
    }
    return {
        "asset_classes": EADCalculator.get_supported_asset_classes(),
        "descriptions": descriptions,
    }
