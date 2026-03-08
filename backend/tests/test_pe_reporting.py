"""
Tests for PE GP/LP Reporting + Impact Framework + IRR Sensitivity
==================================================================
"""
import pytest

from services.pe_reporting_engine import (
    PEReportingEngine,
    FundPerformanceData,
    PortfolioCompanySummary,
    LPReportInput,
    PAI_INDICATORS,
)
from services.pe_impact_framework import (
    PEImpactFramework,
    CompanyImpactData,
    FundImpactInput,
    SDG_DEFINITIONS,
    IMPACT_DIMENSIONS,
)
from services.pe_irr_sensitivity import (
    PEIRRSensitivityEngine,
    IRRSensitivityInput,
    DealCashflow,
    ESG_BPS_PER_POINT,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def report_engine():
    return PEReportingEngine()


@pytest.fixture
def impact_engine():
    return PEImpactFramework()


@pytest.fixture
def irr_engine():
    return PEIRRSensitivityEngine()


def _fund_perf(
    fund_id="F1", fund_name="ESG Growth Fund I", vintage=2021,
    size=500_000_000, committed=500_000_000, called=350_000_000,
    distributed=100_000_000, nav=400_000_000,
    fees=15_000_000, carry=0,
) -> FundPerformanceData:
    return FundPerformanceData(
        fund_id=fund_id, fund_name=fund_name,
        vintage_year=vintage, fund_size_eur=size,
        committed_capital_eur=committed, called_capital_eur=called,
        distributed_capital_eur=distributed, nav_eur=nav,
        management_fees_eur=fees, carried_interest_eur=carry,
        reporting_date="2025-12-31",
    )


def _portfolio_co(
    cid="C1", name="TechCo", sector="Technology",
    invested=20_000_000, nav=30_000_000, ownership=25.0,
    esg_score=65.0, carbon_intensity=50.0,
) -> PortfolioCompanySummary:
    return PortfolioCompanySummary(
        company_id=cid, company_name=name, sector=sector,
        invested_eur=invested, current_nav_eur=nav,
        ownership_pct=ownership, entry_date="2022-03-15",
        esg_score=esg_score, esg_traffic_light="green",
        carbon_intensity_tco2e_per_meur=carbon_intensity,
    )


def _company_impact(
    cid="C1", name="CleanTech", sector="Technology",
    sdgs=None, scores=None, jobs=100, benef=5000,
    co2=1000.0, renew=500.0, invested=10_000_000, nav=15_000_000,
) -> CompanyImpactData:
    return CompanyImpactData(
        company_id=cid, company_name=name, sector=sector,
        primary_sdgs=sdgs or [7, 13],
        impact_scores=scores or {"what": 4, "who": 3, "how_much": 4, "contribution": 4, "risk": 3},
        jobs_created=jobs, beneficiaries_reached=benef,
        co2_avoided_tonnes=co2, renewable_mwh_generated=renew,
        invested_eur=invested, current_nav_eur=nav,
    )


def _irr_input(
    deal_id="D1", name="TargetCo", sector="Technology",
    entry_ev=120_000_000, ebitda=10_000_000, mult=12.0,
    equity=60_000_000, debt=60_000_000, years=5,
    growth=5.0, exit_mult=0.0, esg=50.0, esg_imp=0.0,
) -> IRRSensitivityInput:
    return IRRSensitivityInput(
        deal_id=deal_id, company_name=name, sector=sector,
        entry_ev_eur=entry_ev, entry_ebitda_eur=ebitda,
        entry_multiple=mult, equity_invested_eur=equity,
        net_debt_eur=debt, hold_period_years=years,
        ebitda_growth_pct=growth, exit_multiple=exit_mult,
        esg_score=esg, esg_improvement_expected=esg_imp,
    )


# ===========================================================================
# LP Report Tests
# ===========================================================================

class TestLPReport:
    def test_basic_report_generation(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.fund_name == "ESG Growth Fund I"
        assert r.total_companies == 1
        assert r.reporting_period == "2025-Q4"

    def test_fund_metrics_tvpi(self, report_engine):
        # called=350M, distributed=100M, nav=400M
        # DPI=100/350=0.29, RVPI=400/350=1.14, TVPI=1.43
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.fund_metrics.dpi == 0.29
        assert r.fund_metrics.rvpi == 1.14
        assert r.fund_metrics.tvpi == 1.43

    def test_dry_powder(self, report_engine):
        # committed=500M, called=350M → dry_powder=150M
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[],
            reporting_period="2025-Q4",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.fund_metrics.dry_powder_eur == 150_000_000

    def test_called_pct(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[],
            reporting_period="2025-Q4",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.fund_metrics.called_pct == 70.0

    def test_portfolio_moic(self, report_engine):
        # invested=20M, nav=30M → MOIC=1.5
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.portfolio_summary[0]["moic"] == 1.5

    def test_multiple_companies(self, report_engine):
        cos = [
            _portfolio_co("C1", "Co A", invested=20_000_000, nav=30_000_000),
            _portfolio_co("C2", "Co B", invested=15_000_000, nav=25_000_000),
        ]
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=cos,
            reporting_period="2025-Q4",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.total_companies == 2
        assert r.total_nav_eur == 55_000_000
        assert r.total_invested_eur == 35_000_000

    def test_esg_annex_generated(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
            sfdr_classification="art9",
            include_esg_annex=True,
        )
        r = report_engine.generate_lp_report(inp)
        assert r.esg_annex is not None
        assert r.esg_annex.sfdr_classification == "art9"
        assert r.esg_annex.sustainable_investment_pct == 80.0

    def test_esg_annex_art8(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
            sfdr_classification="art8",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.esg_annex.sustainable_investment_pct == 30.0
        assert r.esg_annex.taxonomy_aligned_pct == 10.0

    def test_esg_annex_skipped_when_false(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
            include_esg_annex=False,
        )
        r = report_engine.generate_lp_report(inp)
        assert r.esg_annex is None

    def test_annual_report_has_extra_section(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-FY",
            report_type="annual",
        )
        r = report_engine.generate_lp_report(inp)
        section_ids = [s["section_id"] for s in r.sections]
        assert "annual_review" in section_ids

    def test_quarterly_no_annual_section(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
            report_type="quarterly",
        )
        r = report_engine.generate_lp_report(inp)
        section_ids = [s["section_id"] for s in r.sections]
        assert "annual_review" not in section_ids

    def test_executive_summary_generated(self, report_engine):
        inp = LPReportInput(
            fund_performance=_fund_perf(),
            portfolio_companies=[_portfolio_co()],
            reporting_period="2025-Q4",
        )
        r = report_engine.generate_lp_report(inp)
        assert "ESG Growth Fund I" in r.executive_summary
        assert "TVPI" in r.executive_summary

    def test_zero_called_capital(self, report_engine):
        perf = _fund_perf(called=0, distributed=0, nav=0)
        inp = LPReportInput(
            fund_performance=perf,
            portfolio_companies=[],
            reporting_period="2025-Q1",
        )
        r = report_engine.generate_lp_report(inp)
        assert r.fund_metrics.tvpi == 0
        assert r.fund_metrics.dry_powder_eur == 500_000_000


class TestPAIReference:
    def test_pai_count(self, report_engine):
        pais = report_engine.get_pai_indicators()
        assert len(pais) == 10

    def test_pai_fields(self, report_engine):
        for pai in report_engine.get_pai_indicators():
            assert "pai_id" in pai
            assert "name" in pai
            assert "unit" in pai
            assert "mandatory" in pai


# ===========================================================================
# Impact Framework Tests
# ===========================================================================

class TestCompanyImpact:
    def test_high_impact_score(self, impact_engine):
        c = _company_impact(
            scores={"what": 5, "who": 4, "how_much": 4, "contribution": 5, "risk": 4},
        )
        r = impact_engine.assess_company_impact(c)
        assert r.impact_rating == "high"
        assert r.composite_impact_score >= 4.0

    def test_medium_impact_score(self, impact_engine):
        c = _company_impact(
            scores={"what": 3, "who": 3, "how_much": 3, "contribution": 3, "risk": 3},
        )
        r = impact_engine.assess_company_impact(c)
        assert r.impact_rating == "medium"
        assert r.composite_impact_score == 3.0

    def test_low_impact_score(self, impact_engine):
        c = _company_impact(
            scores={"what": 2, "who": 2, "how_much": 2, "contribution": 2, "risk": 2},
        )
        r = impact_engine.assess_company_impact(c)
        assert r.impact_rating == "low"

    def test_sdg_names_resolved(self, impact_engine):
        c = _company_impact(sdgs=[7, 13])
        r = impact_engine.assess_company_impact(c)
        assert "Affordable and Clean Energy" in r.sdg_names
        assert "Climate Action" in r.sdg_names

    def test_additionality_strong(self, impact_engine):
        c = _company_impact(
            scores={"what": 3, "who": 3, "how_much": 3, "contribution": 5, "risk": 3},
        )
        r = impact_engine.assess_company_impact(c)
        assert r.additionality_rating == "strong"

    def test_additionality_weak(self, impact_engine):
        c = _company_impact(
            scores={"what": 3, "who": 3, "how_much": 3, "contribution": 1, "risk": 3},
        )
        r = impact_engine.assess_company_impact(c)
        assert r.additionality_rating == "weak"

    def test_quantitative_metrics(self, impact_engine):
        c = _company_impact(jobs=200, benef=10000, co2=5000, renew=2000)
        r = impact_engine.assess_company_impact(c)
        assert r.quantitative_metrics["jobs_created"] == 200
        assert r.quantitative_metrics["co2_avoided_tonnes"] == 5000

    def test_impact_multiple_of_money(self, impact_engine):
        c = _company_impact(benef=5000, co2=1000, invested=10_000_000)
        r = impact_engine.assess_company_impact(c)
        # (5000*100 + 1000*50) / 10M = 550000/10M = 0.055
        assert r.impact_multiple_of_money == 0.055


class TestFundImpact:
    def test_empty_fund(self, impact_engine):
        inp = FundImpactInput(fund_id="F1", fund_name="Test Fund")
        r = impact_engine.assess_fund_impact(inp)
        assert r.total_companies == 0
        assert r.fund_impact_rating == "neutral"

    def test_fund_with_companies(self, impact_engine):
        companies = [
            _company_impact("C1", "Co A"),
            _company_impact("C2", "Co B"),
        ]
        inp = FundImpactInput(
            fund_id="F1", fund_name="Impact Fund I",
            companies=companies,
        )
        r = impact_engine.assess_fund_impact(inp)
        assert r.total_companies == 2
        assert len(r.company_scores) == 2

    def test_sdg_contributions(self, impact_engine):
        companies = [
            _company_impact("C1", "Co A", sdgs=[7, 13]),
            _company_impact("C2", "Co B", sdgs=[7, 9]),
        ]
        inp = FundImpactInput(fund_id="F1", fund_name="Fund", companies=companies)
        r = impact_engine.assess_fund_impact(inp)
        sdg_nums = [c.sdg_number for c in r.sdg_contributions]
        assert 7 in sdg_nums
        assert 13 in sdg_nums
        assert 9 in sdg_nums
        # SDG 7 appears in both companies
        sdg7 = next(c for c in r.sdg_contributions if c.sdg_number == 7)
        assert sdg7.company_count == 2

    def test_totals_aggregated(self, impact_engine):
        companies = [
            _company_impact("C1", jobs=100, benef=5000, co2=1000, renew=500),
            _company_impact("C2", jobs=200, benef=3000, co2=2000, renew=800),
        ]
        inp = FundImpactInput(fund_id="F1", fund_name="Fund", companies=companies)
        r = impact_engine.assess_fund_impact(inp)
        assert r.total_jobs_created == 300
        assert r.total_beneficiaries == 8000
        assert r.total_co2_avoided_tonnes == 3000
        assert r.total_renewable_mwh == 1300

    def test_impact_summary_generated(self, impact_engine):
        companies = [_company_impact("C1")]
        inp = FundImpactInput(fund_id="F1", fund_name="Green Fund", companies=companies)
        r = impact_engine.assess_fund_impact(inp)
        assert "Green Fund" in r.impact_summary


class TestSDGReference:
    def test_sdg_count(self, impact_engine):
        assert len(SDG_DEFINITIONS) == 17

    def test_all_sdgs_have_fields(self):
        for num, defn in SDG_DEFINITIONS.items():
            assert "name" in defn
            assert "category" in defn
            assert 1 <= num <= 17

    def test_impact_dimensions(self, impact_engine):
        dims = impact_engine.get_impact_dimensions()
        assert len(dims) == 5
        assert "what" in dims
        assert "contribution" in dims


# ===========================================================================
# IRR Sensitivity Tests
# ===========================================================================

class TestIRRScenarios:
    def test_base_case_computed(self, irr_engine):
        inp = _irr_input()
        r = irr_engine.analyse(inp)
        assert r.base_case.scenario_name == "Base Case"
        assert r.base_case.irr_pct > 0
        assert r.base_case.moic > 1.0

    def test_upside_beats_base(self, irr_engine):
        inp = _irr_input()
        r = irr_engine.analyse(inp)
        assert r.upside_case.irr_pct > r.base_case.irr_pct
        assert r.upside_case.moic > r.base_case.moic

    def test_downside_below_base(self, irr_engine):
        inp = _irr_input()
        r = irr_engine.analyse(inp)
        assert r.downside_case.irr_pct < r.base_case.irr_pct
        assert r.downside_case.moic < r.base_case.moic

    def test_three_scenarios(self, irr_engine):
        inp = _irr_input()
        r = irr_engine.analyse(inp)
        assert len(r.scenarios) == 3

    def test_higher_growth_higher_irr(self, irr_engine):
        low = _irr_input(growth=2.0)
        high = _irr_input(growth=10.0)
        r_low = irr_engine.analyse(low)
        r_high = irr_engine.analyse(high)
        assert r_high.base_case.irr_pct > r_low.base_case.irr_pct


class TestESGImpactOnReturns:
    def test_esg_improvement_increases_irr(self, irr_engine):
        inp = _irr_input(esg=50, esg_imp=10.0)
        r = irr_engine.analyse(inp)
        assert r.esg_impact.esg_adjusted_irr_pct >= r.esg_impact.base_irr_pct

    def test_esg_improvement_increases_moic(self, irr_engine):
        inp = _irr_input(esg=50, esg_imp=10.0)
        r = irr_engine.analyse(inp)
        assert r.esg_impact.esg_adjusted_moic >= r.esg_impact.base_moic

    def test_zero_improvement_no_delta(self, irr_engine):
        inp = _irr_input(esg=50, esg_imp=0.0)
        r = irr_engine.analyse(inp)
        assert r.esg_impact.irr_delta_bps == 0

    def test_low_esg_has_risk_discount(self, irr_engine):
        inp = _irr_input(esg=30, esg_imp=0.0)
        r = irr_engine.analyse(inp)
        assert r.esg_impact.esg_risk_discount_pct > 0

    def test_high_esg_no_risk_discount(self, irr_engine):
        inp = _irr_input(esg=70, esg_imp=0.0)
        r = irr_engine.analyse(inp)
        assert r.esg_impact.esg_risk_discount_pct == 0

    def test_multiple_expansion_formula(self, irr_engine):
        inp = _irr_input(esg=50, esg_imp=10.0)
        r = irr_engine.analyse(inp)
        expected = round(10.0 * ESG_BPS_PER_POINT / 10000, 4)
        assert r.esg_impact.multiple_expansion_x == expected


class TestSensitivityTable:
    def test_5x5_grid(self, irr_engine):
        inp = _irr_input()
        r = irr_engine.analyse(inp)
        assert len(r.sensitivity_table.cells) == 25  # 5x5
        assert len(r.sensitivity_table.row_values) == 5
        assert len(r.sensitivity_table.col_values) == 5

    def test_base_case_in_grid(self, irr_engine):
        inp = _irr_input(growth=5.0, exit_mult=12.0)
        r = irr_engine.analyse(inp)
        assert r.sensitivity_table.base_irr_pct > 0

    def test_higher_mult_higher_return(self, irr_engine):
        inp = _irr_input()
        r = irr_engine.analyse(inp)
        cells = r.sensitivity_table.cells
        # Find cells at same growth but different multiples
        base_growth = r.sensitivity_table.col_values[2]  # middle
        same_growth = [c for c in cells if c.col_value == base_growth]
        irrs = [(c.row_value, c.irr_pct) for c in same_growth]
        irrs.sort()
        # Higher multiple → higher IRR
        assert irrs[-1][1] >= irrs[0][1]


class TestIRRComputation:
    def test_simple_irr(self, irr_engine):
        """Invest 100, receive 150 after 4 quarters = ~41% annual."""
        cfs = [
            DealCashflow(period=0, amount_eur=-100),
            DealCashflow(period=4, amount_eur=150),
        ]
        irr = irr_engine.compute_irr(cfs)
        assert 30 < irr < 60

    def test_double_in_2_years(self, irr_engine):
        """Invest 100, receive 200 after 8 quarters ≈ 41% annual."""
        cfs = [
            DealCashflow(period=0, amount_eur=-100),
            DealCashflow(period=8, amount_eur=200),
        ]
        irr = irr_engine.compute_irr(cfs)
        assert 30 < irr < 50

    def test_empty_cashflows(self, irr_engine):
        irr = irr_engine.compute_irr([])
        assert irr == 0.0

    def test_summary_generated(self, irr_engine):
        inp = _irr_input()
        r = irr_engine.analyse(inp)
        assert "TargetCo" in r.summary
        assert "Base IRR" in r.summary
