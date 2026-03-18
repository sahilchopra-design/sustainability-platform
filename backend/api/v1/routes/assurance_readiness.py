"""
API Routes: Assurance Readiness Dashboard Engine (E10)
=======================================================
POST /api/v1/assurance-readiness/assess               — Full cross-module assurance readiness
POST /api/v1/assurance-readiness/assess/batch         — Batch: multiple entities
GET  /api/v1/assurance-readiness/ref/criteria         — 26-criterion readiness registry
GET  /api/v1/assurance-readiness/ref/standards        — Assurance standards (ISAE/ISSA/CSRD)
GET  /api/v1/assurance-readiness/ref/csrd-timeline    — CSRD wave phase-in timeline
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.assurance_readiness_engine import (
    AssuranceReadinessEngine,
    AssuranceInput,
    CriterionInput,
    READINESS_CRITERIA,
    ASSURANCE_STANDARDS,
)

router = APIRouter(
    prefix="/api/v1/assurance-readiness",
    tags=["Assurance Readiness"],
)

_ENGINE = AssuranceReadinessEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CriterionInputModel(BaseModel):
    criterion_id: str = Field(..., description="e.g. D1-1, D2-3 — from /ref/criteria")
    met: bool = False
    partial: bool = False
    evidence_description: str = ""
    evidence_quality: str = Field(
        "none",
        description="none | weak | adequate | strong",
    )
    gaps: List[str] = Field(default_factory=list)


class AssuranceInputModel(BaseModel):
    entity_id: str
    entity_name: str
    reporting_framework: str = Field(
        "CSRD_ESRS",
        description="CSRD_ESRS | GRI | ISSB | SFDR_ONLY",
    )
    assurance_standard_target: str = Field(
        "ISSA5000",
        description="ISAE3000 | ISAE3410 | ISSA5000 | CSRD_ART26A",
    )
    target_assurance_level: str = Field(
        "limited",
        description="limited | reasonable",
    )
    csrd_wave: Optional[int] = Field(None, description="1–4 (determines urgency)")
    reporting_year: str = ""

    # Explicit criterion overrides
    criteria: List[CriterionInputModel] = Field(default_factory=list)

    # Module-level flags (auto-derive criterion scores)
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


class AssessRequest(BaseModel):
    entity: AssuranceInputModel
    assessment_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class BatchAssessRequest(BaseModel):
    assessments: List[AssessRequest]


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def _criterion_result_to_dict(cr) -> Dict[str, Any]:
    return {
        "criterion_id": cr.criterion_id,
        "domain": cr.domain,
        "domain_label": cr.domain_label,
        "title": cr.title,
        "standards": cr.standards,
        "weight": cr.weight,
        "blocking": cr.blocking,
        "score": cr.score,
        "weighted_score": cr.weighted_score,
        "status": cr.status,
        "evidence_quality": cr.evidence_quality,
        "evidence_description": cr.evidence_description,
        "gaps": cr.gaps,
    }


def _domain_to_dict(d) -> Dict[str, Any]:
    return {
        "domain_id": d.domain_id,
        "domain_label": d.domain_label,
        "criteria_count": d.criteria_count,
        "criteria_met": d.criteria_met,
        "criteria_partial": d.criteria_partial,
        "criteria_not_met": d.criteria_not_met,
        "domain_score_pct": d.domain_score_pct,
        "blocking_gaps": d.blocking_gaps,
    }


def _result_to_dict(r) -> Dict[str, Any]:
    return {
        "run_id": r.run_id,
        "entity_id": r.entity_id,
        "entity_name": r.entity_name,
        "reporting_framework": r.reporting_framework,
        "assurance_standard_target": r.assurance_standard_target,
        "target_assurance_level": r.target_assurance_level,
        "csrd_wave": r.csrd_wave,
        "reporting_year": r.reporting_year,
        "assessment_date": r.assessment_date,
        "headline": {
            "overall_readiness_score_pct": r.overall_readiness_score_pct,
            "readiness_tier": r.readiness_tier,
            "blocking_gaps_count": r.blocking_gaps_count,
            "estimated_remediation_weeks": r.estimated_remediation_weeks,
        },
        "domain_results": [_domain_to_dict(d) for d in r.domain_results],
        "criterion_results": [_criterion_result_to_dict(cr) for cr in r.criterion_results],
        "blocking_gaps": r.blocking_gaps,
        "standards_coverage": r.standards_coverage,
        "gaps": r.gaps,
        "priority_actions": r.priority_actions,
        "metadata": r.metadata,
    }


def _to_domain(m: AssuranceInputModel) -> AssuranceInput:
    d = m.model_dump()
    d["criteria"] = [CriterionInput(**c) for c in d["criteria"]]
    return AssuranceInput(**d)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full cross-module assurance readiness assessment",
    description=(
        "Scores an entity's sustainability reporting against 26 assurance readiness "
        "criteria across 8 domains (data governance, GHG, EU Taxonomy, ESRS datapoints, "
        "SFDR/PAI, internal controls, materiality, disclosure completeness). "
        "Maps to ISAE 3000, ISAE 3410, ISSA 5000, CSRD Art 26a. "
        "Returns readiness tier (ready/nearly_ready/requires_remediation/not_ready), "
        "blocking gaps, domain scores, and prioritised remediation actions."
    ),
)
def assess(req: AssessRequest):
    result = _ENGINE.assess(
        entity=_to_domain(req.entity),
        assessment_date=req.assessment_date,
    )
    return _result_to_dict(result)


@router.post(
    "/assess/batch",
    summary="Batch assurance readiness — multiple entities",
    description="Run the assurance readiness assessment for multiple entities in one call.",
)
def assess_batch(req: BatchAssessRequest):
    results = []
    for a in req.assessments:
        r = _ENGINE.assess(
            entity=_to_domain(a.entity),
            assessment_date=a.assessment_date,
        )
        results.append(_result_to_dict(r))
    return {
        "batch_count": len(results),
        "entities_ready": sum(1 for r in results if r["headline"]["readiness_tier"] == "ready"),
        "entities_not_ready": sum(1 for r in results if r["headline"]["readiness_tier"] == "not_ready"),
        "total_blocking_gaps": sum(r["headline"]["blocking_gaps_count"] for r in results),
        "assessments": results,
    }


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/criteria",
    summary="Assurance readiness criteria registry (26 criteria, 8 domains)",
)
def ref_criteria():
    domains: Dict[str, List[Dict[str, Any]]] = {}
    for c in READINESS_CRITERIA:
        domains.setdefault(c["domain"], []).append({
            "criterion_id": c["criterion_id"],
            "title": c["title"],
            "standards": c["standards"],
            "weight": c["weight"],
            "blocking": c["blocking"],
            "description": c["description"],
        })
    return {
        "total_criteria": len(READINESS_CRITERIA),
        "blocking_criteria": sum(1 for c in READINESS_CRITERIA if c["blocking"]),
        "domains": [
            {
                "domain_id": domain_id,
                "domain_label": items[0]["criterion_id"].split("-")[0],
                "criteria": items,
            }
            for domain_id, items in domains.items()
        ],
        "reference": (
            "ISAE 3000 (Rev.) | ISAE 3410 | ISSA 5000 (IAASB 2025) | "
            "CSRD Art 26a | AA1000 AS v3"
        ),
    }


@router.get(
    "/ref/standards",
    summary="Sustainability assurance standards registry",
)
def ref_standards():
    return {
        "count": len(ASSURANCE_STANDARDS),
        "standards": [
            {"standard_id": sid, **meta}
            for sid, meta in ASSURANCE_STANDARDS.items()
        ],
    }


@router.get(
    "/ref/csrd-timeline",
    summary="CSRD Art 26a limited assurance phase-in timeline (Waves 1–4)",
)
def ref_csrd_timeline():
    return {
        "assurance_requirement": "Limited assurance on ESRS sustainability statement (Art 26a CSRD)",
        "long_term_trajectory": "Reasonable assurance after Commission review (earliest FY2028+)",
        "waves": {
            "wave_1": {
                "label": "Existing NFRD entities + listed companies >500 employees",
                "first_reporting_year": "FY2025",
                "disclosure_deadline": "2026 (calendar year following reporting year)",
                "assurance_from": "FY2025 reports (published in 2026)",
                "estimated_entity_count": "~11,700 EU entities",
            },
            "wave_2": {
                "label": "Large companies per EU Accounting Directive (non-NFRD)",
                "first_reporting_year": "FY2026",
                "disclosure_deadline": "2027",
                "assurance_from": "FY2026 reports",
                "estimated_entity_count": "~49,000 EU entities",
            },
            "wave_3": {
                "label": "Listed SMEs (EU regulated markets)",
                "first_reporting_year": "FY2027",
                "disclosure_deadline": "2028",
                "assurance_from": "FY2027 reports",
                "opt_out": "2-year opt-out available until FY2029",
            },
            "wave_4": {
                "label": "Third-country large entities with EU subsidiary/branch >€150M turnover",
                "first_reporting_year": "FY2028",
                "disclosure_deadline": "2029",
                "assurance_from": "FY2028 reports",
                "standard": "ESRS standards adopted for third-country undertakings",
            },
        },
        "assurance_provider_eligibility": (
            "Statutory auditor OR accredited independent assurance provider "
            "per Art 34(1)(aa) Accounting Directive as amended by CSRD"
        ),
        "reference": (
            "CSRD Directive (EU) 2022/2464 | "
            "Art 26a Accounting Directive 2013/34/EU (as amended) | "
            "ISSA 5000 (IAASB) — expected effective for FY2026 engagements"
        ),
    }
