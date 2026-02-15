"""
Scenario Builder API Tests
Tests NGFS integration, scenario CRUD, versioning, approval workflow, and impact calculation.
"""
import pytest
import requests
import os
import time

# Get API URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

if not BASE_URL:
    # Fallback for direct execution
    BASE_URL = "https://climate-risk-deploy.preview.emergentagent.com"


class TestHealthCheck:
    """Health check endpoint test"""
    
    def test_api_health(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health check passed: {data}")


class TestNGFSDataSources:
    """NGFS Data Source management tests"""
    
    def test_get_ngfs_sources(self):
        """GET /api/v1/scenarios/ngfs/sources - List all NGFS sources"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/ngfs/sources")
        assert response.status_code == 200
        sources = response.json()
        assert isinstance(sources, list)
        print(f"✅ NGFS sources retrieved: {len(sources)} sources")
        
        # Validate source structure if sources exist
        if len(sources) > 0:
            source = sources[0]
            assert "id" in source
            assert "name" in source
            assert "version" in source
            assert "last_sync_status" in source
            assert "scenario_count" in source
            print(f"✅ Source structure valid: {source['name']} (v{source['version']})")
        
        return sources

    def test_create_ngfs_source(self):
        """POST /api/v1/scenarios/ngfs/sources - Create/update NGFS source"""
        # This should create or update the source (idempotent based on version)
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios/ngfs/sources",
            params={
                "name": "NGFS Phase V Test",
                "version": "5.1-test",
                "url": "https://data.ece.iiasa.ac.at/ngfs/"
            }
        )
        # Should be 201 Created
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        source = response.json()
        assert source["name"] == "NGFS Phase V Test"
        assert source["version"] == "5.1-test"
        print(f"✅ NGFS source created: {source['id']}")
        return source


class TestNGFSSync:
    """NGFS data synchronization tests"""
    
    def test_sync_ngfs_data(self):
        """POST /api/v1/scenarios/ngfs/sync - Sync NGFS scenarios"""
        # First get existing sources
        sources_response = requests.get(f"{BASE_URL}/api/v1/scenarios/ngfs/sources")
        sources = sources_response.json()
        
        if len(sources) == 0:
            # Create a source first
            create_response = requests.post(
                f"{BASE_URL}/api/v1/scenarios/ngfs/sources",
                params={"name": "NGFS Phase V", "version": "5.0"}
            )
            source_id = create_response.json()["id"]
        else:
            source_id = sources[0]["id"]
        
        # Trigger sync
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios/ngfs/sync",
            params={"source_id": source_id}
        )
        assert response.status_code == 200, f"Sync failed: {response.text}"
        data = response.json()
        
        # Could be immediate result or background task message
        if "message" in data:
            print(f"✅ NGFS sync triggered: {data['message']}")
        else:
            print(f"✅ NGFS sync completed: {data.get('scenarios_created', 0)} created, {data.get('scenarios_updated', 0)} updated")
        
        return data


class TestScenarioTemplates:
    """NGFS scenario templates tests"""
    
    def test_get_templates(self):
        """GET /api/v1/scenarios/templates - Get NGFS scenario templates"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/templates")
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        
        print(f"✅ Templates retrieved: {len(templates)} templates")
        
        # Should have NGFS templates
        assert len(templates) > 0, "Expected at least one template"
        
        # Validate template structure
        template = templates[0]
        assert "id" in template
        assert "name" in template
        assert "description" in template
        assert "ngfs_scenario_type" in template
        assert "parameters" in template
        
        # Validate parameters structure
        params = template["parameters"]
        assert "carbon_price" in params
        assert "temperature_pathway" in params
        assert "gdp_impact" in params
        
        print(f"✅ Template structure valid: {template['name']}")
        print(f"   - Type: {template['ngfs_scenario_type']}")
        print(f"   - Carbon Price 2050: ${params['carbon_price'].get('2050', 'N/A')}/tCO2")
        print(f"   - Temperature 2050: +{params['temperature_pathway'].get('2050', 'N/A')}°C")
        
        return templates


class TestScenarioCRUD:
    """Scenario Create, Read, Update, Delete tests"""
    
    @pytest.fixture
    def template_id(self):
        """Get a template ID to fork from"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/templates")
        templates = response.json()
        if len(templates) == 0:
            pytest.skip("No templates available - run NGFS sync first")
        return templates[0]["id"]
    
    def test_list_scenarios(self):
        """GET /api/v1/scenarios - List all scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert isinstance(scenarios, list)
        print(f"✅ Scenarios listed: {len(scenarios)} scenarios")
        
        # Validate scenario structure if scenarios exist
        if len(scenarios) > 0:
            scenario = scenarios[0]
            assert "id" in scenario
            assert "name" in scenario
            assert "source" in scenario
            assert "approval_status" in scenario
            assert "parameters" in scenario
            print(f"✅ Scenario structure valid: {scenario['name']}")
        
        return scenarios
    
    def test_list_scenarios_with_filters(self):
        """GET /api/v1/scenarios with query filters"""
        # Filter by published only
        response = requests.get(f"{BASE_URL}/api/v1/scenarios", params={"published_only": True})
        assert response.status_code == 200
        published = response.json()
        
        # All should be published
        for s in published:
            assert s["is_published"] == True, f"Non-published scenario in filtered results: {s['id']}"
        
        print(f"✅ Published filter working: {len(published)} published scenarios")
    
    def test_create_custom_scenario(self):
        """POST /api/v1/scenarios - Create a new custom scenario"""
        scenario_data = {
            "name": "TEST_Custom Scenario",
            "description": "Test custom scenario for API validation",
            "source": "custom",
            "parameters": {
                "carbon_price": {"2025": 80, "2030": 200, "2040": 400, "2050": 700},
                "temperature_pathway": {"2025": 1.2, "2030": 1.4, "2040": 1.6, "2050": 1.8},
                "gdp_impact": {"2025": -0.3, "2030": -0.8, "2040": -1.5, "2050": -2.0},
                "sectoral_multipliers": {"energy": 1.5, "transport": 1.3},
                "physical_risk": {"flood": 1.1}
            },
            "created_by": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json=scenario_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 201, f"Create failed: {response.text}"
        created = response.json()
        
        assert created["name"] == scenario_data["name"]
        assert created["source"] == "custom"
        assert created["approval_status"] == "draft"
        assert created["current_version"] == 1
        
        print(f"✅ Custom scenario created: {created['id']}")
        
        # Verify by GET
        get_response = requests.get(f"{BASE_URL}/api/v1/scenarios/{created['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == scenario_data["name"]
        print(f"✅ Scenario verified via GET: {fetched['id']}")
        
        return created
    
    def test_get_scenario_by_id(self):
        """GET /api/v1/scenarios/{id} - Get scenario by ID"""
        # First get list
        scenarios = requests.get(f"{BASE_URL}/api/v1/scenarios").json()
        if len(scenarios) == 0:
            pytest.skip("No scenarios available")
        
        scenario_id = scenarios[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/{scenario_id}")
        assert response.status_code == 200
        scenario = response.json()
        assert scenario["id"] == scenario_id
        print(f"✅ Got scenario by ID: {scenario['name']}")
    
    def test_get_scenario_not_found(self):
        """GET /api/v1/scenarios/{id} - Returns 404 for non-existent ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/non-existent-id")
        assert response.status_code == 404
        print(f"✅ 404 returned for non-existent scenario")
    
    def test_update_draft_scenario(self):
        """PATCH /api/v1/scenarios/{id} - Update a draft scenario"""
        # Create a new draft scenario
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json={
                "name": "TEST_Update Scenario",
                "description": "Scenario for update test",
                "source": "custom",
                "parameters": {
                    "carbon_price": {"2025": 50, "2030": 100, "2040": 200, "2050": 400},
                    "temperature_pathway": {"2025": 1.2, "2030": 1.5, "2040": 1.8, "2050": 2.0},
                    "gdp_impact": {"2025": -0.2, "2030": -0.5, "2040": -1.0, "2050": -1.5},
                    "sectoral_multipliers": {},
                    "physical_risk": {}
                },
                "created_by": "test_user"
            }
        )
        
        assert create_response.status_code == 201
        created = create_response.json()
        scenario_id = created["id"]
        
        # Update the scenario
        update_data = {
            "name": "TEST_Updated Scenario Name",
            "description": "Updated description",
            "parameters": {
                "carbon_price": {"2025": 60, "2030": 150, "2040": 300, "2050": 600},
                "temperature_pathway": {"2025": 1.1, "2030": 1.3, "2040": 1.5, "2050": 1.7},
                "gdp_impact": {"2025": -0.25, "2030": -0.6, "2040": -1.2, "2050": -1.8},
                "sectoral_multipliers": {"energy": 1.8},
                "physical_risk": {}
            },
            "change_summary": "Updated parameters for testing"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        updated = response.json()
        
        assert updated["name"] == update_data["name"]
        assert updated["current_version"] == 2  # Version incremented
        
        # Verify via GET
        get_response = requests.get(f"{BASE_URL}/api/v1/scenarios/{scenario_id}")
        fetched = get_response.json()
        assert fetched["name"] == update_data["name"]
        assert fetched["current_version"] == 2
        
        print(f"✅ Scenario updated: {updated['name']} (v{updated['current_version']})")
        
        return updated
    
    def test_delete_draft_scenario(self):
        """DELETE /api/v1/scenarios/{id} - Delete a draft scenario"""
        # Create a new scenario to delete
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json={
                "name": "TEST_To Delete",
                "description": "Scenario to be deleted",
                "source": "custom",
                "parameters": {
                    "carbon_price": {"2025": 50},
                    "temperature_pathway": {"2025": 1.2},
                    "gdp_impact": {"2025": -0.2},
                    "sectoral_multipliers": {},
                    "physical_risk": {}
                }
            }
        )
        
        assert create_response.status_code == 201
        scenario_id = create_response.json()["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/v1/scenarios/{scenario_id}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = requests.get(f"{BASE_URL}/api/v1/scenarios/{scenario_id}")
        assert get_response.status_code == 404
        
        print(f"✅ Draft scenario deleted: {scenario_id}")


class TestScenarioFork:
    """Scenario fork (copy) tests"""
    
    def test_fork_ngfs_template(self):
        """POST /api/v1/scenarios/{id}/fork - Fork an NGFS template"""
        # Get templates
        templates_response = requests.get(f"{BASE_URL}/api/v1/scenarios/templates")
        templates = templates_response.json()
        
        if len(templates) == 0:
            pytest.skip("No templates available for forking")
        
        template = templates[0]
        template_id = template["id"]
        
        fork_data = {
            "new_name": f"TEST_Forked {template['name']}",
            "description": "Forked scenario for testing",
            "created_by": "test_forker"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios/{template_id}/fork",
            json=fork_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 201, f"Fork failed: {response.text}"
        forked = response.json()
        
        assert forked["name"] == fork_data["new_name"]
        assert forked["base_scenario_id"] == template_id
        assert forked["source"] == "hybrid"  # NGFS fork becomes hybrid
        assert forked["approval_status"] == "draft"
        
        # Verify parameters were copied
        assert "carbon_price" in forked["parameters"]
        assert "temperature_pathway" in forked["parameters"]
        
        print(f"✅ Template forked: {forked['id']} (base: {template_id})")
        
        return forked


class TestApprovalWorkflow:
    """Approval workflow tests"""
    
    def test_submit_for_approval(self):
        """POST /api/v1/scenarios/{id}/submit-for-approval - Submit draft for approval"""
        # Create a draft scenario
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json={
                "name": "TEST_For Approval",
                "description": "Scenario to submit for approval",
                "source": "custom",
                "parameters": {
                    "carbon_price": {"2025": 75, "2030": 180, "2040": 350, "2050": 600},
                    "temperature_pathway": {"2025": 1.15, "2030": 1.35, "2040": 1.55, "2050": 1.75},
                    "gdp_impact": {"2025": -0.25, "2030": -0.7, "2040": -1.3, "2050": -1.9},
                    "sectoral_multipliers": {"energy": 1.6},
                    "physical_risk": {}
                },
                "created_by": "analyst_test"
            }
        )
        
        assert create_response.status_code == 201
        scenario = create_response.json()
        scenario_id = scenario["id"]
        
        # Submit for approval
        submit_data = {
            "submitted_by": "analyst_test",
            "notes": "Ready for review - test submission"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}/submit-for-approval",
            json=submit_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Submit failed: {response.text}"
        submitted = response.json()
        
        assert submitted["approval_status"] == "pending_approval"
        assert submitted["submitted_by"] == submit_data["submitted_by"]
        assert submitted["submitted_at"] is not None
        
        print(f"✅ Scenario submitted for approval: {scenario_id}")
        
        return submitted
    
    def test_approve_scenario(self):
        """POST /api/v1/scenarios/{id}/approve - Approve a pending scenario"""
        # Create and submit a scenario
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json={
                "name": "TEST_To Approve",
                "description": "Scenario for approval test",
                "source": "custom",
                "parameters": {
                    "carbon_price": {"2025": 70},
                    "temperature_pathway": {"2025": 1.2},
                    "gdp_impact": {"2025": -0.3},
                    "sectoral_multipliers": {},
                    "physical_risk": {}
                }
            }
        )
        scenario_id = create_response.json()["id"]
        
        # Submit for approval
        requests.post(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}/submit-for-approval",
            json={"submitted_by": "analyst", "notes": ""}
        )
        
        # Approve
        approve_data = {
            "approved": True,
            "approved_by": "risk_manager_test",
            "notes": "Approved for testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}/approve",
            json=approve_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Approval failed: {response.text}"
        approved = response.json()
        
        assert approved["approval_status"] == "approved"
        assert approved["approved_by"] == approve_data["approved_by"]
        assert approved["approved_at"] is not None
        
        print(f"✅ Scenario approved: {scenario_id}")
        
        return approved
    
    def test_reject_scenario(self):
        """POST /api/v1/scenarios/{id}/approve - Reject a pending scenario"""
        # Create and submit a scenario
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json={
                "name": "TEST_To Reject",
                "description": "Scenario for rejection test",
                "source": "custom",
                "parameters": {
                    "carbon_price": {"2025": 70},
                    "temperature_pathway": {"2025": 1.2},
                    "gdp_impact": {"2025": -0.3},
                    "sectoral_multipliers": {},
                    "physical_risk": {}
                }
            }
        )
        scenario_id = create_response.json()["id"]
        
        # Submit
        requests.post(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}/submit-for-approval",
            json={"submitted_by": "analyst", "notes": ""}
        )
        
        # Reject
        reject_data = {
            "approved": False,
            "approved_by": "risk_manager_test",
            "notes": "Parameters need revision"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}/approve",
            json=reject_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Rejection failed: {response.text}"
        rejected = response.json()
        
        assert rejected["approval_status"] == "rejected"
        
        print(f"✅ Scenario rejected: {scenario_id}")


class TestPublish:
    """Scenario publish tests"""
    
    def test_publish_approved_scenario(self):
        """POST /api/v1/scenarios/{id}/publish - Publish an approved scenario"""
        # Create, submit, and approve a scenario
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json={
                "name": "TEST_To Publish",
                "description": "Scenario for publish test",
                "source": "custom",
                "parameters": {
                    "carbon_price": {"2025": 85},
                    "temperature_pathway": {"2025": 1.1},
                    "gdp_impact": {"2025": -0.2},
                    "sectoral_multipliers": {},
                    "physical_risk": {}
                }
            }
        )
        scenario_id = create_response.json()["id"]
        
        # Submit
        requests.post(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}/submit-for-approval",
            json={"submitted_by": "analyst", "notes": ""}
        )
        
        # Approve
        requests.post(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}/approve",
            json={"approved": True, "approved_by": "manager", "notes": ""}
        )
        
        # Publish
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/{scenario_id}/publish")
        
        assert response.status_code == 200, f"Publish failed: {response.text}"
        published = response.json()
        
        assert published["is_published"] == True
        
        # Verify via GET
        get_response = requests.get(f"{BASE_URL}/api/v1/scenarios/{scenario_id}")
        assert get_response.json()["is_published"] == True
        
        print(f"✅ Scenario published: {scenario_id}")


class TestVersioning:
    """Scenario version history tests"""
    
    def test_get_scenario_versions(self):
        """GET /api/v1/scenarios/{id}/versions - Get version history"""
        # Create a scenario
        create_response = requests.post(
            f"{BASE_URL}/api/v1/scenarios",
            json={
                "name": "TEST_Version Test",
                "description": "Scenario for versioning test",
                "source": "custom",
                "parameters": {
                    "carbon_price": {"2025": 50},
                    "temperature_pathway": {"2025": 1.2},
                    "gdp_impact": {"2025": -0.2},
                    "sectoral_multipliers": {},
                    "physical_risk": {}
                }
            }
        )
        scenario_id = create_response.json()["id"]
        
        # Update it to create version 2
        requests.patch(
            f"{BASE_URL}/api/v1/scenarios/{scenario_id}",
            json={
                "parameters": {
                    "carbon_price": {"2025": 60},
                    "temperature_pathway": {"2025": 1.3},
                    "gdp_impact": {"2025": -0.25},
                    "sectoral_multipliers": {},
                    "physical_risk": {}
                },
                "change_summary": "Updated carbon price"
            }
        )
        
        # Get versions
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/{scenario_id}/versions")
        assert response.status_code == 200
        versions = response.json()
        
        assert isinstance(versions, list)
        assert len(versions) >= 2  # Should have at least 2 versions
        
        # Verify version structure
        for version in versions:
            assert "id" in version
            assert "scenario_id" in version
            assert "version_number" in version
            assert "parameters" in version
            assert "created_at" in version
        
        print(f"✅ Got {len(versions)} versions for scenario {scenario_id}")
        
        return versions


class TestCleanup:
    """Cleanup test data after tests"""
    
    def test_cleanup_test_scenarios(self):
        """Delete all TEST_ prefixed scenarios"""
        # Get all scenarios
        response = requests.get(f"{BASE_URL}/api/v1/scenarios")
        scenarios = response.json()
        
        deleted_count = 0
        for scenario in scenarios:
            if scenario["name"].startswith("TEST_") and scenario["approval_status"] == "draft":
                delete_response = requests.delete(f"{BASE_URL}/api/v1/scenarios/{scenario['id']}")
                if delete_response.status_code == 204:
                    deleted_count += 1
        
        print(f"✅ Cleanup: Deleted {deleted_count} test scenarios")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
