"""
Climate Integrated Risk Calculator
======================================
Combines physical and transition risk scores into a single integrated
climate risk measure suitable for portfolio-level credit risk overlays,
ICAAP stress testing, and regulatory reporting (EBA GL/2025/01).

Integration Modes:
  - Additive:        S = (w_p * P + w_t * T + alpha * (P+T)/2) * amplifier
  - Multiplicative:  S = (w_p * P + w_t * T + alpha * P*T/100) * amplifier
  - Max:             S = (w_p * P + w_t * T + alpha * max(P,T)) * amplifier
  - Custom:          S = (w_p * P + w_t * T + alpha * sqrt(P*T)) * amplifier

Optional nature-risk amplifier lifts scores for sectors with high
ecosystem dependency (TNFD ENCORE-aligned sensitivity factors).

Scenario Weighting:
  - Equal:              simple mean across scenarios
  - Probability-weighted: NGFS Phase 5 scenario probabilities
  - Custom:             user-supplied weights

References:
  - EBA GL/2025/01 -- ESG Risk Management
  - NGFS Phase 5 Scenarios
  - TNFD LEAP / ENCORE Dependencies
  - MSCI Climate Value-at-Risk (combined methodology)
  - BIS Working Paper 1274 -- Physical risk in credit models
"""
from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass, field as dc_field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedded Reference Data
# ---------------------------------------------------------------------------

SECTOR_NATURE_SENSITIVITY: dict[str, float] = {
    "agriculture": 1.40,
    "forestry": 1.35,
    "fishing": 1.35,
    "mining": 1.30,
    "oil_and_gas": 1.25,
    "energy": 1.20,
    "water_utilities": 1.30,
    "construction": 1.15,
    "manufacturing": 1.10,
    "chemicals": 1.20,
    "food_and_beverage": 1.25,
    "textiles": 1.15,
    "transport": 1.05,
    "real_estate": 1.10,
    "tourism": 1.20,
    "financial_services": 1.00,
    "technology": 1.00,
    "healthcare": 1.05,
    "general": 1.00,
}

NGFS_SCENARIO_PROBABILITIES: dict[str, float] = {
    "Net Zero 2050": 0.10,
    "Below 2C": 0.20,
    "Divergent Net Zero": 0.15,
    "Delayed Transition": 0.20,
    "NDCs": 0.20,
    "Current Policies": 0.15,
}


# ---------------------------------------------------------------------------
# Config & Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class IntegrationConfig:
    """Configuration for the climate-integrated risk calculation."""

    physical_weight: float = 0.50
    transition_weight: float = 0.50
    interaction_type: str = "additive"  # additive | multiplicative | max | custom
    interaction_alpha: float = 0.10
    scenario_weighting: str = "equal"  # equal | probability_weighted | custom
    scenario_weights: dict[str, float] = dc_field(default_factory=dict)
    nature_risk_amplifier_enabled: bool = False
    nature_risk_amplifier_cap: float = 1.50
    normalize_scores: bool = True


@dataclass
class IntegratedRiskResult:
    """Output of the integrated climate risk calculation for one entity."""

    entity_id: str
    entity_name: str

    # Component scores (0-100)
    physical_score: float
    transition_score: float

    # Integration terms
    interaction_term: float
    nature_amplifier: float  # 1.0 when disabled

    # Integrated output
    integrated_score: float  # 0-100 (capped)
    integrated_rating: str

    # Financial impact
    physical_cvar: float
    transition_cvar: float
    combined_cvar: float
    pd_adjustment: float
    lgd_adjustment: float

    # Multi-scenario detail
    scenario_scores: dict[str, float]

    # Diagnostics
    dominant_risk_type: str  # "physical" or "transition"
    risk_decomposition: dict[str, float]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ClimateIntegratedRisk:
    """Combines physical and transition risk into a single integrated score."""

    VALID_INTERACTION_TYPES = {"additive", "multiplicative", "max", "custom"}
    VALID_SCENARIO_WEIGHTINGS = {"equal", "probability_weighted", "custom"}

    def __init__(self, config: IntegrationConfig | None = None) -> None:
        self.config = config or IntegrationConfig()
        self._validate_config()
        logger.info(
            "ClimateIntegratedRisk initialised — interaction=%s, alpha=%.2f, "
            "weights=(P=%.2f, T=%.2f), nature_amplifier=%s",
            self.config.interaction_type,
            self.config.interaction_alpha,
            self.config.physical_weight,
            self.config.transition_weight,
            "ON" if self.config.nature_risk_amplifier_enabled else "OFF",
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_config(self) -> None:
        """Validate configuration parameters and raise on invalid values."""
        cfg = self.config
        weight_sum = cfg.physical_weight + cfg.transition_weight
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(
                f"physical_weight + transition_weight must be ~1.0, got {weight_sum:.4f}"
            )
        if not (0.0 <= cfg.interaction_alpha <= 1.0):
            raise ValueError(
                f"interaction_alpha must be in [0, 1], got {cfg.interaction_alpha}"
            )
        if cfg.interaction_type not in self.VALID_INTERACTION_TYPES:
            raise ValueError(
                f"interaction_type must be one of {self.VALID_INTERACTION_TYPES}, "
                f"got '{cfg.interaction_type}'"
            )
        if cfg.scenario_weighting not in self.VALID_SCENARIO_WEIGHTINGS:
            raise ValueError(
                f"scenario_weighting must be one of {self.VALID_SCENARIO_WEIGHTINGS}, "
                f"got '{cfg.scenario_weighting}'"
            )
        if not (1.0 <= cfg.nature_risk_amplifier_cap <= 3.0):
            raise ValueError(
                f"nature_risk_amplifier_cap must be in [1.0, 3.0], "
                f"got {cfg.nature_risk_amplifier_cap}"
            )

    # ------------------------------------------------------------------
    # Interaction Term
    # ------------------------------------------------------------------

    def compute_interaction_term(
        self, physical_score: float, transition_score: float
    ) -> float:
        """Compute the interaction term between physical and transition risk.

        The interaction captures the compounding effect when both risk types
        are elevated simultaneously (e.g., a stranded-asset holder in a
        flood-prone region).
        """
        alpha = self.config.interaction_alpha
        mode = self.config.interaction_type

        if mode == "additive":
            term = alpha * (physical_score + transition_score) / 2.0
        elif mode == "multiplicative":
            term = alpha * (physical_score * transition_score) / 100.0
        elif mode == "max":
            term = alpha * max(physical_score, transition_score)
        elif mode == "custom":
            term = alpha * math.sqrt(physical_score * transition_score)
        else:
            term = 0.0

        logger.debug(
            "Interaction term (%s): alpha=%.2f, P=%.1f, T=%.1f -> %.2f",
            mode, alpha, physical_score, transition_score, term,
        )
        return round(term, 4)

    # ------------------------------------------------------------------
    # Nature-Risk Amplifier
    # ------------------------------------------------------------------

    def compute_nature_amplifier(
        self, sector: str, lat: float = 0.0, lon: float = 0.0
    ) -> float:
        """Compute nature-risk amplifier based on sector ecosystem dependency.

        Uses ENCORE-aligned sensitivity factors.  The *lat/lon* parameters
        are reserved for future spatial lookups (e.g., proximity to
        biodiversity hotspots) but are not used in this version.
        """
        if not self.config.nature_risk_amplifier_enabled:
            return 1.0

        sensitivity = SECTOR_NATURE_SENSITIVITY.get(
            sector.lower().replace(" ", "_"), 1.0
        )
        amplifier = min(sensitivity, self.config.nature_risk_amplifier_cap)
        logger.debug(
            "Nature amplifier: sector=%s, sensitivity=%.2f, cap=%.2f -> %.2f",
            sector, sensitivity, self.config.nature_risk_amplifier_cap, amplifier,
        )
        return round(amplifier, 4)

    # ------------------------------------------------------------------
    # Scenario Weighting
    # ------------------------------------------------------------------

    def weight_scenarios(self, scenario_scores: dict[str, float]) -> float:
        """Weight per-scenario integrated scores into a single number.

        Returns:
            Weighted average integrated score (0-100).
        """
        if not scenario_scores:
            return 0.0

        mode = self.config.scenario_weighting

        if mode == "equal":
            result = sum(scenario_scores.values()) / len(scenario_scores)

        elif mode == "probability_weighted":
            total_weight = 0.0
            weighted_sum = 0.0
            for name, score in scenario_scores.items():
                w = NGFS_SCENARIO_PROBABILITIES.get(name, 0.0)
                weighted_sum += w * score
                total_weight += w
            result = weighted_sum / total_weight if total_weight > 0 else 0.0

        elif mode == "custom":
            total_weight = 0.0
            weighted_sum = 0.0
            for name, score in scenario_scores.items():
                w = self.config.scenario_weights.get(name, 0.0)
                weighted_sum += w * score
                total_weight += w
            result = weighted_sum / total_weight if total_weight > 0 else 0.0

        else:
            result = sum(scenario_scores.values()) / len(scenario_scores)

        logger.debug(
            "Scenario weighting (%s): %d scenarios -> %.2f",
            mode, len(scenario_scores), result,
        )
        return round(result, 4)

    # ------------------------------------------------------------------
    # Single-Scenario Integration
    # ------------------------------------------------------------------

    def integrate(
        self,
        physical_result,
        transition_result,
        sector: str = "general",
        lat: float = 0.0,
        lon: float = 0.0,
    ) -> IntegratedRiskResult:
        """Integrate one physical + transition result pair into a single score.

        Parameters:
            physical_result:   PhysicalRiskResult from the physical risk engine.
            transition_result: TransitionRiskResult from the transition risk engine.
            sector:            Sector key for nature-risk amplifier lookup.
            lat:               Latitude (reserved for future spatial lookups).
            lon:               Longitude (reserved for future spatial lookups).

        Returns:
            IntegratedRiskResult with combined score, CVaR, and PD/LGD adjustments.
        """
        p_score = physical_result.physical_risk_score
        t_score = transition_result.composite_transition_score

        interaction = self.compute_interaction_term(p_score, t_score)
        amplifier = self.compute_nature_amplifier(sector, lat, lon)

        cfg = self.config
        integrated_raw = (
            cfg.physical_weight * p_score
            + cfg.transition_weight * t_score
            + interaction
        ) * amplifier
        integrated_score = round(min(100.0, max(0.0, integrated_raw)), 2)

        # Financial impact aggregation
        physical_cvar = physical_result.physical_cvar
        transition_cvar = transition_result.max_transition_cvar
        combined_cvar = physical_cvar + transition_cvar

        pd_adj = max(physical_result.pd_adjustment, transition_result.max_pd_adjustment)
        lgd_adj = max(physical_result.lgd_adjustment, transition_result.max_lgd_adjustment)

        # Dominant risk type
        dominant = "physical" if p_score >= t_score else "transition"

        # Risk decomposition
        physical_contrib = round(cfg.physical_weight * p_score * amplifier, 2)
        transition_contrib = round(cfg.transition_weight * t_score * amplifier, 2)
        interaction_contrib = round(interaction * amplifier, 2)
        decomposition = {
            "physical_contribution": physical_contrib,
            "transition_contribution": transition_contrib,
            "interaction_contribution": interaction_contrib,
            "nature_amplifier": round(amplifier, 4),
        }

        rating = self.score_to_rating(integrated_score)

        logger.info(
            "Integrated risk for %s: P=%.1f T=%.1f interaction=%.2f "
            "amplifier=%.2f -> %.1f (%s)",
            physical_result.entity_name, p_score, t_score,
            interaction, amplifier, integrated_score, rating,
        )

        return IntegratedRiskResult(
            entity_id=physical_result.entity_id,
            entity_name=physical_result.entity_name,
            physical_score=round(p_score, 2),
            transition_score=round(t_score, 2),
            interaction_term=interaction,
            nature_amplifier=amplifier,
            integrated_score=integrated_score,
            integrated_rating=rating,
            physical_cvar=round(physical_cvar, 2),
            transition_cvar=round(transition_cvar, 2),
            combined_cvar=round(combined_cvar, 2),
            pd_adjustment=round(pd_adj, 6),
            lgd_adjustment=round(lgd_adj, 6),
            scenario_scores={},
            dominant_risk_type=dominant,
            risk_decomposition=decomposition,
        )

    # ------------------------------------------------------------------
    # Multi-Scenario Integration
    # ------------------------------------------------------------------

    def integrate_multi_scenario(
        self,
        physical_results: list,
        transition_results: list,
        sector: str = "general",
        lat: float = 0.0,
        lon: float = 0.0,
    ) -> IntegratedRiskResult:
        """Integrate across multiple scenarios and apply scenario weighting.

        Matches physical and transition results by scenario name, integrates
        each pair, then applies the configured scenario-weighting method
        to produce a single blended result.

        Parameters:
            physical_results:  List of PhysicalRiskResult (one per scenario).
            transition_results: List of TransitionRiskResult (one per entity;
                                each contains per-scenario stress results).
            sector:            Sector key for nature-risk amplifier.
            lat:               Latitude (reserved for future spatial lookups).
            lon:               Longitude (reserved for future spatial lookups).

        Returns:
            IntegratedRiskResult with scenario_scores populated and the
            integrated_score set to the weighted average.
        """
        if not physical_results:
            raise ValueError("physical_results list is empty")
        if not transition_results:
            raise ValueError("transition_results list is empty")

        # Build lookup of physical results by scenario
        phys_by_scenario: dict[str, object] = {}
        for pr in physical_results:
            phys_by_scenario[pr.scenario] = pr

        # Use the first transition result (they cover all scenarios internally)
        tr = transition_results[0]

        scenario_scores: dict[str, float] = {}
        per_scenario_results: list[IntegratedRiskResult] = []

        for scenario_name, phys in phys_by_scenario.items():
            result = self.integrate(phys, tr, sector, lat, lon)
            scenario_scores[scenario_name] = result.integrated_score
            per_scenario_results.append(result)

        weighted_score = self.weight_scenarios(scenario_scores)
        weighted_score = round(min(100.0, max(0.0, weighted_score)), 2)

        # Aggregate CVaR and PD/LGD across scenarios (worst-case)
        max_combined_cvar = max(
            (r.combined_cvar for r in per_scenario_results), default=0.0
        )
        max_pd = max(
            (r.pd_adjustment for r in per_scenario_results), default=0.0
        )
        max_lgd = max(
            (r.lgd_adjustment for r in per_scenario_results), default=0.0
        )

        # Average component scores for reporting
        avg_physical = sum(r.physical_score for r in per_scenario_results) / len(per_scenario_results)
        avg_transition = sum(r.transition_score for r in per_scenario_results) / len(per_scenario_results)
        dominant = "physical" if avg_physical >= avg_transition else "transition"

        rating = self.score_to_rating(weighted_score)

        logger.info(
            "Multi-scenario integration: %d scenarios, weighted=%.1f (%s), "
            "max CVaR=%.2f",
            len(scenario_scores), weighted_score, rating, max_combined_cvar,
        )

        # Decomposition uses averaged contributions
        amplifier = self.compute_nature_amplifier(sector, lat, lon)
        cfg = self.config
        decomposition = {
            "physical_contribution": round(cfg.physical_weight * avg_physical * amplifier, 2),
            "transition_contribution": round(cfg.transition_weight * avg_transition * amplifier, 2),
            "interaction_contribution": round(
                self.compute_interaction_term(avg_physical, avg_transition) * amplifier, 2
            ),
            "nature_amplifier": round(amplifier, 4),
        }

        return IntegratedRiskResult(
            entity_id=physical_results[0].entity_id,
            entity_name=physical_results[0].entity_name,
            physical_score=round(avg_physical, 2),
            transition_score=round(avg_transition, 2),
            interaction_term=self.compute_interaction_term(avg_physical, avg_transition),
            nature_amplifier=amplifier,
            integrated_score=weighted_score,
            integrated_rating=rating,
            physical_cvar=round(
                max((r.physical_cvar for r in per_scenario_results), default=0.0), 2
            ),
            transition_cvar=round(
                max((r.transition_cvar for r in per_scenario_results), default=0.0), 2
            ),
            combined_cvar=round(max_combined_cvar, 2),
            pd_adjustment=round(max_pd, 6),
            lgd_adjustment=round(max_lgd, 6),
            scenario_scores=scenario_scores,
            dominant_risk_type=dominant,
            risk_decomposition=decomposition,
        )

    # ------------------------------------------------------------------
    # Rating Helper
    # ------------------------------------------------------------------

    @staticmethod
    def score_to_rating(score: float) -> str:
        """Convert a 0-100 integrated risk score to a human-readable rating.

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
