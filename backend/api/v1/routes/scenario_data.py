"""
Scenario + Target Data API routes -- NGFS scenario time-series + SBTi targets.

Endpoints:
  GET  /scenarios/ngfs                -- search NGFS scenario data points
  GET  /scenarios/ngfs/scenarios      -- list distinct scenarios
  GET  /scenarios/ngfs/variables      -- list distinct variables
  GET  /scenarios/ngfs/models         -- list distinct models
  GET  /scenarios/ngfs/compare        -- compare scenarios for a variable
  GET  /scenarios/sbti                -- search SBTi company targets
  GET  /scenarios/sbti/sectors        -- list sectors with target counts
  GET  /scenarios/sbti/countries      -- list countries with target counts
  GET  /scenarios/sbti/stats          -- summary statistics
  GET  /scenarios/stats               -- combined stats (NGFS + SBTi)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct, case
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.scenario_ingest import NgfsScenarioData, SbtiCompany
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/scenario-data", tags=["scenario-data"])


# -- NGFS endpoints -----------------------------------------------------------

@router.get("/ngfs")
def search_ngfs(
    scenario: Optional[str] = Query(None, description="Scenario name or partial match"),
    variable: Optional[str] = Query(None, description="Variable name or partial match"),
    model: Optional[str] = Query(None),
    region: Optional[str] = Query(None, description="Region code (default: World)"),
    category: Optional[str] = Query(None, description="orderly, disorderly, hot_house_world"),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search NGFS scenario data points with filters."""
    q = db.query(NgfsScenarioData)

    if scenario:
        q = q.filter(NgfsScenarioData.scenario.ilike(f"%{scenario}%"))
    if variable:
        q = q.filter(NgfsScenarioData.variable.ilike(f"%{variable}%"))
    if model:
        q = q.filter(NgfsScenarioData.model.ilike(f"%{model}%"))
    if region:
        q = q.filter(NgfsScenarioData.region == region)
    if category:
        q = q.filter(NgfsScenarioData.category == category.lower())
    if year_min:
        q = q.filter(NgfsScenarioData.year >= year_min)
    if year_max:
        q = q.filter(NgfsScenarioData.year <= year_max)

    total = q.count()
    records = (
        q.order_by(NgfsScenarioData.scenario, NgfsScenarioData.variable, NgfsScenarioData.year)
        .offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_ngfs_to_dict(r) for r in records],
    }


@router.get("/ngfs/scenarios")
def ngfs_scenarios(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List distinct NGFS scenarios with data point counts."""
    rows = (
        db.query(
            NgfsScenarioData.scenario,
            NgfsScenarioData.category,
            func.count(NgfsScenarioData.id).label("data_points"),
            func.min(NgfsScenarioData.year).label("year_min"),
            func.max(NgfsScenarioData.year).label("year_max"),
        )
        .group_by(NgfsScenarioData.scenario, NgfsScenarioData.category)
        .order_by(NgfsScenarioData.scenario)
        .all()
    )
    return {
        "scenarios": [
            {
                "scenario": r[0], "category": r[1],
                "data_points": r[2], "year_min": r[3], "year_max": r[4],
            }
            for r in rows
        ]
    }


@router.get("/ngfs/variables")
def ngfs_variables(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List distinct variables available in NGFS data."""
    rows = (
        db.query(
            NgfsScenarioData.variable,
            func.count(NgfsScenarioData.id).label("data_points"),
        )
        .group_by(NgfsScenarioData.variable)
        .order_by(NgfsScenarioData.variable)
        .all()
    )
    return {"variables": [{"variable": r[0], "data_points": r[1]} for r in rows]}


@router.get("/ngfs/models")
def ngfs_models(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List distinct models in NGFS data."""
    rows = (
        db.query(
            NgfsScenarioData.model,
            func.count(NgfsScenarioData.id).label("data_points"),
        )
        .group_by(NgfsScenarioData.model)
        .order_by(NgfsScenarioData.model)
        .all()
    )
    return {"models": [{"model": r[0], "data_points": r[1]} for r in rows]}


@router.get("/ngfs/compare")
def ngfs_compare(
    variable: str = Query(..., description="Variable to compare across scenarios"),
    region: str = Query("World"),
    model: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Compare a variable across all NGFS scenarios (time-series)."""
    q = (
        db.query(NgfsScenarioData)
        .filter(NgfsScenarioData.variable == variable)
        .filter(NgfsScenarioData.region == region)
    )
    if model:
        q = q.filter(NgfsScenarioData.model.ilike(f"%{model}%"))

    records = q.order_by(NgfsScenarioData.scenario, NgfsScenarioData.year).all()

    # Group by scenario
    by_scenario = {}
    for r in records:
        if r.scenario not in by_scenario:
            by_scenario[r.scenario] = {
                "scenario": r.scenario,
                "category": r.category,
                "model": r.model,
                "unit": r.unit,
                "data": [],
            }
        by_scenario[r.scenario]["data"].append({"year": r.year, "value": r.value})

    return {
        "variable": variable,
        "region": region,
        "scenarios": list(by_scenario.values()),
    }


# -- SBTi endpoints -----------------------------------------------------------

@router.get("/sbti")
def search_sbti(
    company: Optional[str] = Query(None, description="Company name partial match"),
    country: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="committed, near_term_approved, etc."),
    ambition: Optional[str] = Query(None, description="1.5C, well_below_2C, 2C"),
    net_zero: Optional[bool] = Query(None, description="Filter net-zero committed"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search SBTi company targets with filters."""
    q = db.query(SbtiCompany)

    if company:
        q = q.filter(SbtiCompany.company_name.ilike(f"%{company}%"))
    if country:
        q = q.filter(SbtiCompany.country.ilike(f"%{country}%"))
    if sector:
        q = q.filter(SbtiCompany.sector.ilike(f"%{sector}%"))
    if status:
        q = q.filter(SbtiCompany.target_status == status)
    if ambition:
        q = q.filter(SbtiCompany.near_term_ambition == ambition)
    if net_zero is not None:
        q = q.filter(SbtiCompany.net_zero_committed == net_zero)

    total = q.count()
    records = (
        q.order_by(SbtiCompany.company_name)
        .offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [_sbti_to_dict(r) for r in records],
    }


@router.get("/sbti/sectors")
def sbti_sectors(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List sectors with SBTi target counts and ambition breakdown."""
    rows = (
        db.query(
            SbtiCompany.sector,
            func.count(SbtiCompany.id).label("companies"),
            func.sum(case((SbtiCompany.near_term_ambition == "1.5C", 1), else_=0)).label("count_1_5c"),
            func.sum(case((SbtiCompany.net_zero_committed == True, 1), else_=0)).label("net_zero"),
        )
        .group_by(SbtiCompany.sector)
        .order_by(func.count(SbtiCompany.id).desc())
        .all()
    )
    return {
        "sectors": [
            {
                "sector": r[0], "companies": r[1],
                "aligned_1_5c": r[2], "net_zero_committed": r[3],
            }
            for r in rows
        ]
    }


@router.get("/sbti/countries")
def sbti_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """List countries with SBTi target counts."""
    rows = (
        db.query(
            SbtiCompany.country,
            func.count(SbtiCompany.id).label("companies"),
            func.sum(case((SbtiCompany.net_zero_committed == True, 1), else_=0)).label("net_zero"),
        )
        .group_by(SbtiCompany.country)
        .order_by(func.count(SbtiCompany.id).desc())
        .all()
    )
    return {
        "countries": [
            {"country": r[0], "companies": r[1], "net_zero_committed": r[2]}
            for r in rows
        ]
    }


@router.get("/sbti/stats")
def sbti_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """SBTi summary statistics."""
    total = db.query(func.count(SbtiCompany.id)).scalar() or 0
    committed = db.query(func.count(SbtiCompany.id)).filter(SbtiCompany.target_status == "committed").scalar() or 0
    near_term = db.query(func.count(SbtiCompany.id)).filter(SbtiCompany.target_status == "near_term_approved").scalar() or 0
    net_zero = db.query(func.count(SbtiCompany.id)).filter(SbtiCompany.net_zero_committed == True).scalar() or 0
    aligned_15 = db.query(func.count(SbtiCompany.id)).filter(SbtiCompany.near_term_ambition == "1.5C").scalar() or 0
    sectors = db.query(func.count(distinct(SbtiCompany.sector))).scalar() or 0
    countries = db.query(func.count(distinct(SbtiCompany.country))).scalar() or 0

    return {
        "total_companies": total,
        "committed": committed,
        "near_term_approved": near_term,
        "net_zero_committed": net_zero,
        "aligned_1_5c": aligned_15,
        "sectors": sectors,
        "countries": countries,
    }


# -- Combined stats -----------------------------------------------------------

@router.get("/stats")
def combined_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Combined statistics for NGFS scenario data and SBTi targets."""
    ngfs_count = db.query(func.count(NgfsScenarioData.id)).scalar() or 0
    ngfs_scenarios = db.query(func.count(distinct(NgfsScenarioData.scenario))).scalar() or 0
    ngfs_variables = db.query(func.count(distinct(NgfsScenarioData.variable))).scalar() or 0
    sbti_count = db.query(func.count(SbtiCompany.id)).scalar() or 0
    sbti_sectors = db.query(func.count(distinct(SbtiCompany.sector))).scalar() or 0

    return {
        "ngfs": {
            "data_points": ngfs_count,
            "scenarios": ngfs_scenarios,
            "variables": ngfs_variables,
        },
        "sbti": {
            "companies": sbti_count,
            "sectors": sbti_sectors,
        },
    }


# -- Helpers ------------------------------------------------------------------

def _ngfs_to_dict(r: NgfsScenarioData) -> dict:
    return {
        "id": r.id,
        "model": r.model,
        "scenario": r.scenario,
        "variable": r.variable,
        "region": r.region,
        "year": r.year,
        "value": r.value,
        "unit": r.unit,
        "category": r.category,
        "phase": r.phase,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }


def _sbti_to_dict(r: SbtiCompany) -> dict:
    return {
        "id": r.id,
        "company_name": r.company_name,
        "isin": r.isin,
        "lei": r.lei,
        "country": r.country,
        "region": r.region,
        "sector": r.sector,
        "industry": r.industry,
        "company_type": r.company_type,
        "target_status": r.target_status,
        "near_term_target_year": r.near_term_target_year,
        "near_term_scope": r.near_term_scope,
        "near_term_ambition": r.near_term_ambition,
        "long_term_target_year": r.long_term_target_year,
        "long_term_scope": r.long_term_scope,
        "long_term_ambition": r.long_term_ambition,
        "net_zero_committed": r.net_zero_committed,
        "net_zero_year": r.net_zero_year,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }
