"""
Pydantic schemas for scenario API validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ScenarioSource(str, Enum):
    """Source of scenario data."""
    NGFS = "ngfs"
    CUSTOM = "custom"
    HYBRID = "hybrid"


class ScenarioApprovalStatus(str, Enum):
    """Approval status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class NGFSScenarioType(str, Enum):
    """NGFS scenario types."""
    NET_ZERO_2050 = "net_zero_2050"
    DELAYED_TRANSITION = "delayed_transition"
    BELOW_2C = "below_2c"
    NATIONALLY_DETERMINED_CONTRIBUTIONS = "ndc"
    CURRENT_POLICIES = "current_policies"
    FRAGMENTED_WORLD = "fragmented_world"


class ScenarioParametersBase(BaseModel):
    """Base scenario parameters."""
    carbon_price: Dict[str, float] = Field(default_factory=dict, description="Carbon price trajectory by year (USD/tCO2)")
    temperature_pathway: Dict[str, float] = Field(default_factory=dict, description="Temperature pathway by year (°C above pre-industrial)")
    gdp_impact: Dict[str, float] = Field(default_factory=dict, description="GDP impact by year (% change)")
    sectoral_multipliers: Dict[str, float] = Field(default_factory=dict, description="Sector-specific risk multipliers")
    physical_risk: Dict[str, float] = Field(default_factory=dict, description="Physical risk factors by type")
    
    @validator('carbon_price', 'temperature_pathway', 'gdp_impact')
    def validate_year_keys(cls, v):
        """Ensure all keys are valid years."""
        for key in v.keys():
            try:
                year = int(key)
                if year < 2020 or year > 2100:
                    raise ValueError(f"Year {year} out of range (2020-2100)")
            except ValueError:
                raise ValueError(f"Invalid year format: {key}")
        return v


class ScenarioCreate(BaseModel):
    """Create a new scenario."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source: ScenarioSource = ScenarioSource.CUSTOM
    ngfs_scenario_type: Optional[NGFSScenarioType] = None
    base_scenario_id: Optional[str] = None
    parameters: ScenarioParametersBase
    created_by: Optional[str] = None


class ScenarioUpdate(BaseModel):
    """Update scenario."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parameters: Optional[ScenarioParametersBase] = None
    change_summary: Optional[str] = None


class ScenarioResponse(BaseModel):
    """Scenario response."""
    id: str
    name: str
    description: Optional[str]
    source: ScenarioSource
    ngfs_scenario_type: Optional[NGFSScenarioType]
    ngfs_version: Optional[str]
    base_scenario_id: Optional[str]
    approval_status: ScenarioApprovalStatus
    current_version: int
    is_published: bool
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    submitted_by: Optional[str]
    approved_by: Optional[str]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ScenarioVersionResponse(BaseModel):
    """Scenario version response."""
    id: str
    scenario_id: str
    version_number: int
    parameters: Dict[str, Any]
    change_summary: Optional[str]
    changed_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScenarioImpactSummary(BaseModel):
    """Impact summary for a scenario on a portfolio."""
    total_exposure: float
    baseline_expected_loss: float
    scenario_expected_loss: float
    expected_loss_change: float
    expected_loss_change_pct: float
    by_sector: Dict[str, Dict[str, float]]
    by_rating: Dict[str, Dict[str, float]]
    top_impacted_holdings: List[Dict[str, Any]]


class ScenarioImpactPreviewResponse(BaseModel):
    """Scenario impact preview response."""
    id: str
    scenario_id: str
    portfolio_id: str
    impact_summary: ScenarioImpactSummary
    calculated_at: datetime
    calculation_version: str
    
    class Config:
        from_attributes = True


class ScenarioTemplateResponse(BaseModel):
    """NGFS scenario template."""
    id: str
    name: str
    description: str
    ngfs_scenario_type: NGFSScenarioType
    parameters: Dict[str, Any]
    version: str


class NGFSDataSourceResponse(BaseModel):
    """NGFS data source response."""
    id: str
    name: str
    version: str
    release_date: Optional[datetime]
    last_synced_at: Optional[datetime]
    last_sync_status: str
    scenario_count: int
    
    class Config:
        from_attributes = True


class ScenarioSubmitForApproval(BaseModel):
    """Submit scenario for approval."""
    submitted_by: str = Field(..., min_length=1)
    notes: Optional[str] = None


class ScenarioApprovalDecision(BaseModel):
    """Approve or reject scenario."""
    approved: bool
    approved_by: str = Field(..., min_length=1)
    notes: Optional[str] = None


class ScenarioForkRequest(BaseModel):
    """Fork (copy) a scenario."""
    new_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    created_by: Optional[str] = None


class ScenarioImpactPreviewRequest(BaseModel):
    """Request impact preview calculation."""
    portfolio_id: str = Field(..., description="Portfolio ID to calculate impact for")
    parameters: Optional[ScenarioParametersBase] = Field(None, description="Override parameters for preview")
