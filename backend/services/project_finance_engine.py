"""
Project Finance Engine — DSCR / LLCR / PLCR / IRR / PPA modelling
IFRS 9 ECL-compatible; Decimal arithmetic throughout; P50/P90 stress case support.

Key metrics:
  DSCR  = Net Operating Income / Annual Debt Service  (target >= 1.25x)
  LLCR  = NPV(NOI over loan life) / Outstanding Debt  (target >= 1.30x)
  PLCR  = NPV(NOI over project life) / Outstanding Debt
  DSRA  = Debt Service Reserve Account sizing (months)
  IRR   = Equity Internal Rate of Return (post-tax)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Use 20-digit precision for financial calculations
getcontext().prec = 20

# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────
BANKABILITY_DSCR_THRESHOLD = Decimal("1.25")
LLCR_TARGET = Decimal("1.30")
TAX_RATE = Decimal("0.25")           # default corporate tax rate
NGFS_CARBON_PRICE_ESCALATION = Decimal("0.05")  # 5% pa for NZE scenario
DEFAULT_DISCOUNT_RATE = Decimal("0.08")

DSRA_THRESHOLDS = [
    (Decimal("1.30"), 6),   # min_dscr < 1.30 → 6 months DSRA
    (Decimal("1.40"), 3),   # min_dscr < 1.40 → 3 months DSRA
]


# ─────────────────────────────────────────────────────────
# Input / Output Dataclasses
# ─────────────────────────────────────────────────────────
@dataclass
class ProjectFinanceInputs:
    asset_name: str
    total_capex_usd: Decimal
    debt_equity_ratio: Decimal       # 0.70 = 70% debt
    loan_tenor_years: int
    interest_rate_pct: Decimal       # e.g. Decimal("7.5") for 7.5%
    grace_period_months: int         # months of interest-only period

    # PPA parameters
    ppa_price_usd_mwh: Decimal
    ppa_tenor_years: int
    price_escalation_pct: Decimal    # annual escalation, e.g. Decimal("2.0")
    capacity_mw: Decimal
    capacity_factor_p50: Decimal     # e.g. Decimal("0.35") for 35%
    capacity_factor_p90: Decimal     # conservative/stress case
    curtailment_pct: Decimal         # e.g. Decimal("0.03") for 3%
    opex_usd_year: Decimal           # base year OPEX

    # Carbon revenue
    include_etc_revenue: bool = False
    etc_price_usd_tco2: Decimal = Decimal("0")
    annual_etc_tonnes: Decimal = Decimal("0")

    # Optional overrides
    opex_escalation_pct: Decimal = Decimal("2.0")
    project_life_years: Optional[int] = None  # defaults to loan_tenor_years + 5
    discount_rate_pct: Decimal = Decimal("8.0")
    tax_rate_pct: Decimal = Decimal("25.0")


@dataclass
class CashFlowRow:
    year: int
    generation_mwh: Decimal
    ppa_revenue: Decimal
    etc_revenue: Decimal
    gross_revenue: Decimal
    opex: Decimal
    ebitda: Decimal
    depreciation: Decimal
    ebit: Decimal
    tax: Decimal
    noi: Decimal               # Net Operating Income (post-tax)
    debt_service: Decimal
    dscr: Decimal
    equity_cash_flow: Decimal
    outstanding_debt: Decimal


@dataclass
class ProjectFinanceResult:
    asset_name: str
    inputs_summary: dict

    # Year-by-year
    year_by_year: List[CashFlowRow] = field(default_factory=list)
    dscr_by_year: List[Decimal] = field(default_factory=list)

    # Base case metrics (P50)
    min_dscr: Decimal = Decimal("0")
    avg_dscr: Decimal = Decimal("0")
    llcr: Decimal = Decimal("0")
    plcr: Decimal = Decimal("0")
    equity_irr_pct: Decimal = Decimal("0")
    dsra_recommendation_months: int = 0
    is_bankable: bool = False
    total_debt_usd: Decimal = Decimal("0")
    total_equity_usd: Decimal = Decimal("0")

    # Stress case (P90)
    stress_year_by_year: List[CashFlowRow] = field(default_factory=list)
    stress_dscr_by_year: List[Decimal] = field(default_factory=list)
    stress_min_dscr: Decimal = Decimal("0")
    stress_is_bankable: bool = False
    stress_equity_irr_pct: Decimal = Decimal("0")

    # ETC delta (only populated when include_etc_revenue=True)
    etc_irr_delta_pct: Optional[Decimal] = None
    etc_dscr_delta: Optional[Decimal] = None

    data_available: bool = True
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────
def _to_dec(v) -> Decimal:
    return Decimal(str(v))


def _npv(rate: Decimal, cash_flows: List[Decimal]) -> Decimal:
    """Calculate Net Present Value of a cash flow series."""
    total = Decimal("0")
    for t, cf in enumerate(cash_flows, start=1):
        total += cf / ((1 + rate) ** t)
    return total


def _irr(cash_flows: List[Decimal], guess: float = 0.10, iterations: int = 200) -> Optional[Decimal]:
    """Newton-Raphson IRR solver on Decimal cash flows."""
    rate = _to_dec(guess)
    for _ in range(iterations):
        npv = Decimal("0")
        dnpv = Decimal("0")
        for t, cf in enumerate(cash_flows):
            if t == 0:
                npv += cf
            else:
                denom = (1 + rate) ** t
                npv += cf / denom
                dnpv -= _to_dec(t) * cf / ((1 + rate) ** (t + 1))
        if abs(dnpv) < Decimal("1e-10"):
            break
        rate = rate - npv / dnpv
        if abs(npv) < Decimal("0.01"):
            break
    return rate * 100  # return as percentage


def _annuity_payment(principal: Decimal, rate: Decimal, n: int) -> Decimal:
    """Standard annuity formula: P * r / (1 - (1+r)^-n)"""
    if rate == Decimal("0"):
        return principal / n
    factor = rate / (1 - (1 + rate) ** (-n))
    return principal * factor


# ─────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────
class ProjectFinanceEngine:
    """
    Computes project finance metrics for renewable energy projects.
    All intermediate calculations use Decimal for precision.
    """

    def calculate(self, inputs: ProjectFinanceInputs) -> ProjectFinanceResult:
        try:
            result = self._run_calculation(inputs)
            return result
        except Exception as e:
            logger.exception("Project finance calculation failed: %s", e)
            return ProjectFinanceResult(
                asset_name=inputs.asset_name,
                inputs_summary={},
                data_available=False,
                error_message=str(e),
            )

    def _run_calculation(self, inp: ProjectFinanceInputs) -> ProjectFinanceResult:
        # Normalise inputs
        interest_rate = inp.interest_rate_pct / 100
        discount_rate = inp.discount_rate_pct / 100
        tax_rate = inp.tax_rate_pct / 100
        escalation = inp.price_escalation_pct / 100
        opex_esc = inp.opex_escalation_pct / 100
        project_life = inp.project_life_years or (inp.loan_tenor_years + 5)

        # Loan sizing
        debt_amount = (inp.total_capex_usd * inp.debt_equity_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        equity_amount = (inp.total_capex_usd - debt_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        grace_years = Decimal(str(inp.grace_period_months)) / 12

        # Annual debt service (standard annuity, post-grace)
        amort_years = inp.loan_tenor_years - int(inp.grace_period_months / 12)
        if amort_years <= 0:
            amort_years = inp.loan_tenor_years
        annual_ds = _annuity_payment(debt_amount, interest_rate, amort_years)

        # Depreciation (straight-line over project life)
        depreciation = (inp.total_capex_usd / project_life).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Base case (P50) cash flows
        base_rows, base_equity_cfs = self._build_cashflows(
            inp, debt_amount, equity_amount, annual_ds, depreciation,
            inp.capacity_factor_p50, interest_rate, tax_rate, escalation, opex_esc, project_life,
        )

        # Stress case (P90) — lower generation
        stress_rows, stress_equity_cfs = self._build_cashflows(
            inp, debt_amount, equity_amount, annual_ds, depreciation,
            inp.capacity_factor_p90, interest_rate, tax_rate, escalation, opex_esc, project_life,
        )

        base_dscrs = [r.dscr for r in base_rows if r.year <= inp.loan_tenor_years and r.debt_service > 0]
        stress_dscrs = [r.dscr for r in stress_rows if r.year <= inp.loan_tenor_years and r.debt_service > 0]

        min_dscr = min(base_dscrs) if base_dscrs else Decimal("0")
        avg_dscr = (sum(base_dscrs) / len(base_dscrs)).quantize(Decimal("0.01")) if base_dscrs else Decimal("0")
        stress_min = min(stress_dscrs) if stress_dscrs else Decimal("0")

        # LLCR — PV of NOI over loan life / debt
        loan_noi = [r.noi for r in base_rows if r.year <= inp.loan_tenor_years]
        llcr = _npv(discount_rate, loan_noi) / debt_amount if debt_amount > 0 else Decimal("0")

        # PLCR — PV of NOI over project life / debt
        project_noi = [r.noi for r in base_rows]
        plcr = _npv(discount_rate, project_noi) / debt_amount if debt_amount > 0 else Decimal("0")

        # DSRA sizing
        dsra_months = 0
        for threshold, months in DSRA_THRESHOLDS:
            if min_dscr < threshold:
                dsra_months = months
                break

        # Equity IRR — base and stress
        base_equity_irr = _irr([-equity_amount] + base_equity_cfs)
        stress_equity_irr = _irr([-equity_amount] + stress_equity_cfs)

        # ETC delta — compare with and without carbon revenue
        etc_irr_delta = None
        etc_dscr_delta = None
        if inp.include_etc_revenue and inp.etc_price_usd_tco2 > 0:
            # Run without ETC
            inp_no_etc = ProjectFinanceInputs(**{**inp.__dict__, "include_etc_revenue": False})
            no_etc_rows, no_etc_equity = self._build_cashflows(
                inp_no_etc, debt_amount, equity_amount, annual_ds, depreciation,
                inp.capacity_factor_p50, interest_rate, tax_rate, escalation, opex_esc, project_life,
            )
            no_etc_irr = _irr([-equity_amount] + no_etc_equity)
            no_etc_dscrs = [r.dscr for r in no_etc_rows if r.year <= inp.loan_tenor_years and r.debt_service > 0]
            no_etc_min = min(no_etc_dscrs) if no_etc_dscrs else Decimal("0")
            etc_irr_delta = (base_equity_irr - no_etc_irr).quantize(Decimal("0.01")) if base_equity_irr and no_etc_irr else None
            etc_dscr_delta = (min_dscr - no_etc_min).quantize(Decimal("0.01"))

        return ProjectFinanceResult(
            asset_name=inp.asset_name,
            inputs_summary={
                "total_capex_usd": float(inp.total_capex_usd),
                "debt_equity_ratio": float(inp.debt_equity_ratio),
                "loan_tenor_years": inp.loan_tenor_years,
                "interest_rate_pct": float(inp.interest_rate_pct),
                "ppa_price_usd_mwh": float(inp.ppa_price_usd_mwh),
                "capacity_mw": float(inp.capacity_mw),
                "capacity_factor_p50": float(inp.capacity_factor_p50),
                "capacity_factor_p90": float(inp.capacity_factor_p90),
            },
            year_by_year=base_rows,
            dscr_by_year=[r.dscr for r in base_rows],
            min_dscr=min_dscr.quantize(Decimal("0.01")),
            avg_dscr=avg_dscr,
            llcr=llcr.quantize(Decimal("0.01")),
            plcr=plcr.quantize(Decimal("0.01")),
            equity_irr_pct=(base_equity_irr or Decimal("0")).quantize(Decimal("0.01")),
            dsra_recommendation_months=dsra_months,
            is_bankable=min_dscr >= BANKABILITY_DSCR_THRESHOLD,
            total_debt_usd=debt_amount,
            total_equity_usd=equity_amount,
            stress_year_by_year=stress_rows,
            stress_dscr_by_year=[r.dscr for r in stress_rows],
            stress_min_dscr=stress_min.quantize(Decimal("0.01")),
            stress_is_bankable=stress_min >= BANKABILITY_DSCR_THRESHOLD,
            stress_equity_irr_pct=(stress_equity_irr or Decimal("0")).quantize(Decimal("0.01")),
            etc_irr_delta_pct=etc_irr_delta,
            etc_dscr_delta=etc_dscr_delta,
            data_available=True,
        )

    def _build_cashflows(
        self,
        inp: ProjectFinanceInputs,
        debt_amount: Decimal,
        equity_amount: Decimal,
        annual_ds: Decimal,
        depreciation: Decimal,
        capacity_factor: Decimal,
        interest_rate: Decimal,
        tax_rate: Decimal,
        escalation: Decimal,
        opex_esc: Decimal,
        project_life: int,
    ) -> Tuple[List[CashFlowRow], List[Decimal]]:
        rows: List[CashFlowRow] = []
        equity_cfs: List[Decimal] = []
        grace_months = inp.grace_period_months
        outstanding_debt = debt_amount

        annual_generation_base = (
            inp.capacity_mw * 1000 * capacity_factor * 8760
            * (1 - inp.curtailment_pct)
        ).quantize(Decimal("0.01"))

        for year in range(1, project_life + 1):
            t = year - 1  # for escalation (year 1 = base)

            # Generation
            gen_mwh = annual_generation_base  # no degradation for simplicity

            # PPA revenue (escalate only within PPA tenor, merchant after)
            if year <= inp.ppa_tenor_years:
                ppa_price_t = inp.ppa_price_usd_mwh * ((1 + escalation) ** t)
            else:
                ppa_price_t = inp.ppa_price_usd_mwh * ((1 + escalation) ** (inp.ppa_tenor_years - 1))
            ppa_revenue = (gen_mwh * ppa_price_t).quantize(Decimal("0.01"))

            # Carbon revenue (ETC/carbon credit)
            if inp.include_etc_revenue and inp.etc_price_usd_tco2 > 0:
                etc_price_t = inp.etc_price_usd_tco2 * ((1 + NGFS_CARBON_PRICE_ESCALATION) ** t)
                etc_rev = (inp.annual_etc_tonnes * etc_price_t).quantize(Decimal("0.01"))
            else:
                etc_rev = Decimal("0")

            gross_revenue = ppa_revenue + etc_rev

            # OPEX (escalating)
            opex = (inp.opex_usd_year * ((1 + opex_esc) ** t)).quantize(Decimal("0.01"))

            ebitda = gross_revenue - opex

            # Depreciation and EBIT
            ebit = ebitda - depreciation

            # Tax (on EBIT, no loss carry-forward for simplicity)
            tax = max(ebit * tax_rate, Decimal("0")).quantize(Decimal("0.01"))

            # NOI (post-tax)
            noi = ebitda - tax  # ebitda - taxes; depreciation not a cash item

            # Debt service
            in_grace = (year * 12) <= grace_months
            if year > inp.loan_tenor_years:
                ds = Decimal("0")
            elif in_grace:
                # Interest only during grace
                ds = (outstanding_debt * interest_rate).quantize(Decimal("0.01"))
                outstanding_debt = outstanding_debt  # no principal payment
            else:
                ds = annual_ds.quantize(Decimal("0.01"))
                # Track outstanding debt (principal portion)
                interest_portion = (outstanding_debt * interest_rate).quantize(Decimal("0.01"))
                principal_portion = max(ds - interest_portion, Decimal("0"))
                outstanding_debt = max(outstanding_debt - principal_portion, Decimal("0"))

            # DSCR
            dscr = (noi / ds).quantize(Decimal("0.01")) if ds > 0 else Decimal("0")

            # Equity cash flow
            eq_cf = noi - ds

            rows.append(CashFlowRow(
                year=year,
                generation_mwh=gen_mwh,
                ppa_revenue=ppa_revenue,
                etc_revenue=etc_rev,
                gross_revenue=gross_revenue,
                opex=opex,
                ebitda=ebitda,
                depreciation=depreciation,
                ebit=ebit,
                tax=tax,
                noi=noi,
                debt_service=ds,
                dscr=dscr,
                equity_cash_flow=eq_cf,
                outstanding_debt=outstanding_debt,
            ))
            equity_cfs.append(eq_cf)

        return rows, equity_cfs


# Module-level singleton
project_finance_engine = ProjectFinanceEngine()
