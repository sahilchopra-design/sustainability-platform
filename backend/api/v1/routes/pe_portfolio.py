"""
API Routes: PE Portfolio Monitoring + Value Creation
=====================================================
POST /api/v1/pe-portfolio/monitor-company     — Single company KPI monitoring
POST /api/v1/pe-portfolio/monitor-portfolio    — Portfolio-wide monitoring
POST /api/v1/pe-portfolio/value-creation-plan  — Generate value creation plan
GET  /api/v1/pe-portfolio/kpi-template         — ILPA KPI collection template
GET  /api/v1/pe-portfolio/sector-levers        — Available ESG levers by sector

DB-Powered (pe_portfolio_companies):
POST  /api/v1/pe-portfolio/db/companies          — Create portfolio company
GET   /api/v1/pe-portfolio/db/companies          — List portfolio companies
PATCH /api/v1/pe-portfolio/db/companies/{id}     — Update portfolio company
POST  /api/v1/pe-portfolio/db/companies/{id}/exit — Record exit
GET   /api/v1/pe-portfolio/db/summary            — Portfolio summary (TVPI/DPI/RVPI)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date

from services.pe_portfolio_monitor import (
    PEPortfolioMonitor,
    CompanyKPIData,
    CompanyTarget,
    CompanyMonitorInput,
    ILPA_KPIS,
)
from services.pe_value_creation import (
    PEValueCreationEngine,
)

router = APIRouter(prefix="/api/v1/pe-portfolio", tags=["PE Portfolio"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class KPIDataRequest(BaseModel):
    company_id: str
    company_name: str
    sector: str = "Other"
    reporting_period: str = ""
    kpi_values: dict[str, float] = Field(default_factory=dict)


class TargetRequest(BaseModel):
    kpi_id: str
    target_value: float
    target_year: int = 2030


class CompanyMonitorRequest(BaseModel):
    company_id: str
    company_name: str
    sector: str = "Other"
    fund_id: str = ""
    equity_invested_eur: float = Field(0, ge=0)
    ownership_pct: float = Field(0, ge=0, le=100)
    current_period: KPIDataRequest
    prior_period: Optional[KPIDataRequest] = None
    targets: list[TargetRequest] = Field(default_factory=list)


class PortfolioMonitorRequest(BaseModel):
    fund_id: str
    companies: list[CompanyMonitorRequest]


class ValueCreationRequest(BaseModel):
    company_id: str
    company_name: str
    sector: str = "Other"
    ebitda_eur: float = Field(0, ge=0)
    entry_multiple: float = Field(0, ge=0)
    current_esg_score: float = Field(50, ge=0, le=100)
    revenue_eur: float = Field(0, ge=0)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_kpi_data(req: KPIDataRequest) -> CompanyKPIData:
    return CompanyKPIData(
        company_id=req.company_id,
        company_name=req.company_name,
        sector=req.sector,
        reporting_period=req.reporting_period,
        kpi_values=req.kpi_values,
    )


def _to_monitor_input(req: CompanyMonitorRequest) -> CompanyMonitorInput:
    prior = _to_kpi_data(req.prior_period) if req.prior_period else None
    targets = [CompanyTarget(
        kpi_id=t.kpi_id, target_value=t.target_value, target_year=t.target_year,
    ) for t in req.targets]
    return CompanyMonitorInput(
        company_id=req.company_id,
        company_name=req.company_name,
        sector=req.sector,
        fund_id=req.fund_id,
        equity_invested_eur=req.equity_invested_eur,
        ownership_pct=req.ownership_pct,
        current_period=_to_kpi_data(req.current_period),
        prior_period=prior,
        targets=targets,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_kpi_status(k) -> dict:
    return {
        "kpi_id": k.kpi_id,
        "kpi_name": k.kpi_name,
        "category": k.category,
        "unit": k.unit,
        "direction": k.direction,
        "current_value": k.current_value,
        "prior_value": k.prior_value,
        "target_value": k.target_value,
        "yoy_change": k.yoy_change,
        "yoy_change_pct": k.yoy_change_pct,
        "improved": k.improved,
        "on_target": k.on_target,
        "traffic_light": k.traffic_light,
    }


def _ser_company_result(r) -> dict:
    return {
        "company_id": r.company_id,
        "company_name": r.company_name,
        "sector": r.sector,
        "reporting_period": r.reporting_period,
        "kpi_statuses": [_ser_kpi_status(k) for k in r.kpi_statuses],
        "green_count": r.green_count,
        "amber_count": r.amber_count,
        "red_count": r.red_count,
        "total_kpis": r.total_kpis,
        "overall_traffic_light": r.overall_traffic_light,
        "improvement_count": r.improvement_count,
        "deterioration_count": r.deterioration_count,
        "on_target_count": r.on_target_count,
        "off_target_count": r.off_target_count,
    }


def _ser_lever(l) -> dict:
    return {
        "lever_id": l.lever_id,
        "name": l.name,
        "category": l.category,
        "description": l.description,
        "capex_eur_low": l.capex_eur_low,
        "capex_eur_high": l.capex_eur_high,
        "capex_eur_mid": l.capex_eur_mid,
        "annual_savings_pct_low": l.annual_savings_pct_low,
        "annual_savings_pct_high": l.annual_savings_pct_high,
        "annual_savings_eur_mid": l.annual_savings_eur_mid,
        "ebitda_uplift_pct_low": l.ebitda_uplift_pct_low,
        "ebitda_uplift_pct_high": l.ebitda_uplift_pct_high,
        "ebitda_uplift_eur_mid": l.ebitda_uplift_eur_mid,
        "implementation_months": l.implementation_months,
        "roi_multiple": l.roi_multiple,
    }


def _ser_plan(p) -> dict:
    return {
        "company_id": p.company_id,
        "company_name": p.company_name,
        "sector": p.sector,
        "ebitda_eur": p.ebitda_eur,
        "entry_multiple": p.entry_multiple,
        "levers": [_ser_lever(l) for l in p.levers],
        "total_capex_mid_eur": p.total_capex_mid_eur,
        "total_annual_savings_mid_eur": p.total_annual_savings_mid_eur,
        "total_ebitda_uplift_mid_eur": p.total_ebitda_uplift_mid_eur,
        "milestones": [{"month": m.month, "description": m.description, "deliverable": m.deliverable} for m in p.milestones],
        "projected_esg_score_improvement": p.projected_esg_score_improvement,
        "projected_multiple_expansion": p.projected_multiple_expansion,
        "projected_exit_multiple": p.projected_exit_multiple,
        "projected_exit_ev_eur": p.projected_exit_ev_eur,
        "projected_value_creation_eur": p.projected_value_creation_eur,
        "plan_duration_months": p.plan_duration_months,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/monitor-company")
def monitor_company(req: CompanyMonitorRequest):
    """Monitor a single portfolio company's ESG KPIs."""
    engine = PEPortfolioMonitor()
    inp = _to_monitor_input(req)
    result = engine.monitor_company(inp)
    return _ser_company_result(result)


@router.post("/monitor-portfolio")
def monitor_portfolio(req: PortfolioMonitorRequest):
    """Monitor all portfolio companies with aggregate summary."""
    engine = PEPortfolioMonitor()
    companies = [_to_monitor_input(c) for c in req.companies]
    summary = engine.monitor_portfolio(req.fund_id, companies)
    return {
        "fund_id": summary.fund_id,
        "total_companies": summary.total_companies,
        "reporting_period": summary.reporting_period,
        "portfolio_green_pct": summary.portfolio_green_pct,
        "portfolio_amber_pct": summary.portfolio_amber_pct,
        "portfolio_red_pct": summary.portfolio_red_pct,
        "worst_performing": summary.worst_performing,
        "best_performing": summary.best_performing,
        "aggregate_kpis": summary.aggregate_kpis,
        "company_results": [_ser_company_result(r) for r in summary.company_results],
    }


@router.post("/value-creation-plan")
def value_creation_plan(req: ValueCreationRequest):
    """Generate ESG value creation plan for a portfolio company."""
    engine = PEValueCreationEngine()
    plan = engine.generate_plan(
        company_id=req.company_id,
        company_name=req.company_name,
        sector=req.sector,
        ebitda_eur=req.ebitda_eur,
        entry_multiple=req.entry_multiple,
        current_esg_score=req.current_esg_score,
        revenue_eur=req.revenue_eur,
    )
    return _ser_plan(plan)


@router.get("/kpi-template")
def get_kpi_template():
    """Return ILPA-aligned KPI collection template."""
    engine = PEPortfolioMonitor()
    return {"kpis": engine.get_kpi_template()}


@router.get("/sector-levers")
def get_sector_levers(sector: str = Query("Technology")):
    """Return available ESG improvement levers for a sector."""
    engine = PEValueCreationEngine()
    return {
        "sector": sector,
        "levers": engine.get_sector_levers(sector),
        "available_sectors": engine.get_available_sectors(),
    }


# ---------------------------------------------------------------------------
# DB-Powered Endpoints  (pe_portfolio_companies)
# ---------------------------------------------------------------------------

def _get_pe_db():
    """Lazy-load PEDBService with DB engine."""
    from services.pe_db_service import PEDBService
    from db.base import engine as db_engine
    return PEDBService(db_engine)


class PortfolioCompanyCreateRequest(BaseModel):
    """Create a portfolio company record in pe_portfolio_companies."""
    deal_id: Optional[str] = None
    company_name: str
    sector: str = "Other"
    country: str = "US"
    fund_id: str = ""
    investment_date: Optional[date] = None
    equity_invested_eur: float = Field(0, ge=0)
    current_nav_eur: float = Field(0, ge=0)
    ownership_pct: float = Field(0, ge=0, le=100)
    board_seats: int = Field(0, ge=0)
    esg_score_entry: Optional[float] = None
    esg_score_current: Optional[float] = None
    sdg_alignment: list[int] = Field(default_factory=list)


class PortfolioCompanyUpdateRequest(BaseModel):
    """Partial update for a portfolio company."""
    current_nav_eur: Optional[float] = None
    esg_score_current: Optional[float] = None
    ownership_pct: Optional[float] = None
    board_seats: Optional[int] = None
    sdg_alignment: Optional[list[int]] = None
    status: Optional[str] = None


class ExitRequest(BaseModel):
    """Record an exit event."""
    exit_date: date
    exit_proceeds_eur: float = Field(0, ge=0)


@router.post("/db/companies", summary="Create portfolio company in DB")
def db_create_company(req: PortfolioCompanyCreateRequest) -> Dict[str, Any]:
    """Insert a new portfolio company into pe_portfolio_companies."""
    svc = _get_pe_db()
    data = req.model_dump()
    # Convert date to string for DB
    if data.get("investment_date"):
        data["investment_date"] = data["investment_date"].isoformat()
    return svc.create_portfolio_company(data)


@router.get("/db/companies", summary="List portfolio companies from DB")
def db_list_companies(
    fund_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """List portfolio companies with optional fund/status filters."""
    svc = _get_pe_db()
    companies = svc.list_portfolio_companies(fund_id=fund_id, status=status)
    return {"count": len(companies), "companies": companies}


@router.patch("/db/companies/{company_id}", summary="Update portfolio company")
def db_update_company(company_id: str, req: PortfolioCompanyUpdateRequest) -> Dict[str, Any]:
    """Partial update for a portfolio company (NAV, ESG score, etc.)."""
    svc = _get_pe_db()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    result = svc.update_portfolio_company(company_id, updates)
    if not result:
        raise HTTPException(404, f"Portfolio company {company_id} not found")
    return result


@router.post("/db/companies/{company_id}/exit", summary="Record portfolio company exit")
def db_record_exit(company_id: str, req: ExitRequest) -> Dict[str, Any]:
    """Record an exit event — sets status=exited, exit_date, exit_proceeds."""
    svc = _get_pe_db()
    result = svc.record_exit(
        company_id=company_id,
        exit_date=req.exit_date.isoformat(),
        exit_proceeds_eur=req.exit_proceeds_eur,
    )
    if not result:
        raise HTTPException(404, f"Portfolio company {company_id} not found")
    return result


@router.get("/db/summary", summary="Portfolio summary with TVPI/DPI/RVPI")
def db_portfolio_summary(
    fund_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Aggregate portfolio summary: invested, NAV, exits, TVPI, DPI, RVPI."""
    svc = _get_pe_db()
    return svc.portfolio_summary(fund_id=fund_id)
