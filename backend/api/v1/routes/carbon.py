"""
Carbon Credits API Routes
Handles carbon portfolios, projects, methodologies, calculations, and reports.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from db.base import get_db
from db.models.carbon import (
    CarbonMethodology, CarbonEmissionFactor, CarbonPortfolio,
    CarbonProject, CarbonScenario, CarbonCalculation, CarbonReport
)
from schemas.carbon import (
    MethodologyResponse, EmissionFactorResponse,
    CarbonPortfolioCreate, CarbonPortfolioUpdate, CarbonPortfolioResponse, CarbonPortfolioSummary,
    CarbonProjectCreate, CarbonProjectUpdate, CarbonProjectResponse,
    CarbonScenarioCreate, CarbonScenarioUpdate, CarbonScenarioResponse,
    CalculationRequest, CalculationResponse, ProjectCalculationResult,
    YearlyProjection, RiskBreakdown,
    ReportGenerateRequest, ReportResponse,
    PortfolioDashboard, PortfolioDashboardSummary, RiskHeatMapItem
)
from services.carbon_calculator import CarbonCalculationEngine

router = APIRouter(prefix="/api/v1/carbon", tags=["Carbon Credits"])

# Initialize calculation engine
calc_engine = CarbonCalculationEngine()


# ============ Methodologies ============

@router.get("/methodologies", response_model=List[MethodologyResponse])
def get_methodologies(
    sector: Optional[str] = None,
    standard: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get available carbon credit methodologies."""
    query = db.query(CarbonMethodology).filter(CarbonMethodology.status == "active")
    
    if sector:
        query = query.filter(CarbonMethodology.sector == sector)
    if standard:
        query = query.filter(CarbonMethodology.standard == standard)
    
    methodologies = query.offset(skip).limit(limit).all()
    
    # If no methodologies exist, seed some defaults
    if not methodologies and skip == 0:
        _seed_default_methodologies(db)
        methodologies = query.offset(skip).limit(limit).all()
    
    return methodologies


# ============ Emission Factors ============

@router.get("/emission-factors", response_model=List[EmissionFactorResponse])
def get_emission_factors(
    country_code: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get emission factors by country and year."""
    query = db.query(CarbonEmissionFactor)
    
    if country_code:
        query = query.filter(CarbonEmissionFactor.country_code == country_code.upper())
    if year:
        query = query.filter(CarbonEmissionFactor.year == year)
    
    factors = query.order_by(CarbonEmissionFactor.year.desc()).limit(100).all()
    
    # Seed defaults if empty
    if not factors:
        _seed_default_emission_factors(db)
        factors = query.limit(100).all()
    
    return factors


# ============ Portfolios ============

@router.get("/portfolios", response_model=List[CarbonPortfolioSummary])
def get_portfolios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all carbon portfolios."""
    portfolios = db.query(CarbonPortfolio)\
        .filter(CarbonPortfolio.status == "active")\
        .order_by(CarbonPortfolio.updated_at.desc())\
        .offset(skip).limit(limit).all()
    
    result = []
    for p in portfolios:
        project_count = db.query(func.count(CarbonProject.id))\
            .filter(CarbonProject.portfolio_id == p.id).scalar()
        total_credits = db.query(func.sum(CarbonProject.annual_credits))\
            .filter(CarbonProject.portfolio_id == p.id).scalar() or 0
        
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "project_count": project_count,
            "total_annual_credits": total_credits,
            "status": p.status,
            "created_at": p.created_at
        })
    
    return result


@router.post("/portfolios", response_model=CarbonPortfolioResponse)
def create_portfolio(
    data: CarbonPortfolioCreate,
    db: Session = Depends(get_db)
):
    """Create a new carbon portfolio."""
    portfolio = CarbonPortfolio(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        linked_portfolio_id=data.linked_portfolio_id,
        target_annual_credits=data.target_annual_credits,
        budget_usd=data.budget_usd,
        quality_minimum=data.quality_minimum,
        status="active"
    )
    
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return {
        **portfolio.__dict__,
        "project_count": 0,
        "total_annual_credits": 0
    }


@router.get("/portfolios/{portfolio_id}", response_model=CarbonPortfolioResponse)
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Get a specific carbon portfolio."""
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    project_count = db.query(func.count(CarbonProject.id))\
        .filter(CarbonProject.portfolio_id == portfolio_id).scalar()
    total_credits = db.query(func.sum(CarbonProject.annual_credits))\
        .filter(CarbonProject.portfolio_id == portfolio_id).scalar() or 0
    
    return {
        **portfolio.__dict__,
        "project_count": project_count,
        "total_annual_credits": total_credits
    }


@router.put("/portfolios/{portfolio_id}", response_model=CarbonPortfolioResponse)
def update_portfolio(
    portfolio_id: str,
    data: CarbonPortfolioUpdate,
    db: Session = Depends(get_db)
):
    """Update a carbon portfolio."""
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(portfolio, key, value)
    
    portfolio.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(portfolio)
    
    project_count = db.query(func.count(CarbonProject.id))\
        .filter(CarbonProject.portfolio_id == portfolio_id).scalar()
    total_credits = db.query(func.sum(CarbonProject.annual_credits))\
        .filter(CarbonProject.portfolio_id == portfolio_id).scalar() or 0
    
    return {
        **portfolio.__dict__,
        "project_count": project_count,
        "total_annual_credits": total_credits
    }


@router.delete("/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Delete a carbon portfolio."""
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db.delete(portfolio)
    db.commit()
    
    return {"message": "Portfolio deleted", "id": portfolio_id}


@router.get("/portfolios/{portfolio_id}/dashboard", response_model=PortfolioDashboard)
def get_portfolio_dashboard(portfolio_id: str, db: Session = Depends(get_db)):
    """Get dashboard data for a portfolio."""
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    projects = db.query(CarbonProject)\
        .filter(CarbonProject.portfolio_id == portfolio_id)\
        .filter(CarbonProject.status == "active")\
        .all()
    
    # Convert projects to dict format for calculation engine
    project_dicts = [{
        "id": p.id,
        "name": p.name,
        "project_type": p.project_type,
        "country_code": p.country_code,
        "annual_credits": p.annual_credits or 0,
        "quality_rating": p.quality_rating,
        "additionality_score": p.additionality_score,
        "permanence_score": p.permanence_score,
        "co_benefits_score": p.co_benefits_score,
        "verification_status": p.verification_status,
        "price_per_credit_usd": p.price_per_credit_usd
    } for p in projects]
    
    # Get default scenario if exists
    default_scenario = db.query(CarbonScenario)\
        .filter(CarbonScenario.portfolio_id == portfolio_id)\
        .filter(CarbonScenario.is_default == True)\
        .first()
    
    scenario_dict = None
    if default_scenario:
        scenario_dict = {
            "permanence_risk_pct": default_scenario.permanence_risk_pct,
            "delivery_risk_pct": default_scenario.delivery_risk_pct,
            "regulatory_risk_pct": default_scenario.regulatory_risk_pct,
            "market_risk_pct": default_scenario.market_risk_pct,
            "base_carbon_price_usd": default_scenario.base_carbon_price_usd,
            "price_growth_rate_pct": default_scenario.price_growth_rate_pct,
            "discount_rate_pct": default_scenario.discount_rate_pct,
            "projection_years": default_scenario.projection_years
        }
    
    # Calculate portfolio metrics
    calc_result = calc_engine.calculate_portfolio(project_dicts, scenario_dict)
    
    # Generate risk heat map
    risk_heat_map = _generate_risk_heat_map(projects)
    
    # Geographic distribution
    geo_dist = _get_geographic_distribution(projects)
    
    return {
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio.name,
        "summary": {
            "total_annual_credits": calc_result["total_annual_credits"],
            "total_risk_adjusted_credits": calc_result["total_risk_adjusted_credits"],
            "portfolio_quality_score": calc_result["portfolio_quality_score"],
            "portfolio_quality_rating": calc_result["portfolio_quality_rating"],
            "portfolio_npv_10yr_usd": calc_result["portfolio_npv_10yr_usd"],
            "project_count": len(projects),
            "average_risk_score": calc_result["risk_breakdown"]["total_risk_pct"]
        },
        "projects": projects,
        "yearly_projections": calc_result["yearly_projections"],
        "risk_heat_map": risk_heat_map,
        "geographic_distribution": geo_dist
    }


# ============ Projects ============

@router.get("/projects", response_model=List[CarbonProjectResponse])
def get_projects(
    portfolio_id: Optional[str] = None,
    project_type: Optional[str] = None,
    country_code: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get carbon projects with optional filters."""
    query = db.query(CarbonProject).filter(CarbonProject.status == "active")
    
    if portfolio_id:
        query = query.filter(CarbonProject.portfolio_id == portfolio_id)
    if project_type:
        query = query.filter(CarbonProject.project_type == project_type)
    if country_code:
        query = query.filter(CarbonProject.country_code == country_code)
    
    projects = query.order_by(CarbonProject.created_at.desc())\
        .offset(skip).limit(limit).all()
    
    return projects


@router.post("/projects", response_model=CarbonProjectResponse)
def create_project(data: CarbonProjectCreate, db: Session = Depends(get_db)):
    """Create a new carbon project."""
    # Verify portfolio exists
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == data.portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Calculate quality metrics
    quality_score, quality_rating = calc_engine.calculate_quality_score(
        verification_status="unverified"
    )
    
    # Calculate risk
    risk_breakdown = calc_engine.calculate_project_risk(
        project_type=data.project_type,
        country_code=data.country_code,
        quality_rating=data.quality_rating
    )
    
    project = CarbonProject(
        id=str(uuid.uuid4()),
        portfolio_id=data.portfolio_id,
        methodology_id=data.methodology_id,
        name=data.name,
        project_type=data.project_type,
        standard=data.standard,
        registry_id=data.registry_id,
        country_code=data.country_code.upper(),
        region=data.region,
        coordinates=data.coordinates.model_dump() if data.coordinates else None,
        annual_credits=data.annual_credits,
        total_credits=data.total_credits,
        vintage_start=data.vintage_start,
        vintage_end=data.vintage_end,
        crediting_period_years=data.crediting_period_years,
        quality_rating=data.quality_rating or quality_rating,
        quality_score=data.quality_score or quality_score,
        risk_level=data.risk_level or _get_risk_level(risk_breakdown["total_risk_pct"]),
        risk_score=data.risk_score or risk_breakdown["total_risk_pct"],
        price_per_credit_usd=data.price_per_credit_usd,
        total_investment_usd=data.total_investment_usd,
        sdg_contributions=data.sdg_contributions,
        co_benefits=data.co_benefits,
        status="active",
        verification_status="unverified"
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project


@router.get("/projects/{project_id}", response_model=CarbonProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific carbon project."""
    project = db.query(CarbonProject).filter(CarbonProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/projects/{project_id}", response_model=CarbonProjectResponse)
def update_project(
    project_id: str,
    data: CarbonProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a carbon project."""
    project = db.query(CarbonProject).filter(CarbonProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle coordinates specially
    if "coordinates" in update_data and update_data["coordinates"]:
        update_data["coordinates"] = update_data["coordinates"].model_dump() if hasattr(update_data["coordinates"], "model_dump") else update_data["coordinates"]
    
    for key, value in update_data.items():
        setattr(project, key, value)
    
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a carbon project."""
    project = db.query(CarbonProject).filter(CarbonProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted", "id": project_id}


# ============ Scenarios ============

@router.get("/portfolios/{portfolio_id}/scenarios", response_model=List[CarbonScenarioResponse])
def get_scenarios(portfolio_id: str, db: Session = Depends(get_db)):
    """Get scenarios for a portfolio."""
    scenarios = db.query(CarbonScenario)\
        .filter(CarbonScenario.portfolio_id == portfolio_id)\
        .order_by(CarbonScenario.is_default.desc(), CarbonScenario.created_at.desc())\
        .all()
    
    # Create default scenario if none exist
    if not scenarios:
        default_scenario = CarbonScenario(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            name="Base Case",
            description="Default scenario with standard assumptions",
            is_default=True
        )
        db.add(default_scenario)
        db.commit()
        db.refresh(default_scenario)
        scenarios = [default_scenario]
    
    return scenarios


@router.post("/portfolios/{portfolio_id}/scenarios", response_model=CarbonScenarioResponse)
def create_scenario(
    portfolio_id: str,
    data: CarbonScenarioCreate,
    db: Session = Depends(get_db)
):
    """Create a new scenario for a portfolio."""
    # Verify portfolio exists
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # If this is marked as default, unset other defaults
    if data.is_default:
        db.query(CarbonScenario)\
            .filter(CarbonScenario.portfolio_id == portfolio_id)\
            .update({"is_default": False})
    
    scenario = CarbonScenario(
        id=str(uuid.uuid4()),
        portfolio_id=portfolio_id,
        name=data.name,
        description=data.description,
        is_default=data.is_default,
        permanence_risk_pct=data.permanence_risk_pct,
        delivery_risk_pct=data.delivery_risk_pct,
        regulatory_risk_pct=data.regulatory_risk_pct,
        market_risk_pct=data.market_risk_pct,
        base_carbon_price_usd=data.base_carbon_price_usd,
        price_growth_rate_pct=data.price_growth_rate_pct,
        price_volatility_pct=data.price_volatility_pct,
        discount_rate_pct=data.discount_rate_pct,
        projection_years=data.projection_years,
        parameters=data.parameters
    )
    
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    
    return scenario


@router.delete("/portfolios/{portfolio_id}/scenarios/{scenario_id}")
def delete_scenario(
    portfolio_id: str,
    scenario_id: str,
    db: Session = Depends(get_db)
):
    """Delete a scenario."""
    scenario = db.query(CarbonScenario)\
        .filter(CarbonScenario.id == scenario_id)\
        .filter(CarbonScenario.portfolio_id == portfolio_id)\
        .first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    if scenario.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default scenario")
    
    db.delete(scenario)
    db.commit()
    
    return {"message": "Scenario deleted", "id": scenario_id}


# ============ Calculations ============

@router.post("/calculate", response_model=CalculationResponse)
def run_calculation(data: CalculationRequest, db: Session = Depends(get_db)):
    """Run a carbon credit calculation."""
    # Verify portfolio exists
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == data.portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get scenario if specified
    scenario_dict = None
    if data.scenario_id:
        scenario = db.query(CarbonScenario).filter(CarbonScenario.id == data.scenario_id).first()
        if scenario:
            scenario_dict = {
                "permanence_risk_pct": scenario.permanence_risk_pct,
                "delivery_risk_pct": scenario.delivery_risk_pct,
                "regulatory_risk_pct": scenario.regulatory_risk_pct,
                "market_risk_pct": scenario.market_risk_pct,
                "base_carbon_price_usd": scenario.base_carbon_price_usd,
                "price_growth_rate_pct": scenario.price_growth_rate_pct,
                "price_volatility_pct": scenario.price_volatility_pct,
                "discount_rate_pct": scenario.discount_rate_pct,
                "projection_years": scenario.projection_years
            }
    
    # Get projects
    if data.projects:
        # Use specified projects
        project_ids = [p.project_id for p in data.projects]
        projects = db.query(CarbonProject)\
            .filter(CarbonProject.id.in_(project_ids))\
            .all()
        
        # Apply custom overrides
        project_dicts = []
        project_overrides = {p.project_id: p for p in data.projects}
        for p in projects:
            proj_data = {
                "id": p.id,
                "name": p.name,
                "project_type": p.project_type,
                "country_code": p.country_code,
                "annual_credits": p.annual_credits or 0,
                "quality_rating": p.quality_rating,
                "additionality_score": p.additionality_score,
                "permanence_score": p.permanence_score,
                "co_benefits_score": p.co_benefits_score,
                "verification_status": p.verification_status,
                "price_per_credit_usd": p.price_per_credit_usd
            }
            # Apply overrides
            if p.id in project_overrides:
                override = project_overrides[p.id]
                if override.annual_credits is not None:
                    proj_data["annual_credits"] = override.annual_credits
                if override.custom_risk_adjustments:
                    proj_data["custom_risk_adjustments"] = override.custom_risk_adjustments
            project_dicts.append(proj_data)
    else:
        # Use all portfolio projects
        projects = db.query(CarbonProject)\
            .filter(CarbonProject.portfolio_id == data.portfolio_id)\
            .filter(CarbonProject.status == "active")\
            .all()
        
        project_dicts = [{
            "id": p.id,
            "name": p.name,
            "project_type": p.project_type,
            "country_code": p.country_code,
            "annual_credits": p.annual_credits or 0,
            "quality_rating": p.quality_rating,
            "additionality_score": p.additionality_score,
            "permanence_score": p.permanence_score,
            "co_benefits_score": p.co_benefits_score,
            "verification_status": p.verification_status,
            "price_per_credit_usd": p.price_per_credit_usd
        } for p in projects]
    
    # Run calculation
    run_mc = data.calculation_type == "monte_carlo"
    calc_result = calc_engine.calculate_portfolio(
        project_dicts, 
        scenario_dict, 
        run_monte_carlo=run_mc
    )
    
    # Store calculation
    calculation = CarbonCalculation(
        id=str(uuid.uuid4()),
        portfolio_id=data.portfolio_id,
        scenario_id=data.scenario_id,
        calculation_type=data.calculation_type,
        status="completed",
        project_count=len(project_dicts),
        total_input_credits=sum(p["annual_credits"] for p in project_dicts),
        total_annual_credits=calc_result["total_annual_credits"],
        total_risk_adjusted_credits=calc_result["total_risk_adjusted_credits"],
        portfolio_quality_score=calc_result["portfolio_quality_score"],
        portfolio_quality_rating=calc_result["portfolio_quality_rating"],
        portfolio_npv_10yr_usd=calc_result["portfolio_npv_10yr_usd"],
        results_by_project=calc_result["project_results"],
        results_by_year=calc_result["yearly_projections"],
        risk_breakdown=calc_result["risk_breakdown"],
        monte_carlo_runs=data.monte_carlo_runs if run_mc else None,
        confidence_interval_low=calc_result.get("confidence_interval_low"),
        confidence_interval_high=calc_result.get("confidence_interval_high"),
        completed_at=datetime.now(timezone.utc)
    )
    
    db.add(calculation)
    db.commit()
    db.refresh(calculation)
    
    # Build response
    return {
        "calculation_id": calculation.id,
        "portfolio_id": data.portfolio_id,
        "scenario_id": data.scenario_id,
        "status": "completed",
        "calculation_type": data.calculation_type,
        "total_annual_credits": calc_result["total_annual_credits"],
        "total_risk_adjusted_credits": calc_result["total_risk_adjusted_credits"],
        "portfolio_quality_score": calc_result["portfolio_quality_score"],
        "portfolio_quality_rating": calc_result["portfolio_quality_rating"],
        "portfolio_npv_10yr_usd": calc_result["portfolio_npv_10yr_usd"],
        "project_count": len(project_dicts),
        "projects": calc_result["project_results"],
        "yearly_projections": calc_result["yearly_projections"],
        "risk_breakdown": calc_result["risk_breakdown"],
        "confidence_interval_low": calc_result.get("confidence_interval_low"),
        "confidence_interval_high": calc_result.get("confidence_interval_high"),
        "created_at": calculation.created_at
    }


@router.get("/calculations/{calculation_id}")
def get_calculation(calculation_id: str, db: Session = Depends(get_db)):
    """Get a specific calculation result."""
    calculation = db.query(CarbonCalculation).filter(CarbonCalculation.id == calculation_id).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    return {
        "calculation_id": calculation.id,
        "portfolio_id": calculation.portfolio_id,
        "scenario_id": calculation.scenario_id,
        "status": calculation.status,
        "calculation_type": calculation.calculation_type,
        "total_annual_credits": calculation.total_annual_credits,
        "total_risk_adjusted_credits": calculation.total_risk_adjusted_credits,
        "portfolio_quality_score": calculation.portfolio_quality_score,
        "portfolio_quality_rating": calculation.portfolio_quality_rating,
        "portfolio_npv_10yr_usd": calculation.portfolio_npv_10yr_usd,
        "project_count": calculation.project_count,
        "projects": calculation.results_by_project,
        "yearly_projections": calculation.results_by_year,
        "risk_breakdown": calculation.risk_breakdown,
        "confidence_interval_low": calculation.confidence_interval_low,
        "confidence_interval_high": calculation.confidence_interval_high,
        "created_at": calculation.created_at
    }


# ============ Reports ============

@router.post("/reports/generate", response_model=ReportResponse)
def generate_report(data: ReportGenerateRequest, db: Session = Depends(get_db)):
    """Generate a carbon credit report."""
    # Verify portfolio exists
    portfolio = db.query(CarbonPortfolio).filter(CarbonPortfolio.id == data.portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get calculation if specified
    content = {"portfolio_name": portfolio.name}
    if data.calculation_id:
        calculation = db.query(CarbonCalculation).filter(CarbonCalculation.id == data.calculation_id).first()
        if calculation:
            content["calculation"] = {
                "total_annual_credits": calculation.total_annual_credits,
                "risk_adjusted_credits": calculation.total_risk_adjusted_credits,
                "quality_score": calculation.portfolio_quality_score,
                "npv": calculation.portfolio_npv_10yr_usd
            }
    
    # Create report record
    report = CarbonReport(
        id=str(uuid.uuid4()),
        portfolio_id=data.portfolio_id,
        calculation_id=data.calculation_id,
        report_type=data.report_type,
        format=data.format,
        title=data.title or f"{portfolio.name} - {data.report_type.title()} Report",
        content=content,
        status="completed"
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report


@router.get("/reports/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    """Download a generated report."""
    report = db.query(CarbonReport).filter(CarbonReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # In production, this would return the actual file
    return {
        "report_id": report.id,
        "format": report.format,
        "content": report.content,
        "message": "Report download simulated - in production this would return the file"
    }


# ============ Helper Functions ============

def _get_risk_level(risk_pct: float) -> str:
    """Convert risk percentage to risk level."""
    if risk_pct < 20:
        return "Low"
    elif risk_pct < 40:
        return "Medium"
    else:
        return "High"


def _generate_risk_heat_map(projects: List[CarbonProject]) -> List[RiskHeatMapItem]:
    """Generate risk heat map data from projects."""
    risk_categories = {}
    
    for p in projects:
        ptype = p.project_type or "OTHER"
        risk_score = p.risk_score or 30
        
        if ptype not in risk_categories:
            risk_categories[ptype] = {"scores": [], "count": 0}
        
        risk_categories[ptype]["scores"].append(risk_score)
        risk_categories[ptype]["count"] += 1
    
    heat_map = []
    for category, data in risk_categories.items():
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        
        # Determine impact and probability
        if avg_score < 25:
            impact, probability = "Low", "Low"
        elif avg_score < 35:
            impact, probability = "Medium", "Low"
        elif avg_score < 45:
            impact, probability = "Medium", "Medium"
        elif avg_score < 55:
            impact, probability = "High", "Medium"
        else:
            impact, probability = "High", "High"
        
        heat_map.append({
            "category": category.replace("_", " ").title(),
            "score": round(avg_score, 1),
            "impact": impact,
            "probability": probability
        })
    
    return heat_map


def _get_geographic_distribution(projects: List[CarbonProject]) -> List[dict]:
    """Get geographic distribution of projects."""
    geo_dist = {}
    
    for p in projects:
        country = p.country_code or "UNKNOWN"
        if country not in geo_dist:
            geo_dist[country] = {
                "country_code": country,
                "project_count": 0,
                "total_credits": 0,
                "coordinates": []
            }
        
        geo_dist[country]["project_count"] += 1
        geo_dist[country]["total_credits"] += p.annual_credits or 0
        
        if p.coordinates:
            geo_dist[country]["coordinates"].append(p.coordinates)
    
    return list(geo_dist.values())


def _seed_default_methodologies(db: Session):
    """Seed default carbon methodologies."""
    methodologies = [
        {"code": "VM0007", "name": "REDD+ Methodology Framework", "standard": "VCS", "sector": "Forestry", "subsector": "REDD+"},
        {"code": "VM0015", "name": "Avoided Unplanned Deforestation", "standard": "VCS", "sector": "Forestry", "subsector": "AUD"},
        {"code": "VM0006", "name": "Carbon Credits from Wind Power", "standard": "VCS", "sector": "Energy", "subsector": "Wind"},
        {"code": "AMS-I.D", "name": "Grid-connected Renewable Electricity", "standard": "CDM", "sector": "Energy", "subsector": "Renewable"},
        {"code": "AMS-III.D", "name": "Methane Recovery from Manure", "standard": "CDM", "sector": "Agriculture", "subsector": "Methane"},
        {"code": "GS-TPDDTEC", "name": "Technologies and Practices to Displace Decentralized Thermal Energy Consumption", "standard": "GOLD_STANDARD", "sector": "Energy", "subsector": "Cookstoves"},
    ]
    
    for m in methodologies:
        methodology = CarbonMethodology(
            id=str(uuid.uuid4()),
            code=m["code"],
            name=m["name"],
            standard=m["standard"],
            sector=m["sector"],
            subsector=m.get("subsector"),
            status="active"
        )
        db.add(methodology)
    
    db.commit()


def _seed_default_emission_factors(db: Session):
    """Seed default emission factors."""
    factors = [
        {"country_code": "US", "country_name": "United States", "year": 2024, "grid_emission_factor": 0.417},
        {"country_code": "CN", "country_name": "China", "year": 2024, "grid_emission_factor": 0.581},
        {"country_code": "IN", "country_name": "India", "year": 2024, "grid_emission_factor": 0.708},
        {"country_code": "DE", "country_name": "Germany", "year": 2024, "grid_emission_factor": 0.366},
        {"country_code": "BR", "country_name": "Brazil", "year": 2024, "grid_emission_factor": 0.074},
        {"country_code": "GB", "country_name": "United Kingdom", "year": 2024, "grid_emission_factor": 0.233},
        {"country_code": "JP", "country_name": "Japan", "year": 2024, "grid_emission_factor": 0.470},
        {"country_code": "AU", "country_name": "Australia", "year": 2024, "grid_emission_factor": 0.656},
    ]
    
    for f in factors:
        factor = CarbonEmissionFactor(
            id=str(uuid.uuid4()),
            country_code=f["country_code"],
            country_name=f["country_name"],
            year=f["year"],
            grid_emission_factor=f["grid_emission_factor"],
            source="IEA",
            is_default=True
        )
        db.add(factor)
    
    db.commit()
