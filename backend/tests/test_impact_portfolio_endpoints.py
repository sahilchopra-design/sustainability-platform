"""
Test suite for Impact Calculator, Custom Scenario Builder, and Portfolio Upload endpoints.
Tests: POST /api/v1/analysis/impact, POST /api/v1/analysis/custom-scenarios,
       POST /api/v1/analysis/portfolio-upload/parse, POST /api/v1/analysis/portfolio-upload/create
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test scenario and portfolio IDs from existing data
SCENARIO_WITCH = "ad7292d6-72cd-4fcd-82a9-1d09fa6163ef"  # WITCH 1.5C
SCENARIO_TIAM = "47526e8d-bfcf-4857-8e8a-58b5371bd05c"   # TIAM-ECN 2C

# Portfolio with assets
PORTFOLIO_SAMPLE = "698fc3f3a10cb92034afa4bf"  # Sample Portfolio (16 assets)
PORTFOLIO_UPLOADED = "6990a009792bfd9bd7649051"  # Uploaded Portfolio (4 assets)
PORTFOLIO_EMPTY = "698fc53fa10cb92034afa552"  # UI Test Portfolio (0 assets)


class TestImpactCalculator:
    """Test POST /api/v1/analysis/impact - Scenario impact on portfolios"""

    def test_impact_returns_horizons_with_expected_loss(self):
        """Impact calculation returns horizons array with expected_loss, var_95, avg_pd_change_pct."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/impact",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE,
                "horizons": [2030, 2040, 2050]
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify top-level structure
        assert "scenario_id" in data
        assert "scenario_name" in data
        assert "engine_scenario" in data
        assert "horizons" in data
        assert "multipliers" in data
        assert "calculated_at" in data
        
        # Verify horizons array
        assert len(data["horizons"]) == 3
        for h in data["horizons"]:
            assert "horizon" in h
            assert h["horizon"] in [2030, 2040, 2050]
            assert "expected_loss" in h
            assert "expected_loss_pct" in h
            assert "var_95" in h
            assert "var_99" in h
            assert "avg_pd_change_pct" in h
            assert "total_exposure" in h
            assert "weighted_avg_pd" in h
            
            # Verify numeric values
            assert isinstance(h["expected_loss"], (int, float))
            assert isinstance(h["var_95"], (int, float))
            assert isinstance(h["avg_pd_change_pct"], (int, float))

    def test_impact_returns_multipliers(self):
        """Impact calculation returns multipliers (carbon_price, emissions_change, temperature)."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/impact",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "multipliers" in data
        multipliers = data["multipliers"]
        
        # Multipliers may be null but keys should exist
        assert "carbon_price_2030" in multipliers
        assert "carbon_price_2050" in multipliers
        assert "emissions_change_pct" in multipliers
        assert "temperature_2050" in multipliers

    def test_impact_returns_404_for_invalid_portfolio(self):
        """Impact calculation returns 404 for non-existent portfolio."""
        fake_portfolio_id = "000000000000000000000000"  # Invalid ObjectId
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/impact",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": fake_portfolio_id
            }
        )
        assert response.status_code == 404

    def test_impact_returns_400_for_empty_portfolio(self):
        """Impact calculation returns 400 for portfolio with no assets."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/impact",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_EMPTY
            }
        )
        assert response.status_code == 400

    def test_impact_with_default_horizons(self):
        """Impact calculation with default horizons [2030, 2040, 2050]."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/impact",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_UPLOADED
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Default horizons
        assert len(data["horizons"]) == 3
        horizon_years = [h["horizon"] for h in data["horizons"]]
        assert horizon_years == [2030, 2040, 2050]

    def test_impact_sector_breakdown(self):
        """Impact calculation returns sector_breakdown in results."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/impact",
            json={
                "scenario_id": SCENARIO_WITCH,
                "portfolio_id": PORTFOLIO_SAMPLE
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # At least one horizon should have sector_breakdown
        for h in data["horizons"]:
            assert "sector_breakdown" in h


class TestCustomScenarioBuilder:
    """Test POST /api/v1/analysis/custom-scenarios - Blended scenario creation"""

    created_scenario_id = None

    def test_create_custom_scenario_with_overrides(self):
        """Create custom blended scenario with trajectory overrides."""
        unique_name = f"TEST_Custom_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/custom-scenarios",
            json={
                "name": unique_name,
                "description": "Test custom scenario from pytest",
                "base_scenario_id": SCENARIO_WITCH,
                "overrides": [
                    {
                        "variable": "Emissions|CO2",
                        "region": "World",
                        "source_scenario_id": SCENARIO_TIAM
                    }
                ]
            }
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == unique_name
        assert "base_scenario" in data
        assert "overrides_applied" in data
        assert "total_trajectories" in data
        assert "lineage" in data
        
        # Verify lineage tracking
        assert data["lineage"]["base_scenario_id"] == SCENARIO_WITCH
        
        TestCustomScenarioBuilder.created_scenario_id = data["id"]

    def test_create_custom_scenario_minimal(self):
        """Create custom scenario without overrides (just copy base)."""
        unique_name = f"TEST_CustomMin_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/custom-scenarios",
            json={
                "name": unique_name,
                "description": "",
                "base_scenario_id": SCENARIO_WITCH,
                "overrides": []
            }
        )
        assert response.status_code == 201
        data = response.json()
        
        assert data["overrides_applied"] == 0
        assert data["total_trajectories"] > 0

    def test_custom_scenario_404_for_invalid_base(self):
        """Custom scenario creation returns 404 for invalid base_scenario_id."""
        fake_scenario_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/custom-scenarios",
            json={
                "name": "TEST_InvalidBase",
                "description": "",
                "base_scenario_id": fake_scenario_id,
                "overrides": []
            }
        )
        assert response.status_code == 404


class TestPortfolioUpload:
    """Test POST /api/v1/analysis/portfolio-upload/parse and create"""

    SAMPLE_CSV = """name,sector,exposure,rating,asset_type,pd,lgd,maturity
Acme Power Corp,Power,5000000,BBB,Bond,0.02,0.45,5
Global Steel Inc,Metals,3000000,BB,Bond,0.04,0.50,7
Petro Energy Ltd,Oil,4000000,A,Bond,0.01,0.40,3
Auto Motors Co,Automotive,2000000,BBB,Loan,0.025,0.45,4"""

    MINIMAL_CSV = """company,exposure,industry
Test Company,1000000,Energy"""

    def test_parse_csv_returns_assets_and_mapping(self):
        """Portfolio CSV parse returns assets array and column_mapping."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/portfolio-upload/parse",
            json={"content": self.SAMPLE_CSV}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "assets" in data
        assert "errors" in data
        assert "column_mapping" in data
        assert "raw_columns" in data
        assert "total_rows" in data
        assert "valid_rows" in data
        
        # Verify assets parsed correctly
        assert len(data["assets"]) == 4
        assert data["valid_rows"] == 4
        assert data["total_rows"] == 4
        
        # Verify first asset structure
        first_asset = data["assets"][0]
        assert "id" in first_asset
        assert "company" in first_asset
        assert first_asset["company"]["name"] == "Acme Power Corp"
        assert first_asset["company"]["sector"] == "Power Generation"
        assert first_asset["exposure"] == 5000000
        assert first_asset["rating"] == "BBB"
        assert first_asset["asset_type"] == "Bond"

    def test_parse_csv_auto_maps_columns(self):
        """CSV parser auto-detects column mapping from headers."""
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/portfolio-upload/parse",
            json={"content": self.MINIMAL_CSV}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Auto-mapping should detect "company" as name, "industry" as sector
        mapping = data["column_mapping"]
        assert mapping.get("name") == "company"
        assert mapping.get("exposure") == "exposure"
        assert mapping.get("sector") == "industry"
        
        # Verify asset created with defaults
        assert len(data["assets"]) == 1
        asset = data["assets"][0]
        assert asset["company"]["name"] == "Test Company"
        assert asset["base_pd"] == 0.02  # default
        assert asset["base_lgd"] == 0.45  # default
        assert asset["maturity_years"] == 5  # default

    def test_parse_csv_reports_errors(self):
        """CSV parser reports errors for invalid rows."""
        csv_with_errors = """name,sector,exposure
Valid Company,Power,1000000
,Power,2000000
Missing Exposure,Power,"""
        
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/portfolio-upload/parse",
            json={"content": csv_with_errors}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have 1 valid and 2 errors
        assert data["valid_rows"] == 1
        assert len(data["errors"]) == 2

    def test_create_portfolio_from_parsed_assets(self):
        """Create portfolio from parsed assets."""
        # First parse CSV
        parse_response = requests.post(
            f"{BASE_URL}/api/v1/analysis/portfolio-upload/parse",
            json={"content": self.SAMPLE_CSV}
        )
        parsed = parse_response.json()
        
        # Create portfolio
        unique_name = f"TEST_Upload_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/portfolio-upload/create",
            json={
                "name": unique_name,
                "description": "Created by pytest",
                "assets": parsed["assets"]
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response
        assert "id" in data
        assert data["name"] == unique_name
        assert data["num_assets"] == 4
        assert data["total_exposure"] == 14000000  # 5M + 3M + 4M + 2M
        
        # Cleanup - delete the created portfolio
        requests.delete(f"{BASE_URL}/api/portfolios/{data['id']}")


class TestCleanup:
    """Cleanup test data"""

    def test_cleanup_test_scenarios(self):
        """Cleanup TEST_ custom scenarios (via hub_scenarios with custom source)."""
        # Note: Custom scenarios are stored in hub_scenarios table
        # We can't easily delete them via API, but they won't interfere with tests
        assert True

    def test_cleanup_test_portfolios(self):
        """Delete TEST_ prefixed portfolios."""
        response = requests.get(f"{BASE_URL}/api/portfolios")
        if response.status_code == 200:
            portfolios = response.json().get("portfolios", [])
            for p in portfolios:
                if p.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/portfolios/{p['id']}")
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
