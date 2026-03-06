"""
Alert Engine — Continuous Monitoring for the Sustainability Pulse Dashboard

Generates and persists alerts to the platform_alerts table after each computation
run. Follows the WHOOP design principle: every signal produces a daily/weekly
actionable alert when a threshold is breached.

Alert types produced:
  glidepath_deviation    WACI > NZBA glidepath by sector
  dqs_degradation        Portfolio weighted DQS > 3.5
  pcaf_coverage_low      PCAF AUM coverage < 70%
  dscr_breach            Min DSCR < 1.25 (project finance)
  crrem_crossover        Asset crosses CRREM pathway (stranding year reached)
  sicr_trigger           ECL Stage 2/3 migration event
  transition_plan_missing  Entity with >5% exposure, no transition plan
  engagement_overdue     Last engagement > 90 days for escalated counterparty
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# ── Threshold constants ────────────────────────────────────────────────────────
GLIDEPATH_DEVIATION_WARNING_PCT = 0.10   # 10% above glidepath → WARNING
GLIDEPATH_DEVIATION_CRITICAL_PCT = 0.25  # 25% above glidepath → CRITICAL
DQS_WARNING_THRESHOLD = 3.5              # weighted avg DQS > 3.5 → WARNING
DQS_CRITICAL_THRESHOLD = 4.5            # weighted avg DQS > 4.5 → CRITICAL
PCAF_COVERAGE_WARNING_PCT = 0.70         # coverage < 70% → WARNING
PCAF_COVERAGE_CRITICAL_PCT = 0.50        # coverage < 50% → CRITICAL
DSCR_MINIMUM = 1.25                      # DSCR below this → CRITICAL
DSCR_CAUTION = 1.35                      # DSCR below this → WARNING
LARGE_EXPOSURE_PCT = 0.05                # 5% portfolio share = large exposure

# ── Module links (frontend routes) ────────────────────────────────────────────
MODULE_LINKS = {
    "glidepath_deviation":     "/glidepath-tracker",
    "dqs_degradation":         "/financial-risk",
    "pcaf_coverage_low":       "/portfolio-analytics",
    "dscr_breach":             "/sector-assessments",
    "crrem_crossover":         "/real-estate-assessment",
    "sicr_trigger":            "/financial-risk",
    "transition_plan_missing": "/regulatory",
    "engagement_overdue":      "/regulatory",
}


# ── Internal DB helper ─────────────────────────────────────────────────────────

def _get_engine() -> Optional[Engine]:
    """Lazy-import to avoid circular imports at module load time."""
    try:
        from db.base import engine as _engine
        return _engine
    except Exception:
        return None


def _write_alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    portfolio_id: Optional[str] = None,
    entity_lei: Optional[str] = None,
    metric_value: Optional[float] = None,
    threshold: Optional[float] = None,
) -> bool:
    """Persist a single alert to the platform_alerts table."""
    engine = _get_engine()
    if engine is None:
        logger.warning("[AlertEngine] DB unavailable — alert not persisted: %s", title)
        return False
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO platform_alerts
                      (id, portfolio_id, entity_lei, alert_type, severity,
                       title, message, metric_value, threshold, module_link,
                       is_read, is_resolved, created_at)
                    VALUES
                      (:id, :portfolio_id, :entity_lei, :alert_type, :severity,
                       :title, :message, :metric_value, :threshold, :module_link,
                       false, false, NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "portfolio_id": portfolio_id,
                    "entity_lei": entity_lei,
                    "alert_type": alert_type,
                    "severity": severity,
                    "title": title,
                    "message": message,
                    "metric_value": float(metric_value) if metric_value is not None else None,
                    "threshold": float(threshold) if threshold is not None else None,
                    "module_link": MODULE_LINKS.get(alert_type, "/portfolio-health"),
                },
            )
        return True
    except Exception as exc:
        logger.error("[AlertEngine] Failed to persist alert '%s': %s", title, exc)
        return False


def _dedup_check(portfolio_id: str, alert_type: str, within_hours: int = 24) -> bool:
    """
    Return True if a non-resolved alert of this type already exists for
    this portfolio within the dedup window. Prevents duplicate flooding.
    """
    engine = _get_engine()
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT COUNT(*) FROM platform_alerts
                    WHERE portfolio_id = :pid
                      AND alert_type = :atype
                      AND is_resolved = false
                      AND created_at > NOW() - INTERVAL ':hours hours'
                """),
                {"pid": portfolio_id, "atype": alert_type, "hours": within_hours},
            ).scalar()
        return (row or 0) > 0
    except Exception:
        return False


# ── Public API ─────────────────────────────────────────────────────────────────

def evaluate_glidepath_deviation(
    portfolio_id: str,
    sector: str,
    actual_waci: float,
    glidepath_waci: float,
) -> None:
    """
    Fire a glidepath_deviation alert if actual WACI exceeds the NZBA sector
    glidepath by more than the warning or critical threshold.
    """
    if glidepath_waci <= 0:
        return
    deviation = (actual_waci - glidepath_waci) / glidepath_waci
    if deviation <= GLIDEPATH_DEVIATION_WARNING_PCT:
        return  # on track

    severity = "critical" if deviation >= GLIDEPATH_DEVIATION_CRITICAL_PCT else "warning"
    deviation_pct = round(deviation * 100, 1)
    title = f"{sector} WACI is {deviation_pct}% above NZBA glidepath"
    message = (
        f"Portfolio {portfolio_id[:8]}… — {sector} sector WACI is "
        f"{actual_waci:.1f} tCO₂e/MEUR vs. glidepath target of "
        f"{glidepath_waci:.1f} tCO₂e/MEUR ({deviation_pct}% deviation). "
        "Review top-contributing assets and update engagement plans."
    )
    _write_alert(
        alert_type="glidepath_deviation",
        severity=severity,
        title=title,
        message=message,
        portfolio_id=portfolio_id,
        metric_value=actual_waci,
        threshold=glidepath_waci,
    )


def evaluate_dqs(
    portfolio_id: str,
    weighted_dqs: float,
    coverage_pct: float,
) -> None:
    """
    Fire alerts when data quality degrades (DQS > threshold) or PCAF coverage
    falls below acceptable levels.
    """
    # DQS check
    if weighted_dqs >= DQS_CRITICAL_THRESHOLD:
        _write_alert(
            alert_type="dqs_degradation",
            severity="critical",
            title=f"Portfolio data quality critical (DQS {weighted_dqs:.1f}/5.0)",
            message=(
                f"Weighted PCAF Data Quality Score is {weighted_dqs:.2f}/5.0. "
                "Scores above 4.5 mean most emissions data is modelled estimates. "
                "Upload verified scope 1/2 reports for top emitters to improve accuracy."
            ),
            portfolio_id=portfolio_id,
            metric_value=weighted_dqs,
            threshold=DQS_CRITICAL_THRESHOLD,
        )
    elif weighted_dqs >= DQS_WARNING_THRESHOLD:
        _write_alert(
            alert_type="dqs_degradation",
            severity="warning",
            title=f"Portfolio data quality below target (DQS {weighted_dqs:.1f}/5.0)",
            message=(
                f"Weighted PCAF Data Quality Score is {weighted_dqs:.2f}/5.0 — "
                "target is ≤ 3.5. Collect verified emissions data from the "
                "largest counterparties by financed emissions."
            ),
            portfolio_id=portfolio_id,
            metric_value=weighted_dqs,
            threshold=DQS_WARNING_THRESHOLD,
        )

    # Coverage check
    if coverage_pct < PCAF_COVERAGE_CRITICAL_PCT:
        _write_alert(
            alert_type="pcaf_coverage_low",
            severity="critical",
            title=f"PCAF coverage critically low ({coverage_pct:.0%} of AUM)",
            message=(
                f"Only {coverage_pct:.0%} of AUM is covered in the PCAF calculation. "
                "This significantly underestimates financed emissions. "
                "Add emissions data for uncovered positions."
            ),
            portfolio_id=portfolio_id,
            metric_value=coverage_pct * 100,
            threshold=PCAF_COVERAGE_CRITICAL_PCT * 100,
        )
    elif coverage_pct < PCAF_COVERAGE_WARNING_PCT:
        _write_alert(
            alert_type="pcaf_coverage_low",
            severity="warning",
            title=f"PCAF coverage below 70% ({coverage_pct:.0%} of AUM)",
            message=(
                f"PCAF coverage is {coverage_pct:.0%} — below the 70% minimum "
                "for credible disclosure. Prioritise data collection for the "
                "largest uncovered positions."
            ),
            portfolio_id=portfolio_id,
            metric_value=coverage_pct * 100,
            threshold=PCAF_COVERAGE_WARNING_PCT * 100,
        )


def evaluate_dscr(
    portfolio_id: str,
    asset_name: str,
    min_dscr: float,
    entity_lei: Optional[str] = None,
) -> None:
    """Fire alert when a project finance asset falls below DSCR thresholds."""
    if min_dscr >= DSCR_CAUTION:
        return  # healthy

    severity = "critical" if min_dscr < DSCR_MINIMUM else "warning"
    label = "below minimum" if min_dscr < DSCR_MINIMUM else "approaching minimum"
    _write_alert(
        alert_type="dscr_breach",
        severity=severity,
        title=f"{asset_name} DSCR {label} ({min_dscr:.2f}x)",
        message=(
            f"Minimum DSCR for {asset_name} is {min_dscr:.2f}x "
            f"({'below' if min_dscr < DSCR_MINIMUM else 'near'} "
            f"the 1.25x bankability threshold). "
            "Review cash flow waterfall, consider DSRA sizing or restructuring."
        ),
        portfolio_id=portfolio_id,
        entity_lei=entity_lei,
        metric_value=min_dscr,
        threshold=DSCR_MINIMUM,
    )


def evaluate_sicr(
    portfolio_id: str,
    asset_name: str,
    pd_uplift_bps: float,
    triggers: list[str],
    entity_lei: Optional[str] = None,
) -> None:
    """Fire alert on SICR trigger (ECL stage migration event)."""
    if pd_uplift_bps < 100:
        return  # below SICR threshold

    severity = "critical" if pd_uplift_bps >= 500 else "warning"
    triggers_str = ", ".join(triggers) if triggers else "PD uplift"
    _write_alert(
        alert_type="sicr_trigger",
        severity=severity,
        title=f"SICR triggered for {asset_name} (+{pd_uplift_bps:.0f} bps PD)",
        message=(
            f"{asset_name} has triggered Significant Increase in Credit Risk "
            f"(SICR) with a {pd_uplift_bps:.0f} bps PD uplift. "
            f"Triggers: {triggers_str}. "
            "Review for Stage 2 migration and lifetime ECL provisioning."
        ),
        portfolio_id=portfolio_id,
        entity_lei=entity_lei,
        metric_value=pd_uplift_bps,
        threshold=100.0,
    )


def evaluate_transition_coverage(
    portfolio_id: str,
    entity_name: str,
    exposure_pct: float,
    transition_plan_status: Optional[str],
    entity_lei: Optional[str] = None,
) -> None:
    """
    Fire alert when a large-exposure counterparty (>5% AUM) has no transition
    plan in place — key NZBA engagement requirement.
    """
    if exposure_pct < LARGE_EXPOSURE_PCT:
        return
    if transition_plan_status in ("plan_received", "validated", "on_track"):
        return

    _write_alert(
        alert_type="transition_plan_missing",
        severity="warning",
        title=f"{entity_name} — no transition plan ({exposure_pct:.1%} of AUM)",
        message=(
            f"{entity_name} represents {exposure_pct:.1%} of portfolio AUM "
            f"but has transition plan status: '{transition_plan_status or 'not_started'}'. "
            "NZBA engagement guidelines require a credible transition plan for "
            "counterparties > 5% AUM. Initiate engagement or consider portfolio action."
        ),
        portfolio_id=portfolio_id,
        entity_lei=entity_lei,
        metric_value=exposure_pct * 100,
        threshold=LARGE_EXPOSURE_PCT * 100,
    )


def evaluate_crrem_crossover(
    portfolio_id: str,
    asset_name: str,
    stranding_year: int,
    current_year: int = 2026,
    entity_lei: Optional[str] = None,
) -> None:
    """Fire alert when a real estate asset crosses (or is near) its CRREM stranding year."""
    if stranding_year > current_year + 10:
        return  # beyond 10-year horizon — no alert needed yet

    years_to_strand = stranding_year - current_year
    severity = "critical" if years_to_strand <= 0 else "warning"
    timing = "already stranded" if years_to_strand <= 0 else f"stranding in {years_to_strand} years ({stranding_year})"
    _write_alert(
        alert_type="crrem_crossover",
        severity=severity,
        title=f"{asset_name} — CRREM {timing}",
        message=(
            f"{asset_name} is {timing} under the CRREM decarbonisation pathway. "
            "Stranded assets face brown discount on valuation and potential "
            "collateral haircuts. Review energy improvement plan and CRREM target trajectory."
        ),
        portfolio_id=portfolio_id,
        entity_lei=entity_lei,
        metric_value=float(stranding_year),
        threshold=float(current_year),
    )


def get_portfolio_alerts(
    portfolio_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> list[dict]:
    """
    Retrieve alerts for a portfolio, newest first.
    Returns empty list if DB is unavailable (graceful degrade).
    """
    engine = _get_engine()
    if engine is None:
        return []
    try:
        where_clause = "WHERE portfolio_id = :pid"
        if unread_only:
            where_clause += " AND is_read = false"
        with engine.connect() as conn:
            rows = conn.execute(
                text(f"""
                    SELECT id, alert_type, severity, title, message,
                           metric_value, threshold, module_link,
                           is_read, is_resolved, created_at
                    FROM platform_alerts
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :lim
                """),
                {"pid": portfolio_id, "lim": limit},
            ).fetchall()
        return [
            {
                "id": r.id,
                "alert_type": r.alert_type,
                "severity": r.severity,
                "title": r.title,
                "message": r.message,
                "metric_value": float(r.metric_value) if r.metric_value is not None else None,
                "threshold": float(r.threshold) if r.threshold is not None else None,
                "module_link": r.module_link,
                "is_read": r.is_read,
                "is_resolved": r.is_resolved,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    except Exception as exc:
        logger.error("[AlertEngine] get_portfolio_alerts failed: %s", exc)
        return []


def mark_alert_read(alert_id: str) -> bool:
    """Mark a single alert as read."""
    engine = _get_engine()
    if engine is None:
        return False
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE platform_alerts SET is_read = true WHERE id = :id"),
                {"id": alert_id},
            )
        return True
    except Exception as exc:
        logger.error("[AlertEngine] mark_alert_read failed: %s", exc)
        return False


def mark_all_read(portfolio_id: str) -> int:
    """Mark all unread alerts for a portfolio as read. Returns count updated."""
    engine = _get_engine()
    if engine is None:
        return 0
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    UPDATE platform_alerts
                    SET is_read = true
                    WHERE portfolio_id = :pid AND is_read = false
                """),
                {"pid": portfolio_id},
            )
        return result.rowcount
    except Exception as exc:
        logger.error("[AlertEngine] mark_all_read failed: %s", exc)
        return 0


def get_unread_count(portfolio_id: str) -> int:
    """Return unread alert count for a portfolio (used by nav badge)."""
    engine = _get_engine()
    if engine is None:
        return 0
    try:
        with engine.connect() as conn:
            count = conn.execute(
                text("""
                    SELECT COUNT(*) FROM platform_alerts
                    WHERE portfolio_id = :pid
                      AND is_read = false
                      AND is_resolved = false
                """),
                {"pid": portfolio_id},
            ).scalar()
        return int(count or 0)
    except Exception:
        return 0
