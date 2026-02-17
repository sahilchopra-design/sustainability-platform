"""
Test Scheduled Reports API - CRUD operations
Tests for: Create, List, Toggle, Delete endpoints
"""
import pytest
import requests
import os
from uuid import uuid4

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestScheduledReportsAPI:
    """Test Scheduled Reports CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for tests"""
        self.created_report_ids = []
        yield
        # Cleanup test data
        for report_id in self.created_report_ids:
            try:
                requests.delete(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}")
            except:
                pass
    
    # ========== CREATE Tests ==========
    
    def test_create_scheduled_report_returns_200(self):
        """POST /api/v1/scheduled-reports returns 200/201 with valid data"""
        payload = {
            "name": "TEST_Weekly Portfolio Report",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        if "id" in data:
            self.created_report_ids.append(data["id"])
    
    def test_create_scheduled_report_returns_id(self):
        """Created report has ID"""
        payload = {
            "name": "TEST_Report With ID",
            "report_type": "carbon_credits",
            "frequency": "monthly",
            "recipients": ["analyst@company.com"],
            "format": "excel"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        data = response.json()
        assert "id" in data, "Response should contain id"
        assert isinstance(data["id"], str) and len(data["id"]) > 0
        self.created_report_ids.append(data["id"])
    
    def test_create_report_with_all_report_types(self):
        """Test creating reports with different report types"""
        report_types = [
            "portfolio_analytics", "carbon_credits", "stranded_assets",
            "nature_risk", "sustainability", "valuation", "scenario_analysis"
        ]
        for rt in report_types:
            payload = {
                "name": f"TEST_{rt}_Report",
                "report_type": rt,
                "frequency": "weekly",
                "recipients": ["test@example.com"],
                "format": "pdf"
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/scheduled-reports",
                json=payload
            )
            assert response.status_code in [200, 201], f"Failed for report_type={rt}: {response.text}"
            data = response.json()
            assert data["report_type"] == rt
            self.created_report_ids.append(data["id"])
    
    def test_create_report_with_all_frequencies(self):
        """Test creating reports with different frequencies"""
        frequencies = ["daily", "weekly", "monthly", "quarterly"]
        for freq in frequencies:
            payload = {
                "name": f"TEST_{freq}_Report",
                "report_type": "portfolio_analytics",
                "frequency": freq,
                "recipients": ["test@example.com"],
                "format": "pdf"
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/scheduled-reports",
                json=payload
            )
            assert response.status_code in [200, 201], f"Failed for frequency={freq}: {response.text}"
            data = response.json()
            assert data["frequency"] == freq
            self.created_report_ids.append(data["id"])
    
    def test_create_report_with_multiple_recipients(self):
        """Test creating report with multiple email recipients"""
        payload = {
            "name": "TEST_Multi Recipient Report",
            "report_type": "sustainability",
            "frequency": "weekly",
            "recipients": ["user1@example.com", "user2@example.com", "user3@example.com"],
            "format": "pdf"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        data = response.json()
        assert response.status_code in [200, 201]
        assert len(data["recipients"]) == 3
        self.created_report_ids.append(data["id"])
    
    def test_create_report_has_next_run_calculated(self):
        """Created report should have next_run calculated"""
        payload = {
            "name": "TEST_Report With NextRun",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        data = response.json()
        assert "next_run" in data
        assert data["next_run"] is not None, "next_run should be calculated"
        self.created_report_ids.append(data["id"])
    
    def test_create_report_is_active_by_default(self):
        """Created report should be active by default"""
        payload = {
            "name": "TEST_Active By Default",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        data = response.json()
        assert data["is_active"] == True
        self.created_report_ids.append(data["id"])
    
    # ========== LIST Tests ==========
    
    def test_list_scheduled_reports_returns_200(self):
        """GET /api/v1/scheduled-reports returns 200"""
        response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_list_scheduled_reports_returns_items_array(self):
        """List returns items array"""
        response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        assert isinstance(data["items"], list)
    
    def test_list_scheduled_reports_returns_total(self):
        """List returns total count"""
        response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        data = response.json()
        assert "total" in data, "Response should have 'total' field"
        assert isinstance(data["total"], int)
    
    def test_created_report_appears_in_list(self):
        """Created report should appear in list"""
        # Create a report first
        payload = {
            "name": "TEST_Appears In List",
            "report_type": "nature_risk",
            "frequency": "daily",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        created_id = create_response.json()["id"]
        self.created_report_ids.append(created_id)
        
        # List and verify
        list_response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        data = list_response.json()
        
        report_ids = [item["id"] for item in data["items"]]
        assert created_id in report_ids, "Created report should appear in list"
    
    def test_list_items_have_required_fields(self):
        """Listed items have required fields"""
        response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        data = response.json()
        
        if data["items"]:
            item = data["items"][0]
            required_fields = ["id", "name", "report_type", "frequency", "recipients", "format", "is_active"]
            for field in required_fields:
                assert field in item, f"Missing required field: {field}"
    
    # ========== TOGGLE Tests ==========
    
    def test_toggle_report_returns_200(self):
        """POST /api/v1/scheduled-reports/{id}/toggle returns 200"""
        # Create a report first
        payload = {
            "name": "TEST_Toggle Report",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        report_id = create_response.json()["id"]
        self.created_report_ids.append(report_id)
        
        # Toggle
        toggle_response = requests.post(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}/toggle")
        assert toggle_response.status_code == 200, f"Expected 200, got {toggle_response.status_code}"
    
    def test_toggle_changes_is_active_status(self):
        """Toggle changes is_active from true to false"""
        # Create a report (is_active=true by default)
        payload = {
            "name": "TEST_Toggle Status",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        data = create_response.json()
        report_id = data["id"]
        self.created_report_ids.append(report_id)
        assert data["is_active"] == True, "Initially should be active"
        
        # Toggle to inactive
        toggle_response = requests.post(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}/toggle")
        toggled_data = toggle_response.json()
        assert toggled_data["is_active"] == False, "After toggle should be inactive"
        
        # Toggle back to active
        toggle_response2 = requests.post(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}/toggle")
        toggled_data2 = toggle_response2.json()
        assert toggled_data2["is_active"] == True, "After second toggle should be active again"
    
    def test_toggle_nonexistent_report_returns_404(self):
        """Toggle non-existent report returns 404"""
        fake_id = str(uuid4())
        response = requests.post(f"{BASE_URL}/api/v1/scheduled-reports/{fake_id}/toggle")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    # ========== DELETE Tests ==========
    
    def test_delete_report_returns_200(self):
        """DELETE /api/v1/scheduled-reports/{id} returns 200"""
        # Create a report first
        payload = {
            "name": "TEST_Delete Report",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        report_id = create_response.json()["id"]
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
    
    def test_delete_removes_from_list(self):
        """Deleted report no longer appears in list"""
        # Create a report
        payload = {
            "name": "TEST_Delete From List",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        report_id = create_response.json()["id"]
        
        # Delete
        requests.delete(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}")
        
        # Verify not in list
        list_response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports")
        data = list_response.json()
        report_ids = [item["id"] for item in data["items"]]
        assert report_id not in report_ids, "Deleted report should not appear in list"
    
    def test_delete_nonexistent_report_returns_404(self):
        """Delete non-existent report returns 404"""
        fake_id = str(uuid4())
        response = requests.delete(f"{BASE_URL}/api/v1/scheduled-reports/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    # ========== GET BY ID Tests ==========
    
    def test_get_report_by_id_returns_200(self):
        """GET /api/v1/scheduled-reports/{id} returns 200"""
        # Create a report first
        payload = {
            "name": "TEST_Get By ID",
            "report_type": "portfolio_analytics",
            "frequency": "weekly",
            "recipients": ["test@example.com"],
            "format": "pdf"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        report_id = create_response.json()["id"]
        self.created_report_ids.append(report_id)
        
        # Get by ID
        get_response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}")
        assert get_response.status_code == 200, f"Expected 200, got {get_response.status_code}"
    
    def test_get_report_returns_correct_data(self):
        """GET by ID returns correct data"""
        payload = {
            "name": "TEST_Correct Data",
            "report_type": "stranded_assets",
            "frequency": "monthly",
            "recipients": ["user@test.com"],
            "format": "excel"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scheduled-reports",
            json=payload
        )
        created = create_response.json()
        report_id = created["id"]
        self.created_report_ids.append(report_id)
        
        # Get and verify
        get_response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports/{report_id}")
        data = get_response.json()
        
        assert data["name"] == payload["name"]
        assert data["report_type"] == payload["report_type"]
        assert data["frequency"] == payload["frequency"]
        assert data["format"] == payload["format"]
    
    def test_get_nonexistent_report_returns_404(self):
        """GET non-existent report returns 404"""
        fake_id = str(uuid4())
        response = requests.get(f"{BASE_URL}/api/v1/scheduled-reports/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
