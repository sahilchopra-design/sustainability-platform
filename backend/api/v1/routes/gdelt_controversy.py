"""
GDELT Events + Controversy Scores API routes.

Endpoints:
  GET  /gdelt/events/search                   -- search GDELT events with filters
  GET  /gdelt/events/actors                   -- top actors by event count
  GET  /gdelt/events/timeline                 -- event timeline aggregation
  GET  /gdelt/events/countries                -- country breakdown
  GET  /gdelt/events/stats                    -- event statistics

  GET  /gdelt/gkg/search                      -- search GKG records
  GET  /gdelt/gkg/themes                      -- top ESG themes

  GET  /gdelt/controversy/search              -- search controversy scores
  GET  /gdelt/controversy/entity/{name}       -- entity controversy detail
  GET  /gdelt/controversy/rankings            -- ranked entity list
  GET  /gdelt/controversy/stats               -- controversy statistics
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from api.dependencies import require_min_role

router = APIRouter(prefix="/api/v1/gdelt", tags=["gdelt-controversy"])


# ── GDELT Events ──────────────────────────────────────────────────────────────

@router.get("/events/search")
def search_gdelt_events(
    actor: Optional[str] = Query(None, description="Actor name search"),
    country: Optional[str] = Query(None, description="Action country ISO"),
    quad_class: Optional[int] = Query(None, description="Quad class (1-4)"),
    min_mentions: Optional[int] = Query(None, description="Minimum mentions"),
    entity: Optional[str] = Query(None, description="Matched entity name"),
    year: Optional[int] = Query(None, description="Year filter"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search GDELT events with filters."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if actor:
        conditions.append("(actor1_name ILIKE :actor OR actor2_name ILIKE :actor)")
        params["actor"] = f"%{actor}%"
    if country:
        conditions.append("action_geo_country = :country")
        params["country"] = country.upper()
    if quad_class is not None:
        conditions.append("quad_class = :qc")
        params["qc"] = quad_class
    if min_mentions is not None:
        conditions.append("num_mentions >= :min_m")
        params["min_m"] = min_mentions
    if entity:
        conditions.append("matched_entity_name ILIKE :entity")
        params["entity"] = f"%{entity}%"
    if year:
        conditions.append("year = :year")
        params["year"] = year

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, global_event_id, event_date, year, month,
               actor1_name, actor1_country, actor1_type,
               actor2_name, actor2_country, actor2_type,
               event_code, event_base_code, event_root_code,
               quad_class, goldstein_scale,
               num_mentions, num_sources, num_articles, avg_tone,
               action_geo_country, action_geo_lat, action_geo_lon, action_geo_name,
               matched_entity_name
        FROM dh_gdelt_events
        {where}
        ORDER BY num_mentions DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"SELECT COUNT(*) FROM dh_gdelt_events {where}"), params).scalar()
    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/events/actors")
def gdelt_top_actors(
    min_events: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Top actors by event count."""
    rows = db.execute(text("""
        SELECT matched_entity_name AS entity,
               COUNT(*) AS events,
               SUM(num_mentions) AS total_mentions,
               ROUND(AVG(avg_tone)::numeric, 2) AS avg_tone,
               ROUND(AVG(goldstein_scale)::numeric, 2) AS avg_goldstein,
               COUNT(*) FILTER (WHERE quad_class >= 3) AS negative_events,
               COUNT(*) FILTER (WHERE quad_class <= 2) AS positive_events
        FROM dh_gdelt_events
        WHERE matched_entity_name IS NOT NULL
        GROUP BY matched_entity_name
        HAVING COUNT(*) >= :min_ev
        ORDER BY total_mentions DESC
        LIMIT :limit
    """), {"min_ev": min_events, "limit": limit}).mappings().all()
    return {"actors": [dict(r) for r in rows]}


@router.get("/events/timeline")
def gdelt_event_timeline(
    entity: Optional[str] = Query(None, description="Filter by entity"),
    granularity: str = Query("month", description="month or year"),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Event timeline aggregation."""
    entity_filter = ""
    params = {}
    if entity:
        entity_filter = "WHERE matched_entity_name ILIKE :entity"
        params["entity"] = f"%{entity}%"

    if granularity == "year":
        group_col = "year"
    else:
        group_col = "year || '-' || LPAD(month::text, 2, '0')"

    rows = db.execute(text(f"""
        SELECT {group_col} AS period,
               COUNT(*) AS events,
               SUM(num_mentions) AS mentions,
               ROUND(AVG(avg_tone)::numeric, 2) AS avg_tone,
               COUNT(*) FILTER (WHERE quad_class >= 3) AS negative,
               COUNT(*) FILTER (WHERE quad_class <= 2) AS positive
        FROM dh_gdelt_events
        {entity_filter}
        GROUP BY {group_col}
        ORDER BY {group_col}
    """), params).mappings().all()
    return {"timeline": [dict(r) for r in rows]}


@router.get("/events/countries")
def gdelt_event_countries(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Country breakdown of GDELT events."""
    rows = db.execute(text("""
        SELECT action_geo_country AS country,
               COUNT(*) AS events,
               SUM(num_mentions) AS mentions,
               ROUND(AVG(avg_tone)::numeric, 2) AS avg_tone,
               COUNT(DISTINCT matched_entity_name) AS entities
        FROM dh_gdelt_events
        WHERE action_geo_country IS NOT NULL
        GROUP BY action_geo_country
        ORDER BY events DESC
    """)).mappings().all()
    return {"countries": [dict(r) for r in rows]}


@router.get("/events/stats")
def gdelt_event_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """GDELT event statistics."""
    total = db.execute(text("SELECT COUNT(*) FROM dh_gdelt_events")).scalar() or 0
    entities = db.execute(text("SELECT COUNT(DISTINCT matched_entity_name) FROM dh_gdelt_events")).scalar() or 0
    countries = db.execute(text("SELECT COUNT(DISTINCT action_geo_country) FROM dh_gdelt_events")).scalar() or 0
    conflict = db.execute(text("SELECT COUNT(*) FROM dh_gdelt_events WHERE quad_class >= 3")).scalar() or 0
    coop = db.execute(text("SELECT COUNT(*) FROM dh_gdelt_events WHERE quad_class <= 2")).scalar() or 0
    mentions = db.execute(text("SELECT COALESCE(SUM(num_mentions), 0) FROM dh_gdelt_events")).scalar() or 0

    return {
        "events": {
            "total": total,
            "entities": entities,
            "countries": countries,
            "conflict_events": conflict,
            "cooperation_events": coop,
            "total_mentions": int(mentions),
        }
    }


# ── GDELT GKG ─────────────────────────────────────────────────────────────────

@router.get("/gkg/search")
def search_gdelt_gkg(
    entity: Optional[str] = Query(None, description="Matched entity filter"),
    esg_category: Optional[str] = Query(None, description="E, S, or G"),
    controversy_only: bool = Query(False, description="Only controversy-flagged"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search GDELT GKG records."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if entity:
        conditions.append("matched_entity_name ILIKE :entity")
        params["entity"] = f"%{entity}%"
    if esg_category:
        conditions.append("esg_category = :cat")
        params["cat"] = esg_category.upper()
    if controversy_only:
        conditions.append("controversy_flag = true")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, gkg_record_id, publish_date, source_name,
               document_tone, positive_score, negative_score, polarity,
               themes, organizations,
               esg_relevance_score, esg_category, controversy_flag,
               matched_entity_name
        FROM dh_gdelt_gkg
        {where}
        ORDER BY esg_relevance_score DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"SELECT COUNT(*) FROM dh_gdelt_gkg {where}"), params).scalar()
    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/gkg/themes")
def gdelt_gkg_themes(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Top ESG themes from GKG records."""
    rows = db.execute(text("""
        SELECT themes, esg_category, controversy_flag,
               COUNT(*) AS occurrences,
               ROUND(AVG(document_tone)::numeric, 2) AS avg_tone,
               ROUND(AVG(esg_relevance_score)::numeric, 3) AS avg_relevance
        FROM dh_gdelt_gkg
        WHERE themes IS NOT NULL
        GROUP BY themes, esg_category, controversy_flag
        ORDER BY occurrences DESC
    """)).mappings().all()
    return {"themes": [dict(r) for r in rows]}


# ── Controversy Scores ─────────────────────────────────────────────────────────

@router.get("/controversy/search")
def search_controversy(
    entity: Optional[str] = Query(None, description="Entity name search"),
    sector: Optional[str] = Query(None, description="Sector filter"),
    severity: Optional[str] = Query(None, description="Severity level"),
    min_score: Optional[float] = Query(None, description="Minimum controversy score"),
    country: Optional[str] = Query(None, description="Country ISO3"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Search controversy scores with filters."""
    conditions = []
    params = {"limit": limit, "offset": offset}

    if entity:
        conditions.append("entity_name ILIKE :entity")
        params["entity"] = f"%{entity}%"
    if sector:
        conditions.append("sector ILIKE :sector")
        params["sector"] = f"%{sector}%"
    if severity:
        conditions.append("severity_level = :severity")
        params["severity"] = severity
    if min_score is not None:
        conditions.append("controversy_score >= :min_sc")
        params["min_sc"] = min_score
    if country:
        conditions.append("country_iso3 = :country")
        params["country"] = country.upper()

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(text(f"""
        SELECT id, entity_name, entity_lei, country_iso3, sector,
               period_start, period_end,
               controversy_score, severity_level, trend,
               env_score, social_score, governance_score,
               total_events, negative_events, positive_events,
               avg_tone, avg_goldstein, media_mentions, top_themes
        FROM dh_controversy_scores
        {where}
        ORDER BY controversy_score DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    total = db.execute(text(f"SELECT COUNT(*) FROM dh_controversy_scores {where}"), params).scalar()
    return {"records": [dict(r) for r in rows], "total": total}


@router.get("/controversy/entity/{entity_name}")
def controversy_entity_detail(
    entity_name: str,
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Get controversy detail for a specific entity."""
    # Get controversy score
    score = db.execute(text("""
        SELECT id, entity_name, entity_lei, country_iso3, sector,
               period_start, period_end,
               controversy_score, severity_level, trend,
               env_score, social_score, governance_score,
               total_events, negative_events, positive_events,
               avg_tone, avg_goldstein, media_mentions, top_themes
        FROM dh_controversy_scores
        WHERE entity_name ILIKE :name
        ORDER BY period_end DESC
        LIMIT 1
    """), {"name": f"%{entity_name}%"}).mappings().first()

    if not score:
        raise HTTPException(status_code=404, detail=f"No controversy data for {entity_name}")

    # Get recent events
    events = db.execute(text("""
        SELECT global_event_id, event_date, actor1_name, actor2_name,
               event_code, quad_class, goldstein_scale,
               num_mentions, avg_tone, action_geo_name
        FROM dh_gdelt_events
        WHERE matched_entity_name ILIKE :name
        ORDER BY event_date DESC
        LIMIT 10
    """), {"name": f"%{entity_name}%"}).mappings().all()

    # Get GKG records
    gkg = db.execute(text("""
        SELECT gkg_record_id, publish_date, source_name,
               document_tone, themes, esg_category, controversy_flag
        FROM dh_gdelt_gkg
        WHERE matched_entity_name ILIKE :name
        ORDER BY publish_date DESC
        LIMIT 10
    """), {"name": f"%{entity_name}%"}).mappings().all()

    return {
        "entity": entity_name,
        "controversy": dict(score),
        "recent_events": [dict(e) for e in events],
        "recent_gkg": [dict(g) for g in gkg],
    }


@router.get("/controversy/rankings")
def controversy_rankings(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Ranked entities by controversy score."""
    sector_filter = ""
    params = {"limit": limit}
    if sector:
        sector_filter = "WHERE sector ILIKE :sector"
        params["sector"] = f"%{sector}%"

    rows = db.execute(text(f"""
        SELECT entity_name, country_iso3, sector,
               controversy_score, severity_level,
               env_score, social_score, governance_score,
               total_events, media_mentions,
               RANK() OVER (ORDER BY controversy_score DESC) AS rank
        FROM dh_controversy_scores
        {sector_filter}
        ORDER BY controversy_score DESC
        LIMIT :limit
    """), params).mappings().all()
    return {"rankings": [dict(r) for r in rows]}


@router.get("/controversy/stats")
def controversy_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_min_role("viewer")),
):
    """Summary statistics for controversy scoring."""
    total = db.execute(text("SELECT COUNT(*) FROM dh_controversy_scores")).scalar() or 0
    critical = db.execute(text("SELECT COUNT(*) FROM dh_controversy_scores WHERE severity_level = 'Critical'")).scalar() or 0
    high = db.execute(text("SELECT COUNT(*) FROM dh_controversy_scores WHERE severity_level = 'High'")).scalar() or 0
    medium = db.execute(text("SELECT COUNT(*) FROM dh_controversy_scores WHERE severity_level = 'Medium'")).scalar() or 0
    low = db.execute(text("SELECT COUNT(*) FROM dh_controversy_scores WHERE severity_level = 'Low'")).scalar() or 0
    avg_score = db.execute(text("SELECT ROUND(AVG(controversy_score)::numeric, 1) FROM dh_controversy_scores")).scalar() or 0
    sectors = db.execute(text("SELECT COUNT(DISTINCT sector) FROM dh_controversy_scores")).scalar() or 0
    gkg_total = db.execute(text("SELECT COUNT(*) FROM dh_gdelt_gkg")).scalar() or 0
    gkg_controversial = db.execute(text("SELECT COUNT(*) FROM dh_gdelt_gkg WHERE controversy_flag = true")).scalar() or 0

    return {
        "controversy": {
            "entities_scored": total,
            "severity_distribution": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            },
            "avg_score": float(avg_score),
            "sectors": sectors,
            "gkg_records": gkg_total,
            "gkg_controversial": gkg_controversial,
        }
    }
