"""
Carbon Credits Module - Backend API Tests
Tests for carbon portfolios, projects, methodologies, calculations, and reports.
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://climate-risk-deploy.preview.emergentagent.com')

# Test data prefix for cleanup
TEST_PREFIX = "TEST_CARBON_"


class TestCarbonMethodologies:
    """Test Carbon Methodologies API"""
    
    def test_get_methodologies_returns_list(self):
        """GET /api/v1/carbon/methodologies returns list of methodologies"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodologies", params={"limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"Found {len(data)} methodologies")
    
    def test_methodologies_have_required_fields(self):
        """Methodologies have required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodologies", params={"limit": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        methodology = data[0]
        required_fields = ['id', 'code', 'name', 'standard', 'sector', 'status']
        for field in required_fields:
            assert field in methodology, f"Missing field: {field}"
        print(f"Methodology: {methodology['code']} - {methodology['name']}")
    
    def test_methodologies_filter_by_sector(self):
        """Filter methodologies by sector"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodologies", params={"sector": "Forestry"})
        assert response.status_code == 200
        data = response.json()
        for m in data:
            assert m['sector'] == 'Forestry'
        print(f"Found {len(data)} Forestry methodologies")
    
    def test_methodologies_filter_by_standard(self):
        """Filter methodologies by standard"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodologies", params={"standard": "VCS"})
        assert response.status_code == 200
        data = response.json()
        for m in data:
            assert m['standard'] == 'VCS'
        print(f"Found {len(data)} VCS methodologies")


class TestCarbonEmissionFactors:
    """Test Emission Factors API"""
    
    def test_get_emission_factors(self):
        """GET /api/v1/carbon/emission-factors returns emission factors"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/emission-factors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"Found {len(data)} emission factors")
    
    def test_emission_factors_have_required_fields(self):
        """Emission factors have required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/emission-factors", params={"limit": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        factor = data[0]
        required_fields = ['id', 'country_code', 'country_name', 'year', 'grid_emission_factor']
        for field in required_fields:
            assert field in factor, f"Missing field: {field}"
        print(f"Emission factor: {factor['country_code']} ({factor['year']}) - {factor['grid_emission_factor']} tCO2/MWh")
    
    def test_emission_factors_filter_by_country(self):
        """Filter emission factors by country code"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/emission-factors", params={"country_code": "US"})
        assert response.status_code == 200
        data = response.json()
        for f in data:
            assert f['country_code'] == 'US'
        print(f"Found {len(data)} US emission factors")


class TestCarbonPortfolios:
    """Test Carbon Portfolios API - CRUD operations"""
    
    created_portfolio_id = None
    
    def test_create_portfolio(self):
        """POST /api/v1/carbon/portfolios creates new portfolio"""
        payload = {
            "name": f"{TEST_PREFIX}Test Portfolio {uuid.uuid4().hex[:6]}",
            "description": "Test portfolio for API testing",
            "target_annual_credits": 50000,
            "budget_usd": 1000000,
            "quality_minimum": "A"
        }
        response = requests.post(f"{BASE_URL}/api/v1/carbon/portfolios", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert 'id' in data
        assert data['name'] == payload['name']
        assert data['status'] == 'active'
        assert data['project_count'] == 0
        assert data['total_annual_credits'] == 0
        
        TestCarbonPortfolios.created_portfolio_id = data['id']
        print(f"Created portfolio: {data['id']}")
    
    def test_get_portfolios(self):
        """GET /api/v1/carbon/portfolios returns list of portfolios"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/portfolios", params={"limit": 50})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} portfolios")
    
    def test_get_portfolio_by_id(self):
        """GET /api/v1/carbon/portfolios/{id} returns specific portfolio"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        response = requests.get(f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == TestCarbonPortfolios.created_portfolio_id
        print(f"Retrieved portfolio: {data['name']}")
    
    def test_update_portfolio(self):
        """PUT /api/v1/carbon/portfolios/{id} updates portfolio"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        payload = {
            "name": f"{TEST_PREFIX}Updated Portfolio",
            "target_annual_credits": 75000
        }
        response = requests.put(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == payload['name']
        assert data['target_annual_credits'] == payload['target_annual_credits']
        print(f"Updated portfolio: {data['name']}")
    
    def test_get_portfolio_not_found(self):
        """GET /api/v1/carbon/portfolios/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/portfolios/invalid-id-12345")
        assert response.status_code == 404


class TestCarbonProjects:
    """Test Carbon Projects API - CRUD operations"""
    
    created_project_id = None
    
    def test_create_project(self):
        """POST /api/v1/carbon/projects creates new project"""
        # First, ensure we have a portfolio
        if not TestCarbonPortfolios.created_portfolio_id:
            # Create a portfolio first
            payload = {
                "name": f"{TEST_PREFIX}Portfolio for Projects",
                "description": "Test portfolio"
            }
            response = requests.post(f"{BASE_URL}/api/v1/carbon/portfolios", json=payload)
            assert response.status_code == 200
            TestCarbonPortfolios.created_portfolio_id = response.json()['id']
        
        project_payload = {
            "portfolio_id": TestCarbonPortfolios.created_portfolio_id,
            "name": f"{TEST_PREFIX}Solar Farm Project",
            "project_type": "RENEWABLE_ENERGY",
            "standard": "VCS",
            "country_code": "US",
            "region": "California",
            "annual_credits": 25000,
            "total_credits": 250000,
            "crediting_period_years": 10,
            "price_per_credit_usd": 15.50,
            "coordinates": {"lat": 36.7783, "lng": -119.4179}
        }
        response = requests.post(f"{BASE_URL}/api/v1/carbon/projects", json=project_payload)
        assert response.status_code == 200
        data = response.json()
        
        assert 'id' in data
        assert data['name'] == project_payload['name']
        assert data['project_type'] == 'RENEWABLE_ENERGY'
        assert data['status'] == 'active'
        assert data['annual_credits'] == 25000
        
        TestCarbonProjects.created_project_id = data['id']
        print(f"Created project: {data['id']} - {data['name']}")
    
    def test_get_projects(self):
        """GET /api/v1/carbon/projects returns list of projects"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/projects", params={"limit": 50})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} projects")
    
    def test_get_projects_by_portfolio(self):
        """GET /api/v1/carbon/projects filtered by portfolio_id"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/projects",
            params={"portfolio_id": TestCarbonPortfolios.created_portfolio_id}
        )
        assert response.status_code == 200
        data = response.json()
        for p in data:
            assert p['portfolio_id'] == TestCarbonPortfolios.created_portfolio_id
        print(f"Found {len(data)} projects in portfolio")
    
    def test_get_project_by_id(self):
        """GET /api/v1/carbon/projects/{id} returns specific project"""
        if not TestCarbonProjects.created_project_id:
            pytest.skip("No project created")
        
        response = requests.get(f"{BASE_URL}/api/v1/carbon/projects/{TestCarbonProjects.created_project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == TestCarbonProjects.created_project_id
        print(f"Retrieved project: {data['name']}")
    
    def test_update_project(self):
        """PUT /api/v1/carbon/projects/{id} updates project"""
        if not TestCarbonProjects.created_project_id:
            pytest.skip("No project created")
        
        payload = {
            "annual_credits": 30000,
            "verification_status": "verified"
        }
        response = requests.put(
            f"{BASE_URL}/api/v1/carbon/projects/{TestCarbonProjects.created_project_id}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data['annual_credits'] == 30000
        assert data['verification_status'] == 'verified'
        print(f"Updated project: annual_credits = {data['annual_credits']}")
    
    def test_project_not_found(self):
        """GET /api/v1/carbon/projects/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/projects/invalid-project-id")
        assert response.status_code == 404


class TestCarbonPortfolioDashboard:
    """Test Portfolio Dashboard API"""
    
    def test_get_dashboard_returns_data(self):
        """GET /api/v1/carbon/portfolios/{id}/dashboard returns dashboard data"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}/dashboard"
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert 'portfolio_id' in data
        assert 'portfolio_name' in data
        assert 'summary' in data
        assert 'projects' in data
        assert 'yearly_projections' in data
        assert 'risk_heat_map' in data
        assert 'geographic_distribution' in data
        print(f"Dashboard for: {data['portfolio_name']}")
    
    def test_dashboard_summary_fields(self):
        """Dashboard summary has required fields"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}/dashboard"
        )
        assert response.status_code == 200
        summary = response.json()['summary']
        
        required_fields = [
            'total_annual_credits', 
            'total_risk_adjusted_credits',
            'portfolio_quality_score',
            'portfolio_quality_rating',
            'portfolio_npv_10yr_usd',
            'project_count',
            'average_risk_score'
        ]
        for field in required_fields:
            assert field in summary, f"Missing summary field: {field}"
        print(f"Summary - Credits: {summary['total_annual_credits']}, NPV: {summary['portfolio_npv_10yr_usd']}")
    
    def test_dashboard_yearly_projections(self):
        """Dashboard has yearly projections"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}/dashboard"
        )
        assert response.status_code == 200
        projections = response.json()['yearly_projections']
        
        assert isinstance(projections, list)
        if len(projections) > 0:
            proj = projections[0]
            assert 'year' in proj
            assert 'base_case' in proj
            assert 'optimistic' in proj
            assert 'pessimistic' in proj
            assert 'risk_adjusted' in proj
            print(f"Found {len(projections)} yearly projections")


class TestCarbonScenarios:
    """Test Scenarios API"""
    
    created_scenario_id = None
    
    def test_get_scenarios_creates_default(self):
        """GET /api/v1/carbon/portfolios/{id}/scenarios creates default scenario if none exists"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}/scenarios"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # First scenario should be default
        assert data[0]['is_default'] == True
        print(f"Found {len(data)} scenarios, default: {data[0]['name']}")
    
    def test_create_scenario(self):
        """POST /api/v1/carbon/portfolios/{id}/scenarios creates new scenario"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        # Note: portfolio_id is in the URL, not in the payload
        payload = {
            "name": f"{TEST_PREFIX}High Risk Scenario",
            "description": "Scenario with higher risk assumptions",
            "is_default": False,
            "permanence_risk_pct": 15.0,
            "delivery_risk_pct": 10.0,
            "regulatory_risk_pct": 8.0,
            "market_risk_pct": 15.0,
            "base_carbon_price_usd": 20.0,
            "price_growth_rate_pct": 7.0,
            "price_volatility_pct": 25.0,
            "discount_rate_pct": 10.0,
            "projection_years": 15,
            "parameters": {}
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}/scenarios",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert 'id' in data
        assert data['name'] == payload['name']
        assert data['permanence_risk_pct'] == 15.0
        assert data['projection_years'] == 15
        
        TestCarbonScenarios.created_scenario_id = data['id']
        print(f"Created scenario: {data['name']}")
    
    def test_scenarios_have_required_fields(self):
        """Scenarios have all required risk/price fields"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}/scenarios"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        scenario = data[0]
        required_fields = [
            'permanence_risk_pct', 'delivery_risk_pct', 
            'regulatory_risk_pct', 'market_risk_pct',
            'base_carbon_price_usd', 'price_growth_rate_pct',
            'discount_rate_pct', 'projection_years'
        ]
        for field in required_fields:
            assert field in scenario, f"Missing field: {field}"


class TestCarbonCalculations:
    """Test Calculations API"""
    
    calculation_id = None
    
    def test_run_standard_calculation(self):
        """POST /api/v1/carbon/calculate runs standard calculation"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        payload = {
            "portfolio_id": TestCarbonPortfolios.created_portfolio_id,
            "calculation_type": "standard"
        }
        response = requests.post(f"{BASE_URL}/api/v1/carbon/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'calculation_id' in data
        assert 'status' in data
        assert data['status'] == 'completed'
        assert 'total_annual_credits' in data
        assert 'total_risk_adjusted_credits' in data
        assert 'portfolio_npv_10yr_usd' in data
        assert 'risk_breakdown' in data
        assert 'yearly_projections' in data
        
        TestCarbonCalculations.calculation_id = data['calculation_id']
        print(f"Calculation completed: {data['calculation_id']}")
        print(f"Credits: {data['total_annual_credits']}, Risk-adjusted: {data['total_risk_adjusted_credits']}")
        print(f"NPV: ${data['portfolio_npv_10yr_usd']:,.2f}")
    
    def test_calculation_with_scenario(self):
        """POST /api/v1/carbon/calculate with scenario_id"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        # Get scenarios first
        scenarios_response = requests.get(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}/scenarios"
        )
        scenarios = scenarios_response.json()
        if not scenarios:
            pytest.skip("No scenarios available")
        
        payload = {
            "portfolio_id": TestCarbonPortfolios.created_portfolio_id,
            "scenario_id": scenarios[0]['id'],
            "calculation_type": "standard"
        }
        response = requests.post(f"{BASE_URL}/api/v1/carbon/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['scenario_id'] == scenarios[0]['id']
        print(f"Calculated with scenario: {scenarios[0]['name']}")
    
    def test_calculation_risk_breakdown(self):
        """Calculation returns proper risk breakdown"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        payload = {
            "portfolio_id": TestCarbonPortfolios.created_portfolio_id,
            "calculation_type": "standard"
        }
        response = requests.post(f"{BASE_URL}/api/v1/carbon/calculate", json=payload)
        assert response.status_code == 200
        risk = response.json()['risk_breakdown']
        
        required_fields = [
            'permanence_risk', 'delivery_risk', 
            'regulatory_risk', 'market_risk', 'total_risk_pct'
        ]
        for field in required_fields:
            assert field in risk, f"Missing risk field: {field}"
        
        print(f"Risk breakdown - Total: {risk['total_risk_pct']}%")
    
    def test_get_calculation_by_id(self):
        """GET /api/v1/carbon/calculations/{id} retrieves calculation"""
        if not TestCarbonCalculations.calculation_id:
            pytest.skip("No calculation created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/calculations/{TestCarbonCalculations.calculation_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data['calculation_id'] == TestCarbonCalculations.calculation_id
        print(f"Retrieved calculation: {data['calculation_id']}")


class TestCarbonReports:
    """Test Reports API"""
    
    report_id = None
    
    def test_generate_report(self):
        """POST /api/v1/carbon/reports/generate creates a report"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio created")
        
        payload = {
            "portfolio_id": TestCarbonPortfolios.created_portfolio_id,
            "report_type": "summary",
            "format": "pdf",
            "title": f"{TEST_PREFIX}Test Report"
        }
        response = requests.post(f"{BASE_URL}/api/v1/carbon/reports/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert 'id' in data
        assert data['report_type'] == 'summary'
        assert data['format'] == 'pdf'
        assert data['status'] == 'completed'
        
        TestCarbonReports.report_id = data['id']
        print(f"Generated report: {data['id']}")
    
    def test_download_report(self):
        """GET /api/v1/carbon/reports/{id}/download simulates download"""
        if not TestCarbonReports.report_id:
            pytest.skip("No report created")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/reports/{TestCarbonReports.report_id}/download"
        )
        assert response.status_code == 200
        data = response.json()
        assert 'report_id' in data
        print(f"Download simulated for report: {data['report_id']}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_delete_project(self):
        """DELETE /api/v1/carbon/projects/{id}"""
        if not TestCarbonProjects.created_project_id:
            pytest.skip("No project to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/v1/carbon/projects/{TestCarbonProjects.created_project_id}"
        )
        assert response.status_code == 200
        print(f"Deleted project: {TestCarbonProjects.created_project_id}")
    
    def test_delete_portfolio(self):
        """DELETE /api/v1/carbon/portfolios/{id}"""
        if not TestCarbonPortfolios.created_portfolio_id:
            pytest.skip("No portfolio to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/v1/carbon/portfolios/{TestCarbonPortfolios.created_portfolio_id}"
        )
        assert response.status_code == 200
        print(f"Deleted portfolio: {TestCarbonPortfolios.created_portfolio_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
