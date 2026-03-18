"""
Green Asset Ratio (GAR) & Counterparty Climate Score API Routes

Endpoints for:
  - GAR calculation per CRR Art. 449a / EU Taxonomy
  - Counterparty climate risk scoring (composite 0-100)

Router prefix: /api/v1/gar
Tags: GAR & Climate Scoring
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.gar_calculator import (
    GARCalculator,
    GARExposure,
    GARResult,
    EXCLUDED_ASSET_TYPES,
    NACE_TAXONOMY_MAP,
    get_eligible_objectives,
)
from services.counterparty_climate_scorer import (
    CounterpartyClimateScorer,
    CounterpartyInput,
    ClimateScoreResult,
    SECTOR_TRANSITION_RISK,
    RATING_MAP,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/gar", tags=["GAR & Climate Scoring"])


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS -- GAR
# ---------------------------------------------------------------------------


class ExposureModel(BaseModel):
    """Single exposure for GAR calculation."""
    exposure_id: str = Field(..., description="Unique exposure identifier")
    counterparty_name: str = Field(..., description="Counterparty name")
    asset_type: str = Field(..., description="NFC_LOAN, HOUSEHOLD_MORTGAGE, SOVEREIGN, etc.")
    gross_carrying_amount: float = Field(..., ge=0, description="Gross carrying amount (EUR)")
    classification: str = Field(
        "NOT_ELIGIBLE",
        description="TAXONOMY_ALIGNED, TAXONOMY_ELIGIBLE, NOT_ELIGIBLE",
    )
    primary_objective: str = Field("", description="Primary taxonomy objective code")
    secondary_objectives: List[str] = Field(default_factory=list)
    nace_code: str = Field("", description="NACE Rev. 2 activity code")
    sector: str = Field("", description="Sector name")
    country: str = Field("", description="ISO 2-letter country code")
    turnover_aligned: float = Field(0.0, ge=0, description="Turnover-based aligned amount")
    turnover_eligible: float = Field(0.0, ge=0)
    capex_aligned: float = Field(0.0, ge=0, description="CapEx-based aligned amount")
    capex_eligible: float = Field(0.0, ge=0)
    opex_aligned: float = Field(0.0, ge=0, description="OpEx-based aligned amount")
    opex_eligible: float = Field(0.0, ge=0)
    epc_rating: str = Field("", description="EPC rating A-G (for mortgages)")
    is_ev_loan: bool = Field(False)
    is_renovation_loan: bool = Field(False)


class GARCalculateRequest(BaseModel):
    """GAR calculation request."""
    exposures: List[ExposureModel] = Field(
        ..., min_length=1, max_length=50000,
        description="All on-balance-sheet exposures (stock)",
    )
    flow_exposures: Optional[List[ExposureModel]] = Field(
        None, description="New originations in period (for flow GAR)",
    )


class ObjectiveBreakdownResponse(BaseModel):
    objective: str
    objective_label: str
    aligned_amount: float
    eligible_amount: float
    not_eligible_amount: float
    aligned_pct: float
    eligible_pct: float


class KPIBreakdownResponse(BaseModel):
    kpi_type: str
    aligned_amount: float
    eligible_amount: float
    covered_assets: float
    gar_ratio: float


class AssetTypeBreakdownResponse(BaseModel):
    asset_type: str
    total_amount: float
    aligned_amount: float
    eligible_amount: float
    alignment_ratio: float
    count: int


class GARCalculateResponse(BaseModel):
    """GAR calculation response."""
    gar_ratio: float
    gar_eligible_ratio: float
    gar_flow: float
    total_assets: float
    excluded_assets: float
    covered_assets: float
    aligned_assets: float
    eligible_assets: float
    not_eligible_assets: float
    by_objective: List[ObjectiveBreakdownResponse]
    by_kpi_type: List[KPIBreakdownResponse]
    by_asset_type: List[AssetTypeBreakdownResponse]
    assessed_pct: float
    not_assessed_count: int
    exposure_count: int
    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS -- COUNTERPARTY CLIMATE SCORE
# ---------------------------------------------------------------------------


class CounterpartyScoreRequest(BaseModel):
    """Single counterparty climate score request."""
    counterparty_id: str = Field(..., description="Counterparty ID")
    counterparty_name: str = Field(..., description="Counterparty name")
    sector: str = Field(..., description="Industry sector")
    country: str = Field("", description="Country code")
    carbon_intensity_rank: Optional[float] = Field(None, ge=0, le=100)
    sector_risk_level: Optional[str] = Field(None, description="low/medium/high/very_high")
    policy_exposure_score: Optional[float] = Field(None, ge=0, le=100)
    technology_readiness: Optional[float] = Field(None, ge=0, le=100)
    flood_risk: Optional[float] = Field(None, ge=0, le=100)
    heat_stress: Optional[float] = Field(None, ge=0, le=100)
    water_stress: Optional[float] = Field(None, ge=0, le=100)
    supply_chain_exposure: Optional[float] = Field(None, ge=0, le=100)
    sbti_committed: bool = False
    taxonomy_aligned_pct: Optional[float] = Field(None, ge=0, le=100)
    transition_plan_quality: Optional[int] = Field(None, ge=1, le=5)
    disclosure_level: str = Field("none", description="none/partial/full")
    data_recency_years: Optional[float] = Field(None, ge=0, le=5)
    third_party_verified: bool = False


class ScoreBreakdownResponse(BaseModel):
    component_name: str
    weight: float
    raw_score: float
    weighted_score: float
    sub_scores: Dict[str, float]
    data_available: bool


class CounterpartyScoreResponse(BaseModel):
    """Counterparty climate score response."""
    counterparty_id: str
    counterparty_name: str
    sector: str
    composite_score: float
    rating: str
    rating_label: str
    transition_risk: ScoreBreakdownResponse
    physical_risk: ScoreBreakdownResponse
    alignment: ScoreBreakdownResponse
    data_quality: ScoreBreakdownResponse
    methodology_notes: List[str]


class CounterpartyBatchRequest(BaseModel):
    """Batch counterparty scoring request."""
    counterparties: List[CounterpartyScoreRequest] = Field(
        ..., min_length=1, max_length=5000,
    )
    custom_weights: Optional[Dict[str, float]] = None


# ---------------------------------------------------------------------------
# CONVERTERS
# ---------------------------------------------------------------------------


def _to_gar_exposure(m: ExposureModel) -> GARExposure:
    return GARExposure(
        exposure_id=m.exposure_id,
        counterparty_name=m.counterparty_name,
        asset_type=m.asset_type,
        gross_carrying_amount=m.gross_carrying_amount,
        classification=m.classification,
        primary_objective=m.primary_objective,
        secondary_objectives=m.secondary_objectives,
        nace_code=m.nace_code,
        sector=m.sector,
        country=m.country,
        turnover_aligned=m.turnover_aligned,
        turnover_eligible=m.turnover_eligible,
        capex_aligned=m.capex_aligned,
        capex_eligible=m.capex_eligible,
        opex_aligned=m.opex_aligned,
        opex_eligible=m.opex_eligible,
        epc_rating=m.epc_rating,
        is_ev_loan=m.is_ev_loan,
        is_renovation_loan=m.is_renovation_loan,
    )


def _to_counterparty_input(m: CounterpartyScoreRequest) -> CounterpartyInput:
    return CounterpartyInput(
        counterparty_id=m.counterparty_id,
        counterparty_name=m.counterparty_name,
        sector=m.sector,
        country=m.country,
        carbon_intensity_rank=m.carbon_intensity_rank,
        sector_risk_level=m.sector_risk_level,
        policy_exposure_score=m.policy_exposure_score,
        technology_readiness=m.technology_readiness,
        flood_risk=m.flood_risk,
        heat_stress=m.heat_stress,
        water_stress=m.water_stress,
        supply_chain_exposure=m.supply_chain_exposure,
        sbti_committed=m.sbti_committed,
        taxonomy_aligned_pct=m.taxonomy_aligned_pct,
        transition_plan_quality=m.transition_plan_quality,
        disclosure_level=m.disclosure_level,
        data_recency_years=m.data_recency_years,
        third_party_verified=m.third_party_verified,
    )


def _breakdown_response(bd) -> ScoreBreakdownResponse:
    return ScoreBreakdownResponse(
        component_name=bd.component_name,
        weight=bd.weight,
        raw_score=bd.raw_score,
        weighted_score=bd.weighted_score,
        sub_scores=bd.sub_scores,
        data_available=bd.data_available,
    )


def _score_to_response(r: ClimateScoreResult) -> CounterpartyScoreResponse:
    return CounterpartyScoreResponse(
        counterparty_id=r.counterparty_id,
        counterparty_name=r.counterparty_name,
        sector=r.sector,
        composite_score=r.composite_score,
        rating=r.rating,
        rating_label=r.rating_label,
        transition_risk=_breakdown_response(r.transition_risk),
        physical_risk=_breakdown_response(r.physical_risk),
        alignment=_breakdown_response(r.alignment),
        data_quality=_breakdown_response(r.data_quality),
        methodology_notes=r.methodology_notes,
    )


# ---------------------------------------------------------------------------
# GAR ENDPOINTS
# ---------------------------------------------------------------------------


@router.post("/calculate", response_model=GARCalculateResponse)
async def calculate_gar(request: GARCalculateRequest) -> GARCalculateResponse:
    """
    Calculate Green Asset Ratio from a bank's loan book.

    Returns GAR stock ratio (and optionally flow GAR for new originations),
    with breakdowns by EU Taxonomy objective, KPI type, and asset type.
    """
    try:
        calc = GARCalculator()
        exposures = [_to_gar_exposure(e) for e in request.exposures]
        flow = (
            [_to_gar_exposure(e) for e in request.flow_exposures]
            if request.flow_exposures
            else None
        )
        result = calc.calculate(exposures, flow)

        return GARCalculateResponse(
            gar_ratio=result.gar_ratio,
            gar_eligible_ratio=result.gar_eligible_ratio,
            gar_flow=result.gar_flow,
            total_assets=result.total_assets,
            excluded_assets=result.excluded_assets,
            covered_assets=result.covered_assets,
            aligned_assets=result.aligned_assets,
            eligible_assets=result.eligible_assets,
            not_eligible_assets=result.not_eligible_assets,
            by_objective=[
                ObjectiveBreakdownResponse(
                    objective=o.objective,
                    objective_label=o.objective_label,
                    aligned_amount=o.aligned_amount,
                    eligible_amount=o.eligible_amount,
                    not_eligible_amount=o.not_eligible_amount,
                    aligned_pct=o.aligned_pct,
                    eligible_pct=o.eligible_pct,
                )
                for o in result.by_objective
            ],
            by_kpi_type=[
                KPIBreakdownResponse(
                    kpi_type=k.kpi_type,
                    aligned_amount=k.aligned_amount,
                    eligible_amount=k.eligible_amount,
                    covered_assets=k.covered_assets,
                    gar_ratio=k.gar_ratio,
                )
                for k in result.by_kpi_type
            ],
            by_asset_type=[
                AssetTypeBreakdownResponse(
                    asset_type=a.asset_type,
                    total_amount=a.total_amount,
                    aligned_amount=a.aligned_amount,
                    eligible_amount=a.eligible_amount,
                    alignment_ratio=a.alignment_ratio,
                    count=a.count,
                )
                for a in result.by_asset_type
            ],
            assessed_pct=result.assessed_pct,
            not_assessed_count=result.not_assessed_count,
            exposure_count=result.exposure_count,
            methodology_notes=result.methodology_notes,
        )
    except Exception as e:
        logger.error("GAR calculation failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"GAR calculation failed: {str(e)}")


@router.get("/objectives")
async def get_objectives() -> Dict[str, Any]:
    """Return the 6 EU Taxonomy environmental objectives."""
    return {"objectives": GARCalculator.get_taxonomy_objectives()}


@router.get("/nace-mapping")
async def get_nace_mapping(
    nace_code: Optional[str] = Query(None, description="Filter by specific NACE code"),
) -> Dict[str, Any]:
    """
    Return NACE sector code to taxonomy objective mapping.

    Optionally filter by a specific NACE code to see its eligible objectives.
    """
    if nace_code:
        objectives = get_eligible_objectives(nace_code)
        return {
            "nace_code": nace_code,
            "eligible_objectives": objectives,
            "is_mapped": len(objectives) > 0,
        }
    return {"nace_mapping": GARCalculator.get_nace_taxonomy_map()}


@router.get("/excluded-types")
async def get_excluded_types() -> Dict[str, Any]:
    """Return asset types excluded from GAR denominator."""
    return {"excluded_types": GARCalculator.get_excluded_asset_types()}


@router.get("/kpi-types")
async def get_kpi_types() -> Dict[str, Any]:
    """Return CRR2 ITS KPI types (Turnover, CapEx, OpEx)."""
    return {"kpi_types": GARCalculator.get_kpi_types()}


@router.get("/alignment-classifications")
async def get_alignment_classifications() -> Dict[str, Any]:
    """Return possible alignment classification values."""
    return {"classifications": GARCalculator.get_alignment_classifications()}


# ---------------------------------------------------------------------------
# COUNTERPARTY CLIMATE SCORE ENDPOINTS
# ---------------------------------------------------------------------------


@router.post("/counterparty/score", response_model=CounterpartyScoreResponse)
async def score_counterparty(
    request: CounterpartyScoreRequest,
) -> CounterpartyScoreResponse:
    """
    Calculate composite climate risk score for a single counterparty.

    Returns a 0-100 score (higher = better) mapped to A+ through D- rating,
    with breakdown by transition risk, physical risk, alignment, and data quality.
    """
    try:
        scorer = CounterpartyClimateScorer()
        inp = _to_counterparty_input(request)
        result = scorer.score(inp)
        return _score_to_response(result)
    except Exception as e:
        logger.error("Climate score failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Climate scoring failed: {str(e)}")


@router.post("/counterparty/batch", response_model=List[CounterpartyScoreResponse])
async def score_counterparty_batch(
    request: CounterpartyBatchRequest,
) -> List[CounterpartyScoreResponse]:
    """
    Batch climate scoring for multiple counterparties.

    Optionally provide custom_weights to override default component weights.
    """
    try:
        scorer = CounterpartyClimateScorer(weights=request.custom_weights)
        inputs = [_to_counterparty_input(c) for c in request.counterparties]
        results = scorer.score_batch(inputs)
        return [_score_to_response(r) for r in results]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Batch climate scoring failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Batch scoring failed: {str(e)}")


@router.get("/counterparty/sector-risk")
async def get_sector_risk() -> Dict[str, Any]:
    """Return sector-level transition risk classifications."""
    return {"sector_risk_levels": CounterpartyClimateScorer.get_sector_risk_levels()}


@router.get("/counterparty/rating-scale")
async def get_rating_scale() -> Dict[str, Any]:
    """Return the score-to-rating mapping (A+ through D-)."""
    return {"rating_scale": CounterpartyClimateScorer.get_rating_scale()}


@router.get("/counterparty/weights")
async def get_scoring_weights() -> Dict[str, Any]:
    """Return default scoring weights."""
    return {"weights": CounterpartyClimateScorer.get_default_weights()}


# ---------------------------------------------------------------------------
# DB-POWERED GAR AUTO-CALCULATION ENDPOINTS
# ---------------------------------------------------------------------------


def _get_gar_db_service():
    """Lazy-load GARDBService with DB engine."""
    from services.gar_db_service import GARDBService
    from db.base import engine as db_engine
    return GARDBService(db_engine)


@router.get(
    "/auto-calculate/{entity_id}",
    summary="Auto-calculate GAR from DB data for an FI entity",
)
async def auto_calculate_gar(
    entity_id: str,
    reporting_year: int = Query(2024, description="Reporting year"),
    persist: bool = Query(True, description="Persist results to fi_eu_taxonomy_kpis"),
) -> Dict[str, Any]:
    """
    Auto-calculate Green Asset Ratio by pulling data from:
    - eu_taxonomy_assessments + eu_taxonomy_activities (alignment data)
    - fi_loan_books (exposure amounts / sector breakdown)

    Results are persisted to fi_eu_taxonomy_kpis unless persist=false.
    No manual exposure input required.
    """
    svc = _get_gar_db_service()
    return svc.calculate_gar_for_entity(
        entity_id=entity_id,
        reporting_year=reporting_year,
        persist=persist,
    )


@router.get(
    "/auto-calculate/by-lei/{lei}",
    summary="Auto-calculate GAR by LEI",
)
async def auto_calculate_gar_by_lei(
    lei: str,
    reporting_year: int = Query(2024, description="Reporting year"),
    persist: bool = Query(True, description="Persist results to fi_eu_taxonomy_kpis"),
) -> Dict[str, Any]:
    """
    Auto-calculate GAR by LEI — resolves to fi_entities, gathers taxonomy
    and loan book data, computes GAR, and persists results.
    """
    if len(lei) != 20:
        raise HTTPException(400, "LEI must be exactly 20 characters")
    svc = _get_gar_db_service()
    return svc.calculate_gar_by_lei(
        lei=lei,
        reporting_year=reporting_year,
        persist=persist,
    )
