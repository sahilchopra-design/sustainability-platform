"""
Pydantic schemas for Interactive Scenario Builder and Sensitivity Analysis Module
Enables real-time what-if analysis, scenario comparison, and sensitivity testing
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


# ============ Enums ============

class ModificationType(str, Enum):
    RENT_GROWTH = "rent_growth"
    VACANCY = "vacancy"
    EXPENSES = "expenses"
    CAP_RATE = "cap_rate"
    EXIT_CAP_RATE = "exit_cap_rate"
    CERTIFICATION = "certification"
    RETROFIT = "retrofit"
    CLIMATE = "climate"
    DISCOUNT_RATE = "discount_rate"
    NOI = "noi"
    RENT_PSF = "rent_psf"


class ChangeType(str, Enum):
    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"


class SensitivityVariableEnum(str, Enum):
    CAP_RATE = "cap_rate"
    RENT_GROWTH = "rent_growth"
    VACANCY_RATE = "vacancy_rate"
    EXPENSE_RATIO = "expense_ratio"
    EXIT_CAP_RATE = "exit_cap_rate"
    DISCOUNT_RATE = "discount_rate"
    NOI = "noi"
    RENT_PSF = "rent_psf"


# ============ Modification Schemas ============

from typing import Union

class ScenarioModification(BaseModel):
    type: ModificationType
    parameter: str
    new_value: Union[float, str]  # Can be float for numeric params or string for CERTIFICATION/CLIMATE
    description: Optional[str] = None


class ComponentImpact(BaseModel):
    modification: str
    parameter: str
    old_value: Optional[float] = None
    new_value: Union[float, str]  # Can be float or string
    impact: Decimal
    impact_pct: Decimal


# ============ Scenario Builder Schemas ============

class ScenarioBuildRequest(BaseModel):
    base_property_id: UUID
    scenario_name: str = Field(..., max_length=255)
    description: Optional[str] = None
    modifications: List[ScenarioModification] = Field(..., min_length=1)


class ScenarioBuildResult(BaseModel):
    scenario_id: UUID
    scenario_name: str
    base_value: Decimal
    adjusted_value: Decimal
    value_change: Decimal
    value_change_pct: Decimal
    component_impacts: List[ComponentImpact]
    modifications_applied: int


class ScenarioBase(BaseModel):
    scenario_name: str = Field(..., max_length=255)
    description: Optional[str] = None
    base_property_id: Optional[UUID] = None
    modifications: List[Dict[str, Any]] = []
    base_value: Optional[Decimal] = None
    adjusted_value: Optional[Decimal] = None
    value_change_pct: Optional[Decimal] = None


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ScenarioListResponse(BaseModel):
    items: List[ScenarioResponse]
    total: int


# ============ Scenario Comparison Schemas ============

class ScenarioComparisonRequest(BaseModel):
    base_property_id: UUID
    scenario_ids: List[UUID] = Field(..., min_length=1)
    metrics: List[str] = ["value", "noi", "cap_rate", "irr"]


class ScenarioComparisonRow(BaseModel):
    scenario_id: UUID
    scenario_name: str
    value: Decimal
    value_change_pct: Decimal
    noi: Optional[Decimal] = None
    cap_rate: Optional[Decimal] = None
    irr: Optional[Decimal] = None
    expense_ratio: Optional[Decimal] = None


class ScenarioComparisonResult(BaseModel):
    comparison_table: List[ScenarioComparisonRow]
    best_scenario: str
    worst_scenario: str
    key_differentiators: List[str]
    base_value: Decimal


class BatchScenarioRequest(BaseModel):
    base_property_id: UUID
    scenario_templates: List[Dict[str, Any]]


class BatchScenarioResult(BaseModel):
    scenarios: List[ScenarioBuildResult]
    total_created: int


# ============ Sensitivity Analysis Schemas ============

class VariableRange(BaseModel):
    min: float
    max: float


class SensitivityVariable(BaseModel):
    name: str
    base_value: float
    range: VariableRange
    steps: int = Field(10, ge=2, le=50)


class SensitivityDataPoint(BaseModel):
    variable_value: float
    valuation: Decimal
    change_from_base: Decimal
    change_pct: Decimal


class SensitivityAnalyzeRequest(BaseModel):
    property_id: UUID
    base_valuation: Optional[Decimal] = None
    variables: List[SensitivityVariable] = Field(..., min_length=1)


class TornadoDataPoint(BaseModel):
    variable: str
    low_impact: Decimal
    high_impact: Decimal
    swing: Decimal
    low_value: Optional[float] = None
    high_value: Optional[float] = None
    base_value: Optional[float] = None


class SpiderChartScenario(BaseModel):
    name: str
    values: List[float]


class SpiderChartData(BaseModel):
    variables: List[str]
    scenarios: List[SpiderChartScenario]


class SensitivityAnalyzeResult(BaseModel):
    property_id: UUID
    base_valuation: Decimal
    sensitivities: Dict[str, List[SensitivityDataPoint]]
    tornado_data: List[TornadoDataPoint]
    spider_chart_data: Optional[SpiderChartData] = None


class TornadoRequest(BaseModel):
    property_id: UUID
    base_valuation: Decimal
    variables: List[Dict[str, Any]]  # [{name, base, low, high}]


class SpiderRequest(BaseModel):
    property_id: UUID
    base_valuation: Decimal
    variables: List[str]
    variation_range: float = Field(0.2, ge=0.05, le=0.5)  # +/- percentage


# ============ What-If Analysis Schemas ============

class WhatIfChange(BaseModel):
    parameter: str
    change_type: ChangeType
    change_value: float


class WhatIfRequest(BaseModel):
    property_id: UUID
    changes: List[WhatIfChange] = Field(..., min_length=1)
    cascade_effects: bool = True


class ChangeBreakdown(BaseModel):
    parameter: str
    old_value: float
    new_value: float
    direct_impact: Decimal
    cascading_impacts: Decimal
    total_impact: Decimal


class WhatIfResult(BaseModel):
    property_id: UUID
    base_valuation: Decimal
    adjusted_valuation: Decimal
    total_change: Decimal
    total_change_pct: Decimal
    change_breakdown: List[ChangeBreakdown]
    cascade_effects_applied: bool


# ============ Quick Scenario Templates ============

class ScenarioTemplate(BaseModel):
    name: str
    description: str
    modifications: List[ScenarioModification]
    category: str  # 'optimistic', 'pessimistic', 'stress_test', 'green_upgrade'


class TemplateListResponse(BaseModel):
    templates: List[ScenarioTemplate]
    total: int


# ============ Analysis History ============

class SensitivityAnalysisBase(BaseModel):
    property_id: UUID
    valuation_id: Optional[UUID] = None
    variable_name: str
    base_value: Decimal
    min_value: Decimal
    max_value: Decimal
    step_size: Decimal
    results: List[Dict[str, Any]] = []


class SensitivityAnalysisCreate(SensitivityAnalysisBase):
    pass


class SensitivityAnalysisResponse(SensitivityAnalysisBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ Dashboard Schemas ============

class ScenarioAnalysisDashboard(BaseModel):
    total_scenarios: int
    total_analyses: int
    recent_scenarios: List[ScenarioResponse]
    most_impactful_variables: List[TornadoDataPoint]
    avg_value_swing_pct: Decimal
