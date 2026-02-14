"""
Async worker tasks for NGFS data synchronization.

Uses background task processing (would use Celery in production).
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

# In production, this would use Celery:
# from celery import shared_task
# For now, these are regular functions that can be called directly or queued


def sync_ngfs_data_task(source_id: str) -> Dict[str, Any]:
    """
    Background task to sync NGFS data.
    
    In production, this would be a Celery task decorated with @shared_task.
    
    Args:
        source_id: ID of NGFS data source to sync
    
    Returns:
        Dict with sync results
    """
    from db.base import SessionLocal
    from services.ngfs_sync_service import NGFSSyncService
    
    logger.info(f"Starting NGFS sync task for source {source_id}")
    
    try:
        db = SessionLocal()
        try:
            service = NGFSSyncService(db)
            result = service.sync_ngfs_scenarios(source_id)
            
            logger.info(f"NGFS sync task completed successfully: {result}")
            return result
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"NGFS sync task failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


def scheduled_ngfs_sync_task() -> Dict[str, Any]:
    """
    Scheduled task to sync all NGFS sources.
    
    This would run on a schedule (e.g., daily) in production.
    """
    from db.base import SessionLocal
    from services.ngfs_sync_service import NGFSSyncService
    
    logger.info("Starting scheduled NGFS sync for all sources")
    
    try:
        db = SessionLocal()
        try:
            service = NGFSSyncService(db)
            sources = service.get_ngfs_sources()
            
            results = []
            for source in sources:
                # Check if data has changed before syncing
                if service.detect_changes(source.id):
                    logger.info(f"Changes detected for source {source.name}, syncing...")
                    result = service.sync_ngfs_scenarios(source.id)
                    results.append({
                        "source_id": source.id,
                        "source_name": source.name,
                        **result
                    })
                else:
                    logger.info(f"No changes detected for source {source.name}, skipping sync")
                    results.append({
                        "source_id": source.id,
                        "source_name": source.name,
                        "success": True,
                        "skipped": True,
                    })
            
            return {
                "success": True,
                "synced_sources": len(results),
                "results": results,
            }
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Scheduled NGFS sync failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


def calculate_scenario_impact_task(scenario_id: str, portfolio_id: str) -> Dict[str, Any]:
    """
    Background task to calculate scenario impact.
    
    Can be computationally expensive for large portfolios.
    """
    from db.base import SessionLocal
    from services.scenario_impact_service import ScenarioImpactService
    
    logger.info(f"Starting scenario impact calculation: scenario={scenario_id}, portfolio={portfolio_id}")
    
    try:
        db = SessionLocal()
        try:
            service = ScenarioImpactService(db)
            preview = service.calculate_impact(scenario_id, portfolio_id)
            
            return {
                "success": True,
                "preview_id": preview.id,
                "expected_loss_change_pct": preview.impact_summary.get("expected_loss_change_pct"),
            }
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Scenario impact calculation failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


# Celery configuration (for reference - would be in celery_app.py in production)
"""
from celery import Celery
from celery.schedules import crontab

app = Celery('portfolio_risk')

app.conf.beat_schedule = {
    'sync-ngfs-daily': {
        'task': 'backend.workers.tasks.ngfs_sync_tasks.scheduled_ngfs_sync_task',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}

app.conf.timezone = 'UTC'
"""