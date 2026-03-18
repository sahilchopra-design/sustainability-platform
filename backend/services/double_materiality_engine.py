"""
CSRD Double Materiality Assessment Engine (E102)
=================================================
Full ESRS 1 double materiality process — impact materiality + financial materiality — IRO identification.

Sub-modules:
  1. Double Materiality Assessment  — impact + financial scoring per all 10 ESRS topics
  2. IRO Identification             — structured IRO scoring for a single ESRS topic
  3. Materiality Matrix             — 2D plot data with quadrant classification
  4. ESRS Omission Checker          — validates omission justifications (ESRS 1 paras 31-35)
  5. Completeness Scoring           — mandatory DP coverage percentage
  6. Reference Data                 — ESRS topics, NACE triggers, IRO types, CSRD timeline

References:
  - ESRS 1 General Requirements (EFRAG, delegated act July 2023)
  - ESRS 1 Appendix B — List of ESRS Data Points
  - EFRAG IG 1 — Materiality Assessment Implementation Guidance (Dec 2023)
  - EFRAG Double Materiality Conceptual Guidelines (March 2023)
  - CSRD Directive (EU) 2022/2464
  - Delegated Regulation (EU) 2023/2772 (ESRS set 1)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Reference Data — ESRS Topics & Sub-Topics
# 10 topics with 55 sub-topics total
# ---------------------------------------------------------------------------

ESRS_TOPICS: Dict[str, Dict] = {
    "E1": {
        "name": "Climate Change",
        "pillar": "Environmental",
        "standard": "ESRS E1",
        "sub_topics": {
            "E1.1": {
                "name": "Climate change adaptation",
                "dp_reference": "E1-1",
                "ig3_note": "IG 3.E1.1 — Physical risk adaptation plans and capital allocation",
                "mandatory": True,
                "sector_applicability": ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["physical_risk", "transition_risk", "opportunity"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E1.2": {
                "name": "Climate change mitigation",
                "dp_reference": "E1-4",
                "ig3_note": "IG 3.E1.2 — GHG reduction targets, transition plan scope and ambition",
                "mandatory": True,
                "sector_applicability": ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "E1.3": {
                "name": "Energy",
                "dp_reference": "E1-5",
                "ig3_note": "IG 3.E1.3 — Energy consumption, mix (renewable/fossil), and intensity",
                "mandatory": True,
                "sector_applicability": ["B", "C", "D", "E", "F", "G", "H", "I"],
                "iro_types": ["actual_negative_impact", "transition_risk", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "E1.4": {
                "name": "Scope 1, 2 and 3 GHG emissions",
                "dp_reference": "E1-6",
                "ig3_note": "IG 3.E1.4 — GHG inventory per GHG Protocol; PCAF for FIs; Scope 3 C1-C15",
                "mandatory": True,
                "sector_applicability": ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "E1.5": {
                "name": "Climate-related physical risks",
                "dp_reference": "E1-9",
                "ig3_note": "IG 3.E1.5 — Acute and chronic physical risk exposure; NGFS scenarios",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["physical_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E1.6": {
                "name": "Climate-related transition risks and opportunities",
                "dp_reference": "E1-9",
                "ig3_note": "IG 3.E1.6 — Policy, legal, technology, market, reputational transition risks",
                "mandatory": False,
                "sector_applicability": ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K"],
                "iro_types": ["transition_risk", "opportunity"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
        },
    },
    "E2": {
        "name": "Pollution",
        "pillar": "Environmental",
        "standard": "ESRS E2",
        "sub_topics": {
            "E2.1": {
                "name": "Pollution of air",
                "dp_reference": "E2-4",
                "ig3_note": "IG 3.E2.1 — NOx, SOx, PM2.5, VOC, HAP emission volumes and hotspots",
                "mandatory": False,
                "sector_applicability": ["B", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E2.2": {
                "name": "Pollution of water",
                "dp_reference": "E2-4",
                "ig3_note": "IG 3.E2.2 — Discharge to water bodies, effluent treatment adequacy",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E2.3": {
                "name": "Pollution of soil",
                "dp_reference": "E2-4",
                "ig3_note": "IG 3.E2.3 — Hazardous substance spills, soil contamination remediation",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E2.4": {
                "name": "Pollution of living organisms and food resources",
                "dp_reference": "E2-4",
                "ig3_note": "IG 3.E2.4 — Substances of concern in biota and food chains",
                "mandatory": False,
                "sector_applicability": ["A", "C"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 4,
                "financial_threshold": 3,
            },
            "E2.5": {
                "name": "Substances of concern and very high concern (SVHC)",
                "dp_reference": "E2-5",
                "ig3_note": "IG 3.E2.5 — REACH SVHC in products and processes; phase-out plans",
                "mandatory": False,
                "sector_applicability": ["B", "C", "D"],
                "iro_types": ["actual_negative_impact", "transition_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
        },
    },
    "E3": {
        "name": "Water and Marine Resources",
        "pillar": "Environmental",
        "standard": "ESRS E3",
        "sub_topics": {
            "E3.1": {
                "name": "Water consumption",
                "dp_reference": "E3-4",
                "ig3_note": "IG 3.E3.1 — Water consumption in water-stressed areas per WRI Aqueduct",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "physical_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E3.2": {
                "name": "Water withdrawals",
                "dp_reference": "E3-4",
                "ig3_note": "IG 3.E3.2 — Source-level withdrawal data; riparian rights risk",
                "mandatory": False,
                "sector_applicability": ["A", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "physical_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E3.3": {
                "name": "Water discharges",
                "dp_reference": "E3-4",
                "ig3_note": "IG 3.E3.3 — Discharge volumes and quality; nutrient loads to water bodies",
                "mandatory": False,
                "sector_applicability": ["A", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "E3.4": {
                "name": "Marine resources",
                "dp_reference": "E3-5",
                "ig3_note": "IG 3.E3.4 — Extraction of marine resources; ocean ecosystem pressure",
                "mandatory": False,
                "sector_applicability": ["A", "B"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 4,
                "financial_threshold": 3,
            },
            "E3.5": {
                "name": "Water and marine ecosystems",
                "dp_reference": "E3-5",
                "ig3_note": "IG 3.E3.5 — Freshwater/marine ecosystem health dependencies and restoration",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C"],
                "iro_types": ["physical_risk", "opportunity"],
                "impact_threshold": 4,
                "financial_threshold": 3,
            },
        },
    },
    "E4": {
        "name": "Biodiversity and Ecosystems",
        "pillar": "Environmental",
        "standard": "ESRS E4",
        "sub_topics": {
            "E4.1": {
                "name": "Direct impact drivers of biodiversity loss",
                "dp_reference": "E4-2",
                "ig3_note": "IG 3.E4.1 — IPBES 5 direct drivers: land/sea use change, exploitation, climate, pollution, invasives",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E4.2": {
                "name": "Impacts on the state of species",
                "dp_reference": "E4-4",
                "ig3_note": "IG 3.E4.2 — IUCN Red List species affected, population trends",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 4,
                "financial_threshold": 3,
            },
            "E4.3": {
                "name": "Impacts on extent and condition of ecosystems",
                "dp_reference": "E4-4",
                "ig3_note": "IG 3.E4.3 — MSA.km2 footprint; habitat area conversion; ENCORE linkage",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E4.4": {
                "name": "Impacts and dependencies on ecosystem services",
                "dp_reference": "E4-5",
                "ig3_note": "IG 3.E4.4 — ENCORE ecosystem service dependency and impact mapping; PBAF",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D"],
                "iro_types": ["actual_negative_impact", "physical_risk", "opportunity"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E4.5": {
                "name": "Biodiversity-sensitive areas",
                "dp_reference": "E4-2",
                "ig3_note": "IG 3.E4.5 — Operations/supply chains in or near Natura 2000 and IBA sites",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 4,
                "financial_threshold": 3,
            },
            "E4.6": {
                "name": "Biodiversity net gain and ecosystem restoration",
                "dp_reference": "E4-2",
                "ig3_note": "IG 3.E4.6 — BNG commitments, TNFD targets, habitat restoration plans",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "F"],
                "iro_types": ["actual_positive_impact", "potential_positive_impact", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
        },
    },
    "E5": {
        "name": "Resource Use and Circular Economy",
        "pillar": "Environmental",
        "standard": "ESRS E5",
        "sub_topics": {
            "E5.1": {
                "name": "Resource inflows including raw materials",
                "dp_reference": "E5-4",
                "ig3_note": "IG 3.E5.1 — Material inflows; recycled/bio-based content share",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E5.2": {
                "name": "Resource outflows including products",
                "dp_reference": "E5-5",
                "ig3_note": "IG 3.E5.2 — Product durability, repairability, recyclability design at end-of-life",
                "mandatory": False,
                "sector_applicability": ["C", "D", "E"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "E5.3": {
                "name": "Waste",
                "dp_reference": "E5-5",
                "ig3_note": "IG 3.E5.3 — Waste generation, treatment, hazardous waste management",
                "mandatory": False,
                "sector_applicability": ["B", "C", "D", "E", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "E5.4": {
                "name": "Circular product design and lifetime extension",
                "dp_reference": "E5-2",
                "ig3_note": "IG 3.E5.4 — Design for disassembly; remanufacturing and refurbishment programmes",
                "mandatory": False,
                "sector_applicability": ["C", "D"],
                "iro_types": ["actual_positive_impact", "potential_positive_impact", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "E5.5": {
                "name": "Circular economy initiatives in own operations",
                "dp_reference": "E5-3",
                "ig3_note": "IG 3.E5.5 — Circular economy transition plans; circularity rate targets",
                "mandatory": False,
                "sector_applicability": ["C", "D", "E"],
                "iro_types": ["actual_positive_impact", "potential_positive_impact", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
        },
    },
    "S1": {
        "name": "Own Workforce",
        "pillar": "Social",
        "standard": "ESRS S1",
        "sub_topics": {
            "S1.1": {
                "name": "Working conditions",
                "dp_reference": "S1-7",
                "ig3_note": "IG 3.S1.1 — Hours, rest, overtime, living wage, flexible working arrangements",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "S1.2": {
                "name": "Equal treatment and opportunities for all",
                "dp_reference": "S1-9",
                "ig3_note": "IG 3.S1.2 — Gender pay gap, diversity metrics, anti-discrimination policy",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "S1.3": {
                "name": "Other work-related rights",
                "dp_reference": "S1-17",
                "ig3_note": "IG 3.S1.3 — Freedom of association, collective bargaining, child/forced labour",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "S1.4": {
                "name": "Health and safety",
                "dp_reference": "S1-14",
                "ig3_note": "IG 3.S1.4 — OHSMS, accident rates, fatalities, occupational diseases",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "S1.5": {
                "name": "Social dialogue and freedom of association",
                "dp_reference": "S1-8",
                "ig3_note": "IG 3.S1.5 — Works council coverage, collective agreement scope (%)",
                "mandatory": False,
                "sector_applicability": ["B", "C", "D", "E", "F", "G", "H", "I"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "S1.6": {
                "name": "Work-life balance",
                "dp_reference": "S1-12",
                "ig3_note": "IG 3.S1.6 — Flexible arrangements, parental leave uptake, childcare support",
                "mandatory": False,
                "sector_applicability": ["G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_positive_impact", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "S1.7": {
                "name": "Remuneration",
                "dp_reference": "S1-16",
                "ig3_note": "IG 3.S1.7 — CEO pay ratio, living wage alignment, executive ESG link",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "S1.8": {
                "name": "Training and skills development",
                "dp_reference": "S1-13",
                "ig3_note": "IG 3.S1.8 — Training hours per employee; upskilling and reskilling spend",
                "mandatory": False,
                "sector_applicability": ["G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_positive_impact", "potential_positive_impact", "opportunity"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "S1.9": {
                "name": "Employment and inclusion of persons with disabilities",
                "dp_reference": "S1-9",
                "ig3_note": "IG 3.S1.9 — Disability employment rate, reasonable adjustments provision",
                "mandatory": False,
                "sector_applicability": ["G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_positive_impact", "potential_positive_impact"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
        },
    },
    "S2": {
        "name": "Workers in the Value Chain",
        "pillar": "Social",
        "standard": "ESRS S2",
        "sub_topics": {
            "S2.1": {
                "name": "Working conditions in value chain",
                "dp_reference": "S2-4",
                "ig3_note": "IG 3.S2.1 — Living wage, hours, health/safety in tier 1-3 supply chain",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "F", "G", "H"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "S2.2": {
                "name": "Equal treatment and opportunities in value chain",
                "dp_reference": "S2-4",
                "ig3_note": "IG 3.S2.2 — Discrimination and harassment in suppliers",
                "mandatory": False,
                "sector_applicability": ["A", "C", "D", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "S2.3": {
                "name": "Child labour in value chain",
                "dp_reference": "S2-4",
                "ig3_note": "IG 3.S2.3 — UNGP/ILO C138/C182 child labour by country-sector risk",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 5,
                "financial_threshold": 4,
            },
            "S2.4": {
                "name": "Forced labour in value chain",
                "dp_reference": "S2-4",
                "ig3_note": "IG 3.S2.4 — ILO P29 modern slavery indicators and remediation",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 5,
                "financial_threshold": 4,
            },
            "S2.5": {
                "name": "Supplier engagement and capacity building",
                "dp_reference": "S2-2",
                "ig3_note": "IG 3.S2.5 — Supplier sustainability requirements and audit programme",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D"],
                "iro_types": ["actual_positive_impact", "potential_positive_impact"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
        },
    },
    "S3": {
        "name": "Affected Communities",
        "pillar": "Social",
        "standard": "ESRS S3",
        "sub_topics": {
            "S3.1": {
                "name": "Communities' economic, social and cultural rights",
                "dp_reference": "S3-4",
                "ig3_note": "IG 3.S3.1 — Land rights, livelihoods, indigenous FPIC (UNDRIP)",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 4,
                "financial_threshold": 3,
            },
            "S3.2": {
                "name": "Civil and political rights of communities",
                "dp_reference": "S3-4",
                "ig3_note": "IG 3.S3.2 — Freedom of expression, HRD protection, access to remedy",
                "mandatory": False,
                "sector_applicability": ["B", "C", "D", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 4,
                "financial_threshold": 3,
            },
            "S3.3": {
                "name": "Rights of indigenous peoples",
                "dp_reference": "S3-4",
                "ig3_note": "IG 3.S3.3 — UNDRIP FPIC protocols, cultural heritage, sacred sites",
                "mandatory": False,
                "sector_applicability": ["A", "B", "D", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 5,
                "financial_threshold": 4,
            },
            "S3.4": {
                "name": "Local and vulnerable groups",
                "dp_reference": "S3-4",
                "ig3_note": "IG 3.S3.4 — Gender, age, disability, poverty dimension in community impact",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "S3.5": {
                "name": "Community grievance and remedy",
                "dp_reference": "S3-3",
                "ig3_note": "IG 3.S3.5 — Grievance mechanism adequacy; remedy provided per UNGP Pillar 3",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F"],
                "iro_types": ["actual_negative_impact", "actual_positive_impact"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
        },
    },
    "S4": {
        "name": "Consumers and End-users",
        "pillar": "Social",
        "standard": "ESRS S4",
        "sub_topics": {
            "S4.1": {
                "name": "Information-related impacts for consumers",
                "dp_reference": "S4-4",
                "ig3_note": "IG 3.S4.1 — Privacy, data protection (GDPR), misleading advertising",
                "mandatory": False,
                "sector_applicability": ["G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 3,
                "financial_threshold": 3,
            },
            "S4.2": {
                "name": "Personal safety of consumers",
                "dp_reference": "S4-4",
                "ig3_note": "IG 3.S4.2 — Product safety incidents, recalls, adverse event reporting",
                "mandatory": False,
                "sector_applicability": ["C", "G", "I"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 4,
                "financial_threshold": 4,
            },
            "S4.3": {
                "name": "Social inclusion of consumers",
                "dp_reference": "S4-4",
                "ig3_note": "IG 3.S4.3 — Accessibility, affordability, vulnerable consumer protection",
                "mandatory": False,
                "sector_applicability": ["G", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "actual_positive_impact", "opportunity"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "S4.4": {
                "name": "Responsible marketing practices",
                "dp_reference": "S4-4",
                "ig3_note": "IG 3.S4.4 — Advertising to minors, vulnerable-group targeting policies",
                "mandatory": False,
                "sector_applicability": ["G", "I", "J"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
        },
    },
    "G1": {
        "name": "Business Conduct",
        "pillar": "Governance",
        "standard": "ESRS G1",
        "sub_topics": {
            "G1.1": {
                "name": "Corporate culture and business conduct policies",
                "dp_reference": "G1-1",
                "ig3_note": "IG 3.G1.1 — Codes of conduct, whistleblower protection, culture assessment",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "G1.2": {
                "name": "Management of relationships with suppliers",
                "dp_reference": "G1-2",
                "ig3_note": "IG 3.G1.2 — Payment practices; supplier code of conduct; DD coverage",
                "mandatory": False,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
            "G1.3": {
                "name": "Prevention and detection of corruption and bribery",
                "dp_reference": "G1-3",
                "ig3_note": "IG 3.G1.3 — Anti-corruption programme, confirmed cases, remediation",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact", "transition_risk"],
                "impact_threshold": 3,
                "financial_threshold": 4,
            },
            "G1.4": {
                "name": "Political engagement and lobbying activities",
                "dp_reference": "G1-5",
                "ig3_note": "IG 3.G1.4 — Lobbying spend, policy positions, Paris alignment consistency",
                "mandatory": False,
                "sector_applicability": ["C", "D", "E", "J", "K"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 3,
                "financial_threshold": 2,
            },
            "G1.5": {
                "name": "Payment practices",
                "dp_reference": "G1-6",
                "ig3_note": "IG 3.G1.5 — Days payable outstanding; SME payment terms compliance",
                "mandatory": True,
                "sector_applicability": ["A", "B", "C", "D", "E", "F", "G", "H"],
                "iro_types": ["actual_negative_impact", "potential_negative_impact"],
                "impact_threshold": 2,
                "financial_threshold": 2,
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Reference Data — NACE Sector × ESRS Topic Materiality Matrix
# Covers 50 NACE section/subsection entries: high/medium/low/na
# ---------------------------------------------------------------------------

NACE_MATERIALITY_MATRIX: Dict[str, Dict[str, str]] = {
    # NACE sections A-T
    "A": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "high",   "E5": "medium", "S1": "high",   "S2": "high",   "S3": "high",   "S4": "low",    "G1": "medium"},
    "B": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "high",   "E5": "medium", "S1": "high",   "S2": "medium", "S3": "high",   "S4": "low",    "G1": "high"},
    "C": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "medium", "E5": "high",   "S1": "high",   "S2": "high",   "S3": "medium", "S4": "medium", "G1": "high"},
    "D": {"E1": "high",   "E2": "high",   "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "low",    "S4": "low",    "G1": "medium"},
    "E": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "high",   "E5": "high",   "S1": "medium", "S2": "low",    "S3": "high",   "S4": "low",    "G1": "medium"},
    "F": {"E1": "high",   "E2": "medium", "E3": "medium", "E4": "high",   "E5": "high",   "S1": "high",   "S2": "high",   "S3": "high",   "S4": "low",    "G1": "medium"},
    "G": {"E1": "medium", "E2": "low",    "E3": "low",    "E4": "low",    "E5": "high",   "S1": "high",   "S2": "high",   "S3": "medium", "S4": "high",   "G1": "high"},
    "H": {"E1": "high",   "E2": "medium", "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "medium", "G1": "medium"},
    "I": {"E1": "medium", "E2": "low",    "E3": "medium", "E4": "low",    "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "medium"},
    "J": {"E1": "low",    "E2": "na",     "E3": "low",    "E4": "low",    "E5": "medium", "S1": "high",   "S2": "low",    "S3": "low",    "S4": "high",   "G1": "high"},
    "K": {"E1": "medium", "E2": "low",    "E3": "low",    "E4": "medium", "E5": "low",    "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "high"},
    "L": {"E1": "high",   "E2": "low",    "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "low",    "S3": "medium", "S4": "medium", "G1": "medium"},
    "M": {"E1": "low",    "E2": "low",    "E3": "low",    "E4": "low",    "E5": "low",    "S1": "high",   "S2": "low",    "S3": "low",    "S4": "medium", "G1": "high"},
    "N": {"E1": "medium", "E2": "low",    "E3": "low",    "E4": "low",    "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "medium", "G1": "medium"},
    "O": {"E1": "medium", "E2": "medium", "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "high",   "S4": "medium", "G1": "high"},
    "P": {"E1": "low",    "E2": "low",    "E3": "low",    "E4": "low",    "E5": "low",    "S1": "high",   "S2": "low",    "S3": "medium", "S4": "high",   "G1": "medium"},
    "Q": {"E1": "medium", "E2": "medium", "E3": "medium", "E4": "low",    "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "high"},
    "R": {"E1": "medium", "E2": "low",    "E3": "low",    "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "high",   "S4": "high",   "G1": "medium"},
    "S": {"E1": "low",    "E2": "low",    "E3": "low",    "E4": "low",    "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "medium"},
    "T": {"E1": "low",    "E2": "low",    "E3": "low",    "E4": "low",    "E5": "low",    "S1": "high",   "S2": "low",    "S3": "medium", "S4": "medium", "G1": "low"},
    # NACE subsection overrides
    "C10": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "high",   "E5": "high",   "S1": "high",   "S2": "high",   "S3": "high",   "S4": "medium", "G1": "high"},
    "C13": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "medium", "E5": "high",   "S1": "high",   "S2": "high",   "S3": "high",   "S4": "medium", "G1": "high"},
    "C14": {"E1": "medium", "E2": "medium", "E3": "medium", "E4": "medium", "E5": "high",   "S1": "high",   "S2": "high",   "S3": "medium", "S4": "medium", "G1": "medium"},
    "C17": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "medium", "E5": "high",   "S1": "high",   "S2": "medium", "S3": "medium", "S4": "low",    "G1": "medium"},
    "C19": {"E1": "high",   "E2": "high",   "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "low",    "G1": "high"},
    "C20": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "high",   "E5": "high",   "S1": "high",   "S2": "medium", "S3": "medium", "S4": "medium", "G1": "high"},
    "C23": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "medium", "E5": "high",   "S1": "high",   "S2": "medium", "S3": "medium", "S4": "low",    "G1": "medium"},
    "C24": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "medium", "E5": "high",   "S1": "high",   "S2": "medium", "S3": "medium", "S4": "low",    "G1": "high"},
    "C25": {"E1": "high",   "E2": "high",   "E3": "medium", "E4": "medium", "E5": "high",   "S1": "high",   "S2": "medium", "S3": "medium", "S4": "medium", "G1": "medium"},
    "C26": {"E1": "medium", "E2": "medium", "E3": "medium", "E4": "low",    "E5": "high",   "S1": "high",   "S2": "high",   "S3": "low",    "S4": "high",   "G1": "high"},
    "D35": {"E1": "high",   "E2": "high",   "E3": "medium", "E4": "medium", "E5": "medium", "S1": "medium", "S2": "low",    "S3": "medium", "S4": "medium", "G1": "medium"},
    "H49": {"E1": "high",   "E2": "high",   "E3": "low",    "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "medium", "G1": "medium"},
    "H50": {"E1": "high",   "E2": "high",   "E3": "high",   "E4": "high",   "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "medium", "G1": "medium"},
    "H51": {"E1": "high",   "E2": "high",   "E3": "low",    "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "low",    "S4": "high",   "G1": "high"},
    "H52": {"E1": "medium", "E2": "medium", "E3": "low",    "E4": "low",    "E5": "high",   "S1": "high",   "S2": "medium", "S3": "medium", "S4": "medium", "G1": "medium"},
    "K64": {"E1": "medium", "E2": "low",    "E3": "low",    "E4": "medium", "E5": "low",    "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "high"},
    "K65": {"E1": "medium", "E2": "low",    "E3": "low",    "E4": "medium", "E5": "low",    "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "high"},
    "K66": {"E1": "low",    "E2": "na",     "E3": "low",    "E4": "low",    "E5": "low",    "S1": "high",   "S2": "low",    "S3": "low",    "S4": "high",   "G1": "high"},
    "L68": {"E1": "high",   "E2": "low",    "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "low",    "S3": "high",   "S4": "medium", "G1": "medium"},
    "M69": {"E1": "low",    "E2": "na",     "E3": "na",     "E4": "low",    "E5": "low",    "S1": "high",   "S2": "low",    "S3": "low",    "S4": "medium", "G1": "high"},
    "M70": {"E1": "low",    "E2": "na",     "E3": "na",     "E4": "low",    "E5": "low",    "S1": "high",   "S2": "medium", "S3": "low",    "S4": "medium", "G1": "high"},
    "M71": {"E1": "medium", "E2": "low",    "E3": "low",    "E4": "medium", "E5": "low",    "S1": "high",   "S2": "low",    "S3": "low",    "S4": "medium", "G1": "high"},
    "N79": {"E1": "high",   "E2": "high",   "E3": "medium", "E4": "high",   "E5": "medium", "S1": "high",   "S2": "high",   "S3": "high",   "S4": "high",   "G1": "medium"},
    "O84": {"E1": "medium", "E2": "medium", "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "high",   "S4": "medium", "G1": "high"},
    "Q86": {"E1": "medium", "E2": "high",   "E3": "medium", "E4": "low",    "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "high"},
    "Q87": {"E1": "low",    "E2": "medium", "E3": "medium", "E4": "low",    "E5": "medium", "S1": "high",   "S2": "medium", "S3": "high",   "S4": "high",   "G1": "high"},
    "R90": {"E1": "low",    "E2": "low",    "E3": "low",    "E4": "medium", "E5": "low",    "S1": "high",   "S2": "medium", "S3": "high",   "S4": "high",   "G1": "medium"},
    "R93": {"E1": "medium", "E2": "low",    "E3": "medium", "E4": "high",   "E5": "medium", "S1": "high",   "S2": "medium", "S3": "high",   "S4": "high",   "G1": "medium"},
    "S94": {"E1": "low",    "E2": "low",    "E3": "low",    "E4": "low",    "E5": "low",    "S1": "high",   "S2": "medium", "S3": "high",   "S4": "high",   "G1": "medium"},
    "S96": {"E1": "medium", "E2": "medium", "E3": "medium", "E4": "medium", "E5": "medium", "S1": "high",   "S2": "medium", "S3": "medium", "S4": "high",   "G1": "medium"},
}


# ---------------------------------------------------------------------------
# Reference Data — IRO Type Definitions
# ---------------------------------------------------------------------------

IRO_TYPE_DEFINITIONS: Dict[str, Dict] = {
    "actual_negative_impact": {
        "label": "Actual Negative Impact",
        "esrs_ref": "ESRS 1 AR 3 (a)",
        "description": "A negative impact the undertaking is causing or contributing to in the present, or has caused in the past.",
        "impact_materiality_weight": 1.0,
        "financial_materiality_weight": 0.5,
        "reporting_obligation": "Mandatory disclosure with quantitative metrics where feasible (ESRS 1 para 46)",
    },
    "potential_negative_impact": {
        "label": "Potential Negative Impact",
        "esrs_ref": "ESRS 1 AR 3 (b)",
        "description": "A negative impact the undertaking could cause or contribute to in the future.",
        "impact_materiality_weight": 0.7,
        "financial_materiality_weight": 0.6,
        "reporting_obligation": "Qualitative disclosure with likelihood estimate required (ESRS 1 para 47)",
    },
    "actual_positive_impact": {
        "label": "Actual Positive Impact",
        "esrs_ref": "ESRS 1 AR 3 (c)",
        "description": "A positive impact the undertaking is causing or contributing to in the present.",
        "impact_materiality_weight": 0.8,
        "financial_materiality_weight": 0.4,
        "reporting_obligation": "Voluntary disclosure encouraged; required if used in marketing claims (ESRS 1 para 48)",
    },
    "potential_positive_impact": {
        "label": "Potential Positive Impact",
        "esrs_ref": "ESRS 1 AR 3 (d)",
        "description": "A positive impact the undertaking could cause or contribute to in the future.",
        "impact_materiality_weight": 0.5,
        "financial_materiality_weight": 0.4,
        "reporting_obligation": "Voluntary; targets and progress reporting encouraged (ESRS 1 para 48)",
    },
    "physical_risk": {
        "label": "Physical Risk (Financial)",
        "esrs_ref": "ESRS 1 AR 11",
        "description": "Climate or nature-related physical hazard generating material financial effects: revenue disruption, asset impairment, supply chain breakdown.",
        "impact_materiality_weight": 0.3,
        "financial_materiality_weight": 1.0,
        "reporting_obligation": "Quantitative financial effect disclosure required in ESRS E1-9 (ESRS 1 para 49)",
    },
    "transition_risk": {
        "label": "Transition Risk (Financial)",
        "esrs_ref": "ESRS 1 AR 11",
        "description": "Policy, regulatory, technology or reputational risk arising from the transition to a sustainable economy.",
        "impact_materiality_weight": 0.4,
        "financial_materiality_weight": 1.0,
        "reporting_obligation": "Scenario analysis mandatory for climate; qualitative for others (ESRS 1 para 50)",
    },
    "opportunity": {
        "label": "Sustainability-related Opportunity",
        "esrs_ref": "ESRS 1 AR 12",
        "description": "Business opportunity arising from sustainability market, technology, or regulatory developments.",
        "impact_materiality_weight": 0.3,
        "financial_materiality_weight": 0.8,
        "reporting_obligation": "Voluntary where financially material; SBTi/EU Taxonomy alignment encouraged",
    },
}


# ---------------------------------------------------------------------------
# Reference Data — CSRD Wave Timeline
# ---------------------------------------------------------------------------

CSRD_WAVE_TIMELINE: List[Dict] = [
    {
        "wave": 1,
        "label": "Wave 1 — Large PIEs > 500 employees",
        "directive_reference": "CSRD Art 5(1)(a) amending NFRD Art 19a",
        "reporting_year": 2024,
        "financial_year": "FY 2024",
        "publication_deadline": "2025-06-30",
        "scope": "Large PIEs with > 500 employees already subject to NFRD",
        "estimated_companies": 11700,
        "employee_threshold": 500,
        "is_pie_only": True,
        "first_year_relief": ["E4", "S2", "S3", "S4"],
    },
    {
        "wave": 2,
        "label": "Wave 2 — Large non-PIE undertakings",
        "directive_reference": "CSRD Art 5(1)(b) amending NFRD Art 19a",
        "reporting_year": 2025,
        "financial_year": "FY 2025",
        "publication_deadline": "2026-06-30",
        "scope": "Large EU undertakings not previously subject to NFRD (>250 employees OR >EUR40m revenue OR >EUR20m assets)",
        "estimated_companies": 50000,
        "employee_threshold": 250,
        "is_pie_only": False,
        "first_year_relief": ["E4", "S2", "S3", "S4"],
    },
    {
        "wave": 3,
        "label": "Wave 3 — Listed SMEs on EU regulated markets",
        "directive_reference": "CSRD Art 5(1)(c) amending NFRD Art 29a",
        "reporting_year": 2026,
        "financial_year": "FY 2026",
        "publication_deadline": "2027-06-30",
        "scope": "Listed SMEs on EU regulated markets (opt-out available until 2028)",
        "estimated_companies": 37000,
        "employee_threshold": 10,
        "is_pie_only": True,
        "first_year_relief": ["E2", "E3", "E4", "E5", "S2", "S3", "S4"],
    },
    {
        "wave": 4,
        "label": "Wave 4 — Non-EU undertakings with EU nexus",
        "directive_reference": "CSRD Art 5(2) amending Transparency Directive",
        "reporting_year": 2028,
        "financial_year": "FY 2028",
        "publication_deadline": "2029-06-30",
        "scope": "Non-EU parent companies with net EU turnover > EUR150m and at least one EU subsidiary/branch",
        "estimated_companies": 10000,
        "employee_threshold": 0,
        "is_pie_only": False,
        "first_year_relief": [],
    },
]


# ---------------------------------------------------------------------------
# Reference Data — Stakeholder Groups
# ---------------------------------------------------------------------------

STAKEHOLDER_GROUPS: List[Dict] = [
    {"id": "investors",   "label": "Investors and Lenders",       "engagement_method": "Annual investor presentations, ESG roadshows, direct dialogue", "frequency": "quarterly",  "esrs_ref": "ESRS 1 para 20"},
    {"id": "employees",   "label": "Own Workforce",               "engagement_method": "Employee surveys, works council consultation, focus groups",    "frequency": "annual",     "esrs_ref": "ESRS S1-2"},
    {"id": "customers",   "label": "Customers and End-users",     "engagement_method": "Customer satisfaction surveys, complaint tracking, advisory panels", "frequency": "ongoing", "esrs_ref": "ESRS S4-2"},
    {"id": "suppliers",   "label": "Suppliers and Business Partners", "engagement_method": "Supplier assessments, code of conduct sign-off, supplier days", "frequency": "annual",  "esrs_ref": "ESRS S2-2"},
    {"id": "communities", "label": "Affected Communities",        "engagement_method": "Community consultations, grievance mechanisms, local meetings",  "frequency": "biannual",  "esrs_ref": "ESRS S3-2"},
    {"id": "ngos",        "label": "NGOs and Civil Society",      "engagement_method": "Multi-stakeholder forums, regulatory consultations, public comment", "frequency": "as_needed", "esrs_ref": "ESRS 1 para 22"},
]


# ---------------------------------------------------------------------------
# Reference Data — Assurance Criteria
# ---------------------------------------------------------------------------

ASSURANCE_CRITERIA: List[Dict] = [
    {"id": "documentation_completeness", "label": "Documentation Completeness",   "weight": 0.25, "limited_threshold": 60, "reasonable_threshold": 85, "description": "All material topics supported by documented assessment methodology, data sources and assumptions"},
    {"id": "stakeholder_evidence",       "label": "Stakeholder Engagement Evidence", "weight": 0.20, "limited_threshold": 60, "reasonable_threshold": 85, "description": "Structured evidence of stakeholder engagement feeding into materiality determination"},
    {"id": "iro_quantification",         "label": "IRO Quantification",            "weight": 0.25, "limited_threshold": 55, "reasonable_threshold": 80, "description": "Material IROs quantified with ESRS metrics, comparatives, and projection data"},
    {"id": "methodology_consistency",    "label": "Methodology Consistency",       "weight": 0.15, "limited_threshold": 65, "reasonable_threshold": 90, "description": "Double materiality methodology consistently applied; threshold rationale documented"},
    {"id": "audit_trail",               "label": "Audit Trail",                   "weight": 0.15, "limited_threshold": 70, "reasonable_threshold": 90, "description": "Complete traceable record from raw input through to reported figures; version control in place"},
]


# ---------------------------------------------------------------------------
# Reference Data — ESRS Omission Criteria (ESRS 1 paras 29-35)
# ---------------------------------------------------------------------------

OMISSION_CRITERIA: Dict[str, Dict] = {
    "not_applicable": {
        "label": "Not applicable — no relevant activities",
        "esrs_ref": "ESRS 1 para 29",
        "requires_justification": True,
        "requires_nace_evidence": True,
        "description": "The undertaking does not have operations, products, services, or relationships to which the ESRS topic applies",
    },
    "immaterial": {
        "label": "Immaterial — below double materiality threshold",
        "esrs_ref": "ESRS 1 para 31",
        "requires_justification": True,
        "requires_nace_evidence": False,
        "description": "The topic has been assessed and found not material per the double materiality assessment",
    },
    "proprietary": {
        "label": "Proprietary information — commercially sensitive",
        "esrs_ref": "ESRS 1 para 34",
        "requires_justification": True,
        "requires_nace_evidence": False,
        "description": "Disclosure would cause serious prejudice; cannot be applied to mandatory ESRS DPs",
    },
    "third_party_limitation": {
        "label": "Third-party limitation — data not obtainable",
        "esrs_ref": "ESRS 1 para 35",
        "requires_justification": True,
        "requires_nace_evidence": False,
        "description": "Information depends on third-party data that cannot be obtained despite reasonable efforts",
    },
}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class TopicAssessment(BaseModel):
    model_config = {"protected_namespaces": ()}

    esrs_topic: str = Field(..., description="ESRS topic code e.g. E1, S2, G1")
    assessed_by_company: bool = Field(True)
    impact_scale: int = Field(..., ge=1, le=5, description="1=negligible, 5=critical/widespread")
    impact_scope: int = Field(..., ge=1, le=5, description="1=isolated, 5=global")
    impact_likelihood: int = Field(..., ge=1, le=5, description="1=<10%, 5=>90%")
    impact_irremediable: int = Field(..., ge=1, le=5, description="1=fully remediable, 5=irremediable")
    financial_likelihood: int = Field(..., ge=1, le=5)
    financial_magnitude: int = Field(..., ge=1, le=5, description="1=negligible, 5=severe financial effect")
    justification: str = Field("", description="Company narrative justification for ratings")


class IROAssessment(BaseModel):
    model_config = {"protected_namespaces": ()}

    topic: str = Field(..., description="ESRS topic code")
    iro_type: str = Field(..., description="IRO type key from IRO_TYPE_DEFINITIONS")
    description: str = Field(..., description="Narrative description of the IRO")
    time_horizon: str = Field("medium", description="short (<1yr) / medium (1-5yr) / long (>5yr)")
    value_chain_position: str = Field("own_operations", description="upstream / own_operations / downstream")
    impact_scale: int = Field(..., ge=1, le=5)
    impact_scope: int = Field(..., ge=1, le=5)
    impact_likelihood: int = Field(..., ge=1, le=5)
    impact_irremediable: int = Field(..., ge=1, le=5)
    financial_likelihood: int = Field(..., ge=1, le=5)
    financial_magnitude: int = Field(..., ge=1, le=5)


class DoubleMaterialityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_name: str
    nace_sector: str = Field(..., description="NACE section A-T or subsection e.g. C20")
    employee_count: int = Field(..., ge=0)
    csrd_wave: Optional[int] = Field(None, ge=1, le=4)
    reporting_year: int = Field(2024, ge=2024, le=2030)
    topic_assessments: List[TopicAssessment] = Field(default_factory=list)


class IROIdentificationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_name: str
    topic: str = Field(..., description="ESRS topic code e.g. E1")
    iro_assessments: List[IROAssessment] = Field(default_factory=list)


class OmissionCheckRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_name: str
    nace_sector: str
    topics_not_reported: List[Dict[str, str]] = Field(
        ..., description="List of {topic, omission_criterion, justification}"
    )


class MaterialityMatrixRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_name: str
    topic_scores: List[Dict[str, Any]] = Field(
        ..., description="List of {topic, impact_score, financial_score}"
    )


class CompletenessRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_name: str
    nace_sector: str
    topics_reported: List[str]
    dps_reported: int = Field(..., ge=0)
    dps_mandatory_for_sector: int = Field(..., ge=1)


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class DoubleMaterialityEngine:
    """E102 — CSRD Double Materiality Assessment Engine (ESRS 1 methodology)."""

    MATERIALITY_THRESHOLD: float = 0.40
    LIMITED_ASSURANCE_THRESHOLD: float = 0.60
    REASONABLE_ASSURANCE_THRESHOLD: float = 0.85

    # -------------------------------------------------------------------------
    # Public Methods
    # -------------------------------------------------------------------------

    def conduct_double_materiality(
        self,
        entity_name: str,
        nace_sector: str,
        employee_count: int,
        reporting_year: int,
        topic_assessments: List[TopicAssessment],
        csrd_wave: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run full ESRS 1 double materiality assessment for all 10 ESRS topics.

        Impact materiality:
            max(scale x scope x irremediability / 125, likelihood x scale / 25) -> 0-1

        Financial materiality:
            likelihood x magnitude / 25 -> 0-1

        Double material if either score >= MATERIALITY_THRESHOLD (default 0.40).
        NACE materiality triggers applied as baseline for unassessed topics.
        """
        assessed_map: Dict[str, TopicAssessment] = {a.esrs_topic: a for a in topic_assessments}
        nace_key = self._resolve_nace_key(nace_sector)
        nace_triggers: Dict[str, str] = NACE_MATERIALITY_MATRIX.get(nace_key, {})
        inferred_wave = csrd_wave or self._infer_wave(employee_count)

        material_topics: List[Dict] = []
        all_topic_results: List[Dict] = []
        total_iros: int = 0

        for topic_code, topic_meta in ESRS_TOPICS.items():
            assessment = assessed_map.get(topic_code)
            nace_signal: str = nace_triggers.get(topic_code, "na")

            if assessment:
                imp_score, fin_score = self._score_from_assessment(assessment)
                source = "company_assessment"
            else:
                imp_score, fin_score = self._nace_baseline_scores(nace_signal)
                source = f"nace_baseline_{nace_signal}"

            is_mat_impact = imp_score >= self.MATERIALITY_THRESHOLD
            is_mat_financial = fin_score >= self.MATERIALITY_THRESHOLD
            is_double_material = is_mat_impact or is_mat_financial

            sub_iro_count = sum(len(sub["iro_types"]) for sub in topic_meta["sub_topics"].values())
            if is_double_material:
                total_iros += sub_iro_count

            row: Dict[str, Any] = {
                "topic": topic_code,
                "name": topic_meta["name"],
                "pillar": topic_meta["pillar"],
                "nace_signal": nace_signal,
                "source": source,
                "impact_materiality_score": round(imp_score, 4),
                "financial_materiality_score": round(fin_score, 4),
                "is_material_impact": is_mat_impact,
                "is_material_financial": is_mat_financial,
                "is_double_material": is_double_material,
                "sub_topic_count": len(topic_meta["sub_topics"]),
                "mandatory_sub_topics": sum(1 for s in topic_meta["sub_topics"].values() if s["mandatory"]),
                "first_year_reporting_relief": self._has_relief(topic_code, reporting_year, inferred_wave),
                "quadrant": self._quadrant(imp_score, fin_score),
            }
            all_topic_results.append(row)
            if is_double_material:
                material_topics.append(row)

        completeness = self._estimate_completeness(len(material_topics), len(topic_assessments))
        assurance = self._assess_assurance_readiness(completeness, len(topic_assessments))

        return {
            "entity_name": entity_name,
            "nace_sector": nace_sector,
            "employee_count": employee_count,
            "reporting_year": reporting_year,
            "csrd_wave": inferred_wave,
            "assessment_date": datetime.utcnow().isoformat() + "Z",
            "methodology": "ESRS 1 Double Materiality — EFRAG IG1 (Dec 2023)",
            "materiality_threshold": self.MATERIALITY_THRESHOLD,
            "total_topics_assessed": len(all_topic_results),
            "material_topics_count": len(material_topics),
            "material_topics": material_topics,
            "all_topic_results": all_topic_results,
            "total_iro_count": total_iros,
            "completeness_score": round(completeness, 4),
            "assurance_readiness": assurance,
            "stakeholder_groups": STAKEHOLDER_GROUPS,
            "csrd_wave_details": next((w for w in CSRD_WAVE_TIMELINE if w["wave"] == inferred_wave), None),
        }

    def identify_iros(
        self,
        entity_name: str,
        topic: str,
        iro_assessments: List[IROAssessment],
    ) -> Dict[str, Any]:
        """Structured IRO identification and scoring for a single ESRS topic."""
        topic_meta = ESRS_TOPICS.get(topic, {})
        results: List[Dict] = []

        for iro in iro_assessments:
            type_meta = IRO_TYPE_DEFINITIONS.get(iro.iro_type, {})
            iw = type_meta.get("impact_materiality_weight", 1.0)
            fw = type_meta.get("financial_materiality_weight", 1.0)

            imp = min(self._impact_score(iro.impact_scale, iro.impact_scope, iro.impact_irremediable, iro.impact_likelihood) * iw, 1.0)
            fin = min(self._financial_score(iro.financial_likelihood, iro.financial_magnitude) * fw, 1.0)

            results.append({
                "iro_type": iro.iro_type,
                "iro_type_label": type_meta.get("label", iro.iro_type),
                "description": iro.description,
                "time_horizon": iro.time_horizon,
                "value_chain_position": iro.value_chain_position,
                "impact_materiality_score": round(imp, 4),
                "financial_materiality_score": round(fin, 4),
                "is_material_impact": imp >= self.MATERIALITY_THRESHOLD,
                "is_material_financial": fin >= self.MATERIALITY_THRESHOLD,
                "is_double_material": imp >= self.MATERIALITY_THRESHOLD or fin >= self.MATERIALITY_THRESHOLD,
                "quadrant": self._quadrant(imp, fin),
                "priority": self._iro_priority(imp, fin, iro.iro_type),
                "reporting_obligation": type_meta.get("reporting_obligation", ""),
                "input_scores": {
                    "impact_scale": iro.impact_scale,
                    "impact_scope": iro.impact_scope,
                    "impact_likelihood": iro.impact_likelihood,
                    "impact_irremediable": iro.impact_irremediable,
                    "financial_likelihood": iro.financial_likelihood,
                    "financial_magnitude": iro.financial_magnitude,
                },
            })

        material_iros = [r for r in results if r["is_double_material"]]
        top_iro = max(results, key=lambda r: r["impact_materiality_score"] + r["financial_materiality_score"], default=None)

        return {
            "entity_name": entity_name,
            "topic": topic,
            "topic_name": topic_meta.get("name", topic),
            "total_iros_assessed": len(results),
            "material_iros_count": len(material_iros),
            "iro_results": results,
            "material_iros": material_iros,
            "highest_priority_iro": top_iro,
        }

    def generate_materiality_matrix(
        self,
        entity_name: str,
        topic_scores: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate 2D materiality matrix plot data with quadrant classification."""
        plot_points: List[Dict] = []
        quadrant_counts: Dict[str, int] = {"high_high": 0, "high_low": 0, "low_high": 0, "low_low": 0}

        for ts in topic_scores:
            topic = ts.get("topic", "")
            imp = min(max(float(ts.get("impact_score", 0.0)), 0.0), 1.0)
            fin = min(max(float(ts.get("financial_score", 0.0)), 0.0), 1.0)
            topic_meta = ESRS_TOPICS.get(topic, {})
            q = self._quadrant(imp, fin)
            quadrant_counts[q] = quadrant_counts.get(q, 0) + 1

            plot_points.append({
                "topic": topic,
                "name": topic_meta.get("name", topic),
                "pillar": topic_meta.get("pillar", ""),
                "impact_materiality": round(imp, 4),
                "financial_materiality": round(fin, 4),
                "quadrant": q,
                "quadrant_label": self._quadrant_label(q),
                "is_double_material": imp >= self.MATERIALITY_THRESHOLD or fin >= self.MATERIALITY_THRESHOLD,
                "distance_from_origin": round((imp ** 2 + fin ** 2) ** 0.5, 4),
                "combined_score": round((imp + fin) / 2, 4),
            })

        plot_points.sort(key=lambda x: x["combined_score"], reverse=True)

        return {
            "entity_name": entity_name,
            "matrix_type": "ESRS 1 Double Materiality Matrix",
            "x_axis_label": "Financial Materiality (0 = not material, 1 = highly material)",
            "y_axis_label": "Impact Materiality (0 = not material, 1 = highly material)",
            "threshold_line": self.MATERIALITY_THRESHOLD,
            "total_topics": len(plot_points),
            "double_material_count": sum(1 for p in plot_points if p["is_double_material"]),
            "plot_points": plot_points,
            "quadrant_summary": quadrant_counts,
            "quadrant_definitions": {
                "high_high": "Double material — significant impact AND financial effects",
                "high_low": "Impact material only — significant impact, limited financial effect",
                "low_high": "Financial material only — financial effects, limited direct impact",
                "low_low": "Not currently material — monitor for emerging trends",
            },
        }

    def check_esrs_omissions(
        self,
        entity_name: str,
        nace_sector: str,
        topics_not_reported: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Validate omission justifications against ESRS 1 paras 29-35."""
        nace_key = self._resolve_nace_key(nace_sector)
        nace_triggers = NACE_MATERIALITY_MATRIX.get(nace_key, {})
        validation_results: List[Dict] = []
        accepted = rejected = 0

        for item in topics_not_reported:
            topic = item.get("topic", "")
            criterion = item.get("omission_criterion", "")
            justification = item.get("justification", "")
            criterion_meta = OMISSION_CRITERIA.get(criterion, {})
            topic_meta = ESRS_TOPICS.get(topic, {})
            nace_signal = nace_triggers.get(topic, "na")
            issues: List[str] = []
            warnings: List[str] = []

            has_mandatory = any(s["mandatory"] for s in topic_meta.get("sub_topics", {}).values())
            if has_mandatory and criterion in ("immaterial", "proprietary"):
                issues.append(
                    f"Topic {topic} contains mandatory DPs; omission criterion '{criterion}' cannot be applied to mandatory DPs per ESRS 1 para 34"
                )

            if not justification or len(justification.strip()) < 20:
                issues.append("Justification text insufficient (minimum 20 characters per ESRS 1 para 32)")

            if criterion_meta.get("requires_nace_evidence") and nace_signal in ("high", "medium"):
                warnings.append(
                    f"NACE sector '{nace_sector}' signals '{nace_signal}' materiality for {topic}; 'not_applicable' omission requires robust evidence"
                )

            if not criterion_meta:
                issues.append(f"Criterion '{criterion}' is not a recognised ESRS 1 omission criterion")

            status = "accepted" if not issues else "rejected"
            accepted += (1 if status == "accepted" else 0)
            rejected += (1 if status == "rejected" else 0)

            validation_results.append({
                "topic": topic,
                "topic_name": topic_meta.get("name", topic),
                "omission_criterion": criterion,
                "criterion_label": criterion_meta.get("label", criterion),
                "esrs_ref": criterion_meta.get("esrs_ref", ""),
                "justification_provided": justification,
                "nace_materiality_signal": nace_signal,
                "validation_status": status,
                "issues": issues,
                "warnings": warnings,
                "has_mandatory_dps": has_mandatory,
            })

        return {
            "entity_name": entity_name,
            "nace_sector": nace_sector,
            "total_omissions_checked": len(topics_not_reported),
            "accepted_count": accepted,
            "rejected_count": rejected,
            "overall_status": "pass" if rejected == 0 else "fail",
            "validation_results": validation_results,
            "omission_criteria_reference": OMISSION_CRITERIA,
        }

    def calculate_completeness_score(
        self,
        entity_name: str,
        topics_reported: List[str],
        dps_reported: int,
        dps_mandatory_for_sector: int,
    ) -> Dict[str, Any]:
        """Calculate completeness of mandatory DP coverage for the sector."""
        dp_coverage = min(dps_reported / max(dps_mandatory_for_sector, 1), 1.0)
        all_codes = list(ESRS_TOPICS.keys())
        reported_set = set(topics_reported)
        topic_coverage = len(reported_set & set(all_codes)) / len(all_codes)
        not_reported = [t for t in all_codes if t not in reported_set]

        if dp_coverage >= self.REASONABLE_ASSURANCE_THRESHOLD:
            tier = "reasonable_assurance_ready"
        elif dp_coverage >= self.LIMITED_ASSURANCE_THRESHOLD:
            tier = "limited_assurance_ready"
        elif dp_coverage >= 0.40:
            tier = "approaching_limited"
        else:
            tier = "not_ready"

        return {
            "entity_name": entity_name,
            "dps_reported": dps_reported,
            "dps_mandatory_for_sector": dps_mandatory_for_sector,
            "dp_coverage_pct": round(dp_coverage * 100, 2),
            "topic_coverage_pct": round(topic_coverage * 100, 2),
            "topics_reported_count": len(reported_set & set(all_codes)),
            "topics_not_reported": not_reported,
            "completeness_score": round(dp_coverage, 4),
            "assurance_tier": tier,
            "limited_assurance_threshold_pct": self.LIMITED_ASSURANCE_THRESHOLD * 100,
            "reasonable_assurance_threshold_pct": self.REASONABLE_ASSURANCE_THRESHOLD * 100,
            "assurance_criteria": ASSURANCE_CRITERIA,
            "gap_topics": not_reported,
        }

    def get_esrs_topic_metadata(self) -> Dict[str, Any]:
        """Return full ESRS topic and sub-topic reference data."""
        summary: List[Dict] = []
        for code, meta in ESRS_TOPICS.items():
            sub_list = [{"code": sc, **sm} for sc, sm in meta["sub_topics"].items()]
            summary.append({
                "topic": code,
                "name": meta["name"],
                "pillar": meta["pillar"],
                "standard": meta["standard"],
                "sub_topic_count": len(sub_list),
                "mandatory_sub_topics": sum(1 for s in meta["sub_topics"].values() if s["mandatory"]),
                "sub_topics": sub_list,
            })
        return {
            "esrs_topics": summary,
            "total_topics": len(summary),
            "total_sub_topics": sum(len(m["sub_topics"]) for m in ESRS_TOPICS.values()),
            "mandatory_sub_topics_total": sum(
                1 for m in ESRS_TOPICS.values()
                for s in m["sub_topics"].values() if s["mandatory"]
            ),
        }

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    def _score_from_assessment(self, a: TopicAssessment) -> Tuple[float, float]:
        imp = self._impact_score(a.impact_scale, a.impact_scope, a.impact_irremediable, a.impact_likelihood)
        fin = self._financial_score(a.financial_likelihood, a.financial_magnitude)
        return imp, fin

    def _impact_score(self, scale: int, scope: int, irremediable: int, likelihood: int) -> float:
        """ESRS 1 impact materiality = max(severity path, risk path) normalised 0-1."""
        severity_path = (scale * scope * irremediable) / 125.0   # max 5x5x5=125
        risk_path = (likelihood * scale) / 25.0                  # max 5x5=25
        return min(max(severity_path, risk_path), 1.0)

    def _financial_score(self, likelihood: int, magnitude: int) -> float:
        """ESRS 1 financial materiality = likelihood x magnitude normalised 0-1."""
        return min((likelihood * magnitude) / 25.0, 1.0)

    def _nace_baseline_scores(self, signal: str) -> Tuple[float, float]:
        """Convert NACE materiality signal to indicative baseline scores."""
        mapping = {
            "high":   (0.72, 0.65),
            "medium": (0.46, 0.42),
            "low":    (0.20, 0.18),
            "na":     (0.05, 0.04),
        }
        return mapping.get(signal, (0.05, 0.04))

    def _quadrant(self, imp: float, fin: float) -> str:
        t = self.MATERIALITY_THRESHOLD
        if imp >= t and fin >= t:
            return "high_high"
        if imp >= t:
            return "high_low"
        if fin >= t:
            return "low_high"
        return "low_low"

    def _quadrant_label(self, quadrant: str) -> str:
        return {
            "high_high": "Double Material",
            "high_low":  "Impact Material",
            "low_high":  "Financial Material",
            "low_low":   "Not Currently Material",
        }.get(quadrant, quadrant)

    def _iro_priority(self, imp: float, fin: float, iro_type: str) -> str:
        combined = (imp + fin) / 2
        if combined >= 0.70 or iro_type == "actual_negative_impact":
            return "critical"
        if combined >= 0.50:
            return "high"
        if combined >= 0.35:
            return "medium"
        return "low"

    def _estimate_completeness(self, material_count: int, assessed_count: int) -> float:
        if material_count == 0:
            return 1.0
        return min(assessed_count / max(material_count, 1), 1.0)

    def _assess_assurance_readiness(self, completeness: float, assessed_count: int) -> Dict[str, Any]:
        score = completeness * 0.60 + min(assessed_count / 10, 1.0) * 0.40
        if score >= self.REASONABLE_ASSURANCE_THRESHOLD:
            tier = "reasonable_assurance_ready"
        elif score >= self.LIMITED_ASSURANCE_THRESHOLD:
            tier = "limited_assurance_ready"
        elif score >= 0.40:
            tier = "approaching_limited"
        else:
            tier = "not_ready"
        return {
            "score": round(score, 4),
            "tier": tier,
            "limited_assurance_threshold": self.LIMITED_ASSURANCE_THRESHOLD,
            "reasonable_assurance_threshold": self.REASONABLE_ASSURANCE_THRESHOLD,
            "criteria": ASSURANCE_CRITERIA,
        }

    def _infer_wave(self, employee_count: int) -> int:
        if employee_count > 500:
            return 1
        if employee_count > 250:
            return 2
        return 3

    def _has_relief(self, topic: str, reporting_year: int, wave: int) -> bool:
        wave_data = next((w for w in CSRD_WAVE_TIMELINE if w["wave"] == wave), None)
        if not wave_data:
            return False
        return topic in wave_data.get("first_year_relief", []) and reporting_year == wave_data["reporting_year"]

    def _resolve_nace_key(self, nace_sector: str) -> str:
        """Resolve full NACE code to best available matrix key."""
        if nace_sector in NACE_MATERIALITY_MATRIX:
            return nace_sector
        # Try 3-char prefix (e.g. "C20" from "C2010")
        if len(nace_sector) >= 3 and nace_sector[:3] in NACE_MATERIALITY_MATRIX:
            return nace_sector[:3]
        # Fall back to section letter
        section = (nace_sector[0].upper() if nace_sector else "C")
        return section if section in NACE_MATERIALITY_MATRIX else "C"
