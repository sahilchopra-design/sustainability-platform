"""
Tests for Fund Structure Engine
================================
"""
import pytest

from services.fund_structure_engine import (
    FundStructureEngine,
    FundDefinition,
    Holding,
    BenchmarkHolding,
    ShareClass,
    Investor,
    SFDRClassification,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return FundStructureEngine()


def _holding(
    hid="H1", name="Stock A", isin="US0001111111", ticker="STKA",
    asset_class="equity", sector="Technology", country="US",
    weight=10.0, mv=1_000_000, cost=900_000, qty=1000,
    ci=120.0, esg=72.0, tax_pct=30.0, dnsh=True,
    excl=False, excl_reason=None,
) -> Holding:
    return Holding(
        holding_id=hid, security_name=name, isin=isin, ticker=ticker,
        asset_class=asset_class, sector=sector, country=country,
        weight_pct=weight, market_value=mv, acquisition_cost=cost,
        quantity=qty, carbon_intensity=ci, esg_score=esg,
        taxonomy_aligned_pct=tax_pct, dnsh_compliant=dnsh,
        exclusion_flag=excl, exclusion_reason=excl_reason,
    )


def _bench_holding(
    name="Stock A", isin="US0001111111", sector="Technology",
    country="US", weight=10.0, ci=150.0, esg=65.0,
) -> BenchmarkHolding:
    return BenchmarkHolding(
        security_name=name, isin=isin, sector=sector,
        country=country, weight_pct=weight,
        carbon_intensity=ci, esg_score=esg,
    )


def _share_class(
    cid="SC1", name="Class A EUR Acc", isin="LU0001111111",
    currency="EUR", nav=100.0, shares=50000.0,
    ter=0.75, mgmt=0.50, perf=0.0, dist="acc",
) -> ShareClass:
    return ShareClass(
        class_id=cid, class_name=name, isin=isin,
        currency=currency, nav_per_share=nav, total_shares=shares,
        ter_pct=ter, management_fee_pct=mgmt,
        performance_fee_pct=perf, distribution_type=dist,
    )


def _investor(
    iid="INV1", name="Pension Fund A", itype="pension",
    commit=10_000_000, called=8_000_000, dist=2_000_000,
    nav_share=7_000_000, own=25.0,
) -> Investor:
    return Investor(
        investor_id=iid, name=name, investor_type=itype,
        commitment=commit, called=called, distributed=dist,
        nav_share=nav_share, ownership_pct=own,
    )


def _sample_fund(
    holdings=None, bench=None, share_classes=None, investors=None,
    sfdr="art8", aum=10_000_000, benchmark="MSCI World",
) -> FundDefinition:
    return FundDefinition(
        fund_id="F1", fund_name="Test Fund",
        sfdr_classification=sfdr, fund_type="ucits",
        base_currency="EUR", aum=aum,
        benchmark_index=benchmark, esg_strategy="integration",
        minimum_taxonomy_pct=10.0, minimum_sustainable_pct=30.0,
        holdings=holdings or [],
        benchmark_holdings=bench or [],
        share_classes=share_classes or [],
        investors=investors or [],
    )


# ===========================================================================
# NAV & AUM
# ===========================================================================

class TestNAVCalculation:
    def test_nav_from_share_classes(self, engine):
        sc1 = _share_class(nav=100.0, shares=50_000)
        sc2 = _share_class(cid="SC2", name="Class B", nav=50.0, shares=20_000)
        fund = _sample_fund(share_classes=[sc1, sc2], aum=0)
        result = engine.analyse_fund(fund)
        # NAV = 100*50000 + 50*20000 = 5M + 1M = 6M
        assert result.total_nav == 6_000_000.0
        # When aum=0, should use NAV
        assert result.total_aum == 6_000_000.0

    def test_aum_preferred_over_nav(self, engine):
        sc = _share_class(nav=100.0, shares=50_000)
        fund = _sample_fund(share_classes=[sc], aum=10_000_000)
        result = engine.analyse_fund(fund)
        assert result.total_aum == 10_000_000.0
        assert result.total_nav == 5_000_000.0

    def test_empty_fund(self, engine):
        fund = _sample_fund(aum=0)
        result = engine.analyse_fund(fund)
        assert result.total_nav == 0.0
        assert result.holdings_count == 0


# ===========================================================================
# Asset Class Breakdown
# ===========================================================================

class TestAssetClassBreakdown:
    def test_single_asset_class(self, engine):
        h = [_holding(weight=100)]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.asset_class_breakdown["equity"] == 100.0

    def test_multi_asset_class(self, engine):
        h = [
            _holding("H1", weight=60, asset_class="equity"),
            _holding("H2", weight=30, asset_class="fixed_income", isin="US0002222222"),
            _holding("H3", weight=10, asset_class="cash", isin="US0003333333"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.asset_class_breakdown["equity"] == 60.0
        assert result.asset_class_breakdown["fixed_income"] == 30.0
        assert result.asset_class_breakdown["cash"] == 10.0


# ===========================================================================
# Carbon Metrics
# ===========================================================================

class TestCarbonMetrics:
    def test_waci_single_holding(self, engine):
        # 100% weight * 120 tCO2e/MEUR = 120
        h = [_holding(weight=100, ci=120.0)]
        fund = _sample_fund(holdings=h, aum=10_000_000)
        result = engine.analyse_fund(fund)
        assert result.waci == 120.0

    def test_waci_weighted(self, engine):
        h = [
            _holding("H1", weight=60, ci=100.0),
            _holding("H2", weight=40, ci=200.0, isin="US0002222222"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        # WACI = 0.6*100 + 0.4*200 = 60 + 80 = 140
        assert result.waci == 140.0

    def test_carbon_footprint_non_zero(self, engine):
        h = [_holding(weight=100, ci=120.0)]
        fund = _sample_fund(holdings=h, aum=10_000_000)
        result = engine.analyse_fund(fund)
        assert result.carbon_footprint > 0
        assert result.total_financed_emissions > 0

    def test_zero_aum_zero_carbon(self, engine):
        h = [_holding(weight=100, ci=120.0)]
        fund = _sample_fund(holdings=h, aum=0)
        result = engine.analyse_fund(fund)
        assert result.total_financed_emissions == 0.0


# ===========================================================================
# ESG Metrics
# ===========================================================================

class TestESGMetrics:
    def test_weighted_esg_score(self, engine):
        h = [
            _holding("H1", weight=60, esg=80.0),
            _holding("H2", weight=40, esg=60.0, isin="US0002222222"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        # 0.6*80 + 0.4*60 = 48 + 24 = 72
        assert result.avg_esg_score == 72.0

    def test_taxonomy_alignment(self, engine):
        h = [
            _holding("H1", weight=50, tax_pct=40.0),
            _holding("H2", weight=50, tax_pct=20.0, isin="US0002222222"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        # 0.5*40 + 0.5*20 = 30
        assert result.taxonomy_aligned_pct == 30.0

    def test_sustainable_investment_pct(self, engine):
        h = [
            _holding("H1", weight=60, esg=70.0, dnsh=True),   # Sustainable: esg>=50, dnsh
            _holding("H2", weight=40, esg=30.0, dnsh=True, isin="US0002222222"),  # Not sustainable: esg<50
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.sustainable_investment_pct == 60.0

    def test_dnsh_compliant_pct(self, engine):
        h = [
            _holding("H1", weight=70, dnsh=True),
            _holding("H2", weight=30, dnsh=False, isin="US0002222222"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.dnsh_compliant_pct == 70.0


# ===========================================================================
# Benchmark Comparison
# ===========================================================================

class TestBenchmarkComparison:
    def test_waci_vs_benchmark(self, engine):
        h = [_holding(weight=100, ci=100.0)]
        b = [_bench_holding(weight=100, ci=150.0)]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        # (100-150)/150*100 = -33.33%
        assert result.waci_vs_benchmark < 0
        assert abs(result.waci_vs_benchmark - (-33.33)) < 0.1

    def test_esg_delta_positive(self, engine):
        h = [_holding(weight=100, esg=80.0)]
        b = [_bench_holding(weight=100, esg=65.0)]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        # 80 - 65 = 15
        assert result.esg_delta_vs_benchmark == 15.0

    def test_no_benchmark(self, engine):
        h = [_holding(weight=100)]
        fund = _sample_fund(holdings=h, bench=[])
        result = engine.analyse_fund(fund)
        assert result.benchmark_waci == 0.0
        assert result.active_share_pct == 100.0  # No benchmark = 100% active


# ===========================================================================
# Active Share & Tracking Error
# ===========================================================================

class TestActiveShare:
    def test_identical_portfolio_zero_active(self, engine):
        isin = "US0001111111"
        h = [_holding(weight=100, isin=isin)]
        b = [_bench_holding(weight=100, isin=isin)]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        assert result.active_share_pct == 0.0

    def test_completely_different(self, engine):
        h = [_holding("H1", weight=100, isin="US1111111111")]
        b = [_bench_holding(weight=100, isin="US9999999999")]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        # |100-0| + |0-100| = 200, /2 = 100
        assert result.active_share_pct == 100.0

    def test_partial_overlap(self, engine):
        h = [
            _holding("H1", weight=60, isin="US0001111111"),
            _holding("H2", weight=40, isin="US0002222222"),
        ]
        b = [
            _bench_holding("B1", weight=50, isin="US0001111111"),
            _bench_holding("B2", weight=50, isin="US0003333333"),
        ]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        # |60-50| + |40-0| + |0-50| = 10+40+50=100, /2=50
        assert result.active_share_pct == 50.0

    def test_tracking_error_non_zero_with_different_sectors(self, engine):
        h = [_holding(weight=100, sector="Technology")]
        b = [_bench_holding(weight=100, sector="Healthcare")]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        assert result.tracking_error_est > 0

    def test_tracking_error_zero_same_sectors(self, engine):
        h = [_holding(weight=100, sector="Technology")]
        b = [_bench_holding(weight=100, sector="Technology")]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        assert result.tracking_error_est == 0.0


# ===========================================================================
# Concentration
# ===========================================================================

class TestConcentration:
    def test_top10_all_in_few(self, engine):
        h = [_holding(f"H{i}", weight=20, isin=f"US{i:010d}") for i in range(5)]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.concentration_top10_pct == 100.0  # Only 5 holdings, all in top 10

    def test_top10_subset(self, engine):
        # 15 holdings: 10 at 8% + 5 at 4% = 80+20=100
        h = ([_holding(f"H{i}", weight=8, isin=f"US{i:010d}") for i in range(10)] +
             [_holding(f"H{i}", weight=4, isin=f"US{i:010d}") for i in range(10, 15)])
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.concentration_top10_pct == 80.0


# ===========================================================================
# Sector Allocation
# ===========================================================================

class TestSectorAllocation:
    def test_sector_breakdown(self, engine):
        h = [
            _holding("H1", weight=60, sector="Technology", ci=100),
            _holding("H2", weight=40, sector="Healthcare", ci=50, isin="US0002222222"),
        ]
        b = [
            _bench_holding("B1", weight=50, sector="Technology", ci=120),
            _bench_holding("B2", weight=50, sector="Healthcare", ci=80),
        ]
        fund = _sample_fund(holdings=h, bench=b)
        result = engine.analyse_fund(fund)
        sectors = {s.sector: s for s in result.sector_allocations}
        assert "Technology" in sectors
        assert "Healthcare" in sectors
        assert sectors["Technology"].active_weight_pct == 10.0  # 60-50
        assert sectors["Healthcare"].active_weight_pct == -10.0  # 40-50


# ===========================================================================
# Exclusion Compliance
# ===========================================================================

class TestExclusionCompliance:
    def test_no_breaches(self, engine):
        h = [_holding(excl=False)]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.exclusion_breach_count == 0
        assert result.exclusion_breaches == []

    def test_breach_detected(self, engine):
        h = [
            _holding("H1", excl=True, excl_reason="Controversial weapons"),
            _holding("H2", excl=False, isin="US0002222222"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.exclusion_breach_count == 1
        assert result.exclusion_breaches[0]["reason"] == "Controversial weapons"

    def test_multiple_breaches(self, engine):
        h = [
            _holding("H1", excl=True, excl_reason="Tobacco"),
            _holding("H2", excl=True, excl_reason="Thermal coal", isin="US0002222222"),
            _holding("H3", excl=False, isin="US0003333333"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.exclusion_breach_count == 2


# ===========================================================================
# LP / Investor Summary
# ===========================================================================

class TestLPSummary:
    def test_dpi_calculation(self, engine):
        inv = [_investor(called=8_000_000, dist=2_000_000, nav_share=7_000_000)]
        fund = _sample_fund(investors=inv)
        result = engine.analyse_fund(fund)
        # DPI = 2M / 8M = 0.25
        assert result.fund_dpi == 0.25

    def test_tvpi_calculation(self, engine):
        inv = [_investor(called=8_000_000, dist=2_000_000, nav_share=7_000_000)]
        fund = _sample_fund(investors=inv)
        result = engine.analyse_fund(fund)
        # TVPI = (2M + 7M) / 8M = 1.125
        assert result.fund_tvpi == 1.125

    def test_multiple_investors(self, engine):
        inv = [
            _investor("I1", called=8_000_000, dist=2_000_000, nav_share=7_000_000, commit=10_000_000),
            _investor("I2", called=4_000_000, dist=1_000_000, nav_share=3_500_000, commit=5_000_000),
        ]
        fund = _sample_fund(investors=inv)
        result = engine.analyse_fund(fund)
        assert result.total_commitment == 15_000_000.0
        assert result.total_called == 12_000_000.0
        assert result.total_distributed == 3_000_000.0
        # DPI = 3M / 12M = 0.25
        assert result.fund_dpi == 0.25
        # TVPI = (3M + 10.5M) / 12M = 1.125
        assert result.fund_tvpi == 1.125

    def test_zero_called_no_division_error(self, engine):
        inv = [_investor(called=0, dist=0, nav_share=0)]
        fund = _sample_fund(investors=inv)
        result = engine.analyse_fund(fund)
        assert result.fund_dpi == 0.0
        assert result.fund_tvpi == 0.0


# ===========================================================================
# Weight Normalisation
# ===========================================================================

class TestWeightNormalisation:
    def test_normalise_weights(self, engine):
        h = [
            _holding("H1", weight=30),
            _holding("H2", weight=20, isin="US0002222222"),
        ]  # Total = 50, should normalise to 100
        fund = _sample_fund(holdings=h, aum=10_000_000)
        result = engine.analyse_fund(fund)
        assert result.holdings_count == 2
        # Weights normalised: 60% + 40%
        assert result.asset_class_breakdown["equity"] == 100.0

    def test_already_100_no_change(self, engine):
        h = [
            _holding("H1", weight=60),
            _holding("H2", weight=40, isin="US0002222222"),
        ]
        fund = _sample_fund(holdings=h)
        result = engine.analyse_fund(fund)
        assert result.asset_class_breakdown["equity"] == 100.0


# ===========================================================================
# SFDR Classification Pass-through
# ===========================================================================

class TestSFDRClassification:
    def test_art6(self, engine):
        fund = _sample_fund(sfdr="art6")
        result = engine.analyse_fund(fund)
        assert result.sfdr_classification == "art6"

    def test_art9(self, engine):
        fund = _sample_fund(sfdr="art9")
        result = engine.analyse_fund(fund)
        assert result.sfdr_classification == "art9"

    def test_enum_values(self):
        assert SFDRClassification.ART_6.value == "art6"
        assert SFDRClassification.ART_8.value == "art8"
        assert SFDRClassification.ART_8_PLUS.value == "art8plus"
        assert SFDRClassification.ART_9.value == "art9"


# ===========================================================================
# Integration: Full Fund
# ===========================================================================

class TestFullFundAnalysis:
    def test_complete_fund(self, engine):
        holdings = [
            _holding("H1", weight=40, ci=100, esg=75, tax_pct=35, sector="Technology"),
            _holding("H2", weight=30, ci=200, esg=60, tax_pct=20, sector="Energy",
                     isin="US0002222222"),
            _holding("H3", weight=20, ci=50, esg=85, tax_pct=50, sector="Healthcare",
                     isin="US0003333333"),
            _holding("H4", weight=10, ci=300, esg=40, tax_pct=5, sector="Materials",
                     isin="US0004444444", excl=True, excl_reason="Thermal coal"),
        ]
        bench = [
            _bench_holding("B1", weight=30, ci=120, esg=70, sector="Technology",
                           isin="US0001111111"),
            _bench_holding("B2", weight=30, ci=180, esg=55, sector="Energy",
                           isin="US0002222222"),
            _bench_holding("B3", weight=25, ci=60, esg=80, sector="Healthcare",
                           isin="US0003333333"),
            _bench_holding("B4", weight=15, ci=250, esg=45, sector="Materials",
                           isin="US0005555555"),
        ]
        scs = [_share_class(nav=100, shares=50_000)]
        invs = [
            _investor("I1", commit=10_000_000, called=8_000_000,
                      dist=2_000_000, nav_share=7_000_000, own=60),
            _investor("I2", commit=5_000_000, called=4_000_000,
                      dist=1_000_000, nav_share=3_500_000, own=40),
        ]
        fund = _sample_fund(
            holdings=holdings, bench=bench,
            share_classes=scs, investors=invs,
            aum=10_000_000, sfdr="art8plus",
        )
        result = engine.analyse_fund(fund)

        # Basic structural checks
        assert result.fund_id == "F1"
        assert result.sfdr_classification == "art8plus"
        assert result.holdings_count == 4
        assert result.total_aum == 10_000_000.0
        assert result.total_nav == 5_000_000.0

        # Carbon: WACI = 0.4*100 + 0.3*200 + 0.2*50 + 0.1*300 = 40+60+10+30=140
        assert result.waci == 140.0

        # ESG: 0.4*75 + 0.3*60 + 0.2*85 + 0.1*40 = 30+18+17+4=69
        assert result.avg_esg_score == 69.0

        # Taxonomy: 0.4*35 + 0.3*20 + 0.2*50 + 0.1*5 = 14+6+10+0.5=30.5
        assert result.taxonomy_aligned_pct == 30.5

        # Exclusion breaches
        assert result.exclusion_breach_count == 1
        assert result.exclusion_breaches[0]["holding_id"] == "H4"

        # LP totals
        assert result.total_commitment == 15_000_000.0
        assert result.total_called == 12_000_000.0
        assert result.fund_dpi == 0.25
        assert result.fund_tvpi == 1.125

        # Sector count
        assert len(result.sector_allocations) == 4

        # Benchmark: fund WACI < benchmark WACI (fund=140 vs bench=~147.5)
        assert result.waci_vs_benchmark < 0
