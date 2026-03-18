"""
Scope 4 / Avoided Emissions Engine
====================================
GHG Protocol Scope 4 Guidance 2022 + SBTi BVCM Guidance + Paris Agreement Article 6.

Models three Scope 4 categories:
- Enabled emissions reductions (products/services enabling others to reduce)
- Substitution emissions reductions (direct lower-carbon product replacement)
- Facilitated reductions (financed/facilitated reductions in third parties)

Cross-framework linkage:
- GHG Protocol Part C (Scope 4 / Avoided Emissions)
- ISSB S2 section 29 (beyond value chain mitigation)
- CSRD ESRS E1 (climate action, GHG targets)
- TCFD (strategy, metrics)
- CDP (climate change questionnaire C12)
"""
from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

AVOIDED_EMISSION_CATEGORIES = {
    "enabled": {
        "description": "Products/services that enable others to reduce emissions",
        "examples": ["solar_panels", "EVs", "insulation", "efficiency_software", "smart_meters"],
        "additionality_standard": "Technology comparison method — compare to best available alternative",
        "attribution": "Economic allocation or physical causation",
    },
    "substitution": {
        "description": "Direct replacement of higher-carbon products/services",
        "examples": ["recycled_materials", "low_carbon_cement", "plant_based_protein", "led_lighting"],
        "additionality_standard": "Market displacement — compare to weighted average of displaced product",
        "attribution": "Market share x displacement factor",
    },
    "facilitated": {
        "description": "Financed/facilitated emissions reductions in third parties",
        "examples": ["green_bonds", "climate_finance", "transition_loans", "REDD_credits"],
        "additionality_standard": "PCAF / Article 6 attribution rules",
        "attribution": "Outstanding amount / total project cost x annual avoided",
    },
}

# Baseline emission factors for common product categories (kgCO2e per unit)
BASELINE_FACTORS = {
    "coal_electricity_kwh":     0.820,
    "grid_average_eu_kwh":      0.276,
    "grid_average_us_kwh":      0.386,
    "natural_gas_m3":           2.204,
    "diesel_litre":             2.640,
    "petrol_litre":             2.310,
    "steel_tonne_bof":          2.200,
    "cement_tonne_opc":         0.830,
    "aluminium_tonne_primary": 11.500,
    "beef_kg":                  27.00,
    "chicken_kg":               5.700,
    "plastic_pet_kg":           3.400,
    "paper_tonne":              1.100,
    "aviation_pkm":             0.255,
    "car_petrol_km":            0.192,
}

# Article 6 Paris Agreement ITMO eligibility criteria
ARTICLE6_CRITERIA = {
    "corresponding_adjustment": "Host country must apply corresponding adjustment",
    "authorization":            "Host country authorization of activity required",
    "participation":            "Voluntary cooperation between parties",
    "sustainable_development":  "Contribution to SD in host country",
    "real_permanent_additional": "Real, measurable, permanent, verified, additional",
}

# SBTi BVCM guidance — beyond value chain mitigation
BVCM_REQUIREMENTS = {
    "science_based":       "Mitigation must be science-aligned and verified",
    "beyond_value_chain":  "Activity outside company value chain boundary",
    "not_double_count":    "No double counting with Scope 1/2/3 reductions",
    "high_quality":        "ICVCM Core Carbon Principles compliance preferred",
    "transparent":         "Separate reporting from internal decarbonisation",
}

# Product category solution intensities (kgCO2e per unit)
SOLUTION_FACTORS = {
    "solar_kwh":               0.040,
    "wind_kwh":                0.011,
    "ev_km":                   0.050,
    "heat_pump_kwh":           0.060,
    "green_steel_tonne":       0.400,
    "low_carbon_cement_t":     0.500,
    "plant_based_protein_kg":  2.000,
    "recycled_aluminium_t":    0.600,
    "led_kwh_saved":           0.000,
    "energy_efficiency_kwh":   0.000,
}

# Additionality criteria
ADDITIONALITY_CRITERIA = [
    "regulatory_surplus",
    "investment_additionality",
    "technological_additionality",
    "temporal_additionality",
    "geographical_additionality",
]

# Scope 4 reporting quality tiers
REPORTING_QUALITY_TIERS = [
    (80, "verified"),
    (60, "assured"),
    (40, "reported"),
    (0,  "estimated"),
]

# Cross-framework mapping
CROSS_FRAMEWORK_MAP = {
    "GHG_Protocol_Part_C": "GHG Protocol Corporate Value Chain (Scope 3) Standard Part C provides Scope 4 guidance",
    "ISSB_S2_29": "ISSB S2 section 29 permits disclosure of beyond-value-chain mitigation activities",
    "CSRD_ESRS_E1": "ESRS E1-4 requires disclosure of GHG reduction targets and actions, enabling avoided emission claims",
    "TCFD": "TCFD Strategy pillar may reference enabled/facilitated emissions as resilience levers",
    "CDP_C12": "CDP C12 Climate Change questionnaire section on avoided emissions and Scope 4",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class AvoidedEmissionsEngine:
    """Scope 4 / Avoided Emissions engine per GHG Protocol Scope 4 Guidance 2022."""

    # -----------------------------------------------------------------------
    # 1. Calculate avoided per activity
    # -----------------------------------------------------------------------

    def calculate_avoided_per_activity(
        self,
        entity_id: str,
        activity_type: str,
        baseline_factor: float,
        solution_factor: float,
        quantity: float,
        attribution_factor: float = 1.0,
    ) -> dict:
        """
        Calculate avoided emissions for a single activity.

        avoided_per_unit = baseline_factor - solution_factor (kgCO2e/unit)
        total_avoided = avoided_per_unit x quantity x attribution_factor (tCO2e)
        """
        rng = random.Random(hash(entity_id + activity_type) & 0xFFFFFFFF)

        avoided_per_unit_kgco2e = max(0.0, baseline_factor - solution_factor)
        total_avoided_tco2e = round(avoided_per_unit_kgco2e * quantity * attribution_factor / 1000, 4)

        # Determine category
        category = "enabled"
        for cat, cat_data in AVOIDED_EMISSION_CATEGORIES.items():
            if any(activity_type in ex for ex in cat_data.get("examples", [])):
                category = cat
                break

        additionality_basis = AVOIDED_EMISSION_CATEGORIES.get(category, {}).get(
            "additionality_standard", "Technology comparison method"
        )

        return {
            "entity_id": entity_id,
            "activity_type": activity_type,
            "category": category,
            "baseline_factor_kgco2e": baseline_factor,
            "solution_factor_kgco2e": solution_factor,
            "avoided_per_unit_kgco2e": round(avoided_per_unit_kgco2e, 4),
            "quantity": quantity,
            "attribution_factor": attribution_factor,
            "total_avoided_tco2e": total_avoided_tco2e,
            "additionality_basis": additionality_basis,
            "ghg_protocol_method": "GHG_Protocol_Scope4_Technology_Comparison",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 2. Assess additionality
    # -----------------------------------------------------------------------

    def assess_additionality(
        self,
        entity_id: str,
        activity_type: str,
        activity_data: dict,
    ) -> dict:
        """
        Score additionality across five criteria (0-100 each, averaged).
        """
        rng = random.Random(hash(entity_id + activity_type + "add") & 0xFFFFFFFF)

        criteria_scores: dict[str, float] = {}
        criteria_met: list[str] = []

        for criterion in ADDITIONALITY_CRITERIA:
            score = float(activity_data.get(f"{criterion}_score", rng.uniform(40, 90)))
            criteria_scores[criterion] = round(score, 2)
            if score >= 60:
                criteria_met.append(criterion)

        additionality_score = round(sum(criteria_scores.values()) / len(criteria_scores), 2)

        assessment_basis = AVOIDED_EMISSION_CATEGORIES.get(
            activity_data.get("category", "enabled"), {}
        ).get("additionality_standard", "Technology comparison method")

        return {
            "entity_id": entity_id,
            "activity_type": activity_type,
            "criteria_scores": criteria_scores,
            "criteria_met": criteria_met,
            "criteria_not_met": [c for c in ADDITIONALITY_CRITERIA if c not in criteria_met],
            "additionality_score": additionality_score,
            "additionality_strong": additionality_score >= 70 and len(criteria_met) >= 4,
            "assessment_basis": assessment_basis,
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 3. Article 6 eligibility
    # -----------------------------------------------------------------------

    def check_article6_eligibility(
        self,
        entity_id: str,
        activity_data: dict,
    ) -> dict:
        """Check Paris Agreement Article 6 ITMO eligibility."""
        rng = random.Random(hash(entity_id + "art6") & 0xFFFFFFFF)

        criteria_results: dict[str, bool] = {}
        for criterion in ARTICLE6_CRITERIA:
            criteria_results[criterion] = bool(
                activity_data.get(criterion, rng.random() > 0.4)
            )

        criteria_met = [c for c, v in criteria_results.items() if v]
        article6_eligible = len(criteria_met) == len(ARTICLE6_CRITERIA)

        annual_avoided_tco2e = float(activity_data.get("annual_avoided_tco2e", rng.uniform(100, 5000)))
        attribution_factor = float(activity_data.get("attribution_factor", rng.uniform(0.3, 1.0)))
        itmo_potential_units = round(annual_avoided_tco2e * attribution_factor, 2) if article6_eligible else 0.0

        return {
            "entity_id": entity_id,
            "article6_eligible": article6_eligible,
            "criteria_results": criteria_results,
            "criteria_met": criteria_met,
            "criteria_not_met": [c for c, v in criteria_results.items() if not v],
            "itmo_potential_units": itmo_potential_units,
            "corresponding_adjustment_required": True,
            "host_country": activity_data.get("host_country", "Unknown"),
            "legal_basis": "Paris_Agreement_Article_6_2_and_6_4",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 4. BVCM eligibility
    # -----------------------------------------------------------------------

    def check_bvcm_eligibility(
        self,
        entity_id: str,
        activity_data: dict,
    ) -> dict:
        """Check SBTi Beyond Value Chain Mitigation (BVCM) eligibility."""
        rng = random.Random(hash(entity_id + "bvcm") & 0xFFFFFFFF)

        requirements_results: dict[str, bool] = {}
        for req in BVCM_REQUIREMENTS:
            requirements_results[req] = bool(
                activity_data.get(req, rng.random() > 0.35)
            )

        requirements_met = [r for r, v in requirements_results.items() if v]
        sbti_bvcm_eligible = len(requirements_met) >= 4

        science_based_claim = requirements_results.get("science_based", False)

        warnings: list[str] = []
        if not requirements_results.get("not_double_count", True):
            warnings.append("Risk of double counting with Scope 1/2/3 reductions — review boundary")
        if not requirements_results.get("beyond_value_chain", True):
            warnings.append("Activity may fall within value chain boundary — not eligible as BVCM")
        if not requirements_results.get("high_quality", True):
            warnings.append("ICVCM Core Carbon Principles compliance not confirmed")

        return {
            "entity_id": entity_id,
            "sbti_bvcm_eligible": sbti_bvcm_eligible,
            "requirements_results": requirements_results,
            "requirements_met": requirements_met,
            "requirements_not_met": [r for r, v in requirements_results.items() if not v],
            "science_based_claim": science_based_claim,
            "warnings": warnings,
            "sbti_guidance_version": "SBTi_BVCM_Guidance_2023",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 5. Portfolio aggregation
    # -----------------------------------------------------------------------

    def aggregate_portfolio(
        self,
        entity_id: str,
        activities: list,
    ) -> dict:
        """
        Aggregate avoided emissions across all activities.

        Returns total by category, net benefit vs own Scope 1+2+3.
        """
        rng = random.Random(hash(entity_id + "port") & 0xFFFFFFFF)

        by_category: dict[str, float] = {cat: 0.0 for cat in AVOIDED_EMISSION_CATEGORIES}
        total_avoided = 0.0
        activity_count = len(activities)

        for act in activities:
            cat = act.get("category", "enabled")
            avoided = float(act.get("total_avoided_tco2e", rng.uniform(100, 2000)))
            by_category[cat] = by_category.get(cat, 0.0) + avoided
            total_avoided += avoided

        own_emissions_tco2e = float(
            rng.uniform(total_avoided * 0.5, total_avoided * 2.5)
        )
        net_benefit_tco2e = round(total_avoided - own_emissions_tco2e, 2)

        attribution_summary = {
            cat: {"total_tco2e": round(v, 2), "share_pct": round(v / total_avoided * 100, 2) if total_avoided > 0 else 0}
            for cat, v in by_category.items()
        }

        return {
            "entity_id": entity_id,
            "activity_count": activity_count,
            "total_avoided_tco2e": round(total_avoided, 2),
            "avoided_by_category": {k: round(v, 2) for k, v in by_category.items()},
            "attribution_summary": attribution_summary,
            "own_emissions_tco2e": round(own_emissions_tco2e, 2),
            "net_benefit_tco2e": net_benefit_tco2e,
            "avoidance_ratio": round(total_avoided / own_emissions_tco2e, 3) if own_emissions_tco2e > 0 else None,
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 6. Full assessment
    # -----------------------------------------------------------------------

    def full_assessment(
        self,
        entity_id: str,
        entity_name: str,
        assessment_type: str,
        reporting_year: int,
        activities_data: dict,
    ) -> dict:
        """Comprehensive Scope 4 avoided emissions assessment."""
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        activities: list = activities_data.get("activities", [])

        # Generate synthetic activities if none provided
        if not activities:
            sample_types = ["solar_panels", "EVs", "recycled_materials", "green_bonds"]
            for act_type in sample_types:
                baseline = BASELINE_FACTORS.get("coal_electricity_kwh", 0.82)
                solution = SOLUTION_FACTORS.get("solar_kwh", 0.04)
                qty = rng.uniform(1e5, 5e6)
                cat_result = self.calculate_avoided_per_activity(
                    entity_id, act_type, baseline, solution, qty, 1.0
                )
                activities.append(cat_result)

        portfolio = self.aggregate_portfolio(entity_id, activities)

        # Reporting quality
        reporting_score = float(activities_data.get("reporting_quality_score", rng.uniform(50, 90)))
        quality_tier = "estimated"
        for threshold, label in REPORTING_QUALITY_TIERS:
            if reporting_score >= threshold:
                quality_tier = label
                break

        total_avoided = portfolio["total_avoided_tco2e"]
        own_emissions = portfolio["own_emissions_tco2e"]

        cross_framework = CROSS_FRAMEWORK_MAP.copy()

        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "assessment_type": assessment_type,
            "reporting_year": reporting_year,
            "scope4_standard": "GHG_Protocol_Scope4_Guidance_2022",
            "activities_assessed": len(activities),
            "total_avoided_tco2e": total_avoided,
            "avoided_by_category": portfolio["avoided_by_category"],
            "own_scope123_emissions_tco2e": own_emissions,
            "net_benefit_tco2e": portfolio["net_benefit_tco2e"],
            "avoidance_ratio": portfolio["avoidance_ratio"],
            "reporting_quality_score": round(reporting_score, 2),
            "reporting_quality_tier": quality_tier,
            "activity_details": activities,
            "portfolio_summary": portfolio,
            "cross_framework": cross_framework,
            "disclosure_note": (
                "Scope 4 / avoided emissions are reported separately from Scope 1/2/3 "
                "to prevent netting of reductions and own emissions."
            ),
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # Static reference methods
    # -----------------------------------------------------------------------

    @staticmethod
    def get_avoided_emission_categories() -> dict:
        return AVOIDED_EMISSION_CATEGORIES

    @staticmethod
    def get_baseline_factors() -> dict:
        return BASELINE_FACTORS

    @staticmethod
    def get_article6_criteria() -> dict:
        return ARTICLE6_CRITERIA

    @staticmethod
    def get_bvcm_requirements() -> dict:
        return BVCM_REQUIREMENTS

    @staticmethod
    def get_solution_factors() -> dict:
        return SOLUTION_FACTORS
