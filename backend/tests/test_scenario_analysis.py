"""
Scenario Analysis Module - Backend API Tests
Tests for Interactive Scenario Builder, Sensitivity Analysis, What-If Analysis, and Scenario Comparison
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestScenarioAnalysisDashboard:
    """Test Dashboard endpoint"""

    def test_dashboard_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/dashboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Dashboard endpoint returns 200")

    def test_dashboard_has_required_fields(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/dashboard")
        data = response.json()
        assert "total_scenarios" in data
        assert "total_analyses" in data
        assert "recent_scenarios" in data
        assert "most_impactful_variables" in data
        assert "avg_value_swing_pct" in data
        print(f"✓ Dashboard has all required fields: total_scenarios={data['total_scenarios']}")


class TestProperties:
    """Test Properties endpoint for property dropdown"""

    def test_properties_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Properties endpoint returns 200")

    def test_properties_returns_sample_data(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        data = response.json()
        assert "properties" in data
        assert len(data["properties"]) == 3, f"Expected 3 sample properties, got {len(data['properties'])}"
        print(f"✓ Properties returns 3 sample properties")

    def test_properties_have_required_fields(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        properties = response.json()["properties"]
        for prop in properties:
            assert "id" in prop
            assert "name" in prop
            assert "property_type" in prop
            assert "current_value" in prop
            assert "noi" in prop
            assert "cap_rate" in prop
        print(f"✓ All properties have required fields: {[p['name'] for p in properties]}")


class TestScenarioBuilder:
    """Test Scenario Builder - Build endpoint"""

    def setup_method(self):
        """Get a property ID for testing"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        self.property_id = response.json()["properties"][0]["id"]

    def test_build_scenario_returns_200(self):
        payload = {
            "base_property_id": self.property_id,
            "scenario_name": "TEST_Optimistic Case",
            "modifications": [
                {"type": "rent_growth", "parameter": "rent_growth_rate", "new_value": 0.04, "description": "Strong rent growth"}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Build scenario returns 200")

    def test_build_scenario_returns_values(self):
        payload = {
            "base_property_id": self.property_id,
            "scenario_name": "TEST_Value Check Scenario",
            "modifications": [
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.05, "description": "Cap rate compression"}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        data = response.json()
        assert "scenario_id" in data
        assert "base_value" in data
        assert "adjusted_value" in data
        assert "value_change" in data
        assert "value_change_pct" in data
        assert "component_impacts" in data
        print(f"✓ Build scenario returns all values: base={data['base_value']}, adjusted={data['adjusted_value']}")

    def test_build_scenario_with_multiple_modifications(self):
        payload = {
            "base_property_id": self.property_id,
            "scenario_name": "TEST_Multi-Mod Scenario",
            "modifications": [
                {"type": "rent_growth", "parameter": "rent_growth_rate", "new_value": 0.035},
                {"type": "vacancy", "parameter": "vacancy_rate", "new_value": 0.03},
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.052}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        data = response.json()
        assert response.status_code == 200
        assert len(data["component_impacts"]) == 3
        print(f"✓ Multi-modification scenario works: {len(data['component_impacts'])} impacts returned")

    def test_build_scenario_component_impacts_have_values(self):
        payload = {
            "base_property_id": self.property_id,
            "scenario_name": "TEST_Impact Check Scenario",
            "modifications": [
                {"type": "rent_growth", "parameter": "rent_growth_rate", "new_value": 0.04}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        data = response.json()
        impact = data["component_impacts"][0]
        assert "modification" in impact or "parameter" in impact
        assert "impact" in impact
        assert "impact_pct" in impact
        print(f"✓ Component impacts have values: impact_pct={impact['impact_pct']}%")


class TestScenarioTemplates:
    """Test Scenario Templates"""

    def test_templates_list_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/templates/list")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Templates list returns 200")

    def test_templates_list_has_templates(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/templates/list")
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) >= 4, f"Expected at least 4 templates, got {len(data['templates'])}"
        print(f"✓ Templates list has {len(data['templates'])} templates")

    def test_templates_have_required_fields(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/templates/list")
        templates = response.json()["templates"]
        for t in templates:
            assert "name" in t
            assert "description" in t
            assert "modifications" in t
            assert "category" in t
        print(f"✓ Templates have required fields: {[t['name'] for t in templates]}")

    def test_apply_template_returns_200(self):
        # Get property ID
        prop_response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        property_id = prop_response.json()["properties"][0]["id"]
        
        # Apply template
        response = requests.post(
            f"{BASE_URL}/api/v1/scenarios/templates/apply",
            params={"base_property_id": property_id, "template_name": "Optimistic Growth"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Apply template returns 200")


class TestSensitivityAnalysis:
    """Test Sensitivity Analysis endpoints"""

    def setup_method(self):
        """Get a property ID for testing"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        self.property_id = response.json()["properties"][0]["id"]

    def test_sensitivity_presets_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/v1/sensitivity/presets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Sensitivity presets returns 200")

    def test_sensitivity_presets_has_data(self):
        response = requests.get(f"{BASE_URL}/api/v1/sensitivity/presets")
        data = response.json()
        assert "presets" in data
        assert len(data["presets"]) >= 2
        print(f"✓ Sensitivity presets has {len(data['presets'])} presets")

    def test_sensitivity_analyze_returns_200(self):
        payload = {
            "property_id": self.property_id,
            "variables": [
                {"name": "cap_rate", "base_value": 0.055, "range": {"min": 0.04, "max": 0.07}, "steps": 10}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/sensitivity/analyze", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Sensitivity analyze returns 200")

    def test_sensitivity_analyze_returns_tornado_data(self):
        payload = {
            "property_id": self.property_id,
            "variables": [
                {"name": "cap_rate", "base_value": 0.055, "range": {"min": 0.04, "max": 0.07}, "steps": 10},
                {"name": "rent_growth", "base_value": 0.025, "range": {"min": 0.01, "max": 0.04}, "steps": 10}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/sensitivity/analyze", json=payload)
        data = response.json()
        assert "tornado_data" in data
        assert len(data["tornado_data"]) == 2
        tornado = data["tornado_data"][0]
        assert "variable" in tornado
        assert "low_impact" in tornado
        assert "high_impact" in tornado
        assert "swing" in tornado
        print(f"✓ Sensitivity analysis returns tornado data with {len(data['tornado_data'])} variables")

    def test_sensitivity_analyze_returns_spider_data(self):
        payload = {
            "property_id": self.property_id,
            "variables": [
                {"name": "cap_rate", "base_value": 0.055, "range": {"min": 0.04, "max": 0.07}, "steps": 10},
                {"name": "vacancy_rate", "base_value": 0.05, "range": {"min": 0.02, "max": 0.10}, "steps": 10}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/sensitivity/analyze", json=payload)
        data = response.json()
        assert "spider_chart_data" in data
        spider = data["spider_chart_data"]
        assert "variables" in spider
        assert "scenarios" in spider
        assert len(spider["scenarios"]) == 3  # Base, Optimistic, Pessimistic
        print(f"✓ Sensitivity analysis returns spider data with scenarios: {[s['name'] for s in spider['scenarios']]}")

    def test_tornado_endpoint_returns_200(self):
        payload = {
            "property_id": self.property_id,
            "base_valuation": 435000000,
            "variables": [
                {"name": "cap_rate", "base": 0.055, "low": 0.04, "high": 0.07}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/sensitivity/tornado", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Tornado endpoint returns 200")

    def test_spider_endpoint_returns_200(self):
        payload = {
            "property_id": self.property_id,
            "base_valuation": 435000000,
            "variables": ["cap_rate", "rent_growth", "vacancy_rate"]
        }
        response = requests.post(f"{BASE_URL}/api/v1/sensitivity/spider", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Spider endpoint returns 200")


class TestWhatIfAnalysis:
    """Test What-If Analysis endpoints"""

    def setup_method(self):
        """Get a property ID for testing"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        self.property_id = response.json()["properties"][0]["id"]

    def test_whatif_parameters_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/v1/what-if/parameters")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ What-If parameters returns 200")

    def test_whatif_parameters_has_data(self):
        response = requests.get(f"{BASE_URL}/api/v1/what-if/parameters")
        data = response.json()
        assert "parameters" in data
        assert "change_types" in data
        assert len(data["parameters"]) >= 5
        assert len(data["change_types"]) == 2  # absolute, percentage
        print(f"✓ What-If parameters has {len(data['parameters'])} parameters and {len(data['change_types'])} change types")

    def test_whatif_analyze_returns_200(self):
        payload = {
            "property_id": self.property_id,
            "changes": [
                {"parameter": "vacancy_rate", "change_type": "percentage", "change_value": 0.1}
            ],
            "cascade_effects": False
        }
        response = requests.post(f"{BASE_URL}/api/v1/what-if/analyze", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ What-If analyze returns 200")

    def test_whatif_analyze_returns_values(self):
        payload = {
            "property_id": self.property_id,
            "changes": [
                {"parameter": "cap_rate", "change_type": "percentage", "change_value": 0.1}
            ],
            "cascade_effects": False
        }
        response = requests.post(f"{BASE_URL}/api/v1/what-if/analyze", json=payload)
        data = response.json()
        assert "base_valuation" in data
        assert "adjusted_valuation" in data
        assert "total_change" in data
        assert "total_change_pct" in data
        assert "change_breakdown" in data
        assert "cascade_effects_applied" in data
        print(f"✓ What-If analyze returns values: base={data['base_valuation']}, adjusted={data['adjusted_valuation']}")

    def test_whatif_analyze_with_cascading_effects(self):
        payload = {
            "property_id": self.property_id,
            "changes": [
                {"parameter": "vacancy_rate", "change_type": "percentage", "change_value": 0.2}
            ],
            "cascade_effects": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/what-if/analyze", json=payload)
        data = response.json()
        assert response.status_code == 200
        assert data["cascade_effects_applied"] == True
        print(f"✓ What-If with cascading effects works: cascade_effects_applied={data['cascade_effects_applied']}")

    def test_whatif_analyze_multiple_changes(self):
        payload = {
            "property_id": self.property_id,
            "changes": [
                {"parameter": "vacancy_rate", "change_type": "percentage", "change_value": 0.1},
                {"parameter": "cap_rate", "change_type": "absolute", "change_value": 0.005}
            ],
            "cascade_effects": False
        }
        response = requests.post(f"{BASE_URL}/api/v1/what-if/analyze", json=payload)
        data = response.json()
        assert response.status_code == 200
        assert len(data["change_breakdown"]) == 2
        print(f"✓ What-If with multiple changes works: {len(data['change_breakdown'])} breakdown items")


class TestScenarioList:
    """Test Scenario List endpoint"""

    def test_scenario_list_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Scenario list returns 200")

    def test_scenario_list_structure(self):
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/list")
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Scenario list has {data['total']} scenarios")


class TestScenarioComparison:
    """Test Scenario Comparison endpoint"""

    def setup_method(self):
        """Create test scenarios for comparison"""
        response = requests.get(f"{BASE_URL}/api/v1/scenarios/properties")
        self.property_id = response.json()["properties"][0]["id"]
        
        # Create a test scenario
        payload = {
            "base_property_id": self.property_id,
            "scenario_name": "TEST_Comparison Scenario",
            "modifications": [
                {"type": "cap_rate", "parameter": "cap_rate", "new_value": 0.05}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/build", json=payload)
        self.scenario_id = response.json().get("scenario_id")

    def test_compare_scenarios_returns_200(self):
        if not self.scenario_id:
            pytest.skip("No scenario ID available for comparison test")
        
        payload = {
            "base_property_id": self.property_id,
            "scenario_ids": [self.scenario_id],
            "metrics": ["value", "noi", "cap_rate"]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/compare", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Compare scenarios returns 200")

    def test_compare_scenarios_returns_comparison_table(self):
        if not self.scenario_id:
            pytest.skip("No scenario ID available for comparison test")
        
        payload = {
            "base_property_id": self.property_id,
            "scenario_ids": [self.scenario_id],
            "metrics": ["value", "noi", "cap_rate"]
        }
        response = requests.post(f"{BASE_URL}/api/v1/scenarios/compare", json=payload)
        data = response.json()
        assert "comparison_table" in data
        assert "best_scenario" in data
        assert "worst_scenario" in data
        assert "key_differentiators" in data
        assert "base_value" in data
        print(f"✓ Compare scenarios returns comparison table with {len(data['comparison_table'])} rows")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
