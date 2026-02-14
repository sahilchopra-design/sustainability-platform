"""
Sub-Parameter Analysis API — sensitivity, what-if, attribution, interactions, visualization.
Works with ALL hub scenarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from db.base import get_db
from db.models.data_hub import DataHubScenario, DataHubTrajectory
from services.sub_parameter_engine import (
    run_sensitivity_analysis, run_what_if, run_attribution,
    run_interaction_analysis, get_visualization_tornado, get_visualization_waterfall,
    ANALYZABLE_PARAMS,
)

router = APIRouter(prefix="/api/v1/sub-parameter", tags=["sub-parameter"])


def _get_trajs(db: Session, scenario_id: str) -> list:
    sc = db.get(DataHubScenario, scenario_id)
    if not sc:
        raise HTTPException(404, "Scenario not found")
    trajs = db.query(DataHubTrajectory).filter(DataHubTrajectory.scenario_id == scenario_id).all()
    return [{"variable_name": t.variable_name, "region": t.region, "time_series": t.time_series or {}, "unit": t.unit} for t in trajs]


# ---- Schemas ----

class SensitivityRequest(BaseModel):
    scenario_id: str
    target_metric: str = "temperature"
    parameters: List[str] = []
    variation_range: float = Field(0.2, ge=0.05, le=0.5)
    analysis_type: str = "tornado"


class WhatIfChange(BaseModel):
    parameter: str
    change_type: str = "relative"  # absolute, relative
    change_value: float = 0
    apply_year: int = 2050


class WhatIfRequest(BaseModel):
    base_scenario_id: str
    changes: List[WhatIfChange]


class WhatIfBatchRequest(BaseModel):
    base_scenario_id: str
    change_sets: List[List[WhatIfChange]]


class AttributionRequest(BaseModel):
    scenario_id: str
    outcome_metric: str = "temperature"


class InteractionMatrixRequest(BaseModel):
    scenario_id: str
    parameters: List[str] = []
    target_outcome: str = "temperature"


# ---- Routes ----

@router.get("/parameters")
def list_analyzable_parameters():
    """List all parameters available for sub-parameter analysis."""
    return {"parameters": ANALYZABLE_PARAMS}


@router.post("/sensitivity-analysis")
def sensitivity_analysis(body: SensitivityRequest, db: Session = Depends(get_db)):
    """Run sensitivity analysis (tornado/spider) on a scenario."""
    trajs = _get_trajs(db, body.scenario_id)
    return run_sensitivity_analysis(
        trajs, body.target_metric, body.parameters or None,
        body.variation_range, body.analysis_type,
    )


@router.post("/what-if")
def what_if_analysis(body: WhatIfRequest, db: Session = Depends(get_db)):
    """Run what-if analysis comparing baseline vs modified scenario."""
    trajs = _get_trajs(db, body.base_scenario_id)
    changes = [c.model_dump() for c in body.changes]
    return run_what_if(trajs, changes)


@router.post("/what-if/batch")
def what_if_batch(body: WhatIfBatchRequest, db: Session = Depends(get_db)):
    """Run multiple what-if change sets and compare."""
    trajs = _get_trajs(db, body.base_scenario_id)
    results = []
    for i, change_set in enumerate(body.change_sets):
        changes = [c.model_dump() for c in change_set]
        result = run_what_if(trajs, changes)
        result["set_index"] = i
        results.append(result)
    return {"base_scenario_id": body.base_scenario_id, "results": results}


@router.post("/attribution")
def attribution_analysis(body: AttributionRequest, db: Session = Depends(get_db)):
    """Run Shapley-inspired attribution analysis."""
    trajs = _get_trajs(db, body.scenario_id)
    return run_attribution(trajs, body.outcome_metric)


@router.get("/interactions/{scenario_id}")
def interaction_analysis(
    scenario_id: str,
    parameter_set: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Analyze pairwise parameter interactions."""
    trajs = _get_trajs(db, scenario_id)
    params = parameter_set.split(",") if parameter_set else None
    return run_interaction_analysis(trajs, params)


@router.post("/interaction-matrix")
def interaction_matrix(body: InteractionMatrixRequest, db: Session = Depends(get_db)):
    """Full interaction matrix for parameter pairs."""
    trajs = _get_trajs(db, body.scenario_id)
    return run_interaction_analysis(trajs, body.parameters or None)


# ---- Visualization Endpoints ----

@router.get("/visualization/tornado/{scenario_id}")
def viz_tornado(
    scenario_id: str,
    target_metric: str = "temperature",
    top_n: int = Query(10, ge=3, le=20),
    db: Session = Depends(get_db),
):
    """Tornado chart data."""
    trajs = _get_trajs(db, scenario_id)
    return get_visualization_tornado(trajs, target_metric, top_n)


@router.get("/visualization/waterfall/{scenario_id}")
def viz_waterfall(scenario_id: str, db: Session = Depends(get_db)):
    """Waterfall chart data (baseline → final with each parameter's delta)."""
    trajs = _get_trajs(db, scenario_id)
    # Use top 5 parameters as default customizations (10% increase each)
    custs = []
    for pdef in ANALYZABLE_PARAMS[:5]:
        matching = [t for t in trajs if pdef["name"].lower() in t["variable_name"].lower()]
        if matching:
            t = matching[0]
            ts = t["time_series"]
            high = {y: round(v * 1.1, 4) for y, v in ts.items() if isinstance(v, (int, float))}
            custs.append({"variable_name": t["variable_name"], "region": t.get("region", "World"), "customized_values": high})
    return get_visualization_waterfall(trajs, custs)
