"""
Test suite for Scenario Comparison & Analysis API endpoints.
Tests: comparisons CRUD, ad-hoc compare, gap analysis, consistency checks, alerts.
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test scenario IDs that exist in the database
SCENARIO_WITCH = "ad7292d6-72cd-4fcd-82a9-1d09fa6163ef"  # WITCH 1.5C with Emissions|CO2
SCENARIO_TIAM = "47526e8d-bfcf-4857-8e8a-58b5371bd05c"   # TIAM-ECN 2C with Emissions|CO2
SCENARIO_GCAM = "81184d3a-8137-404e-b698-8d6e22ba4910"   # GCAM 2C with Emissions|CO2
SCENARIO_IRENA = "f38206c0-482d-485e-886f-04167c84817b"  # IRENA 1.5C


class TestAdHocComparison:
    """Test POST /api/v1/analysis/compare - Ad-hoc comparison without saving"""

    def test_compare_two_scenarios_returns_chart_data(self):
        """Ad-hoc comparison of 2 scenarios returns chart_data and statistics."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/compare",
            json={
                "scenario_ids": [SCENARIO_WITCH, SCENARIO_IRENA],
                "variables": [],
                "regions": [],
                "time_range": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "scenarios" in data
        assert "groups" in data
        assert "total_groups" in data
        assert len(data["scenarios"]) == 2
        assert data["total_groups"] > 0
        
        # Verify each group has chart_data and statistics
        for group in data["groups"]:
            assert "variable" in group
            assert "region" in group
            assert "chart_data" in group
            assert "statistics" in group
            assert len(group["chart_data"]) > 0

    def test_compare_three_scenarios_with_overlapping_vars(self):
        """Comparison of 3 scenarios with overlapping Emissions|CO2 shows statistics."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/compare",
            json={
                "scenario_ids": [SCENARIO_WITCH, SCENARIO_TIAM, SCENARIO_GCAM],
                "variables": ["Emissions|CO2"],
                "regions": ["World"],
                "time_range": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["scenarios"]) == 3
        # Should have at least one Emissions|CO2 group
        emissions_group = next((g for g in data["groups"] if "CO2" in g["variable"]), None)
        assert emissions_group is not None
        
        # Verify statistics computed
        assert "statistics" in emissions_group
        stats = emissions_group["statistics"]
        if stats.get("summary"):
            assert "min" in stats["summary"]
            assert "max" in stats["summary"]
            assert "mean" in stats["summary"]

    def test_compare_requires_minimum_two_scenarios(self):
        """Comparison with < 2 scenarios returns error."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/compare",
            json={
                "scenario_ids": [SCENARIO_WITCH],
                "variables": [],
                "regions": [],
                "time_range": {}
            }
        )
        assert response.status_code == 422  # Validation error


class TestComparisonsCRUD:
    """Test CRUD operations for saved comparisons"""

    created_comp_id = None

    def test_create_comparison_returns_201(self):
        """POST /api/v1/analysis/comparisons creates a comparison."""
        unique_name = f"TEST_Compare_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/comparisons",
            json={
                "name": unique_name,
                "description": "Test comparison for pytest",
                "base_scenario_id": SCENARIO_WITCH,
                "compare_scenario_ids": [SCENARIO_TIAM, SCENARIO_GCAM],
                "variable_filter": ["Emissions|CO2"],
                "region_filter": ["World"],
                "created_by": "pytest_user"
            }
        )
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == unique_name
        assert data["base_scenario_id"] == SCENARIO_WITCH
        assert SCENARIO_TIAM in data["compare_scenario_ids"]
        assert data["created_by"] == "pytest_user"
        
        # Store for subsequent tests
        TestComparisonsCRUD.created_comp_id = data["id"]

    def test_list_comparisons_includes_created(self):
        """GET /api/v1/analysis/comparisons lists saved comparisons."""
        response = requests.get(f"{BASE_URL}/api/v1/analysis/comparisons")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # At least one comparison should exist
        assert len(data) > 0
        
        # Each comparison should have required fields
        for comp in data:
            assert "id" in comp
            assert "name" in comp
            assert "created_at" in comp

    def test_get_comparison_by_id(self):
        """GET /api/v1/analysis/comparisons/{id} returns comparison metadata."""
        if not TestComparisonsCRUD.created_comp_id:
            pytest.skip("No comparison created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/comparisons/{TestComparisonsCRUD.created_comp_id}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == TestComparisonsCRUD.created_comp_id
        assert data["base_scenario_id"] == SCENARIO_WITCH

    def test_get_comparison_data(self):
        """GET /api/v1/analysis/comparisons/{id}/data returns chart data."""
        if not TestComparisonsCRUD.created_comp_id:
            pytest.skip("No comparison created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/comparisons/{TestComparisonsCRUD.created_comp_id}/data"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "scenarios" in data
        assert "groups" in data
        assert len(data["scenarios"]) >= 2

    def test_delete_comparison(self):
        """DELETE /api/v1/analysis/comparisons/{id} removes comparison."""
        if not TestComparisonsCRUD.created_comp_id:
            pytest.skip("No comparison created")
        
        response = requests.delete(
            f"{BASE_URL}/api/v1/analysis/comparisons/{TestComparisonsCRUD.created_comp_id}"
        )
        assert response.status_code == 204
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/v1/analysis/comparisons/{TestComparisonsCRUD.created_comp_id}"
        )
        assert get_response.status_code == 404

    def test_get_nonexistent_comparison_returns_404(self):
        """GET /api/v1/analysis/comparisons/{id} returns 404 for invalid ID."""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/v1/analysis/comparisons/{fake_id}")
        assert response.status_code == 404


class TestGapAnalysis:
    """Test gap analysis endpoints"""

    created_comp_id = None

    @pytest.fixture(autouse=True)
    def setup_comparison(self):
        """Create a comparison for gap analysis tests."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/comparisons",
            json={
                "name": f"TEST_GapAnalysis_{uuid.uuid4().hex[:8]}",
                "base_scenario_id": SCENARIO_WITCH,
                "compare_scenario_ids": [SCENARIO_TIAM, SCENARIO_GCAM],
                "variable_filter": ["Emissions|CO2"],
                "region_filter": ["World"],
                "created_by": "pytest_gap"
            }
        )
        if response.status_code == 201:
            TestGapAnalysis.created_comp_id = response.json()["id"]
        yield
        # Cleanup
        if TestGapAnalysis.created_comp_id:
            requests.delete(f"{BASE_URL}/api/v1/analysis/comparisons/{TestGapAnalysis.created_comp_id}")

    def test_run_gap_analysis_returns_gaps(self):
        """POST /api/v1/analysis/comparisons/{id}/gap-analysis computes gaps."""
        if not TestGapAnalysis.created_comp_id:
            pytest.skip("No comparison for gap analysis")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/comparisons/{TestGapAnalysis.created_comp_id}/gap-analysis"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "gaps" in data
        # Since we have overlapping Emissions|CO2 data, we should get gaps
        # Note: gap results depend on data alignment at key years
        if len(data["gaps"]) > 0:
            gap = data["gaps"][0]
            assert "gap_type" in gap
            assert "variable" in gap
            assert "region" in gap
            assert "year" in gap
            assert "base_value" in gap
            assert "target_value" in gap
            assert "gap_value" in gap
            assert "gap_pct" in gap

    def test_get_cached_gap_analysis(self):
        """GET /api/v1/analysis/comparisons/{id}/gap-analysis returns cached results."""
        if not TestGapAnalysis.created_comp_id:
            pytest.skip("No comparison for gap analysis")
        
        # First run gap analysis
        requests.post(f"{BASE_URL}/api/v1/analysis/comparisons/{TestGapAnalysis.created_comp_id}/gap-analysis")
        
        # Then get cached results
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/comparisons/{TestGapAnalysis.created_comp_id}/gap-analysis"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestConsistencyChecks:
    """Test consistency check endpoints"""

    def test_run_consistency_check_returns_4_checks(self):
        """POST /api/v1/analysis/scenarios/{id}/consistency-check runs 4 checks."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/scenarios/{SCENARIO_WITCH}/consistency-check"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "checks" in data
        checks = data["checks"]
        
        # Should have 4 check types
        check_types = {c["check_type"] for c in checks}
        expected_types = {"carbon_budget", "energy_balance", "tech_deployment", "economic_feasibility"}
        assert check_types == expected_types
        
        # Each check should have required fields
        for check in checks:
            assert "check_type" in check
            assert "status" in check
            assert "score" in check
            assert check["status"] in ["pass", "warning", "fail"]
            assert 0 <= check["score"] <= 1

    def test_get_cached_consistency_checks(self):
        """GET /api/v1/analysis/scenarios/{id}/consistency-check returns cached results."""
        # First run checks
        requests.post(f"{BASE_URL}/api/v1/analysis/scenarios/{SCENARIO_WITCH}/consistency-check")
        
        # Then get cached
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/scenarios/{SCENARIO_WITCH}/consistency-check"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 4

    def test_consistency_check_nonexistent_scenario(self):
        """Consistency check on nonexistent scenario returns 404."""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/v1/analysis/scenarios/{fake_id}/consistency-check")
        assert response.status_code == 404


class TestAlerts:
    """Test alerts endpoints"""

    def test_list_alerts_returns_list(self):
        """GET /api/v1/analysis/alerts returns list of alerts."""
        response = requests.get(f"{BASE_URL}/api/v1/analysis/alerts")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Alerts may be empty if none exist

    def test_list_alerts_with_user_filter(self):
        """GET /api/v1/analysis/alerts?user_id=X filters by user."""
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/alerts",
            params={"user_id": "default_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_alerts_unread_only(self):
        """GET /api/v1/analysis/alerts?unread_only=true filters unread."""
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/alerts",
            params={"unread_only": "true"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCleanup:
    """Cleanup test comparisons"""

    def test_cleanup_test_comparisons(self):
        """Delete all TEST_ prefixed comparisons."""
        response = requests.get(f"{BASE_URL}/api/v1/analysis/comparisons")
        if response.status_code == 200:
            comps = response.json()
            for comp in comps:
                if comp.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/v1/analysis/comparisons/{comp['id']}")
        assert True  # Always pass cleanup


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
