"""
API Routes: PE Portfolio Monitoring + Value Creation
=====================================================
POST /api/v1/pe-portfolio/monitor-company     — Single company KPI monitoring
POST /api/v1/pe-portfolio/monitor-portfolio    — Portfolio-wide monitoring
POST /api/v1/pe-portfolio/value-creation-plan  — Generate value creation plan
GET  /api/v1/pe-portfolio/kpi-template         — ILPA KPI collection template
GET  /api/v1/pe-portfolio/sector-levers        — Available ESG levers by sector
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

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
