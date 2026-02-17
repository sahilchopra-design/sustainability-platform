"""
Test Database Refactor - Stranded Assets and Real Estate Valuation
Tests that data is being retrieved from PostgreSQL instead of hardcoded sample data.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStrandedAssetsDashboard:
    """Test Stranded Assets dashboard returns DB data (9 assets tracked)"""
    
    def test_dashboard_returns_correct_asset_count(self):
        """Dashboard should return 9 total assets (3 reserves + 3 plants + 3 infra)"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/dashboard")
        assert response.status_code == 200, f"Status {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["total_assets"] == 9, f"Expected 9 total assets, got {data['total_assets']}"
        assert data["total_reserves_count"] == 3, f"Expected 3 reserves, got {data['total_reserves_count']}"
        assert data["total_plants_count"] == 3, f"Expected 3 plants, got {data['total_plants_count']}"
        assert data["total_infrastructure_count"] == 3, f"Expected 3 infrastructure, got {data['total_infrastructure_count']}"
        
    def test_dashboard_has_exposure_calculations(self):
        """Dashboard should have calculated exposure values"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_exposure_usd" in data
        assert "stranded_value_at_risk_usd" in data
        assert "avg_stranding_risk_score" in data
        assert "assets_by_risk_category" in data
        
        # Verify numeric values are present and non-zero
        assert float(data["total_exposure_usd"]) > 0
        assert float(data["stranded_value_at_risk_usd"]) > 0


class TestStrandedAssetsReserves:
    """Test Stranded Assets reserves list from DB (3 reserves)"""
    
    def test_reserves_list_returns_three_reserves(self):
        """Should return exactly 3 reserves from database"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/reserves")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3, f"Expected 3 reserves, got {data['total']}"
        assert len(data["items"]) == 3
    
    def test_reserves_have_db_fields(self):
        """Reserves should have all required fields from DB"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/reserves")
        assert response.status_code == 200
        
        data = response.json()
        for reserve in data["items"]:
            # Check DB-derived fields
            assert "id" in reserve
            assert "asset_name" in reserve
            assert "reserve_type" in reserve
            assert "latitude" in reserve
            assert "longitude" in reserve
            assert "proven_reserves_mmBOE" in reserve
            assert "created_at" in reserve
            
    def test_reserves_names_from_db(self):
        """Verify reserve names match seeded data"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/reserves")
        assert response.status_code == 200
        
        data = response.json()
        names = [r["asset_name"] for r in data["items"]]
        
        # These are the names from the migration script
        expected_names = ["North Sea Oil Field Alpha", "Permian Basin Gas Field", "Queensland Coal Mine"]
        for expected in expected_names:
            assert expected in names, f"Missing reserve: {expected}"


class TestStrandedAssetsPowerPlants:
    """Test Stranded Assets power plants list from DB (3 plants)"""
    
    def test_plants_list_returns_three_plants(self):
        """Should return exactly 3 power plants from database"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/power-plants")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3, f"Expected 3 plants, got {data['total']}"
        assert len(data["items"]) == 3
    
    def test_plants_have_db_fields(self):
        """Power plants should have all required fields from DB"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/power-plants")
        assert response.status_code == 200
        
        data = response.json()
        for plant in data["items"]:
            assert "id" in plant
            assert "plant_name" in plant
            assert "technology_type" in plant
            assert "capacity_mw" in plant
            assert "latitude" in plant
            assert "longitude" in plant
            assert "country_code" in plant
            assert "created_at" in plant
    
    def test_plants_names_from_db(self):
        """Verify plant names match seeded data"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/power-plants")
        assert response.status_code == 200
        
        data = response.json()
        names = [p["plant_name"] for p in data["items"]]
        
        expected_names = ["Drax Coal Power Station", "Pembroke CCGT", "Ratcliffe-on-Soar"]
        for expected in expected_names:
            assert expected in names, f"Missing plant: {expected}"


class TestStrandedAssetsInfrastructure:
    """Test Stranded Assets infrastructure list from DB (3 assets)"""
    
    def test_infrastructure_list_returns_three_assets(self):
        """Should return exactly 3 infrastructure assets from database"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/infrastructure")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3, f"Expected 3 infrastructure assets, got {data['total']}"
        assert len(data["items"]) == 3
    
    def test_infrastructure_have_db_fields(self):
        """Infrastructure assets should have all required fields from DB"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/infrastructure")
        assert response.status_code == 200
        
        data = response.json()
        for asset in data["items"]:
            assert "id" in asset
            assert "asset_name" in asset
            assert "asset_type" in asset
            assert "latitude" in asset
            assert "longitude" in asset
            assert "design_capacity" in asset
            assert "created_at" in asset
    
    def test_infrastructure_names_from_db(self):
        """Verify infrastructure names match seeded data"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/infrastructure")
        assert response.status_code == 200
        
        data = response.json()
        names = [a["asset_name"] for a in data["items"]]
        
        expected_names = ["Trans-Alaska Pipeline", "Nord Stream 1", "Sabine Pass LNG Terminal"]
        for expected in expected_names:
            assert expected in names, f"Missing infrastructure: {expected}"


class TestStrandedAssetsMapData:
    """Test Stranded Assets map data endpoint returns geo coordinates"""
    
    def test_map_data_returns_all_nine_assets(self):
        """Map data should return all 9 assets with coordinates"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 9, f"Expected 9 assets on map, got {data['total']}"
        assert len(data["assets"]) == 9
    
    def test_map_data_has_coordinates(self):
        """Each asset should have valid lat/lng coordinates"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data")
        assert response.status_code == 200
        
        data = response.json()
        for asset in data["assets"]:
            assert "latitude" in asset
            assert "longitude" in asset
            assert "name" in asset
            assert "type" in asset
            # Verify coordinates are valid numbers
            assert isinstance(asset["latitude"], (int, float))
            assert isinstance(asset["longitude"], (int, float))
    
    def test_map_data_filter_by_type(self):
        """Can filter map data by asset type"""
        # Test reserve filter
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data?asset_type=reserve")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(a["type"] == "reserve" for a in data["assets"])
        
        # Test power_plant filter
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/map-data?asset_type=power_plant")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(a["type"] == "power_plant" for a in data["assets"])


class TestREValuationDashboard:
    """Test RE Valuation dashboard returns DB data ($830M portfolio)"""
    
    def test_dashboard_returns_correct_portfolio_value(self):
        """Dashboard should return approximately $830M portfolio value"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        portfolio_value = float(data["total_portfolio_value"])
        # Expected: $450M + $85M + $120M + $175M = $830M
        assert 800_000_000 <= portfolio_value <= 850_000_000, \
            f"Expected ~$830M portfolio, got ${portfolio_value:,.2f}"
        
    def test_dashboard_returns_correct_property_count(self):
        """Dashboard should return 4 properties"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_properties"] == 4, f"Expected 4 properties, got {data['total_properties']}"
    
    def test_dashboard_has_property_type_breakdown(self):
        """Dashboard should have properties by type breakdown"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "properties_by_type" in data
        by_type = data["properties_by_type"]
        
        # Should have 1 of each: office, retail, industrial, multifamily
        assert by_type.get("office") == 1
        assert by_type.get("retail") == 1
        assert by_type.get("industrial") == 1
        assert by_type.get("multifamily") == 1


class TestREValuationProperties:
    """Test RE Valuation properties list from DB (4 properties)"""
    
    def test_properties_list_returns_four_properties(self):
        """Should return exactly 4 properties from database"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 4, f"Expected 4 properties, got {data['total']}"
        assert len(data["items"]) == 4
    
    def test_properties_have_db_fields(self):
        """Properties should have all required fields from DB"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        assert response.status_code == 200
        
        data = response.json()
        for prop in data["items"]:
            assert "id" in prop
            assert "property_name" in prop
            assert "property_type" in prop
            assert "city" in prop
            assert "market_value" in prop
            assert "noi" in prop
            assert "cap_rate" in prop
            assert "created_at" in prop
    
    def test_properties_names_from_db(self):
        """Verify property names match seeded data"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        assert response.status_code == 200
        
        data = response.json()
        names = [p["property_name"] for p in data["items"]]
        
        expected_names = ["Downtown Office Tower", "Suburban Retail Center", 
                         "Industrial Distribution Center", "Urban Multifamily Complex"]
        for expected in expected_names:
            assert expected in names, f"Missing property: {expected}"
    
    def test_properties_filter_by_type(self):
        """Can filter properties by type"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties?property_type=office")
        assert response.status_code == 200
        
        data = response.json()
        assert all(p["property_type"] == "office" for p in data["items"])


class TestREValuationComparables:
    """Test RE Valuation comparables list from DB (5 comparables)"""
    
    def test_comparables_list_returns_five_comparables(self):
        """Should return exactly 5 comparable sales from database"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/comparables")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 5, f"Expected 5 comparables, got {data['total']}"
        assert len(data["items"]) == 5
    
    def test_comparables_have_db_fields(self):
        """Comparables should have all required fields from DB"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/comparables")
        assert response.status_code == 200
        
        data = response.json()
        for comp in data["items"]:
            assert "id" in comp
            assert "property_type" in comp
            assert "address" in comp
            assert "city" in comp
            assert "sale_price" in comp
            assert "size_sf" in comp
            assert "price_per_sf" in comp
            assert "sale_date" in comp
    
    def test_comparables_filter_by_type(self):
        """Can filter comparables by property type"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/comparables?property_type=office")
        assert response.status_code == 200
        
        data = response.json()
        assert all(c["property_type"] == "office" for c in data["items"])


class TestTransitionPathways:
    """Test energy transition pathways from DB"""
    
    def test_pathways_list_exists(self):
        """Transition pathways endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/transition-pathways")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert data["total"] >= 3  # At least 3 pathways seeded


class TestDataPersistence:
    """Verify data comes from DB not hardcoded samples"""
    
    def test_reserves_have_uuid_ids(self):
        """Reserve IDs should be valid UUIDs from PostgreSQL"""
        response = requests.get(f"{BASE_URL}/api/v1/stranded-assets/reserves")
        assert response.status_code == 200
        
        data = response.json()
        for reserve in data["items"]:
            # UUID format check
            id_str = reserve["id"]
            assert len(id_str) == 36  # Standard UUID length
            assert id_str.count("-") == 4  # UUID has 4 hyphens
    
    def test_properties_have_uuid_ids(self):
        """Property IDs should be valid UUIDs from PostgreSQL"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        assert response.status_code == 200
        
        data = response.json()
        for prop in data["items"]:
            id_str = prop["id"]
            assert len(id_str) == 36
            assert id_str.count("-") == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
