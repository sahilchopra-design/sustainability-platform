"""
Stress Testing & PD Backtesting API Routes
===========================================

Endpoints for:
  - Multi-scenario climate stress testing (EBA/ECB/BCBS methodology)
  - PD model backtesting with discriminatory power & calibration metrics
  - Reference data: scenarios, PD multipliers, LGD haircuts, sector risk levels
  - Traffic light system per EBA GL/2017/16

Router prefix: /api/v1/stress-testing
Tags: Stress Testing & PD Backtesting

Author: Risk Analytics Platform
Version: 1.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.stress_test_runner import (
    StressTestRunner,
    LoanBookExposure,
    StressTestResult,
    ScenarioSummary,
    MigrationMatrix,
    SectorConcentration,
    SCENARIOS,
    SCENARIO_WEIGHTS,
    SCENARIO_PD_MULTIPLIERS,
    SCENARIO_LGD_HAIRCUTS,
    SECTOR_RISK_LEVELS,
)
from services.pd_backtester import (
    PDBacktester,
    ObservedDefault,
    BacktestMetrics,
    GradeBacktestResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/stress-testing",
    tags=["Stress Testing & PD Backtesting"],
)


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS -- STRESS TESTING
# ---------------------------------------------------------------------------


class LoanBookExposureModel(BaseModel):
    """Single loan book exposure for stress testing."""
    exposure_id: str = Field(..., description="Unique exposure identifier")
    obligor_name: str = Field("", description="Counterparty / obligor name")
    sector: str = Field("Unclassified", description="Industry sector")
    collateral_type: str = Field(
        "unsecured",
        description="Collateral class: property | equipment | financial | unsecured",
    )
    baseline_pd: float = Field(
        ..., ge=0, le=1, description="Annualised 12-month PD (0-1)"
    )
    baseline_lgd: float = Field(
        ..., ge=0, le=1, description="Point-in-time LGD (0-1)"
    )
    ead: float = Field(..., ge=0, description="Exposure At Default")
    current_stage: int = Field(
        1, ge=1, le=3, description="IFRS 9 stage (1, 2, or 3)"
    )
    maturity_years: float = Field(5.0, ge=0, description="Remaining maturity in years")
    rating_grade: str = Field("", description="Internal rating grade (for reporting)")


class StressTestRequest(BaseModel):
    """Stress test request."""
    loan_book: List[LoanBookExposureModel] = Field(
        ..., min_length=1, max_length=50000,
        description="Loan book exposures to stress",
    )
    portfolio_name: str = Field(
        "Portfolio", description="Portfolio name for reporting"
    )
    scenarios: Optional[List[str]] = Field(
        None,
        description="Scenario names to run (default: all four -- "
                    "OPTIMISTIC, BASE, ADVERSE, SEVERE)",
    )
    include_detailed: bool = Field(
        False,
        description="Include per-exposure results in response (can be large)",
    )


class ScenarioSummaryResponse(BaseModel):
    """Per-scenario summary in response."""
    scenario: str
    weight: float
    total_ead: float
    total_ecl: float
    total_ecl_base: float
    ecl_uplift_pct: float
    weighted_avg_pd: float
    weighted_avg_lgd: float
    rwa_impact: float
    capital_shortfall: float
    stage1_count: int
    stage2_count: int
    stage3_count: int


class MigrationMatrixResponse(BaseModel):
    """Stage migration matrix in response."""
    scenario: str
    transitions: Dict[str, int]
    total_exposures: int
    sicr_trigger_count: int
    default_trigger_count: int


class SectorConcentrationResponse(BaseModel):
    """Sector concentration entry in response."""
    sector: str
    scenario: str
    exposure_count: int
    total_ead: float
    total_ecl_base: float
    total_ecl_stressed: float
    ecl_uplift_pct: float
    concentration_pct: float
    avg_pd_base: float
    avg_pd_stressed: float


class StressTestResponse(BaseModel):
    """Complete stress test response."""
    run_id: str
    portfolio_name: str
    scenarios_run: List[str]
    scenario_summaries: Dict[str, ScenarioSummaryResponse]
    pw_ecl: float
    pw_ecl_base: float
    pw_ecl_uplift_pct: float
    migration_matrices: Dict[str, MigrationMatrixResponse]
    sector_concentrations: Dict[str, List[SectorConcentrationResponse]]
    capital_impact_summary: Dict[str, float]
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS -- PD BACKTESTING
# ---------------------------------------------------------------------------


class ObservedDefaultModel(BaseModel):
    """Single observation for PD backtesting."""
    exposure_id: str = Field(..., description="Exposure identifier")
    rating_grade: str = Field(..., description="Internal rating grade (AAA..D)")
    predicted_pd: float = Field(
        ..., ge=0, le=1, description="Model-predicted PD (0-1)"
    )
    actual_default: int = Field(
        ..., ge=0, le=1, description="1 = defaulted, 0 = non-default"
    )
    exposure_amount: float = Field(0.0, ge=0)
    sector: str = Field("")
    vintage_year: int = Field(0)


class BacktestRequest(BaseModel):
    """PD backtest request."""
    observations: List[ObservedDefaultModel] = Field(
        ..., min_length=30, max_length=100000,
        description="Observations (minimum 30 required per EBA GL/2017/16)",
    )
    n_buckets: int = Field(
        10, ge=2, le=20, description="Number of buckets for Hosmer-Lemeshow test"
    )
    confidence_level: float = Field(
        0.95, ge=0.90, le=0.99, description="Confidence level for binomial test"
    )


class GradeResultResponse(BaseModel):
    """Per-grade backtest result with traffic light."""
    grade: str
    count: int
    default_count: int
    observed_default_rate: float
    predicted_pd_avg: float
    binomial_p_value: float
    traffic_light: str
    prediction_error_pct: float


class BacktestResponse(BaseModel):
    """PD backtest response -- all metrics + grade results + traffic lights."""
    # Discriminatory power
    gini_coefficient: float
    auroc: float
    ks_statistic: float
    ks_p_value: float

    # Calibration
    brier_score: float
    brier_skill_score: float
    hosmer_lemeshow_chi2: float
    hosmer_lemeshow_p_value: float
    hosmer_lemeshow_df: int

    # Information Value
    information_value: float
    iv_interpretation: str

    # Per-grade traffic lights
    grade_results: List[GradeResultResponse]
    overall_traffic_light: str

    # Summary
    total_observations: int
    total_defaults: int
    overall_default_rate: float
    avg_predicted_pd: float
    prediction_error_pct: float

    # Regulatory assessment
    model_valid: bool
    validation_issues: List[str]
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS -- Pydantic <-> dataclass conversion
# ---------------------------------------------------------------------------


def _pydantic_to_exposure(m: LoanBookExposureModel) -> LoanBookExposure:
    """Convert Pydantic request model to service dataclass."""
    return LoanBookExposure(
        exposure_id=m.exposure_id,
        obligor_name=m.obligor_name,
        sector=m.sector,
        collateral_type=m.collateral_type,
        baseline_pd=m.baseline_pd,
        baseline_lgd=m.baseline_lgd,
        ead=m.ead,
        current_stage=m.current_stage,
        maturity_years=m.maturity_years,
        rating_grade=m.rating_grade,
    )


def _pydantic_to_observation(m: ObservedDefaultModel) -> ObservedDefault:
    """Convert Pydantic request model to service dataclass."""
    return ObservedDefault(
        exposure_id=m.exposure_id,
        rating_grade=m.rating_grade,
        predicted_pd=m.predicted_pd,
        actual_default=m.actual_default,
        exposure_amount=m.exposure_amount,
        sector=m.sector,
        vintage_year=m.vintage_year,
    )


def _result_to_stress_response(result: StressTestResult) -> StressTestResponse:
    """Convert service StressTestResult to Pydantic response model."""
    scenario_summaries: Dict[str, ScenarioSummaryResponse] = {}
    for s, summary in result.scenario_summaries.items():
        scenario_summaries[s] = ScenarioSummaryResponse(
            scenario=summary.scenario,
            weight=summary.weight,
            total_ead=summary.total_ead,
            total_ecl=summary.total_ecl,
            total_ecl_base=summary.total_ecl_base,
            ecl_uplift_pct=summary.ecl_uplift_pct,
            weighted_avg_pd=summary.weighted_avg_pd,
            weighted_avg_lgd=summary.weighted_avg_lgd,
            rwa_impact=summary.rwa_impact,
            capital_shortfall=summary.capital_shortfall,
            stage1_count=summary.stage1_count,
            stage2_count=summary.stage2_count,
            stage3_count=summary.stage3_count,
        )

    migration_matrices: Dict[str, MigrationMatrixResponse] = {}
    for s, matrix in result.migration_matrices.items():
        migration_matrices[s] = MigrationMatrixResponse(
            scenario=matrix.scenario,
            transitions=matrix.transitions,
            total_exposures=matrix.total_exposures,
            sicr_trigger_count=matrix.sicr_trigger_count,
            default_trigger_count=matrix.default_trigger_count,
        )

    sector_concentrations: Dict[str, List[SectorConcentrationResponse]] = {}
    for s, concs in result.sector_concentrations.items():
        sector_concentrations[s] = [
            SectorConcentrationResponse(
                sector=sc.sector,
                scenario=sc.scenario,
                exposure_count=sc.exposure_count,
                total_ead=sc.total_ead,
                total_ecl_base=sc.total_ecl_base,
                total_ecl_stressed=sc.total_ecl_stressed,
                ecl_uplift_pct=sc.ecl_uplift_pct,
                concentration_pct=sc.concentration_pct,
                avg_pd_base=sc.avg_pd_base,
                avg_pd_stressed=sc.avg_pd_stressed,
            )
            for sc in concs
        ]

    return StressTestResponse(
        run_id=result.run_id,
        portfolio_name=result.portfolio_name,
        scenarios_run=result.scenarios_run,
        scenario_summaries=scenario_summaries,
        pw_ecl=result.pw_ecl,
        pw_ecl_base=result.pw_ecl_base,
        pw_ecl_uplift_pct=result.pw_ecl_uplift_pct,
        migration_matrices=migration_matrices,
        sector_concentrations=sector_concentrations,
        capital_impact_summary=result.capital_impact_summary,
        methodology_notes=result.methodology_notes,
    )


def _result_to_backtest_response(metrics: BacktestMetrics) -> BacktestResponse:
    """Convert service BacktestMetrics to Pydantic response model."""
    grade_results = [
        GradeResultResponse(
            grade=g.grade,
            count=g.count,
            default_count=g.default_count,
            observed_default_rate=g.observed_default_rate,
            predicted_pd_avg=g.predicted_pd_avg,
            binomial_p_value=g.binomial_p_value,
            traffic_light=g.traffic_light,
            prediction_error_pct=g.prediction_error_pct,
        )
        for g in metrics.grade_results
    ]

    return BacktestResponse(
        gini_coefficient=metrics.gini_coefficient,
        auroc=metrics.auroc,
        ks_statistic=metrics.ks_statistic,
        ks_p_value=metrics.ks_p_value,
        brier_score=metrics.brier_score,
        brier_skill_score=metrics.brier_skill_score,
        hosmer_lemeshow_chi2=metrics.hosmer_lemeshow_chi2,
        hosmer_lemeshow_p_value=metrics.hosmer_lemeshow_p_value,
        hosmer_lemeshow_df=metrics.hosmer_lemeshow_df,
        information_value=metrics.information_value,
        iv_interpretation=metrics.iv_interpretation,
        grade_results=grade_results,
        overall_traffic_light=metrics.overall_traffic_light,
        total_observations=metrics.total_observations,
        total_defaults=metrics.total_defaults,
        overall_default_rate=metrics.overall_default_rate,
        avg_predicted_pd=metrics.avg_predicted_pd,
        prediction_error_pct=metrics.prediction_error_pct,
        model_valid=metrics.model_valid,
        validation_issues=metrics.validation_issues,
        methodology_notes=metrics.methodology_notes,
    )


# ---------------------------------------------------------------------------
# STRESS TEST ENDPOINTS
# ---------------------------------------------------------------------------


@router.post("/run", response_model=StressTestResponse)
async def run_stress_test(request: StressTestRequest) -> StressTestResponse:
    """
    Execute multi-scenario climate stress test on a loan book.

    Runs PD/LGD/ECL stress across NGFS-aligned scenarios, producing
    stage migration matrices, sector concentration analysis,
    probability-weighted ECL, and capital impact estimates.
    """
    try:
        run_id = f"ST-{uuid.uuid4().hex[:8].upper()}"
        runner = StressTestRunner(
            scenarios=request.scenarios,
            include_detailed=request.include_detailed,
        )
        loan_book = [_pydantic_to_exposure(e) for e in request.loan_book]
        result = runner.run(
            loan_book=loan_book,
            portfolio_name=request.portfolio_name,
            run_id=run_id,
        )
        return _result_to_stress_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Stress test failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Stress test failed: {str(e)}"
        )


@router.get("/scenarios")
async def get_scenarios() -> Dict[str, Any]:
    """Return available stress test scenarios and their probability weights."""
    return {
        "scenarios": SCENARIOS,
        "weights": SCENARIO_WEIGHTS,
    }


@router.get("/pd-multipliers")
async def get_pd_multipliers() -> Dict[str, Any]:
    """Return scenario PD multiplier tables (scenario x risk level)."""
    return {"pd_multipliers": SCENARIO_PD_MULTIPLIERS}


@router.get("/lgd-haircuts")
async def get_lgd_haircuts() -> Dict[str, Any]:
    """Return scenario LGD haircut tables (scenario x collateral type)."""
    return {"lgd_haircuts": SCENARIO_LGD_HAIRCUTS}


@router.get("/sector-risk-levels")
async def get_sector_risk_levels() -> Dict[str, Any]:
    """Return sector-to-risk-level mapping (18+ sectors)."""
    return {"sector_risk_levels": SECTOR_RISK_LEVELS}


# ---------------------------------------------------------------------------
# PD BACKTESTING ENDPOINTS
# ---------------------------------------------------------------------------


@router.post("/backtest", response_model=BacktestResponse)
async def run_pd_backtest(request: BacktestRequest) -> BacktestResponse:
    """
    Run PD model backtest with discriminatory power and calibration metrics.

    Returns Gini, AUROC, KS, Brier, Hosmer-Lemeshow, IV, and per-grade
    traffic light results per EBA GL/2017/16.

    Minimum 30 observations required.
    """
    try:
        backtester = PDBacktester(
            n_buckets=request.n_buckets,
            confidence_level=request.confidence_level,
        )
        observations = [_pydantic_to_observation(o) for o in request.observations]
        metrics = backtester.backtest(observations)
        return _result_to_backtest_response(metrics)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("PD backtest failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"PD backtest failed: {str(e)}"
        )


@router.get("/backtest/thresholds")
async def get_backtest_thresholds() -> Dict[str, Any]:
    """
    Return backtest quality thresholds.

    Includes Gini thresholds, IV thresholds, traffic light rules,
    and recommended minimum sample sizes.
    """
    return {
        "gini_thresholds": PDBacktester.get_gini_thresholds(),
        "iv_thresholds": PDBacktester.get_iv_thresholds(),
        "traffic_light_rules": PDBacktester.get_traffic_light_rules(),
        "minimum_sample_sizes": PDBacktester.get_minimum_sample_sizes(),
    }
