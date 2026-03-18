"""
E100 — Multi-Regulatory Climate Stress Test Orchestrator
=========================================================
Standards covered:
- NGFS Phase IV Scenarios (2024 vintage) — 7 scenarios
- ECB Climate Stress Test 2022 (SREP CET1 threshold 4.5%)
- EBA 2023 Climate Risk Stress Test (CET1 threshold 4.5%)
- BoE CBES 2021 (Tier1 threshold 4.0%)
- APRA CPG 229 2022 (CET1 threshold 7.0%)
- MAS Climate Scenario Stress Test 2022 (CET1 threshold 6.5%)
- RBI Climate Risk Guidance 2022 (CET1 threshold 7.0%)
- 20 NACE sector risk profiles
- 5 macro-financial transmission channels
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# NGFS Phase IV (2024) scenario reference data
# ---------------------------------------------------------------------------

NGFS_PHASE4_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "net_zero_2050": {
        "name": "Net Zero 2050",
        "description": "Immediate, coordinated global action — 1.5°C pathway",
        "temperature_c": 1.5,
        "type": "orderly",
        "carbon_price_usd_t": {2025: 75, 2030: 160, 2040: 350, 2050: 700},
        "gdp_deviation_pct": {2025: -0.8, 2030: -1.5, 2040: -0.5, 2050: 1.2},
        "unemployment_shock_pp": {2025: 0.3, 2030: 0.4, 2040: 0.1, 2050: -0.2},
        "energy_price_multiplier": {2025: 1.15, 2030: 1.35, 2040: 1.1, 2050: 0.85},
        "physical_risk_damage_pct": 2.5,
        "transition_loss_pct": 3.8,
        "fossil_fuel_stranding_pct": 18.0,
        "green_investment_gdp_pct": 4.5,
        "policy_certainty": "high",
    },
    "below_2c": {
        "name": "Below 2°C",
        "description": "Strong but not full decarbonisation — 1.8°C pathway",
        "temperature_c": 1.8,
        "type": "orderly",
        "carbon_price_usd_t": {2025: 55, 2030: 110, 2040: 230, 2050: 450},
        "gdp_deviation_pct": {2025: -0.5, 2030: -1.1, 2040: -0.3, 2050: 0.8},
        "unemployment_shock_pp": {2025: 0.2, 2030: 0.3, 2040: 0.1, 2050: -0.1},
        "energy_price_multiplier": {2025: 1.10, 2030: 1.25, 2040: 1.05, 2050: 0.90},
        "physical_risk_damage_pct": 4.0,
        "transition_loss_pct": 2.9,
        "fossil_fuel_stranding_pct": 14.0,
        "green_investment_gdp_pct": 3.5,
        "policy_certainty": "high",
    },
    "nationally_determined": {
        "name": "Nationally Determined Contributions",
        "description": "Countries implement current NDC pledges — 2.5°C pathway",
        "temperature_c": 2.5,
        "type": "ndp",
        "carbon_price_usd_t": {2025: 30, 2030: 60, 2040: 110, 2050: 180},
        "gdp_deviation_pct": {2025: -0.3, 2030: -0.8, 2040: -1.2, 2050: -2.1},
        "unemployment_shock_pp": {2025: 0.1, 2030: 0.2, 2040: 0.5, 2050: 0.8},
        "energy_price_multiplier": {2025: 1.05, 2030: 1.15, 2040: 1.20, 2050: 1.35},
        "physical_risk_damage_pct": 8.5,
        "transition_loss_pct": 1.8,
        "fossil_fuel_stranding_pct": 8.0,
        "green_investment_gdp_pct": 2.0,
        "policy_certainty": "medium",
    },
    "delayed_transition": {
        "name": "Delayed Transition",
        "description": "Policy inaction until 2030, then abrupt tightening — 1.8°C disorderly",
        "temperature_c": 1.8,
        "type": "disorderly",
        "carbon_price_usd_t": {2025: 15, 2030: 140, 2040: 420, 2050: 680},
        "gdp_deviation_pct": {2025: 0.1, 2030: -3.5, 2040: -2.8, 2050: -1.2},
        "unemployment_shock_pp": {2025: -0.1, 2030: 1.8, 2040: 1.2, 2050: 0.5},
        "energy_price_multiplier": {2025: 1.00, 2030: 1.80, 2040: 1.50, 2050: 1.10},
        "physical_risk_damage_pct": 5.5,
        "transition_loss_pct": 7.2,
        "fossil_fuel_stranding_pct": 22.0,
        "green_investment_gdp_pct": 6.0,
        "policy_certainty": "low",
    },
    "divergent_net_zero": {
        "name": "Divergent Net Zero",
        "description": "1.5°C achieved via uncoordinated national policies — divergent pathways",
        "temperature_c": 1.5,
        "type": "disorderly",
        "carbon_price_usd_t": {2025: 50, 2030: 130, 2040: 310, 2050: 600},
        "gdp_deviation_pct": {2025: -1.0, 2030: -2.2, 2040: -1.8, 2050: -0.5},
        "unemployment_shock_pp": {2025: 0.5, 2030: 1.0, 2040: 0.8, 2050: 0.2},
        "energy_price_multiplier": {2025: 1.20, 2030: 1.60, 2040: 1.30, 2050: 0.95},
        "physical_risk_damage_pct": 3.2,
        "transition_loss_pct": 5.9,
        "fossil_fuel_stranding_pct": 20.0,
        "green_investment_gdp_pct": 5.0,
        "policy_certainty": "low",
    },
    "current_policies": {
        "name": "Current Policies",
        "description": "No new policies — hot house world — 2.9°C pathway",
        "temperature_c": 2.9,
        "type": "hot_house",
        "carbon_price_usd_t": {2025: 12, 2030: 18, 2040: 25, 2050: 35},
        "gdp_deviation_pct": {2025: 0.2, 2030: 0.0, 2040: -2.5, 2050: -7.5},
        "unemployment_shock_pp": {2025: 0.0, 2030: 0.1, 2040: 1.2, 2050: 3.5},
        "energy_price_multiplier": {2025: 1.00, 2030: 1.05, 2040: 1.25, 2050: 1.80},
        "physical_risk_damage_pct": 18.0,
        "transition_loss_pct": 0.5,
        "fossil_fuel_stranding_pct": 3.0,
        "green_investment_gdp_pct": 0.8,
        "policy_certainty": "high",
    },
    "low_demand": {
        "name": "Low Energy Demand (Degrowth)",
        "description": "Radical demand reduction + social change — 1.4°C pathway",
        "temperature_c": 1.4,
        "type": "orderly",
        "carbon_price_usd_t": {2025: 40, 2030: 80, 2040: 150, 2050: 250},
        "gdp_deviation_pct": {2025: -1.5, 2030: -2.8, 2040: -2.0, 2050: -1.5},
        "unemployment_shock_pp": {2025: 0.8, 2030: 1.2, 2040: 0.5, 2050: -0.3},
        "energy_price_multiplier": {2025: 0.90, 2030: 0.80, 2040: 0.70, 2050: 0.60},
        "physical_risk_damage_pct": 2.0,
        "transition_loss_pct": 4.5,
        "fossil_fuel_stranding_pct": 28.0,
        "green_investment_gdp_pct": 3.0,
        "policy_certainty": "medium",
    },
}


# ---------------------------------------------------------------------------
# Regulatory framework profiles
# ---------------------------------------------------------------------------

REGULATORY_FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "ECB_2022": {
        "name": "ECB Climate Stress Test 2022",
        "supervisor": "European Central Bank",
        "jurisdiction": ["EU", "Euro Area"],
        "cet1_threshold_pct": 4.5,
        "capital_metric": "CET1",
        "time_horizon_years": [2025, 2030, 2050],
        "scenarios_supported": [
            "net_zero_2050", "below_2c", "delayed_transition",
            "current_policies", "divergent_net_zero",
        ],
        "mandatory": True,
        "sector_risk_weights": {
            "energy": 1.30, "mining": 1.25, "utilities": 1.20,
            "transport": 1.15, "manufacturing": 1.10, "construction": 1.08,
            "agriculture": 1.12, "real_estate": 1.10, "financial": 0.95,
            "technology": 0.85,
        },
        "submission_template_fields": [
            "entity_lei", "reporting_date", "scenario_id", "time_horizon",
            "baseline_cet1", "stressed_cet1", "expected_loss_bn",
            "rwa_bn", "sector_breakdown", "pd_migration_matrix",
            "lgd_uplift_table", "physical_risk_exposure", "transition_risk_exposure",
            "nace_sector_heatmap", "counterfactual_comparison",
        ],
        "legal_basis": "ECB Banking Supervision — Supervisory letter July 2022",
        "next_exercise": "2025-Q3",
    },
    "EBA_2023": {
        "name": "EBA Climate Risk Stress Test 2023",
        "supervisor": "European Banking Authority",
        "jurisdiction": ["EU"],
        "cet1_threshold_pct": 4.5,
        "capital_metric": "CET1",
        "time_horizon_years": [2025, 2030, 2040, 2050],
        "scenarios_supported": [
            "net_zero_2050", "below_2c", "nationally_determined",
            "delayed_transition", "current_policies",
        ],
        "mandatory": True,
        "sector_risk_weights": {
            "energy": 1.35, "mining": 1.30, "utilities": 1.22,
            "transport": 1.18, "manufacturing": 1.12, "construction": 1.10,
            "agriculture": 1.15, "real_estate": 1.12, "financial": 0.92,
            "technology": 0.80,
        },
        "submission_template_fields": [
            "entity_lei", "reporting_date", "scenario_id", "pillar_2r_impact",
            "baseline_cet1", "stressed_cet1", "expected_loss_bn",
            "rwa_bn", "nace_sector_breakdown", "pd_migration",
            "lgd_uplift", "carbon_related_assets_pct",
            "green_asset_ratio", "financed_emissions_tco2e",
            "concentration_risk_by_sector", "transition_plan_assessment",
        ],
        "legal_basis": "EBA/GL/2020/01 — CRR Article 177/178",
        "next_exercise": "2025-Q1",
    },
    "BoE_CBES_2021": {
        "name": "Bank of England Climate Biennial Exploratory Scenario 2021",
        "supervisor": "Bank of England (PRA / FCA)",
        "jurisdiction": ["UK"],
        "cet1_threshold_pct": 4.0,
        "capital_metric": "Tier1",
        "time_horizon_years": [2025, 2030, 2050],
        "scenarios_supported": [
            "net_zero_2050", "delayed_transition", "current_policies",
            "below_2c",
        ],
        "mandatory": True,
        "sector_risk_weights": {
            "energy": 1.28, "mining": 1.22, "utilities": 1.18,
            "transport": 1.14, "manufacturing": 1.08, "construction": 1.06,
            "agriculture": 1.10, "real_estate": 1.08, "financial": 0.90,
            "technology": 0.82,
        },
        "submission_template_fields": [
            "entity_name", "reporting_date", "scenario_name",
            "baseline_tier1", "stressed_tier1", "expected_loss_bn",
            "rwa_bn", "sector_pd_matrix", "lgd_shock_table",
            "physical_risk_loss", "transition_risk_loss",
            "insurance_losses", "mortgage_ltv_shift",
            "management_actions", "climate_va_r",
        ],
        "legal_basis": "PRA SS3/19 — Supervisory Statement Enhancing banks' and insurers' approaches to managing the financial risks from climate change",
        "next_exercise": "2025-CBES",
    },
    "APRA_2022": {
        "name": "APRA CPG 229 Climate Change Financial Risks 2022",
        "supervisor": "Australian Prudential Regulation Authority",
        "jurisdiction": ["Australia"],
        "cet1_threshold_pct": 7.0,
        "capital_metric": "CET1",
        "time_horizon_years": [2030, 2050],
        "scenarios_supported": [
            "net_zero_2050", "below_2c", "nationally_determined",
            "current_policies", "delayed_transition",
        ],
        "mandatory": False,
        "sector_risk_weights": {
            "energy": 1.40, "mining": 1.38, "utilities": 1.25,
            "transport": 1.18, "manufacturing": 1.15, "construction": 1.12,
            "agriculture": 1.20, "real_estate": 1.15, "financial": 0.95,
            "technology": 0.88,
        },
        "submission_template_fields": [
            "entity_name", "reporting_date", "scenario_id",
            "baseline_cet1", "stressed_cet1", "expected_credit_loss_bn",
            "rwa_bn", "physical_risk_exposure_au", "transition_risk_exposure_au",
            "sector_concentration", "climate_scenario_narrative",
            "governance_statement", "risk_appetite_climate",
        ],
        "legal_basis": "APRA CPG 229 — Climate Change: Prudential Practice Guide",
        "next_exercise": "2026-H1",
    },
    "MAS_2022": {
        "name": "MAS Climate Scenario Stress Test 2022",
        "supervisor": "Monetary Authority of Singapore",
        "jurisdiction": ["Singapore"],
        "cet1_threshold_pct": 6.5,
        "capital_metric": "CET1",
        "time_horizon_years": [2030, 2050],
        "scenarios_supported": [
            "net_zero_2050", "below_2c", "nationally_determined",
            "delayed_transition", "current_policies",
        ],
        "mandatory": True,
        "sector_risk_weights": {
            "energy": 1.32, "mining": 1.28, "utilities": 1.20,
            "transport": 1.16, "manufacturing": 1.12, "construction": 1.08,
            "agriculture": 1.14, "real_estate": 1.10, "financial": 0.93,
            "technology": 0.85,
        },
        "submission_template_fields": [
            "entity_name", "reporting_date", "scenario_id",
            "baseline_cet1", "stressed_cet1", "expected_loss_sgd_bn",
            "rwa_sgd_bn", "sector_breakdown", "pd_matrix",
            "lgd_uplift", "south_east_asia_physical_risk",
            "transition_risk_apac", "green_finance_taxonomy_sg",
        ],
        "legal_basis": "MAS Notice 637 — Technology Risk Management / MAS Guidelines on Environmental Risk Management",
        "next_exercise": "2024-Q4",
    },
    "RBI_2022": {
        "name": "RBI Climate Risk Guidance 2022",
        "supervisor": "Reserve Bank of India",
        "jurisdiction": ["India"],
        "cet1_threshold_pct": 7.0,
        "capital_metric": "CET1",
        "time_horizon_years": [2030, 2050],
        "scenarios_supported": [
            "net_zero_2050", "nationally_determined",
            "current_policies", "delayed_transition",
        ],
        "mandatory": False,
        "sector_risk_weights": {
            "energy": 1.38, "mining": 1.35, "utilities": 1.28,
            "transport": 1.20, "manufacturing": 1.16, "construction": 1.14,
            "agriculture": 1.25, "real_estate": 1.12, "financial": 0.96,
            "technology": 0.88,
        },
        "submission_template_fields": [
            "entity_name", "reporting_date", "scenario_id",
            "baseline_cet1", "stressed_cet1", "expected_loss_inr_bn",
            "rwa_inr_bn", "sector_exposure_classification",
            "physical_risk_monsoon_heat", "transition_risk_india",
            "priority_sector_climate_exposure",
            "rbi_climate_disclosure_alignment",
        ],
        "legal_basis": "RBI Discussion Paper on Climate Risk and Sustainable Finance — July 2022",
        "next_exercise": "2025-H2",
    },
}


# ---------------------------------------------------------------------------
# NACE sector risk profiles (20 sectors)
# ---------------------------------------------------------------------------

NACE_SECTOR_RISK_PROFILES: Dict[str, Dict[str, Any]] = {
    "energy_fossil": {
        "nace_code": "B06/B09/D35.11",
        "description": "Fossil fuel extraction & conventional power generation",
        "carbon_intensity_kg_keur": 2800,
        "stranded_asset_pct": 35.0,
        "revenue_at_risk_pct": 42.0,
        "baseline_pd_pct": 1.8,
        "baseline_lgd_pct": 42.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 4.5, "below_2c": 3.2, "nationally_determined": 1.8,
            "delayed_transition": 5.8, "divergent_net_zero": 4.9,
            "current_policies": 0.8, "low_demand": 5.2,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.55, "below_2c": 1.42, "nationally_determined": 1.22,
            "delayed_transition": 1.70, "divergent_net_zero": 1.60,
            "current_policies": 1.12, "low_demand": 1.65,
        },
    },
    "energy_renewable": {
        "nace_code": "D35.11-R",
        "description": "Renewable power generation (wind, solar, hydro)",
        "carbon_intensity_kg_keur": 45,
        "stranded_asset_pct": 2.0,
        "revenue_at_risk_pct": 5.0,
        "baseline_pd_pct": 0.6,
        "baseline_lgd_pct": 32.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": -0.2, "below_2c": -0.1, "nationally_determined": 0.1,
            "delayed_transition": 0.8, "divergent_net_zero": 0.5,
            "current_policies": 1.2, "low_demand": 0.2,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 0.95, "below_2c": 0.97, "nationally_determined": 1.00,
            "delayed_transition": 1.08, "divergent_net_zero": 1.05,
            "current_policies": 1.15, "low_demand": 0.98,
        },
    },
    "mining": {
        "nace_code": "B05-B09",
        "description": "Coal, metal ore and other mining",
        "carbon_intensity_kg_keur": 1950,
        "stranded_asset_pct": 28.0,
        "revenue_at_risk_pct": 34.0,
        "baseline_pd_pct": 2.1,
        "baseline_lgd_pct": 45.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 3.8, "below_2c": 2.8, "nationally_determined": 1.5,
            "delayed_transition": 5.0, "divergent_net_zero": 4.2,
            "current_policies": 0.5, "low_demand": 4.8,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.48, "below_2c": 1.35, "nationally_determined": 1.18,
            "delayed_transition": 1.62, "divergent_net_zero": 1.52,
            "current_policies": 1.08, "low_demand": 1.58,
        },
    },
    "utilities_gas": {
        "nace_code": "D35.22",
        "description": "Gas distribution and gas-fired utilities",
        "carbon_intensity_kg_keur": 1400,
        "stranded_asset_pct": 22.0,
        "revenue_at_risk_pct": 28.0,
        "baseline_pd_pct": 1.2,
        "baseline_lgd_pct": 38.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 3.2, "below_2c": 2.4, "nationally_determined": 1.2,
            "delayed_transition": 4.5, "divergent_net_zero": 3.8,
            "current_policies": 0.4, "low_demand": 4.0,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.42, "below_2c": 1.30, "nationally_determined": 1.14,
            "delayed_transition": 1.58, "divergent_net_zero": 1.48,
            "current_policies": 1.06, "low_demand": 1.52,
        },
    },
    "transport_aviation": {
        "nace_code": "H51",
        "description": "Air transport — airlines and airports",
        "carbon_intensity_kg_keur": 1800,
        "stranded_asset_pct": 15.0,
        "revenue_at_risk_pct": 22.0,
        "baseline_pd_pct": 2.5,
        "baseline_lgd_pct": 48.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 2.8, "below_2c": 2.0, "nationally_determined": 1.0,
            "delayed_transition": 3.8, "divergent_net_zero": 3.2,
            "current_policies": 0.6, "low_demand": 4.5,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.35, "below_2c": 1.25, "nationally_determined": 1.10,
            "delayed_transition": 1.50, "divergent_net_zero": 1.42,
            "current_policies": 1.05, "low_demand": 1.55,
        },
    },
    "transport_road": {
        "nace_code": "H49",
        "description": "Road transport — freight and passenger",
        "carbon_intensity_kg_keur": 980,
        "stranded_asset_pct": 12.0,
        "revenue_at_risk_pct": 16.0,
        "baseline_pd_pct": 1.5,
        "baseline_lgd_pct": 40.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 1.8, "below_2c": 1.3, "nationally_determined": 0.7,
            "delayed_transition": 2.5, "divergent_net_zero": 2.0,
            "current_policies": 0.4, "low_demand": 2.8,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.22, "below_2c": 1.15, "nationally_determined": 1.07,
            "delayed_transition": 1.35, "divergent_net_zero": 1.28,
            "current_policies": 1.03, "low_demand": 1.38,
        },
    },
    "transport_shipping": {
        "nace_code": "H50",
        "description": "Maritime transport — international shipping",
        "carbon_intensity_kg_keur": 1250,
        "stranded_asset_pct": 18.0,
        "revenue_at_risk_pct": 25.0,
        "baseline_pd_pct": 2.0,
        "baseline_lgd_pct": 44.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 2.5, "below_2c": 1.8, "nationally_determined": 0.9,
            "delayed_transition": 3.5, "divergent_net_zero": 3.0,
            "current_policies": 0.5, "low_demand": 4.0,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.30, "below_2c": 1.20, "nationally_determined": 1.08,
            "delayed_transition": 1.45, "divergent_net_zero": 1.38,
            "current_policies": 1.04, "low_demand": 1.48,
        },
    },
    "manufacturing_steel": {
        "nace_code": "C24.1",
        "description": "Iron and steel production",
        "carbon_intensity_kg_keur": 2200,
        "stranded_asset_pct": 20.0,
        "revenue_at_risk_pct": 26.0,
        "baseline_pd_pct": 1.6,
        "baseline_lgd_pct": 42.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 2.2, "below_2c": 1.6, "nationally_determined": 0.8,
            "delayed_transition": 3.2, "divergent_net_zero": 2.7,
            "current_policies": 0.3, "low_demand": 3.5,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.28, "below_2c": 1.18, "nationally_determined": 1.06,
            "delayed_transition": 1.42, "divergent_net_zero": 1.35,
            "current_policies": 1.02, "low_demand": 1.45,
        },
    },
    "manufacturing_cement": {
        "nace_code": "C23.5",
        "description": "Cement and concrete production",
        "carbon_intensity_kg_keur": 2600,
        "stranded_asset_pct": 24.0,
        "revenue_at_risk_pct": 30.0,
        "baseline_pd_pct": 1.8,
        "baseline_lgd_pct": 43.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 2.5, "below_2c": 1.8, "nationally_determined": 0.9,
            "delayed_transition": 3.6, "divergent_net_zero": 3.0,
            "current_policies": 0.4, "low_demand": 3.8,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.32, "below_2c": 1.22, "nationally_determined": 1.07,
            "delayed_transition": 1.48, "divergent_net_zero": 1.40,
            "current_policies": 1.03, "low_demand": 1.50,
        },
    },
    "manufacturing_chemicals": {
        "nace_code": "C20",
        "description": "Chemical and petrochemical manufacturing",
        "carbon_intensity_kg_keur": 1600,
        "stranded_asset_pct": 18.0,
        "revenue_at_risk_pct": 22.0,
        "baseline_pd_pct": 1.3,
        "baseline_lgd_pct": 40.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 1.9, "below_2c": 1.4, "nationally_determined": 0.7,
            "delayed_transition": 2.8, "divergent_net_zero": 2.3,
            "current_policies": 0.3, "low_demand": 3.2,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.24, "below_2c": 1.16, "nationally_determined": 1.05,
            "delayed_transition": 1.38, "divergent_net_zero": 1.30,
            "current_policies": 1.02, "low_demand": 1.42,
        },
    },
    "construction": {
        "nace_code": "F",
        "description": "Construction and real estate development",
        "carbon_intensity_kg_keur": 680,
        "stranded_asset_pct": 10.0,
        "revenue_at_risk_pct": 14.0,
        "baseline_pd_pct": 1.8,
        "baseline_lgd_pct": 38.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 1.2, "below_2c": 0.9, "nationally_determined": 0.5,
            "delayed_transition": 1.8, "divergent_net_zero": 1.5,
            "current_policies": 0.4, "low_demand": 2.0,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.15, "below_2c": 1.10, "nationally_determined": 1.04,
            "delayed_transition": 1.25, "divergent_net_zero": 1.20,
            "current_policies": 1.05, "low_demand": 1.28,
        },
    },
    "agriculture": {
        "nace_code": "A01",
        "description": "Crop and animal production, hunting",
        "carbon_intensity_kg_keur": 1100,
        "stranded_asset_pct": 8.0,
        "revenue_at_risk_pct": 18.0,
        "baseline_pd_pct": 2.2,
        "baseline_lgd_pct": 35.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 1.5, "below_2c": 1.2, "nationally_determined": 0.8,
            "delayed_transition": 2.0, "divergent_net_zero": 1.8,
            "current_policies": 2.5, "low_demand": 0.8,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.18, "below_2c": 1.13, "nationally_determined": 1.06,
            "delayed_transition": 1.25, "divergent_net_zero": 1.22,
            "current_policies": 1.35, "low_demand": 1.05,
        },
    },
    "real_estate_commercial": {
        "nace_code": "L68-COM",
        "description": "Commercial real estate — offices, retail, logistics",
        "carbon_intensity_kg_keur": 420,
        "stranded_asset_pct": 12.0,
        "revenue_at_risk_pct": 15.0,
        "baseline_pd_pct": 1.4,
        "baseline_lgd_pct": 45.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 1.0, "below_2c": 0.8, "nationally_determined": 0.5,
            "delayed_transition": 1.5, "divergent_net_zero": 1.2,
            "current_policies": 1.8, "low_demand": 0.6,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.12, "below_2c": 1.08, "nationally_determined": 1.04,
            "delayed_transition": 1.20, "divergent_net_zero": 1.16,
            "current_policies": 1.28, "low_demand": 1.06,
        },
    },
    "real_estate_residential": {
        "nace_code": "L68-RES",
        "description": "Residential real estate — mortgages and housing",
        "carbon_intensity_kg_keur": 320,
        "stranded_asset_pct": 8.0,
        "revenue_at_risk_pct": 10.0,
        "baseline_pd_pct": 1.0,
        "baseline_lgd_pct": 35.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 0.7, "below_2c": 0.5, "nationally_determined": 0.3,
            "delayed_transition": 1.0, "divergent_net_zero": 0.8,
            "current_policies": 1.5, "low_demand": 0.4,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.08, "below_2c": 1.05, "nationally_determined": 1.02,
            "delayed_transition": 1.15, "divergent_net_zero": 1.12,
            "current_policies": 1.22, "low_demand": 1.04,
        },
    },
    "financial_services": {
        "nace_code": "K64-K66",
        "description": "Banking, insurance and financial services",
        "carbon_intensity_kg_keur": 85,
        "stranded_asset_pct": 3.0,
        "revenue_at_risk_pct": 6.0,
        "baseline_pd_pct": 0.8,
        "baseline_lgd_pct": 30.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 0.4, "below_2c": 0.3, "nationally_determined": 0.2,
            "delayed_transition": 0.8, "divergent_net_zero": 0.6,
            "current_policies": 1.0, "low_demand": 0.5,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.05, "below_2c": 1.03, "nationally_determined": 1.02,
            "delayed_transition": 1.10, "divergent_net_zero": 1.08,
            "current_policies": 1.15, "low_demand": 1.06,
        },
    },
    "technology": {
        "nace_code": "J58-J63",
        "description": "Information and communication technology",
        "carbon_intensity_kg_keur": 120,
        "stranded_asset_pct": 4.0,
        "revenue_at_risk_pct": 7.0,
        "baseline_pd_pct": 0.7,
        "baseline_lgd_pct": 28.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 0.2, "below_2c": 0.2, "nationally_determined": 0.1,
            "delayed_transition": 0.5, "divergent_net_zero": 0.4,
            "current_policies": 0.8, "low_demand": 0.3,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.03, "below_2c": 1.02, "nationally_determined": 1.01,
            "delayed_transition": 1.07, "divergent_net_zero": 1.05,
            "current_policies": 1.10, "low_demand": 1.04,
        },
    },
    "healthcare": {
        "nace_code": "Q86-Q88",
        "description": "Healthcare, hospitals and pharmaceuticals",
        "carbon_intensity_kg_keur": 210,
        "stranded_asset_pct": 3.0,
        "revenue_at_risk_pct": 5.0,
        "baseline_pd_pct": 0.6,
        "baseline_lgd_pct": 32.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 0.3, "below_2c": 0.2, "nationally_determined": 0.1,
            "delayed_transition": 0.5, "divergent_net_zero": 0.4,
            "current_policies": 1.2, "low_demand": 0.2,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.04, "below_2c": 1.03, "nationally_determined": 1.01,
            "delayed_transition": 1.08, "divergent_net_zero": 1.06,
            "current_policies": 1.18, "low_demand": 1.02,
        },
    },
    "food_beverage": {
        "nace_code": "C10-C12",
        "description": "Food and beverage manufacturing and processing",
        "carbon_intensity_kg_keur": 560,
        "stranded_asset_pct": 7.0,
        "revenue_at_risk_pct": 12.0,
        "baseline_pd_pct": 1.2,
        "baseline_lgd_pct": 36.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 1.0, "below_2c": 0.8, "nationally_determined": 0.4,
            "delayed_transition": 1.4, "divergent_net_zero": 1.2,
            "current_policies": 1.8, "low_demand": 0.5,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.12, "below_2c": 1.09, "nationally_determined": 1.03,
            "delayed_transition": 1.20, "divergent_net_zero": 1.16,
            "current_policies": 1.28, "low_demand": 1.04,
        },
    },
    "retail_wholesale": {
        "nace_code": "G45-G47",
        "description": "Retail and wholesale trade",
        "carbon_intensity_kg_keur": 340,
        "stranded_asset_pct": 5.0,
        "revenue_at_risk_pct": 9.0,
        "baseline_pd_pct": 1.5,
        "baseline_lgd_pct": 38.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 0.8, "below_2c": 0.6, "nationally_determined": 0.3,
            "delayed_transition": 1.2, "divergent_net_zero": 1.0,
            "current_policies": 1.5, "low_demand": 1.5,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.10, "below_2c": 1.07, "nationally_determined": 1.03,
            "delayed_transition": 1.18, "divergent_net_zero": 1.14,
            "current_policies": 1.25, "low_demand": 1.20,
        },
    },
    "automotive": {
        "nace_code": "C29",
        "description": "Motor vehicle manufacturing and supply chain",
        "carbon_intensity_kg_keur": 820,
        "stranded_asset_pct": 16.0,
        "revenue_at_risk_pct": 20.0,
        "baseline_pd_pct": 1.4,
        "baseline_lgd_pct": 40.0,
        "pd_uplift_by_scenario": {
            "net_zero_2050": 1.5, "below_2c": 1.1, "nationally_determined": 0.6,
            "delayed_transition": 2.2, "divergent_net_zero": 1.9,
            "current_policies": 0.5, "low_demand": 3.0,
        },
        "lgd_uplift_multiplier_by_scenario": {
            "net_zero_2050": 1.20, "below_2c": 1.14, "nationally_determined": 1.05,
            "delayed_transition": 1.32, "divergent_net_zero": 1.26,
            "current_policies": 1.04, "low_demand": 1.40,
        },
    },
}


# ---------------------------------------------------------------------------
# Physical risk multipliers by latitude band × peril
# ---------------------------------------------------------------------------

PHYSICAL_RISK_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "tropical": {
        "heat": 2.5, "flood": 2.2, "drought": 2.8, "storm": 2.0, "sea_level": 2.4,
    },
    "subtropical": {
        "heat": 2.0, "flood": 1.8, "drought": 2.2, "storm": 1.9, "sea_level": 1.8,
    },
    "temperate": {
        "heat": 1.5, "flood": 1.6, "drought": 1.5, "storm": 1.6, "sea_level": 1.4,
    },
    "boreal": {
        "heat": 1.2, "flood": 1.3, "drought": 1.1, "storm": 1.2, "sea_level": 1.1,
    },
    "polar": {
        "heat": 1.8, "flood": 1.5, "drought": 0.8, "storm": 1.1, "sea_level": 1.8,
    },
}

JURISDICTION_LATITUDE_BAND: Dict[str, str] = {
    "EU": "temperate", "UK": "temperate", "Australia": "subtropical",
    "Singapore": "tropical", "India": "tropical", "US": "temperate",
    "Japan": "temperate", "China": "temperate", "Brazil": "tropical",
    "Canada": "boreal", "Russia": "boreal", "Norway": "boreal",
    "South Africa": "subtropical", "Nigeria": "tropical",
}


# ---------------------------------------------------------------------------
# Transmission channel definitions
# ---------------------------------------------------------------------------

TRANSMISSION_CHANNELS: Dict[str, Dict[str, Any]] = {
    "carbon_price_channel": {
        "name": "Carbon Price → Operating Cost Channel",
        "mechanism": "Rising carbon prices increase energy and input costs, compressing EBITDA margins and raising PD probabilities for carbon-intensive sectors",
        "primary_risk": "transition",
        "affected_variables": ["PD", "EBITDA_margin", "revenue_at_risk"],
        "key_sectors": ["energy_fossil", "mining", "manufacturing_cement", "manufacturing_steel", "manufacturing_chemicals"],
        "amplifiers": ["border_carbon_adjustment", "energy_price_volatility", "stranded_asset_writedowns"],
        "transmission_lag_years": 1,
        "formula_note": "PD_delta = carbon_intensity_kg_keur × carbon_price_USD_t × exposure_sensitivity_factor / 1000",
    },
    "asset_stranding_channel": {
        "name": "Asset Stranding → LGD Channel",
        "mechanism": "Fossil fuel assets and carbon-intensive infrastructure become uneconomic, reducing collateral values and increasing LGD on secured loans",
        "primary_risk": "transition",
        "affected_variables": ["LGD", "collateral_value", "write_downs"],
        "key_sectors": ["energy_fossil", "mining", "utilities_gas", "transport_aviation"],
        "amplifiers": ["early_regulatory_phase_out", "technology_disruption", "market_value_repricing"],
        "transmission_lag_years": 3,
        "formula_note": "LGD_uplift = baseline_LGD × stranded_asset_pct × policy_intensity_factor",
    },
    "physical_damage_channel": {
        "name": "Physical Damage → Collateral Degradation Channel",
        "mechanism": "Acute and chronic physical climate hazards damage collateral (real estate, infrastructure, agricultural land), amplifying LGD and generating NatCat insurance losses",
        "primary_risk": "physical",
        "affected_variables": ["LGD", "NatCat_losses", "insurance_premium", "mortgage_LTV"],
        "key_sectors": ["real_estate_commercial", "real_estate_residential", "agriculture", "construction"],
        "amplifiers": ["sea_level_rise", "flood_zone_repricing", "wildfire_expansion", "drought_frequency"],
        "transmission_lag_years": 5,
        "formula_note": "Physical_LGD = baseline_LGD × physical_damage_pct × latitude_multiplier",
    },
    "macro_gdp_channel": {
        "name": "Policy Shock → GDP Contraction → Credit Cycle Channel",
        "mechanism": "Abrupt policy tightening contracts aggregate demand, slowing GDP growth, raising unemployment and triggering a broad credit quality deterioration across all sectors",
        "primary_risk": "transition",
        "affected_variables": ["GDP_growth", "unemployment", "PD_systemic", "NPL_ratio"],
        "key_sectors": ["all"],
        "amplifiers": ["fiscal_consolidation", "monetary_tightening", "confidence_effects"],
        "transmission_lag_years": 1,
        "formula_note": "Systemic_PD_uplift = |GDP_deviation_pct| × 0.15 + unemployment_shock_pp × 0.08",
    },
    "transition_technology_channel": {
        "name": "Green Capex → Liquidity Squeeze → PD Channel",
        "mechanism": "Mandatory transition capex (green retrofits, equipment replacement, R&D) constrains free cash flow and liquidity, particularly for SMEs and asset-heavy sectors",
        "primary_risk": "transition",
        "affected_variables": ["FCF", "liquidity_ratio", "capex_intensity", "PD"],
        "key_sectors": ["manufacturing_steel", "manufacturing_cement", "automotive", "utilities_gas"],
        "amplifiers": ["green_subsidy_availability", "technology_readiness_level", "first_mover_disadvantage"],
        "transmission_lag_years": 2,
        "formula_note": "Capex_PD_uplift = green_capex_pct_revenue × leverage_ratio × tech_readiness_discount",
    },
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SectorExposure(BaseModel):
    model_config = {"protected_namespaces": ()}
    sector: str
    exposure_bn: float = Field(..., description="Exposure in USD billions")
    baseline_pd_pct: Optional[float] = Field(None, description="Baseline PD %; uses sector default if None")
    lgd_pct: Optional[float] = Field(None, description="LGD %; uses sector default if None")


class StressTestRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    entity_name: str
    entity_type: str = Field(..., description="bank | insurer | pension_fund | asset_manager | corporate")
    jurisdiction: str = Field(..., description="EU | UK | Australia | Singapore | India | US")
    regulatory_framework: str = Field(..., description="ECB_2022 | EBA_2023 | BoE_CBES_2021 | APRA_2022 | MAS_2022 | RBI_2022")
    sectors: List[SectorExposure]
    total_exposure_bn: float
    baseline_cet1_pct: float = Field(..., ge=0, le=50)
    scenarios: List[str] = Field(default_factory=lambda: ["net_zero_2050", "delayed_transition", "current_policies"])
    time_horizons: List[int] = Field(default_factory=lambda: [2030, 2050])


class ScenarioComparisonRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    entity_name: str
    entity_type: str = "bank"
    sectors: List[SectorExposure]
    baseline_cet1_pct: float = Field(..., ge=0, le=50)
    time_horizon_year: int = 2030


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def _get_sector_profile(sector: str) -> Dict[str, Any]:
    """Return sector profile; fall back to financial_services if unknown."""
    return NACE_SECTOR_RISK_PROFILES.get(sector, NACE_SECTOR_RISK_PROFILES["financial_services"])


def calculate_pd_migration(
    sector: str,
    scenario_id: str,
    time_horizon_year: int,
) -> Dict[str, Any]:
    """
    Compute stressed PD for a sector under a given NGFS Phase IV scenario.

    Formula:
        pd_uplift = carbon_intensity × carbon_price_multiplier + physical_damage × physical_multiplier
        stressed_PD = baseline_PD × (1 + pd_uplift / 100)
    """
    profile = _get_sector_profile(sector)
    scenario = NGFS_PHASE4_SCENARIOS.get(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    baseline_pd = profile["baseline_pd_pct"]
    raw_uplift = profile["pd_uplift_by_scenario"].get(scenario_id, 0.0)

    # Time-horizon scaling: longer = more uplift for transition; shorter for hot_house
    horizon_scale = 1.0
    if time_horizon_year <= 2030:
        horizon_scale = 0.65
    elif time_horizon_year <= 2040:
        horizon_scale = 0.85
    else:
        horizon_scale = 1.0

    # Physical risk scenarios worsen with time
    if scenario["type"] == "hot_house":
        horizon_scale = min(horizon_scale + (time_horizon_year - 2030) * 0.02, 1.5)

    scaled_uplift = raw_uplift * horizon_scale
    stressed_pd = baseline_pd + scaled_uplift

    # Carbon price transmission
    carbon_price_2030 = scenario["carbon_price_usd_t"].get(2030, 60)
    carbon_intensity = profile["carbon_intensity_kg_keur"]
    carbon_channel_pd = (carbon_intensity / 5000) * (carbon_price_2030 / 150) * 0.4

    # Physical damage transmission
    physical_damage = scenario["physical_risk_damage_pct"]
    physical_channel_pd = (physical_damage / 10) * 0.3

    total_stressed_pd = max(stressed_pd + carbon_channel_pd + physical_channel_pd, 0.05)

    return {
        "sector": sector,
        "scenario_id": scenario_id,
        "time_horizon_year": time_horizon_year,
        "baseline_pd_pct": round(baseline_pd, 4),
        "pd_uplift_pct": round(scaled_uplift, 4),
        "carbon_channel_pd_pct": round(carbon_channel_pd, 4),
        "physical_channel_pd_pct": round(physical_channel_pd, 4),
        "stressed_pd_pct": round(total_stressed_pd, 4),
        "pd_migration_ratio": round(total_stressed_pd / baseline_pd, 3) if baseline_pd > 0 else 1.0,
        "carbon_intensity_kg_keur": carbon_intensity,
        "nace_code": profile["nace_code"],
    }


def calculate_lgd_uplift(
    sector: str,
    scenario_id: str,
    jurisdiction: str,
    baseline_lgd_pct: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute stressed LGD incorporating stranded-asset and physical-damage channels."""
    profile = _get_sector_profile(sector)
    scenario = NGFS_PHASE4_SCENARIOS.get(scenario_id, {})

    base_lgd = baseline_lgd_pct if baseline_lgd_pct is not None else profile["baseline_lgd_pct"]
    lgd_multiplier = profile["lgd_uplift_multiplier_by_scenario"].get(scenario_id, 1.0)

    # Physical risk geographical adjustment
    lat_band = JURISDICTION_LATITUDE_BAND.get(jurisdiction, "temperate")
    perils = PHYSICAL_RISK_MULTIPLIERS.get(lat_band, PHYSICAL_RISK_MULTIPLIERS["temperate"])
    avg_peril_multiplier = sum(perils.values()) / len(perils)
    physical_adj = (avg_peril_multiplier - 1.0) * (scenario.get("physical_risk_damage_pct", 5) / 20) * 0.5

    stressed_lgd = base_lgd * lgd_multiplier * (1 + physical_adj)
    stressed_lgd = min(stressed_lgd, 95.0)  # cap at 95%

    return {
        "sector": sector,
        "scenario_id": scenario_id,
        "jurisdiction": jurisdiction,
        "latitude_band": lat_band,
        "baseline_lgd_pct": round(base_lgd, 3),
        "lgd_multiplier": round(lgd_multiplier, 4),
        "physical_adj_factor": round(physical_adj, 4),
        "stressed_lgd_pct": round(stressed_lgd, 3),
    }


def calculate_cet1_depletion(
    expected_loss_bn: float,
    rwa_bn: float,
    baseline_cet1_pct: float,
) -> Dict[str, Any]:
    """
    Compute stressed CET1 after expected credit loss absorption.

    Formula:
        stressed_CET1% = baseline_CET1% - (EL_bn / RWA_bn × 100)
    """
    if rwa_bn <= 0:
        raise ValueError("RWA must be positive")

    el_over_rwa_pct = (expected_loss_bn / rwa_bn) * 100
    stressed_cet1 = baseline_cet1_pct - el_over_rwa_pct

    return {
        "expected_loss_bn": round(expected_loss_bn, 4),
        "rwa_bn": round(rwa_bn, 4),
        "baseline_cet1_pct": round(baseline_cet1_pct, 3),
        "el_over_rwa_pct": round(el_over_rwa_pct, 4),
        "stressed_cet1_pct": round(stressed_cet1, 3),
    }


def _run_single_scenario(
    scenario_id: str,
    sectors: List[SectorExposure],
    total_exposure_bn: float,
    baseline_cet1_pct: float,
    jurisdiction: str,
    regulatory_framework: str,
    time_horizon_year: int,
) -> Dict[str, Any]:
    """Run one scenario and return full result dict."""
    scenario = NGFS_PHASE4_SCENARIOS[scenario_id]
    framework = REGULATORY_FRAMEWORKS.get(regulatory_framework, {})
    threshold = framework.get("cet1_threshold_pct", 4.5)
    capital_metric = framework.get("capital_metric", "CET1")

    # Macro systemic uplift from GDP channel
    gdp_dev = abs(scenario["gdp_deviation_pct"].get(time_horizon_year, scenario["gdp_deviation_pct"].get(2030, 0)))
    unemp_shock = scenario["unemployment_shock_pp"].get(time_horizon_year, scenario["unemployment_shock_pp"].get(2030, 0))
    systemic_pd_uplift = gdp_dev * 0.15 + max(unemp_shock, 0) * 0.08

    sector_results = []
    total_el_bn = 0.0

    for sec_exp in sectors:
        profile = _get_sector_profile(sec_exp.sector)

        # PD migration
        pd_result = calculate_pd_migration(sec_exp.sector, scenario_id, time_horizon_year)
        stressed_pd = pd_result["stressed_pd_pct"] + systemic_pd_uplift

        # LGD uplift
        lgd_result = calculate_lgd_uplift(
            sec_exp.sector, scenario_id, jurisdiction, sec_exp.lgd_pct
        )
        stressed_lgd = lgd_result["stressed_lgd_pct"]

        # Sector risk weight adjustment
        sec_risk_weight = framework.get("sector_risk_weights", {})
        sector_category = _map_sector_to_framework_category(sec_exp.sector)
        fw_weight = sec_risk_weight.get(sector_category, 1.0)

        # Expected Loss
        el_bn = sec_exp.exposure_bn * (stressed_pd / 100) * (stressed_lgd / 100) * fw_weight
        total_el_bn += el_bn

        sector_results.append({
            "sector": sec_exp.sector,
            "exposure_bn": round(sec_exp.exposure_bn, 4),
            "baseline_pd_pct": round(pd_result["baseline_pd_pct"], 4),
            "stressed_pd_pct": round(stressed_pd, 4),
            "pd_uplift_pp": round(stressed_pd - pd_result["baseline_pd_pct"], 4),
            "baseline_lgd_pct": round(lgd_result["baseline_lgd_pct"], 4),
            "stressed_lgd_pct": round(stressed_lgd, 4),
            "lgd_uplift_pp": round(stressed_lgd - lgd_result["baseline_lgd_pct"], 4),
            "framework_sector_risk_weight": fw_weight,
            "expected_loss_bn": round(el_bn, 4),
            "stranded_asset_pct": profile["stranded_asset_pct"],
            "revenue_at_risk_pct": profile["revenue_at_risk_pct"],
        })

    # RWA approximation: total exposure × avg risk weight
    avg_risk_weight = 0.75  # approximation for mixed corporate book
    rwa_bn = total_exposure_bn * avg_risk_weight

    cet1_result = calculate_cet1_depletion(total_el_bn, rwa_bn, baseline_cet1_pct)
    stressed_cet1 = cet1_result["stressed_cet1_pct"]

    passes = stressed_cet1 >= threshold

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario["name"],
        "scenario_type": scenario["type"],
        "temperature_c": scenario["temperature_c"],
        "time_horizon_year": time_horizon_year,
        "systemic_pd_uplift_pp": round(systemic_pd_uplift, 4),
        "sector_results": sector_results,
        "total_expected_loss_bn": round(total_el_bn, 4),
        "rwa_bn": round(rwa_bn, 4),
        "el_over_rwa_pct": cet1_result["el_over_rwa_pct"],
        "baseline_cet1_pct": round(baseline_cet1_pct, 3),
        "stressed_cet1_pct": round(stressed_cet1, 3),
        "cet1_depletion_pp": round(baseline_cet1_pct - stressed_cet1, 3),
        "regulatory_threshold_pct": threshold,
        "capital_metric": capital_metric,
        "passes_regulatory_threshold": passes,
        "headroom_pp": round(stressed_cet1 - threshold, 3),
        "carbon_price_usd_t_peak": max(scenario["carbon_price_usd_t"].values()),
        "physical_risk_damage_pct": scenario["physical_risk_damage_pct"],
        "transition_loss_pct": scenario["transition_loss_pct"],
    }


def _map_sector_to_framework_category(sector: str) -> str:
    """Map NACE sector key to framework's sector risk weight category."""
    mapping = {
        "energy_fossil": "energy", "energy_renewable": "energy",
        "mining": "mining", "utilities_gas": "utilities",
        "transport_aviation": "transport", "transport_road": "transport",
        "transport_shipping": "transport",
        "manufacturing_steel": "manufacturing",
        "manufacturing_cement": "manufacturing",
        "manufacturing_chemicals": "manufacturing",
        "construction": "construction", "agriculture": "agriculture",
        "real_estate_commercial": "real_estate",
        "real_estate_residential": "real_estate",
        "financial_services": "financial",
        "technology": "technology", "healthcare": "technology",
        "food_beverage": "manufacturing", "retail_wholesale": "manufacturing",
        "automotive": "manufacturing",
    }
    return mapping.get(sector, "financial")


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def run_stress_test(request: StressTestRequest) -> Dict[str, Any]:
    """
    Run full climate stress test across requested NGFS Phase IV scenarios.
    Returns pass/fail, CET1 depletion, and submission-ready dict.
    """
    framework = REGULATORY_FRAMEWORKS.get(request.regulatory_framework)
    if framework is None:
        raise ValueError(f"Unknown regulatory framework: {request.regulatory_framework}")

    # Validate scenarios against framework
    supported = framework["scenarios_supported"]
    invalid_scenarios = [s for s in request.scenarios if s not in NGFS_PHASE4_SCENARIOS]
    if invalid_scenarios:
        raise ValueError(f"Unknown scenarios: {invalid_scenarios}")

    scenario_results = []
    worst_cet1 = float("inf")
    worst_scenario = None

    for scenario_id in request.scenarios:
        for horizon in request.time_horizons:
            result = _run_single_scenario(
                scenario_id=scenario_id,
                sectors=request.sectors,
                total_exposure_bn=request.total_exposure_bn,
                baseline_cet1_pct=request.baseline_cet1_pct,
                jurisdiction=request.jurisdiction,
                regulatory_framework=request.regulatory_framework,
                time_horizon_year=horizon,
            )
            scenario_results.append(result)
            if result["stressed_cet1_pct"] < worst_cet1:
                worst_cet1 = result["stressed_cet1_pct"]
                worst_scenario = scenario_id

    threshold = framework["cet1_threshold_pct"]
    overall_pass = all(r["passes_regulatory_threshold"] for r in scenario_results)
    failing_scenarios = [
        r["scenario_id"] for r in scenario_results if not r["passes_regulatory_threshold"]
    ]

    return {
        "run_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_name": request.entity_name,
        "entity_type": request.entity_type,
        "jurisdiction": request.jurisdiction,
        "regulatory_framework": request.regulatory_framework,
        "framework_name": framework["name"],
        "supervisor": framework["supervisor"],
        "scenarios_run": request.scenarios,
        "time_horizons": request.time_horizons,
        "baseline_cet1_pct": request.baseline_cet1_pct,
        "regulatory_cet1_threshold_pct": threshold,
        "capital_metric": framework["capital_metric"],
        "overall_pass": overall_pass,
        "worst_case_scenario": worst_scenario,
        "worst_case_cet1_pct": round(worst_cet1, 3) if worst_cet1 != float("inf") else None,
        "failing_scenarios": failing_scenarios,
        "scenario_results": scenario_results,
        "submission_ready": get_regulatory_submission_template(request.regulatory_framework),
        "transmission_channels_active": list(TRANSMISSION_CHANNELS.keys()),
    }


def run_scenario_comparison(request: ScenarioComparisonRequest) -> Dict[str, Any]:
    """Compare all NGFS Phase IV scenarios side-by-side at a single time horizon."""
    all_scenarios = list(NGFS_PHASE4_SCENARIOS.keys())
    comparison_rows = []

    for scenario_id in all_scenarios:
        result = _run_single_scenario(
            scenario_id=scenario_id,
            sectors=request.sectors,
            total_exposure_bn=sum(s.exposure_bn for s in request.sectors),
            baseline_cet1_pct=request.baseline_cet1_pct,
            jurisdiction="EU",
            regulatory_framework="EBA_2023",
            time_horizon_year=request.time_horizon_year,
        )
        comparison_rows.append({
            "scenario_id": scenario_id,
            "scenario_name": result["scenario_name"],
            "scenario_type": result["scenario_type"],
            "temperature_c": result["temperature_c"],
            "stressed_cet1_pct": result["stressed_cet1_pct"],
            "cet1_depletion_pp": result["cet1_depletion_pp"],
            "total_expected_loss_bn": result["total_expected_loss_bn"],
            "physical_risk_damage_pct": result["physical_risk_damage_pct"],
            "transition_loss_pct": result["transition_loss_pct"],
            "carbon_price_peak_usd_t": result["carbon_price_usd_t_peak"],
        })

    # Rank by CET1 depletion (worst first)
    comparison_rows.sort(key=lambda x: x["stressed_cet1_pct"])

    return {
        "run_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_name": request.entity_name,
        "entity_type": request.entity_type,
        "time_horizon_year": request.time_horizon_year,
        "baseline_cet1_pct": request.baseline_cet1_pct,
        "ngfs_phase4_scenarios_compared": len(all_scenarios),
        "comparison_table": comparison_rows,
        "worst_scenario": comparison_rows[0] if comparison_rows else None,
        "best_scenario": comparison_rows[-1] if comparison_rows else None,
        "orderly_avg_cet1_depletion": round(
            sum(r["cet1_depletion_pp"] for r in comparison_rows if "orderly" in r["scenario_type"]) /
            max(sum(1 for r in comparison_rows if "orderly" in r["scenario_type"]), 1), 3
        ),
        "disorderly_avg_cet1_depletion": round(
            sum(r["cet1_depletion_pp"] for r in comparison_rows if "disorderly" in r["scenario_type"]) /
            max(sum(1 for r in comparison_rows if "disorderly" in r["scenario_type"]), 1), 3
        ),
    }


def get_regulatory_submission_template(regulatory_framework: str) -> Dict[str, Any]:
    """Return structured disclosure template for the specified regulatory framework."""
    framework = REGULATORY_FRAMEWORKS.get(regulatory_framework)
    if framework is None:
        raise ValueError(f"Unknown regulatory framework: {regulatory_framework}")

    return {
        "framework": regulatory_framework,
        "framework_name": framework["name"],
        "supervisor": framework["supervisor"],
        "jurisdiction": framework["jurisdiction"],
        "capital_metric": framework["capital_metric"],
        "threshold_pct": framework["cet1_threshold_pct"],
        "required_fields": framework["submission_template_fields"],
        "scenarios_to_include": framework["scenarios_supported"],
        "time_horizons": framework["time_horizon_years"],
        "legal_basis": framework.get("legal_basis", ""),
        "next_exercise": framework.get("next_exercise", "TBD"),
        "mandatory": framework.get("mandatory", False),
        "template_version": "2024-Q1",
    }


def get_ngfs_phase4_scenarios() -> Dict[str, Any]:
    """Return full NGFS Phase IV scenario library."""
    return {
        "vintage": "NGFS Phase IV (2024)",
        "published_by": "Network for Greening the Financial System",
        "publication_date": "2024-Q1",
        "scenarios": NGFS_PHASE4_SCENARIOS,
        "scenario_count": len(NGFS_PHASE4_SCENARIOS),
        "temperature_range_c": {
            "min": min(s["temperature_c"] for s in NGFS_PHASE4_SCENARIOS.values()),
            "max": max(s["temperature_c"] for s in NGFS_PHASE4_SCENARIOS.values()),
        },
        "types": list({s["type"] for s in NGFS_PHASE4_SCENARIOS.values()}),
    }
