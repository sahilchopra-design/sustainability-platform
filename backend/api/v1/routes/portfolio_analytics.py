"""
Portfolio Aggregation and Reporting Module API Routes
Consolidates property valuations into portfolio-level analytics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import date
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS
from decimal import Decimal

from schemas.portfolio_analytics import (
    PortfolioType, InvestmentStrategy, ReportType, ReportFormat,
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioListResponse,
    HoldingCreate, HoldingResponse, HoldingListResponse,
    PortfolioAnalyticsRequest, PortfolioAnalyticsResponse,
    ScenarioComparisonRequest, ScenarioComparisonResult,
    ReportGenerateRequest, ReportResponse, ReportContent,
    DashboardRequest, DashboardResponse,
)
from services.portfolio_analytics_engine_v2 import (
    PortfolioAggregationEngine,
    get_portfolio, get_holdings, save_portfolio, save_holding,
    remove_holding, list_portfolios, get_report, init_sample_data
)


router = APIRouter(prefix="/api/v1/portfolio-analytics", tags=["Portfolio Analytics"])

# Initialize the engine
engine = PortfolioAggregationEngine()


# ============ Portfolio CRUD ============

@router.get("/portfolios", response_model=PortfolioListResponse)
async def list_all_portfolios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    portfolio_type: Optional[PortfolioType] = None,
    strategy: Optional[InvestmentStrategy] = None,
):
    """
    List all portfolios with optional filtering.
    
    Returns paginated list of portfolios with summary metrics.
    """
    all_portfolios = list_portfolios()
    
    # Apply filters
    if portfolio_type:
        all_portfolios = [p for p in all_portfolios if p.get("portfolio_type") == portfolio_type.value]
    if strategy:
        all_portfolios = [p for p in all_portfolios if p.get("investment_strategy") == strategy.value]
    
    total = len(all_portfolios)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_portfolios[start:end]
    
    items = []
    for p in paginated:
        holdings = get_holdings(p["id"])
        total_value = sum(Decimal(str(h.get("current_value", 0))) for h in holdings)
        total_income = sum(Decimal(str(h.get("annual_income", 0))) for h in holdings)
        
        # portfolios_pg uses string IDs (e.g. "demo-eu-banking-sfdr") — normalise to UUID
        try:
            p_uuid = UUID(p["id"])
        except (ValueError, AttributeError):
            p_uuid = uuid5(NAMESPACE_DNS, p["id"])
        items.append(PortfolioResponse(
            id=p_uuid,
            name=p["name"],
            description=p.get("description"),
            portfolio_type=PortfolioType(p.get("portfolio_type", "fund")),
            investment_strategy=InvestmentStrategy(p.get("investment_strategy", "core")) if p.get("investment_strategy") else None,
            target_return=Decimal(str(p.get("target_return", 0))) if p.get("target_return") else None,
            aum=Decimal(str(p.get("aum", 0))),
            currency=p.get("currency", "EUR"),
            inception_date=p.get("inception_date"),
            owner_id=None,
            created_at=p.get("created_at"),
            updated_at=p.get("updated_at"),
            total_properties=len(holdings),
            total_value=total_value,
            total_income=total_income,
        ))
    
    return PortfolioListResponse(items=items, total=total)


@router.post("/portfolios", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(data: PortfolioCreate):
    """
    Create a new portfolio.
    
    Returns the created portfolio with its ID.
    """
    from datetime import datetime, timezone
    
    portfolio_id = str(uuid4())
    now = datetime.now(timezone.utc)
    
    portfolio_data = {
        "id": portfolio_id,
        "name": data.name,
        "description": data.description,
        "portfolio_type": data.portfolio_type.value,
        "investment_strategy": data.investment_strategy.value if data.investment_strategy else None,
        "target_return": data.target_return,
        "aum": data.aum,
        "currency": data.currency,
        "inception_date": data.inception_date,
        "owner_id": None,
        "created_at": now,
        "updated_at": now,
    }
    
    save_portfolio(portfolio_id, portfolio_data)
    
    return PortfolioResponse(
        id=UUID(portfolio_id),
        name=data.name,
        description=data.description,
        portfolio_type=data.portfolio_type,
        investment_strategy=data.investment_strategy,
        target_return=data.target_return,
        aum=data.aum,
        currency=data.currency,
        inception_date=data.inception_date,
        created_at=now,
        updated_at=now,
        total_properties=0,
    )


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio_by_id(portfolio_id: str):
    """
    Get portfolio details by ID.
    
    Returns portfolio information with calculated metrics.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    
    holdings = get_holdings(portfolio_id)
    total_value = sum(Decimal(str(h.get("current_value", 0))) for h in holdings)
    total_income = sum(Decimal(str(h.get("annual_income", 0))) for h in holdings)
    
    return PortfolioResponse(
        id=UUID(portfolio["id"]),
        name=portfolio["name"],
        description=portfolio.get("description"),
        portfolio_type=PortfolioType(portfolio.get("portfolio_type", "fund")),
        investment_strategy=InvestmentStrategy(portfolio.get("investment_strategy", "core")) if portfolio.get("investment_strategy") else None,
        target_return=Decimal(str(portfolio.get("target_return", 0))) if portfolio.get("target_return") else None,
        aum=Decimal(str(portfolio.get("aum", 0))),
        currency=portfolio.get("currency", "USD"),
        inception_date=portfolio.get("inception_date"),
        owner_id=UUID(portfolio["owner_id"]) if portfolio.get("owner_id") else None,
        created_at=portfolio["created_at"],
        updated_at=portfolio["updated_at"],
        total_properties=len(holdings),
        total_value=total_value,
        total_income=total_income,
    )


@router.patch("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(portfolio_id: str, data: PortfolioUpdate):
    """
    Update portfolio information.
    
    Only provided fields will be updated.
    """
    from datetime import datetime, timezone
    
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    
    # Update fields
    if data.name is not None:
        portfolio["name"] = data.name
    if data.description is not None:
        portfolio["description"] = data.description
    if data.portfolio_type is not None:
        portfolio["portfolio_type"] = data.portfolio_type.value
    if data.investment_strategy is not None:
        portfolio["investment_strategy"] = data.investment_strategy.value
    if data.target_return is not None:
        portfolio["target_return"] = data.target_return
    if data.aum is not None:
        portfolio["aum"] = data.aum
    
    portfolio["updated_at"] = datetime.now(timezone.utc)
    save_portfolio(portfolio_id, portfolio)
    
    holdings = get_holdings(portfolio_id)
    total_value = sum(Decimal(str(h.get("current_value", 0))) for h in holdings)
    total_income = sum(Decimal(str(h.get("annual_income", 0))) for h in holdings)
    
    return PortfolioResponse(
        id=UUID(portfolio["id"]),
        name=portfolio["name"],
        description=portfolio.get("description"),
        portfolio_type=PortfolioType(portfolio.get("portfolio_type", "fund")),
        investment_strategy=InvestmentStrategy(portfolio.get("investment_strategy", "core")) if portfolio.get("investment_strategy") else None,
        target_return=Decimal(str(portfolio.get("target_return", 0))) if portfolio.get("target_return") else None,
        aum=Decimal(str(portfolio.get("aum", 0))),
        currency=portfolio.get("currency", "USD"),
        inception_date=portfolio.get("inception_date"),
        owner_id=UUID(portfolio["owner_id"]) if portfolio.get("owner_id") else None,
        created_at=portfolio["created_at"],
        updated_at=portfolio["updated_at"],
        total_properties=len(holdings),
        total_value=total_value,
        total_income=total_income,
    )


# ============ Holdings ============

@router.get("/portfolios/{portfolio_id}/holdings", response_model=HoldingListResponse)
async def list_holdings(portfolio_id: str):
    """
    Get all holdings for a portfolio.
    
    Returns list of property holdings with their details.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    
    holdings = get_holdings(portfolio_id)
    total_value = sum(Decimal(str(h.get("current_value", 0))) for h in holdings)
    
    items = [
        HoldingResponse(
            id=UUID(h["id"]) if isinstance(h["id"], str) and len(h["id"]) == 36 else uuid4(),
            portfolio_id=UUID(portfolio_id),
            property_id=UUID(h.get("property_id", str(uuid4()))),
            acquisition_date=h.get("acquisition_date"),
            acquisition_cost=Decimal(str(h.get("acquisition_cost", 0))) if h.get("acquisition_cost") else None,
            current_value=Decimal(str(h.get("current_value", 0))) if h.get("current_value") else None,
            ownership_percentage=Decimal(str(h.get("ownership_percentage", 1))),
            annual_income=Decimal(str(h.get("annual_income", 0))) if h.get("annual_income") else None,
            unrealized_gain_loss=Decimal(str(h.get("unrealized_gain_loss", 0))) if h.get("unrealized_gain_loss") else None,
            property_name=h.get("property_name"),
            property_type=h.get("property_type"),
            property_location=h.get("property_location"),
        )
        for h in holdings
    ]
    
    return HoldingListResponse(items=items, total=len(items), total_value=total_value)


@router.post("/portfolios/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=201)
async def add_holding(portfolio_id: str, data: HoldingCreate):
    """
    Add a new holding to the portfolio.
    
    Returns the created holding.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    
    holding_id = str(uuid4())
    holding_data = {
        "id": holding_id,
        "portfolio_id": portfolio_id,
        "property_id": str(data.property_id),
        "acquisition_date": data.acquisition_date,
        "acquisition_cost": data.acquisition_cost,
        "current_value": data.current_value,
        "ownership_percentage": data.ownership_percentage,
        "annual_income": data.annual_income,
    }
    
    save_holding(portfolio_id, holding_data)
    
    return HoldingResponse(
        id=UUID(holding_id),
        portfolio_id=UUID(portfolio_id),
        property_id=data.property_id,
        acquisition_date=data.acquisition_date,
        acquisition_cost=data.acquisition_cost,
        current_value=data.current_value,
        ownership_percentage=data.ownership_percentage,
        annual_income=data.annual_income,
    )


@router.delete("/portfolios/{portfolio_id}/holdings/{property_id}", status_code=204)
async def delete_holding(portfolio_id: str, property_id: str):
    """
    Remove a holding from the portfolio.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    
    success = remove_holding(portfolio_id, property_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Holding {property_id} not found in portfolio")


# ============ Analytics ============

@router.get("/portfolios/{portfolio_id}/analytics", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(
    portfolio_id: str,
    scenario_id: Optional[str] = None,
    time_horizon: int = Query(10, ge=1, le=30),
    as_of_date: Optional[date] = None,
):
    """
    Calculate comprehensive portfolio analytics.
    
    Returns aggregated metrics including:
    - Portfolio summary (total value, change, income, yield)
    - Risk metrics (weighted avg risk, VaR, risk distribution)
    - Stranding analysis (count, value, timeline)
    - Sustainability metrics (GRESB, certifications)
    - Concentration analysis (geographic, sector)
    """
    try:
        analytics = engine.get_analytics(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id,
            time_horizon=time_horizon
        )
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/portfolios/{portfolio_id}/scenarios/compare", response_model=ScenarioComparisonResult)
async def compare_scenarios(
    portfolio_id: str,
    data: ScenarioComparisonRequest,
):
    """
    Compare multiple scenarios for a portfolio.
    
    Returns comparison table with value impacts, stranding counts,
    and risk metrics across scenarios. Identifies best/worst scenarios.
    """
    try:
        scenario_ids = [str(sid) for sid in data.scenario_ids]
        result = engine.compare_scenarios(
            portfolio_id=portfolio_id,
            scenario_ids=scenario_ids,
            time_horizon=data.time_horizon
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============ Dashboard ============

@router.get("/portfolios/{portfolio_id}/dashboard", response_model=DashboardResponse)
async def get_portfolio_dashboard(
    portfolio_id: str,
    scenario_id: Optional[str] = None,
    time_horizon: int = Query(10, ge=1, le=30),
):
    """
    Get executive dashboard data for a portfolio.
    
    Returns:
    - KPI cards (total value, properties, risk score, VaR, etc.)
    - Charts (sector allocation, geographic distribution, risk distribution)
    - Alerts (stranded assets, concentration warnings, etc.)
    """
    try:
        dashboard = engine.get_dashboard(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id,
            time_horizon=time_horizon
        )
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============ Reports ============

@router.post("/portfolios/{portfolio_id}/reports/generate")
async def generate_report(
    portfolio_id: str,
    data: ReportGenerateRequest,
):
    """
    Generate a comprehensive report for the portfolio.
    
    Report types:
    - valuation: Detailed property valuations and methodology
    - climate_risk: Physical and transition risk assessment
    - sustainability: ESG metrics, certifications, improvement roadmap
    - tcfd: TCFD-aligned disclosure report
    - investor: Quarterly investor report
    - executive: Executive summary dashboard
    
    Returns the generated report content.
    """
    try:
        report = engine.generate_report(
            portfolio_id=portfolio_id,
            report_type=data.report_type,
            scenario_id=str(data.scenario_id) if data.scenario_id else None,
            time_horizon=data.time_horizon,
            include_charts=data.include_charts,
            include_property_details=data.include_property_details,
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """
    Get a previously generated report by ID.
    """
    report = get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


# ============ Utility Endpoints ============

@router.get("/enums")
async def get_enum_values():
    """
    Get all available enum values for portfolio analytics.
    
    Useful for populating dropdowns in the frontend.
    """
    return {
        "portfolio_types": [e.value for e in PortfolioType],
        "investment_strategies": [e.value for e in InvestmentStrategy],
        "report_types": [e.value for e in ReportType],
        "report_formats": [e.value for e in ReportFormat],
    }


@router.post("/seed-sample-data")
async def seed_sample_data():
    """
    Initialize sample portfolios for demonstration.

    Creates 3 sample portfolios with holdings.
    Any assets created receive DQS-5 badge (demo data — no primary emissions).
    """
    init_sample_data()
    portfolios = list_portfolios()
    return {
        "message": "Sample data initialized",
        "portfolio_count": len(portfolios),
        "portfolios": [{"id": p["id"], "name": p["name"]} for p in portfolios],
        "data_quality_note": "Demo data uses DQS-5 sector-average estimates. "
                             "Upload primary emissions data to improve quality.",
    }


# ============ PCAF / WACI — Real Financed Emissions ============

@router.post("/{portfolio_id}/pcaf-run")
async def run_pcaf_for_portfolio(portfolio_id: str):
    """
    Execute a full PCAF Standard v2.0 financed emissions calculation for
    a portfolio stored in assets_pg.

    - Loads assets and resolves DQS hierarchy (primary data / Data Hub / sector avg)
    - Computes WACI, carbon footprint, ITR, attribution factors
    - Writes results to pcaf_time_series
    - Fires alert engine (glidepath deviation, DQS thresholds)
    - Returns full result including investee breakdown and PAI indicators

    Safe to call repeatedly — each call overwrites pcaf_time_series for
    the current reporting year.
    """
    from services.portfolio_analytics_engine import run_pcaf_calculation

    try:
        result = run_pcaf_calculation(portfolio_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PCAF calculation failed: {str(exc)}",
        )

    if result.get("error") and not result.get("data_available"):
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/{portfolio_id}/pcaf-results")
async def get_pcaf_results(portfolio_id: str):
    """
    Return the latest PCAF metrics for a portfolio.

    Uses cached pcaf_time_series records if available.
    Runs the engine on-demand if no cached data exists (first call).

    Response includes:
      portfolio_summary  — WACI, ITR, coverage, DQS
      dqs_distribution   — count of assets per DQS tier (1-5)
      sector_breakdown   — per-sector WACI contribution
      from_cache         — true if data came from pcaf_time_series
    """
    from services.portfolio_analytics_engine import get_latest_pcaf_results

    try:
        result = get_latest_pcaf_results(portfolio_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PCAF results fetch failed: {str(exc)}",
        )

    return result


@router.get("/{portfolio_id}/waci-history")
async def get_waci_history(
    portfolio_id: str,
    years: int = Query(10, ge=1, le=20, description="Number of reporting years to return"),
):
    """
    Return year-by-year WACI vs. glidepath for the portfolio.

    Used by sparklines on Portfolio Analytics page and Glidepath Tracker.
    Data comes from pcaf_time_series.  Returns empty list if no calculations
    have been run yet.
    """
    from services.portfolio_analytics_engine import get_waci_history as _waci_history

    try:
        history = _waci_history(portfolio_id, years=years)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"WACI history fetch failed: {str(exc)}",
        )

    return {
        "portfolio_id": portfolio_id,
        "history":      history,
        "periods":      len(history),
    }
