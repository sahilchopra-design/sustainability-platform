"""
Entity 360 & Counterparty Master API
========================================
Endpoints for unified cross-module entity profiling, counterparty master
deduplication, and reference data for entity types / sectors / modules.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.entity360_engine import (
    Entity360Engine,
    MODULE_REGISTRY,
    ENTITY_TYPES,
    SECTOR_MAP,
)

router = APIRouter(prefix="/api/v1/entity360", tags=["Entity 360"])

_engine = Entity360Engine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ModuleDataEntry(BaseModel):
    module_id: str
    values: dict[str, float] = {}


class Entity360Request(BaseModel):
    entity_name: str
    entity_id: str
    entity_type: str = "corporate"
    sector: str = "financials"
    reporting_year: int = 2024
    module_data: list[ModuleDataEntry] = []


class CounterpartyInput(BaseModel):
    entity_id: str
    entity_name: str
    lei: str = ""
    entity_type: str = "corporate"
    sector: str = ""
    country: str = ""
    parent_entity_id: Optional[str] = None
    group_name: Optional[str] = None
    exposure_eur: float = 0
    modules_linked: list[str] = []
    last_assessment_date: str = "2024-01-01"


class CounterpartyMasterRequest(BaseModel):
    counterparties: list[CounterpartyInput]


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_module_score(ms) -> dict:
    return {
        "module_id": ms.module_id,
        "module_label": ms.module_label,
        "category": ms.category,
        "data_available": ms.data_available,
        "values": ms.values,
        "data_quality": ms.data_quality,
        "last_updated": ms.last_updated,
    }


def _ser_risk_profile(rp) -> dict:
    return {
        "credit_risk_score": rp.credit_risk_score,
        "climate_risk_score": rp.climate_risk_score,
        "nature_risk_score": rp.nature_risk_score,
        "regulatory_risk_score": rp.regulatory_risk_score,
        "composite_risk_score": rp.composite_risk_score,
        "risk_band": rp.risk_band,
    }


def _ser_esg_profile(ep) -> dict:
    return {
        "total_ghg_tco2e": ep.total_ghg_tco2e,
        "ghg_intensity": ep.ghg_intensity,
        "renewable_share_pct": ep.renewable_share_pct,
        "taxonomy_aligned_pct": ep.taxonomy_aligned_pct,
        "pai_flags": ep.pai_flags,
        "esg_rating": ep.esg_rating,
    }


def _ser_entity360(r) -> dict:
    return {
        "entity_name": r.entity_name,
        "entity_id": r.entity_id,
        "entity_type": r.entity_type,
        "sector": r.sector,
        "sector_label": r.sector_label,
        "reporting_year": r.reporting_year,
        "modules_available": r.modules_available,
        "modules_total": r.modules_total,
        "data_completeness_pct": r.data_completeness_pct,
        "module_scores": [_ser_module_score(ms) for ms in r.module_scores],
        "risk_profile": _ser_risk_profile(r.risk_profile),
        "esg_profile": _ser_esg_profile(r.esg_profile),
        "regulatory_status": r.regulatory_status,
        "data_gaps": r.data_gaps,
        "recommendations": r.recommendations,
    }


def _ser_counterparty(cp) -> dict:
    return {
        "entity_id": cp.entity_id,
        "entity_name": cp.entity_name,
        "lei": cp.lei,
        "entity_type": cp.entity_type,
        "sector": cp.sector,
        "country": cp.country,
        "parent_entity_id": cp.parent_entity_id,
        "group_name": cp.group_name,
        "exposure_eur": cp.exposure_eur,
        "modules_linked": cp.modules_linked,
        "last_assessment_date": cp.last_assessment_date,
        "data_quality_score": cp.data_quality_score,
    }


def _ser_master(r) -> dict:
    return {
        "total_counterparties": r.total_counterparties,
        "counterparties": [_ser_counterparty(cp) for cp in r.counterparties],
        "duplicate_groups": r.duplicate_groups,
        "sector_distribution": r.sector_distribution,
        "entity_type_distribution": r.entity_type_distribution,
        "data_quality_avg": r.data_quality_avg,
        "low_quality_count": r.low_quality_count,
    }


# ---------------------------------------------------------------------------
# Endpoints — Entity 360
# ---------------------------------------------------------------------------

@router.post("/profile", summary="Build Entity 360 profile from module outputs")
def entity360_profile(req: Entity360Request):
    module_data = {m.module_id: m.values for m in req.module_data}
    res = _engine.build_profile(
        entity_name=req.entity_name,
        entity_id=req.entity_id,
        entity_type=req.entity_type,
        sector=req.sector,
        reporting_year=req.reporting_year,
        module_data=module_data,
    )
    return _ser_entity360(res)


# ---------------------------------------------------------------------------
# Endpoints — Counterparty Master
# ---------------------------------------------------------------------------

@router.post("/counterparty-master", summary="Build counterparty master with dedup & quality scoring")
def counterparty_master(req: CounterpartyMasterRequest):
    cp_list = [cp.model_dump() for cp in req.counterparties]
    res = _engine.build_counterparty_master(cp_list)
    return _ser_master(res)


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/module-registry", summary="Platform module registry")
def ref_module_registry():
    return _engine.get_module_registry()


@router.get("/ref/entity-types", summary="Supported entity types")
def ref_entity_types():
    return _engine.get_entity_types()


@router.get("/ref/sectors", summary="Sector classification map")
def ref_sectors():
    return _engine.get_sectors()
