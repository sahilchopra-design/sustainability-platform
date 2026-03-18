"""
API Routes: Financed Emissions Temperature Alignment Engine (E103)
==================================================================
POST /api/v1/temperature-alignment/assess            — Full portfolio temperature alignment
POST /api/v1/temperature-alignment/waci              — WACI calculation
POST /api/v1/temperature-alignment/itr               — ITR from WACI
POST /api/v1/temperature-alignment/sbti-fi           — SBTi FI criteria assessment
POST /api/v1/temperature-alignment/sector-alignment  — Single sector PACTA alignment
GET  /api/v1/temperature-alignment/ref/sbti-fi-criteria   — SBTi FI Net-Zero Standard criteria
GET  /api/v1/temperature-alignment/ref/sector-pathways    — PACTA sector transition pathways
GET  /api/v1/temperature-alignment/ref/itr-table          — WACI to ITR interpolation table
GET  /api/v1/temperature-alignment/ref/asset-class-methods — PCAF/SBTi methods per asset class
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.temperature_alignment_engine import (
    TemperatureAlignmentEngine,
    TemperatureAlignmentRequest,
    WACIRequest,
    SBTiFIRequest,
    SectorAlignmentRequest,
    HoldingEntry,
    SBTiTargets,
    SBTI_FI_CRITERIA,
    PACTA_SECTOR_PATHWAYS,
    SDA_BENCHMARKS,
    ITR_TABLE,
    ASSET_CLASS_METHODS,
    PCAF_DQS_DEFINITIONS,
    SECTOR_PROFILES,
    ENGAGEMENT_THRESHOLDS,
)

router = APIRouter(prefix="/api/v1/temperature-alignment", tags=["Temperature Alignment (E103)"])

# ---------------------------------------------------------------------------
# Engine singleton
# ---------------------------------------------------------------------------

_engine: Optional[TemperatureAlignmentEngine] = None


def _get_engine() -> TemperatureAlignmentEngine:
    global _engine
    if _engine is None:
        _engine = TemperatureAlignmentEngine()
    return _engine


# ---------------------------------------------------------------------------
# POST /assess
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Full portfolio temperature alignment assessment")
def assess_temperature_alignment(req: TemperatureAlignmentRequest) -> Dict[str, Any]:
    """
    Full portfolio temperature alignment assessment combining PCAF + SBTi FI + PACTA.

    Returns:
    - Portfolio WACI (tCO2e per USD million revenue)
    - Portfolio ITR (implied temperature rise, degrees C)
    - PCAF DQS exposure-weighted data quality score
    - Sector-level WACI, ITR, and PACTA alignment %
    - SBTi FI criteria assessment (if sbti_targets provided)
    - Engagement priority list by sector

    Methodology options: waci / sda / temperature_rating / pacta
    """
    engine = _get_engine()
    return engine.assess_temperature_alignment(
        portfolio_name=req.portfolio_name,
        fi_type=req.fi_type,
        total_aum_bn=req.total_aum_bn,
        holdings=req.holdings,
        methodology=req.methodology,
        base_year=req.base_year,
        sbti_targets=req.sbti_targets,
    )


# ---------------------------------------------------------------------------
# POST /waci
# ---------------------------------------------------------------------------

class WACIResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    waci_tco2_per_mn_usd: float
    implied_temperature_c: float
    total_scope12_tco2: float
    total_exposure_bn: float
    holding_count: int
    pcaf_dqs_score: float
    calculation_note: str


@router.post("/waci", response_model=WACIResponse, summary="Calculate WACI for a set of holdings")
def calculate_waci(req: WACIRequest) -> WACIResponse:
    """
    Calculate exposure-weighted average carbon intensity (WACI).

    WACI = sum(portfolio_weight_i x (scope1_i + scope2_i) / revenue_i_mn)
    Result in tCO2e per USD million revenue.

    Also returns the corresponding implied temperature rise (ITR) for context.
    """
    engine = _get_engine()
    waci = engine.calculate_waci(req.holdings)
    itr = engine.calculate_itr(waci)
    dqs = engine.calculate_pcaf_dqs(req.holdings)
    total_s12 = sum(h.scope1_emissions_tco2 + h.scope2_emissions_tco2 for h in req.holdings)
    total_exp = sum(h.exposure_bn for h in req.holdings)

    return WACIResponse(
        waci_tco2_per_mn_usd=round(waci, 4),
        implied_temperature_c=round(itr, 2),
        total_scope12_tco2=round(total_s12, 0),
        total_exposure_bn=round(total_exp, 4),
        holding_count=len(req.holdings),
        pcaf_dqs_score=round(dqs, 2),
        calculation_note="WACI = sum(weight_i x S1+S2_emissions_i / revenue_i). ITR via MSCI/Carbon Delta interpolation.",
    )


# ---------------------------------------------------------------------------
# POST /itr
# ---------------------------------------------------------------------------

class ITRRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    waci: float = Field(..., ge=0.0, description="WACI in tCO2e per USD million revenue")


class ITRResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    waci_input: float
    implied_temperature_c: float
    temperature_label: str
    on_track_1_5c: bool
    on_track_2c: bool
    gap_to_1_5c_waci: float
    interpolation_method: str


@router.post("/itr", response_model=ITRResponse, summary="Implied temperature rise from WACI")
def calculate_itr(req: ITRRequest) -> ITRResponse:
    """
    Convert WACI (tCO2e / USD million revenue) to implied temperature rise (ITR).

    Linear interpolation across MSCI/Carbon Delta anchor table:
    - WACI 50  -> 1.5 deg C (Paris-aligned)
    - WACI 100 -> 1.7 deg C
    - WACI 200 -> 2.0 deg C
    - WACI 300 -> 2.3 deg C
    - WACI 600 -> 3.0 deg C
    - WACI 1000 -> 4.0 deg C
    """
    engine = _get_engine()
    itr = engine.calculate_itr(req.waci)

    if itr <= 1.5:
        label = "Paris-aligned (1.5C)"
    elif itr <= 2.0:
        label = "Below 2C"
    elif itr <= 3.0:
        label = "Delayed transition / current policies"
    else:
        label = "Hot house world (>3C)"

    return ITRResponse(
        waci_input=req.waci,
        implied_temperature_c=round(itr, 2),
        temperature_label=label,
        on_track_1_5c=itr <= 1.5,
        on_track_2c=itr <= 2.0,
        gap_to_1_5c_waci=max(0.0, round(req.waci - 50.0, 2)),
        interpolation_method="MSCI Carbon Delta / Carbon Portfolio Analytics (2021) — linear interpolation",
    )


# ---------------------------------------------------------------------------
# POST /sbti-fi
# ---------------------------------------------------------------------------

@router.post("/sbti-fi", summary="SBTi FI Net-Zero Standard criteria assessment")
def assess_sbti_fi(req: SBTiFIRequest) -> Dict[str, Any]:
    """
    Score a portfolio against all 6 SBTi Financial Institutions Net-Zero Standard v1.0 criteria.

    Criteria:
    - NZ-1: Long-term S1+2 absolute contraction >= 90% (weight 20%)
    - NZ-2: Long-term S3 absolute contraction >= 90% (weight 15%)
    - NT-1: Near-term S1+2 >= 42% reduction by 2030 from 2020 (weight 25%)
    - NT-2: Near-term S3 engagement >= 25% coverage by 2030 (weight 15%)
    - FLAG-1: Land sector target if FLAG exposure >= 5% (weight 10%)
    - FI-1: >= 50% portfolio companies with SBTi-validated targets by 2030 (weight 15%)
    """
    engine = _get_engine()
    return engine.assess_sbti_fi_criteria(
        portfolio_waci=req.portfolio_waci,
        scope1_financed=req.scope1_financed_tco2,
        scope2_financed=req.scope2_financed_tco2,
        scope3_financed=req.scope3_financed_tco2,
        base_year=req.base_year,
        target_year=req.target_year,
        sbti_targets=req.sbti_targets,
        portfolio_name=req.portfolio_name,
        flag_sector_exposure_pct=req.flag_sector_exposure_pct,
        portfolio_companies_with_sbti_pct=req.portfolio_companies_with_sbti_pct,
    )


# ---------------------------------------------------------------------------
# POST /sector-alignment
# ---------------------------------------------------------------------------

@router.post("/sector-alignment", summary="Single sector PACTA alignment assessment")
def sector_alignment(req: SectorAlignmentRequest) -> Dict[str, Any]:
    """
    PACTA alignment assessment for a single sector vs IEA NZE 2050 trajectory.

    Returns:
    - Alignment % vs IEA NZE 2030 benchmark
    - Gap to NZE 2030 and Paris-aligned threshold
    - Full NZE and CPS trajectories (2025-2050)
    - Paris-aligned flag

    Available sectors: power, automotive, steel, cement, oil_and_gas, aviation, shipping, real_estate
    """
    engine = _get_engine()
    return engine.calculate_sector_alignment(
        sector=req.sector,
        current_value=req.current_value,
        base_year=req.base_year,
    )


# ---------------------------------------------------------------------------
# GET /ref/sbti-fi-criteria
# ---------------------------------------------------------------------------

@router.get("/ref/sbti-fi-criteria", summary="SBTi FI Net-Zero Standard v1.0 criteria")
def ref_sbti_fi_criteria() -> Dict[str, Any]:
    """
    All 6 SBTi Financial Institutions Net-Zero Standard v1.0 criteria with:
    - Scope coverage
    - Required reduction / coverage percentages
    - Criterion weight in overall assessment
    - SBTi guidance reference
    - Verification method
    """
    return {
        "sbti_fi_criteria": [
            {"criterion_id": k, **v}
            for k, v in SBTI_FI_CRITERIA.items()
        ],
        "total_criteria": len(SBTI_FI_CRITERIA),
        "standard": "SBTi Financial Institutions Net-Zero Standard v1.0 (September 2022)",
        "validation_body": "Science Based Targets initiative (SBTi)",
        "eligible_asset_classes": list(ASSET_CLASS_METHODS.keys()),
    }


# ---------------------------------------------------------------------------
# GET /ref/sector-pathways
# ---------------------------------------------------------------------------

@router.get("/ref/sector-pathways", summary="PACTA sector transition technology pathways")
def ref_sector_pathways() -> Dict[str, Any]:
    """
    PACTA sector transition pathways for 8 sectors.

    Each sector includes:
    - IEA NZE 2050 scenario trajectory (2025-2050)
    - IEA Current Policies Scenario trajectory (2025-2050)
    - Paris-aligned threshold for 2030
    - Current global average level
    - Metric and unit description
    - NACE codes
    """
    return {
        "sector_pathways": [
            {"sector": k, **v}
            for k, v in PACTA_SECTOR_PATHWAYS.items()
        ],
        "sda_benchmarks": SDA_BENCHMARKS,
        "total_sectors": len(PACTA_SECTOR_PATHWAYS),
        "source": "IEA World Energy Outlook Net Zero Emissions by 2050 Scenario (NZE 2050, 2023)",
        "methodology": "Paris Agreement Capital Transition Assessment (PACTA) — 2022 update",
    }


# ---------------------------------------------------------------------------
# GET /ref/itr-table
# ---------------------------------------------------------------------------

@router.get("/ref/itr-table", summary="WACI to ITR interpolation anchor table")
def ref_itr_table() -> Dict[str, Any]:
    """
    WACI to implied temperature rise (ITR) interpolation anchor table.

    Based on MSCI Carbon Delta / Carbon Portfolio Analytics methodology (2021).
    Linear interpolation applied between anchor points.
    WACI unit: tCO2e per USD million revenue.
    """
    return {
        "itr_table": ITR_TABLE,
        "total_anchors": len(ITR_TABLE),
        "waci_unit": "tCO2e per USD million revenue",
        "temperature_unit": "degrees Celsius",
        "methodology": "MSCI Carbon Delta / Carbon Portfolio Analytics (2021)",
        "key_thresholds": {
            "paris_1_5c_waci": 50,
            "below_2c_waci": 200,
            "current_policies_waci": 450,
        },
        "engagement_thresholds": ENGAGEMENT_THRESHOLDS,
    }


# ---------------------------------------------------------------------------
# GET /ref/asset-class-methods
# ---------------------------------------------------------------------------

@router.get("/ref/asset-class-methods", summary="PCAF/SBTi methods per asset class")
def ref_asset_class_methods() -> Dict[str, Any]:
    """
    PCAF and SBTi recommended methods per eligible asset class.

    Each asset class includes:
    - PCAF attribution formula
    - PCAF standard part reference
    - SBTi FI recommended method
    - Data sources
    - Scope coverage (S1/S2/S3)
    """
    return {
        "asset_class_methods": [
            {"asset_class": k, **v}
            for k, v in ASSET_CLASS_METHODS.items()
        ],
        "total_asset_classes": len(ASSET_CLASS_METHODS),
        "pcaf_standard": "PCAF Global GHG Accounting and Reporting Standard Part A (2022)",
        "sbti_standard": "SBTi Financial Institutions Net-Zero Standard v1.0 (2022)",
    }


# ---------------------------------------------------------------------------
# GET /ref/pcaf-dqs
# ---------------------------------------------------------------------------

@router.get("/ref/pcaf-dqs", summary="PCAF data quality score definitions")
def ref_pcaf_dqs() -> Dict[str, Any]:
    """
    PCAF DQS (Data Quality Score) scale 1-5 with confidence weights.

    DQS 1 = verified company-specific data (100% confidence)
    DQS 5 = EEIO / economic input-output estimate (20% confidence)
    """
    return {
        "pcaf_dqs": [
            {"score": k, **v}
            for k, v in PCAF_DQS_DEFINITIONS.items()
        ],
        "source": "PCAF Global GHG Accounting and Reporting Standard Part A (2022), Section 2.4",
        "note": "Exposure-weighted average DQS across portfolio holdings; target DQS <= 3",
    }


# ---------------------------------------------------------------------------
# GET /ref/sector-profiles
# ---------------------------------------------------------------------------

@router.get("/ref/sector-profiles", summary="Carbon-intensive sector profiles with NACE codes")
def ref_sector_profiles() -> Dict[str, Any]:
    """
    8 carbon-intensive sector profiles with NACE codes, scope focus, and SDA benchmark keys.
    """
    return {
        "sector_profiles": [
            {"sector_key": k, **v}
            for k, v in SECTOR_PROFILES.items()
        ],
        "total_profiles": len(SECTOR_PROFILES),
        "note": "Focus sectors for PACTA and SBTi FI sectoral approach (SDA) coverage",
    }
