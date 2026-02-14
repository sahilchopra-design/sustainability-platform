"""Scenario analysis request/response schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict

from schemas.common import (
    Sector, ScenarioType, VelocityTrajectory, TimestampMixin
)


class RunScenarioAnalysisRequest(BaseModel):
    """Request to run scenario analysis on portfolio"""
    portfolio_id: str = Field(description="Portfolio UUID to analyze")
    scenario_ids: List[str] = Field(
        min_length=1,
        description="Scenario UUIDs to analyze"
    )
    time_horizons: List[int] = Field(
        min_length=1,
        description="Target years for analysis (e.g., [2030, 2040, 2050])"
    )
    include_counterparty_detail: bool = Field(
        default=False,
        description="Include granular counterparty-level results"
    )
    include_sector_breakdown: bool = Field(
        default=True,
        description="Include sector-level breakdown"
    )
    include_geographic_breakdown: bool = Field(
        default=True,
        description="Include geographic breakdown"
    )
    
    @field_validator('time_horizons')
    @classmethod
    def validate_horizons(cls, v: List[int]) -> List[int]:
        """Ensure horizons are in valid range and sorted"""
        for horizon in v:
            if horizon < 2025 or horizon > 2100:
                raise ValueError('Time horizons must be between 2025 and 2100')
        return sorted(v)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_ids": [
                    "660e8400-e29b-41d4-a716-446655440001",
                    "770e8400-e29b-41d4-a716-446655440002"
                ],
                "time_horizons": [2030, 2040, 2050],
                "include_counterparty_detail": True,
                "include_sector_breakdown": True,
                "include_geographic_breakdown": True
            }
        }
    )


class RatingMigration(BaseModel):
    """Credit rating migration statistics"""
    upgrades: int = Field(ge=0, description="Number of upgrades")
    downgrades: int = Field(ge=0, description="Number of downgrades")
    stable: int = Field(ge=0, description="Number of stable ratings")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "upgrades": 3,
                "downgrades": 12,
                "stable": 30
            }
        }
    )


class PortfolioMetrics(BaseModel):
    """Portfolio-level risk metrics for a scenario"""
    scenario_id: str
    scenario_name: str
    scenario_type: ScenarioType
    time_horizon: int
    
    # Adjusted risk parameters
    adjusted_pd: Decimal = Field(decimal_places=4, description="Adjusted Probability of Default")
    adjusted_lgd: Decimal = Field(decimal_places=4, description="Adjusted Loss Given Default")
    pd_change_pct: Decimal = Field(decimal_places=2, description="PD change vs baseline (%)")
    
    # Loss metrics
    expected_loss: Decimal = Field(decimal_places=2, description="Expected Loss in currency")
    expected_loss_pct: Decimal = Field(decimal_places=2, description="Expected Loss as % of exposure")
    
    # VaR metrics
    value_at_risk_95: Decimal = Field(decimal_places=2, description="95% VaR")
    value_at_risk_99: Decimal = Field(decimal_places=2, description="99% VaR")
    
    # Return metrics
    risk_adjusted_return: Decimal = Field(decimal_places=2, description="Return after risk adjustment (%)")
    
    # Concentration metrics
    sector_hhi: Decimal = Field(decimal_places=4, description="Sector HHI (0-1)")
    geographic_hhi: Decimal = Field(decimal_places=4, description="Geographic HHI (0-1)")
    
    # Climate risk contribution
    climate_risk_contribution_pct: Decimal = Field(
        decimal_places=2,
        description="Portion of risk attributable to climate factors (%)"
    )
    
    # Rating migrations
    rating_migrations: RatingMigration
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario_id": "660e8400-e29b-41d4-a716-446655440001",
                "scenario_name": "Net Zero 2050",
                "scenario_type": "Orderly",
                "time_horizon": 2050,
                "adjusted_pd": "0.0325",
                "adjusted_lgd": "0.4650",
                "pd_change_pct": "38.30",
                "expected_loss": "2250000.00",
                "expected_loss_pct": "1.50",
                "value_at_risk_95": "3500000.00",
                "value_at_risk_99": "5000000.00",
                "risk_adjusted_return": "3.45",
                "sector_hhi": "0.2450",
                "geographic_hhi": "0.3025",
                "climate_risk_contribution_pct": "65.50",
                "rating_migrations": {
                    "upgrades": 3,
                    "downgrades": 12,
                    "stable": 30
                }
            }
        }
    )


class SectorExposure(BaseModel):
    """Sector-level exposure and risk"""
    sector: Sector
    exposure_amount: Decimal = Field(decimal_places=2)
    exposure_pct: Decimal = Field(decimal_places=2, description="% of total exposure")
    num_holdings: int
    avg_adjusted_pd: Decimal = Field(decimal_places=4)
    expected_loss: Decimal = Field(decimal_places=2)
    climate_risk_score: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=1,
        description="Composite climate risk score (0-100)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sector": "Power Generation",
                "exposure_amount": "52500000.00",
                "exposure_pct": "35.00",
                "num_holdings": 18,
                "avg_adjusted_pd": "0.0285",
                "expected_loss": "750000.00",
                "climate_risk_score": "72.5"
            }
        }
    )


class GeographicExposure(BaseModel):
    """Geographic exposure and risk"""
    country_code: str = Field(min_length=2, max_length=3)
    country_name: Optional[str] = None
    exposure_amount: Decimal = Field(decimal_places=2)
    exposure_pct: Decimal = Field(decimal_places=2)
    num_holdings: int
    avg_adjusted_pd: Decimal = Field(decimal_places=4)
    expected_loss: Decimal = Field(decimal_places=2)
    physical_risk_score: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        description="Physical climate risk score for region"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "country_code": "DK",
                "country_name": "Denmark",
                "exposure_amount": "25000000.00",
                "exposure_pct": "16.67",
                "num_holdings": 8,
                "avg_adjusted_pd": "0.0210",
                "expected_loss": "250000.00",
                "physical_risk_score": "35.5"
            }
        }
    )


class CounterpartyScenarioDetail(BaseModel):
    """Counterparty-level scenario results"""
    counterparty_id: str
    counterparty_name: str
    sector: Sector
    exposure_amount: Decimal = Field(decimal_places=2)
    baseline_pd: Decimal = Field(decimal_places=4)
    adjusted_pd: Decimal = Field(decimal_places=4)
    pd_change_pct: Decimal = Field(decimal_places=2)
    expected_loss: Decimal = Field(decimal_places=2)
    velocity_score: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        description="Rate of PD change over time"
    )
    velocity_trajectory: Optional[VelocityTrajectory] = None
    pd_contribution_breakdown: Optional[Dict[str, Decimal]] = Field(
        default=None,
        description="Breakdown of PD contributors (transition, physical, etc.)"
    )
    alert_triggered: bool = Field(
        default=False,
        description="Whether counterparty exceeds risk thresholds"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "counterparty_id": "880e8400-e29b-41d4-a716-446655440003",
                "counterparty_name": "Orsted A/S",
                "sector": "Power Generation",
                "exposure_amount": "5000000.00",
                "baseline_pd": "0.0150",
                "adjusted_pd": "0.0185",
                "pd_change_pct": "23.33",
                "expected_loss": "41625.00",
                "velocity_score": "1.25",
                "velocity_trajectory": "Converging",
                "pd_contribution_breakdown": {
                    "transition_risk": "0.0025",
                    "physical_risk": "0.0010"
                },
                "alert_triggered": False
            }
        }
    )


class ScenarioResultResponse(BaseModel):
    """Complete scenario analysis results"""
    analysis_id: str = Field(description="Unique analysis run ID")
    portfolio_id: str
    portfolio_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    portfolio_metrics: List[PortfolioMetrics] = Field(
        description="Portfolio-level metrics for each scenario/horizon"
    )
    sector_breakdown: Optional[List[SectorExposure]] = None
    geographic_breakdown: Optional[List[GeographicExposure]] = None
    counterparty_details: Optional[List[CounterpartyScenarioDetail]] = None
    
    metadata: Optional[Dict] = Field(
        default=None,
        description="Additional analysis metadata"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ScenarioComparisonRequest(BaseModel):
    """Request to compare scenarios"""
    portfolio_id: str
    scenario_ids: List[str] = Field(min_length=2, max_length=5)
    time_horizon: int = Field(ge=2025, le=2100)
    comparison_metrics: List[str] = Field(
        default=["expected_loss", "adjusted_pd", "var_95"],
        description="Metrics to compare"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_ids": [
                    "660e8400-e29b-41d4-a716-446655440001",
                    "770e8400-e29b-41d4-a716-446655440002",
                    "880e8400-e29b-41d4-a716-446655440003"
                ],
                "time_horizon": 2050,
                "comparison_metrics": [
                    "expected_loss",
                    "adjusted_pd",
                    "value_at_risk_95",
                    "climate_risk_contribution_pct"
                ]
            }
        }
    )


class ScenarioComparison(BaseModel):
    """Single metric comparison across scenarios"""
    metric_name: str
    metric_label: str
    unit: Optional[str] = None
    values: Dict[str, Decimal] = Field(
        description="Scenario name -> value mapping"
    )
    ranking: List[str] = Field(
        description="Scenarios ordered by metric value"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metric_name": "expected_loss",
                "metric_label": "Expected Loss",
                "unit": "USD",
                "values": {
                    "Net Zero 2050": "2250000.00",
                    "Delayed Transition": "3500000.00",
                    "Current Policies": "1800000.00"
                },
                "ranking": [
                    "Current Policies",
                    "Net Zero 2050",
                    "Delayed Transition"
                ]
            }
        }
    )


class ScenarioComparisonResponse(BaseModel):
    """Comparison of multiple scenarios"""
    portfolio_id: str
    portfolio_name: str
    time_horizon: int
    scenarios: List[str] = Field(description="Scenario names being compared")
    comparisons: List[ScenarioComparison]
    best_case_scenario: str = Field(
        description="Scenario with lowest overall risk"
    )
    worst_case_scenario: str = Field(
        description="Scenario with highest overall risk"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "portfolio_name": "European Green Energy Portfolio",
                "time_horizon": 2050,
                "scenarios": ["Net Zero 2050", "Delayed Transition", "Current Policies"],
                "comparisons": [],
                "best_case_scenario": "Current Policies",
                "worst_case_scenario": "Delayed Transition"
            }
        }
    )
