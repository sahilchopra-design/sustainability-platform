from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
import uuid, io, csv

from database import get_db
from models.models import KpiMapping, ApplicationKpi, DataSource, SourceField
from schemas.schemas import MappingCreate, MappingUpdate, MappingOut, MappingPreview

router = APIRouter(prefix="/mappings", tags=["KPI Mappings"])


@router.get("", response_model=List[MappingOut])
async def list_mappings(
    kpi_id: Optional[str] = None,
    source_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    include_history: bool = False,
    limit: int = Query(200, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(KpiMapping, ApplicationKpi.name.label("kpi_name"), DataSource.name.label("source_name"))
    q = q.join(ApplicationKpi, ApplicationKpi.id == KpiMapping.kpi_id)
    q = q.join(DataSource, DataSource.id == KpiMapping.source_id)

    if not include_history:
        q = q.where(KpiMapping.is_current == True)
    if kpi_id:
        q = q.where(KpiMapping.kpi_id == kpi_id)
    if source_id:
        q = q.where(KpiMapping.source_id == source_id)
    if is_active is not None:
        q = q.where(KpiMapping.is_active == is_active)

    q = q.order_by(KpiMapping.kpi_id, KpiMapping.priority_order).limit(limit).offset(offset)
    result = await db.execute(q)
    rows = result.all()

    out = []
    for r in rows:
        d = MappingOut.model_validate(r.KpiMapping)
        d.kpi_name = r.kpi_name
        d.source_name = r.source_name
        if r.KpiMapping.source_field_id:
            sf = await db.get(SourceField, r.KpiMapping.source_field_id)
            d.source_field_name = sf.field_name if sf else None
        out.append(d)
    return out


@router.post("", response_model=MappingOut, status_code=201)
async def create_mapping(body: MappingCreate, db: AsyncSession = Depends(get_db)):
    # Validate FK references
    kpi = await db.get(ApplicationKpi, body.kpi_id)
    if not kpi:
        raise HTTPException(404, f"KPI {body.kpi_id} not found.")
    source = await db.get(DataSource, body.source_id)
    if not source:
        raise HTTPException(404, f"Source {body.source_id} not found.")

    # Check for existing active mapping at same priority
    existing_q = await db.execute(
        select(KpiMapping).where(
            KpiMapping.kpi_id == body.kpi_id,
            KpiMapping.source_id == body.source_id,
            KpiMapping.priority_order == body.priority_order,
            KpiMapping.is_current == True,
        )
    )
    if existing_q.scalar_one_or_none():
        raise HTTPException(409, "A mapping already exists for this KPI/Source/Priority combination.")

    mapping = KpiMapping(id=str(uuid.uuid4()), **body.model_dump())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    d = MappingOut.model_validate(mapping)
    d.kpi_name = kpi.name
    d.source_name = source.name
    return d


@router.put("/{mapping_id}", response_model=MappingOut)
async def update_mapping(mapping_id: str, body: MappingUpdate, db: AsyncSession = Depends(get_db)):
    """
    Versioned update: marks current mapping as replaced, creates new version.
    Never overwrites — always appends.
    """
    old = await db.get(KpiMapping, mapping_id)
    if not old:
        raise HTTPException(404, "Mapping not found.")
    if not old.is_current:
        raise HTTPException(409, "Cannot update a historical mapping version.")

    # Retire old
    old.is_current = False

    # Create new version
    new_data = {
        "kpi_id": old.kpi_id,
        "source_id": old.source_id,
        "source_field_id": old.source_field_id,
        "priority_order": old.priority_order,
        "is_active": old.is_active,
        "transform_formula": old.transform_formula,
        "unit_from": old.unit_from,
        "unit_to": old.unit_to,
        "approximation_method": old.approximation_method,
        "approximation_assumption": old.approximation_assumption,
        "confidence_score": old.confidence_score,
        "version": old.version + 1,
        "is_current": True,
        "replaced_by_id": None,
        "change_note": body.change_note,
        "created_by": "user",
    }
    # Apply updates
    for k, v in body.model_dump(exclude_unset=True, exclude={"change_note"}).items():
        new_data[k] = v

    new_mapping = KpiMapping(id=str(uuid.uuid4()), **new_data)
    old.replaced_by_id = new_mapping.id
    db.add(new_mapping)
    await db.commit()
    await db.refresh(new_mapping)

    kpi = await db.get(ApplicationKpi, new_mapping.kpi_id)
    source = await db.get(DataSource, new_mapping.source_id)
    d = MappingOut.model_validate(new_mapping)
    d.kpi_name = kpi.name if kpi else None
    d.source_name = source.name if source else None
    return d


@router.delete("/{mapping_id}", status_code=204)
async def delete_mapping(mapping_id: str, db: AsyncSession = Depends(get_db)):
    mapping = await db.get(KpiMapping, mapping_id)
    if not mapping:
        raise HTTPException(404, "Mapping not found.")
    # Soft-delete: mark inactive + non-current
    mapping.is_active = False
    mapping.is_current = False
    await db.commit()


@router.get("/{mapping_id}/history", response_model=List[MappingOut])
async def get_mapping_history(mapping_id: str, db: AsyncSession = Depends(get_db)):
    """Return full version chain for a mapping (current + all predecessors)."""
    current = await db.get(KpiMapping, mapping_id)
    if not current:
        raise HTTPException(404, "Mapping not found.")

    result = await db.execute(
        select(KpiMapping)
        .where(KpiMapping.kpi_id == current.kpi_id, KpiMapping.source_id == current.source_id)
        .order_by(KpiMapping.version.desc())
    )
    rows = result.scalars().all()
    out = []
    for r in rows:
        d = MappingOut.model_validate(r)
        out.append(d)
    return out


@router.post("/preview", response_model=MappingPreview)
async def preview_mapping(body: MappingCreate, db: AsyncSession = Depends(get_db)):
    """Preview how source field values would look when mapped to a KPI."""
    kpi = await db.get(ApplicationKpi, body.kpi_id)
    source = await db.get(DataSource, body.source_id)
    if not kpi or not source:
        raise HTTPException(404, "KPI or source not found.")

    sf = None
    samples = []
    if body.source_field_id:
        sf = await db.get(SourceField, body.source_field_id)
        if sf and sf.sample_values:
            samples = sf.sample_values

    # Apply transform preview if formula provided
    transformed = []
    if body.transform_formula and samples:
        for s in samples[:5]:
            try:
                val = eval(body.transform_formula.replace("value", str(s)))
                transformed.append(round(val, 4) if isinstance(val, float) else val)
            except Exception:
                transformed.append(None)

    return MappingPreview(
        kpi_name=kpi.name,
        source_name=source.name,
        field_name=sf.field_name if sf else "(no field selected)",
        sample_values=samples[:5],
        transform_formula=body.transform_formula,
        transformed_samples=transformed or None,
        confidence_score=body.confidence_score,
    )


@router.post("/bulk-upload")
async def bulk_upload_mappings(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    CSV upload: columns = kpi_slug, source_name, field_name, priority_order,
    transform_formula, approximation_method, confidence_score
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Upload must be a .csv file.")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    created, errors = 0, []

    for i, row in enumerate(reader, start=2):
        try:
            # Resolve KPI by slug
            kpi_q = await db.execute(
                select(ApplicationKpi).where(ApplicationKpi.slug == row.get("kpi_slug", "").strip())
            )
            kpi = kpi_q.scalar_one_or_none()
            if not kpi:
                errors.append({"row": i, "error": f"KPI slug '{row.get('kpi_slug')}' not found."})
                continue

            # Resolve source by name
            src_q = await db.execute(
                select(DataSource).where(DataSource.name == row.get("source_name", "").strip())
            )
            source = src_q.scalar_one_or_none()
            if not source:
                errors.append({"row": i, "error": f"Source '{row.get('source_name')}' not found."})
                continue

            mapping = KpiMapping(
                id=str(uuid.uuid4()),
                kpi_id=kpi.id,
                source_id=source.id,
                priority_order=int(row.get("priority_order", 1)),
                transform_formula=row.get("transform_formula") or None,
                approximation_method=row.get("approximation_method") or None,
                confidence_score=float(row["confidence_score"]) if row.get("confidence_score") else None,
                is_current=True,
                is_active=True,
                created_by="bulk_upload",
            )
            db.add(mapping)
            created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    await db.commit()
    return {"created": created, "errors": errors, "total_rows": i}
