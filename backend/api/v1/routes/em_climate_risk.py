"""
API Routes — Emerging Market Climate & Transition Risk Engine (E87)
===================================================================
POST /api/v1/em-climate-risk/assess                — full assessment (country_code in body)
POST /api/v1/em-climate-risk/country-risk          — country climate risk
POST /api/v1/em-climate-risk/ifc-ps6               — IFC PS6 biodiversity requirements
POST /api/v1/em-climate-risk/concessional-finance  — concessional finance eligibility
POST /api/v1/em-climate-risk/green-finance-market  — green finance market assessment
POST /api/v1/em-climate-risk/ndc-alignment         — NDC alignment
POST /api/v1/em-climate-risk/portfolio             — portfolio-level EM assessment
GET  /api/v1/em-climate-risk/ref/country-profiles  — full EM_COUNTRY_PROFILES
GET  /api/v1/em-climate-risk/ref/concessional-windows — CONCESSIONAL_FINANCE_WINDOWS
GET  /api/v1/em-climate-risk/ref/ndc-tiers         — NDC_AMBITION_CATEGORIES
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.em_climate_risk_engine import (
    EM_COUNTRY_PROFILES,
    IFC_PS6_THRESHOLDS,
    CONCESSIONAL_FINANCE_WINDOWS,
    GEMS_LOSS_MULTIPLIERS,
    NDC_AMBITION_CATEGORIES,
    EMClimateRiskEngine,
)

router = APIRouter(
    prefix="/api/v1/em-climate-risk",
    tags=["E87 Emerging Market Climate Risk"],
)

_engine = EMClimateRiskEngine()


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------


class FullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    country_code: str = Field(
        ...,
        description="ISO 3166-1 alpha-2 country code. See /ref/country-profiles for supported codes.",
    )
    sector: str = Field(default="industrials")
    exposure_m: float = Field(default=100.0, ge=0, description="Entity exposure in the country $M")
    project_size_m: float = Field(default=25.0, ge=0)
    project_sector: str = Field(default="renewable_energy")
    country_income_group: str = Field(
        default="lower_middle",
        description="low | lower_middle | upper_middle | high",
    )
    government_endorsement: bool = Field(default=True)
    climate_rationale: bool = Field(default=True)
    # IFC PS6 fields
    habitat_type: str = Field(
        default="modified_habitat",
        description="critical_habitat | natural_habitat | modified_habitat",
    )
    iucn_protected_area_km: float = Field(default=15.0, ge=0)
    endangered_species_present: bool = Field(default=False)
    ramsar_site_km: float = Field(default=20.0, ge=0)
    habitat_area_converted_ha: float = Field(default=0.0, ge=0)
    has_biodiversity_plan: bool = Field(default=False)
    has_offset_plan: bool = Field(default=False)
    # NDC fields
    annual_emissions_kt: float = Field(default=100.0, ge=0)
    entity_net_zero_target_year: Optional[int] = Field(default=None)


class CountryRiskRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    exposure_m: float = Field(default=100.0, ge=0, description="Entity exposure $M")
    sector: str = Field(default="industrials")


class IFCPS6Request(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    habitat_type: str = Field(
        default="modified_habitat",
        description="critical_habitat | natural_habitat | modified_habitat",
    )
    iucn_protected_area_km: float = Field(default=15.0, ge=0)
    endangered_species_present: bool = Field(default=False)
    ramsar_site_km: float = Field(default=20.0, ge=0)
    habitat_area_converted_ha: float = Field(default=0.0, ge=0)
    has_biodiversity_plan: bool = Field(default=False)
    has_offset_plan: bool = Field(default=False)
    project_type: str = Field(default="infrastructure")
    project_size_m: float = Field(default=50.0, ge=0)


class ConcessionalFinanceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    project_size_m: float = Field(default=25.0, ge=0)
    project_sector: str = Field(default="renewable_energy")
    country_income_group: str = Field(
        default="lower_middle",
        description="low | lower_middle | upper_middle | high",
    )
    government_endorsement: bool = Field(default=True)
    climate_rationale: bool = Field(default=True)


class GreenFinanceMarketRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field(default="")
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")


class NDCAlignmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    sector: str = Field(default="industrials")
    annual_emissions_kt: float = Field(default=100.0, ge=0)
    entity_net_zero_target_year: Optional[int] = Field(default=None)


class PortfolioExposureItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    country_code: str
    exposure_m: float = Field(..., gt=0)
    sector: str = Field(default="industrials")


class PortfolioRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    exposures: list[PortfolioExposureItem] = Field(
        ..., min_length=1, description="List of country exposures"
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _req_to_entity(req: Any) -> dict:
    return req.model_dump()


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------


@router.post("/assess")
async def full_assessment(req: FullAssessmentRequest):
    """
    Run the complete E87 Emerging Market Climate & Transition Risk assessment
    for a single country exposure.

    Orchestrates country climate risk composite, IFC PS6 biodiversity
    compliance, concessional finance eligibility across 8 facilities,
    green finance market depth and NDC alignment.

    Returns: em_climate_composite (0-100), risk_tier, opportunity_tier,
    physical_risk_score, transition_readiness_score, ndc_ambition_score,
    ifc_ps6_score, blended_finance_potential, gcf_allocation_bn,
    gems_climate_uplift_pct — plus full sub-assessment detail blocks.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.run_full_assessment(entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/country-risk")
async def country_climate_risk(req: CountryRiskRequest):
    """
    Assess country-level EM climate risk.

    Pulls EM_COUNTRY_PROFILES data, computes physical/transition/NDC/fossil
    weighted composite score (0-100), assigns risk tier and GEMS
    climate-adjusted expected annual loss estimate.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.assess_country_climate_risk(req.country_code, entity_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ifc-ps6")
async def ifc_ps6_requirements(req: IFCPS6Request):
    """
    Assess IFC Performance Standard 6 biodiversity requirements.

    Determines applicable tier (critical_habitat / natural_habitat /
    modified_habitat), scores compliance against 6 criteria,
    calculates biodiversity offset requirement and identifies gaps.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.assess_ifc_ps6_requirements(entity_data, req.country_code)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/concessional-finance")
async def concessional_finance_eligibility(req: ConcessionalFinanceRequest):
    """
    Assess concessional finance eligibility across all 8 facilities
    (GCF, GEF, AIIB, ADB, IADB, EIB, AFD, World Bank Climate).

    Returns eligibility score per facility, prioritised top-3 pipeline,
    blended finance potential score (0-100) and grant element ranges.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.assess_concessional_finance_eligibility(entity_data, req.country_code)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/green-finance-market")
async def green_finance_market(req: GreenFinanceMarketRequest):
    """
    Assess EM green bond market depth and sustainable finance opportunity.

    Returns green bond market size, market depth tier (deep / developing /
    nascent / pre-market), estimated pipeline, sustainable finance depth
    score, local currency risk and strategic recommendations.
    """
    try:
        result = _engine.assess_green_finance_market(req.country_code)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ndc-alignment")
async def ndc_alignment(req: NDCAlignmentRequest):
    """
    Assess NDC ambition and alignment for an entity operating in an EM country.

    Returns NDC tier (highly_ambitious / ambitious / moderate / insufficient),
    alignment gap to 'ambitious' threshold, required policy changes,
    just transition risk score and investor implications.
    """
    try:
        entity_data = _req_to_entity(req)
        result = _engine.compute_ndc_alignment(entity_data, req.country_code)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/portfolio")
async def portfolio_assessment(req: PortfolioRequest):
    """
    Portfolio-level EM climate risk assessment aggregating multiple
    country exposures.

    Computes exposure-weighted composite scores, country risk breakdown,
    total GEMS expected annual loss, highest-risk and most-concentrated
    country identification.
    """
    try:
        portfolio_data = {
            "entity_id": req.entity_id,
            "exposures": [e.model_dump() for e in req.exposures],
        }
        result = _engine.run_portfolio_assessment(portfolio_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference data endpoints
# ---------------------------------------------------------------------------


@router.get("/ref/country-profiles")
async def ref_country_profiles():
    """
    Return the full EM_COUNTRY_PROFILES for all 50 emerging market countries.

    Includes physical_risk_score (0-100), transition_readiness_score,
    ndc_ambition_score, nd_gain_score, fossil_fuel_dependency_pct,
    renewable_capacity_gw, carbon_intensity_gdp, just_transition_risk,
    gcf_allocation_bn, gems_historical_loss_bn and green_bond_market_size_bn.
    """
    return {
        "status": "success",
        "country_count": len(EM_COUNTRY_PROFILES),
        "data_sources": [
            "ND-GAIN Country Index 2024",
            "IEA World Energy Outlook 2024",
            "UNFCCC NDC Registry 2025",
            "GCF Portfolio Dashboard 2024",
            "PCAF GEMS Database",
            "BloombergNEF EM Green Finance 2024",
        ],
        "data": EM_COUNTRY_PROFILES,
    }


@router.get("/ref/concessional-windows")
async def ref_concessional_windows():
    """
    Return CONCESSIONAL_FINANCE_WINDOWS — the 8 concessional finance facilities
    (GCF, GEF, AIIB, ADB, IADB, EIB, AFD, World Bank Climate).

    Includes manager, focus areas, minimum project size, eligibility criteria,
    blended finance flag, grant element range and co-financing ratios.
    """
    return {
        "status": "success",
        "facility_count": len(CONCESSIONAL_FINANCE_WINDOWS),
        "data": CONCESSIONAL_FINANCE_WINDOWS,
    }


@router.get("/ref/ndc-tiers")
async def ref_ndc_tiers():
    """
    Return NDC_AMBITION_CATEGORIES — the 4 NDC ambition tiers used in
    NDC alignment scoring.

    Includes score range, tier label, description, climate ratings
    alignment (Climate Action Tracker) and investor implications per tier.
    """
    return {
        "status": "success",
        "tier_count": len(NDC_AMBITION_CATEGORIES),
        "standard": "UNFCCC NDC Registry — Paris Agreement Article 4; Climate Action Tracker methodology",
        "data": NDC_AMBITION_CATEGORIES,
    }


@router.get("/ref/gems-multipliers")
async def ref_gems_multipliers():
    """
    Return GEMS_LOSS_MULTIPLIERS — regional climate uplift percentages
    applied to historical GEMS loss data for forward-looking expected
    annual loss estimation.
    """
    return {
        "status": "success",
        "methodology": "PCAF GEMS Database; IPCC AR6 WG2 regional damage function uplift",
        "region_count": len(GEMS_LOSS_MULTIPLIERS),
        "data": GEMS_LOSS_MULTIPLIERS,
    }


@router.get("/ref/ifc-ps6-thresholds")
async def ref_ifc_ps6_thresholds():
    """
    Return IFC_PS6_THRESHOLDS — the 3 biodiversity habitat tiers
    (critical_habitat, natural_habitat, modified_habitat) with
    requirements, offset ratios, trigger indicators and net gain standards.
    """
    return {
        "status": "success",
        "standard": "IFC Performance Standard 6 — Biodiversity Conservation and Sustainable Management (2012)",
        "tier_count": len(IFC_PS6_THRESHOLDS),
        "data": IFC_PS6_THRESHOLDS,
    }
