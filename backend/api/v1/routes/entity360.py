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


# ---------------------------------------------------------------------------
# DB-Powered Entity 360 — auto-gather data from all modules via LEI
# ---------------------------------------------------------------------------

@router.get(
    "/by-lei/{lei}",
    summary="Auto-generate Entity 360 profile from DB data by LEI",
)
def entity360_by_lei(lei: str):
    """
    Automatically builds an Entity 360 profile by:
    1. Using EntityResolutionService to gather all cross-module data for the LEI
    2. Transforming that data into module_data format
    3. Passing it to Entity360Engine.build_profile()

    No manual module_data input required — everything is read from the database.
    """
    if len(lei) != 20:
        from fastapi import HTTPException
        raise HTTPException(400, "LEI must be exactly 20 characters")

    from services.entity_resolution_service import EntityResolutionService
    from db.base import engine as db_engine

    svc = EntityResolutionService(db_engine)
    graph = svc.build_entity_graph(lei)

    # ── Transform cross-module data into module_data dict ──────────────────
    module_data: dict[str, dict[str, float]] = {}

    # Determine entity metadata from the best available source
    entity_name = "Unknown"
    entity_type = "corporate"
    sector = "financials"

    if graph.company_profile:
        cp = graph.company_profile
        entity_name = cp.get("legal_name", entity_name)
        sector = (cp.get("gics_sector") or "").lower().replace(" ", "_") or sector
        if cp.get("institution_type"):
            entity_type = "fi"

    if graph.fi_entity:
        fi = graph.fi_entity
        entity_name = fi.get("legal_name", entity_name)
        entity_type = "fi"
        # Extract credit/risk data if available
        module_data["ecl_calculator"] = {}

    if graph.energy_entity:
        en = graph.energy_entity
        entity_name = en.get("legal_name", entity_name)
        sector = "energy"

    if graph.csrd_entity:
        csrd = graph.csrd_entity
        entity_name = csrd.get("legal_name", entity_name)

    # PCAF from investees
    if graph.pcaf_investees:
        inv = graph.pcaf_investees[0]
        pcaf_vals = {}
        if inv.get("outstanding_amount"):
            pcaf_vals["outstanding_amount"] = float(inv["outstanding_amount"])
        if inv.get("asset_class"):
            pcaf_vals["asset_class_code"] = 1.0  # signal that data exists
        if pcaf_vals:
            module_data["pcaf_calculator"] = pcaf_vals

    # ECL from assessments
    if graph.ecl_assessments:
        ecl = graph.ecl_assessments[0]
        ecl_vals = {}
        if ecl.get("total_ecl") is not None:
            ecl_vals["ecl_eur"] = float(ecl["total_ecl"])
        if ecl_vals:
            module_data["ecl_calculator"] = ecl_vals

    # Build the Entity 360 profile
    result = _engine.build_profile(
        entity_name=entity_name,
        entity_id=lei,
        entity_type=entity_type,
        sector=sector,
        reporting_year=2025,
        module_data=module_data,
    )

    response = _ser_entity360(result)
    response["cross_module_graph"] = {
        "module_count": graph.module_count,
        "has_company_profile": graph.company_profile is not None,
        "has_fi_entity": graph.fi_entity is not None,
        "has_energy_entity": graph.energy_entity is not None,
        "has_sc_entity": graph.sc_entity is not None,
        "has_regulatory_entity": graph.regulatory_entity is not None,
        "has_csrd_entity": graph.csrd_entity is not None,
        "portfolio_asset_count": len(graph.portfolio_assets),
        "pcaf_investee_count": len(graph.pcaf_investees),
        "ecl_assessment_count": len(graph.ecl_assessments),
    }
    return response
