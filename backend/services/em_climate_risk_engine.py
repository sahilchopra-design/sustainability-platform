"""
Emerging Market Climate & Transition Risk Engine — E87
=======================================================
Standards covered:
- IFC Performance Standard 6 (PS6) Biodiversity Conservation and Sustainable
  Management of Living Natural Resources (2012)
- UNFCCC NDC Registry — Nationally Determined Contributions ambition assessment
- GCF (Green Climate Fund) Programming Manual 2023
- IDA World Bank Climate Change Action Plan 2021-2025
- OECD DAC Blended Finance Principles (2018)
- PCAF GEMS (Global Emerging Market Risk Database) loss methodology
- ND-GAIN Country Index (University of Notre Dame) 2024
- BloombergNEF Emerging Market Green Finance Outlook 2024
- Climate Policy Initiative (CPI) Global Landscape of Climate Finance 2023
"""
from __future__ import annotations

import random
from typing import Any

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

EM_COUNTRY_PROFILES: dict[str, dict[str, Any]] = {
    # ── Sub-Saharan Africa ─────────────────────────────────────────────────
    "NG": {
        "name": "Nigeria", "region": "Sub-Saharan Africa",
        "physical_risk_score": 72, "transition_readiness_score": 28,
        "ndc_ambition_score": 42, "nd_gain_score": 38,
        "fossil_fuel_dependency_pct": 86, "renewable_capacity_gw": 2.1,
        "carbon_intensity_gdp": 0.42, "just_transition_risk": 78,
        "gcf_allocation_bn": 0.18, "gems_historical_loss_bn": 1.4,
        "green_bond_market_size_bn": 0.05,
    },
    "ZA": {
        "name": "South Africa", "region": "Sub-Saharan Africa",
        "physical_risk_score": 65, "transition_readiness_score": 44,
        "ndc_ambition_score": 52, "nd_gain_score": 48,
        "fossil_fuel_dependency_pct": 74, "renewable_capacity_gw": 6.8,
        "carbon_intensity_gdp": 0.81, "just_transition_risk": 82,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.9,
        "green_bond_market_size_bn": 2.1,
    },
    "KE": {
        "name": "Kenya", "region": "Sub-Saharan Africa",
        "physical_risk_score": 68, "transition_readiness_score": 58,
        "ndc_ambition_score": 66, "nd_gain_score": 45,
        "fossil_fuel_dependency_pct": 18, "renewable_capacity_gw": 3.2,
        "carbon_intensity_gdp": 0.18, "just_transition_risk": 55,
        "gcf_allocation_bn": 0.22, "gems_historical_loss_bn": 0.6,
        "green_bond_market_size_bn": 0.85,
    },
    "GH": {
        "name": "Ghana", "region": "Sub-Saharan Africa",
        "physical_risk_score": 70, "transition_readiness_score": 40,
        "ndc_ambition_score": 55, "nd_gain_score": 42,
        "fossil_fuel_dependency_pct": 62, "renewable_capacity_gw": 0.5,
        "carbon_intensity_gdp": 0.29, "just_transition_risk": 68,
        "gcf_allocation_bn": 0.12, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.25,
    },
    "ET": {
        "name": "Ethiopia", "region": "Sub-Saharan Africa",
        "physical_risk_score": 80, "transition_readiness_score": 35,
        "ndc_ambition_score": 70, "nd_gain_score": 32,
        "fossil_fuel_dependency_pct": 8, "renewable_capacity_gw": 4.5,
        "carbon_intensity_gdp": 0.12, "just_transition_risk": 62,
        "gcf_allocation_bn": 0.35, "gems_historical_loss_bn": 1.1,
        "green_bond_market_size_bn": 0.10,
    },
    "TZ": {
        "name": "Tanzania", "region": "Sub-Saharan Africa",
        "physical_risk_score": 74, "transition_readiness_score": 38,
        "ndc_ambition_score": 62, "nd_gain_score": 36,
        "fossil_fuel_dependency_pct": 25, "renewable_capacity_gw": 1.8,
        "carbon_intensity_gdp": 0.20, "just_transition_risk": 60,
        "gcf_allocation_bn": 0.18, "gems_historical_loss_bn": 0.5,
        "green_bond_market_size_bn": 0.08,
    },
    "CI": {
        "name": "Cote d'Ivoire", "region": "Sub-Saharan Africa",
        "physical_risk_score": 66, "transition_readiness_score": 42,
        "ndc_ambition_score": 58, "nd_gain_score": 40,
        "fossil_fuel_dependency_pct": 48, "renewable_capacity_gw": 0.8,
        "carbon_intensity_gdp": 0.24, "just_transition_risk": 58,
        "gcf_allocation_bn": 0.14, "gems_historical_loss_bn": 0.3,
        "green_bond_market_size_bn": 0.15,
    },
    "SN": {
        "name": "Senegal", "region": "Sub-Saharan Africa",
        "physical_risk_score": 71, "transition_readiness_score": 45,
        "ndc_ambition_score": 60, "nd_gain_score": 43,
        "fossil_fuel_dependency_pct": 55, "renewable_capacity_gw": 0.4,
        "carbon_intensity_gdp": 0.22, "just_transition_risk": 54,
        "gcf_allocation_bn": 0.09, "gems_historical_loss_bn": 0.2,
        "green_bond_market_size_bn": 0.08,
    },
    "ZM": {
        "name": "Zambia", "region": "Sub-Saharan Africa",
        "physical_risk_score": 70, "transition_readiness_score": 35,
        "ndc_ambition_score": 58, "nd_gain_score": 36,
        "fossil_fuel_dependency_pct": 12, "renewable_capacity_gw": 3.2,
        "carbon_intensity_gdp": 0.14, "just_transition_risk": 64,
        "gcf_allocation_bn": 0.14, "gems_historical_loss_bn": 0.6,
        "green_bond_market_size_bn": 0.12,
    },
    "RW": {
        "name": "Rwanda", "region": "Sub-Saharan Africa",
        "physical_risk_score": 65, "transition_readiness_score": 55,
        "ndc_ambition_score": 68, "nd_gain_score": 44,
        "fossil_fuel_dependency_pct": 5, "renewable_capacity_gw": 0.6,
        "carbon_intensity_gdp": 0.10, "just_transition_risk": 48,
        "gcf_allocation_bn": 0.10, "gems_historical_loss_bn": 0.2,
        "green_bond_market_size_bn": 0.15,
    },
    "UG": {
        "name": "Uganda", "region": "Sub-Saharan Africa",
        "physical_risk_score": 72, "transition_readiness_score": 36,
        "ndc_ambition_score": 62, "nd_gain_score": 34,
        "fossil_fuel_dependency_pct": 15, "renewable_capacity_gw": 1.2,
        "carbon_intensity_gdp": 0.12, "just_transition_risk": 62,
        "gcf_allocation_bn": 0.12, "gems_historical_loss_bn": 0.3,
        "green_bond_market_size_bn": 0.08,
    },
    "AO": {
        "name": "Angola", "region": "Sub-Saharan Africa",
        "physical_risk_score": 68, "transition_readiness_score": 28,
        "ndc_ambition_score": 44, "nd_gain_score": 32,
        "fossil_fuel_dependency_pct": 92, "renewable_capacity_gw": 2.5,
        "carbon_intensity_gdp": 0.50, "just_transition_risk": 75,
        "gcf_allocation_bn": 0.05, "gems_historical_loss_bn": 0.6,
        "green_bond_market_size_bn": 0.04,
    },
    "CM": {
        "name": "Cameroon", "region": "Sub-Saharan Africa",
        "physical_risk_score": 72, "transition_readiness_score": 34,
        "ndc_ambition_score": 58, "nd_gain_score": 36,
        "fossil_fuel_dependency_pct": 45, "renewable_capacity_gw": 1.8,
        "carbon_intensity_gdp": 0.22, "just_transition_risk": 66,
        "gcf_allocation_bn": 0.10, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.06,
    },
    "ZW": {
        "name": "Zimbabwe", "region": "Sub-Saharan Africa",
        "physical_risk_score": 74, "transition_readiness_score": 28,
        "ndc_ambition_score": 55, "nd_gain_score": 32,
        "fossil_fuel_dependency_pct": 62, "renewable_capacity_gw": 1.8,
        "carbon_intensity_gdp": 0.45, "just_transition_risk": 72,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.05,
    },
    "SD": {
        "name": "Sudan", "region": "Sub-Saharan Africa",
        "physical_risk_score": 84, "transition_readiness_score": 20,
        "ndc_ambition_score": 40, "nd_gain_score": 26,
        "fossil_fuel_dependency_pct": 58, "renewable_capacity_gw": 0.5,
        "carbon_intensity_gdp": 0.28, "just_transition_risk": 82,
        "gcf_allocation_bn": 0.06, "gems_historical_loss_bn": 1.2,
        "green_bond_market_size_bn": 0.02,
    },
    # ── Latin America & Caribbean ──────────────────────────────────────────
    "BR": {
        "name": "Brazil", "region": "Latin America",
        "physical_risk_score": 60, "transition_readiness_score": 62,
        "ndc_ambition_score": 58, "nd_gain_score": 56,
        "fossil_fuel_dependency_pct": 38, "renewable_capacity_gw": 185.0,
        "carbon_intensity_gdp": 0.22, "just_transition_risk": 45,
        "gcf_allocation_bn": 0.32, "gems_historical_loss_bn": 2.8,
        "green_bond_market_size_bn": 12.5,
    },
    "MX": {
        "name": "Mexico", "region": "Latin America",
        "physical_risk_score": 58, "transition_readiness_score": 50,
        "ndc_ambition_score": 44, "nd_gain_score": 54,
        "fossil_fuel_dependency_pct": 68, "renewable_capacity_gw": 28.4,
        "carbon_intensity_gdp": 0.35, "just_transition_risk": 52,
        "gcf_allocation_bn": 0.14, "gems_historical_loss_bn": 1.5,
        "green_bond_market_size_bn": 4.8,
    },
    "CO": {
        "name": "Colombia", "region": "Latin America",
        "physical_risk_score": 62, "transition_readiness_score": 52,
        "ndc_ambition_score": 60, "nd_gain_score": 55,
        "fossil_fuel_dependency_pct": 55, "renewable_capacity_gw": 12.2,
        "carbon_intensity_gdp": 0.28, "just_transition_risk": 50,
        "gcf_allocation_bn": 0.18, "gems_historical_loss_bn": 0.7,
        "green_bond_market_size_bn": 1.9,
    },
    "PE": {
        "name": "Peru", "region": "Latin America",
        "physical_risk_score": 66, "transition_readiness_score": 48,
        "ndc_ambition_score": 62, "nd_gain_score": 51,
        "fossil_fuel_dependency_pct": 42, "renewable_capacity_gw": 6.5,
        "carbon_intensity_gdp": 0.24, "just_transition_risk": 55,
        "gcf_allocation_bn": 0.12, "gems_historical_loss_bn": 0.5,
        "green_bond_market_size_bn": 0.8,
    },
    "CL": {
        "name": "Chile", "region": "Latin America",
        "physical_risk_score": 52, "transition_readiness_score": 68,
        "ndc_ambition_score": 65, "nd_gain_score": 65,
        "fossil_fuel_dependency_pct": 45, "renewable_capacity_gw": 14.8,
        "carbon_intensity_gdp": 0.30, "just_transition_risk": 42,
        "gcf_allocation_bn": 0.06, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 2.4,
    },
    "AR": {
        "name": "Argentina", "region": "Latin America",
        "physical_risk_score": 55, "transition_readiness_score": 45,
        "ndc_ambition_score": 46, "nd_gain_score": 57,
        "fossil_fuel_dependency_pct": 72, "renewable_capacity_gw": 8.0,
        "carbon_intensity_gdp": 0.38, "just_transition_risk": 58,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.6,
        "green_bond_market_size_bn": 0.5,
    },
    "EC": {
        "name": "Ecuador", "region": "Latin America",
        "physical_risk_score": 64, "transition_readiness_score": 44,
        "ndc_ambition_score": 58, "nd_gain_score": 50,
        "fossil_fuel_dependency_pct": 60, "renewable_capacity_gw": 5.2,
        "carbon_intensity_gdp": 0.26, "just_transition_risk": 60,
        "gcf_allocation_bn": 0.10, "gems_historical_loss_bn": 0.3,
        "green_bond_market_size_bn": 0.4,
    },
    "BO": {
        "name": "Bolivia", "region": "Latin America",
        "physical_risk_score": 66, "transition_readiness_score": 38,
        "ndc_ambition_score": 55, "nd_gain_score": 46,
        "fossil_fuel_dependency_pct": 72, "renewable_capacity_gw": 1.2,
        "carbon_intensity_gdp": 0.35, "just_transition_risk": 60,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.1,
    },
    "HN": {
        "name": "Honduras", "region": "Latin America",
        "physical_risk_score": 75, "transition_readiness_score": 42,
        "ndc_ambition_score": 60, "nd_gain_score": 44,
        "fossil_fuel_dependency_pct": 38, "renewable_capacity_gw": 1.8,
        "carbon_intensity_gdp": 0.24, "just_transition_risk": 65,
        "gcf_allocation_bn": 0.12, "gems_historical_loss_bn": 0.5,
        "green_bond_market_size_bn": 0.2,
    },
    # ── South and Southeast Asia ───────────────────────────────────────────
    "IN": {
        "name": "India", "region": "South Asia",
        "physical_risk_score": 75, "transition_readiness_score": 55,
        "ndc_ambition_score": 58, "nd_gain_score": 50,
        "fossil_fuel_dependency_pct": 58, "renewable_capacity_gw": 175.0,
        "carbon_intensity_gdp": 0.45, "just_transition_risk": 70,
        "gcf_allocation_bn": 0.45, "gems_historical_loss_bn": 4.2,
        "green_bond_market_size_bn": 18.5,
    },
    "PK": {
        "name": "Pakistan", "region": "South Asia",
        "physical_risk_score": 82, "transition_readiness_score": 32,
        "ndc_ambition_score": 50, "nd_gain_score": 35,
        "fossil_fuel_dependency_pct": 62, "renewable_capacity_gw": 3.5,
        "carbon_intensity_gdp": 0.38, "just_transition_risk": 78,
        "gcf_allocation_bn": 0.48, "gems_historical_loss_bn": 3.8,
        "green_bond_market_size_bn": 0.3,
    },
    "BD": {
        "name": "Bangladesh", "region": "South Asia",
        "physical_risk_score": 88, "transition_readiness_score": 35,
        "ndc_ambition_score": 55, "nd_gain_score": 38,
        "fossil_fuel_dependency_pct": 70, "renewable_capacity_gw": 0.8,
        "carbon_intensity_gdp": 0.32, "just_transition_risk": 80,
        "gcf_allocation_bn": 0.55, "gems_historical_loss_bn": 3.2,
        "green_bond_market_size_bn": 0.2,
    },
    "NP": {
        "name": "Nepal", "region": "South Asia",
        "physical_risk_score": 78, "transition_readiness_score": 42,
        "ndc_ambition_score": 65, "nd_gain_score": 38,
        "fossil_fuel_dependency_pct": 10, "renewable_capacity_gw": 2.2,
        "carbon_intensity_gdp": 0.08, "just_transition_risk": 58,
        "gcf_allocation_bn": 0.14, "gems_historical_loss_bn": 0.5,
        "green_bond_market_size_bn": 0.05,
    },
    "LK": {
        "name": "Sri Lanka", "region": "South Asia",
        "physical_risk_score": 68, "transition_readiness_score": 48,
        "ndc_ambition_score": 58, "nd_gain_score": 50,
        "fossil_fuel_dependency_pct": 48, "renewable_capacity_gw": 1.8,
        "carbon_intensity_gdp": 0.22, "just_transition_risk": 52,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.3,
    },
    "ID": {
        "name": "Indonesia", "region": "East Asia Pacific",
        "physical_risk_score": 70, "transition_readiness_score": 45,
        "ndc_ambition_score": 52, "nd_gain_score": 48,
        "fossil_fuel_dependency_pct": 64, "renewable_capacity_gw": 12.5,
        "carbon_intensity_gdp": 0.42, "just_transition_risk": 68,
        "gcf_allocation_bn": 0.38, "gems_historical_loss_bn": 2.5,
        "green_bond_market_size_bn": 5.2,
    },
    "PH": {
        "name": "Philippines", "region": "East Asia Pacific",
        "physical_risk_score": 85, "transition_readiness_score": 48,
        "ndc_ambition_score": 60, "nd_gain_score": 46,
        "fossil_fuel_dependency_pct": 52, "renewable_capacity_gw": 8.2,
        "carbon_intensity_gdp": 0.30, "just_transition_risk": 62,
        "gcf_allocation_bn": 0.28, "gems_historical_loss_bn": 2.8,
        "green_bond_market_size_bn": 2.1,
    },
    "VN": {
        "name": "Vietnam", "region": "East Asia Pacific",
        "physical_risk_score": 78, "transition_readiness_score": 52,
        "ndc_ambition_score": 58, "nd_gain_score": 50,
        "fossil_fuel_dependency_pct": 55, "renewable_capacity_gw": 22.5,
        "carbon_intensity_gdp": 0.48, "just_transition_risk": 65,
        "gcf_allocation_bn": 0.22, "gems_historical_loss_bn": 1.8,
        "green_bond_market_size_bn": 3.5,
    },
    "TH": {
        "name": "Thailand", "region": "East Asia Pacific",
        "physical_risk_score": 62, "transition_readiness_score": 55,
        "ndc_ambition_score": 50, "nd_gain_score": 55,
        "fossil_fuel_dependency_pct": 58, "renewable_capacity_gw": 11.0,
        "carbon_intensity_gdp": 0.36, "just_transition_risk": 50,
        "gcf_allocation_bn": 0.12, "gems_historical_loss_bn": 1.2,
        "green_bond_market_size_bn": 4.8,
    },
    "MY": {
        "name": "Malaysia", "region": "East Asia Pacific",
        "physical_risk_score": 58, "transition_readiness_score": 60,
        "ndc_ambition_score": 48, "nd_gain_score": 60,
        "fossil_fuel_dependency_pct": 62, "renewable_capacity_gw": 8.5,
        "carbon_intensity_gdp": 0.38, "just_transition_risk": 45,
        "gcf_allocation_bn": 0.05, "gems_historical_loss_bn": 0.8,
        "green_bond_market_size_bn": 6.2,
    },
    "KH": {
        "name": "Cambodia", "region": "East Asia Pacific",
        "physical_risk_score": 75, "transition_readiness_score": 38,
        "ndc_ambition_score": 55, "nd_gain_score": 40,
        "fossil_fuel_dependency_pct": 45, "renewable_capacity_gw": 1.2,
        "carbon_intensity_gdp": 0.22, "just_transition_risk": 65,
        "gcf_allocation_bn": 0.16, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.15,
    },
    "MM": {
        "name": "Myanmar", "region": "East Asia Pacific",
        "physical_risk_score": 80, "transition_readiness_score": 28,
        "ndc_ambition_score": 48, "nd_gain_score": 33,
        "fossil_fuel_dependency_pct": 40, "renewable_capacity_gw": 3.2,
        "carbon_intensity_gdp": 0.18, "just_transition_risk": 72,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.9,
        "green_bond_market_size_bn": 0.02,
    },
    "LA": {
        "name": "Lao PDR", "region": "East Asia Pacific",
        "physical_risk_score": 70, "transition_readiness_score": 40,
        "ndc_ambition_score": 55, "nd_gain_score": 42,
        "fossil_fuel_dependency_pct": 30, "renewable_capacity_gw": 7.5,
        "carbon_intensity_gdp": 0.18, "just_transition_risk": 60,
        "gcf_allocation_bn": 0.10, "gems_historical_loss_bn": 0.3,
        "green_bond_market_size_bn": 0.08,
    },
    "PG": {
        "name": "Papua New Guinea", "region": "East Asia Pacific",
        "physical_risk_score": 72, "transition_readiness_score": 35,
        "ndc_ambition_score": 60, "nd_gain_score": 38,
        "fossil_fuel_dependency_pct": 35, "renewable_capacity_gw": 1.2,
        "carbon_intensity_gdp": 0.28, "just_transition_risk": 65,
        "gcf_allocation_bn": 0.15, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.05,
    },
    "MN": {
        "name": "Mongolia", "region": "East Asia Pacific",
        "physical_risk_score": 60, "transition_readiness_score": 35,
        "ndc_ambition_score": 45, "nd_gain_score": 48,
        "fossil_fuel_dependency_pct": 88, "renewable_capacity_gw": 0.4,
        "carbon_intensity_gdp": 0.85, "just_transition_risk": 70,
        "gcf_allocation_bn": 0.06, "gems_historical_loss_bn": 0.2,
        "green_bond_market_size_bn": 0.1,
    },
    # ── MENA ──────────────────────────────────────────────────────────────
    "EG": {
        "name": "Egypt", "region": "MENA",
        "physical_risk_score": 72, "transition_readiness_score": 42,
        "ndc_ambition_score": 48, "nd_gain_score": 45,
        "fossil_fuel_dependency_pct": 92, "renewable_capacity_gw": 4.2,
        "carbon_intensity_gdp": 0.52, "just_transition_risk": 70,
        "gcf_allocation_bn": 0.15, "gems_historical_loss_bn": 1.0,
        "green_bond_market_size_bn": 1.8,
    },
    "MA": {
        "name": "Morocco", "region": "MENA",
        "physical_risk_score": 65, "transition_readiness_score": 58,
        "ndc_ambition_score": 65, "nd_gain_score": 52,
        "fossil_fuel_dependency_pct": 72, "renewable_capacity_gw": 4.0,
        "carbon_intensity_gdp": 0.35, "just_transition_risk": 55,
        "gcf_allocation_bn": 0.18, "gems_historical_loss_bn": 0.5,
        "green_bond_market_size_bn": 2.8,
    },
    "TN": {
        "name": "Tunisia", "region": "MENA",
        "physical_risk_score": 68, "transition_readiness_score": 48,
        "ndc_ambition_score": 55, "nd_gain_score": 50,
        "fossil_fuel_dependency_pct": 80, "renewable_capacity_gw": 0.6,
        "carbon_intensity_gdp": 0.40, "just_transition_risk": 60,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.3,
        "green_bond_market_size_bn": 0.6,
    },
    "JO": {
        "name": "Jordan", "region": "MENA",
        "physical_risk_score": 70, "transition_readiness_score": 52,
        "ndc_ambition_score": 58, "nd_gain_score": 53,
        "fossil_fuel_dependency_pct": 88, "renewable_capacity_gw": 1.8,
        "carbon_intensity_gdp": 0.42, "just_transition_risk": 58,
        "gcf_allocation_bn": 0.10, "gems_historical_loss_bn": 0.2,
        "green_bond_market_size_bn": 0.4,
    },
    "IQ": {
        "name": "Iraq", "region": "MENA",
        "physical_risk_score": 74, "transition_readiness_score": 22,
        "ndc_ambition_score": 35, "nd_gain_score": 38,
        "fossil_fuel_dependency_pct": 98, "renewable_capacity_gw": 0.4,
        "carbon_intensity_gdp": 0.75, "just_transition_risk": 80,
        "gcf_allocation_bn": 0.02, "gems_historical_loss_bn": 0.8,
        "green_bond_market_size_bn": 0.05,
    },
    "YE": {
        "name": "Yemen", "region": "MENA",
        "physical_risk_score": 88, "transition_readiness_score": 15,
        "ndc_ambition_score": 32, "nd_gain_score": 22,
        "fossil_fuel_dependency_pct": 82, "renewable_capacity_gw": 0.2,
        "carbon_intensity_gdp": 0.35, "just_transition_risk": 90,
        "gcf_allocation_bn": 0.12, "gems_historical_loss_bn": 1.5,
        "green_bond_market_size_bn": 0.01,
    },
    "LB": {
        "name": "Lebanon", "region": "MENA",
        "physical_risk_score": 68, "transition_readiness_score": 30,
        "ndc_ambition_score": 40, "nd_gain_score": 42,
        "fossil_fuel_dependency_pct": 95, "renewable_capacity_gw": 0.6,
        "carbon_intensity_gdp": 0.60, "just_transition_risk": 75,
        "gcf_allocation_bn": 0.04, "gems_historical_loss_bn": 0.2,
        "green_bond_market_size_bn": 0.1,
    },
    # ── ECA — Eastern Europe, Central Asia and Caucasus ───────────────────
    "TR": {
        "name": "Turkey", "region": "ECA",
        "physical_risk_score": 60, "transition_readiness_score": 48,
        "ndc_ambition_score": 42, "nd_gain_score": 55,
        "fossil_fuel_dependency_pct": 70, "renewable_capacity_gw": 32.0,
        "carbon_intensity_gdp": 0.40, "just_transition_risk": 55,
        "gcf_allocation_bn": 0.06, "gems_historical_loss_bn": 1.2,
        "green_bond_market_size_bn": 3.5,
    },
    "UA": {
        "name": "Ukraine", "region": "ECA",
        "physical_risk_score": 55, "transition_readiness_score": 42,
        "ndc_ambition_score": 45, "nd_gain_score": 52,
        "fossil_fuel_dependency_pct": 68, "renewable_capacity_gw": 8.2,
        "carbon_intensity_gdp": 0.58, "just_transition_risk": 62,
        "gcf_allocation_bn": 0.08, "gems_historical_loss_bn": 0.6,
        "green_bond_market_size_bn": 0.4,
    },
    "KZ": {
        "name": "Kazakhstan", "region": "ECA",
        "physical_risk_score": 58, "transition_readiness_score": 40,
        "ndc_ambition_score": 38, "nd_gain_score": 53,
        "fossil_fuel_dependency_pct": 85, "renewable_capacity_gw": 2.8,
        "carbon_intensity_gdp": 0.82, "just_transition_risk": 68,
        "gcf_allocation_bn": 0.04, "gems_historical_loss_bn": 0.5,
        "green_bond_market_size_bn": 0.2,
    },
    "UZ": {
        "name": "Uzbekistan", "region": "ECA",
        "physical_risk_score": 64, "transition_readiness_score": 38,
        "ndc_ambition_score": 45, "nd_gain_score": 44,
        "fossil_fuel_dependency_pct": 88, "renewable_capacity_gw": 1.5,
        "carbon_intensity_gdp": 0.70, "just_transition_risk": 72,
        "gcf_allocation_bn": 0.12, "gems_historical_loss_bn": 0.4,
        "green_bond_market_size_bn": 0.1,
    },
    "GE": {
        "name": "Georgia", "region": "ECA",
        "physical_risk_score": 56, "transition_readiness_score": 52,
        "ndc_ambition_score": 50, "nd_gain_score": 58,
        "fossil_fuel_dependency_pct": 55, "renewable_capacity_gw": 3.5,
        "carbon_intensity_gdp": 0.28, "just_transition_risk": 48,
        "gcf_allocation_bn": 0.06, "gems_historical_loss_bn": 0.2,
        "green_bond_market_size_bn": 0.3,
    },
    "RS": {
        "name": "Serbia", "region": "ECA",
        "physical_risk_score": 54, "transition_readiness_score": 46,
        "ndc_ambition_score": 42, "nd_gain_score": 56,
        "fossil_fuel_dependency_pct": 72, "renewable_capacity_gw": 3.2,
        "carbon_intensity_gdp": 0.62, "just_transition_risk": 60,
        "gcf_allocation_bn": 0.04, "gems_historical_loss_bn": 0.3,
        "green_bond_market_size_bn": 0.5,
    },
    "AZ": {
        "name": "Azerbaijan", "region": "ECA",
        "physical_risk_score": 58, "transition_readiness_score": 38,
        "ndc_ambition_score": 40, "nd_gain_score": 50,
        "fossil_fuel_dependency_pct": 90, "renewable_capacity_gw": 0.8,
        "carbon_intensity_gdp": 0.65, "just_transition_risk": 68,
        "gcf_allocation_bn": 0.03, "gems_historical_loss_bn": 0.3,
        "green_bond_market_size_bn": 0.1,
    },
    "AM": {
        "name": "Armenia", "region": "ECA",
        "physical_risk_score": 56, "transition_readiness_score": 48,
        "ndc_ambition_score": 52, "nd_gain_score": 55,
        "fossil_fuel_dependency_pct": 55, "renewable_capacity_gw": 1.4,
        "carbon_intensity_gdp": 0.32, "just_transition_risk": 52,
        "gcf_allocation_bn": 0.05, "gems_historical_loss_bn": 0.1,
        "green_bond_market_size_bn": 0.15,
    },
}

IFC_PS6_THRESHOLDS: dict[str, dict[str, Any]] = {
    "critical_habitat": {
        "tier": 1,
        "description": (
            "Habitat of significant importance to critically endangered or endangered "
            "species (IUCN Red List), endemic species with restricted range, migratory "
            "species, globally significant concentrations, or highly threatened and/or "
            "unique ecosystem types (e.g. primary tropical forest)."
        ),
        "requirements": [
            "No net loss — demonstrate measurable net conservation outcomes relative to baseline",
            "Offset ratio minimum 3:1 for critical habitat loss",
            "Independent biodiversity management plan approved before project approval",
            "Mitigation hierarchy: avoid > minimise > restore > offset",
            "Third-party verification of biodiversity offset outcome before commissioning",
            "IFC PS6 para 17: no project where residual critical habitat loss cannot be offset",
        ],
        "applicable_activities": [
            "Infrastructure (roads, dams, pipelines) through IUCN I-IV protected areas",
            "Mining and extraction in Key Biodiversity Areas",
            "Forestry in High Conservation Value forests (HCV 1-4)",
            "Coastal development affecting IUCN Marine Protected Areas",
        ],
        "trigger_indicators": [
            "Project location within 5km of IUCN Category I-II protected area",
            "Presence of IUCN CR or EN species confirmed by rapid biodiversity assessment",
            "Project modifying > 50 ha of natural habitat classified as critical",
        ],
        "offset_requirement": True,
        "net_gain_standard": "IFC PS6 para 16-17 — measurable net conservation outcomes (NNL/NPI)",
    },
    "natural_habitat": {
        "tier": 2,
        "description": (
            "Land and water areas where the biological communities are formed largely "
            "by native plant and animal species, and where human activity has not "
            "essentially modified the primary ecological functions and species composition "
            "(IFC PS6 para 11)."
        ),
        "requirements": [
            "No significant conversion or degradation of natural habitats unless no feasible alternative",
            "Any conversion must be offset with equivalent or superior biodiversity value",
            "Biodiversity management plan required (IFC PS6 para 8)",
            "Offset ratio minimum 1.5:1 for natural habitat conversion",
            "Ecosystem services assessment and compensation plan",
            "Stakeholder engagement with local communities dependent on natural habitat",
        ],
        "applicable_activities": [
            "Agricultural expansion into natural grasslands or wetlands",
            "Infrastructure development through natural savanna or scrubland",
            "Aquaculture development in coastal mangrove areas",
            "Hydropower development affecting natural riverine habitat",
        ],
        "trigger_indicators": [
            "Project converts > 10 ha natural habitat per $100M project cost",
            "Project within 10km of Ramsar wetland site",
            "Presence of IUCN VU species confirmed",
        ],
        "offset_requirement": True,
        "net_gain_standard": "IFC PS6 para 12-15 — no net loss as minimum standard",
    },
    "modified_habitat": {
        "tier": 3,
        "description": (
            "Areas that may contain biodiversity of conservation value and where the "
            "land has been heavily modified by human activities, such as agricultural "
            "land, plantations, secondary forests, and previously developed land "
            "(IFC PS6 para 11 Note 9)."
        ),
        "requirements": [
            "Good practices to maintain or enhance biodiversity during project lifecycle",
            "Pest management plan for agricultural projects (IFC PS6 Annex A)",
            "No deliberate introduction of invasive alien species",
            "Monitoring of biodiversity indicators at 3-year intervals",
            "Community liaison on biodiversity impacts (IFC PS6 para 8)",
        ],
        "applicable_activities": [
            "Projects on agricultural land, plantation forests or secondary growth",
            "Urban development on brownfield sites",
            "Infrastructure in settled landscapes",
        ],
        "trigger_indicators": [
            "Project on land that was natural habitat within last 20 years",
            "Adjacent to natural habitat with > 20% ecosystem connectivity",
        ],
        "offset_requirement": False,
        "net_gain_standard": "IFC PS6 para 11 — apply good international industry practice (GIIP)",
    },
}

CONCESSIONAL_FINANCE_WINDOWS: dict[str, dict[str, Any]] = {
    "GCF": {
        "name": "Green Climate Fund",
        "manager": "GCF Secretariat / Accredited Entities",
        "focus_areas": [
            "Climate adaptation and resilience",
            "Renewable energy and energy efficiency",
            "Sustainable land use and forests (REDD+)",
            "Sustainable transport and cities",
            "Water and food security",
        ],
        "min_project_size_m": 10.0,
        "eligibility_criteria": [
            "Project in developing country (non-Annex I UNFCCC party)",
            "Climate rationale — measurable GHG reduction or adaptation benefit",
            "Country NDA (National Designated Authority) endorsement",
            "Accredited Entity fiduciary and ESS standards compliance",
            "GCF Investment Criteria: impact, paradigm shift, sustainable development, country ownership",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 15, "max": 100},
        "typical_co_financing_ratio": "1:4 (GCF:other)",
        "readiness_grant_available": True,
    },
    "GEF": {
        "name": "Global Environment Facility",
        "manager": "GEF Secretariat / World Bank Trustee",
        "focus_areas": [
            "Biodiversity (CBD)",
            "Climate change mitigation (UNFCCC)",
            "Land degradation (UNCCD)",
            "International waters",
            "Persistent organic pollutants (Stockholm Convention)",
        ],
        "min_project_size_m": 2.0,
        "eligibility_criteria": [
            "GEF-eligible country (172 countries)",
            "Global environmental benefit — GEF Focal Area alignment",
            "Government endorsement through GEF Political Focal Point",
            "STAR (System for Transparent Allocation of Resources) allocation",
            "Incremental cost reasoning",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 50, "max": 100},
        "typical_co_financing_ratio": "1:6 (GEF:other)",
        "readiness_grant_available": False,
    },
    "AIIB": {
        "name": "Asian Infrastructure Investment Bank — Climate Finance Window",
        "manager": "AIIB (Beijing)",
        "focus_areas": [
            "Renewable energy infrastructure (solar, wind, hydro)",
            "Smart city and sustainable urban infrastructure",
            "Cross-border climate-resilient transport",
            "Water and sanitation in climate-vulnerable areas",
        ],
        "min_project_size_m": 50.0,
        "eligibility_criteria": [
            "AIIB member country (106 members, majority Asian)",
            "Infrastructure focus",
            "Environmental and Social Framework (ESF) compliance",
            "Sovereign or non-sovereign operation",
            "Climate co-benefit — minimum 50% of portfolio Paris-aligned",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 0, "max": 30},
        "typical_co_financing_ratio": "1:3 (AIIB:other)",
        "readiness_grant_available": False,
    },
    "ADB": {
        "name": "Asian Development Bank — Climate Finance",
        "manager": "ADB Manila",
        "focus_areas": [
            "Clean energy (renewable, energy efficiency)",
            "Climate-resilient agriculture and food systems",
            "Sustainable transport",
            "Urban climate resilience",
            "Blue and green economy",
        ],
        "min_project_size_m": 5.0,
        "eligibility_criteria": [
            "ADB developing member country (DMC — 46 countries)",
            "ADB Safeguard Policy Statement compliance",
            "Climate change investment threshold — minimum 30% climate finance",
            "Sovereign or non-sovereign (private sector) window",
            "ADB Strategy 2030 Operational Priority 3 alignment",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 0, "max": 100},
        "typical_co_financing_ratio": "1:4 (ADB:other)",
        "readiness_grant_available": True,
    },
    "IADB": {
        "name": "Inter-American Development Bank — Green Finance",
        "manager": "IDB Group (Washington DC)",
        "focus_areas": [
            "Energy transition (renewables, grid modernisation)",
            "Climate-resilient agriculture (LatAm)",
            "Sustainable cities and infrastructure",
            "Disaster risk reduction",
            "Biodiversity and ecosystem services",
        ],
        "min_project_size_m": 5.0,
        "eligibility_criteria": [
            "IDB borrowing member country (26 Latin American and Caribbean)",
            "Environmental and Social Policy compliance",
            "Climate co-benefit — IDB 30% climate finance target",
            "Private sector window (IDB Invest) for commercial projects",
            "Country strategy alignment",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 0, "max": 50},
        "typical_co_financing_ratio": "1:3 (IADB:other)",
        "readiness_grant_available": True,
    },
    "EIB": {
        "name": "European Investment Bank — Global Climate Finance",
        "manager": "EIB Luxembourg",
        "focus_areas": [
            "Climate mitigation (renewables, energy efficiency, EVs)",
            "Climate adaptation (flood defence, resilient agriculture)",
            "Biodiversity and natural capital",
            "Just transition financing (coal regions)",
        ],
        "min_project_size_m": 25.0,
        "eligibility_criteria": [
            "EIB-eligible country (EU-27 + 130 partner countries)",
            "EIB Environmental and Social Standards compliance",
            "Climate Bank Roadmap alignment — 50% operations climate by 2025",
            "Additionality demonstration vs commercial bank financing",
            "EU Taxonomy alignment for projects in EU territory",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 0, "max": 25},
        "typical_co_financing_ratio": "1:3 (EIB:other)",
        "readiness_grant_available": False,
    },
    "AFD": {
        "name": "Agence Francaise de Developpement — Climate Finance",
        "manager": "AFD Group (Paris)",
        "focus_areas": [
            "Renewable energy and energy access (Africa, Asia, Pacific)",
            "Sustainable forestry and REDD+",
            "Climate-resilient water and sanitation",
            "Sustainable agriculture and food systems",
            "Coastal adaptation and blue economy",
        ],
        "min_project_size_m": 3.0,
        "eligibility_criteria": [
            "AFD-eligible country (115 developing countries)",
            "AFD Climate and Biodiversity Policy compliance",
            "Paris Agreement alignment commitment",
            "French ODA objectives — poverty reduction, climate, biodiversity",
            "Gender equity dimension (AFD 3F framework)",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 10, "max": 100},
        "typical_co_financing_ratio": "1:3 (AFD:other)",
        "readiness_grant_available": True,
    },
    "WB_Climate": {
        "name": "World Bank Group — Climate Investment Program",
        "manager": "World Bank IBRD/IDA (Washington DC)",
        "focus_areas": [
            "Clean energy and energy efficiency",
            "Climate-smart agriculture and food systems",
            "Climate-resilient infrastructure",
            "Forests and land use (FCPF, BioCarbon Fund)",
            "Carbon markets and Article 6 preparedness (CIF)",
        ],
        "min_project_size_m": 5.0,
        "eligibility_criteria": [
            "World Bank member country",
            "IDA (low-income) or IBRD (middle-income) eligibility",
            "Environmental and Social Framework (ESF 2018) compliance",
            "Country Climate and Development Report (CCDR) alignment",
            "Minimum 35% climate finance share of total WBG lending",
        ],
        "blended_finance": True,
        "grant_element_pct_range": {"min": 0, "max": 100},
        "typical_co_financing_ratio": "1:5 (WBG:other)",
        "readiness_grant_available": True,
    },
}

GEMS_LOSS_MULTIPLIERS: dict[str, float] = {
    "Sub-Saharan Africa": 38.0,
    "South Asia": 45.0,
    "East Asia Pacific": 32.0,
    "Latin America": 25.0,
    "MENA": 28.0,
    "ECA": 18.0,
}

NDC_AMBITION_CATEGORIES: dict[str, dict[str, Any]] = {
    "highly_ambitious": {
        "score_range": [80, 100],
        "tier": "Highly Ambitious",
        "description": (
            "NDC is consistent with limiting warming to 1.5°C. Unconditional targets "
            "cover all major sectors with absolute emission reduction commitments "
            "calibrated to national fair share. Net-zero target by 2050 or earlier "
            "with credible 5-year review cycle and interim milestones."
        ),
        "typical_countries": ["Morocco (conditional)", "Gambia", "Costa Rica"],
        "climate_ratings_alignment": "Climate Action Tracker: 1.5°C compatible",
        "investor_implications": (
            "Minimal transition risk premium; strong regulatory tailwind; "
            "sovereign green bond eligible"
        ),
    },
    "ambitious": {
        "score_range": [60, 79],
        "tier": "Ambitious",
        "description": (
            "NDC is broadly consistent with a well-below 2°C pathway. Covers most "
            "major emission sectors with quantified targets and clear policy measures. "
            "Net-zero target by 2060 or earlier with sector roadmaps. Conditional NDC "
            "components well-defined with financing requirements specified."
        ),
        "typical_countries": ["India (conditional)", "Ethiopia", "Kenya", "Vietnam"],
        "climate_ratings_alignment": "Climate Action Tracker: Almost Sufficient",
        "investor_implications": (
            "Low-to-medium transition risk; policy credibility supports green finance; "
            "concessional eligible"
        ),
    },
    "moderate": {
        "score_range": [40, 59],
        "tier": "Moderate",
        "description": (
            "NDC represents some improvement over current policies but falls short of "
            "Paris Agreement 2°C pathway. Targets are economy-wide but with significant "
            "conditionality on international finance. Implementation gap between stated "
            "target and enacted domestic policy. Net-zero target absent or vague."
        ),
        "typical_countries": ["Brazil", "South Africa", "Mexico", "Indonesia"],
        "climate_ratings_alignment": "Climate Action Tracker: Insufficient",
        "investor_implications": (
            "Medium transition risk; policy uncertainty; blended finance needed "
            "to bridge ambition gap"
        ),
    },
    "insufficient": {
        "score_range": [0, 39],
        "tier": "Insufficient",
        "description": (
            "NDC is inconsistent with Paris Agreement objectives. No absolute emission "
            "reduction target; emissions projected to continue rising. Heavy dependence "
            "on unconditional BAU scenarios as baseline. No credible transition plan "
            "and high fossil fuel dependency. Climate litigation risk is elevated."
        ),
        "typical_countries": ["Iraq", "Yemen", "Sudan"],
        "climate_ratings_alignment": "Climate Action Tracker: Critically Insufficient",
        "investor_implications": (
            "High transition risk; sovereign climate spread widening; "
            "limited access to climate finance windows"
        ),
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng(seed: str) -> random.Random:
    return random.Random(hash(seed) & 0xFFFF_FFFF)


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _ndc_tier(score: float) -> str:
    if score >= 80:
        return "highly_ambitious"
    elif score >= 60:
        return "ambitious"
    elif score >= 40:
        return "moderate"
    return "insufficient"


# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------

class EMClimateRiskEngine:
    """
    E87 — Emerging Market Climate & Transition Risk Engine.

    Covers country-level EM climate composite scoring, IFC PS6 biodiversity
    compliance, concessional finance eligibility, green finance market depth,
    NDC alignment, and portfolio-level EM aggregation.
    """

    # ------------------------------------------------------------------
    # 1. Country Climate Risk
    # ------------------------------------------------------------------
    def assess_country_climate_risk(self, country_code: str, entity_data: dict) -> dict:
        """
        Pull EM_COUNTRY_PROFILES data, compute physical/transition composite,
        assign risk tier (high/medium/low) and return GEMS climate-adjusted loss estimate.
        """
        profile = EM_COUNTRY_PROFILES.get(country_code)
        if not profile:
            return {
                "error": f"Country code '{country_code}' not found in EM_COUNTRY_PROFILES",
                "available_count": len(EM_COUNTRY_PROFILES),
            }

        entity_id = entity_data.get("entity_id", "unknown")
        exposure_m = _safe_float(entity_data.get("exposure_m", 100))

        rng = _rng(entity_id + country_code)

        physical = _safe_float(profile["physical_risk_score"])
        transition_rev = 100 - _safe_float(profile["transition_readiness_score"])
        ndc_gap = 100 - _safe_float(profile["ndc_ambition_score"])
        fossil_dep = _safe_float(profile["fossil_fuel_dependency_pct"])

        composite = round(_clamp(
            physical * 0.35
            + transition_rev * 0.25
            + ndc_gap * 0.20
            + fossil_dep * 0.20
        ), 1)

        risk_tier = (
            "high" if composite >= 65
            else "medium" if composite >= 40
            else "low"
        )
        opportunity_tier = (
            "high" if _safe_float(profile["transition_readiness_score"]) >= 55
            else "medium" if _safe_float(profile["transition_readiness_score"]) >= 40
            else "low"
        )

        region = profile.get("region", "Sub-Saharan Africa")
        gems_uplift_pct = GEMS_LOSS_MULTIPLIERS.get(region, 25.0)
        gems_base_loss = _safe_float(profile["gems_historical_loss_bn"]) * rng.uniform(0.8, 1.2)
        gems_climate_adjusted_loss_bn = round(gems_base_loss * (1 + gems_uplift_pct / 100), 3)
        entity_loss_m = round(
            exposure_m * (gems_climate_adjusted_loss_bn / max(exposure_m * 50, 1))
            * rng.uniform(0.5, 1.5),
            3,
        )

        key_risks: list[str] = []
        if physical > 70:
            key_risks.append(
                f"High physical risk score ({physical}) — extreme weather, sea-level rise, heat stress"
            )
        if fossil_dep > 70:
            key_risks.append(
                f"High fossil fuel dependency ({fossil_dep}%) — stranded asset and just transition risk"
            )
        if _safe_float(profile["just_transition_risk"]) > 65:
            key_risks.append(
                f"Just transition risk {profile['just_transition_risk']} — "
                "large workforce in fossil-dependent sectors"
            )
        if _safe_float(profile["nd_gain_score"]) < 40:
            key_risks.append(
                f"Low ND-GAIN adaptive capacity ({profile['nd_gain_score']}) — "
                "limited institutional and financial capacity to adapt"
            )

        return {
            "country_code": country_code,
            "country_name": profile["name"],
            "region": region,
            "entity_id": entity_id,
            "em_climate_composite": composite,
            "risk_tier": risk_tier,
            "opportunity_tier": opportunity_tier,
            "physical_risk_score": physical,
            "transition_readiness_score": profile["transition_readiness_score"],
            "ndc_ambition_score": profile["ndc_ambition_score"],
            "nd_gain_score": profile["nd_gain_score"],
            "fossil_fuel_dependency_pct": fossil_dep,
            "just_transition_risk": profile["just_transition_risk"],
            "renewable_capacity_gw": profile["renewable_capacity_gw"],
            "carbon_intensity_gdp": profile["carbon_intensity_gdp"],
            "gems_uplift_pct": gems_uplift_pct,
            "gems_climate_adjusted_loss_bn": gems_climate_adjusted_loss_bn,
            "entity_expected_loss_m": entity_loss_m,
            "key_risks": key_risks,
            "gcf_allocation_bn": profile["gcf_allocation_bn"],
        }

    # ------------------------------------------------------------------
    # 2. IFC PS6 Requirements
    # ------------------------------------------------------------------
    def assess_ifc_ps6_requirements(self, entity_data: dict, country_code: str) -> dict:
        """
        Determine PS6 applicability, score compliance, identify critical
        habitat exposure and biodiversity offset requirement.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        habitat_type = entity_data.get("habitat_type", "modified_habitat").lower()
        iucn_km = _safe_float(entity_data.get("iucn_protected_area_km", 15))
        endangered_present = bool(entity_data.get("endangered_species_present", False))
        ramsar_km = _safe_float(entity_data.get("ramsar_site_km", 20))
        habitat_ha = _safe_float(entity_data.get("habitat_area_converted_ha", 0))
        has_bio_plan = bool(entity_data.get("has_biodiversity_plan", False))
        has_offset_plan = bool(entity_data.get("has_offset_plan", False))

        rng = _rng(entity_id + country_code + "ps6")

        is_critical = iucn_km < 5 or endangered_present or habitat_type == "critical_habitat"
        is_natural = (
            not is_critical
            and (
                habitat_type == "natural_habitat"
                or ramsar_km < 10
                or habitat_ha > 10
            )
        )
        applicable_tier = (
            "critical_habitat" if is_critical
            else "natural_habitat" if is_natural
            else "modified_habitat"
        )
        ps6_profile = IFC_PS6_THRESHOLDS[applicable_tier]

        criteria_scores: dict[str, bool] = {
            "biodiversity_management_plan": has_bio_plan,
            "mitigation_hierarchy_applied": rng.random() < 0.65,
            "offset_plan_in_place": has_offset_plan if ps6_profile["offset_requirement"] else True,
            "third_party_verification": rng.random() < 0.50,
            "community_engagement": rng.random() < 0.70,
            "monitoring_plan": rng.random() < 0.60,
        }
        compliance_score = round(
            sum(1 for v in criteria_scores.values() if v) / len(criteria_scores) * 100, 1
        )

        offset_ratio = 3.0 if is_critical else 1.5 if is_natural else 0.0
        offset_area_ha = max(0.0, habitat_ha * offset_ratio)
        gaps = [c for c, met in criteria_scores.items() if not met]

        return {
            "entity_id": entity_id,
            "country_code": country_code,
            "applicable_tier": applicable_tier,
            "tier_number": ps6_profile["tier"],
            "ps6_applicable": applicable_tier in ["critical_habitat", "natural_habitat"],
            "critical_habitat_exposure": is_critical,
            "natural_habitat_exposure": is_natural,
            "compliance_score": compliance_score,
            "criteria_scores": criteria_scores,
            "compliance_gaps": gaps,
            "offset_required": ps6_profile["offset_requirement"],
            "offset_ratio": offset_ratio,
            "offset_area_required_ha": round(offset_area_ha, 1),
            "net_gain_standard": ps6_profile["net_gain_standard"],
            "requirements": ps6_profile["requirements"],
            "trigger_indicators": ps6_profile.get("trigger_indicators", []),
            "standard": "IFC Performance Standard 6 — Biodiversity Conservation (2012)",
        }

    # ------------------------------------------------------------------
    # 3. Concessional Finance Eligibility
    # ------------------------------------------------------------------
    def assess_concessional_finance_eligibility(
        self, entity_data: dict, country_code: str
    ) -> dict:
        """
        Check eligibility for each of the 8 concessional finance facilities.
        Returns prioritised pipeline (top 3) and blended finance potential score.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        project_size_m = _safe_float(entity_data.get("project_size_m", 25))
        project_sector = entity_data.get("project_sector", "renewable_energy").lower()
        country_income = entity_data.get("country_income_group", "lower_middle").lower()
        govt_endorsement = bool(entity_data.get("government_endorsement", True))
        climate_rationale = bool(entity_data.get("climate_rationale", True))
        region = EM_COUNTRY_PROFILES.get(country_code, {}).get("region", "Sub-Saharan Africa")

        rng = _rng(entity_id + country_code + "concession")

        eligible: list[dict] = []
        ineligible: list[dict] = []

        for fk, facility in CONCESSIONAL_FINANCE_WINDOWS.items():
            size_ok = project_size_m >= facility["min_project_size_m"]

            if "AIIB" in fk:
                geo_ok = region in ["South Asia", "East Asia Pacific", "ECA"]
            elif "IADB" in fk:
                geo_ok = region == "Latin America"
            elif "ADB" in fk:
                geo_ok = region in ["South Asia", "East Asia Pacific", "ECA"]
            else:
                geo_ok = True

            basic_ok = size_ok and geo_ok and climate_rationale

            score = 0.0
            score += 25 if size_ok else 0
            score += 20 if geo_ok else 0
            score += 20 if climate_rationale else 0
            score += 15 if govt_endorsement else 0
            score += 20 if country_income in ["low", "lower_middle"] else 0
            score = _clamp(score + rng.uniform(-5, 5))

            grant_el = facility["grant_element_pct_range"]
            entry = {
                "facility": fk,
                "name": facility["name"],
                "manager": facility["manager"],
                "eligible": basic_ok,
                "eligibility_score": round(score, 1),
                "size_eligible": size_ok,
                "geographic_eligible": geo_ok,
                "min_project_size_m": facility["min_project_size_m"],
                "grant_element_pct_range": grant_el,
                "blended_finance": facility["blended_finance"],
                "focus_areas_match": any(
                    project_sector.replace("_", " ") in fa.lower()
                    for fa in facility["focus_areas"]
                ),
                "typical_co_financing_ratio": facility.get("typical_co_financing_ratio", "1:3"),
                "readiness_grant_available": facility.get("readiness_grant_available", False),
            }
            (eligible if basic_ok else ineligible).append(entry)

        eligible.sort(key=lambda x: x["eligibility_score"], reverse=True)
        top_3 = eligible[:3]

        if not eligible:
            blended_score = 0.0
        else:
            avg = sum(f["eligibility_score"] for f in eligible) / len(eligible)
            mult = 1.2 if country_income in ["low", "lower_middle"] else 1.0 if country_income == "upper_middle" else 0.7
            blended_score = round(_clamp(avg * mult), 1)

        return {
            "entity_id": entity_id,
            "country_code": country_code,
            "region": region,
            "project_size_m": project_size_m,
            "eligible_facility_count": len(eligible),
            "top_3_pipeline": top_3,
            "all_eligible_facilities": eligible,
            "ineligible_facilities": ineligible,
            "blended_finance_potential_score": blended_score,
            "total_facilities_assessed": len(CONCESSIONAL_FINANCE_WINDOWS),
        }

    # ------------------------------------------------------------------
    # 4. Green Finance Market
    # ------------------------------------------------------------------
    def assess_green_finance_market(self, country_code: str) -> dict:
        """
        Assess EM green bond market depth, local currency risk, sustainable
        finance depth and pipeline vs market size ratio.
        """
        profile = EM_COUNTRY_PROFILES.get(country_code)
        if not profile:
            return {
                "error": f"Country code '{country_code}' not found",
                "available_count": len(EM_COUNTRY_PROFILES),
            }

        rng = _rng(country_code + "green_finance")

        gb_size = _safe_float(profile["green_bond_market_size_bn"])
        gcf = _safe_float(profile["gcf_allocation_bn"])
        re_gw = _safe_float(profile["renewable_capacity_gw"])

        market_depth = (
            "deep" if gb_size >= 10.0
            else "developing" if gb_size >= 2.0
            else "nascent" if gb_size >= 0.5
            else "pre-market"
        )

        pipeline_mult = rng.uniform(3.0, 6.0)
        pipeline_bn = round(gb_size * pipeline_mult, 2)

        sf_depth = round(_clamp(
            min(gb_size / 0.5, 30)
            + min(gcf / 0.05, 25)
            + min(re_gw / 10, 20)
            + rng.uniform(5, 25)
        ), 1)

        local_ccy_risk = round(_clamp(
            100 - _safe_float(profile["nd_gain_score"]) + rng.uniform(-5, 5)
        ), 1)

        recommendations: list[str] = []
        if market_depth == "pre-market":
            recommendations.append(
                "Develop domestic green bond framework aligned with ICMA GBP and local currency issuance"
            )
        if gcf < 0.10:
            recommendations.append(
                "Submit GCF Funding Proposal — country may be under-served relative to climate vulnerability"
            )
        if _safe_float(profile["fossil_fuel_dependency_pct"]) > 70:
            recommendations.append(
                "Sovereign green bond issuance to finance transition CapEx and de-risk fossil fuel dependency"
            )
        if local_ccy_risk > 60:
            recommendations.append(
                "Consider FX hedging instruments or local currency guarantees (IFC, MIGA) to reduce currency risk"
            )

        return {
            "country_code": country_code,
            "country_name": profile["name"],
            "region": profile["region"],
            "green_bond_market_size_bn": gb_size,
            "market_depth": market_depth,
            "estimated_pipeline_bn": pipeline_bn,
            "pipeline_to_market_ratio": round(pipeline_mult, 1),
            "sustainable_finance_depth_score": sf_depth,
            "local_currency_risk_score": local_ccy_risk,
            "gcf_allocation_bn": gcf,
            "renewable_capacity_gw": re_gw,
            "recommendations": recommendations,
            "methodology": "BloombergNEF EM Green Finance 2024; CPI Global Landscape 2023; GCF Portfolio Dashboard",
        }

    # ------------------------------------------------------------------
    # 5. NDC Alignment
    # ------------------------------------------------------------------
    def compute_ndc_alignment(self, entity_data: dict, country_code: str) -> dict:
        """
        Assess NDC ambition score, alignment gap, required policy changes
        and just transition risk score.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        sector = entity_data.get("sector", "industrials").lower()
        entity_nz_year = entity_data.get("entity_net_zero_target_year", None)

        profile = EM_COUNTRY_PROFILES.get(country_code)
        if not profile:
            return {"error": f"Country code '{country_code}' not found"}

        ndc_score = _safe_float(profile["ndc_ambition_score"])
        tier = _ndc_tier(ndc_score)
        tier_data = NDC_AMBITION_CATEGORIES[tier]

        alignment_gap = max(0.0, 60 - ndc_score)  # gap to "ambitious" threshold
        alignment_gap_pct = round(alignment_gap / 60 * 100, 1)

        policy_changes: list[str] = []
        fossil_dep = _safe_float(profile["fossil_fuel_dependency_pct"])
        if fossil_dep > 65:
            policy_changes.append(
                "Phase-down fossil fuel subsidies (at least 50% by 2030) per IEA NZE2050 guidance"
            )
        if _safe_float(profile["renewable_capacity_gw"]) < 5:
            policy_changes.append(
                "Accelerate renewable energy auctions — target minimum 30% renewable share by 2030"
            )
        if ndc_score < 50:
            policy_changes.append(
                "Strengthen NDC with absolute emission reduction target aligned to IPCC 1.5°C national fair share"
            )
        if tier in ["insufficient", "moderate"]:
            policy_changes.append(
                "Establish domestic carbon pricing mechanism (ETS or carbon tax) to internalise transition costs"
            )
        if sector in ["coal", "utilities_fossil"] and ndc_score < 55:
            policy_changes.append(
                "Adopt coal phase-out timeline consistent with OECD 2030 / developing world 2040 pathways"
            )

        entity_aligned = False
        if entity_nz_year:
            entity_aligned = int(entity_nz_year) <= (
                2050 if tier in ["highly_ambitious", "ambitious"] else 2060
            )

        just_transition_risk = _safe_float(profile["just_transition_risk"])
        just_tier = (
            "critical" if just_transition_risk >= 75
            else "high" if just_transition_risk >= 55
            else "medium" if just_transition_risk >= 35
            else "low"
        )

        return {
            "entity_id": entity_id,
            "country_code": country_code,
            "country_name": profile["name"],
            "ndc_ambition_score": ndc_score,
            "ndc_tier": tier,
            "tier_description": tier_data["description"][:160] + "...",
            "climate_ratings_alignment": tier_data["climate_ratings_alignment"],
            "alignment_gap_to_ambitious": round(alignment_gap, 1),
            "alignment_gap_pct": alignment_gap_pct,
            "required_policy_changes": policy_changes,
            "entity_net_zero_target": entity_nz_year,
            "entity_ndc_aligned": entity_aligned,
            "just_transition_risk_score": just_transition_risk,
            "just_transition_tier": just_tier,
            "fossil_fuel_dependency_pct": fossil_dep,
            "renewable_capacity_gw": profile["renewable_capacity_gw"],
            "investor_implications": tier_data["investor_implications"],
        }

    # ------------------------------------------------------------------
    # 6. Full Assessment
    # ------------------------------------------------------------------
    def run_full_assessment(self, entity_data: dict) -> dict:
        """
        Orchestrate all sub-assessments for a single EM country exposure.

        Returns consolidated scores: em_climate_composite (0-100), risk_tier,
        opportunity_tier, physical_risk_score, transition_readiness_score,
        ndc_ambition_score, ifc_ps6_score, blended_finance_potential,
        gcf_allocation_bn, gems_climate_uplift_pct.
        """
        entity_id = entity_data.get("entity_id", "unknown")
        country_code = entity_data.get("country_code", "IN")

        profile = EM_COUNTRY_PROFILES.get(country_code)
        if not profile:
            return {
                "error": f"Country code '{country_code}' not found in EM_COUNTRY_PROFILES",
                "supported_count": len(EM_COUNTRY_PROFILES),
            }

        country_risk = self.assess_country_climate_risk(country_code, entity_data)
        ps6 = self.assess_ifc_ps6_requirements(entity_data, country_code)
        concession = self.assess_concessional_finance_eligibility(entity_data, country_code)
        green_market = self.assess_green_finance_market(country_code)
        ndc = self.compute_ndc_alignment(entity_data, country_code)

        region = profile["region"]
        gems_uplift_pct = GEMS_LOSS_MULTIPLIERS.get(region, 25.0)

        return {
            "entity_id": entity_id,
            "country_code": country_code,
            "country_name": profile["name"],
            "region": region,
            # Top-level scores
            "em_climate_composite": country_risk["em_climate_composite"],
            "risk_tier": country_risk["risk_tier"],
            "opportunity_tier": country_risk["opportunity_tier"],
            "physical_risk_score": country_risk["physical_risk_score"],
            "transition_readiness_score": profile["transition_readiness_score"],
            "ndc_ambition_score": profile["ndc_ambition_score"],
            "ifc_ps6_score": ps6["compliance_score"],
            "ifc_ps6_tier": ps6["applicable_tier"],
            "blended_finance_potential": concession["blended_finance_potential_score"],
            "eligible_finance_facilities": concession["eligible_facility_count"],
            "gcf_allocation_bn": profile["gcf_allocation_bn"],
            "gems_climate_uplift_pct": gems_uplift_pct,
            "green_bond_market_size_bn": profile["green_bond_market_size_bn"],
            "green_market_depth": green_market["market_depth"],
            "ndc_tier": ndc["ndc_tier"],
            "just_transition_risk": profile["just_transition_risk"],
            "fossil_fuel_dependency_pct": profile["fossil_fuel_dependency_pct"],
            # Sub-assessment detail
            "country_risk_detail": country_risk,
            "ifc_ps6_detail": ps6,
            "concessional_finance_detail": concession,
            "green_finance_market_detail": green_market,
            "ndc_alignment_detail": ndc,
            "assessment_standards": [
                "IFC Performance Standard 6 — Biodiversity Conservation (2012)",
                "UNFCCC NDC Registry — Paris Agreement Article 4",
                "GCF Programming Manual 2023",
                "OECD DAC Blended Finance Principles (2018)",
                "PCAF GEMS loss methodology",
                "ND-GAIN Country Index (University of Notre Dame 2024)",
                "Climate Policy Initiative — Global Landscape of Climate Finance 2023",
            ],
        }

    # ------------------------------------------------------------------
    # Portfolio-level EM assessment
    # ------------------------------------------------------------------
    def run_portfolio_assessment(self, portfolio_data: dict) -> dict:
        """
        Portfolio-level EM assessment aggregating multiple country exposures.

        Expected input:
            entity_id: str
            exposures: list[{country_code, exposure_m, sector?, ...}]
        """
        entity_id = portfolio_data.get("entity_id", "unknown")
        exposures = portfolio_data.get("exposures", [])

        if not exposures:
            return {"error": "No country exposures provided", "entity_id": entity_id}

        total_exposure_m = sum(_safe_float(e.get("exposure_m", 0)) for e in exposures)
        country_results: list[dict] = []
        w_composite = w_physical = w_transition = w_ndc = 0.0
        total_expected_loss_m = 0.0

        for exp in exposures:
            cc = exp.get("country_code", "IN")
            exp_m = _safe_float(exp.get("exposure_m", 0))
            weight = exp_m / max(total_exposure_m, 1)

            result = self.assess_country_climate_risk(cc, {**exp, "entity_id": entity_id})
            if "error" in result:
                continue

            w_composite += result["em_climate_composite"] * weight
            w_physical += result["physical_risk_score"] * weight
            w_transition += result["transition_readiness_score"] * weight
            w_ndc += result["ndc_ambition_score"] * weight
            total_expected_loss_m += result.get("entity_expected_loss_m", 0)

            country_results.append({
                "country_code": cc,
                "country_name": result["country_name"],
                "region": result["region"],
                "exposure_m": exp_m,
                "weight_pct": round(weight * 100, 2),
                "em_climate_composite": result["em_climate_composite"],
                "risk_tier": result["risk_tier"],
                "physical_risk_score": result["physical_risk_score"],
                "transition_readiness_score": result["transition_readiness_score"],
                "ndc_tier": _ndc_tier(result["ndc_ambition_score"]),
                "gems_climate_uplift_pct": result["gems_uplift_pct"],
                "entity_expected_loss_m": result.get("entity_expected_loss_m", 0),
            })

        country_results.sort(key=lambda x: x["em_climate_composite"], reverse=True)
        highest_risk = country_results[0] if country_results else {}
        most_concentrated = max(country_results, key=lambda x: x["weight_pct"]) if country_results else {}

        portfolio_risk_tier = (
            "high" if w_composite >= 65
            else "medium" if w_composite >= 40
            else "low"
        )

        return {
            "entity_id": entity_id,
            "portfolio_em_composite": round(w_composite, 1),
            "portfolio_risk_tier": portfolio_risk_tier,
            "portfolio_physical_risk": round(w_physical, 1),
            "portfolio_transition_readiness": round(w_transition, 1),
            "portfolio_ndc_ambition": round(w_ndc, 1),
            "total_exposure_m": round(total_exposure_m, 2),
            "total_expected_loss_m": round(total_expected_loss_m, 3),
            "country_count": len(country_results),
            "country_breakdown": country_results,
            "highest_risk_country": highest_risk.get("country_name", "N/A"),
            "most_concentrated_country": most_concentrated.get("country_name", "N/A"),
        }
