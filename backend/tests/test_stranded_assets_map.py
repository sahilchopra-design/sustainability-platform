"""
Tests for Stranded Assets Map Data API Endpoint
Testing the /api/v1/stranded-assets/map-data endpoint for map visualization
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://climate-risk-hub-2.preview.emergentagent.com').rstrip('/')


class TestStrandedAssetsMapData:
    """Tests for the /api/v1/stranded-assets/map-data endpoint"""
    
    def test_map_data_returns_200(self):
        """Test that map-data endpoint returns 200 status"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASSED: map-data endpoint returns 200")
    
    def test_map_data_returns_9_assets(self):
        """Test that map-data returns exactly 9 assets"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        data = response.json()
        assert data["total"] == 9, f"Expected 9 assets, got {data['total']}"
        assert len(data["assets"]) == 9, f"Expected 9 assets in list, got {len(data['assets'])}"
        print("PASSED: map-data returns 9 assets")
    
    def test_map_data_asset_has_required_fields(self):
        """Test that each asset has required fields for map visualization"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        data = response.json()
        
        required_fields = ["id", "name", "type", "latitude", "longitude", "risk_score"]
        
        for asset in data["assets"]:
            for field in required_fields:
                assert field in asset, f"Missing required field: {field} in asset {asset.get('name', 'unknown')}"
        
        print("PASSED: All assets have required fields for map visualization")
    
    def test_map_data_has_valid_coordinates(self):
        """Test that all assets have valid coordinates (lat/long)"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        data = response.json()
        
        for asset in data["assets"]:
            lat = asset["latitude"]
            lon = asset["longitude"]
            
            # Valid latitude: -90 to 90
            assert -90 <= lat <= 90, f"Invalid latitude {lat} for {asset['name']}"
            # Valid longitude: -180 to 180
            assert -180 <= lon <= 180, f"Invalid longitude {lon} for {asset['name']}"
        
        print("PASSED: All assets have valid coordinates")
    
    def test_map_data_has_valid_risk_scores(self):
        """Test that all assets have risk scores between 0 and 1"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        data = response.json()
        
        for asset in data["assets"]:
            risk_score = asset["risk_score"]
            assert 0 <= risk_score <= 1, f"Invalid risk score {risk_score} for {asset['name']}"
        
        print("PASSED: All assets have valid risk scores (0-1)")
    
    def test_map_data_has_all_asset_types(self):
        """Test that data includes reserve, power_plant, and infrastructure types"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        data = response.json()
        
        asset_types = set(asset["type"] for asset in data["assets"])
        
        expected_types = {"reserve", "power_plant", "infrastructure"}
        assert expected_types == asset_types, f"Expected types {expected_types}, got {asset_types}"
        
        print("PASSED: Map data includes all asset types (reserve, power_plant, infrastructure)")
    
    def test_map_data_filter_by_reserve(self):
        """Test filtering by asset_type=reserve"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data", params={"asset_type": "reserve"})
        assert response.status_code == 200
        data = response.json()
        
        for asset in data["assets"]:
            assert asset["type"] == "reserve", f"Expected type 'reserve', got {asset['type']}"
        
        # Should have 3 reserves
        assert len(data["assets"]) == 3, f"Expected 3 reserves, got {len(data['assets'])}"
        print("PASSED: Filter by asset_type=reserve works correctly (3 reserves)")
    
    def test_map_data_filter_by_power_plant(self):
        """Test filtering by asset_type=power_plant"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data", params={"asset_type": "power_plant"})
        assert response.status_code == 200
        data = response.json()
        
        for asset in data["assets"]:
            assert asset["type"] == "power_plant", f"Expected type 'power_plant', got {asset['type']}"
        
        # Should have 3 power plants
        assert len(data["assets"]) == 3, f"Expected 3 power plants, got {len(data['assets'])}"
        print("PASSED: Filter by asset_type=power_plant works correctly (3 power plants)")
    
    def test_map_data_filter_by_infrastructure(self):
        """Test filtering by asset_type=infrastructure"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data", params={"asset_type": "infrastructure"})
        assert response.status_code == 200
        data = response.json()
        
        for asset in data["assets"]:
            assert asset["type"] == "infrastructure", f"Expected type 'infrastructure', got {asset['type']}"
        
        # Should have 3 infrastructure assets
        assert len(data["assets"]) == 3, f"Expected 3 infrastructure assets, got {len(data['assets'])}"
        print("PASSED: Filter by asset_type=infrastructure works correctly (3 infrastructure assets)")


class TestStrandedAssetsDashboard:
    """Tests for the dashboard KPIs endpoint"""
    
    def test_dashboard_returns_200(self):
        """Test that dashboard endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/dashboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASSED: Dashboard endpoint returns 200")
    
    def test_dashboard_has_kpi_fields(self):
        """Test that dashboard returns expected KPI fields"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/dashboard")
        data = response.json()
        
        required_fields = [
            "total_assets", "total_reserves_count", "total_plants_count", 
            "total_infrastructure_count", "high_risk_assets", "critical_risk_assets",
            "total_exposure_usd", "stranded_value_at_risk_usd"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required KPI field: {field}"
        
        print("PASSED: Dashboard has all required KPI fields")


class TestStrandedAssetsCriticalAssets:
    """Tests for critical assets endpoint"""
    
    def test_critical_assets_returns_200(self):
        """Test that critical-assets endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/critical-assets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASSED: Critical assets endpoint returns 200")
    
    def test_critical_assets_has_alerts(self):
        """Test that critical assets returns alerts list"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/critical-assets")
        data = response.json()
        
        assert "alerts" in data, "Missing alerts field"
        assert "total" in data, "Missing total field"
        assert isinstance(data["alerts"], list), "Alerts should be a list"
        
        print(f"PASSED: Critical assets returns {data['total']} alerts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
