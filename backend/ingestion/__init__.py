"""
Ingestion framework — BaseIngester, scheduler, and job manager.

Provides the abstract base class for all data ingesters, an APScheduler-based
scheduler for recurring sync jobs, and a manager for registration and orchestration.
"""

from ingestion.base_ingester import BaseIngester
from ingestion.manager import IngestionManager

__all__ = ["BaseIngester", "IngestionManager"]
