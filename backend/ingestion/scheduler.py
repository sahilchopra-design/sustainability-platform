"""
Ingestion scheduler — APScheduler-based recurring job runner.

Uses BackgroundScheduler (thread-based) suitable for running inside
a FastAPI/uvicorn process. Each registered ingester with a cron schedule
gets a corresponding APScheduler CronTrigger job.

Start/stop is tied to the FastAPI lifespan.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# APScheduler is optional — graceful degradation if not installed
_HAS_APSCHEDULER = False
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
    _HAS_APSCHEDULER = True
except ImportError:
    BackgroundScheduler = None  # type: ignore
    CronTrigger = None  # type: ignore
    logger.warning(
        "APScheduler not installed — scheduled ingestion disabled. "
        "Install with: pip install apscheduler"
    )


class IngestionScheduler:
    """
    Wraps APScheduler BackgroundScheduler to run ingesters on cron schedules.

    Usage:
        from ingestion.manager import ingestion_manager
        scheduler = IngestionScheduler(ingestion_manager)
        scheduler.start()    # in FastAPI lifespan startup
        scheduler.stop()     # in FastAPI lifespan shutdown
    """

    def __init__(self, manager=None):
        self._manager = manager
        self._scheduler: Optional[BackgroundScheduler] = None
        self._started = False

    @property
    def is_available(self) -> bool:
        """Whether APScheduler is installed."""
        return _HAS_APSCHEDULER

    @property
    def is_running(self) -> bool:
        return self._started and self._scheduler is not None

    def start(self):
        """
        Start the scheduler and register all ingester cron jobs.

        Call this during FastAPI startup. If APScheduler is not installed,
        logs a warning and returns (manual triggers still work via API).
        """
        if not _HAS_APSCHEDULER:
            logger.warning("APScheduler not available — scheduler not started")
            return

        if self._started:
            logger.warning("Scheduler already running")
            return

        self._scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": True,       # skip missed runs, only run once
                "max_instances": 1,      # never run same ingester twice
                "misfire_grace_time": 300,  # 5 min grace for misfires
            },
            timezone="UTC",
        )

        # Listen for job events
        self._scheduler.add_listener(self._on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # Register cron jobs for each ingester with a schedule
        if self._manager:
            for source_id in self._manager.registered_sources:
                self._add_ingester_job(source_id)

        self._scheduler.start()
        self._started = True
        job_count = len(self._scheduler.get_jobs())
        logger.info(f"Ingestion scheduler started with {job_count} scheduled jobs")

    def stop(self):
        """Stop the scheduler gracefully. Call during FastAPI shutdown."""
        if self._scheduler and self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Ingestion scheduler stopped")

    def add_job(self, source_id: str):
        """Add or update a scheduled job for a specific ingester."""
        if not self._started or not self._scheduler:
            return
        self._add_ingester_job(source_id)

    def remove_job(self, source_id: str):
        """Remove a scheduled job."""
        if not self._scheduler:
            return
        job_id = f"ingest_{source_id}"
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job: {job_id}")
        except Exception:
            pass

    def list_jobs(self):
        """Return info about all scheduled jobs."""
        if not self._scheduler:
            return []
        jobs = self._scheduler.get_jobs()
        return [
            {
                "job_id": j.id,
                "source_id": j.id.replace("ingest_", ""),
                "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
                "trigger": str(j.trigger),
            }
            for j in jobs
        ]

    def get_next_runs(self):
        """Return upcoming scheduled runs sorted by time."""
        jobs = self.list_jobs()
        return sorted(
            [j for j in jobs if j["next_run"]],
            key=lambda j: j["next_run"],
        )

    # ── Internal ─────────────────────────────────────────────────────────

    def _add_ingester_job(self, source_id: str):
        """Register a cron job for one ingester."""
        if not self._manager or not self._scheduler:
            return

        ingester = self._manager.get_ingester(source_id)
        if not ingester:
            return

        schedule = ingester.get_sync_schedule()
        if not schedule:
            return

        job_id = f"ingest_{source_id}"

        try:
            # Parse cron expression: "minute hour day month day_of_week"
            parts = schedule.strip().split()
            if len(parts) != 5:
                logger.warning(f"Invalid cron for {source_id}: {schedule}")
                return

            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone="UTC",
            )

            # Replace existing job if any
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass

            self._scheduler.add_job(
                self._run_ingester,
                trigger=trigger,
                id=job_id,
                name=f"Ingest: {ingester.display_name}",
                args=[source_id],
                replace_existing=True,
            )
            logger.info(f"Scheduled {source_id} with cron: {schedule}")

        except Exception as exc:
            logger.error(f"Failed to schedule {source_id}: {exc}")

    def _run_ingester(self, source_id: str):
        """Callback for APScheduler — runs the ingester async."""
        if not self._manager:
            return
        self._manager.run_source_async(source_id, triggered_by="scheduler")

    @staticmethod
    def _on_job_event(event):
        """Handle APScheduler job events."""
        if hasattr(event, "exception") and event.exception:
            logger.error(f"Scheduled job {event.job_id} failed: {event.exception}")
        else:
            logger.debug(f"Scheduled job {event.job_id} executed successfully")


# ── Singleton ────────────────────────────────────────────────────────────────

ingestion_scheduler: Optional[IngestionScheduler] = None


def get_scheduler(manager=None) -> IngestionScheduler:
    """Get or create the global scheduler instance."""
    global ingestion_scheduler
    if ingestion_scheduler is None:
        from ingestion.manager import ingestion_manager
        ingestion_scheduler = IngestionScheduler(manager or ingestion_manager)
    return ingestion_scheduler
