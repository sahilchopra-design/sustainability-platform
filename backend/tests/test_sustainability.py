"""
Backend tests for Sustainability Frameworks Integration Module
Tests GRESB, LEED, BREEAM, and Value Impact analysis APIs
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSustainabilityDashboard:
    """Dashboard KPI endpoint tests"""
    
    def test_dashboard_returns_200(self):
        """Dashboard endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/dashboard")
        assert response.status_code == 200
        print("✓ Dashboard endpoint returns 200")
    
    def test_dashboard_has_required_kpis(self):
        """Dashboard has all required KPI fields"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            'total_certified_properties', 'total_uncertified_properties',
            'certification_coverage_percent', 'by_certification_type', 'by_level',
            'total_certified_value', 'avg_value_premium_captured', 'potential_value_uplift',
            'avg_gresb_score', 'avg_leed_points', 'certifications_this_year',
            'certifications_expiring_soon'
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print("✓ Dashboard has all required KPI fields")
    
    def test_dashboard_kpi_values_valid(self):
        """Dashboard KPI values are valid"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/dashboard")
        data = response.json()
        
        assert data['total_certified_properties'] >= 0
        assert data['total_uncertified_properties'] >= 0
        assert float(data['certification_coverage_percent']) >= 0
        assert float(data['total_certified_value']) >= 0
        print("✓ Dashboard KPI values are valid")


class TestCertificationsList:
    """Certifications list endpoint tests"""
    
    def test_certifications_returns_200(self):
        """Certifications endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/certifications")
        assert response.status_code == 200
        print("✓ Certifications endpoint returns 200")
    
    def test_certifications_returns_sample_data(self):
        """Certifications returns 5 sample properties"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/certifications")
        data = response.json()
        
        assert 'items' in data
        assert 'total' in data
        assert data['total'] == 5
        assert len(data['items']) == 5
        print("✓ Certifications returns 5 sample properties")
    
    def test_certifications_have_required_fields(self):
        """Each certification has required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/certifications")
        data = response.json()
        
        required_fields = [
            'id', 'certification_type', 'property_name', 'property_sector',
            'certification_level', 'score', 'value_premium_percent'
        ]
        
        for cert in data['items']:
            for field in required_fields:
                assert field in cert, f"Missing field: {field}"
        print("✓ All certifications have required fields")
    
    def test_certifications_filter_by_type(self):
        """Certifications can be filtered by type"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/certifications?certification_type=leed")
        data = response.json()
        
        assert response.status_code == 200
        for cert in data['items']:
            assert cert['certification_type'] == 'leed'
        print("✓ Certifications filter by type works")


class TestGRESBAssessment:
    """GRESB Assessment endpoint tests"""
    
    def test_gresb_assess_returns_200(self):
        """GRESB assessment endpoint returns 200"""
        payload = {
            "portfolio_name": "TEST_Portfolio",
            "entity_type": "standing_investments",
            "region": "north_america",
            "total_aum": 2500000000,
            "num_assets": 25,
            "component_scores": {
                "management": 20,
                "policy": 8,
                "risk_management": 10,
                "stakeholder_engagement": 10,
                "performance_indicators": 22
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/gresb/assess", json=payload)
        assert response.status_code == 200
        print("✓ GRESB assessment returns 200")
    
    def test_gresb_calculates_correct_score(self):
        """GRESB calculates correct total score"""
        payload = {
            "portfolio_name": "TEST_Portfolio",
            "entity_type": "standing_investments",
            "region": "north_america",
            "total_aum": 2500000000,
            "num_assets": 25,
            "component_scores": {
                "management": 20,
                "policy": 8,
                "risk_management": 10,
                "stakeholder_engagement": 10,
                "performance_indicators": 22
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/gresb/assess", json=payload)
        data = response.json()
        
        expected_score = 20 + 8 + 10 + 10 + 22  # 70
        assert int(data['total_score']) == expected_score
        print(f"✓ GRESB calculates correct score: {data['total_score']}")
    
    def test_gresb_returns_star_rating(self):
        """GRESB returns star rating"""
        payload = {
            "portfolio_name": "TEST_Portfolio",
            "entity_type": "standing_investments",
            "region": "north_america",
            "total_aum": 2500000000,
            "num_assets": 25,
            "component_scores": {
                "management": 20,
                "policy": 8,
                "risk_management": 10,
                "stakeholder_engagement": 10,
                "performance_indicators": 22
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/gresb/assess", json=payload)
        data = response.json()
        
        assert 'star_rating' in data
        assert data['star_rating'] in ['1_star', '2_star', '3_star', '4_star', '5_star']
        # Score 70 should be 4_star (60-79 range)
        assert data['star_rating'] == '4_star'
        print(f"✓ GRESB returns star rating: {data['star_rating']}")
    
    def test_gresb_returns_value_impact(self):
        """GRESB returns value impact metrics"""
        payload = {
            "portfolio_name": "TEST_Portfolio",
            "entity_type": "standing_investments",
            "region": "north_america",
            "total_aum": 2500000000,
            "num_assets": 25,
            "component_scores": {
                "management": 20,
                "policy": 8,
                "risk_management": 10,
                "stakeholder_engagement": 10,
                "performance_indicators": 22
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/gresb/assess", json=payload)
        data = response.json()
        
        assert 'estimated_rent_premium_percent' in data
        assert 'estimated_value_premium_percent' in data
        assert 'estimated_value_impact' in data
        assert float(data['estimated_value_impact']) > 0
        print(f"✓ GRESB returns value impact: ${float(data['estimated_value_impact']):,.0f}")
    
    def test_gresb_returns_benchmark(self):
        """GRESB returns benchmark comparison"""
        payload = {
            "portfolio_name": "TEST_Portfolio",
            "entity_type": "standing_investments",
            "region": "north_america",
            "total_aum": 2500000000,
            "num_assets": 25,
            "component_scores": {
                "management": 20,
                "policy": 8,
                "risk_management": 10,
                "stakeholder_engagement": 10,
                "performance_indicators": 22
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/gresb/assess", json=payload)
        data = response.json()
        
        assert 'benchmark' in data
        assert 'percentile_rank' in data
        assert data['benchmark']['peer_group'] is not None
        print(f"✓ GRESB returns benchmark: {data['percentile_rank']}th percentile")
    
    def test_gresb_returns_recommendations(self):
        """GRESB returns improvement recommendations"""
        payload = {
            "portfolio_name": "TEST_Portfolio",
            "entity_type": "standing_investments",
            "region": "north_america",
            "total_aum": 2500000000,
            "num_assets": 25,
            "component_scores": {
                "management": 15,
                "policy": 5,
                "risk_management": 7,
                "stakeholder_engagement": 7,
                "performance_indicators": 15
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/gresb/assess", json=payload)
        data = response.json()
        
        assert 'improvement_recommendations' in data
        assert len(data['improvement_recommendations']) > 0
        print(f"✓ GRESB returns {len(data['improvement_recommendations'])} recommendations")


class TestLEEDAssessment:
    """LEED Assessment endpoint tests"""
    
    def test_leed_assess_returns_200(self):
        """LEED assessment endpoint returns 200"""
        payload = {
            "property_name": "TEST_Office Building",
            "property_sector": "office",
            "region": "north_america",
            "leed_version": "v4.1",
            "gross_floor_area_m2": 50000,
            "current_value": 100000000,
            "category_scores": {
                "integrative_process": 1,
                "location_transportation": 10,
                "sustainable_sites": 7,
                "water_efficiency": 8,
                "energy_atmosphere": 20,
                "materials_resources": 8,
                "indoor_environmental_quality": 10,
                "innovation": 4,
                "regional_priority": 3
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        assert response.status_code == 200
        print("✓ LEED assessment returns 200")
    
    def test_leed_calculates_correct_points(self):
        """LEED calculates correct total points"""
        payload = {
            "property_name": "TEST_Office Building",
            "property_sector": "office",
            "region": "north_america",
            "gross_floor_area_m2": 50000,
            "category_scores": {
                "integrative_process": 1,
                "location_transportation": 10,
                "sustainable_sites": 7,
                "water_efficiency": 8,
                "energy_atmosphere": 20,
                "materials_resources": 8,
                "indoor_environmental_quality": 10,
                "innovation": 4,
                "regional_priority": 3
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        data = response.json()
        
        expected_points = 1 + 10 + 7 + 8 + 20 + 8 + 10 + 4 + 3  # 71
        assert data['total_points'] == expected_points
        print(f"✓ LEED calculates correct points: {data['total_points']}")
    
    def test_leed_returns_certification_level(self):
        """LEED returns correct certification level"""
        payload = {
            "property_name": "TEST_Office Building",
            "property_sector": "office",
            "region": "north_america",
            "gross_floor_area_m2": 50000,
            "category_scores": {
                "integrative_process": 1,
                "location_transportation": 10,
                "sustainable_sites": 7,
                "water_efficiency": 8,
                "energy_atmosphere": 20,
                "materials_resources": 8,
                "indoor_environmental_quality": 10,
                "innovation": 4,
                "regional_priority": 3
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        data = response.json()
        
        assert 'certification_level' in data
        assert data['certification_level'] in ['certified', 'silver', 'gold', 'platinum']
        # 71 points should be Gold (60-79)
        assert data['certification_level'] == 'gold'
        print(f"✓ LEED returns certification level: {data['certification_level']}")
    
    def test_leed_returns_value_impact(self):
        """LEED returns value impact metrics"""
        payload = {
            "property_name": "TEST_Office Building",
            "property_sector": "office",
            "region": "north_america",
            "gross_floor_area_m2": 50000,
            "current_value": 100000000,
            "category_scores": {
                "integrative_process": 1,
                "location_transportation": 10,
                "sustainable_sites": 7,
                "water_efficiency": 8,
                "energy_atmosphere": 20,
                "materials_resources": 8,
                "indoor_environmental_quality": 10,
                "innovation": 4,
                "regional_priority": 3
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        data = response.json()
        
        assert 'estimated_rent_premium_percent' in data
        assert 'estimated_value_premium_percent' in data
        assert 'estimated_value_impact' in data
        assert float(data['estimated_value_impact']) > 0
        print(f"✓ LEED returns value impact: ${float(data['estimated_value_impact']):,.0f}")
    
    def test_leed_returns_category_analysis(self):
        """LEED returns category performance analysis"""
        payload = {
            "property_name": "TEST_Office Building",
            "property_sector": "office",
            "region": "north_america",
            "gross_floor_area_m2": 50000,
            "category_scores": {
                "integrative_process": 1,
                "location_transportation": 10,
                "sustainable_sites": 7,
                "water_efficiency": 8,
                "energy_atmosphere": 20,
                "materials_resources": 8,
                "indoor_environmental_quality": 10,
                "innovation": 4,
                "regional_priority": 3
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        data = response.json()
        
        assert 'strongest_categories' in data
        assert 'weakest_categories' in data
        assert 'improvement_potential' in data
        print(f"✓ LEED returns category analysis: {len(data['strongest_categories'])} strongest categories")


class TestValueImpact:
    """Value Impact calculation endpoint tests"""
    
    def test_value_impact_returns_200(self):
        """Value Impact endpoint returns 200"""
        payload = {
            "certification_type": "leed",
            "certification_level": "gold",
            "property_sector": "office",
            "region": "north_america",
            "current_value": 100000000
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        assert response.status_code == 200
        print("✓ Value Impact endpoint returns 200")
    
    def test_value_impact_returns_premiums(self):
        """Value Impact returns rent and value premiums"""
        payload = {
            "certification_type": "leed",
            "certification_level": "gold",
            "property_sector": "office",
            "region": "north_america",
            "current_value": 100000000
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        data = response.json()
        
        assert 'rent_premium_percent' in data
        assert 'value_premium_percent' in data
        assert 'rent_premium_range' in data
        assert 'value_premium_range' in data
        assert float(data['rent_premium_percent']) > 0
        assert float(data['value_premium_percent']) > 0
        print(f"✓ Value Impact returns premiums: Rent +{data['rent_premium_percent']}%, Value +{data['value_premium_percent']}%")
    
    def test_value_impact_returns_value_increase(self):
        """Value Impact returns estimated value increase"""
        payload = {
            "certification_type": "leed",
            "certification_level": "gold",
            "property_sector": "office",
            "region": "north_america",
            "current_value": 100000000
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        data = response.json()
        
        assert 'estimated_value_increase' in data
        value_increase = float(data['estimated_value_increase'])
        assert value_increase > 0
        
        # Verify calculation: value_increase = current_value * (value_premium_percent / 100)
        expected = 100000000 * (float(data['value_premium_percent']) / 100)
        assert abs(value_increase - expected) < 1  # Allow small rounding error
        print(f"✓ Value Impact returns value increase: ${value_increase:,.0f}")
    
    def test_value_impact_returns_cap_rate_compression(self):
        """Value Impact returns cap rate compression"""
        payload = {
            "certification_type": "leed",
            "certification_level": "gold",
            "property_sector": "office",
            "region": "north_america",
            "current_value": 100000000
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        data = response.json()
        
        assert 'cap_rate_compression_bps' in data
        assert int(data['cap_rate_compression_bps']) >= 0
        print(f"✓ Value Impact returns cap rate compression: {data['cap_rate_compression_bps']} bps")
    
    def test_value_impact_returns_operating_savings(self):
        """Value Impact returns operating cost savings"""
        payload = {
            "certification_type": "leed",
            "certification_level": "gold",
            "property_sector": "office",
            "region": "north_america",
            "current_value": 100000000,
            "current_noi": 5000000
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        data = response.json()
        
        assert 'estimated_operating_cost_savings_percent' in data
        assert float(data['estimated_operating_cost_savings_percent']) > 0
        print(f"✓ Value Impact returns operating savings: {data['estimated_operating_cost_savings_percent']}%")
    
    def test_value_impact_returns_sources(self):
        """Value Impact returns research sources"""
        payload = {
            "certification_type": "leed",
            "certification_level": "gold",
            "property_sector": "office",
            "region": "north_america",
            "current_value": 100000000
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        data = response.json()
        
        assert 'source_studies' in data
        assert len(data['source_studies']) > 0
        assert 'data_reliability' in data
        print(f"✓ Value Impact returns {len(data['source_studies'])} research sources")
    
    def test_value_impact_with_rent_details(self):
        """Value Impact with rent details returns rent premium PSF"""
        payload = {
            "certification_type": "leed",
            "certification_level": "gold",
            "property_sector": "office",
            "region": "north_america",
            "current_value": 100000000,
            "gross_floor_area_sf": 450000,
            "current_rent_psf": 35
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        data = response.json()
        
        assert 'estimated_rent_premium_psf' in data
        assert 'estimated_annual_rent_increase' in data
        assert float(data['estimated_rent_premium_psf']) > 0
        print(f"✓ Value Impact returns rent premium PSF: ${data['estimated_rent_premium_psf']}/SF")
    
    def test_value_impact_breeam_certification(self):
        """Value Impact works for BREEAM certification"""
        payload = {
            "certification_type": "breeam",
            "certification_level": "excellent",
            "property_sector": "office",
            "region": "europe",
            "current_value": 100000000
        }
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/value-impact", json=payload)
        data = response.json()
        
        assert response.status_code == 200
        assert data['certification_type'] == 'breeam'
        assert data['certification_level'] == 'excellent'
        assert float(data['estimated_value_increase']) > 0
        print(f"✓ BREEAM Value Impact: +{data['value_premium_percent']}% value premium")


class TestGRESBBenchmarks:
    """GRESB Benchmarks endpoint tests"""
    
    def test_benchmarks_returns_200(self):
        """GRESB benchmarks endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/gresb/benchmarks")
        assert response.status_code == 200
        print("✓ GRESB benchmarks returns 200")
    
    def test_benchmarks_has_regions(self):
        """GRESB benchmarks has benchmark data"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/gresb/benchmarks")
        data = response.json()
        
        assert 'benchmarks' in data
        assert len(data['benchmarks']) > 0
        print(f"✓ GRESB benchmarks has {len(data['benchmarks'])} regions")


class TestLEEDThresholds:
    """LEED Thresholds endpoint tests"""
    
    def test_thresholds_returns_200(self):
        """LEED thresholds endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/leed/thresholds")
        assert response.status_code == 200
        print("✓ LEED thresholds returns 200")
    
    def test_thresholds_has_levels(self):
        """LEED thresholds has all certification levels"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/leed/thresholds")
        data = response.json()
        
        assert 'levels' in data
        for level in ['certified', 'silver', 'gold', 'platinum']:
            assert level in data['levels']
        print("✓ LEED thresholds has all levels")


class TestEnums:
    """Enums endpoint tests"""
    
    def test_enums_returns_200(self):
        """Enums endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/enums")
        assert response.status_code == 200
        print("✓ Enums endpoint returns 200")
    
    def test_enums_has_all_types(self):
        """Enums has all certification types"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/enums")
        data = response.json()
        
        assert 'certification_types' in data
        assert 'leed_levels' in data
        assert 'breeam_levels' in data
        assert 'gresb_ratings' in data
        assert 'property_sectors' in data
        assert 'regions' in data
        print("✓ Enums has all required types")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
