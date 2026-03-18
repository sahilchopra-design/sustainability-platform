"""
Reference Data Catalog API
=============================
Endpoints for browsing the centralized reference data catalog,
checking data freshness, and identifying gaps in reference data coverage.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Optional

from services.reference_data_catalog import ReferenceDataCatalogEngine

router = APIRouter(prefix="/api/v1/reference-catalog", tags=["Reference Data Catalog"])

_engine = ReferenceDataCatalogEngine()


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_entry(e) -> dict:
    return {
        "data_id": e.data_id,
        "label": e.label,
        "domain": e.domain,
        "domain_label": e.domain_label,
        "source": e.source,
        "source_url": e.source_url,
        "update_frequency": e.update_frequency,
        "last_known_update": e.last_known_update,
        "record_count": e.record_count,
        "status": e.status,
        "used_by": e.used_by,
        "notes": e.notes,
    }


def _ser_catalog(c) -> dict:
    return {
        "total_datasets": c.total_datasets,
        "embedded_count": c.embedded_count,
        "seed_data_count": c.seed_data_count,
        "missing_count": c.missing_count,
        "stale_count": c.stale_count,
        "coverage_pct": c.coverage_pct,
        "entries": [_ser_entry(e) for e in c.entries],
        "domains": c.domains,
        "missing_critical": [_ser_entry(e) for e in c.missing_critical],
        "recommendations": c.recommendations,
    }


def _ser_gap_report(g) -> dict:
    return {
        "total_missing": g.total_missing,
        "total_stale": g.total_stale,
        "gaps": [_ser_entry(e) for e in g.gaps],
        "remediation_priority": g.remediation_priority,
        "estimated_effort": g.estimated_effort,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", summary="Full reference data catalog")
def catalog(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    include_missing: bool = Query(True, description="Include missing datasets"),
):
    res = _engine.get_catalog(domain=domain, include_missing=include_missing)
    return _ser_catalog(res)


@router.get("/domains", summary="Reference data domains")
def domains():
    return _engine.get_domains()


@router.get("/gaps", summary="Missing and stale reference data")
def gaps():
    res = _engine.find_gaps()
    return _ser_gap_report(res)


@router.get("/module/{module_id}", summary="Reference data for a specific module")
def module_reference_data(module_id: str):
    entries = _engine.get_module_reference_data(module_id)
    return {
        "module_id": module_id,
        "reference_data": [_ser_entry(e) for e in entries],
        "total": len(entries),
    }


@router.get("/dataset/{data_id}", summary="Single reference dataset detail")
def dataset_detail(data_id: str):
    entry = _engine.get_dataset(data_id)
    if entry is None:
        return {"error": f"Dataset '{data_id}' not found"}
    return _ser_entry(entry)
