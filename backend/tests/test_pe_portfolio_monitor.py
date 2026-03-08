"""
Tests for PE Portfolio Monitoring + Value Creation
====================================================
"""
import pytest

from services.pe_portfolio_monitor import (
    PEPortfolioMonitor,
    CompanyKPIData,
    CompanyTarget,
    CompanyMonitorInput,
    ILPA_KPIS,
)
from services.pe_value_creation import (
    PEValueCreationEngine,
    SECTOR_LEVERS,
    DEFAULT_LEVERS,
    ESG_MULTIPLE_EXPANSION_BPS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def monitor():
    return PEPortfolioMonitor()


@pytest.fixture
def vc_engine():
    return PEValueCreationEngine()


def _kpi_data(
    cid="C1", name="PortCo A", period="2025-Q4",
    scope1=1000, scope2=500, renewable=45, board_div=30,
    injuries=2.5, waste=100, water=5000, energy=8000,
    **extra,
) -> CompanyKPIData:
    vals = {
        "scope_1_emissions_tco2e": scope1,
        "scope_2_emissions_tco2e": scope2,
        "renewable_energy_pct": renewable,
        "board_diversity_pct": board_div,
        "work_injuries_rate": injuries,
        "waste_generated_tonnes": waste,
        "water_withdrawal_m3": water,
        "total_energy_mwh": energy,
    }
    vals.update(extra)
    return CompanyKPIData(
        company_id=cid, company_name=name,
        reporting_period=period, kpi_values=vals,
    )


def _monitor_input(
    cid="C1", name="PortCo A", sector="Technology",
    current=None, prior=None, targets=None,
    ownership=60.0,
) -> CompanyMonitorInput:
    return CompanyMonitorInput(
        company_id=cid,
        company_name=name,
        sector=sector,
        fund_id="F1",
        equity_invested_eur=10_000_000,
        ownership_pct=ownership,
        current_period=current or _kpi_data(cid, name),
        prior_period=prior,
        targets=targets or [],
    )


# ===========================================================================
# KPI Status Tests
# ===========================================================================

class TestKPIStatus:
    def test_kpis_reported(self, monitor):
        inp = _monitor_input()
        r = monitor.monitor_company(inp)
        assert r.total_kpis == 8  # 8 KPIs in _kpi_data

    def test_yoy_improvement_lower_is_better(self, monitor):
        """Scope 1 decreased = improved."""
        current = _kpi_data(scope1=800)
        prior = _kpi_data(scope1=1000, period="2024-Q4")
        inp = _monitor_input(current=current, prior=prior)
        r = monitor.monitor_company(inp)
        s1 = next(k for k in r.kpi_statuses if k.kpi_id == "scope_1_emissions_tco2e")
        assert s1.improved is True
        assert s1.yoy_change == -200

    def test_yoy_deterioration_lower_is_better(self, monitor):
        """Scope 1 increased = deteriorated."""
        current = _kpi_data(scope1=1200)
        prior = _kpi_data(scope1=1000, period="2024-Q4")
        inp = _monitor_input(current=current, prior=prior)
        r = monitor.monitor_company(inp)
        s1 = next(k for k in r.kpi_statuses if k.kpi_id == "scope_1_emissions_tco2e")
        assert s1.improved is False

    def test_yoy_improvement_higher_is_better(self, monitor):
        """Renewable % increased = improved."""
        current = _kpi_data(renewable=60)
        prior = _kpi_data(renewable=45, period="2024-Q4")
        inp = _monitor_input(current=current, prior=prior)
        r = monitor.monitor_company(inp)
        ren = next(k for k in r.kpi_statuses if k.kpi_id == "renewable_energy_pct")
        assert ren.improved is True

    def test_no_prior_no_yoy(self, monitor):
        inp = _monitor_input()
        r = monitor.monitor_company(inp)
        for k in r.kpi_statuses:
            assert k.yoy_change is None
            assert k.improved is None


# ===========================================================================
# Traffic Light Tests
# ===========================================================================

class TestTrafficLight:
    def test_green_on_target(self, monitor):
        targets = [CompanyTarget("scope_1_emissions_tco2e", 1200)]
        current = _kpi_data(scope1=1000)
        inp = _monitor_input(current=current, targets=targets)
        r = monitor.monitor_company(inp)
        s1 = next(k for k in r.kpi_statuses if k.kpi_id == "scope_1_emissions_tco2e")
        assert s1.traffic_light == "green"
        assert s1.on_target is True

    def test_red_off_target(self, monitor):
        targets = [CompanyTarget("scope_1_emissions_tco2e", 500)]
        current = _kpi_data(scope1=1000)
        inp = _monitor_input(current=current, targets=targets)
        r = monitor.monitor_company(inp)
        s1 = next(k for k in r.kpi_statuses if k.kpi_id == "scope_1_emissions_tco2e")
        assert s1.traffic_light == "red"
        assert s1.on_target is False

    def test_amber_near_target(self, monitor):
        """Within 20% of target = amber."""
        targets = [CompanyTarget("scope_1_emissions_tco2e", 900)]
        current = _kpi_data(scope1=1000)  # 1000 <= 900*1.2=1080
        inp = _monitor_input(current=current, targets=targets)
        r = monitor.monitor_company(inp)
        s1 = next(k for k in r.kpi_statuses if k.kpi_id == "scope_1_emissions_tco2e")
        assert s1.traffic_light == "amber"

    def test_green_from_improvement_no_target(self, monitor):
        """No target but improved = green."""
        current = _kpi_data(scope1=800)
        prior = _kpi_data(scope1=1000, period="2024-Q4")
        inp = _monitor_input(current=current, prior=prior)
        r = monitor.monitor_company(inp)
        s1 = next(k for k in r.kpi_statuses if k.kpi_id == "scope_1_emissions_tco2e")
        assert s1.traffic_light == "green"

    def test_amber_no_target_no_prior(self, monitor):
        """No target and no prior = amber (insufficient data)."""
        inp = _monitor_input()
        r = monitor.monitor_company(inp)
        for k in r.kpi_statuses:
            assert k.traffic_light == "amber"

    def test_overall_green_when_majority_green(self, monitor):
        """>=60% green = overall green."""
        targets = [
            CompanyTarget("scope_1_emissions_tco2e", 1500),
            CompanyTarget("scope_2_emissions_tco2e", 800),
            CompanyTarget("renewable_energy_pct", 30),
            CompanyTarget("board_diversity_pct", 20),
            CompanyTarget("work_injuries_rate", 5),
            CompanyTarget("waste_generated_tonnes", 200),
            CompanyTarget("water_withdrawal_m3", 10000),
            CompanyTarget("total_energy_mwh", 10000),
        ]
        inp = _monitor_input(targets=targets)
        r = monitor.monitor_company(inp)
        # All on target → all green
        assert r.overall_traffic_light == "green"

    def test_overall_red_when_many_red(self, monitor):
        """>=40% red = overall red."""
        targets = [
            CompanyTarget("scope_1_emissions_tco2e", 100),    # 1000 >> 100 → red
            CompanyTarget("scope_2_emissions_tco2e", 50),     # 500 >> 50 → red
            CompanyTarget("renewable_energy_pct", 90),        # 45 << 90 → red
            CompanyTarget("board_diversity_pct", 80),         # 30 << 80 → red
            CompanyTarget("work_injuries_rate", 0.5),         # 2.5 >> 0.5 → red
        ]
        inp = _monitor_input(targets=targets)
        r = monitor.monitor_company(inp)
        assert r.overall_traffic_light == "red"


# ===========================================================================
# Portfolio Summary Tests
# ===========================================================================

class TestPortfolioMonitor:
    def test_empty_portfolio(self, monitor):
        r = monitor.monitor_portfolio("F1", [])
        assert r.total_companies == 0

    def test_multi_company(self, monitor):
        companies = [
            _monitor_input("C1", "Co A", ownership=60),
            _monitor_input("C2", "Co B", ownership=40),
        ]
        r = monitor.monitor_portfolio("F1", companies)
        assert r.total_companies == 2
        assert len(r.company_results) == 2

    def test_aggregate_kpis_weighted(self, monitor):
        c1 = _monitor_input("C1", "Co A", ownership=60,
                            current=_kpi_data("C1", scope1=1000))
        c2 = _monitor_input("C2", "Co B", ownership=40,
                            current=_kpi_data("C2", scope1=2000))
        r = monitor.monitor_portfolio("F1", [c1, c2])
        # Weighted: (1000*60 + 2000*40)/(60+40) = 140000/100 = 1400
        assert r.aggregate_kpis["scope_1_emissions_tco2e"] == 1400.0

    def test_worst_performing_sorted(self, monitor):
        """Companies with red targets should appear in worst_performing."""
        targets_bad = [CompanyTarget("scope_1_emissions_tco2e", 100)]
        c1 = _monitor_input("C1", "Bad Co", targets=targets_bad)
        c2 = _monitor_input("C2", "Good Co")
        r = monitor.monitor_portfolio("F1", [c1, c2])
        if r.worst_performing:
            assert r.worst_performing[0]["company_id"] == "C1"


# ===========================================================================
# KPI Reference Data Tests
# ===========================================================================

class TestKPIReference:
    def test_ilpa_kpi_count(self):
        assert len(ILPA_KPIS) == 12

    def test_all_kpis_have_required_fields(self):
        for kpi_id, kpi in ILPA_KPIS.items():
            assert "name" in kpi
            assert "category" in kpi
            assert "unit" in kpi
            assert "direction" in kpi
            assert "ilpa_metric_id" in kpi

    def test_kpi_template(self, monitor):
        template = monitor.get_kpi_template()
        assert len(template) == 12
        assert all("kpi_id" in t for t in template)


# ===========================================================================
# Value Creation Plan Tests
# ===========================================================================

class TestValueCreationPlan:
    def test_plan_for_known_sector(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "TechCo", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        assert plan.company_name == "TechCo"
        assert plan.sector == "Technology"
        assert len(plan.levers) == 4  # Technology has 4 levers

    def test_plan_for_unknown_sector(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "UnknownCo", "Agriculture",
            ebitda_eur=5_000_000, entry_multiple=8.0,
        )
        assert len(plan.levers) == len(DEFAULT_LEVERS)

    def test_capex_calculated(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "TechCo", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        assert plan.total_capex_mid_eur > 0

    def test_ebitda_uplift_positive(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "TechCo", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        assert plan.total_ebitda_uplift_mid_eur > 0

    def test_exit_multiple_higher_than_entry(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "TechCo", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        assert plan.projected_exit_multiple > plan.entry_multiple

    def test_value_creation_positive(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "TechCo", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        assert plan.projected_value_creation_eur > 0

    def test_milestones_generated(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "TechCo", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        assert len(plan.milestones) >= 2  # Kick-off + at least 1 lever
        assert plan.milestones[0].month == 0  # Kick-off at month 0

    def test_milestones_sorted_by_month(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "IndCo", "Industrials",
            ebitda_eur=20_000_000, entry_multiple=10.0,
        )
        months = [m.month for m in plan.milestones]
        assert months == sorted(months)

    def test_esg_improvement_capped(self, vc_engine):
        """ESG improvement capped at 20 points."""
        plan = vc_engine.generate_plan(
            "C1", "Co", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        assert plan.projected_esg_score_improvement <= 20.0

    def test_multiple_expansion_formula(self, vc_engine):
        plan = vc_engine.generate_plan(
            "C1", "TechCo", "Technology",
            ebitda_eur=10_000_000, entry_multiple=12.0,
        )
        # 4 levers * 3 points each = 12 improvement
        # 12 * 25bps / 10000 = 0.03x
        expected_expansion = round(12.0 * ESG_MULTIPLE_EXPANSION_BPS / 10000, 2)
        assert plan.projected_multiple_expansion == expected_expansion


# ===========================================================================
# Sector Lever Reference Tests
# ===========================================================================

class TestSectorLevers:
    def test_available_sectors(self, vc_engine):
        sectors = vc_engine.get_available_sectors()
        assert "Technology" in sectors
        assert "Healthcare" in sectors
        assert "Industrials" in sectors
        assert "Energy" in sectors

    def test_sector_lever_count(self, vc_engine):
        tech = vc_engine.get_sector_levers("Technology")
        assert len(tech) == 4
        hc = vc_engine.get_sector_levers("Healthcare")
        assert len(hc) == 3

    def test_unknown_sector_returns_defaults(self, vc_engine):
        levers = vc_engine.get_sector_levers("Mining")
        assert len(levers) == len(DEFAULT_LEVERS)

    def test_lever_has_required_fields(self, vc_engine):
        for sector, levers in SECTOR_LEVERS.items():
            for lev in levers:
                assert "lever_id" in lev
                assert "name" in lev
                assert "category" in lev
                assert "capex_eur_range" in lev
                assert "ebitda_uplift_pct" in lev
                assert "implementation_months" in lev
