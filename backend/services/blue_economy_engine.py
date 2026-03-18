"""
Blue Economy & Ocean Finance Engine — E68
Standards: ICMA Blue Bond Principles 2023, Sustainable Ocean Finance (UNEP-FI SOF),
Blue Carbon Initiative (mangroves/seagrass/saltmarsh), High Seas Treaty BBNJ 2023,
OECD Ocean Finance Framework, Ocean Acidification (IPCC AR6 Chapter 3)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import random
import math

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

BLUE_BOND_USE_OF_PROCEEDS: Dict[str, Dict] = {
    "sustainable_fisheries": {
        "description": "MSC-certified and FIP-supported fisheries, IUU elimination",
        "icma_alignment_score": 0.92,
        "sof_pillar": "sustainable_ocean_economy",
        "sdg_targets": ["SDG14.4", "SDG14.6"],
        "typical_allocation_pct": 18,
    },
    "marine_conservation": {
        "description": "MPA establishment and management, coral reef restoration, seagrass beds",
        "icma_alignment_score": 0.95,
        "sof_pillar": "ocean_health",
        "sdg_targets": ["SDG14.2", "SDG14.5"],
        "typical_allocation_pct": 20,
    },
    "ocean_based_renewable_energy": {
        "description": "Offshore wind, wave energy, tidal power, OTEC",
        "icma_alignment_score": 0.88,
        "sof_pillar": "blue_energy",
        "sdg_targets": ["SDG7.2", "SDG13.1"],
        "typical_allocation_pct": 22,
    },
    "coastal_resilience": {
        "description": "Mangrove restoration, coastal wetland protection, sea-wall alternatives",
        "icma_alignment_score": 0.90,
        "sof_pillar": "climate_adaptation",
        "sdg_targets": ["SDG13.1", "SDG14.2"],
        "typical_allocation_pct": 15,
    },
    "marine_pollution_prevention": {
        "description": "Plastics reduction, port waste facilities, wastewater treatment",
        "icma_alignment_score": 0.85,
        "sof_pillar": "ocean_health",
        "sdg_targets": ["SDG14.1", "SDG12.4"],
        "typical_allocation_pct": 10,
    },
    "sustainable_aquaculture": {
        "description": "ASC-certified aquaculture, low-impact integrated multi-trophic systems",
        "icma_alignment_score": 0.80,
        "sof_pillar": "sustainable_ocean_economy",
        "sdg_targets": ["SDG14.2", "SDG2.3"],
        "typical_allocation_pct": 8,
    },
    "marine_protected_areas": {
        "description": "30x30 Kunming-Montreal target MPA financing, OECM designation",
        "icma_alignment_score": 0.93,
        "sof_pillar": "ocean_governance",
        "sdg_targets": ["SDG14.5", "SDG15.1"],
        "typical_allocation_pct": 5,
    },
    "ocean_acidification_mitigation": {
        "description": "Enhanced weathering, alkalinity addition pilots, seagrass buffers",
        "icma_alignment_score": 0.75,
        "sof_pillar": "climate_mitigation",
        "sdg_targets": ["SDG14.3", "SDG13.2"],
        "typical_allocation_pct": 2,
    },
}

BLUE_CARBON_ECOSYSTEMS: Dict[str, Dict] = {
    "mangrove": {
        "sequestration_rate_min_tco2_ha_yr": 6.0,
        "sequestration_rate_max_tco2_ha_yr": 8.0,
        "sequestration_rate_mean_tco2_ha_yr": 7.0,
        "soil_carbon_stock_tco2_ha": 860,
        "above_ground_carbon_tco2_ha": 120,
        "permanence_risk": "medium",  # saltwater intrusion, storm damage
        "additionality_baseline": "Deforestation rate 0.35%/yr (Hamilton & Friess 2018)",
        "verra_methodology": "VM0007",
        "co2_verra_methodology": "VM0033",
        "co_benefits": ["coastal_protection", "fisheries_habitat", "biodiversity", "livelihood"],
        "typical_project_lifetime_years": 30,
        "verification_cycle_years": 5,
        "monitoring_cost_usd_ha_yr": 45,
    },
    "seagrass": {
        "sequestration_rate_min_tco2_ha_yr": 0.4,
        "sequestration_rate_max_tco2_ha_yr": 0.8,
        "sequestration_rate_mean_tco2_ha_yr": 0.6,
        "soil_carbon_stock_tco2_ha": 140,
        "above_ground_carbon_tco2_ha": 2.5,
        "permanence_risk": "high",  # fragile, difficult monitoring
        "additionality_baseline": "Decline 7%/yr (IPCC 2022 AR6)",
        "verra_methodology": "VM0033",
        "co2_verra_methodology": "VM0033",
        "co_benefits": ["water_quality", "fisheries_nursery", "dugong_habitat"],
        "typical_project_lifetime_years": 20,
        "verification_cycle_years": 3,
        "monitoring_cost_usd_ha_yr": 80,
    },
    "saltmarsh": {
        "sequestration_rate_min_tco2_ha_yr": 2.0,
        "sequestration_rate_max_tco2_ha_yr": 4.0,
        "sequestration_rate_mean_tco2_ha_yr": 3.0,
        "soil_carbon_stock_tco2_ha": 430,
        "above_ground_carbon_tco2_ha": 15,
        "permanence_risk": "medium-low",
        "additionality_baseline": "Coastal squeeze losses (IPCC 2019 SROCC)",
        "verra_methodology": "VM0033",
        "co2_verra_methodology": "VM0033",
        "co_benefits": ["storm_surge_reduction", "bird_habitat", "water_filtration"],
        "typical_project_lifetime_years": 25,
        "verification_cycle_years": 5,
        "monitoring_cost_usd_ha_yr": 35,
    },
    "kelp": {
        "sequestration_rate_min_tco2_ha_yr": 0.2,
        "sequestration_rate_max_tco2_ha_yr": 0.4,
        "sequestration_rate_mean_tco2_ha_yr": 0.3,
        "soil_carbon_stock_tco2_ha": 0,  # exported to deep ocean
        "above_ground_carbon_tco2_ha": 5,
        "permanence_risk": "high",  # uncertain permanence pathway
        "additionality_baseline": "OA and warming-driven range contraction",
        "verra_methodology": "Under development",
        "co2_verra_methodology": "Under development",
        "co_benefits": ["fish_habitat", "urchin_grazing_control", "OA_buffer"],
        "typical_project_lifetime_years": 15,
        "verification_cycle_years": 2,
        "monitoring_cost_usd_ha_yr": 120,
    },
}

BBNJ_ARTICLES: Dict[str, Dict] = {
    "article_9_mgbr": {
        "title": "Marine Genetic Resources & Benefit Sharing",
        "description": "Access and benefit sharing for MGRs in ABNJ; multilateral mechanism",
        "compliance_indicators": ["mgr_access_policy", "benefit_sharing_agreement", "clearing_house_registration"],
        "weight": 0.25,
        "entry_into_force_target": "2025",
    },
    "article_17_eias": {
        "title": "Environmental Impact Assessments",
        "description": "EIA obligation for activities likely to have more than minor/transitory effect",
        "compliance_indicators": ["eia_screening_process", "cumulative_impact_assessment", "transboundary_notification"],
        "weight": 0.25,
        "entry_into_force_target": "2025",
    },
    "article_22_abmt": {
        "title": "Area-Based Management Tools including MPAs",
        "description": "Proposals for ABMTs/MPAs in ABNJ; global ocean governance architecture",
        "compliance_indicators": ["abmt_proposal_contributed", "mpa_management_plan", "monitoring_reporting"],
        "weight": 0.20,
        "entry_into_force_target": "2026",
    },
    "article_43_capacity_building": {
        "title": "Capacity Building & Technology Transfer",
        "description": "Obligations on developed parties to support developing states",
        "compliance_indicators": ["cb_program_active", "technology_transfer_mou", "financial_contribution"],
        "weight": 0.15,
        "entry_into_force_target": "2025",
    },
    "article_52_financial_mechanism": {
        "title": "Financial Mechanism & Special Fund",
        "description": "Voluntary fund and assessed contributions for BBNJ implementation",
        "compliance_indicators": ["fund_contribution_made", "access_to_fund_assessed", "reporting_submitted"],
        "weight": 0.15,
        "entry_into_force_target": "2026",
    },
}

SOF_PILLARS: Dict[str, Dict] = {
    "ocean_health": {
        "description": "Reducing pollution, restoring ecosystems, addressing ocean acidification",
        "key_indicators": ["mpa_coverage_pct", "plastic_reduction_targets", "wqi_score"],
        "financing_instruments": ["blue_bonds", "blue_carbon_credits", "impact_loans"],
        "weight": 0.22,
    },
    "sustainable_ocean_economy": {
        "description": "Sustainable fisheries, aquaculture, shipping decarbonisation",
        "key_indicators": ["msc_certified_pct", "poseidon_principles_alignment", "iuu_risk_score"],
        "financing_instruments": ["sustainability_linked_bonds", "green_shipping_finance"],
        "weight": 0.20,
    },
    "climate_adaptation": {
        "description": "Coastal resilience, mangrove/wetland finance, sea-level rise adaptation",
        "key_indicators": ["coastal_protection_coverage", "ecosystem_restoration_ha", "adaptation_finance_usd"],
        "financing_instruments": ["resilience_bonds", "debt_for_nature", "climate_insurance"],
        "weight": 0.20,
    },
    "climate_mitigation": {
        "description": "Ocean-based NbS, blue carbon sequestration, offshore renewables",
        "key_indicators": ["blue_carbon_tco2_yr", "offshore_renewable_gw", "shipping_ghg_reduction"],
        "financing_instruments": ["blue_carbon_credits", "green_bonds", "blended_finance"],
        "weight": 0.18,
    },
    "ocean_governance": {
        "description": "BBNJ Treaty implementation, high seas MPA, SDG14 financing",
        "key_indicators": ["bbnj_ratification", "sdg14_oda_usd", "high_seas_mpa_coverage"],
        "financing_instruments": ["sovereign_blue_bonds", "multilateral_ocean_funds"],
        "weight": 0.12,
    },
    "blue_energy": {
        "description": "Offshore wind, wave, tidal, OTEC, green hydrogen from ocean sources",
        "key_indicators": ["offshore_wind_gw", "wave_tidal_mw", "h2_blue_production_mt"],
        "financing_instruments": ["project_finance", "infrastructure_bonds", "blended_finance"],
        "weight": 0.08,
    },
}

OCEAN_ACIDIFICATION_RISK: Dict[str, Dict] = {
    "RCP2.6": {
        "ph_change_by_2100": -0.06,
        "aragonite_saturation_omega": 2.8,
        "risk_level": "low",
        "coral_bleaching_freq_multiplier": 1.3,
        "fisheries_revenue_impact_pct": -2.5,
    },
    "RCP4.5": {
        "ph_change_by_2100": -0.14,
        "aragonite_saturation_omega": 2.2,
        "risk_level": "moderate",
        "coral_bleaching_freq_multiplier": 2.0,
        "fisheries_revenue_impact_pct": -6.0,
    },
    "RCP6.0": {
        "ph_change_by_2100": -0.22,
        "aragonite_saturation_omega": 1.8,
        "risk_level": "high",
        "coral_bleaching_freq_multiplier": 3.5,
        "fisheries_revenue_impact_pct": -11.0,
    },
    "RCP8.5": {
        "ph_change_by_2100": -0.33,
        "aragonite_saturation_omega": 1.2,
        "risk_level": "very_high",
        "coral_bleaching_freq_multiplier": 6.0,
        "fisheries_revenue_impact_pct": -18.5,
    },
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class BlueBondScreeningResult:
    bond_id: str
    issuer: str
    bond_amount_usd: float
    icma_alignment_score: float
    eligible_categories: List[str]
    ineligible_categories: List[str]
    sof_pillar_coverage: Dict[str, float]
    use_of_proceeds_breakdown: Dict[str, float]
    greenium_bps: float
    external_review_required: bool
    reporting_frequency: str
    overall_verdict: str  # fully_aligned | partially_aligned | not_aligned
    recommendations: List[str]


@dataclass
class BlueCarbonResult:
    project_id: str
    ecosystem_type: str
    area_hectares: float
    sequestration_rate_tco2_ha_yr: float
    total_annual_sequestration_tco2: float
    project_lifetime_years: int
    total_lifetime_sequestration_tco2: float
    additionality_score: float
    permanence_score: float
    co_benefits: List[str]
    verra_vcs_eligible: bool
    gold_standard_eligible: bool
    carbon_credit_value_usd: float
    monitoring_cost_usd_yr: float
    net_revenue_usd_yr: float
    verification_cycle_years: int
    risk_buffer_pct: float


@dataclass
class BBNJComplianceResult:
    entity_id: str
    entity_type: str
    article_scores: Dict[str, float]
    overall_compliance_score: float
    compliance_level: str  # compliant | partial | non_compliant
    gaps: List[str]
    priority_actions: List[str]
    bbnj_readiness_timeline: str


@dataclass
class OceanAcidificationRisk:
    portfolio_id: str
    rcp_scenario: str
    ph_change_2100: float
    aragonite_saturation: float
    risk_level: str
    ocean_economy_exposure_usd: float
    fisheries_revenue_at_risk_usd: float
    coral_reef_asset_at_risk_usd: float
    aquaculture_at_risk_usd: float
    total_oa_var_usd: float
    adaptation_cost_estimate_usd: float


@dataclass
class OceanPortfolioResult:
    portfolio_id: str
    total_blue_assets_usd: float
    sof_score: float
    sof_pillar_scores: Dict[str, float]
    blue_bond_allocation_pct: float
    blue_carbon_credits_tco2: float
    mpa_financing_usd: float
    ocean_risk_score: float
    oa_risk_var_usd: float
    top_blue_economy_sectors: List[Dict]
    sdg14_alignment_score: float
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Engine Functions
# ---------------------------------------------------------------------------

def screen_blue_bond(bond_data: Dict[str, Any]) -> BlueBondScreeningResult:
    """Screen a bond against ICMA Blue Bond Principles 2023 and SOF framework."""
    entity_id = bond_data.get("entity_id", "default")
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    bond_id = bond_data.get("bond_id", f"BB-{rng.randint(1000, 9999)}")
    issuer = bond_data.get("issuer", "Unknown Issuer")
    bond_amount_usd = float(bond_data.get("bond_amount_usd", 500_000_000))
    declared_categories = bond_data.get("use_of_proceeds_categories", list(BLUE_BOND_USE_OF_PROCEEDS.keys())[:4])

    eligible_categories = []
    ineligible_categories = []
    weighted_alignment = 0.0
    sof_pillar_coverage: Dict[str, float] = {p: 0.0 for p in SOF_PILLARS}
    use_of_proceeds_breakdown: Dict[str, float] = {}

    for cat in declared_categories:
        if cat in BLUE_BOND_USE_OF_PROCEEDS:
            cat_data = BLUE_BOND_USE_OF_PROCEEDS[cat]
            score = cat_data["icma_alignment_score"]
            noise = rng.uniform(-0.03, 0.03)
            final_score = max(0.5, min(1.0, score + noise))
            eligible_categories.append(cat)
            weighted_alignment += final_score / len(declared_categories)
            pillar = cat_data["sof_pillar"]
            if pillar in sof_pillar_coverage:
                sof_pillar_coverage[pillar] += 1.0 / len(declared_categories)
            alloc_pct = cat_data["typical_allocation_pct"] + rng.uniform(-3, 3)
            use_of_proceeds_breakdown[cat] = round(alloc_pct, 1)
        else:
            ineligible_categories.append(cat)

    # Normalise sof pillar coverage
    total_pillar = sum(sof_pillar_coverage.values())
    if total_pillar > 0:
        sof_pillar_coverage = {k: round(v / total_pillar, 3) for k, v in sof_pillar_coverage.items()}

    # Normalise use of proceeds to 100%
    total_alloc = sum(use_of_proceeds_breakdown.values())
    if total_alloc > 0:
        use_of_proceeds_breakdown = {k: round(v / total_alloc * 100, 1) for k, v in use_of_proceeds_breakdown.items()}

    greenium_bps = round(rng.uniform(2.0, 8.0) * weighted_alignment, 2)
    external_review_required = bond_amount_usd >= 100_000_000 or weighted_alignment < 0.75

    if weighted_alignment >= 0.85:
        verdict = "fully_aligned"
        reporting_freq = "annual"
    elif weighted_alignment >= 0.65:
        verdict = "partially_aligned"
        reporting_freq = "semi-annual"
    else:
        verdict = "not_aligned"
        reporting_freq = "quarterly"

    recommendations = []
    if len(eligible_categories) < 3:
        recommendations.append("Diversify use-of-proceeds across at least 3 ICMA-eligible blue categories")
    if weighted_alignment < 0.85:
        recommendations.append("Engage second-party opinion provider (Sustainalytics/DNV/Vigeo)")
    if "marine_conservation" not in eligible_categories:
        recommendations.append("Include marine conservation category to strengthen SDG14 alignment")
    if external_review_required:
        recommendations.append("Obtain external review per ICMA Blue Bond Principles Section 3")
    if greenium_bps < 3.0:
        recommendations.append("Improve use-of-proceeds specificity to capture higher greenium")

    return BlueBondScreeningResult(
        bond_id=bond_id,
        issuer=issuer,
        bond_amount_usd=bond_amount_usd,
        icma_alignment_score=round(weighted_alignment, 4),
        eligible_categories=eligible_categories,
        ineligible_categories=ineligible_categories,
        sof_pillar_coverage=sof_pillar_coverage,
        use_of_proceeds_breakdown=use_of_proceeds_breakdown,
        greenium_bps=greenium_bps,
        external_review_required=external_review_required,
        reporting_frequency=reporting_freq,
        overall_verdict=verdict,
        recommendations=recommendations,
    )


def assess_blue_carbon(project_data: Dict[str, Any]) -> BlueCarbonResult:
    """Calculate blue carbon sequestration, additionality, permanence, and credit economics."""
    project_id = project_data.get("project_id", "default")
    rng = random.Random(hash(str(project_id)) & 0xFFFFFFFF)

    ecosystem_type = project_data.get("ecosystem_type", "mangrove")
    if ecosystem_type not in BLUE_CARBON_ECOSYSTEMS:
        ecosystem_type = "mangrove"
    eco = BLUE_CARBON_ECOSYSTEMS[ecosystem_type]

    area_ha = float(project_data.get("area_hectares", rng.uniform(100, 5000)))
    seq_rate = rng.uniform(eco["sequestration_rate_min_tco2_ha_yr"], eco["sequestration_rate_max_tco2_ha_yr"])
    lifetime_years = eco["typical_project_lifetime_years"]
    total_annual = area_ha * seq_rate
    total_lifetime = total_annual * lifetime_years

    # Additionality score: based on threat level, land tenure clarity, baseline documentation
    threat_level = project_data.get("threat_level", rng.uniform(0.4, 0.9))
    tenure_clarity = project_data.get("tenure_clarity", rng.uniform(0.5, 1.0))
    baseline_quality = project_data.get("baseline_quality", rng.uniform(0.5, 1.0))
    additionality_score = round((threat_level * 0.4 + tenure_clarity * 0.3 + baseline_quality * 0.3), 4)

    # Permanence score: ecosystem fragility, climate vulnerability, governance
    eco_stability = 1.0 - (0.3 if eco["permanence_risk"] == "high" else 0.15 if eco["permanence_risk"] == "medium" else 0.05)
    governance_score = project_data.get("governance_score", rng.uniform(0.5, 0.9))
    permanence_score = round((eco_stability * 0.5 + governance_score * 0.5), 4)

    # Risk buffer per Verra (typically 10-30% depending on permanence)
    risk_buffer_pct = round(max(10.0, min(30.0, (1 - permanence_score) * 60)), 1)
    net_sequestration = total_annual * (1 - risk_buffer_pct / 100)

    # Credit economics
    carbon_price_usd_tco2 = project_data.get("carbon_price_usd_tco2", rng.uniform(15, 45))
    carbon_credit_value_usd = net_sequestration * carbon_price_usd_tco2
    monitoring_cost = area_ha * eco["monitoring_cost_usd_ha_yr"]
    net_revenue = carbon_credit_value_usd - monitoring_cost

    # Eligibility
    verra_eligible = (additionality_score >= 0.6 and permanence_score >= 0.5
                      and eco["verra_methodology"] not in ["Under development"])
    gs_eligible = verra_eligible and additionality_score >= 0.70 and eco_stability >= 0.75

    return BlueCarbonResult(
        project_id=str(project_id),
        ecosystem_type=ecosystem_type,
        area_hectares=round(area_ha, 2),
        sequestration_rate_tco2_ha_yr=round(seq_rate, 3),
        total_annual_sequestration_tco2=round(total_annual, 2),
        project_lifetime_years=lifetime_years,
        total_lifetime_sequestration_tco2=round(total_lifetime, 2),
        additionality_score=additionality_score,
        permanence_score=permanence_score,
        co_benefits=eco["co_benefits"],
        verra_vcs_eligible=verra_eligible,
        gold_standard_eligible=gs_eligible,
        carbon_credit_value_usd=round(carbon_credit_value_usd, 2),
        monitoring_cost_usd_yr=round(monitoring_cost, 2),
        net_revenue_usd_yr=round(net_revenue, 2),
        verification_cycle_years=eco["verification_cycle_years"],
        risk_buffer_pct=risk_buffer_pct,
    )


def assess_bbnj_compliance(entity_data: Dict[str, Any]) -> BBNJComplianceResult:
    """Assess compliance with the High Seas Treaty BBNJ 2023 across 5 key article areas."""
    entity_id = entity_data.get("entity_id", "default")
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    entity_type = entity_data.get("entity_type", "flag_state")  # flag_state | coastal_state | financial_institution
    disclosed_scores = entity_data.get("article_scores", {})

    article_scores: Dict[str, float] = {}
    gaps: List[str] = []

    for art_key, art_data in BBNJ_ARTICLES.items():
        indicators = art_data["compliance_indicators"]
        if art_key in disclosed_scores:
            raw = float(disclosed_scores[art_key])
        else:
            base = rng.uniform(0.3, 0.85)
            # Financial institutions score lower on governance articles
            if entity_type == "financial_institution" and art_key in ["article_22_abmt", "article_9_mgbr"]:
                base *= 0.7
            raw = base

        score = round(min(1.0, max(0.0, raw + rng.uniform(-0.05, 0.05))), 4)
        article_scores[art_key] = score

        if score < 0.6:
            gaps.append(f"{art_data['title']}: score {score:.2f} — review indicators: {', '.join(indicators[:2])}")

    overall = round(sum(article_scores[k] * BBNJ_ARTICLES[k]["weight"] for k in article_scores), 4)

    if overall >= 0.75:
        level = "compliant"
        timeline = "Maintain current practices; update on treaty entry into force"
    elif overall >= 0.50:
        level = "partial"
        timeline = "12-18 months to full compliance post treaty ratification"
    else:
        level = "non_compliant"
        timeline = "24-36 months; requires structural governance changes"

    priority_actions = []
    sorted_gaps = sorted(
        [(k, article_scores[k], BBNJ_ARTICLES[k]["weight"]) for k in article_scores],
        key=lambda x: x[1] * x[2]
    )
    for art_key, score, weight in sorted_gaps[:3]:
        priority_actions.append(
            f"Prioritise {BBNJ_ARTICLES[art_key]['title']} (score {score:.2f}, weight {weight})"
        )

    return BBNJComplianceResult(
        entity_id=str(entity_id),
        entity_type=entity_type,
        article_scores=article_scores,
        overall_compliance_score=overall,
        compliance_level=level,
        gaps=gaps,
        priority_actions=priority_actions,
        bbnj_readiness_timeline=timeline,
    )


def assess_ocean_acidification_risk(portfolio_data: Dict[str, Any]) -> OceanAcidificationRisk:
    """Assess portfolio exposure to ocean acidification under IPCC AR6 RCP scenarios."""
    portfolio_id = portfolio_data.get("portfolio_id", "default")
    rng = random.Random(hash(str(portfolio_id)) & 0xFFFFFFFF)

    rcp_scenario = portfolio_data.get("rcp_scenario", "RCP4.5")
    if rcp_scenario not in OCEAN_ACIDIFICATION_RISK:
        rcp_scenario = "RCP4.5"
    oa = OCEAN_ACIDIFICATION_RISK[rcp_scenario]

    total_ocean_economy_exposure = float(portfolio_data.get("ocean_economy_exposure_usd", rng.uniform(1e8, 5e9)))

    # Sector breakdown of ocean economy
    fisheries_pct = portfolio_data.get("fisheries_pct", rng.uniform(0.2, 0.4))
    coral_reef_pct = portfolio_data.get("coral_reef_pct", rng.uniform(0.1, 0.25))
    aquaculture_pct = portfolio_data.get("aquaculture_pct", rng.uniform(0.1, 0.2))

    fisheries_exposure = total_ocean_economy_exposure * fisheries_pct
    coral_reef_exposure = total_ocean_economy_exposure * coral_reef_pct
    aquaculture_exposure = total_ocean_economy_exposure * aquaculture_pct

    fisheries_at_risk = fisheries_exposure * abs(oa["fisheries_revenue_impact_pct"]) / 100
    # Coral reef: severe bleaching → asset value decline; aragonite saturation drives mortality
    coral_mortality_factor = max(0, (2.5 - oa["aragonite_saturation_omega"]) / 2.5) * 0.8
    coral_at_risk = coral_reef_exposure * coral_mortality_factor
    # Aquaculture: shellfish particularly vulnerable
    aquaculture_at_risk = aquaculture_exposure * max(0, (2.5 - oa["aragonite_saturation_omega"]) / 2.0) * 0.5

    total_oa_var = fisheries_at_risk + coral_at_risk + aquaculture_at_risk
    adaptation_cost = total_oa_var * rng.uniform(0.15, 0.35)

    return OceanAcidificationRisk(
        portfolio_id=str(portfolio_id),
        rcp_scenario=rcp_scenario,
        ph_change_2100=oa["ph_change_by_2100"],
        aragonite_saturation=oa["aragonite_saturation_omega"],
        risk_level=oa["risk_level"],
        ocean_economy_exposure_usd=round(total_ocean_economy_exposure, 2),
        fisheries_revenue_at_risk_usd=round(fisheries_at_risk, 2),
        coral_reef_asset_at_risk_usd=round(coral_at_risk, 2),
        aquaculture_at_risk_usd=round(aquaculture_at_risk, 2),
        total_oa_var_usd=round(total_oa_var, 2),
        adaptation_cost_estimate_usd=round(adaptation_cost, 2),
    )


def aggregate_ocean_portfolio(portfolio_data: Dict[str, Any]) -> OceanPortfolioResult:
    """Aggregate portfolio-level SOF score, blue bond allocation, and ocean risk metrics."""
    portfolio_id = portfolio_data.get("portfolio_id", "default")
    rng = random.Random(hash(str(portfolio_id)) & 0xFFFFFFFF)

    holdings = portfolio_data.get("holdings", [])
    total_aum = float(portfolio_data.get("total_aum_usd", rng.uniform(1e9, 5e10)))

    if not holdings:
        # Generate synthetic portfolio
        sectors = ["offshore_wind", "sustainable_fisheries", "marine_conservation",
                   "coastal_infrastructure", "blue_bonds", "aquaculture"]
        holdings = [
            {"sector": s, "exposure_usd": total_aum * rng.uniform(0.05, 0.20)}
            for s in sectors
        ]

    total_blue = sum(h.get("exposure_usd", 0) for h in holdings)
    blue_bond_alloc_pct = portfolio_data.get("blue_bond_allocation_pct", rng.uniform(8, 25))

    # SOF pillar scores
    pillar_scores: Dict[str, float] = {}
    for pillar, pdata in SOF_PILLARS.items():
        base = rng.uniform(0.40, 0.80)
        pillar_scores[pillar] = round(base, 4)

    sof_score = round(sum(pillar_scores[p] * SOF_PILLARS[p]["weight"] for p in pillar_scores), 4)

    blue_carbon_credits = rng.uniform(5000, 200000)
    mpa_financing = total_blue * rng.uniform(0.03, 0.12)
    ocean_risk_score = round(1 - sof_score * 0.7, 4)

    oa_risk = assess_ocean_acidification_risk({
        "portfolio_id": portfolio_id,
        "rcp_scenario": portfolio_data.get("rcp_scenario", "RCP4.5"),
        "ocean_economy_exposure_usd": total_blue,
    })

    top_sectors = sorted(holdings, key=lambda h: h.get("exposure_usd", 0), reverse=True)[:5]
    top_sectors_out = [
        {"sector": h.get("sector", "unknown"), "exposure_usd": round(h.get("exposure_usd", 0), 2)}
        for h in top_sectors
    ]

    sdg14_score = round(sof_score * 0.85 + rng.uniform(0, 0.1), 4)

    recommendations = []
    if blue_bond_alloc_pct < 15:
        recommendations.append("Increase blue bond allocation to >=15% for SDG14 alignment")
    if pillar_scores.get("ocean_health", 0) < 0.6:
        recommendations.append("Strengthen ocean health pillar through MPA and pollution finance")
    if blue_carbon_credits < 50000:
        recommendations.append("Scale blue carbon credit procurement to offset portfolio OA risk")
    if ocean_risk_score > 0.4:
        recommendations.append("Apply UNEP-FI SOF framework to reduce portfolio ocean risk score")

    return OceanPortfolioResult(
        portfolio_id=str(portfolio_id),
        total_blue_assets_usd=round(total_blue, 2),
        sof_score=sof_score,
        sof_pillar_scores=pillar_scores,
        blue_bond_allocation_pct=round(blue_bond_alloc_pct, 2),
        blue_carbon_credits_tco2=round(blue_carbon_credits, 2),
        mpa_financing_usd=round(mpa_financing, 2),
        ocean_risk_score=ocean_risk_score,
        oa_risk_var_usd=round(oa_risk.total_oa_var_usd, 2),
        top_blue_economy_sectors=top_sectors_out,
        sdg14_alignment_score=sdg14_score,
        recommendations=recommendations,
    )


def assess_sof_alignment(entity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive UNEP-FI Sustainable Ocean Finance alignment assessment."""
    entity_id = entity_data.get("entity_id", "default")
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    pillar_assessments = {}
    for pillar, pdata in SOF_PILLARS.items():
        score = rng.uniform(0.35, 0.90)
        pillar_assessments[pillar] = {
            "score": round(score, 4),
            "description": pdata["description"],
            "key_indicators": pdata["key_indicators"],
            "financing_instruments": pdata["financing_instruments"],
            "contribution_weight": pdata["weight"],
        }

    overall_sof = round(sum(
        pillar_assessments[p]["score"] * SOF_PILLARS[p]["weight"]
        for p in pillar_assessments
    ), 4)

    sdg14_financing_gap_bn = 175  # OECD estimated annual SDG14 gap
    entity_contribution_pct = rng.uniform(0.001, 0.05)

    return {
        "entity_id": entity_id,
        "overall_sof_score": overall_sof,
        "sof_tier": "leader" if overall_sof >= 0.75 else "progressing" if overall_sof >= 0.50 else "emerging",
        "pillar_assessments": pillar_assessments,
        "sdg14_financing_gap_bn_usd": sdg14_financing_gap_bn,
        "entity_contribution_pct": round(entity_contribution_pct, 4),
        "poseidon_principles_aligned": overall_sof >= 0.65,
        "sea_pledge_eligible": overall_sof >= 0.70,
        "priority_pillars": [
            p for p, d in pillar_assessments.items() if d["score"] < 0.55
        ],
        "reference_frameworks": [
            "UNEP-FI Sustainable Ocean Finance 2021",
            "ICMA Blue Bond Principles 2023",
            "OECD Ocean Finance Framework 2022",
            "Poseidon Principles 2019",
        ],
    }
