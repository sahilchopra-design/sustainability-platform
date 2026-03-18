"""
DME Velocity Engine — EWMA-based rate-of-change monitoring for ESG metrics.

Ported from DME (Dynamic Materiality Engine) into Risk Analytics.
Six-stage processing pipeline:
  1. Raw materiality series M(t) enters
  2. Canonical discrete velocity V(t) = [M(t) - M(t-dt)] / dt
  3. Optional EWMA smoothing: EWMA(t) = alpha * V(t) + (1-alpha) * EWMA(t-1)
  4. Percentage velocity V%(t) = [M(t) - M(t-1)] / M(t-1)
  5. Z-score normalisation against rolling window
  6. Regime classification (NORMAL / ELEVATED / CRITICAL / EXTREME)

Reference: FRS Section 3.1 — Velocity & Alert Compound Conditions.
"""
import numpy as np
from typing import List, Dict, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class RawMetricPoint(BaseModel):
    """Raw metric data point."""
    timestamp: datetime
    value: float


class VelocityOutput(BaseModel):
    """Output of one stage-6 velocity computation."""
    timestamp: datetime
    raw_value: float
    velocity_raw: float
    velocity_pct: float
    velocity_smoothed: Optional[float] = None
    acceleration: Optional[float] = None
    z_score: Optional[float] = None
    regime: Literal["NORMAL", "ELEVATED", "CRITICAL", "EXTREME"] = "NORMAL"
    sigma_level_classification: str = "0.0sigma"
    smoothing_applied: Optional[str] = None


class VelocityConfig(BaseModel):
    """Configuration for a single metric's velocity pipeline."""
    metric_key: str
    ewma_alpha: float = Field(0.2, ge=0.01, le=1.0)
    lookback_days: int = Field(252, ge=10)
    z_threshold_elevated: float = 1.0
    z_threshold_critical: float = 2.0
    z_threshold_extreme: float = 3.0
    delta_t: float = Field(1.0, gt=0)


class VelocitySeriesRequest(BaseModel):
    """Request to process a full metric series."""
    entity_id: str
    metric_key: str
    data_points: List[RawMetricPoint]
    config: Optional[VelocityConfig] = None
    apply_smoothing: bool = True


class VelocitySingleRequest(BaseModel):
    """Request to process a single new observation (real-time mode)."""
    entity_id: str
    metric_key: str
    current_value: float
    previous_value: float
    timestamp: datetime
    historical_velocities: List[float] = Field(default_factory=list)
    config: Optional[VelocityConfig] = None


# ── Pure math helpers ────────────────────────────────────────────────────────

def _canonical_velocity(m_current: float, m_previous: float, delta_t: float = 1.0) -> float:
    """V(t) = [M(t) - M(t-dt)] / dt"""
    return (m_current - m_previous) / delta_t


def _percentage_velocity(m_current: float, m_previous: float) -> float:
    """V%(t) = [M(t) - M(t-1)] / M(t-1)"""
    if m_previous == 0:
        return 0.0
    return (m_current - m_previous) / m_previous


def _z_score(v_current: float, v_mean: float, v_std: float) -> float:
    if v_std == 0:
        return 0.0
    return (v_current - v_mean) / v_std


def _canonical_acceleration(m_current: float, m_prev: float, m_prev2: float, delta_t: float = 1.0) -> float:
    """A(t) = [M(t) - 2*M(t-1) + M(t-2)] / dt^2"""
    return (m_current - 2 * m_prev + m_prev2) / (delta_t ** 2)


def _ewma(values: List[float], alpha: float) -> List[float]:
    """Exponentially Weighted Moving Average."""
    if not values:
        return []
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


# ── Engine class ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG = VelocityConfig(metric_key="default")


class VelocityEngine:
    """
    Core velocity calculation engine.
    Stateless — all state comes through request params.
    """

    @staticmethod
    def classify_regime(z: float, cfg: VelocityConfig) -> str:
        abs_z = abs(z)
        if abs_z >= cfg.z_threshold_extreme:
            return "EXTREME"
        elif abs_z >= cfg.z_threshold_critical:
            return "CRITICAL"
        elif abs_z >= cfg.z_threshold_elevated:
            return "ELEVATED"
        return "NORMAL"

    @staticmethod
    def process_series(req: VelocitySeriesRequest) -> List[VelocityOutput]:
        """Process a full metric time series through the 6-stage pipeline."""
        cfg = req.config or DEFAULT_CONFIG
        pts = sorted(req.data_points, key=lambda p: p.timestamp)
        if len(pts) < 2:
            return []

        raw = [p.value for p in pts]
        ts = [p.timestamp for p in pts]
        dt = cfg.delta_t

        # Stage 2: canonical velocity
        velocities = [_canonical_velocity(raw[i], raw[i - 1], dt) for i in range(1, len(raw))]

        # Stage 3: optional EWMA smoothing
        smoothed = _ewma(velocities, cfg.ewma_alpha) if (req.apply_smoothing and len(velocities) >= 3) else None
        smoothing_label = f"EWMA(alpha={cfg.ewma_alpha})" if smoothed else None

        # Stage 4: percentage velocity
        pct_vel = [_percentage_velocity(raw[i], raw[i - 1]) for i in range(1, len(raw))]

        # Stage 5: z-score
        min_obs = 20
        if len(velocities) >= min_obs:
            v_mean = float(np.mean(velocities))
            v_std = float(np.std(velocities, ddof=1))
            z_scores = [_z_score(v, v_mean, v_std) for v in velocities]
        else:
            z_scores = [0.0] * len(velocities)

        # Stage 6: acceleration
        accels: List[Optional[float]] = [None]  # no accel for first velocity point
        for i in range(2, len(raw)):
            accels.append(_canonical_acceleration(raw[i], raw[i - 1], raw[i - 2], dt))

        # Build outputs
        outputs = []
        for i in range(len(velocities)):
            z = z_scores[i]
            outputs.append(VelocityOutput(
                timestamp=ts[i + 1],
                raw_value=raw[i + 1],
                velocity_raw=velocities[i],
                velocity_pct=pct_vel[i],
                velocity_smoothed=smoothed[i] if smoothed else None,
                acceleration=accels[i],
                z_score=z,
                regime=VelocityEngine.classify_regime(z, cfg),
                sigma_level_classification=f"{abs(z):.1f}sigma",
                smoothing_applied=smoothing_label,
            ))
        return outputs

    @staticmethod
    def process_single(req: VelocitySingleRequest) -> VelocityOutput:
        """Process a single new observation (real-time mode)."""
        cfg = req.config or DEFAULT_CONFIG
        v_raw = _canonical_velocity(req.current_value, req.previous_value, cfg.delta_t)
        v_pct = _percentage_velocity(req.current_value, req.previous_value)

        z = 0.0
        if len(req.historical_velocities) >= 20:
            v_mean = float(np.mean(req.historical_velocities))
            v_std = float(np.std(req.historical_velocities, ddof=1))
            z = _z_score(v_raw, v_mean, v_std)

        regime = VelocityEngine.classify_regime(z, cfg)
        return VelocityOutput(
            timestamp=req.timestamp,
            raw_value=req.current_value,
            velocity_raw=v_raw,
            velocity_pct=v_pct,
            z_score=z,
            regime=regime,
            sigma_level_classification=f"{abs(z):.1f}sigma",
        )

    @staticmethod
    def classify_alert_level(
        velocity: float,
        acceleration: float,
        z_score: float,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Optional[str]:
        """
        FRS Section 3.1 compound condition: V > k*sigma AND A > 0.
        Returns tier string or None.
        """
        t = thresholds or {"watch": 1.5, "elevated": 2.0, "critical": 3.0, "extreme": 4.0}
        if acceleration <= 0:
            return None
        abs_z = abs(z_score)
        if abs_z >= t["extreme"]:
            return "EXTREME"
        if abs_z >= t["critical"]:
            return "CRITICAL"
        if abs_z >= t["elevated"]:
            return "ELEVATED"
        if abs_z >= t["watch"]:
            return "WATCH"
        return None

    @staticmethod
    def get_regime_summary(outputs: List[VelocityOutput]) -> Dict:
        """Summarise regime distribution across a series."""
        counts = {"NORMAL": 0, "ELEVATED": 0, "CRITICAL": 0, "EXTREME": 0}
        for o in outputs:
            counts[o.regime] = counts.get(o.regime, 0) + 1
        total = len(outputs) or 1
        return {
            "total_observations": len(outputs),
            "regime_counts": counts,
            "regime_pct": {k: round(v / total * 100, 1) for k, v in counts.items()},
            "latest_regime": outputs[-1].regime if outputs else None,
            "latest_z_score": outputs[-1].z_score if outputs else None,
        }
