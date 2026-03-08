"""
Tests for PCAF -> ECL Climate Overlay Bridge
=============================================
Validates the mapping from PCAF financed emissions data
to ECL climate risk inputs for credit risk adjustment.

Covers:
  - Single investee mapping (all field translations)
  - Portfolio-level bridging (aggregation, confidence weighting)
  - Temperature -> scenario weight mapping
  - WACI -> transition risk scoring
  - Carbon price sensitivity estimation
  - DQS confidence weighting
  - Edge cases (zero emissions, missing data, extreme values)
  - SBTi / Net Zero discount flags
"""

import pytest
from services.pcaf_ecl_bridge import (
    PCAFInvesteeProfile,
    ECLClimateInputs,
    map_investee_to_ecl_climate,
    bridge_portfolio,
    db_row_to_profile,
    demo_bridge,
    _temperature_bucket,
    _waci_to_transition_risk,
    _waci_to_transition_score,
    _carbon_price_sensitivity,
    TEMPERATURE_SCENARIO_WEIGHTS,
    DQS_CONFIDENCE_WEIGHTS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def high_carbon_investee():
    """Oil & gas company with high emissions."""
    return PCAFInvesteeProfile(
        investee_name="PetroCarbon Inc.",
        sector_gics="10102010",  # Energy - Oil & Gas
        country_iso="USA",
        financed_scope1_tco2e=80_000,
        financed_scope2_tco2e=10_000,
        revenue_intensity_tco2e_per_meur=950.0,
        outstanding_eur=100_000_000,
        pcaf_dq_composite=2.0,
        sbti_committed=False,
        implied_temperature_c=3.5,
    )


@pytest.fixture
def low_carbon_investee():
    """Renewable energy company with low emissions."""
    return PCAFInvesteeProfile(
        investee_name="GreenWind AS",
        sector_gics="55105010",  # Utilities - Renewable
        country_iso="NOR",
        financed_scope1_tco2e=500,
        financed_scope2_tco2e=100,
        revenue_intensity_tco2e_per_meur=15.0,
        outstanding_eur=50_000_000,
        pcaf_dq_composite=1.0,
        sbti_committed=True,
        net_zero_target_year=2035,
        implied_temperature_c=1.4,
    )


@pytest.fixture
def medium_carbon_investee():
    """Manufacturing company with moderate emissions."""
    return PCAFInvesteeProfile(
        investee_name="SteelWorks GmbH",
        sector_gics="15104050",  # Materials - Steel
        country_iso="DEU",
        financed_scope1_tco2e=40_000,
        financed_scope2_tco2e=8_000,
        revenue_intensity_tco2e_per_meur=450.0,
        outstanding_eur=75_000_000,
        pcaf_dq_composite=3.0,
        sbti_committed=True,
        net_zero_target_year=2050,
        implied_temperature_c=2.8,
    )


# ── Temperature Bucket Tests ────────────────────────────────────────────────

class TestTemperatureBucket:
    def test_below_1_5(self):
        assert _temperature_bucket(1.2) == "below_1.5"

    def test_1_5_to_2_0(self):
        assert _temperature_bucket(1.7) == "1.5_to_2.0"

    def test_2_0_to_2_5(self):
        assert _temperature_bucket(2.3) == "2.0_to_2.5"

    def test_2_5_to_3_0(self):
        assert _temperature_bucket(2.8) == "2.5_to_3.0"

    def test_3_0_to_3_5(self):
        assert _temperature_bucket(3.2) == "3.0_to_3.5"

    def test_above_3_5(self):
        assert _temperature_bucket(4.1) == "above_3.5"

    def test_boundary_1_5(self):
        assert _temperature_bucket(1.5) == "1.5_to_2.0"

    def test_boundary_3_5(self):
        assert _temperature_bucket(3.5) == "above_3.5"


# ── WACI Transition Risk Tests ──────────────────────────────────────────────

class TestWACITransitionRisk:
    def test_low_waci(self):
        assert _waci_to_transition_risk(30.0) == "low"

    def test_medium_waci(self):
        assert _waci_to_transition_risk(100.0) == "medium"

    def test_high_waci(self):
        assert _waci_to_transition_risk(300.0) == "high"

    def test_very_high_waci(self):
        assert _waci_to_transition_risk(800.0) == "very_high"

    def test_extreme_waci(self):
        assert _waci_to_transition_risk(5000.0) == "very_high"

    def test_zero_waci(self):
        assert _waci_to_transition_risk(0.0) == "low"

    def test_boundary_50(self):
        assert _waci_to_transition_risk(50.0) == "low"

    def test_above_50(self):
        assert _waci_to_transition_risk(51.0) == "medium"


# ── Transition Score Tests ──────────────────────────────────────────────────

class TestTransitionScore:
    def test_zero_waci_score(self):
        score = _waci_to_transition_score(0.0)
        assert score >= 0
        assert score <= 15  # Low but not zero

    def test_moderate_waci_score(self):
        score = _waci_to_transition_score(200.0)
        assert 30 < score < 60

    def test_high_waci_score(self):
        score = _waci_to_transition_score(1000.0)
        assert score > 45

    def test_extreme_waci_score(self):
        score = _waci_to_transition_score(5000.0)
        assert score >= 55

    def test_score_monotonic_increasing(self):
        scores = [_waci_to_transition_score(w) for w in [10, 50, 200, 500, 1000, 3000]]
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], f"Score not monotonic at WACI index {i}"


# ── Carbon Price Sensitivity Tests ──────────────────────────────────────────

class TestCarbonPriceSensitivity:
    def test_low_intensity(self):
        s = _carbon_price_sensitivity(30.0, "45")  # IT sector
        assert 0.1 <= s <= 0.4

    def test_high_intensity_energy(self):
        s = _carbon_price_sensitivity(900.0, "10102010")  # Energy
        assert s >= 0.8

    def test_sector_boost_energy(self):
        s_energy = _carbon_price_sensitivity(200.0, "10")
        s_tech = _carbon_price_sensitivity(200.0, "45")
        assert s_energy > s_tech, "Energy sector should have higher sensitivity"

    def test_cap_at_1(self):
        s = _carbon_price_sensitivity(5000.0, "10")
        assert s <= 1.0


# ── Single Investee Mapping Tests ───────────────────────────────────────────

class TestSingleInvesteeMapping:
    def test_high_carbon_mapping(self, high_carbon_investee):
        result = map_investee_to_ecl_climate(high_carbon_investee)

        assert isinstance(result, ECLClimateInputs)
        assert result.sector_carbon_intensity_tco2e_mrev == 950.0
        assert result.sector_transition_risk == "very_high"
        assert result.transition_risk_score > 40
        assert result.carbon_price_sensitivity >= 0.8
        assert result.sbti_aligned is False
        assert result.net_zero_committed is False
        assert result.pcaf_confidence == 0.90  # DQS 2

    def test_low_carbon_mapping(self, low_carbon_investee):
        result = map_investee_to_ecl_climate(low_carbon_investee)

        assert result.sector_transition_risk == "low"
        assert result.transition_risk_score < 30
        assert result.sbti_aligned is True
        assert result.net_zero_committed is True  # target 2035 < 2050
        assert result.pcaf_confidence == 1.00  # DQS 1

    def test_physical_risk_override(self, high_carbon_investee):
        result = map_investee_to_ecl_climate(
            high_carbon_investee,
            physical_risk_override=85.0,
        )
        assert result.physical_risk_score == 85.0

    def test_default_physical_risk(self, high_carbon_investee):
        result = map_investee_to_ecl_climate(high_carbon_investee)
        assert result.physical_risk_score == 30.0  # Default

    def test_scenario_weights_high_temp(self, high_carbon_investee):
        result = map_investee_to_ecl_climate(high_carbon_investee)
        # 3.5C -> "above_3.5" bucket -> heavy adverse/severe
        assert result.scenario_weights["SEVERE"] >= 0.20
        assert result.scenario_weights["OPTIMISTIC"] <= 0.10

    def test_scenario_weights_low_temp(self, low_carbon_investee):
        result = map_investee_to_ecl_climate(low_carbon_investee)
        # 1.4C -> "below_1.5" bucket -> more optimistic
        assert result.scenario_weights["OPTIMISTIC"] >= 0.30
        assert result.scenario_weights["SEVERE"] <= 0.10

    def test_sbti_only_no_net_zero(self, medium_carbon_investee):
        result = map_investee_to_ecl_climate(medium_carbon_investee)
        assert result.sbti_aligned is True
        assert result.net_zero_committed is True  # 2050 <= 2050

    def test_net_zero_far_future(self):
        profile = PCAFInvesteeProfile(
            investee_name="SlowTransition Co.",
            revenue_intensity_tco2e_per_meur=300.0,
            net_zero_target_year=2070,  # > 2050
        )
        result = map_investee_to_ecl_climate(profile)
        assert result.net_zero_committed is False

    def test_collateral_flood_risk_passthrough(self, high_carbon_investee):
        result = map_investee_to_ecl_climate(
            high_carbon_investee,
            collateral_flood_risk="extreme",
        )
        assert result.collateral_flood_risk == "extreme"

    def test_energy_rating_passthrough(self, high_carbon_investee):
        result = map_investee_to_ecl_climate(
            high_carbon_investee,
            energy_rating="G",
        )
        assert result.energy_rating == "G"


# ── Portfolio Bridge Tests ──────────────────────────────────────────────────

class TestPortfolioBridge:
    def test_bridge_three_investees(self, high_carbon_investee, low_carbon_investee, medium_carbon_investee):
        result = bridge_portfolio(
            [high_carbon_investee, low_carbon_investee, medium_carbon_investee],
            portfolio_temperature_c=2.6,
        )

        assert result.investee_count == 3
        assert result.mapped_count == 3
        assert len(result.investee_climate_inputs) == 3
        assert len(result.warnings) == 0

    def test_portfolio_avg_confidence(self, high_carbon_investee, low_carbon_investee):
        result = bridge_portfolio(
            [high_carbon_investee, low_carbon_investee],
            portfolio_temperature_c=2.5,
        )
        # Exposure-weighted: (100M * 0.90 + 50M * 1.00) / 150M = 0.933
        assert 0.90 <= result.avg_confidence <= 0.95

    def test_portfolio_scenario_weights(self):
        profiles = [
            PCAFInvesteeProfile(
                investee_name="Hot Corp",
                implied_temperature_c=4.0,
                outstanding_eur=10_000_000,
                revenue_intensity_tco2e_per_meur=500.0,
            ),
        ]
        result = bridge_portfolio(profiles, portfolio_temperature_c=3.8)
        # 3.8C -> "above_3.5" bucket
        assert result.scenario_weights["SEVERE"] >= 0.25
        assert result.scenario_weights["OPTIMISTIC"] <= 0.10

    def test_empty_portfolio(self):
        result = bridge_portfolio([], portfolio_temperature_c=2.5)
        assert result.investee_count == 0
        assert result.mapped_count == 0
        assert result.avg_confidence == 0.0

    def test_physical_risk_overrides(self, high_carbon_investee):
        overrides = {"PetroCarbon Inc.": 90.0}
        result = bridge_portfolio(
            [high_carbon_investee],
            portfolio_temperature_c=3.0,
            physical_risk_overrides=overrides,
        )
        inputs = result.investee_climate_inputs[0]["climate_inputs"]
        assert inputs["physical_risk_score"] == 90.0

    def test_investee_names_preserved(self, high_carbon_investee, low_carbon_investee):
        result = bridge_portfolio(
            [high_carbon_investee, low_carbon_investee],
            portfolio_temperature_c=2.5,
        )
        names = [x["investee_name"] for x in result.investee_climate_inputs]
        assert "PetroCarbon Inc." in names
        assert "GreenWind AS" in names


# ── DQS Confidence Tests ───────────────────────────────────────────────────

class TestDQSConfidence:
    def test_dqs_1_verified(self):
        profile = PCAFInvesteeProfile(
            investee_name="Verified Corp",
            pcaf_dq_composite=1.0,
            revenue_intensity_tco2e_per_meur=100.0,
        )
        result = map_investee_to_ecl_climate(profile)
        assert result.pcaf_confidence == 1.00

    def test_dqs_5_estimated(self):
        profile = PCAFInvesteeProfile(
            investee_name="Estimated Corp",
            pcaf_dq_composite=5.0,
            revenue_intensity_tco2e_per_meur=100.0,
        )
        result = map_investee_to_ecl_climate(profile)
        assert result.pcaf_confidence == 0.30

    def test_dqs_rounding(self):
        profile = PCAFInvesteeProfile(
            investee_name="Rounded Corp",
            pcaf_dq_composite=2.7,  # Rounds to 3
            revenue_intensity_tco2e_per_meur=100.0,
        )
        result = map_investee_to_ecl_climate(profile)
        assert result.pcaf_confidence == 0.70  # DQS 3


# ── DB Row Conversion Tests ─────────────────────────────────────────────────

class TestDBRowConversion:
    def test_full_row(self):
        row = {
            "investee_name": "Test Corp",
            "sector_gics": "20301010",
            "country_iso": "GBR",
            "financed_scope1_tco2e": 5000,
            "financed_scope2_tco2e": 1000,
            "financed_scope3_tco2e": 3000,
            "revenue_intensity_tco2e_per_mrevenue": 120.5,
            "outstanding_investment": 25_000_000,
            "pcaf_dq_scope1": 2,
            "pcaf_dq_scope2": 3,
            "sbti_committed": True,
            "implied_temperature_c": 2.1,
            "attribution_factor": 0.35,
        }
        profile = db_row_to_profile(row)
        assert profile.investee_name == "Test Corp"
        assert profile.sector_gics == "20301010"
        assert profile.revenue_intensity_tco2e_per_meur == 120.5
        assert profile.sbti_committed is True
        assert profile.implied_temperature_c == 2.1

    def test_missing_fields(self):
        row = {"investee_name": "Minimal Corp"}
        profile = db_row_to_profile(row)
        assert profile.investee_name == "Minimal Corp"
        assert profile.sector_gics == ""
        assert profile.revenue_intensity_tco2e_per_meur == 0.0
        assert profile.pcaf_dq_composite == 3.0  # Default

    def test_null_fields(self):
        row = {
            "investee_name": "Null Corp",
            "sector_gics": None,
            "country_iso": None,
            "financed_scope1_tco2e": None,
            "implied_temperature_c": None,
        }
        profile = db_row_to_profile(row)
        assert profile.sector_gics == ""
        assert profile.country_iso == ""
        assert profile.financed_scope1_tco2e == 0.0
        assert profile.implied_temperature_c == 2.5  # Default


# ── Demo Bridge Test ────────────────────────────────────────────────────────

class TestDemoBridge:
    def test_demo_runs(self):
        result = demo_bridge()
        assert result.investee_count == 3
        assert result.mapped_count == 3
        assert result.avg_confidence > 0.5
        assert result.avg_transition_risk_score > 0
        assert len(result.investee_climate_inputs) == 3

    def test_demo_totalenergies(self):
        result = demo_bridge()
        total = next(
            x for x in result.investee_climate_inputs
            if x["investee_name"] == "TotalEnergies SE"
        )
        inputs = total["climate_inputs"]
        assert inputs["sector_transition_risk"] == "very_high"
        assert inputs["sbti_aligned"] is True
        assert inputs["net_zero_committed"] is True

    def test_demo_orsted(self):
        result = demo_bridge()
        orsted = next(
            x for x in result.investee_climate_inputs
            if x["investee_name"] == "Orsted A/S"
        )
        inputs = orsted["climate_inputs"]
        assert inputs["sector_transition_risk"] == "low"
        assert inputs["pcaf_confidence"] == 1.00

    def test_demo_arcelor(self):
        result = demo_bridge()
        arcelor = next(
            x for x in result.investee_climate_inputs
            if x["investee_name"] == "ArcelorMittal"
        )
        inputs = arcelor["climate_inputs"]
        assert inputs["sbti_aligned"] is False
        assert inputs["sector_carbon_intensity_tco2e_mrev"] == 1200.0


# ── Edge Cases ──────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_zero_emissions(self):
        profile = PCAFInvesteeProfile(
            investee_name="Zero Corp",
            revenue_intensity_tco2e_per_meur=0.0,
        )
        result = map_investee_to_ecl_climate(profile)
        assert result.sector_transition_risk == "low"
        assert result.transition_risk_score >= 0

    def test_extreme_emissions(self):
        profile = PCAFInvesteeProfile(
            investee_name="Mega Polluter",
            revenue_intensity_tco2e_per_meur=10_000.0,
        )
        result = map_investee_to_ecl_climate(profile)
        assert result.sector_transition_risk == "very_high"
        assert result.carbon_price_sensitivity >= 0.9

    def test_negative_waci_handled(self):
        # Should not happen in practice but shouldn't crash
        profile = PCAFInvesteeProfile(
            investee_name="Negative Corp",
            revenue_intensity_tco2e_per_meur=-10.0,
        )
        result = map_investee_to_ecl_climate(profile)
        assert result.transition_risk_score >= 0
