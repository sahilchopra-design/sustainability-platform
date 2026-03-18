"""
E78 — Carbon Accounting AI & Automation Engine
===============================================
AI-assisted GHG Protocol compliance, emission factor matching, Scope 3 auto-classification,
ML-based DQS derivation, XBRL auto-tagging, CDP response scoring, and data gap intelligence.

References:
- GHG Protocol Corporate Standard (2004) + Scope 3 Standard (2011)
- IPCC AR6 Annex II Emission Factors
- US EPA eGRID 2022
- DEFRA GHG Conversion Factors 2023
- ECOINVENT 3.9
- IEA WEO 2023
- ESRS XBRL Digital Taxonomy 2023
- CDP Climate C1-C12 / Water W1-W8 questionnaire structure
- PCAF DQS 1-5 scoring methodology
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Module-level reference data
# ---------------------------------------------------------------------------

EMISSION_FACTOR_DATABASES: Dict[str, Dict[str, Any]] = {
    "IPCC_AR6": {
        "name": "IPCC Sixth Assessment Report Annex II",
        "version": "AR6 2021",
        "coverage": "global",
        "update_frequency": "per_assessment_cycle",
        "dqs_tier": 2,
        "factors_count": 1200,
        "units": "kgCO2e per unit",
        "url": "https://www.ipcc.ch/report/ar6/wg3/",
    },
    "EPA_EGRID": {
        "name": "US EPA eGRID 2022",
        "version": "eGRID2022",
        "coverage": "USA",
        "update_frequency": "annual",
        "dqs_tier": 1,
        "factors_count": 800,
        "units": "kgCO2e per kWh",
        "url": "https://www.epa.gov/egrid",
    },
    "DEFRA_2023": {
        "name": "UK DEFRA GHG Conversion Factors 2023",
        "version": "2023",
        "coverage": "UK",
        "update_frequency": "annual",
        "dqs_tier": 1,
        "factors_count": 1500,
        "units": "kgCO2e per unit",
        "url": "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting",
    },
    "ECOINVENT_39": {
        "name": "ecoinvent 3.9 Life Cycle Inventory Database",
        "version": "3.9",
        "coverage": "global",
        "update_frequency": "annual",
        "dqs_tier": 1,
        "factors_count": 18000,
        "units": "kgCO2e per unit",
        "url": "https://ecoinvent.org/",
    },
    "IEA_WEO_2023": {
        "name": "IEA World Energy Outlook 2023",
        "version": "WEO2023",
        "coverage": "global",
        "update_frequency": "annual",
        "dqs_tier": 2,
        "factors_count": 300,
        "units": "kgCO2e per kWh/GJ",
        "url": "https://www.iea.org/reports/world-energy-outlook-2023",
    },
}

# 40 common activity categories with EF lookups per database (kgCO2e/unit)
EMISSION_FACTOR_LOOKUP: Dict[str, Dict[str, Any]] = {
    "electricity_grid_uk": {
        "description": "UK grid electricity consumption",
        "unit": "kWh",
        "databases": {"DEFRA_2023": 0.20493, "IEA_WEO_2023": 0.233},
        "best_ef": 0.20493,
        "best_db": "DEFRA_2023",
        "dqs": 1,
        "scope": 2,
    },
    "electricity_grid_us_average": {
        "description": "US average grid electricity",
        "unit": "kWh",
        "databases": {"EPA_EGRID": 0.3861, "IEA_WEO_2023": 0.393},
        "best_ef": 0.3861,
        "best_db": "EPA_EGRID",
        "dqs": 1,
        "scope": 2,
    },
    "natural_gas_combustion": {
        "description": "Natural gas stationary combustion",
        "unit": "m3",
        "databases": {"DEFRA_2023": 2.03441, "IPCC_AR6": 2.0},
        "best_ef": 2.03441,
        "best_db": "DEFRA_2023",
        "dqs": 1,
        "scope": 1,
    },
    "diesel_combustion": {
        "description": "Diesel fuel combustion (road transport)",
        "unit": "litre",
        "databases": {"DEFRA_2023": 2.51081, "IPCC_AR6": 2.68},
        "best_ef": 2.51081,
        "best_db": "DEFRA_2023",
        "dqs": 1,
        "scope": 1,
    },
    "petrol_combustion": {
        "description": "Petrol/gasoline combustion",
        "unit": "litre",
        "databases": {"DEFRA_2023": 2.27884, "IPCC_AR6": 2.31},
        "best_ef": 2.27884,
        "best_db": "DEFRA_2023",
        "dqs": 1,
        "scope": 1,
    },
    "lpg_combustion": {
        "description": "LPG combustion",
        "unit": "litre",
        "databases": {"DEFRA_2023": 1.55490, "IPCC_AR6": 1.61},
        "best_ef": 1.55490,
        "best_db": "DEFRA_2023",
        "dqs": 1,
        "scope": 1,
    },
    "coal_combustion": {
        "description": "Coal combustion for energy",
        "unit": "tonne",
        "databases": {"DEFRA_2023": 2401.1, "IPCC_AR6": 2460.0},
        "best_ef": 2401.1,
        "best_db": "DEFRA_2023",
        "dqs": 1,
        "scope": 1,
    },
    "air_travel_short_haul": {
        "description": "Short-haul air travel (<3700km)",
        "unit": "passenger-km",
        "databases": {"DEFRA_2023": 0.25495, "ECOINVENT_39": 0.271},
        "best_ef": 0.25495,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 6,
    },
    "air_travel_long_haul": {
        "description": "Long-haul air travel (>3700km)",
        "unit": "passenger-km",
        "databases": {"DEFRA_2023": 0.19309, "ECOINVENT_39": 0.210},
        "best_ef": 0.19309,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 6,
    },
    "rail_travel": {
        "description": "Rail passenger travel",
        "unit": "passenger-km",
        "databases": {"DEFRA_2023": 0.03549, "ECOINVENT_39": 0.041},
        "best_ef": 0.03549,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 6,
    },
    "hotel_stay": {
        "description": "Hotel accommodation",
        "unit": "room-night",
        "databases": {"DEFRA_2023": 25.0, "ECOINVENT_39": 28.2},
        "best_ef": 25.0,
        "best_db": "DEFRA_2023",
        "dqs": 3,
        "scope": 3,
        "category": 6,
    },
    "road_freight": {
        "description": "Road freight transport HGV",
        "unit": "tonne-km",
        "databases": {"DEFRA_2023": 0.10312, "ECOINVENT_39": 0.105},
        "best_ef": 0.10312,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 4,
    },
    "sea_freight": {
        "description": "Sea freight container shipping",
        "unit": "tonne-km",
        "databases": {"DEFRA_2023": 0.01611, "ECOINVENT_39": 0.0175},
        "best_ef": 0.01611,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 4,
    },
    "air_freight": {
        "description": "Air freight transport",
        "unit": "tonne-km",
        "databases": {"DEFRA_2023": 1.0200, "ECOINVENT_39": 1.08},
        "best_ef": 1.0200,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 4,
    },
    "steel_production": {
        "description": "Steel production (basic oxygen furnace)",
        "unit": "tonne",
        "databases": {"ECOINVENT_39": 2170.0, "IPCC_AR6": 2300.0},
        "best_ef": 2170.0,
        "best_db": "ECOINVENT_39",
        "dqs": 2,
        "scope": 3,
        "category": 1,
    },
    "cement_production": {
        "description": "Portland cement production",
        "unit": "tonne",
        "databases": {"ECOINVENT_39": 842.0, "IPCC_AR6": 820.0},
        "best_ef": 842.0,
        "best_db": "ECOINVENT_39",
        "dqs": 2,
        "scope": 3,
        "category": 1,
    },
    "aluminium_production": {
        "description": "Primary aluminium production",
        "unit": "tonne",
        "databases": {"ECOINVENT_39": 11500.0, "IPCC_AR6": 12000.0},
        "best_ef": 11500.0,
        "best_db": "ECOINVENT_39",
        "dqs": 2,
        "scope": 3,
        "category": 1,
    },
    "paper_production": {
        "description": "Paper and paperboard production",
        "unit": "tonne",
        "databases": {"ECOINVENT_39": 900.0, "DEFRA_2023": 950.0},
        "best_ef": 900.0,
        "best_db": "ECOINVENT_39",
        "dqs": 3,
        "scope": 3,
        "category": 1,
    },
    "plastic_production": {
        "description": "Generic plastics production",
        "unit": "tonne",
        "databases": {"ECOINVENT_39": 2530.0, "IPCC_AR6": 2600.0},
        "best_ef": 2530.0,
        "best_db": "ECOINVENT_39",
        "dqs": 3,
        "scope": 3,
        "category": 1,
    },
    "waste_landfill": {
        "description": "Waste disposal to landfill",
        "unit": "tonne",
        "databases": {"DEFRA_2023": 467.19, "ECOINVENT_39": 490.0},
        "best_ef": 467.19,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 5,
    },
    "waste_incineration": {
        "description": "Waste incineration (mixed municipal)",
        "unit": "tonne",
        "databases": {"DEFRA_2023": 950.0, "ECOINVENT_39": 1020.0},
        "best_ef": 950.0,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 5,
    },
    "water_supply": {
        "description": "Municipal water supply",
        "unit": "m3",
        "databases": {"DEFRA_2023": 0.344, "ECOINVENT_39": 0.376},
        "best_ef": 0.344,
        "best_db": "DEFRA_2023",
        "dqs": 3,
        "scope": 3,
        "category": 1,
    },
    "refrigerants_hfc134a": {
        "description": "HFC-134a refrigerant leakage",
        "unit": "kg",
        "databases": {"DEFRA_2023": 1430.0, "IPCC_AR6": 1430.0},
        "best_ef": 1430.0,
        "best_db": "IPCC_AR6",
        "dqs": 1,
        "scope": 1,
    },
    "refrigerants_r410a": {
        "description": "R-410A refrigerant leakage",
        "unit": "kg",
        "databases": {"DEFRA_2023": 2088.0, "IPCC_AR6": 2088.0},
        "best_ef": 2088.0,
        "best_db": "IPCC_AR6",
        "dqs": 1,
        "scope": 1,
    },
    "purchased_goods_food": {
        "description": "Purchased food/catering services",
        "unit": "GBP",
        "databases": {"DEFRA_2023": 0.00201, "ECOINVENT_39": 0.0022},
        "best_ef": 0.00201,
        "best_db": "DEFRA_2023",
        "dqs": 4,
        "scope": 3,
        "category": 1,
    },
    "purchased_goods_it": {
        "description": "Purchased IT hardware",
        "unit": "GBP",
        "databases": {"DEFRA_2023": 0.00094, "ECOINVENT_39": 0.0011},
        "best_ef": 0.00094,
        "best_db": "DEFRA_2023",
        "dqs": 4,
        "scope": 3,
        "category": 1,
    },
    "employee_commute_car": {
        "description": "Employee commuting by car (average)",
        "unit": "passenger-km",
        "databases": {"DEFRA_2023": 0.17021, "ECOINVENT_39": 0.175},
        "best_ef": 0.17021,
        "best_db": "DEFRA_2023",
        "dqs": 3,
        "scope": 3,
        "category": 7,
    },
    "employee_commute_bus": {
        "description": "Employee commuting by bus",
        "unit": "passenger-km",
        "databases": {"DEFRA_2023": 0.10279, "ECOINVENT_39": 0.108},
        "best_ef": 0.10279,
        "best_db": "DEFRA_2023",
        "dqs": 3,
        "scope": 3,
        "category": 7,
    },
    "company_car_petrol": {
        "description": "Company car (petrol, average)",
        "unit": "km",
        "databases": {"DEFRA_2023": 0.17021, "ECOINVENT_39": 0.175},
        "best_ef": 0.17021,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 1,
    },
    "company_car_ev": {
        "description": "Company car (battery electric vehicle)",
        "unit": "km",
        "databases": {"DEFRA_2023": 0.05320, "ECOINVENT_39": 0.065},
        "best_ef": 0.05320,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 3,
        "category": 11,
    },
    "district_heating": {
        "description": "District heating consumption",
        "unit": "kWh",
        "databases": {"DEFRA_2023": 0.21990, "ECOINVENT_39": 0.250},
        "best_ef": 0.21990,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 2,
    },
    "bioenergy_wood_pellets": {
        "description": "Bioenergy — wood pellets combustion",
        "unit": "GJ",
        "databases": {"DEFRA_2023": 18.3, "IPCC_AR6": 20.0},
        "best_ef": 18.3,
        "best_db": "DEFRA_2023",
        "dqs": 2,
        "scope": 1,
        "biogenic": True,
    },
    "solar_pv_generation": {
        "description": "Solar PV electricity generation (lifecycle)",
        "unit": "kWh",
        "databases": {"ECOINVENT_39": 0.045, "IEA_WEO_2023": 0.048},
        "best_ef": 0.045,
        "best_db": "ECOINVENT_39",
        "dqs": 2,
        "scope": 3,
        "category": 11,
    },
    "wind_generation": {
        "description": "Wind electricity generation (lifecycle)",
        "unit": "kWh",
        "databases": {"ECOINVENT_39": 0.011, "IEA_WEO_2023": 0.013},
        "best_ef": 0.011,
        "best_db": "ECOINVENT_39",
        "dqs": 2,
        "scope": 3,
        "category": 11,
    },
    "nitrogen_fertilizer": {
        "description": "Synthetic nitrogen fertilizer application",
        "unit": "kg N",
        "databases": {"IPCC_AR6": 3.1, "ECOINVENT_39": 3.5},
        "best_ef": 3.1,
        "best_db": "IPCC_AR6",
        "dqs": 2,
        "scope": 1,
        "flag": True,
    },
    "livestock_cattle": {
        "description": "Cattle enteric fermentation (dairy)",
        "unit": "head-year",
        "databases": {"IPCC_AR6": 1900.0, "ECOINVENT_39": 1950.0},
        "best_ef": 1900.0,
        "best_db": "IPCC_AR6",
        "dqs": 2,
        "scope": 1,
        "flag": True,
    },
    "deforestation_tropical": {
        "description": "Tropical deforestation (land-use change)",
        "unit": "hectare",
        "databases": {"IPCC_AR6": 500000.0, "ECOINVENT_39": 480000.0},
        "best_ef": 500000.0,
        "best_db": "IPCC_AR6",
        "dqs": 3,
        "scope": 3,
        "category": 1,
        "flag": True,
    },
    "sf6_use": {
        "description": "SF6 use in electrical equipment",
        "unit": "kg",
        "databases": {"IPCC_AR6": 23500.0, "DEFRA_2023": 23500.0},
        "best_ef": 23500.0,
        "best_db": "IPCC_AR6",
        "dqs": 1,
        "scope": 1,
    },
    "n2o_adipic_acid": {
        "description": "N2O from adipic acid production",
        "unit": "tonne product",
        "databases": {"IPCC_AR6": 300.0, "ECOINVENT_39": 310.0},
        "best_ef": 300.0,
        "best_db": "IPCC_AR6",
        "dqs": 2,
        "scope": 1,
    },
    "methane_coal_mining": {
        "description": "Fugitive methane from coal mining",
        "unit": "tonne coal",
        "databases": {"IPCC_AR6": 25.0, "ECOINVENT_39": 27.5},
        "best_ef": 25.0,
        "best_db": "IPCC_AR6",
        "dqs": 2,
        "scope": 1,
    },
}

SCOPE3_CLASSIFICATION_RULES: Dict[str, Dict[str, Any]] = {
    "C1_purchased_goods_services": {
        "category": 1,
        "name": "Purchased Goods and Services",
        "keywords": ["purchase", "supplier", "raw material", "ingredient", "component", "procurement",
                     "vendor", "buy", "goods", "material", "stock", "inventory"],
        "sic_codes": list(range(100, 3999)),
        "spend_threshold_usd": 0,
        "flag_applicable": True,
        "default_method": "spend_based",
    },
    "C2_capital_goods": {
        "category": 2,
        "name": "Capital Goods",
        "keywords": ["capital", "machinery", "equipment", "asset", "infrastructure", "building",
                     "plant", "vehicle fleet", "construction", "capex"],
        "sic_codes": [3400, 3500, 3600, 3700, 3800],
        "flag_applicable": False,
        "default_method": "spend_based",
    },
    "C3_fuel_energy": {
        "category": 3,
        "name": "Fuel and Energy Related Activities",
        "keywords": ["upstream", "fuel extraction", "transmission loss", "t&d loss", "wtt",
                     "well-to-tank", "energy upstream", "grid loss"],
        "sic_codes": [1300, 1311, 1321, 1381, 1382, 4911, 4931],
        "flag_applicable": False,
        "default_method": "average_data",
    },
    "C4_upstream_transport": {
        "category": 4,
        "name": "Upstream Transportation and Distribution",
        "keywords": ["freight", "shipping", "logistics", "transport", "delivery", "distribution",
                     "courier", "3pl", "warehouse", "inbound", "upstream transport"],
        "sic_codes": [4210, 4220, 4400, 4500, 4730, 7510, 7520],
        "flag_applicable": False,
        "default_method": "distance_based",
    },
    "C5_waste": {
        "category": 5,
        "name": "Waste Generated in Operations",
        "keywords": ["waste", "landfill", "recycling", "disposal", "sewage", "effluent",
                     "wastewater", "rubbish", "scrap", "hazardous waste"],
        "sic_codes": [4953, 4959],
        "flag_applicable": False,
        "default_method": "waste_type_specific",
    },
    "C6_business_travel": {
        "category": 6,
        "name": "Business Travel",
        "keywords": ["flight", "air travel", "hotel", "accommodation", "business travel",
                     "train", "taxi", "car hire", "rental car", "travel expense"],
        "sic_codes": [4512, 4522, 7011, 7514, 4111, 4131],
        "flag_applicable": False,
        "default_method": "distance_based",
    },
    "C7_employee_commute": {
        "category": 7,
        "name": "Employee Commuting",
        "keywords": ["commute", "employee travel", "home to work", "public transport subsidy",
                     "cycle scheme", "bus pass", "season ticket"],
        "sic_codes": [],
        "flag_applicable": False,
        "default_method": "average_data",
    },
    "C8_upstream_leased": {
        "category": 8,
        "name": "Upstream Leased Assets",
        "keywords": ["leased asset", "operating lease", "rented equipment", "lease payment",
                     "property lease", "asset lease upstream"],
        "sic_codes": [6510, 6512, 6552, 7359],
        "flag_applicable": False,
        "default_method": "asset_specific",
    },
    "C9_downstream_transport": {
        "category": 9,
        "name": "Downstream Transportation and Distribution",
        "keywords": ["customer delivery", "outbound transport", "distribution to customer",
                     "last mile", "retail distribution", "downstream logistics"],
        "sic_codes": [5000, 5200, 5300, 5400, 5600, 5700, 5900],
        "flag_applicable": False,
        "default_method": "distance_based",
    },
    "C10_processing": {
        "category": 10,
        "name": "Processing of Sold Products",
        "keywords": ["processing", "intermediate product", "sold intermediate", "downstream processing",
                     "customer manufacturing"],
        "sic_codes": [2000, 2600, 2700, 2800, 2900],
        "flag_applicable": False,
        "default_method": "average_data",
    },
    "C11_use_of_sold_products": {
        "category": 11,
        "name": "Use of Sold Products",
        "keywords": ["product use", "use phase", "consumer use", "energy consuming product",
                     "end-user", "customer use", "lifetime emissions", "in-use"],
        "sic_codes": [3600, 3700, 3714, 3559, 3640],
        "flag_applicable": False,
        "default_method": "direct_use",
    },
    "C12_end_of_life": {
        "category": 12,
        "name": "End-of-Life Treatment of Sold Products",
        "keywords": ["end of life", "eol", "product disposal", "post-consumer", "take-back",
                     "recycled product", "landfill product"],
        "sic_codes": [],
        "flag_applicable": False,
        "default_method": "waste_type_specific",
    },
    "C13_downstream_leased": {
        "category": 13,
        "name": "Downstream Leased Assets",
        "keywords": ["leased to customer", "property to let", "rental income asset",
                     "tenant operations", "downstream lease"],
        "sic_codes": [6510, 6512, 6552],
        "flag_applicable": False,
        "default_method": "asset_specific",
    },
    "C14_franchises": {
        "category": 14,
        "name": "Franchises",
        "keywords": ["franchise", "franchisee", "licensor", "licensed operation", "franchise fee"],
        "sic_codes": [5812, 5411, 5541, 7011],
        "flag_applicable": False,
        "default_method": "asset_specific",
    },
    "C15_investments": {
        "category": 15,
        "name": "Investments (Financed Emissions)",
        "keywords": ["investment", "loan", "bond", "equity", "portfolio", "financed",
                     "pcaf", "investee", "debt", "credit facility", "project finance"],
        "sic_codes": [6000, 6100, 6200, 6300, 6400, 6500, 6710],
        "flag_applicable": False,
        "default_method": "pcaf_attribution",
    },
}

XBRL_ESRS_CONCEPTS: Dict[str, Dict[str, Any]] = {
    "esrs:GrossScope1GHGEmissions": {
        "label": "Gross Scope 1 GHG Emissions",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:GrossScope2LocationBasedGHGEmissions": {
        "label": "Gross Scope 2 GHG Emissions (location-based)",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:GrossScope2MarketBasedGHGEmissions": {
        "label": "Gross Scope 2 GHG Emissions (market-based)",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:TotalGrossScope3GHGEmissions": {
        "label": "Total Gross Scope 3 GHG Emissions",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:Scope3Category1GHGEmissions": {
        "label": "Scope 3 Category 1 — Purchased Goods and Services",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:Scope3Category6GHGEmissions": {
        "label": "Scope 3 Category 6 — Business Travel",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:Scope3Category15FinancedEmissions": {
        "label": "Scope 3 Category 15 — Financed Emissions",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:TotalGHGEmissions": {
        "label": "Total GHG Emissions (S1+S2+S3)",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:GHGIntensityRevenue": {
        "label": "GHG Intensity per Net Revenue",
        "datatype": "xbrli:decimal",
        "unit": "tCO2e per EUR million",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:GHGIntensityEmployees": {
        "label": "GHG Intensity per FTE",
        "datatype": "xbrli:decimal",
        "unit": "tCO2e per FTE",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:BaseYearGHGEmissions": {
        "label": "Base Year GHG Emissions",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "instant",
        "reporting_frequency": "once_then_update",
    },
    "esrs:BaseYear": {
        "label": "Base Year for GHG Calculations",
        "datatype": "xbrli:gYear",
        "unit": "year",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "instant",
        "reporting_frequency": "once_then_update",
    },
    "esrs:GHGReductionTargetYear": {
        "label": "GHG Reduction Target Year",
        "datatype": "xbrli:gYear",
        "unit": "year",
        "mandatory": True,
        "esrs_reference": "ESRS E1-5",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:GHGAbsoluteReductionTarget": {
        "label": "Absolute GHG Reduction Target (%)",
        "datatype": "xbrli:decimal",
        "unit": "percentage",
        "mandatory": True,
        "esrs_reference": "ESRS E1-5",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:GHGIntensityReductionTarget": {
        "label": "GHG Intensity Reduction Target (%)",
        "datatype": "xbrli:decimal",
        "unit": "percentage",
        "mandatory": False,
        "esrs_reference": "ESRS E1-5",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:EnergyConsumptionTotal": {
        "label": "Total Energy Consumption",
        "datatype": "xbrli:decimal",
        "unit": "MWh",
        "mandatory": True,
        "esrs_reference": "ESRS E1-5",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:EnergyConsumptionRenewable": {
        "label": "Renewable Energy Consumption",
        "datatype": "xbrli:decimal",
        "unit": "MWh",
        "mandatory": True,
        "esrs_reference": "ESRS E1-5",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:EnergyConsumptionNonRenewable": {
        "label": "Non-Renewable Energy Consumption",
        "datatype": "xbrli:decimal",
        "unit": "MWh",
        "mandatory": True,
        "esrs_reference": "ESRS E1-5",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:RenewableEnergyPercentage": {
        "label": "Renewable Energy as % of Total",
        "datatype": "xbrli:decimal",
        "unit": "percentage",
        "mandatory": False,
        "esrs_reference": "ESRS E1-5",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:BiogenicCarbonEmissions": {
        "label": "Biogenic Carbon Emissions",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:BiogenicCarbonRemovals": {
        "label": "Biogenic Carbon Removals",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:CarbonCreditsPurchased": {
        "label": "Carbon Credits Purchased",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": False,
        "esrs_reference": "ESRS E1-7",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:CarbonCreditsRetired": {
        "label": "Carbon Credits Retired (Offset Claimed)",
        "datatype": "xbrli:decimal",
        "unit": "Metric tons CO2 equivalent",
        "mandatory": False,
        "esrs_reference": "ESRS E1-7",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:InternalCarbonPrice": {
        "label": "Internal Carbon Price Applied",
        "datatype": "xbrli:decimal",
        "unit": "EUR per tonne CO2 equivalent",
        "mandatory": False,
        "esrs_reference": "ESRS E1-7",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:PhysicalClimateRiskExposure": {
        "label": "Physical Climate Risk Exposure (% assets)",
        "datatype": "xbrli:decimal",
        "unit": "percentage",
        "mandatory": True,
        "esrs_reference": "ESRS E1-2",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:TransitionClimateRiskExposure": {
        "label": "Transition Climate Risk Financial Exposure",
        "datatype": "xbrli:decimal",
        "unit": "EUR millions",
        "mandatory": True,
        "esrs_reference": "ESRS E1-2",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:ClimateOpportunitiesValue": {
        "label": "Identified Climate Opportunities Value",
        "datatype": "xbrli:decimal",
        "unit": "EUR millions",
        "mandatory": False,
        "esrs_reference": "ESRS E1-3",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:CapexForClimateTransition": {
        "label": "Capital Expenditure for Climate Transition",
        "datatype": "xbrli:decimal",
        "unit": "EUR millions",
        "mandatory": True,
        "esrs_reference": "ESRS E1-3",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:OpexForClimateTransition": {
        "label": "Operating Expenditure for Climate Transition",
        "datatype": "xbrli:decimal",
        "unit": "EUR millions",
        "mandatory": True,
        "esrs_reference": "ESRS E1-3",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:ConsolidationApproach": {
        "label": "GHG Consolidation Approach",
        "datatype": "xbrli:string",
        "unit": "enum: equity_share | operational_control | financial_control",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:OrganisationalBoundaryDescription": {
        "label": "Organisational Boundary Description",
        "datatype": "xbrli:string",
        "unit": "text",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:GHGVerificationStatus": {
        "label": "GHG Data Verification/Assurance Status",
        "datatype": "xbrli:string",
        "unit": "enum: none | limited | reasonable",
        "mandatory": True,
        "esrs_reference": "ESRS E1-6",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:ExclusionsFromScope3": {
        "label": "Categories Excluded from Scope 3",
        "datatype": "xbrli:string",
        "unit": "text",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:UncertaintyQuantification": {
        "label": "GHG Uncertainty Quantification (±%)",
        "datatype": "xbrli:decimal",
        "unit": "percentage",
        "mandatory": False,
        "esrs_reference": "ESRS E1-6",
        "period_type": "duration",
        "reporting_frequency": "annual",
    },
    "esrs:ClimateScenariosUsed": {
        "label": "Climate Scenarios Used in Analysis",
        "datatype": "xbrli:string",
        "unit": "text",
        "mandatory": True,
        "esrs_reference": "ESRS E1-2",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:ParisAlignmentAssessment": {
        "label": "Paris Agreement Alignment Assessment",
        "datatype": "xbrli:string",
        "unit": "text",
        "mandatory": True,
        "esrs_reference": "ESRS E1-5",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:SBTiCommitmentStatus": {
        "label": "Science-Based Targets Initiative Commitment Status",
        "datatype": "xbrli:string",
        "unit": "enum: committed | approved | not_committed",
        "mandatory": False,
        "esrs_reference": "ESRS E1-5",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:Net0TargetYear": {
        "label": "Net-Zero Target Year",
        "datatype": "xbrli:gYear",
        "unit": "year",
        "mandatory": False,
        "esrs_reference": "ESRS E1-5",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:TransitionPlanAdopted": {
        "label": "Climate Transition Plan Adopted (Y/N)",
        "datatype": "xbrli:boolean",
        "unit": "boolean",
        "mandatory": True,
        "esrs_reference": "ESRS E1-1",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:StrategicMilestonesForDecarbonisation": {
        "label": "Strategic Milestones for Decarbonisation",
        "datatype": "xbrli:string",
        "unit": "text",
        "mandatory": True,
        "esrs_reference": "ESRS E1-1",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:ClimateGovernanceDescription": {
        "label": "Board-level Climate Governance Description",
        "datatype": "xbrli:string",
        "unit": "text",
        "mandatory": True,
        "esrs_reference": "ESRS 2-GOV",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:ClimateRelatedRemuneration": {
        "label": "Climate KPIs in Executive Remuneration (Y/N)",
        "datatype": "xbrli:boolean",
        "unit": "boolean",
        "mandatory": False,
        "esrs_reference": "ESRS 2-GOV",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
    "esrs:DoubleMateriailtyAssessmentCompleted": {
        "label": "Double Materiality Assessment Completed (Y/N)",
        "datatype": "xbrli:boolean",
        "unit": "boolean",
        "mandatory": True,
        "esrs_reference": "ESRS 2-IRO",
        "period_type": "instant",
        "reporting_frequency": "annual",
    },
}

CDP_QUESTIONNAIRE_STRUCTURE: Dict[str, Dict[str, Any]] = {
    "C0": {
        "section": "Introduction",
        "questions": ["C0.1", "C0.2", "C0.3"],
        "weight": 0.0,
        "mandatory": True,
        "description": "Company details and reporting boundary",
    },
    "C1": {
        "section": "Governance",
        "questions": ["C1.1", "C1.2", "C1.3"],
        "weight": 0.125,
        "mandatory": True,
        "description": "Board oversight and management responsibility for climate",
        "scoring_criteria": ["board_oversight", "management_responsibility", "climate_remuneration"],
    },
    "C2": {
        "section": "Risks and Opportunities",
        "questions": ["C2.1", "C2.2", "C2.3", "C2.4", "C2.5", "C2.6"],
        "weight": 0.125,
        "mandatory": True,
        "description": "Climate-related risks and opportunities identification",
        "scoring_criteria": ["risk_identification", "risk_assessment_process", "opportunity_identification",
                             "financial_impact_quantification"],
    },
    "C3": {
        "section": "Business Strategy",
        "questions": ["C3.1", "C3.2", "C3.3", "C3.4", "C3.5"],
        "weight": 0.10,
        "mandatory": True,
        "description": "Integration of climate into business strategy",
        "scoring_criteria": ["strategy_integration", "scenario_analysis", "time_horizons"],
    },
    "C4": {
        "section": "Targets and Performance",
        "questions": ["C4.1", "C4.1a", "C4.2", "C4.2a"],
        "weight": 0.125,
        "mandatory": True,
        "description": "GHG reduction targets and progress",
        "scoring_criteria": ["scope_coverage", "sbti_alignment", "interim_targets", "progress_reporting"],
    },
    "C5": {
        "section": "Emissions Methodology",
        "questions": ["C5.1", "C5.1a", "C5.1b", "C5.1c", "C5.2", "C5.3"],
        "weight": 0.05,
        "mandatory": True,
        "description": "GHG accounting methodology and assurance",
        "scoring_criteria": ["ghg_standard", "boundary_description", "assurance_provided"],
    },
    "C6": {
        "section": "Emissions Data",
        "questions": ["C6.1", "C6.2", "C6.3", "C6.4", "C6.5", "C6.7", "C6.10"],
        "weight": 0.125,
        "mandatory": True,
        "description": "Scope 1, 2, 3 emissions data",
        "scoring_criteria": ["scope1_completeness", "scope2_dual_reporting", "scope3_coverage",
                             "biogenic_reporting", "intensity_metric"],
    },
    "C7": {
        "section": "Emissions Breakdown",
        "questions": ["C7.1", "C7.2", "C7.3", "C7.4", "C7.5", "C7.6", "C7.7", "C7.8", "C7.9"],
        "weight": 0.05,
        "mandatory": False,
        "description": "Breakdown by country, business division, activity type",
        "scoring_criteria": ["geographic_breakdown", "activity_breakdown"],
    },
    "C8": {
        "section": "Energy",
        "questions": ["C8.1", "C8.2", "C8.2a"],
        "weight": 0.10,
        "mandatory": True,
        "description": "Energy consumption, mix, and low-carbon transition",
        "scoring_criteria": ["energy_total", "renewable_percentage", "energy_reduction_initiatives"],
    },
    "C9": {
        "section": "Additional Metrics",
        "questions": ["C9.1"],
        "weight": 0.025,
        "mandatory": False,
        "description": "Sector-specific metrics",
    },
    "C10": {
        "section": "Verification",
        "questions": ["C10.1", "C10.1a", "C10.2"],
        "weight": 0.075,
        "mandatory": True,
        "description": "Third-party verification status",
        "scoring_criteria": ["scope1_verified", "scope2_verified", "scope3_verified", "assurance_level"],
    },
    "C11": {
        "section": "Carbon Pricing",
        "questions": ["C11.1", "C11.2", "C11.3"],
        "weight": 0.05,
        "mandatory": False,
        "description": "Exposure to and use of internal/external carbon pricing",
        "scoring_criteria": ["ets_coverage", "internal_carbon_price", "shadow_price"],
    },
    "C12": {
        "section": "Engagement",
        "questions": ["C12.1", "C12.1a", "C12.1b", "C12.2", "C12.3", "C12.4"],
        "weight": 0.075,
        "mandatory": False,
        "description": "Engagement with value chain, policy makers, investors",
        "scoring_criteria": ["supplier_engagement", "customer_engagement", "policy_engagement",
                             "industry_engagement"],
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class GHGDisclosureInput:
    """Input data for a GHG disclosure assessment."""
    entity_name: str
    reporting_year: int
    scope1_tco2e: Optional[float] = None
    scope2_location_tco2e: Optional[float] = None
    scope2_market_tco2e: Optional[float] = None
    scope3_categories: Optional[Dict[int, float]] = None  # category -> tCO2e
    base_year: Optional[int] = None
    consolidation_approach: Optional[str] = None  # equity_share | operational_control | financial_control
    boundary_description: Optional[str] = None
    verification_status: Optional[str] = None  # none | limited | reasonable
    biogenic_emissions_tco2e: Optional[float] = None
    uncertainty_pct: Optional[float] = None
    ghg_reduction_target_pct: Optional[float] = None
    target_year: Optional[int] = None
    sbti_status: Optional[str] = None  # committed | approved | not_committed
    cdp_responses: Optional[Dict[str, Any]] = None
    industry_sector: Optional[str] = None
    revenue_eur_m: Optional[float] = None
    fte_count: Optional[int] = None
    energy_mwh: Optional[float] = None
    renewable_energy_pct: Optional[float] = None


@dataclass
class EmissionFactorQuery:
    """Query for emission factor matching."""
    activity_description: str
    quantity: float
    unit: Optional[str] = None
    country: Optional[str] = None
    year: Optional[int] = None
    preferred_database: Optional[str] = None


@dataclass
class Scope3TransactionInput:
    """Financial transaction data for Scope 3 auto-classification."""
    supplier_name: str
    spend_amount: float
    currency: str = "USD"
    sic_code: Optional[int] = None
    description: Optional[str] = None
    transaction_type: Optional[str] = None


@dataclass
class CarbonAccountingAIResult:
    """Consolidated result from the Carbon Accounting AI engine."""
    entity_name: str
    reporting_year: int
    ghg_compliance: Dict[str, Any] = field(default_factory=dict)
    ef_matching: Dict[str, Any] = field(default_factory=dict)
    scope3_classification: Dict[str, Any] = field(default_factory=dict)
    dqs_score: Dict[str, Any] = field(default_factory=dict)
    xbrl_tagging: Dict[str, Any] = field(default_factory=dict)
    cdp_scoring: Dict[str, Any] = field(default_factory=dict)
    data_gaps: Dict[str, Any] = field(default_factory=dict)
    overall_readiness_score: float = 0.0
    priority_actions: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CarbonAccountingAIEngine:
    """
    E78 Carbon Accounting AI & Automation Engine.

    Provides AI-assisted services for GHG Protocol compliance, emission factor
    matching, Scope 3 classification, DQS derivation, XBRL auto-tagging,
    CDP response scoring, and data gap intelligence.
    """

    # GHG Protocol compliance criteria and their weights
    GHG_COMPLIANCE_CRITERIA: Dict[str, Dict[str, Any]] = {
        "boundary_setting": {
            "weight": 0.20,
            "description": "Organisational and operational boundary clearly defined",
            "sub_checks": ["consolidation_approach_stated", "boundary_description_present",
                           "excluded_sources_documented"],
        },
        "base_year": {
            "weight": 0.15,
            "description": "Base year established with recalculation policy",
            "sub_checks": ["base_year_stated", "base_year_emissions_reported",
                           "recalculation_policy_documented"],
        },
        "scope1_completeness": {
            "weight": 0.15,
            "description": "Scope 1 emissions complete and categorised",
            "sub_checks": ["scope1_value_present", "scope1_by_gas_reported", "scope1_by_facility"],
        },
        "scope2_dual_method": {
            "weight": 0.10,
            "description": "Scope 2 reported under both location and market-based methods",
            "sub_checks": ["scope2_location_present", "scope2_market_present"],
        },
        "scope3_coverage": {
            "weight": 0.15,
            "description": "Scope 3 categories assessed; material categories reported",
            "sub_checks": ["scope3_categories_assessed", "flagged_categories_reported",
                           "c15_financed_emissions"],
        },
        "verification_status": {
            "weight": 0.10,
            "description": "Third-party verification obtained for material scopes",
            "sub_checks": ["scope1_verified", "scope2_verified", "assurance_level_stated"],
        },
        "biogenic_carbon": {
            "weight": 0.05,
            "description": "Biogenic carbon emissions reported separately",
            "sub_checks": ["biogenic_emissions_reported", "biogenic_removals_reported"],
        },
        "uncertainty_quantification": {
            "weight": 0.10,
            "description": "Uncertainty range quantified per GHG Protocol guidance",
            "sub_checks": ["uncertainty_pct_stated", "uncertainty_method_described"],
        },
    }

    def check_ghg_compliance(self, d: GHGDisclosureInput) -> Dict[str, Any]:
        """
        Check completeness of GHG disclosures against GHG Protocol requirements.

        Returns:
            compliance_pct: overall compliance percentage
            criterion_scores: per-criterion pass/fail/partial
            gaps: list of identified compliance gaps
            recommendations: actionable improvement suggestions
        """
        scores: Dict[str, float] = {}
        gaps: List[str] = []
        recommendations: List[str] = []

        # --- Boundary setting ---
        bs_score = 0.0
        if d.consolidation_approach:
            bs_score += 0.40
        else:
            gaps.append("Consolidation approach (equity share / operational / financial control) not stated.")
            recommendations.append("Declare GHG consolidation approach per GHG Protocol §3.")
        if d.boundary_description:
            bs_score += 0.40
        else:
            gaps.append("Organisational boundary description absent.")
        bs_score += 0.20  # assume excluded sources undocumented but minor gap
        scores["boundary_setting"] = bs_score

        # --- Base year ---
        by_score = 0.0
        if d.base_year:
            by_score += 0.50
        else:
            gaps.append("Base year not established.")
            recommendations.append("Set base year ≥2015 with documented recalculation policy.")
        if d.base_year and d.scope1_tco2e is not None:
            by_score += 0.30
        by_score += 0.20  # partial credit for recalculation policy assumed
        scores["base_year"] = min(by_score, 1.0)

        # --- Scope 1 completeness ---
        s1_score = 0.0
        if d.scope1_tco2e is not None:
            s1_score += 0.60
        else:
            gaps.append("Scope 1 emissions value not reported.")
            recommendations.append("Calculate and disclose Scope 1 stationary + mobile combustion, process, and fugitive emissions.")
        s1_score += 0.20  # by-gas breakdown assumed partial
        s1_score += 0.20  # by-facility partial
        scores["scope1_completeness"] = min(s1_score, 1.0)

        # --- Scope 2 dual method ---
        s2_score = 0.0
        if d.scope2_location_tco2e is not None:
            s2_score += 0.50
        else:
            gaps.append("Scope 2 location-based emissions not reported.")
        if d.scope2_market_tco2e is not None:
            s2_score += 0.50
        else:
            gaps.append("Scope 2 market-based emissions not reported.")
            recommendations.append("Report Scope 2 under both location-based and market-based methods (GHG Protocol Scope 2 Guidance 2015).")
        scores["scope2_dual_method"] = s2_score

        # --- Scope 3 coverage ---
        s3_score = 0.0
        if d.scope3_categories:
            n_cats = len(d.scope3_categories)
            s3_score += min(n_cats / 15.0, 0.60)
            if 15 in d.scope3_categories:
                s3_score += 0.20
            else:
                if d.industry_sector in ["banking", "insurance", "asset_management", "investment"]:
                    gaps.append("Category 15 (Financed Emissions) absent — mandatory for financial institutions.")
                    recommendations.append("Calculate C15 financed emissions using PCAF methodology.")
        else:
            gaps.append("Scope 3 categories not assessed.")
            recommendations.append("Conduct Scope 3 category screening; report at least Categories 1, 3, 11, and 15 (if applicable).")
        s3_score += 0.20  # partial for flag categories
        scores["scope3_coverage"] = min(s3_score, 1.0)

        # --- Verification ---
        v_score = 0.0
        if d.verification_status == "reasonable":
            v_score = 1.0
        elif d.verification_status == "limited":
            v_score = 0.60
            recommendations.append("Upgrade from limited to reasonable assurance to meet CSRD Art 26a requirements.")
        else:
            gaps.append("No third-party verification or assurance obtained.")
            recommendations.append("Obtain at least limited assurance from an accredited body (ISAE 3410 or ISO 14064-3).")
        scores["verification_status"] = v_score

        # --- Biogenic carbon ---
        bio_score = 0.0
        if d.biogenic_emissions_tco2e is not None:
            bio_score = 0.80
        else:
            gaps.append("Biogenic carbon emissions not separately reported.")
            recommendations.append("Report biogenic CO2 emissions separately (outside of scopes) per GHG Protocol.")
        bio_score += 0.20  # partial for removals
        scores["biogenic_carbon"] = min(bio_score, 1.0)

        # --- Uncertainty ---
        unc_score = 0.0
        if d.uncertainty_pct is not None:
            unc_score = 0.80
        else:
            gaps.append("Uncertainty quantification (±%) not provided.")
            recommendations.append("Quantify GHG inventory uncertainty using error propagation or Monte Carlo simulation.")
        unc_score += 0.20
        scores["uncertainty_quantification"] = min(unc_score, 1.0)

        # Weighted overall compliance
        compliance_pct = sum(
            scores[k] * self.GHG_COMPLIANCE_CRITERIA[k]["weight"]
            for k in scores
        ) * 100.0

        return {
            "compliance_pct": round(compliance_pct, 1),
            "status": "compliant" if compliance_pct >= 80 else ("partial" if compliance_pct >= 50 else "non_compliant"),
            "criterion_scores": {k: round(v * 100, 1) for k, v in scores.items()},
            "gaps": gaps,
            "recommendations": recommendations,
            "standard_reference": "GHG Protocol Corporate Standard (2004) + Scope 3 Standard (2011)",
        }

    def match_emission_factor(self, query: EmissionFactorQuery) -> Dict[str, Any]:
        """
        Match an activity description to emission factor databases using keyword scoring.

        Returns best-match EF, confidence score, data quality tier, and alternatives.
        """
        desc_lower = query.activity_description.lower()
        best_key: Optional[str] = None
        best_score: float = 0.0

        keyword_map: Dict[str, List[str]] = {
            "electricity_grid_uk": ["electricity", "power", "grid", "uk", "england"],
            "electricity_grid_us_average": ["electricity", "power", "grid", "us", "usa", "america"],
            "natural_gas_combustion": ["natural gas", "gas combustion", "boiler", "furnace", "gas heating"],
            "diesel_combustion": ["diesel", "gasoil", "hgv fuel", "generator diesel"],
            "petrol_combustion": ["petrol", "gasoline", "unleaded", "car fuel"],
            "air_travel_short_haul": ["short haul", "short-haul", "domestic flight", "flight <3700"],
            "air_travel_long_haul": ["long haul", "long-haul", "international flight", "transatlantic"],
            "road_freight": ["road freight", "lorry", "truck", "hgv transport"],
            "sea_freight": ["sea freight", "shipping", "container ship", "ocean freight"],
            "air_freight": ["air freight", "cargo aircraft", "air cargo"],
            "waste_landfill": ["landfill", "waste disposal", "general waste"],
            "waste_incineration": ["incineration", "waste burn", "energy from waste"],
            "refrigerants_hfc134a": ["hfc", "refrigerant", "r134a", "hfc-134a"],
            "refrigerants_r410a": ["r410a", "r-410a", "air conditioning refrigerant"],
            "steel_production": ["steel", "iron", "bof", "blast furnace"],
            "cement_production": ["cement", "clinker", "concrete production"],
            "employee_commute_car": ["employee commute", "staff commute", "home to work car"],
            "company_car_petrol": ["company car", "fleet car", "pool car"],
            "nitrogen_fertilizer": ["fertilizer", "nitrogen", "ammonia", "urea application"],
            "livestock_cattle": ["cattle", "dairy", "beef", "livestock", "enteric fermentation"],
        }

        for key, kws in keyword_map.items():
            matches = sum(1 for kw in kws if kw in desc_lower)
            score = matches / max(len(kws), 1)
            if score > best_score:
                best_score = score
                best_key = key

        if best_key and best_score > 0.0:
            ef_data = EMISSION_FACTOR_LOOKUP[best_key]
            confidence = min(best_score * 1.5, 0.95)
            total_emissions = ef_data["best_ef"] * query.quantity

            # Apply country/database preference
            preferred_ef = ef_data["best_ef"]
            preferred_db = ef_data["best_db"]
            if query.preferred_database and query.preferred_database in ef_data["databases"]:
                preferred_ef = ef_data["databases"][query.preferred_database]
                preferred_db = query.preferred_database

            return {
                "matched_activity": best_key,
                "description": ef_data["description"],
                "confidence": round(confidence, 3),
                "emission_factor_kgco2e_per_unit": preferred_ef,
                "unit": ef_data["unit"],
                "matched_database": preferred_db,
                "total_emissions_kgco2e": round(preferred_ef * query.quantity, 2),
                "total_emissions_tco2e": round(preferred_ef * query.quantity / 1000, 4),
                "dqs_tier": ef_data["dqs"],
                "scope": ef_data.get("scope"),
                "scope3_category": ef_data.get("category"),
                "flag_land_use": ef_data.get("flag", False),
                "biogenic": ef_data.get("biogenic", False),
                "alternative_databases": {
                    db: val for db, val in ef_data["databases"].items() if db != preferred_db
                },
                "methodology_note": "Keyword-based activity matching against 40-category EF registry.",
            }

        return {
            "matched_activity": None,
            "confidence": 0.0,
            "message": "No matching emission factor found. Consider manual lookup or spend-based proxy.",
            "recommendation": "Use DEFRA 2023 spend-based EFs as fallback, or engage specialist for activity-specific data.",
            "dqs_tier": 5,
        }

    def classify_scope3_category(self, tx: Scope3TransactionInput) -> Dict[str, Any]:
        """
        Auto-classify a financial transaction into GHG Protocol Scope 3 Category 1-15.

        Uses keyword matching on description + SIC code range matching.
        Returns primary category, confidence, FLAG/non-FLAG, DQS.
        """
        desc_lower = (tx.description or "").lower()
        supplier_lower = tx.supplier_name.lower()
        combined = desc_lower + " " + supplier_lower

        scores: Dict[str, float] = {}
        for rule_key, rule in SCOPE3_CLASSIFICATION_RULES.items():
            kw_hits = sum(1 for kw in rule["keywords"] if kw in combined)
            kw_score = kw_hits / max(len(rule["keywords"]), 1)

            sic_score = 0.0
            if tx.sic_code and rule["sic_codes"]:
                if tx.sic_code in rule["sic_codes"]:
                    sic_score = 1.0
                elif any(abs(tx.sic_code - s) < 100 for s in rule["sic_codes"]):
                    sic_score = 0.4

            scores[rule_key] = kw_score * 0.7 + sic_score * 0.3

        # Sort by score descending
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if not sorted_cats or sorted_cats[0][1] == 0.0:
            # Default to C1 Purchased Goods for unclassified spend
            primary_key = "C1_purchased_goods_services"
            confidence = 0.30
        else:
            primary_key = sorted_cats[0][0]
            confidence = min(sorted_cats[0][1] * 1.2, 0.92)

        rule = SCOPE3_CLASSIFICATION_RULES[primary_key]
        flag_applicable = rule.get("flag_applicable", False) and (
            "agriculture" in combined or "food" in combined or "forest" in combined
        )

        # Assign DQS based on spend data availability
        dqs = 3
        if tx.sic_code:
            dqs = 3
        if confidence > 0.7:
            dqs = 2
        if confidence > 0.85:
            dqs = 1

        return {
            "primary_category": rule["category"],
            "category_name": rule["name"],
            "confidence": round(confidence, 3),
            "default_method": rule["default_method"],
            "flag_land_use": flag_applicable,
            "dqs_auto_assigned": dqs,
            "alternatives": [
                {
                    "category": SCOPE3_CLASSIFICATION_RULES[k]["category"],
                    "name": SCOPE3_CLASSIFICATION_RULES[k]["name"],
                    "confidence": round(v, 3),
                }
                for k, v in sorted_cats[1:4]
                if v > 0.05
            ],
            "spend_amount": tx.spend_amount,
            "currency": tx.currency,
            "note": "Auto-classification using GHG Protocol Scope 3 Standard (2011) category rules.",
        }

    def derive_dqs_score(self, metadata_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        ML-based DQS (Data Quality Score) derivation from metadata.

        Five input features:
        1. data_source: primary_measurement | supplier_specific | industry_average | spend_based | estimate
        2. verification_status: third_party_reasonable | third_party_limited | internal_review | unverified
        3. measurement_approach: direct_measurement | calculation_primary | calculation_secondary | spend_proxy
        4. coverage_pct: 0-100 (% of activity covered)
        5. recency_yrs: years since data collection (0=current year)

        Returns DQS 1-5 with rationale.
        """
        ds = metadata_input.get("data_source", "estimate")
        vs = metadata_input.get("verification_status", "unverified")
        ma = metadata_input.get("measurement_approach", "spend_proxy")
        coverage = float(metadata_input.get("coverage_pct", 50.0))
        recency = float(metadata_input.get("recency_yrs", 2.0))

        # Score each dimension 0–1 (higher = better quality)
        data_source_scores = {
            "primary_measurement": 1.0,
            "supplier_specific": 0.80,
            "industry_average": 0.55,
            "spend_based": 0.35,
            "estimate": 0.15,
        }
        ds_score = data_source_scores.get(ds, 0.20)

        verification_scores = {
            "third_party_reasonable": 1.0,
            "third_party_limited": 0.75,
            "internal_review": 0.45,
            "unverified": 0.10,
        }
        vs_score = verification_scores.get(vs, 0.10)

        measurement_scores = {
            "direct_measurement": 1.0,
            "calculation_primary": 0.80,
            "calculation_secondary": 0.55,
            "spend_proxy": 0.25,
        }
        ma_score = measurement_scores.get(ma, 0.30)

        coverage_score = coverage / 100.0
        recency_score = max(0.0, 1.0 - recency * 0.15)

        # Weighted composite
        composite = (
            ds_score * 0.30
            + vs_score * 0.25
            + ma_score * 0.25
            + coverage_score * 0.10
            + recency_score * 0.10
        )

        # Map to DQS 1-5
        if composite >= 0.80:
            dqs = 1
        elif composite >= 0.60:
            dqs = 2
        elif composite >= 0.40:
            dqs = 3
        elif composite >= 0.20:
            dqs = 4
        else:
            dqs = 5

        dqs_labels = {
            1: "Verified primary data — highest quality",
            2: "Verified or well-sourced supplier/activity data",
            3: "Industry averages or audited spend data",
            4: "Estimated or spend-based with limited verification",
            5: "Rough estimate or default factor — lowest quality",
        }

        return {
            "dqs_score": dqs,
            "dqs_label": dqs_labels[dqs],
            "composite_quality_index": round(composite, 3),
            "dimension_scores": {
                "data_source": round(ds_score, 2),
                "verification": round(vs_score, 2),
                "measurement_approach": round(ma_score, 2),
                "coverage_pct": round(coverage_score, 2),
                "recency": round(recency_score, 2),
            },
            "improvement_potential": "DQS can improve by upgrading: "
            + (f"data source (currently {ds}); " if ds_score < 0.6 else "")
            + (f"verification (currently {vs}); " if vs_score < 0.5 else "")
            + (f"measurement approach (currently {ma})" if ma_score < 0.5 else ""),
            "pcaf_reference": "PCAF Global GHG Accounting Standard Part A — DQS 1-5 criteria",
        }

    def auto_tag_xbrl(self, d: GHGDisclosureInput) -> Dict[str, Any]:
        """
        Map GHG disclosure fields to ESRS XBRL taxonomy tags.

        Returns tagged concepts, tagging confidence, mandatory/optional flags,
        and untaggable fields.
        """
        tagged: List[Dict[str, Any]] = []
        untagged: List[str] = []

        field_to_concept: Dict[str, str] = {
            "scope1_tco2e": "esrs:GrossScope1GHGEmissions",
            "scope2_location_tco2e": "esrs:GrossScope2LocationBasedGHGEmissions",
            "scope2_market_tco2e": "esrs:GrossScope2MarketBasedGHGEmissions",
            "base_year": "esrs:BaseYear",
            "consolidation_approach": "esrs:ConsolidationApproach",
            "boundary_description": "esrs:OrganisationalBoundaryDescription",
            "verification_status": "esrs:GHGVerificationStatus",
            "biogenic_emissions_tco2e": "esrs:BiogenicCarbonEmissions",
            "uncertainty_pct": "esrs:UncertaintyQuantification",
            "ghg_reduction_target_pct": "esrs:GHGAbsoluteReductionTarget",
            "target_year": "esrs:GHGReductionTargetYear",
            "sbti_status": "esrs:SBTiCommitmentStatus",
            "energy_mwh": "esrs:EnergyConsumptionTotal",
            "renewable_energy_pct": "esrs:RenewableEnergyPercentage",
        }

        for attr, concept in field_to_concept.items():
            value = getattr(d, attr, None)
            if value is not None:
                concept_meta = XBRL_ESRS_CONCEPTS.get(concept, {})
                tagged.append({
                    "field": attr,
                    "value": value,
                    "xbrl_concept": concept,
                    "label": concept_meta.get("label", ""),
                    "datatype": concept_meta.get("datatype", ""),
                    "unit": concept_meta.get("unit", ""),
                    "mandatory": concept_meta.get("mandatory", False),
                    "esrs_reference": concept_meta.get("esrs_reference", ""),
                    "tagging_confidence": 0.95,
                })
            elif XBRL_ESRS_CONCEPTS.get(concept, {}).get("mandatory"):
                untagged.append(f"{attr} → {concept} (MANDATORY — value absent)")

        # Scope 3 categories
        if d.scope3_categories:
            total_s3 = sum(d.scope3_categories.values())
            tagged.append({
                "field": "scope3_total_tco2e",
                "value": total_s3,
                "xbrl_concept": "esrs:TotalGrossScope3GHGEmissions",
                "label": "Total Gross Scope 3 GHG Emissions",
                "datatype": "xbrli:decimal",
                "unit": "Metric tons CO2 equivalent",
                "mandatory": True,
                "esrs_reference": "ESRS E1-6",
                "tagging_confidence": 0.90,
            })
            if 6 in d.scope3_categories:
                tagged.append({
                    "field": "scope3_category_6",
                    "value": d.scope3_categories[6],
                    "xbrl_concept": "esrs:Scope3Category6GHGEmissions",
                    "mandatory": False,
                    "tagging_confidence": 0.90,
                    "esrs_reference": "ESRS E1-6",
                })
            if 15 in d.scope3_categories:
                tagged.append({
                    "field": "scope3_category_15",
                    "value": d.scope3_categories[15],
                    "xbrl_concept": "esrs:Scope3Category15FinancedEmissions",
                    "mandatory": False,
                    "tagging_confidence": 0.90,
                    "esrs_reference": "ESRS E1-6",
                })

        # Compute total if S1 + S2 available
        if d.scope1_tco2e is not None and d.scope2_location_tco2e is not None:
            s3_total = sum(d.scope3_categories.values()) if d.scope3_categories else 0
            total = d.scope1_tco2e + d.scope2_location_tco2e + s3_total
            tagged.append({
                "field": "total_ghg_tco2e",
                "value": round(total, 1),
                "xbrl_concept": "esrs:TotalGHGEmissions",
                "mandatory": True,
                "tagging_confidence": 0.98,
                "esrs_reference": "ESRS E1-6",
            })

        mandatory_tagged = sum(1 for t in tagged if t.get("mandatory"))
        mandatory_total = sum(1 for c in XBRL_ESRS_CONCEPTS.values() if c["mandatory"])
        coverage_pct = round(mandatory_tagged / max(mandatory_total, 1) * 100, 1)

        return {
            "tagged_concepts": tagged,
            "untagged_mandatory": untagged,
            "mandatory_coverage_pct": coverage_pct,
            "total_tagged": len(tagged),
            "taxonomy_reference": "ESRS XBRL Digital Taxonomy 2023 (EFRAG)",
            "format": "iXBRL inline tagging ready",
        }

    def score_cdp_response(self, cdp_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score CDP Climate questionnaire responses for A-list gap analysis.

        Scores C1-C12 sections based on completeness and quality indicators.
        Returns section scores, overall band, and gaps to reach next band.
        """
        responses = cdp_input.get("responses", {})
        section_scores: Dict[str, float] = {}
        gaps: List[str] = []

        for section, meta in CDP_QUESTIONNAIRE_STRUCTURE.items():
            if section == "C0":
                continue
            weight = meta["weight"]
            if weight == 0.0:
                continue

            resp = responses.get(section, {})
            completeness = resp.get("completeness", 0.0)  # 0-1 fraction of questions answered
            quality = resp.get("quality_score", 0.0)      # 0-1 qualitative quality
            has_evidence = resp.get("has_quantitative_evidence", False)

            section_score = completeness * 0.5 + quality * 0.35 + (0.15 if has_evidence else 0.0)
            section_scores[section] = round(section_score, 3)

            if completeness < 0.8:
                unanswered = int((1 - completeness) * len(meta["questions"]))
                gaps.append(f"{section} ({meta['section']}): {unanswered} questions unanswered.")
            if quality < 0.6 and meta["mandatory"]:
                gaps.append(f"{section} ({meta['section']}): Response quality below CDP A-list threshold.")

        # Weighted overall score
        total_weight = sum(
            meta["weight"] for s, meta in CDP_QUESTIONNAIRE_STRUCTURE.items()
            if meta["weight"] > 0 and s != "C0"
        )
        weighted_score = sum(
            section_scores.get(s, 0.0) * meta["weight"]
            for s, meta in CDP_QUESTIONNAIRE_STRUCTURE.items()
            if meta["weight"] > 0 and s != "C0"
        ) / max(total_weight, 0.001)

        # CDP band assignment
        if weighted_score >= 0.90:
            band = "A"
        elif weighted_score >= 0.75:
            band = "A-"
        elif weighted_score >= 0.60:
            band = "B"
        elif weighted_score >= 0.45:
            band = "B-"
        elif weighted_score >= 0.30:
            band = "C"
        elif weighted_score >= 0.15:
            band = "D"
        else:
            band = "D-"

        return {
            "overall_score": round(weighted_score * 100, 1),
            "cdp_band": band,
            "section_scores": {k: round(v * 100, 1) for k, v in section_scores.items()},
            "gaps": gaps,
            "a_list_gap": max(0.0, round((0.90 - weighted_score) * 100, 1)),
            "priority_sections_for_improvement": [
                k for k, v in sorted(section_scores.items(), key=lambda x: x[1])[:3]
            ],
            "reference": "CDP Climate Change Questionnaire 2024 Scoring Methodology",
        }

    def analyse_data_gaps(self, d: GHGDisclosureInput) -> Dict[str, Any]:
        """
        Identify missing data fields, recommend proxy methodologies,
        estimate DQS improvement potential, and calculate materiality-weighted gap score.
        """
        gaps: List[Dict[str, Any]] = []

        # Check each field
        field_checks = [
            ("scope1_tco2e", "Scope 1 total", "direct_measurement", "high", 0.20),
            ("scope2_location_tco2e", "Scope 2 location-based", "grid_ef_calculation", "high", 0.15),
            ("scope2_market_tco2e", "Scope 2 market-based", "supplier_ef_or_rec", "medium", 0.10),
            ("scope3_categories", "Scope 3 categories", "spend_based_or_supplier", "high", 0.20),
            ("base_year", "Base year", "earliest_available", "high", 0.10),
            ("consolidation_approach", "Consolidation approach", "document_in_policy", "medium", 0.05),
            ("verification_status", "Third-party assurance", "isae3410_engagement", "medium", 0.10),
            ("biogenic_emissions_tco2e", "Biogenic CO2 emissions", "activity_based_calculation", "low", 0.03),
            ("uncertainty_pct", "Uncertainty quantification", "error_propagation", "low", 0.02),
            ("ghg_reduction_target_pct", "GHG reduction target", "sbti_or_net_zero_commitment", "medium", 0.05),
        ]

        materiality_weighted_gap = 0.0
        for attr, label, proxy_method, priority, materiality_weight in field_checks:
            value = getattr(d, attr, None)
            if value is None:
                gaps.append({
                    "field": attr,
                    "label": label,
                    "proxy_methodology": proxy_method,
                    "priority": priority,
                    "materiality_weight": materiality_weight,
                    "dqs_improvement_potential": "DQS 5→3 with proxy; DQS 3→1 with primary data",
                })
                materiality_weighted_gap += materiality_weight

        # Scope 3 category gaps
        if d.scope3_categories:
            reported_cats = set(d.scope3_categories.keys())
            critical_cats = {1, 3, 6, 7, 11, 15}
            missing_critical = critical_cats - reported_cats
            if missing_critical:
                gaps.append({
                    "field": "scope3_critical_categories",
                    "label": f"Scope 3 categories {sorted(missing_critical)} missing",
                    "proxy_methodology": "spend_based_or_industry_average",
                    "priority": "medium",
                    "materiality_weight": 0.10,
                    "dqs_improvement_potential": "DQS 4→2 with supplier engagement",
                })
                materiality_weighted_gap += 0.05

        overall_gap_score = round(materiality_weighted_gap * 100, 1)

        return {
            "identified_gaps": gaps,
            "total_gaps": len(gaps),
            "materiality_weighted_gap_score": overall_gap_score,
            "data_readiness_pct": round(max(0, 100 - overall_gap_score), 1),
            "quick_wins": [
                g["label"] for g in gaps if g["priority"] == "high"
            ][:3],
            "effort_estimate": {
                "high_priority_gaps": sum(1 for g in gaps if g["priority"] == "high"),
                "medium_priority_gaps": sum(1 for g in gaps if g["priority"] == "medium"),
                "low_priority_gaps": sum(1 for g in gaps if g["priority"] == "low"),
            },
        }

    def full_assessment(self, d: GHGDisclosureInput) -> CarbonAccountingAIResult:
        """
        Run all Carbon Accounting AI sub-modules and return a consolidated result.
        """
        ghg_compliance = self.check_ghg_compliance(d)
        xbrl_tagging = self.auto_tag_xbrl(d)
        data_gaps = self.analyse_data_gaps(d)

        cdp_input = {
            "responses": d.cdp_responses or {},
        }
        cdp_scoring = self.score_cdp_response(cdp_input)

        # Derive DQS for S1 as representative
        dqs_meta = {
            "data_source": "industry_average" if d.scope1_tco2e is None else "primary_measurement",
            "verification_status": d.verification_status or "unverified",
            "measurement_approach": "direct_measurement" if d.scope1_tco2e else "spend_proxy",
            "coverage_pct": 85 if d.scope1_tco2e else 30,
            "recency_yrs": max(0, 2025 - d.reporting_year),
        }
        dqs_score = self.derive_dqs_score(dqs_meta)

        # EF matching example for electricity (if no S1)
        ef_query = EmissionFactorQuery(
            activity_description="electricity grid consumption UK",
            quantity=1.0,
            unit="kWh",
            country="UK",
        )
        ef_matching = self.match_emission_factor(ef_query)

        # Scope3 classify example
        scope3_classification: Dict[str, Any] = {}
        if d.scope3_categories is None:
            tx = Scope3TransactionInput(
                supplier_name="Generic Supplier",
                spend_amount=100000,
                description="procurement of goods and services",
            )
            scope3_classification = self.classify_scope3_category(tx)

        # Overall readiness score
        readiness = (
            ghg_compliance["compliance_pct"] * 0.40
            + xbrl_tagging["mandatory_coverage_pct"] * 0.20
            + cdp_scoring["overall_score"] * 0.20
            + data_gaps["data_readiness_pct"] * 0.20
        ) / 100.0

        priority_actions = (
            ghg_compliance.get("recommendations", [])[:2]
            + data_gaps.get("quick_wins", [])[:2]
        )

        return CarbonAccountingAIResult(
            entity_name=d.entity_name,
            reporting_year=d.reporting_year,
            ghg_compliance=ghg_compliance,
            ef_matching=ef_matching,
            scope3_classification=scope3_classification,
            dqs_score=dqs_score,
            xbrl_tagging=xbrl_tagging,
            cdp_scoring=cdp_scoring,
            data_gaps=data_gaps,
            overall_readiness_score=round(readiness * 100, 1),
            priority_actions=priority_actions,
        )


# Module-level singleton
carbon_accounting_ai_engine = CarbonAccountingAIEngine()
