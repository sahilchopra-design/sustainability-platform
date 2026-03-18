"""
IFRS S2 Climate-Related Disclosures Engine
===========================================

IFRS S2 Climate-Related Disclosures (June 2023). Implements the four-pillar
disclosure framework: Governance, Strategy, Risk Management, and Metrics &
Targets.

Sub-modules:
  1. Full S2 Assessment — pillar-by-pillar disclosure scoring
  2. Scenario Analysis — 3-scenario (1.5C / 2C / current_policies) resilience
  3. Physical Risk Identification — acute + chronic risks by sector
  4. Transition Risk Identification — policy / technology / market / reputational
  5. SASB Industry-Based Climate Metrics — 8 sector metric sets
  6. Cross-Industry Metrics — absolute emissions, GHG intensity, CapEx, carbon price
  7. TCFD Cross-Reference — TCFD recommendation → IFRS S2 paragraph mapping
  8. Financed Emissions Disclosure — PCAF-aligned attribution

References:
  - IFRS S2 Climate-Related Disclosures (June 2023)
  - IFRS S1 General Requirements for Disclosure (June 2023)
  - PCAF Global GHG Standard (financed emissions)
  - TCFD Recommendations (2017, updated 2021)
  - SASB Standards (SICS industry classification)
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — IFRS S2 Pillars
# ---------------------------------------------------------------------------

IFRS_S2_PILLARS: dict[str, dict] = {
    "governance": {
        "description": "Governance of climate-related risks and opportunities (paragraphs 6-9)",
        "sub_requirements": {
            "board_oversight": {
                "paragraph": "S2-6",
                "description": "Board or equivalent body oversight of climate-related risks and opportunities",
                "disclosure_items": [
                    "board_processes_and_controls",
                    "how_board_informed_about_climate",
                    "board_accountability_for_climate_targets",
                    "board_expertise_or_access_to_expertise",
                ],
            },
            "mgmt_responsibilities": {
                "paragraph": "S2-7",
                "description": "Management role in governance process, controls and procedures",
                "disclosure_items": [
                    "management_role_description",
                    "reporting_line_to_board",
                    "management_processes_and_controls",
                    "management_expertise",
                ],
            },
            "incentives": {
                "paragraph": "S2-9",
                "description": "Whether and how incentives and remuneration are linked to climate",
                "disclosure_items": [
                    "incentive_programmes",
                    "remuneration_policy_climate_link",
                    "performance_targets_climate",
                ],
            },
        },
        "weight": 0.20,
    },
    "strategy": {
        "description": "Strategy for managing climate-related risks and opportunities (paragraphs 10-30)",
        "sub_requirements": {
            "climate_risks_opportunities": {
                "paragraph": "S2-10",
                "description": "Climate-related risks and opportunities over short/medium/long term",
                "disclosure_items": [
                    "risks_identified",
                    "opportunities_identified",
                    "time_horizons_defined",
                    "industry_specific_considerations",
                ],
            },
            "resilience": {
                "paragraph": "S2-22",
                "description": "Resilience of strategy and business model to climate change",
                "disclosure_items": [
                    "resilience_narrative",
                    "scenario_analysis_used",
                    "adaptations_identified",
                ],
            },
            "scenario_analysis": {
                "paragraph": "S2-22a",
                "description": "Climate scenario analysis to assess resilience",
                "disclosure_items": [
                    "scenarios_used",
                    "time_horizons_applied",
                    "inputs_and_assumptions",
                    "analytical_approach",
                    "significant_uncertainties",
                ],
            },
            "impact_on_business": {
                "paragraph": "S2-13",
                "description": "Effects of climate risks/opportunities on business model and value chain",
                "disclosure_items": [
                    "effects_on_business_model",
                    "effects_on_value_chain",
                    "geographic_concentration",
                    "adaptation_plans",
                ],
            },
            "financial_planning": {
                "paragraph": "S2-20",
                "description": "Effects of climate on financial position, performance and cash flows",
                "disclosure_items": [
                    "current_period_effects",
                    "anticipated_effects",
                    "climate_related_financial_disclosures",
                    "capex_opex_plans",
                ],
            },
        },
        "weight": 0.30,
    },
    "risk_management": {
        "description": "Processes for identifying, assessing and managing climate-related risks (paragraphs 25-30)",
        "sub_requirements": {
            "risk_identification": {
                "paragraph": "S2-25",
                "description": "Processes for identifying and assessing climate-related risks",
                "disclosure_items": [
                    "identification_process",
                    "parameters_and_assumptions",
                    "how_prioritised",
                    "data_sources_used",
                ],
            },
            "risk_assessment": {
                "paragraph": "S2-26",
                "description": "Processes for managing climate-related risks",
                "disclosure_items": [
                    "decision_making_processes",
                    "risk_mitigation_actions",
                    "risk_transfer_mechanisms",
                    "residual_risk_assessment",
                ],
            },
            "integration_overall": {
                "paragraph": "S2-27",
                "description": "Integration of climate risk management into overall risk management",
                "disclosure_items": [
                    "integration_with_enterprise_risk",
                    "climate_risk_appetite",
                    "escalation_thresholds",
                ],
            },
        },
        "weight": 0.25,
    },
    "metrics_targets": {
        "description": "Metrics and targets for managing climate-related risks and opportunities (paragraphs 29-50)",
        "sub_requirements": {
            "cross_industry_metrics": {
                "paragraph": "S2-29",
                "description": "Cross-industry climate-related metrics (absolute GHG, intensity, capex)",
                "disclosure_items": [
                    "scope1_absolute_tco2e",
                    "scope2_location_based",
                    "scope2_market_based",
                    "scope3_categories",
                    "total_ghg_tco2e",
                ],
            },
            "industry_metrics": {
                "paragraph": "S2-29b",
                "description": "Industry-based climate-related metrics (SASB SICS classification)",
                "disclosure_items": [
                    "sasb_sector_metrics",
                    "industry_specific_kpis",
                ],
            },
            "scope1_tco2e": {"paragraph": "S2-29a(i)", "description": "Gross Scope 1 GHG emissions", "disclosure_items": ["gross_scope1", "consolidation_approach"]},
            "scope2_tco2e": {"paragraph": "S2-29a(ii)", "description": "Gross Scope 2 GHG emissions (location + market)", "disclosure_items": ["location_based", "market_based", "renewable_energy_pct"]},
            "scope3_tco2e": {"paragraph": "S2-29a(iii)", "description": "Gross Scope 3 GHG emissions (all categories)", "disclosure_items": ["category_breakdown", "data_quality_score", "estimation_methods"]},
            "financed_emissions": {"paragraph": "S2-29a(iv)", "description": "Financed emissions (for financial sector)", "disclosure_items": ["pcaf_attribution", "asset_classes_covered", "data_quality_score"]},
            "internal_carbon_price": {"paragraph": "S2-34", "description": "Internal carbon price applied in decision-making", "disclosure_items": ["price_per_tco2e", "application_scope", "shadow_vs_real"]},
            "climate_capex_pct": {"paragraph": "S2-32", "description": "Proportion of CapEx aligned with climate transition", "disclosure_items": ["green_capex_pct", "capex_plan_description", "taxonomy_alignment"]},
            "targets": {"paragraph": "S2-36", "description": "Climate-related targets", "disclosure_items": ["net_zero_target_year", "scope_coverage", "interim_targets", "methodologies_used", "progress_reporting"]},
        },
        "weight": 0.25,
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Climate Scenarios (IFRS S2 paragraphs 22-24)
# ---------------------------------------------------------------------------

CLIMATE_SCENARIOS: dict[str, dict] = {
    "net_zero_1_5c": {
        "name": "Net Zero 1.5°C",
        "description": "Orderly transition consistent with limiting warming to 1.5°C above pre-industrial levels",
        "temperature_2030_c": 1.3,
        "temperature_2050_c": 1.5,
        "transition_intensity_2030": 0.85,
        "transition_intensity_2050": 1.0,
        "carbon_price_2030_usd": 130,
        "carbon_price_2050_usd": 250,
        "fossil_fuel_demand_change_2030_pct": -30,
        "fossil_fuel_demand_change_2050_pct": -75,
        "renewable_share_2030_pct": 65,
        "renewable_share_2050_pct": 95,
        "alignment": "NGFS Net Zero 2050 / IEA NZE",
        "transition_risk_level": "high",
        "physical_risk_level": "low",
    },
    "below_2c": {
        "name": "Below 2°C",
        "description": "Disorderly or delayed transition limiting warming to below 2°C",
        "temperature_2030_c": 1.5,
        "temperature_2050_c": 1.8,
        "transition_intensity_2030": 0.60,
        "transition_intensity_2050": 0.85,
        "carbon_price_2030_usd": 75,
        "carbon_price_2050_usd": 150,
        "fossil_fuel_demand_change_2030_pct": -15,
        "fossil_fuel_demand_change_2050_pct": -55,
        "renewable_share_2030_pct": 50,
        "renewable_share_2050_pct": 80,
        "alignment": "NGFS Below 2°C / IPCC SSP1-2.6",
        "transition_risk_level": "moderate",
        "physical_risk_level": "moderate",
    },
    "current_policies": {
        "name": "Current Policies",
        "description": "No additional climate policies — high physical risk pathway",
        "temperature_2030_c": 1.9,
        "temperature_2050_c": 3.2,
        "transition_intensity_2030": 0.10,
        "transition_intensity_2050": 0.15,
        "carbon_price_2030_usd": 15,
        "carbon_price_2050_usd": 25,
        "fossil_fuel_demand_change_2030_pct": 5,
        "fossil_fuel_demand_change_2050_pct": 2,
        "renewable_share_2030_pct": 30,
        "renewable_share_2050_pct": 42,
        "alignment": "NGFS Current Policies / IPCC SSP5-8.5",
        "transition_risk_level": "low",
        "physical_risk_level": "high",
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Physical Risk Types
# ---------------------------------------------------------------------------

PHYSICAL_RISK_TYPES: dict[str, dict] = {
    "acute": {
        "description": "Event-driven physical risks from weather/climate extremes",
        "risks": {
            "extreme_weather": {
                "name": "Extreme Weather Events",
                "examples": ["hurricanes", "cyclones", "typhoons", "storm surge"],
                "time_horizon": "short_to_medium",
                "sectors_most_exposed": ["real_estate", "utilities", "transport", "agriculture"],
                "financial_impact_channels": ["asset_damage", "business_interruption", "supply_chain_disruption"],
            },
            "flooding": {
                "name": "Flooding (River and Coastal)",
                "examples": ["riverine_flooding", "flash_floods", "coastal_inundation"],
                "time_horizon": "short_to_medium",
                "sectors_most_exposed": ["real_estate", "financials", "utilities", "food_beverage"],
                "financial_impact_channels": ["asset_impairment", "increased_insurance_costs", "collateral_value_decline"],
            },
            "wildfire": {
                "name": "Wildfire",
                "examples": ["forest_fires", "grassland_fires", "interface_fires"],
                "time_horizon": "short_to_medium",
                "sectors_most_exposed": ["real_estate", "utilities", "materials", "agriculture"],
                "financial_impact_channels": ["asset_destruction", "air_quality_liability", "supply_chain_disruption"],
            },
            "heatwave": {
                "name": "Heatwave and Extreme Heat",
                "examples": ["urban_heat_island", "heat_stress_on_labour", "cooling_demand_spikes"],
                "time_horizon": "short_to_medium",
                "sectors_most_exposed": ["utilities", "tech", "agriculture", "transport"],
                "financial_impact_channels": ["productivity_loss", "energy_demand_increase", "infrastructure_damage"],
            },
        },
    },
    "chronic": {
        "description": "Longer-term shifts in climate patterns",
        "risks": {
            "sea_level_rise": {
                "name": "Sea Level Rise",
                "examples": ["coastal_erosion", "saltwater_intrusion", "permanent_inundation"],
                "time_horizon": "long_term",
                "sectors_most_exposed": ["real_estate", "financials", "utilities", "transport"],
                "financial_impact_channels": ["asset_stranding", "mortgage_portfolio_risk", "infrastructure_relocation"],
            },
            "temp_shift": {
                "name": "Temperature Shift (Chronic)",
                "examples": ["mean_temperature_increase", "frost_day_reduction", "growing_season_change"],
                "time_horizon": "medium_to_long",
                "sectors_most_exposed": ["agriculture", "food_beverage", "utilities", "real_estate"],
                "financial_impact_channels": ["yield_variability", "energy_mix_changes", "health_cost_increases"],
            },
            "precipitation_change": {
                "name": "Precipitation Pattern Change",
                "examples": ["drought_frequency", "altered_rainfall_distribution", "snow_cover_reduction"],
                "time_horizon": "medium_to_long",
                "sectors_most_exposed": ["agriculture", "utilities", "materials", "food_beverage"],
                "financial_impact_channels": ["water_stress_costs", "crop_yield_reduction", "operational_disruption"],
            },
            "ecosystem_degradation": {
                "name": "Ecosystem Services Degradation",
                "examples": ["biodiversity_loss", "ocean_acidification", "permafrost_thaw"],
                "time_horizon": "long_term",
                "sectors_most_exposed": ["agriculture", "financials", "food_beverage", "materials"],
                "financial_impact_channels": ["natural_capital_loss", "regulation_tightening", "supply_chain_reliability"],
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Transition Risk Types
# ---------------------------------------------------------------------------

TRANSITION_RISK_TYPES: dict[str, dict] = {
    "policy": {
        "description": "Policy and legal risks from the transition to a low-carbon economy",
        "risks": {
            "carbon_price": {
                "name": "Carbon Pricing Mechanisms",
                "examples": ["EU ETS expansion", "carbon tax introduction", "CBAM"],
                "impact": "Increased operational costs for carbon-intensive activities",
                "sectors_most_exposed": ["energy", "materials", "utilities", "transport"],
            },
            "regulations": {
                "name": "Enhanced Regulatory Requirements",
                "examples": ["CSRD mandatory disclosure", "SFDR", "building energy codes", "fuel standards"],
                "impact": "Compliance costs, stranded assets, operational constraints",
                "sectors_most_exposed": ["financials", "real_estate", "transport", "energy"],
            },
            "stranded_assets": {
                "name": "Stranded Asset Risk",
                "examples": ["fossil_fuel_reserve_write-downs", "high-emission_facility_closures", "internal_combustion_engine_phase-out"],
                "impact": "Write-downs, impairment charges, early retirement of assets",
                "sectors_most_exposed": ["energy", "utilities", "materials", "transport"],
            },
        },
    },
    "technology": {
        "description": "Technology risks and opportunities from low-carbon innovation",
        "risks": {
            "clean_energy": {
                "name": "Clean Energy Technology Transition",
                "examples": ["solar/wind cost curve", "battery storage", "green hydrogen", "CCS"],
                "impact": "Disruption to incumbent energy business models; opportunities for early movers",
                "sectors_most_exposed": ["utilities", "energy", "transport", "materials"],
            },
            "digitisation": {
                "name": "Digitalisation and AI Energy Use",
                "examples": ["data_centre_energy_demand", "AI_chip_manufacturing_emissions", "blockchain_energy"],
                "impact": "Increased scope 2 emissions; green software pressure",
                "sectors_most_exposed": ["tech", "financials", "utilities"],
            },
        },
    },
    "market": {
        "description": "Market risks from changing investor, consumer and counterparty behaviour",
        "risks": {
            "commodity_prices": {
                "name": "Commodity Price Volatility",
                "examples": ["carbon_price_spike", "fossil_fuel_demand_contraction", "critical_mineral_shortage"],
                "impact": "Input cost increases, margin pressure, procurement risk",
                "sectors_most_exposed": ["materials", "energy", "utilities", "food_beverage"],
            },
            "consumer_preferences": {
                "name": "Changing Consumer and Counterparty Preferences",
                "examples": ["EV_adoption", "plant-based_food", "green_building_demand", "ESG_investment_mandates"],
                "impact": "Revenue decline for non-green products; green premium opportunities",
                "sectors_most_exposed": ["transport", "food_beverage", "real_estate", "financials"],
            },
        },
    },
    "reputational": {
        "description": "Reputational risks from stakeholder perception of climate inaction",
        "risks": {
            "greenwashing": {
                "name": "Greenwashing and Litigation Risk",
                "examples": ["misleading_climate_claims", "target_credibility_challenges", "climate_litigation"],
                "impact": "Regulatory penalties, reputational damage, cost of capital increase",
                "sectors_most_exposed": ["financials", "energy", "food_beverage", "materials"],
            },
            "stakeholder_sentiment": {
                "name": "Negative Stakeholder Sentiment",
                "examples": ["investor_divestment", "employee_retention", "community_opposition"],
                "impact": "Capital withdrawal, talent loss, social licence to operate",
                "sectors_most_exposed": ["energy", "utilities", "materials", "agriculture"],
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Reference Data — SASB Climate Sectors
# ---------------------------------------------------------------------------

SASB_CLIMATE_SECTORS: dict[str, dict] = {
    "financials": {
        "sasb_sector": "Financials",
        "sics_codes": ["FN-AC", "FN-CB", "FN-IB", "FN-IN", "FN-MF"],
        "climate_metrics": [
            {
                "code": "FN-CB-1",
                "name": "Financed Emissions — Absolute",
                "unit": "tCO2e",
                "description": "Absolute gross financed emissions from loans and investments (PCAF-attributed)",
            },
            {
                "code": "FN-CB-2",
                "name": "Financed Emissions Intensity",
                "unit": "tCO2e / USD mn",
                "description": "GHG intensity of loan/investment book per mn USD outstanding",
            },
            {
                "code": "FN-CB-3",
                "name": "Green Finance Ratio",
                "unit": "%",
                "description": "Proportion of lending/investment in green/sustainable activities (EU Taxonomy or equivalent)",
            },
            {
                "code": "FN-CB-4",
                "name": "Climate VaR — Credit Portfolio",
                "unit": "USD mn",
                "description": "Value-at-Risk attributable to climate transition/physical risks in credit portfolio",
            },
        ],
    },
    "energy": {
        "sasb_sector": "Extractives & Minerals Processing",
        "sics_codes": ["EM-EP", "EM-RM", "EM-CO", "EM-NR"],
        "climate_metrics": [
            {
                "code": "EM-EP-1",
                "name": "Reserves — Carbon Intensity",
                "unit": "tCO2e / boe",
                "description": "GHG emissions intensity of proved reserves",
            },
            {
                "code": "EM-EP-2",
                "name": "Methane Flaring & Venting",
                "unit": "tCO2e",
                "description": "Absolute methane and flaring emissions from upstream operations",
            },
            {
                "code": "EM-EP-3",
                "name": "Stranded Asset Exposure",
                "unit": "USD bn",
                "description": "Book value of assets at material risk of stranding under 1.5C scenario",
            },
        ],
    },
    "materials": {
        "sasb_sector": "Resource Transformation",
        "sics_codes": ["RT-CH", "RT-CP", "RT-MM", "RT-AC"],
        "climate_metrics": [
            {
                "code": "RT-CH-1",
                "name": "Process Emissions",
                "unit": "tCO2e",
                "description": "Direct process emissions from chemical/materials production (scope 1)",
            },
            {
                "code": "RT-CH-2",
                "name": "Product Carbon Footprint",
                "unit": "tCO2e / tonne product",
                "description": "Lifecycle GHG intensity of key product lines",
            },
            {
                "code": "RT-CH-3",
                "name": "Carbon Capture Rate",
                "unit": "%",
                "description": "Proportion of process emissions captured and sequestered",
            },
        ],
    },
    "utilities": {
        "sasb_sector": "Infrastructure",
        "sics_codes": ["IF-EU", "IF-GU", "IF-WU"],
        "climate_metrics": [
            {
                "code": "IF-EU-1",
                "name": "Generation Mix — Renewables",
                "unit": "%",
                "description": "Proportion of electricity generation from renewables",
            },
            {
                "code": "IF-EU-2",
                "name": "Grid Emissions Intensity",
                "unit": "tCO2e / MWh",
                "description": "GHG intensity of electricity generated and sold",
            },
            {
                "code": "IF-EU-3",
                "name": "CapEx — Low Carbon",
                "unit": "USD mn",
                "description": "Capital expenditure in low-carbon generation and infrastructure",
            },
        ],
    },
    "real_estate": {
        "sasb_sector": "Real Estate",
        "sics_codes": ["RE-RE", "RE-DV", "RE-HB"],
        "climate_metrics": [
            {
                "code": "RE-RE-1",
                "name": "Energy Intensity",
                "unit": "kWh / sq m",
                "description": "Energy consumption per sq m of managed portfolio",
            },
            {
                "code": "RE-RE-2",
                "name": "GHG Intensity — Building Portfolio",
                "unit": "kgCO2e / sq m",
                "description": "Scope 1 + 2 GHG intensity of managed building portfolio",
            },
            {
                "code": "RE-RE-3",
                "name": "CRREM Alignment Rate",
                "unit": "%",
                "description": "Proportion of portfolio aligned with CRREM decarbonisation pathway",
            },
        ],
    },
    "transport": {
        "sasb_sector": "Transportation",
        "sics_codes": ["TR-AF", "TR-MT", "TR-RA", "TR-SH"],
        "climate_metrics": [
            {
                "code": "TR-AF-1",
                "name": "Fleet Emissions Intensity",
                "unit": "gCO2 / pkm",
                "description": "GHG intensity per passenger-km (or tonne-km for freight)",
            },
            {
                "code": "TR-AF-2",
                "name": "Sustainable Fuel Blend",
                "unit": "%",
                "description": "Proportion of fuel consumption from sustainable/low-carbon sources",
            },
            {
                "code": "TR-AF-3",
                "name": "Fleet Electrification Rate",
                "unit": "%",
                "description": "Proportion of fleet that is electric or low-emission",
            },
        ],
    },
    "food_beverage": {
        "sasb_sector": "Food & Beverage",
        "sics_codes": ["FB-AG", "FB-FR", "FB-BV", "FB-MP", "FB-PF"],
        "climate_metrics": [
            {
                "code": "FB-AG-1",
                "name": "Scope 3 Upstream Agriculture Emissions",
                "unit": "tCO2e",
                "description": "Upstream GHG emissions from agricultural supply chain (scope 3 cat 1)",
            },
            {
                "code": "FB-AG-2",
                "name": "Land Use Change Emissions",
                "unit": "tCO2e",
                "description": "Emissions from direct and indirect land use change in supply chain",
            },
            {
                "code": "FB-AG-3",
                "name": "Regenerative Agriculture Adoption",
                "unit": "%",
                "description": "Proportion of sourced agricultural area using regenerative practices",
            },
            {
                "code": "FB-AG-4",
                "name": "Food Loss & Waste Intensity",
                "unit": "tCO2e / tonne product",
                "description": "GHG footprint attributable to food loss and waste",
            },
        ],
    },
    "tech": {
        "sasb_sector": "Technology & Communications",
        "sics_codes": ["TC-SC", "TC-HW", "TC-SI", "TC-TL"],
        "climate_metrics": [
            {
                "code": "TC-SC-1",
                "name": "Data Centre PUE",
                "unit": "ratio",
                "description": "Power Usage Effectiveness of data centre operations (target ≤1.3)",
            },
            {
                "code": "TC-SC-2",
                "name": "Renewable Energy Coverage",
                "unit": "%",
                "description": "Proportion of electricity consumption matched with renewable energy (RECs/PPAs)",
            },
            {
                "code": "TC-SC-3",
                "name": "E-Waste Recycling Rate",
                "unit": "%",
                "description": "Proportion of electronic waste recovered or recycled responsibly",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Reference Data — TCFD → IFRS S2 Cross-Reference
# ---------------------------------------------------------------------------

TCFD_S2_CROSSREF: dict[str, dict] = {
    "governance_board": {
        "tcfd_recommendation": "Governance — Board oversight",
        "tcfd_description": "Describe board oversight of climate-related risks and opportunities",
        "ifrs_s2_paragraph": "S2-6",
        "ifrs_s2_pillar": "governance",
        "mapping_type": "direct",
        "notes": "IFRS S2 §6 requires disclosure of board oversight processes, information, and accountability",
    },
    "governance_management": {
        "tcfd_recommendation": "Governance — Management role",
        "tcfd_description": "Describe management's role in assessing and managing climate-related risks",
        "ifrs_s2_paragraph": "S2-7",
        "ifrs_s2_pillar": "governance",
        "mapping_type": "direct",
        "notes": "IFRS S2 §7 covers management committee structure and reporting to board",
    },
    "strategy_risks_opportunities": {
        "tcfd_recommendation": "Strategy — Risks and opportunities",
        "tcfd_description": "Describe identified short-, medium-, long-term climate risks and opportunities",
        "ifrs_s2_paragraph": "S2-10 to S2-12",
        "ifrs_s2_pillar": "strategy",
        "mapping_type": "direct",
        "notes": "IFRS S2 requires explicit time-horizon definitions (entity-specific) and industry-based risks",
    },
    "strategy_impact": {
        "tcfd_recommendation": "Strategy — Impact on business",
        "tcfd_description": "Describe impact of climate risks/opportunities on business, strategy, and financial planning",
        "ifrs_s2_paragraph": "S2-13 to S2-21",
        "ifrs_s2_pillar": "strategy",
        "mapping_type": "expanded",
        "notes": "IFRS S2 expands to require effects on value chain, financial statements, and quantification where material",
    },
    "strategy_resilience": {
        "tcfd_recommendation": "Strategy — Resilience",
        "tcfd_description": "Describe resilience of strategy, considering different climate scenarios",
        "ifrs_s2_paragraph": "S2-22 to S2-24",
        "ifrs_s2_pillar": "strategy",
        "mapping_type": "expanded",
        "notes": "IFRS S2 requires scenario analysis and explicit assessment of strategic resilience under each scenario",
    },
    "risk_mgmt_identification": {
        "tcfd_recommendation": "Risk Management — Identification and assessment",
        "tcfd_description": "Describe processes for identifying and assessing climate-related risks",
        "ifrs_s2_paragraph": "S2-25",
        "ifrs_s2_pillar": "risk_management",
        "mapping_type": "direct",
        "notes": "IFRS S2 §25 closely mirrors TCFD but requires disclosure of parameters and data sources used",
    },
    "risk_mgmt_management": {
        "tcfd_recommendation": "Risk Management — Management process",
        "tcfd_description": "Describe processes for managing climate-related risks",
        "ifrs_s2_paragraph": "S2-26",
        "ifrs_s2_pillar": "risk_management",
        "mapping_type": "direct",
        "notes": "Decision criteria, risk mitigation actions, and residual risk reporting required",
    },
    "risk_mgmt_integration": {
        "tcfd_recommendation": "Risk Management — Integration",
        "tcfd_description": "Describe how processes for identifying, assessing, and managing climate-related risks are integrated into overall risk management",
        "ifrs_s2_paragraph": "S2-27",
        "ifrs_s2_pillar": "risk_management",
        "mapping_type": "direct",
        "notes": "IFRS S2 §27 requires integration with enterprise risk management framework",
    },
    "metrics_ghg": {
        "tcfd_recommendation": "Metrics & Targets — Scope 1/2/3 GHG",
        "tcfd_description": "Disclose Scope 1, 2, and if appropriate, Scope 3 GHG emissions",
        "ifrs_s2_paragraph": "S2-29a",
        "ifrs_s2_pillar": "metrics_targets",
        "mapping_type": "mandatory_expanded",
        "notes": "IFRS S2 makes Scope 1 and 2 mandatory; Scope 3 mandatory unless impracticable; requires GHG protocol methodology",
    },
    "metrics_other": {
        "tcfd_recommendation": "Metrics & Targets — Other climate metrics",
        "tcfd_description": "Describe metrics used to assess climate risks and opportunities",
        "ifrs_s2_paragraph": "S2-29b and S2-32 to S2-34",
        "ifrs_s2_pillar": "metrics_targets",
        "mapping_type": "expanded",
        "notes": "IFRS S2 adds: internal carbon price, climate CapEx ratio, financed emissions for financial entities",
    },
    "metrics_targets": {
        "tcfd_recommendation": "Metrics & Targets — Targets",
        "tcfd_description": "Describe targets used to manage climate risks and opportunities",
        "ifrs_s2_paragraph": "S2-36 to S2-41",
        "ifrs_s2_pillar": "metrics_targets",
        "mapping_type": "expanded",
        "notes": "IFRS S2 requires quantified targets, methodology references, and annual progress reporting",
    },
}


# ---------------------------------------------------------------------------
# Dataclass — IFRS S2 Assessment Output
# ---------------------------------------------------------------------------

@dataclass
class ISSBS2Assessment:
    entity_id: str
    entity_name: str
    industry_sector: str
    reporting_period: str
    assessment_date: str

    # GHG Data
    scope1_tco2e: float
    scope2_tco2e: float
    scope3_tco2e: float
    total_ghg_tco2e: float
    ghg_intensity: float  # tCO2e per USD mn revenue
    financed_emissions_tco2e: Optional[float]
    internal_carbon_price_usd: Optional[float]
    climate_capex_pct: float

    # Pillar Scores
    governance_score: float       # 0-100
    strategy_score: float         # 0-100
    risk_management_score: float  # 0-100
    metrics_targets_score: float  # 0-100
    overall_score: float          # 0-100

    # Completeness
    disclosures_complete: int
    disclosures_total: int
    completeness_pct: float

    # Risk Profile
    physical_risk_level: str    # low / moderate / high / critical
    transition_risk_level: str  # low / moderate / high / critical

    # SASB Metrics
    sasb_sector_metrics: list[dict] = field(default_factory=list)

    # Gaps
    material_gaps: list[str] = field(default_factory=list)
    priority_actions: list[str] = field(default_factory=list)

    # Metadata
    assurance_level: str = "none"
    notes: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ISSBS2Engine:
    """IFRS S2 Climate-Related Disclosures assessment engine."""

    # Disclosure item counts per pillar (derived from reference data)
    _PILLAR_DISCLOSURE_COUNTS = {
        "governance": 10,
        "strategy": 17,
        "risk_management": 10,
        "metrics_targets": 18,
    }

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        industry_sector: str = "financials",
        reporting_period: str = "2024",
        scope1_tco2e: float = 0.0,
        scope2_tco2e: float = 0.0,
        scope3_tco2e: float = 0.0,
        financed_emissions_tco2e: Optional[float] = None,
        internal_carbon_price: Optional[float] = None,
        climate_capex_pct: float = 0.0,
        revenue_usd_mn: float = 1000.0,
    ) -> ISSBS2Assessment:
        """Full IFRS S2 disclosure assessment."""
        rng = random.Random(hash(entity_id + reporting_period))

        total_ghg = scope1_tco2e + scope2_tco2e + scope3_tco2e
        ghg_intensity = (total_ghg / revenue_usd_mn) if revenue_usd_mn > 0 else 0.0

        # Score each pillar based on data completeness + quality signals
        gov_score = self._score_governance(entity_id, rng)
        strat_score = self._score_strategy(entity_id, rng, scope3_tco2e > 0)
        rm_score = self._score_risk_management(entity_id, rng)
        mt_score = self._score_metrics_targets(
            entity_id, rng, scope1_tco2e, scope2_tco2e, scope3_tco2e,
            financed_emissions_tco2e, internal_carbon_price, climate_capex_pct,
        )

        overall = (
            gov_score * IFRS_S2_PILLARS["governance"]["weight"]
            + strat_score * IFRS_S2_PILLARS["strategy"]["weight"]
            + rm_score * IFRS_S2_PILLARS["risk_management"]["weight"]
            + mt_score * IFRS_S2_PILLARS["metrics_targets"]["weight"]
        )

        # Completeness
        total_disclosures = sum(self._PILLAR_DISCLOSURE_COUNTS.values())
        complete = round(overall / 100 * total_disclosures)

        # Risk levels
        physical_level = self._classify_risk(rng.uniform(3, 8))
        transition_level = self._classify_risk(rng.uniform(2, 7))

        # SASB metrics for sector
        sasb_metrics = self._build_sasb_metrics(industry_sector, rng)

        # Gaps and actions
        gaps = self._identify_gaps(gov_score, strat_score, rm_score, mt_score,
                                   scope3_tco2e, internal_carbon_price, climate_capex_pct)
        actions = self._priority_actions(gaps)

        return ISSBS2Assessment(
            entity_id=entity_id,
            entity_name=entity_name,
            industry_sector=industry_sector,
            reporting_period=reporting_period,
            assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
            scope1_tco2e=scope1_tco2e,
            scope2_tco2e=scope2_tco2e,
            scope3_tco2e=scope3_tco2e,
            total_ghg_tco2e=round(total_ghg, 2),
            ghg_intensity=round(ghg_intensity, 4),
            financed_emissions_tco2e=financed_emissions_tco2e,
            internal_carbon_price_usd=internal_carbon_price,
            climate_capex_pct=round(climate_capex_pct, 2),
            governance_score=round(gov_score, 1),
            strategy_score=round(strat_score, 1),
            risk_management_score=round(rm_score, 1),
            metrics_targets_score=round(mt_score, 1),
            overall_score=round(overall, 1),
            disclosures_complete=complete,
            disclosures_total=total_disclosures,
            completeness_pct=round(complete / total_disclosures * 100, 1),
            physical_risk_level=physical_level,
            transition_risk_level=transition_level,
            sasb_sector_metrics=sasb_metrics,
            material_gaps=gaps,
            priority_actions=actions,
            assurance_level="limited" if overall >= 60 else "none",
            notes=f"Assessment generated for {entity_name} under IFRS S2 (June 2023). Sector: {industry_sector}.",
        )

    def _score_governance(self, entity_id: str, rng: random.Random) -> float:
        base = rng.uniform(40, 90)
        return min(100.0, base)

    def _score_strategy(self, entity_id: str, rng: random.Random, has_scope3: bool) -> float:
        base = rng.uniform(35, 85)
        if has_scope3:
            base += 5
        return min(100.0, base)

    def _score_risk_management(self, entity_id: str, rng: random.Random) -> float:
        return min(100.0, rng.uniform(45, 88))

    def _score_metrics_targets(
        self, entity_id: str, rng: random.Random,
        s1: float, s2: float, s3: float,
        financed: Optional[float], carbon_price: Optional[float], capex_pct: float,
    ) -> float:
        base = rng.uniform(30, 75)
        if s1 > 0:
            base += 5
        if s2 > 0:
            base += 5
        if s3 > 0:
            base += 8
        if financed is not None:
            base += 5
        if carbon_price is not None:
            base += 4
        if capex_pct > 20:
            base += 3
        return min(100.0, base)

    def _classify_risk(self, score: float) -> str:
        if score >= 7.5:
            return "critical"
        elif score >= 6.0:
            return "high"
        elif score >= 4.0:
            return "moderate"
        else:
            return "low"

    def _build_sasb_metrics(self, sector: str, rng: random.Random) -> list[dict]:
        if sector not in SASB_CLIMATE_SECTORS:
            sector = "financials"
        metrics = []
        for m in SASB_CLIMATE_SECTORS[sector]["climate_metrics"]:
            metrics.append({
                "code": m["code"],
                "name": m["name"],
                "unit": m["unit"],
                "description": m["description"],
                "estimated_value": round(rng.uniform(1, 1000), 2),
                "data_quality": rng.choice(["primary", "estimated", "modelled"]),
                "disclosure_status": rng.choice(["disclosed", "partially_disclosed", "not_disclosed"]),
            })
        return metrics

    def _identify_gaps(
        self, gov: float, strat: float, rm: float, mt: float,
        scope3: float, carbon_price: Optional[float], capex_pct: float,
    ) -> list[str]:
        gaps = []
        if gov < 60:
            gaps.append("Insufficient board oversight disclosure — §S2-6 requirements not met")
        if strat < 60:
            gaps.append("Scenario analysis not documented — §S2-22 resilience disclosure incomplete")
        if rm < 60:
            gaps.append("Risk management integration with enterprise risk framework not evidenced — §S2-27")
        if scope3 == 0:
            gaps.append("Scope 3 GHG emissions not disclosed — §S2-29a(iii) requires Scope 3 or impracticability statement")
        if carbon_price is None:
            gaps.append("Internal carbon price not disclosed — §S2-34 requires price or explanation of non-use")
        if capex_pct < 5:
            gaps.append("Climate-aligned CapEx ratio below 5% — §S2-32 requires disclosure of climate investment plans")
        if mt < 55:
            gaps.append("Quantified climate targets not set — §S2-36 requires absolute emission targets with baselines")
        return gaps

    def _priority_actions(self, gaps: list[str]) -> list[str]:
        actions = []
        for g in gaps[:5]:
            if "Scope 3" in g:
                actions.append("Conduct Scope 3 screening using GHG Protocol Corporate Value Chain Standard across all 15 categories")
            elif "scenario" in g.lower():
                actions.append("Commission climate scenario analysis using NGFS or IEA scenarios across 1.5C/2C/current_policies pathways")
            elif "board" in g.lower():
                actions.append("Establish board-level climate committee or assign climate accountability to existing risk committee")
            elif "carbon price" in g.lower():
                actions.append("Implement internal shadow carbon price (recommended USD 50-130/tCO2e for 2024) in investment appraisal")
            elif "CapEx" in g:
                actions.append("Develop climate CapEx classification taxonomy aligned with EU Taxonomy or sector-specific green standards")
            elif "target" in g.lower():
                actions.append("Set science-based emissions targets validated by SBTi; disclose base year, boundary, and interim milestones")
        return actions

    def run_scenario_analysis(
        self,
        entity_id: str,
        entity_type: str = "corporate",
        scenarios: Optional[list[str]] = None,
    ) -> dict:
        """Run 3-scenario climate resilience analysis per IFRS S2 §22-24."""
        rng = random.Random(hash(entity_id + entity_type))
        if scenarios is None:
            scenarios = list(CLIMATE_SCENARIOS.keys())

        results = {}
        for sc_key in scenarios:
            if sc_key not in CLIMATE_SCENARIOS:
                continue
            sc = CLIMATE_SCENARIOS[sc_key]
            revenue_impact_2030 = rng.uniform(-15, 5) * (sc["transition_intensity_2030"] + 0.2)
            revenue_impact_2050 = rng.uniform(-30, 8) * (sc["transition_intensity_2050"] + 0.2)
            capex_requirement = rng.uniform(50, 500)
            stranded_asset_pct = max(0, rng.uniform(-5, 25) * (1 - sc["transition_intensity_2030"]))
            physical_loss_2030 = rng.uniform(0, 20) * (sc["temperature_2030_c"] / 3.2)
            physical_loss_2050 = rng.uniform(0, 45) * (sc["temperature_2050_c"] / 3.2)

            results[sc_key] = {
                "scenario_name": sc["name"],
                "description": sc["description"],
                "temperature_2030_c": sc["temperature_2030_c"],
                "temperature_2050_c": sc["temperature_2050_c"],
                "carbon_price_2030_usd": sc["carbon_price_2030_usd"],
                "carbon_price_2050_usd": sc["carbon_price_2050_usd"],
                "entity_impacts": {
                    "revenue_impact_2030_pct": round(revenue_impact_2030, 2),
                    "revenue_impact_2050_pct": round(revenue_impact_2050, 2),
                    "additional_capex_required_usd_mn": round(capex_requirement, 1),
                    "stranded_asset_exposure_pct": round(stranded_asset_pct, 2),
                    "physical_loss_2030_usd_mn": round(physical_loss_2030, 1),
                    "physical_loss_2050_usd_mn": round(physical_loss_2050, 1),
                },
                "transition_risk_level": sc["transition_risk_level"],
                "physical_risk_level": sc["physical_risk_level"],
                "strategic_resilience": "adequate" if revenue_impact_2030 > -10 else "at_risk",
            }

        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "scenario_analysis_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "ifrs_s2_reference": "S2-22 to S2-24",
            "scenarios": results,
            "summary": {
                "most_severe_scenario": max(
                    results, key=lambda k: abs(results[k]["entity_impacts"]["revenue_impact_2050_pct"])
                ) if results else None,
                "key_vulnerability": "transition_risk" if entity_type in ["bank", "insurer"] else "physical_risk",
            },
        }

    def identify_risks(
        self,
        entity_id: str,
        sector: str = "financials",
        include_opportunities: bool = True,
    ) -> dict:
        """Identify physical and transition risks per IFRS S2 §10-12."""
        rng = random.Random(hash(entity_id + sector))

        physical_risks = []
        for risk_type, type_data in PHYSICAL_RISK_TYPES.items():
            for risk_key, risk_data in type_data["risks"].items():
                if sector in risk_data["sectors_most_exposed"] or rng.random() > 0.5:
                    physical_risks.append({
                        "risk_key": risk_key,
                        "risk_category": risk_type,
                        "name": risk_data["name"],
                        "time_horizon": risk_data.get("time_horizon", "medium"),
                        "sectors_exposed": risk_data["sectors_most_exposed"],
                        "financial_impact_channels": risk_data["financial_impact_channels"],
                        "materiality": rng.choice(["material", "potentially_material", "not_material"]),
                        "likelihood_score": round(rng.uniform(1, 5), 1),
                        "impact_score": round(rng.uniform(1, 5), 1),
                    })

        transition_risks = []
        for risk_type, type_data in TRANSITION_RISK_TYPES.items():
            for risk_key, risk_data in type_data["risks"].items():
                if sector in risk_data["sectors_most_exposed"] or rng.random() > 0.6:
                    transition_risks.append({
                        "risk_key": risk_key,
                        "risk_category": risk_type,
                        "name": risk_data["name"],
                        "impact": risk_data["impact"],
                        "sectors_exposed": risk_data["sectors_most_exposed"],
                        "materiality": rng.choice(["material", "potentially_material", "not_material"]),
                        "likelihood_score": round(rng.uniform(1, 5), 1),
                        "impact_score": round(rng.uniform(1, 5), 1),
                    })

        opportunities = []
        if include_opportunities:
            opp_list = [
                {"name": "Green Product Innovation", "category": "products_services", "potential_usd_mn": round(rng.uniform(5, 200), 1)},
                {"name": "Energy Efficiency CapEx Savings", "category": "resource_efficiency", "potential_usd_mn": round(rng.uniform(2, 80), 1)},
                {"name": "Green Bond / Sustainability-Linked Finance", "category": "financing", "potential_usd_mn": round(rng.uniform(50, 500), 1)},
                {"name": "Carbon Credit Revenue", "category": "carbon_markets", "potential_usd_mn": round(rng.uniform(1, 50), 1)},
            ]
            opportunities = [o for o in opp_list if rng.random() > 0.3]

        return {
            "entity_id": entity_id,
            "sector": sector,
            "identification_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "ifrs_s2_reference": "S2-10 to S2-12",
            "physical_risks": physical_risks,
            "transition_risks": transition_risks,
            "opportunities": opportunities,
            "summary": {
                "physical_risk_count": len(physical_risks),
                "transition_risk_count": len(transition_risks),
                "material_risks": sum(
                    1 for r in physical_risks + transition_risks if r["materiality"] == "material"
                ),
                "opportunity_count": len(opportunities),
            },
        }

    # -----------------------------------------------------------------------
    # Reference Endpoints
    # -----------------------------------------------------------------------

    def ref_pillars(self) -> dict:
        return {"ifrs_s2_pillars": IFRS_S2_PILLARS}

    def ref_scenarios(self) -> dict:
        return {"climate_scenarios": CLIMATE_SCENARIOS}

    def ref_physical_risks(self) -> dict:
        return {"physical_risk_types": PHYSICAL_RISK_TYPES}

    def ref_transition_risks(self) -> dict:
        return {"transition_risk_types": TRANSITION_RISK_TYPES}

    def ref_sasb_sectors(self) -> dict:
        return {"sasb_climate_sectors": SASB_CLIMATE_SECTORS}

    def ref_tcfd_crossref(self) -> dict:
        return {"tcfd_s2_crossref": TCFD_S2_CROSSREF}


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine_instance: Optional[ISSBS2Engine] = None


def get_engine() -> ISSBS2Engine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ISSBS2Engine()
    return _engine_instance
