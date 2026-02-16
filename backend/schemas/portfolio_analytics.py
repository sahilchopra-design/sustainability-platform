"""
Pydantic schemas for Portfolio Aggregation and Reporting Module
Consolidates property valuations into portfolio-level analytics
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


# ============ Enums ============

class PortfolioType(str, Enum):
    FUND = "fund"
    REIT = "reit"
    SEPARATE_ACCOUNT = "separate_account"
    INDEX = "index"
    PENSION = "pension"
    INSURANCE = "insurance"


class InvestmentStrategy(str, Enum):
    CORE = "core"
    CORE_PLUS = "core_plus"
    VALUE_ADD = "value_add"
    OPPORTUNISTIC = "opportunistic"
    DEBT = "debt"


class ReportType(str, Enum):
    VALUATION = "valuation"
    CLIMATE_RISK = "climate_risk"
    SUSTAINABILITY = "sustainability"
    TCFD = "tcfd"
    INVESTOR = "investor"
    EXECUTIVE = "executive"


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============ Portfolio Schemas ============

class PortfolioBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    portfolio_type: PortfolioType = PortfolioType.FUND
    investment_strategy: Optional[InvestmentStrategy] = InvestmentStrategy.CORE
    target_return: Optional[Decimal] = Field(None, ge=0, le=100)
    aum: Decimal = Field(..., ge=0)
    currency: str = Field("USD", max_length=3)
    inception_date: Optional[date] = None


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    portfolio_type: Optional[PortfolioType] = None
    investment_strategy: Optional[InvestmentStrategy] = None
    target_return: Optional[Decimal] = None
    aum: Optional[Decimal] = None


class PortfolioResponse(PortfolioBase):
    id: UUID
    owner_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Summary stats (computed)
    total_properties: Optional[int] = 0
    total_value: Optional[Decimal] = None
    total_income: Optional[Decimal] = None
    
    model_config = ConfigDict(from_attributes=True)


class PortfolioListResponse(BaseModel):
    items: List[PortfolioResponse]
    total: int


# ============ Holdings Schemas ============

class HoldingBase(BaseModel):
    property_id: UUID
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[Decimal] = Field(None, ge=0)
    current_value: Optional[Decimal] = Field(None, ge=0)
    ownership_percentage: Decimal = Field(Decimal("1.0"), ge=0, le=1)
    annual_income: Optional[Decimal] = Field(None, ge=0)


class HoldingCreate(HoldingBase):
    pass


class HoldingResponse(HoldingBase):
    id: UUID
    portfolio_id: UUID
    unrealized_gain_loss: Optional[Decimal] = None
    property_name: Optional[str] = None
    property_type: Optional[str] = None
    property_location: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class HoldingListResponse(BaseModel):
    items: List[HoldingResponse]
    total: int
    total_value: Decimal


# ============ Analytics Schemas ============

class PortfolioSummary(BaseModel):
    total_properties: int
    total_base_value: Decimal
    total_adjusted_value: Decimal
    total_value_change: Decimal
    value_change_pct: Decimal
    total_income: Optional[Decimal] = None
    avg_yield: Optional[Decimal] = None


class RiskMetrics(BaseModel):
    weighted_avg_risk_score: Decimal
    value_at_risk_95: Decimal
    expected_shortfall: Optional[Decimal] = None
    risk_level: RiskLevel
    risk_distribution: Dict[str, int] = {}


class StrandingAnalysis(BaseModel):
    stranded_assets_count: int
    stranded_assets_value: Decimal
    stranded_pct: Decimal
    avg_years_to_stranding: Optional[Decimal] = None
    stranded_by_sector: Dict[str, int] = {}


class SustainabilityMetrics(BaseModel):
    avg_gresb_score: Optional[Decimal] = None
    pct_certified: Decimal
    certified_count: int
    avg_epc_rating: Optional[str] = None
    certifications_breakdown: Dict[str, int] = {}


class ConcentrationMetrics(BaseModel):
    hhi: Decimal
    concentration_level: str
    top_items: List[Dict[str, Any]] = []


class ConcentrationAnalysis(BaseModel):
    geographic: ConcentrationMetrics
    sector: ConcentrationMetrics
    risk: Optional[ConcentrationMetrics] = None


class PortfolioAnalyticsRequest(BaseModel):
    scenario_id: Optional[UUID] = None
    time_horizon: int = Field(10, ge=1, le=30)
    as_of_date: Optional[date] = None


class PortfolioAnalyticsResponse(BaseModel):
    portfolio_id: UUID
    calculation_date: date
    scenario_name: Optional[str] = None
    
    portfolio_summary: PortfolioSummary
    risk_metrics: RiskMetrics
    stranding_analysis: StrandingAnalysis
    sustainability_metrics: SustainabilityMetrics
    concentration_analysis: ConcentrationAnalysis


# ============ Scenario Comparison Schemas ============

class ScenarioComparisonRequest(BaseModel):
    scenario_ids: List[UUID] = Field(..., min_length=1)
    time_horizon: int = Field(10, ge=1, le=30)


class ScenarioComparisonRow(BaseModel):
    scenario_id: UUID
    scenario_name: str
    total_value: Decimal
    value_change: Decimal
    value_change_pct: Decimal
    stranded_count: int
    stranded_value: Decimal
    var_95: Decimal
    avg_risk_score: Decimal


class ScenarioComparisonResult(BaseModel):
    portfolio_id: UUID
    base_value: Decimal
    comparison_table: List[ScenarioComparisonRow]
    best_scenario: str
    worst_scenario: str
    value_spread: Decimal
    key_insights: List[str] = []


# ============ Reporting Schemas ============

class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat = ReportFormat.JSON
    scenario_id: Optional[UUID] = None
    time_horizon: int = Field(10, ge=1, le=30)
    include_charts: bool = True
    include_property_details: bool = False
    custom_sections: List[str] = []


class ReportResponse(BaseModel):
    report_id: UUID
    portfolio_id: UUID
    report_type: ReportType
    format: ReportFormat
    status: str  # 'pending', 'processing', 'completed', 'failed'
    download_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ReportContent(BaseModel):
    report_id: UUID
    report_type: ReportType
    generated_at: datetime
    
    # Common sections
    executive_summary: Dict[str, Any] = {}
    portfolio_overview: Dict[str, Any] = {}
    
    # Type-specific sections
    valuation_details: Optional[Dict[str, Any]] = None
    climate_risk_details: Optional[Dict[str, Any]] = None
    sustainability_details: Optional[Dict[str, Any]] = None
    tcfd_details: Optional[Dict[str, Any]] = None
    
    # Charts and visualizations (base64 or URLs)
    charts: Dict[str, str] = {}
    
    # Appendices
    appendices: List[Dict[str, Any]] = []


# ============ Dashboard Schemas ============

class KPICard(BaseModel):
    id: str
    label: str
    value: Any
    change: Optional[Decimal] = None
    change_period: Optional[str] = None
    trend: Optional[str] = None  # 'up', 'down', 'stable'
    icon: Optional[str] = None
    color: Optional[str] = None


class ChartData(BaseModel):
    chart_type: str  # 'bar', 'pie', 'line', 'heatmap', 'radar'
    title: str
    data: List[Dict[str, Any]]
    config: Dict[str, Any] = {}


class Alert(BaseModel):
    id: str
    severity: str  # 'info', 'warning', 'critical'
    title: str
    message: str
    property_id: Optional[UUID] = None
    property_name: Optional[str] = None
    action_required: bool = False
    created_at: datetime


class DashboardRequest(BaseModel):
    scenario_id: Optional[UUID] = None
    time_horizon: int = Field(10, ge=1, le=30)


class DashboardResponse(BaseModel):
    portfolio_id: UUID
    portfolio_name: str
    last_updated: datetime
    
    kpi_cards: List[KPICard]
    charts: Dict[str, ChartData]
    alerts: List[Alert]
    
    # Quick stats
    total_aum: Decimal
    property_count: int
    avg_risk_score: Decimal
    sustainability_score: Optional[Decimal] = None


# ============ Property Summary for Holdings ============

class PropertySummary(BaseModel):
    id: UUID
    name: str
    property_type: str
    location: str
    current_value: Decimal
    base_value: Optional[Decimal] = None
    value_change_pct: Optional[Decimal] = None
    risk_score: Optional[Decimal] = None
    gresb_score: Optional[Decimal] = None
    certifications: List[str] = []
    is_stranded: bool = False
    years_to_stranding: Optional[Decimal] = None


class PortfolioHoldingDetail(BaseModel):
    holding: HoldingResponse
    property_details: PropertySummary
    valuation_summary: Dict[str, Any] = {}
