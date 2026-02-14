"""
Scenario Builder API — customize ANY hub scenario, run simulations, manage custom scenarios.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from db.base import get_db
from db.models.custom_builder import CustomScenario, ParameterCustomization, SimulationRun
from db.models.data_hub import DataHubScenario, DataHubTrajectory
from services.builder_engine import (
    calculate_impacts, run_monte_carlo, validate_customizations, interpolate_series,
)

router = APIRouter(prefix="/api/v1/scenario-builder", tags=["scenario-builder"])


# ---- Schemas ----

class CustomizationItem(BaseModel):
    variable_name: str
    region: str = "World"
    customized_values: dict  # {year_str: value}
    interpolation_method: str = "linear"
    reason: str = ""


class PreviewRequest(BaseModel):
    base_scenario_id: str
    customizations: List[CustomizationItem]


class CustomizeRequest(BaseModel):
    base_scenario_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    customizations: List[CustomizationItem]
    is_public: bool = False
    tags: List[str] = []


class SimulateRequest(BaseModel):
    custom_scenario_id: str
    simulation_type: str = "quick"  # quick, full, monte_carlo
    iterations: int = Field(1000, ge=100, le=10000)
    time_horizons: List[int] = [2030, 2050, 2100]


class ForkRequest(BaseModel):
    new_name: str
    additional_customizations: List[CustomizationItem] = []


class UpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    customizations: Optional[List[CustomizationItem]] = None


# ---- Helpers ----

def _get_base_trajectories(db: Session, scenario_id: str) -> list:
    """Get all trajectories for a base hub scenario."""
    trajs = db.query(DataHubTrajectory).filter(
        DataHubTrajectory.scenario_id == scenario_id
    ).all()
    return [{"variable_name": t.variable_name, "region": t.region,
             "time_series": t.time_series or {}, "unit": t.unit} for t in trajs]


def _scenario_response(cs, db):
    """Build response dict for a custom scenario."""
    base = db.get(DataHubScenario, cs.base_scenario_id) if cs.base_scenario_id else None
    custs = db.query(ParameterCustomization).filter(
        ParameterCustomization.custom_scenario_id == cs.id
    ).all()
    return {
        "id": cs.id,
        "name": cs.name,
        "description": cs.description,
        "is_public": cs.is_public,
        "is_fork": cs.is_fork,
        "tags": cs.tags or [],
        "base_scenario": {
            "id": base.id, "name": base.display_name or base.name,
            "source_name": base.source.name if base and base.source else None,
            "temperature_target": base.temperature_target if base else None,
        } if base else None,
        "customizations": [{
            "variable_name": c.variable_name, "region": c.region,
            "original_values": c.original_values, "customized_values": c.customized_values,
            "interpolation_method": c.interpolation_method,
        } for c in custs],
        "calculated_impacts": cs.calculated_impacts or {},
        "created_at": cs.created_at.isoformat() if cs.created_at else None,
        "updated_at": cs.updated_at.isoformat() if cs.updated_at else None,
    }


# ---- Routes ----

@router.post("/preview")
def preview_impacts(body: PreviewRequest, db: Session = Depends(get_db)):
    """Preview impacts of customizations without saving."""
    base = db.get(DataHubScenario, body.base_scenario_id)
    if not base:
        raise HTTPException(404, "Base scenario not found")

    base_trajs = _get_base_trajectories(db, body.base_scenario_id)
    custs = [c.model_dump() for c in body.customizations]
    impacts = calculate_impacts(base_trajs, custs)

    return {
        "base_scenario": {"id": base.id, "name": base.display_name or base.name},
        "impacts": impacts,
    }


@router.post("/customize", status_code=201)
def create_custom_scenario(body: CustomizeRequest, db: Session = Depends(get_db)):
    """Create and save a custom scenario from any hub scenario."""
    base = db.get(DataHubScenario, body.base_scenario_id)
    if not base:
        raise HTTPException(404, "Base scenario not found")

    base_trajs = _get_base_trajectories(db, body.base_scenario_id)

    # Calculate impacts
    custs = [c.model_dump() for c in body.customizations]
    impacts = calculate_impacts(base_trajs, custs)

    # Save custom scenario
    cs = CustomScenario(
        base_scenario_id=body.base_scenario_id,
        name=body.name, description=body.description,
        is_public=body.is_public, tags=body.tags,
        calculated_impacts=impacts,
    )
    db.add(cs)
    db.flush()

    # Save customizations
    for c in body.customizations:
        # Get original values
        orig = {}
        for bt in base_trajs:
            if bt["variable_name"] == c.variable_name and bt["region"] == c.region:
                orig = bt["time_series"]
                break

        db.add(ParameterCustomization(
            custom_scenario_id=cs.id,
            variable_name=c.variable_name, region=c.region,
            original_values=orig,
            customized_values=c.customized_values,
            interpolation_method=c.interpolation_method,
            reason=c.reason,
        ))

    db.commit()
    db.refresh(cs)
    return _scenario_response(cs, db)


@router.post("/calculate-impacts")
def calc_impacts(body: PreviewRequest, db: Session = Depends(get_db)):
    """Calculate full impacts for customizations."""
    base_trajs = _get_base_trajectories(db, body.base_scenario_id)
    if not base_trajs:
        raise HTTPException(404, "No trajectory data for base scenario")
    custs = [c.model_dump() for c in body.customizations]
    return calculate_impacts(base_trajs, custs)


@router.post("/validate")
def validate(body: PreviewRequest, db: Session = Depends(get_db)):
    """Validate customizations against constraints."""
    custs = [c.model_dump() for c in body.customizations]
    return validate_customizations(custs)


@router.post("/simulate")
def run_simulation(body: SimulateRequest, db: Session = Depends(get_db)):
    """Run Monte Carlo or quick simulation."""
    cs = db.get(CustomScenario, body.custom_scenario_id)
    if not cs:
        raise HTTPException(404, "Custom scenario not found")

    # Get base trajectories and customizations
    base_trajs = _get_base_trajectories(db, cs.base_scenario_id)
    custs = db.query(ParameterCustomization).filter(
        ParameterCustomization.custom_scenario_id == cs.id
    ).all()
    cust_dicts = [{"variable_name": c.variable_name, "region": c.region,
                   "customized_values": c.customized_values,
                   "interpolation_method": c.interpolation_method} for c in custs]

    # Create simulation run
    sim = SimulationRun(
        custom_scenario_id=cs.id,
        simulation_type=body.simulation_type,
        iterations=body.iterations,
        time_horizons=body.time_horizons,
        status="running",
    )
    db.add(sim)
    db.flush()

    try:
        if body.simulation_type == "monte_carlo":
            results = run_monte_carlo(base_trajs, cust_dicts, body.iterations)
        else:
            results = calculate_impacts(base_trajs, cust_dicts)

        sim.status = "completed"
        sim.results = results
        sim.completed_at = datetime.now(timezone.utc)
    except Exception as e:
        sim.status = "failed"
        sim.error_message = str(e)

    db.commit()
    db.refresh(sim)

    return {
        "simulation_id": sim.id,
        "status": sim.status,
        "simulation_type": sim.simulation_type,
        "results": sim.results,
    }


@router.get("/simulations/{sim_id}")
def get_simulation(sim_id: str, db: Session = Depends(get_db)):
    """Get simulation status and results."""
    sim = db.get(SimulationRun, sim_id)
    if not sim:
        raise HTTPException(404, "Simulation not found")
    return {
        "simulation_id": sim.id, "status": sim.status,
        "simulation_type": sim.simulation_type, "iterations": sim.iterations,
        "results": sim.results, "error_message": sim.error_message,
        "started_at": sim.started_at.isoformat() if sim.started_at else None,
        "completed_at": sim.completed_at.isoformat() if sim.completed_at else None,
    }


# ---- Custom Scenario CRUD ----

@router.get("/custom")
def list_custom_scenarios(
    user_id: str = "default_user",
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List custom scenarios."""
    q = db.query(CustomScenario)
    if is_public is not None:
        if is_public:
            q = q.filter(CustomScenario.is_public.is_(True))
        else:
            q = q.filter(CustomScenario.user_id == user_id)
    else:
        q = q.filter((CustomScenario.user_id == user_id) | (CustomScenario.is_public.is_(True)))

    return [_scenario_response(cs, db) for cs in q.order_by(CustomScenario.created_at.desc()).all()]


@router.get("/custom/{cs_id}")
def get_custom_scenario(cs_id: str, db: Session = Depends(get_db)):
    """Get full custom scenario."""
    cs = db.get(CustomScenario, cs_id)
    if not cs:
        raise HTTPException(404, "Custom scenario not found")
    return _scenario_response(cs, db)


@router.put("/custom/{cs_id}")
def update_custom_scenario(cs_id: str, body: UpdateRequest, db: Session = Depends(get_db)):
    """Update a custom scenario."""
    cs = db.get(CustomScenario, cs_id)
    if not cs:
        raise HTTPException(404, "Custom scenario not found")

    if body.name is not None:
        cs.name = body.name
    if body.description is not None:
        cs.description = body.description
    if body.is_public is not None:
        cs.is_public = body.is_public

    if body.customizations is not None:
        # Recalculate
        db.query(ParameterCustomization).filter(
            ParameterCustomization.custom_scenario_id == cs.id
        ).delete()
        base_trajs = _get_base_trajectories(db, cs.base_scenario_id)
        custs = [c.model_dump() for c in body.customizations]
        cs.calculated_impacts = calculate_impacts(base_trajs, custs)

        for c in body.customizations:
            orig = {}
            for bt in base_trajs:
                if bt["variable_name"] == c.variable_name and bt["region"] == c.region:
                    orig = bt["time_series"]
                    break
            db.add(ParameterCustomization(
                custom_scenario_id=cs.id,
                variable_name=c.variable_name, region=c.region,
                original_values=orig, customized_values=c.customized_values,
                interpolation_method=c.interpolation_method, reason=c.reason,
            ))

    db.commit()
    db.refresh(cs)
    return _scenario_response(cs, db)


@router.delete("/custom/{cs_id}", status_code=204)
def delete_custom_scenario(cs_id: str, db: Session = Depends(get_db)):
    """Delete a custom scenario."""
    cs = db.get(CustomScenario, cs_id)
    if not cs:
        raise HTTPException(404, "Custom scenario not found")
    db.delete(cs)
    db.commit()


@router.post("/custom/{cs_id}/fork", status_code=201)
def fork_custom_scenario(cs_id: str, body: ForkRequest, db: Session = Depends(get_db)):
    """Fork an existing custom scenario."""
    original = db.get(CustomScenario, cs_id)
    if not original:
        raise HTTPException(404, "Custom scenario not found")

    # Copy customizations
    orig_custs = db.query(ParameterCustomization).filter(
        ParameterCustomization.custom_scenario_id == cs_id
    ).all()

    forked = CustomScenario(
        base_scenario_id=original.base_scenario_id,
        name=body.new_name, description=f"Forked from: {original.name}",
        is_fork=True, forked_from_id=cs_id,
        tags=original.tags,
    )
    db.add(forked)
    db.flush()

    for oc in orig_custs:
        db.add(ParameterCustomization(
            custom_scenario_id=forked.id,
            variable_name=oc.variable_name, region=oc.region,
            original_values=oc.original_values,
            customized_values=oc.customized_values,
            interpolation_method=oc.interpolation_method,
        ))

    # Apply additional customizations
    if body.additional_customizations:
        for c in body.additional_customizations:
            existing = next((x for x in orig_custs if x.variable_name == c.variable_name and x.region == c.region), None)
            if existing:
                db.query(ParameterCustomization).filter(
                    ParameterCustomization.custom_scenario_id == forked.id,
                    ParameterCustomization.variable_name == c.variable_name,
                ).update({"customized_values": c.customized_values})
            else:
                db.add(ParameterCustomization(
                    custom_scenario_id=forked.id,
                    variable_name=c.variable_name, region=c.region,
                    customized_values=c.customized_values,
                    interpolation_method=c.interpolation_method,
                ))

    # Recalculate impacts
    base_trajs = _get_base_trajectories(db, forked.base_scenario_id)
    all_custs = db.query(ParameterCustomization).filter(
        ParameterCustomization.custom_scenario_id == forked.id
    ).all()
    cust_dicts = [{"variable_name": c.variable_name, "region": c.region,
                   "customized_values": c.customized_values} for c in all_custs]
    forked.calculated_impacts = calculate_impacts(base_trajs, cust_dicts)

    db.commit()
    db.refresh(forked)
    return _scenario_response(forked, db)


@router.get("/base-scenarios")
def list_base_scenarios(db: Session = Depends(get_db)):
    """List all available base scenarios from the hub for customization."""
    scenarios = db.query(DataHubScenario).filter(
        DataHubScenario.is_active.is_(True)
    ).order_by(DataHubScenario.name).limit(200).all()

    return [{
        "id": s.id, "name": s.display_name or s.name,
        "source_name": s.source.name if s.source else None,
        "category": s.category, "temperature_target": s.temperature_target,
        "trajectory_count": len(s.trajectories) if s.trajectories else 0,
        "variables": s.variables or [],
    } for s in scenarios]
