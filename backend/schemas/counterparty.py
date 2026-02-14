"""Counterparty-related Pydantic schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

from schemas.common import (
    Sector, EmissionsTrend, TimestampMixin, PaginatedResponse
)


class CounterpartyBase(BaseModel):
    """Base counterparty fields"""
    name: str = Field(min_length=1, max_length=255)
    lei: Optional[str] = Field(
        default=None,
        min_length=20,
        max_length=20,
        description="Legal Entity Identifier (20 chars)"
    )
    sector: Sector
    country_code: str = Field(
        min_length=2,
        max_length=3,
        description="ISO country code"
    )
    emissions_intensity: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Emissions intensity (tCO2e per revenue unit)"
    )
    emissions_trend: Optional[EmissionsTrend] = Field(
        default=EmissionsTrend.STABLE,
        description="Historical emissions trajectory"
    )
    transition_plan_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Quality of climate transition plan (1-5)"
    )
    physical_risk_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Exposure to physical climate risks (1-5)"
    )
    baseline_pd: Decimal = Field(
        ge=0,
        le=1,
        decimal_places=4,
        description="Baseline Probability of Default"
    )
    baseline_lgd: Decimal = Field(
        ge=0,
        le=1,
        decimal_places=4,
        description="Baseline Loss Given Default"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional counterparty data"
    )
    
    @field_validator('lei')
    @classmethod
    def validate_lei_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate LEI format (20 alphanumeric characters)"""
        if v is not None:
            v = v.upper()
            if not v.isalnum():
                raise ValueError('LEI must contain only alphanumeric characters')
        return v
    
    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Ensure country code is uppercase"""
        return v.upper()


class CounterpartyCreate(CounterpartyBase):
    """Schema for creating a counterparty"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Orsted A/S",
                "lei": "529900MTJPDPE4MHJ122",
                "sector": "Power Generation",
                "country_code": "DK",
                "emissions_intensity": "0.1250",
                "emissions_trend": "Improving",
                "transition_plan_score": 5,
                "physical_risk_score": 2,
                "baseline_pd": "0.0150",
                "baseline_lgd": "0.4500",
                "metadata": {
                    "renewable_capacity_mw": 15000,
                    "offshore_wind_share": 0.85
                }
            }
        }
    )


class CounterpartyUpdate(BaseModel):
    """Schema for updating counterparty (all optional)"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    lei: Optional[str] = Field(default=None, min_length=20, max_length=20)
    sector: Optional[Sector] = None
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=3)
    emissions_intensity: Optional[Decimal] = Field(default=None, ge=0, decimal_places=4)
    emissions_trend: Optional[EmissionsTrend] = None
    transition_plan_score: Optional[int] = Field(default=None, ge=1, le=5)
    physical_risk_score: Optional[int] = Field(default=None, ge=1, le=5)
    baseline_pd: Optional[Decimal] = Field(default=None, ge=0, le=1, decimal_places=4)
    baseline_lgd: Optional[Decimal] = Field(default=None, ge=0, le=1, decimal_places=4)
    metadata: Optional[dict] = None


class CounterpartyResponse(CounterpartyBase, TimestampMixin):
    """Full counterparty response"""
    id: str = Field(description="Counterparty UUID")
    
    model_config = ConfigDict(from_attributes=True)


class CounterpartySummary(BaseModel):
    """Lightweight counterparty for lists"""
    id: str
    name: str
    lei: Optional[str] = None
    sector: Sector
    country_code: str
    baseline_pd: Decimal = Field(decimal_places=4)
    transition_plan_score: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class CounterpartyListResponse(PaginatedResponse):
    """Paginated counterparty list"""
    items: List[CounterpartySummary]


class CounterpartyFilter(BaseModel):
    """Query parameters for filtering counterparties"""
    name_contains: Optional[str] = Field(default=None)
    sector: Optional[Sector] = None
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=3)
    min_pd: Optional[Decimal] = Field(default=None, ge=0, le=1)
    max_pd: Optional[Decimal] = Field(default=None, ge=0, le=1)
    emissions_trend: Optional[EmissionsTrend] = None
    min_transition_score: Optional[int] = Field(default=None, ge=1, le=5)
    has_lei: Optional[bool] = Field(default=None, description="Filter by LEI presence")
    
    @field_validator('max_pd')
    @classmethod
    def validate_pd_range(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        if v is not None and info.data.get('min_pd') is not None:
            if v < info.data['min_pd']:
                raise ValueError('max_pd must be >= min_pd')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sector": "Power Generation",
                "country_code": "DK",
                "emissions_trend": "Improving",
                "min_transition_score": 4
            }
        }
    )
