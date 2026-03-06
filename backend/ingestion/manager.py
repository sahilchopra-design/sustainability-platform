"""
IngestionManager — registry and orchestration for all data ingesters.

Maintains a registry of BaseIngester subclasses, provides methods to
run individual or batch ingestion jobs, and exposes status/history.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.ingestion import DhDataSource, DhSyncJob
from ingestion.base_ingester import BaseIngester, IngestionResult

logger = logging.getLogger(__name__)


class IngestionManager:
    """
    Central manager for all ingesters.

    Usage:
        manager = IngestionManager()
        manager.register(GleifIngester)
        manager.register(ClimateTraceIngester)
        ...
        result = manager.run_source("gleif_lei", db)
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseIngester]] = {}
        self._instances: Dict[str, BaseIngester] = {}
        self._running: Dict[str, threading.Thread] = {}
        self._last_results: Dict[str, IngestionResult] = {}
        self._lock = threading.Lock()

    # ── Registration ─────────────────────────────────────────────────────

    def register(self, ingester_cls: Type[BaseIngester]):
        """Register an ingester class by its source_id."""
        sid = ingester_cls.source_id
        if not sid:
            raise ValueError(f"{ingester_cls.__name__} has no source_id set")
        self._registry[sid] = ingester_cls
        self._instances[sid] = ingester_cls()
        logger.info(f"Registered ingester: {sid} ({ingester_cls.display_name})")

    def unregister(self, source_id: str):
        """Remove an ingester from the registry."""
        self._registry.pop(source_id, None)
        self._instances.pop(source_id, None)

    # ── Discovery ────────────────────────────────────────────────────────

    @property
    def registered_sources(self) -> List[str]:
        """Return list of registered source_ids."""
        return list(self._registry.keys())

    def get_ingester(self, source_id: str) -> Optional[BaseIngester]:
        """Get an ingester instance by source_id."""
        return self._instances.get(source_id)

    def list_ingesters(self) -> List[Dict[str, Any]]:
        """Return info about all registered ingesters."""
        results = []
        for sid, inst in self._instances.items():
            results.append({
                "source_id": sid,
                "display_name": inst.display_name,
                "schedule": inst.get_sync_schedule(),
                "is_running": sid in self._running,
                "last_result": self._last_results.get(sid, {}).to_dict()
                    if sid in self._last_results else None,
            })
        return results

    # ── Execution ────────────────────────────────────────────────────────

    def run_source(
        self,
        source_id: str,
        db: Session,
        triggered_by: str = "manual",
    ) -> IngestionResult:
        """
        Run a specific ingester synchronously.

        Returns the IngestionResult with counts and status.
        """
        ingester = self._instances.get(source_id)
        if not ingester:
            return IngestionResult(
                source_id=source_id,
                job_id="",
                status="failed",
                error_message=f"No ingester registered for source_id={source_id}",
            )

        with self._lock:
            if source_id in self._running:
                return IngestionResult(
                    source_id=source_id,
                    job_id="",
                    status="failed",
                    error_message=f"Ingester {source_id} is already running",
                )

        result = ingester.run(db, triggered_by=triggered_by)
        self._last_results[source_id] = result
        return result

    def run_source_async(
        self,
        source_id: str,
        triggered_by: str = "scheduler",
    ):
        """
        Run a specific ingester in a background thread.

        Uses a fresh DB session from the session factory.
        """
        ingester = self._instances.get(source_id)
        if not ingester:
            logger.error(f"No ingester registered for source_id={source_id}")
            return

        with self._lock:
            if source_id in self._running:
                logger.warning(f"Ingester {source_id} already running, skipping")
                return

        def _worker():
            try:
                db_gen = get_db()
                db = next(db_gen)
                try:
                    with self._lock:
                        self._running[source_id] = threading.current_thread()
                    result = ingester.run(db, triggered_by=triggered_by)
                    self._last_results[source_id] = result
                    logger.info(
                        f"Async ingestion {source_id} finished: "
                        f"{result.status} ({result.rows_inserted} inserted)"
                    )
                finally:
                    try:
                        next(db_gen, None)
                    except StopIteration:
                        pass
            except Exception as exc:
                logger.error(f"Async ingestion {source_id} failed: {exc}")
            finally:
                with self._lock:
                    self._running.pop(source_id, None)

        thread = threading.Thread(
            target=_worker,
            name=f"ingester-{source_id}",
            daemon=True,
        )
        thread.start()
        logger.info(f"Started async ingestion for {source_id}")

    def run_all(
        self,
        db: Session,
        triggered_by: str = "manual",
        only_enabled: bool = True,
    ) -> List[IngestionResult]:
        """
        Run all registered ingesters sequentially.

        If only_enabled=True, checks dh_data_sources.sync_enabled flag.
        """
        results = []
        for sid in self._registry:
            if only_enabled:
                source = db.query(DhDataSource).filter(DhDataSource.id == sid).first()
                if source and not source.sync_enabled:
                    logger.info(f"Skipping disabled source: {sid}")
                    continue

            result = self.run_source(sid, db, triggered_by=triggered_by)
            results.append(result)

        return results

    # ── Status queries ───────────────────────────────────────────────────

    def get_status(self, source_id: str) -> Dict[str, Any]:
        """Get current status of an ingester."""
        ingester = self._instances.get(source_id)
        if not ingester:
            return {"error": f"Unknown source_id: {source_id}"}

        return {
            "source_id": source_id,
            "display_name": ingester.display_name,
            "schedule": ingester.get_sync_schedule(),
            "is_running": source_id in self._running,
            "last_result": self._last_results.get(source_id, IngestionResult(
                source_id=source_id, job_id=""
            )).to_dict(),
        }

    def get_running(self) -> List[str]:
        """Return source_ids of currently running ingesters."""
        with self._lock:
            return list(self._running.keys())

    # ── Job history (from DB) ────────────────────────────────────────────

    @staticmethod
    def get_job_history(
        db: Session,
        source_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Query DhSyncJob history from the database."""
        q = db.query(DhSyncJob)
        if source_id:
            q = q.filter(DhSyncJob.source_id == source_id)
        if status:
            q = q.filter(DhSyncJob.status == status)

        total = q.count()
        jobs = q.order_by(desc(DhSyncJob.created_at)).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [
                {
                    "id": j.id,
                    "source_id": j.source_id,
                    "triggered_by": j.triggered_by,
                    "status": j.status,
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "duration_seconds": j.duration_seconds,
                    "rows_fetched": j.rows_fetched,
                    "rows_inserted": j.rows_inserted,
                    "rows_updated": j.rows_updated,
                    "rows_skipped": j.rows_skipped,
                    "rows_failed": j.rows_failed,
                    "error_message": j.error_message,
                }
                for j in jobs
            ],
        }

    @staticmethod
    def get_source_stats(db: Session) -> Dict[str, Any]:
        """Get aggregate ingestion stats across all sources."""
        total_sources = db.query(DhDataSource).count()
        enabled_sources = db.query(DhDataSource).filter(
            DhDataSource.sync_enabled == True
        ).count()
        total_jobs = db.query(DhSyncJob).count()
        failed_jobs = db.query(DhSyncJob).filter(DhSyncJob.status == "failed").count()

        # Latest job per source
        latest_sql = text("""
            SELECT source_id, status, completed_at, rows_inserted
            FROM dh_sync_jobs
            WHERE id IN (
                SELECT DISTINCT ON (source_id) id
                FROM dh_sync_jobs
                ORDER BY source_id, created_at DESC
            )
        """)
        try:
            latest_rows = db.execute(latest_sql).mappings().all()
            latest = [
                {
                    "source_id": r["source_id"],
                    "status": r["status"],
                    "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
                    "rows_inserted": r["rows_inserted"],
                }
                for r in latest_rows
            ]
        except Exception:
            latest = []

        return {
            "total_sources": total_sources,
            "enabled_sources": enabled_sources,
            "total_sync_jobs": total_jobs,
            "failed_jobs": failed_jobs,
            "latest_per_source": latest,
        }


# ── Singleton ────────────────────────────────────────────────────────────────
# Global manager instance — imported by scheduler and API routes
ingestion_manager = IngestionManager()
