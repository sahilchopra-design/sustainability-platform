"""
CSRD PDF Report upload, extraction, and query API.

Endpoints
---------
POST   /api/csrd/reports/upload           Upload PDF → trigger extraction
GET    /api/csrd/reports                  List all report uploads
GET    /api/csrd/reports/{report_id}      Single report + extraction summary
POST   /api/csrd/reports/{report_id}/reprocess   Re-run extraction
POST   /api/csrd/ingest/bulk              Re-process all pending/failed PDFs

GET    /api/csrd/entities                 List registry entities
GET    /api/csrd/entities/{entity_id}/kpis    KPI time-series
GET    /api/csrd/entities/{entity_id}/gaps    Gap tracker
GET    /api/csrd/entities/{entity_id}/dashboard   Full dashboard JSON
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Query,
    BackgroundTasks, status,
)
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from db.base import get_db
from db.models.csrd_models import CsrdReportUpload
from workers.tasks.csrd_tasks import process_csrd_report_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/csrd", tags=["csrd"])

# PDF storage directory — created on first use
CSRD_UPLOAD_DIR = Path(
    os.getenv("CSRD_UPLOAD_DIR", "reports_output/csrd_pdfs")
)

MAX_PDF_SIZE = 100 * 1024 * 1024   # 100 MB


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ReportSummary(BaseModel):
    id: str
    filename: str
    status: str
    entity_name_detected: Optional[str] = None
    reporting_year_detected: Optional[int] = None
    kpis_extracted: int = 0
    kpis_updated: int = 0
    gaps_found: int = 0
    lineage_entries: int = 0
    error_message: Optional[str] = None
    primary_sector: Optional[str] = None
    country_iso: Optional[str] = None
    entity_registry_id: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class BulkIngestResult(BaseModel):
    triggered: int
    skipped: int
    report_ids: List[str]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _report_to_summary(r: CsrdReportUpload) -> dict:
    summary = r.extraction_summary or {}
    return {
        "id": r.id,
        "filename": r.filename,
        "file_size_bytes": r.file_size_bytes,
        "status": r.status,
        "entity_name_detected": summary.get("entity_name_detected"),
        "reporting_year_detected": summary.get("reporting_year_detected"),
        "kpis_extracted": r.kpis_extracted or 0,
        "kpis_updated": r.kpis_updated or 0,
        "gaps_found": r.gaps_found or 0,
        "lineage_entries": r.lineage_entries or 0,
        "error_message": r.error_message,
        "primary_sector": r.primary_sector,
        "country_iso": r.country_iso,
        "entity_registry_id": r.entity_registry_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "validation_summary": summary.get("validation_summary", {}),
        "mandatory_gaps": summary.get("mandatory_gaps", []),
        "indicators_attempted": summary.get("indicators_attempted", 0),
    }


# ---------------------------------------------------------------------------
# Upload endpoints
# ---------------------------------------------------------------------------

@router.post("/reports/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_csrd_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSRD sustainability report PDF"),
    entity_name: Optional[str] = Query(None, description="Override detected entity name"),
    reporting_year: Optional[int] = Query(None, description="Override detected reporting year"),
    primary_sector: str = Query("other", description=(
        "financial_institution | energy_developer | technology | "
        "supply_chain | real_estate | agriculture | mining | "
        "insurance | asset_manager | other"
    )),
    country_iso: str = Query("UNK", description="3-letter ISO country code"),
    uploaded_by: str = Query("user", description="Uploader identifier"),
    db: Session = Depends(get_db),
):
    """
    Upload a CSRD/ESG sustainability report PDF for automated ESRS KPI extraction.

    The endpoint accepts any PDF and runs:
    - pdfplumber text + table extraction
    - Regex-based ESRS indicator matching (Scope 1/2/3, water, waste, headcount, etc.)
    - Confidence scoring and unit normalisation
    - Idempotent DB persistence to csrd_kpi_values, csrd_gap_tracker, csrd_data_lineage

    Returns a report_id immediately; use GET /api/csrd/reports/{report_id} to poll status.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted (.pdf)")

    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(413, f"PDF exceeds {MAX_PDF_SIZE // (1024*1024)} MB limit")

    CSRD_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    report_id = str(uuid.uuid4())
    safe_name = f"{report_id}_{file.filename.replace(' ', '_')}"
    file_path = CSRD_UPLOAD_DIR / safe_name

    file_path.write_bytes(content)

    valid_sectors = {
        "financial_institution", "energy_developer", "technology",
        "supply_chain", "real_estate", "agriculture", "mining",
        "insurance", "asset_manager", "other",
    }
    if primary_sector not in valid_sectors:
        primary_sector = "other"

    record = CsrdReportUpload(
        id=report_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size_bytes=len(content),
        entity_name_override=entity_name,
        reporting_year_override=reporting_year,
        primary_sector=primary_sector,
        country_iso=country_iso[:3].upper() if country_iso else "UNK",
        uploaded_by=uploaded_by,
        status="uploaded",
    )
    db.add(record)
    db.commit()

    background_tasks.add_task(process_csrd_report_task, report_id)

    return {
        "report_id": report_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Extraction queued. Poll GET /api/csrd/reports/{report_id} for status.",
    }


@router.get("/reports")
def list_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all CSRD report uploads, newest first."""
    q = db.query(CsrdReportUpload).order_by(CsrdReportUpload.created_at.desc())
    if status_filter:
        q = q.filter(CsrdReportUpload.status == status_filter)
    reports = q.limit(limit).all()
    return [_report_to_summary(r) for r in reports]


@router.get("/reports/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Get a single report upload record with full extraction summary."""
    r = db.query(CsrdReportUpload).filter(CsrdReportUpload.id == report_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    return _report_to_summary(r)


@router.post("/reports/{report_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
def reprocess_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Re-trigger ESRS extraction for an existing report (e.g. after a failed run)."""
    r = db.query(CsrdReportUpload).filter(CsrdReportUpload.id == report_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    r.status = "uploaded"
    r.error_message = None
    db.commit()
    background_tasks.add_task(process_csrd_report_task, report_id)
    return {"report_id": report_id, "status": "reprocessing"}


@router.post("/ingest/bulk", response_model=BulkIngestResult)
def bulk_ingest(
    background_tasks: BackgroundTasks,
    reprocess_failed: bool = Query(True, description="Re-trigger failed reports"),
    db: Session = Depends(get_db),
):
    """
    Trigger extraction for all uploaded or failed PDF reports that haven't
    been successfully processed yet. Useful after a fresh deploy or pdfplumber
    install to process previously uploaded PDFs.
    """
    statuses = ["uploaded", "failed"] if reprocess_failed else ["uploaded"]
    reports = (
        db.query(CsrdReportUpload)
        .filter(CsrdReportUpload.status.in_(statuses))
        .all()
    )
    triggered_ids = []
    skipped = 0
    for r in reports:
        if not Path(r.file_path).exists():
            skipped += 1
            continue
        r.status = "uploaded"
        r.error_message = None
        db.commit()
        background_tasks.add_task(process_csrd_report_task, r.id)
        triggered_ids.append(r.id)

    return BulkIngestResult(
        triggered=len(triggered_ids),
        skipped=skipped,
        report_ids=triggered_ids,
    )


# ---------------------------------------------------------------------------
# Entity / KPI query endpoints
# ---------------------------------------------------------------------------

@router.get("/entities")
def list_entities(
    sector: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all CSRD entity registry entries."""
    sql = "SELECT id, legal_name, primary_sector, country_iso, created_at FROM csrd_entity_registry"
    params: dict = {}
    if sector:
        sql += " WHERE primary_sector = :sector"
        params["sector"] = sector
    sql += " ORDER BY legal_name LIMIT :lim"
    params["lim"] = limit
    rows = db.execute(text(sql), params).fetchall()
    return [
        {
            "id": str(r[0]),
            "legal_name": r[1],
            "primary_sector": r[2],
            "country_iso": r[3],
            "created_at": r[4].isoformat() if r[4] else None,
        }
        for r in rows
    ]


@router.get("/entities/{entity_id}/kpis")
def get_entity_kpis(
    entity_id: str,
    year: Optional[int] = Query(None, description="Filter by reporting year"),
    standard: Optional[str] = Query(None, description="E1, E2, S1, G1, ..."),
    db: Session = Depends(get_db),
):
    """
    Return all extracted KPI values for a CSRD entity, with optional year / standard filter.
    """
    sql = """
        SELECT
            indicator_code, reporting_year, numeric_value, text_value,
            unit, data_quality_score, status, report_page_reference,
            extraction_method, created_at, updated_at,
            is_assured, assurance_level, coverage_pct
        FROM csrd_kpi_values
        WHERE CAST(entity_registry_id AS text) LIKE :eid
    """
    params: dict = {"eid": f"{entity_id}%"}
    if year:
        sql += " AND reporting_year = :year"
        params["year"] = year
    if standard:
        sql += " AND indicator_code LIKE :std"
        params["std"] = f"{standard}%"
    sql += " ORDER BY indicator_code, reporting_year DESC"

    rows = db.execute(text(sql), params).fetchall()
    return [
        {
            "indicator_code": r[0],
            "reporting_year": r[1],
            "numeric_value": float(r[2]) if r[2] is not None else None,
            "text_value": r[3],
            "unit": r[4],
            "data_quality_score": r[5],
            "status": r[6],
            "report_page_reference": r[7],
            "extraction_method": r[8],
            "created_at": r[9].isoformat() if r[9] else None,
            "updated_at": r[10].isoformat() if r[10] else None,
            "is_assured": r[11],
            "assurance_level": r[12],
            "coverage_pct": float(r[13]) if r[13] is not None else None,
        }
        for r in rows
    ]


@router.get("/entities/{entity_id}/gaps")
def get_entity_gaps(
    entity_id: str,
    year: Optional[int] = Query(None),
    gap_status: Optional[str] = Query(None, description="open | in_progress | closed"),
    db: Session = Depends(get_db),
):
    """Return ESRS mandatory gap tracker entries for a CSRD entity."""
    sql = """
        SELECT
            id, indicator_code, reporting_year_target, gap_status,
            gap_description, priority, regulatory_risk_flag,
            assessment_date, gap_category
        FROM csrd_gap_tracker
        WHERE CAST(entity_registry_id AS text) LIKE :eid
    """
    params: dict = {"eid": f"{entity_id}%"}
    if year:
        sql += " AND reporting_year_target = :year"
        params["year"] = year
    if gap_status:
        sql += " AND gap_status = :gs"
        params["gs"] = gap_status
    sql += " ORDER BY priority, indicator_code"

    rows = db.execute(text(sql), params).fetchall()
    return [
        {
            "id": str(r[0]),
            "indicator_code": r[1],
            "reporting_year_target": r[2],
            "gap_status": r[3],
            "gap_description": r[4],
            "priority": r[5],
            "regulatory_risk_flag": r[6],
            "assessment_date": str(r[7]) if r[7] else None,
            "gap_category": r[8],
        }
        for r in rows
    ]


@router.get("/entities/{entity_id}/dashboard")
def get_entity_dashboard(
    entity_id: str,
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Full CSRD dashboard for a single entity — entity metadata, KPI summary by
    ESRS standard, gap counts, disclosure coverage score, and recent lineage.
    """
    # Entity record
    entity_row = db.execute(
        text(
            "SELECT id, legal_name, primary_sector, country_iso, "
            "is_in_scope_csrd, csrd_first_reporting_year "
            "FROM csrd_entity_registry WHERE CAST(id AS text) LIKE :eid LIMIT 1"
        ),
        {"eid": f"{entity_id}%"},
    ).fetchone()
    if not entity_row:
        raise HTTPException(404, "Entity not found in registry")

    entity = {
        "id": str(entity_row[0]),
        "legal_name": entity_row[1],
        "primary_sector": entity_row[2],
        "country_iso": entity_row[3],
        "is_in_scope_csrd": entity_row[4],
        "csrd_first_reporting_year": entity_row[5],
    }

    # KPI counts by ESRS standard
    kpi_sql = """
        SELECT
            SPLIT_PART(indicator_code, '-', 1)  AS esrs_standard,
            reporting_year,
            COUNT(*)                             AS kpi_count,
            AVG(data_quality_score)              AS avg_dq,
            SUM(CASE WHEN is_assured THEN 1 ELSE 0 END) AS assured_count
        FROM csrd_kpi_values
        WHERE CAST(entity_registry_id AS text) LIKE :eid
    """
    kpi_params: dict = {"eid": f"{entity_id}%"}
    if year:
        kpi_sql += " AND reporting_year = :year"
        kpi_params["year"] = year
    kpi_sql += " GROUP BY esrs_standard, reporting_year ORDER BY esrs_standard, reporting_year DESC"

    kpi_rows = db.execute(text(kpi_sql), kpi_params).fetchall()
    kpi_by_standard = [
        {
            "esrs_standard": r[0],
            "reporting_year": r[1],
            "kpi_count": r[2],
            "avg_data_quality_score": round(float(r[3]), 2) if r[3] else None,
            "assured_count": r[4],
        }
        for r in kpi_rows
    ]

    # Gap summary
    gap_sql = """
        SELECT gap_status, COUNT(*) FROM csrd_gap_tracker
        WHERE CAST(entity_registry_id AS text) LIKE :eid
    """
    gap_params: dict = {"eid": f"{entity_id}%"}
    if year:
        gap_sql += " AND reporting_year_target = :year"
        gap_params["year"] = year
    gap_sql += " GROUP BY gap_status"
    gap_rows = db.execute(text(gap_sql), gap_params).fetchall()
    gap_summary = {r[0]: r[1] for r in gap_rows}

    # Total mandatory indicators = 12 (hardcoded from ESRS_INDICATORS mandatory=True)
    total_mandatory = 12
    gaps_open = gap_summary.get("open", 0) + gap_summary.get("in_progress", 0)
    kpis_disclosed = sum(r["kpi_count"] for r in kpi_by_standard)
    coverage_score = round(
        max(0.0, (total_mandatory - gaps_open) / total_mandatory) * 100, 1
    )

    # Recent lineage
    lineage_sql = """
        SELECT indicator_code, reporting_year, source_document_url,
               source_extraction_date, output_value, output_unit, tool_name
        FROM csrd_data_lineage
        WHERE CAST(entity_registry_id AS text) LIKE :eid
        ORDER BY source_extraction_date DESC
        LIMIT 20
    """
    lineage_rows = db.execute(text(lineage_sql), {"eid": f"{entity_id}%"}).fetchall()
    lineage = [
        {
            "indicator_code": r[0],
            "reporting_year": r[1],
            "source_document": r[2],
            "extraction_date": str(r[3]) if r[3] else None,
            "value": float(r[4]) if r[4] is not None else None,
            "unit": r[5],
            "tool": r[6],
        }
        for r in lineage_rows
    ]

    return {
        "entity": entity,
        "kpi_by_standard": kpi_by_standard,
        "gap_summary": gap_summary,
        "kpis_disclosed": kpis_disclosed,
        "kpi_count": kpis_disclosed,          # alias — used by test scripts
        "gaps_open": gaps_open,
        "gap_count": gaps_open,               # alias — used by test scripts
        "disclosure_coverage_score_pct": coverage_score,
        "recent_lineage": lineage,
    }


@router.get("/entities/{entity_id}/lineage")
def get_entity_lineage(
    entity_id: str,
    indicator_code: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Full audit trail (data lineage) for an entity's extracted KPIs."""
    sql = """
        SELECT
            id, kpi_value_id, indicator_code, reporting_year,
            source_document_url, source_extraction_date,
            raw_value, raw_unit, transformation_applied,
            output_value, output_unit, tool_name, tool_version, calculated_by
        FROM csrd_data_lineage
        WHERE entity_registry_id = :eid
    """
    params: dict = {"eid": entity_id}
    if indicator_code:
        sql += " AND indicator_code = :code"
        params["code"] = indicator_code
    if year:
        sql += " AND reporting_year = :year"
        params["year"] = year
    sql += " ORDER BY source_extraction_date DESC LIMIT :lim"
    params["lim"] = limit

    rows = db.execute(text(sql), params).fetchall()
    return [
        {
            "id": str(r[0]),
            "kpi_value_id": str(r[1]),
            "indicator_code": r[2],
            "reporting_year": r[3],
            "source_document": r[4],
            "extraction_date": str(r[5]) if r[5] else None,
            "raw_value": r[6],
            "raw_unit": r[7],
            "transformation_applied": r[8],
            "output_value": float(r[9]) if r[9] is not None else None,
            "output_unit": r[10],
            "tool_name": r[11],
            "tool_version": r[12],
            "calculated_by": r[13],
        }
        for r in rows
    ]
