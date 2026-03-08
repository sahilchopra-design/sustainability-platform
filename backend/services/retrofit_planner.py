"""
Retrofit CapEx Planner
======================
NPV / payback analysis for energy efficiency upgrades per property.

Key outputs:
- Per-measure cost estimates (LED, HVAC, insulation, solar PV, heat pump, windows, BMS)
- Energy savings (kWh/m2/yr) and carbon savings per measure
- NPV and simple payback per measure
- Portfolio-level retrofit budget: total capex, prioritised by ROI
- Green value uplift estimate post-retrofit
- Target EPC after retrofit (projected upgrade path)

References:
- IEA Energy Efficiency Market Report 2024
- UK Green Finance Institute: "The Green Retrofit Handbook" 2023
- CRREM Retrofit Guidance
- EU Energy Performance of Buildings Directive (EPBD) recast 2024
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Retrofit Measure Catalogue
# ---------------------------------------------------------------------------

@dataclass
class RetrofitMeasure:
    """A single retrofit intervention."""
    measure_id: str
    name: str
    category: str                  # envelope / hvac / lighting / renewables / controls
    capex_eur_m2: float            # Installed cost per m2 of GIA
    energy_saving_kwh_m2: float    # Annual energy saving per m2
    carbon_saving_pct: float       # % reduction in operational carbon
    typical_lifetime_years: int    # Expected measure life
    epc_improvement_steps: int     # Expected EPC rating improvement (steps)
    applicability: list[str]       # Property types this applies to


# Default catalogue — based on UK GFI / CRREM / industry benchmarks
MEASURE_CATALOGUE: list[RetrofitMeasure] = [
    RetrofitMeasure(
        "LED", "LED Lighting Upgrade", "lighting",
        capex_eur_m2=8.0, energy_saving_kwh_m2=12.0,
        carbon_saving_pct=5.0, typical_lifetime_years=15,
        epc_improvement_steps=0, applicability=["office", "retail", "industrial", "hotel", "multifamily"],
    ),
    RetrofitMeasure(
        "BMS", "Building Management System", "controls",
        capex_eur_m2=15.0, energy_saving_kwh_m2=18.0,
        carbon_saving_pct=8.0, typical_lifetime_years=12,
        epc_improvement_steps=0, applicability=["office", "retail", "hotel"],
    ),
    RetrofitMeasure(
        "HVAC", "HVAC System Replacement", "hvac",
        capex_eur_m2=45.0, energy_saving_kwh_m2=35.0,
        carbon_saving_pct=15.0, typical_lifetime_years=20,
        epc_improvement_steps=1, applicability=["office", "retail", "industrial", "hotel", "multifamily"],
    ),
    RetrofitMeasure(
        "INSULATION_WALL", "External Wall Insulation", "envelope",
        capex_eur_m2=65.0, energy_saving_kwh_m2=40.0,
        carbon_saving_pct=18.0, typical_lifetime_years=30,
        epc_improvement_steps=1, applicability=["office", "retail", "multifamily", "hotel"],
    ),
    RetrofitMeasure(
        "INSULATION_ROOF", "Roof Insulation Upgrade", "envelope",
        capex_eur_m2=30.0, energy_saving_kwh_m2=20.0,
        carbon_saving_pct=8.0, typical_lifetime_years=30,
        epc_improvement_steps=1, applicability=["office", "retail", "industrial", "multifamily", "hotel"],
    ),
    RetrofitMeasure(
        "WINDOWS", "Double/Triple Glazing", "envelope",
        capex_eur_m2=80.0, energy_saving_kwh_m2=25.0,
        carbon_saving_pct=10.0, typical_lifetime_years=25,
        epc_improvement_steps=1, applicability=["office", "retail", "multifamily", "hotel"],
    ),
    RetrofitMeasure(
        "SOLAR_PV", "Rooftop Solar PV", "renewables",
        capex_eur_m2=55.0, energy_saving_kwh_m2=30.0,
        carbon_saving_pct=12.0, typical_lifetime_years=25,
        epc_improvement_steps=1, applicability=["office", "retail", "industrial", "multifamily"],
    ),
    RetrofitMeasure(
        "HEAT_PUMP", "Air Source Heat Pump", "hvac",
        capex_eur_m2=70.0, energy_saving_kwh_m2=50.0,
        carbon_saving_pct=25.0, typical_lifetime_years=20,
        epc_improvement_steps=2, applicability=["office", "retail", "multifamily", "hotel"],
    ),
]


# Energy price EUR/kWh by country (blended commercial electricity)
ENERGY_PRICES: dict[str, float] = {
    "NL": 0.18, "GB": 0.22, "FR": 0.14, "DE": 0.20,
    "US": 0.12, "EU": 0.16,
}

# Carbon price EUR/tCO2e (for carbon savings valuation)
DEFAULT_CARBON_PRICE = 90.0  # EU ETS ~90 EUR/t

# Grid emission factors kgCO2e/kWh
GRID_FACTORS: dict[str, float] = {
    "NL": 0.38, "GB": 0.21, "FR": 0.06, "DE": 0.35,
    "US": 0.40, "EU": 0.25,
}

# EPC rank for upgrade path projection
EPC_RANK: dict[str, int] = {
    "A+": 1, "A": 2, "B": 3, "C": 4, "D": 5, "E": 6, "F": 7, "G": 8,
}
RANK_TO_EPC: dict[int, str] = {v: k for k, v in EPC_RANK.items()}


# ---------------------------------------------------------------------------
# Data Classes — Inputs
# ---------------------------------------------------------------------------

@dataclass
class PropertyRetrofitInput:
    """Input for retrofit analysis of a single property."""
    property_id: str
    name: str
    country: str
    property_type: str          # office / retail / industrial / multifamily / hotel
    floor_area_m2: float
    current_epc: str            # A+ through G
    current_energy_intensity_kwh_m2: float  # Current EUI
    market_value: float         # EUR
    annual_rent: float          # EUR
    target_epc: Optional[str] = None   # Desired EPC (defaults to "B")
    discount_rate: float = 0.06        # For NPV calculations
    carbon_price_eur_t: float = DEFAULT_CARBON_PRICE
    existing_measures: list[str] = field(default_factory=list)  # Already-installed measure IDs


# ---------------------------------------------------------------------------
# Data Classes — Outputs
# ---------------------------------------------------------------------------

@dataclass
class MeasureResult:
    """NPV/payback result for a single retrofit measure."""
    measure_id: str
    name: str
    category: str
    capex_total: float                  # EUR
    capex_per_m2: float                 # EUR/m2
    annual_energy_saving_kwh: float     # kWh/yr
    annual_energy_cost_saving: float    # EUR/yr
    annual_carbon_saving_tco2: float    # tCO2e/yr
    annual_carbon_cost_saving: float    # EUR/yr
    total_annual_saving: float          # EUR/yr (energy + carbon)
    simple_payback_years: float         # Years
    npv: float                          # EUR
    irr: Optional[float]               # % (None if cashflows don't cross zero)
    roi_pct: float                      # NPV / capex * 100
    epc_improvement_steps: int
    lifetime_years: int


@dataclass
class PropertyRetrofitPlan:
    """Complete retrofit plan for a single property."""
    property_id: str
    name: str
    current_epc: str
    target_epc: str
    projected_epc_after_retrofit: str
    total_capex: float
    total_annual_saving: float
    portfolio_payback_years: float      # Aggregate simple payback
    aggregate_npv: float
    energy_reduction_pct: float         # Total % reduction in EUI
    carbon_reduction_pct: float         # Total % reduction in carbon
    green_value_uplift_pct: float       # Estimated market value uplift
    green_value_uplift_eur: float
    measures: list[MeasureResult]       # Individual measures, sorted by ROI


@dataclass
class PortfolioRetrofitSummary:
    """Portfolio-level retrofit budget and prioritisation."""
    total_properties: int
    total_capex_required: float
    total_annual_savings: float
    portfolio_simple_payback: float
    portfolio_aggregate_npv: float
    avg_energy_reduction_pct: float
    avg_carbon_reduction_pct: float
    total_green_value_uplift: float
    capex_by_category: dict[str, float]       # envelope / hvac / lighting / renewables / controls
    top_roi_properties: list[dict]            # Top 5 by ROI
    property_plans: list[PropertyRetrofitPlan]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RetrofitPlanner:
    """NPV/payback retrofit analysis per property and portfolio."""

    def __init__(self, catalogue: Optional[list[RetrofitMeasure]] = None):
        self.catalogue = catalogue or MEASURE_CATALOGUE

    def plan_property(self, prop: PropertyRetrofitInput) -> PropertyRetrofitPlan:
        """Generate retrofit plan for a single property."""
        target = prop.target_epc or "B"
        target_rank = EPC_RANK.get(target, 3)
        current_rank = EPC_RANK.get(prop.current_epc, 8)
        country = prop.country.upper()
        energy_price = ENERGY_PRICES.get(country, ENERGY_PRICES["EU"])
        grid_factor = GRID_FACTORS.get(country, GRID_FACTORS["EU"])

        # Filter applicable measures (not already installed, applicable to property type)
        applicable = [
            m for m in self.catalogue
            if m.measure_id not in prop.existing_measures
            and prop.property_type.lower() in m.applicability
        ]

        measure_results: list[MeasureResult] = []
        cumulative_epc_steps = 0
        cumulative_energy_saving_pct = 0.0
        cumulative_carbon_saving_pct = 0.0

        for m in applicable:
            # Scale capex and savings to floor area
            capex = m.capex_eur_m2 * prop.floor_area_m2
            annual_kwh_saved = m.energy_saving_kwh_m2 * prop.floor_area_m2
            annual_energy_eur = annual_kwh_saved * energy_price
            annual_carbon_t = annual_kwh_saved * grid_factor / 1000.0
            annual_carbon_eur = annual_carbon_t * prop.carbon_price_eur_t
            total_annual = annual_energy_eur + annual_carbon_eur

            # Simple payback
            payback = capex / total_annual if total_annual > 0 else 999.0

            # NPV over measure lifetime
            npv = self._npv(capex, total_annual, m.typical_lifetime_years, prop.discount_rate)

            # IRR approximation
            irr = self._irr_approx(capex, total_annual, m.typical_lifetime_years)

            # ROI
            roi = (npv / capex * 100) if capex > 0 else 0.0

            # Energy saving as % of current intensity
            energy_pct = (m.energy_saving_kwh_m2 / prop.current_energy_intensity_kwh_m2 * 100
                          if prop.current_energy_intensity_kwh_m2 > 0 else 0.0)

            mr = MeasureResult(
                measure_id=m.measure_id,
                name=m.name,
                category=m.category,
                capex_total=round(capex, 2),
                capex_per_m2=m.capex_eur_m2,
                annual_energy_saving_kwh=round(annual_kwh_saved, 0),
                annual_energy_cost_saving=round(annual_energy_eur, 2),
                annual_carbon_saving_tco2=round(annual_carbon_t, 3),
                annual_carbon_cost_saving=round(annual_carbon_eur, 2),
                total_annual_saving=round(total_annual, 2),
                simple_payback_years=round(payback, 1),
                npv=round(npv, 2),
                irr=round(irr, 2) if irr is not None else None,
                roi_pct=round(roi, 1),
                epc_improvement_steps=m.epc_improvement_steps,
                lifetime_years=m.typical_lifetime_years,
            )
            measure_results.append(mr)

            cumulative_epc_steps += m.epc_improvement_steps
            cumulative_energy_saving_pct += energy_pct
            cumulative_carbon_saving_pct += m.carbon_saving_pct

        # Sort measures by ROI descending
        measure_results.sort(key=lambda x: x.roi_pct, reverse=True)

        # Select measures needed to reach target EPC (greedy by ROI)
        selected = self._select_measures_to_target(
            measure_results, current_rank, target_rank
        )

        # Totals from selected measures
        total_capex = sum(m.capex_total for m in selected)
        total_annual = sum(m.total_annual_saving for m in selected)
        total_payback = total_capex / total_annual if total_annual > 0 else 999.0
        agg_npv = sum(m.npv for m in selected)

        # Projected EPC
        steps_gained = sum(m.epc_improvement_steps for m in selected)
        projected_rank = max(1, current_rank - steps_gained)
        projected_epc = RANK_TO_EPC.get(projected_rank, "A+")

        # Energy / carbon reduction (capped at 100%)
        energy_red = min(100.0, sum(
            m.annual_energy_saving_kwh / (prop.current_energy_intensity_kwh_m2 * prop.floor_area_m2) * 100
            for m in selected
        ) if prop.current_energy_intensity_kwh_m2 > 0 and prop.floor_area_m2 > 0 else 0.0)

        carbon_red = min(100.0, sum(
            next((cat.carbon_saving_pct for cat in self.catalogue if cat.measure_id == m.measure_id), 0)
            for m in selected
        ))

        # Green value uplift: ~3-5% per EPC step improvement (based on RICS research)
        green_uplift_pct = min(25.0, steps_gained * 3.5)
        green_uplift_eur = prop.market_value * green_uplift_pct / 100.0

        return PropertyRetrofitPlan(
            property_id=prop.property_id,
            name=prop.name,
            current_epc=prop.current_epc,
            target_epc=target,
            projected_epc_after_retrofit=projected_epc,
            total_capex=round(total_capex, 2),
            total_annual_saving=round(total_annual, 2),
            portfolio_payback_years=round(total_payback, 1),
            aggregate_npv=round(agg_npv, 2),
            energy_reduction_pct=round(energy_red, 1),
            carbon_reduction_pct=round(carbon_red, 1),
            green_value_uplift_pct=round(green_uplift_pct, 1),
            green_value_uplift_eur=round(green_uplift_eur, 2),
            measures=selected,
        )

    def plan_portfolio(
        self, properties: list[PropertyRetrofitInput]
    ) -> PortfolioRetrofitSummary:
        """Generate retrofit plan across a portfolio."""
        if not properties:
            return PortfolioRetrofitSummary(
                total_properties=0, total_capex_required=0,
                total_annual_savings=0, portfolio_simple_payback=0,
                portfolio_aggregate_npv=0, avg_energy_reduction_pct=0,
                avg_carbon_reduction_pct=0, total_green_value_uplift=0,
                capex_by_category={}, top_roi_properties=[],
                property_plans=[],
            )

        plans = [self.plan_property(p) for p in properties]
        n = len(plans)

        total_capex = sum(p.total_capex for p in plans)
        total_savings = sum(p.total_annual_saving for p in plans)
        payback = total_capex / total_savings if total_savings > 0 else 999.0
        agg_npv = sum(p.aggregate_npv for p in plans)

        avg_energy = sum(p.energy_reduction_pct for p in plans) / n
        avg_carbon = sum(p.carbon_reduction_pct for p in plans) / n
        total_uplift = sum(p.green_value_uplift_eur for p in plans)

        # CapEx by category
        cat_capex: dict[str, float] = {}
        for plan in plans:
            for m in plan.measures:
                cat_capex[m.category] = cat_capex.get(m.category, 0) + m.capex_total

        # Top 5 by ROI (use aggregate_npv / total_capex)
        sorted_plans = sorted(
            plans,
            key=lambda p: (p.aggregate_npv / p.total_capex) if p.total_capex > 0 else 0,
            reverse=True,
        )
        top_roi = [
            {
                "property_id": p.property_id,
                "name": p.name,
                "total_capex": p.total_capex,
                "aggregate_npv": p.aggregate_npv,
                "payback_years": p.portfolio_payback_years,
                "roi_pct": round(p.aggregate_npv / p.total_capex * 100, 1) if p.total_capex > 0 else 0,
            }
            for p in sorted_plans[:5]
        ]

        return PortfolioRetrofitSummary(
            total_properties=n,
            total_capex_required=round(total_capex, 2),
            total_annual_savings=round(total_savings, 2),
            portfolio_simple_payback=round(payback, 1),
            portfolio_aggregate_npv=round(agg_npv, 2),
            avg_energy_reduction_pct=round(avg_energy, 1),
            avg_carbon_reduction_pct=round(avg_carbon, 1),
            total_green_value_uplift=round(total_uplift, 2),
            capex_by_category={k: round(v, 2) for k, v in cat_capex.items()},
            top_roi_properties=top_roi,
            property_plans=plans,
        )

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _npv(self, capex: float, annual_cf: float, years: int, rate: float) -> float:
        """Simple NPV: -capex + sum(annual_cf / (1+r)^t) for t=1..years."""
        if rate <= 0:
            return -capex + annual_cf * years
        pv = sum(annual_cf / (1 + rate) ** t for t in range(1, years + 1))
        return pv - capex

    def _irr_approx(self, capex: float, annual_cf: float, years: int) -> Optional[float]:
        """Approximate IRR using bisection for uniform cashflows."""
        if capex <= 0 or annual_cf <= 0:
            return None

        def npv_at(r: float) -> float:
            if r <= -1:
                return float("inf")
            return sum(annual_cf / (1 + r) ** t for t in range(1, years + 1)) - capex

        lo, hi = -0.5, 2.0
        if npv_at(lo) < 0:
            return None  # Even at -50% rate, NPV is negative
        if npv_at(hi) > 0:
            return hi * 100  # IRR > 200%

        for _ in range(50):  # bisection iterations
            mid = (lo + hi) / 2
            if npv_at(mid) > 0:
                lo = mid
            else:
                hi = mid
            if abs(hi - lo) < 0.0001:
                break

        return (lo + hi) / 2 * 100  # Return as percentage

    def _select_measures_to_target(
        self,
        measures: list[MeasureResult],
        current_rank: int,
        target_rank: int,
    ) -> list[MeasureResult]:
        """Greedy selection of measures by ROI until target EPC is reached.
        If target is already met, return top 3 positive-NPV measures for optimisation."""
        if current_rank <= target_rank:
            # Already at or better than target — return top positive-NPV measures
            return [m for m in measures if m.npv > 0][:3]

        gap = current_rank - target_rank
        selected: list[MeasureResult] = []
        steps_accumulated = 0

        for m in measures:  # Already sorted by ROI desc
            selected.append(m)
            steps_accumulated += m.epc_improvement_steps
            if steps_accumulated >= gap:
                break

        # If still short on steps, add remaining measures with EPC improvement
        if steps_accumulated < gap:
            remaining = [m for m in measures if m not in selected and m.epc_improvement_steps > 0]
            for m in remaining:
                selected.append(m)
                steps_accumulated += m.epc_improvement_steps
                if steps_accumulated >= gap:
                    break

        return selected
