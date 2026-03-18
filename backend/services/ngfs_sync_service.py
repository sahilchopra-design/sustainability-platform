"""
NGFS Data Synchronization Service.

Handles downloading, parsing, and storing NGFS climate scenario data.
"""

import logging
import hashlib
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models.scenario import (
    NGFSDataSource,
    Scenario,
    ScenarioSource,
    NGFSScenarioType,
    ScenarioApprovalStatus
)

logger = logging.getLogger(__name__)


class NGFSSyncService:
    """Service for syncing with NGFS data sources."""
    
    # NGFS scenario definitions
    # Phase IV (original 6) + Phase V 2024 additions (LOW_DEMAND, DIVERGENT_NET_ZERO)
    # Phase V recalibrates Net Zero 2050 and Delayed Transition per post-AR6 NiGEM model.
    # Carbon prices in USD/tCO2; GDP impact in % deviation from baseline.
    NGFS_SCENARIOS = {
        # ── Phase IV + Phase V recalibrated scenarios ─────────────────────
        NGFSScenarioType.NET_ZERO_2050: {
            "name": "Net Zero 2050",
            "description": (
                "Limits warming to 1.5°C through immediate ambitious policy action and "
                "innovation. Phase V: recalibrated carbon prices +8% vs Phase IV, "
                "stronger near-term transition risk."
            ),
            "phase": "V",
            "carbon_price": {"2025": 81, "2030": 173, "2040": 378, "2050": 735},
            "temperature_pathway": {"2025": 1.1, "2030": 1.2, "2040": 1.3, "2050": 1.4},
            "gdp_impact": {"2025": -0.4, "2030": -0.9, "2040": -1.3, "2050": -1.6},
            "physical_risk_multiplier": {"2030": 1.0, "2050": 1.1},
            "transition_risk_multiplier": {"2030": 1.4, "2050": 1.2},
        },
        NGFSScenarioType.DELAYED_TRANSITION: {
            "name": "Delayed Transition",
            "description": (
                "Late policy action makes achieving 2°C more difficult and costly. "
                "Phase V: peak carbon price raised to USD 1,200/tCO2 by 2050."
            ),
            "phase": "V",
            "carbon_price": {"2025": 15, "2030": 110, "2040": 450, "2050": 1200},
            "temperature_pathway": {"2025": 1.2, "2030": 1.4, "2040": 1.6, "2050": 1.7},
            "gdp_impact": {"2025": -0.1, "2030": -1.6, "2040": -3.2, "2050": -4.8},
            "physical_risk_multiplier": {"2030": 1.0, "2050": 1.2},
            "transition_risk_multiplier": {"2030": 1.0, "2050": 2.0},
        },
        NGFSScenarioType.BELOW_2C: {
            "name": "Below 2°C",
            "description": "Gradual strengthening of policies limits warming to below 2°C",
            "phase": "IV",
            "carbon_price": {"2025": 50, "2030": 120, "2040": 250, "2050": 490},
            "temperature_pathway": {"2025": 1.1, "2030": 1.3, "2040": 1.5, "2050": 1.6},
            "gdp_impact": {"2025": -0.2, "2030": -1.0, "2040": -1.8, "2050": -2.3},
            "physical_risk_multiplier": {"2030": 1.1, "2050": 1.3},
            "transition_risk_multiplier": {"2030": 1.2, "2050": 1.1},
        },
        NGFSScenarioType.NATIONALLY_DETERMINED_CONTRIBUTIONS: {
            "name": "Nationally Determined Contributions (NDCs)",
            "description": "Warming around 2.5°C based on current commitments",
            "phase": "IV",
            "carbon_price": {"2025": 25, "2030": 60, "2040": 120, "2050": 200},
            "temperature_pathway": {"2025": 1.2, "2030": 1.5, "2040": 1.9, "2050": 2.3},
            "gdp_impact": {"2025": -0.1, "2030": -0.5, "2040": -1.5, "2050": -3.0},
            "physical_risk_multiplier": {"2030": 1.2, "2050": 1.8},
            "transition_risk_multiplier": {"2030": 0.8, "2050": 0.9},
        },
        NGFSScenarioType.CURRENT_POLICIES: {
            "name": "Current Policies",
            "description": "Assumes policies as of today with limited further action",
            "phase": "IV",
            "carbon_price": {"2025": 10, "2030": 25, "2040": 40, "2050": 60},
            "temperature_pathway": {"2025": 1.2, "2030": 1.6, "2040": 2.2, "2050": 3.0},
            "gdp_impact": {"2025": 0.0, "2030": -0.3, "2040": -2.0, "2050": -5.0},
            "physical_risk_multiplier": {"2030": 1.4, "2050": 2.8},
            "transition_risk_multiplier": {"2030": 0.3, "2050": 0.2},
        },
        NGFSScenarioType.FRAGMENTED_WORLD: {
            "name": "Fragmented World",
            "description": "Divergent policies lead to high physical and transition risks",
            "phase": "IV",
            "carbon_price": {"2025": 5, "2030": 80, "2040": 200, "2050": 500},
            "temperature_pathway": {"2025": 1.2, "2030": 1.6, "2040": 2.3, "2050": 2.8},
            "gdp_impact": {"2025": 0.0, "2030": -1.2, "2040": -3.5, "2050": -6.5},
            "physical_risk_multiplier": {"2030": 1.3, "2050": 2.2},
            "transition_risk_multiplier": {"2030": 0.5, "2050": 1.5},
        },
        # ── NGFS Phase V (2024) new scenarios ─────────────────────────────
        NGFSScenarioType.LOW_DEMAND: {
            "name": "Low Demand",
            "description": (
                "NEW in Phase V. Demand-side mitigation through sufficiency and efficiency "
                "achieves <1.5°C with lower carbon prices than Net Zero 2050. "
                "IPCC AR6 WG3 Ch5 demand-side potential; NiGEM post-AR6 calibration."
            ),
            "phase": "V",
            "carbon_price": {"2025": 45, "2030": 90, "2040": 180, "2050": 360},
            "temperature_pathway": {"2025": 1.1, "2030": 1.2, "2040": 1.3, "2050": 1.4},
            "gdp_impact": {"2025": -0.2, "2030": -0.5, "2040": -0.9, "2050": -1.1},
            "physical_risk_multiplier": {"2030": 0.9, "2050": 1.0},
            "transition_risk_multiplier": {"2030": 1.1, "2050": 0.8},
            "demand_reduction_pct": {"2025": 5, "2030": 12, "2040": 22, "2050": 32},
        },
        NGFSScenarioType.DIVERGENT_NET_ZERO: {
            "name": "Divergent Net Zero",
            "description": (
                "NEW in Phase V. Heterogeneous climate action across jurisdictions — "
                "some reach net zero 2050, others lag. Results in carbon border friction, "
                "supply-chain disruptions, and elevated transition risk dispersion. ~1.5°C."
            ),
            "phase": "V",
            "carbon_price": {"2025": 60, "2030": 140, "2040": 310, "2050": 590},
            "temperature_pathway": {"2025": 1.1, "2030": 1.2, "2040": 1.3, "2050": 1.5},
            "gdp_impact": {"2025": -0.3, "2030": -1.0, "2040": -1.8, "2050": -2.1},
            "physical_risk_multiplier": {"2030": 1.0, "2050": 1.2},
            "transition_risk_multiplier": {"2030": 1.3, "2050": 1.4},
            "cbam_friction_factor": 1.35,  # carbon border adjustment amplification
        },
    }
    
    # Standard sectoral multipliers (energy sector has highest exposure)
    SECTORAL_MULTIPLIERS = {
        "energy": 1.8,
        "utilities": 1.6,
        "materials": 1.4,
        "industrials": 1.3,
        "transport": 1.5,
        "real_estate": 1.2,
        "consumer_discretionary": 1.1,
        "consumer_staples": 1.0,
        "healthcare": 0.9,
        "financials": 1.0,
        "technology": 0.8,
    }
    
    # Physical risk factors
    PHYSICAL_RISK_FACTORS = {
        "flood": 1.15,
        "drought": 1.10,
        "heatwave": 1.12,
        "storm": 1.18,
        "wildfire": 1.20,
        "sea_level_rise": 1.14,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_ngfs_sources(self) -> List[NGFSDataSource]:
        """Get all NGFS data sources."""
        return self.db.execute(select(NGFSDataSource)).scalars().all()
    
    def create_or_update_source(self, name: str, url: str, version: str, release_date: Optional[datetime] = None) -> NGFSDataSource:
        """Create or update NGFS data source."""
        # Check if source exists
        stmt = select(NGFSDataSource).where(NGFSDataSource.version == version)
        existing = self.db.execute(stmt).scalar_one_or_none()
        
        if existing:
            existing.name = name
            existing.url = url
            existing.release_date = release_date
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            source = NGFSDataSource(
                name=name,
                url=url,
                version=version,
                release_date=release_date,
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
            return source
    
    def sync_ngfs_scenarios(self, source_id: str) -> Dict[str, Any]:
        """
        Sync NGFS scenarios from a data source.
        
        In a production system, this would download CSV/Excel files from NGFS.
        For this implementation, we use embedded scenario definitions.
        """
        # Get source
        source = self.db.get(NGFSDataSource, source_id)
        if not source:
            raise ValueError(f"NGFS source {source_id} not found")
        
        try:
            logger.info(f"Starting NGFS sync for source {source.name} (v{source.version})")
            
            # In production, download data from source.url
            # For now, use embedded definitions
            scenarios_created = 0
            scenarios_updated = 0
            
            for scenario_type, scenario_data in self.NGFS_SCENARIOS.items():
                # Check if scenario already exists for this NGFS version
                stmt = select(Scenario).where(
                    Scenario.source == ScenarioSource.NGFS,
                    Scenario.ngfs_scenario_type == scenario_type,
                    Scenario.ngfs_version == source.version
                )
                existing = self.db.execute(stmt).scalar_one_or_none()
                
                # Build parameters
                parameters = {
                    "carbon_price": scenario_data["carbon_price"],
                    "temperature_pathway": scenario_data["temperature_pathway"],
                    "gdp_impact": scenario_data["gdp_impact"],
                    "sectoral_multipliers": self.SECTORAL_MULTIPLIERS,
                    "physical_risk": self.PHYSICAL_RISK_FACTORS,
                }
                
                if existing:
                    # Update existing scenario
                    existing.parameters = parameters
                    existing.description = scenario_data["description"]
                    existing.updated_at = datetime.now(timezone.utc)
                    scenarios_updated += 1
                else:
                    # Create new scenario
                    scenario = Scenario(
                        name=f"{scenario_data['name']} ({source.version})",
                        description=scenario_data["description"],
                        source=ScenarioSource.NGFS,
                        ngfs_scenario_type=scenario_type,
                        ngfs_version=source.version,
                        parameters=parameters,
                        approval_status=ScenarioApprovalStatus.APPROVED,  # NGFS scenarios are pre-approved
                        is_published=True,
                        created_by="ngfs_sync",
                    )
                    self.db.add(scenario)
                    scenarios_created += 1
            
            # Update source metadata
            source.last_synced_at = datetime.now(timezone.utc)
            source.last_sync_status = "success"
            source.last_sync_error = None
            source.sync_count += 1
            source.scenario_count = len(self.NGFS_SCENARIOS)
            
            # Calculate data hash for change detection
            data_str = str(sorted(self.NGFS_SCENARIOS.items()))
            source.data_hash = hashlib.sha256(data_str.encode()).hexdigest()
            
            self.db.commit()
            
            logger.info(f"NGFS sync completed: {scenarios_created} created, {scenarios_updated} updated")
            
            return {
                "success": True,
                "scenarios_created": scenarios_created,
                "scenarios_updated": scenarios_updated,
                "source_version": source.version,
            }
        
        except Exception as e:
            logger.error(f"NGFS sync failed: {str(e)}", exc_info=True)
            source.last_sync_status = "failed"
            source.last_sync_error = str(e)
            self.db.commit()
            raise
    
    def download_ngfs_data(self, url: str) -> bytes:
        """
        Download NGFS data from URL.
        
        Production implementation would handle:
        - Authentication
        - Rate limiting
        - Retries
        - Progress tracking
        """
        response = requests.get(url, timeout=300)  # 5 minute timeout
        response.raise_for_status()
        return response.content
    
    def detect_changes(self, source_id: str) -> bool:
        """
        Detect if NGFS data has changed since last sync.
        
        Returns True if data has changed or first sync.
        """
        source = self.db.get(NGFSDataSource, source_id)
        if not source or not source.data_hash:
            return True  # First sync
        
        # Calculate current hash
        data_str = str(sorted(self.NGFS_SCENARIOS.items()))
        current_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        return current_hash != source.data_hash
