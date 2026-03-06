"""
Supply Chain Scope 3 Emissions Routes
Endpoints for Scope 3 calculation, SBTi target trajectory and emission factor lookup.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Supply Chain Scope 3"])


class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


class ActivityEntry(BaseModel):
    description: Optional[str] = None
    quantity: float = Field(..., ge=0)
    unit: str
    emission_factor_kgco2e_per_unit: Optional[float] = Field(None, ge=0)
    supplier_country_iso: Optional[str] = None
    spend_gbp: Optional[float] = Field(None, ge=0)


class Scope3CalculateRequest(BaseModel):
    entity_id: str
    reporting_year: int = Field(..., ge=2000, le=2100)
    activities_by_category: Dict[str, List[ActivityEntry]] = Field(
        ...,
        description=(
            "GHG Protocol Scope 3 category labels as keys, "
            "e.g. cat1_purchased_goods, cat4_upstream_transport"
        ),
    )
    include_hotspot_analysis: bool = True


class CategoryResult(BaseModel):
    category: str
    total_tco2e: float
    pct_of_total: float
    data_quality_score: float
    hotspot_flag: bool
    top_activities: List[Dict[str, Any]]


class HotspotEntry(BaseModel):
    category: str
    activity: str
    tco2e: float
    pct_of_total: float
    recommended_action: str


class Scope3CalculateResponse(BaseModel):
    entity_id: str
    reporting_year: int
    total_scope3_tco2e: float
    by_category: List[CategoryResult]
    hotspots: List[HotspotEntry]
    validation_summary: ValidationSummary


class SBTiTargetRequest(BaseModel):
    entity_id: str
    base_year: int = Field(..., ge=2000, le=2030)
    base_year_emissions_tco2e: float = Field(..., gt=0)
    target_year: int = Field(..., ge=2025, le=2050)
    reduction_pct: float = Field(..., ge=0, le=100,
                                 description="Absolute reduction % from base year")
    sbti_pathway: str = Field("1.5C", description="1.5C | well-below-2C | 2C")


class MilestoneYear(BaseModel):
    year: int
    target_tco2e: float
    required_annual_reduction_pct: float
    on_track_indicator: str


class SBTiTargetResponse(BaseModel):
    entity_id: str
    base_year: int
    base_year_emissions_tco2e: float
    target_year: int
    reduction_pct: float
    sbti_pathway: str
    milestones: List[MilestoneYear]
    cagr_required_pct: float
    validation_summary: ValidationSummary


class EmissionFactor(BaseModel):
    factor_id: str
    sector: str
    category: str
    activity_description: str
    unit: str
    kgco2e_per_unit: float
    source: str
    year: int
    country_iso: Optional[str] = None


class EmissionFactorListResponse(BaseModel):
    total_count: int
    filters_applied: Dict[str, Optional[str]]
    factors: List[EmissionFactor]
    validation_summary: ValidationSummary


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


@router.post("/supply-chain/scope3/calculate", response_model=Scope3CalculateResponse)
async def calculate_scope3(request: Scope3CalculateRequest):
    """Calculate Scope 3 emissions by GHG Protocol category with optional hotspot analysis."""
    logger.info("Scope 3 calculation: entity=%s year=%d categories=%d",
                request.entity_id, request.reporting_year, len(request.activities_by_category))
    if not request.activities_by_category:
        raise HTTPException(status_code=400, detail="activities_by_category must not be empty.")
    try:
        from services.supply_chain_scope3_engine import SupplyChainScope3Engine  # type: ignore
        result = SupplyChainScope3Engine().calculate_scope3(
            entity_id=request.entity_id,
            reporting_year=request.reporting_year,
            activities_by_category={
                cat: [a.model_dump() for a in acts]
                for cat, acts in request.activities_by_category.items()
            },
            include_hotspot_analysis=request.include_hotspot_analysis,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return Scope3CalculateResponse(
            entity_id=request.entity_id,
            reporting_year=request.reporting_year,
            total_scope3_tco2e=result["total_scope3_tco2e"],
            by_category=[CategoryResult(**c) for c in result.get("by_category", [])],
            hotspots=[HotspotEntry(**h) for h in result.get("hotspots", [])],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Scope 3 engine error: entity=%s", request.entity_id)
        raise HTTPException(status_code=500, detail=f"Scope 3 engine error: {exc}") from exc


@router.post("/supply-chain/scope3/sbti-target", response_model=SBTiTargetResponse)
async def calculate_sbti_target(request: SBTiTargetRequest):
    """Calculate SBTi-aligned Scope 3 reduction target trajectory with annual milestones."""
    logger.info("SBTi target: entity=%s base_year=%d target_year=%d pathway=%s",
                request.entity_id, request.base_year, request.target_year, request.sbti_pathway)
    try:
        from services.supply_chain_scope3_engine import SupplyChainScope3Engine  # type: ignore
        result = SupplyChainScope3Engine().calculate_sbti_target(
            entity_id=request.entity_id,
            base_year=request.base_year,
            base_year_emissions_tco2e=request.base_year_emissions_tco2e,
            target_year=request.target_year,
            reduction_pct=request.reduction_pct,
            sbti_pathway=request.sbti_pathway,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return SBTiTargetResponse(
            entity_id=request.entity_id,
            base_year=request.base_year,
            base_year_emissions_tco2e=request.base_year_emissions_tco2e,
            target_year=request.target_year,
            reduction_pct=request.reduction_pct,
            sbti_pathway=request.sbti_pathway,
            milestones=[MilestoneYear(**m) for m in result.get("milestones", [])],
            cagr_required_pct=result["cagr_required_pct"],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("SBTi target engine error: entity=%s", request.entity_id)
        raise HTTPException(status_code=500, detail=f"SBTi target engine error: {exc}") from exc


@router.get("/supply-chain/emission-factors", response_model=EmissionFactorListResponse)
async def list_emission_factors(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    category: Optional[str] = Query(None, description="Filter by Scope 3 category"),
    country_iso: Optional[str] = Query(None, description="Filter by country ISO code"),
    year: Optional[int] = Query(None, description="Filter by reference year"),
):
    """List available emission factors, optionally filtered by sector, category or country."""
    logger.info("Emission factor lookup: sector=%s category=%s country=%s year=%s",
                sector, category, country_iso, year)
    try:
        from services.supply_chain_scope3_engine import SupplyChainScope3Engine  # type: ignore
        result = SupplyChainScope3Engine().list_emission_factors(
            sector=sector, category=category, country_iso=country_iso, year=year,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        factors = [EmissionFactor(**f) for f in result.get("factors", [])]
        return EmissionFactorListResponse(
            total_count=len(factors),
            filters_applied={
                "sector": sector, "category": category,
                "country_iso": country_iso, "year": str(year) if year else None,
            },
            factors=factors,
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Emission factor listing engine error")
        raise HTTPException(status_code=500, detail=f"Emission factor engine error: {exc}") from exc
