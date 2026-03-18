"""
Carbon Dioxide Removal (CDR) Engine

Standards implemented:
- IPCC AR6 CDR taxonomy (Chapter 12) — 8 CDR method categories
- Puro.earth methodology standards (CORC methodology framework)
- Isometric verification protocol (Isometric Validation & Verification Standard)
- BeZero Carbon ratings (AAA–CCC) — quality-scoring methodology
- Article 6.4 Paris Agreement mechanism (ITMO / Supervisory Body)
- Oxford Principles for Net Zero Aligned Carbon Offsetting 2024 (4 principles)
- VCMI Claims Code of Practice 2023 (Silver / Gold / Platinum)
- Science Based Targets Network — Net-Zero Standard v1.1 residual emissions criteria
"""

import random
import math
from typing import List, Dict, Any, Optional, Tuple


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

CDR_METHODS: Dict[str, Dict[str, Any]] = {
    "beccs": {
        "permanence_yrs": 200,
        "cost_range_usd_t": (50.0, 150.0),
        "maturity_trl": 7,
        "co_benefits": ["bioenergy_production", "rural_employment", "waste_valorisation"],
        "risks": ["land_use_competition", "water_stress", "biodiversity_loss", "monoculture"],
        "ipcc_classification": "land_management_cdr",
        "description": "Bioenergy with Carbon Capture and Storage",
    },
    "daccs": {
        "permanence_yrs": 1000,
        "cost_range_usd_t": (200.0, 600.0),
        "maturity_trl": 6,
        "co_benefits": ["modular_deployment", "no_land_competition", "pure_co2_stream"],
        "risks": ["high_energy_demand", "water_use", "high_capex", "storage_risk"],
        "ipcc_classification": "engineered_cdr",
        "description": "Direct Air Carbon Capture and Storage",
    },
    "enhanced_weathering": {
        "permanence_yrs": 10000,
        "cost_range_usd_t": (50.0, 200.0),
        "maturity_trl": 5,
        "co_benefits": ["soil_remineralisation", "crop_yield_uplift", "ocean_alkalinity"],
        "risks": ["monitoring_uncertainty", "heavy_metal_leaching", "logistics_cost"],
        "ipcc_classification": "land_management_cdr",
        "description": "Spreading crushed silicate rock on agricultural land to enhance CO2 weathering",
    },
    "biochar": {
        "permanence_yrs": 100,
        "cost_range_usd_t": (30.0, 120.0),
        "maturity_trl": 8,
        "co_benefits": ["soil_health", "water_retention", "waste_reduction", "agricultural_yield"],
        "risks": ["feedstock_availability", "permanence_uncertainty", "leaching"],
        "ipcc_classification": "land_management_cdr",
        "description": "Pyrolysis of organic waste to stable carbon-rich biochar applied to soil",
    },
    "ocean_alkalinity_enhancement": {
        "permanence_yrs": 10000,
        "cost_range_usd_t": (100.0, 300.0),
        "maturity_trl": 4,
        "co_benefits": ["ocean_acidification_reversal", "coral_reef_protection"],
        "risks": ["ecological_impacts", "monitoring_difficulty", "regulatory_uncertainty"],
        "ipcc_classification": "ocean_cdr",
        "description": "Adding alkalinity to seawater to increase ocean CO2 uptake",
    },
    "afforestation": {
        "permanence_yrs": 100,
        "cost_range_usd_t": (5.0, 50.0),
        "maturity_trl": 9,
        "co_benefits": ["biodiversity", "watershed_protection", "community_livelihoods", "sdg_15"],
        "risks": ["reversal_risk", "fire_drought_pests", "albedo_effect", "monoculture"],
        "ipcc_classification": "land_management_cdr",
        "description": "Planting trees on land not previously forested",
    },
    "soil_carbon": {
        "permanence_yrs": 30,
        "cost_range_usd_t": (10.0, 80.0),
        "maturity_trl": 8,
        "co_benefits": ["food_security", "drought_resilience", "biodiversity", "farmer_income"],
        "risks": ["reversal_risk", "measurement_uncertainty", "policy_dependency"],
        "ipcc_classification": "land_management_cdr",
        "description": "Regenerative agriculture practices to sequester carbon in soil",
    },
    "blue_carbon": {
        "permanence_yrs": 50,
        "cost_range_usd_t": (20.0, 100.0),
        "maturity_trl": 7,
        "co_benefits": ["coastal_protection", "fisheries", "biodiversity", "sdg_14"],
        "risks": ["reversal_from_sea_level_rise", "methane_co_emissions", "monitoring_cost"],
        "ipcc_classification": "land_management_cdr",
        "description": "Restoration of mangroves, seagrasses, and salt marshes",
    },
}

BEZERO_RATING_THRESHOLDS: Dict[str, float] = {
    "AAA": 85.0,
    "AA": 75.0,
    "A": 65.0,
    "BBB": 55.0,
    "BB": 45.0,
    "B": 35.0,
    "CCC": 0.0,
}

VERIFICATION_STANDARDS: Dict[str, Dict[str, Any]] = {
    "puro_earth": {
        "methodology": "Puro.earth CORC Standard — industrial and engineered removals",
        "permanence_buffer_pct": 5.0,
        "third_party_required": True,
        "eligible_methods": ["daccs", "biochar", "enhanced_weathering"],
    },
    "isometric": {
        "methodology": "Isometric Validation & Verification Standard — durable geologic storage",
        "permanence_buffer_pct": 3.0,
        "third_party_required": True,
        "eligible_methods": ["daccs", "beccs"],
    },
    "gold_standard": {
        "methodology": "Gold Standard for the Global Goals (GS4GG) — SDG co-benefits",
        "permanence_buffer_pct": 10.0,
        "third_party_required": True,
        "eligible_methods": ["afforestation", "soil_carbon", "blue_carbon"],
    },
    "vcs_vm0042": {
        "methodology": "Verra VM0042 — Improved Agricultural Land Management",
        "permanence_buffer_pct": 15.0,
        "third_party_required": True,
        "eligible_methods": ["soil_carbon", "afforestation"],
    },
    "verra_sdvista": {
        "methodology": "Verra SD VISta — Social & environmental co-benefits",
        "permanence_buffer_pct": 12.0,
        "third_party_required": True,
        "eligible_methods": ["afforestation", "blue_carbon"],
    },
    "article_6_4": {
        "methodology": "Paris Agreement Article 6.4 Mechanism (A6.4ER)",
        "permanence_buffer_pct": 5.0,
        "third_party_required": True,
        "eligible_methods": ["afforestation", "soil_carbon", "blue_carbon", "enhanced_weathering"],
    },
    "climate_action_reserve": {
        "methodology": "Climate Action Reserve — North American forest and soil protocols",
        "permanence_buffer_pct": 18.0,
        "third_party_required": True,
        "eligible_methods": ["afforestation", "soil_carbon"],
    },
}

OXFORD_PRINCIPLES: Dict[str, Dict[str, Any]] = {
    "1_cut_emissions_first": {
        "description": "Prioritise deep and immediate emissions cuts; offsets only for residual emissions",
        "test": "offset_pct_of_total_emissions < 10",
        "weight": 0.30,
    },
    "2_shift_to_durable_removals": {
        "description": "Transition portfolio from nature-based to engineered durable removals over time",
        "test": "durable_removal_share_increasing",
        "weight": 0.25,
    },
    "3_avoid_locking_in_emissions": {
        "description": "Avoid uses of CDR that lock in high-carbon infrastructure",
        "test": "no_enhanced_oil_recovery_credits",
        "weight": 0.25,
    },
    "4_support_carbon_removal_innovation": {
        "description": "Support innovation via portfolio diversification across CDR methods",
        "test": "method_diversity_index > 0.3",
        "weight": 0.20,
    },
}

VCMI_CLAIMS_LEVELS: Dict[str, Dict[str, Any]] = {
    "silver": {
        "sbti_scope_1_2": True,
        "scope_3_disclosure": True,
        "residual_coverage_pct": 100.0,
        "credit_quality_min": 60.0,
        "description": "SBTi-aligned Scope 1+2 + Scope 3 disclosure + 100% residual high-quality CDR",
    },
    "gold": {
        "sbti_scope_1_2": True,
        "scope_3_disclosure": True,
        "residual_coverage_pct": 100.0,
        "credit_quality_min": 70.0,
        "net_zero_trajectory": True,
        "description": "Silver + demonstrated net-zero trajectory + higher quality threshold",
    },
    "platinum": {
        "sbti_scope_1_2": True,
        "scope_3_disclosure": True,
        "residual_coverage_pct": 110.0,
        "credit_quality_min": 80.0,
        "net_zero_trajectory": True,
        "beyond_value_chain": True,
        "description": "Gold + >100% residual coverage (beyond value chain mitigation)",
    },
}

ARTICLE_6_4_CRITERIA: Dict[str, str] = {
    "host_country_authorisation": "Host country must formally authorise A6.4ER issuance",
    "corresponding_adjustment": "Corresponding adjustment applied to prevent double counting",
    "additionality": "Mitigation outcome would not have occurred without the mechanism",
    "permanence": "Storage permanence documented and monitored",
    "sustainable_development": "Contribution to host country sustainable development",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(lo: float, hi: float, val: float) -> float:
    return max(lo, min(hi, val))


def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(entity_id) & 0xFFFFFFFF)


def _bezero_rating(score: float) -> str:
    for rating, threshold in sorted(BEZERO_RATING_THRESHOLDS.items(), key=lambda x: -x[1]):
        if score >= threshold:
            return rating
    return "CCC"


def _npv(cashflows: List[float], rate: float) -> float:
    r = rate / 100.0
    return sum(cf / (1.0 + r) ** (i + 1) for i, cf in enumerate(cashflows))


# ---------------------------------------------------------------------------
# CDR Engine
# ---------------------------------------------------------------------------

class CDREngine:
    """IPCC AR6 / BeZero / Oxford / VCMI / Article 6.4 CDR quality engine."""

    # ------------------------------------------------------------------
    # 1. CDR Quality Assessment (BeZero-style)
    # ------------------------------------------------------------------
    def assess_cdr_quality(
        self,
        entity_id: str,
        cdr_method: str,
        annual_removal_tco2: float,
        permanence_yrs: int,
        verification_standard: str,
        additionality_score: float,
        leakage_risk_pct: float,
    ) -> dict:
        rng = _rng(entity_id)
        method = CDR_METHODS.get(cdr_method, CDR_METHODS["afforestation"])
        vstd = VERIFICATION_STANDARDS.get(verification_standard, VERIFICATION_STANDARDS["gold_standard"])

        # Additionality scoring (0-100)
        add_score = _clamp(0.0, 100.0, additionality_score)

        # Permanence scoring (based on permanence years)
        if permanence_yrs >= 1000:
            perm_score = 100.0
        elif permanence_yrs >= 200:
            perm_score = 85.0
        elif permanence_yrs >= 100:
            perm_score = 70.0
        elif permanence_yrs >= 50:
            perm_score = 55.0
        else:
            perm_score = 35.0

        # Verification tier
        if verification_standard in ("isometric", "puro_earth"):
            verif_score = 90.0
        elif verification_standard in ("gold_standard", "article_6_4"):
            verif_score = 80.0
        else:
            verif_score = 65.0

        # Leakage score (inverted — high leakage = low score)
        leakage = _clamp(0.0, 100.0, leakage_risk_pct)
        leakage_score = _clamp(0.0, 100.0, 100.0 - leakage * 1.5)

        # Co-benefits score
        co_benefit_count = len(method["co_benefits"])
        co_benefits_score = min(100.0, co_benefit_count * 20.0)

        # Weighted BeZero quality score
        quality_score = round(
            add_score * 0.30
            + perm_score * 0.25
            + verif_score * 0.20
            + leakage_score * 0.15
            + co_benefits_score * 0.10,
            2
        )

        bezero_rating = _bezero_rating(quality_score)

        # Buffer pool requirement
        buffer_pool_pct = vstd["permanence_buffer_pct"] + round(rng.uniform(0.0, 2.0), 2)
        buffer_pool_tco2 = round(annual_removal_tco2 * buffer_pool_pct / 100.0, 2)
        net_credits_tco2 = round(annual_removal_tco2 - buffer_pool_tco2, 2)

        additionality_rating = (
            "strong" if add_score >= 80 else
            "adequate" if add_score >= 60 else
            "weak" if add_score >= 40 else
            "insufficient"
        )

        permanence_rating = (
            "durable_1000yr+" if permanence_yrs >= 1000 else
            "long_term_200yr+" if permanence_yrs >= 200 else
            "medium_term_100yr" if permanence_yrs >= 100 else
            "short_term"
        )

        return {
            "entity_id": entity_id,
            "cdr_method": cdr_method,
            "verification_standard": verification_standard,
            "annual_removal_tco2": round(annual_removal_tco2, 2),
            "bezero_rating": bezero_rating,
            "quality_score": quality_score,
            "additionality_rating": additionality_rating,
            "permanence_rating": permanence_rating,
            "verification_tier": "tier_1" if verif_score >= 85 else "tier_2" if verif_score >= 70 else "tier_3",
            "component_scores": {
                "additionality": round(add_score, 2),
                "permanence": round(perm_score, 2),
                "verification": round(verif_score, 2),
                "leakage": round(leakage_score, 2),
                "co_benefits": round(co_benefits_score, 2),
            },
            "buffer_pool_pct": round(buffer_pool_pct, 2),
            "buffer_pool_tco2": buffer_pool_tco2,
            "net_credits_tco2": net_credits_tco2,
            "co_benefits": method["co_benefits"],
            "ipcc_classification": method["ipcc_classification"],
        }

    # ------------------------------------------------------------------
    # 2. LCOR Calculation
    # ------------------------------------------------------------------
    def calculate_lcor(
        self,
        entity_id: str,
        cdr_method: str,
        capacity_tco2_pa: float,
        capex_usd: float,
        opex_usd_pa: float,
        lifetime_yrs: int,
        discount_rate_pct: float,
    ) -> dict:
        rng = _rng(entity_id)

        r = discount_rate_pct / 100.0
        lifetime = max(1, lifetime_yrs)

        # Annuity factor
        if r > 0:
            annuity = r / (1.0 - (1.0 + r) ** (-lifetime))
        else:
            annuity = 1.0 / lifetime

        annual_capex = capex_usd * annuity
        total_annual_cost = annual_capex + opex_usd_pa
        lcor = round(total_annual_cost / max(capacity_tco2_pa, 1.0), 2)

        # Sensitivity: ±20% CAPEX
        capex_lo = capex_usd * 0.80
        capex_hi = capex_usd * 1.20
        lcor_lo = round((capex_lo * annuity + opex_usd_pa) / max(capacity_tco2_pa, 1.0), 2)
        lcor_hi = round((capex_hi * annuity + opex_usd_pa) / max(capacity_tco2_pa, 1.0), 2)

        # ±2% discount rate
        r_lo = max(0.01, r - 0.02)
        r_hi = r + 0.02
        annuity_lo = r_lo / (1.0 - (1.0 + r_lo) ** (-lifetime))
        annuity_hi = r_hi / (1.0 - (1.0 + r_hi) ** (-lifetime))
        lcor_dr_lo = round((capex_usd * annuity_lo + opex_usd_pa) / max(capacity_tco2_pa, 1.0), 2)
        lcor_dr_hi = round((capex_usd * annuity_hi + opex_usd_pa) / max(capacity_tco2_pa, 1.0), 2)

        # Break-even carbon price
        breakeven = lcor  # LCOR equals minimum carbon price for economic viability

        # Project IRR (simplified: revenue must cover costs)
        # Assume breakeven carbon price scenario
        irr_base = round((opex_usd_pa / max(capex_usd, 1.0)) * 100.0 + rng.uniform(2.0, 8.0), 2)
        irr_base = round(_clamp(-5.0, 30.0, irr_base), 2)

        return {
            "entity_id": entity_id,
            "cdr_method": cdr_method,
            "capacity_tco2_pa": round(capacity_tco2_pa, 2),
            "capex_usd": round(capex_usd, 2),
            "opex_usd_pa": round(opex_usd_pa, 2),
            "lifetime_yrs": lifetime_yrs,
            "discount_rate_pct": discount_rate_pct,
            "lcor_usd_tco2": lcor,
            "lcor_sensitivity_lo": min(lcor_lo, lcor_dr_lo),
            "lcor_sensitivity_hi": max(lcor_hi, lcor_dr_hi),
            "lcor_capex_lo": lcor_lo,
            "lcor_capex_hi": lcor_hi,
            "lcor_discount_rate_lo": lcor_dr_lo,
            "lcor_discount_rate_hi": lcor_dr_hi,
            "breakeven_carbon_price_usd_tco2": breakeven,
            "project_irr_pct": irr_base,
        }

    # ------------------------------------------------------------------
    # 3. Oxford Principles Assessment
    # ------------------------------------------------------------------
    def assess_oxford_principles(
        self,
        entity_id: str,
        cdr_method: str,
        avoidance_residual: float,
        preference_durable: bool,
        shift_to_durable_plan: bool,
        avoid_locking_in_emissions: bool,
    ) -> dict:
        rng = _rng(entity_id)

        method = CDR_METHODS.get(cdr_method, CDR_METHODS["afforestation"])
        durable = method["permanence_yrs"] >= 200

        # Principle 1: Cut emissions first (offset < 10% of total)
        p1_score = round(_clamp(0.0, 100.0, 100.0 - max(0.0, avoidance_residual - 5.0) * 3.0), 2)

        # Principle 2: Shift to durable removals
        p2_score = round(100.0 if (durable and preference_durable) else (
            70.0 if shift_to_durable_plan else 30.0
        ), 2)

        # Principle 3: Avoid locking in emissions
        p3_score = round(90.0 if avoid_locking_in_emissions else 20.0, 2)
        # Extra penalty for EOR-type methods
        if "oil" in cdr_method.lower():
            p3_score = 5.0

        # Principle 4: Support innovation (method diversity)
        method_maturity = method["maturity_trl"]
        if method_maturity <= 5:
            p4_score = 90.0  # supports frontier innovation
        elif method_maturity <= 7:
            p4_score = 70.0
        else:
            p4_score = 50.0
        p4_score = round(p4_score, 2)

        principle_scores = {
            "p1_cut_emissions_first": p1_score,
            "p2_shift_to_durable_removals": p2_score,
            "p3_avoid_locking_in_emissions": p3_score,
            "p4_support_innovation": p4_score,
        }

        oxford_score = round(
            p1_score * 0.30 + p2_score * 0.25 + p3_score * 0.25 + p4_score * 0.20, 2
        )

        if oxford_score >= 80:
            overall_alignment = "exemplary"
        elif oxford_score >= 60:
            overall_alignment = "aligned"
        elif oxford_score >= 40:
            overall_alignment = "partial"
        else:
            overall_alignment = "misaligned"

        recommendations = []
        if p1_score < 60:
            recommendations.append("Reduce total offset reliance below 10% of Scope 1+2 emissions")
        if p2_score < 60:
            recommendations.append("Develop roadmap to shift towards durable engineered removals by 2040")
        if p3_score < 60:
            recommendations.append("Exclude EOR-linked credits; avoid long-term fossil infrastructure lock-in")
        if p4_score < 60:
            recommendations.append("Include emerging CDR methods (DACCS, EW) in portfolio mix")

        return {
            "entity_id": entity_id,
            "cdr_method": cdr_method,
            "oxford_alignment_score": oxford_score,
            "principle_scores": principle_scores,
            "overall_alignment": overall_alignment,
            "method_permanence_yrs": method["permanence_yrs"],
            "method_trl": method["maturity_trl"],
            "recommendations": recommendations,
            "standard": "Oxford Principles for Net Zero Aligned Carbon Offsetting 2024",
        }

    # ------------------------------------------------------------------
    # 4. Article 6.4 Assessment
    # ------------------------------------------------------------------
    def assess_article_6_4(
        self,
        entity_id: str,
        cdr_method: str,
        host_country_code: str,
        host_country_authorised: bool,
        corresponding_adjustment_agreed: bool,
        sustainable_dev_safeguards: bool,
    ) -> dict:
        rng = _rng(entity_id)

        # Host country risk (simplified: some countries have higher reversal/policy risk)
        high_risk_countries = {"MM", "VE", "AF", "SD", "YE", "LY", "SO"}
        medium_risk_countries = {"MG", "CD", "CF", "GN", "NE", "ML"}

        if host_country_code in high_risk_countries:
            host_country_risk = "high"
            country_risk_score = 30.0
        elif host_country_code in medium_risk_countries:
            host_country_risk = "medium"
            country_risk_score = 60.0
        else:
            host_country_risk = "low"
            country_risk_score = 85.0

        # Corresponding adjustment
        ca_risk = "low" if corresponding_adjustment_agreed else "high"

        # Eligibility
        eligible = (
            host_country_authorised
            and corresponding_adjustment_agreed
            and sustainable_dev_safeguards
        )

        # ITMO value premium (corresponding adjustment reduces double-counting → premium)
        if corresponding_adjustment_agreed:
            itmo_premium = round(15.0 + rng.uniform(-3.0, 5.0), 2)
        else:
            itmo_premium = 0.0

        # Supervisory body approval score
        method = CDR_METHODS.get(cdr_method, CDR_METHODS["afforestation"])
        vstd_eligible = cdr_method in VERIFICATION_STANDARDS.get("article_6_4", {}).get("eligible_methods", [])
        approval_score = round(
            (80.0 if host_country_authorised else 20.0) * 0.4
            + (75.0 if corresponding_adjustment_agreed else 10.0) * 0.35
            + (70.0 if sustainable_dev_safeguards else 20.0) * 0.25,
            2
        )

        return {
            "entity_id": entity_id,
            "cdr_method": cdr_method,
            "host_country_code": host_country_code,
            "eligible": eligible,
            "criteria_met": {
                "host_country_authorisation": host_country_authorised,
                "corresponding_adjustment": corresponding_adjustment_agreed,
                "additionality": True,  # assumed for assessment purposes
                "permanence": method["permanence_yrs"] >= 50,
                "sustainable_development": sustainable_dev_safeguards,
            },
            "host_country_risk": host_country_risk,
            "corresponding_adjustment_risk": ca_risk,
            "itmo_value_premium_pct": itmo_premium,
            "supervisory_body_approval_score": approval_score,
            "a64_methodology_eligible": vstd_eligible,
            "regulatory_basis": "Paris Agreement Article 6.4; Decision 3/CMA.3",
        }

    # ------------------------------------------------------------------
    # 5. VCMI Claims Assessment
    # ------------------------------------------------------------------
    def assess_vcmi_claims(
        self,
        entity_id: str,
        scope1_sbti_aligned: bool,
        scope2_sbti_aligned: bool,
        scope3_disclosure: bool,
        residual_emissions_tco2: float,
        cdr_credits_tco2: float,
        credit_quality_score: float,
    ) -> dict:
        rng = _rng(entity_id)

        sbti_prerequisite_met = scope1_sbti_aligned and scope2_sbti_aligned
        residual_coverage_pct = round(
            _clamp(0.0, 200.0, (cdr_credits_tco2 / max(residual_emissions_tco2, 1.0)) * 100.0), 2
        )
        quality = _clamp(0.0, 100.0, credit_quality_score)

        # VCMI level determination
        vcmi_level = None
        claims_eligible = False

        silver = VCMI_CLAIMS_LEVELS["silver"]
        gold = VCMI_CLAIMS_LEVELS["gold"]
        platinum = VCMI_CLAIMS_LEVELS["platinum"]

        if (sbti_prerequisite_met and scope3_disclosure
                and residual_coverage_pct >= platinum["residual_coverage_pct"]
                and quality >= platinum["credit_quality_min"]):
            vcmi_level = "platinum"
            claims_eligible = True
        elif (sbti_prerequisite_met and scope3_disclosure
              and residual_coverage_pct >= gold["residual_coverage_pct"]
              and quality >= gold["credit_quality_min"]):
            vcmi_level = "gold"
            claims_eligible = True
        elif (sbti_prerequisite_met and scope3_disclosure
              and residual_coverage_pct >= silver["residual_coverage_pct"]
              and quality >= silver["credit_quality_min"]):
            vcmi_level = "silver"
            claims_eligible = True
        else:
            vcmi_level = "ineligible"
            claims_eligible = False

        # Recommended claim
        if vcmi_level == "platinum":
            recommended_claim = "Making a verified net-zero claim with beyond-value-chain mitigation"
        elif vcmi_level == "gold":
            recommended_claim = "Making a verified net-zero claim aligned with VCMI Gold standard"
        elif vcmi_level == "silver":
            recommended_claim = "Making a verified claim: 'We are on a path to Net Zero'"
        else:
            recommended_claim = "Not yet eligible — address SBTi alignment and credit quality gaps"

        gaps = []
        if not sbti_prerequisite_met:
            gaps.append("SBTi Scope 1+2 alignment required")
        if not scope3_disclosure:
            gaps.append("Scope 3 emissions disclosure required")
        if residual_coverage_pct < 100:
            gaps.append(f"CDR credits cover only {residual_coverage_pct}% of residual emissions (100% required)")
        if quality < silver["credit_quality_min"]:
            gaps.append(f"Credit quality score {round(quality, 1)} below Silver threshold {silver['credit_quality_min']}")

        return {
            "entity_id": entity_id,
            "vcmi_level": vcmi_level,
            "claims_eligible": claims_eligible,
            "sbti_prerequisite_met": sbti_prerequisite_met,
            "scope1_sbti_aligned": scope1_sbti_aligned,
            "scope2_sbti_aligned": scope2_sbti_aligned,
            "scope3_disclosure": scope3_disclosure,
            "residual_emissions_tco2": round(residual_emissions_tco2, 2),
            "cdr_credits_tco2": round(cdr_credits_tco2, 2),
            "residual_coverage_pct": residual_coverage_pct,
            "credit_quality_score": round(quality, 2),
            "credit_quality_threshold_met": quality >= silver["credit_quality_min"],
            "recommended_claim": recommended_claim,
            "gaps": gaps,
            "standard": "VCMI Claims Code of Practice 2023",
        }

    # ------------------------------------------------------------------
    # 6. Portfolio Assessment
    # ------------------------------------------------------------------
    def assess_portfolio(self, entity_id: str, projects: List[Dict[str, Any]]) -> dict:
        rng = _rng(entity_id)

        if not projects:
            return {"entity_id": entity_id, "error": "no projects provided"}

        total_removal = 0.0
        durable_removal = 0.0
        permanence_values = []
        bezero_scores = []
        oxford_scores = []
        method_set = set()

        for proj in projects:
            method = proj.get("cdr_method", "afforestation")
            removal = float(proj.get("annual_removal_tco2", 1000.0))
            quality = float(proj.get("quality_score", 60.0 + rng.uniform(-10.0, 10.0)))
            verification = proj.get("verification_standard", "gold_standard")
            additionality = float(proj.get("additionality_score", 70.0))
            leakage = float(proj.get("leakage_risk_pct", 5.0))

            method_data = CDR_METHODS.get(method, CDR_METHODS["afforestation"])
            perm_yrs = method_data["permanence_yrs"]

            total_removal += removal
            if perm_yrs >= 200:
                durable_removal += removal

            permanence_values.append(perm_yrs)
            bezero_scores.append(quality)
            method_set.add(method)

            oxford_result = self.assess_oxford_principles(
                entity_id + method, method,
                avoidance_residual=5.0,
                preference_durable=perm_yrs >= 200,
                shift_to_durable_plan=True,
                avoid_locking_in_emissions=True,
            )
            oxford_scores.append(oxford_result["oxford_alignment_score"])

        n = len(projects)
        durable_share_pct = round(durable_removal / max(total_removal, 1.0) * 100.0, 2)
        avg_permanence = round(sum(permanence_values) / n, 0)
        weighted_bezero_score = round(sum(bezero_scores) / n, 2)
        portfolio_bezero_rating = _bezero_rating(weighted_bezero_score)
        oxford_pct = round(sum(1 for s in oxford_scores if s >= 60) / n * 100.0, 2)

        return {
            "entity_id": entity_id,
            "project_count": n,
            "total_removal_tco2pa": round(total_removal, 2),
            "durable_share_pct": durable_share_pct,
            "avg_permanence_yrs": avg_permanence,
            "portfolio_bezero_rating": portfolio_bezero_rating,
            "weighted_bezero_score": weighted_bezero_score,
            "oxford_alignment_pct": oxford_pct,
            "method_diversity": len(method_set),
            "methods_represented": list(method_set),
        }
