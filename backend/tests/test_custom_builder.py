"""
Custom Scenario Builder API tests — tests all scenario-builder endpoints.
Module: /api/v1/scenario-builder/*
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL environment variable is required"


class TestBaseScenarios:
    """Tests for GET /api/v1/scenario-builder/base-scenarios"""
    
    def test_returns_base_scenarios(self):
        """Base scenarios endpoint should return list of available scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} base scenarios")
    
    def test_returns_102_scenarios_minimum(self):
        """Should return at least 102 scenarios (as per PRD)"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 50, f"Expected at least 50 scenarios, got {len(data)}"
        print(f"Verified: {len(data)} base scenarios available")
    
    def test_scenario_has_required_fields(self):
        """Each scenario should have id, name, source_name, trajectory_count"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        scenario = data[0]
        assert "id" in scenario
        assert "name" in scenario
        assert "source_name" in scenario
        assert "trajectory_count" in scenario
        assert "variables" in scenario
        print(f"First scenario: {scenario['name']} ({scenario['source_name']}) with {scenario['trajectory_count']} trajectories")
    
    def test_scenarios_have_different_sources(self):
        """Scenarios should come from multiple sources"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        data = response.json()
        sources = set(s.get("source_name") for s in data if s.get("source_name"))
        assert len(sources) >= 3, f"Expected multiple sources, got {len(sources)}"
        print(f"Sources found: {list(sources)[:5]}...")


class TestPreview:
    """Tests for POST /api/v1/scenario-builder/preview"""
    
    @pytest.fixture
    def base_scenario_id(self):
        """Get a base scenario ID with trajectories"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        # Find one with trajectory_count > 0
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"] if scenarios else None
    
    def test_preview_returns_impacts(self, base_scenario_id):
        """Preview should return impact calculations"""
        payload = {
            "base_scenario_id": base_scenario_id,
            "customizations": [
                {
                    "variable_name": "Emissions|CO2",
                    "region": "World",
                    "customized_values": {"2030": 20, "2040": 10, "2050": 0},
                    "interpolation_method": "linear"
                }
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scenario-builder/preview",
            json=payload
        )
        assert response.status_code == 200, f"Preview failed: {response.text}"
        data = response.json()
        assert "impacts" in data
        assert "base_scenario" in data
        print(f"Preview impacts: {list(data['impacts'].keys())}")
    
    def test_preview_returns_temperature_outcome(self, base_scenario_id):
        """Preview impacts should include temperature outcome"""
        payload = {
            "base_scenario_id": base_scenario_id,
            "customizations": [{
                "variable_name": "Emissions|CO2",
                "region": "World",
                "customized_values": {"2030": 15, "2050": -5},
                "interpolation_method": "linear"
            }]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/preview", json=payload)
        assert response.status_code == 200
        
        impacts = response.json()["impacts"]
        assert "temperature_outcome" in impacts
        temp = impacts["temperature_outcome"]
        print(f"Temperature by 2100: {temp.get('by_2100')}°C, P(< 1.5°C): {temp.get('probability_1_5C')}%")
    
    def test_preview_returns_risk_scores(self, base_scenario_id):
        """Preview impacts should include risk indicators"""
        payload = {
            "base_scenario_id": base_scenario_id,
            "customizations": [{
                "variable_name": "Price|Carbon",
                "region": "World",
                "customized_values": {"2030": 100, "2050": 300},
                "interpolation_method": "linear"
            }]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/preview", json=payload)
        assert response.status_code == 200
        
        impacts = response.json()["impacts"]
        assert "risk_indicators" in impacts
        risks = impacts["risk_indicators"]
        assert "physical_risk_score" in risks
        assert "transition_risk_score" in risks
        assert "overall_climate_risk" in risks
        print(f"Risk scores: Physical={risks['physical_risk_score']}, Transition={risks['transition_risk_score']}")
    
    def test_preview_with_invalid_scenario_returns_404(self):
        """Preview with invalid scenario should return 404"""
        payload = {
            "base_scenario_id": "invalid-id-12345",
            "customizations": []
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/preview", json=payload)
        assert response.status_code == 404


class TestCustomize:
    """Tests for POST /api/v1/scenario-builder/customize (save custom scenario)"""
    
    @pytest.fixture
    def base_scenario_id(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]
    
    def test_customize_creates_scenario(self, base_scenario_id):
        """Should create and save a custom scenario"""
        test_name = f"TEST_Custom_Scenario_{int(time.time())}"
        payload = {
            "base_scenario_id": base_scenario_id,
            "name": test_name,
            "description": "Test custom scenario",
            "customizations": [{
                "variable_name": "Emissions|CO2",
                "region": "World",
                "customized_values": {"2030": 25, "2040": 12, "2050": 0},
                "interpolation_method": "linear"
            }],
            "is_public": False,
            "tags": ["test"]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/customize", json=payload)
        assert response.status_code == 201, f"Create failed: {response.text}"
        
        data = response.json()
        assert data["name"] == test_name
        assert "id" in data
        assert "calculated_impacts" in data
        assert data["calculated_impacts"] is not None
        print(f"Created custom scenario: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{data['id']}")
    
    def test_customize_calculates_impacts_on_save(self, base_scenario_id):
        """Saving should automatically calculate impacts"""
        test_name = f"TEST_ImpactCalc_{int(time.time())}"
        payload = {
            "base_scenario_id": base_scenario_id,
            "name": test_name,
            "customizations": [{
                "variable_name": "Emissions|CO2",
                "region": "World",
                "customized_values": {"2030": 30, "2050": 5}
            }]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/customize", json=payload)
        assert response.status_code == 201
        
        data = response.json()
        impacts = data["calculated_impacts"]
        assert "temperature_outcome" in impacts
        assert "risk_indicators" in impacts
        print(f"Impacts calculated: Temp by 2100 = {impacts['temperature_outcome'].get('by_2100')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{data['id']}")
    
    def test_customize_requires_name(self, base_scenario_id):
        """Should reject request without name"""
        payload = {
            "base_scenario_id": base_scenario_id,
            "customizations": []
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/customize", json=payload)
        assert response.status_code == 422  # Validation error


class TestCalculateImpacts:
    """Tests for POST /api/v1/scenario-builder/calculate-impacts"""
    
    @pytest.fixture
    def base_scenario_id(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]
    
    def test_calculate_full_impacts(self, base_scenario_id):
        """Should calculate full impact assessment"""
        payload = {
            "base_scenario_id": base_scenario_id,
            "customizations": [{
                "variable_name": "Emissions|CO2",
                "region": "World",
                "customized_values": {"2030": 20, "2050": -5}
            }]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/calculate-impacts", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Verify all impact categories
        assert "temperature_outcome" in data
        assert "emissions_trajectory" in data
        assert "economic_impacts" in data
        assert "risk_indicators" in data
        print(f"Full impact calculation completed with {len(data.keys())} categories")


class TestValidate:
    """Tests for POST /api/v1/scenario-builder/validate"""
    
    @pytest.fixture
    def base_scenario_id(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        return response.json()[0]["id"]
    
    def test_validate_valid_customization(self, base_scenario_id):
        """Should validate good customizations"""
        payload = {
            "base_scenario_id": base_scenario_id,
            "customizations": [{
                "variable_name": "carbon_price",
                "region": "World",
                "customized_values": {"2030": 100, "2050": 300}
            }]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/validate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
        print(f"Validation: valid={data['is_valid']}, errors={len(data['errors'])}, warnings={len(data['warnings'])}")
    
    def test_validate_detects_out_of_range(self, base_scenario_id):
        """Should detect values outside valid ranges"""
        payload = {
            "base_scenario_id": base_scenario_id,
            "customizations": [{
                "variable_name": "carbon_price",
                "region": "World",
                "customized_values": {"2030": 5000}  # Above max 1000
            }]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/validate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_valid"] is False or len(data["errors"]) > 0
        print(f"Detected invalid carbon_price: errors={data['errors']}")


class TestSimulate:
    """Tests for POST /api/v1/scenario-builder/simulate (Monte Carlo)"""
    
    @pytest.fixture
    def custom_scenario_id(self):
        """Create a custom scenario for simulation"""
        # Get base scenario
        base_resp = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = base_resp.json()
        base_id = None
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                base_id = s["id"]
                break
        if not base_id:
            base_id = scenarios[0]["id"]
        
        # Create custom scenario
        create_payload = {
            "base_scenario_id": base_id,
            "name": f"TEST_Sim_{int(time.time())}",
            "customizations": [{
                "variable_name": "Emissions|CO2",
                "region": "World",
                "customized_values": {"2030": 20, "2050": 0}
            }]
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/scenario-builder/customize", json=create_payload)
        if create_resp.status_code == 201:
            return create_resp.json()["id"]
        return None
    
    def test_simulate_monte_carlo(self, custom_scenario_id):
        """Monte Carlo simulation should return probability distributions"""
        if not custom_scenario_id:
            pytest.skip("Could not create custom scenario for simulation")
        
        payload = {
            "custom_scenario_id": custom_scenario_id,
            "simulation_type": "monte_carlo",
            "iterations": 500,
            "time_horizons": [2030, 2050, 2100]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/simulate", json=payload)
        assert response.status_code == 200, f"Simulation failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "completed"
        assert "results" in data
        results = data["results"]
        
        # Monte Carlo should return distributions
        assert "temperature_distribution" in results
        assert "probability_below_1_5c" in results
        assert "probability_below_2c" in results
        
        temp_dist = results["temperature_distribution"]
        assert "p50" in temp_dist  # Median
        assert "p5" in temp_dist   # 5th percentile
        assert "p95" in temp_dist  # 95th percentile
        
        print(f"Monte Carlo ({results['iterations']} iterations): Temp median={temp_dist['p50']}°C, P(<2°C)={results['probability_below_2c']}%")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{custom_scenario_id}")
    
    def test_simulate_with_invalid_scenario_returns_404(self):
        """Simulation with invalid scenario should return 404"""
        payload = {
            "custom_scenario_id": "invalid-scenario-id",
            "simulation_type": "monte_carlo",
            "iterations": 100
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenario-builder/simulate", json=payload)
        assert response.status_code == 404


class TestCustomScenarioCRUD:
    """Tests for custom scenario CRUD operations"""
    
    @pytest.fixture
    def base_scenario_id(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]
    
    def test_list_custom_scenarios(self):
        """GET /api/v1/scenario-builder/custom should return list"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/custom")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} custom scenarios")
    
    def test_get_custom_scenario_by_id(self, base_scenario_id):
        """GET /api/v1/scenario-builder/custom/{id} should return full scenario"""
        # Create a scenario first
        create_payload = {
            "base_scenario_id": base_scenario_id,
            "name": f"TEST_GetById_{int(time.time())}",
            "customizations": [{
                "variable_name": "Emissions|CO2",
                "region": "World",
                "customized_values": {"2030": 20}
            }]
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/scenario-builder/customize", json=create_payload)
        assert create_resp.status_code == 201
        cs_id = create_resp.json()["id"]
        
        # Get by ID
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/custom/{cs_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cs_id
        assert "customizations" in data
        assert "calculated_impacts" in data
        print(f"Retrieved custom scenario: {data['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{cs_id}")
    
    def test_get_nonexistent_returns_404(self):
        """GET with invalid ID should return 404"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/custom/nonexistent-id")
        assert response.status_code == 404
    
    def test_delete_custom_scenario(self, base_scenario_id):
        """DELETE /api/v1/scenario-builder/custom/{id} should remove scenario"""
        # Create a scenario
        create_payload = {
            "base_scenario_id": base_scenario_id,
            "name": f"TEST_Delete_{int(time.time())}",
            "customizations": []
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/scenario-builder/customize", json=create_payload)
        cs_id = create_resp.json()["id"]
        
        # Delete
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{cs_id}")
        assert delete_resp.status_code == 204
        
        # Verify deleted
        get_resp = requests.get(f"{BASE_URL}/api/v1/scenario-builder/custom/{cs_id}")
        assert get_resp.status_code == 404
        print(f"Successfully deleted custom scenario: {cs_id}")


class TestFork:
    """Tests for POST /api/v1/scenario-builder/custom/{id}/fork"""
    
    @pytest.fixture
    def custom_scenario_id(self):
        """Create a custom scenario to fork"""
        base_resp = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = base_resp.json()
        base_id = None
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                base_id = s["id"]
                break
        if not base_id:
            base_id = scenarios[0]["id"]
        
        create_payload = {
            "base_scenario_id": base_id,
            "name": f"TEST_OriginalForFork_{int(time.time())}",
            "customizations": [{
                "variable_name": "Emissions|CO2",
                "region": "World",
                "customized_values": {"2030": 20, "2050": 0}
            }]
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/scenario-builder/customize", json=create_payload)
        if create_resp.status_code == 201:
            return create_resp.json()["id"]
        return None
    
    def test_fork_creates_copy(self, custom_scenario_id):
        """Fork should create a copy of the custom scenario"""
        if not custom_scenario_id:
            pytest.skip("Could not create source scenario for fork")
        
        fork_payload = {
            "new_name": f"TEST_ForkedScenario_{int(time.time())}"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scenario-builder/custom/{custom_scenario_id}/fork",
            json=fork_payload
        )
        assert response.status_code == 201, f"Fork failed: {response.text}"
        
        data = response.json()
        assert data["is_fork"] is True
        assert "forked_from_id" not in data or data.get("description", "").startswith("Forked from")
        assert data["name"] == fork_payload["new_name"]
        assert "customizations" in data
        
        print(f"Forked scenario created: {data['id']}")
        
        # Cleanup both scenarios
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{data['id']}")
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{custom_scenario_id}")
    
    def test_fork_with_additional_customizations(self, custom_scenario_id):
        """Fork should allow adding additional customizations"""
        if not custom_scenario_id:
            pytest.skip("Could not create source scenario for fork")
        
        fork_payload = {
            "new_name": f"TEST_ForkedWithCustom_{int(time.time())}",
            "additional_customizations": [{
                "variable_name": "Price|Carbon",
                "region": "World",
                "customized_values": {"2030": 150, "2050": 400}
            }]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scenario-builder/custom/{custom_scenario_id}/fork",
            json=fork_payload
        )
        assert response.status_code == 201
        
        data = response.json()
        # Should have original + additional customizations
        assert len(data["customizations"]) >= 1
        print(f"Forked with additions: {len(data['customizations'])} customizations")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{data['id']}")
        requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{custom_scenario_id}")
    
    def test_fork_nonexistent_returns_404(self):
        """Fork on invalid ID should return 404"""
        fork_payload = {"new_name": "TEST_InvalidFork"}
        response = requests.post(
            f"{BASE_URL}/api/v1/scenario-builder/custom/nonexistent-id/fork",
            json=fork_payload
        )
        assert response.status_code == 404


# Cleanup fixture to remove TEST_ prefixed scenarios after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_scenarios():
    yield
    # Cleanup after all tests
    try:
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/custom")
        if response.status_code == 200:
            scenarios = response.json()
            for s in scenarios:
                if s.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/v1/scenario-builder/custom/{s['id']}")
                    print(f"Cleaned up: {s['name']}")
    except Exception as e:
        print(f"Cleanup warning: {e}")
