"""
Real Estate Valuation Module Tests
Tests for Income (Direct Cap, DCF), Cost, and Sales Comparison approaches
"""
import pytest
import requests
import os
from datetime import date

# Use the public URL for API testing
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://climate-risk-hub-1.preview.emergentagent.com')


class TestValuationDashboard:
    """Dashboard KPI endpoint tests"""
    
    def test_dashboard_returns_200(self):
        """Test dashboard endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/dashboard")
        assert response.status_code == 200
        print("✓ Dashboard endpoint returns 200")
    
    def test_dashboard_has_required_kpis(self):
        """Test dashboard returns all required KPI fields"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/dashboard")
        data = response.json()
        
        assert "total_properties" in data
        assert "total_valuations" in data
        assert "total_portfolio_value" in data
        assert "avg_cap_rate" in data
        assert "avg_value_per_sf" in data
        assert "properties_by_type" in data
        assert "valuations_by_method" in data
        print("✓ Dashboard has all required KPI fields")
    
    def test_dashboard_kpi_values_valid(self):
        """Test dashboard KPI values are valid"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/dashboard")
        data = response.json()
        
        assert data["total_properties"] == 4
        assert float(data["total_portfolio_value"]) > 0
        assert 0 < float(data["avg_cap_rate"]) < 1
        print(f"✓ Dashboard shows {data['total_properties']} properties with ${float(data['total_portfolio_value']):,.0f} portfolio value")


class TestPropertiesList:
    """Properties list endpoint tests"""
    
    def test_properties_returns_200(self):
        """Test properties list endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        assert response.status_code == 200
        print("✓ Properties list endpoint returns 200")
    
    def test_properties_returns_4_items(self):
        """Test properties list returns 4 sample properties"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        data = response.json()
        
        assert data["total"] == 4
        assert len(data["items"]) == 4
        print("✓ Properties list returns 4 items")
    
    def test_properties_have_required_fields(self):
        """Test each property has required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties")
        data = response.json()
        
        required_fields = ["id", "property_name", "property_type", "city", "market_value", "cap_rate"]
        
        for prop in data["items"]:
            for field in required_fields:
                assert field in prop, f"Missing field: {field}"
        print("✓ All properties have required fields")
    
    def test_properties_filter_by_type(self):
        """Test filtering properties by type"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/properties?property_type=office")
        data = response.json()
        
        assert data["total"] == 1
        assert data["items"][0]["property_type"] == "office"
        print("✓ Property filtering by type works")


class TestComparablesList:
    """Comparables list endpoint tests"""
    
    def test_comparables_returns_200(self):
        """Test comparables list endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/comparables")
        assert response.status_code == 200
        print("✓ Comparables list endpoint returns 200")
    
    def test_comparables_returns_5_items(self):
        """Test comparables list returns 5 sample items"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/comparables")
        data = response.json()
        
        assert data["total"] == 5
        assert len(data["items"]) == 5
        print("✓ Comparables list returns 5 items")
    
    def test_comparables_have_required_fields(self):
        """Test each comparable has required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/comparables")
        data = response.json()
        
        required_fields = ["id", "property_type", "sale_date", "sale_price", "size_sf", "price_per_sf"]
        
        for comp in data["items"]:
            for field in required_fields:
                assert field in comp, f"Missing field: {field}"
        print("✓ All comparables have required fields")


class TestMarketCapRates:
    """Market cap rates endpoint tests"""
    
    def test_cap_rates_returns_200(self):
        """Test market cap rates endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/market/cap-rates")
        assert response.status_code == 200
        print("✓ Market cap rates endpoint returns 200")
    
    def test_cap_rates_has_all_property_types(self):
        """Test cap rates cover all property types"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/market/cap-rates")
        data = response.json()
        
        property_types = set(cr["property_type"] for cr in data["cap_rates"])
        expected_types = {"office", "retail", "industrial", "multifamily", "hotel"}
        
        assert expected_types.issubset(property_types)
        print("✓ Cap rates cover all property types")


class TestDirectCapitalization:
    """Direct Capitalization (Income Approach) tests"""
    
    def test_direct_cap_returns_200(self):
        """Test direct cap calculation returns 200 OK"""
        payload = {
            "rentable_area_sf": 100000,
            "market_rent_per_sf": 35,
            "other_income": 50000,
            "vacancy_rate": 0.05,
            "collection_loss_rate": 0.02,
            "operating_expense_ratio": 0.35,
            "cap_rate": 0.065
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/direct-capitalization", json=payload)
        assert response.status_code == 200
        print("✓ Direct cap endpoint returns 200")
    
    def test_direct_cap_calculates_correct_value(self):
        """Test direct cap calculates correct property value"""
        payload = {
            "rentable_area_sf": 100000,
            "market_rent_per_sf": 35,
            "other_income": 50000,
            "vacancy_rate": 0.05,
            "collection_loss_rate": 0.02,
            "operating_expense_ratio": 0.35,
            "cap_rate": 0.065
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/direct-capitalization", json=payload)
        data = response.json()
        
        # Verify NOI calculation: PGI - losses - expenses = NOI
        pgi = float(data["pgi"])
        vacancy = float(data["vacancy_loss"])
        collection = float(data["collection_loss"])
        egi = float(data["egi"])
        expenses = float(data["operating_expenses"])
        noi = float(data["noi"])
        value = float(data["property_value"])
        
        assert abs(egi - (pgi - vacancy - collection)) < 1
        assert abs(noi - (egi - expenses)) < 1
        assert abs(value - (noi / 0.065)) < 1
        
        print(f"✓ Direct cap: NOI=${noi:,.0f}, Cap Rate=6.5%, Value=${value:,.0f}")
    
    def test_direct_cap_has_all_metrics(self):
        """Test direct cap returns all required metrics"""
        payload = {
            "rentable_area_sf": 100000,
            "market_rent_per_sf": 35,
            "other_income": 0,
            "vacancy_rate": 0.05,
            "collection_loss_rate": 0.02,
            "operating_expense_ratio": 0.35,
            "cap_rate": 0.065
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/direct-capitalization", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        required_fields = ["pgi", "egi", "noi", "property_value", "value_per_sf", 
                          "expense_ratio", "gross_income_multiplier", "net_income_multiplier"]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print("✓ Direct cap returns all required metrics")


class TestDCFAnalysis:
    """DCF Analysis (Income Approach) tests"""
    
    def test_dcf_returns_200(self):
        """Test DCF analysis returns 200 OK"""
        payload = {
            "projection_years": 10,
            "current_noi": 2500000,
            "revenue_growth_rate": 0.03,
            "expense_growth_rate": 0.02,
            "inflation_rate": 0.02,
            "discount_rate": 0.08,
            "terminal_cap_rate": 0.065,
            "terminal_growth_rate": 0.02,
            "equity_investment": 12000000,
            "debt_service": 1500000,
            "selling_costs_percent": 0.03
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/dcf", json=payload)
        assert response.status_code == 200
        print("✓ DCF endpoint returns 200")
    
    def test_dcf_returns_cash_flows(self):
        """Test DCF returns year-by-year cash flows"""
        payload = {
            "projection_years": 10,
            "current_noi": 2500000,
            "revenue_growth_rate": 0.03,
            "expense_growth_rate": 0.02,
            "inflation_rate": 0.02,
            "discount_rate": 0.08,
            "terminal_cap_rate": 0.065,
            "terminal_growth_rate": 0.02,
            "equity_investment": 12000000,
            "debt_service": 1500000
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/dcf", json=payload)
        data = response.json()
        
        assert "cash_flows" in data
        assert len(data["cash_flows"]) == 10
        
        # Verify cash flow structure
        cf = data["cash_flows"][0]
        assert "year" in cf
        assert "revenue" in cf
        assert "expenses" in cf
        assert "noi" in cf
        assert "cfads" in cf
        
        print(f"✓ DCF returns {len(data['cash_flows'])} years of cash flows")
    
    def test_dcf_returns_key_metrics(self):
        """Test DCF returns NPV, IRR, and equity multiple"""
        payload = {
            "projection_years": 10,
            "current_noi": 2500000,
            "revenue_growth_rate": 0.03,
            "expense_growth_rate": 0.02,
            "inflation_rate": 0.02,
            "discount_rate": 0.08,
            "terminal_cap_rate": 0.065,
            "terminal_growth_rate": 0.02,
            "equity_investment": 12000000,
            "debt_service": 1500000
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/dcf", json=payload)
        data = response.json()
        
        assert "npv" in data
        assert "irr" in data
        assert "equity_multiple" in data
        assert "terminal_value" in data
        
        npv = float(data["npv"])
        irr = float(data["irr"])
        em = float(data["equity_multiple"])
        
        assert npv > 0, "NPV should be positive for this scenario"
        assert 0 < irr < 1, "IRR should be between 0 and 100%"
        assert em > 1, "Equity multiple should be > 1"
        
        print(f"✓ DCF: NPV=${npv:,.0f}, IRR={irr*100:.1f}%, EM={em:.2f}x")
    
    def test_dcf_sensitivity_analysis(self):
        """Test DCF includes sensitivity analysis"""
        payload = {
            "projection_years": 10,
            "current_noi": 2500000,
            "discount_rate": 0.08,
            "terminal_cap_rate": 0.065,
            "equity_investment": 12000000,
            "debt_service": 1500000
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/income/dcf", json=payload)
        data = response.json()
        
        assert "sensitivity_cap_rate" in data
        assert "sensitivity_discount_rate" in data
        assert len(data["sensitivity_cap_rate"]) > 0
        
        print("✓ DCF includes sensitivity analysis")


class TestCostApproach:
    """Cost Approach (Replacement Cost) tests"""
    
    def test_cost_approach_returns_200(self):
        """Test cost approach calculation returns 200 OK"""
        payload = {
            "land_area_acres": 2.5,
            "land_value_per_acre": 5000000,
            "building_area_sf": 100000,
            "construction_type": "steel_frame",
            "quality": "class_a",
            "location_factor": 1.15,
            "effective_age": 15,
            "total_economic_life": 50,
            "condition_rating": "good"
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/cost/replacement", json=payload)
        assert response.status_code == 200
        print("✓ Cost approach endpoint returns 200")
    
    def test_cost_approach_calculates_depreciation(self):
        """Test cost approach calculates depreciation correctly"""
        payload = {
            "land_area_acres": 2.5,
            "land_value_per_acre": 5000000,
            "building_area_sf": 100000,
            "construction_type": "steel_frame",
            "quality": "class_a",
            "location_factor": 1.15,
            "effective_age": 15,
            "total_economic_life": 50,
            "condition_rating": "good",
            "external_obsolescence_percent": 0.02
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/cost/replacement", json=payload)
        data = response.json()
        
        land_value = float(data["land_value"])
        rcn = float(data["rcn"])
        total_depreciation = float(data["total_depreciation"])
        depreciated = float(data["depreciated_improvements"])
        property_value = float(data["property_value"])
        
        # Verify: Value = Land + (RCN - Depreciation)
        assert abs(depreciated - (rcn - total_depreciation)) < 1
        assert abs(property_value - (land_value + depreciated)) < 1
        
        # Age-life ratio should be 15/50 = 0.30
        assert abs(float(data["age_life_ratio"]) - 0.30) < 0.01
        
        print(f"✓ Cost approach: RCN=${rcn:,.0f}, Depreciation=${total_depreciation:,.0f}, Value=${property_value:,.0f}")
    
    def test_cost_approach_construction_types(self):
        """Test cost approach works with different construction types"""
        construction_types = ["steel_frame", "concrete", "masonry", "wood_frame", "prefabricated"]
        
        for ctype in construction_types:
            payload = {
                "land_area_acres": 1,
                "land_value_per_acre": 1000000,
                "building_area_sf": 50000,
                "construction_type": ctype,
                "quality": "class_b",
                "location_factor": 1.0,
                "effective_age": 10,
                "total_economic_life": 50,
                "condition_rating": "good"
            }
            response = requests.post(f"{BASE_URL}/api/v1/valuation/cost/replacement", json=payload)
            assert response.status_code == 200
        
        print(f"✓ Cost approach works with all {len(construction_types)} construction types")


class TestSalesComparison:
    """Sales Comparison Approach tests"""
    
    def test_sales_comparison_returns_200(self):
        """Test sales comparison returns 200 OK"""
        payload = {
            "subject_property": {
                "size_sf": 100000,
                "year_built": 2015,
                "quality": "class_a",
                "condition": "good",
                "location": "urban"
            },
            "comparables": [
                {
                    "id": "bb0e8400-e29b-41d4-a716-446655440001",
                    "sale_price": 42500000,
                    "sale_date": "2024-08-15",
                    "size_sf": 95000,
                    "year_built": 2012,
                    "quality": "class_a",
                    "condition": "good",
                    "location": "urban"
                }
            ],
            "market_appreciation_rate": 0.005
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/sales-comparison", json=payload)
        assert response.status_code == 200
        print("✓ Sales comparison endpoint returns 200")
    
    def test_sales_comparison_adjustments(self):
        """Test sales comparison calculates adjustments correctly"""
        payload = {
            "subject_property": {
                "size_sf": 100000,
                "year_built": 2015,
                "quality": "class_a",
                "condition": "good",
                "location": "urban"
            },
            "comparables": [
                {
                    "id": "bb0e8400-e29b-41d4-a716-446655440001",
                    "sale_price": 42500000,
                    "sale_date": "2024-08-15",
                    "size_sf": 95000,
                    "year_built": 2012,
                    "quality": "class_a",
                    "condition": "good",
                    "location": "urban"
                },
                {
                    "id": "bb0e8400-e29b-41d4-a716-446655440002",
                    "sale_price": 51000000,
                    "sale_date": "2024-06-20",
                    "size_sf": 110000,
                    "year_built": 2018,
                    "quality": "class_a",
                    "condition": "excellent",
                    "location": "urban"
                }
            ],
            "market_appreciation_rate": 0.005
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/sales-comparison", json=payload)
        data = response.json()
        
        assert "adjusted_comparables" in data
        assert len(data["adjusted_comparables"]) == 2
        
        # Verify adjustments are present
        comp = data["adjusted_comparables"][0]
        assert "adjustments" in comp
        assert len(comp["adjustments"]) >= 5  # time, size, age, quality, condition, location
        
        adjustment_types = [adj["type"] for adj in comp["adjustments"]]
        assert "time" in adjustment_types
        assert "size" in adjustment_types
        assert "age" in adjustment_types
        
        print(f"✓ Sales comparison applies {len(adjustment_types)} adjustment types")
    
    def test_sales_comparison_reconciliation(self):
        """Test sales comparison reconciles to final value"""
        payload = {
            "subject_property": {
                "size_sf": 100000,
                "year_built": 2015,
                "quality": "class_a",
                "condition": "good",
                "location": "urban"
            },
            "comparables": [
                {
                    "id": "bb0e8400-e29b-41d4-a716-446655440001",
                    "sale_price": 42500000,
                    "sale_date": "2024-08-15",
                    "size_sf": 95000,
                    "year_built": 2012,
                    "quality": "class_a",
                    "condition": "good",
                    "location": "urban"
                },
                {
                    "id": "bb0e8400-e29b-41d4-a716-446655440002",
                    "sale_price": 51000000,
                    "sale_date": "2024-06-20",
                    "size_sf": 110000,
                    "year_built": 2018,
                    "quality": "class_a",
                    "condition": "excellent",
                    "location": "urban"
                }
            ],
            "market_appreciation_rate": 0.005
        }
        response = requests.post(f"{BASE_URL}/api/v1/valuation/sales-comparison", json=payload)
        data = response.json()
        
        assert "reconciled_value" in data
        assert "value_per_sf" in data
        assert "confidence_level" in data
        assert "confidence_range_low" in data
        assert "confidence_range_high" in data
        
        value = float(data["reconciled_value"])
        low = float(data["confidence_range_low"])
        high = float(data["confidence_range_high"])
        
        assert low <= value <= high, "Reconciled value should be within confidence range"
        
        print(f"✓ Sales comparison: Value=${value:,.0f}, Range=${low:,.0f}-${high:,.0f}, Confidence={data['confidence_level']}")


class TestConstructionCosts:
    """Construction costs endpoint tests"""
    
    def test_construction_costs_returns_200(self):
        """Test construction costs endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/cost/construction-costs")
        assert response.status_code == 200
        print("✓ Construction costs endpoint returns 200")
    
    def test_construction_costs_all_types(self):
        """Test construction costs includes all types"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/cost/construction-costs")
        data = response.json()
        
        assert "construction_costs" in data
        assert len(data["construction_costs"]) > 0
        
        construction_types = set(c["construction_type"] for c in data["construction_costs"])
        expected = {"steel_frame", "concrete", "masonry", "wood_frame", "prefabricated"}
        
        assert expected.issubset(construction_types)
        print(f"✓ Construction costs include {len(construction_types)} types")


class TestLocationFactors:
    """Location factors endpoint tests"""
    
    def test_location_factors_returns_200(self):
        """Test location factors endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/cost/location-factors")
        assert response.status_code == 200
        print("✓ Location factors endpoint returns 200")
    
    def test_location_factors_has_markets(self):
        """Test location factors includes major markets"""
        response = requests.get(f"{BASE_URL}/api/v1/valuation/cost/location-factors")
        data = response.json()
        
        assert "location_factors" in data
        
        expected_markets = ["new_york", "san_francisco", "chicago", "houston"]
        for market in expected_markets:
            assert market in data["location_factors"]
        
        print(f"✓ Location factors include {len(data['location_factors'])} markets")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
