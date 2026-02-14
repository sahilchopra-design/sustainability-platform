"""Export routes for generating reports"""
import io
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.v1.deps import get_db
from api.v1.repositories import PortfolioRepository, AnalysisRepository

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/portfolios/{portfolio_id}/report")
def download_portfolio_report(
    portfolio_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Download portfolio analysis report.
    
    Formats: json, csv (future: pdf, xlsx)
    
    Returns a downloadable file with portfolio details and analysis results.
    """
    # Get portfolio
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Get portfolio metrics
    metrics = portfolio_repo.get_portfolio_metrics(portfolio_id)
    holdings = portfolio_repo.get_holdings(portfolio_id)
    
    # Get latest analysis runs
    analysis_repo = AnalysisRepository(db)
    runs, _ = analysis_repo.get_portfolio_runs(portfolio_id, skip=0, limit=10)
    
    # Build report data
    report_data = {
        "portfolio": {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "created_at": portfolio.created_at.isoformat(),
            "updated_at": portfolio.updated_at.isoformat()
        },
        "metrics": metrics,
        "holdings": [
            {
                "id": h.id,
                "company_name": h.company_name,
                "company_sector": h.company_sector.value,
                "asset_type": h.asset_type.value,
                "exposure": h.exposure,
                "market_value": h.market_value,
                "base_pd": h.base_pd,
                "base_lgd": h.base_lgd,
                "rating": h.rating
            }
            for h in holdings
        ],
        "analysis_runs": [
            {
                "id": run.id,
                "scenarios": run.scenarios,
                "horizons": run.horizons,
                "status": run.status,
                "created_at": run.created_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None
            }
            for run in runs
        ],
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Add results from latest completed run
    completed_runs = [r for r in runs if r.status == "completed"]
    if completed_runs:
        latest_run = completed_runs[0]
        results = analysis_repo.get_results(latest_run.id)
        report_data["latest_analysis_results"] = [
            {
                "scenario": r.scenario,
                "horizon": r.horizon,
                "expected_loss": r.expected_loss,
                "expected_loss_pct": r.expected_loss_pct,
                "var_95": r.var_95,
                "avg_pd_change_pct": r.avg_pd_change_pct,
                "concentration_hhi": r.concentration_hhi
            }
            for r in results
        ]
    
    # Generate file based on format
    if format == "json":
        # JSON format
        json_str = json.dumps(report_data, indent=2)
        file_content = io.BytesIO(json_str.encode('utf-8'))
        
        return StreamingResponse(
            file_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_report.json"
            }
        )
    
    elif format == "csv":
        # CSV format (simplified)
        csv_lines = []
        csv_lines.append("Portfolio Report")
        csv_lines.append(f"Portfolio Name,{portfolio.name}")
        csv_lines.append(f"Total Exposure,{metrics['total_exposure']}")
        csv_lines.append(f"Number of Holdings,{metrics['num_holdings']}")
        csv_lines.append("")
        csv_lines.append("Holdings")
        csv_lines.append("Company Name,Sector,Asset Type,Exposure,PD,LGD,Rating")
        
        for h in holdings:
            csv_lines.append(
                f"{h.company_name},{h.company_sector.value},{h.asset_type.value},"
                f"{h.exposure},{h.base_pd},{h.base_lgd},{h.rating}"
            )
        
        csv_content = "\n".join(csv_lines)
        file_content = io.BytesIO(csv_content.encode('utf-8'))
        
        return StreamingResponse(
            file_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_report.csv"
            }
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}. Supported formats: json, csv"
        )
