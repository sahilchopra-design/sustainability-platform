"""
PPA Risk Scoring Engine
========================
Power Purchase Agreement risk assessment covering counterparty credit,
price structure, tenor, curtailment risk, and regulatory exposure.

References:
- EFET — Standard PPA risk framework
- IRENA — Corporate PPA guidelines
- Pexapark — European PPA market analysis
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — Risk Factor Scores
# ---------------------------------------------------------------------------

# Counterparty credit risk (score 0-100, higher = riskier)
CREDIT_SCORES: dict[str, int] = {
    "AAA": 5, "AA": 8, "A": 12, "BBB": 20, "BB": 35,
    "B": 50, "CCC": 70, "unrated_ig": 25, "unrated_sub_ig": 55,
    "unrated": 40, "sovereign": 10, "utility": 15,
}

# Price structure risk
PRICE_STRUCTURE_SCORES: dict[str, int] = {
    "fixed": 10,
    "fixed_escalation": 15,
    "cap_floor": 25,
    "indexed_power": 35,
    "indexed_gas": 45,
    "partial_merchant": 55,
    "full_merchant": 80,
    "subsidy_cfd": 12,
    "feed_in_tariff": 8,
}

# Tenor risk
TENOR_RISK: dict[str, dict] = {
    "short": {"label": "< 5 years", "min_yr": 0, "max_yr": 5, "score": 40},
    "medium": {"label": "5-15 years", "min_yr": 5, "max_yr": 15, "score": 20},
    "long": {"label": "> 15 years", "min_yr": 15, "max_yr": 99, "score": 10},
}

# Curtailment risk by grid region
CURTAILMENT_RISK: dict[str, dict] = {
    "low": {"label": "Low congestion", "score": 10, "example": "Strong grid, no constraints"},
    "moderate": {"label": "Moderate congestion", "score": 30, "example": "Occasional negative pricing"},
    "high": {"label": "High congestion", "score": 55, "example": "Frequent curtailment, weak grid"},
    "very_high": {"label": "Very high congestion", "score": 75, "example": "Island grid, storage deficit"},
}

# Regulatory risk
REGULATORY_RISK: dict[str, dict] = {
    "stable": {"label": "Stable framework", "score": 10, "example": "DE, NL, FR"},
    "moderate": {"label": "Moderate policy risk", "score": 25, "example": "IT, ES, PL"},
    "high": {"label": "High policy risk", "score": 45, "example": "Subsidy clawback, retroactive changes"},
    "very_high": {"label": "Very high policy risk", "score": 70, "example": "Unstable regime, no track record"},
}


# Dimension weights
PPA_RISK_WEIGHTS: dict[str, float] = {
    "counterparty_credit": 0.25,
    "price_structure": 0.25,
    "tenor": 0.15,
    "curtailment": 0.20,
    "regulatory": 0.15,
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class PPAInput:
    """Input for PPA risk scoring."""
    ppa_id: str
    project_name: str
    offtaker_name: str
    offtaker_credit_rating: str = "unrated"
    price_structure: str = "fixed"
    ppa_price_eur_mwh: float = 60.0
    tenor_years: float = 10.0
    curtailment_risk: str = "low"
    regulatory_risk: str = "stable"
    volume_hedged_pct: float = 100.0  # % of generation under PPA
    merchant_exposure_pct: float = 0.0
    subsidy_dependence_pct: float = 0.0


@dataclass
class PPARiskDimension:
    """Score for a single risk dimension."""
    dimension: str
    label: str
    raw_score: int  # 0-100
    weight: float
    weighted_score: float
    risk_level: str  # "low" | "moderate" | "high" | "very_high"


@dataclass
class PPARiskResult:
    """Complete PPA risk assessment."""
    ppa_id: str
    project_name: str
    offtaker_name: str
    dimension_scores: list[PPARiskDimension]
    composite_score: float  # 0-100
    risk_band: str  # "low" | "moderate" | "high" | "critical"
    risk_factors: list[str]  # Key risk narratives
    mitigation_suggestions: list[str]
    bankability_rating: str  # "bankable" | "conditionally_bankable" | "non_bankable"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PPARiskScorer:
    """PPA risk scoring engine."""

    def score_ppa(self, inp: PPAInput) -> PPARiskResult:
        """Score a PPA across all risk dimensions."""
        dims = []
        risk_factors = []
        mitigations = []

        # 1. Counterparty credit
        credit_score = CREDIT_SCORES.get(inp.offtaker_credit_rating, 40)
        dims.append(self._make_dim("counterparty_credit", "Counterparty Credit", credit_score))
        if credit_score >= 40:
            risk_factors.append(f"Offtaker {inp.offtaker_name} has elevated credit risk ({inp.offtaker_credit_rating})")
            mitigations.append("Obtain parent company guarantee or letter of credit")

        # 2. Price structure
        price_score = PRICE_STRUCTURE_SCORES.get(inp.price_structure, 35)
        # Adjust for merchant exposure
        if inp.merchant_exposure_pct > 0:
            price_score = min(100, price_score + int(inp.merchant_exposure_pct * 0.5))
        dims.append(self._make_dim("price_structure", "Price Structure", price_score))
        if price_score >= 40:
            risk_factors.append(f"Price structure '{inp.price_structure}' carries significant market risk")
            mitigations.append("Consider cap/floor or partial indexation to reduce price volatility")

        # 3. Tenor
        tenor_score = self._tenor_score(inp.tenor_years)
        dims.append(self._make_dim("tenor", "Tenor", tenor_score))
        if inp.tenor_years < 5:
            risk_factors.append(f"Short PPA tenor ({inp.tenor_years}yr) — refinancing risk")
            mitigations.append("Extend tenor or secure back-up offtake agreement")

        # 4. Curtailment
        curt = CURTAILMENT_RISK.get(inp.curtailment_risk, CURTAILMENT_RISK["moderate"])
        curt_score = curt["score"]
        dims.append(self._make_dim("curtailment", "Curtailment / Grid Risk", curt_score))
        if curt_score >= 30:
            risk_factors.append(f"Curtailment risk: {curt['label']}")
            mitigations.append("Investigate battery storage co-location or grid upgrade timeline")

        # 5. Regulatory
        reg = REGULATORY_RISK.get(inp.regulatory_risk, REGULATORY_RISK["moderate"])
        reg_score = reg["score"]
        if inp.subsidy_dependence_pct > 50:
            reg_score = min(100, reg_score + 20)
            risk_factors.append(f"High subsidy dependence ({inp.subsidy_dependence_pct}%)")
            mitigations.append("Diversify revenue streams to reduce subsidy reliance")
        dims.append(self._make_dim("regulatory", "Regulatory", reg_score))

        # Composite
        composite = round(sum(d.weighted_score for d in dims), 1)

        # Risk band
        if composite <= 20:
            band = "low"
        elif composite <= 35:
            band = "moderate"
        elif composite <= 55:
            band = "high"
        else:
            band = "critical"

        # Bankability
        if composite <= 25 and credit_score <= 25:
            bankability = "bankable"
        elif composite <= 40:
            bankability = "conditionally_bankable"
        else:
            bankability = "non_bankable"

        return PPARiskResult(
            ppa_id=inp.ppa_id,
            project_name=inp.project_name,
            offtaker_name=inp.offtaker_name,
            dimension_scores=dims,
            composite_score=composite,
            risk_band=band,
            risk_factors=risk_factors,
            mitigation_suggestions=mitigations,
            bankability_rating=bankability,
        )

    def get_credit_ratings(self) -> dict[str, int]:
        return CREDIT_SCORES

    def get_price_structures(self) -> dict[str, int]:
        return PRICE_STRUCTURE_SCORES

    def _make_dim(self, dim_id: str, label: str, raw_score: int) -> PPARiskDimension:
        weight = PPA_RISK_WEIGHTS.get(dim_id, 0.2)
        if raw_score <= 20:
            level = "low"
        elif raw_score <= 35:
            level = "moderate"
        elif raw_score <= 55:
            level = "high"
        else:
            level = "very_high"

        return PPARiskDimension(
            dimension=dim_id,
            label=label,
            raw_score=raw_score,
            weight=weight,
            weighted_score=round(raw_score * weight, 2),
            risk_level=level,
        )

    def _tenor_score(self, years: float) -> int:
        for key, info in TENOR_RISK.items():
            if info["min_yr"] <= years < info["max_yr"]:
                return info["score"]
        return 30
