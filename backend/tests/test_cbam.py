"""
CBAM (Carbon Border Adjustment Mechanism) Module Backend Tests
Tests for: products, suppliers, emissions, cost projections, countries, certificate prices
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestCBAMSeed:
    """Test CBAM data seeding (15 products, 20 countries, 24 prices)"""
    
    def test_seed_endpoint(self, api_client):
        """POST /api/v1/cbam/seed returns success"""
        response = api_client.post(f"{BASE_URL}/api/v1/cbam/seed")
        assert response.status_code == 200
        data = response.json()
        # Should return counts (0 if already seeded)
        assert "products" in data
        assert "countries" in data
        assert "prices" in data


class TestCBAMDashboard:
    """Test CBAM dashboard stats"""
    
    def test_dashboard_returns_stats(self, api_client):
        """GET /api/v1/cbam/dashboard returns stats"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all stat fields present
        assert "total_suppliers" in data
        assert "total_products" in data
        assert "total_countries" in data
        assert "emissions_records" in data
        assert "high_risk_suppliers" in data
        assert "total_embedded_emissions_tco2" in data
        assert "sector_breakdown" in data
    
    def test_dashboard_correct_counts(self, api_client):
        """Dashboard shows 15 products, 20 countries"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/dashboard")
        data = response.json()
        
        assert data["total_products"] == 15
        assert data["total_countries"] == 20
    
    def test_dashboard_sector_breakdown(self, api_client):
        """Dashboard has 6 sectors: Cement, Iron & Steel, Aluminium, Fertilizers, Electricity, Hydrogen"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/dashboard")
        data = response.json()
        
        sectors = data["sector_breakdown"]
        expected_sectors = ["Cement", "Iron & Steel", "Aluminium", "Fertilizers", "Electricity", "Hydrogen"]
        for sector in expected_sectors:
            assert sector in sectors, f"Missing sector: {sector}"


class TestCBAMProducts:
    """Test CBAM product categories"""
    
    def test_products_returns_15(self, api_client):
        """GET /api/v1/cbam/products returns 15 products"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/products")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 15
    
    def test_products_have_required_fields(self, api_client):
        """Products have all required fields"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/products")
        data = response.json()
        
        for product in data:
            assert "id" in product
            assert "cn_code" in product
            assert "hs_code" in product
            assert "sector" in product
            assert "product_name" in product
            assert "default_direct_emissions" in product
            assert "default_indirect_emissions" in product
            assert "default_total_emissions" in product
    
    def test_products_by_sector_filter(self, api_client):
        """Filter products by sector works"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/products?sector=Cement")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # 3 cement products
        for product in data:
            assert product["sector"] == "Cement"
    
    def test_products_sectors_summary(self, api_client):
        """GET /api/v1/cbam/products/sectors/summary returns sector breakdown"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/products/sectors/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Should have 6 sectors
        assert len(data) == 6
        
        # Each sector has product_count and avg_emissions
        for sector in data:
            assert "sector" in sector
            assert "product_count" in sector
            assert "avg_emissions" in sector
    
    def test_product_counts_by_sector(self, api_client):
        """Verify correct product counts per sector"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/products/sectors/summary")
        data = response.json()
        
        expected_counts = {
            "Cement": 3,
            "Iron & Steel": 4,
            "Aluminium": 3,
            "Fertilizers": 3,
            "Electricity": 1,
            "Hydrogen": 1
        }
        
        for sector in data:
            sector_name = sector["sector"]
            if sector_name in expected_counts:
                assert sector["product_count"] == expected_counts[sector_name], f"Wrong count for {sector_name}"


class TestCBAMSuppliers:
    """Test CBAM supplier management"""
    
    def test_suppliers_list(self, api_client):
        """GET /api/v1/cbam/suppliers returns supplier list"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_supplier_has_required_fields(self, api_client):
        """Suppliers have all required fields"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers")
        data = response.json()
        
        if len(data) > 0:
            supplier = data[0]
            assert "id" in supplier
            assert "supplier_name" in supplier
            assert "country_code" in supplier
            assert "verification_status" in supplier
            assert "has_domestic_carbon_price" in supplier
            assert "domestic_carbon_price" in supplier
            assert "risk_score" in supplier
            assert "risk_category" in supplier
    
    def test_create_supplier_with_auto_risk(self, api_client):
        """POST /api/v1/cbam/suppliers creates supplier with auto-assigned risk"""
        response = api_client.post(f"{BASE_URL}/api/v1/cbam/suppliers", json={
            "supplier_name": "TEST_TestSupplier_India",
            "country_code": "IN"
        })
        assert response.status_code == 201
        data = response.json()
        
        assert data["supplier_name"] == "TEST_TestSupplier_India"
        assert data["country_code"] == "IN"
        # India should have "Very High" risk
        assert data["risk_category"] == "Very High"
        assert data["risk_score"] == 0.85
        
        # Cleanup
        supplier_id = data["id"]
        api_client.delete(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}")
    
    def test_create_supplier_with_domestic_carbon_price(self, api_client):
        """POST /api/v1/cbam/suppliers with carbon pricing country"""
        response = api_client.post(f"{BASE_URL}/api/v1/cbam/suppliers", json={
            "supplier_name": "TEST_TestSupplier_UK",
            "country_code": "GB",
            "has_domestic_carbon_price": True
        })
        assert response.status_code == 201
        data = response.json()
        
        # UK has carbon pricing at €55
        assert data["domestic_carbon_price"] == 55.0
        assert data["risk_category"] == "Low"
        
        # Cleanup
        supplier_id = data["id"]
        api_client.delete(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}")
    
    def test_get_supplier_by_id(self, api_client):
        """GET /api/v1/cbam/suppliers/{id} returns specific supplier"""
        # First get all suppliers
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers")
        suppliers = response.json()
        
        if len(suppliers) > 0:
            supplier_id = suppliers[0]["id"]
            response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == supplier_id
    
    def test_get_supplier_not_found(self, api_client):
        """GET /api/v1/cbam/suppliers/{invalid_id} returns 404"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers/invalid-uuid-12345")
        assert response.status_code == 404
    
    def test_delete_supplier(self, api_client):
        """DELETE /api/v1/cbam/suppliers/{id} deletes supplier"""
        # Create a supplier first
        create_response = api_client.post(f"{BASE_URL}/api/v1/cbam/suppliers", json={
            "supplier_name": "TEST_ToDelete",
            "country_code": "US"
        })
        supplier_id = create_response.json()["id"]
        
        # Delete it
        delete_response = api_client.delete(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}")
        assert delete_response.status_code == 204
        
        # Verify it's gone
        get_response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}")
        assert get_response.status_code == 404


class TestCBAMEmissions:
    """Test CBAM emissions recording"""
    
    def test_record_emissions_with_defaults(self, api_client):
        """POST /api/v1/cbam/emissions uses default values when not provided"""
        # Create supplier first
        supplier_resp = api_client.post(f"{BASE_URL}/api/v1/cbam/suppliers", json={
            "supplier_name": "TEST_EmissionsSupplier",
            "country_code": "CN"
        })
        supplier_id = supplier_resp.json()["id"]
        
        # Get a product ID
        products_resp = api_client.get(f"{BASE_URL}/api/v1/cbam/products?sector=Cement")
        product_id = products_resp.json()[0]["id"]
        
        # Record emissions without specific values
        emissions_resp = api_client.post(f"{BASE_URL}/api/v1/cbam/emissions", json={
            "supplier_id": supplier_id,
            "product_category_id": product_id,
            "reporting_year": 2025,
            "reporting_quarter": 1,
            "import_volume_tonnes": 1000,
            "direct_emissions": 500
        })
        assert emissions_resp.status_code == 201
        data = emissions_resp.json()
        
        assert "id" in data
        assert data["uses_default_values"] == True  # Should use default specific_total
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}")
    
    def test_list_emissions(self, api_client):
        """GET /api/v1/cbam/emissions returns list"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/emissions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCBAMCostCalculation:
    """Test CBAM cost calculation"""
    
    def test_calculate_cost_basic(self, api_client):
        """POST /api/v1/cbam/calculate-cost returns correct values"""
        response = api_client.post(f"{BASE_URL}/api/v1/cbam/calculate-cost", json={
            "emissions_tco2": 1000,
            "eu_ets_price": 80,
            "domestic_carbon_price": 0,
            "free_allocation_pct": 0
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["gross_cost_eur"] == 80000.0  # 1000 * 80
        assert data["domestic_credit_eur"] == 0
        assert data["free_allocation_reduction_eur"] == 0
        assert data["net_cbam_cost_eur"] == 80000.0
    
    def test_calculate_cost_with_domestic_credit(self, api_client):
        """Cost calculation applies domestic carbon credit correctly"""
        response = api_client.post(f"{BASE_URL}/api/v1/cbam/calculate-cost", json={
            "emissions_tco2": 1000,
            "eu_ets_price": 80,
            "domestic_carbon_price": 20,
            "free_allocation_pct": 0
        })
        data = response.json()
        
        assert data["gross_cost_eur"] == 80000.0
        assert data["domestic_credit_eur"] == 20000.0  # 1000 * 20
        assert data["net_cbam_cost_eur"] == 60000.0  # 80000 - 20000
    
    def test_calculate_cost_with_free_allocation(self, api_client):
        """Cost calculation applies free allocation correctly"""
        response = api_client.post(f"{BASE_URL}/api/v1/cbam/calculate-cost", json={
            "emissions_tco2": 1000,
            "eu_ets_price": 80,
            "domestic_carbon_price": 0,
            "free_allocation_pct": 97.5  # 2026 rate
        })
        data = response.json()
        
        assert data["gross_cost_eur"] == 80000.0
        assert data["free_allocation_reduction_eur"] == 78000.0  # 80000 * 0.975
        assert data["net_cbam_cost_eur"] == 2000.0  # 80000 - 78000
    
    def test_calculate_cost_net_cannot_be_negative(self, api_client):
        """Net CBAM cost cannot be negative"""
        response = api_client.post(f"{BASE_URL}/api/v1/cbam/calculate-cost", json={
            "emissions_tco2": 1000,
            "eu_ets_price": 80,
            "domestic_carbon_price": 100,  # Higher than ETS price
            "free_allocation_pct": 50
        })
        data = response.json()
        
        # Net cost should be 0, not negative
        assert data["net_cbam_cost_eur"] >= 0


class TestCBAMSupplierProjections:
    """Test CBAM cost projections for suppliers"""
    
    def test_projections_for_existing_supplier(self, api_client):
        """GET /api/v1/cbam/suppliers/{id}/projections returns cost projections"""
        # Get existing supplier with emissions
        suppliers_resp = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers")
        suppliers = suppliers_resp.json()
        
        if len(suppliers) > 0:
            supplier_id = suppliers[0]["id"]
            response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}/projections")
            assert response.status_code == 200
            data = response.json()
            
            # Should return projections across 3 scenarios and multiple years
            if len(data) > 0:
                projection = data[0]
                assert "supplier_id" in projection
                assert "supplier_name" in projection
                assert "year" in projection
                assert "scenario" in projection
                assert "import_volume_tonnes" in projection
                assert "embedded_emissions_tco2" in projection
                assert "eu_ets_price_eur" in projection
                assert "free_allocation_pct" in projection
                assert "net_cbam_cost_eur" in projection
    
    def test_projections_include_all_scenarios(self, api_client):
        """Projections include all 3 ETS price scenarios"""
        suppliers_resp = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers")
        suppliers = suppliers_resp.json()
        
        if len(suppliers) > 0:
            supplier_id = suppliers[0]["id"]
            response = api_client.get(f"{BASE_URL}/api/v1/cbam/suppliers/{supplier_id}/projections")
            data = response.json()
            
            if len(data) > 0:
                scenarios = set(p["scenario"] for p in data)
                assert "Current Trend" in scenarios
                assert "Ambitious" in scenarios
                assert "Conservative" in scenarios


class TestCBAMCountryRisk:
    """Test CBAM country risk database"""
    
    def test_countries_returns_20(self, api_client):
        """GET /api/v1/cbam/countries returns 20 countries"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/countries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 20
    
    def test_countries_have_required_fields(self, api_client):
        """Countries have all required fields"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/countries")
        data = response.json()
        
        for country in data:
            assert "country_code" in country
            assert "country_name" in country
            assert "has_carbon_pricing" in country
            assert "carbon_price_eur" in country
            assert "grid_emission_factor" in country
            assert "risk_score" in country
            assert "risk_category" in country
    
    def test_countries_sorted_by_risk(self, api_client):
        """Countries sorted by risk score descending"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/countries")
        data = response.json()
        
        risk_scores = [c["risk_score"] for c in data]
        assert risk_scores == sorted(risk_scores, reverse=True)
    
    def test_countries_with_carbon_pricing(self, api_client):
        """Verify some countries have carbon pricing"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/countries")
        data = response.json()
        
        countries_with_pricing = [c for c in data if c["has_carbon_pricing"]]
        assert len(countries_with_pricing) >= 5  # At least 5 countries have pricing
        
        # Verify known carbon pricing countries
        country_codes = {c["country_code"] for c in countries_with_pricing}
        assert "GB" in country_codes  # UK
        assert "CH" in country_codes  # Switzerland
        assert "NO" in country_codes  # Norway


class TestCBAMCertificatePrices:
    """Test CBAM certificate price scenarios"""
    
    def test_certificate_prices_returns_data(self, api_client):
        """GET /api/v1/cbam/certificate-prices returns price scenarios"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/certificate-prices")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 24  # 8 years * 3 scenarios
    
    def test_certificate_prices_have_required_fields(self, api_client):
        """Certificate prices have all required fields"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/certificate-prices")
        data = response.json()
        
        for price in data:
            assert "date" in price  # Year
            assert "ets_price" in price
            assert "cbam_price" in price
            assert "scenario" in price
            assert "is_projection" in price
    
    def test_certificate_prices_filter_by_scenario(self, api_client):
        """Filter certificate prices by scenario"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/certificate-prices?scenario=Ambitious")
        assert response.status_code == 200
        data = response.json()
        
        for price in data:
            assert price["scenario"] == "Ambitious"


class TestCBAMFreeAllocation:
    """Test CBAM free allocation phase-out schedule"""
    
    def test_free_allocation_schedule(self, api_client):
        """GET /api/v1/cbam/free-allocation-schedule returns phase-out"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/free-allocation-schedule")
        assert response.status_code == 200
        data = response.json()
        
        # Should have 9 years (2026-2034)
        assert len(data) == 9
    
    def test_free_allocation_phase_out_values(self, api_client):
        """Free allocation decreases from 97.5% (2026) to 0% (2034)"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/free-allocation-schedule")
        data = response.json()
        
        assert data["2026"] == 97.5
        assert data["2027"] == 95.0
        assert data["2030"] == 51.5
        assert data["2034"] == 0.0


class TestCBAMETSScenarios:
    """Test ETS price scenarios endpoint"""
    
    def test_ets_scenarios(self, api_client):
        """GET /api/v1/cbam/ets-price-scenarios returns 3 scenarios"""
        response = api_client.get(f"{BASE_URL}/api/v1/cbam/ets-price-scenarios")
        assert response.status_code == 200
        data = response.json()
        
        assert "Current Trend" in data
        assert "Ambitious" in data
        assert "Conservative" in data
