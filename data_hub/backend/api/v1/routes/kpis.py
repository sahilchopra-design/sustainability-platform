from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
import uuid

from database import get_db
from models.models import ApplicationKpi, KpiMapping, DataSource
from schemas.schemas import KpiCreate, KpiUpdate, KpiOut, KpiFinderResult

router = APIRouter(prefix="/kpis", tags=["KPIs"])


@router.get("", response_model=List[KpiOut])
async def list_kpis(
    category: Optional[str] = None,
    module: Optional[str] = None,
    search: Optional[str] = None,
    is_required: Optional[bool] = None,
    limit: int = Query(200, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(ApplicationKpi)
    if category:
        q = q.where(ApplicationKpi.category == category)
    if is_required is not None:
        q = q.where(ApplicationKpi.is_required == is_required)
    if search:
        term = f"%{search}%"
        q = q.where(
            ApplicationKpi.name.ilike(term) |
            ApplicationKpi.description.ilike(term) |
            ApplicationKpi.slug.ilike(term)
        )
    q = q.order_by(ApplicationKpi.category, ApplicationKpi.name).limit(limit).offset(offset)
    result = await db.execute(q)
    kpis = result.scalars().all()

    out = []
    for kpi in kpis:
        # Count active mappings
        mc = await db.execute(
            select(func.count()).where(KpiMapping.kpi_id == kpi.id, KpiMapping.is_current == True)
        )
        # Get primary source names
        ps = await db.execute(
            select(DataSource.name)
            .join(KpiMapping, KpiMapping.source_id == DataSource.id)
            .where(KpiMapping.kpi_id == kpi.id, KpiMapping.is_current == True, KpiMapping.priority_order == 1)
        )
        d = KpiOut.model_validate(kpi)
        d.mapping_count = mc.scalar() or 0
        d.primary_sources = [r[0] for r in ps.all()]
        out.append(d)
    return out


@router.post("", response_model=KpiOut, status_code=201)
async def create_kpi(body: KpiCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(ApplicationKpi).where(ApplicationKpi.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"KPI with slug '{body.slug}' already exists.")
    kpi = ApplicationKpi(id=str(uuid.uuid4()), **body.model_dump())
    db.add(kpi)
    await db.commit()
    await db.refresh(kpi)
    d = KpiOut.model_validate(kpi)
    d.mapping_count = 0
    d.primary_sources = []
    return d


@router.get("/search", response_model=List[KpiFinderResult])
async def find_kpi(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
):
    """
    KPI Finder: search by name or tag, return structured source chain per KPI.
    """
    term = f"%{q}%"
    result = await db.execute(
        select(ApplicationKpi).where(
            ApplicationKpi.name.ilike(term) |
            ApplicationKpi.description.ilike(term) |
            ApplicationKpi.slug.ilike(term)
        ).limit(20)
    )
    kpis = result.scalars().all()

    out = []
    for kpi in kpis:
        mappings_q = await db.execute(
            select(KpiMapping, DataSource.name.label("source_name"))
            .join(DataSource, DataSource.id == KpiMapping.source_id)
            .where(KpiMapping.kpi_id == kpi.id, KpiMapping.is_current == True)
            .order_by(KpiMapping.priority_order)
        )
        mappings = mappings_q.all()

        primary_sources = [m.source_name for m in mappings if m.KpiMapping.priority_order == 1]
        fallback_sources = [m.source_name for m in mappings if m.KpiMapping.priority_order > 1]
        approx = next((m.KpiMapping.approximation_method for m in mappings if m.KpiMapping.approximation_method), None)

        if len(mappings) == 0:
            status = "unmapped"
        elif primary_sources:
            status = "mapped"
        else:
            status = "partial"

        kpi_out = KpiOut.model_validate(kpi)
        kpi_out.mapping_count = len(mappings)
        kpi_out.primary_sources = primary_sources

        out.append(KpiFinderResult(
            kpi=kpi_out,
            primary_sources=primary_sources,
            fallback_sources=fallback_sources,
            mapping_status=status,
            approximation_method=approx,
            consuming_modules=kpi.target_modules or [],
        ))
    return out


@router.get("/categories")
async def list_kpi_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApplicationKpi.category, func.count().label("count"))
        .group_by(ApplicationKpi.category)
        .order_by(ApplicationKpi.category)
    )
    return [{"category": r[0], "count": r[1]} for r in result.all()]


@router.get("/{kpi_id}", response_model=KpiOut)
async def get_kpi(kpi_id: str, db: AsyncSession = Depends(get_db)):
    kpi = await db.get(ApplicationKpi, kpi_id)
    if not kpi:
        raise HTTPException(404, "KPI not found.")
    mc = await db.execute(
        select(func.count()).where(KpiMapping.kpi_id == kpi_id, KpiMapping.is_current == True)
    )
    ps = await db.execute(
        select(DataSource.name)
        .join(KpiMapping, KpiMapping.source_id == DataSource.id)
        .where(KpiMapping.kpi_id == kpi_id, KpiMapping.is_current == True, KpiMapping.priority_order == 1)
    )
    d = KpiOut.model_validate(kpi)
    d.mapping_count = mc.scalar() or 0
    d.primary_sources = [r[0] for r in ps.all()]
    return d


@router.put("/{kpi_id}", response_model=KpiOut)
async def update_kpi(kpi_id: str, body: KpiUpdate, db: AsyncSession = Depends(get_db)):
    kpi = await db.get(ApplicationKpi, kpi_id)
    if not kpi:
        raise HTTPException(404, "KPI not found.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(kpi, k, v)
    await db.commit()
    await db.refresh(kpi)
    d = KpiOut.model_validate(kpi)
    return d


@router.delete("/{kpi_id}", status_code=204)
async def delete_kpi(kpi_id: str, db: AsyncSession = Depends(get_db)):
    kpi = await db.get(ApplicationKpi, kpi_id)
    if not kpi:
        raise HTTPException(404, "KPI not found.")
    await db.delete(kpi)
    await db.commit()


@router.get("/{kpi_id}/mappings")
async def get_kpi_mappings(kpi_id: str, db: AsyncSession = Depends(get_db)):
    from schemas.schemas import MappingOut
    result = await db.execute(
        select(KpiMapping, DataSource.name.label("source_name"))
        .join(DataSource, DataSource.id == KpiMapping.source_id)
        .where(KpiMapping.kpi_id == kpi_id, KpiMapping.is_current == True)
        .order_by(KpiMapping.priority_order)
    )
    rows = result.all()
    out = []
    for r in rows:
        d = MappingOut.model_validate(r.KpiMapping)
        d.source_name = r.source_name
        out.append(d)
    return out
