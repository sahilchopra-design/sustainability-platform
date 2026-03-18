"""
API Routes: Green Hydrogen and Energy Transition Engine (E43)
==============================================================
EU Delegated Act 2023/1184 (RFNBO) + IRA Section 45V + LCOH modelling

POST /api/v1/green-hydrogen-engine/classify-pathway      — H2 colour classification
POST /api/v1/green-hydrogen-engine/eu-rfnbo-compliance   — EU Delegated Act 2023/1184 check
POST /api/v1/green-hydrogen-engine/calculate-lcoh        — LCOH calculation
POST /api/v1/green-hydrogen-engine/apply-subsidy         — Subsidy netting
POST /api/v1/green-hydrogen-engine/scenario-analysis     — Multi-scenario LCOH
POST /api/v1/green-hydrogen-engine/full-assessment       — Complete H2 assessment
GET  /api/v1/green-hydrogen-engine/ref/pathways          — H2_PATHWAYS
GET  /api/v1/green-hydrogen-engine/ref/electrolyser-params — ELECTROLYSER_PARAMS
GET  /api/v1/green-hydrogen-engine/ref/rfnbo-criteria    — EU_RFNBO_CRITERIA
GET  /api/v1/green-hydrogen-engine/ref/subsidy-schemes   — SUBSIDY_SCHEMES
GET  /api/v1/green-hydrogen-engine/ref/cost-scenarios    — COST_SCENARIOS
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.green_hydrogen_engine import GreenHydrogenEngine

router = APIRouter(
    prefix="/api/v1/green-hydrogen-engine",
    tags=["Green Hydrogen — E43"],
)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ClassifyPathwayRequest(BaseModel):
    entity_id: str
    production_pathway: str = "green_electrolysis"
    renewable_electricity_pct: float = Field(100.0, ge=0, le=100)
    carbon_intensity_kgco2e_kgh2: float = Field(0.5, ge=0)


class EURFNBOComplianceRequest(BaseModel):
    entity_id: str
    additionality_met: bool = False
    temporal_correlation_met: bool = False
    geographical_correlation_met: bool = False
    carbon_intensity: float = Field(0.5, ge=0)


class CalculateLCOHRequest(BaseModel):
    entity_id: str
    capacity_mw: float = Field(100.0, ge=0)
    capacity_factor_pct: float = Field(45.0, ge=0, le=100)
    electricity_cost_mwh: float = Field(45.0, ge=0)
    capex_per_kw: float = Field(700.0, ge=0)
    discount_rate_pct: float = Field(7.0, ge=0, le=30)
    lifetime_years: int = Field(20, ge=1, le=40)


class ApplySubsidyRequest(BaseModel):
    entity_id: str
    lcoh: float = Field(3.5, ge=0)
    h2_subsidy_scheme: str = "eu_h2_bank"


class ScenarioAnalysisRequest(BaseModel):
    entity_id: str
    assessment_id: str = "h2-scenario-001"
    technology: str = "ALK"
    capacity_mw: float = Field(100.0, ge=0)
    capacity_factor_pct: float = Field(45.0, ge=0, le=100)
    discount_rate_pct: float = Field(7.0, ge=0)


class FullAssessmentRequest(BaseModel):
    entity_id: str
    project_name: str
    country_code: str = "DE"
    production_pathway: str = "green_electrolysis"
    technology: str = "ALK"
    capacity_mw: float = Field(100.0, ge=0)
    capacity_factor_pct: float = Field(45.0, ge=0, le=100)
    electricity_cost_mwh: float = Field(45.0, ge=0)
    capex_per_kw: float = Field(700.0, ge=0)
    h2_subsidy_scheme: str = "eu_h2_bank"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/classify-pathway")
def classify_pathway(req: ClassifyPathwayRequest):
    """Classify H2 production pathway by colour and check EU RFNBO / Taxonomy eligibility."""
    try:
        engine = GreenHydrogenEngine()
        return engine.classify_pathway(
            entity_id=req.entity_id,
            production_pathway=req.production_pathway,
            renewable_electricity_pct=req.renewable_electricity_pct,
            carbon_intensity_kgco2e_kgh2=req.carbon_intensity_kgco2e_kgh2,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/eu-rfnbo-compliance")
def eu_rfnbo_compliance(req: EURFNBOComplianceRequest):
    """Check EU Delegated Act 2023/1184 RFNBO compliance."""
    try:
        engine = GreenHydrogenEngine()
        return engine.check_eu_rfnbo_compliance(
            entity_id=req.entity_id,
            additionality_met=req.additionality_met,
            temporal_correlation_met=req.temporal_correlation_met,
            geographical_correlation_met=req.geographical_correlation_met,
            carbon_intensity=req.carbon_intensity,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/calculate-lcoh")
def calculate_lcoh(req: CalculateLCOHRequest):
    """Calculate Levelised Cost of Hydrogen (LCOH) in USD/kgH2."""
    try:
        engine = GreenHydrogenEngine()
        return engine.calculate_lcoh(
            entity_id=req.entity_id,
            capacity_mw=req.capacity_mw,
            capacity_factor_pct=req.capacity_factor_pct,
            electricity_cost_mwh=req.electricity_cost_mwh,
            capex_per_kw=req.capex_per_kw,
            discount_rate_pct=req.discount_rate_pct,
            lifetime_years=req.lifetime_years,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/apply-subsidy")
def apply_subsidy(req: ApplySubsidyRequest):
    """Net a policy subsidy against gross LCOH and check grey H2 parity."""
    try:
        engine = GreenHydrogenEngine()
        return engine.apply_subsidy(
            entity_id=req.entity_id,
            lcoh=req.lcoh,
            h2_subsidy_scheme=req.h2_subsidy_scheme,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/scenario-analysis")
def scenario_analysis(req: ScenarioAnalysisRequest):
    """Run LCOH across all six cost scenarios (base/optimistic/pessimistic 2025-2040)."""
    try:
        engine = GreenHydrogenEngine()
        return engine.run_scenario_analysis(
            entity_id=req.entity_id,
            assessment_id=req.assessment_id,
            technology=req.technology,
            capacity_mw=req.capacity_mw,
            capacity_factor_pct=req.capacity_factor_pct,
            discount_rate_pct=req.discount_rate_pct,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Complete green hydrogen project assessment with RFNBO, LCOH, subsidy and scenario analysis."""
    try:
        engine = GreenHydrogenEngine()
        return engine.full_assessment(
            entity_id=req.entity_id,
            project_name=req.project_name,
            country_code=req.country_code,
            production_pathway=req.production_pathway,
            technology=req.technology,
            capacity_mw=req.capacity_mw,
            capacity_factor_pct=req.capacity_factor_pct,
            electricity_cost_mwh=req.electricity_cost_mwh,
            capex_per_kw=req.capex_per_kw,
            h2_subsidy_scheme=req.h2_subsidy_scheme,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/pathways")
def ref_pathways():
    """Return all H2 production pathways with colour classification and RFNBO eligibility."""
    return GreenHydrogenEngine.get_h2_pathways()


@router.get("/ref/electrolyser-params")
def ref_electrolyser_params():
    """Return electrolyser technology parameters (CAPEX, efficiency, lifetime)."""
    return GreenHydrogenEngine.get_electrolyser_params()


@router.get("/ref/rfnbo-criteria")
def ref_rfnbo_criteria():
    """Return EU Delegated Act 2023/1184 RFNBO criteria."""
    return GreenHydrogenEngine.get_eu_rfnbo_criteria()


@router.get("/ref/subsidy-schemes")
def ref_subsidy_schemes():
    """Return policy subsidy schemes for green hydrogen."""
    return GreenHydrogenEngine.get_subsidy_schemes()


@router.get("/ref/cost-scenarios")
def ref_cost_scenarios():
    """Return LCOH cost trajectory scenarios (2025-2040)."""
    return GreenHydrogenEngine.get_cost_scenarios()
