from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, timedelta
from typing import List

from database import get_db
from models.models import (
    DataSource, ApplicationKpi, KpiMapping, ReferenceData,
    SyncJob, QueryLog
)
from schemas.schemas import AnalyticsOverview, MappingCoverage, DataQualityDist, TopItem

router = APIRouter(prefix="/analytics", tags=["Analytics Dashboard"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(db: AsyncSession = Depends(get_db)):
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    async def count(model, *conditions):
        q = select(func.count()).select_from(model)
        if conditions:
            q = q.where(*conditions)
        r = await db.execute(q)
        return r.scalar() or 0

    total_sources = await count(DataSource)
    active_sources = await count(DataSource, DataSource.status == "active")
    error_sources = await count(DataSource, DataSource.status == "error")
    paused_sources = await count(DataSource, DataSource.status == "paused")
    planned_sources = await count(DataSource, DataSource.status == "planned")
    configuring_sources = await count(DataSource, DataSource.status == "configuring")

    p0 = await count(DataSource, DataSource.priority == "P0")
    p1 = await count(DataSource, DataSource.priority == "P1")
    p2 = await count(DataSource, DataSource.priority == "P2")

    total_kpis = await count(ApplicationKpi)
    # KPIs with at least one active mapping
    mapped_q = await db.execute(
        select(func.count(ApplicationKpi.id.distinct()))
        .join(KpiMapping, KpiMapping.kpi_id == ApplicationKpi.id)
        .where(KpiMapping.is_current == True, KpiMapping.is_active == True)
    )
    mapped_kpis = mapped_q.scalar() or 0
    unmapped_kpis = total_kpis - mapped_kpis
    coverage_pct = round((mapped_kpis / total_kpis * 100) if total_kpis > 0 else 0.0, 1)

    total_ref = await count(ReferenceData)

    last_24h = await count(SyncJob, SyncJob.created_at >= since_24h)
    failed_24h = await count(SyncJob, SyncJob.status == "failed", SyncJob.created_at >= since_24h)

    return AnalyticsOverview(
        total_sources=total_sources,
        active_sources=active_sources,
        error_sources=error_sources,
        paused_sources=paused_sources,
        planned_sources=planned_sources,
        configuring_sources=configuring_sources,
        total_kpis=total_kpis,
        mapped_kpis=mapped_kpis,
        unmapped_kpis=unmapped_kpis,
        mapping_coverage_pct=coverage_pct,
        total_reference_rows=total_ref,
        p0_sources=p0,
        p1_sources=p1,
        p2_sources=p2,
        last_sync_24h=last_24h,
        failed_syncs_24h=failed_24h,
    )


@router.get("/coverage", response_model=List[MappingCoverage])
async def get_mapping_coverage(db: AsyncSession = Depends(get_db)):
    kpis_q = await db.execute(select(ApplicationKpi).order_by(ApplicationKpi.category, ApplicationKpi.name))
    kpis = kpis_q.scalars().all()

    out = []
    for kpi in kpis:
        mappings_q = await db.execute(
            select(KpiMapping)
            .where(KpiMapping.kpi_id == kpi.id, KpiMapping.is_current == True, KpiMapping.is_active == True)
            .order_by(KpiMapping.priority_order)
        )
        mappings = mappings_q.scalars().all()
        primary = any(m.priority_order == 1 for m in mappings)
        fallback_count = sum(1 for m in mappings if m.priority_order > 1)

        if primary and fallback_count > 0:
            status = "full"
        elif primary:
            status = "partial"
        else:
            status = "unmapped"

        out.append(MappingCoverage(
            kpi_id=kpi.id,
            kpi_name=kpi.name,
            category=kpi.category or "",
            primary_mapped=primary,
            fallback_count=fallback_count,
            modules=kpi.target_modules or [],
            coverage_status=status,
        ))
    return out


@router.get("/data-quality", response_model=DataQualityDist)
async def get_data_quality(db: AsyncSession = Depends(get_db)):
    total_q = await db.execute(select(func.count()).select_from(ReferenceData))
    total = total_q.scalar() or 1  # avoid div/0

    async def count_quality(q_type: str) -> int:
        r = await db.execute(select(func.count()).where(ReferenceData.data_quality == q_type))
        return r.scalar() or 0

    actual = await count_quality("actual")
    estimated = await count_quality("estimated")
    proxy = await count_quality("proxy")

    return DataQualityDist(
        actual=actual,
        estimated=estimated,
        proxy=proxy,
        actual_pct=round(actual / total * 100, 1),
        estimated_pct=round(estimated / total * 100, 1),
        proxy_pct=round(proxy / total * 100, 1),
    )


@router.get("/top-kpis", response_model=List[TopItem])
async def get_top_kpis(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QueryLog.query_payload)
        .order_by(QueryLog.created_at.desc())
        .limit(500)
    )
    kpi_counts: dict = {}
    for row in result.scalars().all():
        if isinstance(row, dict):
            for kpi in (row.get("kpi_names") or []):
                kpi_counts[kpi] = kpi_counts.get(kpi, 0) + 1
    top = sorted(kpi_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [TopItem(name=k, count=v) for k, v in top]


@router.get("/top-sources", response_model=List[TopItem])
async def get_top_sources(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DataSource.name, func.count(KpiMapping.id).label("count"))
        .join(KpiMapping, KpiMapping.source_id == DataSource.id, isouter=True)
        .where(KpiMapping.is_current == True)
        .group_by(DataSource.name)
        .order_by(func.count(KpiMapping.id).desc())
        .limit(limit)
    )
    return [TopItem(name=r[0], count=r[1] or 0) for r in result.all()]


@router.get("/unmapped-kpis")
async def get_unmapped_kpis(db: AsyncSession = Depends(get_db)):
    """KPIs with zero active mappings."""
    result = await db.execute(
        select(ApplicationKpi)
        .where(
            ~ApplicationKpi.id.in_(
                select(KpiMapping.kpi_id)
                .where(KpiMapping.is_current == True, KpiMapping.is_active == True)
                .scalar_subquery()
            )
        )
        .order_by(ApplicationKpi.is_required.desc(), ApplicationKpi.name)
    )
    kpis = result.scalars().all()
    return [
        {
            "id": k.id, "name": k.name, "category": k.category,
            "is_required": k.is_required, "modules": k.target_modules,
        }
        for k in kpis
    ]


@router.get("/source-categories")
async def get_source_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DataSource.category, func.count().label("total"),
               func.sum(func.cast(DataSource.status == "active", db.bind.dialect.name == "postgresql" and "int" or "integer")).label("active")
        )
        .group_by(DataSource.category)
        .order_by(DataSource.category)
    )
    return [{"category": r[0], "total": r[1]} for r in result.all()]
