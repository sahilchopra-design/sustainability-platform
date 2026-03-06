"""Pydantic v2 schemas for Project Finance API."""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ProjectFinanceRequest(BaseModel):
    asset_name: str = Field(description="Name of the project / power plant", min_length=1, max_length=200)
    total_capex_usd: Decimal = Field(description="Total capital expenditure in USD", gt=0)
    debt_equity_ratio: Decimal = Field(description="Debt fraction of total CAPEX (e.g. 0.70)", gt=0, lt=1)
    loan_tenor_years: int = Field(description="Loan tenor in years", ge=1, le=40)
    interest_rate_pct: Decimal = Field(description="Annual interest rate in percent (e.g. 7.5)", gt=0, lt=30)
    grace_period_months: int = Field(default=0, description="Interest-only grace period in months", ge=0, le=36)

    # PPA
    ppa_price_usd_mwh: Decimal = Field(description="PPA strike price in USD/MWh", gt=0)
    ppa_tenor_years: int = Field(description="PPA contract length in years", ge=1, le=30)
    price_escalation_pct: Decimal = Field(default=Decimal("2.0"), description="Annual PPA price escalation %", ge=0, lt=15)
    capacity_mw: Decimal = Field(description="Installed capacity in MW", gt=0)
    capacity_factor_p50: Decimal = Field(description="P50 capacity factor (0.01–0.99)", gt=0, lt=1)
    capacity_factor_p90: Decimal = Field(description="P90 capacity factor (stress case)", gt=0, lt=1)
    curtailment_pct: Decimal = Field(default=Decimal("0.03"), description="Curtailment fraction", ge=0, lt=0.5)
    opex_usd_year: Decimal = Field(description="Annual OPEX in USD", gt=0)

    # Carbon revenue
    include_etc_revenue: bool = Field(default=False)
    etc_price_usd_tco2: Decimal = Field(default=Decimal("0"), description="Carbon credit price USD/tCO2e", ge=0)
    annual_etc_tonnes: Decimal = Field(default=Decimal("0"), description="Annual carbon credits generated (tCO2e)", ge=0)

    # Optional overrides
    opex_escalation_pct: Decimal = Field(default=Decimal("2.0"), ge=0, lt=15)
    project_life_years: Optional[int] = Field(default=None, ge=5, le=50)
    discount_rate_pct: Decimal = Field(default=Decimal("8.0"), gt=0, lt=30)
    tax_rate_pct: Decimal = Field(default=Decimal("25.0"), ge=0, lt=60)

    @field_validator("capacity_factor_p90")
    @classmethod
    def p90_below_p50(cls, v, info):
        if "capacity_factor_p50" in (info.data or {}) and v >= info.data["capacity_factor_p50"]:
            raise ValueError("P90 capacity factor must be below P50")
        return v

    model_config = ConfigDict(json_schema_extra={"example": {
        "asset_name": "Thar Solar Phase 1",
        "total_capex_usd": 120000000,
        "debt_equity_ratio": 0.70,
        "loan_tenor_years": 15,
        "interest_rate_pct": 7.5,
        "grace_period_months": 12,
        "ppa_price_usd_mwh": 55,
        "ppa_tenor_years": 20,
        "price_escalation_pct": 2.0,
        "capacity_mw": 70,
        "capacity_factor_p50": 0.27,
        "capacity_factor_p90": 0.22,
        "curtailment_pct": 0.03,
        "opex_usd_year": 2100000,
        "include_etc_revenue": True,
        "etc_price_usd_tco2": 18,
        "annual_etc_tonnes": 85000,
    }})


class CashFlowRowOut(BaseModel):
    year: int
    generation_mwh: float
    ppa_revenue: float
    etc_revenue: float
    gross_revenue: float
    opex: float
    ebitda: float
    depreciation: float
    ebit: float
    tax: float
    noi: float
    debt_service: float
    dscr: float
    equity_cash_flow: float
    outstanding_debt: float


class ProjectFinanceResponse(BaseModel):
    asset_name: str
    inputs_summary: dict

    # Base case (P50)
    year_by_year: List[CashFlowRowOut]
    dscr_by_year: List[float]
    min_dscr: float
    avg_dscr: float
    llcr: float
    plcr: float
    equity_irr_pct: float
    dsra_recommendation_months: int
    is_bankable: bool
    total_debt_usd: float
    total_equity_usd: float

    # Stress case (P90)
    stress_dscr_by_year: List[float]
    stress_min_dscr: float
    stress_is_bankable: bool
    stress_equity_irr_pct: float
    stress_year_by_year: List[CashFlowRowOut]

    # ETC delta
    etc_irr_delta_pct: Optional[float] = None
    etc_dscr_delta: Optional[float] = None

    data_available: bool = True
    error_message: Optional[str] = None


class SaveProjectFinanceRequest(BaseModel):
    power_plant_id: str = Field(description="FK to power_plant_assets.id", min_length=1)
    inputs: ProjectFinanceRequest
    result: ProjectFinanceResponse
    notes: Optional[str] = None
