"""
Glidepath Serve API -- NZBA sector emissions glidepaths + CRREM pathways.

These are the endpoints consumed by data_hub_client.py:
  GET /glidepaths/nze/{sector}                -- NZBA sector glidepath
  GET /glidepaths/crrem/{country}/{asset_type} -- CRREM kgCO2/m2 pathway
  GET /glidepaths/sectors                      -- list available sectors
  GET /glidepaths/stats                        -- glidepath data stats

Data comes from dh_ngfs_scenario_data (carbon price, emissions trajectories)
and dh_crrem_pathways (live CRREM data from A13 ingester).
Hardcoded reference values serve as fallback when live data unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct, text
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.scenario_ingest import NgfsScenarioData
from api.dependencies import require_min_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/glidepaths", tags=["glidepaths"])

# ISO-2 → ISO-3 mapping for CRREM country lookups
_ISO2_TO_ISO3 = {
    "US": "USA", "GB": "GBR", "DE": "DEU", "FR": "FRA", "NL": "NLD",
    "JP": "JPN", "CN": "CHN", "IN": "IND", "BR": "BRA", "CA": "CAN",
    "AU": "AUS", "CH": "CHE", "SE": "SWE", "NO": "NOR", "DK": "DNK",
    "FI": "FIN", "IE": "IRL", "IT": "ITA", "ES": "ESP", "AT": "AUT",
    "BE": "BEL", "KR": "KOR", "SG": "SGP", "HK": "HKG", "TW": "TWN",
}


# ── Sector mapping: GICS sector → NGFS variable pattern ───────────────────

_SECTOR_EMISSION_VARS = {
    "Energy": "Emissions|CO2|Energy|Supply",
    "Utilities": "Emissions|CO2|Energy|Supply|Electricity",
    "Materials": "Emissions|CO2|Industrial Processes",
    "Industrials": "Emissions|CO2|Energy|Demand|Industry",
    "Transport": "Emissions|CO2|Energy|Demand|Transportation",
    "Buildings": "Emissions|CO2|Energy|Demand|Residential and Commercial",
    "Agriculture": "Emissions|CO2|AFOLU",
    "default": "Emissions|CO2",
}

# ── Reference CRREM pathways (kgCO2/m2/yr) — until A13 provides live data ─

_CRREM_REFERENCE = {
    "office": {
        "DE": [44, 40, 36, 32, 28, 24, 20, 16, 12, 9, 6, 4, 2, 0],
        "GB": [48, 43, 38, 34, 29, 25, 21, 17, 13, 10, 7, 4, 2, 0],
        "US": [52, 47, 42, 37, 32, 28, 23, 19, 15, 11, 8, 5, 2, 0],
        "SG": [56, 51, 46, 41, 36, 31, 26, 22, 17, 13, 9, 6, 3, 0],
        "NL": [42, 38, 34, 30, 27, 23, 19, 16, 12, 9, 6, 4, 2, 0],
    },
    "retail": {
        "DE": [50, 45, 40, 36, 31, 27, 23, 19, 15, 11, 8, 5, 2, 0],
        "GB": [55, 49, 44, 39, 34, 29, 25, 20, 16, 12, 8, 5, 3, 0],
        "US": [60, 54, 48, 43, 38, 33, 28, 23, 18, 14, 10, 6, 3, 0],
    },
    "residential": {
        "DE": [38, 34, 31, 28, 24, 21, 18, 14, 11, 8, 6, 4, 2, 0],
        "GB": [42, 38, 34, 30, 26, 22, 19, 15, 12, 9, 6, 4, 2, 0],
        "US": [46, 41, 37, 33, 29, 25, 21, 17, 14, 10, 7, 5, 2, 0],
    },
    "hotel": {
        "DE": [52, 47, 42, 37, 33, 28, 24, 20, 16, 12, 8, 5, 3, 0],
        "GB": [58, 52, 46, 41, 36, 31, 26, 22, 17, 13, 9, 6, 3, 0],
    },
    "logistics": {
        "DE": [36, 32, 29, 26, 23, 20, 17, 14, 11, 8, 6, 4, 2, 0],
        "GB": [40, 36, 32, 28, 25, 21, 18, 15, 12, 9, 6, 4, 2, 0],
    },
}

_CRREM_YEARS = list(range(2020, 2055, 5)) + [2050]
_CRREM_YEARS = [2020, 2022, 2024, 2026, 2028, 2030, 2032, 2034, 2036, 2038, 2040, 2042, 2045, 2050]


@router.get("/nze/{sector}")
def get_nze_glidepath(
    sector: str,
    scenario: str = Query("Net Zero 2050", description="NGFS scenario name"),
    model: Optional[str] = Query(None, description="IAM model name filter"),
    region: str = Query("World", description="Region code"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """
    NZBA sector emissions intensity glidepath from NGFS data.

    Returns a time-series of target values (tCO2e per unit) by year
    for use in NZBA alignment tracking and portfolio decarbonisation targets.
    """
    # Find the matching variable for this sector
    var_pattern = _SECTOR_EMISSION_VARS.get(
        sector, _SECTOR_EMISSION_VARS.get(sector.title(), _SECTOR_EMISSION_VARS["default"])
    )

    q = db.query(NgfsScenarioData).filter(
        NgfsScenarioData.scenario.ilike(f"%{scenario}%"),
        NgfsScenarioData.variable.ilike(f"%{var_pattern}%"),
        NgfsScenarioData.region == region,
    )
    if model:
        q = q.filter(NgfsScenarioData.model.ilike(f"%{model}%"))

    q = q.order_by(NgfsScenarioData.year)
    records = q.all()

    if not records:
        # Try broader search
        q2 = db.query(NgfsScenarioData).filter(
            NgfsScenarioData.scenario.ilike(f"%{scenario}%"),
            NgfsScenarioData.variable.ilike(f"%Emissions%CO2%"),
            NgfsScenarioData.region == region,
        ).order_by(NgfsScenarioData.year)
        records = q2.limit(50).all()

    # Build glidepath series
    glidepath_series = []
    if records:
        # Get the base year value for normalisation
        base_value = records[0].value if records else 1.0
        for r in records:
            glidepath_series.append({
                "year": r.year,
                "glidepath": round(r.value, 4) if r.value else None,
                "glidepath_normalised": round(r.value / base_value, 4) if r.value and base_value else None,
                "unit": r.unit,
                "source": f"NGFS/{r.model}/{r.scenario}",
            })

    return {
        "sector": sector,
        "scenario": scenario,
        "region": region,
        "variable_pattern": var_pattern,
        "data_points": len(glidepath_series),
        "glidepath_series": glidepath_series,
    }


@router.get("/crrem/{country}/{asset_type}")
def get_crrem_pathway(
    country: str,
    asset_type: str,
    scenario: str = Query("1.5C", description="CRREM scenario (1.5C or 2.0C)"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """
    CRREM carbon intensity decarbonisation pathway (kgCO2/m2/yr).

    Queries live dh_crrem_pathways table first; falls back to hardcoded
    reference values if no live data is available.
    """
    country_upper = country.upper()
    asset_lower = asset_type.lower()

    # Resolve ISO-2 to ISO-3 for DB lookup
    country_iso3 = _ISO2_TO_ISO3.get(country_upper, country_upper)

    # ── Try live DB data from dh_crrem_pathways (populated by A13 ingester) ─
    pathway_series = []
    source_label = "CRREM v2.0 (live)"
    try:
        rows = db.execute(text("""
            SELECT year, carbon_intensity_kgco2_m2, energy_intensity_kwh_m2
            FROM dh_crrem_pathways
            WHERE LOWER(property_type) = :ptype
              AND country_iso3 = :country_iso3
              AND scenario = :scenario
            ORDER BY year
        """), {
            "ptype": asset_lower,
            "country_iso3": country_iso3,
            "scenario": scenario,
        }).mappings().all()

        if rows:
            for r in rows:
                intensity = float(r["carbon_intensity_kgco2_m2"]) if r["carbon_intensity_kgco2_m2"] else None
                if intensity is not None:
                    pathway_series.append({
                        "year": int(r["year"]),
                        "intensity": round(intensity, 2),
                        "energy_intensity_kwh_m2": float(r["energy_intensity_kwh_m2"]) if r["energy_intensity_kwh_m2"] else None,
                        "unit": "kgCO2/m2/yr",
                        "source": source_label,
                    })
    except Exception as exc:
        logger.warning("CRREM live query failed, falling back to reference: %s", exc)

    # ── Fallback to hardcoded reference data ─────────────────────────────────
    if not pathway_series:
        source_label = "CRREM v2.0 (reference fallback)"
        asset_data = _CRREM_REFERENCE.get(asset_lower)
        if not asset_data:
            available = list(_CRREM_REFERENCE.keys())
            raise HTTPException(
                400,
                f"Asset type '{asset_type}' not found. Available: {available}",
            )

        # Hardcoded reference uses 2-letter codes; try both original input and 2-letter prefix
        country_2 = country_upper[:2] if len(country_upper) >= 2 else country_upper
        country_pathway = asset_data.get(country_upper) or asset_data.get(country_2)
        if not country_pathway:
            country_pathway = asset_data.get("DE")
        if not country_pathway:
            country_pathway = list(asset_data.values())[0]

        for i, year in enumerate(_CRREM_YEARS):
            if i < len(country_pathway):
                pathway_series.append({
                    "year": year,
                    "intensity": country_pathway[i],
                    "unit": "kgCO2/m2/yr",
                    "source": source_label,
                })

    return {
        "country": country_upper,
        "asset_type": asset_lower,
        "scenario": scenario,
        "data_points": len(pathway_series),
        "pathway_series": pathway_series,
        "source": source_label,
    }


@router.get("/sectors")
def list_glidepath_sectors(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List sectors with available glidepath data."""
    # Sectors from NGFS variable patterns
    ngfs_sectors = list(_SECTOR_EMISSION_VARS.keys())
    ngfs_sectors = [s for s in ngfs_sectors if s != "default"]

    # CRREM asset types -- try live DB first, fallback to reference
    crrem_types = list(_CRREM_REFERENCE.keys())
    crrem_countries = sorted(set(c for at in _CRREM_REFERENCE.values() for c in at.keys()))
    crrem_source = "reference"

    try:
        db_types = db.execute(text(
            "SELECT DISTINCT property_type FROM dh_crrem_pathways ORDER BY property_type"
        )).scalars().all()
        if db_types:
            crrem_types = [t.lower() for t in db_types]
            crrem_source = "live"
        db_countries = db.execute(text(
            "SELECT DISTINCT country_iso3 FROM dh_crrem_pathways ORDER BY country_iso3"
        )).scalars().all()
        if db_countries:
            crrem_countries = db_countries
    except Exception as exc:
        logger.debug("CRREM sectors live query fallback: %s", exc)

    return {
        "ngfs_sectors": ngfs_sectors,
        "crrem_asset_types": crrem_types,
        "crrem_countries": crrem_countries,
        "crrem_source": crrem_source,
    }


@router.get("/stats")
def glidepath_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Statistics on available glidepath data."""
    # Count NGFS emission-related records
    emission_records = db.query(func.count(NgfsScenarioData.id)).filter(
        NgfsScenarioData.variable.ilike("%Emissions%CO2%")
    ).scalar() or 0

    # Count carbon price records
    carbon_price_records = db.query(func.count(NgfsScenarioData.id)).filter(
        NgfsScenarioData.variable.ilike("%Price%Carbon%")
    ).scalar() or 0

    # CRREM stats -- try live DB, fallback to reference counts
    crrem_records = 0
    crrem_asset_types = len(_CRREM_REFERENCE)
    crrem_countries = len(set(c for at in _CRREM_REFERENCE.values() for c in at.keys()))
    crrem_source = "reference"

    try:
        crrem_records = db.execute(text("SELECT COUNT(*) FROM dh_crrem_pathways")).scalar() or 0
        if crrem_records > 0:
            crrem_asset_types = db.execute(text(
                "SELECT COUNT(DISTINCT property_type) FROM dh_crrem_pathways"
            )).scalar() or 0
            crrem_countries = db.execute(text(
                "SELECT COUNT(DISTINCT country_iso3) FROM dh_crrem_pathways"
            )).scalar() or 0
            crrem_source = "live"
    except Exception:
        pass

    return {
        "ngfs_emission_records": emission_records,
        "ngfs_carbon_price_records": carbon_price_records,
        "crrem_records": crrem_records,
        "crrem_asset_types": crrem_asset_types,
        "crrem_countries": crrem_countries,
        "crrem_source": crrem_source,
    }
