"""
Country Risk & Governance Index Routes
Endpoints for querying CPI, FSI, Freedom House FIW, UNDP GII and coal capacity data.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/country-risk", tags=["Country Risk & Governance"])


# ─────────────────────────────────────────────────────────
# Index metadata
# ─────────────────────────────────────────────────────────
INDEX_META = {
    "CPI": {
        "full_name": "Corruption Perceptions Index",
        "source": "Transparency International",
        "scale": "0-100 (higher = less corrupt)",
        "category": "governance",
    },
    "FSI": {
        "full_name": "Fragile States Index",
        "source": "Fund for Peace",
        "scale": "0-120 (higher = more fragile)",
        "category": "governance",
    },
    "FH_FIW": {
        "full_name": "Freedom in the World",
        "source": "Freedom House",
        "scale": "1-7 PR/CL ratings (1 = most free)",
        "category": "governance",
    },
    "UNDP_GII": {
        "full_name": "Gender Inequality Index",
        "source": "UNDP Human Development Report",
        "scale": "0-1 (higher = more inequality)",
        "category": "social",
    },
}


# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────
@router.get("/indices")
def list_available_indices(db: Session = Depends(get_db)):
    """List all available indices with metadata and row counts."""
    try:
        rows = db.execute(text("""
            SELECT index_name, COUNT(*), MIN(year), MAX(year),
                   COUNT(DISTINCT country_iso3)
            FROM dh_country_risk_indices
            GROUP BY index_name
            ORDER BY index_name
        """)).fetchall()
        return {
            "indices": [
                {
                    "index_name": r[0],
                    **(INDEX_META.get(r[0], {})),
                    "record_count": r[1],
                    "year_range": {"min": r[2], "max": r[3]},
                    "country_count": r[4],
                }
                for r in rows
            ]
        }
    except Exception as exc:
        logger.exception("Country risk indices list error")
        raise HTTPException(500, f"Error: {exc}") from exc


@router.get("/country/{country_iso3}")
def get_country_profile(country_iso3: str, db: Session = Depends(get_db)):
    """Get all risk/governance indices for a single country."""
    iso = country_iso3.upper()
    try:
        rows = db.execute(text("""
            SELECT index_name, year, score, rank, subcategories,
                   country_name, source_name
            FROM dh_country_risk_indices
            WHERE country_iso3 = :iso
            ORDER BY index_name, year DESC
        """), {"iso": iso}).fetchall()

        if not rows:
            raise HTTPException(404, f"No data for country {iso}")

        country_name = rows[0][5]
        by_index: dict = {}
        for r in rows:
            idx = r[0]
            if idx not in by_index:
                by_index[idx] = {
                    "index_name": idx,
                    **(INDEX_META.get(idx, {})),
                    "latest_score": None,
                    "latest_rank": None,
                    "latest_year": None,
                    "time_series": [],
                }
            entry = {
                "year": r[1],
                "score": float(r[2]) if r[2] is not None else None,
                "rank": r[3],
                "subcategories": r[4],
            }
            if by_index[idx]["latest_year"] is None or r[1] > by_index[idx]["latest_year"]:
                by_index[idx]["latest_score"] = entry["score"]
                by_index[idx]["latest_rank"] = entry["rank"]
                by_index[idx]["latest_year"] = entry["year"]
            by_index[idx]["time_series"].append(entry)

        # Also fetch coal capacity from dh_reference_data
        coal = db.execute(text("""
            SELECT kpi_name, value_numeric, unit
            FROM dh_reference_data
            WHERE source_name = 'GEM Coal Plant Tracker'
              AND LOWER(entity_name) = LOWER(:country)
        """), {"country": country_name}).fetchall()

        coal_data = None
        if coal:
            coal_data = {r[0]: {"value": r[1], "unit": r[2]} for r in coal}

        return {
            "country_iso3": iso,
            "country_name": country_name,
            "indices": list(by_index.values()),
            "coal_capacity": coal_data,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Country profile error: %s", iso)
        raise HTTPException(500, f"Country profile error: {exc}") from exc


@router.get("/rankings/{index_name}")
def get_index_rankings(
    index_name: str,
    year: Optional[int] = Query(None, description="Year to rank; defaults to latest"),
    limit: int = Query(50, ge=1, le=300),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get ranked list of countries for a specific index and year."""
    try:
        if index_name not in INDEX_META:
            available = list(INDEX_META.keys())
            raise HTTPException(400, f"Unknown index '{index_name}'. Available: {available}")

        if year is None:
            yr_row = db.execute(text(
                "SELECT MAX(year) FROM dh_country_risk_indices WHERE index_name = :idx"
            ), {"idx": index_name}).fetchone()
            year = yr_row[0] if yr_row and yr_row[0] else 2023

        count_row = db.execute(text(
            "SELECT COUNT(*) FROM dh_country_risk_indices WHERE index_name = :idx AND year = :yr"
        ), {"idx": index_name, "yr": year}).fetchone()

        # Determine sort order: CPI/FH_FIW higher = better → DESC; FSI/GII higher = worse → ASC
        sort = "DESC" if index_name in ("CPI",) else "ASC"

        rows = db.execute(text(f"""
            SELECT country_name, country_iso3, score, rank, subcategories
            FROM dh_country_risk_indices
            WHERE index_name = :idx AND year = :yr
            ORDER BY score {sort} NULLS LAST
            LIMIT :lim OFFSET :off
        """), {"idx": index_name, "yr": year, "lim": limit, "off": offset}).fetchall()

        return {
            "index_name": index_name,
            **(INDEX_META[index_name]),
            "year": year,
            "total": count_row[0] if count_row else 0,
            "rankings": [
                {
                    "rank": i + 1 + offset,
                    "country_name": r[0],
                    "country_iso3": r[1],
                    "score": float(r[2]) if r[2] is not None else None,
                    "original_rank": r[3],
                    "subcategories": r[4],
                }
                for i, r in enumerate(rows)
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Rankings error: %s", index_name)
        raise HTTPException(500, f"Rankings error: {exc}") from exc


@router.get("/compare")
def compare_countries(
    countries: str = Query(..., description="Comma-separated ISO3 codes, e.g. GBR,DEU,FRA"),
    index_name: Optional[str] = Query(None, description="Filter to specific index"),
    db: Session = Depends(get_db),
):
    """Compare multiple countries across all or a specific governance index."""
    iso_list = [c.strip().upper() for c in countries.split(",") if c.strip()]
    if len(iso_list) < 2:
        raise HTTPException(400, "Provide at least 2 comma-separated ISO3 codes")
    if len(iso_list) > 20:
        raise HTTPException(400, "Maximum 20 countries for comparison")

    try:
        placeholders = ", ".join(f":c{i}" for i in range(len(iso_list)))
        params = {f"c{i}": c for i, c in enumerate(iso_list)}

        idx_clause = ""
        if index_name:
            idx_clause = "AND index_name = :idx"
            params["idx"] = index_name

        rows = db.execute(text(f"""
            SELECT country_iso3, country_name, index_name, year, score, rank, subcategories
            FROM dh_country_risk_indices
            WHERE country_iso3 IN ({placeholders}) {idx_clause}
            ORDER BY country_iso3, index_name, year DESC
        """), params).fetchall()

        # Group by country
        by_country: dict = {}
        for r in rows:
            iso = r[0]
            if iso not in by_country:
                by_country[iso] = {"country_iso3": iso, "country_name": r[1], "indices": {}}
            idx = r[2]
            if idx not in by_country[iso]["indices"]:
                by_country[iso]["indices"][idx] = {
                    "index_name": idx,
                    **(INDEX_META.get(idx, {})),
                    "latest": None,
                    "time_series": [],
                }
            entry = {
                "year": r[3],
                "score": float(r[4]) if r[4] is not None else None,
                "rank": r[5],
            }
            if by_country[iso]["indices"][idx]["latest"] is None:
                by_country[iso]["indices"][idx]["latest"] = entry
            by_country[iso]["indices"][idx]["time_series"].append(entry)

        return {
            "countries": list(by_country.values()),
            "indices_included": list(INDEX_META.keys()) if not index_name else [index_name],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Country compare error")
        raise HTTPException(500, f"Compare error: {exc}") from exc


@router.get("/heatmap")
def country_risk_heatmap(
    index_name: str = Query(..., description="Index to visualise"),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Return all countries with scores for a choropleth/heatmap visualisation."""
    try:
        if year is None:
            yr_row = db.execute(text(
                "SELECT MAX(year) FROM dh_country_risk_indices WHERE index_name = :idx"
            ), {"idx": index_name}).fetchone()
            year = yr_row[0] if yr_row and yr_row[0] else 2023

        rows = db.execute(text("""
            SELECT country_iso3, country_iso2, country_name, score, rank
            FROM dh_country_risk_indices
            WHERE index_name = :idx AND year = :yr
            ORDER BY country_name
        """), {"idx": index_name, "yr": year}).fetchall()

        return {
            "index_name": index_name,
            **(INDEX_META.get(index_name, {})),
            "year": year,
            "data": [
                {
                    "iso3": r[0], "iso2": r[1], "name": r[2],
                    "score": float(r[3]) if r[3] is not None else None,
                    "rank": r[4],
                }
                for r in rows
            ],
        }
    except Exception as exc:
        logger.exception("Heatmap error")
        raise HTTPException(500, f"Heatmap error: {exc}") from exc


@router.get("/coal-capacity")
def coal_capacity_by_country(
    country: Optional[str] = Query(None, description="Filter by country name (partial match)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get coal plant capacity data by country from GEM Coal Plant Tracker."""
    try:
        clauses = ["r.source_name = 'GEM Coal Plant Tracker'"]
        params: dict = {}
        if country:
            clauses.append("LOWER(r.entity_name) LIKE :cn")
            params["cn"] = f"%{country.lower()}%"
        where = " AND ".join(clauses)

        # First get limited set of distinct countries
        country_rows = db.execute(text(f"""
            SELECT DISTINCT entity_name FROM dh_reference_data r
            WHERE {where}
            ORDER BY entity_name
            LIMIT :lim
        """), {**params, "lim": limit}).fetchall()
        country_names = [r[0] for r in country_rows]

        if not country_names:
            return {"total_countries": 0, "countries": []}

        # Then get all KPI rows for those countries
        rows = db.execute(text("""
            SELECT entity_name, kpi_name, value_numeric, unit
            FROM dh_reference_data
            WHERE source_name = 'GEM Coal Plant Tracker'
              AND entity_name = ANY(:names)
            ORDER BY entity_name, kpi_name
        """), {"names": country_names}).fetchall()

        # Group by country
        by_country: dict = {}
        for r in rows:
            cn = r[0]
            if cn not in by_country:
                by_country[cn] = {"country": cn, "capacities": {}}
            by_country[cn]["capacities"][r[1]] = {
                "value_mw": r[2],
                "unit": r[3],
            }

        # Get total count of all countries
        total = db.execute(text(
            "SELECT COUNT(DISTINCT entity_name) FROM dh_reference_data WHERE source_name = 'GEM Coal Plant Tracker'"
        )).scalar() or 0

        return {
            "total_countries": total,
            "showing": len(by_country),
            "countries": list(by_country.values()),
        }
    except Exception as exc:
        logger.exception("Coal capacity error")
        raise HTTPException(500, f"Coal capacity error: {exc}") from exc
