"""
BaseIngester — abstract base class for all data ingesters.

Every concrete ingester (GLEIF, Climate TRACE, NGFS, SEC EDGAR, etc.)
inherits from this class and implements the four pipeline stages:
  1. fetch()    — pull raw data from the external source
  2. validate() — check raw data quality / schema
  3. transform()— normalize to platform reference schema
  4. load()     — write to PostgreSQL dh_reference_data / domain tables

The run() method orchestrates these stages with error handling, timing,
and sync-job tracking via the DhSyncJob ORM model.
"""

from __future__ import annotations

import abc
import logging
import time
import traceback
import uuid as _uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from db.models.ingestion import DhDataSource, DhSyncJob, IngestionStatus

logger = logging.getLogger(__name__)


# ── Result container ─────────────────────────────────────────────────────────

@dataclass
class IngestionResult:
    """Returned by run() — summarises what happened."""
    source_id: str
    job_id: str
    status: str = "success"
    rows_fetched: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_skipped: int = 0
    rows_failed: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    error_detail: Optional[Dict] = None
    validation_errors: List[Dict] = field(default_factory=list)
    log_lines: List[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.rows_inserted + self.rows_updated + self.rows_skipped + self.rows_failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "job_id": self.job_id,
            "status": self.status,
            "rows_fetched": self.rows_fetched,
            "rows_inserted": self.rows_inserted,
            "rows_updated": self.rows_updated,
            "rows_skipped": self.rows_skipped,
            "rows_failed": self.rows_failed,
            "duration_seconds": round(self.duration_seconds, 2),
            "error_message": self.error_message,
            "validation_errors_count": len(self.validation_errors),
        }


# ── Abstract Base Ingester ───────────────────────────────────────────────────

class BaseIngester(abc.ABC):
    """
    Abstract base for all data ingesters.

    Subclass and implement:
      - source_id       (class-level str: must match dh_data_sources.id)
      - display_name    (class-level str: human-friendly name)
      - fetch(db)       → raw data from external API / file
      - validate(raw)   → cleaned / validated data
      - transform(data) → list of dicts ready for DB insert
      - load(db, rows)  → write to PostgreSQL

    Optional overrides:
      - pre_run(db)     — setup before the pipeline runs
      - post_run(db, result) — cleanup / post-processing
      - get_sync_schedule() — return cron expression for scheduler
    """

    # ── Subclass must set these ──────────────────────────────────────────
    source_id: str = ""
    display_name: str = ""
    default_schedule: str = ""  # e.g. "0 2 * * *" for 2 AM daily

    # ── Configuration ────────────────────────────────────────────────────
    max_retries: int = 2
    retry_delay_seconds: float = 5.0
    timeout_seconds: float = 300.0      # 5 min default
    batch_size: int = 500

    def __init__(self):
        self._log_buffer: List[str] = []

    # ── Logging helper ───────────────────────────────────────────────────

    def log(self, msg: str, level: str = "info"):
        """Buffer a log line and emit to Python logger."""
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        line = f"[{ts}] [{self.source_id}] {msg}"
        self._log_buffer.append(line)
        getattr(logger, level, logger.info)(line)

    # ── Pipeline stages (abstract) ───────────────────────────────────────

    @abc.abstractmethod
    def fetch(self, db: Session) -> Any:
        """
        Pull raw data from the external source.

        Returns whatever raw structure the source provides (list of dicts,
        DataFrame, XML tree, etc.). The return value is passed to validate().

        Raise on unrecoverable errors (network failure, auth error).
        """
        ...

    def validate(self, raw_data: Any) -> Any:
        """
        Validate and clean raw data.

        Default implementation passes data through unchanged.
        Override to add schema validation, deduplication, null checks, etc.

        Returns cleaned data (same type or different) passed to transform().
        Also return a list of validation error dicts if needed.
        """
        return raw_data

    @abc.abstractmethod
    def transform(self, validated_data: Any) -> List[Dict[str, Any]]:
        """
        Transform validated data into a list of dicts matching the target
        DB schema (dh_reference_data or domain-specific tables).

        Each dict should have keys matching the target table columns.
        """
        ...

    @abc.abstractmethod
    def load(self, db: Session, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Write transformed rows to PostgreSQL.

        Returns a dict with counts: {"inserted": N, "updated": N, "skipped": N, "failed": N}
        """
        ...

    # ── Optional hooks ───────────────────────────────────────────────────

    def pre_run(self, db: Session):
        """Optional setup before the pipeline runs."""
        pass

    def post_run(self, db: Session, result: IngestionResult):
        """Optional cleanup after the pipeline completes."""
        pass

    def get_sync_schedule(self) -> Optional[str]:
        """Return cron expression for scheduled runs. None = manual only."""
        return self.default_schedule or None

    # ── Main orchestration ───────────────────────────────────────────────

    def run(self, db: Session, triggered_by: str = "manual") -> IngestionResult:
        """
        Execute the full ingestion pipeline:
          pre_run → fetch → validate → transform → load → post_run

        Creates a DhSyncJob record to track the run.
        """
        self._log_buffer = []
        job_id = f"job_{_uuid.uuid4().hex[:12]}"
        result = IngestionResult(source_id=self.source_id, job_id=job_id)
        t0 = time.time()

        # Create sync job record
        sync_job = DhSyncJob(
            id=job_id,
            source_id=self.source_id,
            triggered_by=triggered_by,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        try:
            db.add(sync_job)
            db.commit()
        except Exception:
            db.rollback()
            self.log("Warning: could not create sync job record", "warning")

        try:
            # Pre-run hook
            self.log(f"Starting ingestion: {self.display_name}")
            self.pre_run(db)

            # Stage 1: Fetch
            self.log("Stage 1/4: Fetching data from source...")
            raw_data = self.fetch(db)
            if raw_data is None:
                self.log("Fetch returned None — nothing to process", "warning")
                result.status = "success"
                result.duration_seconds = time.time() - t0
                self._complete_job(db, sync_job, result)
                return result

            # Stage 2: Validate
            self.log("Stage 2/4: Validating data...")
            validated = self.validate(raw_data)

            # Stage 3: Transform
            self.log("Stage 3/4: Transforming data...")
            rows = self.transform(validated)
            result.rows_fetched = len(rows) if isinstance(rows, list) else 0
            self.log(f"Transformed {result.rows_fetched} rows")

            if not rows:
                self.log("No rows to load after transform")
                result.status = "success"
                result.duration_seconds = time.time() - t0
                self._complete_job(db, sync_job, result)
                return result

            # Stage 4: Load
            self.log("Stage 4/4: Loading data into database...")
            counts = self.load(db, rows)
            result.rows_inserted = counts.get("inserted", 0)
            result.rows_updated = counts.get("updated", 0)
            result.rows_skipped = counts.get("skipped", 0)
            result.rows_failed = counts.get("failed", 0)

            # Determine final status
            if result.rows_failed > 0 and result.rows_inserted == 0:
                result.status = "failed"
            elif result.rows_failed > 0:
                result.status = "partial"
            else:
                result.status = "success"

            # Post-run hook
            self.post_run(db, result)
            self.log(f"Ingestion complete: {result.rows_inserted} inserted, "
                     f"{result.rows_updated} updated, {result.rows_skipped} skipped, "
                     f"{result.rows_failed} failed")

        except Exception as exc:
            result.status = "failed"
            result.error_message = str(exc)
            result.error_detail = {"traceback": traceback.format_exc()}
            self.log(f"Ingestion failed: {exc}", "error")

        finally:
            result.duration_seconds = time.time() - t0
            result.log_lines = list(self._log_buffer)
            self._complete_job(db, sync_job, result)

        return result

    # ── Internal helpers ─────────────────────────────────────────────────

    def _complete_job(self, db: Session, job: DhSyncJob, result: IngestionResult):
        """Update the DhSyncJob record with final results."""
        try:
            job.status = result.status
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = result.duration_seconds
            job.rows_fetched = result.rows_fetched
            job.rows_inserted = result.rows_inserted
            job.rows_updated = result.rows_updated
            job.rows_skipped = result.rows_skipped
            job.rows_failed = result.rows_failed
            job.error_message = result.error_message
            job.error_detail = result.error_detail
            job.validation_errors = result.validation_errors if result.validation_errors else None
            job.log_output = "\n".join(result.log_lines)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning(f"Could not update sync job {result.job_id}: {exc}")

        # Also update source last_synced_at
        try:
            source = db.get(DhDataSource, self.source_id)
            if source:
                source.last_synced_at = datetime.now(timezone.utc)
                source.last_sync_status = result.status
                source.last_sync_error = result.error_message
                db.commit()
        except Exception:
            db.rollback()
