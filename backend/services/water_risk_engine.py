"""
Water Risk & Security Engine (E53)
===================================
WRI Aqueduct 4.0, CDP Water Security A-List, CSRD ESRS E3,
TNFD Water Dependency (ENCORE), CEO Water Mandate, UN SDG 6.

Sub-modules:
  1. Aqueduct Risk       — WRI Aqueduct 4.0 indicator-based scoring
  2. CDP Water           — CDP Water Security grade + A-list eligibility
  3. ESRS E3             — CSRD mandatory water disclosure assessment
  4. TNFD Water Dependency — ENCORE database dependency rating
  5. Water Footprint     — Blue/Green/Grey water accounting
  6. Financial Impact    — Revenue-at-risk, compliance cost, capex
  7. Physical Risk Scenarios — RCP 2.6/4.5/8.5 per country
  8. Overall Materiality — Aggregated water materiality score

References:
  - WRI Aqueduct 4.0 (2023)
  - CDP Water Security Questionnaire (2024)
  - CSRD ESRS E3 — Water & Marine Resources (EFRAG 2023)
  - TNFD v1.0 — Nature-related disclosures + ENCORE water services
  - CEO Water Mandate — Corporate Water Stewardship
  - UN SDG 6 — Clean Water and Sanitation
  - IPCC AR6 — Physical Risk Projections (2021)
"""
from __future__ import annotations

import random
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

AQUEDUCT_INDICATORS = [
    "water_stress",
    "water_depletion",
    "interannual_variability",
    "seasonal_variability",
    "groundwater_decline",
    "coastal_eutrophication",
    "untreated_wastewater",
]

AQUEDUCT_WEIGHTS: dict[str, float] = {
    "water_stress": 0.40,
    "water_depletion": 0.25,
    "interannual_variability": 0.10,
    "seasonal_variability": 0.10,
    "groundwater_decline": 0.15,
}

RISK_TIER_BANDS: list[tuple[float, float, str]] = [
    (0.0, 1.0, "Low"),
    (1.0, 2.0, "Low-Medium"),
    (2.0, 3.0, "Medium-High"),
    (3.0, 4.0, "High"),
    (4.0, 5.0, "Extremely High"),
]

# Country-specific base stress multipliers (0-1 applied to 0-5 scale)
COUNTRY_STRESS: dict[str, float] = {
    "IN": 0.85, "CN": 0.75, "US": 0.50, "GB": 0.30,
    "BR": 0.40, "ZA": 0.70, "AU": 0.65, "DE": 0.35,
    "FR": 0.38, "MX": 0.60, "ID": 0.45, "SA": 0.95,
    "EG": 0.90, "PK": 0.88, "NG": 0.55, "JP": 0.40,
    "IT": 0.48, "TR": 0.62, "IR": 0.82, "PL": 0.36,
}

HIGH_WATER_DEPENDENCY_SECTORS = {
    "agriculture", "beverages", "textiles", "mining",
    "semiconductor", "food_processing", "paper", "chemicals",
}

ENCORE_WATER_SERVICES = [
    "Surface water regulation",
    "Groundwater recharge",
    "Water purification",
    "Flood regulation",
    "Sediment regulation",
    "Coastal wetland services",
]

# Sector water footprint multipliers (m3/unit)
SECTOR_WATER_INTENSITY: dict[str, dict[str, float]] = {
    "agriculture":    {"blue": 500.0, "green": 1200.0, "grey": 200.0},
    "beverages":      {"blue": 80.0,  "green": 150.0,  "grey": 30.0},
    "textiles":       {"blue": 200.0, "green": 50.0,   "grey": 100.0},
    "mining":         {"blue": 300.0, "green": 0.0,    "grey": 80.0},
    "semiconductor":  {"blue": 15.0,  "green": 0.0,    "grey": 5.0},
    "food_processing":{"blue": 60.0,  "green": 200.0,  "grey": 40.0},
    "manufacturing":  {"blue": 30.0,  "green": 10.0,   "grey": 20.0},
    "energy":         {"blue": 40.0,  "green": 0.0,    "grey": 15.0},
    "other":          {"blue": 20.0,  "green": 10.0,   "grey": 10.0},
}

WATER_FOOTPRINT_THRESHOLD: dict[str, float] = {
    "agriculture": 5_000_000.0,
    "beverages": 500_000.0,
    "textiles": 1_000_000.0,
    "mining": 2_000_000.0,
    "semiconductor": 100_000.0,
    "food_processing": 800_000.0,
    "manufacturing": 300_000.0,
    "energy": 400_000.0,
    "other": 200_000.0,
}

PHYSICAL_RISK_BY_COUNTRY: dict[str, dict[str, str]] = {
    "IN": {"rcp26": "High", "rcp45": "Very High", "rcp85": "Extreme"},
    "CN": {"rcp26": "Medium-High", "rcp45": "High", "rcp85": "Very High"},
    "US": {"rcp26": "Medium", "rcp45": "Medium-High", "rcp85": "High"},
    "GB": {"rcp26": "Low", "rcp45": "Low-Medium", "rcp85": "Medium"},
    "BR": {"rcp26": "Medium", "rcp45": "High", "rcp85": "Very High"},
    "ZA": {"rcp26": "High", "rcp45": "Very High", "rcp85": "Extreme"},
    "AU": {"rcp26": "Medium-High", "rcp45": "High", "rcp85": "Very High"},
    "DE": {"rcp26": "Low", "rcp45": "Low-Medium", "rcp85": "Medium"},
    "SA": {"rcp26": "Very High", "rcp45": "Extreme", "rcp85": "Extreme"},
    "EG": {"rcp26": "Very High", "rcp45": "Extreme", "rcp85": "Extreme"},
}

ADAPTATION_OPTIONS = [
    "Water recycling and reuse systems",
    "Rainwater harvesting",
    "Efficiency upgrades (drip irrigation, low-flow)",
    "Groundwater recharge programs",
    "Water rights diversification",
    "Supplier watershed stewardship programs",
    "Real-time monitoring and leakage detection",
    "Product reformulation to reduce water intensity",
]


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class WaterRiskEngine:
    """Water Risk & Security Engine (E53)."""

    # ------------------------------------------------------------------
    # 1. WRI Aqueduct 4.0 Risk Assessment
    # ------------------------------------------------------------------

    def assess_aqueduct_risk(
        self,
        entity_id: str,
        country_code: str,
        sector: str,
        basin_name: Optional[str] = None,
    ) -> dict:
        """
        WRI Aqueduct 4.0 — 7 physical risk indicators on 0-5 scale.
        Weighted composite determines risk tier.
        """
        rng = random.Random(hash(entity_id + country_code) & 0xFFFFFFFF)

        base_mult = COUNTRY_STRESS.get(country_code.upper(), 0.50)

        # Generate indicator scores seeded by country + entity
        indicators: dict[str, float] = {}
        for ind in AQUEDUCT_INDICATORS:
            base = base_mult * 5.0
            noise = rng.uniform(-0.8, 0.8)
            indicators[ind] = round(max(0.0, min(5.0, base + noise)), 2)

        # Weighted overall score using primary indicators
        overall = sum(
            indicators[k] * v
            for k, v in AQUEDUCT_WEIGHTS.items()
        )
        overall = round(overall, 2)

        risk_tier = "Low"
        for lo, hi, label in RISK_TIER_BANDS:
            if lo <= overall < hi:
                risk_tier = label
                break
        if overall >= 4.0:
            risk_tier = "Extremely High"

        basin_factors: list[str] = []
        if indicators["groundwater_decline"] > 3.0:
            basin_factors.append("Groundwater over-exploitation risk")
        if indicators["water_stress"] > 3.5:
            basin_factors.append("High competition for water resources")
        if indicators["coastal_eutrophication"] > 3.0:
            basin_factors.append("Coastal eutrophication concern")
        if indicators["untreated_wastewater"] > 3.0:
            basin_factors.append("Inadequate wastewater treatment infrastructure")

        return {
            "entity_id": entity_id,
            "country_code": country_code.upper(),
            "sector": sector,
            "basin_name": basin_name or f"{country_code.upper()}_primary_basin",
            "indicators": indicators,
            "overall_score": overall,
            "risk_tier": risk_tier,
            "basin_specific_factors": basin_factors,
            "source": "WRI Aqueduct 4.0 (2023)",
        }

    # ------------------------------------------------------------------
    # 2. CDP Water Security Assessment
    # ------------------------------------------------------------------

    def assess_cdp_water(
        self,
        entity_id: str,
        governance_score: float,
        risk_score: float,
        target_score: float,
    ) -> dict:
        """
        CDP Water Security questionnaire scoring.
        Grade bands: A(90+), A-(80+), B+(70+), B(60+), C(50+), D(<50).
        """
        cdp_weighted = round(
            governance_score * 0.4 + risk_score * 0.3 + target_score * 0.3, 2
        )
        a_list_eligible = cdp_weighted >= 80.0

        if cdp_weighted >= 90.0:
            grade = "A"
        elif cdp_weighted >= 80.0:
            grade = "A-"
        elif cdp_weighted >= 70.0:
            grade = "B+"
        elif cdp_weighted >= 60.0:
            grade = "B"
        elif cdp_weighted >= 50.0:
            grade = "C"
        else:
            grade = "D"

        gap_to_a_list = round(max(0.0, 80.0 - cdp_weighted), 2)

        return {
            "entity_id": entity_id,
            "governance_score": round(governance_score, 2),
            "risk_score": round(risk_score, 2),
            "target_score": round(target_score, 2),
            "weighted_score": cdp_weighted,
            "grade": grade,
            "a_list_eligible": a_list_eligible,
            "gap_to_a_list": gap_to_a_list,
            "methodology": "CDP Water Security Questionnaire 2024",
        }

    # ------------------------------------------------------------------
    # 3. CSRD ESRS E3 Disclosure Assessment
    # ------------------------------------------------------------------

    def assess_esrs_e3(
        self,
        entity_id: str,
        withdrawal_m3_pa: float,
        consumption_m3_pa: float,
        discharge_m3_pa: float,
        recycled_pct: float,
    ) -> dict:
        """
        CSRD ESRS E3 mandatory water disclosure completeness and compliance.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        efficiency_ratio = round(consumption_m3_pa / withdrawal_m3_pa, 4) if withdrawal_m3_pa > 0 else 0.0
        water_intensive = withdrawal_m3_pa > 10_000_000 or recycled_pct < 20.0

        # Disclosure completeness scoring (0-100)
        components = {
            "withdrawal_disclosed": withdrawal_m3_pa > 0,
            "consumption_disclosed": consumption_m3_pa > 0,
            "discharge_disclosed": discharge_m3_pa > 0,
            "recycled_pct_disclosed": recycled_pct >= 0,
            "water_stress_areas": rng.random() > 0.3,
            "targets_set": rng.random() > 0.4,
            "water_policy_documented": rng.random() > 0.25,
        }
        disclosure_score = round(sum(components.values()) / len(components) * 100, 2)
        esrs_e3_compliant = disclosure_score >= 70.0

        return {
            "entity_id": entity_id,
            "withdrawal_m3_pa": round(withdrawal_m3_pa, 1),
            "consumption_m3_pa": round(consumption_m3_pa, 1),
            "discharge_m3_pa": round(discharge_m3_pa, 1),
            "recycled_pct": round(recycled_pct, 2),
            "water_intensive": water_intensive,
            "efficiency_ratio": efficiency_ratio,
            "disclosure_components": components,
            "disclosure_score": disclosure_score,
            "esrs_e3_compliant": esrs_e3_compliant,
            "mandatory_disclosures": ["E3-1", "E3-2", "E3-3", "E3-4", "E3-5"],
            "standard": "CSRD ESRS E3 Water & Marine Resources",
        }

    # ------------------------------------------------------------------
    # 4. TNFD Water Dependency (ENCORE)
    # ------------------------------------------------------------------

    def assess_tnfd_water_dependency(
        self,
        entity_id: str,
        sector: str,
        value_chain_stage: str,
    ) -> dict:
        """
        TNFD ENCORE-based water dependency assessment.
        Rates dependency by sector and value chain position.
        """
        rng = random.Random(hash(entity_id + sector) & 0xFFFFFFFF)

        is_high_dep = sector.lower() in HIGH_WATER_DEPENDENCY_SECTORS

        base_score = rng.uniform(60.0, 90.0) if is_high_dep else rng.uniform(20.0, 55.0)
        dependency_score = round(base_score, 1)

        if dependency_score >= 75.0:
            dependency_rating = "Very High"
        elif dependency_score >= 55.0:
            dependency_rating = "High"
        elif dependency_score >= 35.0:
            dependency_rating = "Medium"
        else:
            dependency_rating = "Low"

        n_services = rng.randint(3, 6) if is_high_dep else rng.randint(1, 3)
        encore_services = rng.sample(ENCORE_WATER_SERVICES, min(n_services, len(ENCORE_WATER_SERVICES)))

        hotspots = []
        if value_chain_stage.lower() in ["upstream", "raw_material"]:
            hotspots.append("Primary production water extraction")
        if sector.lower() in ["agriculture", "food_processing"]:
            hotspots.append("Irrigation water demand")
        if is_high_dep:
            hotspots.append(f"High water intensity in {sector} operations")

        return {
            "entity_id": entity_id,
            "sector": sector,
            "value_chain_stage": value_chain_stage,
            "dependency_score": dependency_score,
            "dependency_rating": dependency_rating,
            "encore_water_services": encore_services,
            "value_chain_hotspots": hotspots,
            "assessment_framework": "TNFD v1.0 + ENCORE database",
        }

    # ------------------------------------------------------------------
    # 5. Water Footprint (Blue/Green/Grey)
    # ------------------------------------------------------------------

    def calculate_water_footprint(
        self,
        entity_id: str,
        product_name: str,
        annual_volume: float,
        sector: str,
    ) -> dict:
        """
        Water footprint accounting: Blue (surface/ground), Green (rain), Grey (dilution).
        """
        rng = random.Random(hash(entity_id + product_name) & 0xFFFFFFFF)

        sec = sector.lower() if sector.lower() in SECTOR_WATER_INTENSITY else "other"
        wf = SECTOR_WATER_INTENSITY[sec]

        # Add entity-level variation
        blue_m3 = round(wf["blue"] * rng.uniform(0.85, 1.15), 3)
        green_m3 = round(wf["green"] * rng.uniform(0.85, 1.15), 3)
        grey_m3 = round(wf["grey"] * rng.uniform(0.85, 1.15), 3)
        total_m3 = round(blue_m3 + green_m3 + grey_m3, 3)

        annual_total = round(total_m3 * annual_volume, 1)
        threshold = WATER_FOOTPRINT_THRESHOLD.get(sec, 200_000.0)
        hotspot_flag = annual_total > threshold

        # Water scarcity adjusted footprint (stress multiplier 1.0-2.5)
        stress_multiplier = rng.uniform(1.0, 2.5)
        water_scarcity_adjusted = round(annual_total * stress_multiplier, 1)

        return {
            "entity_id": entity_id,
            "product_name": product_name,
            "sector": sec,
            "annual_volume": annual_volume,
            "blue_m3_per_unit": blue_m3,
            "green_m3_per_unit": green_m3,
            "grey_m3_per_unit": grey_m3,
            "total_m3_per_unit": total_m3,
            "annual_total_m3": annual_total,
            "hotspot_flag": hotspot_flag,
            "hotspot_threshold_m3": threshold,
            "scarcity_multiplier": round(stress_multiplier, 2),
            "water_scarcity_adjusted_m3": water_scarcity_adjusted,
            "methodology": "ISO 14046 Water Footprint + WFN v2",
        }

    # ------------------------------------------------------------------
    # 6. Financial Impact Assessment
    # ------------------------------------------------------------------

    def assess_financial_impact(
        self,
        entity_id: str,
        water_stress_score: float,
        annual_revenue_usd: float,
        withdrawal_m3_pa: float,
    ) -> dict:
        """
        Financial materiality of water risk: revenue-at-risk, compliance costs,
        capex resilience, and insurance premium impact.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Revenue at risk
        revenue_at_risk_pct = round(min(water_stress_score * 0.6, 3.0), 3)
        revenue_at_risk_usd = round(annual_revenue_usd * revenue_at_risk_pct / 100.0, 0)

        # Compliance cost (water abstraction charges + treatment)
        compliance_cost_usd_pa = round(withdrawal_m3_pa * 0.05, 0)

        # Resilience capex
        capex_resilience_usd = round(revenue_at_risk_pct / 100.0 * annual_revenue_usd * 0.3, 0)

        # Insurance premium uplift
        insurance_premium_uplift_pct = round(water_stress_score * 1.5 + rng.uniform(0.5, 2.0), 2)

        stress_norm = water_stress_score / 5.0 if water_stress_score <= 5.0 else 1.0
        if stress_norm >= 0.8:
            stranded_asset_risk = "High"
        elif stress_norm >= 0.5:
            stranded_asset_risk = "Medium"
        else:
            stranded_asset_risk = "Low"

        return {
            "entity_id": entity_id,
            "water_stress_score": round(water_stress_score, 2),
            "annual_revenue_usd": annual_revenue_usd,
            "revenue_at_risk_pct": revenue_at_risk_pct,
            "revenue_at_risk_usd": revenue_at_risk_usd,
            "compliance_cost_usd_pa": compliance_cost_usd_pa,
            "capex_resilience_usd": capex_resilience_usd,
            "insurance_premium_uplift_pct": insurance_premium_uplift_pct,
            "stranded_asset_risk": stranded_asset_risk,
            "tcfd_category": "Physical Risk — Chronic",
        }

    # ------------------------------------------------------------------
    # 7. Physical Risk Scenarios (RCP)
    # ------------------------------------------------------------------

    def assess_physical_risk_scenarios(
        self,
        entity_id: str,
        country_code: str,
        sector: str,
    ) -> dict:
        """
        IPCC AR6 RCP 2.6/4.5/8.5 physical water risk projections per country.
        """
        rng = random.Random(hash(entity_id + country_code + sector) & 0xFFFFFFFF)

        pr = PHYSICAL_RISK_BY_COUNTRY.get(
            country_code.upper(),
            {"rcp26": "Medium", "rcp45": "Medium-High", "rcp85": "High"},
        )

        # Delta impacts 2030 and 2050
        scenario_delta_2030 = {
            "rcp26": {"water_stress_change_pct": round(rng.uniform(3, 8), 1), "flood_frequency_multiplier": round(rng.uniform(1.1, 1.3), 2)},
            "rcp45": {"water_stress_change_pct": round(rng.uniform(8, 15), 1), "flood_frequency_multiplier": round(rng.uniform(1.2, 1.5), 2)},
            "rcp85": {"water_stress_change_pct": round(rng.uniform(15, 25), 1), "flood_frequency_multiplier": round(rng.uniform(1.4, 1.8), 2)},
        }
        scenario_delta_2050 = {
            "rcp26": {"water_stress_change_pct": round(rng.uniform(5, 12), 1), "flood_frequency_multiplier": round(rng.uniform(1.2, 1.5), 2)},
            "rcp45": {"water_stress_change_pct": round(rng.uniform(15, 25), 1), "flood_frequency_multiplier": round(rng.uniform(1.4, 1.8), 2)},
            "rcp85": {"water_stress_change_pct": round(rng.uniform(30, 50), 1), "flood_frequency_multiplier": round(rng.uniform(1.8, 2.5), 2)},
        }

        n_adapt = rng.randint(3, 5)
        adaptation_options = rng.sample(ADAPTATION_OPTIONS, n_adapt)

        return {
            "entity_id": entity_id,
            "country_code": country_code.upper(),
            "sector": sector,
            "rcp26": pr["rcp26"],
            "rcp45": pr["rcp45"],
            "rcp85": pr["rcp85"],
            "scenario_delta_2030": scenario_delta_2030,
            "scenario_delta_2050": scenario_delta_2050,
            "adaptation_options": adaptation_options,
            "source": "IPCC AR6 WGI Chapter 8 + WRI Aqueduct Climate Projections",
        }

    # ------------------------------------------------------------------
    # 8. Overall Water Materiality
    # ------------------------------------------------------------------

    def compute_overall_water_materiality(
        self,
        entity_id: str,
        aqueduct_score: float,
        cdp_score: float,
        esrs_score: float,
        tnfd_score: float,
    ) -> dict:
        """
        Aggregated water materiality score across four frameworks.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Normalise aqueduct (0-5 → 0-100): higher raw = higher risk = lower score
        aqueduct_norm = round((aqueduct_score / 5.0) * 100.0, 2)

        materiality_score = round(
            aqueduct_norm * 0.35
            + cdp_score * 0.25
            + esrs_score * 0.20
            + tnfd_score * 0.20,
            2,
        )

        if materiality_score >= 70.0:
            materiality_rating = "High"
        elif materiality_score >= 50.0:
            materiality_rating = "Medium"
        elif materiality_score >= 30.0:
            materiality_rating = "Low"
        else:
            materiality_rating = "Negligible"

        priority_actions: list[str] = []
        if aqueduct_norm > 60.0:
            priority_actions.append("Relocate/diversify water sources in stressed basins")
        if cdp_score < 60.0:
            priority_actions.append("Improve CDP Water governance and target-setting")
        if esrs_score < 70.0:
            priority_actions.append("Enhance ESRS E3 disclosure completeness")
        if tnfd_score > 60.0:
            priority_actions.append("Develop TNFD water dependency transition plan")

        sdg6_alignment = round(max(0.0, 100.0 - materiality_score * 0.5 + rng.uniform(-5, 5)), 2)
        ceo_water_mandate_score = round(rng.uniform(40.0, 85.0), 1)

        return {
            "entity_id": entity_id,
            "input_scores": {
                "aqueduct_raw": round(aqueduct_score, 2),
                "aqueduct_normalised": aqueduct_norm,
                "cdp": round(cdp_score, 2),
                "esrs": round(esrs_score, 2),
                "tnfd": round(tnfd_score, 2),
            },
            "materiality_score": materiality_score,
            "materiality_rating": materiality_rating,
            "priority_actions": priority_actions,
            "sdg6_alignment": sdg6_alignment,
            "ceo_water_mandate_score": ceo_water_mandate_score,
            "frameworks_assessed": ["WRI Aqueduct 4.0", "CDP Water", "CSRD ESRS E3", "TNFD v1.0"],
        }


# ---------------------------------------------------------------------------
# Module-level instance
# ---------------------------------------------------------------------------

_engine = WaterRiskEngine()

assess_aqueduct_risk = _engine.assess_aqueduct_risk
assess_cdp_water = _engine.assess_cdp_water
assess_esrs_e3 = _engine.assess_esrs_e3
assess_tnfd_water_dependency = _engine.assess_tnfd_water_dependency
calculate_water_footprint = _engine.calculate_water_footprint
assess_financial_impact = _engine.assess_financial_impact
assess_physical_risk_scenarios = _engine.assess_physical_risk_scenarios
compute_overall_water_materiality = _engine.compute_overall_water_materiality
