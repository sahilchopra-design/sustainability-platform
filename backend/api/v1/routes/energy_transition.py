"""
Energy Transition API
======================
Endpoints for generation transition planning and grid emission factor
trajectory projections.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.generation_transition import (
    GenerationTransitionPlanner,
    PlantInput,
    FUEL_EMISSION_FACTORS,
    NZE_MILESTONES,
    REPLACEMENT_PRIORITY,
)
from services.grid_ef_trajectory import (
    GridEFTrajectoryEngine,
    GRID_EF_BASELINE,
    SCENARIOS,
)

router = APIRouter(prefix="/api/v1/energy-transition", tags=["Energy Transition"])

_transition = GenerationTransitionPlanner()
_grid = GridEFTrajectoryEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PlantModel(BaseModel):
    plant_id: str
    name: str
    fuel_type: str
    capacity_mw: float = Field(ge=0)
    commissioning_year: int = Field(ge=1950, le=2030)
    planned_retirement_year: Optional[int] = None
    capacity_factor_pct: float = Field(60.0, ge=0, le=100)
    annual_generation_mwh: float = Field(0, ge=0)
    book_value_eur: float = Field(0, ge=0)
    remaining_debt_eur: float = Field(0, ge=0)


class FleetTransitionRequest(BaseModel):
    fleet_name: str
    plants: list[PlantModel]
    target_year: int = Field(2040, ge=2025, le=2060)
    replacement_tech: str = ""
    carbon_price_eur_t: float = Field(80.0, ge=0)
    base_year: int = Field(2025, ge=2020, le=2035)


class GridEFProjectionRequest(BaseModel):
    country: str = "DE"
    scenario: str = "nze_2050"
    start_year: int = Field(2023, ge=2020)
    end_year: int = Field(2050, ge=2025, le=2060)


class AvoidedEmissionsRequest(BaseModel):
    country: str = "DE"
    scenario: str = "nze_2050"
    annual_generation_mwh: float = Field(50_000, gt=0)
    start_year: int = Field(2025, ge=2020)
    project_lifetime_years: int = Field(25, ge=1, le=50)


class CountryCompareRequest(BaseModel):
    countries: list[str]
    scenario: str = "nze_2050"


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_schedule(s) -> dict:
    return {
        "plant_id": s.plant_id,
        "name": s.name,
        "fuel_type": s.fuel_type,
        "capacity_mw": s.capacity_mw,
        "retirement_year": s.retirement_year,
        "age_at_retirement": s.age_at_retirement,
        "stranded_book_value_eur": s.stranded_book_value_eur,
        "decommission_cost_eur": s.decommission_cost_eur,
        "annual_co2_avoided_t": s.annual_co2_avoided_t,
        "replacement_technology": s.replacement_technology,
        "replacement_capacity_mw": s.replacement_capacity_mw,
        "replacement_capex_eur": s.replacement_capex_eur,
    }


def _ser_fleet(r) -> dict:
    return {
        "fleet_name": r.fleet_name,
        "total_capacity_mw": r.total_capacity_mw,
        "fossil_capacity_mw": r.fossil_capacity_mw,
        "clean_capacity_mw": r.clean_capacity_mw,
        "current_annual_emissions_t": r.current_annual_emissions_t,
        "retirement_schedule": [_ser_schedule(s) for s in r.retirement_schedule],
        "year_by_year": r.year_by_year,
        "total_stranded_value_eur": r.total_stranded_value_eur,
        "total_decommission_cost_eur": r.total_decommission_cost_eur,
        "total_replacement_capex_eur": r.total_replacement_capex_eur,
        "nze_aligned": r.nze_aligned,
        "nze_gap_description": r.nze_gap_description,
        "emissions_trajectory": r.emissions_trajectory,
    }


def _ser_grid(r) -> dict:
    return {
        "country": r.country,
        "country_label": r.country_label,
        "region": r.region,
        "scenario": r.scenario,
        "scenario_label": r.scenario_label,
        "baseline_ef_2023": r.baseline_ef_2023,
        "trajectory": r.trajectory,
        "ef_2030": r.ef_2030,
        "ef_2040": r.ef_2040,
        "ef_2050": r.ef_2050,
        "total_reduction_pct": r.total_reduction_pct,
    }


def _ser_avoided(r) -> dict:
    return {
        "country": r.country,
        "scenario": r.scenario,
        "annual_generation_mwh": r.annual_generation_mwh,
        "project_lifetime_years": r.project_lifetime_years,
        "year_by_year": r.year_by_year,
        "total_avoided_tco2": r.total_avoided_tco2,
        "average_grid_ef": r.average_grid_ef,
    }


def _ser_compare(r) -> dict:
    return {
        "scenario": r.scenario,
        "scenario_label": r.scenario_label,
        "countries": r.countries,
        "cleanest_2030": r.cleanest_2030,
        "dirtiest_2030": r.dirtiest_2030,
        "fastest_decarboniser": r.fastest_decarboniser,
    }


# ---------------------------------------------------------------------------
# Endpoints — Generation Transition
# ---------------------------------------------------------------------------

@router.post("/fleet-transition", summary="Fleet coal-to-clean transition plan")
def fleet_transition(req: FleetTransitionRequest):
    plants = [
        PlantInput(
            plant_id=p.plant_id,
            name=p.name,
            fuel_type=p.fuel_type,
            capacity_mw=p.capacity_mw,
            commissioning_year=p.commissioning_year,
            planned_retirement_year=p.planned_retirement_year,
            capacity_factor_pct=p.capacity_factor_pct,
            annual_generation_mwh=p.annual_generation_mwh,
            book_value_eur=p.book_value_eur,
            remaining_debt_eur=p.remaining_debt_eur,
        )
        for p in req.plants
    ]
    res = _transition.plan_transition(
        fleet_name=req.fleet_name,
        plants=plants,
        target_year=req.target_year,
        replacement_tech=req.replacement_tech,
        carbon_price_eur_t=req.carbon_price_eur_t,
        base_year=req.base_year,
    )
    return _ser_fleet(res)


# ---------------------------------------------------------------------------
# Endpoints — Grid EF Trajectory
# ---------------------------------------------------------------------------

@router.post("/grid-ef-projection", summary="Grid emission factor trajectory")
def grid_ef_projection(req: GridEFProjectionRequest):
    res = _grid.project_grid_ef(
        country=req.country,
        scenario=req.scenario,
        start_year=req.start_year,
        end_year=req.end_year,
    )
    return _ser_grid(res)


@router.post("/avoided-emissions", summary="Avoided emissions from renewable project")
def avoided_emissions(req: AvoidedEmissionsRequest):
    res = _grid.avoided_emissions(
        country=req.country,
        scenario=req.scenario,
        annual_generation_mwh=req.annual_generation_mwh,
        start_year=req.start_year,
        project_lifetime_years=req.project_lifetime_years,
    )
    return _ser_avoided(res)


@router.post("/country-comparison", summary="Compare grid EFs across countries")
def country_comparison(req: CountryCompareRequest):
    res = _grid.compare_countries(
        countries=req.countries,
        scenario=req.scenario,
    )
    return _ser_compare(res)


# ---------------------------------------------------------------------------
# Endpoints — Reference Data
# ---------------------------------------------------------------------------

@router.get("/ref/fuel-types", summary="Fuel type emission factors and costs")
def ref_fuel_types():
    return _transition.get_fuel_types()


@router.get("/ref/nze-milestones", summary="IEA NZE power sector milestones")
def ref_nze_milestones():
    return _transition.get_nze_milestones()


@router.get("/ref/replacement-options", summary="Replacement technology priority list")
def ref_replacement_options():
    return _transition.get_replacement_options()


@router.get("/ref/grid-ef-countries", summary="Grid EF baseline data by country")
def ref_grid_countries():
    return _grid.get_countries()


@router.get("/ref/grid-ef-scenarios", summary="Grid EF projection scenarios")
def ref_grid_scenarios():
    return _grid.get_scenarios()
