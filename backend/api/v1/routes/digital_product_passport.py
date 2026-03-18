"""
API Routes: Digital Product Passport & Lifecycle Finance Engine (EU ESPR) — E82
================================================================================
POST /api/v1/digital-product-passport/espr-compliance        — ESPR applicability & compliance
POST /api/v1/digital-product-passport/dpp-schema             — DPP schema completeness
POST /api/v1/digital-product-passport/lifecycle-ghg          — Product carbon footprint (ISO 14044/PEF)
POST /api/v1/digital-product-passport/circularity-assessment — Circularity index (5 dimensions)
POST /api/v1/digital-product-passport/battery-regulation     — EU Battery Reg 2023/1542 compliance
POST /api/v1/digital-product-passport/epr-levy               — EPR levy calculation (20 MS)
POST /api/v1/digital-product-passport/full-assessment        — Complete DPP assessment
GET  /api/v1/digital-product-passport/ref/product-categories — ESPR categories + regulation refs
GET  /api/v1/digital-product-passport/ref/dpp-mandatory-fields — 25 mandatory DPP fields
GET  /api/v1/digital-product-passport/ref/epr-rates          — EPR levy rates by country
GET  /api/v1/digital-product-passport/ref/battery-targets    — EU Battery Reg recycled content targets
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.digital_product_passport_engine import (
    DigitalProductPassportEngine,
    DPP_MANDATORY_FIELDS,
    EPR_LEVY_RATES,
    ESPR_PRODUCT_CATEGORIES,
    EU_BATTERY_REGULATION_REQUIREMENTS,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/digital-product-passport",
    tags=["Digital Product Passport (ESPR)"],
)

_engine = DigitalProductPassportEngine()


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------


class ESPRComplianceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    product_name: str
    product_category: str
    gtin_ean: Optional[str] = None
    market_regions: List[str] = Field(default_factory=list)
    existing_certifications: List[str] = Field(default_factory=list)
    recycled_content_pct: Optional[float] = Field(None, ge=0, le=100)
    carbon_footprint_kg: Optional[float] = Field(None, ge=0)
    hazardous_substance_list: Optional[List[str]] = None


class DPPSchemaRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    product_name: str
    product_category: str
    available_data: Dict[str, bool] = Field(
        default_factory=dict,
        description="Map of field_id or field_name → True/False indicating data availability",
    )


class LifecycleGHGRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    product_name: str
    product_category: str
    annual_units: int = Field(1000, ge=1)
    product_weight_kg: Optional[float] = Field(None, ge=0)
    transport_km: Optional[float] = Field(None, ge=0)
    lifecycle_stage_data: Optional[Dict[str, float]] = Field(
        None,
        description="Optional per-stage kg CO2e overrides: raw_materials, manufacturing, "
                    "transport, use_phase, end_of_life",
    )


class CircularityRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    product_name: str
    product_category: Optional[str] = None
    recycled_content_pct: float = Field(0.0, ge=0, le=100)
    recyclability_score: float = Field(0.0, ge=0, le=100)
    durability_years: float = Field(0.0, ge=0)
    repairability_score: float = Field(0.0, ge=0, le=10)
    material_efficiency_pct: float = Field(0.0, ge=0, le=100)


class BatteryRegulationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    product_name: str
    battery_chemistry: str = Field(..., description="e.g. LFP, NMC, NCA, VRLA, NiMH")
    capacity_kwh: float = Field(..., ge=0)
    carbon_footprint_kg_per_kwh: float = Field(0.0, ge=0)
    recycled_li_pct: float = Field(0.0, ge=0, le=100)
    recycled_co_pct: float = Field(0.0, ge=0, le=100)
    recycled_ni_pct: float = Field(0.0, ge=0, le=100)
    recycled_pb_pct: float = Field(0.0, ge=0, le=100)
    has_supply_chain_dd: bool = False
    has_battery_passport: bool = False
    soh_accessible: bool = False


class EPRLevyRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    product_name: str
    product_category: str
    annual_volume_tonnes: float = Field(..., ge=0)
    annual_turnover_eur: Optional[float] = Field(None, ge=0)
    countries: List[str] = Field(
        default_factory=list,
        description="ISO 3166-1 alpha-2 country codes. Empty = all 20 supported MS.",
    )


class DPPFullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    product_name: str
    product_category: str
    gtin_ean: Optional[str] = None
    market_regions: List[str] = Field(default_factory=list)
    existing_certifications: List[str] = Field(default_factory=list)
    available_data: Dict[str, bool] = Field(default_factory=dict)
    annual_units: int = Field(1000, ge=1)
    product_weight_kg: Optional[float] = None
    recycled_content_pct: float = Field(0.0, ge=0, le=100)
    recyclability_score: float = Field(0.0, ge=0, le=100)
    durability_years: float = Field(0.0, ge=0)
    repairability_score: float = Field(0.0, ge=0, le=10)
    material_efficiency_pct: float = Field(0.0, ge=0, le=100)
    recycled_li_pct: float = Field(0.0, ge=0, le=100)
    recycled_co_pct: float = Field(0.0, ge=0, le=100)
    recycled_ni_pct: float = Field(0.0, ge=0, le=100)
    recycled_pb_pct: float = Field(0.0, ge=0, le=100)
    battery_chemistry: Optional[str] = None
    capacity_kwh: Optional[float] = None
    has_supply_chain_dd: bool = False
    has_battery_passport: bool = False
    soh_accessible: bool = False
    annual_volume_tonnes: Optional[float] = None
    annual_turnover_eur: Optional[float] = None
    carbon_footprint_kg: Optional[float] = None
    hazardous_substance_list: Optional[List[str]] = None
    lifecycle_stage_data: Optional[Dict[str, float]] = None


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------


@router.post("/espr-compliance", summary="ESPR applicability and compliance scoring")
async def espr_compliance(request: ESPRComplianceRequest) -> Dict[str, Any]:
    """
    Assess whether a product falls within ESPR scope (Regulation (EU) 2024/1781),
    identify applicable requirements, and compute a compliance score.
    """
    try:
        result = _engine.assess_espr_compliance(request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("ESPR compliance assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/dpp-schema", summary="DPP schema completeness assessment")
async def dpp_schema(request: DPPSchemaRequest) -> Dict[str, Any]:
    """
    Evaluate completeness of a product's Digital Product Passport data against
    the 25 mandatory fields defined in the EU DPP schema (draft 2025).
    """
    try:
        result = _engine.build_dpp_schema(request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("DPP schema assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/lifecycle-ghg", summary="Product carbon footprint (ISO 14044/PEF)")
async def lifecycle_ghg(request: LifecycleGHGRequest) -> Dict[str, Any]:
    """
    Calculate cradle-to-grave product carbon footprint per ISO 14044:2006 /
    ISO 14067:2018 / EU PEF methodology with per-lifecycle-stage breakdown.
    """
    try:
        payload = request.model_dump()
        stage_data = payload.pop("lifecycle_stage_data", None)
        result = _engine.calculate_lifecycle_ghg(payload, stage_data)
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("Lifecycle GHG calculation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/circularity-assessment", summary="Circularity index (5 dimensions)")
async def circularity_assessment(request: CircularityRequest) -> Dict[str, Any]:
    """
    Compute a circularity index (0-100) across 5 weighted dimensions:
    recycled content, recyclability, durability, repairability, material efficiency.
    Per ESPR Art 5 and EU Circular Economy Action Plan.
    """
    try:
        result = _engine.assess_circularity(request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("Circularity assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/battery-regulation", summary="EU Battery Regulation 2023/1542 compliance")
async def battery_regulation(request: BatteryRegulationRequest) -> Dict[str, Any]:
    """
    Assess compliance with Regulation (EU) 2023/1542 including carbon footprint
    declaration (Art 7), recycled content targets (Art 8, 2025/2030/2035),
    supply chain due diligence (Art 52-54), battery passport (Art 38-42),
    and state of health (Art 14).
    """
    try:
        result = _engine.assess_battery_regulation(request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("Battery regulation assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/epr-levy", summary="EPR scheme levy calculation across EU Member States")
async def epr_levy(request: EPRLevyRequest) -> Dict[str, Any]:
    """
    Calculate EPR levy exposure across up to 20 EU Member States
    (Directive 2008/98/EC Art 8a as transposed 2021-2024).
    Includes SME exemption assessment.
    """
    try:
        countries = request.countries if request.countries else None
        result = _engine.calculate_epr_levy(request.model_dump(), countries)
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("EPR levy calculation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/full-assessment", summary="Complete DPP assessment — all sub-modules")
async def full_assessment(request: DPPFullAssessmentRequest) -> Dict[str, Any]:
    """
    Orchestrate all DPP sub-modules (ESPR + DPP schema + LCA + Circularity +
    Battery + EPR) and return composite dpp_readiness_score and espr_tier.

    Weighting: ESPR 40% | DPP schema 25% | LCA 20% | Circularity 15%

    espr_tier: Ready | In Progress | At Risk | Non-Compliant
    """
    try:
        result = _engine.run_full_assessment(request.entity_id, request.model_dump())
        return {"status": "success", "entity_id": request.entity_id, "result": result}
    except Exception as exc:
        logger.exception("DPP full assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------


@router.get("/ref/product-categories", summary="ESPR product categories and regulation references")
async def ref_product_categories() -> Dict[str, Any]:
    """
    Return all 15 ESPR product categories with their regulation references,
    DPP mandatory year, key requirements, and PEF category rules.
    """
    return {
        "status": "success",
        "source": "Regulation (EU) 2024/1781 (ESPR) Annex I and Delegated Acts",
        "total_categories": len(ESPR_PRODUCT_CATEGORIES),
        "categories": ESPR_PRODUCT_CATEGORIES,
    }


@router.get("/ref/dpp-mandatory-fields", summary="25 mandatory DPP fields (EU DPP schema draft 2025)")
async def ref_dpp_mandatory_fields() -> Dict[str, Any]:
    """
    Return the 25 mandatory fields of the EU Digital Product Passport schema
    with field IDs, names, sections, and format guidance.
    """
    sections: Dict[str, List[Dict]] = {}
    for f in DPP_MANDATORY_FIELDS:
        sections.setdefault(f["section"], []).append(f)

    return {
        "status": "success",
        "source": "EU DPP schema draft Q1 2025; Regulation (EU) 2024/1781 Art 8",
        "total_mandatory_fields": len(DPP_MANDATORY_FIELDS),
        "fields": DPP_MANDATORY_FIELDS,
        "fields_by_section": sections,
    }


@router.get("/ref/epr-rates", summary="EPR levy rates by EU Member State")
async def ref_epr_rates() -> Dict[str, Any]:
    """
    Return EPR levy rates (EUR/tonne) for textiles, electronics, packaging,
    and furniture across 20 EU Member States.
    Source: national EPR scheme data (2024 rates).
    """
    summary = {
        cc: {
            "avg_rate_eur_tonne": round(sum(rates.values()) / len(rates), 0),
            "rates": rates,
        }
        for cc, rates in EPR_LEVY_RATES.items()
    }

    return {
        "status": "success",
        "source": "Directive 2008/98/EC Art 8a; national EPR scheme transpositions 2021-2024",
        "total_countries": len(EPR_LEVY_RATES),
        "currency": "EUR",
        "unit": "per tonne of product placed on market",
        "rates_by_country": summary,
    }


@router.get("/ref/battery-targets", summary="EU Battery Regulation recycled content targets")
async def ref_battery_targets() -> Dict[str, Any]:
    """
    Return EU Battery Regulation 2023/1542 recycled content targets for
    lithium, cobalt, nickel, and lead across 2025, 2030, and 2035 milestones.
    """
    recycled_req = EU_BATTERY_REGULATION_REQUIREMENTS["recycled_content_declaration"]
    return {
        "status": "success",
        "source": "Regulation (EU) 2023/1542 Art 8",
        "priority_materials": ["lithium", "cobalt", "nickel", "lead"],
        "targets": recycled_req["targets"],
        "description": recycled_req["description"],
        "all_requirements_overview": {
            k: {
                "article": v.get("article"),
                "description": v.get("description"),
                "effective_date": v.get("effective_date"),
            }
            for k, v in EU_BATTERY_REGULATION_REQUIREMENTS.items()
        },
    }
