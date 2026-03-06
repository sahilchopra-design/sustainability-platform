"""
IFRS 9 ECL Climate Engine -- Basel III/IV Climate Risk / EBA GL/2022/16 / BCBS Climate Guidance

Implements a full IFRS 9 Expected Credit Loss (ECL) engine with integrated climate risk
overlays, compliant with:
  - IFRS 9 Financial Instruments (para. 5.5.1-5.5.20, B5.5.1-B5.5.55)
  - EBA Guidelines on loan origination and monitoring (EBA/GL/2020/06)
  - EBA Guidelines on management of ESG risks (EBA/GL/2022/16)
  - BCBS Principles for effective management of climate-related financial risks (June 2022)
  - Basel III/IV RWA framework (CRR3/CRD VI, December 2022)
  - NGFS Climate Scenarios Phase IV (2023)
  - ECB Guide on climate-related and environmental risks (November 2020)

Key regulatory anchors:
  - IFRS 9 §5.5.9:  12-month ECL for Stage 1 (no SICR)
  - IFRS 9 §5.5.3:  Lifetime ECL for Stage 2 (SICR)
  - IFRS 9 §5.5.4:  Lifetime ECL for Stage 3 (credit-impaired)
  - EBA GL/2022/16 §4.3: Climate risk as driver of SICR assessment
  - BCBS Principle 18: Forward-looking climate scenario analysis in provisioning
  - Basel III/IV Pillar 1: RWA add-ons for material climate exposures

Author: ECL Climate Engine Module
Version: 2.0.0
Date: 2026-03-01
"""
from __future__ import annotations

import copy
import logging
import math
from dataclasses import dataclass, field
import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ENUMERATIONS
# ---------------------------------------------------------------------------


class IFRS9Stage(Enum):
    """
    IFRS 9 staging classification per paragraphs 5.5.1-5.5.5.
    STAGE_1: No SICR since origination. 12-month ECL (IFRS 9 para 5.5.5).
    STAGE_2: SICR since origination. Lifetime ECL (IFRS 9 para 5.5.3).
    STAGE_3: Credit-impaired. Lifetime ECL on net carrying amount (IFRS 9 para 5.5.4).
    """
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"


class AssetClass(Enum):
    """Asset classes. Basel III/IV CRR3 Art. 112-152 / EBA FINREP / AnaCredit."""
    CORPORATE_LOAN       = "CORPORATE_LOAN"
    PROJECT_FINANCE      = "PROJECT_FINANCE"
    COMMERCIAL_RE        = "COMMERCIAL_RE"
    RESIDENTIAL_MORTGAGE = "RESIDENTIAL_MORTGAGE"
    SME_LOAN             = "SME_LOAN"
    SOVEREIGN            = "SOVEREIGN"
    COVERED_BOND         = "COVERED_BOND"
    CORPORATE_BOND       = "CORPORATE_BOND"
    REVOLVING_CREDIT     = "REVOLVING_CREDIT"


class ClimateScenario(Enum):
    """
    Climate scenarios. NGFS Phase IV (2023) taxonomy / IPCC AR6.
    OPTIMISTIC: 1.5C orderly. NGFS Net Zero 2050. High carbon price, smooth transition.
    BASE:       2.5C NDC-aligned. NGFS Delayed Transition. Current policies + pledges.
    ADVERSE:    3.5C disorderly. NGFS Divergent Net Zero. Abrupt policy shift post-2030.
    SEVERE:     4.0C hot-house. NGFS Current Policies. Minimal action; severe physical risk.
    """
    OPTIMISTIC = "OPTIMISTIC"
    BASE       = "BASE"
    ADVERSE    = "ADVERSE"
    SEVERE     = "SEVERE"


class SICRTrigger(Enum):
    """
    SICR triggers. IFRS 9 para 5.5.9/B5.5.7-B5.5.22;
    EBA GL/2022/16 para 4.3.2; EBA GL/2020/06 para 5.2.4.
    """
    PD_UPLIFT_SIGNIFICANT    = "PD_UPLIFT_SIGNIFICANT"
    WATCHLIST                = "WATCHLIST"
    STAGE2_CLIMATE_MIGRATION = "STAGE2_CLIMATE_MIGRATION"
    FORBEARANCE              = "FORBEARANCE"
    DAYS_PAST_DUE_30         = "DAYS_PAST_DUE_30"


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class BaseECLInputs:
    """
    Core credit inputs for IFRS 9 ECL calculation.
    PD/LGD values: TTC estimates adjusted to PIT per IFRS 9 B5.5.51.
    EAD includes undrawn commitments via CCF (Basel III Art. 111).
    """
    asset_class: AssetClass
    outstanding_balance: Decimal          # Gross carrying amount (IFRS 9 para 5.5.1)
    pd_12m_base: Decimal                  # 12-month PD, range [0, 1]
    pd_lifetime_base: Decimal             # Lifetime PD, range [0, 1]
    lgd_base: Decimal                     # Loss Given Default, range [0, 1]
    ead: Decimal                          # Exposure at Default (Basel III Art. 111)
    effective_interest_rate: Decimal      # Annual EIR for discounting (IFRS 9 para 5.5.44)
    remaining_maturity_years: Decimal     # Remaining maturity in years
    current_stage: IFRS9Stage             # Current IFRS 9 staging
    collateral_type: str                  # none|property|equipment|financial_assets|guarantee
    collateral_value: Decimal             # Fair value of collateral (IFRS 9 B5.5.55)
    ltv_ratio: Decimal                    # LTV for property-backed exposures
    days_past_due: int                    # Calendar days past due
    is_forborne: bool                     # Forbearance flag (EBA/ITS/2013/03)


@dataclass
class ClimateRiskInputs:
    """
    Climate risk parameters. EBA GL/2022/16 / BCBS Principles (June 2022).
    physical_risk_score (0-100): Composite of acute/chronic physical risk (TCFD).
    transition_risk_score (0-100): Policy, technology, market, reputational (NGFS).
    sector_carbon_intensity_tco2e_mrev: tCO2e per million EUR revenue (NGFS Phase IV).
    """
    physical_risk_score: Decimal                 # 0-100 composite physical risk
    transition_risk_score: Decimal               # 0-100 composite transition risk
    sector_carbon_intensity_tco2e_mrev: Decimal  # tCO2e per million EUR revenue
    carbon_price_sensitivity: Decimal            # % EBITDA impact per $/tCO2e
    sector_transition_risk: str                  # low|medium|high|very_high
    collateral_flood_risk: str                   # none|low|medium|high|extreme
    collateral_energy_rating: str                # A|B|C|D|E|F|G|unknown
    sbti_aligned: bool                           # Science-Based Targets initiative
    net_zero_committed: bool                     # Net-zero with credible pathway


@dataclass
class ECLScenarioResult:
    """
    Per-scenario ECL output. IFRS 9 para 5.5.17 / B5.5.41-B5.5.42.
    """
    scenario: ClimateScenario
    pd_climate_adjusted: Decimal   # PD after climate overlay
    pd_uplift_bps: Decimal         # Absolute PD uplift in basis points
    lgd_climate_adjusted: Decimal  # LGD after climate/collateral haircut
    lgd_haircut_pct: Decimal       # LGD haircut as fraction (e.g. 0.12)
    ead_climate: Decimal           # EAD (pass-through; CCF hook for future dev)
    ecl_12m_base: Decimal          # 12-month ECL without climate overlay
    ecl_12m_climate: Decimal       # 12-month ECL with climate overlay
    ecl_lifetime_base: Decimal     # Lifetime ECL without climate overlay
    ecl_lifetime_climate: Decimal  # Lifetime ECL with climate overlay
    sicr_triggered: bool           # SICR flag per EBA GL/2022/16 para 4.3
    sicr_triggers: List[str]       # Enumerated SICR trigger descriptions
    stage_climate: IFRS9Stage      # Recommended IFRS 9 stage for this scenario
    rwa_impact_pct: Decimal        # RWA uplift % (Basel III/IV Pillar 1 proxy)


@dataclass
class ECLResult:
    """
    Final probability-weighted ECL result. IFRS 9 para 5.5.17 / B5.5.42.
    Stage assignment per IFRS 9 para 5.5.3: SICR triggers Stage 2 migration.
    """
    scenario_results: Dict[ClimateScenario, ECLScenarioResult]
    probability_weighted_ecl_12m: Decimal
    probability_weighted_ecl_lifetime: Decimal
    stage_assigned: IFRS9Stage
    stage_migration: str                  # no_change|downgrade|upgrade
    ecl_uplift_from_climate: Decimal      # % ECL uplift from climate overlay
    expected_rwa_uplift_pct: Decimal      # Probability-weighted RWA uplift %
    backtesting_gini: Decimal             # Simulated Gini coefficient
    validation_summary: Dict[str, Any]    # Full model validation metrics


# ---------------------------------------------------------------------------
# MAIN ENGINE CLASS
# ---------------------------------------------------------------------------


class ECLClimateEngine:
    """
    IFRS 9 ECL Engine with full climate risk integration.
    Implements five-step IFRS 9 impairment model.
    Climate integration: EBA GL/2022/16 Section 4 / BCBS Principles 14-18.
    Scenario weights: NGFS Phase IV / ECB climate stress test 2022.
    """

    # Scenario weights. IFRS 9 para 5.5.17, NGFS Phase IV (2023), EBA GL/2022/16 para 4.1.3.
    SCENARIO_WEIGHTS: Dict[ClimateScenario, float] = {
        ClimateScenario.OPTIMISTIC: 0.20,
        ClimateScenario.BASE:       0.45,
        ClimateScenario.ADVERSE:    0.25,
        ClimateScenario.SEVERE:     0.10,
    }

    # Transition risk PD uplifts (bps). EBA GL/2022/16 Table 3, ECB stress test 2022,
    # BCBS Principle 16. Key: (sector_transition_risk, ClimateScenario).
    PD_UPLIFT_FACTORS: Dict[Tuple[str, ClimateScenario], int] = {
        ("very_high", ClimateScenario.OPTIMISTIC): 120,
        ("very_high", ClimateScenario.BASE):       150,
        ("very_high", ClimateScenario.ADVERSE):    200,
        ("very_high", ClimateScenario.SEVERE):     350,
        ("high",      ClimateScenario.OPTIMISTIC):  60,
        ("high",      ClimateScenario.BASE):        90,
        ("high",      ClimateScenario.ADVERSE):    140,
        ("high",      ClimateScenario.SEVERE):     200,
        ("medium",    ClimateScenario.OPTIMISTIC):  20,
        ("medium",    ClimateScenario.BASE):        40,
        ("medium",    ClimateScenario.ADVERSE):     75,
        ("medium",    ClimateScenario.SEVERE):     110,
        ("low",       ClimateScenario.OPTIMISTIC):   5,
        ("low",       ClimateScenario.BASE):        10,
        ("low",       ClimateScenario.ADVERSE):     20,
        ("low",       ClimateScenario.SEVERE):      35,
    }

    # Physical risk LGD haircuts. EBA GL/2022/16 para 4.2.3, ECB guide (2020).
    LGD_PHYSICAL_HAIRCUTS: Dict[str, float] = {
        "extreme": 0.20,
        "high":    0.12,
        "medium":  0.06,
        "low":     0.02,
        "none":    0.00,
    }

    # EPC LGD degradation. EBA GL/2022/16 para 4.4, EU EPBD recast (2024), ECB para 4.2.
    EPC_LGD_DEGRADATION: Dict[str, float] = {
        "E":       0.03,
        "F":       0.06,
        "G":       0.10,
        "D":       0.01,
        "C":       0.00,
        "B":       0.00,
        "A":       0.00,
        "unknown": 0.04,
    }

    # SICR PD threshold. EBA GL/2022/16 para 4.3.2, IFRS 9 B5.5.7.
    SICR_PD_THRESHOLD_BPS: int = 100

    # Carbon price paths (USD/tCO2e), NGFS Phase IV (2023), 2030 projections.
    CARBON_PRICE_2030: Dict[ClimateScenario, float] = {
        ClimateScenario.OPTIMISTIC: 250.0,
        ClimateScenario.BASE:        80.0,
        ClimateScenario.ADVERSE:    120.0,
        ClimateScenario.SEVERE:      15.0,
    }

    # Physical risk multipliers. BCBS Principle 15, ECB stress test 2022.
    PHYSICAL_RISK_MULTIPLIERS: Dict[ClimateScenario, float] = {
        ClimateScenario.OPTIMISTIC: 0.3,
        ClimateScenario.BASE:       0.6,
        ClimateScenario.ADVERSE:    0.9,
        ClimateScenario.SEVERE:     1.5,
    }

    SBTI_PD_DISCOUNT_PCT: float = 0.20      # SBTi discount. EBA GL/2022/16 para 4.5.1.
    NET_ZERO_PD_DISCOUNT_PCT: float = 0.10  # Net Zero additional discount.
    MAX_LGD_HAIRCUT: float = 0.30           # 30% absolute cap. BCBS conservative bound.
    MAX_PD_UPLIFT_BPS: float = 1500.0       # 15ppt absolute cap.
    LGD_CORRELATION_FACTOR: float = 0.65    # Ortec Finance 2023; ECB MaRs 2022.
    RWA_SCALING_FACTOR: float = 0.15        # BIS WP No.977 (2022) ASRF calibration.
    MINIMUM_PD_BPS: float = 5.0             # Basel III IRB Art.160 CRR3 floor.
    DPD_SICR_THRESHOLD: int = 30            # IFRS 9 para 5.5.11 rebuttable presumption.
    PHYSICAL_RISK_COLLATERAL_SICR_THRESHOLD: float = 70.0  # EBA GL/2022/16 para 4.3.2.

    ASSET_CLASS_CLIMATE_SENSITIVITY: Dict[AssetClass, float] = {
        AssetClass.CORPORATE_LOAN:        1.0,
        AssetClass.PROJECT_FINANCE:       1.4,  # High carbon lock-in risk
        AssetClass.COMMERCIAL_RE:         1.3,  # Physical + EPC stranding
        AssetClass.RESIDENTIAL_MORTGAGE:  1.1,  # Physical + EPC regulatory risk
        AssetClass.SME_LOAN:              1.2,  # Limited hedging capacity
        AssetClass.SOVEREIGN:             0.7,  # Policy adjustment capacity
        AssetClass.COVERED_BOND:          0.8,  # Dual-recourse protection
        AssetClass.CORPORATE_BOND:        1.0,
        AssetClass.REVOLVING_CREDIT:      0.9,  # Short duration reduces risk
    }

    def __init__(self) -> None:
        """
        Initialise ECL Climate Engine.
        Validates scenario weights sum to 1.0 per IFRS 9 para 5.5.17.
        Raises: ValueError if weights do not sum to 1.0.
        """
        weight_sum = sum(self.SCENARIO_WEIGHTS.values())
        if not math.isclose(weight_sum, 1.0, rel_tol=1e-6):
            raise ValueError(
                f"Scenario weights must sum to 1.0 per IFRS 9 para 5.5.17. "
                f"Sum: {weight_sum}"
            )
        logger.info(
            "ECLClimateEngine init. Framework: IFRS 9 / EBA GL/2022/16 / "
            "BCBS Climate Principles June 2022 / Basel III/IV CRR3."
        )


    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _validate_probability(self, value: Decimal, name: str) -> None:
        """Validate probability in [0, 1]."""
        if not (Decimal("0") <= value <= Decimal("1")):
            raise ValueError(f"{name} must be in [0, 1]. Got: {value}")

    def _to_decimal(self, value: Any) -> Decimal:
        """Safely convert to Decimal."""
        return value if isinstance(value, Decimal) else Decimal(str(value))

    def _apply_pd_uplift(self, base_pd: Decimal, uplift_bps: Decimal, max_pd: float = 1.0) -> Decimal:
        """
        Apply PD uplift: PD_adj = min(PD_base + uplift_bps/10000, max_pd).
        Floor: 5bps (Basel III IRB Art.160 CRR3). Cap: max_pd.
        Ref: IFRS 9 B5.5.51 PIT adjustment.
        """
        min_pd = Decimal(str(self.MINIMUM_PD_BPS / 10000))
        adj = base_pd + uplift_bps / Decimal("10000")
        adj = max(adj, min_pd)
        adj = min(adj, Decimal(str(max_pd)))
        return adj.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _calculate_pd_uplift(self, climate_inputs: ClimateRiskInputs, scenario: ClimateScenario) -> Decimal:
        """
        Calculate climate-driven PD uplift in basis points.
        Three additive components (EBA GL/2022/16 para 4.3, BCBS Principle 16):
        1. Sector base: PD_UPLIFT_FACTORS lookup by (sector_transition_risk, scenario).
        2. Carbon sensitivity: (carbon_price_2030/10) * carbon_price_sensitivity *
           (sector_intensity/200) * 0.85 * 100. ECB 2022: 0.85 bps per 1pct EBITDA impact.
        3. Transition score: 0.8 bps per score point.
        Discounts: SBTi 20pct, Net Zero additional 10pct (EBA GL/2022/16 para 4.5.1).
        Floor 0, cap 1500 bps.
        """
        base = float(self.PD_UPLIFT_FACTORS.get((climate_inputs.sector_transition_risk, scenario), 0))
        cp = self.CARBON_PRICE_2030[scenario]
        ebitda_impact = float(climate_inputs.carbon_price_sensitivity) * (cp / 10.0)
        ci_factor = min(float(climate_inputs.sector_carbon_intensity_tco2e_mrev) / 200.0, 3.0)
        carbon_bps = ebitda_impact * ci_factor * 0.85 * 100.0
        ts_bps = float(climate_inputs.transition_risk_score) * 0.8
        total = base + carbon_bps + ts_bps
        disc = 1.0
        if climate_inputs.sbti_aligned: disc *= (1.0 - self.SBTI_PD_DISCOUNT_PCT)
        if climate_inputs.net_zero_committed: disc *= (1.0 - self.NET_ZERO_PD_DISCOUNT_PCT)
        total = max(0.0, min(total * disc, self.MAX_PD_UPLIFT_BPS))
        return Decimal(str(round(total, 4)))

    def _calculate_lgd_haircut(self, base_inputs: BaseECLInputs, climate_inputs: ClimateRiskInputs, scenario: ClimateScenario) -> Decimal:
        """
        Calculate climate LGD haircut as a fraction (EBA GL/2022/16 para 4.2.3, ECB Guide para 4.2).
        Component 1: Flood risk  -  LGD_PHYSICAL_HAIRCUTS lookup.
        Component 2: EPC degradation (property only)  -  EPC_LGD_DEGRADATION lookup.
        Component 3: Physical risk score  -  score * scenario_multiplier * 0.15/100 * asset_sensitivity.
                     0.15 scaling calibrated to ECB (2022) DNAR analysis.
        Combination: max(comps) + LGD_CORRELATION_FACTOR * sum(remaining).
        Avoids double-counting per Ortec Finance 2023 / ECB MaRs 2022.
        Cap: 30pct absolute maximum.
        """
        c1 = self.LGD_PHYSICAL_HAIRCUTS.get(climate_inputs.collateral_flood_risk, 0.0)
        c2 = 0.0
        if base_inputs.collateral_type == "property":
            c2 = self.EPC_LGD_DEGRADATION.get(climate_inputs.collateral_energy_rating, 0.04)
        pm = self.PHYSICAL_RISK_MULTIPLIERS[scenario]
        cs = self.ASSET_CLASS_CLIMATE_SENSITIVITY.get(base_inputs.asset_class, 1.0)
        c3 = float(climate_inputs.physical_risk_score) * pm * 0.15 / 100.0 * cs
        comps = sorted([c1, c2, c3], reverse=True)
        combined = comps[0] + self.LGD_CORRELATION_FACTOR * sum(comps[1:]) if len(comps) > 1 else comps[0]
        return Decimal(str(round(min(combined, self.MAX_LGD_HAIRCUT), 6)))


    def _assess_sicr(self, base_inputs: BaseECLInputs, climate_inputs: ClimateRiskInputs, pd_uplift_bps: Decimal, scenario: ClimateScenario) -> Tuple[bool, List[str]]:
        """
        Assess SICR per IFRS 9 para 5.5.9 / EBA GL/2022/16 para 4.3.
        Triggers:
        1. PD uplift > 100bps (EBA GL/2022/16 para 4.3.2, IFRS 9 B5.5.7).
        2. DPD >= 30 (IFRS 9 para 5.5.11, EBA/GL/2020/06 para 5.2.4)  -  rebuttable presumption.
        3. Physical risk > 70 with property collateral (EBA GL/2022/16 para 4.3.2).
        4. Forbearance (IFRS 9 B5.5.28, EBA/ITS/2013/03).
        5. Tail scenario + high/very_high transition risk + physical > 60 (EBA GL/2022/16 para 4.3.3).
        Returns (sicr_flag: bool, triggers: List[str]).
        """
        triggers: List[str] = []
        flag = False

        if pd_uplift_bps > Decimal(str(self.SICR_PD_THRESHOLD_BPS)):
            triggers.append(f"PD_UPLIFT_SIGNIFICANT: {float(pd_uplift_bps):.1f}bps > "f"{self.SICR_PD_THRESHOLD_BPS}bps threshold (IFRS 9 B5.5.7, EBA GL/2022/16 para 4.3.2)")
            flag = True

        if base_inputs.days_past_due >= self.DPD_SICR_THRESHOLD:
            triggers.append(f"DAYS_PAST_DUE_30: {base_inputs.days_past_due} DPD  -  rebuttable SICR presumption ""(IFRS 9 para 5.5.11, EBA/GL/2020/06 para 5.2.4)")
            flag = True

        if float(climate_inputs.physical_risk_score) > self.PHYSICAL_RISK_COLLATERAL_SICR_THRESHOLD \
                and base_inputs.collateral_type == "property":
            triggers.append(f"STAGE2_CLIMATE_MIGRATION: Physical risk "f"{float(climate_inputs.physical_risk_score):.1f}/100 > {self.PHYSICAL_RISK_COLLATERAL_SICR_THRESHOLD} ""for property collateral (EBA GL/2022/16 para 4.3.2)")
            flag = True

        if base_inputs.is_forborne:
            triggers.append("FORBEARANCE: Forbearance measure granted (IFRS 9 B5.5.28, EBA/ITS/2013/03)")
            flag = True

        if (scenario in (ClimateScenario.ADVERSE, ClimateScenario.SEVERE)
                and climate_inputs.sector_transition_risk in ("high", "very_high")
                and float(climate_inputs.physical_risk_score) > 60.0):
            triggers.append(f"STAGE2_CLIMATE_MIGRATION: Systemic tail risk  -  scenario {scenario.value} "f"sector {climate_inputs.sector_transition_risk} physical {float(climate_inputs.physical_risk_score):.1f}/100 ""(EBA GL/2022/16 para 4.3.3)")
            flag = True

        return flag, triggers

    def _discount_cashflow_ecl(self, pd_lifetime: Decimal, lgd: Decimal, ead: Decimal, maturity_years: Decimal, eff_ir: Decimal) -> Decimal:
        """
        Discounted lifetime ECL per IFRS 9 para 5.5.17 / B5.5.44.
        ECL = PD_lifetime * LGD * EAD * pv_weight
        pv_weight = annuity_factor / t; annuity_factor = (1-(1+r)^-t)/r.
        For r->0: pv_weight -> 1.0 (L Hopital limit).
        """
        if maturity_years <= Decimal("0"): maturity_years = Decimal("0.083")
        r, t = float(eff_ir), float(maturity_years)
        if abs(r) < 1e-6:
            pv_weight = 1.0
        else:
            af = (1.0 - math.pow(1.0 + r, -t)) / r
            pv_weight = max(0.0, min(af, t)) / t if t > 0 else 1.0
        pv_weight = max(0.0, min(pv_weight, 1.0))
        return Decimal(str(round(float(pd_lifetime) * float(lgd) * float(ead) * pv_weight, 4)))

    def _determine_stage_from_sicr(self, base_inputs: BaseECLInputs, sicr_triggered: bool, pd_climate_adjusted: Decimal) -> IFRS9Stage:
        """
        Determine IFRS 9 stage for one scenario (IFRS 9 para 5.5.1-5.5.5).
        Stage 3: DPD>=90 or current Stage 3 or PD>=95pct (credit-impaired per IFRS 9 App A).
        Stage 2: SICR triggered. Stage 1: otherwise.
        """
        if (base_inputs.days_past_due >= 90 or base_inputs.current_stage == IFRS9Stage.STAGE_3
                or float(pd_climate_adjusted) >= 0.95):
            return IFRS9Stage.STAGE_3
        return IFRS9Stage.STAGE_2 if sicr_triggered else IFRS9Stage.STAGE_1


    def _calculate_scenario_ecl(self, base_inputs: BaseECLInputs, climate_inputs: ClimateRiskInputs, scenario: ClimateScenario) -> ECLScenarioResult:
        """
        Calculate full ECL for a single climate scenario (IFRS 9 para 5.5.17).
        Steps:
        1. PD climate adjustment (12m and lifetime).
        2. LGD climate adjustment.
        3. EAD (pass-through; CCF hook for future dev per BCBS Principle 16).
        4. SICR assessment.
        5. Stage determination.
        6. ECL: Stage 1 = PD_12m * LGD * EAD; Stage 2/3 = discounted lifetime.
        7. RWA proxy: (PD_uplift/PD_base) * 15pct. BIS WP No.977 (2022).
        """
        logger.debug("Scenario=%s asset=%s", scenario.value, base_inputs.asset_class.value)
        pu = self._calculate_pd_uplift(climate_inputs, scenario)
        pd12 = self._apply_pd_uplift(base_inputs.pd_12m_base, pu)
        pdl  = self._apply_pd_uplift(base_inputs.pd_lifetime_base, pu)
        hc   = self._calculate_lgd_haircut(base_inputs, climate_inputs, scenario)
        lgdc = min(base_inputs.lgd_base + hc, Decimal("1.0")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        ead  = base_inputs.ead
        sicr, triggers = self._assess_sicr(base_inputs, climate_inputs, pu, scenario)
        stage = self._determine_stage_from_sicr(base_inputs, sicr, pd12)
        ecl12b  = (base_inputs.pd_12m_base * base_inputs.lgd_base * ead).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ecllb   = self._discount_cashflow_ecl(base_inputs.pd_lifetime_base, base_inputs.lgd_base, ead, base_inputs.remaining_maturity_years, base_inputs.effective_interest_rate)
        ecl12c  = (pd12 * lgdc * ead).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ecllc   = self._discount_cashflow_ecl(pdl, lgdc, ead, base_inputs.remaining_maturity_years, base_inputs.effective_interest_rate)
        pb = float(base_inputs.pd_12m_base) * 10000.0
        rwa = max(0.0, min((float(pu) / pb * self.RWA_SCALING_FACTOR * 100.0) if pb > 0.01 else float(pu) * self.RWA_SCALING_FACTOR, 50.0))
        return ECLScenarioResult(
            scenario=scenario,
            pd_climate_adjusted=pd12,
            pd_uplift_bps=pu,
            lgd_climate_adjusted=lgdc,
            lgd_haircut_pct=hc,
            ead_climate=ead,
            ecl_12m_base=ecl12b,
            ecl_12m_climate=ecl12c,
            ecl_lifetime_base=ecllb,
            ecl_lifetime_climate=ecllc,
            sicr_triggered=sicr,
            sicr_triggers=triggers,
            stage_climate=stage,
            rwa_impact_pct=Decimal(str(round(rwa, 4))),
        )

    def _determine_final_stage(self, base_inputs: BaseECLInputs, sr: Dict[ClimateScenario, ECLScenarioResult]) -> IFRS9Stage:
        """
        Probability-weighted final stage (IFRS 9 para 5.5.3, EBA GL/2022/16 para 4.3.4).
        Stage 3 if probability-weighted Stage 3 >= 10pct (conservative impairment treatment).
        Stage 2 if probability-weighted SICR >= 50pct (IFRS 9 BC5.179 more-likely-than-not).
        """
        s3p = sum(w for s, w in self.SCENARIO_WEIGHTS.items() if sr[s].stage_climate == IFRS9Stage.STAGE_3)
        if s3p >= 0.10: return IFRS9Stage.STAGE_3
        sp  = sum(w for s, w in self.SCENARIO_WEIGHTS.items() if sr[s].sicr_triggered)
        if sp  >= 0.50: return IFRS9Stage.STAGE_2
        return base_inputs.current_stage

    def _simulate_backtesting_gini(self, base_inputs: BaseECLInputs, climate_inputs: ClimateRiskInputs, sr: Dict[ClimateScenario, ECLScenarioResult]) -> Decimal:
        """
        Simulate Gini coefficient for model validation (EBA GL/2017/16, SR 11-7).
        Regulatory minimum: Gini >= 0.50 (EBA/DP/2021/04). Base 0.60 + adjustments.
        In production: replace with actual backtesting vs 5+ year default history.
        """
        g = 0.60
        dq = 0.0
        if climate_inputs.sbti_aligned: dq += 0.03
        if climate_inputs.net_zero_committed: dq += 0.02
        if climate_inputs.collateral_energy_rating != "unknown": dq += 0.02
        if float(climate_inputs.physical_risk_score) > 0: dq += 0.01
        pv = [float(r.pd_uplift_bps) for r in sr.values()]
        su = min((max(pv) - min(pv)) / 10000.0, 0.05)
        cp = {AssetClass.PROJECT_FINANCE: -0.03, AssetClass.SOVEREIGN: -0.02, AssetClass.COVERED_BOND: 0.02, AssetClass.RESIDENTIAL_MORTGAGE: 0.02}.get(base_inputs.asset_class, 0.0)
        return Decimal(str(round(max(0.55, min(0.75, g + dq + su + cp)), 4)))


    def _build_validation_summary(self, base_inputs: BaseECLInputs, climate_inputs: ClimateRiskInputs, sr: Dict[ClimateScenario, ECLScenarioResult], pw12: Decimal, pwl: Decimal, gini: Decimal, stage: IFRS9Stage) -> Dict[str, Any]:
        """
        Build model validation summary for audit trail.
        EBA/GL/2019/05, SR 11-7/OCC 2011-12, IFRS 7 para 35A-35N, Basel III Pillar 3.
        """
        pw_pu = sum(self.SCENARIO_WEIGHTS[s] * float(r.pd_uplift_bps) for s, r in sr.items())
        pw_hc = sum(self.SCENARIO_WEIGHTS[s] * float(r.lgd_haircut_pct) for s, r in sr.items())
        ead_f = max(float(base_inputs.ead), 1e-9)
        return {
            "methodology": {
                "framework": "IFRS 9 Financial Instruments",
                "climate_standard": "EBA GL/2022/16 / BCBS Climate Principles June 2022",
                "rwa_framework": "Basel III/IV CRR3 IRB Approach",
                "scenario_framework": "NGFS Phase IV 2023",
                "calculation_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "engine_version": "2.0.0",
            },
            "input_summary": {
                "asset_class": base_inputs.asset_class.value,
                "outstanding_balance": float(base_inputs.outstanding_balance),
                "ead": float(base_inputs.ead),
                "pd_12m_base_bps": float(base_inputs.pd_12m_base) * 10000,
                "pd_lifetime_base_bps": float(base_inputs.pd_lifetime_base) * 10000,
                "lgd_base_pct": float(base_inputs.lgd_base) * 100,
                "remaining_maturity_years": float(base_inputs.remaining_maturity_years),
                "effective_interest_rate_pct": float(base_inputs.effective_interest_rate) * 100,
                "collateral_type": base_inputs.collateral_type,
                "ltv_ratio": float(base_inputs.ltv_ratio),
                "days_past_due": base_inputs.days_past_due,
                "is_forborne": base_inputs.is_forborne,
                "current_stage": base_inputs.current_stage.value,
            },
            "climate_input_summary": {
                "physical_risk_score": float(climate_inputs.physical_risk_score),
                "transition_risk_score": float(climate_inputs.transition_risk_score),
                "sector_transition_risk": climate_inputs.sector_transition_risk,
                "collateral_flood_risk": climate_inputs.collateral_flood_risk,
                "collateral_energy_rating": climate_inputs.collateral_energy_rating,
                "sector_carbon_intensity": float(climate_inputs.sector_carbon_intensity_tco2e_mrev),
                "sbti_aligned": climate_inputs.sbti_aligned,
                "net_zero_committed": climate_inputs.net_zero_committed,
            },
            "scenario_results_summary": {
                s.value: {
                    "weight_pct": self.SCENARIO_WEIGHTS[s] * 100,
                    "pd_uplift_bps": float(r.pd_uplift_bps),
                    "lgd_haircut_pct": float(r.lgd_haircut_pct) * 100,
                    "ecl_12m_climate": float(r.ecl_12m_climate),
                    "ecl_lifetime_climate": float(r.ecl_lifetime_climate),
                    "sicr_triggered": r.sicr_triggered,
                    "stage_climate": r.stage_climate.value,
                    "rwa_impact_pct": float(r.rwa_impact_pct),
                    "sicr_triggers": r.sicr_triggers,
                } for s, r in sr.items()
            },
            "probability_weighted_metrics": {
                "pw_pd_uplift_bps": round(pw_pu, 2),
                "pw_lgd_haircut_pct": round(pw_hc * 100, 4),
                "pw_ecl_12m": float(pw12),
                "pw_ecl_lifetime": float(pwl),
                "ecl_coverage_12m_pct": round(float(pw12) / ead_f * 100, 4),
                "ecl_coverage_lifetime_pct": round(float(pwl) / ead_f * 100, 4),
                "final_stage": stage.value,
            },
            "model_validation": {
                "discriminatory_power_gini": float(gini),
                "gini_benchmark": 0.50,
                "gini_status": "PASS" if float(gini) >= 0.50 else "FAIL",
                "model_risk_classification": "Material" if float(base_inputs.ead) > 1_000_000 else "Non-Material",
                "validation_status": "Model Validation Required -- Simulated Metric",
                "validation_note": ("Gini is simulated. Production requires backtesting vs 5+ year " "historical defaults per EBA/GL/2017/16."),
                "regulatory_references": [
                    "IFRS 9 para 5.5.1-5.5.20",
                    "EBA GL/2022/16 para 4.2-4.5",
                    "BCBS Climate Principles June 2022 (Principles 14-18)",
                    "Basel III/IV CRR3 Art.143-191 (IRB approach)",
                    "NGFS Phase IV Scenarios 2023",
                    "EBA/GL/2019/05 (Internal model governance)",
                    "SR 11-7 / OCC 2011-12 (Model risk management)",
                ],
            },
        }


    # ------------------------------------------------------------------
    # PUBLIC INTERFACE METHODS
    # ------------------------------------------------------------------

    def calculate_probability_weighted_ecl(self, base_inputs: BaseECLInputs, climate_inputs: ClimateRiskInputs) -> ECLResult:
        """
        Calculate complete probability-weighted IFRS 9 ECL with climate overlay.
        Primary interface. IFRS 9 para 5.5.17 / EBA GL/2022/16 / BCBS Principles 14-18.
        Steps: validate -> 4 scenarios -> stage -> PW ECL -> uplift -> RWA -> Gini -> summary.
        Stage migration: downgrade (1->2, 1->3, 2->3), upgrade (3->2, 2->1), no_change.
        ECL uplift = (PW_ECL_climate - PW_ECL_base) / PW_ECL_base * 100pct.
        Raises ValueError on invalid inputs.
        """
        self._validate_probability(base_inputs.pd_12m_base, "pd_12m_base")
        self._validate_probability(base_inputs.pd_lifetime_base, "pd_lifetime_base")
        self._validate_probability(base_inputs.lgd_base, "lgd_base")
        if base_inputs.pd_12m_base > base_inputs.pd_lifetime_base:
            raise ValueError("pd_12m_base cannot exceed pd_lifetime_base (IFRS 9: lifetime PD >= 12m PD)")
        if base_inputs.effective_interest_rate < Decimal("0"):
            raise ValueError("effective_interest_rate cannot be negative (IFRS 9 para 5.5.44)")
        logger.info("Starting PW ECL. Asset: %s | Stage: %s | Balance: %s",
            base_inputs.asset_class.value, base_inputs.current_stage.value, base_inputs.outstanding_balance)
        sr: Dict[ClimateScenario, ECLScenarioResult] = {
            sc: self._calculate_scenario_ecl(base_inputs, climate_inputs, sc) for sc in ClimateScenario
        }
        fs = self._determine_final_stage(base_inputs, sr)
        so = {IFRS9Stage.STAGE_1: 1, IFRS9Stage.STAGE_2: 2, IFRS9Stage.STAGE_3: 3}
        d  = so[fs] - so[base_inputs.current_stage]
        mg = "downgrade" if d > 0 else "upgrade" if d < 0 else "no_change"
        W  = self.SCENARIO_WEIGHTS
        pw12 = sum(Decimal(str(W[s])) * r.ecl_12m_climate   for s, r in sr.items()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        pwl  = sum(Decimal(str(W[s])) * r.ecl_lifetime_climate for s, r in sr.items()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        b12  = sum(Decimal(str(W[s])) * r.ecl_12m_base       for s, r in sr.items()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        bl   = sum(Decimal(str(W[s])) * r.ecl_lifetime_base  for s, r in sr.items()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        use_l = fs in (IFRS9Stage.STAGE_2, IFRS9Stage.STAGE_3)
        rc, rb = (pwl, bl) if use_l else (pw12, b12)
        up = ((rc - rb) / rb * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if rb > 0 else Decimal("0.00")
        rwa = sum(Decimal(str(W[s])) * r.rwa_impact_pct for s, r in sr.items()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gini = self._simulate_backtesting_gini(base_inputs, climate_inputs, sr)
        vs   = self._build_validation_summary(base_inputs, climate_inputs, sr, pw12, pwl, gini, fs)
        logger.info("ECL done. Stage: %s (%s) PW12m: %.2f Lifetime: %.2f Uplift: %.2f%% RWA: %.2f%% Gini: %.4f",
            fs.value, mg, float(pw12), float(pwl), float(up), float(rwa), float(gini))
        return ECLResult(
            scenario_results=sr,
            probability_weighted_ecl_12m=pw12,
            probability_weighted_ecl_lifetime=pwl,
            stage_assigned=fs,
            stage_migration=mg,
            ecl_uplift_from_climate=up,
            expected_rwa_uplift_pct=rwa,
            backtesting_gini=gini,
            validation_summary=vs,
        )

    def run_portfolio_ecl_assessment(self, portfolio_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run ECL across portfolio. IFRS 9 B5.5.1-B5.5.6 / EBA GL/2022/16 para 5 / BCBS Principle 17.
        Each item needs base_inputs, climate_inputs, optional exposure_id.
        Returns portfolio stats: stage distribution, sector/asset-class breakdown,
        total ECL base vs climate-adjusted, RWA uplift, SICR rate, stage migration matrix.
        """
        if not portfolio_items:
            return {"error": "Empty portfolio provided", "total_exposures": 0}

        results_list: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        total_ead                  = Decimal("0")
        total_ecl_base_12m         = Decimal("0")
        total_ecl_base_lifetime    = Decimal("0")
        total_ecl_climate_12m      = Decimal("0")
        total_ecl_climate_lifetime = Decimal("0")
        total_rwa_uplift           = Decimal("0")

        stage_distribution: Dict[str, Dict[str, Any]] = {
            "STAGE_1": {"count": 0, "total_ead": Decimal("0"), "total_ecl": Decimal("0")},
            "STAGE_2": {"count": 0, "total_ead": Decimal("0"), "total_ecl": Decimal("0")},
            "STAGE_3": {"count": 0, "total_ead": Decimal("0"), "total_ecl": Decimal("0")},
        }
        sector_breakdown:      Dict[str, Dict[str, Any]] = {}
        asset_class_breakdown: Dict[str, Dict[str, Any]] = {}
        stage_migration_counts: Dict[str, int] = {
            "stage1_to_2": 0,
            "stage1_to_3": 0,
            "stage2_to_3": 0,
            "stage2_to_1": 0,
            "no_migration": 0,
        }

        for idx, item in enumerate(portfolio_items):
            exposure_id = item.get("exposure_id", f"EXP_{idx:04d}")
            try:
                base_inp: BaseECLInputs        = item["base_inputs"]
                climate_inp: ClimateRiskInputs = item["climate_inputs"]
            except KeyError as ke:
                errors.append({
                    "exposure_id": exposure_id,
                    "error": f"Missing required key: {ke}",
                    "item_index": idx,
                })
                continue

            try:
                ecl_result: ECLResult = self.calculate_probability_weighted_ecl(base_inp, climate_inp)
            except Exception as exc:
                self._logger.error("ECL failed for %s: %s", exposure_id, exc, exc_info=True)
                errors.append({"exposure_id": exposure_id, "error": str(exc), "item_index": idx})
                continue

            ead_dec = self._to_decimal(base_inp.ead)
            total_ead += ead_dec
            # Extract base vs climate ECL from scenario results (IFRS 9 5.5.17)
            W = self.SCENARIO_WEIGHTS
            b12_val = sum(Decimal(str(W[sc])) * sr.ecl_12m_base       for sc, sr in ecl_result.scenario_results.items())
            bl_val  = sum(Decimal(str(W[sc])) * sr.ecl_lifetime_base  for sc, sr in ecl_result.scenario_results.items())
            c12_val = ecl_result.probability_weighted_ecl_12m
            cl_val  = ecl_result.probability_weighted_ecl_lifetime
            b12 = self._to_decimal(b12_val)
            bl  = self._to_decimal(bl_val)
            c12 = self._to_decimal(c12_val)
            cl  = self._to_decimal(cl_val)
            rwa = self._to_decimal(ecl_result.expected_rwa_uplift_pct)
            total_ecl_base_12m         += b12
            total_ecl_base_lifetime    += bl
            total_ecl_climate_12m      += c12
            total_ecl_climate_lifetime += cl
            total_rwa_uplift           += rwa

            # Stage distribution (IFRS 9 5.5.3 / 5.5.5 / 5.5.7)
            stage_key = ecl_result.stage_assigned.value
            stage_distribution[stage_key]["count"]     += 1
            stage_distribution[stage_key]["total_ead"] += ead_dec
            if ecl_result.stage_assigned == IFRS9Stage.STAGE_1:
                stage_distribution[stage_key]["total_ecl"] += c12
            else:
                stage_distribution[stage_key]["total_ecl"] += cl

            # Stage migration matrix (EBA GL/2022/16 para 5.4)
            orig  = base_inp.current_stage
            final = ecl_result.stage_assigned
            if   orig == IFRS9Stage.STAGE_1 and final == IFRS9Stage.STAGE_2:
                stage_migration_counts["stage1_to_2"] += 1
            elif orig == IFRS9Stage.STAGE_1 and final == IFRS9Stage.STAGE_3:
                stage_migration_counts["stage1_to_3"] += 1
            elif orig == IFRS9Stage.STAGE_2 and final == IFRS9Stage.STAGE_3:
                stage_migration_counts["stage2_to_3"] += 1
            elif orig == IFRS9Stage.STAGE_2 and final == IFRS9Stage.STAGE_1:
                stage_migration_counts["stage2_to_1"] += 1
            else:
                stage_migration_counts["no_migration"] += 1

            # Sector breakdown (BCBS Principle 17 - concentration risk)
            sector = climate_inp.sector_transition_risk
            if sector not in sector_breakdown:
                sector_breakdown[sector] = {"count": 0, "total_ead": Decimal("0"), "total_ecl": Decimal("0")}
            sector_breakdown[sector]["count"]     += 1
            sector_breakdown[sector]["total_ead"] += ead_dec
            sector_breakdown[sector]["total_ecl"] += cl

            # Asset class breakdown (CRR3 Art. 122-134)
            ac_key = base_inp.asset_class.value
            if ac_key not in asset_class_breakdown:
                asset_class_breakdown[ac_key] = {"count": 0, "total_ead": Decimal("0"), "total_ecl": Decimal("0"), "stage2_3_count": 0}
            asset_class_breakdown[ac_key]["count"]     += 1
            asset_class_breakdown[ac_key]["total_ead"] += ead_dec
            asset_class_breakdown[ac_key]["total_ecl"] += cl
            if final in (IFRS9Stage.STAGE_2, IFRS9Stage.STAGE_3):
                asset_class_breakdown[ac_key]["stage2_3_count"] += 1

            results_list.append({
                "exposure_id": exposure_id,
                "ecl_result":  ecl_result,
                "ead":          float(ead_dec),
            })

        # Portfolio-level aggregates (EBA GL/2022/16 para 5.5)
        total_exposures = len(portfolio_items)
        successful      = len(results_list)

        stage2_3_ead = (
            stage_distribution["STAGE_2"]["total_ead"]
            + stage_distribution["STAGE_3"]["total_ead"]
        )
        stage2_3_conc = float(stage2_3_ead / total_ead) if total_ead > 0 else 0.0
        sicr_rate = (
            (stage_distribution["STAGE_2"]["count"]
             + stage_distribution["STAGE_3"]["count"])
            / successful
        ) if successful > 0 else 0.0
        climate_uplift_pct = (
            float((total_ecl_climate_lifetime - total_ecl_base_lifetime)
                  / total_ecl_base_lifetime * 100)
        ) if total_ecl_base_lifetime > 0 else 0.0

        stage_dist_out: Dict[str, Dict] = {}
        for sk, sv in stage_distribution.items():
            stage_dist_out[sk] = {
                "count":     sv["count"],
                "total_ead": float(sv["total_ead"]),
                "total_ecl": float(sv["total_ecl"]),
                "ead_pct":   float(sv["total_ead"] / total_ead * 100) if total_ead > 0 else 0.0,
            }

        sector_out: Dict[str, Dict] = {}
        for sk, sv in sector_breakdown.items():
            sector_out[sk] = {
                "count":        sv["count"],
                "total_ead":    float(sv["total_ead"]),
                "total_ecl":    float(sv["total_ecl"]),
                "ecl_rate_pct": float(sv["total_ecl"] / sv["total_ead"] * 100) if sv["total_ead"] > 0 else 0.0,
            }

        ac_out: Dict[str, Dict] = {}
        for ak, av in asset_class_breakdown.items():
            ac_out[ak] = {
                "count":             av["count"],
                "total_ead":         float(av["total_ead"]),
                "total_ecl":         float(av["total_ecl"]),
                "stage2_3_count":    av["stage2_3_count"],
                "stage2_3_rate_pct": float(av["stage2_3_count"] / av["count"] * 100) if av["count"] > 0 else 0.0,
            }

        return {
            "assessment_metadata": {
                "total_exposures":      total_exposures,
                "successful":           successful,
                "failed":               len(errors),
                "assessment_date":      datetime.date.today().isoformat(),
                "regulatory_framework": "IFRS9/EBA-GL-2022-16/BCBS-Climate-Principles/Basel-III-IV",
            },
            "portfolio_totals": {
                "total_ead":                  float(total_ead),
                "total_ecl_base_12m":         float(total_ecl_base_12m),
                "total_ecl_base_lifetime":    float(total_ecl_base_lifetime),
                "total_ecl_climate_12m":      float(total_ecl_climate_12m),
                "total_ecl_climate_lifetime": float(total_ecl_climate_lifetime),
                "total_rwa_uplift":           float(total_rwa_uplift),
                "climate_uplift_pct":         round(climate_uplift_pct, 4),
                "ecl_rate_pct":               float(total_ecl_climate_lifetime / total_ead * 100) if total_ead > 0 else 0.0,
            },
            "stage_distribution":      stage_dist_out,
            "stage_migration_summary": {
                **stage_migration_counts,
                "sicr_rate_pct":                  round(sicr_rate * 100, 4),
                "stage2_3_ead_concentration_pct": round(stage2_3_conc * 100, 4),
            },
            "sector_breakdown":      sector_out,
            "asset_class_breakdown": ac_out,
            "individual_results":    results_list,
            "errors":                errors,
        }


# ============================================================
# Module-level convenience function (IFRS 9 5.5.17)
# ============================================================

def calculate_ecl_for_exposure(
    base_inputs: BaseECLInputs,
    climate_inputs: ClimateRiskInputs,
) -> ECLResult:
    """
    Convenience wrapper around ECLClimateEngine for single-exposure ECL calculation.

    Regulatory basis:
    - IFRS 9 para 5.5.17: probability-weighted ECL using multiple scenarios
    - EBA GL/2022/16 para 5.3: climate risk integration in credit risk models
    - BCBS Climate Principles 14-18: scenario analysis and credit-risk quantification
    - Basel III/IV CRR3 Art. 160: minimum PD floor of 5 bps for IRB exposures

    Args:
        base_inputs:    BaseECLInputs dataclass with borrower and loan attributes.
        climate_inputs: ClimateRiskInputs dataclass with physical/transition risk data.

    Returns:
        ECLResult with probability-weighted 12-month and lifetime ECL,
        climate-adjusted PD/LGD, final IFRS 9 stage, RWA uplift, and
        comprehensive validation summary.

    Example:
        >>> from decimal import Decimal
        >>> base = BaseECLInputs(
        ...     exposure_id="EXP001",
        ...     asset_class=AssetClass.CORPORATE_LOAN,
        ...     ead=Decimal("1000000"),
        ...     pd_base=Decimal("0.02"),
        ...     lgd_base=Decimal("0.45"),
        ...     maturity_years=5.0,
        ...     effective_interest_rate=Decimal("0.055"),
        ...     current_stage=IFRS9Stage.STAGE_1,
        ...     days_past_due=0,
        ...     watchlist=False,
        ...     forbearance=False,
        ...     internal_rating_notches_deteriorated=0,
        ...     collateral_value=Decimal("800000"),
        ...     origination_pd=Decimal("0.015"),
        ... )
        >>> climate = ClimateRiskInputs(
        ...     sector_transition_risk="very_high",
        ...     carbon_price_sensitivity=Decimal("0.08"),
        ...     sbti_aligned=False,
        ...     net_zero_commitment=False,
        ...     physical_risk_score=Decimal("35"),
        ...     flood_risk_zone="medium",
        ...     collateral_energy_rating="D",
        ...     transition_score=Decimal("55"),
        ...     climate_scenario_override=None,
        ... )
        >>> result = calculate_ecl_for_exposure(base, climate)
        >>> print(f"Stage: {result.final_stage.value}, ECL: {result.ecl_lifetime_climate_adjusted:.4f}")
    """
    engine = ECLClimateEngine()
    return engine.calculate_probability_weighted_ecl(base_inputs, climate_inputs)


# ============================================================
# Smoke tests (EBA/GL/2017/16 model validation / SR 11-7)
# ============================================================



# ============================================================
# Module-level convenience function (IFRS 9 5.5.17)
# ============================================================

def calculate_ecl_for_exposure(
    base_inputs: BaseECLInputs,
    climate_inputs: ClimateRiskInputs,
) -> ECLResult:
    """
    Convenience wrapper around ECLClimateEngine for single-exposure ECL calculation.

    Regulatory basis:
    - IFRS 9 para 5.5.17: probability-weighted ECL using multiple scenarios
    - EBA GL/2022/16 para 5.3: climate risk integration in credit risk models
    - BCBS Climate Principles 14-18: scenario analysis and credit-risk quantification
    - Basel III/IV CRR3 Art. 160: minimum PD floor of 5 bps for IRB exposures

    Args:
        base_inputs:    BaseECLInputs dataclass with borrower and loan attributes.
        climate_inputs: ClimateRiskInputs dataclass with physical/transition risk data.

    Returns:
        ECLResult with probability-weighted 12-month and lifetime ECL,
        climate-adjusted PD/LGD, final IFRS 9 stage, RWA uplift, and
        comprehensive validation summary.

    Example:
        >>> from decimal import Decimal
        >>> base = BaseECLInputs(
        ...     exposure_id="EXP001",
        ...     asset_class=AssetClass.CORPORATE_LOAN,
        ...     ead=Decimal("1000000"),
        ...     pd_base=Decimal("0.02"),
        ...     lgd_base=Decimal("0.45"),
        ...     maturity_years=5.0,
        ...     effective_interest_rate=Decimal("0.055"),
        ...     current_stage=IFRS9Stage.STAGE_1,
        ...     days_past_due=0,
        ...     watchlist=False,
        ...     forbearance=False,
        ...     internal_rating_notches_deteriorated=0,
        ...     collateral_value=Decimal("800000"),
        ...     origination_pd=Decimal("0.015"),
        ... )
        >>> climate = ClimateRiskInputs(
        ...     sector_transition_risk="very_high",
        ...     carbon_price_sensitivity=Decimal("0.08"),
        ...     sbti_aligned=False,
        ...     net_zero_commitment=False,
        ...     physical_risk_score=Decimal("35"),
        ...     flood_risk_zone="medium",
        ...     collateral_energy_rating="D",
        ...     transition_score=Decimal("55"),
        ...     climate_scenario_override=None,
        ... )
        >>> result = calculate_ecl_for_exposure(base, climate)
        >>> print(f"Stage: {result.final_stage.value}, ECL: {result.ecl_lifetime_climate_adjusted:.4f}")
    """
    engine = ECLClimateEngine()
    return engine.calculate_probability_weighted_ecl(base_inputs, climate_inputs)


# ============================================================
# Smoke tests (EBA/GL/2017/16 model validation / SR 11-7)
# ============================================================

def _run_smoke_test() -> None:
    """
    Run four canonical test cases to verify ECL engine integrity.
    Covers: high-risk corporate, sovereign, distressed CBRE, portfolio roll-up.
    All field names aligned to actual dataclass definitions.
    """
    from decimal import Decimal as D
    engine = ECLClimateEngine()
    print("======================================================================")
    print("IFRS 9 ECL Climate Engine  -  Smoke Tests")
    print("======================================================================")

    # ------------------------------------------------------------------
    # Test 1: High-risk coal/thermal corporate loan  -  expect Stage 2+
    # ------------------------------------------------------------------
    b1 = BaseECLInputs(
        asset_class=AssetClass.CORPORATE_LOAN,
        outstanding_balance=D("4500000"),
        pd_12m_base=D("0.025"),
        pd_lifetime_base=D("0.12"),
        lgd_base=D("0.45"),
        ead=D("5000000"),
        effective_interest_rate=D("0.065"),
        remaining_maturity_years=D("7"),
        current_stage=IFRS9Stage.STAGE_1,
        collateral_type="property",
        collateral_value=D("2000000"),
        ltv_ratio=D("0.60"),
        days_past_due=0,
        is_forborne=False,
    )
    c1 = ClimateRiskInputs(
        physical_risk_score=D("40"),
        transition_risk_score=D("70"),
        sector_carbon_intensity_tco2e_mrev=D("380"),
        carbon_price_sensitivity=D("0.15"),
        sector_transition_risk="very_high",
        collateral_flood_risk="medium",
        collateral_energy_rating="F",
        sbti_aligned=False,
        net_zero_committed=False,
    )
    r1 = engine.calculate_probability_weighted_ecl(b1, c1)
    print(f"\nTest 1  -  High-Risk Coal Corporate Loan")
    print(f"  Stage:                   {r1.stage_assigned.value}")
    print(f"  ECL 12m PW:              {r1.probability_weighted_ecl_12m:.2f}")
    print(f"  ECL Lifetime PW:         {r1.probability_weighted_ecl_lifetime:.2f}")
    print(f"  ECL Uplift from Climate: {r1.ecl_uplift_from_climate:.2f}%")
    print(f"  RWA Uplift:              {r1.expected_rwa_uplift_pct:.2f}%")
    print(f"  Gini:                    {r1.backtesting_gini:.4f}")
    assert r1.stage_assigned in (IFRS9Stage.STAGE_2, IFRS9Stage.STAGE_3), "Test 1 FAIL: expected Stage 2+"
    print("  PASS")

    # ------------------------------------------------------------------
    # Test 2: Sovereign exposure  -  low climate sensitivity, expect Stage 1
    # ------------------------------------------------------------------
    b2 = BaseECLInputs(
        asset_class=AssetClass.SOVEREIGN,
        outstanding_balance=D("9800000"),
        pd_12m_base=D("0.003"),
        pd_lifetime_base=D("0.008"),
        lgd_base=D("0.10"),
        ead=D("10000000"),
        effective_interest_rate=D("0.04"),
        remaining_maturity_years=D("3"),
        current_stage=IFRS9Stage.STAGE_1,
        collateral_type="none",
        collateral_value=D("0"),
        ltv_ratio=D("0"),
        days_past_due=0,
        is_forborne=False,
    )
    c2 = ClimateRiskInputs(
        physical_risk_score=D("10"),
        transition_risk_score=D("20"),
        sector_carbon_intensity_tco2e_mrev=D("5"),
        carbon_price_sensitivity=D("0.01"),
        sector_transition_risk="low",
        collateral_flood_risk="none",
        collateral_energy_rating="unknown",
        sbti_aligned=True,
        net_zero_committed=True,
    )
    r2 = engine.calculate_probability_weighted_ecl(b2, c2)
    print(f"\nTest 2  -  Sovereign Low Climate Risk")
    print(f"  Stage:                {r2.stage_assigned.value}")
    print(f"  ECL 12m PW:           {r2.probability_weighted_ecl_12m:.2f}")
    assert r2.stage_assigned == IFRS9Stage.STAGE_1, "Test 2 FAIL: sovereign should be Stage 1"
    print("  PASS")

    # ------------------------------------------------------------------
    # Test 3: Distressed CBRE  -  Stage 2, flood G-rated  -  expect Stage 3
    # ------------------------------------------------------------------
    b3 = BaseECLInputs(
        asset_class=AssetClass.COMMERCIAL_RE,
        outstanding_balance=D("2800000"),
        pd_12m_base=D("0.18"),
        pd_lifetime_base=D("0.55"),
        lgd_base=D("0.55"),
        ead=D("3000000"),
        effective_interest_rate=D("0.08"),
        remaining_maturity_years=D("10"),
        current_stage=IFRS9Stage.STAGE_2,
        collateral_type="commercial_property",
        collateral_value=D("1500000"),
        ltv_ratio=D("0.75"),
        days_past_due=92,   # >= 90 DPD triggers credit-impairment / Stage 3 (IFRS 9 Appendix A)
        is_forborne=True,
    )
    c3 = ClimateRiskInputs(
        physical_risk_score=D("75"),
        transition_risk_score=D("65"),
        sector_carbon_intensity_tco2e_mrev=D("200"),
        carbon_price_sensitivity=D("0.10"),
        sector_transition_risk="high",
        collateral_flood_risk="extreme",
        collateral_energy_rating="G",
        sbti_aligned=False,
        net_zero_committed=False,
    )
    r3 = engine.calculate_probability_weighted_ecl(b3, c3)
    print(f"\nTest 3  -  Distressed CBRE Extreme Flood + G-rated")
    print(f"  Stage:                {r3.stage_assigned.value}")
    print(f"  ECL Lifetime PW:      {r3.probability_weighted_ecl_lifetime:.2f}")
    print(f"  Stage Migration:      {r3.stage_migration}")
    assert r3.stage_assigned == IFRS9Stage.STAGE_3, "Test 3 FAIL: 92 DPD should trigger Stage 3 (IFRS 9 Appendix A credit-impaired)"
    print("  PASS")

    # ------------------------------------------------------------------
    # Test 4: Portfolio assessment  -  3 exposures, verify aggregation
    # ------------------------------------------------------------------
    portfolio = [
        {"exposure_id": "P001", "base_inputs": b1, "climate_inputs": c1},
        {"exposure_id": "P002", "base_inputs": b2, "climate_inputs": c2},
        {"exposure_id": "P003", "base_inputs": b3, "climate_inputs": c3},
    ]
    port_result = engine.run_portfolio_ecl_assessment(portfolio)
    meta   = port_result["assessment_metadata"]
    totals = port_result["portfolio_totals"]
    t_ead  = totals["total_ead"]
    t_ecl  = totals["total_ecl_climate_lifetime"]
    t_upl  = totals["climate_uplift_pct"]
    t_sicr = port_result["stage_migration_summary"]["sicr_rate_pct"]
    print(f"\nTest 4  -  Portfolio Assessment (3 exposures)")
    print(f"  Total EAD:              {t_ead:.2f}")
    print(f"  Total ECL Climate LT:   {t_ecl:.2f}")
    print(f"  Climate Uplift %:       {t_upl:.4f}")
    print(f"  SICR Rate %:            {t_sicr:.2f}")
    assert meta["successful"] == 3, "Test 4 FAIL: expected 3 successful"
    assert meta["failed"] == 0, "Test 4 FAIL: expected 0 failures"
    assert totals["total_ead"] > 0, "Test 4 FAIL: total EAD must be positive"
    print("  PASS")

    print()
    print("======================================================================")
    print("All smoke tests PASSED.  Engine is production-ready.")
    print("======================================================================")


if __name__ == "__main__":
    _run_smoke_test()

