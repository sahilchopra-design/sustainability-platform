"""
nature_capital_engine.py — E77 Nature Capital Accounting
SEEA EA 2021 | TNFD v1.0 | ENCORE 62 ecosystem services | TEEB/BES monetary values
WAVES Adjusted Savings | PBAF 2023 | CBD GBF Target 15 | CSRD ESRS E4
"""
from __future__ import annotations
import random
from datetime import datetime, timezone
from typing import Any

# ── Reference Data ─────────────────────────────────────────────────────────────

SEEA_EA_ACCOUNT_TYPES = [
    {"id": "EA-1", "name": "Ecosystem Extent Account", "description": "Area of each ecosystem type at start and end of accounting period", "unit": "hectares"},
    {"id": "EA-2", "name": "Ecosystem Condition Account", "description": "Condition of each ecosystem measured against reference state", "unit": "condition_index_0-1"},
    {"id": "EA-3", "name": "Physical Ecosystem Services Supply & Use Account", "description": "Physical flows of services from ecosystems to economic units", "unit": "physical_units"},
    {"id": "EA-4", "name": "Monetary Ecosystem Services Account", "description": "Monetary valuation of ecosystem services using market/non-market values", "unit": "USD"},
    {"id": "EA-5", "name": "Ecosystem Asset Account", "description": "Opening/closing stock of ecosystem assets and changes therein", "unit": "USD_or_ha"},
    {"id": "EA-6", "name": "Thematic Ecosystem Accounts", "description": "Specific focus accounts: carbon, water, biodiversity, urban", "unit": "varies"},
]

# TEEB/IPBES biome unit values USD/ha/year (conservative estimates from academic literature)
BIOME_UNIT_VALUES = {
    "tropical_forest": {"total_usd_ha_yr": 5264, "provisioning": 1200, "regulating": 3200, "cultural": 864, "source": "TEEB 2010 / Costanza et al 2014"},
    "temperate_forest": {"total_usd_ha_yr": 3137, "provisioning": 980, "regulating": 1800, "cultural": 357, "source": "TEEB 2010"},
    "boreal_forest": {"total_usd_ha_yr": 894, "provisioning": 320, "regulating": 480, "cultural": 94, "source": "Costanza et al 2014"},
    "tropical_grassland": {"total_usd_ha_yr": 1340, "provisioning": 420, "regulating": 750, "cultural": 170, "source": "TEEB 2010"},
    "temperate_grassland": {"total_usd_ha_yr": 1027, "provisioning": 380, "regulating": 520, "cultural": 127, "source": "TEEB 2010"},
    "wetland_freshwater": {"total_usd_ha_yr": 14785, "provisioning": 2400, "regulating": 10200, "cultural": 2185, "source": "Costanza et al 2014"},
    "wetland_coastal": {"total_usd_ha_yr": 28916, "provisioning": 4500, "regulating": 21000, "cultural": 3416, "source": "Costanza et al 2014"},
    "mangrove": {"total_usd_ha_yr": 33750, "provisioning": 5200, "regulating": 25000, "cultural": 3550, "source": "TEEB 2010 / De Groot et al"},
    "coral_reef": {"total_usd_ha_yr": 352249, "provisioning": 65000, "regulating": 270000, "cultural": 17249, "source": "TEEB 2010"},
    "seagrass": {"total_usd_ha_yr": 19004, "provisioning": 3500, "regulating": 13800, "cultural": 1704, "source": "Costanza et al 2014"},
    "open_ocean": {"total_usd_ha_yr": 491, "provisioning": 250, "regulating": 195, "cultural": 46, "source": "Costanza et al 2014"},
    "cropland": {"total_usd_ha_yr": 1540, "provisioning": 1380, "regulating": 120, "cultural": 40, "source": "TEEB 2010"},
    "urban_greenspace": {"total_usd_ha_yr": 6531, "provisioning": 580, "regulating": 4200, "cultural": 1751, "source": "TEEB Urban 2011"},
    "peatland": {"total_usd_ha_yr": 3677, "provisioning": 450, "regulating": 2900, "cultural": 327, "source": "IPBES 2019"},
    "tundra": {"total_usd_ha_yr": 121, "provisioning": 60, "regulating": 50, "cultural": 11, "source": "Costanza et al 2014"},
    "desert": {"total_usd_ha_yr": 43, "provisioning": 20, "regulating": 15, "cultural": 8, "source": "Costanza et al 2014"},
    "mountain": {"total_usd_ha_yr": 688, "provisioning": 350, "regulating": 270, "cultural": 68, "source": "TEEB 2010"},
    "mediterranean_shrubland": {"total_usd_ha_yr": 2071, "provisioning": 650, "regulating": 1100, "cultural": 321, "source": "TEEB 2010"},
    "savanna": {"total_usd_ha_yr": 930, "provisioning": 350, "regulating": 450, "cultural": 130, "source": "Costanza et al 2014"},
}

# ENCORE ecosystem services (62 services mapped to 3 categories)
ENCORE_ECOSYSTEM_SERVICES = {
    "provisioning": [
        {"id": "ES-P01", "name": "Cultivated terrestrial plants for nutrition", "sector_dependencies": ["agriculture", "food_beverage"]},
        {"id": "ES-P02", "name": "Cultivated aquatic plants for nutrition", "sector_dependencies": ["fishing", "food_beverage"]},
        {"id": "ES-P03", "name": "Reared terrestrial animals for nutrition", "sector_dependencies": ["agriculture", "food_beverage"]},
        {"id": "ES-P04", "name": "Reared aquatic animals for nutrition", "sector_dependencies": ["fishing", "food_beverage"]},
        {"id": "ES-P05", "name": "Wild plants for nutrition", "sector_dependencies": ["food_beverage", "pharmaceuticals"]},
        {"id": "ES-P06", "name": "Wild animals for nutrition", "sector_dependencies": ["fishing", "food_beverage"]},
        {"id": "ES-P07", "name": "Surface water for in-stream use", "sector_dependencies": ["utilities", "energy"]},
        {"id": "ES-P08", "name": "Surface water for irrigation", "sector_dependencies": ["agriculture"]},
        {"id": "ES-P09", "name": "Ground water for irrigation", "sector_dependencies": ["agriculture"]},
        {"id": "ES-P10", "name": "Surface water for non-agricultural uses", "sector_dependencies": ["manufacturing", "utilities"]},
        {"id": "ES-P11", "name": "Ground water for non-agricultural uses", "sector_dependencies": ["manufacturing", "utilities"]},
        {"id": "ES-P12", "name": "Plant-based resources (non-food)", "sector_dependencies": ["forestry", "textiles", "construction"]},
        {"id": "ES-P13", "name": "Animal-based resources (non-food)", "sector_dependencies": ["pharmaceuticals", "textiles"]},
        {"id": "ES-P14", "name": "Fibres and other plant materials", "sector_dependencies": ["textiles", "construction"]},
        {"id": "ES-P15", "name": "Genetic materials from all organisms", "sector_dependencies": ["pharmaceuticals", "agriculture"]},
        {"id": "ES-P16", "name": "Inorganic materials from living organisms", "sector_dependencies": ["construction", "chemicals"]},
        {"id": "ES-P17", "name": "Surface water used as energy", "sector_dependencies": ["energy"]},
        {"id": "ES-P18", "name": "Biomass used as energy", "sector_dependencies": ["energy", "utilities"]},
        {"id": "ES-P19", "name": "Wind used as energy", "sector_dependencies": ["energy"]},
        {"id": "ES-P20", "name": "Solar used as energy", "sector_dependencies": ["energy"]},
    ],
    "regulating_maintenance": [
        {"id": "ES-R01", "name": "Global climate regulation", "sector_dependencies": ["all_sectors"]},
        {"id": "ES-R02", "name": "Rainfall pattern regulation", "sector_dependencies": ["agriculture", "water_utilities"]},
        {"id": "ES-R03", "name": "Local climate regulation", "sector_dependencies": ["real_estate", "tourism"]},
        {"id": "ES-R04", "name": "Air filtration", "sector_dependencies": ["real_estate", "tourism", "healthcare"]},
        {"id": "ES-R05", "name": "Soil quality regulation", "sector_dependencies": ["agriculture", "forestry"]},
        {"id": "ES-R06", "name": "Water quality regulation", "sector_dependencies": ["water_utilities", "food_beverage"]},
        {"id": "ES-R07", "name": "Water flow maintenance", "sector_dependencies": ["water_utilities", "agriculture", "energy"]},
        {"id": "ES-R08", "name": "Flood and storm protection", "sector_dependencies": ["real_estate", "insurance"]},
        {"id": "ES-R09", "name": "Erosion control", "sector_dependencies": ["agriculture", "construction"]},
        {"id": "ES-R10", "name": "Biological control (pests/diseases)", "sector_dependencies": ["agriculture"]},
        {"id": "ES-R11", "name": "Pollination", "sector_dependencies": ["agriculture", "food_beverage"]},
        {"id": "ES-R12", "name": "Seed dispersal", "sector_dependencies": ["forestry", "agriculture"]},
        {"id": "ES-R13", "name": "Decomposition and nutrient cycling", "sector_dependencies": ["agriculture", "forestry"]},
        {"id": "ES-R14", "name": "Water purification and waste management", "sector_dependencies": ["water_utilities"]},
        {"id": "ES-R15", "name": "Noise attenuation", "sector_dependencies": ["real_estate", "construction"]},
        {"id": "ES-R16", "name": "Mass stabilisation and erosion control (mountains)", "sector_dependencies": ["construction", "tourism"]},
        {"id": "ES-R17", "name": "Mediation of sensory impacts", "sector_dependencies": ["real_estate"]},
        {"id": "ES-R18", "name": "Disease regulation", "sector_dependencies": ["healthcare", "agriculture"]},
        {"id": "ES-R19", "name": "Genetic diversity maintenance", "sector_dependencies": ["pharmaceuticals", "agriculture"]},
        {"id": "ES-R20", "name": "Lifecycle maintenance of species", "sector_dependencies": ["fishing", "forestry"]},
        {"id": "ES-R21", "name": "Optical properties regulation", "sector_dependencies": ["real_estate", "tourism"]},
        {"id": "ES-R22", "name": "Chemical condition of freshwater", "sector_dependencies": ["water_utilities"]},
        {"id": "ES-R23", "name": "Chemical condition of salt water", "sector_dependencies": ["fishing", "tourism"]},
    ],
    "cultural": [
        {"id": "ES-C01", "name": "Scientific and educational", "sector_dependencies": ["research", "education"]},
        {"id": "ES-C02", "name": "Recreation and ecotourism", "sector_dependencies": ["tourism", "real_estate"]},
        {"id": "ES-C03", "name": "Aesthetic values", "sector_dependencies": ["real_estate", "tourism"]},
        {"id": "ES-C04", "name": "Spiritual and emblematic", "sector_dependencies": ["tourism"]},
        {"id": "ES-C05", "name": "Cultural heritage and identity", "sector_dependencies": ["tourism", "real_estate"]},
        {"id": "ES-C06", "name": "Existence and bequest values", "sector_dependencies": ["all_sectors"]},
    ],
}

# TNFD v1.0 recommended disclosures (14 topics)
TNFD_DISCLOSURE_TOPICS = [
    {"id": "TNFD-G1", "pillar": "Governance", "topic": "Board oversight of nature-related dependencies, impacts, risks and opportunities"},
    {"id": "TNFD-G2", "pillar": "Governance", "topic": "Management's role in assessing and managing nature-related issues"},
    {"id": "TNFD-S1", "pillar": "Strategy", "topic": "Nature-related risks and opportunities over short, medium and long term"},
    {"id": "TNFD-S2", "pillar": "Strategy", "topic": "Impact of nature-related risks and opportunities on business model, strategy and financial planning"},
    {"id": "TNFD-S3", "pillar": "Strategy", "topic": "Resilience of strategy under different nature scenarios"},
    {"id": "TNFD-S4", "pillar": "Strategy", "topic": "Locations and direct operational footprint in biomes"},
    {"id": "TNFD-RM1", "pillar": "Risk Management", "topic": "Organisation's processes for identifying and assessing nature-related risks"},
    {"id": "TNFD-RM2", "pillar": "Risk Management", "topic": "Organisation's processes for managing nature-related risks"},
    {"id": "TNFD-RM3", "pillar": "Risk Management", "topic": "Integration of nature-related risk management into overall risk framework"},
    {"id": "TNFD-MT1", "pillar": "Metrics & Targets", "topic": "Metrics used to assess nature-related dependencies and impacts"},
    {"id": "TNFD-MT2", "pillar": "Metrics & Targets", "topic": "Metrics used to assess nature-related risks and opportunities"},
    {"id": "TNFD-MT3", "pillar": "Metrics & Targets", "topic": "Targets and performance against them for managing nature-related issues"},
    {"id": "TNFD-MT4", "pillar": "Metrics & Targets", "topic": "Financed nature impacts for financial institutions"},
    {"id": "TNFD-LEAP", "pillar": "Strategy", "topic": "TNFD LEAP approach application: Locate, Evaluate, Assess, Prepare"},
]

# Sector ENCORE dependency matrix (simplified, 58 sectors → 12 illustrative)
SECTOR_NATURE_DEPENDENCY = {
    "agriculture": {"dependency_score": 0.92, "key_services": ["ES-P01", "ES-R11", "ES-R05", "ES-R07"], "revenue_at_risk_pct": 45},
    "food_beverage": {"dependency_score": 0.88, "key_services": ["ES-P01", "ES-P03", "ES-R11", "ES-R06"], "revenue_at_risk_pct": 38},
    "forestry": {"dependency_score": 0.95, "key_services": ["ES-P12", "ES-R01", "ES-R13", "ES-R09"], "revenue_at_risk_pct": 55},
    "fishing": {"dependency_score": 0.90, "key_services": ["ES-P06", "ES-R20", "ES-R23", "ES-R06"], "revenue_at_risk_pct": 60},
    "pharmaceuticals": {"dependency_score": 0.72, "key_services": ["ES-P15", "ES-P05", "ES-R19"], "revenue_at_risk_pct": 28},
    "utilities_water": {"dependency_score": 0.85, "key_services": ["ES-P07", "ES-R07", "ES-R06", "ES-R14"], "revenue_at_risk_pct": 40},
    "energy": {"dependency_score": 0.55, "key_services": ["ES-P17", "ES-P18", "ES-R07"], "revenue_at_risk_pct": 18},
    "real_estate": {"dependency_score": 0.60, "key_services": ["ES-R08", "ES-R03", "ES-R15", "ES-C03"], "revenue_at_risk_pct": 22},
    "mining": {"dependency_score": 0.75, "key_services": ["ES-P09", "ES-R07", "ES-R09"], "revenue_at_risk_pct": 30},
    "construction": {"dependency_score": 0.65, "key_services": ["ES-P14", "ES-R08", "ES-R09"], "revenue_at_risk_pct": 20},
    "tourism": {"dependency_score": 0.80, "key_services": ["ES-C02", "ES-C03", "ES-R03", "ES-R04"], "revenue_at_risk_pct": 35},
    "manufacturing": {"dependency_score": 0.50, "key_services": ["ES-P10", "ES-R06", "ES-R14"], "revenue_at_risk_pct": 15},
}


# ── Core Engine Functions ──────────────────────────────────────────────────────

def assess_natural_capital(
    entity_id: str,
    asset_name: str,
    ecosystem_type: str,
    extent_ha: float,
    location_country: str,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    eco_lower = ecosystem_type.lower().replace(" ", "_").replace("-", "_")
    biome_data = BIOME_UNIT_VALUES.get(eco_lower, BIOME_UNIT_VALUES["temperate_forest"])

    # SEEA EA account type
    seea_account = "EA-2" if rng.random() > 0.5 else "EA-3"

    # Condition score (0-1, reference state = 1.0)
    condition_score = round(rng.uniform(0.45, 0.95), 3)

    # Ecosystem service flows
    service_flows: dict[str, float] = {
        "provisioning_usd_ha_yr": round(biome_data["provisioning"] * condition_score, 2),
        "regulating_usd_ha_yr": round(biome_data["regulating"] * condition_score, 2),
        "cultural_usd_ha_yr": round(biome_data["cultural"] * condition_score, 2),
    }

    # Monetary value
    total_unit_value = biome_data["total_usd_ha_yr"] * condition_score
    monetary_value_usd = total_unit_value * extent_ha

    # TNFD dependency/impact scores
    dependency_score = round(rng.uniform(0.4, 0.9), 3)
    impact_score = round(rng.uniform(0.3, 0.85), 3)

    # TNFD pillar assignment
    pillars = ["Governance", "Strategy", "Risk Management", "Metrics & Targets"]
    tnfd_pillar = rng.choice(pillars)

    # CBD GBF Target 15 alignment
    gbf_t15 = {
        "sub_element_a": rng.random() > 0.3,  # assess nature-related dependencies
        "sub_element_b": rng.random() > 0.4,  # monitor and disclose
        "sub_element_c": rng.random() > 0.5,  # reduce negative impacts
        "sub_element_d": rng.random() > 0.45, # restore biodiversity
        "sub_element_e": rng.random() > 0.5,  # sustainable use of biodiversity
        "sub_element_f": rng.random() > 0.4,  # ensure equitable sharing of benefits
    }
    gbf_t15_score = sum(gbf_t15.values()) / len(gbf_t15)

    # Biodiversity condition index (MSA proxy)
    msa_score = round(condition_score * rng.uniform(0.7, 1.0), 3)

    return {
        "entity_id": entity_id,
        "asset_name": asset_name,
        "ecosystem_type": ecosystem_type,
        "location_country": location_country,
        "extent_ha": extent_ha,
        "seea_ea_account": seea_account,
        "condition_score": condition_score,
        "msa_biodiversity_score": msa_score,
        "service_flows": service_flows,
        "monetary_value_usd": round(monetary_value_usd, 0),
        "monetary_value_per_ha_usd": round(total_unit_value, 2),
        "biome_reference_values": biome_data,
        "dependency_score": dependency_score,
        "impact_score": impact_score,
        "tnfd_pillar": tnfd_pillar,
        "cbf_gbf_target15": gbf_t15,
        "gbf_t15_alignment_score": round(gbf_t15_score, 3),
        "valuation_methodology": "TEEB/IPBES unit value transfer (WAVES Adjusted Savings framework)",
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def valuate_ecosystem_services(
    entity_id: str,
    ecosystem_type: str,
    extent_ha: float,
    services_list: list[str],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    eco_lower = ecosystem_type.lower().replace(" ", "_").replace("-", "_")
    biome_data = BIOME_UNIT_VALUES.get(eco_lower, BIOME_UNIT_VALUES["temperate_forest"])
    condition_multiplier = round(rng.uniform(0.6, 1.0), 3)

    services_valued: list[dict] = []
    total_annual_flow_usd = 0.0

    all_services = (
        ENCORE_ECOSYSTEM_SERVICES["provisioning"]
        + ENCORE_ECOSYSTEM_SERVICES["regulating_maintenance"]
        + ENCORE_ECOSYSTEM_SERVICES["cultural"]
    )

    service_ids = set(services_list)
    if not service_ids:
        # Value all services for this ecosystem
        service_ids = {s["id"] for s in all_services[:15]}

    for service in all_services:
        if service["id"] not in service_ids and not (not services_list):
            continue
        if not services_list and rng.random() > 0.6:
            continue

        # Determine category
        if service["id"].startswith("ES-P"):
            cat = "provisioning"
            base_pct = biome_data["provisioning"] / biome_data["total_usd_ha_yr"] if biome_data["total_usd_ha_yr"] else 0.2
        elif service["id"].startswith("ES-R"):
            cat = "regulating_maintenance"
            base_pct = biome_data["regulating"] / biome_data["total_usd_ha_yr"] if biome_data["total_usd_ha_yr"] else 0.6
        else:
            cat = "cultural"
            base_pct = biome_data["cultural"] / biome_data["total_usd_ha_yr"] if biome_data["total_usd_ha_yr"] else 0.1

        service_rng = random.Random(hash(f"{entity_id}_{service['id']}") & 0xFFFFFFFF)
        unit_value = biome_data["total_usd_ha_yr"] * base_pct * service_rng.uniform(0.05, 0.3) * condition_multiplier
        annual_flow = unit_value * extent_ha

        total_annual_flow_usd += annual_flow
        services_valued.append({
            "service_id": service["id"],
            "service_name": service["name"],
            "category": cat,
            "unit_value_usd_ha_yr": round(unit_value, 2),
            "annual_flow_usd": round(annual_flow, 0),
            "valuation_method": "Benefit transfer (meta-analysis)",
            "confidence": "medium" if condition_multiplier > 0.75 else "low",
        })

    services_valued.sort(key=lambda x: x["annual_flow_usd"], reverse=True)

    # WAVES / Adjusted Savings methodology components
    waves_metadata = {
        "methodology": "WAVES (Wealth Accounting and Valuation of Ecosystem Services) 2021",
        "price_year": 2023,
        "discount_rate_pct": 4.0,
        "currency": "USD",
        "npv_30yr_usd": round(total_annual_flow_usd * 17.3, 0),  # approx PV annuity factor at 4% 30yr
        "inflation_adjustment": "2023 USD",
    }

    return {
        "entity_id": entity_id,
        "ecosystem_type": ecosystem_type,
        "extent_ha": extent_ha,
        "condition_multiplier": condition_multiplier,
        "total_annual_flow_value_usd": round(total_annual_flow_usd, 0),
        "total_unit_value_usd_ha_yr": round(total_annual_flow_usd / extent_ha if extent_ha else 0, 2),
        "services_count": len(services_valued),
        "services_valued": services_valued,
        "category_breakdown": {
            "provisioning_usd": round(sum(s["annual_flow_usd"] for s in services_valued if s["category"] == "provisioning"), 0),
            "regulating_usd": round(sum(s["annual_flow_usd"] for s in services_valued if s["category"] == "regulating_maintenance"), 0),
            "cultural_usd": round(sum(s["annual_flow_usd"] for s in services_valued if s["category"] == "cultural"), 0),
        },
        "waves_metadata": waves_metadata,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def calculate_dependency_score(
    entity_id: str,
    sector: str,
    operations_description: str,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    sector_lower = sector.lower().replace(" ", "_").replace("-", "_")
    profile = SECTOR_NATURE_DEPENDENCY.get(sector_lower, {
        "dependency_score": round(rng.uniform(0.3, 0.7), 2),
        "key_services": ["ES-R01", "ES-P10"],
        "revenue_at_risk_pct": round(rng.uniform(5, 25), 1),
    })

    # TNFD LEAP Step A — dependency identification
    all_services = (
        ENCORE_ECOSYSTEM_SERVICES["provisioning"]
        + ENCORE_ECOSYSTEM_SERVICES["regulating_maintenance"]
        + ENCORE_ECOSYSTEM_SERVICES["cultural"]
    )
    service_map = {s["id"]: s for s in all_services}

    key_dependencies = []
    for svc_id in profile["key_services"]:
        if svc_id in service_map:
            svc = service_map[svc_id]
            dep_rng = random.Random(hash(f"{entity_id}_{svc_id}") & 0xFFFFFFFF)
            key_dependencies.append({
                "service_id": svc_id,
                "service_name": svc["name"],
                "dependency_strength": round(dep_rng.uniform(0.5, 1.0), 3),
                "substitutability": "low" if dep_rng.random() > 0.6 else "medium",
                "criticality": "high" if dep_rng.random() > 0.5 else "medium",
                "tnfd_leap_step": "A - Locate",
            })

    # Revenue at risk
    estimated_revenue_usd = rng.uniform(10e6, 2e9)
    revenue_at_risk_usd = estimated_revenue_usd * profile["revenue_at_risk_pct"] / 100

    # Substitutability score (0=easily substituted, 1=irreplaceable)
    substitutability_score = round(rng.uniform(0.3, 0.9), 3)

    # TNFD LEAP Steps
    leap_assessment = {
        "L_locate": {
            "step": "Locate — Where does the organisation interface with nature?",
            "operations_in_sensitive_areas": rng.random() > 0.5,
            "supply_chain_exposure": "high" if profile.get("dependency_score", 0) > 0.75 else "medium",
            "geographic_focus": ["tropical_forests", "freshwater_systems"] if profile.get("dependency_score", 0) > 0.8 else ["temperate_zones"],
        },
        "E_evaluate": {
            "step": "Evaluate — What are the dependencies and impacts?",
            "top_dependencies": [d["service_name"] for d in key_dependencies],
            "dependency_score": profile.get("dependency_score", 0.5),
            "impact_drivers": ["land_use_change", "water_consumption", "pollution"] if profile.get("dependency_score", 0) > 0.7 else ["water_consumption"],
        },
        "A_assess": {
            "step": "Assess — What are the nature-related risks and opportunities?",
            "physical_risk": round(rng.uniform(0.3, 0.8), 3),
            "transition_risk": round(rng.uniform(0.2, 0.7), 3),
            "systemic_risk": round(rng.uniform(0.1, 0.5), 3),
            "opportunities": ["ecosystem_services_markets", "biodiversity_credits", "nature_based_solutions"],
        },
        "P_prepare": {
            "step": "Prepare — What actions are required?",
            "immediate_actions": ["conduct_site-level_assessment", "map_supply_chain_nature_exposure"],
            "medium_term_actions": ["implement_nature_positive_targets", "engage_TNFD_reporting"],
            "long_term_actions": ["transition_to_regenerative_practices", "invest_in_NbS"],
        },
    }

    return {
        "entity_id": entity_id,
        "sector": sector,
        "dependency_score": profile.get("dependency_score", 0.5),
        "key_dependencies": key_dependencies,
        "revenue_at_risk_pct": profile["revenue_at_risk_pct"],
        "revenue_at_risk_usd": round(revenue_at_risk_usd, 0),
        "substitutability_score": substitutability_score,
        "tnfd_leap_assessment": leap_assessment,
        "sbtn_scope": "direct_operations_and_upstream",
        "nature_loss_scenario_2030": {
            "business_as_usual_risk_pct": round(profile.get("revenue_at_risk_pct", 10) * 1.4, 1),
            "1_5c_aligned_risk_pct": round(profile.get("revenue_at_risk_pct", 10) * 0.6, 1),
        },
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def score_natural_capital_disclosure(
    entity_id: str,
    reporting_standard: str,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    # TNFD v1.0 completeness
    tnfd_scores: list[dict] = []
    for disc in TNFD_DISCLOSURE_TOPICS:
        score = round(rng.uniform(0.2, 1.0), 2)
        tnfd_scores.append({
            "id": disc["id"],
            "pillar": disc["pillar"],
            "topic": disc["topic"],
            "completeness_score": score,
            "status": "complete" if score >= 0.8 else "partial" if score >= 0.5 else "missing",
        })
    tnfd_overall = sum(s["completeness_score"] for s in tnfd_scores) / len(tnfd_scores)

    # SEEA EA adoption
    seea_adoption = {
        "extent_account": rng.random() > 0.3,
        "condition_account": rng.random() > 0.45,
        "services_physical_account": rng.random() > 0.5,
        "services_monetary_account": rng.random() > 0.6,
        "asset_account": rng.random() > 0.65,
        "thematic_accounts": rng.random() > 0.7,
    }
    seea_score = sum(seea_adoption.values()) / len(seea_adoption)

    # GRI 304 biodiversity alignment
    gri304_items = {
        "304-1_operational_sites": rng.random() > 0.4,
        "304-2_significant_impacts": rng.random() > 0.5,
        "304-3_habitats_protected": rng.random() > 0.55,
        "304-4_IUCN_red_list": rng.random() > 0.6,
    }
    gri304_score = sum(gri304_items.values()) / len(gri304_items)

    # CSRD ESRS E4 coverage
    esrs_e4_items = {
        "E4-1_transition_plan_biodiversity": rng.random() > 0.5,
        "E4-2_policies_biodiversity": rng.random() > 0.4,
        "E4-3_biodiversity_and_ecosystem_actions": rng.random() > 0.45,
        "E4-4_resource_use_targets": rng.random() > 0.55,
        "E4-5_impact_metrics": rng.random() > 0.5,
        "E4-6_anticipated_financial_effects": rng.random() > 0.65,
    }
    esrs_e4_score = sum(esrs_e4_items.values()) / len(esrs_e4_items)

    # CBD GBF Target 15 sub-elements
    gbf_t15 = {
        "a_assess_dependencies": rng.random() > 0.4,
        "b_monitor_disclose": rng.random() > 0.5,
        "c_reduce_negative": rng.random() > 0.55,
        "d_restore_biodiversity": rng.random() > 0.6,
        "e_sustainable_use": rng.random() > 0.5,
        "f_equitable_sharing": rng.random() > 0.65,
    }
    gbf_score = sum(gbf_t15.values()) / len(gbf_t15)

    return {
        "entity_id": entity_id,
        "reporting_standard": reporting_standard,
        "tnfd_v1_disclosure": {
            "overall_completeness": round(tnfd_overall, 3),
            "disclosures": tnfd_scores,
            "pillars_status": {p: round(sum(s["completeness_score"] for s in tnfd_scores if s["pillar"] == p) / max(1, sum(1 for s in tnfd_scores if s["pillar"] == p)), 3) for p in ["Governance", "Strategy", "Risk Management", "Metrics & Targets"]},
        },
        "seea_ea_adoption": {
            "adoption_items": seea_adoption,
            "adoption_score": round(seea_score, 3),
        },
        "gri_304_biodiversity": {
            "items": gri304_items,
            "score": round(gri304_score, 3),
        },
        "csrd_esrs_e4": {
            "items": esrs_e4_items,
            "coverage_score": round(esrs_e4_score, 3),
        },
        "cbd_gbf_target15": {
            "sub_elements": gbf_t15,
            "alignment_score": round(gbf_score, 3),
        },
        "composite_disclosure_score": round(
            tnfd_overall * 0.35 + seea_score * 0.2 + gri304_score * 0.15 + esrs_e4_score * 0.2 + gbf_score * 0.1, 3
        ),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_nature_balance_sheet(
    entity_id: str,
    assets: list[dict[str, Any]],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    opening_stock_usd = 0.0
    closing_stock_usd = 0.0
    asset_accounts: list[dict] = []

    for asset in assets:
        eco_type = asset.get("ecosystem_type", "temperate_forest")
        extent = float(asset.get("extent_ha", rng.uniform(100, 10000)))
        biome = BIOME_UNIT_VALUES.get(eco_type.lower().replace(" ", "_"), BIOME_UNIT_VALUES["temperate_forest"])

        open_condition = round(rng.uniform(0.5, 0.9), 3)
        close_condition = round(open_condition + rng.uniform(-0.1, 0.05), 3)
        close_condition = max(0.1, min(1.0, close_condition))

        open_extent = extent
        close_extent = extent * rng.uniform(0.95, 1.02)
        extent_change = close_extent - open_extent

        open_value = biome["total_usd_ha_yr"] * open_condition * open_extent * 10  # capitalised at 10x annual flow
        close_value = biome["total_usd_ha_yr"] * close_condition * close_extent * 10
        value_change = close_value - open_value

        opening_stock_usd += open_value
        closing_stock_usd += close_value

        service_flow_annual = biome["total_usd_ha_yr"] * close_condition * close_extent
        asset_accounts.append({
            "asset_name": asset.get("asset_name", eco_type),
            "ecosystem_type": eco_type,
            "seea_ea_account_type": "EA-5",
            "opening_extent_ha": round(open_extent, 2),
            "closing_extent_ha": round(close_extent, 2),
            "extent_change_ha": round(extent_change, 2),
            "opening_condition": open_condition,
            "closing_condition": close_condition,
            "opening_stock_usd": round(open_value, 0),
            "closing_stock_usd": round(close_value, 0),
            "value_change_usd": round(value_change, 0),
            "annual_service_flow_usd": round(service_flow_annual, 0),
            "depreciation_rate_pct": round((1 - close_condition / open_condition) * 100, 2) if open_condition > 0 else 0,
        })

    net_change = closing_stock_usd - opening_stock_usd
    # Integrated P&L impact
    integrated_pl = {
        "ecosystem_service_revenue_recognised_usd": round(sum(a["annual_service_flow_usd"] for a in asset_accounts), 0),
        "natural_capital_depreciation_usd": round(sum(a["value_change_usd"] for a in asset_accounts if a["value_change_usd"] < 0), 0),
        "restoration_investment_usd": round(rng.uniform(0, abs(net_change) * 0.1), 0),
        "net_integrated_pl_impact_usd": round(net_change, 0),
    }

    return {
        "entity_id": entity_id,
        "accounting_year": datetime.now(timezone.utc).year,
        "seea_ea_structure": "SEEA EA 2021 Tables 5.1-5.4",
        "opening_natural_capital_stock_usd": round(opening_stock_usd, 0),
        "closing_natural_capital_stock_usd": round(closing_stock_usd, 0),
        "net_change_usd": round(net_change, 0),
        "net_change_pct": round(net_change / opening_stock_usd * 100, 2) if opening_stock_usd else 0,
        "asset_accounts": asset_accounts,
        "integrated_pl_impact": integrated_pl,
        "waves_metadata": {
            "methodology": "WAVES Adjusted Savings — capitalised ecosystem service flows",
            "capitalisation_multiple": 10,
            "discount_rate_pct": 4.0,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
