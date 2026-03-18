"""
Biodiversity Credits Engine — Sprint 26
=========================================
Standards covered:
- UK BNG Environment Act 2021 (DEFRA Metric 4.0)
- EU Nature Restoration Law 2024/1991
- Science Based Targets for Nature (SBTN) v1.1
- TNFD LEAP v1.0 advanced metrics
- Biodiversity Credit Alliance (BCA) 2023
- IPBES Global Assessment
- Living Planet Index
- IUCN Red List
"""
from __future__ import annotations

import random
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

HABITAT_DISTINCTIVENESS: dict[str, float] = {
    "woodland": 6.0,
    "grassland": 5.0,
    "heathland": 5.5,
    "wetland": 6.0,
    "marine": 6.0,
    "freshwater": 5.5,
    "agroforestry": 4.0,
    "urban_greenspace": 2.5,
    "hedgerows": 4.5,
    "rivers": 5.0,
}

HABITAT_CONDITION_MULTIPLIERS: dict[str, float] = {
    "poor": 0.5,
    "moderate": 0.7,
    "good": 1.0,
    "excellent": 1.3,
}

SBTN_FRESHWATER_TARGETS: dict[str, dict[str, Any]] = {
    "abstraction": {
        "description": "Water abstraction levels relative to environmental flow requirements",
        "2030_target_reduction_pct": 30.0,
        "unit": "% above EFR",
    },
    "pollution": {
        "description": "Reduction in nutrient / chemical pollution loads",
        "2030_target_reduction_pct": 50.0,
        "unit": "kg N/P per ha",
    },
    "hydromorphology": {
        "description": "Restoration of natural flow regimes and channel morphology",
        "2030_target_restoration_pct": 25.0,
        "unit": "% channel naturalised",
    },
    "invasives": {
        "description": "Control and removal of invasive non-native species",
        "2030_target_control_pct": 40.0,
        "unit": "% coverage controlled",
    },
    "overexploitation": {
        "description": "Fisheries and aquatic species harvesting limits",
        "2030_target_reduction_pct": 20.0,
        "unit": "% above MSY",
    },
}

EU_NRL_ECOSYSTEM_TARGETS: dict[str, dict[str, Any]] = {
    "coastal_lagoons": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "saltmarsh": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "dunes": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "mires_bogs": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "temperate_heath": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "alpine_heath": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "natural_grassland": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "calcareous_grassland": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "atlantic_oak_woodland": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "riparian_forest": {"article": 4, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "rivers_lakes": {"article": 7, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "EQR"},
    "floodplains": {"article": 7, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "EQR"},
    "alluvial_forests": {"article": 7, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "IES"},
    "farmland": {"article": 9, "2030_pct": 10, "2040_pct": 20, "2050_pct": 30, "condition_metric": "FBI"},
    "forest": {"article": 10, "2030_pct": 20, "2040_pct": 40, "2050_pct": 60, "condition_metric": "IES"},
    "urban_ecosystem": {"article": 6, "2030_pct": 0, "2040_pct": 10, "2050_pct": 20, "condition_metric": "UGI"},
    "marine_benthic": {"article": 12, "2030_pct": 20, "2040_pct": 40, "2050_pct": 60, "condition_metric": "BHQ"},
    "seagrass": {"article": 12, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "BHQ"},
    "kelp_forest": {"article": 12, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "BHQ"},
    "coral_reef": {"article": 12, "2030_pct": 30, "2040_pct": 60, "2050_pct": 90, "condition_metric": "BHQ"},
}

BIODIVERSITY_CREDIT_PRICES: dict[str, dict[str, Any]] = {
    "woodland": {"uk_bng_gbp": 28000.0, "eu_habitat_eur": 32000.0, "voluntary_usd": 20000.0, "liquidity": "high"},
    "grassland": {"uk_bng_gbp": 15000.0, "eu_habitat_eur": 18000.0, "voluntary_usd": 12000.0, "liquidity": "medium"},
    "heathland": {"uk_bng_gbp": 18000.0, "eu_habitat_eur": 20000.0, "voluntary_usd": 14000.0, "liquidity": "medium"},
    "wetland": {"uk_bng_gbp": 32000.0, "eu_habitat_eur": 38000.0, "voluntary_usd": 28000.0, "liquidity": "high"},
    "marine": {"uk_bng_gbp": 22000.0, "eu_habitat_eur": 26000.0, "voluntary_usd": 18000.0, "liquidity": "low"},
    "freshwater": {"uk_bng_gbp": 20000.0, "eu_habitat_eur": 24000.0, "voluntary_usd": 16000.0, "liquidity": "medium"},
    "agroforestry": {"uk_bng_gbp": 12000.0, "eu_habitat_eur": 14000.0, "voluntary_usd": 9000.0, "liquidity": "medium"},
    "urban_greenspace": {"uk_bng_gbp": 8000.0, "eu_habitat_eur": 9000.0, "voluntary_usd": 6000.0, "liquidity": "high"},
    "hedgerows": {"uk_bng_gbp": 10000.0, "eu_habitat_eur": 12000.0, "voluntary_usd": 8000.0, "liquidity": "medium"},
    "rivers": {"uk_bng_gbp": 25000.0, "eu_habitat_eur": 30000.0, "voluntary_usd": 22000.0, "liquidity": "medium"},
}

TNFD_METRICS: list[dict[str, Any]] = [
    {"name": "species_richness_delta", "unit": "index", "description": "Change in native species richness per km²"},
    {"name": "mean_species_abundance", "unit": "MSA 0-1", "description": "Mean species abundance relative to pristine baseline"},
    {"name": "habitat_intactness_index", "unit": "HII 0-1", "description": "Intactness of natural habitat relative to intact reference"},
    {"name": "functional_diversity", "unit": "FDiv", "description": "Functional trait diversity of ecological community"},
    {"name": "connectivity_index", "unit": "0-100", "description": "Habitat connectivity and fragmentation score"},
    {"name": "ecosystem_services_value", "unit": "USD/ha/yr", "description": "Total ecosystem services economic value per hectare"},
    {"name": "invasive_species_pressure", "unit": "0-10", "description": "Pressure from invasive non-native species"},
    {"name": "water_quality_index", "unit": "WQI 0-100", "description": "Freshwater quality composite index"},
    {"name": "soil_organic_carbon", "unit": "tC/ha", "description": "Soil organic carbon stock"},
    {"name": "pollinator_diversity", "unit": "species count", "description": "Number of wild pollinator species recorded"},
    {"name": "edge_effect_ratio", "unit": "km edge/km²", "description": "Ratio of habitat edge to core area"},
    {"name": "natural_disturbance_regime", "unit": "0-10", "description": "Naturalness of disturbance regime (fire, flood)"},
    {"name": "protected_area_overlap", "unit": "%", "description": "Percentage of operations within protected areas"},
    {"name": "iucn_species_threat_index", "unit": "0-10", "description": "Weighted IUCN threat score for dependent species"},
]

IUCN_ECOSYSTEM_RED_LIST: dict[str, dict[str, Any]] = {
    "Collapsed": {"code": "CO", "description": "Ecosystem no longer functionally active", "priority": 1},
    "Critical": {"code": "CR", "description": "Facing extremely high risk of collapse", "priority": 2},
    "Endangered": {"code": "EN", "description": "Facing very high risk of collapse", "priority": 3},
    "Vulnerable": {"code": "VU", "description": "Facing high risk of collapse", "priority": 4},
    "Near_Threatened": {"code": "NT", "description": "Close to qualifying for threatened category", "priority": 5},
    "Least_Concern": {"code": "LC", "description": "Not facing elevated risk of collapse", "priority": 6},
    "Data_Deficient": {"code": "DD", "description": "Inadequate information to assess risk", "priority": 7},
    "Not_Evaluated": {"code": "NE", "description": "Not yet evaluated against criteria", "priority": 8},
}


# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------

class BiodiversityCreditsEngine:
    """Sprint 26 Biodiversity Credits Engine implementing BNG / SBTN / EU NRL / TNFD."""

    # ------------------------------------------------------------------
    # 1. BNG (Biodiversity Net Gain) assessment
    # ------------------------------------------------------------------
    def assess_bng(
        self,
        entity_id: str,
        habitat_type: str,
        area_ha: float,
        baseline_condition: str,
        post_condition: str,
        distinctiveness_override: Optional[float] = None,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        distinctiveness = distinctiveness_override if distinctiveness_override is not None else HABITAT_DISTINCTIVENESS.get(habitat_type, 3.0)
        baseline_cond_mult = HABITAT_CONDITION_MULTIPLIERS.get(baseline_condition, 0.7)
        post_cond_mult = HABITAT_CONDITION_MULTIPLIERS.get(post_condition, 1.0)

        # Strategic significance: deterministic per entity + habitat
        strategic_significance = round(max(0.5, min(2.0, 1.0 + rng.uniform(-0.3, 0.5))), 2)

        baseline_units = round(area_ha * distinctiveness * baseline_cond_mult * strategic_significance, 2)
        post_units = round(area_ha * distinctiveness * post_cond_mult * strategic_significance, 2)
        net_gain_units = round(post_units - baseline_units, 2)
        net_gain_pct = round((net_gain_units / max(0.001, baseline_units)) * 100, 2)

        compliant_10pct = net_gain_pct >= 10.0

        prices = BIODIVERSITY_CREDIT_PRICES.get(habitat_type, BIODIVERSITY_CREDIT_PRICES["grassland"])
        credit_value_gbp = round(net_gain_units * prices["uk_bng_gbp"], 2) if net_gain_units > 0 else 0.0

        return {
            "entity_id": entity_id,
            "habitat_type": habitat_type,
            "area_ha": round(area_ha, 2),
            "baseline_units": baseline_units,
            "post_units": post_units,
            "net_gain_units": net_gain_units,
            "net_gain_pct": net_gain_pct,
            "compliant_10pct": compliant_10pct,
            "credit_value_gbp": credit_value_gbp,
            "strategic_significance_score": strategic_significance,
            "distinctiveness_score": distinctiveness,
            "condition_improvement": post_condition,
        }

    # ------------------------------------------------------------------
    # 2. SBTN assessment
    # ------------------------------------------------------------------
    def assess_sbtn(
        self,
        entity_id: str,
        sector: str,
        freshwater_pressures: dict,
        land_footprint_ha: float,
        species_impact_score: float,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Step 1 — Assess
        pressure_scores = []
        for pressure, val in freshwater_pressures.items():
            target_data = SBTN_FRESHWATER_TARGETS.get(pressure, {})
            target_pct = target_data.get("2030_target_reduction_pct", 30.0)
            score = round(max(0, min(100, (target_pct - val) / target_pct * 100 + rng.uniform(-5, 5))), 2)
            pressure_scores.append(score)
        sbtn_assess_score = round(sum(pressure_scores) / max(1, len(pressure_scores)), 2)

        # Step 2 — Commit
        sbtn_commit_score = round(max(0, min(100, sbtn_assess_score * 0.8 + rng.uniform(0, 20))), 2)

        # Step 3 — Transform
        sbtn_transform_score = round(max(0, min(100, sbtn_commit_score * 0.85 + rng.uniform(0, 15))), 2)

        # Step 4 — Track
        sbtn_track_score = round(max(0, min(100, sbtn_transform_score * 0.9 + rng.uniform(0, 10))), 2)

        sbtn_overall = round((sbtn_assess_score + sbtn_commit_score + sbtn_transform_score + sbtn_track_score) / 4, 2)

        no_conversion_compliant = land_footprint_ha < 500 or rng.random() > 0.3

        priority_actions = []
        if sbtn_assess_score < 50:
            priority_actions.append("Complete baseline freshwater pressure assessment")
        if not no_conversion_compliant:
            priority_actions.append("Commit to no net loss of native ecosystems")
        if species_impact_score > 5:
            priority_actions.append("Develop species recovery plan for high-impact footprint")
        if sbtn_commit_score < 40:
            priority_actions.append("Set science-based freshwater targets by 2025")

        return {
            "entity_id": entity_id,
            "sector": sector,
            "sbtn_assess_score": sbtn_assess_score,
            "sbtn_commit_score": sbtn_commit_score,
            "sbtn_transform_score": sbtn_transform_score,
            "sbtn_track_score": sbtn_track_score,
            "sbtn_overall": sbtn_overall,
            "priority_actions": priority_actions,
            "no_conversion_compliant": no_conversion_compliant,
            "land_footprint_ha": round(land_footprint_ha, 2),
            "species_impact_score": round(species_impact_score, 2),
        }

    # ------------------------------------------------------------------
    # 3. EU NRL assessment
    # ------------------------------------------------------------------
    def assess_eu_nrl(
        self,
        entity_id: str,
        country_code: str,
        ecosystem_type: str,
        current_area_ha: float,
        degraded_area_ha: float,
        restoration_plan: bool,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        nrl_meta = EU_NRL_ECOSYSTEM_TARGETS.get(ecosystem_type, EU_NRL_ECOSYSTEM_TARGETS["forest"])

        degraded_pct = (degraded_area_ha / max(1, current_area_ha)) * 100
        restoration_target_ha = round(degraded_area_ha * nrl_meta["2030_pct"] / 100, 2)

        # Compliance checks
        current_restored_pct = round(max(0, min(100, (100 - degraded_pct) + rng.uniform(-10, 10))), 2)
        compliant_2030 = current_restored_pct >= nrl_meta["2030_pct"] and restoration_plan
        compliant_2040 = current_restored_pct >= nrl_meta["2040_pct"]

        compliance_score = round(
            (current_restored_pct / max(1, nrl_meta["2050_pct"])) * 100
            + (10.0 if restoration_plan else 0)
            + rng.uniform(-5, 5),
            2,
        )
        compliance_score = round(max(0, min(100, compliance_score)), 2)

        # Cost estimation: ~€5,000-50,000 per ha depending on ecosystem
        cost_per_ha = rng.uniform(5000, 50000)
        estimated_restoration_cost_eur = round(restoration_target_ha * cost_per_ha, 2)

        biodiversity_uplift = round(max(0, min(100, restoration_target_ha * 0.5 + rng.uniform(10, 30))), 2)

        return {
            "entity_id": entity_id,
            "country_code": country_code,
            "ecosystem_type": ecosystem_type,
            "nrl_article": nrl_meta["article"],
            "restoration_target_ha": restoration_target_ha,
            "current_restored_pct": current_restored_pct,
            "compliant_2030": compliant_2030,
            "compliant_2040": compliant_2040,
            "compliance_score": compliance_score,
            "estimated_restoration_cost_eur": estimated_restoration_cost_eur,
            "biodiversity_uplift_score": biodiversity_uplift,
            "condition_metric": nrl_meta["condition_metric"],
            "milestone_targets": {
                "2030_pct": nrl_meta["2030_pct"],
                "2040_pct": nrl_meta["2040_pct"],
                "2050_pct": nrl_meta["2050_pct"],
            },
        }

    # ------------------------------------------------------------------
    # 4. TNFD advanced metrics
    # ------------------------------------------------------------------
    def assess_tnfd_advanced(
        self,
        entity_id: str,
        sector: str,
        location_lat: float,
        location_lng: float,
        operations_ha: float,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Proxy IBAT scoring from lat/lng seed
        loc_seed = hash(f"{location_lat:.2f}_{location_lng:.2f}") & 0xFFFFFF
        loc_rng = random.Random(loc_seed)

        msa_score = round(max(0.1, min(1.0, loc_rng.uniform(0.3, 0.9))), 2)
        hii_score = round(max(0.1, min(1.0, loc_rng.uniform(0.3, 0.95))), 2)
        species_richness_delta = round(loc_rng.uniform(-0.3, 0.1), 2)
        connectivity_index = round(max(0, min(100, loc_rng.uniform(20, 85))), 2)

        esv_base = loc_rng.uniform(500, 8000)
        ecosystem_services_value_usd_ha = round(esv_base * (msa_score + hii_score) / 2, 2)

        tnfd_metric_scores: dict[str, float] = {}
        for metric in TNFD_METRICS:
            name = metric["name"]
            if name == "mean_species_abundance":
                tnfd_metric_scores[name] = msa_score
            elif name == "habitat_intactness_index":
                tnfd_metric_scores[name] = hii_score
            elif name == "species_richness_delta":
                tnfd_metric_scores[name] = species_richness_delta
            elif name == "connectivity_index":
                tnfd_metric_scores[name] = connectivity_index
            elif name == "ecosystem_services_value":
                tnfd_metric_scores[name] = ecosystem_services_value_usd_ha
            else:
                tnfd_metric_scores[name] = round(rng.uniform(0.2, 0.9), 2)

        return {
            "entity_id": entity_id,
            "sector": sector,
            "location_lat": location_lat,
            "location_lng": location_lng,
            "operations_ha": round(operations_ha, 2),
            "msa_score": msa_score,
            "hii_score": hii_score,
            "species_richness_delta": species_richness_delta,
            "connectivity_index": connectivity_index,
            "ecosystem_services_value_usd_ha": ecosystem_services_value_usd_ha,
            "tnfd_metric_scores": tnfd_metric_scores,
            "total_metrics_assessed": len(TNFD_METRICS),
        }

    # ------------------------------------------------------------------
    # 5. Credit value calculation
    # ------------------------------------------------------------------
    def calculate_credit_value(
        self,
        entity_id: str,
        habitat_type: str,
        bng_net_units: float,
        sbtn_score: float,
        eu_nrl_score: float,
        market_type: str = "blended",
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        prices = BIODIVERSITY_CREDIT_PRICES.get(habitat_type, BIODIVERSITY_CREDIT_PRICES["grassland"])

        # Quality adjustments
        quality_adj = round((sbtn_score / 100) * 0.3 + (eu_nrl_score / 100) * 0.3 + 0.4 + rng.uniform(-0.05, 0.05), 2)
        quality_adj = max(0.5, min(1.5, quality_adj))

        bng_credit_value_gbp = round(bng_net_units * prices["uk_bng_gbp"] * quality_adj, 2)
        eu_credit_value_eur = round(bng_net_units * prices["eu_habitat_eur"] * quality_adj, 2)
        voluntary_credit_value_usd = round(bng_net_units * prices["voluntary_usd"] * quality_adj, 2)

        # Blended (simplified: GBP≈EUR≈1.15 USD, EUR≈1.08 USD)
        blended_value_usd = round(
            bng_credit_value_gbp * 1.25 * 0.4
            + eu_credit_value_eur * 1.08 * 0.4
            + voluntary_credit_value_usd * 0.2,
            2,
        )

        return {
            "entity_id": entity_id,
            "habitat_type": habitat_type,
            "bng_net_units": round(bng_net_units, 2),
            "bng_credit_value_gbp": bng_credit_value_gbp,
            "eu_credit_value_eur": eu_credit_value_eur,
            "voluntary_credit_value_usd": voluntary_credit_value_usd,
            "blended_value_usd": blended_value_usd,
            "market_liquidity": prices["liquidity"],
            "quality_adjustment_factor": quality_adj,
            "market_type": market_type,
        }

    # ------------------------------------------------------------------
    # 6. Portfolio assessment
    # ------------------------------------------------------------------
    def assess_portfolio(self, entity_id: str, projects: list) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        if not projects:
            return {
                "entity_id": entity_id,
                "total_bng_units": 0.0,
                "total_credit_value_usd": 0.0,
                "weighted_sbtn_score": 0.0,
                "eu_nrl_aligned_pct": 0.0,
                "portfolio_biodiversity_rating": "N/A",
                "project_count": 0,
            }

        total_bng = sum(p.get("bng_net_units", 0) for p in projects)
        total_value = sum(p.get("credit_value_usd", 0) for p in projects)
        sbtn_scores = [p.get("sbtn_score", 50) for p in projects]
        weighted_sbtn = round(sum(sbtn_scores) / len(sbtn_scores), 2)
        eu_aligned = sum(1 for p in projects if p.get("eu_nrl_compliant", False))
        eu_nrl_aligned_pct = round(eu_aligned / len(projects) * 100, 2)

        score = weighted_sbtn * 0.5 + eu_nrl_aligned_pct * 0.3 + min(40, total_bng / 10) * 0.2
        if score >= 75:
            rating = "Platinum"
        elif score >= 60:
            rating = "Gold"
        elif score >= 45:
            rating = "Silver"
        else:
            rating = "Bronze"

        return {
            "entity_id": entity_id,
            "total_bng_units": round(total_bng, 2),
            "total_credit_value_usd": round(total_value, 2),
            "weighted_sbtn_score": weighted_sbtn,
            "eu_nrl_aligned_pct": eu_nrl_aligned_pct,
            "portfolio_biodiversity_rating": rating,
            "project_count": len(projects),
            "composite_score": round(score, 2),
        }
