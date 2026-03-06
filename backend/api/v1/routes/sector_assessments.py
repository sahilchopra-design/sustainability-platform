"""
Sector-Specific ESG Assessment Routes
Endpoints for data centres, insurance CAT risk and power plant decarbonisation.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Sector ESG Assessments"])


class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


# ---------------------------------------------------------------------------
# Data Centre models
# ---------------------------------------------------------------------------

class DataCenterRequest(BaseModel):
    facility_id: str
    location: Optional[str] = None
    grid_region: str = Field(..., description="e.g. UK_NATIONAL, EU_DE, US_ERCOT")
    pue: float = Field(..., ge=1.0, le=5.0, description="Power Usage Effectiveness")
    wue: Optional[float] = Field(None, ge=0, description="Water Usage Effectiveness (L/kWh)")
    total_it_load_mw: float = Field(..., gt=0)
    annual_energy_consumption_mwh: float = Field(..., gt=0)
    renewable_energy_pct: float = Field(0.0, ge=0, le=100)
    has_renewable_ppa: bool = False
    cooling_type: Optional[str] = Field(None, description="e.g. air, liquid, free_cooling")


class EfficiencyBenchmark(BaseModel):
    metric: str
    current_value: float
    industry_average: float
    best_in_class: float
    score_0_to_100: float
    gap_to_best_in_class: float


class ImprovementTarget(BaseModel):
    measure: str
    potential_reduction_pct: float
    estimated_cost_gbp: Optional[float] = None
    payback_years: Optional[float] = None
    priority: str


class DataCenterResponse(BaseModel):
    facility_id: str
    overall_efficiency_score: float = Field(..., ge=0, le=100)
    carbon_intensity_kgco2_per_mwh_it: float
    annual_co2e_tonnes: float
    renewable_coverage_pct: float
    efficiency_benchmarks: List[EfficiencyBenchmark]
    improvement_targets: List[ImprovementTarget]
    validation_summary: ValidationSummary


# ---------------------------------------------------------------------------
# CAT Risk models
# ---------------------------------------------------------------------------

class CATRiskRequest(BaseModel):
    property_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country_iso: str
    peril: str = Field(..., description="e.g. flood, windstorm, earthquake, wildfire, hail")
    property_value_gbp: float = Field(..., gt=0)
    construction_type: Optional[str] = Field(None, description="e.g. masonry, timber, steel_frame")
    year_built: Optional[int] = None
    return_period_years: List[int] = Field(default=[50, 100, 200, 250])
    climate_scenario: str = Field("RCP4.5", description="RCP2.6 | RCP4.5 | RCP8.5")
    climate_horizon_year: int = Field(2050, ge=2025, le=2100)


class PMLEstimate(BaseModel):
    return_period_years: int
    pml_gbp: float
    pml_pct_of_value: float
    climate_adjusted_pml_gbp: float
    climate_uplift_pct: float


class CATRiskResponse(BaseModel):
    property_id: str
    peril: str
    climate_scenario: str
    climate_horizon_year: int
    annual_average_loss_gbp: float
    climate_adjusted_aal_gbp: float
    aal_uplift_pct: float
    pml_estimates: List[PMLEstimate]
    insurability_score: float = Field(..., ge=0, le=100)
    insurability_label: str
    key_risk_drivers: List[str]
    validation_summary: ValidationSummary


# ---------------------------------------------------------------------------
# Power Plant models
# ---------------------------------------------------------------------------

class PlantDecarbRequest(BaseModel):
    plant_id: str
    plant_type: str = Field(
        ..., description="e.g. coal, gas_ccgt, gas_peaker, oil, biomass, nuclear"
    )
    country_iso: str
    installed_capacity_mw: float = Field(..., gt=0)
    current_load_factor_pct: float = Field(..., ge=0, le=100)
    current_emission_intensity_gco2_kwh: float = Field(..., ge=0)
    year_commissioned: Optional[int] = None
    remaining_asset_life_years: Optional[int] = Field(None, ge=0)
    ccs_installed: bool = False
    ccs_capture_rate_pct: Optional[float] = Field(None, ge=0, le=100)


class RoadmapStep(BaseModel):
    year: int
    iea_nze_pathway_gco2_kwh: float
    plant_projected_gco2_kwh: float
    gap_gco2_kwh: float
    recommended_action: Optional[str] = None
    estimated_capex_gbp_million: Optional[float] = None


class PlantDecarbResponse(BaseModel):
    plant_id: str
    plant_type: str
    country_iso: str
    current_emission_intensity_gco2_kwh: float
    iea_nze_2030_target_gco2_kwh: float
    iea_nze_2050_target_gco2_kwh: float
    gap_to_pathway_today_pct: float
    stranding_year: Optional[int] = None
    years_to_stranding: Optional[int] = None
    paris_aligned: bool
    decarbonisation_roadmap: List[RoadmapStep]
    total_estimated_capex_gbp_million: Optional[float] = None
    validation_summary: ValidationSummary


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


@router.post("/sector/technology/data-center", response_model=DataCenterResponse)
async def assess_data_center(request: DataCenterRequest):
    """Assess data centre environmental metrics vs benchmarks and generate improvement targets."""
    logger.info("Data centre assessment: facility=%s pue=%.2f renewable=%.1f%%",
                request.facility_id, request.pue, request.renewable_energy_pct)
    try:
        from services.sector_assessment_engine import SectorAssessmentEngine  # type: ignore
        result = SectorAssessmentEngine().assess_data_center(
            facility_id=request.facility_id,
            grid_region=request.grid_region,
            pue=request.pue,
            wue=request.wue,
            total_it_load_mw=request.total_it_load_mw,
            annual_energy_consumption_mwh=request.annual_energy_consumption_mwh,
            renewable_energy_pct=request.renewable_energy_pct,
            has_renewable_ppa=request.has_renewable_ppa,
            cooling_type=request.cooling_type,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return DataCenterResponse(
            facility_id=request.facility_id,
            overall_efficiency_score=result["overall_efficiency_score"],
            carbon_intensity_kgco2_per_mwh_it=result["carbon_intensity_kgco2_per_mwh_it"],
            annual_co2e_tonnes=result["annual_co2e_tonnes"],
            renewable_coverage_pct=result["renewable_coverage_pct"],
            efficiency_benchmarks=[EfficiencyBenchmark(**b) for b in result.get("efficiency_benchmarks", [])],
            improvement_targets=[ImprovementTarget(**t) for t in result.get("improvement_targets", [])],
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Data centre assessment error: facility=%s", request.facility_id)
        raise HTTPException(status_code=500, detail=f"Data centre assessment engine error: {exc}") from exc


@router.post("/sector/insurance/cat-risk", response_model=CATRiskResponse)
async def assess_cat_risk(request: CATRiskRequest):
    """Quick CAT risk scoring with PML estimates and climate-adjusted AAL for a property."""
    logger.info("CAT risk: property=%s peril=%s scenario=%s horizon=%d",
                request.property_id, request.peril, request.climate_scenario, request.climate_horizon_year)
    try:
        from services.sector_assessment_engine import SectorAssessmentEngine  # type: ignore
        result = SectorAssessmentEngine().assess_cat_risk(
            property_id=request.property_id,
            latitude=request.latitude, longitude=request.longitude,
            country_iso=request.country_iso, peril=request.peril,
            property_value_gbp=request.property_value_gbp,
            construction_type=request.construction_type,
            year_built=request.year_built,
            return_period_years=request.return_period_years,
            climate_scenario=request.climate_scenario,
            climate_horizon_year=request.climate_horizon_year,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return CATRiskResponse(
            property_id=request.property_id,
            peril=request.peril,
            climate_scenario=request.climate_scenario,
            climate_horizon_year=request.climate_horizon_year,
            annual_average_loss_gbp=result["annual_average_loss_gbp"],
            climate_adjusted_aal_gbp=result["climate_adjusted_aal_gbp"],
            aal_uplift_pct=result["aal_uplift_pct"],
            pml_estimates=[PMLEstimate(**p) for p in result.get("pml_estimates", [])],
            insurability_score=result["insurability_score"],
            insurability_label=result["insurability_label"],
            key_risk_drivers=result.get("key_risk_drivers", []),
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("CAT risk engine error: property=%s peril=%s", request.property_id, request.peril)
        raise HTTPException(status_code=500, detail=f"CAT risk engine error: {exc}") from exc


@router.post("/sector/energy/plant-decarbonisation", response_model=PlantDecarbResponse)
async def assess_plant_decarbonisation(request: PlantDecarbRequest):
    """Assess power plant Paris alignment vs IEA NZE pathway and generate a decarbonisation roadmap."""
    logger.info("Plant decarbonisation: plant=%s type=%s country=%s intensity=%.1f gCO2/kWh",
                request.plant_id, request.plant_type, request.country_iso,
                request.current_emission_intensity_gco2_kwh)
    try:
        from services.sector_assessment_engine import SectorAssessmentEngine  # type: ignore
        result = SectorAssessmentEngine().assess_plant_decarbonisation(
            plant_id=request.plant_id,
            plant_type=request.plant_type,
            country_iso=request.country_iso,
            installed_capacity_mw=request.installed_capacity_mw,
            current_load_factor_pct=request.current_load_factor_pct,
            current_emission_intensity_gco2_kwh=request.current_emission_intensity_gco2_kwh,
            year_commissioned=request.year_commissioned,
            remaining_asset_life_years=request.remaining_asset_life_years,
            ccs_installed=request.ccs_installed,
            ccs_capture_rate_pct=request.ccs_capture_rate_pct,
        )
        val = _build_validation_summary(result.get("warnings", []), result.get("missing_fields", []))
        return PlantDecarbResponse(
            plant_id=request.plant_id,
            plant_type=request.plant_type,
            country_iso=request.country_iso,
            current_emission_intensity_gco2_kwh=request.current_emission_intensity_gco2_kwh,
            iea_nze_2030_target_gco2_kwh=result["iea_nze_2030_target_gco2_kwh"],
            iea_nze_2050_target_gco2_kwh=result["iea_nze_2050_target_gco2_kwh"],
            gap_to_pathway_today_pct=result["gap_to_pathway_today_pct"],
            stranding_year=result.get("stranding_year"),
            years_to_stranding=result.get("years_to_stranding"),
            paris_aligned=result["paris_aligned"],
            decarbonisation_roadmap=[RoadmapStep(**r) for r in result.get("decarbonisation_roadmap", [])],
            total_estimated_capex_gbp_million=result.get("total_estimated_capex_gbp_million"),
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Plant decarbonisation engine error: plant=%s", request.plant_id)
        raise HTTPException(status_code=500, detail=f"Plant decarbonisation engine error: {exc}") from exc
