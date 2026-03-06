"""
Glidepath Serve API -- NZBA sector emissions glidepaths + CRREM pathways.

These are the endpoints consumed by data_hub_client.py:
  GET /glidepaths/nze/{sector}                -- NZBA sector glidepath
  GET /glidepaths/crrem/{country}/{asset_type} -- CRREM kgCO2/m2 pathway
  GET /glidepaths/sectors                      -- list available sectors
  GET /glidepaths/stats                        -- glidepath data stats

Data comes from dh_ngfs_scenario_data (carbon price, emissions trajectories)
and reference CRREM tables. CRREM ingester (A13) will add live data later;
for now returns reference values.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.scenario_ingest import NgfsScenarioData
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/glidepaths", tags=["glidepaths"])


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
    _user=Depends(require_min_role("viewer")),
):
    """
    CRREM carbon intensity decarbonisation pathway (kgCO2/m2/yr).

    Returns the target intensity by year for a given country and asset type.
    Uses reference CRREM data until A13 ingester provides live data.
    """
    country_upper = country.upper()
    asset_lower = asset_type.lower()

    asset_data = _CRREM_REFERENCE.get(asset_lower)
    if not asset_data:
        available = list(_CRREM_REFERENCE.keys())
        raise HTTPException(
            400,
            f"Asset type '{asset_type}' not found. Available: {available}",
        )

    country_pathway = asset_data.get(country_upper)
    if not country_pathway:
        # Fallback to DE as default
        country_pathway = asset_data.get("DE")
        if not country_pathway:
            country_pathway = list(asset_data.values())[0]

    pathway_series = []
    for i, year in enumerate(_CRREM_YEARS):
        if i < len(country_pathway):
            pathway_series.append({
                "year": year,
                "intensity": country_pathway[i],
                "unit": "kgCO2/m2/yr",
                "source": "CRREM v2.0 (reference)",
            })

    return {
        "country": country_upper,
        "asset_type": asset_lower,
        "data_points": len(pathway_series),
        "pathway_series": pathway_series,
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

    # CRREM asset types
    crrem_types = list(_CRREM_REFERENCE.keys())

    return {
        "ngfs_sectors": ngfs_sectors,
        "crrem_asset_types": crrem_types,
        "crrem_countries": sorted(set(
            c for at in _CRREM_REFERENCE.values() for c in at.keys()
        )),
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

    return {
        "ngfs_emission_records": emission_records,
        "ngfs_carbon_price_records": carbon_price_records,
        "crrem_asset_types": len(_CRREM_REFERENCE),
        "crrem_countries": len(set(c for at in _CRREM_REFERENCE.values() for c in at.keys())),
    }
