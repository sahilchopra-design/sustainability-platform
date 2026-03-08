"""
Tests for Real Estate Portfolio NAV Roll-Up Engine + CRREM Integration.

Coverage:
  - NAV headline calculation (GAV, debt, NAV)
  - Yield metrics (weighted avg cap rate, NOI yield, occupancy)
  - ESG-adjusted NAV (green premium, climate discount)
  - Carbon metrics (intensity, total emissions)
  - EPC distribution (count + GAV breakdown)
  - Green/brown split
  - MEPS compliance (2030/2033 by country)
  - CRREM stranding analysis (per-property + portfolio)
  - Concentration analysis (sector, geographic)
  - Edge cases (empty portfolio, single property, all stranded)
"""

import pytest
from datetime import date
from decimal import Decimal

from services.re_portfolio_engine import (
    CRREMPropertyResult,
    EPCDistribution,
    GeographicConcentration,
    MEPSComplianceResult,
    MEPS_TIMELINES,
    PortfolioDefinition,
    PortfolioNAVResult,
    PropertyAsset,
    REPortfolioEngine,
    SectorConcentration,
    epc_meets_minimum,
    EPC_RANK,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return REPortfolioEngine()


def _make_property(**overrides) -> PropertyAsset:
    defaults = dict(
        property_id="PROP-001",
        name="One London Wall",
        property_type="office",
        country_iso="GB",
        city="London",
        floor_area_m2=Decimal("5000"),
        year_built=2010,
        market_value=Decimal("15000000"),
        book_value=Decimal("14000000"),
        cap_rate_pct=Decimal("5.5"),
        noi=Decimal("825000"),
        occupancy_pct=Decimal("92"),
        gross_rental_income=Decimal("950000"),
        epc_rating="B",
        energy_intensity_kwh_m2=Decimal("180"),
        carbon_intensity_kgco2_m2=Decimal("37.3"),
        outstanding_debt=Decimal("8000000"),
        loan_to_value_pct=Decimal("53.3"),
        esg_adjustment_pct=Decimal("2.5"),
        climate_adjustment_pct=Decimal("-1.5"),
    )
    defaults.update(overrides)
    return PropertyAsset(**defaults)


def _make_portfolio(properties: list, **overrides) -> PortfolioDefinition:
    defaults = dict(
        portfolio_id="PF-001",
        name="UK Commercial Fund",
        fund_structure="open_end",
        base_currency="GBP",
        valuation_basis="market_value",
        valuation_date=date(2026, 3, 1),
        properties=properties,
    )
    defaults.update(overrides)
    return PortfolioDefinition(**defaults)


def _sample_portfolio() -> PortfolioDefinition:
    """5-property diversified portfolio."""
    props = [
        _make_property(
            property_id="PROP-001", name="City Tower", property_type="office",
            country_iso="GB", floor_area_m2=Decimal("8000"),
            market_value=Decimal("25000000"), noi=Decimal("1375000"),
            cap_rate_pct=Decimal("5.5"), occupancy_pct=Decimal("95"),
            gross_rental_income=Decimal("1500000"),
            epc_rating="B", energy_intensity_kwh_m2=Decimal("170"),
            carbon_intensity_kgco2_m2=Decimal("35.2"),
            outstanding_debt=Decimal("12000000"),
            esg_adjustment_pct=Decimal("3"), climate_adjustment_pct=Decimal("-1"),
        ),
        _make_property(
            property_id="PROP-002", name="Westfield Retail", property_type="retail",
            country_iso="GB", floor_area_m2=Decimal("12000"),
            market_value=Decimal("35000000"), noi=Decimal("2275000"),
            cap_rate_pct=Decimal("6.5"), occupancy_pct=Decimal("88"),
            gross_rental_income=Decimal("2800000"),
            epc_rating="D", energy_intensity_kwh_m2=Decimal("280"),
            carbon_intensity_kgco2_m2=Decimal("58.0"),
            outstanding_debt=Decimal("18000000"),
            esg_adjustment_pct=Decimal("-2"), climate_adjustment_pct=Decimal("-5"),
        ),
        _make_property(
            property_id="PROP-003", name="Hamburg Logistik", property_type="industrial",
            country_iso="DE", floor_area_m2=Decimal("15000"),
            market_value=Decimal("18000000"), noi=Decimal("1080000"),
            cap_rate_pct=Decimal("6.0"), occupancy_pct=Decimal("100"),
            gross_rental_income=Decimal("1100000"),
            epc_rating="C", energy_intensity_kwh_m2=Decimal("120"),
            carbon_intensity_kgco2_m2=Decimal("45.6"),
            outstanding_debt=Decimal("9000000"),
            esg_adjustment_pct=Decimal("0"), climate_adjustment_pct=Decimal("-2"),
        ),
        _make_property(
            property_id="PROP-004", name="Paris Résidence", property_type="multifamily",
            country_iso="FR", floor_area_m2=Decimal("6000"),
            market_value=Decimal("22000000"), noi=Decimal("880000"),
            cap_rate_pct=Decimal("4.0"), occupancy_pct=Decimal("97"),
            gross_rental_income=Decimal("920000"),
            epc_rating="A", energy_intensity_kwh_m2=Decimal("85"),
            carbon_intensity_kgco2_m2=Decimal("4.4"),
            outstanding_debt=Decimal("11000000"),
            esg_adjustment_pct=Decimal("5"), climate_adjustment_pct=Decimal("0"),
        ),
        _make_property(
            property_id="PROP-005", name="Amsterdam Hotel", property_type="hotel",
            country_iso="NL", floor_area_m2=Decimal("4000"),
            market_value=Decimal("20000000"), noi=Decimal("1200000"),
            cap_rate_pct=Decimal("6.0"), occupancy_pct=Decimal("82"),
            gross_rental_income=Decimal("1600000"),
            epc_rating="E", energy_intensity_kwh_m2=Decimal("310"),
            carbon_intensity_kgco2_m2=Decimal("101.7"),
            outstanding_debt=Decimal("10000000"),
            esg_adjustment_pct=Decimal("-3"), climate_adjustment_pct=Decimal("-8"),
        ),
    ]
    return _make_portfolio(props)


# ---------------------------------------------------------------------------
# EPC Utility Tests
# ---------------------------------------------------------------------------

class TestEPCUtility:
    def test_epc_rank_ordering(self):
        assert EPC_RANK["A+"] < EPC_RANK["A"] < EPC_RANK["B"] < EPC_RANK["G"]

    def test_epc_meets_minimum_exact(self):
        assert epc_meets_minimum("B", "B") is True

    def test_epc_meets_minimum_better(self):
        assert epc_meets_minimum("A", "C") is True

    def test_epc_meets_minimum_worse(self):
        assert epc_meets_minimum("E", "C") is False

    def test_epc_meets_minimum_a_plus(self):
        assert epc_meets_minimum("A+", "A") is True


# ---------------------------------------------------------------------------
# NAV Headline Tests
# ---------------------------------------------------------------------------

class TestNAVHeadline:
    def test_single_property_nav(self, engine):
        prop = _make_property(market_value=Decimal("10000000"), outstanding_debt=Decimal("5000000"))
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)

        assert result.gross_asset_value == Decimal("10000000")
        assert result.total_debt == Decimal("5000000")
        assert result.net_asset_value == Decimal("5000000")
        assert result.property_count == 1

    def test_multi_property_nav(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)

        expected_gav = Decimal("120000000")  # 25+35+18+22+20
        expected_debt = Decimal("60000000")  # 12+18+9+11+10
        assert result.gross_asset_value == expected_gav
        assert result.total_debt == expected_debt
        assert result.net_asset_value == expected_gav - expected_debt
        assert result.property_count == 5

    def test_nav_per_property(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        expected = (result.net_asset_value / 5).quantize(Decimal("0.01"))
        assert result.nav_per_property == expected

    def test_empty_portfolio(self, engine):
        portfolio = _make_portfolio([])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.gross_asset_value == Decimal("0")
        assert result.property_count == 0


# ---------------------------------------------------------------------------
# Yield Metrics Tests
# ---------------------------------------------------------------------------

class TestYieldMetrics:
    def test_total_noi(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        expected_noi = Decimal("6810000")  # 1375000+2275000+1080000+880000+1200000
        assert result.total_noi == expected_noi

    def test_weighted_avg_cap_rate(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        # Weighted by market value
        assert result.weighted_avg_cap_rate_pct > Decimal("4")
        assert result.weighted_avg_cap_rate_pct < Decimal("7")

    def test_noi_yield(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        expected = (Decimal("6810000") / Decimal("120000000") * 100).quantize(Decimal("0.01"))
        assert result.portfolio_noi_yield_pct == expected

    def test_weighted_avg_occupancy(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.weighted_avg_occupancy_pct > Decimal("80")
        assert result.weighted_avg_occupancy_pct < Decimal("100")


# ---------------------------------------------------------------------------
# ESG-Adjusted NAV Tests
# ---------------------------------------------------------------------------

class TestESGAdjustedNAV:
    def test_positive_esg_adjustment(self, engine):
        prop = _make_property(
            market_value=Decimal("10000000"),
            esg_adjustment_pct=Decimal("5"),
            climate_adjustment_pct=Decimal("0"),
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.esg_adjusted_gav == Decimal("10500000.00")

    def test_negative_climate_adjustment(self, engine):
        prop = _make_property(
            market_value=Decimal("10000000"),
            esg_adjustment_pct=Decimal("0"),
            climate_adjustment_pct=Decimal("-10"),
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.climate_adjusted_gav == Decimal("9000000.00")

    def test_combined_adjustments(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        # ESG adjustment net should be small (mix of positive and negative)
        assert result.esg_adjusted_gav != result.gross_asset_value


# ---------------------------------------------------------------------------
# Carbon Metrics Tests
# ---------------------------------------------------------------------------

class TestCarbonMetrics:
    def test_total_floor_area(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        expected_area = Decimal("45000")  # 8000+12000+15000+6000+4000
        assert result.total_floor_area_m2 == expected_area

    def test_carbon_intensity_positive(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.portfolio_carbon_intensity_kgco2_m2 > 0

    def test_total_emissions_positive(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.total_emissions_tco2e > 0

    def test_derived_carbon_from_energy(self, engine):
        """When carbon_intensity is 0, derive from energy_intensity * grid EF."""
        prop = _make_property(
            country_iso="GB",
            floor_area_m2=Decimal("1000"),
            energy_intensity_kwh_m2=Decimal("200"),
            carbon_intensity_kgco2_m2=Decimal("0"),
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.total_emissions_tco2e > 0


# ---------------------------------------------------------------------------
# EPC Distribution Tests
# ---------------------------------------------------------------------------

class TestEPCDistribution:
    def test_distribution_has_all_ratings(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        ratings = [e.rating for e in result.epc_distribution]
        assert "A+" in ratings
        assert "G" in ratings
        assert len(ratings) == 8

    def test_distribution_counts_correct(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        total_count = sum(e.property_count for e in result.epc_distribution)
        assert total_count == 5

    def test_distribution_gav_sums(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        total_gav = sum(e.gav_total for e in result.epc_distribution)
        assert total_gav == result.gross_asset_value


# ---------------------------------------------------------------------------
# Green / Brown Split Tests
# ---------------------------------------------------------------------------

class TestGreenBrownSplit:
    def test_green_brown_counts(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        # Green (A+, A, B): PROP-001 (B), PROP-004 (A) = 2
        # Brown (D, E, F, G): PROP-002 (D), PROP-005 (E) = 2
        # C is neither: PROP-003 (C) = 1
        assert result.green_property_count == 2
        assert result.brown_property_count == 2

    def test_green_pct_by_gav(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        # Green GAV: 25M + 22M = 47M of 120M
        expected_pct = Decimal("39.2")  # 47/120*100
        assert abs(result.green_pct_by_gav - expected_pct) < Decimal("0.2")


# ---------------------------------------------------------------------------
# MEPS Compliance Tests
# ---------------------------------------------------------------------------

class TestMEPSCompliance:
    def test_gb_2030_compliance(self, engine):
        """GB MEPS 2030 requires EPC B."""
        prop = _make_property(country_iso="GB", epc_rating="B")
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.meps_compliant_2030_count == 1

    def test_gb_2030_non_compliant(self, engine):
        """GB EPC D fails MEPS 2030 (needs B)."""
        prop = _make_property(country_iso="GB", epc_rating="D")
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.meps_compliant_2030_count == 0
        assert len(result.meps_non_compliant_2030) == 1

    def test_nl_2030_requires_a(self, engine):
        """NL requires EPC A by 2030."""
        prop_a = _make_property(property_id="P1", country_iso="NL", epc_rating="A")
        prop_b = _make_property(property_id="P2", country_iso="NL", epc_rating="B")
        portfolio = _make_portfolio([prop_a, prop_b])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.meps_compliant_2030_count == 1

    def test_mixed_country_compliance(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        # Should have non-compliant properties
        assert result.meps_compliant_2030_pct < Decimal("100")

    def test_non_compliant_gap_bands(self, engine):
        prop = _make_property(country_iso="GB", epc_rating="E")
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        nc = result.meps_non_compliant_2030[0]
        # GB 2030 = B, current = E => gap = 3 bands (E→D→C→B)
        assert nc.gap_bands_to_2030 == 3


# ---------------------------------------------------------------------------
# CRREM Stranding Tests
# ---------------------------------------------------------------------------

class TestCRREMStranding:
    def test_efficient_property_not_stranded(self, engine):
        """A+ office in GB at 50 kWh/m2 — well below pathway."""
        prop = _make_property(
            property_type="office", country_iso="GB",
            energy_intensity_kwh_m2=Decimal("50"),
            epc_rating="A+",
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        crrem = result.crrem_property_results[0]
        assert crrem.is_already_stranded is False
        # Should not strand before 2050 (pathway reaches 55 in 2050, asset is at 50)
        assert crrem.stranding_year_1_5c is None or crrem.stranding_year_1_5c >= 2050

    def test_inefficient_property_stranded(self, engine):
        """Retail in GB at 350 kWh/m2 — already exceeds 2025 threshold of 265."""
        prop = _make_property(
            property_type="retail", country_iso="GB",
            energy_intensity_kwh_m2=Decimal("350"),
            epc_rating="G",
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        crrem = result.crrem_property_results[0]
        assert crrem.is_already_stranded is True

    def test_stranding_year_future(self, engine):
        """Office in GB at 180 kWh/m2 — above 2030 threshold (155), strandsby ~2028."""
        prop = _make_property(
            property_type="office", country_iso="GB",
            energy_intensity_kwh_m2=Decimal("180"),
            epc_rating="C",
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        crrem = result.crrem_property_results[0]
        assert crrem.stranding_year_1_5c is not None
        assert 2026 <= crrem.stranding_year_1_5c <= 2032

    def test_2c_scenario_later_stranding(self, engine):
        """2C pathway is less aggressive; stranding year should be later."""
        prop = _make_property(
            property_type="office", country_iso="GB",
            energy_intensity_kwh_m2=Decimal("180"),
            epc_rating="C",
        )
        portfolio = _make_portfolio([prop])
        result_15 = engine.calculate_portfolio_nav(portfolio, crrem_scenario="1.5C")
        result_20 = engine.calculate_portfolio_nav(portfolio, crrem_scenario="2C")

        strand_15 = result_15.crrem_property_results[0].stranding_year_1_5c
        strand_20 = result_20.crrem_property_results[0].stranding_year_1_5c
        # Under 2C, stranding should be same or later
        if strand_15 and strand_20:
            assert strand_20 >= strand_15

    def test_portfolio_stranding_risk_pct(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.crrem_portfolio_stranding_risk_pct >= Decimal("0")
        assert result.crrem_portfolio_stranding_risk_pct <= Decimal("100")

    def test_carbon_cost_calculated(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.crrem_total_annual_carbon_cost_eur > 0

    def test_annual_reduction_required(self, engine):
        prop = _make_property(
            property_type="office", country_iso="GB",
            energy_intensity_kwh_m2=Decimal("200"),
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        crrem = result.crrem_property_results[0]
        assert crrem.annual_reduction_required_pct > 0

    def test_gap_to_pathway_pct(self, engine):
        """Property above pathway should have positive gap."""
        prop = _make_property(
            property_type="office", country_iso="GB",
            energy_intensity_kwh_m2=Decimal("250"),
        )
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        crrem = result.crrem_property_results[0]
        assert crrem.gap_to_pathway_pct > 0

    def test_avg_years_to_stranding(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        if result.crrem_avg_years_to_stranding is not None:
            assert result.crrem_avg_years_to_stranding > 0


# ---------------------------------------------------------------------------
# Concentration Tests
# ---------------------------------------------------------------------------

class TestConcentration:
    def test_sector_concentration_sums_to_100(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        total_pct = sum(s.property_pct for s in result.sector_concentration)
        assert abs(total_pct - Decimal("100")) < Decimal("1")

    def test_sector_concentration_gav_sums(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        total_gav = sum(s.gav_total for s in result.sector_concentration)
        assert total_gav == result.gross_asset_value

    def test_geographic_concentration_countries(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        countries = [g.country_iso for g in result.geographic_concentration]
        assert "GB" in countries
        assert "DE" in countries
        assert "FR" in countries
        assert "NL" in countries

    def test_geographic_gav_sums(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        total_gav = sum(g.gav_total for g in result.geographic_concentration)
        assert total_gav == result.gross_asset_value


# ---------------------------------------------------------------------------
# Validation Summary Tests
# ---------------------------------------------------------------------------

class TestValidationSummary:
    def test_validation_summary_present(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        vs = result.validation_summary
        assert vs["methodology"] is not None
        assert vs["portfolio_id"] == "PF-001"
        assert vs["property_count"] == 5
        assert vs["crrem_scenario"] == "1.5C"

    def test_validation_data_quality_notes(self, engine):
        portfolio = _sample_portfolio()
        result = engine.calculate_portfolio_nav(portfolio)
        assert len(result.validation_summary["data_quality_notes"]) > 0


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_single_property(self, engine):
        prop = _make_property()
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.property_count == 1
        assert result.nav_per_property == result.net_asset_value

    def test_zero_energy_intensity(self, engine):
        prop = _make_property(energy_intensity_kwh_m2=Decimal("0"), carbon_intensity_kgco2_m2=Decimal("0"))
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.total_emissions_tco2e == Decimal("0")

    def test_unknown_country_falls_back_to_eu_meps(self, engine):
        prop = _make_property(country_iso="IT", epc_rating="F")
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        # Italy not in MEPS_TIMELINES → falls back to EU
        assert result.meps_compliant_2030_count == 0

    def test_unknown_property_type_crrem(self, engine):
        """Unknown property type should not crash CRREM."""
        prop = _make_property(property_type="parking_garage", energy_intensity_kwh_m2=Decimal("100"))
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        # Should still compute; CRREM result may have None stranding year
        assert result.crrem_property_results[0].stranding_year_1_5c is None

    def test_high_carbon_price_increases_cost(self, engine):
        portfolio = _sample_portfolio()
        r75 = engine.calculate_portfolio_nav(portfolio, carbon_price_eur_per_tco2=Decimal("75"))
        r150 = engine.calculate_portfolio_nav(portfolio, carbon_price_eur_per_tco2=Decimal("150"))
        assert r150.crrem_total_annual_carbon_cost_eur > r75.crrem_total_annual_carbon_cost_eur

    def test_all_green_portfolio(self, engine):
        props = [
            _make_property(property_id=f"P{i}", epc_rating="A", energy_intensity_kwh_m2=Decimal("60"))
            for i in range(3)
        ]
        portfolio = _make_portfolio(props)
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.green_property_count == 3
        assert result.brown_property_count == 0
        assert result.green_pct_by_gav == Decimal("100.0")

    def test_all_brown_portfolio(self, engine):
        props = [
            _make_property(property_id=f"P{i}", epc_rating="G", energy_intensity_kwh_m2=Decimal("400"))
            for i in range(3)
        ]
        portfolio = _make_portfolio(props)
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.brown_property_count == 3
        assert result.green_property_count == 0
        assert result.brown_pct_by_gav == Decimal("100.0")

    def test_no_debt_portfolio(self, engine):
        prop = _make_property(outstanding_debt=Decimal("0"), loan_to_value_pct=Decimal("0"))
        portfolio = _make_portfolio([prop])
        result = engine.calculate_portfolio_nav(portfolio)
        assert result.net_asset_value == result.gross_asset_value


# ---------------------------------------------------------------------------
# CRREM Pathway Interpolation Tests
# ---------------------------------------------------------------------------

class TestCRREMInterpolation:
    def test_exact_year_lookup(self, engine):
        """Lookup for a year that exists in pathway data."""
        pathway = {2020: 215, 2025: 190, 2030: 155}
        assert engine._interpolate_pathway(pathway, 2025) == 190

    def test_interpolated_year(self, engine):
        """Mid-point between 2020 (215) and 2025 (190) should be ~202.5."""
        pathway = {2020: 215.0, 2025: 190.0, 2030: 155.0}
        result = engine._interpolate_pathway(pathway, 2022)
        # 215 + (2/5) * (190 - 215) = 215 - 10 = 205
        assert abs(result - 205.0) < 0.1

    def test_before_first_year(self, engine):
        pathway = {2020: 215, 2025: 190}
        result = engine._interpolate_pathway(pathway, 2018)
        assert result == 215

    def test_after_last_year(self, engine):
        pathway = {2020: 215, 2025: 190, 2050: 55}
        result = engine._interpolate_pathway(pathway, 2060)
        assert result == 55

    def test_empty_pathway(self, engine):
        result = engine._interpolate_pathway({}, 2025)
        assert result is None
