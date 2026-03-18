"""
Climate Transition Risk Engine
=================================
Assesses financial risks from the shift to a low-carbon economy across
four TCFD categories: Policy/Legal, Technology, Market, Reputation.

Calculation Pipeline (6 configurable stages):
  Stage 1 -- Sector Classification: NACE -> CPRS -> IAM mapping (calls NACECPRSMapper)
  Stage 2 -- Carbon Pricing & CBAM Impact: Scope 1 x price + CBAM + Scope 2 x elec_uplift
  Stage 3 -- Stranded Asset Assessment: fossil reserves x (1 - utilization) x writedown
  Stage 4 -- Portfolio Alignment & Transition Readiness: alignment gap + readiness score
  Stage 5 -- NGFS Scenario Stress Testing: CVaR across 6 Phase 5 scenarios
  Stage 6 -- Composite Transition Risk Score: weighted sum of 4 TCFD categories

References:
  - EBA GL/2025/01 -- ESG Risk Management (effective Jan 2026)
  - NGFS Phase 5 Scenarios (6 scenarios)
  - TCFD Transition Risk Categories
  - IEA Net Zero 2050 Roadmap
  - Battiston et al. -- NACE-CPRS-IAM Mapping
  - EU CBAM Regulation 2023/956
"""
from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass, field as dc_field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedded Reference Data
# ---------------------------------------------------------------------------

NGFS_PHASE5_SCENARIOS: dict[str, dict] = {
    "Net Zero 2050": {
        "category": "orderly",
        "carbon_price_2030": 130,
        "carbon_price_2050": 250,
        "gdp_impact_pct": -1.5,
        "temp_2100_c": 1.5,
        "energy_price_multiplier": 1.25,
        "technology_change_rate": 0.08,
        "renewable_share_2050": 0.90,
        "fossil_demand_reduction_pct": 75,
        "description": (
            "Orderly transition reaching net-zero CO2 emissions by 2050 "
            "through immediate, stringent climate policies and innovation."
        ),
    },
    "Below 2C": {
        "category": "orderly",
        "carbon_price_2030": 90,
        "carbon_price_2050": 200,
        "gdp_impact_pct": -1.0,
        "temp_2100_c": 1.7,
        "energy_price_multiplier": 1.15,
        "technology_change_rate": 0.06,
        "renewable_share_2050": 0.80,
        "fossil_demand_reduction_pct": 60,
        "description": (
            "Orderly transition with gradual policy tightening that limits "
            "warming to below 2 degrees Celsius by end of century."
        ),
    },
    "Divergent Net Zero": {
        "category": "disorderly",
        "carbon_price_2030": 60,
        "carbon_price_2050": 350,
        "gdp_impact_pct": -2.5,
        "temp_2100_c": 1.5,
        "energy_price_multiplier": 1.40,
        "technology_change_rate": 0.10,
        "renewable_share_2050": 0.85,
        "fossil_demand_reduction_pct": 70,
        "description": (
            "Disorderly transition where net-zero is reached but with "
            "divergent policies across sectors causing higher costs."
        ),
    },
    "Delayed Transition": {
        "category": "disorderly",
        "carbon_price_2030": 30,
        "carbon_price_2050": 300,
        "gdp_impact_pct": -3.0,
        "temp_2100_c": 1.8,
        "energy_price_multiplier": 1.50,
        "technology_change_rate": 0.07,
        "renewable_share_2050": 0.70,
        "fossil_demand_reduction_pct": 55,
        "description": (
            "Disorderly transition where action is delayed until 2030 "
            "then sharp policy ramp-up leads to high economic disruption."
        ),
    },
    "NDCs": {
        "category": "hot_house",
        "carbon_price_2030": 25,
        "carbon_price_2050": 50,
        "gdp_impact_pct": -0.5,
        "temp_2100_c": 2.5,
        "energy_price_multiplier": 1.05,
        "technology_change_rate": 0.03,
        "renewable_share_2050": 0.50,
        "fossil_demand_reduction_pct": 25,
        "description": (
            "Hot-house world where only current NDC pledges are implemented, "
            "resulting in approximately 2.5 degrees Celsius warming."
        ),
    },
    "Current Policies": {
        "category": "hot_house",
        "carbon_price_2030": 15,
        "carbon_price_2050": 30,
        "gdp_impact_pct": 0.0,
        "temp_2100_c": 3.0,
        "energy_price_multiplier": 1.00,
        "technology_change_rate": 0.02,
        "renewable_share_2050": 0.35,
        "fossil_demand_reduction_pct": 10,
        "description": (
            "Hot-house world with no additional policy action beyond those "
            "already in place, leading to severe physical risk over time."
        ),
    },
}

IEA_NZE_PATHWAY: dict[str, dict[int, float]] = {
    # tCO2e per unit of output (normalised to 1.0 in base-year)
    "power": {2025: 0.40, 2030: 0.15, 2040: 0.02, 2050: 0.00},
    "cement": {2025: 0.85, 2030: 0.70, 2040: 0.35, 2050: 0.10},
    "steel": {2025: 0.80, 2030: 0.65, 2040: 0.30, 2050: 0.05},
    "transport": {2025: 0.75, 2030: 0.55, 2040: 0.25, 2050: 0.05},
    "chemicals": {2025: 0.82, 2030: 0.68, 2040: 0.38, 2050: 0.12},
    "aluminium": {2025: 0.78, 2030: 0.60, 2040: 0.28, 2050: 0.08},
    "buildings": {2025: 0.70, 2030: 0.50, 2040: 0.20, 2050: 0.02},
    "agriculture": {2025: 0.90, 2030: 0.80, 2040: 0.55, 2050: 0.30},
    "oil_and_gas": {2025: 0.92, 2030: 0.75, 2040: 0.40, 2050: 0.10},
    "aviation": {2025: 0.88, 2030: 0.72, 2040: 0.45, 2050: 0.15},
    "shipping": {2025: 0.85, 2030: 0.68, 2040: 0.35, 2050: 0.10},
    "pulp_and_paper": {2025: 0.78, 2030: 0.60, 2040: 0.30, 2050: 0.08},
}

TCFD_CATEGORY_DESCRIPTIONS: dict[str, dict] = {
    "policy_legal": {
        "description": (
            "Risks arising from policy actions that attempt to constrain "
            "activities contributing to climate change, or from litigation "
            "and legal liability related to climate impacts."
        ),
        "example_risks": [
            "Carbon pricing mechanisms (ETS, carbon taxes)",
            "Emissions caps and performance standards",
            "Climate-related litigation and liability",
            "Stricter building codes and energy-efficiency mandates",
            "CBAM and border adjustment measures",
        ],
    },
    "technology": {
        "description": (
            "Risks from technological innovations that support the "
            "transition to a low-carbon economy, potentially disrupting "
            "incumbent business models."
        ),
        "example_risks": [
            "Falling renewable energy costs displacing fossil generation",
            "Electric vehicle adoption reducing ICE demand",
            "Carbon capture and storage (CCS) cost trajectories",
            "Battery storage and green hydrogen breakthroughs",
            "Digital energy-management and smart-grid adoption",
        ],
    },
    "market": {
        "description": (
            "Risks from shifts in supply and demand for products and "
            "services as the economy transitions to lower-carbon alternatives."
        ),
        "example_risks": [
            "Consumer preference shifts toward sustainable products",
            "Commodity price volatility (fossil fuel vs. renewable inputs)",
            "Raw material supply-chain redesign for critical minerals",
            "Changing insurance cost and availability for high-carbon assets",
            "Investor reallocation away from carbon-intensive sectors",
        ],
    },
    "reputation": {
        "description": (
            "Risks arising from stakeholder perceptions of an organisation's "
            "contribution to or detraction from the transition to a low-carbon "
            "economy."
        ),
        "example_risks": [
            "Stigmatisation of high-carbon sectors",
            "Stakeholder concern over greenwashing claims",
            "Loss of social licence to operate",
            "ESG rating downgrades affecting cost of capital",
            "Activist campaigns and divestment movements",
        ],
    },
}

CBAM_COVERED_SECTORS: list[str] = [
    "cement",
    "steel",
    "aluminium",
    "fertilizers",
    "electricity",
    "hydrogen",
    "iron",
]

WRITEDOWN_CURVE_FUNCTIONS: list[str] = ["linear", "front_loaded", "s_curve", "step"]

# Mapping from CPRS dominant category to a default IEA_NZE sector key
_CPRS_TO_IEA_SECTOR: dict[str, str] = {
    "Fossil Fuel": "oil_and_gas",
    "Utility": "power",
    "Energy-Intensive": "cement",
    "Housing": "buildings",
    "Transport": "transport",
    "Agriculture": "agriculture",
    "Finance (indirect)": "buildings",
    "Other": "buildings",
}


# ---------------------------------------------------------------------------
# Config Dataclass
# ---------------------------------------------------------------------------


@dataclass
class TransitionRiskConfig:
    """Configuration for all six stages of the transition-risk pipeline."""

    # Stage 1: Sector classification
    cprs_risk_weight_overrides: dict[str, float] = dc_field(default_factory=dict)
    nace_override_weights: dict[str, float] = dc_field(default_factory=dict)
    multi_activity_method: str = "revenue_weighted"  # revenue_weighted / max / primary_only
    ghg_bucket_thresholds: list[float] = dc_field(
        default_factory=lambda: [20.0, 100.0, 500.0, 1000.0]
    )

    # Stage 2: Carbon pricing
    carbon_price_source: str = "ngfs"  # ngfs / iea / custom
    carbon_price_override_by_year: dict[int, float] = dc_field(default_factory=dict)
    cbam_sectors_enabled: list[str] = dc_field(
        default_factory=lambda: [
            "cement", "steel", "aluminium", "fertilizers", "electricity", "hydrogen",
        ]
    )
    cbam_rate_method: str = "net_of_home"  # full_eu_ets / net_of_home / custom
    pass_through_rate: float = 0.70  # 70 % absorbed by company
    scope3_inclusion: str = "scope_1_2"  # scope_1_only / scope_1_2 / scope_1_2_3

    # Stage 3: Stranded assets
    phase_out_pathway: str = "iea_nze"  # iea_nze / ngfs_orderly / custom
    stranded_asset_categories: list[str] = dc_field(
        default_factory=lambda: ["fossil_reserves", "coal_plants", "ice_vehicles"]
    )
    writedown_curve_type: str = "linear"  # linear / front_loaded / s_curve / step
    technology_substitution_speed: str = "moderate"  # slow / moderate / fast
    residual_value_floor_pct: float = 10.0  # 0-30 %

    # Stage 4: Alignment
    benchmark_pathway: str = "iea_nze_2050"  # iea_nze / paris_1_5 / paris_below_2 / ndc / custom
    readiness_indicators: list[str] = dc_field(
        default_factory=lambda: [
            "sbti_target", "green_capex_ratio", "governance_quality", "disclosed_pathway",
        ]
    )
    readiness_weights: dict[str, float] = dc_field(default_factory=dict)  # empty -> equal
    alignment_metric: str = "emission_intensity"  # absolute / intensity / temperature_score
    temperature_overshoot_penalty: float = 1.5  # multiplier for > 2 C aligned

    # Stage 5: NGFS scenarios
    scenario_selection: list[str] = dc_field(
        default_factory=lambda: [
            "Net Zero 2050",
            "Below 2C",
            "Divergent Net Zero",
            "Delayed Transition",
            "NDCs",
            "Current Policies",
        ]
    )
    transition_risk_category_weights: dict[str, float] = dc_field(
        default_factory=lambda: {
            "policy_legal": 0.35,
            "technology": 0.25,
            "market": 0.25,
            "reputation": 0.15,
        }
    )
    stress_severity_multiplier: float = 1.0
    pd_transition_sensitivity: float = 0.015
    lgd_transition_uplift: float = 0.03
    macro_feedback_loops: bool = True

    # Stage 6: Composite -- uses transition_risk_category_weights from Stage 5


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SectorClassificationResult:
    """Stage 1 output: NACE -> CPRS -> IAM sector classification."""

    entity_name: str
    primary_nace: str
    cprs_category: str
    cprs_risk_weight: float
    sector_risk_score: float
    ghg_bucket: str
    iam_sectors: list[str]


@dataclass
class CarbonPricingResult:
    """Stage 2 output: carbon cost breakdown under a given scenario/horizon."""

    scope1_cost: float
    scope2_cost: float
    scope3_cost: float
    cbam_cost: float
    total_carbon_cost: float
    carbon_cost_as_pct_revenue: float
    scenario: str
    time_horizon: int


@dataclass
class StrandedAssetResult:
    """Stage 3 output: stranded-asset writedown assessment."""

    fossil_reserve_value: float
    utilization_rate: float
    writedown_factor: float
    stranded_asset_risk: float
    residual_value: float
    years_to_full_writedown: int


@dataclass
class AlignmentResult:
    """Stage 4 output: portfolio alignment and transition readiness."""

    current_intensity: float  # tCO2e per EUR M revenue
    pathway_target: float
    alignment_gap: float  # positive = above target (bad)
    alignment_pct: float  # % gap relative to target
    transition_readiness_score: float  # 0-100
    readiness_breakdown: dict[str, float]  # per-indicator scores
    implied_temperature: float  # degrees Celsius


@dataclass
class ScenarioStressResult:
    """Stage 5 output: single-scenario stress-test result."""

    scenario: str
    scenario_category: str  # orderly / disorderly / hot_house
    time_horizon: int
    carbon_cost: float
    stranded_risk: float
    tech_disruption_cost: float
    market_shift_impact: float
    transition_cvar: float
    pd_adjustment: float
    lgd_adjustment: float


@dataclass
class TransitionRiskResult:
    """Full six-stage transition risk assessment for one entity."""

    entity_id: str
    entity_name: str

    # Stage outputs
    sector_classification: SectorClassificationResult
    carbon_pricing: dict[str, CarbonPricingResult]  # keyed "scenario|horizon"
    stranded_assets: StrandedAssetResult
    alignment: AlignmentResult
    scenario_stress: list[ScenarioStressResult]

    # Composite
    composite_transition_score: float  # 0-100
    category_scores: dict[str, float]  # policy_legal, technology, market, reputation
    transition_risk_rating: str  # Very Low / Low / Medium / High / Very High

    # Financial impact (worst-case scenario)
    max_transition_cvar: float
    max_pd_adjustment: float
    max_lgd_adjustment: float

    # Top risk drivers
    top_risk_categories: list[tuple[str, float]]

    # Metadata
    config_snapshot: dict


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class TransitionRiskEngine:
    """Assess transition risk across six configurable stages.

    Instantiate with an optional :class:`TransitionRiskConfig`.  An external
    :class:`NACECPRSMapper` can be injected for testing; otherwise one is
    created internally.
    """

    # Substitution-speed -> total writedown years
    _SPEED_TO_YEARS: dict[str, int] = {
        "slow": 30,
        "moderate": 20,
        "fast": 10,
    }

    # Electricity-price uplift factor used to convert scope-2 emissions into a
    # cost proxy (pass-through of carbon cost in electricity pricing).
    _ELEC_PRICE_UPLIFT: float = 0.50

    def __init__(
        self,
        config: TransitionRiskConfig | None = None,
        nace_mapper: object | None = None,
    ) -> None:
        self.config = config or TransitionRiskConfig()

        # Lazy import to avoid circular dependencies at module level.
        from services.nace_cprs_mapper import NACECPRSMapper

        self.nace_mapper: NACECPRSMapper = nace_mapper or NACECPRSMapper(
            cprs_risk_weight_overrides=self.config.cprs_risk_weight_overrides,
            nace_overrides=self.config.nace_override_weights,
        )

        self._validate_config()
        logger.info(
            "TransitionRiskEngine initialised — %d scenarios, writedown=%s/%s",
            len(self.config.scenario_selection),
            self.config.writedown_curve_type,
            self.config.technology_substitution_speed,
        )

    # ------------------------------------------------------------------
    # Config validation
    # ------------------------------------------------------------------

    def _validate_config(self) -> None:
        """Validate configuration parameters are within acceptable ranges."""
        cfg = self.config

        # Category weights must sum to ~1.0
        weight_sum = sum(cfg.transition_risk_category_weights.values())
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(
                f"transition_risk_category_weights must sum to 1.0 (got {weight_sum:.4f})"
            )

        if cfg.pass_through_rate < 0.0 or cfg.pass_through_rate > 1.0:
            raise ValueError("pass_through_rate must be in [0.0, 1.0]")

        if cfg.residual_value_floor_pct < 0.0 or cfg.residual_value_floor_pct > 30.0:
            raise ValueError("residual_value_floor_pct must be in [0, 30]")

        if cfg.writedown_curve_type not in WRITEDOWN_CURVE_FUNCTIONS:
            raise ValueError(
                f"writedown_curve_type must be one of {WRITEDOWN_CURVE_FUNCTIONS}"
            )

        if cfg.technology_substitution_speed not in self._SPEED_TO_YEARS:
            raise ValueError(
                "technology_substitution_speed must be one of: slow, moderate, fast"
            )

        if cfg.stress_severity_multiplier < 0.0:
            raise ValueError("stress_severity_multiplier must be non-negative")

        for name in cfg.scenario_selection:
            if name not in NGFS_PHASE5_SCENARIOS:
                raise ValueError(f"Unknown NGFS scenario: {name!r}")

        logger.debug("Config validation passed")

    # ------------------------------------------------------------------
    # Stage 1 -- Sector Classification
    # ------------------------------------------------------------------

    def classify_sector(
        self,
        entity_name: str,
        nace_codes_with_revenue: list[dict],
    ) -> SectorClassificationResult:
        """Map NACE activities to CPRS category, IAM sectors, and GHG bucket.

        Parameters
        ----------
        entity_name:
            Legal name of the entity.
        nace_codes_with_revenue:
            List of dicts, each with ``nace_code`` (str), ``revenue_share``
            (float 0-1), and optionally ``ghg_intensity_tco2e_per_eur_m``.
        """
        if not nace_codes_with_revenue:
            raise ValueError("nace_codes_with_revenue must not be empty")

        method = self.config.multi_activity_method

        # Use the mapper for the heavy lifting
        cp_score = self.nace_mapper.score_counterparty(
            entity_name=entity_name,
            activities=nace_codes_with_revenue,
        )

        if method == "max":
            sector_risk_score = max(
                c.cprs_risk_weight for c in cp_score.classifications
            )
        elif method == "primary_only":
            sector_risk_score = cp_score.classifications[0].cprs_risk_weight
        else:
            # revenue_weighted (default) -- already computed by mapper
            sector_risk_score = cp_score.sector_risk_score

        # Collect IAM sectors from dominant CPRS
        from services.nace_cprs_mapper import CPRS_TO_IAM

        iam_sectors = CPRS_TO_IAM.get(cp_score.dominant_cprs_category, ["Services"])

        result = SectorClassificationResult(
            entity_name=entity_name,
            primary_nace=cp_score.primary_nace,
            cprs_category=cp_score.dominant_cprs_category,
            cprs_risk_weight=next(
                (
                    c.cprs_risk_weight
                    for c in cp_score.classifications
                    if c.cprs_category == cp_score.dominant_cprs_category
                ),
                0.0,
            ),
            sector_risk_score=round(sector_risk_score, 4),
            ghg_bucket=cp_score.ghg_bucket,
            iam_sectors=iam_sectors,
        )

        logger.info(
            "Stage 1 — %s: CPRS=%s, risk_score=%.4f, GHG=%s",
            entity_name,
            result.cprs_category,
            result.sector_risk_score,
            result.ghg_bucket,
        )
        return result

    # ------------------------------------------------------------------
    # Stage 2 -- Carbon Pricing & CBAM Impact
    # ------------------------------------------------------------------

    def assess_carbon_pricing(
        self,
        scope1_tco2e: float,
        scope2_tco2e: float,
        scope3_tco2e: float,
        revenue_eur: float,
        is_cbam_sector: bool,
        home_carbon_price: float = 0.0,
        scenario: str | None = None,
        time_horizon: int | None = None,
    ) -> CarbonPricingResult:
        """Compute carbon cost under a specific scenario and time horizon.

        Parameters
        ----------
        scope1_tco2e, scope2_tco2e, scope3_tco2e:
            Annual emissions in tCO2e for each scope.
        revenue_eur:
            Annual revenue (EUR).
        is_cbam_sector:
            Whether the entity's products fall under EU CBAM.
        home_carbon_price:
            Effective carbon price already paid in the entity's home
            jurisdiction (EUR / tCO2e).  Used when cbam_rate_method is
            ``net_of_home``.
        scenario:
            NGFS scenario name.  Defaults to first in ``scenario_selection``.
        time_horizon:
            Target year for carbon-price interpolation.  Defaults to 2030.
        """
        cfg = self.config
        scenario = scenario or cfg.scenario_selection[0]
        time_horizon = time_horizon or 2030

        carbon_price = self._get_carbon_price(scenario, time_horizon)

        # Scope 1 cost
        scope1_cost = scope1_tco2e * carbon_price * cfg.pass_through_rate

        # Scope 2 cost (electricity-price uplift)
        scope2_cost = scope2_tco2e * carbon_price * self._ELEC_PRICE_UPLIFT

        # Scope 3 cost
        if cfg.scope3_inclusion == "scope_1_2_3":
            scope3_cost = scope3_tco2e * carbon_price * cfg.pass_through_rate * 0.30
        elif cfg.scope3_inclusion == "scope_1_only":
            scope3_cost = 0.0
        else:
            # scope_1_2 (default) -- no scope 3
            scope3_cost = 0.0

        # CBAM cost
        cbam_cost = 0.0
        if is_cbam_sector and cfg.cbam_sectors_enabled:
            if cfg.cbam_rate_method == "full_eu_ets":
                cbam_unit_price = carbon_price
            elif cfg.cbam_rate_method == "net_of_home":
                cbam_unit_price = max(0.0, carbon_price - home_carbon_price)
            else:
                # custom -- fall back to full price
                cbam_unit_price = carbon_price

            cbam_cost = scope1_tco2e * cbam_unit_price * 0.20  # 20 % CBAM-exposed share

        total = scope1_cost + scope2_cost + scope3_cost + cbam_cost
        pct_revenue = (total / revenue_eur * 100.0) if revenue_eur > 0 else 0.0

        result = CarbonPricingResult(
            scope1_cost=round(scope1_cost, 2),
            scope2_cost=round(scope2_cost, 2),
            scope3_cost=round(scope3_cost, 2),
            cbam_cost=round(cbam_cost, 2),
            total_carbon_cost=round(total, 2),
            carbon_cost_as_pct_revenue=round(pct_revenue, 4),
            scenario=scenario,
            time_horizon=time_horizon,
        )

        logger.info(
            "Stage 2 — scenario=%s, horizon=%d: total_carbon_cost=EUR %.0f (%.2f%% rev)",
            scenario,
            time_horizon,
            total,
            pct_revenue,
        )
        return result

    def _get_carbon_price(self, scenario: str, year: int) -> float:
        """Return the carbon price (EUR / tCO2e) for a scenario and year.

        Linearly interpolates between the scenario's 2030 and 2050 prices for
        intermediate years.  Years before 2030 are extrapolated from a base of
        EUR 10 (current approximate average).  Custom overrides take precedence.
        """
        cfg = self.config

        # Check custom overrides first
        if cfg.carbon_price_override_by_year and year in cfg.carbon_price_override_by_year:
            return cfg.carbon_price_override_by_year[year]

        sc = NGFS_PHASE5_SCENARIOS.get(scenario)
        if sc is None:
            logger.warning("Unknown scenario %r — using default carbon price 50", scenario)
            return 50.0

        p2030 = sc["carbon_price_2030"]
        p2050 = sc["carbon_price_2050"]

        if year <= 2025:
            # Extrapolate backwards from 2030 to a EUR-10 base at 2025
            base_2025 = 10.0
            return base_2025
        if year <= 2030:
            # Linear interpolation 2025-2030
            base_2025 = 10.0
            frac = (year - 2025) / 5.0
            return base_2025 + frac * (p2030 - base_2025)
        if year >= 2050:
            return float(p2050)

        # Linear interpolation 2030-2050
        frac = (year - 2030) / 20.0
        return p2030 + frac * (p2050 - p2030)

    # ------------------------------------------------------------------
    # Stage 3 -- Stranded Asset Assessment
    # ------------------------------------------------------------------

    def assess_stranded_assets(
        self,
        fossil_reserve_value: float,
        asset_categories: list[str],
        scenario: str | None = None,
        time_horizon: int | None = None,
    ) -> StrandedAssetResult:
        """Compute stranded-asset writedown risk.

        Parameters
        ----------
        fossil_reserve_value:
            Book value of fossil-fuel reserves or high-carbon assets (EUR).
        asset_categories:
            List of asset categories, e.g. ``["fossil_reserves", "coal_plants"]``.
        scenario:
            NGFS scenario name.  Defaults to first in ``scenario_selection``.
        time_horizon:
            Target year.  Defaults to 2040.
        """
        cfg = self.config
        scenario = scenario or cfg.scenario_selection[0]
        time_horizon = time_horizon or 2040

        if fossil_reserve_value <= 0 or not asset_categories:
            return StrandedAssetResult(
                fossil_reserve_value=fossil_reserve_value,
                utilization_rate=1.0,
                writedown_factor=0.0,
                stranded_asset_risk=0.0,
                residual_value=fossil_reserve_value,
                years_to_full_writedown=0,
            )

        sc = NGFS_PHASE5_SCENARIOS.get(scenario, NGFS_PHASE5_SCENARIOS["Net Zero 2050"])
        fossil_demand_reduction = sc["fossil_demand_reduction_pct"] / 100.0

        # Utilization rate falls as demand for fossil fuels drops
        utilization_rate = max(0.0, 1.0 - fossil_demand_reduction)

        # Total writedown period
        total_years = self._SPEED_TO_YEARS[cfg.technology_substitution_speed]
        years_elapsed = max(0, time_horizon - 2025)

        # Base writedown factor
        base_factor = fossil_demand_reduction
        writedown_factor = self._apply_writedown_curve(
            base_factor, years_elapsed, total_years
        )

        # Apply residual value floor
        floor = cfg.residual_value_floor_pct / 100.0
        writedown_factor = min(writedown_factor, 1.0 - floor)

        stranded_asset_risk = fossil_reserve_value * writedown_factor
        residual_value = fossil_reserve_value * (1.0 - writedown_factor)

        # Years to full writedown (up to the floor)
        if writedown_factor > 0:
            years_to_full = int(
                total_years * ((1.0 - floor) / base_factor)
            ) if base_factor > 0 else total_years
        else:
            years_to_full = 0

        result = StrandedAssetResult(
            fossil_reserve_value=round(fossil_reserve_value, 2),
            utilization_rate=round(utilization_rate, 4),
            writedown_factor=round(writedown_factor, 4),
            stranded_asset_risk=round(stranded_asset_risk, 2),
            residual_value=round(residual_value, 2),
            years_to_full_writedown=years_to_full,
        )

        logger.info(
            "Stage 3 — scenario=%s, horizon=%d: writedown=%.2f%%, risk=EUR %.0f",
            scenario,
            time_horizon,
            writedown_factor * 100,
            stranded_asset_risk,
        )
        return result

    def _apply_writedown_curve(
        self, base_factor: float, years_elapsed: int, total_years: int,
    ) -> float:
        """Dispatch to the configured writedown-curve function.

        Returns a value in [0, 1] representing the fraction of the asset that
        has been written down at ``years_elapsed`` into the transition.
        """
        if total_years <= 0 or years_elapsed <= 0:
            return 0.0

        t = min(years_elapsed / total_years, 1.0)
        curve = self.config.writedown_curve_type

        if curve == "linear":
            return base_factor * t

        if curve == "front_loaded":
            # Quadratic front-loading: faster writedown early
            return base_factor * (1.0 - (1.0 - t) ** 2)

        if curve == "s_curve":
            # Logistic sigmoid centred at the midpoint
            midpoint = 0.5
            steepness = 10.0  # controls sharpness of the S
            sigmoid = 1.0 / (1.0 + math.exp(-steepness * (t - midpoint)))
            # Normalise so sigmoid(0)->~0 and sigmoid(1)->~1
            sig_0 = 1.0 / (1.0 + math.exp(-steepness * (0.0 - midpoint)))
            sig_1 = 1.0 / (1.0 + math.exp(-steepness * (1.0 - midpoint)))
            normalised = (sigmoid - sig_0) / (sig_1 - sig_0) if sig_1 != sig_0 else t
            return base_factor * normalised

        if curve == "step":
            # Step function: 30 % writedown up to 60 % of the period, then jump
            if t > 0.6:
                return base_factor
            return base_factor * 0.3

        # Fallback
        return base_factor * t

    # ------------------------------------------------------------------
    # Stage 4 -- Portfolio Alignment & Transition Readiness
    # ------------------------------------------------------------------

    def assess_alignment(
        self,
        sector: str,
        current_emission_intensity: float,
        revenue_eur: float,
        readiness_data: dict | None = None,
    ) -> AlignmentResult:
        """Compute alignment gap and transition-readiness score.

        Parameters
        ----------
        sector:
            IEA NZE sector key (e.g. ``"power"``, ``"cement"``).  If not found
            in ``IEA_NZE_PATHWAY`` the closest match is attempted via the
            CPRS->IEA mapping.
        current_emission_intensity:
            tCO2e per EUR M revenue for the entity today.
        revenue_eur:
            Annual revenue (EUR).
        readiness_data:
            Dict mapping indicator names to scores (0-100), e.g.
            ``{"sbti_target": 80, "green_capex_ratio": 40, ...}``.
        """
        readiness_data = readiness_data or {}

        # Resolve sector to IEA pathway
        pathway = IEA_NZE_PATHWAY.get(sector)
        if pathway is None:
            # Try CPRS->IEA fallback
            iea_key = _CPRS_TO_IEA_SECTOR.get(sector, "buildings")
            pathway = IEA_NZE_PATHWAY.get(iea_key, IEA_NZE_PATHWAY["buildings"])
            logger.debug("Sector %r not in IEA NZE pathway — falling back to %s", sector, iea_key)

        # Get the target for the current year via linear interpolation
        pathway_target = self._interpolate_pathway(pathway, 2026)

        # Alignment gap: positive means entity is above (worse than) target
        alignment_gap = current_emission_intensity - pathway_target
        alignment_pct = (
            (alignment_gap / pathway_target * 100.0) if pathway_target > 0 else 0.0
        )

        # Transition readiness score (0-100)
        readiness_breakdown = self._compute_readiness(readiness_data)
        readiness_values = list(readiness_breakdown.values())
        transition_readiness = (
            sum(readiness_values) / len(readiness_values) if readiness_values else 0.0
        )

        # Implied temperature: 1.5 + (gap / target) x 1.5, capped at 4.0
        if pathway_target > 0:
            implied_temp = 1.5 + (max(0.0, alignment_gap) / pathway_target) * 1.5
        else:
            implied_temp = 1.5
        implied_temp = min(implied_temp, 4.0)

        # Apply temperature overshoot penalty if > 2C
        if implied_temp > 2.0:
            overshoot_mult = self.config.temperature_overshoot_penalty
            alignment_gap *= overshoot_mult
            alignment_pct *= overshoot_mult

        result = AlignmentResult(
            current_intensity=round(current_emission_intensity, 4),
            pathway_target=round(pathway_target, 4),
            alignment_gap=round(alignment_gap, 4),
            alignment_pct=round(alignment_pct, 2),
            transition_readiness_score=round(transition_readiness, 2),
            readiness_breakdown=readiness_breakdown,
            implied_temperature=round(implied_temp, 2),
        )

        logger.info(
            "Stage 4 — sector=%s: gap=%.4f (%.1f%%), readiness=%.1f, implied_T=%.2f C",
            sector,
            result.alignment_gap,
            result.alignment_pct,
            result.transition_readiness_score,
            result.implied_temperature,
        )
        return result

    def _interpolate_pathway(self, pathway: dict[int, float], year: int) -> float:
        """Linearly interpolate pathway targets between milestone years."""
        years = sorted(pathway.keys())
        if year <= years[0]:
            return pathway[years[0]]
        if year >= years[-1]:
            return pathway[years[-1]]

        for i in range(len(years) - 1):
            y0, y1 = years[i], years[i + 1]
            if y0 <= year <= y1:
                frac = (year - y0) / (y1 - y0)
                return pathway[y0] + frac * (pathway[y1] - pathway[y0])

        return pathway[years[-1]]

    def _compute_readiness(self, readiness_data: dict) -> dict[str, float]:
        """Compute weighted readiness scores for each indicator.

        Returns a dict of indicator -> weighted score.  If explicit weights
        are not configured, equal weighting is applied.
        """
        cfg = self.config
        indicators = cfg.readiness_indicators
        weights = cfg.readiness_weights

        if not weights:
            # Equal weighting
            n = len(indicators)
            weights = {ind: 1.0 / n for ind in indicators} if n > 0 else {}

        breakdown: dict[str, float] = {}
        for ind in indicators:
            raw_score = float(readiness_data.get(ind, 0.0))
            raw_score = max(0.0, min(100.0, raw_score))
            weight = weights.get(ind, 1.0 / len(indicators) if indicators else 1.0)
            breakdown[ind] = round(raw_score * weight * len(indicators), 2)

        return breakdown

    # ------------------------------------------------------------------
    # Stage 5 -- NGFS Scenario Stress Testing
    # ------------------------------------------------------------------

    def stress_test_scenarios(
        self,
        carbon_cost_base: float,
        stranded_risk_base: float,
        sector_risk_score: float,
        revenue_eur: float,
        fossil_exposure_pct: float = 0.0,
    ) -> list[ScenarioStressResult]:
        """Run transition-risk stress tests across selected NGFS scenarios.

        Parameters
        ----------
        carbon_cost_base:
            Carbon cost from Stage 2 for the default scenario (EUR).
        stranded_risk_base:
            Stranded-asset risk from Stage 3 (EUR).
        sector_risk_score:
            CPRS sector risk score from Stage 1 (0-1).
        revenue_eur:
            Annual revenue (EUR).
        fossil_exposure_pct:
            Percentage of revenue / assets exposed to fossil fuels (0-100).
        """
        cfg = self.config
        default_scenario_name = cfg.scenario_selection[0]
        default_sc = NGFS_PHASE5_SCENARIOS[default_scenario_name]
        default_cp_2030 = default_sc["carbon_price_2030"]

        results: list[ScenarioStressResult] = []

        for name in cfg.scenario_selection:
            sc = NGFS_PHASE5_SCENARIOS[name]

            # Carbon-price ratio relative to the default scenario at 2030
            price_ratio = (
                sc["carbon_price_2030"] / default_cp_2030 if default_cp_2030 > 0 else 1.0
            )
            carbon_cost = carbon_cost_base * price_ratio * cfg.stress_severity_multiplier

            # Stranded-asset risk scaled by fossil demand reduction
            fossil_reduction = sc["fossil_demand_reduction_pct"] / 100.0
            stranded_risk = stranded_risk_base * fossil_reduction * cfg.stress_severity_multiplier

            # Technology disruption cost
            tech_rate = sc["technology_change_rate"]
            tech_disruption = (
                revenue_eur
                * sector_risk_score
                * tech_rate
                * cfg.stress_severity_multiplier
            )

            # Market shift impact
            renewable_share = sc["renewable_share_2050"]
            market_shift = (
                revenue_eur
                * (1.0 - renewable_share)
                * sector_risk_score
                * 0.1
                * cfg.stress_severity_multiplier
            )

            # Transition CVaR (total conditional value-at-risk)
            transition_cvar = carbon_cost + stranded_risk + tech_disruption + market_shift

            # Macro feedback loops
            if cfg.macro_feedback_loops:
                gdp_mult = 1.0 + abs(sc["gdp_impact_pct"]) / 100.0
                transition_cvar *= gdp_mult
                carbon_cost *= gdp_mult
                stranded_risk *= gdp_mult
                tech_disruption *= gdp_mult
                market_shift *= gdp_mult

            # PD and LGD adjustments
            cvar_rev_ratio = transition_cvar / revenue_eur if revenue_eur > 0 else 0.0
            pd_adj = cvar_rev_ratio * cfg.pd_transition_sensitivity
            lgd_adj = cvar_rev_ratio * cfg.lgd_transition_uplift

            results.append(
                ScenarioStressResult(
                    scenario=name,
                    scenario_category=sc["category"],
                    time_horizon=2030,
                    carbon_cost=round(carbon_cost, 2),
                    stranded_risk=round(stranded_risk, 2),
                    tech_disruption_cost=round(tech_disruption, 2),
                    market_shift_impact=round(market_shift, 2),
                    transition_cvar=round(transition_cvar, 2),
                    pd_adjustment=round(pd_adj, 6),
                    lgd_adjustment=round(lgd_adj, 6),
                )
            )

            logger.debug(
                "Stage 5 — %s (%s): CVaR=EUR %.0f, PD_adj=%.4f%%, LGD_adj=%.4f%%",
                name,
                sc["category"],
                transition_cvar,
                pd_adj * 100,
                lgd_adj * 100,
            )

        logger.info(
            "Stage 5 — stress-tested %d scenarios, max CVaR=EUR %.0f",
            len(results),
            max(r.transition_cvar for r in results) if results else 0,
        )
        return results

    # ------------------------------------------------------------------
    # Stage 6 -- Composite Transition Risk Score
    # ------------------------------------------------------------------

    def compute_composite_score(
        self,
        sector_score: float,
        carbon_pricing_results: dict[str, CarbonPricingResult],
        stranded_result: StrandedAssetResult,
        alignment_result: AlignmentResult,
        scenario_results: list[ScenarioStressResult],
    ) -> tuple[float, dict[str, float]]:
        """Compute the weighted composite transition-risk score.

        Returns
        -------
        tuple[float, dict[str, float]]
            ``(composite_score_0_100, {category: score_0_100})``.
        """
        cfg = self.config
        weights = cfg.transition_risk_category_weights

        # ---------- policy_legal ----------
        # Driven by carbon cost as % of revenue and CBAM exposure
        avg_carbon_pct = 0.0
        if carbon_pricing_results:
            avg_carbon_pct = sum(
                r.carbon_cost_as_pct_revenue for r in carbon_pricing_results.values()
            ) / len(carbon_pricing_results)

        # Normalise: 0 % -> 0, 10 % -> 100
        policy_raw = min(avg_carbon_pct / 10.0, 1.0) * 100.0

        # ---------- technology ----------
        # Driven by stranded-asset writedown factor and substitution speed
        writedown_score = stranded_result.writedown_factor * 100.0
        speed_mult = {"slow": 0.7, "moderate": 1.0, "fast": 1.3}.get(
            cfg.technology_substitution_speed, 1.0
        )
        tech_raw = min(writedown_score * speed_mult, 100.0)

        # ---------- market ----------
        # Driven by alignment gap and sector risk score
        gap_normalised = min(abs(alignment_result.alignment_pct) / 200.0, 1.0) * 100.0
        sector_component = sector_score * 100.0
        market_raw = min((gap_normalised * 0.6 + sector_component * 0.4), 100.0)

        # ---------- reputation ----------
        # Driven by transition readiness (inverse) and disclosure quality
        readiness_inv = max(0.0, 100.0 - alignment_result.transition_readiness_score)
        reputation_raw = min(readiness_inv, 100.0)

        category_scores = {
            "policy_legal": round(policy_raw, 2),
            "technology": round(tech_raw, 2),
            "market": round(market_raw, 2),
            "reputation": round(reputation_raw, 2),
        }

        composite = sum(
            weights.get(cat, 0.0) * score
            for cat, score in category_scores.items()
        )
        composite = round(max(0.0, min(100.0, composite)), 2)

        logger.info(
            "Stage 6 — composite=%.2f  [P/L=%.1f, T=%.1f, M=%.1f, R=%.1f]",
            composite,
            policy_raw,
            tech_raw,
            market_raw,
            reputation_raw,
        )
        return composite, category_scores

    # ------------------------------------------------------------------
    # Full Entity Assessment (orchestrator)
    # ------------------------------------------------------------------

    def assess_entity(
        self,
        entity_id: str,
        entity_name: str,
        nace_codes_with_revenue: list[dict],
        scope1_tco2e: float,
        scope2_tco2e: float,
        scope3_tco2e: float = 0.0,
        revenue_eur: float = 1e9,
        fossil_reserve_value: float = 0.0,
        current_emission_intensity: float = 0.0,
        readiness_data: dict | None = None,
        is_cbam_sector: bool = False,
        home_carbon_price: float = 0.0,
        fossil_exposure_pct: float = 0.0,
    ) -> TransitionRiskResult:
        """Run all six stages for one entity and return a unified result.

        Parameters
        ----------
        entity_id:
            Unique identifier.
        entity_name:
            Legal name.
        nace_codes_with_revenue:
            NACE codes with revenue shares (see :meth:`classify_sector`).
        scope1_tco2e, scope2_tco2e, scope3_tco2e:
            Annual emissions by scope (tCO2e).
        revenue_eur:
            Annual revenue (EUR).
        fossil_reserve_value:
            Book value of fossil / high-carbon assets (EUR).
        current_emission_intensity:
            tCO2e per EUR M revenue.
        readiness_data:
            Transition-readiness indicators dict (see :meth:`assess_alignment`).
        is_cbam_sector:
            Whether entity is CBAM-affected.
        home_carbon_price:
            Carbon price already paid domestically (EUR / tCO2e).
        fossil_exposure_pct:
            Percentage of revenue exposed to fossil fuels.
        """
        logger.info("=== Transition-risk assessment: %s (%s) ===", entity_name, entity_id)

        # Stage 1 -- Sector Classification
        sector_cls = self.classify_sector(entity_name, nace_codes_with_revenue)

        # Stage 2 -- Carbon Pricing (per scenario x time horizon)
        carbon_pricing: dict[str, CarbonPricingResult] = {}
        horizons = [2030, 2040, 2050]
        for scen_name in self.config.scenario_selection:
            for hz in horizons:
                key = f"{scen_name}|{hz}"
                carbon_pricing[key] = self.assess_carbon_pricing(
                    scope1_tco2e=scope1_tco2e,
                    scope2_tco2e=scope2_tco2e,
                    scope3_tco2e=scope3_tco2e,
                    revenue_eur=revenue_eur,
                    is_cbam_sector=is_cbam_sector,
                    home_carbon_price=home_carbon_price,
                    scenario=scen_name,
                    time_horizon=hz,
                )

        # Stage 3 -- Stranded Assets
        stranded = self.assess_stranded_assets(
            fossil_reserve_value=fossil_reserve_value,
            asset_categories=self.config.stranded_asset_categories,
        )

        # Stage 4 -- Alignment
        iea_sector = _CPRS_TO_IEA_SECTOR.get(sector_cls.cprs_category, "buildings")
        alignment = self.assess_alignment(
            sector=iea_sector,
            current_emission_intensity=current_emission_intensity,
            revenue_eur=revenue_eur,
            readiness_data=readiness_data,
        )

        # Stage 5 -- Scenario Stress
        # Use the default 2030-scenario carbon cost as the base
        default_key = f"{self.config.scenario_selection[0]}|2030"
        base_carbon_cost = (
            carbon_pricing[default_key].total_carbon_cost
            if default_key in carbon_pricing
            else 0.0
        )
        scenario_stress = self.stress_test_scenarios(
            carbon_cost_base=base_carbon_cost,
            stranded_risk_base=stranded.stranded_asset_risk,
            sector_risk_score=sector_cls.sector_risk_score,
            revenue_eur=revenue_eur,
            fossil_exposure_pct=fossil_exposure_pct,
        )

        # Stage 6 -- Composite Score
        composite, category_scores = self.compute_composite_score(
            sector_score=sector_cls.sector_risk_score,
            carbon_pricing_results=carbon_pricing,
            stranded_result=stranded,
            alignment_result=alignment,
            scenario_results=scenario_stress,
        )

        # Worst-case scenario metrics
        max_cvar = max((r.transition_cvar for r in scenario_stress), default=0.0)
        max_pd = max((r.pd_adjustment for r in scenario_stress), default=0.0)
        max_lgd = max((r.lgd_adjustment for r in scenario_stress), default=0.0)

        # Top risk categories (sorted descending)
        top_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

        rating = self.score_to_rating(composite)

        result = TransitionRiskResult(
            entity_id=entity_id,
            entity_name=entity_name,
            sector_classification=sector_cls,
            carbon_pricing=carbon_pricing,
            stranded_assets=stranded,
            alignment=alignment,
            scenario_stress=scenario_stress,
            composite_transition_score=composite,
            category_scores=category_scores,
            transition_risk_rating=rating,
            max_transition_cvar=round(max_cvar, 2),
            max_pd_adjustment=round(max_pd, 6),
            max_lgd_adjustment=round(max_lgd, 6),
            top_risk_categories=top_cats,
            config_snapshot=asdict(self.config),
        )

        logger.info(
            "=== Result: %s — composite=%.2f (%s), max_CVaR=EUR %.0f ===",
            entity_name,
            composite,
            rating,
            max_cvar,
        )
        return result

    # ------------------------------------------------------------------
    # Portfolio Assessment
    # ------------------------------------------------------------------

    def assess_portfolio(self, entities: list[dict]) -> list[TransitionRiskResult]:
        """Assess transition risk for every entity in a portfolio.

        Parameters
        ----------
        entities:
            List of dicts, each containing the keyword arguments accepted by
            :meth:`assess_entity`.

        Returns
        -------
        list[TransitionRiskResult]
        """
        results: list[TransitionRiskResult] = []
        for i, entity in enumerate(entities):
            logger.info(
                "Portfolio assessment %d/%d: %s",
                i + 1,
                len(entities),
                entity.get("entity_name", "unknown"),
            )
            result = self.assess_entity(**entity)
            results.append(result)

        if results:
            avg_score = sum(r.composite_transition_score for r in results) / len(results)
            logger.info(
                "Portfolio complete — %d entities, avg composite=%.2f (%s)",
                len(results),
                avg_score,
                self.score_to_rating(avg_score),
            )
        return results

    # ------------------------------------------------------------------
    # Rating Helper
    # ------------------------------------------------------------------

    @staticmethod
    def score_to_rating(score: float) -> str:
        """Convert a 0-100 composite score to a human-readable rating.

        Thresholds:
          < 20  Very Low
          < 40  Low
          < 60  Medium
          < 80  High
          >= 80 Very High
        """
        if score < 20:
            return "Very Low"
        if score < 40:
            return "Low"
        if score < 60:
            return "Medium"
        if score < 80:
            return "High"
        return "Very High"
