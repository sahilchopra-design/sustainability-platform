"""Glidepath Tracker API — NZBA / CRREM sector glidepath data."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.base import get_db
from services.pcaf_time_series_engine import (
    pcaf_time_series_engine,
    NZBA_FALLBACK_GLIDEPATHS,
    CRREM_FALLBACK,
    GlidepathDataPoint,
    SectorGlidepathResult,
    CRREMAssetResult,
    GlidepathStatusRow,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/glidepath", tags=["Glidepath Tracker"])


def _compute_waci_rows(portfolio_id: str, db: Session) -> list:
    """
    Compute WACI time-series rows from assets_pg + esrs_e1_ghg_emissions.
    WACI = Σ_i (exposure_weight_i x GHG_intensity_i)
    GHG_intensity = (scope1 + scope2_market) tCO2e / net_turnover_mEUR
    Returns rows in the format expected by pcaf_time_series_engine.
    """
    try:
        rows = db.execute(text("""
            SELECT
                a.company_sector,
                a.exposure,
                g.scope1_gross_tco2e,
                g.scope2_market_based_tco2e,
                cer.net_turnover_meur,
                g.reporting_year
            FROM assets_pg a
            JOIN csrd_entity_registry cer ON cer.legal_name = a.company_name
            LEFT JOIN esrs_e1_ghg_emissions g ON g.entity_registry_id = cer.id
            WHERE a.portfolio_id = :pid
              AND g.scope1_gross_tco2e IS NOT NULL
              AND cer.net_turnover_meur IS NOT NULL
              AND cer.net_turnover_meur > 0
        """), {"pid": portfolio_id}).fetchall()
        if not rows:
            return []
        total_exposure = sum(float(r[1]) for r in rows if r[1]) or 1.0
        sector_year: dict = defaultdict(lambda: {"w": 0.0, "waci": 0.0})
        for r in rows:
            sector = r[0] or "Other"
            exposure = float(r[1] or 0)
            s1 = float(r[2] or 0)
            s2 = float(r[3] or 0)
            revenue = float(r[4] or 1)
            year = int(r[5]) if r[5] else 2024
            weight = exposure / total_exposure
            intensity = (s1 + s2) / revenue   # tCO2e per MEUR revenue
            key = (sector, year)
            sector_year[key]["w"] += weight
            sector_year[key]["waci"] += weight * intensity
        result = []
        for (sector, year), v in sector_year.items():
            if v["w"] > 0:
                result.append({
                    "metric_type": "waci",
                    "sector": sector,
                    "reporting_year": year,
                    "actual_value": round(v["waci"], 4),
                })
        return result
    except Exception as exc:
        logger.warning("WACI computation failed: %s", exc)
        return []


# ─────────────────────────────────────────────────────────
# Response helpers
# ─────────────────────────────────────────────────────────
def _dp_to_dict(dp: GlidepathDataPoint) -> dict:
    return {
        "year": dp.year,
        "actual_waci": dp.actual_waci,
        "nzba_target": dp.nzba_target,
        "iea_nze_reference": dp.iea_nze_reference,
        "rag_status": dp.rag_status,
        "deviation_pct": dp.deviation_pct,
    }


# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────
@router.get("/sectors", summary="List available sectors with NZBA glidepaths")
async def list_glidepath_sectors():
    return {
        "sectors": pcaf_time_series_engine.get_available_sectors(),
        "source": "NZBA 2021 Guidelines / IEA WEO 2023 (fallback — connect Data Hub for live glidepaths)",
    }


@router.get("/sector/{sector}", summary="Sector glidepath vs actual portfolio WACI")
async def get_sector_glidepath(
    sector: str,
    portfolio_id: str = Query(..., description="Portfolio ID"),
    db: Session = Depends(get_db),
):
    """
    Returns actual WACI trajectory from assets_pg + esrs_e1_ghg_emissions vs NZBA/IEA NZE reference.
    WACI is computed from real CSRD entity GHG data for the given portfolio.
    Falls back to reference glidepath only when no CSRD entities are mapped.
    """
    waci_rows = _compute_waci_rows(portfolio_id, db)
    result = pcaf_time_series_engine.get_sector_glidepath(
        portfolio_id=portfolio_id,
        sector=sector,
        time_series_rows=waci_rows,
        data_hub_glidepath=None,
    )

    if not result.data_available:
        raise HTTPException(status_code=500, detail=result.error_message)

    return {
        "sector": result.sector,
        "portfolio_id": result.portfolio_id,
        "current_rag": result.current_rag,
        "glidepath_source": result.glidepath_source,
        "data_points": [_dp_to_dict(dp) for dp in result.data_points],
        "data_available": True,
        "waci_rows_found": len(waci_rows),
    }


@router.get("/portfolio/{portfolio_id}/status-grid", summary="Multi-sector RAG status grid")
async def get_glidepath_status_grid(
    portfolio_id: str,
    sectors: str = Query(
        default="Power,Oil & Gas,Steel,Shipping",
        description="Comma-separated sector list"
    ),
    db: Session = Depends(get_db),
):
    """Returns a sector x year RAG grid for the Glidepath Tracker table."""
    sector_list = [s.strip() for s in sectors.split(",") if s.strip()]
    waci_rows = _compute_waci_rows(portfolio_id, db)
    grid = pcaf_time_series_engine.build_status_grid(
        portfolio_id=portfolio_id,
        sectors=sector_list,
        time_series_rows=waci_rows,
    )
    return {
        "portfolio_id": portfolio_id,
        "sectors": sector_list,
        "years": [2025, 2030, 2035, 2040, 2045, 2050],
        "grid": [
            {"sector": r.sector, "year": r.year, "actual": r.actual, "target": r.target, "rag": r.rag}
            for r in grid
        ],
    }


@router.get("/nzba/{sector}", summary="Raw NZBA glidepath values for a sector")
async def get_nzba_glidepath(sector: str):
    """Returns the NZBA reference glidepath (fallback values — use Data Hub for authoritative data)."""
    glidepath = NZBA_FALLBACK_GLIDEPATHS.get(sector, NZBA_FALLBACK_GLIDEPATHS.get("Other"))
    if not glidepath:
        raise HTTPException(status_code=404, detail=f"No glidepath found for sector '{sector}'")
    return {
        "sector": sector,
        "metric": "WACI tCO2e/MEUR",
        "source": "NZBA 2021 Guidelines (fallback)",
        "glidepath": [{"year": yr, "value": val} for yr, val in sorted(glidepath.items())],
    }


@router.get("/crrem/{asset_type}", summary="CRREM reference pathway for real estate asset type")
async def get_crrem_pathway(
    asset_type: str,
    country: str = Query(default="EU", description="Country / region code"),
):
    """Returns CRREM kgCO2/m² pathway for a given asset type."""
    pathway = CRREM_FALLBACK.get(asset_type, CRREM_FALLBACK.get("Office"))
    return {
        "asset_type": asset_type,
        "country": country,
        "metric": "kgCO2/m2",
        "source": "CRREM v2.0 (fallback — connect Data Hub for country-specific pathways)",
        "pathway": [{"year": yr, "value": val} for yr, val in sorted(pathway.items())],
    }


@router.get("/crrem/asset/{asset_id}", summary="CRREM comparison for a specific real estate asset")
async def get_crrem_asset(
    asset_id: str,
    asset_name: str = Query(default="Asset"),
    asset_type: str = Query(default="Office"),
    country: str = Query(default="EU"),
):
    """Returns CRREM pathway vs actual energy intensity for a single asset."""
    # TODO: load actual data from real_estate / assets tables
    result = pcaf_time_series_engine.get_crrem_asset(
        asset_id=asset_id,
        asset_name=asset_name,
        asset_type=asset_type,
        country=country,
        actual_by_year={},
        crrem_pathway=None,
    )
    return {
        "asset_id": result.asset_id,
        "asset_name": result.asset_name,
        "stranding_year": result.stranding_year,
        "current_intensity_kgco2_m2": result.current_intensity_kgco2_m2,
        "pathway_source": result.crrem_pathway_source,
        "data_points": [_dp_to_dict(dp) for dp in result.data_points],
    }
