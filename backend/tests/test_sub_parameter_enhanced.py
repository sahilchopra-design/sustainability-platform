"""
Enhanced Sub-Parameter Analysis Tests
Tests: elasticity, partial correlation, OLS regression, Shapley values,
export (Excel/PDF/JSON), and custom scenario integration (analysis + key drivers).
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def scenario_id():
    """Get a valid hub scenario ID with trajectories"""
    response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/base-scenarios")
    scenarios = response.json()
    for s in scenarios:
        if s.get("trajectory_count", 0) > 0:
            return s["id"]
    return scenarios[0]["id"]


@pytest.fixture(scope="module")
def custom_scenario_id():
    """Get a valid custom scenario ID"""
    response = requests.get(f"{BASE_URL}/api/v1/scenario-builder/custom")
    custom_list = response.json()
    if custom_list and len(custom_list) > 0:
        return custom_list[0]["id"]
    return None


# ============================================================================
# Elasticity Analysis Tests
# ============================================================================

class TestElasticityAnalysis:
    """Test POST /api/v1/sub-parameter/elasticity — % outcome change per 1% param change"""

    def test_elasticity_returns_data(self, scenario_id):
        """Should return elasticity values with interpretations"""
        payload = {
            "scenario_id": scenario_id,
            "target_metric": "temperature"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/sub-parameter/elasticity",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["method"] == "elasticity", "method should be 'elasticity'"
        assert "target_metric" in data
        assert "baseline_value" in data
        assert "delta_pct" in data
        assert "elasticities" in data
        assert len(data["elasticities"]) > 0
        print(f"Elasticity analysis returned {len(data['elasticities'])} parameters")

    def test_elasticity_fields_complete(self, scenario_id):
        """Each elasticity entry should have parameter, elasticity, outcome_change_pct, interpretation"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature"}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/elasticity", json=payload)
        data = response.json()
        
        for e in data["elasticities"]:
            assert "parameter" in e, "Missing 'parameter'"
            assert "elasticity" in e, "Missing 'elasticity'"
            assert "outcome_change_pct" in e, "Missing 'outcome_change_pct'"
            assert "interpretation" in e, "Missing 'interpretation'"
        print("All elasticity entries have required fields")

    def test_elasticity_with_custom_delta(self, scenario_id):
        """Should work with custom delta_pct (default is 1%)"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "delta_pct": 5.0}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/elasticity", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["delta_pct"] == 5.0
        print("Elasticity works with custom delta_pct=5.0")

    def test_elasticity_sorted_by_magnitude(self, scenario_id):
        """Elasticities should be sorted by absolute elasticity descending"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature"}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/elasticity", json=payload)
        data = response.json()
        
        abs_vals = [abs(e["elasticity"]) for e in data["elasticities"]]
        assert abs_vals == sorted(abs_vals, reverse=True), "Elasticities not sorted by magnitude"
        print("Elasticities properly sorted by magnitude")


# ============================================================================
# Partial Correlation Tests
# ============================================================================

class TestPartialCorrelation:
    """Test POST /api/v1/sub-parameter/partial-correlation — correlation controlling for others"""

    def test_partial_correlation_returns_data(self, scenario_id):
        """Should return correlation coefficients with strength labels"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "variation_range": 0.2}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/partial-correlation", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["method"] == "partial_correlation"
        assert "correlations" in data
        assert "n_samples" in data
        assert data["n_samples"] > 0
        print(f"Partial correlation returned {len(data['correlations'])} correlations using {data['n_samples']} samples")

    def test_partial_correlation_fields_complete(self, scenario_id):
        """Each correlation should have parameter, correlation, direction, strength"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "variation_range": 0.2}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/partial-correlation", json=payload)
        data = response.json()
        
        for c in data["correlations"]:
            assert "parameter" in c
            assert "correlation" in c
            assert "abs_correlation" in c
            assert "direction" in c
            assert "strength" in c
            assert c["direction"] in ["positive", "negative"]
            assert c["strength"] in ["strong", "moderate", "weak"]
        print("All correlations have required fields with valid values")


# ============================================================================
# OLS Attribution Tests
# ============================================================================

class TestOLSAttribution:
    """Test POST /api/v1/sub-parameter/ols-attribution — linear regression coefficients"""

    def test_ols_returns_data(self, scenario_id):
        """Should return R-squared and coefficients"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "variation_range": 0.2}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/ols-attribution", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["method"] == "ols_regression"
        assert "r_squared" in data
        assert "intercept" in data
        assert "coefficients" in data
        assert "n_samples" in data
        assert data["n_samples"] == 80, "OLS should use 80 samples"
        print(f"OLS returned R²={data['r_squared']:.4f} with {len(data['coefficients'])} coefficients")

    def test_ols_r_squared_range(self, scenario_id):
        """R-squared should be between 0 and 1"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "variation_range": 0.2}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/ols-attribution", json=payload)
        data = response.json()
        
        assert 0 <= data["r_squared"] <= 1, f"R² out of range: {data['r_squared']}"
        print(f"R²={data['r_squared']:.4f} is within valid range [0,1]")

    def test_ols_coefficients_complete(self, scenario_id):
        """Each coefficient should have parameter, coefficient, weight_pct, direction"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "variation_range": 0.2}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/ols-attribution", json=payload)
        data = response.json()
        
        for c in data["coefficients"]:
            assert "parameter" in c
            assert "coefficient" in c
            assert "weight_pct" in c
            assert "direction" in c
            assert c["direction"] in ["positive", "negative"]
        print("All OLS coefficients have required fields")


# ============================================================================
# Shapley Attribution Tests
# ============================================================================

class TestShapleyAttribution:
    """Test POST /api/v1/sub-parameter/shapley — Shapley values with permutation sampling"""

    def test_shapley_returns_data(self, scenario_id):
        """Should return Shapley values with contribution percentages"""
        payload = {
            "scenario_id": scenario_id,
            "target_metric": "temperature",
            "n_permutations": 15
        }
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/shapley", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["method"] == "shapley"
        assert data["n_permutations"] == 15
        assert "attributions" in data
        assert len(data["attributions"]) > 0
        print(f"Shapley returned {len(data['attributions'])} attributions from {data['n_permutations']} permutations")

    def test_shapley_attributions_complete(self, scenario_id):
        """Each attribution should have parameter, shapley_value, contribution_pct, direction"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "n_permutations": 15}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/shapley", json=payload)
        data = response.json()
        
        for a in data["attributions"]:
            assert "parameter" in a
            assert "shapley_value" in a
            assert "contribution_pct" in a
            assert "direction" in a
            assert isinstance(a["shapley_value"], (int, float))
            assert isinstance(a["contribution_pct"], (int, float))
        print("All Shapley attributions have required fields")

    def test_shapley_sorted_by_magnitude(self, scenario_id):
        """Attributions should be sorted by absolute shapley_value descending"""
        payload = {"scenario_id": scenario_id, "target_metric": "temperature", "n_permutations": 15}
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/shapley", json=payload)
        data = response.json()
        
        abs_vals = [abs(a["shapley_value"]) for a in data["attributions"]]
        assert abs_vals == sorted(abs_vals, reverse=True)
        print("Shapley attributions sorted by magnitude")

    def test_shapley_with_different_permutations(self, scenario_id):
        """Should work with different n_permutations (5-100)"""
        for n in [5, 20]:
            payload = {"scenario_id": scenario_id, "target_metric": "temperature", "n_permutations": n}
            response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/shapley", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["n_permutations"] == n
        print("Shapley works with different permutation counts")


# ============================================================================
# Export Tests
# ============================================================================

class TestExport:
    """Test POST /api/v1/sub-parameter/export — Excel/PDF/JSON export"""

    def test_export_excel(self):
        """Should export to Excel and return download URL"""
        payload = {
            "analyses": [{"method": "elasticity", "elasticities": [{"parameter": "CO2", "elasticity": 0.5, "outcome_change_pct": 0.5, "interpretation": "test"}]}],
            "format": "excel"
        }
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/export", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "excel"
        assert "filename" in data
        assert data["filename"].endswith(".xlsx")
        assert "download_url" in data
        assert "/api/v1/analysis/reports/download/" in data["download_url"]
        print(f"Excel export: {data['filename']}")

    def test_export_pdf(self):
        """Should export to PDF and return download URL"""
        payload = {
            "analyses": [{"method": "tornado", "tornado_data": [{"parameter": "CO2", "low_impact": 1.0, "high_impact": 2.0, "swing": 1.0}]}],
            "format": "pdf"
        }
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/export", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "pdf"
        assert data["filename"].endswith(".pdf")
        assert "download_url" in data
        print(f"PDF export: {data['filename']}")

    def test_export_json(self):
        """Should export to JSON and return download URL"""
        payload = {
            "analyses": [{"method": "test_data", "values": [1, 2, 3]}],
            "format": "json"
        }
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/export", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "json"
        assert data["filename"].endswith(".json")
        assert "download_url" in data
        print(f"JSON export: {data['filename']}")

    def test_export_download_works(self):
        """Exported file should be downloadable"""
        payload = {
            "analyses": [{"method": "test", "data": "test"}],
            "format": "json"
        }
        export_resp = requests.post(f"{BASE_URL}/api/v1/sub-parameter/export", json=payload)
        data = export_resp.json()
        
        download_resp = requests.get(f"{BASE_URL}{data['download_url']}")
        assert download_resp.status_code == 200
        print(f"Download verified: {len(download_resp.content)} bytes")


# ============================================================================
# Custom Scenario Integration Tests
# ============================================================================

class TestCustomScenarioAnalysis:
    """Test POST /api/v1/sub-parameter/custom-scenario/{id}/analysis — auto-analysis on custom scenario"""

    def test_analysis_returns_all_methods(self, custom_scenario_id):
        """Should return sensitivity, elasticity, and attribution for custom scenario"""
        if not custom_scenario_id:
            pytest.skip("No custom scenarios available")
        
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/custom-scenario/{custom_scenario_id}/analysis")
        assert response.status_code == 200
        data = response.json()
        
        assert "custom_scenario_id" in data
        assert data["custom_scenario_id"] == custom_scenario_id
        assert "base_scenario_id" in data
        assert "sensitivity" in data
        assert "elasticity" in data
        assert "attribution" in data
        print(f"Custom scenario analysis returned all 3 methods for {custom_scenario_id}")

    def test_analysis_sensitivity_valid(self, custom_scenario_id):
        """Sensitivity sub-response should have tornado_data"""
        if not custom_scenario_id:
            pytest.skip("No custom scenarios available")
        
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/custom-scenario/{custom_scenario_id}/analysis")
        data = response.json()
        
        assert "tornado_data" in data["sensitivity"]
        assert "baseline_value" in data["sensitivity"]
        print("Sensitivity data is valid")

    def test_analysis_invalid_id_returns_404(self):
        """Invalid custom scenario ID should return 404"""
        response = requests.post(f"{BASE_URL}/api/v1/sub-parameter/custom-scenario/invalid-id-12345/analysis")
        assert response.status_code == 404
        print("Invalid custom scenario properly returns 404")


class TestCustomScenarioKeyDrivers:
    """Test GET /api/v1/sub-parameter/custom-scenario/{id}/key-drivers — top 5 drivers"""

    def test_key_drivers_returns_top5(self, custom_scenario_id):
        """Should return top 5 key drivers for custom scenario"""
        if not custom_scenario_id:
            pytest.skip("No custom scenarios available")
        
        response = requests.get(f"{BASE_URL}/api/v1/sub-parameter/custom-scenario/{custom_scenario_id}/key-drivers")
        assert response.status_code == 200
        data = response.json()
        
        assert "custom_scenario_id" in data
        assert "key_drivers" in data
        assert len(data["key_drivers"]) <= 5, "Should return at most 5 key drivers"
        print(f"Key drivers returned {len(data['key_drivers'])} drivers")

    def test_key_drivers_fields_complete(self, custom_scenario_id):
        """Each driver should have parameter, total_sensitivity, metrics_affected, rank"""
        if not custom_scenario_id:
            pytest.skip("No custom scenarios available")
        
        response = requests.get(f"{BASE_URL}/api/v1/sub-parameter/custom-scenario/{custom_scenario_id}/key-drivers")
        data = response.json()
        
        for d in data["key_drivers"]:
            assert "parameter" in d
            assert "total_sensitivity" in d
            assert "metrics_affected" in d
            assert "rank" in d
            assert isinstance(d["metrics_affected"], list)
        print("All key drivers have required fields")

    def test_key_drivers_ranked_correctly(self, custom_scenario_id):
        """Drivers should be ranked 1, 2, 3, ... in order"""
        if not custom_scenario_id:
            pytest.skip("No custom scenarios available")
        
        response = requests.get(f"{BASE_URL}/api/v1/sub-parameter/custom-scenario/{custom_scenario_id}/key-drivers")
        data = response.json()
        
        ranks = [d["rank"] for d in data["key_drivers"]]
        expected = list(range(1, len(ranks) + 1))
        assert ranks == expected, f"Ranks {ranks} don't match expected {expected}"
        print("Key drivers properly ranked")

    def test_key_drivers_invalid_id_returns_404(self):
        """Invalid custom scenario ID should return 404"""
        response = requests.get(f"{BASE_URL}/api/v1/sub-parameter/custom-scenario/invalid-id-12345/key-drivers")
        assert response.status_code == 404
        print("Invalid custom scenario properly returns 404 for key-drivers")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
