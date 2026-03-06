"""Project Finance API — DSCR / LLCR / IRR / PPA calculations."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from schemas.project_finance import (
    ProjectFinanceRequest,
    ProjectFinanceResponse,
    CashFlowRowOut,
    SaveProjectFinanceRequest,
)
from services.project_finance_engine import (
    ProjectFinanceInputs,
    project_finance_engine,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/project-finance", tags=["Project Finance"])


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def _row_to_out(row) -> CashFlowRowOut:
    return CashFlowRowOut(
        year=row.year,
        generation_mwh=float(row.generation_mwh),
        ppa_revenue=float(row.ppa_revenue),
        etc_revenue=float(row.etc_revenue),
        gross_revenue=float(row.gross_revenue),
        opex=float(row.opex),
        ebitda=float(row.ebitda),
        depreciation=float(row.depreciation),
        ebit=float(row.ebit),
        tax=float(row.tax),
        noi=float(row.noi),
        debt_service=float(row.debt_service),
        dscr=float(row.dscr),
        equity_cash_flow=float(row.equity_cash_flow),
        outstanding_debt=float(row.outstanding_debt),
    )


def _result_to_response(result) -> ProjectFinanceResponse:
    if not result.data_available:
        return ProjectFinanceResponse(
            asset_name=result.asset_name,
            inputs_summary=result.inputs_summary or {},
            year_by_year=[],
            dscr_by_year=[],
            min_dscr=0.0,
            avg_dscr=0.0,
            llcr=0.0,
            plcr=0.0,
            equity_irr_pct=0.0,
            dsra_recommendation_months=0,
            is_bankable=False,
            total_debt_usd=0.0,
            total_equity_usd=0.0,
            stress_dscr_by_year=[],
            stress_min_dscr=0.0,
            stress_is_bankable=False,
            stress_equity_irr_pct=0.0,
            stress_year_by_year=[],
            data_available=False,
            error_message=result.error_message,
        )

    return ProjectFinanceResponse(
        asset_name=result.asset_name,
        inputs_summary=result.inputs_summary,
        year_by_year=[_row_to_out(r) for r in result.year_by_year],
        dscr_by_year=[float(d) for d in result.dscr_by_year],
        min_dscr=float(result.min_dscr),
        avg_dscr=float(result.avg_dscr),
        llcr=float(result.llcr),
        plcr=float(result.plcr),
        equity_irr_pct=float(result.equity_irr_pct),
        dsra_recommendation_months=result.dsra_recommendation_months,
        is_bankable=result.is_bankable,
        total_debt_usd=float(result.total_debt_usd),
        total_equity_usd=float(result.total_equity_usd),
        stress_dscr_by_year=[float(d) for d in result.stress_dscr_by_year],
        stress_min_dscr=float(result.stress_min_dscr),
        stress_is_bankable=result.stress_is_bankable,
        stress_equity_irr_pct=float(result.stress_equity_irr_pct),
        stress_year_by_year=[_row_to_out(r) for r in result.stress_year_by_year],
        etc_irr_delta_pct=float(result.etc_irr_delta_pct) if result.etc_irr_delta_pct is not None else None,
        etc_dscr_delta=float(result.etc_dscr_delta) if result.etc_dscr_delta is not None else None,
        data_available=True,
    )


# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────
@router.post("/calculate", response_model=ProjectFinanceResponse, summary="Run project finance model (no DB write)")
async def calculate_project_finance(request: ProjectFinanceRequest):
    """
    Compute DSCR, LLCR, PLCR, Equity IRR, DSRA sizing for a renewable energy project.
    Returns both P50 (base case) and P90 (stress case) results.
    """
    try:
        inputs = ProjectFinanceInputs(
            asset_name=request.asset_name,
            total_capex_usd=request.total_capex_usd,
            debt_equity_ratio=request.debt_equity_ratio,
            loan_tenor_years=request.loan_tenor_years,
            interest_rate_pct=request.interest_rate_pct,
            grace_period_months=request.grace_period_months,
            ppa_price_usd_mwh=request.ppa_price_usd_mwh,
            ppa_tenor_years=request.ppa_tenor_years,
            price_escalation_pct=request.price_escalation_pct,
            capacity_mw=request.capacity_mw,
            capacity_factor_p50=request.capacity_factor_p50,
            capacity_factor_p90=request.capacity_factor_p90,
            curtailment_pct=request.curtailment_pct,
            opex_usd_year=request.opex_usd_year,
            include_etc_revenue=request.include_etc_revenue,
            etc_price_usd_tco2=request.etc_price_usd_tco2,
            annual_etc_tonnes=request.annual_etc_tonnes,
            opex_escalation_pct=request.opex_escalation_pct,
            project_life_years=request.project_life_years,
            discount_rate_pct=request.discount_rate_pct,
            tax_rate_pct=request.tax_rate_pct,
        )
        result = project_finance_engine.calculate(inputs)
        return _result_to_response(result)
    except Exception as e:
        logger.exception("Project finance calculate error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save", summary="Save project finance assessment to DB")
async def save_project_finance(request: SaveProjectFinanceRequest):
    """
    Persists a completed project finance assessment.
    Currently returns a stub ID — DB write to be wired when project_finance_assessments table exists.
    """
    # TODO: wire to DB when migration 021 is applied
    return {
        "assessment_id": str(uuid.uuid4()),
        "power_plant_id": request.power_plant_id,
        "status": "saved",
        "message": "Assessment saved (in-memory stub — DB table pending migration 021)",
    }


@router.get("/{power_plant_id}", summary="Load saved project finance assessment")
async def get_project_finance(power_plant_id: str):
    """Load the most recent project finance assessment for a power plant."""
    # TODO: query project_finance_assessments table
    raise HTTPException(
        status_code=404,
        detail=f"No saved assessment found for power plant {power_plant_id}. Run a new calculation."
    )


@router.get("/demo/sample", response_model=ProjectFinanceResponse, summary="Return demo calculation (70MW solar)")
async def get_demo_project_finance():
    """Return a pre-computed example for UI development / demo mode."""
    from decimal import Decimal
    inputs = ProjectFinanceInputs(
        asset_name="Demo Solar Project — 70 MW",
        total_capex_usd=Decimal("120000000"),
        debt_equity_ratio=Decimal("0.70"),
        loan_tenor_years=15,
        interest_rate_pct=Decimal("7.5"),
        grace_period_months=12,
        ppa_price_usd_mwh=Decimal("55"),
        ppa_tenor_years=20,
        price_escalation_pct=Decimal("2.0"),
        capacity_mw=Decimal("70"),
        capacity_factor_p50=Decimal("0.27"),
        capacity_factor_p90=Decimal("0.22"),
        curtailment_pct=Decimal("0.03"),
        opex_usd_year=Decimal("2100000"),
        include_etc_revenue=True,
        etc_price_usd_tco2=Decimal("18"),
        annual_etc_tonnes=Decimal("85000"),
    )
    result = project_finance_engine.calculate(inputs)
    return _result_to_response(result)
