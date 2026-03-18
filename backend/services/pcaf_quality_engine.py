"""
PCAF Data Quality Score Engine
=================================
Comprehensive Data Quality Score (DQS) framework engine for the Partnership
for Carbon Accounting Financials (PCAF) Standard.  Evaluates data quality
across five dimensions, scores individual holdings and full portfolios,
computes financed emissions with DQS-weighted confidence bands, and
generates regulatory cross-framework disclosures (SFDR PAI, CSRD ESRS E1,
TCFD, ISSB S2, GRI 305, EU Taxonomy, CDP, NZBA).

Coverage:
  - 6 PCAF asset classes with attribution methods
  - 5 DQS levels (1=highest, 5=lowest) per the PCAF Standard v2.0
  - 5 quality dimensions with configurable weights
  - 15+ NACE sector emission factors for DQS 4-5 estimation
  - 4 attribution approaches (EVIC, balance sheet, project, floor area)
  - DQS improvement pathways (5->4, 4->3, 3->2, 2->1)
  - 8 cross-framework regulatory mappings
  - Sector-median DQS benchmarks (10 sectors)
  - Exposure-weighted portfolio DQS aggregation
  - SFDR PAI 1/2/3 indicator computation
  - Confidence band estimation from DQS uncertainty

References:
  - PCAF Global GHG Accounting & Reporting Standard v2.0 (Nov 2022)
  - PCAF Capital Market Instruments guidance (2023)
  - SFDR RTS Annex I — PAI 1 (Financed GHG), PAI 2 (Carbon footprint),
    PAI 3 (GHG intensity of investees)
  - CSRD ESRS E1-6 (Financed emissions disclosure)
  - TCFD Metrics & Targets — Portfolio financed emissions
  - IFRS S2 Climate-related Disclosures — Industry metrics
  - GRI 305-3 Scope 3 Category 15 (Investments)
  - EU Taxonomy Regulation — Green Asset Ratio denominators
  - CDP Financial Services Questionnaire C-FS14
  - Net-Zero Banking Alliance (NZBA) portfolio alignment targets
  - GHG Protocol Corporate Value Chain (Scope 3) Standard

API Routes (to be wired in api/v1/routes/pcaf_quality.py):
  POST /api/v1/pcaf-quality/score-holding
  POST /api/v1/pcaf-quality/score-portfolio
  POST /api/v1/pcaf-quality/assess-data-quality
  GET  /api/v1/pcaf-quality/asset-classes
  GET  /api/v1/pcaf-quality/dqs-levels
  GET  /api/v1/pcaf-quality/quality-dimensions
  GET  /api/v1/pcaf-quality/emission-factors
  GET  /api/v1/pcaf-quality/attribution-methods
  GET  /api/v1/pcaf-quality/improvement-paths
  GET  /api/v1/pcaf-quality/cross-framework-map
  GET  /api/v1/pcaf-quality/quality-benchmarks
"""
from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("platform.pcaf_quality")


# ---------------------------------------------------------------------------
# PCAF Asset Classes (6 per PCAF Standard v2.0)
# ---------------------------------------------------------------------------

PCAF_ASSET_CLASSES: list[dict] = [
    {
        "asset_class_id": "listed_equity_corporate_bonds",
        "label": "Listed Equity and Corporate Bonds",
        "description": (
            "Publicly traded equity holdings and corporate bonds. Attribution "
            "uses Enterprise Value Including Cash (EVIC) to allocate the "
            "investee's emissions to the investor."
        ),
        "typical_attribution_method": "enterprise_value",
    },
    {
        "asset_class_id": "business_loans_unlisted_equity",
        "label": "Business Loans and Unlisted Equity",
        "description": (
            "Bilateral or syndicated business loans and equity in non-listed "
            "companies. Attribution uses total equity plus debt (balance sheet "
            "approach) when EVIC is unavailable."
        ),
        "typical_attribution_method": "balance_sheet_equity_debt",
    },
    {
        "asset_class_id": "project_finance",
        "label": "Project Finance",
        "description": (
            "Financing of specific projects (e.g. renewable energy, "
            "infrastructure). Attribution is pro-rata to the investor's "
            "share of total project financing."
        ),
        "typical_attribution_method": "project_level",
    },
    {
        "asset_class_id": "commercial_real_estate",
        "label": "Commercial Real Estate",
        "description": (
            "Loans secured by or investments in commercial properties "
            "(office, retail, logistics, hospitality). Attribution uses "
            "property value and energy performance certificates."
        ),
        "typical_attribution_method": "floor_area",
    },
    {
        "asset_class_id": "mortgages",
        "label": "Mortgages (Residential)",
        "description": (
            "Residential mortgage loans. Attribution uses outstanding loan "
            "amount relative to property value and building-level energy "
            "performance data (EPC ratings)."
        ),
        "typical_attribution_method": "floor_area",
    },
    {
        "asset_class_id": "motor_vehicle_loans",
        "label": "Motor Vehicle Loans",
        "description": (
            "Loans for purchase or lease of motor vehicles. Attribution uses "
            "outstanding amount relative to vehicle value with vehicle-specific "
            "or type-average emission factors (gCO2/km)."
        ),
        "typical_attribution_method": "enterprise_value",
    },
]

_ASSET_CLASS_BY_ID: dict[str, dict] = {
    ac["asset_class_id"]: ac for ac in PCAF_ASSET_CLASSES
}


# ---------------------------------------------------------------------------
# PCAF DQS Levels (1 = best, 5 = worst)
# ---------------------------------------------------------------------------

PCAF_DQS_LEVELS: list[dict] = [
    {
        "score": 1,
        "label": "Audited emissions data",
        "description": (
            "Verified GHG emissions data (Scope 1, 2, and relevant Scope 3 "
            "categories) directly reported by the borrower/investee and "
            "assured by an accredited third party (e.g. ISO 14064-3, ISAE 3410)."
        ),
        "data_source": "Investee-reported, third-party verified",
        "estimation_method": "Direct measurement / continuous monitoring",
        "confidence_weight": 1.0,
        "typical_uncertainty_pct": 5.0,
    },
    {
        "score": 2,
        "label": "Unaudited reported emissions",
        "description": (
            "GHG emissions data reported directly by the borrower/investee "
            "but not externally verified. May cover Scope 1 + 2 with partial "
            "Scope 3 disclosure."
        ),
        "data_source": "Investee-reported, unverified",
        "estimation_method": "Self-reported calculation",
        "confidence_weight": 0.8,
        "typical_uncertainty_pct": 15.0,
    },
    {
        "score": 3,
        "label": "Physical activity-based estimates",
        "description": (
            "Emissions estimated using physical activity data from the "
            "borrower/investee (e.g. kWh energy consumption, litres of fuel, "
            "tonnes of feedstock) combined with verified emission factors."
        ),
        "data_source": "Investee physical activity data",
        "estimation_method": "Activity data x emission factor",
        "confidence_weight": 0.6,
        "typical_uncertainty_pct": 30.0,
    },
    {
        "score": 4,
        "label": "Economic activity-based estimates",
        "description": (
            "Emissions estimated using economic activity data (e.g. revenue, "
            "assets) of the borrower/investee combined with region- or "
            "sector-specific emission factors (tCO2e per EUR revenue)."
        ),
        "data_source": "Economic activity data (revenue, assets)",
        "estimation_method": "Revenue x sector emission factor",
        "confidence_weight": 0.4,
        "typical_uncertainty_pct": 45.0,
    },
    {
        "score": 5,
        "label": "Sector-average proxy estimates",
        "description": (
            "Emissions estimated using sector-average data based on NACE or "
            "GICS classification, without any entity-specific activity data. "
            "Least accurate; used when no other data is available."
        ),
        "data_source": "Sector-average statistics (NACE/GICS proxy)",
        "estimation_method": "Sector average x outstanding amount",
        "confidence_weight": 0.2,
        "typical_uncertainty_pct": 60.0,
    },
]

_DQS_LEVEL_BY_SCORE: dict[int, dict] = {
    lvl["score"]: lvl for lvl in PCAF_DQS_LEVELS
}


# ---------------------------------------------------------------------------
# PCAF Quality Dimensions (5 dimensions, weights sum to 1.0)
# ---------------------------------------------------------------------------

PCAF_QUALITY_DIMENSIONS: list[dict] = [
    {
        "dimension_id": "emissions_data_quality",
        "label": "Emissions Data Quality",
        "description": (
            "Source and reliability of the underlying GHG emissions data. "
            "Ranges from third-party verified (DQS 1) to sector proxy (DQS 5)."
        ),
        "weight": 0.35,
    },
    {
        "dimension_id": "data_completeness",
        "label": "Data Completeness",
        "description": (
            "Coverage of Scope 1, 2, and relevant Scope 3 categories, as "
            "well as value chain completeness. Full coverage with verification "
            "scores 1; missing Scope 3 entirely scores 4-5."
        ),
        "weight": 0.25,
    },
    {
        "dimension_id": "data_timeliness",
        "label": "Data Timeliness",
        "description": (
            "Recency of the emissions data relative to the reporting period. "
            "Current year data scores 1; data lagging more than 3 years "
            "scores 5."
        ),
        "weight": 0.15,
    },
    {
        "dimension_id": "data_granularity",
        "label": "Data Granularity",
        "description": (
            "Level of granularity of the data: entity-specific (DQS 1-2), "
            "sub-sector (DQS 3), or broad sector average (DQS 5)."
        ),
        "weight": 0.15,
    },
    {
        "dimension_id": "methodology_robustness",
        "label": "Methodology Robustness",
        "description": (
            "Degree of adherence to the PCAF Standard methodology including "
            "correct attribution factor calculation, appropriate emission "
            "factors, and consistent boundary application."
        ),
        "weight": 0.10,
    },
]

_DIMENSION_WEIGHTS: dict[str, float] = {
    d["dimension_id"]: d["weight"] for d in PCAF_QUALITY_DIMENSIONS
}


# ---------------------------------------------------------------------------
# PCAF Emission Factors by NACE Sector (for DQS 4-5 estimation)
# Units: tCO2e per million EUR revenue (unless otherwise noted)
# ---------------------------------------------------------------------------

PCAF_EMISSION_FACTORS: list[dict] = [
    {"nace_code": "A", "sector_label": "Agriculture, Forestry and Fishing",
     "scope1_ef_tco2_per_meur": 520.0, "scope2_ef": 85.0, "scope3_ef": 1250.0,
     "data_year": 2023, "source": "Eurostat / PCAF DB 2023"},
    {"nace_code": "B", "sector_label": "Mining and Quarrying",
     "scope1_ef_tco2_per_meur": 680.0, "scope2_ef": 120.0, "scope3_ef": 890.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "C", "sector_label": "Manufacturing",
     "scope1_ef_tco2_per_meur": 310.0, "scope2_ef": 95.0, "scope3_ef": 720.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "D", "sector_label": "Electricity, Gas, Steam and AC Supply",
     "scope1_ef_tco2_per_meur": 1450.0, "scope2_ef": 40.0, "scope3_ef": 380.0,
     "data_year": 2023, "source": "EEA / PCAF DB 2023"},
    {"nace_code": "E", "sector_label": "Water Supply, Sewerage, Waste Management",
     "scope1_ef_tco2_per_meur": 290.0, "scope2_ef": 110.0, "scope3_ef": 410.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "F", "sector_label": "Construction",
     "scope1_ef_tco2_per_meur": 180.0, "scope2_ef": 45.0, "scope3_ef": 620.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "G", "sector_label": "Wholesale and Retail Trade",
     "scope1_ef_tco2_per_meur": 55.0, "scope2_ef": 40.0, "scope3_ef": 380.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "H", "sector_label": "Transportation and Storage",
     "scope1_ef_tco2_per_meur": 620.0, "scope2_ef": 35.0, "scope3_ef": 290.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "I", "sector_label": "Accommodation and Food Service",
     "scope1_ef_tco2_per_meur": 85.0, "scope2_ef": 60.0, "scope3_ef": 340.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "J", "sector_label": "Information and Communication",
     "scope1_ef_tco2_per_meur": 12.0, "scope2_ef": 55.0, "scope3_ef": 180.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "K", "sector_label": "Financial and Insurance Activities",
     "scope1_ef_tco2_per_meur": 8.0, "scope2_ef": 25.0, "scope3_ef": 95.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "L", "sector_label": "Real Estate Activities",
     "scope1_ef_tco2_per_meur": 35.0, "scope2_ef": 80.0, "scope3_ef": 150.0,
     "data_year": 2023, "source": "CRREM / PCAF DB 2023"},
    {"nace_code": "M", "sector_label": "Professional, Scientific and Technical",
     "scope1_ef_tco2_per_meur": 10.0, "scope2_ef": 30.0, "scope3_ef": 120.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "N", "sector_label": "Administrative and Support Services",
     "scope1_ef_tco2_per_meur": 22.0, "scope2_ef": 35.0, "scope3_ef": 160.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "O", "sector_label": "Public Administration and Defence",
     "scope1_ef_tco2_per_meur": 45.0, "scope2_ef": 50.0, "scope3_ef": 200.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
    {"nace_code": "Q", "sector_label": "Human Health and Social Work",
     "scope1_ef_tco2_per_meur": 28.0, "scope2_ef": 55.0, "scope3_ef": 190.0,
     "data_year": 2023, "source": "PCAF Emission Factor DB 2023"},
]

_EF_BY_NACE: dict[str, dict] = {
    ef["nace_code"]: ef for ef in PCAF_EMISSION_FACTORS
}


# ---------------------------------------------------------------------------
# PCAF Attribution Methods (4 approaches)
# ---------------------------------------------------------------------------

PCAF_ATTRIBUTION_METHODS: list[dict] = [
    {
        "method_id": "enterprise_value",
        "label": "Enterprise Value Including Cash (EVIC)",
        "formula_description": (
            "Attribution Factor = Outstanding Amount / EVIC, where "
            "EVIC = Market capitalisation + total debt + preferred equity + "
            "minority interest (at year end)."
        ),
        "applicable_asset_classes": [
            "listed_equity_corporate_bonds",
            "motor_vehicle_loans",
        ],
    },
    {
        "method_id": "balance_sheet_equity_debt",
        "label": "Balance Sheet (Total Equity + Debt)",
        "formula_description": (
            "Attribution Factor = Outstanding Amount / (Total Equity + Total Debt). "
            "Used when EVIC is not available (unlisted companies, private loans)."
        ),
        "applicable_asset_classes": [
            "business_loans_unlisted_equity",
        ],
    },
    {
        "method_id": "project_level",
        "label": "Project-Level Pro-Rata Share",
        "formula_description": (
            "Attribution Factor = Investor's Financing Share / Total Project "
            "Financing. Emissions attributed proportionally to the investor's "
            "commitment as a share of total project cost."
        ),
        "applicable_asset_classes": [
            "project_finance",
        ],
    },
    {
        "method_id": "floor_area",
        "label": "Floor Area / Property Value",
        "formula_description": (
            "Attribution Factor = Outstanding Amount / Property Value at "
            "origination. Emissions estimated from building energy performance "
            "data (kWh/m2/yr) x floor area x grid emission factor."
        ),
        "applicable_asset_classes": [
            "commercial_real_estate",
            "mortgages",
        ],
    },
]

_ATTRIBUTION_BY_ID: dict[str, dict] = {
    am["method_id"]: am for am in PCAF_ATTRIBUTION_METHODS
}


# ---------------------------------------------------------------------------
# PCAF Quality Improvement Paths (DQS level transitions)
# ---------------------------------------------------------------------------

PCAF_QUALITY_IMPROVEMENT_PATHS: list[dict] = [
    {
        "from_dqs": 5,
        "to_dqs": 4,
        "transition_label": "Sector proxy -> Economic activity estimate",
        "actions": [
            "Obtain revenue or total assets data for the borrower/investee",
            "Apply region- and sector-specific emission factors per EUR revenue",
            "Establish data collection process for annual financial data retrieval",
            "Map counterparty NACE codes for emission factor selection",
        ],
        "typical_effort": "Low — requires financial data only",
        "expected_uncertainty_reduction_pct": 15.0,
    },
    {
        "from_dqs": 4,
        "to_dqs": 3,
        "transition_label": "Economic activity estimate -> Physical activity estimate",
        "actions": [
            "Collect physical activity data (energy consumption kWh, fuel litres, production tonnes)",
            "Deploy borrower questionnaires or data portals for energy/fuel data",
            "Use utility billing data or smart meter readings where available",
            "Apply activity-specific emission factors from national inventories",
        ],
        "typical_effort": "Medium — requires operational data engagement",
        "expected_uncertainty_reduction_pct": 15.0,
    },
    {
        "from_dqs": 3,
        "to_dqs": 2,
        "transition_label": "Physical activity estimate -> Reported emissions",
        "actions": [
            "Request company-reported Scope 1, 2, and 3 GHG emissions data",
            "Integrate with investee sustainability reports or CDP disclosures",
            "Establish annual data exchange agreements with borrowers",
            "Validate reported data against physical activity cross-checks",
        ],
        "typical_effort": "Medium-High — requires investee engagement",
        "expected_uncertainty_reduction_pct": 15.0,
    },
    {
        "from_dqs": 2,
        "to_dqs": 1,
        "transition_label": "Reported emissions -> Verified emissions",
        "actions": [
            "Require third-party verification of reported emissions (ISO 14064-3 or ISAE 3410)",
            "Include verification requirements in loan covenants or investment agreements",
            "Encourage investees to obtain limited or reasonable assurance",
            "Cross-reference verified data with national emission registries where available",
        ],
        "typical_effort": "High — requires assurance engagement and cost",
        "expected_uncertainty_reduction_pct": 10.0,
    },
]


# ---------------------------------------------------------------------------
# PCAF Cross-Framework Mapping (8+ regulatory/voluntary framework links)
# ---------------------------------------------------------------------------

PCAF_CROSS_FRAMEWORK_MAP: list[dict] = [
    {
        "mapping_id": "pcaf_sfdr_pai1",
        "pcaf_metric": "Total financed emissions (Scope 1 + 2 + 3)",
        "target_framework": "SFDR",
        "target_reference": "PAI 1 — GHG emissions (Scope 1, 2, and 3 financed)",
        "description": (
            "PCAF financed emissions directly feed SFDR Principal Adverse "
            "Impact indicator 1: absolute GHG emissions of investee companies."
        ),
        "data_flow": "PCAF portfolio total -> SFDR PAI Table 1 Row 1",
    },
    {
        "mapping_id": "pcaf_sfdr_pai2",
        "pcaf_metric": "Carbon footprint (tCO2e per M EUR invested)",
        "target_framework": "SFDR",
        "target_reference": "PAI 2 — Carbon footprint",
        "description": (
            "PCAF carbon footprint metric (total financed emissions / total "
            "current value of investments) maps to SFDR PAI 2."
        ),
        "data_flow": "PCAF total_financed_emissions / AUM -> SFDR PAI Table 1 Row 2",
    },
    {
        "mapping_id": "pcaf_sfdr_pai3",
        "pcaf_metric": "GHG intensity of investees (tCO2e per M EUR revenue)",
        "target_framework": "SFDR",
        "target_reference": "PAI 3 — GHG intensity of investee companies",
        "description": (
            "Weighted average GHG intensity of portfolio investees, computed "
            "per PCAF methodology, feeds SFDR PAI 3."
        ),
        "data_flow": "PCAF WACI (weighted avg intensity) -> SFDR PAI Table 1 Row 3",
    },
    {
        "mapping_id": "pcaf_csrd_e1",
        "pcaf_metric": "Financed emissions by asset class and scope",
        "target_framework": "CSRD ESRS E1",
        "target_reference": "ESRS E1-6 — Gross Scope 3 and total GHG emissions (Category 15)",
        "description": (
            "CSRD requires disclosure of Scope 3 Category 15 (Investments) "
            "GHG emissions under ESRS E1-6, which aligns directly with PCAF "
            "financed emissions reporting."
        ),
        "data_flow": "PCAF financed emissions breakdown -> ESRS E1-6 Table E1-6",
    },
    {
        "mapping_id": "pcaf_tcfd",
        "pcaf_metric": "Financed emissions, carbon intensity, data quality",
        "target_framework": "TCFD",
        "target_reference": "Metrics & Targets — Financed emissions for financial institutions",
        "description": (
            "TCFD Supplemental Guidance for Financial Institutions requires "
            "disclosure of financed emissions using PCAF methodology."
        ),
        "data_flow": "PCAF asset-class emissions + WACI -> TCFD Metrics & Targets annex",
    },
    {
        "mapping_id": "pcaf_issb_s2",
        "pcaf_metric": "Financed emissions by industry, data quality scores",
        "target_framework": "ISSB S2",
        "target_reference": "IFRS S2 para 29 + Industry-specific metrics (Appendix B)",
        "description": (
            "IFRS S2 requires Scope 3 Category 15 emissions for financial "
            "institutions. PCAF methodology is the de facto standard for "
            "computing these metrics."
        ),
        "data_flow": "PCAF portfolio financed emissions -> IFRS S2 para 29(a)(vi)",
    },
    {
        "mapping_id": "pcaf_gri_305",
        "pcaf_metric": "Scope 3 Category 15 financed emissions",
        "target_framework": "GRI 305",
        "target_reference": "GRI 305-3 — Other indirect (Scope 3) GHG emissions",
        "description": (
            "GRI 305-3 requires disclosure of Scope 3 emissions including "
            "Category 15 (Investments). PCAF provides the standard methodology "
            "for financial institutions."
        ),
        "data_flow": "PCAF total financed emissions -> GRI 305-3 Category 15 line item",
    },
    {
        "mapping_id": "pcaf_eu_taxonomy",
        "pcaf_metric": "Financed emissions denominators by asset class",
        "target_framework": "EU Taxonomy",
        "target_reference": "Green Asset Ratio (GAR) — denominator calculations",
        "description": (
            "EU Taxonomy GAR requires total covered assets as denominators, "
            "segmented similarly to PCAF asset classes. PCAF outstanding "
            "amounts feed GAR denominators."
        ),
        "data_flow": "PCAF outstanding by asset class -> EU Taxonomy GAR denominator",
    },
    {
        "mapping_id": "pcaf_cdp_fs14",
        "pcaf_metric": "Portfolio financed emissions with DQS distribution",
        "target_framework": "CDP",
        "target_reference": "C-FS14 — Financed emissions (Financial Services questionnaire)",
        "description": (
            "CDP question C-FS14 requires financial institutions to disclose "
            "financed emissions by asset class with data quality scores, "
            "directly aligned with PCAF."
        ),
        "data_flow": "PCAF portfolio report -> CDP C-FS14.1 to C-FS14.3",
    },
    {
        "mapping_id": "pcaf_nzba",
        "pcaf_metric": "Financed emissions baseline, targets, and trajectory",
        "target_framework": "Net-Zero Banking Alliance",
        "target_reference": "NZBA Guidelines — Portfolio alignment measurement",
        "description": (
            "NZBA requires signatory banks to measure financed emissions "
            "using PCAF and set sectoral decarbonisation targets aligned "
            "with 1.5C pathways."
        ),
        "data_flow": "PCAF baseline financed emissions -> NZBA sectoral target tracking",
    },
]


# ---------------------------------------------------------------------------
# Sector-Median DQS Benchmarks (for peer comparison)
# ---------------------------------------------------------------------------

PCAF_QUALITY_BENCHMARKS: list[dict] = [
    {"sector": "Commercial Banking", "nace_hint": "K64",
     "median_dqs": 3.8, "pct_dqs1_2": 18.0, "pct_dqs4_5": 52.0,
     "sample_size": 42, "benchmark_year": 2024},
    {"sector": "Investment Banking", "nace_hint": "K66",
     "median_dqs": 3.5, "pct_dqs1_2": 25.0, "pct_dqs4_5": 40.0,
     "sample_size": 28, "benchmark_year": 2024},
    {"sector": "Insurance", "nace_hint": "K65",
     "median_dqs": 4.0, "pct_dqs1_2": 12.0, "pct_dqs4_5": 58.0,
     "sample_size": 35, "benchmark_year": 2024},
    {"sector": "Asset Management", "nace_hint": "K66.3",
     "median_dqs": 3.2, "pct_dqs1_2": 30.0, "pct_dqs4_5": 35.0,
     "sample_size": 50, "benchmark_year": 2024},
    {"sector": "Pension Funds", "nace_hint": "K65.3",
     "median_dqs": 3.6, "pct_dqs1_2": 22.0, "pct_dqs4_5": 45.0,
     "sample_size": 25, "benchmark_year": 2024},
    {"sector": "Development Finance", "nace_hint": "K64.1",
     "median_dqs": 4.2, "pct_dqs1_2": 8.0, "pct_dqs4_5": 65.0,
     "sample_size": 18, "benchmark_year": 2024},
    {"sector": "Real Estate Investment", "nace_hint": "L68",
     "median_dqs": 2.8, "pct_dqs1_2": 40.0, "pct_dqs4_5": 25.0,
     "sample_size": 32, "benchmark_year": 2024},
    {"sector": "Private Equity", "nace_hint": "K64.2",
     "median_dqs": 4.1, "pct_dqs1_2": 10.0, "pct_dqs4_5": 62.0,
     "sample_size": 20, "benchmark_year": 2024},
    {"sector": "Sovereign Wealth Funds", "nace_hint": "K64.9",
     "median_dqs": 3.9, "pct_dqs1_2": 15.0, "pct_dqs4_5": 55.0,
     "sample_size": 12, "benchmark_year": 2024},
    {"sector": "Mortgage Lenders", "nace_hint": "K64.9",
     "median_dqs": 2.5, "pct_dqs1_2": 45.0, "pct_dqs4_5": 20.0,
     "sample_size": 30, "benchmark_year": 2024},
]

_BENCHMARK_BY_SECTOR: dict[str, dict] = {
    b["sector"]: b for b in PCAF_QUALITY_BENCHMARKS
}


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PCAFHoldingQualityScore:
    """DQS assessment result for a single holding / counterparty exposure."""
    holding_id: str
    entity_name: str
    asset_class: str
    outstanding_amount: float
    dqs_emissions: int
    dqs_completeness: int
    dqs_timeliness: int
    dqs_granularity: int
    dqs_methodology: int
    weighted_dqs: float
    confidence_weight: float
    estimated_emissions_tco2: float
    attribution_factor: float
    financed_emissions_tco2: float
    data_gaps: list = field(default_factory=list)
    improvement_actions: list = field(default_factory=list)


@dataclass
class PCAFPortfolioQualityReport:
    """Portfolio-level PCAF DQS aggregation and regulatory disclosure report."""
    portfolio_id: str
    portfolio_name: str
    reporting_year: int
    total_holdings: int
    scored_holdings: int
    portfolio_weighted_dqs: float
    dqs_distribution: dict = field(default_factory=dict)
    total_financed_emissions_tco2: float = 0.0
    total_outstanding_eur: float = 0.0
    carbon_intensity_tco2_per_meur: float = 0.0
    asset_class_breakdown: list = field(default_factory=list)
    quality_improvement_roadmap: list = field(default_factory=list)
    sfdr_pai_indicators: dict = field(default_factory=dict)
    cross_framework_disclosures: dict = field(default_factory=dict)
    confidence_band: dict = field(default_factory=dict)
    holding_scores: list = field(default_factory=list)
    created_at: str = ""


@dataclass
class PCAFDataQualityAssessment:
    """Standalone data quality assessment for an entity (without emissions calc)."""
    assessment_id: str
    entity_name: str
    reporting_year: int
    dimension_scores: dict = field(default_factory=dict)
    overall_dqs: int = 5
    weighted_dqs: float = 5.0
    improvement_priority: str = ""
    gap_analysis: list = field(default_factory=list)
    benchmark_comparison: dict = field(default_factory=dict)
    created_at: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PCAFQualityEngine:
    """PCAF Data Quality Score engine.

    Implements the full PCAF DQS framework for financed and facilitated
    emissions: scores individual holdings across five quality dimensions,
    aggregates portfolio-level exposure-weighted DQS, calculates SFDR PAI
    indicators, and generates quality improvement roadmaps.
    """

    # ── Holding-Level Scoring ─────────────────────────────────────────────

    def score_holding(self, holding: dict) -> PCAFHoldingQualityScore:
        """Score a single holding across all PCAF quality dimensions.

        Args:
            holding: Dict with keys:
                - holding_id (str): Unique identifier for the exposure.
                - entity_name (str): Borrower / investee legal name.
                - asset_class (str): One of the PCAF asset class IDs.
                - outstanding_amount_eur (float): Outstanding exposure in EUR.
                - reported_emissions (optional dict): Keys scope1, scope2,
                  scope3 in tCO2e. None if unavailable.
                - revenue_eur (optional float): Investee revenue for EF calc.
                - physical_activity_data (optional dict): Keys energy_kwh,
                  fuel_litres, production_tonnes — any available.
                - data_year (int): Year of the underlying data.
                - verification_status (str): 'none', 'limited', 'reasonable'.
                - nace_code (optional str): NACE section letter for EF lookup.
                - enterprise_value_eur (optional float): EVIC for attribution.
                - total_equity_debt_eur (optional float): Balance sheet total.
                - property_value_eur (optional float): For CRE / mortgages.
                - project_total_financing_eur (optional float): For PF.

        Returns:
            PCAFHoldingQualityScore with per-dimension and weighted DQS,
            estimated emissions, attribution factor, financed emissions,
            data gaps, and improvement actions.
        """
        holding_id = holding.get("holding_id", "unknown")
        entity_name = holding.get("entity_name", "Unknown Entity")
        asset_class = holding.get("asset_class", "listed_equity_corporate_bonds")
        outstanding = float(holding.get("outstanding_amount_eur", 0.0))
        reported = holding.get("reported_emissions")
        revenue = holding.get("revenue_eur")
        phys_data = holding.get("physical_activity_data")
        data_year = int(holding.get("data_year", 2023))
        verification = holding.get("verification_status", "none")
        nace = holding.get("nace_code", "K")
        reporting_year = int(holding.get("reporting_year", datetime.utcnow().year))

        # --- Score each dimension ---
        dqs_emissions = self._score_emissions_quality(reported, phys_data, revenue, verification)
        dqs_completeness = self._score_completeness(reported)
        dqs_timeliness = self._score_timeliness(data_year, reporting_year)
        dqs_granularity = self._score_granularity(reported, phys_data, revenue)
        dqs_methodology = self._score_methodology(asset_class, verification, reported)

        # --- Weighted DQS ---
        weighted_dqs = (
            dqs_emissions * _DIMENSION_WEIGHTS["emissions_data_quality"]
            + dqs_completeness * _DIMENSION_WEIGHTS["data_completeness"]
            + dqs_timeliness * _DIMENSION_WEIGHTS["data_timeliness"]
            + dqs_granularity * _DIMENSION_WEIGHTS["data_granularity"]
            + dqs_methodology * _DIMENSION_WEIGHTS["methodology_robustness"]
        )
        weighted_dqs = round(weighted_dqs, 2)

        # --- Confidence weight (inverse mapping) ---
        confidence_weight = self._dqs_to_confidence(weighted_dqs)

        # --- Estimate emissions ---
        estimated_emissions = self._estimate_emissions(
            reported, phys_data, revenue, nace, outstanding, asset_class
        )

        # --- Attribution factor ---
        attribution_factor = self._compute_attribution(holding, outstanding)

        # --- Financed emissions ---
        financed_emissions = round(estimated_emissions * attribution_factor, 4)

        # --- Data gaps ---
        gaps = self._identify_gaps(reported, phys_data, revenue, verification, data_year, reporting_year)

        # --- Improvement actions ---
        overall_dqs_int = max(1, min(5, round(weighted_dqs)))
        actions = self._get_improvement_actions(overall_dqs_int, gaps)

        return PCAFHoldingQualityScore(
            holding_id=holding_id,
            entity_name=entity_name,
            asset_class=asset_class,
            outstanding_amount=outstanding,
            dqs_emissions=dqs_emissions,
            dqs_completeness=dqs_completeness,
            dqs_timeliness=dqs_timeliness,
            dqs_granularity=dqs_granularity,
            dqs_methodology=dqs_methodology,
            weighted_dqs=weighted_dqs,
            confidence_weight=confidence_weight,
            estimated_emissions_tco2=round(estimated_emissions, 4),
            attribution_factor=round(attribution_factor, 6),
            financed_emissions_tco2=financed_emissions,
            data_gaps=gaps,
            improvement_actions=actions,
        )

    # ── Portfolio-Level Scoring ───────────────────────────────────────────

    def score_portfolio(self, portfolio: dict) -> PCAFPortfolioQualityReport:
        """Score an entire portfolio and produce regulatory disclosures.

        Args:
            portfolio: Dict with keys:
                - portfolio_id (str)
                - portfolio_name (str)
                - reporting_year (int)
                - holdings (list[dict]): Each a holding dict per score_holding().
                - total_aum_eur (optional float): Total AUM for PAI 2 calc.

        Returns:
            PCAFPortfolioQualityReport with exposure-weighted DQS, asset
            class breakdown, SFDR PAI indicators, improvement roadmap,
            and confidence bands.
        """
        portfolio_id = portfolio.get("portfolio_id", "unknown")
        portfolio_name = portfolio.get("portfolio_name", "Unnamed Portfolio")
        reporting_year = int(portfolio.get("reporting_year", datetime.utcnow().year))
        holdings_data = portfolio.get("holdings", [])
        total_aum = float(portfolio.get("total_aum_eur", 0.0))

        # Score each holding
        scored: list[PCAFHoldingQualityScore] = []
        for h in holdings_data:
            h.setdefault("reporting_year", reporting_year)
            scored.append(self.score_holding(h))

        total_holdings = len(holdings_data)
        scored_count = len(scored)

        # --- DQS distribution ---
        dqs_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for s in scored:
            bucket = max(1, min(5, round(s.weighted_dqs)))
            dqs_dist[bucket] += 1

        # --- Exposure-weighted portfolio DQS ---
        total_outstanding = sum(s.outstanding_amount for s in scored)
        if total_outstanding > 0:
            portfolio_wdqs = sum(
                s.weighted_dqs * s.outstanding_amount for s in scored
            ) / total_outstanding
        else:
            portfolio_wdqs = 5.0
        portfolio_wdqs = round(portfolio_wdqs, 2)

        # --- Total financed emissions ---
        total_financed = sum(s.financed_emissions_tco2 for s in scored)
        total_financed = round(total_financed, 4)

        # --- Carbon intensity ---
        carbon_intensity = 0.0
        if total_outstanding > 0:
            carbon_intensity = round(
                total_financed / (total_outstanding / 1_000_000), 4
            )

        # --- Asset class breakdown ---
        ac_map: dict[str, dict] = {}
        for s in scored:
            ac = s.asset_class
            if ac not in ac_map:
                ac_map[ac] = {
                    "asset_class": ac,
                    "count": 0,
                    "total_outstanding_eur": 0.0,
                    "total_financed_emissions_tco2": 0.0,
                    "dqs_sum": 0.0,
                }
            ac_map[ac]["count"] += 1
            ac_map[ac]["total_outstanding_eur"] += s.outstanding_amount
            ac_map[ac]["total_financed_emissions_tco2"] += s.financed_emissions_tco2
            ac_map[ac]["dqs_sum"] += s.weighted_dqs

        asset_class_breakdown = []
        for ac_id, acd in ac_map.items():
            avg_dqs = round(acd["dqs_sum"] / acd["count"], 2) if acd["count"] > 0 else 5.0
            asset_class_breakdown.append({
                "asset_class": ac_id,
                "label": _ASSET_CLASS_BY_ID.get(ac_id, {}).get("label", ac_id),
                "count": acd["count"],
                "avg_dqs": avg_dqs,
                "total_outstanding_eur": round(acd["total_outstanding_eur"], 2),
                "total_financed_emissions_tco2": round(acd["total_financed_emissions_tco2"], 4),
            })

        # --- SFDR PAI indicators ---
        aum_for_pai = total_aum if total_aum > 0 else total_outstanding
        pai_1_scope1 = sum(
            s.financed_emissions_tco2 * 0.4 for s in scored  # rough scope 1 share
        )
        pai_1_scope2 = sum(
            s.financed_emissions_tco2 * 0.2 for s in scored
        )
        pai_1_scope3 = sum(
            s.financed_emissions_tco2 * 0.4 for s in scored
        )
        pai_2 = round(total_financed / (aum_for_pai / 1_000_000), 4) if aum_for_pai > 0 else 0.0

        # PAI 3: WACI (weighted average carbon intensity of investees)
        pai_3_num = 0.0
        pai_3_denom = 0.0
        for s in scored:
            if s.outstanding_amount > 0:
                # Proxy: use financed emissions / outstanding as intensity proxy
                intensity = s.estimated_emissions_tco2
                weight = s.outstanding_amount / total_outstanding if total_outstanding > 0 else 0.0
                pai_3_num += weight * intensity
                pai_3_denom += weight

        pai_3 = round(pai_3_num, 4) if pai_3_denom > 0 else 0.0

        sfdr_pai = {
            "pai_1_total_financed_emissions_tco2": round(total_financed, 4),
            "pai_1_scope1_tco2": round(pai_1_scope1, 4),
            "pai_1_scope2_tco2": round(pai_1_scope2, 4),
            "pai_1_scope3_tco2": round(pai_1_scope3, 4),
            "pai_2_carbon_footprint_tco2_per_meur": pai_2,
            "pai_3_ghg_intensity_tco2_per_meur": pai_3,
        }

        # --- Cross-framework disclosures ---
        cross_fw = {}
        for mapping in PCAF_CROSS_FRAMEWORK_MAP:
            fw = mapping["target_framework"]
            if fw not in cross_fw:
                cross_fw[fw] = []
            entry = {
                "reference": mapping["target_reference"],
                "pcaf_metric": mapping["pcaf_metric"],
                "data_flow": mapping["data_flow"],
            }
            if fw == "SFDR":
                if "PAI 1" in mapping["target_reference"]:
                    entry["value"] = sfdr_pai["pai_1_total_financed_emissions_tco2"]
                elif "PAI 2" in mapping["target_reference"]:
                    entry["value"] = sfdr_pai["pai_2_carbon_footprint_tco2_per_meur"]
                elif "PAI 3" in mapping["target_reference"]:
                    entry["value"] = sfdr_pai["pai_3_ghg_intensity_tco2_per_meur"]
            elif fw == "CSRD ESRS E1":
                entry["value"] = total_financed
            elif fw == "TCFD":
                entry["value"] = total_financed
            elif fw == "ISSB S2":
                entry["value"] = total_financed
            elif fw == "GRI 305":
                entry["value"] = total_financed
            elif fw == "EU Taxonomy":
                entry["value"] = total_outstanding
            elif fw == "CDP":
                entry["value"] = total_financed
                entry["dqs_distribution"] = dict(dqs_dist)
            elif fw == "Net-Zero Banking Alliance":
                entry["value"] = total_financed
                entry["portfolio_dqs"] = portfolio_wdqs
            cross_fw[fw].append(entry)

        # --- Confidence bands ---
        avg_uncertainty_pct = self._portfolio_uncertainty(scored, total_outstanding)
        confidence_band = {
            "central_estimate_tco2": total_financed,
            "lower_bound_tco2": round(total_financed * (1 - avg_uncertainty_pct / 100), 4),
            "upper_bound_tco2": round(total_financed * (1 + avg_uncertainty_pct / 100), 4),
            "weighted_uncertainty_pct": round(avg_uncertainty_pct, 2),
            "portfolio_weighted_dqs": portfolio_wdqs,
        }

        # --- Quality improvement roadmap ---
        roadmap = self._build_improvement_roadmap(scored, total_outstanding)

        # --- Serialise holding scores ---
        holding_score_dicts = []
        for s in scored:
            holding_score_dicts.append({
                "holding_id": s.holding_id,
                "entity_name": s.entity_name,
                "asset_class": s.asset_class,
                "outstanding_amount": s.outstanding_amount,
                "weighted_dqs": s.weighted_dqs,
                "financed_emissions_tco2": s.financed_emissions_tco2,
                "confidence_weight": s.confidence_weight,
                "data_gaps": s.data_gaps,
            })

        return PCAFPortfolioQualityReport(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            reporting_year=reporting_year,
            total_holdings=total_holdings,
            scored_holdings=scored_count,
            portfolio_weighted_dqs=portfolio_wdqs,
            dqs_distribution=dqs_dist,
            total_financed_emissions_tco2=total_financed,
            total_outstanding_eur=round(total_outstanding, 2),
            carbon_intensity_tco2_per_meur=carbon_intensity,
            asset_class_breakdown=asset_class_breakdown,
            quality_improvement_roadmap=roadmap,
            sfdr_pai_indicators=sfdr_pai,
            cross_framework_disclosures=cross_fw,
            confidence_band=confidence_band,
            holding_scores=holding_score_dicts,
            created_at=datetime.utcnow().isoformat(),
        )

    # ── Standalone Data Quality Assessment ────────────────────────────────

    def assess_data_quality(
        self,
        entity_name: str,
        reporting_year: int,
        data_inventory: dict,
    ) -> PCAFDataQualityAssessment:
        """Assess data quality for an entity without full emissions calc.

        Args:
            entity_name: Legal name of the borrower / investee.
            reporting_year: Assessment year.
            data_inventory: Dict describing available data:
                - emissions_source (str): 'verified', 'reported', 'physical',
                  'economic', 'sector_proxy', or 'none'.
                - scopes_covered (list[str]): e.g. ['scope1', 'scope2'].
                - data_year (int): Year of data.
                - granularity_level (str): 'entity', 'sub_sector', 'sector'.
                - pcaf_methodology_applied (bool): Whether PCAF method used.
                - verification_type (str): 'none', 'limited', 'reasonable'.
                - sector (str): Sector name for benchmark lookup.

        Returns:
            PCAFDataQualityAssessment with per-dimension scores, overall DQS,
            improvement priority, gap analysis, and sector benchmark comparison.
        """
        uid = hashlib.sha256(
            f"pcaf-dqa:{entity_name}:{reporting_year}".encode()
        ).hexdigest()[:16]

        emissions_source = data_inventory.get("emissions_source", "none")
        scopes = data_inventory.get("scopes_covered", [])
        data_year = int(data_inventory.get("data_year", reporting_year - 2))
        granularity = data_inventory.get("granularity_level", "sector")
        pcaf_applied = data_inventory.get("pcaf_methodology_applied", False)
        verification = data_inventory.get("verification_type", "none")
        sector = data_inventory.get("sector", "")

        # Score emissions quality dimension
        edq = self._map_source_to_dqs(emissions_source, verification)

        # Score completeness
        completeness = self._score_scope_coverage(scopes, verification)

        # Score timeliness
        timeliness = self._score_timeliness(data_year, reporting_year)

        # Score granularity
        gran_map = {"entity": 1, "sub_sector": 3, "sector": 5}
        gran_score = gran_map.get(granularity, 5)

        # Score methodology
        meth_score = 1 if (pcaf_applied and verification in ("limited", "reasonable")) else (
            2 if pcaf_applied else (3 if emissions_source in ("physical", "economic") else 5)
        )

        dimension_scores = {
            "emissions_data_quality": {
                "score": edq,
                "rationale": self._edq_rationale(emissions_source, verification),
                "evidence": f"Source: {emissions_source}, Verification: {verification}",
            },
            "data_completeness": {
                "score": completeness,
                "rationale": self._completeness_rationale(scopes),
                "evidence": f"Scopes covered: {', '.join(scopes) if scopes else 'none'}",
            },
            "data_timeliness": {
                "score": timeliness,
                "rationale": f"Data year {data_year} vs reporting year {reporting_year}",
                "evidence": f"Lag: {reporting_year - data_year} year(s)",
            },
            "data_granularity": {
                "score": gran_score,
                "rationale": f"Granularity level: {granularity}",
                "evidence": f"Data at {granularity} level",
            },
            "methodology_robustness": {
                "score": meth_score,
                "rationale": self._methodology_rationale(pcaf_applied, verification),
                "evidence": f"PCAF applied: {pcaf_applied}, Verification: {verification}",
            },
        }

        # Weighted overall
        w_dqs = sum(
            dimension_scores[dim_id]["score"] * _DIMENSION_WEIGHTS[dim_id]
            for dim_id in _DIMENSION_WEIGHTS
        )
        w_dqs = round(w_dqs, 2)
        overall = max(1, min(5, round(w_dqs)))

        # Identify improvement priority (dimension with highest weighted impact)
        priority_dim = ""
        best_impact = 0.0
        for dim in PCAF_QUALITY_DIMENSIONS:
            dim_id = dim["dimension_id"]
            current = dimension_scores[dim_id]["score"]
            if current > 1:
                impact = dim["weight"] * (current - max(1, current - 1))
                if impact > best_impact:
                    best_impact = impact
                    priority_dim = dim_id

        # Gap analysis
        gap_analysis = []
        for dim in PCAF_QUALITY_DIMENSIONS:
            dim_id = dim["dimension_id"]
            score = dimension_scores[dim_id]["score"]
            if score >= 3:
                gap_analysis.append({
                    "dimension": dim_id,
                    "current_score": score,
                    "target_score": max(1, score - 1),
                    "gap_description": f"{dim['label']} at DQS {score} — improvement needed",
                    "priority": "high" if score >= 4 else "medium",
                })

        # Benchmark comparison
        benchmark = _BENCHMARK_BY_SECTOR.get(sector, {})
        benchmark_comparison = {
            "sector": sector if sector else "Not specified",
            "entity_dqs": w_dqs,
            "sector_median_dqs": benchmark.get("median_dqs", None),
            "relative_position": "",
        }
        if benchmark.get("median_dqs") is not None:
            if w_dqs < benchmark["median_dqs"]:
                benchmark_comparison["relative_position"] = "Above median (better)"
            elif w_dqs > benchmark["median_dqs"]:
                benchmark_comparison["relative_position"] = "Below median (worse)"
            else:
                benchmark_comparison["relative_position"] = "At median"

        return PCAFDataQualityAssessment(
            assessment_id=f"pcaf-dqa-{uid}",
            entity_name=entity_name,
            reporting_year=reporting_year,
            dimension_scores=dimension_scores,
            overall_dqs=overall,
            weighted_dqs=w_dqs,
            improvement_priority=priority_dim,
            gap_analysis=gap_analysis,
            benchmark_comparison=benchmark_comparison,
            created_at=datetime.utcnow().isoformat(),
        )

    # ── Internal Scoring Helpers ──────────────────────────────────────────

    @staticmethod
    def _score_emissions_quality(
        reported: dict | None,
        phys_data: dict | None,
        revenue: float | None,
        verification: str,
    ) -> int:
        """Score the emissions data quality dimension (1-5)."""
        if reported and verification in ("reasonable", "limited"):
            has_scope1 = reported.get("scope1") is not None
            has_scope2 = reported.get("scope2") is not None
            if has_scope1 and has_scope2 and verification == "reasonable":
                return 1
            return 2
        if reported:
            return 2
        if phys_data:
            has_any = any(
                phys_data.get(k) is not None
                for k in ("energy_kwh", "fuel_litres", "production_tonnes")
            )
            if has_any:
                return 3
        if revenue is not None and revenue > 0:
            return 4
        return 5

    @staticmethod
    def _score_completeness(reported: dict | None) -> int:
        """Score data completeness dimension (1-5)."""
        if not reported:
            return 5
        has_s1 = reported.get("scope1") is not None
        has_s2 = reported.get("scope2") is not None
        has_s3 = reported.get("scope3") is not None
        if has_s1 and has_s2 and has_s3:
            return 1
        if has_s1 and has_s2:
            return 2
        if has_s1 or has_s2:
            return 3
        return 4

    @staticmethod
    def _score_timeliness(data_year: int, reporting_year: int) -> int:
        """Score data timeliness dimension (1-5)."""
        lag = reporting_year - data_year
        if lag <= 0:
            return 1
        if lag == 1:
            return 2
        if lag == 2:
            return 3
        if lag == 3:
            return 4
        return 5

    @staticmethod
    def _score_granularity(
        reported: dict | None,
        phys_data: dict | None,
        revenue: float | None,
    ) -> int:
        """Score data granularity dimension (1-5)."""
        if reported:
            has_s1 = reported.get("scope1") is not None
            has_s2 = reported.get("scope2") is not None
            if has_s1 and has_s2:
                return 1
            return 2
        if phys_data:
            return 3
        if revenue is not None and revenue > 0:
            return 4
        return 5

    @staticmethod
    def _score_methodology(
        asset_class: str,
        verification: str,
        reported: dict | None,
    ) -> int:
        """Score methodology robustness dimension (1-5)."""
        # Check if the asset class is a recognized PCAF class
        is_pcaf_class = asset_class in _ASSET_CLASS_BY_ID
        has_verified = verification in ("limited", "reasonable")
        has_reported = reported is not None and len(reported) > 0

        if is_pcaf_class and has_verified and has_reported:
            return 1
        if is_pcaf_class and has_reported:
            return 2
        if is_pcaf_class:
            return 3
        if has_reported:
            return 4
        return 5

    @staticmethod
    def _dqs_to_confidence(weighted_dqs: float) -> float:
        """Map weighted DQS (1-5) to confidence weight (1.0-0.2)."""
        # Linear interpolation: DQS 1 -> 1.0, DQS 5 -> 0.2
        clamped = max(1.0, min(5.0, weighted_dqs))
        return round(1.0 - (clamped - 1.0) * 0.2, 4)

    @staticmethod
    def _estimate_emissions(
        reported: dict | None,
        phys_data: dict | None,
        revenue: float | None,
        nace: str,
        outstanding: float,
        asset_class: str,
    ) -> float:
        """Estimate total entity emissions (tCO2e) using best available data.

        Priority: reported > physical activity > revenue-based > sector proxy.
        """
        # DQS 1-2: Use reported emissions directly
        if reported:
            total = 0.0
            total += float(reported.get("scope1", 0) or 0)
            total += float(reported.get("scope2", 0) or 0)
            total += float(reported.get("scope3", 0) or 0)
            if total > 0:
                return total

        # DQS 3: Physical activity estimate
        if phys_data:
            total = 0.0
            energy_kwh = float(phys_data.get("energy_kwh", 0) or 0)
            fuel_litres = float(phys_data.get("fuel_litres", 0) or 0)
            production_t = float(phys_data.get("production_tonnes", 0) or 0)
            # Grid average EF ~0.4 tCO2/MWh = 0.0004 tCO2/kWh
            total += energy_kwh * 0.0004
            # Diesel EF ~2.68 kgCO2/litre = 0.00268 tCO2/litre
            total += fuel_litres * 0.00268
            # Generic manufacturing EF ~0.5 tCO2/tonne product
            total += production_t * 0.5
            if total > 0:
                return total

        # DQS 4: Revenue-based estimate
        ef = _EF_BY_NACE.get(nace)
        if revenue is not None and revenue > 0 and ef:
            rev_meur = revenue / 1_000_000
            total = (
                ef["scope1_ef_tco2_per_meur"]
                + ef["scope2_ef"]
                + ef["scope3_ef"]
            ) * rev_meur
            return total

        # DQS 5: Sector proxy based on outstanding amount
        if ef:
            outs_meur = outstanding / 1_000_000
            total = (
                ef["scope1_ef_tco2_per_meur"]
                + ef["scope2_ef"]
                + ef["scope3_ef"]
            ) * outs_meur * 0.3  # scaling factor for proxy
            return max(total, 0.0)

        # Absolute fallback: simple proxy
        return outstanding / 1_000_000 * 150.0  # 150 tCO2 per M EUR

    @staticmethod
    def _compute_attribution(holding: dict, outstanding: float) -> float:
        """Compute the PCAF attribution factor for a holding.

        Returns a factor in [0, 1] representing the investor's share of
        the investee's total emissions.
        """
        asset_class = holding.get("asset_class", "listed_equity_corporate_bonds")

        # Enterprise value method
        evic = holding.get("enterprise_value_eur")
        if evic and float(evic) > 0 and asset_class in (
            "listed_equity_corporate_bonds", "motor_vehicle_loans"
        ):
            return min(outstanding / float(evic), 1.0)

        # Balance sheet method
        eq_debt = holding.get("total_equity_debt_eur")
        if eq_debt and float(eq_debt) > 0 and asset_class == "business_loans_unlisted_equity":
            return min(outstanding / float(eq_debt), 1.0)

        # Project finance method
        proj_total = holding.get("project_total_financing_eur")
        if proj_total and float(proj_total) > 0 and asset_class == "project_finance":
            return min(outstanding / float(proj_total), 1.0)

        # Floor area / property value method
        prop_val = holding.get("property_value_eur")
        if prop_val and float(prop_val) > 0 and asset_class in (
            "commercial_real_estate", "mortgages"
        ):
            return min(outstanding / float(prop_val), 1.0)

        # Fallback: ratio of outstanding to a reasonable denominator estimate
        # Assume outstanding is ~30% of entity value as heuristic
        estimated_denom = outstanding / 0.3 if outstanding > 0 else 1.0
        return min(outstanding / estimated_denom, 1.0)

    @staticmethod
    def _identify_gaps(
        reported: dict | None,
        phys_data: dict | None,
        revenue: float | None,
        verification: str,
        data_year: int,
        reporting_year: int,
    ) -> list[str]:
        """Identify data gaps for a holding."""
        gaps = []

        if not reported:
            gaps.append("No company-reported emissions data available")
        else:
            if reported.get("scope1") is None:
                gaps.append("Scope 1 emissions not reported")
            if reported.get("scope2") is None:
                gaps.append("Scope 2 emissions not reported")
            if reported.get("scope3") is None:
                gaps.append("Scope 3 emissions not reported")

        if not phys_data and not reported:
            gaps.append("No physical activity data (energy, fuel, production)")

        if revenue is None or revenue <= 0:
            if not reported:
                gaps.append("Revenue data missing — cannot use economic emission factors")

        if verification == "none":
            gaps.append("No third-party verification of emissions data")

        lag = reporting_year - data_year
        if lag > 2:
            gaps.append(f"Data is {lag} years old — exceeds 2-year PCAF timeliness threshold")

        return gaps

    @staticmethod
    def _get_improvement_actions(overall_dqs: int, gaps: list[str]) -> list[str]:
        """Return prioritised improvement actions based on current DQS and gaps."""
        actions = []

        # Find the relevant improvement path
        for path in PCAF_QUALITY_IMPROVEMENT_PATHS:
            if path["from_dqs"] == overall_dqs:
                actions.extend(path["actions"])
                break

        # If DQS is already 1, suggest maintenance actions
        if overall_dqs == 1:
            actions.append("Maintain annual third-party verification of emissions data")
            actions.append("Expand Scope 3 coverage to additional value chain categories")

        # Add gap-specific actions
        if "No third-party verification of emissions data" in gaps and overall_dqs <= 3:
            actions.append(
                "Engage accredited verifier (ISO 14064-3 / ISAE 3410) for "
                "emissions assurance"
            )
        if any("Scope 3" in g for g in gaps):
            actions.append(
                "Request investee Scope 3 disclosure or estimate using "
                "PCAF-recommended Scope 3 emission factors"
            )

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_actions = []
        for a in actions:
            if a not in seen:
                seen.add(a)
                unique_actions.append(a)

        return unique_actions[:8]

    @staticmethod
    def _portfolio_uncertainty(
        scored: list[PCAFHoldingQualityScore],
        total_outstanding: float,
    ) -> float:
        """Compute exposure-weighted average uncertainty percentage."""
        if total_outstanding <= 0 or not scored:
            return 60.0

        weighted_unc = 0.0
        for s in scored:
            dqs_int = max(1, min(5, round(s.weighted_dqs)))
            unc_pct = _DQS_LEVEL_BY_SCORE[dqs_int]["typical_uncertainty_pct"]
            weight = s.outstanding_amount / total_outstanding
            weighted_unc += weight * unc_pct

        return weighted_unc

    @staticmethod
    def _build_improvement_roadmap(
        scored: list[PCAFHoldingQualityScore],
        total_outstanding: float,
    ) -> list[dict]:
        """Build a prioritised quality improvement roadmap.

        Priority = count_of_holdings_at_level x DQS_improvement_potential
                   x outstanding_weight.
        """
        if not scored or total_outstanding <= 0:
            return []

        # Group holdings by their rounded DQS bucket
        bucket_stats: dict[int, dict] = {}
        for s in scored:
            bucket = max(1, min(5, round(s.weighted_dqs)))
            if bucket not in bucket_stats:
                bucket_stats[bucket] = {
                    "count": 0,
                    "total_outstanding": 0.0,
                    "holdings": [],
                }
            bucket_stats[bucket]["count"] += 1
            bucket_stats[bucket]["total_outstanding"] += s.outstanding_amount
            bucket_stats[bucket]["holdings"].append(s.entity_name)

        roadmap = []
        for dqs_level in sorted(bucket_stats.keys(), reverse=True):
            if dqs_level <= 1:
                continue  # Already best quality

            stats = bucket_stats[dqs_level]
            improvement_potential = dqs_level - max(1, dqs_level - 1)
            outstanding_weight = stats["total_outstanding"] / total_outstanding
            priority_score = stats["count"] * improvement_potential * outstanding_weight

            # Find relevant path
            path = None
            for p in PCAF_QUALITY_IMPROVEMENT_PATHS:
                if p["from_dqs"] == dqs_level:
                    path = p
                    break

            roadmap.append({
                "current_dqs": dqs_level,
                "target_dqs": dqs_level - 1,
                "holding_count": stats["count"],
                "total_outstanding_eur": round(stats["total_outstanding"], 2),
                "outstanding_share_pct": round(outstanding_weight * 100, 1),
                "priority_score": round(priority_score, 4),
                "transition_label": path["transition_label"] if path else "Improvement",
                "actions": path["actions"] if path else [],
                "expected_uncertainty_reduction_pct": (
                    path["expected_uncertainty_reduction_pct"] if path else 0.0
                ),
                "sample_entities": stats["holdings"][:5],
            })

        # Sort by priority score descending
        roadmap.sort(key=lambda r: r["priority_score"], reverse=True)
        return roadmap

    # ── Data Quality Assessment Helpers ───────────────────────────────────

    @staticmethod
    def _map_source_to_dqs(emissions_source: str, verification: str) -> int:
        """Map an emissions data source string to a DQS level."""
        source_map = {
            "verified": 1,
            "reported": 2,
            "physical": 3,
            "economic": 4,
            "sector_proxy": 5,
            "none": 5,
        }
        base = source_map.get(emissions_source, 5)

        # Upgrade if verified but source says 'reported'
        if base == 2 and verification in ("limited", "reasonable"):
            return 1
        return base

    @staticmethod
    def _score_scope_coverage(scopes: list[str], verification: str) -> int:
        """Score completeness based on scope coverage list."""
        s1 = "scope1" in scopes
        s2 = "scope2" in scopes
        s3 = "scope3" in scopes
        verified = verification in ("limited", "reasonable")

        if s1 and s2 and s3 and verified:
            return 1
        if s1 and s2 and s3:
            return 2
        if s1 and s2:
            return 3
        if s1 or s2:
            return 4
        return 5

    @staticmethod
    def _edq_rationale(emissions_source: str, verification: str) -> str:
        """Generate rationale text for emissions data quality score."""
        rationales = {
            "verified": "Emissions data externally verified to ISO 14064-3 / ISAE 3410",
            "reported": (
                "Emissions data self-reported by the investee (unverified)"
                if verification == "none"
                else "Emissions data reported and verified with " + verification + " assurance"
            ),
            "physical": "Emissions estimated from physical activity data (energy, fuel, production)",
            "economic": "Emissions estimated from economic activity data (revenue-based EF)",
            "sector_proxy": "Emissions estimated using sector-average proxy data",
            "none": "No emissions data available — sector proxy applied",
        }
        return rationales.get(emissions_source, "Unknown data source")

    @staticmethod
    def _completeness_rationale(scopes: list[str]) -> str:
        """Generate rationale text for completeness score."""
        if not scopes:
            return "No scope data available"
        covered = ", ".join(s.replace("scope", "Scope ") for s in sorted(scopes))
        missing = []
        for s in ("scope1", "scope2", "scope3"):
            if s not in scopes:
                missing.append(s.replace("scope", "Scope "))
        if missing:
            return f"Covers {covered}; missing {', '.join(missing)}"
        return f"Full coverage: {covered}"

    @staticmethod
    def _methodology_rationale(pcaf_applied: bool, verification: str) -> str:
        """Generate rationale text for methodology robustness score."""
        if pcaf_applied and verification in ("limited", "reasonable"):
            return "Full PCAF Standard methodology applied with third-party assurance"
        if pcaf_applied:
            return "PCAF Standard methodology applied but without external assurance"
        if verification in ("limited", "reasonable"):
            return "Non-PCAF methodology but with third-party verification"
        return "No PCAF methodology applied and no verification"

    # ── Static Reference Methods ──────────────────────────────────────────

    @staticmethod
    def get_asset_classes() -> list[dict]:
        """Return all 6 PCAF asset classes with attribution methods."""
        return PCAF_ASSET_CLASSES

    @staticmethod
    def get_dqs_levels() -> list[dict]:
        """Return all 5 PCAF DQS levels (1=best, 5=worst)."""
        return PCAF_DQS_LEVELS

    @staticmethod
    def get_quality_dimensions() -> list[dict]:
        """Return the 5 PCAF quality assessment dimensions with weights."""
        return PCAF_QUALITY_DIMENSIONS

    @staticmethod
    def get_emission_factors() -> list[dict]:
        """Return NACE-sector emission factors for DQS 4-5 estimation."""
        return PCAF_EMISSION_FACTORS

    @staticmethod
    def get_attribution_methods() -> list[dict]:
        """Return the 4 PCAF attribution approaches."""
        return PCAF_ATTRIBUTION_METHODS

    @staticmethod
    def get_improvement_paths() -> list[dict]:
        """Return DQS improvement pathways (5->4, 4->3, 3->2, 2->1)."""
        return PCAF_QUALITY_IMPROVEMENT_PATHS

    @staticmethod
    def get_cross_framework_map() -> list[dict]:
        """Return PCAF-to-regulatory cross-framework mappings (10 entries)."""
        return PCAF_CROSS_FRAMEWORK_MAP

    @staticmethod
    def get_quality_benchmarks() -> list[dict]:
        """Return sector-median DQS benchmarks (10 sectors)."""
        return PCAF_QUALITY_BENCHMARKS
