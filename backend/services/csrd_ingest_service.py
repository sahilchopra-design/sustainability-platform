"""
CSRD data ingestion service.

Takes the structured output from CSRDExtractor and persists to:
  - csrd_entity_registry   (one record per reporting entity)
  - csrd_kpi_values        (one row per entity × indicator_code × year, idempotent)
  - csrd_gap_tracker       (mandatory disclosures not found)
  - csrd_data_lineage      (audit trail for each extracted KPI)

All inserts are idempotent — safe to re-run on the same PDF.
"""

import uuid
import logging
from datetime import date, datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# PCAF data quality score: 1 (best, primary_measurement) → 5 (worst, management_estimate)
_CONFIDENCE_TO_DQ = [(0.9, 1), (0.75, 2), (0.60, 3), (0.45, 4), (0.0, 5)]


def _dq_score(confidence: float) -> int:
    for threshold, score in _CONFIDENCE_TO_DQ:
        if confidence >= threshold:
            return score
    return 5


class CSRDIngestService:
    """Persist one PDF extraction result to the CSRD database tables."""

    def __init__(self, db: Session):
        self.db = db

    # -----------------------------------------------------------------------
    # Main pipeline entry point
    # -----------------------------------------------------------------------

    def ingest(
        self,
        extraction_result: dict,
        report_filename: str,
        entity_name_override: Optional[str] = None,
        reporting_year_override: Optional[int] = None,
        primary_sector: str = "other",
        country_iso: str = "UNK",
        submitted_by: str = "pdf_pipeline",
    ) -> dict:
        """
        Persist one extraction result to the DB.

        Returns summary dict with counts and any errors.
        """
        summary = {
            "entity_registry_id": None,
            "kpis_inserted": 0,
            "kpis_updated": 0,
            "gaps_inserted": 0,
            "lineage_inserted": 0,
            "errors": [],
        }

        entity_name = (
            entity_name_override
            or extraction_result.get("entity_name")
            or "Unknown Entity"
        )
        reporting_year = (
            reporting_year_override
            or extraction_result.get("reporting_year")
            or datetime.now().year - 1
        )

        # Validate sector value against DB check constraint
        valid_sectors = {
            "financial_institution", "energy_developer", "technology",
            "supply_chain", "real_estate", "agriculture", "mining",
            "insurance", "asset_manager", "other",
        }
        if primary_sector not in valid_sectors:
            primary_sector = "other"

        # 1. Upsert entity
        entity_id = self._upsert_entity(entity_name, primary_sector, country_iso)
        if not entity_id:
            summary["errors"].append("Failed to create/find entity registry record")
            return summary
        summary["entity_registry_id"] = str(entity_id)

        # 2. Persist KPI values + lineage
        for indicator_code, kpi in extraction_result.get("extracted_kpis", {}).items():
            try:
                kpi_id, was_updated = self._upsert_kpi_value(
                    entity_id=entity_id,
                    indicator_code=indicator_code,
                    reporting_year=reporting_year,
                    kpi=kpi,
                    report_filename=report_filename,
                    submitted_by=submitted_by,
                )
                if was_updated:
                    summary["kpis_updated"] += 1
                else:
                    summary["kpis_inserted"] += 1

                if kpi_id:
                    ok = self._insert_lineage(
                        kpi_value_id=kpi_id,
                        entity_id=entity_id,
                        indicator_code=indicator_code,
                        reporting_year=reporting_year,
                        kpi=kpi,
                        report_filename=report_filename,
                    )
                    if ok:
                        summary["lineage_inserted"] += 1

            except Exception as exc:
                msg = f"{indicator_code}: {exc}"
                logger.error(f"KPI insert failed — {msg}")
                summary["errors"].append(msg)

        # 3. Gap tracker for mandatory missing indicators
        for missing_code in extraction_result.get("mandatory_gaps", []):
            try:
                if self._upsert_gap(entity_id, missing_code, reporting_year):
                    summary["gaps_inserted"] += 1
            except Exception as exc:
                msg = f"gap:{missing_code}: {exc}"
                logger.error(f"Gap insert failed — {msg}")
                summary["errors"].append(msg)

        self.db.commit()
        return summary

    # -----------------------------------------------------------------------
    # csrd_entity_registry
    # -----------------------------------------------------------------------

    def _upsert_entity(
        self, legal_name: str, primary_sector: str, country_iso: str
    ) -> Optional[str]:
        """Return existing entity id or insert a new one."""
        try:
            row = self.db.execute(
                text(
                    "SELECT id FROM csrd_entity_registry "
                    "WHERE legal_name = :name LIMIT 1"
                ),
                {"name": legal_name},
            ).fetchone()
            if row:
                return str(row[0])

            new_id = str(uuid.uuid4())
            self.db.execute(
                text(
                    """
                    INSERT INTO csrd_entity_registry
                        (id, legal_name, primary_sector, country_iso,
                         is_in_scope_csrd, created_by)
                    VALUES
                        (:id, :name, :sector, :country, true, 'pdf_pipeline')
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "id": new_id,
                    "name": legal_name,
                    "sector": primary_sector,
                    "country": country_iso[:3] if country_iso else "UNK",
                },
            )
            return new_id
        except Exception as exc:
            logger.error(f"Entity upsert failed: {exc}")
            return None

    # -----------------------------------------------------------------------
    # csrd_kpi_values
    # -----------------------------------------------------------------------

    def _upsert_kpi_value(
        self,
        entity_id: str,
        indicator_code: str,
        reporting_year: int,
        kpi: dict,
        report_filename: str,
        submitted_by: str,
    ) -> Tuple[Optional[str], bool]:
        """
        INSERT or UPDATE csrd_kpi_values.
        Returns (kpi_uuid, was_updated).
        """
        row = self.db.execute(
            text(
                """
                SELECT id FROM csrd_kpi_values
                WHERE entity_registry_id = :eid
                  AND indicator_code      = :code
                  AND reporting_year      = :year
                """
            ),
            {"eid": entity_id, "code": indicator_code, "year": reporting_year},
        ).fetchone()

        numeric_val = kpi.get("numeric_value")
        text_val    = kpi.get("text_value")
        unit        = kpi.get("unit", "")
        confidence  = float(kpi.get("confidence", 0.5))
        page_ref    = kpi.get("page_number")
        method      = kpi.get("extraction_method", "nlp_extraction")
        dq          = _dq_score(confidence)

        if row:
            kpi_id = str(row[0])
            self.db.execute(
                text(
                    """
                    UPDATE csrd_kpi_values
                    SET numeric_value        = :num,
                        text_value           = :txt,
                        unit                 = :unit,
                        data_quality_score   = :dq,
                        data_source_type     = 'third_party',
                        data_source_name     = :src_name,
                        report_page_reference = :pg,
                        extraction_method    = :method,
                        updated_at           = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    "num": numeric_val, "txt": text_val, "unit": unit,
                    "dq": dq, "src_name": report_filename,
                    "pg": str(page_ref) if page_ref else None,
                    "method": method, "id": kpi_id,
                },
            )
            return kpi_id, True

        kpi_id = str(uuid.uuid4())
        self.db.execute(
            text(
                """
                INSERT INTO csrd_kpi_values
                    (id, entity_registry_id, indicator_code, reporting_year,
                     numeric_value, text_value, unit, data_quality_score,
                     data_source_type, data_source_name,
                     report_page_reference, extraction_method,
                     submitted_by, status)
                VALUES
                    (:id, :eid, :code, :year,
                     :num, :txt, :unit, :dq,
                     'third_party', :src_name,
                     :pg, :method, :submitted_by, 'draft')
                """
            ),
            {
                "id": kpi_id, "eid": entity_id,
                "code": indicator_code, "year": reporting_year,
                "num": numeric_val, "txt": text_val, "unit": unit,
                "dq": dq, "src_name": report_filename,
                "pg": str(page_ref) if page_ref else None,
                "method": method, "submitted_by": submitted_by,
            },
        )
        return kpi_id, False

    # -----------------------------------------------------------------------
    # csrd_gap_tracker
    # -----------------------------------------------------------------------

    def _upsert_gap(
        self, entity_id: str, indicator_code: str, reporting_year: int
    ) -> bool:
        """Insert gap entry if not already tracked (open or in_progress)."""
        existing = self.db.execute(
            text(
                """
                SELECT id FROM csrd_gap_tracker
                WHERE entity_registry_id    = :eid
                  AND indicator_code        = :code
                  AND reporting_year_target = :year
                  AND gap_status            IN ('open', 'in_progress')
                """
            ),
            {"eid": entity_id, "code": indicator_code, "year": reporting_year},
        ).fetchone()

        if existing:
            return False

        self.db.execute(
            text(
                """
                INSERT INTO csrd_gap_tracker
                    (id, entity_registry_id, assessment_date, reporting_year_target,
                     indicator_code, framework, current_status, target_status,
                     gap_description, gap_category, priority,
                     regulatory_risk_flag, gap_status)
                VALUES
                    (:id, :eid, :adate, :year,
                     :code, 'CSRD', 'data_not_available', 'complete',
                     :desc, 'data_availability', 'high', true, 'open')
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "eid": entity_id,
                "adate": date.today().isoformat(),
                "year": reporting_year,
                "code": indicator_code,
                "desc": (
                    f"Mandatory ESRS indicator '{indicator_code}' not found "
                    "in PDF extraction. Manual data entry required."
                ),
            },
        )
        return True

    # -----------------------------------------------------------------------
    # csrd_data_lineage
    # -----------------------------------------------------------------------

    def _insert_lineage(
        self,
        kpi_value_id: str,
        entity_id: str,
        indicator_code: str,
        reporting_year: int,
        kpi: dict,
        report_filename: str,
    ) -> bool:
        """Insert immutable audit-trail record for extracted KPI."""
        try:
            multiplier = kpi.get("multiplier_applied", 1.0)
            transformation = (
                f"unit_conversion: {kpi.get('raw_unit', '')} → "
                f"{kpi.get('unit', '')} (×{multiplier}); "
                f"confidence: {kpi.get('confidence', 0):.2f}; "
                f"method: {kpi.get('extraction_method', 'regex')}"
            )
            self.db.execute(
                text(
                    """
                    INSERT INTO csrd_data_lineage
                        (id, kpi_value_id, entity_registry_id,
                         indicator_code, reporting_year,
                         source_system, source_document_url,
                         source_extraction_date, raw_value, raw_unit,
                         transformation_applied, output_value, output_unit,
                         tool_name, tool_version, calculated_by)
                    VALUES
                        (:id, :kv_id, :eid,
                         :code, :year,
                         'pdf_extraction', :doc_name,
                         :extract_dt, :raw_val, :raw_unit,
                         :transform, :out_val, :out_unit,
                         'csrd_extractor', '1.0', 'pdf_pipeline')
                    """
                ),
                {
                    "id":          str(uuid.uuid4()),
                    "kv_id":       kpi_value_id,
                    "eid":         entity_id,
                    "code":        indicator_code,
                    "year":        reporting_year,
                    "doc_name":    report_filename,
                    "extract_dt":  datetime.now(timezone.utc).isoformat(),
                    "raw_val":     str(kpi.get("raw_value_str", "")),
                    "raw_unit":    kpi.get("raw_unit", ""),
                    "transform":   transformation,
                    "out_val":     kpi.get("numeric_value"),
                    "out_unit":    kpi.get("unit", ""),
                },
            )
            return True
        except Exception as exc:
            logger.error(f"Lineage insert failed: {exc}")
            return False
