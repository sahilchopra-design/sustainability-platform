"""
EU ETS Phase 4 Engine
========================
Carbon allowance management, compliance tracking, and auction price modelling
for the EU Emissions Trading System (Directive 2003/87/EC as amended by
Directive 2023/959 — ETS2 for buildings/transport from 2027).

Sub-modules:
  1. Allowance Allocation — Free allocation (benchmarking), auctioning, MSR
  2. Compliance Tracker — Installation-level surrender obligations vs. holdings
  3. Carbon Price Modelling — Forward curve, scenario-based price paths
  4. ETS2 Readiness — Buildings/transport fuel distributors (Art. 30a–30j)
  5. CBAM Interaction — Phase-out of free allocation ↔ CBAM overlap

References:
  - EU ETS Directive 2003/87/EC (consolidated)
  - Delegated Regulation (EU) 2019/331 — Free allocation rules (Phase 4)
  - Commission Decision (EU) 2021/927 — Benchmark values 2021-2025
  - Market Stability Reserve Decision (EU) 2015/1814 (amended 2023)
  - Directive 2023/959 — ETS reform (Fit for 55)
  - ICAP ETS Map — Global carbon pricing reference
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference Data — Benchmark Values (Phase 4, 2021-2025 period)
# Source: Commission Decision (EU) 2021/927 + CLER update 2024
# ---------------------------------------------------------------------------

# Product benchmark values (tCO2/t product) for key sectors
PRODUCT_BENCHMARKS: dict[str, dict] = {
    "hot_metal":          {"benchmark_2021": 1.328, "annual_reduction": 0.024, "unit": "tCO2/t"},
    "sintered_ore":       {"benchmark_2021": 0.171, "annual_reduction": 0.003, "unit": "tCO2/t"},
    "coke":               {"benchmark_2021": 0.286, "annual_reduction": 0.005, "unit": "tCO2/t"},
    "cement_clinker":     {"benchmark_2021": 0.766, "annual_reduction": 0.015, "unit": "tCO2/t"},
    "lime":               {"benchmark_2021": 0.954, "annual_reduction": 0.017, "unit": "tCO2/t"},
    "float_glass":        {"benchmark_2021": 0.453, "annual_reduction": 0.008, "unit": "tCO2/t"},
    "ammonia":            {"benchmark_2021": 1.619, "annual_reduction": 0.029, "unit": "tCO2/t"},
    "hydrogen":           {"benchmark_2021": 8.850, "annual_reduction": 0.160, "unit": "tCO2/t"},
    "aluminium":          {"benchmark_2021": 1.514, "annual_reduction": 0.027, "unit": "tCO2/t"},
    "paper":              {"benchmark_2021": 0.318, "annual_reduction": 0.006, "unit": "tCO2/t"},
    "refinery_products":  {"benchmark_2021": 0.0295, "annual_reduction": 0.0005, "unit": "tCO2/CWT"},
    "heat_benchmark":     {"benchmark_2021": 62.3, "annual_reduction": 1.13, "unit": "tCO2/TJ"},
    "fuel_benchmark":     {"benchmark_2021": 56.1, "annual_reduction": 1.02, "unit": "tCO2/TJ"},
}

# ETS cap and MSR parameters
ETS_CAP_PARAMETERS: dict = {
    "base_cap_2021_mt": 1571.6,     # MtCO2e (stationary installations)
    "annual_lrf_pct_2021_2023": 2.2,  # Linear Reduction Factor 2021-2023
    "annual_lrf_pct_2024_2027": 4.3,  # LRF increased under Fit for 55
    "annual_lrf_pct_2028_plus": 4.4,
    "msr_intake_rate_pct": 24,        # MSR intake rate (2023 onwards)
    "msr_threshold_upper_mt": 833,    # TNAC upper threshold
    "msr_threshold_lower_mt": 400,    # TNAC lower threshold
    "msr_invalidation_above_mt": 400, # Allowances invalidated above this
    "ets2_start_year": 2027,
    "ets2_initial_cap_mt": 600,       # Approximate ETS2 cap
}

# Carbon price scenarios (EUR/tCO2e)
# Source: NGFS Phase IV + IEA WEO 2024 + EU Climate Target Plan modelling
CARBON_PRICE_SCENARIOS: dict[str, dict[int, float]] = {
    "EU_REFERENCE":    {2025: 80, 2030: 110, 2035: 150, 2040: 200, 2050: 300},
    "FIT_FOR_55":      {2025: 85, 2030: 130, 2035: 180, 2040: 250, 2050: 400},
    "NET_ZERO_2050":   {2025: 90, 2030: 150, 2035: 220, 2040: 320, 2050: 500},
    "DELAYED_ACTION":  {2025: 70, 2030: 90,  2035: 130, 2040: 200, 2050: 350},
    "CURRENT_POLICY":  {2025: 75, 2030: 85,  2035: 95,  2040: 110, 2050: 130},
}

# ── ETS2 Reference Data (Directive 2023/959, Art. 30a–30j) ──────────────────
# ETS2 covers fuel distributors for: road transport, buildings (heating/cooling).
# Scope: combustion emissions from fuel placed on market in EU territory.
# Regulated entities: "regulated entities" = fuel distributors (not end users).
# Timeline: MRV monitoring from 2025, compliance starts 2027.

# Emission factors (kgCO2 per litre of fuel combusted).
# Source: IPCC 2006 Guidelines Vol.2 Ch.3 / EU EEA emission factor database.
ETS2_EMISSION_FACTORS: dict[str, dict] = {
    "diesel":         {"ef_kgco2_per_litre": 2.640, "ef_kgco2_per_kg": 3.168,  "description": "Diesel / gas oil — road transport, off-road, heating", "ets2_covered": True},
    "petrol":         {"ef_kgco2_per_litre": 2.319, "ef_kgco2_per_kg": 3.120,  "description": "Petrol / motor gasoline — road transport",          "ets2_covered": True},
    "lpg":            {"ef_kgco2_per_litre": 1.635, "ef_kgco2_per_kg": 2.996,  "description": "Liquefied Petroleum Gas — heating and transport",      "ets2_covered": True},
    "natural_gas":    {"ef_kgco2_per_litre": None,  "ef_kgco2_per_kg": 2.750,  "description": "Natural gas (pipeline) — heating, industrial process",  "ets2_covered": True,  "ef_kgco2_per_m3": 2.020},
    "heating_oil":    {"ef_kgco2_per_litre": 2.630, "ef_kgco2_per_kg": 3.150,  "description": "Light heating oil — residential/commercial heating",    "ets2_covered": True},
    "kerosene":       {"ef_kgco2_per_litre": 2.520, "ef_kgco2_per_kg": 3.140,  "description": "Kerosene / jet fuel — ETS2 only for non-aviation use",  "ets2_covered": True},
    "heavy_fuel_oil": {"ef_kgco2_per_litre": 3.174, "ef_kgco2_per_kg": 3.109,  "description": "Heavy fuel oil — industrial heating",                   "ets2_covered": True},
    "biofuel_blend":  {"ef_kgco2_per_litre": 1.450, "ef_kgco2_per_kg": 1.800,  "description": "Blended biofuel (E10/B7 typical) — partial ETS2 scope", "ets2_covered": True,  "biofuel_exemption_note": "Sustainable biomass fraction exempt under Art. 30c(5)"},
    "cng":            {"ef_kgco2_per_litre": None,  "ef_kgco2_per_kg": 2.720,  "description": "Compressed Natural Gas — road transport",               "ets2_covered": True,  "ef_kgco2_per_m3": 1.960},
    "hydrogen":       {"ef_kgco2_per_litre": 0.0,   "ef_kgco2_per_kg": 0.0,    "description": "Green/blue hydrogen — zero direct combustion emissions", "ets2_covered": False},
    "e_fuel":         {"ef_kgco2_per_litre": 0.0,   "ef_kgco2_per_kg": 0.0,    "description": "E-fuels (electrofuels) — lifecycle emissions apply",    "ets2_covered": False, "note": "Scope 3 lifecycle assessment required"},
}

# ETS2 price corridor per Art. 30d Directive 2023/959 (price stabilisation mechanism).
# Price corridor active from 2027 until ETS2 is fully merged with ETS1 (post-2030 review).
ETS2_PRICE_CORRIDOR: dict = {
    2027: {"floor_eur": 45.0,  "ceiling_eur": 60.0,  "note": "Art. 30d(1): price corridor operative from first compliance year"},
    2028: {"floor_eur": 45.0,  "ceiling_eur": 60.0,  "note": "Price corridor maintained — subject to Commission review"},
    2029: {"floor_eur": 45.0,  "ceiling_eur": 60.0,  "note": "Ceiling triggers release of 20 MtCO2 additional allowances per Art. 30d(3)"},
    2030: {"floor_eur": 45.0,  "ceiling_eur": 60.0,  "note": "Post-2030 corridor review per Art. 30d(4)"},
}

# ETS2 compliance calendar (Directive 2023/959 implementation timeline).
ETS2_COMPLIANCE_CALENDAR: list[dict] = [
    {"year": 2025, "deadline": "2025-01-01", "obligation": "Monitoring Plan submission to competent authority", "article": "Art. 30a(4)"},
    {"year": 2025, "deadline": "2025-12-31", "obligation": "First reporting year for fuel volumes and emissions (reporting only, no surrender)", "article": "Art. 30a(4)"},
    {"year": 2026, "deadline": "2026-03-31", "obligation": "Submit verified 2025 emissions report", "article": "Art. 30a(4)"},
    {"year": 2026, "deadline": "2026-05-30", "obligation": "Register as regulated entity; obtain EUA2 account in EU registry", "article": "Art. 30a(3)"},
    {"year": 2027, "deadline": "2027-04-30", "obligation": "First allowance surrender deadline (for 2026 verified emissions)", "article": "Art. 30b"},
    {"year": 2027, "deadline": "2027-01-01", "obligation": "ETS2 compliance period begins — allowances (EUA2) allocated and auctioned", "article": "Art. 30b"},
    {"year": 2030, "deadline": "2030-12-31", "obligation": "CBAM full implementation — buildings ETS2 fuel distribution fully covered", "article": "Art. 30c"},
]

# CBAM sectors and free allocation phase-out schedule
# Source: Regulation (EU) 2023/956 Article 31
CBAM_FREE_ALLOCATION_PHASEOUT: dict[int, float] = {
    2026: 0.975,   # 97.5% free allocation retained
    2027: 0.950,
    2028: 0.900,
    2029: 0.825,
    2030: 0.750,
    2031: 0.625,
    2032: 0.500,
    2033: 0.375,
    2034: 0.250,
    2035: 0.000,   # Free allocation fully phased out for CBAM sectors
}

CBAM_SECTORS: list[str] = [
    "cement", "iron_steel", "aluminium", "fertilisers",
    "electricity", "hydrogen",
]


# ---------------------------------------------------------------------------
# Carbon Leakage Risk Assessment
# Source: Commission Delegated Decision (EU) 2019/708
# ---------------------------------------------------------------------------

CARBON_LEAKAGE_TIERS: dict[str, dict] = {
    "HIGH": {
        "description": "Deemed at risk of carbon leakage (CL list)",
        "free_allocation_factor": 1.00,
        "trade_intensity_threshold": 0.10,
        "emission_intensity_threshold": 0.05,
    },
    "MEDIUM": {
        "description": "Not on CL list but significant exposure",
        "free_allocation_factor": 0.30,
        "trade_intensity_threshold": 0.05,
        "emission_intensity_threshold": 0.03,
    },
    "LOW": {
        "description": "Low carbon leakage risk — auction-only",
        "free_allocation_factor": 0.00,
    },
}


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AllowanceAllocation:
    """Free allocation result for a single installation."""
    installation_id: str
    installation_name: str
    sector: str
    product_benchmark: str
    year: int
    historical_activity_level: float   # product output per year
    benchmark_value: float             # tCO2/unit in that year
    preliminary_allocation_tco2: float
    carbon_leakage_factor: float       # 1.0 for CL list, 0.3 otherwise
    cross_sectoral_correction: float   # CSCF if cap exceeded
    cbam_reduction_factor: float       # CBAM phase-out factor
    final_allocation_tco2: float
    auction_exposure_tco2: float       # emissions - final allocation
    auction_cost_eur: float            # at assumed carbon price


@dataclass
class CompliancePosition:
    """Installation compliance position for a given year."""
    installation_id: str
    year: int
    verified_emissions_tco2: float
    free_allocation_tco2: float
    purchased_allowances_tco2: float
    banked_allowances_tco2: float
    total_holdings_tco2: float
    surrender_obligation_tco2: float
    surplus_deficit_tco2: float
    compliance_status: str             # compliant | deficit | excess
    estimated_purchase_cost_eur: float
    penalty_exposure_eur: float        # EUR 100/tCO2 penalty for non-compliance


@dataclass
class CarbonPriceForecast:
    """Carbon price forecast under a scenario."""
    scenario: str
    prices_by_year: dict[int, float]
    cagr_pct: float
    price_current_eur: float
    price_2030_eur: float
    price_2050_eur: float
    volatility_annual_pct: float


@dataclass
class ETS2ReadinessResult:
    """ETS2 readiness assessment for building/transport fuel distributors."""
    entity_id: str
    entity_name: str
    ets2_eligible: bool
    fuel_type: str
    annual_emissions_tco2: float
    estimated_allowance_cost_eur: float
    pass_through_potential_pct: float
    consumer_impact_eur_per_litre: float
    readiness_score: float             # 0-100
    gaps: list[str]
    recommendations: list[str]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EUETSEngine:
    """
    EU ETS Phase 4 compliance and carbon price analytics.

    Usage:
        engine = EUETSEngine()
        alloc = engine.calculate_free_allocation(installation_data, year)
        position = engine.assess_compliance(installation_data, year)
        forecast = engine.forecast_carbon_price("NET_ZERO_2050", current_price=80)
    """

    # ── 1. Free Allocation Calculation ────────────────────────────────────

    def calculate_free_allocation(
        self,
        installation_id: str,
        installation_name: str,
        sector: str,
        product_benchmark: str,
        year: int,
        historical_activity_level: float,
        carbon_leakage_listed: bool = True,
        carbon_price_eur: float = 80.0,
    ) -> AllowanceAllocation:
        """Calculate free allocation for an installation under ETS Phase 4."""

        bm = PRODUCT_BENCHMARKS.get(product_benchmark)
        if not bm:
            raise ValueError(f"Unknown product benchmark: {product_benchmark}")

        # Benchmark value for the year (declining annually)
        years_from_2021 = max(0, year - 2021)
        bm_value = max(0.0, bm["benchmark_2021"] - bm["annual_reduction"] * years_from_2021)

        # Preliminary allocation
        preliminary = historical_activity_level * bm_value

        # Carbon leakage factor
        cl_factor = 1.0 if carbon_leakage_listed else 0.3

        # Cross-sectoral correction factor (simplified — 1.0 if cap not exceeded)
        cscf = 1.0

        # CBAM reduction for covered sectors
        cbam_factor = 1.0
        if sector.lower() in CBAM_SECTORS:
            cbam_factor = CBAM_FREE_ALLOCATION_PHASEOUT.get(year, 1.0 if year < 2026 else 0.0)

        final = preliminary * cl_factor * cscf * cbam_factor
        auction_exposure = max(0.0, historical_activity_level * bm["benchmark_2021"] - final)
        auction_cost = auction_exposure * carbon_price_eur

        return AllowanceAllocation(
            installation_id=installation_id,
            installation_name=installation_name,
            sector=sector,
            product_benchmark=product_benchmark,
            year=year,
            historical_activity_level=historical_activity_level,
            benchmark_value=round(bm_value, 6),
            preliminary_allocation_tco2=round(preliminary, 2),
            carbon_leakage_factor=cl_factor,
            cross_sectoral_correction=cscf,
            cbam_reduction_factor=round(cbam_factor, 4),
            final_allocation_tco2=round(final, 2),
            auction_exposure_tco2=round(auction_exposure, 2),
            auction_cost_eur=round(auction_cost, 2),
        )

    # ── 2. Compliance Assessment ──────────────────────────────────────────

    def assess_compliance(
        self,
        installation_id: str,
        year: int,
        verified_emissions_tco2: float,
        free_allocation_tco2: float,
        purchased_allowances_tco2: float = 0.0,
        banked_allowances_tco2: float = 0.0,
        carbon_price_eur: float = 80.0,
    ) -> CompliancePosition:
        """Assess compliance position for an installation."""

        total_holdings = free_allocation_tco2 + purchased_allowances_tco2 + banked_allowances_tco2
        surrender = verified_emissions_tco2
        surplus_deficit = total_holdings - surrender

        if surplus_deficit >= 0:
            status = "compliant" if surplus_deficit == 0 else "excess"
            purchase_cost = 0.0
            penalty = 0.0
        else:
            status = "deficit"
            purchase_cost = abs(surplus_deficit) * carbon_price_eur
            penalty = abs(surplus_deficit) * 100.0  # EUR 100/tCO2 penalty

        return CompliancePosition(
            installation_id=installation_id,
            year=year,
            verified_emissions_tco2=round(verified_emissions_tco2, 2),
            free_allocation_tco2=round(free_allocation_tco2, 2),
            purchased_allowances_tco2=round(purchased_allowances_tco2, 2),
            banked_allowances_tco2=round(banked_allowances_tco2, 2),
            total_holdings_tco2=round(total_holdings, 2),
            surrender_obligation_tco2=round(surrender, 2),
            surplus_deficit_tco2=round(surplus_deficit, 2),
            compliance_status=status,
            estimated_purchase_cost_eur=round(purchase_cost, 2),
            penalty_exposure_eur=round(penalty, 2),
        )

    # ── 3. Carbon Price Forecasting ───────────────────────────────────────

    def forecast_carbon_price(
        self,
        scenario: str = "FIT_FOR_55",
        current_price_eur: float = 80.0,
    ) -> CarbonPriceForecast:
        """Forecast EU ETS carbon price under a given scenario."""

        prices = CARBON_PRICE_SCENARIOS.get(scenario)
        if not prices:
            raise ValueError(f"Unknown scenario: {scenario}. Options: {list(CARBON_PRICE_SCENARIOS)}")

        years = sorted(prices.keys())
        p_2030 = prices.get(2030, 0)
        p_2050 = prices.get(2050, 0)

        # CAGR from current to 2050
        if current_price_eur > 0 and p_2050 > 0:
            n_years = 2050 - 2025
            cagr = ((p_2050 / current_price_eur) ** (1 / n_years) - 1) * 100
        else:
            cagr = 0.0

        # Historical volatility proxy (EU ETS ~30-40% annual)
        volatility = 35.0

        return CarbonPriceForecast(
            scenario=scenario,
            prices_by_year=prices,
            cagr_pct=round(cagr, 2),
            price_current_eur=current_price_eur,
            price_2030_eur=p_2030,
            price_2050_eur=p_2050,
            volatility_annual_pct=volatility,
        )

    # ── 4. ETS Cap Trajectory ─────────────────────────────────────────────

    def compute_cap_trajectory(
        self,
        start_year: int = 2021,
        end_year: int = 2050,
    ) -> list[dict]:
        """Compute EU ETS cap trajectory with LRF schedule."""

        trajectory = []
        cap = ETS_CAP_PARAMETERS["base_cap_2021_mt"]

        for yr in range(start_year, end_year + 1):
            if yr <= 2023:
                lrf = ETS_CAP_PARAMETERS["annual_lrf_pct_2021_2023"]
            elif yr <= 2027:
                lrf = ETS_CAP_PARAMETERS["annual_lrf_pct_2024_2027"]
            else:
                lrf = ETS_CAP_PARAMETERS["annual_lrf_pct_2028_plus"]

            if yr > 2021:
                reduction = ETS_CAP_PARAMETERS["base_cap_2021_mt"] * (lrf / 100)
                cap = max(0.0, cap - reduction)

            trajectory.append({
                "year": yr,
                "cap_mt": round(cap, 1),
                "lrf_pct": lrf,
                "ets2_cap_mt": round(ETS_CAP_PARAMETERS["ets2_initial_cap_mt"], 1) if yr >= 2027 else None,
            })

        return trajectory

    # ── 5. ETS2 Readiness ─────────────────────────────────────────────────

    def assess_ets2_readiness(
        self,
        entity_id: str,
        entity_name: str,
        fuel_type: str,
        annual_fuel_volume_litres: float,
        annual_fuel_volume_kg: float = 0.0,          # for gaseous fuels (kg)
        emission_factor_kgco2_per_litre: float = 0.0,  # override; 0 = use table
        carbon_price_eur: float = 45.0,              # expected ETS2 starting price
        # ETS2 compliance readiness factors (Directive 2023/959 Art. 30a-30j)
        has_mrv_system: bool = False,                # Art. 30c — MRV in place
        monitoring_plan_submitted: bool = False,     # Art. 30c §2 — by 01 Jan 2025
        has_registry_account: bool = False,          # Art. 30d — registry entry
        has_verified_emissions_report: bool = False, # Art. 30e — verified report
        fuel_volume_data_quality: str = "estimated", # "measured"|"calculated"|"estimated"
    ) -> ETS2ReadinessResult:
        """Assess readiness for ETS2 (buildings/transport from 2027).

        Enhanced (E8):
        - Resolves emission factor from ETS2_EMISSION_FACTORS table per fuel type
        - Calculates allowance cost at Art. 30d price corridor floor AND ceiling
        - Scores compliance readiness from 5 weighted factors (100-point scale)
        - Distinguishes road (85% pass-through) vs. heating (70%) fuel categories
        - Returns compliance calendar deadlines from ETS2_COMPLIANCE_CALENDAR
        """
        # ── 1. Emission factor resolution ──────────────────────────────────
        ef_data = self.ETS2_EMISSION_FACTORS.get(fuel_type, {})
        ets2_covered = bool(ef_data) and ef_data.get("ets2_covered", False)

        if emission_factor_kgco2_per_litre and emission_factor_kgco2_per_litre > 0:
            ef_per_litre = emission_factor_kgco2_per_litre
        elif ef_data.get("ef_kgco2_per_litre", 0) > 0:
            ef_per_litre = ef_data["ef_kgco2_per_litre"]
        else:
            ef_per_litre = 2.31  # fallback diesel default

        # Gaseous fuels may be metered by kg/m³ — use whichever volume is non-zero
        if annual_fuel_volume_litres > 0:
            annual_emissions = annual_fuel_volume_litres * ef_per_litre / 1000  # tCO2
        elif annual_fuel_volume_kg > 0 and ef_data.get("ef_kgco2_per_kg", 0) > 0:
            annual_emissions = annual_fuel_volume_kg * ef_data["ef_kgco2_per_kg"] / 1000
        else:
            annual_emissions = 0.0

        # ── 2. Price corridor cost range (Art. 30d) ─────────────────────
        current_year = 2026
        corridor = self.ETS2_PRICE_CORRIDOR.get(
            max(k for k in self.ETS2_PRICE_CORRIDOR if k <= max(current_year, 2027)),
            {"floor": 45.0, "ceiling": 60.0}
        )
        allowance_cost_floor   = annual_emissions * corridor["floor"]
        allowance_cost_ceiling = annual_emissions * corridor["ceiling"]
        allowance_cost         = annual_emissions * max(carbon_price_eur, corridor["floor"])

        # ── 3. Pass-through potential by fuel category ────────────────────
        road_fuels    = {"diesel", "petrol", "lpg", "cng", "biofuel_blend", "e_fuel"}
        heating_fuels = {"heating_oil", "natural_gas", "kerosene", "heavy_fuel_oil"}
        if fuel_type in road_fuels:
            pass_through = 85.0   # road transport — competitive retail market
        elif fuel_type in heating_fuels:
            pass_through = 70.0   # heating — longer-term supply contracts
        else:
            pass_through = 60.0   # unknown — conservative

        consumer_impact = (carbon_price_eur * ef_per_litre / 1000)

        # ── 4. Compliance readiness scoring (100-point) ──────────────────
        # Factor weights: MRV 25, monitoring plan 20, registry 20, verified report 20, data quality 15
        readiness = 100.0
        gaps = []

        if not has_mrv_system:
            readiness -= 25.0
            gaps.append("No MRV system — Art. 30c monitoring plan required by 01 Jan 2025")
        if not monitoring_plan_submitted:
            readiness -= 20.0
            gaps.append("Monitoring plan not submitted to competent authority (Art. 30c §2)")
        if not has_registry_account:
            readiness -= 20.0
            gaps.append("No registry account — must register before first surrender deadline 31 May 2028")
        if not has_verified_emissions_report:
            readiness -= 20.0
            gaps.append("No verified emissions report — accredited verifier required (Art. 30e)")
        if fuel_volume_data_quality == "estimated":
            readiness -= 15.0
            gaps.append("Fuel volume based on estimates — upgrade to metered/calculated data (Tier 1+)")
        elif fuel_volume_data_quality == "calculated":
            readiness -= 5.0   # minor deduction for non-metered

        if annual_fuel_volume_litres <= 0 and annual_fuel_volume_kg <= 0:
            gaps.append("Fuel volume data missing — cannot calculate emissions or allowance cost")

        if not ets2_covered:
            gaps.append(f"Fuel type '{fuel_type}' may not be ETS2-covered under Annex III")

        readiness = max(0.0, readiness)

        # ── 5. Recommendations ───────────────────────────────────────────
        recs = []
        cal = self.ETS2_COMPLIANCE_CALENDAR
        if not has_mrv_system:
            recs.append(
                f"Implement MRV system immediately — monitoring plan deadline: "
                f"{cal.get('monitoring_plan_deadline', '2025-01-01')} (Art. 30c)"
            )
        if not has_registry_account:
            recs.append(
                f"Open ETS2 registry account before first surrender: "
                f"{cal.get('first_surrender_deadline', '2028-05-31')} (Art. 30d)"
            )
        if not has_verified_emissions_report:
            recs.append("Engage accredited verifier for annual emissions report (Art. 30e §3)")
        if allowance_cost_ceiling > 1_000_000:
            recs.append(
                f"Material allowance cost — floor €{allowance_cost_floor:,.0f} / "
                f"ceiling €{allowance_cost_ceiling:,.0f} — evaluate hedging via EUA futures"
            )
        if pass_through >= 85.0:
            recs.append("Road fuel pass-through ~85% achievable — update consumer price models for 2027")
        else:
            recs.append("Heating fuel pass-through ~70% — longer contract renegotiation cycles; plan ahead")
        recs.append(
            f"ETS2 goes live {cal.get('ets2_start', '2027-01-01')} — "
            f"price corridor €{corridor['floor']}–€{corridor['ceiling']}/tCO₂ (Art. 30d)"
        )

        return ETS2ReadinessResult(
            entity_id=entity_id,
            entity_name=entity_name,
            ets2_eligible=ets2_covered,
            fuel_type=fuel_type,
            annual_emissions_tco2=round(annual_emissions, 2),
            estimated_allowance_cost_eur=round(allowance_cost, 2),
            pass_through_potential_pct=pass_through,
            consumer_impact_eur_per_litre=round(consumer_impact, 4),
            readiness_score=round(readiness, 1),
            gaps=gaps,
            recommendations=recs,
        )

    # ── Utility / Reference ───────────────────────────────────────────────

    @staticmethod
    def get_product_benchmarks() -> dict:
        """
        Return product benchmarks as a flat dict for API reference endpoints.

        GAP-012: Prefers live DB values for the current allocation period
        (2026-2030 if today >= 2026-01-01, else 2021-2025).
        Falls back to the hardcoded PRODUCT_BENCHMARKS dict if the DB query
        fails or the table doesn't exist yet.
        """
        today = date.today()
        period_start = 2026 if today >= date(2026, 1, 1) else 2021

        try:
            from db.base import engine as db_engine
            from sqlalchemy import text

            with db_engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT product_key, product_name, benchmark_value, unit,
                           period_start, period_end, annual_reduction,
                           source_decision, cbam_overlap
                    FROM   ets_product_benchmarks
                    WHERE  period_start = :ps
                    ORDER  BY product_key
                """), {"ps": period_start}).fetchall()

            if rows:
                result: dict = {}
                for r in rows:
                    result[r.product_key] = {
                        "benchmark_value": float(r.benchmark_value),
                        # Keep legacy key names so existing callers don't break
                        "benchmark_2021": float(r.benchmark_value),
                        "annual_reduction": float(r.annual_reduction or 0),
                        "unit": r.unit,
                        "product_name": r.product_name,
                        "period": f"{r.period_start}-{r.period_end}",
                        "source_decision": r.source_decision,
                        "cbam_overlap": bool(r.cbam_overlap),
                    }
                logger.debug(
                    "EUETSEngine: loaded %d benchmarks from DB (period %d)",
                    len(result), period_start,
                )
                return result

        except Exception as exc:
            logger.debug("EUETSEngine: DB benchmark lookup failed — using hardcoded fallback: %s", exc)

        # Fallback: return hardcoded 2021-2025 values
        return PRODUCT_BENCHMARKS

    @staticmethod
    def get_product_benchmarks_all_periods() -> list[dict]:
        """
        Return all benchmark rows across all allocation periods for the
        reference-data endpoint (/api/v1/eu-ets/ref/benchmarks/all).
        """
        try:
            from db.base import engine as db_engine
            from sqlalchemy import text

            with db_engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT product_key, product_name, benchmark_value, unit,
                           period_start, period_end, annual_reduction,
                           source_decision, source_article, cbam_overlap,
                           valid_from, valid_to
                    FROM   ets_product_benchmarks
                    ORDER  BY period_start, product_key
                """)).fetchall()

            return [
                {
                    "product_key": r.product_key,
                    "product_name": r.product_name,
                    "benchmark_value": float(r.benchmark_value),
                    "unit": r.unit,
                    "period": f"{r.period_start}-{r.period_end}",
                    "annual_reduction": float(r.annual_reduction or 0),
                    "source_decision": r.source_decision,
                    "source_article": r.source_article,
                    "cbam_overlap": bool(r.cbam_overlap),
                    "valid_from": r.valid_from.isoformat() if r.valid_from else None,
                    "valid_to": r.valid_to.isoformat() if r.valid_to else None,
                }
                for r in rows
            ]
        except Exception as exc:
            logger.debug("EUETSEngine: get_product_benchmarks_all_periods DB error: %s", exc)
            # Return the hardcoded values wrapped in a list
            return [
                {
                    "product_key": k,
                    "product_name": k.replace("_", " ").title(),
                    "benchmark_value": v["benchmark_2021"],
                    "unit": v["unit"],
                    "period": "2021-2025",
                    "annual_reduction": v["annual_reduction"],
                    "source_decision": "Decision (EU) 2021/927",
                    "source_article": "Annex I",
                    "cbam_overlap": k in ("hot_metal", "cement_clinker", "aluminium", "ammonia", "hydrogen"),
                    "valid_from": "2021-01-01",
                    "valid_to": "2025-12-31",
                }
                for k, v in PRODUCT_BENCHMARKS.items()
            ]

    @staticmethod
    def get_carbon_price_scenarios() -> dict:
        return CARBON_PRICE_SCENARIOS

    @staticmethod
    def get_cbam_phaseout_schedule() -> dict:
        return CBAM_FREE_ALLOCATION_PHASEOUT

    @staticmethod
    def get_ets_cap_parameters() -> dict:
        return ETS_CAP_PARAMETERS

    @staticmethod
    def get_carbon_leakage_tiers() -> dict:
        return CARBON_LEAKAGE_TIERS
