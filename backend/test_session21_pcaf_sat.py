"""
Session 21 — PCAF All 7 Asset Classes (Investor-Grade) + SAT Coal Phase-Out Checker
Tests cover all endpoints, DQS auto-derivation, uncertainty bands, regulatory disclosure,
and coal phase-out criteria scoring.
"""
import pytest
import requests

BASE = "http://localhost:8001"
PCAF = f"{BASE}/api/v1/pcaf"
SAT = f"{BASE}/api/v1/sat-coal"


# =====================================================================
# PCAF — Metadata / Reference Endpoints
# =====================================================================

class TestPCAFMetadata:
    def test_asset_classes(self):
        r = requests.get(f"{PCAF}/asset-classes")
        assert r.status_code == 200
        d = r.json()
        assert d["standard"].startswith("PCAF")
        assert len(d["asset_classes"]) == 7
        ids = [ac["id"] for ac in d["asset_classes"]]
        assert "listed_equity" in ids
        assert "sovereign_bonds" in ids
        # Each class must have table references
        for ac in d["asset_classes"]:
            assert "pcaf_row" in ac
            assert "dqs_table" in ac
            assert "af_formula" in ac
            assert "intensity_unit" in ac

    def test_methodology(self):
        r = requests.get(f"{PCAF}/methodology")
        assert r.status_code == 200
        d = r.json()
        assert "standard" in d
        assert "attribution_factors" in d
        assert "data_quality" in d
        assert "regulatory_alignment" in d
        assert d["regulatory_alignment"]["sfdr"].startswith("EU SFDR")

    def test_sector_emission_factors(self):
        r = requests.get(f"{PCAF}/sector-emission-factors")
        assert r.status_code == 200
        d = r.json()
        assert "factors" in d
        # Each sector should have scope1, scope2, scope3
        for sector, ef in d["factors"].items():
            assert "scope1" in ef
            assert "scope2" in ef
            assert "scope3" in ef

    def test_epc_benchmarks(self):
        r = requests.get(f"{PCAF}/epc-benchmarks")
        assert r.status_code == 200
        d = r.json()
        assert "A" in d["ratings"]
        assert "G" in d["ratings"]
        assert d["ratings"]["A"] < d["ratings"]["G"]

    def test_vehicle_benchmarks(self):
        r = requests.get(f"{PCAF}/vehicle-benchmarks")
        assert r.status_code == 200
        d = r.json()
        assert d["types"]["BEV"] == 0.0
        assert d["types"]["ICE_petrol"] > d["types"]["PHEV"]

    def test_sovereign_data(self):
        r = requests.get(f"{PCAF}/sovereign-data")
        assert r.status_code == 200
        d = r.json()
        assert "US" in d["countries"]
        assert d["countries"]["US"]["emissions_mtco2e"] > 4000

    def test_dqs_improvement_guidance(self):
        r = requests.get(f"{PCAF}/dqs-improvement-guidance")
        assert r.status_code == 200
        d = r.json()
        assert "priority_order" in d
        assert len(d["data_sources_by_dqs"]) == 5


# =====================================================================
# PCAF — Asset Class 1: Listed Equity & Corporate Bonds
# =====================================================================

class TestListedEquity:
    def _base_payload(self, **overrides):
        asset = {
            "asset_id": "EQ001",
            "name": "TotalEnergies SE",
            "isin": "FR0000120271",
            "sector": "Energy",
            "country_iso": "FR",
            "outstanding_eur": 50_000_000,
            "evic_eur": 120_000_000_000,
            "annual_revenue_eur": 200_000_000_000,
            "scope1_tco2e": 40_000_000,
            "scope2_tco2e": 5_000_000,
            "emissions_verified": True,
        }
        asset.update(overrides)
        return {"assets": [asset], "reporting_year": 2024}

    def test_basic_assessment(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload())
        assert r.status_code == 200
        d = r.json()
        assert d["asset_class"] == "listed_equity"
        assert d["total_assets"] == 1
        assert d["total_outstanding_eur"] == 50_000_000
        # AF = 50M / 120B = 0.000417
        asset = d["per_asset"][0]
        assert 0.0004 < asset["attribution_factor"] < 0.0005
        assert asset["financed_scope1_tco2e"] > 0
        assert asset["attribution_formula"] == "Outstanding / EVIC"

    def test_auto_dqs_verified(self):
        """Verified emissions -> DQS 1"""
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload(
            emissions_verified=True, scope1_tco2e=40_000_000
        ))
        d = r.json()
        asset = d["per_asset"][0]
        assert asset["pcaf_data_quality_score"] == 1
        assert asset["pcaf_dqs_auto_derived"] is True

    def test_auto_dqs_reported_unverified(self):
        """Reported but not verified -> DQS 2"""
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload(
            emissions_verified=False, scope1_tco2e=40_000_000
        ))
        d = r.json()
        assert d["per_asset"][0]["pcaf_data_quality_score"] == 2

    def test_auto_dqs_sector_average(self):
        """No emissions data, has revenue -> DQS 4"""
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload(
            scope1_tco2e=None, scope2_tco2e=None, emissions_verified=False,
            annual_revenue_eur=200_000_000_000
        ))
        d = r.json()
        assert d["per_asset"][0]["pcaf_data_quality_score"] == 4

    def test_auto_dqs_proxy(self):
        """No emissions, no revenue -> DQS 5"""
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload(
            scope1_tco2e=None, scope2_tco2e=None, emissions_verified=False,
            annual_revenue_eur=None
        ))
        d = r.json()
        assert d["per_asset"][0]["pcaf_data_quality_score"] == 5

    def test_dqs_override_validation(self):
        """User claims DQS 1 but no verified emissions -> capped to DQS 2"""
        payload = self._base_payload(emissions_verified=False, pcaf_data_quality_score=1)
        r = requests.post(f"{PCAF}/listed-equity", json=payload)
        d = r.json()
        assert d["per_asset"][0]["pcaf_data_quality_score"] == 2

    def test_uncertainty_bands(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload())
        d = r.json()
        asset = d["per_asset"][0]
        central = asset["financed_total_tco2e"]
        low = asset["financed_total_low_tco2e"]
        high = asset["financed_total_high_tco2e"]
        assert low < central < high
        # DQS 1 -> +/- 10%
        assert abs(low - central * 0.9) < central * 0.01
        assert abs(high - central * 1.1) < central * 0.01

    def test_emission_intensity(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload())
        d = r.json()
        asset = d["per_asset"][0]
        assert asset["emission_intensity"] > 0
        assert asset["emission_intensity_unit"] == "tCO2e / EUR M invested"

    def test_data_completeness(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload())
        d = r.json()
        assert d["per_asset"][0]["data_completeness_pct"] > 80

    def test_data_gaps_identified(self):
        """Missing scope1 -> data gap flagged"""
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload(
            scope1_tco2e=None, emissions_verified=False
        ))
        d = r.json()
        gaps = d["per_asset"][0]["data_gaps"]
        assert len(gaps) > 0
        assert any(g["field"] == "scope1_tco2e" for g in gaps)

    def test_regulatory_disclosure(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload())
        d = r.json()
        rd = d["regulatory_disclosure"]
        assert rd["sfdr_pai_1_financed_ghg_tco2e"] > 0
        assert rd["sfdr_pai_2_carbon_footprint_tco2e_per_meur"] > 0
        assert rd["tcfd_financed_emissions_tco2e"] > 0

    def test_waci_calculated(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload())
        d = r.json()
        assert d["waci_scope12_tco2e_per_meur"] is not None
        assert d["implied_temperature_rise_c"] is not None

    def test_methodology_provenance(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload())
        d = r.json()
        assert "PCAF v2.0" in d["methodology"]["standard"]
        assert "Table 5.3" in d["methodology"]["asset_class_table"]
        assert d["per_asset"][0]["pcaf_table_reference"] == "PCAF Standard Part A, Table 5.3"

    def test_scope3_optional(self):
        payload = self._base_payload(scope3_tco2e=100_000_000)
        payload["include_scope3"] = True
        r = requests.post(f"{PCAF}/listed-equity", json=payload)
        d = r.json()
        assert d["total_financed_scope3_tco2e"] > 0

    def test_scope3_excluded_by_default(self):
        r = requests.post(f"{PCAF}/listed-equity", json=self._base_payload(scope3_tco2e=100_000_000))
        d = r.json()
        assert d["total_financed_scope3_tco2e"] == 0

    def test_portfolio_level_metrics(self):
        """Multiple assets -> portfolio aggregation"""
        payload = {
            "assets": [
                {"asset_id": "EQ001", "sector": "Energy", "outstanding_eur": 50e6,
                 "evic_eur": 120e9, "annual_revenue_eur": 200e9, "scope1_tco2e": 40e6,
                 "scope2_tco2e": 5e6, "emissions_verified": True},
                {"asset_id": "EQ002", "sector": "Financials", "outstanding_eur": 30e6,
                 "evic_eur": 80e9, "annual_revenue_eur": 50e9, "scope1_tco2e": 500_000,
                 "scope2_tco2e": 200_000, "emissions_verified": False},
            ],
            "reporting_year": 2024,
        }
        r = requests.post(f"{PCAF}/listed-equity", json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["total_assets"] == 2
        assert d["total_outstanding_eur"] == 80_000_000
        # Both assets have DQS <= 2 (entity-reported data) -> counted as "verified"
        assert d["assets_with_verified_data_pct"] == 100.0

    def test_empty_request_rejected(self):
        r = requests.post(f"{PCAF}/listed-equity", json={"assets": [], "reporting_year": 2024})
        assert r.status_code == 400


# =====================================================================
# PCAF — Asset Class 2: Business Loans
# =====================================================================

class TestBusinessLoans:
    def test_with_balance_sheet(self):
        r = requests.post(f"{PCAF}/business-loans", json={
            "assets": [{
                "asset_id": "BL001", "name": "SME Loan",
                "sector": "Industrials",
                "outstanding_eur": 5_000_000,
                "total_equity_eur": 10_000_000,
                "total_debt_eur": 15_000_000,
                "scope1_tco2e": 5000,
                "scope2_tco2e": 2000,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        # AF = 5M / (10M + 15M) = 0.2
        assert abs(d["per_asset"][0]["attribution_factor"] - 0.2) < 0.001
        assert d["per_asset"][0]["attribution_formula"] == "Outstanding / (Total Equity + Total Debt)"

    def test_without_balance_sheet(self):
        """No equity/debt -> AF = outstanding / (2 * outstanding) = 0.5"""
        r = requests.post(f"{PCAF}/business-loans", json={
            "assets": [{
                "asset_id": "BL002",
                "sector": "Industrials",
                "outstanding_eur": 5_000_000,
                "scope1_tco2e": 5000,
                "scope2_tco2e": 2000,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert abs(d["per_asset"][0]["attribution_factor"] - 0.5) < 0.001
        gaps = d["per_asset"][0]["data_gaps"]
        assert any("balance sheet" in g["impact"].lower() or "equity" in g["field"].lower() for g in gaps)


# =====================================================================
# PCAF — Asset Class 3: Project Finance
# =====================================================================

class TestProjectFinance:
    def test_renewable_project(self):
        r = requests.post(f"{PCAF}/project-finance", json={
            "assets": [{
                "asset_id": "PF001", "name": "Solar Farm Alpha",
                "sector": "Energy",
                "outstanding_eur": 30_000_000,
                "total_project_cost_eur": 100_000_000,
                "project_generation_mwh": 150_000,
                "technology": "solar_pv",
                "project_type": "renewable",
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["attribution_factor"] == 0.3
        # Solar PV EF = 0.020 tCO2e/MWh * 150000 * 0.3 = 900 tCO2e
        assert d["per_asset"][0]["financed_total_tco2e"] < 5000  # Very low for solar
        assert d["per_asset"][0]["estimation_method"] == "technology_factor"

    def test_fossil_project_with_actual_emissions(self):
        r = requests.post(f"{PCAF}/project-finance", json={
            "assets": [{
                "asset_id": "PF002",
                "sector": "Energy",
                "outstanding_eur": 50_000_000,
                "total_project_cost_eur": 200_000_000,
                "project_scope1_tco2e": 500_000,
                "project_scope2_tco2e": 10_000,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["attribution_factor"] == 0.25
        assert d["per_asset"][0]["estimation_method"] == "reported"


# =====================================================================
# PCAF — Asset Class 4: Commercial Real Estate
# =====================================================================

class TestCRE:
    def test_with_epc_rating(self):
        r = requests.post(f"{PCAF}/commercial-real-estate", json={
            "assets": [{
                "asset_id": "CRE001",
                "outstanding_eur": 20_000_000,
                "property_value_eur": 50_000_000,
                "floor_area_m2": 5000,
                "building_type": "office",
                "epc_rating": "C",
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["attribution_factor"] == 0.4
        assert d["per_asset"][0]["emission_intensity_unit"] == "kgCO2/m2/year (building-level)"
        assert d["per_asset"][0]["estimation_method"] == "epc_proxy"
        # EPC C = 45 kgCO2/m2 -> intensity should be ~45
        assert 40 < d["per_asset"][0]["emission_intensity"] < 50

    def test_with_actual_energy_data(self):
        r = requests.post(f"{PCAF}/commercial-real-estate", json={
            "assets": [{
                "asset_id": "CRE002",
                "outstanding_eur": 10_000_000,
                "property_value_eur": 25_000_000,
                "floor_area_m2": 3000,
                "building_type": "retail",
                "energy_intensity_kwh_m2": 150,
                "emission_factor_kgco2_kwh": 0.4,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["estimation_method"] == "energy_intensity"

    def test_no_building_data(self):
        """No EPC, no energy -> DQS 5, gaps flagged"""
        r = requests.post(f"{PCAF}/commercial-real-estate", json={
            "assets": [{
                "asset_id": "CRE003",
                "outstanding_eur": 10_000_000,
                "property_value_eur": 25_000_000,
                "floor_area_m2": 3000,
                "building_type": "industrial",
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["pcaf_data_quality_score"] == 5
        assert len(d["per_asset"][0]["data_gaps"]) > 0


# =====================================================================
# PCAF — Asset Class 5: Mortgages
# =====================================================================

class TestMortgages:
    def test_residential_with_epc(self):
        r = requests.post(f"{PCAF}/mortgages", json={
            "assets": [{
                "asset_id": "MG001",
                "outstanding_eur": 200_000,
                "property_value_eur": 350_000,
                "floor_area_m2": 120,
                "property_type": "terraced",
                "epc_rating": "D",
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["attribution_factor"] < 1.0
        # EPC D = 70 kgCO2/m2
        assert 65 < d["per_asset"][0]["emission_intensity"] < 75

    def test_mortgage_portfolio(self):
        assets = [
            {"asset_id": f"MG{i:03d}", "outstanding_eur": 200_000,
             "property_value_eur": 350_000, "floor_area_m2": 100,
             "epc_rating": rating}
            for i, rating in enumerate(["A", "B", "C", "D", "E"])
        ]
        r = requests.post(f"{PCAF}/mortgages", json={"assets": assets, "reporting_year": 2024})
        assert r.status_code == 200
        d = r.json()
        assert d["total_assets"] == 5
        # Higher EPC ratings should have lower intensity
        intensities = [a["emission_intensity"] for a in d["per_asset"]]
        assert intensities[0] < intensities[-1]


# =====================================================================
# PCAF — Asset Class 6: Vehicle Loans
# =====================================================================

class TestVehicleLoans:
    def test_bev(self):
        r = requests.post(f"{PCAF}/vehicle-loans", json={
            "assets": [{
                "asset_id": "VL001",
                "outstanding_eur": 25_000,
                "vehicle_value_eur": 45_000,
                "vehicle_type": "BEV",
                "annual_distance_km": 15000,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        # BEV: 0 gCO2/km tailpipe
        assert d["per_asset"][0]["financed_scope1_tco2e"] == 0
        assert d["per_asset"][0]["emission_intensity"] == 0.0

    def test_ice_petrol(self):
        r = requests.post(f"{PCAF}/vehicle-loans", json={
            "assets": [{
                "asset_id": "VL002",
                "outstanding_eur": 15_000,
                "vehicle_value_eur": 30_000,
                "vehicle_type": "ICE_petrol",
                "annual_distance_km": 15000,
                "emission_factor_gco2_km": 160,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["financed_scope1_tco2e"] > 0
        assert d["per_asset"][0]["financed_scope2_tco2e"] == 0
        assert d["per_asset"][0]["emission_intensity"] == 160.0

    def test_phev_split(self):
        r = requests.post(f"{PCAF}/vehicle-loans", json={
            "assets": [{
                "asset_id": "VL003",
                "outstanding_eur": 20_000,
                "vehicle_value_eur": 40_000,
                "vehicle_type": "PHEV",
                "annual_distance_km": 15000,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        # PHEV: split between S1 and S2
        assert d["per_asset"][0]["financed_scope1_tco2e"] > 0
        assert d["per_asset"][0]["financed_scope2_tco2e"] > 0


# =====================================================================
# PCAF — Asset Class 7: Sovereign Bonds
# =====================================================================

class TestSovereignBonds:
    def test_us_bond(self):
        r = requests.post(f"{PCAF}/sovereign-bonds", json={
            "assets": [{
                "asset_id": "SB001",
                "country_iso": "US",
                "outstanding_eur": 100_000_000,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["financed_total_tco2e"] > 0
        assert d["per_asset"][0]["emission_intensity_unit"] == "tCO2e / USD M GDP PPP"
        assert d["per_asset"][0]["attribution_formula"] == "Outstanding / PPP-adjusted GDP (EUR)"

    def test_unknown_country(self):
        """Unknown ISO -> gaps flagged, proxy emissions used"""
        r = requests.post(f"{PCAF}/sovereign-bonds", json={
            "assets": [{
                "asset_id": "SB002",
                "country_iso": "ZZ",
                "outstanding_eur": 10_000_000,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert len(d["per_asset"][0]["data_gaps"]) > 0

    def test_override_data(self):
        """User provides custom emissions and GDP"""
        r = requests.post(f"{PCAF}/sovereign-bonds", json={
            "assets": [{
                "asset_id": "SB003",
                "country_iso": "US",
                "outstanding_eur": 50_000_000,
                "sovereign_emissions_mtco2e": 6000.0,
                "gdp_ppp_usd_tn": 28.0,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["per_asset"][0]["pcaf_data_quality_score"] == 1  # Override -> DQS 1


# =====================================================================
# PCAF — Portfolio Aggregation
# =====================================================================

class TestPortfolioAggregate:
    def test_multi_asset_class(self):
        r = requests.post(f"{PCAF}/portfolio-aggregate", json={
            "reporting_year": 2024,
            "listed_equity": {
                "assets": [{
                    "asset_id": "EQ001", "sector": "Energy",
                    "outstanding_eur": 50e6, "evic_eur": 120e9,
                    "annual_revenue_eur": 200e9,
                    "scope1_tco2e": 40e6, "scope2_tco2e": 5e6,
                }],
                "reporting_year": 2024,
            },
            "sovereign_bonds": {
                "assets": [{
                    "asset_id": "SB001", "country_iso": "DE",
                    "outstanding_eur": 30e6,
                }],
                "reporting_year": 2024,
            },
        })
        assert r.status_code == 200
        d = r.json()
        assert d["total_assets"] == 2
        assert d["total_outstanding_eur"] == 80_000_000
        assert len(d["by_asset_class"]) == 2
        # Regulatory disclosure present
        rd = d["regulatory_disclosure"]
        assert rd["sfdr_pai_1_financed_ghg_tco2e"] > 0
        assert rd["sfdr_pai_2_carbon_footprint_tco2e_per_meur"] > 0

    def test_single_asset_class(self):
        r = requests.post(f"{PCAF}/portfolio-aggregate", json={
            "reporting_year": 2024,
            "mortgages": {
                "assets": [{
                    "asset_id": "MG001", "outstanding_eur": 200_000,
                    "property_value_eur": 350_000, "floor_area_m2": 120,
                    "epc_rating": "C",
                }],
                "reporting_year": 2024,
            },
        })
        assert r.status_code == 200
        d = r.json()
        assert d["total_assets"] == 1
        assert len(d["by_asset_class"]) == 1


# =====================================================================
# SAT Coal Phase-Out Checker
# =====================================================================

class TestSATCoal:
    def test_thresholds(self):
        r = requests.get(f"{SAT}/thresholds")
        assert r.status_code == 200
        d = r.json()
        assert d["revenue_thresholds"]["exclusion"] == 25.0
        assert d["phase_out_deadlines"]["OECD"] == 2030
        assert len(d["criteria"]) == 5

    def test_green_entity(self):
        """All 5 criteria met -> GREEN"""
        r = requests.post(f"{SAT}/check", json={
            "entities": [{
                "entity_id": "E001",
                "entity_name": "GreenPower Corp",
                "country_iso": "DE",
                "is_oecd": True,
                "sector": "Utilities",
                "total_revenue_eur": 10_000_000_000,
                "thermal_coal_revenue_eur": 100_000_000,  # 1%
                "no_new_coal_since_2021": True,
                "has_phase_out_commitment": True,
                "phase_out_target_year": 2028,
                "has_transition_plan": True,
                "transition_plan_verified": True,
                "has_just_transition_plan": True,
                "coal_revenue_declining_yoy": True,
            }],
        })
        assert r.status_code == 200
        d = r.json()
        ent = d["entity_results"][0]
        assert ent["rag_status"] == "GREEN"
        assert ent["criteria_met"] == 5
        assert ent["phase_out_aligned"] is True

    def test_red_entity_exclusion(self):
        """Revenue > 25% and not declining -> RED"""
        r = requests.post(f"{SAT}/check", json={
            "entities": [{
                "entity_id": "E002",
                "entity_name": "CoalHeavy Mining",
                "country_iso": "IN",
                "is_oecd": False,
                "sector": "Mining",
                "total_revenue_eur": 5_000_000_000,
                "thermal_coal_revenue_eur": 2_000_000_000,  # 40%
                "no_new_coal_since_2021": False,
                "has_phase_out_commitment": False,
                "new_coal_projects_announced": 3,
                "coal_expansion_capex_eur": 500_000_000,
                "coal_revenue_declining_yoy": False,
            }],
        })
        assert r.status_code == 200
        d = r.json()
        ent = d["entity_results"][0]
        assert ent["rag_status"] == "RED"
        assert ent["revenue_classification"] == "Exclusion"
        assert ent["thermal_coal_revenue_pct"] == 40.0
        assert ent["expansion_risk"] == "HIGH"
        assert "EXCLUSION" in ent["recommendation"]

    def test_amber_entity(self):
        """3-4 criteria met -> AMBER"""
        r = requests.post(f"{SAT}/check", json={
            "entities": [{
                "entity_id": "E003",
                "entity_name": "TransitionUtil Corp",
                "country_iso": "PL",
                "is_oecd": True,
                "sector": "Utilities",
                "total_revenue_eur": 8_000_000_000,
                "thermal_coal_revenue_eur": 800_000_000,  # 10%
                "no_new_coal_since_2021": True,
                "has_phase_out_commitment": True,
                "phase_out_target_year": 2032,  # Past 2030 OECD deadline
                "has_transition_plan": True,
                "transition_plan_verified": True,   # verified -> C3 met
                "has_just_transition_plan": False,   # C4 not met
                "coal_revenue_declining_yoy": True,  # C5 met (10% < 25%)
            }],
        })
        # C1 (no new coal) + C3 (transition plan verified) + C5 (revenue declining) = 3 met
        assert r.status_code == 200
        d = r.json()
        ent = d["entity_results"][0]
        assert ent["rag_status"] == "AMBER"
        assert ent["criteria_met"] == 3

    def test_portfolio_coal_concentration(self):
        r = requests.post(f"{SAT}/check", json={
            "entities": [
                {"entity_id": "E001", "entity_name": "Green Co", "total_revenue_eur": 10e9,
                 "thermal_coal_revenue_eur": 100e6, "no_new_coal_since_2021": True,
                 "has_phase_out_commitment": True, "phase_out_target_year": 2028,
                 "has_transition_plan": True, "transition_plan_verified": True,
                 "has_just_transition_plan": True, "coal_revenue_declining_yoy": True},
                {"entity_id": "E002", "entity_name": "Coal Co", "total_revenue_eur": 5e9,
                 "thermal_coal_revenue_eur": 2e9, "no_new_coal_since_2021": False},
            ],
        })
        assert r.status_code == 200
        d = r.json()
        assert d["total_entities"] == 2
        assert d["entities_exclusion"] >= 1
        assert d["portfolio_coal_exposure_pct"] > 0

    def test_revenue_classification_watchlist(self):
        r = requests.post(f"{SAT}/check", json={
            "entities": [{
                "entity_id": "E004",
                "entity_name": "WatchlistCo",
                "total_revenue_eur": 10e9,
                "thermal_coal_revenue_eur": 1.5e9,  # 15%
                "no_new_coal_since_2021": True,
                "has_phase_out_commitment": True,
                "phase_out_target_year": 2029,
                "has_transition_plan": True,
                "transition_plan_verified": True,
                "has_just_transition_plan": True,
                "coal_revenue_declining_yoy": True,
            }],
        })
        d = r.json()
        assert d["entity_results"][0]["revenue_classification"] == "Watchlist"

    def test_empty_request_rejected(self):
        r = requests.post(f"{SAT}/check", json={"entities": []})
        assert r.status_code == 400

    def test_gem_summary(self):
        r = requests.get(f"{SAT}/gem-summary")
        assert r.status_code == 200

    def test_policy_reference_in_response(self):
        r = requests.post(f"{SAT}/check", json={
            "entities": [{
                "entity_id": "E005", "entity_name": "Test Co",
                "total_revenue_eur": 1e9,
                "thermal_coal_revenue_eur": 0,
                "no_new_coal_since_2021": True,
                "has_phase_out_commitment": True,
                "phase_out_target_year": 2028,
                "has_transition_plan": True,
                "transition_plan_verified": True,
                "has_just_transition_plan": True,
                "coal_revenue_declining_yoy": True,
            }],
        })
        d = r.json()
        assert "iea_nze" in d["policy_reference"]
        assert "nzba" in d["policy_reference"]

    def test_expansion_override_to_red(self):
        """Active coal expansion -> RED regardless of criteria count"""
        r = requests.post(f"{SAT}/check", json={
            "entities": [{
                "entity_id": "E006", "entity_name": "Expand Co",
                "total_revenue_eur": 10e9,
                "thermal_coal_revenue_eur": 500e6,  # 5%
                "no_new_coal_since_2021": False,
                "has_phase_out_commitment": True,
                "phase_out_target_year": 2029,
                "has_transition_plan": True,
                "transition_plan_verified": True,
                "has_just_transition_plan": True,
                "coal_revenue_declining_yoy": True,
                "new_coal_projects_announced": 2,
                "coal_expansion_capex_eur": 300e6,
            }],
        })
        d = r.json()
        assert d["entity_results"][0]["rag_status"] == "RED"
        assert "EXPANSION" in d["entity_results"][0]["rag_detail"]


# =====================================================================
# PCAF Advanced — Security / Fund / Portfolio / Index Analytics
# =====================================================================

ADV = f"{BASE}/api/v1/pcaf/advanced"


class TestAdvancedIndices:
    """Index benchmark profiles and reference data."""

    def test_list_indices(self):
        r = requests.get(f"{ADV}/indices")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] == 8
        assert "MSCI_WORLD" in d["indices"]
        assert "SP500" in d["indices"]
        assert "MSCI_WORLD_PAB" in d["indices"]

    def test_get_index_profile(self):
        r = requests.get(f"{ADV}/indices/MSCI_WORLD")
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "MSCI World"
        assert d["constituents"] == 1509
        assert d["carbon_footprint_tco2e_meur"] > 0
        assert "sector_breakdown" in d

    def test_index_not_found(self):
        r = requests.get(f"{ADV}/indices/NONEXISTENT")
        assert r.status_code == 404

    def test_paris_aligned_benchmark_low_fossil(self):
        r = requests.get(f"{ADV}/indices/MSCI_WORLD_PAB")
        d = r.json()
        assert d["fossil_fuel_exposure_pct"] < 1.0
        assert d["implied_temp_c"] < 2.0


class TestAdvancedReferenceData:
    """Expanded global reference data endpoints."""

    def test_gics_sub_sectors(self):
        r = requests.get(f"{ADV}/gics-sub-sectors")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 50

    def test_sovereign_coverage(self):
        r = requests.get(f"{ADV}/sovereign-coverage")
        assert r.status_code == 200
        d = r.json()
        assert d["countries"] >= 120

    def test_nze_pathways(self):
        r = requests.get(f"{ADV}/nze-pathways")
        assert r.status_code == 200
        d = r.json()
        assert "Energy" in d["pathways"]
        assert "2050" in d["pathways"]["Energy"]
        # NZE 2050 intensity should be near-zero
        assert d["pathways"]["Energy"]["2050"] < 20

    def test_nace_gics_mapping(self):
        r = requests.get(f"{ADV}/nace-gics-mapping")
        assert r.status_code == 200
        d = r.json()
        assert d["mapping"]["K"] == "Financials"
        assert d["mapping"]["Q"] == "Health Care"


class TestAdvancedSecurityLevel:
    """Security/instrument-level financed-emission assessment."""

    def test_equity_with_verified_data(self):
        r = requests.post(f"{ADV}/securities", json={
            "securities": [{
                "isin": "US0378331005", "name": "Apple Inc",
                "instrument_type": "equity", "sector": "Information Technology",
                "country_iso2": "US", "market_value_eur": 50e6,
                "evic_eur": 3e12, "scope1_tco2e": 55000, "scope2_tco2e": 850000,
                "emissions_verified": True, "annual_revenue_eur": 383e9,
                "has_sbti_target": True, "sbti_status": "committed",
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["total_securities"] == 1
        sec = d["results"][0]
        assert sec["data_quality_score"] == 1  # verified
        assert sec["sbti_status"] == "committed"
        assert sec["fossil_fuel_flag"] is False
        assert sec["implied_temperature_c"] is not None
        assert sec["transition_risk_level"] == "low"

    def test_sovereign_bond_auto_emissions(self):
        r = requests.post(f"{ADV}/securities", json={
            "securities": [{
                "name": "US Treasury", "instrument_type": "sovereign_bond",
                "country_iso2": "US", "market_value_eur": 100e6,
                "outstanding_amount_eur": 100e6,
            }],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        sec = r.json()["results"][0]
        assert sec["pcaf_asset_class"] == "sovereign_bonds"
        assert sec["financed_total_tco2e"] > 0
        assert sec["data_quality_score"] == 5  # no company-specific data
        assert sec["af_formula"] == "Outstanding / PPP-GDP (EUR)"

    def test_fossil_fuel_flag(self):
        r = requests.post(f"{ADV}/securities", json={
            "securities": [{
                "name": "Oil Major", "instrument_type": "equity",
                "sector": "Energy", "country_iso2": "GB",
                "market_value_eur": 10e6, "evic_eur": 100e9,
                "scope1_tco2e": 30e6, "scope2_tco2e": 5e6,
                "emissions_verified": True, "annual_revenue_eur": 200e9,
                "coal_revenue_pct": 10,
            }],
            "reporting_year": 2024,
        })
        sec = r.json()["results"][0]
        assert sec["fossil_fuel_flag"] is True
        assert sec["transition_risk_level"] in ("medium", "high")

    def test_benchmark_comparison(self):
        r = requests.post(f"{ADV}/securities", json={
            "securities": [{
                "name": "Low Carbon Co", "instrument_type": "equity",
                "sector": "Information Technology", "country_iso2": "US",
                "market_value_eur": 10e6, "evic_eur": 500e9,
                "scope1_tco2e": 1000, "scope2_tco2e": 5000,
                "emissions_verified": True, "annual_revenue_eur": 50e9,
            }],
            "reporting_year": 2024,
            "benchmark_index": "MSCI_WORLD",
        })
        d = r.json()
        assert d["benchmark_carbon_footprint"] == 68.2
        assert d["carbon_footprint_vs_benchmark_pct"] is not None

    def test_multi_instrument_types(self):
        """Mix of equity, corporate bond, sovereign, green bond."""
        r = requests.post(f"{ADV}/securities", json={
            "securities": [
                {"name": "Equity A", "instrument_type": "equity", "sector": "Financials",
                 "market_value_eur": 20e6, "evic_eur": 100e9,
                 "scope1_tco2e": 5000, "scope2_tco2e": 8000, "annual_revenue_eur": 40e9},
                {"name": "Corp Bond B", "instrument_type": "corporate_bond", "sector": "Utilities",
                 "market_value_eur": 15e6, "evic_eur": 80e9,
                 "scope1_tco2e": 500000, "scope2_tco2e": 50000, "annual_revenue_eur": 20e9},
                {"name": "DE Bund", "instrument_type": "sovereign_bond", "country_iso2": "DE",
                 "market_value_eur": 30e6, "outstanding_amount_eur": 30e6},
                {"name": "Green Bond X", "instrument_type": "green_bond", "sector": "Utilities",
                 "market_value_eur": 10e6, "evic_eur": 50e9,
                 "scope1_tco2e": 100, "scope2_tco2e": 200, "emissions_verified": True,
                 "green_bond_certified": True, "taxonomy_aligned_pct": 90},
            ],
            "reporting_year": 2024,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["total_securities"] == 4
        types = {s["instrument_type"] for s in d["results"]}
        assert types == {"equity", "corporate_bond", "sovereign_bond", "green_bond"}


class TestAdvancedFundLevel:
    """Fund-level look-through analytics."""

    def test_fund_basic(self):
        r = requests.post(f"{ADV}/fund", json={
            "fund_name": "Test Fund", "fund_type": "equity_fund",
            "total_nav_eur": 100e6,
            "holdings": [
                {"name": "Holding A", "instrument_type": "equity", "sector": "Financials",
                 "market_value_eur": 50e6, "evic_eur": 200e9,
                 "scope1_tco2e": 10000, "scope2_tco2e": 20000, "annual_revenue_eur": 80e9},
                {"name": "Holding B", "instrument_type": "equity", "sector": "Materials",
                 "market_value_eur": 30e6, "evic_eur": 50e9,
                 "scope1_tco2e": 500000, "scope2_tco2e": 100000, "annual_revenue_eur": 30e9},
            ],
        })
        assert r.status_code == 200
        d = r.json()
        assert d["holdings_count"] == 2
        assert d["financed_total_tco2e"] > 0
        assert d["carbon_footprint_tco2e_per_meur"] > 0
        assert len(d["sector_carbon_breakdown"]) >= 2
        assert d["sfdr_pai_1_tco2e"] > 0

    def test_fund_benchmark_delta(self):
        r = requests.post(f"{ADV}/fund", json={
            "fund_name": "Benchmark Fund", "fund_type": "equity_fund",
            "total_nav_eur": 200e6, "benchmark_index": "SP500",
            "holdings": [
                {"name": "H1", "instrument_type": "equity", "sector": "Information Technology",
                 "market_value_eur": 100e6, "evic_eur": 2e12,
                 "scope1_tco2e": 50000, "scope2_tco2e": 400000,
                 "emissions_verified": True, "annual_revenue_eur": 300e9},
                {"name": "H2", "instrument_type": "equity", "sector": "Health Care",
                 "market_value_eur": 80e6, "evic_eur": 500e9,
                 "scope1_tco2e": 5000, "scope2_tco2e": 8000,
                 "annual_revenue_eur": 60e9},
            ],
        })
        assert r.status_code == 200
        d = r.json()
        assert d["benchmark_index"] == "SP500"
        assert d["benchmark_carbon_footprint"] == 62.5
        assert d["carbon_footprint_vs_benchmark_pct"] is not None

    def test_fund_empty_holdings_rejected(self):
        r = requests.post(f"{ADV}/fund", json={
            "fund_name": "Empty Fund", "fund_type": "equity_fund",
            "total_nav_eur": 100e6, "holdings": [],
        })
        assert r.status_code == 400


class TestAdvancedPortfolioLevel:
    """Multi-fund + direct holdings portfolio analytics."""

    def test_portfolio_multi_fund(self):
        r = requests.post(f"{ADV}/portfolio", json={
            "portfolio_name": "Multi-Fund Portfolio", "reporting_year": 2024,
            "benchmark_index": "MSCI_WORLD",
            "funds": [
                {
                    "fund_name": "Equity Fund A", "fund_type": "equity_fund",
                    "total_nav_eur": 200e6,
                    "holdings": [
                        {"name": "Stock X", "instrument_type": "equity", "sector": "Financials",
                         "country_iso2": "US", "market_value_eur": 100e6, "evic_eur": 500e9,
                         "scope1_tco2e": 20000, "scope2_tco2e": 40000, "annual_revenue_eur": 100e9,
                         "has_sbti_target": True, "sbti_status": "target_set"},
                    ],
                },
                {
                    "fund_name": "Bond Fund B", "fund_type": "bond_fund",
                    "total_nav_eur": 100e6,
                    "holdings": [
                        {"name": "US Treas", "instrument_type": "sovereign_bond",
                         "country_iso2": "US", "market_value_eur": 80e6,
                         "outstanding_amount_eur": 80e6},
                    ],
                },
            ],
            "direct_holdings": [
                {"name": "Direct Equity Z", "instrument_type": "equity", "sector": "Utilities",
                 "country_iso2": "DE", "market_value_eur": 50e6, "evic_eur": 80e9,
                 "scope1_tco2e": 2e6, "scope2_tco2e": 300000, "annual_revenue_eur": 25e9},
            ],
        })
        assert r.status_code == 200
        d = r.json()
        assert d["total_securities"] == 3
        assert d["total_aum_eur"] > 0
        assert "sector_attribution" in d
        assert "country_attribution" in d
        assert "asset_class_attribution" in d
        assert len(d["top_10_emitters"]) <= 10
        assert d["nzif_portfolio_coverage_pct"] is not None
        # Fund results nested
        assert len(d["fund_results"]) == 2
        assert len(d["direct_holdings_results"]) == 1

    def test_portfolio_regulatory_metrics(self):
        """SFDR PAI #1-#4 present in portfolio response."""
        r = requests.post(f"{ADV}/portfolio", json={
            "portfolio_name": "Regulatory Test", "reporting_year": 2024,
            "direct_holdings": [
                {"name": "Stock A", "instrument_type": "equity", "sector": "Energy",
                 "market_value_eur": 50e6, "evic_eur": 200e9,
                 "scope1_tco2e": 10e6, "scope2_tco2e": 1e6, "annual_revenue_eur": 100e9,
                 "coal_revenue_pct": 15},
            ],
        })
        assert r.status_code == 200
        d = r.json()
        assert d["sfdr_pai_1_tco2e"] > 0
        assert d["sfdr_pai_2_tco2e_per_meur"] > 0
        assert d["sfdr_pai_4_fossil_pct"] > 0
        assert d["fossil_fuel_exposure_pct"] > 0


class TestAdvancedIndexComparison:
    """Portfolio vs index benchmark comparison."""

    def test_compare_to_index(self):
        r = requests.post(f"{ADV}/compare-to-index", json={
            "securities": [
                {"name": "Green Stock", "instrument_type": "equity",
                 "sector": "Information Technology", "country_iso2": "US",
                 "market_value_eur": 100e6, "evic_eur": 1e12,
                 "scope1_tco2e": 5000, "scope2_tco2e": 20000,
                 "emissions_verified": True, "annual_revenue_eur": 100e9},
            ],
            "reporting_year": 2024,
            "benchmark_index": "MSCI_WORLD",
        })
        assert r.status_code == 200
        d = r.json()
        assert "portfolio" in d
        assert "benchmark" in d
        assert "delta" in d
        assert d["benchmark"]["name"] == "MSCI World"
        assert d["delta"]["carbon_footprint_pct"] is not None

    def test_compare_no_benchmark_rejected(self):
        r = requests.post(f"{ADV}/compare-to-index", json={
            "securities": [
                {"name": "S1", "instrument_type": "equity",
                 "market_value_eur": 10e6, "evic_eur": 100e9},
            ],
            "reporting_year": 2024,
        })
        assert r.status_code == 400


# =====================================================================
# Run
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-q"])
