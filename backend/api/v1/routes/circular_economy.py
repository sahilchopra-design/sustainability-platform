"""
API Routes: Circular Economy Finance (E55)
==========================================
POST /api/v1/circular-economy/esrs-e5           — CSRD ESRS E5 disclosure scoring
POST /api/v1/circular-economy/mci               — EMF Material Circularity Indicator
POST /api/v1/circular-economy/wbcsd-cti         — WBCSD CTI v4.0 composite score
POST /api/v1/circular-economy/epr-compliance    — EU EPR cost calculation
POST /api/v1/circular-economy/crm-risk          — EU CRM Act 2023 dependency analysis
POST /api/v1/circular-economy/lca               — ISO 14044 cradle-to-cradle LCA
POST /api/v1/circular-economy/material-flows    — Material flow circularity analysis
POST /api/v1/circular-economy/overall-circularity — Aggregated circularity score
GET  /api/v1/circular-economy/ref/crm-list      — EU CRM Act 2023 list of 34 materials
GET  /api/v1/circular-economy/ref/epr-rates     — EPR cost rates by country and category
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from services.circular_economy_engine import (
    CircularEconomyEngine,
    EU_CRM_LIST,
    EU_STRATEGIC_RM,
    EU_CRM_2030_TARGETS,
    EPR_COSTS,
)

router = APIRouter(
    prefix="/api/v1/circular-economy",
    tags=["Circular Economy"],
)

_engine = CircularEconomyEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ESRSE5Request(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    resource_inflows_t: float = Field(..., ge=0)
    recycled_inflows_pct: float = Field(..., ge=0, le=100)
    resource_outflows_t: float = Field(..., ge=0)
    waste_t: float = Field(..., ge=0)


class MCIRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    recycled_input_fraction: float = Field(..., ge=0, le=1)
    waste_recovery_fraction: float = Field(..., ge=0, le=1)
    product_lifetime_multiplier: float = Field(1.0, ge=0.1, le=10.0)


class WBCSDCTIRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    entity_name: str
    sector: str = Field(..., description="automotive | electronics | textiles | construction | chemicals | food | metals | plastics | other")


class EPRComplianceRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    packaging_tonnes: float = Field(0.0, ge=0)
    ewaste_tonnes: float = Field(0.0, ge=0)
    battery_tonnes: float = Field(0.0, ge=0)
    country: str = Field("EU", description="ISO-2 country code or EU for average")


class CRMRiskRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    materials_used: list[str] = Field(..., description="List of material names to screen against EU CRM list")


class LCARequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    product_name: str
    annual_production: float = Field(..., ge=0)
    sector: str = Field(..., description="automotive | electronics | textiles | construction | chemicals | food | metals | plastics | other")


class MaterialItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    primary_input_t: float = Field(0.0, ge=0)
    recycled_input_t: float = Field(0.0, ge=0)
    bio_based_input_t: float = Field(0.0, ge=0)


class MaterialFlowsRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    materials: list[MaterialItem] = Field(..., min_length=1)


class OverallCircularityRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity_id: str
    esrs_score: float = Field(..., ge=0, le=100, description="ESRS E5 disclosure score 0-100")
    mci_score: float = Field(..., ge=0, le=1, description="EMF MCI 0-1")
    cti_score: float = Field(..., ge=0, le=100, description="WBCSD CTI composite 0-100")
    lca_benefit_pct: float = Field(..., ge=0, le=100, description="LCA circularity benefit %")


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/esrs-e5")
def esrs_e5(req: ESRSE5Request) -> dict:
    """CSRD ESRS E5 resource use and circular economy disclosure assessment."""
    return _engine.assess_esrs_e5(
        entity_id=req.entity_id,
        resource_inflows_t=req.resource_inflows_t,
        recycled_inflows_pct=req.recycled_inflows_pct,
        resource_outflows_t=req.resource_outflows_t,
        waste_t=req.waste_t,
    )


@router.post("/mci")
def mci(req: MCIRequest) -> dict:
    """Ellen MacArthur Foundation Material Circularity Indicator (0-1 scale)."""
    return _engine.calculate_mci(
        entity_id=req.entity_id,
        recycled_input_fraction=req.recycled_input_fraction,
        waste_recovery_fraction=req.waste_recovery_fraction,
        product_lifetime_multiplier=req.product_lifetime_multiplier,
    )


@router.post("/wbcsd-cti")
def wbcsd_cti(req: WBCSDCTIRequest) -> dict:
    """WBCSD Circular Transition Indicators v4.0 — 4-dimension circular scorecard."""
    return _engine.assess_wbcsd_cti(
        entity_id=req.entity_id,
        entity_name=req.entity_name,
        sector=req.sector,
    )


@router.post("/epr-compliance")
def epr_compliance(req: EPRComplianceRequest) -> dict:
    """EU EPR cost calculation for packaging, e-waste, and battery streams."""
    return _engine.calculate_epr_compliance(
        entity_id=req.entity_id,
        packaging_tonnes=req.packaging_tonnes,
        ewaste_tonnes=req.ewaste_tonnes,
        battery_tonnes=req.battery_tonnes,
        country=req.country,
    )


@router.post("/crm-risk")
def crm_risk(req: CRMRiskRequest) -> dict:
    """EU CRM Act 2023 dependency assessment with supply risk and 2030 target gaps."""
    return _engine.assess_crm_risk(
        entity_id=req.entity_id,
        materials_used=req.materials_used,
    )


@router.post("/lca")
def lca(req: LCARequest) -> dict:
    """ISO 14044 LCA: cradle-to-gate vs cradle-to-cradle circularity benefit."""
    return _engine.perform_lca(
        entity_id=req.entity_id,
        product_name=req.product_name,
        annual_production=req.annual_production,
        sector=req.sector,
    )


@router.post("/material-flows")
def material_flows(req: MaterialFlowsRequest) -> dict:
    """Material flow analysis: recycled input %, CRM exposure, EU 2030 compliance."""
    materials_dicts = [m.model_dump() for m in req.materials]
    return _engine.analyse_material_flows(
        entity_id=req.entity_id,
        materials=materials_dicts,
    )


@router.post("/overall-circularity")
def overall_circularity(req: OverallCircularityRequest) -> dict:
    """Aggregated circularity score across ESRS E5, MCI, CTI, and LCA — with investment gap."""
    return _engine.compute_overall_circularity(
        entity_id=req.entity_id,
        esrs_score=req.esrs_score,
        mci_score=req.mci_score,
        cti_score=req.cti_score,
        lca_benefit_pct=req.lca_benefit_pct,
    )


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/crm-list")
def ref_crm_list() -> dict:
    """EU CRM Act 2023 — full list of 34 Critical Raw Materials and 9 Strategic RM."""
    return {
        "total_crm_count": len(EU_CRM_LIST),
        "critical_raw_materials": sorted(EU_CRM_LIST),
        "strategic_raw_materials": sorted(EU_STRATEGIC_RM),
        "eu_2030_targets": EU_CRM_2030_TARGETS,
        "regulation": "EU CRM Act 2023 (Regulation (EU) 2024/1252)",
        "review_cycle": "Every 3 years",
        "strategic_stockpiling": "6-month demand buffer target",
    }


@router.get("/ref/epr-rates")
def ref_epr_rates() -> dict:
    """EU EPR cost rates by country and waste category (EUR/tonne)."""
    rates_formatted = []
    for category, countries in EPR_COSTS.items():
        for country, rate in countries.items():
            rates_formatted.append({
                "country": country,
                "category": category,
                "rate_eur_t": rate,
            })
    return {
        "rates": rates_formatted,
        "categories": ["packaging", "ewaste", "battery"],
        "currency": "EUR",
        "unit": "per tonne",
        "directives": {
            "packaging": "Directive 94/62/EC as amended by 2018/852/EU",
            "ewaste": "WEEE Directive 2012/19/EU",
            "battery": "Batteries Regulation (EU) 2023/1542",
        },
        "note": "Rates are indicative PRO (Producer Responsibility Organisation) fees; vary by material composition and collection system.",
    }
