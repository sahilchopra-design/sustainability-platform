"""
Just Transition Calculator
Aligned with: ILO Just Transition Guidelines (2015), Climate Investment Funds (CIF),
              WBG Just Transition Framework, IRENA World Energy Transitions Outlook 2023

Computes:
  - Job displacement (direct + indirect + induced) from fossil fuel phase-out
  - Green job creation (RE + efficiency + grid + hydrogen)
  - Net employment delta
  - Social cost of transition (retraining, income support, community investment)
  - Regional economic impact (GDP exposure, community dependency)
  - Transition compensation needed for affected workers

Reference multipliers:
  - ILO 2023: Coal sector employment multiplier (total jobs per direct job) ≈ 3.2x
  - IRENA 2023: Renewable energy jobs per MW installed (solar: 7.5, wind: 5.8, hydro: 3.2)
  - World Bank 2022: Average retraining cost per worker (LIC $4k, MIC $12k, HIC $28k)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# ── Employment Multipliers (total jobs per direct job) ── ILO / IRENA
EMPLOYMENT_MULTIPLIERS: Dict[str, float] = {
    "coal_mining": 3.2,
    "oil_gas": 2.8,
    "coal_power": 2.5,
    "natural_gas_power": 2.2,
    "refinery": 3.0,
}

# Green jobs per MW installed (IRENA 2023, operations + construction average)
GREEN_JOBS_PER_MW: Dict[str, float] = {
    "solar_pv": 7.5,
    "onshore_wind": 5.8,
    "offshore_wind": 8.2,
    "hydro": 3.2,
    "geothermal": 4.0,
    "green_hydrogen": 12.0,   # entire value chain per MW electrolyser
    "energy_efficiency": 15.0, # per MW equivalent saved
    "grid_modernisation": 6.0,
}

# Income support cost per worker per year (USD, World Bank income groups)
INCOME_SUPPORT_ANNUAL: Dict[str, float] = {
    "HIC": 18_000,   # High income
    "UMC": 9_000,    # Upper middle income
    "LMC": 4_500,    # Lower middle income
    "LIC": 2_000,    # Low income
}

# Retraining cost per worker (USD)
RETRAINING_COST: Dict[str, float] = {
    "HIC": 28_000,
    "UMC": 12_000,
    "LMC": 6_000,
    "LIC": 4_000,
}

# Average fossil fuel worker wage (USD/yr, World Bank)
AVG_FOSSIL_WAGE: Dict[str, float] = {
    "HIC": 72_000,
    "UMC": 28_000,
    "LMC": 12_000,
    "LIC": 5_000,
}

# Community investment multiplier (USD per displaced worker for community infrastructure)
COMMUNITY_INVEST_MULTIPLIER: Dict[str, float] = {
    "HIC": 40_000, "UMC": 15_000, "LMC": 7_000, "LIC": 3_000,
}


@dataclass
class JustTransitionInput:
    region_name: str
    country_income_group: str                      # HIC | UMC | LMC | LIC
    fossil_sector: str                             # coal_mining | oil_gas | coal_power | natural_gas_power
    direct_fossil_jobs: int
    capacity_mw: Optional[float] = None            # MW of fossil capacity being retired
    transition_years: int = 10                     # planned phase-out period
    # Planned green investment
    planned_re_mw: float = 0.0                     # renewable MW planned in region
    re_technology: str = "solar_pv"
    planned_ee_mw_equiv: float = 0.0               # energy efficiency MW-equivalent
    planned_grid_mw: float = 0.0                   # grid infrastructure MW
    planned_h2_mw: float = 0.0                     # green hydrogen electrolyser MW
    # Policy levers
    income_support_years: int = 3                  # years of income support
    retraining_coverage_pct: float = 0.75          # % of displaced workers retrained
    community_investment_included: bool = True
    # Social context
    community_dependency_pct: float = 0.6          # fraction of local GDP from fossil sector
    just_transition_fund_usd: float = 0.0          # external fund already committed


@dataclass
class JustTransitionResult:
    region_name: str

    # Employment
    direct_displaced_jobs: int
    total_displaced_jobs: int                      # includes multiplier effect
    green_jobs_created: int
    net_employment_delta: int
    jobs_gap: int                                  # positive = shortfall

    # Social costs (USD)
    income_support_cost_usd: float
    retraining_cost_usd: float
    community_investment_usd: float
    total_social_cost_usd: float

    # Financing gap
    just_transition_fund_gap_usd: float            # social cost - existing fund
    cost_per_displaced_worker_usd: float

    # Economic impact
    annual_wage_bill_lost_usd: float
    gdp_exposure_pct: float                        # community dependency × regional GDP proxy

    # Summary
    transition_feasibility: str                    # feasible | challenging | high_risk
    narrative: str
    annual_green_jobs_ramp: List[Dict]             # year-by-year job creation ramp


def calculate_just_transition(inp: JustTransitionInput) -> JustTransitionResult:
    ig = inp.country_income_group.upper()
    if ig not in INCOME_SUPPORT_ANNUAL:
        ig = "UMC"

    mult = EMPLOYMENT_MULTIPLIERS.get(inp.fossil_sector, 2.5)
    direct = inp.direct_fossil_jobs
    total_displaced = int(direct * mult)

    # Green job creation
    green_jobs = 0
    if inp.planned_re_mw > 0:
        green_jobs += int(inp.planned_re_mw * GREEN_JOBS_PER_MW.get(inp.re_technology, 7.0))
    if inp.planned_ee_mw_equiv > 0:
        green_jobs += int(inp.planned_ee_mw_equiv * GREEN_JOBS_PER_MW["energy_efficiency"])
    if inp.planned_grid_mw > 0:
        green_jobs += int(inp.planned_grid_mw * GREEN_JOBS_PER_MW["grid_modernisation"])
    if inp.planned_h2_mw > 0:
        green_jobs += int(inp.planned_h2_mw * GREEN_JOBS_PER_MW["green_hydrogen"])

    net_delta = green_jobs - total_displaced
    jobs_gap = max(0, total_displaced - green_jobs)

    # Social cost calculation
    displaced = total_displaced
    income_support = (
        INCOME_SUPPORT_ANNUAL[ig]
        * inp.income_support_years
        * displaced
    )
    retrain_workers = int(displaced * inp.retraining_coverage_pct)
    retraining_cost = RETRAINING_COST[ig] * retrain_workers

    community_invest = (
        COMMUNITY_INVEST_MULTIPLIER[ig] * displaced
        if inp.community_investment_included else 0.0
    )

    total_social_cost = income_support + retraining_cost + community_invest
    fund_gap = max(0, total_social_cost - inp.just_transition_fund_usd)
    cost_per_worker = total_social_cost / displaced if displaced > 0 else 0.0

    # Wage bill impact
    annual_wage = AVG_FOSSIL_WAGE[ig] * direct
    gdp_exposure = inp.community_dependency_pct * 100  # % of local GDP at risk

    # Feasibility assessment
    replacement_ratio = green_jobs / total_displaced if total_displaced > 0 else 0
    if replacement_ratio >= 0.9 and fund_gap < total_social_cost * 0.3:
        feasibility = "feasible"
    elif replacement_ratio >= 0.6 or fund_gap < total_social_cost * 0.6:
        feasibility = "challenging"
    else:
        feasibility = "high_risk"

    # Annual ramp (sigmoid-like)
    annual_ramp = []
    for yr in range(1, inp.transition_years + 1):
        # Jobs lost: linear phase-out
        jobs_lost_yr = int(total_displaced * (yr / inp.transition_years))
        # Green jobs: assume S-curve (slow start, fast middle, plateau)
        progress = yr / inp.transition_years
        sigmoid = 1 / (1 + math.exp(-10 * (progress - 0.5)))
        green_yr = int(green_jobs * sigmoid)
        annual_ramp.append({
            "year": 2024 + yr,
            "cumulative_displaced": jobs_lost_yr,
            "cumulative_green_created": green_yr,
            "net_gap": max(0, jobs_lost_yr - green_yr),
        })

    narrative_parts = [
        f"{inp.region_name}: {total_displaced:,} total jobs at risk ({direct:,} direct × {mult}x multiplier) over {inp.transition_years} years. ",
        f"Planned green investment creates {green_jobs:,} new jobs (net delta: {'+' if net_delta >= 0 else ''}{net_delta:,}). ",
        f"Total just transition cost: USD {total_social_cost/1e6:.1f}M (income support: {income_support/1e6:.1f}M + retraining: {retraining_cost/1e6:.1f}M). ",
    ]
    if fund_gap > 0:
        narrative_parts.append(f"Financing gap: USD {fund_gap/1e6:.1f}M vs committed fund. ")
    narrative_parts.append(f"Assessment: {feasibility.replace('_', ' ').upper()}.")
    narrative = "".join(narrative_parts)

    return JustTransitionResult(
        region_name=inp.region_name,
        direct_displaced_jobs=direct,
        total_displaced_jobs=total_displaced,
        green_jobs_created=green_jobs,
        net_employment_delta=net_delta,
        jobs_gap=jobs_gap,
        income_support_cost_usd=income_support,
        retraining_cost_usd=retraining_cost,
        community_investment_usd=community_invest,
        total_social_cost_usd=total_social_cost,
        just_transition_fund_gap_usd=fund_gap,
        cost_per_displaced_worker_usd=cost_per_worker,
        annual_wage_bill_lost_usd=annual_wage,
        gdp_exposure_pct=gdp_exposure,
        transition_feasibility=feasibility,
        narrative=narrative,
        annual_green_jobs_ramp=annual_ramp,
    )


# ETM (Energy Transition Mechanism) Calculator
# Source: ADB/AIIB/Citi ETM Framework, 2022
# Early retirement of coal plants via debt buyout + concessional refinancing

@dataclass
class ETMInput:
    plant_name: str
    plant_country: str
    capacity_mw: float
    remaining_useful_life_years: int              # without ETM
    early_retirement_year: int                    # planned
    current_year: int = 2024
    # Financial parameters
    outstanding_debt_usd_m: float = 0.0          # coal plant outstanding debt
    equity_book_value_usd_m: float = 0.0
    offtake_tariff_usd_per_mwh: float = 65.0     # current PPA tariff
    capacity_factor_pct: float = 0.6
    # Cost of capital
    incumbent_wacc_pct: float = 12.0             # % pa, blended COC
    etm_refinance_rate_pct: float = 4.5          # concessional rate under ETM
    # ETM structure
    etm_tranche_pct: float = 0.6                 # % of debt taken out by ETM SPV
    # RE replacement
    re_replacement_mw: float = 0.0               # RE built in place
    re_capex_usd_per_mw: float = 800_000.0       # USD/MW for RE replacement
    re_lcoe_usd_per_mwh: float = 35.0


@dataclass
class ETMResult:
    plant_name: str
    years_early_retirement: int                  # YEL = early_retirement - current
    stranded_asset_value_usd_m: float           # NPV of lost future cash flows
    etm_debt_buyout_usd_m: float               # debt portion taken by ETM SPV
    concessional_savings_usd_m: float          # interest savings from refinancing
    equity_compensation_usd_m: float           # equity investor compensation
    total_etm_cost_usd_m: float               # total public/blended finance needed
    re_replacement_capex_usd_m: float
    avoided_co2_mt: float                      # megatonnes CO2 avoided
    co2_abatement_cost_usd_per_tco2: float   # $/tCO2 (total ETM cost / avoided CO2)
    npv_saving_vs_natural_retirement: float   # NPV saving of early vs natural
    feasibility: str                          # viable | marginal | unviable
    narrative: str


_CO2_EF_COAL = 0.88  # tCO2/MWh (IEA average coal plant)


def calculate_etm(inp: ETMInput) -> ETMResult:
    years_early = max(0, inp.early_retirement_year - inp.current_year)
    remaining = inp.remaining_useful_life_years
    early_years = min(remaining, remaining - years_early)  # years actually shortened

    # Annual generation
    annual_mwh = inp.capacity_mw * 8760 * (inp.capacity_factor_pct / 100)

    # Annual revenue (PPA tariff)
    annual_revenue = annual_mwh * inp.offtake_tariff_usd_per_mwh / 1e6  # USD M

    # Stranded asset NPV — NPV of lost future revenues for early_years
    r = inp.incumbent_wacc_pct / 100
    if r > 0 and years_early > 0:
        npv_lost = annual_revenue * (1 - (1 + r) ** (-years_early)) / r
    else:
        npv_lost = annual_revenue * years_early

    # ETM debt buyout
    etm_debt = inp.outstanding_debt_usd_m * inp.etm_tranche_pct

    # Concessional savings (interest differential × remaining loan tenor)
    rate_diff = (inp.incumbent_wacc_pct - inp.etm_refinance_rate_pct) / 100
    avg_loan_tenor = min(remaining, 15)  # assume max 15y remaining
    concessional_savings = etm_debt * rate_diff * avg_loan_tenor

    # Equity compensation
    equity_comp = inp.equity_book_value_usd_m * 0.60  # typically 60% book buyout

    # RE replacement capex
    re_capex = inp.re_replacement_mw * inp.re_capex_usd_per_mw / 1e6  # USD M

    # Total ETM cost
    total_etm = etm_debt + equity_comp + re_capex

    # Avoided CO2
    avoided_co2_mt = (annual_mwh * years_early * _CO2_EF_COAL) / 1e6  # megatonnes

    # Abatement cost
    abatement_cost = (total_etm * 1e6) / (avoided_co2_mt * 1e6) if avoided_co2_mt > 0 else 0

    # NPV saving vs natural retirement (value of earlier decarbonisation)
    # Assume social cost of carbon $80/tCO2 (WB 2023 SCC)
    scc = 80.0  # USD/tCO2
    npv_saving = avoided_co2_mt * 1e6 * scc / 1e6 - total_etm  # USD M

    if abatement_cost < 80:
        feasibility = "viable"
    elif abatement_cost < 150:
        feasibility = "marginal"
    else:
        feasibility = "unviable"

    narrative = (
        f"{inp.plant_name} ({inp.capacity_mw:.0f} MW): ETM structure closes {years_early} years early. "
        f"Stranded value NPV: USD {npv_lost:.1f}M. "
        f"ETM package: debt buyout USD {etm_debt:.1f}M + equity USD {equity_comp:.1f}M + RE USD {re_capex:.1f}M = USD {total_etm:.1f}M total. "
        f"Avoided CO₂: {avoided_co2_mt:.2f} Mt — abatement cost USD {abatement_cost:.0f}/tCO₂. "
        f"Feasibility: {feasibility.upper()}."
    )

    return ETMResult(
        plant_name=inp.plant_name,
        years_early_retirement=years_early,
        stranded_asset_value_usd_m=round(npv_lost, 2),
        etm_debt_buyout_usd_m=round(etm_debt, 2),
        concessional_savings_usd_m=round(concessional_savings, 2),
        equity_compensation_usd_m=round(equity_comp, 2),
        total_etm_cost_usd_m=round(total_etm, 2),
        re_replacement_capex_usd_m=round(re_capex, 2),
        avoided_co2_mt=round(avoided_co2_mt, 3),
        co2_abatement_cost_usd_per_tco2=round(abatement_cost, 1),
        npv_saving_vs_natural_retirement=round(npv_saving, 2),
        feasibility=feasibility,
        narrative=narrative,
    )
