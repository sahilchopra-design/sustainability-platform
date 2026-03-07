"""
Energy Data API routes -- GEM Global Coal Plant Tracker queries.

Endpoints:
  GET  /energy-data/coal-plants              -- search coal plants
  GET  /energy-data/coal-plants/{gem_id}     -- single plant by GEM ID
  GET  /energy-data/coal-plants/countries    -- countries with coal plants
  GET  /energy-data/coal-plants/owners       -- top owners/parent companies
  GET  /energy-data/coal-plants/nearby       -- plants near coordinates
  GET  /energy-data/coal-plants/pipeline     -- announced + construction plants
  GET  /energy-data/coal-units/{plant_id}    -- units for a plant
  GET  /energy-data/stats                    -- summary counts
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/energy-data", tags=["energy-data"])


# ── Coal Plants ──────────────────────────────────────────────────────────────

@router.get("/coal-plants")
def search_coal_plants(
    country: Optional[str] = Query(None, description="Country ISO3 filter"),
    status: Optional[str] = Query(None, description="Status filter (Operating, Announced, etc.)"),
    parent_company: Optional[str] = Query(None, description="Parent company filter"),
    coal_type: Optional[str] = Query(None, description="Coal type filter"),
    min_capacity_mw: Optional[float] = Query(None, description="Min capacity MW"),
    search: Optional[str] = Query(None, description="Plant name search"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search GEM coal plants with filters."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()
    if status:
        conditions.append("status = :status")
        params["status"] = status
    if parent_company:
        conditions.append("parent_company ILIKE :parent")
        params["parent"] = f"%{parent_company}%"
    if coal_type:
        conditions.append("coal_type ILIKE :coal_type")
        params["coal_type"] = f"%{coal_type}%"
    if min_capacity_mw is not None:
        conditions.append("capacity_mw >= :min_cap")
        params["min_cap"] = min_capacity_mw
    if search:
        conditions.append("plant_name ILIKE :search")
        params["search"] = f"%{search}%"

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, gem_id, plant_name, country, country_iso3, subnational,
               owner, parent_company, latitude, longitude,
               status, capacity_mw, num_units, year_opened, year_retired,
               planned_retire_year, coal_type, combustion_technology,
               annual_co2_mt
        FROM dh_gem_coal_plants
        {where}
        ORDER BY capacity_mw DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"""
        SELECT COUNT(*) FROM dh_gem_coal_plants {where}
    """), params).scalar()

    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/coal-plants/countries")
def coal_plant_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List countries with coal plants and aggregate capacity."""
    rows = db.execute(text("""
        SELECT country_iso3 AS iso3, country AS name,
               COUNT(*) AS plants,
               SUM(capacity_mw) AS total_capacity_mw,
               SUM(annual_co2_mt) AS total_co2_mt,
               COUNT(*) FILTER (WHERE status = 'Operating') AS operating,
               COUNT(*) FILTER (WHERE status IN ('Announced', 'Pre-permit', 'Permitted')) AS pipeline
        FROM dh_gem_coal_plants
        WHERE country_iso3 IS NOT NULL
        GROUP BY country_iso3, country
        ORDER BY total_capacity_mw DESC NULLS LAST
    """)).mappings().all()
    return {"countries": [dict(r) for r in rows]}


@router.get("/coal-plants/owners")
def coal_plant_owners(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Top parent companies by coal capacity."""
    rows = db.execute(text("""
        SELECT parent_company, COUNT(*) AS plants,
               SUM(capacity_mw) AS total_capacity_mw,
               SUM(annual_co2_mt) AS total_co2_mt,
               COUNT(*) FILTER (WHERE status = 'Operating') AS operating,
               COUNT(*) FILTER (WHERE planned_retire_year IS NOT NULL) AS with_retire_date
        FROM dh_gem_coal_plants
        WHERE parent_company IS NOT NULL
        GROUP BY parent_company
        ORDER BY total_capacity_mw DESC NULLS LAST
        LIMIT :limit
    """), {"limit": limit}).mappings().all()
    return {"owners": [dict(r) for r in rows]}


@router.get("/coal-plants/nearby")
def coal_plants_nearby(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(100, ge=1, le=1000, description="Search radius km"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Find coal plants near a coordinate (haversine distance)."""
    rows = db.execute(text("""
        SELECT * FROM (
            SELECT id, gem_id, plant_name, country_iso3, status, capacity_mw,
                   annual_co2_mt, latitude, longitude,
                   (6371 * acos(
                       LEAST(1.0, cos(radians(:lat)) * cos(radians(latitude)) *
                       cos(radians(longitude) - radians(:lng)) +
                       sin(radians(:lat)) * sin(radians(latitude)))
                   )) AS distance_km
            FROM dh_gem_coal_plants
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ) sub
        WHERE sub.distance_km <= :radius
        ORDER BY sub.distance_km
        LIMIT :limit
    """), {"lat": lat, "lng": lng, "radius": radius_km, "limit": limit}).mappings().all()

    return {"results": [dict(r) for r in rows], "center": {"lat": lat, "lng": lng}, "radius_km": radius_km}


@router.get("/coal-plants/pipeline")
def coal_plant_pipeline(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get announced + under-construction coal plants (stranded asset pipeline)."""
    rows = db.execute(text("""
        SELECT id, gem_id, plant_name, country, country_iso3, status,
               capacity_mw, coal_type, combustion_technology, owner, parent_company,
               latitude, longitude
        FROM dh_gem_coal_plants
        WHERE status IN ('Announced', 'Pre-permit', 'Permitted', 'Construction')
        ORDER BY capacity_mw DESC NULLS LAST
    """)).mappings().all()

    return {"pipeline": [dict(r) for r in rows], "total": len(rows)}


@router.get("/coal-plants/{gem_id}")
def get_coal_plant(
    gem_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get a single coal plant by GEM ID."""
    row = db.execute(text("""
        SELECT * FROM dh_gem_coal_plants WHERE gem_id = :gem_id
    """), {"gem_id": gem_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"GEM ID {gem_id} not found")
    return dict(row)


# ── Coal Plant Units ─────────────────────────────────────────────────────────

@router.get("/coal-units/{plant_id}")
def coal_plant_units(
    plant_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get generating units for a coal plant."""
    rows = db.execute(text("""
        SELECT * FROM dh_gem_coal_plant_units WHERE plant_id = CAST(:plant_id AS uuid)
        ORDER BY capacity_mw DESC NULLS LAST
    """), {"plant_id": plant_id}).mappings().all()

    return {"units": [dict(r) for r in rows], "total": len(rows)}


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
def energy_data_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for energy data tables."""
    plants = db.execute(text("SELECT COUNT(*) FROM dh_gem_coal_plants")).scalar() or 0
    countries = db.execute(text("SELECT COUNT(DISTINCT country_iso3) FROM dh_gem_coal_plants")).scalar() or 0
    total_mw = db.execute(text("SELECT COALESCE(SUM(capacity_mw), 0) FROM dh_gem_coal_plants")).scalar() or 0
    operating = db.execute(text("SELECT COUNT(*) FROM dh_gem_coal_plants WHERE status = 'Operating'")).scalar() or 0
    pipeline = db.execute(text("SELECT COUNT(*) FROM dh_gem_coal_plants WHERE status IN ('Announced','Pre-permit','Permitted','Construction')")).scalar() or 0
    units = db.execute(text("SELECT COUNT(*) FROM dh_gem_coal_plant_units")).scalar() or 0

    return {
        "coal_plants": {
            "total": plants,
            "countries": countries,
            "total_capacity_mw": float(total_mw),
            "operating": operating,
            "pipeline": pipeline,
        },
        "coal_units": {"total": units},
    }
