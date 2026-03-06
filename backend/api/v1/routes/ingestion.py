"""
Ingestion API — manage data source syncs, view job history, trigger runs.

Provides endpoints for:
  - Listing registered ingesters and their status
  - Triggering manual ingestion runs
  - Querying sync job history and logs
  - Scheduler status and upcoming runs
  - Data source stats
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.ingestion import DhDataSource, DhSyncJob
from api.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class TriggerRequest(BaseModel):
    source_id: str
    async_mode: bool = True


class TriggerAllRequest(BaseModel):
    only_enabled: bool = True
    async_mode: bool = True


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_manager():
    """Lazy import to avoid circular imports at module load."""
    from ingestion.manager import ingestion_manager
    return ingestion_manager


def _get_scheduler():
    from ingestion.scheduler import get_scheduler
    return get_scheduler()


# ── Ingester Registry ────────────────────────────────────────────────────────

@router.get("/ingesters", summary="List all registered ingesters")
def list_ingesters(
    _user=Depends(get_current_user),
):
    """Return all registered ingesters with their status and schedule."""
    manager = _get_manager()
    return {
        "ingesters": manager.list_ingesters(),
        "total": len(manager.registered_sources),
    }


@router.get("/ingesters/{source_id}", summary="Get ingester status")
def get_ingester_status(
    source_id: str,
    _user=Depends(get_current_user),
):
    """Get detailed status for a specific ingester."""
    manager = _get_manager()
    status = manager.get_status(source_id)
    if "error" in status:
        raise HTTPException(404, status["error"])
    return status


# ── Trigger Ingestion ────────────────────────────────────────────────────────

@router.post("/trigger", summary="Trigger ingestion for a specific source")
def trigger_ingestion(
    body: TriggerRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "data_engineer")),
):
    """
    Trigger a manual ingestion run for one data source.

    Requires admin or data_engineer role.
    If async_mode=True (default), runs in background and returns immediately.
    """
    manager = _get_manager()

    if body.source_id not in manager.registered_sources:
        raise HTTPException(404, f"No ingester registered for source: {body.source_id}")

    if body.async_mode:
        manager.run_source_async(body.source_id, triggered_by="manual_api")
        return {
            "message": f"Ingestion started for {body.source_id}",
            "source_id": body.source_id,
            "mode": "async",
        }
    else:
        result = manager.run_source(body.source_id, db, triggered_by="manual_api")
        return {
            "message": f"Ingestion completed for {body.source_id}",
            "result": result.to_dict(),
        }


@router.post("/trigger-all", summary="Trigger ingestion for all sources")
def trigger_all_ingestion(
    body: TriggerAllRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    """
    Trigger ingestion for all registered sources.

    Admin only. If only_enabled=True, skips sources with sync_enabled=False.
    """
    manager = _get_manager()

    if body.async_mode:
        for sid in manager.registered_sources:
            if body.only_enabled:
                source = db.query(DhDataSource).filter(DhDataSource.id == sid).first()
                if source and not source.sync_enabled:
                    continue
            manager.run_source_async(sid, triggered_by="manual_api_batch")
        return {
            "message": "Batch ingestion started",
            "sources_triggered": len(manager.registered_sources),
            "mode": "async",
        }
    else:
        results = manager.run_all(db, triggered_by="manual_api_batch", only_enabled=body.only_enabled)
        return {
            "message": "Batch ingestion completed",
            "results": [r.to_dict() for r in results],
        }


# ── Currently Running ────────────────────────────────────────────────────────

@router.get("/running", summary="List currently running ingestion jobs")
def get_running_jobs(
    _user=Depends(get_current_user),
):
    """Return source_ids of ingesters currently running."""
    manager = _get_manager()
    running = manager.get_running()
    return {"running": running, "count": len(running)}


# ── Job History ──────────────────────────────────────────────────────────────

@router.get("/jobs", summary="Query sync job history")
def list_sync_jobs(
    source_id: Optional[str] = Query(None, description="Filter by source"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Query the dh_sync_jobs table for ingestion run history."""
    from ingestion.manager import IngestionManager
    return IngestionManager.get_job_history(db, source_id=source_id, status=status,
                                            limit=limit, offset=offset)


@router.get("/jobs/{job_id}", summary="Get sync job detail")
def get_sync_job(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Get full details of a specific sync job including log output."""
    job = db.query(DhSyncJob).filter(DhSyncJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Sync job not found")

    return {
        "id": job.id,
        "source_id": job.source_id,
        "triggered_by": job.triggered_by,
        "status": job.status,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": job.duration_seconds,
        "rows_fetched": job.rows_fetched,
        "rows_inserted": job.rows_inserted,
        "rows_updated": job.rows_updated,
        "rows_skipped": job.rows_skipped,
        "rows_failed": job.rows_failed,
        "error_message": job.error_message,
        "error_detail": job.error_detail,
        "validation_errors": job.validation_errors,
        "log_output": job.log_output,
    }


# ── Scheduler Status ─────────────────────────────────────────────────────────

@router.get("/scheduler", summary="Get scheduler status and scheduled jobs")
def get_scheduler_status(
    _user=Depends(get_current_user),
):
    """Return scheduler status and list of upcoming scheduled runs."""
    scheduler = _get_scheduler()
    return {
        "available": scheduler.is_available,
        "running": scheduler.is_running,
        "scheduled_jobs": scheduler.list_jobs() if scheduler.is_running else [],
        "next_runs": scheduler.get_next_runs() if scheduler.is_running else [],
    }


# ── Data Source Stats ────────────────────────────────────────────────────────

@router.get("/stats", summary="Ingestion statistics")
def get_ingestion_stats(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Aggregate ingestion statistics across all sources."""
    from ingestion.manager import IngestionManager
    return IngestionManager.get_source_stats(db)


# ── Data Sources (from dh_data_sources) ──────────────────────────────────────

@router.get("/sources", summary="List all data sources from registry")
def list_data_sources(
    category: Optional[str] = Query(None),
    sync_enabled: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Query the dh_data_sources registry with optional filters."""
    q = db.query(DhDataSource)
    if category:
        q = q.filter(DhDataSource.category == category)
    if sync_enabled is not None:
        q = q.filter(DhDataSource.sync_enabled == sync_enabled)

    total = q.count()
    sources = q.order_by(DhDataSource.name).offset(offset).limit(limit).all()

    return {
        "total": total,
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "sub_category": s.sub_category,
                "access_type": s.access_type,
                "sync_enabled": s.sync_enabled,
                "sync_schedule": s.sync_schedule,
                "last_synced_at": s.last_synced_at.isoformat() if s.last_synced_at else None,
                "last_sync_status": s.last_sync_status,
                "priority": s.priority,
                "quality_rating": s.quality_rating,
                "assessment_score": s.assessment_score,
            }
            for s in sources
        ],
    }


@router.get("/sources/{source_id}", summary="Get data source detail")
def get_data_source(
    source_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Get full details of a data source from the registry."""
    source = db.query(DhDataSource).filter(DhDataSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")

    return {
        "id": source.id,
        "name": source.name,
        "category": source.category,
        "sub_category": source.sub_category,
        "description": source.description,
        "rationale": source.rationale,
        "access_type": source.access_type,
        "base_url": source.base_url,
        "auth_method": source.auth_method,
        "docs_url": source.docs_url,
        "data_format": source.data_format,
        "update_freq": source.update_freq,
        "geographic": source.geographic,
        "quality_rating": source.quality_rating,
        "cost": source.cost,
        "rate_limit": source.rate_limit,
        "batch": source.batch,
        "status": source.status,
        "priority": source.priority,
        "assessment_score": source.assessment_score,
        "sync_enabled": source.sync_enabled,
        "sync_schedule": source.sync_schedule,
        "last_synced_at": source.last_synced_at.isoformat() if source.last_synced_at else None,
        "last_sync_status": source.last_sync_status,
        "last_sync_error": source.last_sync_error,
    }


@router.patch("/sources/{source_id}/sync-config", summary="Update source sync configuration")
def update_sync_config(
    source_id: str,
    sync_enabled: Optional[bool] = None,
    sync_schedule: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "data_engineer")),
):
    """Update the sync configuration for a data source."""
    source = db.query(DhDataSource).filter(DhDataSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")

    if sync_enabled is not None:
        source.sync_enabled = sync_enabled
    if sync_schedule is not None:
        source.sync_schedule = sync_schedule

    db.commit()
    db.refresh(source)

    return {
        "id": source.id,
        "name": source.name,
        "sync_enabled": source.sync_enabled,
        "sync_schedule": source.sync_schedule,
        "message": "Sync configuration updated",
    }
