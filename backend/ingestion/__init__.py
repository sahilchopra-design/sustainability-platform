"""
Ingestion framework — BaseIngester, scheduler, and job manager.

Provides the abstract base class for all data ingesters, an APScheduler-based
scheduler for recurring sync jobs, and a manager for registration and orchestration.
"""

from ingestion.base_ingester import BaseIngester
from ingestion.manager import IngestionManager

__all__ = ["BaseIngester", "IngestionManager"]


def register_all_ingesters():
    """Register all concrete ingesters with the global manager."""
    from ingestion.manager import ingestion_manager
    from ingestion.gleif_ingester import GleifIngester
    from ingestion.sanctions_ingester import SanctionsIngester
    from ingestion.climate_trace_ingester import ClimateTraceIngester
    from ingestion.owid_ingester import OwidIngester

    ingestion_manager.register(GleifIngester)
    ingestion_manager.register(SanctionsIngester)
    ingestion_manager.register(ClimateTraceIngester)
    ingestion_manager.register(OwidIngester)
