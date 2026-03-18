"""
API Routes: Spatial Query Engine (PostGIS P1-8)
================================================
POST /api/v1/spatial/assets/protected-areas  — Assets within N km of protected areas
POST /api/v1/spatial/assets/flood-zones      — Assets inside flood zone polygons
POST /api/v1/spatial/assets/wildfire-risk    — Assets inside wildfire risk zones
POST /api/v1/spatial/eudr/plot-overlap       — EUDR plots overlapping protected areas
POST /api/v1/spatial/point/hazards           — All hazard layers for a single point
GET  /api/v1/spatial/ref/status              — PostGIS version and extension status
GET  /api/v1/spatial/ref/hazard-tables       — Spatial reference table row counts

Powered by PostGIS 3.3.7 (EPSG:4326 / WGS 84).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

router = APIRouter(prefix="/api/v1/spatial", tags=["Spatial (PostGIS)"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class AssetProtectedAreasRequest(BaseModel):
    asset_ids: Optional[List[str]] = Field(
        None, description="Filter to specific asset IDs (UUID strings). Null = all assets."
    )
    radius_km: float = Field(10.0, ge=0.1, le=100.0, description="Search radius in km")
    iucn_categories: Optional[List[str]] = Field(
        None, description="Filter by IUCN category e.g. ['Ia','Ib','II']"
    )
    limit: int = Field(500, ge=1, le=2000)


class PointHazardRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(10.0, ge=0.1, le=50.0)


class AssetFloodRequest(BaseModel):
    asset_ids: Optional[List[str]] = None
    return_period_years: Optional[List[int]] = Field(
        None, description="Filter by return period e.g. [100, 500]"
    )
    scenario: Optional[str] = Field(
        None, description="baseline | rcp45_2050 | rcp85_2050 | rcp85_2100"
    )
    limit: int = Field(500, ge=1, le=2000)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assets/protected-areas",
    summary="Assets within N km of WDPA protected areas",
    description=(
        "Spatial query: find all portfolio assets within the specified radius of any "
        "WDPA protected area. Returns asset–PA pairs with distance in km. "
        "Relevant for ESRS E4-3 (biodiversity-sensitive areas) and EUDR Article 10. "
        "Requires ref_protected_areas table to be populated (currently empty — seed with WDPA data)."
    ),
)
def assets_in_protected_areas(
    req: AssetProtectedAreasRequest,
    db: Session = Depends(get_db),
):
    radius_m = req.radius_km * 1000

    where_clauses = ["va.location IS NOT NULL"]
    params: Dict[str, Any] = {"radius_m": radius_m, "limit": req.limit}

    if req.asset_ids:
        where_clauses.append("va.id = ANY(:asset_ids)")
        params["asset_ids"] = req.asset_ids
    if req.iucn_categories:
        where_clauses.append("pa.iucn_category = ANY(:iucn_cats)")
        params["iucn_cats"] = req.iucn_categories

    where_sql = " AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            va.id::TEXT             AS asset_id,
            va.asset_name,
            va.city,
            va.country_iso,
            pa.wdpa_id,
            pa.name                 AS protected_area_name,
            pa.iucn_category,
            pa.country_iso3,
            (ST_Distance(va.location, pa.boundary::GEOGRAPHY) / 1000.0)::NUMERIC(10,2)
                                    AS distance_km,
            pa.area_km2
        FROM valuation_assets va
        CROSS JOIN ref_protected_areas pa
        WHERE {where_sql}
          AND ST_DWithin(va.location, pa.boundary::GEOGRAPHY, :radius_m)
        ORDER BY distance_km
        LIMIT :limit
    """)

    try:
        rows = db.execute(sql, params).mappings().all()
        return {
            "count": len(rows),
            "radius_km": req.radius_km,
            "results": [dict(r) for r in rows],
            "note": "Returns empty if ref_protected_areas has no rows (requires WDPA data load)",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Spatial query error: {exc}") from exc


@router.post(
    "/assets/flood-zones",
    summary="Assets inside flood zone polygons",
    description=(
        "Spatial query: find portfolio assets located inside flood zone polygons "
        "(EU FHRM / Copernicus style). Returns asset–zone pairs by return period and scenario. "
        "Requires ref_flood_zones table to be populated."
    ),
)
def assets_in_flood_zones(
    req: AssetFloodRequest,
    db: Session = Depends(get_db),
):
    where_clauses = ["va.location IS NOT NULL"]
    params: Dict[str, Any] = {"limit": req.limit}

    if req.asset_ids:
        where_clauses.append("va.id = ANY(:asset_ids)")
        params["asset_ids"] = req.asset_ids
    if req.return_period_years:
        where_clauses.append("fz.return_period_y = ANY(:rp_years)")
        params["rp_years"] = req.return_period_years
    if req.scenario:
        where_clauses.append("fz.scenario = :scenario")
        params["scenario"] = req.scenario

    where_sql = " AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            va.id::TEXT             AS asset_id,
            va.asset_name,
            va.city,
            va.country_iso,
            fz.zone_id,
            fz.return_period_y,
            fz.scenario             AS flood_scenario,
            fz.max_depth_m
        FROM valuation_assets va
        CROSS JOIN ref_flood_zones fz
        WHERE {where_sql}
          AND ST_Within(va.location::GEOMETRY, fz.zone_boundary)
        ORDER BY fz.return_period_y, va.asset_name
        LIMIT :limit
    """)

    try:
        rows = db.execute(sql, params).mappings().all()
        return {
            "count": len(rows),
            "results": [dict(r) for r in rows],
            "note": "Returns empty if ref_flood_zones has no rows (requires EU FHRM data load)",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Spatial query error: {exc}") from exc


@router.post(
    "/assets/wildfire-risk",
    summary="Assets inside wildfire risk zones",
)
def assets_wildfire_risk(
    db: Session = Depends(get_db),
    asset_ids: Optional[List[str]] = None,
    risk_levels: Optional[List[str]] = None,
    limit: int = 500,
):
    where_clauses = ["va.location IS NOT NULL"]
    params: Dict[str, Any] = {"limit": limit}

    if asset_ids:
        where_clauses.append("va.id = ANY(:asset_ids)")
        params["asset_ids"] = asset_ids
    if risk_levels:
        where_clauses.append("wz.risk_level = ANY(:risk_levels)")
        params["risk_levels"] = risk_levels

    where_sql = " AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            va.id::TEXT     AS asset_id,
            va.asset_name,
            va.city,
            va.country_iso,
            wz.zone_id,
            wz.risk_level,
            wz.fwi_mean
        FROM valuation_assets va
        CROSS JOIN ref_wildfire_zones wz
        WHERE {where_sql}
          AND ST_Within(va.location::GEOMETRY, wz.zone_boundary)
        ORDER BY wz.risk_level DESC, va.asset_name
        LIMIT :limit
    """)

    try:
        rows = db.execute(sql, params).mappings().all()
        return {
            "count": len(rows),
            "results": [dict(r) for r in rows],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Spatial query error: {exc}") from exc


@router.post(
    "/point/hazards",
    summary="All physical hazard layers intersecting a single lat/lng point",
    description=(
        "Given a latitude/longitude, returns all hazard exposures across all "
        "spatial reference layers: protected areas (within radius), flood zones, "
        "wildfire zones, sea level rise zones. "
        "Useful for single-asset physical risk screening."
    ),
)
def point_hazards(
    req: PointHazardRequest,
    db: Session = Depends(get_db),
):
    radius_m = req.radius_km * 1000
    params = {
        "lat": req.latitude,
        "lng": req.longitude,
        "radius_m": radius_m,
    }

    try:
        # Protected areas (proximity)
        pa_rows = db.execute(text("""
            SELECT pa.wdpa_id, pa.name, pa.iucn_category,
                   (ST_Distance(
                       make_point_geography(:lat, :lng),
                       pa.boundary::GEOGRAPHY
                   ) / 1000.0)::NUMERIC(10,2) AS distance_km
            FROM ref_protected_areas pa
            WHERE ST_DWithin(
                make_point_geography(:lat, :lng),
                pa.boundary::GEOGRAPHY,
                :radius_m
            )
            ORDER BY distance_km LIMIT 10
        """), params).mappings().all()

        # Flood zones (containment)
        fz_rows = db.execute(text("""
            SELECT fz.zone_id, fz.return_period_y, fz.scenario, fz.max_depth_m
            FROM ref_flood_zones fz
            WHERE ST_Within(
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                fz.zone_boundary
            ) LIMIT 10
        """), params).mappings().all()

        # Wildfire zones
        wz_rows = db.execute(text("""
            SELECT wz.zone_id, wz.risk_level, wz.scenario, wz.fwi_mean
            FROM ref_wildfire_zones wz
            WHERE ST_Within(
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                wz.zone_boundary
            ) LIMIT 10
        """), params).mappings().all()

        # Sea level rise zones
        slr_rows = db.execute(text("""
            SELECT sz.zone_id, sz.slr_scenario, sz.horizon_year, sz.slr_m
            FROM ref_sea_level_zones sz
            WHERE ST_Within(
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                sz.zone_boundary
            ) LIMIT 10
        """), params).mappings().all()

        total_hazards = len(pa_rows) + len(fz_rows) + len(wz_rows) + len(slr_rows)

        return {
            "latitude": req.latitude,
            "longitude": req.longitude,
            "radius_km": req.radius_km,
            "total_hazard_layers_hit": total_hazards,
            "hazards": {
                "protected_areas": [dict(r) for r in pa_rows],
                "flood_zones": [dict(r) for r in fz_rows],
                "wildfire_zones": [dict(r) for r in wz_rows],
                "sea_level_rise": [dict(r) for r in slr_rows],
            },
            "note": "All layers return empty until reference spatial data is loaded",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Spatial query error: {exc}") from exc


@router.post(
    "/eudr/plot-overlap",
    summary="EUDR commodity plots overlapping WDPA protected areas",
    description=(
        "Finds EUDR commodity lot geolocation proofs that spatially intersect "
        "any protected area in ref_protected_areas. Returns overlap area in hectares. "
        "Implements EUDR Article 10 deforestation-risk assessment for protected area proximity."
    ),
)
def eudr_plot_overlap(
    db: Session = Depends(get_db),
    limit: int = 200,
):
    try:
        rows = db.execute(text("""
            SELECT
                eg.id           AS proof_id,
                pa.name         AS protected_area_name,
                pa.iucn_category,
                pa.wdpa_id,
                (ST_Area(
                    ST_Intersection(eg.plot_geometry, pa.boundary)::GEOGRAPHY
                ) / 10000.0)::NUMERIC(14,4) AS overlap_ha
            FROM eudr_geolocation_proofs eg
            CROSS JOIN ref_protected_areas pa
            WHERE eg.plot_geometry IS NOT NULL
              AND ST_Intersects(eg.plot_geometry, pa.boundary)
            ORDER BY overlap_ha DESC
            LIMIT :limit
        """), {"limit": limit}).mappings().all()
        return {
            "count": len(rows),
            "results": [dict(r) for r in rows],
            "note": "Returns empty until eudr_geolocation_proofs and ref_protected_areas are populated",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Spatial query error: {exc}") from exc


@router.get(
    "/ref/status",
    summary="PostGIS extension versions and spatial table row counts",
)
def ref_postgis_status(db: Session = Depends(get_db)):
    try:
        ext_rows = db.execute(text(
            "SELECT extension, version, schema FROM vw_postgis_status"
        )).mappings().all()

        counts = db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM ref_protected_areas)  AS protected_areas,
                (SELECT COUNT(*) FROM ref_flood_zones)      AS flood_zones,
                (SELECT COUNT(*) FROM ref_wildfire_zones)   AS wildfire_zones,
                (SELECT COUNT(*) FROM ref_sea_level_zones)  AS sea_level_zones
        """)).mappings().one()

        return {
            "postgis_active": True,
            "extensions": [dict(r) for r in ext_rows],
            "reference_table_counts": dict(counts),
            "data_load_required": (
                dict(counts)["protected_areas"] == 0
                or dict(counts)["flood_zones"] == 0
            ),
            "note": (
                "Reference spatial data (WDPA, EU FHRM, Copernicus) must be loaded "
                "to activate spatial queries. Geometry columns and indexes are ready."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PostGIS status error: {exc}") from exc


@router.get(
    "/ref/spatial-indexes",
    summary="List all spatial (GiST) indexes on the platform",
)
def ref_spatial_indexes(db: Session = Depends(get_db)):
    try:
        rows = db.execute(text("""
            SELECT
                n.nspname           AS schema,
                t.relname           AS table_name,
                i.relname           AS index_name,
                a.attname           AS column_name,
                am.amname           AS index_type
            FROM pg_index ix
            JOIN pg_class t  ON t.oid = ix.indrelid
            JOIN pg_class i  ON i.oid = ix.indexrelid
            JOIN pg_am am    ON am.oid = i.relam
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE am.amname = 'gist'
              AND n.nspname = 'public'
            ORDER BY t.relname, i.relname
        """)).mappings().all()
        return {
            "gist_index_count": len(rows),
            "indexes": [dict(r) for r in rows],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
