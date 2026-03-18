"""
API Routes: MiFID II Sustainability Preferences Engine (E12)
=============================================================
POST /api/v1/mifid-spt/assess                  — Single client preference assessment
POST /api/v1/mifid-spt/assess/batch            — Batch: multiple client/product pairs
POST /api/v1/mifid-spt/suitability-report      — Generate suitability report text from result
GET  /api/v1/mifid-spt/ref/preference-categories — 3 preference category definitions
GET  /api/v1/mifid-spt/ref/product-esg-types     — SFDR Art 6/8/9 product ESG types
GET  /api/v1/mifid-spt/ref/suitability-process   — 5-step Art 25(2) suitability process
GET  /api/v1/mifid-spt/ref/cross-framework       — MiFID II SPT ↔ SFDR / EU Taxonomy / CSRD
GET  /api/v1/mifid-spt/ref/timeline              — MiFID II SPT regulatory timeline
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.mifid_spt_engine import (
    MiFIDSPTEngine,
    ClientPreferences,
    ProductProfile,
    PREFERENCE_CATEGORIES,
    PRODUCT_ESG_TYPES,
    SUITABILITY_PROCESS_STEPS,
    MIFID_CROSS_FRAMEWORK,
)

router = APIRouter(
    prefix="/api/v1/mifid-spt",
    tags=["MiFID II — Sustainability Preferences"],
)

_ENGINE = MiFIDSPTEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ClientPreferencesModel(BaseModel):
    client_id: str
    name: str
    preference_category_a_min_pct: float = Field(
        0.0,
        ge=0.0, le=100.0,
        description="Minimum EU Taxonomy-aligned % required (Category A)",
    )
    preference_category_b_min_pct: float = Field(
        0.0,
        ge=0.0, le=100.0,
        description="Minimum SFDR sustainable investment % required (Category B)",
    )
    preference_category_c: bool = Field(
        False,
        description="Whether client requires PAI consideration (Category C)",
    )
    investor_type: str = Field(
        "retail",
        description="retail | professional | eligible_counterparty",
    )
    risk_profile: str = Field(
        "balanced",
        description="conservative | balanced | growth | aggressive",
    )


class ProductProfileModel(BaseModel):
    product_id: str
    product_name: str
    product_type: str = Field(
        "article_8_with_commitment",
        description="article_9 | article_8_with_commitment | article_8_without_commitment | article_6",
    )
    taxonomy_alignment_pct: float = Field(0.0, ge=0.0, le=100.0)
    sfdr_sustainable_investment_pct: float = Field(0.0, ge=0.0, le=100.0)
    considers_pais: bool = False
    sfdr_article: str = Field("art_8", description="art_6 | art_8 | art_9")
    domicile: str = Field("IE", description="Fund domicile (ISO country code)")


class AssessmentRequest(BaseModel):
    client: ClientPreferencesModel
    products: List[ProductProfileModel]


class BatchAssessmentItem(BaseModel):
    client: ClientPreferencesModel
    products: List[ProductProfileModel]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Single client preference assessment (Art 25(2) MiFID II)")
def assess(request: AssessmentRequest) -> Dict[str, Any]:
    """
    Run MiFID II Art 25(2) sustainability preference suitability matching for one client
    against a list of products.  Returns matched products, match rate, and suitability notes.
    """
    client = ClientPreferences(
        client_id=request.client.client_id,
        name=request.client.name,
        preference_category_a_min_pct=request.client.preference_category_a_min_pct,
        preference_category_b_min_pct=request.client.preference_category_b_min_pct,
        preference_category_c=request.client.preference_category_c,
        investor_type=request.client.investor_type,
        risk_profile=request.client.risk_profile,
    )
    products = [
        ProductProfile(
            product_id=p.product_id,
            product_name=p.product_name,
            product_type=p.product_type,
            taxonomy_alignment_pct=p.taxonomy_alignment_pct,
            sfdr_sustainable_investment_pct=p.sfdr_sustainable_investment_pct,
            considers_pais=p.considers_pais,
            sfdr_article=p.sfdr_article,
            domicile=p.domicile,
        )
        for p in request.products
    ]
    result = _ENGINE.assess_client_preferences(client, products)
    return result.to_dict()


@router.post("/assess/batch", summary="Batch client preference assessments")
def assess_batch(requests: List[BatchAssessmentItem]) -> List[Dict[str, Any]]:
    """
    Run Art 25(2) suitability preference matching for multiple client/product pairs.
    Each item in the request body contains a client and a product list.
    """
    results = []
    for item in requests:
        client = ClientPreferences(
            client_id=item.client.client_id,
            name=item.client.name,
            preference_category_a_min_pct=item.client.preference_category_a_min_pct,
            preference_category_b_min_pct=item.client.preference_category_b_min_pct,
            preference_category_c=item.client.preference_category_c,
            investor_type=item.client.investor_type,
            risk_profile=item.client.risk_profile,
        )
        products = [
            ProductProfile(
                product_id=p.product_id,
                product_name=p.product_name,
                product_type=p.product_type,
                taxonomy_alignment_pct=p.taxonomy_alignment_pct,
                sfdr_sustainable_investment_pct=p.sfdr_sustainable_investment_pct,
                considers_pais=p.considers_pais,
                sfdr_article=p.sfdr_article,
                domicile=p.domicile,
            )
            for p in item.products
        ]
        result = _ENGINE.assess_client_preferences(client, products)
        results.append(result.to_dict())
    return results


class SuitabilityReportRequest(BaseModel):
    result: Dict[str, Any] = Field(
        ..., description="MiFIDSPTResult dict from /assess endpoint"
    )


@router.post(
    "/suitability-report",
    summary="Generate suitability report text (Art 25(6) MiFID II)",
)
def suitability_report(request: SuitabilityReportRequest) -> Dict[str, str]:
    """
    Generate human-readable suitability report text blocks from a MiFIDSPTResult dict.
    Required for Art 25(6) MiFID II written suitability report documentation.
    """
    return _ENGINE.generate_suitability_report_text(request.result)


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/preference-categories",
    summary="Art 2(7) MiFID II — 3 sustainability preference categories",
)
def ref_preference_categories() -> Dict[str, Any]:
    return _ENGINE.get_preference_categories()


@router.get(
    "/ref/product-esg-types",
    summary="SFDR product ESG types and typical sustainability metrics",
)
def ref_product_esg_types() -> Dict[str, Any]:
    return _ENGINE.get_product_esg_types()


@router.get(
    "/ref/suitability-process",
    summary="Art 25(2) MiFID II — 5-step suitability process",
)
def ref_suitability_process() -> List[Dict[str, Any]]:
    return _ENGINE.get_suitability_process()


@router.get(
    "/ref/cross-framework",
    summary="MiFID II SPT ↔ SFDR / EU Taxonomy / CSRD / EBA cross-framework mapping",
)
def ref_cross_framework() -> Dict[str, str]:
    return _ENGINE.get_cross_framework()


@router.get(
    "/ref/timeline",
    summary="MiFID II SPT regulatory timeline (2021-2025)",
)
def ref_timeline() -> List[Dict[str, str]]:
    return _ENGINE.get_timeline()
