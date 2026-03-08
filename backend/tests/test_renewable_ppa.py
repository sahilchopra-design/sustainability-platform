"""
Tests for Renewable Project Finance + PPA Risk Scoring
=======================================================
Covers: WindYield, SolarYield, LCOE, ProjectFinance, PPARiskScorer,
        plus reference data lookups.
"""
import sys, os, math, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.renewable_project_engine import (
    RenewableProjectEngine,
    TURBINE_CLASSES,
    WIND_RESOURCE_REGIONS,
    SOLAR_GHI_DATA,
    SOLAR_DEFAULTS,
    WindYieldResult,
    SolarYieldResult,
    LCOEResult,
    ProjectFinanceResult,
)
from services.ppa_risk_scorer import (
    PPARiskScorer,
    PPAInput,
    PPARiskResult,
    PPARiskDimension,
    CREDIT_SCORES,
    PRICE_STRUCTURE_SCORES,
    TENOR_RISK,
    CURTAILMENT_RISK,
    REGULATORY_RISK,
    PPA_RISK_WEIGHTS,
)


# ── Factories ──────────────────────────────────────────────────────────

def _wind(**kw):
    defaults = dict(
        turbine_class="onshore_2mw",
        region="northern_europe_onshore",
        num_turbines=10,
        wake_loss_pct=8.0,
        availability_pct=97.0,
    )
    defaults.update(kw)
    return RenewableProjectEngine().wind_yield(**defaults)


def _solar(**kw):
    defaults = dict(country="DE", capacity_kwp=1000)
    defaults.update(kw)
    return RenewableProjectEngine().solar_yield(**defaults)


def _lcoe(**kw):
    defaults = dict(
        technology="wind",
        total_capex_eur=24_000_000,
        annual_opex_eur=700_000,
        annual_generation_mwh=50_000,
        wacc_pct=6.0,
        lifetime_years=25,
    )
    defaults.update(kw)
    return RenewableProjectEngine().lcoe(**defaults)


def _project(**kw):
    defaults = dict(
        project_name="Test Wind Farm",
        technology="wind",
        turbine_class="onshore_2mw",
        region="northern_europe_onshore",
        num_turbines=10,
        ppa_price_eur_mwh=60.0,
        carbon_price_eur_tonne=80.0,
        grid_ef_tco2_mwh=0.4,
        wacc_pct=6.0,
    )
    defaults.update(kw)
    return RenewableProjectEngine().assess_project(**defaults)


def _ppa_input(**kw):
    defaults = dict(
        ppa_id="PPA-001",
        project_name="Windpark Alpha",
        offtaker_name="UtilityCo",
        offtaker_credit_rating="A",
        price_structure="fixed",
        ppa_price_eur_mwh=60.0,
        tenor_years=10.0,
        curtailment_risk="low",
        regulatory_risk="stable",
        volume_hedged_pct=100.0,
        merchant_exposure_pct=0.0,
        subsidy_dependence_pct=0.0,
    )
    defaults.update(kw)
    return PPAInput(**defaults)


# ========================================================================
# Wind Yield
# ========================================================================

class TestWindYield:
    def test_default_returns_result(self):
        r = _wind()
        assert isinstance(r, WindYieldResult)
        assert r.total_capacity_mw == 20.0

    def test_capacity_factor_in_range(self):
        r = _wind()
        assert 10 < r.capacity_factor_pct < 65

    def test_p50_gt_p75_gt_p90(self):
        r = _wind()
        assert r.p50_generation_mwh > r.p75_generation_mwh > r.p90_generation_mwh

    def test_offshore_higher_cf(self):
        onshore = _wind(turbine_class="onshore_2mw", region="northern_europe_onshore")
        offshore = _wind(turbine_class="offshore_8mw", region="north_sea")
        assert offshore.capacity_factor_pct > onshore.capacity_factor_pct

    def test_more_turbines_more_gen(self):
        r5 = _wind(num_turbines=5)
        r20 = _wind(num_turbines=20)
        assert r20.p50_generation_mwh > r5.p50_generation_mwh

    def test_higher_wake_loss_lower_gen(self):
        low = _wind(wake_loss_pct=3.0)
        high = _wind(wake_loss_pct=15.0)
        assert low.p50_generation_mwh > high.p50_generation_mwh

    def test_unknown_turbine_falls_back(self):
        r = _wind(turbine_class="nonexistent")
        assert r.turbine_name == "Onshore 2 MW"

    def test_unknown_region_falls_back(self):
        r = _wind(region="nonexistent")
        assert r.region == "nonexistent"  # stored as-is but params default

    def test_all_regions_produce(self):
        eng = RenewableProjectEngine()
        for region in WIND_RESOURCE_REGIONS:
            r = eng.wind_yield(region=region)
            assert r.p50_generation_mwh > 0

    def test_all_turbines_produce(self):
        eng = RenewableProjectEngine()
        for tc in TURBINE_CLASSES:
            r = eng.wind_yield(turbine_class=tc)
            assert r.p50_generation_mwh > 0

    def test_eflh_consistent_with_cf(self):
        r = _wind()
        expected_eflh = r.capacity_factor_pct / 100 * 8760
        assert abs(r.equivalent_full_load_hours - expected_eflh) < 5


# ========================================================================
# Solar Yield
# ========================================================================

class TestSolarYield:
    def test_default_returns_result(self):
        r = _solar()
        assert isinstance(r, SolarYieldResult)
        assert r.capacity_kwp == 1000

    def test_p50_gt_p75_gt_p90(self):
        r = _solar()
        assert r.p50_generation_mwh_yr1 > r.p75_generation_mwh_yr1 > r.p90_generation_mwh_yr1

    def test_higher_ghi_more_yield(self):
        de = _solar(country="DE")  # 1100 kWh/m2
        es = _solar(country="ES")  # 1800 kWh/m2
        assert es.p50_generation_mwh_yr1 > de.p50_generation_mwh_yr1

    def test_lifetime_avg_less_than_yr1(self):
        r = _solar()
        assert r.p50_lifetime_avg_mwh < r.p50_generation_mwh_yr1

    def test_custom_performance_ratio(self):
        high = _solar(performance_ratio=0.90)
        low = _solar(performance_ratio=0.70)
        assert high.p50_generation_mwh_yr1 > low.p50_generation_mwh_yr1

    def test_capacity_factor_plausible(self):
        r = _solar(country="AU")  # high GHI
        assert 10 < r.capacity_factor_pct < 30

    def test_unknown_country_fallback(self):
        r = _solar(country="XX")
        assert r.ghi_kwh_m2_yr == 1400  # default

    def test_all_countries_produce(self):
        eng = RenewableProjectEngine()
        for c in SOLAR_GHI_DATA:
            r = eng.solar_yield(country=c)
            assert r.p50_generation_mwh_yr1 > 0

    def test_specific_yield_matches(self):
        r = _solar(country="ES")
        # specific_yield = GHI * effective_PR
        expected_gen = r.capacity_kwp * r.specific_yield_kwh_kwp / 1000
        assert abs(r.p50_generation_mwh_yr1 - expected_gen) < 1.0


# ========================================================================
# LCOE
# ========================================================================

class TestLCOE:
    def test_basic_lcoe(self):
        r = _lcoe()
        assert isinstance(r, LCOEResult)
        assert r.lcoe_eur_mwh > 0

    def test_higher_capex_higher_lcoe(self):
        base = _lcoe(total_capex_eur=24_000_000)
        high = _lcoe(total_capex_eur=48_000_000)
        assert high.lcoe_eur_mwh > base.lcoe_eur_mwh

    def test_degradation_increases_lcoe(self):
        base = _lcoe(degradation_pct_yr=0.0)
        deg = _lcoe(degradation_pct_yr=1.0)
        assert deg.lcoe_with_degradation_eur_mwh > base.lcoe_with_degradation_eur_mwh

    def test_zero_wacc(self):
        r = _lcoe(wacc_pct=0.0)
        assert r.crf == pytest.approx(1 / 25, rel=1e-3)

    def test_crf_positive(self):
        r = _lcoe(wacc_pct=8.0)
        assert r.crf > 0

    def test_lower_wacc_lower_lcoe(self):
        low = _lcoe(wacc_pct=3.0)
        high = _lcoe(wacc_pct=10.0)
        assert low.lcoe_eur_mwh < high.lcoe_eur_mwh


# ========================================================================
# Project Finance Assessment
# ========================================================================

class TestProjectFinance:
    def test_wind_project(self):
        r = _project(technology="wind")
        assert isinstance(r, ProjectFinanceResult)
        assert r.technology == "wind"
        assert r.irr_pct > 0
        assert r.co2_avoided_tonnes_yr > 0

    def test_solar_project(self):
        r = _project(
            technology="solar",
            project_name="Solar Farm",
            country="ES",
            capacity_kwp=5000,
        )
        assert r.technology == "solar"
        assert r.npv_eur != 0

    def test_carbon_revenue_positive(self):
        r = _project(carbon_price_eur_tonne=100)
        assert r.carbon_revenue_eur_yr > 0
        assert r.irr_with_carbon_pct > r.irr_pct

    def test_high_ppa_price_better_irr(self):
        low = _project(ppa_price_eur_mwh=30)
        high = _project(ppa_price_eur_mwh=100)
        assert high.irr_pct > low.irr_pct

    def test_lifetime_co2(self):
        r = _project()
        # For wind (no degradation), lifetime = annual * 25
        assert r.lifetime_co2_avoided_tonnes > r.co2_avoided_tonnes_yr

    def test_capex_override(self):
        normal = _project()
        override = _project(capex_override_eur=10_000_000)
        assert override.total_capex_eur == 10_000_000.0
        assert override.total_capex_eur != normal.total_capex_eur

    def test_payback_positive(self):
        r = _project(ppa_price_eur_mwh=80)
        assert r.payback_years > 0


# ========================================================================
# PPA Risk Scorer
# ========================================================================

class TestPPARiskScorer:
    def test_basic_score(self):
        r = PPARiskScorer().score_ppa(_ppa_input())
        assert isinstance(r, PPARiskResult)
        assert 0 <= r.composite_score <= 100

    def test_five_dimensions(self):
        r = PPARiskScorer().score_ppa(_ppa_input())
        assert len(r.dimension_scores) == 5
        dims = {d.dimension for d in r.dimension_scores}
        assert dims == {"counterparty_credit", "price_structure", "tenor", "curtailment", "regulatory"}

    def test_low_risk_bankable(self):
        r = PPARiskScorer().score_ppa(_ppa_input(
            offtaker_credit_rating="AAA",
            price_structure="fixed",
            tenor_years=20,
            curtailment_risk="low",
            regulatory_risk="stable",
        ))
        assert r.risk_band == "low"
        assert r.bankability_rating == "bankable"

    def test_high_risk_non_bankable(self):
        r = PPARiskScorer().score_ppa(_ppa_input(
            offtaker_credit_rating="CCC",
            price_structure="full_merchant",
            tenor_years=2,
            curtailment_risk="very_high",
            regulatory_risk="very_high",
        ))
        assert r.composite_score > 50
        assert r.bankability_rating == "non_bankable"

    def test_merchant_exposure_increases_price_risk(self):
        base = PPARiskScorer().score_ppa(_ppa_input(merchant_exposure_pct=0))
        high = PPARiskScorer().score_ppa(_ppa_input(merchant_exposure_pct=60))
        base_price = next(d for d in base.dimension_scores if d.dimension == "price_structure")
        high_price = next(d for d in high.dimension_scores if d.dimension == "price_structure")
        assert high_price.raw_score > base_price.raw_score

    def test_subsidy_dependence_increases_reg_risk(self):
        base = PPARiskScorer().score_ppa(_ppa_input(subsidy_dependence_pct=0))
        high = PPARiskScorer().score_ppa(_ppa_input(subsidy_dependence_pct=70))
        base_reg = next(d for d in base.dimension_scores if d.dimension == "regulatory")
        high_reg = next(d for d in high.dimension_scores if d.dimension == "regulatory")
        assert high_reg.raw_score > base_reg.raw_score

    def test_short_tenor_risk_factor(self):
        r = PPARiskScorer().score_ppa(_ppa_input(tenor_years=3))
        assert any("Short PPA tenor" in f for f in r.risk_factors)

    def test_mitigation_present_for_high_risk(self):
        r = PPARiskScorer().score_ppa(_ppa_input(
            offtaker_credit_rating="unrated",
            curtailment_risk="high",
        ))
        assert len(r.mitigation_suggestions) > 0

    def test_weights_sum_to_one(self):
        total = sum(PPA_RISK_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=0.001)

    def test_weighted_score_matches(self):
        r = PPARiskScorer().score_ppa(_ppa_input())
        for d in r.dimension_scores:
            expected = round(d.raw_score * d.weight, 2)
            assert d.weighted_score == expected

    def test_composite_is_sum_of_weighted(self):
        r = PPARiskScorer().score_ppa(_ppa_input())
        expected = round(sum(d.weighted_score for d in r.dimension_scores), 1)
        assert r.composite_score == expected


# ========================================================================
# PPA Risk Bands
# ========================================================================

class TestPPARiskBands:
    def test_low_band(self):
        # AAA + fixed + long tenor + low curtailment + stable regulation
        r = PPARiskScorer().score_ppa(_ppa_input(
            offtaker_credit_rating="AAA",
            price_structure="feed_in_tariff",
            tenor_years=20,
            curtailment_risk="low",
            regulatory_risk="stable",
        ))
        assert r.risk_band == "low"

    def test_critical_band(self):
        r = PPARiskScorer().score_ppa(_ppa_input(
            offtaker_credit_rating="CCC",
            price_structure="full_merchant",
            tenor_years=2,
            curtailment_risk="very_high",
            regulatory_risk="very_high",
            merchant_exposure_pct=50,
        ))
        assert r.risk_band == "critical"


# ========================================================================
# Reference Data Lookups
# ========================================================================

class TestReferenceData:
    def test_turbine_classes_populated(self):
        assert len(TURBINE_CLASSES) == 5
        for tc in TURBINE_CLASSES.values():
            assert "capacity_mw" in tc
            assert "capex_eur_per_kw" in tc

    def test_wind_regions_populated(self):
        assert len(WIND_RESOURCE_REGIONS) == 15
        for wr in WIND_RESOURCE_REGIONS.values():
            assert "k" in wr
            assert "lambda" in wr

    def test_solar_ghi_populated(self):
        assert len(SOLAR_GHI_DATA) == 20
        for sg in SOLAR_GHI_DATA.values():
            assert sg["ghi"] > 0

    def test_credit_scores_populated(self):
        assert len(CREDIT_SCORES) == 12
        assert CREDIT_SCORES["AAA"] < CREDIT_SCORES["CCC"]

    def test_price_structure_scores(self):
        assert PRICE_STRUCTURE_SCORES["fixed"] < PRICE_STRUCTURE_SCORES["full_merchant"]

    def test_tenor_risk_data(self):
        assert len(TENOR_RISK) == 3
        assert TENOR_RISK["short"]["score"] > TENOR_RISK["long"]["score"]

    def test_curtailment_risk_data(self):
        assert len(CURTAILMENT_RISK) == 4

    def test_regulatory_risk_data(self):
        assert len(REGULATORY_RISK) == 4


# ========================================================================
# Tenor Score Edge Cases
# ========================================================================

class TestTenorScore:
    def test_short_tenor(self):
        r = PPARiskScorer().score_ppa(_ppa_input(tenor_years=3))
        tenor_dim = next(d for d in r.dimension_scores if d.dimension == "tenor")
        assert tenor_dim.raw_score == 40

    def test_medium_tenor(self):
        r = PPARiskScorer().score_ppa(_ppa_input(tenor_years=10))
        tenor_dim = next(d for d in r.dimension_scores if d.dimension == "tenor")
        assert tenor_dim.raw_score == 20

    def test_long_tenor(self):
        r = PPARiskScorer().score_ppa(_ppa_input(tenor_years=20))
        tenor_dim = next(d for d in r.dimension_scores if d.dimension == "tenor")
        assert tenor_dim.raw_score == 10

    def test_boundary_5_years(self):
        # 5 years is >= min_yr for medium (5), so should be medium (score 20)
        r = PPARiskScorer().score_ppa(_ppa_input(tenor_years=5))
        tenor_dim = next(d for d in r.dimension_scores if d.dimension == "tenor")
        assert tenor_dim.raw_score == 20

    def test_boundary_15_years(self):
        # 15 years is >= min_yr for long (15), so should be long (score 10)
        r = PPARiskScorer().score_ppa(_ppa_input(tenor_years=15))
        tenor_dim = next(d for d in r.dimension_scores if d.dimension == "tenor")
        assert tenor_dim.raw_score == 10
