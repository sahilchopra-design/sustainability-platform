"""
PE IRR / MOIC Sensitivity Engine
==================================
Monte Carlo + scenario-based sensitivity analysis for PE fund returns,
incorporating ESG risk adjustments to entry/exit multiples and hold periods.

References:
- CFA Institute — PE return analysis and benchmarking
- ILPA Guidance — Performance reporting (IRR, TVPI, DPI)
- Academic — "ESG and the cost of capital" (Gianfrate & Peri, 2019)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Data Classes — Input
# ---------------------------------------------------------------------------

@dataclass
class DealCashflow:
    """Single cashflow for IRR calculation."""
    period: int  # quarters from investment (0=entry)
    amount_eur: float  # negative = outflow, positive = inflow


@dataclass
class IRRSensitivityInput:
    """Input for IRR sensitivity analysis."""
    deal_id: str
    company_name: str
    sector: str
    entry_ev_eur: float
    entry_ebitda_eur: float
    entry_multiple: float
    equity_invested_eur: float
    net_debt_eur: float
    hold_period_years: int = 5
    ebitda_growth_pct: float = 5.0  # Annual EBITDA growth %
    exit_multiple: float = 0.0     # 0 = same as entry
    esg_score: float = 50.0        # 0-100 ESG score
    esg_improvement_expected: float = 0.0  # Points of improvement


# ---------------------------------------------------------------------------
# Data Classes — Output
# ---------------------------------------------------------------------------

@dataclass
class SensitivityCell:
    """Single cell in a sensitivity table."""
    row_label: str
    col_label: str
    row_value: float
    col_value: float
    irr_pct: float
    moic: float
    equity_return_eur: float


@dataclass
class SensitivityTable:
    """2D sensitivity grid."""
    row_dimension: str  # e.g. "exit_multiple"
    col_dimension: str  # e.g. "ebitda_growth_pct"
    row_values: list[float]
    col_values: list[float]
    cells: list[SensitivityCell]
    base_irr_pct: float
    base_moic: float


@dataclass
class ESGImpactAnalysis:
    """ESG impact on returns."""
    base_irr_pct: float
    esg_adjusted_irr_pct: float
    irr_delta_bps: int  # basis points
    base_moic: float
    esg_adjusted_moic: float
    multiple_expansion_x: float
    esg_valuation_premium_pct: float
    esg_risk_discount_pct: float


@dataclass
class ScenarioResult:
    """Result for a single scenario."""
    scenario_name: str
    irr_pct: float
    moic: float
    exit_ev_eur: float
    equity_value_eur: float
    hold_period_years: int


@dataclass
class IRRAnalysisResult:
    """Complete IRR/MOIC analysis output."""
    deal_id: str
    company_name: str
    base_case: ScenarioResult
    upside_case: ScenarioResult
    downside_case: ScenarioResult
    esg_impact: ESGImpactAnalysis
    sensitivity_table: SensitivityTable
    scenarios: list[ScenarioResult]
    summary: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ESG multiple expansion: basis points per ESG score point improvement
ESG_BPS_PER_POINT: int = 15  # 0.15% multiple expansion per ESG score point

# ESG discount rate adjustment: basis points per 10 ESG score points below 50
ESG_RISK_BPS_PER_10: int = 25  # higher cost of equity for low ESG


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PEIRRSensitivityEngine:
    """IRR/MOIC sensitivity analysis with ESG adjustments."""

    def analyse(self, inp: IRRSensitivityInput) -> IRRAnalysisResult:
        """Run complete IRR sensitivity analysis."""
        exit_mult = inp.exit_multiple if inp.exit_multiple > 0 else inp.entry_multiple

        # 1. Base case
        base = self._compute_scenario(
            "Base Case", inp.equity_invested_eur, inp.entry_ebitda_eur,
            inp.ebitda_growth_pct, exit_mult, inp.net_debt_eur,
            inp.hold_period_years,
        )

        # 2. Upside (+2x multiple, +2% growth)
        upside = self._compute_scenario(
            "Upside", inp.equity_invested_eur, inp.entry_ebitda_eur,
            inp.ebitda_growth_pct + 2.0, exit_mult + 2.0, inp.net_debt_eur,
            inp.hold_period_years,
        )

        # 3. Downside (-2x multiple, -2% growth)
        downside = self._compute_scenario(
            "Downside", inp.equity_invested_eur, inp.entry_ebitda_eur,
            max(0, inp.ebitda_growth_pct - 2.0), max(4.0, exit_mult - 2.0),
            inp.net_debt_eur, inp.hold_period_years,
        )

        # 4. ESG impact analysis
        esg = self._esg_impact(
            inp.equity_invested_eur, inp.entry_ebitda_eur,
            inp.ebitda_growth_pct, exit_mult, inp.net_debt_eur,
            inp.hold_period_years, inp.esg_score, inp.esg_improvement_expected,
        )

        # 5. Sensitivity table: exit multiple vs EBITDA growth
        sensitivity = self._build_sensitivity_table(
            inp.equity_invested_eur, inp.entry_ebitda_eur,
            inp.ebitda_growth_pct, exit_mult, inp.net_debt_eur,
            inp.hold_period_years,
        )

        scenarios = [base, upside, downside]

        summary = (
            f"{inp.company_name} — Base IRR: {base.irr_pct}% / MOIC: {base.moic}x. "
            f"Upside: {upside.irr_pct}% / {upside.moic}x. "
            f"Downside: {downside.irr_pct}% / {downside.moic}x. "
            f"ESG adj. IRR: {esg.esg_adjusted_irr_pct}% ({esg.irr_delta_bps:+d}bps)."
        )

        return IRRAnalysisResult(
            deal_id=inp.deal_id,
            company_name=inp.company_name,
            base_case=base,
            upside_case=upside,
            downside_case=downside,
            esg_impact=esg,
            sensitivity_table=sensitivity,
            scenarios=scenarios,
            summary=summary,
        )

    def compute_irr(self, cashflows: list[DealCashflow]) -> float:
        """Compute IRR from a series of cashflows using Newton's method."""
        if not cashflows:
            return 0.0

        amounts = [(cf.period, cf.amount_eur) for cf in cashflows]

        # Newton-Raphson IRR
        rate = 0.10  # initial guess
        for _ in range(200):
            npv = sum(a / (1 + rate) ** (p / 4) for p, a in amounts)
            dnpv = sum(-p / 4 * a / (1 + rate) ** (p / 4 + 1) for p, a in amounts)
            if abs(dnpv) < 1e-12:
                break
            new_rate = rate - npv / dnpv
            if abs(new_rate - rate) < 1e-8:
                rate = new_rate
                break
            rate = new_rate

        return round(rate * 100, 2)  # Annualised %

    # -------------------------------------------------------------------
    # Scenario Computation
    # -------------------------------------------------------------------

    def _compute_scenario(
        self, name: str, equity: float, entry_ebitda: float,
        growth_pct: float, exit_mult: float, debt: float, years: int,
    ) -> ScenarioResult:
        """Compute IRR and MOIC for a single scenario."""
        exit_ebitda = entry_ebitda * (1 + growth_pct / 100) ** years
        exit_ev = exit_ebitda * exit_mult
        equity_value = exit_ev - debt
        moic = round(equity_value / equity, 2) if equity > 0 else 0

        # Simplified IRR from MOIC
        irr = round((moic ** (1 / years) - 1) * 100, 1) if moic > 0 and years > 0 else 0

        return ScenarioResult(
            scenario_name=name,
            irr_pct=irr,
            moic=moic,
            exit_ev_eur=round(exit_ev, 2),
            equity_value_eur=round(equity_value, 2),
            hold_period_years=years,
        )

    # -------------------------------------------------------------------
    # ESG Impact
    # -------------------------------------------------------------------

    def _esg_impact(
        self, equity: float, entry_ebitda: float,
        growth_pct: float, base_exit_mult: float, debt: float,
        years: int, esg_score: float, esg_improvement: float,
    ) -> ESGImpactAnalysis:
        """Compute ESG impact on IRR/MOIC."""
        # Base case
        base = self._compute_scenario(
            "Base", equity, entry_ebitda, growth_pct,
            base_exit_mult, debt, years,
        )

        # ESG multiple expansion
        expansion = round(esg_improvement * ESG_BPS_PER_POINT / 10000, 4)
        premium_pct = round(esg_improvement * ESG_BPS_PER_POINT / 100, 2)

        # ESG risk discount (low ESG = higher risk)
        risk_discount = 0.0
        if esg_score < 50:
            deficit = (50 - esg_score) / 10
            risk_discount = round(deficit * ESG_RISK_BPS_PER_10 / 100, 2)

        # Adjusted exit multiple
        adj_exit_mult = base_exit_mult + expansion
        adj = self._compute_scenario(
            "ESG Adjusted", equity, entry_ebitda, growth_pct,
            adj_exit_mult, debt, years,
        )

        delta_bps = round((adj.irr_pct - base.irr_pct) * 100)

        return ESGImpactAnalysis(
            base_irr_pct=base.irr_pct,
            esg_adjusted_irr_pct=adj.irr_pct,
            irr_delta_bps=delta_bps,
            base_moic=base.moic,
            esg_adjusted_moic=adj.moic,
            multiple_expansion_x=round(expansion, 4),
            esg_valuation_premium_pct=premium_pct,
            esg_risk_discount_pct=risk_discount,
        )

    # -------------------------------------------------------------------
    # Sensitivity Table
    # -------------------------------------------------------------------

    def _build_sensitivity_table(
        self, equity: float, entry_ebitda: float,
        base_growth: float, base_exit_mult: float, debt: float, years: int,
    ) -> SensitivityTable:
        """Build exit multiple x EBITDA growth sensitivity grid."""
        # 5x5 grid
        mult_offsets = [-2, -1, 0, 1, 2]
        growth_offsets = [-2, -1, 0, 1, 2]

        row_values = [round(base_exit_mult + o, 1) for o in mult_offsets]
        col_values = [round(base_growth + o, 1) for o in growth_offsets]

        # Filter out invalid values
        row_values = [max(2.0, v) for v in row_values]
        col_values = [max(0.0, v) for v in col_values]

        cells = []
        base_irr = 0.0
        base_moic = 0.0

        for mult in row_values:
            for growth in col_values:
                sc = self._compute_scenario(
                    f"{mult}x/{growth}%", equity, entry_ebitda,
                    growth, mult, debt, years,
                )
                cell = SensitivityCell(
                    row_label=f"{mult}x",
                    col_label=f"{growth}%",
                    row_value=mult,
                    col_value=growth,
                    irr_pct=sc.irr_pct,
                    moic=sc.moic,
                    equity_return_eur=sc.equity_value_eur,
                )
                cells.append(cell)

                if mult == base_exit_mult and growth == base_growth:
                    base_irr = sc.irr_pct
                    base_moic = sc.moic

        return SensitivityTable(
            row_dimension="exit_multiple",
            col_dimension="ebitda_growth_pct",
            row_values=row_values,
            col_values=col_values,
            cells=cells,
            base_irr_pct=base_irr,
            base_moic=base_moic,
        )
