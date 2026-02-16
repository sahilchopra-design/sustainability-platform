"""
Portfolio Analytics Module API Tests
Tests for portfolio aggregation and reporting endpoints

Sample portfolio IDs:
- 00000000-0000-0000-0000-000000000101 (Core Real Estate Fund I)
- 00000000-0000-0000-0000-000000000102 (Value-Add Opportunity Fund II)
- 00000000-0000-0000-0000-000000000103 (Green Building REIT)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_BASE = f"{BASE_URL}/api/v1/portfolio-analytics"

# Sample portfolio IDs for testing
PORTFOLIO_ID_1 = "00000000-0000-0000-0000-000000000101"  # Core Real Estate Fund I
PORTFOLIO_ID_2 = "00000000-0000-0000-0000-000000000102"  # Value-Add Opportunity Fund II
PORTFOLIO_ID_3 = "00000000-0000-0000-0000-000000000103"  # Green Building REIT


class TestPortfolioListEndpoint:
    """Test GET /portfolios endpoint - list all portfolios"""
    
    def test_list_portfolios_returns_200(self):
        response = requests.get(f"{API_BASE}/portfolios")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ List portfolios returns 200")
    
    def test_list_portfolios_returns_items(self):
        response = requests.get(f"{API_BASE}/portfolios")
        data = response.json()
        
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        assert len(data["items"]) > 0, "Should have at least 1 portfolio"
        print(f"✓ List portfolios returns {len(data['items'])} portfolios")
    
    def test_portfolio_has_required_fields(self):
        response = requests.get(f"{API_BASE}/portfolios")
        data = response.json()
        portfolio = data["items"][0]
        
        required_fields = ["id", "name", "portfolio_type", "aum", "total_properties"]
        for field in required_fields:
            assert field in portfolio, f"Portfolio should have '{field}' field"
        print(f"✓ Portfolio has all required fields: {required_fields}")
    
    def test_portfolio_has_summary_metrics(self):
        response = requests.get(f"{API_BASE}/portfolios")
        data = response.json()
        portfolio = data["items"][0]
        
        # Check summary metrics
        assert portfolio.get("total_properties", 0) > 0, "Should have properties count"
        assert portfolio.get("total_value") is not None, "Should have total value"
        print("✓ Portfolio has summary metrics (total_properties, total_value)")


class TestPortfolioDetailEndpoint:
    """Test GET /portfolios/{id} endpoint"""
    
    def test_get_portfolio_by_id_returns_200(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Get portfolio {PORTFOLIO_ID_1} returns 200")
    
    def test_get_portfolio_returns_correct_data(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}")
        data = response.json()
        
        assert data["id"] == PORTFOLIO_ID_1, "Should return correct portfolio ID"
        assert data["name"] == "Core Real Estate Fund I", "Should return correct name"
        print(f"✓ Portfolio data correct: {data['name']}")
    
    def test_get_nonexistent_portfolio_returns_404(self):
        fake_id = "00000000-0000-0000-0000-000000000999"
        response = requests.get(f"{API_BASE}/portfolios/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent portfolio returns 404")


class TestPortfolioAnalyticsEndpoint:
    """Test GET /portfolios/{id}/analytics endpoint"""
    
    def test_analytics_returns_200(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/analytics")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Analytics endpoint returns 200")
    
    def test_analytics_has_portfolio_summary(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/analytics")
        data = response.json()
        
        assert "portfolio_summary" in data, "Should have portfolio_summary"
        summary = data["portfolio_summary"]
        
        assert "total_properties" in summary, "Summary should have total_properties"
        assert "total_base_value" in summary, "Summary should have total_base_value"
        assert "total_adjusted_value" in summary, "Summary should have total_adjusted_value"
        assert "value_change_pct" in summary, "Summary should have value_change_pct"
        print("✓ Analytics has portfolio_summary with required fields")
    
    def test_analytics_has_risk_metrics(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/analytics")
        data = response.json()
        
        assert "risk_metrics" in data, "Should have risk_metrics"
        risk = data["risk_metrics"]
        
        assert "weighted_avg_risk_score" in risk, "Risk should have weighted_avg_risk_score"
        assert "value_at_risk_95" in risk, "Risk should have value_at_risk_95"
        assert "risk_level" in risk, "Risk should have risk_level"
        assert "risk_distribution" in risk, "Risk should have risk_distribution"
        print("✓ Analytics has risk_metrics with required fields")
    
    def test_analytics_has_stranding_analysis(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/analytics")
        data = response.json()
        
        assert "stranding_analysis" in data, "Should have stranding_analysis"
        stranding = data["stranding_analysis"]
        
        assert "stranded_assets_count" in stranding, "Should have stranded_assets_count"
        assert "stranded_assets_value" in stranding, "Should have stranded_assets_value"
        assert "stranded_pct" in stranding, "Should have stranded_pct"
        print("✓ Analytics has stranding_analysis with required fields")
    
    def test_analytics_has_sustainability_metrics(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/analytics")
        data = response.json()
        
        assert "sustainability_metrics" in data, "Should have sustainability_metrics"
        sustainability = data["sustainability_metrics"]
        
        assert "pct_certified" in sustainability, "Should have pct_certified"
        assert "certified_count" in sustainability, "Should have certified_count"
        print("✓ Analytics has sustainability_metrics with required fields")
    
    def test_analytics_has_concentration_analysis(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/analytics")
        data = response.json()
        
        assert "concentration_analysis" in data, "Should have concentration_analysis"
        concentration = data["concentration_analysis"]
        
        assert "geographic" in concentration, "Should have geographic concentration"
        assert "sector" in concentration, "Should have sector concentration"
        print("✓ Analytics has concentration_analysis with geographic and sector")


class TestPortfolioDashboardEndpoint:
    """Test GET /portfolios/{id}/dashboard endpoint"""
    
    def test_dashboard_returns_200(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/dashboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Dashboard endpoint returns 200")
    
    def test_dashboard_has_kpi_cards(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/dashboard")
        data = response.json()
        
        assert "kpi_cards" in data, "Should have kpi_cards"
        assert len(data["kpi_cards"]) > 0, "Should have at least 1 KPI card"
        
        # Check KPI card structure
        kpi = data["kpi_cards"][0]
        assert "id" in kpi, "KPI should have id"
        assert "label" in kpi, "KPI should have label"
        assert "value" in kpi, "KPI should have value"
        print(f"✓ Dashboard has {len(data['kpi_cards'])} KPI cards")
    
    def test_dashboard_has_charts(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/dashboard")
        data = response.json()
        
        assert "charts" in data, "Should have charts"
        charts = data["charts"]
        
        expected_charts = ["sector_allocation", "geographic_distribution", "risk_distribution"]
        for chart in expected_charts:
            assert chart in charts, f"Should have {chart} chart"
        print(f"✓ Dashboard has charts: {list(charts.keys())}")
    
    def test_dashboard_has_alerts(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/dashboard")
        data = response.json()
        
        assert "alerts" in data, "Should have alerts array"
        # Portfolio 1 has stranded assets, so should have alerts
        assert len(data["alerts"]) > 0, "Should have at least 1 alert"
        
        alert = data["alerts"][0]
        assert "severity" in alert, "Alert should have severity"
        assert "title" in alert, "Alert should have title"
        assert "message" in alert, "Alert should have message"
        print(f"✓ Dashboard has {len(data['alerts'])} alerts")


class TestScenarioComparisonEndpoint:
    """Test POST /portfolios/{id}/scenarios/compare endpoint"""
    
    def test_compare_scenarios_returns_200(self):
        payload = {
            "scenario_ids": [
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002"
            ],
            "time_horizon": 10
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/scenarios/compare",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Scenario comparison returns 200")
    
    def test_compare_scenarios_returns_comparison_table(self):
        payload = {
            "scenario_ids": [
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002"
            ],
            "time_horizon": 10
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/scenarios/compare",
            json=payload
        )
        data = response.json()
        
        assert "comparison_table" in data, "Should have comparison_table"
        # Base case + 2 scenarios = 3 rows
        assert len(data["comparison_table"]) >= 3, "Should have at least 3 rows"
        print(f"✓ Comparison table has {len(data['comparison_table'])} rows")
    
    def test_compare_scenarios_returns_best_worst(self):
        payload = {
            "scenario_ids": [
                "00000000-0000-0000-0000-000000000001"
            ],
            "time_horizon": 10
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/scenarios/compare",
            json=payload
        )
        data = response.json()
        
        assert "best_scenario" in data, "Should have best_scenario"
        assert "worst_scenario" in data, "Should have worst_scenario"
        assert "value_spread" in data, "Should have value_spread"
        print(f"✓ Best: {data['best_scenario']}, Worst: {data['worst_scenario']}")
    
    def test_compare_scenarios_row_has_required_fields(self):
        payload = {
            "scenario_ids": [
                "00000000-0000-0000-0000-000000000001"
            ],
            "time_horizon": 10
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/scenarios/compare",
            json=payload
        )
        data = response.json()
        row = data["comparison_table"][0]
        
        required_fields = ["scenario_name", "total_value", "value_change_pct", "stranded_count", "var_95"]
        for field in required_fields:
            assert field in row, f"Row should have '{field}' field"
        print(f"✓ Comparison row has all required fields")


class TestReportGenerationEndpoint:
    """Test POST /portfolios/{id}/reports/generate endpoint"""
    
    def test_generate_valuation_report_returns_200(self):
        payload = {
            "report_type": "valuation",
            "format": "json",
            "time_horizon": 10
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/reports/generate",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Valuation report generation returns 200")
    
    def test_generate_climate_risk_report_returns_200(self):
        payload = {
            "report_type": "climate_risk",
            "format": "json"
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/reports/generate",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Climate risk report generation returns 200")
    
    def test_generate_sustainability_report_returns_200(self):
        payload = {
            "report_type": "sustainability",
            "format": "json"
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/reports/generate",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Sustainability report generation returns 200")
    
    def test_generate_tcfd_report_returns_200(self):
        payload = {
            "report_type": "tcfd",
            "format": "json"
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/reports/generate",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ TCFD report generation returns 200")
    
    def test_report_has_executive_summary(self):
        payload = {
            "report_type": "valuation",
            "format": "json"
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/reports/generate",
            json=payload
        )
        data = response.json()
        
        assert "executive_summary" in data, "Should have executive_summary"
        summary = data["executive_summary"]
        
        assert "portfolio_name" in summary, "Summary should have portfolio_name"
        assert "total_value" in summary, "Summary should have total_value"
        assert "property_count" in summary, "Summary should have property_count"
        print("✓ Report has executive_summary with required fields")
    
    def test_report_has_portfolio_overview(self):
        payload = {
            "report_type": "valuation",
            "format": "json"
        }
        response = requests.post(
            f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/reports/generate",
            json=payload
        )
        data = response.json()
        
        assert "portfolio_overview" in data, "Should have portfolio_overview"
        overview = data["portfolio_overview"]
        
        assert "portfolio_type" in overview, "Overview should have portfolio_type"
        assert "investment_strategy" in overview, "Overview should have investment_strategy"
        print("✓ Report has portfolio_overview with required fields")


class TestHoldingsEndpoint:
    """Test GET /portfolios/{id}/holdings endpoint"""
    
    def test_holdings_returns_200(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/holdings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Holdings endpoint returns 200")
    
    def test_holdings_returns_items(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/holdings")
        data = response.json()
        
        assert "items" in data, "Should have items"
        assert "total" in data, "Should have total"
        assert "total_value" in data, "Should have total_value"
        assert len(data["items"]) > 0, "Should have holdings"
        print(f"✓ Holdings returns {len(data['items'])} items")
    
    def test_holding_has_required_fields(self):
        response = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/holdings")
        data = response.json()
        holding = data["items"][0]
        
        required_fields = ["id", "portfolio_id", "property_name", "property_type", "current_value"]
        for field in required_fields:
            assert field in holding, f"Holding should have '{field}' field"
        print(f"✓ Holding has all required fields")


class TestEnumsEndpoint:
    """Test GET /enums endpoint"""
    
    def test_enums_returns_200(self):
        response = requests.get(f"{API_BASE}/enums")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Enums endpoint returns 200")
    
    def test_enums_has_expected_values(self):
        response = requests.get(f"{API_BASE}/enums")
        data = response.json()
        
        assert "portfolio_types" in data, "Should have portfolio_types"
        assert "investment_strategies" in data, "Should have investment_strategies"
        assert "report_types" in data, "Should have report_types"
        
        assert "fund" in data["portfolio_types"], "Should have 'fund' type"
        assert "reit" in data["portfolio_types"], "Should have 'reit' type"
        assert "valuation" in data["report_types"], "Should have 'valuation' report"
        print("✓ Enums has expected values")


class TestCRUDOperations:
    """Test CRUD operations for portfolios"""
    
    def test_create_portfolio(self):
        payload = {
            "name": "TEST_New Portfolio",
            "description": "Test portfolio for API testing",
            "portfolio_type": "fund",
            "investment_strategy": "core",
            "target_return": 8.5,
            "aum": 500000000,
            "currency": "USD"
        }
        response = requests.post(f"{API_BASE}/portfolios", json=payload)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        
        data = response.json()
        assert data["name"] == payload["name"], "Name should match"
        assert "id" in data, "Should return created ID"
        print(f"✓ Created portfolio with ID: {data['id']}")
        return data["id"]
    
    def test_update_portfolio(self):
        # First create a portfolio
        create_payload = {
            "name": "TEST_Update Portfolio",
            "portfolio_type": "fund",
            "aum": 100000000
        }
        create_response = requests.post(f"{API_BASE}/portfolios", json=create_payload)
        portfolio_id = create_response.json()["id"]
        
        # Update it
        update_payload = {
            "name": "TEST_Updated Portfolio Name",
            "aum": 200000000
        }
        response = requests.patch(
            f"{API_BASE}/portfolios/{portfolio_id}",
            json=update_payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["name"] == update_payload["name"], "Name should be updated"
        print(f"✓ Updated portfolio: {data['name']}")


# Additional integration tests
class TestMultiPortfolioAnalytics:
    """Test analytics across different portfolios"""
    
    def test_all_sample_portfolios_have_analytics(self):
        portfolio_ids = [PORTFOLIO_ID_1, PORTFOLIO_ID_2, PORTFOLIO_ID_3]
        
        for pid in portfolio_ids:
            response = requests.get(f"{API_BASE}/portfolios/{pid}/analytics")
            assert response.status_code == 200, f"Analytics for {pid} should return 200"
            data = response.json()
            assert data["portfolio_id"] == pid, f"Should return correct portfolio ID"
        
        print(f"✓ All {len(portfolio_ids)} portfolios have valid analytics")
    
    def test_different_portfolios_have_different_metrics(self):
        response1 = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_1}/analytics")
        response2 = requests.get(f"{API_BASE}/portfolios/{PORTFOLIO_ID_3}/analytics")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Different portfolios should have different values
        assert data1["portfolio_summary"]["total_properties"] != data2["portfolio_summary"]["total_properties"], \
            "Different portfolios should have different property counts"
        print("✓ Different portfolios have different metrics")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
