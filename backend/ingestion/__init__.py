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
    from ingestion.ngfs_ingester import NgfsIngester
    from ingestion.sbti_ingester import SbtiIngester
    from ingestion.sec_edgar_ingester import SecEdgarIngester
    from ingestion.yfinance_ingester import YfinanceIngester
    from ingestion.wdpa_gfw_ingester import WdpaGfwIngester
    from ingestion.gem_coal_ingester import GemCoalIngester
    from ingestion.irena_crrem_grid_ingester import IrenaCrremGridIngester
    from ingestion.violation_tracker_ingester import ViolationTrackerIngester

    ingestion_manager.register(GleifIngester)
    ingestion_manager.register(SanctionsIngester)
    ingestion_manager.register(ClimateTraceIngester)
    ingestion_manager.register(OwidIngester)
    ingestion_manager.register(NgfsIngester)
    ingestion_manager.register(SbtiIngester)
    ingestion_manager.register(SecEdgarIngester)
    ingestion_manager.register(YfinanceIngester)
    ingestion_manager.register(WdpaGfwIngester)
    ingestion_manager.register(GemCoalIngester)
    ingestion_manager.register(IrenaCrremGridIngester)
    ingestion_manager.register(ViolationTrackerIngester)
