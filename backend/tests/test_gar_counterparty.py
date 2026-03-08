"""
Unit tests for GAR Calculator and Counterparty Climate Scorer.

Test classes:
  GAR:
    TestGARBasic         - Simple portfolio: 3 aligned + 7 non-aligned loans
    TestGARObjectives    - Multi-objective alignment breakdown
    TestGARExclusions    - Sovereign bonds excluded from denominator
    TestGARKPITypes      - Turnover vs CapEx vs OpEx GAR

  Counterparty Climate Scorer:
    TestCounterpartyBasic      - High-risk Oil & Gas vs low-risk Tech
    TestCounterpartyComponents - Each of the 4 components independently
    TestCounterpartyRating     - Verify A+ through D- mapping
    TestCounterpartyBatch      - Batch of 10 counterparties
    TestEdgeCases              - All excluded, zero exposures, perfect score
"""
import pytest

from services.gar_calculator import (
    GARCalculator,
    GARExposure,
    GARResult,
    EXCLUDED_ASSET_TYPES,
    NACE_TAXONOMY_MAP,
    get_eligible_objectives,
)
from services.counterparty_climate_scorer import (
    CounterpartyClimateScorer,
    CounterpartyInput,
    ClimateScoreResult,
    SECTOR_TRANSITION_RISK,
    RATING_MAP,
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------


@pytest.fixture
def gar_calc():
    return GARCalculator()


@pytest.fixture
def scorer():
    return CounterpartyClimateScorer()


def _make_exposure(**kwargs) -> GARExposure:
    """Helper to create a GARExposure with defaults."""
    defaults = {
        "exposure_id": "EXP001",
        "counterparty_name": "Test Corp",
        "asset_type": "NFC_LOAN",
        "gross_carrying_amount": 1_000_000,
        "classification": "NOT_ELIGIBLE",
        "sector": "Technology",
        "country": "DE",
    }
    defaults.update(kwargs)
    return GARExposure(**defaults)


def _make_counterparty(**kwargs) -> CounterpartyInput:
    """Helper to create a CounterpartyInput with defaults."""
    defaults = {
        "counterparty_id": "CP001",
        "counterparty_name": "Test Corp",
        "sector": "Technology",
        "country": "DE",
    }
    defaults.update(kwargs)
    return CounterpartyInput(**defaults)


# ===========================================================================
# GAR CALCULATOR TESTS
# ===========================================================================


class TestGARBasic:
    """Simple portfolio: 3 aligned + 7 non-aligned NFC loans."""

    def test_three_aligned_seven_not(self, gar_calc):
        exposures = []
        # 3 aligned loans at 1M each
        for i in range(3):
            exposures.append(
                _make_exposure(
                    exposure_id=f"AL{i}",
                    gross_carrying_amount=1_000_000,
                    classification="TAXONOMY_ALIGNED",
                    primary_objective="CLIMATE_MITIGATION",
                )
            )
        # 7 non-aligned loans at 1M each
        for i in range(7):
            exposures.append(
                _make_exposure(
                    exposure_id=f"NA{i}",
                    gross_carrying_amount=1_000_000,
                    classification="NOT_ELIGIBLE",
                )
            )

        result = gar_calc.calculate(exposures)

        assert result.total_assets == 10_000_000
        assert result.covered_assets == 10_000_000
        assert result.excluded_assets == 0
        assert result.aligned_assets == 3_000_000
        assert result.gar_ratio == pytest.approx(0.3, abs=0.001)
        assert result.exposure_count == 10

    def test_all_aligned(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id=f"AL{i}",
                gross_carrying_amount=500_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
            )
            for i in range(5)
        ]
        result = gar_calc.calculate(exposures)
        assert result.gar_ratio == pytest.approx(1.0, abs=0.001)

    def test_none_aligned(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id=f"NA{i}",
                gross_carrying_amount=1_000_000,
                classification="NOT_ELIGIBLE",
            )
            for i in range(4)
        ]
        result = gar_calc.calculate(exposures)
        assert result.gar_ratio == 0.0
        assert result.aligned_assets == 0

    def test_eligible_not_aligned_counted_in_eligible(self, gar_calc):
        exposures = [
            _make_exposure(
                classification="TAXONOMY_ELIGIBLE",
                primary_objective="CLIMATE_MITIGATION",
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.aligned_assets == 0
        assert result.eligible_assets == 1_000_000
        assert result.gar_ratio == 0.0
        assert result.gar_eligible_ratio == pytest.approx(1.0, abs=0.001)


class TestGARObjectives:
    """Multi-objective alignment breakdown."""

    def test_two_objectives(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="MIT1",
                gross_carrying_amount=5_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
            ),
            _make_exposure(
                exposure_id="WAT1",
                gross_carrying_amount=3_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="WATER",
            ),
            _make_exposure(
                exposure_id="NE1",
                gross_carrying_amount=2_000_000,
                classification="NOT_ELIGIBLE",
            ),
        ]
        result = gar_calc.calculate(exposures)

        # Find objective breakdowns
        mit = next(o for o in result.by_objective if o.objective == "CLIMATE_MITIGATION")
        wat = next(o for o in result.by_objective if o.objective == "WATER")

        assert mit.aligned_amount == 5_000_000
        assert wat.aligned_amount == 3_000_000
        assert result.aligned_assets == 8_000_000
        assert result.gar_ratio == pytest.approx(0.8, abs=0.01)

    def test_all_six_objectives_present(self, gar_calc):
        exposures = [_make_exposure()]
        result = gar_calc.calculate(exposures)
        objectives_in_result = [o.objective for o in result.by_objective]
        assert len(objectives_in_result) == 6
        assert "CLIMATE_MITIGATION" in objectives_in_result
        assert "BIODIVERSITY" in objectives_in_result

    def test_objective_pct_calculation(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="A1",
                gross_carrying_amount=2_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CIRCULAR_ECONOMY",
            ),
            _make_exposure(
                exposure_id="A2",
                gross_carrying_amount=8_000_000,
                classification="NOT_ELIGIBLE",
            ),
        ]
        result = gar_calc.calculate(exposures)
        ce = next(o for o in result.by_objective if o.objective == "CIRCULAR_ECONOMY")
        assert ce.aligned_pct == pytest.approx(20.0, abs=0.1)


class TestGARExclusions:
    """Sovereign bonds and other excluded types removed from denominator."""

    def test_sovereign_excluded(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="SOV1",
                asset_type="SOVEREIGN",
                gross_carrying_amount=50_000_000,
            ),
            _make_exposure(
                exposure_id="NFC1",
                asset_type="NFC_LOAN",
                gross_carrying_amount=10_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
            ),
        ]
        result = gar_calc.calculate(exposures)

        assert result.total_assets == 60_000_000
        assert result.excluded_assets == 50_000_000
        assert result.covered_assets == 10_000_000
        assert result.aligned_assets == 10_000_000
        assert result.gar_ratio == pytest.approx(1.0, abs=0.001)

    def test_central_bank_excluded(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="CB1",
                asset_type="CENTRAL_BANK",
                gross_carrying_amount=100_000_000,
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.excluded_assets == 100_000_000
        assert result.covered_assets == 0

    def test_interbank_excluded(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="IB1",
                asset_type="INTERBANK",
                gross_carrying_amount=20_000_000,
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.excluded_assets == 20_000_000
        assert result.covered_assets == 0

    def test_hedging_derivative_excluded(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="HD1",
                asset_type="HEDGING_DERIVATIVE",
                gross_carrying_amount=5_000_000,
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.excluded_assets == 5_000_000
        assert result.covered_assets == 0

    def test_mixed_excluded_and_covered(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="SOV", asset_type="SOVEREIGN",
                gross_carrying_amount=100_000_000,
            ),
            _make_exposure(
                exposure_id="CB", asset_type="CENTRAL_BANK",
                gross_carrying_amount=50_000_000,
            ),
            _make_exposure(
                exposure_id="IB", asset_type="INTERBANK",
                gross_carrying_amount=25_000_000,
            ),
            _make_exposure(
                exposure_id="NFC1", asset_type="NFC_LOAN",
                gross_carrying_amount=20_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
            ),
            _make_exposure(
                exposure_id="NFC2", asset_type="NFC_LOAN",
                gross_carrying_amount=80_000_000,
                classification="NOT_ELIGIBLE",
            ),
        ]
        result = gar_calc.calculate(exposures)

        assert result.total_assets == 275_000_000
        assert result.excluded_assets == 175_000_000
        assert result.covered_assets == 100_000_000
        assert result.aligned_assets == 20_000_000
        assert result.gar_ratio == pytest.approx(0.2, abs=0.01)

    def test_excluded_types_constant(self):
        assert "SOVEREIGN" in EXCLUDED_ASSET_TYPES
        assert "CENTRAL_BANK" in EXCLUDED_ASSET_TYPES
        assert "INTERBANK" in EXCLUDED_ASSET_TYPES
        assert "HEDGING_DERIVATIVE" in EXCLUDED_ASSET_TYPES
        assert "NFC_LOAN" not in EXCLUDED_ASSET_TYPES


class TestGARKPITypes:
    """Turnover vs CapEx vs OpEx GAR per CRR2 ITS."""

    def test_turnover_gar(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="T1",
                gross_carrying_amount=10_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
                turnover_aligned=8_000_000,
                turnover_eligible=10_000_000,
            ),
            _make_exposure(
                exposure_id="T2",
                gross_carrying_amount=10_000_000,
                classification="NOT_ELIGIBLE",
            ),
        ]
        result = gar_calc.calculate(exposures)

        turnover_kpi = next(k for k in result.by_kpi_type if k.kpi_type == "TURNOVER")
        assert turnover_kpi.aligned_amount == 8_000_000
        assert turnover_kpi.eligible_amount == 10_000_000
        assert turnover_kpi.gar_ratio == pytest.approx(0.4, abs=0.01)

    def test_capex_gar(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="C1",
                gross_carrying_amount=5_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
                capex_aligned=3_000_000,
                capex_eligible=5_000_000,
            ),
        ]
        result = gar_calc.calculate(exposures)

        capex_kpi = next(k for k in result.by_kpi_type if k.kpi_type == "CAPEX")
        assert capex_kpi.aligned_amount == 3_000_000

    def test_opex_gar(self, gar_calc):
        exposures = [
            _make_exposure(
                exposure_id="O1",
                gross_carrying_amount=5_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
                opex_aligned=1_000_000,
                opex_eligible=2_000_000,
            ),
        ]
        result = gar_calc.calculate(exposures)

        opex_kpi = next(k for k in result.by_kpi_type if k.kpi_type == "OPEX")
        assert opex_kpi.aligned_amount == 1_000_000
        assert opex_kpi.eligible_amount == 2_000_000

    def test_all_three_kpi_types_present(self, gar_calc):
        exposures = [_make_exposure()]
        result = gar_calc.calculate(exposures)
        kpi_types = [k.kpi_type for k in result.by_kpi_type]
        assert "TURNOVER" in kpi_types
        assert "CAPEX" in kpi_types
        assert "OPEX" in kpi_types

    def test_different_kpi_ratios(self, gar_calc):
        """Same loan book can have different GAR by KPI type."""
        exposures = [
            _make_exposure(
                exposure_id="M1",
                gross_carrying_amount=10_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
                turnover_aligned=7_000_000,
                turnover_eligible=10_000_000,
                capex_aligned=9_000_000,
                capex_eligible=10_000_000,
                opex_aligned=2_000_000,
                opex_eligible=4_000_000,
            ),
        ]
        result = gar_calc.calculate(exposures)

        t = next(k for k in result.by_kpi_type if k.kpi_type == "TURNOVER")
        c = next(k for k in result.by_kpi_type if k.kpi_type == "CAPEX")
        o = next(k for k in result.by_kpi_type if k.kpi_type == "OPEX")

        # CapEx GAR > Turnover GAR > OpEx GAR
        assert c.gar_ratio > t.gar_ratio
        assert t.gar_ratio > o.gar_ratio


class TestGARNACEMapping:
    """NACE taxonomy mapping utility."""

    def test_known_nace_code(self):
        objs = get_eligible_objectives("D35.11")
        assert "CLIMATE_MITIGATION" in objs
        assert "CLIMATE_ADAPTATION" in objs

    def test_unknown_nace_code(self):
        objs = get_eligible_objectives("Z99.99")
        assert objs == []

    def test_map_has_at_least_20_codes(self):
        assert len(NACE_TAXONOMY_MAP) >= 20

    def test_all_objectives_represented(self):
        all_objs = set()
        for objs in NACE_TAXONOMY_MAP.values():
            all_objs.update(objs)
        assert "CLIMATE_MITIGATION" in all_objs
        assert "CLIMATE_ADAPTATION" in all_objs
        assert "WATER" in all_objs
        assert "CIRCULAR_ECONOMY" in all_objs
        assert "POLLUTION" in all_objs
        assert "BIODIVERSITY" in all_objs


class TestGARHouseholdAutoAssess:
    """Auto-assessment for household exposures (EPC, EV, renovation)."""

    def test_mortgage_epc_a_aligned(self, gar_calc):
        exposures = [
            _make_exposure(
                asset_type="HOUSEHOLD_MORTGAGE",
                gross_carrying_amount=400_000,
                classification="",  # trigger auto-assess
                epc_rating="A",
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.aligned_assets == 400_000

    def test_mortgage_epc_c_eligible(self, gar_calc):
        exposures = [
            _make_exposure(
                asset_type="HOUSEHOLD_MORTGAGE",
                gross_carrying_amount=300_000,
                classification="",
                epc_rating="C",
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.aligned_assets == 0
        assert result.eligible_assets == 300_000

    def test_ev_loan_aligned(self, gar_calc):
        exposures = [
            _make_exposure(
                asset_type="HOUSEHOLD_AUTO",
                gross_carrying_amount=45_000,
                classification="",
                is_ev_loan=True,
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.aligned_assets == 45_000

    def test_renovation_loan_aligned(self, gar_calc):
        exposures = [
            _make_exposure(
                asset_type="HOUSEHOLD_RENOVATION",
                gross_carrying_amount=80_000,
                classification="",
                is_renovation_loan=True,
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.aligned_assets == 80_000


class TestGARFlowGAR:
    """Flow GAR for new originations."""

    def test_flow_gar_calculation(self, gar_calc):
        stock = [
            _make_exposure(gross_carrying_amount=100_000_000),
        ]
        flow = [
            _make_exposure(
                exposure_id="F1",
                gross_carrying_amount=5_000_000,
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
            ),
            _make_exposure(
                exposure_id="F2",
                gross_carrying_amount=15_000_000,
                classification="NOT_ELIGIBLE",
            ),
        ]
        result = gar_calc.calculate(stock, flow)
        # Flow GAR = 5M / 20M = 25%
        assert result.gar_flow == pytest.approx(0.25, abs=0.01)


class TestGARUtilities:
    """Utility / static methods."""

    def test_taxonomy_objectives_count(self):
        objs = GARCalculator.get_taxonomy_objectives()
        assert len(objs) == 6

    def test_excluded_asset_types(self):
        excluded = GARCalculator.get_excluded_asset_types()
        assert "SOVEREIGN" in excluded
        assert "NFC_LOAN" not in excluded

    def test_kpi_types(self):
        kpis = GARCalculator.get_kpi_types()
        assert len(kpis) == 3
        codes = [k["code"] for k in kpis]
        assert "TURNOVER" in codes
        assert "CAPEX" in codes
        assert "OPEX" in codes

    def test_nace_taxonomy_map(self):
        m = GARCalculator.get_nace_taxonomy_map()
        assert len(m) >= 20
        assert "D35.11" in m


# ===========================================================================
# COUNTERPARTY CLIMATE SCORER TESTS
# ===========================================================================


class TestCounterpartyBasic:
    """High-risk Oil & Gas vs low-risk Technology."""

    def test_oil_gas_high_risk(self, scorer):
        inp = _make_counterparty(
            counterparty_name="PetroCorp",
            sector="Oil & Gas",
            carbon_intensity_rank=10,       # very carbon-heavy (low rank = bad)
            policy_exposure_score=15,       # heavily exposed
            technology_readiness=20,
            flood_risk=40,
            heat_stress=50,
            water_stress=30,
            supply_chain_exposure=35,
        )
        result = scorer.score(inp)
        # Oil & Gas with bad metrics should score low (bad)
        assert result.composite_score < 45
        assert result.rating in ("C", "D+", "D-")

    def test_tech_company_low_risk(self, scorer):
        inp = _make_counterparty(
            counterparty_name="GreenTech Inc",
            sector="Technology",
            carbon_intensity_rank=90,
            policy_exposure_score=85,
            technology_readiness=95,
            flood_risk=80,
            heat_stress=85,
            water_stress=90,
            supply_chain_exposure=80,
            sbti_committed=True,
            taxonomy_aligned_pct=60,
            transition_plan_quality=5,
            disclosure_level="full",
            data_recency_years=0.5,
            third_party_verified=True,
        )
        result = scorer.score(inp)
        # Tech with excellent metrics should score high
        assert result.composite_score > 70
        assert result.rating in ("A+", "A", "B+")

    def test_higher_is_better(self, scorer):
        """Confirm that higher score = better climate posture."""
        good = _make_counterparty(
            counterparty_id="GOOD",
            sector="Technology",
            carbon_intensity_rank=95,
            sbti_committed=True,
            taxonomy_aligned_pct=80,
            transition_plan_quality=5,
            disclosure_level="full",
            data_recency_years=0,
            third_party_verified=True,
        )
        bad = _make_counterparty(
            counterparty_id="BAD",
            sector="Oil & Gas",
            carbon_intensity_rank=5,
        )
        r_good = scorer.score(good)
        r_bad = scorer.score(bad)
        assert r_good.composite_score > r_bad.composite_score


class TestCounterpartyComponents:
    """Test each of the 4 components independently."""

    def test_transition_risk_component(self, scorer):
        # High carbon intensity rank = good transition score
        good_tr = _make_counterparty(
            carbon_intensity_rank=95,
            sector_risk_level="low",
            policy_exposure_score=90,
            technology_readiness=90,
        )
        bad_tr = _make_counterparty(
            carbon_intensity_rank=5,
            sector_risk_level="very_high",
            policy_exposure_score=10,
            technology_readiness=10,
        )
        r_good = scorer.score(good_tr)
        r_bad = scorer.score(bad_tr)
        assert r_good.transition_risk.raw_score > r_bad.transition_risk.raw_score

    def test_physical_risk_component(self, scorer):
        good_pr = _make_counterparty(
            flood_risk=95, heat_stress=90, water_stress=95, supply_chain_exposure=90,
        )
        bad_pr = _make_counterparty(
            flood_risk=10, heat_stress=15, water_stress=5, supply_chain_exposure=10,
        )
        r_good = scorer.score(good_pr)
        r_bad = scorer.score(bad_pr)
        assert r_good.physical_risk.raw_score > r_bad.physical_risk.raw_score

    def test_alignment_component(self, scorer):
        # sbti_committed=True -> +20, taxonomy_aligned_pct=100 -> +40, plan=5 -> +40 = 100
        best = _make_counterparty(
            sbti_committed=True,
            taxonomy_aligned_pct=100,
            transition_plan_quality=5,
        )
        worst = _make_counterparty(
            sbti_committed=False,
            taxonomy_aligned_pct=0,
            transition_plan_quality=1,
        )
        r_best = scorer.score(best)
        r_worst = scorer.score(worst)
        assert r_best.alignment.raw_score == 100.0
        assert r_worst.alignment.raw_score == 0.0

    def test_alignment_sbti_gives_20(self, scorer):
        with_sbti = _make_counterparty(sbti_committed=True)
        without_sbti = _make_counterparty(sbti_committed=False)
        r1 = scorer.score(with_sbti)
        r2 = scorer.score(without_sbti)
        diff = r1.alignment.sub_scores["sbti_committed"] - r2.alignment.sub_scores["sbti_committed"]
        assert diff == pytest.approx(20.0, abs=0.1)

    def test_data_quality_component(self, scorer):
        good_dq = _make_counterparty(
            disclosure_level="full",
            data_recency_years=0,
            third_party_verified=True,
        )
        bad_dq = _make_counterparty(
            disclosure_level="none",
            data_recency_years=5,
            third_party_verified=False,
        )
        r_good = scorer.score(good_dq)
        r_bad = scorer.score(bad_dq)
        assert r_good.data_quality.raw_score > r_bad.data_quality.raw_score

    def test_data_quality_verified_bonus(self, scorer):
        verified = _make_counterparty(third_party_verified=True)
        not_verified = _make_counterparty(third_party_verified=False)
        r1 = scorer.score(verified)
        r2 = scorer.score(not_verified)
        assert r1.data_quality.sub_scores["third_party_verified"] == 30.0
        assert r2.data_quality.sub_scores["third_party_verified"] == 0.0

    def test_disclosure_levels(self, scorer):
        full = _make_counterparty(disclosure_level="full")
        partial = _make_counterparty(disclosure_level="partial")
        none_ = _make_counterparty(disclosure_level="none")
        r_full = scorer.score(full)
        r_partial = scorer.score(partial)
        r_none = scorer.score(none_)
        assert r_full.data_quality.sub_scores["disclosure_level"] == 100.0
        assert r_partial.data_quality.sub_scores["disclosure_level"] == 50.0
        assert r_none.data_quality.sub_scores["disclosure_level"] == 0.0


class TestCounterpartyRating:
    """Verify A+ through D- mapping."""

    def test_rating_band_coverage(self):
        """Every integer 0-100 should map to exactly one rating."""
        scorer = CounterpartyClimateScorer()
        valid_ratings = {b["rating"] for b in RATING_MAP}
        for s in range(0, 101):
            rating, label = scorer._score_to_rating(float(s))
            assert rating in valid_ratings, f"Score {s} mapped to unknown rating {rating}"

    def test_a_plus_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(90)[0] == "A+"
        assert scorer._score_to_rating(100)[0] == "A+"

    def test_a_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(80)[0] == "A"
        assert scorer._score_to_rating(89)[0] == "A"

    def test_b_plus_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(70)[0] == "B+"
        assert scorer._score_to_rating(79)[0] == "B+"

    def test_b_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(60)[0] == "B"
        assert scorer._score_to_rating(69)[0] == "B"

    def test_c_plus_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(50)[0] == "C+"
        assert scorer._score_to_rating(59)[0] == "C+"

    def test_c_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(40)[0] == "C"
        assert scorer._score_to_rating(49)[0] == "C"

    def test_d_plus_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(30)[0] == "D+"
        assert scorer._score_to_rating(39)[0] == "D+"

    def test_d_minus_boundary(self):
        scorer = CounterpartyClimateScorer()
        assert scorer._score_to_rating(0)[0] == "D-"
        assert scorer._score_to_rating(29)[0] == "D-"

    def test_rating_scale_has_eight_bands(self):
        scale = CounterpartyClimateScorer.get_rating_scale()
        assert len(scale) == 8


class TestCounterpartyBatch:
    """Batch scoring of 10 counterparties."""

    def test_batch_ten_counterparties(self, scorer):
        sectors = [
            "Oil & Gas", "Coal Mining", "Technology", "Healthcare",
            "Real Estate", "Steel", "Airlines", "Retail",
            "Financial Services", "Agriculture",
        ]
        inputs = [
            _make_counterparty(
                counterparty_id=f"CP{i:03d}",
                counterparty_name=f"Company {i}",
                sector=sectors[i],
            )
            for i in range(10)
        ]
        results = scorer.score_batch(inputs)

        assert len(results) == 10
        for r in results:
            assert 0 <= r.composite_score <= 100
            assert r.rating in {b["rating"] for b in RATING_MAP}

    def test_batch_preserves_order(self, scorer):
        inputs = [
            _make_counterparty(counterparty_id=f"CP{i}", sector="Technology")
            for i in range(5)
        ]
        results = scorer.score_batch(inputs)
        for i, r in enumerate(results):
            assert r.counterparty_id == f"CP{i}"

    def test_batch_with_custom_weights(self):
        scorer = CounterpartyClimateScorer(weights={
            "transition_risk": 0.60,
            "physical_risk": 0.20,
            "alignment": 0.10,
            "data_quality": 0.10,
        })
        inputs = [
            _make_counterparty(counterparty_id="W1", sector="Oil & Gas"),
            _make_counterparty(counterparty_id="W2", sector="Technology"),
        ]
        results = scorer.score_batch(inputs)
        assert len(results) == 2

    def test_batch_empty_raises(self, scorer):
        """Empty list should return empty list (not error)."""
        results = scorer.score_batch([])
        assert results == []


class TestEdgeCases:
    """All excluded assets, zero exposures, perfect score scenarios."""

    def test_all_excluded_assets(self, gar_calc):
        """Portfolio of only excluded types: covered_assets = 0, GAR = 0."""
        exposures = [
            _make_exposure(exposure_id="S1", asset_type="SOVEREIGN", gross_carrying_amount=50_000_000),
            _make_exposure(exposure_id="S2", asset_type="CENTRAL_BANK", gross_carrying_amount=30_000_000),
            _make_exposure(exposure_id="S3", asset_type="INTERBANK", gross_carrying_amount=20_000_000),
        ]
        result = gar_calc.calculate(exposures)
        assert result.covered_assets == 0
        assert result.gar_ratio == 0.0
        assert result.excluded_assets == 100_000_000
        assert result.exposure_count == 0

    def test_single_exposure(self, gar_calc):
        """Single aligned exposure: GAR = 100%."""
        exposures = [
            _make_exposure(
                classification="TAXONOMY_ALIGNED",
                primary_objective="CLIMATE_MITIGATION",
            ),
        ]
        result = gar_calc.calculate(exposures)
        assert result.gar_ratio == pytest.approx(1.0, abs=0.001)
        assert result.exposure_count == 1

    def test_very_large_portfolio(self, gar_calc):
        """100 exposures should work without error."""
        exposures = [
            _make_exposure(
                exposure_id=f"E{i:04d}",
                gross_carrying_amount=1_000_000,
                classification="TAXONOMY_ALIGNED" if i < 25 else "NOT_ELIGIBLE",
                primary_objective="CLIMATE_MITIGATION" if i < 25 else "",
            )
            for i in range(100)
        ]
        result = gar_calc.calculate(exposures)
        assert result.exposure_count == 100
        assert result.gar_ratio == pytest.approx(0.25, abs=0.01)

    def test_perfect_counterparty_score(self, scorer):
        """Counterparty with all best inputs should score near 100."""
        inp = _make_counterparty(
            sector="Technology",
            carbon_intensity_rank=100,
            sector_risk_level="low",
            policy_exposure_score=100,
            technology_readiness=100,
            flood_risk=100,
            heat_stress=100,
            water_stress=100,
            supply_chain_exposure=100,
            sbti_committed=True,
            taxonomy_aligned_pct=100,
            transition_plan_quality=5,
            disclosure_level="full",
            data_recency_years=0,
            third_party_verified=True,
        )
        result = scorer.score(inp)
        assert result.composite_score >= 90
        assert result.rating == "A+"

    def test_worst_counterparty_score(self, scorer):
        """Counterparty with all worst inputs should score near 0."""
        inp = _make_counterparty(
            sector="Coal Mining",
            carbon_intensity_rank=0,
            sector_risk_level="very_high",
            policy_exposure_score=0,
            technology_readiness=0,
            flood_risk=0,
            heat_stress=0,
            water_stress=0,
            supply_chain_exposure=0,
            sbti_committed=False,
            taxonomy_aligned_pct=0,
            transition_plan_quality=1,
            disclosure_level="none",
            data_recency_years=5,
            third_party_verified=False,
        )
        result = scorer.score(inp)
        assert result.composite_score <= 15
        assert result.rating == "D-"

    def test_scorer_weight_validation(self):
        """Weights that do not sum to 1.0 should raise ValueError."""
        with pytest.raises(ValueError):
            CounterpartyClimateScorer(weights={
                "transition_risk": 0.5,
                "physical_risk": 0.5,
                "alignment": 0.5,
                "data_quality": 0.5,
            })

    def test_scorer_default_weights_sum(self):
        """Default weights must sum to 1.0."""
        w = CounterpartyClimateScorer.get_default_weights()
        assert sum(w.values()) == pytest.approx(1.0)

    def test_sector_risk_levels(self):
        """Sector risk dict should have 15+ entries."""
        levels = CounterpartyClimateScorer.get_sector_risk_levels()
        assert len(levels) >= 15
        assert "Oil & Gas" in levels
        assert levels["Oil & Gas"] == "very_high"
        assert levels["Technology"] == "low"

    def test_gar_flow_no_flow_data(self, gar_calc):
        """No flow exposures: gar_flow should be 0."""
        exposures = [_make_exposure()]
        result = gar_calc.calculate(exposures, flow_exposures=None)
        assert result.gar_flow == 0.0

    def test_gar_methodology_notes_populated(self, gar_calc):
        exposures = [_make_exposure()]
        result = gar_calc.calculate(exposures)
        assert len(result.methodology_notes) > 0
        assert any("GAR" in n for n in result.methodology_notes)
