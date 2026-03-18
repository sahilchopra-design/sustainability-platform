"""
DME Greenwashing Detection Engine — CUSUM-based change detection for ESG credibility.

Detects divergence between marketing sentiment and operational evidence using:
  - Credibility-weighted scoring (PCAF DQS + freshness decay)
  - EMA-smoothed divergence tracking
  - Central-difference velocity of divergence
  - CUSUM (Cumulative Sum) change-point detection
  - Three-condition compound trigger (velocity > 1σ, acceleration > 0, z-score > 2σ)

Ported from DME (Dynamic Materiality Engine) into Risk Analytics.
"""
import numpy as np
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class CredibilityWeightedScore(BaseModel):
    raw_score: float
    quality_weight: float
    freshness: float
    weighted_score: float


class GreenwashConfig(BaseModel):
    ema_alpha: float = Field(0.08, ge=0.01, le=1.0)
    cusum_k_factor: float = Field(0.5, gt=0, description="CUSUM slack = k * σ")
    cusum_h: float = Field(5.0, gt=0, description="CUSUM decision interval = h * σ")
    warning_threshold: float = Field(2.0, ge=1.0, description="Z-score for WARNING")
    critical_threshold: float = Field(3.0, ge=1.0, description="Z-score for CRITICAL")


class ScoreObservation(BaseModel):
    """One observation of (score, pcaf_quality, age_months)."""
    score: float
    pcaf_quality: int = Field(ge=1, le=5)
    age_months: float = Field(ge=0)


class GreenwashDetectRequest(BaseModel):
    entity_id: str
    marketing_observations: List[ScoreObservation]
    operational_observations: List[ScoreObservation]
    timestamps: List[datetime]
    config: Optional[GreenwashConfig] = None


class GreenwashScanRequest(BaseModel):
    """Lightweight scan for a single entity (latest snapshot)."""
    entity_id: str
    marketing_score: float
    operational_score: float
    marketing_pcaf: int = 3
    operational_pcaf: int = 2
    marketing_age_months: float = 6
    operational_age_months: float = 3


# ── Engine ───────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = GreenwashConfig()


class GreenwashingEngine:
    """Stateless greenwashing detection engine."""

    @staticmethod
    def credibility_weighted_score(
        raw_score: float,
        pcaf_score: int,
        age_months: float,
        half_life_months: float = 36.0,
    ) -> CredibilityWeightedScore:
        """
        W = RawScore × QualityWeight × Freshness
        QualityWeight = 1 - (PCAF - 1) × 0.2
        Freshness = exp(-λ × age),  λ = ln(2) / half_life
        """
        qw = max(0.0, min(1.0, 1.0 - (pcaf_score - 1) * 0.2))
        lam = np.log(2) / half_life_months
        freshness = float(np.exp(-lam * age_months))
        return CredibilityWeightedScore(
            raw_score=raw_score,
            quality_weight=qw,
            freshness=freshness,
            weighted_score=raw_score * qw * freshness,
        )

    @staticmethod
    def _ema(series: List[float], alpha: float) -> List[float]:
        if not series:
            return []
        out = [series[0]]
        for v in series[1:]:
            out.append(alpha * v + (1 - alpha) * out[-1])
        return out

    @staticmethod
    def _central_diff_velocity(ema_series: List[float]) -> List[float]:
        """v_t = (EMA_{t+1} - EMA_{t-1}) / 2"""
        if len(ema_series) < 3:
            return []
        return [(ema_series[i + 1] - ema_series[i - 1]) / 2.0 for i in range(1, len(ema_series) - 1)]

    @staticmethod
    def _cusum(series: List[float], mean: float, std: float, k_factor: float, h: float) -> Tuple[List[float], bool]:
        """
        CUSUM change-point detection.
        C_t+ = max(0, C_{t-1}+ + (D_t - μ) - k*σ)
        Alert if C_t+ > h*σ
        """
        k = k_factor * std
        h_thresh = h * std
        cusum = [0.0]
        alert = False
        for d in series:
            c = max(0.0, cusum[-1] + (d - mean) - k)
            cusum.append(c)
            if c > h_thresh:
                alert = True
        return cusum[1:], alert

    @staticmethod
    def detect(req: GreenwashDetectRequest) -> Dict:
        """
        Full detection: compare marketing vs operational over time.
        Three simultaneous conditions for trigger:
          1. V_m > 1σ  (divergence velocity exceeds historical)
          2. A_m > 0   (acceleration positive — gap widening)
          3. z-score > 2σ (WARNING) or > 3σ (CRITICAL)
        """
        cfg = req.config or DEFAULT_CONFIG
        n = min(len(req.marketing_observations), len(req.operational_observations), len(req.timestamps))
        if n < 2:
            return {"greenwashing_detected": False, "severity": "INSUFFICIENT_DATA", "error": "Need ≥ 2 observations"}

        # Credibility-weighted averages
        mw, ow = [], []
        for i in range(n):
            m = req.marketing_observations[i]
            o = req.operational_observations[i]
            mw.append(GreenwashingEngine.credibility_weighted_score(m.score, m.pcaf_quality, m.age_months).weighted_score)
            ow.append(GreenwashingEngine.credibility_weighted_score(o.score, o.pcaf_quality, o.age_months).weighted_score)

        divergence = [m - o for m, o in zip(mw, ow)]
        ema_div = GreenwashingEngine._ema(divergence, cfg.ema_alpha)
        velocity = GreenwashingEngine._central_diff_velocity(ema_div)

        if len(divergence) < 20:
            return {
                "greenwashing_detected": False,
                "severity": "INSUFFICIENT_DATA",
                "divergence_latest": divergence[-1],
                "marketing_weighted_avg": float(np.mean(mw)),
                "operational_weighted_avg": float(np.mean(ow)),
                "error": "Need ≥ 20 observations for statistical detection",
            }

        div_mean = float(np.mean(divergence))
        div_std = float(np.std(divergence, ddof=1))
        z_scores = [(d - div_mean) / div_std if div_std > 0 else 0.0 for d in divergence]

        latest_z = z_scores[-1]
        latest_v = velocity[-1] if velocity else 0.0
        accel = (velocity[-1] - velocity[-2]) if len(velocity) >= 2 else 0.0

        v_exceeds = False
        if len(velocity) >= 20:
            vm = float(np.mean(velocity))
            vs = float(np.std(velocity, ddof=1))
            v_exceeds = abs(latest_v - vm) > vs

        c1 = v_exceeds
        c2 = accel > 0
        c3_warn = latest_z > cfg.warning_threshold
        c3_crit = latest_z > cfg.critical_threshold

        detected = c1 and c2 and c3_warn
        severity = "CRITICAL" if (c1 and c2 and c3_crit) else "WARNING" if detected else "NONE"

        cusum_vals, cusum_alert = GreenwashingEngine._cusum(divergence, div_mean, div_std, cfg.cusum_k_factor, cfg.cusum_h)

        return {
            "greenwashing_detected": detected,
            "severity": severity,
            "divergence_latest": divergence[-1],
            "divergence_z_score": latest_z,
            "velocity_latest": latest_v,
            "acceleration_latest": accel,
            "condition_velocity_exceeds_1sigma": c1,
            "condition_acceleration_positive": c2,
            "condition_z_score_exceeds_threshold": c3_warn,
            "cusum_alert": cusum_alert,
            "marketing_weighted_avg": float(np.mean(mw)),
            "operational_weighted_avg": float(np.mean(ow)),
            "observations_used": n,
        }

    @staticmethod
    def quick_scan(req: GreenwashScanRequest) -> Dict:
        """Lightweight single-point credibility gap scan."""
        m = GreenwashingEngine.credibility_weighted_score(req.marketing_score, req.marketing_pcaf, req.marketing_age_months)
        o = GreenwashingEngine.credibility_weighted_score(req.operational_score, req.operational_pcaf, req.operational_age_months)
        gap = m.weighted_score - o.weighted_score
        gap_pct = (gap / o.weighted_score * 100) if o.weighted_score != 0 else 0.0
        risk = "HIGH" if gap_pct > 30 else "MEDIUM" if gap_pct > 15 else "LOW"
        return {
            "entity_id": req.entity_id,
            "marketing_weighted": m.weighted_score,
            "operational_weighted": o.weighted_score,
            "credibility_gap": gap,
            "credibility_gap_pct": round(gap_pct, 2),
            "risk_level": risk,
            "marketing_detail": m.model_dump(),
            "operational_detail": o.model_dump(),
        }
