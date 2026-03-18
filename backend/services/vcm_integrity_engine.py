"""
Voluntary Carbon Market (VCM) Integrity Engine — E96
=====================================================

Regulatory / framework basis:
  - ICVCM Core Carbon Principles (CCP) Assessment Framework v2.0, 2023
  - VCMI Claims Code of Practice v1.1, 2023
  - Oxford Offsetting Principles, 2020 (Smith School, University of Oxford)
  - Verra VCS v4.0 / Gold Standard v4.3 / ACR v13.0 / CAR / Art 6 ITMOs
  - CORSIA Eligible Fuels & Carbon Units (2024-2026 cycle, ICAO)
  - Paris Agreement Article 6 — corresponding adjustment requirements
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Reference Data — ICVCM Core Carbon Principles (10 criteria)
# ---------------------------------------------------------------------------

ICVCM_CRITERIA: dict[str, dict[str, Any]] = {
    "C1": {
        "id": "C1",
        "title": "Effective Governance",
        "pillar": "Governance",
        "weight": 0.10,
        "description": (
            "The carbon-crediting programme has effective governance structures, procedures and processes "
            "that ensure transparency, accountability and overall credibility of the programme."
        ),
        "assessment_elements": [
            "Publicly available governance documentation",
            "Independent oversight body",
            "Conflict of interest policy",
            "Appeals and grievance mechanism",
            "Financial sustainability of the programme",
        ],
        "ccp_threshold": 0.70,
    },
    "C2": {
        "id": "C2",
        "title": "Transparency",
        "pillar": "Governance",
        "weight": 0.08,
        "description": (
            "The carbon-crediting programme has high levels of transparency by making key data and "
            "information about carbon credits publicly available in a structured accessible format."
        ),
        "assessment_elements": [
            "Public project documentation",
            "Monitoring reports publicly available",
            "Registry issuance and retirement data public",
            "Validation/verification reports public",
            "Methodology documentation public",
        ],
        "ccp_threshold": 0.75,
    },
    "C3": {
        "id": "C3",
        "title": "Robust Independent Third-Party Validation & Verification",
        "pillar": "Governance",
        "weight": 0.10,
        "description": (
            "Carbon credits are validated and verified by independent, qualified and competent "
            "third-party validation/verification bodies (VVBs) that are accredited by the programme."
        ),
        "assessment_elements": [
            "VVB accreditation requirements",
            "VVB independence from project developers",
            "Competency requirements for auditors",
            "Site visit requirements",
            "Sampling and materiality thresholds",
        ],
        "ccp_threshold": 0.70,
    },
    "C4": {
        "id": "C4",
        "title": "Additionality",
        "pillar": "Emissions Impact",
        "weight": 0.15,
        "description": (
            "The GHG emission reductions or removals from the project would not have occurred in the "
            "absence of the incentive created by carbon finance (additionality)."
        ),
        "assessment_elements": [
            "Regulatory surplus test",
            "Financial/investment additionality test",
            "Common practice barrier analysis",
            "Performance standard additionality (where applicable)",
            "Additionality reassessment frequency",
        ],
        "ccp_threshold": 0.70,
    },
    "C5": {
        "id": "C5",
        "title": "Permanence",
        "pillar": "Emissions Impact",
        "weight": 0.12,
        "description": (
            "GHG emission reductions or removals that are credited are permanent or, where there is "
            "a risk of reversal, that risk is identified and adequately mitigated."
        ),
        "assessment_elements": [
            "Buffer pool / insurance mechanism",
            "Reversal risk assessment",
            "Long-term monitoring post-crediting",
            "Reversals covered by buffer pool",
            "Unplanned reversal procedures",
        ],
        "ccp_threshold": 0.65,
    },
    "C6": {
        "id": "C6",
        "title": "Robust Quantification of Emissions Reductions & Removals",
        "pillar": "Emissions Impact",
        "weight": 0.12,
        "description": (
            "GHG emission reductions and removals are calculated accurately, conservatively, and "
            "transparently in accordance with a clearly defined and scientifically grounded methodology."
        ),
        "assessment_elements": [
            "Conservative baseline methodology",
            "Uncertainty quantification and conservative adjustments",
            "Approved/scientifically grounded methodology",
            "Monitoring plan with key parameters",
            "Regular verification against monitoring data",
        ],
        "ccp_threshold": 0.70,
    },
    "C7": {
        "id": "C7",
        "title": "No Double Counting",
        "pillar": "Emissions Impact",
        "weight": 0.10,
        "description": (
            "GHG emission reductions or removals are not double counted, meaning they are only "
            "counted once toward meeting a mitigation target or in a representation."
        ),
        "assessment_elements": [
            "Registry serial number uniqueness",
            "Corresponding adjustment if in NDC territory",
            "No double issuance across programmes",
            "Single use / retirement tracking",
            "Vintage and project boundary uniqueness",
        ],
        "ccp_threshold": 0.80,
    },
    "C8": {
        "id": "C8",
        "title": "Sustainable Development",
        "pillar": "Sustainable Development",
        "weight": 0.08,
        "description": (
            "Carbon-crediting activities contribute to sustainable development by creating benefits "
            "for local communities and the environment beyond GHG mitigation."
        ),
        "assessment_elements": [
            "SDG co-benefit identification",
            "Community benefit sharing",
            "Local employment and capacity building",
            "Gender equity provisions",
            "Monitoring of sustainable development benefits",
        ],
        "ccp_threshold": 0.60,
    },
    "C9": {
        "id": "C9",
        "title": "Biodiversity & Ecosystem Safeguards",
        "pillar": "Sustainable Development",
        "weight": 0.08,
        "description": (
            "Carbon-crediting activities protect biodiversity and ecosystems from any negative impacts "
            "that could arise from project activities."
        ),
        "assessment_elements": [
            "Biodiversity impact assessment required",
            "Ecosystem services assessment",
            "No-net-loss / net gain provisions",
            "Invasive species risk management",
            "Protected area / sensitive ecosystem safeguards",
        ],
        "ccp_threshold": 0.60,
    },
    "C10": {
        "id": "C10",
        "title": "Respect for Human Rights & Indigenous Peoples",
        "pillar": "Sustainable Development",
        "weight": 0.07,
        "description": (
            "Carbon-crediting activities respect human rights, including the rights of indigenous "
            "peoples and local communities (IPLCs), including Free Prior and Informed Consent (FPIC)."
        ),
        "assessment_elements": [
            "FPIC process for IPLC-affected projects",
            "Grievance and redress mechanism",
            "Labour rights compliance",
            "Land tenure and property rights verification",
            "UNDRIP alignment",
        ],
        "ccp_threshold": 0.65,
    },
}

# ---------------------------------------------------------------------------
# Reference Data — VCMI Claims Code of Practice tiers
# ---------------------------------------------------------------------------

VCMI_CLAIM_TIERS: dict[str, dict[str, Any]] = {
    "no_claim": {
        "tier": "no_claim",
        "label": "No VCMI Claim",
        "description": "Company does not meet eligibility criteria for any VCMI claim level.",
        "sbti_near_term_required": False,
        "residual_emissions_max_pct": None,
        "high_integrity_credits_pct": 0,
        "annual_claim_volume_rule": None,
        "ccp_label_required": False,
        "additional_requirements": [],
    },
    "silver": {
        "tier": "silver",
        "label": "VCMI Silver Claim",
        "description": (
            "Company has an SBTi-validated near-term target and retires high-integrity credits "
            "equal to at least 60% of residual emissions (≤40% residual gap)."
        ),
        "sbti_near_term_required": True,
        "residual_emissions_max_pct": 40,
        "high_integrity_credits_pct": 60,
        "annual_claim_volume_rule": "credits >= 60% of residual scope 1+2+3 above target",
        "ccp_label_required": False,
        "ccp_label_preferred": True,
        "additional_requirements": [
            "SBTi near-term target validated and publicly disclosed",
            "Annual VCMI Credibility Checklist submission",
            "Credit vintage within 5 years of retirement",
        ],
    },
    "gold": {
        "tier": "gold",
        "label": "VCMI Gold Claim",
        "description": (
            "Company has SBTi-validated near-term AND long-term targets; retires high-integrity "
            "credits covering residual emissions (≤20% residual gap)."
        ),
        "sbti_near_term_required": True,
        "sbti_long_term_required": True,
        "residual_emissions_max_pct": 20,
        "high_integrity_credits_pct": 100,
        "annual_claim_volume_rule": "credits >= 100% of residual scope 1+2+3 above target",
        "ccp_label_required": False,
        "ccp_label_preferred": True,
        "additional_requirements": [
            "SBTi near-term AND long-term (net-zero) targets validated",
            "Annual VCMI Credibility Checklist submission",
            "Third-party assurance of emissions inventory",
            "Credit vintage within 5 years of retirement",
        ],
    },
    "platinum": {
        "tier": "platinum",
        "label": "VCMI Platinum Claim",
        "description": (
            "Highest VCMI tier. Company has SBTi near-term + long-term targets; residual emissions "
            "≤10%; retires ICVCM CCP-labelled credits exclusively."
        ),
        "sbti_near_term_required": True,
        "sbti_long_term_required": True,
        "residual_emissions_max_pct": 10,
        "high_integrity_credits_pct": 100,
        "annual_claim_volume_rule": "credits >= 100% of residual scope 1+2+3 above target",
        "ccp_label_required": True,
        "additional_requirements": [
            "SBTi near-term AND net-zero validated targets",
            "Annual VCMI Credibility Checklist + independent assurance",
            "ALL credits must carry ICVCM CCP label",
            "Credit vintage within 5 years of retirement",
            "Public disclosure of credit registry serials",
        ],
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Oxford Offsetting Principles (2020)
# ---------------------------------------------------------------------------

OXFORD_PRINCIPLES: dict[str, dict[str, Any]] = {
    "P1": {
        "id": "P1",
        "title": "Prioritise emission reductions and then use high-quality offsets",
        "description": (
            "Companies and individuals should prioritise direct emission reductions across "
            "their value chains before using carbon offsets. Offsetting is not a substitute "
            "for near-term decarbonisation."
        ),
        "scoring_rubric": {
            "1.0": "Science-based reduction targets; decarbonisation spend >5× offset spend; offsets <10% of total GHG",
            "0.75": "Near-term reduction targets; decarbonisation plan in place; offsets <25% of GHG",
            "0.50": "Reduction targets set but not SBTi validated; moderate offset reliance",
            "0.25": "Weak reduction commitments; heavy offset reliance (>50% of GHG)",
            "0.0": "No reduction targets; offsets used as primary mitigation strategy",
        },
    },
    "P2": {
        "id": "P2",
        "title": "Shift to carbon removal offsets over time",
        "description": (
            "Over time, offsetting portfolios should shift from emission avoidance/reduction "
            "to carbon removal (both nature-based and engineered), as removals provide greater "
            "long-term climate benefit."
        ),
        "scoring_rubric": {
            "1.0": "Removal credits >50% of portfolio; clear trajectory to increase removal share",
            "0.75": "Removal credits 25-50% with committed trajectory to increase",
            "0.50": "Removal credits 10-25% with some commitment to shift",
            "0.25": "Removal credits <10% with weak commitment",
            "0.0": "No removal credits; no commitment to shift",
        },
    },
    "P3": {
        "id": "P3",
        "title": "Shift to long-lived storage solutions over time",
        "description": (
            "Where removal credits are used, portfolio should shift toward long-lived geological "
            "or mineralisation storage (DACCS, BECCS, enhanced weathering) rather than "
            "short-lived biological storage (forestry)."
        ),
        "scoring_rubric": {
            "1.0": "Geological removal >25% of removals; committed trajectory; durability >1000yr",
            "0.75": "Mixed portfolio with some geological storage; clear trajectory to increase",
            "0.50": "Primarily biological but with technology roadmap",
            "0.25": "Biological only; no plan to include long-lived storage",
            "0.0": "Biological storage only; no awareness of durability issue",
        },
    },
    "P4": {
        "id": "P4",
        "title": "Support development of a responsible carbon market",
        "description": (
            "Buyers should take steps to support market integrity, including paying a price "
            "that reflects the full cost of high-quality offsets, advocating for robust "
            "standards, and addressing lifecycle GHG impacts."
        ),
        "scoring_rubric": {
            "1.0": "CCP/high-integrity credits only; price premium paid; advocacy for standards; lifecycle GHG addressed",
            "0.75": "High-integrity credits; fair pricing; some market advocacy",
            "0.50": "Mixed quality portfolio; adequate pricing",
            "0.25": "Low-price, low-quality credits dominant; minimal market engagement",
            "0.0": "Purchasing lowest-cost credits; undermining market integrity",
        },
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Registries
# ---------------------------------------------------------------------------

REGISTRY_PROFILES: dict[str, dict[str, Any]] = {
    "verra_vcs": {
        "name": "Verra Verified Carbon Standard (VCS)",
        "abbreviation": "VCS",
        "body": "Verra",
        "registry_url": "https://registry.verra.org",
        "serial_format": "VCS-{project_id}-{vintage}-{serial}",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "version": "v4.0",
        "projects_registered": 2000,
        "credits_issued_mtco2e": 1050,
        "credits_retired_mtco2e": 620,
    },
    "gold_standard": {
        "name": "Gold Standard for the Global Goals",
        "abbreviation": "GS4GG",
        "body": "Gold Standard Foundation",
        "registry_url": "https://registry.goldstandard.org",
        "serial_format": "GS{project_id}-{vintage}-{serial}",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "version": "v4.3",
        "projects_registered": 550,
        "credits_issued_mtco2e": 185,
        "credits_retired_mtco2e": 142,
    },
    "acr": {
        "name": "American Carbon Registry",
        "abbreviation": "ACR",
        "body": "Winrock International",
        "registry_url": "https://acr2.apx.com",
        "serial_format": "ACR{project_id}-{vintage}-{serial}",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "version": "v13.0",
        "projects_registered": 310,
        "credits_issued_mtco2e": 115,
        "credits_retired_mtco2e": 78,
    },
    "car": {
        "name": "Climate Action Reserve",
        "abbreviation": "CAR",
        "body": "Climate Action Reserve",
        "registry_url": "https://thereserve2.apx.com",
        "serial_format": "CAR{project_id}-{vintage}-{serial}",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "version": "v6.0",
        "projects_registered": 280,
        "credits_issued_mtco2e": 95,
        "credits_retired_mtco2e": 62,
    },
    "art6_itmo": {
        "name": "Article 6 International Registry",
        "abbreviation": "ITMO",
        "body": "UNFCCC Article 6 Supervisory Body",
        "registry_url": "https://unfccc.int/process-and-meetings/the-paris-agreement/article-6",
        "serial_format": "ITMO-{country_code}-{year}-{serial}",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "version": "Paris Agreement 2015",
        "projects_registered": 45,
        "credits_issued_mtco2e": 12,
        "credits_retired_mtco2e": 3,
        "corresponding_adjustment_required": True,
    },
}

# ---------------------------------------------------------------------------
# Reference Data — CORSIA Eligible Programmes
# ---------------------------------------------------------------------------

CORSIA_PROGRAMMES: list[dict[str, Any]] = [
    {
        "programme": "Verra VCS",
        "body": "Verra",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": True,
        "url": "https://www.icao.int/environmental-protection/CORSIA",
    },
    {
        "programme": "Gold Standard",
        "body": "Gold Standard Foundation",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": True,
        "url": "https://www.goldstandard.org/resources/corsia",
    },
    {
        "programme": "American Carbon Registry (ACR)",
        "body": "Winrock International",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": True,
        "url": "https://americancarbonregistry.org/carbon-accounting/corsia",
    },
    {
        "programme": "Climate Action Reserve (CAR)",
        "body": "Climate Action Reserve",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": True,
        "url": "https://www.climateactionreserve.org/how/corsia/",
    },
    {
        "programme": "Social Carbon Standard",
        "body": "Ecologica Institute",
        "icao_approved_cycle": "2021-2023",
        "category_level_assessment": False,
        "note": "Approved for 2021-2023 pilot phase; 2024-2026 pending re-approval",
        "url": "https://socialcarbon.org",
    },
    {
        "programme": "REDD+ via UNFCCC",
        "body": "UNFCCC",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": False,
        "note": "Government-to-government REDD+ results only under Warsaw Framework",
        "url": "https://unfccc.int/topics/land-use/workstreams/redd",
    },
    {
        "programme": "Global Carbon Council (GCC)",
        "body": "QCBS / Gulf States",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": False,
        "note": "Regional programme primarily covering GCC member states",
        "url": "https://globalcarboncouncil.com",
    },
    {
        "programme": "Architecture for REDD+ Transactions (ART TREES)",
        "body": "Architecture for REDD+ Transactions",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": True,
        "note": "Jurisdictional-level REDD+ credits; high additionality requirements",
        "url": "https://www.artredd.org",
    },
    {
        "programme": "China GHG Voluntary Emission Reduction Program (CCER)",
        "body": "China NDRC / MEE",
        "icao_approved_cycle": "2024-2026",
        "category_level_assessment": False,
        "note": "Chinese domestic standard; restricted to Chinese carriers for CORSIA compliance",
        "url": "https://www.ccchina.org.cn",
    },
]

# ---------------------------------------------------------------------------
# Reference Data — Permanence risk by project type
# ---------------------------------------------------------------------------

PERMANENCE_PROFILES: dict[str, dict[str, Any]] = {
    "geological_storage": {
        "storage_type": "geological",
        "durability_years": 10000,
        "durability_label": "≥10,000 years",
        "reversal_risk": "negligible",
        "reversal_risk_score": 0.02,
        "examples": ["DACCS", "enhanced mineralisation", "deep saline aquifer injection"],
        "permanence_score": 0.98,
    },
    "deep_ocean": {
        "storage_type": "geological",
        "durability_years": 5000,
        "durability_label": "1,000-10,000 years",
        "reversal_risk": "very_low",
        "reversal_risk_score": 0.05,
        "examples": ["ocean alkalinity enhancement", "deep ocean biomass sinking"],
        "permanence_score": 0.90,
    },
    "mineral_carbonation": {
        "storage_type": "technological",
        "durability_years": 1000,
        "durability_label": "100-1,000 years",
        "reversal_risk": "low",
        "reversal_risk_score": 0.08,
        "examples": ["ex-situ mineral carbonation", "concrete curing with CO2"],
        "permanence_score": 0.85,
    },
    "bioenergy_ccs": {
        "storage_type": "technological",
        "durability_years": 500,
        "durability_label": "50-300 years",
        "reversal_risk": "low",
        "reversal_risk_score": 0.10,
        "examples": ["BECCS power plants", "BECCS industry"],
        "permanence_score": 0.82,
    },
    "biochar": {
        "storage_type": "biological_enhanced",
        "durability_years": 200,
        "durability_label": "50-300 years",
        "reversal_risk": "low_moderate",
        "reversal_risk_score": 0.15,
        "examples": ["biochar soil application", "biochar building materials"],
        "permanence_score": 0.75,
    },
    "blue_carbon": {
        "storage_type": "biological",
        "durability_years": 100,
        "durability_label": "20-100 years",
        "reversal_risk": "moderate",
        "reversal_risk_score": 0.25,
        "examples": ["mangrove restoration", "seagrass restoration", "tidal marsh"],
        "permanence_score": 0.65,
    },
    "redd_plus": {
        "storage_type": "biological",
        "durability_years": 50,
        "durability_label": "20-100 years",
        "reversal_risk": "moderate_high",
        "reversal_risk_score": 0.30,
        "examples": ["avoided deforestation", "REDD+", "IFM", "avoided conversion"],
        "permanence_score": 0.60,
    },
    "afforestation_reforestation": {
        "storage_type": "biological",
        "durability_years": 40,
        "durability_label": "20-80 years",
        "reversal_risk": "high",
        "reversal_risk_score": 0.35,
        "examples": ["A/R CDM", "reforestation", "afforestation", "VCS A/R"],
        "permanence_score": 0.55,
    },
    "soil_carbon": {
        "storage_type": "biological",
        "durability_years": 30,
        "durability_label": "10-50 years",
        "reversal_risk": "high",
        "reversal_risk_score": 0.40,
        "examples": ["regenerative agriculture", "no-till", "cover crops", "agroforestry"],
        "permanence_score": 0.50,
    },
    "renewable_energy": {
        "storage_type": "avoidance",
        "durability_years": 0,
        "durability_label": "Avoidance — no physical storage",
        "reversal_risk": "none",
        "reversal_risk_score": 0.05,
        "examples": ["solar PV", "wind", "run-of-river hydro", "geothermal"],
        "permanence_score": 0.85,
        "note": "Not removal; reversal risk reflects additionality concerns for mature technologies",
    },
    "cookstoves": {
        "storage_type": "avoidance",
        "durability_years": 0,
        "durability_label": "Avoidance — no physical storage",
        "reversal_risk": "low",
        "reversal_risk_score": 0.10,
        "examples": ["improved cookstoves", "clean cooking fuels"],
        "permanence_score": 0.75,
    },
    "methane_avoidance": {
        "storage_type": "avoidance",
        "durability_years": 0,
        "durability_label": "Avoidance — no physical storage",
        "reversal_risk": "low",
        "reversal_risk_score": 0.08,
        "examples": ["landfill gas capture", "coal mine methane", "rice cultivation"],
        "permanence_score": 0.80,
    },
    "industrial_energy_efficiency": {
        "storage_type": "avoidance",
        "durability_years": 0,
        "durability_label": "Avoidance — no physical storage",
        "reversal_risk": "very_low",
        "reversal_risk_score": 0.05,
        "examples": ["industrial process efficiency", "fuel switching", "waste heat recovery"],
        "permanence_score": 0.88,
    },
    "direct_air_capture": {
        "storage_type": "geological",
        "durability_years": 10000,
        "durability_label": "≥10,000 years (geological injection)",
        "reversal_risk": "negligible",
        "reversal_risk_score": 0.02,
        "examples": ["DAC + geological storage", "DACCS point source"],
        "permanence_score": 0.98,
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Price Benchmarks
# ---------------------------------------------------------------------------

PRICE_BENCHMARKS: dict[str, dict[str, Any]] = {
    "geological_removal_daccs": {
        "project_type": "Direct Air Capture + Geological Storage (DACCS)",
        "storage_class": "geological_removal",
        "price_low_usd_t": 200,
        "price_mid_usd_t": 350,
        "price_high_usd_t": 500,
        "ccp_premium_pct": 10,
        "corsia_eligible": True,
        "registry": "verra_vcs / art6_itmo",
    },
    "bioenergy_ccs_removal": {
        "project_type": "Bioenergy with CCS (BECCS)",
        "storage_class": "technological_removal",
        "price_low_usd_t": 80,
        "price_mid_usd_t": 150,
        "price_high_usd_t": 300,
        "ccp_premium_pct": 10,
        "corsia_eligible": True,
        "registry": "verra_vcs / gold_standard",
    },
    "biochar_removal": {
        "project_type": "Biochar Soil Application",
        "storage_class": "biological_enhanced_removal",
        "price_low_usd_t": 80,
        "price_mid_usd_t": 130,
        "price_high_usd_t": 200,
        "ccp_premium_pct": 15,
        "corsia_eligible": True,
        "registry": "verra_vcs / gold_standard",
    },
    "blue_carbon_removal": {
        "project_type": "Blue Carbon (Mangrove / Seagrass / Salt Marsh)",
        "storage_class": "nature_based_removal",
        "price_low_usd_t": 20,
        "price_mid_usd_t": 45,
        "price_high_usd_t": 100,
        "ccp_premium_pct": 20,
        "corsia_eligible": True,
        "registry": "verra_vcs / gold_standard",
    },
    "redd_plus_avoidance": {
        "project_type": "REDD+ (Avoided Deforestation)",
        "storage_class": "nature_based_avoidance",
        "price_low_usd_t": 3,
        "price_mid_usd_t": 12,
        "price_high_usd_t": 30,
        "ccp_premium_pct": 50,
        "corsia_eligible": True,
        "registry": "verra_vcs / acr",
    },
    "afforestation_reforestation": {
        "project_type": "Afforestation / Reforestation",
        "storage_class": "nature_based_removal",
        "price_low_usd_t": 5,
        "price_mid_usd_t": 15,
        "price_high_usd_t": 35,
        "ccp_premium_pct": 30,
        "corsia_eligible": True,
        "registry": "verra_vcs / gold_standard / acr / car",
    },
    "soil_carbon": {
        "project_type": "Soil Carbon (Regenerative Agriculture)",
        "storage_class": "nature_based_removal",
        "price_low_usd_t": 5,
        "price_mid_usd_t": 18,
        "price_high_usd_t": 40,
        "ccp_premium_pct": 25,
        "corsia_eligible": True,
        "registry": "verra_vcs / acr / car",
    },
    "renewable_energy": {
        "project_type": "Renewable Energy (Solar / Wind / Hydro)",
        "storage_class": "avoidance",
        "price_low_usd_t": 2,
        "price_mid_usd_t": 5,
        "price_high_usd_t": 10,
        "ccp_premium_pct": 0,
        "corsia_eligible": True,
        "registry": "verra_vcs / gold_standard / acr",
        "note": "Low prices reflect additionality concerns for mature technology",
    },
    "cookstoves": {
        "project_type": "Improved Cookstoves / Clean Cooking",
        "storage_class": "avoidance",
        "price_low_usd_t": 4,
        "price_mid_usd_t": 10,
        "price_high_usd_t": 25,
        "ccp_premium_pct": 20,
        "corsia_eligible": True,
        "registry": "gold_standard / verra_vcs",
    },
    "landfill_methane": {
        "project_type": "Landfill Gas Capture / Methane Avoidance",
        "storage_class": "avoidance",
        "price_low_usd_t": 3,
        "price_mid_usd_t": 8,
        "price_high_usd_t": 18,
        "ccp_premium_pct": 10,
        "corsia_eligible": True,
        "registry": "verra_vcs / acr / car",
    },
    "industrial_efficiency": {
        "project_type": "Industrial Energy Efficiency / Fuel Switching",
        "storage_class": "avoidance",
        "price_low_usd_t": 3,
        "price_mid_usd_t": 7,
        "price_high_usd_t": 15,
        "ccp_premium_pct": 5,
        "corsia_eligible": True,
        "registry": "verra_vcs / gold_standard / car",
    },
    "art6_itmo_generic": {
        "project_type": "Article 6 ITMO (Corresponding Adjustment)",
        "storage_class": "art6_itmo",
        "price_low_usd_t": 10,
        "price_mid_usd_t": 30,
        "price_high_usd_t": 80,
        "ccp_premium_pct": 15,
        "corsia_eligible": True,
        "registry": "art6_itmo",
        "note": "Price includes corresponding adjustment premium vs non-CA credits",
    },
    "mineral_weathering": {
        "project_type": "Enhanced Weathering / Mineral Carbonation",
        "storage_class": "geological_removal",
        "price_low_usd_t": 50,
        "price_mid_usd_t": 100,
        "price_high_usd_t": 250,
        "ccp_premium_pct": 10,
        "corsia_eligible": False,
        "registry": "verra_vcs (methodology in development)",
    },
    "ocean_alkalinity": {
        "project_type": "Ocean Alkalinity Enhancement",
        "storage_class": "geological_removal",
        "price_low_usd_t": 100,
        "price_mid_usd_t": 200,
        "price_high_usd_t": 450,
        "ccp_premium_pct": 10,
        "corsia_eligible": False,
        "registry": "Not yet approved by major registries",
    },
    "art_trees_jurisdictional": {
        "project_type": "ART TREES Jurisdictional REDD+",
        "storage_class": "nature_based_avoidance",
        "price_low_usd_t": 8,
        "price_mid_usd_t": 20,
        "price_high_usd_t": 45,
        "ccp_premium_pct": 40,
        "corsia_eligible": True,
        "registry": "art",
    },
    "walhi_blue_nbs": {
        "project_type": "Nature-Based Solutions Bundle (Mixed)",
        "storage_class": "nature_based_mixed",
        "price_low_usd_t": 6,
        "price_mid_usd_t": 15,
        "price_high_usd_t": 35,
        "ccp_premium_pct": 25,
        "corsia_eligible": True,
        "registry": "verra_vcs",
    },
    "coal_mine_methane": {
        "project_type": "Coal Mine Methane Capture",
        "storage_class": "avoidance",
        "price_low_usd_t": 4,
        "price_mid_usd_t": 9,
        "price_high_usd_t": 20,
        "ccp_premium_pct": 5,
        "corsia_eligible": True,
        "registry": "acr / car",
    },
    "rice_cultivation_methane": {
        "project_type": "Rice Cultivation Methane Reduction",
        "storage_class": "avoidance",
        "price_low_usd_t": 3,
        "price_mid_usd_t": 7,
        "price_high_usd_t": 15,
        "ccp_premium_pct": 10,
        "corsia_eligible": True,
        "registry": "verra_vcs / gold_standard",
    },
    "cement_ccs": {
        "project_type": "Cement / Industrial CCS (Point Source)",
        "storage_class": "technological_removal",
        "price_low_usd_t": 60,
        "price_mid_usd_t": 120,
        "price_high_usd_t": 250,
        "ccp_premium_pct": 10,
        "corsia_eligible": False,
        "registry": "verra_vcs (in development)",
    },
}

# ---------------------------------------------------------------------------
# Additionality scoring by methodology category
# ---------------------------------------------------------------------------

ADDITIONALITY_PROFILES: dict[str, float] = {
    "redd_plus": 0.60,
    "afforestation_reforestation": 0.65,
    "blue_carbon": 0.75,
    "soil_carbon": 0.65,
    "cookstoves": 0.70,
    "renewable_energy": 0.50,
    "methane_avoidance": 0.80,
    "industrial_energy_efficiency": 0.72,
    "geological_storage": 0.92,
    "bioenergy_ccs": 0.85,
    "biochar": 0.80,
    "direct_air_capture": 0.98,
    "mineral_weathering": 0.90,
    "ocean_alkalinity": 0.88,
}

# ---------------------------------------------------------------------------
# Quality tier thresholds
# ---------------------------------------------------------------------------

QUALITY_TIERS: dict[str, dict[str, Any]] = {
    "A": {
        "tier": "A",
        "label": "Premium",
        "ccp_score_min": 0.80,
        "permanence_score_min": 0.80,
        "additionality_min": 0.80,
        "description": "Highest integrity; CCP-label eligible; suitable for VCMI Platinum",
        "vcmi_eligible": ["platinum", "gold", "silver"],
        "price_premium_pct": 40,
    },
    "B": {
        "tier": "B",
        "label": "High",
        "ccp_score_min": 0.65,
        "permanence_score_min": 0.65,
        "additionality_min": 0.65,
        "description": "High integrity; likely CORSIA eligible; suitable for VCMI Gold/Silver",
        "vcmi_eligible": ["gold", "silver"],
        "price_premium_pct": 20,
    },
    "C": {
        "tier": "C",
        "label": "Standard",
        "ccp_score_min": 0.50,
        "permanence_score_min": 0.50,
        "additionality_min": 0.50,
        "description": "Standard quality; registered credit; limited use for VCMI claims",
        "vcmi_eligible": ["silver"],
        "price_premium_pct": 0,
    },
    "D": {
        "tier": "D",
        "label": "Below Standard",
        "ccp_score_min": 0.0,
        "permanence_score_min": 0.0,
        "additionality_min": 0.0,
        "description": "Below standard; significant integrity concerns; not recommended for VCMI claims",
        "vcmi_eligible": [],
        "price_premium_pct": -30,
    },
}


# ---------------------------------------------------------------------------
# Core computation helpers
# ---------------------------------------------------------------------------

def _compute_icvcm_criteria_scores(
    registry: str,
    methodology: str,
    project_type: str,
    vintage_year: int,
    has_vvb_accreditation: bool,
    monitoring_frequency_years: int,
    public_documentation: bool,
    fpic_completed: Optional[bool],
) -> dict[str, dict[str, Any]]:
    """Score all 10 ICVCM CCP criteria."""
    registry_base = {
        "verra_vcs": 0.82,
        "gold_standard": 0.88,
        "acr": 0.80,
        "car": 0.78,
        "art6_itmo": 0.85,
    }.get(registry, 0.70)

    vintage_penalty = max(0, (2015 - vintage_year) * 0.02) if vintage_year < 2015 else 0

    results: dict[str, dict[str, Any]] = {}
    for code, criterion in ICVCM_CRITERIA.items():
        base = registry_base
        pillar = criterion["pillar"]

        if pillar == "Governance":
            score = base - vintage_penalty
            if not public_documentation:
                score -= 0.10
            if not has_vvb_accreditation and code == "C3":
                score -= 0.20
        elif pillar == "Emissions Impact":
            perm_profile = PERMANENCE_PROFILES.get(project_type, {})
            if code == "C4":
                score = ADDITIONALITY_PROFILES.get(project_type, 0.65)
            elif code == "C5":
                score = perm_profile.get("permanence_score", 0.60) - vintage_penalty
            elif code == "C6":
                score = base * (1 - (monitoring_frequency_years - 1) * 0.04)
            else:  # C7 No double counting
                score = 0.90 if registry == "art6_itmo" else (base - 0.05)
        else:  # Sustainable Development
            score = base - vintage_penalty
            if code == "C10" and fpic_completed is False:
                score -= 0.20
            if code == "C10" and fpic_completed is True:
                score = min(1.0, score + 0.10)

        score = max(0.0, min(1.0, score))
        threshold = criterion["ccp_threshold"]
        results[code] = {
            "criterion_id": code,
            "title": criterion["title"],
            "pillar": pillar,
            "weight": criterion["weight"],
            "score": round(score, 4),
            "threshold": threshold,
            "meets_threshold": score >= threshold,
            "weighted_contribution": round(score * criterion["weight"], 4),
        }
    return results


def _derive_ccp_composite(criteria_scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-criterion results into a CCP composite score and label."""
    total_weighted = sum(v["weighted_contribution"] for v in criteria_scores.values())
    total_weight = sum(v["weight"] for v in criteria_scores.values())
    composite = total_weighted / total_weight if total_weight > 0 else 0

    passed = sum(1 for v in criteria_scores.values() if v["meets_threshold"])
    total = len(criteria_scores)
    blocking_failures = [
        v["criterion_id"]
        for v in criteria_scores.values()
        if not v["meets_threshold"]
        and v["criterion_id"] in ("C4", "C5", "C6", "C7")  # Emissions Impact must pass
    ]
    ccp_eligible = (passed == total) and len(blocking_failures) == 0

    return {
        "ccp_composite_score": round(composite, 4),
        "criteria_passed": passed,
        "criteria_total": total,
        "blocking_failures": blocking_failures,
        "ccp_label_eligible": ccp_eligible,
    }


def _score_oxford_principles(
    reduction_pct_of_portfolio: float,
    removal_pct_of_portfolio: float,
    geological_removal_pct: float,
    price_usd_t: float,
    sbti_validated: bool,
) -> dict[str, Any]:
    """Score the 4 Oxford Offsetting Principles."""

    def _band(value: float, bands: list[tuple[float, float]]) -> float:
        for threshold, result in bands:
            if value >= threshold:
                return result
        return 0.0

    p1 = _band(
        1 - (reduction_pct_of_portfolio / 100),
        [(0.90, 1.0), (0.75, 0.75), (0.50, 0.50), (0.25, 0.25)],
    )
    if sbti_validated:
        p1 = min(1.0, p1 + 0.15)

    p2 = _band(
        removal_pct_of_portfolio / 100,
        [(0.50, 1.0), (0.25, 0.75), (0.10, 0.50), (0.01, 0.25)],
    )

    p3 = _band(
        geological_removal_pct / 100,
        [(0.25, 1.0), (0.10, 0.75), (0.05, 0.50), (0.01, 0.25)],
    )

    # P4: proxy by price and credit quality
    price_score = _band(price_usd_t, [(100, 1.0), (30, 0.75), (10, 0.50), (5, 0.25)])
    p4 = (price_score + (0.20 if sbti_validated else 0)) / 1.0
    p4 = min(1.0, p4)

    composite = (p1 + p2 + p3 + p4) / 4
    return {
        "P1_reduction_priority": round(p1, 4),
        "P2_shift_to_removals": round(p2, 4),
        "P3_long_lived_storage": round(p3, 4),
        "P4_market_integrity": round(p4, 4),
        "oxford_composite": round(composite, 4),
        "oxford_principles_met": sum(
            1 for v in [p1, p2, p3, p4] if v >= 0.50
        ),
    }


def _derive_vcmi_claim(
    sbti_near_term: bool,
    sbti_long_term: bool,
    residual_emissions_pct: float,
    ccp_label_credits: bool,
    has_assurance: bool,
) -> dict[str, Any]:
    """Determine highest achievable VCMI claim tier."""
    if not sbti_near_term:
        return {"claim_tier": "no_claim", "reason": "SBTi near-term target not validated"}

    if ccp_label_credits and sbti_long_term and residual_emissions_pct <= 10:
        tier = "platinum"
    elif sbti_long_term and residual_emissions_pct <= 20:
        tier = "gold"
    elif residual_emissions_pct <= 40:
        tier = "silver"
    else:
        tier = "no_claim"

    tier_data = VCMI_CLAIM_TIERS.get(tier, VCMI_CLAIM_TIERS["no_claim"])
    return {
        "claim_tier": tier,
        "label": tier_data["label"],
        "description": tier_data["description"],
        "residual_emissions_pct": residual_emissions_pct,
        "sbti_near_term_validated": sbti_near_term,
        "sbti_long_term_validated": sbti_long_term,
        "ccp_label_credits_used": ccp_label_credits,
        "assurance_obtained": has_assurance,
        "annual_checklist_required": tier != "no_claim",
    }


def _determine_quality_tier(
    ccp_composite: float,
    permanence_score: float,
    additionality_score: float,
) -> dict[str, Any]:
    """Map scores to A/B/C/D quality tier."""
    combined = (ccp_composite * 0.50) + (permanence_score * 0.25) + (additionality_score * 0.25)
    if combined >= QUALITY_TIERS["A"]["ccp_score_min"]:
        tier_key = "A"
    elif combined >= QUALITY_TIERS["B"]["ccp_score_min"]:
        tier_key = "B"
    elif combined >= QUALITY_TIERS["C"]["ccp_score_min"]:
        tier_key = "C"
    else:
        tier_key = "D"
    t = QUALITY_TIERS[tier_key]
    return {
        "quality_tier": tier_key,
        "quality_label": t["label"],
        "combined_quality_score": round(combined, 4),
        "vcmi_eligible_tiers": t["vcmi_eligible"],
        "price_premium_pct": t["price_premium_pct"],
        "description": t["description"],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assess_vcm_integrity(
    project_id: str,
    registry: str,
    methodology: str,
    project_type: str,
    vintage_year: int,
    volume_tco2e: float,
    price_usd_t: float,
    has_vvb_accreditation: bool = True,
    monitoring_frequency_years: int = 1,
    public_documentation: bool = True,
    fpic_completed: Optional[bool] = None,
    sbti_near_term: bool = False,
    sbti_long_term: bool = False,
    residual_emissions_pct: float = 50.0,
    reduction_pct_of_portfolio: float = 70.0,
    removal_pct_of_portfolio: float = 10.0,
    geological_removal_pct: float = 2.0,
    has_assurance: bool = False,
    corresponding_adjustment: bool = False,
) -> dict[str, Any]:
    """
    Full VCM integrity assessment for a single carbon credit project.

    Parameters
    ----------
    project_id : str
        Unique project identifier (e.g. VCS-1234).
    registry : str
        Registry key: verra_vcs | gold_standard | acr | car | art6_itmo.
    methodology : str
        Methodology code (e.g. VM0007, GS TPDDTEC).
    project_type : str
        Project type key (e.g. redd_plus, cookstoves, geological_storage).
    vintage_year : int
        Year the emissions reductions were generated.
    volume_tco2e : float
        Volume in tonnes CO2e.
    price_usd_t : float
        Transaction / purchase price in USD/tCO2e.
    has_vvb_accreditation : bool
        Whether the validating/verifying body is accredited.
    monitoring_frequency_years : int
        Years between monitoring reports (1 = annual).
    public_documentation : bool
        Whether full project documentation is publicly available.
    fpic_completed : Optional[bool]
        Free Prior and Informed Consent completed (relevant for IPLC-affected projects).
    sbti_near_term : bool
        Entity has SBTi-validated near-term target.
    sbti_long_term : bool
        Entity has SBTi-validated long-term (net-zero) target.
    residual_emissions_pct : float
        Residual emissions as % above SBTi pathway (used for VCMI claim tier).
    reduction_pct_of_portfolio : float
        % of portfolio GHG addressed by direct reductions (used for Oxford P1).
    removal_pct_of_portfolio : float
        % of offset portfolio that are removals (used for Oxford P2).
    geological_removal_pct : float
        % of removals that use geological/long-lived storage (used for Oxford P3).
    has_assurance : bool
        Whether emissions inventory has independent assurance.
    corresponding_adjustment : bool
        Whether a corresponding adjustment has been applied (Art 6).

    Returns
    -------
    dict
        Comprehensive integrity assessment with ICVCM criteria, VCMI claim, Oxford scores,
        permanence profile, quality tier, CORSIA eligibility, and Article 6 status.
    """
    now = datetime.utcnow().isoformat() + "Z"

    # --- ICVCM CCP criteria scoring ---
    criteria_scores = _compute_icvcm_criteria_scores(
        registry=registry,
        methodology=methodology,
        project_type=project_type,
        vintage_year=vintage_year,
        has_vvb_accreditation=has_vvb_accreditation,
        monitoring_frequency_years=monitoring_frequency_years,
        public_documentation=public_documentation,
        fpic_completed=fpic_completed,
    )
    ccp_result = _derive_ccp_composite(criteria_scores)
    ccp_composite = ccp_result["ccp_composite_score"]

    # --- Permanence profile ---
    perm_profile = PERMANENCE_PROFILES.get(
        project_type,
        PERMANENCE_PROFILES.get("redd_plus"),
    )
    permanence_score = perm_profile["permanence_score"]
    leakage_risk_pct = round(perm_profile["reversal_risk_score"] * 100, 1)

    # --- Additionality ---
    additionality_score = ADDITIONALITY_PROFILES.get(project_type, 0.65)

    # --- Registry profile ---
    reg_profile = REGISTRY_PROFILES.get(registry, {})
    corsia_eligible = reg_profile.get("corsia_eligible", False)

    # --- Article 6 ---
    art6_eligible = registry == "art6_itmo"
    art6_status = {
        "eligible": art6_eligible,
        "corresponding_adjustment_applied": corresponding_adjustment,
        "ndc_boundary_concern": not corresponding_adjustment and registry != "art6_itmo",
        "itmo_note": (
            "Corresponding adjustment confirmed — avoids double counting at sovereign level"
            if corresponding_adjustment
            else "No corresponding adjustment — potential sovereign double count under Paris Art 4"
        ),
    }

    # --- MRV quality score ---
    mrv_quality = (
        (0.30 if monitoring_frequency_years <= 1 else max(0.10, 0.30 - (monitoring_frequency_years - 1) * 0.05))
        + (0.30 if public_documentation else 0.10)
        + (0.25 if has_vvb_accreditation else 0.05)
        + (0.15 if vintage_year >= 2020 else max(0.05, 0.15 - (2020 - vintage_year) * 0.01))
    )
    mrv_quality = round(min(1.0, mrv_quality), 4)

    # --- Oxford Principles ---
    oxford = _score_oxford_principles(
        reduction_pct_of_portfolio=reduction_pct_of_portfolio,
        removal_pct_of_portfolio=removal_pct_of_portfolio,
        geological_removal_pct=geological_removal_pct,
        price_usd_t=price_usd_t,
        sbti_validated=sbti_near_term,
    )

    # --- VCMI claim ---
    vcmi = _derive_vcmi_claim(
        sbti_near_term=sbti_near_term,
        sbti_long_term=sbti_long_term,
        residual_emissions_pct=residual_emissions_pct,
        ccp_label_credits=ccp_result["ccp_label_eligible"],
        has_assurance=has_assurance,
    )

    # --- Quality tier ---
    quality = _determine_quality_tier(ccp_composite, permanence_score, additionality_score)

    # --- Price benchmarks ---
    bench_key = project_type if project_type in PRICE_BENCHMARKS else None
    benchmark = PRICE_BENCHMARKS.get(bench_key, {}) if bench_key else {}
    price_assessment = {
        "price_provided_usd_t": price_usd_t,
        "benchmark_mid_usd_t": benchmark.get("price_mid_usd_t"),
        "benchmark_range": (
            f"${benchmark.get('price_low_usd_t', 'N/A')} - ${benchmark.get('price_high_usd_t', 'N/A')}"
            if benchmark
            else "N/A"
        ),
        "price_vs_benchmark": (
            "above_benchmark"
            if benchmark and price_usd_t > benchmark.get("price_high_usd_t", 0)
            else (
                "below_benchmark"
                if benchmark and price_usd_t < benchmark.get("price_low_usd_t", 999999)
                else "within_benchmark"
            )
        ),
    }

    return {
        "assessment_id": f"VCM-{project_id}-{vintage_year}",
        "generated_at": now,
        "project_id": project_id,
        "registry": registry,
        "registry_name": reg_profile.get("name", registry),
        "methodology": methodology,
        "project_type": project_type,
        "vintage_year": vintage_year,
        "volume_tco2e": volume_tco2e,
        "icvcm_criteria_scores": criteria_scores,
        "icvcm_ccp_summary": ccp_result,
        "permanence_profile": perm_profile,
        "leakage_risk_pct": leakage_risk_pct,
        "additionality_score": additionality_score,
        "mrv_quality_score": mrv_quality,
        "oxford_principles": oxford,
        "vcmi_claim": vcmi,
        "quality_assessment": quality,
        "corsia_eligibility": {
            "eligible": corsia_eligible,
            "programme": reg_profile.get("name"),
            "cycle": "2024-2026",
        },
        "article6_status": art6_status,
        "price_assessment": price_assessment,
        "recommendations": _generate_recommendations(ccp_result, quality, vcmi, art6_status),
    }


def _generate_recommendations(
    ccp_result: dict[str, Any],
    quality: dict[str, Any],
    vcmi: dict[str, Any],
    art6_status: dict[str, Any],
) -> list[str]:
    """Generate actionable recommendations based on assessment results."""
    recs: list[str] = []
    if not ccp_result["ccp_label_eligible"]:
        failing = ccp_result["blocking_failures"]
        if failing:
            recs.append(
                f"Resolve blocking CCP criteria failures ({', '.join(failing)}) to achieve CCP label eligibility."
            )
    if quality["quality_tier"] in ("C", "D"):
        recs.append("Consider higher-quality replacement credits (Tier A/B) for corporate sustainability claims.")
    if vcmi["claim_tier"] == "no_claim":
        recs.append("Validate an SBTi near-term target to become eligible for VCMI Silver/Gold/Platinum claims.")
    if art6_status["ndc_boundary_concern"]:
        recs.append(
            "Apply a corresponding adjustment per Art 6.2/6.4 to prevent sovereign-level double counting."
        )
    if not recs:
        recs.append("Credit meets high-integrity standards. Continue current practices.")
    return recs


def screen_registry_entry(
    registry_name: str,
    serial_number: str,
    project_type: str = "redd_plus",
    vintage_year: int = 2022,
    volume_tco2e: float = 1000.0,
    retirement_status: str = "active",
    beneficiary: Optional[str] = None,
) -> dict[str, Any]:
    """
    Screen a registry entry by serial number for basic integrity checks.

    Parameters
    ----------
    registry_name : str
        Registry identifier (verra_vcs, gold_standard, acr, car, art6_itmo).
    serial_number : str
        Registry serial / batch number.
    project_type : str
        Project type category.
    vintage_year : int
        Vintage year.
    volume_tco2e : float
        Volume in tCO2e.
    retirement_status : str
        active | retired | cancelled | suspended.
    beneficiary : Optional[str]
        Named beneficiary for retirement (if any).

    Returns
    -------
    dict
        Registry entry screening result with integrity flags and CORSIA status.
    """
    reg_profile = REGISTRY_PROFILES.get(registry_name, {})
    perm_profile = PERMANENCE_PROFILES.get(project_type, {})

    flags: list[str] = []
    if retirement_status == "retired":
        flags.append("ALREADY_RETIRED — credit cannot be resold or re-used")
    if retirement_status == "cancelled":
        flags.append("CANCELLED — credit invalidated by registry")
    if retirement_status == "suspended":
        flags.append("SUSPENDED — project under investigation; do not purchase")
    if vintage_year < 2016:
        flags.append("PRE-2016_VINTAGE — additionality and MRV standards may be outdated")
    if perm_profile.get("reversal_risk_score", 0) > 0.30:
        flags.append("HIGH_REVERSAL_RISK — biological storage with permanence concerns")

    corsia_ok = reg_profile.get("corsia_eligible", False) and retirement_status == "active"

    return {
        "serial_number": serial_number,
        "registry": registry_name,
        "registry_name": reg_profile.get("name", registry_name),
        "project_type": project_type,
        "vintage_year": vintage_year,
        "volume_tco2e": volume_tco2e,
        "retirement_status": retirement_status,
        "beneficiary": beneficiary,
        "corsia_eligible": corsia_ok,
        "ccp_programme_eligible": reg_profile.get("ccp_label_eligible", False),
        "integrity_flags": flags,
        "flag_count": len(flags),
        "screen_result": "FAIL" if any(f.startswith("CANCELLED") or f.startswith("SUSPENDED") or f.startswith("ALREADY_RETIRED") for f in flags) else ("WARNING" if flags else "PASS"),
        "permanence_durability": perm_profile.get("durability_label", "Unknown"),
    }


def get_vcm_benchmarks() -> dict[str, Any]:
    """
    Return all VCM price benchmark data organised by storage class.

    Returns
    -------
    dict
        Price benchmarks keyed by project type with storage class groupings.
    """
    by_class: dict[str, list[dict[str, Any]]] = {}
    for key, bench in PRICE_BENCHMARKS.items():
        cls = bench.get("storage_class", "other")
        by_class.setdefault(cls, []).append({**bench, "key": key})

    return {
        "benchmarks_by_project_type": PRICE_BENCHMARKS,
        "benchmarks_by_storage_class": by_class,
        "ccp_premium_note": (
            "CCP-labelled credits command a premium of 5-50% depending on project type. "
            "Geological removal premiums are lower (10%) as quality is already high. "
            "Nature-based avoidance (REDD+) CCP premiums are higher (50%) due to baseline quality variance."
        ),
        "currency": "USD",
        "price_basis": "tCO2e",
        "vintage_note": "Prices reflect 2023-2024 spot market data. Forward prices for 2030+ removal credits may be 2-5× higher.",
    }
