"""
DME Alert Engine — Four-Tier Velocity Alert Framework.

Tiers: WATCH (1.5σ) → ELEVATED (2.0σ) → CRITICAL (3.0σ) → EXTREME (4.0σ)
Compound condition: V > k·σ AND A > 0 (acceleration positive)
Priority scoring: 30% velocity + 20% acceleration + 30% exposure + 20% sensitivity
Priority bands: LOW (0-25), MEDIUM (26-50), HIGH (51-75), CRITICAL (76-100)
Suppression windows: WATCH 48h, ELEVATED 24h, CRITICAL 4h, EXTREME 0h
SLA: LOW 72h, MEDIUM 24h, HIGH 4h, CRITICAL immediate

Ported from DME (Dynamic Materiality Engine) into Risk Analytics.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid


# ── Pydantic schemas ────────────────────────────────────────────────────────

class AlertThresholds(BaseModel):
    watch: float = 1.5
    elevated: float = 2.0
    critical: float = 3.0
    extreme: float = 4.0
    threshold_type: str = "z_score"


class AlertRuleConfig(BaseModel):
    metric_key: str
    factor_id: Optional[str] = None
    thresholds: AlertThresholds = AlertThresholds()
    suppression_hours_watch: int = 48
    suppression_hours_elevated: int = 24
    suppression_hours_critical: int = 4
    suppression_hours_extreme: int = 0


class VelocitySignalInput(BaseModel):
    entity_id: str
    factor_id: str
    pillar: str = "E"  # E/S/G/X
    velocity: float
    z_velocity: float
    acceleration: Optional[float] = None
    z_acceleration: float = 0.0
    exposure_share: float = Field(0.0, ge=0, le=1)
    sensitivity_alpha: float = Field(0.1, ge=0)
    timestamp: datetime


class AlertRecord(BaseModel):
    alert_id: str
    entity_id: str
    factor_id: str
    pillar: str
    velocity_raw: float
    velocity_z_score: float
    acceleration: Optional[float]
    alert_tier: str
    trigger_type: str  # Z_SCORE / COMPOUND
    priority_score: int
    priority_band: str
    triggered_at: datetime
    response_sla_hours: int
    factor_override_applied: bool = False
    contagion_active: bool = False
    pd_adjustment: Optional[float] = None
    var_adjustment: Optional[float] = None


class ProcessSignalsRequest(BaseModel):
    signals: List[VelocitySignalInput]
    rules: Optional[Dict[str, AlertRuleConfig]] = None


class AlertSummaryRequest(BaseModel):
    entity_id: Optional[str] = None
    tier_filter: Optional[str] = None
    since: Optional[datetime] = None


# ── Engine ───────────────────────────────────────────────────────────────────

DEFAULT_THRESHOLDS = AlertThresholds()

SLA_HOURS = {"LOW": 72, "MEDIUM": 24, "HIGH": 4, "CRITICAL": 0}

SUPPRESSION_HOURS = {"WATCH": 48, "ELEVATED": 24, "CRITICAL": 4, "EXTREME": 0}


class AlertEngine:
    """
    Stateless alert processing engine.
    Suppression state is managed externally (DB) — this engine is pure logic.
    """

    @staticmethod
    def classify_tier(
        z_score: float,
        acceleration: Optional[float],
        thresholds: AlertThresholds,
    ) -> Optional[str]:
        """Compound condition: V > k·σ AND A > 0."""
        if acceleration is not None and acceleration <= 0:
            return None
        abs_z = abs(z_score)
        if abs_z >= thresholds.extreme:
            return "EXTREME"
        if abs_z >= thresholds.critical:
            return "CRITICAL"
        if abs_z >= thresholds.elevated:
            return "ELEVATED"
        if abs_z >= thresholds.watch:
            return "WATCH"
        return None

    @staticmethod
    def priority_score(
        z_velocity: float,
        z_acceleration: float,
        exposure_share: float,
        sensitivity_alpha: float,
        max_z_v: float = 4.0,
        max_z_a: float = 3.0,
    ) -> int:
        """PS = 0.30×norm(Z_V) + 0.20×norm(Z_A) + 0.30×norm(Exposure) + 0.20×norm(Sensitivity)"""
        v_norm = min(abs(z_velocity), max_z_v) / max_z_v * 100
        a_norm = min(abs(z_acceleration), max_z_a) / max_z_a * 100
        e_norm = exposure_share * 100
        s_norm = min(sensitivity_alpha, 0.30) / 0.30 * 100
        return int(round(0.30 * v_norm + 0.20 * a_norm + 0.30 * e_norm + 0.20 * s_norm))

    @staticmethod
    def priority_band(score: int) -> str:
        if score <= 25:
            return "LOW"
        if score <= 50:
            return "MEDIUM"
        if score <= 75:
            return "HIGH"
        return "CRITICAL"

    @staticmethod
    def process_signal(
        sig: VelocitySignalInput,
        rules: Optional[Dict[str, AlertRuleConfig]] = None,
    ) -> Optional[AlertRecord]:
        """Process one velocity signal, return AlertRecord or None."""
        rule = (rules or {}).get(sig.factor_id)
        thresholds = rule.thresholds if rule else DEFAULT_THRESHOLDS
        override = rule is not None

        tier = AlertEngine.classify_tier(sig.z_velocity, sig.acceleration, thresholds)
        if tier is None:
            return None

        ps = AlertEngine.priority_score(
            sig.z_velocity, sig.z_acceleration, sig.exposure_share, sig.sensitivity_alpha
        )
        band = AlertEngine.priority_band(ps)
        sla = SLA_HOURS.get(band, 24)

        return AlertRecord(
            alert_id=f"DME-{sig.timestamp.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            entity_id=sig.entity_id,
            factor_id=sig.factor_id,
            pillar=sig.pillar,
            velocity_raw=sig.velocity,
            velocity_z_score=sig.z_velocity,
            acceleration=sig.acceleration,
            alert_tier=tier,
            trigger_type="COMPOUND" if (sig.acceleration and sig.acceleration > 0) else "Z_SCORE",
            priority_score=ps,
            priority_band=band,
            triggered_at=sig.timestamp,
            response_sla_hours=sla,
            factor_override_applied=override,
        )

    @staticmethod
    def process_batch(req: ProcessSignalsRequest) -> Dict:
        """Process multiple signals, return alerts grouped by tier."""
        alerts = []
        for sig in req.signals:
            record = AlertEngine.process_signal(sig, req.rules)
            if record:
                alerts.append(record)

        tier_counts = {"WATCH": 0, "ELEVATED": 0, "CRITICAL": 0, "EXTREME": 0}
        for a in alerts:
            tier_counts[a.alert_tier] = tier_counts.get(a.alert_tier, 0) + 1

        return {
            "total_signals": len(req.signals),
            "alerts_generated": len(alerts),
            "tier_breakdown": tier_counts,
            "alerts": [a.model_dump() for a in alerts],
        }

    @staticmethod
    def get_reference_data() -> Dict:
        return {
            "tier_thresholds": DEFAULT_THRESHOLDS.model_dump(),
            "priority_bands": {"LOW": "0-25", "MEDIUM": "26-50", "HIGH": "51-75", "CRITICAL": "76-100"},
            "sla_hours": SLA_HOURS,
            "suppression_hours": SUPPRESSION_HOURS,
            "priority_formula": "PS = 0.30×norm(Z_V) + 0.20×norm(Z_A) + 0.30×norm(Exposure) + 0.20×norm(Sensitivity)",
            "compound_condition": "V > k·σ AND A(t) > 0",
        }
