from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import get_db
from models.models import DataSource, SourceField, KpiMapping, SyncJob, SourceAssessment
from schemas.schemas import (
    DataSourceCreate, DataSourceUpdate, DataSourceOut,
    SourceFieldCreate, SourceFieldOut, ConnectionTestResult,
    SyncJobOut, SyncTriggerResponse, AssessmentOut
)
from services.assessment_engine import assess_source
from services.connector import test_connection, run_sync

router = APIRouter(prefix="/sources", tags=["Data Sources"])


async def _run_assessment(source_id: str, source_dict: dict, db_url: str):
    """Background task: compute and persist assessment."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    engine = create_async_engine(db_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        result = assess_source(source_dict)
        assessment = SourceAssessment(
            id=str(uuid.uuid4()),
            source_id=source_id,
            **result,
            assessed_by="auto",
        )
        session.add(assessment)
        # Update source priority/utility/score
        await session.execute(
            update(DataSource)
            .where(DataSource.id == source_id)
            .values(
                priority=result["priority"],
                utility=result["utility"],
                assessment_score=result["total_score"],
            )
        )
        await session.commit()
    await engine.dispose()


@router.get("", response_model=List[DataSourceOut])
async def list_sources(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    batch: Optional[int] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(DataSource)
    if status:
        q = q.where(DataSource.status == status)
    if category:
        q = q.where(DataSource.category == category)
    if priority:
        q = q.where(DataSource.priority == priority)
    if batch:
        q = q.where(DataSource.batch == batch)
    if search:
        term = f"%{search}%"
        q = q.where(
            DataSource.name.ilike(term) |
            DataSource.category.ilike(term) |
            DataSource.rationale.ilike(term)
        )
    q = q.order_by(DataSource.assessment_score.desc().nullslast(), DataSource.name)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    sources = result.scalars().all()

    # Enrich with counts
    out = []
    for s in sources:
        count_q = await db.execute(
            select(func.count()).where(KpiMapping.source_id == s.id, KpiMapping.is_current == True)
        )
        mapped_count = count_q.scalar() or 0
        sync_q = await db.execute(
            select(func.count()).where(SyncJob.source_id == s.id)
        )
        sync_count = sync_q.scalar() or 0
        d = DataSourceOut.model_validate(s)
        d.mapped_kpi_count = mapped_count
        d.sync_job_count = sync_count
        out.append(d)
    return out


@router.post("", response_model=DataSourceOut, status_code=201)
async def create_source(
    body: DataSourceCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Check unique name
    existing = await db.execute(select(DataSource).where(DataSource.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Source '{body.name}' already exists.")

    source = DataSource(id=str(uuid.uuid4()), **body.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)

    # Auto-assess unless skip_assessment is set
    if not body.skip_assessment:
        from database import settings
        source_dict = {**body.model_dump(), "name": body.name}
        background_tasks.add_task(
            _run_assessment, source.id, source_dict, settings.database_url
        )

    d = DataSourceOut.model_validate(source)
    d.mapped_kpi_count = 0
    d.sync_job_count = 0
    return d


@router.get("/{source_id}", response_model=DataSourceOut)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    count_q = await db.execute(
        select(func.count()).where(KpiMapping.source_id == source_id, KpiMapping.is_current == True)
    )
    sync_q = await db.execute(select(func.count()).where(SyncJob.source_id == source_id))
    d = DataSourceOut.model_validate(source)
    d.mapped_kpi_count = count_q.scalar() or 0
    d.sync_job_count = sync_q.scalar() or 0
    return d


@router.put("/{source_id}", response_model=DataSourceOut)
async def update_source(
    source_id: str,
    body: DataSourceUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")

    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    for k, v in update_data.items():
        setattr(source, k, v)

    await db.commit()
    await db.refresh(source)

    # Re-assess if key fields changed
    reasses_fields = {"quality_rating", "cost", "access_type", "update_freq", "geographic", "status"}
    if reasses_fields & set(update_data.keys()) and not source.skip_assessment:
        from database import settings
        source_dict = {c.name: getattr(source, c.name) for c in source.__table__.columns}
        background_tasks.add_task(_run_assessment, source.id, source_dict, settings.database_url)

    d = DataSourceOut.model_validate(source)
    return d


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    # Check active mappings
    mapping_q = await db.execute(
        select(func.count()).where(KpiMapping.source_id == source_id, KpiMapping.is_current == True)
    )
    if mapping_q.scalar() > 0:
        raise HTTPException(
            409,
            "Source has active KPI mappings. Remove mappings first or they will be orphaned."
        )
    await db.delete(source)
    await db.commit()


# ── Connection test ───────────────────────────────────────────────────────────

@router.post("/{source_id}/test-connection", response_model=ConnectionTestResult)
async def test_source_connection(source_id: str, db: AsyncSession = Depends(get_db)):
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    source_dict = {c.name: getattr(source, c.name) for c in source.__table__.columns}
    result = await test_connection(source_dict)
    return ConnectionTestResult(
        source_id=source_id,
        source_name=source.name,
        **result,
    )


# ── Manual refresh ────────────────────────────────────────────────────────────

@router.post("/{source_id}/refresh", response_model=SyncTriggerResponse)
async def trigger_refresh(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger an immediate manual data refresh for this source."""
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")

    job = SyncJob(
        id=str(uuid.uuid4()),
        source_id=source_id,
        triggered_by="manual",
        status="pending",
    )
    db.add(job)
    # Update source status to show it is syncing
    source.last_sync_status = "pending"
    await db.commit()

    # Run sync in background
    background_tasks.add_task(_execute_sync, job.id, source_id, source.name)

    return SyncTriggerResponse(
        job_id=job.id,
        source_id=source_id,
        source_name=source.name,
        status="pending",
        message=f"Sync job created. Job ID: {job.id}. Use GET /sync/jobs/{job.id} to track progress.",
    )


async def _execute_sync(job_id: str, source_id: str, source_name: str):
    """Background task: run the actual sync and update job record."""
    from database import settings, AsyncSessionLocal
    from datetime import datetime, timezone
    async with AsyncSessionLocal() as session:
        job = await session.get(SyncJob, job_id)
        source = await session.get(DataSource, source_id)
        if not job or not source:
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        source.last_sync_status = "running"
        await session.commit()

        source_dict = {c.name: getattr(source, c.name) for c in source.__table__.columns}
        try:
            stats = await run_sync(source_dict, job_id)
            job.status = "success"
            job.rows_fetched = stats.get("rows_fetched", 0)
            job.rows_inserted = stats.get("rows_inserted", 0)
            job.rows_updated = stats.get("rows_updated", 0)
            job.rows_skipped = stats.get("rows_skipped", 0)
            job.rows_failed = stats.get("rows_failed", 0)
            source.last_sync_status = "success"
            source.last_synced_at = datetime.now(timezone.utc)
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            source.last_sync_status = "failed"
            source.last_sync_error = str(e)

        job.completed_at = datetime.now(timezone.utc)
        if job.started_at:
            job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
        await session.commit()


# ── Source fields ─────────────────────────────────────────────────────────────

@router.get("/{source_id}/fields", response_model=List[SourceFieldOut])
async def get_source_fields(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SourceField).where(SourceField.source_id == source_id)
        .order_by(SourceField.field_name)
    )
    return result.scalars().all()


@router.post("/{source_id}/fields", response_model=SourceFieldOut, status_code=201)
async def add_source_field(
    source_id: str, body: SourceFieldCreate, db: AsyncSession = Depends(get_db)
):
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    field = SourceField(id=str(uuid.uuid4()), source_id=source_id, **body.model_dump(exclude={"source_id"}))
    db.add(field)
    await db.commit()
    await db.refresh(field)
    return field


# ── Sync history ──────────────────────────────────────────────────────────────

@router.get("/{source_id}/sync-history", response_model=List[SyncJobOut])
async def get_sync_history(
    source_id: str,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    q = (
        select(SyncJob)
        .where(SyncJob.source_id == source_id)
        .order_by(SyncJob.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    jobs = result.scalars().all()
    out = []
    for j in jobs:
        d = SyncJobOut.model_validate(j)
        d.source_name = source.name
        out.append(d)
    return out


# ── Assessment ────────────────────────────────────────────────────────────────

@router.get("/{source_id}/assessment", response_model=AssessmentOut)
async def get_assessment(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SourceAssessment)
        .where(SourceAssessment.source_id == source_id, SourceAssessment.is_current == True)
        .order_by(SourceAssessment.created_at.desc())
        .limit(1)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "No assessment found for this source.")
    source = await db.get(DataSource, source_id)
    d = AssessmentOut.model_validate(assessment)
    d.source_name = source.name if source else None
    return d


@router.post("/{source_id}/assess", response_model=AssessmentOut)
async def trigger_assessment(source_id: str, db: AsyncSession = Depends(get_db)):
    """Force re-run of assessment for this source."""
    source = await db.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")

    # Deactivate previous assessments
    await db.execute(
        update(SourceAssessment)
        .where(SourceAssessment.source_id == source_id)
        .values(is_current=False)
    )

    source_dict = {c.name: getattr(source, c.name) for c in source.__table__.columns}
    result = assess_source(source_dict)
    assessment = SourceAssessment(
        id=str(uuid.uuid4()),
        source_id=source_id,
        **result,
        assessed_by="manual",
    )
    db.add(assessment)
    source.priority = result["priority"]
    source.utility = result["utility"]
    source.assessment_score = result["total_score"]
    await db.commit()
    await db.refresh(assessment)

    d = AssessmentOut.model_validate(assessment)
    d.source_name = source.name
    return d
