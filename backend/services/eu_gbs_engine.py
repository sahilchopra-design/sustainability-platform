"""
EU Green Bond Standard Engine (E14)
=====================================

Regulation (EU) 2023/2631 on European Green Bonds (EUGBS).

Covers:
  - Pre-issuance Green Bond Factsheet (GBFS) completeness assessment
  - Full EU GBS compliance scoring (taxonomy alignment, DNSH, minimum safeguards,
    external reviewer, reporting commitment)
  - Post-issuance allocation report compliance check
  - Post-issuance impact report compliance check
  - Comparison with ICMA Green Bond Principles and Climate Bonds Standard
  - External Reviewer (ER) requirements (ESMA registration, Art 22-24)
  - 6 EU Taxonomy environmental objectives (CCM/CCA/WMR/CE/PPE/BIO)
  - Sovereign-specific provisions (Art 21)
  - EUGBS regulatory timeline (2023-2026)

E14 in the engine series (E13=TCFD Metrics → E14=EU GBS → E15=...).
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

BOND_TYPES: Dict[str, Dict[str, Any]] = {
    "senior_unsecured": {
        "name": "Senior Unsecured Green Bond",
        "art": "Art 3",
        "taxonomy_requirement": "full",
    },
    "covered_bond": {
        "name": "EU Green Covered Bond",
        "art": "Art 3 + CBDB Directive",
        "taxonomy_requirement": "full",
    },
    "sovereign": {
        "name": "Sovereign/Sub-Sovereign EU Green Bond",
        "art": "Art 21",
        "taxonomy_requirement": "full",
        "sovereign_specific": True,
    },
    "high_yield": {
        "name": "High Yield EU Green Bond",
        "art": "Art 3",
        "taxonomy_requirement": "full",
    },
    "green_loan_linked": {
        "name": "Green Loan linked EU GBS",
        "art": "Art 3",
        "taxonomy_requirement": "full",
    },
    "standard_green_bond": {
        "name": "Standard Green Bond (non-EU-GBS)",
        "art": "N/A",
        "taxonomy_requirement": "none",
    },
}

GBFS_SECTIONS: Dict[str, List[str]] = {
    "section_1_basic": [
        "issuer_name", "bond_type", "issuance_date", "maturity_date",
        "principal_amount", "currency", "isin", "listing_venue",
    ],
    "section_2_use_of_proceeds": [
        "taxonomy_activity_categories", "taxonomy_alignment_pct_committed",
        "dnsh_confirmation", "minimum_safeguards_confirmation",
        "estimated_environmental_objectives",
    ],
    "section_3_allocation_plan": [
        "allocation_timeline", "asset_types", "geographic_scope",
        "refinancing_share_pct", "unallocated_proceeds_policy",
    ],
    "section_4_external_review": [
        "er_name", "er_type", "er_scope", "er_report_date", "er_conclusion",
    ],
    "section_5_reporting": [
        "allocation_report_committed", "impact_report_committed", "reporting_frequency",
    ],
}

TAXONOMY_ENVIRONMENTAL_OBJECTIVES: Dict[str, Dict[str, str]] = {
    "CCM": {
        "id": "CCM", "name": "Climate Change Mitigation",
        "delegated_act": "2021/2139",
    },
    "CCA": {
        "id": "CCA", "name": "Climate Change Adaptation",
        "delegated_act": "2021/2139",
    },
    "WMR": {
        "id": "WMR", "name": "Water & Marine Resources",
        "delegated_act": "2023/2486",
    },
    "CE": {
        "id": "CE", "name": "Circular Economy",
        "delegated_act": "2023/2486",
    },
    "PPE": {
        "id": "PPE", "name": "Pollution Prevention & Control",
        "delegated_act": "2023/2486",
    },
    "BIO": {
        "id": "BIO", "name": "Biodiversity & Ecosystems",
        "delegated_act": "2023/2486",
    },
}

STANDARDS_COMPARISON: Dict[str, Dict[str, Any]] = {
    "eugbs": {
        "name": "EU Green Bond Standard",
        "regulator": "European Commission",
        "mandatory_taxonomy_alignment": True,
        "external_review": "Mandatory (ESMA-registered ER)",
        "post_issuance_reporting": "Mandatory",
        "sovereign_article": "Art 21",
        "flexibility_provision": True,
    },
    "icma_gbp": {
        "name": "ICMA Green Bond Principles",
        "regulator": "ICMA (self-regulatory)",
        "mandatory_taxonomy_alignment": False,
        "external_review": "Recommended (Second Party Opinion)",
        "post_issuance_reporting": "Recommended",
        "sovereign_article": "N/A",
        "flexibility_provision": False,
    },
    "climate_bonds_standard": {
        "name": "Climate Bonds Standard",
        "regulator": "Climate Bonds Initiative",
        "mandatory_taxonomy_alignment": False,
        "external_review": "Mandatory (CBI-approved verifier)",
        "post_issuance_reporting": "Mandatory",
        "sovereign_article": "N/A",
        "flexibility_provision": False,
    },
}

ER_REQUIREMENTS: Dict[str, str] = {
    "registration": (
        "Must be registered with ESMA under Art 22 Regulation 2023/2631"
    ),
    "independence": "No conflict of interest with issuer (Art 23)",
    "methodology": "Publicly available, transparent methodology (Art 24)",
    "scope": (
        "Pre-issuance review of GBFS and/or post-issuance allocation/impact review"
    ),
    "report": (
        "External review report must be published on issuer website and ESMA register"
    ),
}

EUGBS_TIMELINE: List[Dict[str, str]] = [
    {
        "date": "2023-10-04",
        "event": "Regulation (EU) 2023/2631 published in OJEU",
        "article": "All",
    },
    {
        "date": "2024-12-21",
        "event": "Regulation enters into force",
        "article": "Art 28",
    },
    {
        "date": "2025-12-21",
        "event": "ESMA External Reviewer registration opens",
        "article": "Art 22",
    },
    {
        "date": "2026-06-30",
        "event": "Full application date for all provisions",
        "article": "Art 28",
    },
]

# Scoring weights
_W_TAXONOMY = 0.40
_W_DNSH = 0.20
_W_MIN_SAFEGUARDS = 0.15
_W_ER = 0.15
_W_REPORTING = 0.10

# Taxonomy alignment threshold (% of proceeds)
_TAXONOMY_THRESHOLD_STANDARD = 100.0
_TAXONOMY_THRESHOLD_SOVEREIGN = 80.0  # Art 21 sovereign flexibility


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class IssuanceInput:
    bond_id: str
    issuer_name: str
    bond_type: str
    principal_amount: float
    currency: str = "EUR"
    taxonomy_alignment_pct: float = 0.0
    dnsh_confirmed: bool = False
    min_safeguards_confirmed: bool = False
    environmental_objectives: List[str] = field(default_factory=list)
    has_external_reviewer: bool = False
    er_name: str = ""
    has_pre_issuance_review: bool = False
    refinancing_share_pct: float = 0.0
    is_sovereign: bool = False


@dataclass
class AllocationReportInput:
    bond_id: str
    reporting_period: str
    total_allocated_pct: float
    taxonomy_aligned_pct: float
    allocation_by_objective: Dict[str, float]
    unallocated_pct: float
    geographic_breakdown: Dict[str, float]


@dataclass
class ImpactReportInput:
    bond_id: str
    reporting_period: str
    impact_indicators: Dict[str, float]
    methodology_description: str
    alignment_maintained: bool


@dataclass
class EUGBSResult:
    assessment_id: str
    bond_id: str
    issuer_name: str
    bond_type: str
    overall_compliant: bool
    compliance_score: float
    blocking_gaps: List[str]
    warnings: List[str]
    gbfs_completeness_pct: float
    taxonomy_alignment_pct: float
    dnsh_status: str
    er_status: str
    standards_comparison: Dict[str, Any]
    environmental_objectives: List[str]
    sovereign_provisions_applicable: bool
    priority_actions: List[str]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "bond_id": self.bond_id,
            "issuer_name": self.issuer_name,
            "bond_type": self.bond_type,
            "overall_compliant": self.overall_compliant,
            "compliance_score": round(self.compliance_score, 2),
            "blocking_gaps": self.blocking_gaps,
            "warnings": self.warnings,
            "gbfs_completeness_pct": round(self.gbfs_completeness_pct, 2),
            "taxonomy_alignment_pct": self.taxonomy_alignment_pct,
            "dnsh_status": self.dnsh_status,
            "er_status": self.er_status,
            "standards_comparison": self.standards_comparison,
            "environmental_objectives": self.environmental_objectives,
            "sovereign_provisions_applicable": self.sovereign_provisions_applicable,
            "priority_actions": self.priority_actions,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EUGBSEngine:
    """EU Green Bond Standard compliance assessment engine (Regulation 2023/2631)."""

    def assess_issuance(self, inp: IssuanceInput) -> EUGBSResult:
        """
        Full EU GBS compliance assessment for a bond issuance.
        Returns EUGBSResult with compliance score, blocking gaps, and priority actions.
        """
        logger.info(
            "EUGBSEngine assess_issuance: bond_id=%s issuer=%s",
            inp.bond_id, inp.issuer_name,
        )

        blocking_gaps: List[str] = []
        warnings: List[str] = []

        # Determine applicable taxonomy threshold
        tax_threshold = (
            _TAXONOMY_THRESHOLD_SOVEREIGN if inp.is_sovereign
            else _TAXONOMY_THRESHOLD_STANDARD
        )

        # --- Taxonomy alignment check ---
        if inp.taxonomy_alignment_pct < tax_threshold:
            blocking_gaps.append(
                f"Taxonomy alignment ({inp.taxonomy_alignment_pct:.1f}%) is below "
                f"required {tax_threshold:.0f}% per "
                f"{'Art 21 (sovereign)' if inp.is_sovereign else 'Art 3'} "
                f"Regulation 2023/2631."
            )
        tax_score = min(inp.taxonomy_alignment_pct / tax_threshold, 1.0) * 100.0

        # --- DNSH check ---
        if not inp.dnsh_confirmed:
            blocking_gaps.append(
                "Do No Significant Harm (DNSH) confirmation missing — required per "
                "Art 3 + EU Taxonomy Regulation 2020/852 Art 17."
            )
        dnsh_status = "confirmed" if inp.dnsh_confirmed else "not-confirmed"
        dnsh_score = 100.0 if inp.dnsh_confirmed else 0.0

        # --- Minimum safeguards check ---
        if not inp.min_safeguards_confirmed:
            blocking_gaps.append(
                "Minimum safeguards confirmation missing — required per EU Taxonomy "
                "Regulation Art 18 (OECD Guidelines, UN Guiding Principles)."
            )
        ms_score = 100.0 if inp.min_safeguards_confirmed else 0.0

        # --- External reviewer check ---
        er_compliant = inp.has_external_reviewer and inp.has_pre_issuance_review
        er_status = "compliant" if er_compliant else "non-compliant"
        if not inp.has_external_reviewer:
            blocking_gaps.append(
                "No ESMA-registered External Reviewer engaged — mandatory per Art 22 "
                "Regulation 2023/2631."
            )
        elif not inp.has_pre_issuance_review:
            warnings.append(
                f"External reviewer '{inp.er_name}' engaged but pre-issuance review "
                f"not confirmed. Pre-issuance review of GBFS is required before issuance."
            )
        er_score = 100.0 if er_compliant else (50.0 if inp.has_external_reviewer else 0.0)

        # --- Reporting commitment check ---
        # We assume reporting committed if issuer has confirmed both allocation + impact intent.
        # In production this would come from additional fields; here we proxy via er_status.
        reporting_score = 80.0 if er_compliant else 40.0

        # --- Environmental objectives ---
        valid_objectives = [
            obj for obj in inp.environmental_objectives
            if obj in TAXONOMY_ENVIRONMENTAL_OBJECTIVES
        ]
        if not valid_objectives:
            warnings.append(
                "No recognised EU Taxonomy environmental objectives specified "
                "(CCM/CCA/WMR/CE/PPE/BIO). At least one is required."
            )

        # --- GBFS completeness proxy ---
        gbfs_completeness_pct = self._estimate_gbfs_completeness(inp)

        # --- Overall compliance score ---
        compliance_score = (
            _W_TAXONOMY * tax_score
            + _W_DNSH * dnsh_score
            + _W_MIN_SAFEGUARDS * ms_score
            + _W_ER * er_score
            + _W_REPORTING * reporting_score
        )

        overall_compliant = (compliance_score >= 70.0) and (len(blocking_gaps) == 0)

        # --- Priority actions ---
        priority_actions = self._build_priority_actions(
            blocking_gaps, warnings, inp
        )

        return EUGBSResult(
            assessment_id=str(uuid.uuid4()),
            bond_id=inp.bond_id,
            issuer_name=inp.issuer_name,
            bond_type=inp.bond_type,
            overall_compliant=overall_compliant,
            compliance_score=compliance_score,
            blocking_gaps=blocking_gaps,
            warnings=warnings,
            gbfs_completeness_pct=gbfs_completeness_pct,
            taxonomy_alignment_pct=inp.taxonomy_alignment_pct,
            dnsh_status=dnsh_status,
            er_status=er_status,
            standards_comparison=STANDARDS_COMPARISON,
            environmental_objectives=valid_objectives,
            sovereign_provisions_applicable=inp.is_sovereign,
            priority_actions=priority_actions,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def generate_factsheet(self, inp: IssuanceInput) -> Dict[str, Any]:
        """
        Generate a structured GBFS (Green Bond Factsheet) covering all 5 sections
        as defined in GBFS_SECTIONS.
        """
        bond_type_meta = BOND_TYPES.get(inp.bond_type, {})
        return {
            "section_1_basic": {
                "issuer_name": inp.issuer_name,
                "bond_type": bond_type_meta.get("name", inp.bond_type),
                "issuance_date": None,
                "maturity_date": None,
                "principal_amount": inp.principal_amount,
                "currency": inp.currency,
                "isin": None,
                "listing_venue": None,
            },
            "section_2_use_of_proceeds": {
                "taxonomy_activity_categories": inp.environmental_objectives,
                "taxonomy_alignment_pct_committed": inp.taxonomy_alignment_pct,
                "dnsh_confirmation": inp.dnsh_confirmed,
                "minimum_safeguards_confirmation": inp.min_safeguards_confirmed,
                "estimated_environmental_objectives": inp.environmental_objectives,
            },
            "section_3_allocation_plan": {
                "allocation_timeline": "Within 24 months of issuance",
                "asset_types": "To be specified in final GBFS",
                "geographic_scope": "To be specified in final GBFS",
                "refinancing_share_pct": inp.refinancing_share_pct,
                "unallocated_proceeds_policy": (
                    "Unallocated proceeds held in cash/cash equivalents or "
                    "short-term government bonds pending allocation"
                ),
            },
            "section_4_external_review": {
                "er_name": inp.er_name or "Not yet engaged",
                "er_type": "ESMA-registered External Reviewer" if inp.has_external_reviewer else "None",
                "er_scope": "Pre-issuance GBFS review" if inp.has_pre_issuance_review else "Not confirmed",
                "er_report_date": None,
                "er_conclusion": None,
            },
            "section_5_reporting": {
                "allocation_report_committed": True,
                "impact_report_committed": True,
                "reporting_frequency": "Annual",
            },
            "_metadata": {
                "regulation": "Regulation (EU) 2023/2631",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sovereign_provisions_applicable": inp.is_sovereign,
                "applicable_taxonomy_threshold_pct": (
                    _TAXONOMY_THRESHOLD_SOVEREIGN if inp.is_sovereign
                    else _TAXONOMY_THRESHOLD_STANDARD
                ),
            },
        }

    def assess_allocation_report(self, inp: AllocationReportInput) -> Dict[str, Any]:
        """
        Post-issuance allocation report compliance check.
        Checks: allocated_pct >= 95%, taxonomy_aligned_pct >= 100%, unallocated policy.
        """
        gaps: List[str] = []
        warnings: List[str] = []

        if inp.total_allocated_pct < 95.0:
            gaps.append(
                f"Proceeds allocation ({inp.total_allocated_pct:.1f}%) is below "
                f"95% — full allocation expected within reporting period per Art 7 "
                f"Regulation 2023/2631."
            )

        if inp.taxonomy_aligned_pct < 100.0:
            gaps.append(
                f"Taxonomy-aligned allocation ({inp.taxonomy_aligned_pct:.1f}%) "
                f"is below 100% — all allocated proceeds must be taxonomy-aligned "
                f"per Art 3 Regulation 2023/2631."
            )

        if inp.unallocated_pct > 5.0:
            warnings.append(
                f"Unallocated proceeds ({inp.unallocated_pct:.1f}%) exceed 5% — "
                f"document temporary investment policy and timeline for full allocation."
            )

        # Check objective breakdown sums to ~100% of allocated
        obj_sum = sum(inp.allocation_by_objective.values())
        if abs(obj_sum - inp.total_allocated_pct) > 1.0:
            warnings.append(
                f"Allocation by environmental objective sum ({obj_sum:.1f}%) does not "
                f"reconcile with total allocated ({inp.total_allocated_pct:.1f}%)."
            )

        compliant = len(gaps) == 0

        return {
            "bond_id": inp.bond_id,
            "reporting_period": inp.reporting_period,
            "compliant": compliant,
            "total_allocated_pct": inp.total_allocated_pct,
            "taxonomy_aligned_pct": inp.taxonomy_aligned_pct,
            "unallocated_pct": inp.unallocated_pct,
            "allocation_by_objective": inp.allocation_by_objective,
            "geographic_breakdown": inp.geographic_breakdown,
            "gaps": gaps,
            "warnings": warnings,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }

    def assess_impact_report(self, inp: ImpactReportInput) -> Dict[str, Any]:
        """
        Post-issuance impact report compliance check.
        Checks: indicators populated, methodology described, alignment maintained.
        """
        gaps: List[str] = []
        warnings: List[str] = []

        if not inp.impact_indicators:
            gaps.append(
                "No impact indicators reported — quantitative indicators per "
                "funded environmental objective required (Art 8 Regulation 2023/2631)."
            )

        if not inp.methodology_description or len(inp.methodology_description.strip()) < 20:
            gaps.append(
                "Impact measurement methodology description missing or insufficient — "
                "methodology must be described transparently per Art 8(3)."
            )

        if not inp.alignment_maintained:
            gaps.append(
                "Taxonomy alignment of funded assets is no longer maintained — "
                "issuer must disclose steps taken to restore compliance or redeem bonds."
            )

        if len(inp.impact_indicators) < 2:
            warnings.append(
                "Only one impact indicator reported. Best practice is to report "
                "multiple indicators per environmental objective (e.g. tCO2e avoided, "
                "MWh renewable energy produced)."
            )

        compliant = len(gaps) == 0

        return {
            "bond_id": inp.bond_id,
            "reporting_period": inp.reporting_period,
            "compliant": compliant,
            "alignment_maintained": inp.alignment_maintained,
            "impact_indicators": inp.impact_indicators,
            "methodology_description": inp.methodology_description,
            "indicator_count": len(inp.impact_indicators),
            "gaps": gaps,
            "warnings": warnings,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }

    def compare_standards(self) -> Dict[str, Any]:
        """Return STANDARDS_COMPARISON with analysis notes."""
        analysis = {
            "key_differentiator": (
                "EU GBS is the only standard with mandatory EU Taxonomy alignment "
                "and mandatory ESMA-registered external review, making it the most "
                "stringent green bond framework globally."
            ),
            "use_case_eugbs": (
                "Issuers seeking 'gold standard' EU market access and investor confidence "
                "from institutional allocators subject to SFDR/Taxonomy requirements."
            ),
            "use_case_icma_gbp": (
                "Issuers outside the EU or seeking flexibility — self-regulatory "
                "with no mandatory taxonomy alignment."
            ),
            "use_case_cbs": (
                "Climate-focused issuers who want sector-specific climate science criteria "
                "but do not require EU Taxonomy alignment."
            ),
            "cross_recognition": (
                "ICMA GBP and Climate Bonds Standard-certified bonds may overlap with "
                "EU GBS requirements but do not automatically qualify for the EU GBS label."
            ),
        }
        return {**STANDARDS_COMPARISON, "_analysis": analysis}

    # ------------------------------------------------------------------
    # Reference data accessors
    # ------------------------------------------------------------------

    def get_bond_types(self) -> Dict[str, Any]:
        return BOND_TYPES

    def get_taxonomy_objectives(self) -> Dict[str, Any]:
        return TAXONOMY_ENVIRONMENTAL_OBJECTIVES

    def get_er_requirements(self) -> Dict[str, str]:
        return ER_REQUIREMENTS

    def get_timeline(self) -> List[Dict[str, str]]:
        return EUGBS_TIMELINE

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_gbfs_completeness(inp: IssuanceInput) -> float:
        """
        Proxy GBFS completeness based on available issuance input fields.
        Each section contributes equally (20% each, 5 sections).
        """
        section_scores: List[float] = []

        # Section 1: basic bond info
        s1_fields = [
            inp.issuer_name, inp.bond_type,
            str(inp.principal_amount), inp.currency,
        ]
        s1_score = sum(1 for f in s1_fields if f and str(f).strip()) / len(s1_fields)
        section_scores.append(s1_score)

        # Section 2: use of proceeds
        s2_fields = [
            bool(inp.environmental_objectives),
            inp.taxonomy_alignment_pct > 0,
            inp.dnsh_confirmed,
            inp.min_safeguards_confirmed,
        ]
        s2_score = sum(s2_fields) / len(s2_fields)
        section_scores.append(s2_score)

        # Section 3: allocation plan
        s3_score = 0.6 if inp.refinancing_share_pct >= 0 else 0.4
        section_scores.append(s3_score)

        # Section 4: external review
        s4_score = (0.5 * int(inp.has_external_reviewer)) + (0.5 * int(inp.has_pre_issuance_review))
        section_scores.append(s4_score)

        # Section 5: reporting
        section_scores.append(0.8)  # Always partially complete (committed in issuance)

        return (sum(section_scores) / len(section_scores)) * 100.0

    @staticmethod
    def _build_priority_actions(
        blocking_gaps: List[str],
        warnings: List[str],
        inp: IssuanceInput,
    ) -> List[str]:
        actions: List[str] = []
        if not inp.has_external_reviewer:
            actions.append(
                "Engage an ESMA-registered External Reviewer prior to issuance "
                "(mandatory per Art 22 Regulation 2023/2631)."
            )
        if not inp.dnsh_confirmed:
            actions.append(
                "Complete DNSH assessment for all funded taxonomy activities and "
                "include confirmation in GBFS Section 2."
            )
        if not inp.min_safeguards_confirmed:
            actions.append(
                "Confirm minimum safeguards compliance per EU Taxonomy Art 18 "
                "(OECD Guidelines, UNGP) and document in GBFS."
            )
        if inp.taxonomy_alignment_pct < (
            _TAXONOMY_THRESHOLD_SOVEREIGN if inp.is_sovereign else _TAXONOMY_THRESHOLD_STANDARD
        ):
            actions.append(
                f"Increase taxonomy-aligned use of proceeds to meet the "
                f"{'80%' if inp.is_sovereign else '100%'} threshold required "
                f"under Regulation 2023/2631."
            )
        if not inp.environmental_objectives:
            actions.append(
                "Specify at least one EU Taxonomy environmental objective (CCM/CCA/WMR/CE/PPE/BIO) "
                "in the GBFS."
            )
        return actions[:5]
