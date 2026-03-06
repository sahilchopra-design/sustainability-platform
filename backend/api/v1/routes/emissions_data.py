"""
Emissions Data API routes -- Climate TRACE + OWID CO2/energy queries.

Endpoints:
  GET  /emissions/climate-trace          -- search Climate TRACE emissions
  GET  /emissions/climate-trace/sectors  -- list available sectors
  GET  /emissions/climate-trace/countries -- list countries with data
  GET  /emissions/owid                   -- search OWID CO2/energy data
  GET  /emissions/owid/countries         -- list countries with data
  GET  /emissions/owid/{iso3}            -- get time-series for a country
  GET  /emissions/stats                  -- summary counts
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.emissions import ClimateTraceEmission, OwidCo2Energy
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/emissions", tags=["emissions"])


# -- Climate TRACE endpoints --------------------------------------------------

@router.get("/climate-trace")
def search_climate_trace(
    country: Optional[str] = Query(None, description="ISO3 country code"),
    sector: Optional[str] = Query(None),
    gas: Optional[str] = Query(None, description="co2e, co2, ch4, n2o"),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search Climate TRACE satellite-derived emissions."""
    q = db.query(ClimateTraceEmission)

    if country:
        q = q.filter(ClimateTraceEmission.country_iso3 == country.upper())
    if sector:
        q = q.filter(ClimateTraceEmission.sector.ilike(f"%{sector}%"))
    if gas:
        q = q.filter(ClimateTraceEmission.gas == gas.lower())
    if year_min:
        q = q.filter(ClimateTraceEmission.year >= year_min)
    if year_max:
        q = q.filter(ClimateTraceEmission.year <= year_max)

    total = q.count()
    records = (
        q.order_by(ClimateTraceEmission.country_iso3, ClimateTraceEmission.year.desc())
        .offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_ct_to_dict(r) for r in records],
    }


@router.get("/climate-trace/sectors")
def ct_sectors(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List distinct sectors in Climate TRACE data."""
    rows = (
        db.query(
            ClimateTraceEmission.sector,
            func.count(ClimateTraceEmission.id).label("count"),
        )
        .group_by(ClimateTraceEmission.sector)
        .order_by(ClimateTraceEmission.sector)
        .all()
    )
    return {"sectors": [{"sector": r[0], "count": r[1]} for r in rows]}


@router.get("/climate-trace/countries")
def ct_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List countries with Climate TRACE data."""
    rows = (
        db.query(
            ClimateTraceEmission.country_iso3,
            ClimateTraceEmission.country_name,
            func.count(ClimateTraceEmission.id).label("count"),
        )
        .group_by(ClimateTraceEmission.country_iso3, ClimateTraceEmission.country_name)
        .order_by(ClimateTraceEmission.country_iso3)
        .all()
    )
    return {
        "countries": [
            {"iso3": r[0], "name": r[1], "records": r[2]} for r in rows
        ]
    }


# -- OWID endpoints -----------------------------------------------------------

@router.get("/owid")
def search_owid(
    country: Optional[str] = Query(None, description="ISO3 country code"),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search OWID CO2 and energy data."""
    q = db.query(OwidCo2Energy)

    if country:
        q = q.filter(OwidCo2Energy.country_iso3 == country.upper())
    if year_min:
        q = q.filter(OwidCo2Energy.year >= year_min)
    if year_max:
        q = q.filter(OwidCo2Energy.year <= year_max)

    total = q.count()
    records = (
        q.order_by(OwidCo2Energy.country_iso3, OwidCo2Energy.year.desc())
        .offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_owid_to_dict(r) for r in records],
    }


@router.get("/owid/countries")
def owid_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List countries with OWID data."""
    rows = (
        db.query(
            OwidCo2Energy.country_iso3,
            OwidCo2Energy.country_name,
            func.count(OwidCo2Energy.id).label("count"),
            func.min(OwidCo2Energy.year).label("year_min"),
            func.max(OwidCo2Energy.year).label("year_max"),
        )
        .group_by(OwidCo2Energy.country_iso3, OwidCo2Energy.country_name)
        .order_by(OwidCo2Energy.country_iso3)
        .all()
    )
    return {
        "countries": [
            {
                "iso3": r[0], "name": r[1], "records": r[2],
                "year_min": r[3], "year_max": r[4],
            }
            for r in rows
        ]
    }


@router.get("/owid/{iso3}")
def owid_country_series(
    iso3: str,
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get full CO2/energy time-series for a single country."""
    q = db.query(OwidCo2Energy).filter(OwidCo2Energy.country_iso3 == iso3.upper())

    if year_min:
        q = q.filter(OwidCo2Energy.year >= year_min)
    if year_max:
        q = q.filter(OwidCo2Energy.year <= year_max)

    records = q.order_by(OwidCo2Energy.year).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No OWID data for country {iso3.upper()}")

    return {
        "country_iso3": iso3.upper(),
        "country_name": records[0].country_name if records else None,
        "years": len(records),
        "series": [_owid_to_dict(r) for r in records],
    }


# -- Stats endpoint -----------------------------------------------------------

@router.get("/stats")
def emissions_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for emissions ingestion tables."""
    ct_count = db.query(func.count(ClimateTraceEmission.id)).scalar() or 0
    ct_countries = db.query(func.count(distinct(ClimateTraceEmission.country_iso3))).scalar() or 0
    owid_count = db.query(func.count(OwidCo2Energy.id)).scalar() or 0
    owid_countries = db.query(func.count(distinct(OwidCo2Energy.country_iso3))).scalar() or 0

    return {
        "climate_trace": {
            "records": ct_count,
            "countries": ct_countries,
        },
        "owid": {
            "records": owid_count,
            "countries": owid_countries,
        },
    }


# -- Helpers ------------------------------------------------------------------

def _ct_to_dict(r: ClimateTraceEmission) -> dict:
    return {
        "id": r.id,
        "country_iso3": r.country_iso3,
        "country_name": r.country_name,
        "sector": r.sector,
        "subsector": r.subsector,
        "gas": r.gas,
        "year": r.year,
        "emissions_quantity": r.emissions_quantity,
        "emissions_unit": r.emissions_unit,
        "facility_name": r.facility_name,
        "facility_id": r.facility_id,
        "latitude": r.latitude,
        "longitude": r.longitude,
        "confidence": r.confidence,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }


def _owid_to_dict(r: OwidCo2Energy) -> dict:
    return {
        "country_iso3": r.country_iso3,
        "country_name": r.country_name,
        "year": r.year,
        "population": r.population,
        "gdp": r.gdp,
        "co2": r.co2,
        "co2_per_capita": r.co2_per_capita,
        "co2_per_gdp": r.co2_per_gdp,
        "co2_growth_pct": r.co2_growth_pct,
        "cumulative_co2": r.cumulative_co2,
        "share_global_co2": r.share_global_co2,
        "coal_co2": r.coal_co2,
        "oil_co2": r.oil_co2,
        "gas_co2": r.gas_co2,
        "cement_co2": r.cement_co2,
        "flaring_co2": r.flaring_co2,
        "other_co2": r.other_co2,
        "methane": r.methane,
        "nitrous_oxide": r.nitrous_oxide,
        "total_ghg": r.total_ghg,
        "total_ghg_excl_lucf": r.total_ghg_excl_lucf,
        "primary_energy_consumption": r.primary_energy_consumption,
        "energy_per_capita": r.energy_per_capita,
        "energy_per_gdp": r.energy_per_gdp,
        "electricity_generation": r.electricity_generation,
        "renewables_share_energy": r.renewables_share_energy,
        "renewables_share_elec": r.renewables_share_elec,
        "fossil_share_energy": r.fossil_share_energy,
        "nuclear_share_energy": r.nuclear_share_energy,
        "solar_share_energy": r.solar_share_energy,
        "wind_share_energy": r.wind_share_energy,
        "hydro_share_energy": r.hydro_share_energy,
        "temperature_change_from_co2": r.temperature_change_from_co2,
        "temperature_change_from_ghg": r.temperature_change_from_ghg,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }
