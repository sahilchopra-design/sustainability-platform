"""
API Routes: Nature-Based Solutions & Carbon Sequestration (E52)
===============================================================
POST /api/v1/nature-based-solutions/iucn-assessment       — IUCN GS v2.0 assessment
POST /api/v1/nature-based-solutions/redd-plus             — REDD+ VM0007 net credits
POST /api/v1/nature-based-solutions/blue-carbon           — Blue carbon sequestration
POST /api/v1/nature-based-solutions/soil-carbon           — IPCC Tier 1-3 soil carbon
POST /api/v1/nature-based-solutions/arr-assessment        — ARR afforestation assessment
POST /api/v1/nature-based-solutions/afolu-balance         — AFOLU net GHG balance
POST /api/v1/nature-based-solutions/credit-quality        — Credit quality + price
POST /api/v1/nature-based-solutions/sequestration-timeseries — 30-year projection
GET  /api/v1/nature-based-solutions/ref/ecosystem-types   — Blue carbon ecosystems
GET  /api/v1/nature-based-solutions/ref/methodologies     — VCS/Gold Standard list
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from services.nature_based_solutions_engine import (
    NatureBasedSolutionsEngine,
    BLUE_CARBON_RATES,
    BLUE_CARBON_METHODOLOGY,
    BLUE_CARBON_PERMANENCE,
    CERTIFICATION_SCHEMES,
)

router = APIRouter(
    prefix="/api/v1/nature-based-solutions",
    tags=["Nature-Based Solutions"],
)

_engine = NatureBasedSolutionsEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class IUCNAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    criteria_scores: list[float] = Field(default_factory=list, description="0-100 score per IUCN GS criterion (up to 8)")


class REDDPlusRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    area_ha: float = Field(..., ge=0)
    reference_level_tco2_pa: float = Field(..., ge=0)
    actual_emissions_tco2_pa: float = Field(..., ge=0)
    jurisdictional: bool = False


class BlueCarbonRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    ecosystem_type: str = Field(..., description="mangrove | seagrass | saltmarsh | tidal_flat")
    area_ha: float = Field(..., ge=0)


class SoilCarbonRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    area_ha: float = Field(..., ge=0)
    land_use_change: str
    ipcc_tier: int = Field(1, ge=1, le=3)


class ARRAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    area_ha: float = Field(..., ge=0)
    species_type: str = Field("mixed", description="native | mixed | exotic")


class AFOLUBalanceRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    sequestration_tco2_pa: float = Field(..., ge=0)
    land_area_ha: float = Field(..., ge=0)


class CreditQualityRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    iucn_score: float = Field(..., ge=0, le=100)
    redd_net_credits: float = Field(..., ge=0)
    co_benefits: dict = Field(
        default_factory=dict,
        description="Keys: biodiversity, water, livelihoods (each 0-100)",
    )


class SequestrationTimeseriesRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    annual_seq_tco2: float = Field(..., ge=0)
    project_years: int = Field(30, ge=1, le=100)


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/iucn-assessment")
def iucn_assessment(req: IUCNAssessmentRequest) -> dict:
    """IUCN Global Standard v2.0 — 8-criteria composite scoring with tier classification."""
    return _engine.assess_iucn_gs(
        entity_id=req.entity_id,
        criteria_scores=req.criteria_scores,
    )


@router.post("/redd-plus")
def redd_plus(req: REDDPlusRequest) -> dict:
    """VCS VM0007 REDD+ avoided deforestation net credit calculation."""
    return _engine.assess_redd_plus(
        entity_id=req.entity_id,
        area_ha=req.area_ha,
        reference_level_tco2_pa=req.reference_level_tco2_pa,
        actual_emissions_tco2_pa=req.actual_emissions_tco2_pa,
        jurisdictional=req.jurisdictional,
    )


@router.post("/blue-carbon")
def blue_carbon(req: BlueCarbonRequest) -> dict:
    """Blue carbon sequestration for coastal/marine ecosystems (VM0033/VM0024)."""
    return _engine.assess_blue_carbon(
        entity_id=req.entity_id,
        ecosystem_type=req.ecosystem_type,
        area_ha=req.area_ha,
    )


@router.post("/soil-carbon")
def soil_carbon(req: SoilCarbonRequest) -> dict:
    """IPCC Tier 1-3 soil organic carbon delta methodology."""
    return _engine.assess_soil_carbon(
        entity_id=req.entity_id,
        area_ha=req.area_ha,
        land_use_change=req.land_use_change,
        ipcc_tier=req.ipcc_tier,
    )


@router.post("/arr-assessment")
def arr_assessment(req: ARRAssessmentRequest) -> dict:
    """Afforestation, Reforestation & Revegetation carbon accounting."""
    return _engine.assess_arr(
        entity_id=req.entity_id,
        area_ha=req.area_ha,
        species_type=req.species_type,
    )


@router.post("/afolu-balance")
def afolu_balance(req: AFOLUBalanceRequest) -> dict:
    """AFOLU net GHG balance including N2O and CH4 non-CO2 emissions."""
    return _engine.compute_afolu_balance(
        entity_id=req.entity_id,
        sequestration_tco2_pa=req.sequestration_tco2_pa,
        land_area_ha=req.land_area_ha,
    )


@router.post("/credit-quality")
def credit_quality(req: CreditQualityRequest) -> dict:
    """Carbon credit quality assessment with ICVCM CCP compatibility and price range."""
    return _engine.assess_credit_quality(
        entity_id=req.entity_id,
        iucn_score=req.iucn_score,
        redd_net_credits=req.redd_net_credits,
        co_benefits=req.co_benefits,
    )


@router.post("/sequestration-timeseries")
def sequestration_timeseries(req: SequestrationTimeseriesRequest) -> dict:
    """30-year project-level sequestration timeseries with ramp-up and variability."""
    ts = _engine.project_sequestration_timeseries(
        entity_id=req.entity_id,
        annual_seq_tco2=req.annual_seq_tco2,
        project_years=req.project_years,
    )
    total_credits = sum(r["credits_issued_tco2"] for r in ts)
    return {
        "entity_id": req.entity_id,
        "project_years": req.project_years,
        "annual_seq_tco2_input": req.annual_seq_tco2,
        "total_credits_projected_tco2": round(total_credits, 2),
        "timeseries": ts,
    }


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ecosystem-types")
def ref_ecosystem_types() -> dict:
    """Blue carbon ecosystem types with sequestration rates, permanence risk, and methodology."""
    ecosystems = []
    for eco, rate in BLUE_CARBON_RATES.items():
        ecosystems.append({
            "ecosystem": eco,
            "seq_rate_tco2_ha_pa": rate,
            "permanence_risk": BLUE_CARBON_PERMANENCE[eco],
            "vcs_methodology": BLUE_CARBON_METHODOLOGY[eco],
        })
    return {
        "ecosystems": ecosystems,
        "source": "Verra VCS VM0033/VM0024 + Coastal Blue Carbon Initiative",
    }


@router.get("/ref/methodologies")
def ref_methodologies() -> dict:
    """Recognised NBS carbon credit methodologies (VCS, Gold Standard, ACR, CAR)."""
    methodologies = [
        {
            "code": "VM0007",
            "name": "REDD+ Methodology Framework",
            "standard": "Verra VCS",
            "project_type": "Avoided Deforestation",
            "permanence_years": 100,
        },
        {
            "code": "VM0033",
            "name": "Tidal Wetland and Seagrass Restoration",
            "standard": "Verra VCS",
            "project_type": "Blue Carbon",
            "permanence_years": 40,
        },
        {
            "code": "VM0024",
            "name": "Applied Research for Tidal Wetland Carbon",
            "standard": "Verra VCS",
            "project_type": "Blue Carbon",
            "permanence_years": 40,
        },
        {
            "code": "VM0047",
            "name": "Afforestation, Reforestation and Revegetation",
            "standard": "Verra VCS",
            "project_type": "ARR",
            "permanence_years": 40,
        },
        {
            "code": "GS-ARR",
            "name": "Afforestation/Reforestation of Degraded Land",
            "standard": "Gold Standard",
            "project_type": "ARR",
            "permanence_years": 30,
        },
        {
            "code": "IPCC-T1",
            "name": "Tier 1 Soil Carbon (Default EF)",
            "standard": "IPCC 2006 GLs",
            "project_type": "Soil Carbon",
            "permanence_years": 20,
        },
        {
            "code": "IPCC-T2",
            "name": "Tier 2 Soil Carbon (Country-specific EF)",
            "standard": "IPCC 2006 GLs",
            "project_type": "Soil Carbon",
            "permanence_years": 20,
        },
        {
            "code": "IPCC-T3",
            "name": "Tier 3 Soil Carbon (Direct Measurement)",
            "standard": "IPCC 2006 GLs",
            "project_type": "Soil Carbon",
            "permanence_years": 20,
        },
    ]
    return {
        "methodologies": methodologies,
        "certification_schemes": CERTIFICATION_SCHEMES,
        "icvcm_ccp_standard": "Core Carbon Principles 2023",
    }
