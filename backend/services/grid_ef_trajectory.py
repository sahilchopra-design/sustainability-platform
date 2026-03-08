"""
Grid Emission Factor Trajectory Engine
========================================
Projects grid emission factors per country/region from 2020 to 2050 under
multiple scenarios (Current Policies, NZE, Stated Policies, NGFS).
Provides location-based Scope 2 factors and avoided emissions calculations.

References:
- IEA World Energy Outlook (2024) — grid EF projections
- NGFS Phase IV (2024) — Orderly / Disorderly / Hot House scenarios
- UNFCCC CDM combined margin methodology (ACM0002)
- Ember Global Electricity Review (2024)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Reference Data — Grid EFs by Country (tCO2/MWh, 2023 baseline)
# ---------------------------------------------------------------------------

GRID_EF_BASELINE: dict[str, dict] = {
    "DE": {"ef_2023": 0.38, "label": "Germany", "region": "EU"},
    "FR": {"ef_2023": 0.06, "label": "France", "region": "EU"},
    "NL": {"ef_2023": 0.34, "label": "Netherlands", "region": "EU"},
    "PL": {"ef_2023": 0.66, "label": "Poland", "region": "EU"},
    "ES": {"ef_2023": 0.17, "label": "Spain", "region": "EU"},
    "IT": {"ef_2023": 0.28, "label": "Italy", "region": "EU"},
    "GB": {"ef_2023": 0.21, "label": "United Kingdom", "region": "Europe"},
    "SE": {"ef_2023": 0.01, "label": "Sweden", "region": "EU"},
    "US": {"ef_2023": 0.39, "label": "United States", "region": "Americas"},
    "CN": {"ef_2023": 0.58, "label": "China", "region": "Asia-Pacific"},
    "IN": {"ef_2023": 0.72, "label": "India", "region": "Asia-Pacific"},
    "JP": {"ef_2023": 0.47, "label": "Japan", "region": "Asia-Pacific"},
    "AU": {"ef_2023": 0.62, "label": "Australia", "region": "Asia-Pacific"},
    "BR": {"ef_2023": 0.08, "label": "Brazil", "region": "Americas"},
    "ZA": {"ef_2023": 0.90, "label": "South Africa", "region": "Africa"},
    "KR": {"ef_2023": 0.42, "label": "South Korea", "region": "Asia-Pacific"},
    "CA": {"ef_2023": 0.12, "label": "Canada", "region": "Americas"},
    "MX": {"ef_2023": 0.41, "label": "Mexico", "region": "Americas"},
    "ID": {"ef_2023": 0.73, "label": "Indonesia", "region": "Asia-Pacific"},
    "SA": {"ef_2023": 0.58, "label": "Saudi Arabia", "region": "Middle East"},
    "AE": {"ef_2023": 0.44, "label": "UAE", "region": "Middle East"},
    "NG": {"ef_2023": 0.45, "label": "Nigeria", "region": "Africa"},
    "EG": {"ef_2023": 0.47, "label": "Egypt", "region": "Africa"},
    "TH": {"ef_2023": 0.46, "label": "Thailand", "region": "Asia-Pacific"},
    "VN": {"ef_2023": 0.52, "label": "Vietnam", "region": "Asia-Pacific"},
}

# Scenario reduction rates (annual % reduction from baseline)
SCENARIOS: dict[str, dict] = {
    "current_policies": {
        "label": "Current Policies",
        "annual_reduction_pct": 1.5,
        "target_2030_factor": 0.88,
        "target_2050_factor": 0.55,
    },
    "stated_policies": {
        "label": "Stated Policies (STEPS)",
        "annual_reduction_pct": 2.5,
        "target_2030_factor": 0.78,
        "target_2050_factor": 0.30,
    },
    "nze_2050": {
        "label": "Net Zero by 2050",
        "annual_reduction_pct": 5.5,
        "target_2030_factor": 0.55,
        "target_2050_factor": 0.00,
    },
    "ngfs_orderly": {
        "label": "NGFS Orderly (Below 2C)",
        "annual_reduction_pct": 4.0,
        "target_2030_factor": 0.65,
        "target_2050_factor": 0.08,
    },
    "ngfs_disorderly": {
        "label": "NGFS Disorderly (Delayed Transition)",
        "annual_reduction_pct": 1.0,
        "target_2030_factor": 0.92,
        "target_2050_factor": 0.15,
    },
    "ngfs_hot_house": {
        "label": "NGFS Hot House World",
        "annual_reduction_pct": 0.5,
        "target_2030_factor": 0.95,
        "target_2050_factor": 0.65,
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class GridEFProjection:
    """Grid emission factor projection for one country under one scenario."""
    country: str
    country_label: str
    region: str
    scenario: str
    scenario_label: str
    baseline_ef_2023: float
    trajectory: list[dict]  # [{year, ef_tco2_mwh}]
    ef_2030: float
    ef_2040: float
    ef_2050: float
    total_reduction_pct: float


@dataclass
class AvoidedEmissionsResult:
    """Avoided emissions from a renewable project at a given location."""
    country: str
    scenario: str
    annual_generation_mwh: float
    project_lifetime_years: int
    year_by_year: list[dict]  # [{year, grid_ef, avoided_tco2}]
    total_avoided_tco2: float
    average_grid_ef: float


@dataclass
class MultiCountryComparison:
    """Compare grid EF trajectories across multiple countries."""
    scenario: str
    scenario_label: str
    countries: list[dict]  # [{country, label, ef_2023, ef_2030, ef_2050, reduction_pct}]
    cleanest_2030: str
    dirtiest_2030: str
    fastest_decarboniser: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GridEFTrajectoryEngine:
    """Grid emission factor projection and avoided emissions engine."""

    def project_grid_ef(
        self,
        country: str = "DE",
        scenario: str = "nze_2050",
        start_year: int = 2023,
        end_year: int = 2050,
    ) -> GridEFProjection:
        """Project grid EF trajectory for a country under a scenario."""
        baseline = GRID_EF_BASELINE.get(country)
        if not baseline:
            baseline = {"ef_2023": 0.40, "label": country, "region": "Unknown"}

        scen = SCENARIOS.get(scenario)
        if not scen:
            scen = SCENARIOS["current_policies"]

        ef_base = baseline["ef_2023"]

        # Build trajectory using target factors
        trajectory = []
        for yr in range(start_year, end_year + 1):
            ef = self._interpolate_ef(yr, ef_base, scen, start_year)
            trajectory.append({"year": yr, "ef_tco2_mwh": round(ef, 4)})

        ef_2030 = self._interpolate_ef(2030, ef_base, scen, start_year)
        ef_2040 = self._interpolate_ef(2040, ef_base, scen, start_year)
        ef_2050 = self._interpolate_ef(2050, ef_base, scen, start_year)

        reduction = (1 - ef_2050 / ef_base) * 100 if ef_base > 0 else 0

        return GridEFProjection(
            country=country,
            country_label=baseline["label"],
            region=baseline["region"],
            scenario=scenario,
            scenario_label=scen["label"],
            baseline_ef_2023=ef_base,
            trajectory=trajectory,
            ef_2030=round(ef_2030, 4),
            ef_2040=round(ef_2040, 4),
            ef_2050=round(ef_2050, 4),
            total_reduction_pct=round(reduction, 1),
        )

    def avoided_emissions(
        self,
        country: str = "DE",
        scenario: str = "nze_2050",
        annual_generation_mwh: float = 50_000,
        start_year: int = 2025,
        project_lifetime_years: int = 25,
    ) -> AvoidedEmissionsResult:
        """Calculate avoided emissions for a renewable project."""
        baseline = GRID_EF_BASELINE.get(country)
        if not baseline:
            baseline = {"ef_2023": 0.40, "label": country, "region": "Unknown"}

        scen = SCENARIOS.get(scenario, SCENARIOS["current_policies"])
        ef_base = baseline["ef_2023"]

        year_data = []
        total_avoided = 0
        ef_sum = 0

        for i in range(project_lifetime_years):
            yr = start_year + i
            ef = self._interpolate_ef(yr, ef_base, scen, 2023)
            avoided = annual_generation_mwh * ef
            total_avoided += avoided
            ef_sum += ef
            year_data.append({
                "year": yr,
                "grid_ef": round(ef, 4),
                "avoided_tco2": round(avoided, 1),
            })

        avg_ef = ef_sum / project_lifetime_years if project_lifetime_years > 0 else 0

        return AvoidedEmissionsResult(
            country=country,
            scenario=scenario,
            annual_generation_mwh=annual_generation_mwh,
            project_lifetime_years=project_lifetime_years,
            year_by_year=year_data,
            total_avoided_tco2=round(total_avoided, 1),
            average_grid_ef=round(avg_ef, 4),
        )

    def compare_countries(
        self,
        countries: list[str],
        scenario: str = "nze_2050",
    ) -> MultiCountryComparison:
        """Compare grid EF trajectories across countries."""
        scen = SCENARIOS.get(scenario, SCENARIOS["current_policies"])
        results = []

        for c in countries:
            proj = self.project_grid_ef(c, scenario)
            results.append({
                "country": c,
                "label": proj.country_label,
                "ef_2023": proj.baseline_ef_2023,
                "ef_2030": proj.ef_2030,
                "ef_2050": proj.ef_2050,
                "reduction_pct": proj.total_reduction_pct,
            })

        cleanest_2030 = min(results, key=lambda x: x["ef_2030"])["country"] if results else ""
        dirtiest_2030 = max(results, key=lambda x: x["ef_2030"])["country"] if results else ""
        fastest = max(results, key=lambda x: x["reduction_pct"])["country"] if results else ""

        return MultiCountryComparison(
            scenario=scenario,
            scenario_label=scen["label"],
            countries=results,
            cleanest_2030=cleanest_2030,
            dirtiest_2030=dirtiest_2030,
            fastest_decarboniser=fastest,
        )

    def _interpolate_ef(self, year: int, ef_base: float, scen: dict, base_year: int) -> float:
        """Interpolate grid EF for a given year using scenario target factors."""
        if year <= base_year:
            return ef_base

        f_2030 = scen["target_2030_factor"]
        f_2050 = scen["target_2050_factor"]

        if year <= 2030:
            frac = (year - base_year) / (2030 - base_year) if 2030 > base_year else 0
            factor = 1 + (f_2030 - 1) * frac
        elif year <= 2050:
            frac = (year - 2030) / 20
            factor = f_2030 + (f_2050 - f_2030) * frac
        else:
            factor = f_2050

        return max(0, ef_base * factor)

    def get_countries(self) -> dict[str, dict]:
        return GRID_EF_BASELINE

    def get_scenarios(self) -> dict[str, dict]:
        return SCENARIOS
