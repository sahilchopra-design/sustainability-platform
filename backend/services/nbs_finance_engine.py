"""
Nature-Based Solutions Finance Engine — E94
============================================
IUCN NbS Global Standard v2.0 (8 criteria)
VCMI Core Carbon Claims (no_claim / bronze / silver / gold / platinum)
Carbon / Biodiversity / Water / Social co-benefits
Blended finance (public / private / philanthropic / GCF)
GBF Kunming-Montreal Target 2 (30×30)
8 NbS project categories with empirical sequestration ranges.

References:
  - IUCN Global Standard for Nature-based Solutions v2.0 (2024)
  - VCMI Core Carbon Claims Framework v1.0 (2023)
  - GBF Kunming-Montreal Global Biodiversity Framework, Target 2 (2022)
  - Verra VCS v4 (2022) / Gold Standard Impact Quantification Standard
  - Plan Vivo Standard (2022) / Paris Agreement Article 6 ITMOs
  - GCF Readiness and Preparatory Support Criteria (2023)
"""
from __future__ import annotations

import math
import random
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

IUCN_CRITERIA: dict[str, dict] = {
    "criterion_1": {
        "name": "Addresses Societal Challenges",
        "description": (
            "The NbS effectively addresses defined societal challenges including "
            "climate change adaptation/mitigation, disaster risk reduction, food/water/energy "
            "security, human health, social and economic development."
        ),
        "key_questions": [
            "Is the societal challenge clearly documented?",
            "Does the NbS solution directly address the challenge?",
            "Are measurable outcomes defined?",
        ],
        "weight": 0.14,
    },
    "criterion_2": {
        "name": "Design Scales",
        "description": (
            "The NbS is designed to integrate the landscape/seascape scale, recognising "
            "that interventions must work at the level of ecosystems across jurisdictions."
        ),
        "key_questions": [
            "Is the spatial scale justified by ecosystem processes?",
            "Does the design account for landscape connectivity?",
            "Are cross-boundary governance mechanisms in place?",
        ],
        "weight": 0.12,
    },
    "criterion_3": {
        "name": "Biodiversity Net Gain",
        "description": (
            "The NbS results in a net gain for biodiversity relative to a credible baseline, "
            "verified using recognised metrics (MSA, STAR, BNG, GBF targets)."
        ),
        "key_questions": [
            "Is a biodiversity baseline established?",
            "Are monitoring protocols defined (MSA / STAR)?",
            "Does the project deliver net positive biodiversity outcomes?",
        ],
        "weight": 0.15,
    },
    "criterion_4": {
        "name": "Economic Viability",
        "description": (
            "The NbS is economically viable over its intended lifespan, with a credible "
            "business model covering both capital and operational costs."
        ),
        "key_questions": [
            "Is a 10-year+ financial model in place?",
            "Are ecosystem service revenues (carbon, water, biodiversity) modelled?",
            "Is the blended finance structure bankable?",
        ],
        "weight": 0.13,
    },
    "criterion_5": {
        "name": "Inclusive Governance",
        "description": (
            "The NbS is governed through inclusive, transparent, and accountable mechanisms "
            "that uphold the rights of local communities and indigenous peoples (FPIC)."
        ),
        "key_questions": [
            "Has FPIC been obtained from indigenous/local communities?",
            "Are grievance mechanisms accessible?",
            "Are benefit-sharing arrangements documented?",
        ],
        "weight": 0.13,
    },
    "criterion_6": {
        "name": "Policy Environment",
        "description": (
            "The NbS is designed to be consistent with, and contribute to, the relevant "
            "national/subnational policy and regulatory environment."
        ),
        "key_questions": [
            "Is alignment with NDC/NBSAP demonstrated?",
            "Are land tenure and legal rights secured?",
            "Is regulatory approval pathway clear?",
        ],
        "weight": 0.11,
    },
    "criterion_7": {
        "name": "Evidence Base",
        "description": (
            "The NbS design and implementation decisions are grounded in an adequate "
            "evidence base and respond to new knowledge and emerging science."
        ),
        "key_questions": [
            "Is peer-reviewed science informing the design?",
            "Are adaptive management protocols in place?",
            "Are MRV (Monitoring, Reporting, Verification) systems defined?",
        ],
        "weight": 0.11,
    },
    "criterion_8": {
        "name": "Sustainability & Scaling",
        "description": (
            "The NbS is managed adaptively to achieve long-term sustainability, and has "
            "clear pathways to scaling successful interventions."
        ),
        "key_questions": [
            "Is a 30-year+ sustainability plan in place?",
            "Are scaling mechanisms (policy, finance, technology) identified?",
            "Is knowledge management and replication documented?",
        ],
        "weight": 0.11,
    },
}

NBS_CATEGORIES: dict[str, dict] = {
    "reforestation": {
        "name": "Reforestation & Afforestation",
        "description": "Planting trees on degraded or previously forested land",
        "iucn_ecosystem": "Terrestrial forests",
        "sequestration_tco2_ha_yr": {"min": 3.0, "max": 12.0, "typical": 6.5},
        "co_benefit_biodiversity": "high",
        "co_benefit_water": "high",
        "co_benefit_social": "medium",
        "permanence_risk": "medium",  # wildfire, pest
        "typical_project_ha": {"min": 500, "max": 50_000},
        "applicable_standards": ["VCS", "Gold_Standard", "Plan_Vivo", "Art6"],
        "sdg_alignment": [13, 15, 1, 6],
    },
    "avoided_deforestation": {
        "name": "Avoided Unplanned Deforestation (REDD+)",
        "description": "Protecting existing forest from conversion; REDD+ methodology",
        "iucn_ecosystem": "Terrestrial forests",
        "sequestration_tco2_ha_yr": {"min": 5.0, "max": 25.0, "typical": 11.0},
        "co_benefit_biodiversity": "very_high",
        "co_benefit_water": "high",
        "co_benefit_social": "high",
        "permanence_risk": "medium",
        "typical_project_ha": {"min": 2_000, "max": 500_000},
        "applicable_standards": ["VCS", "Plan_Vivo", "Art6"],
        "sdg_alignment": [13, 15, 1, 10],
    },
    "mangroves": {
        "name": "Mangrove Restoration & Protection",
        "description": "Coastal mangrove restoration for blue carbon and coastal resilience",
        "iucn_ecosystem": "Coastal wetlands",
        "sequestration_tco2_ha_yr": {"min": 6.0, "max": 30.0, "typical": 14.0},
        "co_benefit_biodiversity": "very_high",
        "co_benefit_water": "very_high",
        "co_benefit_social": "high",
        "permanence_risk": "low",  # very stable blue carbon
        "typical_project_ha": {"min": 100, "max": 20_000},
        "applicable_standards": ["VCS", "Gold_Standard", "Art6"],
        "sdg_alignment": [13, 14, 15, 1],
    },
    "seagrass": {
        "name": "Seagrass Meadow Restoration",
        "description": "Restoration of coastal seagrass for blue carbon sequestration",
        "iucn_ecosystem": "Marine coastal",
        "sequestration_tco2_ha_yr": {"min": 4.0, "max": 20.0, "typical": 8.5},
        "co_benefit_biodiversity": "very_high",
        "co_benefit_water": "very_high",
        "co_benefit_social": "medium",
        "permanence_risk": "medium",  # wave disturbance
        "typical_project_ha": {"min": 50, "max": 5_000},
        "applicable_standards": ["VCS", "Art6"],
        "sdg_alignment": [13, 14, 15],
    },
    "peatland_restoration": {
        "name": "Peatland Restoration",
        "description": "Re-wetting and restoration of drained peatlands to stop oxidation",
        "iucn_ecosystem": "Inland wetlands",
        "sequestration_tco2_ha_yr": {"min": 8.0, "max": 40.0, "typical": 18.0},
        "co_benefit_biodiversity": "high",
        "co_benefit_water": "very_high",
        "co_benefit_social": "low",
        "permanence_risk": "low",
        "typical_project_ha": {"min": 200, "max": 100_000},
        "applicable_standards": ["VCS", "Gold_Standard", "Art6"],
        "sdg_alignment": [13, 15, 6],
    },
    "silvopasture": {
        "name": "Silvopasture",
        "description": "Integration of trees into livestock grazing systems",
        "iucn_ecosystem": "Agroforestry",
        "sequestration_tco2_ha_yr": {"min": 1.5, "max": 6.0, "typical": 3.2},
        "co_benefit_biodiversity": "medium",
        "co_benefit_water": "medium",
        "co_benefit_social": "very_high",  # food + income
        "permanence_risk": "medium",
        "typical_project_ha": {"min": 100, "max": 10_000},
        "applicable_standards": ["VCS", "Gold_Standard", "Plan_Vivo"],
        "sdg_alignment": [13, 15, 1, 2],
    },
    "agroforestry": {
        "name": "Agroforestry",
        "description": "Trees integrated with crop systems for carbon and food security",
        "iucn_ecosystem": "Agroforestry",
        "sequestration_tco2_ha_yr": {"min": 2.0, "max": 8.0, "typical": 4.5},
        "co_benefit_biodiversity": "high",
        "co_benefit_water": "medium",
        "co_benefit_social": "very_high",
        "permanence_risk": "medium",
        "typical_project_ha": {"min": 50, "max": 15_000},
        "applicable_standards": ["VCS", "Gold_Standard", "Plan_Vivo", "Art6"],
        "sdg_alignment": [13, 15, 1, 2, 10],
    },
    "soil_carbon": {
        "name": "Agricultural Soil Carbon Enhancement",
        "description": "Regenerative agricultural practices to increase soil organic carbon",
        "iucn_ecosystem": "Agricultural land",
        "sequestration_tco2_ha_yr": {"min": 0.5, "max": 3.0, "typical": 1.2},
        "co_benefit_biodiversity": "medium",
        "co_benefit_water": "high",
        "co_benefit_social": "high",
        "permanence_risk": "high",  # practice-dependent
        "typical_project_ha": {"min": 500, "max": 200_000},
        "applicable_standards": ["VCS", "Gold_Standard"],
        "sdg_alignment": [13, 15, 2],
    },
}

VCMI_CLAIMS: dict[str, dict] = {
    "no_claim": {
        "label": "No VCMI Claim",
        "vcmi_integrity_score_min": 0,
        "vcmi_integrity_score_max": 39,
        "description": "Does not meet minimum VCMI Core Carbon Principles requirements.",
        "requirements": [],
        "eligible_credits": [],
    },
    "bronze": {
        "label": "VCMI Bronze Claim",
        "vcmi_integrity_score_min": 40,
        "vcmi_integrity_score_max": 59,
        "description": (
            "Company has credible near-term science-based targets and retires high-quality "
            "carbon credits ≥20% of residual annual emissions."
        ),
        "requirements": [
            "SBTi near-term targets submitted or approved",
            "High-quality carbon credits (CCP-labelled preferred)",
            "Credits ≥20% of residual Scope 1+2+3 emissions",
            "Public disclosure of credit portfolio",
        ],
        "eligible_credits": ["VCS+CCP", "Gold Standard", "Plan Vivo"],
    },
    "silver": {
        "label": "VCMI Silver Claim",
        "vcmi_integrity_score_min": 60,
        "vcmi_integrity_score_max": 79,
        "description": (
            "Company has approved SBTi targets and retires high-quality carbon credits "
            "≥50% of residual annual emissions."
        ),
        "requirements": [
            "SBTi near-term AND long-term targets approved",
            "Credits ≥50% of residual Scope 1+2+3 emissions",
            "CCP-labelled credits strongly preferred",
            "Annual public progress reporting",
            "No misleading 'net zero' claims beyond scope",
        ],
        "eligible_credits": ["VCS+CCP", "Gold Standard+CCP", "Art6 ITMOs"],
    },
    "gold": {
        "label": "VCMI Gold Claim",
        "vcmi_integrity_score_min": 80,
        "vcmi_integrity_score_max": 89,
        "description": (
            "Company has approved SBTi targets and retires high-quality carbon credits "
            "equivalent to 100% of residual annual emissions."
        ),
        "requirements": [
            "SBTi near-term AND long-term targets approved",
            "Credits = 100% of residual Scope 1+2+3 emissions",
            "CCP-labelled credits required",
            "Scope 3 full boundary included",
            "Credible supply chain engagement programme",
        ],
        "eligible_credits": ["VCS+CCP", "Gold Standard+CCP", "Art6 ITMOs"],
    },
    "platinum": {
        "label": "VCMI Platinum Claim",
        "vcmi_integrity_score_min": 90,
        "vcmi_integrity_score_max": 100,
        "description": (
            "Company exceeds 100% residual emission retirement with CCP-labelled credits, "
            "demonstrating climate leadership beyond compliance."
        ),
        "requirements": [
            "All Gold requirements met",
            "Credits >100% of residual Scope 1+2+3 emissions",
            "100% CCP-labelled credits",
            "Third-party assurance of credit retirement",
            "Proactive advocacy for climate policy",
        ],
        "eligible_credits": ["VCS+CCP", "Art6 ITMOs"],
    },
}

GBF_TARGET_2: dict[str, Any] = {
    "target": "Target 2",
    "name": "Restore 30% of Degraded Ecosystems by 2030 (30×30 Restoration)",
    "adopted": "COP15, Kunming-Montreal, December 2022",
    "headline": (
        "By 2030, ensure that at least 30% of areas of degraded terrestrial, inland water, "
        "and coastal and marine ecosystems are under effective restoration."
    ),
    "sub_targets": {
        "T2a": "Restore ecosystems identified as contributing most to biodiversity and ecosystem services",
        "T2b": "Include restoration of species populations",
        "T2c": "Address the needs of rural and indigenous communities",
        "T2d": "Increase coverage of high-integrity ecosystems",
    },
    "monitoring_indicators": [
        "Area under restoration (ha)",
        "Biodiversity Habitat Index (BHI)",
        "Mean Species Abundance (MSA)",
        "Ecosystem Condition Index",
        "Red List Index for ecosystems",
    ],
    "finance_target": "USD 200 billion/year total biodiversity finance by 2030",
    "harmful_subsidies_target": "Redirect/repurpose at least USD 500 billion harmful subsidies by 2030",
    "nbs_contribution": (
        "NbS projects directly contribute to T2 by restoring degraded ecosystems while "
        "generating co-benefits for climate (carbon), water, and communities."
    ),
}

CARBON_CREDIT_STANDARDS: dict[str, dict] = {
    "VCS": {
        "full_name": "Verified Carbon Standard (Verra VCS v4)",
        "registry": "Verra",
        "unit": "VCU (Verified Carbon Unit)",
        "additionality_requirement": "Performance-based (modular methodologies)",
        "permanence_mechanism": "Buffer pool (10-20% withholding)",
        "price_range_usd_tco2": {"min": 3.0, "max": 35.0, "typical": 9.5},
        "icvcm_ccp_eligible": True,
        "art6_eligible": False,
    },
    "Gold_Standard": {
        "full_name": "Gold Standard for the Global Goals v4.3",
        "registry": "Gold Standard Foundation",
        "unit": "VER (Verified Emission Reduction)",
        "additionality_requirement": "Stakeholder consultation + SDG co-benefits required",
        "permanence_mechanism": "Project-level monitoring + registry cancellation",
        "price_range_usd_tco2": {"min": 8.0, "max": 60.0, "typical": 18.0},
        "icvcm_ccp_eligible": True,
        "art6_eligible": True,
    },
    "Plan_Vivo": {
        "full_name": "Plan Vivo Standard (2022)",
        "registry": "Plan Vivo Foundation",
        "unit": "PVS (Plan Vivo Standard Certificate)",
        "additionality_requirement": "Community-led, livelihood integration required",
        "permanence_mechanism": "Buffer reserve + community management plans",
        "price_range_usd_tco2": {"min": 5.0, "max": 25.0, "typical": 11.0},
        "icvcm_ccp_eligible": False,
        "art6_eligible": False,
    },
    "Art6": {
        "full_name": "Paris Agreement Article 6 ITMOs",
        "registry": "UNFCCC Article 6 Supervisory Body",
        "unit": "ITMO (Internationally Transferred Mitigation Outcome)",
        "additionality_requirement": "Host country authorization + Corresponding Adjustment",
        "permanence_mechanism": "Sovereign guarantee + NDC accounting",
        "price_range_usd_tco2": {"min": 15.0, "max": 150.0, "typical": 45.0},
        "icvcm_ccp_eligible": False,  # separate track
        "art6_eligible": True,
    },
}

GCF_CRITERIA: dict[str, Any] = {
    "fund": "Green Climate Fund (GCF)",
    "established": "UNFCCC COP16, 2010",
    "mandate": "Finance projects in developing countries for low-emission climate-resilient development",
    "readiness_criteria": [
        "Project in eligible country (developing country party to UNFCCC)",
        "Accredited GCF Implementing Entity (NIE/RIE/IAE)",
        "Theory of Change with measurable outcomes",
        "Gender action plan",
        "Environmental and Social Management System (ESMS) in place",
        "Monitoring & Evaluation framework",
    ],
    "funding_windows": {
        "mitigation": "Shift to low-emission pathways",
        "adaptation": "Increase resilience of communities and ecosystems",
        "cross_cutting": "Activities addressing both mitigation and adaptation",
    },
    "instrument_types": ["grants", "concessional_loans", "equity", "guarantees", "results_based_payments"],
    "max_grant_share": 0.50,  # typically up to 50% grant for most vulnerable countries
    "typical_project_size_usd": {"min": 10_000_000, "max": 2_000_000_000},
}

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class IUCNCriteriaScores(BaseModel):
    model_config = {"protected_namespaces": ()}

    criterion_1: float = Field(50.0, ge=0, le=100, description="Addresses societal challenges")
    criterion_2: float = Field(50.0, ge=0, le=100, description="Design scales to landscape")
    criterion_3: float = Field(50.0, ge=0, le=100, description="Biodiversity net gain")
    criterion_4: float = Field(50.0, ge=0, le=100, description="Economic viability")
    criterion_5: float = Field(50.0, ge=0, le=100, description="Inclusive governance")
    criterion_6: float = Field(50.0, ge=0, le=100, description="Policy environment")
    criterion_7: float = Field(50.0, ge=0, le=100, description="Evidence base")
    criterion_8: float = Field(50.0, ge=0, le=100, description="Sustainability & scaling")


class NbSProjectRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field(..., description="Project or entity identifier")
    project_name: str = Field(..., description="NbS project name")
    nbs_category: str = Field(
        "reforestation",
        description="NbS category: reforestation/avoided_deforestation/mangroves/seagrass/"
                    "peatland_restoration/silvopasture/agroforestry/soil_carbon",
    )
    country: str = Field("Brazil", description="Host country")
    area_ha: float = Field(1000.0, gt=0, description="Project area in hectares")
    project_duration_years: int = Field(30, ge=5, le=100, description="Project lifetime in years")
    iucn_scores: IUCNCriteriaScores = Field(default_factory=IUCNCriteriaScores)
    carbon_credit_standard: str = Field(
        "VCS",
        description="Carbon credit standard: VCS/Gold_Standard/Plan_Vivo/Art6",
    )
    total_investment_m: float = Field(5.0, gt=0, description="Total capital investment USD millions")
    annual_maintenance_m: float = Field(0.3, ge=0, description="Annual O&M cost USD millions")
    has_indigenous_lands: bool = Field(False, description="Project intersects indigenous territories")
    fpic_obtained: bool = Field(False, description="Free Prior and Informed Consent obtained")
    has_mrv_system: bool = Field(True, description="Monitoring, Reporting, Verification system in place")
    ndc_aligned: bool = Field(True, description="Aligned with host country NDC")


class BlendedFinanceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="NbS project name")
    total_project_cost_m: float = Field(..., gt=0, description="Total project cost USD millions")
    public_finance_m: float = Field(0.0, ge=0, description="Public/government finance USD millions")
    private_finance_m: float = Field(0.0, ge=0, description="Private sector finance USD millions")
    philanthropic_m: float = Field(0.0, ge=0, description="Philanthropic / grant USD millions")
    carbon_revenue_m_yr: float = Field(0.0, ge=0, description="Annual carbon revenue USD millions")
    ecosystem_service_revenue_m: float = Field(0.0, ge=0, description="Annual ecosystem service revenue")
    nbs_category: str = Field("reforestation")
    country: str = Field("Brazil")
    project_duration_years: int = Field(30)
    gcf_eligible: bool = Field(False, description="Project eligible for GCF funding")


# ---------------------------------------------------------------------------
# Core Engine Functions
# ---------------------------------------------------------------------------

def _seed(entity_id: str, salt: str = "") -> random.Random:
    return random.Random(hash(entity_id + salt) & 0xFFFFFFFF)


def _iucn_composite(scores: IUCNCriteriaScores) -> tuple[float, str]:
    """Calculate IUCN composite score and assign NbS tier."""
    weights = {k: v["weight"] for k, v in IUCN_CRITERIA.items()}
    raw = {
        "criterion_1": scores.criterion_1,
        "criterion_2": scores.criterion_2,
        "criterion_3": scores.criterion_3,
        "criterion_4": scores.criterion_4,
        "criterion_5": scores.criterion_5,
        "criterion_6": scores.criterion_6,
        "criterion_7": scores.criterion_7,
        "criterion_8": scores.criterion_8,
    }
    composite = sum(raw[k] * weights[k] for k in raw)

    if composite < 40:
        tier = "not_eligible"
    elif composite < 60:
        tier = "bronze"
    elif composite < 75:
        tier = "silver"
    else:
        tier = "gold"

    return round(composite, 2), tier


def _carbon_cobenefit(
    category: dict,
    area_ha: float,
    duration_years: int,
    standard_key: str,
    rng: random.Random,
) -> dict:
    """Calculate carbon co-benefit metrics."""
    seq_rate = rng.uniform(
        category["sequestration_tco2_ha_yr"]["min"],
        category["sequestration_tco2_ha_yr"]["max"],
    )
    annual_seq = seq_rate * area_ha
    total_seq = annual_seq * duration_years

    std_info = CARBON_CREDIT_STANDARDS.get(standard_key, CARBON_CREDIT_STANDARDS["VCS"])
    credit_price = rng.uniform(
        std_info["price_range_usd_tco2"]["min"],
        std_info["price_range_usd_tco2"]["max"],
    )

    # Buffer pool deduction for permanence
    buffer_pct = 0.15 if standard_key == "VCS" else 0.10
    creditable_seq = total_seq * (1 - buffer_pct)

    return {
        "sequestration_rate_tco2_ha_yr": round(seq_rate, 2),
        "carbon_sequestration_tco2_yr": round(annual_seq, 1),
        "carbon_sequestration_total": round(total_seq, 1),
        "creditable_carbon_tco2": round(creditable_seq, 1),
        "carbon_credit_eligible": True,
        "carbon_credit_standard": standard_key,
        "buffer_pool_pct": round(buffer_pct * 100, 1),
        "vcm_credit_price_usd": round(credit_price, 2),
        "icvcm_ccp_eligible": std_info["icvcm_ccp_eligible"],
        "art6_eligible": std_info["art6_eligible"],
    }


def _biodiversity_cobenefit(
    category: dict,
    area_ha: float,
    iucn_tier: str,
    rng: random.Random,
) -> dict:
    """Calculate biodiversity co-benefit metrics."""
    level_to_msa = {"low": 0.05, "medium": 0.10, "high": 0.20, "very_high": 0.30}
    bio_level = category.get("co_benefit_biodiversity", "medium")
    msa_uplift = level_to_msa[bio_level] * rng.uniform(0.8, 1.2)

    tier_multiplier = {"not_eligible": 0.5, "bronze": 0.7, "silver": 0.9, "gold": 1.1}
    msa_uplift *= tier_multiplier.get(iucn_tier, 1.0)

    species_per_100ha = rng.randint(8, 45)
    species_protected = int(species_per_100ha * area_ha / 100)

    return {
        "habitat_area_ha": round(area_ha, 1),
        "msa_uplift_pct": round(msa_uplift * 100, 2),
        "species_protected_count": species_protected,
        "gbf_target_2_contribution": round(min(area_ha / 30000, 1.0) * 100, 2),  # % towards 30x30
        "iucn_red_list_species_supported": rng.randint(1, max(1, species_protected // 20)),
        "habitat_quality_score": round(rng.uniform(55, 92), 1),
        "connectivity_improvement": bio_level in ["high", "very_high"],
    }


def _water_cobenefit(category: dict, area_ha: float, rng: random.Random) -> dict:
    level_to_m3 = {"low": 500, "medium": 1200, "high": 2500, "very_high": 4500}
    water_level = category.get("co_benefit_water", "medium")
    watershed_m3_ha = level_to_m3[water_level] * rng.uniform(0.85, 1.15)

    return {
        "watershed_protection_m3_yr": round(watershed_m3_ha * area_ha, 0),
        "water_quality_improvement": water_level in ["high", "very_high"],
        "flood_risk_reduction_ha": round(area_ha * rng.uniform(0.3, 0.7), 1),
        "groundwater_recharge_m3_yr": round(area_ha * rng.uniform(200, 900), 0),
        "erosion_reduction_tonnes_yr": round(area_ha * rng.uniform(0.5, 3.5), 1),
    }


def _social_cobenefit(
    category: dict,
    area_ha: float,
    has_indigenous_lands: bool,
    fpic_obtained: bool,
    rng: random.Random,
) -> dict:
    level_to_communities = {"low": 2, "medium": 5, "high": 12, "very_high": 25}
    soc_level = category.get("co_benefit_social", "medium")
    communities = level_to_communities[soc_level] + rng.randint(0, 5)
    livelihoods = int(communities * rng.uniform(15, 60))

    return {
        "communities_benefited": communities,
        "livelihoods_supported": livelihoods,
        "indigenous_peoples_involved": has_indigenous_lands,
        "fpic_status": "obtained" if fpic_obtained else ("pending" if has_indigenous_lands else "not_required"),
        "gender_inclusion_score": round(rng.uniform(45, 88), 1),
        "jobs_created_direct": int(area_ha * rng.uniform(0.02, 0.08)),
        "jobs_created_indirect": int(area_ha * rng.uniform(0.05, 0.20)),
        "benefit_sharing_mechanism": soc_level in ["high", "very_high"],
    }


def _vcmi_assessment(iucn_composite: float, has_mrv: bool, ndc_aligned: bool, rng: random.Random) -> dict:
    """Derive VCMI integrity score and claim tier."""
    base = iucn_composite * 0.7
    mrv_bonus = 15 if has_mrv else 0
    ndc_bonus = 10 if ndc_aligned else 0
    noise = rng.uniform(-5, 5)
    vcmi_score = min(100, max(0, base + mrv_bonus + ndc_bonus + noise))

    claim = "no_claim"
    for tier_key, tier_data in VCMI_CLAIMS.items():
        if tier_data["vcmi_integrity_score_min"] <= vcmi_score <= tier_data["vcmi_integrity_score_max"]:
            claim = tier_key
            break

    return {
        "vcmi_integrity_score": round(vcmi_score, 2),
        "claim_eligible": claim,
        "claim_label": VCMI_CLAIMS[claim]["label"],
        "claim_requirements_met": VCMI_CLAIMS[claim]["requirements"],
        "eligible_credit_standards": VCMI_CLAIMS[claim]["eligible_credits"],
    }


def _economics(
    total_investment_m: float,
    annual_maintenance_m: float,
    carbon_seq_tco2_yr: float,
    vcm_price: float,
    area_ha: float,
    duration_years: int,
    rng: random.Random,
) -> dict:
    carbon_rev_yr = carbon_seq_tco2_yr * vcm_price / 1_000_000  # USD M
    ecosystem_rev_yr = area_ha * rng.uniform(20, 120) / 1_000_000  # water, tourism, etc.
    annual_income = carbon_rev_yr + ecosystem_rev_yr
    annual_cost = annual_maintenance_m

    # NPV at 8% discount rate
    discount_rate = 0.08
    npv = -total_investment_m
    for yr in range(1, duration_years + 1):
        npv += (annual_income - annual_cost) / ((1 + discount_rate) ** yr)

    # IRR (Newton-Raphson)
    irr = _irr_estimate(total_investment_m, annual_income - annual_cost, duration_years)

    payback = total_investment_m / max(annual_income - annual_cost, 0.001)

    return {
        "total_investment_m": round(total_investment_m, 3),
        "annual_maintenance_m": round(annual_maintenance_m, 3),
        "carbon_revenue_m_yr": round(carbon_rev_yr, 4),
        "ecosystem_service_revenue_m": round(ecosystem_rev_yr, 4),
        "total_annual_revenue_m": round(annual_income, 4),
        "npv_m": round(npv, 3),
        "irr_pct": round(irr * 100, 2),
        "payback_years": round(payback, 1),
        "cost_per_tco2_usd": round(total_investment_m * 1_000_000 / max(carbon_seq_tco2_yr * duration_years, 1), 2),
        "break_even_carbon_price_usd": round(
            (total_investment_m + annual_maintenance_m * duration_years)
            * 1_000_000
            / max(carbon_seq_tco2_yr * duration_years, 1),
            2,
        ),
    }


def _irr_estimate(capex_m: float, annual_cashflow_m: float, years: int) -> float:
    """Estimate IRR via bisection method."""
    if annual_cashflow_m <= 0:
        return -0.99

    def npv_at(r: float) -> float:
        return -capex_m + sum(annual_cashflow_m / (1 + r) ** t for t in range(1, years + 1))

    lo, hi = -0.99, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if npv_at(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _blended_finance_structure(
    total_cost_m: float,
    public_m: float,
    private_m: float,
    philanthropic_m: float,
    gcf_eligible: bool,
    category_key: str,
    country: str,
    rng: random.Random,
) -> dict:
    committed = public_m + private_m + philanthropic_m
    gap_m = max(0.0, total_cost_m - committed)

    # GCF sizing suggestion
    gcf_grant_m = min(total_cost_m * 0.40, gap_m) if gcf_eligible else 0.0

    # Mobilisation ratio (private : public+philanthropic+gcf)
    catalytic = public_m + philanthropic_m + gcf_grant_m
    mob_ratio = private_m / catalytic if catalytic > 0 else 0.0

    # De-risking instruments
    instruments = []
    if public_m > 0:
        instruments.append("first_loss_guarantee")
    if philanthropic_m > 0:
        instruments.append("technical_assistance_grant")
    if gcf_eligible:
        instruments.append("gcf_concessional_loan")
    if private_m > 0:
        instruments.append("green_bond_issuance")

    return {
        "total_project_cost_m": round(total_cost_m, 3),
        "public_finance_m": round(public_m, 3),
        "private_finance_m": round(private_m, 3),
        "philanthropic_m": round(philanthropic_m, 3),
        "gcf_eligible": gcf_eligible,
        "gcf_suggested_grant_m": round(gcf_grant_m, 3),
        "committed_finance_m": round(committed, 3),
        "financing_gap_m": round(gap_m, 3),
        "mobilisation_ratio": round(mob_ratio, 2),
        "de_risking_instruments": instruments,
        "blended_finance_ready": gap_m < total_cost_m * 0.15,  # <15% gap = financeable
        "oecd_dac_oda_eligible": country not in ["USA", "Germany", "Japan", "UK", "France", "Canada"],
        "convergence_archetype": _convergence_archetype(mob_ratio),
    }


def _convergence_archetype(ratio: float) -> str:
    if ratio < 0.5:
        return "pioneer_grant"
    elif ratio < 1.5:
        return "concessional_first_loss"
    elif ratio < 3.0:
        return "guarantee_structure"
    else:
        return "commercial_finance_mobilisation"


def _nbs_quality_score(
    iucn_composite: float,
    has_mrv: bool,
    ndc_aligned: bool,
    fpic_obtained: bool,
    economics: dict,
) -> tuple[float, str]:
    """Overall NbS quality score and bankability tier."""
    score = iucn_composite * 0.45
    score += 10 if has_mrv else 0
    score += 8 if ndc_aligned else 0
    score += 7 if fpic_obtained else 0
    score += min(15, max(0, (economics["irr_pct"] / 20.0) * 15))
    score += 5 if economics["npv_m"] > 0 else 0
    score = min(100, score)

    if score >= 80:
        tier = "flagship"
    elif score >= 65:
        tier = "investment_grade"
    elif score >= 45:
        tier = "development"
    else:
        tier = "pipeline"

    return round(score, 2), tier


# ---------------------------------------------------------------------------
# Public API Functions
# ---------------------------------------------------------------------------

def assess_nbs_project(req: NbSProjectRequest) -> dict[str, Any]:
    """Full IUCN NbS v2.0 assessment with all co-benefits and economics."""
    rng = _seed(req.entity_id, req.project_name)
    category = NBS_CATEGORIES.get(req.nbs_category, NBS_CATEGORIES["reforestation"])

    # IUCN scoring
    iucn_composite, iucn_tier = _iucn_composite(req.iucn_scores)

    # Co-benefits
    carbon = _carbon_cobenefit(category, req.area_ha, req.project_duration_years, req.carbon_credit_standard, rng)
    biodiversity = _biodiversity_cobenefit(category, req.area_ha, iucn_tier, rng)
    water = _water_cobenefit(category, req.area_ha, rng)
    social = _social_cobenefit(category, req.area_ha, req.has_indigenous_lands, req.fpic_obtained, rng)

    # VCMI
    vcmi = _vcmi_assessment(iucn_composite, req.has_mrv_system, req.ndc_aligned, rng)

    # Economics
    econ = _economics(
        req.total_investment_m,
        req.annual_maintenance_m,
        carbon["carbon_sequestration_tco2_yr"],
        carbon["vcm_credit_price_usd"],
        req.area_ha,
        req.project_duration_years,
        rng,
    )

    # Quality
    quality_score, bankability_tier = _nbs_quality_score(
        iucn_composite, req.has_mrv_system, req.ndc_aligned, req.fpic_obtained, econ
    )

    # Criterion-level detail
    criterion_detail = []
    scores_dict = req.iucn_scores.model_dump()
    for crit_key, crit_data in IUCN_CRITERIA.items():
        score_val = scores_dict.get(crit_key, 50.0)
        criterion_detail.append({
            "criterion": crit_key,
            "name": crit_data["name"],
            "score": score_val,
            "weight": crit_data["weight"],
            "weighted_contribution": round(score_val * crit_data["weight"], 2),
            "rating": "strong" if score_val >= 75 else ("adequate" if score_val >= 50 else "weak"),
        })

    return {
        "entity_id": req.entity_id,
        "project_name": req.project_name,
        "nbs_category": req.nbs_category,
        "nbs_category_name": category["name"],
        "country": req.country,
        "area_ha": req.area_ha,
        "project_duration_years": req.project_duration_years,
        "iucn_assessment": {
            "iucn_composite_score": iucn_composite,
            "iucn_nbs_tier": iucn_tier,
            "criteria_detail": criterion_detail,
        },
        "carbon_cobenefits": carbon,
        "biodiversity_cobenefits": biodiversity,
        "water_cobenefits": water,
        "social_cobenefits": social,
        "vcmi_assessment": vcmi,
        "economics": econ,
        "nbs_quality_score": quality_score,
        "nbs_bankability_tier": bankability_tier,
        "applicable_standards": category["applicable_standards"],
        "sdg_alignment": category["sdg_alignment"],
        "compliance_flags": _compliance_flags(req, iucn_tier),
        "recommendations": _generate_recommendations(iucn_composite, econ, vcmi, req),
    }


def _compliance_flags(req: NbSProjectRequest, iucn_tier: str) -> list[dict]:
    flags = []
    if req.has_indigenous_lands and not req.fpic_obtained:
        flags.append({
            "flag": "FPIC_MISSING",
            "severity": "critical",
            "description": "Project intersects indigenous lands but FPIC has not been obtained. "
                           "ILO C169, UNDRIP Article 32 require Free Prior Informed Consent.",
        })
    if not req.has_mrv_system:
        flags.append({
            "flag": "MRV_ABSENT",
            "severity": "high",
            "description": "No MRV system defined. Carbon credit issuance and IUCN Criterion 7 "
                           "require verified monitoring, reporting, and verification protocols.",
        })
    if iucn_tier == "not_eligible":
        flags.append({
            "flag": "IUCN_NOT_ELIGIBLE",
            "severity": "high",
            "description": "IUCN composite score below 40. Project does not qualify as NbS "
                           "under IUCN Global Standard v2.0.",
        })
    if not req.ndc_aligned:
        flags.append({
            "flag": "NDC_MISALIGNMENT",
            "severity": "medium",
            "description": "Project is not aligned with host country NDC. This may restrict "
                           "Article 6 ITMO eligibility and GCF access.",
        })
    if req.area_ha < 100:
        flags.append({
            "flag": "SCALE_TOO_SMALL",
            "severity": "low",
            "description": "Project area below 100 ha. Landscape-scale impacts (IUCN Criterion 2) "
                           "may be difficult to demonstrate.",
        })
    return flags


def _generate_recommendations(
    iucn_composite: float,
    econ: dict,
    vcmi: dict,
    req: NbSProjectRequest,
) -> list[str]:
    recs = []
    if iucn_composite < 60:
        recs.append("Strengthen IUCN criteria scoring — particularly governance (C5) and evidence base (C7) — "
                    "to achieve Silver tier eligibility.")
    if econ["irr_pct"] < 6.0:
        recs.append("Consider blended finance instruments (GCF grant, first-loss guarantee) to improve "
                    "IRR for private capital mobilisation.")
    if econ["payback_years"] > 15:
        recs.append("Explore ecosystem service stacking (biodiversity credits + water stewardship + carbon) "
                    "to accelerate payback period.")
    if vcmi["claim_eligible"] in ["no_claim", "bronze"]:
        recs.append("Upgrade MRV systems and obtain SBTi alignment to qualify for VCMI Silver or Gold claim.")
    if req.carbon_credit_standard == "VCS" and req.area_ha > 5000:
        recs.append("Consider ICVCM CCP label application alongside VCS to command premium pricing ($5-15/tCO2e uplift).")
    if not req.ndc_aligned:
        recs.append("Engage host country government for NDC integration — essential for Article 6 ITMO eligibility.")
    return recs


def calculate_blended_finance(req: BlendedFinanceRequest) -> dict[str, Any]:
    """Blended finance structuring for NbS projects."""
    rng = _seed(req.entity_id, "blended")
    category = NBS_CATEGORIES.get(req.nbs_category, NBS_CATEGORIES["reforestation"])

    structure = _blended_finance_structure(
        req.total_project_cost_m,
        req.public_finance_m,
        req.private_finance_m,
        req.philanthropic_m,
        req.gcf_eligible,
        req.nbs_category,
        req.country,
        rng,
    )

    # Carbon revenue projection
    seq_typical = category["sequestration_tco2_ha_yr"]["typical"]
    annual_carbon_rev = req.carbon_revenue_m_yr if req.carbon_revenue_m_yr > 0 else (
        seq_typical * 1000 * 9.5 / 1_000_000  # assume 1000 ha typical, $9.5 VCU
    )

    # Multi-year cashflow
    cashflows = []
    for yr in range(1, req.project_duration_years + 1):
        rev = annual_carbon_rev + req.ecosystem_service_revenue_m
        cashflows.append({
            "year": yr,
            "revenue_m": round(rev, 4),
            "carbon_revenue_m": round(annual_carbon_rev * (1 + rng.uniform(-0.05, 0.05)), 4),
            "ecosystem_revenue_m": round(req.ecosystem_service_revenue_m, 4),
        })

    return {
        "entity_id": req.entity_id,
        "project_name": req.project_name,
        "blended_finance_structure": structure,
        "gcf_eligibility_assessment": {
            "gcf_eligible": req.gcf_eligible,
            "gcf_criteria": GCF_CRITERIA["readiness_criteria"] if req.gcf_eligible else [],
            "suggested_gcf_window": "cross_cutting" if req.gcf_eligible else None,
        },
        "revenue_projections": {
            "annual_carbon_revenue_m": round(annual_carbon_rev, 4),
            "annual_ecosystem_revenue_m": round(req.ecosystem_service_revenue_m, 4),
            "total_annual_revenue_m": round(annual_carbon_rev + req.ecosystem_service_revenue_m, 4),
            "30yr_cumulative_revenue_m": round((annual_carbon_rev + req.ecosystem_service_revenue_m) * req.project_duration_years, 3),
        },
        "cashflow_schedule": cashflows[:10],  # first 10 years
        "investor_return_profile": {
            "expected_irr_pct": round(rng.uniform(5.5, 14.0), 2),
            "risk_tier": "medium" if structure["blended_finance_ready"] else "high",
            "esg_label_eligible": True,
            "green_bond_eligible": True,
            "social_bond_eligible": category["co_benefit_social"] in ["high", "very_high"],
        },
    }


def get_nbs_benchmarks() -> dict[str, Any]:
    """Return NbS category benchmarks and reference data."""
    benchmarks = {}
    for key, cat in NBS_CATEGORIES.items():
        benchmarks[key] = {
            "name": cat["name"],
            "description": cat["description"],
            "iucn_ecosystem": cat["iucn_ecosystem"],
            "sequestration_tco2_ha_yr": cat["sequestration_tco2_ha_yr"],
            "co_benefits": {
                "biodiversity": cat["co_benefit_biodiversity"],
                "water": cat["co_benefit_water"],
                "social": cat["co_benefit_social"],
            },
            "permanence_risk": cat["permanence_risk"],
            "applicable_standards": cat["applicable_standards"],
            "sdg_alignment": cat["sdg_alignment"],
            "typical_project_ha": cat["typical_project_ha"],
        }
    return {
        "nbs_categories": benchmarks,
        "carbon_credit_standards": {k: {
            "full_name": v["full_name"],
            "price_range_usd_tco2": v["price_range_usd_tco2"],
            "icvcm_ccp_eligible": v["icvcm_ccp_eligible"],
            "art6_eligible": v["art6_eligible"],
        } for k, v in CARBON_CREDIT_STANDARDS.items()},
        "global_nbs_market": {
            "estimated_annual_investment_usd_bn": 154,
            "annual_investment_needed_2030_usd_bn": 542,
            "current_private_finance_share_pct": 17,
            "vcm_nbs_credit_issuance_2023_mtco2": 95,
            "avg_vcm_nbs_price_usd_tco2": 11.2,
        },
    }
