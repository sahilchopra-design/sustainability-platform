"""
Tests for ESG Attribution Engine + Benchmark Analytics
=======================================================
"""
import pytest

from services.esg_attribution_engine import (
    ESGAttributionEngine,
    AttributionInput,
    HoldingAttribution,
    BenchmarkAttribution,
    PAIIndicator,
)
from services.benchmark_analytics import (
    BenchmarkAnalyticsService,
    PeerFundMetrics,
    MANDATORY_PAI_INDICATORS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def attr_engine():
    return ESGAttributionEngine()


@pytest.fixture
def bench_service():
    return BenchmarkAnalyticsService()


def _h(hid="H1", sector="Technology", weight=50.0, ci=100.0, esg=70.0,
       tax=30.0, isin="US0001111111") -> HoldingAttribution:
    return HoldingAttribution(
        holding_id=hid, security_name=f"Stock {hid}",
        isin=isin, sector=sector, weight_pct=weight,
        carbon_intensity=ci, esg_score=esg, taxonomy_aligned_pct=tax,
    )


def _b(sector="Technology", weight=50.0, ci=120.0, esg=65.0,
       tax=25.0, isin="US0001111111") -> BenchmarkAttribution:
    return BenchmarkAttribution(
        security_name=f"Bench {sector}", isin=isin, sector=sector,
        weight_pct=weight, carbon_intensity=ci, esg_score=esg,
        taxonomy_aligned_pct=tax,
    )


def _input(port=None, bench=None, pai=None, prior_waci=None, prior_esg=None):
    return AttributionInput(
        fund_id="F1", fund_name="Test Fund",
        portfolio_holdings=port or [],
        benchmark_holdings=bench or [],
        pai_indicators=pai or [],
        prior_waci=prior_waci, prior_esg_score=prior_esg,
    )


def _peer(fid="P1", waci=120.0, esg=68.0, tax=25.0, active=40.0):
    return PeerFundMetrics(
        fund_id=fid, fund_name=f"Peer {fid}",
        sfdr_classification="art8",
        waci=waci, esg_score=esg,
        taxonomy_aligned_pct=tax, active_share_pct=active,
    )


# ===========================================================================
# ESG Attribution Engine
# ===========================================================================

class TestBrinsonFachlerCarbon:
    def test_identical_portfolio_zero_effects(self, attr_engine):
        port = [_h(sector="Technology", weight=100, ci=100)]
        bench = [_b(sector="Technology", weight=100, ci=100)]
        result = attr_engine.analyse(_input(port, bench))
        ca = result.carbon_attribution
        assert ca.active_metric == 0.0
        assert ca.total_allocation_effect == 0.0
        assert ca.total_selection_effect == 0.0
        assert ca.total_interaction_effect == 0.0

    def test_selection_effect_lower_carbon(self, attr_engine):
        # Same sector weights, different carbon intensity
        port = [_h(sector="Technology", weight=100, ci=80)]
        bench = [_b(sector="Technology", weight=100, ci=120)]
        result = attr_engine.analyse(_input(port, bench))
        ca = result.carbon_attribution
        # Port lower carbon = outperforming
        assert ca.is_outperforming is True
        assert ca.active_metric < 0  # 80 - 120 = -40
        assert ca.total_selection_effect < 0  # Selection drove improvement

    def test_allocation_effect_two_sectors(self, attr_engine):
        # Portfolio overweights low-carbon sector
        port = [
            _h("H1", sector="Technology", weight=70, ci=80),
            _h("H2", sector="Energy", weight=30, ci=200, isin="US0002222222"),
        ]
        bench = [
            _b(sector="Technology", weight=50, ci=80),
            _b(sector="Energy", weight=50, ci=200, isin="US0002222222"),
        ]
        result = attr_engine.analyse(_input(port, bench))
        ca = result.carbon_attribution
        # Port WACI = 0.7*80 + 0.3*200 = 56+60=116
        # Bench WACI = 0.5*80 + 0.5*200 = 40+100=140
        assert ca.portfolio_metric == 116.0
        assert ca.benchmark_metric == 140.0
        assert ca.is_outperforming is True  # Lower carbon

    def test_effects_sum_to_active(self, attr_engine):
        port = [
            _h("H1", sector="Technology", weight=60, ci=90, esg=75),
            _h("H2", sector="Healthcare", weight=40, ci=50, esg=85, isin="US0002222222"),
        ]
        bench = [
            _b(sector="Technology", weight=50, ci=120, esg=65),
            _b(sector="Healthcare", weight=50, ci=70, esg=80, isin="US0002222222"),
        ]
        result = attr_engine.analyse(_input(port, bench))
        ca = result.carbon_attribution
        # Verify decomposition sums to active
        total = ca.total_allocation_effect + ca.total_selection_effect + ca.total_interaction_effect
        assert abs(total - ca.active_metric) < 0.01


class TestBrinsonFachlerESG:
    def test_higher_esg_outperforms(self, attr_engine):
        port = [_h(weight=100, esg=80)]
        bench = [_b(weight=100, esg=65)]
        result = attr_engine.analyse(_input(port, bench))
        ea = result.esg_attribution
        assert ea.is_outperforming is True  # Higher ESG = better
        assert ea.active_metric == 15.0  # 80 - 65

    def test_taxonomy_attribution(self, attr_engine):
        port = [_h(weight=100, tax=40)]
        bench = [_b(weight=100, tax=25)]
        result = attr_engine.analyse(_input(port, bench))
        ta = result.taxonomy_attribution
        assert ta.is_outperforming is True
        assert ta.active_metric == 15.0


class TestActiveShareAndTE:
    def test_identical_isins_zero_active(self, attr_engine):
        port = [_h(weight=100, isin="US1111111111")]
        bench = [_b(weight=100, isin="US1111111111")]
        result = attr_engine.analyse(_input(port, bench))
        assert result.active_share_pct == 0.0

    def test_no_overlap_full_active(self, attr_engine):
        port = [_h(weight=100, isin="US1111111111")]
        bench = [_b(weight=100, isin="US9999999999")]
        result = attr_engine.analyse(_input(port, bench))
        assert result.active_share_pct == 100.0

    def test_tracking_error_different_sectors(self, attr_engine):
        port = [_h(weight=100, sector="Technology")]
        bench = [_b(weight=100, sector="Healthcare")]
        result = attr_engine.analyse(_input(port, bench))
        assert result.tracking_error_pct > 0


class TestInformationRatio:
    def test_carbon_ir_positive_when_outperforming(self, attr_engine):
        # Portfolio has lower carbon (outperforming) with sector difference for TE > 0
        port = [
            _h("H1", sector="Technology", weight=70, ci=80),
            _h("H2", sector="Energy", weight=30, ci=100, isin="US0002222222"),
        ]
        bench = [
            _b(sector="Technology", weight=50, ci=120),
            _b(sector="Energy", weight=50, ci=200, isin="US0002222222"),
        ]
        result = attr_engine.analyse(_input(port, bench))
        assert result.carbon_information_ratio > 0  # Positive = outperforming

    def test_esg_ir_positive_when_outperforming(self, attr_engine):
        port = [
            _h("H1", sector="Technology", weight=70, esg=85),
            _h("H2", sector="Energy", weight=30, esg=70, isin="US0002222222"),
        ]
        bench = [
            _b(sector="Technology", weight=50, esg=65),
            _b(sector="Energy", weight=50, esg=55, isin="US0002222222"),
        ]
        result = attr_engine.analyse(_input(port, bench))
        assert result.esg_information_ratio > 0


class TestPAIComparison:
    def test_pai_outperformance(self, attr_engine):
        pai = [
            PAIIndicator("PAI_1", "Scope 1", 100, 150, "tCO2e", "lower_is_better"),
            PAIIndicator("PAI_14", "Board Diversity", 40, 30, "%", "higher_is_better"),
            PAIIndicator("PAI_5", "WACI", 200, 180, "tCO2e/MEUR", "lower_is_better"),
        ]
        result = attr_engine.analyse(_input([_h()], [_b()], pai))
        assert result.pai_outperformance_count == 2  # PAI_1 and PAI_14
        assert result.pai_total_count == 3


class TestYoYChanges:
    def test_waci_yoy_decrease(self, attr_engine):
        port = [_h(weight=100, ci=90)]
        bench = [_b(weight=100)]
        result = attr_engine.analyse(_input(port, bench, prior_waci=100.0))
        assert result.waci_yoy_change_pct == -10.0  # 90 vs 100 = -10%

    def test_esg_yoy_increase(self, attr_engine):
        port = [_h(weight=100, esg=80)]
        bench = [_b(weight=100)]
        result = attr_engine.analyse(_input(port, bench, prior_esg=70.0))
        # (80-70)/70*100 = 14.29%
        assert abs(result.esg_yoy_change_pct - 14.29) < 0.1

    def test_no_prior_returns_none(self, attr_engine):
        result = attr_engine.analyse(_input([_h()], [_b()]))
        assert result.waci_yoy_change_pct is None
        assert result.esg_yoy_change_pct is None


# ===========================================================================
# Benchmark Analytics Service
# ===========================================================================

class TestPeerRankings:
    def test_best_waci_rank_1(self, bench_service):
        fund = _peer("F1", waci=80)
        peers = [_peer("P1", waci=120), _peer("P2", waci=150)]
        rankings = bench_service.compute_peer_rankings(fund, peers)
        waci_rank = next(r for r in rankings if r.metric_name == "waci")
        assert waci_rank.rank == 1  # Best (lowest) WACI

    def test_worst_esg_last(self, bench_service):
        fund = _peer("F1", esg=50)
        peers = [_peer("P1", esg=70), _peer("P2", esg=80)]
        rankings = bench_service.compute_peer_rankings(fund, peers)
        esg_rank = next(r for r in rankings if r.metric_name == "esg_score")
        assert esg_rank.rank == 3  # Worst (lowest) ESG

    def test_statistics_computed(self, bench_service):
        fund = _peer("F1", waci=100)
        peers = [_peer("P1", waci=80), _peer("P2", waci=120)]
        rankings = bench_service.compute_peer_rankings(fund, peers)
        waci_rank = next(r for r in rankings if r.metric_name == "waci")
        assert waci_rank.peer_count == 3
        assert waci_rank.peer_min == 80.0
        assert waci_rank.peer_max == 120.0
        assert waci_rank.peer_mean == 100.0


class TestPeriodComparison:
    def test_improvement_detected(self, bench_service):
        current = {"waci": 90.0, "esg_score": 75.0}
        prior = {"waci": 100.0, "esg_score": 70.0}
        directions = {"waci": "lower_is_better", "esg_score": "higher_is_better"}
        comps = bench_service.compute_period_comparison(current, prior, directions)
        for c in comps:
            assert c.improved is True

    def test_deterioration_detected(self, bench_service):
        current = {"waci": 110.0}
        prior = {"waci": 100.0}
        directions = {"waci": "lower_is_better"}
        comps = bench_service.compute_period_comparison(current, prior, directions)
        assert comps[0].improved is False
        assert comps[0].pct_change == 10.0

    def test_zero_prior_no_error(self, bench_service):
        current = {"waci": 100.0}
        prior = {"waci": 0.0}
        directions = {"waci": "lower_is_better"}
        comps = bench_service.compute_period_comparison(current, prior, directions)
        assert comps[0].pct_change == 0.0


class TestClimateBenchmarkCompliance:
    def test_ctb_aligned(self, bench_service):
        # 35% WACI reduction > 30% required
        result = bench_service.check_climate_benchmark_compliance(
            fund_waci=65.0, benchmark_waci=100.0,
            prior_waci=70.0,  # 7.14% YoY decarb
            fossil_fuel_pct=5.0, controversial_weapons_pct=0.0,
        )
        assert result.is_ctb_aligned is True
        assert result.waci_reduction_pct == 35.0

    def test_pab_aligned(self, bench_service):
        # 55% reduction, no fossil, no weapons
        result = bench_service.check_climate_benchmark_compliance(
            fund_waci=45.0, benchmark_waci=100.0,
            prior_waci=50.0,  # 10% decarb
            fossil_fuel_pct=0.0, controversial_weapons_pct=0.0,
        )
        assert result.is_pab_aligned is True

    def test_pab_fails_fossil_fuel(self, bench_service):
        result = bench_service.check_climate_benchmark_compliance(
            fund_waci=45.0, benchmark_waci=100.0,
            prior_waci=50.0, fossil_fuel_pct=5.0,
            controversial_weapons_pct=0.0,
        )
        assert result.is_pab_aligned is False
        assert any("Fossil fuel" in r for r in result.pab_reasons)

    def test_ctb_fails_insufficient_reduction(self, bench_service):
        result = bench_service.check_climate_benchmark_compliance(
            fund_waci=80.0, benchmark_waci=100.0,
            prior_waci=None, fossil_fuel_pct=0.0,
            controversial_weapons_pct=0.0,
        )
        assert result.is_ctb_aligned is False
        assert result.waci_reduction_pct == 20.0

    def test_yoy_decarb_insufficient(self, bench_service):
        result = bench_service.check_climate_benchmark_compliance(
            fund_waci=66.0, benchmark_waci=100.0,
            prior_waci=68.0,  # 2.94% < 7% required
            fossil_fuel_pct=0.0, controversial_weapons_pct=0.0,
        )
        assert result.is_ctb_aligned is False
        assert any("decarbonisation" in r for r in result.ctb_reasons)


class TestFullReport:
    def test_report_generation(self, bench_service):
        fund = _peer("F1", waci=90, esg=75, tax=35, active=45)
        peers = [
            _peer("P1", waci=110, esg=68, tax=28, active=38),
            _peer("P2", waci=130, esg=62, tax=22, active=50),
        ]
        current = {"waci": 90.0, "esg_score": 75.0}
        prior = {"waci": 100.0, "esg_score": 70.0}
        directions = {"waci": "lower_is_better", "esg_score": "higher_is_better"}

        report = bench_service.generate_report(
            fund=fund, peers=peers,
            current_metrics=current, prior_metrics=prior,
            metric_directions=directions,
            benchmark_waci=140.0,
        )
        assert report.fund_id == "F1"
        assert len(report.peer_rankings) == 4
        assert len(report.period_comparisons) == 2
        assert report.improvement_count == 2
        assert report.deterioration_count == 0
        assert report.benchmark_compliance.waci_reduction_pct > 30


class TestReferenceData:
    def test_mandatory_pai_count(self):
        assert len(MANDATORY_PAI_INDICATORS) == 18

    def test_pai_has_required_fields(self):
        for pai in MANDATORY_PAI_INDICATORS:
            assert "id" in pai
            assert "name" in pai
            assert "unit" in pai
            assert "direction" in pai
