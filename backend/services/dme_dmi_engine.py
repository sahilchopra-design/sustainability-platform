"""
DME Dynamic Materiality Index (DMI) Engine — Velocity-weighted ESG scoring.

Extends the existing double_materiality_engine with temporal dynamics:
  - PCAF confidence → weighting (DQS 1-5 mapped to 1.0/0.85/0.70/0.55/0.40)
  - Recency decay: λ = 0.2/year (18% confidence loss per year)
  - Vertical aggregation: S = Σ(w × c × x) / Σ(w × c)
  - Concentration penalty (single-name, sector HHI, geographic HHI)
  - Portfolio-level DMI with velocity-weighted adjustments

Ported from DME (Dynamic Materiality Engine) into Risk Analytics.
"""
import numpy as np
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ── Pydantic schemas ────────────────────────────────────────────────────────

class HoldingInput(BaseModel):
    entity_id: str
    instrument_id: Optional[str] = None
    outstanding_amount: float = Field(gt=0)
    entity_evic: float = Field(gt=0, description="Enterprise Value Including Cash")
    entity_emissions_tco2e: float = Field(ge=0)
    esg_score: float = Field(ge=0, le=100)
    data_quality_score: int = Field(ge=1, le=5, description="PCAF DQS 1-5")
    recency_years: float = Field(0.0, ge=0)


class ConcentrationInput(BaseModel):
    single_name_max: float = Field(ge=0, le=1, description="Max single-name share")
    sector_hhi: float = Field(ge=0, le=1, description="Sector HHI")
    geographic_hhi: float = Field(ge=0, le=1, description="Geographic HHI")


class DMIConfig(BaseModel):
    single_name_threshold: float = Field(0.05, ge=0, le=1)
    alpha_entity: float = Field(0.20, ge=0)
    alpha_sector: float = Field(0.15, ge=0)
    alpha_geographic: float = Field(0.10, ge=0)
    velocity_weight: float = Field(0.3, ge=0, le=1, description="How much velocity adjusts base DMI")


class PCAFAttributionRequest(BaseModel):
    holdings: List[HoldingInput]


class PortfolioDMIRequest(BaseModel):
    holdings: List[HoldingInput]
    concentration: ConcentrationInput
    config: Optional[DMIConfig] = None
    velocity_adjustments: Optional[Dict[str, float]] = None  # entity_id -> velocity z-score


class EntityDMIRequest(BaseModel):
    entity_id: str
    factor_scores: List[float] = Field(description="Factor-level scores [0,1]")
    factor_weights: List[float]
    factor_confidences: List[float]
    velocity_z_scores: Optional[List[float]] = None
    config: Optional[DMIConfig] = None


# ── Engine ───────────────────────────────────────────────────────────────────

# PCAF DQS → confidence mapping
PCAF_CONFIDENCE = {1: 1.00, 2: 0.85, 3: 0.70, 4: 0.55, 5: 0.40}

DEFAULT_CONFIG = DMIConfig()


class DMIEngine:
    """Stateless Dynamic Materiality Index engine."""

    @staticmethod
    def pcaf_to_confidence(pcaf_score: int, recency_years: float = 0.0) -> float:
        """
        Base confidence from PCAF DQS, with recency decay.
        Decay: λ = 0.2/year → 18% loss/year.
        """
        base = PCAF_CONFIDENCE.get(pcaf_score, 0.70)
        return base * float(np.exp(-0.20 * recency_years))

    @staticmethod
    def confidence_weighted_agg(scores: List[float], weights: List[float], confidences: List[float]) -> float:
        """S = Σ(w × c × x) / Σ(w × c)"""
        num = sum(w * c * x for w, c, x in zip(weights, confidences, scores))
        den = sum(w * c for w, c in zip(weights, confidences))
        return num / den if den > 0 else 0.0

    @staticmethod
    def concentration_penalty(conc: ConcentrationInput, cfg: DMIConfig) -> float:
        """Multiplicative penalty from concentration metrics."""
        penalty = 1.0
        if conc.single_name_max > cfg.single_name_threshold:
            penalty *= 1.0 - cfg.alpha_entity * (conc.single_name_max - cfg.single_name_threshold)
        penalty *= 1.0 - cfg.alpha_sector * conc.sector_hhi
        penalty *= 1.0 - cfg.alpha_geographic * conc.geographic_hhi
        return max(penalty, 0.0)

    @staticmethod
    def pcaf_attribution(req: PCAFAttributionRequest) -> Dict:
        """PCAF financed emissions attribution: Σ (Outstanding/EVIC) × Emissions."""
        total_fe = 0.0
        total_out = 0.0
        quality_breakdown = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

        for h in req.holdings:
            af = h.outstanding_amount / h.entity_evic
            fe = af * h.entity_emissions_tco2e
            total_fe += fe
            total_out += h.outstanding_amount
            quality_breakdown[h.data_quality_score] += fe

        weighted_pcaf = (
            sum(s * e for s, e in quality_breakdown.items()) / total_fe
            if total_fe > 0 else 3.0
        )

        return {
            "total_financed_emissions": round(total_fe, 2),
            "total_outstanding": round(total_out, 2),
            "financed_intensity": round(total_fe / total_out, 6) if total_out > 0 else 0,
            "weighted_pcaf_score": round(weighted_pcaf, 2),
            "quality_breakdown": quality_breakdown,
            "num_holdings": len(req.holdings),
        }

    @staticmethod
    def entity_dmi(req: EntityDMIRequest) -> Dict:
        """
        Entity-level DMI: confidence-weighted factor aggregation,
        optionally adjusted by velocity z-scores.
        """
        cfg = req.config or DEFAULT_CONFIG
        n = len(req.factor_scores)
        if n != len(req.factor_weights) or n != len(req.factor_confidences):
            return {"error": "factor_scores, factor_weights, factor_confidences must have same length"}

        base_score = DMIEngine.confidence_weighted_agg(
            req.factor_scores, req.factor_weights, req.factor_confidences
        )

        # Velocity adjustment: inflate/deflate by average velocity z-score
        velocity_adj = 0.0
        if req.velocity_z_scores and len(req.velocity_z_scores) == n:
            avg_z = float(np.mean(req.velocity_z_scores))
            velocity_adj = avg_z * cfg.velocity_weight
        adjusted = base_score * (1 + velocity_adj)

        return {
            "entity_id": req.entity_id,
            "dmi_base": round(base_score, 4),
            "velocity_adjustment": round(velocity_adj, 4),
            "dmi_adjusted": round(adjusted, 4),
            "num_factors": n,
        }

    @staticmethod
    def portfolio_dmi(req: PortfolioDMIRequest) -> Dict:
        """Portfolio-level DMI with concentration penalties."""
        cfg = req.config or DEFAULT_CONFIG

        scores = [h.esg_score for h in req.holdings]
        raw_weights = [h.outstanding_amount for h in req.holdings]
        total_w = sum(raw_weights)
        norm_weights = [w / total_w for w in raw_weights]
        confidences = [DMIEngine.pcaf_to_confidence(h.data_quality_score, h.recency_years) for h in req.holdings]

        base = DMIEngine.confidence_weighted_agg(scores, norm_weights, confidences)

        # Velocity overlay (if provided)
        velocity_adj = 0.0
        if req.velocity_adjustments:
            v_scores = []
            for h in req.holdings:
                if h.entity_id in req.velocity_adjustments:
                    v_scores.append(req.velocity_adjustments[h.entity_id])
            if v_scores:
                velocity_adj = float(np.mean(v_scores)) * cfg.velocity_weight

        conc_factor = DMIEngine.concentration_penalty(req.concentration, cfg)
        final = base * (1 + velocity_adj) * conc_factor

        return {
            "portfolio_dmi_base": round(base, 4),
            "velocity_adjustment": round(velocity_adj, 4),
            "concentration_penalty": round(1.0 - conc_factor, 4),
            "portfolio_dmi_adjusted": round(final, 4),
            "weighted_avg_pcaf": round(
                sum(h.data_quality_score * h.outstanding_amount / total_w for h in req.holdings), 2
            ),
            "num_holdings": len(req.holdings),
        }

    @staticmethod
    def get_reference_data() -> Dict:
        return {
            "pcaf_confidence_map": PCAF_CONFIDENCE,
            "recency_decay": "λ = 0.2/year (18% loss/year)",
            "aggregation_formula": "S = Σ(w × c × x) / Σ(w × c)",
            "concentration_penalties": {
                "single_name": "α_entity × (share - threshold)",
                "sector_hhi": "α_sector × HHI",
                "geographic_hhi": "α_geo × HHI",
            },
        }
