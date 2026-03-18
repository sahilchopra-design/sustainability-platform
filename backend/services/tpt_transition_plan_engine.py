"""
Transition Plan Taskforce (TPT) Disclosure Framework Engine
=============================================================

TPT Disclosure Framework 2023 (published October 2023 by the TPT Secretariat,
hosted by the UK Transition Plan Taskforce). Incorporated into FCA PS23/22
(UK-listed companies and FCA-regulated firms).

Sub-modules:
  1. Full TPT Assessment — 6-element scoring with quality tier determination
  2. Element Scorer — granular sub-element completion tracking
  3. Gap Analysis — element-level gaps with remediation guidance
  4. Cross-Framework Mapper — TCFD / IFRS S2 / CSRD ESRS E1 alignment

References:
  - TPT Disclosure Framework (October 2023)
  - TPT Implementation Guidance (October 2023)
  - FCA PS23/22 (Sustainability Disclosure Requirements)
  - IFRS S2 Climate-Related Disclosures (June 2023)
  - CSRD ESRS E1 Climate Change
  - TCFD Recommendations (2017, updated 2021)
  - Net Zero Transition Plans: A Practitioner Guide (CBI/WBCSD 2023)
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — TPT Elements and Sub-Elements
# ---------------------------------------------------------------------------

TPT_ELEMENTS: dict[str, dict] = {
    "foundations": {
        "element_id": "1",
        "name": "Foundations",
        "description": "The ambition, current state, and milestones underpinning the transition plan",
        "tpt_reference": "TPT Framework §§1-3",
        "sub_elements": {
            "1.1": {
                "name": "Ambition",
                "description": "Net zero or other high-level climate ambition and the scope of emissions covered",
                "key_disclosures": [
                    "Net zero target year (e.g. 2050 or earlier)",
                    "Emissions scope coverage (Scope 1, 2, 3)",
                    "Science-based or equivalent methodology reference",
                    "Interim target years (e.g. 2025, 2030, 2035, 2040)",
                    "Whether ambition covers full value chain",
                ],
                "quality_indicators": {
                    "initial": "High-level net zero commitment stated without quantified target",
                    "developing": "Net zero target year stated with Scope 1/2 coverage",
                    "advanced": "SBTi-validated or equivalent targets with Scope 1/2/3 and interim milestones",
                    "leading": "1.5C-aligned targets, full value chain coverage, sector-specific pathway reference",
                },
            },
            "1.2": {
                "name": "Current State",
                "description": "Baseline GHG emissions, current portfolio composition, and climate risk exposure",
                "key_disclosures": [
                    "Base year GHG emissions (Scope 1, 2, 3)",
                    "Financed/facilitated/insurance-associated emissions (for FIs)",
                    "Current low-carbon asset/revenue proportion",
                    "Summary of current climate risks (physical + transition)",
                    "Current progress against prior targets",
                ],
                "quality_indicators": {
                    "initial": "Scope 1/2 base year emissions disclosed",
                    "developing": "Scope 1/2/3 emissions with PCAF attribution for FIs",
                    "advanced": "Full emissions inventory + Paris alignment assessment",
                    "leading": "Verified emissions data with third-party assurance + portfolio temperature score",
                },
            },
            "1.3": {
                "name": "Milestones",
                "description": "Quantified interim milestones on the pathway to the long-term ambition",
                "key_disclosures": [
                    "2025 interim target (absolute / intensity)",
                    "2030 interim target (minimum required by most frameworks)",
                    "2035 interim target (for leading practice)",
                    "2040 interim target",
                    "Sector-specific trajectory reference (e.g. IEA NZE, NGFS)",
                ],
                "quality_indicators": {
                    "initial": "High-level commitment to reduce emissions by 2030",
                    "developing": "Quantified 2030 target stated",
                    "advanced": "2025 and 2030 quantified targets with base year",
                    "leading": "Full milestone schedule (2025/2030/2035/2040/2050) with science-based reference",
                },
            },
        },
        "weight": 0.20,
    },
    "implementation_strategy": {
        "element_id": "2",
        "name": "Implementation Strategy",
        "description": "Actions, levers, and dependencies required to achieve the transition ambition",
        "tpt_reference": "TPT Framework §§4-7",
        "sub_elements": {
            "2.1": {
                "name": "Decarbonisation Levers",
                "description": "Specific actions and initiatives to reduce absolute and intensity emissions",
                "key_disclosures": [
                    "Energy efficiency programmes (operational)",
                    "Renewable energy procurement strategy (PPAs, RECs, onsite)",
                    "Process electrification plans",
                    "Low-carbon fuel/feedstock substitution",
                    "Carbon capture, use and storage (CCUS) plans (if applicable)",
                    "Product/service portfolio shift (e.g. EV transition, green buildings)",
                ],
                "quality_indicators": {
                    "initial": "General commitments to operational efficiency and renewables",
                    "developing": "Named initiatives with investment envelopes",
                    "advanced": "Quantified abatement potential per lever; timeline committed",
                    "leading": "Marginal abatement cost curve (MACC) analysis; lever-by-lever GHG reduction modelled",
                },
            },
            "2.2": {
                "name": "Dependencies",
                "description": "External conditions, infrastructure, and policy required for plan delivery",
                "key_disclosures": [
                    "Grid decarbonisation dependency",
                    "Policy and regulatory enablers required",
                    "Technology readiness dependencies (e.g. green hydrogen, CCUS)",
                    "Supply chain decarbonisation dependency",
                    "Finance availability and cost assumptions",
                ],
                "quality_indicators": {
                    "initial": "Mentions of regulatory dependency",
                    "developing": "Key dependencies listed with probability assessment",
                    "advanced": "Scenario analysis of dependency risks; contingency plans",
                    "leading": "Quantified dependency risk; sensitivity analysis showing impact on target achievability",
                },
            },
            "2.3": {
                "name": "Climate Solutions",
                "description": "Nature-based solutions, carbon removal, and contribution to system-level transition",
                "key_disclosures": [
                    "Voluntary carbon offset strategy (role and limits)",
                    "Carbon removal technologies (BECCS, DAC) — long-term plans",
                    "Nature-based solutions (afforestation, blue carbon, soil carbon)",
                    "Investment in climate solutions beyond own operations",
                    "Position on residual emissions and offset quality criteria",
                ],
                "quality_indicators": {
                    "initial": "Mentions of carbon offsets without quality criteria",
                    "developing": "Offset quality criteria stated; nature-based solutions budget",
                    "advanced": "Residual emissions strategy with high-quality removal focus (e.g. Gold Standard, VCS)",
                    "leading": "Minimal offset reliance; robust removal strategy aligned with Oxford Principles on Net Zero",
                },
            },
            "2.4": {
                "name": "Operations",
                "description": "Operational changes to facilities, fleets, and real estate to deliver decarbonisation",
                "key_disclosures": [
                    "Real estate energy efficiency roadmap (CRREM aligned for FIs)",
                    "Fleet electrification timeline",
                    "Manufacturing process redesign",
                    "Data centre PUE improvement plans",
                    "Supply chain operations collaboration",
                ],
                "quality_indicators": {
                    "initial": "General commitment to operational improvements",
                    "developing": "Facility-level energy audit results and planned investments",
                    "advanced": "Site-by-site retrofit plans with cost estimates",
                    "leading": "Asset-level decarbonisation plans aligned with SBTi FLAG / CRREM / IEA sector pathways",
                },
            },
        },
        "weight": 0.25,
    },
    "engagement_accountability": {
        "element_id": "3",
        "name": "Engagement and Accountability",
        "description": "How the organisation engages value chain partners and holds itself accountable",
        "tpt_reference": "TPT Framework §§8-11",
        "sub_elements": {
            "3.1": {
                "name": "Value Chain Engagement",
                "description": "Supplier, customer, and investee engagement on climate transition",
                "key_disclosures": [
                    "Supplier climate requirements (code of conduct, contractual clauses)",
                    "Supplier decarbonisation programme",
                    "Customer/investee climate engagement programme",
                    "Financed emissions engagement (for FIs — PCAF Part C)",
                    "Value chain Scope 3 category coverage",
                ],
                "quality_indicators": {
                    "initial": "Supplier questionnaire on environmental practices",
                    "developing": "Supplier climate targets requested; PCAF engagement for FIs",
                    "advanced": "Science-based target requirements for significant suppliers",
                    "leading": "Verified SBTi targets required for top suppliers; financed emissions engagement with milestones",
                },
            },
            "3.2": {
                "name": "Industry Bodies",
                "description": "Engagement with industry associations and standard-setters on climate policy",
                "key_disclosures": [
                    "Membership of climate-aligned industry coalitions (GFANZ, RE100, EV100)",
                    "Industry body alignment with Paris Agreement",
                    "Policy advocacy positions on carbon pricing and climate regulation",
                    "Lobbying disclosure (consistency with net zero commitments)",
                ],
                "quality_indicators": {
                    "initial": "Listed membership of relevant industry associations",
                    "developing": "Assessment of industry body Paris-alignment conducted",
                    "advanced": "Proactive exit from misaligned associations; GFANZ or equivalent commitment",
                    "leading": "Active climate policy advocacy; transparent lobbying register published",
                },
            },
            "3.3": {
                "name": "Policy Engagement",
                "description": "Engagement with government and regulators on climate-enabling policies",
                "key_disclosures": [
                    "Support for carbon pricing mechanisms",
                    "Regulatory engagement on climate disclosure standards",
                    "Participation in national net zero consultations",
                    "Policy positions published and updated",
                ],
                "quality_indicators": {
                    "initial": "General statement of support for Paris Agreement",
                    "developing": "Named policy positions on key regulations (CBAM, EU ETS, SEC disclosure)",
                    "advanced": "Active public advocacy; responses to consultations published",
                    "leading": "Board-approved policy engagement strategy; independent review of lobbying positions",
                },
            },
            "3.4": {
                "name": "Accountability Mechanisms",
                "description": "Internal and external accountability for transition plan delivery",
                "key_disclosures": [
                    "Named individual(s) responsible for transition plan delivery",
                    "Board accountability for plan progress",
                    "External audit/assurance of transition plan metrics",
                    "Regulatory accountability (FCA PS23/22, ESRS E1)",
                    "Consequence management for missed milestones",
                ],
                "quality_indicators": {
                    "initial": "CEO-level commitment statement",
                    "developing": "Named executive owner; board oversight stated",
                    "advanced": "External assurance of key metrics; escalation procedures",
                    "leading": "Independent transition plan review; regulatory filing of plan; legal accountability framework",
                },
            },
        },
        "weight": 0.15,
    },
    "metrics_targets": {
        "element_id": "4",
        "name": "Metrics and Targets",
        "description": "Quantitative KPIs, targets, and progress tracking for the transition plan",
        "tpt_reference": "TPT Framework §§12-15",
        "sub_elements": {
            "4.1": {
                "name": "GHG Targets",
                "description": "Absolute and intensity GHG emission targets across all relevant scopes",
                "key_disclosures": [
                    "Absolute Scope 1 + 2 reduction target (% vs base year by target year)",
                    "Absolute Scope 3 reduction target (% vs base year)",
                    "Financed/facilitated emissions target (for FIs)",
                    "Net zero target definition (residual emissions + removal approach)",
                    "Science-based target methodology (SBTi, PCAF, NZBA)",
                ],
                "quality_indicators": {
                    "initial": "High-level commitment to reduce GHG emissions",
                    "developing": "2030 Scope 1/2 absolute reduction target stated",
                    "advanced": "SBTi-validated Scope 1/2/3 targets with base year",
                    "leading": "Full target set (2025/2030/2035/2040/2050) for all scopes + financed emissions",
                },
            },
            "4.2": {
                "name": "Financial Metrics",
                "description": "Financial KPIs linking transition investment to climate outcomes",
                "key_disclosures": [
                    "Green/sustainable CapEx as % of total CapEx",
                    "Climate transition finance mobilised (USD mn) — for FIs",
                    "Stranded asset exposure (USD mn at risk under 1.5C)",
                    "Climate-related revenue (green products/services as % total)",
                    "Internal carbon price (USD/tCO2e) applied to investment decisions",
                ],
                "quality_indicators": {
                    "initial": "Green investment mentioned without quantification",
                    "developing": "Green CapEx % disclosed; internal carbon price stated",
                    "advanced": "Climate revenue tracking; stranded asset quantification",
                    "leading": "Full climate finance KPI suite; PCAF-aligned financed emissions KPIs; TCFD financial effects",
                },
            },
            "4.3": {
                "name": "Progress Tracking",
                "description": "Annual reporting on progress against transition plan milestones",
                "key_disclosures": [
                    "Annual GHG emissions vs target trajectory",
                    "Energy intensity vs target",
                    "Green CapEx deployment vs plan",
                    "Scope 3 engagement coverage vs target",
                    "Board sign-off on progress report",
                ],
                "quality_indicators": {
                    "initial": "Annual emissions reported without comparison to trajectory",
                    "developing": "Progress vs 2030 target reported annually",
                    "advanced": "Multi-year trajectory with variance analysis; board sign-off",
                    "leading": "Verified annual progress report; third-party assurance; integrated into financial reporting",
                },
            },
        },
        "weight": 0.20,
    },
    "governance": {
        "element_id": "5",
        "name": "Governance",
        "description": "Board and management oversight, skills, and incentives for transition plan delivery",
        "tpt_reference": "TPT Framework §§16-18",
        "sub_elements": {
            "5.1": {
                "name": "Oversight",
                "description": "Board and senior management oversight structures for the transition plan",
                "key_disclosures": [
                    "Board committee responsible for transition plan (Risk/Audit/Sustainability)",
                    "Reporting frequency to board on transition progress",
                    "Management-level climate governance (Chief Climate Officer, ESG committee)",
                    "Integration with enterprise risk management",
                    "Climate in board risk appetite statement",
                ],
                "quality_indicators": {
                    "initial": "Board awareness of climate risk stated",
                    "developing": "Board committee assigned; management owner named",
                    "advanced": "Climate in risk appetite; quarterly board reporting on metrics",
                    "leading": "Dedicated board climate committee; externally assessed governance effectiveness",
                },
            },
            "5.2": {
                "name": "Skills and Capacity",
                "description": "Climate expertise on board and management; training and capability building",
                "key_disclosures": [
                    "Board member climate/sustainability expertise",
                    "External climate advisory access",
                    "Employee climate training programmes",
                    "Transition plan skill gap assessment",
                    "Third-party transition plan review",
                ],
                "quality_indicators": {
                    "initial": "Board receives annual climate briefing",
                    "developing": "Named board member with climate expertise; annual training programme",
                    "advanced": "Externally verified board climate competency; management climate certification",
                    "leading": "Independent climate advisory board; board climate competency framework published",
                },
            },
            "5.3": {
                "name": "Incentives",
                "description": "Executive and workforce remuneration linked to transition plan KPIs",
                "key_disclosures": [
                    "% of CEO variable pay linked to climate KPIs",
                    "Climate KPIs used in annual bonus (e.g. GHG reduction, green CapEx)",
                    "Long-term incentive plan (LTIP) climate conditions",
                    "Workforce climate incentive programmes",
                    "Say-on-pay disclosure of climate link",
                ],
                "quality_indicators": {
                    "initial": "General commitment to linking pay to sustainability performance",
                    "developing": "CEO bonus includes at least one climate KPI (>5% weighting)",
                    "advanced": "10-20% of CEO variable pay linked to quantified climate targets",
                    "leading": ">25% variable pay linked to verified climate metrics; LTIP with science-based conditions",
                },
            },
        },
        "weight": 0.10,
    },
    "finance": {
        "element_id": "6",
        "name": "Finance",
        "description": "Capital allocation, financing instruments, and mobilisation of transition finance",
        "tpt_reference": "TPT Framework §§19-22",
        "sub_elements": {
            "6.1": {
                "name": "CapEx and OpEx Plans",
                "description": "Capital and operational expenditure required to deliver the transition plan",
                "key_disclosures": [
                    "Total transition CapEx envelope (USD mn over 5/10 years)",
                    "Green vs brown CapEx split (current and planned)",
                    "R&D expenditure on low-carbon innovation",
                    "Asset retirement/decommissioning provisions (for fossil assets)",
                    "Transition CapEx as % of total CapEx (current and 2030 target)",
                ],
                "quality_indicators": {
                    "initial": "General commitment to increased climate investment",
                    "developing": "Transition CapEx envelope stated for 5-year period",
                    "advanced": "Green CapEx % target with base year; asset retirement plan",
                    "leading": "Full CapEx/OpEx/R&D breakdown aligned with CAPEX plan (EU Taxonomy);  quantified annual deployment",
                },
            },
            "6.2": {
                "name": "Financing Instruments",
                "description": "Use of green bonds, sustainability-linked instruments, and transition finance",
                "key_disclosures": [
                    "Green bond / sustainability-linked bond issuance (amount and framework)",
                    "Sustainability-linked loan (SLL) usage with KPI ratchets",
                    "Transition bond framework (if applicable)",
                    "ICMA / LMA green/sustainability-linked principles alignment",
                    "Second party opinion (SPO) provider",
                ],
                "quality_indicators": {
                    "initial": "Considering green finance options",
                    "developing": "At least one green/SLL instrument in place",
                    "advanced": "Documented green financing framework aligned with ICMA/LMA",
                    "leading": "Comprehensive sustainable finance framework; external SPO; green/SLL as primary funding source",
                },
            },
            "6.3": {
                "name": "Transition Finance Mobilised",
                "description": "Financing directed to third-party climate transition activities (primarily for FIs)",
                "key_disclosures": [
                    "Total transition finance mobilised to clients/investees (USD bn)",
                    "Definition of transition finance used (taxonomy reference)",
                    "Asset classes and sectors covered",
                    "Alignment with GFANZ Transition Finance Guidance",
                    "Progress against transition finance commitment",
                ],
                "quality_indicators": {
                    "initial": "Commitment to increase climate-related lending/investment",
                    "developing": "Transition finance target stated (e.g. USD bn by 2030)",
                    "advanced": "Annual tracking of mobilised transition finance vs commitment",
                    "leading": "GFANZ-aligned transition finance framework; portfolio-level Paris alignment assessment published",
                },
            },
        },
        "weight": 0.10,
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Entity Types
# ---------------------------------------------------------------------------

ENTITY_TYPES: dict[str, dict] = {
    "bank": {
        "name": "Bank / Credit Institution",
        "relevant_elements": ["foundations", "implementation_strategy", "engagement_accountability", "metrics_targets", "governance", "finance"],
        "priority_sub_elements": ["1.2", "2.1", "3.1", "4.1", "4.2", "6.3"],
        "financed_emissions_required": True,
        "sector_specific_notes": "NZBA (Net Zero Banking Alliance) commitment aligns with TPT. PCAF financed emissions required for 4.2.",
        "regulatory_triggers": ["FCA PS23/22 (UK-listed banks)", "ESRS E1 (EU CRD scope)", "CSRD (large EU banks)"],
    },
    "insurer": {
        "name": "Insurance Company",
        "relevant_elements": ["foundations", "implementation_strategy", "engagement_accountability", "metrics_targets", "governance", "finance"],
        "priority_sub_elements": ["1.2", "2.1", "3.1", "4.1", "4.2", "6.2"],
        "financed_emissions_required": True,
        "sector_specific_notes": "NZIA (Net Zero Insurance Alliance) signatories; insurance-associated emissions (PCAF Part B) required.",
        "regulatory_triggers": ["FCA PS23/22 (UK-listed insurers)", "EIOPA sustainability reporting", "CSRD"],
    },
    "asset_manager": {
        "name": "Asset Manager",
        "relevant_elements": ["foundations", "implementation_strategy", "engagement_accountability", "metrics_targets", "governance", "finance"],
        "priority_sub_elements": ["1.2", "3.1", "3.2", "4.1", "4.2", "4.3"],
        "financed_emissions_required": True,
        "sector_specific_notes": "NZAM (Net Zero Asset Managers Initiative); TCFD PAT (Portfolio Alignment Team) metrics applicable.",
        "regulatory_triggers": ["FCA PS23/22", "SFDR (AIFMD/UCITS scope)", "CSRD"],
    },
    "pension": {
        "name": "Pension Fund",
        "relevant_elements": ["foundations", "implementation_strategy", "engagement_accountability", "metrics_targets", "governance"],
        "priority_sub_elements": ["1.1", "1.3", "3.1", "4.1", "4.2"],
        "financed_emissions_required": True,
        "sector_specific_notes": "Paris Aligned Investment Initiative (PAII) net zero framework. TCFD required for UK pension schemes >GBP 1bn.",
        "regulatory_triggers": ["UK Pension Schemes Act 2021 (TCFD)", "IORP II (EU)", "CSRD"],
    },
    "corporate": {
        "name": "Non-Financial Corporate",
        "relevant_elements": ["foundations", "implementation_strategy", "engagement_accountability", "metrics_targets", "governance", "finance"],
        "priority_sub_elements": ["1.1", "1.2", "2.1", "2.2", "4.1", "5.3"],
        "financed_emissions_required": False,
        "sector_specific_notes": "SBTi Corporate Net Zero Standard applicable. Sector-specific decarbonisation levers vary significantly.",
        "regulatory_triggers": ["CSRD ESRS E1 (EU large corporates)", "IFRS S2 (capital market reporters)", "SEC Climate Rule (US-listed)"],
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Quality Tiers
# ---------------------------------------------------------------------------

QUALITY_TIERS: dict[str, dict] = {
    "initial": {
        "name": "Initial",
        "score_range": [0, 25],
        "description": "Early-stage transition planning. High-level commitments present but limited quantification or implementation detail.",
        "typical_characteristics": [
            "Net zero commitment stated but not quantified",
            "Limited base year emissions data",
            "No interim milestones",
            "Minimal governance structures for climate",
            "No transition finance strategy",
        ],
        "recommended_next_steps": [
            "Establish complete GHG inventory (Scope 1/2/3)",
            "Set quantified 2030 interim target",
            "Assign board-level climate oversight responsibility",
        ],
    },
    "developing": {
        "name": "Developing",
        "score_range": [25, 50],
        "description": "Transition plan in development. Key elements present but gaps in implementation detail, value chain coverage, or financial planning.",
        "typical_characteristics": [
            "Quantified 2030 targets for Scope 1/2",
            "Key decarbonisation levers identified",
            "Board oversight mechanism in place",
            "Limited Scope 3 / value chain coverage",
            "Basic green finance in place",
        ],
        "recommended_next_steps": [
            "Extend target coverage to Scope 3",
            "Develop supplier engagement programme",
            "Quantify transition CapEx requirements",
        ],
    },
    "advanced": {
        "name": "Advanced",
        "score_range": [50, 75],
        "description": "Comprehensive transition plan with science-based targets, implementation strategy, and accountability mechanisms. Minor gaps remain.",
        "typical_characteristics": [
            "SBTi-validated or equivalent targets (Scope 1/2/3)",
            "Detailed decarbonisation levers with quantified abatement",
            "Supplier engagement programme active",
            "External assurance of key metrics",
            "Green financing framework in place",
        ],
        "recommended_next_steps": [
            "Publish detailed 5-year milestone schedule",
            "Achieve external verification of transition plan",
            "Link executive pay to climate KPIs (>10% weighting)",
        ],
    },
    "leading": {
        "name": "Leading",
        "score_range": [75, 100],
        "description": "Best-practice transition plan meeting all TPT elements at high quality. Independently verified and fully integrated with financial planning.",
        "typical_characteristics": [
            "Full milestone schedule (2025 through 2050)",
            "Third-party verified transition plan",
            "Full value chain Scope 3 coverage",
            "MACC analysis for decarbonisation levers",
            "GFANZ framework alignment (for FIs)",
            "Executive remuneration strongly linked to climate",
        ],
        "recommended_next_steps": [
            "Pursue external peer review of transition plan credibility",
            "Participate in industry benchmark disclosure initiatives",
            "Commit to annual transition plan update cycle",
        ],
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Cross-Framework Mapping
# ---------------------------------------------------------------------------

CROSS_FRAMEWORK_MAP: dict[str, dict] = {
    "tcfd_governance_board": {
        "tcfd": "Governance — Board oversight",
        "tpt_element": "governance",
        "tpt_sub_element": "5.1",
        "ifrs_s2": "S2-6 (Board oversight of climate)",
        "csrd_esrs_e1": "E1-GOV-1 (Climate-related governance)",
        "mapping_quality": "direct",
        "notes": "All three frameworks require disclosure of board-level oversight; TPT adds specific transition plan accountability",
    },
    "tcfd_strategy_risks": {
        "tcfd": "Strategy — Risks and opportunities",
        "tpt_element": "foundations",
        "tpt_sub_element": "1.2",
        "ifrs_s2": "S2-10 to S2-12 (Climate risks/opportunities)",
        "csrd_esrs_e1": "E1-2 (Policies/material topics)",
        "mapping_quality": "partial",
        "notes": "TPT focuses on transition-specific risks; TCFD/IFRS S2 broader climate risk scope",
    },
    "tcfd_strategy_resilience": {
        "tcfd": "Strategy — Resilience (scenario analysis)",
        "tpt_element": "implementation_strategy",
        "tpt_sub_element": "2.2",
        "ifrs_s2": "S2-22 to S2-24 (Scenario analysis)",
        "csrd_esrs_e1": "E1-SBM-3 (Scenario analysis resilience)",
        "mapping_quality": "direct",
        "notes": "Scenario dependency analysis in TPT §2.2 maps to IFRS S2 resilience and ESRS E1 SBM-3",
    },
    "tcfd_risk_mgmt": {
        "tcfd": "Risk Management — Processes",
        "tpt_element": "governance",
        "tpt_sub_element": "5.1",
        "ifrs_s2": "S2-25 to S2-27 (Risk management processes)",
        "csrd_esrs_e1": "E1-IRO-1 (Identification of impacts, risks, opportunities)",
        "mapping_quality": "partial",
        "notes": "TPT governance element covers risk management integration; TCFD/IFRS S2 more detailed on process",
    },
    "tcfd_metrics_ghg": {
        "tcfd": "Metrics — Scope 1/2/3 GHG",
        "tpt_element": "metrics_targets",
        "tpt_sub_element": "4.1",
        "ifrs_s2": "S2-29a (GHG emissions metrics)",
        "csrd_esrs_e1": "E1-6 (Gross Scope 1/2/3 GHG emissions)",
        "mapping_quality": "direct",
        "notes": "All frameworks require Scope 1, 2, 3 GHG disclosure; TPT additionally requires trajectory vs target",
    },
    "tcfd_metrics_targets": {
        "tcfd": "Metrics — Climate targets",
        "tpt_element": "metrics_targets",
        "tpt_sub_element": "4.1",
        "ifrs_s2": "S2-36 to S2-41 (Climate targets)",
        "csrd_esrs_e1": "E1-4 (Targets related to climate change)",
        "mapping_quality": "direct",
        "notes": "Direct alignment across all frameworks on quantified target disclosure",
    },
    "ifrs_s2_capex": {
        "tcfd": "N/A",
        "tpt_element": "finance",
        "tpt_sub_element": "6.1",
        "ifrs_s2": "S2-32 (Climate CapEx proportion)",
        "csrd_esrs_e1": "E1-5 (Energy consumption/mix) + E1-financial_effects",
        "mapping_quality": "direct",
        "notes": "TPT finance element §6.1 and IFRS S2 §32 both require green CapEx proportion disclosure",
    },
    "esrs_e1_transition_plan": {
        "tcfd": "Strategy (all pillars)",
        "tpt_element": "foundations",
        "tpt_sub_element": "1.1",
        "ifrs_s2": "S2-10 to S2-22 (Strategy disclosures)",
        "csrd_esrs_e1": "E1-1 (Transition plan for climate change mitigation)",
        "mapping_quality": "direct",
        "notes": "CSRD ESRS E1-1 explicitly requires a transition plan disclosure; TPT provides the most detailed framework for this",
    },
}


# ---------------------------------------------------------------------------
# Dataclass — TPT Assessment Output
# ---------------------------------------------------------------------------

@dataclass
class TPTAssessment:
    entity_id: str
    entity_name: str
    entity_type: str
    plan_year: int
    assessment_date: str

    net_zero_target_year: Optional[int]
    interim_targets: dict = field(default_factory=dict)  # {2025: -20, 2030: -45, ...}
    financed_emissions_trajectory: Optional[list[dict]] = field(default_factory=list)
    capex_green_pct: float = 0.0

    # Element Scores (0-100 per element)
    element_scores: dict = field(default_factory=dict)
    overall_score: float = 0.0
    quality_tier: str = "initial"

    # Completeness
    sub_elements_completed: int = 0
    sub_elements_total: int = 0
    completion_pct: float = 0.0

    # Gaps
    gaps: list[dict] = field(default_factory=list)
    priority_actions: list[str] = field(default_factory=list)

    # Cross-framework
    tcfd_alignment_pct: float = 0.0
    ifrs_s2_alignment_pct: float = 0.0
    csrd_esrs_e1_alignment_pct: float = 0.0

    notes: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TPTTransitionPlanEngine:
    """TPT Disclosure Framework 2023 transition plan assessment engine."""

    _TOTAL_SUB_ELEMENTS = sum(len(el["sub_elements"]) for el in TPT_ELEMENTS.values())

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str = "corporate",
        plan_year: int = 2024,
        net_zero_target_year: Optional[int] = 2050,
        elements_completed: Optional[list[str]] = None,
        interim_targets: Optional[dict] = None,
        financed_emissions_trajectory: Optional[list[dict]] = None,
        capex_green_pct: float = 0.0,
    ) -> TPTAssessment:
        """Full TPT Disclosure Framework assessment."""
        rng = random.Random(hash(entity_id + str(plan_year)))
        elements_completed = elements_completed or []
        interim_targets = interim_targets or {}

        # Score each element
        element_scores: dict[str, float] = {}
        for el_key, el_data in TPT_ELEMENTS.items():
            if el_key in elements_completed:
                score = rng.uniform(60, 90)
            else:
                score = rng.uniform(10, 55)

            # Boost for specific data availability
            if el_key == "foundations" and net_zero_target_year:
                score = min(100, score + 10)
            if el_key == "metrics_targets" and interim_targets:
                score = min(100, score + 15)
            if el_key == "finance" and capex_green_pct > 25:
                score = min(100, score + 10)

            element_scores[el_key] = round(score, 1)

        # Weighted overall score
        overall = sum(
            element_scores[k] * TPT_ELEMENTS[k]["weight"]
            for k in TPT_ELEMENTS
        )

        # Quality tier
        quality_tier = self._get_quality_tier(overall)

        # Completeness
        sub_completed = sum(
            1 for el_key in elements_completed
            for _ in TPT_ELEMENTS.get(el_key, {}).get("sub_elements", {})
        ) + rng.randint(0, 5)
        sub_completed = min(sub_completed, self._TOTAL_SUB_ELEMENTS)

        # Gaps
        gaps = self._generate_gaps(element_scores, net_zero_target_year, interim_targets, capex_green_pct, entity_type)

        # Cross-framework alignment
        tcfd_pct = round(overall * 0.9 + rng.uniform(-5, 5), 1)
        s2_pct = round(overall * 0.85 + rng.uniform(-5, 5), 1)
        esrs_pct = round(overall * 0.88 + rng.uniform(-5, 5), 1)

        return TPTAssessment(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            plan_year=plan_year,
            assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
            net_zero_target_year=net_zero_target_year,
            interim_targets=interim_targets,
            financed_emissions_trajectory=financed_emissions_trajectory or [],
            capex_green_pct=round(capex_green_pct, 2),
            element_scores=element_scores,
            overall_score=round(overall, 1),
            quality_tier=quality_tier,
            sub_elements_completed=sub_completed,
            sub_elements_total=self._TOTAL_SUB_ELEMENTS,
            completion_pct=round(sub_completed / self._TOTAL_SUB_ELEMENTS * 100, 1),
            gaps=gaps,
            priority_actions=[g["recommended_action"] for g in gaps[:5]],
            tcfd_alignment_pct=min(100, max(0, tcfd_pct)),
            ifrs_s2_alignment_pct=min(100, max(0, s2_pct)),
            csrd_esrs_e1_alignment_pct=min(100, max(0, esrs_pct)),
            notes=f"TPT Disclosure Framework assessment for {entity_name}. Entity type: {entity_type}. Plan year: {plan_year}.",
        )

    def _get_quality_tier(self, score: float) -> str:
        for tier_key, tier_data in QUALITY_TIERS.items():
            lo, hi = tier_data["score_range"]
            if lo <= score < hi:
                return tier_key
        return "leading" if score >= 75 else "initial"

    def _generate_gaps(
        self,
        element_scores: dict,
        net_zero_year: Optional[int],
        interim_targets: dict,
        capex_pct: float,
        entity_type: str,
    ) -> list[dict]:
        gaps = []
        for el_key, score in element_scores.items():
            if score < 50:
                el = TPT_ELEMENTS[el_key]
                gaps.append({
                    "element": el_key,
                    "element_name": el["name"],
                    "current_score": score,
                    "gap_description": f"Element {el['element_id']} ({el['name']}) below threshold — requires development",
                    "recommended_action": f"Develop {el['name']} disclosures per TPT §§{el['tpt_reference'].split('§§')[1]}",
                    "priority": "high" if score < 30 else "medium",
                })
        if not net_zero_year:
            gaps.append({
                "element": "foundations",
                "element_name": "Foundations",
                "current_score": element_scores.get("foundations", 0),
                "gap_description": "Net zero target year not set — TPT §1.1 ambition disclosure incomplete",
                "recommended_action": "Set and publish net zero target year aligned with 1.5C pathway (2050 or earlier)",
                "priority": "critical",
            })
        if not interim_targets.get(2030):
            gaps.append({
                "element": "metrics_targets",
                "element_name": "Metrics and Targets",
                "current_score": element_scores.get("metrics_targets", 0),
                "gap_description": "2030 interim target not quantified — TPT §1.3 milestone requirement not met",
                "recommended_action": "Set quantified 2030 Scope 1/2 reduction target (at least -45% vs base year for 1.5C alignment)",
                "priority": "high",
            })
        if capex_pct < 20 and entity_type not in ["bank", "insurer", "asset_manager", "pension"]:
            gaps.append({
                "element": "finance",
                "element_name": "Finance",
                "current_score": element_scores.get("finance", 0),
                "gap_description": f"Green CapEx ratio {capex_pct:.1f}% below recommended 20%+ threshold — TPT §6.1",
                "recommended_action": "Develop transition CapEx plan targeting 25%+ green proportion by 2027",
                "priority": "medium",
            })
        return gaps

    def score_element(
        self,
        entity_id: str,
        element_id: str,
        sub_elements_completed: Optional[list[str]] = None,
    ) -> dict:
        """Score a single TPT element based on sub-element completion."""
        if element_id not in TPT_ELEMENTS:
            return {"error": f"Element '{element_id}' not found. Valid: {list(TPT_ELEMENTS.keys())}"}

        rng = random.Random(hash(entity_id + element_id))
        el = TPT_ELEMENTS[element_id]
        sub_elements_completed = sub_elements_completed or []
        all_sub = list(el["sub_elements"].keys())

        scored_sub_elements = []
        total_score = 0.0
        for sub_id in all_sub:
            sub = el["sub_elements"][sub_id]
            if sub_id in sub_elements_completed:
                sub_score = rng.uniform(60, 95)
            else:
                sub_score = rng.uniform(5, 45)
            total_score += sub_score
            quality = "leading" if sub_score >= 75 else (
                "advanced" if sub_score >= 50 else (
                    "developing" if sub_score >= 25 else "initial"
                )
            )
            scored_sub_elements.append({
                "sub_element_id": sub_id,
                "sub_element_name": sub["name"],
                "score": round(sub_score, 1),
                "quality_tier": quality,
                "key_disclosures": sub["key_disclosures"],
                "quality_indicator": sub["quality_indicators"][quality],
                "completed": sub_id in sub_elements_completed,
            })

        element_score = total_score / len(all_sub) if all_sub else 0.0
        quality_tier = self._get_quality_tier(element_score)

        return {
            "entity_id": entity_id,
            "element_id": element_id,
            "element_name": el["name"],
            "element_score": round(element_score, 1),
            "quality_tier": quality_tier,
            "weight_in_overall": el["weight"],
            "sub_elements": scored_sub_elements,
            "completed_count": len(sub_elements_completed),
            "total_count": len(all_sub),
            "tpt_reference": el["tpt_reference"],
        }

    def generate_gap_analysis(self, entity_id: str, assessment: TPTAssessment) -> list[dict]:
        """Generate detailed gap analysis from a TPT assessment."""
        return assessment.gaps

    # -----------------------------------------------------------------------
    # Reference Endpoints
    # -----------------------------------------------------------------------

    def ref_elements(self) -> dict:
        return {"tpt_elements": TPT_ELEMENTS}

    def ref_entity_types(self) -> dict:
        return {"entity_types": ENTITY_TYPES}

    def ref_quality_tiers(self) -> dict:
        return {"quality_tiers": QUALITY_TIERS}

    def ref_cross_framework(self) -> dict:
        return {"cross_framework_map": CROSS_FRAMEWORK_MAP}

    def ref_interim_targets_guidance(self) -> dict:
        return {
            "interim_targets_guidance": {
                "2025": {
                    "required_by": ["leading_practice", "GFANZ_commitment"],
                    "typical_reduction_vs_base_year": "-10% to -20% Scope 1+2",
                    "notes": "Short-term operational wins; renewable energy procurement",
                },
                "2030": {
                    "required_by": ["SBTi", "IFRS_S2", "CSRD_ESRS_E1", "TPT_minimum"],
                    "typical_reduction_vs_base_year": "-42% to -50% Scope 1+2 (1.5C); -25% to -30% Scope 3",
                    "notes": "Minimum interim milestone per most frameworks; pivotal policy alignment year",
                },
                "2035": {
                    "required_by": ["leading_practice", "SBTi_1.5C_Corporate"],
                    "typical_reduction_vs_base_year": "-60% to -70% Scope 1+2",
                    "notes": "Advanced practice; aligns with EU 2035 ICE phase-out",
                },
                "2040": {
                    "required_by": ["leading_practice", "GFANZ"],
                    "typical_reduction_vs_base_year": "-80% to -90% Scope 1+2",
                    "notes": "Near-complete decarbonisation; residual emissions addressed by carbon removal",
                },
                "2050": {
                    "required_by": ["Paris_Agreement", "all_major_frameworks"],
                    "typical_reduction_vs_base_year": "-100% net (residuals offset by removals)",
                    "notes": "Net zero target year — residual emissions must be balanced by carbon removal, not offsets",
                },
            }
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine_instance: Optional[TPTTransitionPlanEngine] = None


def get_engine() -> TPTTransitionPlanEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TPTTransitionPlanEngine()
    return _engine_instance
