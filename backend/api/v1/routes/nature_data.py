"""
Nature Data API routes -- WDPA Protected Areas + GFW Tree Cover Loss queries.

Endpoints:
  GET  /nature-data/wdpa                  -- search protected areas
  GET  /nature-data/wdpa/{wdpa_id}        -- get single PA by WDPA ID
  GET  /nature-data/wdpa/countries        -- list countries with PAs
  GET  /nature-data/wdpa/nearby           -- find PAs near coordinates
  GET  /nature-data/gfw                   -- search GFW tree cover loss
  GET  /nature-data/gfw/{iso3}            -- country time-series
  GET  /nature-data/gfw/countries         -- list countries with data
  GET  /nature-data/overlaps              -- spatial overlaps for an asset
  GET  /nature-data/stats                 -- summary counts
"""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct, text
from sqlalchemy.orm import Session

from db.base import get_db
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/nature-data", tags=["nature-data"])


# ── WDPA Protected Areas ─────────────────────────────────────────────────────

@router.get("/wdpa")
def search_wdpa(
    country: Optional[str] = Query(None, description="Country ISO3 filter"),
    iucn_cat: Optional[str] = Query(None, description="IUCN category filter"),
    status: Optional[str] = Query(None, description="Designation status filter"),
    search: Optional[str] = Query(None, description="Name search"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search WDPA protected areas with filters."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()
    if iucn_cat:
        conditions.append("iucn_cat = :iucn_cat")
        params["iucn_cat"] = iucn_cat
    if status:
        conditions.append("status = :status")
        params["status"] = status
    if search:
        conditions.append("name ILIKE :search")
        params["search"] = f"%{search}%"

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, wdpa_id, name, country_iso3, country_name, desig, desig_type,
               iucn_cat, marine, rep_area_km2, gis_area_km2, status, status_yr,
               latitude, longitude
        FROM dh_wdpa_protected_areas
        {where}
        ORDER BY rep_area_km2 DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"""
        SELECT COUNT(*) FROM dh_wdpa_protected_areas {where}
    """), params).scalar()

    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/wdpa/countries")
def wdpa_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List countries with WDPA protected areas."""
    rows = db.execute(text("""
        SELECT country_iso3 AS iso3, country_name AS name, COUNT(*) AS count,
               SUM(rep_area_km2) AS total_area_km2
        FROM dh_wdpa_protected_areas
        WHERE country_iso3 IS NOT NULL
        GROUP BY country_iso3, country_name
        ORDER BY count DESC
    """)).mappings().all()
    return {"countries": [dict(r) for r in rows]}


@router.get("/wdpa/nearby")
def wdpa_nearby(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(50, ge=1, le=500, description="Search radius km"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """
    Find WDPA protected areas near a coordinate (haversine distance).
    No PostGIS required -- uses SQL haversine formula.
    """
    rows = db.execute(text("""
        SELECT * FROM (
            SELECT id, wdpa_id, name, country_iso3, iucn_cat, rep_area_km2, status,
                   latitude, longitude,
                   (6371 * acos(
                       LEAST(1.0, cos(radians(:lat)) * cos(radians(latitude)) *
                       cos(radians(longitude) - radians(:lng)) +
                       sin(radians(:lat)) * sin(radians(latitude)))
                   )) AS distance_km
            FROM dh_wdpa_protected_areas
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ) sub
        WHERE sub.distance_km <= :radius
        ORDER BY sub.distance_km
        LIMIT :limit
    """), {"lat": lat, "lng": lng, "radius": radius_km, "limit": limit}).mappings().all()

    return {"results": [dict(r) for r in rows], "center": {"lat": lat, "lng": lng}, "radius_km": radius_km}


@router.get("/wdpa/{wdpa_id}")
def get_wdpa_by_id(
    wdpa_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get a single protected area by WDPA ID."""
    row = db.execute(text("""
        SELECT * FROM dh_wdpa_protected_areas WHERE wdpa_id = :wdpa_id
    """), {"wdpa_id": wdpa_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"WDPA ID {wdpa_id} not found")
    return dict(row)


# ── GFW Tree Cover Loss ──────────────────────────────────────────────────────

@router.get("/gfw")
def search_gfw(
    country: Optional[str] = Query(None, description="Country ISO3 filter"),
    year_start: Optional[int] = Query(None, description="Start year"),
    year_end: Optional[int] = Query(None, description="End year"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search GFW tree cover loss data."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()
    if year_start:
        conditions.append("year >= :year_start")
        params["year_start"] = year_start
    if year_end:
        conditions.append("year <= :year_end")
        params["year_end"] = year_end

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, country_iso3, country_name, year,
               tree_cover_loss_ha, tree_cover_extent_ha,
               primary_forest_loss_ha, co2_emissions_mt,
               driver_category, threshold_pct
        FROM dh_gfw_tree_cover_loss
        {where}
        ORDER BY country_iso3, year
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"""
        SELECT COUNT(*) FROM dh_gfw_tree_cover_loss {where}
    """), params).scalar()

    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/gfw/countries")
def gfw_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List countries with GFW data."""
    rows = db.execute(text("""
        SELECT country_iso3 AS iso3, country_name AS name,
               COUNT(DISTINCT year) AS years,
               SUM(tree_cover_loss_ha) AS total_loss_ha
        FROM dh_gfw_tree_cover_loss
        WHERE country_iso3 IS NOT NULL
        GROUP BY country_iso3, country_name
        ORDER BY total_loss_ha DESC NULLS LAST
    """)).mappings().all()
    return {"countries": [dict(r) for r in rows]}


@router.get("/gfw/{iso3}")
def gfw_country_timeseries(
    iso3: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get tree cover loss time-series for a country."""
    rows = db.execute(text("""
        SELECT year, tree_cover_loss_ha, tree_cover_extent_ha,
               primary_forest_loss_ha, co2_emissions_mt, driver_category
        FROM dh_gfw_tree_cover_loss
        WHERE country_iso3 = :iso3
        ORDER BY year
    """), {"iso3": iso3.upper()}).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No GFW data for {iso3}")
    return {"country": iso3.upper(), "records": [dict(r) for r in rows]}


# ── Spatial Overlaps ─────────────────────────────────────────────────────────

@router.get("/overlaps")
def nature_overlaps(
    asset_id: Optional[str] = Query(None, description="Platform asset UUID"),
    wdpa_id: Optional[int] = Query(None, description="WDPA site ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Query precomputed nature spatial overlaps."""
    conditions = []
    params = {"limit": limit}

    if asset_id:
        conditions.append("asset_id = :asset_id::uuid")
        params["asset_id"] = asset_id
    if wdpa_id:
        conditions.append("wdpa_id = :wdpa_id")
        params["wdpa_id"] = wdpa_id

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, asset_id, protected_area_id, wdpa_id, protected_area_name,
               iucn_cat, overlap_km2, overlap_pct, distance_km,
               gfw_loss_ha, calculation_method
        FROM dh_nature_spatial_overlaps
        {where}
        ORDER BY distance_km ASC NULLS LAST
        LIMIT :limit
    """), params).mappings().all()

    return {"overlaps": [dict(r) for r in rows], "total": len(rows)}


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
def nature_data_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for nature data tables."""
    wdpa_count = db.execute(text("SELECT COUNT(*) FROM dh_wdpa_protected_areas")).scalar() or 0
    wdpa_countries = db.execute(text("SELECT COUNT(DISTINCT country_iso3) FROM dh_wdpa_protected_areas")).scalar() or 0
    gfw_count = db.execute(text("SELECT COUNT(*) FROM dh_gfw_tree_cover_loss")).scalar() or 0
    gfw_countries = db.execute(text("SELECT COUNT(DISTINCT country_iso3) FROM dh_gfw_tree_cover_loss")).scalar() or 0
    overlaps_count = db.execute(text("SELECT COUNT(*) FROM dh_nature_spatial_overlaps")).scalar() or 0

    return {
        "wdpa": {"records": wdpa_count, "countries": wdpa_countries},
        "gfw": {"records": gfw_count, "countries": gfw_countries},
        "overlaps": {"records": overlaps_count},
    }
