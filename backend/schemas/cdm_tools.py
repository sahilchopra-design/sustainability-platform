"""
CDM Methodological Tools - Pydantic Schemas
Request/response models for CDM tools API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Tool metadata
# ---------------------------------------------------------------------------

class CDMToolSummary(BaseModel):
    """Compact tool listing."""
    code: str
    name: str
    short_name: Optional[str] = None
    category: str
    version: Optional[str] = None
    status: str = "active"


class CDMToolDetail(BaseModel):
    """Full tool detail including schemas."""
    code: str
    name: str
    short_name: Optional[str] = None
    category: str
    description: Optional[str] = None
    version: Optional[str] = None
    unfccc_reference: Optional[str] = None
    applicable_scopes: List[str] = []
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    default_parameters: Dict[str, Any] = {}
    status: str = "active"


class CDMToolListResponse(BaseModel):
    """Response for GET /cdm-tools/"""
    total: int
    tools: List[CDMToolSummary]


class CDMToolCategoryGroup(BaseModel):
    """Tools grouped by category."""
    category: str
    count: int
    tools: List[CDMToolSummary]


class CDMToolCategoriesResponse(BaseModel):
    """Response for GET /cdm-tools/categories"""
    total_categories: int
    total_tools: int
    categories: List[CDMToolCategoryGroup]


# ---------------------------------------------------------------------------
# Tool calculation
# ---------------------------------------------------------------------------

class CDMToolCalculationRequest(BaseModel):
    """Request body for POST /cdm-tools/{tool_code}/calculate"""
    inputs: Dict[str, Any] = Field(default_factory=dict,
                                    description="Input parameters for the tool")
    methodology_code: Optional[str] = Field(None,
                                             description="Optional: methodology context")
    portfolio_id: Optional[str] = Field(None,
                                         description="Optional: link to portfolio")
    project_id: Optional[str] = Field(None,
                                       description="Optional: link to project")


class CDMToolCalculationResult(BaseModel):
    """Single tool calculation result."""
    tool_code: str
    tool_name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    methodology_notes: str = ""
    unit: str = ""


class CDMToolCalculationResponse(BaseModel):
    """Response for POST /cdm-tools/{tool_code}/calculate"""
    success: bool = True
    result: CDMToolCalculationResult
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Batch / chain execution
# ---------------------------------------------------------------------------

class CDMToolBatchItem(BaseModel):
    """Single tool in a batch request."""
    tool_code: str
    inputs: Dict[str, Any] = Field(default_factory=dict)


class CDMToolBatchRequest(BaseModel):
    """Request body for POST /cdm-tools/batch"""
    tools: List[CDMToolBatchItem]
    methodology_code: Optional[str] = None
    portfolio_id: Optional[str] = None
    project_id: Optional[str] = None


class CDMToolBatchResponse(BaseModel):
    """Response for POST /cdm-tools/batch"""
    success: bool = True
    total_tools: int
    completed: int
    failed: int
    results: List[CDMToolCalculationResult]
    errors: List[Dict[str, Any]] = []


class CDMToolChainRequest(BaseModel):
    """Request body for POST /cdm-tools/chain/{methodology_code}"""
    tool_inputs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Dict mapping tool_code -> inputs for that tool"
    )
    portfolio_id: Optional[str] = None
    project_id: Optional[str] = None


class CDMToolChainResponse(BaseModel):
    """Response for POST /cdm-tools/chain/{methodology_code}"""
    success: bool = True
    methodology_code: str
    tools_executed: int
    tools_failed: int
    results: List[CDMToolCalculationResult]
    errors: List[Dict[str, Any]] = []
    aggregated_outputs: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Methodology-tool mapping
# ---------------------------------------------------------------------------

class MethodologyToolMap(BaseModel):
    """Tools required by a methodology."""
    methodology_code: str
    tools: List[CDMToolSummary]
    total_tools: int


# ---------------------------------------------------------------------------
# Activity Guide schemas
# ---------------------------------------------------------------------------

class ActivityInputGuide(BaseModel):
    """Describes one input parameter for an activity."""
    parameter: str
    label: str
    description: str
    unit: str = ""
    typical_range: Optional[Dict[str, Any]] = None
    example_value: Optional[Any] = None
    data_sources: List[str] = []
    required: bool = True
    tooltip: str = ""


class ActivityRealWorldExample(BaseModel):
    """A real-world project example."""
    project: str
    credits: int
    year: int


class ActivitySummary(BaseModel):
    """Compact activity listing."""
    id: str
    name: str
    sector: str
    scale: str
    user_types: List[str]
    value_chain_position: str
    recommended_methodology: Optional[str] = None
    typical_credit_range: Optional[Dict[str, Any]] = None


class ActivityDetail(BaseModel):
    """Full activity detail with inputs guide."""
    id: str
    name: str
    description: str
    sector: str
    user_types: List[str]
    value_chain_position: str
    applicable_methodologies: List[str]
    recommended_methodology: Optional[str] = None
    scale: str
    typical_credit_range: Optional[Dict[str, Any]] = None
    inputs_guide: List[ActivityInputGuide]
    real_world_examples: List[ActivityRealWorldExample] = []
    regulatory_notes: str = ""
    cdm_tools_needed: List[str] = []
    estimated_cost_range_usd: Optional[Dict[str, Any]] = None
    crediting_period_years: Optional[Dict[str, Any]] = None


class ActivityListResponse(BaseModel):
    """Response for GET /cdm-tools/activities"""
    total: int
    activities: List[ActivitySummary]


class ActivitySearchResponse(BaseModel):
    """Response for search endpoint."""
    query: str
    total: int
    activities: List[ActivitySummary]
