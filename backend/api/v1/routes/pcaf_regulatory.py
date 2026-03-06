"""
PCAF, SFDR and EU Taxonomy Routes
Endpoints for financed emissions, SFDR PAI indicators and EU Taxonomy alignment.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["PCAF / SFDR / EU Taxonomy"])


class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


class InvesteeEntry(BaseModel):
    investee_id: str
    name: Optional[str] = None
    sector: str
    country_iso: str
    investment_value_gbp: float = Field(..., gt=0)
    enterprise_value_gbp: Optional[float] = Field(None, gt=0)
    revenue_gbp: Optional[float] = Field(None, gt=0)
    scope1_tco2e: Optional[float] = Field(None, ge=0)
    scope2_tco2e: Optional[float] = Field(None, ge=0)
    scope3_tco2e: Optional[float] = Field(None, ge=0)
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class PCAFRequest(BaseModel):
    investees: List[InvesteeEntry]
    reporting_year: int = Field(..., ge=2000, le=2100)
    asset_class: str = Field(
        "listed_equity",
        description="listed_equity | corporate_bonds | loans | real_estate",
    )


class InvesteeEmissions(BaseModel):
    investee_id: str
    financed_emissions_tco2e: float
    attribution_factor: float
    pcaf_data_quality_score: int
    scope1_attributed: float
    scope2_attributed: float
    scope3_attributed: Optional[float] = None


class PCAFResponse(BaseModel):
    reporting_year: int
    asset_class: str
    total_financed_emissions_tco2e: float
    waci_tco2e_per_mrevenue: float
    carbon_footprint_tco2e_per_minvested: float
    implied_temperature_rise_c: Optional[float] = None
    per_investee: List[InvesteeEmissions]
    validation_summary: ValidationSummary


class SFDRPAIRequest(BaseModel):
    investees: List[InvesteeEntry]
    reporting_year: int = Field(..., ge=2000, le=2100)
    reference_year: Optional[int] = None


class PAIIndicator(BaseModel):
    indicator_id: str
    indicator_name: str
    value: Optional[float] = None
    unit: str
    data_quality_score: float = Field(..., ge=0, le=1)
    coverage_pct: float = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class SFDRPAIResponse(BaseModel):
    reporting_year: int
    mandatory_indicators: List[PAIIndicator]
    optional_indicators: List[PAIIndicator]
    overall_data_coverage_pct: float
    validation_summary: ValidationSummary


class ActivityBreakdown(BaseModel):
    activity_code: str
    activity_name: str
    turnover_pct: float = Field(..., ge=0, le=100)
    capex_pct: float = Field(..., ge=0, le=100)
    opex_pct: Optional[float] = Field(None, ge=0, le=100)
    substantial_contribution_objective: Optional[str] = None


class EntityTaxonomyEntry(BaseModel):
    entity_id: str
    name: Optional[str] = None
    sector: str
    country_iso: str
    activities: List[ActivityBreakdown]
    total_revenue_gbp: Optional[float] = None
    total_capex_gbp: Optional[float] = None


class TaxonomyAlignmentRequest(BaseModel):
    entities: List[EntityTaxonomyEntry]
    reporting_year: int = Field(..., ge=2000, le=2100)


class ObjectiveAlignment(BaseModel):
    objective: str
    eligible_turnover_pct: float
    aligned_turnover_pct: float
    eligible_capex_pct: float
    aligned_capex_pct: float
    dnsh_compliant: bool


class TaxonomyAlignmentResponse(BaseModel):
    reporting_year: int
    total_entities: int
    portfolio_eligible_turnover_pct: float
    portfolio_aligned_turnover_pct: float
    portfolio_eligible_capex_pct: float
    portfolio_aligned_capex_pct: float
    by_objective: List[ObjectiveAlignment]
    validation_summary: ValidationSummary


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


@router.post("/pcaf/financed-emissions", response_model=PCAFResponse)
async def calculate_financed_emissions(request: PCAFRequest):
    """Calculate PCAF-compliant financed emissions, WACI and carbon footprint for a portfolio."""
    logger.info("PCAF financed emissions: %d investees year=%d asset_class=%s",
                len(request.investees), request.reporting_year, request.asset_class)
    if not request.investees:
        raise HTTPException(status_code=400, detail="At least one investee is required.")
    try:
        from services.pcaf_waci_engine import PCAFWACIEngine  # type: ignore
        result = PCAFWACIEngine().calculate_financed_emissions(
            investees=[i.model_dump() for i in request.investees],
            reporting_year=request.reporting_year,
            asset_class=request.asset_class,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return PCAFResponse(
            reporting_year=request.reporting_year,
            asset_class=request.asset_class,
            total_financed_emissions_tco2e=result["total_financed_emissions_tco2e"],
            waci_tco2e_per_mrevenue=result["waci_tco2e_per_mrevenue"],
            carbon_footprint_tco2e_per_minvested=result["carbon_footprint_tco2e_per_minvested"],
            implied_temperature_rise_c=result.get("implied_temperature_rise_c"),
            per_investee=[InvesteeEmissions(**e) for e in result.get("per_investee", [])],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("PCAF financed emissions engine error")
        raise HTTPException(status_code=500, detail=f"PCAF engine error: {exc}") from exc


@router.post("/sfdr/pai", response_model=SFDRPAIResponse)
async def calculate_sfdr_pai(request: SFDRPAIRequest):
    """Calculate all 14 mandatory SFDR Principal Adverse Impact indicators for a portfolio."""
    logger.info("SFDR PAI: %d investees year=%d", len(request.investees), request.reporting_year)
    if not request.investees:
        raise HTTPException(status_code=400, detail="At least one investee is required.")
    try:
        from services.pcaf_waci_engine import PCAFWACIEngine  # type: ignore
        result = PCAFWACIEngine().calculate_sfdr_pai(
            investees=[i.model_dump() for i in request.investees],
            reporting_year=request.reporting_year,
            reference_year=request.reference_year,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return SFDRPAIResponse(
            reporting_year=request.reporting_year,
            mandatory_indicators=[PAIIndicator(**i) for i in result.get("mandatory_indicators", [])],
            optional_indicators=[PAIIndicator(**i) for i in result.get("optional_indicators", [])],
            overall_data_coverage_pct=result.get("overall_data_coverage_pct", 0.0),
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("SFDR PAI engine error")
        raise HTTPException(status_code=500, detail=f"SFDR PAI engine error: {exc}") from exc


@router.post("/eu-taxonomy/alignment", response_model=TaxonomyAlignmentResponse)
async def assess_eu_taxonomy_alignment(request: TaxonomyAlignmentRequest):
    """Assess EU Taxonomy eligibility and alignment with DNSH compliance by objective."""
    logger.info("EU Taxonomy alignment: %d entities year=%d",
                len(request.entities), request.reporting_year)
    if not request.entities:
        raise HTTPException(status_code=400, detail="At least one entity is required.")
    try:
        from services.pcaf_waci_engine import PCAFWACIEngine  # type: ignore
        result = PCAFWACIEngine().assess_taxonomy_alignment(
            entities=[e.model_dump() for e in request.entities],
            reporting_year=request.reporting_year,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return TaxonomyAlignmentResponse(
            reporting_year=request.reporting_year,
            total_entities=len(request.entities),
            portfolio_eligible_turnover_pct=result["portfolio_eligible_turnover_pct"],
            portfolio_aligned_turnover_pct=result["portfolio_aligned_turnover_pct"],
            portfolio_eligible_capex_pct=result["portfolio_eligible_capex_pct"],
            portfolio_aligned_capex_pct=result["portfolio_aligned_capex_pct"],
            by_objective=[ObjectiveAlignment(**o) for o in result.get("by_objective", [])],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("EU Taxonomy alignment engine error")
        raise HTTPException(status_code=500, detail=f"EU Taxonomy engine error: {exc}") from exc
