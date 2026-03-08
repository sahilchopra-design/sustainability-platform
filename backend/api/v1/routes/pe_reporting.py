"""
PE GP/LP Reporting + Impact Framework + IRR Sensitivity Routes
================================================================
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.pe_reporting_engine import (
    PEReportingEngine,
    FundPerformanceData,
    PortfolioCompanySummary,
    LPReportInput,
)
from services.pe_impact_framework import (
    PEImpactFramework,
    CompanyImpactData,
    FundImpactInput,
)
from services.pe_irr_sensitivity import (
    PEIRRSensitivityEngine,
    IRRSensitivityInput,
    DealCashflow,
)

router = APIRouter(prefix="/api/v1/pe/reporting", tags=["PE Reporting & Impact"])

_report_engine = PEReportingEngine()
_impact_engine = PEImpactFramework()
_irr_engine = PEIRRSensitivityEngine()


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class FundPerformanceRequest(BaseModel):
    fund_id: str
    fund_name: str
    vintage_year: int
    fund_size_eur: float
    committed_capital_eur: float
    called_capital_eur: float
    distributed_capital_eur: float
    nav_eur: float
    management_fees_eur: float = 0.0
    carried_interest_eur: float = 0.0
    reporting_date: str = ""


class PortfolioCompanyRequest(BaseModel):
    company_id: str
    company_name: str
    sector: str
    invested_eur: float
    current_nav_eur: float
    ownership_pct: float
    entry_date: str
    esg_score: float = 50.0
    esg_traffic_light: str = "amber"
    carbon_intensity_tco2e_per_meur: float = 0.0


class LPReportRequest(BaseModel):
    fund_performance: FundPerformanceRequest
    portfolio_companies: list[PortfolioCompanyRequest]
    reporting_period: str
    report_type: str = "quarterly"
    sfdr_classification: str = "art8"
    include_esg_annex: bool = True


class CompanyImpactRequest(BaseModel):
    company_id: str
    company_name: str
    sector: str
    primary_sdgs: list[int] = []
    secondary_sdgs: list[int] = []
    impact_scores: dict[str, float] = {}
    jobs_created: int = 0
    beneficiaries_reached: int = 0
    co2_avoided_tonnes: float = 0.0
    renewable_mwh_generated: float = 0.0
    theory_of_change: str = ""
    additionality_evidence: str = ""
    invested_eur: float = 0.0
    current_nav_eur: float = 0.0


class FundImpactRequest(BaseModel):
    fund_id: str
    fund_name: str
    fund_strategy: str = "impact"
    sfdr_classification: str = "art9"
    companies: list[CompanyImpactRequest] = []


class IRRRequest(BaseModel):
    deal_id: str
    company_name: str
    sector: str
    entry_ev_eur: float
    entry_ebitda_eur: float
    entry_multiple: float
    equity_invested_eur: float
    net_debt_eur: float
    hold_period_years: int = 5
    ebitda_growth_pct: float = 5.0
    exit_multiple: float = 0.0
    esg_score: float = 50.0
    esg_improvement_expected: float = 0.0


class CashflowRequest(BaseModel):
    period: int
    amount_eur: float


class IRRCashflowRequest(BaseModel):
    cashflows: list[CashflowRequest]


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_fund_perf(r: FundPerformanceRequest) -> FundPerformanceData:
    return FundPerformanceData(
        fund_id=r.fund_id, fund_name=r.fund_name,
        vintage_year=r.vintage_year, fund_size_eur=r.fund_size_eur,
        committed_capital_eur=r.committed_capital_eur,
        called_capital_eur=r.called_capital_eur,
        distributed_capital_eur=r.distributed_capital_eur,
        nav_eur=r.nav_eur, management_fees_eur=r.management_fees_eur,
        carried_interest_eur=r.carried_interest_eur,
        reporting_date=r.reporting_date,
    )


def _to_portfolio_co(r: PortfolioCompanyRequest) -> PortfolioCompanySummary:
    return PortfolioCompanySummary(
        company_id=r.company_id, company_name=r.company_name,
        sector=r.sector, invested_eur=r.invested_eur,
        current_nav_eur=r.current_nav_eur, ownership_pct=r.ownership_pct,
        entry_date=r.entry_date, esg_score=r.esg_score,
        esg_traffic_light=r.esg_traffic_light,
        carbon_intensity_tco2e_per_meur=r.carbon_intensity_tco2e_per_meur,
    )


def _to_company_impact(r: CompanyImpactRequest) -> CompanyImpactData:
    return CompanyImpactData(
        company_id=r.company_id, company_name=r.company_name,
        sector=r.sector, primary_sdgs=r.primary_sdgs,
        secondary_sdgs=r.secondary_sdgs, impact_scores=r.impact_scores,
        jobs_created=r.jobs_created, beneficiaries_reached=r.beneficiaries_reached,
        co2_avoided_tonnes=r.co2_avoided_tonnes,
        renewable_mwh_generated=r.renewable_mwh_generated,
        theory_of_change=r.theory_of_change,
        additionality_evidence=r.additionality_evidence,
        invested_eur=r.invested_eur, current_nav_eur=r.current_nav_eur,
    )


def _to_irr_input(r: IRRRequest) -> IRRSensitivityInput:
    return IRRSensitivityInput(
        deal_id=r.deal_id, company_name=r.company_name,
        sector=r.sector, entry_ev_eur=r.entry_ev_eur,
        entry_ebitda_eur=r.entry_ebitda_eur, entry_multiple=r.entry_multiple,
        equity_invested_eur=r.equity_invested_eur, net_debt_eur=r.net_debt_eur,
        hold_period_years=r.hold_period_years,
        ebitda_growth_pct=r.ebitda_growth_pct,
        exit_multiple=r.exit_multiple, esg_score=r.esg_score,
        esg_improvement_expected=r.esg_improvement_expected,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _serialise_report(r):
    return {
        "fund_id": r.fund_id,
        "fund_name": r.fund_name,
        "reporting_period": r.reporting_period,
        "report_type": r.report_type,
        "fund_metrics": {
            "tvpi": r.fund_metrics.tvpi,
            "dpi": r.fund_metrics.dpi,
            "rvpi": r.fund_metrics.rvpi,
            "net_irr_pct": r.fund_metrics.net_irr_pct,
            "gross_irr_pct": r.fund_metrics.gross_irr_pct,
            "called_pct": r.fund_metrics.called_pct,
            "dry_powder_eur": r.fund_metrics.dry_powder_eur,
        },
        "portfolio_summary": r.portfolio_summary,
        "total_nav_eur": r.total_nav_eur,
        "total_invested_eur": r.total_invested_eur,
        "total_companies": r.total_companies,
        "esg_annex": _serialise_esg_annex(r.esg_annex) if r.esg_annex else None,
        "executive_summary": r.executive_summary,
        "sections": r.sections,
    }


def _serialise_esg_annex(a):
    return {
        "sfdr_classification": a.sfdr_classification,
        "sustainable_investment_pct": a.sustainable_investment_pct,
        "taxonomy_aligned_pct": a.taxonomy_aligned_pct,
        "do_no_significant_harm_pct": a.do_no_significant_harm_pct,
        "esg_score_weighted_avg": a.esg_score_weighted_avg,
        "carbon_footprint_tco2e": a.carbon_footprint_tco2e,
        "green_revenue_pct": a.green_revenue_pct,
        "pai_indicators": a.pai_indicators,
    }


def _serialise_impact_report(r):
    return {
        "fund_id": r.fund_id,
        "fund_name": r.fund_name,
        "fund_strategy": r.fund_strategy,
        "sfdr_classification": r.sfdr_classification,
        "total_companies": r.total_companies,
        "fund_impact_score": r.fund_impact_score,
        "fund_impact_rating": r.fund_impact_rating,
        "high_impact_count": r.high_impact_count,
        "medium_impact_count": r.medium_impact_count,
        "low_impact_count": r.low_impact_count,
        "total_jobs_created": r.total_jobs_created,
        "total_beneficiaries": r.total_beneficiaries,
        "total_co2_avoided_tonnes": r.total_co2_avoided_tonnes,
        "total_renewable_mwh": r.total_renewable_mwh,
        "additionality_score": r.additionality_score,
        "impact_summary": r.impact_summary,
        "company_scores": [
            {
                "company_id": s.company_id,
                "company_name": s.company_name,
                "impact_rating": s.impact_rating,
                "composite_impact_score": s.composite_impact_score,
                "dimension_scores": s.dimension_scores,
                "primary_sdgs": s.primary_sdgs,
                "sdg_names": s.sdg_names,
                "additionality_rating": s.additionality_rating,
                "impact_multiple_of_money": s.impact_multiple_of_money,
                "quantitative_metrics": s.quantitative_metrics,
            }
            for s in r.company_scores
        ],
        "sdg_contributions": [
            {
                "sdg_number": c.sdg_number,
                "sdg_name": c.sdg_name,
                "category": c.category,
                "company_count": c.company_count,
                "total_invested_eur": c.total_invested_eur,
                "pct_of_fund": c.pct_of_fund,
            }
            for c in r.sdg_contributions
        ],
    }


def _serialise_irr(r):
    def _sc(s):
        return {
            "scenario_name": s.scenario_name,
            "irr_pct": s.irr_pct,
            "moic": s.moic,
            "exit_ev_eur": s.exit_ev_eur,
            "equity_value_eur": s.equity_value_eur,
            "hold_period_years": s.hold_period_years,
        }

    return {
        "deal_id": r.deal_id,
        "company_name": r.company_name,
        "base_case": _sc(r.base_case),
        "upside_case": _sc(r.upside_case),
        "downside_case": _sc(r.downside_case),
        "esg_impact": {
            "base_irr_pct": r.esg_impact.base_irr_pct,
            "esg_adjusted_irr_pct": r.esg_impact.esg_adjusted_irr_pct,
            "irr_delta_bps": r.esg_impact.irr_delta_bps,
            "base_moic": r.esg_impact.base_moic,
            "esg_adjusted_moic": r.esg_impact.esg_adjusted_moic,
            "multiple_expansion_x": r.esg_impact.multiple_expansion_x,
            "esg_valuation_premium_pct": r.esg_impact.esg_valuation_premium_pct,
            "esg_risk_discount_pct": r.esg_impact.esg_risk_discount_pct,
        },
        "sensitivity_table": {
            "row_dimension": r.sensitivity_table.row_dimension,
            "col_dimension": r.sensitivity_table.col_dimension,
            "row_values": r.sensitivity_table.row_values,
            "col_values": r.sensitivity_table.col_values,
            "base_irr_pct": r.sensitivity_table.base_irr_pct,
            "base_moic": r.sensitivity_table.base_moic,
            "cells": [
                {
                    "row_label": c.row_label,
                    "col_label": c.col_label,
                    "irr_pct": c.irr_pct,
                    "moic": c.moic,
                    "equity_return_eur": c.equity_return_eur,
                }
                for c in r.sensitivity_table.cells
            ],
        },
        "scenarios": [_sc(s) for s in r.scenarios],
        "summary": r.summary,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/lp-report")
async def generate_lp_report(req: LPReportRequest):
    """Generate a quarterly or annual LP report."""
    inp = LPReportInput(
        fund_performance=_to_fund_perf(req.fund_performance),
        portfolio_companies=[_to_portfolio_co(c) for c in req.portfolio_companies],
        reporting_period=req.reporting_period,
        report_type=req.report_type,
        sfdr_classification=req.sfdr_classification,
        include_esg_annex=req.include_esg_annex,
    )
    result = _report_engine.generate_lp_report(inp)
    return _serialise_report(result)


@router.post("/fund-impact")
async def assess_fund_impact(req: FundImpactRequest):
    """Assess impact measurement across a fund."""
    inp = FundImpactInput(
        fund_id=req.fund_id,
        fund_name=req.fund_name,
        fund_strategy=req.fund_strategy,
        sfdr_classification=req.sfdr_classification,
        companies=[_to_company_impact(c) for c in req.companies],
    )
    result = _impact_engine.assess_fund_impact(inp)
    return _serialise_impact_report(result)


@router.post("/irr-sensitivity")
async def irr_sensitivity(req: IRRRequest):
    """Run IRR/MOIC sensitivity analysis with ESG adjustments."""
    inp = _to_irr_input(req)
    result = _irr_engine.analyse(inp)
    return _serialise_irr(result)


@router.post("/compute-irr")
async def compute_irr(req: IRRCashflowRequest):
    """Compute IRR from explicit cashflows."""
    cfs = [DealCashflow(period=c.period, amount_eur=c.amount_eur) for c in req.cashflows]
    irr = _irr_engine.compute_irr(cfs)
    return {"irr_pct": irr, "cashflow_count": len(cfs)}


@router.get("/pai-indicators")
async def get_pai_indicators():
    """Return SFDR PAI indicator reference data."""
    return {"pai_indicators": _report_engine.get_pai_indicators()}


@router.get("/sdg-definitions")
async def get_sdg_definitions():
    """Return UN SDG reference data."""
    sdgs = _impact_engine.get_sdg_definitions()
    return {
        "sdgs": [
            {"sdg_number": k, **v}
            for k, v in sdgs.items()
        ]
    }


@router.get("/impact-dimensions")
async def get_impact_dimensions():
    """Return IMP impact dimensions."""
    return {"dimensions": _impact_engine.get_impact_dimensions()}
