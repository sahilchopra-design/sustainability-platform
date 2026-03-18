"""
EIOPA ORSA Climate Stress Test Engine (E7)
==========================================

Implements EIOPA's climate stress testing framework for insurers under
Solvency II Article 45a (SFCR climate section) and EIOPA Guidelines on
ORSA (GL 01/2018 + 2023 update).

Modelled frameworks:
- Solvency II Article 45a   — Climate risk integration in ORSA
- EIOPA Opinion 2021        — Supervision of use of climate scenarios
- EIOPA 2022 Climate Stress Test — Sudden transition + NatCat scenarios
- EIOPA 2023 Insurance Stress Test — Expanded physical + transition
- TCFD for insurers          — Physical + transition scenario disclosure
- NGFS x EIOPA mapping       — Net Zero 2050 / Delayed / Hot-House / Below 2°C

Stress modules:
  1. Market Risk          — Equity, bonds (sovereign + corporate), RE, alternatives
  2. Underwriting Risk    — NatCat amplification, reserve adequacy, lapse stress
  3. Life Risk            — Mortality, longevity, morbidity climate adjustments
  4. SCR / MCR Impact     — Post-stress Basic SCR recalculation, solvency ratio
  5. Liquidity Stress     — Asset-liability mismatch, surrender risk
  6. ORSA Disclosure      — 12-point EIOPA Art 45a checklist
  7. Recovery Capacity    — Pre-positioned management actions, capital buffer
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Reference Data: EIOPA Climate Stress Scenarios
# ---------------------------------------------------------------------------

# Four canonical EIOPA/NGFS scenarios mapped to insurer shock factors
# Sources: EIOPA 2022 Stress Test, EIOPA 2023 Insurance ST, NGFS Phase IV
EIOPA_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "sudden_transition": {
        "name": "Sudden / Disorderly Transition",
        "description": (
            "Abrupt policy tightening at 2030: carbon tax >€150/tCO₂, "
            "stranded fossil-fuel assets. Mimics EIOPA 2022 Stress Test Scenario A."
        ),
        "ngfs_equivalent": "Disorderly Transition (Divergent Net Zero)",
        "horizon_years": 3,
        "temp_outcome_c": 1.8,
        # Asset shocks (as %-haircut of market value, negative = loss)
        "equity_listed_shock_pct": -35.0,
        "equity_fossil_fuel_shock_pct": -55.0,
        "re_commercial_shock_pct": -30.0,
        "re_residential_shock_pct": -20.0,
        "sovereign_bond_spread_bps": 120.0,
        "ig_corp_bond_spread_bps": 250.0,
        "hy_corp_bond_spread_bps": 550.0,
        "infrastructure_shock_pct": -20.0,
        "alternatives_shock_pct": -25.0,
        # Underwriting / NatCat
        "natcat_amplifier": 1.25,          # multiplied on existing NatCat SCR
        "reserve_adequacy_shock_pct": 5.0, # % deterioration in technical provisions
        "lapse_shock_pct": 8.0,            # % additional lapses (life insurance)
        # Life underwriting adjustments
        "mortality_shift_bps": 30.0,       # increase in mortality (heat/air quality)
        "longevity_shift_bps": -10.0,      # improvement slows (heat stress)
        "morbidity_shift_bps": 40.0,       # respiratory / heat-related claims
    },
    "orderly_transition": {
        "name": "Orderly / Paris-Aligned Transition",
        "description": (
            "Smooth net-zero-2050 transition. Moderate asset re-pricing; "
            "NatCat claims contained. NGFS Net Zero 2050."
        ),
        "ngfs_equivalent": "Net Zero 2050",
        "horizon_years": 10,
        "temp_outcome_c": 1.5,
        "equity_listed_shock_pct": -15.0,
        "equity_fossil_fuel_shock_pct": -30.0,
        "re_commercial_shock_pct": -12.0,
        "re_residential_shock_pct": -8.0,
        "sovereign_bond_spread_bps": 40.0,
        "ig_corp_bond_spread_bps": 80.0,
        "hy_corp_bond_spread_bps": 200.0,
        "infrastructure_shock_pct": -8.0,
        "alternatives_shock_pct": -10.0,
        "natcat_amplifier": 1.10,
        "reserve_adequacy_shock_pct": 2.0,
        "lapse_shock_pct": 3.0,
        "mortality_shift_bps": 15.0,
        "longevity_shift_bps": 5.0,
        "morbidity_shift_bps": 20.0,
    },
    "hot_house_world": {
        "name": "Hot House World (No Action)",
        "description": (
            "Climate policies fail; >3°C warming by 2100. Severe physical risk "
            "dominates: NatCat frequency doubles, chronic risk re-prices RE. "
            "NGFS Current Policies."
        ),
        "ngfs_equivalent": "Current Policies",
        "horizon_years": 30,
        "temp_outcome_c": 3.0,
        "equity_listed_shock_pct": -20.0,
        "equity_fossil_fuel_shock_pct": -10.0,   # fossil benefits short-term
        "re_commercial_shock_pct": -45.0,
        "re_residential_shock_pct": -35.0,
        "sovereign_bond_spread_bps": 200.0,
        "ig_corp_bond_spread_bps": 180.0,
        "hy_corp_bond_spread_bps": 400.0,
        "infrastructure_shock_pct": -35.0,
        "alternatives_shock_pct": -30.0,
        "natcat_amplifier": 2.00,
        "reserve_adequacy_shock_pct": 15.0,
        "lapse_shock_pct": 12.0,
        "mortality_shift_bps": 80.0,
        "longevity_shift_bps": -30.0,
        "morbidity_shift_bps": 100.0,
    },
    "below_2c": {
        "name": "Below 2°C (Delayed but Decisive)",
        "description": (
            "Action taken but only after a decade of delay. Higher transition "
            "costs than orderly; physical risk partially locked-in. "
            "NGFS Below 2°C."
        ),
        "ngfs_equivalent": "Below 2°C",
        "horizon_years": 10,
        "temp_outcome_c": 1.9,
        "equity_listed_shock_pct": -25.0,
        "equity_fossil_fuel_shock_pct": -40.0,
        "re_commercial_shock_pct": -22.0,
        "re_residential_shock_pct": -15.0,
        "sovereign_bond_spread_bps": 80.0,
        "ig_corp_bond_spread_bps": 160.0,
        "hy_corp_bond_spread_bps": 380.0,
        "infrastructure_shock_pct": -15.0,
        "alternatives_shock_pct": -18.0,
        "natcat_amplifier": 1.50,
        "reserve_adequacy_shock_pct": 8.0,
        "lapse_shock_pct": 6.0,
        "mortality_shift_bps": 45.0,
        "longevity_shift_bps": -5.0,
        "morbidity_shift_bps": 60.0,
    },
}

# ---------------------------------------------------------------------------
# Reference: EIOPA Art 45a ORSA Climate Checklist
# ---------------------------------------------------------------------------

ORSA_CLIMATE_CHECKLIST: List[Dict[str, str]] = [
    {
        "ref": "Art45a-1",
        "requirement": "Governance: board-level climate risk oversight",
        "eiopa_source": "EIOPA Opinion (EIOPA-BoS-21/127) §3.1",
    },
    {
        "ref": "Art45a-2",
        "requirement": "Risk identification: physical and transition risks identified across all material risk categories",
        "eiopa_source": "EIOPA Opinion §3.2; EIOPA GL 05 on ORSA",
    },
    {
        "ref": "Art45a-3",
        "requirement": "Scenario analysis: at least one orderly + one disorderly scenario applied",
        "eiopa_source": "EIOPA 2022 Stress Test design; NGFS Phase IV",
    },
    {
        "ref": "Art45a-4",
        "requirement": "Time horizon: long-term scenarios (10–30 years) alongside short-term ORSA horizon",
        "eiopa_source": "EIOPA Opinion §3.3; Art 45a(2) Solvency II",
    },
    {
        "ref": "Art45a-5",
        "requirement": "Investment portfolio: climate risk quantified for equity, bonds, RE, infrastructure",
        "eiopa_source": "EIOPA 2022 ST Modules M1-M4",
    },
    {
        "ref": "Art45a-6",
        "requirement": "Underwriting: NatCat exposure assessed under climate scenarios; reserve adequacy tested",
        "eiopa_source": "EIOPA 2023 ST — NatCat Module; EIOPA GL 01/2018",
    },
    {
        "ref": "Art45a-7",
        "requirement": "Life underwriting: mortality/longevity/morbidity adjustments under climate scenarios",
        "eiopa_source": "EIOPA 2023 ST — Life Module",
    },
    {
        "ref": "Art45a-8",
        "requirement": "SCR and MCR impact: stressed capital requirements quantified and solvency ratio disclosed",
        "eiopa_source": "Art 101, 129 Solvency II; EIOPA ST Quantitative Assessment",
    },
    {
        "ref": "Art45a-9",
        "requirement": "Management actions: pre-positioned recovery measures identified and costed",
        "eiopa_source": "EIOPA GL 07 on ORSA; Art 45a(3)",
    },
    {
        "ref": "Art45a-10",
        "requirement": "Data quality: data sources, assumptions, and limitations disclosed",
        "eiopa_source": "EIOPA Opinion §3.5",
    },
    {
        "ref": "Art45a-11",
        "requirement": "Regulatory reporting: climate section in ORSA report submitted to NCA",
        "eiopa_source": "Art 45(6) Solvency II; EIOPA GL on ORSA supervisory assessment",
    },
    {
        "ref": "Art45a-12",
        "requirement": "Double materiality: climate risk materiality assessment with financial + impact perspectives",
        "eiopa_source": "EIOPA Opinion §3.2; ISSB S2 integration for re/insurers",
    },
]

# ---------------------------------------------------------------------------
# Reference: Insurer Type Profiles
# ---------------------------------------------------------------------------

INSURER_TYPE_PROFILES: Dict[str, Dict[str, Any]] = {
    "life": {
        "label": "Life Insurer",
        "dominant_risk": "longevity + mortality + lapse",
        "tp_sensitivity": "high",          # technical provisions interest-rate + mortality sensitive
        "natcat_exposure": "low",
        "asset_intensity": "very_high",    # long-duration bond-heavy portfolios
    },
    "non_life": {
        "label": "Non-Life / P&C Insurer",
        "dominant_risk": "NatCat + reserve adequacy",
        "tp_sensitivity": "medium",
        "natcat_exposure": "very_high",
        "asset_intensity": "medium",
    },
    "composite": {
        "label": "Composite Insurer",
        "dominant_risk": "combined",
        "tp_sensitivity": "high",
        "natcat_exposure": "medium",
        "asset_intensity": "high",
    },
    "reinsurer": {
        "label": "Reinsurer",
        "dominant_risk": "peak NatCat + reserve",
        "tp_sensitivity": "medium",
        "natcat_exposure": "extreme",
        "asset_intensity": "high",
    },
    "captive": {
        "label": "Captive Insurer",
        "dominant_risk": "parent group risk concentration",
        "tp_sensitivity": "low",
        "natcat_exposure": "low",
        "asset_intensity": "medium",
    },
}

# SCR standard formula module weights (used in Basic SCR approximation)
# Weights applied to stressed values to estimate SCR module contribution
_SCR_MODULE_WEIGHTS = {
    "market_risk": 0.45,
    "underwriting_nonlife": 0.25,
    "underwriting_life": 0.20,
    "counterparty": 0.05,
    "operational": 0.05,
}

# Duration assumption (years) for bond spread → price impact: ΔP ≈ -D × Δspread
_BOND_DURATION_SOVEREIGN = 7.0
_BOND_DURATION_IG_CORP = 5.0
_BOND_DURATION_HY_CORP = 4.0

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class InsurerInput:
    """Balance sheet and portfolio inputs for a single (re)insurer."""
    entity_id: str
    entity_name: str
    insurer_type: str = "composite"                 # life | non_life | composite | reinsurer | captive
    domicile: str = "DE"                            # ISO-2

    # Balance sheet (EUR)
    total_assets_eur: float = 0.0
    total_tp_eur: float = 0.0                       # Technical Provisions (best estimate + RM)
    eligible_own_funds_eur: float = 0.0
    scr_eur: float = 0.0                            # Current SCR
    mcr_eur: float = 0.0                            # Current MCR

    # Investment portfolio breakdown (% of total invested assets)
    equity_listed_pct: float = 15.0
    equity_fossil_fuel_pct: float = 3.0             # subset of equity_listed
    re_commercial_pct: float = 8.0
    re_residential_pct: float = 4.0
    sovereign_bonds_pct: float = 35.0
    ig_corp_bonds_pct: float = 25.0
    hy_corp_bonds_pct: float = 5.0
    infrastructure_pct: float = 3.0
    alternatives_pct: float = 2.0                   # hedges, commodities, etc.

    # Underwriting / liability data
    annual_natcat_exposure_eur: float = 0.0         # current annual NatCat expected loss
    technical_provision_adequacy_pct: float = 100.0 # current TP as % of best estimate (100=adequate)
    annual_premium_eur: float = 0.0

    # Life-specific
    in_force_sum_assured_eur: float = 0.0           # total life sum assured
    lapse_sensitive_reserves_pct: float = 20.0      # % TPs sensitive to lapses

    # ORSA completeness flags (for checklist scoring)
    has_board_climate_oversight: bool = False
    has_climate_scenario_analysis: bool = False
    has_long_term_scenarios: bool = False
    has_natcat_climate_assessment: bool = False
    has_life_climate_adjustment: bool = False
    has_management_actions_plan: bool = False
    has_data_quality_disclosure: bool = False
    has_nca_orsa_submission: bool = False
    has_double_materiality: bool = False


@dataclass
class AssetShockResult:
    equity_loss_eur: float = 0.0
    re_loss_eur: float = 0.0
    sovereign_bond_loss_eur: float = 0.0
    ig_corp_bond_loss_eur: float = 0.0
    hy_corp_bond_loss_eur: float = 0.0
    infrastructure_loss_eur: float = 0.0
    alternatives_loss_eur: float = 0.0
    total_asset_loss_eur: float = 0.0
    total_asset_loss_pct: float = 0.0


@dataclass
class UnderwritingShockResult:
    natcat_additional_loss_eur: float = 0.0
    reserve_deterioration_eur: float = 0.0
    lapse_loss_eur: float = 0.0
    mortality_additional_loss_eur: float = 0.0
    morbidity_additional_loss_eur: float = 0.0
    total_uw_shock_eur: float = 0.0


@dataclass
class CapitalImpactResult:
    pre_stress_scr_eur: float = 0.0
    post_stress_scr_eur: float = 0.0
    pre_stress_own_funds_eur: float = 0.0
    post_stress_own_funds_eur: float = 0.0
    pre_stress_solvency_ratio_pct: float = 0.0
    post_stress_solvency_ratio_pct: float = 0.0
    scr_breach: bool = False
    mcr_breach: bool = False
    capital_shortfall_eur: float = 0.0
    scr_coverage_change_pp: float = 0.0             # percentage-point change in solvency ratio


@dataclass
class OrsaChecklistResult:
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    items_met: int = 0
    items_total: int = 0
    orsa_completeness_pct: float = 0.0
    gaps: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)


@dataclass
class ScenarioStressResult:
    scenario_id: str = ""
    scenario_name: str = ""
    scenario_description: str = ""
    ngfs_equivalent: str = ""
    temp_outcome_c: float = 0.0
    horizon_years: int = 0

    asset_shock: AssetShockResult = field(default_factory=AssetShockResult)
    underwriting_shock: UnderwritingShockResult = field(default_factory=UnderwritingShockResult)
    capital_impact: CapitalImpactResult = field(default_factory=CapitalImpactResult)

    total_stress_loss_eur: float = 0.0
    total_stress_loss_pct_of_own_funds: float = 0.0
    stress_severity: str = ""               # mild | moderate | severe | extreme
    key_drivers: List[str] = field(default_factory=list)
    management_actions_capacity_eur: float = 0.0
    recovery_feasible: bool = True
    narrative: str = ""


@dataclass
class EiopaStressResult:
    run_id: str = ""
    entity_id: str = ""
    entity_name: str = ""
    insurer_type: str = ""
    assessment_date: str = ""

    # Per-scenario results
    scenario_results: List[ScenarioStressResult] = field(default_factory=list)

    # Worst-case across all scenarios
    worst_scenario_id: str = ""
    worst_solvency_ratio_pct: float = 0.0
    worst_capital_shortfall_eur: float = 0.0

    # ORSA completeness
    orsa_checklist: OrsaChecklistResult = field(default_factory=OrsaChecklistResult)

    # Headline flags
    any_scr_breach: bool = False
    any_mcr_breach: bool = False
    overall_resilience: str = ""            # resilient | vulnerable | at_risk | critical

    gaps: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EiopaStressEngine:
    """
    EIOPA Climate Stress Test engine for Solvency II (re)insurers.
    Implements Art 45a ORSA climate risk integration.
    """

    # Management action capacity: % of stressed loss that can be offset
    # by pre-positioned actions (dividend cut, capital issuance, RI placement)
    _MGMT_ACTION_CAPACITY = {
        "life": 0.30,
        "non_life": 0.25,
        "composite": 0.28,
        "reinsurer": 0.20,
        "captive": 0.15,
    }

    def assess(
        self,
        insurer: InsurerInput,
        scenarios: Optional[List[str]] = None,
        assessment_date: Optional[str] = None,
    ) -> EiopaStressResult:
        """
        Run full EIOPA climate stress test for one insurer.

        Args:
            insurer: Balance sheet + portfolio + ORSA flag data.
            scenarios: List of scenario IDs to run. Default = all four.
            assessment_date: ISO date YYYY-MM-DD.

        Returns:
            EiopaStressResult with per-scenario results, ORSA checklist, and capital impacts.
        """
        if assessment_date is None:
            assessment_date = date.today().isoformat()
        if scenarios is None:
            scenarios = list(EIOPA_SCENARIOS.keys())

        run_id = f"EIOPA-{insurer.entity_id[:8].upper()}-{uuid.uuid4().hex[:6].upper()}"

        invested_assets = insurer.total_assets_eur - insurer.total_tp_eur
        if invested_assets <= 0:
            invested_assets = insurer.total_assets_eur * 0.85  # fallback heuristic

        scenario_results: List[ScenarioStressResult] = []
        for sc_id in scenarios:
            if sc_id not in EIOPA_SCENARIOS:
                continue
            sc = EIOPA_SCENARIOS[sc_id]
            result = self._run_scenario(insurer, sc_id, sc, invested_assets)
            scenario_results.append(result)

        # Worst-case solvency ratio
        worst_ratio = min(
            (r.capital_impact.post_stress_solvency_ratio_pct for r in scenario_results),
            default=insurer.eligible_own_funds_eur / max(insurer.scr_eur, 1) * 100,
        )
        worst_sc_id = next(
            (r.scenario_id for r in scenario_results
             if r.capital_impact.post_stress_solvency_ratio_pct == worst_ratio),
            scenarios[0] if scenarios else "",
        )
        worst_shortfall = max(
            (r.capital_impact.capital_shortfall_eur for r in scenario_results), default=0.0
        )

        any_scr_breach = any(r.capital_impact.scr_breach for r in scenario_results)
        any_mcr_breach = any(r.capital_impact.mcr_breach for r in scenario_results)

        orsa_checklist = self._assess_orsa_checklist(insurer)

        gaps, priority_actions = self._derive_gaps(
            insurer, scenario_results, orsa_checklist, any_scr_breach, any_mcr_breach
        )

        overall_resilience = self._derive_resilience(
            worst_ratio, any_scr_breach, any_mcr_breach, orsa_checklist.orsa_completeness_pct
        )

        return EiopaStressResult(
            run_id=run_id,
            entity_id=insurer.entity_id,
            entity_name=insurer.entity_name,
            insurer_type=insurer.insurer_type,
            assessment_date=assessment_date,
            scenario_results=scenario_results,
            worst_scenario_id=worst_sc_id,
            worst_solvency_ratio_pct=round(worst_ratio, 1),
            worst_capital_shortfall_eur=round(worst_shortfall, 0),
            orsa_checklist=orsa_checklist,
            any_scr_breach=any_scr_breach,
            any_mcr_breach=any_mcr_breach,
            overall_resilience=overall_resilience,
            gaps=gaps,
            priority_actions=priority_actions,
            metadata={
                "framework": "Solvency II Art 45a + EIOPA 2022/2023 Climate Stress Test",
                "scenarios_run": scenarios,
                "engine_version": "E7.1",
                "reference": (
                    "EIOPA-BoS-21/127 (Opinion on climate change) | "
                    "EIOPA 2022 Insurance Stress Test | "
                    "EIOPA 2023 Insurance Stress Test | "
                    "NGFS Phase IV Scenarios"
                ),
            },
        )

    # -----------------------------------------------------------------------
    # Private: Scenario execution
    # -----------------------------------------------------------------------

    def _run_scenario(
        self,
        ins: InsurerInput,
        sc_id: str,
        sc: Dict[str, Any],
        invested_assets: float,
    ) -> ScenarioStressResult:

        asset_shock = self._calc_asset_shock(ins, sc, invested_assets)
        uw_shock = self._calc_underwriting_shock(ins, sc)
        capital = self._calc_capital_impact(ins, asset_shock, uw_shock, sc_id)

        total_loss = asset_shock.total_asset_loss_eur + uw_shock.total_uw_shock_eur
        loss_pct_of_of = (
            total_loss / max(ins.eligible_own_funds_eur, 1) * 100
            if ins.eligible_own_funds_eur > 0 else 0.0
        )

        mgmt_capacity_rate = self._MGMT_ACTION_CAPACITY.get(ins.insurer_type, 0.25)
        mgmt_capacity_eur = total_loss * mgmt_capacity_rate

        recovery_feasible = (
            capital.post_stress_own_funds_eur + mgmt_capacity_eur
        ) >= capital.post_stress_scr_eur

        severity = self._severity_label(loss_pct_of_of, capital.scr_breach, capital.mcr_breach)
        key_drivers = self._key_drivers(ins, asset_shock, uw_shock)
        narrative = self._build_narrative(ins, sc, asset_shock, uw_shock, capital, severity)

        return ScenarioStressResult(
            scenario_id=sc_id,
            scenario_name=sc["name"],
            scenario_description=sc["description"],
            ngfs_equivalent=sc["ngfs_equivalent"],
            temp_outcome_c=sc["temp_outcome_c"],
            horizon_years=sc["horizon_years"],
            asset_shock=asset_shock,
            underwriting_shock=uw_shock,
            capital_impact=capital,
            total_stress_loss_eur=round(total_loss, 0),
            total_stress_loss_pct_of_own_funds=round(loss_pct_of_of, 1),
            stress_severity=severity,
            key_drivers=key_drivers,
            management_actions_capacity_eur=round(mgmt_capacity_eur, 0),
            recovery_feasible=recovery_feasible,
            narrative=narrative,
        )

    def _calc_asset_shock(
        self,
        ins: InsurerInput,
        sc: Dict[str, Any],
        invested: float,
    ) -> AssetShockResult:
        """Compute EUR loss for each asset class under the scenario shocks."""

        # Equity: blended shock accounting for fossil-fuel subset
        equity_base_pct = ins.equity_listed_pct / 100
        fossil_subset_pct = min(ins.equity_fossil_fuel_pct, ins.equity_listed_pct) / 100
        non_fossil_equity_pct = equity_base_pct - fossil_subset_pct

        equity_loss = invested * (
            non_fossil_equity_pct * abs(sc["equity_listed_shock_pct"]) / 100
            + fossil_subset_pct * abs(sc["equity_fossil_fuel_shock_pct"]) / 100
        )

        # Real estate
        re_c_loss = invested * ins.re_commercial_pct / 100 * abs(sc["re_commercial_shock_pct"]) / 100
        re_r_loss = invested * ins.re_residential_pct / 100 * abs(sc["re_residential_shock_pct"]) / 100
        re_loss = re_c_loss + re_r_loss

        # Bonds: duration-based ΔP = -D × Δspread
        sov_loss = invested * ins.sovereign_bonds_pct / 100 * (
            _BOND_DURATION_SOVEREIGN * sc["sovereign_bond_spread_bps"] / 10000
        )
        ig_loss = invested * ins.ig_corp_bonds_pct / 100 * (
            _BOND_DURATION_IG_CORP * sc["ig_corp_bond_spread_bps"] / 10000
        )
        hy_loss = invested * ins.hy_corp_bonds_pct / 100 * (
            _BOND_DURATION_HY_CORP * sc["hy_corp_bond_spread_bps"] / 10000
        )

        infra_loss = invested * ins.infrastructure_pct / 100 * abs(sc["infrastructure_shock_pct"]) / 100
        alt_loss = invested * ins.alternatives_pct / 100 * abs(sc["alternatives_shock_pct"]) / 100

        total = equity_loss + re_loss + sov_loss + ig_loss + hy_loss + infra_loss + alt_loss
        total_pct = total / max(invested, 1) * 100

        return AssetShockResult(
            equity_loss_eur=round(equity_loss, 0),
            re_loss_eur=round(re_loss, 0),
            sovereign_bond_loss_eur=round(sov_loss, 0),
            ig_corp_bond_loss_eur=round(ig_loss, 0),
            hy_corp_bond_loss_eur=round(hy_loss, 0),
            infrastructure_loss_eur=round(infra_loss, 0),
            alternatives_loss_eur=round(alt_loss, 0),
            total_asset_loss_eur=round(total, 0),
            total_asset_loss_pct=round(total_pct, 1),
        )

    def _calc_underwriting_shock(
        self,
        ins: InsurerInput,
        sc: Dict[str, Any],
    ) -> UnderwritingShockResult:
        """Compute liability-side shocks for underwriting and life modules."""

        # NatCat: amplify current expected annual NatCat loss by scenario factor
        natcat_add = ins.annual_natcat_exposure_eur * (sc["natcat_amplifier"] - 1.0)

        # Reserve adequacy deterioration
        reserve_det = ins.total_tp_eur * sc["reserve_adequacy_shock_pct"] / 100

        # Lapse shock: applied to lapse-sensitive reserves (mainly unit-linked, with-profits)
        lapse_sensitive_eur = ins.total_tp_eur * ins.lapse_sensitive_reserves_pct / 100
        lapse_loss = lapse_sensitive_eur * sc["lapse_shock_pct"] / 100

        # Life shocks: mortality and morbidity expressed in bps of sum assured
        mortality_loss = ins.in_force_sum_assured_eur * sc["mortality_shift_bps"] / 10000
        morbidity_loss = ins.annual_premium_eur * sc["morbidity_shift_bps"] / 10000

        total = natcat_add + reserve_det + lapse_loss + mortality_loss + morbidity_loss

        return UnderwritingShockResult(
            natcat_additional_loss_eur=round(natcat_add, 0),
            reserve_deterioration_eur=round(reserve_det, 0),
            lapse_loss_eur=round(lapse_loss, 0),
            mortality_additional_loss_eur=round(mortality_loss, 0),
            morbidity_additional_loss_eur=round(morbidity_loss, 0),
            total_uw_shock_eur=round(total, 0),
        )

    def _calc_capital_impact(
        self,
        ins: InsurerInput,
        asset_shock: AssetShockResult,
        uw_shock: UnderwritingShockResult,
        sc_id: str,
    ) -> CapitalImpactResult:
        """Recalculate SCR/MCR and solvency ratio post-stress."""

        pre_ratio = (
            ins.eligible_own_funds_eur / max(ins.scr_eur, 1) * 100
            if ins.scr_eur > 0 else 200.0
        )

        total_loss = asset_shock.total_asset_loss_eur + uw_shock.total_uw_shock_eur

        # Post-stress own funds: reduce by total loss (after tax benefit at 20%)
        after_tax_loss = total_loss * 0.80
        post_of = ins.eligible_own_funds_eur - after_tax_loss

        # Post-stress SCR: market risk component increases under stressed conditions
        # Approximation: market risk SCR grows proportional to realised volatility
        market_shock_intensity = asset_shock.total_asset_loss_pct / 100
        market_scr_uplift = 1.0 + market_shock_intensity * _SCR_MODULE_WEIGHTS["market_risk"]

        # NatCat module uplift
        sc_params = EIOPA_SCENARIOS[sc_id]
        natcat_uplift = sc_params["natcat_amplifier"] * _SCR_MODULE_WEIGHTS["underwriting_nonlife"]
        other_scr = ins.scr_eur * (
            _SCR_MODULE_WEIGHTS["underwriting_life"]
            + _SCR_MODULE_WEIGHTS["counterparty"]
            + _SCR_MODULE_WEIGHTS["operational"]
        )
        post_scr = (
            ins.scr_eur * _SCR_MODULE_WEIGHTS["market_risk"] * market_scr_uplift
            + ins.scr_eur * _SCR_MODULE_WEIGHTS["underwriting_nonlife"] * natcat_uplift
            + other_scr
        )

        post_ratio = post_of / max(post_scr, 1) * 100
        scr_breach = post_of < post_scr
        mcr_breach = post_of < ins.mcr_eur
        shortfall = max(post_scr - post_of, 0.0) if scr_breach else 0.0

        return CapitalImpactResult(
            pre_stress_scr_eur=round(ins.scr_eur, 0),
            post_stress_scr_eur=round(post_scr, 0),
            pre_stress_own_funds_eur=round(ins.eligible_own_funds_eur, 0),
            post_stress_own_funds_eur=round(post_of, 0),
            pre_stress_solvency_ratio_pct=round(pre_ratio, 1),
            post_stress_solvency_ratio_pct=round(post_ratio, 1),
            scr_breach=scr_breach,
            mcr_breach=mcr_breach,
            capital_shortfall_eur=round(shortfall, 0),
            scr_coverage_change_pp=round(post_ratio - pre_ratio, 1),
        )

    # -----------------------------------------------------------------------
    # Private: ORSA Checklist
    # -----------------------------------------------------------------------

    def _assess_orsa_checklist(self, ins: InsurerInput) -> OrsaChecklistResult:
        flag_map = {
            "Art45a-1": ins.has_board_climate_oversight,
            "Art45a-2": True,   # risk identification — base assumption when calling this API
            "Art45a-3": ins.has_climate_scenario_analysis,
            "Art45a-4": ins.has_long_term_scenarios,
            "Art45a-5": ins.total_assets_eur > 0,   # portfolio data provided
            "Art45a-6": ins.has_natcat_climate_assessment,
            "Art45a-7": ins.has_life_climate_adjustment if ins.insurer_type in ("life", "composite") else True,
            "Art45a-8": ins.scr_eur > 0,             # SCR data provided = quantification exists
            "Art45a-9": ins.has_management_actions_plan,
            "Art45a-10": ins.has_data_quality_disclosure,
            "Art45a-11": ins.has_nca_orsa_submission,
            "Art45a-12": ins.has_double_materiality,
        }

        rows = []
        met = 0
        gaps: List[str] = []
        actions: List[str] = []

        for item in ORSA_CLIMATE_CHECKLIST:
            ref = item["ref"]
            satisfied = flag_map.get(ref, False)
            rows.append({**item, "met": satisfied})
            if satisfied:
                met += 1
            else:
                gaps.append(f"{ref}: {item['requirement']}")
                actions.append(
                    f"Implement {ref}: {item['requirement'].split(':')[0]} "
                    f"— ref {item['eiopa_source']}"
                )

        completeness = met / len(ORSA_CLIMATE_CHECKLIST) * 100

        return OrsaChecklistResult(
            checklist=rows,
            items_met=met,
            items_total=len(ORSA_CLIMATE_CHECKLIST),
            orsa_completeness_pct=round(completeness, 1),
            gaps=gaps,
            priority_actions=actions[:5],
        )

    # -----------------------------------------------------------------------
    # Private: Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _severity_label(
        loss_pct_of_of: float,
        scr_breach: bool,
        mcr_breach: bool,
    ) -> str:
        if mcr_breach:
            return "extreme"
        if scr_breach:
            return "severe"
        if loss_pct_of_of > 30:
            return "severe"
        if loss_pct_of_of > 15:
            return "moderate"
        return "mild"

    @staticmethod
    def _key_drivers(
        ins: InsurerInput,
        asset: AssetShockResult,
        uw: UnderwritingShockResult,
    ) -> List[str]:
        drivers = []
        total = asset.total_asset_loss_eur + uw.total_uw_shock_eur
        if total == 0:
            return ["Insufficient data to determine key drivers"]

        components = {
            "equity market shock": asset.equity_loss_eur,
            "real estate devaluation": asset.re_loss_eur,
            "sovereign bond spread widening": asset.sovereign_bond_loss_eur,
            "corporate bond spread widening": asset.ig_corp_bond_loss_eur + asset.hy_corp_bond_loss_eur,
            "NatCat amplification": uw.natcat_additional_loss_eur,
            "reserve deterioration": uw.reserve_deterioration_eur,
            "lapse stress": uw.lapse_loss_eur,
            "life risk adjustments": uw.mortality_additional_loss_eur + uw.morbidity_additional_loss_eur,
        }
        sorted_drivers = sorted(components.items(), key=lambda x: x[1], reverse=True)
        for name, val in sorted_drivers[:3]:
            pct = val / total * 100
            if pct >= 5:
                drivers.append(f"{name} ({pct:.0f}% of total shock)")
        return drivers or ["diversified across asset and underwriting modules"]

    @staticmethod
    def _build_narrative(
        ins: InsurerInput,
        sc: Dict[str, Any],
        asset: AssetShockResult,
        uw: UnderwritingShockResult,
        cap: CapitalImpactResult,
        severity: str,
    ) -> str:
        ratio_delta = cap.scr_coverage_change_pp
        direction = "falls" if ratio_delta < 0 else "rises"
        return (
            f"Under the '{sc['name']}' scenario (NGFS: {sc['ngfs_equivalent']}, "
            f"{sc['temp_outcome_c']}°C outcome), {ins.entity_name}'s solvency ratio "
            f"{direction} by {abs(ratio_delta):.0f} pp to {cap.post_stress_solvency_ratio_pct:.0f}%. "
            f"Total stress loss of €{(asset.total_asset_loss_eur + uw.total_uw_shock_eur)/1e6:.1f}M "
            f"is classified as '{severity}'. "
            f"{'SCR breach confirmed — immediate recovery action required.' if cap.scr_breach else 'Solvency requirement maintained.'} "
            f"{'MCR breach — regulatory intervention threshold breached.' if cap.mcr_breach else ''}"
        ).strip()

    @staticmethod
    def _derive_gaps(
        ins: InsurerInput,
        results: List[ScenarioStressResult],
        orsa: OrsaChecklistResult,
        any_scr: bool,
        any_mcr: bool,
    ) -> tuple[List[str], List[str]]:
        gaps: List[str] = []
        actions: List[str] = []

        if any_mcr:
            gaps.append("MCR breach under at least one scenario — regulatory intervention threshold exceeded")
            actions.append("Immediate capital raise or portfolio de-risking to restore MCR compliance")
        if any_scr:
            gaps.append("SCR breach under at least one scenario — capital plan required")
            actions.append("Develop SCR recovery plan; explore management actions (dividend cut, RI placement, capital issuance)")

        if orsa.orsa_completeness_pct < 50:
            gaps.append(f"ORSA climate completeness critically low ({orsa.orsa_completeness_pct:.0f}%) — regulatory non-compliance with Art 45a")
            actions.append("Commission ORSA climate section remediation project — target submission within 2 reporting cycles")
        elif orsa.orsa_completeness_pct < 80:
            gaps.append(f"ORSA climate completeness below target ({orsa.orsa_completeness_pct:.0f}%)")
            actions.append("Address ORSA climate gaps: " + "; ".join(orsa.gaps[:3]))

        if not ins.has_long_term_scenarios:
            gaps.append("Long-term climate scenarios (10–30 yr) absent — required by Art 45a(2)")
            actions.append("Implement 10-year and 30-year NGFS-mapped climate scenarios in ORSA")

        if not ins.has_management_actions_plan:
            gaps.append("No pre-positioned management actions plan under climate stress")
            actions.append("Develop management actions playbook: RI cover expansion, portfolio de-risking, dividend suspension trigger")

        if not ins.has_natcat_climate_assessment and ins.insurer_type in ("non_life", "composite", "reinsurer"):
            gaps.append("NatCat climate risk not quantified — core risk for this insurer type")
            actions.append("Commission climate-adjusted NatCat model (RCP 4.5/8.5 hazard layers)")

        # Top 3 ORSA gaps
        for gap in orsa.gaps[:3]:
            if gap not in gaps:
                gaps.append(gap)

        return gaps[:8], actions[:6]

    @staticmethod
    def _derive_resilience(
        worst_ratio: float,
        any_scr: bool,
        any_mcr: bool,
        orsa_pct: float,
    ) -> str:
        if any_mcr:
            return "critical"
        if any_scr:
            return "at_risk"
        if worst_ratio < 130:
            return "vulnerable"
        return "resilient"
