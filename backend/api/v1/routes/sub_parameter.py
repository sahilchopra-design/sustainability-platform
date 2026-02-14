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
    run_elasticity_analysis, run_partial_correlation, run_ols_attribution,
    run_enhanced_shapley, get_key_drivers,
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



# ============================================================================
# Enhanced Calculation Methods
# ============================================================================

class ElasticityRequest(BaseModel):
    scenario_id: str
    target_metric: str = "temperature"
    parameters: List[str] = []
    delta_pct: float = Field(1.0, ge=0.1, le=10.0)


@router.post("/elasticity")
def elasticity_analysis(body: ElasticityRequest, db: Session = Depends(get_db)):
    """Elasticity analysis: % outcome change per 1% parameter change."""
    trajs = _get_trajs(db, body.scenario_id)
    return run_elasticity_analysis(trajs, body.target_metric, body.parameters or None, body.delta_pct)


@router.post("/partial-correlation")
def partial_corr(body: SensitivityRequest, db: Session = Depends(get_db)):
    """Partial correlation controlling for other parameters."""
    trajs = _get_trajs(db, body.scenario_id)
    return run_partial_correlation(trajs, body.target_metric, body.parameters or None)


@router.post("/ols-attribution")
def ols_attribution(body: SensitivityRequest, db: Session = Depends(get_db)):
    """OLS regression-based attribution with R-squared."""
    trajs = _get_trajs(db, body.scenario_id)
    return run_ols_attribution(trajs, body.target_metric, body.parameters or None)


class ShapleyRequest(BaseModel):
    scenario_id: str
    target_metric: str = "temperature"
    parameters: List[str] = []
    n_permutations: int = Field(20, ge=5, le=100)


@router.post("/shapley")
def shapley_attribution(body: ShapleyRequest, db: Session = Depends(get_db)):
    """Enhanced Shapley value attribution with permutation sampling."""
    trajs = _get_trajs(db, body.scenario_id)
    return run_enhanced_shapley(trajs, body.target_metric, body.parameters or None, body.n_permutations)


# ============================================================================
# Export
# ============================================================================

class ExportRequest(BaseModel):
    analyses: List[dict]
    format: str = "excel"  # excel, pdf, json


@router.post("/export")
def export_analyses(body: ExportRequest, db: Session = Depends(get_db)):
    """Export analysis results to Excel/PDF/JSON."""
    from services.analysis_export import export_analysis_excel, export_analysis_pdf, export_analysis_json

    if body.format == "pdf":
        filename = export_analysis_pdf(body.analyses)
    elif body.format == "json":
        filename = export_analysis_json(body.analyses)
    else:
        filename = export_analysis_excel(body.analyses)

    return {
        "filename": filename,
        "format": body.format,
        "download_url": f"/api/v1/analysis/reports/download/{filename}",
    }


# ============================================================================
# Scenario Builder Integration
# ============================================================================

@router.post("/custom-scenario/{cs_id}/analysis")
def analyze_custom_scenario(cs_id: str, db: Session = Depends(get_db)):
    """Auto-run full analysis on a custom scenario's base trajectories."""
    from db.models.custom_builder import CustomScenario
    cs = db.get(CustomScenario, cs_id)
    if not cs or not cs.base_scenario_id:
        raise HTTPException(404, "Custom scenario not found")

    trajs = _get_trajs(db, cs.base_scenario_id)
    sensitivity = run_sensitivity_analysis(trajs)
    elasticity = run_elasticity_analysis(trajs)
    attribution = run_attribution(trajs)

    return {
        "custom_scenario_id": cs_id,
        "base_scenario_id": cs.base_scenario_id,
        "sensitivity": sensitivity,
        "elasticity": elasticity,
        "attribution": attribution,
    }


@router.get("/custom-scenario/{cs_id}/key-drivers")
def custom_key_drivers(cs_id: str, db: Session = Depends(get_db)):
    """Top 5 parameters driving a custom scenario's outcomes."""
    from db.models.custom_builder import CustomScenario
    cs = db.get(CustomScenario, cs_id)
    if not cs or not cs.base_scenario_id:
        raise HTTPException(404, "Custom scenario not found")

    trajs = _get_trajs(db, cs.base_scenario_id)
    drivers = get_key_drivers(trajs, top_n=5)
    return {"custom_scenario_id": cs_id, "key_drivers": drivers}
