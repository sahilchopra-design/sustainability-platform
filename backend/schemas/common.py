"""Common schemas and utilities for API validation"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


class Sector(str, Enum):
    """Climate-sensitive sectors"""
    POWER = "Power Generation"
    OIL_GAS = "Oil & Gas"
    MINING = "Metals & Mining"
    AUTOMOTIVE = "Automotive"
    AIRLINES = "Airlines"
    REAL_ESTATE = "Real Estate"


class AssetType(str, Enum):
    """Financial instrument types"""
    BOND = "Bond"
    LOAN = "Loan"
    EQUITY = "Equity"
    DERIVATIVE = "Derivative"


class ScenarioType(str, Enum):
    """NGFS climate scenarios"""
    ORDERLY = "Orderly"
    DISORDERLY = "Disorderly"
    HOT_HOUSE = "Hot house world"


class EmissionsTrend(str, Enum):
    """Counterparty emissions trajectory"""
    IMPROVING = "Improving"
    STABLE = "Stable"
    DETERIORATING = "Deteriorating"


class VelocityTrajectory(str, Enum):
    """PD velocity over time"""
    CONVERGING = "Converging"
    DIVERGING = "Diverging"
    STABLE = "Stable"


class CurrencyCode(str, Enum):
    """ISO 4217 currency codes"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CNY = "CNY"


class PaginationParams(BaseModel):
    """Pagination query parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 20
            }
        }
    )
    
    @property
    def skip(self) -> int:
        """Calculate number of items to skip"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Items to return"""
        return self.page_size


class DateRangeFilter(BaseModel):
    """Date range for time-based queries"""
    start_date: Optional[datetime] = Field(default=None, description="Start date (inclusive)")
    end_date: Optional[datetime] = Field(default=None, description="End date (inclusive)")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure end_date is after start_date"""
        if v is not None and info.data.get('start_date') is not None:
            if v < info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z"
            }
        }
    )


class MonetaryAmount(BaseModel):
    """Monetary value with currency"""
    amount: Decimal = Field(description="Amount in currency units", decimal_places=2)
    currency: CurrencyCode = Field(default=CurrencyCode.USD)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": "1000000.00",
                "currency": "USD"
            }
        }
    )


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    items: list[Any]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    )


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = Field(default=True)
    message: Optional[str] = Field(default=None)
    data: Optional[Any] = Field(default=None)
    errors: Optional[list[str]] = Field(default=None)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {},
                "errors": None
            }
        }
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)
