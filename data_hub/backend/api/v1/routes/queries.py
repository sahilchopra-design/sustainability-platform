from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from typing import List, Optional
from datetime import datetime, timezone
import uuid, time, re

from database import get_db
from models.models import ReferenceData, QueryLog, SavedQuery, DataSource
from schemas.schemas import (
    QueryFilter, NLQueryRequest, QueryResponse, ReferenceDataOut,
    SavedQueryCreate, SavedQueryOut
)

router = APIRouter(prefix="/queries", tags=["Query Interface"])


def _parse_nl_query(nl_text: str) -> QueryFilter:
    """
    Parse natural language query into structured QueryFilter.
    Simple keyword extraction — expand with LLM integration later.
    """
    text_lower = nl_text.lower()
    filters = QueryFilter()

    # Extract KPI names
    kpi_keywords = {
        "scope 1": "scope1_ghg_emissions",
        "scope 2": "scope2_ghg_emissions",
        "scope 3": "scope3_ghg_emissions",
        "carbon intensity": "carbon_intensity",
        "esg score": "esg_score_overall",
        "emissions": "total_ghg_emissions",
        "market cap": "market_cap",
        "revenue": "revenue",
        "pd": "probability_of_default",
        "probability of default": "probability_of_default",
        "water risk": "water_risk_score",
        "temperature": "temperature_alignment",
        "sbti": "sbti_target_status",
    }
    matched_kpis = [v for k, v in kpi_keywords.items() if k in text_lower]
    if matched_kpis:
        filters.kpi_names = matched_kpis

    # Geography
    geo_map = {
        "europe": "Europe", "european": "Europe",
        "asia": "Asia", "us": "US", "united states": "US",
        "global": "Global", "uk": "UK",
    }
    for k, v in geo_map.items():
        if re.search(r'\b' + k + r'\b', text_lower):
            filters.geographies = [v]
            break

    # Sector / entity type
    sector_map = {
        "bank": "Financial Services", "banking": "Financial Services",
        "energy": "Energy", "oil": "Energy", "renewable": "Energy",
        "real estate": "Real Estate", "property": "Real Estate",
        "technology": "Technology", "tech": "Technology",
        "mining": "Mining", "steel": "Steel", "shipping": "Shipping",
    }
    for k, v in sector_map.items():
        if k in text_lower:
            filters.sectors = [v]
            break

    # Year extraction
    years = re.findall(r'\b(20[12][0-9])\b', nl_text)
    if years:
        year = years[0]
        filters.date_from = datetime(int(year), 1, 1, tzinfo=timezone.utc)
        filters.date_to = datetime(int(year), 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    # Data quality
    if "actual" in text_lower:
        filters.data_quality = ["actual"]
    elif "estimate" in text_lower or "proxy" in text_lower:
        filters.data_quality = ["estimated", "proxy"]

    return filters


async def _execute_query(filters: QueryFilter, db: AsyncSession):
    start = time.monotonic()
    conditions = []

    if filters.kpi_names:
        conditions.append(ReferenceData.kpi_name.in_(filters.kpi_names))
    if filters.entity_names:
        conditions.append(or_(*[ReferenceData.entity_name.ilike(f"%{n}%") for n in filters.entity_names]))
    if filters.entity_types:
        conditions.append(ReferenceData.entity_type.in_(filters.entity_types))
    if filters.source_ids:
        conditions.append(ReferenceData.source_id.in_(filters.source_ids))
    if filters.geographies:
        conditions.append(ReferenceData.geography.in_(filters.geographies))
    if filters.sectors:
        conditions.append(ReferenceData.sector.in_(filters.sectors))
    if filters.data_quality:
        conditions.append(ReferenceData.data_quality.in_(filters.data_quality))
    if filters.date_from:
        conditions.append(ReferenceData.date >= filters.date_from)
    if filters.date_to:
        conditions.append(ReferenceData.date <= filters.date_to)
    if filters.min_confidence is not None:
        conditions.append(ReferenceData.confidence_score >= filters.min_confidence)
    if filters.period:
        conditions.append(ReferenceData.period == filters.period)

    q = select(ReferenceData)
    if conditions:
        q = q.where(and_(*conditions))
    q = q.order_by(ReferenceData.ingested_at.desc())

    # Count
    count_q = select(func.count()).select_from(ReferenceData)
    if conditions:
        count_q = count_q.where(and_(*conditions))

    total_r = await db.execute(count_q)
    total = total_r.scalar() or 0

    q = q.limit(filters.limit or 100).offset(filters.offset or 0)
    result = await db.execute(q)
    rows = result.scalars().all()

    elapsed_ms = int((time.monotonic() - start) * 1000)
    source_ids_used = list({r.source_id for r in rows if r.source_id})
    source_names = []
    if source_ids_used:
        sn_q = await db.execute(select(DataSource.name).where(DataSource.id.in_(source_ids_used)))
        source_names = [r[0] for r in sn_q.all()]

    return rows, total, elapsed_ms, source_names


@router.post("/execute", response_model=QueryResponse)
async def execute_query(body: QueryFilter, db: AsyncSession = Depends(get_db)):
    rows, total, elapsed_ms, sources = await _execute_query(body, db)

    # Log query
    log = QueryLog(
        id=str(uuid.uuid4()),
        query_type="builder",
        query_payload=body.model_dump(mode="json"),
        result_count=total,
        execution_ms=elapsed_ms,
        sources_used=sources,
    )
    db.add(log)
    await db.commit()

    return QueryResponse(
        results=[ReferenceDataOut.model_validate(r) for r in rows],
        total=total,
        execution_ms=elapsed_ms,
        sources_used=sources,
        filters_applied=body.model_dump(exclude_none=True, mode="json"),
    )


@router.post("/nl", response_model=QueryResponse)
async def natural_language_query(body: NLQueryRequest, db: AsyncSession = Depends(get_db)):
    filters = _parse_nl_query(body.text)
    filters.limit = body.limit
    rows, total, elapsed_ms, sources = await _execute_query(filters, db)

    log = QueryLog(
        id=str(uuid.uuid4()),
        query_type="nl",
        nl_text=body.text,
        query_payload=filters.model_dump(mode="json"),
        result_count=total,
        execution_ms=elapsed_ms,
        sources_used=sources,
    )
    db.add(log)
    await db.commit()

    return QueryResponse(
        results=[ReferenceDataOut.model_validate(r) for r in rows],
        total=total,
        execution_ms=elapsed_ms,
        sources_used=sources,
        filters_applied=filters.model_dump(exclude_none=True, mode="json"),
    )


@router.post("/export")
async def export_query(body: QueryFilter, format: str = Query("csv", regex="^(csv|json)$"), db: AsyncSession = Depends(get_db)):
    from fastapi.responses import StreamingResponse
    import io, csv as csv_lib, json as json_lib

    rows, total, _, _ = await _execute_query(body, db)

    if format == "json":
        data = [ReferenceDataOut.model_validate(r).model_dump(mode="json") for r in rows]
        return StreamingResponse(
            io.BytesIO(json_lib.dumps(data, indent=2, default=str).encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=reference_data.json"},
        )

    # CSV
    output = io.StringIO()
    fields = [
        "entity_name", "entity_id", "entity_type", "kpi_name", "value",
        "value_numeric", "unit", "period", "date", "geography", "sector",
        "source_name", "source_field", "data_quality", "confidence_score",
        "approximation_method", "transform_applied", "ingested_at",
    ]
    writer = csv_lib.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        d = ReferenceDataOut.model_validate(r).model_dump(mode="json")
        writer.writerow(d)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reference_data.csv"},
    )


# ── Saved queries ─────────────────────────────────────────────────────────────

@router.get("/saved", response_model=List[SavedQueryOut])
async def list_saved_queries(
    is_public: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(SavedQuery).order_by(SavedQuery.updated_at.desc())
    if is_public is not None:
        q = q.where(SavedQuery.is_public == is_public)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/saved", response_model=SavedQueryOut, status_code=201)
async def save_query(body: SavedQueryCreate, db: AsyncSession = Depends(get_db)):
    sq = SavedQuery(id=str(uuid.uuid4()), **body.model_dump())
    db.add(sq)
    await db.commit()
    await db.refresh(sq)
    return sq


@router.post("/saved/{query_id}/run", response_model=QueryResponse)
async def run_saved_query(query_id: str, db: AsyncSession = Depends(get_db)):
    sq = await db.get(SavedQuery, query_id)
    if not sq:
        raise HTTPException(404, "Saved query not found.")
    sq.run_count += 1
    await db.commit()
    filters = QueryFilter(**sq.query_payload)
    rows, total, elapsed_ms, sources = await _execute_query(filters, db)
    return QueryResponse(
        results=[ReferenceDataOut.model_validate(r) for r in rows],
        total=total,
        execution_ms=elapsed_ms,
        sources_used=sources,
        filters_applied=filters.model_dump(exclude_none=True, mode="json"),
    )


@router.delete("/saved/{query_id}", status_code=204)
async def delete_saved_query(query_id: str, db: AsyncSession = Depends(get_db)):
    sq = await db.get(SavedQuery, query_id)
    if not sq:
        raise HTTPException(404, "Saved query not found.")
    await db.delete(sq)
    await db.commit()


# ── Query logs ────────────────────────────────────────────────────────────────

@router.get("/logs")
async def get_query_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
