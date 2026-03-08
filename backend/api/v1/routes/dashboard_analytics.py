"""
Dashboard Analytics API -- real-data aggregation for the Interactive Dashboard.

Replaces seed-based random data generators in the frontend with pre-computed
summaries from the live database (SBTi, CA100+, Country Risk, CSRD KPIs,
Company Profiles, Portfolios, NGFS Scenarios).

Endpoints:
  GET  /dashboard/analytics            -- full dashboard dataset
  GET  /dashboard/analytics/portfolio   -- portfolio exposure by sector
  GET  /dashboard/analytics/climate     -- SBTi/CA100+ climate risk summary
  GET  /dashboard/analytics/emissions   -- emissions by sector from SBTi
  GET  /dashboard/analytics/governance  -- country risk governance summary
  GET  /dashboard/analytics/kpis        -- top-level KPI cards
  GET  /dashboard/analytics/time-series -- NGFS scenario loss trajectories
  GET  /dashboard/analytics/sensitivity -- tornado driver impact analysis
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, distinct, text, case
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.scenario_ingest import SbtiCompany

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard-analytics"])


# ── Combined Dashboard Analytics ────────────────────────────────────────────

@router.get("/analytics")
def full_dashboard(
    db: Session = Depends(get_db),

):
    """Complete dashboard dataset aggregated from all live data sources."""
    return {
        "kpis": _compute_kpis(db),
        "portfolio_exposure": _compute_portfolio_exposure(db),
        "climate_risk": _compute_climate_risk(db),
        "emissions_by_sector": _compute_emissions_by_sector(db),
        "governance_heatmap": _compute_governance_heatmap(db),
        "sbti_alignment": _compute_sbti_alignment(db),
        "ca100_overview": _compute_ca100_overview(db),
    }


@router.get("/analytics/kpis")
def dashboard_kpis(
    db: Session = Depends(get_db),

):
    """Top-level KPI cards for the dashboard."""
    return _compute_kpis(db)


@router.get("/analytics/portfolio")
def dashboard_portfolio(
    db: Session = Depends(get_db),

):
    """Portfolio exposure breakdown by sector."""
    return {"portfolio_exposure": _compute_portfolio_exposure(db)}


@router.get("/analytics/climate")
def dashboard_climate(
    db: Session = Depends(get_db),

):
    """Climate risk summary from SBTi + CA100+."""
    return {
        "climate_risk": _compute_climate_risk(db),
        "ca100_overview": _compute_ca100_overview(db),
    }


@router.get("/analytics/emissions")
def dashboard_emissions(
    db: Session = Depends(get_db),

):
    """Emissions data aggregated from SBTi sectors."""
    return {"emissions_by_sector": _compute_emissions_by_sector(db)}


@router.get("/analytics/governance")
def dashboard_governance(
    db: Session = Depends(get_db),

):
    """Governance/country risk heatmap data."""
    return {"governance_heatmap": _compute_governance_heatmap(db)}


@router.get("/analytics/time-series")
def dashboard_time_series(
    db: Session = Depends(get_db),
    horizon: int = Query(2050, ge=2030, le=2100, description="Projection horizon year"),
):
    """Loss trajectory over time using NGFS scenario carbon price pathways.

    Returns [{year, scenario1_el, scenario2_el, ...}] where EL is expected
    loss in $M derived from NGFS carbon price trajectories combined with
    the SBTi sector alignment rate as a risk multiplier.
    """
    return {"time_series": _compute_time_series(db, horizon)}


@router.get("/analytics/sensitivity")
def dashboard_sensitivity(
    db: Session = Depends(get_db),
):
    """Tornado chart driver impact analysis.

    Uses NGFS scenario carbon price spreads, SBTi alignment distributions,
    country risk index spreads, and portfolio exposure ranges to compute
    the low/high/swing impact of each macro driver on Expected Loss.
    """
    return {"sensitivity": _compute_sensitivity_drivers(db)}


# ── Internal Aggregation Functions ──────────────────────────────────────────

def _compute_kpis(db: Session) -> dict:
    """Top-level platform-wide KPI cards."""
    # Company profiles
    cp_total = _safe_scalar(db, "SELECT COUNT(*) FROM company_profiles")
    cp_csrd = _safe_scalar(db, "SELECT COUNT(*) FROM company_profiles WHERE data_source = 'csrd_report'")

    # SBTi
    sbti_total = db.query(func.count(SbtiCompany.id)).scalar() or 0
    sbti_nz = db.query(func.count(SbtiCompany.id)).filter(
        SbtiCompany.net_zero_committed == True
    ).scalar() or 0
    sbti_15c = db.query(func.count(SbtiCompany.id)).filter(
        SbtiCompany.near_term_ambition.ilike("1.5%")
    ).scalar() or 0

    # CA100+
    ca100 = _safe_scalar(db, "SELECT COUNT(*) FROM dh_ca100_assessments")

    # Country risk
    cr_countries = _safe_scalar(db, "SELECT COUNT(DISTINCT country_iso3) FROM dh_country_risk_indices")
    cr_indices = _safe_scalar(db, "SELECT COUNT(DISTINCT index_name) FROM dh_country_risk_indices")

    # CSRD KPIs
    csrd_kpis = _safe_scalar(db, "SELECT COUNT(*) FROM csrd_kpi_values")
    csrd_entities = _safe_scalar(db, "SELECT COUNT(*) FROM csrd_entity_registry")

    # Portfolios
    portfolios = _safe_scalar(db, "SELECT COUNT(*) FROM portfolios_pg")

    return {
        "total_entities": cp_total,
        "csrd_entities": cp_csrd,
        "csrd_kpi_values": csrd_kpis,
        "sbti_companies": sbti_total,
        "sbti_net_zero": sbti_nz,
        "sbti_aligned_1_5c": sbti_15c,
        "ca100_companies": ca100,
        "country_risk_countries": cr_countries,
        "country_risk_indices": cr_indices,
        "portfolios": portfolios,
        "total_data_points": sbti_total + ca100 + cr_countries + csrd_kpis,
    }


def _compute_portfolio_exposure(db: Session) -> list:
    """Portfolio sector exposure from SBTi sector distribution (proxy for portfolio)."""
    rows = (
        db.query(
            SbtiCompany.sector,
            func.count(SbtiCompany.id).label("companies"),
            func.sum(case((SbtiCompany.near_term_ambition.ilike("1.5%"), 1), else_=0)).label("aligned_1_5c"),
            func.sum(case((SbtiCompany.net_zero_committed == True, 1), else_=0)).label("net_zero"),
            func.sum(case(
                (func.lower(SbtiCompany.target_status) == "targets set", 1), else_=0
            )).label("targets_set"),
        )
        .group_by(SbtiCompany.sector)
        .order_by(func.count(SbtiCompany.id).desc())
        .limit(15)
        .all()
    )
    return [
        {
            "sector": r[0] or "Unknown",
            "companies": r[1],
            "aligned_1_5c": r[2],
            "net_zero": r[3],
            "targets_set": r[4],
            "risk_score": round(100 - (r[2] / max(r[1], 1)) * 100, 1),
        }
        for r in rows
    ]


def _compute_climate_risk(db: Session) -> dict:
    """Climate risk summary from SBTi target status distribution."""
    status_rows = (
        db.query(
            SbtiCompany.target_status,
            func.count(SbtiCompany.id),
        )
        .group_by(SbtiCompany.target_status)
        .all()
    )
    ambition_rows = (
        db.query(
            SbtiCompany.near_term_ambition,
            func.count(SbtiCompany.id),
        )
        .filter(SbtiCompany.near_term_ambition.isnot(None))
        .group_by(SbtiCompany.near_term_ambition)
        .all()
    )

    return {
        "target_status_distribution": [
            {"status": r[0] or "Unknown", "count": r[1]} for r in status_rows
        ],
        "ambition_distribution": [
            {"ambition": r[0] or "Unknown", "count": r[1]} for r in ambition_rows
        ],
    }


def _compute_emissions_by_sector(db: Session) -> list:
    """Sector-level emissions proxy from SBTi sectors with alignment rates."""
    rows = (
        db.query(
            SbtiCompany.sector,
            func.count(SbtiCompany.id).label("total"),
            func.sum(case((SbtiCompany.near_term_ambition.ilike("1.5%"), 1), else_=0)).label("a15"),
            func.sum(case((SbtiCompany.near_term_ambition.ilike("Well-below%"), 1), else_=0)).label("wb2"),
            func.sum(case((SbtiCompany.near_term_ambition.ilike("2%"), 1), else_=0)).label("a2"),
            func.sum(case((SbtiCompany.net_zero_committed == True, 1), else_=0)).label("nz"),
        )
        .group_by(SbtiCompany.sector)
        .order_by(func.count(SbtiCompany.id).desc())
        .limit(12)
        .all()
    )
    return [
        {
            "sector": r[0] or "Unknown",
            "total_companies": r[1],
            "aligned_1_5c": r[2],
            "well_below_2c": r[3],
            "aligned_2c": r[4],
            "net_zero": r[5],
            "alignment_rate": round((r[2] + r[3]) / max(r[1], 1) * 100, 1),
            "paris_aligned": (r[2] + r[3]) / max(r[1], 1) > 0.5,
        }
        for r in rows
    ]


def _compute_governance_heatmap(db: Session) -> list:
    """Country governance heatmap from CPI + FSI + FH_FIW + UNDP_GII."""
    try:
        rows = db.execute(text("""
            SELECT
                c.country_name,
                c.country_iso3,
                MAX(CASE WHEN c.index_name = 'CPI' THEN c.score END) AS cpi,
                MAX(CASE WHEN c.index_name = 'FSI' THEN c.score END) AS fsi,
                MAX(CASE WHEN c.index_name = 'FH_FIW' THEN c.score END) AS fh_fiw,
                MAX(CASE WHEN c.index_name = 'UNDP_GII' THEN c.score END) AS gii
            FROM dh_country_risk_indices c
            WHERE c.year = (
                SELECT MAX(year) FROM dh_country_risk_indices sub
                WHERE sub.index_name = c.index_name AND sub.country_iso3 = c.country_iso3
            )
            GROUP BY c.country_name, c.country_iso3
            HAVING COUNT(DISTINCT c.index_name) >= 3
            ORDER BY c.country_name
            LIMIT 50
        """)).fetchall()

        return [
            {
                "country": r[0],
                "iso3": r[1],
                "cpi": r[2],
                "fsi": r[3],
                "fh_fiw": r[4],
                "gii": r[5],
                # Composite governance score: normalise each to 0-100 (higher = better)
                "composite": round(
                    (
                        (r[2] or 0)  # CPI: already 0-100 (higher = better)
                        + (120 - (r[3] or 120)) / 120 * 100  # FSI: invert (lower = better)
                        + (14 - (r[4] or 14)) / 14 * 100  # FH_FIW: invert (lower = better)
                        + (1 - (r[5] or 1)) * 100  # GII: invert (lower = better)
                    ) / 4,
                    1,
                ),
            }
            for r in rows
        ]
    except Exception:
        return []


def _compute_sbti_alignment(db: Session) -> dict:
    """SBTi alignment time series by country (top 10)."""
    rows = (
        db.query(
            SbtiCompany.country,
            func.count(SbtiCompany.id).label("total"),
            func.sum(case((SbtiCompany.near_term_ambition.ilike("1.5%"), 1), else_=0)).label("a15"),
            func.sum(case((SbtiCompany.net_zero_committed == True, 1), else_=0)).label("nz"),
        )
        .filter(SbtiCompany.country.isnot(None))
        .group_by(SbtiCompany.country)
        .order_by(func.count(SbtiCompany.id).desc())
        .limit(10)
        .all()
    )
    return {
        "top_countries": [
            {
                "country": r[0],
                "total": r[1],
                "aligned_1_5c": r[2],
                "net_zero": r[3],
                "alignment_pct": round(r[2] / max(r[1], 1) * 100, 1),
            }
            for r in rows
        ],
    }


def _compute_ca100_overview(db: Session) -> dict:
    """CA100+ sector cluster overview."""
    try:
        rows = db.execute(text("""
            SELECT
                sector_cluster,
                COUNT(*) AS companies,
                COUNT(CASE WHEN indicator_1_score = 'Yes' THEN 1 END) AS disclosure_yes,
                COUNT(CASE WHEN indicator_2_score = 'Yes' THEN 1 END) AS targets_yes,
                COUNT(CASE WHEN indicator_3_score = 'Yes' THEN 1 END) AS emissions_yes,
                -- Alignment score: count of 'Yes' across first 3 indicators / 3
                ROUND(AVG(
                    (CASE WHEN indicator_1_score = 'Yes' THEN 1 ELSE 0 END +
                     CASE WHEN indicator_2_score = 'Yes' THEN 1 ELSE 0 END +
                     CASE WHEN indicator_3_score = 'Yes' THEN 1 ELSE 0 END)::numeric / 3 * 100
                )::numeric, 1) AS avg_alignment
            FROM dh_ca100_assessments
            WHERE sector_cluster IS NOT NULL
            GROUP BY sector_cluster
            ORDER BY COUNT(*) DESC
        """)).fetchall()
        return {
            "sector_clusters": [
                {
                    "cluster": r[0],
                    "companies": r[1],
                    "disclosure_aligned": r[2],
                    "targets_aligned": r[3],
                    "emissions_aligned": r[4],
                    "avg_alignment_pct": float(r[5]) if r[5] else 0.0,
                }
                for r in rows
            ],
        }
    except Exception:
        return {"sector_clusters": []}


# ── Time-Series & Sensitivity Aggregation ────────────────────────────────────

def _compute_time_series(db: Session, horizon: int) -> list:
    """Build loss trajectory from NGFS scenario carbon-price pathways.

    For each 5-year step from 2025 to *horizon*, linearly interpolate the
    carbon price for each NGFS scenario, then convert to an expected-loss
    proxy (EL = base_exposure * carbon_price_factor * alignment_risk).

    The alignment_risk comes from SBTi: the higher the proportion of
    companies without targets, the higher the portfolio transition risk.
    """
    try:
        # 1. NGFS scenario carbon prices
        ngfs_rows = db.execute(text("""
            SELECT scenario_name, carbon_price_2030_usd, carbon_price_2050_usd
            FROM ngfs_scenarios
            WHERE carbon_price_2030_usd IS NOT NULL
            ORDER BY scenario_name
        """)).fetchall()

        if not ngfs_rows:
            return []

        # 2. SBTi alignment risk multiplier
        sbti = db.execute(text("""
            SELECT
                COUNT(*) AS total,
                COUNT(CASE WHEN LOWER(target_status) = 'targets set' THEN 1 END) AS targets_set
            FROM dh_sbti_companies
        """)).fetchone()
        sbti_total = sbti[0] or 1
        sbti_set = sbti[1] or 0
        # Companies without targets → higher transition risk
        no_target_ratio = 1 - (sbti_set / sbti_total)  # 0..1

        # 3. Build yearly grid
        years = list(range(2025, horizon + 1, 5))
        if years[-1] != horizon:
            years.append(horizon)

        results = []
        for year in years:
            entry: dict = {"year": year}
            for row in ngfs_rows:
                name = row[0]
                cp_2030 = float(row[1])
                cp_2050 = float(row[2])
                # 2025 carbon price = assumed 80% of 2030
                cp_2025 = cp_2030 * 0.8

                # Linear interpolation
                if year <= 2030:
                    t = (year - 2025) / 5
                    cp = cp_2025 + t * (cp_2030 - cp_2025)
                elif year <= 2050:
                    t = (year - 2030) / 20
                    cp = cp_2030 + t * (cp_2050 - cp_2030)
                else:
                    # Extrapolate beyond 2050 at the same slope
                    slope = (cp_2050 - cp_2030) / 20
                    cp = cp_2050 + slope * (year - 2050)

                # Convert to expected loss $M
                # Higher carbon price → higher transition cost
                # Higher no-target ratio → more vulnerable portfolio
                base_exposure_m = 500  # Normalised portfolio exposure $M
                carbon_factor = cp / 1000  # Scale: $100/t → 0.1
                risk_mult = 0.3 + no_target_ratio * 0.7  # 0.3–1.0
                el = round(base_exposure_m * carbon_factor * risk_mult, 2)
                entry[name] = el

            results.append(entry)

        return results

    except Exception:
        return []


def _compute_sensitivity_drivers(db: Session) -> list:
    """Compute tornado chart data: impact of each macro driver on EL.

    Each driver contributes a low/high swing computed from the actual data
    ranges observed in the database (NGFS carbon price spread, SBTi
    alignment spread, country risk index spread, portfolio exposure).
    """
    drivers = []

    try:
        # 1. Carbon Price (NGFS spread at 2050)
        cp = db.execute(text("""
            SELECT MIN(carbon_price_2050_usd), MAX(carbon_price_2050_usd),
                   AVG(carbon_price_2050_usd)
            FROM ngfs_scenarios
            WHERE carbon_price_2050_usd IS NOT NULL
        """)).fetchone()
        if cp and cp[2]:
            avg_cp = float(cp[2])
            low_impact = round((float(cp[0]) - avg_cp) / avg_cp * 100, 2) if avg_cp else 0
            high_impact = round((float(cp[1]) - avg_cp) / avg_cp * 100, 2) if avg_cp else 0
            drivers.append({
                "driver": "Carbon Price",
                "low": low_impact,
                "high": high_impact,
                "swing": round(high_impact - low_impact, 2),
                "source": "NGFS v4",
            })

        # 2. SBTi Sector Alignment Spread
        sa = db.execute(text("""
            SELECT
                MIN(alignment_rate) AS min_ar,
                MAX(alignment_rate) AS max_ar,
                AVG(alignment_rate) AS avg_ar
            FROM (
                SELECT sector,
                    ROUND(
                        (COUNT(CASE WHEN near_term_ambition ILIKE '1.5%%' THEN 1 END)
                         + COUNT(CASE WHEN near_term_ambition ILIKE 'Well-below%%' THEN 1 END)
                        )::numeric / GREATEST(COUNT(*), 1) * 100, 1
                    ) AS alignment_rate
                FROM dh_sbti_companies
                WHERE sector IS NOT NULL
                GROUP BY sector
                HAVING COUNT(*) >= 20
            ) sub
        """)).fetchone()
        if sa and sa[2]:
            avg_ar = float(sa[2])
            # Higher alignment = lower risk
            drivers.append({
                "driver": "Sector Alignment Rate",
                "low": round(-(float(sa[1]) - avg_ar) / max(avg_ar, 1) * 15, 2),
                "high": round(-(float(sa[0]) - avg_ar) / max(avg_ar, 1) * 15, 2),
                "swing": 0,
                "source": "SBTi",
            })
            drivers[-1]["swing"] = round(drivers[-1]["high"] - drivers[-1]["low"], 2)

        # 3. Governance Risk (CPI score spread)
        cpi = db.execute(text("""
            SELECT MIN(score), MAX(score), AVG(score)
            FROM dh_country_risk_indices
            WHERE index_name = 'CPI' AND score IS NOT NULL
        """)).fetchone()
        if cpi and cpi[2]:
            avg_cpi = float(cpi[2])
            # Lower CPI → higher governance risk → higher EL
            drivers.append({
                "driver": "Governance Risk (CPI)",
                "low": round(-(float(cpi[1]) - avg_cpi) / max(avg_cpi, 1) * 12, 2),
                "high": round(-(float(cpi[0]) - avg_cpi) / max(avg_cpi, 1) * 12, 2),
                "swing": 0,
                "source": "Transparency International",
            })
            drivers[-1]["swing"] = round(drivers[-1]["high"] - drivers[-1]["low"], 2)

        # 4. Fragile State Index spread
        fsi = db.execute(text("""
            SELECT MIN(score), MAX(score), AVG(score)
            FROM dh_country_risk_indices
            WHERE index_name = 'FSI' AND score IS NOT NULL
        """)).fetchone()
        if fsi and fsi[2]:
            avg_fsi = float(fsi[2])
            # Higher FSI → more fragile → higher EL
            drivers.append({
                "driver": "State Fragility (FSI)",
                "low": round((float(fsi[0]) - avg_fsi) / max(avg_fsi, 1) * 10, 2),
                "high": round((float(fsi[1]) - avg_fsi) / max(avg_fsi, 1) * 10, 2),
                "swing": 0,
                "source": "Fund for Peace",
            })
            drivers[-1]["swing"] = round(drivers[-1]["high"] - drivers[-1]["low"], 2)

        # 5. Gender Inequality Index spread
        gii = db.execute(text("""
            SELECT MIN(score), MAX(score), AVG(score)
            FROM dh_country_risk_indices
            WHERE index_name = 'UNDP_GII' AND score IS NOT NULL
        """)).fetchone()
        if gii and gii[2]:
            avg_gii = float(gii[2])
            drivers.append({
                "driver": "Gender Inequality (GII)",
                "low": round((float(gii[0]) - avg_gii) / max(avg_gii, 1) * 8, 2),
                "high": round((float(gii[1]) - avg_gii) / max(avg_gii, 1) * 8, 2),
                "swing": 0,
                "source": "UNDP",
            })
            drivers[-1]["swing"] = round(drivers[-1]["high"] - drivers[-1]["low"], 2)

        # 6. Freedom House score spread
        fh = db.execute(text("""
            SELECT MIN(score), MAX(score), AVG(score)
            FROM dh_country_risk_indices
            WHERE index_name = 'FH_FIW' AND year = (
                SELECT MAX(year) FROM dh_country_risk_indices WHERE index_name = 'FH_FIW'
            ) AND score IS NOT NULL
        """)).fetchone()
        if fh and fh[2]:
            avg_fh = float(fh[2])
            # Higher FH score → less free → higher risk
            drivers.append({
                "driver": "Political Freedom (FH)",
                "low": round((float(fh[0]) - avg_fh) / max(avg_fh, 1) * 9, 2),
                "high": round((float(fh[1]) - avg_fh) / max(avg_fh, 1) * 9, 2),
                "swing": 0,
                "source": "Freedom House",
            })
            drivers[-1]["swing"] = round(drivers[-1]["high"] - drivers[-1]["low"], 2)

        # 7. Net Zero Commitment Impact
        nz = db.execute(text("""
            SELECT
                ROUND(COUNT(CASE WHEN net_zero_committed = true THEN 1 END)::numeric
                      / GREATEST(COUNT(*), 1) * 100, 1) AS nz_pct
            FROM dh_sbti_companies
        """)).fetchone()
        if nz and nz[0]:
            nz_pct = float(nz[0])
            drivers.append({
                "driver": "Net Zero Commitment",
                "low": round(-nz_pct * 0.15, 2),
                "high": round((100 - nz_pct) * 0.12, 2),
                "swing": 0,
                "source": "SBTi",
            })
            drivers[-1]["swing"] = round(drivers[-1]["high"] - drivers[-1]["low"], 2)

        # 8. CA100+ Alignment Impact
        ca = db.execute(text("""
            SELECT
                COUNT(*) AS total,
                COUNT(CASE WHEN indicator_1_score = 'Yes' THEN 1 END) AS disc_y,
                COUNT(CASE WHEN indicator_2_score = 'Yes' THEN 1 END) AS tgt_y
            FROM dh_ca100_assessments
        """)).fetchone()
        if ca and ca[0]:
            disc_pct = ca[1] / max(ca[0], 1) * 100
            tgt_pct = ca[2] / max(ca[0], 1) * 100
            avg_pct = (disc_pct + tgt_pct) / 2
            drivers.append({
                "driver": "CA100+ Compliance",
                "low": round(-avg_pct * 0.12, 2),
                "high": round((100 - avg_pct) * 0.1, 2),
                "swing": 0,
                "source": "CA100+",
            })
            drivers[-1]["swing"] = round(drivers[-1]["high"] - drivers[-1]["low"], 2)

        # Sort by swing descending
        drivers.sort(key=lambda d: d["swing"], reverse=True)
        return drivers

    except Exception:
        return []


# ── Utility ─────────────────────────────────────────────────────────────────

def _safe_scalar(db: Session, sql: str, default: int = 0) -> int:
    try:
        result = db.execute(text(sql)).scalar()
        return result or default
    except Exception:
        db.rollback()
        return default
