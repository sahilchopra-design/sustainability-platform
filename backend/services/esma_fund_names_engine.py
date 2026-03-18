"""
ESMA Fund Names ESG Guidelines Engine (E16)
============================================

ESMA/2024/249 Guidelines on funds' names using ESG or sustainability-related
terms. Effective 21 November 2024 (new funds) / 21 May 2025 (existing funds).
Applies to UCITS and AIFs.

Covers:
  - Term detection across 6 ESG category groups
  - 80% investment threshold compliance check
  - PAB exclusion requirements (controversial weapons, UNGC, tobacco, fossil fuel,
    high GHG intensity)
  - DNSH, Paris-Aligned Benchmark, and real-world impact checks
  - SFDR Art 8 / Art 9 minimum requirement alignment
  - Batch assessment for fund ranges
  - Cross-framework mapping: SFDR, EU Taxonomy, MiFID II, PRIIPs, PAB Regulation

E16 in the engine series.
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

ESG_TERM_CATEGORIES: Dict[str, Any] = {
    "environmental": {
        "terms": [
            "environmental", "climate", "green", "ESG", "sustainable",
            "sustainability", "natural", "nature", "ecology", "ecological",
            "biodiversity", "low-carbon", "net-zero", "transition",
            "Paris-aligned", "Paris-alignment", "GHG", "greenhouse",
        ],
        "threshold_pct": 80.0,
        "pai_exclusions_required": True,
        "pai_category": "environmental",
    },
    "social": {
        "terms": [
            "social", "societal", "equality", "diversity", "inclusion",
            "human rights", "community", "employment", "labour", "gender",
            "women",
        ],
        "threshold_pct": 80.0,
        "pai_exclusions_required": True,
        "pai_category": "social",
    },
    "governance": {
        "terms": [
            "governance", "board", "accountability", "transparency",
            "anti-corruption", "stewardship",
        ],
        "threshold_pct": 80.0,
        "pai_exclusions_required": True,
        "pai_category": "governance",
    },
    "impact": {
        "terms": [
            "impact", "positive impact", "measurable impact", "additionality",
        ],
        "threshold_pct": 80.0,
        "pai_exclusions_required": True,
        "real_world_impact_required": True,
        "pai_category": "all",
    },
    "transition": {
        "terms": [
            "transition", "transforming", "evolving", "improving",
            "progressing",
        ],
        "threshold_pct": 80.0,
        "pai_exclusions_required": True,
        "paris_aligned_benchmark_required": True,
        "pai_category": "environmental",
    },
    "sustainable_focus": {
        "terms": [
            "sustainable focus", "sustainable", "sustainability focus",
        ],
        "threshold_pct": 80.0,
        "pai_exclusions_required": True,
        "dnsh_required": True,
        "pai_category": "all",
    },
}

PAB_EXCLUSIONS: Dict[str, Any] = {
    "controversial_weapons": {
        "description": (
            "Companies involved in controversial weapons (cluster munitions, "
            "anti-personnel mines, biological/chemical weapons)"
        ),
        "article": "Art 12(1)(a) PAB Delegated Regulation",
    },
    "ungc_violations": {
        "description": (
            "Companies in violation of UNGC principles or OECD Guidelines for MNEs"
        ),
        "article": "Art 12(1)(b)",
    },
    "tobacco_production": {
        "description": (
            "Companies with 5%+ revenue from tobacco production"
        ),
        "article": "Art 12(1)(c)",
    },
    "fossil_fuel_exploration": {
        "description": (
            "Companies with 1%+ revenue from coal, 10%+ from oil, "
            "50%+ from gas activities"
        ),
        "article": "Art 12(1)(d) - Paris-Aligned",
    },
    "high_ghg_intensity": {
        "description": (
            "Companies with high greenhouse gas intensity above sector thresholds"
        ),
        "article": "Art 12(1)(e) - Climate Transition",
    },
}

SFDR_MINIMUM_REQUIREMENTS: Dict[str, Any] = {
    "art_8": {
        "min_threshold_pct": 80.0,
        "pai_exclusions": True,
        "dnsh": False,
        "note": "Art 8 products must meet 80% ESG investment threshold",
    },
    "art_9": {
        "min_threshold_pct": 80.0,
        "pai_exclusions": True,
        "dnsh": True,
        "note": "Art 9 products must meet 80% + DNSH requirements",
    },
}

ESMA_TIMELINE: List[Dict[str, str]] = [
    {
        "date": "2024-05-14",
        "event": "ESMA Final Report published (ESMA/2024/249)",
        "article": "All",
    },
    {
        "date": "2024-08-21",
        "event": "Entered into force (OJ publication)",
        "article": "Art 1",
    },
    {
        "date": "2024-11-21",
        "event": "Application date for NEW funds",
        "article": "Transitional provision §47",
    },
    {
        "date": "2025-05-21",
        "event": "Application date for EXISTING funds",
        "article": "Transitional provision §47",
    },
]

CROSS_FRAMEWORK: Dict[str, str] = {
    "sfdr_art8_art9": (
        "Fund names using ESG terms must comply with SFDR Art 8/9 minimum thresholds; "
        "SFDR classification does NOT automatically satisfy name guidelines"
    ),
    "eu_taxonomy": (
        "For 'sustainable' terms: minimum taxonomy-aligned % should be disclosed per "
        "Art 8 Taxonomy Regulation Delegated Act"
    ),
    "mifid_spt": (
        "MiFID II Art 2(7) product categorisation should reflect the binding investment "
        "constraints imposed by the name"
    ),
    "priips_kid": (
        "PRIIPs KID Section 1 product description must accurately reflect the ESG "
        "investment policy consistent with the fund name"
    ),
    "paris_aligned_benchmark": (
        "Transition-term funds must track a Paris-Aligned Benchmark per EU "
        "Benchmark Regulation 2016/1011"
    ),
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FundNameInput:
    fund_id: str
    fund_name: str
    sfdr_classification: str = "art_8"
    esg_investment_pct: float = 0.0
    has_pai_exclusions: bool = False
    has_dnsh_assessment: bool = False
    tracks_paris_benchmark: bool = False
    has_real_world_impact_evidence: bool = False
    excluded_categories: List[str] = field(default_factory=list)
    fund_type: str = "UCITS"


@dataclass
class TermDetectionResult:
    detected_terms: List[str]
    term_categories: List[str]
    highest_requirement_category: str
    required_threshold_pct: float
    paris_benchmark_required: bool
    real_world_impact_required: bool
    dnsh_required: bool
    pai_exclusions_required: bool


@dataclass
class ComplianceGap:
    gap_id: str
    category: str
    description: str
    requirement: str
    blocking: bool


@dataclass
class FundNameResult:
    assessment_id: str
    fund_id: str
    fund_name: str
    term_detection: Dict[str, Any]
    esg_investment_pct: float
    required_threshold_pct: float
    threshold_met: bool
    pai_exclusions_compliant: bool
    dnsh_compliant: bool
    paris_benchmark_compliant: bool
    impact_compliant: bool
    overall_compliant: bool
    compliance_score: float
    blocking_gaps: List[str]
    compliance_gaps: List[Dict[str, Any]]
    sfdr_alignment: str
    recommendations: List[str]
    applicable_exclusions: List[str]
    generated_at: str

    def dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "fund_id": self.fund_id,
            "fund_name": self.fund_name,
            "term_detection": self.term_detection,
            "esg_investment_pct": self.esg_investment_pct,
            "required_threshold_pct": self.required_threshold_pct,
            "threshold_met": self.threshold_met,
            "pai_exclusions_compliant": self.pai_exclusions_compliant,
            "dnsh_compliant": self.dnsh_compliant,
            "paris_benchmark_compliant": self.paris_benchmark_compliant,
            "impact_compliant": self.impact_compliant,
            "overall_compliant": self.overall_compliant,
            "compliance_score": self.compliance_score,
            "blocking_gaps": self.blocking_gaps,
            "compliance_gaps": self.compliance_gaps,
            "sfdr_alignment": self.sfdr_alignment,
            "recommendations": self.recommendations,
            "applicable_exclusions": self.applicable_exclusions,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ESMAFundNamesEngine:
    """ESMA Fund Names ESG Guidelines Engine (E16) — ESMA/2024/249."""

    def detect_terms(self, fund_name: str) -> TermDetectionResult:
        """Detect ESG terms in a fund name and derive applicable requirements."""
        name_lower = fund_name.lower()
        detected_terms: List[str] = []
        term_categories: List[str] = []
        required_threshold_pct = 0.0
        paris_benchmark_required = False
        real_world_impact_required = False
        dnsh_required = False
        pai_exclusions_required = False
        highest_requirement_category = "none"

        for category, cfg in ESG_TERM_CATEGORIES.items():
            matched = [t for t in cfg["terms"] if t.lower() in name_lower]
            if matched:
                detected_terms.extend(matched)
                if category not in term_categories:
                    term_categories.append(category)
                if cfg["threshold_pct"] > required_threshold_pct:
                    required_threshold_pct = cfg["threshold_pct"]
                    highest_requirement_category = category
                if cfg.get("pai_exclusions_required"):
                    pai_exclusions_required = True
                if cfg.get("paris_aligned_benchmark_required"):
                    paris_benchmark_required = True
                if cfg.get("real_world_impact_required"):
                    real_world_impact_required = True
                if cfg.get("dnsh_required"):
                    dnsh_required = True

        # Deduplicate
        detected_terms = list(dict.fromkeys(detected_terms))

        return TermDetectionResult(
            detected_terms=detected_terms,
            term_categories=term_categories,
            highest_requirement_category=highest_requirement_category,
            required_threshold_pct=required_threshold_pct,
            paris_benchmark_required=paris_benchmark_required,
            real_world_impact_required=real_world_impact_required,
            dnsh_required=dnsh_required,
            pai_exclusions_required=pai_exclusions_required,
        )

    def assess_fund_name(self, inp: FundNameInput) -> FundNameResult:
        """Full ESMA fund name compliance assessment."""
        assessment_id = str(uuid.uuid4())
        term_det = self.detect_terms(inp.fund_name)

        required_threshold_pct = term_det.required_threshold_pct
        threshold_met = inp.esg_investment_pct >= required_threshold_pct if required_threshold_pct > 0 else True

        pai_exclusions_compliant = (
            inp.has_pai_exclusions if term_det.pai_exclusions_required else True
        )
        dnsh_compliant = (
            inp.has_dnsh_assessment if term_det.dnsh_required else True
        )
        paris_benchmark_compliant = (
            inp.tracks_paris_benchmark if term_det.paris_benchmark_required else True
        )
        impact_compliant = (
            inp.has_real_world_impact_evidence if term_det.real_world_impact_required else True
        )

        # Compliance score: threshold 40% + pai 25% + dnsh 15% + paris 10% + impact 10%
        score_parts = [
            40.0 if threshold_met else 0.0,
            25.0 if pai_exclusions_compliant else 0.0,
            15.0 if dnsh_compliant else 0.0,
            10.0 if paris_benchmark_compliant else 0.0,
            10.0 if impact_compliant else 0.0,
        ]
        compliance_score = sum(score_parts)

        overall_compliant = (
            threshold_met
            and pai_exclusions_compliant
            and dnsh_compliant
            and paris_benchmark_compliant
            and impact_compliant
        )

        # Build compliance gaps
        gaps: List[ComplianceGap] = []
        if not threshold_met:
            gaps.append(ComplianceGap(
                gap_id="gap_threshold",
                category="investment_threshold",
                description=(
                    f"ESG investment allocation {inp.esg_investment_pct:.1f}% is below "
                    f"required {required_threshold_pct:.1f}%"
                ),
                requirement=f"Minimum {required_threshold_pct:.0f}% ESG-aligned investment (ESMA/2024/249 §27)",
                blocking=True,
            ))
        if not pai_exclusions_compliant:
            gaps.append(ComplianceGap(
                gap_id="gap_pai_exclusions",
                category="pai_exclusions",
                description="Fund does not apply mandatory PAB exclusions for ESG-named funds",
                requirement="Apply PAB exclusions (ESMA/2024/249 §28–30)",
                blocking=True,
            ))
        if not dnsh_compliant:
            gaps.append(ComplianceGap(
                gap_id="gap_dnsh",
                category="dnsh",
                description="No DNSH assessment in place; required for 'sustainable' term funds",
                requirement="Conduct DNSH assessment per Art 2(17) SFDR / EU Taxonomy",
                blocking=False,
            ))
        if not paris_benchmark_compliant:
            gaps.append(ComplianceGap(
                gap_id="gap_paris_benchmark",
                category="paris_benchmark",
                description="Fund does not track a Paris-Aligned Benchmark",
                requirement="Track PAB per EU Benchmark Regulation 2016/1011 (for 'transition' terms)",
                blocking=False,
            ))
        if not impact_compliant:
            gaps.append(ComplianceGap(
                gap_id="gap_real_world_impact",
                category="real_world_impact",
                description="No evidence of real-world measurable impact; required for 'impact' term funds",
                requirement="Provide additionality + measurability evidence (ESMA/2024/249 §33)",
                blocking=False,
            ))

        blocking_gaps = [g.gap_id for g in gaps if g.blocking]

        # Applicable exclusions: environmental/transition categories trigger all PAB exclusions
        env_transition_detected = any(
            c in term_det.term_categories for c in ["environmental", "transition"]
        )
        applicable_exclusions = list(PAB_EXCLUSIONS.keys()) if env_transition_detected else []

        # SFDR alignment note
        sfdr_req = SFDR_MINIMUM_REQUIREMENTS.get(inp.sfdr_classification, {})
        if sfdr_req:
            sfdr_alignment = (
                f"SFDR {inp.sfdr_classification.upper()}: "
                f"threshold {sfdr_req['min_threshold_pct']}%, "
                f"DNSH required: {sfdr_req['dnsh']}. "
                f"{sfdr_req.get('note', '')}"
            )
        else:
            sfdr_alignment = f"SFDR classification '{inp.sfdr_classification}' not recognised."

        # Recommendations
        recs: List[str] = []
        if not threshold_met:
            recs.append(
                f"Increase ESG-aligned investment allocation from "
                f"{inp.esg_investment_pct:.1f}% to at least {required_threshold_pct:.0f}% "
                f"or rename the fund to remove ESG terms."
            )
        if not pai_exclusions_compliant:
            recs.append(
                "Implement PAB exclusion screens: controversial weapons, UNGC violations, "
                "tobacco (≥5% revenue), fossil fuels (coal ≥1%, oil ≥10%, gas ≥50%), "
                "high GHG intensity."
            )
        if not dnsh_compliant:
            recs.append(
                "Conduct and document a DNSH assessment across all six EU Taxonomy environmental "
                "objectives for all material underlying investments."
            )
        if not paris_benchmark_compliant:
            recs.append(
                "Align benchmark to an EU Paris-Aligned Benchmark under Regulation 2016/1011, "
                "or remove transition-related terms from the fund name."
            )
        if not impact_compliant:
            recs.append(
                "Document real-world additionality and measurable impact evidence; consider "
                "independent third-party verification of impact claims."
            )
        if overall_compliant:
            recs.append(
                "Fund name is compliant. Ensure annual review of ESG term alignment and "
                "update prospectus / KIID to reflect binding investment constraints."
            )

        return FundNameResult(
            assessment_id=assessment_id,
            fund_id=inp.fund_id,
            fund_name=inp.fund_name,
            term_detection={
                "detected_terms": term_det.detected_terms,
                "term_categories": term_det.term_categories,
                "highest_requirement_category": term_det.highest_requirement_category,
                "required_threshold_pct": term_det.required_threshold_pct,
                "paris_benchmark_required": term_det.paris_benchmark_required,
                "real_world_impact_required": term_det.real_world_impact_required,
                "dnsh_required": term_det.dnsh_required,
                "pai_exclusions_required": term_det.pai_exclusions_required,
            },
            esg_investment_pct=inp.esg_investment_pct,
            required_threshold_pct=required_threshold_pct,
            threshold_met=threshold_met,
            pai_exclusions_compliant=pai_exclusions_compliant,
            dnsh_compliant=dnsh_compliant,
            paris_benchmark_compliant=paris_benchmark_compliant,
            impact_compliant=impact_compliant,
            overall_compliant=overall_compliant,
            compliance_score=round(compliance_score, 2),
            blocking_gaps=blocking_gaps,
            compliance_gaps=[
                {
                    "gap_id": g.gap_id,
                    "category": g.category,
                    "description": g.description,
                    "requirement": g.requirement,
                    "blocking": g.blocking,
                }
                for g in gaps
            ],
            sfdr_alignment=sfdr_alignment,
            recommendations=recs,
            applicable_exclusions=applicable_exclusions,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def batch_assess(self, funds: List[FundNameInput]) -> List[FundNameResult]:
        """Assess a list of fund name inputs."""
        return [self.assess_fund_name(f) for f in funds]

    # ------------------------------------------------------------------
    # Reference accessors
    # ------------------------------------------------------------------

    def get_term_categories(self) -> Dict[str, Any]:
        return ESG_TERM_CATEGORIES

    def get_pab_exclusions(self) -> Dict[str, Any]:
        return PAB_EXCLUSIONS

    def get_sfdr_requirements(self) -> Dict[str, Any]:
        return SFDR_MINIMUM_REQUIREMENTS

    def get_cross_framework(self) -> Dict[str, str]:
        return CROSS_FRAMEWORK

    def get_timeline(self) -> List[Dict[str, str]]:
        return ESMA_TIMELINE
