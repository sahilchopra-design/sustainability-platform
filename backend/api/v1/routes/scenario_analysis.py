"""
Interactive Scenario Builder and Sensitivity Analysis API Routes
Enables real-time what-if analysis, scenario comparison, and sensitivity testing
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID
from decimal import Decimal

from schemas.scenario_analysis import (
    # Scenario Builder
    ScenarioBuildRequest, ScenarioBuildResult,
    ScenarioResponse, ScenarioListResponse,
    ScenarioComparisonRequest, ScenarioComparisonResult,
    BatchScenarioRequest, BatchScenarioResult,
    ScenarioTemplate, TemplateListResponse,
    # Sensitivity Analysis
    SensitivityAnalyzeRequest, SensitivityAnalyzeResult,
    SensitivityVariable, VariableRange,
    TornadoRequest, SpiderRequest,
    TornadoDataPoint,
    # What-If Analysis
    WhatIfRequest, WhatIfResult,
    # Dashboard
    ScenarioAnalysisDashboard,
)
from services.scenario_analysis_engine import (
    InteractiveScenarioEngine,
    get_scenario_templates,
    get_sample_properties,
    list_scenarios,
    get_scenario,
)

router = APIRouter(prefix="/api/v1/scenarios", tags=["Scenario Analysis"])

# Initialize engine
scenario_engine = InteractiveScenarioEngine()


# ============ Dashboard ============

@router.get("/dashboard", response_model=ScenarioAnalysisDashboard)
async def get_dashboard():
    """Get scenario analysis dashboard with KPIs and recent scenarios."""
    scenarios = list_scenarios()
    
    # Get recent scenarios
    recent = sorted(scenarios, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    recent_scenarios = [
        ScenarioResponse(
            id=UUID(s["id"]),
            scenario_name=s["scenario_name"],
            description=s.get("description"),
            base_property_id=UUID(s["base_property_id"]) if s.get("base_property_id") else None,
            modifications=s.get("modifications", []),
            base_value=Decimal(str(s.get("base_value", 0))),
            adjusted_value=Decimal(str(s.get("adjusted_value", 0))),
            value_change_pct=Decimal(str(s.get("value_change_pct", 0))),
            created_at=datetime.fromisoformat(s["created_at"]) if s.get("created_at") else datetime.now(timezone.utc),
        )
        for s in recent
    ]
    
    # Most impactful variables (sample data)
    impactful_vars = [
        TornadoDataPoint(variable="Cap Rate", low_impact=Decimal("-15.2"), high_impact=Decimal("18.5"), swing=Decimal("33.7")),
        TornadoDataPoint(variable="Rent Growth", low_impact=Decimal("-12.1"), high_impact=Decimal("14.3"), swing=Decimal("26.4")),
        TornadoDataPoint(variable="Vacancy Rate", low_impact=Decimal("8.2"), high_impact=Decimal("-10.5"), swing=Decimal("18.7")),
    ]
    
    return ScenarioAnalysisDashboard(
        total_scenarios=len(scenarios),
        total_analyses=len(scenarios) * 2,  # Estimate
        recent_scenarios=recent_scenarios,
        most_impactful_variables=impactful_vars,
        avg_value_swing_pct=Decimal("18.5"),
    )


# ============ Scenario Builder ============

@router.post("/build", response_model=ScenarioBuildResult)
async def build_scenario(request: ScenarioBuildRequest):
    """
    Build a custom scenario with modifications.
    
    Supported modification types:
    - rent_growth: Change rent growth rate
    - vacancy: Change vacancy rate
    - expenses: Change expense ratio
    - cap_rate: Change capitalization rate
    - exit_cap_rate: Change exit cap rate
    - discount_rate: Change discount rate
    - certification: Add green certification
    - retrofit: Apply retrofit improvements
    - climate: Apply climate risk scenario
    """
    result = scenario_engine.build_scenario(request)
    return result


@router.get("/list", response_model=ScenarioListResponse)
async def list_all_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all saved scenarios."""
    scenarios = list_scenarios()
    
    # Pagination
    total = len(scenarios)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = scenarios[start:end]
    
    items = [
        ScenarioResponse(
            id=UUID(s["id"]),
            scenario_name=s["scenario_name"],
            description=s.get("description"),
            base_property_id=UUID(s["base_property_id"]) if s.get("base_property_id") else None,
            modifications=s.get("modifications", []),
            base_value=Decimal(str(s.get("base_value", 0))),
            adjusted_value=Decimal(str(s.get("adjusted_value", 0))),
            value_change_pct=Decimal(str(s.get("value_change_pct", 0))),
            created_at=datetime.fromisoformat(s["created_at"]) if s.get("created_at") else datetime.now(timezone.utc),
        )
        for s in paginated
    ]
    
    return ScenarioListResponse(items=items, total=total)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario_by_id(scenario_id: str):
    """Get a specific scenario by ID."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return ScenarioResponse(
        id=UUID(scenario["id"]),
        scenario_name=scenario["scenario_name"],
        description=scenario.get("description"),
        base_property_id=UUID(scenario["base_property_id"]) if scenario.get("base_property_id") else None,
        modifications=scenario.get("modifications", []),
        base_value=Decimal(str(scenario.get("base_value", 0))),
        adjusted_value=Decimal(str(scenario.get("adjusted_value", 0))),
        value_change_pct=Decimal(str(scenario.get("value_change_pct", 0))),
        created_at=datetime.fromisoformat(scenario["created_at"]) if scenario.get("created_at") else datetime.now(timezone.utc),
    )


@router.post("/compare", response_model=ScenarioComparisonResult)
async def compare_scenarios(request: ScenarioComparisonRequest):
    """
    Compare multiple scenarios against base property.
    
    Returns comparison table with key metrics and identifies
    best/worst scenarios with key differentiators.
    """
    result = scenario_engine.compare_scenarios(
        str(request.base_property_id),
        [str(sid) for sid in request.scenario_ids],
        request.metrics,
    )
    return result


@router.post("/batch-create", response_model=BatchScenarioResult)
async def batch_create_scenarios(request: BatchScenarioRequest):
    """
    Create multiple scenarios at once using templates.
    """
    results = []
    
    for template in request.scenario_templates:
        from schemas.scenario_analysis import ScenarioModification, ModificationType
        
        modifications = []
        for mod in template.get("modifications", []):
            modifications.append(ScenarioModification(
                type=ModificationType(mod.get("type", "cap_rate")),
                parameter=mod.get("parameter", "cap_rate"),
                new_value=mod.get("new_value", 0),
                description=mod.get("description"),
            ))
        
        build_request = ScenarioBuildRequest(
            base_property_id=request.base_property_id,
            scenario_name=template.get("name", "Unnamed Scenario"),
            description=template.get("description"),
            modifications=modifications,
        )
        
        result = scenario_engine.build_scenario(build_request)
        results.append(result)
    
    return BatchScenarioResult(
        scenarios=results,
        total_created=len(results),
    )


# ============ Templates ============

@router.get("/templates/list", response_model=TemplateListResponse)
async def get_templates():
    """
    Get predefined scenario templates.
    
    Available categories:
    - optimistic: Favorable market conditions
    - pessimistic: Unfavorable conditions
    - stress_test: Economic stress scenarios
    - green_upgrade: Sustainability improvements
    """
    templates = get_scenario_templates()
    return TemplateListResponse(
        templates=templates,
        total=len(templates),
    )


@router.post("/templates/apply")
async def apply_template(
    base_property_id: UUID,
    template_name: str,
):
    """Apply a predefined template to create a scenario."""
    templates = get_scenario_templates()
    template = next((t for t in templates if t.name == template_name), None)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    request = ScenarioBuildRequest(
        base_property_id=base_property_id,
        scenario_name=f"{template.name} - {datetime.now().strftime('%Y%m%d')}",
        description=template.description,
        modifications=template.modifications,
    )
    
    return scenario_engine.build_scenario(request)


# ============ Sensitivity Analysis ============

sensitivity_router = APIRouter(prefix="/api/v1/sensitivity", tags=["Sensitivity Analysis"])


@sensitivity_router.post("/analyze", response_model=SensitivityAnalyzeResult)
async def analyze_sensitivity(request: SensitivityAnalyzeRequest):
    """
    Perform comprehensive sensitivity analysis.
    
    Analyzes how changes in key variables affect property valuation.
    Returns:
    - Sensitivity data for each variable
    - Tornado chart data (sorted by impact)
    - Spider chart data for scenario comparison
    """
    variables = [
        SensitivityVariable(
            name=v.name,
            base_value=v.base_value,
            range=v.range,
            steps=v.steps,
        )
        for v in request.variables
    ]
    
    result = scenario_engine.analyze_sensitivity(
        str(request.property_id),
        request.base_valuation,
        variables,
    )
    return result


@sensitivity_router.post("/tornado")
async def generate_tornado_chart(request: TornadoRequest):
    """
    Generate tornado chart data for visualization.
    
    Shows the relative impact of each variable on valuation,
    sorted from highest to lowest impact (swing).
    """
    variables = []
    for v in request.variables:
        variables.append(SensitivityVariable(
            name=v["name"],
            base_value=v["base"],
            range=VariableRange(min=v["low"], max=v["high"]),
            steps=10,
        ))
    
    result = scenario_engine.analyze_sensitivity(
        str(request.property_id),
        request.base_valuation,
        variables,
    )
    
    return {
        "tornado_data": result.tornado_data,
        "base_valuation": result.base_valuation,
    }


@sensitivity_router.post("/spider")
async def generate_spider_chart(request: SpiderRequest):
    """
    Generate spider/radar chart data for visualization.
    
    Compares base case, optimistic, and pessimistic scenarios
    across multiple variables.
    """
    # Build variables with variation range
    variables = []
    properties = get_sample_properties()
    prop = list(properties.values())[0]  # Use first property for base values
    
    var_defaults = {
        "cap_rate": (0.055, 0.04, 0.07),
        "rent_growth": (0.025, 0.01, 0.04),
        "vacancy_rate": (0.05, 0.02, 0.10),
        "expense_ratio": (0.35, 0.28, 0.42),
        "exit_cap_rate": (0.06, 0.045, 0.075),
        "discount_rate": (0.08, 0.06, 0.10),
    }
    
    for var_name in request.variables:
        defaults = var_defaults.get(var_name.lower(), (0.05, 0.03, 0.08))
        base, low, high = defaults
        
        variables.append(SensitivityVariable(
            name=var_name,
            base_value=base,
            range=VariableRange(min=low, max=high),
            steps=10,
        ))
    
    result = scenario_engine.analyze_sensitivity(
        str(request.property_id),
        request.base_valuation,
        variables,
    )
    
    return {
        "spider_chart_data": result.spider_chart_data,
        "base_valuation": result.base_valuation,
    }


@sensitivity_router.get("/presets")
async def get_sensitivity_presets():
    """Get preset sensitivity analysis configurations."""
    return {
        "presets": [
            {
                "name": "Standard Analysis",
                "description": "Core valuation variables",
                "variables": [
                    {"name": "cap_rate", "base": 0.055, "low": 0.04, "high": 0.07},
                    {"name": "rent_growth", "base": 0.025, "low": 0.01, "high": 0.04},
                    {"name": "vacancy_rate", "base": 0.05, "low": 0.02, "high": 0.10},
                    {"name": "expense_ratio", "base": 0.35, "low": 0.28, "high": 0.42},
                ]
            },
            {
                "name": "DCF Focus",
                "description": "Variables affecting DCF valuation",
                "variables": [
                    {"name": "discount_rate", "base": 0.08, "low": 0.06, "high": 0.10},
                    {"name": "exit_cap_rate", "base": 0.06, "low": 0.045, "high": 0.075},
                    {"name": "rent_growth", "base": 0.025, "low": 0.01, "high": 0.04},
                ]
            },
            {
                "name": "Operating Performance",
                "description": "Property operations variables",
                "variables": [
                    {"name": "vacancy_rate", "base": 0.05, "low": 0.02, "high": 0.12},
                    {"name": "expense_ratio", "base": 0.35, "low": 0.25, "high": 0.45},
                    {"name": "rent_psf", "base": 65, "low": 55, "high": 80},
                ]
            }
        ]
    }


# ============ What-If Analysis ============

whatif_router = APIRouter(prefix="/api/v1/what-if", tags=["What-If Analysis"])


@whatif_router.post("/analyze", response_model=WhatIfResult)
async def whatif_analyze(request: WhatIfRequest):
    """
    Perform what-if analysis with optional cascading effects.
    
    Cascading effects (when enabled):
    - Higher vacancy → increased collection loss
    - Higher expenses → may reduce rent competitiveness
    - Large rent increases → may increase vacancy
    
    Change types:
    - absolute: Add/subtract fixed amount
    - percentage: Multiply by (1 + value)
    """
    result = scenario_engine.what_if_analysis(request)
    return result


@whatif_router.get("/parameters")
async def get_whatif_parameters():
    """Get available parameters for what-if analysis."""
    return {
        "parameters": [
            {"name": "cap_rate", "label": "Capitalization Rate", "unit": "%", "typical_range": [4.0, 8.0]},
            {"name": "vacancy_rate", "label": "Vacancy Rate", "unit": "%", "typical_range": [2.0, 15.0]},
            {"name": "expense_ratio", "label": "Expense Ratio", "unit": "%", "typical_range": [20.0, 45.0]},
            {"name": "rent_growth", "label": "Rent Growth Rate", "unit": "%", "typical_range": [0.0, 5.0]},
            {"name": "discount_rate", "label": "Discount Rate", "unit": "%", "typical_range": [6.0, 12.0]},
            {"name": "exit_cap_rate", "label": "Exit Cap Rate", "unit": "%", "typical_range": [4.5, 8.0]},
            {"name": "rent_psf", "label": "Rent per SF", "unit": "$/SF", "typical_range": [30, 100]},
            {"name": "noi", "label": "Net Operating Income", "unit": "$", "typical_range": [1000000, 50000000]},
        ],
        "change_types": [
            {"value": "absolute", "label": "Absolute Change", "description": "Add/subtract a fixed amount"},
            {"value": "percentage", "label": "Percentage Change", "description": "Change by percentage (e.g., 0.1 = +10%)"},
        ]
    }


# ============ Properties (for dropdown) ============

@router.get("/properties")
async def get_available_properties():
    """Get list of properties available for scenario analysis."""
    properties = get_sample_properties()
    return {
        "properties": [
            {
                "id": p["id"],
                "name": p["name"],
                "property_type": p["property_type"],
                "current_value": float(p["current_value"]),
                "noi": float(p["noi"]),
                "cap_rate": float(p["cap_rate"]),
            }
            for p in properties.values()
        ]
    }


# Export routers for registration
__all__ = ["router", "sensitivity_router", "whatif_router"]
