"""
Assurance Readiness Dashboard Engine (E10)
==========================================

Cross-module assurance scoring engine for sustainability disclosure readiness.
Evaluates an entity's preparedness for third-party limited or reasonable assurance
across all sustainability reporting modules on the platform.

Assurance standards mapped:
  ISAE 3000 (rev.)  — Assurance engagements other than audits/reviews
  ISAE 3410         — GHG statements (Scope 1/2/3 carbon data)
  ISSA 5000         — IAASB International Standard on Sustainability Assurance (2025)
  CSRD Art 26a      — Mandatory limited assurance on ESRS disclosures (wave 1: FY2025)
  AA1000 AS v3      — AccountAbility Assurance Standard
  EU Taxonomy       — Emerging assurance expectations (ECB/ESMA supervisory)
  SFDR Art 4        — PAI statement data quality

Assurance readiness criteria (26 criteria across 8 domains):
  D1 — Data governance and lineage
  D2 — GHG and carbon accounting
  D3 — EU Taxonomy alignment
  D4 — ESRS quantitative datapoints
  D5 — SFDR / PAI data
  D6 — Internal controls
  D7 — Materiality and scope
  D8 — Disclosure completeness
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Reference: Assurance Standards Registry
# ---------------------------------------------------------------------------

ASSURANCE_STANDARDS: Dict[str, Dict[str, Any]] = {
    "ISAE3000": {
        "title": "ISAE 3000 (Revised) — General Sustainability Assurance",
        "issuer": "IAASB / IFAC",
        "scope": "All sustainability disclosures not covered by specific standards",
        "assurance_levels": ["limited", "reasonable"],
        "key_requirements": [
            "Defined criteria (reporting standard, e.g. ESRS, GRI)",
            "Evidence base for material assertions",
            "Practitioner independence",
            "Engagement documentation",
        ],
    },
    "ISAE3410": {
        "title": "ISAE 3410 — GHG Statements",
        "issuer": "IAASB / IFAC",
        "scope": "Greenhouse gas emissions (Scope 1, 2, 3) per GHG Protocol / ISO 14064",
        "assurance_levels": ["limited", "reasonable"],
        "key_requirements": [
            "Organisational boundary (equity / control)",
            "Operational boundary (Scope 1/2/3 completeness)",
            "Emission factor sources and vintages",
            "Data collection procedures and controls",
            "Prior-period comparison",
        ],
    },
    "ISSA5000": {
        "title": "ISSA 5000 — International Standard on Sustainability Assurance",
        "issuer": "IAASB",
        "scope": "All sustainability information; replaces ISAE 3000 for sustainability from ~2026",
        "assurance_levels": ["limited", "reasonable"],
        "key_requirements": [
            "Scoping against applicable sustainability reporting framework",
            "Double materiality assessment documented",
            "Value chain data sources mapped",
            "Controls over sustainability reporting process",
            "Disclosure of practitioner's conclusion",
        ],
        "effective_date": "2026 (expected)",
    },
    "CSRD_ART26A": {
        "title": "CSRD Art 26a — Mandatory Limited Assurance",
        "issuer": "EU Commission",
        "scope": "ESRS disclosures (CSRD in-scope entities)",
        "assurance_levels": ["limited"],
        "phase_in": {
            "wave_1": "FY2025 (>500 employees, listed; existing NFRD entities)",
            "wave_2": "FY2026 (large companies per EU Accounting Directive)",
            "wave_3": "FY2027 (listed SMEs)",
            "wave_4": "FY2028 (third-country entities with EU nexus)",
        },
        "key_requirements": [
            "Assurance over entire ESRS disclosure package",
            "Auditor or accredited ESG assurance provider",
            "ESRS 2 general disclosures mandatory",
            "Material topic DPs assured",
        ],
    },
    "AA1000AS_V3": {
        "title": "AA1000 Assurance Standard v3",
        "issuer": "AccountAbility",
        "scope": "Sustainability reporting — stakeholder engagement focus",
        "assurance_levels": ["type_1", "type_2"],
        "key_requirements": [
            "Inclusivity — stakeholder engagement documented",
            "Materiality — material topics identified",
            "Responsiveness — response to stakeholder concerns",
            "Impact — sustainability impact management",
        ],
    },
    "GRI_ASSURANCE": {
        "title": "GRI — External Assurance Guidance",
        "issuer": "GRI",
        "scope": "GRI Standards disclosures",
        "assurance_levels": ["limited", "reasonable"],
        "key_requirements": [
            "GRI content index assured",
            "GRI 2-5 assurance disclosure populated",
            "Material topic disclosures covered",
        ],
    },
}

# ---------------------------------------------------------------------------
# Reference: Assurance Readiness Criteria (26 criteria across 8 domains)
# ---------------------------------------------------------------------------

READINESS_CRITERIA: List[Dict[str, Any]] = [
    # D1 — Data Governance and Lineage
    {
        "criterion_id": "D1-1",
        "domain": "D1_data_governance",
        "domain_label": "Data Governance and Lineage",
        "title": "Data lineage documented for all material sustainability KPIs",
        "standards": ["ISSA5000", "ISAE3000", "CSRD_ART26A"],
        "weight": 1.5,
        "blocking": True,
        "description": "Source-to-disclosure traceability for all material quantitative datapoints",
    },
    {
        "criterion_id": "D1-2",
        "domain": "D1_data_governance",
        "domain_label": "Data Governance and Lineage",
        "title": "Audit log with immutable change history for disclosure data",
        "standards": ["ISSA5000", "ISAE3000"],
        "weight": 1.2,
        "blocking": True,
        "description": "All modifications to sustainability data logged with timestamp, user, reason",
    },
    {
        "criterion_id": "D1-3",
        "domain": "D1_data_governance",
        "domain_label": "Data Governance and Lineage",
        "title": "PCAF Data Quality Scores (DQS) documented and disclosed",
        "standards": ["ISAE3410", "ISSA5000"],
        "weight": 1.0,
        "blocking": False,
        "description": "PCAF DQS 1-5 assigned per asset class; methodology disclosed",
    },
    {
        "criterion_id": "D1-4",
        "domain": "D1_data_governance",
        "domain_label": "Data Governance and Lineage",
        "title": "Third-party data sources identified with vendor credentials",
        "standards": ["ISAE3000", "ISSA5000"],
        "weight": 0.8,
        "blocking": False,
        "description": "All external ESG data providers named; contracts / data license documented",
    },
    # D2 — GHG and Carbon Accounting
    {
        "criterion_id": "D2-1",
        "domain": "D2_ghg_carbon",
        "domain_label": "GHG and Carbon Accounting",
        "title": "Scope 1 and 2 GHG emissions with calculation methodology",
        "standards": ["ISAE3410", "ISSA5000", "CSRD_ART26A"],
        "weight": 2.0,
        "blocking": True,
        "description": "Scope 1/2 data per GHG Protocol; emission factors cited with vintage",
    },
    {
        "criterion_id": "D2-2",
        "domain": "D2_ghg_carbon",
        "domain_label": "GHG and Carbon Accounting",
        "title": "Scope 3 categories covered with PCAF / GHG Protocol methodology",
        "standards": ["ISAE3410", "ISSA5000", "CSRD_ART26A"],
        "weight": 1.5,
        "blocking": False,
        "description": "At least categories 1, 5, 11, 15 quantified for financial sector",
    },
    {
        "criterion_id": "D2-3",
        "domain": "D2_ghg_carbon",
        "domain_label": "GHG and Carbon Accounting",
        "title": "Organisational and operational boundary defined",
        "standards": ["ISAE3410"],
        "weight": 1.2,
        "blocking": True,
        "description": "Equity share / operational control boundary selection documented and applied consistently",
    },
    {
        "criterion_id": "D2-4",
        "domain": "D2_ghg_carbon",
        "domain_label": "GHG and Carbon Accounting",
        "title": "Prior-period comparison with restatement policy",
        "standards": ["ISAE3410", "ISSA5000", "CSRD_ART26A"],
        "weight": 1.0,
        "blocking": False,
        "description": "At least one prior period presented; restatement triggers defined",
    },
    # D3 — EU Taxonomy Alignment
    {
        "criterion_id": "D3-1",
        "domain": "D3_eu_taxonomy",
        "domain_label": "EU Taxonomy Alignment",
        "title": "Taxonomy eligibility and alignment assessment per NACE activity",
        "standards": ["CSRD_ART26A", "ISAE3000"],
        "weight": 1.5,
        "blocking": True,
        "description": "All in-scope NACE activities screened for eligibility and alignment to 6 objectives",
    },
    {
        "criterion_id": "D3-2",
        "domain": "D3_eu_taxonomy",
        "domain_label": "EU Taxonomy Alignment",
        "title": "Technical Screening Criteria (TSC) and DNSH documented per activity",
        "standards": ["CSRD_ART26A"],
        "weight": 1.2,
        "blocking": True,
        "description": "TSC compliance evidence maintained per Taxonomy Delegated Acts",
    },
    {
        "criterion_id": "D3-3",
        "domain": "D3_eu_taxonomy",
        "domain_label": "EU Taxonomy Alignment",
        "title": "KPIs: CapEx%, OpEx%, Turnover% disclosed by objective",
        "standards": ["CSRD_ART26A", "ISAE3000"],
        "weight": 1.0,
        "blocking": False,
        "description": "Three KPIs disclosed per Art 8 Delegated Regulation 2021/2178",
    },
    # D4 — ESRS Quantitative Datapoints
    {
        "criterion_id": "D4-1",
        "domain": "D4_esrs_datapoints",
        "domain_label": "ESRS Quantitative Datapoints",
        "title": "ESRS 2 general disclosures complete (governance, strategy, risk, targets)",
        "standards": ["CSRD_ART26A", "ISSA5000"],
        "weight": 2.0,
        "blocking": True,
        "description": "GOV-1 to GOV-5, SBM-1 to SBM-3, IRO-1 to IRO-2, MDR sections populated",
    },
    {
        "criterion_id": "D4-2",
        "domain": "D4_esrs_datapoints",
        "domain_label": "ESRS Quantitative Datapoints",
        "title": "Material topic ESRS datapoints identified and populated",
        "standards": ["CSRD_ART26A", "ISSA5000"],
        "weight": 1.5,
        "blocking": True,
        "description": "All material topic DPs per IRO-1 materiality assessment populated",
    },
    {
        "criterion_id": "D4-3",
        "domain": "D4_esrs_datapoints",
        "domain_label": "ESRS Quantitative Datapoints",
        "title": "Double materiality assessment documented with IRO register",
        "standards": ["CSRD_ART26A", "ISSA5000", "ISAE3000"],
        "weight": 1.5,
        "blocking": True,
        "description": "Impact and financial materiality assessed per ESRS 1 §§ 43-68; IRO register maintained",
    },
    {
        "criterion_id": "D4-4",
        "domain": "D4_esrs_datapoints",
        "domain_label": "ESRS Quantitative Datapoints",
        "title": "ESRS disclosure index published with topic/DP mapping",
        "standards": ["CSRD_ART26A"],
        "weight": 0.8,
        "blocking": False,
        "description": "Index of all ESRS topics with populated/omitted/not-material status",
    },
    # D5 — SFDR / PAI Data
    {
        "criterion_id": "D5-1",
        "domain": "D5_sfdr_pai",
        "domain_label": "SFDR / PAI Data",
        "title": "All 14 mandatory PAI indicators populated with data quality disclosure",
        "standards": ["ISAE3000", "ISSA5000"],
        "weight": 1.2,
        "blocking": False,
        "description": "RTS Annex I Table 1 indicators 1–14 populated; estimated data flagged",
    },
    {
        "criterion_id": "D5-2",
        "domain": "D5_sfdr_pai",
        "domain_label": "SFDR / PAI Data",
        "title": "SFDR pre-contractual and periodic disclosure templates complete",
        "standards": ["ISAE3000"],
        "weight": 0.8,
        "blocking": False,
        "description": "Annex II/III (Art 8) or Annex IV/V (Art 9) >90% complete",
    },
    # D6 — Internal Controls
    {
        "criterion_id": "D6-1",
        "domain": "D6_internal_controls",
        "domain_label": "Internal Controls",
        "title": "Sustainability reporting process controls documented (ICSR)",
        "standards": ["ISSA5000", "ISAE3000", "CSRD_ART26A"],
        "weight": 1.5,
        "blocking": True,
        "description": "Internal Controls over Sustainability Reporting (ICSR) framework documented; board-approved",
    },
    {
        "criterion_id": "D6-2",
        "domain": "D6_internal_controls",
        "domain_label": "Internal Controls",
        "title": "Error correction and restatement procedures in place",
        "standards": ["ISSA5000", "ISAE3410"],
        "weight": 1.0,
        "blocking": False,
        "description": "Documented procedures for identifying, correcting, and disclosing errors in sustainability data",
    },
    {
        "criterion_id": "D6-3",
        "domain": "D6_internal_controls",
        "domain_label": "Internal Controls",
        "title": "Management sign-off on sustainability disclosures",
        "standards": ["ISSA5000", "CSRD_ART26A"],
        "weight": 1.0,
        "blocking": True,
        "description": "Responsible management body (board/CEO/CFO) signs the sustainability statement",
    },
    # D7 — Materiality and Scope
    {
        "criterion_id": "D7-1",
        "domain": "D7_materiality_scope",
        "domain_label": "Materiality and Scope",
        "title": "Reporting boundary aligned with consolidated financial statements",
        "standards": ["ISAE3000", "ISSA5000", "CSRD_ART26A"],
        "weight": 1.2,
        "blocking": True,
        "description": "Sustainability reporting boundary consistent with financial consolidation scope",
    },
    {
        "criterion_id": "D7-2",
        "domain": "D7_materiality_scope",
        "domain_label": "Materiality and Scope",
        "title": "Value chain inclusion and limitations disclosed",
        "standards": ["ISSA5000", "CSRD_ART26A"],
        "weight": 1.0,
        "blocking": False,
        "description": "Upstream/downstream value chain scope defined; exclusions justified",
    },
    # D8 — Disclosure Completeness
    {
        "criterion_id": "D8-1",
        "domain": "D8_disclosure_completeness",
        "domain_label": "Disclosure Completeness",
        "title": "Sustainability statement complete per applicable framework",
        "standards": ["ISSA5000", "CSRD_ART26A", "ISAE3000"],
        "weight": 1.5,
        "blocking": True,
        "description": "No material omissions in the disclosure package to be assured",
    },
    {
        "criterion_id": "D8-2",
        "domain": "D8_disclosure_completeness",
        "domain_label": "Disclosure Completeness",
        "title": "Targets and transition plan disclosed with measurable milestones",
        "standards": ["CSRD_ART26A", "ISSA5000"],
        "weight": 1.0,
        "blocking": False,
        "description": "Net zero / Paris-aligned targets with interim milestones; transition plan per ESRS E1-6",
    },
    {
        "criterion_id": "D8-3",
        "domain": "D8_disclosure_completeness",
        "domain_label": "Disclosure Completeness",
        "title": "Assurance provider engagement and scope letter issued",
        "standards": ["ISAE3000", "ISSA5000", "CSRD_ART26A"],
        "weight": 0.8,
        "blocking": False,
        "description": "Assurance provider identified; engagement scope and terms agreed",
    },
    {
        "criterion_id": "D8-4",
        "domain": "D8_disclosure_completeness",
        "domain_label": "Disclosure Completeness",
        "title": "Comparative information / restatements provided for prior periods",
        "standards": ["CSRD_ART26A", "ISAE3410"],
        "weight": 0.8,
        "blocking": False,
        "description": "At least one year of prior-period comparatives; restatements explained",
    },
]

# Total weight
_TOTAL_WEIGHT = sum(c["weight"] for c in READINESS_CRITERIA)

# Blocking criteria IDs
_BLOCKING_CRITERIA = {c["criterion_id"] for c in READINESS_CRITERIA if c["blocking"]}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CriterionInput:
    """Status of a single assurance readiness criterion."""
    criterion_id: str
    met: bool = False
    partial: bool = False                   # partial = 50% score
    evidence_description: str = ""
    evidence_quality: str = "none"          # none | weak | adequate | strong
    gaps: List[str] = field(default_factory=list)


@dataclass
class AssuranceInput:
    """Full entity assurance readiness input."""
    entity_id: str
    entity_name: str
    reporting_framework: str = "CSRD_ESRS"         # CSRD_ESRS | GRI | ISSB | SFDR_ONLY
    assurance_standard_target: str = "ISSA5000"    # ISAE3000 | ISAE3410 | ISSA5000 | CSRD_ART26A
    target_assurance_level: str = "limited"        # limited | reasonable
    csrd_wave: Optional[int] = None               # 1–4 (determines urgency)
    reporting_year: str = ""

    # Criterion statuses (keyed by criterion_id)
    criteria: List[CriterionInput] = field(default_factory=list)

    # Module-level flags (derived from platform module states)
    has_scope1_scope2_data: bool = False
    has_scope3_data: bool = False
    has_ghg_methodology: bool = False
    has_pcaf_dqs: bool = False
    has_eu_taxonomy_assessment: bool = False
    has_taxonomy_tsc_evidence: bool = False
    has_esrs2_general: bool = False
    has_double_materiality: bool = False
    has_material_esrs_dps: bool = False
    has_esrs_disclosure_index: bool = False
    has_sfdr_pai_14: bool = False
    has_sfdr_annex_templates: bool = False
    has_audit_log: bool = False
    has_data_lineage: bool = False
    has_icsr_controls: bool = False
    has_management_signoff: bool = False
    has_error_correction_procedure: bool = False
    has_reporting_boundary_defined: bool = False
    has_value_chain_scope: bool = False
    has_assurance_provider: bool = False
    has_prior_period_comparison: bool = False
    has_transition_plan_with_targets: bool = False
    has_third_party_data_documented: bool = False


@dataclass
class CriterionResult:
    criterion_id: str
    domain: str
    domain_label: str
    title: str
    standards: List[str]
    weight: float
    blocking: bool
    score: float                    # 0 | 0.5 | 1.0
    weighted_score: float
    status: str                     # met | partial | not_met
    evidence_quality: str
    evidence_description: str
    gaps: List[str]


@dataclass
class DomainResult:
    domain_id: str
    domain_label: str
    criteria_count: int
    criteria_met: int
    criteria_partial: int
    criteria_not_met: int
    domain_score_pct: float
    blocking_gaps: List[str]


@dataclass
class AssuranceReadinessResult:
    run_id: str = ""
    entity_id: str = ""
    entity_name: str = ""
    reporting_framework: str = ""
    assurance_standard_target: str = ""
    target_assurance_level: str = ""
    csrd_wave: Optional[int] = None
    reporting_year: str = ""
    assessment_date: str = ""

    # Scoring
    overall_readiness_score_pct: float = 0.0
    readiness_tier: str = ""        # ready | nearly_ready | requires_remediation | not_ready
    weighted_score: float = 0.0

    # Criteria detail
    criterion_results: List[CriterionResult] = field(default_factory=list)
    domain_results: List[DomainResult] = field(default_factory=list)

    # Blocking gaps
    blocking_gaps_count: int = 0
    blocking_gaps: List[str] = field(default_factory=list)

    # Standards coverage
    standards_coverage: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Actions
    gaps: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    estimated_remediation_weeks: int = 0

    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AssuranceReadinessEngine:
    """
    Cross-module assurance readiness scoring engine.
    Maps platform module states to sustainability assurance criteria.
    """

    # Module-flag → criterion_id mapping (auto-derive scores from platform flags)
    _FLAG_CRITERION_MAP: Dict[str, str] = {
        "has_data_lineage": "D1-1",
        "has_audit_log": "D1-2",
        "has_pcaf_dqs": "D1-3",
        "has_third_party_data_documented": "D1-4",
        "has_scope1_scope2_data": "D2-1",
        "has_scope3_data": "D2-2",
        "has_ghg_methodology": "D2-3",
        "has_prior_period_comparison": "D2-4",
        "has_eu_taxonomy_assessment": "D3-1",
        "has_taxonomy_tsc_evidence": "D3-2",
        "has_esrs2_general": "D4-1",
        "has_material_esrs_dps": "D4-2",
        "has_double_materiality": "D4-3",
        "has_esrs_disclosure_index": "D4-4",
        "has_sfdr_pai_14": "D5-1",
        "has_sfdr_annex_templates": "D5-2",
        "has_icsr_controls": "D6-1",
        "has_error_correction_procedure": "D6-2",
        "has_management_signoff": "D6-3",
        "has_reporting_boundary_defined": "D7-1",
        "has_value_chain_scope": "D7-2",
        "has_material_esrs_dps": "D8-1",    # proxy: material DPs = completeness
        "has_transition_plan_with_targets": "D8-2",
        "has_assurance_provider": "D8-3",
        "has_prior_period_comparison": "D8-4",
    }

    def assess(
        self,
        entity: AssuranceInput,
        assessment_date: Optional[str] = None,
    ) -> AssuranceReadinessResult:
        assessment_date = assessment_date or date.today().isoformat()
        run_id = f"ASSU-{entity.entity_id[:8].upper()}-{uuid.uuid4().hex[:6].upper()}"

        # Build criterion score map from explicit criteria + auto-derived flags
        score_map = self._build_score_map(entity)

        # Score each criterion
        criterion_results: List[CriterionResult] = []
        for c in READINESS_CRITERIA:
            cid = c["criterion_id"]
            score, status, ev_desc, ev_quality, gaps = score_map.get(
                cid, (0.0, "not_met", "", "none", [f"No data provided for {cid}"])
            )
            cr = CriterionResult(
                criterion_id=cid,
                domain=c["domain"],
                domain_label=c["domain_label"],
                title=c["title"],
                standards=c["standards"],
                weight=c["weight"],
                blocking=c["blocking"],
                score=score,
                weighted_score=round(score * c["weight"], 3),
                status=status,
                evidence_quality=ev_quality,
                evidence_description=ev_desc,
                gaps=gaps,
            )
            criterion_results.append(cr)

        # Overall weighted score
        total_weighted = sum(cr.weighted_score for cr in criterion_results)
        readiness_pct = total_weighted / _TOTAL_WEIGHT * 100

        # Domain roll-up
        domain_results = self._build_domain_results(criterion_results)

        # Blocking gaps
        blocking_gaps = [
            f"[{cr.criterion_id}] {cr.title}"
            for cr in criterion_results
            if cr.blocking and cr.status == "not_met"
        ]

        # Standards coverage
        standards_coverage = self._assess_standards_coverage(
            criterion_results, entity.assurance_standard_target
        )

        # Tier
        readiness_tier = self._derive_tier(
            readiness_pct, len(blocking_gaps), entity.target_assurance_level
        )

        gaps, actions, est_weeks = self._derive_gaps_actions(
            criterion_results, blocking_gaps, entity
        )

        return AssuranceReadinessResult(
            run_id=run_id,
            entity_id=entity.entity_id,
            entity_name=entity.entity_name,
            reporting_framework=entity.reporting_framework,
            assurance_standard_target=entity.assurance_standard_target,
            target_assurance_level=entity.target_assurance_level,
            csrd_wave=entity.csrd_wave,
            reporting_year=entity.reporting_year,
            assessment_date=assessment_date,
            overall_readiness_score_pct=round(readiness_pct, 1),
            readiness_tier=readiness_tier,
            weighted_score=round(total_weighted, 2),
            criterion_results=criterion_results,
            domain_results=domain_results,
            blocking_gaps_count=len(blocking_gaps),
            blocking_gaps=blocking_gaps,
            standards_coverage=standards_coverage,
            gaps=gaps[:10],
            priority_actions=actions[:6],
            estimated_remediation_weeks=est_weeks,
            metadata={
                "framework": entity.reporting_framework,
                "target_standard": entity.assurance_standard_target,
                "target_level": entity.target_assurance_level,
                "total_criteria": len(READINESS_CRITERIA),
                "blocking_criteria": len(_BLOCKING_CRITERIA),
                "total_weight": _TOTAL_WEIGHT,
                "engine_version": "E10.1",
                "reference": (
                    "ISAE 3000 (Rev.) | ISAE 3410 | ISSA 5000 (IAASB 2025) | "
                    "CSRD Art 26a | AA1000 AS v3"
                ),
            },
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _build_score_map(
        self, entity: AssuranceInput
    ) -> Dict[str, tuple]:
        """
        Build a map of criterion_id → (score, status, evidence, quality, gaps).
        Priority: explicit CriterionInput entries > auto-derived from module flags.
        """
        result: Dict[str, tuple] = {}

        # Auto-derive from module flags
        for flag_name, cid in self._FLAG_CRITERION_MAP.items():
            flag_val = getattr(entity, flag_name, False)
            if cid not in result:
                if flag_val:
                    result[cid] = (1.0, "met", f"Platform flag {flag_name}=True", "adequate", [])
                else:
                    result[cid] = (0.0, "not_met", "", "none", [f"{flag_name} not enabled"])

        # Override with explicit criterion inputs
        for ci in entity.criteria:
            cid = ci.criterion_id
            if ci.met:
                result[cid] = (1.0, "met", ci.evidence_description, ci.evidence_quality, ci.gaps)
            elif ci.partial:
                result[cid] = (0.5, "partial", ci.evidence_description, ci.evidence_quality, ci.gaps)
            else:
                result[cid] = (0.0, "not_met", ci.evidence_description, ci.evidence_quality,
                               ci.gaps or [f"{cid} not met"])

        # Fill any criteria not yet in result
        for c in READINESS_CRITERIA:
            if c["criterion_id"] not in result:
                result[c["criterion_id"]] = (
                    0.0, "not_met", "", "none", [f"No information provided for {c['criterion_id']}"]
                )

        return result

    @staticmethod
    def _build_domain_results(crs: List[CriterionResult]) -> List[DomainResult]:
        domains: Dict[str, List[CriterionResult]] = {}
        for cr in crs:
            domains.setdefault(cr.domain, []).append(cr)

        results = []
        for domain_id, items in domains.items():
            met = sum(1 for cr in items if cr.status == "met")
            partial = sum(1 for cr in items if cr.status == "partial")
            not_met = sum(1 for cr in items if cr.status == "not_met")
            total_w = sum(cr.weight for cr in items)
            earned_w = sum(cr.weighted_score for cr in items)
            score_pct = earned_w / max(total_w, 0.001) * 100
            blocking_gaps = [cr.title for cr in items if cr.blocking and cr.status == "not_met"]
            results.append(DomainResult(
                domain_id=domain_id,
                domain_label=items[0].domain_label,
                criteria_count=len(items),
                criteria_met=met,
                criteria_partial=partial,
                criteria_not_met=not_met,
                domain_score_pct=round(score_pct, 1),
                blocking_gaps=blocking_gaps,
            ))
        return results

    @staticmethod
    def _assess_standards_coverage(
        crs: List[CriterionResult], target_standard: str
    ) -> Dict[str, Dict[str, Any]]:
        coverage = {}
        for std_id in ASSURANCE_STANDARDS:
            relevant = [cr for cr in crs if std_id in cr.standards]
            if not relevant:
                continue
            met = sum(1 for cr in relevant if cr.status == "met")
            partial = sum(1 for cr in relevant if cr.status == "partial")
            score_pct = (met + partial * 0.5) / max(len(relevant), 1) * 100
            coverage[std_id] = {
                "standard_title": ASSURANCE_STANDARDS[std_id]["title"],
                "relevant_criteria": len(relevant),
                "met": met,
                "partial": partial,
                "not_met": len(relevant) - met - partial,
                "coverage_pct": round(score_pct, 1),
                "is_target": std_id == target_standard,
            }
        return coverage

    @staticmethod
    def _derive_tier(
        readiness_pct: float,
        blocking_count: int,
        level: str,
    ) -> str:
        if blocking_count > 5:
            return "not_ready"
        if blocking_count > 2:
            return "requires_remediation"
        threshold_ready = 85 if level == "limited" else 92
        threshold_near = 65 if level == "limited" else 75
        if readiness_pct >= threshold_ready and blocking_count == 0:
            return "ready"
        if readiness_pct >= threshold_near:
            return "nearly_ready"
        if readiness_pct >= 45:
            return "requires_remediation"
        return "not_ready"

    @staticmethod
    def _derive_gaps_actions(
        crs: List[CriterionResult],
        blocking_gaps: List[str],
        entity: AssuranceInput,
    ) -> tuple[List[str], List[str], int]:
        gaps: List[str] = []
        actions: List[str] = []
        weeks = 0

        # Blocking first
        for cr in crs:
            if cr.blocking and cr.status == "not_met":
                gap_msg = f"BLOCKING — {cr.criterion_id}: {cr.title} ({', '.join(cr.standards)})"
                gaps.append(gap_msg)
                actions.append(
                    f"Immediate: implement {cr.criterion_id} — {cr.title}. "
                    f"Reference: {cr.standards[0]}"
                )
                weeks += 4  # 4 weeks per blocking gap (rough estimate)

        # Non-blocking not-met
        non_block_gaps = [cr for cr in crs if not cr.blocking and cr.status == "not_met"]
        for cr in sorted(non_block_gaps, key=lambda x: x.weight, reverse=True)[:5]:
            gaps.append(f"{cr.criterion_id}: {cr.title}")
            actions.append(f"Remediate {cr.criterion_id}: {cr.title}")
            weeks += 2

        # Partial criteria
        partial_crs = [cr for cr in crs if cr.status == "partial"]
        for cr in sorted(partial_crs, key=lambda x: x.weight, reverse=True)[:3]:
            gaps.append(f"PARTIAL — {cr.criterion_id}: {cr.title}")
            weeks += 1

        # CSRD wave urgency
        if entity.csrd_wave == 1:
            gaps.insert(0, "CSRD Wave 1: limited assurance required for FY2025 reporting")
            actions.insert(0, "Engage assurance provider immediately — Wave 1 FY2025 deadline approaching")
            weeks = min(weeks, 24)  # capped urgency

        return gaps, actions, min(weeks, 52)
