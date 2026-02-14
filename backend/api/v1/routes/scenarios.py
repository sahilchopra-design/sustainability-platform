"""Scenario routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.v1.deps import get_db
from api.v1.repositories import ScenarioRepository
from api.v1.schemas import ScenarioSummary, ScenarioDetail

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


# Predefined NGFS scenarios
NGFS_SCENARIOS = [
    {
        "name": "Orderly",
        "description": "Net zero by 2050 with immediate policy action",
        "type": "Orderly"
    },
    {
        "name": "Disorderly",
        "description": "Delayed transition with sudden policy shifts",
        "type": "Disorderly"
    },
    {
        "name": "Hot house world",
        "description": "Current policies continue, warming exceeds 2°C",
        "type": "Hot house world"
    }
]


@router.get("", response_model=List[ScenarioSummary])
def list_scenarios(
    db: Session = Depends(get_db)
):
    """
    List all available NGFS scenarios.
    
    Returns predefined NGFS climate scenarios that can be used for analysis.
    """
    return [
        ScenarioSummary(
            name=scenario["name"],
            description=scenario["description"],
            type=scenario["type"]
        )
        for scenario in NGFS_SCENARIOS
    ]


@router.get("/{scenario_name}", response_model=ScenarioDetail)
def get_scenario(
    scenario_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific scenario.
    
    Returns available variables, regions, and time horizons for the scenario.
    """
    repo = ScenarioRepository(db)
    
    # Check if scenario exists
    available_scenarios = repo.get_all_scenarios()
    if scenario_name not in available_scenarios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_name}' not found or no data available"
        )
    
    # Get summary to find available data
    summary = repo.get_scenario_summary()
    
    return ScenarioDetail(
        scenario=scenario_name,
        variables=summary["variables"],
        regions=summary["regions"],
        years=summary["years"]
    )
