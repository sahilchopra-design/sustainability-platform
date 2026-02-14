"""
Scenario Sync Orchestrator — coordinates fetching, normalizing, and persisting
scenario data from all 26 sources across 6 tiers.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import logging

from db.models.data_hub import SyncStatus
from services.data_hub_service import DataHubService
from services.scenario_fetchers.fetchers import FETCHER_REGISTRY

logger = logging.getLogger(__name__)


ALL_SOURCES = [
    # Tier 1 — Primary (3 real IIASA + 2 synthetic)
    {"name": "NGFS Phase V", "short_name": "ngfs", "organization": "NGFS / IIASA",
     "description": "Network for Greening the Financial System Phase V scenarios. REAL DATA from IIASA Scenario Explorer.",
     "url": "https://data.ece.iiasa.ac.at/ngfs/", "tier": "tier_1", "update_frequency": "Quarterly",
     "data_license": "CC BY 4.0",
     "coverage_regions": ["World", "R5.2OECD90+EU", "R5.2ASIA", "R5.2MAF", "R5.2LAM", "R5.2REF"],
     "coverage_variables": ["Price|Carbon", "Emissions|CO2", "GDP|PPP", "Primary Energy", "Temperature"]},
    {"name": "IPCC AR6", "short_name": "ipcc", "organization": "IPCC / IIASA",
     "description": "IPCC 6th Assessment Report scenarios. REAL DATA from IIASA AR6 public database.",
     "url": "https://data.ece.iiasa.ac.at/ar6/", "tier": "tier_1", "update_frequency": "Every 6 years",
     "data_license": "Open Access",
     "coverage_regions": ["World"],
     "coverage_variables": ["Emissions|CO2", "Price|Carbon", "Primary Energy", "GDP|PPP"]},
    {"name": "IAMC 1.5°C Scenarios", "short_name": "iamc15", "organization": "IIASA",
     "description": "IAMC 1.5°C Scenario Database with REMIND, GCAM, MESSAGEix, IMAGE, WITCH models. REAL DATA.",
     "url": "https://data.ece.iiasa.ac.at/iamc15/", "tier": "tier_1", "update_frequency": "Periodic",
     "data_license": "Open Access",
     "coverage_regions": ["World"],
     "coverage_variables": ["Emissions|CO2", "Price|Carbon", "Primary Energy", "GDP|PPP"]},
    {"name": "IEA World Energy Outlook", "short_name": "iea", "organization": "IEA",
     "description": "IEA World Energy Outlook scenarios (STEPS, APS, NZE). Synthetic data.",
     "url": "https://www.iea.org/reports/world-energy-outlook-2024", "tier": "tier_1", "update_frequency": "Annual",
     "data_license": "IEA License",
     "coverage_regions": ["World", "Advanced Economies", "Emerging Markets"],
     "coverage_variables": ["Primary Energy", "Electricity Generation", "Emissions|CO2|Energy"]},
    {"name": "IRENA", "short_name": "irena", "organization": "IRENA",
     "description": "IRENA World Energy Transitions Outlook. Synthetic data.",
     "url": "https://www.irena.org/Energy-Transition/Outlook", "tier": "tier_1", "update_frequency": "Annual",
     "data_license": "IRENA License",
     "coverage_regions": ["World"],
     "coverage_variables": ["Renewable Energy Share", "Installed Capacity", "Investment|Renewables"]},

    # Tier 2 — Model Frameworks
    {"name": "REMIND (PIK)", "short_name": "remind", "organization": "PIK Potsdam",
     "description": "PIK REMIND-MAgPIE integrated assessment model scenarios.",
     "url": "https://www.pik-potsdam.de/research/transformation-pathways/models/remind",
     "tier": "tier_2", "update_frequency": "Periodic",
     "coverage_regions": ["World"], "coverage_variables": ["Price|Carbon", "Emissions|CO2", "GDP|PPP"]},
    {"name": "GCAM", "short_name": "gcam", "organization": "PNNL / UMD",
     "description": "Global Change Analysis Model scenarios.",
     "url": "https://www.globalchange.umd.edu/gcam/", "tier": "tier_2", "update_frequency": "Periodic",
     "coverage_regions": ["World"], "coverage_variables": ["Emissions|CO2", "Primary Energy"]},
    {"name": "MESSAGEix (IIASA)", "short_name": "messageix", "organization": "IIASA",
     "description": "IIASA MESSAGEix-GLOBIOM global energy system model.",
     "url": "https://messageix.iiasa.ac.at/", "tier": "tier_2", "update_frequency": "Periodic",
     "coverage_regions": ["World"], "coverage_variables": ["Price|Carbon", "Emissions|CO2", "GDP|PPP"]},
    {"name": "IMAGE (PBL)", "short_name": "image", "organization": "PBL Netherlands",
     "description": "PBL IMAGE integrated assessment model.",
     "url": "https://models.pbl.nl/image/", "tier": "tier_2", "update_frequency": "Periodic",
     "coverage_regions": ["World"], "coverage_variables": ["Emissions|CO2", "Primary Energy"]},
    {"name": "WITCH (FEEM/CMCC)", "short_name": "witch", "organization": "FEEM / CMCC",
     "description": "WITCH-GLOBIOM regional integrated assessment model.",
     "url": "https://www.witchmodel.org/", "tier": "tier_2", "update_frequency": "Periodic",
     "coverage_regions": ["World"], "coverage_variables": ["Price|Carbon", "Emissions|CO2", "GDP|PPP"]},
    {"name": "TIAM-ECN", "short_name": "tiam", "organization": "ETSAP",
     "description": "TIAM-ECN energy system optimization model.",
     "url": "https://iea-etsap.org/", "tier": "tier_2", "update_frequency": "Periodic",
     "coverage_regions": ["World"], "coverage_variables": ["Primary Energy", "Emissions|CO2"]},

    # Tier 3 — Regional / National
    {"name": "EU Reference Scenario", "short_name": "eu_ref", "organization": "European Commission",
     "description": "European Commission Reference Scenario and Fit for 55.",
     "url": "https://energy.ec.europa.eu/", "tier": "tier_3", "update_frequency": "Every 2-3 years",
     "coverage_regions": ["EU"], "coverage_variables": ["Emissions|CO2", "Renewable Energy Share"]},
    {"name": "UK Carbon Budget (CCC)", "short_name": "uk_ccc", "organization": "UK CCC",
     "description": "UK Climate Change Committee 6th Carbon Budget pathways.",
     "url": "https://www.theccc.org.uk/", "tier": "tier_3", "update_frequency": "Every 5 years",
     "coverage_regions": ["United Kingdom"], "coverage_variables": ["Emissions|CO2"]},
    {"name": "US Annual Energy Outlook", "short_name": "us_eia", "organization": "US EIA",
     "description": "US EIA Annual Energy Outlook scenarios.",
     "url": "https://www.eia.gov/outlooks/aeo/", "tier": "tier_3", "update_frequency": "Annual",
     "coverage_regions": ["USA"], "coverage_variables": ["Primary Energy", "Emissions|CO2|Energy"]},
    {"name": "China Energy Scenarios", "short_name": "china_ndrc", "organization": "NDRC / IEA",
     "description": "China carbon peak and neutrality pathways.",
     "url": "https://www.iea.org/countries/china", "tier": "tier_3", "update_frequency": "Periodic",
     "coverage_regions": ["China"], "coverage_variables": ["Emissions|CO2", "Primary Energy|Coal"]},
    {"name": "Japan Strategic Energy Plan", "short_name": "japan_meti", "organization": "METI",
     "description": "Japan METI Strategic Energy Plan scenarios.",
     "url": "https://www.enecho.meti.go.jp/en/", "tier": "tier_3", "update_frequency": "Periodic",
     "coverage_regions": ["Japan"], "coverage_variables": ["Primary Energy", "Electricity Generation|Renewables"]},

    # Tier 4 — Sector-Specific
    {"name": "IEA Sector Roadmaps", "short_name": "iea_sectors", "organization": "IEA",
     "description": "IEA sectoral technology roadmaps (Steel, Cement, Aviation, Shipping).",
     "url": "https://www.iea.org/reports/net-zero-by-2050", "tier": "tier_4", "update_frequency": "Periodic",
     "coverage_regions": ["World"], "coverage_variables": ["Emissions|CO2|Industry", "Emissions|CO2|Transport"]},

    # Tier 5 — Carbon Pricing
    {"name": "Carbon Pricing Dashboard", "short_name": "carbon_price",
     "organization": "World Bank / OECD / ICAP",
     "description": "Global carbon pricing data from World Bank, OECD, and ICAP.",
     "url": "https://carbonpricingdashboard.worldbank.org/", "tier": "tier_5", "update_frequency": "Annual",
     "coverage_regions": ["World", "EU", "China", "United Kingdom", "USA"],
     "coverage_variables": ["Price|Carbon"]},

    # Tier 6 — Physical Risk
    {"name": "Physical Risk Scenarios", "short_name": "physical_risk",
     "organization": "CMIP6 / ISIMIP / Copernicus",
     "description": "Physical climate risk projections from CMIP6, ISIMIP, and Copernicus.",
     "url": "https://pcmdi.llnl.gov/CMIP6/", "tier": "tier_6", "update_frequency": "Periodic",
     "coverage_regions": ["World", "EU", "USA", "China", "India", "Africa", "Southeast Asia"],
     "coverage_variables": ["Temperature|Global Mean", "Sea Level Rise", "Precipitation Change"]},
]


class ScenarioSyncOrchestrator:
    """Orchestrates syncing scenario data from external sources."""

    def __init__(self, db: Session):
        self.db = db
        self.service = DataHubService(db)

    def seed_sources(self):
        """Create all source entries if they don't exist."""
        created = 0
        for src_data in ALL_SOURCES:
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
            logger.info(f"Syncing source: {source.name} ({source.short_name})")
            data = fetcher.fetch()

            scenarios_added = 0
            scenarios_updated = 0
            trajectories_added = 0

            for sc_data in data["scenarios"]:
                sc_id = sc_data.pop("id")
                sc_data["source_id"] = source_id
                sc = self.service.upsert_scenario(sc_data)
                actual_id = sc.id

                # Remap trajectory scenario_id
                for traj in data["trajectories"]:
                    if traj["scenario_id"] == sc_id:
                        traj["scenario_id"] = actual_id

                if sc.created_at == sc.updated_at:
                    scenarios_added += 1
                else:
                    scenarios_updated += 1

            # Clear old trajectories for this source's scenarios then bulk insert
            source_scenario_ids = [s.id for s in self.service.list_scenarios(source_id=source_id, limit=5000)[0]]
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
                "source": source.short_name,
                "scenarios_added": scenarios_added,
                "scenarios_updated": scenarios_updated,
                "trajectories_added": trajectories_added,
            }

        except Exception as e:
            logger.error(f"Sync failed for {source.short_name}: {e}")
            self.service.complete_sync_log(log.id, SyncStatus.FAILED, error_message=str(e))
            raise

    def sync_all(self, include_real_data: bool = True) -> dict:
        """Sync all active sources."""
        sources = self.service.list_sources(active_only=True)
        results = {}
        for source in sources:
            fetcher_cls = FETCHER_REGISTRY.get(source.short_name)
            if not fetcher_cls:
                continue
            # Skip real data sources if flag is false (they take longer)
            if not include_real_data and source.short_name in ("ngfs", "ipcc", "iamc15"):
                results[source.short_name] = {"status": "skipped", "reason": "real data sources skipped"}
                continue
            try:
                result = self.sync_source(source.id)
                results[source.short_name] = result
            except Exception as e:
                results[source.short_name] = {"status": "failed", "error": str(e)}
        return results

    def sync_synthetic_only(self) -> dict:
        """Sync only synthetic sources (fast)."""
        return self.sync_all(include_real_data=False)
