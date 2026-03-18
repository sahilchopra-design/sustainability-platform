"""
API Routes: Adaptation Finance & Resilience Economics Engine — E83
==================================================================
POST /api/v1/adaptation-finance/gfma-alignment       — GFMA adaptation taxonomy alignment
POST /api/v1/adaptation-finance/resilience-delta     — Physical risk reduction quantification
POST /api/v1/adaptation-finance/gari-scoring         — GARI investment criteria scoring
POST /api/v1/adaptation-finance/adaptation-npv       — BCR and NPV for adaptation projects
POST /api/v1/adaptation-finance/mdb-eligibility      — MDB facility eligibility assessment
POST /api/v1/adaptation-finance/nap-ndc-alignment    — National adaptation plan alignment
POST /api/v1/adaptation-finance/full-assessment      — Complete adaptation finance assessment
POST /api/v1/adaptation-finance/portfolio-assessment — Portfolio-level aggregation
GET  /api/v1/adaptation-finance/ref/gfma-categories  — GFMA adaptation taxonomy
GET  /api/v1/adaptation-finance/ref/mdb-facilities   — MDB climate finance facilities
GET  /api/v1/adaptation-finance/ref/nap-profiles     — Country NAP profiles
GET  /api/v1/adaptation-finance/ref/hazard-risk-profiles — Hazard risk reduction benchmarks
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.adaptation_finance_engine import (
    AdaptationFinanceEngine,
    DISCOUNT_RATES_BY_CONTEXT,
    GFMA_ADAPTATION_CATEGORIES,
    GARI_SCORING_CRITERIA,
    HAZARD_RISK_REDUCTION_PROFILES,
    MDB_CLIMATE_FACILITIES,
    NAP_COUNTRY_PROFILES,
    RCP_HAZARD_PROJECTIONS,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/adaptation-finance",
    tags=["Adaptation Finance (E83)"],
)

_engine = AdaptationFinanceEngine()


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------


class GFMAAlignmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    project_name: str
    country_code: str = Field(..., min_length=2, max_length=3)
    primary_sector: str = Field(..., description="e.g. water, coastal, agriculture, health, transport, energy, nature")
    project_description: str = ""
    co_benefits: List[str] = Field(default_factory=list)


class ResilienceDeltaRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    project_name: str
    country_code: str
    hazard_type: str = Field(
        ...,
        description="One of: flooding, drought, sea_level_rise, heat_waves, storm_surge, "
                    "tropical_cyclone, wildfire, permafrost_thaw, vector_borne_disease, water_scarcity",
    )
    baseline_exposure_m: float = Field(..., ge=0, description="Current annual average loss or risk score (USD M or 0-100)")
    adaptation_measure: str = Field(..., description="e.g. dyke_levee, mangrove_restoration, early_warning_system")
    rcp_scenario: str = Field("2C", description="RCP/warming scenario: 1.5C, 2C, 3C, or 4C")
    time_horizon_years: int = Field(20, ge=1, le=100)


class GARIScoringRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    project_name: str
    additionality_evidence: Any = Field(50, description="Score 0-100 or descriptive text")
    effectiveness_data: Any = Field(50, description="Score 0-100 or descriptive text")
    sustainability_plan: Any = Field(50, description="Score 0-100 or descriptive text")
    scalability_potential: Any = Field(50, description="Score 0-100 or descriptive text")
    co_benefits_data: Any = Field(50, description="Score 0-100 or descriptive text")
    governance_structure: Any = Field(50, description="Score 0-100 or descriptive text")


class AdaptationNPVRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    project_name: str
    total_investment_m: float = Field(..., ge=0, description="Total project investment (USD millions)")
    annual_benefits_m: float = Field(..., ge=0, description="Annual climate risk reduction benefits (USD millions)")
    annual_om_m: float = Field(0.0, ge=0, description="Annual operation & maintenance costs (USD millions)")
    discount_rate: float = Field(7.0, ge=0, le=30, description="Discount rate (%)")
    horizon_years: int = Field(20, ge=1, le=100)
    beneficiaries_count: int = Field(10000, ge=1)


class MDBEligibilityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    project_name: str
    country_code: str
    sector: str
    total_investment_m: float = Field(..., ge=0)
    public_component_m: Optional[float] = Field(None, ge=0)
    adaptation_category: Optional[str] = None
    gfma_aligned: bool = True


class NAPNDCAlignmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    project_name: str
    country_code: str
    adaptation_measures: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)


class AdaptationFullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    project_name: str
    country_code: str
    primary_sector: str
    project_description: str = ""
    co_benefits: List[str] = Field(default_factory=list)
    hazard_type: str = "flooding"
    baseline_exposure_m: float = Field(10.0, ge=0)
    adaptation_measure: str = "early_warning_system"
    rcp_scenario: str = "2C"
    time_horizon_years: int = Field(20, ge=1, le=100)
    additionality_evidence: Any = 50
    effectiveness_data: Any = 50
    sustainability_plan: Any = 50
    scalability_potential: Any = 50
    co_benefits_data: Any = 50
    governance_structure: Any = 50
    total_investment_m: float = Field(10.0, ge=0)
    annual_benefits_m: float = Field(2.0, ge=0)
    annual_om_m: float = Field(0.2, ge=0)
    discount_rate: float = Field(7.0, ge=0, le=30)
    horizon_years: int = Field(20, ge=1, le=100)
    beneficiaries_count: int = Field(10000, ge=1)
    public_component_m: Optional[float] = None
    gfma_aligned: bool = True
    adaptation_measures: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)


class AdaptationPortfolioRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    projects: List[Dict[str, Any]] = Field(
        ...,
        description="List of project_data dicts. Each dict may include any fields from "
                    "AdaptationFullAssessmentRequest.",
    )


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------


@router.post("/gfma-alignment", summary="GFMA adaptation taxonomy alignment")
async def gfma_alignment(request: GFMAAlignmentRequest) -> Dict[str, Any]:
    """
    Assess project alignment with the GFMA Adaptation Finance Framework taxonomy.
    Returns GFMA category, co-benefit mapping, BCR range, and taxonomy reference.

    Ref: GFMA Adaptation Finance Framework 2022
    """
    try:
        result = _engine.assess_gfma_alignment(request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("GFMA alignment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/resilience-delta", summary="Physical risk reduction quantification")
async def resilience_delta(request: ResilienceDeltaRequest) -> Dict[str, Any]:
    """
    Quantify climate risk reduction (resilience delta) from an adaptation measure
    under a specified RCP/warming scenario. Includes maladaptation risk assessment.

    Ref: IPCC AR6 WG2; ISO 14091:2021; GFMA Hazard Profiles
    """
    try:
        result = _engine.calculate_resilience_delta(
            baseline_risk=request.baseline_exposure_m,
            project_data=request.model_dump(),
            rcp_scenario=request.rcp_scenario,
        )
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("Resilience delta calculation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/gari-scoring", summary="GARI investment criteria scoring")
async def gari_scoring(request: GARIScoringRequest) -> Dict[str, Any]:
    """
    Score an adaptation project against the 6 GARI criteria:
    additionality (20%), effectiveness (25%), sustainability (15%),
    scalability (15%), co-benefits (15%), governance (10%).

    Ref: GARI Framework — Climate Policy Initiative / Global Adaptation Commission 2023
    """
    try:
        result = _engine.score_gari(request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("GARI scoring failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/adaptation-npv", summary="BCR and NPV for adaptation projects")
async def adaptation_npv(request: AdaptationNPVRequest) -> Dict[str, Any]:
    """
    Calculate adaptation project NPV, benefit-cost ratio (BCR), SROI,
    cost per beneficiary, and approximate IRR.

    Ref: HM Treasury Green Book 2022; EU JASPERS methodology; ISO 14093:2022
    """
    try:
        result = _engine.calculate_adaptation_npv(
            project_data=request.model_dump(),
            discount_rate=request.discount_rate,
            horizon_years=request.horizon_years,
        )
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("Adaptation NPV calculation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/mdb-eligibility", summary="MDB climate finance facility eligibility")
async def mdb_eligibility(request: MDBEligibilityRequest) -> Dict[str, Any]:
    """
    Assess project eligibility across 8 MDB climate finance facilities
    (GCF, GEF, AIIB, ADB, IADB, EIB, AFD, World Bank).
    Returns eligible facilities, estimated grant/loan split, and key criteria.
    """
    try:
        result = _engine.assess_mdb_eligibility(request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("MDB eligibility assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/nap-ndc-alignment", summary="National Adaptation Plan and NDC alignment")
async def nap_ndc_alignment(request: NAPNDCAlignmentRequest) -> Dict[str, Any]:
    """
    Assess project alignment with the country's National Adaptation Plan (NAP)
    and NDC adaptation component.

    Covers 30 developing country profiles. Ref: UNFCCC NAP portal; Paris Agreement Art 7
    """
    try:
        result = _engine.assess_nap_ndc_alignment(
            project_data=request.model_dump(),
            country_code=request.country_code,
        )
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("NAP/NDC alignment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/full-assessment", summary="Complete adaptation finance assessment — all sub-modules")
async def full_assessment(request: AdaptationFullAssessmentRequest) -> Dict[str, Any]:
    """
    Orchestrate all adaptation finance sub-modules and return composite
    adaptation_score and bankability_tier.

    Weighting: GFMA 20% | GARI 30% | NPV/BCR 25% | MDB 15% | NAP/NDC 10%

    bankability_tier: Highly Bankable | Bankable | Conditionally Bankable | Pre-Bankable
    """
    try:
        result = _engine.run_full_assessment(request.entity_id, request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("Adaptation full assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/portfolio-assessment", summary="Portfolio-level adaptation finance aggregation")
async def portfolio_assessment(request: AdaptationPortfolioRequest) -> Dict[str, Any]:
    """
    Aggregate adaptation metrics across a portfolio of projects.
    Returns weighted adaptation score, bankability distribution, sector
    diversification, total NPV, and aggregate grant potential.
    """
    try:
        result = _engine.aggregate_portfolio(request.entity_id, request.projects)
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("Portfolio adaptation assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------


@router.get("/ref/gfma-categories", summary="GFMA adaptation taxonomy — 8 categories")
async def ref_gfma_categories() -> Dict[str, Any]:
    """
    Return all 8 GFMA adaptation taxonomy categories with BCR ranges,
    co-benefits, hazard coverage, SDG alignment, and taxonomy references.

    Ref: GFMA Adaptation Finance Framework 2022
    """
    return {
        "status": "success",
        "source": "GFMA Adaptation Finance Framework 2022",
        "total_categories": len(GFMA_ADAPTATION_CATEGORIES),
        "categories": GFMA_ADAPTATION_CATEGORIES,
    }


@router.get("/ref/mdb-facilities", summary="MDB climate finance facilities — 8 institutions")
async def ref_mdb_facilities() -> Dict[str, Any]:
    """
    Return details of 8 multilateral development bank climate finance facilities:
    GCF, GEF, AIIB, ADB, IADB, EIB, AFD, World Bank. Includes eligibility
    criteria, minimum project size, and grant/concessional loan availability.
    """
    return {
        "status": "success",
        "source": "MDB climate finance eligibility criteria (2024)",
        "total_facilities": len(MDB_CLIMATE_FACILITIES),
        "facilities": MDB_CLIMATE_FACILITIES,
    }


@router.get("/ref/nap-profiles", summary="Country NAP profiles — 30 developing countries")
async def ref_nap_profiles() -> Dict[str, Any]:
    """
    Return NAP status, priority adaptation sectors, NDC adaptation component,
    and adaptation ambition score for 30 developing countries.

    Ref: UNFCCC NAP portal; NDC Registry; Paris Agreement Art 7
    """
    submitted = sum(1 for p in NAP_COUNTRY_PROFILES.values() if p["nap_status"] == "Submitted")
    in_progress = sum(1 for p in NAP_COUNTRY_PROFILES.values() if p["nap_status"] == "In-Progress")

    return {
        "status": "success",
        "source": "UNFCCC NAP Portal (2024); NDC Registry",
        "total_countries": len(NAP_COUNTRY_PROFILES),
        "nap_submitted_count": submitted,
        "nap_in_progress_count": in_progress,
        "profiles": NAP_COUNTRY_PROFILES,
    }


@router.get("/ref/hazard-risk-profiles", summary="Hazard risk reduction benchmarks — 10 hazards")
async def ref_hazard_risk_profiles() -> Dict[str, Any]:
    """
    Return risk reduction factors by adaptation measure type, time horizons,
    residual risk floors, and RCP hazard projection multipliers for 10
    climate hazards.

    Ref: IPCC AR6 WG2; World Bank NatCat risk database; GFMA profiles
    """
    rcp_summary: Dict[str, Dict[str, Any]] = {}
    for hazard, scenarios in RCP_HAZARD_PROJECTIONS.items():
        if hazard == "_default":
            continue
        rcp_summary[hazard] = scenarios

    return {
        "status": "success",
        "source": "IPCC AR6 WG2; World Bank NatCat risk database; GFMA Hazard Profiles",
        "total_hazards": len([k for k in HAZARD_RISK_REDUCTION_PROFILES]),
        "hazard_profiles": HAZARD_RISK_REDUCTION_PROFILES,
        "rcp_hazard_projections": rcp_summary,
        "gari_scoring_criteria": {
            k: {
                "weight": v["weight"],
                "description": v["description"],
                "gari_ref": v["gari_ref"],
            }
            for k, v in GARI_SCORING_CRITERIA.items()
        },
        "discount_rates_by_context": DISCOUNT_RATES_BY_CONTEXT,
    }
