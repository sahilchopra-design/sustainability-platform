"""Analysis routes with async job processing"""
import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from api.v1.deps import get_db, PaginationParams
from api.v1.repositories import PortfolioRepository, AnalysisRepository
from api.v1.schemas import (
    AnalysisRequest, AnalysisJobResponse, AnalysisResultsResponse,
    CompareRequest, CompareResponse, ComparisonMetric, ScenarioResultResponse,
    MessageResponse
)
from services.calculation_engine import ClimateRiskCalculationEngine
from services.engine_integration import assets_to_inputs
from db.models_sql import Asset
from db.postgres import SessionLocal

router = APIRouter(prefix="/analysis", tags=["analysis"])


def run_analysis_job(run_id: str, portfolio_id: str):
    """
    Background task to run analysis.
    
    This runs in a separate thread/process and updates the analysis run status.
    """
    db = SessionLocal()
    try:
        # Get repositories
        portfolio_repo = PortfolioRepository(db)
        analysis_repo = AnalysisRepository(db)
        
        # Get analysis run
        analysis_run = analysis_repo.get_analysis_run(run_id)
        if not analysis_run:
            return
        
        # Update status to running
        analysis_repo.update_analysis_status(run_id, "running")
        
        # Get portfolio assets
        portfolio = portfolio_repo.get_by_id(portfolio_id)
        if not portfolio or not portfolio.assets:
            analysis_repo.update_analysis_status(
                run_id,
                "failed",
                error_message="Portfolio has no assets"
            )
            return
        
        # Convert assets to engine input
        mongo_compatible_assets = []
        for asset in portfolio.assets:
            # Create a simple object that mimics the MongoDB Asset structure
            class SimpleAsset:
                def __init__(self, asset_sql):
                    self.id = asset_sql.id
                    self.exposure = asset_sql.exposure
                    self.base_pd = asset_sql.base_pd
                    self.base_lgd = asset_sql.base_lgd
                    self.asset_type = type('obj', (object,), {'value': asset_sql.asset_type.value})
                    self.company = type('obj', (object,), {
                        'name': asset_sql.company_name,
                        'sector': type('obj', (object,), {'value': asset_sql.company_sector.value}),
                        'subsector': asset_sql.company_subsector
                    })
            
            mongo_compatible_assets.append(SimpleAsset(asset))
        
        asset_inputs = assets_to_inputs(mongo_compatible_assets)
        
        # Run calculation engine
        engine = ClimateRiskCalculationEngine(
            n_simulations=10000,
            correlation=0.3,
            var_method='monte_carlo',
            base_return=0.05,
            random_seed=42
        )
        
        engine_results = engine.calculate_multiple_scenarios(
            assets=asset_inputs,
            scenarios=analysis_run.scenarios,
            horizons=analysis_run.horizons,
            include_sector_breakdown=False
        )
        
        # Convert results to database format
        results_data = []
        for result in engine_results:
            results_data.append({
                "scenario": result.scenario,
                "horizon": result.horizon,
                "expected_loss": result.expected_loss,
                "expected_loss_pct": result.expected_loss_pct,
                "risk_adjusted_return": result.risk_adjusted_return,
                "avg_pd_change_pct": result.avg_pd_change_pct,
                "rating_migrations": result.rating_migrations,
                "var_95": result.var_95,
                "concentration_hhi": result.sector_hhi,
                "total_exposure": result.total_exposure
            })
        
        # Save results
        analysis_repo.add_results(run_id, results_data)
        
        # Update status to completed
        analysis_repo.update_analysis_status(run_id, "completed")
        
    except Exception as e:
        # Handle errors
        analysis_repo = AnalysisRepository(db)
        analysis_repo.update_analysis_status(
            run_id,
            "failed",
            error_message=str(e)
        )
    finally:
        db.close()


@router.post("/run", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED)
def run_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run scenario analysis on a portfolio (async).
    
    This endpoint immediately returns a job ID and processes the analysis in the background.
    Use GET /analysis/jobs/{job_id} to check status.
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(request.portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {request.portfolio_id} not found"
        )
    
    # Create analysis run
    analysis_repo = AnalysisRepository(db)
    analysis_run = analysis_repo.create_analysis_run(
        portfolio_id=request.portfolio_id,
        portfolio_name=portfolio.name,
        scenarios=request.scenarios,
        horizons=request.horizons
    )
    
    # Add background task
    background_tasks.add_task(run_analysis_job, analysis_run.id, request.portfolio_id)
    
    return AnalysisJobResponse(
        job_id=analysis_run.id,
        portfolio_id=analysis_run.portfolio_id,
        portfolio_name=analysis_run.portfolio_name,
        scenarios=analysis_run.scenarios,
        horizons=analysis_run.horizons,
        status=analysis_run.status,
        created_at=analysis_run.created_at,
        completed_at=analysis_run.completed_at,
        error_message=analysis_run.error_message
    )


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get status of an analysis job.
    
    Returns current status: pending, running, completed, or failed.
    """
    repo = AnalysisRepository(db)
    analysis_run = repo.get_analysis_run(job_id)
    
    if not analysis_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found"
        )
    
    return AnalysisJobResponse(
        job_id=analysis_run.id,
        portfolio_id=analysis_run.portfolio_id,
        portfolio_name=analysis_run.portfolio_name,
        scenarios=analysis_run.scenarios,
        horizons=analysis_run.horizons,
        status=analysis_run.status,
        created_at=analysis_run.created_at,
        completed_at=analysis_run.completed_at,
        error_message=analysis_run.error_message
    )


@router.get("/jobs/{job_id}/results", response_model=AnalysisResultsResponse)
def get_job_results(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get results of a completed analysis job.
    
    Returns detailed results for all scenario-horizon combinations.
    """
    repo = AnalysisRepository(db)
    analysis_run = repo.get_analysis_run(job_id)
    
    if not analysis_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job {job_id} not found"
        )
    
    if analysis_run.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis job is {analysis_run.status}. Results only available for completed jobs."
        )
    
    results = repo.get_results(job_id)
    
    return AnalysisResultsResponse(
        job_id=analysis_run.id,
        portfolio_id=analysis_run.portfolio_id,
        portfolio_name=analysis_run.portfolio_name,
        status=analysis_run.status,
        results=[
            ScenarioResultResponse(
                scenario=r.scenario,
                horizon=r.horizon,
                expected_loss=r.expected_loss,
                expected_loss_pct=r.expected_loss_pct,
                risk_adjusted_return=r.risk_adjusted_return,
                avg_pd_change_pct=r.avg_pd_change_pct,
                rating_migrations=r.rating_migrations,
                var_95=r.var_95,
                concentration_hhi=r.concentration_hhi,
                total_exposure=r.total_exposure
            )
            for r in results
        ],
        created_at=analysis_run.created_at,
        completed_at=analysis_run.completed_at
    )


@router.get("/portfolios/{portfolio_id}/results", response_model=List[AnalysisJobResponse])
def get_portfolio_analysis_history(
    portfolio_id: str,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get historical analysis runs for a portfolio.
    
    Returns list of all analysis runs (completed, pending, or failed).
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Get analysis runs
    analysis_repo = AnalysisRepository(db)
    runs, total = analysis_repo.get_portfolio_runs(
        portfolio_id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return [
        AnalysisJobResponse(
            job_id=run.id,
            portfolio_id=run.portfolio_id,
            portfolio_name=run.portfolio_name,
            scenarios=run.scenarios,
            horizons=run.horizons,
            status=run.status,
            created_at=run.created_at,
            completed_at=run.completed_at,
            error_message=run.error_message
        )
        for run in runs
    ]


@router.post("/compare", response_model=CompareResponse)
def compare_scenarios(
    request: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple scenarios for a portfolio at a specific horizon.
    
    Returns comparison metrics across the selected scenarios.
    """
    # Note: This would need to find matching analysis runs with the specified scenarios
    # For now, return a placeholder structure
    
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(request.portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {request.portfolio_id} not found"
        )
    
    # This would query actual results and compare them
    # Placeholder implementation
    return CompareResponse(
        portfolio_id=request.portfolio_id,
        portfolio_name=portfolio.name,
        horizon=request.horizon,
        scenarios=request.scenario_ids,
        comparisons=[
            ComparisonMetric(
                metric_name="expected_loss",
                values={scenario: 0.0 for scenario in request.scenario_ids}
            )
        ]
    )


@router.get("/portfolios/{portfolio_id}/heatmap")
def get_portfolio_heatmap(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """
    Get heatmap data for portfolio risk across scenarios and horizons.
    
    Returns grid data suitable for heatmap visualization.
    """
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Get all completed analysis runs for this portfolio
    analysis_repo = AnalysisRepository(db)
    runs, _ = analysis_repo.get_portfolio_runs(portfolio_id, skip=0, limit=100)
    
    # Find the most recent completed run
    completed_runs = [r for r in runs if r.status == "completed"]
    
    if not completed_runs:
        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name,
            "data": [],
            "message": "No completed analysis runs found"
        }
    
    latest_run = completed_runs[0]
    results = analysis_repo.get_results(latest_run.id)
    
    # Build heatmap data
    heatmap_data = []
    for result in results:
        heatmap_data.append({
            "scenario": result.scenario,
            "horizon": result.horizon,
            "expected_loss_pct": result.expected_loss_pct,
            "var_95": result.var_95,
            "avg_pd_change_pct": result.avg_pd_change_pct
        })
    
    return {
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio.name,
        "analysis_run_id": latest_run.id,
        "created_at": latest_run.created_at,
        "data": heatmap_data
    }
