"""
LGD Downturn & Vintage Analysis API Routes

Endpoints for:
  - Downturn LGD estimation (CRR2 Art. 181(1)(b), EBA GL/2019/03)
  - Credit portfolio vintage analysis (IFRS 9, EBA GL/2017/06, ECB NPL Guidance)

Router prefix: /api/v1/lgd-vintage
Tags: LGD Downturn & Vintage Analysis
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.lgd_downturn_engine import (
    LGDDownturnEngine,
    DownturnLGDInput,
    DownturnLGDResult,
    DownturnLGDBatchResult,
    REGULATORY_LGD_FLOORS,
    DOWNTURN_ADDON_BY_COLLATERAL,
    SECTOR_DOWNTURN_MULT,
    COUNTRY_CYCLE_SEVERITY,
    CLIMATE_STRANDED_HAIRCUTS,
    GREEN_PREMIUM,
    PHYSICAL_RISK_LGD_MULT,
    SCENARIO_MULTIPLIERS,
)
from services.vintage_analyzer import (
    VintageAnalyzer,
    VintageExposure,
    VintageAnalysisResult,
    ECB_NPE_COVERAGE,
    BENCHMARK_CUMULATIVE_DR,
    EARLY_WARNING_THRESHOLD,
)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/lgd-vintage",
    tags=["LGD Downturn & Vintage Analysis"],
)


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS -- DOWNTURN LGD
# ---------------------------------------------------------------------------


class DownturnLGDInputModel(BaseModel):
    """Single exposure for downturn LGD calculation."""
    exposure_id: str = Field(..., description="Unique exposure identifier")
    counterparty_name: str = Field(..., description="Counterparty name")
    long_run_avg_lgd: float = Field(
        ..., ge=0, le=1, description="Long-run average LGD (0-1)"
    )
    collateral_type: str = Field(
        "unsecured",
        description=(
            "Collateral type: property, equipment, financial, unsecured, "
            "inventory, receivables, cash, other, "
            "real_estate_residential, real_estate_commercial"
        ),
    )
    collateral_value: float = Field(0.0, ge=0)
    exposure_amount: float = Field(..., ge=0, description="EAD")
    ltv_ratio: float = Field(0.0, ge=0, le=2.0)
    sector: str = Field("", description="Sector name")
    country: str = Field("", description="ISO 2-letter country code")
    asset_class: str = Field(
        "CORPORATE",
        description="CORPORATE, RETAIL_MORTGAGE, SME, etc.",
    )
    epc_rating: str = Field("", description="EPC rating A-G")
    physical_risk_level: str = Field(
        "", description="extreme / high / medium / low"
    )
    is_fossil_fuel_collateral: bool = Field(False)


class DownturnLGDRequest(BaseModel):
    """Batch downturn LGD calculation request."""
    exposures: List[DownturnLGDInputModel] = Field(
        ..., min_length=1, max_length=50000,
        description="Exposures for downturn LGD calculation",
    )
    include_climate_overlay: bool = Field(
        True, description="Include climate adjustments (stranded, physical, green)"
    )
    scenario: str = Field(
        "ADVERSE",
        description="Stress scenario: BASE (0.6x), ADVERSE (1.0x), SEVERE (1.5x)",
    )


class DownturnLGDContributionResponse(BaseModel):
    """Downturn LGD contribution breakdown."""
    base_long_run_lgd: float
    downturn_addon: float
    country_cycle_adjustment: float
    sector_severity_adjustment: float
    climate_stranded_addon: float
    climate_physical_addon: float
    green_premium_adjustment: float
    regulatory_floor_applied: bool
    regulatory_floor_value: float


class DownturnLGDResultResponse(BaseModel):
    """Single downturn LGD result."""
    exposure_id: str
    long_run_avg_lgd: float
    downturn_lgd: float
    downturn_uplift_pct: float
    contribution: DownturnLGDContributionResponse
    methodology_notes: List[str]


class DownturnLGDBatchResponse(BaseModel):
    """Batch downturn LGD response."""
    results: List[DownturnLGDResultResponse]
    portfolio_avg_lr_lgd: float
    portfolio_avg_dt_lgd: float
    portfolio_avg_uplift_pct: float
    floor_applied_count: int
    exposure_count: int
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS -- VINTAGE ANALYSIS
# ---------------------------------------------------------------------------


class VintageExposureModel(BaseModel):
    """Single exposure with vintage data."""
    exposure_id: str = Field(...)
    counterparty_name: str = Field(...)
    origination_date: str = Field(..., description="YYYY-MM-DD")
    origination_year: int = Field(..., ge=1990, le=2030)
    origination_quarter: int = Field(0, ge=0, le=4)
    original_amount: float = Field(0.0, ge=0)
    current_balance: float = Field(0.0, ge=0)
    is_defaulted: bool = Field(False)
    default_date: str = Field("")
    months_to_default: int = Field(0, ge=0)
    current_stage: int = Field(1, ge=1, le=3)
    sector: str = Field("")
    asset_class: str = Field("CORPORATE")
    collateral_type: str = Field("unsecured")
    is_npe: bool = Field(False)
    npe_age_years: float = Field(0.0, ge=0)
    provision_amount: float = Field(0.0, ge=0)
    epc_rating: str = Field("")
    is_green: bool = Field(False)


class VintageAnalysisRequest(BaseModel):
    """Vintage analysis request."""
    exposures: List[VintageExposureModel] = Field(
        ..., min_length=1, max_length=100000,
        description="Exposures for vintage analysis",
    )
    reference_year: int = Field(
        2025, ge=2000, le=2035,
        description="Reference year for age calculation",
    )
    granularity: str = Field(
        "annual",
        description="Cohort granularity: annual or quarterly",
    )


class VintageCohortResponse(BaseModel):
    """Single vintage cohort summary."""
    vintage_label: str
    vintage_year: int
    vintage_quarter: int
    exposure_count: int
    original_amount_total: float
    current_balance_total: float
    default_count: int
    cumulative_default_rate: float
    avg_months_to_default: float
    stage1_count: int
    stage2_count: int
    stage3_count: int
    stage2_migration_rate: float
    npe_count: int
    npe_coverage_ratio: float
    ecb_coverage_shortfall: float
    early_warning: bool
    benchmark_dr: float
    green_share_pct: float


class VintageMatrixResponse(BaseModel):
    """Vintage matrix response."""
    vintage_labels: List[str]
    age_labels: List[int]
    cumulative_dr_matrix: List[List[Optional[float]]]
    marginal_dr_matrix: List[List[Optional[float]]]


class VintageAnalysisResponse(BaseModel):
    """Complete vintage analysis response."""
    cohorts: List[VintageCohortResponse]
    vintage_matrix: VintageMatrixResponse
    total_exposures: int
    total_original_amount: float
    total_current_balance: float
    overall_cumulative_dr: float
    worst_vintage: str
    worst_vintage_dr: float
    best_vintage: str
    best_vintage_dr: float
    early_warning_vintages: List[str]
    npe_coverage_gap_total: float
    green_origination_trend: List[Dict[str, Any]]
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _model_to_downturn_input(m: DownturnLGDInputModel) -> DownturnLGDInput:
    """Convert Pydantic model to engine dataclass."""
    return DownturnLGDInput(
        exposure_id=m.exposure_id,
        counterparty_name=m.counterparty_name,
        long_run_avg_lgd=m.long_run_avg_lgd,
        collateral_type=m.collateral_type,
        collateral_value=m.collateral_value,
        exposure_amount=m.exposure_amount,
        ltv_ratio=m.ltv_ratio,
        sector=m.sector,
        country=m.country,
        asset_class=m.asset_class,
        epc_rating=m.epc_rating,
        physical_risk_level=m.physical_risk_level,
        is_fossil_fuel_collateral=m.is_fossil_fuel_collateral,
    )


def _model_to_vintage_exposure(m: VintageExposureModel) -> VintageExposure:
    """Convert Pydantic model to engine dataclass."""
    return VintageExposure(
        exposure_id=m.exposure_id,
        counterparty_name=m.counterparty_name,
        origination_date=m.origination_date,
        origination_year=m.origination_year,
        origination_quarter=m.origination_quarter,
        original_amount=m.original_amount,
        current_balance=m.current_balance,
        is_defaulted=m.is_defaulted,
        default_date=m.default_date,
        months_to_default=m.months_to_default,
        current_stage=m.current_stage,
        sector=m.sector,
        asset_class=m.asset_class,
        collateral_type=m.collateral_type,
        is_npe=m.is_npe,
        npe_age_years=m.npe_age_years,
        provision_amount=m.provision_amount,
        epc_rating=m.epc_rating,
        is_green=m.is_green,
    )


def _downturn_result_to_response(
    r: DownturnLGDResult,
) -> DownturnLGDResultResponse:
    """Convert engine result to API response model."""
    return DownturnLGDResultResponse(
        exposure_id=r.exposure_id,
        long_run_avg_lgd=r.long_run_avg_lgd,
        downturn_lgd=r.downturn_lgd,
        downturn_uplift_pct=r.downturn_uplift_pct,
        contribution=DownturnLGDContributionResponse(
            base_long_run_lgd=r.contribution.base_long_run_lgd,
            downturn_addon=r.contribution.downturn_addon,
            country_cycle_adjustment=r.contribution.country_cycle_adjustment,
            sector_severity_adjustment=r.contribution.sector_severity_adjustment,
            climate_stranded_addon=r.contribution.climate_stranded_addon,
            climate_physical_addon=r.contribution.climate_physical_addon,
            green_premium_adjustment=r.contribution.green_premium_adjustment,
            regulatory_floor_applied=r.contribution.regulatory_floor_applied,
            regulatory_floor_value=r.contribution.regulatory_floor_value,
        ),
        methodology_notes=r.methodology_notes,
    )


# ---------------------------------------------------------------------------
# DOWNTURN LGD ENDPOINTS
# ---------------------------------------------------------------------------


@router.post("/downturn", response_model=DownturnLGDBatchResponse)
async def calculate_downturn_lgd(
    request: DownturnLGDRequest,
) -> DownturnLGDBatchResponse:
    """
    Calculate downturn LGD for a portfolio of exposures.

    Returns downturn LGD per CRR2 Art. 181(1)(b) / EBA GL/2019/03 with:
      - Collateral-type downturn add-ons
      - Country cycle severity (25 countries)
      - Sector downturn multipliers (19 sectors)
      - Climate overlays (stranded assets, physical risk, green premium)
      - CRR2 Art. 164 regulatory floors
    """
    try:
        engine = LGDDownturnEngine(
            include_climate_overlay=request.include_climate_overlay,
            scenario=request.scenario,
        )
        inputs = [_model_to_downturn_input(e) for e in request.exposures]
        batch_result = engine.calculate_batch(inputs)

        return DownturnLGDBatchResponse(
            results=[
                _downturn_result_to_response(r)
                for r in batch_result.results
            ],
            portfolio_avg_lr_lgd=batch_result.portfolio_avg_lr_lgd,
            portfolio_avg_dt_lgd=batch_result.portfolio_avg_dt_lgd,
            portfolio_avg_uplift_pct=batch_result.portfolio_avg_uplift_pct,
            floor_applied_count=batch_result.floor_applied_count,
            exposure_count=batch_result.exposure_count,
            methodology_notes=batch_result.methodology_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Downturn LGD calculation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Downturn LGD failed: {str(e)}",
        )


@router.get("/downturn/regulatory-floors")
async def get_regulatory_floors() -> Dict[str, Any]:
    """
    Return CRR2 Art. 164 regulatory LGD floors.

    Floor values by asset class / collateral type:
      RESIDENTIAL_MORTGAGE=10%, COMMERCIAL_MORTGAGE=15%,
      CORPORATE_UNSECURED=25%, CORPORATE_SECURED=15%,
      SME_UNSECURED=25%, SME_SECURED=15%, RETAIL_UNSECURED=25%
    """
    return {
        "regulatory_floors": LGDDownturnEngine.get_regulatory_floors(),
        "regulation": "CRR2 Art. 164",
    }


@router.get("/downturn/addons")
async def get_downturn_addons() -> Dict[str, Any]:
    """
    Return downturn add-on table by collateral type (EBA GL/2019/03).

    property=8pp, equipment=10pp, financial=5pp, unsecured=12pp,
    inventory=10pp, receivables=8pp, cash=2pp, other=12pp
    """
    return {
        "downturn_addons": LGDDownturnEngine.get_downturn_addons(),
        "regulation": "EBA GL/2019/03",
    }


@router.get("/downturn/sector-severity")
async def get_sector_severity() -> Dict[str, Any]:
    """
    Return sector downturn severity multipliers (19 sectors).

    Range from 0.70 (Government) to 1.70 (Coal Mining).
    """
    return {
        "sector_severity": LGDDownturnEngine.get_sector_severity(),
    }


@router.get("/downturn/country-severity")
async def get_country_severity() -> Dict[str, Any]:
    """
    Return country economic cycle severity factors (25 countries).

    Range from 0.70 (CH, SG) to 1.50 (GR).
    """
    return {
        "country_cycle_severity": LGDDownturnEngine.get_country_cycle_severity(),
    }


@router.get("/downturn/climate-haircuts")
async def get_climate_haircuts() -> Dict[str, Any]:
    """
    Return climate stranded asset haircuts (8 sectors),
    physical risk multipliers, green premium / brown discount table,
    and scenario multipliers.
    """
    return {
        "stranded_haircuts": LGDDownturnEngine.get_climate_stranded_haircuts(),
        "physical_risk_multipliers": dict(PHYSICAL_RISK_LGD_MULT),
        "green_premium": LGDDownturnEngine.get_green_premium_table(),
        "scenario_multipliers": dict(SCENARIO_MULTIPLIERS),
    }


# ---------------------------------------------------------------------------
# VINTAGE ANALYSIS ENDPOINTS
# ---------------------------------------------------------------------------


@router.post("/vintage", response_model=VintageAnalysisResponse)
async def run_vintage_analysis(
    request: VintageAnalysisRequest,
) -> VintageAnalysisResponse:
    """
    Run vintage analysis on a credit portfolio.

    Returns:
      - Cohort summaries (per vintage year/quarter)
      - Vintage matrix (cumulative + marginal default rates by age)
      - ECB NPE backstop coverage gaps (EU Regulation 2019/630)
      - Early warning flags (vintages exceeding benchmark)
      - Green origination trend
    """
    try:
        analyzer = VintageAnalyzer(
            reference_year=request.reference_year,
            granularity=request.granularity,
        )
        exposures = [
            _model_to_vintage_exposure(e) for e in request.exposures
        ]
        result = analyzer.analyze(exposures)

        cohort_responses = [
            VintageCohortResponse(
                vintage_label=c.vintage_label,
                vintage_year=c.vintage_year,
                vintage_quarter=c.vintage_quarter,
                exposure_count=c.exposure_count,
                original_amount_total=c.original_amount_total,
                current_balance_total=c.current_balance_total,
                default_count=c.default_count,
                cumulative_default_rate=c.cumulative_default_rate,
                avg_months_to_default=c.avg_months_to_default,
                stage1_count=c.stage1_count,
                stage2_count=c.stage2_count,
                stage3_count=c.stage3_count,
                stage2_migration_rate=c.stage2_migration_rate,
                npe_count=c.npe_count,
                npe_coverage_ratio=c.npe_coverage_ratio,
                ecb_coverage_shortfall=c.ecb_coverage_shortfall,
                early_warning=c.early_warning,
                benchmark_dr=c.benchmark_dr,
                green_share_pct=c.green_share_pct,
            )
            for c in result.cohorts
        ]

        matrix_response = VintageMatrixResponse(
            vintage_labels=result.vintage_matrix.vintage_labels,
            age_labels=result.vintage_matrix.age_labels,
            cumulative_dr_matrix=result.vintage_matrix.cumulative_dr_matrix,
            marginal_dr_matrix=result.vintage_matrix.marginal_dr_matrix,
        )

        return VintageAnalysisResponse(
            cohorts=cohort_responses,
            vintage_matrix=matrix_response,
            total_exposures=result.total_exposures,
            total_original_amount=result.total_original_amount,
            total_current_balance=result.total_current_balance,
            overall_cumulative_dr=result.overall_cumulative_dr,
            worst_vintage=result.worst_vintage,
            worst_vintage_dr=result.worst_vintage_dr,
            best_vintage=result.best_vintage,
            best_vintage_dr=result.best_vintage_dr,
            early_warning_vintages=result.early_warning_vintages,
            npe_coverage_gap_total=result.npe_coverage_gap_total,
            green_origination_trend=result.green_origination_trend,
            methodology_notes=result.methodology_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Vintage analysis failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Vintage analysis failed: {str(e)}",
        )


@router.get("/vintage/ecb-coverage")
async def get_ecb_coverage_table() -> Dict[str, Any]:
    """
    Return ECB NPE calendar provisioning backstop table
    (EU Regulation 2019/630).

    Shows minimum coverage ratio by NPE age:
      - Unsecured: 35% at year 1, 100% at year 2+
      - Secured: 25% at year 3, ramp to 100% at year 9
    """
    return {
        "ecb_npe_coverage": VintageAnalyzer.get_ecb_npe_coverage_table(),
        "regulation": "EU Regulation 2019/630",
    }


@router.get("/vintage/benchmark-rates")
async def get_benchmark_rates() -> Dict[str, Any]:
    """
    Return benchmark cumulative default rates by vintage age.

    Used for early warning detection when a vintage exceeds
    the benchmark by more than the threshold (50%).
    """
    return {
        "benchmark_rates": VintageAnalyzer.get_benchmark_default_rates(),
        "early_warning_threshold": EARLY_WARNING_THRESHOLD,
    }
