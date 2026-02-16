"""
Test BREEAM Calculator and Export APIs

Tests:
1. BREEAM Assessment endpoint (POST /api/v1/sustainability/breeam/assess)
2. LEED Assessment endpoint for comparison (POST /api/v1/sustainability/leed/assess)
3. Sustainability Export PDF endpoint
4. Sustainability Export Excel endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBREEAMAssessment:
    """Test BREEAM certification assessment endpoint"""
    
    def test_breeam_assess_returns_200(self):
        """Test that BREEAM assessment endpoint returns 200"""
        payload = {
            "property_name": "TEST_BREEAM_Property",
            "property_sector": "office",
            "region": "europe",
            "breeam_scheme": "new_construction",
            "category_scores": {
                "management": 50,
                "health_wellbeing": 50,
                "energy": 50,
                "transport": 50,
                "water": 50,
                "materials": 50,
                "waste": 50,
                "land_use_ecology": 50,
                "pollution": 50,
                "innovation": 50
            },
            "weights": {
                "management": 0.12,
                "health_wellbeing": 0.15,
                "energy": 0.19,
                "transport": 0.08,
                "water": 0.06,
                "materials": 0.125,
                "waste": 0.075,
                "land_use_ecology": 0.10,
                "pollution": 0.10,
                "innovation": 0.10
            },
            "gross_floor_area_m2": 5000,
            "year_built": 2020,
            "current_value": 50000000
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/breeam/assess", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_breeam_assess_returns_weighted_score(self):
        """Test that BREEAM assessment returns weighted score"""
        payload = {
            "property_name": "TEST_BREEAM_Property_Score",
            "property_sector": "office",
            "region": "europe",
            "breeam_scheme": "new_construction",
            "category_scores": {
                "management": 70,
                "health_wellbeing": 65,
                "energy": 60,
                "transport": 55,
                "water": 50,
                "materials": 60,
                "waste": 55,
                "land_use_ecology": 50,
                "pollution": 45,
                "innovation": 70
            },
            "weights": {
                "management": 0.12,
                "health_wellbeing": 0.15,
                "energy": 0.19,
                "transport": 0.08,
                "water": 0.06,
                "materials": 0.125,
                "waste": 0.075,
                "land_use_ecology": 0.10,
                "pollution": 0.10,
                "innovation": 0.10
            },
            "gross_floor_area_m2": 10000,
            "year_built": 2015,
            "current_value": 100000000
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/breeam/assess", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Check weighted_score is returned
        assert "weighted_score" in data, "Response should contain weighted_score"
        weighted_score = float(data["weighted_score"])
        assert 0 <= weighted_score <= 100, f"Weighted score {weighted_score} should be 0-100"
        
    def test_breeam_assess_returns_rating(self):
        """Test that BREEAM assessment returns rating level"""
        payload = {
            "property_name": "TEST_BREEAM_Rating",
            "property_sector": "retail",
            "region": "europe",
            "breeam_scheme": "new_construction",
            "category_scores": {
                "management": 85,
                "health_wellbeing": 80,
                "energy": 85,
                "transport": 75,
                "water": 70,
                "materials": 80,
                "waste": 75,
                "land_use_ecology": 70,
                "pollution": 65,
                "innovation": 90
            },
            "weights": {
                "management": 0.12,
                "health_wellbeing": 0.15,
                "energy": 0.19,
                "transport": 0.08,
                "water": 0.06,
                "materials": 0.125,
                "waste": 0.075,
                "land_use_ecology": 0.10,
                "pollution": 0.10,
                "innovation": 0.10
            },
            "gross_floor_area_m2": 8000,
            "year_built": 2022,
            "current_value": 75000000
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/breeam/assess", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Check rating is returned
        assert "rating" in data, "Response should contain rating"
        valid_ratings = ["pass", "good", "very_good", "excellent", "outstanding", "unclassified"]
        assert data["rating"] in valid_ratings, f"Rating {data['rating']} should be a valid BREEAM rating"
        
    def test_breeam_assess_returns_value_impact(self):
        """Test that BREEAM assessment returns value impact estimates"""
        payload = {
            "property_name": "TEST_BREEAM_Value",
            "property_sector": "office",
            "region": "europe",
            "breeam_scheme": "new_construction",
            "category_scores": {
                "management": 60,
                "health_wellbeing": 60,
                "energy": 60,
                "transport": 60,
                "water": 60,
                "materials": 60,
                "waste": 60,
                "land_use_ecology": 60,
                "pollution": 60,
                "innovation": 60
            },
            "weights": {
                "management": 0.12,
                "health_wellbeing": 0.15,
                "energy": 0.19,
                "transport": 0.08,
                "water": 0.06,
                "materials": 0.125,
                "waste": 0.075,
                "land_use_ecology": 0.10,
                "pollution": 0.10,
                "innovation": 0.10
            },
            "gross_floor_area_m2": 5000,
            "year_built": 2020,
            "current_value": 50000000
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/breeam/assess", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Check value impact fields
        assert "estimated_rent_premium_percent" in data or "estimated_value_premium_percent" in data, \
            "Response should contain premium estimates"


class TestLEEDAssessment:
    """Test LEED certification assessment endpoint for comparison feature"""
    
    def test_leed_assess_returns_200(self):
        """Test that LEED assessment endpoint returns 200"""
        payload = {
            "property_name": "TEST_LEED_Property",
            "property_sector": "office",
            "region": "north_america",
            "leed_version": "v4.1",
            "project_type": "bd+c",
            "category_scores": {
                "energy_atmosphere": 15,
                "location_transportation": 8,
                "indoor_environmental_quality": 8,
                "materials_resources": 6,
                "water_efficiency": 5,
                "sustainable_sites": 5,
                "innovation": 3,
                "regional_priority": 2,
                "integrative_process": 1
            },
            "gross_floor_area_m2": 5000,
            "year_built": 2020,
            "current_value": 50000000
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_leed_assess_returns_total_points(self):
        """Test that LEED assessment returns total points"""
        payload = {
            "property_name": "TEST_LEED_Points",
            "property_sector": "office",
            "region": "north_america",
            "leed_version": "v4.1",
            "project_type": "bd+c",
            "category_scores": {
                "energy_atmosphere": 20,
                "location_transportation": 10,
                "indoor_environmental_quality": 10,
                "materials_resources": 8,
                "water_efficiency": 7,
                "sustainable_sites": 6,
                "innovation": 4,
                "regional_priority": 3,
                "integrative_process": 1
            },
            "gross_floor_area_m2": 5000,
            "year_built": 2020,
            "current_value": 50000000
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_points" in data, "Response should contain total_points"
        
    def test_leed_assess_returns_certification_level(self):
        """Test that LEED assessment returns certification level"""
        payload = {
            "property_name": "TEST_LEED_Level",
            "property_sector": "office",
            "region": "north_america",
            "leed_version": "v4.1",
            "project_type": "bd+c",
            "category_scores": {
                "energy_atmosphere": 25,
                "location_transportation": 12,
                "indoor_environmental_quality": 12,
                "materials_resources": 10,
                "water_efficiency": 8,
                "sustainable_sites": 8,
                "innovation": 5,
                "regional_priority": 3,
                "integrative_process": 1
            },
            "gross_floor_area_m2": 8000,
            "year_built": 2022,
            "current_value": 80000000
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/sustainability/leed/assess", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "certification_level" in data, "Response should contain certification_level"
        valid_levels = ["certified", "silver", "gold", "platinum", "not_certified"]
        assert data["certification_level"] in valid_levels, f"Level {data['certification_level']} should be valid"


class TestSustainabilityExportPDF:
    """Test sustainability assessment PDF export"""
    
    def test_export_breeam_pdf_returns_200(self):
        """Test that BREEAM PDF export returns 200"""
        payload = {
            "property_name": "TEST_Export_Property",
            "weighted_score": 65.5,
            "rating": "excellent",
            "estimated_rent_premium_percent": 7.5,
            "estimated_value_premium_percent": 12.8,
            "estimated_value_impact": 6400000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=pdf&assessment_type=breeam",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_export_breeam_pdf_content_type(self):
        """Test that BREEAM PDF export returns PDF content type"""
        payload = {
            "property_name": "TEST_Export_PDF",
            "weighted_score": 70.0,
            "rating": "excellent"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=pdf&assessment_type=breeam",
            json=payload
        )
        assert response.status_code == 200
        content_type = response.headers.get('Content-Type', '')
        assert 'application/pdf' in content_type, f"Expected PDF content type, got {content_type}"
        
    def test_export_breeam_pdf_has_content(self):
        """Test that PDF export has actual content"""
        payload = {
            "property_name": "TEST_Export_Content",
            "weighted_score": 55.0,
            "rating": "very_good"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=pdf&assessment_type=breeam",
            json=payload
        )
        assert response.status_code == 200
        # PDF file should have content
        assert len(response.content) > 0, "PDF should have content"
        # PDF files start with %PDF
        assert response.content[:4] == b'%PDF', "Content should be valid PDF"
        
    def test_export_leed_pdf_returns_200(self):
        """Test that LEED PDF export returns 200"""
        payload = {
            "property_name": "TEST_LEED_Export",
            "total_score": 68,
            "certification_level": "gold"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=pdf&assessment_type=leed",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestSustainabilityExportExcel:
    """Test sustainability assessment Excel export"""
    
    def test_export_breeam_excel_returns_200(self):
        """Test that BREEAM Excel export returns 200"""
        payload = {
            "property_name": "TEST_Excel_Property",
            "weighted_score": 65.5,
            "rating": "excellent",
            "estimated_rent_premium_percent": 7.5,
            "estimated_value_premium_percent": 12.8
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=excel&assessment_type=breeam",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_export_breeam_excel_content_type(self):
        """Test that BREEAM Excel export returns Excel content type"""
        payload = {
            "property_name": "TEST_Excel_Type",
            "weighted_score": 70.0,
            "rating": "excellent"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=excel&assessment_type=breeam",
            json=payload
        )
        assert response.status_code == 200
        content_type = response.headers.get('Content-Type', '')
        assert 'spreadsheetml' in content_type or 'xlsx' in content_type or 'excel' in content_type, \
            f"Expected Excel content type, got {content_type}"
        
    def test_export_breeam_excel_has_content(self):
        """Test that Excel export has actual content"""
        payload = {
            "property_name": "TEST_Excel_Content",
            "weighted_score": 55.0,
            "rating": "very_good"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=excel&assessment_type=breeam",
            json=payload
        )
        assert response.status_code == 200
        # Excel file should have content
        assert len(response.content) > 0, "Excel should have content"
        # XLSX files start with PK (ZIP format)
        assert response.content[:2] == b'PK', "Content should be valid XLSX (ZIP format)"
        
    def test_export_leed_excel_returns_200(self):
        """Test that LEED Excel export returns 200"""
        payload = {
            "property_name": "TEST_LEED_Excel",
            "total_score": 75,
            "certification_level": "gold"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=excel&assessment_type=leed",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestBREEAMWeightsEndpoint:
    """Test BREEAM weights reference endpoint"""
    
    def test_breeam_weights_returns_200(self):
        """Test that BREEAM weights endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/breeam/weights")
        assert response.status_code == 200
        
    def test_breeam_weights_has_categories(self):
        """Test that BREEAM weights returns all categories"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/breeam/weights")
        assert response.status_code == 200
        
        data = response.json()
        assert "weights" in data, "Response should contain weights"
        
        expected_categories = [
            "management", "health_wellbeing", "energy", "transport",
            "water", "materials", "waste", "land_use_ecology", "pollution", "innovation"
        ]
        for cat in expected_categories:
            assert cat in data["weights"], f"Weights should contain {cat}"
            
    def test_breeam_weights_has_rating_thresholds(self):
        """Test that BREEAM weights returns rating thresholds"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/breeam/weights")
        assert response.status_code == 200
        
        data = response.json()
        assert "rating_thresholds" in data, "Response should contain rating_thresholds"
        
        expected_thresholds = ["pass", "good", "very_good", "excellent", "outstanding"]
        for threshold in expected_thresholds:
            assert threshold in data["rating_thresholds"], f"Thresholds should contain {threshold}"


class TestLEEDThresholdsEndpoint:
    """Test LEED thresholds reference endpoint"""
    
    def test_leed_thresholds_returns_200(self):
        """Test that LEED thresholds endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/leed/thresholds")
        assert response.status_code == 200
        
    def test_leed_thresholds_has_levels(self):
        """Test that LEED thresholds returns certification levels"""
        response = requests.get(f"{BASE_URL}/api/v1/sustainability/leed/thresholds")
        assert response.status_code == 200
        
        data = response.json()
        assert "levels" in data, "Response should contain levels"
        
        expected_levels = ["certified", "silver", "gold", "platinum"]
        for level in expected_levels:
            assert level in data["levels"], f"Levels should contain {level}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
