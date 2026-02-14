"""
Core Data Hub service — CRUD for sources, scenarios, trajectories, comparisons, favorites.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from datetime import datetime, timezone

from db.models.data_hub import (
    DataHubSource, DataHubScenario, DataHubTrajectory,
    DataHubComparison, DataHubSyncLog, DataHubFavorite,
    SyncStatus,
)


class DataHubService:

    def __init__(self, db: Session):
        self.db = db

    # ---- Sources ----

    def list_sources(self, active_only: bool = False):
        q = self.db.query(DataHubSource)
        if active_only:
            q = q.filter(DataHubSource.is_active.is_(True))
        return q.order_by(DataHubSource.tier, DataHubSource.name).all()

    def get_source(self, source_id: str):
        return self.db.get(DataHubSource, source_id)

    def get_source_by_short_name(self, short_name: str):
        return self.db.query(DataHubSource).filter(DataHubSource.short_name == short_name).first()

    def create_source(self, data: dict) -> DataHubSource:
        src = DataHubSource(**data)
        self.db.add(src)
        self.db.commit()
        self.db.refresh(src)
        return src

    # ---- Scenarios ----

    def list_scenarios(
        self,
        source_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ):
        q = self.db.query(DataHubScenario).filter(DataHubScenario.is_active.is_(True))
        if source_id:
            q = q.filter(DataHubScenario.source_id == source_id)
        if category:
            q = q.filter(DataHubScenario.category == category)
        total = q.count()
        rows = q.order_by(DataHubScenario.name).offset(offset).limit(limit).all()
        return rows, total

    def search_scenarios(self, params: dict):
        q = self.db.query(DataHubScenario).filter(DataHubScenario.is_active.is_(True))

        if params.get("query"):
            term = f"%{params['query']}%"
            q = q.filter(or_(
                DataHubScenario.name.ilike(term),
                DataHubScenario.description.ilike(term),
            ))
        if params.get("source_ids"):
            q = q.filter(DataHubScenario.source_id.in_(params["source_ids"]))
        if params.get("categories"):
            q = q.filter(DataHubScenario.category.in_(params["categories"]))
        if params.get("temperature_min") is not None:
            q = q.filter(DataHubScenario.temperature_target >= params["temperature_min"])
        if params.get("temperature_max") is not None:
            q = q.filter(DataHubScenario.temperature_target <= params["temperature_max"])

        total = q.count()
        limit = params.get("limit", 50)
        offset = params.get("offset", 0)
        rows = q.order_by(DataHubScenario.name).offset(offset).limit(limit).all()
        return rows, total

    def get_scenario(self, scenario_id: str):
        return self.db.get(DataHubScenario, scenario_id)

    def upsert_scenario(self, data: dict) -> DataHubScenario:
        """Insert or update a scenario based on source_id + external_id."""
        existing = self.db.query(DataHubScenario).filter(
            DataHubScenario.source_id == data["source_id"],
            DataHubScenario.external_id == data.get("external_id"),
        ).first()
        if existing:
            for k, v in data.items():
                if k != "id":
                    setattr(existing, k, v)
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        sc = DataHubScenario(**data)
        self.db.add(sc)
        self.db.commit()
        self.db.refresh(sc)
        return sc

    # ---- Trajectories ----

    def get_trajectories(
        self,
        scenario_id: Optional[str] = None,
        variable_name: Optional[str] = None,
        region: Optional[str] = None,
    ):
        q = self.db.query(DataHubTrajectory)
        if scenario_id:
            q = q.filter(DataHubTrajectory.scenario_id == scenario_id)
        if variable_name:
            q = q.filter(DataHubTrajectory.variable_name == variable_name)
        if region:
            q = q.filter(DataHubTrajectory.region == region)
        return q.all()

    def bulk_insert_trajectories(self, trajectories: List[dict]):
        objs = [DataHubTrajectory(**t) for t in trajectories]
        self.db.bulk_save_objects(objs)
        self.db.commit()
        return len(objs)

    def delete_trajectories_for_scenario(self, scenario_id: str):
        self.db.query(DataHubTrajectory).filter(
            DataHubTrajectory.scenario_id == scenario_id
        ).delete()
        self.db.commit()

    # ---- Comparisons ----

    def list_comparisons(self):
        return self.db.query(DataHubComparison).order_by(DataHubComparison.created_at.desc()).all()

    def create_comparison(self, data: dict) -> DataHubComparison:
        comp = DataHubComparison(**data)
        self.db.add(comp)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def get_comparison(self, comparison_id: str):
        return self.db.get(DataHubComparison, comparison_id)

    def delete_comparison(self, comparison_id: str):
        comp = self.db.get(DataHubComparison, comparison_id)
        if comp:
            self.db.delete(comp)
            self.db.commit()
            return True
        return False

    # ---- Sync Logs ----

    def create_sync_log(self, source_id: str) -> DataHubSyncLog:
        log = DataHubSyncLog(source_id=source_id, status=SyncStatus.RUNNING)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def complete_sync_log(self, log_id: str, status: SyncStatus, scenarios_added=0,
                          scenarios_updated=0, trajectories_added=0, error_message=None):
        log = self.db.get(DataHubSyncLog, log_id)
        if log:
            log.status = status
            log.completed_at = datetime.now(timezone.utc)
            log.scenarios_added = scenarios_added
            log.scenarios_updated = scenarios_updated
            log.trajectories_added = trajectories_added
            log.error_message = error_message
            self.db.commit()
            self.db.refresh(log)
        return log

    def get_sync_logs(self, source_id: Optional[str] = None, limit: int = 20):
        q = self.db.query(DataHubSyncLog)
        if source_id:
            q = q.filter(DataHubSyncLog.source_id == source_id)
        return q.order_by(DataHubSyncLog.started_at.desc()).limit(limit).all()

    # ---- Favorites ----

    def list_favorites(self, user_id: str):
        return self.db.query(DataHubFavorite).filter(
            DataHubFavorite.user_id == user_id
        ).order_by(DataHubFavorite.created_at.desc()).all()

    def add_favorite(self, data: dict) -> DataHubFavorite:
        fav = DataHubFavorite(**data)
        self.db.add(fav)
        self.db.commit()
        self.db.refresh(fav)
        return fav

    def remove_favorite(self, favorite_id: str):
        fav = self.db.get(DataHubFavorite, favorite_id)
        if fav:
            self.db.delete(fav)
            self.db.commit()
            return True
        return False

    # ---- Stats ----

    def get_stats(self):
        total_sources = self.db.query(func.count(DataHubSource.id)).scalar() or 0
        active_sources = self.db.query(func.count(DataHubSource.id)).filter(
            DataHubSource.is_active.is_(True)
        ).scalar() or 0
        total_scenarios = self.db.query(func.count(DataHubScenario.id)).scalar() or 0
        total_trajectories = self.db.query(func.count(DataHubTrajectory.id)).scalar() or 0
        total_comparisons = self.db.query(func.count(DataHubComparison.id)).scalar() or 0

        # Counts by tier
        tier_rows = self.db.query(
            DataHubSource.tier, func.count(DataHubSource.id)
        ).group_by(DataHubSource.tier).all()
        sources_by_tier = {str(t): c for t, c in tier_rows}

        recent_syncs = self.db.query(DataHubSyncLog).order_by(
            DataHubSyncLog.started_at.desc()
        ).limit(5).all()

        return {
            "total_sources": total_sources,
            "active_sources": active_sources,
            "total_scenarios": total_scenarios,
            "total_trajectories": total_trajectories,
            "total_comparisons": total_comparisons,
            "sources_by_tier": sources_by_tier,
            "recent_syncs": recent_syncs,
        }

    # ---- Update source counts helper ----

    def refresh_source_counts(self, source_id: str):
        src = self.db.get(DataHubSource, source_id)
        if src:
            src.scenario_count = self.db.query(func.count(DataHubScenario.id)).filter(
                DataHubScenario.source_id == source_id
            ).scalar() or 0
            src.trajectory_count = self.db.query(func.count(DataHubTrajectory.id)).join(
                DataHubScenario
            ).filter(DataHubScenario.source_id == source_id).scalar() or 0
            src.last_synced_at = datetime.now(timezone.utc)
            self.db.commit()
