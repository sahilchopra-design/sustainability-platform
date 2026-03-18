"""
API Routes: UK Sustainability Disclosure Requirements Engine (E11)
==================================================================
POST /api/v1/uk-sdr/assess              — Full SDR label eligibility + AGR + naming assessment
POST /api/v1/uk-sdr/assess/batch        — Batch: multiple products
POST /api/v1/uk-sdr/agr-check           — Standalone Anti-Greenwashing Rule check
GET  /api/v1/uk-sdr/ref/labels          — 4 SDR label definitions
GET  /api/v1/uk-sdr/ref/agr-requirements — 10-item AGR checklist
GET  /api/v1/uk-sdr/ref/naming-rules    — Naming and Marketing Requirements reference
GET  /api/v1/uk-sdr/ref/cross-framework — SDR ↔ SFDR / ISSB / EU Taxonomy mapping
GET  /api/v1/uk-sdr/ref/timeline        — SDR regulatory timeline
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.uk_sdr_engine import (
    UKSDREngine,
    ProductInput,
    SDR_LABELS,
    AGR_REQUIREMENTS,
    SDR_NAMING_RULES,
    SDR_CROSS_FRAMEWORK,
    UKSDRResult,
)

router = APIRouter(
    prefix="/api/v1/uk-sdr",
    tags=["UK SDR — Sustainability Disclosure Requirements"],
)

_ENGINE = UKSDREngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ProductInputModel(BaseModel):
    product_id: str
    product_name: str
    product_type: str = Field(
        "equity_fund",
        description="equity_fund | bond_fund | mixed_asset_fund | etf | private_equity | infrastructure_fund | private_debt",
    )
    aum_gbp: float = Field(100_000_000.0, description="AUM in GBP")
    domicile: str = Field("UK", description="UK | IE | LU | etc.")
    fca_authorised: bool = True
    distributor_type: str = Field("retail", description="retail | professional | institutional")

    # Sustainability characteristics
    qualifying_sustainable_pct: float = Field(0.0, ge=0, le=100, description="% of assets meeting label threshold")
    has_improvement_targets: bool = False
    has_measurable_impact_kpis: bool = False
    impact_additionality: bool = False
    uses_sustainability_terms_in_name: bool = False

    # Evidence
    sustainability_evidence_quality: str = Field("none", description="none | weak | adequate | strong")
    methodology_published: bool = False
    third_party_verified: bool = False
    data_coverage_pct: float = Field(0.0, ge=0, le=100)

    # AGR / naming
    claims_reviewed_by_legal: bool = False
    claims_updated_on_change: bool = False
    pre_contractual_disclosure_produced: bool = False
    ongoing_disclosure_produced: bool = False
    entity_disclosure_produced: bool = False

    # Cross-framework
    sfdr_classification: Optional[str] = Field(None, description="art_6 | art_8 | art_9")
    eu_taxonomy_alignment_pct: Optional[float] = None


class AssessRequest(BaseModel):
    product: ProductInputModel
    assessment_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class AGROnlyRequest(BaseModel):
    product: ProductInputModel


class BatchAssessRequest(BaseModel):
    products: List[AssessRequest]


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _label_result_to_dict(r) -> Dict[str, Any]:
    return {
        "label_id": r.label_id,
        "label_name": r.label_name,
        "eligible": r.eligible,
        "qualifying_pct": r.qualifying_pct,
        "threshold_pct": r.threshold_pct,
        "gaps": r.gaps,
        "conditions": r.conditions,
    }


def _agr_result_to_dict(r) -> Dict[str, Any]:
    return {
        "req_id": r.req_id,
        "title": r.title,
        "source": r.source,
        "blocking": r.blocking,
        "compliant": r.compliant,
        "status": r.status,
    }


def _naming_to_dict(n) -> Dict[str, Any]:
    return {
        "product_name": n.product_name,
        "contains_sustainability_terms": n.contains_sustainability_terms,
        "prohibited_terms_found": n.prohibited_terms_found,
        "label_held": n.label_held,
        "naming_compliant": n.naming_compliant,
        "required_actions": n.required_actions,
    }


def _result_to_dict(r: UKSDRResult) -> Dict[str, Any]:
    recommended_label_meta = SDR_LABELS.get(r.recommended_label, {}) if r.recommended_label else {}
    return {
        "run_id": r.run_id,
        "product_id": r.product_id,
        "product_name": r.product_name,
        "product_type": r.product_type,
        "aum_gbp": r.aum_gbp,
        "headline": {
            "recommended_label": r.recommended_label,
            "recommended_label_name": recommended_label_meta.get("label_name"),
            "overall_status": r.overall_status,
            "agr_compliant": r.agr_compliant,
            "agr_blocking_gaps": r.agr_blocking_gaps,
            "icis_score": r.icis_score,
            "icis_tier": r.icis_tier,
            "labels_eligible_count": sum(1 for lr in r.label_eligibility if lr.eligible),
        },
        "label_eligibility": [_label_result_to_dict(lr) for lr in r.label_eligibility],
        "agr_assessment": {
            "compliant": r.agr_compliant,
            "blocking_gaps": r.agr_blocking_gaps,
            "requirements": [_agr_result_to_dict(ar) for ar in r.agr_results],
        },
        "naming_assessment": _naming_to_dict(r.naming_assessment) if r.naming_assessment else None,
        "icis": {
            "score": r.icis_score,
            "tier": r.icis_tier,
            "description": {
                "exemplary": "ICIS ≥80 — robust evidence, third-party verified, published methodology",
                "robust": "ICIS 60-79 — adequate evidence with minor gaps",
                "developing": "ICIS 40-59 — partial evidence; AGR risk present",
                "inadequate": "ICIS <40 — insufficient evidence for sustainability claims",
            }.get(r.icis_tier, ""),
        },
        "sfdr_comparison": r.sfdr_comparison,
        "disclosure_obligations": r.disclosure_obligations,
        "priority_actions": r.priority_actions,
        "metadata": r.metadata,
    }


def _to_domain(m: ProductInputModel) -> ProductInput:
    return ProductInput(**m.model_dump())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full UK SDR label eligibility + AGR + naming assessment",
    description=(
        "Assesses a product for eligibility under the 4 UK SDR investment labels "
        "(Sustainable Focus, Sustainable Improvers, Sustainable Impact, Mixed Goals), "
        "checks Anti-Greenwashing Rule compliance (10 requirements), assesses product "
        "naming against FCA Naming and Marketing Requirements, calculates ICIS proxy "
        "score, and generates cross-framework mapping to SFDR/ISSB/EU Taxonomy."
    ),
)
def assess(req: AssessRequest):
    result = _ENGINE.assess(
        product=_to_domain(req.product),
        assessment_date=req.assessment_date,
    )
    return _result_to_dict(result)


@router.post(
    "/assess/batch",
    summary="Batch UK SDR assessment — multiple products",
    description="Run SDR label eligibility + AGR assessments for multiple products in one call.",
)
def assess_batch(req: BatchAssessRequest):
    results = []
    for a in req.products:
        r = _ENGINE.assess(
            product=_to_domain(a.product),
            assessment_date=a.assessment_date,
        )
        results.append(_result_to_dict(r))
    return {
        "batch_count": len(results),
        "products_with_label": sum(1 for r in results if r["headline"]["recommended_label"]),
        "products_agr_compliant": sum(1 for r in results if r["headline"]["agr_compliant"]),
        "products_naming_issues": sum(
            1 for r in results
            if r["naming_assessment"] and not r["naming_assessment"]["naming_compliant"]
        ),
        "assessments": results,
    }


@router.post(
    "/agr-check",
    summary="Standalone Anti-Greenwashing Rule (AGR) check",
    description=(
        "Runs only the 10-item Anti-Greenwashing Rule check (FCA AGR, effective 31 May 2024) "
        "without the full label eligibility assessment. Returns requirement-level compliance."
    ),
)
def agr_check(req: AGROnlyRequest):
    product = _to_domain(req.product)
    result = _ENGINE.assess(product=product)
    return {
        "product_id": product.product_id,
        "agr_compliant": result.agr_compliant,
        "blocking_gaps": result.agr_blocking_gaps,
        "requirements": [_agr_result_to_dict(ar) for ar in result.agr_results],
        "priority_actions": [a for a in result.priority_actions if "AGR" in a or "claim" in a.lower()],
    }


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/labels",
    summary="4 UK SDR investment label definitions",
)
def ref_labels():
    return {
        "count": len(SDR_LABELS),
        "labels": [
            {"label_id": k, **v}
            for k, v in SDR_LABELS.items()
        ],
        "regime": "FCA PS 23/16 — UK SDR and Investment Labels",
        "effective_date": "31 July 2024 (optional from launch; naming rules from 2 December 2024)",
    }


@router.get(
    "/ref/agr-requirements",
    summary="Anti-Greenwashing Rule (AGR) checklist — 10 requirements",
)
def ref_agr_requirements():
    blocking = sum(1 for r in AGR_REQUIREMENTS if r["blocking"])
    return {
        "total": len(AGR_REQUIREMENTS),
        "blocking": blocking,
        "effective_date": "31 May 2024",
        "requirements": AGR_REQUIREMENTS,
        "reference": "FCA COBS 4.15 + FCA AGR Policy Statement PS 23/16 §2",
    }


@router.get(
    "/ref/naming-rules",
    summary="FCA Naming and Marketing Requirements reference",
)
def ref_naming_rules():
    return {
        "effective_date": "2 December 2024",
        "reference": "FCA SDR Policy Statement PS 23/16 §4 + Naming and Marketing Rules (NMR)",
        "prohibited_without_label": SDR_NAMING_RULES["prohibited_without_label"],
        "key_rules": [
            "Using sustainability-related terms in a product name requires holding an SDR label (or clear qualification)",
            "Label name must be displayed prominently alongside all uses of sustainability terms",
            "Marketing materials must not create misleading impressions inconsistent with the product's characteristics",
            "FCA may issue stop orders or public censure for violations",
        ],
        "example_compliant": "Apex UK Sustainable Equity Fund — Sustainable Focus",
        "example_non_compliant": "Apex Green Fund (no label held, qualifying % < 70%)",
    }


@router.get(
    "/ref/cross-framework",
    summary="UK SDR ↔ SFDR / ISSB S1-S2 / EU Taxonomy cross-mapping",
)
def ref_cross_framework():
    return {
        "note": "Cross-framework mappings are approximate. A product eligible for an EU SFDR Article does not automatically qualify for the corresponding UK SDR label.",
        "mappings": [
            {"framework": fw, **meta}
            for fw, meta in SDR_CROSS_FRAMEWORK.items()
        ],
        "uk_taxonomy_status": "UK Green Taxonomy (GTAG) under development as of Q1 2025; onshored EU Taxonomy is interim reference",
        "issb_srs_status": "UK Sustainability Reporting Standards (UK SRS) endorsed January 2025 — entity-level disclosure; separate from SDR product labels",
    }


@router.get(
    "/ref/timeline",
    summary="UK SDR regulatory implementation timeline",
)
def ref_timeline():
    return {
        "regime": "UK Sustainability Disclosure Requirements (SDR) — FCA PS 23/16",
        "milestones": [
            {"date": "28 November 2023", "event": "FCA publishes PS 23/16 — SDR and Investment Labels Policy Statement"},
            {"date": "31 May 2024", "event": "Anti-Greenwashing Rule (AGR) comes into force — applies to all FCA-regulated firms"},
            {"date": "31 July 2024", "event": "SDR investment labels regime open — firms may voluntarily adopt labels"},
            {"date": "2 December 2024", "event": "Naming and Marketing Requirements come into force for UK UCITS/AIFs"},
            {"date": "2 April 2025", "event": "Consumer-facing product disclosures mandatory (pre-contractual + ongoing)"},
            {"date": "2 October 2025", "event": "Entity-level and annual product disclosures mandatory"},
            {"date": "2 April 2026", "event": "SDR requirements extended to portfolio management services"},
        ],
        "scope": {
            "in_scope": "FCA-authorised UK UCITS and UK AIFs; distribution in UK",
            "out_of_scope": "Offshore funds not distributed in UK; non-FCA authorised entities",
            "overseas_extension": "FCA consulting on extending labels to overseas funds distributed in UK (expected 2025-2026)",
        },
        "reference": "FCA PS 23/16 | FCA SDR webpage | FCA AGR Guidance (April 2024)",
    }
