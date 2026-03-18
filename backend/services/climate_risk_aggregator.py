"""
Climate Risk Aggregator -- Multi-Level Roll-Up of Risk Scores
=============================================================

Performs hierarchical aggregation of integrated climate risk scores from
asset level through security, fund, and portfolio levels.  Supports
multiple aggregation functions, diversification benefit discounting,
outlier treatment, and full contribution analysis.

Key capabilities:
  1. Flat aggregation via weighted-average, sum, max, min, median, or
     value-weighted methods
  2. Hierarchical (bottom-up) aggregation across four entity levels:
     asset (0) -> security (1) -> fund (2) -> portfolio (3)
  3. Winsorize / cap outlier treatment to reduce tail influence
  4. Portfolio diversification benefit discount (0.5-1.0 multiplier)
  5. Per-entity contribution and marginal-contribution analysis
  6. Descriptive statistics (mean, median, std_dev, percentiles)

Risk rating mapping (higher score = higher risk):
  0-19   Very Low
  20-39  Low
  40-59  Medium
  60-79  High
  80-100 Very High

Regulatory alignment:
  - TCFD: Portfolio-level climate risk aggregation guidance
  - PCAF: Financed-emissions attribution / roll-up
  - EBA GL/2022/16: ESG risk integration in credit portfolios
  - ECB Climate Stress Test: Bottom-up aggregation methodology

Author: Risk Analytics Platform
Version: 1.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# VALID ENUMERATIONS
# ---------------------------------------------------------------------------

VALID_AGGREGATION_FUNCTIONS: List[str] = [
    "weighted_average", "sum", "max", "min", "median", "value_weighted",
]

VALID_OUTLIER_TREATMENTS: List[str] = ["cap", "winsorize", "include"]

VALID_ENTITY_TYPES: List[str] = ["asset", "security", "fund", "portfolio"]

ENTITY_LEVEL_MAP: Dict[str, int] = {
    "asset": 0, "security": 1, "fund": 2, "portfolio": 3,
}


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

@dataclass
class AggregationConfig:
    """Configuration for risk score aggregation behaviour."""

    aggregation_function: str = "weighted_average"
    diversification_benefit_enabled: bool = True
    diversification_factor: float = 0.85
    outlier_treatment: str = "winsorize"
    outlier_percentile: float = 95.0
    contribution_analysis_enabled: bool = True
    minimum_entities_for_diversification: int = 3

    def __post_init__(self) -> None:
        if self.aggregation_function not in VALID_AGGREGATION_FUNCTIONS:
            raise ValueError(
                f"aggregation_function must be one of {VALID_AGGREGATION_FUNCTIONS}, "
                f"got '{self.aggregation_function}'"
            )
        if self.outlier_treatment not in VALID_OUTLIER_TREATMENTS:
            raise ValueError(
                f"outlier_treatment must be one of {VALID_OUTLIER_TREATMENTS}, "
                f"got '{self.outlier_treatment}'"
            )
        if not 0.5 <= self.diversification_factor <= 1.0:
            raise ValueError(
                f"diversification_factor must be in [0.5, 1.0], "
                f"got {self.diversification_factor}"
            )
        if not 80.0 <= self.outlier_percentile <= 100.0:
            raise ValueError(
                f"outlier_percentile must be in [80, 100], "
                f"got {self.outlier_percentile}"
            )


# ---------------------------------------------------------------------------
# ENTITY NODE
# ---------------------------------------------------------------------------

@dataclass
class EntityNode:
    """A single entity in the aggregation hierarchy.

    ``level`` follows the convention: 0 = asset, 1 = security, 2 = fund,
    3 = portfolio.  ``integrated_result`` should be an IntegratedRiskResult
    instance when available (duck-typed -- any object with the expected
    attributes will work).
    """

    entity_id: str
    entity_name: str
    entity_type: str
    level: int
    weight: float = 1.0
    value: float = 0.0
    parent_id: str | None = None
    integrated_result: object | None = None

    def __post_init__(self) -> None:
        if self.entity_type not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"entity_type must be one of {VALID_ENTITY_TYPES}, "
                f"got '{self.entity_type}'"
            )


# ---------------------------------------------------------------------------
# AGGREGATION RESULT
# ---------------------------------------------------------------------------

@dataclass
class AggregationResult:
    """Output of a single aggregation step."""

    group_id: str
    group_name: str
    group_level: str
    entity_count: int
    aggregated_score: float
    aggregated_rating: str
    aggregated_cvar: float
    physical_component: float
    transition_component: float
    diversification_applied: bool
    diversification_discount: float
    outlier_adjusted: bool
    contributions: List[Dict[str, Any]] = field(default_factory=list)
    statistics: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# AGGREGATOR
# ---------------------------------------------------------------------------

class ClimateRiskAggregator:
    """Multi-level climate risk score aggregator.

    Parameters
    ----------
    config : AggregationConfig | None
        Aggregation configuration.  Uses sensible defaults when *None*.
    """

    def __init__(self, config: AggregationConfig | None = None) -> None:
        self.config = config or AggregationConfig()
        logger.info(
            "ClimateRiskAggregator initialised  function=%s  "
            "diversification=%s (factor=%.2f)  outlier=%s (p=%.1f)",
            self.config.aggregation_function,
            self.config.diversification_benefit_enabled,
            self.config.diversification_factor,
            self.config.outlier_treatment,
            self.config.outlier_percentile,
        )

    # ------------------------------------------------------------------
    # PUBLIC -- flat aggregation
    # ------------------------------------------------------------------

    def aggregate(self, entities: List[EntityNode]) -> AggregationResult:
        """Aggregate a flat list of *EntityNode* objects into a single score.

        Parameters
        ----------
        entities : list[EntityNode]
            Entities to aggregate.  Each should carry an
            ``integrated_result`` with at least ``integrated_score``,
            ``physical_score``, ``transition_score``, and ``combined_cvar``
            attributes.

        Returns
        -------
        AggregationResult
        """
        if not entities:
            logger.warning("aggregate() called with empty entity list")
            return AggregationResult(
                group_id="empty",
                group_name="Empty Group",
                group_level="unknown",
                entity_count=0,
                aggregated_score=0.0,
                aggregated_rating=self.score_to_rating(0.0),
                aggregated_cvar=0.0,
                physical_component=0.0,
                transition_component=0.0,
                diversification_applied=False,
                diversification_discount=0.0,
                outlier_adjusted=False,
            )

        # --- extract raw vectors ---
        scores: List[float] = []
        weights: List[float] = []
        values: List[float] = []
        physical_scores: List[float] = []
        transition_scores: List[float] = []
        cvars: List[float] = []

        for ent in entities:
            ir = ent.integrated_result
            scores.append(getattr(ir, "integrated_score", 0.0) if ir else 0.0)
            physical_scores.append(getattr(ir, "physical_score", 0.0) if ir else 0.0)
            transition_scores.append(getattr(ir, "transition_score", 0.0) if ir else 0.0)
            cvars.append(getattr(ir, "combined_cvar", 0.0) if ir else 0.0)
            weights.append(max(ent.weight, 0.0))
            values.append(max(ent.value, 0.0))

        # --- outlier treatment ---
        scores, outlier_adjusted = self._treat_outliers(scores, weights)

        # --- aggregated score ---
        agg_score = self._apply_aggregation(scores, weights, values)

        # --- physical / transition components (always weighted-average) ---
        w_sum = sum(weights) or 1.0
        physical_component = sum(w * s for w, s in zip(weights, physical_scores)) / w_sum
        transition_component = sum(w * s for w, s in zip(weights, transition_scores)) / w_sum
        agg_cvar = sum(w * c for w, c in zip(weights, cvars)) / w_sum

        # --- diversification benefit ---
        div_applied = False
        div_discount = 0.0
        if (
            self.config.diversification_benefit_enabled
            and len(entities) >= self.config.minimum_entities_for_diversification
        ):
            div_applied = True
            div_discount = agg_score * (1.0 - self.config.diversification_factor)
            agg_score *= self.config.diversification_factor
            agg_cvar *= self.config.diversification_factor
            logger.debug(
                "Diversification benefit applied: factor=%.2f  discount=%.2f",
                self.config.diversification_factor,
                div_discount,
            )

        agg_score = max(0.0, min(100.0, agg_score))

        # --- contribution analysis ---
        contributions: List[Dict[str, Any]] = []
        if self.config.contribution_analysis_enabled:
            contributions = self._compute_contributions(
                entities, scores, weights, agg_score,
            )

        # --- descriptive statistics ---
        stats = self._compute_statistics(scores)

        group_level = entities[0].entity_type if entities else "unknown"

        return AggregationResult(
            group_id=f"agg_{group_level}_{len(entities)}",
            group_name=f"Aggregated {group_level.title()} Group",
            group_level=group_level,
            entity_count=len(entities),
            aggregated_score=round(agg_score, 4),
            aggregated_rating=self.score_to_rating(agg_score),
            aggregated_cvar=round(agg_cvar, 4),
            physical_component=round(physical_component, 4),
            transition_component=round(transition_component, 4),
            diversification_applied=div_applied,
            diversification_discount=round(div_discount, 4),
            outlier_adjusted=outlier_adjusted,
            contributions=contributions,
            statistics=stats,
        )

    # ------------------------------------------------------------------
    # PUBLIC -- hierarchical aggregation
    # ------------------------------------------------------------------

    def aggregate_hierarchy(self, entity_tree: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate a nested hierarchy bottom-up.

        Parameters
        ----------
        entity_tree : dict
            Nested dict whose leaf values are lists of *EntityNode*.
            Expected shape::

                {
                    "portfolio_name": {
                        "fund_a": {
                            "security_x": {
                                "assets": [EntityNode, ...]
                            }
                        }
                    }
                }

            Any dict value that is a *list* is treated as the leaf level
            (list of EntityNode).

        Returns
        -------
        dict
            Mirrored structure with an ``_result`` key holding the
            *AggregationResult* at every intermediate and root level.
        """
        logger.info("aggregate_hierarchy() starting bottom-up roll-up")
        return self._recurse_aggregate(entity_tree, depth=0)

    # ------------------------------------------------------------------
    # STATIC -- score to rating
    # ------------------------------------------------------------------

    @staticmethod
    def score_to_rating(score: float) -> str:
        """Map a 0-100 risk score to a categorical rating label.

        Thresholds
        ----------
        < 20  -> Very Low
        < 40  -> Low
        < 60  -> Medium
        < 80  -> High
        >= 80 -> Very High
        """
        if score < 20.0:
            return "Very Low"
        if score < 40.0:
            return "Low"
        if score < 60.0:
            return "Medium"
        if score < 80.0:
            return "High"
        return "Very High"

    # ------------------------------------------------------------------
    # PRIVATE -- aggregation functions
    # ------------------------------------------------------------------

    def _apply_aggregation(
        self,
        scores: List[float],
        weights: List[float],
        values: List[float],
    ) -> float:
        """Dispatch to the configured aggregation function."""
        fn = self.config.aggregation_function

        if fn == "weighted_average":
            w_sum = sum(weights) or 1.0
            return sum(w * s for w, s in zip(weights, scores)) / w_sum

        if fn == "sum":
            return sum(scores)

        if fn == "max":
            return max(scores) if scores else 0.0

        if fn == "min":
            return min(scores) if scores else 0.0

        if fn == "median":
            return float(statistics.median(scores)) if scores else 0.0

        if fn == "value_weighted":
            v_sum = sum(values) or 1.0
            return sum(v * s for v, s in zip(values, scores)) / v_sum

        # Fallback (should not reach here due to validation)
        logger.error("Unknown aggregation function '%s'; falling back to mean", fn)
        return statistics.mean(scores) if scores else 0.0

    # ------------------------------------------------------------------
    # PRIVATE -- outlier treatment
    # ------------------------------------------------------------------

    def _treat_outliers(
        self,
        scores: List[float],
        weights: List[float],
    ) -> Tuple[List[float], bool]:
        """Apply outlier treatment to *scores*.

        Returns
        -------
        (treated_scores, was_adjusted)
        """
        treatment = self.config.outlier_treatment

        if treatment == "include" or len(scores) < 2:
            return scores, False

        pct = self.config.outlier_percentile / 100.0
        sorted_scores = sorted(scores)
        n = len(sorted_scores)

        if treatment == "cap":
            threshold = self._percentile(sorted_scores, pct)
            adjusted = [min(s, threshold) for s in scores]
            changed = adjusted != scores
            if changed:
                logger.debug(
                    "Outlier cap applied at p%.0f (threshold=%.2f)",
                    self.config.outlier_percentile,
                    threshold,
                )
            return adjusted, changed

        if treatment == "winsorize":
            p_low = self._percentile(sorted_scores, 1.0 - pct)
            p_high = self._percentile(sorted_scores, pct)
            adjusted = [max(p_low, min(s, p_high)) for s in scores]
            changed = adjusted != scores
            if changed:
                logger.debug(
                    "Winsorize applied: low=%.2f  high=%.2f",
                    p_low,
                    p_high,
                )
            return adjusted, changed

        return scores, False

    # ------------------------------------------------------------------
    # PRIVATE -- contribution analysis
    # ------------------------------------------------------------------

    def _compute_contributions(
        self,
        entities: List[EntityNode],
        scores: List[float],
        weights: List[float],
        agg_score: float,
    ) -> List[Dict[str, Any]]:
        """Compute per-entity contribution and marginal contribution.

        contribution_pct = (w_i * s_i) / sum(w_j * s_j) * 100
        marginal_contribution = s_i - mean(scores)
        """
        total_weighted = sum(w * s for w, s in zip(weights, scores)) or 1.0
        mean_score = statistics.mean(scores) if scores else 0.0

        contributions: List[Dict[str, Any]] = []
        for ent, score, weight in zip(entities, scores, weights):
            contrib_pct = (weight * score) / total_weighted * 100.0
            marginal = score - mean_score
            contributions.append({
                "entity_id": ent.entity_id,
                "entity_name": ent.entity_name,
                "score": round(score, 4),
                "weight": round(weight, 4),
                "contribution_pct": round(contrib_pct, 4),
                "marginal_contribution": round(marginal, 4),
            })

        # Sort descending by contribution
        contributions.sort(key=lambda c: c["contribution_pct"], reverse=True)
        return contributions

    # ------------------------------------------------------------------
    # PRIVATE -- descriptive statistics
    # ------------------------------------------------------------------

    def _compute_statistics(self, scores: List[float]) -> Dict[str, float]:
        """Return descriptive statistics for the score distribution."""
        if not scores:
            return {
                "mean": 0.0, "median": 0.0, "std_dev": 0.0,
                "min": 0.0, "max": 0.0,
                "p5": 0.0, "p25": 0.0, "p75": 0.0, "p95": 0.0,
            }

        sorted_s = sorted(scores)
        n = len(sorted_s)

        mean_val = statistics.mean(sorted_s)
        median_val = statistics.median(sorted_s)
        std_val = statistics.stdev(sorted_s) if n >= 2 else 0.0

        return {
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "std_dev": round(std_val, 4),
            "min": round(sorted_s[0], 4),
            "max": round(sorted_s[-1], 4),
            "p5": round(self._percentile(sorted_s, 0.05), 4),
            "p25": round(self._percentile(sorted_s, 0.25), 4),
            "p75": round(self._percentile(sorted_s, 0.75), 4),
            "p95": round(self._percentile(sorted_s, 0.95), 4),
        }

    # ------------------------------------------------------------------
    # PRIVATE -- hierarchy recursion
    # ------------------------------------------------------------------

    def _recurse_aggregate(
        self,
        node: Dict[str, Any] | List[EntityNode],
        depth: int,
    ) -> Dict[str, Any]:
        """Recursively aggregate from leaves to root."""
        # Base case: leaf list of EntityNode
        if isinstance(node, list):
            result = self.aggregate(node)
            return {"_result": result, "_entities": node}

        # Recursive case: dict of children
        output: Dict[str, Any] = {}
        child_pseudo_entities: List[EntityNode] = []

        for key, child in node.items():
            child_output = self._recurse_aggregate(child, depth + 1)
            output[key] = child_output

            # Build a pseudo-entity from the child aggregation to roll up
            child_result: AggregationResult | None = child_output.get("_result")
            if child_result is not None:
                # Create a lightweight stand-in object for the child result
                pseudo_ir = _PseudoIntegratedResult(
                    integrated_score=child_result.aggregated_score,
                    physical_score=child_result.physical_component,
                    transition_score=child_result.transition_component,
                    combined_cvar=child_result.aggregated_cvar,
                )
                level_type = VALID_ENTITY_TYPES[min(depth, len(VALID_ENTITY_TYPES) - 1)]
                child_pseudo_entities.append(EntityNode(
                    entity_id=child_result.group_id,
                    entity_name=child_result.group_name,
                    entity_type=level_type,
                    level=depth,
                    weight=float(child_result.entity_count),
                    value=0.0,
                    integrated_result=pseudo_ir,
                ))

        if child_pseudo_entities:
            output["_result"] = self.aggregate(child_pseudo_entities)
        else:
            output["_result"] = None

        return output

    # ------------------------------------------------------------------
    # PRIVATE -- percentile helper (linear interpolation)
    # ------------------------------------------------------------------

    @staticmethod
    def _percentile(sorted_values: List[float], pct: float) -> float:
        """Compute the *pct*-th percentile using linear interpolation.

        Parameters
        ----------
        sorted_values : list[float]
            Pre-sorted list of values.
        pct : float
            Percentile in [0.0, 1.0].
        """
        if not sorted_values:
            return 0.0
        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]

        k = pct * (n - 1)
        lo = int(math.floor(k))
        hi = min(lo + 1, n - 1)
        frac = k - lo
        return sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo])


# ---------------------------------------------------------------------------
# INTERNAL HELPER -- lightweight stand-in for IntegratedRiskResult
# ---------------------------------------------------------------------------

@dataclass
class _PseudoIntegratedResult:
    """Minimal duck-typed substitute used during hierarchy roll-up."""

    integrated_score: float = 0.0
    physical_score: float = 0.0
    transition_score: float = 0.0
    combined_cvar: float = 0.0
