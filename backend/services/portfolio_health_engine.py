"""
Portfolio Health Engine — Three-Score Sustainability Pulse

Computes three actionable health scores (0–100) for a portfolio on each data refresh:

  Climate Health Score      How well is WACI tracking vs. the NZBA glidepath?
                            100 = on or below glidepath across all sectors
                            0   = 50%+ above glidepath

  Financial Resilience Score  How exposed is the book to credit deterioration?
                            100 = no SICR triggers, all DSCR > 1.35
                            0   = >20% AUM in Stage 2/3 ECL or DSCR breach

  Transition Readiness Score  How prepared are counterparties for net-zero?
                            100 = all large exposures SBTi-aligned with validated plans
                            0   = <10% AUM with any form of transition commitment

Design principle (WHOOP analogy):
  These scores are displayed prominently on the Sustainability Pulse dashboard.
  They update whenever new PCAF, ECL, or glidepath data is written.
  Each score drives a specific "what to do" action link.

Graceful degrade: if DB is unavailable, returns null scores with data_available=False.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


# ── Score dataclasses ──────────────────────────────────────────────────────────

@dataclass
class HealthScore:
    value: float                  # 0–100
    rag: str                      # GREEN | AMBER | RED
    label: str                    # human-readable one-liner
    action: str                   # actionable text: "Review glidepath deviations"
    action_link: str              # frontend route


@dataclass
class PortfolioHealthScores:
    portfolio_id: str
    portfolio_name: str
    climate_health: HealthScore
    financial_resilience: HealthScore
    transition_readiness: HealthScore
    overall_score: float          # simple average of the three
    alert_count: int
    data_available: bool
    last_updated: str             # ISO 8601


# ── RAG helpers ────────────────────────────────────────────────────────────────

def _rag(value: float) -> str:
    if value >= 70:
        return "GREEN"
    elif value >= 40:
        return "AMBER"
    else:
        return "RED"


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _get_engine():
    try:
        from db.base import engine as _engine
        return _engine
    except Exception:
        return None


def _exec(engine, query: str, params: dict):
    try:
        with engine.connect() as conn:
            return conn.execute(text(query), params).fetchall()
    except Exception as exc:
        logger.warning("[HealthEngine] query failed: %s", exc)
        return []


def _scalar(engine, query: str, params: dict):
    try:
        with engine.connect() as conn:
            return conn.execute(text(query), params).scalar()
    except Exception:
        return None


# ── Score 1: Climate Health ───────────────────────────────────────────────────

def _compute_climate_health(engine, portfolio_id: str) -> HealthScore:
    """
    Compare actual WACI per sector (from pcaf_time_series) against glidepath_value.
    Score = 100 - average_glidepath_deviation_pct (capped at 0–100).
    If no time-series data exists, return neutral 50 with data_available note.
    """
    rows = _exec(
        engine,
        """
        SELECT sector,
               actual_value,
               glidepath_value,
               reporting_year
        FROM pcaf_time_series
        WHERE portfolio_id = :pid
          AND metric_type   = 'waci'
          AND glidepath_value IS NOT NULL
          AND actual_value IS NOT NULL
          AND reporting_year = (
              SELECT MAX(reporting_year)
              FROM pcaf_time_series
              WHERE portfolio_id = :pid AND metric_type = 'waci'
          )
        """,
        {"pid": portfolio_id},
    )

    if not rows:
        return HealthScore(
            value=50.0,
            rag="AMBER",
            label="No WACI data available — run PCAF calculation",
            action="Run PCAF calculation to populate climate health score",
            action_link="/portfolio-analytics",
        )

    deviations = []
    for r in rows:
        if r.glidepath_value and r.glidepath_value > 0:
            dev = (float(r.actual_value) - float(r.glidepath_value)) / float(r.glidepath_value)
            deviations.append(max(dev, 0.0))  # only penalise above-glidepath

    if not deviations:
        return HealthScore(value=60.0, rag="AMBER", label="Glidepath reference unavailable", action="Connect Data Hub for sector glidepaths", action_link="/data-hub")

    avg_dev = sum(deviations) / len(deviations)
    # Map deviation → score: 0% dev = 100, 50% dev = 0
    score = _clamp(100.0 - (avg_dev / 0.50) * 100.0)

    worst_sector = max(zip(deviations, [r.sector for r in rows]), key=lambda x: x[0])

    if score >= 70:
        label = f"Portfolio WACI on track — within {avg_dev:.0%} of glidepath"
        action = "Maintain engagement with transition-lagging counterparties"
    elif score >= 40:
        label = f"WACI {avg_dev:.0%} above NZBA glidepath — action required"
        action = f"Review {worst_sector[1]} sector — largest glidepath deviation"
    else:
        label = f"WACI severely off-track ({avg_dev:.0%} above glidepath)"
        action = f"Immediate review needed: {worst_sector[1]} sector"

    return HealthScore(
        value=round(score, 1),
        rag=_rag(score),
        label=label,
        action=action,
        action_link="/glidepath-tracker",
    )


# ── Score 2: Financial Resilience ─────────────────────────────────────────────

def _compute_financial_resilience(engine, portfolio_id: str) -> HealthScore:
    """
    Estimates credit health from two signals:
      1. ECL stage distribution (% AUM in Stage 1 / 2 / 3 from ecl_exposures table)
      2. DSCR minimum (from project_finance_assessments table if available)
    Score degrades based on Stage 2/3 exposure fraction and DSCR breaches.
    """
    # ECL stage distribution
    stage_rows = _exec(
        engine,
        """
        SELECT stage_assigned, SUM(exposure_value) AS exposure_sum
        FROM ecl_exposures
        WHERE portfolio_id = :pid
        GROUP BY stage_assigned
        """,
        {"pid": portfolio_id},
    )

    total_ecl_exposure = sum(float(r.exposure_sum or 0) for r in stage_rows)
    stage2_3_exposure = sum(
        float(r.exposure_sum or 0)
        for r in stage_rows
        if r.stage_assigned in ("STAGE_2", "STAGE_3")
    )

    stage_fraction = (stage2_3_exposure / total_ecl_exposure) if total_ecl_exposure > 0 else 0.0

    # DSCR signal (optional — table may not exist yet)
    min_dscr = _scalar(
        engine,
        """
        SELECT MIN(min_dscr) FROM project_finance_assessments
        WHERE portfolio_id = :pid
        """,
        {"pid": portfolio_id},
    )

    # Score from ECL: 0% stage2/3 = 100, 20%+ stage2/3 = 0
    ecl_score = _clamp(100.0 - (stage_fraction / 0.20) * 100.0)

    # Score from DSCR: ≥ 1.40 = 100, ≤ 1.25 = 0
    if min_dscr is not None:
        dscr_score = _clamp((float(min_dscr) - 1.25) / (1.40 - 1.25) * 100.0)
    else:
        dscr_score = 75.0  # neutral if no project finance data

    # Combined: weight ECL 60%, DSCR 40%
    score = 0.6 * ecl_score + 0.4 * dscr_score

    if total_ecl_exposure == 0 and min_dscr is None:
        return HealthScore(
            value=50.0,
            rag="AMBER",
            label="No ECL or DSCR data — run financial risk assessment",
            action="Run ECL Climate assessment to populate resilience score",
            action_link="/financial-risk",
        )

    if score >= 70:
        label = f"Strong financial resilience — {stage_fraction:.1%} AUM in Stage 2/3"
        action = "Monitor Stage 2 watch-list and upcoming maturity schedule"
    elif score >= 40:
        label = f"Resilience moderate — {stage_fraction:.1%} AUM may migrate to Stage 2"
        action = "Review SICR triggers and increase ECL provisioning headroom"
    else:
        label = f"Financial resilience at risk — {stage_fraction:.1%} AUM Stage 2/3"
        action = "Immediate review: high Stage 2/3 exposure requires provisions"

    return HealthScore(
        value=round(score, 1),
        rag=_rag(score),
        label=label,
        action=action,
        action_link="/financial-risk",
    )


# ── Score 3: Transition Readiness ─────────────────────────────────────────────

def _compute_transition_readiness(engine, portfolio_id: str) -> HealthScore:
    """
    Measures how prepared counterparties are for net-zero:
      - % AUM with SBTi-aligned targets
      - % AUM with validated/on-track transition plans
      - PCAF DQS coverage (proxy for data availability to track)

    Score = weighted average: SBTi 40%, transition plan 40%, DQS ≤ 3 20%
    """
    # SBTi + transition plan from assets_pg
    asset_rows = _exec(
        engine,
        """
        SELECT exposure,
               sbti_aligned,
               transition_plan_status,
               pcaf_dqs
        FROM assets_pg
        WHERE portfolio_id = :pid
        """,
        {"pid": portfolio_id},
    )

    if not asset_rows:
        return HealthScore(
            value=50.0,
            rag="AMBER",
            label="No asset transition data — add counterparty details",
            action="Update SBTi and transition plan status for portfolio assets",
            action_link="/portfolio-analytics",
        )

    total_exposure = sum(float(r.exposure or 0) for r in asset_rows)
    if total_exposure <= 0:
        total_exposure = 1.0  # prevent division by zero

    sbti_exposure = sum(
        float(r.exposure or 0)
        for r in asset_rows
        if r.sbti_aligned
    )
    plan_exposure = sum(
        float(r.exposure or 0)
        for r in asset_rows
        if r.transition_plan_status in ("plan_received", "validated", "on_track")
    )
    good_dqs_exposure = sum(
        float(r.exposure or 0)
        for r in asset_rows
        if r.pcaf_dqs is not None and int(r.pcaf_dqs) <= 3
    )

    sbti_pct = sbti_exposure / total_exposure
    plan_pct = plan_exposure / total_exposure
    dqs_pct = good_dqs_exposure / total_exposure

    score = _clamp(
        sbti_pct * 40.0 +
        plan_pct * 40.0 +
        dqs_pct * 20.0
    )

    if score >= 70:
        label = f"Strong readiness — {sbti_pct:.0%} AUM SBTi-aligned, {plan_pct:.0%} with plans"
        action = "Focus on remaining {:.0%} of AUM without transition plans".format(1 - plan_pct)
    elif score >= 40:
        label = f"Readiness developing — {sbti_pct:.0%} AUM SBTi-aligned"
        action = "Engage top emitters without plans — NZBA engagement obligation"
    else:
        label = f"Low readiness — only {sbti_pct:.0%} AUM SBTi-aligned"
        action = "Prioritise SBTi engagement across portfolio — urgent NZBA requirement"

    return HealthScore(
        value=round(score, 1),
        rag=_rag(score),
        label=label,
        action=action,
        action_link="/regulatory",
    )


# ── Main public function ───────────────────────────────────────────────────────

def compute_portfolio_health(portfolio_id: str) -> PortfolioHealthScores:
    """
    Compute all three health scores for a portfolio.
    Safe to call at any time — returns neutral AMBER scores if data is unavailable.
    """
    engine = _get_engine()

    # Fetch portfolio name
    portfolio_name = portfolio_id[:8] + "…"
    if engine is not None:
        try:
            with engine.connect() as conn:
                name_row = conn.execute(
                    text("SELECT name FROM portfolios_pg WHERE id = :pid"),
                    {"pid": portfolio_id},
                ).fetchone()
            if name_row:
                portfolio_name = name_row.name
        except Exception:
            pass

    # Alert count
    from services.alert_engine import get_unread_count
    alert_count = get_unread_count(portfolio_id)

    if engine is None:
        neutral = HealthScore(
            value=50.0,
            rag="AMBER",
            label="Database unavailable",
            action="Check backend connectivity",
            action_link="/",
        )
        return PortfolioHealthScores(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            climate_health=neutral,
            financial_resilience=neutral,
            transition_readiness=neutral,
            overall_score=50.0,
            alert_count=0,
            data_available=False,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    climate_health = _compute_climate_health(engine, portfolio_id)
    financial_resilience = _compute_financial_resilience(engine, portfolio_id)
    transition_readiness = _compute_transition_readiness(engine, portfolio_id)

    overall_score = round(
        (climate_health.value + financial_resilience.value + transition_readiness.value) / 3.0,
        1,
    )

    return PortfolioHealthScores(
        portfolio_id=portfolio_id,
        portfolio_name=portfolio_name,
        climate_health=climate_health,
        financial_resilience=financial_resilience,
        transition_readiness=transition_readiness,
        overall_score=overall_score,
        alert_count=alert_count,
        data_available=True,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


def get_score_history(portfolio_id: str, weeks: int = 12) -> list[dict]:
    """
    Return weekly score history for sparkline charts.
    Currently returns simulated history based on pcaf_time_series; will be
    replaced by a snapshot store in a future sprint.
    """
    engine = _get_engine()
    if engine is None:
        return []

    # Return year-by-year actual vs glidepath for each metric as proxy
    rows = _exec(
        engine,
        """
        SELECT reporting_year,
               AVG(CASE WHEN metric_type = 'waci'
                   THEN CASE WHEN glidepath_value > 0
                        THEN GREATEST(0, 100 - ((actual_value - glidepath_value) / glidepath_value * 100))
                        ELSE 50 END
                   END) AS climate_score
        FROM pcaf_time_series
        WHERE portfolio_id = :pid
          AND actual_value IS NOT NULL
        GROUP BY reporting_year
        ORDER BY reporting_year ASC
        LIMIT :w
        """,
        {"pid": portfolio_id, "w": weeks},
    )
    return [
        {
            "period": str(r.reporting_year),
            "climate_health": round(float(r.climate_score or 50), 1),
        }
        for r in rows
    ]
