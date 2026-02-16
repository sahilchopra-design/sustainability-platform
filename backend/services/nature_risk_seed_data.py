"""
Nature Risk Seed Data
Complete ENCORE database and sample biodiversity/water risk data
"""

from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any


def get_all_encore_sectors() -> List[Dict]:
    """Get all ENCORE sectors."""
    return [
        {"code": "ENERGY", "name": "Energy", "subsectors": ["Oil & Gas", "Coal", "Renewables", "Utilities"]},
        {"code": "MINING", "name": "Mining & Metals", "subsectors": ["Coal Mining", "Metal Mining", "Quarrying"]},
        {"code": "AGRICULTURE", "name": "Agriculture", "subsectors": ["Crops", "Livestock", "Forestry", "Fishing"]},
        {"code": "FOOD", "name": "Food & Beverages", "subsectors": ["Food Processing", "Beverages", "Tobacco"]},
        {"code": "FINANCE", "name": "Financial Services", "subsectors": ["Banking", "Insurance", "Asset Management"]},
        {"code": "PHARMA", "name": "Pharmaceuticals", "subsectors": ["Drug Manufacturing", "Biotech"]},
        {"code": "CHEMICALS", "name": "Chemicals", "subsectors": ["Basic Chemicals", "Specialty Chemicals", "Fertilizers"]},
        {"code": "CONSTRUCTION", "name": "Construction", "subsectors": ["Building Construction", "Infrastructure"]},
        {"code": "TRANSPORT", "name": "Transportation", "subsectors": ["Road", "Rail", "Air", "Shipping"]},
        {"code": "RETAIL", "name": "Retail & Consumer", "subsectors": ["Food Retail", "General Retail"]},
        {"code": "TEXTILE", "name": "Textiles & Apparel", "subsectors": ["Fiber Production", "Garment Manufacturing"]},
        {"code": "PAPER", "name": "Paper & Forestry", "subsectors": ["Pulp & Paper", "Wood Products"]},
        {"code": "TOURISM", "name": "Tourism & Hospitality", "subsectors": ["Hotels", "Recreation", "Travel"]},
        {"code": "TECH", "name": "Technology", "subsectors": ["Hardware", "Software", "Semiconductors"]},
        {"code": "TELECOM", "name": "Telecommunications", "subsectors": ["Fixed Line", "Mobile", "Infrastructure"]},
        {"code": "REAL_ESTATE", "name": "Real Estate", "subsectors": ["Commercial", "Residential", "Industrial"]},
        {"code": "HEALTHCARE", "name": "Healthcare", "subsectors": ["Hospitals", "Medical Devices", "Services"]},
        {"code": "UTILITIES", "name": "Utilities", "subsectors": ["Electric", "Gas", "Water"]}
    ]


def get_encore_dependencies_by_sector(sector_code: str) -> List[Dict]:
    """Get ENCORE dependencies for a specific sector."""
    
    # Complete ENCORE dependency database
    encore_database = {
        "ENERGY": [
            {"id": str(uuid4()), "sector_code": "ENERGY", "sector_name": "Energy", "subsector_code": "OIL_GAS", "subsector_name": "Oil & Gas Extraction",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Water for drilling, hydraulic fracturing, and processing", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "ENERGY", "sector_name": "Energy", "subsector_code": "OIL_GAS", "subsector_name": "Oil & Gas Extraction",
             "ecosystem_service": "climate_regulation", "dependency_type": "indirect", "dependency_score": 3, "dependency_description": "Stable climate for operations", "data_quality": "medium"},
            {"id": str(uuid4()), "sector_code": "ENERGY", "sector_name": "Energy", "subsector_code": "COAL", "subsector_name": "Coal Mining",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Water for coal washing and dust suppression", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "ENERGY", "sector_name": "Energy", "subsector_code": "COAL", "subsector_name": "Coal Mining",
             "ecosystem_service": "soil_quality", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Land stability for mining operations", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "ENERGY", "sector_name": "Energy", "subsector_code": "UTILITIES", "subsector_name": "Electric Utilities",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Cooling water for thermal power plants", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "ENERGY", "sector_name": "Energy", "subsector_code": "UTILITIES", "subsector_name": "Electric Utilities",
             "ecosystem_service": "flood_protection", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Protection of power infrastructure", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "ENERGY", "sector_name": "Energy", "subsector_code": "RENEWABLES", "subsector_name": "Renewable Energy",
             "ecosystem_service": "climate_regulation", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Predictable weather patterns for solar/wind", "data_quality": "high"},
        ],
        "MINING": [
            {"id": str(uuid4()), "sector_code": "MINING", "sector_name": "Mining & Metals", "subsector_code": "METAL", "subsector_name": "Metal Mining",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Water for ore processing and dust control", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "MINING", "sector_name": "Mining & Metals", "subsector_code": "METAL", "subsector_name": "Metal Mining",
             "ecosystem_service": "soil_quality", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Stable ground conditions for mining", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "MINING", "sector_name": "Mining & Metals", "subsector_code": "METAL", "subsector_name": "Metal Mining",
             "ecosystem_service": "flood_protection", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Protection from flooding in open pits", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "MINING", "sector_name": "Mining & Metals", "subsector_code": "QUARRY", "subsector_name": "Quarrying",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Water for dust suppression and processing", "data_quality": "medium"},
        ],
        "AGRICULTURE": [
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "CROPS", "subsector_name": "Crop Production",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Irrigation water for crop growth", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "CROPS", "subsector_name": "Crop Production",
             "ecosystem_service": "pollination", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Pollination services for fruit and vegetable crops", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "CROPS", "subsector_name": "Crop Production",
             "ecosystem_service": "soil_quality", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Fertile soil for crop production", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "CROPS", "subsector_name": "Crop Production",
             "ecosystem_service": "climate_regulation", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Stable climate for growing seasons", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "CROPS", "subsector_name": "Crop Production",
             "ecosystem_service": "disease_control", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Natural pest control services", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "LIVESTOCK", "subsector_name": "Livestock",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Drinking water and pasture irrigation", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "LIVESTOCK", "subsector_name": "Livestock",
             "ecosystem_service": "genetic_resources", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Genetic diversity in livestock breeds", "data_quality": "medium"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "FORESTRY", "subsector_name": "Forestry",
             "ecosystem_service": "climate_regulation", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Climate stability for forest growth", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "FISHING", "subsector_name": "Fishing",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Clean water for aquaculture and wild fisheries", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "AGRICULTURE", "sector_name": "Agriculture", "subsector_code": "FISHING", "subsector_name": "Fishing",
             "ecosystem_service": "habitat", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Marine and freshwater habitats for fish populations", "data_quality": "high"},
        ],
        "FOOD": [
            {"id": str(uuid4()), "sector_code": "FOOD", "sector_name": "Food & Beverages", "subsector_code": "PROCESSING", "subsector_name": "Food Processing",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Water for processing and cleaning", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "FOOD", "sector_name": "Food & Beverages", "subsector_code": "BEVERAGES", "subsector_name": "Beverages",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "High-quality water as ingredient and for processing", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "FOOD", "sector_name": "Food & Beverages", "subsector_code": "PROCESSING", "subsector_name": "Food Processing",
             "ecosystem_service": "genetic_resources", "dependency_type": "indirect", "dependency_score": 3, "dependency_description": "Genetic diversity in food crops", "data_quality": "medium"},
        ],
        "FINANCE": [
            {"id": str(uuid4()), "sector_code": "FINANCE", "sector_name": "Financial Services", "subsector_code": "BANKING", "subsector_name": "Banking",
             "ecosystem_service": "water", "dependency_type": "indirect", "dependency_score": 3, "dependency_description": "Water dependencies through lending portfolio", "data_quality": "medium"},
            {"id": str(uuid4()), "sector_code": "FINANCE", "sector_name": "Financial Services", "subsector_code": "BANKING", "subsector_name": "Banking",
             "ecosystem_service": "climate_regulation", "dependency_type": "indirect", "dependency_score": 4, "dependency_description": "Climate stability affects loan portfolio", "data_quality": "medium"},
            {"id": str(uuid4()), "sector_code": "FINANCE", "sector_name": "Financial Services", "subsector_code": "INSURANCE", "subsector_name": "Insurance",
             "ecosystem_service": "flood_protection", "dependency_type": "indirect", "dependency_score": 5, "dependency_description": "Natural flood protection reduces claims", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "FINANCE", "sector_name": "Financial Services", "subsector_code": "INSURANCE", "subsector_name": "Insurance",
             "ecosystem_service": "climate_regulation", "dependency_type": "indirect", "dependency_score": 5, "dependency_description": "Climate stability affects underwriting", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "FINANCE", "sector_name": "Financial Services", "subsector_code": "ASSET_MGMT", "subsector_name": "Asset Management",
             "ecosystem_service": "water", "dependency_type": "indirect", "dependency_score": 3, "dependency_description": "Water dependencies in portfolio companies", "data_quality": "medium"},
        ],
        "PHARMA": [
            {"id": str(uuid4()), "sector_code": "PHARMA", "sector_name": "Pharmaceuticals", "subsector_code": "DRUG", "subsector_name": "Drug Manufacturing",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Ultra-pure water for drug production", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "PHARMA", "sector_name": "Pharmaceuticals", "subsector_code": "DRUG", "subsector_name": "Drug Manufacturing",
             "ecosystem_service": "genetic_resources", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Natural compounds for drug discovery", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "PHARMA", "sector_name": "Pharmaceuticals", "subsector_code": "BIOTECH", "subsector_name": "Biotechnology",
             "ecosystem_service": "genetic_resources", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Genetic material for biotech research", "data_quality": "high"},
        ],
        "CHEMICALS": [
            {"id": str(uuid4()), "sector_code": "CHEMICALS", "sector_name": "Chemicals", "subsector_code": "BASIC", "subsector_name": "Basic Chemicals",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Water for chemical processing and cooling", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "CHEMICALS", "sector_name": "Chemicals", "subsector_code": "FERTILIZER", "subsector_name": "Fertilizers",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Water for fertilizer production", "data_quality": "high"},
        ],
        "CONSTRUCTION": [
            {"id": str(uuid4()), "sector_code": "CONSTRUCTION", "sector_name": "Construction", "subsector_code": "BUILDING", "subsector_name": "Building Construction",
             "ecosystem_service": "timber", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Wood and timber for construction", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "CONSTRUCTION", "sector_name": "Construction", "subsector_code": "BUILDING", "subsector_name": "Building Construction",
             "ecosystem_service": "soil_quality", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Stable soil for foundations", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "CONSTRUCTION", "sector_name": "Construction", "subsector_code": "INFRA", "subsector_name": "Infrastructure",
             "ecosystem_service": "flood_protection", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Flood protection for infrastructure", "data_quality": "high"},
        ],
        "TRANSPORT": [
            {"id": str(uuid4()), "sector_code": "TRANSPORT", "sector_name": "Transportation", "subsector_code": "SHIPPING", "subsector_name": "Shipping",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Navigable waterways for shipping", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "TRANSPORT", "sector_name": "Transportation", "subsector_code": "SHIPPING", "subsector_name": "Shipping",
             "ecosystem_service": "climate_regulation", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Stable weather for shipping routes", "data_quality": "high"},
        ],
        "RETAIL": [
            {"id": str(uuid4()), "sector_code": "RETAIL", "sector_name": "Retail & Consumer", "subsector_code": "FOOD_RETAIL", "subsector_name": "Food Retail",
             "ecosystem_service": "pollination", "dependency_type": "indirect", "dependency_score": 4, "dependency_description": "Pollination for food supply chain", "data_quality": "medium"},
            {"id": str(uuid4()), "sector_code": "RETAIL", "sector_name": "Retail & Consumer", "subsector_code": "FOOD_RETAIL", "subsector_name": "Food Retail",
             "ecosystem_service": "water", "dependency_type": "indirect", "dependency_score": 4, "dependency_description": "Water for food production in supply chain", "data_quality": "medium"},
        ],
        "TEXTILE": [
            {"id": str(uuid4()), "sector_code": "TEXTILE", "sector_name": "Textiles & Apparel", "subsector_code": "FIBER", "subsector_name": "Fiber Production",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Water for cotton and fiber processing", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "TEXTILE", "sector_name": "Textiles & Apparel", "subsector_code": "FIBER", "subsector_name": "Fiber Production",
             "ecosystem_service": "soil_quality", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Soil for cotton cultivation", "data_quality": "high"},
        ],
        "PAPER": [
            {"id": str(uuid4()), "sector_code": "PAPER", "sector_name": "Paper & Forestry", "subsector_code": "PULP", "subsector_name": "Pulp & Paper",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Water for pulp production", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "PAPER", "sector_name": "Paper & Forestry", "subsector_code": "PULP", "subsector_name": "Pulp & Paper",
             "ecosystem_service": "timber", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Wood fiber for paper production", "data_quality": "high"},
        ],
        "TOURISM": [
            {"id": str(uuid4()), "sector_code": "TOURISM", "sector_name": "Tourism & Hospitality", "subsector_code": "HOTELS", "subsector_name": "Hotels",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Water for hotel operations", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "TOURISM", "sector_name": "Tourism & Hospitality", "subsector_code": "RECREATION", "subsector_name": "Recreation",
             "ecosystem_service": "habitat", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Natural habitats attract tourists", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "TOURISM", "sector_name": "Tourism & Hospitality", "subsector_code": "RECREATION", "subsector_name": "Recreation",
             "ecosystem_service": "climate_regulation", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Stable climate for tourism seasons", "data_quality": "high"},
        ],
        "TECH": [
            {"id": str(uuid4()), "sector_code": "TECH", "sector_name": "Technology", "subsector_code": "HARDWARE", "subsector_name": "Hardware",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Ultra-pure water for semiconductor manufacturing", "data_quality": "high"},
        ],
        "TELECOM": [
            {"id": str(uuid4()), "sector_code": "TELECOM", "sector_name": "Telecommunications", "subsector_code": "INFRA", "subsector_name": "Infrastructure",
             "ecosystem_service": "flood_protection", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Protection of telecom infrastructure", "data_quality": "high"},
        ],
        "REAL_ESTATE": [
            {"id": str(uuid4()), "sector_code": "REAL_ESTATE", "sector_name": "Real Estate", "subsector_code": "COMMERCIAL", "subsector_name": "Commercial",
             "ecosystem_service": "flood_protection", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Flood protection for property values", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "REAL_ESTATE", "sector_name": "Real Estate", "subsector_code": "COMMERCIAL", "subsector_name": "Commercial",
             "ecosystem_service": "air_quality", "dependency_type": "direct", "dependency_score": 3, "dependency_description": "Air quality affects property values", "data_quality": "medium"},
        ],
        "HEALTHCARE": [
            {"id": str(uuid4()), "sector_code": "HEALTHCARE", "sector_name": "Healthcare", "subsector_code": "HOSPITALS", "subsector_name": "Hospitals",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Clean water for medical operations", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "HEALTHCARE", "sector_name": "Healthcare", "subsector_code": "HOSPITALS", "subsector_name": "Hospitals",
             "ecosystem_service": "air_quality", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Clean air for patient health", "data_quality": "high"},
        ],
        "UTILITIES": [
            {"id": str(uuid4()), "sector_code": "UTILITIES", "sector_name": "Utilities", "subsector_code": "WATER", "subsector_name": "Water Utilities",
             "ecosystem_service": "water", "dependency_type": "direct", "dependency_score": 5, "dependency_description": "Source water for treatment and distribution", "data_quality": "high"},
            {"id": str(uuid4()), "sector_code": "UTILITIES", "sector_name": "Utilities", "subsector_code": "WATER", "subsector_name": "Water Utilities",
             "ecosystem_service": "climate_regulation", "dependency_type": "direct", "dependency_score": 4, "dependency_description": "Precipitation patterns affect water supply", "data_quality": "high"},
        ]
    }
    
    return encore_database.get(sector_code, [])


def get_default_scenarios() -> List[Dict]:
    """Get default nature risk scenarios."""
    return [
        {
            "id": "scenario-tnfd-current",
            "name": "TNFD Current Trajectory",
            "description": "Business as usual scenario with continued biodiversity decline",
            "scenario_type": "combined",
            "framework": "TNFD",
            "temperature_c": 3.0,
            "precipitation_change_percent": -5.0,
            "biodiversity_trend": "decline",
            "policy_stringency": "low",
            "water_scarcity_index": 3.5,
            "ecosystem_degradation_rate": 0.03,
            "assumptions": {
                "land_use_change": "continued_conversion",
                "pollution_levels": "increasing",
                "overexploitation": "continued"
            },
            "is_active": True
        },
        {
            "id": "scenario-tnfd-sustainable",
            "name": "TNFD Sustainable Pathway",
            "description": "Scenario with strong nature protection and restoration",
            "scenario_type": "combined",
            "framework": "TNFD",
            "temperature_c": 1.8,
            "precipitation_change_percent": -2.0,
            "biodiversity_trend": "recovery",
            "policy_stringency": "high",
            "water_scarcity_index": 2.0,
            "ecosystem_degradation_rate": 0.005,
            "assumptions": {
                "land_use_change": "restoration_focus",
                "pollution_levels": "decreasing",
                "overexploitation": "sustainable_management"
            },
            "is_active": True
        },
        {
            "id": "scenario-ncore-physical",
            "name": "NCORE Physical Risk",
            "description": "Focus on physical nature risks including water scarcity and ecosystem collapse",
            "scenario_type": "physical",
            "framework": "NCORE",
            "temperature_c": 2.5,
            "precipitation_change_percent": -10.0,
            "biodiversity_trend": "decline",
            "policy_stringency": "medium",
            "water_scarcity_index": 4.0,
            "ecosystem_degradation_rate": 0.04,
            "assumptions": {
                "extreme_weather_frequency": "increasing",
                "ecosystem_tipping_points": "possible",
                "water_availability": "decreasing"
            },
            "is_active": True
        },
        {
            "id": "scenario-ncore-transition",
            "name": "NCORE Transition Risk",
            "description": "Focus on transition risks from nature policy and market changes",
            "scenario_type": "transition",
            "framework": "NCORE",
            "temperature_c": 2.0,
            "precipitation_change_percent": -3.0,
            "biodiversity_trend": "stable",
            "policy_stringency": "high",
            "water_scarcity_index": 2.5,
            "ecosystem_degradation_rate": 0.01,
            "assumptions": {
                "carbon_pricing": "aggressive",
                "biodiversity_offsets": "mandatory",
                "supply_chain_requirements": "strict"
            },
            "is_active": True
        },
        {
            "id": "scenario-ipbes-ssp1",
            "name": "IPBES SSP1 - Sustainability",
            "description": "IPBES Shared Socioeconomic Pathway 1 - Taking the Green Road",
            "scenario_type": "combined",
            "framework": "custom",
            "temperature_c": 1.5,
            "precipitation_change_percent": -1.0,
            "biodiversity_trend": "recovery",
            "policy_stringency": "high",
            "water_scarcity_index": 1.8,
            "ecosystem_degradation_rate": 0.002,
            "assumptions": {
                "inequality": "low",
                "consumption": "sustainable",
                "technology": "green_innovation"
            },
            "is_active": True
        },
        {
            "id": "scenario-ipbes-ssp3",
            "name": "IPBES SSP3 - Regional Rivalry",
            "description": "IPBES Shared Socioeconomic Pathway 3 - A Rocky Road",
            "scenario_type": "combined",
            "framework": "custom",
            "temperature_c": 3.5,
            "precipitation_change_percent": -15.0,
            "biodiversity_trend": "decline",
            "policy_stringency": "low",
            "water_scarcity_index": 4.5,
            "ecosystem_degradation_rate": 0.05,
            "assumptions": {
                "inequality": "high",
                "consumption": "resource_intensive",
                "cooperation": "limited"
            },
            "is_active": True
        }
    ]


def get_sample_biodiversity_sites() -> List[Dict]:
    """Get sample biodiversity sites from WDPA, KBA, Ramsar, etc."""
    return [
        # Amazon - World Heritage Sites
        {"id": str(uuid4()), "site_name": "Central Amazon Conservation Complex", "site_type": "world_heritage",
         "country_code": "BR", "latitude": -3.4653, "longitude": -62.2159, "area_km2": 60000,
         "designation_year": 2000, "iucn_category": "II", "ecosystem_type": "tropical_forest",
         "key_species": ["jaguar", "giant_otter", "harpy_eagle"], "data_source": "WDPA"},
        {"id": str(uuid4()), "site_name": "Manu National Park", "site_type": "world_heritage",
         "country_code": "PE", "latitude": -11.8333, "longitude": -71.5833, "area_km2": 15328,
         "designation_year": 1987, "iucn_category": "II", "ecosystem_type": "tropical_forest",
         "key_species": ["giant_otter", "spectacled_bear", "cock_of_the_rock"], "data_source": "WDPA"},
        
        # Ramsar Wetlands
        {"id": str(uuid4()), "site_name": "Pantanal Matogrossense", "site_type": "ramsar",
         "country_code": "BR", "latitude": -17.8333, "longitude": -57.4167, "area_km2": 135000,
         "designation_year": 1993, "ecosystem_type": "wetland",
         "key_species": ["giant_anteater", "marsh_deer", "hyacinth_macaw"], "data_source": "Ramsar"},
        {"id": str(uuid4()), "site_name": "Okavango Delta", "site_type": "ramsar",
         "country_code": "BW", "latitude": -19.5000, "longitude": 22.5000, "area_km2": 20000,
         "designation_year": 1996, "ecosystem_type": "wetland",
         "key_species": ["african_elephant", "lion", "hippopotamus"], "data_source": "Ramsar"},
        {"id": str(uuid4()), "site_name": "Sundarbans", "site_type": "ramsar",
         "country_code": "BD", "latitude": 21.9497, "longitude": 89.1833, "area_km2": 6017,
         "designation_year": 1992, "ecosystem_type": "mangrove",
         "key_species": ["bengal_tiger", "saltwater_crocodile", "ganges_dolphin"], "data_source": "Ramsar"},
        
        # Key Biodiversity Areas
        {"id": str(uuid4()), "site_name": "Atlantic Forest Biodiversity Hotspot", "site_type": "key_biodiversity_area",
         "country_code": "BR", "latitude": -23.5505, "longitude": -46.6333, "area_km2": 148000,
         "designation_year": 2004, "ecosystem_type": "tropical_forest",
         "key_species": ["golden_lion_tamarin", "muriqui", "toucan"], "data_source": "KBA"},
        {"id": str(uuid4()), "site_name": "Western Ghats", "site_type": "key_biodiversity_area",
         "country_code": "IN", "latitude": 10.0000, "longitude": 77.0000, "area_km2": 160000,
         "designation_year": 2012, "ecosystem_type": "tropical_forest",
         "key_species": ["lion_tailed_macaque", "nilgiri_tahr", "malabar_giant_squirrel"], "data_source": "KBA"},
        {"id": str(uuid4()), "site_name": "Coral Triangle", "site_type": "key_biodiversity_area",
         "country_code": "ID", "latitude": -2.5000, "longitude": 128.0000, "area_km2": 600000,
         "designation_year": 2009, "ecosystem_type": "marine",
         "key_species": ["whale_shark", "manta_ray", "dugong"], "data_source": "KBA"},
        
        # Protected Areas
        {"id": str(uuid4()), "site_name": "Serengeti National Park", "site_type": "protected_area",
         "country_code": "TZ", "latitude": -2.3333, "longitude": 34.8333, "area_km2": 14763,
         "designation_year": 1951, "iucn_category": "II", "ecosystem_type": "savanna",
         "key_species": ["lion", "elephant", "wildebeest"], "data_source": "WDPA"},
        {"id": str(uuid4()), "site_name": "Great Barrier Reef Marine Park", "site_type": "protected_area",
         "country_code": "AU", "latitude": -18.2871, "longitude": 147.6992, "area_km2": 344400,
         "designation_year": 1975, "iucn_category": "VI", "ecosystem_type": "marine",
         "key_species": ["dugong", "green_turtle", "humpback_whale"], "data_source": "WDPA"},
        {"id": str(uuid4()), "site_name": "Yellowstone National Park", "site_type": "protected_area",
         "country_code": "US", "latitude": 44.4280, "longitude": -110.5885, "area_km2": 8983,
         "designation_year": 1872, "iucn_category": "II", "ecosystem_type": "temperate_forest",
         "key_species": ["grizzly_bear", "wolf", "bison"], "data_source": "WDPA"},
        {"id": str(uuid4()), "site_name": "Galápagos National Park", "site_type": "protected_area",
         "country_code": "EC", "latitude": -0.9538, "longitude": -90.9656, "area_km2": 7995,
         "designation_year": 1959, "iucn_category": "II", "ecosystem_type": "marine",
         "key_species": ["giant_tortoise", "marine_iguana", "blue_footed_booby"], "data_source": "WDPA"},
        
        # Important Bird Areas
        {"id": str(uuid4()), "site_name": "Doñana", "site_type": "iba",
         "country_code": "ES", "latitude": 36.9833, "longitude": -6.4500, "area_km2": 543,
         "designation_year": 1980, "ecosystem_type": "wetland",
         "key_species": ["spanish_imperial_eagle", "greater_flamingo", "eurasian_spoonbill"], "data_source": "BirdLife"},
        {"id": str(uuid4()), "site_name": "Kakadu", "site_type": "iba",
         "country_code": "AU", "latitude": -12.6728, "longitude": 132.8906, "area_km2": 19804,
         "designation_year": 1981, "ecosystem_type": "wetland",
         "key_species": ["magpie_goose", "brolga", "black_necked_stork"], "data_source": "BirdLife"},
        
        # Additional sites for global coverage
        {"id": str(uuid4()), "site_name": "Borneo Rainforest", "site_type": "key_biodiversity_area",
         "country_code": "MY", "latitude": 4.5000, "longitude": 117.5000, "area_km2": 730000,
         "designation_year": 2010, "ecosystem_type": "tropical_forest",
         "key_species": ["orangutan", "clouded_leopard", "proboscis_monkey"], "data_source": "KBA"},
        {"id": str(uuid4()), "site_name": "Congo Basin", "site_type": "key_biodiversity_area",
         "country_code": "CD", "latitude": 0.0000, "longitude": 25.0000, "area_km2": 2000000,
         "designation_year": 2008, "ecosystem_type": "tropical_forest",
         "key_species": ["gorilla", "forest_elephant", "bonobo"], "data_source": "KBA"},
        {"id": str(uuid4()), "site_name": "Madagascar Rainforest", "site_type": "key_biodiversity_area",
         "country_code": "MG", "latitude": -18.7669, "longitude": 46.8691, "area_km2": 120000,
         "designation_year": 2007, "ecosystem_type": "tropical_forest",
         "key_species": ["lemur", "fossa", "aye_aye"], "data_source": "KBA"},
    ]


def get_sample_water_risk_locations() -> List[Dict]:
    """Get sample water risk locations with Aqueduct data."""
    return [
        # High water stress regions
        {"id": "water-loc-001", "location_name": "Gujarat Power Plant", "location_type": "power_plant",
         "country_code": "IN", "latitude": 21.1702, "longitude": 72.8311, "basin_name": "Sabarmati",
         "baseline_water_stress": 4.5, "groundwater_table_decline": 3.8, "drought_risk": 4.2,
         "flood_risk": 2.0, "interannual_variability": 3.5, "seasonal_variability": 4.0,
         "projected_water_stress_2030": 4.7, "projected_water_stress_2040": 4.9, "projected_water_stress_2050": 5.0,
         "annual_water_withdrawal_m3": 50000000, "water_source_type": "groundwater", "linked_asset_type": "power_plant"},
        
        {"id": "water-loc-002", "location_name": "Atacama Mining Complex", "location_type": "mine",
         "country_code": "CL", "latitude": -23.6345, "longitude": -70.3947, "basin_name": "Atacama Desert",
         "baseline_water_stress": 5.0, "groundwater_table_decline": 4.5, "drought_risk": 4.8,
         "flood_risk": 1.0, "interannual_variability": 2.0, "seasonal_variability": 2.5,
         "projected_water_stress_2030": 5.0, "projected_water_stress_2040": 5.0, "projected_water_stress_2050": 5.0,
         "annual_water_withdrawal_m3": 30000000, "water_source_type": "desalinated", "linked_asset_type": "mine"},
        
        {"id": "water-loc-003", "location_name": "Middle East Refinery", "location_type": "refinery",
         "country_code": "SA", "latitude": 26.4207, "longitude": 50.0888, "basin_name": "Persian Gulf",
         "baseline_water_stress": 5.0, "groundwater_table_decline": 4.0, "drought_risk": 4.5,
         "flood_risk": 1.5, "interannual_variability": 1.5, "seasonal_variability": 2.0,
         "projected_water_stress_2030": 5.0, "projected_water_stress_2040": 5.0, "projected_water_stress_2050": 5.0,
         "annual_water_withdrawal_m3": 80000000, "water_source_type": "desalinated", "linked_asset_type": "refinery"},
        
        # Medium water stress regions
        {"id": "water-loc-004", "location_name": "Texas Shale Operations", "location_type": "facility",
         "country_code": "US", "latitude": 31.9686, "longitude": -99.9018, "basin_name": "Colorado River",
         "baseline_water_stress": 3.5, "groundwater_table_decline": 3.0, "drought_risk": 3.8,
         "flood_risk": 2.5, "interannual_variability": 3.0, "seasonal_variability": 3.2,
         "projected_water_stress_2030": 3.8, "projected_water_stress_2040": 4.2, "projected_water_stress_2050": 4.5,
         "annual_water_withdrawal_m3": 25000000, "water_source_type": "groundwater", "linked_asset_type": "facility"},
        
        {"id": "water-loc-005", "location_name": "Australian Coal Mine", "location_type": "mine",
         "country_code": "AU", "latitude": -23.7000, "longitude": 148.1500, "basin_name": "Fitzroy Basin",
         "baseline_water_stress": 2.8, "groundwater_table_decline": 2.5, "drought_risk": 3.5,
         "flood_risk": 3.0, "interannual_variability": 3.5, "seasonal_variability": 3.0,
         "projected_water_stress_2030": 3.2, "projected_water_stress_2040": 3.5, "projected_water_stress_2050": 3.8,
         "annual_water_withdrawal_m3": 20000000, "water_source_type": "surface", "linked_asset_type": "mine"},
        
        {"id": "water-loc-006", "location_name": "South African Gold Mine", "location_type": "mine",
         "country_code": "ZA", "latitude": -26.2041, "longitude": 28.0473, "basin_name": "Witwatersrand",
         "baseline_water_stress": 3.2, "groundwater_table_decline": 2.8, "drought_risk": 3.0,
         "flood_risk": 2.0, "interannual_variability": 2.5, "seasonal_variability": 3.0,
         "projected_water_stress_2030": 3.5, "projected_water_stress_2040": 3.8, "projected_water_stress_2050": 4.0,
         "annual_water_withdrawal_m3": 35000000, "water_source_type": "surface", "linked_asset_type": "mine"},
        
        # Low water stress regions
        {"id": "water-loc-007", "location_name": "Norwegian Hydro Plant", "location_type": "power_plant",
         "country_code": "NO", "latitude": 60.3913, "longitude": 5.3221, "basin_name": "Western Norway",
         "baseline_water_stress": 0.5, "groundwater_table_decline": 0.3, "drought_risk": 0.5,
         "flood_risk": 2.5, "interannual_variability": 1.5, "seasonal_variability": 2.0,
         "projected_water_stress_2030": 0.6, "projected_water_stress_2040": 0.7, "projected_water_stress_2050": 0.8,
         "annual_water_withdrawal_m3": 100000000, "water_source_type": "surface", "linked_asset_type": "power_plant"},
        
        {"id": "water-loc-008", "location_name": "Canadian Oil Sands", "location_type": "facility",
         "country_code": "CA", "latitude": 56.7267, "longitude": -111.3790, "basin_name": "Athabasca",
         "baseline_water_stress": 1.2, "groundwater_table_decline": 1.0, "drought_risk": 1.5,
         "flood_risk": 2.0, "interannual_variability": 2.0, "seasonal_variability": 2.5,
         "projected_water_stress_2030": 1.4, "projected_water_stress_2040": 1.6, "projected_water_stress_2050": 1.8,
         "annual_water_withdrawal_m3": 150000000, "water_source_type": "surface", "linked_asset_type": "facility"},
        
        {"id": "water-loc-009", "location_name": "Brazilian Sugar Mill", "location_type": "facility",
         "country_code": "BR", "latitude": -21.1775, "longitude": -47.8103, "basin_name": "Paraná",
         "baseline_water_stress": 1.8, "groundwater_table_decline": 1.5, "drought_risk": 2.0,
         "flood_risk": 2.5, "interannual_variability": 2.5, "seasonal_variability": 3.0,
         "projected_water_stress_2030": 2.0, "projected_water_stress_2040": 2.3, "projected_water_stress_2050": 2.5,
         "annual_water_withdrawal_m3": 40000000, "water_source_type": "surface", "linked_asset_type": "facility"},
        
        # Flood risk regions
        {"id": "water-loc-010", "location_name": "Bangladesh Textile Factory", "location_type": "facility",
         "country_code": "BD", "latitude": 23.8103, "longitude": 90.4125, "basin_name": "Ganges-Brahmaputra",
         "baseline_water_stress": 2.0, "groundwater_table_decline": 3.5, "drought_risk": 2.0,
         "flood_risk": 5.0, "interannual_variability": 4.0, "seasonal_variability": 4.5,
         "projected_water_stress_2030": 2.5, "projected_water_stress_2040": 3.0, "projected_water_stress_2050": 3.5,
         "annual_water_withdrawal_m3": 15000000, "water_source_type": "surface", "linked_asset_type": "facility"},
    ]
