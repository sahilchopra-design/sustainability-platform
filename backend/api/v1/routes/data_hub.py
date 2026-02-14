"""
API routes for the Universal Scenario Data Hub.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from db.base import get_db
from services.data_hub_service import DataHubService
from services.sync_orchestrator import ScenarioSyncOrchestrator
from schemas.data_hub import (
    DataHubSourceResponse, DataHubSourceCreate,
    DataHubScenarioResponse, DataHubScenarioSearch,
    DataHubTrajectoryResponse, TrajectoryQuery,
    DataHubComparisonCreate, DataHubComparisonResponse,
    DataHubSyncLogResponse, SyncTriggerRequest,
    DataHubFavoriteCreate, DataHubFavoriteResponse,
    DataHubStats,
)

router = APIRouter(prefix="/api/v1/data-hub", tags=["data-hub"])


def _scenario_to_response(sc) -> DataHubScenarioResponse:
    """Convert a DataHubScenario ORM object to response schema."""
    traj_count = len(sc.trajectories) if sc.trajectories else 0
    return DataHubScenarioResponse(
        id=sc.id,
        source_id=sc.source_id,
        source_name=sc.source.name if sc.source else None,
        external_id=sc.external_id,
        name=sc.name,
        display_name=sc.display_name,
        description=sc.description,
        category=sc.category,
        model=sc.model,
        version=sc.version,
        tags=sc.tags or [],
        temperature_target=sc.temperature_target,
        carbon_neutral_year=sc.carbon_neutral_year,
        time_horizon_start=sc.time_horizon_start,
        time_horizon_end=sc.time_horizon_end,
        regions=sc.regions or [],
        variables=sc.variables or [],
        trajectory_count=traj_count,
        is_active=sc.is_active,
        created_at=sc.created_at,
    )


# ============================================================================
# Stats / Overview
# ============================================================================

@router.get("/stats", response_model=DataHubStats)
def get_hub_stats(db: Session = Depends(get_db)):
    """Get overall Data Hub statistics."""
    svc = DataHubService(db)
    return svc.get_stats()


# ============================================================================
# Sources
# ============================================================================

@router.get("/sources", response_model=List[DataHubSourceResponse])
def list_sources(active_only: bool = False, db: Session = Depends(get_db)):
    """List all scenario data sources."""
    svc = DataHubService(db)
    return svc.list_sources(active_only=active_only)


@router.get("/sources/{source_id}", response_model=DataHubSourceResponse)
def get_source(source_id: str, db: Session = Depends(get_db)):
    """Get a single source by ID."""
    svc = DataHubService(db)
    src = svc.get_source(source_id)
    if not src:
        raise HTTPException(404, "Source not found")
    return src


@router.post("/sources", response_model=DataHubSourceResponse, status_code=201)
def create_source(body: DataHubSourceCreate, db: Session = Depends(get_db)):
    """Create a new source."""
    svc = DataHubService(db)
    return svc.create_source(body.model_dump())


@router.post("/sources/seed")
def seed_sources(db: Session = Depends(get_db)):
    """Seed Tier 1 data sources (NGFS, IPCC, IEA, IRENA)."""
    orch = ScenarioSyncOrchestrator(db)
    created = orch.seed_sources()
    return {"message": f"Seeded {created} new source(s)", "created": created}


# ============================================================================
# Sync
# ============================================================================

@router.post("/sources/{source_id}/sync")
def sync_source(source_id: str, db: Session = Depends(get_db)):
    """Trigger sync for a single source."""
    orch = ScenarioSyncOrchestrator(db)
    try:
        result = orch.sync_source(source_id)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Sync failed: {e}")


@router.post("/sync-all")
def sync_all_sources(
    include_real: bool = Query(True, description="Include real IIASA data sources (slower)"),
    db: Session = Depends(get_db),
):
    """Sync all active sources. Set include_real=false for fast synthetic-only sync."""
    orch = ScenarioSyncOrchestrator(db)
    results = orch.sync_all(include_real_data=include_real)
    return {"results": results}


@router.post("/sync-synthetic")
def sync_synthetic_only(db: Session = Depends(get_db)):
    """Sync only synthetic data sources (fast, no network calls)."""
    orch = ScenarioSyncOrchestrator(db)
    results = orch.sync_synthetic_only()
    return {"results": results}


@router.get("/sync-logs", response_model=List[DataHubSyncLogResponse])
def get_sync_logs(
    source_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get sync history logs."""
    svc = DataHubService(db)
    return svc.get_sync_logs(source_id=source_id, limit=limit)


# ============================================================================
# Scenarios
# ============================================================================

@router.get("/scenarios", response_model=dict)
def list_scenarios(
    source_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List hub scenarios with optional filters."""
    svc = DataHubService(db)
    rows, total = svc.list_scenarios(source_id=source_id, category=category, limit=limit, offset=offset)
    scenarios_out = [_scenario_to_response(sc) for sc in rows]
    return {"scenarios": scenarios_out, "total": total, "limit": limit, "offset": offset}


@router.post("/scenarios/search", response_model=dict)
def search_scenarios(body: DataHubScenarioSearch, db: Session = Depends(get_db)):
    """Full-text search on hub scenarios."""
    svc = DataHubService(db)
    rows, total = svc.search_scenarios(body.model_dump())
    scenarios_out = [_scenario_to_response(sc) for sc in rows]
    return {"scenarios": scenarios_out, "total": total}


@router.get("/scenarios/{scenario_id}", response_model=DataHubScenarioResponse)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Get a single hub scenario."""
    svc = DataHubService(db)
    sc = svc.get_scenario(scenario_id)
    if not sc:
        raise HTTPException(404, "Scenario not found")
    return _scenario_to_response(sc)


# ============================================================================
# Trajectories
# ============================================================================

@router.get("/scenarios/{scenario_id}/trajectories", response_model=List[DataHubTrajectoryResponse])
def get_scenario_trajectories(
    scenario_id: str,
    variable: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get trajectories for a scenario, optionally filtered."""
    svc = DataHubService(db)
    sc = svc.get_scenario(scenario_id)
    if not sc:
        raise HTTPException(404, "Scenario not found")
    return svc.get_trajectories(scenario_id=scenario_id, variable_name=variable, region=region)


@router.post("/trajectories/query", response_model=List[DataHubTrajectoryResponse])
def query_trajectories(body: TrajectoryQuery, db: Session = Depends(get_db)):
    """Query trajectories across multiple scenarios."""
    svc = DataHubService(db)
    results = []
    for sid in body.scenario_ids:
        for var in (body.variable_names or [None]):
            for reg in (body.regions or [None]):
                results.extend(svc.get_trajectories(scenario_id=sid, variable_name=var, region=reg))
    return results


# ============================================================================
# Comparisons
# ============================================================================

@router.get("/comparisons", response_model=List[DataHubComparisonResponse])
def list_comparisons(db: Session = Depends(get_db)):
    """List saved scenario comparisons."""
    svc = DataHubService(db)
    return svc.list_comparisons()


@router.post("/comparisons", response_model=DataHubComparisonResponse, status_code=201)
def create_comparison(body: DataHubComparisonCreate, db: Session = Depends(get_db)):
    """Save a new scenario comparison."""
    svc = DataHubService(db)
    return svc.create_comparison(body.model_dump())


@router.get("/comparisons/{comparison_id}", response_model=DataHubComparisonResponse)
def get_comparison(comparison_id: str, db: Session = Depends(get_db)):
    """Get a saved comparison."""
    svc = DataHubService(db)
    comp = svc.get_comparison(comparison_id)
    if not comp:
        raise HTTPException(404, "Comparison not found")
    return comp


@router.delete("/comparisons/{comparison_id}", status_code=204)
def delete_comparison(comparison_id: str, db: Session = Depends(get_db)):
    """Delete a saved comparison."""
    svc = DataHubService(db)
    if not svc.delete_comparison(comparison_id):
        raise HTTPException(404, "Comparison not found")


# ============================================================================
# Favorites
# ============================================================================

@router.get("/favorites", response_model=List[DataHubFavoriteResponse])
def list_favorites(user_id: str = "default_user", db: Session = Depends(get_db)):
    """List user's favorite scenarios."""
    svc = DataHubService(db)
    return svc.list_favorites(user_id)


@router.post("/favorites", response_model=DataHubFavoriteResponse, status_code=201)
def add_favorite(body: DataHubFavoriteCreate, db: Session = Depends(get_db)):
    """Add a scenario to favorites."""
    svc = DataHubService(db)
    return svc.add_favorite(body.model_dump())


@router.delete("/favorites/{favorite_id}", status_code=204)
def remove_favorite(favorite_id: str, db: Session = Depends(get_db)):
    """Remove a favorite."""
    svc = DataHubService(db)
    if not svc.remove_favorite(favorite_id):
        raise HTTPException(404, "Favorite not found")



# ============================================================================
# Analytics
# ============================================================================

@router.get("/analytics/coverage")
def get_coverage_analytics(db: Session = Depends(get_db)):
    """Coverage analytics — sources, scenarios, variables by tier/category."""
    svc = DataHubService(db)
    return svc.get_coverage_analytics()


@router.get("/analytics/temperature-range")
def get_temperature_range(db: Session = Depends(get_db)):
    """Temperature target distribution across all scenarios."""
    svc = DataHubService(db)
    return svc.get_temperature_analytics()


@router.get("/analytics/carbon-price-range")
def get_carbon_price_range(db: Session = Depends(get_db)):
    """Carbon price trajectory summary across scenarios."""
    svc = DataHubService(db)
    return svc.get_carbon_price_analytics()


@router.get("/trajectories/available-variables")
def get_available_variables(db: Session = Depends(get_db)):
    """List all unique variable names across all trajectories."""
    svc = DataHubService(db)
    return svc.get_available_variables()
