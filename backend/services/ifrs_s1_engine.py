"""
IFRS S1 General Requirements for Disclosure of Sustainability-related
Financial Information Engine (E18)
======================================================================

ISSB Standard IFRS S1 (issued June 2023, effective 1 January 2024 with
optional IFRS S2 concurrent application).

Covers all 4 IFRS S1 pillars across general sustainability topics
(not climate-specific):
  - Governance (S1.15–S1.20)
  - Strategy (S1.22–S1.30)
  - Risk Management (S1.33–S1.36)
  - Metrics & Targets (S1.38–S1.44)

Also covers:
  - SASB industry metric mapping (S1.38)
  - Transitional reliefs (prior period comparative, Scope 3, industry metrics)
  - Cross-framework: IFRS S2, CSRD ESRS, TCFD, GRI, SASB, SEC Climate
  - Batch assessment for multi-entity reporting groups

E18 in the engine series.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

IFRS_S1_PILLARS: Dict[str, Any] = {
    "governance": {
        "pillar_id": "governance",
        "name": "Governance",
        "description": (
            "Governance processes, controls and procedures used to monitor, manage "
            "and oversee sustainability-related risks and opportunities"
        ),
        "paragraphs": ["S1.15", "S1.16", "S1.17", "S1.18", "S1.19", "S1.20"],
        "blocking": True,
    },
    "strategy": {
        "pillar_id": "strategy",
        "name": "Strategy",
        "description": (
            "Approach for addressing sustainability-related risks and opportunities "
            "that could affect the entity's business model, strategy and cash flows "
            "over the short, medium and long term"
        ),
        "paragraphs": [
            "S1.22", "S1.23", "S1.24", "S1.25",
            "S1.26", "S1.27", "S1.28", "S1.29", "S1.30",
        ],
        "blocking": True,
    },
    "risk_management": {
        "pillar_id": "risk_management",
        "name": "Risk Management",
        "description": (
            "Processes and related policies used to identify, assess, prioritise "
            "and monitor sustainability-related risks and opportunities"
        ),
        "paragraphs": ["S1.33", "S1.34", "S1.35", "S1.36"],
        "blocking": True,
    },
    "metrics_targets": {
        "pillar_id": "metrics_targets",
        "name": "Metrics & Targets",
        "description": (
            "Information used to measure, monitor and manage relevant "
            "sustainability-related risks and opportunities, including progress "
            "against targets"
        ),
        "paragraphs": [
            "S1.38", "S1.39", "S1.40", "S1.41",
            "S1.42", "S1.43", "S1.44",
        ],
        "blocking": True,
    },
}

IFRS_S1_DISCLOSURE_REQUIREMENTS: Dict[str, Any] = {
    "S1.15": {
        "id": "S1.15",
        "pillar": "governance",
        "name": "Board Oversight",
        "description": (
            "Governance body(ies) or individual(s) responsible for oversight of "
            "sustainability-related risks and opportunities"
        ),
        "blocking": True,
    },
    "S1.16": {
        "id": "S1.16",
        "pillar": "governance",
        "name": "Management's Role",
        "description": (
            "Management's role in governance processes, controls and procedures"
        ),
        "blocking": True,
    },
    "S1.22": {
        "id": "S1.22",
        "pillar": "strategy",
        "name": "Sustainability-related Risks & Opportunities",
        "description": (
            "Risks and opportunities that could reasonably be expected to affect "
            "the entity's prospects"
        ),
        "blocking": True,
    },
    "S1.23": {
        "id": "S1.23",
        "pillar": "strategy",
        "name": "Time Horizons",
        "description": (
            "Short, medium and long-term time horizons (entity-defined)"
        ),
        "blocking": True,
    },
    "S1.24": {
        "id": "S1.24",
        "pillar": "strategy",
        "name": "Current & Anticipated Effects",
        "description": (
            "Current and anticipated effects on business model, value chain, "
            "strategy, and financial position"
        ),
        "blocking": True,
    },
    "S1.25": {
        "id": "S1.25",
        "pillar": "strategy",
        "name": "Resilience Assessment",
        "description": (
            "Assessment of resilience of strategy and business model using scenario "
            "analysis or other approaches"
        ),
        "blocking": False,
    },
    "S1.33": {
        "id": "S1.33",
        "pillar": "risk_management",
        "name": "Risk Identification & Assessment",
        "description": (
            "Inputs, parameters, assumptions and analytical methods used to identify "
            "and assess sustainability-related risks"
        ),
        "blocking": True,
    },
    "S1.34": {
        "id": "S1.34",
        "pillar": "risk_management",
        "name": "Prioritisation",
        "description": (
            "How entity prioritises sustainability-related risks relative to other risks"
        ),
        "blocking": True,
    },
    "S1.35": {
        "id": "S1.35",
        "pillar": "risk_management",
        "name": "Monitoring",
        "description": "Processes for monitoring sustainability-related risks",
        "blocking": True,
    },
    "S1.38": {
        "id": "S1.38",
        "pillar": "metrics_targets",
        "name": "Metrics Required by ISSB Standards",
        "description": (
            "Metrics required by applicable ISSB Standards (S2 climate + SASB industry)"
        ),
        "blocking": True,
    },
    "S1.39": {
        "id": "S1.39",
        "pillar": "metrics_targets",
        "name": "Metrics Required by Regulation",
        "description": (
            "Metrics required by applicable regulations (CSRD, SEC, etc.)"
        ),
        "blocking": False,
    },
    "S1.40": {
        "id": "S1.40",
        "pillar": "metrics_targets",
        "name": "Internally-Developed Metrics",
        "description": (
            "Metrics entity uses to measure and monitor sustainability-related risks "
            "or opportunities not covered above"
        ),
        "blocking": False,
    },
    "S1.42": {
        "id": "S1.42",
        "pillar": "metrics_targets",
        "name": "Targets",
        "description": (
            "Targets entity has set or is required to meet by law or regulation"
        ),
        "blocking": True,
    },
}

# Pillar → disclosure requirement IDs mapping (derived from IFRS_S1_DISCLOSURE_REQUIREMENTS)
_PILLAR_REQS: Dict[str, List[str]] = {
    "governance": [],
    "strategy": [],
    "risk_management": [],
    "metrics_targets": [],
}
for _req_id, _req in IFRS_S1_DISCLOSURE_REQUIREMENTS.items():
    _pillar = _req["pillar"]
    if _pillar in _PILLAR_REQS:
        _PILLAR_REQS[_pillar].append(_req_id)

INDUSTRY_SASB_MAPPING: Dict[str, List[str]] = {
    "financial_services": ["FN-AC", "FN-CB", "FN-CF", "FN-IB", "FN-IN", "FN-MF", "FN-MS", "FN-EX"],
    "energy": ["EM-CO", "EM-EP", "EM-MD", "EM-RM", "EM-SV", "EM-NR"],
    "real_estate": ["IF-RE"],
    "technology": ["TC-HW", "TC-IM", "TC-SC", "TC-SE", "TC-TL"],
    "healthcare": ["HC-BP", "HC-DI", "HC-DR", "HC-DY", "HC-MC", "HC-MS"],
    "consumer_goods": ["CG-AA", "CG-FB", "CG-HP", "CG-MR", "CG-TS"],
    "industrials": ["IF-EN", "IF-WM", "IF-RS", "IF-HB", "CN-AG", "CN-BI", "CN-CM", "CN-CO"],
}

IFRS_S1_CROSS_FRAMEWORK: Dict[str, str] = {
    "ifrs_s2": (
        "IFRS S2 is the climate-specific companion standard; S1 governs process, "
        "S2 provides climate metrics/disclosures"
    ),
    "csrd_esrs": (
        "ESRS 1 (general requirements) and ESRS 2 (general disclosures) are the EU "
        "equivalent; interoperability guidance published 2024"
    ),
    "tcfd": (
        "IFRS S1 pillars directly mirror TCFD 4-pillar framework; S1 is TCFD "
        "operationalised into GAAP-quality disclosure"
    ),
    "gri": (
        "GRI Universal Standards 2021 (GRI 1/2/3) are aligned; GRI 2-12 "
        "(activities/workers) maps to S1 value chain"
    ),
    "sasb": (
        "S1.38 requires SASB industry-specific metrics as part of applicable ISSB Standards"
    ),
    "sec_climate": (
        "SEC Rule 33-11275 parallels S1 but US-focused; S1 jurisdiction-neutral"
    ),
}

IFRS_S1_RELIEFS: Dict[str, Any] = {
    "prior_period_comparative": {
        "relief": (
            "In the first year of applying IFRS S1, entities are not required to "
            "provide comparative information"
        ),
        "applicable_period": "First annual reporting period",
        "paragraph": "S1.BC125",
    },
    "scope3_grace_period": {
        "relief": (
            "One year grace period for Scope 3 financed emissions "
            "(if applying IFRS S2 concurrently)"
        ),
        "applicable_period": "First annual reporting period",
        "paragraph": "S2.BC99",
    },
    "industry_metrics_grace": {
        "relief": (
            "If not applying IFRS S2 concurrently, SASB industry metrics may be phased in"
        ),
        "applicable_period": "First annual reporting period",
        "paragraph": "S1.BC128",
    },
}

# Pillar weights for overall score
_PILLAR_WEIGHTS: Dict[str, float] = {
    "governance": 0.25,
    "strategy": 0.35,
    "risk_management": 0.20,
    "metrics_targets": 0.20,
}

# Quality score map
_QUALITY_SCORE: Dict[str, float] = {"full": 100.0, "partial": 50.0, "none": 0.0}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class S1DisclosureInput:
    requirement_id: str
    disclosed: bool
    disclosure_quality: str  # "none" | "partial" | "full"
    notes: str = ""


@dataclass
class S1AssessmentInput:
    entity_id: str
    entity_name: str
    industry: str = "general"
    reporting_year: int = 2025
    disclosures: Dict[str, S1DisclosureInput] = field(default_factory=dict)
    applying_reliefs: List[str] = field(default_factory=list)


@dataclass
class S1PillarResult:
    pillar_id: str
    pillar_name: str
    total_requirements: int
    fully_disclosed: int
    partially_disclosed: int
    not_disclosed: int
    pillar_score: float
    blocking_gaps: List[str]

    def dict(self) -> Dict[str, Any]:
        return {
            "pillar_id": self.pillar_id,
            "pillar_name": self.pillar_name,
            "total_requirements": self.total_requirements,
            "fully_disclosed": self.fully_disclosed,
            "partially_disclosed": self.partially_disclosed,
            "not_disclosed": self.not_disclosed,
            "pillar_score": self.pillar_score,
            "blocking_gaps": self.blocking_gaps,
        }


@dataclass
class IFRSS1Result:
    assessment_id: str
    entity_id: str
    entity_name: str
    industry: str
    reporting_year: int
    pillar_results: Dict[str, Any]
    overall_score: float
    overall_compliant: bool
    blocking_gaps: List[str]
    applied_reliefs: List[str]
    industry_sasb_codes: List[str]
    cross_framework: Dict[str, str]
    priority_actions: List[str]
    generated_at: str

    def dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "industry": self.industry,
            "reporting_year": self.reporting_year,
            "pillar_results": self.pillar_results,
            "overall_score": self.overall_score,
            "overall_compliant": self.overall_compliant,
            "blocking_gaps": self.blocking_gaps,
            "applied_reliefs": self.applied_reliefs,
            "industry_sasb_codes": self.industry_sasb_codes,
            "cross_framework": self.cross_framework,
            "priority_actions": self.priority_actions,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class IFRSS1Engine:
    """IFRS S1 General Sustainability Disclosures Engine (E18)."""

    def assess_pillar(
        self,
        pillar_id: str,
        entity_id: str,
        entity_name: str,
        disclosures: Dict[str, S1DisclosureInput],
    ) -> S1PillarResult:
        """Assess a single IFRS S1 pillar."""
        pillar_cfg = IFRS_S1_PILLARS.get(pillar_id, {})
        pillar_name = pillar_cfg.get("name", pillar_id)
        req_ids = _PILLAR_REQS.get(pillar_id, [])

        fully_disclosed = 0
        partially_disclosed = 0
        not_disclosed = 0
        blocking_gaps: List[str] = []

        weighted_sum = 0.0
        total_weight = 0.0

        for req_id in req_ids:
            req_cfg = IFRS_S1_DISCLOSURE_REQUIREMENTS.get(req_id, {})
            is_blocking = req_cfg.get("blocking", False)
            w = 1.5 if is_blocking else 1.0

            disc = disclosures.get(req_id)
            if disc:
                quality = disc.disclosure_quality
            else:
                quality = "none"

            score = _QUALITY_SCORE.get(quality, 0.0)
            weighted_sum += score * w
            total_weight += w

            if quality == "full":
                fully_disclosed += 1
            elif quality == "partial":
                partially_disclosed += 1
            else:
                not_disclosed += 1
                if is_blocking:
                    blocking_gaps.append(
                        f"{req_id} — {req_cfg.get('name', req_id)}: not disclosed"
                    )

        pillar_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0

        return S1PillarResult(
            pillar_id=pillar_id,
            pillar_name=pillar_name,
            total_requirements=len(req_ids),
            fully_disclosed=fully_disclosed,
            partially_disclosed=partially_disclosed,
            not_disclosed=not_disclosed,
            pillar_score=round(pillar_score, 2),
            blocking_gaps=blocking_gaps,
        )

    def assess(self, inp: S1AssessmentInput) -> IFRSS1Result:
        """Full IFRS S1 compliance assessment across all 4 pillars."""
        assessment_id = str(uuid.uuid4())

        pillar_results: Dict[str, Any] = {}
        overall_blocking_gaps: List[str] = []

        for pillar_id in IFRS_S1_PILLARS:
            pr = self.assess_pillar(
                pillar_id=pillar_id,
                entity_id=inp.entity_id,
                entity_name=inp.entity_name,
                disclosures=inp.disclosures,
            )
            pillar_results[pillar_id] = pr.dict()
            overall_blocking_gaps.extend(pr.blocking_gaps)

        # Overall score: weighted average across pillars
        overall_score = sum(
            pillar_results[pid]["pillar_score"] * _PILLAR_WEIGHTS.get(pid, 0.0)
            for pid in IFRS_S1_PILLARS
        )

        overall_compliant = overall_score >= 70.0 and len(overall_blocking_gaps) == 0

        # SASB codes for industry
        industry_sasb_codes = INDUSTRY_SASB_MAPPING.get(inp.industry, [])

        # Priority actions: up to 4 lowest-scoring blocking requirements not fully disclosed
        candidate_actions: List[tuple] = []
        for req_id, req_cfg in IFRS_S1_DISCLOSURE_REQUIREMENTS.items():
            if not req_cfg.get("blocking"):
                continue
            disc = inp.disclosures.get(req_id)
            quality = disc.disclosure_quality if disc else "none"
            score = _QUALITY_SCORE.get(quality, 0.0)
            if score < 100.0:
                candidate_actions.append((score, req_id, req_cfg.get("name", req_id)))
        candidate_actions.sort(key=lambda x: x[0])
        priority_actions = [
            f"Improve disclosure for {req_id} — {name} (current: {score:.0f}/100)"
            for score, req_id, name in candidate_actions[:4]
        ]

        return IFRSS1Result(
            assessment_id=assessment_id,
            entity_id=inp.entity_id,
            entity_name=inp.entity_name,
            industry=inp.industry,
            reporting_year=inp.reporting_year,
            pillar_results=pillar_results,
            overall_score=round(overall_score, 2),
            overall_compliant=overall_compliant,
            blocking_gaps=overall_blocking_gaps,
            applied_reliefs=inp.applying_reliefs,
            industry_sasb_codes=industry_sasb_codes,
            cross_framework=IFRS_S1_CROSS_FRAMEWORK,
            priority_actions=priority_actions,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Reference accessors
    # ------------------------------------------------------------------

    def get_pillars(self) -> Dict[str, Any]:
        return IFRS_S1_PILLARS

    def get_disclosure_requirements(self) -> Dict[str, Any]:
        return IFRS_S1_DISCLOSURE_REQUIREMENTS

    def get_industry_sasb_mapping(self) -> Dict[str, List[str]]:
        return INDUSTRY_SASB_MAPPING

    def get_cross_framework(self) -> Dict[str, str]:
        return IFRS_S1_CROSS_FRAMEWORK

    def get_reliefs(self) -> Dict[str, Any]:
        return IFRS_S1_RELIEFS
