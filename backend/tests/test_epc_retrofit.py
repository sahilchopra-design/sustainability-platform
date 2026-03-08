"""
Tests for EPC Transition Risk Engine + Retrofit CapEx Planner
=============================================================
"""
import pytest
from decimal import Decimal

from services.epc_transition_engine import (
    EPCTransitionEngine,
    PropertyEPCInput,
    EPC_RANK,
    MEPS_TIMELINES,
)
from services.retrofit_planner import (
    RetrofitPlanner,
    PropertyRetrofitInput,
    MEASURE_CATALOGUE,
    RANK_TO_EPC,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def epc_engine():
    return EPCTransitionEngine()


@pytest.fixture
def planner():
    return RetrofitPlanner()


def _epc_prop(
    pid="P1", name="Test Office", country="GB", epc="D",
    area=5000, value=10_000_000, rent=500_000, age=1990
) -> PropertyEPCInput:
    return PropertyEPCInput(
        property_id=pid, name=name, country=country,
        epc_rating=epc, floor_area_m2=Decimal(str(area)),
        market_value=Decimal(str(value)), annual_rent=Decimal(str(rent)),
        building_age=age,
    )


def _retrofit_prop(
    pid="P1", name="Test Office", country="GB", ptype="office",
    area=5000.0, epc="D", eui=180.0, value=10_000_000.0, rent=500_000.0,
    target=None, discount=0.06, carbon=90.0, existing=None,
) -> PropertyRetrofitInput:
    return PropertyRetrofitInput(
        property_id=pid, name=name, country=country,
        property_type=ptype, floor_area_m2=area,
        current_epc=epc, current_energy_intensity_kwh_m2=eui,
        market_value=value, annual_rent=rent,
        target_epc=target, discount_rate=discount,
        carbon_price_eur_t=carbon,
        existing_measures=existing or [],
    )


# ===========================================================================
# EPC Transition Risk Engine Tests
# ===========================================================================

class TestEPCRankOrdering:
    def test_a_plus_is_best(self):
        assert EPC_RANK["A+"] < EPC_RANK["A"] < EPC_RANK["G"]

    def test_all_ratings_present(self):
        assert len(EPC_RANK) == 8


class TestPropertyTransitionRisk:
    def test_compliant_property_low_risk(self, epc_engine):
        prop = _epc_prop(epc="A", country="GB")
        result = epc_engine.assess_property(prop)
        assert result.risk_band == "Low"
        assert result.composite_risk_score == 0.0
        assert all(d.is_compliant for d in result.deadlines)

    def test_non_compliant_property_high_risk(self, epc_engine):
        prop = _epc_prop(epc="F", country="GB")
        result = epc_engine.assess_property(prop)
        assert result.risk_band in ("High", "Critical")
        assert result.composite_risk_score >= 50

    def test_first_non_compliant_year(self, epc_engine):
        prop = _epc_prop(epc="F", country="GB")
        result = epc_engine.assess_property(prop)
        assert result.first_non_compliant_year is not None
        assert result.first_non_compliant_year <= 2030

    def test_gap_steps_positive_when_below(self, epc_engine):
        prop = _epc_prop(epc="D", country="GB")
        result = epc_engine.assess_property(prop)
        assert result.worst_gap_steps > 0

    def test_gap_steps_zero_when_above(self, epc_engine):
        prop = _epc_prop(epc="A", country="GB")
        result = epc_engine.assess_property(prop)
        assert result.worst_gap_steps == 0

    def test_nl_requires_a_by_2030(self, epc_engine):
        prop = _epc_prop(epc="C", country="NL")
        result = epc_engine.assess_property(prop)
        # C is below A for NL 2030 deadline
        non_compliant = [d for d in result.deadlines if not d.is_compliant]
        assert len(non_compliant) >= 1

    def test_penalty_exposure_calculated(self, epc_engine):
        prop = _epc_prop(epc="G", country="GB", area=10000)
        result = epc_engine.assess_property(prop)
        assert result.total_annual_penalty_at_risk > 0


class TestDeadlineExposure:
    def test_years_remaining_positive(self, epc_engine):
        prop = _epc_prop(epc="E", country="GB")
        result = epc_engine.assess_property(prop)
        for d in result.deadlines:
            assert d.years_remaining >= 0

    def test_stranding_probability_zero_when_compliant(self, epc_engine):
        prop = _epc_prop(epc="A", country="GB")
        result = epc_engine.assess_property(prop)
        for d in result.deadlines:
            if d.is_compliant:
                assert d.stranding_probability == 0.0

    def test_stranding_probability_positive_when_non_compliant(self, epc_engine):
        prop = _epc_prop(epc="G", country="GB")
        result = epc_engine.assess_property(prop)
        non_compliant = [d for d in result.deadlines if not d.is_compliant]
        assert all(d.stranding_probability > 0 for d in non_compliant)


class TestPortfolioTransitionRisk:
    def test_portfolio_counts(self, epc_engine):
        props = [
            _epc_prop("P1", epc="A"),
            _epc_prop("P2", epc="D"),
            _epc_prop("P3", epc="G"),
        ]
        result = epc_engine.assess_portfolio(props)
        assert result.total_properties == 3
        assert result.compliant_now_count >= 1  # At least EPC A is compliant

    def test_risk_distribution_sums(self, epc_engine):
        props = [
            _epc_prop("P1", epc="A"),
            _epc_prop("P2", epc="C"),
            _epc_prop("P3", epc="E"),
            _epc_prop("P4", epc="G"),
        ]
        result = epc_engine.assess_portfolio(props)
        total = sum(result.risk_distribution.values())
        assert total == 4

    def test_empty_portfolio(self, epc_engine):
        result = epc_engine.assess_portfolio([])
        assert result.total_properties == 0
        assert result.avg_composite_score == 0

    def test_worst_properties_sorted(self, epc_engine):
        props = [_epc_prop(f"P{i}", epc=epc) for i, epc in enumerate(["A", "C", "F", "G"])]
        result = epc_engine.assess_portfolio(props)
        scores = [w["score"] for w in result.worst_properties]
        assert scores == sorted(scores, reverse=True)

    def test_gav_at_risk_2030(self, epc_engine):
        props = [
            _epc_prop("P1", epc="A", value=5_000_000),
            _epc_prop("P2", epc="F", value=3_000_000),  # Non-compliant
        ]
        result = epc_engine.assess_portfolio(props)
        assert result.gav_at_risk_2030 >= 3_000_000  # At least the F-rated property

    def test_at_risk_pct_bounded(self, epc_engine):
        props = [_epc_prop(f"P{i}", epc="G") for i in range(5)]
        result = epc_engine.assess_portfolio(props)
        assert 0 <= result.at_risk_2030_pct <= 100
        assert 0 <= result.at_risk_2033_pct <= 100


class TestCompositeScore:
    def test_score_bounded(self, epc_engine):
        for epc in ["A+", "A", "B", "C", "D", "E", "F", "G"]:
            prop = _epc_prop(epc=epc)
            result = epc_engine.assess_property(prop)
            assert 0 <= result.composite_risk_score <= 100

    def test_worse_epc_higher_score(self, epc_engine):
        score_a = epc_engine.assess_property(_epc_prop(epc="A")).composite_risk_score
        score_g = epc_engine.assess_property(_epc_prop(epc="G")).composite_risk_score
        assert score_g > score_a

    def test_country_certainty_affects_score(self, epc_engine):
        # NL has higher regulatory certainty than EU default
        nl = epc_engine.assess_property(_epc_prop(epc="E", country="NL"))
        eu = epc_engine.assess_property(_epc_prop(epc="E", country="XX"))  # Falls to EU
        # Both should have risk, but NL should be somewhat higher due to certainty
        assert nl.regulatory_certainty >= eu.regulatory_certainty


class TestCountryTimelines:
    def test_all_countries_have_timelines(self):
        for country in ["NL", "GB", "FR", "DE", "EU"]:
            assert country in MEPS_TIMELINES
            assert len(MEPS_TIMELINES[country]) >= 2

    def test_unknown_country_uses_eu_fallback(self, epc_engine):
        prop = _epc_prop(epc="F", country="ZZ")
        result = epc_engine.assess_property(prop)
        assert result.country == "ZZ"
        assert len(result.deadlines) == len(MEPS_TIMELINES["EU"])


# ===========================================================================
# Retrofit Planner Tests
# ===========================================================================

class TestMeasureCatalogue:
    def test_catalogue_not_empty(self):
        assert len(MEASURE_CATALOGUE) >= 5

    def test_all_measures_have_positive_capex(self):
        for m in MEASURE_CATALOGUE:
            assert m.capex_eur_m2 > 0

    def test_all_measures_have_savings(self):
        for m in MEASURE_CATALOGUE:
            assert m.energy_saving_kwh_m2 > 0


class TestSinglePropertyRetrofit:
    def test_basic_plan_has_measures(self, planner):
        prop = _retrofit_prop(epc="F", target="B")
        plan = planner.plan_property(prop)
        assert len(plan.measures) > 0
        assert plan.total_capex > 0

    def test_total_capex_is_sum_of_measures(self, planner):
        prop = _retrofit_prop(epc="E")
        plan = planner.plan_property(prop)
        expected = sum(m.capex_total for m in plan.measures)
        assert abs(plan.total_capex - expected) < 0.01

    def test_projected_epc_improves(self, planner):
        prop = _retrofit_prop(epc="G", target="B")
        plan = planner.plan_property(prop)
        current_rank = EPC_RANK[plan.current_epc]
        projected_rank = EPC_RANK.get(plan.projected_epc_after_retrofit, 8)
        assert projected_rank <= current_rank  # Lower rank = better

    def test_measures_sorted_by_roi(self, planner):
        prop = _retrofit_prop(epc="F", target="B")
        plan = planner.plan_property(prop)
        rois = [m.roi_pct for m in plan.measures]
        assert rois == sorted(rois, reverse=True)

    def test_green_value_uplift(self, planner):
        prop = _retrofit_prop(epc="G", target="B", value=10_000_000)
        plan = planner.plan_property(prop)
        assert plan.green_value_uplift_pct > 0
        assert plan.green_value_uplift_eur > 0

    def test_energy_reduction_bounded(self, planner):
        prop = _retrofit_prop(epc="G")
        plan = planner.plan_property(prop)
        assert 0 <= plan.energy_reduction_pct <= 100

    def test_already_at_target_still_returns_measures(self, planner):
        prop = _retrofit_prop(epc="A", target="B")
        plan = planner.plan_property(prop)
        # Already better than target — returns top positive-NPV measures
        assert plan.projected_epc_after_retrofit in ("A+", "A")

    def test_existing_measures_excluded(self, planner):
        prop = _retrofit_prop(epc="F", existing=["LED", "BMS"])
        plan = planner.plan_property(prop)
        measure_ids = [m.measure_id for m in plan.measures]
        assert "LED" not in measure_ids
        assert "BMS" not in measure_ids


class TestNPVAndPayback:
    def test_simple_payback_positive(self, planner):
        prop = _retrofit_prop(epc="E")
        plan = planner.plan_property(prop)
        for m in plan.measures:
            assert m.simple_payback_years > 0

    def test_npv_can_be_positive(self, planner):
        prop = _retrofit_prop(epc="F", discount=0.04)  # Low discount rate favours NPV
        plan = planner.plan_property(prop)
        positive_npv = [m for m in plan.measures if m.npv > 0]
        assert len(positive_npv) > 0

    def test_irr_calculated(self, planner):
        prop = _retrofit_prop(epc="F")
        plan = planner.plan_property(prop)
        with_irr = [m for m in plan.measures if m.irr is not None]
        assert len(with_irr) > 0

    def test_high_discount_lowers_npv(self, planner):
        prop_low = _retrofit_prop(epc="E", discount=0.04)
        prop_high = _retrofit_prop(epc="E", discount=0.12)
        plan_low = planner.plan_property(prop_low)
        plan_high = planner.plan_property(prop_high)
        npv_low = plan_low.aggregate_npv
        npv_high = plan_high.aggregate_npv
        assert npv_low > npv_high


class TestPortfolioRetrofit:
    def test_portfolio_totals(self, planner):
        props = [
            _retrofit_prop("P1", epc="D", area=5000),
            _retrofit_prop("P2", epc="F", area=3000),
            _retrofit_prop("P3", epc="G", area=8000),
        ]
        result = planner.plan_portfolio(props)
        assert result.total_properties == 3
        assert result.total_capex_required > 0
        assert result.total_annual_savings > 0

    def test_capex_by_category(self, planner):
        props = [_retrofit_prop("P1", epc="F")]
        result = planner.plan_portfolio(props)
        assert len(result.capex_by_category) > 0
        total_cat = sum(result.capex_by_category.values())
        assert abs(total_cat - result.total_capex_required) < 1.0

    def test_top_roi_sorted(self, planner):
        props = [
            _retrofit_prop(f"P{i}", epc=epc, area=a)
            for i, (epc, a) in enumerate([("D", 5000), ("F", 3000), ("G", 8000)])
        ]
        result = planner.plan_portfolio(props)
        rois = [p["roi_pct"] for p in result.top_roi_properties]
        assert rois == sorted(rois, reverse=True)

    def test_empty_portfolio(self, planner):
        result = planner.plan_portfolio([])
        assert result.total_properties == 0
        assert result.total_capex_required == 0

    def test_portfolio_payback_reasonable(self, planner):
        props = [_retrofit_prop("P1", epc="E")]
        result = planner.plan_portfolio(props)
        assert result.portfolio_simple_payback < 30  # Should be < 30 years for reasonable measures


class TestCarbonPriceImpact:
    def test_higher_carbon_price_increases_savings(self, planner):
        prop_low = _retrofit_prop(epc="F", carbon=50.0)
        prop_high = _retrofit_prop(epc="F", carbon=150.0)
        plan_low = planner.plan_property(prop_low)
        plan_high = planner.plan_property(prop_high)
        # Higher carbon price -> higher annual savings
        assert plan_high.total_annual_saving > plan_low.total_annual_saving

    def test_zero_carbon_price_only_energy_savings(self, planner):
        prop = _retrofit_prop(epc="F", carbon=0.0)
        plan = planner.plan_property(prop)
        for m in plan.measures:
            assert m.annual_carbon_cost_saving == 0.0
            assert m.annual_energy_cost_saving > 0


class TestPropertyTypeApplicability:
    def test_industrial_excludes_windows(self, planner):
        prop = _retrofit_prop(epc="F", ptype="industrial")
        plan = planner.plan_property(prop)
        measure_ids = [m.measure_id for m in plan.measures]
        # Windows measure doesn't list 'industrial' in applicability
        assert "WINDOWS" not in measure_ids

    def test_office_includes_bms(self, planner):
        prop = _retrofit_prop(epc="F", ptype="office")
        plan = planner.plan_property(prop)
        measure_ids = [m.measure_id for m in plan.measures]
        assert "BMS" in measure_ids
