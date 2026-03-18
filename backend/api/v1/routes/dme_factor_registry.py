"""
DME Factor Registry — API Routes.

Prefix: /api/v1/dme-factor-registry

Unified interface for the 627-factor DME taxonomy + 31 overlay registries.
"""
from fastapi import APIRouter, Query
from services.dme_factor_registry import (
    FactorRegistryEngine, FactorSearchRequest, FactorCompareRequest,
)

router = APIRouter(prefix="/api/v1/dme-factor-registry", tags=["DME Factor Registry"])


@router.get("/factors")
def list_factors(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
):
    """List all factors (paginated). Returns DME + overlay factors."""
    return FactorRegistryEngine.get_all_factors(limit=limit, offset=offset)


@router.get("/factors/{factor_id}")
def get_factor(factor_id: str):
    """Get a single factor by ID (e.g. ENV-001-I or OVR-ESG-001)."""
    result = FactorRegistryEngine.get_factor(factor_id)
    if not result:
        return {"error": f"Factor {factor_id} not found"}
    return result


@router.post("/search")
def search_factors(req: FactorSearchRequest):
    """Search/filter factors by pillar, topic, source, materiality dimension, etc."""
    return FactorRegistryEngine.search_factors(req)


@router.get("/stats")
def get_stats():
    """Registry statistics: counts by source, pillar, materiality, velocity method."""
    return FactorRegistryEngine.get_stats()


@router.get("/overlay-mapping")
def get_overlay_mapping():
    """Return the 31 overlay registry → factor mappings."""
    return FactorRegistryEngine.get_overlay_mapping()


@router.post("/compare")
def compare_factor(req: FactorCompareRequest):
    """Compare a DME factor with closest overlay registry counterparts."""
    return FactorRegistryEngine.compare_factor(req.dme_factor_id)


@router.get("/ref/pillars")
def get_pillars():
    """Reference: pillars, materiality dimensions, velocity methods, frequencies, decay categories."""
    return FactorRegistryEngine.get_pillars()


@router.get("/ref/dme-topics")
def get_dme_topics():
    """Reference: DME base topics per pillar (209 topics)."""
    return FactorRegistryEngine.get_dme_topics()
