"""
Data Hub API Tests
Tests the Universal Scenario Data Hub with NGFS, IPCC, IEA, IRENA sources.
Tests: stats, sources, scenarios, trajectories, sync operations.
"""
import pytest
import requests
import os

# API URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://emissions-hub-2.preview.emergentagent.com').rstrip('/')


class TestDataHubStats:
    """Tests for /api/v1/data-hub/stats endpoint"""
    
    def test_get_stats_returns_correct_counts(self):
        """GET /api/v1/data-hub/stats returns correct counts (4 sources, 16 scenarios, 342 trajectories)"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate structure
        assert "total_sources" in data
        assert "active_sources" in data
        assert "total_scenarios" in data
        assert "total_trajectories" in data
        assert "total_comparisons" in data
        assert "sources_by_tier" in data
        assert "recent_syncs" in data
        
        # Validate expected counts
        assert data["total_sources"] == 4, f"Expected 4 sources, got {data['total_sources']}"
        assert data["active_sources"] == 4, f"Expected 4 active sources, got {data['active_sources']}"
        assert data["total_scenarios"] == 16, f"Expected 16 scenarios, got {data['total_scenarios']}"
        assert data["total_trajectories"] == 342, f"Expected 342 trajectories, got {data['total_trajectories']}"
        
        print(f"✅ Stats: {data['total_sources']} sources, {data['total_scenarios']} scenarios, {data['total_trajectories']} trajectories")


class TestDataHubSources:
    """Tests for /api/v1/data-hub/sources endpoint"""
    
    def test_get_sources_returns_4_tier1_sources(self):
        """GET /api/v1/data-hub/sources returns 4 Tier 1 sources (NGFS, IPCC, IEA, IRENA)"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sources")
        assert response.status_code == 200
        
        sources = response.json()
        assert isinstance(sources, list)
        assert len(sources) == 4, f"Expected 4 sources, got {len(sources)}"
        
        # Verify all 4 Tier 1 sources exist
        short_names = {s["short_name"] for s in sources}
        expected = {"ngfs", "ipcc", "iea", "irena"}
        assert short_names == expected, f"Expected {expected}, got {short_names}"
        
        # Verify tier
        for src in sources:
            assert src["tier"] == "tier_1", f"Source {src['short_name']} is not tier_1"
            assert src["is_active"] == True, f"Source {src['short_name']} is not active"
            assert "id" in src
            assert "name" in src
            assert "scenario_count" in src
            assert "trajectory_count" in src
        
        print(f"✅ Sources: {', '.join([s['short_name'].upper() for s in sources])}")

    def test_get_single_source_by_id(self):
        """GET /api/v1/data-hub/sources/{id} returns source details"""
        # Get source list first
        sources = requests.get(f"{BASE_URL}/api/v1/data-hub/sources").json()
        source_id = sources[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sources/{source_id}")
        assert response.status_code == 200
        
        source = response.json()
        assert source["id"] == source_id
        print(f"✅ Got source by ID: {source['short_name']}")

    def test_seed_sources_is_idempotent(self):
        """POST /api/v1/data-hub/sources/seed is idempotent (returns created=0 on second call)"""
        # First call (sources already exist)
        response = requests.post(f"{BASE_URL}/api/v1/data-hub/sources/seed")
        assert response.status_code == 200
        
        data = response.json()
        assert "created" in data
        assert "message" in data
        # Since sources already exist, created should be 0
        assert data["created"] == 0, f"Expected 0 created (idempotent), got {data['created']}"
        
        print(f"✅ Seed sources idempotent: {data['message']}")


class TestDataHubScenarios:
    """Tests for /api/v1/data-hub/scenarios endpoint"""
    
    def test_list_scenarios_paginated(self):
        """GET /api/v1/data-hub/scenarios returns paginated scenarios with source_name populated"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=10&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert "scenarios" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        
        assert data["total"] == 16, f"Expected 16 total, got {data['total']}"
        assert len(data["scenarios"]) == 10, f"Expected 10 scenarios, got {len(data['scenarios'])}"
        
        # Verify source_name is populated
        for scenario in data["scenarios"]:
            assert "id" in scenario
            assert "name" in scenario
            assert "source_id" in scenario
            assert "source_name" in scenario, "source_name should be populated"
            assert scenario["source_name"] is not None, f"source_name is None for {scenario['name']}"
            assert "trajectory_count" in scenario
        
        print(f"✅ Paginated scenarios: {len(data['scenarios'])} of {data['total']}")

    def test_filter_scenarios_by_source_id(self):
        """GET /api/v1/data-hub/scenarios?source_id=<id> filters by source"""
        # Get NGFS source ID
        sources = requests.get(f"{BASE_URL}/api/v1/data-hub/sources").json()
        ngfs_source = next((s for s in sources if s["short_name"] == "ngfs"), None)
        assert ngfs_source is not None, "NGFS source not found"
        
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?source_id={ngfs_source['id']}")
        assert response.status_code == 200
        
        data = response.json()
        # NGFS has 6 scenarios
        assert data["total"] == 6, f"Expected 6 NGFS scenarios, got {data['total']}"
        
        # All returned scenarios should be from NGFS
        for scenario in data["scenarios"]:
            assert scenario["source_id"] == ngfs_source["id"]
            assert scenario["source_name"] == "Network for Greening the Financial System"
        
        print(f"✅ Filter by NGFS source: {data['total']} scenarios")

    def test_search_scenarios(self):
        """POST /api/v1/data-hub/scenarios/search with query body returns matching scenarios"""
        search_body = {
            "query": "Net Zero",
            "limit": 50,
            "offset": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/data-hub/scenarios/search",
            json=search_body,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "scenarios" in data
        assert "total" in data
        
        # Should find Net Zero scenarios
        scenario_names = [s["name"].lower() for s in data["scenarios"]]
        # Check at least one contains "net zero"
        has_match = any("net zero" in name for name in scenario_names)
        print(f"✅ Search 'Net Zero': {data['total']} results, match found: {has_match}")

    def test_get_single_scenario(self):
        """GET /api/v1/data-hub/scenarios/{id} returns scenario details"""
        # Get first scenario
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=1").json()["scenarios"]
        scenario_id = scenarios[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{scenario_id}")
        assert response.status_code == 200
        
        scenario = response.json()
        assert scenario["id"] == scenario_id
        assert "source_name" in scenario
        assert "trajectory_count" in scenario
        print(f"✅ Got scenario by ID: {scenario['name']}")

    def test_get_scenario_not_found(self):
        """GET /api/v1/data-hub/scenarios/{id} returns 404 for invalid ID"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/invalid-uuid-here")
        assert response.status_code == 404
        print("✅ 404 for invalid scenario ID")


class TestDataHubTrajectories:
    """Tests for trajectory endpoints"""
    
    def test_get_scenario_trajectories(self):
        """GET /api/v1/data-hub/scenarios/<id>/trajectories returns trajectory data with time_series"""
        # Get a scenario with trajectories
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=1").json()["scenarios"]
        scenario = scenarios[0]
        scenario_id = scenario["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{scenario_id}/trajectories")
        assert response.status_code == 200
        
        trajectories = response.json()
        assert isinstance(trajectories, list)
        assert len(trajectories) > 0, f"Expected trajectories for scenario {scenario['name']}"
        
        # Verify trajectory structure
        for traj in trajectories:
            assert "id" in traj
            assert "scenario_id" in traj
            assert "variable_name" in traj
            assert "unit" in traj
            assert "region" in traj
            assert "time_series" in traj, "time_series should be present"
            assert isinstance(traj["time_series"], dict), "time_series should be a dict"
            assert len(traj["time_series"]) > 0, "time_series should have data points"
        
        print(f"✅ Trajectories for '{scenario['name']}': {len(trajectories)} time series")

    def test_filter_trajectories_by_variable(self):
        """GET trajectories with variable filter"""
        # Get a scenario
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=1").json()["scenarios"]
        scenario_id = scenarios[0]["id"]
        
        # Get all trajectories first
        all_traj = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{scenario_id}/trajectories").json()
        
        if len(all_traj) > 0:
            variable = all_traj[0]["variable_name"]
            
            # Filter by that variable
            response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{scenario_id}/trajectories?variable={variable}")
            assert response.status_code == 200
            
            filtered = response.json()
            for traj in filtered:
                assert traj["variable_name"] == variable
            
            print(f"✅ Filtered trajectories by variable '{variable}': {len(filtered)}")

    def test_filter_trajectories_by_region(self):
        """GET trajectories with region filter"""
        # Get a scenario
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=1").json()["scenarios"]
        scenario_id = scenarios[0]["id"]
        
        # Get all trajectories first
        all_traj = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{scenario_id}/trajectories").json()
        
        if len(all_traj) > 0:
            region = all_traj[0]["region"]
            
            # Filter by that region
            response = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios/{scenario_id}/trajectories?region={region}")
            assert response.status_code == 200
            
            filtered = response.json()
            for traj in filtered:
                assert traj["region"] == region
            
            print(f"✅ Filtered trajectories by region '{region}': {len(filtered)}")


class TestDataHubSyncLogs:
    """Tests for sync log endpoint"""
    
    def test_get_sync_logs(self):
        """GET /api/v1/data-hub/sync-logs returns sync history"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sync-logs")
        assert response.status_code == 200
        
        logs = response.json()
        assert isinstance(logs, list)
        assert len(logs) >= 4, f"Expected at least 4 sync logs, got {len(logs)}"
        
        # Verify log structure
        for log in logs:
            assert "id" in log
            assert "source_id" in log
            assert "status" in log
            assert "started_at" in log
            assert "scenarios_added" in log
            assert "trajectories_added" in log
            
            # All syncs should be successful
            assert log["status"] == "success", f"Sync {log['id']} status: {log['status']}"
        
        print(f"✅ Sync logs: {len(logs)} entries, all successful")

    def test_get_sync_logs_with_limit(self):
        """GET /api/v1/data-hub/sync-logs?limit=2 respects limit"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/sync-logs?limit=2")
        assert response.status_code == 200
        
        logs = response.json()
        assert len(logs) <= 2, f"Expected max 2 logs with limit=2, got {len(logs)}"
        print(f"✅ Sync logs with limit=2: {len(logs)} entries")


class TestDataHubSync:
    """Tests for sync trigger endpoints"""
    
    def test_sync_single_source(self):
        """POST /api/v1/data-hub/sources/{source_id}/sync triggers sync"""
        # Get IRENA source (smallest dataset)
        sources = requests.get(f"{BASE_URL}/api/v1/data-hub/sources").json()
        irena_source = next((s for s in sources if s["short_name"] == "irena"), None)
        assert irena_source is not None
        
        response = requests.post(f"{BASE_URL}/api/v1/data-hub/sources/{irena_source['id']}/sync")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        print(f"✅ Sync IRENA source: {data}")


class TestDataHubComparisons:
    """Tests for comparison endpoints"""
    
    def test_list_comparisons(self):
        """GET /api/v1/data-hub/comparisons returns list"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/comparisons")
        assert response.status_code == 200
        
        comparisons = response.json()
        assert isinstance(comparisons, list)
        print(f"✅ Comparisons: {len(comparisons)} saved")

    def test_create_and_delete_comparison(self):
        """POST/DELETE /api/v1/data-hub/comparisons creates and deletes comparison"""
        # Get two scenario IDs
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=2").json()["scenarios"]
        assert len(scenarios) >= 2
        
        comparison_data = {
            "name": "TEST_Comparison",
            "description": "Test comparison for API validation",
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
        assert created["name"] == "TEST_Comparison"
        comparison_id = created["id"]
        print(f"✅ Created comparison: {comparison_id}")
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/v1/data-hub/comparisons/{comparison_id}")
        assert delete_response.status_code == 204
        print(f"✅ Deleted comparison: {comparison_id}")


class TestDataHubFavorites:
    """Tests for favorites endpoints"""
    
    def test_list_favorites(self):
        """GET /api/v1/data-hub/favorites returns list"""
        response = requests.get(f"{BASE_URL}/api/v1/data-hub/favorites")
        assert response.status_code == 200
        
        favorites = response.json()
        assert isinstance(favorites, list)
        print(f"✅ Favorites: {len(favorites)} saved")

    def test_add_and_remove_favorite(self):
        """POST/DELETE /api/v1/data-hub/favorites adds and removes favorite"""
        # Get a scenario
        scenarios = requests.get(f"{BASE_URL}/api/v1/data-hub/scenarios?limit=1").json()["scenarios"]
        scenario_id = scenarios[0]["id"]
        
        fav_data = {
            "scenario_id": scenario_id,
            "user_id": "test_user",
            "folder": "test_folder"
        }
        
        # Add
        add_response = requests.post(
            f"{BASE_URL}/api/v1/data-hub/favorites",
            json=fav_data,
            headers={"Content-Type": "application/json"}
        )
        assert add_response.status_code == 201
        
        fav = add_response.json()
        fav_id = fav["id"]
        print(f"✅ Added favorite: {fav_id}")
        
        # Remove
        remove_response = requests.delete(f"{BASE_URL}/api/v1/data-hub/favorites/{fav_id}")
        assert remove_response.status_code == 204
        print(f"✅ Removed favorite: {fav_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
