"""
Corporate Nature Strategy & SBTN Engine — E80
==============================================
Comprehensive nature strategy assessment covering SBTN 5-step framework,
TNFD v1.0 disclosure requirements, EU Nature Restoration Law 2024/1991,
GBF Target 3 (30x30) exposure, and ENCORE ecosystem service dependencies.

Sub-modules:
  1. SBTN 5-Step Assessment — Science Based Targets for Nature
  2. TNFD Disclosure Scoring — Taskforce on Nature-related Financial Disclosures v1.0
  3. EU NRL Exposure — Nature Restoration Law (EU) 2024/1991 habitat obligations
  4. GBF Target 3 Mapping — Convention on Biological Diversity 30x30 global target
  5. ENCORE Dependency Matrix — Natural Capital Finance Alliance ecosystem services
  6. Full Assessment Orchestrator — weighted composite nature strategy score

References:
  - SBTN Step Guidance v1.1 (2023) — Science Based Targets Network
  - TNFD Recommendations and Guidance v1.0 (Sep 2023)
  - Regulation (EU) 2024/1991 — Nature Restoration Law, Official Journal L 2024/1991
  - CBD Kunming-Montreal Global Biodiversity Framework Target 3 (Dec 2022)
  - ENCORE v2.1 — Natural Capital Finance Alliance / UNEP-WCMC (2023)
  - EU Biodiversity Strategy 2030 — Annex biodiversity targets
  - TNFD LEAP approach — Locate, Evaluate, Assess, Prepare

Composite score weights:
  SBTN 35% + TNFD 30% + NRL 15% + GBF 10% + ENCORE 10%
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reference Data — SBTN Sector Impact Map (11 sectors)
# ---------------------------------------------------------------------------

SBTN_SECTOR_IMPACT_MAP: Dict[str, Dict[str, Any]] = {
    "food_and_beverage": {
        "description": "Food production, processing and beverages",
        "primary_impact_drivers": ["land_use", "water_extraction", "pollution", "overexploitation"],
        "secondary_impact_drivers": ["climate_change", "invasive_species"],
        "high_impact": True,
        "sbtn_priority": "tier_1",
        "key_ecosystems": ["tropical_forests", "freshwater", "grasslands", "coastal"],
    },
    "agriculture_and_forestry": {
        "description": "Crop and livestock farming, silviculture, fishing",
        "primary_impact_drivers": ["land_use", "water_extraction", "pollution", "overexploitation", "invasive_species"],
        "secondary_impact_drivers": ["climate_change"],
        "high_impact": True,
        "sbtn_priority": "tier_1",
        "key_ecosystems": ["tropical_forests", "temperate_forests", "freshwater", "grasslands"],
    },
    "mining_and_materials": {
        "description": "Metal mining, quarrying, materials processing",
        "primary_impact_drivers": ["land_use", "pollution", "water_extraction"],
        "secondary_impact_drivers": ["climate_change", "invasive_species"],
        "high_impact": True,
        "sbtn_priority": "tier_1",
        "key_ecosystems": ["terrestrial_ecosystems", "freshwater", "marine"],
    },
    "energy": {
        "description": "Oil & gas, electricity generation, energy distribution",
        "primary_impact_drivers": ["land_use", "pollution", "climate_change"],
        "secondary_impact_drivers": ["water_extraction", "overexploitation"],
        "high_impact": True,
        "sbtn_priority": "tier_1",
        "key_ecosystems": ["terrestrial_ecosystems", "freshwater", "marine", "coastal"],
    },
    "chemicals": {
        "description": "Chemical manufacturing, specialty chemicals, agrochemicals",
        "primary_impact_drivers": ["pollution", "water_extraction"],
        "secondary_impact_drivers": ["land_use", "climate_change"],
        "high_impact": True,
        "sbtn_priority": "tier_2",
        "key_ecosystems": ["freshwater", "marine", "terrestrial_ecosystems"],
    },
    "construction_and_real_estate": {
        "description": "Building construction, infrastructure, real estate management",
        "primary_impact_drivers": ["land_use", "pollution"],
        "secondary_impact_drivers": ["water_extraction", "climate_change"],
        "high_impact": True,
        "sbtn_priority": "tier_2",
        "key_ecosystems": ["terrestrial_ecosystems", "urban_green_spaces", "freshwater"],
    },
    "transportation": {
        "description": "Road, rail, aviation, maritime transport",
        "primary_impact_drivers": ["land_use", "pollution", "climate_change", "invasive_species"],
        "secondary_impact_drivers": ["water_extraction"],
        "high_impact": False,
        "sbtn_priority": "tier_2",
        "key_ecosystems": ["terrestrial_ecosystems", "marine", "freshwater"],
    },
    "financial_services": {
        "description": "Banking, insurance, asset management, capital markets",
        "primary_impact_drivers": ["land_use"],  # via financed activities
        "secondary_impact_drivers": ["water_extraction", "pollution", "climate_change", "overexploitation"],
        "high_impact": False,
        "sbtn_priority": "tier_2",
        "key_ecosystems": ["all_ecosystems"],  # portfolio-mediated
        "note": "Impact primarily via financed/facilitated emissions and nature loss",
    },
    "textiles_and_apparel": {
        "description": "Clothing, textiles, leather goods manufacturing",
        "primary_impact_drivers": ["land_use", "water_extraction", "pollution"],
        "secondary_impact_drivers": ["overexploitation", "invasive_species"],
        "high_impact": True,
        "sbtn_priority": "tier_1",
        "key_ecosystems": ["freshwater", "grasslands", "tropical_forests"],
    },
    "tourism_and_hospitality": {
        "description": "Hotels, resorts, tourism operators, recreation",
        "primary_impact_drivers": ["land_use", "water_extraction", "overexploitation"],
        "secondary_impact_drivers": ["pollution", "invasive_species"],
        "high_impact": False,
        "sbtn_priority": "tier_3",
        "key_ecosystems": ["coastal", "marine", "mountain_ecosystems"],
    },
    "pharmaceuticals_and_healthcare": {
        "description": "Drug discovery, manufacturing, medical devices",
        "primary_impact_drivers": ["pollution", "overexploitation"],
        "secondary_impact_drivers": ["land_use", "water_extraction"],
        "high_impact": False,
        "sbtn_priority": "tier_3",
        "key_ecosystems": ["tropical_forests", "freshwater", "marine"],
        "note": "Dependency on natural compounds; concern over pharmaceutical pollution",
    },
}

# ---------------------------------------------------------------------------
# Reference Data — TNFD 14 Core Metrics (v1.0, Sep 2023)
# ---------------------------------------------------------------------------

TNFD_DISCLOSURE_REQUIREMENTS: List[Dict[str, Any]] = [
    # Governance pillar
    {
        "id": "G1", "pillar": "governance", "metric": "Board oversight",
        "description": "Describe board-level oversight of nature-related dependencies, impacts, risks and opportunities",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R1",
    },
    {
        "id": "G2", "pillar": "governance", "metric": "Management responsibilities",
        "description": "Describe management's role in assessing and managing nature-related dependencies",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R2",
    },
    {
        "id": "G3", "pillar": "governance", "metric": "Policies and commitments",
        "description": "Describe nature-related policies, commitments and targets at governance level",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R3",
    },
    # Strategy pillar
    {
        "id": "S1", "pillar": "strategy", "metric": "Nature-related risks and opportunities",
        "description": "Describe nature-related risks and opportunities identified over short/medium/long term",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R4",
    },
    {
        "id": "S2", "pillar": "strategy", "metric": "Business model impacts",
        "description": "Describe how nature-related risks and opportunities affect business model and value chain",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R5",
    },
    {
        "id": "S3", "pillar": "strategy", "metric": "Scenario analysis",
        "description": "Describe resilience of nature strategy under different scenarios including 1.5°C and high-physical-risk",
        "disclosure_type": "qualitative_quantitative", "mandatory": True, "reference": "TNFD R6",
    },
    {
        "id": "S4", "pillar": "strategy", "metric": "Transition planning",
        "description": "Describe plans to achieve nature-related targets aligned with GBF Target 15",
        "disclosure_type": "qualitative", "mandatory": False, "reference": "TNFD R7 (encouraged)",
    },
    # Risk & Opportunity Management pillar
    {
        "id": "R1", "pillar": "risk_opportunity_management", "metric": "Risk identification processes",
        "description": "Describe processes for identifying and assessing nature-related risks in the LEAP approach",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R8",
    },
    {
        "id": "R2", "pillar": "risk_opportunity_management", "metric": "Risk prioritisation",
        "description": "Describe processes for managing nature-related risks and priorities",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R9",
    },
    {
        "id": "R3", "pillar": "risk_opportunity_management", "metric": "Integration into enterprise risk",
        "description": "Describe integration of nature-related risk management into overall enterprise risk management",
        "disclosure_type": "qualitative", "mandatory": True, "reference": "TNFD R10",
    },
    # Metrics & Targets pillar
    {
        "id": "M1", "pillar": "metrics_and_targets", "metric": "Land/water/ocean use metrics",
        "description": "Area (km²) used, affected, or restored; water withdrawal and consumption volumes",
        "disclosure_type": "quantitative", "unit": "km², m³", "mandatory": True, "reference": "TNFD M1",
    },
    {
        "id": "M2", "pillar": "metrics_and_targets", "metric": "Biodiversity footprint",
        "description": "MSA.km² impact; species affected by site; ecosystem condition indicators",
        "disclosure_type": "quantitative", "unit": "MSA.km²", "mandatory": True, "reference": "TNFD M2",
    },
    {
        "id": "M3", "pillar": "metrics_and_targets", "metric": "Ecosystem services dependency",
        "description": "Monetary or physical estimate of dependency on key ecosystem services per ENCORE",
        "disclosure_type": "quantitative", "unit": "USD or relative score", "mandatory": True, "reference": "TNFD M3",
    },
    {
        "id": "M4", "pillar": "metrics_and_targets", "metric": "Targets and progress",
        "description": "Science-based targets (SBTN) and progress against targets for nature; GBF alignment",
        "disclosure_type": "quantitative", "mandatory": True, "reference": "TNFD M4",
    },
]

# ---------------------------------------------------------------------------
# Reference Data — ENCORE 21 Ecosystem Services
# ---------------------------------------------------------------------------

ENCORE_ECOSYSTEM_SERVICES: Dict[str, Dict[str, Any]] = {
    "biomass": {
        "full_name": "Biomass provisioning",
        "category": "provisioning",
        "financial_dependency_weight": 0.12,
        "high_dependency_sectors": ["agriculture_and_forestry", "food_and_beverage", "pharmaceuticals_and_healthcare"],
        "encore_code": "ES-01",
        "valuation_range_usd_ha_yr": (50, 3500),
    },
    "climate_regulation": {
        "full_name": "Climate regulation (global)",
        "category": "regulating",
        "financial_dependency_weight": 0.14,
        "high_dependency_sectors": ["agriculture_and_forestry", "energy", "financial_services"],
        "encore_code": "ES-02",
        "valuation_range_usd_ha_yr": (100, 8000),
    },
    "freshwater": {
        "full_name": "Surface and ground water flows",
        "category": "provisioning",
        "financial_dependency_weight": 0.11,
        "high_dependency_sectors": ["agriculture_and_forestry", "chemicals", "food_and_beverage", "mining_and_materials"],
        "encore_code": "ES-03",
        "valuation_range_usd_ha_yr": (20, 5000),
    },
    "flood_hazard_attenuation": {
        "full_name": "Flood and storm protection",
        "category": "regulating",
        "financial_dependency_weight": 0.08,
        "high_dependency_sectors": ["construction_and_real_estate", "financial_services", "transportation"],
        "encore_code": "ES-04",
        "valuation_range_usd_ha_yr": (10, 2000),
    },
    "pollination": {
        "full_name": "Pollination (wild)",
        "category": "regulating",
        "financial_dependency_weight": 0.09,
        "high_dependency_sectors": ["agriculture_and_forestry", "food_and_beverage"],
        "encore_code": "ES-05",
        "valuation_range_usd_ha_yr": (15, 1200),
    },
    "soil_quality": {
        "full_name": "Soil quality and fertility",
        "category": "regulating",
        "financial_dependency_weight": 0.07,
        "high_dependency_sectors": ["agriculture_and_forestry", "food_and_beverage", "construction_and_real_estate"],
        "encore_code": "ES-06",
        "valuation_range_usd_ha_yr": (30, 900),
    },
    "erosion_control": {
        "full_name": "Erosion and sediment retention",
        "category": "regulating",
        "financial_dependency_weight": 0.05,
        "high_dependency_sectors": ["agriculture_and_forestry", "mining_and_materials", "construction_and_real_estate"],
        "encore_code": "ES-07",
        "valuation_range_usd_ha_yr": (5, 600),
    },
    "disease_regulation": {
        "full_name": "Disease and pest regulation",
        "category": "regulating",
        "financial_dependency_weight": 0.04,
        "high_dependency_sectors": ["agriculture_and_forestry", "tourism_and_hospitality", "pharmaceuticals_and_healthcare"],
        "encore_code": "ES-08",
        "valuation_range_usd_ha_yr": (5, 500),
    },
    "marine_fisheries": {
        "full_name": "Marine fish and seafood supply",
        "category": "provisioning",
        "financial_dependency_weight": 0.06,
        "high_dependency_sectors": ["food_and_beverage", "agriculture_and_forestry"],
        "encore_code": "ES-09",
        "valuation_range_usd_ha_yr": (10, 4000),
    },
    "genetic_resources": {
        "full_name": "Genetic resources (wild species)",
        "category": "provisioning",
        "financial_dependency_weight": 0.03,
        "high_dependency_sectors": ["pharmaceuticals_and_healthcare", "agriculture_and_forestry"],
        "encore_code": "ES-10",
        "valuation_range_usd_ha_yr": (2, 800),
    },
    "water_quality": {
        "full_name": "Water purification and quality",
        "category": "regulating",
        "financial_dependency_weight": 0.06,
        "high_dependency_sectors": ["food_and_beverage", "chemicals", "mining_and_materials", "pharmaceuticals_and_healthcare"],
        "encore_code": "ES-11",
        "valuation_range_usd_ha_yr": (10, 1500),
    },
    "coastal_protection": {
        "full_name": "Coastal hazard attenuation",
        "category": "regulating",
        "financial_dependency_weight": 0.04,
        "high_dependency_sectors": ["construction_and_real_estate", "tourism_and_hospitality", "financial_services"],
        "encore_code": "ES-12",
        "valuation_range_usd_ha_yr": (50, 3000),
    },
    "air_quality": {
        "full_name": "Air quality regulation",
        "category": "regulating",
        "financial_dependency_weight": 0.03,
        "high_dependency_sectors": ["energy", "chemicals", "transportation"],
        "encore_code": "ES-13",
        "valuation_range_usd_ha_yr": (2, 400),
    },
    "noise_attenuation": {
        "full_name": "Noise mitigation",
        "category": "regulating",
        "financial_dependency_weight": 0.02,
        "high_dependency_sectors": ["construction_and_real_estate", "transportation", "tourism_and_hospitality"],
        "encore_code": "ES-14",
        "valuation_range_usd_ha_yr": (1, 200),
    },
    "biological_control": {
        "full_name": "Biological control (pest/predator balance)",
        "category": "regulating",
        "financial_dependency_weight": 0.03,
        "high_dependency_sectors": ["agriculture_and_forestry", "food_and_beverage"],
        "encore_code": "ES-15",
        "valuation_range_usd_ha_yr": (5, 700),
    },
    "fibre_raw_material": {
        "full_name": "Fibres and other materials",
        "category": "provisioning",
        "financial_dependency_weight": 0.04,
        "high_dependency_sectors": ["textiles_and_apparel", "agriculture_and_forestry", "construction_and_real_estate"],
        "encore_code": "ES-16",
        "valuation_range_usd_ha_yr": (5, 1200),
    },
    "energy_biomass": {
        "full_name": "Bioenergy (biomass for energy)",
        "category": "provisioning",
        "financial_dependency_weight": 0.03,
        "high_dependency_sectors": ["energy", "agriculture_and_forestry"],
        "encore_code": "ES-17",
        "valuation_range_usd_ha_yr": (10, 800),
    },
    "cultural_recreation": {
        "full_name": "Recreation and mental/physical health",
        "category": "cultural",
        "financial_dependency_weight": 0.03,
        "high_dependency_sectors": ["tourism_and_hospitality", "construction_and_real_estate"],
        "encore_code": "ES-18",
        "valuation_range_usd_ha_yr": (5, 600),
    },
    "soil_erosion_prevention": {
        "full_name": "Mass flow (landslide, avalanche prevention)",
        "category": "regulating",
        "financial_dependency_weight": 0.02,
        "high_dependency_sectors": ["construction_and_real_estate", "mining_and_materials", "transportation"],
        "encore_code": "ES-19",
        "valuation_range_usd_ha_yr": (2, 500),
    },
    "optical_uv_regulation": {
        "full_name": "Optical environment regulation",
        "category": "regulating",
        "financial_dependency_weight": 0.01,
        "high_dependency_sectors": ["pharmaceuticals_and_healthcare"],
        "encore_code": "ES-20",
        "valuation_range_usd_ha_yr": (1, 50),
    },
    "scientific_knowledge": {
        "full_name": "Scientific research and knowledge",
        "category": "cultural",
        "financial_dependency_weight": 0.05,
        "high_dependency_sectors": ["pharmaceuticals_and_healthcare", "financial_services"],
        "encore_code": "ES-21",
        "valuation_range_usd_ha_yr": (2, 300),
    },
}

# ---------------------------------------------------------------------------
# Reference Data — EU NRL Habitat Types (Regulation (EU) 2024/1991)
# ---------------------------------------------------------------------------

EU_NRL_HABITAT_TYPES: Dict[str, Dict[str, Any]] = {
    "wetlands": {
        "description": "Inland and coastal wetland ecosystems including peatlands, marshes",
        "restoration_target_2030": 30,   # % of degraded area to restore
        "restoration_target_2040": 60,
        "restoration_target_2050": 90,
        "deterioration_standstill": "2024",  # no further deterioration from this year
        "key_article": "Art 7 EU NRL",
        "legal_target": "Restore 30% of degraded wetland area by 2030",
        "annual_gain_target_ha": 30000,
    },
    "rivers_floodplains": {
        "description": "Rivers, streams, lakes and their associated floodplains",
        "restoration_target_2030": 25,
        "restoration_target_2040": 50,
        "restoration_target_2050": 75,
        "deterioration_standstill": "2024",
        "key_article": "Art 7 EU NRL + Art 11 river connectivity",
        "legal_target": "Restore 25% degraded freshwater; re-connect 25,000 km of rivers by 2030",
        "free_flowing_river_km_target_2030": 25000,
    },
    "forests": {
        "description": "Primary, old-growth and managed forests including boreal, temperate, Mediterranean",
        "restoration_target_2030": 20,
        "restoration_target_2040": 40,
        "restoration_target_2050": 60,
        "deterioration_standstill": "2024",
        "key_article": "Art 10 EU NRL",
        "legal_target": "Increase forest biodiversity indicators; restore 20% of degraded forest by 2030",
        "old_growth_forest_protected_pct": 10,
    },
    "grasslands_and_heathlands": {
        "description": "Semi-natural grasslands, heathlands, scrubland and shrubland",
        "restoration_target_2030": 30,
        "restoration_target_2040": 60,
        "restoration_target_2050": 90,
        "deterioration_standstill": "2024",
        "key_article": "Art 9 EU NRL",
        "legal_target": "Restore 30% of degraded grassland/heathland by 2030 from high distinctiveness",
    },
    "agricultural_land": {
        "description": "Arable land and farmland with high biodiversity value (HNV farmland)",
        "restoration_target_2030": 10,
        "restoration_target_2040": 20,
        "restoration_target_2050": 30,
        "deterioration_standstill": "2024",
        "key_article": "Art 9 EU NRL",
        "legal_target": "Increase farmland bird index; increase high-diversity landscape features by 10% by 2030",
        "pollinator_trend": "increasing_by_2030",
    },
    "marine_and_coastal": {
        "description": "Seagrass beds, reefs, coastal dunes, salt marshes, macroalgae",
        "restoration_target_2030": 30,
        "restoration_target_2040": 60,
        "restoration_target_2050": 90,
        "deterioration_standstill": "2024",
        "key_article": "Art 12 EU NRL",
        "legal_target": "Restore 30% of degraded marine and coastal habitats by 2030",
    },
    "urban_green_infrastructure": {
        "description": "Urban trees, parks, green roofs/walls, urban forests, peri-urban nature",
        "restoration_target_2030": 5,   # net gain in urban green
        "restoration_target_2040": 10,
        "restoration_target_2050": 15,
        "deterioration_standstill": "2030",
        "key_article": "Art 6 EU NRL",
        "legal_target": "Net increase in urban green space/urban canopy cover by 2030; no net loss after 2030",
        "urban_tree_cover_increase_pct": 3,
    },
    "mires_bogs_fens": {
        "description": "Peatland-forming wetlands including raised bogs, blanket bogs, and fens",
        "restoration_target_2030": 30,
        "restoration_target_2040": 50,
        "restoration_target_2050": 70,
        "deterioration_standstill": "2024",
        "key_article": "Art 11 EU NRL",
        "legal_target": "Rewet 30% of drained peatlands under agricultural use by 2030",
        "peatland_rewetting_target_ha_2030": 4000000,
    },
    "rocky_habitats": {
        "description": "Rock faces, screes, caves, subterranean karst and volcanic habitats",
        "restoration_target_2030": 15,
        "restoration_target_2040": 30,
        "restoration_target_2050": 50,
        "deterioration_standstill": "2024",
        "key_article": "Annex I EU NRL — Habitat type list",
        "legal_target": "Restore 15% of rocky and subterranean habitats by 2030",
    },
    "sparsely_vegetated": {
        "description": "Sand dunes, inland dunes, snowfields, glaciers, bare rock outcrops",
        "restoration_target_2030": 15,
        "restoration_target_2040": 30,
        "restoration_target_2050": 50,
        "deterioration_standstill": "2024",
        "key_article": "Annex I EU NRL — Habitat type list",
        "legal_target": "Restore 15% of sparsely vegetated habitats by 2030",
    },
}

# ---------------------------------------------------------------------------
# Reference Data — GBF Target 3 Country Protection Data (30x30)
# ---------------------------------------------------------------------------

GBF_TARGET_3_COUNTRIES: Dict[str, Dict[str, Any]] = {
    "DE": {"name": "Germany", "land_protected_pct": 38.4, "sea_protected_pct": 45.2, "gbf_committed": True, "eu_member": True},
    "FR": {"name": "France", "land_protected_pct": 33.2, "sea_protected_pct": 23.1, "gbf_committed": True, "eu_member": True},
    "GB": {"name": "United Kingdom", "land_protected_pct": 28.1, "sea_protected_pct": 38.0, "gbf_committed": True, "eu_member": False},
    "US": {"name": "United States", "land_protected_pct": 13.0, "sea_protected_pct": 26.0, "gbf_committed": True, "eu_member": False},
    "CA": {"name": "Canada", "land_protected_pct": 13.5, "sea_protected_pct": 14.0, "gbf_committed": True, "eu_member": False},
    "BR": {"name": "Brazil", "land_protected_pct": 29.8, "sea_protected_pct": 26.4, "gbf_committed": True, "eu_member": False},
    "CN": {"name": "China", "land_protected_pct": 18.0, "sea_protected_pct": 4.6, "gbf_committed": True, "eu_member": False},
    "IN": {"name": "India", "land_protected_pct": 5.4, "sea_protected_pct": 0.7, "gbf_committed": True, "eu_member": False},
    "AU": {"name": "Australia", "land_protected_pct": 22.0, "sea_protected_pct": 45.1, "gbf_committed": True, "eu_member": False},
    "JP": {"name": "Japan", "land_protected_pct": 20.5, "sea_protected_pct": 13.3, "gbf_committed": True, "eu_member": False},
    "ZA": {"name": "South Africa", "land_protected_pct": 10.6, "sea_protected_pct": 5.4, "gbf_committed": True, "eu_member": False},
    "ID": {"name": "Indonesia", "land_protected_pct": 14.7, "sea_protected_pct": 6.2, "gbf_committed": True, "eu_member": False},
    "MX": {"name": "Mexico", "land_protected_pct": 11.6, "sea_protected_pct": 22.0, "gbf_committed": True, "eu_member": False},
    "AR": {"name": "Argentina", "land_protected_pct": 10.5, "sea_protected_pct": 5.8, "gbf_committed": True, "eu_member": False},
    "CL": {"name": "Chile", "land_protected_pct": 22.4, "sea_protected_pct": 42.5, "gbf_committed": True, "eu_member": False},
    "CO": {"name": "Colombia", "land_protected_pct": 17.7, "sea_protected_pct": 16.7, "gbf_committed": True, "eu_member": False},
    "RU": {"name": "Russia", "land_protected_pct": 13.8, "sea_protected_pct": 1.5, "gbf_committed": False, "eu_member": False},
    "NG": {"name": "Nigeria", "land_protected_pct": 14.4, "sea_protected_pct": 0.4, "gbf_committed": True, "eu_member": False},
    "KE": {"name": "Kenya", "land_protected_pct": 13.6, "sea_protected_pct": 10.2, "gbf_committed": True, "eu_member": False},
    "ET": {"name": "Ethiopia", "land_protected_pct": 18.8, "sea_protected_pct": 0.0, "gbf_committed": True, "eu_member": False},
    "SE": {"name": "Sweden", "land_protected_pct": 15.6, "sea_protected_pct": 6.4, "gbf_committed": True, "eu_member": True},
    "NL": {"name": "Netherlands", "land_protected_pct": 22.3, "sea_protected_pct": 16.5, "gbf_committed": True, "eu_member": True},
    "PL": {"name": "Poland", "land_protected_pct": 39.8, "sea_protected_pct": 18.2, "gbf_committed": True, "eu_member": True},
    "ES": {"name": "Spain", "land_protected_pct": 29.0, "sea_protected_pct": 12.2, "gbf_committed": True, "eu_member": True},
    "IT": {"name": "Italy", "land_protected_pct": 21.5, "sea_protected_pct": 11.5, "gbf_committed": True, "eu_member": True},
    "PT": {"name": "Portugal", "land_protected_pct": 25.0, "sea_protected_pct": 6.0, "gbf_committed": True, "eu_member": True},
    "SG": {"name": "Singapore", "land_protected_pct": 5.2, "sea_protected_pct": 3.1, "gbf_committed": True, "eu_member": False},
    "MY": {"name": "Malaysia", "land_protected_pct": 15.5, "sea_protected_pct": 1.8, "gbf_committed": True, "eu_member": False},
    "TZ": {"name": "Tanzania", "land_protected_pct": 37.5, "sea_protected_pct": 6.2, "gbf_committed": True, "eu_member": False},
    "VN": {"name": "Vietnam", "land_protected_pct": 9.6, "sea_protected_pct": 0.5, "gbf_committed": True, "eu_member": False},
}

# ---------------------------------------------------------------------------
# Reference Data — Nature Maturity Tiers
# ---------------------------------------------------------------------------

NATURE_MATURITY_TIERS: Dict[str, Dict[str, Any]] = {
    "leading": {
        "min_score": 80,
        "max_score": 100,
        "description": "Best-in-class nature strategy; science-based targets set and in progress; TNFD-aligned disclosures; NRL/GBF compliant",
        "typical_profile": "SBTN targets set; TNFD full-disclosure; NRL compliance plan filed; 30x30 portfolio screened; ENCORE quantified",
        "investor_signal": "Preferred — leading nature governance; eligible for nature-positive bond premium",
        "regulatory_flags": [],
    },
    "advanced": {
        "min_score": 60,
        "max_score": 79,
        "description": "Strong nature strategy with most components in place; minor disclosure gaps",
        "typical_profile": "SBTN steps 1-3 complete; TNFD partial disclosure; NRL exposure mapped; ENCORE semi-quantified",
        "investor_signal": "Positive — advanced nature risk management; monitor gap closure",
        "regulatory_flags": ["SFDR PAI I14 biodiversity tracking recommended"],
    },
    "developing": {
        "min_score": 40,
        "max_score": 59,
        "description": "Nature strategy under development; some assessments initiated but material gaps remain",
        "typical_profile": "SBTN step 1 only; TNFD qualitative only; NRL known but unquantified; ENCORE qualitative",
        "investor_signal": "Neutral — nature strategy developing; request remediation timeline",
        "regulatory_flags": ["CSRD ESRS E4 non-compliance risk", "SFDR PAI I14 gap"],
    },
    "early": {
        "min_score": 20,
        "max_score": 39,
        "description": "Early-stage nature awareness; limited formal assessment; high disclosure gaps",
        "typical_profile": "No SBTN commitment; minimal TNFD; no NRL analysis; ENCORE unknown",
        "investor_signal": "Cautionary — limited nature governance; engagement required",
        "regulatory_flags": ["CSRD ESRS E4 material gap", "SFDR Art 8/9 biodiversity PAI gap", "TNFD non-disclosure risk"],
    },
    "minimal": {
        "min_score": 0,
        "max_score": 19,
        "description": "No meaningful nature strategy; no assessments; greenwashing risk",
        "typical_profile": "No SBTN; no TNFD; NRL ignored; ENCORE not considered",
        "investor_signal": "High risk — no nature strategy; divestment review or escalation warranted",
        "regulatory_flags": ["CSRD ESRS E4 non-compliance", "SFDR Art 9 unsuitable", "EUDR risk if agricultural supply chain", "EU NRL exposure unmanaged"],
    },
}

# ---------------------------------------------------------------------------
# Land-use MSA factors (Mean Species Abundance) — GLOBIO model
# ---------------------------------------------------------------------------

LAND_USE_MSA_FACTORS: Dict[str, float] = {
    "primary_vegetation": 1.00,
    "secondary_vegetation": 0.70,
    "lightly_used_natural": 0.80,
    "extensive_agriculture": 0.50,
    "intensive_agriculture": 0.30,
    "plantation_forestry": 0.20,
    "urban_built_up": 0.05,
    "mining_quarrying": 0.10,
    "aquaculture_freshwater": 0.40,
    "aquaculture_marine": 0.55,
    "pasture": 0.35,
    "managed_grassland": 0.45,
}


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class CorporateNatureStrategyEngine:
    """
    E80: Corporate Nature Strategy & SBTN Engine.

    Assesses corporate nature strategy across five frameworks:
      1. SBTN 5-step readiness and target quality
      2. TNFD v1.0 disclosure completeness
      3. EU Nature Restoration Law (NRL) 2024/1991 habitat exposure
      4. GBF Target 3 (30x30) portfolio exposure
      5. ENCORE ecosystem service dependencies and financial exposure
    """

    def __init__(self) -> None:
        logger.info("CorporateNatureStrategyEngine initialised (E80)")

    # ------------------------------------------------------------------
    # 1. SBTN 5-Step Assessment
    # ------------------------------------------------------------------

    def assess_sbtn_steps(
        self,
        entity_id: str,
        sectors: List[str],
        locations: List[Dict[str, Any]],
        current_targets: List[Dict[str, Any]],
        disclosures: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Score SBTN 5-step readiness (Assess/Interpret/Measure/Set/Disclose).
        Each step scored 0-100. MSA.km² footprint estimated from locations.
        High-impact sectors and material locations flagged.

        SBTN Step Guidance v1.1 (2023):
          Step 1 Assess   — prioritise with SBTN materiality tool
          Step 2 Interpret — understand state of nature at material locations
          Step 3 Measure  — measure baseline biodiversity state
          Step 4 Set      — set science-based targets per SBTN freshwater/land targets
          Step 5 Act      — implement actions and disclose annually
        """
        logger.debug("assess_sbtn_steps entity=%s sectors=%s", entity_id, sectors)

        # --- Step 1: Assess (materiality + prioritisation) ---
        has_materiality_screening = disclosures.get("sbtn_materiality_screening", False)
        has_leap_locate = disclosures.get("leap_locate_complete", False)
        n_locations_mapped = len(locations)
        step1_score = 0
        if has_materiality_screening:
            step1_score += 40
        if has_leap_locate:
            step1_score += 30
        if n_locations_mapped > 0:
            step1_score += min(30, n_locations_mapped * 5)

        # --- Step 2: Interpret (dependency/impact analysis) ---
        has_dependency_assessment = disclosures.get("encore_dependency_assessment", False)
        has_state_of_nature = disclosures.get("state_of_nature_report", False)
        has_scenario = disclosures.get("scenario_analysis_nature", False)
        step2_score = 0
        if has_dependency_assessment:
            step2_score += 35
        if has_state_of_nature:
            step2_score += 35
        if has_scenario:
            step2_score += 30

        # --- Step 3: Measure (baseline metrics) ---
        has_msa_footprint = disclosures.get("msa_footprint_calculated", False)
        has_biodiversity_footprint = disclosures.get("biodiversity_footprint", False)
        has_water_metrics = disclosures.get("water_metrics_disclosed", False)
        step3_score = 0
        if has_msa_footprint:
            step3_score += 40
        if has_biodiversity_footprint:
            step3_score += 35
        if has_water_metrics:
            step3_score += 25

        # --- Step 4: Set targets ---
        sbtn_targets = [t for t in current_targets if t.get("framework", "").upper() == "SBTN"]
        land_targets = [t for t in sbtn_targets if t.get("type") == "land"]
        freshwater_targets = [t for t in sbtn_targets if t.get("type") == "freshwater"]
        step4_score = 0
        if len(sbtn_targets) > 0:
            step4_score += 30
        if len(land_targets) > 0:
            step4_score += 35
        if len(freshwater_targets) > 0:
            step4_score += 35

        # --- Step 5: Disclose ---
        has_tnfd_disclosure = disclosures.get("tnfd_disclosure", False)
        has_annual_progress = disclosures.get("annual_progress_report", False)
        has_third_party_verification = disclosures.get("third_party_verification", False)
        step5_score = 0
        if has_tnfd_disclosure:
            step5_score += 40
        if has_annual_progress:
            step5_score += 35
        if has_third_party_verification:
            step5_score += 25

        # --- MSA.km² footprint ---
        total_msa_km2 = 0.0
        for loc in locations:
            area_ha = loc.get("area_ha", 0)
            area_km2 = area_ha / 100.0
            land_use = loc.get("land_use_type", "intensive_agriculture")
            msa_factor = LAND_USE_MSA_FACTORS.get(land_use, 0.30)
            # MSA loss = area × (1 - MSA_factor) i.e. how much species abundance is lost
            total_msa_km2 += area_km2 * (1.0 - msa_factor)

        # --- High-impact sectors ---
        high_impact_sectors = []
        for sec in sectors:
            sec_data = SBTN_SECTOR_IMPACT_MAP.get(sec)
            if sec_data and sec_data.get("high_impact"):
                high_impact_sectors.append(sec)

        # --- Material locations ---
        material_locations = []
        for loc in locations:
            if loc.get("area_ha", 0) >= 100 or loc.get("protected_area_overlap", False):
                material_locations.append({
                    "country": loc.get("country", ""),
                    "lat": loc.get("lat"),
                    "lng": loc.get("lng"),
                    "area_ha": loc.get("area_ha", 0),
                    "materiality_reason": "large_footprint" if loc.get("area_ha", 0) >= 100 else "protected_area",
                })

        # Composite SBTN readiness
        sbtn_composite = round(
            step1_score * 0.15 + step2_score * 0.20 + step3_score * 0.25
            + step4_score * 0.25 + step5_score * 0.15,
            1,
        )

        return {
            "entity_id": entity_id,
            "framework": "SBTN v1.1 (2023)",
            "step_scores": {
                "step1_assess": step1_score,
                "step2_interpret": step2_score,
                "step3_measure": step3_score,
                "step4_set": step4_score,
                "step5_disclose": step5_score,
            },
            "sbtn_composite_score": sbtn_composite,
            "msa_km2_footprint": round(total_msa_km2, 3),
            "high_impact_sectors": high_impact_sectors,
            "material_locations": material_locations,
            "sbtn_targets_count": len(sbtn_targets),
            "land_targets_count": len(land_targets),
            "freshwater_targets_count": len(freshwater_targets),
            "sectors_assessed": sectors,
            "n_locations": n_locations_mapped,
        }

    # ------------------------------------------------------------------
    # 2. TNFD Disclosure Assessment
    # ------------------------------------------------------------------

    def assess_tnfd_disclosure(
        self,
        entity_id: str,
        governance_data: Dict[str, Any],
        strategy_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        metrics_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Score TNFD v1.0 disclosure across 4 pillars and 14 core metrics.
        Returns pillar scores (0-100), composite TNFD score, and gap list.

        TNFD v1.0 Sep 2023: 4 pillars, 14 recommended disclosures R1-R14.
        """
        logger.debug("assess_tnfd_disclosure entity=%s", entity_id)

        pillar_inputs = {
            "governance": governance_data,
            "strategy": strategy_data,
            "risk_opportunity_management": risk_data,
            "metrics_and_targets": metrics_data,
        }

        pillar_scores: Dict[str, float] = {}
        gaps: List[Dict[str, str]] = []

        # Group metrics by pillar
        pillar_metrics: Dict[str, List[Dict]] = {
            "governance": [],
            "strategy": [],
            "risk_opportunity_management": [],
            "metrics_and_targets": [],
        }
        for metric in TNFD_DISCLOSURE_REQUIREMENTS:
            pillar = metric["pillar"]
            if pillar in pillar_metrics:
                pillar_metrics[pillar].append(metric)

        for pillar, metrics_list in pillar_metrics.items():
            data = pillar_inputs.get(pillar, {})
            mandatory_total = sum(1 for m in metrics_list if m["mandatory"])
            optional_total = sum(1 for m in metrics_list if not m["mandatory"])
            mandatory_met = 0
            optional_met = 0

            for metric in metrics_list:
                metric_key = metric["id"].lower()
                # Check if this metric is addressed in the data dict
                provided = data.get(metric_key) or data.get(metric["metric"].lower().replace(" ", "_"))
                is_complete = bool(provided) if provided is not None else False
                if is_complete:
                    if metric["mandatory"]:
                        mandatory_met += 1
                    else:
                        optional_met += 1
                else:
                    gaps.append({
                        "pillar": pillar,
                        "metric_id": metric["id"],
                        "metric": metric["metric"],
                        "mandatory": str(metric["mandatory"]),
                        "reference": metric["reference"],
                        "gap_description": f"Missing: {metric['description'][:80]}",
                    })

            # Mandatory accounts for 80% of pillar score; optional 20%
            mandatory_score = (mandatory_met / mandatory_total * 80) if mandatory_total > 0 else 0
            optional_score = (optional_met / optional_total * 20) if optional_total > 0 else 20
            pillar_scores[pillar] = round(mandatory_score + optional_score, 1)

        # Equal-weight pillars for composite (TNFD does not prescribe weighting)
        composite_score = round(sum(pillar_scores.values()) / len(pillar_scores), 1)
        mandatory_gaps = [g for g in gaps if g["mandatory"] == "True"]

        return {
            "entity_id": entity_id,
            "framework": "TNFD v1.0 (Sep 2023)",
            "pillar_scores": pillar_scores,
            "composite_tnfd_score": composite_score,
            "total_metrics_assessed": len(TNFD_DISCLOSURE_REQUIREMENTS),
            "gaps": gaps,
            "mandatory_gaps_count": len(mandatory_gaps),
            "optional_gaps_count": len(gaps) - len(mandatory_gaps),
            "leap_approach_referenced": strategy_data.get("leap_approach", False),
        }

    # ------------------------------------------------------------------
    # 3. EU NRL Exposure Assessment
    # ------------------------------------------------------------------

    def assess_nrl_exposure(
        self,
        entity_id: str,
        operations: List[Dict[str, Any]],
        supply_chain_countries: List[str],
    ) -> Dict[str, Any]:
        """
        Assess EU Nature Restoration Law 2024/1991 habitat exposure.
        Estimates restoration liability and compliance timeline per Art 4-12.
        """
        logger.debug("assess_nrl_exposure entity=%s ops=%d countries=%d",
                     entity_id, len(operations), len(supply_chain_countries))

        affected_habitats: Dict[str, Dict[str, Any]] = {}
        total_restoration_liability_ha = 0.0
        compliance_gaps: List[str] = []
        eu_country_exposure = False

        EU_MEMBER_CODES = {"AT","BE","BG","CY","CZ","DE","DK","EE","ES","FI","FR","GR","HR",
                           "HU","IE","IT","LT","LU","LV","MT","NL","PL","PT","RO","SE","SI","SK"}

        # Check EU operations
        for op in operations:
            country = op.get("country", "")
            habitat_types = op.get("habitat_types", [])
            area_ha = op.get("area_ha", 0.0)

            if country in EU_MEMBER_CODES:
                eu_country_exposure = True

            for hab in habitat_types:
                if hab in EU_NRL_HABITAT_TYPES:
                    hab_data = EU_NRL_HABITAT_TYPES[hab]
                    restoration_pct_2030 = hab_data["restoration_target_2030"] / 100.0
                    # Estimate liability as % of operation area needing restoration
                    degradation_assumed = op.get("degradation_level", 0.5)  # 50% default
                    liability_ha = area_ha * degradation_assumed * restoration_pct_2030

                    if hab not in affected_habitats:
                        affected_habitats[hab] = {
                            "habitat": hab,
                            "description": hab_data["description"],
                            "total_area_ha": 0.0,
                            "restoration_liability_ha_2030": 0.0,
                            "restoration_target_2030_pct": hab_data["restoration_target_2030"],
                            "restoration_target_2050_pct": hab_data["restoration_target_2050"],
                            "deterioration_standstill_year": hab_data["deterioration_standstill"],
                            "key_article": hab_data["key_article"],
                        }
                    affected_habitats[hab]["total_area_ha"] += area_ha
                    affected_habitats[hab]["restoration_liability_ha_2030"] += liability_ha
                    total_restoration_liability_ha += liability_ha

                    if country in EU_MEMBER_CODES and degradation_assumed > 0.3:
                        compliance_gaps.append(
                            f"{hab} at {op.get('site_name', country)}: "
                            f"{liability_ha:.0f} ha restoration by 2030 per {hab_data['key_article']}"
                        )

        # Supply chain EU exposure
        sc_eu_countries = [c for c in supply_chain_countries if c in EU_MEMBER_CODES]

        # Estimate financial liability: €3,000/ha average NRL restoration cost (EU Commission IA 2023)
        restoration_cost_per_ha = 3000  # EUR
        estimated_financial_liability_eur = total_restoration_liability_ha * restoration_cost_per_ha

        # NRL compliance score
        n_ops_in_eu = sum(1 for op in operations if op.get("country", "") in EU_MEMBER_CODES)
        n_ops_with_plan = sum(1 for op in operations if op.get("restoration_plan_filed", False))
        nrl_compliance_score = 100 if n_ops_in_eu == 0 else (
            round((n_ops_with_plan / n_ops_in_eu) * 100, 1) if n_ops_in_eu > 0 else 0
        )

        return {
            "entity_id": entity_id,
            "framework": "EU Nature Restoration Law 2024/1991",
            "eu_operations_exposure": eu_country_exposure,
            "eu_supply_chain_countries": sc_eu_countries,
            "affected_habitats": list(affected_habitats.values()),
            "total_restoration_liability_ha": round(total_restoration_liability_ha, 1),
            "estimated_financial_liability_eur": round(estimated_financial_liability_eur, 0),
            "compliance_gaps": compliance_gaps,
            "nrl_compliance_score": nrl_compliance_score,
            "compliance_deadline_primary": "2030-12-31",
            "compliance_deadline_full": "2050-12-31",
            "deterioration_standstill": "2024-01-01",
            "habitat_types_exposed": list(affected_habitats.keys()),
        }

    # ------------------------------------------------------------------
    # 4. GBF Target 3 (30x30) Assessment
    # ------------------------------------------------------------------

    def assess_gbf_target3(
        self,
        entity_id: str,
        portfolio_locations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Assess portfolio exposure within 30x30 protected areas per GBF Target 3.
        Returns % exposure in protected zones by country and financial exposure estimate.

        GBF Target 3 (KM-GBF 2022): 30% of land and 30% of oceans under effective protection by 2030.
        """
        logger.debug("assess_gbf_target3 entity=%s locs=%d", entity_id, len(portfolio_locations))

        country_exposure: Dict[str, Dict[str, Any]] = {}
        total_exposure_m = 0.0
        in_protected_zone_m = 0.0

        for loc in portfolio_locations:
            country = loc.get("country", "UNKNOWN")
            exposure_m = loc.get("exposure_m", 0.0)
            is_land = loc.get("asset_type", "land") != "marine"
            total_exposure_m += exposure_m

            country_data = GBF_TARGET_3_COUNTRIES.get(country, {})
            if not country_data:
                # Unknown country: use global average 17% land protected
                protected_pct = 17.0 if is_land else 8.0
                gbf_committed = False
            else:
                protected_pct = country_data["land_protected_pct"] if is_land else country_data["sea_protected_pct"]
                gbf_committed = country_data["gbf_committed"]

            # Estimate portion in protected zones
            in_protected = exposure_m * (protected_pct / 100.0)
            in_protected_zone_m += in_protected

            # Flag if country at risk of 30x30 expansion (below 30%)
            below_30x30 = protected_pct < 30.0
            risk_of_restriction = below_30x30 and gbf_committed

            if country not in country_exposure:
                country_exposure[country] = {
                    "country": country,
                    "country_name": country_data.get("name", country),
                    "total_exposure_m": 0.0,
                    "estimated_in_protected_zone_m": 0.0,
                    "land_protected_pct": country_data.get("land_protected_pct", 17.0),
                    "sea_protected_pct": country_data.get("sea_protected_pct", 8.0),
                    "gbf_committed": gbf_committed,
                    "below_30x30_target": below_30x30,
                    "future_restriction_risk": risk_of_restriction,
                }
            country_exposure[country]["total_exposure_m"] += exposure_m
            country_exposure[country]["estimated_in_protected_zone_m"] += in_protected

        portfolio_protected_pct = (in_protected_zone_m / total_exposure_m * 100) if total_exposure_m > 0 else 0
        below_30_countries = [c for c, d in country_exposure.items() if d["below_30x30_target"]]

        # GBF alignment score: penalise for exposure in countries below 30x30 without a path to compliance
        risk_countries_count = len([c for c, d in country_exposure.items() if d["future_restriction_risk"]])
        total_countries = len(country_exposure)
        gbf_score = round(100 - (risk_countries_count / total_countries * 40), 1) if total_countries > 0 else 100

        return {
            "entity_id": entity_id,
            "framework": "CBD Kunming-Montreal GBF Target 3 (2022)",
            "gbf_target_3_2030": "30% land + 30% ocean under effective protection by 2030",
            "total_portfolio_exposure_m": round(total_exposure_m, 2),
            "estimated_in_protected_zone_m": round(in_protected_zone_m, 2),
            "portfolio_protected_zone_pct": round(portfolio_protected_pct, 2),
            "country_exposure": list(country_exposure.values()),
            "countries_below_30x30": below_30_countries,
            "countries_with_restriction_risk": [c for c, d in country_exposure.items() if d["future_restriction_risk"]],
            "gbf_alignment_score": gbf_score,
        }

    # ------------------------------------------------------------------
    # 5. ENCORE Dependency Assessment
    # ------------------------------------------------------------------

    def assess_encore_dependencies(
        self,
        entity_id: str,
        sector: str,
        operations_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Score 21 ENCORE ecosystem service dependencies and impacts.
        Returns dependency/impact scores and financial exposure matrix.

        ENCORE v2.1 (2023): Natural Capital Finance Alliance / UNEP-WCMC.
        Maps sector activities to ecosystem service dependencies and impacts.
        """
        logger.debug("assess_encore_dependencies entity=%s sector=%s", entity_id, sector)

        sector_data = SBTN_SECTOR_IMPACT_MAP.get(sector, {})
        primary_drivers = sector_data.get("primary_impact_drivers", [])
        revenue_m = operations_data.get("annual_revenue_m", 100.0)
        operational_area_ha = operations_data.get("operational_area_ha", 500.0)

        dependency_scores: List[Dict[str, Any]] = []
        total_financial_exposure_m = 0.0

        driver_to_services = {
            "land_use": ["biomass", "soil_quality", "erosion_control", "pollination",
                         "biological_control", "cultural_recreation", "soil_erosion_prevention"],
            "water_extraction": ["freshwater", "water_quality", "flood_hazard_attenuation"],
            "pollution": ["air_quality", "water_quality", "disease_regulation", "marine_fisheries"],
            "climate_change": ["climate_regulation", "coastal_protection", "genetic_resources"],
            "invasive_species": ["biological_control", "disease_regulation", "genetic_resources"],
            "overexploitation": ["marine_fisheries", "genetic_resources", "biomass", "fibre_raw_material"],
        }

        affected_services = set()
        for driver in primary_drivers:
            affected_services.update(driver_to_services.get(driver, []))

        for svc_key, svc_data in ENCORE_ECOSYSTEM_SERVICES.items():
            is_affected = svc_key in affected_services
            is_high_dep = sector in svc_data.get("high_dependency_sectors", [])

            # Dependency score 0-100
            base_dependency = svc_data["financial_dependency_weight"] * 100
            if is_high_dep:
                base_dependency = min(100, base_dependency * 1.8)
            dependency_score = round(base_dependency, 1)

            # Impact score 0-100 (how much this sector impacts the service)
            impact_score = round(min(100, dependency_score * (1.5 if is_affected else 0.4)), 1)

            # Financial exposure: dependency weight × revenue
            low_val, high_val = svc_data["valuation_range_usd_ha_yr"]
            mid_val_usd_ha_yr = (low_val + high_val) / 2.0
            financial_exposure_m = (operational_area_ha * mid_val_usd_ha_yr / 1_000_000.0) * (dependency_score / 100.0)
            total_financial_exposure_m += financial_exposure_m

            dependency_scores.append({
                "service_key": svc_key,
                "service_name": svc_data["full_name"],
                "encore_code": svc_data["encore_code"],
                "category": svc_data["category"],
                "dependency_score": dependency_score,
                "impact_score": impact_score,
                "is_primary_driver_affected": is_affected,
                "is_high_dependency_sector": is_high_dep,
                "financial_exposure_m_usd": round(financial_exposure_m, 3),
                "valuation_range_usd_ha_yr": svc_data["valuation_range_usd_ha_yr"],
            })

        # Sort by financial exposure descending
        dependency_scores.sort(key=lambda x: x["financial_exposure_m_usd"], reverse=True)

        top_dependencies = [s for s in dependency_scores if s["dependency_score"] >= 50]
        high_impact_services = [s for s in dependency_scores if s["impact_score"] >= 60]

        encore_score = round(
            100 - min(100, (len(top_dependencies) / len(ENCORE_ECOSYSTEM_SERVICES)) * 50
                      + (total_financial_exposure_m / max(revenue_m, 1)) * 10),
            1,
        )

        return {
            "entity_id": entity_id,
            "framework": "ENCORE v2.1 (NCFA / UNEP-WCMC 2023)",
            "sector": sector,
            "services_assessed": len(dependency_scores),
            "dependency_scores": dependency_scores,
            "total_financial_exposure_m_usd": round(total_financial_exposure_m, 2),
            "top_dependencies": [s["service_key"] for s in top_dependencies],
            "high_impact_services": [s["service_key"] for s in high_impact_services],
            "encore_composite_score": encore_score,
            "primary_impact_drivers": primary_drivers,
        }

    # ------------------------------------------------------------------
    # 6. Full Assessment Orchestrator
    # ------------------------------------------------------------------

    def run_full_assessment(
        self,
        entity_id: str,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Orchestrate all 5 sub-assessments and compute composite nature_strategy_score.

        Weights: SBTN 35% + TNFD 30% + NRL 15% + GBF 10% + ENCORE 10%
        """
        logger.info("run_full_assessment entity=%s", entity_id)

        # Extract sub-inputs
        sectors = request_data.get("sectors", [])
        locations = request_data.get("locations", [])
        current_targets = request_data.get("current_targets", [])
        disclosures = request_data.get("disclosures", {})
        governance_data = request_data.get("governance_data", {})
        strategy_data = request_data.get("strategy_data", {})
        risk_data = request_data.get("risk_data", {})
        metrics_data = request_data.get("metrics_data", {})
        operations = request_data.get("operations", [])
        supply_chain_countries = request_data.get("supply_chain_countries", [])
        portfolio_locations = request_data.get("portfolio_locations", [])
        sector = sectors[0] if sectors else "financial_services"
        operations_data = request_data.get("operations_data", {})

        sbtn_result = self.assess_sbtn_steps(entity_id, sectors, locations, current_targets, disclosures)
        tnfd_result = self.assess_tnfd_disclosure(entity_id, governance_data, strategy_data, risk_data, metrics_data)
        nrl_result = self.assess_nrl_exposure(entity_id, operations, supply_chain_countries)
        gbf_result = self.assess_gbf_target3(entity_id, portfolio_locations)
        encore_result = self.assess_encore_dependencies(entity_id, sector, operations_data)

        sbtn_score = sbtn_result["sbtn_composite_score"]
        tnfd_score = tnfd_result["composite_tnfd_score"]
        nrl_score = nrl_result["nrl_compliance_score"]
        gbf_score = gbf_result["gbf_alignment_score"]
        encore_score = encore_result["encore_composite_score"]

        nature_strategy_score = round(
            sbtn_score * 0.35
            + tnfd_score * 0.30
            + nrl_score * 0.15
            + gbf_score * 0.10
            + encore_score * 0.10,
            1,
        )

        # Assign maturity tier
        maturity_tier = "minimal"
        for tier_name, tier_data in NATURE_MATURITY_TIERS.items():
            if tier_data["min_score"] <= nature_strategy_score <= tier_data["max_score"]:
                maturity_tier = tier_name
                break

        tier_info = NATURE_MATURITY_TIERS[maturity_tier]

        # Key gaps and priorities
        priority_actions: List[str] = []
        if sbtn_score < 40:
            priority_actions.append("Initiate SBTN Step 1 materiality screening using SBTN tool")
        if tnfd_score < 50:
            priority_actions.append("Complete TNFD LEAP approach and publish core R1-R14 disclosures")
        if nrl_score < 60 and nrl_result["eu_operations_exposure"]:
            priority_actions.append("File NRL restoration plan for EU habitat sites by 2024 standstill deadline")
        if gbf_score < 70:
            priority_actions.append("Screen portfolio for 30x30 zone exposure and engage affected countries")
        if encore_score < 60:
            priority_actions.append("Quantify top ENCORE ecosystem service dependencies and set mitigation targets")

        return {
            "entity_id": entity_id,
            "assessment_type": "full_nature_strategy",
            "framework_versions": {
                "sbtn": "SBTN v1.1 (2023)",
                "tnfd": "TNFD v1.0 (Sep 2023)",
                "nrl": "Regulation (EU) 2024/1991",
                "gbf": "CBD KM-GBF Target 3 (2022)",
                "encore": "ENCORE v2.1 (2023)",
            },
            "component_scores": {
                "sbtn_score": sbtn_score,
                "tnfd_score": tnfd_score,
                "nrl_score": nrl_score,
                "gbf_score": gbf_score,
                "encore_score": encore_score,
            },
            "score_weights": {
                "sbtn": 0.35, "tnfd": 0.30, "nrl": 0.15, "gbf": 0.10, "encore": 0.10,
            },
            "nature_strategy_score": nature_strategy_score,
            "maturity_tier": maturity_tier,
            "maturity_description": tier_info["description"],
            "investor_signal": tier_info["investor_signal"],
            "regulatory_flags": tier_info["regulatory_flags"],
            "priority_actions": priority_actions,
            "sbtn_result": sbtn_result,
            "tnfd_result": tnfd_result,
            "nrl_result": nrl_result,
            "gbf_result": gbf_result,
            "encore_result": encore_result,
        }

    # ------------------------------------------------------------------
    # Reference data helpers
    # ------------------------------------------------------------------

    def ref_sbtn_sectors(self) -> Dict[str, Any]:
        return SBTN_SECTOR_IMPACT_MAP

    def ref_tnfd_metrics(self) -> List[Dict[str, Any]]:
        return TNFD_DISCLOSURE_REQUIREMENTS

    def ref_nrl_habitats(self) -> Dict[str, Any]:
        return EU_NRL_HABITAT_TYPES

    def ref_encore_services(self) -> Dict[str, Any]:
        return ENCORE_ECOSYSTEM_SERVICES

    def ref_gbf_countries(self) -> Dict[str, Any]:
        return GBF_TARGET_3_COUNTRIES

    def ref_maturity_tiers(self) -> Dict[str, Any]:
        return NATURE_MATURITY_TIERS


def get_engine() -> CorporateNatureStrategyEngine:
    """Return a module-level singleton engine."""
    return CorporateNatureStrategyEngine()
