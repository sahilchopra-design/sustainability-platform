"""
API routes for scenario management.

Provides endpoints for NGFS data sync, scenario CRUD, approval workflow,
versioning, and impact calculation.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional

from db.base import get_db
from db.models.scenario import ScenarioApprovalStatus, ScenarioSource, NGFSDataSource, Scenario
from schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioVersionResponse,
    ScenarioTemplateResponse,
    ScenarioImpactPreviewResponse,
    NGFSDataSourceResponse,
    ScenarioSubmitForApproval,
    ScenarioApprovalDecision,
    ScenarioForkRequest,
    ScenarioImpactPreviewRequest,
)
from services.ngfs_sync_service import NGFSSyncService
from services.scenario_builder_service import ScenarioBuilderService
from services.scenario_impact_service import ScenarioImpactService
from workers.tasks.ngfs_sync_tasks import sync_ngfs_data_task, calculate_scenario_impact_task

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


# ============================================================================
# NGFS Data Management
# ============================================================================

@router.get("/ngfs/sources", response_model=List[NGFSDataSourceResponse])
def get_ngfs_sources(db: Session = Depends(get_db)):
    """Get all NGFS data sources."""
    service = NGFSSyncService(db)
    sources = service.get_ngfs_sources()
    return sources


@router.post("/ngfs/sync")
def sync_ngfs_data(
    source_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Trigger NGFS data synchronization.
    
    If source_id is provided, sync that specific source.
    Otherwise, sync all sources.
    
    Returns immediately and processes in background.
    """
    if source_id:
        # Verify source exists
        service = NGFSSyncService(db)
        source = db.get(NGFSDataSource, source_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"NGFS source {source_id} not found")
        
        # Queue background task
        if background_tasks:
            background_tasks.add_task(sync_ngfs_data_task, source_id)
        else:
            # If no background tasks support, run synchronously
            result = sync_ngfs_data_task(source_id)
            return result
        
        return {"message": f"NGFS sync started for source {source_id}", "source_id": source_id}
    else:
        # Sync all sources (scheduled task)
        if background_tasks:
            from backend.workers.tasks.ngfs_sync_tasks import scheduled_ngfs_sync_task
            background_tasks.add_task(scheduled_ngfs_sync_task)
        
        return {"message": "NGFS sync started for all sources"}


# ============================================================================
# Scenario Templates
# ============================================================================

@router.get("/templates", response_model=List[ScenarioTemplateResponse])
def get_scenario_templates(db: Session = Depends(get_db)):
    """Get NGFS scenario templates for creating new scenarios."""
    service = ScenarioBuilderService(db)
    templates = service.get_ngfs_templates()
    
    # Convert to template response format
    return [
        ScenarioTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description or "",
            ngfs_scenario_type=t.ngfs_scenario_type,
            parameters=t.parameters,
            version=t.ngfs_version or "latest",
        )
        for t in templates
    ]


# ============================================================================
# Scenario CRUD
# ============================================================================

@router.get("", response_model=List[ScenarioResponse])
def list_scenarios(
    approval_status: Optional[ScenarioApprovalStatus] = None,
    source: Optional[ScenarioSource] = None,
    published_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    List scenarios with optional filters.
    
    - approval_status: Filter by approval status
    - source: Filter by source (ngfs, custom, hybrid)
    - published_only: Only return published scenarios
    """
    service = ScenarioBuilderService(db)
    scenarios = service.list_scenarios(
        approval_status=approval_status,
        source=source,
        published_only=published_only,
    )
    return scenarios


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(scenario: ScenarioCreate, db: Session = Depends(get_db)):
    """
    Create a new scenario.
    
    Scenarios start in DRAFT status and must be submitted for approval.
    """
    service = ScenarioBuilderService(db)
    try:
        new_scenario = service.create_scenario(scenario)
        return new_scenario
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Get scenario by ID."""
    service = ScenarioBuilderService(db)
    scenario = service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    return scenario


@router.patch("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: str,
    updates: ScenarioUpdate,
    updated_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Update scenario.
    
    Only DRAFT and REJECTED scenarios can be updated.
    Creates a new version if parameters are changed.
    """
    service = ScenarioBuilderService(db)
    try:
        updated = service.update_scenario(scenario_id, updates, updated_by)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Delete scenario."""
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    
    # Only allow deletion of draft scenarios
    if scenario.approval_status != ScenarioApprovalStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete scenario with status {scenario.approval_status}"
        )
    
    db.delete(scenario)
    db.commit()
    return None


# ============================================================================
# Scenario Operations
# ============================================================================

@router.post("/{scenario_id}/fork", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def fork_scenario(scenario_id: str, fork_request: ScenarioForkRequest, db: Session = Depends(get_db)):
    """
    Fork (copy) a scenario.
    
    Creates a new DRAFT scenario with copied parameters.
    Useful for creating variations of NGFS scenarios or existing custom scenarios.
    """
    service = ScenarioBuilderService(db)
    try:
        forked = service.fork_scenario(
            scenario_id,
            fork_request.new_name,
            fork_request.description,
            fork_request.created_by,
        )
        return forked
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{scenario_id}/publish", response_model=ScenarioResponse)
def publish_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """
    Publish an approved scenario.
    
    Makes the scenario available for use in analysis.
    """
    service = ScenarioBuilderService(db)
    try:
        published = service.publish_scenario(scenario_id)
        return published
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Approval Workflow
# ============================================================================

@router.post("/{scenario_id}/submit-for-approval", response_model=ScenarioResponse)
def submit_for_approval(
    scenario_id: str,
    submission: ScenarioSubmitForApproval,
    db: Session = Depends(get_db),
):
    """
    Submit scenario for approval.
    
    Changes status from DRAFT to PENDING_APPROVAL.
    """
    service = ScenarioBuilderService(db)
    try:
        submitted = service.submit_for_approval(
            scenario_id,
            submission.submitted_by,
            submission.notes,
        )
        return submitted
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{scenario_id}/approve", response_model=ScenarioResponse)
def approve_scenario(
    scenario_id: str,
    decision: ScenarioApprovalDecision,
    db: Session = Depends(get_db),
):
    """
    Approve or reject a scenario.
    
    Requires PENDING_APPROVAL status.
    """
    service = ScenarioBuilderService(db)
    try:
        if decision.approved:
            result = service.approve_scenario(
                scenario_id,
                decision.approved_by,
                decision.notes,
            )
        else:
            result = service.reject_scenario(
                scenario_id,
                decision.approved_by,
                decision.notes or "No reason provided",
            )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Versioning
# ============================================================================

@router.get("/{scenario_id}/versions", response_model=List[ScenarioVersionResponse])
def get_scenario_versions(scenario_id: str, db: Session = Depends(get_db)):
    """Get all versions of a scenario."""
    service = ScenarioBuilderService(db)
    
    # Verify scenario exists
    scenario = service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    
    versions = service.get_scenario_versions(scenario_id)
    return versions


# ============================================================================
# Impact Preview
# ============================================================================

@router.post("/{scenario_id}/preview", response_model=ScenarioImpactPreviewResponse)
def calculate_impact_preview(
    scenario_id: str,
    request: ScenarioImpactPreviewRequest,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Calculate scenario impact on a portfolio.
    
    Returns impact summary with expected loss changes.
    
    If background_tasks is available, calculation runs asynchronously.
    """
    # Verify scenario exists
    service_builder = ScenarioBuilderService(db)
    scenario = service_builder.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    
    # Verify portfolio exists (would check portfolio table in production)
    # For now, assume it exists
    
    # Calculate impact
    service_impact = ScenarioImpactService(db)
    
    try:
        # Use override parameters if provided
        parameters_override = request.parameters.dict() if request.parameters else None
        
        if background_tasks:
            # Queue for background processing
            background_tasks.add_task(
                calculate_scenario_impact_task,
                scenario_id,
                request.portfolio_id,
            )
            return {
                "message": "Impact calculation queued",
                "scenario_id": scenario_id,
                "portfolio_id": request.portfolio_id,
            }
        else:
            # Calculate synchronously
            preview = service_impact.calculate_impact(
                scenario_id,
                request.portfolio_id,
                parameters_override,
            )
            return preview
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{scenario_id}/preview/{portfolio_id}", response_model=ScenarioImpactPreviewResponse)
def get_impact_preview(scenario_id: str, portfolio_id: str, db: Session = Depends(get_db)):
    """Get cached impact preview for a scenario and portfolio."""
    from sqlalchemy import select
    from backend.models.scenario import ScenarioImpactPreview
    
    stmt = select(ScenarioImpactPreview).where(
        ScenarioImpactPreview.scenario_id == scenario_id,
        ScenarioImpactPreview.portfolio_id == portfolio_id,
    )
    preview = db.execute(stmt).scalar_one_or_none()
    
    if not preview:
        raise HTTPException(
            status_code=404,
            detail=f"No impact preview found for scenario {scenario_id} and portfolio {portfolio_id}"
        )
    
    return preview
