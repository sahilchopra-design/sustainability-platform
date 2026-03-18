"""
Tests -- NACE-CPRS Mapper + Climate Physical Risk Engine
========================================================
57 tests across 12 test classes covering:
  - CPRS category reference data (completeness, weights, descriptions)
  - NACE-to-CPRS mapping (fossil fuel, utility, transport, agriculture, other)
  - NACE-CPRS Mapper (exact match, fallback, overrides, GHG intensity)
  - GHG intensity bucket classification
  - Counterparty sector scoring (single, multi-activity, edge cases)
  - Physical Risk Config validation (defaults, invalid params)
  - Hazard assessment (lat-band proxies, scenario scaling, time horizons)
  - Exposure assessment (asset value scaling, type modifiers, concentration)
  - Vulnerability assessment (sector matrix, adaptation, structural modifiers)
  - Damage functions (sigmoid, linear, step, exponential)
  - Full entity assessment (all fields, high-risk, adaptation, rating)
  - Portfolio assessment (list results, multi-entity, empty)
"""
import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.nace_cprs_mapper import (
    CPRS_CATEGORIES,
    NACE_TO_CPRS,
    CPRS_TO_IAM,
    GHG_INTENSITY_BUCKETS,
    SectorClassification,
    CounterpartySectorScore,
    NACECPRSMapper,
)
from services.climate_physical_risk_engine import (
    HAZARD_TYPES,
    SECTOR_VULNERABILITY_MATRIX,
    DAMAGE_FUNCTION_COEFFICIENTS,
    PhysicalRiskConfig,
    HazardScore,
    ExposureResult,
    VulnerabilityResult,
    DamageResult,
    PhysicalRiskResult,
    PhysicalRiskEngine,
)


# ═══════════════════════════════════════════════════════════════════════════
#  CPRS CATEGORIES — Reference Data
# ═══════════════════════════════════════════════════════════════════════════

class TestCPRSCategories:
    """Verify CPRS category reference data completeness and integrity."""

    def test_eight_categories_exist(self):
        expected = [
            "Fossil Fuel", "Utility", "Energy-Intensive", "Housing",
            "Transport", "Agriculture", "Finance (indirect)", "Other",
        ]
        for cat in expected:
            assert cat in CPRS_CATEGORIES, f"Missing CPRS category: {cat}"
        assert len(CPRS_CATEGORIES) == 8

    def test_risk_weights_range(self):
        for cat, data in CPRS_CATEGORIES.items():
            w = data["risk_weight"]
            assert 0 <= w <= 1, f"{cat} risk_weight {w} outside [0, 1]"

    def test_fossil_fuel_highest_weight(self):
        ff_weight = CPRS_CATEGORIES["Fossil Fuel"]["risk_weight"]
        for cat, data in CPRS_CATEGORIES.items():
            assert data["risk_weight"] <= ff_weight, (
                f"{cat} weight {data['risk_weight']} exceeds Fossil Fuel {ff_weight}"
            )

    def test_other_lowest_weight(self):
        other_weight = CPRS_CATEGORIES["Other"]["risk_weight"]
        for cat, data in CPRS_CATEGORIES.items():
            assert data["risk_weight"] >= other_weight, (
                f"{cat} weight {data['risk_weight']} below Other {other_weight}"
            )

    def test_all_have_descriptions(self):
        for cat, data in CPRS_CATEGORIES.items():
            assert "description" in data, f"{cat} missing description"
            assert len(data["description"]) > 10, f"{cat} description too short"


# ═══════════════════════════════════════════════════════════════════════════
#  NACE-TO-CPRS — Mapping Verification
# ═══════════════════════════════════════════════════════════════════════════

class TestNACEToCPRS:
    """Verify NACE Rev.2 to CPRS mapping correctness."""

    def test_fossil_fuel_mappings(self):
        for code in ["05", "06", "19"]:
            assert NACE_TO_CPRS[code] == "Fossil Fuel", (
                f"NACE {code} should map to Fossil Fuel"
            )

    def test_utility_mappings(self):
        for code in ["35", "36", "37", "38"]:
            assert NACE_TO_CPRS[code] == "Utility", (
                f"NACE {code} should map to Utility"
            )

    def test_transport_mappings(self):
        for code in ["49", "50", "51"]:
            assert NACE_TO_CPRS[code] == "Transport", (
                f"NACE {code} should map to Transport"
            )

    def test_agriculture_mappings(self):
        for code in ["01", "02", "10"]:
            assert NACE_TO_CPRS[code] == "Agriculture", (
                f"NACE {code} should map to Agriculture"
            )

    def test_other_mappings(self):
        for code in ["62", "85", "86"]:
            assert NACE_TO_CPRS[code] == "Other", (
                f"NACE {code} should map to Other"
            )


# ═══════════════════════════════════════════════════════════════════════════
#  NACE-CPRS MAPPER — Classification Logic
# ═══════════════════════════════════════════════════════════════════════════

class TestNACECPRSMapper:
    """Test NACECPRSMapper classification and cascading lookup."""

    def setup_method(self):
        self.mapper = NACECPRSMapper()

    def test_exact_match_4digit(self):
        cls = self.mapper.classify_nace("06.10")
        assert cls.cprs_category == "Fossil Fuel"
        assert cls.nace_code == "06.10"

    def test_2digit_fallback(self):
        cls = self.mapper.classify_nace("06")
        assert cls.cprs_category == "Fossil Fuel"

    def test_unknown_code_defaults_other(self):
        cls = self.mapper.classify_nace("99")
        assert cls.cprs_category == "Other"
        assert cls.cprs_risk_weight == CPRS_CATEGORIES["Other"]["risk_weight"]

    def test_cascading_3char_lookup(self):
        cls = self.mapper.classify_nace("35.1")
        assert cls.cprs_category == "Utility"

    def test_classify_nace_returns_sector_classification(self):
        cls = self.mapper.classify_nace("24.10", nace_description="Basic iron/steel")
        assert isinstance(cls, SectorClassification)
        assert cls.nace_code == "24.10"
        assert cls.nace_description == "Basic iron/steel"
        assert cls.cprs_category == "Energy-Intensive"
        assert len(cls.iam_sectors) > 0

    def test_classify_nace_with_ghg_intensity(self):
        cls = self.mapper.classify_nace("19.20", ghg_intensity_tco2e_per_eur_m=1500.0)
        assert cls.ghg_intensity_bucket == "Very High"

    def test_risk_weight_overrides(self):
        mapper = NACECPRSMapper(cprs_risk_weight_overrides={"Other": 0.50})
        cls = mapper.classify_nace("99")
        assert cls.cprs_risk_weight == 0.50

    def test_nace_overrides(self):
        mapper = NACECPRSMapper(nace_overrides={"99": "Fossil Fuel"})
        cls = mapper.classify_nace("99")
        assert cls.cprs_category == "Fossil Fuel"


# ═══════════════════════════════════════════════════════════════════════════
#  GHG INTENSITY BUCKETS — Classification
# ═══════════════════════════════════════════════════════════════════════════

class TestGHGBuckets:
    """Test GHG intensity bucket classification thresholds."""

    def test_very_high(self):
        assert NACECPRSMapper.classify_ghg_intensity(1500) == "Very High"

    def test_high(self):
        assert NACECPRSMapper.classify_ghg_intensity(600) == "High"

    def test_medium(self):
        assert NACECPRSMapper.classify_ghg_intensity(200) == "Medium"

    def test_low(self):
        assert NACECPRSMapper.classify_ghg_intensity(50) == "Low"

    def test_very_low(self):
        assert NACECPRSMapper.classify_ghg_intensity(10) == "Very Low"


# ═══════════════════════════════════════════════════════════════════════════
#  COUNTERPARTY SCORING — Multi-Activity Risk
# ═══════════════════════════════════════════════════════════════════════════

class TestCounterpartyScoring:
    """Test counterparty sector risk scoring."""

    def setup_method(self):
        self.mapper = NACECPRSMapper()

    def test_single_activity(self):
        score = self.mapper.score_counterparty(
            "Oil Corp",
            [{"nace_code": "06.10", "revenue_share": 1.0}],
        )
        assert isinstance(score, CounterpartySectorScore)
        assert score.entity_name == "Oil Corp"
        assert score.primary_nace == "06.10"
        assert score.multi_activity is False
        assert score.sector_risk_score == 1.0  # Fossil Fuel weight

    def test_multi_activity_revenue_weighted(self):
        score = self.mapper.score_counterparty(
            "Diversified Corp",
            [
                {"nace_code": "06.10", "revenue_share": 0.5},   # Fossil Fuel 1.0
                {"nace_code": "62", "revenue_share": 0.5},      # Other
            ],
        )
        assert score.multi_activity is True
        # Revenue-weighted score should be between the two individual weights
        ff_weight = score.classifications[0].cprs_risk_weight   # Fossil Fuel
        oth_weight = score.classifications[1].cprs_risk_weight  # Other
        expected = 0.5 * ff_weight + 0.5 * oth_weight
        assert abs(score.sector_risk_score - expected) < 0.01
        # Fossil Fuel contribution should dominate
        assert score.sector_risk_score > oth_weight

    def test_empty_activities_raises(self):
        with pytest.raises(ValueError, match="activities list must not be empty"):
            self.mapper.score_counterparty("Empty Corp", [])

    def test_dominant_cprs_category(self):
        score = self.mapper.score_counterparty(
            "Utility Firm",
            [
                {"nace_code": "35.11", "revenue_share": 0.7},  # Utility
                {"nace_code": "62", "revenue_share": 0.3},     # Other
            ],
        )
        assert score.dominant_cprs_category == "Utility"

    def test_ghg_bucket_in_counterparty(self):
        score = self.mapper.score_counterparty(
            "Heavy Emitter",
            [
                {
                    "nace_code": "19.20",
                    "revenue_share": 1.0,
                    "ghg_intensity_tco2e_per_eur_m": 1200.0,
                },
            ],
        )
        assert score.ghg_bucket == "Very High"


# ═══════════════════════════════════════════════════════════════════════════
#  PHYSICAL RISK CONFIG — Validation
# ═══════════════════════════════════════════════════════════════════════════

class TestPhysicalRiskConfig:
    """Test PhysicalRiskConfig construction and validation."""

    def test_default_config_valid(self):
        engine = PhysicalRiskEngine()
        assert engine.config is not None
        assert engine.config.damage_function_type == "sigmoid"
        assert engine.config.discount_rate_pct == 3.5

    def test_invalid_adaptation_discount_raises(self):
        with pytest.raises(ValueError, match="adaptation_discount_pct"):
            PhysicalRiskEngine(config=PhysicalRiskConfig(adaptation_discount_pct=60.0))

    def test_invalid_damage_cap_raises(self):
        with pytest.raises(ValueError, match="damage_cap_pct"):
            PhysicalRiskEngine(config=PhysicalRiskConfig(damage_cap_pct=150.0))

    def test_invalid_scenario_raises(self):
        with pytest.raises(ValueError, match="Unknown scenario"):
            PhysicalRiskEngine(config=PhysicalRiskConfig(scenarios=["RCP-99"]))

    def test_invalid_damage_function_type_raises(self):
        with pytest.raises(ValueError, match="damage_function_type"):
            PhysicalRiskEngine(config=PhysicalRiskConfig(damage_function_type="cubic"))


# ═══════════════════════════════════════════════════════════════════════════
#  HAZARD ASSESSMENT — Stage 1
# ═══════════════════════════════════════════════════════════════════════════

class TestHazardAssessment:
    """Test hazard score computation across locations and scenarios."""

    def setup_method(self):
        self.engine = PhysicalRiskEngine()

    def test_tropical_flooding_higher_than_polar(self):
        # Tropical location (lat=5) should have higher flooding score than polar (lat=70)
        tropical = self.engine.assess_hazard("flooding", 5.0, 0.0, "SSP2-4.5", 2050)
        polar = self.engine.assess_hazard("flooding", 70.0, 0.0, "SSP2-4.5", 2050)
        assert tropical.score > polar.score

    def test_scenario_severity_scales_score(self):
        high = self.engine.assess_hazard("flooding", 10.0, 0.0, "SSP5-8.5", 2050)
        low = self.engine.assess_hazard("flooding", 10.0, 0.0, "SSP1-1.9", 2050)
        assert high.score > low.score

    def test_later_time_horizon_higher(self):
        # Chronic hazards should intensify over time
        early = self.engine.assess_hazard("temperature_increase", 30.0, 0.0, "SSP2-4.5", 2030)
        late = self.engine.assess_hazard("temperature_increase", 30.0, 0.0, "SSP2-4.5", 2050)
        assert late.score >= early.score

    def test_hazard_score_bounded_0_1(self):
        # Test extreme inputs to confirm score stays in [0, 1]
        score = self.engine.assess_hazard("cyclone", 15.0, 0.0, "SSP5-8.5", 2100)
        assert 0.0 <= score.score <= 1.0

    def test_all_13_hazards_produce_scores(self):
        all_hazards = list(HAZARD_TYPES.keys())
        assert len(all_hazards) == 13
        for hz in all_hazards:
            hs = self.engine.assess_hazard(hz, 25.0, 10.0, "SSP2-4.5", 2050)
            assert isinstance(hs, HazardScore)
            assert 0.0 <= hs.score <= 1.0
            assert hs.hazard_type == hz


# ═══════════════════════════════════════════════════════════════════════════
#  EXPOSURE ASSESSMENT — Stage 2
# ═══════════════════════════════════════════════════════════════════════════

class TestExposureAssessment:
    """Test exposure score computation."""

    def setup_method(self):
        self.engine = PhysicalRiskEngine()

    def test_exposure_scales_with_asset_value(self):
        small = self.engine.assess_exposure(1_000_000, "general", 30.0, 0.0, "flooding")
        large = self.engine.assess_exposure(10_000_000, "general", 30.0, 0.0, "flooding")
        assert large.exposure_score > small.exposure_score

    def test_asset_type_modifier(self):
        config = PhysicalRiskConfig(asset_type_modifiers={"underground": 0.3})
        engine = PhysicalRiskEngine(config=config)
        normal = engine.assess_exposure(5_000_000, "general", 30.0, 0.0, "severe_wind")
        under = engine.assess_exposure(5_000_000, "underground", 30.0, 0.0, "severe_wind")
        assert under.exposure_fraction < normal.exposure_fraction

    def test_concentration_penalty_raises_score(self):
        config = PhysicalRiskConfig(concentration_penalty=1.5)
        engine = PhysicalRiskEngine(config=config)
        result = engine.assess_exposure(5_000_000, "general", 30.0, 0.0, "flooding")
        assert result.concentration_factor == 1.5
        # Score with penalty > score without
        baseline = self.engine.assess_exposure(5_000_000, "general", 30.0, 0.0, "flooding")
        assert result.exposure_score > baseline.exposure_score


# ═══════════════════════════════════════════════════════════════════════════
#  VULNERABILITY ASSESSMENT — Stage 3
# ═══════════════════════════════════════════════════════════════════════════

class TestVulnerabilityAssessment:
    """Test vulnerability computation with sector matrix and modifiers."""

    def setup_method(self):
        self.engine = PhysicalRiskEngine()

    def test_agriculture_drought_high_vulnerability(self):
        vuln = self.engine.assess_vulnerability("Agriculture", "drought")
        # Agriculture drought base = 0.90
        assert vuln.base_vulnerability >= 0.80
        assert vuln.final_vulnerability > 0.5

    def test_ict_has_low_vulnerability(self):
        vuln = self.engine.assess_vulnerability("ICT", "drought")
        # ICT drought base = 0.10
        assert vuln.base_vulnerability <= 0.20

    def test_adaptation_reduces_vulnerability(self):
        config = PhysicalRiskConfig(adaptation_discount_pct=30.0)
        engine = PhysicalRiskEngine(config=config)
        no_adapt = engine.assess_vulnerability("Agriculture", "drought", has_adaptation=False)
        with_adapt = engine.assess_vulnerability("Agriculture", "drought", has_adaptation=True)
        assert with_adapt.final_vulnerability < no_adapt.final_vulnerability
        assert with_adapt.adaptation_discount == 0.30

    def test_building_age_increases_vulnerability(self):
        young = self.engine.assess_vulnerability(
            "Real Estate", "flooding", building_age_years=5
        )
        old = self.engine.assess_vulnerability(
            "Real Estate", "flooding", building_age_years=80
        )
        assert old.modifier_product > young.modifier_product

    def test_elevation_reduces_flood_vulnerability(self):
        low = self.engine.assess_vulnerability(
            "Real Estate", "flooding", elevation_m=2.0
        )
        high = self.engine.assess_vulnerability(
            "Real Estate", "flooding", elevation_m=150.0
        )
        assert high.final_vulnerability < low.final_vulnerability


# ═══════════════════════════════════════════════════════════════════════════
#  DAMAGE FUNCTIONS — Stage 4
# ═══════════════════════════════════════════════════════════════════════════

class TestDamageFunction:
    """Test damage function dispatch and output bounds."""

    def test_sigmoid_output_bounded(self):
        engine = PhysicalRiskEngine(config=PhysicalRiskConfig(damage_function_type="sigmoid"))
        hs = HazardScore(hazard_type="flooding", category="acute",
                         intensity=0.8, frequency=0.6, duration=0.4, score=0.6)
        exp = ExposureResult(asset_value=1_000_000, exposure_fraction=0.5,
                             concentration_factor=1.0, exposure_score=500_000)
        vuln = VulnerabilityResult(sector="Agriculture", base_vulnerability=0.7,
                                   modifier_product=1.0, adaptation_discount=0.0,
                                   cascading_multiplier=1.2, final_vulnerability=0.7)
        dmg = engine.compute_damage(hs, exp, vuln, "flooding")
        assert 0.0 <= dmg.damage_function_output <= 1.0
        assert dmg.cvar_contribution >= 0.0

    def test_linear_damage_proportional(self):
        engine = PhysicalRiskEngine(config=PhysicalRiskConfig(damage_function_type="linear"))
        hs = HazardScore(hazard_type="flooding", category="acute",
                         intensity=0.5, frequency=0.5, duration=0.5, score=0.5)
        exp = ExposureResult(asset_value=1_000_000, exposure_fraction=0.4,
                             concentration_factor=1.0, exposure_score=400_000)
        vuln = VulnerabilityResult(sector="Real Estate", base_vulnerability=0.6,
                                   modifier_product=1.0, adaptation_discount=0.0,
                                   cascading_multiplier=1.0, final_vulnerability=0.6)
        dmg = engine.compute_damage(hs, exp, vuln, "flooding")
        assert dmg.damage_function_output > 0.0
        assert dmg.damage_function_output <= 1.0

    def test_step_function_discrete_jumps(self):
        engine = PhysicalRiskEngine(config=PhysicalRiskConfig(damage_function_type="step"))
        # Low combined score -> lowest step value
        hs_low = HazardScore(hazard_type="flooding", category="acute",
                             intensity=0.1, frequency=0.1, duration=0.1, score=0.1)
        exp = ExposureResult(asset_value=1_000_000, exposure_fraction=0.1,
                             concentration_factor=1.0, exposure_score=100_000)
        vuln = VulnerabilityResult(sector="ICT", base_vulnerability=0.1,
                                   modifier_product=1.0, adaptation_discount=0.0,
                                   cascading_multiplier=1.0, final_vulnerability=0.1)
        dmg_low = engine.compute_damage(hs_low, exp, vuln, "flooding")

        # High combined score -> higher step value
        hs_high = HazardScore(hazard_type="flooding", category="acute",
                              intensity=0.9, frequency=0.9, duration=0.9, score=0.9)
        exp_high = ExposureResult(asset_value=1_000_000, exposure_fraction=0.9,
                                  concentration_factor=1.0, exposure_score=900_000)
        vuln_high = VulnerabilityResult(sector="Agriculture", base_vulnerability=0.9,
                                        modifier_product=1.0, adaptation_discount=0.0,
                                        cascading_multiplier=1.0, final_vulnerability=0.9)
        dmg_high = engine.compute_damage(hs_high, exp_high, vuln_high, "flooding")

        assert dmg_high.damage_function_output > dmg_low.damage_function_output

    def test_exponential_increases_with_score(self):
        engine = PhysicalRiskEngine(config=PhysicalRiskConfig(damage_function_type="exponential"))
        exp = ExposureResult(asset_value=1_000_000, exposure_fraction=0.5,
                             concentration_factor=1.0, exposure_score=500_000)
        vuln = VulnerabilityResult(sector="Energy", base_vulnerability=0.6,
                                   modifier_product=1.0, adaptation_discount=0.0,
                                   cascading_multiplier=1.0, final_vulnerability=0.6)

        hs_low = HazardScore(hazard_type="wildfire", category="acute",
                             intensity=0.2, frequency=0.2, duration=0.2, score=0.2)
        hs_high = HazardScore(hazard_type="wildfire", category="acute",
                              intensity=0.8, frequency=0.8, duration=0.8, score=0.8)

        dmg_low = engine.compute_damage(hs_low, exp, vuln, "wildfire")
        dmg_high = engine.compute_damage(hs_high, exp, vuln, "wildfire")
        assert dmg_high.damage_function_output > dmg_low.damage_function_output


# ═══════════════════════════════════════════════════════════════════════════
#  FULL ENTITY ASSESSMENT — End-to-End Pipeline
# ═══════════════════════════════════════════════════════════════════════════

class TestFullEntityAssessment:
    """Test full 5-stage entity assessment pipeline."""

    def setup_method(self):
        self.engine = PhysicalRiskEngine()

    def test_entity_assessment_returns_all_fields(self):
        result = self.engine.assess_entity(
            entity_id="E001",
            entity_name="Test Farm",
            entity_type="asset",
            sector="Agriculture",
            asset_value=5_000_000,
            lat=30.0,
            lon=10.0,
        )
        assert isinstance(result, PhysicalRiskResult)
        assert result.entity_id == "E001"
        assert result.entity_name == "Test Farm"
        assert result.entity_type == "asset"
        assert result.scenario == "SSP2-4.5"
        assert result.time_horizon == 2030
        assert len(result.hazard_scores) == 13
        assert result.exposure is not None
        assert len(result.vulnerability_by_hazard) == 13
        assert len(result.damage_by_hazard) == 13
        assert result.physical_cvar >= 0.0
        assert 0.0 <= result.physical_risk_score <= 100.0
        assert result.risk_rating in ("Very Low", "Low", "Medium", "High", "Very High")
        assert result.expected_annual_loss >= 0.0
        assert result.pd_adjustment >= 0.0
        assert result.lgd_adjustment >= 0.0
        assert len(result.top_hazards) > 0
        assert isinstance(result.config_snapshot, dict)

    def test_entity_assessment_high_risk_location(self):
        # Tropical coastal location under worst-case scenario should score higher
        result_high = self.engine.assess_entity(
            entity_id="E002",
            entity_name="Coastal Hotel",
            entity_type="asset",
            sector="Tourism",
            asset_value=10_000_000,
            lat=10.0,
            lon=0.0,
            scenario="SSP5-8.5",
            time_horizon=2100,
        )
        result_low = self.engine.assess_entity(
            entity_id="E003",
            entity_name="Nordic Office",
            entity_type="asset",
            sector="ICT",
            asset_value=10_000_000,
            lat=60.0,
            lon=25.0,
            scenario="SSP1-1.9",
            time_horizon=2030,
        )
        assert result_high.physical_risk_score > result_low.physical_risk_score

    def test_entity_assessment_with_adaptation(self):
        config = PhysicalRiskConfig(adaptation_discount_pct=40.0)
        engine = PhysicalRiskEngine(config=config)
        no_adapt = engine.assess_entity(
            entity_id="E004", entity_name="Factory A", entity_type="asset",
            sector="Manufacturing", asset_value=5_000_000, lat=35.0, lon=0.0,
            has_adaptation=False,
        )
        with_adapt = engine.assess_entity(
            entity_id="E005", entity_name="Factory B", entity_type="asset",
            sector="Manufacturing", asset_value=5_000_000, lat=35.0, lon=0.0,
            has_adaptation=True,
        )
        assert with_adapt.physical_risk_score <= no_adapt.physical_risk_score

    def test_score_to_rating_thresholds(self):
        assert PhysicalRiskEngine.score_to_rating(0) == "Very Low"
        assert PhysicalRiskEngine.score_to_rating(10) == "Very Low"
        assert PhysicalRiskEngine.score_to_rating(19.9) == "Very Low"
        assert PhysicalRiskEngine.score_to_rating(20) == "Low"
        assert PhysicalRiskEngine.score_to_rating(39.9) == "Low"
        assert PhysicalRiskEngine.score_to_rating(40) == "Medium"
        assert PhysicalRiskEngine.score_to_rating(59.9) == "Medium"
        assert PhysicalRiskEngine.score_to_rating(60) == "High"
        assert PhysicalRiskEngine.score_to_rating(79.9) == "High"
        assert PhysicalRiskEngine.score_to_rating(80) == "Very High"
        assert PhysicalRiskEngine.score_to_rating(100) == "Very High"


# ═══════════════════════════════════════════════════════════════════════════
#  PORTFOLIO ASSESSMENT — Multi-Entity Roll-Up
# ═══════════════════════════════════════════════════════════════════════════

class TestPortfolioAssessment:
    """Test portfolio-level physical risk assessment."""

    def setup_method(self):
        self.engine = PhysicalRiskEngine()

    def test_portfolio_returns_list_of_results(self):
        entities = [
            {
                "entity_id": "P001",
                "entity_name": "Farm Alpha",
                "entity_type": "asset",
                "sector": "Agriculture",
                "asset_value": 2_000_000,
                "lat": 25.0,
                "lon": 5.0,
            },
        ]
        results = self.engine.assess_portfolio(entities, scenario="SSP2-4.5", time_horizon=2050)
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], PhysicalRiskResult)

    def test_portfolio_multiple_entities(self):
        entities = [
            {
                "entity_id": "P010",
                "entity_name": "Office Tower",
                "entity_type": "asset",
                "sector": "Real Estate",
                "asset_value": 50_000_000,
                "lat": 40.0,
                "lon": -74.0,
            },
            {
                "entity_id": "P011",
                "entity_name": "Solar Farm",
                "entity_type": "asset",
                "sector": "Energy",
                "asset_value": 20_000_000,
                "lat": 35.0,
                "lon": -5.0,
            },
            {
                "entity_id": "P012",
                "entity_name": "Cargo Fleet",
                "entity_type": "asset",
                "sector": "Transport Water",
                "asset_value": 15_000_000,
                "lat": 10.0,
                "lon": 100.0,
            },
        ]
        results = self.engine.assess_portfolio(entities)
        assert len(results) == 3
        for r in results:
            assert isinstance(r, PhysicalRiskResult)
            assert r.physical_cvar >= 0.0

    def test_portfolio_empty_entities(self):
        results = self.engine.assess_portfolio([])
        assert results == []
