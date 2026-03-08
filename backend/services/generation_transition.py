"""
Generation Transition Planner
==============================
Coal-to-clean transition pathway modelling for power generation assets.
Produces year-by-year fleet retirement schedules, replacement capacity
requirements, stranded cost estimates, and emissions trajectories aligned
to IEA NZE / NGFS / SBTi Power Sector targets.

References:
- IEA Net Zero by 2050 — power sector milestones
- NGFS Phase IV Scenarios (2024)
- SBTi Power Sector 1.5C pathway
- GEM Global Coal Plant Tracker methodology
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# Fuel-specific emission factors (tCO2/MWh)
FUEL_EMISSION_FACTORS: dict[str, dict] = {
    "coal_subcritical": {"ef": 1.10, "label": "Coal Subcritical", "capex_eur_kw": 1800, "opex_eur_kw_yr": 40},
    "coal_supercritical": {"ef": 0.90, "label": "Coal Supercritical", "capex_eur_kw": 2200, "opex_eur_kw_yr": 45},
    "coal_usc": {"ef": 0.78, "label": "Coal Ultra-Supercritical", "capex_eur_kw": 2500, "opex_eur_kw_yr": 48},
    "gas_ocgt": {"ef": 0.55, "label": "Gas OCGT", "capex_eur_kw": 500, "opex_eur_kw_yr": 12},
    "gas_ccgt": {"ef": 0.35, "label": "Gas CCGT", "capex_eur_kw": 900, "opex_eur_kw_yr": 20},
    "gas_ccgt_ccs": {"ef": 0.05, "label": "Gas CCGT + CCS", "capex_eur_kw": 1800, "opex_eur_kw_yr": 45},
    "oil": {"ef": 0.70, "label": "Oil / Diesel", "capex_eur_kw": 700, "opex_eur_kw_yr": 18},
    "biomass": {"ef": 0.10, "label": "Biomass", "capex_eur_kw": 2000, "opex_eur_kw_yr": 50},
    "nuclear": {"ef": 0.005, "label": "Nuclear", "capex_eur_kw": 6000, "opex_eur_kw_yr": 100},
    "wind_onshore": {"ef": 0.0, "label": "Wind Onshore", "capex_eur_kw": 1150, "opex_eur_kw_yr": 30},
    "wind_offshore": {"ef": 0.0, "label": "Wind Offshore", "capex_eur_kw": 2800, "opex_eur_kw_yr": 80},
    "solar_pv": {"ef": 0.0, "label": "Solar PV", "capex_eur_kw": 750, "opex_eur_kw_yr": 12},
    "hydro": {"ef": 0.0, "label": "Hydro", "capex_eur_kw": 2500, "opex_eur_kw_yr": 35},
    "battery": {"ef": 0.0, "label": "Battery Storage", "capex_eur_kw": 600, "opex_eur_kw_yr": 10},
}

# IEA NZE milestones for power sector
NZE_MILESTONES: dict[int, dict] = {
    2025: {"coal_share_pct": 25, "renewables_share_pct": 45, "grid_ef_tco2_mwh": 0.40},
    2030: {"coal_share_pct": 10, "renewables_share_pct": 60, "grid_ef_tco2_mwh": 0.25},
    2035: {"coal_share_pct": 2, "renewables_share_pct": 75, "grid_ef_tco2_mwh": 0.10},
    2040: {"coal_share_pct": 0, "renewables_share_pct": 85, "grid_ef_tco2_mwh": 0.04},
    2050: {"coal_share_pct": 0, "renewables_share_pct": 90, "grid_ef_tco2_mwh": 0.00},
}

# Replacement technology priorities (ordered by preference)
REPLACEMENT_PRIORITY = [
    "solar_pv", "wind_onshore", "wind_offshore", "battery",
    "gas_ccgt", "gas_ccgt_ccs", "hydro", "nuclear",
]

# Decommissioning cost per MW (EUR)
DECOMMISSION_COST_EUR_MW: dict[str, float] = {
    "coal_subcritical": 80_000,
    "coal_supercritical": 90_000,
    "coal_usc": 100_000,
    "gas_ocgt": 30_000,
    "gas_ccgt": 50_000,
    "gas_ccgt_ccs": 60_000,
    "oil": 40_000,
    "biomass": 35_000,
    "nuclear": 500_000,
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class PlantInput:
    """A generation asset in the fleet."""
    plant_id: str
    name: str
    fuel_type: str  # key into FUEL_EMISSION_FACTORS
    capacity_mw: float
    commissioning_year: int
    planned_retirement_year: Optional[int] = None
    capacity_factor_pct: float = 60.0
    annual_generation_mwh: float = 0  # computed if 0
    book_value_eur: float = 0
    remaining_debt_eur: float = 0


@dataclass
class RetirementSchedule:
    """Year-by-year retirement plan for a single plant."""
    plant_id: str
    name: str
    fuel_type: str
    capacity_mw: float
    retirement_year: int
    age_at_retirement: int
    stranded_book_value_eur: float
    decommission_cost_eur: float
    annual_co2_avoided_t: float
    replacement_technology: str
    replacement_capacity_mw: float
    replacement_capex_eur: float


@dataclass
class FleetTransitionResult:
    """Complete fleet transition assessment."""
    fleet_name: str
    total_capacity_mw: float
    fossil_capacity_mw: float
    clean_capacity_mw: float
    current_annual_emissions_t: float
    retirement_schedule: list[RetirementSchedule]
    year_by_year: list[dict]  # [{year, remaining_fossil_mw, cumulative_co2_saved, ...}]
    total_stranded_value_eur: float
    total_decommission_cost_eur: float
    total_replacement_capex_eur: float
    nze_aligned: bool
    nze_gap_description: str
    emissions_trajectory: list[dict]  # [{year, emissions_tco2, target_tco2}]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GenerationTransitionPlanner:
    """Coal-to-clean transition planning engine."""

    def plan_transition(
        self,
        fleet_name: str,
        plants: list[PlantInput],
        target_year: int = 2040,
        replacement_tech: str = "",  # empty = auto-select
        carbon_price_eur_t: float = 80.0,
        base_year: int = 2025,
    ) -> FleetTransitionResult:
        """Generate a fleet transition plan."""

        # Fill in annual generation if not provided
        for p in plants:
            if p.annual_generation_mwh <= 0:
                p.annual_generation_mwh = p.capacity_mw * 8760 * p.capacity_factor_pct / 100

        # Classify plants
        fossil_fuels = {"coal_subcritical", "coal_supercritical", "coal_usc", "gas_ocgt", "gas_ccgt", "oil"}
        fossil_plants = [p for p in plants if p.fuel_type in fossil_fuels]
        clean_plants = [p for p in plants if p.fuel_type not in fossil_fuels]

        total_cap = sum(p.capacity_mw for p in plants)
        fossil_cap = sum(p.capacity_mw for p in fossil_plants)
        clean_cap = sum(p.capacity_mw for p in clean_plants)

        current_emissions = sum(
            p.annual_generation_mwh * FUEL_EMISSION_FACTORS.get(p.fuel_type, {}).get("ef", 0)
            for p in plants
        )

        # Build retirement schedule — oldest and dirtiest first
        fossil_plants_sorted = sorted(
            fossil_plants,
            key=lambda p: (
                -FUEL_EMISSION_FACTORS.get(p.fuel_type, {}).get("ef", 0),
                p.commissioning_year,
            ),
        )

        num_fossil = len(fossil_plants_sorted)
        years_available = target_year - base_year
        if years_available < 1:
            years_available = 1

        schedule = []
        for i, plant in enumerate(fossil_plants_sorted):
            # Spread retirements evenly
            retire_year = base_year + int((i + 1) * years_available / num_fossil) if num_fossil > 0 else base_year
            retire_year = min(retire_year, target_year)

            # If plant has a planned retirement, use earlier date
            if plant.planned_retirement_year and plant.planned_retirement_year < retire_year:
                retire_year = plant.planned_retirement_year

            age = retire_year - plant.commissioning_year
            ef = FUEL_EMISSION_FACTORS.get(plant.fuel_type, {}).get("ef", 0)
            co2_avoided = plant.annual_generation_mwh * ef

            # Stranded cost: linear depreciation
            expected_life = 40 if "coal" in plant.fuel_type else 30
            remaining_life = max(0, plant.commissioning_year + expected_life - retire_year)
            stranded_frac = remaining_life / expected_life if expected_life > 0 else 0
            stranded_value = plant.book_value_eur * stranded_frac

            decomm = DECOMMISSION_COST_EUR_MW.get(plant.fuel_type, 50_000) * plant.capacity_mw / 1000

            # Replacement
            rep_tech = replacement_tech if replacement_tech else self._auto_replace(plant.fuel_type)
            rep_info = FUEL_EMISSION_FACTORS.get(rep_tech, FUEL_EMISSION_FACTORS["solar_pv"])
            # Nameplate replacement: ~1.5x for intermittent to match baseload
            multiplier = 1.5 if rep_tech in ("solar_pv", "wind_onshore", "wind_offshore") else 1.0
            rep_cap = plant.capacity_mw * multiplier
            rep_capex = rep_cap * 1000 * rep_info["capex_eur_kw"]

            schedule.append(RetirementSchedule(
                plant_id=plant.plant_id,
                name=plant.name,
                fuel_type=plant.fuel_type,
                capacity_mw=plant.capacity_mw,
                retirement_year=retire_year,
                age_at_retirement=age,
                stranded_book_value_eur=round(stranded_value, 2),
                decommission_cost_eur=round(decomm, 2),
                annual_co2_avoided_t=round(co2_avoided, 1),
                replacement_technology=rep_tech,
                replacement_capacity_mw=round(rep_cap, 1),
                replacement_capex_eur=round(rep_capex, 2),
            ))

        # Year-by-year trajectory
        year_data = []
        emissions_traj = []
        remaining_fossil = fossil_cap
        cumulative_saved = 0
        cumulative_capex = 0

        for yr in range(base_year, target_year + 1):
            retired_this_year = [s for s in schedule if s.retirement_year == yr]
            retired_mw = sum(s.capacity_mw for s in retired_this_year)
            remaining_fossil -= retired_mw
            remaining_fossil = max(0, remaining_fossil)
            co2_saved = sum(s.annual_co2_avoided_t for s in retired_this_year)
            cumulative_saved += co2_saved
            capex_yr = sum(s.replacement_capex_eur for s in retired_this_year)
            cumulative_capex += capex_yr

            yr_emissions = current_emissions - cumulative_saved

            # NZE target for this year
            nze_target = self._interpolate_nze(yr, current_emissions, base_year)

            year_data.append({
                "year": yr,
                "remaining_fossil_mw": round(remaining_fossil, 1),
                "retired_this_year_mw": round(retired_mw, 1),
                "cumulative_co2_saved_t": round(cumulative_saved, 1),
                "replacement_capex_eur": round(capex_yr, 2),
                "cumulative_capex_eur": round(cumulative_capex, 2),
            })
            emissions_traj.append({
                "year": yr,
                "emissions_tco2": round(max(0, yr_emissions), 1),
                "target_tco2": round(max(0, nze_target), 1),
            })

        total_stranded = sum(s.stranded_book_value_eur for s in schedule)
        total_decomm = sum(s.decommission_cost_eur for s in schedule)
        total_rep_capex = sum(s.replacement_capex_eur for s in schedule)

        # NZE alignment check
        final_fossil = remaining_fossil
        nze_aligned = final_fossil == 0 and target_year <= 2040
        if final_fossil > 0:
            gap_desc = f"{round(final_fossil, 1)} MW fossil capacity still operating at {target_year}"
        elif target_year > 2040:
            gap_desc = f"Transition completes by {target_year}, IEA NZE requires coal phase-out by 2040"
        else:
            gap_desc = "Fleet transition aligned with IEA NZE pathway"

        return FleetTransitionResult(
            fleet_name=fleet_name,
            total_capacity_mw=round(total_cap, 1),
            fossil_capacity_mw=round(fossil_cap, 1),
            clean_capacity_mw=round(clean_cap, 1),
            current_annual_emissions_t=round(current_emissions, 1),
            retirement_schedule=schedule,
            year_by_year=year_data,
            total_stranded_value_eur=round(total_stranded, 2),
            total_decommission_cost_eur=round(total_decomm, 2),
            total_replacement_capex_eur=round(total_rep_capex, 2),
            nze_aligned=nze_aligned,
            nze_gap_description=gap_desc,
            emissions_trajectory=emissions_traj,
        )

    def _auto_replace(self, fuel_type: str) -> str:
        """Select replacement technology based on original fuel type."""
        if "coal" in fuel_type:
            return "solar_pv"  # Default for coal: solar (cheapest LCOE)
        elif fuel_type in ("gas_ocgt", "gas_ccgt"):
            return "wind_onshore"
        elif fuel_type == "oil":
            return "solar_pv"
        return "solar_pv"

    def _interpolate_nze(self, year: int, base_emissions: float, base_year: int) -> float:
        """Interpolate NZE target emissions for a given year."""
        milestones = sorted(NZE_MILESTONES.keys())
        if year <= milestones[0]:
            return base_emissions
        if year >= milestones[-1]:
            return 0

        # Find bracket
        for i in range(len(milestones) - 1):
            y0, y1 = milestones[i], milestones[i + 1]
            if y0 <= year <= y1:
                # Linear interpolation on grid_ef reduction
                ef0 = NZE_MILESTONES[y0]["grid_ef_tco2_mwh"]
                ef1 = NZE_MILESTONES[y1]["grid_ef_tco2_mwh"]
                frac = (year - y0) / (y1 - y0) if y1 > y0 else 0
                ef_yr = ef0 + (ef1 - ef0) * frac
                # Scale base emissions by ratio
                ef_base = NZE_MILESTONES[milestones[0]]["grid_ef_tco2_mwh"]
                if ef_base > 0:
                    return base_emissions * ef_yr / ef_base
                return base_emissions
        return base_emissions

    def get_fuel_types(self) -> dict[str, dict]:
        return FUEL_EMISSION_FACTORS

    def get_nze_milestones(self) -> dict[int, dict]:
        return NZE_MILESTONES

    def get_replacement_options(self) -> list[str]:
        return REPLACEMENT_PRIORITY
