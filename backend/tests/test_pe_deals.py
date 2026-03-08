"""
Tests for PE Deal Pipeline + ESG Screening Engine
===================================================
"""
import pytest

from services.pe_deal_engine import (
    PEDealEngine,
    DealInput,
    SECTOR_ESG_RISK,
    ESG_SUB_DIMENSIONS,
    HIGH_CARBON_SECTORS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return PEDealEngine()


def _deal(
    deal_id="D1", name="TargetCo", sector="Technology", stage="screening",
    deal_size=50_000_000, entry_mult=12.0,
    esg_scores=None,
    transition_plan=True, ungc=False, sanctions=False,
    weapons=False, env_incident=False, child_labor=False,
    tax_haven=False,
) -> DealInput:
    return DealInput(
        deal_id=deal_id,
        company_name=name,
        sector=sector,
        stage=stage,
        deal_size_eur=deal_size,
        entry_multiple=entry_mult,
        esg_scores=esg_scores or {},
        has_transition_plan=transition_plan,
        ungc_violation=ungc,
        sanctions_hit=sanctions,
        controversial_weapons=weapons,
        severe_environmental_incident=env_incident,
        child_labor_risk=child_labor,
        tax_haven_structure=tax_haven,
    )


def _deal_with_scores(
    deal_id="D1", name="TargetCo", sector="Technology",
    env=3, soc=3, gov=3, trans=3, phys=3,
    **kwargs,
) -> DealInput:
    """Create deal with uniform sub-dimension scores per dimension."""
    esg = {}
    for dim, sub_dims in ESG_SUB_DIMENSIONS.items():
        val = {"environmental": env, "social": soc, "governance": gov,
               "transition_risk": trans, "physical_risk": phys}[dim]
        esg[dim] = {sd: val for sd in sub_dims}
    return _deal(deal_id=deal_id, name=name, sector=sector, esg_scores=esg, **kwargs)


# ===========================================================================
# ESG Dimension Scoring Tests
# ===========================================================================

class TestDimensionScoring:
    def test_default_neutral_when_no_scores(self, engine):
        """Unassessed dimensions default to 3.0 (neutral)."""
        d = _deal()
        r = engine.screen_deal(d)
        assert len(r.dimension_scores) == 5
        for ds in r.dimension_scores:
            assert ds.avg_score == 3.0  # default

    def test_scores_reflected_correctly(self, engine):
        d = _deal_with_scores(env=2, soc=4, gov=1, trans=5, phys=3)
        r = engine.screen_deal(d)
        dim_map = {ds.dimension: ds.avg_score for ds in r.dimension_scores}
        assert dim_map["environmental"] == 2.0
        assert dim_map["social"] == 4.0
        assert dim_map["governance"] == 1.0
        assert dim_map["transition_risk"] == 5.0
        assert dim_map["physical_risk"] == 3.0

    def test_partial_scoring(self, engine):
        """Only some sub-dimensions scored — average should use assessed only."""
        esg = {"environmental": {"carbon_intensity": 2, "resource_efficiency": 4}}
        d = _deal(esg_scores=esg)
        r = engine.screen_deal(d)
        env = next(ds for ds in r.dimension_scores if ds.dimension == "environmental")
        assert env.avg_score == 3.0  # (2+4)/2
        assert env.assessed_count == 2

    def test_assessed_count(self, engine):
        d = _deal_with_scores(env=3, soc=3, gov=3, trans=3, phys=3)
        r = engine.screen_deal(d)
        for ds in r.dimension_scores:
            assert ds.assessed_count == 4  # 4 sub-dimensions per dimension


# ===========================================================================
# Composite Score + Risk Band Tests
# ===========================================================================

class TestCompositeScore:
    def test_low_risk(self, engine):
        d = _deal_with_scores(env=1, soc=1, gov=1, trans=2, phys=2)
        r = engine.screen_deal(d)
        assert r.composite_esg_score <= 2.0
        assert r.esg_risk_band == "low"

    def test_medium_risk(self, engine):
        d = _deal_with_scores(env=3, soc=3, gov=3, trans=3, phys=3)
        r = engine.screen_deal(d)
        assert r.composite_esg_score == 3.0
        assert r.esg_risk_band == "medium"

    def test_high_risk(self, engine):
        d = _deal_with_scores(env=4, soc=3, gov=4, trans=4, phys=3)
        r = engine.screen_deal(d)
        assert 3.0 < r.composite_esg_score <= 4.0
        assert r.esg_risk_band == "high"

    def test_critical_risk(self, engine):
        d = _deal_with_scores(env=5, soc=5, gov=4, trans=5, phys=4)
        r = engine.screen_deal(d)
        assert r.composite_esg_score > 4.0
        assert r.esg_risk_band == "critical"

    def test_composite_is_average_of_dimensions(self, engine):
        d = _deal_with_scores(env=1, soc=2, gov=3, trans=4, phys=5)
        r = engine.screen_deal(d)
        assert r.composite_esg_score == 3.0  # (1+2+3+4+5)/5


# ===========================================================================
# Red Flag Detection Tests
# ===========================================================================

class TestRedFlags:
    def test_clean_deal_no_flags(self, engine):
        d = _deal()
        r = engine.screen_deal(d)
        assert len(r.red_flags) == 0
        assert r.has_deal_breaker is False

    def test_weapons_hard_flag(self, engine):
        d = _deal(weapons=True)
        r = engine.screen_deal(d)
        assert r.hard_flag_count == 1
        assert r.has_deal_breaker is True
        assert any(f.flag_id == "RF_WEAPONS" for f in r.red_flags)

    def test_sanctions_hard_flag(self, engine):
        d = _deal(sanctions=True)
        r = engine.screen_deal(d)
        assert r.hard_flag_count == 1
        assert any(f.flag_id == "RF_SANCTIONS" for f in r.red_flags)

    def test_ungc_hard_flag(self, engine):
        d = _deal(ungc=True)
        r = engine.screen_deal(d)
        assert r.hard_flag_count == 1
        assert any(f.flag_id == "RF_UNGC" for f in r.red_flags)

    def test_child_labor_hard_flag(self, engine):
        d = _deal(child_labor=True)
        r = engine.screen_deal(d)
        assert r.hard_flag_count == 1
        assert any(f.flag_id == "RF_CHILD_LABOR" for f in r.red_flags)

    def test_multiple_hard_flags(self, engine):
        d = _deal(weapons=True, sanctions=True, ungc=True)
        r = engine.screen_deal(d)
        assert r.hard_flag_count == 3

    def test_high_carbon_no_transition_soft_flag(self, engine):
        d = _deal(sector="Energy", transition_plan=False)
        r = engine.screen_deal(d)
        assert r.soft_flag_count >= 1
        assert any(f.flag_id == "RF_NO_TRANSITION" for f in r.red_flags)

    def test_high_carbon_with_transition_no_flag(self, engine):
        d = _deal(sector="Energy", transition_plan=True)
        r = engine.screen_deal(d)
        transition_flags = [f for f in r.red_flags if f.flag_id == "RF_NO_TRANSITION"]
        assert len(transition_flags) == 0

    def test_env_incident_soft_flag(self, engine):
        d = _deal(env_incident=True)
        r = engine.screen_deal(d)
        assert any(f.flag_id == "RF_ENV_INCIDENT" for f in r.red_flags)
        assert any(f.severity == "soft" for f in r.red_flags if f.flag_id == "RF_ENV_INCIDENT")

    def test_tax_haven_soft_flag(self, engine):
        d = _deal(tax_haven=True)
        r = engine.screen_deal(d)
        assert any(f.flag_id == "RF_TAX_HAVEN" for f in r.red_flags)

    def test_high_dimension_score_triggers_flag(self, engine):
        """Dimension avg > 4.0 triggers a soft flag."""
        d = _deal_with_scores(env=5, soc=2, gov=2, trans=2, phys=2)
        r = engine.screen_deal(d)
        env_flags = [f for f in r.red_flags if "ENVIRONMENTAL" in f.flag_id]
        assert len(env_flags) == 1


# ===========================================================================
# Recommendation Tests
# ===========================================================================

class TestRecommendation:
    def test_proceed_for_clean_low_risk(self, engine):
        d = _deal_with_scores(env=2, soc=2, gov=2, trans=2, phys=2)
        r = engine.screen_deal(d)
        assert r.screening_recommendation == "proceed"
        assert len(r.conditions) == 0

    def test_reject_with_hard_flag(self, engine):
        d = _deal(weapons=True)
        r = engine.screen_deal(d)
        assert r.screening_recommendation == "reject"

    def test_reject_critical_risk(self, engine):
        d = _deal_with_scores(env=5, soc=5, gov=5, trans=5, phys=5)
        r = engine.screen_deal(d)
        assert r.screening_recommendation == "reject"

    def test_proceed_with_conditions_soft_flags(self, engine):
        d = _deal(sector="Energy", transition_plan=False)
        r = engine.screen_deal(d)
        assert r.screening_recommendation == "proceed_with_conditions"
        assert len(r.conditions) >= 1

    def test_proceed_with_conditions_high_risk(self, engine):
        d = _deal_with_scores(env=4, soc=4, gov=3, trans=4, phys=3)
        r = engine.screen_deal(d)
        assert r.screening_recommendation == "proceed_with_conditions"


# ===========================================================================
# Sector Heatmap Tests
# ===========================================================================

class TestSectorHeatmap:
    def test_heatmap_sectors_present(self, engine):
        heatmap = engine.get_sector_heatmap()
        sectors = [h["sector"] for h in heatmap]
        assert "Energy" in sectors
        assert "Technology" in sectors
        assert "Financials" in sectors

    def test_heatmap_dimensions_complete(self, engine):
        heatmap = engine.get_sector_heatmap()
        for entry in heatmap:
            assert "environmental" in entry
            assert "social" in entry
            assert "governance" in entry
            assert "transition_risk" in entry
            assert "physical_risk" in entry
            assert "overall_risk" in entry

    def test_energy_highest_transition_risk(self, engine):
        heatmap = engine.get_sector_heatmap()
        energy = next(h for h in heatmap if h["sector"] == "Energy")
        assert energy["transition_risk"] == 5

    def test_technology_low_physical_risk(self, engine):
        heatmap = engine.get_sector_heatmap()
        tech = next(h for h in heatmap if h["sector"] == "Technology")
        assert tech["physical_risk"] == 1

    def test_all_scores_1_to_5(self, engine):
        heatmap = engine.get_sector_heatmap()
        for entry in heatmap:
            for dim in ["environmental", "social", "governance", "transition_risk", "physical_risk"]:
                assert 1 <= entry[dim] <= 5


# ===========================================================================
# Deal Comparison Tests
# ===========================================================================

class TestDealComparison:
    def test_comparison_returns_all_deals(self, engine):
        deals = [
            _deal_with_scores("D1", "Co A", env=2, soc=2, gov=2, trans=2, phys=2),
            _deal_with_scores("D2", "Co B", env=4, soc=4, gov=4, trans=4, phys=4),
        ]
        rows = engine.compare_deals(deals)
        assert len(rows) == 2

    def test_comparison_scores_differ(self, engine):
        deals = [
            _deal_with_scores("D1", "Co A", env=1, soc=1, gov=1, trans=1, phys=1),
            _deal_with_scores("D2", "Co B", env=5, soc=5, gov=5, trans=5, phys=5),
        ]
        rows = engine.compare_deals(deals)
        assert rows[0].composite_esg_score < rows[1].composite_esg_score

    def test_comparison_includes_dimension_breakdown(self, engine):
        deals = [_deal_with_scores("D1", "Co A", env=2, soc=3, gov=4, trans=1, phys=5)]
        rows = engine.compare_deals(deals)
        assert "environmental" in rows[0].dimension_scores
        assert rows[0].dimension_scores["environmental"] == 2.0

    def test_comparison_flags_deal_breaker(self, engine):
        deals = [
            _deal("D1", "Clean Co"),
            _deal("D2", "Weapons Co", weapons=True),
        ]
        rows = engine.compare_deals(deals)
        assert rows[0].has_deal_breaker is False
        assert rows[1].has_deal_breaker is True


# ===========================================================================
# Pipeline Summary Tests
# ===========================================================================

class TestPipelineSummary:
    def test_empty_pipeline(self, engine):
        r = engine.pipeline_summary([])
        assert r.total_deals == 0
        assert r.avg_deal_size_eur == 0
        assert r.avg_esg_score == 0

    def test_counts_by_stage(self, engine):
        deals = [
            _deal("D1", stage="sourcing"),
            _deal("D2", stage="sourcing"),
            _deal("D3", stage="dd"),
        ]
        r = engine.pipeline_summary(deals)
        assert r.total_deals == 3
        assert r.deals_by_stage["sourcing"] == 2
        assert r.deals_by_stage["dd"] == 1

    def test_counts_by_sector(self, engine):
        deals = [
            _deal("D1", sector="Technology"),
            _deal("D2", sector="Technology"),
            _deal("D3", sector="Healthcare"),
        ]
        r = engine.pipeline_summary(deals)
        assert r.deals_by_sector["Technology"] == 2
        assert r.deals_by_sector["Healthcare"] == 1

    def test_avg_deal_size(self, engine):
        deals = [
            _deal("D1", deal_size=100_000_000),
            _deal("D2", deal_size=200_000_000),
        ]
        r = engine.pipeline_summary(deals)
        assert r.avg_deal_size_eur == 150_000_000.0

    def test_red_flag_deals_counted(self, engine):
        deals = [
            _deal("D1"),
            _deal("D2", ungc=True),
            _deal("D3", tax_haven=True),
        ]
        r = engine.pipeline_summary(deals)
        assert r.red_flag_deals == 2  # D2 (ungc) and D3 (tax_haven)
        assert r.deal_breaker_deals == 1  # D2 (ungc is hard)

    def test_pipeline_includes_heatmap(self, engine):
        deals = [_deal("D1")]
        r = engine.pipeline_summary(deals)
        assert len(r.sector_heatmap) == len(SECTOR_ESG_RISK)

    def test_pipeline_includes_comparison_table(self, engine):
        deals = [_deal("D1"), _deal("D2")]
        r = engine.pipeline_summary(deals)
        assert len(r.comparison_table) == 2


# ===========================================================================
# Reference Data Tests
# ===========================================================================

class TestReferenceData:
    def test_sector_heatmap_count(self):
        assert len(SECTOR_ESG_RISK) == 11

    def test_sub_dimensions_count(self):
        assert len(ESG_SUB_DIMENSIONS) == 5
        for dim, subs in ESG_SUB_DIMENSIONS.items():
            assert len(subs) == 4

    def test_high_carbon_sectors(self):
        assert "Energy" in HIGH_CARBON_SECTORS
        assert "Utilities" in HIGH_CARBON_SECTORS
        assert "Materials" in HIGH_CARBON_SECTORS
        assert "Technology" not in HIGH_CARBON_SECTORS
