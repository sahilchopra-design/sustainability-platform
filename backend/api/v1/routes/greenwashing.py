"""
Greenwashing Risk & Substantiation API routes.
Prefix: /api/v1/greenwashing
Tags: Greenwashing Risk
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.greenwashing_engine import get_engine

router = APIRouter(prefix="/api/v1/greenwashing", tags=["Greenwashing Risk"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ClaimItem(BaseModel):
    text: str = Field(..., example="Our fund is 100% sustainable and carbon neutral")
    type: str = Field(default="qualitative", example="qualitative")


class AssessRequest(BaseModel):
    entity_id: str
    entity_name: str
    claims: list[ClaimItem] = Field(default_factory=list)
    product_labels: list[str] = Field(default_factory=list, example=["sfdr_article_9", "eu_taxonomy_aligned"])
    sfdr_classification: str = Field(default="8", example="9")
    taxonomy_alignment_pct: float = Field(default=0.0, ge=0.0, le=100.0, example=35.0)


class ScreenClaimRequest(BaseModel):
    claim_text: str = Field(..., example="This product is eco-friendly and carbon neutral")
    claim_type: str = Field(default="qualitative", example="quantitative")


class VerifyLabelsRequest(BaseModel):
    entity_id: str
    labels: list[str] = Field(..., example=["sfdr_article_9"])
    sfdr_art: str = Field(default="9", example="9")
    taxonomy_pct: float = Field(default=0.0, ge=0.0, le=100.0, example=25.0)


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
def assess(req: AssessRequest) -> dict:
    """
    Full greenwashing risk assessment for an entity.
    Screens all claims, verifies labels, scores EU and FCA compliance,
    and provides remediation actions.
    """
    try:
        engine = get_engine()
        claims_dicts = [c.dict() for c in req.claims]
        result = engine.assess(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            claims=claims_dicts,
            product_labels=req.product_labels,
            sfdr_classification=req.sfdr_classification,
            taxonomy_alignment_pct=req.taxonomy_alignment_pct,
        )
        return asdict(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/screen-claim")
def screen_claim(req: ScreenClaimRequest) -> dict:
    """
    Screen a single sustainability claim for greenwashing risk.
    Returns risk level, matched problematic terms, substantiation score,
    and regulatory references (EU GCD + FCA AGR).
    """
    try:
        engine = get_engine()
        return engine.screen_claim(claim_text=req.claim_text, claim_type=req.claim_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/verify-labels")
def verify_labels(req: VerifyLabelsRequest) -> dict:
    """
    Verify sustainability label usage against SFDR, SDR and EU Taxonomy rules.
    Checks SFDR Article 8/9 consistency, SDR label criteria, and taxonomy alignment.
    """
    try:
        engine = get_engine()
        return engine.verify_labels(
            entity_id=req.entity_id,
            labels=req.labels,
            sfdr_art=req.sfdr_art,
            taxonomy_pct=req.taxonomy_pct,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/misleading-terms")
def ref_misleading_terms() -> list:
    """Reference: 40 vague/misleading sustainability terms with risk levels and substantiation requirements."""
    try:
        return get_engine().ref_misleading_terms()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/claim-types")
def ref_claim_types() -> dict:
    """Reference: Claim type definitions (quantitative, qualitative, label, comparative, forward_looking) with requirements."""
    try:
        return get_engine().ref_claim_types()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/eu-requirements")
def ref_eu_requirements() -> list:
    """Reference: 8 EU Green Claims Directive (COM/2023/166) requirements with article citations."""
    try:
        return get_engine().ref_eu_requirements()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/fca-requirements")
def ref_fca_requirements() -> list:
    """Reference: 6 FCA Anti-Greenwashing Rule (SDR PS23/16) and Consumer Duty (PS22/9) requirements."""
    try:
        return get_engine().ref_fca_requirements()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/label-rules")
def ref_label_rules() -> dict:
    """Reference: Label verification rules for SFDR Art 8/9, UK SDR labels (Focus/Improvers/Impact/Mixed), EU Taxonomy."""
    try:
        return get_engine().ref_label_rules()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
