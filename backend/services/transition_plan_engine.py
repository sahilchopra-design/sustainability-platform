"""
Climate Transition Plan Assessment Engine
=============================================
Exhaustive assessment against 6 frameworks at the datapoint/metric level:

  1. TPT Framework (Transition Plan Taskforce — UK FCA endorsed)
  2. GFANZ (Glasgow Financial Alliance for Net Zero)
  3. IIGCC Net Zero Investment Framework (NZIF) v2.0
  4. CSDDD Article 22 (Directive (EU) 2024/1760)
  5. CSRD ESRS E1 — Climate Change (EFRAG IG-3)
  6. CDP Climate Change Questionnaire C4 — Targets and Performance

Includes a 55+ datapoint inter-framework cross-mapping at the metric level.

References:
  - TPT Disclosure Framework (Oct 2023 Final)
  - GFANZ Recommendations and Guidance (Jun 2022 + Nov 2022)
  - IIGCC NZIF v2.0 (Mar 2024)
  - Directive (EU) 2024/1760 Article 22
  - ESRS E1 Climate Change (EFRAG Set 1, delegated 2023/2772)
  - CDP 2024 Climate Change Questionnaire
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import hashlib

# ═══════════════════════════════════════════════════════════════════════════════
# 1. TPT FRAMEWORK — 5 Elements, 16 Sub-Elements
# ═══════════════════════════════════════════════════════════════════════════════

TPT_FRAMEWORK: dict = {
    "TPT-F": {
        "element": "Foundations",
        "sub_elements": {
            "TPT-F-1": {"name": "Strategic ambition", "description": "Net-zero commitment with interim targets; alignment with 1.5C or well-below 2C; scope coverage", "weight": 0.15,
                        "datapoints": ["net_zero_year", "interim_target_2030", "interim_target_2035", "paris_scenario", "scope_coverage"]},
            "TPT-F-2": {"name": "Business model and value chain", "description": "Current business model climate dependencies; planned changes to products/services/operations; value chain decarbonisation", "weight": 0.10,
                        "datapoints": ["business_model_description", "climate_dependencies", "planned_changes", "value_chain_emissions_pct"]},
            "TPT-F-3": {"name": "Assumptions and external factors", "description": "Policy assumptions, technology readiness, market evolution, physical risk materiality", "weight": 0.05,
                        "datapoints": ["policy_assumptions", "technology_assumptions", "market_assumptions", "physical_risk_materiality"]},
        }
    },
    "TPT-IS": {
        "element": "Implementation Strategy",
        "sub_elements": {
            "TPT-IS-1": {"name": "Business operations", "description": "Operational changes for decarbonisation; energy efficiency programmes; renewable energy procurement", "weight": 0.10,
                         "datapoints": ["operational_changes", "energy_efficiency_plan", "renewable_procurement_target", "fleet_electrification"]},
            "TPT-IS-2": {"name": "Products and services", "description": "Revenue alignment trajectory; phase-out of carbon-intensive products; green product development", "weight": 0.10,
                         "datapoints": ["revenue_aligned_pct", "phase_out_plans", "green_product_pipeline", "taxonomy_alignment_target"]},
            "TPT-IS-3": {"name": "Policies and conditions", "description": "Internal carbon price; investment exclusion criteria; procurement standards; engagement conditions", "weight": 0.05,
                         "datapoints": ["internal_carbon_price_eur_tco2", "exclusion_criteria", "procurement_standards", "engagement_conditions"]},
            "TPT-IS-4": {"name": "Financial planning", "description": "CapEx allocation to climate; R&D investment; M&A climate lens; funding strategy", "weight": 0.10,
                         "datapoints": ["capex_aligned_eur", "capex_aligned_pct", "rd_climate_spend", "ma_climate_criteria", "green_bond_issued"]},
        }
    },
    "TPT-ES": {
        "element": "Engagement Strategy",
        "sub_elements": {
            "TPT-ES-1": {"name": "Value chain engagement", "description": "Supplier decarbonisation programmes; customer transition support; Scope 3 reduction partnerships", "weight": 0.05,
                         "datapoints": ["supplier_engagement_pct", "scope3_reduction_target", "customer_transition_support", "supplier_sbti_coverage"]},
            "TPT-ES-2": {"name": "Industry collaboration", "description": "Sector initiatives participation; pre-competitive R&D; standard-setting", "weight": 0.03,
                         "datapoints": ["industry_initiatives", "pre_competitive_partnerships", "standard_setting_participation"]},
            "TPT-ES-3": {"name": "Government and public sector", "description": "Policy advocacy alignment with net-zero; public-private partnerships; just transition", "weight": 0.02,
                         "datapoints": ["policy_advocacy_alignment", "public_private_partnerships", "just_transition_commitment"]},
        }
    },
    "TPT-MT": {
        "element": "Metrics and Targets",
        "sub_elements": {
            "TPT-MT-1": {"name": "GHG metrics", "description": "Scope 1/2/3 absolute emissions; intensity metrics; methodology (GHG Protocol); verification status", "weight": 0.10,
                         "datapoints": ["scope1_tco2e", "scope2_location_tco2e", "scope2_market_tco2e", "scope3_total_tco2e", "scope3_by_category", "ghg_intensity_revenue", "ghg_methodology", "verification_status"]},
            "TPT-MT-2": {"name": "Non-GHG metrics", "description": "Energy mix and intensity; taxonomy-aligned CapEx/revenue; temperature rating; portfolio alignment", "weight": 0.05,
                         "datapoints": ["energy_consumption_mwh", "renewable_share_pct", "energy_intensity", "taxonomy_capex_pct", "taxonomy_turnover_pct", "implied_temperature_rise"]},
            "TPT-MT-3": {"name": "Targets", "description": "Short-term (1-3yr), medium-term (3-10yr), long-term (10yr+); science-based; sectoral pathway alignment", "weight": 0.08,
                         "datapoints": ["target_short_term", "target_medium_term", "target_long_term", "sbti_validated", "sbti_target_type", "sector_pathway_aligned"]},
            "TPT-MT-4": {"name": "Carbon credits", "description": "Offset strategy; volume; quality criteria (ICVCM CCP); vintage; role limitation (residual only)", "weight": 0.02,
                         "datapoints": ["credits_volume_tco2", "credit_type", "credit_certification", "credit_vintage", "residual_emissions_only"]},
        }
    },
    "TPT-G": {
        "element": "Governance",
        "sub_elements": {
            "TPT-G-1": {"name": "Board oversight", "description": "Board climate competence; reporting frequency; strategic direction approval; risk oversight", "weight": 0.05,
                         "datapoints": ["board_climate_competence", "board_reporting_frequency", "board_strategy_approval", "board_risk_oversight"]},
            "TPT-G-2": {"name": "Management roles", "description": "C-suite climate responsibility; cross-functional coordination; implementation accountability", "weight": 0.03,
                         "datapoints": ["csuite_climate_role", "cross_functional_team", "implementation_accountability"]},
            "TPT-G-3": {"name": "Incentives", "description": "Executive remuneration linked to climate KPIs; short-term and long-term incentive plans", "weight": 0.05,
                         "datapoints": ["exec_remuneration_linked", "sti_climate_kpi", "lti_climate_kpi", "remuneration_pct_climate"]},
            "TPT-G-4": {"name": "Skills and culture", "description": "Climate training programmes; organisational climate literacy; change management", "weight": 0.02,
                         "datapoints": ["training_programme", "climate_literacy_coverage", "change_management_plan"]},
        }
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. GFANZ — Net Zero Components + Sub-Alliance Specifics
# ═══════════════════════════════════════════════════════════════════════════════

GFANZ_COMPONENTS: dict = {
    "target_setting": {
        "name": "Net-Zero Target Setting", "weight": 0.20,
        "requirements": [
            {"id": "GFANZ-T-1", "desc": "1.5C alignment commitment (no/low overshoot)", "datapoints": ["net_zero_year", "overshoot_scenario", "paris_alignment"]},
            {"id": "GFANZ-T-2", "desc": "Scope 1/2/3 coverage in targets", "datapoints": ["scope_coverage", "scope3_target"]},
            {"id": "GFANZ-T-3", "desc": "5-year interim targets (2025/2030/2035/2040)", "datapoints": ["interim_target_2025", "interim_target_2030", "interim_target_2035", "interim_target_2040"]},
            {"id": "GFANZ-T-4", "desc": "Sector-specific intensity targets", "datapoints": ["sector_intensity_targets"]},
        ]
    },
    "transition_financing": {
        "name": "Transition Financing Framework", "weight": 0.15,
        "requirements": [
            {"id": "GFANZ-TF-1", "desc": "Climate solutions financing (green)", "datapoints": ["green_financing_eur", "green_revenue_pct"]},
            {"id": "GFANZ-TF-2", "desc": "Aligned financing (already low-carbon)", "datapoints": ["aligned_financing_eur"]},
            {"id": "GFANZ-TF-3", "desc": "Managed phaseout financing", "datapoints": ["phaseout_financing_eur", "phaseout_timeline"]},
            {"id": "GFANZ-TF-4", "desc": "Transition financing (high-emitting decarbonising)", "datapoints": ["transition_financing_eur"]},
        ]
    },
    "portfolio_alignment": {
        "name": "Portfolio Alignment Metrics", "weight": 0.15,
        "requirements": [
            {"id": "GFANZ-PA-1", "desc": "Implied Temperature Rise (ITR)", "datapoints": ["implied_temperature_rise"]},
            {"id": "GFANZ-PA-2", "desc": "PACTA sector alignment", "datapoints": ["pacta_alignment_score"]},
            {"id": "GFANZ-PA-3", "desc": "SBTi portfolio target coverage", "datapoints": ["sbti_portfolio_coverage_pct"]},
            {"id": "GFANZ-PA-4", "desc": "Financed emissions trajectory", "datapoints": ["financed_emissions_tco2e", "financed_emissions_trend"]},
        ]
    },
    "sector_expectations": {
        "name": "Sector-Specific Expectations", "weight": 0.10,
        "requirements": [
            {"id": "GFANZ-SE-1", "desc": "Power: coal phase-out by 2030 (OECD)/2040 (non-OECD)", "datapoints": ["coal_phaseout_date", "renewable_capacity_target"]},
            {"id": "GFANZ-SE-2", "desc": "Oil & Gas: no new unabated fossil fuel expansion", "datapoints": ["fossil_expansion_policy", "methane_reduction_target"]},
            {"id": "GFANZ-SE-3", "desc": "Steel/Cement: Paris-aligned intensity pathway", "datapoints": ["steel_intensity_tco2_per_t", "cement_intensity_tco2_per_t"]},
            {"id": "GFANZ-SE-4", "desc": "Transport: fleet electrification trajectory", "datapoints": ["ev_fleet_pct", "electrification_target"]},
            {"id": "GFANZ-SE-5", "desc": "Real Estate: CRREM pathway alignment", "datapoints": ["crrem_aligned_pct", "energy_intensity_kwh_m2"]},
        ]
    },
    "engagement": {
        "name": "Real-Economy Engagement", "weight": 0.10,
        "requirements": [
            {"id": "GFANZ-E-1", "desc": "Active stewardship with portfolio companies", "datapoints": ["stewardship_engagement_pct"]},
            {"id": "GFANZ-E-2", "desc": "Climate voting policy", "datapoints": ["climate_voting_policy", "votes_against_climate_laggards"]},
            {"id": "GFANZ-E-3", "desc": "Escalation policy (divestment timeline)", "datapoints": ["escalation_policy", "divestment_timeline_years"]},
        ]
    },
    "governance": {
        "name": "Governance and Accountability", "weight": 0.15,
        "requirements": [
            {"id": "GFANZ-G-1", "desc": "Board-level net-zero oversight", "datapoints": ["board_nz_oversight"]},
            {"id": "GFANZ-G-2", "desc": "Executive accountability and remuneration", "datapoints": ["exec_accountability", "exec_remuneration_linked"]},
            {"id": "GFANZ-G-3", "desc": "Robust MRV (Measurement, Reporting, Verification)", "datapoints": ["third_party_verification", "reporting_standard"]},
        ]
    },
    "reporting": {
        "name": "Annual Reporting", "weight": 0.15,
        "requirements": [
            {"id": "GFANZ-R-1", "desc": "Progress against targets (actual vs planned)", "datapoints": ["progress_vs_target_pct"]},
            {"id": "GFANZ-R-2", "desc": "Methodology changes and restatements", "datapoints": ["methodology_changes", "restatements"]},
            {"id": "GFANZ-R-3", "desc": "Use of carbon credits disclosure", "datapoints": ["credits_disclosed", "credits_volume_tco2"]},
            {"id": "GFANZ-R-4", "desc": "Sub-alliance specific reporting (NZBA/NZAOA/NZAMI/NZIA)", "datapoints": ["sub_alliance_membership", "sub_alliance_report_filed"]},
        ]
    },
    "sub_alliances": {
        "NZBA": {"name": "Net Zero Banking Alliance", "members_required": "Banks with >USD 1B assets", "commitments": "Scope 1/2/3 financed emissions targets, sector decarbonisation pathways, annual reporting"},
        "NZAOA": {"name": "Net Zero Asset Owners Alliance", "members_required": "Asset owners", "commitments": "Portfolio-level targets, engagement milestones, sector targets, sovereign bond approach"},
        "NZAMI": {"name": "Net Zero Asset Managers Initiative", "members_required": "Asset managers", "commitments": "AuM-level targets, stewardship strategy, client engagement, product development"},
        "NZIA": {"name": "Net Zero Insurance Alliance", "members_required": "Re/insurers", "commitments": "Underwriting portfolio targets, engagement with insureds, product innovation"},
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 3. IIGCC NET ZERO INVESTMENT FRAMEWORK v2.0
# ═══════════════════════════════════════════════════════════════════════════════

IIGCC_NZIF_STEPS: dict = {
    "step1": {
        "name": "Governance and Strategy", "weight": 0.15,
        "requirements": [
            {"id": "NZIF-1.1", "desc": "Net-zero investment policy adopted by board", "datapoints": ["nz_policy_adopted", "board_approval_date"]},
            {"id": "NZIF-1.2", "desc": "Dedicated climate resources and expertise", "datapoints": ["climate_team_fte", "climate_expertise_board"]},
            {"id": "NZIF-1.3", "desc": "Integration into investment beliefs and process", "datapoints": ["investment_beliefs_updated", "esg_integration_approach"]},
        ]
    },
    "step2": {
        "name": "Objectives and Targets", "weight": 0.20,
        "requirements": [
            {"id": "NZIF-2.1", "desc": "Portfolio reference targets: 50% by 2030 from 2019 base", "datapoints": ["portfolio_target_2030_pct", "base_year", "target_methodology"]},
            {"id": "NZIF-2.2", "desc": "Net-zero by 2050 commitment", "datapoints": ["net_zero_year"]},
            {"id": "NZIF-2.3", "desc": "Asset-level alignment criteria", "datapoints": ["aligned_pct", "aligning_pct", "committed_pct", "not_aligned_pct"]},
            {"id": "NZIF-2.4", "desc": "Engagement thresholds (2yr/5yr escalation)", "datapoints": ["engagement_threshold_2yr", "engagement_threshold_5yr", "escalation_actions"]},
        ]
    },
    "step3": {
        "name": "Strategic Asset Allocation", "weight": 0.10,
        "requirements": [
            {"id": "NZIF-3.1", "desc": "Climate-integrated SAA process", "datapoints": ["saa_climate_integrated"]},
            {"id": "NZIF-3.2", "desc": "Green/transition allocation targets", "datapoints": ["green_allocation_target_pct", "transition_allocation_pct"]},
        ]
    },
    "step4": {
        "name": "Asset Class Implementation", "weight": 0.20,
        "requirements": [
            {"id": "NZIF-4.1", "desc": "Listed equity: company alignment assessment", "datapoints": ["listed_equity_aligned_pct", "engagement_coverage_pct"]},
            {"id": "NZIF-4.2", "desc": "Corporate bonds: issuer alignment + stewardship", "datapoints": ["corp_bonds_aligned_pct"]},
            {"id": "NZIF-4.3", "desc": "Sovereign bonds: country-level climate alignment", "datapoints": ["sovereign_climate_aligned_pct"]},
            {"id": "NZIF-4.4", "desc": "Real estate: CRREM pathway + energy performance", "datapoints": ["re_crrem_aligned_pct", "re_energy_intensity"]},
            {"id": "NZIF-4.5", "desc": "Infrastructure: project-level assessment", "datapoints": ["infra_green_pct"]},
            {"id": "NZIF-4.6", "desc": "Private equity: portfolio company engagement", "datapoints": ["pe_engagement_coverage"]},
        ]
    },
    "step5": {
        "name": "Policy Advocacy", "weight": 0.10,
        "requirements": [
            {"id": "NZIF-5.1", "desc": "Investor policy advocacy framework", "datapoints": ["policy_advocacy_active"]},
            {"id": "NZIF-5.2", "desc": "Alignment of lobbying and trade associations", "datapoints": ["lobbying_alignment_review"]},
        ]
    },
    "step6": {
        "name": "Market-Wide Initiatives", "weight": 0.10,
        "requirements": [
            {"id": "NZIF-6.1", "desc": "Collaborative engagement participation", "datapoints": ["collab_engagement_count"]},
            {"id": "NZIF-6.2", "desc": "Industry standard development", "datapoints": ["standard_contributions"]},
        ]
    },
    "step7": {
        "name": "Monitoring, Reporting and Verification", "weight": 0.15,
        "requirements": [
            {"id": "NZIF-7.1", "desc": "Annual progress reporting", "datapoints": ["annual_report_published"]},
            {"id": "NZIF-7.2", "desc": "Third-party verification/assurance", "datapoints": ["third_party_assurance"]},
            {"id": "NZIF-7.3", "desc": "Target review and recalibration", "datapoints": ["target_review_frequency"]},
        ]
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 4. CSDDD ARTICLE 22 — Climate Transition Plan
# ═══════════════════════════════════════════════════════════════════════════════

CSDDD_REQUIREMENTS: dict = {
    "art22_1": {
        "ref": "Art 22(1)", "desc": "Adopt and put into effect a transition plan for climate change mitigation",
        "requirements": {
            "art22_1_a": {"ref": "Art 22(1)(a)", "desc": "Time-bound targets for 2030 and in five-year steps to 2050, aligned with Paris Agreement 1.5C",
                         "datapoints": ["net_zero_year", "interim_target_2030", "interim_targets_5yr_steps", "paris_alignment_1_5c"],
                         "mandatory": True},
            "art22_1_b": {"ref": "Art 22(1)(b)", "desc": "Scope 1, 2, and where appropriate Scope 3 GHG emissions coverage",
                         "datapoints": ["scope1_covered", "scope2_covered", "scope3_covered", "scope3_material_categories"],
                         "mandatory": True},
            "art22_1_c": {"ref": "Art 22(1)(c)", "desc": "Identification of decarbonisation levers available to the company",
                         "datapoints": ["decarbonisation_levers", "technology_roadmap", "energy_transition_plan"],
                         "mandatory": True},
            "art22_1_d": {"ref": "Art 22(1)(d)", "desc": "Description of key actions planned to reach targets",
                         "datapoints": ["key_actions", "action_timeline", "milestones", "responsible_persons"],
                         "mandatory": True},
            "art22_1_e": {"ref": "Art 22(1)(e)", "desc": "Explanation of investments and funding supporting implementation",
                         "datapoints": ["capex_plan_eur", "funding_sources", "green_bond_plan", "rd_budget_climate"],
                         "mandatory": True},
            "art22_1_f": {"ref": "Art 22(1)(f)", "desc": "Role of carbon credits (supplementary only, quality criteria)",
                         "datapoints": ["credits_role", "credits_volume_tco2", "credits_quality_standard", "residual_emissions_only"],
                         "mandatory": True},
            "art22_1_g": {"ref": "Art 22(1)(g)", "desc": "Board oversight and management roles in implementation",
                         "datapoints": ["board_oversight", "management_responsibility", "reporting_to_board_frequency"],
                         "mandatory": True},
        }
    },
    "art22_2": {
        "ref": "Art 22(2)", "desc": "Annual update obligation — report on progress, reasons for deviation, remedial actions",
        "datapoints": ["annual_update_published", "progress_vs_targets", "deviation_explanations", "remedial_actions"],
        "mandatory": True,
    },
    "art22_3": {
        "ref": "Art 22(3)", "desc": "Link to due diligence obligations (Articles 5-16)",
        "datapoints": ["dd_integration", "adverse_impact_linkage"],
        "mandatory": True,
    },
    "art22_4": {
        "ref": "Art 22(4)", "desc": "Plan considered satisfying CSRD ESRS E1 requirements if ESRS-compliant",
        "datapoints": ["esrs_e1_compliant", "csrd_reporting_entity"],
        "mandatory": False,
    },
    "phase_in": {
        "group_1": {"from": "2027-07-26", "companies": "EU >5000 employees AND >EUR 1.5B turnover"},
        "group_2": {"from": "2028-07-26", "companies": "EU >3000 employees AND >EUR 900M turnover"},
        "group_3": {"from": "2029-07-26", "companies": "EU >1000 employees AND >EUR 450M turnover; non-EU >EUR 450M EU turnover"},
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 5. CSRD ESRS E1 — Climate Change Disclosures
# ═══════════════════════════════════════════════════════════════════════════════

ESRS_E1_DISCLOSURES: dict = {
    "E1-1": {
        "name": "Transition plan for climate change mitigation", "paragraphs": "14-19",
        "datapoints": [
            {"id": "E1-1-01", "name": "Net-zero target year", "type": "quantitative", "unit": "year", "mandatory": True},
            {"id": "E1-1-02", "name": "GHG scope coverage (1/2/3)", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-1-03", "name": "Decarbonisation levers identified", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-1-04", "name": "Key actions and timeline", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-1-05", "name": "CapEx and OpEx aligned with transition plan", "type": "quantitative", "unit": "EUR", "mandatory": True},
            {"id": "E1-1-06", "name": "Locked-in GHG emissions from existing assets", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-1-07", "name": "Carbon credits role and quality", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-1-08", "name": "Governance of transition plan", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-1-09", "name": "Paris-aligned scenario reference", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-1-10", "name": "Stakeholder engagement in transition planning", "type": "qualitative", "unit": "text", "mandatory": False},
        ]
    },
    "E1-2": {
        "name": "Policies related to climate change mitigation and adaptation", "paragraphs": "20-24",
        "datapoints": [
            {"id": "E1-2-01", "name": "Climate mitigation policy description", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-2-02", "name": "Climate adaptation policy description", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-2-03", "name": "Policy scope and boundaries", "type": "qualitative", "unit": "text", "mandatory": True},
        ]
    },
    "E1-3": {
        "name": "Actions and resources related to climate change policies", "paragraphs": "25-33",
        "datapoints": [
            {"id": "E1-3-01", "name": "Key climate actions undertaken/planned", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-3-02", "name": "Resources allocated (financial/human)", "type": "quantitative", "unit": "EUR", "mandatory": True},
            {"id": "E1-3-03", "name": "Expected GHG reduction from actions", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
        ]
    },
    "E1-4": {
        "name": "Targets related to climate change mitigation and adaptation", "paragraphs": "34-40",
        "datapoints": [
            {"id": "E1-4-01", "name": "Absolute GHG reduction target", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-4-02", "name": "Intensity GHG reduction target", "type": "quantitative", "unit": "tCO2e/EUR M", "mandatory": True},
            {"id": "E1-4-03", "name": "Target base year and target year", "type": "quantitative", "unit": "year", "mandatory": True},
            {"id": "E1-4-04", "name": "Science-based target methodology", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-4-05", "name": "SBTi validation status", "type": "boolean", "unit": "yes/no", "mandatory": True},
            {"id": "E1-4-06", "name": "Interim milestones (5-year steps)", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
        ]
    },
    "E1-5": {
        "name": "Energy consumption and mix", "paragraphs": "41-47",
        "datapoints": [
            {"id": "E1-5-01", "name": "Total energy consumption", "type": "quantitative", "unit": "MWh", "mandatory": True},
            {"id": "E1-5-02", "name": "Renewable energy share", "type": "quantitative", "unit": "%", "mandatory": True},
            {"id": "E1-5-03", "name": "Non-renewable breakdown by source", "type": "quantitative", "unit": "MWh", "mandatory": True},
            {"id": "E1-5-04", "name": "Energy intensity per net revenue", "type": "quantitative", "unit": "MWh/EUR M", "mandatory": True},
            {"id": "E1-5-05", "name": "Fossil fuel-related activities energy consumption", "type": "quantitative", "unit": "MWh", "mandatory": True},
        ]
    },
    "E1-6": {
        "name": "Gross Scope 1, 2 and 3 GHG emissions", "paragraphs": "48-57",
        "datapoints": [
            {"id": "E1-6-01", "name": "Gross Scope 1 GHG emissions", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-6-02", "name": "Gross Scope 2 GHG emissions (location-based)", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-6-03", "name": "Gross Scope 2 GHG emissions (market-based)", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-6-04", "name": "Gross Scope 3 total", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-6-05", "name": "Scope 3 by category (15 categories)", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-6-06", "name": "Total GHG emissions (1+2+3)", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-6-07", "name": "GHG intensity per net revenue", "type": "quantitative", "unit": "tCO2e/EUR M", "mandatory": True},
        ]
    },
    "E1-7": {
        "name": "GHG removals and carbon credits", "paragraphs": "58-62",
        "datapoints": [
            {"id": "E1-7-01", "name": "GHG removals within own operations", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-7-02", "name": "Carbon credits purchased", "type": "quantitative", "unit": "tCO2e", "mandatory": True},
            {"id": "E1-7-03", "name": "Carbon credit certification scheme", "type": "qualitative", "unit": "text", "mandatory": True},
            {"id": "E1-7-04", "name": "Carbon credit vintage year", "type": "quantitative", "unit": "year", "mandatory": True},
            {"id": "E1-7-05", "name": "Carbon credit type (avoidance/removal)", "type": "qualitative", "unit": "text", "mandatory": True},
        ]
    },
    "E1-8": {
        "name": "Internal carbon pricing", "paragraphs": "63-66",
        "datapoints": [
            {"id": "E1-8-01", "name": "Internal carbon price scope", "type": "qualitative", "unit": "text", "mandatory": False},
            {"id": "E1-8-02", "name": "Internal carbon price per tCO2e", "type": "quantitative", "unit": "EUR/tCO2e", "mandatory": False},
            {"id": "E1-8-03", "name": "Carbon pricing type (shadow/fee/implicit)", "type": "qualitative", "unit": "text", "mandatory": False},
        ]
    },
    "E1-9": {
        "name": "Anticipated financial effects from physical risks", "paragraphs": "67-72",
        "datapoints": [
            {"id": "E1-9-01", "name": "Assets at material physical risk", "type": "quantitative", "unit": "EUR", "mandatory": True},
            {"id": "E1-9-02", "name": "Revenue at risk from physical impacts", "type": "quantitative", "unit": "%", "mandatory": True},
            {"id": "E1-9-03", "name": "Adaptation costs anticipated", "type": "quantitative", "unit": "EUR", "mandatory": True},
        ]
    },
    "E1-10": {
        "name": "Anticipated financial effects from transition risks and opportunities", "paragraphs": "73-78",
        "datapoints": [
            {"id": "E1-10-01", "name": "Assets at material transition risk", "type": "quantitative", "unit": "EUR", "mandatory": True},
            {"id": "E1-10-02", "name": "Stranded asset exposure", "type": "quantitative", "unit": "EUR", "mandatory": True},
            {"id": "E1-10-03", "name": "Green revenue opportunity", "type": "quantitative", "unit": "EUR", "mandatory": True},
        ]
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 6. CDP C4 — Targets and Performance + Transition Plan
# ═══════════════════════════════════════════════════════════════════════════════

CDP_C4_QUESTIONS: dict = {
    "C4.1": {
        "name": "Emissions reduction targets", "section": "C4 Targets and Performance",
        "sub_questions": {
            "C4.1a": {"desc": "Absolute target details", "datapoints": ["absolute_target_scope", "base_year", "base_year_emissions", "target_year", "target_reduction_pct", "target_status"]},
            "C4.1b": {"desc": "Intensity target details", "datapoints": ["intensity_metric", "intensity_base_year", "intensity_target_year", "intensity_reduction_pct", "denominator"]},
            "C4.1c": {"desc": "Net-zero target details", "datapoints": ["nz_target_year", "nz_scope_coverage", "nz_interim_targets", "nz_residual_emissions_approach"]},
        }
    },
    "C4.2": {
        "name": "Other climate-related targets", "section": "C4 Targets and Performance",
        "sub_questions": {
            "C4.2a": {"desc": "Target details (energy, waste, water)", "datapoints": ["target_type", "target_metric", "target_year", "target_value"]},
            "C4.2b": {"desc": "Plans to introduce targets", "datapoints": ["planned_target_type", "expected_timeline"]},
            "C4.2c": {"desc": "Net-zero target progress tracking", "datapoints": ["nz_progress_pct", "on_track_status"]},
        }
    },
    "C4.3": {
        "name": "Emissions reduction initiatives", "section": "C4 Targets and Performance",
        "sub_questions": {
            "C4.3a": {"desc": "Total emissions saved from initiatives", "datapoints": ["total_emissions_saved_tco2e"]},
            "C4.3b": {"desc": "Methodology for calculating reductions", "datapoints": ["calculation_methodology"]},
            "C4.3c": {"desc": "Details on each initiative", "datapoints": ["initiative_type", "scope", "voluntary_mandatory", "annual_savings_tco2e", "investment_eur", "payback_years"]},
            "C4.3d": {"desc": "Anticipated emissions trajectory", "datapoints": ["trajectory_2025", "trajectory_2030", "trajectory_2050"]},
        }
    },
    "C4.5": {
        "name": "Transition plan", "section": "C4 Targets and Performance",
        "sub_questions": {
            "C4.5a": {"desc": "Scenario(s) used for transition planning", "datapoints": ["scenarios_used", "scenario_alignment"]},
            "C4.5b": {"desc": "Transition plan elements", "datapoints": ["strategy_element", "governance_element", "metrics_element", "targets_element", "implementation_actions"]},
        }
    },
    "C1": {
        "name": "Governance (linked)", "section": "C1 Governance",
        "sub_questions": {
            "C1.1a": {"desc": "Board oversight of climate issues", "datapoints": ["board_oversight_type", "board_climate_competence"]},
            "C1.2": {"desc": "Management responsibility", "datapoints": ["highest_management_position", "climate_in_job_description"]},
            "C1.3": {"desc": "Incentives linked to climate", "datapoints": ["incentives_type", "incentives_pct_compensation"]},
        }
    },
    "C3": {
        "name": "Business Strategy (linked)", "section": "C3 Business Strategy",
        "sub_questions": {
            "C3.1": {"desc": "Business strategy influenced by climate", "datapoints": ["strategy_influenced"]},
            "C3.3": {"desc": "Scenario analysis conducted", "datapoints": ["scenarios_list", "time_horizons", "implications"]},
            "C3.4": {"desc": "Transition plan disclosure", "datapoints": ["transition_plan_published", "plan_aligned_to_1_5c"]},
        }
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 7. INTER-FRAMEWORK CROSS-MAPPING (55 Datapoints)
# ═══════════════════════════════════════════════════════════════════════════════

CROSS_FRAMEWORK_MAPPING: list[dict] = [
    # ── TARGET SETTING ─────────────────────────────────────────────────────
    {"metric_id": "CFM-001", "metric_name": "Net-zero target year",
     "tpt_ref": "TPT-F-1", "gfanz_ref": "GFANZ-T-1", "iigcc_ref": "NZIF-2.2", "csddd_ref": "Art 22(1)(a)", "esrs_e1_ref": "E1-1-01", "cdp_ref": "C4.1c",
     "data_type": "quantitative", "unit": "year", "description": "Year by which entity commits to net-zero GHG emissions"},
    {"metric_id": "CFM-002", "metric_name": "Interim target 2030 (absolute reduction %)",
     "tpt_ref": "TPT-F-1", "gfanz_ref": "GFANZ-T-3", "iigcc_ref": "NZIF-2.1", "csddd_ref": "Art 22(1)(a)", "esrs_e1_ref": "E1-4-01", "cdp_ref": "C4.1a",
     "data_type": "quantitative", "unit": "%", "description": "Percentage absolute GHG reduction target for 2030 from base year"},
    {"metric_id": "CFM-003", "metric_name": "Interim targets in 5-year steps to 2050",
     "tpt_ref": "TPT-F-1", "gfanz_ref": "GFANZ-T-3", "iigcc_ref": "NZIF-2.1", "csddd_ref": "Art 22(1)(a)", "esrs_e1_ref": "E1-4-06", "cdp_ref": "C4.1a",
     "data_type": "quantitative", "unit": "%", "description": "Interim reduction milestones every 5 years (2025/2030/2035/2040/2045)"},
    {"metric_id": "CFM-004", "metric_name": "Paris Agreement 1.5C alignment",
     "tpt_ref": "TPT-F-1", "gfanz_ref": "GFANZ-T-1", "iigcc_ref": "NZIF-2.2", "csddd_ref": "Art 22(1)(a)", "esrs_e1_ref": "E1-1-09", "cdp_ref": "C4.5a",
     "data_type": "boolean", "unit": "yes/no", "description": "Whether transition plan is aligned with 1.5C no/low overshoot pathway"},
    {"metric_id": "CFM-005", "metric_name": "SBTi validation status",
     "tpt_ref": "TPT-MT-3", "gfanz_ref": "GFANZ-PA-3", "iigcc_ref": "NZIF-2.1", "csddd_ref": "N/A", "esrs_e1_ref": "E1-4-05", "cdp_ref": "C4.1a",
     "data_type": "boolean", "unit": "yes/no", "description": "Whether targets are validated by the Science Based Targets initiative"},
    {"metric_id": "CFM-006", "metric_name": "Intensity GHG reduction target",
     "tpt_ref": "TPT-MT-3", "gfanz_ref": "GFANZ-T-4", "iigcc_ref": "NZIF-2.1", "csddd_ref": "Art 22(1)(a)", "esrs_e1_ref": "E1-4-02", "cdp_ref": "C4.1b",
     "data_type": "quantitative", "unit": "tCO2e/unit", "description": "GHG intensity reduction target (per revenue, output, etc.)"},
    {"metric_id": "CFM-007", "metric_name": "Target base year",
     "tpt_ref": "TPT-MT-3", "gfanz_ref": "GFANZ-T-3", "iigcc_ref": "NZIF-2.1", "csddd_ref": "Art 22(1)(a)", "esrs_e1_ref": "E1-4-03", "cdp_ref": "C4.1a",
     "data_type": "quantitative", "unit": "year", "description": "Base year from which emission reductions are measured"},

    # ── GHG EMISSIONS ──────────────────────────────────────────────────────
    {"metric_id": "CFM-008", "metric_name": "Scope 1 GHG emissions",
     "tpt_ref": "TPT-MT-1", "gfanz_ref": "GFANZ-R-1", "iigcc_ref": "NZIF-7.1", "csddd_ref": "Art 22(1)(b)", "esrs_e1_ref": "E1-6-01", "cdp_ref": "C6.1",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Direct GHG emissions from owned/controlled sources"},
    {"metric_id": "CFM-009", "metric_name": "Scope 2 GHG emissions (location-based)",
     "tpt_ref": "TPT-MT-1", "gfanz_ref": "GFANZ-R-1", "iigcc_ref": "NZIF-7.1", "csddd_ref": "Art 22(1)(b)", "esrs_e1_ref": "E1-6-02", "cdp_ref": "C6.3",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Indirect GHG emissions from purchased energy (location-based)"},
    {"metric_id": "CFM-010", "metric_name": "Scope 2 GHG emissions (market-based)",
     "tpt_ref": "TPT-MT-1", "gfanz_ref": "GFANZ-R-1", "iigcc_ref": "NZIF-7.1", "csddd_ref": "Art 22(1)(b)", "esrs_e1_ref": "E1-6-03", "cdp_ref": "C6.3",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Indirect GHG emissions from purchased energy (market-based)"},
    {"metric_id": "CFM-011", "metric_name": "Scope 3 total GHG emissions",
     "tpt_ref": "TPT-MT-1", "gfanz_ref": "GFANZ-R-1", "iigcc_ref": "NZIF-7.1", "csddd_ref": "Art 22(1)(b)", "esrs_e1_ref": "E1-6-04", "cdp_ref": "C6.5",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Value chain GHG emissions (all 15 categories combined)"},
    {"metric_id": "CFM-012", "metric_name": "Scope 3 emissions by category (15 categories)",
     "tpt_ref": "TPT-MT-1", "gfanz_ref": "GFANZ-R-1", "iigcc_ref": "NZIF-7.1", "csddd_ref": "Art 22(1)(b)", "esrs_e1_ref": "E1-6-05", "cdp_ref": "C6.5",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Scope 3 broken down by GHG Protocol categories 1-15"},
    {"metric_id": "CFM-013", "metric_name": "GHG intensity per revenue",
     "tpt_ref": "TPT-MT-1", "gfanz_ref": "GFANZ-T-4", "iigcc_ref": "NZIF-7.1", "csddd_ref": "N/A", "esrs_e1_ref": "E1-6-07", "cdp_ref": "C6.10",
     "data_type": "quantitative", "unit": "tCO2e/EUR M", "description": "Total GHG emissions normalised by net revenue"},
    {"metric_id": "CFM-014", "metric_name": "GHG verification/assurance status",
     "tpt_ref": "TPT-MT-1", "gfanz_ref": "GFANZ-G-3", "iigcc_ref": "NZIF-7.2", "csddd_ref": "N/A", "esrs_e1_ref": "E1-6-01 (para 56)", "cdp_ref": "C10.1",
     "data_type": "qualitative", "unit": "text", "description": "Whether GHG data is third-party verified (limited/reasonable assurance)"},

    # ── ENERGY METRICS ─────────────────────────────────────────────────────
    {"metric_id": "CFM-015", "metric_name": "Total energy consumption",
     "tpt_ref": "TPT-MT-2", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-5-01", "cdp_ref": "C8.2a",
     "data_type": "quantitative", "unit": "MWh", "description": "Total energy consumed from all sources"},
    {"metric_id": "CFM-016", "metric_name": "Renewable energy share",
     "tpt_ref": "TPT-MT-2", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-5-02", "cdp_ref": "C8.2a",
     "data_type": "quantitative", "unit": "%", "description": "Percentage of total energy from renewable sources"},
    {"metric_id": "CFM-017", "metric_name": "Energy intensity per revenue",
     "tpt_ref": "TPT-MT-2", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-5-04", "cdp_ref": "C8.2a",
     "data_type": "quantitative", "unit": "MWh/EUR M", "description": "Energy consumed normalised by net revenue"},

    # ── FINANCIAL PLANNING ─────────────────────────────────────────────────
    {"metric_id": "CFM-018", "metric_name": "CapEx aligned with transition plan",
     "tpt_ref": "TPT-IS-4", "gfanz_ref": "GFANZ-TF-1", "iigcc_ref": "NZIF-3.2", "csddd_ref": "Art 22(1)(e)", "esrs_e1_ref": "E1-1-05", "cdp_ref": "C4.3c",
     "data_type": "quantitative", "unit": "EUR", "description": "Capital expenditure allocated to climate transition activities"},
    {"metric_id": "CFM-019", "metric_name": "CapEx aligned percentage",
     "tpt_ref": "TPT-IS-4", "gfanz_ref": "GFANZ-TF-1", "iigcc_ref": "NZIF-3.2", "csddd_ref": "Art 22(1)(e)", "esrs_e1_ref": "E1-1-05", "cdp_ref": "N/A",
     "data_type": "quantitative", "unit": "%", "description": "Percentage of total CapEx aligned with EU Taxonomy/transition"},
    {"metric_id": "CFM-020", "metric_name": "Green revenue / climate solutions revenue",
     "tpt_ref": "TPT-IS-2", "gfanz_ref": "GFANZ-TF-1", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-10-03", "cdp_ref": "C4.5b",
     "data_type": "quantitative", "unit": "EUR", "description": "Revenue from products/services that contribute to climate mitigation"},
    {"metric_id": "CFM-021", "metric_name": "Internal carbon price",
     "tpt_ref": "TPT-IS-3", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-8-02", "cdp_ref": "C11.3a",
     "data_type": "quantitative", "unit": "EUR/tCO2e", "description": "Shadow or internal fee price applied to carbon emissions"},
    {"metric_id": "CFM-022", "metric_name": "R&D investment in climate solutions",
     "tpt_ref": "TPT-IS-4", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(e)", "esrs_e1_ref": "E1-3-02", "cdp_ref": "C4.3c",
     "data_type": "quantitative", "unit": "EUR", "description": "Research and development spend on climate technologies"},

    # ── CARBON CREDITS ─────────────────────────────────────────────────────
    {"metric_id": "CFM-023", "metric_name": "Carbon credits volume purchased",
     "tpt_ref": "TPT-MT-4", "gfanz_ref": "GFANZ-R-3", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(f)", "esrs_e1_ref": "E1-7-02", "cdp_ref": "C11.2a",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Total volume of carbon credits purchased in reporting period"},
    {"metric_id": "CFM-024", "metric_name": "Carbon credit quality standard/certification",
     "tpt_ref": "TPT-MT-4", "gfanz_ref": "GFANZ-R-3", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(f)", "esrs_e1_ref": "E1-7-03", "cdp_ref": "C11.2a",
     "data_type": "qualitative", "unit": "text", "description": "Certification standard (ICVCM CCP, Verra VCS, Gold Standard, CDM, Article 6.4)"},
    {"metric_id": "CFM-025", "metric_name": "Carbon credit type (avoidance/removal)",
     "tpt_ref": "TPT-MT-4", "gfanz_ref": "GFANZ-R-3", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(f)", "esrs_e1_ref": "E1-7-05", "cdp_ref": "C11.2a",
     "data_type": "qualitative", "unit": "text", "description": "Whether credits are avoidance-based or removal-based"},
    {"metric_id": "CFM-026", "metric_name": "Credits limited to residual emissions",
     "tpt_ref": "TPT-MT-4", "gfanz_ref": "GFANZ-R-3", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(f)", "esrs_e1_ref": "E1-7-01", "cdp_ref": "C11.2a",
     "data_type": "boolean", "unit": "yes/no", "description": "Whether carbon credits are used only for hard-to-abate residual emissions"},

    # ── GOVERNANCE ─────────────────────────────────────────────────────────
    {"metric_id": "CFM-027", "metric_name": "Board climate oversight",
     "tpt_ref": "TPT-G-1", "gfanz_ref": "GFANZ-G-1", "iigcc_ref": "NZIF-1.1", "csddd_ref": "Art 22(1)(g)", "esrs_e1_ref": "E1-1-08", "cdp_ref": "C1.1a",
     "data_type": "qualitative", "unit": "text", "description": "Board-level oversight of climate strategy and transition plan"},
    {"metric_id": "CFM-028", "metric_name": "Board climate competence",
     "tpt_ref": "TPT-G-1", "gfanz_ref": "N/A", "iigcc_ref": "NZIF-1.2", "csddd_ref": "N/A", "esrs_e1_ref": "E1-1-08", "cdp_ref": "C1.1a",
     "data_type": "qualitative", "unit": "text", "description": "Climate expertise among board members (training, qualifications)"},
    {"metric_id": "CFM-029", "metric_name": "Management climate responsibility",
     "tpt_ref": "TPT-G-2", "gfanz_ref": "GFANZ-G-2", "iigcc_ref": "NZIF-1.2", "csddd_ref": "Art 22(1)(g)", "esrs_e1_ref": "E1-1-08", "cdp_ref": "C1.2",
     "data_type": "qualitative", "unit": "text", "description": "C-suite/senior management climate roles and accountability"},
    {"metric_id": "CFM-030", "metric_name": "Executive remuneration linked to climate KPIs",
     "tpt_ref": "TPT-G-3", "gfanz_ref": "GFANZ-G-2", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "ESRS 2 GOV-3", "cdp_ref": "C1.3",
     "data_type": "boolean", "unit": "yes/no", "description": "Whether executive compensation is linked to climate targets"},
    {"metric_id": "CFM-031", "metric_name": "Climate remuneration percentage",
     "tpt_ref": "TPT-G-3", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "ESRS 2 GOV-3", "cdp_ref": "C1.3",
     "data_type": "quantitative", "unit": "%", "description": "Percentage of variable compensation linked to climate metrics"},

    # ── DECARBONISATION LEVERS & IMPLEMENTATION ────────────────────────────
    {"metric_id": "CFM-032", "metric_name": "Decarbonisation levers identified",
     "tpt_ref": "TPT-IS-1", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(c)", "esrs_e1_ref": "E1-1-03", "cdp_ref": "C4.3c",
     "data_type": "qualitative", "unit": "text", "description": "Specific technical and operational levers for emission reduction"},
    {"metric_id": "CFM-033", "metric_name": "Key actions planned with timeline",
     "tpt_ref": "TPT-IS-1", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(d)", "esrs_e1_ref": "E1-1-04", "cdp_ref": "C4.3c",
     "data_type": "qualitative", "unit": "text", "description": "Description of actions with implementation milestones and deadlines"},
    {"metric_id": "CFM-034", "metric_name": "Expected GHG reduction from actions",
     "tpt_ref": "TPT-IS-1", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-3-03", "cdp_ref": "C4.3a",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Estimated annual emission reduction from planned initiatives"},
    {"metric_id": "CFM-035", "metric_name": "Locked-in GHG emissions from existing assets",
     "tpt_ref": "TPT-F-2", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-1-06", "cdp_ref": "N/A",
     "data_type": "quantitative", "unit": "tCO2e", "description": "Committed future emissions from long-lived assets (stranded asset risk)"},

    # ── ENGAGEMENT ─────────────────────────────────────────────────────────
    {"metric_id": "CFM-036", "metric_name": "Supplier engagement on emissions",
     "tpt_ref": "TPT-ES-1", "gfanz_ref": "GFANZ-E-1", "iigcc_ref": "NZIF-4.1", "csddd_ref": "Art 22(1)(c)", "esrs_e1_ref": "E1-3-01", "cdp_ref": "C12.1a",
     "data_type": "quantitative", "unit": "%", "description": "Percentage of suppliers (by spend/emissions) engaged on decarbonisation"},
    {"metric_id": "CFM-037", "metric_name": "Scope 3 supplier reduction target",
     "tpt_ref": "TPT-ES-1", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(b)", "esrs_e1_ref": "E1-4-01", "cdp_ref": "C4.1a",
     "data_type": "quantitative", "unit": "%", "description": "Target for Scope 3 upstream supplier emission reductions"},
    {"metric_id": "CFM-038", "metric_name": "Industry initiative participation",
     "tpt_ref": "TPT-ES-2", "gfanz_ref": "GFANZ-E-3", "iigcc_ref": "NZIF-6.1", "csddd_ref": "N/A", "esrs_e1_ref": "N/A", "cdp_ref": "C12.3",
     "data_type": "qualitative", "unit": "text", "description": "Membership in sector decarbonisation initiatives (RE100, EV100, SBTi, etc.)"},
    {"metric_id": "CFM-039", "metric_name": "Policy advocacy alignment with net-zero",
     "tpt_ref": "TPT-ES-3", "gfanz_ref": "N/A", "iigcc_ref": "NZIF-5.1", "csddd_ref": "N/A", "esrs_e1_ref": "N/A", "cdp_ref": "C12.3",
     "data_type": "qualitative", "unit": "text", "description": "Whether lobbying and trade association positions align with 1.5C policy"},

    # ── PROGRESS TRACKING ──────────────────────────────────────────────────
    {"metric_id": "CFM-040", "metric_name": "Annual progress vs targets",
     "tpt_ref": "TPT-MT-3", "gfanz_ref": "GFANZ-R-1", "iigcc_ref": "NZIF-7.1", "csddd_ref": "Art 22(2)", "esrs_e1_ref": "E1-4-01", "cdp_ref": "C4.2c",
     "data_type": "quantitative", "unit": "%", "description": "Actual emission reduction achieved vs planned trajectory"},
    {"metric_id": "CFM-041", "metric_name": "Methodology changes and restatements",
     "tpt_ref": "N/A", "gfanz_ref": "GFANZ-R-2", "iigcc_ref": "NZIF-7.3", "csddd_ref": "Art 22(2)", "esrs_e1_ref": "E1-6 (para 56)", "cdp_ref": "C5.1",
     "data_type": "qualitative", "unit": "text", "description": "Disclosure of any methodology or base year recalculation changes"},
    {"metric_id": "CFM-042", "metric_name": "Annual update publication",
     "tpt_ref": "N/A", "gfanz_ref": "GFANZ-R-1", "iigcc_ref": "NZIF-7.1", "csddd_ref": "Art 22(2)", "esrs_e1_ref": "E1-1 (annual)", "cdp_ref": "C0.1",
     "data_type": "boolean", "unit": "yes/no", "description": "Whether annual transition plan progress update has been published"},

    # ── RISK & SCENARIO ANALYSIS ───────────────────────────────────────────
    {"metric_id": "CFM-043", "metric_name": "Climate scenario analysis conducted",
     "tpt_ref": "TPT-F-3", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-1-09", "cdp_ref": "C3.3",
     "data_type": "boolean", "unit": "yes/no", "description": "Whether quantitative climate scenario analysis has been performed"},
    {"metric_id": "CFM-044", "metric_name": "Assets at material physical risk",
     "tpt_ref": "TPT-F-3", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-9-01", "cdp_ref": "C2.3a",
     "data_type": "quantitative", "unit": "EUR", "description": "Value of assets exposed to material physical climate risks"},
    {"metric_id": "CFM-045", "metric_name": "Assets at material transition risk",
     "tpt_ref": "TPT-F-3", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-10-01", "cdp_ref": "C2.4a",
     "data_type": "quantitative", "unit": "EUR", "description": "Value of assets exposed to material transition risks"},
    {"metric_id": "CFM-046", "metric_name": "Stranded asset exposure",
     "tpt_ref": "TPT-F-2", "gfanz_ref": "GFANZ-TF-3", "iigcc_ref": "N/A", "csddd_ref": "N/A", "esrs_e1_ref": "E1-10-02", "cdp_ref": "C2.4a",
     "data_type": "quantitative", "unit": "EUR", "description": "Book value of assets at risk of stranding under transition scenarios"},

    # ── SECTOR-SPECIFIC ────────────────────────────────────────────────────
    {"metric_id": "CFM-047", "metric_name": "Coal phase-out date (power sector)",
     "tpt_ref": "TPT-IS-2", "gfanz_ref": "GFANZ-SE-1", "iigcc_ref": "NZIF-4.1", "csddd_ref": "Art 22(1)(d)", "esrs_e1_ref": "E1-1-04", "cdp_ref": "C4.3c",
     "data_type": "quantitative", "unit": "year", "description": "Committed date for full coal phase-out (OECD 2030/non-OECD 2040)"},
    {"metric_id": "CFM-048", "metric_name": "Fleet electrification percentage",
     "tpt_ref": "TPT-IS-1", "gfanz_ref": "GFANZ-SE-4", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(c)", "esrs_e1_ref": "E1-3-01", "cdp_ref": "C4.3c",
     "data_type": "quantitative", "unit": "%", "description": "Share of fleet vehicles that are electric/zero-emission"},
    {"metric_id": "CFM-049", "metric_name": "Building energy intensity (real estate)",
     "tpt_ref": "TPT-IS-1", "gfanz_ref": "GFANZ-SE-5", "iigcc_ref": "NZIF-4.4", "csddd_ref": "N/A", "esrs_e1_ref": "E1-5-04", "cdp_ref": "C8.2a",
     "data_type": "quantitative", "unit": "kWh/m2/yr", "description": "Average energy intensity of managed real estate portfolio"},
    {"metric_id": "CFM-050", "metric_name": "CRREM pathway alignment (real estate)",
     "tpt_ref": "TPT-IS-2", "gfanz_ref": "GFANZ-SE-5", "iigcc_ref": "NZIF-4.4", "csddd_ref": "N/A", "esrs_e1_ref": "N/A", "cdp_ref": "N/A",
     "data_type": "quantitative", "unit": "%", "description": "Percentage of portfolio aligned with CRREM 1.5C decarbonisation pathway"},

    # ── ADDITIONAL CROSS-CUTTING ───────────────────────────────────────────
    {"metric_id": "CFM-051", "metric_name": "Implied Temperature Rise (ITR)",
     "tpt_ref": "TPT-MT-2", "gfanz_ref": "GFANZ-PA-1", "iigcc_ref": "NZIF-2.3", "csddd_ref": "N/A", "esrs_e1_ref": "N/A", "cdp_ref": "C4.2c",
     "data_type": "quantitative", "unit": "degrees C", "description": "Portfolio-level implied temperature rise metric"},
    {"metric_id": "CFM-052", "metric_name": "Taxonomy-aligned CapEx percentage",
     "tpt_ref": "TPT-MT-2", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "Art 22(1)(e)", "esrs_e1_ref": "E1-1-05", "cdp_ref": "N/A",
     "data_type": "quantitative", "unit": "%", "description": "EU Taxonomy-aligned share of capital expenditure"},
    {"metric_id": "CFM-053", "metric_name": "Stakeholder engagement in transition planning",
     "tpt_ref": "TPT-ES-1", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "Art 22(3)", "esrs_e1_ref": "E1-1-10", "cdp_ref": "C12.1",
     "data_type": "qualitative", "unit": "text", "description": "Description of how stakeholders were engaged in developing transition plan"},
    {"metric_id": "CFM-054", "metric_name": "Just transition considerations",
     "tpt_ref": "TPT-ES-3", "gfanz_ref": "N/A", "iigcc_ref": "N/A", "csddd_ref": "Art 22(3) via Art 6", "esrs_e1_ref": "ESRS S1 (workforce)", "cdp_ref": "C4.5b",
     "data_type": "qualitative", "unit": "text", "description": "How transition plan addresses workforce and community impacts"},
    {"metric_id": "CFM-055", "metric_name": "Third-party reporting standard used",
     "tpt_ref": "N/A", "gfanz_ref": "GFANZ-G-3", "iigcc_ref": "NZIF-7.2", "csddd_ref": "N/A", "esrs_e1_ref": "E1-6 (para 56)", "cdp_ref": "C10.1",
     "data_type": "qualitative", "unit": "text", "description": "Reporting standard/framework (GHG Protocol, ISO 14064, ISAE 3410)"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 8. SCORING RUBRICS & SECTOR PATHWAYS
# ═══════════════════════════════════════════════════════════════════════════════

SCORING_RUBRICS: dict = {
    "target_credibility": {"weight": 0.25, "criteria": {"sbti_validated": 30, "paris_1_5c": 25, "scope_1_2_3": 20, "interim_milestones": 15, "base_year_recent": 10}},
    "implementation_maturity": {"weight": 0.25, "criteria": {"actions_underway": 25, "capex_allocated": 25, "milestones_met": 20, "technology_deployed": 15, "rd_investment": 15}},
    "governance_strength": {"weight": 0.20, "criteria": {"board_oversight": 25, "exec_accountability": 25, "remuneration_linked": 25, "skills_training": 15, "reporting_frequency": 10}},
    "financial_commitment": {"weight": 0.15, "criteria": {"capex_aligned_pct": 30, "green_revenue_pct": 25, "rd_climate_pct": 20, "carbon_price_applied": 15, "funding_secured": 10}},
    "transparency_quality": {"weight": 0.15, "criteria": {"quantitative_disclosure": 30, "third_party_verification": 25, "cross_framework_coverage": 20, "annual_update": 15, "stakeholder_engagement": 10}},
}

SECTOR_PATHWAYS: dict = {
    "power": {"source": "IEA NZE 2023", "unit": "gCO2/kWh", "2020": 442, "2025": 340, "2030": 138, "2035": 27, "2040": -10, "2050": -40},
    "steel": {"source": "SBTi Iron & Steel", "unit": "tCO2/t steel", "2020": 1.89, "2025": 1.62, "2030": 1.24, "2035": 0.89, "2040": 0.58, "2050": 0.05},
    "cement": {"source": "TPI Cement", "unit": "tCO2/t cementitious", "2020": 0.60, "2025": 0.55, "2030": 0.47, "2035": 0.37, "2040": 0.27, "2050": 0.06},
    "oil_gas": {"source": "IEA NZE 2023", "unit": "MtCO2 (scope 1+2)", "2020": 5200, "2025": 4700, "2030": 3600, "2035": 2500, "2040": 1500, "2050": 200},
    "aviation": {"source": "IEA NZE 2023", "unit": "gCO2/RPK", "2020": 96, "2025": 88, "2030": 67, "2035": 45, "2040": 25, "2050": 3},
    "shipping": {"source": "IMO GHG Strategy", "unit": "gCO2/t-nm", "2020": 11.0, "2025": 10.0, "2030": 7.7, "2035": 5.5, "2040": 3.3, "2050": 0.0},
    "real_estate": {"source": "CRREM", "unit": "kgCO2/m2/yr", "2020": 40, "2025": 32, "2030": 22, "2035": 14, "2040": 7, "2050": 0},
    "automotive": {"source": "IEA NZE 2023", "unit": "gCO2/km (fleet avg)", "2020": 120, "2025": 95, "2030": 60, "2035": 30, "2040": 10, "2050": 0},
}

TARGET_VALIDATION_CRITERIA: dict = {
    "sbti_near_term": {"horizon": "5-10 years", "ambition": "1.5C or well-below 2C", "scope": "Scope 1+2 mandatory, Scope 3 if >40%", "base_year": "No older than 2 years from submission"},
    "sbti_long_term": {"horizon": "By 2050 or sooner", "ambition": "1.5C no/low overshoot", "scope": "Scope 1+2+3", "residual": "<= 10% of base year", "neutralisation": "Required for residual"},
    "paris_1_5c": {"carbon_budget": "400-500 GtCO2 from 2020", "reduction_by_2030": "~43% from 2019", "reduction_by_2050": "~84% from 2019", "net_zero_by": 2050},
    "well_below_2c": {"carbon_budget": "900-1150 GtCO2 from 2020", "reduction_by_2030": "~27% from 2019", "reduction_by_2050": "~63% from 2019", "net_zero_by": 2070},
}

CARBON_CREDIT_QUALITY: dict = {
    "icvcm_ccp": {"name": "Integrity Council Core Carbon Principles", "requirements": ["Additionality", "Permanence", "Robust quantification", "No double counting", "Sustainable development", "Transition towards net-zero"]},
    "article_6_4": {"name": "Paris Agreement Article 6.4 Mechanism", "requirements": ["Corresponding adjustment", "Share of proceeds for adaptation", "Net global emission reduction", "Centralised crediting"]},
    "vintage_limit": {"recommendation": "Credits no older than 5 years", "removal_preference": "Removal credits preferred over avoidance for net-zero claims"},
    "usage_hierarchy": {"1": "Reduce own emissions first (mitigation hierarchy)", "2": "Use credits for residual/hard-to-abate only", "3": "No substitution for absolute reduction targets"},
}

REGULATORY_TIMELINE: dict = {
    "csddd": {"directive": "2024/1760", "group_1": "2027-07-26", "group_2": "2028-07-26", "group_3": "2029-07-26"},
    "csrd": {"directive": "2022/2464", "wave_1": "FY2024 (large PIEs >500 employees)", "wave_2": "FY2025 (large companies)", "wave_3": "FY2026 (listed SMEs, opt-out to FY2028)"},
    "cdp": {"2024_cycle": "Apr-Jul 2024 questionnaire window", "2025_cycle": "Aligned with ISSB S2 from 2025"},
    "sfdr": {"level_2_rts": "2023-01-01 (entity + product)", "taxonomy_alignment": "2024-01-01 (full alignment KPIs)"},
    "eu_taxonomy": {"climate_da": "2022-01-01", "complementary_da": "2023-01-01", "environmental_da": "2024-01-01", "climate_amendments": "2024-01-01"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# 9. DATACLASS RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TransitionPlanAssessment:
    entity_name: str = ""
    sector: str = ""
    reporting_year: int = 2025
    overall_score: float = 0.0
    overall_rating: str = "No Plan"
    tpt_assessment: dict = field(default_factory=dict)
    gfanz_assessment: dict = field(default_factory=dict)
    iigcc_assessment: dict = field(default_factory=dict)
    csddd_compliance: dict = field(default_factory=dict)
    esrs_e1_coverage: dict = field(default_factory=dict)
    cdp_c4_alignment: dict = field(default_factory=dict)
    target_credibility_score: float = 0.0
    implementation_maturity_score: float = 0.0
    governance_strength_score: float = 0.0
    financial_commitment_score: float = 0.0
    cross_framework_completeness: dict = field(default_factory=dict)
    inter_framework_gaps: list = field(default_factory=list)
    improvement_roadmap: list = field(default_factory=list)
    regulatory_readiness: dict = field(default_factory=dict)


@dataclass
class TargetAssessment:
    target_type: str = "absolute"
    target_year: int = 2050
    base_year: int = 2019
    interim_years: list = field(default_factory=list)
    scope_coverage: list = field(default_factory=list)
    reduction_pct: float = 0.0
    science_based: bool = False
    sbti_validated: bool = False
    paris_aligned: bool = False
    methodology: str = ""
    credibility_score: float = 0.0
    gap_to_pathway: float = 0.0


@dataclass
class SectorPathwayAssessment:
    sector: str = ""
    pathway_source: str = ""
    current_intensity: float = 0.0
    target_intensity: float = 0.0
    pathway_intensity_for_year: float = 0.0
    aligned: bool = False
    gap_pct: float = 0.0
    peer_comparison: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class TransitionPlanEngine:
    """
    Climate Transition Plan Assessment Engine
    ===========================================
    Exhaustive assessment against TPT, GFANZ, IIGCC NZIF, CSDDD Art 22,
    CSRD ESRS E1, and CDP C4 with 55-datapoint inter-framework cross-mapping.
    """

    def assess_transition_plan(
        self,
        entity_name: str,
        sector: str,
        reporting_year: int,
        plan_data: dict,
    ) -> TransitionPlanAssessment:
        """Assess transition plan against all 6 frameworks."""
        result = TransitionPlanAssessment(entity_name=entity_name, sector=sector, reporting_year=reporting_year)

        # Assess each framework
        result.tpt_assessment = self._assess_tpt(plan_data)
        result.gfanz_assessment = self._assess_gfanz(plan_data)
        result.iigcc_assessment = self._assess_iigcc(plan_data)
        result.csddd_compliance = self._assess_csddd(plan_data)
        result.esrs_e1_coverage = self._assess_esrs_e1(plan_data)
        result.cdp_c4_alignment = self._assess_cdp_c4(plan_data)

        # Dimension scores
        result.target_credibility_score = self._score_dimension("target_credibility", plan_data)
        result.implementation_maturity_score = self._score_dimension("implementation_maturity", plan_data)
        result.governance_strength_score = self._score_dimension("governance_strength", plan_data)
        result.financial_commitment_score = self._score_dimension("financial_commitment", plan_data)

        # Overall score (weighted)
        fw_scores = [
            self._avg_score(result.tpt_assessment) * 0.20,
            self._avg_score(result.gfanz_assessment) * 0.15,
            self._avg_score(result.iigcc_assessment) * 0.15,
            self._avg_score(result.csddd_compliance) * 0.20,
            self._avg_score(result.esrs_e1_coverage) * 0.15,
            self._avg_score(result.cdp_c4_alignment) * 0.15,
        ]
        result.overall_score = round(sum(fw_scores), 1)

        # Rating
        if result.overall_score >= 80:
            result.overall_rating = "Leading"
        elif result.overall_score >= 60:
            result.overall_rating = "Advanced"
        elif result.overall_score >= 40:
            result.overall_rating = "Developing"
        elif result.overall_score >= 20:
            result.overall_rating = "Nascent"
        else:
            result.overall_rating = "No Plan"

        # Cross-framework completeness
        result.cross_framework_completeness = self._calc_completeness(plan_data)
        result.inter_framework_gaps = self._identify_gaps(plan_data)
        result.improvement_roadmap = self._build_roadmap(result)
        result.regulatory_readiness = self._assess_regulatory_readiness(result)

        return result

    def _assess_tpt(self, plan_data: dict) -> dict:
        results = {}
        for elem_id, elem in TPT_FRAMEWORK.items():
            for sub_id, sub in elem["sub_elements"].items():
                dps = sub["datapoints"]
                provided = sum(1 for dp in dps if plan_data.get(dp) is not None)
                score = round((provided / max(len(dps), 1)) * 100, 1)
                results[sub_id] = {"name": sub["name"], "score": score, "provided": provided, "total": len(dps),
                                   "gaps": [dp for dp in dps if plan_data.get(dp) is None]}
        return results

    def _assess_gfanz(self, plan_data: dict) -> dict:
        results = {}
        for comp_id, comp in GFANZ_COMPONENTS.items():
            if comp_id == "sub_alliances":
                continue
            total_dps = 0
            provided_dps = 0
            for req in comp["requirements"]:
                for dp in req["datapoints"]:
                    total_dps += 1
                    if plan_data.get(dp) is not None:
                        provided_dps += 1
            score = round((provided_dps / max(total_dps, 1)) * 100, 1)
            results[comp_id] = {"name": comp["name"], "score": score, "provided": provided_dps, "total": total_dps}
        return results

    def _assess_iigcc(self, plan_data: dict) -> dict:
        results = {}
        for step_id, step in IIGCC_NZIF_STEPS.items():
            total_dps = 0
            provided_dps = 0
            for req in step["requirements"]:
                for dp in req["datapoints"]:
                    total_dps += 1
                    if plan_data.get(dp) is not None:
                        provided_dps += 1
            score = round((provided_dps / max(total_dps, 1)) * 100, 1)
            results[step_id] = {"name": step["name"], "score": score, "provided": provided_dps, "total": total_dps}
        return results

    def _assess_csddd(self, plan_data: dict) -> dict:
        results = {}
        reqs = CSDDD_REQUIREMENTS["art22_1"]["requirements"]
        for req_id, req in reqs.items():
            dps = req["datapoints"]
            provided = sum(1 for dp in dps if plan_data.get(dp) is not None)
            score = round((provided / max(len(dps), 1)) * 100, 1)
            compliant = score >= 75
            results[req["ref"]] = {"compliant": compliant, "score": score, "provided": provided, "total": len(dps),
                                   "gaps": [dp for dp in dps if plan_data.get(dp) is None]}
        # Art 22(2)
        art22_2_dps = CSDDD_REQUIREMENTS["art22_2"]["datapoints"]
        provided_22_2 = sum(1 for dp in art22_2_dps if plan_data.get(dp) is not None)
        results["Art 22(2)"] = {"compliant": provided_22_2 >= 3, "score": round((provided_22_2 / len(art22_2_dps)) * 100, 1)}
        return results

    def _assess_esrs_e1(self, plan_data: dict) -> dict:
        results = {}
        for disc_id, disc in ESRS_E1_DISCLOSURES.items():
            total = len(disc["datapoints"])
            provided = 0
            for dp in disc["datapoints"]:
                dp_id = dp["id"]
                if plan_data.get(dp_id) is not None or plan_data.get(dp["name"].lower().replace(" ", "_")) is not None:
                    provided += 1
            score = round((provided / max(total, 1)) * 100, 1)
            results[disc_id] = {"name": disc["name"], "disclosed": provided > 0, "quality_score": score, "provided": provided, "total": total}
        return results

    def _assess_cdp_c4(self, plan_data: dict) -> dict:
        results = {}
        for q_id, q in CDP_C4_QUESTIONS.items():
            total_dps = 0
            provided_dps = 0
            for sub_id, sub in q["sub_questions"].items():
                for dp in sub["datapoints"]:
                    total_dps += 1
                    if plan_data.get(dp) is not None:
                        provided_dps += 1
            score = round((provided_dps / max(total_dps, 1)) * 100, 1)
            results[q_id] = {"name": q["name"], "answered": provided_dps > 0, "quality_score": score, "provided": provided_dps, "total": total_dps}
        return results

    def _score_dimension(self, dimension: str, plan_data: dict) -> float:
        rubric = SCORING_RUBRICS.get(dimension, {})
        criteria = rubric.get("criteria", {})
        total = 0.0
        for crit_key, max_points in criteria.items():
            val = plan_data.get(crit_key)
            if val is not None:
                if isinstance(val, bool):
                    total += max_points if val else 0
                elif isinstance(val, (int, float)):
                    total += min(max_points, val / 100 * max_points)
                else:
                    total += max_points * 0.5  # qualitative presence
        return round(total, 1)

    def _avg_score(self, assessment: dict) -> float:
        if not assessment:
            return 0.0
        scores = [v.get("score", v.get("quality_score", 0.0)) for v in assessment.values() if isinstance(v, dict)]
        return sum(scores) / max(len(scores), 1)

    def _calc_completeness(self, plan_data: dict) -> dict:
        frameworks = {"TPT": 0, "GFANZ": 0, "IIGCC": 0, "CSDDD": 0, "ESRS_E1": 0, "CDP_C4": 0}
        totals = {"TPT": 0, "GFANZ": 0, "IIGCC": 0, "CSDDD": 0, "ESRS_E1": 0, "CDP_C4": 0}
        for entry in CROSS_FRAMEWORK_MAPPING:
            for fw, ref_key in [("TPT", "tpt_ref"), ("GFANZ", "gfanz_ref"), ("IIGCC", "iigcc_ref"),
                                ("CSDDD", "csddd_ref"), ("ESRS_E1", "esrs_e1_ref"), ("CDP_C4", "cdp_ref")]:
                if entry.get(ref_key, "N/A") != "N/A":
                    totals[fw] += 1
                    # Check if the metric_id data is present in plan_data
                    mn = entry["metric_name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
                    if plan_data.get(mn) is not None or plan_data.get(entry["metric_id"]) is not None:
                        frameworks[fw] += 1
        return {fw: {"total_datapoints": totals[fw], "disclosed": frameworks[fw],
                      "pct": round((frameworks[fw] / max(totals[fw], 1)) * 100, 1)} for fw in frameworks}

    def _identify_gaps(self, plan_data: dict) -> list:
        gaps = []
        for entry in CROSS_FRAMEWORK_MAPPING:
            mn = entry["metric_name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
            if plan_data.get(mn) is None and plan_data.get(entry["metric_id"]) is None:
                missing_fws = []
                for fw, key in [("TPT", "tpt_ref"), ("GFANZ", "gfanz_ref"), ("IIGCC", "iigcc_ref"),
                                ("CSDDD", "csddd_ref"), ("ESRS_E1", "esrs_e1_ref"), ("CDP_C4", "cdp_ref")]:
                    if entry.get(key, "N/A") != "N/A":
                        missing_fws.append(fw)
                if len(missing_fws) >= 3:
                    gaps.append({"metric_id": entry["metric_id"], "metric_name": entry["metric_name"],
                                 "missing_frameworks": missing_fws,
                                 "recommendation": f"Disclose {entry['metric_name']} to satisfy {len(missing_fws)} frameworks simultaneously"})
        return sorted(gaps, key=lambda x: -len(x["missing_frameworks"]))

    def _build_roadmap(self, result: TransitionPlanAssessment) -> list:
        roadmap = []
        if result.target_credibility_score < 50:
            roadmap.append({"priority": 1, "action": "Set SBTi-validated 1.5C targets with Scope 1/2/3 coverage",
                           "impact": "Satisfies TPT-MT-3, GFANZ-T-1, IIGCC-2.1, CSDDD Art 22(1)(a), ESRS E1-4, CDP C4.1"})
        if result.governance_strength_score < 50:
            roadmap.append({"priority": 2, "action": "Establish board-level climate oversight with executive remuneration linkage",
                           "impact": "Satisfies TPT-G-1/G-3, GFANZ-G-1/G-2, CSDDD Art 22(1)(g), ESRS E1-1-08, CDP C1.1-C1.3"})
        if result.financial_commitment_score < 50:
            roadmap.append({"priority": 3, "action": "Allocate CapEx to transition plan with published funding strategy",
                           "impact": "Satisfies TPT-IS-4, GFANZ-TF-1, CSDDD Art 22(1)(e), ESRS E1-1-05, CDP C4.3c"})
        if result.implementation_maturity_score < 50:
            roadmap.append({"priority": 4, "action": "Implement key decarbonisation actions with measurable milestones",
                           "impact": "Satisfies TPT-IS-1, CSDDD Art 22(1)(c)(d), ESRS E1-3, CDP C4.3c"})
        if not roadmap:
            roadmap.append({"priority": 1, "action": "Maintain annual progress reporting and third-party verification",
                           "impact": "Ensures ongoing compliance with all 6 frameworks"})
        return roadmap

    def _assess_regulatory_readiness(self, result: TransitionPlanAssessment) -> dict:
        csddd_ready = all(v.get("compliant", False) for v in result.csddd_compliance.values() if isinstance(v, dict))
        esrs_covered = sum(1 for v in result.esrs_e1_coverage.values() if isinstance(v, dict) and v.get("disclosed")) >= 8
        cdp_answered = sum(1 for v in result.cdp_c4_alignment.values() if isinstance(v, dict) and v.get("answered")) >= 4
        return {
            "CSDDD_Art22": {"ready": csddd_ready, "gaps": [k for k, v in result.csddd_compliance.items() if isinstance(v, dict) and not v.get("compliant", False)]},
            "CSRD_ESRS_E1": {"ready": esrs_covered, "gaps": [k for k, v in result.esrs_e1_coverage.items() if isinstance(v, dict) and not v.get("disclosed", False)]},
            "CDP_C4": {"ready": cdp_answered, "gaps": [k for k, v in result.cdp_c4_alignment.items() if isinstance(v, dict) and not v.get("answered", False)]},
        }

    # ── Target Credibility ───────────────────────────────────────────────

    def assess_target_credibility(self, targets_data: list[dict]) -> list:
        results = []
        for t in targets_data:
            ta = TargetAssessment(
                target_type=t.get("target_type", "absolute"),
                target_year=t.get("target_year", 2050),
                base_year=t.get("base_year", 2019),
                interim_years=t.get("interim_years", []),
                scope_coverage=t.get("scope_coverage", []),
                reduction_pct=t.get("reduction_pct", 0.0),
                science_based=t.get("science_based", False),
                sbti_validated=t.get("sbti_validated", False),
                paris_aligned=t.get("paris_aligned", False),
                methodology=t.get("methodology", ""),
            )
            score = 0.0
            if ta.sbti_validated:
                score += 30
            if ta.paris_aligned:
                score += 25
            if "scope1" in ta.scope_coverage and "scope2" in ta.scope_coverage and "scope3" in ta.scope_coverage:
                score += 20
            elif "scope1" in ta.scope_coverage and "scope2" in ta.scope_coverage:
                score += 10
            if ta.interim_years:
                score += min(15, len(ta.interim_years) * 5)
            if ta.base_year >= 2018:
                score += 10
            ta.credibility_score = min(100.0, round(score, 1))

            # Gap to pathway
            pathway = SECTOR_PATHWAYS.get("power", {})
            if pathway and ta.target_year in [2030, 2035, 2040, 2050]:
                pathway_val = pathway.get(str(ta.target_year), 0)
                if pathway_val != 0:
                    ta.gap_to_pathway = round(((ta.reduction_pct - 50) / 50) * 100, 1)

            results.append(ta)
        return results

    # ── Sector Pathway ───────────────────────────────────────────────────

    def assess_sector_pathway(
        self, sector: str, current_metrics: dict, target_year: int
    ) -> SectorPathwayAssessment:
        pathway = SECTOR_PATHWAYS.get(sector, {})
        result = SectorPathwayAssessment(sector=sector)
        if not pathway:
            return result

        result.pathway_source = pathway.get("source", "")
        result.current_intensity = current_metrics.get("intensity", 0.0)
        result.target_intensity = current_metrics.get("target_intensity", 0.0)
        result.pathway_intensity_for_year = pathway.get(str(target_year), 0.0)

        result.aligned = result.current_intensity <= result.pathway_intensity_for_year
        if result.pathway_intensity_for_year > 0:
            result.gap_pct = round(((result.current_intensity - result.pathway_intensity_for_year) / result.pathway_intensity_for_year) * 100, 1)
        else:
            result.gap_pct = 0.0 if result.current_intensity <= 0 else 100.0

        result.peer_comparison = {"sector_median": pathway.get(str(target_year), 0.0), "unit": pathway.get("unit", "")}
        return result

    # ── Cross-Framework Mapping ──────────────────────────────────────────

    def map_cross_framework_datapoints(self, plan_data: dict) -> dict:
        coverage = {}
        for entry in CROSS_FRAMEWORK_MAPPING:
            mid = entry["metric_id"]
            mn = entry["metric_name"]
            mn_key = mn.lower().replace(" ", "_").replace("(", "").replace(")", "")
            present = plan_data.get(mn_key) is not None or plan_data.get(mid) is not None

            satisfied_fws = []
            for fw, key in [("TPT", "tpt_ref"), ("GFANZ", "gfanz_ref"), ("IIGCC", "iigcc_ref"),
                            ("CSDDD", "csddd_ref"), ("ESRS_E1", "esrs_e1_ref"), ("CDP_C4", "cdp_ref")]:
                if entry.get(key, "N/A") != "N/A":
                    satisfied_fws.append(fw)

            coverage[mid] = {
                "metric_name": mn, "data_provided": present,
                "satisfies_frameworks": satisfied_fws if present else [],
                "missing_from": satisfied_fws if not present else [],
                "data_type": entry["data_type"], "unit": entry["unit"],
            }
        return {"datapoint_map": coverage, "total": len(CROSS_FRAMEWORK_MAPPING),
                "disclosed": sum(1 for v in coverage.values() if v["data_provided"])}

    # ── CSDDD Compliance Report ──────────────────────────────────────────

    def generate_csddd_compliance_report(self, plan_data: dict) -> dict:
        csddd = self._assess_csddd(plan_data)
        esrs_equiv = plan_data.get("esrs_e1_compliant", False)
        overall_compliant = all(v.get("compliant", False) for v in csddd.values() if isinstance(v, dict))
        return {
            "overall_compliant": overall_compliant,
            "esrs_e1_equivalence": esrs_equiv,
            "art22_4_satisfied": esrs_equiv,
            "article_assessments": csddd,
            "remediation_needed": not overall_compliant,
            "remediation_items": [k for k, v in csddd.items() if isinstance(v, dict) and not v.get("compliant", False)],
        }

    # ── Static Reference Methods ─────────────────────────────────────────

    @staticmethod
    def get_tpt_framework() -> dict:
        return TPT_FRAMEWORK

    @staticmethod
    def get_gfanz_components() -> dict:
        return GFANZ_COMPONENTS

    @staticmethod
    def get_iigcc_nzif_steps() -> dict:
        return IIGCC_NZIF_STEPS

    @staticmethod
    def get_csddd_requirements() -> dict:
        return CSDDD_REQUIREMENTS

    @staticmethod
    def get_esrs_e1_disclosures() -> dict:
        return ESRS_E1_DISCLOSURES

    @staticmethod
    def get_cdp_c4_questions() -> dict:
        return CDP_C4_QUESTIONS

    @staticmethod
    def get_cross_framework_mapping() -> list[dict]:
        return CROSS_FRAMEWORK_MAPPING

    @staticmethod
    def get_scoring_rubrics() -> dict:
        return SCORING_RUBRICS

    @staticmethod
    def get_sector_pathways() -> dict:
        return SECTOR_PATHWAYS

    @staticmethod
    def get_target_validation_criteria() -> dict:
        return TARGET_VALIDATION_CRITERIA

    @staticmethod
    def get_carbon_credit_quality_criteria() -> dict:
        return CARBON_CREDIT_QUALITY

    @staticmethod
    def get_regulatory_timeline() -> dict:
        return REGULATORY_TIMELINE
