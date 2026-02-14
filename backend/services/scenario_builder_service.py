"""
Scenario Builder Service.

Handles creation, updating, versioning, and approval of climate scenarios.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
import copy

from models.scenario import (
    Scenario,
    ScenarioVersion,
    ScenarioSource,
    ScenarioApprovalStatus,
    NGFSScenarioType,
)
from schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
)

logger = logging.getLogger(__name__)


class ScenarioBuilderService:
    """Service for building and managing climate scenarios."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_scenarios(
        self,
        approval_status: Optional[ScenarioApprovalStatus] = None,
        source: Optional[ScenarioSource] = None,
        published_only: bool = False,
    ) -> List[Scenario]:
        """List scenarios with optional filters."""
        stmt = select(Scenario)
        
        if approval_status:
            stmt = stmt.where(Scenario.approval_status == approval_status)
        
        if source:
            stmt = stmt.where(Scenario.source == source)
        
        if published_only:
            stmt = stmt.where(Scenario.is_published == True)
        
        stmt = stmt.order_by(Scenario.created_at.desc())
        
        return self.db.execute(stmt).scalars().all()
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get scenario by ID."""
        return self.db.get(Scenario, scenario_id)
    
    def create_scenario(self, scenario_data: ScenarioCreate) -> Scenario:
        """Create a new scenario."""
        # If base_scenario_id provided, validate it exists
        if scenario_data.base_scenario_id:
            base = self.db.get(Scenario, scenario_data.base_scenario_id)
            if not base:
                raise ValueError(f"Base scenario {scenario_data.base_scenario_id} not found")
        
        # Create scenario
        scenario = Scenario(
            name=scenario_data.name,
            description=scenario_data.description,
            source=scenario_data.source,
            ngfs_scenario_type=scenario_data.ngfs_scenario_type,
            base_scenario_id=scenario_data.base_scenario_id,
            parameters=scenario_data.parameters.dict(),
            created_by=scenario_data.created_by,
            approval_status=ScenarioApprovalStatus.DRAFT,
            current_version=1,
        )
        
        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)
        
        # Create initial version
        self._create_version(
            scenario.id,
            1,
            scenario.parameters,
            "Initial version",
            scenario_data.created_by,
        )
        
        logger.info(f"Created scenario {scenario.id}: {scenario.name}")
        return scenario
    
    def update_scenario(self, scenario_id: str, updates: ScenarioUpdate, updated_by: Optional[str] = None) -> Scenario:
        """Update scenario and create new version."""
        scenario = self.db.get(Scenario, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Only allow updates to draft or rejected scenarios
        if scenario.approval_status not in [ScenarioApprovalStatus.DRAFT, ScenarioApprovalStatus.REJECTED]:
            raise ValueError(f"Cannot update scenario with status {scenario.approval_status}")
        
        # Track what changed
        changed_fields = []
        
        if updates.name:
            scenario.name = updates.name
            changed_fields.append("name")
        
        if updates.description is not None:
            scenario.description = updates.description
            changed_fields.append("description")
        
        if updates.parameters:
            scenario.parameters = updates.parameters.dict()
            changed_fields.append("parameters")
            
            # Increment version
            scenario.current_version += 1
            
            # Create version record
            change_summary = updates.change_summary or f"Updated {', '.join(changed_fields)}"
            self._create_version(
                scenario.id,
                scenario.current_version,
                scenario.parameters,
                change_summary,
                updated_by,
            )
        
        scenario.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(scenario)
        
        logger.info(f"Updated scenario {scenario.id}: {', '.join(changed_fields)}")
        return scenario
    
    def fork_scenario(self, scenario_id: str, new_name: str, description: Optional[str] = None, created_by: Optional[str] = None) -> Scenario:
        """Fork (copy) a scenario."""
        source_scenario = self.db.get(Scenario, scenario_id)
        if not source_scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Create new scenario with copied parameters
        forked = Scenario(
            name=new_name,
            description=description or f"Forked from {source_scenario.name}",
            source=ScenarioSource.HYBRID if source_scenario.source == ScenarioSource.NGFS else ScenarioSource.CUSTOM,
            base_scenario_id=scenario_id,
            parameters=copy.deepcopy(source_scenario.parameters),
            created_by=created_by,
            approval_status=ScenarioApprovalStatus.DRAFT,
            current_version=1,
        )
        
        self.db.add(forked)
        self.db.commit()
        self.db.refresh(forked)
        
        # Create initial version
        self._create_version(
            forked.id,
            1,
            forked.parameters,
            f"Forked from scenario {source_scenario.name}",
            created_by,
        )
        
        logger.info(f"Forked scenario {scenario_id} to new scenario {forked.id}")
        return forked
    
    def submit_for_approval(self, scenario_id: str, submitted_by: str, notes: Optional[str] = None) -> Scenario:
        """Submit scenario for approval."""
        scenario = self.db.get(Scenario, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        if scenario.approval_status != ScenarioApprovalStatus.DRAFT:
            raise ValueError(f"Can only submit draft scenarios for approval")
        
        scenario.approval_status = ScenarioApprovalStatus.PENDING_APPROVAL
        scenario.submitted_by = submitted_by
        scenario.submitted_at = datetime.now(timezone.utc)
        scenario.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(scenario)
        
        logger.info(f"Scenario {scenario_id} submitted for approval by {submitted_by}")
        return scenario
    
    def approve_scenario(self, scenario_id: str, approved_by: str, notes: Optional[str] = None) -> Scenario:
        """Approve a scenario."""
        scenario = self.db.get(Scenario, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        if scenario.approval_status != ScenarioApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Can only approve scenarios pending approval")
        
        scenario.approval_status = ScenarioApprovalStatus.APPROVED
        scenario.approved_by = approved_by
        scenario.approved_at = datetime.now(timezone.utc)
        scenario.updated_at = datetime.now(timezone.utc)
        scenario.rejection_reason = None
        
        self.db.commit()
        self.db.refresh(scenario)
        
        logger.info(f"Scenario {scenario_id} approved by {approved_by}")
        return scenario
    
    def reject_scenario(self, scenario_id: str, rejected_by: str, reason: str) -> Scenario:
        """Reject a scenario."""
        scenario = self.db.get(Scenario, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        if scenario.approval_status != ScenarioApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Can only reject scenarios pending approval")
        
        scenario.approval_status = ScenarioApprovalStatus.REJECTED
        scenario.rejection_reason = reason
        scenario.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(scenario)
        
        logger.info(f"Scenario {scenario_id} rejected by {rejected_by}: {reason}")
        return scenario
    
    def publish_scenario(self, scenario_id: str) -> Scenario:
        """Publish an approved scenario."""
        scenario = self.db.get(Scenario, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        if scenario.approval_status != ScenarioApprovalStatus.APPROVED:
            raise ValueError(f"Can only publish approved scenarios")
        
        scenario.is_published = True
        scenario.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(scenario)
        
        logger.info(f"Scenario {scenario_id} published")
        return scenario
    
    def get_scenario_versions(self, scenario_id: str) -> List[ScenarioVersion]:
        """Get all versions of a scenario."""
        stmt = select(ScenarioVersion).where(
            ScenarioVersion.scenario_id == scenario_id
        ).order_by(ScenarioVersion.version_number.desc())
        
        return self.db.execute(stmt).scalars().all()
    
    def get_ngfs_templates(self) -> List[Scenario]:
        """Get NGFS scenario templates."""
        stmt = select(Scenario).where(
            Scenario.source == ScenarioSource.NGFS,
            Scenario.is_published == True,
        ).order_by(Scenario.name)
        
        return self.db.execute(stmt).scalars().all()
    
    def _create_version(self, scenario_id: str, version_number: int, parameters: Dict[str, Any], change_summary: str, changed_by: Optional[str]) -> ScenarioVersion:
        """Create a scenario version record."""
        version = ScenarioVersion(
            scenario_id=scenario_id,
            version_number=version_number,
            parameters=parameters,
            change_summary=change_summary,
            changed_by=changed_by,
        )
        
        self.db.add(version)
        self.db.flush()  # Don't commit, let caller handle transaction
        
        return version
