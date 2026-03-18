"""
EU Social Taxonomy & Human Rights Due Diligence Engine — E97
=============================================================

Regulatory / framework basis:
  - EU Social Taxonomy — Platform on Sustainable Finance Final Report 2022
    + Supplementary Report 2023
  - ILO Declaration on Fundamental Principles and Rights at Work 1998
    (8 Core Conventions: C029, C087, C098, C100, C105, C111, C138, C182)
  - CSDDD Annex I / II Social Adverse Impacts (Directive (EU) 2024/1760)
  - UN Guiding Principles on Business and Human Rights (UNGP) 2011
  - OECD Guidelines for Multinational Enterprises (2023 update), DDG 5-step
  - ILO / UN SDG 8 Decent Work Framework
  - ILO Convention on Violence and Harassment in the World of Work (C190)
  - European Social Charter (Revised, 1996)
  - UN Convention on the Rights of the Child (UNCRC Art 32)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Reference Data — EU Social Taxonomy Objectives
# ---------------------------------------------------------------------------

EU_SOCIAL_TAXONOMY_OBJECTIVES: dict[str, dict[str, Any]] = {
    "OBJ1": {
        "id": "OBJ1",
        "title": "Decent Work",
        "description": (
            "Activities that substantially contribute to decent work for the company's own workforce "
            "and for workers in the value chain, covering adequate wages, safe and healthy working "
            "conditions, job security, and freedom of association."
        ),
        "esrs_reference": "ESRS S1 (Own Workforce), ESRS S2 (Workers in Value Chain)",
        "sdg_targets": ["SDG 8.5", "SDG 8.7", "SDG 8.8"],
        "sub_criteria": {
            "SC1_1": {
                "id": "SC1_1",
                "title": "Adequate Wages",
                "description": "Wages at or above living wage benchmarks (Anker methodology); gender pay gap disclosed.",
                "ilo_references": ["C100"],
                "weight": 0.25,
                "metrics": [
                    "wages_vs_living_wage_pct",
                    "gender_pay_gap_pct",
                    "pay_ratio_disclosure",
                ],
            },
            "SC1_2": {
                "id": "SC1_2",
                "title": "Health & Safety",
                "description": "Zero-injury target; OHSAS 18001 / ISO 45001 certification; fatality rate.",
                "ilo_references": ["C155", "C187"],
                "weight": 0.25,
                "metrics": [
                    "ltir_per_200k_hours",
                    "fatality_rate",
                    "iso45001_certified",
                    "h_and_s_management_system",
                ],
            },
            "SC1_3": {
                "id": "SC1_3",
                "title": "Job Security & Fair Contracts",
                "description": "No excessive fixed-term contracts; redundancy protection; notice periods above legal minimums.",
                "weight": 0.20,
                "metrics": [
                    "permanent_contract_pct",
                    "precarious_work_pct",
                    "redundancy_pay_policy",
                ],
            },
            "SC1_4": {
                "id": "SC1_4",
                "title": "Social Dialogue & Freedom of Association",
                "description": "Collective bargaining coverage; trade union recognition; works council presence.",
                "ilo_references": ["C087", "C098", "C135"],
                "weight": 0.15,
                "metrics": [
                    "collective_bargaining_coverage_pct",
                    "union_recognition",
                    "works_council_present",
                ],
            },
            "SC1_5": {
                "id": "SC1_5",
                "title": "Work-Life Balance",
                "description": "Parental leave provision above statutory; flexible working; non-discrimination in caregiving.",
                "weight": 0.15,
                "metrics": [
                    "parental_leave_weeks_above_statutory",
                    "flexible_working_policy",
                    "childcare_support",
                ],
            },
        },
    },
    "OBJ2": {
        "id": "OBJ2",
        "title": "Adequate Living Standards & Wellbeing",
        "description": (
            "Activities that substantially contribute to ensuring adequate living standards "
            "and wellbeing for end-users and communities, including access to essential services: "
            "healthcare, housing, education, food security, and financial inclusion."
        ),
        "esrs_reference": "ESRS S3 (Affected Communities), ESRS S4 (Consumers)",
        "sdg_targets": ["SDG 1.4", "SDG 2.1", "SDG 3.8", "SDG 4.1", "SDG 11.1"],
        "sub_criteria": {
            "SC2_1": {
                "id": "SC2_1",
                "title": "Healthcare Access",
                "description": "Products/services that improve access to healthcare for underserved populations.",
                "weight": 0.25,
                "metrics": [
                    "healthcare_access_improvement",
                    "affordable_medicines_policy",
                    "universal_health_coverage_contribution",
                ],
            },
            "SC2_2": {
                "id": "SC2_2",
                "title": "Affordable Housing",
                "description": "Social / affordable housing provision; housing cost burden reduction.",
                "weight": 0.20,
                "metrics": [
                    "affordable_units_pct",
                    "housing_cost_burden_below_30pct",
                    "social_housing_designation",
                ],
            },
            "SC2_3": {
                "id": "SC2_3",
                "title": "Education & Skills",
                "description": "Education services; vocational training; digital literacy; lifelong learning.",
                "weight": 0.20,
                "metrics": [
                    "training_hours_per_employee",
                    "literacy_improvement_programmes",
                    "vocational_training_coverage",
                ],
            },
            "SC2_4": {
                "id": "SC2_4",
                "title": "Food Security",
                "description": "No adverse impact on food security; contribution to sustainable food systems.",
                "weight": 0.20,
                "metrics": [
                    "food_insecurity_impact_assessment",
                    "sustainable_sourcing_pct",
                    "food_waste_reduction_pct",
                ],
            },
            "SC2_5": {
                "id": "SC2_5",
                "title": "Financial Inclusion",
                "description": "Affordable financial services to underserved; microfinance; fintech inclusion.",
                "weight": 0.15,
                "metrics": [
                    "underserved_customer_pct",
                    "affordable_product_pricing",
                    "financial_literacy_programmes",
                ],
            },
        },
    },
    "OBJ3": {
        "id": "OBJ3",
        "title": "Inclusive & Sustainable Communities",
        "description": (
            "Activities that substantially contribute to building inclusive, resilient, sustainable "
            "communities by enabling inclusive growth, digital access, preserving cultural heritage, "
            "and contributing to a just transition away from fossil fuels."
        ),
        "esrs_reference": "ESRS S3 (Affected Communities), ESRS G1 (Business Conduct)",
        "sdg_targets": ["SDG 10.2", "SDG 11.3", "SDG 11.4", "SDG 17.17"],
        "sub_criteria": {
            "SC3_1": {
                "id": "SC3_1",
                "title": "Inclusive Growth",
                "description": "Local procurement; SME engagement; gender-diverse supply chains.",
                "weight": 0.25,
                "metrics": [
                    "local_procurement_pct",
                    "sme_supplier_pct",
                    "diverse_supplier_pct",
                ],
            },
            "SC3_2": {
                "id": "SC3_2",
                "title": "Digital Access",
                "description": "Digital infrastructure; broadband access; bridging digital divide.",
                "weight": 0.20,
                "metrics": [
                    "digital_inclusion_programme",
                    "broadband_coverage_contribution",
                    "device_access_programme",
                ],
            },
            "SC3_3": {
                "id": "SC3_3",
                "title": "Cultural Heritage",
                "description": "Preservation of cultural heritage; respect for indigenous cultural rights.",
                "weight": 0.20,
                "metrics": [
                    "cultural_heritage_impact_assessment",
                    "iplc_cultural_rights_compliance",
                    "heritage_site_protection",
                ],
            },
            "SC3_4": {
                "id": "SC3_4",
                "title": "Just Transition",
                "description": "Reskilling for workers in fossil fuel sectors; community economic diversification.",
                "weight": 0.20,
                "metrics": [
                    "just_transition_plan",
                    "affected_worker_reskilling_pct",
                    "community_investment_usd_per_employee",
                ],
            },
            "SC3_5": {
                "id": "SC3_5",
                "title": "Stakeholder Engagement & Social Licence",
                "description": "Meaningful stakeholder consultation; grievance mechanisms; social licence to operate.",
                "weight": 0.15,
                "metrics": [
                    "stakeholder_engagement_frequency",
                    "grievance_mechanism_accessible",
                    "community_satisfaction_score",
                ],
            },
        },
    },
}

# ---------------------------------------------------------------------------
# Reference Data — ILO 8 Core Conventions
# ---------------------------------------------------------------------------

ILO_CORE_CONVENTIONS: dict[str, dict[str, Any]] = {
    "C029": {
        "id": "C029",
        "title": "Forced Labour Convention",
        "year": 1930,
        "protocol": "P029 (2014)",
        "subject": "Forced or compulsory labour",
        "ilo_declaration_category": "Forced Labour",
        "fundamental": True,
        "key_obligations": [
            "Suppress use of all forms of forced or compulsory labour",
            "Prohibition of forced labour in all forms including state-imposed",
            "Prosecution of violations",
        ],
        "ratifications_global": 179,
        "weight": 0.15,
        "csddd_mapping": "HR-01",
    },
    "C087": {
        "id": "C087",
        "title": "Freedom of Association and Protection of the Right to Organise",
        "year": 1948,
        "subject": "Freedom of association",
        "ilo_declaration_category": "Freedom of Association",
        "fundamental": True,
        "key_obligations": [
            "Workers and employers right to form and join organisations",
            "No interference by public authorities",
            "Protection against dissolution or suspension by administrative authority",
        ],
        "ratifications_global": 158,
        "weight": 0.12,
        "csddd_mapping": "HR-03",
    },
    "C098": {
        "id": "C098",
        "title": "Right to Organise and Collective Bargaining Convention",
        "year": 1949,
        "subject": "Collective bargaining",
        "ilo_declaration_category": "Freedom of Association",
        "fundamental": True,
        "key_obligations": [
            "Protection against anti-union discrimination",
            "Protection of workers' and employers' organisations from interference",
            "Measures to encourage voluntary collective bargaining",
        ],
        "ratifications_global": 169,
        "weight": 0.12,
        "csddd_mapping": "HR-03",
    },
    "C100": {
        "id": "C100",
        "title": "Equal Remuneration Convention",
        "year": 1951,
        "subject": "Equal pay for men and women",
        "ilo_declaration_category": "Elimination of Discrimination",
        "fundamental": True,
        "key_obligations": [
            "Equal remuneration for work of equal value",
            "Application to basic wage and any additional emoluments",
            "Objective job evaluation",
        ],
        "ratifications_global": 174,
        "weight": 0.10,
        "csddd_mapping": "HR-04",
    },
    "C105": {
        "id": "C105",
        "title": "Abolition of Forced Labour Convention",
        "year": 1957,
        "subject": "Abolition of specific forms of forced labour",
        "ilo_declaration_category": "Forced Labour",
        "fundamental": True,
        "key_obligations": [
            "No use of forced labour as a means of political coercion",
            "No use of forced labour as labour discipline",
            "No use as means of racial, social, national or religious discrimination",
        ],
        "ratifications_global": 176,
        "weight": 0.15,
        "csddd_mapping": "HR-01",
    },
    "C111": {
        "id": "C111",
        "title": "Discrimination (Employment and Occupation) Convention",
        "year": 1958,
        "subject": "Non-discrimination",
        "ilo_declaration_category": "Elimination of Discrimination",
        "fundamental": True,
        "key_obligations": [
            "Pursue national policy to promote equality of opportunity",
            "Prohibition of discrimination based on race, colour, sex, religion, political opinion",
            "Eliminate discrimination in access to vocational training and employment",
        ],
        "ratifications_global": 175,
        "weight": 0.10,
        "csddd_mapping": "HR-04",
    },
    "C138": {
        "id": "C138",
        "title": "Minimum Age Convention",
        "year": 1973,
        "subject": "Minimum age for work",
        "ilo_declaration_category": "Child Labour",
        "fundamental": True,
        "key_obligations": [
            "National minimum age policy to raise school leaving age",
            "Minimum age of 15 (or 14 for developing countries) for employment",
            "Minimum age of 18 for hazardous work",
        ],
        "ratifications_global": 173,
        "weight": 0.13,
        "csddd_mapping": "HR-02",
    },
    "C182": {
        "id": "C182",
        "title": "Worst Forms of Child Labour Convention",
        "year": 1999,
        "subject": "Child labour worst forms",
        "ilo_declaration_category": "Child Labour",
        "fundamental": True,
        "key_obligations": [
            "Immediate elimination of worst forms of child labour",
            "Prohibition of child trafficking, debt bondage, serfdom",
            "Prohibition of use of child in armed conflict, prostitution, pornography, drug trafficking",
            "Effective measures to remove children from worst forms and ensure rehabilitation",
        ],
        "ratifications_global": 187,
        "weight": 0.13,
        "csddd_mapping": "HR-02",
    },
}

# ---------------------------------------------------------------------------
# Reference Data — CSDDD Annex I/II Social HR Adverse Impact Categories
# ---------------------------------------------------------------------------

CSDDD_SOCIAL_CATEGORIES: dict[str, dict[str, Any]] = {
    "HR-01": {
        "id": "HR-01",
        "title": "Forced / Compulsory Labour",
        "instruments": ["ILO C29", "ILO C105"],
        "severity_weight": 1.0,
        "sector_high_risk": ["agriculture", "mining", "fishing", "construction", "garments"],
        "region_high_risk": ["South Asia", "Southeast Asia", "Sub-Saharan Africa", "Gulf States"],
    },
    "HR-02": {
        "id": "HR-02",
        "title": "Child Labour",
        "instruments": ["ILO C138", "ILO C182", "UNCRC Art 32"],
        "severity_weight": 1.0,
        "sector_high_risk": ["agriculture", "mining", "fishing", "manufacturing"],
        "region_high_risk": ["Sub-Saharan Africa", "South Asia", "Latin America"],
    },
    "HR-03": {
        "id": "HR-03",
        "title": "Freedom of Association & Collective Bargaining",
        "instruments": ["ILO C87", "ILO C98"],
        "severity_weight": 0.80,
        "sector_high_risk": ["manufacturing", "logistics", "food_processing", "retail"],
        "region_high_risk": ["China", "Gulf States", "Central America"],
    },
    "HR-04": {
        "id": "HR-04",
        "title": "Discrimination in Employment",
        "instruments": ["ILO C100", "ILO C111", "ICERD"],
        "severity_weight": 0.75,
        "sector_high_risk": ["financial_services", "technology", "construction"],
        "region_high_risk": ["Global"],
    },
    "HR-05": {
        "id": "HR-05",
        "title": "Living Wage Deprivation",
        "instruments": ["ILO Living Wage guidance", "UDHR Art 23"],
        "severity_weight": 0.70,
        "sector_high_risk": ["agriculture", "garments", "food_service", "retail"],
        "region_high_risk": ["South Asia", "Southeast Asia", "Sub-Saharan Africa"],
    },
    "HR-06": {
        "id": "HR-06",
        "title": "Occupational Health & Safety Violations",
        "instruments": ["ILO C155", "ILO C187"],
        "severity_weight": 0.80,
        "sector_high_risk": ["mining", "construction", "chemicals", "agriculture"],
        "region_high_risk": ["South Asia", "Sub-Saharan Africa", "Latin America"],
    },
    "HR-07": {
        "id": "HR-07",
        "title": "Indigenous Peoples' Rights",
        "instruments": ["UNDRIP", "ILO C169", "UNGP Principle 16"],
        "severity_weight": 0.90,
        "sector_high_risk": ["extractives", "forestry", "agribusiness", "infrastructure"],
        "region_high_risk": ["Latin America", "Pacific", "Sub-Saharan Africa", "Arctic"],
    },
    "HR-08": {
        "id": "HR-08",
        "title": "Privacy & Data Rights",
        "instruments": ["UDHR Art 12", "ICCPR Art 17", "EU GDPR"],
        "severity_weight": 0.65,
        "sector_high_risk": ["technology", "financial_services", "healthcare", "media"],
        "region_high_risk": ["Global"],
    },
    "HR-09": {
        "id": "HR-09",
        "title": "Violence & Harassment",
        "instruments": ["ILO C190", "CEDAW"],
        "severity_weight": 0.85,
        "sector_high_risk": ["healthcare", "retail", "hospitality", "transportation"],
        "region_high_risk": ["Global"],
    },
    "HR-10": {
        "id": "HR-10",
        "title": "Arbitrary Detention / Security Forces",
        "instruments": ["UNGP Principle 7", "UDHR Art 9"],
        "severity_weight": 0.95,
        "sector_high_risk": ["extractives", "agribusiness", "infrastructure"],
        "region_high_risk": ["Sub-Saharan Africa", "South Asia", "Latin America"],
    },
}

# ---------------------------------------------------------------------------
# Reference Data — UNGP HRDD 6 Steps
# ---------------------------------------------------------------------------

UNGP_HRDD_STEPS: dict[str, dict[str, Any]] = {
    "S1": {
        "step": 1,
        "title": "Policy Commitment",
        "description": "Board-approved human rights policy commitment referencing UNGP; public disclosure.",
        "ungp_principles": ["13", "16"],
        "weight": 0.15,
        "assessment_indicators": [
            "Board-approved HR policy exists",
            "Policy references UNGP / ILO standards",
            "Policy is publicly available",
            "CEO/board sign-off",
        ],
    },
    "S2": {
        "step": 2,
        "title": "Human Rights Due Diligence",
        "description": "Identify and assess adverse HR impacts across value chain (actual and potential).",
        "ungp_principles": ["17", "18"],
        "weight": 0.20,
        "assessment_indicators": [
            "Salient HR issue mapping completed",
            "Value chain mapping (Tier 1+ suppliers assessed)",
            "Risk-based prioritisation documented",
            "Input from potentially affected stakeholders",
        ],
    },
    "S3": {
        "step": 3,
        "title": "Cessation / Prevention & Mitigation",
        "description": "Take action to cease, prevent and mitigate adverse human rights impacts.",
        "ungp_principles": ["19", "20"],
        "weight": 0.20,
        "assessment_indicators": [
            "Corrective action plans for identified impacts",
            "Supplier contracts include HR clauses",
            "Time-bound targets to address salient issues",
            "Leverage over business partners utilised",
        ],
    },
    "S4": {
        "step": 4,
        "title": "Remediation",
        "description": "Provide or cooperate in remediation for adverse impacts the company has caused or contributed to.",
        "ungp_principles": ["22", "25", "26", "27", "28", "29", "30", "31"],
        "weight": 0.20,
        "assessment_indicators": [
            "Operational grievance mechanism accessible to affected people",
            "Grievance mechanism meets UNGP Principle 31 effectiveness criteria",
            "Track record of providing remedy",
            "Collaboration with judicial/non-judicial mechanisms",
        ],
    },
    "S5": {
        "step": 5,
        "title": "Communication / Reporting",
        "description": "Communicate externally how adverse impacts are addressed; HRDD report / CSDDD disclosure.",
        "ungp_principles": ["21"],
        "weight": 0.12,
        "assessment_indicators": [
            "Annual HRDD report or CSRD ESRS S1/S2/S3 disclosure",
            "Coverage of all salient issues",
            "Quantitative metrics disclosed",
            "Verification / assurance obtained",
        ],
    },
    "S6": {
        "step": 6,
        "title": "Governance Integration",
        "description": "Embed HRDD into governance: executive accountability, incentives, integration with ERM.",
        "ungp_principles": ["15", "16"],
        "weight": 0.13,
        "assessment_indicators": [
            "Board-level HR oversight assigned",
            "Executive KPIs linked to HR outcomes",
            "HRDD integrated into ERM",
            "HR function adequately resourced",
        ],
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Decent Work Framework (ILO/SDG 8)
# ---------------------------------------------------------------------------

DECENT_WORK_INDICATORS: dict[str, dict[str, Any]] = {
    "DW1": {
        "id": "DW1",
        "sdg": "8.5",
        "title": "Full and Productive Employment",
        "description": "Employment rate; unemployment below 5%; youth NEET rate.",
        "benchmark": "Unemployment <5%; youth NEET <10%",
        "weight": 0.15,
    },
    "DW2": {
        "id": "DW2",
        "sdg": "8.5",
        "title": "Equal Pay for Equal Work",
        "description": "Gender pay gap <10%; pay ratio CEO:median worker <50:1.",
        "benchmark": "Gender pay gap <10%; Anker living wage compliance",
        "weight": 0.15,
    },
    "DW3": {
        "id": "DW3",
        "sdg": "8.7",
        "title": "Eradicate Forced Labour & Child Labour",
        "description": "Zero incidents of forced labour and child labour; supplier screening.",
        "benchmark": "Zero incidents; >80% tier-1 suppliers screened",
        "weight": 0.20,
    },
    "DW4": {
        "id": "DW4",
        "sdg": "8.8",
        "title": "Protect Labour Rights",
        "description": "Collective bargaining coverage; occupational injury rate.",
        "benchmark": "CB coverage >60%; LTIR <1.0 per 200k hours",
        "weight": 0.15,
    },
    "DW5": {
        "id": "DW5",
        "sdg": "8.6",
        "title": "Youth Employment & Skills",
        "description": "Apprenticeships; vocational training; youth employment programmes.",
        "benchmark": "Apprenticeship ratio >2%; training >= 20 hrs/year per employee",
        "weight": 0.10,
    },
    "DW6": {
        "id": "DW6",
        "sdg": "8.3",
        "title": "Decent Job Creation",
        "description": "Net job creation; formal sector growth; entrepreneurship support.",
        "benchmark": "Net jobs created positive; informal economy share declining",
        "weight": 0.10,
    },
    "DW7": {
        "id": "DW7",
        "sdg": "8.9",
        "title": "Sustainable Tourism",
        "description": "Only applicable to tourism sector — local employment; cultural preservation.",
        "benchmark": "Local employment >60%; community benefit sharing",
        "weight": 0.05,
    },
    "DW8": {
        "id": "DW8",
        "sdg": "8.10",
        "title": "Financial Services Access",
        "description": "Access to banking, insurance, and financial services for all.",
        "benchmark": "Unbanked customer outreach; microfinance provision",
        "weight": 0.10,
    },
}

# ---------------------------------------------------------------------------
# Reference Data — Country Labour Risk Profiles (20+)
# ---------------------------------------------------------------------------

COUNTRY_LABOUR_RISK_PROFILES: dict[str, dict[str, Any]] = {
    "GBR": {
        "country": "United Kingdom",
        "iso3": "GBR",
        "region": "Western Europe",
        "labour_risk_tier": 1,
        "labour_risk_label": "Low",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "low",
        "child_labour_risk": "negligible",
        "freedom_of_association_risk": "low",
        "living_wage_gap_pct": 5,
        "gender_pay_gap_pct": 14.3,
        "union_density_pct": 23,
        "notable_risks": ["migrant_worker_exploitation_in_agriculture", "modern_slavery_supply_chain"],
    },
    "DEU": {
        "country": "Germany",
        "iso3": "DEU",
        "region": "Western Europe",
        "labour_risk_tier": 1,
        "labour_risk_label": "Low",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "low",
        "child_labour_risk": "negligible",
        "freedom_of_association_risk": "low",
        "living_wage_gap_pct": 3,
        "gender_pay_gap_pct": 17.6,
        "union_density_pct": 17,
        "notable_risks": ["gender_pay_gap", "mini_job_precarious_employment"],
        "lksg_applicable": True,
    },
    "FRA": {
        "country": "France",
        "iso3": "FRA",
        "region": "Western Europe",
        "labour_risk_tier": 1,
        "labour_risk_label": "Low",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "low",
        "child_labour_risk": "negligible",
        "freedom_of_association_risk": "low",
        "living_wage_gap_pct": 2,
        "gender_pay_gap_pct": 16.8,
        "union_density_pct": 11,
        "notable_risks": ["undocumented_migrant_labour", "seasonal_agricultural_workers"],
        "duty_of_vigilance_applicable": True,
    },
    "USA": {
        "country": "United States",
        "iso3": "USA",
        "region": "North America",
        "labour_risk_tier": 2,
        "labour_risk_label": "Medium-Low",
        "ilo_conventions_ratified": 2,
        "ilo_core_ratified_all": False,
        "ilo_core_gaps": ["C087", "C098", "C138", "C111"],
        "forced_labour_risk": "low",
        "child_labour_risk": "low",
        "freedom_of_association_risk": "medium",
        "living_wage_gap_pct": 20,
        "gender_pay_gap_pct": 18.0,
        "union_density_pct": 10,
        "notable_risks": [
            "limited_ILO_ratification",
            "gig_economy_worker_rights",
            "migrant_farmworker_exploitation",
            "right_to_work_laws_restrict_unions",
        ],
    },
    "CHN": {
        "country": "China",
        "iso3": "CHN",
        "region": "East Asia",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 4,
        "ilo_core_ratified_all": False,
        "ilo_core_gaps": ["C087", "C098", "C105", "C111"],
        "forced_labour_risk": "very_high",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "very_high",
        "living_wage_gap_pct": 30,
        "gender_pay_gap_pct": 22.0,
        "union_density_pct": 70,
        "notable_risks": [
            "state_controlled_unions_only",
            "Xinjiang_forced_labour_concerns",
            "strike_restrictions",
            "prison_labour",
            "migrant_hukou_discrimination",
        ],
        "uflpa_watch": True,
    },
    "IND": {
        "country": "India",
        "iso3": "IND",
        "region": "South Asia",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 6,
        "ilo_core_ratified_all": False,
        "ilo_core_gaps": ["C087", "C098"],
        "forced_labour_risk": "high",
        "child_labour_risk": "high",
        "freedom_of_association_risk": "medium",
        "living_wage_gap_pct": 60,
        "gender_pay_gap_pct": 28.0,
        "union_density_pct": 7,
        "notable_risks": [
            "bonded_labour_in_agriculture_and_brick_kilns",
            "child_labour_in_textiles_and_mining",
            "caste_discrimination_in_employment",
            "informal_economy_80pct",
        ],
    },
    "BGD": {
        "country": "Bangladesh",
        "iso3": "BGD",
        "region": "South Asia",
        "labour_risk_tier": 4,
        "labour_risk_label": "Very High",
        "ilo_conventions_ratified": 7,
        "ilo_core_ratified_all": False,
        "ilo_core_gaps": ["C087"],
        "forced_labour_risk": "high",
        "child_labour_risk": "high",
        "freedom_of_association_risk": "very_high",
        "living_wage_gap_pct": 75,
        "gender_pay_gap_pct": 30.0,
        "union_density_pct": 3,
        "notable_risks": [
            "garment_sector_unsafe_conditions",
            "union_suppression_in_EPZs",
            "child_labour_in_tanneries",
        ],
    },
    "BRA": {
        "country": "Brazil",
        "iso3": "BRA",
        "region": "Latin America",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "high",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "medium",
        "living_wage_gap_pct": 40,
        "gender_pay_gap_pct": 20.0,
        "union_density_pct": 16,
        "notable_risks": [
            "slave_labour_in_agriculture_and_construction",
            "deforestation_linked_land_rights_conflicts",
            "indigenous_peoples_rights_violations",
        ],
        "dirty_list": True,
    },
    "NGA": {
        "country": "Nigeria",
        "iso3": "NGA",
        "region": "Sub-Saharan Africa",
        "labour_risk_tier": 4,
        "labour_risk_label": "Very High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "high",
        "child_labour_risk": "very_high",
        "freedom_of_association_risk": "medium",
        "living_wage_gap_pct": 80,
        "gender_pay_gap_pct": 35.0,
        "union_density_pct": 9,
        "notable_risks": [
            "child_labour_in_artisanal_mining",
            "oil_sector_community_rights",
            "trafficking_for_forced_labour",
            "informal_economy_90pct",
        ],
    },
    "ETH": {
        "country": "Ethiopia",
        "iso3": "ETH",
        "region": "Sub-Saharan Africa",
        "labour_risk_tier": 4,
        "labour_risk_label": "Very High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "very_high",
        "child_labour_risk": "very_high",
        "freedom_of_association_risk": "high",
        "living_wage_gap_pct": 90,
        "gender_pay_gap_pct": 40.0,
        "union_density_pct": 4,
        "notable_risks": [
            "garment_sector_low_wages",
            "forced_agricultural_labour",
            "child_labour_in_coffee_and_flowers",
        ],
    },
    "MEX": {
        "country": "Mexico",
        "iso3": "MEX",
        "region": "Latin America",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "medium",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "high",
        "living_wage_gap_pct": 50,
        "gender_pay_gap_pct": 14.0,
        "union_density_pct": 13,
        "notable_risks": [
            "protection_contract_unions_corrupt",
            "migrant_farmworkers_exploitation",
            "femicide_and_workplace_violence",
        ],
    },
    "TUR": {
        "country": "Turkey",
        "iso3": "TUR",
        "region": "Eastern Europe",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "medium",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "high",
        "living_wage_gap_pct": 30,
        "gender_pay_gap_pct": 18.0,
        "union_density_pct": 12,
        "notable_risks": [
            "Syrian_refugee_informal_labour",
            "union_repression_in_public_sector",
            "seasonal_agricultural_child_labour",
        ],
    },
    "VNM": {
        "country": "Vietnam",
        "iso3": "VNM",
        "region": "Southeast Asia",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 7,
        "ilo_core_ratified_all": False,
        "ilo_core_gaps": ["C087"],
        "forced_labour_risk": "medium",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "very_high",
        "living_wage_gap_pct": 55,
        "gender_pay_gap_pct": 12.0,
        "union_density_pct": 70,
        "notable_risks": [
            "state_controlled_VGCL_union_only",
            "strike_restrictions_in_essential_sectors",
            "excessive_overtime_in_garments",
        ],
    },
    "IDN": {
        "country": "Indonesia",
        "iso3": "IDN",
        "region": "Southeast Asia",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "medium",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "medium",
        "living_wage_gap_pct": 50,
        "gender_pay_gap_pct": 16.0,
        "union_density_pct": 6,
        "notable_risks": [
            "palm_oil_forced_labour_debt_bondage",
            "domestic_workers_exclusions",
            "migrant_labour_exploitation",
        ],
    },
    "SAU": {
        "country": "Saudi Arabia",
        "iso3": "SAU",
        "region": "Middle East",
        "labour_risk_tier": 4,
        "labour_risk_label": "Very High",
        "ilo_conventions_ratified": 5,
        "ilo_core_ratified_all": False,
        "ilo_core_gaps": ["C087", "C098", "C111"],
        "forced_labour_risk": "very_high",
        "child_labour_risk": "low",
        "freedom_of_association_risk": "very_high",
        "living_wage_gap_pct": 20,
        "gender_pay_gap_pct": 25.0,
        "union_density_pct": 0,
        "notable_risks": [
            "kafala_sponsorship_system_forced_labour",
            "no_trade_unions_permitted",
            "domestic_worker_exploitation",
            "gender_discrimination_in_workplace",
        ],
    },
    "ZAF": {
        "country": "South Africa",
        "iso3": "ZAF",
        "region": "Sub-Saharan Africa",
        "labour_risk_tier": 2,
        "labour_risk_label": "Medium",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "low",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "low",
        "living_wage_gap_pct": 45,
        "gender_pay_gap_pct": 23.0,
        "union_density_pct": 25,
        "notable_risks": [
            "mining_sector_health_safety",
            "farm_worker_seasonal_insecurity",
            "youth_unemployment_60pct",
        ],
    },
    "COD": {
        "country": "Democratic Republic of Congo",
        "iso3": "COD",
        "region": "Sub-Saharan Africa",
        "labour_risk_tier": 4,
        "labour_risk_label": "Very High",
        "ilo_conventions_ratified": 7,
        "ilo_core_ratified_all": False,
        "ilo_core_gaps": ["C138"],
        "forced_labour_risk": "very_high",
        "child_labour_risk": "very_high",
        "freedom_of_association_risk": "high",
        "living_wage_gap_pct": 95,
        "gender_pay_gap_pct": 40.0,
        "union_density_pct": 2,
        "notable_risks": [
            "artisanal_cobalt_child_labour",
            "conflict_minerals_forced_labour",
            "sexual_violence_in_mining_communities",
        ],
        "conflict_affected": True,
    },
    "PHL": {
        "country": "Philippines",
        "iso3": "PHL",
        "region": "Southeast Asia",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "medium",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "high",
        "living_wage_gap_pct": 55,
        "gender_pay_gap_pct": 8.0,
        "union_density_pct": 9,
        "notable_risks": [
            "endo_contractualisation",
            "ofw_overseas_worker_exploitation",
            "trade_union_leader_killings",
        ],
    },
    "PER": {
        "country": "Peru",
        "iso3": "PER",
        "region": "Latin America",
        "labour_risk_tier": 3,
        "labour_risk_label": "High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "high",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "medium",
        "living_wage_gap_pct": 50,
        "gender_pay_gap_pct": 22.0,
        "union_density_pct": 5,
        "notable_risks": [
            "artisanal_gold_forced_labour",
            "indigenous_land_rights_in_mining",
            "informal_economy_70pct",
        ],
    },
    "KHM": {
        "country": "Cambodia",
        "iso3": "KHM",
        "region": "Southeast Asia",
        "labour_risk_tier": 4,
        "labour_risk_label": "Very High",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "high",
        "child_labour_risk": "medium",
        "freedom_of_association_risk": "very_high",
        "living_wage_gap_pct": 65,
        "gender_pay_gap_pct": 13.0,
        "union_density_pct": 8,
        "notable_risks": [
            "garment_union_crackdowns",
            "land_grabs_displacement",
            "trafficking_for_forced_online_scam_labour",
        ],
    },
    "JPN": {
        "country": "Japan",
        "iso3": "JPN",
        "region": "East Asia",
        "labour_risk_tier": 2,
        "labour_risk_label": "Medium-Low",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "low",
        "child_labour_risk": "negligible",
        "freedom_of_association_risk": "low",
        "living_wage_gap_pct": 10,
        "gender_pay_gap_pct": 22.1,
        "union_density_pct": 17,
        "notable_risks": [
            "technical_intern_training_programme_abuses",
            "overwork_karoshi_culture",
            "gender_pay_gap_significant",
        ],
    },
    "KOR": {
        "country": "South Korea",
        "iso3": "KOR",
        "region": "East Asia",
        "labour_risk_tier": 2,
        "labour_risk_label": "Medium-Low",
        "ilo_conventions_ratified": 8,
        "ilo_core_ratified_all": True,
        "forced_labour_risk": "low",
        "child_labour_risk": "negligible",
        "freedom_of_association_risk": "medium",
        "living_wage_gap_pct": 8,
        "gender_pay_gap_pct": 31.1,
        "union_density_pct": 14,
        "notable_risks": [
            "highest_OECD_gender_pay_gap",
            "subcontract_worker_rights",
            "long_working_hours",
        ],
    },
}

# ---------------------------------------------------------------------------
# Conflict-affected / high-risk areas (CAHRA) list
# ---------------------------------------------------------------------------

CAHRA_COUNTRIES: set[str] = {
    "COD", "SOM", "YEM", "SYR", "IRQ", "AFG", "SDN", "SSD", "CAF",
    "LBY", "MMR", "ERI", "PRK", "VEN", "HTI", "MLI", "BFA",
}

# ---------------------------------------------------------------------------
# Internal scoring helpers
# ---------------------------------------------------------------------------

def _score_ilo_compliance(supplier_countries: list[str]) -> dict[str, Any]:
    """Compute ILO compliance score for a set of supplier countries."""
    if not supplier_countries:
        return {"ilo_composite": 0.70, "note": "No supplier countries provided — using sector default"}

    total_weight = 0.0
    weighted_sum = 0.0
    country_results = []
    for iso3 in supplier_countries:
        profile = COUNTRY_LABOUR_RISK_PROFILES.get(iso3.upper())
        if not profile:
            score = 0.65
            note = "Country not in reference database — assuming moderate risk"
        else:
            ratified = profile.get("ilo_conventions_ratified", 0)
            all_core = profile.get("ilo_core_ratified_all", False)
            tier = profile.get("labour_risk_tier", 3)
            base = ratified / 8
            if all_core:
                base = min(1.0, base + 0.10)
            tier_penalty = {1: 0, 2: 0.05, 3: 0.20, 4: 0.40}.get(tier, 0.20)
            score = max(0.0, base - tier_penalty)
            note = f"Labour risk tier {tier}; ILO core conventions: {ratified}/8 ratified"
        total_weight += 1
        weighted_sum += score
        country_results.append({"country": iso3, "ilo_score": round(score, 4), "note": note})

    ilo_composite = weighted_sum / total_weight if total_weight > 0 else 0
    return {
        "ilo_composite": round(ilo_composite, 4),
        "supplier_country_results": country_results,
    }


def _score_ungp_hrdd(
    policy_commitment: bool,
    value_chain_mapping: bool,
    corrective_actions: int,
    grievance_mechanism: bool,
    annual_reporting: bool,
    board_oversight: bool,
) -> dict[str, Any]:
    """Score UNGP HRDD across 6 steps."""
    step_scores = {
        "S1": 1.0 if policy_commitment else 0.20,
        "S2": 1.0 if value_chain_mapping else 0.10,
        "S3": min(1.0, 0.30 + corrective_actions * 0.14),
        "S4": 1.0 if grievance_mechanism else 0.15,
        "S5": 1.0 if annual_reporting else 0.20,
        "S6": 1.0 if board_oversight else 0.20,
    }
    total_weight = sum(s["weight"] for s in UNGP_HRDD_STEPS.values())
    composite = sum(
        step_scores[sid] * UNGP_HRDD_STEPS[sid]["weight"]
        for sid in UNGP_HRDD_STEPS
    ) / total_weight
    return {
        "ungp_composite": round(composite, 4),
        "step_scores": {
            sid: {
                "score": round(step_scores[sid], 4),
                "title": UNGP_HRDD_STEPS[sid]["title"],
                "weight": UNGP_HRDD_STEPS[sid]["weight"],
            }
            for sid in step_scores
        },
        "ungp_maturity": (
            "Advanced" if composite >= 0.80
            else "Established" if composite >= 0.60
            else "Developing" if composite >= 0.40
            else "Nascent"
        ),
    }


def _score_social_taxonomy_objectives(
    obj1_inputs: dict[str, Any],
    obj2_inputs: dict[str, Any],
    obj3_inputs: dict[str, Any],
) -> dict[str, Any]:
    """Score EU Social Taxonomy 3 objectives + DNSH checks."""

    def _score_obj1(inp: dict) -> float:
        living_wage_compliance = inp.get("living_wage_compliance_pct", 50) / 100
        h_s_score = inp.get("h_and_s_score", 0.60)
        job_security = inp.get("permanent_contract_pct", 60) / 100
        cb_coverage = inp.get("collective_bargaining_coverage_pct", 30) / 100
        work_life = inp.get("work_life_balance_score", 0.50)
        return (
            living_wage_compliance * 0.25
            + h_s_score * 0.25
            + job_security * 0.20
            + cb_coverage * 0.15
            + work_life * 0.15
        )

    def _score_obj2(inp: dict) -> float:
        healthcare = inp.get("healthcare_access_score", 0.50)
        housing = inp.get("affordable_housing_score", 0.50)
        education = inp.get("education_score", 0.50)
        food = inp.get("food_security_score", 0.50)
        financial = inp.get("financial_inclusion_score", 0.50)
        return (
            healthcare * 0.25
            + housing * 0.20
            + education * 0.20
            + food * 0.20
            + financial * 0.15
        )

    def _score_obj3(inp: dict) -> float:
        inclusive = inp.get("inclusive_growth_score", 0.50)
        digital = inp.get("digital_access_score", 0.50)
        cultural = inp.get("cultural_heritage_score", 0.50)
        just_transition = inp.get("just_transition_score", 0.50)
        stakeholder = inp.get("stakeholder_engagement_score", 0.50)
        return (
            inclusive * 0.25
            + digital * 0.20
            + cultural * 0.20
            + just_transition * 0.20
            + stakeholder * 0.15
        )

    s1 = _score_obj1(obj1_inputs)
    s2 = _score_obj2(obj2_inputs)
    s3 = _score_obj3(obj3_inputs)

    # DNSH: each objective must not significantly harm the other two (threshold 0.30)
    dnsh_flags = []
    if s1 < 0.30:
        dnsh_flags.append("OBJ1_DNSH_FAIL — Decent Work score too low; harmful to workforce")
    if s2 < 0.30:
        dnsh_flags.append("OBJ2_DNSH_FAIL — Adequate Living Standards score too low")
    if s3 < 0.30:
        dnsh_flags.append("OBJ3_DNSH_FAIL — Inclusive Communities score too low")

    safeguards_met = s1 >= 0.40 and s2 >= 0.30 and s3 >= 0.30
    composite = (s1 * 0.40) + (s2 * 0.35) + (s3 * 0.25)

    if composite >= 0.75 and not dnsh_flags and safeguards_met:
        alignment = "taxonomy_aligned"
    elif composite >= 0.50 and safeguards_met:
        alignment = "taxonomy_enabling"
    elif composite >= 0.30:
        alignment = "transitioning"
    else:
        alignment = "not_taxonomy_eligible"

    return {
        "obj1_decent_work_score": round(s1, 4),
        "obj2_living_standards_score": round(s2, 4),
        "obj3_inclusive_communities_score": round(s3, 4),
        "social_taxonomy_composite": round(composite, 4),
        "dnsh_flags": dnsh_flags,
        "minimum_safeguards_met": safeguards_met,
        "taxonomy_alignment": alignment,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assess_social_taxonomy(
    entity_name: str,
    nace_code: str,
    sector: str,
    country_of_operations: str = "GBR",
    # OBJ1 — Decent Work
    living_wage_compliance_pct: float = 70.0,
    h_and_s_score: float = 0.65,
    permanent_contract_pct: float = 75.0,
    collective_bargaining_coverage_pct: float = 40.0,
    work_life_balance_score: float = 0.60,
    # OBJ2 — Living Standards
    healthcare_access_score: float = 0.60,
    affordable_housing_score: float = 0.50,
    education_score: float = 0.55,
    food_security_score: float = 0.55,
    financial_inclusion_score: float = 0.55,
    # OBJ3 — Inclusive Communities
    inclusive_growth_score: float = 0.55,
    digital_access_score: float = 0.50,
    cultural_heritage_score: float = 0.55,
    just_transition_score: float = 0.50,
    stakeholder_engagement_score: float = 0.55,
    # UNGP / HRDD inputs
    policy_commitment: bool = True,
    value_chain_mapping: bool = False,
    corrective_actions_count: int = 2,
    grievance_mechanism: bool = True,
    annual_reporting: bool = True,
    board_oversight: bool = False,
    # ILO
    supplier_countries: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Full EU Social Taxonomy assessment for an entity.

    Scores 3 EU Social Taxonomy objectives (Decent Work, Adequate Living Standards,
    Inclusive Communities), applies DNSH cross-checks, evaluates UNGP HRDD maturity,
    ILO convention compliance across the supply chain, and determines taxonomy alignment.
    """
    now = datetime.utcnow().isoformat() + "Z"

    obj_scores = _score_social_taxonomy_objectives(
        obj1_inputs={
            "living_wage_compliance_pct": living_wage_compliance_pct,
            "h_and_s_score": h_and_s_score,
            "permanent_contract_pct": permanent_contract_pct,
            "collective_bargaining_coverage_pct": collective_bargaining_coverage_pct,
            "work_life_balance_score": work_life_balance_score,
        },
        obj2_inputs={
            "healthcare_access_score": healthcare_access_score,
            "affordable_housing_score": affordable_housing_score,
            "education_score": education_score,
            "food_security_score": food_security_score,
            "financial_inclusion_score": financial_inclusion_score,
        },
        obj3_inputs={
            "inclusive_growth_score": inclusive_growth_score,
            "digital_access_score": digital_access_score,
            "cultural_heritage_score": cultural_heritage_score,
            "just_transition_score": just_transition_score,
            "stakeholder_engagement_score": stakeholder_engagement_score,
        },
    )

    ungp = _score_ungp_hrdd(
        policy_commitment=policy_commitment,
        value_chain_mapping=value_chain_mapping,
        corrective_actions=corrective_actions_count,
        grievance_mechanism=grievance_mechanism,
        annual_reporting=annual_reporting,
        board_oversight=board_oversight,
    )

    ilo = _score_ilo_compliance(supplier_countries or [country_of_operations])

    sector_hr_flags = [
        cat_id
        for cat_id, cat in CSDDD_SOCIAL_CATEGORIES.items()
        if sector in cat.get("sector_high_risk", [])
    ]

    country_profile = COUNTRY_LABOUR_RISK_PROFILES.get(country_of_operations.upper(), {})
    country_risk_tier = country_profile.get("labour_risk_tier", 2)
    cahra_flag = country_of_operations.upper() in CAHRA_COUNTRIES

    csrd_esrs = {
        "ESRS_S1": "Own Workforce — covers OBJ1 Decent Work entirely",
        "ESRS_S2": "Workers in Value Chain — OBJ1 extended to supply chain",
        "ESRS_S3": "Affected Communities — OBJ2 + OBJ3",
        "ESRS_S4": "Consumers and End-users — OBJ2 (wellbeing/safety)",
    }

    recs: list[str] = []
    if obj_scores["obj1_decent_work_score"] < 0.60:
        recs.append("Improve Decent Work performance: increase living wage compliance and H&S standards.")
    if not value_chain_mapping:
        recs.append("Complete a value chain mapping to identify salient HR issues (UNGP Step 2).")
    if not board_oversight:
        recs.append("Assign board-level accountability for human rights to strengthen UNGP Step 6.")
    if cahra_flag:
        recs.append(f"Operations in CAHRA country ({country_of_operations}) — enhanced HRDD required per CSDDD Art 6.")
    if sector_hr_flags:
        recs.append(f"Sector '{sector}' has elevated risk in: {', '.join(sector_hr_flags)} — prioritise these areas.")
    if not recs:
        recs.append("Social taxonomy performance is strong. Maintain current standards and continue annual disclosure.")

    return {
        "assessment_id": f"ST-{entity_name.replace(' ', '_')}-{now[:10]}",
        "generated_at": now,
        "entity_name": entity_name,
        "nace_code": nace_code,
        "sector": sector,
        "country_of_operations": country_of_operations,
        "eu_social_taxonomy": obj_scores,
        "ungp_hrdd_assessment": ungp,
        "ilo_compliance": ilo,
        "sector_hr_risk_categories": sector_hr_flags,
        "country_labour_risk": {
            "iso3": country_of_operations,
            "risk_tier": country_risk_tier,
            "cahra": cahra_flag,
            "profile": country_profile,
        },
        "csrd_esrs_mapping": csrd_esrs,
        "recommendations": recs,
    }


def conduct_hrdd(
    company_name: str,
    supplier_countries: list[str],
    supply_chain_tiers: int = 2,
    sector: str = "manufacturing",
    policy_commitment: bool = True,
    salient_issues_mapped: bool = False,
    corrective_action_plans: int = 1,
    grievance_mechanism: bool = True,
    annual_reporting: bool = False,
    board_oversight: bool = False,
    third_party_audit_coverage_pct: float = 40.0,
    ilo_compliance_self_assessed: bool = True,
    fpic_process_in_place: bool = False,
) -> dict[str, Any]:
    """
    Human Rights Due Diligence assessment per UNGP / CSDDD / OECD DDG.

    Returns UNGP step scores, country risk breakdown, CSDDD adverse impact
    likelihood matrix, OECD DDG 5-step alignment, and risk priority recommendations.
    """
    now = datetime.utcnow().isoformat() + "Z"

    ungp = _score_ungp_hrdd(
        policy_commitment=policy_commitment,
        value_chain_mapping=salient_issues_mapped,
        corrective_actions=corrective_action_plans,
        grievance_mechanism=grievance_mechanism,
        annual_reporting=annual_reporting,
        board_oversight=board_oversight,
    )

    ilo = _score_ilo_compliance(supplier_countries)

    high_risk_countries = [
        iso3 for iso3 in supplier_countries
        if COUNTRY_LABOUR_RISK_PROFILES.get(iso3.upper(), {}).get("labour_risk_tier", 2) >= 3
    ]
    cahra_suppliers = [iso3 for iso3 in supplier_countries if iso3.upper() in CAHRA_COUNTRIES]

    csddd_impact_matrix = {}
    for cat_id, cat in CSDDD_SOCIAL_CATEGORIES.items():
        base_likelihood = 0.30
        if sector in cat.get("sector_high_risk", []):
            base_likelihood += 0.30
        if cahra_suppliers:
            base_likelihood += 0.10
        severity = cat["severity_weight"]
        risk_score = round(min(1.0, base_likelihood) * severity, 4)
        csddd_impact_matrix[cat_id] = {
            "title": cat["title"],
            "likelihood": round(min(1.0, base_likelihood), 4),
            "severity": severity,
            "risk_score": risk_score,
            "priority": "high" if risk_score >= 0.60 else "medium" if risk_score >= 0.35 else "low",
        }

    oecd_steps = {
        "step1_embed_hrdd": policy_commitment and board_oversight,
        "step2_identify_impacts": salient_issues_mapped,
        "step3_respond": corrective_action_plans >= 1,
        "step4_track": annual_reporting,
        "step5_communicate": annual_reporting and third_party_audit_coverage_pct >= 30,
    }
    oecd_score = sum(1 for v in oecd_steps.values() if v) / len(oecd_steps)

    priority_issues = sorted(
        [(cid, v) for cid, v in csddd_impact_matrix.items() if v["priority"] == "high"],
        key=lambda x: x[1]["risk_score"],
        reverse=True,
    )

    recs: list[str] = []
    if not oecd_steps["step2_identify_impacts"]:
        recs.append("Complete a salient human rights issues mapping (OECD DDG Step 2 / UNGP Principle 17).")
    if not oecd_steps["step1_embed_hrdd"]:
        recs.append("Appoint a board-level HR accountable executive and publish a formal HR policy commitment.")
    if high_risk_countries:
        recs.append(f"Heightened HRDD required for suppliers in high-risk countries: {', '.join(high_risk_countries)}.")
    if cahra_suppliers:
        recs.append(
            f"Conflict-affected / high-risk area suppliers detected ({', '.join(cahra_suppliers)}): "
            "apply enhanced monitoring per CSDDD Art 6 and OECD DDG Annex II."
        )
    if priority_issues:
        top_id, top_data = priority_issues[0]
        recs.append(
            f"Highest priority adverse impact: {top_id} — {top_data['title']} "
            f"(risk score {top_data['risk_score']}). Initiate prevention/mitigation action plan."
        )
    if not fpic_process_in_place and cahra_suppliers:
        recs.append("Implement FPIC process for activities affecting indigenous peoples / local communities.")
    if ungp["ungp_composite"] < 0.50:
        recs.append("UNGP HRDD maturity below 'Established' — prioritise Step 3 (Cessation/Mitigation) improvement.")

    return {
        "assessment_id": f"HRDD-{company_name.replace(' ', '_')}-{now[:10]}",
        "generated_at": now,
        "company_name": company_name,
        "sector": sector,
        "supplier_countries": supplier_countries,
        "supply_chain_tiers_mapped": supply_chain_tiers,
        "ungp_hrdd": ungp,
        "ilo_compliance": ilo,
        "csddd_adverse_impact_matrix": csddd_impact_matrix,
        "priority_hr_issues": [{"id": cid, **v} for cid, v in priority_issues],
        "oecd_ddg_alignment": {
            "steps": oecd_steps,
            "score": round(oecd_score, 4),
            "maturity": (
                "Strong" if oecd_score >= 0.80
                else "Moderate" if oecd_score >= 0.60
                else "Weak" if oecd_score >= 0.40
                else "Nascent"
            ),
        },
        "supply_chain_risk_summary": {
            "high_risk_countries": high_risk_countries,
            "cahra_countries": cahra_suppliers,
            "third_party_audit_coverage_pct": third_party_audit_coverage_pct,
            "ilo_compliance_self_assessed": ilo_compliance_self_assessed,
            "fpic_in_place": fpic_process_in_place,
        },
        "csddd_scope_applicable": supply_chain_tiers >= 1,
        "recommendations": recs,
    }


def get_social_taxonomy_criteria() -> dict[str, Any]:
    """
    Return all reference data for the EU Social Taxonomy and related frameworks.

    Returns
    -------
    dict
        EU Social Taxonomy objectives, ILO conventions, CSDDD social categories,
        UNGP steps, Decent Work indicators, and country labour risk profiles.
    """
    return {
        "eu_social_taxonomy": EU_SOCIAL_TAXONOMY_OBJECTIVES,
        "ilo_core_conventions": ILO_CORE_CONVENTIONS,
        "csddd_social_categories": CSDDD_SOCIAL_CATEGORIES,
        "ungp_hrdd_steps": UNGP_HRDD_STEPS,
        "decent_work_indicators": DECENT_WORK_INDICATORS,
        "country_labour_risk_profiles": COUNTRY_LABOUR_RISK_PROFILES,
    }
