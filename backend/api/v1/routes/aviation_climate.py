"""
API Routes: Aviation Climate Engine
=====================================
POST /api/v1/aviation-climate/corsia           — CORSIA Phase 2 obligation
POST /api/v1/aviation-climate/saf-compliance   — SAF blending mandate compliance
POST /api/v1/aviation-climate/ira-45z          — IRA 45Z SAF tax credit
POST /api/v1/aviation-climate/eu-ets           — EU ETS Aviation obligation
POST /api/v1/aviation-climate/iata-nzc         — IATA Net Zero pathway alignment
POST /api/v1/aviation-climate/aircraft-stranding — Aircraft asset stranding
POST /api/v1/aviation-climate/full-assessment  — Complete operator assessment
GET  /api/v1/aviation-climate/ref/corsia-phases      — CORSIA phase parameters
GET  /api/v1/aviation-climate/ref/saf-mandates        — SAF blending mandates
GET  /api/v1/aviation-climate/ref/aircraft-intensity  — Aircraft CO2 intensity
GET  /api/v1/aviation-climate/ref/iata-nzc-pathway    — IATA NZC pathway split
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

try:
    from services.aviation_climate_engine import (
        AviationClimateEngine,
        CORSIA_PHASES,
        REFUELEU_SAF_MANDATES,
        EU_ETS_AVIATION,
        IATA_NZC_PATHWAY,
        AIRCRAFT_CO2_INTENSITY,
        AIRCRAFT_STRANDING_TIMELINE,
        SAF_COST_PREMIUMS,
        IRA_45Z_SAF_CREDITS,
    )
    _engine = AviationClimateEngine()
except Exception:
    _engine = None
    CORSIA_PHASES = {}
    REFUELEU_SAF_MANDATES = {}
    EU_ETS_AVIATION = {}
    IATA_NZC_PATHWAY = {}
    AIRCRAFT_CO2_INTENSITY = {}
    AIRCRAFT_STRANDING_TIMELINE = {}
    SAF_COST_PREMIUMS = {}
    IRA_45Z_SAF_CREDITS = {}

router = APIRouter(prefix="/api/v1/aviation-climate", tags=["Aviation Climate"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CORSIARequest(BaseModel):
    entity_id: str
    icao_designator: str = "EZY"
    baseline_tco2: float = Field(500_000.0, gt=0)
    actual_tco2: float = Field(530_000.0, gt=0)
    phase: str = "phase_2"
    eligible_routes_pct: float = Field(100.0, ge=0, le=100)

    class Config:
        extra = "allow"


class SAFComplianceRequest(BaseModel):
    entity_id: str
    total_fuel_uplift_t: float = Field(200_000.0, gt=0)
    saf_blended_t: float = Field(4_000.0, ge=0)
    year: int = 2025
    jurisdiction: str = "EU"

    class Config:
        extra = "allow"


class IRA45ZRequest(BaseModel):
    entity_id: str
    saf_volume_gge: float = Field(1_000_000.0, gt=0)
    saf_pathway: str = "HEFA"
    lifecycle_ci: float = Field(35.0, ge=0)

    class Config:
        extra = "allow"


class EUETSAviationRequest(BaseModel):
    entity_id: str
    intra_eea_co2_t: float = Field(120_000.0, gt=0)
    year: int = 2025

    class Config:
        extra = "allow"


class IATANZCRequest(BaseModel):
    entity_id: str
    current_intensity: float = Field(78.0, gt=0)
    fleet_mix: dict = {}
    saf_pct: float = Field(2.0, ge=0)
    year: int = 2030

    class Config:
        extra = "allow"


class AircraftStrandingRequest(BaseModel):
    entity_id: str
    fleet_data: list[dict] = []

    class Config:
        extra = "allow"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    operator_data: dict = {}

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock(entity_id: str, endpoint: str) -> dict:
    return {
        "status": "success",
        "data": {
            "entity_id": entity_id,
            "endpoint": endpoint,
            "note": "engine_unavailable_mock_response",
        },
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/corsia")
def corsia(req: CORSIARequest):
    """CORSIA Phase 2 offsetting obligation (ICAO CORSIA SARPs)."""
    if _engine is None:
        return _mock(req.entity_id, "corsia")
    r = _engine.calculate_corsia_obligation(
        req.entity_id, req.icao_designator, req.baseline_tco2,
        req.actual_tco2, req.phase, req.eligible_routes_pct,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "icao_designator": r.icao_designator,
            "phase": r.phase,
            "baseline_tco2": r.baseline_tco2,
            "actual_tco2": r.actual_tco2,
            "growth_tco2": r.growth_tco2,
            "offset_factor": r.offset_factor,
            "offsetting_obligation_tco2": r.offsetting_obligation_tco2,
            "eligible_units_breakdown": r.eligible_units_breakdown,
            "offset_cost_usd": r.offset_cost_usd,
            "mandatory": r.mandatory,
        },
    }


@router.post("/saf-compliance")
def saf_compliance(req: SAFComplianceRequest):
    """SAF blending mandate compliance — ReFuelEU Aviation (EU 2023/2405)."""
    if _engine is None:
        return _mock(req.entity_id, "saf-compliance")
    r = _engine.assess_saf_compliance(
        req.entity_id, req.total_fuel_uplift_t, req.saf_blended_t, req.year, req.jurisdiction,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "year": r.year,
            "jurisdiction": r.jurisdiction,
            "total_fuel_uplift_t": r.total_fuel_uplift_t,
            "saf_blended_t": r.saf_blended_t,
            "blend_pct": r.blend_pct,
            "mandate_pct": r.mandate_pct,
            "compliance_gap_pct": r.compliance_gap_pct,
            "gap_volume_t": r.gap_volume_t,
            "compliant": r.compliant,
            "penalty_usd": r.penalty_usd,
        },
    }


@router.post("/ira-45z")
def ira_45z(req: IRA45ZRequest):
    """IRA Section 45Z SAF tax credit calculation (US)."""
    if _engine is None:
        return _mock(req.entity_id, "ira-45z")
    r = _engine.calculate_ira_45z(req.entity_id, req.saf_volume_gge, req.saf_pathway, req.lifecycle_ci)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "saf_volume_gge": r.saf_volume_gge,
            "saf_pathway": r.saf_pathway,
            "lifecycle_ci": r.lifecycle_ci,
            "eligible": r.eligible,
            "credit_tier": r.credit_tier,
            "credit_per_gge": r.credit_per_gge,
            "total_credit_usd": r.total_credit_usd,
        },
    }


@router.post("/eu-ets")
def eu_ets(req: EUETSAviationRequest):
    """EU ETS Aviation intra-EEA allowance obligation."""
    if _engine is None:
        return _mock(req.entity_id, "eu-ets")
    r = _engine.assess_eu_ets_aviation(req.entity_id, req.intra_eea_co2_t, req.year)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "year": r.year,
            "intra_eea_co2_t": r.intra_eea_co2_t,
            "free_allocation_pct": r.free_allocation_pct,
            "obligation_allowances": r.obligation_allowances,
            "free_allocation": r.free_allocation,
            "surrender_gap": r.surrender_gap,
            "cost_eur": r.cost_eur,
        },
    }


@router.post("/iata-nzc")
def iata_nzc(req: IATANZCRequest):
    """IATA Net Zero 2050 pathway alignment scoring."""
    if _engine is None:
        return _mock(req.entity_id, "iata-nzc")
    r = _engine.assess_iata_nzc(
        req.entity_id, req.current_intensity, req.fleet_mix, req.saf_pct, req.year,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "year": r.year,
            "current_intensity": r.current_intensity,
            "pathway_target_intensity": r.pathway_target_intensity,
            "alignment_score": r.alignment_score,
            "efficiency_gap": r.efficiency_gap,
            "saf_gap": r.saf_gap,
            "offset_gap": r.offset_gap,
            "overall_aligned": r.overall_aligned,
        },
    }


@router.post("/aircraft-stranding")
def aircraft_stranding(req: AircraftStrandingRequest):
    """Aircraft asset stranding timeline and residual value under NZ2050."""
    if _engine is None:
        return _mock(req.entity_id, "aircraft-stranding")
    r = _engine.model_aircraft_stranding(req.entity_id, req.fleet_data)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "stranding_events": r.stranding_events,
            "total_stranded_value_usd": r.total_stranded_value_usd,
            "fleet_avg_age": r.fleet_avg_age,
            "high_emission_pct": r.high_emission_pct,
            "earliest_stranding_year": r.earliest_stranding_year,
        },
    }


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Consolidated operator assessment across all aviation climate frameworks."""
    if _engine is None:
        return _mock(req.entity_id, "full-assessment")
    r = _engine.generate_full_assessment(req.entity_id, req.operator_data)
    return {"status": "success", "data": r}


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/corsia-phases")
def ref_corsia_phases():
    """CORSIA phase parameters — phases 1-3 timeline, baselines, offset factors."""
    return {"status": "success", "data": CORSIA_PHASES}


@router.get("/ref/saf-mandates")
def ref_saf_mandates():
    """SAF blending mandates by year (ReFuelEU Aviation) and IRA 45Z credit tiers."""
    return {
        "status": "success",
        "data": {
            "refueleu_mandates": REFUELEU_SAF_MANDATES,
            "ira_45z_credits": IRA_45Z_SAF_CREDITS,
            "saf_cost_premiums_usd_per_tonne": SAF_COST_PREMIUMS,
            "eu_ets_aviation_schedule": EU_ETS_AVIATION,
        },
    }


@router.get("/ref/aircraft-intensity")
def ref_aircraft_intensity():
    """Aircraft CO2 intensity (gCO2/pkm) by type and stranding timeline."""
    return {
        "status": "success",
        "data": {
            "co2_intensity_gco2_pkm": AIRCRAFT_CO2_INTENSITY,
            "stranding_timeline_nz2050": AIRCRAFT_STRANDING_TIMELINE,
        },
    }


@router.get("/ref/iata-nzc-pathway")
def ref_iata_nzc_pathway():
    """IATA Net Zero 2050 pathway breakdown by year (efficiency/SAF/removal/offset)."""
    return {"status": "success", "data": IATA_NZC_PATHWAY}
