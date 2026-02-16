"""
Test Portfolio Analytics DB Persistence and Export Functionality
Tests:
1. Portfolio Analytics PostgreSQL persistence
2. Export PDF/Excel for Portfolio Analytics
3. Export endpoints for all modules
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "newtestuser@test.com"
TEST_PASSWORD = "password"
SAMPLE_PORTFOLIO_ID = "00000000-0000-0000-0000-000000000101"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with authentication."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPortfolioAnalyticsDBPersistence:
    """Test Portfolio Analytics PostgreSQL data persistence."""

    def test_list_portfolios_returns_200(self, auth_headers):
        """Test listing portfolios from database."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_list_portfolios_returns_data(self, auth_headers):
        """Test portfolios list contains sample data."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Response is paginated with items array
        assert "items" in data, "Expected paginated response with 'items'"
        assert isinstance(data["items"], list)
        # Sample data should be seeded
        if len(data["items"]) > 0:
            assert "id" in data["items"][0]
            assert "name" in data["items"][0]

    def test_list_portfolios_has_total_count(self, auth_headers):
        """Test portfolios list has total count for pagination."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data, "Expected 'total' count in response"
        assert data["total"] >= 0

    def test_get_portfolio_by_id(self, auth_headers):
        """Test getting single portfolio by ID."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}",
            headers=auth_headers
        )
        # Should return 200 with data from PostgreSQL
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["id"] == SAMPLE_PORTFOLIO_ID

    def test_get_portfolio_has_name_and_type(self, auth_headers):
        """Test portfolio response includes name and type."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "portfolio_type" in data

    def test_portfolio_dashboard_returns_200(self, auth_headers):
        """Test portfolio dashboard endpoint returns data from DB."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_portfolio_dashboard_has_kpi_cards(self, auth_headers):
        """Test dashboard contains KPI cards."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "kpi_cards" in data, "Dashboard should have kpi_cards"
        assert isinstance(data["kpi_cards"], list)
        assert len(data["kpi_cards"]) > 0, "Should have at least one KPI card"

    def test_portfolio_dashboard_has_charts(self, auth_headers):
        """Test dashboard contains chart data."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "charts" in data, "Dashboard should have charts"

    def test_portfolio_analytics_calculation(self, auth_headers):
        """Test portfolio analytics calculation endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_summary" in data
        assert "risk_metrics" in data

    def test_portfolio_holdings_returns_200(self, auth_headers):
        """Test portfolio holdings endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/v1/portfolio-analytics/portfolios/{SAMPLE_PORTFOLIO_ID}/holdings",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestPortfolioAnalyticsExportPDF:
    """Test Portfolio Analytics PDF Export."""

    def test_export_portfolio_pdf_returns_200(self, auth_headers):
        """Test PDF export returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=pdf",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_export_portfolio_pdf_content_type(self, auth_headers):
        """Test PDF export has correct content type."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=pdf",
            headers=auth_headers
        )
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "pdf" in content_type.lower(), f"Expected PDF content type, got: {content_type}"

    def test_export_portfolio_pdf_has_content(self, auth_headers):
        """Test PDF export has actual file content."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=pdf",
            headers=auth_headers
        )
        assert response.status_code == 200
        content = response.content
        assert len(content) > 100, "PDF should have content"
        # PDF files start with %PDF
        assert content[:4] == b'%PDF', f"Invalid PDF header: {content[:10]}"

    def test_export_portfolio_pdf_with_report_type(self, auth_headers):
        """Test PDF export with executive report type."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=pdf&report_type=executive",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.content[:4] == b'%PDF'


class TestPortfolioAnalyticsExportExcel:
    """Test Portfolio Analytics Excel Export."""

    def test_export_portfolio_excel_returns_200(self, auth_headers):
        """Test Excel export returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=excel",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_export_portfolio_excel_content_type(self, auth_headers):
        """Test Excel export has correct content type."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type.lower() or "xlsx" in content_type.lower() or "zip" in content_type.lower() or "octet" in content_type.lower(), \
            f"Expected Excel content type, got: {content_type}"

    def test_export_portfolio_excel_has_content(self, auth_headers):
        """Test Excel export has actual file content."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/portfolio-analytics/{SAMPLE_PORTFOLIO_ID}?format=excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        content = response.content
        assert len(content) > 100, "Excel file should have content"
        # XLSX files are ZIP archives starting with PK
        assert content[:2] == b'PK', f"Invalid XLSX header (not ZIP): {content[:10]}"


class TestOtherModuleExports:
    """Test export endpoints for other modules."""

    def test_sustainability_export_pdf(self, auth_headers):
        """Test sustainability assessment PDF export."""
        assessment_data = {
            "weighted_score": "72.5",
            "rating": "excellent",
            "estimated_rent_premium_percent": 5.5,
            "estimated_value_premium_percent": 8.2,
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=pdf&assessment_type=breeam",
            headers=auth_headers,
            json=assessment_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF'

    def test_sustainability_export_excel(self, auth_headers):
        """Test sustainability assessment Excel export."""
        assessment_data = {
            "weighted_score": "72.5",
            "rating": "excellent",
            "estimated_rent_premium_percent": 5.5,
            "estimated_value_premium_percent": 8.2,
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/sustainability/assessment?format=excel&assessment_type=breeam",
            headers=auth_headers,
            json=assessment_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:2] == b'PK'

    def test_stranded_assets_export_pdf(self, auth_headers):
        """Test stranded assets PDF export."""
        analysis_data = {
            "stranding_risk_score": 0.65,
            "risk_category": "high",
            "stranded_volume_pct": 25.5,
            "npv_impact": 15000000,
            "key_drivers": ["Policy risk", "Technology obsolescence"],
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/stranded-assets/analysis?format=pdf",
            headers=auth_headers,
            json=analysis_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF'

    def test_nature_risk_export_pdf(self, auth_headers):
        """Test nature risk assessment PDF export."""
        assessment_data = {
            "total_score": 3.5,
            "rating": "moderate",
            "estimated_rent_premium_percent": 2.5,
            "estimated_value_premium_percent": 4.0,
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/nature-risk/assessment?format=pdf",
            headers=auth_headers,
            json=assessment_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF'

    def test_valuation_export_pdf(self, auth_headers):
        """Test valuation analysis PDF export."""
        valuation_data = {
            "property_name": "Test Office Tower",
            "indicated_value": 45000000,
            "noi": 3500000,
            "cap_rate": 0.078,
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/valuation/analysis?format=pdf&valuation_type=dcf",
            headers=auth_headers,
            json=valuation_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF'

    def test_carbon_export_pdf(self, auth_headers):
        """Test carbon calculation PDF export."""
        calc_data = {
            "total_credits": 50000,
            "portfolio_value_usd": 750000,
            "total_value": 825000,
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/carbon/calculation?format=pdf",
            headers=auth_headers,
            json=calc_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF'

    def test_scenario_analysis_export_pdf(self, auth_headers):
        """Test scenario analysis PDF export."""
        comparison_data = {
            "comparison_table": [
                {"scenario_name": "Base Case", "total_value": 100000000, "value_change_pct": 0, "avg_risk_score": 45, "var_95": 5000000},
                {"scenario_name": "Growth", "total_value": 115000000, "value_change_pct": 15, "avg_risk_score": 42, "var_95": 6000000},
            ],
            "best_scenario": "Growth",
            "worst_scenario": "Base Case",
            "value_spread": 15000000,
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/exports/scenario-analysis/comparison?format=pdf",
            headers=auth_headers,
            json=comparison_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF'


class TestExportEndpointsList:
    """Test the bulk export endpoint info."""

    def test_get_available_exports(self, auth_headers):
        """Test getting list of available exports."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/bulk",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "exports" in data
        assert len(data["exports"]) > 0

    def test_exports_list_has_portfolio_analytics(self, auth_headers):
        """Test exports list includes portfolio analytics."""
        response = requests.get(
            f"{BASE_URL}/api/v1/exports/bulk",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        modules = [e["module"] for e in data["exports"]]
        assert "portfolio_analytics" in modules
