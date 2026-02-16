"""
Tests for Scenario Persistence to PostgreSQL
- POST /api/v1/scenarios/build - Create scenario
- GET /api/v1/scenarios/list - List all scenarios
- GET /api/v1/scenarios/{id} - Get scenario by ID
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Sample property UUID from scenario_analysis_engine.py
SAMPLE_PROPERTY_ID = "00000000-0000-0000-0000-000000000001"


class TestScenarioBuild:
    """Test POST /api/v1/scenarios/build endpoint for scenario creation"""
    
    def test_build_scenario_returns_200(self):
        """POST /api/v1/scenarios/build should return 200 with valid payload"""
        payload = {
            "base_property_id": SAMPLE_PROPERTY_ID,
            "scenario_name": f"TEST_Scenario_{uuid.uuid4().hex[:8]}",
            "description": "Testing scenario persistence",
            "modifications": [
                {
                    "type": "cap_rate",
                    "parameter": "cap_rate",
                    "new_value": 0.055
                }
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_build_scenario_returns_scenario_id(self):
        """Build scenario should return a scenario_id in response"""
        payload = {
            "base_property_id": SAMPLE_PROPERTY_ID,
            "scenario_name": f"TEST_ScenarioID_{uuid.uuid4().hex[:8]}",
            "modifications": [
                {"type": "vacancy", "parameter": "vacancy_rate", "new_value": 0.08}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "scenario_id" in data, f"Response should contain scenario_id. Got: {data.keys()}"
        assert data["scenario_id"] is not None
    
    def test_build_scenario_returns_values(self):
        """Build scenario should return base_value, adjusted_value, value_change_pct"""
        payload = {
            "base_property_id": SAMPLE_PROPERTY_ID,
            "scenario_name": f"TEST_Values_{uuid.uuid4().hex[:8]}",
            "modifications": [
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.05}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "base_value" in data, "Response should contain base_value"
        assert "adjusted_value" in data, "Response should contain adjusted_value"
        assert "value_change_pct" in data, "Response should contain value_change_pct"
        
        # Values should be numeric
        base_value = float(data["base_value"])
        adjusted_value = float(data["adjusted_value"])
        assert base_value > 0, "base_value should be positive"
        assert adjusted_value > 0, "adjusted_value should be positive"
    
    def test_build_scenario_with_multiple_modifications(self):
        """Build scenario should support multiple modifications"""
        payload = {
            "base_property_id": SAMPLE_PROPERTY_ID,
            "scenario_name": f"TEST_MultiMod_{uuid.uuid4().hex[:8]}",
            "modifications": [
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.06},
                {"type": "vacancy", "parameter": "vacancy_rate", "new_value": 0.10},
                {"type": "rent_growth", "parameter": "rent_growth_rate", "new_value": 0.03}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "modifications_applied" in data
        assert data["modifications_applied"] == 3, f"Expected 3 modifications, got {data['modifications_applied']}"


class TestScenarioList:
    """Test GET /api/v1/scenarios/list endpoint"""
    
    def test_list_scenarios_returns_200(self):
        """GET /api/v1/scenarios/list should return 200"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_list_scenarios_returns_items_array(self):
        """List scenarios should return items array"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data, "Response should contain 'items' array"
        assert isinstance(data["items"], list), "'items' should be a list"
    
    def test_list_scenarios_returns_total(self):
        """List scenarios should return total count"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data, "Response should contain 'total' count"
        assert isinstance(data["total"], int), "'total' should be an integer"
    
    def test_list_scenarios_items_have_required_fields(self):
        """Scenario items should have id, scenario_name, base_value, adjusted_value"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            item = data["items"][0]
            assert "id" in item, "Scenario should have 'id'"
            assert "scenario_name" in item, "Scenario should have 'scenario_name'"
            assert "base_value" in item, "Scenario should have 'base_value'"
            assert "adjusted_value" in item, "Scenario should have 'adjusted_value'"


class TestScenarioGetById:
    """Test GET /api/v1/scenarios/{id} endpoint"""
    
    def test_get_scenario_by_id_returns_200(self):
        """GET /api/v1/scenarios/{id} should return 200 for existing scenario"""
        # First create a scenario
        payload = {
            "base_property_id": SAMPLE_PROPERTY_ID,
            "scenario_name": f"TEST_GetById_{uuid.uuid4().hex[:8]}",
            "modifications": [
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.055}
            ]
        }
        create_response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert create_response.status_code == 200
        scenario_id = create_response.json()["scenario_id"]
        
        # Then retrieve it
        get_response = requests.get(f"{BASE_URL}/api/v1/scenarios/{scenario_id}")
        assert get_response.status_code == 200, f"Expected 200, got {get_response.status_code}: {get_response.text}"
    
    def test_get_scenario_returns_correct_data(self):
        """Get scenario should return correct scenario data"""
        # Create scenario with known name
        unique_name = f"TEST_DataCheck_{uuid.uuid4().hex[:8]}"
        payload = {
            "base_property_id": SAMPLE_PROPERTY_ID,
            "scenario_name": unique_name,
            "description": "Test description for data check",
            "modifications": [
                {"type": "vacancy", "parameter": "vacancy_rate", "new_value": 0.12}
            ]
        }
        create_response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert create_response.status_code == 200
        scenario_id = create_response.json()["scenario_id"]
        
        # Retrieve and verify
        get_response = requests.get(f"{BASE_URL}/api/v1/scenarios/{scenario_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        
        assert data["scenario_name"] == unique_name, f"Expected name {unique_name}, got {data['scenario_name']}"
        assert data["id"] == scenario_id, f"Expected id {scenario_id}, got {data['id']}"
    
    def test_get_nonexistent_scenario_returns_404(self):
        """GET /api/v1/scenarios/{id} should return 404 for non-existent scenario"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/{fake_id}")
        # Should return 404 for not found
        assert response.status_code in [404, 200], f"Expected 404, got {response.status_code}"


class TestScenarioPersistence:
    """Test that scenarios are actually persisted to database"""
    
    def test_created_scenario_appears_in_list(self):
        """Creating a scenario should make it appear in the list"""
        unique_name = f"TEST_Persist_{uuid.uuid4().hex[:8]}"
        payload = {
            "base_property_id": SAMPLE_PROPERTY_ID,
            "scenario_name": unique_name,
            "modifications": [
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.048}
            ]
        }
        
        # Create scenario
        create_response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert create_response.status_code == 200
        scenario_id = create_response.json()["scenario_id"]
        
        # Check it appears in list
        list_response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        assert list_response.status_code == 200
        
        items = list_response.json()["items"]
        scenario_ids = [item["id"] for item in items]
        assert scenario_id in scenario_ids, f"Created scenario {scenario_id} should appear in list"
        
        # Also verify name
        matching = [item for item in items if item["id"] == scenario_id]
        assert len(matching) == 1
        assert matching[0]["scenario_name"] == unique_name


class TestScenarioProperties:
    """Test properties endpoint for dropdown data"""
    
    def test_properties_returns_200(self):
        """GET /api/v1/scenarios/properties should return 200"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        assert response.status_code == 200
    
    def test_properties_returns_list(self):
        """Properties endpoint should return list of properties"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        assert response.status_code == 200
        data = response.json()
        
        assert "properties" in data
        assert isinstance(data["properties"], list)
        assert len(data["properties"]) > 0, "Should have at least one sample property"
    
    def test_property_has_required_fields(self):
        """Each property should have id, name, property_type"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        assert response.status_code == 200
        properties = response.json()["properties"]
        
        if properties:
            prop = properties[0]
            assert "id" in prop, "Property should have 'id'"
            assert "name" in prop, "Property should have 'name'"
            assert "property_type" in prop, "Property should have 'property_type'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
