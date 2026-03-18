"""
API Routes: EU ETS Phase 4 Engine
====================================
POST /api/v1/eu-ets/free-allocation         — Calculate free allocation for an installation
POST /api/v1/eu-ets/compliance              — Assess compliance position
POST /api/v1/eu-ets/carbon-price-forecast   — Carbon price forecast under scenarios
POST /api/v1/eu-ets/cap-trajectory          — ETS cap trajectory with LRF
POST /api/v1/eu-ets/ets2-readiness          — ETS2 readiness assessment (buildings/transport)
GET  /api/v1/eu-ets/ref/benchmarks          — Product benchmark values
GET  /api/v1/eu-ets/ref/price-scenarios     — Carbon price scenario paths
GET  /api/v1/eu-ets/ref/cbam-phaseout       — CBAM free allocation phase-out schedule
GET  /api/v1/eu-ets/ref/cap-parameters      — ETS cap and MSR parameters
GET  /api/v1/eu-ets/ref/leakage-tiers       — Carbon leakage risk tiers
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.eu_ets_engine import EUETSEngine

router = APIRouter(prefix="/api/v1/eu-ets", tags=["EU ETS"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class FreeAllocationRequest(BaseModel):
    installation_id: str
    installation_name: str = ""
    sector: str
    product_benchmark: str
    year: int = Field(2025, ge=2021, le=2050)
    historical_activity_level: float = Field(0, ge=0)
    carbon_leakage_listed: bool = True
    carbon_price_eur: float = Field(80.0, ge=0)


class ComplianceRequest(BaseModel):
    installation_id: str
    year: int = Field(2025, ge=2021, le=2050)
    verified_emissions_tco2: float = Field(0, ge=0)
    free_allocation_tco2: float = Field(0, ge=0)
    purchased_allowances_tco2: float = Field(0, ge=0)
    banked_allowances_tco2: float = Field(0, ge=0)
    carbon_price_eur: float = Field(80.0, ge=0)


class PriceForecastRequest(BaseModel):
    scenario: str = "FIT_FOR_55"
    current_price_eur: float = Field(80.0, ge=0)


class CapTrajectoryRequest(BaseModel):
    start_year: int = Field(2021, ge=2005, le=2050)
    end_year: int = Field(2050, ge=2021, le=2060)


class ETS2ReadinessRequest(BaseModel):
    """ETS2 readiness assessment request (E8 enhanced).

    New optional fields mirror the enhanced assess_ets2_readiness() parameters.
    All default to backward-compatible values so existing callers are unaffected.
    """
    entity_id: str
    entity_name: str = ""
    fuel_type: str = "diesel"
    annual_fuel_volume_litres: float = Field(0, ge=0)
    annual_fuel_volume_kg: float = Field(0.0, ge=0,
        description="Gaseous fuel volume in kg (alternative to litres)")
    emission_factor_kgco2_per_litre: float = Field(0.0, ge=0,
        description="Override EF; 0 = resolve from ETS2_EMISSION_FACTORS table")
    carbon_price_eur: float = Field(45.0, ge=0,
        description="Expected ETS2 carbon price (will be floored at Art. 30d corridor)")
    # Compliance readiness factors (Art. 30a-30j)
    has_mrv_system: bool = Field(False,
        description="Art. 30c — MRV system in place")
    monitoring_plan_submitted: bool = Field(False,
        description="Art. 30c §2 — monitoring plan submitted to competent authority")
    has_registry_account: bool = Field(False,
        description="Art. 30d — ETS2 registry account opened")
    has_verified_emissions_report: bool = Field(False,
        description="Art. 30e — accredited-verifier emissions report available")
    fuel_volume_data_quality: str = Field("estimated",
        description="'measured' | 'calculated' | 'estimated' (affects readiness score)")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/free-allocation")
def calculate_free_allocation(req: FreeAllocationRequest):
    """Calculate free allowance allocation for an installation."""
    engine = EUETSEngine()
    r = engine.calculate_free_allocation(
        req.installation_id, req.installation_name, req.sector,
        req.product_benchmark, req.year, req.historical_activity_level,
        req.carbon_leakage_listed, req.carbon_price_eur,
    )
    return {
        "installation_id": r.installation_id,
        "installation_name": r.installation_name,
        "sector": r.sector,
        "product_benchmark": r.product_benchmark,
        "year": r.year,
        "historical_activity_level": r.historical_activity_level,
        "benchmark_value": r.benchmark_value,
        "preliminary_allocation_tco2": r.preliminary_allocation_tco2,
        "carbon_leakage_factor": r.carbon_leakage_factor,
        "cross_sectoral_correction": r.cross_sectoral_correction,
        "cbam_reduction_factor": r.cbam_reduction_factor,
        "final_allocation_tco2": r.final_allocation_tco2,
        "auction_exposure_tco2": r.auction_exposure_tco2,
        "auction_cost_eur": r.auction_cost_eur,
    }


@router.post("/compliance")
def assess_compliance(req: ComplianceRequest):
    """Assess installation compliance position."""
    engine = EUETSEngine()
    r = engine.assess_compliance(
        req.installation_id, req.year, req.verified_emissions_tco2,
        req.free_allocation_tco2, req.purchased_allowances_tco2,
        req.banked_allowances_tco2, req.carbon_price_eur,
    )
    return {
        "installation_id": r.installation_id,
        "year": r.year,
        "verified_emissions_tco2": r.verified_emissions_tco2,
        "free_allocation_tco2": r.free_allocation_tco2,
        "purchased_allowances_tco2": r.purchased_allowances_tco2,
        "banked_allowances_tco2": r.banked_allowances_tco2,
        "total_holdings_tco2": r.total_holdings_tco2,
        "surrender_obligation_tco2": r.surrender_obligation_tco2,
        "surplus_deficit_tco2": r.surplus_deficit_tco2,
        "compliance_status": r.compliance_status,
        "estimated_purchase_cost_eur": r.estimated_purchase_cost_eur,
        "penalty_exposure_eur": r.penalty_exposure_eur,
    }


@router.post("/carbon-price-forecast")
def forecast_carbon_price(req: PriceForecastRequest):
    """Forecast EU ETS carbon price under a scenario."""
    engine = EUETSEngine()
    r = engine.forecast_carbon_price(req.scenario, req.current_price_eur)
    return {
        "scenario": r.scenario,
        "prices_by_year": r.prices_by_year,
        "cagr_pct": r.cagr_pct,
        "price_current_eur": r.price_current_eur,
        "price_2030_eur": r.price_2030_eur,
        "price_2050_eur": r.price_2050_eur,
        "volatility_annual_pct": r.volatility_annual_pct,
    }


@router.post("/cap-trajectory")
def compute_cap_trajectory(req: CapTrajectoryRequest):
    """Compute EU ETS cap trajectory with linear reduction factor."""
    engine = EUETSEngine()
    return {"cap_trajectory": engine.compute_cap_trajectory(req.start_year, req.end_year)}


@router.post("/ets2-readiness")
def assess_ets2_readiness(req: ETS2ReadinessRequest):
    """Assess ETS2 readiness for building/transport fuel distributors."""
    engine = EUETSEngine()
    r = engine.assess_ets2_readiness(
        entity_id=req.entity_id,
        entity_name=req.entity_name,
        fuel_type=req.fuel_type,
        annual_fuel_volume_litres=req.annual_fuel_volume_litres,
        annual_fuel_volume_kg=req.annual_fuel_volume_kg,
        emission_factor_kgco2_per_litre=req.emission_factor_kgco2_per_litre,
        carbon_price_eur=req.carbon_price_eur,
        has_mrv_system=req.has_mrv_system,
        monitoring_plan_submitted=req.monitoring_plan_submitted,
        has_registry_account=req.has_registry_account,
        has_verified_emissions_report=req.has_verified_emissions_report,
        fuel_volume_data_quality=req.fuel_volume_data_quality,
    )
    return {
        "entity_id": r.entity_id,
        "entity_name": r.entity_name,
        "ets2_eligible": r.ets2_eligible,
        "fuel_type": r.fuel_type,
        "annual_emissions_tco2": r.annual_emissions_tco2,
        "estimated_allowance_cost_eur": r.estimated_allowance_cost_eur,
        "pass_through_potential_pct": r.pass_through_potential_pct,
        "consumer_impact_eur_per_litre": r.consumer_impact_eur_per_litre,
        "readiness_score": r.readiness_score,
        "gaps": r.gaps,
        "recommendations": r.recommendations,
    }


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/benchmarks")
def ref_benchmarks():
    """
    Product benchmark values for the current active allocation period.
    GAP-012: Returns 2026-2030 values (Decision EU 2024/903) when today >= 2026-01-01,
    otherwise 2021-2025 values (Decision EU 2021/927).
    DB-first with hardcoded fallback.
    """
    return {"product_benchmarks": EUETSEngine.get_product_benchmarks()}


@router.get("/ref/benchmarks/all")
def ref_benchmarks_all():
    """
    All benchmark rows across all allocation periods (2021-2025 and 2026-2030).
    GAP-012: Surfaces the full versioned benchmark history from ets_product_benchmarks table.
    """
    return {
        "product_benchmarks": EUETSEngine.get_product_benchmarks_all_periods(),
        "note": "Source: Decision (EU) 2021/927 (2021-2025) · Decision (EU) 2024/903 (2026-2030)",
    }


@router.get("/ref/price-scenarios")
def ref_price_scenarios():
    """Carbon price scenario paths."""
    return {"carbon_price_scenarios": EUETSEngine.get_carbon_price_scenarios()}


@router.get("/ref/cbam-phaseout")
def ref_cbam_phaseout():
    """CBAM free allocation phase-out schedule."""
    return {"cbam_phaseout": EUETSEngine.get_cbam_phaseout_schedule()}


@router.get("/ref/cap-parameters")
def ref_cap_parameters():
    """ETS cap and MSR parameters."""
    return {"ets_cap_parameters": EUETSEngine.get_ets_cap_parameters()}


@router.get("/ref/leakage-tiers")
def ref_leakage_tiers():
    """Carbon leakage risk tier definitions."""
    return {"carbon_leakage_tiers": EUETSEngine.get_carbon_leakage_tiers()}
