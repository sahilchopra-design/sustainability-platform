"""
Tests for Climate Transition Risk Engine
============================================
52 tests covering:
  - NGFS Phase 5 scenario reference data (6 scenarios)
  - IEA NZE Pathway reference data (12 sectors)
  - TransitionRiskConfig validation and defaults
  - Stage 1: Sector Classification (NACE -> CPRS -> IAM)
  - Stage 2: Carbon Pricing & CBAM Impact
  - Stage 3: Stranded Asset Assessment (4 writedown curves)
  - Stage 4: Portfolio Alignment & Transition Readiness
  - Stage 5: NGFS Scenario Stress Testing
  - Stage 6: Composite Transition Risk Score
  - Full entity assessment pipeline
  - Portfolio assessment
"""
import sys, os, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.climate_transition_risk_engine import (
    NGFS_PHASE5_SCENARIOS,
    IEA_NZE_PATHWAY,
    TCFD_CATEGORY_DESCRIPTIONS,
    CBAM_COVERED_SECTORS,
    WRITEDOWN_CURVE_FUNCTIONS,
    TransitionRiskConfig,
    SectorClassificationResult,
    CarbonPricingResult,
    StrandedAssetResult,
    AlignmentResult,
    ScenarioStressResult,
    TransitionRiskResult,
    TransitionRiskEngine,
)
from services.nace_cprs_mapper import NACECPRSMapper


# ── Helpers ────────────────────────────────────────────────────────────

def _engine(**config_kw):
    """Return a TransitionRiskEngine with optional config overrides."""
    cfg = TransitionRiskConfig(**config_kw)
    return TransitionRiskEngine(config=cfg)


def _default_engine():
    return TransitionRiskEngine()


def _fossil_nace():
    """NACE activities for a fossil-fuel entity (coal mining + refining)."""
    return [
        {"nace_code": "05", "revenue_share": 0.60, "ghg_intensity_tco2e_per_eur_m": 1200.0},
        {"nace_code": "19.20", "revenue_share": 0.40, "ghg_intensity_tco2e_per_eur_m": 900.0},
    ]


def _ict_nace():
    """NACE activities for a low-risk ICT entity."""
    return [
        {"nace_code": "62", "revenue_share": 0.80, "ghg_intensity_tco2e_per_eur_m": 5.0},
        {"nace_code": "63", "revenue_share": 0.20, "ghg_intensity_tco2e_per_eur_m": 3.0},
    ]


def _cement_nace():
    """NACE activities for a cement manufacturer (CBAM sector)."""
    return [
        {"nace_code": "23.51", "revenue_share": 1.0, "ghg_intensity_tco2e_per_eur_m": 800.0},
    ]


def _multi_nace():
    """Mixed multi-activity entity: utility + housing + agriculture."""
    return [
        {"nace_code": "35.11", "revenue_share": 0.50, "ghg_intensity_tco2e_per_eur_m": 400.0},
        {"nace_code": "41", "revenue_share": 0.30, "ghg_intensity_tco2e_per_eur_m": 50.0},
        {"nace_code": "01", "revenue_share": 0.20, "ghg_intensity_tco2e_per_eur_m": 150.0},
    ]


# ========================================================================
# NGFS Scenarios
# ========================================================================

class TestNGFSScenarios:
    def test_six_scenarios_exist(self):
        assert len(NGFS_PHASE5_SCENARIOS) == 6
        expected = {
            "Net Zero 2050", "Below 2C", "Divergent Net Zero",
            "Delayed Transition", "NDCs", "Current Policies",
        }
        assert set(NGFS_PHASE5_SCENARIOS.keys()) == expected

    def test_all_have_required_keys(self):
        required = {
            "carbon_price_2030", "carbon_price_2050", "gdp_impact_pct",
            "temp_2100_c", "category", "energy_price_multiplier",
            "technology_change_rate", "renewable_share_2050",
            "fossil_demand_reduction_pct", "description",
        }
        for name, sc in NGFS_PHASE5_SCENARIOS.items():
            for key in required:
                assert key in sc, f"{name} missing key {key}"

    def test_orderly_vs_disorderly_categories(self):
        orderly = [n for n, s in NGFS_PHASE5_SCENARIOS.items() if s["category"] == "orderly"]
        disorderly = [n for n, s in NGFS_PHASE5_SCENARIOS.items() if s["category"] == "disorderly"]
        hot_house = [n for n, s in NGFS_PHASE5_SCENARIOS.items() if s["category"] == "hot_house"]
        assert set(orderly) == {"Net Zero 2050", "Below 2C"}
        assert set(disorderly) == {"Divergent Net Zero", "Delayed Transition"}
        assert set(hot_house) == {"NDCs", "Current Policies"}

    def test_net_zero_highest_carbon_price_2030(self):
        nz_price = NGFS_PHASE5_SCENARIOS["Net Zero 2050"]["carbon_price_2030"]
        for name, sc in NGFS_PHASE5_SCENARIOS.items():
            assert sc["carbon_price_2030"] <= nz_price, (
                f"{name} has higher 2030 carbon price than Net Zero 2050"
            )

    def test_current_policies_lowest_carbon_price(self):
        cp_price = NGFS_PHASE5_SCENARIOS["Current Policies"]["carbon_price_2030"]
        for name, sc in NGFS_PHASE5_SCENARIOS.items():
            assert sc["carbon_price_2030"] >= cp_price, (
                f"{name} has lower 2030 carbon price than Current Policies"
            )


# ========================================================================
# IEA NZE Pathway
# ========================================================================

class TestIEAPathway:
    def test_twelve_sectors_exist(self):
        assert len(IEA_NZE_PATHWAY) == 12
        expected = {
            "power", "cement", "steel", "transport", "chemicals", "aluminium",
            "buildings", "agriculture", "oil_and_gas", "aviation", "shipping",
            "pulp_and_paper",
        }
        assert set(IEA_NZE_PATHWAY.keys()) == expected

    def test_all_sectors_have_four_milestones(self):
        required_years = {2025, 2030, 2040, 2050}
        for sector, pathway in IEA_NZE_PATHWAY.items():
            assert set(pathway.keys()) == required_years, (
                f"Sector {sector} missing milestones"
            )

    def test_intensities_decline_over_time(self):
        for sector, pathway in IEA_NZE_PATHWAY.items():
            years = sorted(pathway.keys())
            for i in range(len(years) - 1):
                assert pathway[years[i]] >= pathway[years[i + 1]], (
                    f"Sector {sector}: intensity increases from {years[i]} to {years[i+1]}"
                )

    def test_power_reaches_zero_by_2050(self):
        assert IEA_NZE_PATHWAY["power"][2050] == 0.0


# ========================================================================
# TransitionRiskConfig
# ========================================================================

class TestTransitionRiskConfig:
    def test_default_config_valid(self):
        cfg = TransitionRiskConfig()
        # Should not raise
        engine = TransitionRiskEngine(config=cfg)
        assert engine.config.writedown_curve_type == "linear"
        assert engine.config.technology_substitution_speed == "moderate"
        assert engine.config.pass_through_rate == 0.70
        assert engine.config.residual_value_floor_pct == 10.0

    def test_invalid_category_weights_raises(self):
        with pytest.raises(ValueError, match="transition_risk_category_weights must sum to 1.0"):
            _engine(transition_risk_category_weights={
                "policy_legal": 0.50,
                "technology": 0.25,
                "market": 0.25,
                "reputation": 0.15,
            })

    def test_invalid_pass_through_rate_raises(self):
        with pytest.raises(ValueError, match="pass_through_rate"):
            _engine(pass_through_rate=1.5)

    def test_invalid_residual_floor_raises(self):
        with pytest.raises(ValueError, match="residual_value_floor_pct"):
            _engine(residual_value_floor_pct=50.0)

    def test_invalid_writedown_curve_raises(self):
        with pytest.raises(ValueError, match="writedown_curve_type"):
            _engine(writedown_curve_type="exponential")


# ========================================================================
# Stage 1: Sector Classification
# ========================================================================

class TestSectorClassification:
    def test_fossil_fuel_entity(self):
        engine = _default_engine()
        result = engine.classify_sector("CoalCorp", _fossil_nace())
        assert isinstance(result, SectorClassificationResult)
        assert result.cprs_category == "Fossil Fuel"
        assert result.sector_risk_score > 0.5
        assert result.ghg_bucket is not None

    def test_multi_nace_revenue_weighted(self):
        engine = _default_engine()
        result = engine.classify_sector("MixedCo", _multi_nace())
        assert isinstance(result, SectorClassificationResult)
        # Utility (0.50 revenue) dominates
        assert result.cprs_category in ("Utility", "Energy-Intensive")
        # Revenue-weighted score should be between min and max of component weights
        assert 0.0 < result.sector_risk_score <= 1.0

    def test_multi_activity_max_method(self):
        engine = _engine(multi_activity_method="max")
        result = engine.classify_sector("MixedCo", _multi_nace())
        # Max method: picks the highest risk weight among all activities
        assert result.sector_risk_score > 0.0

    def test_primary_only_method(self):
        engine = _engine(multi_activity_method="primary_only")
        result = engine.classify_sector("MixedCo", _multi_nace())
        # Primary only: uses just the first classification's risk weight
        assert result.sector_risk_score > 0.0

    def test_empty_nace_raises(self):
        engine = _default_engine()
        with pytest.raises(ValueError, match="nace_codes_with_revenue must not be empty"):
            engine.classify_sector("EmptyCo", [])


# ========================================================================
# Stage 2: Carbon Pricing
# ========================================================================

class TestCarbonPricing:
    def test_scope1_cost_calculation(self):
        engine = _default_engine()
        result = engine.assess_carbon_pricing(
            scope1_tco2e=100_000, scope2_tco2e=0, scope3_tco2e=0,
            revenue_eur=1e9, is_cbam_sector=False,
            scenario="Net Zero 2050", time_horizon=2030,
        )
        assert isinstance(result, CarbonPricingResult)
        # scope1_cost = 100_000 * 130 * 0.70 = 9_100_000
        assert result.scope1_cost == pytest.approx(9_100_000.0, rel=0.01)
        assert result.scope2_cost == 0.0
        assert result.scope3_cost == 0.0
        assert result.cbam_cost == 0.0

    def test_scope2_uses_elec_uplift(self):
        engine = _default_engine()
        result = engine.assess_carbon_pricing(
            scope1_tco2e=0, scope2_tco2e=50_000, scope3_tco2e=0,
            revenue_eur=1e9, is_cbam_sector=False,
            scenario="Net Zero 2050", time_horizon=2030,
        )
        # scope2_cost = 50_000 * 130 * 0.50 = 3_250_000
        assert result.scope2_cost == pytest.approx(3_250_000.0, rel=0.01)
        assert result.scope1_cost == 0.0

    def test_scope3_only_with_scope_1_2_3(self):
        engine = _engine(scope3_inclusion="scope_1_2_3")
        result = engine.assess_carbon_pricing(
            scope1_tco2e=10_000, scope2_tco2e=5_000, scope3_tco2e=200_000,
            revenue_eur=1e9, is_cbam_sector=False,
            scenario="Net Zero 2050", time_horizon=2030,
        )
        # scope3_cost = 200_000 * 130 * 0.70 * 0.30 = 5_460_000
        assert result.scope3_cost == pytest.approx(5_460_000.0, rel=0.01)
        assert result.scope3_cost > 0

    def test_cbam_cost_applied_when_sector(self):
        engine = _default_engine()
        result = engine.assess_carbon_pricing(
            scope1_tco2e=100_000, scope2_tco2e=0, scope3_tco2e=0,
            revenue_eur=1e9, is_cbam_sector=True, home_carbon_price=0.0,
            scenario="Net Zero 2050", time_horizon=2030,
        )
        # cbam_cost = 100_000 * 130 * 0.20 = 2_600_000
        assert result.cbam_cost == pytest.approx(2_600_000.0, rel=0.01)
        assert result.total_carbon_cost > result.scope1_cost

    def test_cbam_net_of_home_reduces_cost(self):
        engine = _default_engine()
        # With home_carbon_price = 50, CBAM unit price = max(0, 130-50) = 80
        result_home = engine.assess_carbon_pricing(
            scope1_tco2e=100_000, scope2_tco2e=0, scope3_tco2e=0,
            revenue_eur=1e9, is_cbam_sector=True, home_carbon_price=50.0,
            scenario="Net Zero 2050", time_horizon=2030,
        )
        result_no_home = engine.assess_carbon_pricing(
            scope1_tco2e=100_000, scope2_tco2e=0, scope3_tco2e=0,
            revenue_eur=1e9, is_cbam_sector=True, home_carbon_price=0.0,
            scenario="Net Zero 2050", time_horizon=2030,
        )
        assert result_home.cbam_cost < result_no_home.cbam_cost

    def test_carbon_price_interpolation_2035(self):
        engine = _default_engine()
        # Net Zero 2050: cp2030=130, cp2050=250
        # 2035 interpolation: 130 + (5/20) * (250-130) = 130 + 30 = 160
        result = engine.assess_carbon_pricing(
            scope1_tco2e=1_000, scope2_tco2e=0, scope3_tco2e=0,
            revenue_eur=1e9, is_cbam_sector=False,
            scenario="Net Zero 2050", time_horizon=2035,
        )
        expected_price = 160.0
        expected_cost = 1_000 * expected_price * 0.70
        assert result.scope1_cost == pytest.approx(expected_cost, rel=0.01)


# ========================================================================
# Stage 3: Stranded Assets
# ========================================================================

class TestStrandedAssets:
    def test_zero_reserve_returns_zero_risk(self):
        engine = _default_engine()
        result = engine.assess_stranded_assets(
            fossil_reserve_value=0.0,
            asset_categories=["fossil_reserves"],
        )
        assert isinstance(result, StrandedAssetResult)
        assert result.stranded_asset_risk == 0.0
        assert result.writedown_factor == 0.0
        assert result.residual_value == 0.0

    def test_linear_writedown(self):
        engine = _engine(writedown_curve_type="linear")
        result = engine.assess_stranded_assets(
            fossil_reserve_value=1_000_000_000,
            asset_categories=["fossil_reserves"],
            scenario="Net Zero 2050",
            time_horizon=2040,
        )
        assert result.writedown_factor > 0
        assert result.stranded_asset_risk > 0
        assert result.residual_value < result.fossil_reserve_value

    def test_front_loaded_writedown_faster_early(self):
        engine_fl = _engine(writedown_curve_type="front_loaded")
        engine_lin = _engine(writedown_curve_type="linear")
        # At an early time horizon (2035 = 10 years into transition),
        # front-loaded should write down more than linear
        result_fl = engine_fl.assess_stranded_assets(
            fossil_reserve_value=1e9,
            asset_categories=["fossil_reserves"],
            scenario="Net Zero 2050",
            time_horizon=2035,
        )
        result_lin = engine_lin.assess_stranded_assets(
            fossil_reserve_value=1e9,
            asset_categories=["fossil_reserves"],
            scenario="Net Zero 2050",
            time_horizon=2035,
        )
        assert result_fl.writedown_factor >= result_lin.writedown_factor

    def test_s_curve_writedown(self):
        engine = _engine(writedown_curve_type="s_curve")
        result = engine.assess_stranded_assets(
            fossil_reserve_value=1e9,
            asset_categories=["fossil_reserves"],
            scenario="Net Zero 2050",
            time_horizon=2040,
        )
        assert 0 < result.writedown_factor <= 1.0
        assert result.stranded_asset_risk > 0

    def test_step_writedown(self):
        engine = _engine(writedown_curve_type="step")
        # Before 60% of the period (moderate=20yr, 60% = 12yr, so before 2037):
        # writedown = base * 0.3
        result_early = engine.assess_stranded_assets(
            fossil_reserve_value=1e9,
            asset_categories=["fossil_reserves"],
            scenario="Net Zero 2050",
            time_horizon=2035,
        )
        # After 60% of the period:
        result_late = engine.assess_stranded_assets(
            fossil_reserve_value=1e9,
            asset_categories=["fossil_reserves"],
            scenario="Net Zero 2050",
            time_horizon=2040,
        )
        assert result_late.writedown_factor > result_early.writedown_factor

    def test_residual_value_floor(self):
        engine = _engine(
            writedown_curve_type="linear",
            residual_value_floor_pct=10.0,
        )
        # At time_horizon=2050 (25 years elapsed, moderate=20yr total => t=1.0),
        # linear writedown = base_factor * 1.0, but capped at 1.0 - floor
        result = engine.assess_stranded_assets(
            fossil_reserve_value=1e9,
            asset_categories=["fossil_reserves"],
            scenario="Net Zero 2050",
            time_horizon=2050,
        )
        # With 10% floor, writedown_factor <= 0.90
        assert result.writedown_factor <= 0.90
        # Residual value >= 10% of original
        assert result.residual_value >= 1e9 * 0.10 - 1.0  # small tolerance


# ========================================================================
# Stage 4: Alignment
# ========================================================================

class TestAlignment:
    def test_aligned_entity_small_gap(self):
        engine = _default_engine()
        # Power sector 2026 target is between 2025 (0.40) and 2030 (0.15)
        # Interpolated: 0.40 + (1/5)*(0.15-0.40) = 0.40 - 0.05 = 0.35
        # Set current intensity at 0.35 => zero or very small gap
        result = engine.assess_alignment(
            sector="power",
            current_emission_intensity=0.35,
            revenue_eur=1e9,
            readiness_data={"sbti_target": 90, "green_capex_ratio": 80,
                            "governance_quality": 85, "disclosed_pathway": 75},
        )
        assert isinstance(result, AlignmentResult)
        assert result.alignment_gap <= 0.05
        assert result.implied_temperature < 2.5

    def test_misaligned_entity_large_gap(self):
        engine = _default_engine()
        # Cement sector 2026 target ~ 0.85 + (1/5)*(0.70-0.85) = 0.82
        # Set current intensity at 2.0 => large gap
        result = engine.assess_alignment(
            sector="cement",
            current_emission_intensity=2.0,
            revenue_eur=1e9,
        )
        assert result.alignment_gap > 0.5
        assert result.implied_temperature > 2.0

    def test_temperature_overshoot_penalty(self):
        engine = _default_engine()
        # High intensity => implied_temp > 2.0 => overshoot_penalty multiplies gap
        result = engine.assess_alignment(
            sector="power",
            current_emission_intensity=1.5,  # Well above target
            revenue_eur=1e9,
        )
        # implied_temp = 1.5 + (gap/target)*1.5, should be > 2.0
        assert result.implied_temperature > 2.0
        # With penalty (1.5x), alignment_gap should be amplified
        # The raw gap before penalty would be ~1.15 (1.5-0.35),
        # multiplied by 1.5 => ~1.725
        assert result.alignment_gap > 1.0

    def test_readiness_score_calculation(self):
        engine = _default_engine()
        result = engine.assess_alignment(
            sector="buildings",
            current_emission_intensity=0.5,
            revenue_eur=1e9,
            readiness_data={
                "sbti_target": 100,
                "green_capex_ratio": 100,
                "governance_quality": 100,
                "disclosed_pathway": 100,
            },
        )
        # All indicators at 100 => readiness should be high (close to 100)
        assert result.transition_readiness_score >= 80.0
        assert len(result.readiness_breakdown) == 4

    def test_pathway_fallback_cprs_to_iea(self):
        engine = _default_engine()
        # "Fossil Fuel" CPRS maps to "oil_and_gas" IEA sector via _CPRS_TO_IEA_SECTOR
        result = engine.assess_alignment(
            sector="Fossil Fuel",  # Not a direct IEA key
            current_emission_intensity=0.80,
            revenue_eur=1e9,
        )
        assert isinstance(result, AlignmentResult)
        # Should fall back to oil_and_gas pathway (2026 target ~0.885)
        assert result.pathway_target > 0


# ========================================================================
# Stage 5: Scenario Stress Testing
# ========================================================================

class TestScenarioStress:
    def test_six_scenarios_returned(self):
        engine = _default_engine()
        results = engine.stress_test_scenarios(
            carbon_cost_base=5_000_000, stranded_risk_base=1_000_000,
            sector_risk_score=0.8, revenue_eur=1e9,
        )
        assert len(results) == 6
        scenario_names = {r.scenario for r in results}
        assert scenario_names == set(NGFS_PHASE5_SCENARIOS.keys())

    def test_net_zero_highest_carbon_cost(self):
        engine = _default_engine()
        results = engine.stress_test_scenarios(
            carbon_cost_base=5_000_000, stranded_risk_base=1_000_000,
            sector_risk_score=0.8, revenue_eur=1e9,
        )
        nz = next(r for r in results if r.scenario == "Net Zero 2050")
        for r in results:
            assert r.carbon_cost <= nz.carbon_cost + 0.01, (
                f"{r.scenario} has higher carbon cost than Net Zero 2050"
            )

    def test_current_policies_lowest_cost(self):
        engine = _default_engine()
        results = engine.stress_test_scenarios(
            carbon_cost_base=5_000_000, stranded_risk_base=1_000_000,
            sector_risk_score=0.8, revenue_eur=1e9,
        )
        cp = next(r for r in results if r.scenario == "Current Policies")
        for r in results:
            assert r.carbon_cost >= cp.carbon_cost - 0.01, (
                f"{r.scenario} has lower carbon cost than Current Policies"
            )

    def test_macro_feedback_increases_cvar(self):
        engine_on = _engine(macro_feedback_loops=True)
        engine_off = _engine(macro_feedback_loops=False)
        results_on = engine_on.stress_test_scenarios(
            carbon_cost_base=5_000_000, stranded_risk_base=1_000_000,
            sector_risk_score=0.8, revenue_eur=1e9,
        )
        results_off = engine_off.stress_test_scenarios(
            carbon_cost_base=5_000_000, stranded_risk_base=1_000_000,
            sector_risk_score=0.8, revenue_eur=1e9,
        )
        # For scenarios with non-zero gdp_impact_pct, macro feedback should increase CVaR
        for r_on, r_off in zip(results_on, results_off):
            gdp = NGFS_PHASE5_SCENARIOS[r_on.scenario]["gdp_impact_pct"]
            if abs(gdp) > 0:
                assert r_on.transition_cvar >= r_off.transition_cvar

    def test_pd_lgd_adjustments_positive(self):
        engine = _default_engine()
        results = engine.stress_test_scenarios(
            carbon_cost_base=5_000_000, stranded_risk_base=1_000_000,
            sector_risk_score=0.8, revenue_eur=1e9,
        )
        for r in results:
            assert r.pd_adjustment >= 0
            assert r.lgd_adjustment >= 0


# ========================================================================
# Stage 6: Composite Score
# ========================================================================

class TestCompositeScore:
    def test_composite_weighted_sum(self):
        engine = _default_engine()
        # Create minimal inputs for composite calculation
        carbon_results = {
            "NZ|2030": CarbonPricingResult(
                scope1_cost=5e6, scope2_cost=1e6, scope3_cost=0,
                cbam_cost=0, total_carbon_cost=6e6,
                carbon_cost_as_pct_revenue=0.6,
                scenario="Net Zero 2050", time_horizon=2030,
            ),
        }
        stranded = StrandedAssetResult(
            fossil_reserve_value=1e9, utilization_rate=0.25,
            writedown_factor=0.5, stranded_asset_risk=5e8,
            residual_value=5e8, years_to_full_writedown=20,
        )
        alignment = AlignmentResult(
            current_intensity=0.8, pathway_target=0.35,
            alignment_gap=0.45, alignment_pct=128.57,
            transition_readiness_score=40.0,
            readiness_breakdown={}, implied_temperature=2.5,
        )
        composite, cat_scores = engine.compute_composite_score(
            sector_score=0.8,
            carbon_pricing_results=carbon_results,
            stranded_result=stranded,
            alignment_result=alignment,
            scenario_results=[],
        )
        assert 0 <= composite <= 100
        assert "policy_legal" in cat_scores
        assert "technology" in cat_scores
        assert "market" in cat_scores
        assert "reputation" in cat_scores
        # Verify it is a weighted sum
        weights = engine.config.transition_risk_category_weights
        expected = sum(weights[c] * cat_scores[c] for c in cat_scores)
        assert composite == pytest.approx(expected, abs=0.1)

    def test_policy_legal_normalisation(self):
        engine = _default_engine()
        # carbon_cost_as_pct_revenue = 10% => policy_raw = 100
        carbon_results = {
            "test": CarbonPricingResult(
                scope1_cost=0, scope2_cost=0, scope3_cost=0,
                cbam_cost=0, total_carbon_cost=0,
                carbon_cost_as_pct_revenue=10.0,
                scenario="test", time_horizon=2030,
            ),
        }
        stranded = StrandedAssetResult(
            fossil_reserve_value=0, utilization_rate=1.0,
            writedown_factor=0.0, stranded_asset_risk=0,
            residual_value=0, years_to_full_writedown=0,
        )
        alignment = AlignmentResult(
            current_intensity=0, pathway_target=0.5,
            alignment_gap=0, alignment_pct=0,
            transition_readiness_score=100, readiness_breakdown={},
            implied_temperature=1.5,
        )
        _, cat_scores = engine.compute_composite_score(
            sector_score=0.0,
            carbon_pricing_results=carbon_results,
            stranded_result=stranded,
            alignment_result=alignment,
            scenario_results=[],
        )
        # 10% revenue => normalised to 100
        assert cat_scores["policy_legal"] == pytest.approx(100.0, abs=0.1)

    def test_technology_speed_multiplier(self):
        # Fast speed should multiply by 1.3
        engine_fast = _engine(technology_substitution_speed="fast")
        engine_slow = _engine(technology_substitution_speed="slow")
        stranded = StrandedAssetResult(
            fossil_reserve_value=1e9, utilization_rate=0.25,
            writedown_factor=0.5, stranded_asset_risk=5e8,
            residual_value=5e8, years_to_full_writedown=20,
        )
        empty_carbon = {}
        alignment = AlignmentResult(
            current_intensity=0, pathway_target=0.5,
            alignment_gap=0, alignment_pct=0,
            transition_readiness_score=50, readiness_breakdown={},
            implied_temperature=1.5,
        )
        _, scores_fast = engine_fast.compute_composite_score(
            sector_score=0.5, carbon_pricing_results=empty_carbon,
            stranded_result=stranded, alignment_result=alignment,
            scenario_results=[],
        )
        _, scores_slow = engine_slow.compute_composite_score(
            sector_score=0.5, carbon_pricing_results=empty_carbon,
            stranded_result=stranded, alignment_result=alignment,
            scenario_results=[],
        )
        # tech_raw = writedown_factor * 100 * speed_mult
        # fast: 0.5 * 100 * 1.3 = 65
        # slow: 0.5 * 100 * 0.7 = 35
        assert scores_fast["technology"] > scores_slow["technology"]

    def test_reputation_inversely_related_to_readiness(self):
        engine = _default_engine()
        stranded = StrandedAssetResult(
            fossil_reserve_value=0, utilization_rate=1.0,
            writedown_factor=0.0, stranded_asset_risk=0,
            residual_value=0, years_to_full_writedown=0,
        )
        align_high_readiness = AlignmentResult(
            current_intensity=0, pathway_target=0.5,
            alignment_gap=0, alignment_pct=0,
            transition_readiness_score=90,
            readiness_breakdown={}, implied_temperature=1.5,
        )
        align_low_readiness = AlignmentResult(
            current_intensity=0, pathway_target=0.5,
            alignment_gap=0, alignment_pct=0,
            transition_readiness_score=20,
            readiness_breakdown={}, implied_temperature=1.5,
        )
        _, scores_high = engine.compute_composite_score(
            sector_score=0.5, carbon_pricing_results={},
            stranded_result=stranded, alignment_result=align_high_readiness,
            scenario_results=[],
        )
        _, scores_low = engine.compute_composite_score(
            sector_score=0.5, carbon_pricing_results={},
            stranded_result=stranded, alignment_result=align_low_readiness,
            scenario_results=[],
        )
        # reputation = 100 - readiness_score => low readiness = high reputation risk
        assert scores_low["reputation"] > scores_high["reputation"]


# ========================================================================
# Full Entity Assessment
# ========================================================================

class TestFullEntityAssessment:
    def test_returns_all_result_fields(self):
        engine = _default_engine()
        result = engine.assess_entity(
            entity_id="E001",
            entity_name="TestCorp",
            nace_codes_with_revenue=_cement_nace(),
            scope1_tco2e=500_000,
            scope2_tco2e=100_000,
            scope3_tco2e=50_000,
            revenue_eur=2e9,
            fossil_reserve_value=5e8,
            current_emission_intensity=0.80,
            readiness_data={"sbti_target": 60, "green_capex_ratio": 30},
            is_cbam_sector=True,
            home_carbon_price=10.0,
            fossil_exposure_pct=30.0,
        )
        assert isinstance(result, TransitionRiskResult)
        assert result.entity_id == "E001"
        assert result.entity_name == "TestCorp"
        assert isinstance(result.sector_classification, SectorClassificationResult)
        assert isinstance(result.carbon_pricing, dict)
        assert len(result.carbon_pricing) > 0
        assert isinstance(result.stranded_assets, StrandedAssetResult)
        assert isinstance(result.alignment, AlignmentResult)
        assert isinstance(result.scenario_stress, list)
        assert len(result.scenario_stress) == 6
        assert 0 <= result.composite_transition_score <= 100
        assert result.transition_risk_rating in (
            "Very Low", "Low", "Medium", "High", "Very High"
        )
        assert result.max_transition_cvar >= 0
        assert result.max_pd_adjustment >= 0
        assert result.max_lgd_adjustment >= 0
        assert len(result.top_risk_categories) == 4
        assert isinstance(result.config_snapshot, dict)

    def test_fossil_fuel_entity_high_risk(self):
        engine = _default_engine()
        result = engine.assess_entity(
            entity_id="FOSSIL01",
            entity_name="BigOil Corp",
            nace_codes_with_revenue=_fossil_nace(),
            scope1_tco2e=2_000_000,
            scope2_tco2e=500_000,
            scope3_tco2e=5_000_000,
            revenue_eur=5e9,
            fossil_reserve_value=10e9,
            current_emission_intensity=1.5,
            readiness_data={"sbti_target": 10, "green_capex_ratio": 5},
            is_cbam_sector=False,
            fossil_exposure_pct=80.0,
        )
        # Fossil fuel entity should have a high composite score
        assert result.composite_transition_score > 40
        assert result.transition_risk_rating in ("Medium", "High", "Very High")
        assert result.sector_classification.cprs_category == "Fossil Fuel"

    def test_ict_entity_low_risk(self):
        engine = _default_engine()
        result = engine.assess_entity(
            entity_id="ICT01",
            entity_name="TechSoft Inc",
            nace_codes_with_revenue=_ict_nace(),
            scope1_tco2e=500,
            scope2_tco2e=2_000,
            scope3_tco2e=5_000,
            revenue_eur=2e9,
            fossil_reserve_value=0,
            current_emission_intensity=0.01,
            readiness_data={
                "sbti_target": 95, "green_capex_ratio": 60,
                "governance_quality": 90, "disclosed_pathway": 85,
            },
            is_cbam_sector=False,
            fossil_exposure_pct=0.0,
        )
        # ICT entity should have a low composite score
        assert result.composite_transition_score < 50
        assert result.transition_risk_rating in ("Very Low", "Low", "Medium")

    def test_score_to_rating_thresholds(self):
        assert TransitionRiskEngine.score_to_rating(0) == "Very Low"
        assert TransitionRiskEngine.score_to_rating(10) == "Very Low"
        assert TransitionRiskEngine.score_to_rating(19.99) == "Very Low"
        assert TransitionRiskEngine.score_to_rating(20) == "Low"
        assert TransitionRiskEngine.score_to_rating(39.99) == "Low"
        assert TransitionRiskEngine.score_to_rating(40) == "Medium"
        assert TransitionRiskEngine.score_to_rating(59.99) == "Medium"
        assert TransitionRiskEngine.score_to_rating(60) == "High"
        assert TransitionRiskEngine.score_to_rating(79.99) == "High"
        assert TransitionRiskEngine.score_to_rating(80) == "Very High"
        assert TransitionRiskEngine.score_to_rating(100) == "Very High"


# ========================================================================
# Portfolio Assessment
# ========================================================================

class TestPortfolioAssessment:
    def test_portfolio_multiple_entities(self):
        engine = _default_engine()
        entities = [
            {
                "entity_id": "E1",
                "entity_name": "CoalCorp",
                "nace_codes_with_revenue": _fossil_nace(),
                "scope1_tco2e": 1_000_000,
                "scope2_tco2e": 200_000,
                "revenue_eur": 3e9,
                "fossil_reserve_value": 5e9,
                "current_emission_intensity": 1.2,
            },
            {
                "entity_id": "E2",
                "entity_name": "TechCo",
                "nace_codes_with_revenue": _ict_nace(),
                "scope1_tco2e": 1_000,
                "scope2_tco2e": 5_000,
                "revenue_eur": 1e9,
                "current_emission_intensity": 0.02,
            },
        ]
        results = engine.assess_portfolio(entities)
        assert len(results) == 2
        assert all(isinstance(r, TransitionRiskResult) for r in results)
        # Fossil entity should score higher than ICT
        coal_score = results[0].composite_transition_score
        tech_score = results[1].composite_transition_score
        assert coal_score > tech_score

    def test_portfolio_single_entity(self):
        engine = _default_engine()
        entities = [
            {
                "entity_id": "E1",
                "entity_name": "SingleCo",
                "nace_codes_with_revenue": _cement_nace(),
                "scope1_tco2e": 300_000,
                "scope2_tco2e": 50_000,
                "revenue_eur": 1e9,
            },
        ]
        results = engine.assess_portfolio(entities)
        assert len(results) == 1
        assert results[0].entity_id == "E1"

    def test_portfolio_empty_returns_empty(self):
        engine = _default_engine()
        results = engine.assess_portfolio([])
        assert results == []
