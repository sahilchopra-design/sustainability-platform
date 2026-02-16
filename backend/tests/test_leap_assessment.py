"""
Tests for LEAP Assessment API
- POST /api/v1/nature-risk/leap-assessments - Create LEAP assessment
- GET /api/v1/nature-risk/leap-assessments - List assessments
- POST /api/v1/nature-risk/leap-assessments/calculate - Calculate LEAP scores
"""

import pytest
import requests
import os
from datetime import date

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Valid scenario IDs from seed data
VALID_SCENARIO_IDS = [
    "scenario-tnfd-current",
    "scenario-tnfd-sustainable",
    "scenario-ncore-physical",
    "scenario-ncore-transition"
]


class TestLEAPAssessmentCreate:
    """Test POST /api/v1/nature-risk/leap-assessments endpoint"""
    
    def test_create_leap_assessment_returns_200(self):
        """Create LEAP assessment should return 200"""
        payload = {
            "entity_id": "test-entity-001",
            "entity_type": "company",
            "assessment_name": "Test Company LEAP Assessment",
            "assessment_date": str(date.today()),
            "sector_code": "ENERGY"
        }
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_create_leap_assessment_returns_id(self):
        """Created LEAP assessment should have an id"""
        payload = {
            "entity_id": "test-entity-002",
            "entity_type": "asset",
            "assessment_name": "Test Asset LEAP Assessment",
            "assessment_date": str(date.today()),
            "sector_code": "MINING"
        }
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert data["id"] is not None


class TestLEAPAssessmentList:
    """Test GET /api/v1/nature-risk/leap-assessments endpoint"""
    
    def test_list_leap_assessments_returns_200(self):
        """List LEAP assessments should return 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/leap-assessments")
        assert response.status_code == 200
    
    def test_list_leap_assessments_returns_array(self):
        """List LEAP assessments should return an array"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/leap-assessments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"


class TestLEAPAssessmentCalculate:
    """Test POST /api/v1/nature-risk/leap-assessments/calculate endpoint"""
    
    def test_calculate_leap_returns_200(self):
        """Calculate LEAP assessment should return 200"""
        payload = {
            "entity_id": "test-entity-calc-001",
            "entity_type": "company",
            "scenario_ids": [VALID_SCENARIO_IDS[0]],
            "include_dependencies": True,
            "include_water_risk": True,
            "include_biodiversity_overlap": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments/calculate", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_calculate_leap_returns_scores(self):
        """Calculate LEAP should return locate, evaluate, assess, prepare scores"""
        payload = {
            "entity_id": "test-entity-calc-002",
            "entity_type": "company",
            "scenario_ids": [VALID_SCENARIO_IDS[0]],
            "include_dependencies": True,
            "include_water_risk": True,
            "include_biodiversity_overlap": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "scenario_results" in data, "Response should contain scenario_results"
        results = data["scenario_results"]
        assert len(results) > 0, "Should have at least one scenario result"
        
        result = results[0]
        assert "locate_score" in result, "Result should have locate_score"
        assert "evaluate_score" in result, "Result should have evaluate_score"
        assert "assess_score" in result, "Result should have assess_score"
        assert "prepare_score" in result, "Result should have prepare_score"
        assert "overall_score" in result, "Result should have overall_score"
    
    def test_calculate_leap_returns_risk_rating(self):
        """Calculate LEAP should return overall risk rating"""
        payload = {
            "entity_id": "test-entity-calc-003",
            "entity_type": "company",
            "scenario_ids": [VALID_SCENARIO_IDS[1]],  # TNFD Sustainable
            "include_dependencies": True,
            "include_water_risk": False,
            "include_biodiversity_overlap": False
        }
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        result = data["scenario_results"][0]
        assert "overall_risk_rating" in result, "Result should have overall_risk_rating"
        # Valid risk ratings
        valid_ratings = ["low", "medium-low", "medium", "medium-high", "high"]
        assert result["overall_risk_rating"] in valid_ratings, f"Risk rating should be valid, got {result['overall_risk_rating']}"
    
    def test_calculate_leap_returns_recommendations(self):
        """Calculate LEAP should return recommendations"""
        payload = {
            "entity_id": "test-entity-calc-004",
            "entity_type": "asset",
            "scenario_ids": [VALID_SCENARIO_IDS[2]],  # NCORE Physical
            "include_dependencies": True,
            "include_water_risk": True,
            "include_biodiversity_overlap": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        result = data["scenario_results"][0]
        assert "recommendations" in result, "Result should have recommendations"
        assert isinstance(result["recommendations"], list), "Recommendations should be a list"
    
    def test_calculate_leap_with_invalid_scenario_returns_400(self):
        """Calculate LEAP with invalid scenario should return 400"""
        payload = {
            "entity_id": "test-entity-calc-005",
            "entity_type": "company",
            "scenario_ids": ["invalid-scenario-id"],
            "include_dependencies": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments/calculate", json=payload)
        assert response.status_code == 400, f"Expected 400 for invalid scenario, got {response.status_code}"


class TestNatureRiskScenarios:
    """Test nature risk scenarios endpoints"""
    
    def test_list_scenarios_returns_200(self):
        """GET /api/v1/nature-risk/scenarios should return 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios")
        assert response.status_code == 200
    
    def test_list_scenarios_returns_array(self):
        """Scenarios endpoint should return array of scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one scenario"
    
    def test_scenarios_have_required_fields(self):
        """Each scenario should have id, name, framework"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios")
        assert response.status_code == 200
        data = response.json()
        
        if data:
            scenario = data[0]
            assert "id" in scenario, "Scenario should have 'id'"
            assert "name" in scenario, "Scenario should have 'name'"
            assert "framework" in scenario, "Scenario should have 'framework'"


class TestENCOREEndpoints:
    """Test ENCORE dependency endpoints used by LEAP wizard"""
    
    def test_encore_sectors_returns_200(self):
        """GET /api/v1/nature-risk/encore/sectors should return 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/sectors")
        assert response.status_code == 200
    
    def test_encore_sectors_returns_array(self):
        """ENCORE sectors should return array"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/sectors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_encore_ecosystem_services_returns_200(self):
        """GET /api/v1/nature-risk/encore/ecosystem-services should return 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/ecosystem-services")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
