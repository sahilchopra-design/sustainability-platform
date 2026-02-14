"""
NGFS Scenario Module API — all 24 scenarios across 3 phases.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from db.base import get_db
from db.models.ngfs_v2 import NGFSScenario, NGFSScenarioParameter, NGFSScenarioTimeSeries

router = APIRouter(prefix="/api/v1/ngfs-scenarios", tags=["ngfs-scenarios"])


# ---- Schemas ----

class ScenarioSummary(BaseModel):
    id: str; name: str; slug: str; phase: int; phase_year: Optional[int] = None
    category: Optional[str] = None; temperature_target: Optional[float] = None
    temperature_by_2100: Optional[float] = None; carbon_neutral_year: Optional[int] = None
    description: Optional[str] = None; physical_risk_level: Optional[str] = None
    transition_risk_level: Optional[str] = None; is_active: bool = True
    class Config:
        from_attributes = True


class ParameterResponse(BaseModel):
    id: str; parameter_name: str; display_name: str; unit: Optional[str] = None
    category: Optional[str] = None; is_editable: bool = True
    min_value: Optional[float] = None; max_value: Optional[float] = None
    default_value: Optional[float] = None; step_size: Optional[float] = None
    class Config:
        from_attributes = True


class TimeSeriesPoint(BaseModel):
    year: int; value: float; is_interpolated: bool = False


class ScenarioFull(ScenarioSummary):
    key_assumptions: dict = {}; policy_implications: Optional[str] = None
    parameters: List[ParameterResponse] = []


class CompareRequest(BaseModel):
    scenario_ids: List[str]
    metrics: List[str] = ["carbon_price", "emissions", "temperature", "gdp_impact"]


# ---- Helpers ----

def _wrap(data, meta=None):
    """Standard response wrapper."""
    base_meta = {"version": "2023.2"}
    if meta:
        base_meta.update(meta)
    return {"data": data, "meta": base_meta}


# ---- Routes ----

@router.get("")
def list_scenarios(
    phase: Optional[int] = None,
    category: Optional[str] = None,
    temperature_target: Optional[float] = None,
    sort_by: str = Query("phase", regex="^(phase|temperature_target|name|carbon_neutral_year)$"),
    db: Session = Depends(get_db),
):
    """List all NGFS scenarios with optional filters."""
    q = db.query(NGFSScenario).filter(NGFSScenario.is_active.is_(True))
    if phase:
        q = q.filter(NGFSScenario.phase == phase)
    if category:
        q = q.filter(NGFSScenario.category.ilike(f"%{category}%"))
    if temperature_target:
        q = q.filter(NGFSScenario.temperature_target <= temperature_target + 0.3,
                     NGFSScenario.temperature_target >= temperature_target - 0.3)

    order = {"phase": NGFSScenario.phase, "temperature_target": NGFSScenario.temperature_target,
             "name": NGFSScenario.name, "carbon_neutral_year": NGFSScenario.carbon_neutral_year}
    q = q.order_by(order.get(sort_by, NGFSScenario.phase), NGFSScenario.name)

    scenarios = q.all()
    total = len(scenarios)
    phase_count = {}
    for s in scenarios:
        phase_count[str(s.phase)] = phase_count.get(str(s.phase), 0) + 1

    temps = [s.temperature_by_2100 for s in scenarios if s.temperature_by_2100]
    return _wrap(
        [ScenarioSummary.model_validate(s).model_dump() for s in scenarios],
        {"total_scenarios": total, "phase_count": phase_count,
         "temperature_range": {"min": min(temps) if temps else None, "max": max(temps) if temps else None}}
    )


@router.get("/phases")
def get_phases(db: Session = Depends(get_db)):
    """Summary of scenarios by phase."""
    phases = {}
    for phase_num, year in [(1, 2020), (2, 2021), (3, 2023)]:
        scs = db.query(NGFSScenario).filter(NGFSScenario.phase == phase_num).all()
        temps = [s.temperature_by_2100 for s in scs if s.temperature_by_2100]
        phases[str(phase_num)] = {
            "year": year, "count": len(scs),
            "scenarios": [{"id": s.id, "name": s.name, "slug": s.slug,
                          "category": s.category, "temperature": s.temperature_by_2100} for s in scs],
            "temperature_range": {"min": min(temps) if temps else None, "max": max(temps) if temps else None},
        }
    return _wrap(phases)


@router.get("/temperature-ranges")
def get_temperature_ranges(db: Session = Depends(get_db)):
    """Scenarios grouped by temperature outcome."""
    scs = db.query(NGFSScenario).filter(NGFSScenario.is_active.is_(True)).all()
    buckets = {"below_1.5C": [], "1.5-2.0C": [], "2.0-2.5C": [], "2.5-3.0C": [], "above_3.0C": []}
    for s in scs:
        t = s.temperature_by_2100 or 99
        entry = {"id": s.id, "name": s.name, "temperature": t, "category": s.category, "phase": s.phase}
        if t <= 1.5: buckets["below_1.5C"].append(entry)
        elif t <= 2.0: buckets["1.5-2.0C"].append(entry)
        elif t <= 2.5: buckets["2.0-2.5C"].append(entry)
        elif t <= 3.0: buckets["2.5-3.0C"].append(entry)
        else: buckets["above_3.0C"].append(entry)
    return _wrap(buckets)


@router.get("/filter")
def filter_scenarios(
    min_temp: Optional[float] = None,
    max_temp: Optional[float] = None,
    phases: Optional[str] = None,
    has_net_zero_target: Optional[bool] = None,
    net_zero_by_year: Optional[int] = None,
    carbon_price_min: Optional[float] = None,
    carbon_price_max: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Advanced filtering."""
    q = db.query(NGFSScenario).filter(NGFSScenario.is_active.is_(True))
    if min_temp is not None:
        q = q.filter(NGFSScenario.temperature_by_2100 >= min_temp)
    if max_temp is not None:
        q = q.filter(NGFSScenario.temperature_by_2100 <= max_temp)
    if phases:
        phase_list = [int(p) for p in phases.split(",")]
        q = q.filter(NGFSScenario.phase.in_(phase_list))
    if has_net_zero_target is True:
        q = q.filter(NGFSScenario.carbon_neutral_year.isnot(None))
    elif has_net_zero_target is False:
        q = q.filter(NGFSScenario.carbon_neutral_year.is_(None))
    if net_zero_by_year:
        q = q.filter(NGFSScenario.carbon_neutral_year <= net_zero_by_year)

    scenarios = q.order_by(NGFSScenario.temperature_by_2100).all()

    # Post-filter by carbon price if needed (requires time series lookup)
    if carbon_price_min is not None or carbon_price_max is not None:
        filtered = []
        for s in scenarios:
            ts = db.query(NGFSScenarioTimeSeries).filter(
                NGFSScenarioTimeSeries.scenario_id == s.id,
                NGFSScenarioTimeSeries.parameter_name == "carbon_price",
                NGFSScenarioTimeSeries.year == 2050,
            ).first()
            if ts:
                if carbon_price_min and ts.value < carbon_price_min: continue
                if carbon_price_max and ts.value > carbon_price_max: continue
            filtered.append(s)
        scenarios = filtered

    return _wrap([ScenarioSummary.model_validate(s).model_dump() for s in scenarios],
                 {"total": len(scenarios)})


@router.post("/search")
def search_scenarios(body: dict, db: Session = Depends(get_db)):
    """Full-text search."""
    query = body.get("query", "").strip()
    if not query:
        return _wrap([])
    term = f"%{query}%"
    scs = db.query(NGFSScenario).filter(
        NGFSScenario.is_active.is_(True),
        (NGFSScenario.name.ilike(term) | NGFSScenario.description.ilike(term) |
         NGFSScenario.category.ilike(term))
    ).order_by(NGFSScenario.phase).all()
    return _wrap([ScenarioSummary.model_validate(s).model_dump() for s in scs],
                 {"total": len(scs), "query": query})


@router.get("/{scenario_id}")
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Full scenario details with parameters."""
    sc = db.get(NGFSScenario, scenario_id)
    if not sc:
        # Try by slug
        sc = db.query(NGFSScenario).filter(NGFSScenario.slug == scenario_id).first()
    if not sc:
        raise HTTPException(404, "Scenario not found")

    params = db.query(NGFSScenarioParameter).filter(
        NGFSScenarioParameter.scenario_id == sc.id
    ).all()

    data = ScenarioSummary.model_validate(sc).model_dump()
    data["key_assumptions"] = sc.key_assumptions
    data["policy_implications"] = sc.policy_implications
    data["parameters"] = [ParameterResponse.model_validate(p).model_dump() for p in params]
    return _wrap(data)


@router.get("/{scenario_id}/parameters")
def get_parameters(scenario_id: str, db: Session = Depends(get_db)):
    """Get all parameters with their time series."""
    sc = db.get(NGFSScenario, scenario_id)
    if not sc:
        raise HTTPException(404, "Scenario not found")

    params = db.query(NGFSScenarioParameter).filter(
        NGFSScenarioParameter.scenario_id == sc.id
    ).all()

    result = []
    for p in params:
        ts = db.query(NGFSScenarioTimeSeries).filter(
            NGFSScenarioTimeSeries.scenario_id == sc.id,
            NGFSScenarioTimeSeries.parameter_name == p.parameter_name,
        ).order_by(NGFSScenarioTimeSeries.year).all()

        result.append({
            **ParameterResponse.model_validate(p).model_dump(),
            "time_series": [{"year": t.year, "value": t.value, "is_interpolated": t.is_interpolated} for t in ts],
        })
    return _wrap(result)


@router.get("/{scenario_id}/time-series")
def get_time_series(
    scenario_id: str,
    parameter_name: Optional[str] = None,
    start_year: int = 2025,
    end_year: int = 2100,
    db: Session = Depends(get_db),
):
    """Get time series data for a scenario."""
    sc = db.get(NGFSScenario, scenario_id)
    if not sc:
        raise HTTPException(404, "Scenario not found")

    q = db.query(NGFSScenarioTimeSeries).filter(
        NGFSScenarioTimeSeries.scenario_id == sc.id,
        NGFSScenarioTimeSeries.year >= start_year,
        NGFSScenarioTimeSeries.year <= end_year,
    )
    if parameter_name:
        q = q.filter(NGFSScenarioTimeSeries.parameter_name == parameter_name)

    ts = q.order_by(NGFSScenarioTimeSeries.parameter_name, NGFSScenarioTimeSeries.year).all()

    # Group by parameter
    grouped = {}
    for t in ts:
        if t.parameter_name not in grouped:
            grouped[t.parameter_name] = []
        grouped[t.parameter_name].append({"year": t.year, "value": t.value, "is_interpolated": t.is_interpolated})

    return _wrap(grouped)


@router.post("/compare")
def compare_scenarios(body: CompareRequest, db: Session = Depends(get_db)):
    """Side-by-side comparison of selected scenarios."""
    scenarios = db.query(NGFSScenario).filter(
        NGFSScenario.id.in_(body.scenario_ids)
    ).all()
    if not scenarios:
        raise HTTPException(404, "No scenarios found")

    sc_map = {s.id: s for s in scenarios}
    result = {"scenarios": [], "metrics": {}}

    for sc in scenarios:
        result["scenarios"].append(ScenarioSummary.model_validate(sc).model_dump())

    for metric in body.metrics:
        metric_data = {"name": metric, "series": {}}
        for sc in scenarios:
            ts = db.query(NGFSScenarioTimeSeries).filter(
                NGFSScenarioTimeSeries.scenario_id == sc.id,
                NGFSScenarioTimeSeries.parameter_name == metric,
            ).order_by(NGFSScenarioTimeSeries.year).all()
            metric_data["series"][sc.name] = {str(t.year): t.value for t in ts}
        result["metrics"][metric] = metric_data

    return _wrap(result)


@router.post("/seed")
def seed_scenarios(db: Session = Depends(get_db)):
    """Seed all 24 NGFS scenarios."""
    from services.ngfs_seeder import seed_ngfs_scenarios
    return seed_ngfs_scenarios(db)
