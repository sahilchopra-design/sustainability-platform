"""
Scenario Sync Orchestrator — coordinates fetching, normalizing, and persisting
scenario data from multiple sources.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from db.models.data_hub import SyncStatus
from services.data_hub_service import DataHubService
from services.scenario_fetchers.fetchers import FETCHER_REGISTRY


# Seed definitions for Tier 1 sources
TIER1_SOURCES = [
    {
        "name": "Network for Greening the Financial System",
        "short_name": "ngfs",
        "organization": "NGFS",
        "description": "Central bank & supervisor network providing climate scenarios for financial risk assessment.",
        "url": "https://www.ngfs.net/ngfs-scenarios-portal/",
        "tier": "tier_1",
        "data_license": "CC BY 4.0",
        "coverage_regions": ["World", "United States", "European Union", "China", "India"],
        "coverage_variables": ["Price|Carbon", "Emissions|CO2", "Temperature|Global Mean", "GDP|PPP",
                               "Primary Energy|Coal", "Primary Energy|Gas", "Primary Energy|Solar", "Primary Energy|Wind"],
    },
    {
        "name": "Intergovernmental Panel on Climate Change",
        "short_name": "ipcc",
        "organization": "IPCC",
        "description": "AR6 Shared Socioeconomic Pathways (SSPs) providing global climate projections.",
        "url": "https://www.ipcc.ch/assessment-report/ar6/",
        "tier": "tier_1",
        "data_license": "Open Access",
        "coverage_regions": ["World"],
        "coverage_variables": ["Emissions|CO2", "Temperature|Global Mean", "Sea Level Rise", "Radiative Forcing"],
    },
    {
        "name": "International Energy Agency",
        "short_name": "iea",
        "organization": "IEA",
        "description": "World Energy Outlook scenarios for global energy system transitions.",
        "url": "https://www.iea.org/reports/world-energy-outlook-2024",
        "tier": "tier_1",
        "data_license": "IEA License",
        "coverage_regions": ["World", "Advanced Economies", "Emerging Markets"],
        "coverage_variables": ["Primary Energy|Total", "Primary Energy|Coal", "Primary Energy|Oil",
                               "Primary Energy|Gas", "Primary Energy|Renewables",
                               "Electricity Generation|Solar", "Electricity Generation|Wind", "Emissions|CO2|Energy"],
    },
    {
        "name": "International Renewable Energy Agency",
        "short_name": "irena",
        "organization": "IRENA",
        "description": "World Energy Transitions Outlook with renewable energy deployment scenarios.",
        "url": "https://www.irena.org/Energy-Transition/Outlook",
        "tier": "tier_1",
        "data_license": "IRENA License",
        "coverage_regions": ["World"],
        "coverage_variables": ["Renewable Energy Share", "Installed Capacity|Solar PV",
                               "Installed Capacity|Wind", "Investment|Renewables", "Emissions|CO2|Energy"],
    },
]


class ScenarioSyncOrchestrator:
    """Orchestrates syncing scenario data from external sources."""

    def __init__(self, db: Session):
        self.db = db
        self.service = DataHubService(db)

    def seed_sources(self):
        """Create Tier 1 source entries if they don't exist."""
        created = 0
        for src_data in TIER1_SOURCES:
            existing = self.service.get_source_by_short_name(src_data["short_name"])
            if not existing:
                self.service.create_source(src_data)
                created += 1
        return created

    def sync_source(self, source_id: str) -> dict:
        """Sync a single source by its ID."""
        source = self.service.get_source(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        fetcher_cls = FETCHER_REGISTRY.get(source.short_name)
        if not fetcher_cls:
            raise ValueError(f"No fetcher registered for source '{source.short_name}'")

        log = self.service.create_sync_log(source_id)

        try:
            fetcher = fetcher_cls()
            data = fetcher.fetch()

            scenarios_added = 0
            scenarios_updated = 0
            trajectories_added = 0

            for sc_data in data["scenarios"]:
                sc_id = sc_data.pop("id")
                sc_data["source_id"] = source_id
                sc = self.service.upsert_scenario(sc_data)
                # Use the actual persisted ID for trajectory linking
                actual_id = sc.id

                # Replace the temp scenario_id in trajectories
                for traj in data["trajectories"]:
                    if traj["scenario_id"] == sc_id:
                        traj["scenario_id"] = actual_id

                if sc.created_at == sc.updated_at:
                    scenarios_added += 1
                else:
                    scenarios_updated += 1

            # Bulk insert trajectories
            # First delete existing trajectories for this source's scenarios
            source_scenario_ids = [s.id for s in self.service.list_scenarios(source_id=source_id, limit=1000)[0]]
            for sid in source_scenario_ids:
                self.service.delete_trajectories_for_scenario(sid)

            trajectories_added = self.service.bulk_insert_trajectories(data["trajectories"])

            self.service.refresh_source_counts(source_id)
            self.service.complete_sync_log(
                log.id, SyncStatus.SUCCESS,
                scenarios_added=scenarios_added,
                scenarios_updated=scenarios_updated,
                trajectories_added=trajectories_added,
            )

            return {
                "status": "success",
                "scenarios_added": scenarios_added,
                "scenarios_updated": scenarios_updated,
                "trajectories_added": trajectories_added,
            }

        except Exception as e:
            self.service.complete_sync_log(log.id, SyncStatus.FAILED, error_message=str(e))
            raise

    def sync_all(self) -> dict:
        """Sync all active sources."""
        sources = self.service.list_sources(active_only=True)
        results = {}
        for source in sources:
            fetcher_cls = FETCHER_REGISTRY.get(source.short_name)
            if fetcher_cls:
                try:
                    result = self.sync_source(source.id)
                    results[source.short_name] = result
                except Exception as e:
                    results[source.short_name] = {"status": "failed", "error": str(e)}
        return results
