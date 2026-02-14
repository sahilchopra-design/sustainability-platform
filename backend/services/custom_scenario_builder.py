"""
Custom Scenario Builder — blend trajectories from multiple source scenarios.
Creates new hub_scenarios with lineage tracking.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from db.models.data_hub import DataHubScenario, DataHubTrajectory, DataHubSource


def build_custom_scenario(
    db: Session,
    name: str,
    description: str,
    base_scenario_id: str,
    overrides: List[Dict[str, Any]],
    created_by: str = "default_user",
) -> Dict[str, Any]:
    """
    Create a custom scenario by blending trajectories.

    Args:
        name: Name for the custom scenario
        description: Description
        base_scenario_id: The base scenario to start from
        overrides: List of {"variable": str, "region": str, "source_scenario_id": str}
            — take that variable+region trajectory from source_scenario_id instead of base
        created_by: User ID

    Returns:
        The created custom scenario dict
    """
    base = db.get(DataHubScenario, base_scenario_id)
    if not base:
        raise ValueError("Base scenario not found")

    # Find or create a "Custom" source
    custom_source = db.query(DataHubSource).filter(DataHubSource.short_name == "custom").first()
    if not custom_source:
        custom_source = DataHubSource(
            name="Custom Scenarios",
            short_name="custom",
            organization="User-Created",
            description="User-created blended scenarios.",
            tier="tier_1",
            is_active=True,
        )
        db.add(custom_source)
        db.commit()
        db.refresh(custom_source)

    # Create the new scenario
    sc_id = str(uuid.uuid4())
    lineage = {
        "base_scenario_id": base_scenario_id,
        "base_scenario_name": base.display_name or base.name,
        "overrides": overrides,
    }
    new_sc = DataHubScenario(
        id=sc_id,
        source_id=custom_source.id,
        external_id=f"custom|{sc_id[:8]}",
        name=name,
        display_name=name,
        description=description,
        category="Custom",
        model="Blended",
        version="custom",
        tags=["custom", "blended"],
        temperature_target=base.temperature_target,
        carbon_neutral_year=base.carbon_neutral_year,
        time_horizon_start=base.time_horizon_start,
        time_horizon_end=base.time_horizon_end,
        regions=base.regions,
        variables=base.variables,
        parameters=lineage,
        is_active=True,
    )
    db.add(new_sc)
    db.commit()

    # Copy base trajectories
    base_trajs = db.query(DataHubTrajectory).filter(
        DataHubTrajectory.scenario_id == base_scenario_id
    ).all()

    # Build override lookup: (variable, region) -> source_scenario_id
    override_map = {}
    for ov in overrides:
        key = (ov["variable"], ov.get("region", "World"))
        override_map[key] = ov["source_scenario_id"]

    new_trajs = []
    variables_set = set()
    for bt in base_trajs:
        key = (bt.variable_name, bt.region)
        src_id = override_map.get(key)

        if src_id:
            # Use override trajectory
            override_traj = db.query(DataHubTrajectory).filter(
                DataHubTrajectory.scenario_id == src_id,
                DataHubTrajectory.variable_name == bt.variable_name,
                DataHubTrajectory.region == bt.region,
            ).first()
            if override_traj:
                ts = override_traj.time_series
                unit = override_traj.unit
                meta = {"source": "override", "from_scenario": src_id}
            else:
                ts = bt.time_series
                unit = bt.unit
                meta = {"source": "base", "override_not_found": True}
        else:
            ts = bt.time_series
            unit = bt.unit
            meta = {"source": "base"}

        variables_set.add(bt.variable_name)
        new_trajs.append(DataHubTrajectory(
            scenario_id=sc_id,
            variable_name=bt.variable_name,
            variable_code=bt.variable_code,
            unit=unit,
            region=bt.region,
            sector=bt.sector,
            time_series=ts,
            data_quality_score=3,
            interpolation_method="blended",
            metadata_info=meta,
        ))

    db.bulk_save_objects(new_trajs)

    # Update scenario metadata
    new_sc.variables = list(variables_set)
    db.commit()
    db.refresh(new_sc)

    # Update custom source counts
    custom_source.scenario_count = db.query(DataHubScenario).filter(
        DataHubScenario.source_id == custom_source.id
    ).count()
    custom_source.trajectory_count = len(new_trajs)
    db.commit()

    return {
        "id": sc_id,
        "name": name,
        "description": description,
        "base_scenario": base.display_name or base.name,
        "overrides_applied": len([o for o in overrides if override_map.get((o["variable"], o.get("region", "World")))]),
        "total_trajectories": len(new_trajs),
        "lineage": lineage,
    }
