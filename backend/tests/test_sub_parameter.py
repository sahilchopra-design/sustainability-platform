"""
Sub-Parameter Analysis Module Tests
Tests: sensitivity analysis (tornado charts), what-if testing, Shapley attribution, 
pairwise interaction analysis, and visualization endpoints.
Works with ALL 102 hub scenarios.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestParametersEndpoint:
    """Test GET /api/v1/sub-parameter/parameters - lists analyzable parameters"""

    def test_returns_analyzable_parameters(self):
        """Should return list of parameters available for analysis"""
        response = requests.get(f"{BASE_URL}/api/v1/sub-parameter/parameters")
        assert response.status_code == 200
        data = response.json()
        assert "parameters" in data
        assert len(data["parameters"]) > 0
        print(f"Found {len(data['parameters'])} analyzable parameters")

    def test_parameters_have_required_fields(self):
        """Each parameter should have name, label, unit, default_range"""
        response = requests.get(f"{BASE_URL}/api/v1/sub-parameter/parameters")
        data = response.json()
        for param in data["parameters"]:
            assert "name" in param, f"Missing 'name' in param: {param}"
            assert "label" in param, f"Missing 'label' in param: {param}"
            assert "unit" in param, f"Missing 'unit' in param: {param}"
            assert "default_range" in param, f"Missing 'default_range' in param: {param}"
        print("All parameters have required fields: name, label, unit, default_range")

    def test_parameters_include_expected_types(self):
        """Should include CO2, carbon price, GDP, energy params"""
        response = requests.get(f"{BASE_URL}/api/v1/sub-parameter/parameters")
        data = response.json()
        names = [p["name"] for p in data["parameters"]]
        
        # Check for expected parameters
        expected = ["Emissions|CO2", "Price|Carbon", "GDP|PPP", "Primary Energy"]
        for exp in expected:
            assert exp in names, f"Missing expected parameter: {exp}"
        print(f"Found all expected parameter types: {expected}")


class TestSensitivityAnalysis:
    """Test POST /api/v1/sub-parameter/sensitivity-analysis - tornado data with rankings"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID from base-scenarios"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        # Use first scenario with trajectory_count > 0
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]

    def test_sensitivity_analysis_returns_tornado_data(self, scenario_id):
        """Should return tornado data with parameter impacts"""
        payload = {
            "scenario_id": scenario_id,
            "target_metric": "temperature",
            "variation_range": 0.2
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/sensitivity-analysis",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "tornado_data" in data, "Missing tornado_data"
        assert "rankings" in data, "Missing rankings"
        assert "baseline_value" in data, "Missing baseline_value"
        assert "variation_range_pct" in data, "Missing variation_range_pct"
        print(f"Sensitivity analysis returned {len(data['tornado_data'])} parameters in tornado_data")

    def test_tornado_data_sorted_by_swing(self, scenario_id):
        """Tornado data should be sorted by swing (most impactful first)"""
        payload = {
            "scenario_id": scenario_id,
            "target_metric": "temperature",
            "variation_range": 0.2
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/sensitivity-analysis",
            json=payload
        )
        data = response.json()
        
        if len(data["tornado_data"]) > 1:
            swings = [td["swing"] for td in data["tornado_data"]]
            assert swings == sorted(swings, reverse=True), "tornado_data not sorted by swing descending"
        print("Tornado data properly sorted by swing (descending)")

    def test_tornado_data_has_required_fields(self, scenario_id):
        """Each tornado_data entry should have parameter, low_impact, high_impact, baseline, swing"""
        payload = {
            "scenario_id": scenario_id,
            "target_metric": "temperature",
            "variation_range": 0.2
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/sensitivity-analysis",
            json=payload
        )
        data = response.json()
        
        for td in data["tornado_data"]:
            assert "parameter" in td, "Missing 'parameter'"
            assert "low_impact" in td, "Missing 'low_impact'"
            assert "high_impact" in td, "Missing 'high_impact'"
            assert "baseline" in td, "Missing 'baseline'"
            assert "swing" in td, "Missing 'swing'"
            assert "sensitivity_score" in td, "Missing 'sensitivity_score'"
        print("All tornado_data entries have required fields")

    def test_rankings_have_rank_and_score(self, scenario_id):
        """Rankings should have parameter, sensitivity_score, rank"""
        payload = {
            "scenario_id": scenario_id,
            "target_metric": "temperature",
            "variation_range": 0.2
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/sensitivity-analysis",
            json=payload
        )
        data = response.json()
        
        for r in data["rankings"]:
            assert "parameter" in r, "Missing 'parameter' in ranking"
            assert "sensitivity_score" in r, "Missing 'sensitivity_score' in ranking"
            assert "rank" in r, "Missing 'rank' in ranking"
        print("All rankings have required fields")

    def test_sensitivity_with_different_metrics(self, scenario_id):
        """Should work with different target metrics"""
        metrics = ["temperature", "risk_physical", "risk_transition", "risk_overall"]
        
        for metric in metrics:
            payload = {
                "scenario_id": scenario_id,
                "target_metric": metric,
                "variation_range": 0.2
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/sub-parameter/sensitivity-analysis",
                json=payload
            )
            assert response.status_code == 200, f"Failed for metric: {metric}"
            data = response.json()
            assert data["target_metric"] == metric
        print(f"Sensitivity analysis works for all metrics: {metrics}")

    def test_invalid_scenario_returns_404(self):
        """Invalid scenario ID should return 404"""
        payload = {
            "scenario_id": "non-existent-id-12345",
            "target_metric": "temperature",
            "variation_range": 0.2
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/sensitivity-analysis",
            json=payload
        )
        assert response.status_code == 404
        print("Invalid scenario properly returns 404")


class TestWhatIfAnalysis:
    """Test POST /api/v1/sub-parameter/what-if - baseline vs modified comparison with insights"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]

    def test_whatif_returns_baseline_and_modified(self, scenario_id):
        """Should return baseline and modified impact comparisons"""
        payload = {
            "base_scenario_id": scenario_id,
            "changes": [{
                "parameter": "Emissions|CO2",
                "change_type": "relative",
                "change_value": -20,
                "apply_year": 2030
            }]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/what-if",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "baseline" in data, "Missing 'baseline'"
        assert "modified" in data, "Missing 'modified'"
        assert "differences" in data, "Missing 'differences'"
        assert "key_insights" in data, "Missing 'key_insights'"
        assert "changes_applied" in data, "Missing 'changes_applied'"
        print(f"What-if returned {data['changes_applied']} changes applied")

    def test_whatif_differences_have_required_fields(self, scenario_id):
        """Differences should have baseline, modified, absolute_change, pct_change"""
        payload = {
            "base_scenario_id": scenario_id,
            "changes": [{
                "parameter": "Emissions|CO2",
                "change_type": "relative",
                "change_value": -20,
                "apply_year": 2030
            }]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/what-if",
            json=payload
        )
        data = response.json()
        
        for key, diff in data["differences"].items():
            assert "baseline" in diff, f"Missing 'baseline' in difference for {key}"
            assert "modified" in diff, f"Missing 'modified' in difference for {key}"
            assert "absolute_change" in diff, f"Missing 'absolute_change' in difference for {key}"
            assert "pct_change" in diff, f"Missing 'pct_change' in difference for {key}"
        print("All differences have required fields")

    def test_whatif_with_absolute_change(self, scenario_id):
        """Should work with absolute change type"""
        payload = {
            "base_scenario_id": scenario_id,
            "changes": [{
                "parameter": "Price|Carbon",
                "change_type": "absolute",
                "change_value": 150,
                "apply_year": 2040
            }]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/what-if",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["changes_applied"] == 1
        print("What-if works with absolute change type")

    def test_whatif_with_multiple_changes(self, scenario_id):
        """Should work with multiple changes"""
        payload = {
            "base_scenario_id": scenario_id,
            "changes": [
                {"parameter": "Emissions|CO2", "change_type": "relative", "change_value": -10, "apply_year": 2030},
                {"parameter": "Primary Energy", "change_type": "relative", "change_value": -5, "apply_year": 2035}
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/what-if",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["changes_applied"] >= 1
        print(f"What-if works with multiple changes: {data['changes_applied']} applied")


class TestWhatIfBatch:
    """Test POST /api/v1/sub-parameter/what-if/batch - multiple change sets compared"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        return response.json()[0]["id"]

    def test_batch_returns_multiple_results(self, scenario_id):
        """Should return results for each change set"""
        payload = {
            "base_scenario_id": scenario_id,
            "change_sets": [
                [{"parameter": "Emissions|CO2", "change_type": "relative", "change_value": -10, "apply_year": 2030}],
                [{"parameter": "Emissions|CO2", "change_type": "relative", "change_value": -30, "apply_year": 2030}]
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/what-if/batch",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data, "Missing 'results'"
        assert len(data["results"]) == 2, f"Expected 2 results, got {len(data['results'])}"
        assert data["base_scenario_id"] == scenario_id
        print(f"Batch what-if returned {len(data['results'])} result sets")

    def test_batch_results_have_set_index(self, scenario_id):
        """Each result should have set_index"""
        payload = {
            "base_scenario_id": scenario_id,
            "change_sets": [
                [{"parameter": "Emissions|CO2", "change_type": "relative", "change_value": -10, "apply_year": 2030}],
                [{"parameter": "Emissions|CO2", "change_type": "relative", "change_value": -20, "apply_year": 2030}]
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/what-if/batch",
            json=payload
        )
        data = response.json()
        
        for i, result in enumerate(data["results"]):
            assert "set_index" in result, f"Missing 'set_index' in result {i}"
            assert result["set_index"] == i, f"set_index mismatch: expected {i}, got {result['set_index']}"
        print("All batch results have correct set_index")


class TestAttribution:
    """Test POST /api/v1/sub-parameter/attribution - Shapley attribution with contribution percentages"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]

    def test_attribution_returns_contributions(self, scenario_id):
        """Should return attributed changes with contribution percentages"""
        payload = {
            "scenario_id": scenario_id,
            "outcome_metric": "temperature"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/attribution",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "outcome_metric" in data, "Missing 'outcome_metric'"
        assert "total_value" in data, "Missing 'total_value'"
        assert "attributed_changes" in data, "Missing 'attributed_changes'"
        assert "total_explained_pct" in data, "Missing 'total_explained_pct'"
        assert "unexplained_pct" in data, "Missing 'unexplained_pct'"
        print(f"Attribution returned {len(data['attributed_changes'])} contributions")

    def test_attribution_contributions_have_required_fields(self, scenario_id):
        """Each attribution should have parameter, label, contribution, contribution_pct"""
        payload = {
            "scenario_id": scenario_id,
            "outcome_metric": "temperature"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/attribution",
            json=payload
        )
        data = response.json()
        
        for attr in data["attributed_changes"]:
            assert "parameter" in attr, f"Missing 'parameter'"
            assert "label" in attr, f"Missing 'label'"
            assert "contribution" in attr, f"Missing 'contribution'"
            assert "contribution_pct" in attr, f"Missing 'contribution_pct'"
            assert "confidence" in attr, f"Missing 'confidence'"
        print("All attribution contributions have required fields")

    def test_attribution_with_different_metrics(self, scenario_id):
        """Should work with different outcome metrics"""
        metrics = ["temperature", "risk_physical", "risk_transition"]
        
        for metric in metrics:
            payload = {
                "scenario_id": scenario_id,
                "outcome_metric": metric
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/sub-parameter/attribution",
                json=payload
            )
            assert response.status_code == 200, f"Failed for metric: {metric}"
            data = response.json()
            assert data["outcome_metric"] == metric
        print(f"Attribution works for metrics: {metrics}")


class TestInteractions:
    """Test GET /api/v1/sub-parameter/interactions/{id} - pairwise interaction analysis"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]

    def test_interactions_returns_pairwise_data(self, scenario_id):
        """Should return pairwise interaction analysis"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/interactions/{scenario_id}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "baseline" in data, "Missing 'baseline'"
        assert "pairwise_interactions" in data, "Missing 'pairwise_interactions'"
        print(f"Interactions returned {len(data['pairwise_interactions'])} pairwise combinations")

    def test_interactions_have_required_fields(self, scenario_id):
        """Each interaction should have param1, param2, interaction_type, etc."""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/interactions/{scenario_id}"
        )
        data = response.json()
        
        for ix in data["pairwise_interactions"]:
            assert "param1" in ix, "Missing 'param1'"
            assert "param2" in ix, "Missing 'param2'"
            assert "individual_effect_1" in ix, "Missing 'individual_effect_1'"
            assert "individual_effect_2" in ix, "Missing 'individual_effect_2'"
            assert "expected_joint" in ix, "Missing 'expected_joint'"
            assert "actual_joint" in ix, "Missing 'actual_joint'"
            assert "interaction_effect" in ix, "Missing 'interaction_effect'"
            assert "interaction_type" in ix, "Missing 'interaction_type'"
            assert "interaction_strength" in ix, "Missing 'interaction_strength'"
        print("All interactions have required fields")

    def test_interactions_type_valid_values(self, scenario_id):
        """interaction_type should be synergistic, antagonistic, or independent"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/interactions/{scenario_id}"
        )
        data = response.json()
        
        valid_types = {"synergistic", "antagonistic", "independent"}
        for ix in data["pairwise_interactions"]:
            assert ix["interaction_type"] in valid_types, f"Invalid interaction_type: {ix['interaction_type']}"
        print("All interaction types are valid (synergistic/antagonistic/independent)")

    def test_interactions_with_parameter_set(self, scenario_id):
        """Should work with custom parameter_set query param"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/interactions/{scenario_id}",
            params={"parameter_set": "Emissions|CO2,Primary Energy"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "pairwise_interactions" in data
        print("Interactions works with custom parameter_set filter")

    def test_invalid_scenario_returns_404(self):
        """Invalid scenario ID should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/interactions/non-existent-id-12345"
        )
        assert response.status_code == 404
        print("Invalid scenario properly returns 404")


class TestVisualizationTornado:
    """Test GET /api/v1/sub-parameter/visualization/tornado/{id} - tornado chart data"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]

    def test_tornado_returns_chart_data(self, scenario_id):
        """Should return tornado chart formatted data"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/visualization/tornado/{scenario_id}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["chart_type"] == "tornado", "chart_type should be 'tornado'"
        assert "target_metric" in data, "Missing 'target_metric'"
        assert "baseline" in data, "Missing 'baseline'"
        assert "bars" in data, "Missing 'bars'"
        print(f"Tornado visualization returned {len(data['bars'])} bars")

    def test_tornado_with_top_n_param(self, scenario_id):
        """Should respect top_n query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/visualization/tornado/{scenario_id}",
            params={"top_n": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["bars"]) <= 5
        print(f"Tornado with top_n=5 returned {len(data['bars'])} bars")

    def test_tornado_with_target_metric(self, scenario_id):
        """Should work with different target_metric"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/visualization/tornado/{scenario_id}",
            params={"target_metric": "risk_physical"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_metric"] == "risk_physical"
        print("Tornado works with target_metric=risk_physical")


class TestVisualizationWaterfall:
    """Test GET /api/v1/sub-parameter/visualization/waterfall/{id} - waterfall chart data"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        scenarios = response.json()
        for s in scenarios:
            if s.get("trajectory_count", 0) > 0:
                return s["id"]
        return scenarios[0]["id"]

    def test_waterfall_returns_chart_data(self, scenario_id):
        """Should return waterfall chart formatted data"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/visualization/waterfall/{scenario_id}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["chart_type"] == "waterfall", "chart_type should be 'waterfall'"
        assert "steps" in data, "Missing 'steps'"
        print(f"Waterfall visualization returned {len(data['steps'])} steps")

    def test_waterfall_steps_structure(self, scenario_id):
        """Steps should have label and cumulative values"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sub-parameter/visualization/waterfall/{scenario_id}"
        )
        data = response.json()
        
        assert len(data["steps"]) >= 2, "Should have at least Baseline and Final steps"
        
        # First step should be Baseline
        assert data["steps"][0]["label"] == "Baseline", "First step should be Baseline"
        
        # Last step should be Final
        assert data["steps"][-1]["label"] == "Final", "Last step should be Final"
        
        for step in data["steps"]:
            assert "label" in step, "Missing 'label' in step"
            assert "cumulative" in step, "Missing 'cumulative' in step"
        print("Waterfall steps have correct structure with Baseline -> ... -> Final")


class TestInteractionMatrix:
    """Test POST /api/v1/sub-parameter/interaction-matrix - full interaction matrix"""

    @pytest.fixture(scope="class")
    def scenario_id(self):
        """Get a valid scenario ID"""
        response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
        return response.json()[0]["id"]

    def test_interaction_matrix_returns_data(self, scenario_id):
        """Should return pairwise interaction matrix"""
        payload = {
            "scenario_id": scenario_id,
            "parameters": [],
            "target_outcome": "temperature"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/interaction-matrix",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "baseline" in data, "Missing 'baseline'"
        assert "pairwise_interactions" in data, "Missing 'pairwise_interactions'"
        print(f"Interaction matrix returned {len(data['pairwise_interactions'])} pairs")

    def test_interaction_matrix_with_custom_params(self, scenario_id):
        """Should work with specific parameter list"""
        payload = {
            "scenario_id": scenario_id,
            "parameters": ["Emissions|CO2", "Primary Energy", "GDP|PPP"],
            "target_outcome": "temperature"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/interaction-matrix",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "pairwise_interactions" in data
        print(f"Interaction matrix with custom params: {len(data['pairwise_interactions'])} pairs")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
