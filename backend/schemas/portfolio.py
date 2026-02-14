"""Portfolio-related Pydantic schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4

from schemas.common import (
    Sector, AssetType, CurrencyCode, TimestampMixin,
    PaginatedResponse, MonetaryAmount
)


class PortfolioBase(BaseModel):
    """Base portfolio fields"""
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Portfolio name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Portfolio description"
    )
    currency: CurrencyCode = Field(
        default=CurrencyCode.USD,
        description="Base currency for portfolio"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional portfolio metadata"
    )


class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "European Green Energy Portfolio",
                "description": "Focused on renewable energy transition in Europe",
                "currency": "EUR",
                "metadata": {
                    "strategy": "ESG-focused",
                    "benchmark": "MSCI Europe Energy"
                }
            }
        }
    )


class PortfolioUpdate(BaseModel):
    """Schema for updating portfolio (all fields optional)"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    currency: Optional[CurrencyCode] = None
    metadata: Optional[dict] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Updated portfolio description",
                "metadata": {"last_reviewed": "2024-01-15"}
            }
        }
    )


class HoldingBase(BaseModel):
    """Base holding/asset fields"""
    asset_type: AssetType
    company_name: str = Field(min_length=1, max_length=255)
    sector: Sector
    subsector: Optional[str] = Field(default=None, max_length=100)
    country_code: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=3,
        description="ISO country code"
    )
    exposure: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Exposure at Default (EAD) in portfolio currency"
    )
    market_value: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Current market value"
    )
    base_pd: Decimal = Field(
        ge=0,
        le=1,
        decimal_places=4,
        description="Base Probability of Default (0-1)"
    )
    base_lgd: Decimal = Field(
        ge=0,
        le=1,
        decimal_places=4,
        description="Base Loss Given Default (0-1)"
    )
    rating: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Credit rating (e.g., AAA, BB+)"
    )
    maturity_years: Optional[int] = Field(
        default=None,
        ge=0,
        description="Years to maturity"
    )
    
    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        """Ensure country code is uppercase"""
        return v.upper() if v else None


class HoldingCreate(HoldingBase):
    """Schema for adding asset to portfolio"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_type": "Bond",
                "company_name": "Orsted A/S",
                "sector": "Power Generation",
                "subsector": "Offshore Wind",
                "country_code": "DK",
                "exposure": "5000000.00",
                "market_value": "4850000.00",
                "base_pd": "0.0150",
                "base_lgd": "0.4500",
                "rating": "BBB+",
                "maturity_years": 7
            }
        }
    )


class HoldingResponse(HoldingBase, TimestampMixin):
    """Schema for holding in API responses"""
    id: str = Field(description="Unique holding identifier")
    portfolio_id: str = Field(description="Parent portfolio ID")
    
    model_config = ConfigDict(from_attributes=True)


class PortfolioMetrics(BaseModel):
    """Aggregated portfolio metrics"""
    total_exposure: Decimal = Field(decimal_places=2)
    total_market_value: Decimal = Field(decimal_places=2)
    num_holdings: int = Field(ge=0)
    weighted_avg_pd: Decimal = Field(decimal_places=4, description="Exposure-weighted PD")
    weighted_avg_lgd: Decimal = Field(decimal_places=4, description="Exposure-weighted LGD")
    expected_loss_baseline: Decimal = Field(
        decimal_places=2,
        description="Baseline EL = sum(EAD * PD * LGD)"
    )
    sector_concentration: dict[str, Decimal] = Field(
        description="Sector exposure percentages"
    )
    geographic_concentration: dict[str, Decimal] = Field(
        description="Geographic exposure percentages"
    )
    hhi_sector: Decimal = Field(
        ge=0,
        decimal_places=4,
        description="Herfindahl-Hirschman Index for sectors"
    )
    hhi_geographic: Decimal = Field(
        ge=0,
        decimal_places=4,
        description="Herfindahl-Hirschman Index for geographies"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_exposure": "150000000.00",
                "total_market_value": "148500000.00",
                "num_holdings": 45,
                "weighted_avg_pd": "0.0235",
                "weighted_avg_lgd": "0.4250",
                "expected_loss_baseline": "1498125.00",
                "sector_concentration": {
                    "Power Generation": "0.3500",
                    "Oil & Gas": "0.2500",
                    "Automotive": "0.1500"
                },
                "geographic_concentration": {
                    "US": "0.4000",
                    "EU": "0.3500",
                    "CN": "0.1500"
                },
                "hhi_sector": "0.2450",
                "hhi_geographic": "0.3025"
            }
        }
    )


class PortfolioResponse(PortfolioBase, TimestampMixin):
    """Full portfolio response with holdings"""
    id: str = Field(description="Portfolio UUID")
    holdings: List[HoldingResponse] = Field(default_factory=list)
    metrics: Optional[PortfolioMetrics] = Field(
        default=None,
        description="Calculated portfolio metrics"
    )
    
    model_config = ConfigDict(from_attributes=True)


class PortfolioSummary(BaseModel):
    """Lightweight portfolio summary for lists/dropdowns"""
    id: str
    name: str
    num_holdings: int
    total_exposure: Decimal = Field(decimal_places=2)
    currency: CurrencyCode
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "European Green Energy Portfolio",
                "num_holdings": 45,
                "total_exposure": "150000000.00",
                "currency": "EUR",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class PortfolioListResponse(PaginatedResponse):
    """Paginated list of portfolio summaries"""
    items: List[PortfolioSummary]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "European Green Energy Portfolio",
                        "num_holdings": 45,
                        "total_exposure": "150000000.00",
                        "currency": "EUR",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 15,
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        }
    )


class PortfolioFilter(BaseModel):
    """Query parameters for filtering portfolios"""
    name_contains: Optional[str] = Field(default=None, description="Filter by name substring")
    currency: Optional[CurrencyCode] = None
    min_exposure: Optional[Decimal] = Field(default=None, ge=0)
    max_exposure: Optional[Decimal] = Field(default=None, ge=0)
    sector: Optional[Sector] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    @field_validator('max_exposure')
    @classmethod
    def validate_exposure_range(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """Ensure max_exposure >= min_exposure"""
        if v is not None and info.data.get('min_exposure') is not None:
            if v < info.data['min_exposure']:
                raise ValueError('max_exposure must be >= min_exposure')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_contains": "Energy",
                "currency": "EUR",
                "min_exposure": "1000000.00",
                "sector": "Power Generation"
            }
        }
    )
