"""
Tests for SFDR Report Generator + Exclusion List Engine
=========================================================
"""
import pytest

from services.sfdr_report_generator import (
    SFDRReportGenerator,
    SFDRFundInput,
    SFDRHolding,
    PAI_INDICATOR_NAMES,
    ART8_SECTIONS,
    ART9_SECTIONS,
)
from services.exclusion_list_engine import (
    ExclusionListEngine,
    HoldingScreenInput,
    CustomExclusionRule,
    DEFAULT_EXCLUSION_RULES,
    ExclusionCategory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sfdr_gen():
    return SFDRReportGenerator()


@pytest.fixture
def excl_engine():
    return ExclusionListEngine()


def _sfdr_holding(
    hid="H1", name="Stock A", sector="Technology", country="US",
    weight=25.0, mv=1_000_000, tax=30.0, env=10.0, soc=5.0,
    esg=72.0, dnsh=True, ci=100.0,
) -> SFDRHolding:
    return SFDRHolding(
        holding_id=hid, security_name=name, sector=sector,
        country=country, weight_pct=weight, market_value=mv,
        taxonomy_aligned_pct=tax, sustainable_environmental_pct=env,
        sustainable_social_pct=soc, esg_score=esg,
        dnsh_compliant=dnsh, carbon_intensity=ci,
    )


def _sfdr_fund(
    holdings=None, sfdr="art8", pai=None, prior_pai=None,
    min_tax=10.0, min_sus=30.0, aum=10_000_000,
) -> SFDRFundInput:
    return SFDRFundInput(
        fund_id="F1", fund_name="Test Fund",
        sfdr_classification=sfdr, fund_type="ucits",
        reporting_period="2025-01-01 to 2025-12-31",
        reference_benchmark="MSCI World",
        aum=aum,
        promoted_characteristics=["climate", "social"],
        esg_strategy="integration",
        minimum_taxonomy_pct=min_tax,
        minimum_sustainable_pct=min_sus,
        holdings=holdings or [],
        pai_values=pai or {},
        prior_pai_values=prior_pai or {},
    )


def _screen_holding(
    hid="H1", name="Stock A", weight=10.0,
    weapons=0.0, tobacco=0.0, coal=0.0, coal_gen=0.0,
    arctic=0.0, oil_sands=0.0, nuclear=False, ungc=False,
    custom=None,
) -> HoldingScreenInput:
    return HoldingScreenInput(
        holding_id=hid, security_name=name, weight_pct=weight,
        controversial_weapons_revenue_pct=weapons,
        tobacco_revenue_pct=tobacco,
        thermal_coal_revenue_pct=coal,
        coal_power_generation_pct=coal_gen,
        arctic_oil_revenue_pct=arctic,
        oil_sands_revenue_pct=oil_sands,
        nuclear_weapons_involved=nuclear,
        ungc_violation=ungc,
        custom_exclusion_flags=custom or {},
    )


# ===========================================================================
# SFDR Report Generator Tests
# ===========================================================================

class TestSFDRProportions:
    def test_proportion_calculation(self, sfdr_gen):
        h = [_sfdr_holding(weight=100, tax=30, env=10, soc=5)]
        fund = _sfdr_fund(holdings=h)
        r = sfdr_gen.generate(fund)
        assert r.proportion.taxonomy_aligned_pct == 30.0
        assert r.proportion.other_environmental_pct == 10.0
        assert r.proportion.social_pct == 5.0
        assert r.proportion.not_sustainable_pct == 55.0

    def test_multi_holding_proportions(self, sfdr_gen):
        h = [
            _sfdr_holding("H1", weight=60, tax=40, env=10, soc=5),
            _sfdr_holding("H2", weight=40, tax=20, env=5, soc=10),
        ]
        fund = _sfdr_fund(holdings=h)
        r = sfdr_gen.generate(fund)
        # Tax: (60*40 + 40*20)/100 = 3200/100 = 32
        assert r.proportion.taxonomy_aligned_pct == 32.0


class TestSFDRTopInvestments:
    def test_top_15_sorted_by_weight(self, sfdr_gen):
        h = [_sfdr_holding(f"H{i}", weight=100 - i * 5) for i in range(20)]
        fund = _sfdr_fund(holdings=h)
        r = sfdr_gen.generate(fund)
        assert len(r.top_investments) == 15
        assert r.top_investments[0].weight_pct >= r.top_investments[-1].weight_pct


class TestSFDRSectorGeo:
    def test_sector_breakdown(self, sfdr_gen):
        h = [
            _sfdr_holding("H1", sector="Technology", weight=60),
            _sfdr_holding("H2", sector="Healthcare", weight=40),
        ]
        fund = _sfdr_fund(holdings=h)
        r = sfdr_gen.generate(fund)
        sectors = {s.sector: s for s in r.sector_breakdown}
        assert "Technology" in sectors
        assert "Healthcare" in sectors
        assert sectors["Technology"].weight_pct == 60.0

    def test_geography_breakdown(self, sfdr_gen):
        h = [
            _sfdr_holding("H1", country="US", weight=60),
            _sfdr_holding("H2", country="DE", weight=40),
        ]
        fund = _sfdr_fund(holdings=h)
        r = sfdr_gen.generate(fund)
        geo = {g.country: g for g in r.geography_breakdown}
        assert geo["US"].weight_pct == 60.0
        assert geo["DE"].weight_pct == 40.0


class TestSFDRCompliance:
    def test_art8_compliant_when_targets_met(self, sfdr_gen):
        h = [_sfdr_holding(weight=100, tax=30, env=10, soc=5)]
        fund = _sfdr_fund(holdings=h, sfdr="art8", min_tax=10, min_sus=30)
        r = sfdr_gen.generate(fund)
        assert r.taxonomy_target_met is True
        assert r.sustainable_target_met is True
        assert r.is_art8_compliant is True

    def test_art8_fails_taxonomy_target(self, sfdr_gen):
        h = [_sfdr_holding(weight=100, tax=5, env=10, soc=5)]
        fund = _sfdr_fund(holdings=h, sfdr="art8", min_tax=10)
        r = sfdr_gen.generate(fund)
        assert r.taxonomy_target_met is False
        assert r.is_art8_compliant is False
        assert any("Taxonomy" in i for i in r.compliance_issues)

    def test_art9_requires_high_sustainable(self, sfdr_gen):
        h = [_sfdr_holding(weight=100, tax=20, env=10, soc=5)]
        fund = _sfdr_fund(holdings=h, sfdr="art9", min_tax=10, min_sus=30)
        r = sfdr_gen.generate(fund)
        # Sustainable = 20+10+5 = 35% < 90% required for Art.9
        assert r.is_art9_compliant is False

    def test_art9_compliant(self, sfdr_gen):
        h = [_sfdr_holding(weight=100, tax=60, env=20, soc=15)]
        fund = _sfdr_fund(holdings=h, sfdr="art9", min_tax=50, min_sus=80)
        r = sfdr_gen.generate(fund)
        assert r.actual_sustainable_pct == 95.0
        assert r.is_art9_compliant is True


class TestSFDRPAI:
    def test_pai_summary_with_yoy(self, sfdr_gen):
        pai = {"PAI_5": 120.0, "PAI_6": 5.0}
        prior = {"PAI_5": 150.0, "PAI_6": 6.0}
        fund = _sfdr_fund(holdings=[_sfdr_holding()], pai=pai, prior_pai=prior)
        r = sfdr_gen.generate(fund)
        assert len(r.pai_summary) == 2
        waci_row = next(p for p in r.pai_summary if p.indicator_id == "PAI_5")
        assert waci_row.yoy_change < 0  # WACI decreased


class TestSFDRSections:
    def test_art8_sections(self, sfdr_gen):
        fund = _sfdr_fund(holdings=[_sfdr_holding()], sfdr="art8")
        r = sfdr_gen.generate(fund)
        assert "environmental_social_characteristics" in r.applicable_sections
        assert "sustainable_investment_objective" not in r.applicable_sections

    def test_art9_has_extra_sections(self, sfdr_gen):
        fund = _sfdr_fund(holdings=[_sfdr_holding()], sfdr="art9")
        r = sfdr_gen.generate(fund)
        assert "sustainable_investment_objective" in r.applicable_sections
        assert "no_significant_harm" in r.applicable_sections


# ===========================================================================
# Exclusion List Engine Tests
# ===========================================================================

class TestExclusionScreening:
    def test_clean_portfolio(self, excl_engine):
        h = [_screen_holding("H1"), _screen_holding("H2")]
        result = excl_engine.screen_fund("F1", "Test", "art8", h)
        assert result.is_compliant is True
        assert result.breach_count == 0

    def test_weapons_zero_tolerance(self, excl_engine):
        h = [_screen_holding("H1", weapons=0.5)]  # Any > 0%
        result = excl_engine.screen_fund("F1", "Test", "art8", h)
        assert result.is_compliant is False
        assert result.hard_breach_count == 1

    def test_tobacco_threshold(self, excl_engine):
        h = [_screen_holding("H1", tobacco=6.0)]  # >5% threshold
        result = excl_engine.screen_fund("F1", "Test", "art8", h)
        assert result.breach_count == 1
        assert result.breaches[0].severity == "soft"

    def test_tobacco_below_threshold_ok(self, excl_engine):
        h = [_screen_holding("H1", tobacco=3.0)]  # <5% ok
        result = excl_engine.screen_fund("F1", "Test", "art8", h)
        assert result.is_compliant is True

    def test_thermal_coal_mining(self, excl_engine):
        h = [_screen_holding("H1", coal=12.0)]  # >10% mining
        result = excl_engine.screen_fund("F1", "Test", "art8plus", h)
        assert result.breach_count == 1

    def test_thermal_coal_generation(self, excl_engine):
        h = [_screen_holding("H1", coal_gen=35.0)]  # >30% generation
        result = excl_engine.screen_fund("F1", "Test", "art8plus", h)
        assert result.breach_count == 1

    def test_ungc_violation(self, excl_engine):
        h = [_screen_holding("H1", ungc=True)]
        result = excl_engine.screen_fund("F1", "Test", "art8", h)
        assert result.breach_count == 1
        assert result.category_summary.get("ungc_violations", 0) == 1

    def test_multiple_breaches_same_holding(self, excl_engine):
        h = [_screen_holding("H1", weapons=1.0, ungc=True)]
        result = excl_engine.screen_fund("F1", "Test", "art8", h)
        assert result.breach_count == 2  # Two different categories
        # But only 1 unique holding breached
        unique_holdings = set(b.holding_id for b in result.breaches)
        assert len(unique_holdings) == 1


class TestExclusionSFDRApplicability:
    def test_art6_only_controversial_weapons(self, excl_engine):
        rules = excl_engine.get_rules("art6")
        categories = [r["category"] for r in rules]
        assert "controversial_weapons" in categories
        # Tobacco should not apply to art6
        assert "tobacco" not in categories

    def test_art9_includes_all(self, excl_engine):
        rules = excl_engine.get_rules("art9")
        categories = [r["category"] for r in rules]
        assert "controversial_weapons" in categories
        assert "thermal_coal" in categories
        assert "arctic_oil_gas" in categories
        assert "oil_sands" in categories


class TestCustomExclusionRules:
    def test_custom_rule_breach(self):
        custom = [CustomExclusionRule(
            rule_id="gambling", name="Gambling",
            description="Companies with >10% gambling revenue",
            flag_key="gambling_flag",
        )]
        engine = ExclusionListEngine(custom_rules=custom)
        h = [_screen_holding("H1", custom={"gambling_flag": True})]
        result = engine.screen_fund("F1", "Test", "art8", h)
        assert result.breach_count >= 1
        gambling_breach = [b for b in result.breaches if "gambling" in b.category]
        assert len(gambling_breach) == 1

    def test_custom_rule_no_breach(self):
        custom = [CustomExclusionRule(
            rule_id="gambling", name="Gambling",
            description="Companies with >10% gambling revenue",
            flag_key="gambling_flag",
        )]
        engine = ExclusionListEngine(custom_rules=custom)
        h = [_screen_holding("H1", custom={"gambling_flag": False})]
        result = engine.screen_fund("F1", "Test", "art8", h)
        gambling_breach = [b for b in result.breaches if "gambling" in b.category]
        assert len(gambling_breach) == 0


class TestExclusionReferenceData:
    def test_default_rules_count(self):
        assert len(DEFAULT_EXCLUSION_RULES) == 7

    def test_all_categories_have_names(self):
        for cat, rule in DEFAULT_EXCLUSION_RULES.items():
            assert "name" in rule
            assert "description" in rule
            assert "applies_to" in rule

    def test_pai_indicators_populated(self):
        assert len(PAI_INDICATOR_NAMES) > 0
        assert "PAI_5" in PAI_INDICATOR_NAMES  # WACI
