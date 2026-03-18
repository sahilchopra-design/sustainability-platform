"""
Carbon Removal & CDR Finance Engine (E90)
==========================================
Comprehensive assessment engine for Carbon Dioxide Removal (CDR) project finance,
quality scoring, and market eligibility under IPCC AR6, Oxford CDR Principles,
Paris Agreement Article 6.4, and voluntary/compliance carbon markets.

Sub-modules:
  1. CDR Technology Assessment — TRL, cost trajectory, co-benefits, scalability
  2. Oxford CDR Principles Scoring — Additionality, permanence, MRV, no-harm
  3. Article 6.4 Eligibility Assessment — ITMO eligibility, corresponding adjustment
  4. CDR Economics — LCOE, NPV/IRR, break-even price, blended finance modelling
  5. Market Eligibility — CORSIA, Frontier AMC, voluntary, corporate buyer matching
  6. Full Assessment — composite cdr_quality_score, tier, market recommendations

References:
  - IPCC AR6 WG3 Ch.12 — CDR modalities and scale
  - Oxford Principles for Net Zero Aligned Carbon Offsetting (2023 update)
  - Paris Agreement Article 6.4 Supervisory Body rules (2024)
  - CORSIA Eligible Emissions Units criteria (ICAO Doc 10148, Ed.3)
  - Frontier Advance Market Commitment eligibility criteria (2023)
  - ICVCM Core Carbon Principles v2 (2023)
  - Verra VCS Standard v4.4 — Removals methodology requirements
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — CDR Technology Profiles (IPCC AR6 WG3 Ch.12)
# ---------------------------------------------------------------------------

CDR_TECHNOLOGY_PROFILES: dict[str, dict] = {
    "beccs": {
        "name": "Bioenergy with Carbon Capture and Storage",
        "ipcc_category": "technological",
        "trl_level": 6,
        "cost_usd_tco2_current": 100,
        "cost_usd_tco2_2030": 80,
        "cost_usd_tco2_2050": 60,
        "permanence_years": 10000,
        "co_benefits": ["bioenergy_generation", "rural_employment", "energy_security"],
        "risks": ["land_use_change", "water_stress", "food_security_competition", "biodiversity_loss"],
        "scalability_rating": "moderate",
        "land_use_ha_per_mtco2": 0.4,
        "water_use_m3_per_tco2": 3.5,
        "description": "Combustion or fermentation of biomass with CO2 capture and geological storage",
        "ipcc_ar6_potential_gtco2yr": 0.5,
        "corsia_eligible": False,
        "article_64_pathway": "eligible_with_conditions",
    },
    "dacs": {
        "name": "Direct Air Carbon Capture and Storage",
        "ipcc_category": "technological",
        "trl_level": 7,
        "cost_usd_tco2_current": 400,
        "cost_usd_tco2_2030": 200,
        "cost_usd_tco2_2050": 100,
        "permanence_years": 10000,
        "co_benefits": ["technology_learning", "modular_deployment", "no_land_competition"],
        "risks": ["high_energy_requirement", "water_consumption", "cost_uncertainty"],
        "scalability_rating": "moderate",
        "land_use_ha_per_mtco2": 0.001,
        "water_use_m3_per_tco2": 1.2,
        "description": "Mechanical/chemical systems that capture CO2 directly from ambient air",
        "ipcc_ar6_potential_gtco2yr": 0.1,
        "corsia_eligible": False,
        "article_64_pathway": "eligible_with_conditions",
    },
    "enhanced_weathering": {
        "name": "Enhanced Rock Weathering",
        "ipcc_category": "geochemical",
        "trl_level": 4,
        "cost_usd_tco2_current": 80,
        "cost_usd_tco2_2030": 55,
        "cost_usd_tco2_2050": 35,
        "permanence_years": 100000,
        "co_benefits": ["soil_health_improvement", "crop_yield_uplift", "reduced_fertiliser_need"],
        "risks": ["mrv_uncertainty", "heavy_metal_leaching", "logistics_grinding_energy"],
        "scalability_rating": "high",
        "land_use_ha_per_mtco2": 0.15,
        "water_use_m3_per_tco2": 0.1,
        "description": "Application of crushed silicate rock to agricultural land to accelerate natural weathering",
        "ipcc_ar6_potential_gtco2yr": 2.0,
        "corsia_eligible": False,
        "article_64_pathway": "under_development",
    },
    "blue_carbon": {
        "name": "Blue Carbon (Mangrove/Seagrass/Saltmarsh)",
        "ipcc_category": "biological",
        "trl_level": 8,
        "cost_usd_tco2_current": 15,
        "cost_usd_tco2_2030": 12,
        "cost_usd_tco2_2050": 10,
        "permanence_years": 50,
        "co_benefits": ["coastal_protection", "fishery_habitat", "biodiversity_uplift", "community_livelihoods"],
        "risks": ["sea_level_rise_reversal", "hydrology_alteration", "limited_global_scale"],
        "scalability_rating": "limited",
        "land_use_ha_per_mtco2": 5.0,
        "water_use_m3_per_tco2": 0.0,
        "description": "Conservation and restoration of coastal and marine ecosystems for carbon sequestration",
        "ipcc_ar6_potential_gtco2yr": 0.5,
        "corsia_eligible": True,
        "article_64_pathway": "eligible",
    },
    "biochar": {
        "name": "Biochar",
        "ipcc_category": "biological",
        "trl_level": 8,
        "cost_usd_tco2_current": 60,
        "cost_usd_tco2_2030": 45,
        "cost_usd_tco2_2050": 30,
        "permanence_years": 1000,
        "co_benefits": ["soil_fertility", "reduced_n2o_emissions", "waste_biomass_utilisation"],
        "risks": ["feedstock_availability", "land_use_competition", "heavy_metal_contamination"],
        "scalability_rating": "high",
        "land_use_ha_per_mtco2": 0.05,
        "water_use_m3_per_tco2": 0.2,
        "description": "Pyrolysis of organic biomass to produce stable charcoal applied to soil",
        "ipcc_ar6_potential_gtco2yr": 3.0,
        "corsia_eligible": False,
        "article_64_pathway": "eligible",
    },
    "afforestation_reforestation": {
        "name": "Afforestation & Reforestation",
        "ipcc_category": "biological",
        "trl_level": 9,
        "cost_usd_tco2_current": 5,
        "cost_usd_tco2_2030": 5,
        "cost_usd_tco2_2050": 6,
        "permanence_years": 30,
        "co_benefits": ["biodiversity_habitat", "watershed_protection", "local_livelihoods", "soil_conservation"],
        "risks": ["fire_drought_reversal", "monoculture_risk", "albedo_effect", "limited_permanence"],
        "scalability_rating": "high",
        "land_use_ha_per_mtco2": 1.0,
        "water_use_m3_per_tco2": 2.0,
        "description": "Planting trees on non-forested or previously forested land for carbon sequestration",
        "ipcc_ar6_potential_gtco2yr": 3.9,
        "corsia_eligible": True,
        "article_64_pathway": "eligible",
    },
    "soil_carbon": {
        "name": "Soil Carbon Sequestration",
        "ipcc_category": "biological",
        "trl_level": 7,
        "cost_usd_tco2_current": 10,
        "cost_usd_tco2_2030": 8,
        "cost_usd_tco2_2050": 7,
        "permanence_years": 20,
        "co_benefits": ["food_security", "drought_resilience", "reduced_synthetic_fertiliser"],
        "risks": ["reversal_risk", "mrv_complexity", "tillage_change_permanence"],
        "scalability_rating": "very_high",
        "land_use_ha_per_mtco2": 0.8,
        "water_use_m3_per_tco2": 0.3,
        "description": "Agricultural management practices that increase organic carbon stocks in soil",
        "ipcc_ar6_potential_gtco2yr": 5.0,
        "corsia_eligible": False,
        "article_64_pathway": "eligible_with_conditions",
    },
    "ocean_alkalinity_enhancement": {
        "name": "Ocean Alkalinity Enhancement",
        "ipcc_category": "geochemical",
        "trl_level": 3,
        "cost_usd_tco2_current": 150,
        "cost_usd_tco2_2030": 100,
        "cost_usd_tco2_2050": 60,
        "permanence_years": 100000,
        "co_benefits": ["ocean_acidification_reversal", "marine_ecosystem_support"],
        "risks": ["ecological_disruption", "mrv_immaturity", "governance_uncertainty", "heavy_metal_release"],
        "scalability_rating": "high",
        "land_use_ha_per_mtco2": 0.0,
        "water_use_m3_per_tco2": 0.0,
        "description": "Addition of alkaline minerals to seawater to accelerate ocean CO2 absorption",
        "ipcc_ar6_potential_gtco2yr": 1.0,
        "corsia_eligible": False,
        "article_64_pathway": "under_development",
    },
}


# ---------------------------------------------------------------------------
# Oxford CDR Principles (2023 update)
# ---------------------------------------------------------------------------

OXFORD_CDR_PRINCIPLES: dict[str, dict] = {
    "additionality": {
        "description": "Carbon removal would not have occurred without the carbon credit incentive",
        "sub_criteria": [
            "financial_additionality",
            "regulatory_additionality",
            "common_practice_test",
            "baseline_conservativeness",
        ],
        "scoring_guidance": (
            "Score 0-25. Award full 25 for projects meeting all 4 sub-criteria with independent "
            "verification. Deduct 6.25 per unmet criterion. Partial credit for documented rationale."
        ),
        "weight": 0.30,
        "max_score": 25,
    },
    "permanence": {
        "description": "Carbon storage is durable and protected from reversal over relevant time horizons",
        "sub_criteria": [
            "physical_permanence_>100yr",
            "buffer_pool_or_insurance",
            "reversal_monitoring_protocol",
            "liability_chain_post_transfer",
        ],
        "scoring_guidance": (
            "Score 0-25. Geological storage scores full marks. Biological storage scored on "
            "permanence_years: >=1000yr=20, >=100yr=15, >=30yr=10, <30yr=5. Buffer pool adds 3. "
            "Monitored reversal protocol adds 2."
        ),
        "weight": 0.30,
        "max_score": 25,
    },
    "monitoring_verification": {
        "description": "Robust measurement, reporting, and verification (MRV) with independent third-party audit",
        "sub_criteria": [
            "quantification_methodology_approved",
            "third_party_verification",
            "digital_monitoring_satellite",
            "registry_issuance_retirement",
        ],
        "scoring_guidance": (
            "Score 0-25. Approved quantification methodology (VCS/CDM/Gold Standard/ICVCM CCP) "
            "scores 10. Third-party ISO 14064-3 verification adds 7. Digital/satellite monitoring adds 5. "
            "Registry tracking adds 3."
        ),
        "weight": 0.25,
        "max_score": 25,
    },
    "no_harm": {
        "description": "Project avoids significant harm to biodiversity, communities, and other SDGs",
        "sub_criteria": [
            "biodiversity_net_positive_or_neutral",
            "free_prior_informed_consent",
            "no_food_security_displacement",
            "water_stress_assessment",
        ],
        "scoring_guidance": (
            "Score 0-25. Each sub-criterion contributes 6.25. Biodiversity net-positive scores full. "
            "FPIC documented adds full mark. No food security displacement adds full. "
            "Water stress assessment completed adds full."
        ),
        "weight": 0.15,
        "max_score": 25,
    },
}


# ---------------------------------------------------------------------------
# Paris Agreement Article 6.4 Eligibility
# ---------------------------------------------------------------------------

ARTICLE_64_ELIGIBILITY: dict[str, dict] = {
    "corresponding_adjustment": {
        "description": (
            "Host country must apply a corresponding adjustment to its NDC for any "
            "ITMO transferred internationally, preventing double counting (Art 6.2)"
        ),
        "required": True,
        "statute_ref": "Paris Agreement Art 6.2 and Decision 2/CMA.3 §3",
    },
    "host_country_approval": {
        "description": (
            "Competent national authority in host country must formally authorise the "
            "activity for participation under Art 6.4 Supervisory Body"
        ),
        "required": True,
        "statute_ref": "Paris Agreement Art 6.4(b) and Supervisory Body Rule 10",
    },
    "suppressed_demand_exclusion": {
        "description": (
            "Activities must not rely on suppressed demand baselines that artificially "
            "inflate removal credits (particularly relevant for LDCs and developing countries)"
        ),
        "required": True,
        "statute_ref": "Decision 3/CMA.3 Annex §22-24 — Baseline methodologies",
    },
    "social_environmental_safeguards": {
        "description": (
            "Activities must apply UNFCCC safeguards: avoid adverse social and "
            "environmental impacts, promote food security, biodiversity conservation, "
            "respect indigenous rights, and manage water resources sustainably"
        ),
        "required": True,
        "statute_ref": "Paris Agreement Art 6.4(e) and Supervisory Body Decision SBM003",
    },
    "monitoring_plan": {
        "description": (
            "Detailed monitoring plan consistent with approved Art 6.4 methodology "
            "must be submitted and approved before activity registration"
        ),
        "required": True,
        "statute_ref": "Supervisory Body Rule 12 and Methodology Requirements §4.3",
    },
    "authorized_party": {
        "description": (
            "Project participants must be designated as authorized parties by the "
            "host country and recognised by the Art 6.4 Supervisory Body registry"
        ),
        "required": True,
        "statute_ref": "Decision 3/CMA.3 §7 — Authorisation of participating parties",
    },
}


# ---------------------------------------------------------------------------
# CDR Market Benchmarks
# ---------------------------------------------------------------------------

CDR_MARKET_BENCHMARKS: dict[str, dict] = {
    "corporate_net_zero": {
        "buyer_description": "Corporates with SBTi net-zero targets using CDR for residual emissions",
        "typical_price_usd": 50,
        "price_range_usd": (15, 200),
        "volume_tco2_yr_2024": 25_000_000,
        "growth_rate_pct": 35,
        "quality_preference": "SBTi Beyond Value Chain Mitigation guidance; permanence >30yr preferred",
        "preferred_cdr_types": ["afforestation_reforestation", "biochar", "soil_carbon", "blue_carbon"],
        "key_frameworks": ["SBTi Corporate Net-Zero Standard", "VCMI Claims Code of Practice"],
    },
    "voluntary_market": {
        "buyer_description": "Voluntary carbon market buyers (diverse; spot and forward purchases)",
        "typical_price_usd": 20,
        "price_range_usd": (5, 100),
        "volume_tco2_yr_2024": 80_000_000,
        "growth_rate_pct": 20,
        "quality_preference": "VCS/Gold Standard certification; ICVCM CCP label increasingly required",
        "preferred_cdr_types": ["afforestation_reforestation", "blue_carbon", "biochar", "soil_carbon"],
        "key_frameworks": ["Verra VCS v4.4", "Gold Standard for the Global Goals", "ICVCM CCP"],
    },
    "CORSIA_airline": {
        "buyer_description": "ICAO CORSIA-obligated airlines offsetting international aviation emissions",
        "typical_price_usd": 12,
        "price_range_usd": (5, 25),
        "volume_tco2_yr_2024": 35_000_000,
        "growth_rate_pct": 60,
        "quality_preference": "CORSIA Eligible Emissions Units (EEUs); TAB-approved programmes only",
        "preferred_cdr_types": ["afforestation_reforestation", "blue_carbon"],
        "key_frameworks": ["ICAO CORSIA Doc 10148 Ed.3", "TAB-approved offset programmes"],
    },
    "government_procurement": {
        "buyer_description": "Government agencies purchasing CDR for national NDC contribution",
        "typical_price_usd": 45,
        "price_range_usd": (20, 150),
        "volume_tco2_yr_2024": 5_000_000,
        "growth_rate_pct": 80,
        "quality_preference": "Art 6.4 ITMOs; high-permanence; co-benefit rich; domestic preference",
        "preferred_cdr_types": ["dacs", "beccs", "enhanced_weathering"],
        "key_frameworks": ["Paris Agreement Art 6.4", "UNFCCC ITMO registry"],
    },
    "Frontier_advance_market": {
        "buyer_description": "Frontier AMC (Stripe/Alphabet/Meta/McKinsey/Shopify) advance purchases",
        "typical_price_usd": 500,
        "price_range_usd": (200, 1000),
        "volume_tco2_yr_2024": 500_000,
        "growth_rate_pct": 150,
        "quality_preference": "Novel, high-durability (>1000yr), scientifically rigorous, cost reduction pathway",
        "preferred_cdr_types": ["dacs", "enhanced_weathering", "ocean_alkalinity_enhancement", "beccs"],
        "key_frameworks": ["Frontier Eligibility Criteria v1.2", "ICVCM CCP (encouraged)"],
    },
    "EU_innovation_fund": {
        "buyer_description": "EU Innovation Fund and ETS-linked carbon removal support mechanisms",
        "typical_price_usd": 75,
        "price_range_usd": (30, 200),
        "volume_tco2_yr_2024": 3_000_000,
        "growth_rate_pct": 100,
        "quality_preference": "EU ETS-linked; CCUS Regulation compliance; Net Zero Industry Act alignment",
        "preferred_cdr_types": ["dacs", "beccs", "enhanced_weathering"],
        "key_frameworks": ["EU Innovation Fund Regulation", "CCUS Regulation (EU) 2024/1610", "Net Zero Industry Act"],
    },
}


# ---------------------------------------------------------------------------
# Frontier Advance Market Commitment Eligibility Criteria
# ---------------------------------------------------------------------------

FRONTIER_ELIGIBILITY_CRITERIA: dict[str, dict] = {
    "novel_technology": {
        "description": "Technology must be novel or pre-commercial; mature natural solutions excluded",
        "threshold": "TRL <= 7 at time of application; not afforestation/reforestation or REDD+",
        "weight": 0.20,
        "evaluation_guidance": (
            "Score 0-20. TRL <=5 scores 20. TRL 6-7 scores 15. TRL 8 scores 5. "
            "Afforestation/reforestation and REDD+ excluded entirely (score 0)."
        ),
    },
    "high_durability": {
        "description": "Carbon storage must be highly durable, ideally geological or mineralised",
        "threshold": "Permanence >= 1000 years for full score; minimum 100 years for eligibility",
        "weight": 0.25,
        "evaluation_guidance": (
            "Score 0-25. Geological/mineralised (>=10000yr) scores 25. "
            ">=1000yr scores 20. >=100yr scores 12. <100yr disqualified."
        ),
    },
    "scalability_pathway": {
        "description": "Credible pathway to gigatonne-scale deployment exists",
        "threshold": "Technical potential >=0.5 GtCO2/yr by 2050 based on IPCC AR6 estimates",
        "weight": 0.20,
        "evaluation_guidance": (
            "Score 0-20. IPCC AR6 technical potential >=1 GtCO2/yr scores 20. "
            ">=0.5 GtCO2/yr scores 15. >=0.1 GtCO2/yr scores 10. <0.1 GtCO2/yr scores 5."
        ),
    },
    "cost_reduction_trajectory": {
        "description": "Demonstrated or modelled cost reduction trajectory toward <$100/tCO2 by 2050",
        "threshold": "Current cost < $500/tCO2; modelled 2050 cost < $100/tCO2; >50% reduction expected",
        "weight": 0.20,
        "evaluation_guidance": (
            "Score 0-20. >70% cost reduction 2024→2050 scores 20. 50-70% scores 15. "
            "30-50% scores 10. <30% scores 5. 2050 cost >$300/tCO2 disqualifies."
        ),
    },
    "scientific_validity": {
        "description": "Scientific evidence base and quantification methodology is peer-reviewed and robust",
        "threshold": "Peer-reviewed publications; approved or under-development quantification methodology",
        "weight": 0.15,
        "evaluation_guidance": (
            "Score 0-15. Approved ICVCM/VCS/CDM methodology scores 15. "
            "Peer-reviewed quantification approach + independent validation scores 10. "
            "Internal methodology only scores 5."
        ),
    },
}


# ---------------------------------------------------------------------------
# Dataclasses for structured results
# ---------------------------------------------------------------------------

@dataclass
class CDRTechnologyResult:
    cdr_type: str
    name: str
    ipcc_category: str
    trl_level: int
    trl_assessment: str
    cost_current_usd_tco2: float
    cost_2030_usd_tco2: float
    cost_2050_usd_tco2: float
    cost_reduction_pct_to_2050: float
    permanence_years: int
    scalability_rating: str
    co_benefit_score: float
    risk_count: int
    risk_flags: list[str]
    co_benefits: list[str]
    land_use_ha_per_mtco2: float
    water_use_m3_per_tco2: float
    technology_readiness_score: float
    notes: list[str]


@dataclass
class OxfordPrinciplesResult:
    additionality_score: float
    permanence_score: float
    monitoring_verification_score: float
    no_harm_score: float
    composite_score: float
    quality_tier: str
    gap_analysis: list[dict]
    strengths: list[str]
    improvement_actions: list[str]


@dataclass
class Article64Result:
    corresponding_adjustment: bool
    host_country_approval: bool
    suppressed_demand_exclusion: bool
    social_environmental_safeguards: bool
    monitoring_plan: bool
    authorized_party: bool
    requirements_met: int
    total_requirements: int
    itmo_eligible: bool
    corresponding_adjustment_required: bool
    host_country_ndc_contribution: str
    eligibility_gaps: list[str]
    eligibility_notes: list[str]


@dataclass
class CDREconomicsResult:
    capex_usd_total: float
    annual_opex_usd: float
    annual_removal_tco2: float
    project_life_years: int
    lcoe_usd_tco2: float
    break_even_price_usd_tco2: float
    npv_at_50_usd: float
    npv_at_100_usd: float
    npv_at_200_usd: float
    irr_at_50_usd_pct: float
    irr_at_100_usd_pct: float
    irr_at_200_usd_pct: float
    blended_finance_uplift_usd: float
    lcoe_with_blended_finance: float
    economics_viability: str
    sensitivity_notes: list[str]


@dataclass
class MarketEligibilityResult:
    corsia_eligible: bool
    corsia_programme: str
    frontier_eligible: bool
    frontier_score: float
    frontier_gap_analysis: list[dict]
    voluntary_market_tier: str
    voluntary_registry: str
    eligible_buyer_types: list[str]
    best_match_buyer: str
    credit_price_benchmark_usd: float
    price_range_usd: tuple
    market_notes: list[str]


@dataclass
class CDRFullAssessmentResult:
    project_id: str
    assessment_date: str
    cdr_type: str
    # Technology
    trl_level: int
    scalability_rating: str
    cost_current_usd_tco2: float
    cost_2050_usd_tco2: float
    # Oxford Principles
    oxford_composite_score: float
    oxford_quality_tier: str
    # Art 6.4
    article_64_eligible: bool
    itmo_eligible: bool
    # Economics
    lcoe_usd_tco2: float
    break_even_price_usd_tco2: float
    irr_at_100_usd_pct: float
    # Market
    frontier_eligible: bool
    corsia_eligible: bool
    best_match_buyer: str
    credit_price_benchmark_usd: float
    # Composite
    cdr_quality_score: float
    cdr_quality_tier: str
    key_strengths: list[str]
    key_risks: list[str]
    recommended_actions: list[str]
    cross_framework: dict


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CarbonRemovalEngine:
    """Carbon Removal and CDR Finance Assessment Engine (E90)."""

    # TRL descriptions per IPCC convention
    _TRL_DESCRIPTIONS = {
        1: "Basic principles observed",
        2: "Technology concept formulated",
        3: "Experimental proof of concept",
        4: "Technology validated in lab",
        5: "Technology validated in relevant environment",
        6: "Technology demonstrated in relevant environment",
        7: "System prototype demonstrated",
        8: "System complete and qualified",
        9: "Actual system proven in operational environment",
    }

    # Oxford quality tiers by composite score
    _OXFORD_TIERS = [
        (80, "gold"),
        (60, "silver"),
        (40, "bronze"),
        (0, "basic"),
    ]

    # CDR quality tiers
    _CDR_QUALITY_TIERS = [
        (80, "gold"),
        (60, "silver"),
        (40, "bronze"),
        (0, "basic"),
    ]

    def assess_cdr_technology(self, project_data: dict) -> CDRTechnologyResult:
        """
        Match project to CDR technology profile, assess TRL, cost trajectory,
        scalability, and co-benefit scoring.
        """
        cdr_type = project_data.get("cdr_type", "").lower().strip()
        profile = CDR_TECHNOLOGY_PROFILES.get(cdr_type)

        if profile is None:
            # Attempt partial match
            for key in CDR_TECHNOLOGY_PROFILES:
                if cdr_type in key or key in cdr_type:
                    cdr_type = key
                    profile = CDR_TECHNOLOGY_PROFILES[key]
                    break

        if profile is None:
            # Default to afforestation as nearest well-understood type
            cdr_type = "afforestation_reforestation"
            profile = CDR_TECHNOLOGY_PROFILES[cdr_type]

        trl = profile["trl_level"]
        trl_desc = self._TRL_DESCRIPTIONS.get(trl, "Unknown TRL")

        # TRL assessment narrative
        if trl >= 8:
            trl_assessment = f"TRL {trl} — Commercially deployed or near-commercial. {trl_desc}."
        elif trl >= 6:
            trl_assessment = f"TRL {trl} — Demonstration stage. {trl_desc}. Near-commercial pathway within 5-10 years."
        elif trl >= 4:
            trl_assessment = f"TRL {trl} — R&D stage. {trl_desc}. Significant scale-up investment required."
        else:
            trl_assessment = f"TRL {trl} — Early research. {trl_desc}. Commercial deployment >10 years away."

        # Cost reduction trajectory
        cost_current = float(project_data.get("cost_usd_tco2_current", profile["cost_usd_tco2_current"]))
        cost_2030 = profile["cost_usd_tco2_2030"]
        cost_2050 = profile["cost_usd_tco2_2050"]
        cost_reduction_pct = ((cost_current - cost_2050) / cost_current * 100) if cost_current > 0 else 0

        # Co-benefit scoring (1 point per co-benefit, max 10)
        co_benefits = profile["co_benefits"]
        co_benefit_score = min(len(co_benefits) * 2.0, 10.0)

        # Risk flags
        risk_flags = []
        provided_risks = project_data.get("identified_risks", [])
        for risk in profile["risks"]:
            if any(r.lower() in risk.lower() or risk.lower() in r.lower() for r in provided_risks) or not provided_risks:
                risk_flags.append(risk)

        # Technology readiness score (0-100)
        trl_score = (trl / 9) * 50
        scalability_map = {"limited": 10, "moderate": 20, "high": 35, "very_high": 50}
        scalability_score = scalability_map.get(profile["scalability_rating"], 15)
        technology_readiness_score = round(trl_score + scalability_score * 0.5 + co_benefit_score * 0.5, 1)

        notes = []
        if cost_reduction_pct > 50:
            notes.append(f"Strong cost reduction trajectory: {cost_reduction_pct:.0f}% decline expected by 2050.")
        if profile["land_use_ha_per_mtco2"] > 1.0:
            notes.append("High land use per MtCO2 removed — land availability may constrain scale.")
        if profile["water_use_m3_per_tco2"] > 2.0:
            notes.append("Significant water consumption — water stress risk assessment required.")

        return CDRTechnologyResult(
            cdr_type=cdr_type,
            name=profile["name"],
            ipcc_category=profile["ipcc_category"],
            trl_level=trl,
            trl_assessment=trl_assessment,
            cost_current_usd_tco2=cost_current,
            cost_2030_usd_tco2=cost_2030,
            cost_2050_usd_tco2=cost_2050,
            cost_reduction_pct_to_2050=round(cost_reduction_pct, 1),
            permanence_years=profile["permanence_years"],
            scalability_rating=profile["scalability_rating"],
            co_benefit_score=co_benefit_score,
            risk_count=len(risk_flags),
            risk_flags=risk_flags,
            co_benefits=co_benefits,
            land_use_ha_per_mtco2=profile["land_use_ha_per_mtco2"],
            water_use_m3_per_tco2=profile["water_use_m3_per_tco2"],
            technology_readiness_score=round(technology_readiness_score, 1),
            notes=notes,
        )

    def score_oxford_principles(self, project_data: dict) -> OxfordPrinciplesResult:
        """
        Score all 4 Oxford CDR Principles. Returns composite 0-100 score,
        quality tier, and gap analysis.
        """
        # --- Additionality (max 25) ---
        add = 0.0
        if project_data.get("financial_additionality_documented", False):
            add += 6.25
        if project_data.get("regulatory_additionality_documented", False):
            add += 6.25
        if project_data.get("common_practice_test_passed", False):
            add += 6.25
        if project_data.get("conservative_baseline_used", False):
            add += 6.25
        # Partial credit for verbal justification
        if add == 0 and project_data.get("additionality_justification", ""):
            add = 6.25

        # --- Permanence (max 25) ---
        cdr_type = project_data.get("cdr_type", "").lower()
        profile = CDR_TECHNOLOGY_PROFILES.get(cdr_type, {})
        perm_years = project_data.get("permanence_years", profile.get("permanence_years", 0))

        if perm_years >= 10000:
            perm = 20.0
        elif perm_years >= 1000:
            perm = 17.0
        elif perm_years >= 100:
            perm = 12.0
        elif perm_years >= 30:
            perm = 8.0
        else:
            perm = 3.0

        if project_data.get("buffer_pool_or_insurance", False):
            perm = min(perm + 3.0, 25.0)
        if project_data.get("reversal_monitoring_protocol", False):
            perm = min(perm + 2.0, 25.0)

        # --- Monitoring & Verification (max 25) ---
        mrv = 0.0
        if project_data.get("approved_quantification_methodology", False):
            mrv += 10.0
        if project_data.get("third_party_verification", False):
            mrv += 7.0
        if project_data.get("digital_satellite_monitoring", False):
            mrv += 5.0
        if project_data.get("registry_issuance", False):
            mrv += 3.0

        # --- No Harm (max 25) ---
        nh = 0.0
        if project_data.get("biodiversity_net_positive", False):
            nh += 6.25
        elif project_data.get("biodiversity_neutral", False):
            nh += 3.0
        if project_data.get("fpic_documented", False):
            nh += 6.25
        if project_data.get("no_food_security_displacement", True):  # default True
            nh += 6.25
        if project_data.get("water_stress_assessment_done", False):
            nh += 6.25

        # Composite (weighted)
        composite = (
            add * OXFORD_CDR_PRINCIPLES["additionality"]["weight"] * 4.0
            + perm * OXFORD_CDR_PRINCIPLES["permanence"]["weight"] * 4.0
            + mrv * OXFORD_CDR_PRINCIPLES["monitoring_verification"]["weight"] * 4.0
            + nh * OXFORD_CDR_PRINCIPLES["no_harm"]["weight"] * 4.0
        )
        composite = round(min(composite, 100.0), 1)

        # Tier
        quality_tier = "basic"
        for threshold, tier in self._OXFORD_TIERS:
            if composite >= threshold:
                quality_tier = tier
                break

        # Gap analysis
        gap_analysis = []
        if add < 18.75:
            gap_analysis.append({
                "principle": "additionality",
                "current_score": round(add, 1),
                "max_score": 25,
                "gap": round(25 - add, 1),
                "action": "Document financial additionality, common practice test, and regulatory additionality with independent verification.",
            })
        if perm < 18.0:
            gap_analysis.append({
                "principle": "permanence",
                "current_score": round(perm, 1),
                "max_score": 25,
                "gap": round(25 - perm, 1),
                "action": "Establish buffer pool insurance or transition to geological storage; implement reversal monitoring protocol.",
            })
        if mrv < 18.75:
            gap_analysis.append({
                "principle": "monitoring_verification",
                "current_score": round(mrv, 1),
                "max_score": 25,
                "gap": round(25 - mrv, 1),
                "action": "Obtain ICVCM CCP-approved methodology; engage ISO 14064-3 accredited third-party verifier; register on Verra/Gold Standard registry.",
            })
        if nh < 18.75:
            gap_analysis.append({
                "principle": "no_harm",
                "current_score": round(nh, 1),
                "max_score": 25,
                "gap": round(25 - nh, 1),
                "action": "Conduct FPIC process with affected communities; commission biodiversity impact assessment; complete water stress ESIA.",
            })

        strengths = []
        if add >= 18.75:
            strengths.append("Strong additionality documentation")
        if perm >= 18.0:
            strengths.append("High permanence / geological or well-buffered storage")
        if mrv >= 18.75:
            strengths.append("Robust MRV system with third-party verification")
        if nh >= 18.75:
            strengths.append("Comprehensive social and environmental safeguards")

        improvement_actions = [g["action"] for g in gap_analysis]

        return OxfordPrinciplesResult(
            additionality_score=round(add, 1),
            permanence_score=round(perm, 1),
            monitoring_verification_score=round(mrv, 1),
            no_harm_score=round(nh, 1),
            composite_score=composite,
            quality_tier=quality_tier,
            gap_analysis=gap_analysis,
            strengths=strengths,
            improvement_actions=improvement_actions,
        )

    def assess_article64_eligibility(self, project_data: dict) -> Article64Result:
        """
        Check all 6 Paris Agreement Article 6.4 requirements.
        Returns ITMO eligibility, corresponding adjustment requirement, and gap analysis.
        """
        checks = {
            "corresponding_adjustment": project_data.get("corresponding_adjustment_agreed", False),
            "host_country_approval": project_data.get("host_country_approval", False),
            "suppressed_demand_exclusion": project_data.get("no_suppressed_demand_baseline", True),
            "social_environmental_safeguards": project_data.get("safeguards_applied", False),
            "monitoring_plan": project_data.get("monitoring_plan_submitted", False),
            "authorized_party": project_data.get("authorized_party_designated", False),
        }

        requirements_met = sum(1 for v in checks.values() if v)
        total_requirements = len(checks)

        # ITMO eligible only if all 6 requirements met
        itmo_eligible = all(checks.values())

        # Corresponding adjustment always required for internationally transferred credits
        international_transfer = project_data.get("international_transfer_intended", True)
        corresponding_adjustment_required = international_transfer

        # Host country NDC contribution narrative
        host_country = project_data.get("host_country", "Unknown")
        if checks["host_country_approval"] and checks["corresponding_adjustment"]:
            ndc_contribution = (
                f"{host_country} NDC: Removal units will be reflected in national GHG inventory "
                f"with corresponding adjustment applied per Decision 2/CMA.3."
            )
        elif checks["host_country_approval"]:
            ndc_contribution = (
                f"{host_country} has approved the activity but corresponding adjustment "
                f"arrangements are not yet formalised."
            )
        else:
            ndc_contribution = (
                f"Host country approval not yet obtained. Cannot confirm NDC contribution pathway."
            )

        eligibility_gaps = []
        for req_key, met in checks.items():
            if not met:
                req_def = ARTICLE_64_ELIGIBILITY[req_key]
                eligibility_gaps.append(
                    f"{req_key}: {req_def['description']} [Ref: {req_def['statute_ref']}]"
                )

        eligibility_notes = []
        if itmo_eligible:
            eligibility_notes.append(
                "Project meets all Art 6.4 requirements. ITMOs may be issued upon Supervisory Body registration."
            )
        else:
            eligibility_notes.append(
                f"Project meets {requirements_met}/{total_requirements} Art 6.4 requirements. "
                f"ITMO issuance blocked until all gaps resolved."
            )
        if project_data.get("cdr_type", "") in ["ocean_alkalinity_enhancement", "enhanced_weathering"]:
            eligibility_notes.append(
                "Technology type is geochemical CDR — Supervisory Body methodology under development. "
                "Art 6.4 registration timeline may be extended by 12-24 months pending methodology approval."
            )

        return Article64Result(
            corresponding_adjustment=checks["corresponding_adjustment"],
            host_country_approval=checks["host_country_approval"],
            suppressed_demand_exclusion=checks["suppressed_demand_exclusion"],
            social_environmental_safeguards=checks["social_environmental_safeguards"],
            monitoring_plan=checks["monitoring_plan"],
            authorized_party=checks["authorized_party"],
            requirements_met=requirements_met,
            total_requirements=total_requirements,
            itmo_eligible=itmo_eligible,
            corresponding_adjustment_required=corresponding_adjustment_required,
            host_country_ndc_contribution=ndc_contribution,
            eligibility_gaps=eligibility_gaps,
            eligibility_notes=eligibility_notes,
        )

    def calculate_cdr_economics(self, project_data: dict) -> CDREconomicsResult:
        """
        Model CAPEX/OPEX, LCOE ($/tCO2), NPV/IRR at credit price scenarios,
        break-even price, and blended finance uplift.
        """
        capex = float(project_data.get("capex_usd", 1_000_000))
        annual_opex = float(project_data.get("annual_opex_usd", 100_000))
        annual_removal = float(project_data.get("annual_removal_tco2", 1_000))
        project_life = int(project_data.get("project_life_years", 20))
        discount_rate = float(project_data.get("discount_rate_pct", 8)) / 100
        blended_finance_grant_pct = float(project_data.get("blended_finance_grant_pct", 0)) / 100

        # If annual_removal is 0, avoid division errors
        if annual_removal <= 0:
            annual_removal = 1.0

        # Annualised capex (straight-line)
        annual_capex = capex / project_life if project_life > 0 else capex

        # LCOE (Levelised Cost of CO2 Removal)
        total_annual_cost = annual_capex + annual_opex
        lcoe = total_annual_cost / annual_removal

        # Apply blended finance uplift (grant reduces effective capex)
        blended_grant = capex * blended_finance_grant_pct
        effective_capex = capex - blended_grant
        lcoe_blended = ((effective_capex / project_life) + annual_opex) / annual_removal if project_life > 0 else lcoe

        # Break-even price (full cost recovery without blended finance)
        break_even = lcoe

        # NPV at three credit price scenarios
        def _npv(credit_price: float) -> float:
            annual_revenue = credit_price * annual_removal
            annual_net_cf = annual_revenue - annual_opex
            # PV of annuity
            if discount_rate > 0:
                pv_annuity = annual_net_cf * (1 - (1 + discount_rate) ** (-project_life)) / discount_rate
            else:
                pv_annuity = annual_net_cf * project_life
            return pv_annuity - capex

        npv_50 = round(_npv(50), 0)
        npv_100 = round(_npv(100), 0)
        npv_200 = round(_npv(200), 0)

        # IRR approximation using Newton's method
        def _irr(credit_price: float) -> float:
            annual_revenue = credit_price * annual_removal
            annual_net_cf = annual_revenue - annual_opex
            if annual_net_cf <= 0:
                return -99.0
            # Binary search for IRR
            low, high = -0.99, 10.0
            for _ in range(100):
                mid = (low + high) / 2
                pv = sum(annual_net_cf / (1 + mid) ** t for t in range(1, project_life + 1))
                if pv > capex:
                    low = mid
                else:
                    high = mid
            return round((low + high) / 2 * 100, 1)

        irr_50 = _irr(50)
        irr_100 = _irr(100)
        irr_200 = _irr(200)

        # Viability assessment
        if npv_100 > 0:
            viability = "economically_viable_at_100usd"
        elif npv_200 > 0:
            viability = "viable_at_premium_markets_only"
        elif irr_200 > 5:
            viability = "marginally_viable_with_blended_finance"
        else:
            viability = "requires_significant_subsidy_or_cost_reduction"

        sensitivity_notes = []
        if break_even > 200:
            sensitivity_notes.append(f"Break-even price ${break_even:.0f}/tCO2 is above most voluntary market benchmarks — Frontier AMC or public finance required.")
        if blended_finance_grant_pct > 0:
            sensitivity_notes.append(f"Blended finance grant of {blended_finance_grant_pct*100:.0f}% reduces LCOE from ${lcoe:.0f} to ${lcoe_blended:.0f}/tCO2.")
        if irr_100 > 15:
            sensitivity_notes.append(f"IRR of {irr_100}% at $100/tCO2 is attractive for institutional investors.")
        if project_life < 10:
            sensitivity_notes.append("Short project life (<10 years) reduces NPV significantly — consider permanence extension protocols.")

        return CDREconomicsResult(
            capex_usd_total=capex,
            annual_opex_usd=annual_opex,
            annual_removal_tco2=annual_removal,
            project_life_years=project_life,
            lcoe_usd_tco2=round(lcoe, 2),
            break_even_price_usd_tco2=round(break_even, 2),
            npv_at_50_usd=npv_50,
            npv_at_100_usd=npv_100,
            npv_at_200_usd=npv_200,
            irr_at_50_usd_pct=irr_50,
            irr_at_100_usd_pct=irr_100,
            irr_at_200_usd_pct=irr_200,
            blended_finance_uplift_usd=round(blended_grant, 0),
            lcoe_with_blended_finance=round(lcoe_blended, 2),
            economics_viability=viability,
            sensitivity_notes=sensitivity_notes,
        )

    def assess_market_eligibility(self, project_data: dict) -> MarketEligibilityResult:
        """
        Assess CORSIA eligibility, Frontier AMC eligibility, voluntary market tier,
        and identify optimal buyer type with credit price benchmark.
        """
        cdr_type = project_data.get("cdr_type", "").lower()
        profile = CDR_TECHNOLOGY_PROFILES.get(cdr_type, {})
        trl = profile.get("trl_level", 5)
        permanence = profile.get("permanence_years", project_data.get("permanence_years", 30))
        ipcc_potential = profile.get("ipcc_ar6_potential_gtco2yr", 0.1)

        # --- CORSIA eligibility ---
        corsia_native = profile.get("corsia_eligible", False)
        corsia_programme_mapping = {
            "afforestation_reforestation": "American Carbon Registry / CAR Forest Project Protocol (TAB-approved)",
            "blue_carbon": "Verra VCS Blue Carbon Programme (TAB-approved)",
        }
        if corsia_native:
            corsia_eligible = True
            corsia_programme = corsia_programme_mapping.get(cdr_type, "CORSIA-eligible programme — programme-level TAB assessment required")
        elif project_data.get("corsia_programme_enrollment", False):
            corsia_eligible = True
            corsia_programme = project_data.get("corsia_programme_name", "Enrolled CORSIA programme")
        else:
            corsia_eligible = False
            corsia_programme = "Not eligible — CDR type not on TAB-approved programme list"

        # --- Frontier eligibility ---
        frontier_scores = {}
        # Novel technology: TRL scoring
        if cdr_type in ["afforestation_reforestation", "blue_carbon", "soil_carbon"]:
            frontier_scores["novel_technology"] = 0  # Mature/natural solutions excluded
        elif trl <= 5:
            frontier_scores["novel_technology"] = 20
        elif trl <= 7:
            frontier_scores["novel_technology"] = 15
        else:
            frontier_scores["novel_technology"] = 5

        # High durability
        if permanence >= 10000:
            frontier_scores["high_durability"] = 25
        elif permanence >= 1000:
            frontier_scores["high_durability"] = 20
        elif permanence >= 100:
            frontier_scores["high_durability"] = 12
        else:
            frontier_scores["high_durability"] = 0  # Disqualified

        # Scalability pathway
        if ipcc_potential >= 1.0:
            frontier_scores["scalability_pathway"] = 20
        elif ipcc_potential >= 0.5:
            frontier_scores["scalability_pathway"] = 15
        elif ipcc_potential >= 0.1:
            frontier_scores["scalability_pathway"] = 10
        else:
            frontier_scores["scalability_pathway"] = 5

        # Cost reduction trajectory
        cost_current = profile.get("cost_usd_tco2_current", 200)
        cost_2050 = profile.get("cost_usd_tco2_2050", 100)
        if cost_current > 0:
            cost_reduction = (cost_current - cost_2050) / cost_current
        else:
            cost_reduction = 0
        if cost_reduction >= 0.70 and cost_2050 < 100:
            frontier_scores["cost_reduction_trajectory"] = 20
        elif cost_reduction >= 0.50:
            frontier_scores["cost_reduction_trajectory"] = 15
        elif cost_reduction >= 0.30:
            frontier_scores["cost_reduction_trajectory"] = 10
        else:
            frontier_scores["cost_reduction_trajectory"] = 5

        # Scientific validity
        if project_data.get("approved_quantification_methodology", False):
            frontier_scores["scientific_validity"] = 15
        elif project_data.get("peer_reviewed_methodology", False):
            frontier_scores["scientific_validity"] = 10
        else:
            frontier_scores["scientific_validity"] = 5

        frontier_score = sum(
            frontier_scores[k] * FRONTIER_ELIGIBILITY_CRITERIA[k]["weight"]
            for k in FRONTIER_ELIGIBILITY_CRITERIA
        ) * 100 / sum(FRONTIER_ELIGIBILITY_CRITERIA[k]["weight"] for k in FRONTIER_ELIGIBILITY_CRITERIA)

        # Frontier eligible if score >=60 AND novel technology score > 0
        frontier_eligible = frontier_score >= 60 and frontier_scores.get("novel_technology", 0) > 0

        frontier_gap_analysis = []
        for criterion, score in frontier_scores.items():
            max_raw = int(FRONTIER_ELIGIBILITY_CRITERIA[criterion]["weight"] * 100)
            if score < max_raw * 0.75:
                frontier_gap_analysis.append({
                    "criterion": criterion,
                    "score": score,
                    "threshold": max_raw,
                    "gap": max_raw - score,
                    "guidance": FRONTIER_ELIGIBILITY_CRITERIA[criterion]["evaluation_guidance"],
                })

        # --- Voluntary market tier ---
        oxford_score = project_data.get("oxford_composite_score", 0)
        if oxford_score >= 80:
            voluntary_tier = "premium"
            voluntary_registry = "ICVCM CCP Label + Verra VCS or Gold Standard"
        elif oxford_score >= 60:
            voluntary_tier = "standard"
            voluntary_registry = "Verra VCS v4.4 or Gold Standard for the Global Goals"
        elif oxford_score >= 40:
            voluntary_tier = "basic"
            voluntary_registry = "Verra VCS or comparable approved standard"
        else:
            voluntary_tier = "pre-market"
            voluntary_registry = "Methodology development stage — not yet market-ready"

        # --- Buyer matching ---
        eligible_buyer_types = []
        if corsia_eligible:
            eligible_buyer_types.append("CORSIA_airline")
        if frontier_eligible:
            eligible_buyer_types.append("Frontier_advance_market")
        if voluntary_tier in ["premium", "standard"]:
            eligible_buyer_types.append("corporate_net_zero")
            eligible_buyer_types.append("voluntary_market")
        if project_data.get("article_64_eligible", False):
            eligible_buyer_types.append("government_procurement")
        if cdr_type in ["dacs", "beccs", "enhanced_weathering"]:
            eligible_buyer_types.append("EU_innovation_fund")
        if not eligible_buyer_types:
            eligible_buyer_types.append("voluntary_market")

        # Best match (highest price)
        price_map = {k: CDR_MARKET_BENCHMARKS[k]["typical_price_usd"] for k in CDR_MARKET_BENCHMARKS}
        best_match = max(eligible_buyer_types, key=lambda b: price_map.get(b, 0))
        bench = CDR_MARKET_BENCHMARKS.get(best_match, {})
        credit_price_benchmark = bench.get("typical_price_usd", 20)
        price_range = bench.get("price_range_usd", (5, 50))

        market_notes = []
        if frontier_eligible:
            market_notes.append("Frontier AMC eligibility opens advance purchase at $200-$1000/tCO2 — prioritise Frontier outreach.")
        if corsia_eligible:
            market_notes.append("CORSIA eligibility provides access to growing airline offset demand (ICAO growth rate 60%+ p.a.).")
        if not frontier_eligible and trl >= 8:
            market_notes.append("High TRL reduces Frontier eligibility — focus on voluntary premium market with ICVCM CCP label.")

        return MarketEligibilityResult(
            corsia_eligible=corsia_eligible,
            corsia_programme=corsia_programme,
            frontier_eligible=frontier_eligible,
            frontier_score=round(frontier_score, 1),
            frontier_gap_analysis=frontier_gap_analysis,
            voluntary_market_tier=voluntary_tier,
            voluntary_registry=voluntary_registry,
            eligible_buyer_types=eligible_buyer_types,
            best_match_buyer=best_match,
            credit_price_benchmark_usd=credit_price_benchmark,
            price_range_usd=price_range,
            market_notes=market_notes,
        )

    def run_full_assessment(self, project_data: dict) -> CDRFullAssessmentResult:
        """
        Comprehensive CDR project assessment producing composite cdr_quality_score,
        tier, Oxford score, Art 6.4 eligibility, LCOE, Frontier eligibility, and
        credit price benchmark.
        """
        project_id = project_data.get("project_id", f"CDR-{date.today().strftime('%Y%m%d')}")
        assessment_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Run all sub-assessments
        tech = self.assess_cdr_technology(project_data)
        oxford = self.score_oxford_principles(project_data)
        art64 = self.assess_article64_eligibility(project_data)
        econ = self.calculate_cdr_economics(project_data)

        # Pass Oxford composite into market eligibility
        project_data_augmented = {**project_data, "oxford_composite_score": oxford.composite_score}
        market = self.assess_market_eligibility(project_data_augmented)

        # --- Composite CDR quality score (0-100) ---
        # Oxford principles: 40%
        oxford_contribution = oxford.composite_score * 0.40
        # Technology readiness: 25%
        tech_contribution = tech.technology_readiness_score * 0.25
        # Art 6.4: 20% (binary: all met = 20, partial credit pro-rata)
        art64_contribution = (art64.requirements_met / art64.total_requirements) * 20.0
        # Economics viability: 15%
        econ_map = {
            "economically_viable_at_100usd": 15,
            "viable_at_premium_markets_only": 10,
            "marginally_viable_with_blended_finance": 7,
            "requires_significant_subsidy_or_cost_reduction": 3,
        }
        econ_contribution = econ_map.get(econ.economics_viability, 5)

        cdr_quality_score = round(
            oxford_contribution + tech_contribution + art64_contribution + econ_contribution,
            1,
        )
        cdr_quality_score = min(cdr_quality_score, 100.0)

        # Quality tier
        cdr_quality_tier = "basic"
        for threshold, tier in self._CDR_QUALITY_TIERS:
            if cdr_quality_score >= threshold:
                cdr_quality_tier = tier
                break

        # Key strengths and risks
        key_strengths = []
        if oxford.composite_score >= 70:
            key_strengths.append(f"Strong Oxford CDR Principles score: {oxford.composite_score}/100")
        if art64.itmo_eligible:
            key_strengths.append("Paris Agreement Art 6.4 ITMO eligible — access to government procurement")
        if market.frontier_eligible:
            key_strengths.append(f"Frontier AMC eligible — premium pricing at ${market.credit_price_benchmark_usd}/tCO2")
        if tech.cost_reduction_pct_to_2050 > 50:
            key_strengths.append(f"Strong cost reduction trajectory: {tech.cost_reduction_pct_to_2050:.0f}% by 2050")
        if tech.permanence_years >= 1000:
            key_strengths.append(f"High permanence ({tech.permanence_years:,} years)")

        key_risks = []
        key_risks.extend(tech.risk_flags[:3])
        if not art64.itmo_eligible:
            key_risks.append(f"Art 6.4 gaps: {len(art64.eligibility_gaps)} unmet requirements")
        if econ.lcoe_usd_tco2 > 200:
            key_risks.append(f"High LCOE (${econ.lcoe_usd_tco2:.0f}/tCO2) limits market accessibility")

        # Recommended actions
        recommended_actions = []
        recommended_actions.extend(oxford.improvement_actions[:2])
        if art64.eligibility_gaps:
            recommended_actions.append(f"Resolve Art 6.4 gap: {art64.eligibility_gaps[0]}")
        if market.frontier_eligible:
            recommended_actions.append("Apply to Frontier Advance Market Commitment for pre-purchase agreement.")
        if market.corsia_eligible:
            recommended_actions.append("Enroll in TAB-approved CORSIA programme for airline offset market access.")
        if econ.break_even_price_usd_tco2 > 100:
            recommended_actions.append("Pursue blended finance (IFC/GCF) to reduce effective LCOE below market benchmark.")

        # Cross-framework linkage
        cross_framework = {
            "IPCC_AR6": f"Chapter 12 CDR — {tech.ipcc_category} category; potential {CDR_TECHNOLOGY_PROFILES.get(tech.cdr_type, {}).get('ipcc_ar6_potential_gtco2yr', 'N/A')} GtCO2/yr by 2050",
            "Oxford_CDR_Principles_2023": f"Composite score {oxford.composite_score}/100 — {oxford.quality_tier} tier",
            "Paris_Agreement_Art_6.4": f"{'Eligible' if art64.itmo_eligible else 'Not yet eligible'} — {art64.requirements_met}/{art64.total_requirements} requirements met",
            "CORSIA_ICAO": f"{'Eligible' if market.corsia_eligible else 'Not eligible'} — {market.corsia_programme}",
            "Frontier_AMC": f"{'Eligible' if market.frontier_eligible else 'Not eligible'} — Score {market.frontier_score}/100",
            "ICVCM_CCP": f"{'CCP-compatible registry' if oxford.quality_tier in ['gold','silver'] else 'Pre-CCP stage'} — verify with ICVCM CCP application",
            "CSRD_ESRS_E1": "Scope 4 / beyond-value-chain removals; CDR credits disclosed under ESRS E1 §§51-53 climate targets",
            "SBTi_BVCM": "Eligible as Beyond Value Chain Mitigation under SBTi Corporate Net-Zero Standard Appendix B",
        }

        return CDRFullAssessmentResult(
            project_id=project_id,
            assessment_date=assessment_date,
            cdr_type=tech.cdr_type,
            trl_level=tech.trl_level,
            scalability_rating=tech.scalability_rating,
            cost_current_usd_tco2=tech.cost_current_usd_tco2,
            cost_2050_usd_tco2=tech.cost_2050_usd_tco2,
            oxford_composite_score=oxford.composite_score,
            oxford_quality_tier=oxford.quality_tier,
            article_64_eligible=art64.itmo_eligible,
            itmo_eligible=art64.itmo_eligible,
            lcoe_usd_tco2=econ.lcoe_usd_tco2,
            break_even_price_usd_tco2=econ.break_even_price_usd_tco2,
            irr_at_100_usd_pct=econ.irr_at_100_usd_pct,
            frontier_eligible=market.frontier_eligible,
            corsia_eligible=market.corsia_eligible,
            best_match_buyer=market.best_match_buyer,
            credit_price_benchmark_usd=market.credit_price_benchmark_usd,
            cdr_quality_score=cdr_quality_score,
            cdr_quality_tier=cdr_quality_tier,
            key_strengths=key_strengths,
            key_risks=key_risks,
            recommended_actions=recommended_actions,
            cross_framework=cross_framework,
        )
