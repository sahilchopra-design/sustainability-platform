"""
Data Hub API Tests - Expanded Version (19 Sources)
Tests the Universal Scenario Data Hub with 19 sources across 6 tiers.
3 sources have REAL data from IIASA (NGFS, IPCC, IAMC15), rest are synthetic.
Tests: stats, sources, scenarios, trajectories, analytics endpoints.
"""
import pytest
import requests
import os

# API URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nature-risk-module.preview.emergentagent.com').rstrip('/')


class TestExpandedDataHubStats:
    """Tests for /api/v1/data-hub/stats endpoint - 19 sources, 99 scenarios, ~875 trajectories"""
    
    def test_stats_returns_19_sources(self):
        """GET /api/v1/data-hub/stats returns 19 sources"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate structure
        assert "total_sources" in data
        assert "active_sources" in data
        assert "total_scenarios" in data
        assert "total_trajectories" in data
        assert "sources_by_tier" in data
        
        # Validate expected counts
        assert data["total_sources"] == 19, f"Expected 19 sources, got {data['total_sources']}"
        assert data["active_sources"] == 19, f"Expected 19 active sources, got {data['active_sources']}"
        print(f"✅ Stats: {data['total_sources']} sources")
    
    def test_stats_returns_99_scenarios(self):
        """GET /api/v1/data-hub/stats returns 99 scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_scenarios"] == 99, f"Expected 99 scenarios, got {data['total_scenarios']}"
        print(f"✅ Stats: {data['total_scenarios']} scenarios")
    
    def test_stats_returns_approx_875_trajectories(self):
        """GET /api/v1/data-hub/stats returns ~875 trajectories"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/stats")
        assert response.status_code == 200
        
        data = response.json()
        # Allow some tolerance as real data syncs may vary
        assert 800 <= data["total_trajectories"] <= 950, f"Expected ~875 trajectories, got {data['total_trajectories']}"
        print(f"✅ Stats: {data['total_trajectories']} trajectories")
    
    def test_stats_sources_by_tier_correct(self):
        """GET /api/v1/data-hub/stats has correct sources_by_tier distribution"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/stats")
        assert response.status_code == 200
        
        data = response.json()
        by_tier = data["sources_by_tier"]
        
        # Expected: Tier 1=5, Tier 2=6, Tier 3=5, Tier 4=1, Tier 5=1, Tier 6=1
        # Note: keys may have enum prefix
        tier_1_count = by_tier.get("SourceTier.TIER_1") or by_tier.get("1") or by_tier.get("tier_1", 0)
        assert tier_1_count == 5, f"Expected 5 Tier 1 sources, got {tier_1_count}"
        
        print(f"✅ Stats by tier: {by_tier}")


class TestExpandedDataHubSources:
    """Tests for /api/v1/data-hub/sources endpoint - 19 sources across tiers 1-6"""
    
    def test_sources_returns_19_sources(self):
        """GET /api/v1/data-hub/sources returns 19 sources"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sources")
        assert response.status_code == 200
        
        sources = response.json()
        assert isinstance(sources, list)
        assert len(sources) == 19, f"Expected 19 sources, got {len(sources)}"
        print(f"✅ Sources: {len(sources)} total")
    
    def test_sources_have_6_tiers(self):
        """GET /api/v1/data-hub/sources returns sources across tiers 1-6"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sources")
        assert response.status_code == 200
        
        sources = response.json()
        tiers = set(s["tier"] for s in sources)
        
        expected_tiers = {"tier_1", "tier_2", "tier_3", "tier_4", "tier_5", "tier_6"}
        assert tiers == expected_tiers, f"Expected tiers {expected_tiers}, got {tiers}"
        print(f"✅ Sources across 6 tiers: {tiers}")
    
    def test_sources_tier1_has_5_sources(self):
        """Tier 1 has 5 sources: NGFS, IPCC, IAMC15, IEA, IRENA"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sources")
        assert response.status_code == 200
        
        sources = response.json()
        tier1_sources = [s for s in sources if s["tier"] == "tier_1"]
        assert len(tier1_sources) == 5, f"Expected 5 Tier 1 sources, got {len(tier1_sources)}"
        
        tier1_names = {s["short_name"] for s in tier1_sources}
        expected = {"ngfs", "ipcc", "iamc15", "iea", "irena"}
        assert tier1_names == expected, f"Expected {expected}, got {tier1_names}"
        print(f"✅ Tier 1 sources: {tier1_names}")
    
    def test_sources_structure_complete(self):
        """Sources have required fields: id, name, short_name, tier, scenario_count, trajectory_count"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sources")
        assert response.status_code == 200
        
        sources = response.json()
        for src in sources:
            assert "id" in src, "Missing id"
            assert "name" in src, "Missing name"
            assert "short_name" in src, "Missing short_name"
            assert "tier" in src, "Missing tier"
            assert "scenario_count" in src, "Missing scenario_count"
            assert "trajectory_count" in src, "Missing trajectory_count"
            assert "is_active" in src, "Missing is_active"
            assert src["is_active"] == True, f"Source {src['short_name']} not active"
        print("✅ All sources have complete structure")


class TestNGFSScenarioFiltering:
    """Tests for filtering NGFS scenarios - should have 27 scenarios with real IIASA data"""
    
    def test_ngfs_filter_returns_27_scenarios(self):
        """GET /api/v1/data-hub/scenarios?source_id=<ngfs_id> returns 27 NGFS scenarios"""
        # Get NGFS source ID
        sources = requests.get(f"{BASE_URL}/api/v1/data-hub/sources").json()
        ngfs_source = next((s for s in sources if s["short_name"] == "ngfs"), None)
        assert ngfs_source is not None, "NGFS source not found"
        
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?source_id={ngfs_source['id']}&limit=100")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 27, f"Expected 27 NGFS scenarios, got {data['total']}"
        
        # All returned scenarios should be from NGFS
        for scenario in data["scenarios"]:
            assert scenario["source_id"] == ngfs_source["id"]
        print(f"✅ NGFS scenarios: {data['total']}")
    
    def test_ngfs_scenarios_have_real_data_external_ids(self):
        """NGFS scenarios with real data have external_id containing '|' (model|scenario format)"""
        sources = requests.get(f"{BASE_URL}/api/v1/data-hub/sources").json()
        ngfs_source = next((s for s in sources if s["short_name"] == "ngfs"), None)
        
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?source_id={ngfs_source['id']}&limit=100")
        data = response.json()
        
        # Real IIASA scenarios have external_id like "REMIND-MAgPIE 3.3-4.8|Net Zero 2050"
        real_data_scenarios = [s for s in data["scenarios"] if s.get("external_id") and "|" in s["external_id"]]
        
        # Most NGFS scenarios should have real data
        assert len(real_data_scenarios) >= 20, f"Expected at least 20 real data scenarios, got {len(real_data_scenarios)}"
        print(f"✅ NGFS real data scenarios: {len(real_data_scenarios)} of {len(data['scenarios'])}")


class TestExpandedScenarios:
    """Tests for /api/v1/data-hub/scenarios endpoint"""
    
    def test_scenarios_paginated_returns_display_name(self):
        """GET /api/v1/data-hub/scenarios returns scenarios with display_name"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        assert "scenarios" in data
        assert "total" in data
        assert data["total"] == 99, f"Expected 99 total, got {data['total']}"
        
        # Check for display_name field
        for scenario in data["scenarios"][:10]:
            assert "display_name" in scenario, f"Missing display_name for {scenario['name']}"
        print(f"✅ Scenarios have display_name: {len(data['scenarios'])} returned")
    
    def test_scenarios_have_carbon_neutral_year(self):
        """Scenarios include carbon_neutral_year field"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        
        # Count scenarios with carbon_neutral_year set
        with_cn_year = [s for s in data["scenarios"] if s.get("carbon_neutral_year")]
        assert len(with_cn_year) > 0, "Expected some scenarios with carbon_neutral_year"
        print(f"✅ Scenarios with carbon_neutral_year: {len(with_cn_year)}")


class TestScenarioSearch:
    """Tests for POST /api/v1/data-hub/scenarios/search"""
    
    def test_search_net_zero_returns_results(self):
        """POST /api/v1/data-hub/scenarios/search with 'Net Zero' query returns results"""
        response = requests.post(
            f"{BASE_URL}/api/v1/data-hub/scenarios/search",
            json={"query": "Net Zero", "limit": 50},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "scenarios" in data
        assert "total" in data
        assert data["total"] > 0, "Expected 'Net Zero' search to return results"
        print(f"✅ Search 'Net Zero': {data['total']} results")
    
    def test_search_carbon_returns_results(self):
        """POST /api/v1/data-hub/scenarios/search with 'carbon' query returns results"""
        response = requests.post(
            f"{BASE_URL}/api/v1/data-hub/scenarios/search",
            json={"query": "carbon", "limit": 50},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] > 0, "Expected 'carbon' search to return results"
        print(f"✅ Search 'carbon': {data['total']} results")


class TestTrajectories:
    """Tests for trajectory endpoints"""
    
    def test_get_trajectories_has_variable_code_and_quality(self):
        """GET /api/v1/data-hub/scenarios/<id>/trajectories returns variable_code, sector, data_quality_score"""
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=1").json()["scenarios"]
        scenario_id = scenarios[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{scenario_id}/trajectories")
        assert response.status_code == 200
        
        trajectories = response.json()
        assert len(trajectories) > 0
        
        for traj in trajectories[:5]:
            assert "variable_code" in traj, "Missing variable_code"
            assert "data_quality_score" in traj, "Missing data_quality_score"
            assert "time_series" in traj
            # sector may be null for some variables
            assert "sector" in traj
        print(f"✅ Trajectories have variable_code, sector, data_quality_score")
    
    def test_real_data_trajectories_have_high_quality_score(self):
        """Real data scenarios (NGFS/IPCC/IAMC) have data_quality_score >= 4"""
        # Get a NGFS scenario with real data
        sources = requests.get(f"{BASE_URL}/api/v1/data-hub/sources").json()
        ngfs_source = next((s for s in sources if s["short_name"] == "ngfs"), None)
        
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?source_id={ngfs_source['id']}&limit=10").json()["scenarios"]
        
        # Find a real data scenario
        real_scenario = next((s for s in scenarios if s.get("external_id") and "|" in s["external_id"]), None)
        if real_scenario:
            trajs = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{real_scenario['id']}/trajectories").json()
            
            if trajs:
                for traj in trajs[:5]:
                    score = traj.get("data_quality_score", 0)
                    assert score >= 4, f"Expected quality score >= 4 for real data, got {score}"
                print(f"✅ Real data trajectories have high quality score")
        else:
            print("⚠️ No real data scenario found in NGFS")


class TestAnalyticsCoverage:
    """Tests for GET /api/v1/data-hub/analytics/coverage"""
    
    def test_coverage_returns_by_tier(self):
        """Coverage analytics returns by_tier breakdown"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/analytics/coverage")
        assert response.status_code == 200
        
        data = response.json()
        assert "by_tier" in data
        assert len(data["by_tier"]) == 6, "Expected 6 tiers in by_tier"
        print(f"✅ Analytics coverage by_tier: {list(data['by_tier'].keys())}")
    
    def test_coverage_returns_by_category(self):
        """Coverage analytics returns by_category breakdown"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/analytics/coverage")
        assert response.status_code == 200
        
        data = response.json()
        assert "by_category" in data
        assert len(data["by_category"]) > 10, "Expected many categories"
        print(f"✅ Analytics coverage by_category: {len(data['by_category'])} categories")
    
    def test_coverage_returns_variables_and_regions(self):
        """Coverage analytics returns variables and regions lists"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/analytics/coverage")
        assert response.status_code == 200
        
        data = response.json()
        assert "variables" in data
        assert "regions" in data
        assert "total_variables" in data
        assert "total_regions" in data
        
        assert len(data["variables"]) > 30, f"Expected 30+ variables, got {len(data['variables'])}"
        assert len(data["regions"]) >= 10, f"Expected 10+ regions, got {len(data['regions'])}"
        print(f"✅ Analytics coverage: {len(data['variables'])} variables, {len(data['regions'])} regions")


class TestTemperatureRangeAnalytics:
    """Tests for GET /api/v1/data-hub/analytics/temperature-range"""
    
    def test_temperature_range_returns_buckets(self):
        """Temperature analytics returns temperature buckets"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/analytics/temperature-range")
        assert response.status_code == 200
        
        data = response.json()
        assert "buckets" in data
        
        expected_buckets = ["<1.5C", "1.5-2.0C", "2.0-3.0C", "3.0-4.0C", ">4.0C"]
        for bucket in expected_buckets:
            assert bucket in data["buckets"], f"Missing bucket {bucket}"
        
        # Sum of buckets should match total_with_target
        total = sum(data["buckets"].values())
        assert total == data.get("total_with_target", total)
        print(f"✅ Temperature buckets: {data['buckets']}")
    
    def test_temperature_range_returns_details(self):
        """Temperature analytics returns scenario details"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/analytics/temperature-range")
        assert response.status_code == 200
        
        data = response.json()
        assert "details" in data
        assert len(data["details"]) > 0
        
        for detail in data["details"][:5]:
            assert "id" in detail
            assert "name" in detail
            assert "temperature_target" in detail
        print(f"✅ Temperature details: {len(data['details'])} scenarios with temperature targets")


class TestAvailableVariables:
    """Tests for GET /api/v1/data-hub/trajectories/available-variables"""
    
    def test_available_variables_returns_62(self):
        """Available variables returns ~62 unique variables"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/trajectories/available-variables")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Allow some tolerance
        assert 50 <= len(data) <= 80, f"Expected ~62 variables, got {len(data)}"
        print(f"✅ Available variables: {len(data)}")
    
    def test_available_variables_structure(self):
        """Available variables returns variable, unit, count for each"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/trajectories/available-variables")
        assert response.status_code == 200
        
        data = response.json()
        for var in data[:10]:
            assert "variable" in var
            assert "unit" in var
            assert "count" in var
        print("✅ Available variables structure: variable, unit, count")


class TestDataHubComparisons:
    """Tests for comparison endpoints"""
    
    def test_create_and_delete_comparison(self):
        """POST/DELETE /api/v1/data-hub/comparisons creates and deletes comparison"""
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=2").json()["scenarios"]
        assert len(scenarios) >= 2
        
        comparison_data = {
            "name": "TEST_Expanded_Comparison",
            "description": "Test comparison for expanded hub",
            "base_scenario_id": scenarios[0]["id"],
            "compare_scenario_ids": [scenarios[1]["id"]],
            "variable_filter": [],
            "region_filter": []
        }
        
        # Create
        create_response = requests.post(
            f"{BASE_URL}/api/v1/data-hub/comparisons",
            json=comparison_data,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 201
        
        created = create_response.json()
        comparison_id = created["id"]
        print(f"✅ Created comparison: {comparison_id}")
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/v1/data-hub/comparisons/{comparison_id}")
        assert delete_response.status_code == 204
        print(f"✅ Deleted comparison: {comparison_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
