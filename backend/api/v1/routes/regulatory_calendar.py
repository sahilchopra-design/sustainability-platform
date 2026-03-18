"""
API Routes: Regulatory Obligation Calendar (E3)
================================================
GET  /api/v1/regulatory-calendar/obligations       — Full obligation list (filterable)
GET  /api/v1/regulatory-calendar/alerts            — Upcoming deadlines with urgency scoring
GET  /api/v1/regulatory-calendar/summary           — Counts by framework / urgency
GET  /api/v1/regulatory-calendar/module-coverage   — Platform module → obligation mapping
GET  /api/v1/regulatory-calendar/frameworks        — List all supported frameworks
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query

from services.regulatory_obligation_calendar import RegulatoryObligationCalendar

router = APIRouter(
    prefix="/api/v1/regulatory-calendar",
    tags=["Regulatory Calendar"],
)

# Singleton calendar instance (stateless — all computation is in-memory)
_CALENDAR = RegulatoryObligationCalendar()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _obligation_to_dict(ob) -> dict:
    return {
        "obligation_id": ob.obligation_id,
        "framework": ob.framework,
        "short_name": ob.short_name,
        "description": ob.description,
        "deadline": ob.deadline,
        "recurrence": ob.recurrence,
        "entity_scope": ob.entity_scope,
        "jurisdiction": ob.jurisdiction,
        "urgency": ob.urgency,
        "penalty_risk": ob.penalty_risk,
        "platform_modules": ob.platform_modules,
        "regulatory_reference": ob.regulatory_reference,
        "is_rescinded": ob.is_rescinded,
    }


def _alert_to_dict(alert: dict) -> dict:
    """Alert dicts are already plain dicts from get_upcoming_alerts()."""
    return alert


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/obligations",
    summary="List all regulatory obligations",
    description=(
        "Returns the full obligation registry.  Optional filters: frameworks (comma-separated), "
        "jurisdictions (comma-separated), entity_type."
    ),
)
def list_obligations(
    frameworks: Optional[str] = Query(
        None, description="Comma-separated framework names, e.g. CSRD,SFDR,ISSB"
    ),
    jurisdictions: Optional[str] = Query(
        None, description="Comma-separated jurisdiction codes, e.g. EU,IN,US"
    ),
    entity_type: Optional[str] = Query(
        None, description="Entity type filter, e.g. large_EU_company, insurer, UCITS_fund"
    ),
    include_rescinded: bool = Query(False, description="Include rescinded obligations"),
):
    framework_list: Optional[List[str]] = (
        [f.strip() for f in frameworks.split(",")] if frameworks else None
    )
    jurisdiction_list: Optional[List[str]] = (
        [j.strip() for j in jurisdictions.split(",")] if jurisdictions else None
    )

    calendar = _CALENDAR.filter(
        frameworks=framework_list,
        jurisdictions=jurisdiction_list,
        entity_types=[entity_type] if entity_type else None,
    )

    obligations = calendar._obligations
    if not include_rescinded:
        obligations = [o for o in obligations if not o.is_rescinded]

    return {
        "count": len(obligations),
        "filters_applied": {
            "frameworks": framework_list,
            "jurisdictions": jurisdiction_list,
            "entity_type": entity_type,
            "include_rescinded": include_rescinded,
        },
        "obligations": [_obligation_to_dict(o) for o in obligations],
    }


@router.get(
    "/alerts",
    summary="Upcoming deadline alerts with urgency scoring",
    description=(
        "Returns obligations due within `days_ahead` days, sorted by deadline ascending. "
        "Urgency is computed dynamically: ≤14 days → critical, ≤45 → high, ≤90 → medium, else low."
    ),
)
def get_alerts(
    days_ahead: int = Query(
        90, ge=1, le=730, description="Lookahead window in days (default 90)"
    ),
    frameworks: Optional[str] = Query(None, description="Comma-separated framework filter"),
    urgency: Optional[str] = Query(
        None, description="Filter by urgency level: critical | high | medium | low"
    ),
    include_rescinded: bool = Query(False),
):
    framework_list: Optional[List[str]] = (
        [f.strip() for f in frameworks.split(",")] if frameworks else None
    )

    calendar = _CALENDAR
    if framework_list:
        calendar = _CALENDAR.filter(frameworks=framework_list)

    alerts = calendar.get_upcoming_alerts(days_ahead=days_ahead)

    if not include_rescinded:
        alerts = [a for a in alerts if not a.get("is_rescinded", False)]

    if urgency:
        alerts = [a for a in alerts if a.get("urgency") == urgency]

    return {
        "days_ahead": days_ahead,
        "alert_count": len(alerts),
        "critical": sum(1 for a in alerts if a.get("urgency") == "critical"),
        "high": sum(1 for a in alerts if a.get("urgency") == "high"),
        "medium": sum(1 for a in alerts if a.get("urgency") == "medium"),
        "low": sum(1 for a in alerts if a.get("urgency") == "low"),
        "alerts": alerts,
    }


@router.get(
    "/summary",
    summary="Obligation counts by framework and urgency",
    description="Returns a summary dashboard of obligations grouped by framework and urgency bucket.",
)
def get_summary():
    return _CALENDAR.get_summary()


@router.get(
    "/module-coverage",
    summary="Platform module → obligation cross-reference",
    description=(
        "For each platform module (e.g. csrd_engine, pcaf_waci_engine), lists which "
        "regulatory obligations it produces evidence for."
    ),
)
def get_module_coverage():
    coverage = _CALENDAR.get_platform_module_coverage()
    return {
        "module_count": len(coverage),
        "coverage": coverage,
        "note": (
            "Each module entry lists obligations whose platform_modules field references "
            "that module.  Use this to ensure no obligation lacks platform evidence."
        ),
    }


@router.get(
    "/frameworks",
    summary="List all supported regulatory frameworks",
    description="Returns distinct framework names and the count of obligations per framework.",
)
def list_frameworks():
    all_obs = _CALENDAR._obligations
    framework_counts: dict = {}
    for ob in all_obs:
        framework_counts.setdefault(ob.framework, {"count": 0, "rescinded_count": 0})
        framework_counts[ob.framework]["count"] += 1
        if ob.is_rescinded:
            framework_counts[ob.framework]["rescinded_count"] += 1

    return {
        "framework_count": len(framework_counts),
        "frameworks": [
            {"framework": fw, **counts}
            for fw, counts in sorted(framework_counts.items())
        ],
    }


@router.get(
    "/obligations/{obligation_id}",
    summary="Get a single obligation by ID",
)
def get_obligation(obligation_id: str):
    for ob in _CALENDAR._obligations:
        if ob.obligation_id == obligation_id:
            return _obligation_to_dict(ob)
    from fastapi import HTTPException
    raise HTTPException(404, f"Obligation '{obligation_id}' not found")
