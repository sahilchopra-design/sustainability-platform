"""
Tests — Insurance Risk Engine + Reference Data Tables
========================================================
107 tests across 17 test classes covering:
  - Reference data tables (WHO, IPCC, Solvency II, Basel III, FATF, FAO, EUDR, BNG)
  - Insurance risk engine (mortality, liability, nat-cat, climate freq, underwriting,
    retrocession, medical trend, comprehensive)
  - API routes (import verification, endpoint existence)
  - Data lineage integration (insurance module signature, dependency edges)
"""
import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.reference_data_tables import (
    WHO_MORTALITY_TABLES,
    IPCC_AR6_DAMAGE_FUNCTIONS,
    SOLVENCY2_NAT_CAT_FACTORS,
    SOLVENCY2_PERIL_CORRELATIONS,
    BASEL3_HQLA_CLASSIFICATION,
    BASEL3_LCR_OUTFLOW_RATES,
    BASEL3_NSFR_ASF_FACTORS,
    BASEL3_NSFR_RSF_FACTORS,
    FATF_COUNTRY_RISK_RATINGS,
    FAO_CROP_YIELD_DATABASE,
    EUDR_COUNTRY_BENCHMARKS,
    EUDR_COMMODITY_DEFINITIONS,
    BNG_HABITAT_DISTINCTIVENESS,
    BNG_CONDITION_MULTIPLIERS,
    BNG_STRATEGIC_SIGNIFICANCE,
    BNG_TRADING_RULES,
    get_mortality_rate,
    get_damage_function,
    get_nat_cat_factor,
    get_fatf_rating,
    get_crop_yield,
    get_eudr_country_risk,
    get_habitat_distinctiveness,
    calculate_habitat_units,
)
from services.insurance_risk_engine import InsuranceRiskEngine


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — WHO Mortality Tables
# ═══════════════════════════════════════════════════════════════════════════

class TestWHOMortalityTables:
    """Verify WHO life table data completeness and integrity."""

    def test_country_count(self):
        assert len(WHO_MORTALITY_TABLES) >= 10

    def test_countries_have_both_sexes(self):
        for country, data in WHO_MORTALITY_TABLES.items():
            assert "male" in data, f"{country} missing male"
            assert "female" in data, f"{country} missing female"

    def test_age_bands_present(self):
        expected_bands = ["0-1", "1-4", "5-14", "15-24", "25-34", "35-44",
                          "45-54", "55-64", "65-74", "75-84", "85+"]
        for country, data in WHO_MORTALITY_TABLES.items():
            for sex in ("male", "female"):
                for band in expected_bands:
                    assert band in data[sex], f"{country}/{sex} missing band {band}"

    def test_qx_values_valid(self):
        for country, data in WHO_MORTALITY_TABLES.items():
            for sex in ("male", "female"):
                for band, qx in data[sex].items():
                    assert 0 < qx < 1, f"{country}/{sex}/{band} qx={qx} out of range"

    def test_qx_increases_with_age(self):
        """Mortality generally increases with age (except infant mortality)."""
        for country in ["GBR", "USA", "DEU"]:
            data = WHO_MORTALITY_TABLES[country]["male"]
            # After age 5-14, mortality should generally increase
            assert data["65-74"] > data["35-44"]
            assert data["85+"] > data["65-74"]

    def test_get_mortality_rate_valid(self):
        qx = get_mortality_rate("GBR", "male", "45-54")
        assert qx is not None
        assert 0 < qx < 1

    def test_get_mortality_rate_invalid_country(self):
        qx = get_mortality_rate("ZZZ", "male", "45-54")
        assert qx is None

    def test_get_mortality_rate_invalid_sex(self):
        qx = get_mortality_rate("GBR", "other", "45-54")
        assert qx is None


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — IPCC AR6 Damage Functions
# ═══════════════════════════════════════════════════════════════════════════

class TestIPCCDamageFunctions:
    """Verify IPCC AR6 damage function data."""

    def test_hazard_count(self):
        assert len(IPCC_AR6_DAMAGE_FUNCTIONS) >= 8

    def test_hazard_keys_present(self):
        expected = ["tropical_cyclone", "river_flood", "coastal_flood",
                    "wildfire", "drought", "heatwave"]
        for h in expected:
            assert h in IPCC_AR6_DAMAGE_FUNCTIONS

    def test_damage_function_keys(self):
        for hazard, data in IPCC_AR6_DAMAGE_FUNCTIONS.items():
            assert "damage_pct_gdp_per_c" in data
            assert "frequency_multiplier_per_c" in data
            assert "severity_multiplier_per_c" in data
            assert "confidence" in data

    def test_multipliers_positive(self):
        for hazard, data in IPCC_AR6_DAMAGE_FUNCTIONS.items():
            assert data["frequency_multiplier_per_c"] > 0
            assert data["severity_multiplier_per_c"] > 0

    def test_get_damage_function_valid(self):
        df = get_damage_function("tropical_cyclone")
        assert df is not None
        assert "frequency_multiplier_per_c" in df

    def test_get_damage_function_invalid(self):
        df = get_damage_function("nonexistent_hazard")
        assert df is None


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — Solvency II Nat-Cat Factors
# ═══════════════════════════════════════════════════════════════════════════

class TestSolvency2NatCatFactors:
    """Verify Solvency II nat-cat data."""

    def test_country_count(self):
        assert len(SOLVENCY2_NAT_CAT_FACTORS) >= 13

    def test_peril_keys(self):
        for country, data in SOLVENCY2_NAT_CAT_FACTORS.items():
            for peril in data:
                assert "factor_200yr" in data[peril]
                assert "zone_count" in data[peril]

    def test_factors_positive(self):
        for country, data in SOLVENCY2_NAT_CAT_FACTORS.items():
            for peril, vals in data.items():
                assert vals["factor_200yr"] >= 0
                assert vals["zone_count"] >= 0

    def test_peril_correlations(self):
        assert len(SOLVENCY2_PERIL_CORRELATIONS) >= 6
        for pair, corr in SOLVENCY2_PERIL_CORRELATIONS.items():
            assert 0 <= corr <= 1

    def test_get_nat_cat_factor_valid(self):
        factor = get_nat_cat_factor("DE", "windstorm")
        assert factor is not None
        assert factor["factor_200yr"] > 0

    def test_get_nat_cat_factor_invalid_country(self):
        factor = get_nat_cat_factor("ZZ", "windstorm")
        assert factor is None


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — Basel III NSFR/LCR
# ═══════════════════════════════════════════════════════════════════════════

class TestBasel3Factors:
    """Verify Basel III HQLA, LCR outflow, NSFR ASF/RSF data."""

    def test_hqla_count(self):
        assert len(BASEL3_HQLA_CLASSIFICATION) >= 8

    def test_hqla_structure(self):
        for asset, data in BASEL3_HQLA_CLASSIFICATION.items():
            assert "level" in data
            assert "haircut_pct" in data
            assert "cap_pct" in data

    def test_lcr_outflow_count(self):
        assert len(BASEL3_LCR_OUTFLOW_RATES) >= 18

    def test_nsfr_asf_count(self):
        assert len(BASEL3_NSFR_ASF_FACTORS) >= 9

    def test_nsfr_rsf_count(self):
        assert len(BASEL3_NSFR_RSF_FACTORS) >= 17

    def test_haircuts_in_range(self):
        for asset, data in BASEL3_HQLA_CLASSIFICATION.items():
            assert 0 <= data["haircut_pct"] <= 100

    def test_outflow_rates_in_range(self):
        for item, data in BASEL3_LCR_OUTFLOW_RATES.items():
            assert 0 <= data["outflow_pct"] <= 100

    def test_asf_factors_in_range(self):
        for item, data in BASEL3_NSFR_ASF_FACTORS.items():
            assert 0 <= data["asf_factor_pct"] <= 100

    def test_rsf_factors_in_range(self):
        for item, data in BASEL3_NSFR_RSF_FACTORS.items():
            assert 0 <= data["rsf_factor_pct"] <= 100


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — FATF Country Risk
# ═══════════════════════════════════════════════════════════════════════════

class TestFATFCountryRisk:
    """Verify FATF country risk ratings."""

    def test_country_count(self):
        assert len(FATF_COUNTRY_RISK_RATINGS) >= 25

    def test_rating_structure(self):
        for country, data in FATF_COUNTRY_RISK_RATINGS.items():
            assert "tc_rating" in data
            assert "effectiveness_rating" in data
            assert "risk_tier" in data

    def test_risk_tiers_valid(self):
        valid_tiers = {1, 2, 3, 4}
        for country, data in FATF_COUNTRY_RISK_RATINGS.items():
            assert data["risk_tier"] in valid_tiers

    def test_get_fatf_rating_valid(self):
        rating = get_fatf_rating("GB")
        assert rating is not None
        assert rating["risk_tier"] == 1

    def test_get_fatf_rating_invalid(self):
        rating = get_fatf_rating("ZZZ")
        assert rating is None


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — FAO Crop Yields
# ═══════════════════════════════════════════════════════════════════════════

class TestFAOCropYields:
    """Verify FAO crop yield data."""

    def test_country_count(self):
        assert len(FAO_CROP_YIELD_DATABASE) >= 8

    def test_crop_types(self):
        for country, crops in FAO_CROP_YIELD_DATABASE.items():
            assert len(crops) >= 4

    def test_yield_values_non_negative(self):
        for country, crops in FAO_CROP_YIELD_DATABASE.items():
            for crop, data in crops.items():
                assert data["yield_index_100"] >= 0

    def test_get_crop_yield_valid(self):
        y = get_crop_yield("US", "wheat")
        assert y is not None
        assert y["yield_index_100"] > 0

    def test_get_crop_yield_invalid(self):
        y = get_crop_yield("ZZZ", "wheat")
        assert y is None


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — EUDR Commodity Criteria
# ═══════════════════════════════════════════════════════════════════════════

class TestEUDRCommodityCriteria:
    """Verify EUDR country benchmarks and commodity definitions."""

    def test_country_benchmark_count(self):
        assert len(EUDR_COUNTRY_BENCHMARKS) >= 35

    def test_commodity_definitions_count(self):
        assert len(EUDR_COMMODITY_DEFINITIONS) >= 7

    def test_risk_tiers_valid(self):
        valid = {"low", "standard", "high"}
        for country, data in EUDR_COUNTRY_BENCHMARKS.items():
            assert data["risk_tier"] in valid

    def test_commodities_have_hs_codes(self):
        for commodity, data in EUDR_COMMODITY_DEFINITIONS.items():
            assert "hs_codes" in data
            assert len(data["hs_codes"]) > 0

    def test_get_eudr_country_risk_valid(self):
        risk = get_eudr_country_risk("BR")
        assert risk is not None
        assert risk["risk_tier"] == "standard"

    def test_get_eudr_country_risk_invalid(self):
        risk = get_eudr_country_risk("ZZZ")
        assert risk is None


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA — BNG Statutory Metric
# ═══════════════════════════════════════════════════════════════════════════

class TestBNGStatutoryMetric:
    """Verify BNG habitat distinctiveness and calculation components."""

    def test_habitat_count(self):
        assert len(BNG_HABITAT_DISTINCTIVENESS) >= 24

    def test_condition_multipliers(self):
        assert len(BNG_CONDITION_MULTIPLIERS) >= 6
        for cond, mult in BNG_CONDITION_MULTIPLIERS.items():
            assert 0 <= mult <= 3.0

    def test_strategic_significance(self):
        assert len(BNG_STRATEGIC_SIGNIFICANCE) >= 3

    def test_trading_rules(self):
        assert len(BNG_TRADING_RULES) >= 5

    def test_distinctiveness_scores_valid(self):
        for hab, data in BNG_HABITAT_DISTINCTIVENESS.items():
            assert data["distinctiveness"] in ("v_low", "low", "medium", "high", "v_high")
            assert 0 <= data["score"] <= 10

    def test_get_habitat_distinctiveness_valid(self):
        d = get_habitat_distinctiveness("lowland_meadow")
        assert d is not None
        assert d["score"] > 0

    def test_calculate_habitat_units_basic(self):
        units = calculate_habitat_units(
            habitat_type="lowland_meadow",
            area_ha=2.0,
            condition="good",
            strategic_significance="high_strategic_significance",
        )
        assert units > 0

    def test_calculate_habitat_units_unknown_habitat(self):
        units = calculate_habitat_units(
            habitat_type="unknown",
            area_ha=1.0,
            condition="good",
            strategic_significance="low_strategic_significance",
        )
        assert units == 0.0


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Construction
# ═══════════════════════════════════════════════════════════════════════════

class TestInsuranceRiskEngineInit:
    """Test engine initialisation."""

    def test_engine_creates(self):
        engine = InsuranceRiskEngine()
        assert engine is not None

    def test_available_countries(self):
        engine = InsuranceRiskEngine()
        countries = engine.get_available_countries()
        assert len(countries) >= 10
        assert "GBR" in countries

    def test_available_perils(self):
        engine = InsuranceRiskEngine()
        perils = engine.get_available_perils()
        assert "tropical_cyclone" in perils
        assert "river_flood" in perils

    def test_solvency2_countries(self):
        engine = InsuranceRiskEngine()
        countries = engine.get_solvency2_countries()
        assert "DE" in countries
        assert "FR" in countries

    def test_climate_adjustments(self):
        engine = InsuranceRiskEngine()
        adj = engine.get_climate_adjustments()
        assert len(adj) >= 3


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Mortality Assessment
# ═══════════════════════════════════════════════════════════════════════════

class TestMortalityAssessment:
    """Test climate-adjusted mortality risk assessment."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_basic_mortality(self):
        result = self.engine.assess_mortality("GBR", "male", 1.5)
        assert result.country == "GBR"
        assert result.sex == "male"
        assert result.warming_c == 1.5
        assert len(result.base_mortality) > 0
        assert len(result.adjusted_mortality) > 0

    def test_climate_increases_mortality(self):
        result = self.engine.assess_mortality("GBR", "male", 2.0)
        assert result.reserve_impact_pct > 0  # Warming increases mortality

    def test_life_expectancy_delta_with_warming(self):
        result = self.engine.assess_mortality("GBR", "female", 3.0)
        # Warming should produce a non-zero life expectancy delta
        assert result.life_expectancy_delta_years != 0

    def test_mortality_unknown_country_falls_back(self):
        # Engine falls back to GBR for unknown countries, does not raise
        result = self.engine.assess_mortality("ZZZ", "male", 1.5)
        assert result.country == "ZZZ"
        assert len(result.base_mortality) > 0  # Falls back to GBR data

    def test_climate_drivers_present(self):
        result = self.engine.assess_mortality("USA", "male", 2.0)
        assert len(result.climate_drivers) > 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Liability Valuation
# ═══════════════════════════════════════════════════════════════════════════

class TestLiabilityValuation:
    """Test life liability valuation under climate stress."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_basic_valuation(self):
        result = self.engine.value_liabilities(
            total_lives=100_000,
            avg_sum_assured_eur=150_000,
        )
        assert result.total_lives == 100_000
        assert result.liability_pv_base_eur > 0
        assert result.liability_pv_stressed_eur > 0

    def test_longevity_shock_impact_positive(self):
        result = self.engine.value_liabilities(
            total_lives=50_000,
            avg_sum_assured_eur=200_000,
        )
        assert result.longevity_shock_impact_eur != 0

    def test_solvency_ratios_positive(self):
        result = self.engine.value_liabilities(
            total_lives=10_000,
            avg_sum_assured_eur=100_000,
        )
        assert result.solvency_ratio_base > 0
        assert result.solvency_ratio_stressed > 0

    def test_total_sum_assured_computed(self):
        result = self.engine.value_liabilities(
            total_lives=100_000,
            avg_sum_assured_eur=150_000,
            avg_remaining_term_years=20,
        )
        assert result.total_sum_assured_eur == 100_000 * 150_000


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Nat-Cat Exposure
# ═══════════════════════════════════════════════════════════════════════════

class TestNatCatExposure:
    """Test Solvency II nat-cat exposure assessment."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_basic_natcat(self):
        result = self.engine.assess_natcat_exposure(
            country="DE",
            exposure_eur=5_000_000_000,
            perils=["windstorm", "flood"],
            warming_c=1.5,
        )
        assert result.country == "DE"
        assert result.total_exposure_eur == 5_000_000_000
        assert result.solvency2_nat_cat_scr_eur > 0
        assert result.pml_100yr_eur > 0

    def test_diversification_benefit(self):
        result = self.engine.assess_natcat_exposure(
            country="DE",
            exposure_eur=5_000_000_000,
            perils=["windstorm", "flood", "hail"],
            warming_c=1.5,
        )
        assert result.diversification_benefit_pct > 0

    def test_concentration_risk_populated(self):
        result = self.engine.assess_natcat_exposure(
            country="FR",
            exposure_eur=1_000_000_000,
            perils=["windstorm", "flood"],
            warming_c=2.0,
        )
        assert len(result.concentration_risk) > 0

    def test_expected_annual_loss_positive(self):
        result = self.engine.assess_natcat_exposure(
            country="IT",
            exposure_eur=2_000_000_000,
            perils=["earthquake"],
            warming_c=1.5,
        )
        assert result.expected_annual_loss_eur > 0

    def test_natcat_unknown_country_falls_back(self):
        # Engine falls back to DE for unknown countries, does not raise
        result = self.engine.assess_natcat_exposure(
            country="ZZ",
            exposure_eur=1_000_000_000,
            perils=["windstorm"],
        )
        assert result.solvency2_nat_cat_scr_eur > 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Climate Frequency
# ═══════════════════════════════════════════════════════════════════════════

class TestClimateFrequency:
    """Test IPCC AR6 climate-driven frequency/severity projection."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_basic_frequency(self):
        result = self.engine.assess_climate_frequency(
            hazard_types=["tropical_cyclone", "river_flood"],
            warming_scenario_c=2.0,
        )
        assert result.warming_scenario_c == 2.0
        assert len(result.loss_freq_stressed) > 0

    def test_frequency_multiplier_above_one(self):
        result = self.engine.assess_climate_frequency(
            hazard_types=["wildfire"],
            warming_scenario_c=3.0,
        )
        # Wildfire freq mult > 1 at 3C
        assert result.loss_freq_stressed["wildfire"] > result.loss_freq_base["wildfire"]

    def test_severity_multiplier_above_one(self):
        result = self.engine.assess_climate_frequency(
            hazard_types=["heatwave"],
            warming_scenario_c=2.5,
        )
        assert result.severity_multiplier["heatwave"] > 1.0

    def test_unknown_hazard_skipped(self):
        # Engine skips unknown hazards (doesn't raise)
        result = self.engine.assess_climate_frequency(
            hazard_types=["nonexistent"],
            warming_scenario_c=2.0,
        )
        assert len(result.loss_freq_stressed) == 0
        assert len(result.damage_functions_used) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Underwriting
# ═══════════════════════════════════════════════════════════════════════════

class TestUnderwriting:
    """Test underwriting risk assessment with climate overlay."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_basic_underwriting(self):
        result = self.engine.assess_underwriting(
            gwp_eur=2_000_000_000,
            net_earned_premium_eur=1_800_000_000,
            claims_incurred_eur=1_200_000_000,
            expense_ratio_pct=30.0,
        )
        assert result.gross_written_premium_eur == 2_000_000_000
        assert result.loss_ratio_pct > 0
        assert result.expense_ratio_pct == 30.0
        assert result.combined_ratio_pct > 0

    def test_climate_increases_combined_ratio(self):
        result = self.engine.assess_underwriting(
            gwp_eur=1_000_000_000,
            net_earned_premium_eur=900_000_000,
            claims_incurred_eur=600_000_000,
            expense_ratio_pct=30.0,
            warming_c=2.0,
        )
        assert result.climate_adjusted_combined_ratio_pct >= result.combined_ratio_pct

    def test_risk_margin_calculated(self):
        result = self.engine.assess_underwriting(
            gwp_eur=1_000_000_000,
            net_earned_premium_eur=900_000_000,
            claims_incurred_eur=400_000_000,
            expense_ratio_pct=25.0,
        )
        assert result.risk_margin_eur > 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Retrocession
# ═══════════════════════════════════════════════════════════════════════════

class TestRetrocession:
    """Test reinsurance retrocession chain assessment."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_basic_retrocession(self):
        result = self.engine.assess_retrocession(
            gross_exposure_eur=10_000_000_000,
            ceded_premium_eur=500_000_000,
        )
        assert result.gross_exposure_eur == 10_000_000_000
        assert result.net_retention_eur >= 0

    def test_retrocession_with_custom_layers(self):
        layers = [
            {"name": "QS_50", "attachment_eur": 0, "limit_eur": 5_000_000_000},
            {"name": "XL_1", "attachment_eur": 1_000_000_000, "limit_eur": 2_000_000_000},
        ]
        result = self.engine.assess_retrocession(
            gross_exposure_eur=10_000_000_000,
            ceded_premium_eur=800_000_000,
            layers=layers,
        )
        assert len(result.layers) == 2

    def test_cascade_failure_prob(self):
        result = self.engine.assess_retrocession(
            gross_exposure_eur=5_000_000_000,
            ceded_premium_eur=300_000_000,
        )
        assert result.cascade_failure_prob_pct >= 0

    def test_counterparty_credit_risk(self):
        result = self.engine.assess_retrocession(
            gross_exposure_eur=5_000_000_000,
            ceded_premium_eur=300_000_000,
        )
        assert result.counterparty_credit_risk_eur >= 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Medical Trend
# ═══════════════════════════════════════════════════════════════════════════

class TestMedicalTrend:
    """Test medical cost trend projection with climate overlay."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_basic_medical_trend(self):
        result = self.engine.assess_medical_trend(
            claim_cost_per_member_eur=3_500,
            member_count=50_000,
        )
        assert result.claim_cost_per_member_eur == 3_500
        assert result.projected_claim_cost_1yr_eur > 3_500  # Trend > 0

    def test_climate_adds_to_trend(self):
        result = self.engine.assess_medical_trend(
            claim_cost_per_member_eur=3_000,
            member_count=10_000,
            warming_c=2.0,
        )
        assert result.climate_health_overlay_pct > 0
        total_trend = result.medical_cpi_trend_pct + result.climate_health_overlay_pct
        assert total_trend > result.medical_cpi_trend_pct

    def test_pandemic_scenario_increases_cost(self):
        result_no = self.engine.assess_medical_trend(
            claim_cost_per_member_eur=5_000,
            member_count=100_000,
            pandemic_scenario=False,
        )
        result_yes = self.engine.assess_medical_trend(
            claim_cost_per_member_eur=5_000,
            member_count=100_000,
            pandemic_scenario=True,
        )
        assert result_yes.projected_claim_cost_1yr_eur > result_no.projected_claim_cost_1yr_eur
        assert result_yes.pandemic_surge_pct > 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSURANCE RISK ENGINE — Comprehensive Assessment
# ═══════════════════════════════════════════════════════════════════════════

class TestComprehensiveAssessment:
    """Test full insurance risk assessment across all sub-modules."""

    def setup_method(self):
        self.engine = InsuranceRiskEngine()

    def test_comprehensive_returns_all_sub_modules(self):
        result = self.engine.comprehensive_assessment(
            entity_name="Test Insurer",
            country="GBR",
            warming_c=1.5,
        )
        assert result.entity_name == "Test Insurer"
        assert result.life_mortality is not None
        assert result.life_liability is not None
        assert result.underwriting is not None
        assert result.medical_trend is not None

    def test_comprehensive_solvency_ratio(self):
        result = self.engine.comprehensive_assessment(
            entity_name="Test Insurer",
            country="GBR",
            warming_c=2.0,
        )
        assert result.overall_solvency_ratio > 0

    def test_comprehensive_scr_positive(self):
        result = self.engine.comprehensive_assessment(
            entity_name="Test Insurer",
            country="USA",
            warming_c=1.5,
        )
        assert result.total_scr_eur > 0

    def test_comprehensive_capital_computed(self):
        result = self.engine.comprehensive_assessment(
            entity_name="Test Insurer",
            country="GBR",
            warming_c=2.0,
            exposure_eur=5_000_000_000,
            own_funds_eur=800_000_000,
        )
        assert result.capital_surplus_eur is not None

    def test_comprehensive_recommendations(self):
        result = self.engine.comprehensive_assessment(
            entity_name="Test Insurer",
            country="GBR",
            warming_c=3.0,
        )
        assert len(result.recommendations) > 0

    def test_comprehensive_natcat_included(self):
        result = self.engine.comprehensive_assessment(
            entity_name="Test Insurer",
            country="GBR",
        )
        assert result.natcat_exposure is not None


# ═══════════════════════════════════════════════════════════════════════════
#  API Routes — Insurance Risk
# ═══════════════════════════════════════════════════════════════════════════

class TestInsuranceRiskRoutes:
    """Test insurance risk API route imports and endpoint existence."""

    def test_route_module_imports(self):
        from api.v1.routes.insurance_risk import router
        assert router is not None
        assert router.prefix == "/api/v1/insurance-risk"

    def test_mortality_endpoint_exists(self):
        from api.v1.routes.insurance_risk import assess_mortality
        assert callable(assess_mortality)

    def test_liability_endpoint_exists(self):
        from api.v1.routes.insurance_risk import value_liabilities
        assert callable(value_liabilities)

    def test_natcat_endpoint_exists(self):
        from api.v1.routes.insurance_risk import assess_natcat
        assert callable(assess_natcat)

    def test_climate_frequency_endpoint_exists(self):
        from api.v1.routes.insurance_risk import assess_climate_frequency
        assert callable(assess_climate_frequency)

    def test_underwriting_endpoint_exists(self):
        from api.v1.routes.insurance_risk import assess_underwriting
        assert callable(assess_underwriting)

    def test_retrocession_endpoint_exists(self):
        from api.v1.routes.insurance_risk import assess_retrocession
        assert callable(assess_retrocession)

    def test_medical_trend_endpoint_exists(self):
        from api.v1.routes.insurance_risk import assess_medical_trend
        assert callable(assess_medical_trend)

    def test_comprehensive_endpoint_exists(self):
        from api.v1.routes.insurance_risk import comprehensive_assessment
        assert callable(comprehensive_assessment)

    def test_available_countries_endpoint_exists(self):
        from api.v1.routes.insurance_risk import available_countries
        assert callable(available_countries)


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE INTEGRATION — Insurance Module
# ═══════════════════════════════════════════════════════════════════════════

class TestInsuranceLineageIntegration:
    """Verify insurance module is properly wired into data lineage."""

    def test_insurance_signature_exists(self):
        from services.data_lineage_service import MODULE_SIGNATURES
        assert "insurance_risk_engine" in MODULE_SIGNATURES

    def test_insurance_signature_complete(self):
        from services.data_lineage_service import MODULE_SIGNATURES
        sig = MODULE_SIGNATURES["insurance_risk_engine"]
        assert sig["category"] == "insurance"
        assert len(sig["inputs"]) >= 10
        assert len(sig["outputs"]) >= 10
        assert "who_mortality_tables" in sig["reference_data"]
        assert "ipcc_ar6_damage_functions" in sig["reference_data"]
        assert "solvency2_nat_cat_factors" in sig["reference_data"]

    def test_insurance_dependency_edges_exist(self):
        from services.data_lineage_service import MODULE_DEPENDENCIES
        ins_edges = [d for d in MODULE_DEPENDENCIES
                     if d["source"] == "insurance_risk_engine"
                     or d["target"] == "insurance_risk_engine"]
        assert len(ins_edges) >= 2  # At least → entity360 and → csrd

    def test_insurance_feeds_entity360(self):
        from services.data_lineage_service import MODULE_DEPENDENCIES
        e360_edges = [d for d in MODULE_DEPENDENCIES
                      if d["source"] == "insurance_risk_engine"
                      and d["target"] == "entity360"]
        assert len(e360_edges) >= 1

    def test_reference_datasets_all_embedded(self):
        from services.reference_data_catalog import REFERENCE_DATASETS
        previously_missing = [
            "who_mortality_tables", "ipcc_ar6_damage_functions",
            "solvency2_nat_cat_factors", "basel3_nsfr_lcr_factors",
            "fatf_country_risk_ratings", "fao_crop_yield_database",
            "eudr_commodity_criteria", "bng_metric_4",
        ]
        for ds_id in previously_missing:
            ds = REFERENCE_DATASETS[ds_id]
            assert ds["status"] == "embedded", f"{ds_id} should be embedded, got {ds['status']}"
            assert ds["record_count"] > 0, f"{ds_id} should have record_count > 0"
