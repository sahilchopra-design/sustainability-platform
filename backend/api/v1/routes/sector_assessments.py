"""
Sector-Specific ESG Assessment Routes
Endpoints for data centres, insurance CAT risk and power plant decarbonisation.
Inline computation + PostgreSQL persistence via SQLAlchemy.
"""
import json
import logging
import math
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Sector ESG Assessments"])


# ─────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────
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
    facility_name: Optional[str] = None
    assessment_year: Optional[int] = None
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
    assessment_id: Optional[str] = None


# ---------------------------------------------------------------------------
# CAT Risk models
# ---------------------------------------------------------------------------

class CATRiskRequest(BaseModel):
    property_id: str
    property_reference: Optional[str] = None
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
    assessment_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Power Plant models
# ---------------------------------------------------------------------------

class PlantDecarbRequest(BaseModel):
    plant_id: str
    plant_name: Optional[str] = None
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
    assessment_id: Optional[str] = None


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


# ─────────────────────────────────────────────────────────
# Data Centre computation constants
# ─────────────────────────────────────────────────────────
_GRID_EMISSION_FACTORS = {   # kgCO2/MWh
    "UK_NATIONAL": 207, "EU_DE": 385, "EU_FR": 56, "EU_NL": 340,
    "US_ERCOT": 410, "US_PJM": 380, "US_CAISO": 220, "US_MISO": 450,
    "SG": 408, "AU_NEM": 680, "IN_NATIONAL": 720, "JP": 470,
}
_PUE_INDUSTRY_AVG = 1.58
_PUE_BEST = 1.10
_WUE_INDUSTRY_AVG = 1.8  # L/kWh
_WUE_BEST = 0.2


# ─────────────────────────────────────────────────────────
# CAT Risk computation constants
# ─────────────────────────────────────────────────────────
# Base annual average loss rates by peril (% of property value)
_BASE_AAL_RATES = {
    "flood": 0.0035, "windstorm": 0.0025, "earthquake": 0.0020,
    "wildfire": 0.0015, "hail": 0.0010, "subsidence": 0.0008,
}

# Climate scenario uplift multipliers (applied to AAL)
_CLIMATE_SCENARIO_UPLIFT = {
    "RCP2.6": {"flood": 1.15, "windstorm": 1.10, "earthquake": 1.00, "wildfire": 1.20, "hail": 1.05},
    "RCP4.5": {"flood": 1.30, "windstorm": 1.20, "earthquake": 1.00, "wildfire": 1.45, "hail": 1.15},
    "RCP8.5": {"flood": 1.60, "windstorm": 1.40, "earthquake": 1.00, "wildfire": 1.90, "hail": 1.30},
}

# Construction vulnerability multipliers
_CONSTRUCTION_VULNERABILITY = {
    "masonry": 1.0, "timber": 1.3, "steel_frame": 0.8,
    "reinforced_concrete": 0.7, "modular": 1.1,
}


# ─────────────────────────────────────────────────────────
# Power Plant IEA NZE pathway (gCO2/kWh)
# ─────────────────────────────────────────────────────────
_IEA_NZE_PATHWAY = {
    2020: 460, 2025: 340, 2030: 138, 2035: 60, 2040: 25, 2045: 10, 2050: 0,
}

# Typical emission intensities by plant type (gCO2/kWh)
_PLANT_TYPE_DEFAULTS = {
    "coal": 900, "gas_ccgt": 360, "gas_peaker": 500,
    "oil": 650, "biomass": 50, "nuclear": 12,
}

# Annual natural efficiency degradation (gCO2/kWh per year)
_ANNUAL_DEGRADATION = {
    "coal": 2.0, "gas_ccgt": 1.0, "gas_peaker": 1.5,
    "oil": 1.5, "biomass": 0.5, "nuclear": 0.2,
}

# Decarbonisation actions by plant type
_DECARB_ACTIONS = {
    "coal": [
        (2026, "Install continuous emission monitoring systems", 2.0),
        (2028, "Co-firing with biomass (20%)", 15.0),
        (2030, "Full conversion to biomass or CCS retrofit", 150.0),
        (2035, "Phase out coal generation; replace with renewables + storage", 200.0),
    ],
    "gas_ccgt": [
        (2026, "Heat recovery optimisation", 1.5),
        (2028, "Hydrogen blending (10-20%)", 25.0),
        (2032, "CCS retrofit (90% capture)", 180.0),
        (2040, "Full hydrogen conversion or decommission", 100.0),
    ],
    "gas_peaker": [
        (2026, "Efficiency upgrade; reduce start-up emissions", 3.0),
        (2030, "Replace with battery storage + demand response", 80.0),
    ],
    "oil": [
        (2026, "Switch to gas (CCGT conversion)", 50.0),
        (2030, "CCS retrofit or decommission", 120.0),
    ],
    "biomass": [
        (2026, "Optimise feedstock supply chain sustainability", 1.0),
        (2030, "BECCS installation", 60.0),
    ],
    "nuclear": [
        (2030, "Life extension programme", 30.0),
        (2040, "SMR replacement evaluation", 80.0),
    ],
}


def _interpolate_nze(year: int) -> float:
    """Linear interpolation on the IEA NZE pathway."""
    years = sorted(_IEA_NZE_PATHWAY.keys())
    if year <= years[0]:
        return _IEA_NZE_PATHWAY[years[0]]
    if year >= years[-1]:
        return _IEA_NZE_PATHWAY[years[-1]]
    for i in range(len(years) - 1):
        if years[i] <= year <= years[i + 1]:
            frac = (year - years[i]) / (years[i + 1] - years[i])
            return _IEA_NZE_PATHWAY[years[i]] + frac * (_IEA_NZE_PATHWAY[years[i + 1]] - _IEA_NZE_PATHWAY[years[i]])
    return _IEA_NZE_PATHWAY[years[-1]]


# Efficiency rating from score
def _efficiency_rating(score: float) -> str:
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 35:
        return "D"
    else:
        return "E"


# ─────────────────────────────────────────────────────────
# DB persist helpers (non-blocking)
# ─────────────────────────────────────────────────────────
def _persist_dc_assessment(
    db: Session,
    facility_name: str,
    assessment_year: int,
    req: DataCenterRequest,
    resp_data: dict,
    benchmarks: List[EfficiencyBenchmark],
    targets: List[ImprovementTarget],
    validation_json: dict,
) -> Optional[str]:
    """Insert into data_centre_assessments. Returns assessment_id."""
    try:
        grid_ef = _GRID_EMISSION_FACTORS.get(req.grid_region, 350)
        improvement_json = [
            {"measure": t.measure, "reduction_pct": t.potential_reduction_pct,
             "cost_gbp": t.estimated_cost_gbp, "payback_years": t.payback_years,
             "priority": t.priority}
            for t in targets
        ]
        recommended_json = improvement_json  # same data for recommended_actions

        row = db.execute(text("""
            INSERT INTO data_centre_assessments
            (facility_name, assessment_year,
             total_it_load_mw, annual_energy_consumption_mwh,
             pue, wue, renewable_energy_pct,
             has_renewable_ppa,
             grid_emission_factor_kgco2e_kwh,
             carbon_intensity_kgco2e_kwh_it,
             annual_co2e_tco2e,
             efficiency_score, efficiency_rating,
             improvement_targets, recommended_actions,
             validation_summary, status)
            VALUES
            (:name, :yr,
             :it_load, :energy_mwh,
             :pue, :wue, :renewable_pct,
             :has_ppa,
             :grid_ef,
             :ci,
             :co2e,
             :score, :rating,
             CAST(:improvement AS jsonb), CAST(:recommended AS jsonb),
             CAST(:validation AS jsonb), 'draft')
            RETURNING id::text
        """), {
            "name": facility_name,
            "yr": assessment_year,
            "it_load": req.total_it_load_mw,
            "energy_mwh": req.annual_energy_consumption_mwh,
            "pue": req.pue,
            "wue": req.wue,
            "renewable_pct": req.renewable_energy_pct,
            "has_ppa": req.has_renewable_ppa,
            "grid_ef": grid_ef / 1000,  # convert kgCO2/MWh → kgCO2e/kWh
            "ci": resp_data["carbon_intensity_kgco2_per_mwh_it"] / 1000,  # per kWh
            "co2e": resp_data["annual_co2e_tonnes"],
            "score": resp_data["overall_efficiency_score"],
            "rating": _efficiency_rating(resp_data["overall_efficiency_score"]),
            "improvement": json.dumps(improvement_json),
            "recommended": json.dumps(recommended_json),
            "validation": json.dumps(validation_json),
        }).fetchone()

        db.commit()
        aid = row[0]
        logger.info("Persisted data centre assessment %s", aid)
        return aid
    except Exception:
        db.rollback()
        logger.warning("Non-blocking: failed to persist DC assessment", exc_info=True)
        return None


def _persist_cat_risk_assessment(
    db: Session,
    req: CATRiskRequest,
    aal: float,
    climate_aal: float,
    aal_uplift_pct: float,
    pml_estimates: List[PMLEstimate],
    risk_score: float,
    risk_category: str,
    validation_json: dict,
) -> Optional[str]:
    """Insert into cat_risk_assessments + cat_risk_climate_scenarios. Returns assessment_id."""
    try:
        # Map return period losses
        rp_losses = {}
        for p in pml_estimates:
            col = f"loss_1in{p.return_period_years}yr_gbp"
            rp_losses[col] = p.pml_gbp

        return_period_curve = [
            {"return_period_yr": p.return_period_years, "loss_gbp": p.pml_gbp,
             "climate_adjusted_gbp": p.climate_adjusted_pml_gbp}
            for p in pml_estimates
        ]

        # Find largest PML for the pml_gbp column (250yr)
        pml_250 = max((p.pml_gbp for p in pml_estimates), default=0)

        row = db.execute(text("""
            INSERT INTO cat_risk_assessments
            (property_reference, assessment_date, peril,
             property_value_gbp, aal_gbp,
             aal_pct_of_value, pml_gbp,
             return_period_curve,
             risk_score, risk_category,
             validation_summary, status)
            VALUES
            (:ref, CURRENT_DATE, :peril,
             :value, :aal,
             :aal_pct, :pml,
             CAST(:rp_curve AS jsonb),
             :risk_score, :risk_cat,
             CAST(:validation AS jsonb), 'draft')
            RETURNING id::text
        """), {
            "ref": req.property_reference or req.property_id,
            "peril": req.peril.lower(),
            "value": req.property_value_gbp,
            "aal": round(aal, 2),
            "aal_pct": round(aal / req.property_value_gbp * 100, 4) if req.property_value_gbp > 0 else 0,
            "pml": round(pml_250, 2),
            "rp_curve": json.dumps(return_period_curve),
            "risk_score": round(risk_score / 10, 2),  # convert 0-100 to 0-10
            "risk_cat": risk_category,
            "validation": json.dumps(validation_json),
        }).fetchone()
        assessment_id = row[0]

        # Insert climate scenario row
        db.execute(text("""
            INSERT INTO cat_risk_climate_scenarios
            (assessment_id, climate_scenario, time_horizon_year,
             aal_delta_pct, aal_climate_adjusted_gbp,
             pml_delta_pct, pml_climate_adjusted_gbp)
            VALUES
            (:aid, :scenario, :horizon,
             :aal_delta, :aal_adj,
             :pml_delta, :pml_adj)
        """), {
            "aid": assessment_id,
            "scenario": req.climate_scenario,
            "horizon": req.climate_horizon_year,
            "aal_delta": round(aal_uplift_pct, 3),
            "aal_adj": round(climate_aal, 2),
            "pml_delta": round(aal_uplift_pct, 3),
            "pml_adj": round(pml_250 * (1 + aal_uplift_pct / 100), 2) if pml_250 else 0,
        })

        db.commit()
        logger.info("Persisted CAT risk assessment %s", assessment_id)
        return assessment_id
    except Exception:
        db.rollback()
        logger.warning("Non-blocking: failed to persist CAT risk assessment", exc_info=True)
        return None


def _persist_plant_assessment(
    db: Session,
    req: PlantDecarbRequest,
    plant_name: str,
    intensity: float,
    nze_2030: float,
    nze_2050: float,
    gap_today_pct: float,
    paris_aligned: bool,
    stranding_year: Optional[int],
    roadmap: List[RoadmapStep],
    total_capex: Optional[float],
    validation_json: dict,
) -> Optional[str]:
    """Insert into power_plant_assessments + power_plant_trajectories. Returns assessment_id."""
    try:
        recommended = [
            {"action": s.recommended_action, "year": s.year,
             "capex_gbp_m": s.estimated_capex_gbp_million}
            for s in roadmap if s.recommended_action
        ]

        row = db.execute(text("""
            INSERT INTO power_plant_assessments
            (plant_name, assessment_date,
             current_ci_gco2_kwh,
             iea_nze_2030_threshold_gco2_kwh,
             iea_nze_2050_threshold_gco2_kwh,
             implied_stranding_year,
             transition_capex_required_gbp,
             recommended_actions,
             validation_summary, status)
            VALUES
            (:name, CURRENT_DATE,
             :ci,
             :nze_2030, :nze_2050,
             :stranding_yr,
             :capex,
             CAST(:recommended AS jsonb),
             CAST(:validation AS jsonb), 'draft')
            RETURNING id::text
        """), {
            "name": plant_name,
            "ci": intensity,
            "nze_2030": nze_2030,
            "nze_2050": nze_2050,
            "stranding_yr": stranding_year,
            "capex": round(total_capex * 1_000_000, 2) if total_capex else None,
            "recommended": json.dumps(recommended),
            "validation": json.dumps(validation_json),
        }).fetchone()
        assessment_id = row[0]

        # Insert trajectory rows
        for step in roadmap:
            is_aligned = step.plant_projected_gco2_kwh <= step.iea_nze_pathway_gco2_kwh * 1.1
            db.execute(text("""
                INSERT INTO power_plant_trajectories
                (assessment_id, year,
                 baseline_ci_gco2_kwh, target_ci_gco2_kwh,
                 nze_benchmark_ci_gco2_kwh, is_aligned_with_nze)
                VALUES
                (:aid, :yr, :baseline, :target, :nze, :aligned)
            """), {
                "aid": assessment_id,
                "yr": step.year,
                "baseline": step.plant_projected_gco2_kwh,
                "target": step.plant_projected_gco2_kwh,
                "nze": step.iea_nze_pathway_gco2_kwh,
                "aligned": is_aligned,
            })

        db.commit()
        logger.info("Persisted plant assessment %s (%d trajectory rows)", assessment_id, len(roadmap))
        return assessment_id
    except Exception:
        db.rollback()
        logger.warning("Non-blocking: failed to persist plant assessment", exc_info=True)
        return None


# ─────────────────────────────────────────────────────────
# POST Routes (compute + persist)
# ─────────────────────────────────────────────────────────
@router.post("/sector/technology/data-center", response_model=DataCenterResponse)
def assess_data_center(request: DataCenterRequest, db: Session = Depends(get_db)):
    """Assess data centre environmental metrics vs benchmarks and generate improvement targets."""
    logger.info("Data centre assessment: facility=%s pue=%.2f renewable=%.1f%%",
                request.facility_id, request.pue, request.renewable_energy_pct)
    try:
        warnings: List[str] = []
        grid_ef = _GRID_EMISSION_FACTORS.get(request.grid_region, 350)  # kgCO2/MWh fallback

        # Carbon intensity per MWh of IT load
        fossil_share = max(0, 1 - request.renewable_energy_pct / 100)
        carbon_intensity = grid_ef * request.pue * fossil_share
        annual_co2 = request.annual_energy_consumption_mwh * grid_ef / 1000 * fossil_share  # tonnes

        # Benchmarks
        pue_score = max(0, min(100, ((_PUE_INDUSTRY_AVG - request.pue) / (_PUE_INDUSTRY_AVG - _PUE_BEST)) * 100))
        pue_gap = round(request.pue - _PUE_BEST, 2)

        benchmarks = [
            EfficiencyBenchmark(
                metric="PUE",
                current_value=request.pue,
                industry_average=_PUE_INDUSTRY_AVG,
                best_in_class=_PUE_BEST,
                score_0_to_100=round(pue_score, 1),
                gap_to_best_in_class=pue_gap,
            ),
        ]

        if request.wue is not None:
            wue_score = max(0, min(100, ((_WUE_INDUSTRY_AVG - request.wue) / (_WUE_INDUSTRY_AVG - _WUE_BEST)) * 100))
            benchmarks.append(EfficiencyBenchmark(
                metric="WUE (L/kWh)",
                current_value=request.wue,
                industry_average=_WUE_INDUSTRY_AVG,
                best_in_class=_WUE_BEST,
                score_0_to_100=round(wue_score, 1),
                gap_to_best_in_class=round(request.wue - _WUE_BEST, 2),
            ))

        renewable_score = request.renewable_energy_pct  # 0-100 directly
        benchmarks.append(EfficiencyBenchmark(
            metric="Renewable Energy %",
            current_value=request.renewable_energy_pct,
            industry_average=40.0,
            best_in_class=100.0,
            score_0_to_100=round(renewable_score, 1),
            gap_to_best_in_class=round(100 - request.renewable_energy_pct, 1),
        ))

        overall_score = round(sum(b.score_0_to_100 for b in benchmarks) / len(benchmarks), 1)

        # Improvement targets
        targets: List[ImprovementTarget] = []
        if request.pue > 1.3:
            potential = round((request.pue - 1.2) / request.pue * 100, 1)
            targets.append(ImprovementTarget(
                measure="Hot/cold aisle containment and airflow optimisation",
                potential_reduction_pct=potential,
                estimated_cost_gbp=round(request.total_it_load_mw * 50_000, 0),
                payback_years=2.5,
                priority="high" if request.pue > 1.6 else "medium",
            ))
        if request.renewable_energy_pct < 80:
            targets.append(ImprovementTarget(
                measure="Renewable energy PPA or on-site solar/wind",
                potential_reduction_pct=round((100 - request.renewable_energy_pct) * 0.9, 1),
                estimated_cost_gbp=round(request.annual_energy_consumption_mwh * 5, 0),
                payback_years=7.0,
                priority="high",
            ))
        if request.cooling_type == "air" and request.total_it_load_mw > 5:
            targets.append(ImprovementTarget(
                measure="Transition to liquid cooling for high-density racks",
                potential_reduction_pct=15.0,
                estimated_cost_gbp=round(request.total_it_load_mw * 200_000, 0),
                payback_years=4.0,
                priority="medium",
            ))
        if not request.has_renewable_ppa:
            targets.append(ImprovementTarget(
                measure="Negotiate long-term Renewable Energy PPA (10-15yr)",
                potential_reduction_pct=round(fossil_share * 100, 1),
                estimated_cost_gbp=None,
                payback_years=None,
                priority="high",
            ))

        val = _build_validation_summary(warnings, [])
        resp_data = {
            "overall_efficiency_score": overall_score,
            "carbon_intensity_kgco2_per_mwh_it": round(carbon_intensity, 2),
            "annual_co2e_tonnes": round(annual_co2, 2),
        }

        # ---- DB persist (non-blocking) ----
        facility_name = request.facility_name or request.facility_id
        assess_year = request.assessment_year or date.today().year
        assessment_id = _persist_dc_assessment(
            db, facility_name, assess_year,
            request, resp_data, benchmarks, targets, val.model_dump(),
        )

        return DataCenterResponse(
            facility_id=request.facility_id,
            overall_efficiency_score=overall_score,
            carbon_intensity_kgco2_per_mwh_it=round(carbon_intensity, 2),
            annual_co2e_tonnes=round(annual_co2, 2),
            renewable_coverage_pct=request.renewable_energy_pct,
            efficiency_benchmarks=benchmarks,
            improvement_targets=targets,
            validation_summary=val,
            assessment_id=assessment_id,
        )
    except Exception as exc:
        logger.exception("Data centre assessment error: facility=%s", request.facility_id)
        raise HTTPException(status_code=500, detail=f"Data centre assessment engine error: {exc}") from exc


@router.post("/sector/insurance/cat-risk", response_model=CATRiskResponse)
def assess_cat_risk(request: CATRiskRequest, db: Session = Depends(get_db)):
    """Quick CAT risk scoring with PML estimates and climate-adjusted AAL for a property."""
    logger.info("CAT risk: property=%s peril=%s scenario=%s horizon=%d",
                request.property_id, request.peril, request.climate_scenario, request.climate_horizon_year)
    try:
        warnings: List[str] = []
        value = request.property_value_gbp
        peril = request.peril.lower()

        # Base AAL
        base_rate = _BASE_AAL_RATES.get(peril, 0.002)
        construction_mult = _CONSTRUCTION_VULNERABILITY.get(
            (request.construction_type or "masonry").lower(), 1.0
        )

        # Age vulnerability (older buildings more vulnerable)
        age_mult = 1.0
        if request.year_built:
            age = 2025 - request.year_built
            if age > 50:
                age_mult = 1.15
            elif age > 30:
                age_mult = 1.05

        aal = value * base_rate * construction_mult * age_mult

        # Climate adjustment
        scenario_uplift = _CLIMATE_SCENARIO_UPLIFT.get(request.climate_scenario, {}).get(peril, 1.0)
        # Scale uplift by horizon year (more uplift further out)
        horizon_scale = (request.climate_horizon_year - 2025) / 75  # 0 to 1 over 75 years
        effective_uplift = 1.0 + (scenario_uplift - 1.0) * horizon_scale
        climate_aal = aal * effective_uplift
        aal_uplift_pct = (effective_uplift - 1.0) * 100

        # PML estimates at various return periods
        pml_estimates: List[PMLEstimate] = []
        for rp in request.return_period_years:
            # PML scales logarithmically with return period
            pml_mult = math.log(rp / 10 + 1) * 0.15  # 0-30% range
            pml = value * pml_mult * construction_mult
            climate_pml = pml * effective_uplift
            pml_estimates.append(PMLEstimate(
                return_period_years=rp,
                pml_gbp=round(pml, 2),
                pml_pct_of_value=round(pml / value * 100, 2),
                climate_adjusted_pml_gbp=round(climate_pml, 2),
                climate_uplift_pct=round(aal_uplift_pct, 2),
            ))

        # Insurability score (100 = fully insurable, 0 = uninsurable)
        aal_ratio = climate_aal / value
        if aal_ratio < 0.001:
            insurability = 95.0
            label = "Fully Insurable"
            risk_cat = "Low"
        elif aal_ratio < 0.005:
            insurability = 80.0
            label = "Standard Risk"
            risk_cat = "Medium"
        elif aal_ratio < 0.01:
            insurability = 60.0
            label = "Elevated Risk"
            risk_cat = "High"
        elif aal_ratio < 0.03:
            insurability = 35.0
            label = "High Risk — Specialist Market"
            risk_cat = "High"
        else:
            insurability = 15.0
            label = "Difficult to Insure"
            risk_cat = "Very High"

        # Key risk drivers
        drivers = [f"Primary peril: {peril}"]
        if construction_mult > 1.0:
            drivers.append(f"Construction type ({request.construction_type}) increases vulnerability")
        if age_mult > 1.0:
            drivers.append(f"Building age ({2025 - (request.year_built or 2000)} years) adds vulnerability")
        if aal_uplift_pct > 20:
            drivers.append(f"Climate scenario {request.climate_scenario} projects {aal_uplift_pct:.0f}% AAL increase by {request.climate_horizon_year}")
        if peril in ("flood", "wildfire") and request.climate_scenario == "RCP8.5":
            drivers.append(f"High-emission scenario significantly amplifies {peril} risk")

        val = _build_validation_summary(warnings, [])

        # ---- DB persist (non-blocking) ----
        assessment_id = _persist_cat_risk_assessment(
            db, request, round(aal, 2), round(climate_aal, 2),
            round(aal_uplift_pct, 2), pml_estimates,
            insurability, risk_cat, val.model_dump(),
        )

        return CATRiskResponse(
            property_id=request.property_id,
            peril=request.peril,
            climate_scenario=request.climate_scenario,
            climate_horizon_year=request.climate_horizon_year,
            annual_average_loss_gbp=round(aal, 2),
            climate_adjusted_aal_gbp=round(climate_aal, 2),
            aal_uplift_pct=round(aal_uplift_pct, 2),
            pml_estimates=pml_estimates,
            insurability_score=round(insurability, 1),
            insurability_label=label,
            key_risk_drivers=drivers,
            validation_summary=val,
            assessment_id=assessment_id,
        )
    except Exception as exc:
        logger.exception("CAT risk engine error: property=%s peril=%s", request.property_id, request.peril)
        raise HTTPException(status_code=500, detail=f"CAT risk engine error: {exc}") from exc


@router.post("/sector/energy/plant-decarbonisation", response_model=PlantDecarbResponse)
def assess_plant_decarbonisation(request: PlantDecarbRequest, db: Session = Depends(get_db)):
    """Assess power plant Paris alignment vs IEA NZE pathway and generate a decarbonisation roadmap."""
    logger.info("Plant decarbonisation: plant=%s type=%s country=%s intensity=%.1f gCO2/kWh",
                request.plant_id, request.plant_type, request.country_iso,
                request.current_emission_intensity_gco2_kwh)
    try:
        warnings: List[str] = []
        intensity = request.current_emission_intensity_gco2_kwh
        plant_type = request.plant_type.lower()

        # Apply CCS reduction if installed
        if request.ccs_installed and request.ccs_capture_rate_pct:
            intensity *= (1 - request.ccs_capture_rate_pct / 100)

        # IEA NZE targets
        nze_2030 = _interpolate_nze(2030)
        nze_2050 = _interpolate_nze(2050)
        nze_today = _interpolate_nze(2025)

        gap_today_pct = ((intensity - nze_today) / nze_today * 100) if nze_today > 0 else 100.0
        paris_aligned = intensity <= nze_today * 1.1  # within 10% of pathway

        # Stranding year: when plant intensity exceeds IEA NZE pathway
        degradation = _ANNUAL_DEGRADATION.get(plant_type, 1.0)
        stranding_year = None
        years_to_stranding = None

        # Project plant intensity forward (gets worse with degradation unless action taken)
        for yr in range(2025, 2051):
            projected = intensity + degradation * (yr - 2025)
            nze_at_yr = _interpolate_nze(yr)
            if projected > nze_at_yr * 1.5:  # 50% above pathway = stranded
                stranding_year = yr
                years_to_stranding = yr - 2025
                break

        # If remaining_asset_life_years constrains the timeline
        if request.remaining_asset_life_years:
            retirement_yr = 2025 + request.remaining_asset_life_years
            if stranding_year and retirement_yr < stranding_year:
                stranding_year = None
                years_to_stranding = None
                warnings.append("Asset retires before stranding threshold is reached")

        # Decarbonisation roadmap
        roadmap: List[RoadmapStep] = []
        total_capex = 0.0
        actions = _DECARB_ACTIONS.get(plant_type, [])
        action_idx = 0

        for yr in range(2025, 2051, 5):
            nze_yr = _interpolate_nze(yr)
            projected = intensity + degradation * (yr - 2025)
            # If we have an action for this period, apply it
            action_text = None
            capex = None
            if action_idx < len(actions):
                act_yr, act_text, act_capex = actions[action_idx]
                if yr >= act_yr:
                    action_text = act_text
                    capex = act_capex
                    total_capex += act_capex
                    # Action reduces projected intensity
                    projected *= 0.6  # assume each action achieves ~40% reduction
                    action_idx += 1

            gap = projected - nze_yr
            roadmap.append(RoadmapStep(
                year=yr,
                iea_nze_pathway_gco2_kwh=round(nze_yr, 1),
                plant_projected_gco2_kwh=round(max(projected, 0), 1),
                gap_gco2_kwh=round(max(gap, 0), 1),
                recommended_action=action_text,
                estimated_capex_gbp_million=capex,
            ))

        val = _build_validation_summary(warnings, [])

        # ---- DB persist (non-blocking) ----
        plant_name = request.plant_name or request.plant_id
        assessment_id = _persist_plant_assessment(
            db, request, plant_name, intensity,
            nze_2030, nze_2050, gap_today_pct, paris_aligned,
            stranding_year, roadmap,
            round(total_capex, 1) if total_capex > 0 else None,
            val.model_dump(),
        )

        return PlantDecarbResponse(
            plant_id=request.plant_id,
            plant_type=request.plant_type,
            country_iso=request.country_iso,
            current_emission_intensity_gco2_kwh=request.current_emission_intensity_gco2_kwh,
            iea_nze_2030_target_gco2_kwh=round(nze_2030, 1),
            iea_nze_2050_target_gco2_kwh=round(nze_2050, 1),
            gap_to_pathway_today_pct=round(gap_today_pct, 2),
            stranding_year=stranding_year,
            years_to_stranding=years_to_stranding,
            paris_aligned=paris_aligned,
            decarbonisation_roadmap=roadmap,
            total_estimated_capex_gbp_million=round(total_capex, 1) if total_capex > 0 else None,
            validation_summary=val,
            assessment_id=assessment_id,
        )
    except Exception as exc:
        logger.exception("Plant decarbonisation engine error: plant=%s", request.plant_id)
        raise HTTPException(status_code=500, detail=f"Plant decarbonisation engine error: {exc}") from exc


# ─────────────────────────────────────────────────────────
# GET Routes (retrieve persisted data)
# ─────────────────────────────────────────────────────────
@router.get("/sector/technology/data-center/assessments")
def list_dc_assessments(
    status: Optional[str] = Query(None),
    assessment_year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """List persisted data centre assessments."""
    try:
        clauses = ["1=1"]
        params: dict = {}
        if status:
            clauses.append("status = :status")
            params["status"] = status
        if assessment_year:
            clauses.append("assessment_year = :yr")
            params["yr"] = assessment_year

        where = " AND ".join(clauses)
        rows = db.execute(text(f"""
            SELECT id::text, facility_name, assessment_year,
                   pue, renewable_energy_pct,
                   efficiency_score, efficiency_rating,
                   annual_co2e_tco2e, status, created_at
            FROM data_centre_assessments
            WHERE {where}
            ORDER BY created_at DESC LIMIT 50
        """), params).fetchall()

        return {
            "assessments": [
                {
                    "assessment_id": r[0], "facility_name": r[1],
                    "assessment_year": r[2],
                    "pue": float(r[3]) if r[3] else None,
                    "renewable_energy_pct": float(r[4]) if r[4] else None,
                    "efficiency_score": float(r[5]) if r[5] else None,
                    "efficiency_rating": r[6],
                    "annual_co2e_tco2e": float(r[7]) if r[7] else None,
                    "status": r[8],
                    "created_at": str(r[9]) if r[9] else None,
                }
                for r in rows
            ],
            "total_count": len(rows),
        }
    except Exception as exc:
        logger.exception("Failed to list DC assessments")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sector/technology/data-center/assessments/{assessment_id}")
def get_dc_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Get a specific data centre assessment."""
    try:
        row = db.execute(text("""
            SELECT id::text, facility_name, assessment_year,
                   total_it_load_mw, annual_energy_consumption_mwh,
                   pue, wue, renewable_energy_pct,
                   grid_emission_factor_kgco2e_kwh,
                   carbon_intensity_kgco2e_kwh_it,
                   annual_co2e_tco2e,
                   efficiency_score, efficiency_rating,
                   improvement_targets, recommended_actions,
                   validation_summary, status, created_at
            FROM data_centre_assessments WHERE id = :aid
        """), {"aid": assessment_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")

        return {
            "assessment_id": row[0], "facility_name": row[1],
            "assessment_year": row[2],
            "total_it_load_mw": float(row[3]) if row[3] else None,
            "annual_energy_consumption_mwh": float(row[4]) if row[4] else None,
            "pue": float(row[5]) if row[5] else None,
            "wue": float(row[6]) if row[6] else None,
            "renewable_energy_pct": float(row[7]) if row[7] else None,
            "grid_emission_factor": float(row[8]) if row[8] else None,
            "carbon_intensity_kgco2e_kwh_it": float(row[9]) if row[9] else None,
            "annual_co2e_tco2e": float(row[10]) if row[10] else None,
            "efficiency_score": float(row[11]) if row[11] else None,
            "efficiency_rating": row[12],
            "improvement_targets": row[13],
            "recommended_actions": row[14],
            "validation_summary": row[15],
            "status": row[16],
            "created_at": str(row[17]) if row[17] else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get DC assessment %s", assessment_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sector/insurance/cat-risk/assessments")
def list_cat_risk_assessments(
    status: Optional[str] = Query(None),
    peril: Optional[str] = Query(None),
    risk_category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List persisted CAT risk assessments."""
    try:
        clauses = ["1=1"]
        params: dict = {}
        if status:
            clauses.append("status = :status")
            params["status"] = status
        if peril:
            clauses.append("peril = :peril")
            params["peril"] = peril.lower()
        if risk_category:
            clauses.append("risk_category = :cat")
            params["cat"] = risk_category

        where = " AND ".join(clauses)
        rows = db.execute(text(f"""
            SELECT id::text, property_reference, peril,
                   property_value_gbp, aal_gbp, pml_gbp,
                   risk_score, risk_category,
                   status, created_at
            FROM cat_risk_assessments
            WHERE {where}
            ORDER BY created_at DESC LIMIT 50
        """), params).fetchall()

        return {
            "assessments": [
                {
                    "assessment_id": r[0], "property_reference": r[1],
                    "peril": r[2],
                    "property_value_gbp": float(r[3]) if r[3] else 0,
                    "aal_gbp": float(r[4]) if r[4] else 0,
                    "pml_gbp": float(r[5]) if r[5] else 0,
                    "risk_score": float(r[6]) if r[6] else None,
                    "risk_category": r[7],
                    "status": r[8],
                    "created_at": str(r[9]) if r[9] else None,
                }
                for r in rows
            ],
            "total_count": len(rows),
        }
    except Exception as exc:
        logger.exception("Failed to list CAT risk assessments")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sector/insurance/cat-risk/assessments/{assessment_id}")
def get_cat_risk_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Get a specific CAT risk assessment with climate scenario."""
    try:
        row = db.execute(text("""
            SELECT id::text, property_reference, assessment_date, peril,
                   property_value_gbp, aal_gbp, aal_pct_of_value, pml_gbp,
                   return_period_curve,
                   risk_score, risk_category,
                   validation_summary, status, created_at
            FROM cat_risk_assessments WHERE id = :aid
        """), {"aid": assessment_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Fetch climate scenarios
        scenarios = db.execute(text("""
            SELECT climate_scenario, time_horizon_year,
                   aal_delta_pct, aal_climate_adjusted_gbp,
                   pml_delta_pct, pml_climate_adjusted_gbp
            FROM cat_risk_climate_scenarios WHERE assessment_id = :aid
        """), {"aid": assessment_id}).fetchall()

        return {
            "assessment_id": row[0], "property_reference": row[1],
            "assessment_date": str(row[2]) if row[2] else None,
            "peril": row[3],
            "property_value_gbp": float(row[4]) if row[4] else 0,
            "aal_gbp": float(row[5]) if row[5] else 0,
            "aal_pct_of_value": float(row[6]) if row[6] else 0,
            "pml_gbp": float(row[7]) if row[7] else 0,
            "return_period_curve": row[8],
            "risk_score": float(row[9]) if row[9] else None,
            "risk_category": row[10],
            "validation_summary": row[11],
            "status": row[12],
            "created_at": str(row[13]) if row[13] else None,
            "climate_scenarios": [
                {
                    "scenario": s[0], "horizon_year": s[1],
                    "aal_delta_pct": float(s[2]) if s[2] else 0,
                    "aal_climate_adjusted_gbp": float(s[3]) if s[3] else 0,
                    "pml_delta_pct": float(s[4]) if s[4] else 0,
                    "pml_climate_adjusted_gbp": float(s[5]) if s[5] else 0,
                }
                for s in scenarios
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get CAT risk assessment %s", assessment_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sector/energy/plant-decarbonisation/assessments")
def list_plant_assessments(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List persisted power plant assessments."""
    try:
        clauses = ["1=1"]
        params: dict = {}
        if status:
            clauses.append("status = :status")
            params["status"] = status

        where = " AND ".join(clauses)
        rows = db.execute(text(f"""
            SELECT id::text, plant_name, assessment_date,
                   current_ci_gco2_kwh,
                   iea_nze_2030_threshold_gco2_kwh,
                   implied_stranding_year,
                   transition_capex_required_gbp,
                   status, created_at
            FROM power_plant_assessments
            WHERE {where}
            ORDER BY created_at DESC LIMIT 50
        """), params).fetchall()

        return {
            "assessments": [
                {
                    "assessment_id": r[0], "plant_name": r[1],
                    "assessment_date": str(r[2]) if r[2] else None,
                    "current_ci_gco2_kwh": float(r[3]) if r[3] else None,
                    "iea_nze_2030_target": float(r[4]) if r[4] else None,
                    "implied_stranding_year": r[5],
                    "transition_capex_gbp": float(r[6]) if r[6] else None,
                    "status": r[7],
                    "created_at": str(r[8]) if r[8] else None,
                }
                for r in rows
            ],
            "total_count": len(rows),
        }
    except Exception as exc:
        logger.exception("Failed to list plant assessments")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sector/energy/plant-decarbonisation/assessments/{assessment_id}")
def get_plant_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Get a specific power plant assessment with trajectory."""
    try:
        row = db.execute(text("""
            SELECT id::text, plant_name, assessment_date,
                   current_ci_gco2_kwh,
                   iea_nze_2030_threshold_gco2_kwh,
                   iea_nze_2040_threshold_gco2_kwh,
                   iea_nze_2050_threshold_gco2_kwh,
                   implied_stranding_year,
                   transition_capex_required_gbp,
                   recommended_actions,
                   validation_summary, status, created_at
            FROM power_plant_assessments WHERE id = :aid
        """), {"aid": assessment_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")

        trajectories = db.execute(text("""
            SELECT year, baseline_ci_gco2_kwh, target_ci_gco2_kwh,
                   nze_benchmark_ci_gco2_kwh, is_aligned_with_nze
            FROM power_plant_trajectories WHERE assessment_id = :aid
            ORDER BY year
        """), {"aid": assessment_id}).fetchall()

        return {
            "assessment_id": row[0], "plant_name": row[1],
            "assessment_date": str(row[2]) if row[2] else None,
            "current_ci_gco2_kwh": float(row[3]) if row[3] else None,
            "iea_nze_2030_target": float(row[4]) if row[4] else None,
            "iea_nze_2040_target": float(row[5]) if row[5] else None,
            "iea_nze_2050_target": float(row[6]) if row[6] else None,
            "implied_stranding_year": row[7],
            "transition_capex_gbp": float(row[8]) if row[8] else None,
            "recommended_actions": row[9],
            "validation_summary": row[10],
            "status": row[11],
            "created_at": str(row[12]) if row[12] else None,
            "trajectories": [
                {
                    "year": t[0],
                    "baseline_ci_gco2_kwh": float(t[1]) if t[1] else None,
                    "target_ci_gco2_kwh": float(t[2]) if t[2] else None,
                    "nze_benchmark_ci_gco2_kwh": float(t[3]) if t[3] else None,
                    "is_aligned_with_nze": t[4],
                }
                for t in trajectories
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get plant assessment %s", assessment_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
