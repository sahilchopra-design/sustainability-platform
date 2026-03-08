"""
Counterparty Climate Risk Scorer -- Composite Climate Score (0-100)

Implements a composite climate risk scoring framework per:
  - EBA GL/2022/16: ESG risk management in credit risk
  - ECB Guide on climate-related and environmental risks (Nov 2020)
  - BCBS Principles for climate-related financial risks (June 2022)
  - NGFS conceptual framework for climate risk scoring

Composite score = weighted average of:
  - Transition Risk Score (40%): Carbon intensity rank, sector risk, policy exposure, tech readiness
  - Physical Risk Score (30%): Flood risk, heat stress, water stress, supply chain exposure
  - Alignment Score (20%): SBTi commitment, taxonomy alignment, transition plan quality
  - Data Quality Score (10%): Disclosure level, data recency, third-party verification

Each component scored 0-100 (higher = better).

Rating mapping (composite score -> letter grade):
  90-100 = A+
  80-89  = A
  70-79  = B+
  60-69  = B
  50-59  = C+
  40-49  = C
  30-39  = D+
  0-29   = D-

Author: Counterparty Climate Scorer Module
Version: 2.0.0
Date: 2026-03-08
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RATING MAP (higher score = better)
# ---------------------------------------------------------------------------

RATING_MAP: List[Dict[str, Any]] = [
    {"min": 90, "max": 100, "rating": "A+", "label": "Excellent climate posture"},
    {"min": 80, "max": 89,  "rating": "A",  "label": "Strong climate posture"},
    {"min": 70, "max": 79,  "rating": "B+", "label": "Good climate posture"},
    {"min": 60, "max": 69,  "rating": "B",  "label": "Adequate climate posture"},
    {"min": 50, "max": 59,  "rating": "C+", "label": "Below-average climate posture"},
    {"min": 40, "max": 49,  "rating": "C",  "label": "Weak climate posture"},
    {"min": 30, "max": 39,  "rating": "D+", "label": "Poor climate posture"},
    {"min": 0,  "max": 29,  "rating": "D-", "label": "Very poor climate posture"},
]


# ---------------------------------------------------------------------------
# SECTOR TRANSITION RISK -- base risk levels (higher = MORE transition risk)
# Used to derive the transition risk sub-component when counterparty-level
# data is sparse.
# ---------------------------------------------------------------------------

SECTOR_TRANSITION_RISK: Dict[str, str] = {
    "Oil & Gas": "very_high",
    "Coal Mining": "very_high",
    "Power Generation": "high",
    "Steel": "high",
    "Cement": "high",
    "Airlines": "high",
    "Shipping": "high",
    "Chemicals": "medium",
    "Automotive": "medium",
    "Metals & Mining": "medium",
    "Agriculture": "medium",
    "Utilities": "medium",
    "Real Estate": "medium",
    "Construction": "medium",
    "Food & Beverage": "low",
    "Retail": "low",
    "Telecommunications": "low",
    "Financial Services": "low",
    "Technology": "low",
    "Healthcare": "low",
    "Paper & Forestry": "medium",
    "Textiles": "medium",
}

# Numeric mapping for sector risk levels (used in scoring)
_SECTOR_RISK_SCORES: Dict[str, float] = {
    "low": 80.0,
    "medium": 55.0,
    "high": 30.0,
    "very_high": 10.0,
}


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------


@dataclass
class CounterpartyInput:
    """Input data for climate scoring a single counterparty."""
    counterparty_id: str
    counterparty_name: str
    sector: str
    country: str = ""

    # Transition risk inputs
    carbon_intensity_rank: Optional[float] = None        # 0-100 (100 = best / lowest intensity)
    sector_risk_level: Optional[str] = None              # low / medium / high / very_high
    policy_exposure_score: Optional[float] = None        # 0-100 (100 = least exposed)
    technology_readiness: Optional[float] = None         # 0-100 (100 = most ready)

    # Physical risk inputs
    flood_risk: Optional[float] = None                   # 0-100 (100 = lowest risk)
    heat_stress: Optional[float] = None                  # 0-100 (100 = lowest stress)
    water_stress: Optional[float] = None                 # 0-100 (100 = lowest stress)
    supply_chain_exposure: Optional[float] = None        # 0-100 (100 = least exposed)

    # Alignment inputs
    sbti_committed: bool = False                         # +20 points if True
    taxonomy_aligned_pct: Optional[float] = None         # 0-100, mapped to 0-40
    transition_plan_quality: Optional[int] = None        # 1-5, mapped to 0-40

    # Data quality inputs
    disclosure_level: str = "none"                       # none / partial / full -> 0 / 50 / 100
    data_recency_years: Optional[float] = None           # 0-5, mapped inversely
    third_party_verified: bool = False                   # +30 if True


@dataclass
class ScoreBreakdown:
    """Breakdown for a single scoring component."""
    component_name: str
    weight: float
    raw_score: float                     # 0-100 before weighting
    weighted_score: float                # raw * weight
    sub_scores: Dict[str, float]         # Named sub-component scores
    data_available: bool


@dataclass
class ClimateScoreResult:
    """Complete counterparty climate score result."""
    counterparty_id: str
    counterparty_name: str
    sector: str

    composite_score: float               # 0-100 (higher = better)
    rating: str                          # A+ through D-
    rating_label: str

    transition_risk: ScoreBreakdown
    physical_risk: ScoreBreakdown
    alignment: ScoreBreakdown
    data_quality: ScoreBreakdown

    methodology_notes: List[str]


# ---------------------------------------------------------------------------
# MAIN SCORER CLASS
# ---------------------------------------------------------------------------


class CounterpartyClimateScorer:
    """
    Counterparty composite climate risk scorer.

    Produces a 0-100 score (higher = better) mapped to A+ through D-.

    Default weights:
      Transition Risk: 40%
      Physical Risk:   30%
      Alignment:       20%
      Data Quality:    10%
    """

    DEFAULT_WEIGHTS = {
        "transition_risk": 0.40,
        "physical_risk": 0.30,
        "alignment": 0.20,
        "data_quality": 0.10,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        """
        Initialize scorer with optional custom weights.

        Args:
            weights: Custom component weights (must sum to 1.0).

        Raises:
            ValueError: If weights do not sum to 1.0 (+/- 0.01).
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")

    # -------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------

    def score(self, inp: CounterpartyInput) -> ClimateScoreResult:
        """
        Calculate composite climate score for a single counterparty.

        Args:
            inp: CounterpartyInput with all available data.

        Returns:
            ClimateScoreResult with score, rating, and breakdown.
        """
        notes: List[str] = []

        tr = self._score_transition_risk(inp, notes)
        pr = self._score_physical_risk(inp, notes)
        al = self._score_alignment(inp, notes)
        dq = self._score_data_quality(inp, notes)

        composite = (
            tr.weighted_score
            + pr.weighted_score
            + al.weighted_score
            + dq.weighted_score
        )
        composite = float(np.clip(round(composite, 1), 0, 100))

        rating, label = self._score_to_rating(composite)

        notes.append(
            f"Composite: {composite:.1f} ({rating}) | "
            f"TR={tr.raw_score:.0f} PR={pr.raw_score:.0f} "
            f"AL={al.raw_score:.0f} DQ={dq.raw_score:.0f}"
        )

        return ClimateScoreResult(
            counterparty_id=inp.counterparty_id,
            counterparty_name=inp.counterparty_name,
            sector=inp.sector,
            composite_score=composite,
            rating=rating,
            rating_label=label,
            transition_risk=tr,
            physical_risk=pr,
            alignment=al,
            data_quality=dq,
            methodology_notes=notes,
        )

    def score_batch(
        self, inputs: List[CounterpartyInput]
    ) -> List[ClimateScoreResult]:
        """Score multiple counterparties."""
        return [self.score(inp) for inp in inputs]

    # -------------------------------------------------------------------
    # TRANSITION RISK (40%) -- 0-100, higher = lower risk = better
    # -------------------------------------------------------------------

    def _score_transition_risk(
        self, inp: CounterpartyInput, notes: List[str]
    ) -> ScoreBreakdown:
        """
        Score transition risk.  All sub-scores are 0-100 (100 = best).

        Sub-components:
          carbon_intensity_rank (30%): direct input 0-100
          sector_risk (25%): mapped from low/medium/high/very_high
          policy_exposure (25%): direct input 0-100
          technology_readiness (20%): direct input 0-100
        """
        w = self.weights["transition_risk"]
        sub: Dict[str, float] = {}
        data_available = False

        # Carbon intensity rank
        if inp.carbon_intensity_rank is not None:
            sub["carbon_intensity_rank"] = float(np.clip(inp.carbon_intensity_rank, 0, 100))
            data_available = True
        else:
            # Fall back to sector-based estimate
            sr = inp.sector_risk_level or SECTOR_TRANSITION_RISK.get(inp.sector, "medium")
            sub["carbon_intensity_rank"] = _SECTOR_RISK_SCORES.get(sr, 55.0)

        # Sector risk level
        sr_level = inp.sector_risk_level or SECTOR_TRANSITION_RISK.get(inp.sector, "medium")
        sub["sector_risk"] = _SECTOR_RISK_SCORES.get(sr_level, 55.0)
        if inp.sector_risk_level is not None:
            data_available = True

        # Policy exposure
        if inp.policy_exposure_score is not None:
            sub["policy_exposure"] = float(np.clip(inp.policy_exposure_score, 0, 100))
            data_available = True
        else:
            sub["policy_exposure"] = sub["sector_risk"]  # proxy

        # Technology readiness
        if inp.technology_readiness is not None:
            sub["technology_readiness"] = float(np.clip(inp.technology_readiness, 0, 100))
            data_available = True
        else:
            sub["technology_readiness"] = 50.0  # neutral default

        raw = (
            sub["carbon_intensity_rank"] * 0.30
            + sub["sector_risk"] * 0.25
            + sub["policy_exposure"] * 0.25
            + sub["technology_readiness"] * 0.20
        )
        raw = float(np.clip(round(raw, 1), 0, 100))
        weighted = round(raw * w, 2)

        notes.append(f"Transition risk: raw={raw:.1f}, weighted={weighted:.2f}")

        return ScoreBreakdown(
            component_name="Transition Risk",
            weight=w,
            raw_score=raw,
            weighted_score=weighted,
            sub_scores=sub,
            data_available=data_available,
        )

    # -------------------------------------------------------------------
    # PHYSICAL RISK (30%) -- 0-100, higher = lower risk = better
    # -------------------------------------------------------------------

    def _score_physical_risk(
        self, inp: CounterpartyInput, notes: List[str]
    ) -> ScoreBreakdown:
        """
        Score physical risk.

        Sub-components (equal weight 25% each):
          flood_risk, heat_stress, water_stress, supply_chain_exposure
        All 0-100 where 100 = lowest risk.
        """
        w = self.weights["physical_risk"]
        sub: Dict[str, float] = {}
        data_available = False

        for field_name, default in [
            ("flood_risk", 60.0),
            ("heat_stress", 60.0),
            ("water_stress", 60.0),
            ("supply_chain_exposure", 60.0),
        ]:
            val = getattr(inp, field_name, None)
            if val is not None:
                sub[field_name] = float(np.clip(val, 0, 100))
                data_available = True
            else:
                sub[field_name] = default

        raw = (
            sub["flood_risk"] * 0.25
            + sub["heat_stress"] * 0.25
            + sub["water_stress"] * 0.25
            + sub["supply_chain_exposure"] * 0.25
        )
        raw = float(np.clip(round(raw, 1), 0, 100))
        weighted = round(raw * w, 2)

        notes.append(f"Physical risk: raw={raw:.1f}, weighted={weighted:.2f}")

        return ScoreBreakdown(
            component_name="Physical Risk",
            weight=w,
            raw_score=raw,
            weighted_score=weighted,
            sub_scores=sub,
            data_available=data_available,
        )

    # -------------------------------------------------------------------
    # ALIGNMENT (20%) -- 0-100, higher = better alignment
    # -------------------------------------------------------------------

    def _score_alignment(
        self, inp: CounterpartyInput, notes: List[str]
    ) -> ScoreBreakdown:
        """
        Score climate alignment.

        Sub-components:
          sbti_committed: bool -> +20 points (out of 100)
          taxonomy_aligned_pct: 0-100 mapped to 0-40
          transition_plan_quality: 1-5 mapped to 0-40
        """
        w = self.weights["alignment"]
        sub: Dict[str, float] = {}
        data_available = False

        # SBTi commitment: +20
        sbti_pts = 20.0 if inp.sbti_committed else 0.0
        sub["sbti_committed"] = sbti_pts
        if inp.sbti_committed:
            data_available = True

        # Taxonomy aligned pct: 0-100 -> 0-40
        if inp.taxonomy_aligned_pct is not None:
            tax_pts = float(np.clip(inp.taxonomy_aligned_pct, 0, 100)) / 100.0 * 40.0
            sub["taxonomy_aligned"] = round(tax_pts, 1)
            data_available = True
        else:
            sub["taxonomy_aligned"] = 0.0

        # Transition plan quality: 1-5 -> 0-40
        if inp.transition_plan_quality is not None:
            tp = int(np.clip(inp.transition_plan_quality, 1, 5))
            tp_pts = (tp - 1) / 4.0 * 40.0  # 1->0, 2->10, 3->20, 4->30, 5->40
            sub["transition_plan"] = round(tp_pts, 1)
            data_available = True
        else:
            sub["transition_plan"] = 0.0

        raw = sub["sbti_committed"] + sub["taxonomy_aligned"] + sub["transition_plan"]
        raw = float(np.clip(round(raw, 1), 0, 100))
        weighted = round(raw * w, 2)

        notes.append(f"Alignment: raw={raw:.1f}, weighted={weighted:.2f}")

        return ScoreBreakdown(
            component_name="Alignment",
            weight=w,
            raw_score=raw,
            weighted_score=weighted,
            sub_scores=sub,
            data_available=data_available,
        )

    # -------------------------------------------------------------------
    # DATA QUALITY (10%) -- 0-100, higher = better data
    # -------------------------------------------------------------------

    def _score_data_quality(
        self, inp: CounterpartyInput, notes: List[str]
    ) -> ScoreBreakdown:
        """
        Score data quality.

        Sub-components:
          disclosure_level: none=0, partial=50, full=100
          data_recency_years: 0->100, 5->0 (linear inverse)
          third_party_verified: bool -> +30
        Max possible = 100+100+30 = 230, but we cap at 100 after normalize.
        Weighted: disclosure 40%, recency 30%, verified 30%.
        """
        w = self.weights["data_quality"]
        sub: Dict[str, float] = {}

        # Disclosure level
        disc_map = {"none": 0.0, "partial": 50.0, "full": 100.0}
        sub["disclosure_level"] = disc_map.get(inp.disclosure_level, 0.0)

        # Data recency (0 years lag = 100, 5 years lag = 0)
        if inp.data_recency_years is not None:
            lag = float(np.clip(inp.data_recency_years, 0, 5))
            sub["data_recency"] = round((1.0 - lag / 5.0) * 100.0, 1)
        else:
            sub["data_recency"] = 20.0  # assume stale if unknown

        # Third-party verified: +30 bonus (added into weighted calc)
        verified_pts = 30.0 if inp.third_party_verified else 0.0
        sub["third_party_verified"] = verified_pts

        raw = (
            sub["disclosure_level"] * 0.40
            + sub["data_recency"] * 0.30
            + sub["third_party_verified"]  # additive bonus, not pct-weighted
        )
        raw = float(np.clip(round(raw, 1), 0, 100))
        weighted = round(raw * w, 2)

        data_available = inp.disclosure_level != "none" or inp.data_recency_years is not None

        notes.append(f"Data quality: raw={raw:.1f}, weighted={weighted:.2f}")

        return ScoreBreakdown(
            component_name="Data Quality",
            weight=w,
            raw_score=raw,
            weighted_score=weighted,
            sub_scores=sub,
            data_available=data_available,
        )

    # -------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------

    @staticmethod
    def _score_to_rating(score: float) -> tuple:
        """Map composite score (0-100, higher=better) to rating and label."""
        for band in RATING_MAP:
            if band["min"] <= score <= band["max"]:
                return band["rating"], band["label"]
        # Below lowest band
        return "D-", "Very poor climate posture"

    @staticmethod
    def get_rating_scale() -> List[Dict[str, Any]]:
        """Return the full rating scale."""
        return list(RATING_MAP)

    @staticmethod
    def get_sector_risk_levels() -> Dict[str, str]:
        """Return sector-level transition risk classifications."""
        return dict(SECTOR_TRANSITION_RISK)

    @staticmethod
    def get_default_weights() -> Dict[str, float]:
        """Return default scoring weights."""
        return dict(CounterpartyClimateScorer.DEFAULT_WEIGHTS)
