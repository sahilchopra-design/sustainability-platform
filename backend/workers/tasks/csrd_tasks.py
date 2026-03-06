"""
CSRD PDF extraction background task.

Called after a PDF is saved to disk. Pipeline:
  1. Read PDF bytes from file_path
  2. CSRDExtractor  → structured extraction_result dict
  3. CSRDIngestService → persist to csrd_* tables
  4. Update csrd_report_uploads.status + extraction_summary JSON
"""

import logging
from pathlib import Path

from db.postgres import SessionLocal
from db.models.csrd_models import CsrdReportUpload
from services.csrd_extractor import CSRDExtractor
from services.csrd_ingest_service import CSRDIngestService

logger = logging.getLogger(__name__)


def process_csrd_report_task(report_id: str):
    """Background task: extract ESRS KPIs from a PDF and persist to DB."""
    db = SessionLocal()
    try:
        report = db.query(CsrdReportUpload).filter(CsrdReportUpload.id == report_id).first()
        if not report:
            logger.error(f"CSRD report not found: {report_id}")
            return

        report.status = "processing"
        db.commit()

        pdf_path = Path(report.file_path)
        if not pdf_path.exists():
            report.status = "failed"
            report.error_message = f"File not found: {report.file_path}"
            db.commit()
            return

        pdf_bytes = pdf_path.read_bytes()

        extractor = CSRDExtractor()
        extraction_result = extractor.extract_from_bytes(pdf_bytes, report.filename)

        # Extractor returns dict with "extracted_kpis", "entity_name" etc.
        # It does NOT set a "success" key — check for real failure instead.
        if extraction_result.get("error") and not extraction_result.get("extracted_kpis"):
            report.status = "failed"
            report.error_message = extraction_result.get("error", "Extraction failed")
            db.commit()
            return

        # Honor user-supplied overrides
        if report.entity_name_override:
            extraction_result["entity_name"] = report.entity_name_override
        if report.reporting_year_override:
            extraction_result["reporting_year"] = report.reporting_year_override

        ingest = CSRDIngestService(db)
        summary = ingest.ingest(
            extraction_result=extraction_result,
            report_filename=report.filename,
            primary_sector=report.primary_sector or "other",
            country_iso=report.country_iso or "UNK",
            submitted_by=report.uploaded_by or "pdf_pipeline",
        )

        report.status = "completed"
        report.entity_registry_id = summary.get("entity_registry_id")
        report.kpis_extracted = summary.get("kpis_inserted", 0)
        report.kpis_updated = summary.get("kpis_updated", 0)
        report.gaps_found = summary.get("gaps_inserted", 0)
        report.lineage_entries = summary.get("lineage_inserted", 0)
        report.extraction_summary = {
            **summary,
            "validation_summary": extraction_result.get("validation_summary", {}),
            "entity_name_detected": extraction_result.get("entity_name"),
            "reporting_year_detected": extraction_result.get("reporting_year"),
            "indicators_attempted": len(extraction_result.get("extracted_kpis", {})),
            "mandatory_gaps": extraction_result.get("mandatory_gaps", []),
        }
        if summary.get("errors"):
            report.error_message = "; ".join(str(e) for e in summary["errors"][:5])

        db.commit()
        logger.info(
            f"CSRD extraction done [{report_id}]: "
            f"{report.kpis_extracted} inserted, {report.kpis_updated} updated, "
            f"{report.gaps_found} gaps"
        )

    except Exception as exc:
        logger.exception(f"CSRD task failed [{report_id}]: {exc}")
        try:
            report = db.query(CsrdReportUpload).filter(CsrdReportUpload.id == report_id).first()
            if report:
                report.status = "failed"
                report.error_message = str(exc)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
