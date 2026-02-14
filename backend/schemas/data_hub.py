"""
Pydantic schemas for the Universal Scenario Data Hub API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SourceTier(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    TIER_4 = "tier_4"
    TIER_5 = "tier_5"
    TIER_6 = "tier_6"


class SyncStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# --- Source schemas ---

class DataHubSourceResponse(BaseModel):
    id: str
    name: str
    short_name: str
    organization: str
    description: Optional[str] = None
    url: Optional[str] = None
    tier: SourceTier
    is_active: bool
    data_license: Optional[str] = None
    coverage_regions: List[str] = []
    coverage_variables: List[str] = []
    last_synced_at: Optional[datetime] = None
    scenario_count: int = 0
    trajectory_count: int = 0

    class Config:
        from_attributes = True


class DataHubSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    short_name: str = Field(..., min_length=1, max_length=50)
    organization: str
    description: Optional[str] = None
    url: Optional[str] = None
    api_endpoint: Optional[str] = None
    tier: SourceTier = SourceTier.TIER_1
    data_license: Optional[str] = None
    coverage_regions: List[str] = []
    coverage_variables: List[str] = []


# --- Scenario schemas ---

class DataHubScenarioResponse(BaseModel):
    id: str
    source_id: str
    source_name: Optional[str] = None
    external_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = []
    temperature_target: Optional[float] = None
    time_horizon_start: Optional[int] = None
    time_horizon_end: Optional[int] = None
    regions: List[str] = []
    variables: List[str] = []
    trajectory_count: int = 0
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class DataHubScenarioSearch(BaseModel):
    query: Optional[str] = None
    source_ids: List[str] = []
    categories: List[str] = []
    tags: List[str] = []
    regions: List[str] = []
    variables: List[str] = []
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# --- Trajectory schemas ---

class DataHubTrajectoryResponse(BaseModel):
    id: str
    scenario_id: str
    variable_name: str
    unit: str
    region: str
    time_series: Dict[str, float]
    metadata_info: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class TrajectoryQuery(BaseModel):
    scenario_ids: List[str] = []
    variable_names: List[str] = []
    regions: List[str] = []


# --- Comparison schemas ---

class DataHubComparisonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    base_scenario_id: str
    compare_scenario_ids: List[str] = []
    variable_filter: List[str] = []
    region_filter: List[str] = []
    created_by: Optional[str] = None


class DataHubComparisonResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    base_scenario_id: Optional[str] = None
    compare_scenario_ids: List[str] = []
    variable_filter: List[str] = []
    region_filter: List[str] = []
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Sync schemas ---

class DataHubSyncLogResponse(BaseModel):
    id: str
    source_id: str
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    scenarios_added: int = 0
    scenarios_updated: int = 0
    trajectories_added: int = 0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class SyncTriggerRequest(BaseModel):
    source_id: str


# --- Favorite schemas ---

class DataHubFavoriteCreate(BaseModel):
    scenario_id: str
    user_id: str = "default_user"
    folder: str = "default"
    notes: Optional[str] = None


class DataHubFavoriteResponse(BaseModel):
    id: str
    user_id: str
    scenario_id: str
    folder: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Stats / Overview ---

class DataHubStats(BaseModel):
    total_sources: int
    active_sources: int
    total_scenarios: int
    total_trajectories: int
    total_comparisons: int
    sources_by_tier: Dict[str, int] = {}
    recent_syncs: List[DataHubSyncLogResponse] = []
