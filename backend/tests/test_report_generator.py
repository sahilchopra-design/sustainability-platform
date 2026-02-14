"""
Test suite for Report Generator endpoints.
Tests: POST /api/v1/analysis/reports/generate (PDF, Excel, CSV)
       GET /api/v1/analysis/reports/download/{filename}
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test scenario and portfolio IDs from existing data (from previous tests)
SCENARIO_WITCH = "ad7292d6-72cd-4fcd-82a9-1d09fa6163ef"  # WITCH 1.5C
PORTFOLIO_SAMPLE = "698fc3f3a10cb92034afa4bf"  # Sample Portfolio (16 assets)
PORTFOLIO_EMPTY = "698fc53fa10cb92034afa552"  # UI Test Portfolio (0 assets)


class TestReportGeneratePDF:
    """Test PDF report generation via POST /api/v1/analysis/reports/generate"""

    def test_generate_pdf_returns_filename_and_download_url(self):
        """Generate PDF report returns filename with .pdf extension and download_url."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "pdf",
                "horizons": [2030, 2040, 2050]
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "filename" in data
        assert "format" in data
        assert "download_url" in data
        
        # Verify PDF format
        assert data["filename"].endswith(".pdf")
        assert data["format"] == "pdf"
        assert data["download_url"].startswith("/api/v1/analysis/reports/download/")
        assert data["download_url"].endswith(".pdf")
        
        # Store for download test
        TestReportGeneratePDF.pdf_filename = data["filename"]
        TestReportGeneratePDF.download_url = data["download_url"]


class TestReportGenerateExcel:
    """Test Excel report generation via POST /api/v1/analysis/reports/generate"""

    def test_generate_excel_returns_xlsx_filename(self):
        """Generate Excel report returns filename with .xlsx extension."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "excel"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify Excel format
        assert data["filename"].endswith(".xlsx")
        assert data["format"] in ("excel", "xlsx")
        assert data["download_url"].endswith(".xlsx")
        
        # Store for download test
        TestReportGenerateExcel.excel_filename = data["filename"]


class TestReportGenerateCSV:
    """Test CSV report generation via POST /api/v1/analysis/reports/generate"""

    def test_generate_csv_returns_csv_filename(self):
        """Generate CSV report returns filename with .csv extension."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "csv"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify CSV format
        assert data["filename"].endswith(".csv")
        assert data["format"] == "csv"
        assert data["download_url"].endswith(".csv")
        
        # Store for download test
        TestReportGenerateCSV.csv_filename = data["filename"]


class TestReportDownload:
    """Test GET /api/v1/analysis/reports/download/{filename}"""

    def test_download_pdf_returns_actual_file(self):
        """Download PDF returns actual PDF file with correct content-type."""
        # First generate a PDF
        gen_response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "pdf"
            }
        )
        assert gen_response.status_code == 200
        filename = gen_response.json()["filename"]
        
        # Download the PDF
        download_response = requests.get(
            f"{BASE_URL}/api/v1/analysis/reports/download/{filename}",
            stream=True
        )
        assert download_response.status_code == 200
        
        # Verify content-type
        content_type = download_response.headers.get("content-type", "")
        assert "application/pdf" in content_type
        
        # Verify file is non-empty (PDF should have content)
        content = download_response.content
        assert len(content) > 0, "PDF file should not be empty"
        
        # PDF files start with %PDF
        assert content[:4] == b"%PDF", "File should be a valid PDF"

    def test_download_excel_returns_actual_file(self):
        """Download Excel returns actual xlsx file."""
        # First generate an Excel
        gen_response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "excel"
            }
        )
        assert gen_response.status_code == 200
        filename = gen_response.json()["filename"]
        
        # Download the Excel
        download_response = requests.get(
            f"{BASE_URL}/api/v1/analysis/reports/download/{filename}",
            stream=True
        )
        assert download_response.status_code == 200
        
        # Verify content-type
        content_type = download_response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "xlsx" in content_type.lower() or "vnd.openxmlformats" in content_type
        
        # Verify file is non-empty
        content = download_response.content
        assert len(content) > 0, "Excel file should not be empty"
        
        # XLSX files are ZIP archives starting with PK
        assert content[:2] == b"PK", "File should be a valid XLSX (ZIP archive)"

    def test_download_csv_returns_actual_file(self):
        """Download CSV returns actual CSV file."""
        # First generate a CSV
        gen_response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "csv"
            }
        )
        assert gen_response.status_code == 200
        filename = gen_response.json()["filename"]
        
        # Download the CSV
        download_response = requests.get(
            f"{BASE_URL}/api/v1/analysis/reports/download/{filename}",
            stream=True
        )
        assert download_response.status_code == 200
        
        # Verify content-type
        content_type = download_response.headers.get("content-type", "")
        assert "text/csv" in content_type or "text/plain" in content_type
        
        # Verify file is non-empty and is CSV
        content = download_response.content.decode("utf-8")
        assert len(content) > 0, "CSV file should not be empty"
        
        # CSV should contain "Climate Risk Impact Report" header
        assert "Climate Risk Impact Report" in content

    def test_download_returns_404_for_nonexistent_file(self):
        """Download returns 404 for non-existent file."""
        fake_filename = f"nonexistent_report_{uuid.uuid4().hex[:8]}.pdf"
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/reports/download/{fake_filename}"
        )
        assert response.status_code == 404


class TestReportGenerateErrors:
    """Test error handling for report generation"""

    def test_generate_returns_404_for_invalid_portfolio(self):
        """Generate report returns 404 for non-existent portfolio."""
        fake_portfolio_id = "000000000000000000000000"  # Invalid ObjectId
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": fake_portfolio_id,
                "format": "pdf"
            }
        )
        assert response.status_code == 404

    def test_generate_returns_400_for_empty_portfolio(self):
        """Generate report returns 400 for portfolio with no assets."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_EMPTY,
                "format": "pdf"
            }
        )
        assert response.status_code == 400

    def test_generate_returns_400_for_unsupported_format(self):
        """Generate report returns 400 for unsupported format."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "docx"  # Not supported
            }
        )
        assert response.status_code == 400

    def test_generate_returns_404_for_invalid_scenario(self):
        """Generate report returns 404 for non-existent scenario."""
        fake_scenario_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/reports/generate",
            json={
                "scenario_id": fake_scenario_id,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "format": "pdf"
            }
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
