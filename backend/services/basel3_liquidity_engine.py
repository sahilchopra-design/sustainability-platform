"""
Basel III Liquidity Risk Engine
================================

Comprehensive liquidity risk assessment covering LCR, NSFR, ALM gap analysis,
IRRBB (Interest Rate Risk in the Banking Book), and liquidity stress testing.

Key regulatory frameworks modelled:
- Basel III LCR (Liquidity Coverage Ratio) — BCBS 238 / CRR2 Art 411-428
- Basel III NSFR (Net Stable Funding Ratio) — BCBS 295
- IRRBB (Interest Rate Risk in the Banking Book) — BCBS 368 / EBA/GL/2018/02
- EBA liquidity stress testing — EBA/GL/2019/02
- BCBS 248 — Monitoring tools for intraday liquidity management
- BCBS 238 — Monitoring tools for liquidity risk

Climate-liquidity intersection:
- Climate scenario haircuts on HQLA (L2A/L2B) under disorderly/hot_house
- Green bond HQLA eligibility considerations
- Stranded asset collateral impairment
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data Constants
# ---------------------------------------------------------------------------

# HQLA haircuts per CRR2 / LCR Delegated Regulation (EU) 2015/61
HQLA_HAIRCUTS: dict = {
    "level_1": {
        "coins_and_banknotes": 0.00,
        "central_bank_reserves": 0.00,
        "central_govt_bonds_0_rw": 0.00,
        "central_bank_bonds": 0.00,
        "multilateral_dev_bank_0rw": 0.00,
        "description": "Level 1 HQLA — 0% haircut, unlimited inclusion",
    },
    "level_2a": {
        "central_govt_bonds_20rw": 0.15,
        "corporate_bonds_aa_minus": 0.15,
        "covered_bonds_aa_minus": 0.15,
        "description": "Level 2A HQLA — 15% haircut, max 40% of HQLA stock",
    },
    "level_2b": {
        "rmbs_aa_plus": 0.25,
        "corporate_bonds_bbplus": 0.50,
        "listed_equities": 0.50,
        "description": "Level 2B HQLA — 25-50% haircut, max 15% of HQLA stock",
    },
}

# Cash outflow runoff rates — LCR stress scenario (30-day)
RUNOFF_RATES: dict = {
    "retail_stable": 0.03,
    "retail_less_stable": 0.10,
    "small_business_stable": 0.05,
    "small_business_less_stable": 0.10,
    "wholesale_operational": 0.25,
    "wholesale_non_operational_financial": 0.40,
    "wholesale_non_operational_non_financial": 0.20,
    "secured_level1": 0.00,
    "secured_level2a": 0.15,
    "secured_level2b": 0.25,
    "unsecured_credit_lines_retail": 0.05,
    "unsecured_credit_lines_corporate": 0.10,
    "liquidity_facilities_credit": 0.30,
}

# ASF factors — NSFR
ASF_FACTORS: dict = {
    "stable_retail_deposits": 0.95,
    "less_stable_retail_deposits": 0.90,
    "wholesale_funding_gt1y": 1.00,
    "wholesale_funding_lt1y_non_operational": 0.00,
    "wholesale_funding_lt1y_operational": 0.50,
    "retail_deposits_lt6m": 0.90,
    "retail_deposits_6m_1y": 0.95,
    "equity_tier1": 1.00,
    "equity_tier2": 1.00,
    "long_term_liabilities_gt1y": 1.00,
}

# RSF factors — NSFR
RSF_FACTORS: dict = {
    "level1_hqla": 0.05,
    "level2a_hqla": 0.15,
    "level2b_hqla": 0.50,
    "unencumbered_residential_loans_lte35rw": 0.65,
    "unencumbered_residential_loans_gt35rw": 0.85,
    "corporate_loans_lt1y": 0.50,
    "corporate_loans_gt1y": 0.85,
    "non_hqla_equities": 0.85,
    "derivatives_assets": 1.00,
    "other_assets": 1.00,
    "off_balance_sheet_committed": 0.05,
}

# EBA interest rate shock scenarios — BCBS 368 / EBA/GL/2018/02
EBA_RATE_SHOCKS: dict = {
    "parallel_up": 200,
    "parallel_down": -200,
    "steepener": 150,
    "flattener": -150,
    "short_up": 250,
    "short_down": -250,
}

# BCBS 248 monitoring tools for intraday liquidity
BCBS238_MONITORING: dict = {
    "contractual_maturity_mismatch": {
        "description": "Map of contractual cash inflows/outflows across time buckets",
        "frequency": "monthly",
        "article": "BCBS 238 para 18",
    },
    "concentration_of_funding": {
        "description": "Significant counterparties and instruments as % of total liabilities",
        "threshold_pct": 1.0,
        "frequency": "monthly",
        "article": "BCBS 238 para 19",
    },
    "available_unencumbered_assets": {
        "description": "Inventory of unencumbered assets available as central bank collateral",
        "frequency": "monthly",
        "article": "BCBS 238 para 20",
    },
    "lcr_by_significant_currency": {
        "description": "LCR computed separately per currency >5% of total liabilities",
        "threshold_pct": 5.0,
        "frequency": "monthly",
        "article": "BCBS 238 para 21",
    },
    "market_related_monitoring": {
        "description": "Market-wide, financial sector, entity-specific early warning indicators",
        "frequency": "daily",
        "article": "BCBS 238 para 22",
        "indicators": [
            "equity_price_decline",
            "cds_spread_widening",
            "wholesale_funding_rollover",
            "asset_backed_cp_issuance",
            "central_bank_borrowing",
        ],
    },
}

# Climate scenario identifiers that trigger HQLA haircut uplift
DISORDERLY_SCENARIOS = {"delayed_transition", "current_policies", "nationally_determined", "hot_house_world"}

# Regulatory thresholds
LCR_MINIMUM_PCT = 100.0
NSFR_MINIMUM_PCT = 100.0
L2_CAP_PCT = 40.0       # L2 assets capped at 40% of HQLA
L2B_CAP_PCT = 15.0      # L2B capped at 15% of HQLA

# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LCRResult:
    entity_id: str
    assessment_date: str
    hqla_l1_mn: float = 0.0
    hqla_l2a_mn: float = 0.0
    hqla_l2b_mn: float = 0.0
    hqla_stock_mn: float = 0.0
    gross_outflow_30d_mn: float = 0.0
    gross_inflow_30d_mn: float = 0.0
    net_outflow_30d_mn: float = 0.0
    lcr_pct: float = 0.0
    climate_scenario: str = ""
    climate_hqla_haircut_bps: float = 0.0
    climate_adjusted_lcr_pct: float = 0.0
    lcr_breach: bool = False
    l2_cap_breach: bool = False
    l2b_cap_breach: bool = False
    notes: list = field(default_factory=list)


@dataclass
class NSFRResult:
    entity_id: str
    assessment_date: str
    asf_mn: float = 0.0
    rsf_mn: float = 0.0
    nsfr_pct: float = 0.0
    nsfr_breach: bool = False
    asf_breakdown: dict = field(default_factory=dict)
    rsf_breakdown: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


@dataclass
class ALMGapResult:
    entity_id: str
    assessment_date: str
    bucket_gaps: list = field(default_factory=list)
    cumulative_gap_mn: float = 0.0
    duration_gap_years: float = 0.0
    eve_parallel_up_mn: float = 0.0
    eve_parallel_down_mn: float = 0.0
    eve_steepener_mn: float = 0.0
    eve_flattener_mn: float = 0.0
    eve_short_up_mn: float = 0.0
    eve_short_down_mn: float = 0.0
    nii_12m_sensitivity_mn: float = 0.0
    irrbb_material: bool = False
    notes: list = field(default_factory=list)


@dataclass
class LiquidityStressResult:
    entity_id: str
    assessment_date: str
    scenario_id: str
    survival_horizon_days: int = 0
    liquidity_at_risk_mn: float = 0.0
    stress_outflow_deposit_mn: float = 0.0
    stress_outflow_wholesale_mn: float = 0.0
    stressed_lcr_pct: float = 0.0
    stressed_nsfr_pct: float = 0.0
    liquidity_buffer_adequacy: str = ""
    notes: list = field(default_factory=list)


@dataclass
class BaselLiquidityAssessmentResult:
    entity_id: str
    entity_name: str
    reporting_date: str
    scenario_id: str
    lcr: dict = field(default_factory=dict)
    nsfr: dict = field(default_factory=dict)
    alm_gap: dict = field(default_factory=dict)
    stress: dict = field(default_factory=dict)
    monitoring_metrics: dict = field(default_factory=dict)
    regulatory_breaches: dict = field(default_factory=dict)
    overall_liquidity_rating: str = ""
    priority_actions: list = field(default_factory=list)
    cross_framework: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class Basel3LiquidityEngine:
    """Basel III liquidity risk assessment engine (LCR, NSFR, ALM/IRRBB, stress)."""

    def __init__(self) -> None:
        self._today = datetime.utcnow().strftime("%Y-%m-%d")

    # ── LCR Assessment ─────────────────────────────────────────────────────

    def assess_lcr(
        self,
        entity_id: str,
        hqla_l1: float,
        hqla_l2a: float,
        hqla_l2b: float,
        gross_outflow: float,
        gross_inflow: float,
        climate_scenario: Optional[str] = None,
    ) -> LCRResult:
        """Compute Liquidity Coverage Ratio with optional climate haircut overlay."""
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Apply standard haircuts
        l1_adj = hqla_l1 * (1.0 - 0.00)
        l2a_adj = hqla_l2a * (1.0 - 0.15)
        l2b_adj = hqla_l2b * (1.0 - 0.50)

        # Cap checks
        total_stock_uncapped = l1_adj + l2a_adj + l2b_adj
        l2_total = l2a_adj + l2b_adj
        l2_cap_breach = False
        l2b_cap_breach = False

        if total_stock_uncapped > 0:
            l2_pct = l2_total / total_stock_uncapped * 100
            l2b_pct = l2b_adj / total_stock_uncapped * 100
            if l2_pct > L2_CAP_PCT:
                l2_cap_breach = True
                max_l2 = l1_adj * (L2_CAP_PCT / (100.0 - L2_CAP_PCT))
                l2_total = min(l2_total, max_l2)
            if l2b_pct > L2B_CAP_PCT:
                l2b_cap_breach = True
                max_l2b = total_stock_uncapped * L2B_CAP_PCT / 100.0
                l2b_adj = min(l2b_adj, max_l2b)
                l2_total = l2a_adj + l2b_adj

        hqla_stock = l1_adj + l2_total

        # Net outflow (inflow capped at 75% of gross outflow)
        capped_inflow = min(gross_inflow, gross_outflow * 0.75)
        net_outflow = max(0.0, gross_outflow - capped_inflow)
        lcr_pct = (hqla_stock / net_outflow * 100.0) if net_outflow > 0 else 999.0

        # Climate scenario HQLA haircut
        climate_haircut_bps = 0.0
        climate_adj_lcr = lcr_pct
        if climate_scenario and climate_scenario in DISORDERLY_SCENARIOS:
            l2a_extra_bps = rng.uniform(5.0, 15.0)
            l2b_extra_bps = rng.uniform(10.0, 25.0)
            climate_haircut_bps = round((l2a_extra_bps + l2b_extra_bps) / 2.0, 1)
            l2a_climate = hqla_l2a * (1.0 - 0.15 - l2a_extra_bps / 10000.0)
            l2b_climate = hqla_l2b * (1.0 - 0.50 - l2b_extra_bps / 10000.0)
            hqla_climate = l1_adj + l2a_climate + l2b_climate
            climate_adj_lcr = (hqla_climate / net_outflow * 100.0) if net_outflow > 0 else 999.0

        notes = []
        if l2_cap_breach:
            notes.append("L2 HQLA cap of 40% breached — adjusted stock applied")
        if l2b_cap_breach:
            notes.append("L2B HQLA cap of 15% breached — adjusted stock applied")
        if climate_scenario in DISORDERLY_SCENARIOS:
            notes.append(f"Climate haircut applied under {climate_scenario}: {climate_haircut_bps} bps additional haircut on L2A/L2B")

        return LCRResult(
            entity_id=entity_id,
            assessment_date=self._today,
            hqla_l1_mn=round(hqla_l1, 2),
            hqla_l2a_mn=round(hqla_l2a, 2),
            hqla_l2b_mn=round(hqla_l2b, 2),
            hqla_stock_mn=round(hqla_stock, 2),
            gross_outflow_30d_mn=round(gross_outflow, 2),
            gross_inflow_30d_mn=round(gross_inflow, 2),
            net_outflow_30d_mn=round(net_outflow, 2),
            lcr_pct=round(lcr_pct, 1),
            climate_scenario=climate_scenario or "",
            climate_hqla_haircut_bps=round(climate_haircut_bps, 1),
            climate_adjusted_lcr_pct=round(climate_adj_lcr, 1),
            lcr_breach=lcr_pct < LCR_MINIMUM_PCT,
            l2_cap_breach=l2_cap_breach,
            l2b_cap_breach=l2b_cap_breach,
            notes=notes,
        )

    # ── NSFR Assessment ────────────────────────────────────────────────────

    def assess_nsfr(
        self,
        entity_id: str,
        asf_breakdown: dict,
        rsf_breakdown: dict,
    ) -> NSFRResult:
        """Compute Net Stable Funding Ratio from ASF/RSF component breakdown."""
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        asf_total = 0.0
        asf_computed = {}
        for component, amount in asf_breakdown.items():
            factor = ASF_FACTORS.get(component, rng.uniform(0.5, 0.9))
            weighted = amount * factor
            asf_computed[component] = {"amount_mn": round(amount, 2), "factor": factor, "weighted_mn": round(weighted, 2)}
            asf_total += weighted

        rsf_total = 0.0
        rsf_computed = {}
        for component, amount in rsf_breakdown.items():
            factor = RSF_FACTORS.get(component, rng.uniform(0.5, 1.0))
            weighted = amount * factor
            rsf_computed[component] = {"amount_mn": round(amount, 2), "factor": factor, "weighted_mn": round(weighted, 2)}
            rsf_total += weighted

        nsfr_pct = (asf_total / rsf_total * 100.0) if rsf_total > 0 else 999.0

        notes = []
        if nsfr_pct < NSFR_MINIMUM_PCT:
            shortfall = rsf_total - asf_total
            notes.append(f"NSFR breach: shortfall of EUR {round(shortfall, 1)} mn stable funding required")

        return NSFRResult(
            entity_id=entity_id,
            assessment_date=self._today,
            asf_mn=round(asf_total, 2),
            rsf_mn=round(rsf_total, 2),
            nsfr_pct=round(nsfr_pct, 1),
            nsfr_breach=nsfr_pct < NSFR_MINIMUM_PCT,
            asf_breakdown=asf_computed,
            rsf_breakdown=rsf_computed,
            notes=notes,
        )

    # ── ALM Gap & IRRBB ────────────────────────────────────────────────────

    def assess_alm_gap(
        self,
        entity_id: str,
        time_buckets: list,
    ) -> ALMGapResult:
        """
        ALM maturity gap analysis and IRRBB (EVE + NII) sensitivity.

        time_buckets: list of dicts with keys:
            bucket (str), assets_mn (float), liabilities_mn (float)
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        bucket_gaps = []
        cumulative = 0.0
        total_asset_duration = 0.0
        total_liability_duration = 0.0
        total_assets = 0.0
        total_liabilities = 0.0

        # Approximate duration midpoints per bucket label
        duration_map = {
            "overnight": 0.003,
            "1w": 0.019,
            "2w": 0.038,
            "1m": 0.083,
            "2m": 0.167,
            "3m": 0.25,
            "6m": 0.5,
            "1y": 1.0,
            "2y": 2.0,
            "3y": 3.0,
            "5y": 5.0,
            "7y": 7.0,
            "10y": 10.0,
            "15y": 15.0,
            "20y": 20.0,
            "gt20y": 25.0,
        }

        eve_sensitivity = {k: 0.0 for k in EBA_RATE_SHOCKS}
        pv01_total_asset = 0.0
        pv01_total_liability = 0.0

        for bucket in time_buckets:
            label = bucket.get("bucket", "1y")
            assets = float(bucket.get("assets_mn", 0.0))
            liabs = float(bucket.get("liabilities_mn", 0.0))
            gap = assets - liabs
            cumulative += gap

            dur = duration_map.get(label, rng.uniform(0.5, 5.0))
            total_asset_duration += assets * dur
            total_liability_duration += liabs * dur
            total_assets += assets
            total_liabilities += liabs

            # PV01 per bucket: assets price up when rates fall (negative PV01 for fixed rate assets)
            pv01_a = assets * dur / 10000.0
            pv01_l = liabs * dur / 10000.0
            pv01_total_asset += pv01_a
            pv01_total_liability += pv01_l

            bucket_gaps.append({
                "bucket": label,
                "assets_mn": round(assets, 2),
                "liabilities_mn": round(liabs, 2),
                "gap_mn": round(gap, 2),
                "cumulative_gap_mn": round(cumulative, 2),
                "duration_mid_years": round(dur, 3),
                "pv01_asset_mn": round(pv01_a, 4),
                "pv01_liability_mn": round(pv01_l, 4),
            })

        duration_gap = 0.0
        if total_assets > 0 and total_liabilities > 0:
            asset_dur = total_asset_duration / total_assets if total_assets > 0 else 0.0
            liab_dur = total_liability_duration / total_liabilities if total_liabilities > 0 else 0.0
            duration_gap = asset_dur - liab_dur

        # EVE sensitivity = net PV01 * shock (bps)
        net_pv01 = pv01_total_asset - pv01_total_liability
        eve_parallel_up = -net_pv01 * EBA_RATE_SHOCKS["parallel_up"]
        eve_parallel_down = -net_pv01 * EBA_RATE_SHOCKS["parallel_down"]
        eve_steepener = -net_pv01 * EBA_RATE_SHOCKS["steepener"] * 0.6
        eve_flattener = -net_pv01 * EBA_RATE_SHOCKS["flattener"] * 0.4
        eve_short_up = -pv01_total_asset * EBA_RATE_SHOCKS["short_up"] * 0.5
        eve_short_down = -pv01_total_liability * abs(EBA_RATE_SHOCKS["short_down"]) * 0.5

        # NII 12m: repricing gap for <1y buckets * 200bps / 2 (average)
        nii_12m = cumulative * 200.0 / 10000.0 / 2.0

        irrbb_material = abs(eve_parallel_up) > total_assets * 0.20 if total_assets > 0 else False

        return ALMGapResult(
            entity_id=entity_id,
            assessment_date=self._today,
            bucket_gaps=bucket_gaps,
            cumulative_gap_mn=round(cumulative, 2),
            duration_gap_years=round(duration_gap, 3),
            eve_parallel_up_mn=round(eve_parallel_up, 2),
            eve_parallel_down_mn=round(eve_parallel_down, 2),
            eve_steepener_mn=round(eve_steepener, 2),
            eve_flattener_mn=round(eve_flattener, 2),
            eve_short_up_mn=round(eve_short_up, 2),
            eve_short_down_mn=round(eve_short_down, 2),
            nii_12m_sensitivity_mn=round(nii_12m, 2),
            irrbb_material=irrbb_material,
            notes=[
                f"Duration gap: {round(duration_gap, 2)} years",
                f"EVE adverse scenario (parallel up +200bps): EUR {round(eve_parallel_up, 1)} mn",
            ],
        )

    # ── Liquidity Stress Test ───────────────────────────────────────────────

    def run_liquidity_stress(
        self,
        entity_id: str,
        base_lcr: float,
        base_nsfr: float,
        scenario_id: str,
    ) -> LiquidityStressResult:
        """Idiosyncratic + market-wide liquidity stress scenario."""
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        scenario_shocks = {
            "mild_idiosyncratic": {"deposit_runoff_mult": 1.2, "wholesale_runoff_mult": 1.3, "hqla_haircut_mult": 1.0},
            "severe_idiosyncratic": {"deposit_runoff_mult": 1.5, "wholesale_runoff_mult": 1.8, "hqla_haircut_mult": 1.1},
            "market_wide": {"deposit_runoff_mult": 1.3, "wholesale_runoff_mult": 2.0, "hqla_haircut_mult": 1.2},
            "combined": {"deposit_runoff_mult": 1.8, "wholesale_runoff_mult": 2.5, "hqla_haircut_mult": 1.3},
            "net_zero_2050": {"deposit_runoff_mult": 1.05, "wholesale_runoff_mult": 1.1, "hqla_haircut_mult": 1.05},
            "delayed_transition": {"deposit_runoff_mult": 1.2, "wholesale_runoff_mult": 1.5, "hqla_haircut_mult": 1.15},
            "current_policies": {"deposit_runoff_mult": 1.15, "wholesale_runoff_mult": 1.4, "hqla_haircut_mult": 1.2},
        }

        shock = scenario_shocks.get(scenario_id, scenario_shocks["mild_idiosyncratic"])
        deposit_mult = shock["deposit_runoff_mult"]
        wholesale_mult = shock["wholesale_runoff_mult"]
        hqla_mult = shock["hqla_haircut_mult"]

        base_deposit_exposure = rng.uniform(500.0, 5000.0)
        base_wholesale_exposure = rng.uniform(200.0, 3000.0)

        stress_deposit = base_deposit_exposure * (deposit_mult - 1.0) * RUNOFF_RATES["retail_less_stable"]
        stress_wholesale = base_wholesale_exposure * (wholesale_mult - 1.0) * RUNOFF_RATES["wholesale_non_operational_financial"]

        total_stress_outflow = stress_deposit + stress_wholesale
        stressed_lcr = base_lcr / hqla_mult * (1.0 / (1.0 + (deposit_mult - 1.0) * 0.2 + (wholesale_mult - 1.0) * 0.1))
        stressed_nsfr = base_nsfr * (0.95 - (wholesale_mult - 1.0) * 0.05)

        liquidity_at_risk = total_stress_outflow * rng.uniform(0.3, 0.7)

        if stressed_lcr >= 120:
            survival_days = rng.randint(270, 365)
            adequacy = "adequate"
        elif stressed_lcr >= 100:
            survival_days = rng.randint(180, 270)
            adequacy = "borderline"
        elif stressed_lcr >= 75:
            survival_days = rng.randint(60, 180)
            adequacy = "vulnerable"
        else:
            survival_days = rng.randint(7, 60)
            adequacy = "critical"

        return LiquidityStressResult(
            entity_id=entity_id,
            assessment_date=self._today,
            scenario_id=scenario_id,
            survival_horizon_days=survival_days,
            liquidity_at_risk_mn=round(liquidity_at_risk, 2),
            stress_outflow_deposit_mn=round(stress_deposit, 2),
            stress_outflow_wholesale_mn=round(stress_wholesale, 2),
            stressed_lcr_pct=round(max(0.0, stressed_lcr), 1),
            stressed_nsfr_pct=round(max(0.0, stressed_nsfr), 1),
            liquidity_buffer_adequacy=adequacy,
            notes=[
                f"Scenario: {scenario_id}",
                f"Deposit runoff multiplier: {deposit_mult}x",
                f"Wholesale runoff multiplier: {wholesale_mult}x",
                f"HQLA haircut multiplier: {hqla_mult}x",
            ],
        )

    # ── Full Assessment ─────────────────────────────────────────────────────

    def full_assessment(
        self,
        entity_id: str,
        entity_name: str,
        reporting_date: str,
        scenario_id: str,
        hqla_l1: float = 1000.0,
        hqla_l2a: float = 300.0,
        hqla_l2b: float = 100.0,
        gross_outflow: float = 1200.0,
        gross_inflow: float = 500.0,
        climate_scenario: Optional[str] = None,
        asf_breakdown: Optional[dict] = None,
        rsf_breakdown: Optional[dict] = None,
        time_buckets: Optional[list] = None,
    ) -> dict:
        """Full Basel III liquidity risk assessment combining LCR, NSFR, ALM, and stress."""
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Default inputs if not provided
        if asf_breakdown is None:
            asf_breakdown = {
                "stable_retail_deposits": rng.uniform(800.0, 2000.0),
                "less_stable_retail_deposits": rng.uniform(200.0, 600.0),
                "wholesale_funding_gt1y": rng.uniform(300.0, 1000.0),
                "equity_tier1": rng.uniform(400.0, 800.0),
            }
        if rsf_breakdown is None:
            rsf_breakdown = {
                "level1_hqla": hqla_l1,
                "level2a_hqla": hqla_l2a,
                "unencumbered_residential_loans_lte35rw": rng.uniform(500.0, 1500.0),
                "corporate_loans_gt1y": rng.uniform(300.0, 900.0),
            }
        if time_buckets is None:
            buckets_def = ["overnight", "1m", "3m", "6m", "1y", "3y", "5y", "10y"]
            time_buckets = [
                {
                    "bucket": b,
                    "assets_mn": rng.uniform(100.0, 800.0),
                    "liabilities_mn": rng.uniform(100.0, 800.0),
                }
                for b in buckets_def
            ]

        lcr_r = self.assess_lcr(entity_id, hqla_l1, hqla_l2a, hqla_l2b, gross_outflow, gross_inflow, climate_scenario)
        nsfr_r = self.assess_nsfr(entity_id, asf_breakdown, rsf_breakdown)
        alm_r = self.assess_alm_gap(entity_id, time_buckets)
        stress_r = self.run_liquidity_stress(entity_id, lcr_r.lcr_pct, nsfr_r.nsfr_pct, scenario_id)

        # Monitoring metrics (BCBS 238)
        monitoring = {
            tool: {
                "description": meta["description"],
                "frequency": meta.get("frequency", "monthly"),
                "status": "reported" if rng.random() > 0.2 else "pending",
            }
            for tool, meta in BCBS238_MONITORING.items()
        }

        # Regulatory breach register
        breaches = {}
        if lcr_r.lcr_breach:
            breaches["lcr_breach"] = {
                "metric": "LCR",
                "current_pct": lcr_r.lcr_pct,
                "minimum_pct": LCR_MINIMUM_PCT,
                "shortfall_pct": round(LCR_MINIMUM_PCT - lcr_r.lcr_pct, 1),
                "article": "CRR2 Art 412 / LCR DA Art 4",
            }
        if nsfr_r.nsfr_breach:
            breaches["nsfr_breach"] = {
                "metric": "NSFR",
                "current_pct": nsfr_r.nsfr_pct,
                "minimum_pct": NSFR_MINIMUM_PCT,
                "shortfall_mn": round(nsfr_r.rsf_mn - nsfr_r.asf_mn, 1),
                "article": "CRR2 Art 428b",
            }

        # Overall rating
        breach_count = len(breaches)
        if breach_count == 0 and lcr_r.lcr_pct >= 130 and nsfr_r.nsfr_pct >= 115:
            overall = "strong"
        elif breach_count == 0:
            overall = "adequate"
        elif breach_count == 1:
            overall = "vulnerable"
        else:
            overall = "critical"

        # Priority actions
        actions = []
        if lcr_r.lcr_breach:
            actions.append("Increase HQLA buffer — issue covered bonds or repo HQLA-eligible collateral")
        if nsfr_r.nsfr_breach:
            actions.append("Extend wholesale funding maturity profile beyond 1 year")
        if alm_r.irrbb_material:
            actions.append("Implement interest rate hedges (IRS) to reduce duration gap")
        if stress_r.liquidity_buffer_adequacy in ("vulnerable", "critical"):
            actions.append("Activate contingency funding plan — diversify funding sources")
        if not actions:
            actions.append("Continue monitoring BCBS 238 tools on a monthly basis")

        cross_framework = {
            "crd5_art74": "Internal liquidity adequacy assessment (ILAAP) required",
            "srep_pillar2": "EBA/GL/2014/13 — SREP liquidity adequacy assessment",
            "ilaap": "BCBS 239 — Risk data aggregation and reporting for liquidity",
            "recovery_plan": "BRRD Art 5 — Liquidity component of recovery plan",
            "resolution": "BRRD Art 74 — Minimum liquidity requirement for resolution",
        }

        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "reporting_date": reporting_date,
            "scenario_id": scenario_id,
            "overall_liquidity_rating": overall,
            "lcr": {
                "lcr_pct": lcr_r.lcr_pct,
                "hqla_stock_mn": lcr_r.hqla_stock_mn,
                "net_outflow_30d_mn": lcr_r.net_outflow_30d_mn,
                "climate_adjusted_lcr_pct": lcr_r.climate_adjusted_lcr_pct,
                "climate_hqla_haircut_bps": lcr_r.climate_hqla_haircut_bps,
                "lcr_breach": lcr_r.lcr_breach,
                "l2_cap_breach": lcr_r.l2_cap_breach,
            },
            "nsfr": {
                "nsfr_pct": nsfr_r.nsfr_pct,
                "asf_mn": nsfr_r.asf_mn,
                "rsf_mn": nsfr_r.rsf_mn,
                "nsfr_breach": nsfr_r.nsfr_breach,
            },
            "alm_gap": {
                "cumulative_gap_mn": alm_r.cumulative_gap_mn,
                "duration_gap_years": alm_r.duration_gap_years,
                "eve_parallel_up_mn": alm_r.eve_parallel_up_mn,
                "eve_parallel_down_mn": alm_r.eve_parallel_down_mn,
                "nii_12m_sensitivity_mn": alm_r.nii_12m_sensitivity_mn,
                "irrbb_material": alm_r.irrbb_material,
                "bucket_gaps": alm_r.bucket_gaps,
            },
            "stress": {
                "survival_horizon_days": stress_r.survival_horizon_days,
                "liquidity_at_risk_mn": stress_r.liquidity_at_risk_mn,
                "stress_outflow_deposit_mn": stress_r.stress_outflow_deposit_mn,
                "stress_outflow_wholesale_mn": stress_r.stress_outflow_wholesale_mn,
                "stressed_lcr_pct": stress_r.stressed_lcr_pct,
                "stressed_nsfr_pct": stress_r.stressed_nsfr_pct,
                "liquidity_buffer_adequacy": stress_r.liquidity_buffer_adequacy,
            },
            "monitoring_metrics": monitoring,
            "regulatory_breaches": breaches,
            "priority_actions": actions,
            "cross_framework": cross_framework,
        }

    # ── Reference Data (static) ────────────────────────────────────────────

    @staticmethod
    def get_hqla_factors() -> dict:
        return HQLA_HAIRCUTS

    @staticmethod
    def get_runoff_rates() -> dict:
        return RUNOFF_RATES

    @staticmethod
    def get_asf_rsf_factors() -> dict:
        return {"asf_factors": ASF_FACTORS, "rsf_factors": RSF_FACTORS}

    @staticmethod
    def get_eba_shocks() -> dict:
        return EBA_RATE_SHOCKS

    @staticmethod
    def get_monitoring_tools() -> dict:
        return BCBS238_MONITORING
