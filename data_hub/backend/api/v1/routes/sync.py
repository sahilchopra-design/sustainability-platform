from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from database import get_db
from models.models import SyncJob, DataSource
from schemas.schemas import SyncJobOut

router = APIRouter(prefix="/sync", tags=["Sync & Ingestion"])


@router.get("/jobs", response_model=List[SyncJobOut])
async def list_sync_jobs(
    source_id: Optional[str] = None,
    status: Optional[str] = None,
    triggered_by: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(SyncJob, DataSource.name.label("source_name"))
        .join(DataSource, DataSource.id == SyncJob.source_id, isouter=True)
        .order_by(SyncJob.created_at.desc())
    )
    if source_id:
        q = q.where(SyncJob.source_id == source_id)
    if status:
        q = q.where(SyncJob.status == status)
    if triggered_by:
        q = q.where(SyncJob.triggered_by == triggered_by)
    q = q.limit(limit).offset(offset)

    result = await db.execute(q)
    rows = result.all()
    out = []
    for r in rows:
        d = SyncJobOut.model_validate(r.SyncJob)
        d.source_name = r.source_name
        out.append(d)
    return out


@router.get("/jobs/{job_id}", response_model=SyncJobOut)
async def get_sync_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SyncJob, DataSource.name.label("source_name"))
        .join(DataSource, DataSource.id == SyncJob.source_id, isouter=True)
        .where(SyncJob.id == job_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Sync job not found.")
    d = SyncJobOut.model_validate(row.SyncJob)
    d.source_name = row.source_name
    return d


@router.get("/stats")
async def get_sync_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate sync statistics across all sources."""
    total_q = await db.execute(select(func.count()).select_from(SyncJob))
    success_q = await db.execute(select(func.count()).where(SyncJob.status == "success"))
    failed_q = await db.execute(select(func.count()).where(SyncJob.status == "failed"))
    running_q = await db.execute(select(func.count()).where(SyncJob.status == "running"))
    pending_q = await db.execute(select(func.count()).where(SyncJob.status == "pending"))

    # Last 24h
    from datetime import datetime, timezone, timedelta
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_q = await db.execute(select(func.count()).where(SyncJob.created_at >= since))
    failed_24h_q = await db.execute(
        select(func.count()).where(SyncJob.status == "failed", SyncJob.created_at >= since)
    )

    # Sources with enabled sync
    enabled_q = await db.execute(
        select(func.count()).select_from(DataSource).where(DataSource.sync_enabled == True)
    )

    # Most recently synced
    recent_jobs_q = await db.execute(
        select(SyncJob, DataSource.name.label("source_name"))
        .join(DataSource, DataSource.id == SyncJob.source_id, isouter=True)
        .order_by(SyncJob.created_at.desc())
        .limit(5)
    )
    recent_jobs = []
    for r in recent_jobs_q.all():
        recent_jobs.append({
            "job_id": r.SyncJob.id,
            "source_name": r.source_name,
            "status": r.SyncJob.status,
            "triggered_by": r.SyncJob.triggered_by,
            "created_at": r.SyncJob.created_at.isoformat() if r.SyncJob.created_at else None,
            "duration_seconds": r.SyncJob.duration_seconds,
        })

    return {
        "total_jobs": total_q.scalar(),
        "success": success_q.scalar(),
        "failed": failed_q.scalar(),
        "running": running_q.scalar(),
        "pending": pending_q.scalar(),
        "syncs_last_24h": recent_q.scalar(),
        "failures_last_24h": failed_24h_q.scalar(),
        "sources_with_sync_enabled": enabled_q.scalar(),
        "recent_jobs": recent_jobs,
    }
