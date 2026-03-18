"""
Transition Finance Credibility Engine  (E99)
============================================
TPT Disclosure Framework (Oct 2023), GFANZ Expectations for Real-Economy
Transition Plans (2023), SBTi Corporate Net-Zero Standard v1.1, Race to Zero
2023 Criteria, Portfolio Temperature Alignment (WACI/implied temperature),
TNFD LEAP nature integration, and Transition Instrument Classification.

References:
  - TPT Disclosure Framework, Transition Plan Taskforce (Oct 2023)
  - GFANZ Expectations for Real-economy Transition Plans (Nov 2023)
  - SBTi Corporate Net-Zero Standard v1.1 (Sep 2023)
  - SBTi FLAG Guidance (2022)
  - Race to Zero 2023 Criteria (UNFCCC High-Level Champions)
  - TNFD Recommendations v1.0 (Sep 2023)
  - SBTN Step-by-step guide (2023)
  - ICMA Climate Transition Finance Handbook (Dec 2023)
  - LMA SLL Principles 2023
  - LMA Transition Guidance 2023
"""
from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# Reference Data — TPT 6 Elements + Weights + Quality Tiers
# ---------------------------------------------------------------------------

TPT_ELEMENTS: dict[str, dict] = {
    "foundations": {
        "element_id": "E1",
        "name": "Foundations",
        "weight": 0.25,
        "description": (
            "Strategic ambition (net-zero/interim targets), scenario analysis used "
            "(1.5°C aligned, IEA NZE2050 / IPCC AR6), and transition governance mandate."
        ),
        "sub_elements": [
            "strategic_ambition_net_zero",
            "scenario_analysis_15c_aligned",
            "interim_targets_2030_2040",
            "board_approved_plan",
        ],
        "quality_indicators": {
            "initial": "No formal ambition or informal net-zero pledge only",
            "developing": "Net-zero pledge with unvalidated 2030 target",
            "advanced": "SBTi-validated near-term + long-term targets; 1.5°C scenario",
            "leading": "SBTi net-zero validated; IPCC 1.5°C aligned; board-approved; third-party assured",
        },
    },
    "implementation": {
        "element_id": "E2",
        "name": "Implementation",
        "weight": 0.20,
        "description": (
            "Decarbonisation levers (operational efficiency, fuel switching, CCS), "
            "capital allocation plan (green CAPEX), milestones with timelines."
        ),
        "sub_elements": [
            "decarbonisation_levers_identified",
            "green_capex_pct_defined",
            "phase_out_plan_fossil_assets",
            "technology_roadmap_2030_2050",
            "milestones_with_kpis",
        ],
        "quality_indicators": {
            "initial": "High-level initiatives without quantified roadmap",
            "developing": "Some levers identified; partial CAPEX alignment",
            "advanced": "Quantified roadmap; green CAPEX ≥20%; asset phase-out timeline",
            "leading": "Full CAPEX alignment; green CAPEX ≥40%; technology roadmap to 2050",
        },
    },
    "engagement": {
        "element_id": "E3",
        "name": "Engagement",
        "weight": 0.10,
        "description": (
            "Supply chain / value chain engagement, policy advocacy alignment with "
            "Paris goals, collaborative initiatives (SBTi, RE100, CA100+)."
        ),
        "sub_elements": [
            "supplier_engagement_programme",
            "policy_advocacy_paris_aligned",
            "collaborative_initiatives_membership",
            "customer_engagement_scope3_c11",
        ],
        "quality_indicators": {
            "initial": "No formal supplier engagement",
            "developing": "Supplier survey; informal policy dialogue",
            "advanced": "Formal supplier decarbonisation programme; CA100+ or SBTi supply chain",
            "leading": "Science-based supplier targets; public policy lobbying Paris-aligned; RE100/EP100 member",
        },
    },
    "metrics_targets": {
        "element_id": "E4",
        "name": "Metrics & Targets",
        "weight": 0.20,
        "description": (
            "GHG disclosure (S1/S2/S3), sector-specific KPIs, Paris-aligned interim "
            "targets (2025/2030/2040/2050), temperature overshoot metrics."
        ),
        "sub_elements": [
            "scope1_scope2_disclosed",
            "scope3_coverage_pct",
            "sector_kpis_defined",
            "sbti_validation_status",
            "temperature_score_implied",
            "carbon_intensity_trajectory",
        ],
        "quality_indicators": {
            "initial": "Scope 1+2 only; no interim targets",
            "developing": "Scope 1+2+3; unvalidated 2030 target",
            "advanced": "Full Scope 1+2+3 with SBTi near-term validation; sector KPIs",
            "leading": "SBTi net-zero validated; 1.5°C pathway; assured; carbon intensity time-series",
        },
    },
    "governance": {
        "element_id": "E5",
        "name": "Governance",
        "weight": 0.15,
        "description": (
            "Board oversight (climate committee/mandate), executive remuneration link to "
            "climate targets, risk management integration (TCFD-aligned)."
        ),
        "sub_elements": [
            "board_climate_committee",
            "executive_remuneration_climate_linked",
            "tcfd_risk_management_integrated",
            "transition_accountability_structure",
        ],
        "quality_indicators": {
            "initial": "No board-level climate mandate",
            "developing": "Board awareness; informal oversight",
            "advanced": "Named board champion; partial remuneration link",
            "leading": "Dedicated board climate committee; >15% exec pay linked to climate; TCFD fully integrated",
        },
    },
    "finance": {
        "element_id": "E6",
        "name": "Finance",
        "weight": 0.10,
        "description": (
            "CAPEX/OPEX alignment with transition pathway, green/transition finance instruments "
            "issued, stranded asset provisions, internal carbon price."
        ),
        "sub_elements": [
            "green_capex_alignment_ratio",
            "internal_carbon_price_set",
            "stranded_asset_provisions",
            "transition_instruments_issued",
            "financing_gap_assessment",
        ],
        "quality_indicators": {
            "initial": "No financial alignment assessment",
            "developing": "Green bond / SLL issued; no capex alignment ratio",
            "advanced": "Green CAPEX ratio >30%; internal carbon price >USD 50/tCO2",
            "leading": "Full CAPEX/OPEX alignment; ICP >USD 150/tCO2; stranded assets provisioned",
        },
    },
}

QUALITY_TIERS: dict[str, dict] = {
    "initial":    {"min_score": 0.00, "max_score": 0.40, "label": "Initial (<40%)", "color": "red"},
    "developing": {"min_score": 0.40, "max_score": 0.60, "label": "Developing (40-60%)", "color": "orange"},
    "advanced":   {"min_score": 0.60, "max_score": 0.80, "label": "Advanced (60-80%)", "color": "amber"},
    "leading":    {"min_score": 0.80, "max_score": 1.00, "label": "Leading (≥80%)", "color": "green"},
}

# ---------------------------------------------------------------------------
# SBTi Validation Criteria (Corporate Net-Zero Standard v1.1, Sep 2023)
# ---------------------------------------------------------------------------

SBTI_CRITERIA: dict[str, dict] = {
    "near_term_scope12": {
        "id": "NT-1",
        "name": "Near-term Scope 1+2 target",
        "description": "Reduce absolute Scope 1+2 by ≥42% by 2030 vs base year (SBTi v1.1)",
        "reduction_pct_required": 42.0,
        "target_year": 2030,
        "pathway": "1.5°C linear regression",
        "validation_body": "SBTi",
        "weight": 0.25,
    },
    "near_term_scope3": {
        "id": "NT-2",
        "name": "Near-term Scope 3 target",
        "description": "Reduce Scope 3 by ≥25% by 2030 if Scope 3 > 40% of total emissions",
        "reduction_pct_required": 25.0,
        "trigger_pct": 40.0,
        "target_year": 2030,
        "pathway": "Sector-specific SDA or absolute contraction",
        "validation_body": "SBTi",
        "weight": 0.15,
    },
    "long_term_scope12": {
        "id": "LT-1",
        "name": "Long-term Scope 1+2 target",
        "description": "Reduce absolute Scope 1+2 by ≥90% by 2050 vs base year",
        "reduction_pct_required": 90.0,
        "target_year": 2050,
        "residual_max_pct": 10.0,
        "pathway": "1.5°C-aligned; neutralise residuals with carbon removals",
        "weight": 0.25,
    },
    "long_term_scope3": {
        "id": "LT-2",
        "name": "Long-term Scope 3 target",
        "description": "Reduce Scope 3 by ≥90% by 2050, or apply FLAG methodology for land-use sectors",
        "reduction_pct_required": 90.0,
        "target_year": 2050,
        "flag_alternative": True,
        "weight": 0.15,
    },
    "net_zero_target": {
        "id": "NZ-1",
        "name": "Net-Zero Target",
        "description": (
            "Residual emissions (≤10% of base year) neutralised by permanent carbon removal "
            "by 2050. Removal must be IPCC AR6-consistent (DACCS, BECCS, enhanced weathering, etc.)."
        ),
        "max_residual_pct": 10.0,
        "removal_types": ["DACCS", "BECCS", "enhanced_weathering", "biochar", "ocean_alkalinity"],
        "weight": 0.15,
    },
    "flag_sector": {
        "id": "FLAG-1",
        "name": "FLAG (Forest, Land, Agriculture) AFOLU Target",
        "description": "Entities with AFOLU emissions must set SBTi FLAG targets separately from non-land targets",
        "sectors": ["agriculture", "forestry", "land_use", "food_beverage", "paper_pulp"],
        "required_if_afolu_pct": 20.0,
        "weight": 0.05,
    },
}

# ---------------------------------------------------------------------------
# Race to Zero 2023 Criteria (UNFCCC High-Level Champions — 5 Cs)
# ---------------------------------------------------------------------------

RACE_TO_ZERO_CRITERIA: dict[str, dict] = {
    "commit": {
        "criterion": "Commit",
        "description": "Pledge net-zero GHG emissions (Scope 1+2+3) by 2050 at latest; no new coal.",
        "requirements": [
            "Net-zero pledge by 2050 (or earlier)",
            "No investment in new unabated coal capacity",
            "No new oil/gas exploration (for energy sector)",
        ],
        "weight": 0.25,
        "membership_link": "GFANZ sub-alliances (NZBA, NZAM, NZI, NZAOA)",
    },
    "countable": {
        "criterion": "Countable (Plan)",
        "description": "2030 interim target ≥50% reduction (Paris-aligned); published roadmap covering Scope 1+2+3.",
        "requirements": [
            "2030 interim target ≥50% vs base year",
            "Scope 3 covered",
            "Roadmap publicly available",
            "Validated by SBTi or equivalent credible body",
        ],
        "weight": 0.25,
        "interim_target_min_pct": 50.0,
    },
    "consistent": {
        "criterion": "Consistent (Proceed)",
        "description": "Annual GHG disclosure aligned with CDP/TCFD/ISSB S2 reporting standards.",
        "requirements": [
            "Annual GHG inventory (Scope 1+2+3)",
            "CDP disclosure (A-list preferred)",
            "TCFD or ISSB S2 aligned report",
            "Third-party verification (limited or reasonable assurance)",
        ],
        "weight": 0.20,
        "reporting_standards": ["CDP", "TCFD", "ISSB S2", "CSRD ESRS E1"],
    },
    "credible": {
        "criterion": "Credible (Publish)",
        "description": "Annual progress report within 12 months of reporting period end.",
        "requirements": [
            "Annual progress report within 12 months",
            "Milestones vs interim targets disclosed",
            "Action taken vs plan disclosed",
        ],
        "weight": 0.15,
    },
    "communicate": {
        "criterion": "Communicate (Account)",
        "description": "Science-based or equivalent validation required; no greenwashing.",
        "requirements": [
            "SBTi validation or equivalent (Exponential Roadmap, Gold Standard)",
            "Anti-greenwashing compliance (EU Reg 2023/2441)",
            "Third-party certification of offset quality (ICVCM CCP label)",
        ],
        "weight": 0.15,
        "validation_bodies": ["SBTi", "Exponential Roadmap Initiative", "Gold Standard", "VCMI"],
    },
}

RTZ_MEMBERSHIP_CATEGORIES: dict[str, list[str]] = {
    "gfanz": ["NZBA (Net-Zero Banking Alliance)", "NZAM (Net-Zero Asset Managers)", "NZI (Net-Zero Insurance)", "NZAOA (Net-Zero Asset Owner Alliance)"],
    "re100": ["RE100 — 100% renewable electricity commitment"],
    "ep100": ["EP100 — energy productivity commitment"],
    "ev100": ["EV100 — electric vehicles commitment"],
    "sbti": ["SBTi Committed", "SBTi Validated Near-Term", "SBTi Net-Zero Validated"],
    "ca100plus": ["CA100+ — engagement target company", "CA100+ — lead investor"],
}

# ---------------------------------------------------------------------------
# 20 Sector Transition Pathways (2030 / 2040 / 2050 GHG reduction targets)
# ---------------------------------------------------------------------------

SECTOR_PATHWAYS: dict[str, dict] = {
    "power_generation": {
        "name": "Power Generation & Utilities",
        "nace": "D35",
        "pathway_source": "IEA NZE2050; IPCC AR6",
        "base_year": 2019,
        "targets": {2030: 60, 2040: 80, 2050: 95},
        "key_levers": ["renewable_scale_up", "coal_phase_out", "grid_flexibility", "CCUS"],
        "current_intensity_gco2_kwh": 450.0,
        "target_intensity_gco2_kwh": {2030: 180, 2040: 90, 2050: 25},
        "temperature_alignment_2c": 55,
        "temperature_alignment_15c": 60,
    },
    "oil_gas": {
        "name": "Oil & Gas Extraction",
        "nace": "B06",
        "pathway_source": "IEA NZE2050; OGCI",
        "base_year": 2019,
        "targets": {2030: 30, 2040: 55, 2050: 90},
        "key_levers": ["methane_abatement", "CCUS", "hydrogen_shift", "no_new_exploration_post_2025"],
        "current_intensity_kgco2_boe": 60.0,
        "temperature_alignment_2c": 25,
        "temperature_alignment_15c": 30,
    },
    "steel": {
        "name": "Iron & Steel",
        "nace": "C24.1",
        "pathway_source": "STEEL Zero / Mission Possible Partnership",
        "base_year": 2019,
        "targets": {2030: 25, 2040: 55, 2050: 90},
        "key_levers": ["hydrogen_dri", "electric_arc_furnace", "CCUS", "scrap_recovery"],
        "current_intensity_tco2_tsteel": 1.85,
        "target_intensity_tco2_tsteel": {2030: 1.39, 2040: 0.83, 2050: 0.19},
        "temperature_alignment_2c": 20,
        "temperature_alignment_15c": 25,
    },
    "cement": {
        "name": "Cement & Concrete",
        "nace": "C23.5",
        "pathway_source": "GCCA Net Zero Roadmap 2050",
        "base_year": 2019,
        "targets": {2030: 20, 2040: 50, 2050: 80},
        "key_levers": ["clinker_substitution", "alternative_fuels", "CCUS", "novel_cements"],
        "current_intensity_kgco2_tclinker": 842.0,
        "temperature_alignment_2c": 18,
        "temperature_alignment_15c": 20,
    },
    "chemicals": {
        "name": "Chemicals & Petrochemicals",
        "nace": "C20",
        "pathway_source": "IEA Chemicals; Mission Possible Partnership",
        "base_year": 2019,
        "targets": {2030: 20, 2040: 45, 2050: 75},
        "key_levers": ["green_hydrogen_feedstock", "bio_based_materials", "CCUS", "circular_economy"],
        "temperature_alignment_2c": 18,
        "temperature_alignment_15c": 20,
    },
    "aviation": {
        "name": "Aviation",
        "nace": "H51",
        "pathway_source": "IATA Net Zero 2050; ICAO CORSIA",
        "base_year": 2019,
        "targets": {2030: 5, 2040: 35, 2050: 100},
        "key_levers": ["SAF_scale_up", "aircraft_efficiency", "operations_optimisation", "hydrogen_aircraft"],
        "saf_target_pct_2030": 10.0,
        "saf_target_pct_2050": 65.0,
        "temperature_alignment_2c": 5,
        "temperature_alignment_15c": 5,
    },
    "shipping": {
        "name": "Shipping & Maritime",
        "nace": "H50",
        "pathway_source": "IMO GHG Strategy 2023 (net-zero by 2050)",
        "base_year": 2008,
        "targets": {2030: 30, 2040: 70, 2050: 100},
        "key_levers": ["green_ammonia", "green_methanol", "vessel_efficiency", "slow_steaming"],
        "temperature_alignment_2c": 30,
        "temperature_alignment_15c": 30,
    },
    "road_transport": {
        "name": "Road Transport",
        "nace": "H49",
        "pathway_source": "IEA NZE2050; EU Fit for 55",
        "base_year": 2019,
        "targets": {2030: 25, 2040: 65, 2050: 95},
        "key_levers": ["ev_transition", "charging_infrastructure", "public_transport", "vehicle_efficiency"],
        "ev_fleet_pct_target": {2030: 30, 2040: 70, 2050: 95},
        "temperature_alignment_2c": 22,
        "temperature_alignment_15c": 25,
    },
    "real_estate": {
        "name": "Real Estate & Buildings",
        "nace": "L68",
        "pathway_source": "CRREM 2.0; EU EPBD 2024",
        "base_year": 2019,
        "targets": {2030: 35, 2040: 60, 2050: 90},
        "key_levers": ["energy_efficiency_retrofit", "heat_pump_switch", "renewable_onsite", "embodied_carbon"],
        "temperature_alignment_2c": 30,
        "temperature_alignment_15c": 35,
    },
    "banking_finance": {
        "name": "Banking & Financial Services",
        "nace": "K64",
        "pathway_source": "NZBA Guidelines 2.0; PCAF",
        "base_year": 2019,
        "targets": {2030: 50, 2040: 70, 2050: 100},
        "key_levers": ["portfolio_decarbonisation", "green_lending", "engagement", "divestment"],
        "metric": "Financed emissions (PCAF-attributed)",
        "temperature_alignment_2c": 45,
        "temperature_alignment_15c": 50,
    },
    "asset_management": {
        "name": "Asset Management",
        "nace": "K66.3",
        "pathway_source": "NZAM Initiative v2; TCFD",
        "base_year": 2019,
        "targets": {2030: 50, 2040: 70, 2050: 100},
        "key_levers": ["portfolio_temperature_alignment", "engagement", "esg_integration", "green_products"],
        "metric": "WACI (tCO2e / USD mn revenue)",
        "temperature_alignment_2c": 45,
        "temperature_alignment_15c": 50,
    },
    "insurance": {
        "name": "Insurance",
        "nace": "K65",
        "pathway_source": "NZI Initiative v1.0; EIOPA",
        "base_year": 2019,
        "targets": {2030: 30, 2040: 55, 2050: 90},
        "key_levers": ["insurance_portfolio_alignment", "underwriting_exclusions", "cat_risk_pricing"],
        "temperature_alignment_2c": 28,
        "temperature_alignment_15c": 30,
    },
    "agriculture": {
        "name": "Agriculture & Food",
        "nace": "A01",
        "pathway_source": "SBTi FLAG; UNFCCC AFOLU",
        "base_year": 2019,
        "targets": {2030: 30, 2040: 55, 2050: 72},
        "key_levers": ["methane_abatement", "precision_ag", "land_use_efficiency", "soil_carbon"],
        "note": "FLAG targets separate from non-land targets under SBTi v1.1",
        "temperature_alignment_2c": 25,
        "temperature_alignment_15c": 30,
    },
    "forestry_land_use": {
        "name": "Forestry, Land Use & Timber",
        "nace": "A02",
        "pathway_source": "SBTi FLAG; SBTN",
        "base_year": 2019,
        "targets": {2030: 50, 2040: 70, 2050: 90},
        "key_levers": ["deforestation_halt", "reforestation", "sustainable_forest_management"],
        "temperature_alignment_2c": 45,
        "temperature_alignment_15c": 50,
    },
    "mining": {
        "name": "Mining & Metals",
        "nace": "B08",
        "pathway_source": "ICMM; IEA NZE2050",
        "base_year": 2019,
        "targets": {2030: 25, 2040: 50, 2050: 80},
        "key_levers": ["electrification", "green_hydrogen", "renewable_power", "scope3_engagement"],
        "temperature_alignment_2c": 22,
        "temperature_alignment_15c": 25,
    },
    "paper_pulp": {
        "name": "Paper, Pulp & Packaging",
        "nace": "C17",
        "pathway_source": "Two Degrees Separator",
        "base_year": 2019,
        "targets": {2030: 25, 2040: 50, 2050: 75},
        "key_levers": ["biomass_efficiency", "renewable_heat", "circular_recycling"],
        "temperature_alignment_2c": 20,
        "temperature_alignment_15c": 25,
    },
    "textiles_apparel": {
        "name": "Textiles & Apparel",
        "nace": "C13-C15",
        "pathway_source": "Fashion Pact; Science Based Targets Network",
        "base_year": 2019,
        "targets": {2030: 30, 2040: 55, 2050: 90},
        "key_levers": ["renewable_energy", "scope3_supplier_engagement", "circular_design"],
        "temperature_alignment_2c": 28,
        "temperature_alignment_15c": 30,
    },
    "food_beverage": {
        "name": "Food & Beverage Processing",
        "nace": "C10-C11",
        "pathway_source": "SBTi FLAG + non-FLAG",
        "base_year": 2019,
        "targets": {2030: 30, 2040: 55, 2050: 72},
        "key_levers": ["agricultural_sourcing", "scope3_supplier", "energy_efficiency", "refrigerants"],
        "temperature_alignment_2c": 25,
        "temperature_alignment_15c": 30,
    },
    "telecommunications": {
        "name": "Telecommunications & IT",
        "nace": "J61-J63",
        "pathway_source": "GeSI SMARTer2030; SBTi ICT guidance",
        "base_year": 2019,
        "targets": {2030: 50, 2040: 75, 2050: 95},
        "key_levers": ["renewable_power_data_centres", "network_efficiency", "device_lifecycle"],
        "temperature_alignment_2c": 45,
        "temperature_alignment_15c": 50,
    },
    "healthcare": {
        "name": "Healthcare & Pharmaceuticals",
        "nace": "Q86",
        "pathway_source": "HCWH; SBTi",
        "base_year": 2019,
        "targets": {2030: 30, 2040: 55, 2050: 80},
        "key_levers": ["anaesthetic_gas_elimination", "supply_chain_engagement", "renewable_energy"],
        "temperature_alignment_2c": 25,
        "temperature_alignment_15c": 30,
    },
}

# ---------------------------------------------------------------------------
# GFANZ Expectations for Real-Economy Transition Plans (Nov 2023)
# ---------------------------------------------------------------------------

GFANZ_EXPECTATIONS: dict[str, Any] = {
    "name": "GFANZ Expectations for Real-economy Transition Plans",
    "version": "November 2023",
    "url": "https://www.gfanzalliance.com/",
    "five_components": {
        "ambition": {
            "description": "Net-zero ambition with 2050 target and interim milestones",
            "key_question": "Does the entity have a validated net-zero or Paris-aligned target?",
            "aligned_frameworks": ["SBTi", "Race to Zero", "UNFCCC"],
        },
        "action": {
            "description": "Concrete near-term actions (2025-2030) to decarbonise operations and value chain",
            "key_question": "What specific actions will be taken in the next 5 years?",
            "expected_disclosures": ["green CAPEX ratio", "phase-out timeline", "technology roadmap"],
        },
        "accountability": {
            "description": "Governance, incentives, and accountability structures",
            "key_question": "Who is accountable for delivery at board and executive level?",
            "expected_disclosures": ["board mandate", "exec remuneration link", "progress monitoring"],
        },
        "fairness": {
            "description": "Just transition considerations — workforce, communities, supply chain",
            "key_question": "How does the plan address impacts on workers and communities?",
            "frameworks": ["ILO Just Transition Guidelines", "B Team Just Transition Principles"],
        },
        "credibility": {
            "description": "Third-party validation and independent assurance of commitments",
            "key_question": "Has the plan been independently validated?",
            "validation_bodies": ["SBTi", "VCMI Claims Code", "Exponential Roadmap Initiative"],
        },
    },
    "high_climate_impact_sectors": [
        "power_generation", "oil_gas", "steel", "cement", "chemicals",
        "aviation", "shipping", "road_transport", "real_estate", "agriculture",
    ],
    "portfolio_alignment_expectation": {
        "financed_emissions_reduction_2030_pct": 50,
        "portfolio_temperature_target_2030_c": 2.0,
        "portfolio_temperature_target_2050_c": 1.5,
        "engagement_coverage_aum_pct": 70,
    },
}

# ---------------------------------------------------------------------------
# Transition Instrument Classification
# ---------------------------------------------------------------------------

TRANSITION_INSTRUMENT_CRITERIA: dict[str, dict] = {
    "transition_bond": {
        "name": "Transition Bond",
        "standard": "ICMA Climate Transition Finance Handbook 2023",
        "criteria": [
            "Issuer has a credible climate transition strategy (TPT/GFANZ aligned)",
            "Use of proceeds: transition activities (decarbonisation capex, asset modernisation)",
            "Science-based targets: SBTi validated or equivalent",
            "Transparent tracking of proceeds allocation",
            "Annual reporting vs interim milestones",
        ],
        "eligible_sectors": ["steel", "cement", "chemicals", "aviation", "shipping", "oil_gas"],
        "key_risk": "No universal taxonomy; relies on issuer-level credibility assessment",
    },
    "sustainability_linked_loan": {
        "name": "Sustainability-Linked Loan (SLL)",
        "standard": "LMA Sustainability-Linked Loan Principles 2023",
        "criteria": [
            "KPI materiality: ≥1 core sustainability KPI relevant to borrower's business",
            "SPT ambition: ambitious, credible, measurable vs base year",
            "SPT calibration: consistent with sector decarbonisation pathway",
            "Margin ratchet: step-up/step-down tied to SPT achievement",
            "Annual KPI verification by external reviewer",
        ],
        "margin_ratchet_bps_typical": {"step_up": 5, "step_down": 5},
        "kpi_examples": ["GHG intensity tCO2/revenue", "RE pct", "water withdrawal", "LTIR"],
    },
    "transition_loan_facility": {
        "name": "Transition Loan Facility (TLF)",
        "standard": "LMA Transition Loan Guidance 2023",
        "criteria": [
            "Borrower has Paris-aligned transition plan",
            "Loan proceeds for transition capital expenditure",
            "Four sector pathways defined: power, transport, industry, buildings",
            "Third-party transition plan assessment required",
        ],
        "sector_pathways": ["power_generation", "road_transport", "steel_cement_chemicals", "real_estate"],
    },
    "blended_finance_transition": {
        "name": "Blended Finance — Transition",
        "standard": "Convergence Blended Finance; OECD DAC Principles",
        "criteria": [
            "First-loss / concessional tranche from DFI/MDB/government",
            "Commercial tranche with market-rate returns",
            "Climate additionality demonstrated",
            "Catalytic capital ratio ≥3:1 (mobilisation vs concessional)",
        ],
        "typical_structures": ["first_loss_guarantee", "concessional_subordinated_debt", "equity_co_investment"],
    },
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WACI_UNIT = "tCO2e / USD mn revenue"
IMPLIED_TEMP_BASE_WACI = 300.0  # tCO2e/USD mn → ~2.5°C baseline assumption
IMPLIED_TEMP_15C_WACI = 100.0   # tCO2e/USD mn → 1.5°C target
IMPLIED_TEMP_3C_WACI = 600.0    # tCO2e/USD mn → ~3°C

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _score_tpt_element(element_id: str, element_inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Score a single TPT element 0-1 from user-provided sub-element scores or qualitative tier.
    element_inputs: dict with optional keys 'score' (float 0-1) or 'sub_scores' (list of floats).
    """
    element = TPT_ELEMENTS.get(element_id, {})
    n_sub = len(element.get("sub_elements", [1]))

    if "score" in element_inputs:
        score = float(element_inputs["score"])
    elif "sub_scores" in element_inputs:
        scores = element_inputs["sub_scores"]
        score = sum(scores) / len(scores) if scores else 0.0
    elif "tier" in element_inputs:
        tier_map = {"initial": 0.20, "developing": 0.50, "advanced": 0.70, "leading": 0.90}
        score = tier_map.get(element_inputs["tier"].lower(), 0.20)
    else:
        score = element_inputs.get("completion_pct", 0.0) / 100.0

    score = max(0.0, min(1.0, score))

    # Quality tier
    tier = "initial"
    for t, bounds in QUALITY_TIERS.items():
        if bounds["min_score"] <= score < bounds["max_score"]:
            tier = t
            break
    if score >= 0.80:
        tier = "leading"

    return {
        "element_id": element.get("element_id", element_id),
        "name": element.get("name", element_id),
        "weight": element.get("weight", 0.0),
        "score": round(score, 4),
        "weighted_score": round(score * element.get("weight", 0.0), 4),
        "quality_tier": tier,
    }


def _get_quality_tier(score: float) -> str:
    if score >= 0.80:
        return "leading"
    if score >= 0.60:
        return "advanced"
    if score >= 0.40:
        return "developing"
    return "initial"


def _calculate_waci(holdings: list[dict[str, Any]]) -> float:
    """
    WACI = Σ(weight_i × tCO2e_i / revenue_i_M)
    holdings: list of {weight: float, tco2e: float, revenue_usd_mn: float}
    """
    waci = 0.0
    for h in holdings:
        w = h.get("weight", 0.0)
        emissions = h.get("tco2e", 0.0)
        revenue = h.get("revenue_usd_mn", 1.0) or 1.0
        waci += w * (emissions / revenue)
    return round(waci, 4)


def _implied_temperature(waci: float) -> float:
    """
    Estimate implied portfolio temperature from WACI using linear interpolation
    between benchmark anchors:
      WACI 100 → 1.5°C
      WACI 300 → 2.5°C
      WACI 600 → 3.5°C
    Simplified proxy; full TCFD/SBTi approach requires sector-specific SDA.
    """
    if waci <= IMPLIED_TEMP_15C_WACI:
        return 1.5
    if waci <= IMPLIED_TEMP_BASE_WACI:
        # 100-300 → 1.5-2.5°C
        frac = (waci - IMPLIED_TEMP_15C_WACI) / (IMPLIED_TEMP_BASE_WACI - IMPLIED_TEMP_15C_WACI)
        return round(1.5 + frac * 1.0, 2)
    if waci <= IMPLIED_TEMP_3C_WACI:
        # 300-600 → 2.5-3.5°C
        frac = (waci - IMPLIED_TEMP_BASE_WACI) / (IMPLIED_TEMP_3C_WACI - IMPLIED_TEMP_BASE_WACI)
        return round(2.5 + frac * 1.0, 2)
    return round(3.5 + (waci - IMPLIED_TEMP_3C_WACI) / 600.0, 2)


def _detect_red_flags(
    tpt_score: float,
    sbti_score: float,
    rtz_score: float,
    tpt_inputs: dict,
    sbti_inputs: dict,
) -> list[dict[str, str]]:
    """Identify greenwash / credibility red flags."""
    flags: list[dict[str, str]] = []

    if tpt_inputs.get("net_zero_pledge") and tpt_score < 0.30:
        flags.append({
            "flag": "NET_ZERO_PLEDGE_WITHOUT_PLAN",
            "severity": "HIGH",
            "description": "Net-zero pledge made but transition plan quality score <30% — potential greenwash.",
        })

    if sbti_inputs.get("sbti_committed") and sbti_score < 0.20:
        flags.append({
            "flag": "SBTI_COMMITTED_WITHOUT_VALIDATED_TARGETS",
            "severity": "MEDIUM",
            "description": "SBTi 'Committed' status but targets not yet validated — monitor deadline.",
        })

    scope3_coverage = tpt_inputs.get("scope3_coverage_pct", 0.0)
    if tpt_inputs.get("net_zero_pledge") and scope3_coverage < 40.0:
        flags.append({
            "flag": "SCOPE3_COVERAGE_INSUFFICIENT",
            "severity": "HIGH",
            "description": f"Net-zero claim but Scope 3 coverage only {scope3_coverage}% — GHG Protocol S3 >40% threshold not met.",
        })

    if tpt_inputs.get("offset_reliance_pct", 0.0) > 50.0:
        flags.append({
            "flag": "EXCESSIVE_OFFSET_RELIANCE",
            "severity": "HIGH",
            "description": "Offset reliance >50% of target — inconsistent with SBTi Net-Zero Standard (max 10% residuals).",
        })

    if tpt_inputs.get("no_interim_targets") and tpt_inputs.get("net_zero_pledge"):
        flags.append({
            "flag": "NO_INTERIM_TARGETS",
            "severity": "MEDIUM",
            "description": "Net-zero 2050 pledge without 2030 interim target — credibility gap per TPT + Race to Zero.",
        })

    return flags


# ---------------------------------------------------------------------------
# Public API Functions
# ---------------------------------------------------------------------------


def assess_transition_finance_credibility(
    entity_name: str,
    sector: str,
    tpt_inputs: dict[str, Any] | None = None,
    sbti_inputs: dict[str, Any] | None = None,
    rtz_inputs: dict[str, Any] | None = None,
    portfolio_inputs: dict[str, Any] | None = None,
    tnfd_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Full transition finance credibility assessment.

    Scores:
    - TPT 6-element composite (weighted)
    - SBTi validation criteria
    - Race to Zero 5 Cs
    - Portfolio temperature alignment (WACI-based)
    - TNFD LEAP nature integration
    - Overall credibility composite + red flags
    """
    tpt_in = tpt_inputs or {}
    sbti_in = sbti_inputs or {}
    rtz_in = rtz_inputs or {}
    port_in = portfolio_inputs or {}
    tnfd_in = tnfd_inputs or {}

    # ── TPT Scoring ──────────────────────────────────────────────────────────
    tpt_element_scores: dict[str, Any] = {}
    tpt_weighted_sum = 0.0
    for elem_id, elem_data in TPT_ELEMENTS.items():
        elem_input = tpt_in.get(elem_id, {})
        scored = _score_tpt_element(elem_id, elem_input)
        tpt_element_scores[elem_id] = scored
        tpt_weighted_sum += scored["weighted_score"]

    tpt_tier = _get_quality_tier(tpt_weighted_sum)

    # ── SBTi Scoring ─────────────────────────────────────────────────────────
    sbti_scores: dict[str, Any] = {}
    sbti_total = 0.0
    sector_data = SECTOR_PATHWAYS.get(sector, {})
    sector_2030_target = sector_data.get("targets", {}).get(2030, 42)

    for crit_id, crit in SBTI_CRITERIA.items():
        raw = sbti_in.get(crit_id, {})
        score = float(raw.get("score", 0.0))
        status = raw.get("status", "not_assessed")
        if status == "validated":
            score = 1.0
        elif status == "committed":
            score = max(score, 0.5)
        elif status == "not_applicable":
            score = 1.0  # full marks for N/A criteria (e.g. FLAG for non-land sector)
        sbti_scores[crit_id] = {
            "name": crit["name"],
            "weight": crit["weight"],
            "score": round(score, 3),
            "weighted": round(score * crit["weight"], 4),
            "status": status,
        }
        sbti_total += score * crit["weight"]

    sbti_tier = _get_quality_tier(sbti_total)

    # ── Race to Zero Scoring ─────────────────────────────────────────────────
    rtz_scores: dict[str, Any] = {}
    rtz_total = 0.0
    for crit_id, crit in RACE_TO_ZERO_CRITERIA.items():
        raw = rtz_in.get(crit_id, {})
        score = float(raw.get("score", 0.0))
        rtz_scores[crit_id] = {
            "name": crit["criterion"],
            "weight": crit["weight"],
            "score": round(score, 3),
            "weighted": round(score * crit["weight"], 4),
            "met": score >= 0.7,
        }
        rtz_total += score * crit["weight"]

    rtz_tier = _get_quality_tier(rtz_total)

    # ── Portfolio Temperature ─────────────────────────────────────────────────
    holdings = port_in.get("holdings", [])
    portfolio_temp_result: dict[str, Any] = {}
    port_score = 0.5  # default
    if holdings:
        portfolio_temp_result = calculate_portfolio_temperature(holdings)
        implied_temp = portfolio_temp_result["implied_temperature_c"]
        if implied_temp <= 1.5:
            port_score = 1.0
        elif implied_temp <= 2.0:
            port_score = 0.8
        elif implied_temp <= 2.5:
            port_score = 0.6
        elif implied_temp <= 3.0:
            port_score = 0.4
        else:
            port_score = 0.2

    # ── TNFD LEAP Scoring ────────────────────────────────────────────────────
    leap_stages_completed = tnfd_in.get("leap_stages_completed", [])
    max_leap = 4
    leap_score = len(leap_stages_completed) / max_leap
    sbtn_steps = len(tnfd_in.get("sbtn_steps_completed", []))
    sbtn_score = sbtn_steps / 5
    tnfd_score = round((leap_score + sbtn_score) / 2.0, 3)

    tnfd_result = {
        "leap_stages_completed": leap_stages_completed,
        "leap_completion_pct": round(len(leap_stages_completed) / max_leap * 100, 1),
        "sbtn_steps_completed": tnfd_in.get("sbtn_steps_completed", []),
        "sbtn_completion_pct": round(sbtn_steps / 5 * 100, 1),
        "nature_targets_set": tnfd_in.get("nature_targets_set", False),
        "tnfd_score": tnfd_score,
    }

    # ── Composite Score ──────────────────────────────────────────────────────
    # Weights: TPT 40%, SBTi 30%, RtZ 15%, Portfolio 10%, TNFD 5%
    composite = (
        tpt_weighted_sum * 0.40
        + sbti_total * 0.30
        + rtz_total * 0.15
        + port_score * 0.10
        + tnfd_score * 0.05
    )
    overall_tier = _get_quality_tier(composite)

    # ── Red Flags ────────────────────────────────────────────────────────────
    red_flags = _detect_red_flags(tpt_weighted_sum, sbti_total, rtz_total, tpt_in, sbti_in)

    # ── Sector Context ───────────────────────────────────────────────────────
    sector_context = {
        "sector": sector,
        "nace": sector_data.get("nace", "N/A"),
        "pathway_source": sector_data.get("pathway_source", "N/A"),
        "sector_2030_target_pct": sector_data.get("targets", {}).get(2030, "N/A"),
        "sector_2050_target_pct": sector_data.get("targets", {}).get(2050, "N/A"),
        "temperature_alignment_2c_pct": sector_data.get("temperature_alignment_2c", "N/A"),
        "temperature_alignment_15c_pct": sector_data.get("temperature_alignment_15c", "N/A"),
        "key_levers": sector_data.get("key_levers", []),
    }

    return {
        "entity_name": entity_name,
        "sector": sector,
        "overall_credibility_score": round(composite, 4),
        "overall_quality_tier": overall_tier,
        "overall_label": QUALITY_TIERS[overall_tier]["label"],
        "tpt_assessment": {
            "composite_score": round(tpt_weighted_sum, 4),
            "quality_tier": tpt_tier,
            "element_scores": tpt_element_scores,
        },
        "sbti_assessment": {
            "composite_score": round(sbti_total, 4),
            "quality_tier": sbti_tier,
            "criteria_scores": sbti_scores,
        },
        "race_to_zero_assessment": {
            "composite_score": round(rtz_total, 4),
            "quality_tier": rtz_tier,
            "criteria_scores": rtz_scores,
        },
        "portfolio_temperature": portfolio_temp_result or {
            "note": "No holdings provided; supply portfolio_inputs.holdings for temperature assessment."
        },
        "tnfd_nature_integration": tnfd_result,
        "red_flags": red_flags,
        "greenwash_risk": "HIGH" if len(red_flags) >= 2 else ("MEDIUM" if red_flags else "LOW"),
        "sector_context": sector_context,
        "membership_status": {
            c: rtz_in.get("memberships", {}).get(c, False)
            for c in RTZ_MEMBERSHIP_CATEGORIES
        },
    }


def calculate_portfolio_temperature(
    holdings: list[dict[str, Any]],
    engagement_coverage_pct: float | None = None,
    paris_aligned_pct: float | None = None,
) -> dict[str, Any]:
    """
    Calculate portfolio temperature alignment using WACI and implied temperature.

    holdings: list of {
        name: str, weight: float (sum to 1.0),
        tco2e: float, revenue_usd_mn: float,
        has_sbti: bool (optional), sbti_temperature: float (optional)
    }
    """
    if not holdings:
        return {"error": "No holdings provided."}

    total_weight = sum(h.get("weight", 0.0) for h in holdings)
    if total_weight <= 0:
        return {"error": "Holdings weights sum to zero."}

    # Normalise weights
    norm_holdings = [
        {**h, "weight": h.get("weight", 0.0) / total_weight}
        for h in holdings
    ]

    waci = _calculate_waci(norm_holdings)
    implied_temp = _implied_temperature(waci)

    # SBTi-weighted temperature (where available)
    sbti_holdings = [h for h in norm_holdings if h.get("has_sbti") and h.get("sbti_temperature")]
    sbti_weighted_temp: float | None = None
    if sbti_holdings:
        sbti_weighted_temp = round(
            sum(h["weight"] * h["sbti_temperature"] for h in sbti_holdings) /
            sum(h["weight"] for h in sbti_holdings), 2
        )

    # Engagement coverage
    engagement_cov = engagement_coverage_pct or (
        sum(h["weight"] for h in norm_holdings if h.get("has_sbti")) * 100.0
    )

    # Paris aligned (≤2°C)
    paris_aligned = paris_aligned_pct or (
        sum(h["weight"] for h in norm_holdings
            if h.get("sbti_temperature") and h["sbti_temperature"] <= 2.0) * 100.0
    )

    alignment_label = (
        "1.5°C Aligned" if implied_temp <= 1.5
        else ("Below 2°C" if implied_temp <= 2.0
              else ("2-3°C Pathway" if implied_temp <= 3.0
                    else "Above 3°C — Misaligned"))
    )

    return {
        "waci": waci,
        "waci_unit": WACI_UNIT,
        "implied_temperature_c": implied_temp,
        "sbti_weighted_temperature_c": sbti_weighted_temp,
        "alignment_label": alignment_label,
        "engagement_coverage_pct": round(engagement_cov, 1),
        "paris_aligned_holdings_pct": round(paris_aligned, 1),
        "holdings_count": len(holdings),
        "methodology": {
            "waci": "TCFD: Σ(weight_i × tCO2e_i / revenue_i_M)",
            "implied_temperature": "Simplified linear interpolation vs benchmark anchors (100 tCO2e/Mn=1.5°C; 300=2.5°C; 600=3.5°C)",
            "note": "Full PACTA / SBTi temperature score requires sector-specific SDA and portfolio-level trajectory analysis.",
        },
    }


def screen_transition_instrument(
    instrument_type: str,
    entity_name: str,
    sector: str,
    kpis: list[dict[str, Any]] | None = None,
    spts: list[dict[str, Any]] | None = None,
    has_transition_plan: bool = False,
    transition_plan_tier: str = "developing",
    sbti_status: str = "not_committed",
    use_of_proceeds_aligned: bool = False,
    external_reviewer: bool = False,
) -> dict[str, Any]:
    """
    Screen a transition finance instrument against applicable credibility criteria.

    instrument_type: transition_bond / sustainability_linked_loan / transition_loan_facility / blended_finance_transition
    """
    instrument_criteria = TRANSITION_INSTRUMENT_CRITERIA.get(instrument_type)
    if instrument_criteria is None:
        available = list(TRANSITION_INSTRUMENT_CRITERIA.keys())
        return {
            "error": f"Unknown instrument type '{instrument_type}'. Available: {available}"
        }

    kpis_list = kpis or []
    spts_list = spts or []

    checks: list[dict[str, Any]] = []
    score_sum = 0.0
    n_checks = 0

    # Common checks across instruments
    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0) -> None:
        nonlocal score_sum, n_checks
        s = weight if passed else 0.0
        checks.append({"check": name, "passed": passed, "score": s, "detail": detail})
        score_sum += s
        n_checks += weight

    # 1. Transition plan
    tier_scores = {"initial": 0.2, "developing": 0.5, "advanced": 0.7, "leading": 1.0}
    plan_score = tier_scores.get(transition_plan_tier.lower(), 0.2)
    add_check(
        "Credible Transition Plan",
        has_transition_plan and plan_score >= 0.5,
        f"Transition plan present: {has_transition_plan}; quality tier: {transition_plan_tier} ({plan_score:.1f}/1.0)",
        weight=2.0,
    )

    # 2. SBTi / validated targets
    sbti_ok = sbti_status in ("validated_near_term", "validated_net_zero")
    add_check(
        "Science-Based Targets",
        sbti_ok,
        f"SBTi status: {sbti_status}. Committed but not yet validated is acceptable only for SLLs.",
    )

    # 3. Instrument-specific checks
    if instrument_type == "transition_bond":
        add_check(
            "Use of Proceeds Alignment",
            use_of_proceeds_aligned,
            "Proceeds must fund eligible transition capex (decarbonisation activities)",
        )
        add_check(
            "Annual Impact Reporting",
            external_reviewer,
            "Annual reporting vs milestones required; external review recommended (ICMA Handbook 2023)",
        )
        eligible = sector in instrument_criteria.get("eligible_sectors", [])
        add_check(
            "Sector Eligibility (Transition Bond)",
            eligible,
            f"Sector '{sector}' {'is' if eligible else 'is NOT'} in ICMA transition-eligible hard-to-abate sectors.",
        )

    elif instrument_type == "sustainability_linked_loan":
        has_material_kpi = len(kpis_list) >= 1
        add_check(
            "Material KPI Identified",
            has_material_kpi,
            f"{len(kpis_list)} KPI(s) provided. LMA SLL Principles require ≥1 material sustainability KPI.",
        )
        has_ambitious_spt = any(
            s.get("ambitious", False) or s.get("reduction_pct", 0) >= 25 for s in spts_list
        )
        add_check(
            "Ambitious SPT Set",
            has_ambitious_spt,
            "SPT must be ambitious vs sector decarbonisation pathway (LMA SLL P2 Core Component).",
        )
        add_check(
            "External SPT Verification",
            external_reviewer,
            "Annual KPI verification by independent external reviewer required (LMA SLL P5).",
        )

    elif instrument_type == "transition_loan_facility":
        add_check(
            "Transition Plan Assessed",
            has_transition_plan and plan_score >= 0.5,
            "Third-party transition plan assessment required per LMA Transition Guidance 2023.",
        )
        sector_ok = sector in instrument_criteria.get("sector_pathways", [])
        add_check(
            "Defined Sector Pathway",
            sector_ok,
            f"LMA TLF defines 4 sector pathways. Sector '{sector}' {'matches' if sector_ok else 'does not match'}.",
        )
        add_check(
            "Third-Party Review",
            external_reviewer,
            "External review of transition alignment required.",
        )

    elif instrument_type == "blended_finance_transition":
        add_check(
            "Concessional Layer Present",
            True,  # assumed true for blended finance submission
            "Blended finance structure requires first-loss / concessional tranche.",
        )
        add_check(
            "Climate Additionality Demonstrated",
            has_transition_plan,
            "Climate additionality requires credible transition plan showing project would not proceed without concessional support.",
        )

    # Score
    composite = score_sum / n_checks if n_checks > 0 else 0.0
    tier = _get_quality_tier(composite)
    eligible = composite >= 0.60

    return {
        "instrument_type": instrument_type,
        "instrument_name": instrument_criteria["name"],
        "standard": instrument_criteria["standard"],
        "entity_name": entity_name,
        "sector": sector,
        "eligible": eligible,
        "composite_score": round(composite, 4),
        "quality_tier": tier,
        "checks": checks,
        "criteria_summary": instrument_criteria["criteria"],
        "recommendation": (
            f"Instrument meets credibility threshold for {instrument_criteria['name']}."
            if eligible else
            f"Instrument does NOT yet meet credibility threshold. Address failing checks to qualify."
        ),
    }


def get_transition_benchmarks() -> dict[str, Any]:
    """Return consolidated benchmark and reference data for transition finance analysis."""
    return {
        "tpt_elements": TPT_ELEMENTS,
        "quality_tiers": QUALITY_TIERS,
        "sbti_criteria": SBTI_CRITERIA,
        "race_to_zero_criteria": RACE_TO_ZERO_CRITERIA,
        "rtz_membership_categories": RTZ_MEMBERSHIP_CATEGORIES,
        "sector_pathways": SECTOR_PATHWAYS,
        "gfanz_expectations": GFANZ_EXPECTATIONS,
        "transition_instrument_criteria": TRANSITION_INSTRUMENT_CRITERIA,
        "waci_temperature_benchmarks": {
            "1.5c": {"waci_tco2e_usd_mn": IMPLIED_TEMP_15C_WACI},
            "2.5c": {"waci_tco2e_usd_mn": IMPLIED_TEMP_BASE_WACI},
            "3.5c": {"waci_tco2e_usd_mn": IMPLIED_TEMP_3C_WACI},
        },
        "credibility_composite_weights": {
            "tpt": 0.40,
            "sbti": 0.30,
            "race_to_zero": 0.15,
            "portfolio_temperature": 0.10,
            "tnfd_nature": 0.05,
        },
    }
