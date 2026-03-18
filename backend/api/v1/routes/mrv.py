"""
Climate Data & MRV Infrastructure  —  E73 Routes
=================================================
Prefix: /api/v1/mrv
"""
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.mrv_engine import (
    assess_mrv_tier,
    calculate_data_quality,
    verify_satellite_coverage,
    score_verification_readiness,
    generate_mrv_improvement_plan,
    MRV_TIERS,
    SATELLITE_PLATFORMS,
    VERIFICATION_BODIES,
    IPCC_UNCERTAINTY_TIERS,
    CDP_CDSB_REQUIREMENTS,
)

router = APIRouter(prefix="/api/v1/mrv", tags=["E73 Climate Data & MRV Infrastructure"])


# ── Pydantic Request Models ───────────────────────────────────────────────────

class MRVTierRequest(BaseModel):
    entity_id: str
    facility_type: str = Field("manufacturing", description="Facility type (e.g. manufacturing, power_plant, oil_gas)")
    current_capabilities: dict = Field(
        default_factory=dict,
        description="Dict of capabilities: erp_integrated, iot_sensors, satellite, ai_analytics, blockchain",
    )


class DataQualityRequest(BaseModel):
    entity_id: str
    emission_sources: list[dict] = Field(
        default_factory=list,
        description="List of dicts with keys: source, method (Tier1/2/3), value_tco2e",
    )
    measurement_methods: list[str] = Field(default_factory=list)


class SatelliteCoverageRequest(BaseModel):
    entity_id: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    facility_size_ha: float = Field(..., gt=0)


class VerificationReadinessRequest(BaseModel):
    entity_id: str
    standard: str = Field("ISO_14064_3", description="Assurance standard (ISO_14064_3 / ISAE_3410 / ISSA_5000)")
    scope_1_2_3: dict = Field(
        default_factory=dict,
        description="Keys: scope1_tco2e, scope2_tco2e, scope3_tco2e",
    )


class ImprovementPlanRequest(BaseModel):
    entity_id: str
    current_tier: int = Field(..., ge=1, le=5)
    target_tier: int = Field(..., ge=2, le=5)
    budget_usd: float = Field(..., gt=0)


# ── POST Endpoints ────────────────────────────────────────────────────────────

@router.post("/tier-assessment", summary="Assess current MRV tier and upgrade roadmap")
async def post_mrv_tier(req: MRVTierRequest) -> dict[str, Any]:
    """
    Assess the facility's current MRV tier (1-5: manual → blockchain-attested).

    Returns ISO 14064-3:2019 verification requirements, gap analysis to next
    tier, IPCC uncertainty range, and DQS quality score.
    """
    try:
        return assess_mrv_tier(
            entity_id=req.entity_id,
            facility_type=req.facility_type,
            current_capabilities=req.current_capabilities,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/data-quality", summary="Score MRV data quality (IPCC / PCAF DQS / CDP CDSB)")
async def post_data_quality(req: DataQualityRequest) -> dict[str, Any]:
    """
    Score MRV data quality across emission sources.

    Applies IPCC Tier 1/2/3 uncertainty ranges, PCAF-style DQS 1-5 mapping,
    CDP CDSB compliance checks and AI-assisted anomaly detection scoring.
    """
    try:
        return calculate_data_quality(
            entity_id=req.entity_id,
            emission_sources=req.emission_sources,
            measurement_methods=req.measurement_methods,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/satellite-coverage", summary="Verify satellite GHG detection coverage")
async def post_satellite_coverage(req: SatelliteCoverageRequest) -> dict[str, Any]:
    """
    Assess satellite GHG detection coverage for a facility location.

    Evaluates TROPOMI, GHGSat, Copernicus Sentinel-5P and Carbon Mapper
    against facility size, latitude, cloud cover and detection limits.
    """
    try:
        return verify_satellite_coverage(
            entity_id=req.entity_id,
            lat=req.lat,
            lng=req.lng,
            facility_size_ha=req.facility_size_ha,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/verification-readiness", summary="Score verification readiness (ISO 14064-3 / ISAE 3410 / ISSA 5000)")
async def post_verification_readiness(req: VerificationReadinessRequest) -> dict[str, Any]:
    """
    Score readiness for third-party GHG verification.

    Covers ISO 14064-3:2019 (limited/reasonable assurance), ISAE 3410
    equivalence and ISSA 5000 (IAASB 2024) preparation score.
    """
    try:
        return score_verification_readiness(
            entity_id=req.entity_id,
            standard=req.standard,
            scope_1_2_3=req.scope_1_2_3,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/improvement-plan", summary="Generate MRV upgrade improvement plan")
async def post_improvement_plan(req: ImprovementPlanRequest) -> dict[str, Any]:
    """
    Generate MRV upgrade plan from current tier to target tier.

    Models technology costs (IoT / CEMS / satellite subscriptions /
    AI analytics / blockchain), 12-36 month timeline, and ROI from
    data quality improvement (lower audit costs + carbon credit premiums).
    """
    try:
        if req.target_tier <= req.current_tier:
            raise HTTPException(
                status_code=400,
                detail=f"target_tier ({req.target_tier}) must be greater than current_tier ({req.current_tier})",
            )
        return generate_mrv_improvement_plan(
            entity_id=req.entity_id,
            current_tier=req.current_tier,
            target_tier=req.target_tier,
            budget_usd=req.budget_usd,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Reference GET Endpoints ───────────────────────────────────────────────────

@router.get("/ref/tiers", summary="Reference: MRV tier definitions")
async def get_mrv_tiers() -> dict[str, Any]:
    """Return the 5 MRV tier definitions with descriptions, data sources and uncertainty ranges."""
    return {
        "mrv_tiers": {
            str(k): {
                "name": v["name"],
                "description": v["description"],
                "iso14064_level": v["iso14064_level"],
                "ipcc_tier": v["ipcc_tier"],
                "typical_uncertainty_pct_range": list(v["typical_uncertainty_pct"]),
                "data_sources": v["data_sources"],
            }
            for k, v in MRV_TIERS.items()
        }
    }


@router.get("/ref/standards", summary="Reference: verification standards")
async def get_verification_standards() -> dict[str, Any]:
    """Return supported GHG verification standards and assurance levels."""
    return {
        "standards": {
            "ISO_14064_3": {
                "full_name": "ISO 14064-3:2019 Specification for verification and validation of GHG statements",
                "assurance_levels": ["limited", "reasonable"],
                "scope": "Scope 1, 2 and 3 emissions",
            },
            "ISAE_3410": {
                "full_name": "ISAE 3410 Assurance Engagements on GHG Statements",
                "assurance_levels": ["limited", "reasonable"],
                "scope": "Financial statement-style assurance",
            },
            "ISSA_5000": {
                "full_name": "ISSA 5000 General Requirements for Sustainability Assurance (IAASB 2024)",
                "assurance_levels": ["limited", "reasonable"],
                "scope": "Full sustainability reporting",
            },
            "CDP_CDSB": {
                "full_name": "CDP CDSB Framework Application Guidance 2022",
                "assurance_levels": ["data_validation"],
                "scope": "Climate and environmental disclosures",
            },
        }
    }


@router.get("/ref/satellite-platforms", summary="Reference: satellite GHG detection platforms")
async def get_satellite_platforms() -> dict[str, Any]:
    """Return TROPOMI, GHGSat, Sentinel-5P and Carbon Mapper specifications."""
    return {"satellite_platforms": SATELLITE_PLATFORMS}


@router.get("/ref/verification-bodies", summary="Reference: accredited verification bodies")
async def get_verification_bodies() -> dict[str, Any]:
    """Return accredited third-party verifiers with accreditation scope."""
    return {"verification_bodies": VERIFICATION_BODIES}


@router.get("/ref/uncertainty-tiers", summary="Reference: IPCC uncertainty tiers")
async def get_uncertainty_tiers() -> dict[str, Any]:
    """Return IPCC Tier 1/2/3 uncertainty guidelines and data requirements."""
    return {
        "ipcc_uncertainty_tiers": IPCC_UNCERTAINTY_TIERS,
        "cdp_cdsb_requirements": CDP_CDSB_REQUIREMENTS,
    }
