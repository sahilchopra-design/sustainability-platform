"""
Financed Emissions Temperature Alignment Engine (E103)
======================================================
PCAF + SBTi Financial Institutions Net-Zero Standard v1.0 + PACTA — portfolio implied temperature rise (ITR).

Sub-modules:
  1. Temperature Alignment Assessment  — portfolio WACI, ITR, SBTi criteria, PACTA alignment
  2. WACI Calculation                  — exposure-weighted average carbon intensity
  3. ITR Interpolation                 — WACI to implied temperature via MSCI/Carbon Delta table
  4. SBTi FI Criteria Assessment       — 6-criteria SBTi FI Net-Zero Standard scoring
  5. Sector PACTA Alignment            — single sector % aligned vs IEA NZE trajectory
  6. PCAF DQS Scoring                  — exposure-weighted data quality score
  7. Reference Data                    — SBTi criteria, sector pathways, asset class methods

References:
  - SBTi Financial Institutions Net-Zero Standard v1.0 (September 2022)
  - PCAF Global GHG Accounting & Reporting Standard Part A (2022)
  - PACTA for Banks Methodology (2022 Climate Alignment)
  - IEA Net Zero Emissions by 2050 Scenario (NZE 2050, 2023)
  - IEA Current Policies Scenario (CPS, 2023)
  - MSCI Carbon Delta / Carbon Portfolio Analytics methodology (2021)
  - IPCC AR6 WG3 Chapter 3 — mitigation pathways
  - EU Paris-Aligned Benchmark Regulation (EU) 2020/1818
"""
from __future__ import annotations

import bisect
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Reference Data — SBTi FI Net-Zero Standard v1.0 Criteria
# ---------------------------------------------------------------------------

SBTI_FI_CRITERIA: Dict[str, Dict] = {
    "NZ-1": {
        "label": "Long-term Net-Zero S1+S2 Absolute Contraction",
        "description": "Reduce absolute Scope 1+2 financed emissions by >= 90% from base year to net-zero target year (no later than 2050).",
        "scope": "S1+S2",
        "method": "Absolute Contraction Approach (ACA)",
        "required_reduction_pct": 90.0,
        "target_year_max": 2050,
        "weight": 0.20,
        "sbti_guidance": "SBTi FI Net-Zero Standard v1.0, Section 4.2 NZ-1",
        "verification_method": "Third-party SBTi validation",
    },
    "NZ-2": {
        "label": "Long-term Net-Zero S3 Absolute Contraction",
        "description": "Reduce absolute Scope 3 financed emissions by >= 90% from base year to net-zero target year.",
        "scope": "S3",
        "method": "Absolute Contraction Approach (ACA)",
        "required_reduction_pct": 90.0,
        "target_year_max": 2050,
        "weight": 0.15,
        "sbti_guidance": "SBTi FI Net-Zero Standard v1.0, Section 4.2 NZ-2",
        "verification_method": "Third-party SBTi validation",
    },
    "NT-1": {
        "label": "Near-term S1+S2 Reduction Target",
        "description": "Reduce absolute Scope 1+2 financed emissions by >= 42% by 2030 from 2020 base year (1.5C-aligned).",
        "scope": "S1+S2",
        "method": "Absolute Contraction Approach (ACA)",
        "required_reduction_pct": 42.0,
        "base_year": 2020,
        "target_year": 2030,
        "weight": 0.25,
        "sbti_guidance": "SBTi FI Net-Zero Standard v1.0, Section 4.1 NT-1",
        "verification_method": "Third-party SBTi validation",
    },
    "NT-2": {
        "label": "Near-term S3 Engagement Target",
        "description": "Engage portfolio companies representing >= 25% of Scope 3 financed emissions to set SBTi-validated targets by 2030.",
        "scope": "S3",
        "method": "Engagement / SBTi-validated targets",
        "required_coverage_pct": 25.0,
        "base_year": 2020,
        "target_year": 2030,
        "weight": 0.15,
        "sbti_guidance": "SBTi FI Net-Zero Standard v1.0, Section 4.1 NT-2",
        "verification_method": "Portfolio company SBTi target validation",
    },
    "FLAG-1": {
        "label": "Land Sector and Removals Target",
        "description": "Set FLAG (Forests, Land and Agriculture) sector-specific targets aligned with the FLAG Science-Based Target-Setting Guidance.",
        "scope": "FLAG sectors",
        "method": "FLAG Guidance v1.0",
        "applies_if_flag_exposure_pct": 5.0,
        "weight": 0.10,
        "sbti_guidance": "SBTi FLAG Guidance v1.0 (September 2022)",
        "verification_method": "SBTi FLAG validation",
    },
    "FI-1": {
        "label": "Portfolio Alignment Requirement",
        "description": "At least 50% of portfolio companies by financed emissions must have SBTi-validated near-term targets by 2030 or intermediate milestones.",
        "scope": "All eligible asset classes",
        "method": "Portfolio company SBTi coverage",
        "required_coverage_pct": 50.0,
        "milestone_year": 2030,
        "weight": 0.15,
        "sbti_guidance": "SBTi FI Net-Zero Standard v1.0, Section 5 FI-1",
        "verification_method": "SBTi target registry verification",
    },
}


# ---------------------------------------------------------------------------
# Reference Data — PACTA Sector Transition Technology Pathways
# IEA NZE 2050 benchmark trajectories vs IEA Current Policies Scenario
# ---------------------------------------------------------------------------

PACTA_SECTOR_PATHWAYS: Dict[str, Dict] = {
    "power": {
        "label": "Power Generation",
        "nace_codes": ["D35.1", "D35.11", "D35.12"],
        "metric": "Capacity (GW renewable share %)",
        "metric_unit": "% renewable of total installed capacity",
        "nze_trajectory": {2025: 55.0, 2030: 74.0, 2035: 86.0, 2040: 94.0, 2050: 99.0},
        "cps_trajectory": {2025: 35.0, 2030: 42.0, 2035: 50.0, 2040: 58.0, 2050: 68.0},
        "paris_aligned_threshold_2030": 70.0,
        "current_global_level": 31.0,
        "unit_description": "Percent of total electricity generation from renewables",
    },
    "automotive": {
        "label": "Automotive / Light-duty Vehicles",
        "nace_codes": ["C29.1", "C29.10", "G45.11"],
        "metric": "EV share of new vehicle sales (%)",
        "metric_unit": "% EV of annual new car sales",
        "nze_trajectory": {2025: 40.0, 2030: 60.0, 2035: 85.0, 2040: 95.0, 2050: 100.0},
        "cps_trajectory": {2025: 20.0, 2030: 30.0, 2035: 40.0, 2040: 55.0, 2050: 70.0},
        "paris_aligned_threshold_2030": 55.0,
        "current_global_level": 18.0,
        "unit_description": "Percent of new passenger car sales that are battery electric or fuel cell",
    },
    "steel": {
        "label": "Steel Production",
        "nace_codes": ["C24.1", "C24.10"],
        "metric": "CO2 intensity (tCO2/t steel)",
        "metric_unit": "tCO2 per tonne of crude steel",
        "nze_trajectory": {2025: 1.60, 2030: 1.30, 2035: 0.90, 2040: 0.50, 2050: 0.05},
        "cps_trajectory": {2025: 1.90, 2030: 1.85, 2035: 1.80, 2040: 1.75, 2050: 1.60},
        "paris_aligned_threshold_2030": 1.40,
        "current_global_level": 1.89,
        "unit_description": "Tonnes CO2 per tonne of crude steel produced",
        "lower_is_better": True,
    },
    "cement": {
        "label": "Cement Production",
        "nace_codes": ["C23.5", "C23.51"],
        "metric": "CO2 intensity (kgCO2/t clinker)",
        "metric_unit": "kgCO2 per tonne of clinker",
        "nze_trajectory": {2025: 770, 2030: 710, 2035: 610, 2040: 480, 2050: 190},
        "cps_trajectory": {2025: 840, 2030: 830, 2035: 820, 2040: 810, 2050: 790},
        "paris_aligned_threshold_2030": 730,
        "current_global_level": 853,
        "unit_description": "kg CO2 per tonne of clinker produced",
        "lower_is_better": True,
    },
    "oil_and_gas": {
        "label": "Oil and Gas Extraction",
        "nace_codes": ["B06.1", "B06.2", "B06.10", "B06.20"],
        "metric": "Production volume (Mboe/d)",
        "metric_unit": "Million barrels of oil equivalent per day",
        "nze_trajectory": {2025: 96.0, 2030: 77.0, 2035: 60.0, 2040: 44.0, 2050: 24.0},
        "cps_trajectory": {2025: 102.0, 2030: 108.0, 2035: 112.0, 2040: 115.0, 2050: 118.0},
        "paris_aligned_threshold_2030": 82.0,
        "current_global_level": 100.0,
        "unit_description": "Global oil and gas production in million boe/d",
        "lower_is_better": True,
    },
    "aviation": {
        "label": "Aviation",
        "nace_codes": ["H51.1", "H51.10"],
        "metric": "CO2 intensity (gCO2/RPK)",
        "metric_unit": "grams CO2 per revenue passenger kilometre",
        "nze_trajectory": {2025: 88, 2030: 75, 2035: 55, 2040: 35, 2050: 7},
        "cps_trajectory": {2025: 97, 2030: 92, 2035: 88, 2040: 85, 2050: 80},
        "paris_aligned_threshold_2030": 80,
        "current_global_level": 95,
        "unit_description": "gCO2 per revenue passenger kilometre",
        "lower_is_better": True,
    },
    "shipping": {
        "label": "Shipping / Maritime Transport",
        "nace_codes": ["H50.1", "H50.2", "H50.10", "H50.20"],
        "metric": "CO2 intensity (gCO2/tonne-mile)",
        "metric_unit": "grams CO2 per tonne-nautical mile",
        "nze_trajectory": {2025: 10.5, 2030: 8.5, 2035: 5.5, 2040: 2.5, 2050: 0.3},
        "cps_trajectory": {2025: 12.0, 2030: 11.5, 2035: 11.0, 2040: 10.5, 2050: 10.0},
        "paris_aligned_threshold_2030": 9.0,
        "current_global_level": 11.9,
        "unit_description": "gCO2 per tonne-nautical mile",
        "lower_is_better": True,
    },
    "real_estate": {
        "label": "Commercial Real Estate",
        "nace_codes": ["L68.1", "L68.2", "L68.20", "L68.31", "L68.32"],
        "metric": "Energy intensity (kWh/m2/yr)",
        "metric_unit": "kWh per square metre per year",
        "nze_trajectory": {2025: 155, 2030: 120, 2035: 85, 2040: 55, 2050: 20},
        "cps_trajectory": {2025: 185, 2030: 178, 2035: 170, 2040: 163, 2050: 150},
        "paris_aligned_threshold_2030": 130,
        "current_global_level": 190,
        "unit_description": "kWh per square metre per year (commercial buildings)",
        "lower_is_better": True,
    },
}


# ---------------------------------------------------------------------------
# Reference Data — SDA Sectoral Decarbonization Approach Benchmarks
# kgCO2/unit from 2020 to 2050 at 5-year intervals for 10 sectors
# ---------------------------------------------------------------------------

SDA_BENCHMARKS: Dict[str, Dict] = {
    "power_kwh": {
        "label": "Power Generation",
        "unit": "gCO2/kWh",
        "benchmarks": {2020: 475, 2025: 350, 2030: 185, 2035: 85, 2040: 30, 2045: 8, 2050: 0},
    },
    "steel_t": {
        "label": "Steel Production",
        "unit": "tCO2/t crude steel",
        "benchmarks": {2020: 1.89, 2025: 1.60, 2030: 1.30, 2035: 0.90, 2040: 0.50, 2045: 0.20, 2050: 0.05},
    },
    "cement_t": {
        "label": "Cement Production",
        "unit": "kgCO2/t clinker",
        "benchmarks": {2020: 853, 2025: 770, 2030: 710, 2035: 610, 2040: 480, 2045: 330, 2050: 190},
    },
    "aluminium_t": {
        "label": "Aluminium Smelting",
        "unit": "tCO2/t aluminium",
        "benchmarks": {2020: 11.5, 2025: 9.8, 2030: 7.5, 2035: 5.0, 2040: 2.8, 2045: 1.2, 2050: 0.3},
    },
    "paper_t": {
        "label": "Paper and Pulp",
        "unit": "tCO2/t paper",
        "benchmarks": {2020: 0.89, 2025: 0.75, 2030: 0.58, 2035: 0.40, 2040: 0.24, 2045: 0.12, 2050: 0.03},
    },
    "chemicals_t": {
        "label": "Chemicals (High Value)",
        "unit": "tCO2/t HVC",
        "benchmarks": {2020: 1.75, 2025: 1.55, 2030: 1.25, 2035: 0.90, 2040: 0.55, 2045: 0.25, 2050: 0.05},
    },
    "aviation_rpk": {
        "label": "Aviation",
        "unit": "gCO2/RPK",
        "benchmarks": {2020: 95, 2025: 88, 2030: 75, 2035: 55, 2040: 35, 2045: 16, 2050: 7},
    },
    "shipping_tkm": {
        "label": "Shipping",
        "unit": "gCO2/tonne-nautical mile",
        "benchmarks": {2020: 11.9, 2025: 10.5, 2030: 8.5, 2035: 5.5, 2040: 2.5, 2045: 0.8, 2050: 0.3},
    },
    "buildings_kwh": {
        "label": "Buildings (Commercial)",
        "unit": "kWh/m2/yr",
        "benchmarks": {2020: 190, 2025: 155, 2030: 120, 2035: 85, 2040: 55, 2045: 35, 2050: 20},
    },
    "transport_pkm": {
        "label": "Road Transport (LDV)",
        "unit": "gCO2/pkm",
        "benchmarks": {2020: 155, 2025: 130, 2030: 95, 2035: 55, 2040: 25, 2045: 8, 2050: 2},
    },
}


# ---------------------------------------------------------------------------
# Reference Data — WACI to ITR Interpolation Table
# Anchor points: MSCI Carbon Delta / Carbon Portfolio Analytics (2021)
# WACI in tCO2e per USD million revenue
# ---------------------------------------------------------------------------

ITR_TABLE: List[Dict] = [
    {"waci_tco2_per_mn_usd": 0,    "temperature_c": 1.1},
    {"waci_tco2_per_mn_usd": 25,   "temperature_c": 1.3},
    {"waci_tco2_per_mn_usd": 50,   "temperature_c": 1.5},
    {"waci_tco2_per_mn_usd": 100,  "temperature_c": 1.7},
    {"waci_tco2_per_mn_usd": 200,  "temperature_c": 2.0},
    {"waci_tco2_per_mn_usd": 300,  "temperature_c": 2.3},
    {"waci_tco2_per_mn_usd": 450,  "temperature_c": 2.7},
    {"waci_tco2_per_mn_usd": 600,  "temperature_c": 3.0},
    {"waci_tco2_per_mn_usd": 800,  "temperature_c": 3.5},
    {"waci_tco2_per_mn_usd": 1000, "temperature_c": 4.0},
    {"waci_tco2_per_mn_usd": 1500, "temperature_c": 4.5},
    {"waci_tco2_per_mn_usd": 2000, "temperature_c": 5.0},
]

# Pre-built parallel lists for bisect interpolation
_ITR_WACI_LIST = [row["waci_tco2_per_mn_usd"] for row in ITR_TABLE]
_ITR_TEMP_LIST = [row["temperature_c"] for row in ITR_TABLE]


# ---------------------------------------------------------------------------
# Reference Data — PCAF DQS Data Quality Score Definitions
# ---------------------------------------------------------------------------

PCAF_DQS_DEFINITIONS: Dict[int, Dict] = {
    1: {"label": "Verified company-specific data",           "confidence_weight": 1.00, "description": "Audited or third-party verified GHG inventory at company level"},
    2: {"label": "Unverified company-specific data",         "confidence_weight": 0.80, "description": "Self-reported company GHG data without third-party verification"},
    3: {"label": "Sector average with company activity",     "confidence_weight": 0.60, "description": "Sector-average emission factor applied to company-specific activity data"},
    4: {"label": "Sector average with NACE proxy activity",  "confidence_weight": 0.40, "description": "Sector-average emission factor applied to NACE-level estimated activity"},
    5: {"label": "EEIO / economic input-output estimate",    "confidence_weight": 0.20, "description": "Environmentally-extended input-output model estimate from spend data"},
}


# ---------------------------------------------------------------------------
# Reference Data — 8 Carbon-intensive Sector Profiles
# ---------------------------------------------------------------------------

SECTOR_PROFILES: Dict[str, Dict] = {
    "power":      {"label": "Power Generation",         "nace": ["D35"],    "scope_focus": "S1", "benchmark_key": "power_kwh",    "high_carbon": True},
    "automotive": {"label": "Automotive",               "nace": ["C29"],    "scope_focus": "S3", "benchmark_key": "transport_pkm","high_carbon": True},
    "steel":      {"label": "Steel & Metals",           "nace": ["C24"],    "scope_focus": "S1", "benchmark_key": "steel_t",      "high_carbon": True},
    "cement":     {"label": "Cement & Construction",    "nace": ["C23"],    "scope_focus": "S1", "benchmark_key": "cement_t",     "high_carbon": True},
    "oil_and_gas":{"label": "Oil & Gas",                "nace": ["B06"],    "scope_focus": "S1", "benchmark_key": "chemicals_t",  "high_carbon": True},
    "aviation":   {"label": "Aviation",                 "nace": ["H51"],    "scope_focus": "S1", "benchmark_key": "aviation_rpk", "high_carbon": True},
    "shipping":   {"label": "Shipping",                 "nace": ["H50"],    "scope_focus": "S1", "benchmark_key": "shipping_tkm", "high_carbon": True},
    "real_estate":{"label": "Real Estate",              "nace": ["L68"],    "scope_focus": "S1", "benchmark_key": "buildings_kwh","high_carbon": True},
}


# ---------------------------------------------------------------------------
# Reference Data — SBTi FI Eligible Asset Classes and Methods
# ---------------------------------------------------------------------------

ASSET_CLASS_METHODS: Dict[str, Dict] = {
    "listed_equity": {
        "label": "Listed Equity",
        "pcaf_method": "WACI or Sectoral Decarbonization Approach (SDA)",
        "sbti_method": "Portfolio coverage approach or Temperature Rating method",
        "attribution_formula": "equity_ownership_pct x company_emissions",
        "data_sources": "CDP, company disclosures, MSCI, Trucost",
        "pcaf_part": "Part A, Section 3.1",
        "scope_coverage": ["S1", "S2", "S3"],
    },
    "corporate_bonds": {
        "label": "Corporate Bonds",
        "pcaf_method": "WACI or SDA — enterprise value including cash (EVIC) attribution",
        "sbti_method": "Portfolio coverage or Temperature Rating",
        "attribution_formula": "outstanding_amount / EVIC x company_emissions",
        "data_sources": "Bloomberg, Refinitiv, CDP, PCAF database",
        "pcaf_part": "Part A, Section 3.2",
        "scope_coverage": ["S1", "S2", "S3"],
    },
    "project_finance": {
        "label": "Project Finance",
        "pcaf_method": "Absolute Contraction Approach (project-level emissions)",
        "sbti_method": "Sector-specific benchmarks (IEA NZE)",
        "attribution_formula": "loan_amount / total_project_capex x project_emissions",
        "data_sources": "Project developer data, ESIA reports",
        "pcaf_part": "Part A, Section 3.3",
        "scope_coverage": ["S1", "S2"],
    },
    "real_estate": {
        "label": "Real Estate (Commercial & Residential)",
        "pcaf_method": "CRREM decarbonisation pathway or absolute contraction",
        "sbti_method": "CRREM pathway alignment or SBTi Buildings pathway",
        "attribution_formula": "mortgage_outstanding / property_value x property_emissions",
        "data_sources": "EPC certificates, energy bills, CRREM tool",
        "pcaf_part": "Part A, Section 3.4",
        "scope_coverage": ["S1", "S2"],
    },
    "mortgages": {
        "label": "Residential Mortgages",
        "pcaf_method": "CRREM residential pathway",
        "sbti_method": "CRREM pathway alignment",
        "attribution_formula": "outstanding_mortgage / property_value x property_emissions",
        "data_sources": "EPC certificates, national energy databases, CRREM",
        "pcaf_part": "Part A, Section 3.5",
        "scope_coverage": ["S1", "S2"],
    },
    "sovereign_bonds": {
        "label": "Sovereign Bonds",
        "pcaf_method": "GDP/debt-based attribution — PCAF Part D",
        "sbti_method": "Not yet included in SBTi FI standard; NDC alignment proxy",
        "attribution_formula": "bond_value / (GDP + total_government_debt) x country_ghg_inventory",
        "data_sources": "UNFCCC inventories, World Bank GDP/debt, NDC Registry",
        "pcaf_part": "Part D",
        "scope_coverage": ["S1", "S2", "S3_LULUCF"],
    },
}


# ---------------------------------------------------------------------------
# Engagement Priority Thresholds
# ---------------------------------------------------------------------------

ENGAGEMENT_THRESHOLDS: Dict[str, Dict] = {
    "high": {
        "criteria": "Sector ITR > 3.0C OR sector exposure > 15% of portfolio",
        "action": "Bilateral direct engagement, escalation to proxy voting within 12 months",
    },
    "medium": {
        "criteria": "Sector ITR between 2.0-3.0C OR sector exposure 5-15% of portfolio",
        "action": "Collaborative engagement via CA100+/NZIF; progress review annually",
    },
    "low": {
        "criteria": "Sector ITR < 2.0C AND sector exposure < 5% of portfolio",
        "action": "Monitor; include in routine stewardship letters",
    },
}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class HoldingEntry(BaseModel):
    model_config = {"protected_namespaces": ()}

    asset_name: str
    asset_class: str = Field(..., description="Asset class key: listed_equity / corporate_bonds / project_finance / real_estate / mortgages / sovereign_bonds")
    sector: str = Field(..., description="Sector key matching PACTA_SECTOR_PATHWAYS or SECTOR_PROFILES")
    nace_code: str = Field("", description="NACE code of the investee")
    portfolio_weight_pct: float = Field(..., ge=0.0, le=100.0, description="Portfolio weight as % of total AUM")
    exposure_bn: float = Field(..., ge=0.0, description="Exposure in USD billions")
    scope1_emissions_tco2: float = Field(0.0, ge=0.0, description="Scope 1 financed emissions tCO2e")
    scope2_emissions_tco2: float = Field(0.0, ge=0.0, description="Scope 2 financed emissions tCO2e")
    scope3_emissions_tco2: float = Field(0.0, ge=0.0, description="Scope 3 financed emissions tCO2e")
    revenue_mn: float = Field(..., gt=0.0, description="Investee annual revenue in USD millions")
    data_quality_score: int = Field(..., ge=1, le=5, description="PCAF DQS 1 (best) to 5 (worst)")


class SBTiTargets(BaseModel):
    model_config = {"protected_namespaces": ()}

    near_term_year: int = Field(2030, ge=2025, le=2035)
    near_term_reduction_pct: float = Field(..., ge=0.0, le=100.0, description="% absolute reduction in S1+2 vs base year by near_term_year")
    long_term_year: int = Field(2050, ge=2040, le=2060)
    long_term_reduction_pct: float = Field(..., ge=0.0, le=100.0, description="% absolute reduction in S1+2 vs base year by long_term_year")
    net_zero_year: int = Field(2050, ge=2040, le=2070)


class TemperatureAlignmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    portfolio_name: str
    fi_type: str = Field(..., description="FI type: bank / insurer / asset_manager / pension_fund / development_fi")
    total_aum_bn: float = Field(..., gt=0.0, description="Total AUM in USD billions")
    holdings: List[HoldingEntry]
    methodology: str = Field("waci", description="waci / sda / temperature_rating / pacta")
    base_year: int = Field(2020, ge=2015, le=2025)
    sbti_targets: Optional[SBTiTargets] = None


class WACIRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    holdings: List[HoldingEntry]


class SBTiFIRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    portfolio_name: str
    portfolio_waci: float = Field(..., ge=0.0)
    scope1_financed_tco2: float = Field(..., ge=0.0)
    scope2_financed_tco2: float = Field(..., ge=0.0)
    scope3_financed_tco2: float = Field(..., ge=0.0)
    base_year: int = Field(2020)
    target_year: int = Field(2050)
    sbti_targets: Optional[SBTiTargets] = None
    flag_sector_exposure_pct: float = Field(0.0, ge=0.0, le=100.0)
    portfolio_companies_with_sbti_pct: float = Field(0.0, ge=0.0, le=100.0)


class SectorAlignmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    sector: str = Field(..., description="Sector key matching PACTA_SECTOR_PATHWAYS")
    current_value: float = Field(..., description="Current metric value (same unit as pathway metric_unit)")
    metric_unit: str = Field("", description="Unit description (optional override)")
    base_year: int = Field(2023, ge=2020, le=2030)


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class TemperatureAlignmentEngine:
    """E103 — Financed Emissions Temperature Alignment Engine (PCAF + SBTi FI + PACTA)."""

    # -------------------------------------------------------------------------
    # Public Methods
    # -------------------------------------------------------------------------

    def assess_temperature_alignment(
        self,
        portfolio_name: str,
        fi_type: str,
        total_aum_bn: float,
        holdings: List[HoldingEntry],
        methodology: str,
        base_year: int,
        sbti_targets: Optional[SBTiTargets] = None,
    ) -> Dict[str, Any]:
        """
        Full portfolio temperature alignment assessment.

        Computes:
        - WACI (exposure-weighted average carbon intensity) tCO2/$mn
        - Portfolio-level ITR via WACI interpolation
        - Sector-level WACI, ITR, and PACTA alignment %
        - PCAF DQS exposure-weighted quality score
        - SBTi FI criteria assessment (if targets provided)
        - Engagement priority list by sector
        """
        if not holdings:
            return {"error": "No holdings provided", "portfolio_name": portfolio_name}

        portfolio_waci = self.calculate_waci(holdings)
        portfolio_itr = self.calculate_itr(portfolio_waci)
        dqs_score = self.calculate_pcaf_dqs(holdings)

        # Sector breakdown
        sector_map: Dict[str, List[HoldingEntry]] = {}
        for h in holdings:
            sector_map.setdefault(h.sector, []).append(h)

        sector_results: List[Dict] = []
        engagement_list: List[Dict] = []

        for sector, sector_holdings in sector_map.items():
            s_waci = self.calculate_waci(sector_holdings)
            s_itr = self.calculate_itr(s_waci)
            s_exposure = sum(h.exposure_bn for h in sector_holdings)
            s_weight_pct = (s_exposure / total_aum_bn) * 100 if total_aum_bn > 0 else 0.0

            # PACTA alignment for sector
            pathway = PACTA_SECTOR_PATHWAYS.get(sector)
            pacta_pct: Optional[float] = None
            if pathway:
                nze_2030 = pathway["nze_trajectory"].get(2030)
                lower = pathway.get("lower_is_better", False)
                if nze_2030 is not None:
                    pacta_pct = self._pacta_alignment_pct(s_waci, nze_2030, lower)

            eng_priority = self._engagement_priority(s_itr, s_weight_pct)
            sector_results.append({
                "sector": sector,
                "sector_label": SECTOR_PROFILES.get(sector, {}).get("label", sector),
                "exposure_bn": round(s_exposure, 4),
                "portfolio_weight_pct": round(s_weight_pct, 2),
                "sector_waci": round(s_waci, 2),
                "sector_itr": round(s_itr, 2),
                "pacta_alignment_pct": round(pacta_pct, 1) if pacta_pct is not None else None,
                "engagement_priority": eng_priority,
                "holding_count": len(sector_holdings),
            })
            if eng_priority in ("high", "medium"):
                engagement_list.append({
                    "sector": sector,
                    "itr": round(s_itr, 2),
                    "exposure_bn": round(s_exposure, 4),
                    "priority": eng_priority,
                    "recommended_action": ENGAGEMENT_THRESHOLDS[eng_priority]["action"],
                })

        # Total financed emissions
        total_s1 = sum(h.scope1_emissions_tco2 for h in holdings)
        total_s2 = sum(h.scope2_emissions_tco2 for h in holdings)
        total_s3 = sum(h.scope3_emissions_tco2 for h in holdings)

        # SBTi assessment
        sbti_result: Optional[Dict] = None
        if sbti_targets:
            sbti_result = self.assess_sbti_fi_criteria(
                portfolio_waci=portfolio_waci,
                scope1_financed=total_s1,
                scope2_financed=total_s2,
                scope3_financed=total_s3,
                base_year=base_year,
                target_year=sbti_targets.long_term_year,
                sbti_targets=sbti_targets,
            )

        on_track_15c = portfolio_itr <= 1.5
        on_track_2c = portfolio_itr <= 2.0

        return {
            "portfolio_name": portfolio_name,
            "fi_type": fi_type,
            "total_aum_bn": total_aum_bn,
            "base_year": base_year,
            "methodology": methodology,
            "assessment_date": datetime.utcnow().isoformat() + "Z",
            "portfolio_waci": round(portfolio_waci, 2),
            "portfolio_itr": round(portfolio_itr, 2),
            "pcaf_dqs_score": round(dqs_score, 2),
            "on_track_1_5c": on_track_15c,
            "on_track_2c": on_track_2c,
            "total_holdings": len(holdings),
            "total_financed_emissions": {
                "scope1_tco2": round(total_s1, 0),
                "scope2_tco2": round(total_s2, 0),
                "scope3_tco2": round(total_s3, 0),
                "total_tco2": round(total_s1 + total_s2 + total_s3, 0),
            },
            "sector_results": sorted(sector_results, key=lambda x: x["sector_itr"], reverse=True),
            "engagement_priorities": sorted(engagement_list, key=lambda x: x["itr"], reverse=True),
            "sbti_assessment": sbti_result,
            "waci_benchmarks": {
                "1_5c_aligned": 50,
                "below_2c": 200,
                "current_policies": 450,
            },
            "dqs_confidence": PCAF_DQS_DEFINITIONS.get(round(dqs_score), {}).get("label", ""),
        }

    def calculate_waci(self, holdings: List[HoldingEntry]) -> float:
        """
        WACI = sum(portfolio_weight_i x scope12_emissions_i / revenue_i_mn).
        Exposure-weighted average carbon intensity in tCO2e per USD million revenue.
        """
        if not holdings:
            return 0.0
        total_weight = sum(h.portfolio_weight_pct for h in holdings)
        if total_weight <= 0:
            return 0.0
        waci = 0.0
        for h in holdings:
            weight_norm = h.portfolio_weight_pct / total_weight
            total_emissions = h.scope1_emissions_tco2 + h.scope2_emissions_tco2
            if h.revenue_mn > 0:
                waci += weight_norm * (total_emissions / h.revenue_mn)
        return waci

    def calculate_itr(self, waci: float) -> float:
        """
        Interpolate ITR from WACI using MSCI/Carbon Delta anchor table.
        Linear interpolation between table anchor points.
        Returns temperature in degrees Celsius.
        """
        if waci <= 0:
            return _ITR_TEMP_LIST[0]
        if waci >= _ITR_WACI_LIST[-1]:
            return _ITR_TEMP_LIST[-1]

        idx = bisect.bisect_right(_ITR_WACI_LIST, waci) - 1
        idx = max(0, min(idx, len(_ITR_WACI_LIST) - 2))

        w0, w1 = _ITR_WACI_LIST[idx], _ITR_WACI_LIST[idx + 1]
        t0, t1 = _ITR_TEMP_LIST[idx], _ITR_TEMP_LIST[idx + 1]
        frac = (waci - w0) / (w1 - w0) if (w1 - w0) > 0 else 0.0
        return t0 + frac * (t1 - t0)

    def calculate_pcaf_dqs(self, holdings: List[HoldingEntry]) -> float:
        """
        Exposure-weighted PCAF DQS score 1-5.
        DQS 1 = best (verified); DQS 5 = worst (EEIO estimate).
        """
        if not holdings:
            return 5.0
        total_exposure = sum(h.exposure_bn for h in holdings)
        if total_exposure <= 0:
            return 5.0
        weighted_dqs = sum(h.data_quality_score * h.exposure_bn for h in holdings)
        return weighted_dqs / total_exposure

    def assess_sbti_fi_criteria(
        self,
        portfolio_waci: float,
        scope1_financed: float,
        scope2_financed: float,
        scope3_financed: float,
        base_year: int,
        target_year: int,
        sbti_targets: Optional[SBTiTargets] = None,
        portfolio_name: str = "",
        flag_sector_exposure_pct: float = 0.0,
        portfolio_companies_with_sbti_pct: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Score portfolio against all 6 SBTi FI Net-Zero Standard v1.0 criteria.
        Returns per-criterion compliance status and overall score.
        """
        total_s12 = scope1_financed + scope2_financed
        criteria_results: List[Dict] = []
        total_weight = 0.0
        weighted_score = 0.0

        for crit_id, crit_meta in SBTI_FI_CRITERIA.items():
            weight = crit_meta["weight"]
            score, status, notes = self._score_sbti_criterion(
                crit_id, crit_meta, total_s12, scope3_financed,
                portfolio_waci, sbti_targets,
                flag_sector_exposure_pct, portfolio_companies_with_sbti_pct,
                base_year,
            )
            weighted_score += score * weight
            total_weight += weight

            criteria_results.append({
                "criterion_id": crit_id,
                "label": crit_meta["label"],
                "scope": crit_meta["scope"],
                "method": crit_meta["method"],
                "weight": weight,
                "score": round(score, 3),
                "status": status,
                "notes": notes,
                "sbti_guidance": crit_meta["sbti_guidance"],
            })

        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
        overall_status = (
            "compliant" if overall_score >= 0.80
            else "partial" if overall_score >= 0.50
            else "non_compliant"
        )

        return {
            "portfolio_name": portfolio_name,
            "overall_score": round(overall_score, 4),
            "overall_status": overall_status,
            "criteria_results": criteria_results,
            "total_financed_s1_s2_tco2": round(total_s12, 0),
            "total_financed_s3_tco2": round(scope3_financed, 0),
            "standard": "SBTi Financial Institutions Net-Zero Standard v1.0",
            "validation_body": "Science Based Targets initiative (SBTi)",
        }

    def calculate_sector_alignment(
        self,
        sector: str,
        current_value: float,
        base_year: int,
    ) -> Dict[str, Any]:
        """
        PACTA % alignment for a single sector vs IEA NZE 2050 trajectory.
        Returns alignment percentage and gap to 2030 NZE benchmark.
        """
        pathway = PACTA_SECTOR_PATHWAYS.get(sector)
        if not pathway:
            return {
                "sector": sector,
                "error": f"Sector '{sector}' not found in PACTA pathways",
                "available_sectors": list(PACTA_SECTOR_PATHWAYS.keys()),
            }

        nze_2030 = pathway["nze_trajectory"].get(2030, 0.0)
        nze_2050 = pathway["nze_trajectory"].get(2050, 0.0)
        cps_2030 = pathway["cps_trajectory"].get(2030, 0.0)
        lower = pathway.get("lower_is_better", False)
        threshold = pathway.get("paris_aligned_threshold_2030", nze_2030)
        current_global = pathway.get("current_global_level", 0.0)

        if lower:
            gap_to_nze_2030 = current_value - nze_2030
            gap_to_threshold = current_value - threshold
            paris_aligned = current_value <= threshold
            alignment_pct = max(0.0, 100.0 - ((current_value - nze_2030) / max(cps_2030 - nze_2030, 0.001)) * 100)
        else:
            gap_to_nze_2030 = nze_2030 - current_value
            gap_to_threshold = threshold - current_value
            paris_aligned = current_value >= threshold
            alignment_pct = min(100.0, (current_value / max(nze_2030, 0.001)) * 100)

        alignment_pct = max(0.0, min(alignment_pct, 100.0))

        return {
            "sector": sector,
            "sector_label": pathway["label"],
            "metric": pathway["metric"],
            "metric_unit": pathway["metric_unit"],
            "current_value": current_value,
            "nze_2030_benchmark": nze_2030,
            "nze_2050_benchmark": nze_2050,
            "cps_2030_benchmark": cps_2030,
            "paris_aligned_threshold_2030": threshold,
            "current_global_average": current_global,
            "base_year": base_year,
            "paris_aligned": paris_aligned,
            "pacta_alignment_pct": round(alignment_pct, 1),
            "gap_to_nze_2030": round(gap_to_nze_2030, 4),
            "gap_to_paris_threshold": round(gap_to_threshold, 4),
            "lower_is_better": lower,
            "nze_full_trajectory": pathway["nze_trajectory"],
            "cps_full_trajectory": pathway["cps_trajectory"],
        }

    def get_alignment_benchmarks(self) -> Dict[str, Any]:
        """Return all sector pathways and ITR interpolation table."""
        return {
            "sector_pathways": PACTA_SECTOR_PATHWAYS,
            "itr_table": ITR_TABLE,
            "sda_benchmarks": SDA_BENCHMARKS,
            "total_sectors": len(PACTA_SECTOR_PATHWAYS),
            "itr_methodology": "MSCI Carbon Delta / Carbon Portfolio Analytics (2021)",
            "pathway_source": "IEA World Energy Outlook NZE 2050 Scenario (2023)",
        }

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    def _pacta_alignment_pct(self, current: float, nze_target: float, lower_is_better: bool) -> float:
        """Calculate % alignment relative to NZE 2030 target."""
        if lower_is_better:
            if current <= nze_target:
                return 100.0
            # Score degrades linearly; assume 2x NZE = 0%
            return max(0.0, 100.0 - ((current - nze_target) / max(nze_target, 1.0)) * 100)
        else:
            if current >= nze_target:
                return 100.0
            return max(0.0, (current / max(nze_target, 0.001)) * 100)

    def _engagement_priority(self, itr: float, weight_pct: float) -> str:
        if itr > 3.0 or weight_pct > 15.0:
            return "high"
        if itr > 2.0 or weight_pct > 5.0:
            return "medium"
        return "low"

    def _score_sbti_criterion(
        self,
        crit_id: str,
        crit_meta: Dict,
        total_s12: float,
        scope3_financed: float,
        portfolio_waci: float,
        sbti_targets: Optional[SBTiTargets],
        flag_exposure_pct: float,
        companies_with_sbti_pct: float,
        base_year: int,
    ) -> Tuple[float, str, str]:
        """Return (score 0-1, status, notes) for a single SBTi FI criterion."""

        if crit_id == "NZ-1":
            if sbti_targets:
                req = crit_meta.get("required_reduction_pct", 90.0)
                score = min(sbti_targets.long_term_reduction_pct / req, 1.0)
                status = "met" if score >= 1.0 else "partially_met" if score >= 0.5 else "not_met"
                notes = f"Long-term S1+2 reduction target: {sbti_targets.long_term_reduction_pct}% vs required {req}%"
            else:
                score = 0.0
                status = "not_assessed"
                notes = "No long-term SBTi targets provided"

        elif crit_id == "NZ-2":
            if sbti_targets:
                req = crit_meta.get("required_reduction_pct", 90.0)
                # Use near-term reduction as proxy for long-term direction
                score = min(sbti_targets.long_term_reduction_pct / req, 1.0) * 0.9
                status = "partially_met" if score >= 0.5 else "not_met"
                notes = f"Scope 3 net-zero target inferred from long-term: {sbti_targets.long_term_reduction_pct}%"
            else:
                score = 0.0
                status = "not_assessed"
                notes = "No S3 long-term reduction target provided"

        elif crit_id == "NT-1":
            if sbti_targets:
                req = crit_meta.get("required_reduction_pct", 42.0)
                score = min(sbti_targets.near_term_reduction_pct / req, 1.0)
                status = "met" if score >= 1.0 else "partially_met" if score >= 0.5 else "not_met"
                notes = f"Near-term S1+2 target: {sbti_targets.near_term_reduction_pct}% by {sbti_targets.near_term_year} vs required {req}%"
            else:
                # Infer from WACI proximity to 1.5C benchmark (WACI < 50)
                score = max(0.0, 1.0 - (portfolio_waci / 200))
                status = "partially_met" if score >= 0.4 else "not_met"
                notes = f"No formal NT targets; portfolio WACI {portfolio_waci:.1f} used as proxy"

        elif crit_id == "NT-2":
            req = crit_meta.get("required_coverage_pct", 25.0)
            # proxy: if scope3 < 40% of total emissions, consider engaged
            total = total_s12 + scope3_financed
            s3_share = (scope3_financed / total * 100) if total > 0 else 0
            score = min(s3_share / req, 1.0) * 0.6  # engagement is directional
            status = "partially_met" if score >= 0.3 else "not_met"
            notes = f"S3 share of financed emissions: {s3_share:.1f}%; no formal engagement target provided"

        elif crit_id == "FLAG-1":
            applies = flag_exposure_pct >= crit_meta.get("applies_if_flag_exposure_pct", 5.0)
            if not applies:
                score = 1.0
                status = "not_applicable"
                notes = f"FLAG exposure {flag_exposure_pct:.1f}% below 5% threshold; FLAG-1 not required"
            else:
                score = 0.3
                status = "not_met"
                notes = f"FLAG exposure {flag_exposure_pct:.1f}% >= 5%; FLAG Science-Based Target required"

        elif crit_id == "FI-1":
            req = crit_meta.get("required_coverage_pct", 50.0)
            score = min(companies_with_sbti_pct / req, 1.0)
            status = "met" if score >= 1.0 else "partially_met" if score >= 0.5 else "not_met"
            notes = f"Portfolio companies with SBTi-validated targets: {companies_with_sbti_pct:.1f}% vs required {req:.0f}%"

        else:
            score = 0.0
            status = "not_assessed"
            notes = "Criterion not recognised"

        return score, status, notes
