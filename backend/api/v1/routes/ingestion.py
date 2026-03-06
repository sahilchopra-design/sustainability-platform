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
from db.models.ingestion import DhDataSource, DhSyncJob, DhApplicationKpi, DhSourceField, DhKpiMapping
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


# ══════════════════════════════════════════════════════════════════════════════
#  DATA MAPPING UI — KPIs, Source Fields, Mappings CRUD
# ══════════════════════════════════════════════════════════════════════════════


# ── Application KPIs ────────────────────────────────────────────────────────

@router.get("/kpis", summary="List application KPIs")
def list_kpis(
    category: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Filter by target module slug"),
    is_required: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search in name/description"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """List application KPIs with optional category/module filters."""
    from sqlalchemy import func, cast, String as SA_String
    q = db.query(DhApplicationKpi)

    if category:
        q = q.filter(DhApplicationKpi.category == category)
    if is_required is not None:
        q = q.filter(DhApplicationKpi.is_required == is_required)
    if search:
        q = q.filter(
            DhApplicationKpi.name.ilike(f"%{search}%")
            | DhApplicationKpi.description.ilike(f"%{search}%")
        )
    # Module filter — target_modules is a JSON array
    if module:
        q = q.filter(
            cast(DhApplicationKpi.target_modules, SA_String).ilike(f"%{module}%")
        )

    total = q.count()
    kpis = q.order_by(DhApplicationKpi.category, DhApplicationKpi.name).offset(offset).limit(limit).all()

    # Count active mappings per KPI
    from sqlalchemy import func as sa_func
    mapping_counts = dict(
        db.query(DhKpiMapping.kpi_id, sa_func.count(DhKpiMapping.id))
        .filter(DhKpiMapping.is_active == True)
        .group_by(DhKpiMapping.kpi_id)
        .all()
    )

    return {
        "total": total,
        "kpis": [
            {
                "id": k.id,
                "name": k.name,
                "slug": k.slug,
                "category": k.category,
                "sub_category": k.sub_category,
                "description": k.description,
                "unit": k.unit,
                "data_type": k.data_type,
                "target_modules": k.target_modules,
                "tags": k.tags,
                "is_required": k.is_required,
                "mapping_count": mapping_counts.get(k.id, 0),
            }
            for k in kpis
        ],
    }


@router.get("/kpis/{kpi_id}", summary="Get KPI detail with mappings")
def get_kpi_detail(
    kpi_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Get full KPI detail including all mappings and source info."""
    kpi = db.query(DhApplicationKpi).filter(DhApplicationKpi.id == kpi_id).first()
    if not kpi:
        raise HTTPException(404, "KPI not found")

    mappings = (
        db.query(DhKpiMapping)
        .filter(DhKpiMapping.kpi_id == kpi_id)
        .order_by(DhKpiMapping.priority_order)
        .all()
    )

    mapping_list = []
    for m in mappings:
        source = db.query(DhDataSource).filter(DhDataSource.id == m.source_id).first()
        field = db.query(DhSourceField).filter(DhSourceField.id == m.source_field_id).first() if m.source_field_id else None
        mapping_list.append({
            "id": m.id,
            "source_id": m.source_id,
            "source_name": source.name if source else None,
            "source_category": source.category if source else None,
            "source_field_id": m.source_field_id,
            "source_field_name": field.field_name if field else None,
            "source_field_path": field.field_path if field else None,
            "priority_order": m.priority_order,
            "is_active": m.is_active,
            "transform_formula": m.transform_formula,
            "unit_from": m.unit_from,
            "unit_to": m.unit_to,
            "approximation_method": m.approximation_method,
            "confidence_score": m.confidence_score,
            "version": m.version,
            "is_current": m.is_current,
            "change_note": m.change_note,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {
        "id": kpi.id,
        "name": kpi.name,
        "slug": kpi.slug,
        "category": kpi.category,
        "sub_category": kpi.sub_category,
        "description": kpi.description,
        "unit": kpi.unit,
        "data_type": kpi.data_type,
        "target_modules": kpi.target_modules,
        "tags": kpi.tags,
        "is_required": kpi.is_required,
        "mappings": mapping_list,
    }


# ── KPI Categories (distinct values) ───────────────────────────────────────

@router.get("/kpi-categories", summary="List distinct KPI categories")
def list_kpi_categories(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Return distinct KPI categories and sub-categories for filter dropdowns."""
    from sqlalchemy import func
    cats = (
        db.query(
            DhApplicationKpi.category,
            func.count(DhApplicationKpi.id).label("count"),
        )
        .group_by(DhApplicationKpi.category)
        .order_by(DhApplicationKpi.category)
        .all()
    )
    return {
        "categories": [{"category": c[0], "count": c[1]} for c in cats if c[0]],
    }


# ── Source Fields ───────────────────────────────────────────────────────────

@router.get("/source-fields", summary="List source fields")
def list_source_fields(
    source_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """List source fields, optionally filtered by source."""
    q = db.query(DhSourceField)
    if source_id:
        q = q.filter(DhSourceField.source_id == source_id)
    if search:
        q = q.filter(
            DhSourceField.field_name.ilike(f"%{search}%")
            | DhSourceField.description.ilike(f"%{search}%")
        )

    total = q.count()
    fields = q.order_by(DhSourceField.source_id, DhSourceField.field_name).offset(offset).limit(limit).all()

    return {
        "total": total,
        "fields": [
            {
                "id": f.id,
                "source_id": f.source_id,
                "field_name": f.field_name,
                "field_path": f.field_path,
                "data_type": f.data_type,
                "description": f.description,
                "unit": f.unit,
                "sample_values": f.sample_values,
                "is_primary_key": f.is_primary_key,
                "is_nullable": f.is_nullable,
            }
            for f in fields
        ],
    }


@router.post("/source-fields", summary="Create a source field")
def create_source_field(
    body: dict,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "data_engineer")),
):
    """Register a new source field (used during mapping to catalog new fields)."""
    import uuid
    required = ["source_id", "field_name"]
    for r in required:
        if r not in body:
            raise HTTPException(422, f"Missing required field: {r}")

    source = db.query(DhDataSource).filter(DhDataSource.id == body["source_id"]).first()
    if not source:
        raise HTTPException(404, "Source not found")

    field = DhSourceField(
        id=str(uuid.uuid4()),
        source_id=body["source_id"],
        field_name=body["field_name"],
        field_path=body.get("field_path"),
        data_type=body.get("data_type"),
        description=body.get("description"),
        unit=body.get("unit"),
        sample_values=body.get("sample_values"),
        is_primary_key=body.get("is_primary_key", False),
        is_nullable=body.get("is_nullable", True),
    )
    db.add(field)
    db.commit()
    db.refresh(field)

    return {
        "id": field.id,
        "source_id": field.source_id,
        "field_name": field.field_name,
        "message": "Source field created",
    }


# ── KPI Mappings CRUD ───────────────────────────────────────────────────────

@router.get("/mappings", summary="List KPI mappings")
def list_mappings(
    kpi_id: Optional[str] = Query(None),
    source_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """List KPI mappings with join info for source names and field names."""
    q = db.query(DhKpiMapping)
    if kpi_id:
        q = q.filter(DhKpiMapping.kpi_id == kpi_id)
    if source_id:
        q = q.filter(DhKpiMapping.source_id == source_id)
    if is_active is not None:
        q = q.filter(DhKpiMapping.is_active == is_active)

    total = q.count()
    mappings = q.order_by(DhKpiMapping.kpi_id, DhKpiMapping.priority_order).offset(offset).limit(limit).all()

    result = []
    for m in mappings:
        kpi = db.query(DhApplicationKpi).filter(DhApplicationKpi.id == m.kpi_id).first()
        source = db.query(DhDataSource).filter(DhDataSource.id == m.source_id).first()
        field = db.query(DhSourceField).filter(DhSourceField.id == m.source_field_id).first() if m.source_field_id else None
        result.append({
            "id": m.id,
            "kpi_id": m.kpi_id,
            "kpi_name": kpi.name if kpi else None,
            "kpi_category": kpi.category if kpi else None,
            "source_id": m.source_id,
            "source_name": source.name if source else None,
            "source_field_id": m.source_field_id,
            "source_field_name": field.field_name if field else None,
            "priority_order": m.priority_order,
            "is_active": m.is_active,
            "transform_formula": m.transform_formula,
            "unit_from": m.unit_from,
            "unit_to": m.unit_to,
            "approximation_method": m.approximation_method,
            "confidence_score": m.confidence_score,
            "version": m.version,
            "is_current": m.is_current,
            "change_note": m.change_note,
            "created_by": m.created_by,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {"total": total, "mappings": result}


class MappingCreate(BaseModel):
    kpi_id: str
    source_id: str
    source_field_id: Optional[str] = None
    priority_order: Optional[int] = 1
    is_active: bool = True
    transform_formula: Optional[str] = None
    unit_from: Optional[str] = None
    unit_to: Optional[str] = None
    approximation_method: Optional[str] = None
    approximation_assumption: Optional[str] = None
    confidence_score: Optional[float] = None
    change_note: Optional[str] = None


class MappingUpdate(BaseModel):
    source_field_id: Optional[str] = None
    priority_order: Optional[int] = None
    is_active: Optional[bool] = None
    transform_formula: Optional[str] = None
    unit_from: Optional[str] = None
    unit_to: Optional[str] = None
    approximation_method: Optional[str] = None
    approximation_assumption: Optional[str] = None
    confidence_score: Optional[float] = None
    change_note: Optional[str] = None


@router.post("/mappings", summary="Create a KPI mapping")
def create_mapping(
    body: MappingCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "data_engineer")),
):
    """Create a new KPI-to-source mapping."""
    import uuid

    # Validate references
    kpi = db.query(DhApplicationKpi).filter(DhApplicationKpi.id == body.kpi_id).first()
    if not kpi:
        raise HTTPException(404, f"KPI not found: {body.kpi_id}")

    source = db.query(DhDataSource).filter(DhDataSource.id == body.source_id).first()
    if not source:
        raise HTTPException(404, f"Source not found: {body.source_id}")

    if body.source_field_id:
        field = db.query(DhSourceField).filter(DhSourceField.id == body.source_field_id).first()
        if not field:
            raise HTTPException(404, f"Source field not found: {body.source_field_id}")

    # Auto-version: find current max version for this kpi+source pair
    existing_max = (
        db.query(DhKpiMapping)
        .filter(DhKpiMapping.kpi_id == body.kpi_id, DhKpiMapping.source_id == body.source_id)
        .order_by(desc(DhKpiMapping.version))
        .first()
    )
    version = (existing_max.version + 1) if existing_max and existing_max.version else 1

    mapping = DhKpiMapping(
        id=str(uuid.uuid4()),
        kpi_id=body.kpi_id,
        source_id=body.source_id,
        source_field_id=body.source_field_id,
        priority_order=body.priority_order,
        is_active=body.is_active,
        transform_formula=body.transform_formula,
        unit_from=body.unit_from,
        unit_to=body.unit_to,
        approximation_method=body.approximation_method,
        approximation_assumption=body.approximation_assumption,
        confidence_score=body.confidence_score,
        version=version,
        is_current=True,
        change_note=body.change_note,
        created_by=_user.email if hasattr(_user, "email") else "api",
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return {
        "id": mapping.id,
        "kpi_id": mapping.kpi_id,
        "source_id": mapping.source_id,
        "version": mapping.version,
        "message": "Mapping created",
    }


@router.put("/mappings/{mapping_id}", summary="Update a KPI mapping")
def update_mapping(
    mapping_id: str,
    body: MappingUpdate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "data_engineer")),
):
    """Update an existing KPI mapping."""
    mapping = db.query(DhKpiMapping).filter(DhKpiMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(404, "Mapping not found")

    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mapping, key, value)

    db.commit()
    db.refresh(mapping)

    return {
        "id": mapping.id,
        "kpi_id": mapping.kpi_id,
        "source_id": mapping.source_id,
        "message": "Mapping updated",
    }


@router.delete("/mappings/{mapping_id}", summary="Delete a KPI mapping")
def delete_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "data_engineer")),
):
    """Delete a KPI mapping."""
    mapping = db.query(DhKpiMapping).filter(DhKpiMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(404, "Mapping not found")

    db.delete(mapping)
    db.commit()

    return {"id": mapping_id, "message": "Mapping deleted"}


# ── Module Coverage ─────────────────────────────────────────────────────────

@router.get("/module-coverage", summary="Module coverage from mappings")
def get_module_coverage(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Aggregate module coverage — for each target module, how many KPIs exist
    and how many have at least one active mapping (data source linked).
    """
    from sqlalchemy import func, distinct
    from collections import defaultdict

    kpis = db.query(DhApplicationKpi).all()

    module_kpis = defaultdict(list)
    for k in kpis:
        modules = k.target_modules or []
        if isinstance(modules, list):
            for m in modules:
                module_kpis[m].append(k.id)
        elif isinstance(modules, str):
            module_kpis[modules].append(k.id)

    # Get KPI IDs with at least one active mapping
    mapped_kpi_ids = set(
        row[0] for row in
        db.query(distinct(DhKpiMapping.kpi_id))
        .filter(DhKpiMapping.is_active == True)
        .all()
    )

    # Build per-source mapping counts for each module
    coverage = []
    for module_name, kpi_ids in sorted(module_kpis.items()):
        mapped_count = len(set(kpi_ids) & mapped_kpi_ids)
        total_count = len(kpi_ids)

        # Get sources contributing to this module
        source_ids = set(
            row[0] for row in
            db.query(distinct(DhKpiMapping.source_id))
            .filter(
                DhKpiMapping.kpi_id.in_(kpi_ids),
                DhKpiMapping.is_active == True,
            )
            .all()
        ) if kpi_ids else set()

        coverage.append({
            "module": module_name,
            "total_kpis": total_count,
            "mapped_kpis": mapped_count,
            "coverage_pct": round(mapped_count / total_count * 100, 1) if total_count else 0,
            "source_count": len(source_ids),
        })

    return {
        "modules": coverage,
        "total_kpis": len(kpis),
        "total_mapped": len(mapped_kpi_ids),
    }


# ── Cross-Source Comparison ─────────────────────────────────────────────────

@router.get("/cross-source", summary="Compare source coverage for a KPI")
def cross_source_comparison(
    kpi_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    For a given KPI or category, show which sources provide data and their
    confidence/priority scores. Used for source selection decisions.
    """
    from sqlalchemy import func

    q = db.query(DhKpiMapping)
    if kpi_id:
        q = q.filter(DhKpiMapping.kpi_id == kpi_id)

    if category:
        kpi_ids_in_cat = [
            row[0] for row in
            db.query(DhApplicationKpi.id)
            .filter(DhApplicationKpi.category == category)
            .all()
        ]
        q = q.filter(DhKpiMapping.kpi_id.in_(kpi_ids_in_cat))

    mappings = q.order_by(DhKpiMapping.priority_order).all()

    rows = []
    for m in mappings:
        kpi = db.query(DhApplicationKpi).filter(DhApplicationKpi.id == m.kpi_id).first()
        source = db.query(DhDataSource).filter(DhDataSource.id == m.source_id).first()
        rows.append({
            "kpi_id": m.kpi_id,
            "kpi_name": kpi.name if kpi else None,
            "source_id": m.source_id,
            "source_name": source.name if source else None,
            "source_category": source.category if source else None,
            "priority_order": m.priority_order,
            "confidence_score": m.confidence_score,
            "is_active": m.is_active,
            "transform_formula": m.transform_formula,
            "unit_from": m.unit_from,
            "unit_to": m.unit_to,
        })

    return {"comparisons": rows, "total": len(rows)}
