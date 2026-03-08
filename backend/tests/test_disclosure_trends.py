"""
Tests for Disclosure Completeness & Trend Analytics
=====================================================
"""
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.disclosure_completeness import (
    DisclosureCompletenessEngine,
    FRAMEWORK_REQUIREMENTS,
)
from services.trend_analytics import (
    TrendAnalyticsEngine,
    KPI_DEFINITIONS,
    PEER_BENCHMARKS,
)

_disclosure = DisclosureCompletenessEngine()
_trends = TrendAnalyticsEngine()


# ═══════════════════════════════════════════════════════════════════════════
# Disclosure Completeness Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDisclosureBasic:
    """Basic disclosure completeness tests."""

    def test_full_esrs_e1_compliance(self):
        dps = {dp["dp_id"]: 1.0 for dp in FRAMEWORK_REQUIREMENTS["ESRS_E1"]["required_dps"]}
        res = _disclosure.assess("Full Corp", dps, frameworks=["ESRS_E1"])
        assert res.framework_results[0].completeness_pct == 100.0
        assert res.framework_results[0].readiness == "compliant"

    def test_empty_disclosure(self):
        res = _disclosure.assess("Empty Corp", {}, frameworks=["ESRS_E1"])
        assert res.framework_results[0].completeness_pct == 0.0
        assert res.framework_results[0].readiness == "early_stage"

    def test_partial_disclosure(self):
        # Provide 8 of 15 E1 DPs (53%)
        e1_dps = FRAMEWORK_REQUIREMENTS["ESRS_E1"]["required_dps"][:8]
        dps = {dp["dp_id"]: 1.0 for dp in e1_dps}
        res = _disclosure.assess("Partial Corp", dps, frameworks=["ESRS_E1"])
        fr = res.framework_results[0]
        assert fr.provided_count == 8
        assert fr.missing_count == 7
        assert 50 < fr.completeness_pct < 60
        assert fr.readiness == "partial"

    def test_near_compliant_threshold(self):
        # 11 of 15 = 73%
        e1_dps = FRAMEWORK_REQUIREMENTS["ESRS_E1"]["required_dps"][:11]
        dps = {dp["dp_id"]: 1.0 for dp in e1_dps}
        res = _disclosure.assess("Near Corp", dps, frameworks=["ESRS_E1"])
        assert res.framework_results[0].readiness == "near_compliant"

    def test_entity_name_in_result(self):
        res = _disclosure.assess("Named Corp", {}, frameworks=["ESRS_E1"])
        assert res.entity_name == "Named Corp"

    def test_reporting_year(self):
        res = _disclosure.assess("Year Corp", {}, reporting_year=2025, frameworks=["ESRS_E1"])
        assert res.reporting_year == 2025


class TestMultiFramework:
    """Multi-framework assessment tests."""

    def test_all_frameworks_assessed(self):
        res = _disclosure.assess("All Corp", {})
        assert res.frameworks_assessed == len(FRAMEWORK_REQUIREMENTS)

    def test_specific_frameworks(self):
        res = _disclosure.assess("Select Corp", {}, frameworks=["ESRS_E1", "TCFD"])
        assert res.frameworks_assessed == 2

    def test_cross_framework_coverage(self):
        res = _disclosure.assess("Cross Corp", {}, frameworks=["ESRS_E1", "ISSB_S2"])
        assert "ESRS_E1" in res.cross_framework_coverage
        assert "ISSB_S2" in res.cross_framework_coverage

    def test_overall_readiness(self):
        # All empty → early_stage
        res = _disclosure.assess("Low Corp", {})
        assert res.overall_readiness == "early_stage"

    def test_priority_gaps_sorted(self):
        res = _disclosure.assess("Gaps Corp", {})
        assert len(res.priority_gaps) > 0
        # CSRD/ESRS gaps should come first (urgency=4)
        assert res.priority_gaps[0]["framework"] == "CSRD/ESRS"


class TestMissingDPs:
    """Test gap identification."""

    def test_missing_dps_list(self):
        res = _disclosure.assess("Miss Corp", {}, frameworks=["TCFD"])
        fr = res.framework_results[0]
        assert len(fr.missing_dps) == 11  # All TCFD DPs

    def test_missing_dp_has_label(self):
        res = _disclosure.assess("Label Corp", {}, frameworks=["TCFD"])
        for gap in res.framework_results[0].missing_dps:
            assert "label" in gap
            assert "dp_id" in gap

    def test_provided_dp_not_in_gaps(self):
        dps = {"TCFD_gov_board": 1.0}
        res = _disclosure.assess("Partial TCFD", dps, frameworks=["TCFD"])
        missing_ids = [g["dp_id"] for g in res.framework_results[0].missing_dps]
        assert "TCFD_gov_board" not in missing_ids


class TestDisclosureRefData:
    """Reference data tests."""

    def test_framework_requirements_count(self):
        req = _disclosure.get_framework_requirements()
        assert len(req) >= 9

    def test_framework_list(self):
        fl = _disclosure.get_framework_list()
        assert len(fl) >= 9
        for f in fl:
            assert "id" in f
            assert "total_dps" in f

    def test_sfdr_pai_has_14_indicators(self):
        assert FRAMEWORK_REQUIREMENTS["SFDR_PAI"]["total_dps"] == 14


# ═══════════════════════════════════════════════════════════════════════════
# Trend Analytics Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestTrendBasic:
    """Basic trend analysis tests."""

    def test_single_kpi_improving(self):
        series = {
            "scope1_tco2e": [
                {"year": 2021, "value": 100000},
                {"year": 2022, "value": 90000},
                {"year": 2023, "value": 80000},
            ]
        }
        res = _trends.analyse("Improving Corp", series)
        assert res.kpi_trends[0].trend_direction == "improving"

    def test_single_kpi_worsening(self):
        series = {
            "scope1_tco2e": [
                {"year": 2021, "value": 80000},
                {"year": 2022, "value": 90000},
                {"year": 2023, "value": 100000},
            ]
        }
        res = _trends.analyse("Worsening Corp", series)
        assert res.kpi_trends[0].trend_direction == "worsening"

    def test_stable_kpi(self):
        series = {
            "scope1_tco2e": [
                {"year": 2021, "value": 100000},
                {"year": 2023, "value": 100000},
            ]
        }
        res = _trends.analyse("Stable Corp", series)
        assert res.kpi_trends[0].trend_direction == "stable"

    def test_higher_better_improving(self):
        series = {
            "renewable_share_pct": [
                {"year": 2021, "value": 20},
                {"year": 2023, "value": 40},
            ]
        }
        res = _trends.analyse("Green Corp", series)
        assert res.kpi_trends[0].trend_direction == "improving"

    def test_single_data_point(self):
        series = {"scope1_tco2e": [{"year": 2023, "value": 50000}]}
        res = _trends.analyse("Single Corp", series)
        assert res.kpi_trends[0].trend_direction == "insufficient_data"


class TestTrendYoY:
    """Year-over-year change tests."""

    def test_yoy_count(self):
        series = {
            "scope1_tco2e": [
                {"year": 2021, "value": 100000},
                {"year": 2022, "value": 90000},
                {"year": 2023, "value": 80000},
            ]
        }
        res = _trends.analyse("YoY Corp", series)
        assert len(res.kpi_trends[0].yoy_changes) == 2

    def test_yoy_values(self):
        series = {
            "scope1_tco2e": [
                {"year": 2021, "value": 100000},
                {"year": 2022, "value": 90000},
            ]
        }
        res = _trends.analyse("YoY Val", series)
        yoy = res.kpi_trends[0].yoy_changes[0]
        assert yoy["change_abs"] == -10000
        assert yoy["change_pct"] == -10.0


class TestTrendCAGR:
    """CAGR calculation tests."""

    def test_cagr_decreasing(self):
        series = {
            "scope1_tco2e": [
                {"year": 2020, "value": 100000},
                {"year": 2023, "value": 70000},
            ]
        }
        res = _trends.analyse("CAGR Corp", series)
        cagr = res.kpi_trends[0].cagr_pct
        assert cagr is not None
        assert cagr < 0

    def test_cagr_increasing(self):
        series = {
            "renewable_share_pct": [
                {"year": 2020, "value": 20},
                {"year": 2023, "value": 40},
            ]
        }
        res = _trends.analyse("CAGR Inc", series)
        cagr = res.kpi_trends[0].cagr_pct
        assert cagr is not None
        assert cagr > 0


class TestTrendTargets:
    """Target tracking tests."""

    def test_on_track_lower_better(self):
        series = {
            "scope1_tco2e": [
                {"year": 2021, "value": 100000},
                {"year": 2023, "value": 60000},
            ]
        }
        targets = {"scope1_tco2e": 50000}
        res = _trends.analyse("Target Corp", series, targets=targets)
        assert res.kpi_trends[0].target_value == 50000
        # Decreasing trend → on_track
        assert res.kpi_trends[0].on_track is True

    def test_on_track_higher_better(self):
        series = {
            "renewable_share_pct": [
                {"year": 2021, "value": 30},
                {"year": 2023, "value": 60},
            ]
        }
        targets = {"renewable_share_pct": 50}
        res = _trends.analyse("Renew Target", series, targets=targets)
        assert res.kpi_trends[0].on_track is True

    def test_no_target(self):
        series = {"scope1_tco2e": [{"year": 2023, "value": 50000}]}
        res = _trends.analyse("No Target", series)
        assert res.kpi_trends[0].target_value is None
        assert res.kpi_trends[0].on_track is None


class TestTrendPeerBenchmark:
    """Peer benchmark comparison tests."""

    def test_peer_benchmark_present(self):
        series = {
            "financed_emissions_tco2e": [
                {"year": 2023, "value": 1200000},
            ]
        }
        res = _trends.analyse("Peer Corp", series, sector="financial_institutions")
        assert res.kpi_trends[0].peer_benchmark == 1500000
        assert res.kpi_trends[0].vs_peer_pct is not None

    def test_below_peer_negative_pct(self):
        series = {
            "financed_emissions_tco2e": [
                {"year": 2023, "value": 1000000},
            ]
        }
        res = _trends.analyse("Low Peer", series, sector="financial_institutions")
        # 1M vs 1.5M benchmark → -33.3%
        assert res.kpi_trends[0].vs_peer_pct < 0

    def test_no_peer_for_unknown_kpi(self):
        series = {"esrs_completeness_pct": [{"year": 2023, "value": 75}]}
        res = _trends.analyse("No Peer", series, sector="energy")
        assert res.kpi_trends[0].peer_benchmark is None


class TestTrendOverall:
    """Overall trajectory tests."""

    def test_positive_trajectory(self):
        series = {
            "scope1_tco2e": [{"year": 2021, "value": 100000}, {"year": 2023, "value": 70000}],
            "scope2_tco2e": [{"year": 2021, "value": 50000}, {"year": 2023, "value": 30000}],
            "renewable_share_pct": [{"year": 2021, "value": 20}, {"year": 2023, "value": 50}],
        }
        res = _trends.analyse("Positive Corp", series)
        assert res.improving_count == 3
        assert res.overall_trajectory == "positive"

    def test_negative_trajectory(self):
        series = {
            "scope1_tco2e": [{"year": 2021, "value": 70000}, {"year": 2023, "value": 100000}],
            "scope2_tco2e": [{"year": 2021, "value": 30000}, {"year": 2023, "value": 50000}],
            "renewable_share_pct": [{"year": 2021, "value": 50}, {"year": 2023, "value": 20}],
        }
        res = _trends.analyse("Negative Corp", series)
        assert res.worsening_count == 3
        assert res.overall_trajectory == "negative"

    def test_years_range(self):
        series = {
            "scope1_tco2e": [
                {"year": 2020, "value": 100000},
                {"year": 2023, "value": 80000},
            ]
        }
        res = _trends.analyse("Range Corp", series)
        assert res.years_range == "2020-2023"


class TestTrendRefData:
    """Reference data tests."""

    def test_kpi_definitions(self):
        defs = _trends.get_kpi_definitions()
        assert len(defs) >= 20

    def test_peer_benchmarks(self):
        benchmarks = _trends.get_peer_benchmarks()
        assert len(benchmarks) >= 5

    def test_sectors(self):
        sectors = _trends.get_sectors()
        assert "financial_institutions" in sectors
        assert "energy" in sectors

    def test_kpi_has_direction(self):
        for kpi_id, defn in KPI_DEFINITIONS.items():
            assert defn["direction"] in ("lower_better", "higher_better")
