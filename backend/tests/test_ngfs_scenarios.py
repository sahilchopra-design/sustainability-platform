"""
NGFS Scenarios API Tests - All 24 scenarios across 3 phases.
Tests for: listing, filtering, phase summary, temperature ranges, detail view,
parameters, time-series, search, and comparison.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestNGFSScenariosListing:
    """Tests for GET /api/v1/ngfs-scenarios listing endpoint"""
    
    def test_list_all_scenarios_returns_24(self):
        """List all scenarios should return 24 total"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert data["meta"]["total_scenarios"] == 24
        assert len(data["data"]) == 24
    
    def test_list_scenarios_has_meta_with_temperature_range(self):
        """Meta should include temperature_range with min/max"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        data = response.json()
        assert "temperature_range" in data["meta"]
        assert data["meta"]["temperature_range"]["min"] is not None
        assert data["meta"]["temperature_range"]["max"] is not None
    
    def test_list_scenarios_has_phase_count(self):
        """Meta should include phase_count dictionary"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        data = response.json()
        assert "phase_count" in data["meta"]
        assert data["meta"]["phase_count"]["1"] == 6
        assert data["meta"]["phase_count"]["2"] == 10
        assert data["meta"]["phase_count"]["3"] == 8


class TestNGFSPhaseFiltering:
    """Tests for filtering scenarios by phase"""
    
    def test_filter_phase_1_returns_6_scenarios(self):
        """Phase 1 (2020) should have 6 scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios?phase=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 6
        for sc in data["data"]:
            assert sc["phase"] == 1
            assert sc["phase_year"] == 2020
    
    def test_filter_phase_2_returns_10_scenarios(self):
        """Phase 2 (2021) should have 10 scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios?phase=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        for sc in data["data"]:
            assert sc["phase"] == 2
    
    def test_filter_phase_3_returns_8_scenarios(self):
        """Phase 3 (2023) should have 8 scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios?phase=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 8
        for sc in data["data"]:
            assert sc["phase"] == 3


class TestNGFSPhaseSummary:
    """Tests for GET /api/v1/ngfs-scenarios/phases endpoint"""
    
    def test_phases_endpoint_returns_3_phases(self):
        """Phases endpoint should return data for phases 1, 2, 3"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/phases")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "1" in data["data"]
        assert "2" in data["data"]
        assert "3" in data["data"]
    
    def test_phases_have_correct_year_mapping(self):
        """Each phase should have correct year mapping"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/phases")
        data = response.json()["data"]
        assert data["1"]["year"] == 2020
        assert data["2"]["year"] == 2021
        assert data["3"]["year"] == 2023
    
    def test_phases_have_correct_counts(self):
        """Each phase should have correct scenario count"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/phases")
        data = response.json()["data"]
        assert data["1"]["count"] == 6
        assert data["2"]["count"] == 10
        assert data["3"]["count"] == 8
    
    def test_phases_include_scenario_list(self):
        """Each phase should include list of scenarios with id, name, slug"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/phases")
        data = response.json()["data"]
        for phase in ["1", "2", "3"]:
            assert "scenarios" in data[phase]
            for sc in data[phase]["scenarios"]:
                assert "id" in sc
                assert "name" in sc
                assert "slug" in sc


class TestNGFSTemperatureRanges:
    """Tests for GET /api/v1/ngfs-scenarios/temperature-ranges endpoint"""
    
    def test_temperature_ranges_returns_5_buckets(self):
        """Should return 5 temperature buckets"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/temperature-ranges")
        assert response.status_code == 200
        data = response.json()["data"]
        expected_buckets = ["below_1.5C", "1.5-2.0C", "2.0-2.5C", "2.5-3.0C", "above_3.0C"]
        for bucket in expected_buckets:
            assert bucket in data
    
    def test_temperature_buckets_have_scenarios(self):
        """Each bucket should have list of scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/temperature-ranges")
        data = response.json()["data"]
        total = sum(len(data[bucket]) for bucket in data)
        assert total == 24  # All 24 scenarios should be bucketed


class TestNGFSFilterEndpoint:
    """Tests for GET /api/v1/ngfs-scenarios/filter endpoint"""
    
    def test_filter_by_temperature_range(self):
        """Filter scenarios by min_temp and max_temp"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/filter?min_temp=2.0&max_temp=3.0")
        assert response.status_code == 200
        data = response.json()
        for sc in data["data"]:
            assert sc["temperature_by_2100"] >= 2.0
            assert sc["temperature_by_2100"] <= 3.0
    
    def test_filter_by_phases(self):
        """Filter scenarios by phases parameter (comma-separated)"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/filter?phases=1,3")
        assert response.status_code == 200
        data = response.json()
        for sc in data["data"]:
            assert sc["phase"] in [1, 3]
    
    def test_filter_has_net_zero_target(self):
        """Filter scenarios with net zero target"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/filter?has_net_zero_target=true")
        assert response.status_code == 200
        data = response.json()
        for sc in data["data"]:
            assert sc["carbon_neutral_year"] is not None


class TestNGFSScenarioDetail:
    """Tests for GET /api/v1/ngfs-scenarios/{id} endpoint"""
    
    def test_get_scenario_by_id(self):
        """Get scenario details by ID"""
        # First get a valid ID
        list_resp = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        sc_id = list_resp.json()["data"][0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/{sc_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == sc_id
        assert "name" in data
        assert "key_assumptions" in data
        assert "parameters" in data
    
    def test_get_scenario_by_slug(self):
        """Get scenario details by slug"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/net-zero-2050")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["slug"] == "net-zero-2050"
        assert data["name"] == "Net Zero 2050"
    
    def test_get_scenario_includes_4_parameters(self):
        """Scenario detail should include 4 parameters"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/net-zero-2050")
        data = response.json()["data"]
        assert len(data["parameters"]) == 4
        param_names = [p["parameter_name"] for p in data["parameters"]]
        assert set(param_names) == {"carbon_price", "emissions", "temperature", "gdp_impact"}
    
    def test_get_scenario_not_found(self):
        """Return 404 for non-existent scenario"""
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/non-existent-id")
        assert response.status_code == 404


class TestNGFSParameters:
    """Tests for GET /api/v1/ngfs-scenarios/{id}/parameters endpoint"""
    
    def test_get_parameters_with_time_series(self):
        """Parameters endpoint should include time series data"""
        list_resp = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        sc_id = list_resp.json()["data"][0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/{sc_id}/parameters")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 4
        
        for param in data:
            assert "time_series" in param
            assert len(param["time_series"]) == 76  # 2025-2100 = 76 years
            assert all("year" in ts for ts in param["time_series"])
            assert all("value" in ts for ts in param["time_series"])


class TestNGFSTimeSeries:
    """Tests for GET /api/v1/ngfs-scenarios/{id}/time-series endpoint"""
    
    def test_get_time_series_all_params(self):
        """Time series endpoint returns all 4 parameters"""
        list_resp = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        sc_id = list_resp.json()["data"][0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/{sc_id}/time-series")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 4
        assert set(data.keys()) == {"carbon_price", "emissions", "temperature", "gdp_impact"}
    
    def test_time_series_has_76_years(self):
        """Each parameter should have 76 years of data (2025-2100)"""
        list_resp = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        sc_id = list_resp.json()["data"][0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios/{sc_id}/time-series")
        data = response.json()["data"]
        for param_name, series in data.items():
            assert len(series) == 76, f"{param_name} should have 76 years"


class TestNGFSSearch:
    """Tests for POST /api/v1/ngfs-scenarios/search endpoint"""
    
    def test_search_by_name(self):
        """Search scenarios by name"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ngfs-scenarios/search",
            json={"query": "net zero"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] >= 2
        for sc in data["data"]:
            assert "net zero" in sc["name"].lower() or "net zero" in (sc["description"] or "").lower()
    
    def test_search_by_category(self):
        """Search scenarios by category"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ngfs-scenarios/search",
            json={"query": "orderly"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] >= 1
    
    def test_search_empty_query_returns_empty(self):
        """Empty query returns empty results"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ngfs-scenarios/search",
            json={"query": ""},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        assert len(response.json()["data"]) == 0


class TestNGFSCompare:
    """Tests for POST /api/v1/ngfs-scenarios/compare endpoint"""
    
    def test_compare_3_scenarios(self):
        """Compare 3 scenarios returns comparison data"""
        list_resp = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        ids = [sc["id"] for sc in list_resp.json()["data"][:3]]
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ngfs-scenarios/compare",
            json={"scenario_ids": ids},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "scenarios" in data
        assert len(data["scenarios"]) == 3
        assert "metrics" in data
        assert len(data["metrics"]) == 4
    
    def test_compare_has_all_4_metrics(self):
        """Comparison includes all 4 metrics"""
        list_resp = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        ids = [sc["id"] for sc in list_resp.json()["data"][:2]]
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ngfs-scenarios/compare",
            json={"scenario_ids": ids},
            headers={"Content-Type": "application/json"}
        )
        data = response.json()["data"]
        assert set(data["metrics"].keys()) == {"carbon_price", "emissions", "temperature", "gdp_impact"}
    
    def test_compare_metrics_have_series_data(self):
        """Each metric should have series data for each scenario"""
        list_resp = requests.get(f"{BASE_URL}/api/v1/ngfs-scenarios")
        ids = [sc["id"] for sc in list_resp.json()["data"][:2]]
        names = [sc["name"] for sc in list_resp.json()["data"][:2]]
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ngfs-scenarios/compare",
            json={"scenario_ids": ids},
            headers={"Content-Type": "application/json"}
        )
        data = response.json()["data"]
        for metric_name, metric_data in data["metrics"].items():
            assert "series" in metric_data
            for name in names:
                assert name in metric_data["series"]


class TestNGFSSeed:
    """Tests for POST /api/v1/ngfs-scenarios/seed endpoint"""
    
    def test_seed_is_idempotent(self):
        """Seed endpoint should be idempotent"""
        response = requests.post(f"{BASE_URL}/api/v1/ngfs-scenarios/seed")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Already seeded"
        assert data["count"] == 24
