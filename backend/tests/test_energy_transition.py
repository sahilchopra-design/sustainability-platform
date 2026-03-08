"""
Tests for Generation Transition Planner + Grid EF Trajectory
==============================================================
"""
import sys, os, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.generation_transition import (
    GenerationTransitionPlanner,
    PlantInput,
    FleetTransitionResult,
    RetirementSchedule,
    FUEL_EMISSION_FACTORS,
    NZE_MILESTONES,
    REPLACEMENT_PRIORITY,
    DECOMMISSION_COST_EUR_MW,
)
from services.grid_ef_trajectory import (
    GridEFTrajectoryEngine,
    GridEFProjection,
    AvoidedEmissionsResult,
    MultiCountryComparison,
    GRID_EF_BASELINE,
    SCENARIOS,
)


# ── Helpers ────────────────────────────────────────────────────────────

def _plant(**kw):
    defaults = dict(
        plant_id="P1",
        name="Coal Plant 1",
        fuel_type="coal_subcritical",
        capacity_mw=500,
        commissioning_year=1995,
        capacity_factor_pct=60,
    )
    defaults.update(kw)
    return PlantInput(**defaults)


def _fleet(plants=None, **kw):
    if plants is None:
        plants = [
            _plant(plant_id="P1", name="Old Coal 1", fuel_type="coal_subcritical",
                   capacity_mw=500, commissioning_year=1990),
            _plant(plant_id="P2", name="Gas CCGT 1", fuel_type="gas_ccgt",
                   capacity_mw=400, commissioning_year=2010),
            _plant(plant_id="P3", name="Solar Farm", fuel_type="solar_pv",
                   capacity_mw=200, commissioning_year=2020),
        ]
    defaults = dict(fleet_name="Test Fleet", plants=plants, target_year=2040)
    defaults.update(kw)
    return GenerationTransitionPlanner().plan_transition(**defaults)


# ========================================================================
# Generation Transition Planner
# ========================================================================

class TestFleetTransition:
    def test_returns_result(self):
        r = _fleet()
        assert isinstance(r, FleetTransitionResult)

    def test_capacity_breakdown(self):
        r = _fleet()
        assert r.total_capacity_mw == 1100.0
        assert r.fossil_capacity_mw == 900.0
        assert r.clean_capacity_mw == 200.0

    def test_emissions_positive(self):
        r = _fleet()
        assert r.current_annual_emissions_t > 0

    def test_retirement_schedule_covers_fossil(self):
        r = _fleet()
        retired_ids = {s.plant_id for s in r.retirement_schedule}
        assert "P1" in retired_ids  # coal
        assert "P2" in retired_ids  # gas
        assert "P3" not in retired_ids  # solar — clean, not retired

    def test_dirtiest_retired_first(self):
        r = _fleet()
        # Coal (ef=1.10) should retire before gas (ef=0.35)
        coal_ret = next(s for s in r.retirement_schedule if s.plant_id == "P1")
        gas_ret = next(s for s in r.retirement_schedule if s.plant_id == "P2")
        assert coal_ret.retirement_year <= gas_ret.retirement_year

    def test_co2_avoided_per_plant(self):
        r = _fleet()
        coal = next(s for s in r.retirement_schedule if s.plant_id == "P1")
        assert coal.annual_co2_avoided_t > 0

    def test_replacement_assigned(self):
        r = _fleet()
        for s in r.retirement_schedule:
            assert s.replacement_technology in FUEL_EMISSION_FACTORS

    def test_replacement_capex_positive(self):
        r = _fleet()
        assert r.total_replacement_capex_eur > 0

    def test_year_by_year_trajectory(self):
        r = _fleet()
        assert len(r.year_by_year) > 0
        first = r.year_by_year[0]
        assert "year" in first
        assert "remaining_fossil_mw" in first

    def test_emissions_trajectory(self):
        r = _fleet()
        assert len(r.emissions_trajectory) > 0
        last = r.emissions_trajectory[-1]
        # By target year, emissions should be reduced
        assert last["emissions_tco2"] < r.current_annual_emissions_t

    def test_nze_aligned_when_complete(self):
        r = _fleet(target_year=2040)
        # All fossil retires by 2040 → aligned
        assert r.nze_aligned

    def test_stranded_value_with_book(self):
        plants = [
            _plant(plant_id="P1", fuel_type="coal_subcritical",
                   capacity_mw=500, commissioning_year=2015, book_value_eur=100_000_000),
        ]
        r = _fleet(plants=plants, target_year=2035)
        assert r.total_stranded_value_eur > 0

    def test_planned_retirement_honoured(self):
        plants = [
            _plant(plant_id="P1", fuel_type="coal_subcritical",
                   capacity_mw=500, commissioning_year=1990, planned_retirement_year=2028),
        ]
        r = _fleet(plants=plants, target_year=2040)
        sched = r.retirement_schedule[0]
        assert sched.retirement_year == 2028


class TestFleetSinglePlant:
    def test_single_coal(self):
        plants = [_plant()]
        r = _fleet(plants=plants)
        assert len(r.retirement_schedule) == 1

    def test_single_clean_no_retirement(self):
        plants = [_plant(fuel_type="solar_pv")]
        r = _fleet(plants=plants)
        assert len(r.retirement_schedule) == 0


class TestAutoReplacement:
    def test_coal_replaced_by_solar(self):
        planner = GenerationTransitionPlanner()
        assert planner._auto_replace("coal_subcritical") == "solar_pv"

    def test_gas_replaced_by_wind(self):
        planner = GenerationTransitionPlanner()
        assert planner._auto_replace("gas_ccgt") == "wind_onshore"


# ========================================================================
# Grid EF Trajectory
# ========================================================================

class TestGridEFProjection:
    def test_default_projection(self):
        r = GridEFTrajectoryEngine().project_grid_ef()
        assert isinstance(r, GridEFProjection)
        assert r.country == "DE"

    def test_trajectory_length(self):
        r = GridEFTrajectoryEngine().project_grid_ef(start_year=2023, end_year=2050)
        assert len(r.trajectory) == 28  # 2023 to 2050 inclusive

    def test_ef_decreases_nze(self):
        r = GridEFTrajectoryEngine().project_grid_ef(scenario="nze_2050")
        assert r.ef_2050 < r.baseline_ef_2023

    def test_nze_reaches_zero(self):
        r = GridEFTrajectoryEngine().project_grid_ef(country="DE", scenario="nze_2050")
        assert r.ef_2050 == 0.0

    def test_hot_house_slow_reduction(self):
        nze = GridEFTrajectoryEngine().project_grid_ef(scenario="nze_2050")
        hot = GridEFTrajectoryEngine().project_grid_ef(scenario="ngfs_hot_house")
        assert hot.ef_2050 > nze.ef_2050

    def test_high_carbon_country(self):
        r = GridEFTrajectoryEngine().project_grid_ef(country="IN", scenario="nze_2050")
        assert r.baseline_ef_2023 > 0.5

    def test_low_carbon_country(self):
        r = GridEFTrajectoryEngine().project_grid_ef(country="FR")
        assert r.baseline_ef_2023 < 0.10

    def test_unknown_country_fallback(self):
        r = GridEFTrajectoryEngine().project_grid_ef(country="XX")
        assert r.baseline_ef_2023 == 0.40

    def test_reduction_pct(self):
        r = GridEFTrajectoryEngine().project_grid_ef(country="DE", scenario="nze_2050")
        assert r.total_reduction_pct == 100.0  # Full decarbonisation

    def test_all_scenarios(self):
        eng = GridEFTrajectoryEngine()
        for scen in SCENARIOS:
            r = eng.project_grid_ef(scenario=scen)
            assert r.ef_2030 <= r.baseline_ef_2023

    def test_all_countries(self):
        eng = GridEFTrajectoryEngine()
        for c in GRID_EF_BASELINE:
            r = eng.project_grid_ef(country=c)
            assert r.trajectory[0]["ef_tco2_mwh"] == r.baseline_ef_2023


# ========================================================================
# Avoided Emissions
# ========================================================================

class TestAvoidedEmissions:
    def test_basic(self):
        r = GridEFTrajectoryEngine().avoided_emissions()
        assert isinstance(r, AvoidedEmissionsResult)
        assert r.total_avoided_tco2 > 0

    def test_higher_gen_more_avoided(self):
        low = GridEFTrajectoryEngine().avoided_emissions(annual_generation_mwh=10_000)
        high = GridEFTrajectoryEngine().avoided_emissions(annual_generation_mwh=100_000)
        assert high.total_avoided_tco2 > low.total_avoided_tco2

    def test_dirty_grid_more_avoided(self):
        clean = GridEFTrajectoryEngine().avoided_emissions(country="FR")  # 0.06
        dirty = GridEFTrajectoryEngine().avoided_emissions(country="IN")  # 0.72
        assert dirty.total_avoided_tco2 > clean.total_avoided_tco2

    def test_year_by_year_length(self):
        r = GridEFTrajectoryEngine().avoided_emissions(project_lifetime_years=20)
        assert len(r.year_by_year) == 20

    def test_average_ef_plausible(self):
        r = GridEFTrajectoryEngine().avoided_emissions(country="DE", scenario="nze_2050")
        assert 0 <= r.average_grid_ef <= r.year_by_year[0]["grid_ef"]


# ========================================================================
# Country Comparison
# ========================================================================

class TestCountryComparison:
    def test_basic_compare(self):
        r = GridEFTrajectoryEngine().compare_countries(["DE", "FR", "PL"])
        assert isinstance(r, MultiCountryComparison)
        assert len(r.countries) == 3

    def test_cleanest_dirtiest(self):
        r = GridEFTrajectoryEngine().compare_countries(["FR", "PL", "IN"])
        assert r.cleanest_2030 == "FR"
        assert r.dirtiest_2030 in ("PL", "IN")

    def test_single_country(self):
        r = GridEFTrajectoryEngine().compare_countries(["DE"])
        assert r.cleanest_2030 == "DE"
        assert r.dirtiest_2030 == "DE"


# ========================================================================
# Reference Data
# ========================================================================

class TestTransitionReferenceData:
    def test_fuel_types_populated(self):
        assert len(FUEL_EMISSION_FACTORS) == 14
        for f in FUEL_EMISSION_FACTORS.values():
            assert "ef" in f
            assert "capex_eur_kw" in f

    def test_nze_milestones(self):
        assert len(NZE_MILESTONES) == 5
        assert NZE_MILESTONES[2050]["coal_share_pct"] == 0

    def test_replacement_priority(self):
        assert len(REPLACEMENT_PRIORITY) == 8
        assert REPLACEMENT_PRIORITY[0] == "solar_pv"

    def test_grid_ef_baseline(self):
        assert len(GRID_EF_BASELINE) == 25
        for c in GRID_EF_BASELINE.values():
            assert c["ef_2023"] >= 0

    def test_scenarios(self):
        assert len(SCENARIOS) == 6
        assert "nze_2050" in SCENARIOS

    def test_decommission_costs(self):
        assert len(DECOMMISSION_COST_EUR_MW) > 0
        assert DECOMMISSION_COST_EUR_MW["nuclear"] > DECOMMISSION_COST_EUR_MW["gas_ocgt"]
