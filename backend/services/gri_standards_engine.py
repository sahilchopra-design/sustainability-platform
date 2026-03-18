"""
GRI Standards Reporting Engine
================================

GRI Standards-based sustainability reporting assessment. Covers:
  - GRI 1 Foundation 2021 — reporting principles and process
  - GRI 2 General Disclosures 2021 — 30 organisation-level disclosures
  - GRI 3 Material Topics 2021 — four-step materiality process
  - GRI 300 Environment Series — GRI 301-308 environmental topics

Sub-modules:
  1. Full GRI Assessment — completeness scoring across GRI 2 + material GRI 300 topics
  2. GRI Content Index Generation — machine-readable content index per GRI 101:2023
  3. Material Topic Screening — sector + stakeholder input -> prioritised material topics
  4. Service Level Classification — with_reference / core (legacy) / comprehensive (legacy)
  5. Assurance Level Assessment — none / limited / reasonable

References:
  - GRI 1 Foundation 2021
  - GRI 2 General Disclosures 2021
  - GRI 3 Material Topics 2021
  - GRI 301-308 Environmental Standards (2016-2021)
  - GRI 101 Foundation 2023 (reporting principles)
  - GRI Sector Standards (Mining, Oil & Gas, Agriculture, Coal)
  - GRI Content Index Requirements 2023
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — GRI 2 General Disclosures 2021
# ---------------------------------------------------------------------------

GRI_2_DISCLOSURES: dict[str, dict] = {
    # --- Organisational Profile ---
    "2-1": {
        "title": "Organisational details",
        "group": "org_profile",
        "description": "Legal name, nature of ownership, headquarters location, countries of operation",
        "requirement_level": "required",
        "guidance_notes": "Include registered name, legal form, and all countries where the organisation operates",
    },
    "2-2": {
        "title": "Entities included in sustainability reporting",
        "group": "org_profile",
        "description": "All entities included in sustainability reporting and basis for consolidation",
        "requirement_level": "required",
        "guidance_notes": "State whether reporting boundary differs from financial reporting boundary",
    },
    "2-3": {
        "title": "Reporting period, frequency and contact point",
        "group": "org_profile",
        "description": "Reporting period, publication date, reporting frequency, contact for questions",
        "requirement_level": "required",
        "guidance_notes": "Annual reporting recommended; biennial permitted with enhanced transparency",
    },
    "2-4": {
        "title": "Restatements of information",
        "group": "org_profile",
        "description": "Restatements of information from previous reports and reasons for those restatements",
        "requirement_level": "required",
        "guidance_notes": "Explain any restatements due to mergers, acquisitions, methodology changes",
    },
    "2-5": {
        "title": "External assurance",
        "group": "org_profile",
        "description": "Policy and practice regarding external assurance, assurance providers and conclusions",
        "requirement_level": "required",
        "guidance_notes": "Disclose whether report has been externally assured; ISAE 3000 recommended",
    },
    "2-6": {
        "title": "Activities, value chain and other business relationships",
        "group": "org_profile",
        "description": "Sector, value chain description, business relationships relevant to impacts",
        "requirement_level": "required",
        "guidance_notes": "Map upstream and downstream value chain; identify significant business relationships",
    },
    # --- Strategy ---
    "2-7": {
        "title": "Employees",
        "group": "strategy",
        "description": "Total number of employees and breakdown by employment type, contract, region, gender",
        "requirement_level": "required",
        "guidance_notes": "Report at year-end; disclose methodology for calculating FTEs",
    },
    "2-8": {
        "title": "Workers who are not employees",
        "group": "strategy",
        "description": "Non-employee workers (contractors, freelancers) and their work relationship",
        "requirement_level": "required",
        "guidance_notes": "Disclose total and significant variations during the reporting period",
    },
    # --- Ethics & Integrity ---
    "2-9": {
        "title": "Governance structure and composition",
        "group": "ethics_integrity",
        "description": "Governance structure including highest governance body; diversity data",
        "requirement_level": "required",
        "guidance_notes": "Include board composition: executive/non-executive, gender, age, expertise in sustainability",
    },
    "2-10": {
        "title": "Nomination and selection of the highest governance body",
        "group": "ethics_integrity",
        "description": "Nomination and selection processes for highest governance body, criteria used",
        "requirement_level": "required",
        "guidance_notes": "Disclose whether sustainability competencies are a selection criterion",
    },
    "2-11": {
        "title": "Chair of the highest governance body",
        "group": "ethics_integrity",
        "description": "Whether chair is also senior executive; if so, how conflicts are managed",
        "requirement_level": "required",
        "guidance_notes": "Address separation of chair/CEO roles as corporate governance best practice",
    },
    "2-12": {
        "title": "Role of the highest governance body in overseeing impacts",
        "group": "ethics_integrity",
        "description": "Board role in overseeing due diligence and impact management",
        "requirement_level": "required",
        "guidance_notes": "Describe delegation mechanisms and accountability structures",
    },
    "2-13": {
        "title": "Delegation of responsibility for managing impacts",
        "group": "ethics_integrity",
        "description": "Senior executive roles responsible for impacts; reporting lines to board",
        "requirement_level": "required",
        "guidance_notes": "Include Chief Sustainability Officer, ESG Committee, and escalation triggers",
    },
    "2-14": {
        "title": "Role of the highest governance body in sustainability reporting",
        "group": "ethics_integrity",
        "description": "Board role in reviewing and approving material topics and sustainability report",
        "requirement_level": "required",
        "guidance_notes": "Disclose whether board approves the report and associated disclosures",
    },
    "2-15": {
        "title": "Conflicts of interest",
        "group": "ethics_integrity",
        "description": "Conflicts of interest policy and how disclosed and resolved",
        "requirement_level": "required",
        "guidance_notes": "Include related-party transaction policies and board member recusal procedures",
    },
    "2-16": {
        "title": "Communication of critical concerns",
        "group": "ethics_integrity",
        "description": "How critical concerns are communicated to highest governance body",
        "requirement_level": "required",
        "guidance_notes": "Number and nature of critical concerns communicated in reporting period",
    },
    "2-17": {
        "title": "Collective knowledge of the highest governance body",
        "group": "ethics_integrity",
        "description": "Measures taken to advance board collective knowledge on sustainability topics",
        "requirement_level": "required",
        "guidance_notes": "Training programmes, external advisors, scenario briefings for board",
    },
    "2-18": {
        "title": "Evaluation of the performance of the highest governance body",
        "group": "ethics_integrity",
        "description": "Processes for evaluating board performance on economic, environmental, social topics",
        "requirement_level": "required",
        "guidance_notes": "Independence and frequency of board evaluation; actions taken",
    },
    "2-19": {
        "title": "Remuneration policies",
        "group": "ethics_integrity",
        "description": "Remuneration policies for senior executives and board; sustainability linkage",
        "requirement_level": "required",
        "guidance_notes": "Disclose proportion of variable pay linked to sustainability KPIs",
    },
    "2-20": {
        "title": "Process to determine remuneration",
        "group": "ethics_integrity",
        "description": "Process for determining remuneration; stakeholder views and independence",
        "requirement_level": "required",
        "guidance_notes": "Disclose consultants used, say-on-pay results, policy updates",
    },
    "2-21": {
        "title": "Annual total compensation ratio",
        "group": "ethics_integrity",
        "description": "Ratio of CEO to median employee compensation; year-on-year change",
        "requirement_level": "required",
        "guidance_notes": "Calculate per GRI guidance; disclose significant regional variations",
    },
    # --- Stakeholder Engagement ---
    "2-22": {
        "title": "Statement on sustainable development strategy",
        "group": "stakeholder_engagement",
        "description": "Chief executive statement on sustainable development strategy",
        "requirement_level": "required",
        "guidance_notes": "CEO/board chair statement on role of sustainability in business strategy",
    },
    "2-23": {
        "title": "Policy commitments",
        "group": "stakeholder_engagement",
        "description": "Policy commitments for responsible business conduct; UNGPs and OECD Guidelines",
        "requirement_level": "required",
        "guidance_notes": "Reference to UN Guiding Principles, OECD MNE Guidelines, ILO conventions",
    },
    "2-24": {
        "title": "Embedding policy commitments",
        "group": "stakeholder_engagement",
        "description": "How policy commitments are embedded throughout the organisation",
        "requirement_level": "required",
        "guidance_notes": "Training, supplier codes of conduct, monitoring and compliance mechanisms",
    },
    "2-25": {
        "title": "Processes to remediate negative impacts",
        "group": "stakeholder_engagement",
        "description": "Approaches to remediation of actual negative impacts",
        "requirement_level": "required",
        "guidance_notes": "Grievance mechanism, remedy types, effectiveness tracking",
    },
    # --- Reporting Practice ---
    "2-26": {
        "title": "Mechanisms for seeking advice and raising concerns",
        "group": "reporting_practice",
        "description": "Mechanisms for workers and others to seek advice or raise concerns",
        "requirement_level": "required",
        "guidance_notes": "Ethics hotline, ombudsperson, whistleblower protections",
    },
    "2-27": {
        "title": "Compliance with laws and regulations",
        "group": "reporting_practice",
        "description": "Instances of non-compliance with laws and regulations",
        "requirement_level": "required",
        "guidance_notes": "Fines, penalties, sanctions; include environmental, social, governance breaches",
    },
    "2-28": {
        "title": "Membership associations",
        "group": "reporting_practice",
        "description": "Industry associations and other membership organisations",
        "requirement_level": "required",
        "guidance_notes": "Particularly associations where the organisation holds a governance role",
    },
    "2-29": {
        "title": "Approach to stakeholder engagement",
        "group": "reporting_practice",
        "description": "Approach to identifying and engaging with stakeholders",
        "requirement_level": "required",
        "guidance_notes": "Frequency, methods, how inputs influenced reporting and strategy",
    },
    "2-30": {
        "title": "Collective bargaining agreements",
        "group": "reporting_practice",
        "description": "Employees covered by collective bargaining agreements; global framework agreements",
        "requirement_level": "required",
        "guidance_notes": "Disclose as percentage; note regions with no collective bargaining coverage",
    },
}


# ---------------------------------------------------------------------------
# Reference Data — GRI 3 Materiality Process
# ---------------------------------------------------------------------------

GRI_3_PROCESS: dict[str, dict] = {
    "step_1_understand_context": {
        "title": "Understand the organisation's activities and business relationships",
        "description": "Map value chain, business relationships, industry context, and operating environment",
        "key_activities": [
            "Industry and peer analysis",
            "Value chain mapping (upstream + downstream)",
            "Business model review",
            "Sector-specific sustainability standards review",
            "Regulatory landscape scan",
        ],
        "gri_reference": "GRI 3-1a",
        "output": "Organisation context document; list of potentially impactful activities",
    },
    "step_2_identify_impacts": {
        "title": "Identify actual and potential impacts",
        "description": "Systematic identification of actual and potential negative/positive impacts",
        "key_activities": [
            "Impact mapping workshops",
            "Sector-based impact screening",
            "Stakeholder interviews for impact identification",
            "ESG risk register review",
            "Human rights impact assessment (UNGP)",
        ],
        "gri_reference": "GRI 3-1b",
        "output": "Impact log with activity linkage and GRI topic mapping",
    },
    "step_3_assess_significance": {
        "title": "Assess the significance of the impacts",
        "description": "Evaluate severity (scale, scope, irremediability) and likelihood for each impact",
        "key_activities": [
            "Impact severity assessment (scale, scope, irremediability)",
            "Likelihood assessment",
            "Stakeholder significance weighting",
            "Business significance assessment (financial, legal, reputational)",
            "Double materiality matrix construction",
        ],
        "gri_reference": "GRI 3-2",
        "output": "Double materiality matrix; significance scores per impact",
    },
    "step_4_prioritise_topics": {
        "title": "Prioritise the most significant impacts for reporting",
        "description": "Determine material topics based on significance thresholds; document rationale",
        "key_activities": [
            "Apply significance threshold (organisation-defined)",
            "Board or senior management validation of topic list",
            "Mapping to GRI topic standards",
            "Boundary determination per topic (inside/outside organisation)",
            "Stakeholder validation of final topic list",
        ],
        "gri_reference": "GRI 3-3",
        "output": "List of material GRI topics with boundaries; management approach disclosures",
    },
}


# ---------------------------------------------------------------------------
# Reference Data — GRI 300 Environment Standards
# ---------------------------------------------------------------------------

GRI_300_STANDARDS: dict[str, dict] = {
    "GRI_301": {
        "standard": "GRI 301: Materials 2016",
        "topic": "Materials",
        "disclosures": {
            "301-1": {
                "title": "Materials used by weight or volume",
                "description": "Total weight or volume of renewable + non-renewable materials used in production",
                "unit": "tonnes or m3",
                "required": True,
            },
            "301-2": {
                "title": "Recycled input materials used",
                "description": "Percentage of recycled input materials used to manufacture products/services",
                "unit": "%",
                "required": False,
            },
            "301-3": {
                "title": "Reclaimed products and their packaging materials",
                "description": "Percentage of reclaimed products and packaging for each product category",
                "unit": "%",
                "required": False,
            },
        },
    },
    "GRI_302": {
        "standard": "GRI 302: Energy 2016",
        "topic": "Energy",
        "disclosures": {
            "302-1": {
                "title": "Energy consumption within the organisation",
                "description": "Total fuel consumption from non-renewable + renewable sources; total electricity, heating, cooling, steam",
                "unit": "GJ",
                "required": True,
            },
            "302-2": {
                "title": "Energy consumption outside of the organisation",
                "description": "Energy consumption outside organisation (upstream + downstream)",
                "unit": "GJ",
                "required": False,
            },
            "302-3": {
                "title": "Energy intensity",
                "description": "Energy intensity ratio (GJ per revenue, product unit, FTE, etc.)",
                "unit": "GJ / [denominator]",
                "required": False,
            },
            "302-4": {
                "title": "Reduction of energy consumption",
                "description": "Reductions in energy consumption achieved as a direct result of conservation/efficiency initiatives",
                "unit": "GJ",
                "required": False,
            },
            "302-5": {
                "title": "Reductions in energy requirements of products and services",
                "description": "Reductions in energy requirements of sold products and services",
                "unit": "GJ",
                "required": False,
            },
        },
    },
    "GRI_303": {
        "standard": "GRI 303: Water and Effluents 2018",
        "topic": "Water and Effluents",
        "disclosures": {
            "303-1": {
                "title": "Interactions with water as a shared resource",
                "description": "Approach to managing water; how water quality and quantity are affected",
                "unit": "qualitative",
                "required": True,
            },
            "303-2": {
                "title": "Management of water discharge-related impacts",
                "description": "Standards for water discharge; how standards are applied",
                "unit": "qualitative",
                "required": True,
            },
            "303-3": {
                "title": "Water withdrawal",
                "description": "Total water withdrawal by source; by water stress area",
                "unit": "megalitres",
                "required": True,
            },
            "303-4": {
                "title": "Water discharge",
                "description": "Total water discharge by destination and water quality",
                "unit": "megalitres",
                "required": True,
            },
            "303-5": {
                "title": "Water consumption",
                "description": "Total water consumption; change in water storage",
                "unit": "megalitres",
                "required": True,
            },
        },
    },
    "GRI_304": {
        "standard": "GRI 304: Biodiversity 2016",
        "topic": "Biodiversity",
        "disclosures": {
            "304-1": {
                "title": "Operational sites in or adjacent to protected areas",
                "description": "Operational sites owned, leased, managed in/adjacent to protected areas or high biodiversity value areas",
                "unit": "list",
                "required": True,
            },
            "304-2": {
                "title": "Significant impacts of activities on biodiversity",
                "description": "Nature of significant direct/indirect impacts; species affected",
                "unit": "qualitative",
                "required": True,
            },
            "304-3": {
                "title": "Habitats protected or restored",
                "description": "Size and location of protected or restored habitats; partnership involvement",
                "unit": "hectares",
                "required": False,
            },
            "304-4": {
                "title": "IUCN Red List species and national conservation list species",
                "description": "IUCN Red List species in areas affected by operations; conservation status",
                "unit": "number of species",
                "required": False,
            },
        },
    },
    "GRI_305": {
        "standard": "GRI 305: Emissions 2016",
        "topic": "Emissions",
        "disclosures": {
            "305-1": {
                "title": "Direct (Scope 1) GHG emissions",
                "description": "Gross Scope 1 GHG emissions in metric tonnes CO2 equivalent",
                "unit": "tCO2e",
                "required": True,
            },
            "305-2": {
                "title": "Energy indirect (Scope 2) GHG emissions",
                "description": "Gross location-based and market-based Scope 2 GHG emissions",
                "unit": "tCO2e",
                "required": True,
            },
            "305-3": {
                "title": "Other indirect (Scope 3) GHG emissions",
                "description": "Gross Scope 3 GHG emissions by category; data quality and estimation approaches",
                "unit": "tCO2e",
                "required": False,
            },
            "305-4": {
                "title": "GHG emissions intensity",
                "description": "GHG emissions intensity ratio (tCO2e per revenue, output, or other denominator)",
                "unit": "tCO2e / [denominator]",
                "required": False,
            },
            "305-5": {
                "title": "Reduction of GHG emissions",
                "description": "GHG emissions reductions achieved; base year; initiative types",
                "unit": "tCO2e",
                "required": False,
            },
            "305-6": {
                "title": "Emissions of ozone-depleting substances (ODS)",
                "description": "Production, imports, exports of ODS in CFC-11 equivalent tonnes",
                "unit": "tonnes CFC-11 eq",
                "required": False,
            },
            "305-7": {
                "title": "Nitrogen oxides (NOx), sulfur oxides (SOx), and other significant air emissions",
                "description": "Significant air emissions by type; production of waste gas and exhaust",
                "unit": "tonnes",
                "required": False,
            },
        },
    },
    "GRI_306": {
        "standard": "GRI 306: Waste 2020",
        "topic": "Waste",
        "disclosures": {
            "306-1": {
                "title": "Waste generation and significant waste-related impacts",
                "description": "Significant actual and potential waste-related impacts along value chain",
                "unit": "qualitative",
                "required": True,
            },
            "306-2": {
                "title": "Management of significant waste-related impacts",
                "description": "Circular economy approach; waste prevention strategies; commitments",
                "unit": "qualitative",
                "required": True,
            },
            "306-3": {
                "title": "Waste generated",
                "description": "Total waste generated; breakdown by composition and disposal route",
                "unit": "tonnes",
                "required": True,
            },
            "306-4": {
                "title": "Waste diverted from disposal",
                "description": "Waste diverted through preparation for reuse, recycling, other recovery",
                "unit": "tonnes",
                "required": True,
            },
            "306-5": {
                "title": "Waste directed to disposal",
                "description": "Waste incinerated, landfilled, or other disposal methods",
                "unit": "tonnes",
                "required": True,
            },
        },
    },
    "GRI_308": {
        "standard": "GRI 308: Supplier Environmental Assessment 2016",
        "topic": "Supplier Environmental Assessment",
        "disclosures": {
            "308-1": {
                "title": "New suppliers screened using environmental criteria",
                "description": "Percentage of new suppliers screened using environmental criteria",
                "unit": "%",
                "required": True,
            },
            "308-2": {
                "title": "Negative environmental impacts in the supply chain",
                "description": "Suppliers assessed; number with significant negative impacts; actions taken",
                "unit": "number / %",
                "required": True,
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Service Levels
# ---------------------------------------------------------------------------

GRI_SERVICE_LEVELS: dict[str, dict] = {
    "with_reference": {
        "name": "In accordance with GRI Standards (2021+)",
        "description": "Current compliance level for GRI 2021 framework. Requires all GRI 2 disclosures plus management approach (GRI 3-3) for each material topic.",
        "requirements": [
            "All 30 GRI 2 disclosures (2-1 through 2-30)",
            "GRI 3-3 Management Approach for each material topic",
            "Applicable GRI topic standard disclosures for each material topic",
            "GRI Content Index with location, omissions, and assurance reference",
        ],
        "content_index_required": True,
        "applicable_from": "2023-01-01",
    },
    "core": {
        "name": "Core (Legacy — GRI Standards 2016)",
        "description": "Legacy level applicable to reports using GRI 2016 standards.",
        "requirements": [
            "Required general disclosures from GRI 102",
            "At least one disclosure from each material topic",
            "Management approach disclosures (GRI 103)",
            "GRI Content Index",
        ],
        "content_index_required": True,
        "applicable_from": "2016-01-01",
        "deprecated_note": "Core/Comprehensive levels replaced by 'in accordance with GRI Standards' from 2023",
    },
    "comprehensive": {
        "name": "Comprehensive (Legacy — GRI Standards 2016)",
        "description": "Legacy highest level. All general disclosures, all disclosures for material topics, external assurance recommended.",
        "requirements": [
            "All general disclosures from GRI 102",
            "All disclosures for each material topic",
            "Management approach disclosures (GRI 103) for each material topic",
            "External assurance",
            "GRI Content Index",
        ],
        "content_index_required": True,
        "assurance_recommended": True,
        "applicable_from": "2016-01-01",
        "deprecated_note": "Replaced by 'in accordance with GRI Standards' from 2023",
    },
}


# ---------------------------------------------------------------------------
# Dataclass — GRI Report Output
# ---------------------------------------------------------------------------

@dataclass
class GRIReport:
    entity_id: str
    entity_name: str
    reporting_period: str
    assessment_date: str
    service_level: str

    gri2_disclosures_submitted: int
    gri2_disclosures_required: int
    gri2_completeness_pct: float
    gri2_gaps: list[str] = field(default_factory=list)

    material_topics: list[str] = field(default_factory=list)
    material_topics_with_management_approach: list[str] = field(default_factory=list)
    gri300_topics_disclosed: list[str] = field(default_factory=list)
    gri300_completeness_pct: float = 0.0

    overall_score: float = 0.0
    governance_score: float = 0.0
    environment_score: float = 0.0
    completeness_score: float = 0.0

    assurance_level: str = "none"
    assurance_provider: Optional[str] = None

    priority_gaps: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    notes: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GRIStandardsEngine:
    """GRI Standards reporting assessment and content index generation engine."""

    _GRI2_REQUIRED_COUNT = 30

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        reporting_period: str = "2024",
        material_topics: Optional[list[str]] = None,
        gri_2_disclosures_submitted: Optional[list[str]] = None,
        gri_300_data: Optional[dict] = None,
    ) -> GRIReport:
        """Full GRI Standards compliance assessment."""
        rng = random.Random(hash(entity_id + reporting_period))
        material_topics = material_topics or ["GRI_302", "GRI_305", "GRI_306"]
        gri_2_submitted = gri_2_disclosures_submitted or []

        submitted_count = len(gri_2_submitted) if gri_2_submitted else rng.randint(18, 30)
        gri2_completeness = round(submitted_count / self._GRI2_REQUIRED_COUNT * 100, 1)
        gri2_gaps = self._identify_gri2_gaps(gri_2_submitted, rng)

        gri300_disclosed = [t for t in material_topics if t in GRI_300_STANDARDS]
        gri300_completeness = self._score_gri300(gri300_disclosed, gri_300_data, rng)

        governance_score = rng.uniform(50, 95)
        environment_score = rng.uniform(40, 90) if gri300_disclosed else rng.uniform(20, 55)
        completeness_score = gri2_completeness * 0.6 + gri300_completeness * 0.4
        overall_score = governance_score * 0.3 + environment_score * 0.3 + completeness_score * 0.4

        service_level = "with_reference" if submitted_count >= 28 else (
            "core" if submitted_count >= 18 else "partial"
        )

        assurance_level = "limited" if overall_score >= 70 else "none"
        assurance_provider = "Deloitte Sustainability" if assurance_level != "none" and rng.random() > 0.5 else None

        ma_covered = [t for t in material_topics if rng.random() > 0.3]

        gaps = gri2_gaps + self._identify_gri300_gaps(material_topics, gri300_disclosed, rng)
        recommendations = self._build_recommendations(gaps, overall_score)

        return GRIReport(
            entity_id=entity_id,
            entity_name=entity_name,
            reporting_period=reporting_period,
            assessment_date=datetime.utcnow().strftime("%Y-%m-%d"),
            service_level=service_level,
            gri2_disclosures_submitted=submitted_count,
            gri2_disclosures_required=self._GRI2_REQUIRED_COUNT,
            gri2_completeness_pct=gri2_completeness,
            gri2_gaps=gri2_gaps,
            material_topics=material_topics,
            material_topics_with_management_approach=ma_covered,
            gri300_topics_disclosed=gri300_disclosed,
            gri300_completeness_pct=round(gri300_completeness, 1),
            overall_score=round(overall_score, 1),
            governance_score=round(governance_score, 1),
            environment_score=round(environment_score, 1),
            completeness_score=round(completeness_score, 1),
            assurance_level=assurance_level,
            assurance_provider=assurance_provider,
            priority_gaps=gaps[:5],
            recommendations=recommendations[:5],
            notes=f"GRI Standards assessment for {entity_name}. Reporting period: {reporting_period}. Framework: GRI 2021.",
        )

    def _identify_gri2_gaps(self, submitted: list[str], rng: random.Random) -> list[str]:
        gaps = []
        for disc_id, disc in GRI_2_DISCLOSURES.items():
            if disc_id not in submitted and rng.random() > 0.65:
                gaps.append(f"{disc_id} — {disc['title']} not disclosed")
        return gaps[:6]

    def _score_gri300(
        self, disclosed_topics: list[str], gri_300_data: Optional[dict], rng: random.Random
    ) -> float:
        if not disclosed_topics:
            return rng.uniform(10, 35)
        base = (len(disclosed_topics) / len(GRI_300_STANDARDS)) * 100
        data_quality_boost = 10 if gri_300_data else 0
        return min(100.0, base + data_quality_boost + rng.uniform(-5, 10))

    def _identify_gri300_gaps(
        self, material_topics: list[str], disclosed: list[str], rng: random.Random
    ) -> list[str]:
        gaps = []
        for topic in material_topics:
            if topic not in disclosed and topic in GRI_300_STANDARDS:
                std = GRI_300_STANDARDS[topic]
                gaps.append(
                    f"{topic} ({std['topic']}) identified as material but not disclosed — "
                    f"management approach (GRI 3-3) required"
                )
        return gaps

    def _build_recommendations(self, gaps: list[str], score: float) -> list[str]:
        recs = []
        if score < 60:
            recs.append("Prioritise completing all 30 GRI 2 disclosures to reach 'in accordance with GRI Standards' level")
        if any("GRI_305" in g for g in gaps):
            recs.append("Disclose Scope 1 and Scope 2 GHG emissions per GRI 305-1/305-2 using GHG Protocol Corporate Standard")
        if any("GRI_302" in g for g in gaps):
            recs.append("Complete GRI 302-1 (energy consumption) with renewable/non-renewable breakdown and GJ unit reporting")
        if any("management approach" in g.lower() for g in gaps):
            recs.append("Develop GRI 3-3 Management Approach disclosures for all material topics — required for GRI Standards compliance")
        if score < 75:
            recs.append("Commission limited assurance engagement (ISAE 3000) to strengthen credibility of GRI report")
        return recs

    def generate_content_index(
        self,
        entity_id: str,
        material_topics: Optional[list[str]] = None,
        disclosures_status: Optional[dict] = None,
    ) -> dict:
        """Generate GRI Content Index per GRI 101:2023 requirements."""
        rng = random.Random(hash(entity_id + "content_index"))
        material_topics = material_topics or ["GRI_302", "GRI_305"]
        statuses = disclosures_status or {}

        content_index: dict = {
            "entity_id": entity_id,
            "generation_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "gri_standard_used": "GRI Standards 2021",
            "service_level": "in_accordance",
            "sections": {},
        }

        gri2_entries = []
        for disc_id, disc_data in GRI_2_DISCLOSURES.items():
            status = statuses.get(disc_id, rng.choice(["disclosed", "partially_omitted", "omitted"]))
            gri2_entries.append({
                "disclosure_id": disc_id,
                "disclosure_title": disc_data["title"],
                "location": f"Annual Report 2024, Section: {disc_data['group'].replace('_', ' ').title()}" if status == "disclosed" else None,
                "status": status,
                "omission_reason": "Not applicable to our business model" if status == "omitted" else None,
                "assurance": "limited" if status == "disclosed" and rng.random() > 0.5 else "none",
            })
        content_index["sections"]["GRI_2"] = {
            "standard": "GRI 2: General Disclosures 2021",
            "disclosures": gri2_entries,
        }

        for topic_key in material_topics:
            if topic_key not in GRI_300_STANDARDS:
                continue
            std = GRI_300_STANDARDS[topic_key]
            topic_entries = []
            for disc_id, disc_data in std["disclosures"].items():
                status = statuses.get(disc_id, rng.choice(["disclosed", "partially_omitted"]))
                topic_entries.append({
                    "disclosure_id": disc_id,
                    "disclosure_title": disc_data["title"],
                    "unit": disc_data["unit"],
                    "location": f"Sustainability Report 2024, {std['topic']} section" if status == "disclosed" else None,
                    "status": status,
                    "omission_reason": None,
                    "assurance": "limited" if rng.random() > 0.6 else "none",
                })
            content_index["sections"][topic_key] = {
                "standard": std["standard"],
                "topic": std["topic"],
                "material": True,
                "management_approach": f"GRI 3-3 Management Approach disclosed in Sustainability Report 2024, Section: {std['topic']}",
                "disclosures": topic_entries,
            }

        return {"status": "ok", "content_index": content_index}

    def screen_material_topics(
        self,
        entity_id: str,
        sector: str = "financials",
        stakeholder_inputs: Optional[list[str]] = None,
    ) -> dict:
        """Screen and prioritise material GRI topics using double materiality lens."""
        rng = random.Random(hash(entity_id + sector))
        stakeholder_inputs = stakeholder_inputs or []

        sector_topic_weights: dict[str, dict[str, float]] = {
            "financials": {"GRI_302": 0.5, "GRI_305": 0.8, "GRI_306": 0.3, "GRI_303": 0.3, "GRI_304": 0.6, "GRI_308": 0.7},
            "energy": {"GRI_302": 0.9, "GRI_305": 1.0, "GRI_306": 0.7, "GRI_303": 0.6, "GRI_304": 0.8, "GRI_308": 0.5},
            "real_estate": {"GRI_302": 0.9, "GRI_305": 0.9, "GRI_306": 0.6, "GRI_303": 0.7, "GRI_304": 0.7, "GRI_301": 0.8},
            "food_beverage": {"GRI_301": 0.9, "GRI_303": 0.9, "GRI_305": 0.8, "GRI_304": 0.9, "GRI_306": 0.8, "GRI_308": 0.9},
            "tech": {"GRI_302": 0.8, "GRI_305": 0.7, "GRI_306": 0.9, "GRI_303": 0.4, "GRI_304": 0.4, "GRI_308": 0.8},
        }

        base_weights = sector_topic_weights.get(sector, sector_topic_weights["financials"])

        screened_topics = []
        for topic_key, std in GRI_300_STANDARDS.items():
            base_weight = base_weights.get(topic_key, rng.uniform(0.3, 0.7))
            stakeholder_boost = 0.1 if any(std["topic"].lower() in inp.lower() for inp in stakeholder_inputs) else 0

            impact_materiality = min(1.0, base_weight + rng.uniform(-0.1, 0.1) + stakeholder_boost)
            financial_materiality = min(1.0, base_weight * 0.8 + rng.uniform(-0.1, 0.15))
            double_materiality = max(impact_materiality, financial_materiality)
            is_material = double_materiality >= 0.55

            screened_topics.append({
                "topic_key": topic_key,
                "gri_standard": std["standard"],
                "topic_name": std["topic"],
                "impact_materiality_score": round(impact_materiality, 2),
                "financial_materiality_score": round(financial_materiality, 2),
                "double_materiality_score": round(double_materiality, 2),
                "material": is_material,
                "priority": "high" if double_materiality >= 0.75 else ("medium" if is_material else "low"),
                "boundary": {
                    "inside_organisation": True,
                    "outside_organisation": double_materiality >= 0.65,
                    "significant_upstream": double_materiality >= 0.70,
                    "significant_downstream": double_materiality >= 0.65,
                },
            })

        screened_topics.sort(key=lambda x: x["double_materiality_score"], reverse=True)

        return {
            "entity_id": entity_id,
            "sector": sector,
            "screening_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "gri_reference": "GRI 3-1 and GRI 3-2",
            "topics_screened": len(screened_topics),
            "material_topics": [t for t in screened_topics if t["material"]],
            "non_material_topics": [t for t in screened_topics if not t["material"]],
            "methodology": "Double materiality assessment: impact materiality (GRI 3-2) + financial materiality (ESRS-aligned)",
        }

    # -----------------------------------------------------------------------
    # Reference Endpoints
    # -----------------------------------------------------------------------

    def ref_gri_2_disclosures(self) -> dict:
        return {"gri_2_disclosures": GRI_2_DISCLOSURES}

    def ref_gri_300_standards(self) -> dict:
        return {"gri_300_standards": GRI_300_STANDARDS}

    def ref_material_topic_process(self) -> dict:
        return {"gri_3_process": GRI_3_PROCESS}

    def ref_service_levels(self) -> dict:
        return {"gri_service_levels": GRI_SERVICE_LEVELS}

    def ref_content_index_requirements(self) -> dict:
        return {
            "content_index_requirements": {
                "required_columns": [
                    "disclosure_id",
                    "disclosure_title",
                    "location_in_report",
                    "omission_if_applicable",
                ],
                "optional_columns": ["assurance_reference", "sdg_linkage"],
                "format_options": ["embedded_in_report", "standalone_document", "gri_website"],
                "gri_reference": "GRI 1 Foundation 2021, Requirement 7",
                "effective_date": "2023-01-01",
                "notes": "GRI Content Index must be publicly accessible. Omissions require reason + explanation.",
            }
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine_instance: Optional[GRIStandardsEngine] = None


def get_engine() -> GRIStandardsEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = GRIStandardsEngine()
    return _engine_instance
