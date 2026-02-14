"""
API routes for Scenario Comparison, Gap Analysis, Consistency Checks, and Alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from db.base import get_db
from services.scenario_comparison_service import ScenarioComparisonService

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


# ---- Pydantic schemas ----

class ComparisonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    base_scenario_id: str
    compare_scenario_ids: List[str] = []
    variable_filter: List[str] = []
    region_filter: List[str] = []
    sector_filter: List[str] = []
    time_range: dict = {}
    is_public: bool = False
    created_by: str = "default_user"


class AdhocComparisonRequest(BaseModel):
    scenario_ids: List[str] = Field(..., min_length=2)
    variables: List[str] = []
    regions: List[str] = []
    time_range: dict = {}


class ComparisonResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    base_scenario_id: Optional[str] = None
    compare_scenario_ids: List[str] = []
    variable_filter: List[str] = []
    region_filter: List[str] = []
    sector_filter: List[str] = []
    time_range: dict = {}
    is_public: bool = False
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GapAnalysisResponse(BaseModel):
    id: str
    comparison_id: str
    gap_type: str
    variable: str
    region: str
    base_value: Optional[float] = None
    target_value: Optional[float] = None
    gap_value: Optional[float] = None
    gap_pct: Optional[float] = None
    gap_unit: Optional[str] = None
    year: Optional[int] = None
    required_action: Optional[str] = None
    confidence_level: Optional[float] = None

    class Config:
        from_attributes = True


class ConsistencyCheckResponse(BaseModel):
    id: str
    scenario_id: str
    check_type: str
    status: str
    score: Optional[float] = None
    issues: list = []
    details: dict = {}
    checked_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: str
    user_id: str
    alert_type: str
    ref_scenario_id: Optional[str] = None
    ref_source_id: Optional[str] = None
    title: str
    message: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Comparisons
# ============================================================================

@router.get("/comparisons", response_model=List[ComparisonResponse])
def list_comparisons(db: Session = Depends(get_db)):
    """List all saved comparisons."""
    svc = ScenarioComparisonService(db)
    return svc.list_comparisons()


@router.post("/comparisons", response_model=ComparisonResponse, status_code=201)
def create_comparison(body: ComparisonCreate, db: Session = Depends(get_db)):
    """Save a new scenario comparison."""
    svc = ScenarioComparisonService(db)
    return svc.create_comparison(body.model_dump())


@router.get("/comparisons/{comp_id}")
def get_comparison(comp_id: str, db: Session = Depends(get_db)):
    """Get a saved comparison metadata."""
    svc = ScenarioComparisonService(db)
    comp = svc.get_comparison(comp_id)
    if not comp:
        raise HTTPException(404, "Comparison not found")
    return ComparisonResponse.model_validate(comp)


@router.get("/comparisons/{comp_id}/data")
def get_comparison_data(comp_id: str, db: Session = Depends(get_db)):
    """Get the full comparison dataset with charts and statistics."""
    svc = ScenarioComparisonService(db)
    try:
        return svc.build_comparison_data(comp_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/comparisons/{comp_id}", status_code=204)
def delete_comparison(comp_id: str, db: Session = Depends(get_db)):
    """Delete a comparison and its gap analyses."""
    svc = ScenarioComparisonService(db)
    if not svc.delete_comparison(comp_id):
        raise HTTPException(404, "Comparison not found")


@router.post("/compare")
def adhoc_compare(body: AdhocComparisonRequest, db: Session = Depends(get_db)):
    """Run an ad-hoc comparison without saving."""
    svc = ScenarioComparisonService(db)
    return svc.build_adhoc_comparison(
        body.scenario_ids, body.variables, body.regions, body.time_range
    )


# ============================================================================
# Gap Analysis
# ============================================================================

@router.post("/comparisons/{comp_id}/gap-analysis")
def run_gap_analysis(comp_id: str, db: Session = Depends(get_db)):
    """Run gap analysis for a saved comparison."""
    svc = ScenarioComparisonService(db)
    try:
        return {"gaps": svc.run_gap_analysis(comp_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/comparisons/{comp_id}/gap-analysis", response_model=List[GapAnalysisResponse])
def get_gap_analysis(comp_id: str, db: Session = Depends(get_db)):
    """Get cached gap analysis results."""
    svc = ScenarioComparisonService(db)
    return svc.get_gap_analyses(comp_id)


# ============================================================================
# Consistency Checks
# ============================================================================

@router.post("/scenarios/{scenario_id}/consistency-check")
def run_consistency_check(scenario_id: str, db: Session = Depends(get_db)):
    """Run consistency checks on a scenario."""
    svc = ScenarioComparisonService(db)
    try:
        return {"checks": svc.run_consistency_check(scenario_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/scenarios/{scenario_id}/consistency-check", response_model=List[ConsistencyCheckResponse])
def get_consistency_checks(scenario_id: str, db: Session = Depends(get_db)):
    """Get cached consistency check results."""
    svc = ScenarioComparisonService(db)
    return svc.get_consistency_checks(scenario_id)


# ============================================================================
# Alerts
# ============================================================================

@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    user_id: str = "default_user",
    unread_only: bool = False,
    db: Session = Depends(get_db),
):
    """List alerts for a user."""
    svc = ScenarioComparisonService(db)
    return svc.list_alerts(user_id, unread_only)


@router.patch("/alerts/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(alert_id: str, db: Session = Depends(get_db)):
    """Mark an alert as read."""
    svc = ScenarioComparisonService(db)
    alert = svc.mark_alert_read(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return alert



class AlertCreate(BaseModel):
    alert_type: str
    title: str
    message: Optional[str] = None
    user_id: str = "default_user"
    ref_scenario_id: Optional[str] = None
    ref_source_id: Optional[str] = None


@router.post("/alerts", response_model=AlertResponse, status_code=201)
def create_alert(body: AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert."""
    svc = ScenarioComparisonService(db)
    return svc.create_alert(body.model_dump())



# ============================================================================
# Impact Calculator
# ============================================================================

class ImpactRequest(BaseModel):
    scenario_id: str
    portfolio_id: str
    horizons: List[int] = [2030, 2040, 2050]


@router.post("/impact")
async def calculate_impact(body: ImpactRequest, db: Session = Depends(get_db)):
    """Calculate scenario impact on a portfolio."""
    from models import Portfolio
    from services.impact_calculator import run_impact_calculation

    portfolio = await Portfolio.get(body.portfolio_id)
    if not portfolio:
        raise HTTPException(404, "Portfolio not found")
    if not portfolio.assets:
        raise HTTPException(400, "Portfolio has no assets")

    try:
        result = run_impact_calculation(db, body.scenario_id, portfolio.assets, body.horizons)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Calculation error: {e}")


# ============================================================================
# Custom Scenario Builder
# ============================================================================

class CustomScenarioRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    base_scenario_id: str
    overrides: List[dict] = []  # [{"variable": "...", "region": "World", "source_scenario_id": "..."}]


@router.post("/custom-scenarios", status_code=201)
def create_custom_scenario(body: CustomScenarioRequest, db: Session = Depends(get_db)):
    """Create a custom blended scenario."""
    from services.custom_scenario_builder import build_custom_scenario
    try:
        return build_custom_scenario(
            db, body.name, body.description, body.base_scenario_id, body.overrides
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============================================================================
# Portfolio Upload
# ============================================================================

class UploadParseRequest(BaseModel):
    content: str
    column_mapping: Optional[dict] = None


class PortfolioCreateFromUpload(BaseModel):
    name: str
    description: str = ""
    assets: List[dict]


@router.post("/portfolio-upload/parse")
def parse_portfolio_file(body: UploadParseRequest):
    """Parse CSV content and return mapped assets with validation."""
    from services.portfolio_upload import parse_portfolio_csv
    return parse_portfolio_csv(body.content, body.column_mapping)


@router.post("/portfolio-upload/create")
async def create_portfolio_from_upload(body: PortfolioCreateFromUpload):
    """Create a portfolio from parsed/validated assets."""
    from models import Portfolio, Asset, Company, AssetType, Sector

    SECTOR_ENUM = {s.value: s for s in Sector}
    TYPE_ENUM = {t.value: t for t in AssetType}

    assets = []
    for a in body.assets:
        company_data = a.get("company", {})
        sector = SECTOR_ENUM.get(company_data.get("sector", "Power Generation"), Sector.POWER_GENERATION)
        asset_type = TYPE_ENUM.get(a.get("asset_type", "Bond"), AssetType.BOND)
        assets.append(Asset(
            id=a.get("id", str(__import__("uuid").uuid4())),
            asset_type=asset_type,
            company=Company(name=company_data.get("name", "Unknown"), sector=sector,
                          subsector=company_data.get("subsector")),
            exposure=a.get("exposure", 0),
            market_value=a.get("market_value", a.get("exposure", 0)),
            base_pd=a.get("base_pd", 0.02),
            base_lgd=a.get("base_lgd", 0.45),
            rating=a.get("rating", "BBB"),
            maturity_years=a.get("maturity_years", 5),
        ))

    portfolio = Portfolio(name=body.name, description=body.description, assets=assets)
    await portfolio.insert()

    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "num_assets": len(assets),
        "total_exposure": sum(a.exposure for a in assets),
    }



# ============================================================================
# Report Generator
# ============================================================================

class ReportRequest(BaseModel):
    scenario_id: str
    portfolio_id: str
    format: str = "pdf"  # pdf, excel, csv
    horizons: List[int] = [2030, 2040, 2050]


@router.post("/reports/generate")
async def generate_report(body: ReportRequest, db: Session = Depends(get_db)):
    """Generate a downloadable impact report (PDF, Excel, or CSV)."""
    from models import Portfolio
    from services.impact_calculator import run_impact_calculation
    from services.report_generator import generate_pdf_report, generate_excel_report, generate_csv_report

    # Get portfolio
    portfolio = await Portfolio.get(body.portfolio_id)
    if not portfolio:
        raise HTTPException(404, "Portfolio not found")
    if not portfolio.assets:
        raise HTTPException(400, "Portfolio has no assets")

    portfolio_data = {
        "name": portfolio.name,
        "num_assets": len(portfolio.assets),
        "total_exposure": sum(a.exposure for a in portfolio.assets),
    }

    # Run impact calculation
    try:
        impact_data = run_impact_calculation(db, body.scenario_id, portfolio.assets, body.horizons)
    except ValueError as e:
        raise HTTPException(404, str(e))

    # Get scenario details
    from db.models.data_hub import DataHubScenario
    sc = db.get(DataHubScenario, body.scenario_id)
    scenario_data = {}
    if sc:
        scenario_data = {
            "name": sc.display_name or sc.name,
            "source_name": sc.source.name if sc.source else "",
            "category": sc.category,
            "temperature_target": sc.temperature_target,
            "carbon_neutral_year": sc.carbon_neutral_year,
            "model": sc.model,
            "description": sc.description,
        }

    # Generate report
    fmt = body.format.lower()
    if fmt == "pdf":
        filename = generate_pdf_report(impact_data, portfolio_data, scenario_data)
        content_type = "application/pdf"
    elif fmt in ("excel", "xlsx"):
        filename = generate_excel_report(impact_data, portfolio_data, scenario_data)
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif fmt == "csv":
        filename = generate_csv_report(impact_data, portfolio_data)
        content_type = "text/csv"
    else:
        raise HTTPException(400, f"Unsupported format: {fmt}. Use pdf, excel, or csv.")

    return {
        "filename": filename,
        "format": fmt,
        "download_url": f"/api/v1/analysis/reports/download/{filename}",
    }


@router.get("/reports/download/{filename}")
async def download_report(filename: str):
    """Download a generated report file."""
    from fastapi.responses import FileResponse
    import os

    filepath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "reports_output", filename
    )
    if not os.path.exists(filepath):
        raise HTTPException(404, "Report not found")

    media_type = "application/pdf"
    if filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".csv"):
        media_type = "text/csv"

    return FileResponse(filepath, filename=filename, media_type=media_type)
