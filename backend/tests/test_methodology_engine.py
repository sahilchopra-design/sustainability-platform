"""
Test suite for Carbon Credit Methodology Engine
Tests 40+ methodologies (CDM, VCS, Gold Standard, CAR, ACR, GCC)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://asset-analytics-pro.preview.emergentagent.com')


class TestMethodologyList:
    """Tests for GET /api/v1/carbon/methodology-list endpoint"""

    def test_get_all_methodologies_returns_list(self):
        """Should return all available methodologies with 40+ entries"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list")
        assert response.status_code == 200
        data = response.json()
        
        assert "methodologies" in data
        assert "total_count" in data
        assert "sectors" in data
        
        # Verify we have 40+ methodologies as specified
        assert data["total_count"] >= 40, f"Expected 40+ methodologies, got {data['total_count']}"
        assert len(data["methodologies"]) >= 40

    def test_methodologies_have_required_fields(self):
        """Each methodology should have code, name, standard, scale, sector"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list")
        data = response.json()
        
        for method in data["methodologies"][:10]:  # Test first 10
            assert "code" in method, f"Missing 'code' in {method}"
            assert "name" in method, f"Missing 'name' in {method}"
            assert "standard" in method, f"Missing 'standard' in {method}"
            assert "scale" in method, f"Missing 'scale' in {method}"
            assert "sector" in method, f"Missing 'sector' in {method}"

    def test_sectors_list_complete(self):
        """Should include all 10 sectors"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list")
        data = response.json()
        
        expected_sectors = ["ENERGY", "WASTE", "FORESTRY", "AGRICULTURE", 
                          "INDUSTRIAL", "TRANSPORT", "BUILDINGS", "HOUSEHOLD", 
                          "MINING", "BLUE_CARBON"]
        
        for sector in expected_sectors:
            assert sector in data["sectors"], f"Missing sector: {sector}"


class TestMethodologyBySector:
    """Tests for GET /api/v1/carbon/methodology-list/{sector}"""

    @pytest.mark.parametrize("sector,min_count", [
        ("ENERGY", 8),
        ("FORESTRY", 4),
        ("WASTE", 5),
        ("AGRICULTURE", 4),
        ("INDUSTRIAL", 4),
    ])
    def test_filter_by_sector(self, sector, min_count):
        """Should return methodologies filtered by sector"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/{sector}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["sector"] == sector
        assert "methodologies" in data
        assert "count" in data
        assert len(data["methodologies"]) >= min_count, f"Expected at least {min_count} for {sector}"

    def test_invalid_sector_returns_empty(self):
        """Invalid sector should return empty list with message"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-list/INVALID")
        assert response.status_code == 200
        data = response.json()
        
        assert data["methodologies"] == []
        assert "message" in data
        assert "Valid sectors" in data["message"]


class TestMethodologyCalculation:
    """Tests for POST /api/v1/carbon/calculate/methodology"""

    def test_acm0002_renewable_energy(self):
        """ACM0002: Grid-connected Renewable Energy calculation"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=ACM0002",
            json={
                "installed_capacity_mw": 150,
                "capacity_factor": 0.28,
                "grid_emission_factor": 0.45
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["methodology"] == "ACM0002"
        assert data["version"] == "21.0"
        assert data["sector"] == "Energy"
        assert "annual_generation_mwh" in data
        assert "baseline_emissions" in data
        assert "project_emissions" in data
        assert "emission_reductions" in data
        assert data["unit"] == "tCO2e"
        
        # Verify calculation logic - renewable has zero project emissions
        assert data["project_emissions"] == 0
        assert data["emission_reductions"] > 0
        
        # Verify annual generation: 150 MW * 0.28 * 8760 hours = 367,920 MWh
        assert data["annual_generation_mwh"] == 367920

    def test_ar_acm0003_forestry(self):
        """AR-ACM0003: Afforestation/Reforestation calculation"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=AR-ACM0003",
            json={
                "start_year": 2024,
                "crediting_period_years": 30,
                "risk_buffer_percentage": 0.20
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["methodology"] == "AR-ACM0003"
        assert data["version"] == "5.0"
        assert data["sector"] == "Forestry"
        assert "yearly_results" in data
        assert "total_credits" in data
        assert "emission_reductions" in data
        
        # Verify yearly results structure
        assert len(data["yearly_results"]) == 30  # 30 year crediting period
        
        first_year = data["yearly_results"][0]
        assert first_year["year"] == 2024
        assert "co2_sequestered" in first_year
        assert "risk_buffer" in first_year
        assert "net_credits" in first_year
        
        # Risk buffer should be 20% of sequestered
        for yr in data["yearly_results"][:5]:
            expected_buffer = int(yr["co2_sequestered"] * 0.20)
            assert abs(yr["risk_buffer"] - expected_buffer) <= 1  # Allow rounding

    def test_tpddtec_cookstoves(self):
        """TPDDTEC: Clean Cookstoves calculation (Gold Standard)"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=TPDDTEC",
            json={
                "stove_count": 10000,
                "baseline_fuel_consumption": 2.5,
                "project_fuel_consumption": 1.5
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "TPDDTEC" in data["methodology"]
        assert data["standard"] == "Gold Standard"
        assert data["sector"] == "Household"
        assert "stove_count" in data
        assert data["stove_count"] == 10000
        
        # Verify emissions
        assert data["baseline_emissions"] > data["project_emissions"]
        assert data["emission_reductions"] > 0
        
        # Verify per-stove metric
        assert "annual_credits_per_stove" in data
        expected_per_stove = data["emission_reductions"] / 10000
        assert abs(data["annual_credits_per_stove"] - expected_per_stove) < 0.01

    def test_vm0048_redd(self):
        """VM0048: REDD+ calculation (VCS)"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=VM0048",
            json={
                "forest_area": 10000,
                "baseline_deforestation_rate": 0.02,
                "project_deforestation_rate": 0.005,
                "carbon_stock_per_hectare": 150,
                "buffer_percentage": 0.25
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["methodology"] == "VM0048"
        assert data["standard"] == "VCS"
        assert data["sector"] == "Forestry"
        
        # Verify emission reductions
        assert data["baseline_emissions"] > data["project_emissions"]
        assert data["gross_emission_reductions"] > 0
        assert data["emission_reductions"] > 0
        
        # Net credits should be after 25% buffer deduction
        expected_net = int(data["gross_emission_reductions"] * 0.75)
        assert abs(data["emission_reductions"] - expected_net) <= 1

    def test_invalid_methodology_returns_error(self):
        """Invalid methodology code should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=INVALID",
            json={}
        )
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "error" in data["detail"]
        assert "available_methodologies" in data["detail"]

    def test_calculation_with_default_inputs(self):
        """Calculation should work with default inputs"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code=ACM0001",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["methodology"] == "ACM0001"
        assert data["emission_reductions"] > 0


class TestBatchCalculation:
    """Tests for POST /api/v1/carbon/calculate/batch"""

    def test_batch_calculation_multiple_methodologies(self):
        """Batch calculation should process multiple methodologies"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/batch",
            json=[
                {"methodology_code": "ACM0002", "inputs": {"installed_capacity_mw": 100}},
                {"methodology_code": "TPDDTEC", "inputs": {"stove_count": 5000}},
                {"methodology_code": "VM0048", "inputs": {"forest_area": 5000}}
            ]
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert "total_emission_reductions" in data
        assert "calculation_count" in data
        assert data["unit"] == "tCO2e"
        
        # Verify 3 results
        assert len(data["results"]) == 3
        assert data["calculation_count"] == 3
        
        # Verify total is sum of individual reductions
        total = sum(r.get("emission_reductions", 0) for r in data["results"])
        assert data["total_emission_reductions"] == total

    def test_batch_with_missing_methodology_code(self):
        """Batch should handle missing methodology_code gracefully"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/batch",
            json=[
                {"methodology_code": "ACM0002", "inputs": {}},
                {"inputs": {"stove_count": 1000}}  # Missing methodology_code
            ]
        )
        assert response.status_code == 200
        data = response.json()
        
        # Second result should have error
        assert "error" in data["results"][1]


class TestGridEmissionFactor:
    """Tests for GET /api/v1/carbon/data/grid-emission-factor"""

    @pytest.mark.parametrize("country,expected_name", [
        ("US", "United States"),
        ("CN", "China"),
        ("IN", "India"),
        ("DE", "Germany"),
        ("BR", "Brazil"),
        ("GB", "United Kingdom"),
        ("JP", "Japan"),
        ("AU", "Australia"),
        ("FR", "France"),
        ("CA", "Canada"),
    ])
    def test_get_emission_factor_by_country(self, country, expected_name):
        """Should return emission factor for various countries"""
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/data/grid-emission-factor?country_code={country}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["country_code"] == country
        assert data["country_name"] == expected_name
        assert data["year"] == 2024
        assert "grid_emission_factor" in data
        assert data["unit"] == "tCO2/MWh"
        assert data["grid_emission_factor"] > 0

    def test_invalid_country_returns_404(self):
        """Invalid country code should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/data/grid-emission-factor?country_code=XX"
        )
        assert response.status_code == 404

    def test_brazil_has_low_emission_factor(self):
        """Brazil should have low emission factor (hydro heavy grid)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/carbon/data/grid-emission-factor?country_code=BR"
        )
        data = response.json()
        
        # Brazil has very clean grid (mostly hydro)
        assert data["grid_emission_factor"] < 0.2


class TestMethodologyDetails:
    """Tests for GET /api/v1/carbon/methodology-details/{code}"""

    def test_get_acm0002_details(self):
        """Should return detailed info for ACM0002"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-details/ACM0002")
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Grid-connected Renewable Electricity Generation"
        assert data["standard"] == "CDM"
        assert data["sector"] == "Energy"
        assert "required_inputs" in data

    def test_implemented_methodology_without_details(self):
        """Implemented methodology without full docs should return status"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-details/ACM0003")
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == "ACM0003"
        assert data["status"] == "available"

    def test_invalid_methodology_returns_404(self):
        """Invalid methodology should return 404"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-details/INVALID")
        assert response.status_code == 404


class TestMethodologyInputs:
    """Tests for GET /api/v1/carbon/methodology-inputs/{code}"""

    def test_get_acm0002_inputs(self):
        """Should return example inputs for ACM0002"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-inputs/ACM0002")
        assert response.status_code == 200
        data = response.json()
        
        assert data["methodology_code"] == "ACM0002"
        assert data["description"] == "Grid-connected Renewable Energy"
        assert "inputs" in data
        
        # Verify required inputs
        assert "installed_capacity_mw" in data["inputs"]
        assert "capacity_factor" in data["inputs"]
        assert "grid_emission_factor" in data["inputs"]
        
        # Verify input structure
        capacity_input = data["inputs"]["installed_capacity_mw"]
        assert "value" in capacity_input
        assert "description" in capacity_input
        assert "required" in capacity_input

    def test_undocumented_methodology_returns_default_calc(self):
        """Undocumented methodology should return default calculation"""
        response = requests.get(f"{BASE_URL}/api/v1/carbon/methodology-inputs/ACM0003")
        assert response.status_code == 200
        data = response.json()
        
        assert data["methodology_code"] == "ACM0003"
        assert "default_calculation" in data


class TestAllMethodologyCalculations:
    """Test a representative sample of all 40+ methodologies"""

    @pytest.mark.parametrize("methodology_code", [
        "ACM0001",   # Landfill Gas
        "ACM0002",   # Renewable Energy
        "ACM0005",   # Waste Heat Recovery
        "ACM0006",   # Biomass Energy
        "ACM0007",   # Fuel Switch
        "ACM0009",   # Coal to Gas
        "ACM0010",   # Manure Methane
        "ACM0012",   # Waste Heat Power
        "ACM0014",   # Cement Blending
        "ACM0022",   # Composting
        "AMS-I.A",   # Small Renewable Electricity
        "AMS-I.D",   # Small Grid Renewable
        "AMS-II.D",  # Building Efficiency
        "AMS-II.G",  # Industrial Efficiency
        "AMS-III.B", # Wastewater Methane
        "AR-ACM0003",# Afforestation
        "VM0008",    # Wastewater (VCS)
        "VM0022",    # Agricultural N2O
        "VM0033",    # Blue Carbon
        "VM0042",    # Agricultural Land
        "VM0044",    # Biochar
        "VM0047",    # ARR
        "VM0048",    # REDD+
        "TPDDTEC",   # Cookstoves
        "MMECD",     # Building Efficiency (GS)
        "CAR-Landfill", # CAR Landfill
        "CAR-Forest",   # CAR Forest
        "ACR-IFM",      # ACR Forest
        "GCCM001",      # GCC Renewable
    ])
    def test_methodology_calculates_successfully(self, methodology_code):
        """Each methodology should calculate with default inputs"""
        response = requests.post(
            f"{BASE_URL}/api/v1/carbon/calculate/methodology?methodology_code={methodology_code}",
            json={}
        )
        assert response.status_code == 200, f"Failed for {methodology_code}: {response.text}"
        data = response.json()
        
        # All should have emission_reductions
        assert "emission_reductions" in data, f"Missing emission_reductions for {methodology_code}"
        assert data["emission_reductions"] > 0, f"Zero reductions for {methodology_code}"
        assert data["unit"] == "tCO2e", f"Wrong unit for {methodology_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
