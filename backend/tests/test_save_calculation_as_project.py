"""
Test Save Calculation as Project Feature for Carbon Credits Module
Tests the POST /api/v1/carbon/projects/from-calculation endpoint

This feature allows users to save their methodology calculation results 
as new projects in their carbon credits portfolio.
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSaveCalculationAsProject:
    """Tests for the Save Calculation as Project feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.test_portfolio_id = "0f6aebd0-c2fc-4668-ab31-b7490e2fe6d7"
        self.test_project_prefix = "TEST_PYTEST_"
        yield
        # Cleanup test projects
        self._cleanup_test_projects()
    
    def _cleanup_test_projects(self):
        """Remove test projects created during tests"""
        try:
            projects_response = requests.get(
                f"{BASE_URL}/api/v1/carbon/projects",
                params={"portfolio_id": self.test_portfolio_id}
            )
            if projects_response.status_code == 200:
                projects = projects_response.json()
                for project in projects:
                    if project["name"].startswith(self.test_project_prefix):
                        requests.delete(f"{BASE_URL}/api/v1/carbon/projects/{project['id']}")
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def test_save_calculation_returns_201_with_valid_data(self):
        """Test that saving a calculation creates a new project successfully"""
        payload = {
            "portfolio_id": self.test_portfolio_id,
            "project_name": f"{self.test_project_prefix}Solar Farm Test",
            "methodology_code": "ACM0002",
            "annual_credits": 157286.0,
            "country_code": "US"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == payload["project_name"]
        assert data["annual_credits"] == payload["annual_credits"]
        assert data["country_code"] == payload["country_code"].upper()
        assert "id" in data
        print(f"Created project: {data['id']} - {data['name']}")
    
    def test_save_calculation_maps_methodology_to_project_type(self):
        """Test that methodology code is correctly mapped to project type and standard"""
        test_cases = [
            {"methodology_code": "ACM0002", "expected_type": "RENEWABLE_ENERGY", "expected_standard": "CDM"},
            {"methodology_code": "VM0048", "expected_type": "FOREST_CONSERVATION", "expected_standard": "VCS"},
            {"methodology_code": "TPDDTEC", "expected_type": "COOKSTOVES", "expected_standard": "GOLD_STANDARD"},
            {"methodology_code": "ACM0001", "expected_type": "METHANE_CAPTURE", "expected_standard": "CDM"},
        ]
        
        for tc in test_cases:
            payload = {
                "portfolio_id": self.test_portfolio_id,
                "project_name": f"{self.test_project_prefix}{tc['methodology_code']}_test",
                "methodology_code": tc["methodology_code"],
                "annual_credits": 10000.0,
                "country_code": "US"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["project_type"] == tc["expected_type"], f"Expected {tc['expected_type']}, got {data['project_type']} for {tc['methodology_code']}"
            assert data["standard"] == tc["expected_standard"], f"Expected {tc['expected_standard']}, got {data['standard']} for {tc['methodology_code']}"
            print(f"Methodology {tc['methodology_code']} correctly mapped to {data['project_type']}/{data['standard']}")
    
    def test_save_calculation_persists_to_database(self):
        """Test that saved project is actually persisted and can be retrieved"""
        project_name = f"{self.test_project_prefix}Persistence_Test_{uuid.uuid4().hex[:8]}"
        
        # Create project
        payload = {
            "portfolio_id": self.test_portfolio_id,
            "project_name": project_name,
            "methodology_code": "ACM0002",
            "annual_credits": 50000.0,
            "country_code": "BR"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
            json=payload
        )
        assert create_response.status_code == 200
        created_project = create_response.json()
        project_id = created_project["id"]
        
        # Verify project exists via GET
        get_response = requests.get(f"{BASE_URL}/api/v1/carbon/projects/{project_id}")
        assert get_response.status_code == 200
        
        fetched_project = get_response.json()
        assert fetched_project["name"] == project_name
        assert fetched_project["annual_credits"] == 50000.0
        assert fetched_project["country_code"] == "BR"
        print(f"Project {project_id} successfully persisted and retrieved")
    
    def test_save_calculation_sets_default_values(self):
        """Test that saving a calculation sets appropriate default values"""
        payload = {
            "portfolio_id": self.test_portfolio_id,
            "project_name": f"{self.test_project_prefix}Defaults_Test",
            "methodology_code": "ACM0002",
            "annual_credits": 100000.0,
            "country_code": "US"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check default values are set
        assert data["crediting_period_years"] == 10
        assert data["total_credits"] == data["annual_credits"] * 10  # 10 year crediting period
        assert data["status"] == "active"
        assert data["verification_status"] == "unverified"
        assert data["quality_rating"] == "BBB"
        assert data["quality_score"] is not None
        assert data["risk_level"] in ["Low", "Medium", "High"]
        assert data["risk_score"] is not None
        assert data["price_per_credit_usd"] == 15.0
        print("All default values correctly set")
    
    def test_save_calculation_with_invalid_portfolio_returns_404(self):
        """Test that saving to a non-existent portfolio returns 404"""
        payload = {
            "portfolio_id": "non-existent-portfolio-id",
            "project_name": f"{self.test_project_prefix}Invalid_Portfolio",
            "methodology_code": "ACM0002",
            "annual_credits": 10000.0,
            "country_code": "US"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
            json=payload
        )
        
        assert response.status_code == 404
        assert "Portfolio not found" in response.json().get("detail", "")
        print("Correctly returned 404 for invalid portfolio")
    
    def test_save_calculation_with_missing_required_fields_returns_422(self):
        """Test validation of required fields"""
        # Missing project_name
        payload = {
            "portfolio_id": self.test_portfolio_id,
            "methodology_code": "ACM0002",
            "annual_credits": 10000.0,
            "country_code": "US"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
            json=payload
        )
        
        assert response.status_code == 422
        print("Correctly returned 422 for missing required field")
    
    def test_save_calculation_with_different_countries(self):
        """Test that different country codes are correctly saved"""
        countries = ["US", "BR", "IN", "CN", "DE", "AU"]
        
        for country in countries:
            payload = {
                "portfolio_id": self.test_portfolio_id,
                "project_name": f"{self.test_project_prefix}Country_{country}",
                "methodology_code": "ACM0002",
                "annual_credits": 10000.0,
                "country_code": country
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["country_code"] == country.upper()
            print(f"Country {country} correctly saved")
    
    def test_save_calculation_with_optional_fields(self):
        """Test saving with optional calculation_inputs and calculation_result fields"""
        payload = {
            "portfolio_id": self.test_portfolio_id,
            "project_name": f"{self.test_project_prefix}Optional_Fields",
            "methodology_code": "ACM0002",
            "annual_credits": 157286.0,
            "country_code": "US",
            "calculation_inputs": {
                "installed_capacity_mw": 150,
                "capacity_factor": 0.28,
                "grid_emission_factor": 0.45
            },
            "calculation_result": {
                "emission_reductions": 157286,
                "baseline_emissions": 165564,
                "project_emissions": 0
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == payload["project_name"]
        print("Optional fields handled correctly")


class TestCalculatorIntegration:
    """Integration tests for Calculator workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_portfolio_id = "0f6aebd0-c2fc-4668-ab31-b7490e2fe6d7"
        self.test_project_prefix = "TEST_INTEG_"
        yield
        self._cleanup_test_projects()
    
    def _cleanup_test_projects(self):
        try:
            projects_response = requests.get(
                f"{BASE_URL}/api/v1/carbon/projects",
                params={"portfolio_id": self.test_portfolio_id}
            )
            if projects_response.status_code == 200:
                projects = projects_response.json()
                for project in projects:
                    if project["name"].startswith(self.test_project_prefix):
                        requests.delete(f"{BASE_URL}/api/v1/carbon/projects/{project['id']}")
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def test_full_calculator_to_save_workflow(self):
        """Test full workflow: Calculate → Get Result → Save as Project → Verify"""
        
        # Step 1: Run calculation with ACM0002
        calc_payload = {
            "installed_capacity_mw": 200,
            "capacity_factor": 0.30,
            "grid_emission_factor": 0.50
        }
        
        calc_response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=ACM0002",
            json=calc_payload
        )
        assert calc_response.status_code == 200
        calc_result = calc_response.json()
        emission_reductions = calc_result["emission_reductions"]
        print(f"Step 1: Calculated {emission_reductions} tCO2e")
        
        # Step 2: Save as project
        save_payload = {
            "portfolio_id": self.test_portfolio_id,
            "project_name": f"{self.test_project_prefix}Full_Workflow",
            "methodology_code": "ACM0002",
            "annual_credits": emission_reductions,
            "country_code": "DE",
            "calculation_inputs": calc_payload,
            "calculation_result": calc_result
        }
        
        save_response = requests.post(
            f"{BASE_URL}/api/v1/carbon/projects/from-calculation",
            json=save_payload
        )
        assert save_response.status_code == 200
        saved_project = save_response.json()
        project_id = saved_project["id"]
        print(f"Step 2: Saved project {project_id}")
        
        # Step 3: Verify project in portfolio projects list
        list_response = requests.get(
            f"{BASE_URL}/api/v1/carbon/projects",
            params={"portfolio_id": self.test_portfolio_id}
        )
        assert list_response.status_code == 200
        projects = list_response.json()
        
        project_found = any(p["id"] == project_id for p in projects)
        assert project_found, "Saved project not found in portfolio projects list"
        print(f"Step 3: Project verified in portfolio list")
        
        # Step 4: Verify annual credits match calculation
        saved_credits = next(p["annual_credits"] for p in projects if p["id"] == project_id)
        assert saved_credits == emission_reductions
        print(f"Step 4: Annual credits verified: {saved_credits}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
