"""
Biodiversity Credits & Nature Markets Engine — E88
====================================================
Standards covered:
- UK BNG Environment Act 2021 (DEFRA Metric 4.0)
- Verra VM0033 Methodology for Tidal Wetland / Coastal Ecosystem
- Plan Vivo Standard (community-based land management)
- TNFD v1.0 LEAP process (Location / Evaluate / Assess / Prepare)
- Gold Standard for the Global Goals — Nature Framework
- Architecture for REDD+ Transactions (ART TREES v2.0)
- Kunming-Montreal Global Biodiversity Framework (GBF) Target 15
- TEEB / SEEA-EA ecosystem service valuation
- ENCORE (Exploring Natural Capital Opportunities, Risks and Exposure)
"""
from __future__ import annotations

import math
import random
from typing import Any

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

BIODIVERSITY_CREDIT_STANDARDS: dict[str, dict[str, Any]] = {
    "Verra_VM0033": {
        "name": "Verra VM0033 — Tidal Wetland & Coastal Ecosystems",
        "type": "ecosystem",
        "methodology_basis": "VM0033 v2.0; GHG + biodiversity co-benefits; VCS + CCB Standards",
        "accepted_jurisdictions": [
            "USA", "Australia", "Bangladesh", "Indonesia", "India",
            "Philippines", "Mozambique", "Kenya", "Senegal", "Mexico",
        ],
        "min_permanence_years": 30,
        "additionality_required": True,
        "co_benefits": [
            "carbon_sequestration", "coastal_protection", "fisheries_habitat",
            "water_purification", "community_livelihoods",
        ],
    },
    "Plan_Vivo": {
        "name": "Plan Vivo Standard — Community Land Management",
        "type": "habitat",
        "methodology_basis": "Plan Vivo 2013 Standard; community land-use plans; agroforestry/REDD+",
        "accepted_jurisdictions": [
            "Malawi", "Uganda", "Tanzania", "Ethiopia", "India",
            "Mexico", "Guatemala", "Nicaragua", "Syria", "Pakistan",
        ],
        "min_permanence_years": 20,
        "additionality_required": True,
        "co_benefits": [
            "community_wellbeing", "food_security", "biodiversity_habitat",
            "soil_formation", "water_purification",
        ],
    },
    "BNG_DEFRA_Metric_4": {
        "name": "UK Biodiversity Net Gain — DEFRA Metric 4.0",
        "type": "habitat",
        "methodology_basis": "Environment Act 2021 s.98; DEFRA Biodiversity Metric 4.0 (Feb 2023)",
        "accepted_jurisdictions": ["England"],
        "min_permanence_years": 30,
        "additionality_required": True,
        "co_benefits": [
            "habitat_connectivity", "species_recovery", "green_infrastructure",
            "flood_regulation", "recreation",
        ],
    },
    "TNFD_v1": {
        "name": "TNFD v1.0 — Taskforce on Nature-related Financial Disclosures",
        "type": "ecosystem",
        "methodology_basis": "TNFD Final Recommendations Sep 2023; LEAP process; 14 core metrics",
        "accepted_jurisdictions": ["Global"],
        "min_permanence_years": 10,
        "additionality_required": False,
        "co_benefits": [
            "investor_transparency", "risk_management", "regulatory_alignment",
            "biodiversity_habitat", "climate_regulation",
        ],
    },
    "Gold_Standard_Nature": {
        "name": "Gold Standard for the Global Goals — Nature Framework",
        "type": "species",
        "methodology_basis": "Gold Standard Nature v1.0 2022; SDG alignment; IUCN species criteria",
        "accepted_jurisdictions": [
            "Kenya", "Rwanda", "Uganda", "Peru", "Colombia", "Brazil",
            "India", "Nepal", "Bhutan", "Cambodia", "Vietnam",
        ],
        "min_permanence_years": 25,
        "additionality_required": True,
        "co_benefits": [
            "species_recovery", "community_livelihoods", "carbon_sequestration",
            "pollination", "nutrient_cycling",
        ],
    },
    "ART_TREES": {
        "name": "Architecture for REDD+ Transactions — TREES v2.0",
        "type": "ecosystem",
        "methodology_basis": "ART TREES v2.0 2021; jurisdictional REDD+; Paris Agreement Art 6.2/6.4",
        "accepted_jurisdictions": [
            "Brazil", "Colombia", "Peru", "Ecuador", "Guyana",
            "Democratic Republic of Congo", "Gabon", "Cameroon",
            "Indonesia", "Papua New Guinea", "Malaysia",
        ],
        "min_permanence_years": 40,
        "additionality_required": True,
        "co_benefits": [
            "carbon_sequestration", "biodiversity_habitat", "indigenous_rights",
            "water_purification", "climate_regulation",
        ],
    },
}

HABITAT_DISTINCTIVENESS_TIERS: dict[str, dict[str, Any]] = {
    "high_distinctiveness": {
        "score_range": (0.7, 1.0),
        "description": (
            "Ancient semi-natural habitats with long ecological continuity, high species "
            "richness and irreplaceability (e.g. ancient woodland, lowland meadow, blanket bog)"
        ),
        "bng_multiplier": 3.5,
        "examples": ["ancient_woodland", "lowland_meadow", "blanket_bog", "chalk_grassland"],
    },
    "medium_distinctiveness": {
        "score_range": (0.4, 0.69),
        "description": (
            "Semi-improved or modified habitats retaining moderate ecological value "
            "(e.g. grassland, heathland, scrub, broadleaved woodland)"
        ),
        "bng_multiplier": 2.0,
        "examples": ["grassland", "heathland", "broadleaved_woodland", "scrub", "hedgerow"],
    },
    "low_distinctiveness": {
        "score_range": (0.2, 0.39),
        "description": (
            "Modified habitats with limited but recognisable ecological value "
            "(e.g. arable land, improved grassland, urban greenspace)"
        ),
        "bng_multiplier": 1.0,
        "examples": ["arable", "improved_grassland", "urban_greenspace", "amenity_grassland"],
    },
    "very_low_distinctiveness": {
        "score_range": (0.1, 0.19),
        "description": (
            "Heavily modified or degraded habitats with minimal ecological function "
            "(e.g. intensive arable, compacted/sealed surfaces)"
        ),
        "bng_multiplier": 0.5,
        "examples": ["intensive_arable", "hard_standing_permeable", "built_area_soft"],
    },
    "degraded": {
        "score_range": (0.01, 0.09),
        "description": (
            "Severely degraded habitats with negligible biodiversity value "
            "(e.g. contaminated land, bare soil, invasive species monoculture)"
        ),
        "bng_multiplier": 0.1,
        "examples": ["contaminated_land", "bare_soil", "invasive_monoculture"],
    },
    "post_industrial": {
        "score_range": (0.0, 0.0),
        "description": (
            "Sealed or built surfaces with no ecological value "
            "(e.g. concrete, tarmac, buildings). Zero habitat units before intervention."
        ),
        "bng_multiplier": 0.0,
        "examples": ["concrete", "tarmac", "buildings", "impermeable_surface"],
    },
}

ECOSYSTEM_SERVICE_VALUATION: dict[str, dict[str, Any]] = {
    "carbon_sequestration": {
        "unit": "tCO2e/ha/yr",
        "usd_per_unit_low": 15.0,
        "usd_per_unit_high": 85.0,
        "method": "Social Cost of Carbon (US-IWG 2021 $51/tCO2) / market REDD+ price",
    },
    "water_purification": {
        "unit": "m3 clean water/ha/yr",
        "usd_per_unit_low": 0.002,
        "usd_per_unit_high": 0.05,
        "method": "Replacement cost (water treatment avoided cost); SEEA-EA Table 5",
    },
    "flood_regulation": {
        "unit": "USD/ha/yr",
        "usd_per_unit_low": 120.0,
        "usd_per_unit_high": 4200.0,
        "method": "Avoided damage cost; JRC flood risk maps; TEEB D0 Table 3",
    },
    "pollination": {
        "unit": "USD/ha/yr",
        "usd_per_unit_low": 30.0,
        "usd_per_unit_high": 900.0,
        "method": "Crop value dependency; IPBES pollination assessment 2016",
    },
    "soil_formation": {
        "unit": "tonne soil/ha/yr",
        "usd_per_unit_low": 0.5,
        "usd_per_unit_high": 8.0,
        "method": "Replacement cost (soil amendment inputs avoided); SEEA Soil",
    },
    "nutrient_cycling": {
        "unit": "USD/ha/yr",
        "usd_per_unit_low": 90.0,
        "usd_per_unit_high": 600.0,
        "method": "Avoided fertiliser cost; TEEB 2010 nutrient cycling estimates",
    },
    "climate_regulation": {
        "unit": "USD/ha/yr",
        "usd_per_unit_low": 50.0,
        "usd_per_unit_high": 400.0,
        "method": "Albedo + evapotranspiration cooling effect; SEEA-EA climate account",
    },
    "biodiversity_habitat": {
        "unit": "habitat_unit/ha",
        "usd_per_unit_low": 500.0,
        "usd_per_unit_high": 8000.0,
        "method": "BNG market price / conservation value hedonic pricing; CVM studies",
    },
    "coastal_protection": {
        "unit": "USD/ha/yr",
        "usd_per_unit_low": 200.0,
        "usd_per_unit_high": 12000.0,
        "method": "Avoided storm damage; coastal engineering replacement cost; TEEB D2",
    },
    "recreation": {
        "unit": "USD/ha/yr",
        "usd_per_unit_low": 40.0,
        "usd_per_unit_high": 500.0,
        "method": "Travel cost method; willingness-to-pay; ONS natural capital accounts",
    },
    "food_provision": {
        "unit": "tonne food/ha/yr",
        "usd_per_unit_low": 200.0,
        "usd_per_unit_high": 2500.0,
        "method": "Market price of provisioned food commodities; FAO FAOSTAT",
    },
    "timber_provision": {
        "unit": "m3 timber/ha/yr",
        "usd_per_unit_low": 40.0,
        "usd_per_unit_high": 280.0,
        "method": "Market price of roundwood; FSC certified premium; FAO forestry data",
    },
}

GBF_TARGET_15_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "a": {
        "description": (
            "Regularly monitor, assess and transparently disclose biodiversity-related risks "
            "and dependencies across operations and value chains."
        ),
        "disclosure_elements": [
            "biodiversity_risk_identification",
            "dependency_mapping_operations",
            "dependency_mapping_supply_chain",
            "materiality_threshold_applied",
            "monitoring_frequency",
        ],
        "materiality_threshold": "Gross revenue > USD 50M or significant nature footprint",
    },
    "b": {
        "description": (
            "Provide information needed by consumers to promote sustainable consumption, "
            "including nature-related disclosures in product labelling and supply chains."
        ),
        "disclosure_elements": [
            "product_level_nature_impact",
            "supply_chain_nature_footprint",
            "consumer_disclosure_mechanism",
            "sustainable_sourcing_commitments",
        ],
        "materiality_threshold": "B2C companies with significant consumer-facing products",
    },
    "c": {
        "description": (
            "Report on nature-related impacts across the full value chain including "
            "Scope 3 equivalent nature impacts, aligned with TNFD recommendations."
        ),
        "disclosure_elements": [
            "scope1_nature_impact",
            "scope2_nature_impact",
            "scope3_nature_impact_upstream",
            "scope3_nature_impact_downstream",
            "tnfd_leap_completion",
        ],
        "materiality_threshold": "TNFD early adopter or CSRD in-scope entity",
    },
    "d": {
        "description": (
            "Integrate biodiversity considerations into strategic planning, with board-level "
            "oversight and executive remuneration linked to nature targets."
        ),
        "disclosure_elements": [
            "board_oversight_mechanism",
            "executive_remuneration_linkage",
            "nature_strategy_document",
            "nature_targets_set",
            "review_cycle",
        ],
        "materiality_threshold": "Listed companies and significant private sector operators",
    },
    "e": {
        "description": (
            "Implement measures to reduce biodiversity loss by 2030, including sector-specific "
            "targets aligned with SBTN and Science-Based Targets for Nature."
        ),
        "disclosure_elements": [
            "sbtn_step1_assess",
            "sbtn_step2_interpret_prioritise",
            "sbtn_step3_measure_set",
            "sbtn_step4_act",
            "sbtn_step5_track",
            "2030_biodiversity_targets",
        ],
        "materiality_threshold": "High-impact sector companies; GBF Article 15 in-scope entities",
    },
    "f": {
        "description": (
            "Engage with public disclosure frameworks (TNFD, GRI, CSRD ESRS E4) and "
            "provide annual biodiversity disclosures accessible to all stakeholders."
        ),
        "disclosure_elements": [
            "annual_biodiversity_report",
            "public_accessibility",
            "framework_alignment_tnfd",
            "framework_alignment_gri_304",
            "framework_alignment_csrd_esrs_e4",
            "third_party_assurance",
        ],
        "materiality_threshold": "All entities within scope of national transposition of GBF Target 15",
    },
}

NATURE_MARKET_PRICE_BENCHMARKS: dict[str, dict[str, Any]] = {
    "BNG_habitat_unit": {
        "price_usd_low": 1_200.0,
        "price_usd_high": 18_000.0,
        "liquidity_score": 0.65,
        "key_buyers": ["UK property developers", "infrastructure operators", "local authorities"],
        "trend": "rising — mandatory BNG from Nov 2023 driving demand",
    },
    "biodiversity_unit_verra": {
        "price_usd_low": 8.0,
        "price_usd_high": 55.0,
        "liquidity_score": 0.40,
        "key_buyers": ["corporates", "banks", "sovereign wealth funds", "impact investors"],
        "trend": "developing — VCS biodiversity module under consultation",
    },
    "REDD_plus_biodiversity": {
        "price_usd_low": 3.0,
        "price_usd_high": 25.0,
        "liquidity_score": 0.55,
        "key_buyers": ["airlines (CORSIA)", "oil & gas majors", "consumer brands"],
        "trend": "mixed — quality concerns suppressing prices; CCB premium +$5-10",
    },
    "blue_carbon_mangrove": {
        "price_usd_low": 10.0,
        "price_usd_high": 60.0,
        "liquidity_score": 0.35,
        "key_buyers": ["coastal infrastructure operators", "shipping companies", "banks"],
        "trend": "rising — mangrove scarcity + dual carbon/biodiversity credit value",
    },
    "seagrass_unit": {
        "price_usd_low": 15.0,
        "price_usd_high": 80.0,
        "liquidity_score": 0.15,
        "key_buyers": ["ports", "aquaculture operators", "marine renewables developers"],
        "trend": "nascent — UK Seagrass Ocean Rescue pilot; very limited supply",
    },
    "rewilding_unit": {
        "price_usd_low": 25.0,
        "price_usd_high": 120.0,
        "liquidity_score": 0.25,
        "key_buyers": ["food & beverage companies", "financial sector", "luxury brands"],
        "trend": "growing — corporate nature pledges + TNFD disclosure driving interest",
    },
    "species_recovery": {
        "price_usd_low": 200.0,
        "price_usd_high": 2_500.0,
        "liquidity_score": 0.10,
        "key_buyers": ["infrastructure developers", "mining companies", "conservation banks"],
        "trend": "illiquid — mostly mitigation hierarchy compliance; bespoke transactions",
    },
    "wetland_credit": {
        "price_usd_low": 5_000.0,
        "price_usd_high": 50_000.0,
        "liquidity_score": 0.45,
        "key_buyers": ["US Army Corps permittees", "transport infrastructure", "energy"],
        "trend": "stable — US 404/401 wetland mitigation banking well-established market",
    },
}

# ---------------------------------------------------------------------------
# Helper constants
# ---------------------------------------------------------------------------

_TNFD_PILLARS: dict[str, list[str]] = {
    "governance": [
        "board_oversight", "management_role", "incentive_linkage",
        "policy_commitment",
    ],
    "strategy": [
        "location_prioritisation", "scenario_analysis", "portfolio_integration",
        "transition_planning",
    ],
    "risk_management": [
        "identification_process", "assessment_methodology", "mitigation_hierarchy",
        "residual_risk_monitoring",
    ],
    "metrics_targets": [
        "dependency_metrics", "impact_metrics", "2030_targets",
        "sbtn_alignment", "gbf_alignment", "progress_tracking",
    ],
}

_ENCORE_ECOSYSTEM_MAPPING: dict[str, list[str]] = {
    "provisioning": ["food_provision", "timber_provision", "water_purification"],
    "regulating": [
        "carbon_sequestration", "flood_regulation", "pollination",
        "climate_regulation", "coastal_protection",
    ],
    "supporting": ["soil_formation", "nutrient_cycling", "biodiversity_habitat"],
    "cultural": ["recreation"],
}

_PERMANENCE_RISK_FACTORS: dict[str, float] = {
    "wildfire": 0.15,
    "pest_disease": 0.12,
    "drought": 0.10,
    "flooding": 0.08,
    "political_instability": 0.20,
    "land_tenure_insecurity": 0.18,
    "funding_dependency": 0.10,
    "governance_weakness": 0.14,
}

# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------


class BiodiversityCreditEngine:
    """
    Biodiversity Credits & Nature Markets Engine (E88).

    All methods accept a plain dict and return a structured result dict.
    Missing fields are handled gracefully via .get() with sensible defaults.
    """

    # ------------------------------------------------------------------
    # 1. BNG Metric 4.0
    # ------------------------------------------------------------------

    def assess_bng_metric(self, project_data: dict) -> dict:
        """
        DEFRA BNG Metric 4.0 — calculate pre/post habitat units, determine whether
        the 10% mandatory net gain threshold is met, and estimate saleable credits.

        Expected keys (all optional with defaults):
            habitat_type, pre_condition, post_condition, area_ha,
            distinctiveness_tier, strategic_significance, offsite_distance_km,
            legal_agreement_years, irreplaceability_flag
        """
        habitat_type = project_data.get("habitat_type", "grassland")
        pre_condition = project_data.get("pre_condition", "poor")  # poor/moderate/good/excellent
        post_condition = project_data.get("post_condition", "good")
        area_ha = float(project_data.get("area_ha", 10.0))
        distinctiveness_tier = project_data.get(
            "distinctiveness_tier", "medium_distinctiveness"
        )
        strategic_significance = float(project_data.get("strategic_significance", 1.15))
        offsite_distance_km = float(project_data.get("offsite_distance_km", 0.0))
        legal_agreement_years = int(project_data.get("legal_agreement_years", 30))
        irreplaceability_flag = bool(project_data.get("irreplaceability_flag", False))

        # Distinctiveness score (midpoint of tier range)
        tier_info = HABITAT_DISTINCTIVENESS_TIERS.get(
            distinctiveness_tier, HABITAT_DISTINCTIVENESS_TIERS["medium_distinctiveness"]
        )
        low_s, high_s = tier_info["score_range"]
        distinctiveness_score = (low_s + high_s) / 2.0 if high_s > 0 else 0.0

        # Condition multipliers
        condition_map = {"poor": 0.5, "moderate": 0.7, "good": 1.0, "excellent": 1.3}
        pre_cond_mult = condition_map.get(pre_condition, 0.7)
        post_cond_mult = condition_map.get(post_condition, 1.0)

        # Temporal discounting (30 yr baseline; shorter = penalised)
        temporal_factor = min(1.0, legal_agreement_years / 30.0)

        # Proximity multiplier for offsite credits (distance penalty)
        if offsite_distance_km == 0.0:
            proximity_mult = 1.0  # onsite
        elif offsite_distance_km <= 5.0:
            proximity_mult = 0.95
        elif offsite_distance_km <= 20.0:
            proximity_mult = 0.85
        else:
            proximity_mult = 0.75

        # Irreplaceability penalty
        irreplaceability_mult = 1.25 if irreplaceability_flag else 1.0

        # Habitat unit calculations
        pre_units = (
            area_ha
            * distinctiveness_score
            * pre_cond_mult
            * strategic_significance
        )
        post_units = (
            area_ha
            * distinctiveness_score
            * post_cond_mult
            * strategic_significance
            * temporal_factor
            * proximity_mult
            * irreplaceability_mult
        )

        net_gain_units = post_units - pre_units
        net_gain_pct = (net_gain_units / pre_units * 100.0) if pre_units > 0 else 100.0
        compliant_10pct = net_gain_pct >= 10.0

        # Credit generation (units available for sale above 10% threshold)
        mandatory_threshold_units = pre_units * 1.10
        saleable_credits = max(0.0, post_units - mandatory_threshold_units)

        # Pricing estimate
        price_bench = NATURE_MARKET_PRICE_BENCHMARKS["BNG_habitat_unit"]
        mid_price = (price_bench["price_usd_low"] + price_bench["price_usd_high"]) / 2.0
        credit_value_usd = saleable_credits * mid_price

        return {
            "habitat_type": habitat_type,
            "distinctiveness_tier": distinctiveness_tier,
            "distinctiveness_score": round(distinctiveness_score, 3),
            "bng_multiplier": tier_info["bng_multiplier"],
            "area_ha": area_ha,
            "pre_condition": pre_condition,
            "post_condition": post_condition,
            "pre_habitat_units": round(pre_units, 3),
            "post_habitat_units": round(post_units, 3),
            "net_gain_units": round(net_gain_units, 3),
            "net_gain_pct": round(net_gain_pct, 2),
            "compliant_10pct_bng": compliant_10pct,
            "mandatory_threshold_units": round(mandatory_threshold_units, 3),
            "saleable_credits": round(saleable_credits, 3),
            "credit_value_usd_estimate": round(credit_value_usd, 2),
            "temporal_factor": round(temporal_factor, 3),
            "proximity_multiplier": proximity_mult,
            "legal_agreement_years": legal_agreement_years,
            "standard": "DEFRA BNG Metric 4.0 (Feb 2023) / Environment Act 2021 s.98",
            "flags": (
                ["IRREPLACEABLE_HABITAT_UPLIFT"] if irreplaceability_flag else []
            ) + (
                ["NON_COMPLIANT_BNG_10PCT"] if not compliant_10pct else []
            ),
        }

    # ------------------------------------------------------------------
    # 2. TNFD Disclosure (LEAP process)
    # ------------------------------------------------------------------

    def assess_tnfd_disclosure(self, entity_data: dict) -> dict:
        """
        TNFD v1.0 LEAP process assessment.
        Scores 14 core metrics across 4 pillars: Governance, Strategy,
        Risk Management, Metrics & Targets.

        Expected keys: entity_id, sector, country, pillar_scores dict,
                        has_location_data, has_scenario_analysis,
                        sbtn_aligned, gbf_aligned, leap_stage_reached
        """
        entity_id = entity_data.get("entity_id", "ENTITY_001")
        sector = entity_data.get("sector", "unknown")
        country = entity_data.get("country", "unknown")
        pillar_scores: dict = entity_data.get("pillar_scores", {})
        has_location_data = bool(entity_data.get("has_location_data", False))
        has_scenario_analysis = bool(entity_data.get("has_scenario_analysis", False))
        sbtn_aligned = bool(entity_data.get("sbtn_aligned", False))
        gbf_aligned = bool(entity_data.get("gbf_aligned", False))
        leap_stage = entity_data.get("leap_stage_reached", "L")  # L/E/A/P

        leap_stages = {"L": 1, "E": 2, "A": 3, "P": 4}
        leap_score = leap_stages.get(leap_stage.upper(), 1) / 4.0

        # Score each of the 14 metrics across 4 pillars
        pillar_results: dict[str, dict] = {}
        all_metric_scores: list[float] = []
        gaps: list[str] = []

        for pillar, metrics in _TNFD_PILLARS.items():
            p_score = float(pillar_scores.get(pillar, 50.0))  # 0-100 input
            metric_detail = []
            for m in metrics:
                # Apply modifiers
                mod = 1.0
                if m == "location_prioritisation" and not has_location_data:
                    mod = 0.4
                    gaps.append(f"{pillar}.{m}: location data missing")
                if m == "scenario_analysis" and not has_scenario_analysis:
                    mod = 0.3
                    gaps.append(f"{pillar}.{m}: scenario analysis not conducted")
                if m == "sbtn_alignment" and not sbtn_aligned:
                    mod = 0.5
                    gaps.append(f"{pillar}.{m}: SBTN targets not set")
                if m == "gbf_alignment" and not gbf_aligned:
                    mod = 0.5
                    gaps.append(f"{pillar}.{m}: GBF Target 15 not addressed")

                metric_score = min(100.0, p_score * mod)
                metric_detail.append({"metric": m, "score": round(metric_score, 1)})
                all_metric_scores.append(metric_score)

            pillar_results[pillar] = {
                "pillar_score": round(p_score, 1),
                "metrics": metric_detail,
                "metrics_count": len(metrics),
            }

        raw_composite = sum(all_metric_scores) / len(all_metric_scores) if all_metric_scores else 0.0
        # Blend LEAP process completion into composite
        tnfd_composite = round(raw_composite * 0.8 + leap_score * 100 * 0.2, 2)

        # Tier assignment
        if tnfd_composite >= 75:
            disclosure_tier = "advanced"
        elif tnfd_composite >= 50:
            disclosure_tier = "progressing"
        elif tnfd_composite >= 25:
            disclosure_tier = "developing"
        else:
            disclosure_tier = "early_stage"

        return {
            "entity_id": entity_id,
            "sector": sector,
            "country": country,
            "leap_stage_reached": leap_stage,
            "leap_completion_pct": round(leap_score * 100, 1),
            "pillar_results": pillar_results,
            "metrics_scored": len(all_metric_scores),
            "tnfd_composite_score": tnfd_composite,
            "disclosure_tier": disclosure_tier,
            "gaps": gaps,
            "has_location_data": has_location_data,
            "has_scenario_analysis": has_scenario_analysis,
            "sbtn_aligned": sbtn_aligned,
            "gbf_aligned": gbf_aligned,
            "standard": "TNFD Final Recommendations v1.0 (Sep 2023)",
            "next_steps": [
                g.replace(":", " →") for g in gaps[:5]
            ],
        }

    # ------------------------------------------------------------------
    # 3. Ecosystem Service Valuation (TEEB / SEEA)
    # ------------------------------------------------------------------

    def value_ecosystem_services(self, project_data: dict) -> dict:
        """
        TEEB / SEEA-EA ecosystem service valuation.
        Values all 12 service categories, computes total economic value (TEV),
        identifies key dependencies, and maps to ENCORE categories.

        Expected keys: project_id, area_ha, ecosystem_type,
                        service_quantities dict (service → quantity per ha),
                        use_high_estimate bool
        """
        project_id = project_data.get("project_id", "PROJECT_001")
        area_ha = float(project_data.get("area_ha", 100.0))
        ecosystem_type = project_data.get("ecosystem_type", "grassland")
        service_quantities: dict = project_data.get("service_quantities", {})
        use_high = bool(project_data.get("use_high_estimate", False))

        services_valued: list[dict] = []
        tev_usd = 0.0

        for service, meta in ECOSYSTEM_SERVICE_VALUATION.items():
            qty_per_ha = float(service_quantities.get(service, 1.0))
            price = meta["usd_per_unit_high"] if use_high else meta["usd_per_unit_low"]
            value_ha = qty_per_ha * price
            total_value = value_ha * area_ha
            tev_usd += total_value

            services_valued.append({
                "service": service,
                "quantity_per_ha": qty_per_ha,
                "unit": meta["unit"],
                "price_usd_per_unit": price,
                "value_per_ha_usd": round(value_ha, 2),
                "total_value_usd": round(total_value, 2),
                "valuation_method": meta["method"],
            })

        # Sort by total value desc
        services_valued.sort(key=lambda x: x["total_value_usd"], reverse=True)

        # ENCORE category mapping
        encore_breakdown: dict[str, float] = {cat: 0.0 for cat in _ENCORE_ECOSYSTEM_MAPPING}
        for sv in services_valued:
            for cat, svcs in _ENCORE_ECOSYSTEM_MAPPING.items():
                if sv["service"] in svcs:
                    encore_breakdown[cat] += sv["total_value_usd"]

        # Key dependencies (top 3 services)
        top_services = [sv["service"] for sv in services_valued[:3]]

        tev_m = tev_usd / 1_000_000.0

        return {
            "project_id": project_id,
            "ecosystem_type": ecosystem_type,
            "area_ha": area_ha,
            "estimate_type": "high" if use_high else "low",
            "services_valued": services_valued,
            "encore_category_breakdown_usd": {
                k: round(v, 2) for k, v in encore_breakdown.items()
            },
            "total_ecosystem_value_usd": round(tev_usd, 2),
            "total_ecosystem_value_m_usd": round(tev_m, 4),
            "value_per_ha_usd": round(tev_usd / area_ha if area_ha > 0 else 0, 2),
            "key_dependencies": top_services,
            "dominant_encore_category": max(encore_breakdown, key=encore_breakdown.get),
            "methodology": "TEEB (2010) / SEEA-EA (UN 2021) / IPBES (2019)",
        }

    # ------------------------------------------------------------------
    # 4. GBF Target 15 Assessment
    # ------------------------------------------------------------------

    def assess_gbf_target15(self, entity_data: dict) -> dict:
        """
        Kunming-Montreal GBF Target 15 disclosure assessment.
        Evaluates all 6 sub-targets (a-f), produces completeness score,
        identifies gaps, and provides peer comparison.

        Expected keys: entity_id, sector, revenue_usd_m,
                        sub_target_status dict (a-f → completion 0-100),
                        has_tnfd_disclosure, has_csrd_esrs_e4,
                        has_gri_304, peer_sector_avg_score
        """
        entity_id = entity_data.get("entity_id", "ENTITY_001")
        sector = entity_data.get("sector", "unknown")
        revenue_usd_m = float(entity_data.get("revenue_usd_m", 500.0))
        sub_target_status: dict = entity_data.get("sub_target_status", {})
        has_tnfd = bool(entity_data.get("has_tnfd_disclosure", False))
        has_csrd = bool(entity_data.get("has_csrd_esrs_e4", False))
        has_gri = bool(entity_data.get("has_gri_304", False))
        peer_avg = float(entity_data.get("peer_sector_avg_score", 42.0))

        subtarget_results: dict[str, dict] = {}
        gaps: list[str] = []
        total_score = 0.0

        for st_key, req in GBF_TARGET_15_REQUIREMENTS.items():
            completion = float(sub_target_status.get(st_key, 0.0))
            # Cap at 100
            completion = min(100.0, completion)

            # Apply framework boosts
            boost = 0.0
            if st_key == "c" and has_tnfd:
                boost += 10.0
            if st_key == "f" and has_csrd:
                boost += 8.0
            if st_key == "f" and has_gri:
                boost += 5.0

            adjusted = min(100.0, completion + boost)

            # Check materiality
            material = revenue_usd_m >= 50.0  # simplified threshold
            if material and adjusted < 50.0:
                gaps.append(
                    f"Sub-target {st_key.upper()}: {req['description'][:70]}... — score {adjusted:.0f}%"
                )

            subtarget_results[st_key] = {
                "description": req["description"],
                "disclosure_elements": req["disclosure_elements"],
                "materiality_threshold": req["materiality_threshold"],
                "completion_pct": round(completion, 1),
                "adjusted_score": round(adjusted, 1),
                "in_scope": material,
            }
            total_score += adjusted

        n = len(GBF_TARGET_15_REQUIREMENTS)
        overall_score = round(total_score / n, 2)

        # Peer comparison
        vs_peer = round(overall_score - peer_avg, 2)
        peer_position = (
            "above_peer" if vs_peer > 5 else
            "at_peer" if abs(vs_peer) <= 5 else
            "below_peer"
        )

        # Framework alignment
        framework_alignment = []
        if has_tnfd:
            framework_alignment.append("TNFD v1.0")
        if has_csrd:
            framework_alignment.append("CSRD ESRS E4")
        if has_gri:
            framework_alignment.append("GRI 304")

        return {
            "entity_id": entity_id,
            "sector": sector,
            "revenue_usd_m": revenue_usd_m,
            "subtarget_results": subtarget_results,
            "overall_gbf_t15_score": overall_score,
            "peer_sector_avg": peer_avg,
            "vs_peer": vs_peer,
            "peer_position": peer_position,
            "gaps": gaps,
            "framework_alignment": framework_alignment,
            "regulatory_basis": "Kunming-Montreal GBF Article 15 (Dec 2022 COP15)",
        }

    # ------------------------------------------------------------------
    # 5. Credit Quality Assessment
    # ------------------------------------------------------------------

    def assess_credit_quality(self, credit_data: dict) -> dict:
        """
        Biodiversity credit quality assessment:
        - Additionality check
        - Permanence risk scoring (0-100; lower = less risky)
        - Reversal buffer adequacy
        - CORSIA eligibility
        - Price benchmarking vs market

        Expected keys: credit_id, standard, credit_type, project_country,
                        permanence_years, has_additionality_demonstration,
                        reversal_buffer_pct, risk_factors list,
                        asking_price_usd, co_benefits list
        """
        credit_id = credit_data.get("credit_id", "CREDIT_001")
        standard = credit_data.get("standard", "Verra_VM0033")
        credit_type = credit_data.get("credit_type", "REDD_plus_biodiversity")
        project_country = credit_data.get("project_country", "Brazil")
        permanence_years = int(credit_data.get("permanence_years", 30))
        has_additionality = bool(credit_data.get("has_additionality_demonstration", True))
        reversal_buffer_pct = float(credit_data.get("reversal_buffer_pct", 10.0))
        risk_factors: list = credit_data.get("risk_factors", [])
        asking_price = float(credit_data.get("asking_price_usd", 20.0))
        co_benefits: list = credit_data.get("co_benefits", [])

        # --- Additionality ---
        std_info = BIODIVERSITY_CREDIT_STANDARDS.get(standard, {})
        additionality_required = std_info.get("additionality_required", True)
        additionality_pass = (not additionality_required) or has_additionality
        additionality_score = 100.0 if additionality_pass else 0.0

        # --- Permanence risk ---
        min_perm = std_info.get("min_permanence_years", 30)
        perm_years_score = min(100.0, (permanence_years / max(min_perm, 1)) * 100.0)

        risk_penalty = sum(
            _PERMANENCE_RISK_FACTORS.get(rf, 0.08)
            for rf in risk_factors
        ) * 100.0
        permanence_risk_score = max(0.0, 100.0 - risk_penalty)

        # --- Reversal buffer ---
        # ICROA recommends ≥10-20% depending on risk; industry standard ~15%
        buffer_adequate = reversal_buffer_pct >= 10.0
        buffer_score = min(100.0, (reversal_buffer_pct / 20.0) * 100.0)

        # --- CORSIA eligibility ---
        corsia_eligible_standards = {"Verra_VM0033", "ART_TREES", "Gold_Standard_Nature"}
        corsia_eligible = standard in corsia_eligible_standards

        # --- Price benchmarking ---
        bench = NATURE_MARKET_PRICE_BENCHMARKS.get(credit_type, {})
        price_low = bench.get("price_usd_low", 5.0)
        price_high = bench.get("price_usd_high", 50.0)
        price_mid = (price_low + price_high) / 2.0
        price_vs_market = round(asking_price - price_mid, 2)

        # Premium for co-benefits
        co_benefit_premium_pct = min(40.0, len(co_benefits) * 5.0)

        # --- Overall quality score ---
        quality_score = (
            additionality_score * 0.30
            + permanence_risk_score * 0.25
            + perm_years_score * 0.15
            + buffer_score * 0.15
            + (100.0 if corsia_eligible else 50.0) * 0.15
        )
        quality_score = round(quality_score, 2)

        if quality_score >= 80:
            quality_tier = "A"
        elif quality_score >= 65:
            quality_tier = "B"
        elif quality_score >= 45:
            quality_tier = "C"
        else:
            quality_tier = "D"

        return {
            "credit_id": credit_id,
            "standard": standard,
            "credit_type": credit_type,
            "project_country": project_country,
            "additionality": {
                "required": additionality_required,
                "demonstrated": has_additionality,
                "pass": additionality_pass,
                "score": additionality_score,
            },
            "permanence": {
                "years": permanence_years,
                "min_required_years": min_perm,
                "permanence_years_score": round(perm_years_score, 1),
                "risk_factors": risk_factors,
                "permanence_risk_score": round(permanence_risk_score, 1),
            },
            "reversal_buffer": {
                "buffer_pct": reversal_buffer_pct,
                "adequate": buffer_adequate,
                "buffer_score": round(buffer_score, 1),
            },
            "corsia_eligible": corsia_eligible,
            "price_benchmarking": {
                "asking_price_usd": asking_price,
                "market_low_usd": price_low,
                "market_high_usd": price_high,
                "market_mid_usd": round(price_mid, 2),
                "price_vs_market_mid": price_vs_market,
                "assessment": (
                    "above_market" if price_vs_market > 5
                    else "at_market" if abs(price_vs_market) <= 5
                    else "below_market"
                ),
                "co_benefit_premium_pct": co_benefit_premium_pct,
                "liquidity_score": bench.get("liquidity_score", 0.3),
                "market_trend": bench.get("trend", "unknown"),
            },
            "co_benefits": co_benefits,
            "quality_score": quality_score,
            "quality_tier": quality_tier,
        }

    # ------------------------------------------------------------------
    # 6. Full Assessment (orchestrator)
    # ------------------------------------------------------------------

    def run_full_assessment(self, entity_data: dict) -> dict:
        """
        Orchestrates all sub-assessments and produces a consolidated
        biodiversity credit & nature markets report.

        Expected keys: All keys from sub-methods, plus:
            project_data dict, credit_data dict
        """
        project_data = entity_data.get("project_data", entity_data)
        credit_data = entity_data.get("credit_data", entity_data)

        bng = self.assess_bng_metric(project_data)
        tnfd = self.assess_tnfd_disclosure(entity_data)
        esv = self.value_ecosystem_services(project_data)
        gbf = self.assess_gbf_target15(entity_data)
        cq = self.assess_credit_quality(credit_data)

        # Composite biodiversity credit score (0-100)
        bng_score = min(100.0, bng["net_gain_pct"])
        tnfd_score = tnfd["tnfd_composite_score"]
        gbf_score = gbf["overall_gbf_t15_score"]
        cq_score = cq["quality_score"]

        biodiversity_credit_score = round(
            bng_score * 0.20
            + tnfd_score * 0.25
            + gbf_score * 0.25
            + cq_score * 0.30,
            2,
        )

        # Credit quality tier from sub-assessment
        credit_quality_tier = cq["quality_tier"]

        # TEV
        total_ecosystem_value_m = esv["total_ecosystem_value_m_usd"]

        # BNG
        biodiversity_net_gain_pct = bng["net_gain_pct"]

        # TNFD composite
        tnfd_composite = tnfd["tnfd_composite_score"]

        # GBF T15 disclosure
        gbf_t15_disclosure_score = gbf["overall_gbf_t15_score"]

        # Aggregate gaps
        all_gaps = tnfd["gaps"] + gbf["gaps"]
        priority_gaps = all_gaps[:5]

        return {
            "entity_id": entity_data.get("entity_id", "ENTITY_001"),
            "biodiversity_credit_score": biodiversity_credit_score,
            "credit_quality_tier": credit_quality_tier,
            "total_ecosystem_value_m_usd": total_ecosystem_value_m,
            "biodiversity_net_gain_pct": biodiversity_net_gain_pct,
            "tnfd_composite_score": tnfd_composite,
            "gbf_t15_disclosure_score": gbf_t15_disclosure_score,
            "sub_assessments": {
                "bng_metric": bng,
                "tnfd_disclosure": tnfd,
                "ecosystem_service_valuation": esv,
                "gbf_target15": gbf,
                "credit_quality": cq,
            },
            "priority_gaps": priority_gaps,
            "methodology": (
                "DEFRA BNG Metric 4.0 | TNFD v1.0 | TEEB/SEEA-EA | "
                "GBF Target 15 | ICROA Quality Standards"
            ),
        }
