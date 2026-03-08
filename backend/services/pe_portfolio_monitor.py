"""
PE Portfolio Company Monitoring Engine
=======================================
Tracks portfolio company ESG KPIs quarterly, generates traffic-light
dashboards, and monitors YoY improvement against targets.

References:
- ILPA ESG Data Convergence Initiative — standardised PE ESG KPIs
- UN PRI — Portfolio company engagement and monitoring
- SFDR Art.7 — PAI consideration for unlisted assets
- GHG Protocol — Scope 1+2+3 for portfolio companies
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TrafficLight(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class KPICategory(str, Enum):
    EMISSIONS = "emissions"
    ENERGY = "energy"
    WATER = "water"
    WASTE = "waste"
    DIVERSITY = "diversity"
    SAFETY = "safety"
    GOVERNANCE = "governance"


# ---------------------------------------------------------------------------
# Reference Data — ILPA ESG KPI Definitions
# ---------------------------------------------------------------------------

ILPA_KPIS: dict[str, dict] = {
    "scope_1_emissions_tco2e": {
        "name": "Scope 1 GHG Emissions",
        "category": "emissions",
        "unit": "tCO2e",
        "direction": "lower_is_better",
        "ilpa_metric_id": "GHG-1",
    },
    "scope_2_emissions_tco2e": {
        "name": "Scope 2 GHG Emissions",
        "category": "emissions",
        "unit": "tCO2e",
        "direction": "lower_is_better",
        "ilpa_metric_id": "GHG-2",
    },
    "total_energy_mwh": {
        "name": "Total Energy Consumption",
        "category": "energy",
        "unit": "MWh",
        "direction": "lower_is_better",
        "ilpa_metric_id": "E-1",
    },
    "renewable_energy_pct": {
        "name": "Renewable Energy Share",
        "category": "energy",
        "unit": "%",
        "direction": "higher_is_better",
        "ilpa_metric_id": "E-2",
    },
    "water_withdrawal_m3": {
        "name": "Water Withdrawal",
        "category": "water",
        "unit": "m3",
        "direction": "lower_is_better",
        "ilpa_metric_id": "W-1",
    },
    "waste_generated_tonnes": {
        "name": "Total Waste Generated",
        "category": "waste",
        "unit": "tonnes",
        "direction": "lower_is_better",
        "ilpa_metric_id": "WS-1",
    },
    "waste_recycled_pct": {
        "name": "Waste Recycled",
        "category": "waste",
        "unit": "%",
        "direction": "higher_is_better",
        "ilpa_metric_id": "WS-2",
    },
    "board_diversity_pct": {
        "name": "Board Gender Diversity",
        "category": "diversity",
        "unit": "%",
        "direction": "higher_is_better",
        "ilpa_metric_id": "D-1",
    },
    "workforce_diversity_pct": {
        "name": "Workforce Gender Diversity",
        "category": "diversity",
        "unit": "%",
        "direction": "higher_is_better",
        "ilpa_metric_id": "D-2",
    },
    "work_injuries_rate": {
        "name": "Work-Related Injuries Rate",
        "category": "safety",
        "unit": "per 200k hours",
        "direction": "lower_is_better",
        "ilpa_metric_id": "S-1",
    },
    "fatalities": {
        "name": "Work-Related Fatalities",
        "category": "safety",
        "unit": "count",
        "direction": "lower_is_better",
        "ilpa_metric_id": "S-2",
    },
    "independent_board_pct": {
        "name": "Independent Board Members",
        "category": "governance",
        "unit": "%",
        "direction": "higher_is_better",
        "ilpa_metric_id": "G-1",
    },
}


# ---------------------------------------------------------------------------
# Data Classes — Input
# ---------------------------------------------------------------------------

@dataclass
class CompanyKPIData:
    """Quarterly KPI data for a single portfolio company."""
    company_id: str
    company_name: str
    sector: str = "Other"
    reporting_period: str = ""   # e.g. "2025-Q4"
    kpi_values: dict[str, float] = field(default_factory=dict)
    # e.g. {"scope_1_emissions_tco2e": 1500, "renewable_energy_pct": 45, ...}


@dataclass
class CompanyTarget:
    """Target for a specific KPI."""
    kpi_id: str
    target_value: float
    target_year: int = 2030


@dataclass
class CompanyMonitorInput:
    """Full monitoring input for a portfolio company."""
    company_id: str
    company_name: str
    sector: str = "Other"
    fund_id: str = ""
    equity_invested_eur: float = 0.0
    ownership_pct: float = 0.0
    current_period: CompanyKPIData = field(default_factory=lambda: CompanyKPIData("", ""))
    prior_period: Optional[CompanyKPIData] = None
    targets: list[CompanyTarget] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Data Classes — Output
# ---------------------------------------------------------------------------

@dataclass
class KPIStatus:
    """Status of a single KPI for a company."""
    kpi_id: str
    kpi_name: str
    category: str
    unit: str
    direction: str
    current_value: float
    prior_value: Optional[float]
    target_value: Optional[float]
    yoy_change: Optional[float]        # Absolute change
    yoy_change_pct: Optional[float]    # Percentage change
    improved: Optional[bool]
    on_target: Optional[bool]
    traffic_light: str                 # green/amber/red


@dataclass
class CompanyMonitorResult:
    """Monitoring result for a single portfolio company."""
    company_id: str
    company_name: str
    sector: str
    reporting_period: str
    kpi_statuses: list[KPIStatus]
    green_count: int
    amber_count: int
    red_count: int
    total_kpis: int
    overall_traffic_light: str
    improvement_count: int
    deterioration_count: int
    on_target_count: int
    off_target_count: int


@dataclass
class PortfolioMonitorSummary:
    """Portfolio-wide monitoring summary."""
    fund_id: str
    total_companies: int
    reporting_period: str
    company_results: list[CompanyMonitorResult]
    portfolio_green_pct: float
    portfolio_amber_pct: float
    portfolio_red_pct: float
    worst_performing: list[dict]    # Companies with most red KPIs
    best_performing: list[dict]     # Companies with most green KPIs
    aggregate_kpis: dict[str, float]  # Portfolio-level weighted avg KPIs


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PEPortfolioMonitor:
    """Portfolio company ESG KPI monitoring engine."""

    def monitor_company(self, inp: CompanyMonitorInput) -> CompanyMonitorResult:
        """Monitor a single portfolio company's ESG KPIs."""
        kpi_statuses = []
        green = amber = red = 0
        improved = deteriorated = 0
        on_target = off_target = 0

        for kpi_id, kpi_def in ILPA_KPIS.items():
            current_val = inp.current_period.kpi_values.get(kpi_id)
            if current_val is None:
                continue

            prior_val = None
            if inp.prior_period:
                prior_val = inp.prior_period.kpi_values.get(kpi_id)

            target_val = None
            for t in inp.targets:
                if t.kpi_id == kpi_id:
                    target_val = t.target_value
                    break

            direction = kpi_def["direction"]

            # YoY change
            yoy = None
            yoy_pct = None
            is_improved = None
            if prior_val is not None:
                yoy = current_val - prior_val
                if prior_val != 0:
                    yoy_pct = round((current_val - prior_val) / abs(prior_val) * 100, 2)
                if direction == "lower_is_better":
                    is_improved = current_val < prior_val
                else:
                    is_improved = current_val > prior_val

                if is_improved:
                    improved += 1
                else:
                    deteriorated += 1

            # Target check
            is_on_target = None
            if target_val is not None:
                if direction == "lower_is_better":
                    is_on_target = current_val <= target_val
                else:
                    is_on_target = current_val >= target_val
                if is_on_target:
                    on_target += 1
                else:
                    off_target += 1

            # Traffic light
            tl = self._traffic_light(current_val, prior_val, target_val, direction)
            if tl == "green":
                green += 1
            elif tl == "amber":
                amber += 1
            else:
                red += 1

            kpi_statuses.append(KPIStatus(
                kpi_id=kpi_id,
                kpi_name=kpi_def["name"],
                category=kpi_def["category"],
                unit=kpi_def["unit"],
                direction=direction,
                current_value=current_val,
                prior_value=prior_val,
                target_value=target_val,
                yoy_change=round(yoy, 4) if yoy is not None else None,
                yoy_change_pct=yoy_pct,
                improved=is_improved,
                on_target=is_on_target,
                traffic_light=tl,
            ))

        total = len(kpi_statuses)
        overall = self._overall_traffic_light(green, amber, red, total)

        return CompanyMonitorResult(
            company_id=inp.company_id,
            company_name=inp.company_name,
            sector=inp.sector,
            reporting_period=inp.current_period.reporting_period,
            kpi_statuses=kpi_statuses,
            green_count=green,
            amber_count=amber,
            red_count=red,
            total_kpis=total,
            overall_traffic_light=overall,
            improvement_count=improved,
            deterioration_count=deteriorated,
            on_target_count=on_target,
            off_target_count=off_target,
        )

    def monitor_portfolio(
        self, fund_id: str, companies: list[CompanyMonitorInput],
    ) -> PortfolioMonitorSummary:
        """Monitor all portfolio companies and produce summary."""
        results = [self.monitor_company(c) for c in companies]

        if not results:
            return PortfolioMonitorSummary(
                fund_id=fund_id, total_companies=0, reporting_period="",
                company_results=[], portfolio_green_pct=0, portfolio_amber_pct=0,
                portfolio_red_pct=0, worst_performing=[], best_performing=[],
                aggregate_kpis={},
            )

        total_g = sum(r.green_count for r in results)
        total_a = sum(r.amber_count for r in results)
        total_r = sum(r.red_count for r in results)
        total_all = total_g + total_a + total_r

        pct_g = round(total_g / total_all * 100, 1) if total_all > 0 else 0
        pct_a = round(total_a / total_all * 100, 1) if total_all > 0 else 0
        pct_r = round(total_r / total_all * 100, 1) if total_all > 0 else 0

        # Best/worst by red count
        sorted_by_red = sorted(results, key=lambda r: r.red_count, reverse=True)
        worst = [{"company_id": r.company_id, "company_name": r.company_name,
                  "red_count": r.red_count, "overall": r.overall_traffic_light}
                 for r in sorted_by_red[:5] if r.red_count > 0]

        sorted_by_green = sorted(results, key=lambda r: r.green_count, reverse=True)
        best = [{"company_id": r.company_id, "company_name": r.company_name,
                 "green_count": r.green_count, "overall": r.overall_traffic_light}
                for r in sorted_by_green[:5] if r.green_count > 0]

        # Aggregate KPIs (weighted by ownership)
        agg = self._aggregate_kpis(companies)

        period = results[0].reporting_period if results else ""

        return PortfolioMonitorSummary(
            fund_id=fund_id,
            total_companies=len(results),
            reporting_period=period,
            company_results=results,
            portfolio_green_pct=pct_g,
            portfolio_amber_pct=pct_a,
            portfolio_red_pct=pct_r,
            worst_performing=worst,
            best_performing=best,
            aggregate_kpis=agg,
        )

    def get_kpi_template(self) -> list[dict]:
        """Return KPI collection template for portfolio companies."""
        return [
            {"kpi_id": k, **v}
            for k, v in ILPA_KPIS.items()
        ]

    # -------------------------------------------------------------------
    # Traffic Light Logic
    # -------------------------------------------------------------------

    def _traffic_light(
        self, current: float, prior: Optional[float],
        target: Optional[float], direction: str,
    ) -> str:
        """Determine traffic light for a single KPI."""
        # If target exists, use target-based logic
        if target is not None:
            if direction == "lower_is_better":
                if current <= target:
                    return "green"
                elif current <= target * 1.2:  # Within 20% of target
                    return "amber"
                else:
                    return "red"
            else:
                if current >= target:
                    return "green"
                elif current >= target * 0.8:  # Within 20% of target
                    return "amber"
                else:
                    return "red"

        # If no target but has prior, use trend-based logic
        if prior is not None:
            if direction == "lower_is_better":
                if current < prior:
                    return "green"
                elif current == prior:
                    return "amber"
                else:
                    return "red"
            else:
                if current > prior:
                    return "green"
                elif current == prior:
                    return "amber"
                else:
                    return "red"

        # No target and no prior — amber (insufficient data)
        return "amber"

    def _overall_traffic_light(
        self, green: int, amber: int, red: int, total: int,
    ) -> str:
        """Overall company traffic light from KPI distribution."""
        if total == 0:
            return "amber"
        red_pct = red / total * 100
        green_pct = green / total * 100

        if red_pct >= 40:
            return "red"
        elif green_pct >= 60:
            return "green"
        else:
            return "amber"

    # -------------------------------------------------------------------
    # Aggregation
    # -------------------------------------------------------------------

    def _aggregate_kpis(self, companies: list[CompanyMonitorInput]) -> dict[str, float]:
        """Weighted-average KPIs across portfolio (by ownership %)."""
        totals: dict[str, float] = {}
        weights: dict[str, float] = {}

        for c in companies:
            w = c.ownership_pct if c.ownership_pct > 0 else 1.0
            for kpi_id, val in c.current_period.kpi_values.items():
                if kpi_id not in totals:
                    totals[kpi_id] = 0.0
                    weights[kpi_id] = 0.0
                totals[kpi_id] += val * w
                weights[kpi_id] += w

        result = {}
        for kpi_id in totals:
            if weights[kpi_id] > 0:
                result[kpi_id] = round(totals[kpi_id] / weights[kpi_id], 4)
        return result
