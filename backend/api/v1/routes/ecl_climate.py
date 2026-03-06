"""
IFRS 9 ECL Climate-Adjusted Routes
Endpoints for climate-adjusted expected credit loss calculation under IFRS 9.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["IFRS 9 ECL Climate"])


class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


class ECLBaseInputs(BaseModel):
    exposure_id: str
    counterparty_id: Optional[str] = None
    sector: str
    country_iso: str
    exposure_at_default_gbp: float = Field(..., gt=0)
    base_pd_12m: float = Field(..., ge=0, le=1)
    base_pd_lifetime: float = Field(..., ge=0, le=1)
    lgd: float = Field(..., ge=0, le=1)
    maturity_years: int = Field(..., ge=1)
    current_stage: int = Field(..., ge=1, le=3)
    origination_pd: Optional[float] = Field(None, ge=0, le=1)


class ECLClimateInputs(BaseModel):
    physical_risk_score: Optional[float] = Field(None, ge=0, le=10)
    transition_risk_score: Optional[float] = Field(None, ge=0, le=10)
    carbon_intensity_tco2_revenue: Optional[float] = Field(None, ge=0)
    green_revenue_pct: Optional[float] = Field(None, ge=0, le=1)
    climate_scenario_weights: Optional[Dict[str, float]] = Field(
        None, description="Scenario name to probability weight mapping (must sum to 1.0)",
    )


class ECLCalculateRequest(BaseModel):
    base_inputs: ECLBaseInputs
    climate_inputs: ECLClimateInputs
    reporting_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class ScenarioECLResult(BaseModel):
    scenario: str
    pd_12m_adjusted: float
    pd_lifetime_adjusted: float
    ecl_12m_gbp: float
    ecl_lifetime_gbp: float
    stage: int


class ECLCalculateResponse(BaseModel):
    exposure_id: str
    probability_weighted_ecl_12m_gbp: float
    probability_weighted_ecl_lifetime_gbp: float
    determined_stage: int
    sicr_triggered: bool
    sicr_triggers: List[str]
    climate_uplift_pct: float
    scenario_results: List[ScenarioECLResult]
    validation_summary: ValidationSummary


class PortfolioECLRequest(BaseModel):
    exposures: List[ECLCalculateRequest]
    reporting_date: Optional[str] = None


class SectorBreakdown(BaseModel):
    sector: str
    count: int
    total_ecl_gbp: float
    average_climate_uplift_pct: float


class StageDistribution(BaseModel):
    stage_1_count: int
    stage_2_count: int
    stage_3_count: int
    stage_1_ecl_gbp: float
    stage_2_ecl_gbp: float
    stage_3_ecl_gbp: float


class PortfolioECLResponse(BaseModel):
    total_exposures: int
    total_ead_gbp: float
    total_ecl_baseline_gbp: float
    total_ecl_climate_adjusted_gbp: float
    total_ecl_uplift_gbp: float
    total_ecl_uplift_pct: float
    stage_distribution: StageDistribution
    sector_breakdown: List[SectorBreakdown]
    validation_summary: ValidationSummary


class SICRExposure(BaseModel):
    exposure_id: str
    sector: str
    current_stage: int
    sicr_triggered: bool
    sicr_triggers: List[str]
    pd_increase_pct: Optional[float] = None
    recommended_action: str


class SICRScreeningRequest(BaseModel):
    exposures: List[ECLCalculateRequest]
    reporting_date: Optional[str] = None


class SICRScreeningResponse(BaseModel):
    total_screened: int
    sicr_count: int
    sicr_pct: float
    exposures: List[SICRExposure]
    validation_summary: ValidationSummary


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


@router.post("/ecl/calculate", response_model=ECLCalculateResponse)
async def calculate_ecl(request: ECLCalculateRequest):
    """Calculate climate-adjusted ECL for a single exposure under IFRS 9."""
    logger.info("ECL calculation: exposure=%s sector=%s",
                request.base_inputs.exposure_id, request.base_inputs.sector)
    try:
        from services.ecl_climate_engine import ECLClimateEngine  # type: ignore
        result = ECLClimateEngine().calculate(
            base_inputs=request.base_inputs.model_dump(),
            climate_inputs=request.climate_inputs.model_dump(),
            reporting_date=request.reporting_date,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return ECLCalculateResponse(
            exposure_id=request.base_inputs.exposure_id,
            probability_weighted_ecl_12m_gbp=result["probability_weighted_ecl_12m_gbp"],
            probability_weighted_ecl_lifetime_gbp=result["probability_weighted_ecl_lifetime_gbp"],
            determined_stage=result["determined_stage"],
            sicr_triggered=result["sicr_triggered"],
            sicr_triggers=result.get("sicr_triggers", []),
            climate_uplift_pct=result["climate_uplift_pct"],
            scenario_results=[ScenarioECLResult(**s) for s in result.get("scenario_results", [])],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("ECL engine error: exposure=%s", request.base_inputs.exposure_id)
        raise HTTPException(status_code=500, detail=f"ECL engine error: {exc}") from exc


@router.post("/ecl/portfolio", response_model=PortfolioECLResponse)
async def calculate_portfolio_ecl(request: PortfolioECLRequest):
    """Portfolio-level climate-adjusted ECL with sector and stage breakdown."""
    logger.info("Portfolio ECL: %d exposures", len(request.exposures))
    if not request.exposures:
        raise HTTPException(status_code=400, detail="At least one exposure is required.")
    try:
        from services.ecl_climate_engine import ECLClimateEngine  # type: ignore
        result = ECLClimateEngine().calculate_portfolio(
            exposures=[
                {"base_inputs": e.base_inputs.model_dump(),
                 "climate_inputs": e.climate_inputs.model_dump()}
                for e in request.exposures
            ],
            reporting_date=request.reporting_date,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return PortfolioECLResponse(
            total_exposures=result["total_exposures"],
            total_ead_gbp=result["total_ead_gbp"],
            total_ecl_baseline_gbp=result["total_ecl_baseline_gbp"],
            total_ecl_climate_adjusted_gbp=result["total_ecl_climate_adjusted_gbp"],
            total_ecl_uplift_gbp=result["total_ecl_uplift_gbp"],
            total_ecl_uplift_pct=result["total_ecl_uplift_pct"],
            stage_distribution=StageDistribution(**result["stage_distribution"]),
            sector_breakdown=[SectorBreakdown(**s) for s in result.get("sector_breakdown", [])],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Portfolio ECL engine error")
        raise HTTPException(status_code=500, detail=f"Portfolio ECL engine error: {exc}") from exc


@router.post("/ecl/sicr-screening", response_model=SICRScreeningResponse)
async def screen_sicr(request: SICRScreeningRequest):
    """Screen a portfolio for Significant Increase in Credit Risk (SICR) triggers."""
    logger.info("SICR screening: %d exposures", len(request.exposures))
    if not request.exposures:
        raise HTTPException(status_code=400, detail="At least one exposure is required.")
    try:
        from services.ecl_climate_engine import ECLClimateEngine  # type: ignore
        result = ECLClimateEngine().screen_sicr(
            exposures=[
                {"base_inputs": e.base_inputs.model_dump(),
                 "climate_inputs": e.climate_inputs.model_dump()}
                for e in request.exposures
            ],
            reporting_date=request.reporting_date,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        exposures_out = [SICRExposure(**e) for e in result.get("exposures", [])]
        total = len(exposures_out)
        sicr_count = sum(1 for e in exposures_out if e.sicr_triggered)
        return SICRScreeningResponse(
            total_screened=total,
            sicr_count=sicr_count,
            sicr_pct=round(sicr_count / total * 100, 2) if total else 0.0,
            exposures=exposures_out,
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("SICR screening engine error")
        raise HTTPException(status_code=500, detail=f"SICR screening engine error: {exc}") from exc
