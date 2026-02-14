"""
Integration layer between API/models and the calculation engine.

This module provides mappers to convert between:
- Portfolio.assets → AssetInput (for calculation engine)
- ScenarioHorizonResult → ScenarioResult (for API response)
"""
from typing import List
from models import Asset, ScenarioResult, RatingMigration
from services.calculation_engine import AssetInput, ScenarioHorizonResult


def asset_to_input(asset: Asset) -> AssetInput:
    """
    Convert a Portfolio Asset to AssetInput for the calculation engine.
    
    Args:
        asset: Asset from Portfolio model
        
    Returns:
        AssetInput with mapped fields and reasonable defaults for optional climate fields
    """
    # Get sector
    sector = asset.company.sector.value
    subsector = asset.company.subsector or ''
    
    # Assign emissions intensity based on subsector heuristics
    if 'Coal' in subsector:
        emissions_intensity = 1.8
        emissions_trend = 'Deteriorating'
        transition_plan_score = 1
    elif 'Renewables' in subsector or 'Solar' in subsector or 'Wind' in subsector:
        emissions_intensity = 0.2
        emissions_trend = 'Improving'
        transition_plan_score = 5
    elif 'EV' in subsector or 'Electric' in subsector:
        emissions_intensity = 0.3
        emissions_trend = 'Improving'
        transition_plan_score = 5
    elif 'Oil' in subsector or 'Gas' in subsector or 'Petro' in asset.company.name:
        emissions_intensity = 1.2
        emissions_trend = 'Stable'
        transition_plan_score = 2
    elif 'ICE' in subsector:
        emissions_intensity = 0.9
        emissions_trend = 'Deteriorating'
        transition_plan_score = 2
    elif 'Green' in asset.company.name or 'Renewable' in asset.company.name:
        emissions_intensity = 0.4
        emissions_trend = 'Improving'
        transition_plan_score = 4
    else:
        emissions_intensity = 0.8
        emissions_trend = 'Stable'
        transition_plan_score = 3
    
    # Assign physical risk score based on sector
    if sector in ['Real Estate', 'Airlines']:
        physical_risk_score = 4
    elif sector in ['Power Generation', 'Metals & Mining']:
        physical_risk_score = 3
    else:
        physical_risk_score = 2
    
    # Assign collateral type based on asset type
    asset_type = asset.asset_type.value
    if asset_type == 'Equity':
        collateral_type = 'Unsecured'
    elif asset_type == 'Bond':
        collateral_type = 'Financial'
    elif asset_type == 'Loan':
        collateral_type = 'Equipment'
    else:
        collateral_type = 'Unsecured'
    
    return AssetInput(
        id=asset.id,
        exposure=asset.exposure,
        baseline_pd=asset.base_pd,
        baseline_lgd=asset.base_lgd,
        sector=sector,
        country='World',  # Default; could be enhanced with actual country data
        emissions_intensity=emissions_intensity,
        emissions_trend=emissions_trend,
        transition_plan_score=transition_plan_score,
        physical_risk_score=physical_risk_score,
        collateral_type=collateral_type
    )


def assets_to_inputs(assets: List[Asset]) -> List[AssetInput]:
    """
    Convert a list of Portfolio Assets to AssetInput list.
    
    Args:
        assets: List of Asset objects
        
    Returns:
        List of AssetInput objects
    """
    return [asset_to_input(asset) for asset in assets]


def engine_result_to_model(result: ScenarioHorizonResult) -> ScenarioResult:
    """
    Convert ScenarioHorizonResult to ScenarioResult model for API response.
    
    This maintains backwards compatibility with the existing API response format
    that the frontend expects.
    
    Args:
        result: ScenarioHorizonResult from calculation engine
        
    Returns:
        ScenarioResult model instance
    """
    return ScenarioResult(
        scenario=result.scenario,
        horizon=result.horizon,
        expected_loss=result.expected_loss,
        expected_loss_pct=result.expected_loss_pct,
        risk_adjusted_return=result.risk_adjusted_return,
        avg_pd_change_pct=result.avg_pd_change_pct,
        rating_migrations=RatingMigration(
            upgrades=result.rating_migrations['upgrades'],
            downgrades=result.rating_migrations['downgrades'],
            stable=result.rating_migrations['stable']
        ),
        var_95=result.var_95,
        concentration_hhi=result.sector_hhi,  # Map sector_hhi to concentration_hhi for backwards compatibility
        total_exposure=result.total_exposure
    )


def engine_results_to_models(results: List[ScenarioHorizonResult]) -> List[ScenarioResult]:
    """
    Convert list of ScenarioHorizonResult to list of ScenarioResult models.
    
    Args:
        results: List of ScenarioHorizonResult objects
        
    Returns:
        List of ScenarioResult model instances
    """
    return [engine_result_to_model(result) for result in results]
