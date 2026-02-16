"""
Universal Export API Routes
Provides PDF and Excel export for all modules in the platform
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
import json

from services.export_service import export_service
from services.portfolio_analytics_engine import (
    PortfolioAggregationEngine, get_portfolio, get_holdings
)
from services.sustainability_calculator import SustainabilityEngine
from schemas.portfolio_analytics import ReportType

router = APIRouter(prefix="/api/v1/exports", tags=["Exports"])

# Initialize engines
portfolio_engine = PortfolioAggregationEngine()
sustainability_engine = SustainabilityEngine()


def _serialize_data(data: Any) -> Any:
    """Recursively serialize data for export, handling Decimal and UUID."""
    if isinstance(data, dict):
        return {k: _serialize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_data(v) for v in data]
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, UUID):
        return str(data)
    elif hasattr(data, 'model_dump'):
        return _serialize_data(data.model_dump())
    elif hasattr(data, '__dict__'):
        return _serialize_data(data.__dict__)
    return data


# ==================== Portfolio Analytics Exports ====================

@router.get("/portfolio-analytics/{portfolio_id}")
async def export_portfolio_analytics(
    portfolio_id: str,
    format: str = Query("pdf", enum=["pdf", "excel"]),
    report_type: str = Query("executive", enum=["valuation", "climate_risk", "sustainability", "tcfd", "investor", "executive"]),
    include_property_details: bool = Query(True),
):
    """
    Export portfolio analytics report.
    
    Generates comprehensive PDF or Excel report including:
    - Executive summary with KPIs
    - Portfolio overview
    - Property details (optional)
    - Risk analysis
    - Sustainability metrics
    """
    try:
        # Generate report
        report = portfolio_engine.reports.generate_report(
            portfolio_id=portfolio_id,
            report_type=ReportType(report_type),
            include_property_details=include_property_details,
        )
        
        # Serialize for export
        export_data = _serialize_data(report)
        
        # Generate file
        buffer = export_service.export('portfolio_analytics', export_data, format)
        
        # Determine content type and filename
        if format == 'excel':
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"portfolio_analytics_{portfolio_id[:8]}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        else:
            content_type = "application/pdf"
            filename = f"portfolio_analytics_{portfolio_id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/portfolio-analytics/{portfolio_id}/dashboard")
async def export_portfolio_dashboard(
    portfolio_id: str,
    format: str = Query("pdf", enum=["pdf", "excel"]),
):
    """Export portfolio dashboard data."""
    try:
        dashboard = portfolio_engine.get_dashboard(portfolio_id)
        export_data = _serialize_data(dashboard)
        
        buffer = export_service.export('portfolio_analytics', export_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=portfolio_dashboard_{portfolio_id[:8]}.{ext}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Sustainability Exports ====================

@router.post("/sustainability/assessment")
async def export_sustainability_assessment(
    assessment_data: Dict[str, Any],
    format: str = Query("pdf", enum=["pdf", "excel"]),
    assessment_type: str = Query("gresb", enum=["gresb", "leed", "breeam", "value_impact"]),
):
    """
    Export sustainability assessment results.
    
    Accepts the assessment result data and generates a PDF or Excel report.
    """
    try:
        # Add assessment type to data
        export_data = _serialize_data(assessment_data)
        export_data['assessment_type'] = assessment_type
        
        buffer = export_service.export('sustainability', export_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={assessment_type}_assessment.{ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/sustainability/certifications")
async def export_sustainability_certifications(
    format: str = Query("excel", enum=["pdf", "excel"]),
):
    """Export all certifications data as Excel or PDF."""
    try:
        # Get sample certifications (would come from DB in production)
        from api.v1.routes.sustainability import get_sample_certifications
        certifications = get_sample_certifications()
        
        # Format for export
        export_data = {
            'executive_summary': {
                'portfolio_name': 'Sustainability Certifications',
                'total_value': sum(float(c.get('current_value', 0) or 0) for c in certifications),
                'property_count': len(certifications),
                'avg_risk_score': 0,
                'stranded_assets': 0,
            },
            'property_details': [
                {
                    'name': c.get('property_name', 'N/A'),
                    'type': c.get('certification_type', 'N/A'),
                    'location': c.get('region', 'N/A'),
                    'value': float(c.get('current_value', 0) or 0),
                    'risk_score': c.get('score', 'N/A'),
                    'certifications': [c.get('certification_level', '')],
                }
                for c in certifications
            ]
        }
        
        buffer = export_service.export('portfolio_analytics', export_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=certifications_export.{ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ==================== Stranded Assets Exports ====================

@router.post("/stranded-assets/analysis")
async def export_stranded_asset_analysis(
    analysis_data: Dict[str, Any],
    format: str = Query("pdf", enum=["pdf", "excel"]),
):
    """Export stranded asset analysis results."""
    try:
        export_data = _serialize_data(analysis_data)
        buffer = export_service.export('stranded_assets', export_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=stranded_asset_analysis.{ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ==================== Scenario Analysis Exports ====================

@router.post("/scenario-analysis/comparison")
async def export_scenario_comparison(
    comparison_data: Dict[str, Any],
    format: str = Query("pdf", enum=["pdf", "excel"]),
):
    """Export scenario comparison results."""
    try:
        export_data = _serialize_data(comparison_data)
        buffer = export_service.export('scenario_analysis', export_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=scenario_comparison.{ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/scenario-analysis/{portfolio_id}/scenarios")
async def export_portfolio_scenarios(
    portfolio_id: str,
    scenario_ids: str = Query(..., description="Comma-separated scenario IDs"),
    format: str = Query("pdf", enum=["pdf", "excel"]),
):
    """Export scenario comparison for a portfolio."""
    try:
        ids = [s.strip() for s in scenario_ids.split(',') if s.strip()]
        
        # Run comparison
        comparison = portfolio_engine.compare_scenarios(portfolio_id, ids)
        export_data = _serialize_data(comparison)
        
        buffer = export_service.export('scenario_analysis', export_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=scenario_comparison_{portfolio_id[:8]}.{ext}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ==================== Nature Risk Exports ====================

@router.post("/nature-risk/assessment")
async def export_nature_risk_assessment(
    assessment_data: Dict[str, Any],
    format: str = Query("pdf", enum=["pdf", "excel"]),
):
    """Export nature risk assessment (LEAP, water risk, biodiversity)."""
    try:
        export_data = _serialize_data(assessment_data)
        # Use sustainability export format (similar structure)
        export_data['assessment_type'] = 'nature_risk'
        
        buffer = export_service.export('sustainability', export_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=nature_risk_assessment.{ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ==================== Real Estate Valuation Exports ====================

@router.post("/valuation/analysis")
async def export_valuation_analysis(
    valuation_data: Dict[str, Any],
    format: str = Query("pdf", enum=["pdf", "excel"]),
    valuation_type: str = Query("dcf", enum=["direct_cap", "dcf", "cost", "sales_comparison"]),
):
    """Export real estate valuation analysis."""
    try:
        export_data = _serialize_data(valuation_data)
        export_data['valuation_type'] = valuation_type
        
        # Format for portfolio analytics template
        formatted_data = {
            'executive_summary': {
                'portfolio_name': valuation_data.get('property_name', 'Valuation Analysis'),
                'total_value': valuation_data.get('indicated_value') or valuation_data.get('value', 0),
                'property_count': 1,
                'avg_risk_score': 0,
                'stranded_assets': 0,
                'key_findings': [
                    f"Valuation Method: {valuation_type.replace('_', ' ').title()}",
                    f"Indicated Value: ${valuation_data.get('indicated_value', 0):,.0f}" if valuation_data.get('indicated_value') else "",
                ]
            },
            'portfolio_overview': {
                'portfolio_type': 'single_asset',
                'investment_strategy': valuation_type,
                'aum': valuation_data.get('indicated_value') or valuation_data.get('value', 0),
                'currency': 'USD',
                'total_income': valuation_data.get('noi') or valuation_data.get('annual_income', 0),
                'yield': valuation_data.get('cap_rate', 0) * 100 if valuation_data.get('cap_rate') else 0,
            }
        }
        
        buffer = export_service.export('portfolio_analytics', formatted_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={valuation_type}_valuation.{ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ==================== Carbon Credits Exports ====================

@router.post("/carbon/calculation")
async def export_carbon_calculation(
    calculation_data: Dict[str, Any],
    format: str = Query("pdf", enum=["pdf", "excel"]),
):
    """Export carbon credit calculation results."""
    try:
        export_data = _serialize_data(calculation_data)
        
        # Format for sustainability template
        formatted_data = {
            'assessment_type': 'carbon_credits',
            'total_score': calculation_data.get('total_credits', 0),
            'estimated_rent_premium_percent': 0,
            'estimated_value_premium_percent': 0,
            'estimated_value_impact': calculation_data.get('total_value', 0),
        }
        
        buffer = export_service.export('sustainability', formatted_data, format)
        
        ext = 'xlsx' if format == 'excel' else 'pdf'
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == 'excel' else "application/pdf"
        
        return StreamingResponse(
            buffer,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=carbon_calculation.{ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ==================== Bulk Export ====================

@router.get("/bulk")
async def get_available_exports():
    """Get list of available export endpoints and their parameters."""
    return {
        "exports": [
            {
                "module": "portfolio_analytics",
                "endpoint": "/api/v1/exports/portfolio-analytics/{portfolio_id}",
                "methods": ["GET"],
                "formats": ["pdf", "excel"],
                "description": "Export portfolio analytics report with properties and risk metrics"
            },
            {
                "module": "sustainability",
                "endpoint": "/api/v1/exports/sustainability/assessment",
                "methods": ["POST"],
                "formats": ["pdf", "excel"],
                "description": "Export GRESB, LEED, BREEAM, or value impact assessment"
            },
            {
                "module": "stranded_assets",
                "endpoint": "/api/v1/exports/stranded-assets/analysis",
                "methods": ["POST"],
                "formats": ["pdf", "excel"],
                "description": "Export stranded asset risk analysis"
            },
            {
                "module": "scenario_analysis",
                "endpoint": "/api/v1/exports/scenario-analysis/comparison",
                "methods": ["POST"],
                "formats": ["pdf", "excel"],
                "description": "Export scenario comparison results"
            },
            {
                "module": "nature_risk",
                "endpoint": "/api/v1/exports/nature-risk/assessment",
                "methods": ["POST"],
                "formats": ["pdf", "excel"],
                "description": "Export nature risk assessment (LEAP, water, biodiversity)"
            },
            {
                "module": "valuation",
                "endpoint": "/api/v1/exports/valuation/analysis",
                "methods": ["POST"],
                "formats": ["pdf", "excel"],
                "description": "Export real estate valuation analysis"
            },
            {
                "module": "carbon",
                "endpoint": "/api/v1/exports/carbon/calculation",
                "methods": ["POST"],
                "formats": ["pdf", "excel"],
                "description": "Export carbon credit calculation"
            },
        ]
    }
