"""
Critical Minerals & Transition Metals Risk Engine — E93
Standards: IEA Critical Minerals 2024, EU Critical Raw Materials Act 2024/1252,
IRMA Standard for Responsible Mining v1.0, OECD Due Diligence Guidance for
Responsible Mineral Supply Chains (5-step framework), Conflict Minerals (Dodd-Frank
Section 1502, EU Regulation 2017/821).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Reference Data — IEA Critical Minerals 2024
# ---------------------------------------------------------------------------

IEA_CRITICAL_MINERALS_2024: Dict[str, Dict] = {
    "lithium": {
        "iea_criticality_composite": 88,
        "demand_growth_score": 95,
        "supply_concentration_hhi": 7200,
        "top3_country_share_pct": {"Australia": 47, "Chile": 26, "China": 15},
        "substitutability_score": 18,
        "geopolitical_risk_score": 62,
        "key_applications": ["EV batteries", "grid storage", "consumer electronics"],
        "transition_technology_dependence": "critical",
        "iea_demand_growth_2023_2040_x": 6.5,
        "recycling_rate_pct": 5,
        "primary_ore": "spodumene / brine",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "cobalt": {
        "iea_criticality_composite": 91,
        "demand_growth_score": 72,
        "supply_concentration_hhi": 8900,
        "top3_country_share_pct": {"DRC": 73, "Russia": 4, "Australia": 4},
        "substitutability_score": 22,
        "geopolitical_risk_score": 88,
        "key_applications": ["NMC/NCA batteries", "superalloys", "hard metals"],
        "transition_technology_dependence": "critical",
        "iea_demand_growth_2023_2040_x": 3.8,
        "recycling_rate_pct": 32,
        "primary_ore": "copper-cobalt laterite (DRC)",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "nickel": {
        "iea_criticality_composite": 74,
        "demand_growth_score": 68,
        "supply_concentration_hhi": 2800,
        "top3_country_share_pct": {"Indonesia": 48, "Philippines": 11, "Russia": 9},
        "substitutability_score": 38,
        "geopolitical_risk_score": 55,
        "key_applications": ["NMC/NCA batteries", "stainless steel", "alloys"],
        "transition_technology_dependence": "high",
        "iea_demand_growth_2023_2040_x": 4.2,
        "recycling_rate_pct": 57,
        "primary_ore": "laterite / sulphide",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "copper": {
        "iea_criticality_composite": 71,
        "demand_growth_score": 62,
        "supply_concentration_hhi": 1900,
        "top3_country_share_pct": {"Chile": 27, "Peru": 11, "DRC": 10},
        "substitutability_score": 42,
        "geopolitical_risk_score": 48,
        "key_applications": ["electric motors", "wiring", "charging infrastructure", "wind turbines"],
        "transition_technology_dependence": "high",
        "iea_demand_growth_2023_2040_x": 2.1,
        "recycling_rate_pct": 43,
        "primary_ore": "sulphide / oxide porphyry",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "manganese": {
        "iea_criticality_composite": 65,
        "demand_growth_score": 58,
        "supply_concentration_hhi": 3100,
        "top3_country_share_pct": {"South Africa": 33, "Gabon": 22, "Australia": 17},
        "substitutability_score": 30,
        "geopolitical_risk_score": 52,
        "key_applications": ["LMFP batteries", "stainless steel", "fertilisers"],
        "transition_technology_dependence": "medium",
        "iea_demand_growth_2023_2040_x": 3.1,
        "recycling_rate_pct": 38,
        "primary_ore": "oxide / carbonate",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "graphite": {
        "iea_criticality_composite": 82,
        "demand_growth_score": 88,
        "supply_concentration_hhi": 7800,
        "top3_country_share_pct": {"China": 65, "Mozambique": 12, "Madagascar": 8},
        "substitutability_score": 15,
        "geopolitical_risk_score": 78,
        "key_applications": ["lithium-ion battery anodes", "refractories", "lubricants"],
        "transition_technology_dependence": "critical",
        "iea_demand_growth_2023_2040_x": 5.8,
        "recycling_rate_pct": 8,
        "primary_ore": "natural flake graphite",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "rare_earths": {
        "iea_criticality_composite": 86,
        "demand_growth_score": 76,
        "supply_concentration_hhi": 8500,
        "top3_country_share_pct": {"China": 62, "USA": 13, "Australia": 8},
        "substitutability_score": 12,
        "geopolitical_risk_score": 82,
        "key_applications": ["permanent magnets (EV motors, wind turbines)", "fluorescent lighting", "catalysts"],
        "transition_technology_dependence": "critical",
        "iea_demand_growth_2023_2040_x": 4.5,
        "recycling_rate_pct": 2,
        "primary_ore": "bastnaesite / monazite / ion-adsorption clays",
        "iea_report_page": "IEA CRM 2024 Chapter 4",
    },
    "silicon_metal": {
        "iea_criticality_composite": 68,
        "demand_growth_score": 74,
        "supply_concentration_hhi": 3600,
        "top3_country_share_pct": {"China": 68, "Brazil": 8, "Norway": 5},
        "substitutability_score": 28,
        "geopolitical_risk_score": 70,
        "key_applications": ["solar PV wafers", "semiconductors", "aluminium alloys", "silicon anode batteries"],
        "transition_technology_dependence": "high",
        "iea_demand_growth_2023_2040_x": 3.9,
        "recycling_rate_pct": 20,
        "primary_ore": "quartz smelted with carbon",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "titanium": {
        "iea_criticality_composite": 62,
        "demand_growth_score": 48,
        "supply_concentration_hhi": 2200,
        "top3_country_share_pct": {"China": 35, "South Africa": 22, "Australia": 18},
        "substitutability_score": 35,
        "geopolitical_risk_score": 45,
        "key_applications": ["aerospace alloys", "pigments", "armour", "hydrogen electrolysers"],
        "transition_technology_dependence": "medium",
        "iea_demand_growth_2023_2040_x": 1.8,
        "recycling_rate_pct": 28,
        "primary_ore": "rutile / ilmenite",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "platinum_group_metals": {
        "iea_criticality_composite": 79,
        "demand_growth_score": 55,
        "supply_concentration_hhi": 7100,
        "top3_country_share_pct": {"South Africa": 71, "Russia": 12, "Zimbabwe": 6},
        "substitutability_score": 25,
        "geopolitical_risk_score": 76,
        "key_applications": ["fuel cell catalysts (PEMFC)", "hydrogen electrolysers", "autocatalysts"],
        "transition_technology_dependence": "high",
        "iea_demand_growth_2023_2040_x": 2.8,
        "recycling_rate_pct": 65,
        "primary_ore": "palladium / platinum / iridium in UG2 reef",
        "iea_report_page": "IEA CRM 2024 Chapter 4",
    },
    "indium": {
        "iea_criticality_composite": 77,
        "demand_growth_score": 62,
        "supply_concentration_hhi": 4800,
        "top3_country_share_pct": {"China": 57, "South Korea": 12, "Japan": 10},
        "substitutability_score": 20,
        "geopolitical_risk_score": 68,
        "key_applications": ["thin-film solar (CIGS)", "ITO transparent electrodes", "semiconductors"],
        "transition_technology_dependence": "high",
        "iea_demand_growth_2023_2040_x": 2.5,
        "recycling_rate_pct": 40,
        "primary_ore": "by-product of zinc smelting",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "gallium": {
        "iea_criticality_composite": 83,
        "demand_growth_score": 78,
        "supply_concentration_hhi": 9200,
        "top3_country_share_pct": {"China": 80, "Russia": 5, "Japan": 5},
        "substitutability_score": 14,
        "geopolitical_risk_score": 85,
        "key_applications": ["GaN semiconductors", "III-V solar cells", "LEDs", "5G RF chips"],
        "transition_technology_dependence": "critical",
        "iea_demand_growth_2023_2040_x": 4.8,
        "recycling_rate_pct": 25,
        "primary_ore": "by-product of bauxite / zinc processing",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "germanium": {
        "iea_criticality_composite": 81,
        "demand_growth_score": 65,
        "supply_concentration_hhi": 7600,
        "top3_country_share_pct": {"China": 59, "Russia": 8, "Canada": 7},
        "substitutability_score": 16,
        "geopolitical_risk_score": 80,
        "key_applications": ["fibre optic cables", "infrared optics", "solar cells", "semiconductors"],
        "transition_technology_dependence": "high",
        "iea_demand_growth_2023_2040_x": 2.9,
        "recycling_rate_pct": 30,
        "primary_ore": "by-product of coal fly ash / zinc smelting",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "tellurium": {
        "iea_criticality_composite": 75,
        "demand_growth_score": 68,
        "supply_concentration_hhi": 4200,
        "top3_country_share_pct": {"China": 45, "Japan": 15, "Russia": 10},
        "substitutability_score": 22,
        "geopolitical_risk_score": 65,
        "key_applications": ["CdTe thin-film solar", "thermoelectrics", "phase-change memory"],
        "transition_technology_dependence": "high",
        "iea_demand_growth_2023_2040_x": 3.6,
        "recycling_rate_pct": 35,
        "primary_ore": "by-product of copper anode slimes",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
    "selenium": {
        "iea_criticality_composite": 63,
        "demand_growth_score": 52,
        "supply_concentration_hhi": 3500,
        "top3_country_share_pct": {"China": 38, "Germany": 12, "Japan": 11},
        "substitutability_score": 32,
        "geopolitical_risk_score": 55,
        "key_applications": ["CIGS thin-film solar", "glass decolourising", "agriculture"],
        "transition_technology_dependence": "medium",
        "iea_demand_growth_2023_2040_x": 2.2,
        "recycling_rate_pct": 42,
        "primary_ore": "by-product of copper refining",
        "iea_report_page": "IEA CRM 2024 Chapter 3",
    },
}

# ---------------------------------------------------------------------------
# Reference Data — EU Critical Raw Materials Act 2024/1252
# ---------------------------------------------------------------------------

EU_CRM_ACT_MINERALS: Dict[str, Dict] = {
    # Strategic minerals (Art 3 — critical to green/digital/defence transitions with high supply risk)
    "lithium":              {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "cobalt":               {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "nickel":               {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "manganese":            {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "graphite":             {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "silicon_metal":        {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "rare_earths":          {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "platinum_group_metals":{"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "titanium":             {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "gallium":              {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "germanium":            {"strategic": True, "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    # Critical minerals (Art 2 — supply risk + economic importance)
    "copper":               {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "indium":               {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "tellurium":            {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "selenium":             {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    # Additional EU CRM Act listed minerals
    "boron":                {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "chromium":             {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "magnesium":            {"strategic": True,  "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "scandium":             {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "vanadium":             {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "tungsten":             {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "antimony":             {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "arsenic":              {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "bismuth":              {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "hafnium":              {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "natural_rubber":       {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "phosphorus":           {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "strontium":            {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "tantalum":             {"strategic": False, "critical": True,  "eu_benchmark_extraction_pct": None, "eu_benchmark_processing_pct": None, "eu_benchmark_recycling_pct": None, "audit_required": False},
    "bauxite_aluminium":    {"strategic": True,  "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "copper_refined":       {"strategic": True,  "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
    "nickel_refined":       {"strategic": True,  "critical": True,  "eu_benchmark_extraction_pct": 10, "eu_benchmark_processing_pct": 40, "eu_benchmark_recycling_pct": 15, "audit_required": True},
}

EU_CRM_ACT_COMPLIANCE_OBLIGATIONS: List[Dict] = [
    {
        "obligation": "Strategic stockpiling",
        "article": "Art 11",
        "description": "Member States must ensure strategic stocks equal to minimum 90 days of average annual domestic consumption for strategic minerals",
        "applies_to": "strategic",
    },
    {
        "obligation": "Supply chain due diligence",
        "article": "Art 14",
        "description": "Large companies sourcing strategic CRMs must conduct supply chain due diligence aligned with OECD DDG; annual audit",
        "applies_to": "strategic",
    },
    {
        "obligation": "Diversification benchmarks",
        "article": "Art 5",
        "description": "EU targets: 10% extraction, 40% processing, 15% recycling of annual CRM consumption domestically; no single non-EU country >65% of any CRM",
        "applies_to": "strategic",
    },
    {
        "obligation": "Permitting acceleration",
        "article": "Art 7",
        "description": "Strategic projects must receive EIA decision within 27 months of application; maximum 15 months operating permit",
        "applies_to": "strategic",
    },
    {
        "obligation": "Circularity and recycling reporting",
        "article": "Art 22",
        "description": "Producers must report on CRM content, recyclability, and end-of-life collection for batteries, magnets, motors, solar panels",
        "applies_to": "all",
    },
    {
        "obligation": "National CRM programmes",
        "article": "Art 8",
        "description": "Each Member State must publish national CRM programme covering exploration, production, recycling, and substitution",
        "applies_to": "all",
    },
]

# ---------------------------------------------------------------------------
# Reference Data — IRMA Standard for Responsible Mining v1.0
# ---------------------------------------------------------------------------

IRMA_STANDARD_CRITERIA: Dict[str, Dict] = {
    "chapter_2_planning": {
        "chapter": "Chapter 2 — Planning for Positive Legacies",
        "weight": 0.10,
        "sub_criteria": [
            "Integrated impact assessment (social, environmental, economic)",
            "Community development agreements with affected communities",
            "Post-mine closure plan with legacy fund",
            "Revenue transparency (EITI alignment)",
        ],
        "tiers": {"tier_1": "Basic commitments", "tier_2": "Established practice", "tier_3": "Leadership"},
    },
    "chapter_3_corporate_responsibility": {
        "chapter": "Chapter 3 — Corporate Responsibility Commitments",
        "weight": 0.15,
        "sub_criteria": [
            "Public commitments to responsible mining",
            "Anti-corruption compliance (FCPA / UK Bribery Act)",
            "Human rights due diligence (UNGP aligned)",
            "Grievance mechanism accessible to workers and communities",
        ],
        "tiers": {"tier_1": "Policy exists", "tier_2": "Implemented", "tier_3": "Verified and effective"},
    },
    "chapter_4_indigenous_rights": {
        "chapter": "Chapter 4 — Indigenous Peoples Rights",
        "weight": 0.15,
        "sub_criteria": [
            "Free, Prior and Informed Consent (FPIC) process documented",
            "Indigenous land and resource rights respected",
            "Benefit sharing agreements signed",
            "Cultural heritage protection plan",
        ],
        "tiers": {"tier_1": "Engagement initiated", "tier_2": "FPIC achieved", "tier_3": "Ongoing partnership"},
    },
    "chapter_5_community_wellbeing": {
        "chapter": "Chapter 5 — Community Wellbeing",
        "weight": 0.15,
        "sub_criteria": [
            "In-migration and resettlement risk management",
            "Local procurement and employment targets",
            "Community health impact assessment",
            "Gender equity and women's safety programme",
        ],
        "tiers": {"tier_1": "Assessment done", "tier_2": "Mitigation in place", "tier_3": "Positive outcomes demonstrated"},
    },
    "chapter_6_environment": {
        "chapter": "Chapter 6 — Environmental Protection",
        "weight": 0.25,
        "sub_criteria": [
            "Biodiversity action plan (no net loss target)",
            "Water quality and quantity management (site balance)",
            "Tailings storage facility (Global Industry Standard — GISTM 2020)",
            "GHG emissions inventory and reduction targets",
            "Acid rock drainage prevention and monitoring",
        ],
        "tiers": {"tier_1": "Legal compliance", "tier_2": "Best practice", "tier_3": "Industry leadership"},
    },
    "chapter_7_labour_rights": {
        "chapter": "Chapter 7 — Labour Rights and Occupational Health",
        "weight": 0.20,
        "sub_criteria": [
            "Freedom of association and collective bargaining",
            "Fatality-free operations target; safety management system ISO 45001",
            "No child or forced labour (ILO Convention 138/182)",
            "Fair wages — living wage commitment",
        ],
        "tiers": {"tier_1": "ILO compliance", "tier_2": "Proactive programmes", "tier_3": "Exemplary performance"},
    },
}

IRMA_TIER_THRESHOLDS: Dict[str, Dict] = {
    "tier_1": {"min_score": 0.50, "label": "IRMA Tier 1 — Basic Commitments",      "certified": False, "description": "Minimum policy commitments made; implementation limited"},
    "tier_2": {"min_score": 0.70, "label": "IRMA Tier 2 — Established Practice",   "certified": True,  "description": "Responsible mining practices implemented and documented"},
    "tier_3": {"min_score": 0.85, "label": "IRMA Tier 3 — Leadership",             "certified": True,  "description": "Industry-leading responsible mining; third-party verified"},
    "not_rated": {"min_score": 0.00, "label": "Not IRMA Rated",                     "certified": False, "description": "Below Tier 1 threshold; material gaps across chapters"},
}

# ---------------------------------------------------------------------------
# Reference Data — OECD Due Diligence Guidance (5-Step Framework)
# ---------------------------------------------------------------------------

OECD_5_STEP_FRAMEWORK: Dict[str, Dict] = {
    "step_1_management_systems": {
        "step_number": 1,
        "title": "Establish strong company management systems",
        "description": "Adopt and communicate a company supply chain policy; structure internal management to support due diligence",
        "weight": 0.20,
        "key_requirements": [
            "Board-approved conflict minerals / CRM supply chain policy",
            "Designated senior manager responsible for due diligence",
            "Supplier code of conduct for CRM procurement",
            "Contractual provisions requiring supplier due diligence",
        ],
        "conflict_mineral_focus": ["tin (3TG)", "tantalum (3TG)", "tungsten (3TG)", "gold (3TG)"],
    },
    "step_2_risk_identification": {
        "step_number": 2,
        "title": "Identify and assess risks in the supply chain",
        "description": "Map supply chain from mine to smelter/refiner; assess against Annex II risk indicators",
        "weight": 0.20,
        "key_requirements": [
            "Supply chain mapping to smelter/refiner (RMAP or equivalent)",
            "Annex II adverse impact assessment (conflict, serious abuses, corruption)",
            "Country-level conflict risk assessment (OECD/UN Panel reports)",
            "Risk-prioritised supplier engagement list",
        ],
        "annex_ii_risk_indicators": [
            "Operations or sourcing from conflict-affected or high-risk areas (CAHRA)",
            "Association with illegal armed groups or security forces",
            "Tax evasion or fraud along the supply chain",
            "Money laundering proceeds from mineral sales",
        ],
    },
    "step_3_risk_response": {
        "step_number": 3,
        "title": "Design and implement a strategy to respond to identified risks",
        "description": "Suspend or disengage from suppliers where risks cannot be mitigated; engage suppliers on improvement",
        "weight": 0.25,
        "key_requirements": [
            "Supplier remediation plan for identified risks",
            "Measurable improvement targets and monitoring schedule",
            "Suspension protocol for non-responsive suppliers",
            "Engagement with multi-stakeholder initiatives (RMAP, iTSCi, RJC)",
        ],
    },
    "step_4_third_party_audit": {
        "step_number": 4,
        "title": "Carry out independent third-party audit of supply chain due diligence",
        "description": "Commission independent audits of smelters/refiners or certification scheme participation",
        "weight": 0.20,
        "key_requirements": [
            "RMAP (Responsible Minerals Assurance Process) audit of all smelters/refiners",
            "Or equivalent certification (RJC, LBMA, London Platinum & Palladium Market)",
            "Audit scope covers Steps 1-3; results reported to board",
            "Annual re-certification; gap remediation tracked",
        ],
        "recognised_schemes": ["RMAP — RMAI", "RJC — Responsible Jewellery Council", "LBMA — London Bullion Market Association", "LPPM — Platinum/Palladium"],
    },
    "step_5_reporting": {
        "step_number": 5,
        "title": "Report on supply chain due diligence",
        "description": "Publish annual supply chain due diligence report; disclose on company website and to regulators",
        "weight": 0.15,
        "key_requirements": [
            "Annual public conflict minerals / CRM due diligence report",
            "SEC Form SD (if SEC-listed) or EU Regulation 2017/821 compliance declaration",
            "Disclosure of smelter/refiner list and audit status",
            "Progress on risk remediation communicated to stakeholders",
        ],
        "regulatory_references": ["US Dodd-Frank Section 1502", "EU Regulation 2017/821 (3TG)", "EU CRM Act Art 14"],
    },
}

CONFLICT_MINERAL_HIGH_RISK_COUNTRIES: Dict[str, Dict] = {
    "DRC":          {"risk": "very_high", "minerals": ["cobalt", "tantalum", "tin", "tungsten", "gold"], "un_panel_documented": True},
    "CAR":          {"risk": "very_high", "minerals": ["gold", "diamonds"],                              "un_panel_documented": True},
    "South Sudan":  {"risk": "very_high", "minerals": ["gold"],                                          "un_panel_documented": True},
    "Myanmar":      {"risk": "very_high", "minerals": ["rare_earths", "jade", "tin"],                    "un_panel_documented": True},
    "Mali":         {"risk": "high",      "minerals": ["gold"],                                          "un_panel_documented": False},
    "Sudan":        {"risk": "high",      "minerals": ["gold", "chromium"],                              "un_panel_documented": True},
    "Zimbabwe":     {"risk": "high",      "minerals": ["platinum_group_metals", "lithium", "chromium"],  "un_panel_documented": False},
    "Guinea":       {"risk": "medium",    "minerals": ["bauxite", "iron_ore"],                           "un_panel_documented": False},
    "Mozambique":   {"risk": "medium",    "minerals": ["graphite", "titanium", "rubies"],                "un_panel_documented": False},
    "Philippines":  {"risk": "medium",    "minerals": ["nickel", "copper", "cobalt"],                    "un_panel_documented": False},
}

# ---------------------------------------------------------------------------
# Reference Data — Transition Technology Exposure
# ---------------------------------------------------------------------------

TRANSITION_TECHNOLOGY_MINERAL_INTENSITY: Dict[str, Dict] = {
    "ev_battery_pack_per_gwh": {
        "lithium_tonnes": 160,
        "cobalt_tonnes":  12,
        "nickel_tonnes":  750,
        "manganese_tonnes": 90,
        "graphite_tonnes": 800,
        "copper_tonnes":  60,
        "note": "NMC 811 chemistry 70%; LFP 30% weighted average per IEA 2024",
    },
    "solar_pv_per_gw_utility": {
        "silicon_metal_tonnes":  4500,
        "copper_tonnes":         4000,
        "tellurium_tonnes":       110,
        "indium_tonnes":           40,
        "selenium_tonnes":         25,
        "note": "c-Si mono 60%; CdTe thin-film 20%; CIGS 10%; perovskite 10% blend per IRENA 2024",
    },
    "onshore_wind_per_gw": {
        "copper_tonnes":         2500,
        "rare_earths_tonnes":     200,
        "manganese_tonnes":       350,
        "nickel_tonnes":           80,
        "note": "PMDD and SCIG generator mix; tower + foundation steel excluded (not CRM)",
    },
    "offshore_wind_per_gw": {
        "copper_tonnes":         8000,
        "rare_earths_tonnes":     400,
        "manganese_tonnes":       700,
        "nickel_tonnes":          150,
        "note": "Higher cable requirements; predominantly DD-PMG turbines",
    },
    "grid_storage_per_gwh": {
        "lithium_tonnes":        300,
        "manganese_tonnes":      180,
        "nickel_tonnes":          90,
        "copper_tonnes":          50,
        "note": "LFP 60%; NMC 30%; vanadium flow 10% weighted blend",
    },
    "electrolyser_pem_per_gw": {
        "platinum_group_metals_tonnes": 0.3,
        "titanium_tonnes":       200,
        "nickel_tonnes":          85,
        "note": "PEM alkaline 50%; PEM 50% weighted; iridium and platinum critical for PEM",
    },
}

# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------


class CriticalMineralsAssessRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    entity_name: Optional[str] = "Unknown Entity"
    sector: Optional[str] = "manufacturing"

    # Mineral exposure list
    minerals_exposed: Optional[List[str]] = None

    # Financial exposure by transition technology (USD million)
    ev_battery_exposure_m: Optional[float] = Field(None, ge=0.0, description="EV battery supply chain exposure USD million")
    solar_pv_exposure_m: Optional[float] = Field(None, ge=0.0, description="Solar PV supply chain exposure USD million")
    wind_turbine_exposure_m: Optional[float] = Field(None, ge=0.0, description="Wind turbine supply chain exposure USD million")
    grid_storage_exposure_m: Optional[float] = Field(None, ge=0.0, description="Grid storage supply chain exposure USD million")

    # IEA CRM sub-scores (0-100) — optional overrides
    iea_demand_growth_override: Optional[float] = Field(None, ge=0, le=100)
    iea_supply_concentration_override: Optional[float] = Field(None, ge=0, le=100)
    iea_geopolitical_risk_override: Optional[float] = Field(None, ge=0, le=100)
    iea_substitutability_override: Optional[float] = Field(None, ge=0, le=100)

    # EU CRM Act compliance
    eu_crm_act_applicable: Optional[bool] = True
    eu_strategic_minerals_sourced: Optional[List[str]] = None
    eu_crm_audit_completed: Optional[bool] = False

    # IRMA pillar scores (0-1)
    irma_planning_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    irma_corporate_responsibility_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    irma_indigenous_rights_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    irma_community_wellbeing_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    irma_environment_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    irma_labour_rights_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # OECD 5-step compliance scores (0-1)
    oecd_step1_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    oecd_step2_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    oecd_step3_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    oecd_step4_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    oecd_step5_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Supply chain context
    conflict_affected_sourcing: Optional[bool] = False
    conflict_countries: Optional[List[str]] = None

    # Financial context
    total_procurement_m: Optional[float] = Field(100.0, ge=0.0)


class SupplyChainMapRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    entity_name: Optional[str] = "Unknown Entity"
    mineral: str
    technology_application: Optional[str] = "ev_battery"
    annual_volume_tonnes: Optional[float] = 1000.0
    known_countries_of_origin: Optional[List[str]] = None
    smelter_audit_completed: Optional[bool] = False
    certification_scheme: Optional[str] = None


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CriticalMineralsResult:
    entity_id: str
    entity_name: str
    sector: str
    minerals_assessed: List[str]

    # IEA CRM 2024
    iea_demand_growth_score: float
    iea_supply_concentration: float
    iea_geopolitical_risk: float
    iea_substitutability: float
    iea_criticality_composite: float

    # EU CRM Act 2024/1252
    eu_crm_act_applicable: bool
    eu_crm_strategic_mineral_count: int
    eu_crm_critical_mineral_count: int
    eu_crm_audit_required: bool
    eu_crm_compliance_score: float
    eu_crm_gaps: List[str]

    # IRMA
    irma_applicable: bool
    irma_score: float
    irma_tier: str
    irma_gaps: List[str]

    # OECD DDG
    oecd_ddg_score: float
    oecd_5step_compliance: Dict[str, float]
    conflict_mineral_risk: str
    conflict_region_exposure: bool

    # Transition exposure
    ev_battery_exposure_m: float
    solar_pv_exposure_m: float
    wind_turbine_exposure_m: float
    grid_storage_exposure_m: float
    total_transition_exposure_m: float

    # Supply chain metrics
    price_volatility_score: float
    supply_disruption_prob_pct: float
    concentration_hhi: float
    top3_country_share_pct: float

    # Overall
    crm_risk_score: float
    crm_risk_tier: str
    key_findings: List[str]
    recommendations: List[str]
    standards_applied: List[str]


@dataclass
class SupplyChainMapResult:
    entity_id: str
    entity_name: str
    mineral: str
    technology_application: str
    annual_volume_tonnes: float
    mineral_profile: Dict[str, Any]
    tier1_country_risks: List[Dict]
    conflict_region_flag: bool
    smelter_audit_completed: bool
    certification_scheme: Optional[str]
    rmap_recommended: bool
    oecd_annex_ii_risk: str
    sourcing_recommendations: List[str]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _seed_float(entity_id: str, key: str, lo: float, hi: float) -> float:
    """Deterministic seeded float — reproducible demo data."""
    h = hash(f"{entity_id}:{key}") & 0xFFFFFF
    return round(lo + (h / 0xFFFFFF) * (hi - lo), 3)


def _weighted_irma_score(data: Dict, eid: str) -> float:
    spec = {
        "irma_planning_score":              ("irma_p",  0.10),
        "irma_corporate_responsibility_score":("irma_cr", 0.15),
        "irma_indigenous_rights_score":     ("irma_ir",  0.15),
        "irma_community_wellbeing_score":   ("irma_cw",  0.15),
        "irma_environment_score":           ("irma_en",  0.25),
        "irma_labour_rights_score":         ("irma_lr",  0.20),
    }
    total = 0.0
    for field, (key, wt) in spec.items():
        val = data.get(field) or _seed_float(eid, key, 0.35, 0.88)
        total += val * wt
    return round(total, 3)


def _irma_tier(score: float) -> str:
    if score >= 0.85:
        return "tier_3"
    elif score >= 0.70:
        return "tier_2"
    elif score >= 0.50:
        return "tier_1"
    return "not_rated"


def _oecd_5step_scores(data: Dict, eid: str) -> Dict[str, float]:
    steps = {
        "step_1_management_systems": ("oecd_s1", data.get("oecd_step1_score")),
        "step_2_risk_identification": ("oecd_s2", data.get("oecd_step2_score")),
        "step_3_risk_response":       ("oecd_s3", data.get("oecd_step3_score")),
        "step_4_third_party_audit":   ("oecd_s4", data.get("oecd_step4_score")),
        "step_5_reporting":           ("oecd_s5", data.get("oecd_step5_score")),
    }
    result = {}
    for name, (key, val) in steps.items():
        result[name] = round(val if val is not None else _seed_float(eid, key, 0.30, 0.88), 3)
    return result


def _oecd_composite(step_scores: Dict[str, float]) -> float:
    weights = {
        "step_1_management_systems": 0.20,
        "step_2_risk_identification": 0.20,
        "step_3_risk_response":       0.25,
        "step_4_third_party_audit":   0.20,
        "step_5_reporting":           0.15,
    }
    return round(sum(step_scores.get(k, 0.0) * w for k, w in weights.items()), 3)


def _iea_mineral_composite(minerals: List[str]) -> Dict[str, float]:
    """Aggregate IEA scores across a portfolio of minerals (simple average)."""
    if not minerals:
        return {"demand_growth_score": 65.0, "supply_concentration": 50.0, "geopolitical_risk": 60.0, "substitutability": 30.0, "composite": 60.0}
    valid = [m for m in minerals if m in IEA_CRITICAL_MINERALS_2024]
    if not valid:
        valid = list(IEA_CRITICAL_MINERALS_2024.keys())[:3]
    n = len(valid)
    dg  = round(sum(IEA_CRITICAL_MINERALS_2024[m]["demand_growth_score"] for m in valid) / n, 1)
    sc  = round(sum(IEA_CRITICAL_MINERALS_2024[m]["supply_concentration_hhi"] / 100.0 for m in valid) / n, 1)
    geo = round(sum(IEA_CRITICAL_MINERALS_2024[m]["geopolitical_risk_score"] for m in valid) / n, 1)
    sub = round(sum(IEA_CRITICAL_MINERALS_2024[m]["substitutability_score"] for m in valid) / n, 1)
    composite = round(sum(IEA_CRITICAL_MINERALS_2024[m]["iea_criticality_composite"] for m in valid) / n, 1)
    return {"demand_growth_score": dg, "supply_concentration": sc, "geopolitical_risk": geo, "substitutability": sub, "composite": composite}


def _crm_tier(score: float) -> str:
    if score < 30:
        return "low"
    elif score < 55:
        return "medium"
    elif score < 75:
        return "high"
    return "critical"


# ---------------------------------------------------------------------------
# Public Service Functions
# ---------------------------------------------------------------------------

def assess_critical_minerals(request_data: Dict) -> CriticalMineralsResult:
    """
    Full critical minerals risk assessment per:
    IEA CRM 2024 | EU CRM Act 2024/1252 | IRMA Standard v1.0 | OECD DDG 5-step.
    Returns CriticalMineralsResult dataclass.
    """
    eid     = request_data.get("entity_id", "unknown")
    ename   = request_data.get("entity_name", "Unknown Entity")
    sector  = request_data.get("sector", "manufacturing")
    minerals = request_data.get("minerals_exposed") or ["lithium", "cobalt", "nickel", "graphite", "copper"]

    # ---- IEA CRM 2024 ----
    iea = _iea_mineral_composite(minerals)
    iea_dg  = iea["demand_growth_score"]
    iea_sc  = iea["supply_concentration"]
    iea_geo = iea["geopolitical_risk"]
    iea_sub = iea["substitutability"]
    iea_comp = iea["composite"]

    # Apply overrides if provided
    if request_data.get("iea_demand_growth_override") is not None:
        iea_dg = float(request_data["iea_demand_growth_override"])
    if request_data.get("iea_supply_concentration_override") is not None:
        iea_sc = float(request_data["iea_supply_concentration_override"])
    if request_data.get("iea_geopolitical_risk_override") is not None:
        iea_geo = float(request_data["iea_geopolitical_risk_override"])
    if request_data.get("iea_substitutability_override") is not None:
        iea_sub = float(request_data["iea_substitutability_override"])

    # ---- EU CRM Act 2024/1252 ----
    eu_applicable = bool(request_data.get("eu_crm_act_applicable", True))
    eu_strategic_sourced = request_data.get("eu_strategic_minerals_sourced") or [
        m for m in minerals if EU_CRM_ACT_MINERALS.get(m, {}).get("strategic", False)
    ]
    eu_audit_done = bool(request_data.get("eu_crm_audit_completed", False))

    eu_strategic_count = sum(1 for m in minerals if EU_CRM_ACT_MINERALS.get(m, {}).get("strategic", False))
    eu_critical_count  = sum(1 for m in minerals if EU_CRM_ACT_MINERALS.get(m, {}).get("critical", False))
    eu_audit_required  = eu_strategic_count > 0

    eu_crm_gaps: List[str] = []
    eu_compliance_score = 0.0
    if eu_applicable:
        if not eu_audit_done and eu_audit_required:
            eu_crm_gaps.append("Annual supply chain due diligence audit (Art 14) not completed for strategic minerals.")
        else:
            eu_compliance_score += 0.40
        if eu_strategic_count > 0:
            eu_compliance_score += 0.30
        # Check 65% single-country concentration rule
        for m in minerals:
            profile = IEA_CRITICAL_MINERALS_2024.get(m, {})
            top_country = profile.get("top3_country_share_pct", {})
            for country, share in top_country.items():
                if share > 65:
                    eu_crm_gaps.append(f"{m.capitalize()}: {country} supplies {share}% — exceeds EU 65% single-source concentration limit (Art 5).")
        eu_compliance_score += max(0.0, 0.30 - len(eu_crm_gaps) * 0.05)
        eu_compliance_score = min(round(eu_compliance_score, 3), 1.0)

    # ---- IRMA Standard v1.0 ----
    irma_applicable = any(IEA_CRITICAL_MINERALS_2024.get(m, {}).get("transition_technology_dependence") in ("critical", "high") for m in minerals)
    irma_score = _weighted_irma_score(request_data, eid)
    irma_tier  = _irma_tier(irma_score)
    irma_gaps: List[str] = []
    if irma_score < 0.70:
        irma_gaps.append("IRMA Tier 2 not achieved; review environmental protection (Ch6) and labour rights (Ch7) chapters.")
    if (request_data.get("irma_indigenous_rights_score") or _seed_float(eid, "irma_ir", 0.35, 0.88)) < 0.70:
        irma_gaps.append("IRMA Chapter 4 (Indigenous Rights / FPIC) below Tier 2 — FPIC documentation needed.")
    if (request_data.get("irma_environment_score") or _seed_float(eid, "irma_en", 0.35, 0.88)) < 0.70:
        irma_gaps.append("IRMA Chapter 6 (Environment) below Tier 2 — GISTM tailings compliance check required.")

    # ---- OECD DDG 5-step ----
    step_scores = _oecd_5step_scores(request_data, eid)
    oecd_composite = _oecd_composite(step_scores)
    conflict_sourcing = bool(request_data.get("conflict_affected_sourcing", False))
    conflict_countries = request_data.get("conflict_countries") or []
    conflict_risk = "very_high" if conflict_sourcing else ("high" if any(c in CONFLICT_MINERAL_HIGH_RISK_COUNTRIES for c in conflict_countries) else "low")

    # ---- Transition exposure ----
    ev_m     = float(request_data.get("ev_battery_exposure_m") or _seed_float(eid, "ev_m",   10.0, 500.0))
    solar_m  = float(request_data.get("solar_pv_exposure_m")   or _seed_float(eid, "sol_m",   5.0, 300.0))
    wind_m   = float(request_data.get("wind_turbine_exposure_m") or _seed_float(eid, "wnd_m",  5.0, 200.0))
    grid_m   = float(request_data.get("grid_storage_exposure_m") or _seed_float(eid, "grd_m",  2.0, 150.0))
    total_m  = round(ev_m + solar_m + wind_m + grid_m, 2)

    # ---- Supply chain aggregated metrics ----
    avg_hhi = round(
        sum(IEA_CRITICAL_MINERALS_2024.get(m, {}).get("supply_concentration_hhi", 4000) for m in minerals) / len(minerals), 0
    )
    avg_top3 = round(
        sum(sum(IEA_CRITICAL_MINERALS_2024.get(m, {}).get("top3_country_share_pct", {}).values() if isinstance(IEA_CRITICAL_MINERALS_2024.get(m, {}).get("top3_country_share_pct"), dict) else [70]) for m in minerals) / len(minerals), 1
    )
    price_vol = round(_seed_float(eid, "pvol", 35.0, 85.0), 1)
    disruption_prob = round(min((avg_hhi / 100.0) * (iea_geo / 100.0) * 15.0, 35.0), 1)

    # ---- Overall CRM risk score ----
    # Composite of IEA criticality (40%) + OECD due diligence gap (30%) + concentration risk (30%)
    oecd_gap_score = round((1.0 - oecd_composite) * 100.0, 1)
    concentration_score = round(min(avg_hhi / 100.0, 100.0), 1)
    crm_risk_score = round(
        iea_comp * 0.40 + oecd_gap_score * 0.30 + concentration_score * 0.30, 1
    )
    crm_tier = _crm_tier(crm_risk_score)

    # ---- Findings and recommendations ----
    findings: List[str] = []
    recs:     List[str] = []

    if iea_comp >= 80:
        findings.append(f"IEA CRM 2024 composite criticality score {iea_comp}/100 — CRITICAL portfolio of minerals with high supply concentration and demand growth.")
        recs.append("Develop a critical minerals procurement diversification strategy with 3-5 year supply chain roadmap.")
    elif iea_comp >= 65:
        findings.append(f"IEA CRM 2024 composite score {iea_comp}/100 — HIGH criticality; significant supply concentration risk.")
        recs.append("Engage strategic suppliers on long-term supply agreements and consider offtake partnerships.")

    if eu_crm_gaps:
        findings.append(f"EU CRM Act 2024/1252: {len(eu_crm_gaps)} compliance gap(s) identified for strategic minerals.")
        recs.append("Complete Art 14 supply chain due diligence audit; address single-country concentration breaches.")
    if conflict_sourcing or conflict_risk in ("very_high", "high"):
        findings.append(f"Conflict mineral risk rated '{conflict_risk}' — OECD DDG Step 2 Annex II screening mandatory.")
        recs.append("Conduct RMAP smelter/refiner audit for all 3TG + cobalt supply chains; engage iTSCi or equivalent.")
    if irma_tier == "not_rated":
        findings.append("IRMA Standard rating: Not Rated — material gaps in environmental and community chapters.")
        recs.append("Initiate IRMA self-assessment for operating mines; prioritise Ch6 (Environment) and Ch7 (Labour).")
    if oecd_composite < 0.70:
        findings.append(f"OECD DDG 5-step composite {oecd_composite:.2f} — below recommended threshold (0.70).")
        recs.append("Strengthen OECD Step 3 (risk response) and Step 4 (third-party audit) to improve DDG compliance.")
    if disruption_prob > 20:
        findings.append(f"Supply disruption probability {disruption_prob:.1f}% — above 20% threshold given high HHI and geopolitical risk.")
        recs.append("Build strategic inventory buffers and establish secondary supplier relationships in lower-risk jurisdictions.")

    return CriticalMineralsResult(
        entity_id=eid,
        entity_name=ename,
        sector=sector,
        minerals_assessed=minerals,
        iea_demand_growth_score=iea_dg,
        iea_supply_concentration=iea_sc,
        iea_geopolitical_risk=iea_geo,
        iea_substitutability=iea_sub,
        iea_criticality_composite=iea_comp,
        eu_crm_act_applicable=eu_applicable,
        eu_crm_strategic_mineral_count=eu_strategic_count,
        eu_crm_critical_mineral_count=eu_critical_count,
        eu_crm_audit_required=eu_audit_required,
        eu_crm_compliance_score=eu_compliance_score,
        eu_crm_gaps=eu_crm_gaps,
        irma_applicable=irma_applicable,
        irma_score=irma_score,
        irma_tier=irma_tier,
        irma_gaps=irma_gaps,
        oecd_ddg_score=oecd_composite,
        oecd_5step_compliance=step_scores,
        conflict_mineral_risk=conflict_risk,
        conflict_region_exposure=conflict_sourcing or bool(conflict_countries),
        ev_battery_exposure_m=round(ev_m, 2),
        solar_pv_exposure_m=round(solar_m, 2),
        wind_turbine_exposure_m=round(wind_m, 2),
        grid_storage_exposure_m=round(grid_m, 2),
        total_transition_exposure_m=total_m,
        price_volatility_score=price_vol,
        supply_disruption_prob_pct=disruption_prob,
        concentration_hhi=avg_hhi,
        top3_country_share_pct=avg_top3,
        crm_risk_score=crm_risk_score,
        crm_risk_tier=crm_tier,
        key_findings=findings,
        recommendations=recs,
        standards_applied=[
            "IEA Critical Minerals 2024 Report — Global demand and supply outlook",
            "EU Critical Raw Materials Act (Regulation EU 2024/1252)",
            "IRMA Standard for Responsible Mining v1.0",
            "OECD Due Diligence Guidance for Responsible Mineral Supply Chains (5-step)",
            "EU Regulation 2017/821 — Conflict Minerals (3TG)",
            "US Dodd-Frank Section 1502 — Conflict Minerals Reporting",
            "RMAP — Responsible Minerals Assurance Process (RMAI)",
            "GRI 306: Waste 2020; GRI 204: Procurement Practices",
            "ISSB IFRS S2 — Physical and transition risk disclosures",
        ],
    )


def map_supply_chain(request_data: Dict) -> SupplyChainMapResult:
    """
    Map mineral supply chain tiers for a specific mineral and technology application.
    Identifies conflict region exposure, RMAP audit need, and OECD Annex II risks.
    """
    eid         = request_data.get("entity_id", "unknown")
    ename       = request_data.get("entity_name", "Unknown Entity")
    mineral     = request_data.get("mineral", "lithium")
    app         = request_data.get("technology_application", "ev_battery")
    volume      = float(request_data.get("annual_volume_tonnes") or 1000.0)
    countries   = request_data.get("known_countries_of_origin") or []
    audit_done  = bool(request_data.get("smelter_audit_completed", False))
    cert_scheme = request_data.get("certification_scheme")

    profile = IEA_CRITICAL_MINERALS_2024.get(mineral, {
        "iea_criticality_composite": 70,
        "top3_country_share_pct": {"Unknown": 60},
        "transition_technology_dependence": "medium",
        "recycling_rate_pct": 20,
    })

    # Assess conflict region exposure
    conflict_flag = any(c in CONFLICT_MINERAL_HIGH_RISK_COUNTRIES for c in countries)
    if not countries:
        # Use known top producer countries from profile
        top_countries = profile.get("top3_country_share_pct", {})
        conflict_flag = any(c in CONFLICT_MINERAL_HIGH_RISK_COUNTRIES for c in top_countries)
        countries = list(top_countries.keys())

    tier1_risks: List[Dict] = []
    for country in countries:
        cr = CONFLICT_MINERAL_HIGH_RISK_COUNTRIES.get(country, {})
        tier1_risks.append({
            "country": country,
            "conflict_risk": cr.get("risk", "low"),
            "un_panel_documented": cr.get("un_panel_documented", False),
            "affected_minerals": cr.get("minerals", []),
            "oecd_cahra": cr.get("risk", "low") in ("very_high", "high"),
        })

    # OECD Annex II risk assessment
    if conflict_flag:
        annex_ii_risk = "high"
    elif any(t.get("conflict_risk") == "medium" for t in tier1_risks):
        annex_ii_risk = "medium"
    else:
        annex_ii_risk = "low"

    rmap_recommended = (annex_ii_risk in ("high", "medium")) or not audit_done

    recs: List[str] = []
    if not audit_done:
        recs.append("Complete RMAP smelter/refiner audit for all supply chain nodes before next reporting cycle.")
    if conflict_flag:
        recs.append(f"Conflict region exposure detected — OECD DDG Step 3 risk response plan required immediately.")
    if not cert_scheme:
        recs.append("Adopt a recognised certification scheme (RMAP / RJC / LBMA) to demonstrate supply chain due diligence.")
    if profile.get("recycling_rate_pct", 0) < 20:
        recs.append(f"{mineral.capitalize()} has low recycling rate — evaluate secondary supply and urban mining partnerships.")

    return SupplyChainMapResult(
        entity_id=eid,
        entity_name=ename,
        mineral=mineral,
        technology_application=app,
        annual_volume_tonnes=volume,
        mineral_profile=profile,
        tier1_country_risks=tier1_risks,
        conflict_region_flag=conflict_flag,
        smelter_audit_completed=audit_done,
        certification_scheme=cert_scheme,
        rmap_recommended=rmap_recommended,
        oecd_annex_ii_risk=annex_ii_risk,
        sourcing_recommendations=recs,
    )


def get_mineral_profile(mineral_name: str) -> Dict[str, Any]:
    """Return IEA CRM 2024 profile and EU CRM Act status for a single mineral."""
    iea_profile = IEA_CRITICAL_MINERALS_2024.get(mineral_name)
    eu_status   = EU_CRM_ACT_MINERALS.get(mineral_name)
    if not iea_profile and not eu_status:
        return {"error": f"Mineral '{mineral_name}' not found in IEA or EU CRM Act databases."}
    return {
        "mineral": mineral_name,
        "iea_crm_2024": iea_profile or {},
        "eu_crm_act_2024": eu_status or {"strategic": False, "critical": False, "audit_required": False},
        "transition_intensity": {
            k: {k2: v2 for k2, v2 in v.items() if mineral_name in k2 or "note" in k2}
            for k, v in TRANSITION_TECHNOLOGY_MINERAL_INTENSITY.items()
            if any(mineral_name in k2 for k2 in v)
        },
        "conflict_country_exposure": {
            country: info for country, info in CONFLICT_MINERAL_HIGH_RISK_COUNTRIES.items()
            if mineral_name in info.get("minerals", [])
        },
    }
