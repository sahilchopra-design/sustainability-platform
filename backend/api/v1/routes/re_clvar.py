"""
Real Estate CLVaR and CRREM Stranding Routes
Endpoints for property-level climate value-at-risk and carbon pathway assessment.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Real Estate CLVaR and CRREM"])


class PhysicalInputs(BaseModel):
    flood_zone: Optional[str] = Field(None, description="FEMA / EU flood zone code")
    coastal_proximity_km: Optional[float] = Field(None, ge=0)
    wildfire_risk_score: Optional[float] = Field(None, ge=0, le=10)
    heat_stress_days_2050: Optional[float] = Field(None, ge=0)
    wind_storm_exposure: Optional[str] = None
    subsidence_risk: Optional[str] = None
    annual_expected_loss_pct: Optional[float] = Field(None, ge=0, le=1)


class TransitionInputs(BaseModel):
    epc_rating: Optional[str] = Field(None, description="EPC label A-G")
    energy_intensity_kwh_m2: Optional[float] = Field(None, ge=0)
    carbon_intensity_kgco2_m2: Optional[float] = Field(None, ge=0)
    heating_system: Optional[str] = None
    glazing_type: Optional[str] = None
    solar_installed: bool = False
    heat_pump_installed: bool = False


class PropertyInfo(BaseModel):
    property_id: str
    address: Optional[str] = None
    property_type: str = Field(..., description="e.g. office, residential, retail, industrial")
    country_iso: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    gross_internal_area_m2: float = Field(..., gt=0)
    year_built: Optional[int] = None
    current_valuation_gbp: Optional[float] = Field(None, gt=0)
    loan_to_value: Optional[float] = Field(None, ge=0, le=1)


class PropertyCLVaRRequest(BaseModel):
    property_info: PropertyInfo
    physical_inputs: PhysicalInputs
    transition_inputs: TransitionInputs
    scenario: str = Field("1.5C", description="Climate scenario: 1.5C | 2C | 3C")
    horizon_years: int = Field(10, ge=1, le=30)


class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


class CLVaRResponse(BaseModel):
    property_id: str
    scenario: str
    horizon_years: int
    physical_clvar_pct: float
    transition_clvar_pct: float
    total_clvar_pct: float
    physical_clvar_gbp: Optional[float] = None
    transition_clvar_gbp: Optional[float] = None
    total_clvar_gbp: Optional[float] = None
    risk_rating: str
    top_risk_drivers: List[Dict[str, Any]] = []
    validation_summary: ValidationSummary


class CRREMRequest(BaseModel):
    property_info: PropertyInfo
    transition_inputs: TransitionInputs
    scenario: str = Field("1.5C", description="CRREM scenario: 1.5C | 2C")


class CRREMStrandingResponse(BaseModel):
    property_id: str
    property_type: str
    country_iso: str
    scenario: str
    stranding_year: Optional[int] = None
    is_stranded_today: bool
    current_intensity_kgco2_m2: float
    pathway_intensity_2030_kgco2_m2: float
    pathway_intensity_2050_kgco2_m2: float
    gap_to_pathway_today_pct: float
    estimated_retrofit_cost_gbp: Optional[float] = None
    validation_summary: ValidationSummary


class RoadmapYear(BaseModel):
    year: int
    target_intensity_kgco2_m2: float
    required_reduction_pct: float
    recommended_measures: List[str] = []
    estimated_cost_gbp: Optional[float] = None


class CRREMRoadmapResponse(BaseModel):
    property_id: str
    scenario: str
    roadmap: List[RoadmapYear]
    total_estimated_cost_gbp: Optional[float] = None
    validation_summary: ValidationSummary


class PortfolioPropertyResult(BaseModel):
    property_id: str
    total_clvar_pct: float
    total_clvar_gbp: Optional[float] = None
    risk_rating: str
    stranding_year: Optional[int] = None


class PortfolioCLVaRRequest(BaseModel):
    properties: List[PropertyCLVaRRequest]
    scenario: str = "1.5C"
    horizon_years: int = 10


class PortfolioCLVaRResponse(BaseModel):
    scenario: str
    horizon_years: int
    total_properties: int
    per_property: List[PortfolioPropertyResult]
    portfolio_weighted_clvar_pct: float
    total_portfolio_clvar_gbp: Optional[float] = None
    risk_distribution: Dict[str, int]
    validation_summary: ValidationSummary


class CRREMPathwayYear(BaseModel):
    year: int
    intensity_15c_kgco2_m2: float
    intensity_2c_kgco2_m2: float


class CRREMPathwayResponse(BaseModel):
    property_type: str
    country_iso: str
    pathway: List[CRREMPathwayYear]
    source: str
    validation_summary: ValidationSummary


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


@router.post("/re/clvar/calculate", response_model=CLVaRResponse)
async def calculate_re_clvar(request: PropertyCLVaRRequest):
    """Run CLVaR for a single property across physical and transition risk dimensions."""
    logger.info("CLVaR: property=%s scenario=%s horizon=%d yr",
                request.property_info.property_id, request.scenario, request.horizon_years)
    try:
        from services.re_clvar_engine import RECLVaREngine  # type: ignore
        result = RECLVaREngine().calculate(
            property_info=request.property_info.model_dump(),
            physical_inputs=request.physical_inputs.model_dump(),
            transition_inputs=request.transition_inputs.model_dump(),
            scenario=request.scenario, horizon_years=request.horizon_years,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return CLVaRResponse(
            property_id=request.property_info.property_id,
            scenario=request.scenario, horizon_years=request.horizon_years,
            physical_clvar_pct=result["physical_clvar_pct"],
            transition_clvar_pct=result["transition_clvar_pct"],
            total_clvar_pct=result["total_clvar_pct"],
            physical_clvar_gbp=result.get("physical_clvar_gbp"),
            transition_clvar_gbp=result.get("transition_clvar_gbp"),
            total_clvar_gbp=result.get("total_clvar_gbp"),
            risk_rating=result["risk_rating"],
            top_risk_drivers=result.get("top_risk_drivers", []),
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("CLVaR engine error: property=%s", request.property_info.property_id)
        raise HTTPException(status_code=500, detail=f"CLVaR engine error: {exc}") from exc


@router.post("/re/crrem/stranding", response_model=CRREMStrandingResponse)
async def assess_crrem_stranding(request: CRREMRequest):
    """Assess CRREM stranding risk for a property against the decarbonisation pathway."""
    logger.info("CRREM stranding: property=%s scenario=%s",
                request.property_info.property_id, request.scenario)
    try:
        from services.crrem_stranding_engine import CRREMStrandingEngine  # type: ignore
        result = CRREMStrandingEngine().assess_stranding(
            property_info=request.property_info.model_dump(),
            transition_inputs=request.transition_inputs.model_dump(),
            scenario=request.scenario,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return CRREMStrandingResponse(
            property_id=request.property_info.property_id,
            property_type=request.property_info.property_type,
            country_iso=request.property_info.country_iso,
            scenario=request.scenario,
            stranding_year=result.get("stranding_year"),
            is_stranded_today=result["is_stranded_today"],
            current_intensity_kgco2_m2=result["current_intensity_kgco2_m2"],
            pathway_intensity_2030_kgco2_m2=result["pathway_intensity_2030_kgco2_m2"],
            pathway_intensity_2050_kgco2_m2=result["pathway_intensity_2050_kgco2_m2"],
            gap_to_pathway_today_pct=result["gap_to_pathway_today_pct"],
            estimated_retrofit_cost_gbp=result.get("estimated_retrofit_cost_gbp"),
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("CRREM stranding error: property=%s", request.property_info.property_id)
        raise HTTPException(status_code=500, detail=f"CRREM stranding engine error: {exc}") from exc


@router.post("/re/crrem/roadmap", response_model=CRREMRoadmapResponse)
async def generate_crrem_roadmap(request: CRREMRequest):
    """Generate a year-by-year decarbonisation roadmap to 2050 for a property."""
    logger.info("CRREM roadmap: property=%s scenario=%s",
                request.property_info.property_id, request.scenario)
    try:
        from services.crrem_stranding_engine import CRREMStrandingEngine  # type: ignore
        result = CRREMStrandingEngine().generate_roadmap(
            property_info=request.property_info.model_dump(),
            transition_inputs=request.transition_inputs.model_dump(),
            scenario=request.scenario,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return CRREMRoadmapResponse(
            property_id=request.property_info.property_id, scenario=request.scenario,
            roadmap=[RoadmapYear(**yr) for yr in result.get("roadmap", [])],
            total_estimated_cost_gbp=result.get("total_estimated_cost_gbp"),
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("CRREM roadmap error: property=%s", request.property_info.property_id)
        raise HTTPException(status_code=500, detail=f"CRREM roadmap engine error: {exc}") from exc


@router.post("/re/clvar/portfolio", response_model=PortfolioCLVaRResponse)
async def calculate_portfolio_clvar(request: PortfolioCLVaRRequest):
    """Run CLVaR for a portfolio of properties and return per-property and aggregate results."""
    logger.info("Portfolio CLVaR: %d properties scenario=%s",
                len(request.properties), request.scenario)
    if not request.properties:
        raise HTTPException(status_code=400, detail="Portfolio must contain at least one property.")
    try:
        from services.re_clvar_engine import RECLVaREngine  # type: ignore
        engine = RECLVaREngine()
        per_property: List[PortfolioPropertyResult] = []
        all_warnings: List[str] = []
        all_missing: List[str] = []
        total_wclvar = 0.0
        total_gbp_sum: Optional[float] = 0.0
        risk_dist: Dict[str, int] = {"Low": 0, "Medium": 0, "High": 0, "Very High": 0}
        for prop_req in request.properties:
            result = engine.calculate(
                property_info=prop_req.property_info.model_dump(),
                physical_inputs=prop_req.physical_inputs.model_dump(),
                transition_inputs=prop_req.transition_inputs.model_dump(),
                scenario=request.scenario, horizon_years=request.horizon_years,
            )
            gbp = result.get("total_clvar_gbp")
            if gbp is None:
                total_gbp_sum = None
            elif total_gbp_sum is not None:
                total_gbp_sum += gbp
            per_property.append(PortfolioPropertyResult(
                property_id=prop_req.property_info.property_id,
                total_clvar_pct=result["total_clvar_pct"], total_clvar_gbp=gbp,
                risk_rating=result["risk_rating"], stranding_year=result.get("stranding_year"),
            ))
            total_wclvar += result["total_clvar_pct"]
            all_warnings.extend(result.get("warnings", []))
            all_missing.extend(result.get("missing_fields", []))
            risk_dist[result["risk_rating"]] = risk_dist.get(result["risk_rating"], 0) + 1
        val = _build_validation_summary(list(set(all_warnings)), list(set(all_missing)))
        return PortfolioCLVaRResponse(
            scenario=request.scenario, horizon_years=request.horizon_years,
            total_properties=len(request.properties), per_property=per_property,
            portfolio_weighted_clvar_pct=round(total_wclvar / len(request.properties), 4),
            total_portfolio_clvar_gbp=(
                round(total_gbp_sum, 2) if total_gbp_sum is not None else None
            ),
            risk_distribution=risk_dist, validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Portfolio CLVaR engine error")
        raise HTTPException(status_code=500, detail=f"Portfolio CLVaR engine error: {exc}") from exc


@router.get("/re/crrem/pathways/{property_type}/{country_iso}", response_model=CRREMPathwayResponse)
async def get_crrem_pathways(property_type: str, country_iso: str):
    """Retrieve CRREM pathway data (year-by-year 1.5C and 2C intensity targets)."""
    logger.info("CRREM pathway lookup: type=%s country=%s", property_type, country_iso)
    try:
        from services.crrem_stranding_engine import CRREMStrandingEngine  # type: ignore
        result = CRREMStrandingEngine().get_pathway(
            property_type=property_type, country_iso=country_iso,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return CRREMPathwayResponse(
            property_type=property_type, country_iso=country_iso.upper(),
            pathway=[CRREMPathwayYear(**yr) for yr in result.get("pathway", [])],
            source=result.get("source", "CRREM v2"), validation_summary=val,
        )
    except Exception as exc:
        logger.exception("CRREM pathway error: type=%s country=%s", property_type, country_iso)
        raise HTTPException(status_code=500, detail=f"CRREM pathway engine error: {exc}") from exc
