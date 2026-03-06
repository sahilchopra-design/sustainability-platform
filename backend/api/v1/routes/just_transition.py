"""
Just Transition + ETM Routes
Routes: /api/v1/just-transition/*

Aligned with:
  ILO Just Transition Guidelines (2015)
  Climate Investment Funds (CIF) Just Transition Framework
  IRENA World Energy Transitions Outlook 2023
  ADB/AIIB/Citi Energy Transition Mechanism (ETM) Framework 2022
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.just_transition_calculator import (
    JustTransitionInput,
    ETMInput,
    calculate_just_transition,
    calculate_etm,
    EMPLOYMENT_MULTIPLIERS,
    GREEN_JOBS_PER_MW,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/just-transition",
    tags=["Just Transition + ETM"],
)


class JustTransitionRequest(BaseModel):
    region_name: str = "Hunter Valley, Australia"
    country_income_group: str = "HIC"
    fossil_sector: str = "coal_mining"
    direct_fossil_jobs: int = 5000
    capacity_mw: Optional[float] = None
    transition_years: int = 10
    planned_re_mw: float = 1500.0
    re_technology: str = "solar_pv"
    planned_ee_mw_equiv: float = 200.0
    planned_grid_mw: float = 500.0
    planned_h2_mw: float = 0.0
    income_support_years: int = 3
    retraining_coverage_pct: float = 0.75
    community_investment_included: bool = True
    community_dependency_pct: float = 0.6
    just_transition_fund_usd: float = 0.0


class ETMRequest(BaseModel):
    plant_name: str = "Hazelwood Power Station"
    plant_country: str = "Australia"
    capacity_mw: float = 1600.0
    remaining_useful_life_years: int = 15
    early_retirement_year: int = 2030
    current_year: int = 2024
    outstanding_debt_usd_m: float = 800.0
    equity_book_value_usd_m: float = 200.0
    offtake_tariff_usd_per_mwh: float = 65.0
    capacity_factor_pct: float = 60.0
    incumbent_wacc_pct: float = 12.0
    etm_refinance_rate_pct: float = 4.5
    etm_tranche_pct: float = 0.6
    re_replacement_mw: float = 2000.0
    re_capex_usd_per_mw: float = 800_000.0
    re_lcoe_usd_per_mwh: float = 35.0


@router.post("/calculate")
def compute_just_transition(payload: JustTransitionRequest):
    """Compute just transition employment, social cost and financing analysis."""
    try:
        inp = JustTransitionInput(**payload.dict())
        result = calculate_just_transition(inp)
        return {
            "region_name": result.region_name,
            "employment": {
                "direct_displaced": result.direct_displaced_jobs,
                "total_displaced": result.total_displaced_jobs,
                "green_jobs_created": result.green_jobs_created,
                "net_delta": result.net_employment_delta,
                "jobs_gap": result.jobs_gap,
            },
            "social_costs_usd": {
                "income_support": result.income_support_cost_usd,
                "retraining": result.retraining_cost_usd,
                "community_investment": result.community_investment_usd,
                "total": result.total_social_cost_usd,
            },
            "financing": {
                "total_cost_usd": result.total_social_cost_usd,
                "fund_gap_usd": result.just_transition_fund_gap_usd,
                "cost_per_worker_usd": result.cost_per_displaced_worker_usd,
            },
            "economic_impact": {
                "annual_wage_bill_lost_usd": result.annual_wage_bill_lost_usd,
                "gdp_exposure_pct": result.gdp_exposure_pct,
            },
            "feasibility": result.transition_feasibility,
            "narrative": result.narrative,
            "annual_ramp": result.annual_green_jobs_ramp,
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/etm/calculate")
def compute_etm(payload: ETMRequest):
    """Compute ETM (Energy Transition Mechanism) financing package for early coal retirement."""
    try:
        inp = ETMInput(**payload.dict())
        result = calculate_etm(inp)
        return {
            "plant_name": result.plant_name,
            "years_early_retirement": result.years_early_retirement,
            "stranded_value": {
                "npv_lost_usd_m": result.stranded_asset_value_usd_m,
            },
            "etm_package_usd_m": {
                "debt_buyout": result.etm_debt_buyout_usd_m,
                "concessional_savings": result.concessional_savings_usd_m,
                "equity_compensation": result.equity_compensation_usd_m,
                "re_replacement_capex": result.re_replacement_capex_usd_m,
                "total": result.total_etm_cost_usd_m,
            },
            "climate_impact": {
                "avoided_co2_mt": result.avoided_co2_mt,
                "abatement_cost_usd_per_tco2": result.co2_abatement_cost_usd_per_tco2,
                "npv_saving_vs_natural_retirement_usd_m": result.npv_saving_vs_natural_retirement,
            },
            "feasibility": result.feasibility,
            "narrative": result.narrative,
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/reference-data")
def get_reference_data():
    """Return employment multipliers and green job creation factors."""
    return {
        "employment_multipliers": EMPLOYMENT_MULTIPLIERS,
        "green_jobs_per_mw": GREEN_JOBS_PER_MW,
        "sources": {
            "multipliers": "ILO Just Transition Report 2023",
            "green_jobs": "IRENA World Energy Transitions Outlook 2023",
            "social_costs": "World Bank Just Transition Framework 2022",
        },
    }
