"""
Tests for Methane OGMP 2.0 + Scope 3 Cat 11 + CSRD Auto-Population
=====================================================================
"""
import sys, os, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.methane_ogmp import (
    MethaneOGMPEngine,
    MethaneSource,
    FacilityMethaneResult,
    MethaneSourceResult,
    SOURCE_CATEGORIES,
    OGMP_LEVELS,
    ABATEMENT_MEASURES,
    GWP_100,
    GWP_20,
)
from services.scope3_cat11 import (
    Scope3Cat11Engine,
    FuelSoldInput,
    ProductSoldInput,
    Scope3Cat11Result,
    FuelEmissionsResult,
    ProductEmissionsResult,
    FUEL_COMBUSTION_EF,
    PRODUCT_USE_PROFILES,
)
from services.csrd_auto_populate import (
    CSRDAutoPopulateEngine,
    ModuleOutput,
    AutoPopulateResult,
    PopulatedDataPoint,
    ESRS_MAPPINGS,
    ESRS_MINIMUMS,
)


# ── Factories ──────────────────────────────────────────────────────────

def _source(**kw):
    defaults = dict(
        source_id="S1",
        category="venting",
        facility_name="Platform Alpha",
        ogmp_level=2,
        activity_bcm_yr=1.0,
    )
    defaults.update(kw)
    return MethaneSource(**defaults)


def _facility(sources=None, **kw):
    if sources is None:
        sources = [
            _source(source_id="S1", category="venting", activity_bcm_yr=1.0),
            _source(source_id="S2", category="fugitive_wellhead", activity_bcm_yr=0.5),
            _source(source_id="S3", category="flaring", activity_bcm_yr=2.0),
        ]
    defaults = dict(facility_name="Platform Alpha", sources=sources)
    defaults.update(kw)
    return MethaneOGMPEngine().assess_facility(**defaults)


# ========================================================================
# Methane OGMP 2.0
# ========================================================================

class TestMethaneBasic:
    def test_returns_result(self):
        r = _facility()
        assert isinstance(r, FacilityMethaneResult)

    def test_total_tch4_positive(self):
        r = _facility()
        assert r.total_tch4 > 0

    def test_gwp_conversion(self):
        r = _facility()
        assert r.total_tco2e_gwp100 == pytest.approx(r.total_tch4 * GWP_100, rel=0.01)
        assert r.total_tco2e_gwp20 == pytest.approx(r.total_tch4 * GWP_20, rel=0.01)

    def test_gwp20_gt_gwp100(self):
        r = _facility()
        assert r.total_tco2e_gwp20 > r.total_tco2e_gwp100

    def test_source_count(self):
        r = _facility()
        assert len(r.source_results) == 3

    def test_intensity_positive(self):
        r = _facility()
        assert r.methane_intensity_tch4_bcm > 0


class TestMethaneOGMPLevels:
    def test_level2_uses_default_ef(self):
        src = [_source(ogmp_level=2, activity_bcm_yr=1.0)]
        r = _facility(sources=src)
        expected = SOURCE_CATEGORIES["venting"]["typical_ef_tch4_bcm"]
        assert r.source_results[0].emissions_tch4 == pytest.approx(expected, rel=0.01)

    def test_level4_uses_measurement(self):
        src = [_source(ogmp_level=4, measured_tch4_yr=0.5, activity_bcm_yr=1.0)]
        r = _facility(sources=src)
        assert r.source_results[0].emissions_tch4 == 0.5
        assert r.source_results[0].method_used == "Direct measurement"

    def test_custom_ef_level3(self):
        src = [_source(ogmp_level=3, activity_bcm_yr=2.0, custom_ef_tch4_bcm=0.25)]
        r = _facility(sources=src)
        assert r.source_results[0].emissions_tch4 == pytest.approx(0.5, rel=0.01)

    def test_eu_compliance_level2(self):
        src = [_source(ogmp_level=2)]
        r = _facility(sources=src)
        assert not r.eu_methane_reg_compliant

    def test_eu_compliance_level3(self):
        src = [_source(ogmp_level=3, activity_bcm_yr=1.0)]
        r = _facility(sources=src)
        assert r.eu_methane_reg_compliant


class TestMethaneAbatement:
    def test_abatement_potential(self):
        r = _facility()
        assert r.abatement_potential_tch4 > 0
        assert r.abatement_potential_pct > 0

    def test_pathway_sorted_by_cost(self):
        r = _facility()
        costs = [p["cost_eur_per_tco2e"] for p in r.reduction_pathway]
        assert costs == sorted(costs)

    def test_measures_recommended(self):
        r = _facility()
        for s in r.source_results:
            if s.emissions_tch4 > 0:
                assert len(s.recommended_measures) > 0


# ========================================================================
# Scope 3 Category 11
# ========================================================================

class TestScope3Cat11Fuels:
    def test_basic_fuel(self):
        fuels = [FuelSoldInput(fuel_type="crude_oil_bbl", volume_sold=1_000_000)]
        r = Scope3Cat11Engine().assess(fuels=fuels)
        assert isinstance(r, Scope3Cat11Result)
        assert r.total_fuel_tco2 > 0

    def test_coal_high_emissions(self):
        coal = [FuelSoldInput(fuel_type="thermal_coal_tonne", volume_sold=100_000)]
        r = Scope3Cat11Engine().assess(fuels=coal)
        assert r.total_fuel_tco2 == pytest.approx(100_000 * 2.42, rel=0.01)

    def test_multiple_fuels(self):
        fuels = [
            FuelSoldInput(fuel_type="crude_oil_bbl", volume_sold=500_000),
            FuelSoldInput(fuel_type="natural_gas_mcf", volume_sold=10_000_000),
        ]
        r = Scope3Cat11Engine().assess(fuels=fuels)
        assert len(r.fuel_results) == 2
        assert r.total_fuel_tco2 > 0

    def test_unknown_fuel_skipped(self):
        fuels = [FuelSoldInput(fuel_type="unknown_fuel", volume_sold=1000)]
        r = Scope3Cat11Engine().assess(fuels=fuels)
        assert len(r.fuel_results) == 0


class TestScope3Cat11Products:
    def test_ice_car(self):
        products = [ProductSoldInput(product_type="passenger_car_ice", units_sold=10_000)]
        r = Scope3Cat11Engine().assess(products=products)
        assert r.total_product_lifetime_tco2 > 0

    def test_ev_lower_than_ice(self):
        ice = Scope3Cat11Engine().assess(products=[
            ProductSoldInput(product_type="passenger_car_ice", units_sold=1000, grid_ef_tco2_mwh=0.40)])
        ev = Scope3Cat11Engine().assess(products=[
            ProductSoldInput(product_type="passenger_car_ev", units_sold=1000, grid_ef_tco2_mwh=0.40)])
        assert ev.total_product_lifetime_tco2 < ice.total_product_lifetime_tco2

    def test_grid_ef_affects_ev(self):
        clean = Scope3Cat11Engine().assess(products=[
            ProductSoldInput(product_type="passenger_car_ev", units_sold=1000, grid_ef_tco2_mwh=0.05)])
        dirty = Scope3Cat11Engine().assess(products=[
            ProductSoldInput(product_type="passenger_car_ev", units_sold=1000, grid_ef_tco2_mwh=0.80)])
        assert dirty.total_product_lifetime_tco2 > clean.total_product_lifetime_tco2

    def test_unknown_product_skipped(self):
        products = [ProductSoldInput(product_type="unknown_product", units_sold=100)]
        r = Scope3Cat11Engine().assess(products=products)
        assert len(r.product_results) == 0


class TestScope3Cat11Combined:
    def test_combined(self):
        r = Scope3Cat11Engine().assess(
            fuels=[FuelSoldInput(fuel_type="crude_oil_bbl", volume_sold=100_000)],
            products=[ProductSoldInput(product_type="passenger_car_ice", units_sold=5000)],
        )
        assert r.total_cat11_tco2 == pytest.approx(r.total_fuel_tco2 + r.total_product_lifetime_tco2, rel=0.01)

    def test_top_contributor(self):
        r = Scope3Cat11Engine().assess(
            fuels=[FuelSoldInput(fuel_type="thermal_coal_tonne", volume_sold=1_000_000)],
            products=[ProductSoldInput(product_type="household_appliance", units_sold=100)],
        )
        assert r.top_contributor == "Thermal Coal"

    def test_intensity_with_revenue(self):
        r = Scope3Cat11Engine().assess(
            fuels=[FuelSoldInput(fuel_type="crude_oil_bbl", volume_sold=100_000)],
            revenue_m_eur=500,
        )
        assert r.intensity_tco2_per_m_revenue > 0

    def test_empty_input(self):
        r = Scope3Cat11Engine().assess()
        assert r.total_cat11_tco2 == 0


# ========================================================================
# CSRD Auto-Population
# ========================================================================

class TestCSRDAutoPopulate:
    def test_basic_populate(self):
        outputs = [
            ModuleOutput(module="carbon_calculator", field="scope1_total_tco2e", value=50000),
            ModuleOutput(module="carbon_calculator", field="scope2_location_tco2e", value=20000),
        ]
        r = CSRDAutoPopulateEngine().populate("TestCo", outputs)
        assert isinstance(r, AutoPopulateResult)
        assert r.populated_count == 2

    def test_population_rate(self):
        # 2 out of total mappings
        outputs = [
            ModuleOutput(module="carbon_calculator", field="scope1_total_tco2e", value=50000),
        ]
        r = CSRDAutoPopulateEngine().populate("TestCo", outputs)
        assert r.population_rate_pct == pytest.approx(1 / len(ESRS_MAPPINGS) * 100, rel=0.1)

    def test_gaps_identified(self):
        r = CSRDAutoPopulateEngine().populate("TestCo", [])
        assert len(r.gaps) == len(ESRS_MAPPINGS)

    def test_full_populate(self):
        outputs = []
        for dp_id, mapping in ESRS_MAPPINGS.items():
            outputs.append(ModuleOutput(
                module=mapping["source_module"],
                field=mapping["source_field"],
                value=100.0,
            ))
        r = CSRDAutoPopulateEngine().populate("TestCo", outputs)
        assert r.populated_count == len(ESRS_MAPPINGS)
        assert r.population_rate_pct == 100.0
        assert r.readiness_rating == "high"

    def test_esrs_coverage_breakdown(self):
        outputs = [
            ModuleOutput(module="carbon_calculator", field="scope1_total_tco2e", value=50000),
        ]
        r = CSRDAutoPopulateEngine().populate("TestCo", outputs)
        assert "E1" in r.esrs_coverage
        assert r.esrs_coverage["E1"]["populated"] >= 1

    def test_readiness_low(self):
        r = CSRDAutoPopulateEngine().populate("TestCo", [])
        assert r.readiness_rating == "low"

    def test_confidence_high_for_direct(self):
        outputs = [
            ModuleOutput(module="carbon_calculator", field="scope1_total_tco2e", value=50000),
        ]
        r = CSRDAutoPopulateEngine().populate("TestCo", outputs)
        assert r.populated_dps[0].confidence == "high"


# ========================================================================
# Reference Data
# ========================================================================

class TestEnergyEmissionsRefData:
    def test_source_categories(self):
        assert len(SOURCE_CATEGORIES) == 10

    def test_ogmp_levels(self):
        assert len(OGMP_LEVELS) == 5

    def test_abatement_measures(self):
        assert len(ABATEMENT_MEASURES) == 6

    def test_fuel_combustion_efs(self):
        assert len(FUEL_COMBUSTION_EF) == 10
        assert FUEL_COMBUSTION_EF["thermal_coal_tonne"]["ef_tco2"] > 0

    def test_product_profiles(self):
        assert len(PRODUCT_USE_PROFILES) == 8

    def test_esrs_mappings(self):
        assert len(ESRS_MAPPINGS) >= 14
        for m in ESRS_MAPPINGS.values():
            assert "esrs" in m
            assert "source_module" in m

    def test_esrs_minimums(self):
        assert len(ESRS_MINIMUMS) >= 7
