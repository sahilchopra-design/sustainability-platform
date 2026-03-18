"""
Real Asset Decarbonisation  —  E74 Routes
==========================================
Prefix: /api/v1/real-asset-decarb
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.real_asset_decarb_engine import (
    assess_lock_in_risk,
    plan_capex_transition,
    calculate_retrofit_npv,
    model_brown_to_green,
    generate_decarb_roadmap,
    ASSET_TYPES,
    RETROFIT_MEASURES,
    CRREM_PATHWAYS,
    CARBON_PRICE_SCENARIOS,
    CAPEX_ABATEMENT_TECHNOLOGIES,
)

router = APIRouter(prefix="/api/v1/real-asset-decarb", tags=["E74 Real Asset Decarbonisation"])


# ── Pydantic Request Models ───────────────────────────────────────────────────

class LockInRiskRequest(BaseModel):
    entity_id: str
    asset_type: str = Field(
        "office",
        description="Asset type: office/retail/residential/industrial_building/steel_plant/cement_plant/data_centre/logistics",
    )
    age_years: float = Field(..., ge=0)
    capex_cycle_years: float = Field(..., gt=0)
    current_intensity: float = Field(..., ge=0, description="Current carbon intensity kgCO2e/m²")


class CapexTransitionRequest(BaseModel):
    entity_id: str
    asset_type: str = Field("office")
    current_emissions: float = Field(..., gt=0, description="Current total emissions tCO2e")
    target_year: int = Field(2040, ge=2026, le=2060)
    budget_usd: float = Field(..., gt=0)


class RetrofitNPVRequest(BaseModel):
    entity_id: str
    building_type: str = Field("office")
    retrofit_measures: list[str] = Field(
        default_factory=list,
        description="Measures: insulation/hvac_upgrade/glazing/solar_pv/led_lighting/bms/fuel_switch_heat_pump/ccs/electrification",
    )


class BrownToGreenRequest(BaseModel):
    entity_id: str
    portfolio: list[dict] = Field(
        default_factory=list,
        description="Asset dicts: asset_id, asset_type, book_value_usd, floor_area_m2",
    )
    transition_scenarios: list[str] = Field(
        default_factory=lambda: ["1_5C", "2C"],
    )


class DecarbRoadmapRequest(BaseModel):
    entity_id: str
    assets: list[dict] = Field(
        default_factory=list,
        description="Asset dicts: asset_id, asset_type, current_emissions_tco2e, abatement_potential_pct, capex_required_usd",
    )
    budget_constraint: float = Field(..., gt=0)


# ── POST Endpoints ────────────────────────────────────────────────────────────

@router.post("/lock-in-risk", summary="Assess real asset lock-in and stranded cost risk")
async def post_lock_in_risk(req: LockInRiskRequest) -> dict[str, Any]:
    """
    Assess stranded asset lock-in risk.

    Returns lock-in horizon (remaining life), stranded cost USD, CRREM 2.0
    pathway divergence, SBTi sector decarb rate (buildings 7%pa / industry
    4.2%pa / transport 3.8%pa) and carbon price risk ($50-$110/tCO2e 2030).
    """
    try:
        return assess_lock_in_risk(
            entity_id=req.entity_id,
            asset_type=req.asset_type,
            age_years=req.age_years,
            capex_cycle_years=req.capex_cycle_years,
            current_intensity=req.current_intensity,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/capex-transition", summary="Plan capex transition stack")
async def post_capex_transition(req: CapexTransitionRequest) -> dict[str, Any]:
    """
    Build capex transition plan ranked by abatement cost curve.

    Technologies: energy_efficiency → fuel_switch → electrification → CCS →
    renewable_procurement. Returns year-by-year emissions trajectory and
    capital recycling potential from brown asset disposals.
    """
    try:
        return plan_capex_transition(
            entity_id=req.entity_id,
            asset_type=req.asset_type,
            current_emissions=req.current_emissions,
            target_year=req.target_year,
            budget_usd=req.budget_usd,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/retrofit-npv", summary="Calculate retrofit NPV")
async def post_retrofit_npv(req: RetrofitNPVRequest) -> dict[str, Any]:
    """
    Calculate NPV of building retrofit measures at 5%, 7%, 10% discount rates.

    Returns energy savings %, CAPEX/m², annual savings USD, payback period
    and CRREM 2.0 alignment post-retrofit for each measure.
    """
    try:
        return calculate_retrofit_npv(
            entity_id=req.entity_id,
            building_type=req.building_type,
            retrofit_measures=req.retrofit_measures,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/brown-to-green", summary="Model brown-to-green transformation")
async def post_brown_to_green(req: BrownToGreenRequest) -> dict[str, Any]:
    """
    Model brown-to-green portfolio transformation 2025-2050.

    Returns per-asset capex, stranded risk reduction, green value uplift
    (5-15% JLL/CBRE data), portfolio emissions trajectory under 1.5C and 2C.
    """
    try:
        return model_brown_to_green(
            entity_id=req.entity_id,
            portfolio=req.portfolio,
            transition_scenarios=req.transition_scenarios,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/decarb-roadmap", summary="Generate prioritised decarbonisation roadmap")
async def post_decarb_roadmap(req: DecarbRoadmapRequest) -> dict[str, Any]:
    """
    Generate prioritised decarbonisation roadmap within a budget constraint.

    Ranks by cost-effectiveness (tCO2e/$M), identifies quick wins and
    long-horizon investments, sets interim targets aligned with SBTi
    42% reduction by 2030. TCFD and IFRS S2 aligned.
    """
    try:
        return generate_decarb_roadmap(
            entity_id=req.entity_id,
            assets=req.assets,
            budget_constraint=req.budget_constraint,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Reference GET Endpoints ───────────────────────────────────────────────────

@router.get("/ref/asset-types", summary="Reference: real asset types")
async def get_asset_types() -> dict[str, Any]:
    """Return all supported asset types with CRREM pathways and SBTi decarb rates."""
    return {
        "asset_types": {
            k: {
                "sector": v["sector"],
                "typical_life_years": v["typical_life_years"],
                "capex_cycle_years": v["capex_cycle_years"],
                "sbti_decarb_rate_pa_pct": v["sbti_decarb_rate_pa_pct"],
                "crrem_2030_intensity_kgco2_m2": v["crrem_2030_intensity_kgco2_m2"],
                "current_avg_intensity_kgco2_m2": v["current_avg_intensity_kgco2_m2"],
                "green_premium_pct_range": list(v["green_premium_pct_range"]),
                "retrofit_feasibility": v["retrofit_feasibility"],
            }
            for k, v in ASSET_TYPES.items()
        }
    }


@router.get("/ref/retrofit-measures", summary="Reference: retrofit measure library")
async def get_retrofit_measures() -> dict[str, Any]:
    """Return retrofit measure library with energy savings, capex and payback ranges."""
    return {
        "retrofit_measures": {
            k: {
                "description": v["description"],
                "applicable_types": v["applicable_types"],
                "energy_saving_pct_range": list(v["energy_saving_pct"]),
                "capex_per_m2_usd_range": list(v["capex_per_m2_usd"]),
                "lifespan_years": v["lifespan_years"],
                "payback_years_range": list(v["payback_years_range"]),
            }
            for k, v in RETROFIT_MEASURES.items()
        }
    }


@router.get("/ref/crrem-pathways", summary="Reference: CRREM 2.0 pathways")
async def get_crrem_pathways() -> dict[str, Any]:
    """Return CRREM 2.0 1.5°C and 2°C intensity reduction milestones by year."""
    return {"crrem_pathways": CRREM_PATHWAYS}


@router.get("/ref/sbti-sectors", summary="Reference: SBTi sector decarb rates")
async def get_sbti_sectors() -> dict[str, Any]:
    """Return SBTi Buildings / Industry / Transport sector annual decarbonisation rates."""
    return {
        "sbti_sector_rates": {
            "buildings": {"rate_pa_pct": 7.0, "standard": "SBTi Buildings Sector Guidance 2022"},
            "industry":  {"rate_pa_pct": 4.2, "standard": "SBTi Industry Sector Guidance 2021"},
            "transport": {"rate_pa_pct": 3.8, "standard": "SBTi Transport Sector Guidance 2021"},
        },
        "sbti_nz_standard": {
            "near_term_2030_reduction_pct": 42,
            "long_term_2050_reduction_pct": 90,
            "residual_neutralisation_pct": 10,
        },
    }


@router.get("/ref/abatement-costs", summary="Reference: capex abatement cost ranges")
async def get_abatement_costs() -> dict[str, Any]:
    """Return IPCC AR6 WG III abatement cost ranges per technology."""
    return {
        "abatement_technologies": {
            k: {
                "abatement_cost_usd_per_tco2e_range": list(v["abatement_cost_usd_per_tco2e"]),
                "max_emissions_reduction_pct": v["max_reduction_pct"],
                "deployment_time_years": v["deployment_time_years"],
            }
            for k, v in CAPEX_ABATEMENT_TECHNOLOGIES.items()
        },
        "carbon_price_scenarios": CARBON_PRICE_SCENARIOS,
    }
