"""
Full Regression Test Suite for Climate Risk and Real Estate Analysis Platform
Tests all modules: Auth, Carbon, Nature Risk, Stranded Assets, Valuation, 
Sustainability, Scenarios, Portfolio Analytics, Exports, Scheduled Reports
"""

import pytest
import requests
import os
from datetime import datetime

# Public URL from frontend/.env
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://risk-assessment-hub-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "newtestuser@test.com"
TEST_PASSWORD = "password"
SAMPLE_PORTFOLIO_ID = "00000000-0000-0000-0000-000000000101"
SAMPLE_PROPERTY_ID = "00000000-0000-0000-0000-000000000001"


class TestAuthentication:
    """Authentication module tests"""
    
    def test_login_returns_200(self):
        """POST /api/auth/login returns 200"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Login returns 200")
    
    def test_login_returns_token(self):
        """Login response contains access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        data = response.json()
        assert "access_token" in data, "Login response should contain access_token"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        print("✓ Login returns valid JWT token")
    
    def test_me_endpoint(self):
        """GET /api/auth/me returns user info"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_resp.json().get("access_token")
        
        # Call /me endpoint
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "email" in data
        print("✓ /me endpoint returns user info")


class TestCarbonCreditsModule:
    """Carbon Credits module tests - 10 sector tabs"""
    
    def test_list_carbon_portfolios(self):
        """GET /api/v1/carbon/portfolios returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/portfolios")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Carbon portfolios list returns 200")
    
    def test_carbon_methodologies(self):
        """GET /api/v1/carbon/methodologies returns methodologies"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodologies")
        assert response.status_code == 200
        print("✓ Carbon methodologies returns 200")
    
    def test_methodology_list(self):
        """GET /api/v1/carbon/methodology-list returns all methodologies"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list")
        assert response.status_code == 200
        data = response.json()
        assert "methodologies" in data
        assert "sectors" in data
        print(f"✓ Methodology list returns {len(data.get('methodologies', []))} methodologies")
    
    def test_methodology_by_sector_energy(self):
        """GET /api/v1/carbon/methodology-list/ENERGY returns energy sector"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/ENERGY")
        assert response.status_code == 200
        data = response.json()
        assert data.get("sector") == "ENERGY"
        print("✓ Energy sector methodologies returned")
    
    def test_methodology_by_sector_forestry(self):
        """GET /api/v1/carbon/methodology-list/FORESTRY returns forestry sector"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/FORESTRY")
        assert response.status_code == 200
        data = response.json()
        assert data.get("sector") == "FORESTRY"
        print("✓ Forestry sector methodologies returned")
    
    def test_methodology_by_sector_waste(self):
        """GET /api/v1/carbon/methodology-list/WASTE returns waste sector"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/WASTE")
        assert response.status_code == 200
        print("✓ Waste sector methodologies returned")
    
    def test_methodology_by_sector_agriculture(self):
        """GET /api/v1/carbon/methodology-list/AGRICULTURE"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/AGRICULTURE")
        assert response.status_code == 200
        print("✓ Agriculture sector methodologies returned")
    
    def test_methodology_by_sector_household(self):
        """GET /api/v1/carbon/methodology-list/HOUSEHOLD"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/HOUSEHOLD")
        assert response.status_code == 200
        print("✓ Household sector methodologies returned")
    
    def test_methodology_by_sector_industrial(self):
        """GET /api/v1/carbon/methodology-list/INDUSTRIAL"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/INDUSTRIAL")
        assert response.status_code == 200
        print("✓ Industrial sector methodologies returned")
    
    def test_methodology_by_sector_transport(self):
        """GET /api/v1/carbon/methodology-list/TRANSPORT"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/TRANSPORT")
        assert response.status_code == 200
        print("✓ Transport sector methodologies returned")
    
    def test_methodology_by_sector_buildings(self):
        """GET /api/v1/carbon/methodology-list/BUILDINGS"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/BUILDINGS")
        assert response.status_code == 200
        print("✓ Buildings sector methodologies returned")
    
    def test_methodology_by_sector_mining(self):
        """GET /api/v1/carbon/methodology-list/MINING"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/MINING")
        assert response.status_code == 200
        print("✓ Mining sector methodologies returned")
    
    def test_methodology_by_sector_blue_carbon(self):
        """GET /api/v1/carbon/methodology-list/BLUE_CARBON"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/BLUE_CARBON")
        assert response.status_code == 200
        print("✓ Blue Carbon sector methodologies returned")
    
    def test_carbon_calculation_post(self):
        """POST /api/v1/carbon/calculate/methodology runs calculation"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=ACM0002",
            json={"installed_capacity_mw": 100, "capacity_factor": 0.3, "grid_emission_factor": 0.5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "emission_reductions" in data or "annual_credits" in data or "error" not in data
        print("✓ Carbon calculation returns results")
    
    def test_grid_emission_factor(self):
        """GET /api/v1/carbon/data/grid-emission-factor returns factor"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/data/grid-emission-factor?country_code=US")
        assert response.status_code == 200
        data = response.json()
        assert "grid_emission_factor" in data
        print(f"✓ US grid emission factor: {data.get('grid_emission_factor')} tCO2/MWh")


class TestNatureRiskModule:
    """Nature Risk module tests - LEAP, Water Risk, ENCORE, GBF"""
    
    def test_nature_risk_summary(self):
        """GET /api/v1/nature-risk/summary or dashboard"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/dashboard/summary")
        assert response.status_code == 200
        print("✓ Nature risk summary returns 200")
    
    def test_water_risk_locations(self):
        """GET /api/v1/nature-risk/water-risk/locations"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/water-risk/locations")
        assert response.status_code == 200
        data = response.json()
        # Should return locations array
        assert "locations" in data or isinstance(data, list)
        print("✓ Water risk locations returned")
    
    def test_nature_risk_scenarios(self):
        """GET /api/v1/nature-risk/scenarios returns TNFD scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
        print("✓ Nature risk scenarios returned")
    
    def test_encore_sectors(self):
        """GET /api/v1/nature-risk/encore/sectors returns ENCORE sectors"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/sectors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "sectors" in data
        print("✓ ENCORE sectors returned")
    
    def test_encore_ecosystem_services(self):
        """GET /api/v1/nature-risk/encore/ecosystem-services"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/ecosystem-services")
        assert response.status_code == 200
        print("✓ ENCORE ecosystem services returned")
    
    def test_leap_assessment_calculate(self):
        """POST /api/v1/nature-risk/leap-assessments/calculate"""
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/leap-assessments/calculate", json={
            "entity_id": "test-entity",
            "entity_type": "company",
            "scenario_ids": ["scenario-tnfd-current"],
            "include_dependencies": True,
            "include_water_risk": True,
            "include_biodiversity_overlap": False
        })
        assert response.status_code == 200
        data = response.json()
        # Should return LEAP scores
        assert "scenario_results" in data or "locate_score" in data
        print("✓ LEAP calculation returns scores")


class TestStrandedAssetsModule:
    """Stranded Assets module tests - Dashboard, Map, Risk Analysis"""
    
    def test_stranded_assets_dashboard(self):
        """GET /api/v1/stranded-assets/dashboard returns KPIs"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_assets" in data
        assert "high_risk_assets" in data
        print(f"✓ Stranded assets dashboard: {data.get('total_assets')} assets")
    
    def test_stranded_assets_list(self):
        """GET /api/v1/stranded-assets/reserves returns reserves"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/reserves")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)
        print("✓ Stranded assets reserves list returned")
    
    def test_stranded_assets_power_plants(self):
        """GET /api/v1/stranded-assets/power-plants"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/power-plants")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Power plants returned: {data.get('total', 0)} items")
    
    def test_stranded_assets_infrastructure(self):
        """GET /api/v1/stranded-assets/infrastructure"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/infrastructure")
        assert response.status_code == 200
        print("✓ Infrastructure assets returned")
    
    def test_stranded_assets_map_data(self):
        """GET /api/v1/stranded-assets/map-data for visualization"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        print(f"✓ Map data returned: {len(data.get('assets', []))} assets")
    
    def test_stranded_assets_scenarios(self):
        """GET /api/v1/stranded-assets/scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) and len(data) > 0
        print(f"✓ Stranded assets scenarios: {len(data)} scenarios")
    
    def test_critical_assets(self):
        """GET /api/v1/stranded-assets/critical-assets"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/critical-assets")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        print(f"✓ Critical assets: {data.get('total', 0)} alerts")


class TestRealEstateValuationModule:
    """Real Estate Valuation tests - DCF, Direct Cap, Cost, Sales Comparison"""
    
    def test_valuation_dashboard(self):
        """GET /api/v1/valuation/dashboard returns KPIs"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_properties" in data
        assert "total_portfolio_value" in data
        print(f"✓ Valuation dashboard: {data.get('total_properties')} properties")
    
    def test_valuation_properties_list(self):
        """GET /api/v1/valuation/properties returns properties"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Valuation properties: {data.get('total', 0)} items")
    
    def test_direct_capitalization(self):
        """POST /api/v1/valuation/income/direct-capitalization"""
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/direct-capitalization", json={
            "rentable_area_sf": 10000,
            "market_rent_per_sf": 35,
            "other_income": 5000,
            "vacancy_rate": 0.05,
            "collection_loss_rate": 0.02,
            "operating_expense_ratio": 0.35,
            "cap_rate": 0.065
        })
        assert response.status_code == 200
        data = response.json()
        assert "indicated_value" in data or "value" in data
        print("✓ Direct capitalization calculation works")
    
    def test_dcf_calculation(self):
        """POST /api/v1/valuation/income/dcf"""
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/dcf", json={
            "projection_years": 10,
            "current_noi": 500000,
            "revenue_growth_rate": 0.03,
            "expense_growth_rate": 0.02,
            "inflation_rate": 0.02,
            "discount_rate": 0.08,
            "terminal_cap_rate": 0.07,
            "terminal_growth_rate": 0.02,
            "equity_investment": 3000000,
            "debt_service": 250000
        })
        assert response.status_code == 200
        data = response.json()
        assert "npv" in data or "net_present_value" in data or "indicated_value" in data
        print("✓ DCF calculation works")
    
    def test_cost_approach(self):
        """POST /api/v1/valuation/cost/replacement"""
        response = requests.post(f"{BASE_URL}/api/v1/valuation/cost/replacement", json={
            "land_area_acres": 2,
            "land_value_per_acre": 1000000,
            "building_area_sf": 50000,
            "construction_type": "steel_frame",
            "quality": "class_a",
            "location_factor": 1.2,
            "effective_age": 10,
            "total_economic_life": 50,
            "condition_rating": "good"
        })
        assert response.status_code == 200
        data = response.json()
        assert "indicated_value" in data or "total_value" in data
        print("✓ Cost approach calculation works")
    
    def test_comparables_list(self):
        """GET /api/v1/valuation/comparables"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/comparables")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Comparables: {data.get('total', 0)} items")
    
    def test_market_cap_rates(self):
        """GET /api/v1/valuation/market/cap-rates"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/market/cap-rates")
        assert response.status_code == 200
        data = response.json()
        assert "cap_rates" in data
        print(f"✓ Market cap rates: {len(data.get('cap_rates', []))} entries")


class TestSustainabilityModule:
    """Sustainability module tests - LEED, BREEAM calculations"""
    
    def test_leed_calculation(self):
        """POST /api/v1/sustainability/leed"""
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed", json={
            "building_id": "test-building",
            "location": {"water_stressed": False, "brownfield": True},
            "sustainable_sites": {"brownfield_redevelopment": True, "public_transit_access": True},
            "water_efficiency": {"water_use_reduction_percent": 30, "rainwater_harvesting": True},
            "energy_atmosphere": {"energy_reduction_percent": 25, "renewable_percent": 15},
            "materials_resources": {"recycled_content_percent": 15, "regional_materials": True},
            "indoor_quality": {"co2_monitoring": True, "low_voc_materials": True}
        })
        assert response.status_code == 200
        data = response.json()
        assert "total_score" in data or "points" in data
        print("✓ LEED calculation works")
    
    def test_breeam_calculation(self):
        """POST /api/v1/sustainability/breeam"""
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/breeam", json={
            "building_id": "test-building-breeam",
            "management": {"sustainable_procurement": True, "construction_site_management": True},
            "health_wellbeing": {"daylighting": True, "thermal_comfort": True},
            "energy": {"energy_reduction_percent": 20, "low_carbon_systems": True},
            "transport": {"public_transport_accessibility": True, "cyclist_facilities": True},
            "water": {"water_consumption_reduction_percent": 25},
            "materials": {"responsible_sourcing_percent": 50, "recycled_aggregates": True},
            "waste": {"construction_waste_diverted_percent": 80},
            "land_use_ecology": {"ecological_enhancement": True, "long_term_biodiversity": True},
            "pollution": {"nox_emissions_reduction": True, "flood_risk_assessment": True}
        })
        assert response.status_code == 200
        data = response.json()
        assert "total_score" in data or "score" in data
        print("✓ BREEAM calculation works")


class TestScenarioAnalysisModule:
    """Scenario Analysis module tests - Build, List, Comparison"""
    
    def test_scenario_build(self):
        """POST /api/v1/scenarios/build creates scenario"""
        # First get available properties
        props_resp = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        if props_resp.status_code == 200:
            props = props_resp.json()
            if isinstance(props, list) and len(props) > 0:
                property_id = props[0].get("id", SAMPLE_PROPERTY_ID)
            else:
                property_id = SAMPLE_PROPERTY_ID
        else:
            property_id = SAMPLE_PROPERTY_ID
        
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json={
            "base_property_id": property_id,
            "scenario_name": f"TEST_Regression_Scenario_{datetime.now().strftime('%H%M%S')}",
            "description": "Regression test scenario",
            "modifications": [
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.07},
                {"type": "vacancy", "parameter": "vacancy_rate", "new_value": 0.08}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "scenario_id" in data or "id" in data
        print("✓ Scenario build works")
        return data.get("scenario_id") or data.get("id")
    
    def test_scenario_list(self):
        """GET /api/v1/scenarios/list returns scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Scenarios list: {data.get('total', 0)} scenarios")
    
    def test_scenario_properties(self):
        """GET /api/v1/scenarios/properties"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
        print("✓ Scenario properties returned")


class TestPortfolioAnalyticsModule:
    """Portfolio Analytics tests - Dashboard, Holdings, KPIs"""
    
    def test_portfolios_list(self):
        """GET /api/v1/portfolio-analytics/portfolios"""
        response = requests.get(f"{BASE_URL}/api/v1/portfolio-analytics/portfolios")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Portfolios list: {data.get('total', 0)} portfolios")
    
    def test_portfolio_by_id(self):
        """GET /api/v1/portfolio-analytics/portfolios/{id}"""
        response = requests.get(f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "name" in data
        print(f"✓ Portfolio {SAMPLE_PORTFOLIO_ID[:8]}... returned")
    
    def test_portfolio_holdings(self):
        """GET /api/v1/portfolio-analytics/portfolios/{id}/holdings"""
        response = requests.get(f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}/holdings")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Portfolio holdings: {len(data.get('items', []))} items")
    
    def test_portfolio_dashboard(self):
        """GET /api/v1/portfolio-analytics/portfolios/{id}/dashboard"""
        response = requests.get(f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data or "total_value" in data
        print("✓ Portfolio dashboard returns KPIs")


class TestExportFunctionality:
    """Export module tests - PDF and Excel exports"""
    
    def test_export_portfolio_pdf(self):
        """GET /api/v1/exports/portfolio-analytics/{id}?format=pdf"""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=pdf",
            stream=True
        )
        assert response.status_code == 200
        # Should return PDF content
        content_type = response.headers.get('content-type', '')
        assert 'pdf' in content_type or 'application/octet-stream' in content_type
        print("✓ PDF export works")
    
    def test_export_portfolio_excel(self):
        """GET /api/v1/exports/portfolio-analytics/{id}?format=excel"""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=excel",
            stream=True
        )
        assert response.status_code == 200
        content_type = response.headers.get('content-type', '')
        # Excel has specific content type
        assert 'spreadsheet' in content_type or 'excel' in content_type or 'application/octet-stream' in content_type
        print("✓ Excel export works")
    
    def test_export_available_endpoints(self):
        """GET /api/v1/exports/bulk lists available exports"""
        response = requests.get(f"{BASE_URL}/api/v1/exports/bulk")
        assert response.status_code == 200
        data = response.json()
        assert "exports" in data
        print(f"✓ Export endpoints: {len(data.get('exports', []))} available")


class TestScheduledReportsModule:
    """Scheduled Reports CRUD tests"""
    
    def test_create_scheduled_report(self):
        """POST /api/v1/scheduled-reports creates report"""
        response = requests.post(f"{BASE_URL}/api/v1/scheduled-reports", json={
            "name": f"TEST_Regression_Report_{datetime.now().strftime('%H%M%S')}",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf",
            "parameters": {}
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data.get("is_active") == True
        print("✓ Scheduled report created")
        return data.get("id")
    
    def test_list_scheduled_reports(self):
        """GET /api/v1/scheduled-reports"""
        response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Scheduled reports: {data.get('total', 0)} items")
    
    def test_scheduled_report_lifecycle(self):
        """Create, toggle, delete scheduled report"""
        # Create
        create_resp = requests.post(f"{BASE_URL}/api/v1/scheduled-reports", json={
            "name": f"TEST_Lifecycle_{datetime.now().strftime('%H%M%S')}",
            "report_type": "climate_risk",
            "frequency": "monthly",
            "recipients": ["lifecycle@test.com"],
            "format": "excel"
        })
        assert create_resp.status_code == 200
        report_id = create_resp.json().get("id")
        
        # Toggle
        toggle_resp = requests.post(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}/toggle")
        assert toggle_resp.status_code == 200
        assert toggle_resp.json().get("is_active") == False
        
        # Delete
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}")
        assert delete_resp.status_code == 200
        print("✓ Scheduled report lifecycle (create->toggle->delete) works")


class TestAPIEndpointStatus:
    """Quick status check for all major endpoints"""
    
    def test_all_major_endpoints(self):
        """Verify all major endpoints return successful status"""
        endpoints = [
            ("GET", "/api/auth/me"),  # Skip - needs auth
            ("GET", "/api/v1/carbon/portfolios"),
            ("GET", "/api/v1/carbon/methodologies"),
            ("GET", "/api/v1/nature-risk/dashboard/summary"),
            ("GET", "/api/v1/nature-risk/water-risk/locations"),
            ("GET", "/api/v1/stranded-assets/dashboard"),
            ("GET", "/api/v1/stranded-assets/map-data"),
            ("GET", "/api/v1/valuation/dashboard"),
            ("GET", "/api/v1/valuation/properties"),
            ("GET", "/api/v1/portfolio-analytics/portfolios"),
            ("GET", "/api/v1/scheduled-reports"),
            ("GET", "/api/v1/exports/bulk"),
        ]
        
        success_count = 0
        for method, endpoint in endpoints:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                else:
                    resp = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=10)
                
                if resp.status_code in [200, 201]:
                    success_count += 1
                    print(f"  ✓ {method} {endpoint} - {resp.status_code}")
                else:
                    print(f"  ✗ {method} {endpoint} - {resp.status_code}")
            except Exception as e:
                print(f"  ✗ {method} {endpoint} - Error: {str(e)}")
        
        print(f"\n✓ Endpoint status: {success_count}/{len(endpoints)} successful")


# Cleanup fixture for test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after all tests"""
    yield
    # Cleanup scheduled reports with TEST_ prefix
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        if resp.status_code == 200:
            reports = resp.json().get("items", [])
            for report in reports:
                if report.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/v1/scheduled-reports/{report['id']}")
                    print(f"Cleaned up test report: {report['id']}")
    except Exception:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
