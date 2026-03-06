"""
Carbon Price API -- carbon price projections from NGFS scenario data.

Endpoints:
  GET  /carbon-prices/compare        -- compare carbon prices across scenarios
  GET  /carbon-prices/scenarios      -- list scenarios with carbon price data
  GET  /carbon-prices/stats          -- carbon price range summary
  GET  /carbon-prices/{scenario}     -- carbon price by scenario and year

Consumed by data_hub_client.get_carbon_price(scenario, year).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.scenario_ingest import NgfsScenarioData
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/carbon-prices", tags=["carbon-prices"])


# NGFS variable names for carbon price
_CARBON_PRICE_VARS = [
    "Price|Carbon",
    "Price|Carbon|Average",
]


def _find_carbon_price_records(db: Session, scenario: str, region: str = "World"):
    """Find NGFS records matching carbon price variables for a scenario."""
    q = db.query(NgfsScenarioData).filter(
        NgfsScenarioData.scenario.ilike(f"%{scenario}%"),
        NgfsScenarioData.region == region,
    )
    # Try exact variable matches first
    for var in _CARBON_PRICE_VARS:
        sub = q.filter(NgfsScenarioData.variable == var).order_by(NgfsScenarioData.year)
        records = sub.all()
        if records:
            return records

    # Fallback to pattern match
    sub = q.filter(NgfsScenarioData.variable.ilike("%Price%Carbon%")).order_by(NgfsScenarioData.year)
    return sub.all()


# ── Static routes MUST be defined before /{scenario} path-param ─────────


@router.get("/compare", name="compare_carbon_prices")
def compare_carbon_prices(
    scenarios: str = Query(..., description="Comma-separated scenario names"),
    region: str = Query("World"),
    year: Optional[int] = Query(None, description="Specific year for comparison"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Compare carbon prices across multiple NGFS scenarios."""
    scenario_list = [s.strip() for s in scenarios.split(",")]
    results = []

    for sc_name in scenario_list:
        records = _find_carbon_price_records(db, sc_name, region)
        series = [{
            "year": r.year,
            "price_usd": round(r.value, 2) if r.value else None,
        } for r in records]

        # Extract price for specific year if requested
        price_at_year = None
        if year and series:
            exact = [s for s in series if s["year"] == year]
            if exact:
                price_at_year = exact[0]["price_usd"]

        results.append({
            "scenario": sc_name,
            "price_at_year": price_at_year,
            "data_points": len(series),
            "min_price": min((s["price_usd"] for s in series if s["price_usd"]), default=None),
            "max_price": max((s["price_usd"] for s in series if s["price_usd"]), default=None),
            "time_series": series,
        })

    return {
        "region": region,
        "year": year,
        "scenarios": results,
    }


@router.get("/scenarios", name="list_carbon_price_scenarios")
def list_carbon_price_scenarios(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List NGFS scenarios that have carbon price data."""
    q = db.query(
        NgfsScenarioData.scenario,
        NgfsScenarioData.model,
        NgfsScenarioData.category,
        func.count(NgfsScenarioData.id).label("data_points"),
        func.min(NgfsScenarioData.year).label("year_min"),
        func.max(NgfsScenarioData.year).label("year_max"),
    ).filter(
        NgfsScenarioData.variable.ilike("%Price%Carbon%")
    ).group_by(
        NgfsScenarioData.scenario,
        NgfsScenarioData.model,
        NgfsScenarioData.category,
    ).order_by(NgfsScenarioData.scenario)

    rows = q.all()
    return {
        "scenarios": [{
            "scenario": r[0],
            "model": r[1],
            "category": r[2],
            "data_points": r[3],
            "year_range": {"min": r[4], "max": r[5]},
        } for r in rows],
        "total": len(rows),
    }


@router.get("/stats", name="carbon_price_stats")
def carbon_price_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for carbon price data."""
    base_q = db.query(NgfsScenarioData).filter(
        NgfsScenarioData.variable.ilike("%Price%Carbon%")
    )

    total = base_q.count()
    scenarios = db.query(func.count(distinct(NgfsScenarioData.scenario))).filter(
        NgfsScenarioData.variable.ilike("%Price%Carbon%")
    ).scalar() or 0
    models = db.query(func.count(distinct(NgfsScenarioData.model))).filter(
        NgfsScenarioData.variable.ilike("%Price%Carbon%")
    ).scalar() or 0

    return {
        "total_data_points": total,
        "distinct_scenarios": scenarios,
        "distinct_models": models,
    }


# ── Dynamic route (path-param) MUST come after all static routes ────────


@router.get("/{scenario}")
def get_carbon_price(
    scenario: str,
    year: Optional[int] = Query(None, description="Specific year (returns closest match)"),
    region: str = Query("World"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """
    Carbon price projection (USD/tCO2) for a given NGFS scenario.

    If year is specified, returns the price for that year (or nearest match).
    Otherwise returns the full time-series.
    """
    records = _find_carbon_price_records(db, scenario, region)

    if not records:
        # Return a sensible response even without data
        return {
            "scenario": scenario,
            "region": region,
            "year": year,
            "price_usd": None,
            "unit": "USD/tCO2",
            "source": "NGFS (no data found)",
            "time_series": [],
        }

    # Build full series
    series = []
    for r in records:
        series.append({
            "year": r.year,
            "price_usd": round(r.value, 2) if r.value else None,
            "unit": r.unit or "USD/tCO2",
            "model": r.model,
            "source": f"NGFS/{r.model}/{r.scenario}",
        })

    # If a specific year is requested, find the closest match
    price_for_year = None
    if year and series:
        exact = [s for s in series if s["year"] == year]
        if exact:
            price_for_year = exact[0]["price_usd"]
        else:
            # Find closest year
            closest = min(series, key=lambda s: abs(s["year"] - year))
            price_for_year = closest["price_usd"]

    return {
        "scenario": scenario,
        "region": region,
        "year": year,
        "price_usd": price_for_year,
        "unit": "USD/tCO2",
        "source": f"NGFS/{records[0].model}" if records else "NGFS",
        "time_series": series,
    }
