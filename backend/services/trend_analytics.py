"""
Multi-Year Trend Analytics Engine
====================================
Analyses time-series sustainability KPIs across multiple reporting years.
Computes year-over-year changes, CAGR, trend direction, target trajectory
alignment, and peer-relative positioning.

References:
- ESRS ESRS 2 BP-2 — disclosure of information in relation to prior periods
- GRI 2-4 — restatements of information
- ISSB S1 §B35 — comparative information
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Reference Data — Common KPI Definitions
# ---------------------------------------------------------------------------

KPI_DEFINITIONS: dict[str, dict] = {
    "scope1_tco2e": {"label": "Scope 1 GHG emissions", "unit": "tCO2e", "direction": "lower_better", "category": "climate"},
    "scope2_tco2e": {"label": "Scope 2 GHG emissions", "unit": "tCO2e", "direction": "lower_better", "category": "climate"},
    "scope3_tco2e": {"label": "Scope 3 GHG emissions", "unit": "tCO2e", "direction": "lower_better", "category": "climate"},
    "total_ghg_tco2e": {"label": "Total GHG emissions", "unit": "tCO2e", "direction": "lower_better", "category": "climate"},
    "ghg_intensity_revenue": {"label": "GHG intensity / revenue", "unit": "tCO2e/EUR M", "direction": "lower_better", "category": "climate"},
    "energy_consumption_mwh": {"label": "Total energy consumption", "unit": "MWh", "direction": "lower_better", "category": "energy"},
    "renewable_share_pct": {"label": "Renewable energy share", "unit": "%", "direction": "higher_better", "category": "energy"},
    "water_consumption_m3": {"label": "Water consumption", "unit": "m3", "direction": "lower_better", "category": "water"},
    "waste_total_tonnes": {"label": "Total waste generated", "unit": "tonnes", "direction": "lower_better", "category": "circular"},
    "waste_recycling_pct": {"label": "Waste recycling rate", "unit": "%", "direction": "higher_better", "category": "circular"},
    "board_diversity_pct": {"label": "Board gender diversity", "unit": "%", "direction": "higher_better", "category": "social"},
    "gender_pay_gap_pct": {"label": "Gender pay gap", "unit": "%", "direction": "lower_better", "category": "social"},
    "employee_turnover_pct": {"label": "Employee turnover rate", "unit": "%", "direction": "lower_better", "category": "social"},
    "training_hours_per_employee": {"label": "Training hours per employee", "unit": "hours", "direction": "higher_better", "category": "social"},
    "financed_emissions_tco2e": {"label": "Financed emissions (PCAF)", "unit": "tCO2e", "direction": "lower_better", "category": "financed"},
    "waci_tco2e_per_m": {"label": "WACI", "unit": "tCO2e/EUR M", "direction": "lower_better", "category": "financed"},
    "carbon_footprint_tco2e_per_m": {"label": "Carbon footprint per EUR M invested", "unit": "tCO2e/EUR M", "direction": "lower_better", "category": "financed"},
    "taxonomy_alignment_pct": {"label": "EU Taxonomy alignment", "unit": "%", "direction": "higher_better", "category": "regulatory"},
    "esrs_completeness_pct": {"label": "ESRS disclosure completeness", "unit": "%", "direction": "higher_better", "category": "regulatory"},
    "pai_coverage_pct": {"label": "SFDR PAI coverage", "unit": "%", "direction": "higher_better", "category": "regulatory"},
}

# Peer benchmark averages by sector (illustrative)
PEER_BENCHMARKS: dict[str, dict] = {
    "financial_institutions": {
        "financed_emissions_tco2e": 1500000,
        "waci_tco2e_per_m": 120,
        "taxonomy_alignment_pct": 15,
        "esrs_completeness_pct": 55,
    },
    "energy": {
        "scope1_tco2e": 2000000,
        "renewable_share_pct": 35,
        "ghg_intensity_revenue": 250,
    },
    "manufacturing": {
        "scope1_tco2e": 500000,
        "waste_recycling_pct": 60,
        "water_consumption_m3": 1000000,
    },
    "technology": {
        "scope1_tco2e": 50000,
        "renewable_share_pct": 70,
        "energy_consumption_mwh": 500000,
    },
    "real_estate": {
        "energy_consumption_mwh": 200000,
        "ghg_intensity_revenue": 50,
        "taxonomy_alignment_pct": 20,
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class YearDataPoint:
    """KPI value for a single year."""
    year: int
    value: float


@dataclass
class KPITrend:
    """Trend analysis for a single KPI."""
    kpi_id: str
    label: str
    unit: str
    direction: str  # "lower_better" | "higher_better"
    category: str
    data_points: list[YearDataPoint]
    latest_value: float
    earliest_value: float
    yoy_changes: list[dict]  # [{year, value, prev_value, change_abs, change_pct}]
    cagr_pct: Optional[float]
    trend_direction: str  # "improving" | "worsening" | "stable" | "insufficient_data"
    years_covered: int
    target_value: Optional[float]
    on_track: Optional[bool]
    peer_benchmark: Optional[float]
    vs_peer_pct: Optional[float]


@dataclass
class TrendAnalysisResult:
    """Complete multi-year trend analysis."""
    entity_name: str
    sector: str
    years_range: str
    kpi_count: int
    kpi_trends: list[KPITrend]
    improving_count: int
    worsening_count: int
    stable_count: int
    overall_trajectory: str  # "positive" | "mixed" | "negative"
    highlight_improvements: list[str]
    highlight_concerns: list[str]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TrendAnalyticsEngine:
    """Multi-year trend analysis for sustainability KPIs."""

    def analyse(
        self,
        entity_name: str,
        kpi_series: dict[str, list[dict]],  # {kpi_id: [{year, value}]}
        sector: str = "financial_institutions",
        targets: dict[str, float] = None,  # {kpi_id: target_value}
    ) -> TrendAnalysisResult:
        """Analyse multi-year KPI trends."""
        targets = targets or {}
        peer_data = PEER_BENCHMARKS.get(sector, {})

        trends = []
        improving = 0
        worsening = 0
        stable = 0
        improvements = []
        concerns = []

        all_years = set()

        for kpi_id, series in kpi_series.items():
            defn = KPI_DEFINITIONS.get(kpi_id, {
                "label": kpi_id, "unit": "", "direction": "lower_better", "category": "other"
            })

            # Sort by year
            sorted_pts = sorted(series, key=lambda x: x["year"])
            data_pts = [YearDataPoint(year=p["year"], value=p["value"]) for p in sorted_pts]
            for dp in data_pts:
                all_years.add(dp.year)

            if len(data_pts) < 1:
                continue

            latest = data_pts[-1].value
            earliest = data_pts[0].value
            n_years = len(data_pts)

            # YoY changes
            yoy = []
            for i in range(1, len(data_pts)):
                prev = data_pts[i - 1].value
                curr = data_pts[i].value
                change_abs = curr - prev
                change_pct = ((curr - prev) / abs(prev) * 100) if prev != 0 else 0
                yoy.append({
                    "year": data_pts[i].year,
                    "value": curr,
                    "prev_value": prev,
                    "change_abs": round(change_abs, 2),
                    "change_pct": round(change_pct, 1),
                })

            # CAGR
            cagr = None
            if n_years >= 2 and earliest != 0 and latest / earliest > 0:
                years_span = data_pts[-1].year - data_pts[0].year
                if years_span > 0:
                    cagr = ((latest / earliest) ** (1 / years_span) - 1) * 100

            # Trend direction
            if n_years < 2:
                trend_dir = "insufficient_data"
            else:
                lower_better = defn["direction"] == "lower_better"
                if lower_better:
                    if latest < earliest * 0.97:
                        trend_dir = "improving"
                    elif latest > earliest * 1.03:
                        trend_dir = "worsening"
                    else:
                        trend_dir = "stable"
                else:
                    if latest > earliest * 1.03:
                        trend_dir = "improving"
                    elif latest < earliest * 0.97:
                        trend_dir = "worsening"
                    else:
                        trend_dir = "stable"

            if trend_dir == "improving":
                improving += 1
                improvements.append(f"{defn['label']}: {trend_dir}")
            elif trend_dir == "worsening":
                worsening += 1
                concerns.append(f"{defn['label']}: {trend_dir}")
            else:
                stable += 1

            # Target tracking
            target_val = targets.get(kpi_id)
            on_track = None
            if target_val is not None and n_years >= 2:
                lower_better = defn["direction"] == "lower_better"
                if lower_better:
                    on_track = latest <= target_val or (cagr is not None and cagr < 0)
                else:
                    on_track = latest >= target_val or (cagr is not None and cagr > 0)

            # Peer comparison
            peer_val = peer_data.get(kpi_id)
            vs_peer = None
            if peer_val and peer_val > 0:
                vs_peer = round((latest - peer_val) / peer_val * 100, 1)

            trends.append(KPITrend(
                kpi_id=kpi_id,
                label=defn["label"],
                unit=defn["unit"],
                direction=defn["direction"],
                category=defn["category"],
                data_points=data_pts,
                latest_value=latest,
                earliest_value=earliest,
                yoy_changes=yoy,
                cagr_pct=round(cagr, 2) if cagr is not None else None,
                trend_direction=trend_dir,
                years_covered=n_years,
                target_value=target_val,
                on_track=on_track,
                peer_benchmark=peer_val,
                vs_peer_pct=vs_peer,
            ))

        # Overall trajectory
        if improving > worsening * 2:
            trajectory = "positive"
        elif worsening > improving * 2:
            trajectory = "negative"
        else:
            trajectory = "mixed"

        sorted_years = sorted(all_years)
        years_range = f"{sorted_years[0]}-{sorted_years[-1]}" if sorted_years else ""

        return TrendAnalysisResult(
            entity_name=entity_name,
            sector=sector,
            years_range=years_range,
            kpi_count=len(trends),
            kpi_trends=trends,
            improving_count=improving,
            worsening_count=worsening,
            stable_count=stable,
            overall_trajectory=trajectory,
            highlight_improvements=improvements[:5],
            highlight_concerns=concerns[:5],
        )

    def get_kpi_definitions(self) -> dict[str, dict]:
        return KPI_DEFINITIONS

    def get_peer_benchmarks(self) -> dict[str, dict]:
        return PEER_BENCHMARKS

    def get_sectors(self) -> list[str]:
        return sorted(PEER_BENCHMARKS.keys())
