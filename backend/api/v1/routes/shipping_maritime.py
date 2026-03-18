"""
API Routes: Shipping & Maritime Climate Engine
===============================================
POST /api/v1/shipping-maritime/cii-rating       — CII annual rating calculation
POST /api/v1/shipping-maritime/eexi             — EEXI technical efficiency
POST /api/v1/shipping-maritime/poseidon-principles — Poseidon Principles alignment
POST /api/v1/shipping-maritime/fueleu           — FuelEU Maritime compliance
POST /api/v1/shipping-maritime/ets-obligation   — EU ETS Shipping obligation
POST /api/v1/shipping-maritime/fuel-switch      — Alternative fuel transition economics
POST /api/v1/shipping-maritime/fleet-portfolio  — Fleet-level portfolio assessment
POST /api/v1/shipping-maritime/full-assessment  — Complete vessel assessment
GET  /api/v1/shipping-maritime/ref/vessel-types        — Vessel type constants
GET  /api/v1/shipping-maritime/ref/cii-requirements    — CII required reductions by year
GET  /api/v1/shipping-maritime/ref/fueleu-targets      — FuelEU GHG targets 2025-2050
GET  /api/v1/shipping-maritime/ref/fuel-emission-factors — Fuel emission factors
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

try:
    from services.shipping_maritime_engine import (
        ShippingMaritimeEngine,
        VESSEL_TYPES,
        CII_REQUIRED_REDUCTION,
        FUELEU_GHG_TARGETS,
        FUEL_EMISSION_FACTORS,
        SEA_CARGO_CHARTER_BENCHMARKS,
        ALTERNATIVE_FUEL_READINESS,
    )
    _engine = ShippingMaritimeEngine()
except Exception:
    _engine = None
    VESSEL_TYPES = {}
    CII_REQUIRED_REDUCTION = {}
    FUELEU_GHG_TARGETS = {}
    FUEL_EMISSION_FACTORS = {}
    SEA_CARGO_CHARTER_BENCHMARKS = {}
    ALTERNATIVE_FUEL_READINESS = {}

router = APIRouter(prefix="/api/v1/shipping-maritime", tags=["Shipping & Maritime"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CIIRequest(BaseModel):
    entity_id: str
    vessel_type: str = "bulk_carrier"
    dwt: float = Field(50000.0, gt=0)
    distance_nm: float = Field(80000.0, gt=0)
    fuel_consumed_t: float = Field(3000.0, gt=0)
    fuel_type: str = "HFO"
    year: int = 2025

    class Config:
        extra = "allow"


class EEXIRequest(BaseModel):
    entity_id: str
    vessel_type: str = "bulk_carrier"
    dwt: float = Field(50000.0, gt=0)
    installed_power_kw: float = Field(8000.0, gt=0)
    service_speed_knots: float = Field(13.0, gt=0)
    epl_applied: bool = False
    epl_power_kw: float = 0.0

    class Config:
        extra = "allow"


class PoseidonRequest(BaseModel):
    entity_id: str
    vessel_type: str = "bulk_carrier"
    dwt: float = Field(50000.0, gt=0)
    actual_intensity: float = Field(6.0, gt=0)
    pp_year: int = 2025

    class Config:
        extra = "allow"


class FuelEURequest(BaseModel):
    entity_id: str
    annual_energy_mj: float = Field(120_000_000.0, gt=0)
    ghg_intensity_wtw: float = Field(91.16, gt=0)
    year: int = 2025

    class Config:
        extra = "allow"


class ETSRequest(BaseModel):
    entity_id: str
    co2_tonne_pa: float = Field(10000.0, gt=0)
    voyage_types: list[str] = []
    year: int = 2025

    class Config:
        extra = "allow"


class FuelSwitchRequest(BaseModel):
    entity_id: str
    vessel_type: str = "bulk_carrier"
    current_fuel: str = "HFO"
    target_fuel: str = "LNG"
    fleet_size: int = Field(5, gt=0)
    voyage_profile: dict = {}

    class Config:
        extra = "allow"


class FleetPortfolioRequest(BaseModel):
    entity_id: str
    vessel_list: list[dict] = []

    class Config:
        extra = "allow"


class FullAssessmentRequest(BaseModel):
    entity_id: str
    vessel_data: dict = {}

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# Helper: mock response
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

@router.post("/cii-rating")
def cii_rating(req: CIIRequest):
    """CII annual rating (A-E) per MARPOL Annex VI Reg 24."""
    if _engine is None:
        return _mock(req.entity_id, "cii-rating")
    r = _engine.calculate_cii(
        req.entity_id, req.vessel_type, req.dwt, req.distance_nm,
        req.fuel_consumed_t, req.fuel_type, req.year,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "vessel_type": r.vessel_type,
            "year": r.year,
            "cii_attained": r.cii_attained,
            "cii_required": r.cii_required,
            "ratio": r.ratio,
            "rating": r.rating,
            "reduction_target_pct": r.reduction_target_pct,
            "year_to_d_rating": r.year_to_d_rating,
            "fuel_type": r.fuel_type,
            "co2_emitted_t": r.co2_emitted_t,
        },
    }


@router.post("/eexi")
def eexi(req: EEXIRequest):
    """EEXI technical efficiency assessment (MARPOL Annex VI Reg 21)."""
    if _engine is None:
        return _mock(req.entity_id, "eexi")
    r = _engine.calculate_eexi(
        req.entity_id, req.vessel_type, req.dwt, req.installed_power_kw,
        req.service_speed_knots, req.epl_applied, req.epl_power_kw,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "vessel_type": r.vessel_type,
            "eexi_attained": r.eexi_attained,
            "eexi_required": r.eexi_required,
            "compliant": r.compliant,
            "margin_pct": r.margin_pct,
            "epl_applied": r.epl_applied,
            "epl_power_kw": r.epl_power_kw,
        },
    }


@router.post("/poseidon-principles")
def poseidon_principles(req: PoseidonRequest):
    """Poseidon Principles climate alignment scoring."""
    if _engine is None:
        return _mock(req.entity_id, "poseidon-principles")
    r = _engine.assess_poseidon_principles(
        req.entity_id, req.vessel_type, req.dwt, req.actual_intensity, req.pp_year,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "vessel_type": r.vessel_type,
            "year": r.year,
            "actual_intensity": r.actual_intensity,
            "required_intensity": r.required_intensity,
            "alignment_score": r.alignment_score,
            "climate_score": r.climate_score,
            "delta_pct": r.delta_pct,
            "trajectory_gap": r.trajectory_gap,
            "aligned": r.aligned,
        },
    }


@router.post("/fueleu")
def fueleu(req: FuelEURequest):
    """FuelEU Maritime GHG intensity compliance and penalty (EU 2023/1805)."""
    if _engine is None:
        return _mock(req.entity_id, "fueleu")
    r = _engine.assess_fueleu(req.entity_id, req.annual_energy_mj, req.ghg_intensity_wtw, req.year)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "year": r.year,
            "ghg_intensity": r.ghg_intensity,
            "target": r.target,
            "compliant": r.compliant,
            "deficit_gco2eq_mj": r.deficit_gco2eq_mj,
            "deficit_energy_mj": r.deficit_energy_mj,
            "penalty_eur": r.penalty_eur,
        },
    }


@router.post("/ets-obligation")
def ets_obligation(req: ETSRequest):
    """EU ETS Shipping allowance obligation with 2024-2026 phase-in."""
    if _engine is None:
        return _mock(req.entity_id, "ets-obligation")
    r = _engine.calculate_ets_obligation(req.entity_id, req.co2_tonne_pa, req.voyage_types, req.year)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "year": r.year,
            "co2_tonne_pa": r.co2_tonne_pa,
            "phase_in_pct": r.phase_in_pct,
            "obligation_allowances": r.obligation_allowances,
            "free_allocation": r.free_allocation,
            "surrender_gap": r.surrender_gap,
            "cost_eur": r.cost_eur,
        },
    }


@router.post("/fuel-switch")
def fuel_switch(req: FuelSwitchRequest):
    """Alternative fuel transition economics — CAPEX, OPEX delta, NPV, payback."""
    if _engine is None:
        return _mock(req.entity_id, "fuel-switch")
    r = _engine.model_fuel_switch(
        req.entity_id, req.vessel_type, req.current_fuel,
        req.target_fuel, req.fleet_size, req.voyage_profile,
    )
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "vessel_type": r.vessel_type,
            "current_fuel": r.current_fuel,
            "target_fuel": r.target_fuel,
            "fleet_size": r.fleet_size,
            "capex_usd": r.capex_usd,
            "opex_delta_usd_pa": r.opex_delta_usd_pa,
            "co2_reduction_tpa": r.co2_reduction_tpa,
            "payback_yrs": r.payback_yrs,
            "npv_usd": r.npv_usd,
            "technology_readiness": r.technology_readiness,
            "availability_score": r.availability_score,
        },
    }


@router.post("/fleet-portfolio")
def fleet_portfolio(req: FleetPortfolioRequest):
    """Fleet-level portfolio CII distribution, PP alignment and ETS obligation."""
    if _engine is None:
        return _mock(req.entity_id, "fleet-portfolio")
    r = _engine.assess_fleet_portfolio(req.entity_id, req.vessel_list)
    return {
        "status": "success",
        "data": {
            "entity_id": r.entity_id,
            "total_vessels": r.total_vessels,
            "cii_distribution": r.cii_distribution,
            "cii_a_pct": r.cii_a_pct,
            "cii_d_or_e_pct": r.cii_d_or_e_pct,
            "pp_alignment_pct": r.pp_alignment_pct,
            "fueleu_total_penalty": r.fueleu_total_penalty,
            "ets_total_obligation": r.ets_total_obligation,
            "stranding_risk_summary": r.stranding_risk_summary,
            "sea_cargo_charter_aligned": r.sea_cargo_charter_aligned,
            "avg_cii_ratio": r.avg_cii_ratio,
        },
    }


@router.post("/full-assessment")
def full_assessment(req: FullAssessmentRequest):
    """Consolidated vessel assessment across all frameworks."""
    if _engine is None:
        return _mock(req.entity_id, "full-assessment")
    r = _engine.generate_full_assessment(req.entity_id, req.vessel_data)
    return {"status": "success", "data": r}


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/vessel-types")
def ref_vessel_types():
    """Vessel type constants — IMO category, CII coeff, EEXI required."""
    return {"status": "success", "data": VESSEL_TYPES}


@router.get("/ref/cii-requirements")
def ref_cii_requirements():
    """CII required reduction percentages by year (2023-2030)."""
    return {"status": "success", "data": CII_REQUIRED_REDUCTION}


@router.get("/ref/fueleu-targets")
def ref_fueleu_targets():
    """FuelEU Maritime GHG intensity targets 2025-2050 (gCO2eq/MJ)."""
    return {"status": "success", "data": FUELEU_GHG_TARGETS}


@router.get("/ref/fuel-emission-factors")
def ref_fuel_emission_factors():
    """Fuel emission factors: CO2/tonne, WtW GHG intensity, LCV."""
    return {
        "status": "success",
        "data": {
            "fuel_factors": FUEL_EMISSION_FACTORS,
            "sea_cargo_charter_benchmarks": SEA_CARGO_CHARTER_BENCHMARKS,
            "alternative_fuel_readiness": ALTERNATIVE_FUEL_READINESS,
        },
    }
