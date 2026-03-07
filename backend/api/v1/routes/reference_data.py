"""
Reference Data API routes -- IRENA LCOE, CRREM Pathways, Grid Emission Factors.

Endpoints:
  GET  /reference-data/irena-lcoe                 -- search IRENA LCOE benchmarks
  GET  /reference-data/irena-lcoe/technologies    -- list technologies
  GET  /reference-data/irena-lcoe/trend/{tech}    -- technology cost trend
  GET  /reference-data/crrem                      -- search CRREM pathways
  GET  /reference-data/crrem/property-types       -- list property types
  GET  /reference-data/crrem/pathway              -- get pathway for type/scenario/country
  GET  /reference-data/grid-ef                    -- search grid emission factors
  GET  /reference-data/grid-ef/countries          -- list countries with grid EFs
  GET  /reference-data/grid-ef/{iso3}             -- country time-series
  GET  /reference-data/stats                      -- summary counts
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/reference-data", tags=["reference-data"])


# ── IRENA LCOE ────────────────────────────────────────────────────────────────

@router.get("/irena-lcoe")
def search_irena_lcoe(
    technology: Optional[str] = Query(None, description="Technology filter"),
    year_start: Optional[int] = Query(None, description="Start year"),
    year_end: Optional[int] = Query(None, description="End year"),
    country: Optional[str] = Query(None, description="Country ISO3 filter"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search IRENA LCOE benchmarks with filters."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if technology:
        conditions.append("technology ILIKE :tech")
        params["tech"] = f"%{technology}%"
    if year_start:
        conditions.append("year >= :year_start")
        params["year_start"] = year_start
    if year_end:
        conditions.append("year <= :year_end")
        params["year_end"] = year_end
    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, technology, sub_technology, year, country_iso3, region,
               lcoe_usd_mwh, lcoe_min_usd_mwh, lcoe_max_usd_mwh,
               capacity_factor_pct, installed_cost_usd_kw
        FROM dh_irena_lcoe
        {where}
        ORDER BY technology, year
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"SELECT COUNT(*) FROM dh_irena_lcoe {where}"), params).scalar()
    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/irena-lcoe/technologies")
def irena_technologies(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List technologies with LCOE data."""
    rows = db.execute(text("""
        SELECT technology, sub_technology, COUNT(*) AS data_points,
               MIN(year) AS first_year, MAX(year) AS last_year,
               MIN(lcoe_usd_mwh) AS min_lcoe, MAX(lcoe_usd_mwh) AS max_lcoe
        FROM dh_irena_lcoe
        GROUP BY technology, sub_technology
        ORDER BY technology, sub_technology NULLS FIRST
    """)).mappings().all()
    return {"technologies": [dict(r) for r in rows]}


@router.get("/irena-lcoe/trend/{technology}")
def irena_lcoe_trend(
    technology: str,
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get LCOE cost trend for a technology over time."""
    params = {"tech": f"%{technology}%"}
    country_filter = ""
    if country:
        country_filter = "AND country_iso3 = :country"
        params["country"] = country.upper()
    else:
        country_filter = "AND country_iso3 IS NULL"

    rows = db.execute(text(f"""
        SELECT year, technology, sub_technology, lcoe_usd_mwh,
               lcoe_min_usd_mwh, lcoe_max_usd_mwh, capacity_factor_pct,
               installed_cost_usd_kw
        FROM dh_irena_lcoe
        WHERE technology ILIKE :tech {country_filter}
        ORDER BY year
    """), params).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No LCOE data for {technology}")
    return {"technology": technology, "trend": [dict(r) for r in rows]}


# ── CRREM Pathways ────────────────────────────────────────────────────────────

@router.get("/crrem")
def search_crrem(
    property_type: Optional[str] = Query(None, description="Property type filter"),
    scenario: Optional[str] = Query(None, description="Scenario filter (1.5C, 2C)"),
    country: Optional[str] = Query(None, description="Country ISO3"),
    year_start: Optional[int] = Query(None),
    year_end: Optional[int] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search CRREM decarbonization pathways."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if property_type:
        conditions.append("property_type ILIKE :ptype")
        params["ptype"] = f"%{property_type}%"
    if scenario:
        conditions.append("scenario = :scenario")
        params["scenario"] = scenario
    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()
    if year_start:
        conditions.append("year >= :ys")
        params["ys"] = year_start
    if year_end:
        conditions.append("year <= :ye")
        params["ye"] = year_end

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, property_type, country_iso3, scenario, year,
               energy_intensity_kwh_m2, carbon_intensity_kgco2_m2,
               cumulative_reduction_pct, stranding_risk
        FROM dh_crrem_pathways
        {where}
        ORDER BY property_type, scenario, year
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"SELECT COUNT(*) FROM dh_crrem_pathways {where}"), params).scalar()
    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/crrem/property-types")
def crrem_property_types(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List property types with CRREM pathway data."""
    rows = db.execute(text("""
        SELECT property_type, COUNT(DISTINCT country_iso3) AS countries,
               COUNT(DISTINCT scenario) AS scenarios,
               COUNT(*) AS data_points
        FROM dh_crrem_pathways
        GROUP BY property_type
        ORDER BY property_type
    """)).mappings().all()
    return {"property_types": [dict(r) for r in rows]}


@router.get("/crrem/pathway")
def crrem_pathway(
    property_type: str = Query(..., description="Property type"),
    scenario: str = Query(..., description="Scenario (1.5C or 2C)"),
    country: Optional[str] = Query(None, description="Country ISO3"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get a specific CRREM pathway time-series."""
    params = {"ptype": property_type, "scenario": scenario}
    country_filter = ""
    if country:
        country_filter = "AND country_iso3 = :country"
        params["country"] = country.upper()

    rows = db.execute(text(f"""
        SELECT year, energy_intensity_kwh_m2, carbon_intensity_kgco2_m2,
               cumulative_reduction_pct, stranding_risk, retrofit_cost_usd_m2
        FROM dh_crrem_pathways
        WHERE property_type = :ptype AND scenario = :scenario {country_filter}
        ORDER BY year
    """), params).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No CRREM pathway for {property_type}/{scenario}")
    return {
        "property_type": property_type,
        "scenario": scenario,
        "country": country,
        "pathway": [dict(r) for r in rows],
    }


# ── Grid Emission Factors ─────────────────────────────────────────────────────

@router.get("/grid-ef")
def search_grid_ef(
    country: Optional[str] = Query(None, description="Country ISO3"),
    year_start: Optional[int] = Query(None),
    year_end: Optional[int] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search grid emission factors."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()
    if year_start:
        conditions.append("year >= :ys")
        params["ys"] = year_start
    if year_end:
        conditions.append("year <= :ye")
        params["ye"] = year_end

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, country_iso3, country_name, year, grid_ef_kgco2_kwh,
               grid_ef_tco2_mwh, generation_mix_coal_pct, generation_mix_gas_pct,
               generation_mix_nuclear_pct, generation_mix_hydro_pct,
               generation_mix_wind_pct, generation_mix_solar_pct,
               total_generation_twh, data_source_org
        FROM dh_grid_emission_factors
        {where}
        ORDER BY country_iso3, year
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"SELECT COUNT(*) FROM dh_grid_emission_factors {where}"), params).scalar()
    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/grid-ef/countries")
def grid_ef_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List countries with grid emission factor data."""
    rows = db.execute(text("""
        SELECT country_iso3 AS iso3, country_name AS name,
               COUNT(*) AS years,
               MIN(grid_ef_kgco2_kwh) AS min_ef, MAX(grid_ef_kgco2_kwh) AS max_ef,
               MIN(year) AS first_year, MAX(year) AS last_year
        FROM dh_grid_emission_factors
        WHERE country_iso3 IS NOT NULL
        GROUP BY country_iso3, country_name
        ORDER BY max_ef DESC
    """)).mappings().all()
    return {"countries": [dict(r) for r in rows]}


@router.get("/grid-ef/{iso3}")
def grid_ef_country(
    iso3: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get grid emission factor time-series for a country."""
    rows = db.execute(text("""
        SELECT year, grid_ef_kgco2_kwh, grid_ef_tco2_mwh,
               generation_mix_coal_pct, generation_mix_gas_pct,
               generation_mix_nuclear_pct, generation_mix_hydro_pct,
               generation_mix_wind_pct, generation_mix_solar_pct,
               total_generation_twh
        FROM dh_grid_emission_factors
        WHERE country_iso3 = :iso3
        ORDER BY year
    """), {"iso3": iso3.upper()}).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No grid EF data for {iso3}")
    return {"country": iso3.upper(), "records": [dict(r) for r in rows]}


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def reference_data_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for reference data tables."""
    irena = db.execute(text("SELECT COUNT(*) FROM dh_irena_lcoe")).scalar() or 0
    irena_techs = db.execute(text("SELECT COUNT(DISTINCT technology) FROM dh_irena_lcoe")).scalar() or 0
    crrem = db.execute(text("SELECT COUNT(*) FROM dh_crrem_pathways")).scalar() or 0
    crrem_types = db.execute(text("SELECT COUNT(DISTINCT property_type) FROM dh_crrem_pathways")).scalar() or 0
    grid_ef = db.execute(text("SELECT COUNT(*) FROM dh_grid_emission_factors")).scalar() or 0
    grid_countries = db.execute(text("SELECT COUNT(DISTINCT country_iso3) FROM dh_grid_emission_factors")).scalar() or 0

    return {
        "irena_lcoe": {"records": irena, "technologies": irena_techs},
        "crrem_pathways": {"records": crrem, "property_types": crrem_types},
        "grid_emission_factors": {"records": grid_ef, "countries": grid_countries},
    }
