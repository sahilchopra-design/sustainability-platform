"""
DME NLP Pulse Score Engine — Sentiment-based signal processing.

Implements:
  - Pulse score: P(t) = S(t) × ln(1 + I(t))
  - Greenwashing Discount Factor (GDF) for self-reported positive signals
  - Signal decay by event type (breaking news → corporate disclosure)
  - Source credibility tiering (Tier 1 institutional → Tier 4 social)
  - Aggregate pulse with credibility-weighted EMA

Ported from DME (Dynamic Materiality Engine) into Risk Analytics.
"""
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ── Enums & Constants ────────────────────────────────────────────────────────

class EventType(str, Enum):
    BREAKING_NEWS = "breaking_news"
    REGULATORY_ENFORCEMENT = "regulatory_enforcement"
    INVESTIGATIVE_JOURNALISM = "investigative_journalism"
    INDUSTRY_POLICY_SHIFT = "industry_policy_shift"
    CORPORATE_DISCLOSURE = "corporate_disclosure"


class SourceTier(int, Enum):
    TIER1_INSTITUTIONAL = 1   # Bloomberg, Reuters, SEC
    TIER2_SPECIALIST = 2      # FT, NGO, IEEE
    TIER3_BROAD_MEDIA = 3     # General news
    TIER4_SOCIAL = 4          # Twitter, Reddit, Glassdoor


DECAY_HALF_LIVES_HOURS = {
    EventType.BREAKING_NEWS: 12.0,
    EventType.REGULATORY_ENFORCEMENT: 168.0,   # 7 days
    EventType.INVESTIGATIVE_JOURNALISM: 336.0,  # 14 days
    EventType.INDUSTRY_POLICY_SHIFT: 2160.0,    # 90 days
    EventType.CORPORATE_DISCLOSURE: 4320.0,     # 180 days
}

SOURCE_CREDIBILITY = {
    SourceTier.TIER1_INSTITUTIONAL: 0.95,
    SourceTier.TIER2_SPECIALIST: 0.70,
    SourceTier.TIER3_BROAD_MEDIA: 0.40,
    SourceTier.TIER4_SOCIAL: 0.15,
}


# ── Pydantic schemas ────────────────────────────────────────────────────────

class SentimentSignal(BaseModel):
    entity_id: str
    timestamp: datetime
    sentiment_score: float = Field(ge=-100, le=100)
    information_density: float = Field(ge=0)
    source_tier: int = Field(ge=1, le=4)
    event_type: EventType
    is_self_reported: bool = False


class NLPPulseConfig(BaseModel):
    greenwashing_kappa: float = Field(0.5, ge=0.0, le=1.0, description="GDF κ parameter")
    ema_alpha: float = Field(0.25, ge=0.01, le=1.0)


class ProcessSignalRequest(BaseModel):
    signal: SentimentSignal
    s_marketing: float = 0.0
    s_operational: float = 0.0
    config: Optional[NLPPulseConfig] = None


class ProcessBatchRequest(BaseModel):
    entity_id: str
    signals: List[SentimentSignal]
    config: Optional[NLPPulseConfig] = None


class DecayRequest(BaseModel):
    initial_value: float
    event_type: EventType
    elapsed_hours: float = Field(ge=0)


# ── Engine ───────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = NLPPulseConfig()


class NLPPulseEngine:
    """Stateless NLP pulse score engine."""

    @staticmethod
    def pulse_score(sentiment: float, information_density: float) -> float:
        """P(t) = S(t) × ln(1 + I(t))"""
        return sentiment * float(np.log(1 + information_density))

    @staticmethod
    def greenwashing_discount(
        pulse: float,
        s_marketing: float,
        s_operational: float,
        kappa: float,
    ) -> tuple[float, float]:
        """
        GDF = max(0, 1 - κ × max(0, S_marketing - S_operational) / 100)
        Returns (discounted_pulse, gdf).
        Applied ONLY to positive self-reported signals.
        """
        gap = max(0.0, s_marketing - s_operational)
        gdf = max(0.0, 1.0 - kappa * gap / 100.0)
        return pulse * gdf, gdf

    @staticmethod
    def decay_lambda(event_type: EventType) -> float:
        """λ = ln(2) / (half_life_hours / 24)"""
        hl = DECAY_HALF_LIVES_HOURS[event_type]
        return float(np.log(2) / (hl / 24.0))

    @staticmethod
    def apply_decay(initial_value: float, event_type: EventType, elapsed_hours: float) -> float:
        """S(t) = S₀ × exp(−λ × t_days)"""
        lam = NLPPulseEngine.decay_lambda(event_type)
        return initial_value * float(np.exp(-lam * elapsed_hours / 24.0))

    @staticmethod
    def source_credibility(tier: int) -> float:
        try:
            return SOURCE_CREDIBILITY[SourceTier(tier)]
        except (ValueError, KeyError):
            return 0.5

    @staticmethod
    def process_signal(req: ProcessSignalRequest) -> Dict:
        """Full pipeline for one sentiment signal."""
        cfg = req.config or DEFAULT_CONFIG
        sig = req.signal

        # Stage 1: raw pulse
        pulse_raw = NLPPulseEngine.pulse_score(sig.sentiment_score, sig.information_density)

        # Stage 2: greenwashing discount (if self-reported + positive)
        pulse_disc = pulse_raw
        gdf = 1.0
        if sig.is_self_reported and pulse_raw > 0:
            pulse_disc, gdf = NLPPulseEngine.greenwashing_discount(
                pulse_raw, req.s_marketing, req.s_operational, cfg.greenwashing_kappa
            )

        # Stage 3: decay parameters
        lam = NLPPulseEngine.decay_lambda(sig.event_type)
        hl = DECAY_HALF_LIVES_HOURS[sig.event_type]

        # Stage 4: credibility
        cred = NLPPulseEngine.source_credibility(sig.source_tier)

        return {
            "entity_id": sig.entity_id,
            "timestamp": sig.timestamp.isoformat(),
            "pulse_raw": round(pulse_raw, 4),
            "pulse_discounted": round(pulse_disc, 4),
            "greenwash_discount_factor": round(gdf, 4),
            "source_credibility": cred,
            "credibility_adjusted_pulse": round(pulse_disc * cred, 4),
            "decay_lambda_per_day": round(lam, 6),
            "decay_half_life_hours": hl,
            "event_type": sig.event_type.value,
            "sentiment_score": sig.sentiment_score,
            "information_density": sig.information_density,
        }

    @staticmethod
    def process_batch(req: ProcessBatchRequest) -> Dict:
        """Process batch of signals and compute aggregate pulse."""
        cfg = req.config or DEFAULT_CONFIG
        results = []
        now = req.signals[-1].timestamp if req.signals else datetime.utcnow()

        for sig in sorted(req.signals, key=lambda s: s.timestamp):
            single = ProcessSignalRequest(signal=sig, config=cfg)
            processed = NLPPulseEngine.process_signal(single)

            # Apply time decay from signal time to latest
            elapsed = (now - sig.timestamp).total_seconds() / 3600.0
            decayed = NLPPulseEngine.apply_decay(processed["credibility_adjusted_pulse"], sig.event_type, elapsed)
            processed["decayed_pulse"] = round(decayed, 4)
            results.append(processed)

        # Aggregate
        decayed_values = [r["decayed_pulse"] for r in results]
        pos = sum(1 for v in decayed_values if v > 0)
        neg = sum(1 for v in decayed_values if v < 0)
        avg_cred = np.mean([r["source_credibility"] for r in results]) if results else 0.0

        return {
            "entity_id": req.entity_id,
            "aggregate_pulse": round(sum(decayed_values), 4),
            "signal_count": len(results),
            "positive_signals": pos,
            "negative_signals": neg,
            "avg_credibility": round(float(avg_cred), 4),
            "signals": results,
        }

    @staticmethod
    def get_reference_data() -> Dict:
        """Return reference tables for event types, source tiers, decay rates."""
        return {
            "event_types": [
                {"type": et.value, "half_life_hours": DECAY_HALF_LIVES_HOURS[et]}
                for et in EventType
            ],
            "source_tiers": [
                {"tier": st.value, "name": st.name, "credibility": SOURCE_CREDIBILITY[st]}
                for st in SourceTier
            ],
        }
