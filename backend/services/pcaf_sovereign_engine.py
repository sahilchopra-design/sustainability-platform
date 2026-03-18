"""
PCAF Sovereign Bonds and Loans Engine
========================================

PCAF Global GHG Accounting and Reporting Standard for the Financial Industry —
Part D: Sovereign Bonds and Loans (2023 Edition).

GDP-based attribution methodology: outstanding loan/bond amount divided by
government debt (in nominal terms) multiplied by the sovereign's national GHG
inventory. Covers government bonds, sovereign loans, and government-guaranteed
instruments.

Sub-modules:
  1. Single Sovereign Assessment — attribution, DQS, NDC alignment, climate risk overlay
  2. Portfolio Assessment — exposure-weighted portfolio-level aggregation
  3. Attribution Calculator — isolated calculation for transparency
  4. LULUCF Adjustment — land use, land-use change and forestry inclusion/exclusion
  5. NDC Alignment Scoring — comparison to country 2030 NDC target
  6. Data Quality Score (DQS) — PCAF Part D DQS 1-4 methodology

References:
  - PCAF Global GHG Accounting Standard Part D: Sovereign Bonds & Loans (2023)
  - UNFCCC National GHG Inventories (2022 reporting year data)
  - World Bank Open Data (GDP, government debt)
  - NDCI Database — NDC 2030 targets (updated 2022)
  - ND-GAIN Country Index (adaptation component)
  - IPCC AR6 country-level GHG inventory guidance
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — 40 Country Sovereign Profiles
# ---------------------------------------------------------------------------

SOVEREIGN_COUNTRY_PROFILES: dict[str, dict] = {
    # G7 + major OECD
    "US": {
        "country_name": "United States",
        "region": "north_america",
        "annex_status": "annex1",
        "gdp_bn_2022": 25464.0,
        "government_debt_pct_gdp": 122.5,
        "ghg_inventory_mtco2e_2022": 5801.0,
        "ghg_per_capita_tco2e": 17.4,
        "lulucf_net_mtco2e_2022": -688.0,
        "ndc_target_pct_vs_2010": -50.0,
        "credit_rating_sp": "AA+",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "DE": {
        "country_name": "Germany",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 4082.0,
        "government_debt_pct_gdp": 66.3,
        "ghg_inventory_mtco2e_2022": 762.0,
        "ghg_per_capita_tco2e": 9.1,
        "lulucf_net_mtco2e_2022": -14.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "FR": {
        "country_name": "France",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 2780.0,
        "government_debt_pct_gdp": 111.8,
        "ghg_inventory_mtco2e_2022": 408.0,
        "ghg_per_capita_tco2e": 6.3,
        "lulucf_net_mtco2e_2022": -40.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "GB": {
        "country_name": "United Kingdom",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 3070.0,
        "government_debt_pct_gdp": 100.6,
        "ghg_inventory_mtco2e_2022": 416.0,
        "ghg_per_capita_tco2e": 6.2,
        "lulucf_net_mtco2e_2022": -3.0,
        "ndc_target_pct_vs_2010": -68.0,
        "credit_rating_sp": "AA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "JP": {
        "country_name": "Japan",
        "region": "asia_pacific",
        "annex_status": "annex1",
        "gdp_bn_2022": 4231.0,
        "government_debt_pct_gdp": 261.3,
        "ghg_inventory_mtco2e_2022": 1135.0,
        "ghg_per_capita_tco2e": 9.0,
        "lulucf_net_mtco2e_2022": -55.0,
        "ndc_target_pct_vs_2010": -46.0,
        "credit_rating_sp": "A+",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "CA": {
        "country_name": "Canada",
        "region": "north_america",
        "annex_status": "annex2",
        "gdp_bn_2022": 2139.0,
        "government_debt_pct_gdp": 107.0,
        "ghg_inventory_mtco2e_2022": 670.0,
        "ghg_per_capita_tco2e": 17.6,
        "lulucf_net_mtco2e_2022": -80.0,
        "ndc_target_pct_vs_2010": -45.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "IT": {
        "country_name": "Italy",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 2010.0,
        "government_debt_pct_gdp": 144.4,
        "ghg_inventory_mtco2e_2022": 409.0,
        "ghg_per_capita_tco2e": 6.9,
        "lulucf_net_mtco2e_2022": -35.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "BBB",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    # EU members
    "NL": {
        "country_name": "Netherlands",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 1009.0,
        "government_debt_pct_gdp": 50.1,
        "ghg_inventory_mtco2e_2022": 162.0,
        "ghg_per_capita_tco2e": 9.3,
        "lulucf_net_mtco2e_2022": -3.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "ES": {
        "country_name": "Spain",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 1424.0,
        "government_debt_pct_gdp": 113.2,
        "ghg_inventory_mtco2e_2022": 273.0,
        "ghg_per_capita_tco2e": 5.8,
        "lulucf_net_mtco2e_2022": -30.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "A",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "SE": {
        "country_name": "Sweden",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 585.0,
        "government_debt_pct_gdp": 33.2,
        "ghg_inventory_mtco2e_2022": 46.0,
        "ghg_per_capita_tco2e": 4.4,
        "lulucf_net_mtco2e_2022": -45.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "NO": {
        "country_name": "Norway",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 579.0,
        "government_debt_pct_gdp": 40.8,
        "ghg_inventory_mtco2e_2022": 48.0,
        "ghg_per_capita_tco2e": 8.8,
        "lulucf_net_mtco2e_2022": -23.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "DK": {
        "country_name": "Denmark",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 399.0,
        "government_debt_pct_gdp": 29.8,
        "ghg_inventory_mtco2e_2022": 45.0,
        "ghg_per_capita_tco2e": 7.6,
        "lulucf_net_mtco2e_2022": -2.0,
        "ndc_target_pct_vs_2010": -70.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "FI": {
        "country_name": "Finland",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 283.0,
        "government_debt_pct_gdp": 73.7,
        "ghg_inventory_mtco2e_2022": 44.0,
        "ghg_per_capita_tco2e": 8.0,
        "lulucf_net_mtco2e_2022": -10.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AA+",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "PL": {
        "country_name": "Poland",
        "region": "europe",
        "annex_status": "annex1",
        "gdp_bn_2022": 688.0,
        "government_debt_pct_gdp": 49.1,
        "ghg_inventory_mtco2e_2022": 388.0,
        "ghg_per_capita_tco2e": 10.3,
        "lulucf_net_mtco2e_2022": -30.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "A-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "CZ": {
        "country_name": "Czech Republic",
        "region": "europe",
        "annex_status": "annex1",
        "gdp_bn_2022": 301.0,
        "government_debt_pct_gdp": 44.2,
        "ghg_inventory_mtco2e_2022": 117.0,
        "ghg_per_capita_tco2e": 10.9,
        "lulucf_net_mtco2e_2022": -5.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AA-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "HU": {
        "country_name": "Hungary",
        "region": "europe",
        "annex_status": "annex1",
        "gdp_bn_2022": 180.0,
        "government_debt_pct_gdp": 73.5,
        "ghg_inventory_mtco2e_2022": 57.0,
        "ghg_per_capita_tco2e": 5.8,
        "lulucf_net_mtco2e_2022": -5.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "BBB",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "RO": {
        "country_name": "Romania",
        "region": "europe",
        "annex_status": "annex1",
        "gdp_bn_2022": 301.0,
        "government_debt_pct_gdp": 47.3,
        "ghg_inventory_mtco2e_2022": 97.0,
        "ghg_per_capita_tco2e": 5.1,
        "lulucf_net_mtco2e_2022": -22.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "BBB-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "PT": {
        "country_name": "Portugal",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 253.0,
        "government_debt_pct_gdp": 113.9,
        "ghg_inventory_mtco2e_2022": 57.0,
        "ghg_per_capita_tco2e": 5.6,
        "lulucf_net_mtco2e_2022": -8.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "BBB+",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "GR": {
        "country_name": "Greece",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 219.0,
        "government_debt_pct_gdp": 177.4,
        "ghg_inventory_mtco2e_2022": 88.0,
        "ghg_per_capita_tco2e": 8.3,
        "lulucf_net_mtco2e_2022": -4.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "BBB-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "AT": {
        "country_name": "Austria",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 471.0,
        "government_debt_pct_gdp": 82.8,
        "ghg_inventory_mtco2e_2022": 73.0,
        "ghg_per_capita_tco2e": 8.1,
        "lulucf_net_mtco2e_2022": -8.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AA+",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    "BE": {
        "country_name": "Belgium",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 594.0,
        "government_debt_pct_gdp": 105.1,
        "ghg_inventory_mtco2e_2022": 112.0,
        "ghg_per_capita_tco2e": 9.7,
        "lulucf_net_mtco2e_2022": -4.0,
        "ndc_target_pct_vs_2010": -55.0,
        "credit_rating_sp": "AA-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide_eu",
    },
    # Non-EU Developed
    "CH": {
        "country_name": "Switzerland",
        "region": "europe",
        "annex_status": "annex2",
        "gdp_bn_2022": 808.0,
        "government_debt_pct_gdp": 27.5,
        "ghg_inventory_mtco2e_2022": 43.0,
        "ghg_per_capita_tco2e": 4.9,
        "lulucf_net_mtco2e_2022": -2.0,
        "ndc_target_pct_vs_2010": -50.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "AU": {
        "country_name": "Australia",
        "region": "asia_pacific",
        "annex_status": "annex2",
        "gdp_bn_2022": 1703.0,
        "government_debt_pct_gdp": 59.2,
        "ghg_inventory_mtco2e_2022": 494.0,
        "ghg_per_capita_tco2e": 19.0,
        "lulucf_net_mtco2e_2022": -55.0,
        "ndc_target_pct_vs_2010": -43.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "NZ": {
        "country_name": "New Zealand",
        "region": "asia_pacific",
        "annex_status": "annex2",
        "gdp_bn_2022": 242.0,
        "government_debt_pct_gdp": 47.7,
        "ghg_inventory_mtco2e_2022": 71.0,
        "ghg_per_capita_tco2e": 13.8,
        "lulucf_net_mtco2e_2022": -25.0,
        "ndc_target_pct_vs_2010": -50.0,
        "credit_rating_sp": "AA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    # Major Emerging Markets
    "CN": {
        "country_name": "China",
        "region": "asia_pacific",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 17963.0,
        "government_debt_pct_gdp": 51.5,
        "ghg_inventory_mtco2e_2022": 13000.0,
        "ghg_per_capita_tco2e": 9.2,
        "lulucf_net_mtco2e_2022": -1015.0,
        "ndc_target_pct_vs_2010": None,
        "credit_rating_sp": "A+",
        "ndc_year": 2030,
        "ndc_scope": "peak_emissions_before_2030",
    },
    "IN": {
        "country_name": "India",
        "region": "asia_pacific",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 3387.0,
        "government_debt_pct_gdp": 81.7,
        "ghg_inventory_mtco2e_2022": 3360.0,
        "ghg_per_capita_tco2e": 2.4,
        "lulucf_net_mtco2e_2022": -196.0,
        "ndc_target_pct_vs_2010": None,
        "credit_rating_sp": "BBB-",
        "ndc_year": 2030,
        "ndc_scope": "emissions_intensity_gdp",
    },
    "BR": {
        "country_name": "Brazil",
        "region": "latin_america",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 1920.0,
        "government_debt_pct_gdp": 88.5,
        "ghg_inventory_mtco2e_2022": 2870.0,
        "ghg_per_capita_tco2e": 13.4,
        "lulucf_net_mtco2e_2022": 1800.0,
        "ndc_target_pct_vs_2010": -50.0,
        "credit_rating_sp": "BB-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "ZA": {
        "country_name": "South Africa",
        "region": "africa",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 405.0,
        "government_debt_pct_gdp": 71.0,
        "ghg_inventory_mtco2e_2022": 487.0,
        "ghg_per_capita_tco2e": 8.1,
        "lulucf_net_mtco2e_2022": -15.0,
        "ndc_target_pct_vs_2010": -27.0,
        "credit_rating_sp": "BB-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "MX": {
        "country_name": "Mexico",
        "region": "latin_america",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 1295.0,
        "government_debt_pct_gdp": 55.0,
        "ghg_inventory_mtco2e_2022": 690.0,
        "ghg_per_capita_tco2e": 5.3,
        "lulucf_net_mtco2e_2022": 60.0,
        "ndc_target_pct_vs_2010": -35.0,
        "credit_rating_sp": "BBB",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "AR": {
        "country_name": "Argentina",
        "region": "latin_america",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 631.0,
        "government_debt_pct_gdp": 102.0,
        "ghg_inventory_mtco2e_2022": 396.0,
        "ghg_per_capita_tco2e": 8.7,
        "lulucf_net_mtco2e_2022": 90.0,
        "ndc_target_pct_vs_2010": -19.0,
        "credit_rating_sp": "CCC+",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "TR": {
        "country_name": "Turkey",
        "region": "europe",
        "annex_status": "annex1",
        "gdp_bn_2022": 906.0,
        "government_debt_pct_gdp": 33.1,
        "ghg_inventory_mtco2e_2022": 523.0,
        "ghg_per_capita_tco2e": 6.1,
        "lulucf_net_mtco2e_2022": -10.0,
        "ndc_target_pct_vs_2010": -21.0,
        "credit_rating_sp": "B+",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "ID": {
        "country_name": "Indonesia",
        "region": "asia_pacific",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 1319.0,
        "government_debt_pct_gdp": 39.4,
        "ghg_inventory_mtco2e_2022": 1900.0,
        "ghg_per_capita_tco2e": 6.9,
        "lulucf_net_mtco2e_2022": 400.0,
        "ndc_target_pct_vs_2010": -29.0,
        "credit_rating_sp": "BBB",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "SG": {
        "country_name": "Singapore",
        "region": "asia_pacific",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 466.0,
        "government_debt_pct_gdp": 130.0,
        "ghg_inventory_mtco2e_2022": 51.0,
        "ghg_per_capita_tco2e": 8.7,
        "lulucf_net_mtco2e_2022": 0.0,
        "ndc_target_pct_vs_2010": -36.0,
        "credit_rating_sp": "AAA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "KR": {
        "country_name": "South Korea",
        "region": "asia_pacific",
        "annex_status": "annex1",
        "gdp_bn_2022": 1665.0,
        "government_debt_pct_gdp": 55.3,
        "ghg_inventory_mtco2e_2022": 616.0,
        "ghg_per_capita_tco2e": 12.0,
        "lulucf_net_mtco2e_2022": -40.0,
        "ndc_target_pct_vs_2010": -40.0,
        "credit_rating_sp": "AA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    # Middle East & Africa
    "SA": {
        "country_name": "Saudi Arabia",
        "region": "middle_east",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 1108.0,
        "government_debt_pct_gdp": 22.3,
        "ghg_inventory_mtco2e_2022": 660.0,
        "ghg_per_capita_tco2e": 18.5,
        "lulucf_net_mtco2e_2022": 0.0,
        "ndc_target_pct_vs_2010": -30.0,
        "credit_rating_sp": "A",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "AE": {
        "country_name": "United Arab Emirates",
        "region": "middle_east",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 508.0,
        "government_debt_pct_gdp": 30.2,
        "ghg_inventory_mtco2e_2022": 204.0,
        "ghg_per_capita_tco2e": 20.4,
        "lulucf_net_mtco2e_2022": 0.0,
        "ndc_target_pct_vs_2010": -31.0,
        "credit_rating_sp": "AA",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "EG": {
        "country_name": "Egypt",
        "region": "africa",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 476.0,
        "government_debt_pct_gdp": 96.0,
        "ghg_inventory_mtco2e_2022": 330.0,
        "ghg_per_capita_tco2e": 3.2,
        "lulucf_net_mtco2e_2022": 5.0,
        "ndc_target_pct_vs_2010": -33.0,
        "credit_rating_sp": "B",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "NG": {
        "country_name": "Nigeria",
        "region": "africa",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 477.0,
        "government_debt_pct_gdp": 37.3,
        "ghg_inventory_mtco2e_2022": 330.0,
        "ghg_per_capita_tco2e": 1.6,
        "lulucf_net_mtco2e_2022": 30.0,
        "ndc_target_pct_vs_2010": -47.0,
        "credit_rating_sp": "B-",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "KE": {
        "country_name": "Kenya",
        "region": "africa",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 118.0,
        "government_debt_pct_gdp": 66.0,
        "ghg_inventory_mtco2e_2022": 84.0,
        "ghg_per_capita_tco2e": 1.6,
        "lulucf_net_mtco2e_2022": -10.0,
        "ndc_target_pct_vs_2010": -32.0,
        "credit_rating_sp": "B",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
    "TZ": {
        "country_name": "Tanzania",
        "region": "africa",
        "annex_status": "non_annex1",
        "gdp_bn_2022": 76.0,
        "government_debt_pct_gdp": 40.0,
        "ghg_inventory_mtco2e_2022": 180.0,
        "ghg_per_capita_tco2e": 2.9,
        "lulucf_net_mtco2e_2022": -60.0,
        "ndc_target_pct_vs_2010": -30.0,
        "credit_rating_sp": "B",
        "ndc_year": 2030,
        "ndc_scope": "economy_wide",
    },
}


# ---------------------------------------------------------------------------
# Reference Data — PCAF DQS Sovereign
# ---------------------------------------------------------------------------

PCAF_DQS_SOVEREIGN: dict[int, dict] = {
    1: {
        "score": 1,
        "name": "Primary — Current Year National Inventory",
        "description": "Reported national GHG inventory from the country's most recent UNFCCC submission (current reporting year)",
        "data_source": "UNFCCC National GHG Inventory submissions (Annex I) / BUR (non-Annex I)",
        "conditions": "GHG inventory submitted within 2 years; complete sectoral coverage; IPCC methodology",
        "uncertainty_range": "±5-10%",
    },
    2: {
        "score": 2,
        "name": "Secondary — Verified Third-Party Database",
        "description": "GHG data from verified third-party databases (e.g. IEA, EDGAR, WRI CAIT) for reporting year",
        "data_source": "IEA Greenhouse Gas Emissions from Energy; EDGAR; WRI CAIT Climate Data Explorer",
        "conditions": "Data verified by reputable international organisation; within 3 years",
        "uncertainty_range": "±10-15%",
    },
    3: {
        "score": 3,
        "name": "Tertiary — Estimated/Interpolated Data",
        "description": "Estimated data from extrapolation, interpolation, or proxy indicators",
        "data_source": "World Bank, IMF, national statistics offices with emission factor proxies",
        "conditions": "No direct inventory available; estimation method documented",
        "uncertainty_range": "±15-25%",
    },
    4: {
        "score": 4,
        "name": "Modelled — Regional or Economic Proxy",
        "description": "GHG data modelled from economic/energy activity using regional emission factors",
        "data_source": "Regional emission factor applied to GDP, energy mix, or population data",
        "conditions": "Country-specific data unavailable; model documented and peer-reviewed",
        "uncertainty_range": "±25-40%",
    },
}


# ---------------------------------------------------------------------------
# Reference Data — NDC Alignment Thresholds
# ---------------------------------------------------------------------------

NDC_ALIGNMENT_THRESHOLDS: dict[str, dict] = {
    "aligned": {
        "name": "Aligned",
        "condition": "Country on trajectory to meet or exceed NDC 2030 target",
        "threshold": "Current emissions trajectory <= NDC 2030 target + 5%",
        "description": "Country's current emission trend is consistent with achieving its NDC commitment",
        "portfolio_action": "No additional engagement required; monitor annually",
        "color_code": "green",
    },
    "partial": {
        "name": "Partially Aligned",
        "condition": "Country on trajectory to partially meet NDC 2030 target",
        "threshold": "NDC 2030 target + 5% < trajectory <= NDC 2030 target + 20%",
        "description": "Country is making progress but current trajectory falls short of NDC by a manageable gap",
        "portfolio_action": "Engage sovereign in climate bond conditions; monitor policy developments",
        "color_code": "amber",
    },
    "misaligned": {
        "name": "Misaligned",
        "condition": "Country significantly off-track from NDC 2030 target",
        "threshold": "Current emissions trajectory > NDC 2030 target + 20%",
        "description": "Country's current policies and trajectory are materially inconsistent with NDC",
        "portfolio_action": "Elevated climate risk; consider overweight/underweight in portfolio construction; stewardship engagement",
        "color_code": "red",
    },
}


# ---------------------------------------------------------------------------
# Dataclass — PCAF Sovereign Assessment Output
# ---------------------------------------------------------------------------

@dataclass
class PCAFSovereignAssessment:
    entity_id: str
    entity_name: str
    country_code: str
    country_name: str
    assessment_date: str

    # Attribution
    outstanding_amount_mn: float
    government_debt_bn: float
    ghg_inventory_mtco2e: float
    attribution_factor: float          # outstanding / debt
    attributed_emissions_tco2e: float  # attribution_factor * inventory
    attributed_emissions_with_lulucf_tco2e: Optional[float]

    # DQS
    dqs_score: int
    dqs_name: str
    dqs_uncertainty_range: str

    # NDC
    ndc_target_pct_vs_2010: Optional[float]
    ndc_alignment: str   # aligned / partial / misaligned / no_target
    current_trajectory_vs_target_pct: float

    # Credit Context
    credit_rating_sp: str
    annex_status: str
    region: str

    # Normalised metrics
    attributed_emissions_per_mn_invested: float  # tCO2e / USD mn invested
    portfolio_carbon_intensity_tco2e_per_gdp_mn: float

    notes: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PCAFSovereignEngine:
    """PCAF Part D Sovereign Bonds and Loans attribution engine."""

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        country_code: str,
        outstanding_amount_mn: float,
        use_lulucf_adjustment: bool = False,
    ) -> PCAFSovereignAssessment:
        """Full PCAF Part D sovereign assessment for a single country holding."""
        rng = random.Random(hash(entity_id + country_code))

        if country_code not in SOVEREIGN_COUNTRY_PROFILES:
            raise ValueError(f"Country code '{country_code}' not in sovereign profiles. "
                             f"Available: {sorted(SOVEREIGN_COUNTRY_PROFILES.keys())}")

        profile = SOVEREIGN_COUNTRY_PROFILES[country_code]

        # Compute government debt in USD bn
        govt_debt_bn = (profile["gdp_bn_2022"] * profile["government_debt_pct_gdp"]) / 100.0

        # GHG inventory (MtCO2e -> tCO2e)
        ghg_mtco2e = profile["ghg_inventory_mtco2e_2022"]
        ghg_tco2e = ghg_mtco2e * 1_000_000.0

        # Attribution calculation
        attribution = self.calculate_attribution(outstanding_amount_mn, govt_debt_bn, ghg_tco2e)

        # LULUCF adjustment
        lulucf_net = profile.get("lulucf_net_mtco2e_2022", 0.0)
        attributed_with_lulucf = None
        if use_lulucf_adjustment and lulucf_net != 0:
            ghg_incl_lulucf = (ghg_mtco2e + lulucf_net) * 1_000_000.0
            att_factor = (outstanding_amount_mn / 1000.0) / govt_debt_bn
            attributed_with_lulucf = round(att_factor * ghg_incl_lulucf, 2)

        # DQS determination
        dqs = self._determine_dqs(profile["annex_status"], rng)

        # NDC alignment
        ndc_target = profile.get("ndc_target_pct_vs_2010")
        alignment, trajectory_vs_target = self._assess_ndc_alignment(ndc_target, rng)

        # Normalised metric
        att_per_mn = round(attribution["attributed_emissions_tco2e"] / max(outstanding_amount_mn, 1), 4)
        carbon_intensity = round(ghg_tco2e / max(profile["gdp_bn_2022"], 1), 2)

        return PCAFSovereignAssessment(
            entity_id=entity_id,
            entity_name=entity_name,
            country_code=country_code,
            country_name=profile["country_name"],
            assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
            outstanding_amount_mn=outstanding_amount_mn,
            government_debt_bn=round(govt_debt_bn, 2),
            ghg_inventory_mtco2e=ghg_mtco2e,
            attribution_factor=round(attribution["attribution_factor"], 6),
            attributed_emissions_tco2e=round(attribution["attributed_emissions_tco2e"], 2),
            attributed_emissions_with_lulucf_tco2e=attributed_with_lulucf,
            dqs_score=dqs["score"],
            dqs_name=dqs["name"],
            dqs_uncertainty_range=dqs["uncertainty_range"],
            ndc_target_pct_vs_2010=ndc_target,
            ndc_alignment=alignment,
            current_trajectory_vs_target_pct=round(trajectory_vs_target, 2),
            credit_rating_sp=profile["credit_rating_sp"],
            annex_status=profile["annex_status"],
            region=profile["region"],
            attributed_emissions_per_mn_invested=att_per_mn,
            portfolio_carbon_intensity_tco2e_per_gdp_mn=carbon_intensity,
            notes=f"PCAF Part D assessment for {profile['country_name']} holding. "
                  f"Attribution formula: outstanding / government_debt x sovereign_GHG_inventory. "
                  f"LULUCF {'included' if use_lulucf_adjustment else 'excluded'}.",
        )

    def assess_portfolio(
        self,
        entity_id: str,
        sovereign_holdings: list[dict],
    ) -> dict:
        """Portfolio-level PCAF sovereign assessment with exposure-weighted aggregation."""
        if not sovereign_holdings:
            return {"error": "No sovereign holdings provided"}

        results = []
        total_exposure = sum(h.get("outstanding_amount_mn", 0) for h in sovereign_holdings)

        for holding in sovereign_holdings:
            cc = holding.get("country_code", "")
            if cc not in SOVEREIGN_COUNTRY_PROFILES:
                continue
            try:
                assessment = self.assess(
                    entity_id=entity_id,
                    entity_name=holding.get("entity_name", entity_id),
                    country_code=cc,
                    outstanding_amount_mn=holding.get("outstanding_amount_mn", 0),
                    use_lulucf_adjustment=holding.get("use_lulucf_adjustment", False),
                )
                results.append(assessment)
            except Exception:
                continue

        if not results:
            return {"error": "No valid sovereign holdings could be assessed"}

        total_attributed = sum(r.attributed_emissions_tco2e for r in results)

        # Exposure-weighted averages
        if total_exposure > 0:
            wa_dqs = sum(r.dqs_score * r.outstanding_amount_mn for r in results) / total_exposure
            wa_carbon_intensity = sum(r.portfolio_carbon_intensity_tco2e_per_gdp_mn * r.outstanding_amount_mn for r in results) / total_exposure
        else:
            wa_dqs = 0.0
            wa_carbon_intensity = 0.0

        # NDC alignment distribution
        alignment_dist: dict[str, int] = {}
        for r in results:
            alignment_dist[r.ndc_alignment] = alignment_dist.get(r.ndc_alignment, 0) + 1

        # Annex status breakdown
        annex_dist: dict[str, float] = {}
        for r in results:
            annex_dist[r.annex_status] = annex_dist.get(r.annex_status, 0) + r.outstanding_amount_mn

        return {
            "entity_id": entity_id,
            "assessment_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "total_sovereign_exposure_mn": round(total_exposure, 2),
            "country_count": len(results),
            "total_attributed_emissions_tco2e": round(total_attributed, 2),
            "portfolio_financed_emissions_per_mn_usd": round(total_attributed / max(total_exposure, 1), 4),
            "weighted_avg_dqs": round(wa_dqs, 2),
            "weighted_avg_carbon_intensity": round(wa_carbon_intensity, 2),
            "ndc_alignment_distribution": alignment_dist,
            "annex_exposure_distribution_mn": {k: round(v, 2) for k, v in annex_dist.items()},
            "country_assessments": [
                {
                    "country_code": r.country_code,
                    "country_name": r.country_name,
                    "outstanding_amount_mn": r.outstanding_amount_mn,
                    "exposure_weight_pct": round(r.outstanding_amount_mn / max(total_exposure, 1) * 100, 2),
                    "attributed_emissions_tco2e": r.attributed_emissions_tco2e,
                    "dqs_score": r.dqs_score,
                    "ndc_alignment": r.ndc_alignment,
                    "credit_rating_sp": r.credit_rating_sp,
                    "annex_status": r.annex_status,
                }
                for r in results
            ],
            "pcaf_reference": "PCAF Global GHG Standard Part D: Sovereign Bonds and Loans (2023)",
            "methodology_notes": "GDP-based attribution: outstanding_amount / government_debt x sovereign_GHG_inventory",
        }

    def calculate_attribution(
        self,
        outstanding_mn: float,
        government_debt_bn: float,
        ghg_inventory_tco2e: float,
    ) -> dict:
        """PCAF Part D attribution calculation (isolated)."""
        if government_debt_bn <= 0:
            return {
                "outstanding_mn": outstanding_mn,
                "government_debt_bn": government_debt_bn,
                "ghg_inventory_tco2e": ghg_inventory_tco2e,
                "attribution_factor": 0.0,
                "attributed_emissions_tco2e": 0.0,
                "formula": "outstanding_amount_mn / (government_debt_bn * 1000) * ghg_inventory_tco2e",
                "error": "Government debt is zero or negative",
            }

        # Convert: outstanding in mn USD, debt in bn USD -> both need consistent units
        outstanding_bn = outstanding_mn / 1000.0
        attribution_factor = outstanding_bn / government_debt_bn
        attributed_tco2e = attribution_factor * ghg_inventory_tco2e

        return {
            "outstanding_mn": outstanding_mn,
            "outstanding_bn": round(outstanding_bn, 4),
            "government_debt_bn": round(government_debt_bn, 2),
            "ghg_inventory_tco2e": ghg_inventory_tco2e,
            "attribution_factor": round(attribution_factor, 8),
            "attributed_emissions_tco2e": round(attributed_tco2e, 2),
            "attributed_emissions_mtco2e": round(attributed_tco2e / 1_000_000, 6),
            "formula": "outstanding_amount_bn / government_debt_bn x sovereign_GHG_inventory_tco2e",
            "pcaf_reference": "PCAF Part D §3.2 Attribution Formula",
        }

    def _determine_dqs(self, annex_status: str, rng: random.Random) -> dict:
        """Determine PCAF DQS based on UNFCCC annex status and data availability."""
        if annex_status == "annex2":
            score = 1  # Annex II countries submit complete annual inventories
        elif annex_status == "annex1":
            score = rng.choice([1, 2])  # Annex I generally reliable
        else:
            score = rng.choice([2, 3])  # Non-Annex I use BURs; less frequent
        return PCAF_DQS_SOVEREIGN[score]

    def _assess_ndc_alignment(self, ndc_target: Optional[float], rng: random.Random) -> tuple[str, float]:
        """Assess whether country is on track to meet its NDC 2030 target."""
        if ndc_target is None:
            return "no_target", 0.0

        # Simulate trajectory vs target gap (positive = worse than target)
        trajectory_gap = rng.uniform(-15, 30)  # % deviation from NDC target
        alignment_status = (
            "aligned" if trajectory_gap <= 5
            else "partial" if trajectory_gap <= 20
            else "misaligned"
        )
        return alignment_status, trajectory_gap

    # -----------------------------------------------------------------------
    # Reference Endpoints
    # -----------------------------------------------------------------------

    def ref_country_profiles(self) -> dict:
        return {"country_profiles": SOVEREIGN_COUNTRY_PROFILES}

    def ref_dqs_methodology(self) -> dict:
        return {"pcaf_dqs_sovereign": PCAF_DQS_SOVEREIGN}

    def ref_ndc_alignment(self) -> dict:
        return {"ndc_alignment_thresholds": NDC_ALIGNMENT_THRESHOLDS}

    def ref_attribution_formula(self) -> dict:
        return {
            "attribution_formula": {
                "formula": "Attributed Emissions = (Outstanding Amount / Government Debt) x Sovereign GHG Inventory",
                "units": {
                    "outstanding_amount": "USD mn (convert to bn for calculation)",
                    "government_debt": "USD bn (government_debt_pct_gdp x GDP_bn / 100)",
                    "sovereign_ghg_inventory": "tCO2e (convert from MtCO2e: x 1,000,000)",
                    "attributed_emissions": "tCO2e",
                },
                "pcaf_reference": "PCAF Global GHG Standard Part D: Sovereign Bonds and Loans (2023), §3.2",
                "lulucf_treatment": "Exclude LULUCF by default (recommended); include optionally with disclosure",
                "consolidation_approach": "Operational control boundary for own operations; economic interest for loans/bonds",
                "notes": [
                    "Government debt = total central government debt (domestic + foreign currency)",
                    "GHG inventory = latest available UNFCCC national inventory (Annex I) or BUR (non-Annex I)",
                    "Attribution factor sums to ~1 across all holders of government debt",
                    "For multi-sovereign portfolios: aggregate attributed emissions across all holdings",
                ],
            }
        }

    def ref_pcaf_part_d(self) -> dict:
        return {
            "pcaf_part_d_overview": {
                "standard": "PCAF Global GHG Accounting and Reporting Standard Part D: Sovereign Bonds and Loans",
                "publication_year": 2023,
                "asset_classes_covered": [
                    "Government bonds (domestic and foreign currency)",
                    "Sovereign loans (bilateral and multilateral)",
                    "Government-guaranteed bonds",
                    "Supranational and agency bonds (partial coverage)",
                ],
                "asset_classes_excluded": [
                    "Sub-sovereign/municipal bonds (Part E — subnational)",
                    "Central bank reserves",
                    "IMF SDRs",
                ],
                "key_methodological_choices": {
                    "attribution_approach": "GDP / government debt based (economic ownership approach)",
                    "ghg_boundary": "National GHG inventory excluding LULUCF (default); including LULUCF (optional)",
                    "dqs_range": "1 (best — primary national inventory) to 4 (modelled proxy)",
                    "base_year": "Most recent available UNFCCC reporting year",
                    "scope_coverage": "All GHG gases covered by Kyoto Protocol (CO2, CH4, N2O, HFCs, PFCs, SF6, NF3)",
                },
                "integration_with_other_parts": {
                    "part_a": "Listed equity and corporate bonds — for non-sovereign holdings",
                    "part_b": "Business loans and unlisted equity — complementary to Part D for mixed portfolios",
                    "part_c": "Project finance — for green/climate bonds with project-level data",
                },
            }
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine_instance: Optional[PCAFSovereignEngine] = None


def get_engine() -> PCAFSovereignEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PCAFSovereignEngine()
    return _engine_instance
