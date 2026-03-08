"""
Tests for LGD Downturn Engine and Vintage Analyzer

Covers:
  - LGDDownturnEngine: downturn add-ons, country/sector severity, climate overlays, floors
  - VintageAnalyzer: cohort construction, vintage matrix, ECB backstop, green trend

Regulatory references:
  - CRR2 Art. 181(1)(b), Art. 164 (floors)
  - EBA GL/2019/03 (downturn LGD estimation)
  - IFRS 9 B5.5.52-55 (vintage groupings)
  - EBA GL/2017/06 (credit risk management)
  - ECB NPL Guidance / EU Regulation 2019/630 (calendar provisioning)

Run: pytest backend/tests/test_lgd_vintage.py -v
"""
from __future__ import annotations

import pytest
import numpy as np

from services.lgd_downturn_engine import (
    LGDDownturnEngine,
    DownturnLGDInput,
    REGULATORY_LGD_FLOORS,
    DOWNTURN_ADDON_BY_COLLATERAL,
    SECTOR_DOWNTURN_MULT,
    COUNTRY_CYCLE_SEVERITY,
    CLIMATE_STRANDED_HAIRCUTS,
    GREEN_PREMIUM,
)
from services.vintage_analyzer import (
    VintageAnalyzer,
    VintageExposure,
    ECB_NPE_COVERAGE,
    BENCHMARK_CUMULATIVE_DR,
)


# ---------------------------------------------------------------------------
# FIXTURES -- LGD DOWNTURN
# ---------------------------------------------------------------------------


def _make_downturn_input(**overrides) -> DownturnLGDInput:
    """Create a downturn LGD input with sensible defaults (corporate unsecured in US)."""
    defaults = dict(
        exposure_id="EXP-001",
        counterparty_name="Test Corp",
        long_run_avg_lgd=0.40,
        collateral_type="unsecured",
        collateral_value=0.0,
        exposure_amount=10_000_000,
        ltv_ratio=0.0,
        sector="Technology",
        country="US",
        asset_class="CORPORATE",
        epc_rating="",
        physical_risk_level="",
        is_fossil_fuel_collateral=False,
    )
    defaults.update(overrides)
    return DownturnLGDInput(**defaults)


def _make_batch_inputs(n: int = 20) -> list:
    """Generate a batch of diverse downturn LGD inputs (mix of asset classes,
    collateral types, countries)."""
    rng = np.random.RandomState(42)
    sectors = ["Oil & Gas", "Technology", "Real Estate", "Healthcare", "Steel"]
    collaterals = ["unsecured", "real_estate_residential", "equipment", "financial"]
    countries = ["US", "UK", "DE", "ES", "BR"]
    inputs = []
    for i in range(n):
        inputs.append(DownturnLGDInput(
            exposure_id=f"EXP-{i:04d}",
            counterparty_name=f"Company {i}",
            long_run_avg_lgd=round(rng.uniform(0.20, 0.60), 4),
            collateral_type=collaterals[i % len(collaterals)],
            collateral_value=rng.uniform(0, 5_000_000),
            exposure_amount=rng.uniform(1_000_000, 20_000_000),
            sector=sectors[i % len(sectors)],
            country=countries[i % len(countries)],
            asset_class="CORPORATE",
            epc_rating=rng.choice(["", "A", "C", "F"]),
            physical_risk_level=rng.choice(["", "low", "medium", "high"]),
            is_fossil_fuel_collateral=(i % 5 == 0),
        ))
    return inputs


# ---------------------------------------------------------------------------
# FIXTURES -- VINTAGE
# ---------------------------------------------------------------------------


def _make_vintage_exposures(n: int = 200) -> list:
    """Generate vintage exposures spanning 2018-2024 with increasing green share."""
    rng = np.random.RandomState(55)
    exposures = []
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]

    for i in range(n):
        year = years[i % len(years)]
        is_defaulted = rng.random() < 0.05
        months_to_default = int(rng.uniform(6, 48)) if is_defaulted else 0
        is_npe = is_defaulted or rng.random() < 0.03
        npe_age = rng.uniform(0.5, 4.0) if is_npe else 0.0
        original = rng.uniform(500_000, 10_000_000)
        current = original * rng.uniform(0.3, 0.95)
        provision = current * rng.uniform(0.1, 0.5) if is_npe else 0

        exposures.append(VintageExposure(
            exposure_id=f"VIN-{i:04d}",
            counterparty_name=f"Borrower {i}",
            origination_date=f"{year}-06-15",
            origination_year=year,
            origination_quarter=rng.choice([1, 2, 3, 4]),
            original_amount=round(original, 2),
            current_balance=round(current, 2),
            is_defaulted=is_defaulted,
            default_date=f"{year + int(months_to_default / 12)}-01-01" if is_defaulted else "",
            months_to_default=months_to_default,
            current_stage=3 if is_defaulted else (2 if rng.random() < 0.1 else 1),
            sector=rng.choice(["Corporate", "SME", "Real Estate"]),
            collateral_type=rng.choice(["unsecured", "property", "equipment"]),
            is_npe=is_npe,
            npe_age_years=round(npe_age, 1),
            provision_amount=round(provision, 2),
            is_green=(rng.random() < 0.15 + (year - 2018) * 0.05),
        ))
    return exposures


# ===========================================================================
# LGD DOWNTURN ENGINE TESTS
# ===========================================================================


class TestDownturnBasic:
    """Basic downturn LGD calculation."""

    def test_downturn_exceeds_long_run(self):
        """Downturn LGD must >= long-run average (EBA GL/2019/03)."""
        engine = LGDDownturnEngine()
        inp = _make_downturn_input(long_run_avg_lgd=0.40)
        result = engine.calculate(inp)
        assert result.downturn_lgd >= inp.long_run_avg_lgd

    def test_downturn_capped_at_1(self):
        """Downturn LGD must not exceed 100%."""
        engine = LGDDownturnEngine(scenario="SEVERE")
        inp = _make_downturn_input(
            long_run_avg_lgd=0.85,
            sector="Oil & Gas",
            is_fossil_fuel_collateral=True,
            physical_risk_level="extreme",
        )
        result = engine.calculate(inp)
        assert result.downturn_lgd <= 1.0

    def test_result_structure(self):
        """Verify result has all expected fields."""
        engine = LGDDownturnEngine()
        inp = _make_downturn_input()
        result = engine.calculate(inp)

        assert result.exposure_id == "EXP-001"
        assert result.downturn_uplift_pct >= 0
        assert len(result.methodology_notes) > 0
        assert result.contribution is not None


class TestDownturnCollateral:
    """Collateral-type-specific downturn add-ons."""

    def test_real_estate_higher_addon_than_financial(self):
        """Property (0.08) add-on mapped for real estate vs financial (0.05)."""
        engine = LGDDownturnEngine()
        re_inp = _make_downturn_input(collateral_type="real_estate_residential")
        fin_inp = _make_downturn_input(collateral_type="financial")

        re_result = engine.calculate(re_inp)
        fin_result = engine.calculate(fin_inp)

        assert re_result.contribution.downturn_addon > fin_result.contribution.downturn_addon

    def test_inventory_high_addon(self):
        """Inventory add-on (0.10) should produce a positive component."""
        engine = LGDDownturnEngine()
        inp = _make_downturn_input(collateral_type="inventory")
        result = engine.calculate(inp)
        assert result.contribution.downturn_addon > 0

    def test_unsecured_higher_than_cash(self):
        """Unsecured (0.12) should have higher add-on than cash (0.02)."""
        engine = LGDDownturnEngine()
        unsec_inp = _make_downturn_input(collateral_type="unsecured")
        cash_inp = _make_downturn_input(collateral_type="cash")

        unsec_result = engine.calculate(unsec_inp)
        cash_result = engine.calculate(cash_inp)

        assert unsec_result.contribution.downturn_addon > cash_result.contribution.downturn_addon


class TestDownturnCountry:
    """Country cycle severity adjustments."""

    def test_greece_higher_than_switzerland(self):
        """Greece (1.50) should have higher severity than Switzerland (0.70)."""
        engine = LGDDownturnEngine()
        gr_inp = _make_downturn_input(country="GR")
        ch_inp = _make_downturn_input(country="CH")

        gr_result = engine.calculate(gr_inp)
        ch_result = engine.calculate(ch_inp)

        assert gr_result.downturn_lgd > ch_result.downturn_lgd

    def test_spain_higher_than_germany(self):
        """Spain (ES=1.25) should have higher severity than Germany (DE=0.90)."""
        engine = LGDDownturnEngine()
        es_inp = _make_downturn_input(country="ES")
        de_inp = _make_downturn_input(country="DE")

        es_result = engine.calculate(es_inp)
        de_result = engine.calculate(de_inp)

        assert es_result.downturn_lgd > de_result.downturn_lgd

    def test_unknown_country_defaults_to_1(self):
        """Unknown country code should default to severity 1.0 without crash."""
        engine = LGDDownturnEngine()
        inp = _make_downturn_input(country="ZZ")
        result = engine.calculate(inp)
        assert result.downturn_lgd > 0

    def test_all_25_countries_present(self):
        """Verify all 25 countries from the spec are in the table."""
        expected = {
            "US", "UK", "DE", "FR", "ES", "IT", "GR", "PT", "IE", "NL",
            "BE", "AT", "CH", "JP", "AU", "CA", "SE", "NO", "DK", "FI",
            "SG", "HK", "KR", "BR", "IN",
        }
        assert set(COUNTRY_CYCLE_SEVERITY.keys()) == expected


class TestDownturnSector:
    """Sector severity multipliers."""

    def test_coal_mining_higher_than_technology(self):
        """Coal Mining (1.70) >> Technology (0.90)."""
        engine = LGDDownturnEngine()
        cm_inp = _make_downturn_input(sector="Coal Mining")
        tech_inp = _make_downturn_input(sector="Technology")

        cm_result = engine.calculate(cm_inp)
        tech_result = engine.calculate(tech_inp)

        assert cm_result.downturn_lgd > tech_result.downturn_lgd

    def test_oil_gas_higher_than_healthcare(self):
        """Oil & Gas (1.50) > Healthcare (0.85)."""
        engine = LGDDownturnEngine()
        og_inp = _make_downturn_input(sector="Oil & Gas")
        hc_inp = _make_downturn_input(sector="Healthcare")

        og_result = engine.calculate(og_inp)
        hc_result = engine.calculate(hc_inp)

        assert og_result.downturn_lgd > hc_result.downturn_lgd

    def test_all_19_sectors_present(self):
        """Verify all 19 sectors from the spec are in the table."""
        assert len(SECTOR_DOWNTURN_MULT) == 19


class TestDownturnClimate:
    """Climate overlay tests."""

    def test_stranded_asset_haircut(self):
        """Coal Mining with fossil fuel collateral should get stranded addon."""
        engine = LGDDownturnEngine(include_climate_overlay=True)
        inp = _make_downturn_input(
            sector="Coal Mining",
            is_fossil_fuel_collateral=True,
        )
        result = engine.calculate(inp)
        assert result.contribution.climate_stranded_addon > 0

    def test_no_climate_overlay(self):
        """With climate overlay OFF, all climate components should be zero."""
        engine = LGDDownturnEngine(include_climate_overlay=False)
        inp = _make_downturn_input(
            sector="Oil & Gas",
            is_fossil_fuel_collateral=True,
            physical_risk_level="extreme",
            epc_rating="G",
        )
        result = engine.calculate(inp)
        assert result.contribution.climate_stranded_addon == 0
        assert result.contribution.climate_physical_addon == 0
        assert result.contribution.green_premium_adjustment == 0

    def test_climate_on_vs_off(self):
        """Climate overlay ON should produce higher LGD for stranded sectors."""
        on_engine = LGDDownturnEngine(include_climate_overlay=True)
        off_engine = LGDDownturnEngine(include_climate_overlay=False)
        inp = _make_downturn_input(
            sector="Oil & Gas",
            is_fossil_fuel_collateral=True,
            physical_risk_level="high",
        )
        on_result = on_engine.calculate(inp)
        off_result = off_engine.calculate(inp)
        assert on_result.downturn_lgd > off_result.downturn_lgd

    def test_physical_risk_extreme(self):
        """Extreme physical risk should add +20% * scenario_mult."""
        engine = LGDDownturnEngine()
        inp = _make_downturn_input(physical_risk_level="extreme")
        result = engine.calculate(inp)
        assert result.contribution.climate_physical_addon > 0

    def test_green_premium_epc_a(self):
        """EPC A should give a negative (green) premium (-0.05)."""
        engine = LGDDownturnEngine()
        inp_a = _make_downturn_input(epc_rating="A")
        result_a = engine.calculate(inp_a)
        assert result_a.contribution.green_premium_adjustment < 0

    def test_brown_discount_epc_g(self):
        """EPC G should give a positive (brown) penalty (+0.08)."""
        engine = LGDDownturnEngine()
        inp_g = _make_downturn_input(epc_rating="G")
        result_g = engine.calculate(inp_g)
        assert result_g.contribution.green_premium_adjustment > 0

    def test_all_8_stranded_sectors(self):
        """Verify all 8 stranded sectors from the spec are present."""
        expected = {
            "Coal Mining", "Oil & Gas", "Gas Utilities", "Thermal Power",
            "Carbon-Intensive Manufacturing", "Cement", "Steel", "Chemicals",
        }
        assert set(CLIMATE_STRANDED_HAIRCUTS.keys()) == expected

    def test_green_premium_all_epc_grades(self):
        """Verify all 7 EPC grades A-G are in the green premium table."""
        for grade in ["A", "B", "C", "D", "E", "F", "G"]:
            assert grade in GREEN_PREMIUM


class TestDownturnFloors:
    """Regulatory floor tests (CRR2 Art. 164)."""

    def test_residential_mortgage_floor(self):
        """Residential mortgage floor = 10%."""
        engine = LGDDownturnEngine()
        inp = _make_downturn_input(
            long_run_avg_lgd=0.05,
            collateral_type="real_estate_residential",
            asset_class="RETAIL_MORTGAGE",
        )
        result = engine.calculate(inp)
        assert result.downturn_lgd >= REGULATORY_LGD_FLOORS["RESIDENTIAL_MORTGAGE"]
        assert result.contribution.regulatory_floor_applied

    def test_commercial_mortgage_floor(self):
        """Commercial mortgage floor = 15%."""
        engine = LGDDownturnEngine()
        inp = _make_downturn_input(
            long_run_avg_lgd=0.08,
            collateral_type="real_estate_commercial",
        )
        result = engine.calculate(inp)
        assert result.downturn_lgd >= REGULATORY_LGD_FLOORS["COMMERCIAL_MORTGAGE"]

    def test_corporate_unsecured_floor(self):
        """Corporate unsecured floor = 25%."""
        engine = LGDDownturnEngine(scenario="BASE")
        inp = _make_downturn_input(
            long_run_avg_lgd=0.10,
            collateral_type="unsecured",
            asset_class="CORPORATE",
        )
        result = engine.calculate(inp)
        assert result.downturn_lgd >= REGULATORY_LGD_FLOORS["CORPORATE_UNSECURED"]

    def test_sme_secured_floor(self):
        """SME secured floor = 15%."""
        engine = LGDDownturnEngine(scenario="BASE")
        inp = _make_downturn_input(
            long_run_avg_lgd=0.05,
            collateral_type="equipment",
            asset_class="SME",
        )
        result = engine.calculate(inp)
        assert result.downturn_lgd >= REGULATORY_LGD_FLOORS["SME_SECURED"]

    def test_all_7_floor_categories(self):
        """Verify all 7 regulatory floor categories from the spec."""
        expected = {
            "RESIDENTIAL_MORTGAGE", "COMMERCIAL_MORTGAGE",
            "CORPORATE_UNSECURED", "CORPORATE_SECURED",
            "SME_UNSECURED", "SME_SECURED", "RETAIL_UNSECURED",
        }
        assert set(REGULATORY_LGD_FLOORS.keys()) == expected


class TestDownturnScenarios:
    """Scenario severity tests (BASE=0.6, ADVERSE=1.0, SEVERE=1.5)."""

    def test_severe_higher_than_base(self):
        """SEVERE should produce higher LGD than BASE."""
        base_engine = LGDDownturnEngine(scenario="BASE")
        severe_engine = LGDDownturnEngine(scenario="SEVERE")
        inp = _make_downturn_input()

        base_result = base_engine.calculate(inp)
        severe_result = severe_engine.calculate(inp)

        assert severe_result.downturn_lgd > base_result.downturn_lgd

    def test_adverse_between_base_and_severe(self):
        """ADVERSE should sit between BASE and SEVERE."""
        engines = {
            s: LGDDownturnEngine(scenario=s)
            for s in ["BASE", "ADVERSE", "SEVERE"]
        }
        inp = _make_downturn_input(sector="Coal Mining")

        results = {s: e.calculate(inp).downturn_lgd for s, e in engines.items()}
        assert results["BASE"] <= results["ADVERSE"] <= results["SEVERE"]

    def test_scenario_multiplier_values(self):
        """Verify exact scenario multiplier values."""
        from services.lgd_downturn_engine import SCENARIO_MULTIPLIERS
        assert SCENARIO_MULTIPLIERS["BASE"] == 0.6
        assert SCENARIO_MULTIPLIERS["ADVERSE"] == 1.0
        assert SCENARIO_MULTIPLIERS["SEVERE"] == 1.5


class TestDownturnBatch:
    """Batch calculation tests."""

    def test_batch_execution(self):
        """Batch of 20 should return valid portfolio-level summaries."""
        engine = LGDDownturnEngine()
        inputs = _make_batch_inputs(20)
        result = engine.calculate_batch(inputs)

        assert result.exposure_count == 20
        assert len(result.results) == 20
        assert result.portfolio_avg_dt_lgd >= result.portfolio_avg_lr_lgd
        assert result.portfolio_avg_uplift_pct >= 0

    def test_batch_floor_count(self):
        """Floor count should be between 0 and total exposures."""
        engine = LGDDownturnEngine()
        inputs = _make_batch_inputs(20)
        result = engine.calculate_batch(inputs)
        assert result.floor_applied_count >= 0
        assert result.floor_applied_count <= 20

    def test_batch_all_results_valid(self):
        """Every result in the batch should have valid LGD in [0, 1]."""
        engine = LGDDownturnEngine()
        inputs = _make_batch_inputs(20)
        result = engine.calculate_batch(inputs)
        for r in result.results:
            assert 0 <= r.downturn_lgd <= 1.0
            assert r.downturn_lgd >= r.long_run_avg_lgd


class TestDownturnUtilities:
    """Utility / static method tests."""

    def test_get_regulatory_floors(self):
        floors = LGDDownturnEngine.get_regulatory_floors()
        assert "RESIDENTIAL_MORTGAGE" in floors
        assert floors["RESIDENTIAL_MORTGAGE"] == 0.10

    def test_get_downturn_addons(self):
        addons = LGDDownturnEngine.get_downturn_addons()
        assert "real_estate_residential" in addons
        assert addons["unsecured"] == 0.12

    def test_get_green_premium_table(self):
        table = LGDDownturnEngine.get_green_premium_table()
        assert table["A"] < 0   # Green premium
        assert table["G"] > 0   # Brown discount
        assert table["D"] == 0  # Neutral

    def test_get_sector_severity(self):
        sectors = LGDDownturnEngine.get_sector_severity()
        assert sectors["Coal Mining"] == 1.70
        assert sectors["Government"] == 0.70

    def test_get_country_severity(self):
        countries = LGDDownturnEngine.get_country_cycle_severity()
        assert countries["GR"] == 1.50
        assert countries["CH"] == 0.70

    def test_get_climate_haircuts(self):
        haircuts = LGDDownturnEngine.get_climate_stranded_haircuts()
        assert haircuts["Coal Mining"] == 0.40
        assert haircuts["Chemicals"] == 0.08


# ===========================================================================
# VINTAGE ANALYZER TESTS
# ===========================================================================


class TestVintageBasic:
    """Basic vintage analysis."""

    def test_analyze_returns_result(self):
        """Analyze should return a populated result."""
        exposures = _make_vintage_exposures(100)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        assert result.total_exposures == 100
        assert len(result.cohorts) > 0
        assert result.vintage_matrix is not None

    def test_empty_raises(self):
        """Empty exposures list should raise ValueError."""
        analyzer = VintageAnalyzer()
        with pytest.raises(ValueError):
            analyzer.analyze([])


class TestVintageCohorts:
    """Cohort construction and metrics."""

    def test_annual_cohorts(self):
        """Annual granularity should produce cohorts for 2018-2024."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025, granularity="annual")
        result = analyzer.analyze(exposures)

        years = {c.vintage_year for c in result.cohorts}
        assert len(years) >= 5

    def test_quarterly_cohorts(self):
        """Quarterly should produce more cohorts than annual."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025, granularity="quarterly")
        result = analyzer.analyze(exposures)

        assert len(result.cohorts) > 7

    def test_cohort_counts_sum(self):
        """Sum of cohort exposure counts should equal total."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        total = sum(c.exposure_count for c in result.cohorts)
        assert total == 200

    def test_default_rate_range(self):
        """Cumulative DR should be in [0, 1]."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        for c in result.cohorts:
            assert 0 <= c.cumulative_default_rate <= 1

    def test_stage_counts_consistent(self):
        """Stage 1 + Stage 2 + Stage 3 should equal total exposure count."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        for c in result.cohorts:
            assert c.stage1_count + c.stage2_count + c.stage3_count == c.exposure_count


class TestVintageMatrix:
    """Vintage matrix tests."""

    def test_matrix_dimensions(self):
        """Matrix should have correct dimensions."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        m = result.vintage_matrix
        assert len(m.vintage_labels) > 0
        assert len(m.age_labels) > 0
        assert len(m.cumulative_dr_matrix) == len(m.vintage_labels)
        assert len(m.marginal_dr_matrix) == len(m.vintage_labels)

    def test_cumulative_dr_non_decreasing(self):
        """Cumulative DR should be non-decreasing across ages for each vintage."""
        exposures = _make_vintage_exposures(500)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        for row in result.vintage_matrix.cumulative_dr_matrix:
            prev = 0.0
            for val in row:
                if val is not None:
                    assert val >= prev - 0.0001  # Small tolerance
                    prev = val

    def test_marginal_dr_non_negative(self):
        """Marginal DR should be >= 0 for all observable cells."""
        exposures = _make_vintage_exposures(500)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        for row in result.vintage_matrix.marginal_dr_matrix:
            for val in row:
                if val is not None:
                    assert val >= -0.0001  # Small tolerance

    def test_none_for_unobservable_ages(self):
        """Recent vintages should have None for ages they have not reached."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        m = result.vintage_matrix
        # The most recent vintage (2024) with reference 2025 should have
        # age 1 observable but age 2+ should be None (if max_age > 1)
        if len(m.age_labels) > 1:
            last_row = m.cumulative_dr_matrix[-1]
            # At least the last cell should be None for recent vintage
            assert last_row[-1] is None or len(m.age_labels) <= 1


class TestEarlyWarning:
    """Early warning system tests."""

    def test_early_warning_detection(self):
        """early_warning field should be boolean for all cohorts."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        for c in result.cohorts:
            assert isinstance(c.early_warning, bool)

    def test_worst_best_vintage(self):
        """worst_vintage_dr should be >= best_vintage_dr."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        assert result.worst_vintage != ""
        assert result.best_vintage != ""
        assert result.worst_vintage_dr >= result.best_vintage_dr

    def test_early_warning_threshold_value(self):
        """Threshold should be 0.50 (flag if DR > 1.5x benchmark)."""
        from services.vintage_analyzer import EARLY_WARNING_THRESHOLD
        assert EARLY_WARNING_THRESHOLD == 0.50


class TestECBBackstop:
    """ECB NPE coverage tests (EU Regulation 2019/630)."""

    def test_npe_coverage_computed(self):
        """Cohorts with NPEs should have non-negative coverage ratios."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        npe_cohorts = [c for c in result.cohorts if c.npe_count > 0]
        for c in npe_cohorts:
            assert c.npe_coverage_ratio >= 0

    def test_coverage_gap_non_negative(self):
        """Total coverage gap should be >= 0."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        assert result.npe_coverage_gap_total >= 0

    def test_ecb_unsecured_year2_full_writeoff(self):
        """ECB backstop: unsecured NPE should be 100% covered by year 2."""
        table = ECB_NPE_COVERAGE
        assert table[2]["unsecured"] == 1.00

    def test_ecb_secured_year9_full_writeoff(self):
        """ECB backstop: secured NPE should be 100% covered by year 9."""
        table = ECB_NPE_COVERAGE
        assert table[9]["secured"] == 1.00

    def test_ecb_secured_ramp(self):
        """ECB secured coverage should ramp up through years 3-9."""
        table = ECB_NPE_COVERAGE
        prev = 0.0
        for yr in range(3, 10):
            assert table[yr]["secured"] >= prev
            prev = table[yr]["secured"]


class TestGreenTrend:
    """Green origination trend tests."""

    def test_green_trend_populated(self):
        """Green trend should have entries with correct keys."""
        exposures = _make_vintage_exposures(200)
        analyzer = VintageAnalyzer(reference_year=2025)
        result = analyzer.analyze(exposures)

        assert len(result.green_origination_trend) > 0
        for entry in result.green_origination_trend:
            assert "vintage" in entry
            assert "green_share_pct" in entry
            assert 0 <= entry["green_share_pct"] <= 100

    def test_green_share_increasing(self):
        """Green share should generally increase over time (by construction)."""
        exposures = _make_vintage_exposures(500)
        analyzer = VintageAnalyzer(reference_year=2025, granularity="annual")
        result = analyzer.analyze(exposures)

        trend = result.green_origination_trend
        if len(trend) >= 3:
            first_share = trend[0]["green_share_pct"]
            last_share = trend[-1]["green_share_pct"]
            # The fixture increases green share by 5% per year from 15%
            assert last_share >= first_share


class TestVintageUtilities:
    """Utility method tests."""

    def test_ecb_coverage_table(self):
        """ECB table should have entries for years 0-9."""
        table = VintageAnalyzer.get_ecb_npe_coverage_table()
        assert 0 in table
        assert 9 in table
        assert table[2]["unsecured"] == 1.00

    def test_benchmark_rates(self):
        """Benchmark rates should increase with age."""
        rates = VintageAnalyzer.get_benchmark_default_rates()
        assert 1 in rates
        assert rates[1] < rates[5]
        assert rates[10] == 0.125

    def test_early_warning_threshold(self):
        """Threshold getter should return 0.50."""
        threshold = VintageAnalyzer.get_early_warning_threshold()
        assert threshold == 0.50
