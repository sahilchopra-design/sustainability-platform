"""
CDM Methodological Tools & Activity Guide - API Routes
Provides endpoints for tool browsing, execution, methodology mapping,
and the Activity Guide for user accessibility.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from schemas.cdm_tools import (
    CDMToolSummary,
    CDMToolDetail,
    CDMToolListResponse,
    CDMToolCategoryGroup,
    CDMToolCategoriesResponse,
    CDMToolCalculationRequest,
    CDMToolCalculationResult,
    CDMToolCalculationResponse,
    CDMToolBatchRequest,
    CDMToolBatchResponse,
    CDMToolChainRequest,
    CDMToolChainResponse,
    MethodologyToolMap,
    ActivitySummary,
    ActivityDetail,
    ActivityListResponse,
    ActivitySearchResponse,
    ActivityInputGuide,
    ActivityRealWorldExample,
)

from services.cdm_tools_engine import (
    CDM_TOOLS_REGISTRY,
    CDM_TOOL_CALCULATORS,
    METHODOLOGY_TOOL_DEPENDENCIES,
    CDMToolCategory,
    calculate_cdm_tool,
    get_tools_for_methodology,
    get_tool_details,
    execute_tool_chain,
    get_all_tools,
    get_tools_by_category,
)

# Import activity guide catalog (lazy — may not be ready yet)
try:
    from services.activity_guide_catalog import (
        ACTIVITY_CATALOG,
        get_all_activities,
        get_activities_by_sector,
        get_activities_by_user_type,
        get_activities_for_methodology,
        get_activity_detail,
        search_activities,
        get_activities_by_value_chain,
        get_activities_by_scale,
    )
    _ACTIVITY_GUIDE_AVAILABLE = True
except ImportError:
    _ACTIVITY_GUIDE_AVAILABLE = False
    ACTIVITY_CATALOG = {}

router = APIRouter(prefix="/api/v1/cdm-tools", tags=["CDM Methodological Tools"])


# =========================================================================
# CDM Tool endpoints
# =========================================================================

@router.get("/", response_model=CDMToolListResponse)
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query("active", description="Filter by status"),
):
    """List all 43 CDM methodological tools."""
    if category:
        try:
            cat_enum = CDMToolCategory(category.upper())
        except ValueError:
            raise HTTPException(400, f"Unknown category: {category}")
        tools = get_tools_by_category(cat_enum.value)
    else:
        tools = get_all_tools()

    if status:
        tools = [t for t in tools if t.get("status", "active") == status]

    summaries = [
        CDMToolSummary(
            code=t["code"],
            name=t["name"],
            short_name=t.get("short_name"),
            category=t["category"],
            version=t.get("version"),
            status=t.get("status", "active"),
        )
        for t in tools
    ]
    return CDMToolListResponse(total=len(summaries), tools=summaries)


@router.get("/categories", response_model=CDMToolCategoriesResponse)
async def list_tool_categories():
    """Get tools grouped by category."""
    all_tools = get_all_tools()
    by_cat: Dict[str, List[Dict]] = defaultdict(list)
    for t in all_tools:
        by_cat[t["category"]].append(t)

    groups = []
    for cat_name, cat_tools in sorted(by_cat.items()):
        groups.append(CDMToolCategoryGroup(
            category=cat_name,
            count=len(cat_tools),
            tools=[
                CDMToolSummary(
                    code=t["code"],
                    name=t["name"],
                    short_name=t.get("short_name"),
                    category=t["category"],
                    version=t.get("version"),
                    status=t.get("status", "active"),
                )
                for t in cat_tools
            ],
        ))
    return CDMToolCategoriesResponse(
        total_categories=len(groups),
        total_tools=len(all_tools),
        categories=groups,
    )


@router.get("/for-methodology/{methodology_code}", response_model=MethodologyToolMap)
async def tools_for_methodology(methodology_code: str):
    """Get CDM tools required by a specific methodology."""
    tool_codes = get_tools_for_methodology(methodology_code)
    if not tool_codes:
        raise HTTPException(404, f"No tool mapping for methodology: {methodology_code}")

    tool_summaries = []
    for code in tool_codes:
        detail = get_tool_details(code)
        if detail:
            tool_summaries.append(CDMToolSummary(
                code=detail["code"],
                name=detail["name"],
                short_name=detail.get("short_name"),
                category=detail["category"],
                version=detail.get("version"),
                status=detail.get("status", "active"),
            ))
    return MethodologyToolMap(
        methodology_code=methodology_code,
        tools=tool_summaries,
        total_tools=len(tool_summaries),
    )


@router.get("/{tool_code}", response_model=CDMToolDetail)
async def get_tool(tool_code: str):
    """Get full detail for a specific CDM tool."""
    detail = get_tool_details(tool_code.upper())
    if not detail:
        raise HTTPException(404, f"Tool not found: {tool_code}")
    return CDMToolDetail(**detail)


@router.get("/{tool_code}/defaults")
async def get_tool_defaults(tool_code: str):
    """Get default parameter values for a CDM tool."""
    detail = get_tool_details(tool_code.upper())
    if not detail:
        raise HTTPException(404, f"Tool not found: {tool_code}")
    return {
        "tool_code": detail["code"],
        "tool_name": detail["name"],
        "default_parameters": detail.get("default_parameters", {}),
    }


@router.post("/{tool_code}/calculate", response_model=CDMToolCalculationResponse)
async def calculate_tool(tool_code: str, request: CDMToolCalculationRequest):
    """Execute a single CDM tool calculation."""
    code = tool_code.upper()
    if code not in CDM_TOOL_CALCULATORS:
        raise HTTPException(404, f"Tool not found: {tool_code}")

    t0 = time.perf_counter()
    try:
        result = calculate_cdm_tool(code, request.inputs)
    except Exception as e:
        return CDMToolCalculationResponse(
            success=False,
            result=CDMToolCalculationResult(
                tool_code=code,
                tool_name=CDM_TOOLS_REGISTRY.get(code, {}).get("name", code),
                inputs=request.inputs,
                outputs={},
                methodology_notes=str(e),
                unit="",
            ),
            error=str(e),
        )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return CDMToolCalculationResponse(
        success=True,
        result=CDMToolCalculationResult(**result),
        execution_time_ms=elapsed_ms,
    )


@router.post("/batch", response_model=CDMToolBatchResponse)
async def batch_calculate(request: CDMToolBatchRequest):
    """Execute multiple CDM tools in sequence."""
    results: List[CDMToolCalculationResult] = []
    errors: List[Dict[str, Any]] = []

    for item in request.tools:
        code = item.tool_code.upper()
        try:
            result = calculate_cdm_tool(code, item.inputs)
            results.append(CDMToolCalculationResult(**result))
        except Exception as e:
            errors.append({"tool_code": code, "error": str(e)})

    return CDMToolBatchResponse(
        success=len(errors) == 0,
        total_tools=len(request.tools),
        completed=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
    )


@router.post("/chain/{methodology_code}", response_model=CDMToolChainResponse)
async def chain_calculate(methodology_code: str, request: CDMToolChainRequest):
    """Execute the full CDM tool chain for a methodology."""
    try:
        chain_result = execute_tool_chain(methodology_code, request.tool_inputs)
    except Exception as e:
        raise HTTPException(400, str(e))

    tool_results = [
        CDMToolCalculationResult(**r)
        for r in chain_result.get("results", [])
    ]

    tools_exec = chain_result.get("tools_executed", [])
    errs = chain_result.get("errors", [])
    summary = chain_result.get("summary", {})

    return CDMToolChainResponse(
        success=len(errs) == 0,
        methodology_code=methodology_code,
        tools_executed=len(tools_exec) if isinstance(tools_exec, list) else tools_exec,
        tools_failed=summary.get("errors_count", len(errs)),
        results=tool_results,
        errors=errs,
        aggregated_outputs=summary,
    )


# =========================================================================
# Activity Guide endpoints
# =========================================================================

@router.get("/activities", response_model=ActivityListResponse)
async def list_activities(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    user_type: Optional[str] = Query(None, description="Filter by user type"),
    scale: Optional[str] = Query(None, description="Filter by scale (Large/Small/Micro)"),
    value_chain: Optional[str] = Query(None, description="Filter by value chain position (upstream/core/downstream)"),
    methodology: Optional[str] = Query(None, description="Filter by methodology code"),
):
    """List all activities with optional filters."""
    if not _ACTIVITY_GUIDE_AVAILABLE:
        raise HTTPException(503, "Activity guide catalog not available")

    # Start with all activities
    activities = get_all_activities()

    # Apply filters
    if sector:
        activities = [a for a in activities if a.get("sector", "").lower() == sector.lower()]
    if user_type:
        activities = [
            a for a in activities
            if any(ut.lower() == user_type.lower() for ut in a.get("user_types", []))
        ]
    if scale:
        activities = [a for a in activities if a.get("scale", "").lower() == scale.lower()]
    if value_chain:
        activities = [
            a for a in activities
            if a.get("value_chain_position", "").lower() == value_chain.lower()
        ]
    if methodology:
        activities = [
            a for a in activities
            if methodology.upper() in [m.upper() for m in a.get("applicable_methodologies", [])]
        ]

    summaries = [
        ActivitySummary(
            id=a["id"],
            name=a["name"],
            sector=a.get("sector", ""),
            scale=a.get("scale", ""),
            user_types=a.get("user_types", []),
            value_chain_position=a.get("value_chain_position", "core"),
            recommended_methodology=a.get("recommended_methodology"),
            typical_credit_range=a.get("typical_credit_range"),
        )
        for a in activities
    ]
    return ActivityListResponse(total=len(summaries), activities=summaries)


@router.get("/activities/for-user/{user_type}", response_model=ActivityListResponse)
async def activities_for_user(user_type: str):
    """Get activities recommended for a specific user type."""
    if not _ACTIVITY_GUIDE_AVAILABLE:
        raise HTTPException(503, "Activity guide catalog not available")

    activities = get_activities_by_user_type(user_type)
    summaries = [
        ActivitySummary(
            id=a["id"],
            name=a["name"],
            sector=a.get("sector", ""),
            scale=a.get("scale", ""),
            user_types=a.get("user_types", []),
            value_chain_position=a.get("value_chain_position", "core"),
            recommended_methodology=a.get("recommended_methodology"),
            typical_credit_range=a.get("typical_credit_range"),
        )
        for a in activities
    ]
    return ActivityListResponse(total=len(summaries), activities=summaries)


@router.get("/activities/search", response_model=ActivitySearchResponse)
async def search_activities_endpoint(
    q: str = Query(..., description="Search query"),
):
    """Search activities by keyword."""
    if not _ACTIVITY_GUIDE_AVAILABLE:
        raise HTTPException(503, "Activity guide catalog not available")

    results = search_activities(q)
    summaries = [
        ActivitySummary(
            id=a["id"],
            name=a["name"],
            sector=a.get("sector", ""),
            scale=a.get("scale", ""),
            user_types=a.get("user_types", []),
            value_chain_position=a.get("value_chain_position", "core"),
            recommended_methodology=a.get("recommended_methodology"),
            typical_credit_range=a.get("typical_credit_range"),
        )
        for a in results
    ]
    return ActivitySearchResponse(query=q, total=len(summaries), activities=summaries)


@router.get("/activities/{activity_id}", response_model=ActivityDetail)
async def get_activity(activity_id: str):
    """Get full detail for an activity including inputs guide."""
    if not _ACTIVITY_GUIDE_AVAILABLE:
        raise HTTPException(503, "Activity guide catalog not available")

    detail = get_activity_detail(activity_id)
    if not detail:
        raise HTTPException(404, f"Activity not found: {activity_id}")

    return ActivityDetail(
        id=detail["id"],
        name=detail["name"],
        description=detail.get("description", ""),
        sector=detail.get("sector", ""),
        user_types=detail.get("user_types", []),
        value_chain_position=detail.get("value_chain_position", "core"),
        applicable_methodologies=detail.get("applicable_methodologies", []),
        recommended_methodology=detail.get("recommended_methodology"),
        scale=detail.get("scale", ""),
        typical_credit_range=detail.get("typical_credit_range"),
        inputs_guide=[
            ActivityInputGuide(**ig) for ig in detail.get("inputs_guide", [])
        ],
        real_world_examples=[
            ActivityRealWorldExample(**ex) for ex in detail.get("real_world_examples", [])
        ],
        regulatory_notes=detail.get("regulatory_notes", ""),
        cdm_tools_needed=detail.get("cdm_tools_needed", []),
        estimated_cost_range_usd=detail.get("estimated_cost_range_usd"),
        crediting_period_years=detail.get("crediting_period_years"),
    )


@router.get("/activities/{activity_id}/inputs")
async def get_activity_inputs(activity_id: str):
    """Get detailed input guide with data sourcing info for an activity."""
    if not _ACTIVITY_GUIDE_AVAILABLE:
        raise HTTPException(503, "Activity guide catalog not available")

    detail = get_activity_detail(activity_id)
    if not detail:
        raise HTTPException(404, f"Activity not found: {activity_id}")

    return {
        "activity_id": activity_id,
        "activity_name": detail["name"],
        "recommended_methodology": detail.get("recommended_methodology"),
        "inputs": detail.get("inputs_guide", []),
        "cdm_tools_needed": detail.get("cdm_tools_needed", []),
    }
