"""
API Routes: PRIIPs KID ESG Engine (E15)
========================================
POST /api/v1/priips-kid/generate-kid           — Full PRIIPs KID generation
POST /api/v1/priips-kid/assess-sri             — Standalone SRI calculation
POST /api/v1/priips-kid/calculate-scenarios    — 4 performance scenarios
POST /api/v1/priips-kid/esg-inserts            — ESG insert list for a SFDR classification
POST /api/v1/priips-kid/generate-kid/batch     — Batch KID generation
GET  /api/v1/priips-kid/ref/kid-sections       — 6 KID section definitions
GET  /api/v1/priips-kid/ref/sri-classes        — SRI market risk class table
GET  /api/v1/priips-kid/ref/esg-insert-types   — ESG insert type registry
GET  /api/v1/priips-kid/ref/cross-framework    — PRIIPs ↔ SFDR / EU Taxonomy / MiFID II / UK
GET  /api/v1/priips-kid/ref/timeline           — PRIIPs regulatory timeline
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.priips_kid_engine import (
    PRIIPSKIDEngine,
    KIDProductInput,
    KID_SECTIONS,
    SRI_MARKET_RISK_CLASSES,
    ESG_INSERT_TYPES,
    PRIIPS_CROSS_FRAMEWORK,
)

router = APIRouter(
    prefix="/api/v1/priips-kid",
    tags=["PRIIPs — Key Information Document ESG Engine"],
)

_ENGINE = PRIIPSKIDEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class KIDProductInputModel(BaseModel):
    product_id: str
    product_name: str
    product_type: str = Field(
        "UCITS",
        description="UCITS | AIF | Structured Product | Insurance-Based Investment Product | etc.",
    )
    isin: str = Field("", description="ISIN (leave blank if not yet assigned)")
    manufacturer: str = Field("", description="PRIIP manufacturer / management company name")
    rhp_years: int = Field(5, ge=1, le=40, description="Recommended Holding Period in years")
    annual_volatility: float = Field(
        0.15, ge=0.0,
        description="Annualised return volatility (e.g. 0.15 = 15%) used for SRI calculation",
    )
    credit_quality: str = Field(
        "investment_grade",
        description="investment_grade | sub_investment_grade | unrated",
    )
    sfdr_classification: str = Field(
        "art_6",
        description="art_6 | art_8 | art_8_pai | art_8_taxonomy | art_9",
    )
    considers_pais: bool = Field(
        False,
        description="Whether product considers principal adverse impacts",
    )
    taxonomy_alignment_pct: float = Field(
        0.0, ge=0.0, le=100.0,
        description="% of investments that are EU Taxonomy-aligned",
    )
    entry_cost_pct: float = Field(0.0, ge=0.0, description="Entry cost as % of investment")
    exit_cost_pct: float = Field(0.0, ge=0.0, description="Exit cost as % of investment")
    ongoing_cost_pct: float = Field(
        1.5, ge=0.0, description="Ongoing charges figure (OCF) as % p.a."
    )
    performance_fee_pct: float = Field(
        0.0, ge=0.0, description="Performance fee as % p.a. (estimate)"
    )
    transaction_cost_pct: float = Field(
        0.1, ge=0.0, description="Portfolio transaction costs as % p.a."
    )
    expected_annual_return_pct: float = Field(
        5.0,
        description="Expected annual return % (pre-cost) used for performance scenarios",
    )


class ESGInsertsRequest(BaseModel):
    sfdr_classification: str = Field(
        ...,
        description="art_6 | art_8 | art_8_pai | art_8_taxonomy | art_9",
    )
    product_name: str = Field(
        "[Product]",
        description="Product name used in template text blocks",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_product_input(model: KIDProductInputModel) -> KIDProductInput:
    return KIDProductInput(
        product_id=model.product_id,
        product_name=model.product_name,
        product_type=model.product_type,
        isin=model.isin,
        manufacturer=model.manufacturer,
        rhp_years=model.rhp_years,
        annual_volatility=model.annual_volatility,
        credit_quality=model.credit_quality,
        sfdr_classification=model.sfdr_classification,
        considers_pais=model.considers_pais,
        taxonomy_alignment_pct=model.taxonomy_alignment_pct,
        entry_cost_pct=model.entry_cost_pct,
        exit_cost_pct=model.exit_cost_pct,
        ongoing_cost_pct=model.ongoing_cost_pct,
        performance_fee_pct=model.performance_fee_pct,
        transaction_cost_pct=model.transaction_cost_pct,
        expected_annual_return_pct=model.expected_annual_return_pct,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/generate-kid",
    summary="Generate full PRIIPs KID with SRI, scenarios, costs and ESG inserts",
)
def generate_kid(request: KIDProductInputModel) -> Dict[str, Any]:
    """
    Generate a complete PRIIPs KID covering:
    - SRI (1-7) based on volatility and credit quality
    - 4 performance scenarios (stress / unfavourable / moderate / favourable)
    - Cost summary with RIY (Reduction in Yield)
    - SFDR ESG inserts (Art 6 / Art 8 / Art 9)
    - KID completeness validation
    """
    inp = _build_product_input(request)
    result = _ENGINE.generate_kid(inp)
    return result.to_dict()


@router.post(
    "/assess-sri",
    summary="Standalone SRI calculation (1-7) per PRIIPs Annex II",
)
def assess_sri(request: KIDProductInputModel) -> Dict[str, Any]:
    """
    Calculate the Summary Risk Indicator (SRI) from annual volatility (market risk class)
    and credit quality (credit risk class).  Final SRI = max(MRC, adjusted CRC).
    """
    inp = _build_product_input(request)
    result = _ENGINE.assess_sri(inp)
    return result.to_dict()


@router.post(
    "/calculate-scenarios",
    summary="Generate 4 PRIIPs performance scenarios",
)
def calculate_scenarios(request: KIDProductInputModel) -> List[Dict[str, Any]]:
    """
    Generate stress, unfavourable, moderate and favourable performance scenarios
    per the revised PRIIPs RTS Annex IV methodology (Regulation 2021/2268).
    Returns annualised returns and final value per EUR 10,000 invested.
    """
    inp = _build_product_input(request)
    scenarios = _ENGINE.calculate_scenarios(inp)
    return [s.to_dict() for s in scenarios]


@router.post(
    "/esg-inserts",
    summary="Get required SFDR ESG inserts for a PRIIPs KID",
)
def esg_inserts(request: ESGInsertsRequest) -> List[Dict[str, Any]]:
    """
    Return the ESG text inserts required in the PRIIPs KID for the given SFDR classification.
    Art 6 → sustainability risk only.
    Art 8 → sustainability risk + ESG characteristics.
    Art 8 (PAI) → adds PAI consideration statement.
    Art 8 (taxonomy) → adds taxonomy alignment disclosure.
    Art 9 → all 5 inserts including sustainable investment objective.
    """
    inserts = _ENGINE.get_esg_inserts(
        sfdr_classification=request.sfdr_classification,
        product_name=request.product_name,
    )
    return [i.to_dict() for i in inserts]


@router.post(
    "/generate-kid/batch",
    summary="Batch PRIIPs KID generation for multiple products",
)
def generate_kid_batch(requests: List[KIDProductInputModel]) -> List[Dict[str, Any]]:
    """
    Generate PRIIPs KIDs for multiple products in a single request.
    """
    results = []
    for request in requests:
        inp = _build_product_input(request)
        result = _ENGINE.generate_kid(inp)
        results.append(result.to_dict())
    return results


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/kid-sections",
    summary="PRIIPs KID — 6 mandatory section definitions",
)
def ref_kid_sections() -> Dict[str, Any]:
    return _ENGINE.get_kid_sections()


@router.get(
    "/ref/sri-classes",
    summary="SRI market risk class table (volatility ranges 1-7)",
)
def ref_sri_classes() -> Dict[str, Any]:
    return _ENGINE.get_sri_classes()


@router.get(
    "/ref/esg-insert-types",
    summary="ESG insert type registry — SFDR Art 3/4/8/9 and EU Taxonomy Art 6",
)
def ref_esg_insert_types() -> Dict[str, Any]:
    return _ENGINE.get_esg_insert_types()


@router.get(
    "/ref/cross-framework",
    summary="PRIIPs ↔ SFDR / EU Taxonomy / MiFID II SPT / UK PRIIPs / UCITS KIID mapping",
)
def ref_cross_framework() -> Dict[str, str]:
    return _ENGINE.get_cross_framework()


@router.get(
    "/ref/timeline",
    summary="PRIIPs regulatory timeline (2014 → 2024)",
)
def ref_timeline() -> List[Dict[str, str]]:
    return _ENGINE.get_timeline()
