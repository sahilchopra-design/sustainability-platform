"""
Nature Risk Module Backend Tests
Tests for TNFD LEAP methodology APIs including:
- Dashboard summary
- Scenarios (list, get)
- ENCORE dependencies
- Water risk locations and analysis
- Biodiversity sites
- Portfolio analysis
- GBF alignment
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNatureRiskDashboard:
    """Dashboard API Tests"""
    
    def test_dashboard_summary_returns_200(self):
        """Test dashboard summary endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/dashboard/summary")
        assert response.status_code == 200
        print("✓ Dashboard summary returns 200")
    
    def test_dashboard_summary_has_required_fields(self):
        """Test dashboard summary has all required KPI fields"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/dashboard/summary")
        data = response.json()
        
        # Verify required fields exist
        assert "total_assessments" in data
        assert "high_risk_entities" in data
        assert "water_risk_exposure" in data
        assert "biodiversity_overlaps" in data
        assert "gbf_alignment" in data
        assert "sector_breakdown" in data
        assert "trend_data" in data
        
        # Verify data types
        assert isinstance(data["total_assessments"], int)
        assert isinstance(data["high_risk_entities"], int)
        assert isinstance(data["water_risk_exposure"], dict)
        assert isinstance(data["sector_breakdown"], dict)
        print("✓ Dashboard summary has all required fields")
    
    def test_dashboard_water_risk_exposure_structure(self):
        """Test water risk exposure has correct structure"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/dashboard/summary")
        data = response.json()
        
        water_risk = data["water_risk_exposure"]
        assert "high_stress_locations" in water_risk
        assert "total_locations" in water_risk
        assert "avg_water_stress" in water_risk
        print("✓ Water risk exposure structure is correct")
    
    def test_dashboard_gbf_alignment_structure(self):
        """Test GBF alignment has correct structure"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/dashboard/summary")
        data = response.json()
        
        gbf = data["gbf_alignment"]
        assert "aligned_targets" in gbf
        assert "partial_targets" in gbf
        assert "not_aligned_targets" in gbf
        assert "total_targets" in gbf
        assert gbf["total_targets"] == 23  # GBF has 23 targets
        print("✓ GBF alignment structure is correct")


class TestNatureRiskScenarios:
    """Scenarios API Tests"""
    
    def test_list_scenarios_returns_200(self):
        """Test listing scenarios returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios")
        assert response.status_code == 200
        print("✓ List scenarios returns 200")
    
    def test_list_scenarios_returns_array(self):
        """Test scenarios endpoint returns array with data"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios")
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"✓ List scenarios returns array with {len(data)} scenarios")
    
    def test_scenario_has_required_fields(self):
        """Test each scenario has required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios")
        data = response.json()
        
        for scenario in data:
            assert "id" in scenario
            assert "name" in scenario
            assert "scenario_type" in scenario
            assert "framework" in scenario
        print("✓ All scenarios have required fields")
    
    def test_get_specific_scenario(self):
        """Test getting a specific scenario by ID"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios/scenario-tnfd-current")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "scenario-tnfd-current"
        assert data["name"] == "TNFD Current Trajectory"
        assert data["framework"] == "TNFD"
        print("✓ Get specific scenario works correctly")
    
    def test_get_nonexistent_scenario_returns_404(self):
        """Test getting nonexistent scenario returns 404"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/scenarios/nonexistent-id")
        assert response.status_code == 404
        print("✓ Nonexistent scenario returns 404")


class TestENCOREDependencies:
    """ENCORE Dependency API Tests"""
    
    def test_list_encore_sectors_returns_200(self):
        """Test listing ENCORE sectors returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/sectors")
        assert response.status_code == 200
        print("✓ List ENCORE sectors returns 200")
    
    def test_encore_sectors_has_expected_sectors(self):
        """Test ENCORE sectors contains expected sectors"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/sectors")
        data = response.json()
        
        sector_codes = [s["code"] for s in data]
        assert "ENERGY" in sector_codes
        assert "MINING" in sector_codes
        assert "AGRICULTURE" in sector_codes
        assert "FINANCE" in sector_codes
        assert len(data) >= 10
        print(f"✓ ENCORE sectors has {len(data)} sectors including expected ones")
    
    def test_get_encore_dependencies_by_sector(self):
        """Test getting ENCORE dependencies for a specific sector"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/dependencies?sector_code=ENERGY")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify dependency structure
        for dep in data:
            assert "ecosystem_service" in dep
            assert "dependency_score" in dep
        print(f"✓ ENCORE dependencies for ENERGY sector: {len(data)} dependencies")
    
    def test_list_ecosystem_services(self):
        """Test listing ecosystem services"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/encore/ecosystem-services")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        
        # Verify water service exists
        service_ids = [s["id"] for s in data]
        assert "water" in service_ids
        print(f"✓ Ecosystem services list has {len(data)} services")


class TestWaterRiskLocations:
    """Water Risk Location API Tests"""
    
    def test_list_water_risk_locations_returns_200(self):
        """Test listing water risk locations returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/water-risk/locations")
        assert response.status_code == 200
        print("✓ List water risk locations returns 200")
    
    def test_water_risk_locations_returns_10_locations(self):
        """Test water risk locations returns expected 10 locations"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/water-risk/locations")
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 10
        print("✓ Water risk locations returns 10 locations")
    
    def test_water_risk_location_has_required_fields(self):
        """Test water risk location has all required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/water-risk/locations")
        data = response.json()
        
        for loc in data:
            assert "id" in loc
            assert "location_name" in loc
            assert "country_code" in loc
            assert "baseline_water_stress" in loc
            assert "basin_name" in loc
        print("✓ All water risk locations have required fields")
    
    def test_get_water_risk_report_for_location(self):
        """Test getting water risk report for a specific location"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/water-risk/locations/water-loc-001/risk-report")
        assert response.status_code == 200
        
        data = response.json()
        assert "baseline_risk_score" in data
        assert "baseline_risk_level" in data
        assert "projected_risk_scores" in data
        assert "recommendations" in data
        assert "indicators" in data
        
        # Check projections exist
        assert "2030" in data["projected_risk_scores"] or 2030 in data["projected_risk_scores"]
        print("✓ Water risk report for location has correct structure")
    
    def test_water_risk_report_nonexistent_location_returns_404(self):
        """Test getting report for nonexistent location returns 404"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/water-risk/locations/nonexistent-id/risk-report")
        assert response.status_code == 404
        print("✓ Nonexistent water risk location returns 404")
    
    def test_water_risk_analysis_post(self):
        """Test water risk analysis POST endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/nature-risk/water-risk/analyze",
            json={
                "location_ids": ["water-loc-001", "water-loc-002"],
                "scenario_ids": ["scenario-tnfd-current"],
                "include_projections": True
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "analysis_date" in data
        assert "location_count" in data
        assert "results" in data
        print("✓ Water risk analysis POST works correctly")


class TestBiodiversitySites:
    """Biodiversity Sites API Tests"""
    
    def test_list_biodiversity_sites_returns_200(self):
        """Test listing biodiversity sites returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/biodiversity/sites")
        assert response.status_code == 200
        print("✓ List biodiversity sites returns 200")
    
    def test_biodiversity_sites_returns_17_sites(self):
        """Test biodiversity sites returns expected 17 sites"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/biodiversity/sites")
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 17
        print("✓ Biodiversity sites returns 17 sites")
    
    def test_biodiversity_site_has_required_fields(self):
        """Test biodiversity site has all required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/biodiversity/sites")
        data = response.json()
        
        for site in data:
            assert "id" in site
            assert "site_name" in site
            assert "site_type" in site
            assert "country_code" in site
        print("✓ All biodiversity sites have required fields")
    
    def test_biodiversity_sites_has_various_types(self):
        """Test biodiversity sites includes various site types"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/biodiversity/sites")
        data = response.json()
        
        site_types = set(s["site_type"] for s in data)
        assert "world_heritage" in site_types
        assert "ramsar" in site_types
        assert "key_biodiversity_area" in site_types
        assert "protected_area" in site_types
        print(f"✓ Biodiversity sites has {len(site_types)} different site types")
    
    def test_biodiversity_filter_by_site_type(self):
        """Test filtering biodiversity sites by site type"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/biodiversity/sites?site_type=world_heritage")
        assert response.status_code == 200
        
        data = response.json()
        for site in data:
            assert site["site_type"] == "world_heritage"
        print("✓ Biodiversity sites filter by type works")


class TestPortfolioNatureRisk:
    """Portfolio Nature Risk API Tests"""
    
    def test_portfolio_analysis_returns_200(self):
        """Test portfolio analysis returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/v1/nature-risk/portfolio/analyze",
            json={
                "portfolio_id": "test-portfolio",
                "scenario_ids": ["scenario-tnfd-current"],
                "include_collateral_impact": True
            }
        )
        assert response.status_code == 200
        print("✓ Portfolio analysis returns 200")
    
    def test_portfolio_analysis_has_required_fields(self):
        """Test portfolio analysis response has all required fields"""
        response = requests.post(
            f"{BASE_URL}/api/v1/nature-risk/portfolio/analyze",
            json={
                "portfolio_id": "test-portfolio",
                "scenario_ids": ["scenario-tnfd-current"],
                "include_collateral_impact": True
            }
        )
        data = response.json()
        
        assert "portfolio_id" in data
        assert "holding_count" in data
        assert "aggregate_metrics" in data
        assert "holding_results" in data
        print("✓ Portfolio analysis has all required fields")
    
    def test_portfolio_analysis_aggregate_metrics(self):
        """Test portfolio analysis aggregate metrics structure"""
        response = requests.post(
            f"{BASE_URL}/api/v1/nature-risk/portfolio/analyze",
            json={
                "portfolio_id": "test-portfolio",
                "scenario_ids": ["scenario-tnfd-current"],
                "include_collateral_impact": True
            }
        )
        data = response.json()
        
        metrics = data["aggregate_metrics"]
        assert "average_leap_score" in metrics
        assert "avg_locate_score" in metrics
        assert "avg_evaluate_score" in metrics
        assert "avg_assess_score" in metrics
        assert "avg_prepare_score" in metrics
        assert "high_risk_count" in metrics
        assert "total_exposure_at_risk_usd" in metrics
        print("✓ Portfolio aggregate metrics structure is correct")
    
    def test_portfolio_analysis_holding_results(self):
        """Test portfolio analysis holding results structure"""
        response = requests.post(
            f"{BASE_URL}/api/v1/nature-risk/portfolio/analyze",
            json={
                "portfolio_id": "test-portfolio",
                "scenario_ids": ["scenario-tnfd-current"],
                "include_collateral_impact": True
            }
        )
        data = response.json()
        
        assert len(data["holding_results"]) > 0
        
        for holding in data["holding_results"]:
            assert "entity_name" in holding
            assert "sector" in holding
            assert "leap_scores" in holding
            assert "risk_rating" in holding
            assert "financial_impact" in holding
        print(f"✓ Portfolio has {len(data['holding_results'])} holding results with correct structure")
    
    def test_portfolio_nature_exposure(self):
        """Test getting portfolio nature exposure"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/portfolio/test-portfolio/nature-exposure")
        assert response.status_code == 200
        
        data = response.json()
        assert "portfolio_id" in data
        assert "total_exposure_usd" in data
        assert "sector_breakdown" in data
        print("✓ Portfolio nature exposure endpoint works")


class TestGBFAlignment:
    """GBF Alignment API Tests"""
    
    def test_list_gbf_targets_returns_200(self):
        """Test listing GBF targets returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/gbf-targets")
        assert response.status_code == 200
        print("✓ List GBF targets returns 200")
    
    def test_gbf_targets_returns_23_targets(self):
        """Test GBF targets returns expected 23 targets"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/gbf-targets")
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 23
        print("✓ GBF targets returns 23 targets")
    
    def test_gbf_target_has_required_fields(self):
        """Test each GBF target has required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/gbf-targets")
        data = response.json()
        
        for target in data:
            assert "number" in target
            assert "description" in target
            assert "category" in target
        print("✓ All GBF targets have required fields")
    
    def test_gbf_alignment_for_entity(self):
        """Test getting GBF alignment for an entity"""
        response = requests.get(f"{BASE_URL}/api/v1/nature-risk/gbf-alignment/portfolio/demo-portfolio")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        for alignment in data:
            assert "target_number" in alignment
            assert "alignment_status" in alignment
            assert "alignment_score" in alignment
        print("✓ GBF alignment for entity works correctly")


class TestLEAPAssessment:
    """LEAP Assessment API Tests"""
    
    def test_calculate_leap_assessment(self):
        """Test calculating LEAP assessment"""
        response = requests.post(
            f"{BASE_URL}/api/v1/nature-risk/leap-assessments/calculate",
            json={
                "entity_id": "test-entity",
                "entity_type": "company",
                "scenario_ids": ["scenario-tnfd-current"],
                "include_dependencies": True,
                "include_water_risk": True,
                "include_biodiversity_overlap": True
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "entity_id" in data
        assert "scenario_results" in data
        assert len(data["scenario_results"]) > 0
        
        result = data["scenario_results"][0]
        assert "locate_score" in result
        assert "evaluate_score" in result
        assert "assess_score" in result
        assert "prepare_score" in result
        assert "overall_score" in result
        assert "overall_risk_rating" in result
        print("✓ LEAP assessment calculation works correctly")


class TestDataImport:
    """Data Import API Tests"""
    
    def test_import_encore_data(self):
        """Test importing ENCORE data"""
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/import/encore-data")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "sectors_imported" in data
        assert "dependencies_imported" in data
        print("✓ ENCORE data import works correctly")
    
    def test_import_biodiversity_sites(self):
        """Test importing biodiversity sites"""
        response = requests.post(f"{BASE_URL}/api/v1/nature-risk/import/biodiversity-sites")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "sites_imported" in data
        print("✓ Biodiversity sites import works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
