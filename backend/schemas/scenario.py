"""Scenario-related Pydantic schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

from schemas.common import ScenarioType, TimestampMixin, PaginatedResponse


class ScenarioBase(BaseModel):
    """Base scenario fields"""
    name: str = Field(min_length=1, max_length=255)
    scenario_type: ScenarioType
    description: Optional[str] = Field(default=None, max_length=2000)
    temperature_target: Optional[Decimal] = Field(
        default=None,
        ge=1.0,
        le=5.0,
        decimal_places=1,
        description="Temperature increase target (°C)"
    )
    carbon_price_trajectory: Optional[Dict[int, Decimal]] = Field(
        default=None,
        description="Carbon price by year (USD/tCO2)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether scenario is available for analysis"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional scenario parameters"
    )


class ScenarioCreate(ScenarioBase):
    """Schema for creating a scenario"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Net Zero 2050",
                "scenario_type": "Orderly",
                "description": "Immediate policy action with net zero emissions by 2050",
                "temperature_target": "1.5",
                "carbon_price_trajectory": {
                    "2030": "100.00",
                    "2040": "250.00",
                    "2050": "500.00"
                },
                "is_active": True,
                "metadata": {
                    "ngfs_version": "Phase 5",
                    "model": "REMIND-MAgPIE 3.0",
                    "policy_stringency": "high"
                }
            }
        }
    )


class ScenarioUpdate(BaseModel):
    """Schema for updating scenario"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    temperature_target: Optional[Decimal] = Field(default=None, ge=1.0, le=5.0)
    carbon_price_trajectory: Optional[Dict[int, Decimal]] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class ScenarioVariable(BaseModel):
    """Climate variable data point"""
    variable_name: str = Field(description="e.g., Emissions|CO2, Price|Carbon")
    region: str = Field(description="Geographic region or 'World'")
    unit: str = Field(description="e.g., GtCO2, USD/tCO2")
    values: Dict[int, Decimal] = Field(
        description="Year -> value mapping"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "variable_name": "Price|Carbon",
                "region": "World",
                "unit": "USD/tCO2",
                "values": {
                    "2030": "100.00",
                    "2040": "250.00",
                    "2050": "500.00"
                }
            }
        }
    )


class ScenarioResponse(ScenarioBase, TimestampMixin):
    """Full scenario response"""
    id: str = Field(description="Scenario UUID")
    variables: Optional[List[ScenarioVariable]] = Field(
        default=None,
        description="Associated climate variables"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ScenarioSummary(BaseModel):
    """Lightweight scenario for lists"""
    id: str
    name: str
    scenario_type: ScenarioType
    temperature_target: Optional[Decimal] = Field(default=None, decimal_places=1)
    is_active: bool
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Net Zero 2050",
                "scenario_type": "Orderly",
                "temperature_target": "1.5",
                "is_active": True
            }
        }
    )


class ScenarioListResponse(PaginatedResponse):
    """Paginated scenario list"""
    items: List[ScenarioSummary]


class ScenarioDataRefreshRequest(BaseModel):
    """Request to refresh scenario data from external sources"""
    force: bool = Field(
        default=False,
        description="Force refresh even if data exists"
    )
    source: Optional[str] = Field(
        default=None,
        description="Data source identifier (e.g., 'NGFS_Phase5')"
    )
    variables: Optional[List[str]] = Field(
        default=None,
        description="Specific variables to refresh (default: all)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "force": True,
                "source": "NGFS_Phase5",
                "variables": ["Price|Carbon", "Emissions|CO2", "GDP|PPP"]
            }
        }
    )


class ScenarioDataRefreshResponse(BaseModel):
    """Response from scenario data refresh"""
    success: bool
    records_inserted: int
    records_updated: int
    source_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    errors: Optional[List[str]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "records_inserted": 2160,
                "records_updated": 0,
                "source_version": "NGFS_Phase5_20240115",
                "timestamp": "2024-01-15T14:30:00Z",
                "errors": None
            }
        }
    )
