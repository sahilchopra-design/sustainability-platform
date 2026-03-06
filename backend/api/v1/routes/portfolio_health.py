"""
Portfolio Health API — Sustainability Pulse Scores and Alerts

Endpoints:
  GET  /api/v1/portfolio-health/{portfolio_id}/scores   → three health scores
  GET  /api/v1/portfolio-health/{portfolio_id}/alerts   → paginated alert feed
  GET  /api/v1/portfolio-health/{portfolio_id}/history  → score trend (sparklines)
  POST /api/v1/portfolio-health/{portfolio_id}/refresh  → trigger recomputation
  PATCH /api/v1/portfolio-health/alerts/{alert_id}/read → mark alert as read
  PATCH /api/v1/portfolio-health/{portfolio_id}/read-all → mark all alerts read
  GET  /api/v1/portfolio-health/{portfolio_id}/unread-count → badge number
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.portfolio_health_engine import (
    compute_portfolio_health,
    get_score_history,
    PortfolioHealthScores,
    HealthScore,
)
from services.alert_engine import (
    get_portfolio_alerts,
    mark_alert_read,
    mark_all_read,
    get_unread_count,
)

router = APIRouter(prefix="/api/v1/portfolio-health", tags=["Portfolio Health"])


# ── Pydantic response models ───────────────────────────────────────────────────

class HealthScoreOut(BaseModel):
    value: float
    rag: str
    label: str
    action: str
    action_link: str


class PortfolioHealthResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    climate_health: HealthScoreOut
    financial_resilience: HealthScoreOut
    transition_readiness: HealthScoreOut
    overall_score: float
    alert_count: int
    data_available: bool
    last_updated: str


def _score_to_out(score: HealthScore) -> HealthScoreOut:
    return HealthScoreOut(
        value=score.value,
        rag=score.rag,
        label=score.label,
        action=score.action,
        action_link=score.action_link,
    )


def _health_to_response(h: PortfolioHealthScores) -> PortfolioHealthResponse:
    return PortfolioHealthResponse(
        portfolio_id=h.portfolio_id,
        portfolio_name=h.portfolio_name,
        climate_health=_score_to_out(h.climate_health),
        financial_resilience=_score_to_out(h.financial_resilience),
        transition_readiness=_score_to_out(h.transition_readiness),
        overall_score=h.overall_score,
        alert_count=h.alert_count,
        data_available=h.data_available,
        last_updated=h.last_updated,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{portfolio_id}/scores", response_model=PortfolioHealthResponse)
def get_health_scores(portfolio_id: str):
    """
    Return the three sustainability health scores for a portfolio.
    Safe to call frequently — scores are computed on-the-fly from DB state.
    Returns neutral AMBER scores if no data has been computed yet.
    """
    try:
        health = compute_portfolio_health(portfolio_id)
        return _health_to_response(health)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Health score computation failed: {str(exc)}",
        )


@router.get("/{portfolio_id}/alerts")
def get_alerts(
    portfolio_id: str,
    unread_only: bool = Query(False, description="Return only unread alerts"),
    limit: int = Query(50, ge=1, le=200, description="Max alerts to return"),
):
    """
    Return the alert feed for a portfolio, newest first.
    Use unread_only=true for the nav badge count query.
    """
    alerts = get_portfolio_alerts(
        portfolio_id=portfolio_id,
        unread_only=unread_only,
        limit=limit,
    )
    return {
        "portfolio_id": portfolio_id,
        "alerts": alerts,
        "total": len(alerts),
    }


@router.get("/{portfolio_id}/history")
def get_score_history_endpoint(
    portfolio_id: str,
    weeks: int = Query(12, ge=4, le=52),
):
    """
    Return score trend history for sparkline charts on the Sustainability Pulse
    dashboard. Returns year-by-year WACI vs. glidepath history as a proxy until
    a dedicated snapshot store is implemented (Sprint 8).
    """
    history = get_score_history(portfolio_id=portfolio_id, weeks=weeks)
    return {
        "portfolio_id": portfolio_id,
        "history": history,
        "periods": len(history),
    }


@router.post("/{portfolio_id}/refresh")
def refresh_health_scores(portfolio_id: str):
    """
    Trigger a recomputation of health scores for the portfolio.
    Useful after uploading new data or completing a PCAF/ECL calculation.
    The response includes the freshly computed scores.
    """
    try:
        health = compute_portfolio_health(portfolio_id)
        return {
            "message": "Health scores refreshed successfully",
            "scores": _health_to_response(health),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Refresh failed: {str(exc)}",
        )


@router.patch("/alerts/{alert_id}/read")
def mark_alert_as_read(alert_id: str):
    """Mark a single alert as read."""
    success = mark_alert_read(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or DB unavailable")
    return {"alert_id": alert_id, "is_read": True}


@router.patch("/{portfolio_id}/read-all")
def mark_all_alerts_read(portfolio_id: str):
    """Mark all unread alerts for a portfolio as read."""
    updated = mark_all_read(portfolio_id)
    return {"portfolio_id": portfolio_id, "alerts_marked_read": updated}


@router.get("/{portfolio_id}/unread-count")
def get_unread_alert_count(portfolio_id: str):
    """
    Return count of unread alerts — used for the nav badge on the
    Sustainability Pulse link in the sidebar.
    """
    count = get_unread_count(portfolio_id)
    return {"portfolio_id": portfolio_id, "unread_count": count}
