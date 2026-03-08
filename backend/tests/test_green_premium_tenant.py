"""
Tests for Green Premium Engine + Tenant ESG Tracker
====================================================
"""
import pytest

from services.green_premium_engine import (
    GreenPremiumEngine,
    PropertyGreenInput,
    GREEN_RENT_PREMIUM,
    EPC_CAP_RATE_ADJUSTMENT_BPS,
    EPC_RENT_DISCOUNT,
)
from services.tenant_esg_tracker import (
    TenantESGTracker,
    TenantInput,
    PropertyTenantInput,
    GreenLeaseClause,
    SECTOR_BENCHMARKS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gp_engine():
    return GreenPremiumEngine()


@pytest.fixture
def tenant_tracker():
    return TenantESGTracker()


def _green_prop(
    pid="P1", epc="B", rent_m2=300.0, area=5000.0,
    value=10_000_000.0, cap=5.5, noi=500_000.0,
    certs=None, country="GB",
) -> PropertyGreenInput:
    return PropertyGreenInput(
        property_id=pid, name=f"Property {pid}",
        epc_rating=epc, base_rent_per_m2=rent_m2,
        floor_area_m2=area, market_value=value,
        base_cap_rate_pct=cap, noi=noi,
        certifications=certs or {}, country=country,
    )


def _tenant(
    tid="T1", name="TechCo", sector="technology",
    area=2000.0, rent=200_000.0, headcount=100,
    s1=50.0, s2=150.0, clauses=None,
    energy_rpt=True, sbt=True, nz=False,
) -> TenantInput:
    return TenantInput(
        tenant_id=tid, name=name, sector=sector,
        leased_area_m2=area, annual_rent_eur=rent,
        headcount=headcount, scope1_tco2e=s1, scope2_tco2e=s2,
        green_lease_clauses=clauses or [],
        energy_data_reported=energy_rpt,
        has_science_based_target=sbt,
        has_net_zero_commitment=nz,
    )


def _property_tenant(pid="P1", area=10000.0, tenants=None) -> PropertyTenantInput:
    return PropertyTenantInput(
        property_id=pid, name=f"Property {pid}",
        total_lettable_area_m2=area,
        tenants=tenants or [],
    )


# ===========================================================================
# Green Premium Engine Tests
# ===========================================================================

class TestGreenPremiumBasics:
    def test_green_property_classification(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="A"))
        assert result.is_green is True
        assert result.is_brown is False

    def test_brown_property_classification(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="F"))
        assert result.is_green is False
        assert result.is_brown is True

    def test_neutral_property(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="C"))
        assert result.is_green is False
        assert result.is_brown is False


class TestCertificationPremium:
    def test_leed_gold_premium(self, gp_engine):
        prop = _green_prop(epc="A", certs={"LEED": "Gold"})
        result = gp_engine.assess_property(prop)
        assert result.total_cert_premium_pct == 8.0

    def test_breeam_excellent_premium(self, gp_engine):
        prop = _green_prop(epc="A", certs={"BREEAM": "Excellent"})
        result = gp_engine.assess_property(prop)
        assert result.total_cert_premium_pct == 7.0

    def test_multiple_certs_uses_highest(self, gp_engine):
        prop = _green_prop(epc="A", certs={"LEED": "Platinum", "BREEAM": "Good"})
        result = gp_engine.assess_property(prop)
        # LEED Platinum = 12% is highest, not additive
        assert result.total_cert_premium_pct == 12.0

    def test_no_certification(self, gp_engine):
        prop = _green_prop(epc="A", certs={})
        result = gp_engine.assess_property(prop)
        assert result.total_cert_premium_pct == 0.0

    def test_unknown_cert_level(self, gp_engine):
        prop = _green_prop(epc="A", certs={"LEED": "Unknown"})
        result = gp_engine.assess_property(prop)
        assert result.total_cert_premium_pct == 0.0


class TestEPCAdjustments:
    def test_green_epc_no_rent_discount(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="A"))
        assert result.epc_rent_adjustment_pct == 0.0

    def test_brown_epc_rent_discount(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="G"))
        assert result.epc_rent_adjustment_pct == -12.0

    def test_cap_rate_compression_for_green(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="A"))
        assert result.epc_cap_rate_adjustment_bps == -20  # 20bps compression

    def test_cap_rate_expansion_for_brown(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="G"))
        assert result.epc_cap_rate_adjustment_bps == 80  # 80bps expansion

    def test_neutral_epc_no_cap_adjustment(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="C"))
        assert result.epc_cap_rate_adjustment_bps == 0


class TestValueImpact:
    def test_green_property_value_increases(self, gp_engine):
        # Cap rate compression -> higher value
        # NOI/cap = 500K/0.055 = 9,090,909 (use as market value for consistency)
        prop = _green_prop(epc="A", cap=5.5, noi=500_000, value=9_090_909)
        result = gp_engine.assess_property(prop)
        # Adjusted cap = 5.5 - 0.20 = 5.30%, adjusted value = 500K/0.053 = 9,433,962
        assert result.green_adjusted_value > result.base_market_value

    def test_brown_property_value_decreases(self, gp_engine):
        # Cap rate expansion -> lower value
        prop = _green_prop(epc="G", cap=5.5, noi=500_000)
        result = gp_engine.assess_property(prop)
        assert result.green_adjusted_value < result.base_market_value

    def test_brown_vacancy_cost(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="G", rent_m2=300, area=5000))
        assert result.annual_void_cost_eur > 0
        assert result.brown_vacancy_months == 3.0

    def test_green_no_vacancy_cost(self, gp_engine):
        result = gp_engine.assess_property(_green_prop(epc="A"))
        assert result.annual_void_cost_eur == 0.0


class TestNetRent:
    def test_certified_green_rent_increases(self, gp_engine):
        prop = _green_prop(epc="A", certs={"LEED": "Gold"}, rent_m2=300)
        result = gp_engine.assess_property(prop)
        assert result.green_adjusted_rent_per_m2 > 300

    def test_brown_rent_decreases(self, gp_engine):
        prop = _green_prop(epc="G", rent_m2=300)
        result = gp_engine.assess_property(prop)
        assert result.green_adjusted_rent_per_m2 < 300

    def test_net_change_pct_calculated(self, gp_engine):
        prop = _green_prop(epc="B", certs={"BREEAM": "Excellent"}, rent_m2=300)
        result = gp_engine.assess_property(prop)
        expected_pct = 7.0  # BREEAM Excellent + EPC B (0 discount)
        assert abs(result.net_rent_change_pct - expected_pct) < 0.01


class TestPortfolioGreenPremium:
    def test_portfolio_counts(self, gp_engine):
        props = [
            _green_prop("P1", epc="A"),
            _green_prop("P2", epc="C"),
            _green_prop("P3", epc="G"),
        ]
        result = gp_engine.assess_portfolio(props)
        assert result.green_count == 1
        assert result.neutral_count == 1
        assert result.brown_count == 1

    def test_portfolio_value_impact(self, gp_engine):
        props = [
            _green_prop("P1", epc="A", noi=500_000, cap=5.5, value=10_000_000),
            _green_prop("P2", epc="G", noi=500_000, cap=5.5, value=10_000_000),
        ]
        result = gp_engine.assess_portfolio(props)
        assert result.portfolio_value_impact_eur != 0  # Should have net impact

    def test_empty_portfolio(self, gp_engine):
        result = gp_engine.assess_portfolio([])
        assert result.total_properties == 0
        assert result.portfolio_value_impact_eur == 0


# ===========================================================================
# Tenant ESG Tracker Tests
# ===========================================================================

class TestTenantESGProfile:
    def test_carbon_intensity_per_employee(self, tenant_tracker):
        t = _tenant(headcount=100, s1=50, s2=150)
        result = tenant_tracker.assess_tenant(t)
        assert result.carbon_intensity_per_employee == 2.0  # 200/100

    def test_vs_benchmark(self, tenant_tracker):
        # Technology benchmark = 3.5 tCO2e/emp
        t = _tenant(sector="technology", headcount=100, s1=50, s2=150)
        result = tenant_tracker.assess_tenant(t)
        # 2.0 vs 3.5 benchmark -> negative % (below benchmark = good)
        assert result.vs_benchmark_pct < 0

    def test_green_lease_score(self, tenant_tracker):
        t = _tenant(clauses=["energy_data_sharing", "fitout_standards", "waste_management"])
        result = tenant_tracker.assess_tenant(t)
        # 0.25 + 0.20 + 0.15 = 0.60 * 100 = 60
        assert result.green_lease_score == 60.0

    def test_no_green_lease_clauses(self, tenant_tracker):
        t = _tenant(clauses=[])
        result = tenant_tracker.assess_tenant(t)
        assert result.green_lease_score == 0.0

    def test_esg_score_bounded(self, tenant_tracker):
        t = _tenant(clauses=list(c.value for c in GreenLeaseClause),
                    energy_rpt=True, sbt=True, nz=True)
        result = tenant_tracker.assess_tenant(t)
        assert 0 <= result.tenant_esg_score <= 100

    def test_zero_headcount(self, tenant_tracker):
        t = _tenant(headcount=0, s1=0, s2=0)
        result = tenant_tracker.assess_tenant(t)
        assert result.carbon_intensity_per_employee == 0


class TestPropertyTenantESG:
    def test_occupancy_rate(self, tenant_tracker):
        tenants = [
            _tenant("T1", area=3000),
            _tenant("T2", area=4000),
        ]
        prop = _property_tenant(area=10000, tenants=tenants)
        result = tenant_tracker.assess_property(prop)
        assert result.occupancy_rate_pct == 70.0

    def test_green_lease_coverage(self, tenant_tracker):
        tenants = [
            _tenant("T1", area=6000, clauses=["energy_data_sharing"]),
            _tenant("T2", area=4000, clauses=[]),
        ]
        prop = _property_tenant(area=10000, tenants=tenants)
        result = tenant_tracker.assess_property(prop)
        assert result.green_lease_coverage_pct == 60.0  # 6000/10000

    def test_clause_coverage(self, tenant_tracker):
        tenants = [
            _tenant("T1", area=6000, clauses=["energy_data_sharing"]),
            _tenant("T2", area=4000, clauses=["energy_data_sharing", "waste_management"]),
        ]
        prop = _property_tenant(area=10000, tenants=tenants)
        result = tenant_tracker.assess_property(prop)
        # energy_data_sharing: 6000+4000=10000/10000=100%
        assert result.clause_coverage["energy_data_sharing"] == 100.0
        # waste_management: 4000/10000=40%
        assert result.clause_coverage["waste_management"] == 40.0

    def test_total_emissions(self, tenant_tracker):
        tenants = [
            _tenant("T1", s1=50, s2=150),
            _tenant("T2", s1=30, s2=100),
        ]
        prop = _property_tenant(tenants=tenants)
        result = tenant_tracker.assess_property(prop)
        assert result.total_scope1_tco2e == 80.0
        assert result.total_scope2_tco2e == 250.0

    def test_engagement_metrics(self, tenant_tracker):
        tenants = [
            _tenant("T1", area=6000, energy_rpt=True, sbt=True, nz=True),
            _tenant("T2", area=4000, energy_rpt=False, sbt=False, nz=False),
        ]
        prop = _property_tenant(tenants=tenants)
        result = tenant_tracker.assess_property(prop)
        assert result.energy_data_reporting_pct == 60.0
        assert result.sbt_coverage_pct == 60.0
        assert result.net_zero_coverage_pct == 60.0

    def test_empty_tenants(self, tenant_tracker):
        prop = _property_tenant(tenants=[])
        result = tenant_tracker.assess_property(prop)
        assert result.tenant_count == 0
        assert result.property_tenant_esg_score == 0


class TestPortfolioTenantESG:
    def test_portfolio_totals(self, tenant_tracker):
        props = [
            _property_tenant("P1", tenants=[_tenant("T1"), _tenant("T2")]),
            _property_tenant("P2", tenants=[_tenant("T3")]),
        ]
        result = tenant_tracker.assess_portfolio(props)
        assert result.total_properties == 2
        assert result.total_tenants == 3

    def test_portfolio_emissions(self, tenant_tracker):
        props = [
            _property_tenant("P1", tenants=[_tenant("T1", s1=50, s2=150)]),
            _property_tenant("P2", tenants=[_tenant("T2", s1=30, s2=100)]),
        ]
        result = tenant_tracker.assess_portfolio(props)
        assert result.total_tenant_emissions_tco2e == 330.0

    def test_empty_portfolio(self, tenant_tracker):
        result = tenant_tracker.assess_portfolio([])
        assert result.total_properties == 0
        assert result.portfolio_tenant_esg_score == 0

    def test_portfolio_esg_score_bounded(self, tenant_tracker):
        props = [
            _property_tenant("P1", tenants=[
                _tenant("T1", clauses=list(c.value for c in GreenLeaseClause),
                        energy_rpt=True, sbt=True, nz=True)
            ]),
        ]
        result = tenant_tracker.assess_portfolio(props)
        assert 0 <= result.portfolio_tenant_esg_score <= 100


class TestReferenceData:
    def test_all_epc_ratings_have_cap_adjustment(self):
        for epc in ["A+", "A", "B", "C", "D", "E", "F", "G"]:
            assert epc in EPC_CAP_RATE_ADJUSTMENT_BPS

    def test_rent_discount_negative_for_brown(self):
        for epc in ["E", "F", "G"]:
            assert EPC_RENT_DISCOUNT[epc] < 0

    def test_sector_benchmarks_positive(self):
        for sector, value in SECTOR_BENCHMARKS.items():
            assert value > 0
