"""
Portfolio Analytics Engine — Real PCAF Computation
Sprint 2: Kill the Mock

Replaces the previous sample-data version (which used import random
and hardcoded portfolios).  This engine:

  1. Loads assets from assets_pg, including the PCAF columns added by
     migration 019 (evic_eur, scope1_tco2e, scope2_tco2e, scope3_tco2e,
     pcaf_dqs, annual_revenue_eur, entity_lei, isin, pcaf_asset_class,
     sbti_aligned, transition_plan_status).

  2. For each asset, resolves emission data via the DQS hierarchy:
       DQS 3 — scope1/2/3 columns populated in assets_pg
       DQS 4 — Data Hub LEI lookup (get_emissions)
       DQS 5 — sector-average intensity x exposure (fallback estimate)

  3. Delegates to PCAFWACIEngine (pcaf_waci_engine.py) for standard-
     compliant financed emissions, WACI, carbon footprint, temperature
     alignment, and SFDR PAI indicators.

  4. Writes per-sector WACI results to pcaf_time_series for the
     glidepath tracker and platform benchmark flywheel.

  5. Triggers the alert engine to evaluate glidepath deviation and DQS.

  6. Returns PortfolioPCAFResult plus a richer dict suitable for the API.

All monetary arithmetic uses Decimal.  DB access is via SQLAlchemy text()
queries (the new tables from migrations 018/019 are not in the ORM yet).
"""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy import text

logger = logging.getLogger(__name__)


# ── Sector-average emission intensity fallback (DQS 5) ────────────────────────
# Unit: tCO2e per EUR million of revenue.
# Calibrated from IEA/PCAF sector benchmarks (2022 vintage).
# Used only when no primary data or Data Hub record is available.

_SECTOR_INTENSITY_TCO2E_MEUR: Dict[str, float] = {
    "Energy":                            850.0,
    "Utilities":                         650.0,
    "Oil Gas & Consumable Fuels":       1200.0,
    "Coal & Consumable Fuels":          2200.0,
    "Oil Gas Exploration & Production": 1100.0,
    "Integrated Oil & Gas":             1150.0,
    "Materials":                         420.0,
    "Steel":                             980.0,
    "Cement":                           1100.0,
    "Chemicals":                         390.0,
    "Metals & Mining":                   380.0,
    "Industrials":                       180.0,
    "Aerospace & Defense":               140.0,
    "Construction & Engineering":        260.0,
    "Transportation":                    320.0,
    "Airlines":                          540.0,
    "Marine":                            410.0,
    "Ground Transportation":             240.0,
    "Real Estate":                       115.0,
    "Commercial Real Estate":            130.0,
    "Residential":                        95.0,
    "Financials":                         22.0,
    "Banks":                              18.0,
    "Insurance":                          15.0,
    "Information Technology":             48.0,
    "Communication Services":             35.0,
    "Consumer Staples":                  110.0,
    "Consumer Discretionary":             90.0,
    "Health Care":                        65.0,
    "Sovereign":                          12.0,
    "Unknown":                           200.0,
}


# ── PCAF asset class mapping from AssetPG.asset_type ─────────────────────────

_ASSET_TYPE_TO_PCAF: Dict[str, str] = {
    "Bond":           "corporate_bonds",
    "Loan":           "business_loans",
    "Equity":         "listed_equity",
    "Project":        "project_finance",
    "Mortgage":       "mortgages",
    "Real Estate":    "commercial_real_estate",
    "Infrastructure": "infrastructure",
    "Vehicle":        "vehicle_loans",
    "Sovereign":      "sovereign_bonds",
}


def _get_db_engine():
    """Lazy import to avoid circular imports at module load."""
    try:
        from db.base import engine as db_engine
        return db_engine
    except Exception as exc:
        logger.error("Cannot connect to database: %s", exc)
        return None


# ── DQS resolution ────────────────────────────────────────────────────────────

def _resolve_emissions(asset: Dict[str, Any]) -> Tuple[Decimal, Decimal, Decimal, int]:
    """
    Resolve Scope 1, 2, 3 emissions and PCAF DQS for one asset row.

    Priority:
      DQS 3 -- scope1/2/3 columns populated in assets_pg
      DQS 4 -- Data Hub LEI lookup
      DQS 5 -- sector-average intensity x revenue (estimated proxy)

    Returns (scope1_tco2e, scope2_tco2e, scope3_tco2e, dqs_int)
    """
    # DQS 3 -- primary columns present in assets_pg (migration 019)
    if asset.get("scope1_tco2e") is not None:
        return (
            Decimal(str(asset["scope1_tco2e"])),
            Decimal(str(asset.get("scope2_tco2e") or 0)),
            Decimal(str(asset.get("scope3_tco2e") or 0)),
            3,
        )

    # DQS 4 -- Data Hub LEI lookup
    lei = asset.get("entity_lei")
    if lei:
        try:
            from services.data_hub_client import get_emissions as hub_emissions
            hub = hub_emissions(lei)
            if hub:
                return (
                    Decimal(str(hub.get("scope1") or 0)),
                    Decimal(str(hub.get("scope2") or 0)),
                    Decimal(str(hub.get("scope3") or 0)),
                    4,
                )
        except Exception as exc:
            logger.debug("Data Hub lookup failed for LEI %s: %s", lei, exc)

    # DQS 5 -- sector average x revenue
    sector    = asset.get("company_sector", "Unknown")
    intensity = Decimal(str(_SECTOR_INTENSITY_TCO2E_MEUR.get(sector, 200.0)))
    revenue   = Decimal(str(
        asset.get("annual_revenue_eur")
        or asset.get("exposure")
        or 0
    ))
    revenue_meur  = revenue / Decimal("1000000")
    estimated_s1  = (intensity * revenue_meur).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return (estimated_s1, Decimal("0"), Decimal("0"), 5)


# ── Write pcaf_time_series ────────────────────────────────────────────────────

def _write_time_series(
    db_engine,
    portfolio_id: str,
    sector: str,
    metric_type: str,
    actual_value: Decimal,
    glidepath_value: Optional[Decimal],
    unit: str,
    dqs_score: Decimal,
    data_source: str,
    reporting_year: int,
    entity_lei: Optional[str] = None,
) -> None:
    """Insert one record into pcaf_time_series. No-ops if table doesn't exist."""
    try:
        with db_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO pcaf_time_series
                    (portfolio_id, entity_lei, sector, metric_type, reporting_year,
                     actual_value, glidepath_value, unit, dqs_score, data_source,
                     is_benchmark, created_at)
                VALUES
                    (:portfolio_id, :entity_lei, :sector, :metric_type, :reporting_year,
                     :actual_value, :glidepath_value, :unit, :dqs_score, :data_source,
                     false, now())
            """), {
                "portfolio_id":    portfolio_id,
                "entity_lei":      entity_lei,
                "sector":          sector,
                "metric_type":     metric_type,
                "reporting_year":  reporting_year,
                "actual_value":    float(actual_value),
                "glidepath_value": float(glidepath_value) if glidepath_value else None,
                "unit":            unit,
                "dqs_score":       float(dqs_score),
                "data_source":     data_source,
            })
            conn.commit()
    except Exception as exc:
        logger.warning("pcaf_time_series write failed: %s", exc)


# ── Main calculation function ─────────────────────────────────────────────────

def run_pcaf_calculation(portfolio_id: str) -> Dict[str, Any]:
    """
    Execute a full PCAF Standard v2.0 financed emissions calculation for
    the given portfolio.

    Returns a serialisable dict with keys:
      data_available, portfolio_id, portfolio_name, reporting_year,
      portfolio_summary, dqs_distribution, sector_breakdown,
      investee_results, pai_indicators, validation_summary,
      parse_errors, engine_version, calculation_timestamp
    """
    db_engine = _get_db_engine()
    if db_engine is None:
        return {"error": "Database unavailable", "data_available": False}

    reporting_year = datetime.now(timezone.utc).year - 1

    # ── Load assets ──────────────────────────────────────────────────────────
    try:
        with db_engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    a.id, a.company_name, a.company_sector, a.asset_type,
                    a.exposure, a.market_value,
                    a.evic_eur, a.scope1_tco2e, a.scope2_tco2e, a.scope3_tco2e,
                    a.pcaf_dqs, a.attribution_factor, a.annual_revenue_eur,
                    a.entity_lei, a.isin, a.sbti_aligned, a.net_zero_committed,
                    a.transition_plan_status, a.pcaf_asset_class,
                    p.name AS portfolio_name
                FROM assets_pg a
                JOIN portfolios_pg p ON p.id = a.portfolio_id
                WHERE a.portfolio_id = :pid
                ORDER BY a.company_name
            """), {"pid": portfolio_id}).mappings().all()
    except Exception as exc:
        logger.warning(
            "PCAF columns not available (migration 019 pending?) for portfolio %s: %s",
            portfolio_id, exc,
        )
        # Fallback: load base columns only
        try:
            with db_engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT
                        a.id, a.company_name, a.company_sector, a.asset_type,
                        a.exposure, a.market_value,
                        NULL AS evic_eur, NULL AS scope1_tco2e, NULL AS scope2_tco2e,
                        NULL AS scope3_tco2e, NULL AS pcaf_dqs, NULL AS attribution_factor,
                        NULL AS annual_revenue_eur, NULL AS entity_lei, NULL AS isin,
                        NULL AS sbti_aligned, NULL AS net_zero_committed,
                        NULL AS transition_plan_status, NULL AS pcaf_asset_class,
                        p.name AS portfolio_name
                    FROM assets_pg a
                    JOIN portfolios_pg p ON p.id = a.portfolio_id
                    WHERE a.portfolio_id = :pid
                    ORDER BY a.company_name
                """), {"pid": portfolio_id}).mappings().all()
        except Exception as exc2:
            logger.error("Asset load completely failed: %s", exc2)
            return {"error": f"Failed to load assets: {exc2}", "data_available": False}

    if not rows:
        return {
            "error": None,
            "data_available": False,
            "portfolio_summary": None,
            "message": "No assets found. Add assets to compute PCAF metrics.",
            "investee_count": 0,
        }

    portfolio_name = rows[0]["portfolio_name"]
    assets = [dict(r) for r in rows]

    # ── Build InvesteeData list ───────────────────────────────────────────────
    from services.pcaf_waci_engine import (
        PCAFWACIEngine, InvesteeData, PCAFAssetClass, DataQualityScore
    )

    investees: List[InvesteeData] = []
    dqs_distribution: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    parse_errors: List[str] = []

    for asset in assets:
        try:
            s1, s2, s3, dqs_int = _resolve_emissions(asset)
            dqs_distribution[dqs_int] = dqs_distribution.get(dqs_int, 0) + 1

            raw_ac    = asset.get("pcaf_asset_class") or asset.get("asset_type", "Loan")
            pcaf_ac_s = _ASSET_TYPE_TO_PCAF.get(raw_ac, "business_loans")
            try:
                pcaf_ac = PCAFAssetClass(pcaf_ac_s)
            except ValueError:
                pcaf_ac = PCAFAssetClass.BUSINESS_LOANS

            outstanding = Decimal(str(asset.get("exposure") or 0))
            evic        = Decimal(str(asset.get("evic_eur") or 0))
            revenue     = Decimal(str(
                asset.get("annual_revenue_eur") or asset.get("exposure") or 0
            ))
            total_equity = evic if evic > Decimal("0") else outstanding

            investees.append(InvesteeData(
                company_name           = asset["company_name"],
                sector_gics            = asset.get("company_sector", "Unknown"),
                country_iso            = "XX",
                asset_class            = pcaf_ac,
                outstanding_amount_eur = outstanding,
                enterprise_value_eur   = evic if evic > Decimal("0") else outstanding,
                total_equity_eur       = total_equity,
                total_debt_eur         = Decimal("0"),
                annual_revenue_eur     = revenue,
                scope1_co2e_tonnes     = s1,
                scope2_co2e_tonnes     = s2,
                scope3_co2e_tonnes     = s3,
                data_quality           = DataQualityScore(dqs_int),
                reporting_year         = reporting_year,
                isin                   = asset.get("isin"),
            ))
        except Exception as exc:
            msg = f"{asset.get('company_name', 'unknown')}: {exc}"
            logger.error("InvesteeData build failed -- %s", msg)
            parse_errors.append(msg)

    if not investees:
        return {
            "error": "No valid investee records could be built.",
            "parse_errors": parse_errors,
            "data_available": False,
        }

    # ── Run PCAF engine ───────────────────────────────────────────────────────
    pcaf_engine = PCAFWACIEngine()
    portfolio_result = pcaf_engine.calculate_portfolio_financed_emissions(investees)
    pai             = pcaf_engine.generate_pai_metrics(investees)

    # ── Per-investee breakdown ────────────────────────────────────────────────
    investee_results = []
    for inv in investees:
        try:
            res = pcaf_engine._calculate_investee_financed_emissions(inv)
            investee_results.append({
                "company_name":              res.investee_name,
                "asset_class":               res.asset_class.value,
                "sector_gics":               inv.sector_gics,
                "attribution_factor":        float(res.attribution_factor),
                "financed_scope1_tco2e":     float(res.financed_scope1_co2e),
                "financed_scope2_tco2e":     float(res.financed_scope2_co2e),
                "financed_scope3_tco2e":     float(res.financed_scope3_co2e),
                "financed_total_tco2e":      float(res.financed_total_co2e),
                "waci_intensity_tco2e_meur": float(res.waci_scope12_tco2e_meur),
                "data_quality_score":        res.data_quality_score.value,
                "outstanding_eur":           float(inv.outstanding_amount_eur),
            })
        except Exception as exc:
            logger.warning("Per-investee breakdown failed for %s: %s", inv.company_name, exc)

    # ── Sector-level WACI ─────────────────────────────────────────────────────
    total_aum = portfolio_result.total_aum_eur
    sector_waci: Dict[str, Dict[str, Any]] = {}

    for inv in investees:
        sector = inv.sector_gics
        weight = (
            inv.outstanding_amount_eur / total_aum
            if total_aum > Decimal("0") else Decimal("0")
        )
        rev_meur = inv.annual_revenue_eur / Decimal("1000000")
        s12_int  = (
            (inv.scope1_co2e_tonnes + inv.scope2_co2e_tonnes) / rev_meur
            if rev_meur > Decimal("0") else Decimal("0")
        )
        if sector not in sector_waci:
            sector_waci[sector] = {
                "outstanding_eur": Decimal("0"),
                "weight_pct":      Decimal("0"),
                "waci_contrib":    Decimal("0"),
                "asset_count":     0,
            }
        e = sector_waci[sector]
        e["outstanding_eur"] += inv.outstanding_amount_eur
        e["waci_contrib"]    += weight * s12_int
        e["asset_count"]     += 1

    for sector, e in sector_waci.items():
        e["weight_pct"] = (
            (e["outstanding_eur"] / total_aum * Decimal("100"))
            .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_aum > Decimal("0") else Decimal("0")
        )

    # ── Write pcaf_time_series ────────────────────────────────────────────────
    try:
        for sector, e in sector_waci.items():
            glidepath_val: Optional[Decimal] = None
            try:
                from services.data_hub_client import get_glidepath
                gp_series = get_glidepath(sector)
                if gp_series:
                    gp_y = min(
                        gp_series,
                        key=lambda g: abs(int(g.get("year", 9999)) - reporting_year),
                    )
                    if gp_y:
                        glidepath_val = Decimal(str(gp_y.get("glidepath", 0) or 0))
            except Exception:
                pass

            _write_time_series(
                db_engine, portfolio_id, sector, "waci",
                e["waci_contrib"], glidepath_val,
                "tCO2e_per_MEUR", portfolio_result.weighted_data_quality,
                "pcaf_waci_engine_v2", reporting_year,
            )

        _write_time_series(
            db_engine, portfolio_id, "portfolio", "waci",
            portfolio_result.portfolio_waci_scope12, None,
            "tCO2e_per_MEUR", portfolio_result.weighted_data_quality,
            "pcaf_waci_engine_v2", reporting_year,
        )
        _write_time_series(
            db_engine, portfolio_id, "portfolio", "carbon_footprint",
            portfolio_result.portfolio_carbon_footprint, None,
            "tCO2e_per_MEUR_invested", portfolio_result.weighted_data_quality,
            "pcaf_waci_engine_v2", reporting_year,
        )
    except Exception as exc:
        logger.warning("pcaf_time_series writes failed (non-critical): %s", exc)

    # ── Trigger alert engine ──────────────────────────────────────────────────
    try:
        from services.alert_engine import evaluate_dqs, evaluate_glidepath_deviation

        evaluate_dqs(
            portfolio_id=portfolio_id,
            weighted_dqs=float(portfolio_result.weighted_data_quality),
            coverage_pct=float(portfolio_result.coverage_pct) / 100.0,
        )

        for sector, e in sector_waci.items():
            try:
                from services.data_hub_client import get_glidepath
                gp_series = get_glidepath(sector)
                if gp_series:
                    gp_y = min(
                        gp_series,
                        key=lambda g: abs(int(g.get("year", 9999)) - reporting_year),
                    )
                    if gp_y and gp_y.get("glidepath"):
                        evaluate_glidepath_deviation(
                            portfolio_id=portfolio_id,
                            sector=sector,
                            actual_waci=float(e["waci_contrib"]),
                            glidepath_waci=float(gp_y["glidepath"]),
                        )
            except Exception:
                pass
    except Exception as exc:
        logger.warning("Alert evaluation failed (non-critical): %s", exc)

    # ── Build output ──────────────────────────────────────────────────────────
    sector_breakdown_out = [
        {
            "sector":          sector,
            "outstanding_eur": float(e["outstanding_eur"]),
            "weight_pct":      float(e["weight_pct"]),
            "waci_contrib":    float(e["waci_contrib"]),
            "asset_count":     e["asset_count"],
        }
        for sector, e in sorted(
            sector_waci.items(),
            key=lambda kv: float(kv[1]["outstanding_eur"]),
            reverse=True,
        )
    ]

    return {
        "data_available":  True,
        "portfolio_id":    portfolio_id,
        "portfolio_name":  portfolio_name,
        "reporting_year":  reporting_year,
        "portfolio_summary": {
            "total_financed_scope1_tco2e":  float(portfolio_result.total_financed_scope1_co2e),
            "total_financed_scope2_tco2e":  float(portfolio_result.total_financed_scope2_co2e),
            "total_financed_scope3_tco2e":  float(portfolio_result.total_financed_scope3_co2e),
            "total_financed_co2e_tco2e":    float(portfolio_result.total_financed_co2e),
            "portfolio_waci_scope12":        float(portfolio_result.portfolio_waci_scope12),
            "portfolio_waci_scope123":       float(portfolio_result.portfolio_waci_scope123),
            "portfolio_carbon_footprint":    float(portfolio_result.portfolio_carbon_footprint),
            "total_aum_eur":                 float(portfolio_result.total_aum_eur),
            "covered_aum_eur":               float(portfolio_result.covered_aum_eur),
            "coverage_pct":                  float(portfolio_result.coverage_pct),
            "weighted_data_quality_score":   float(portfolio_result.weighted_data_quality),
            "implied_temperature_c":         float(portfolio_result.temperature_score_c),
            "investee_count":                portfolio_result.investee_count,
        },
        "dqs_distribution":   dqs_distribution,
        "sector_breakdown":   sector_breakdown_out,
        "investee_results":   investee_results,
        "pai_indicators":     pai,
        "validation_summary": portfolio_result.validation_summary,
        "parse_errors":       parse_errors,
        "engine_version":     "PCAF-Analytics-Engine v2.0 (Sprint-2 real-data)",
        "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_latest_pcaf_results(portfolio_id: str) -> Dict[str, Any]:
    """
    Return the most recent PCAF metrics from pcaf_time_series (cached).
    Runs the engine on-demand if no cached record exists.
    """
    db_engine = _get_db_engine()
    if db_engine is None:
        return {"error": "Database unavailable", "data_available": False}

    reporting_year = datetime.now(timezone.utc).year - 1

    try:
        with db_engine.connect() as conn:
            cnt = conn.execute(text(
                "SELECT COUNT(*) FROM pcaf_time_series WHERE portfolio_id = :pid"
            ), {"pid": portfolio_id}).scalar()

            if cnt and cnt > 0:
                metrics = conn.execute(text("""
                    SELECT metric_type, actual_value, glidepath_value, dqs_score, unit
                    FROM pcaf_time_series
                    WHERE portfolio_id = :pid AND sector = 'portfolio'
                    ORDER BY created_at DESC LIMIT 10
                """), {"pid": portfolio_id}).mappings().all()

                sectors = conn.execute(text("""
                    SELECT sector, actual_value AS waci_contrib,
                           glidepath_value, dqs_score, reporting_year
                    FROM pcaf_time_series
                    WHERE portfolio_id = :pid
                      AND metric_type = 'waci'
                      AND sector != 'portfolio'
                      AND reporting_year = :yr
                    ORDER BY actual_value DESC LIMIT 20
                """), {"pid": portfolio_id, "yr": reporting_year}).mappings().all()

                waci_val, cf_val, dqs_val = None, None, None
                for m in metrics:
                    if m["metric_type"] == "waci" and waci_val is None:
                        waci_val = float(m["actual_value"]) if m["actual_value"] else None
                        dqs_val  = float(m["dqs_score"])   if m["dqs_score"]   else None
                    elif m["metric_type"] == "carbon_footprint" and cf_val is None:
                        cf_val = float(m["actual_value"]) if m["actual_value"] else None

                return {
                    "data_available":               True,
                    "portfolio_id":                 portfolio_id,
                    "from_cache":                   True,
                    "reporting_year":               reporting_year,
                    "portfolio_waci_scope12":        waci_val,
                    "portfolio_carbon_footprint":    cf_val,
                    "weighted_data_quality_score":   dqs_val,
                    "sector_waci_series":            [dict(s) for s in sectors],
                    "message":                       "Cached. Run POST /pcaf-run to refresh.",
                }
    except Exception as exc:
        logger.info("pcaf_time_series read failed (table may not exist yet): %s", exc)

    # No cache — run on demand
    return run_pcaf_calculation(portfolio_id)


def get_waci_history(portfolio_id: str, years: int = 10) -> List[Dict[str, Any]]:
    """Return year-by-year WACI vs glidepath for sparkline charts."""
    db_engine = _get_db_engine()
    if db_engine is None:
        return []

    try:
        with db_engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT reporting_year, actual_value AS waci,
                       glidepath_value AS glidepath, dqs_score
                FROM pcaf_time_series
                WHERE portfolio_id = :pid
                  AND metric_type = 'waci'
                  AND sector = 'portfolio'
                ORDER BY reporting_year ASC
                LIMIT :lim
            """), {"pid": portfolio_id, "lim": years}).mappings().all()

            return [
                {
                    "period":    r["reporting_year"],
                    "waci":      float(r["waci"])      if r["waci"]      else None,
                    "glidepath": float(r["glidepath"]) if r["glidepath"] else None,
                    "dqs_score": float(r["dqs_score"]) if r["dqs_score"] else None,
                }
                for r in rows
            ]
    except Exception as exc:
        logger.debug("WACI history query failed: %s", exc)
        return []


# ─── Compatibility shim ────────────────────────────────────────────────────────
# Legacy interface expected by universal_exports.py (predates Sprint 2 rewrite).
# These wrappers delegate to the module-level functions above.

def get_portfolio(portfolio_id: str) -> Dict[str, Any]:
    """Return portfolio metadata from portfolios_pg."""
    db_engine = _get_db_engine()
    if db_engine is None:
        return {"id": portfolio_id, "name": "Unknown Portfolio"}
    try:
        with db_engine.connect() as conn:
            row = conn.execute(text(
                "SELECT id, name, description, created_at "
                "FROM portfolios_pg WHERE id = :pid LIMIT 1"
            ), {"pid": portfolio_id}).mappings().first()
            if not row:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            return dict(row)
    except ValueError:
        raise
    except Exception as exc:
        logger.warning("get_portfolio failed: %s", exc)
        return {"id": portfolio_id, "name": "Unknown", "error": str(exc)}


def get_holdings(portfolio_id: str) -> List[Dict[str, Any]]:
    """Return asset holdings for a portfolio from assets_pg."""
    db_engine = _get_db_engine()
    if db_engine is None:
        return []
    try:
        with db_engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, company_name, sector, country, exposure, outstanding_amount, "
                "       scope1_emissions, scope2_emissions, scope3_emissions "
                "FROM assets_pg WHERE portfolio_id = :pid ORDER BY exposure DESC"
            ), {"pid": portfolio_id}).mappings().all()
            return [dict(r) for r in rows]
    except Exception as exc:
        logger.warning("get_holdings failed: %s", exc)
        return []


class _ReportSubEngine:
    """Minimal report generator used by PortfolioAggregationEngine.reports."""

    def generate_report(
        self,
        portfolio_id: str,
        report_type: Any,
        include_property_details: bool = True,
    ) -> Dict[str, Any]:
        import datetime as _dt
        pcaf = run_pcaf_calculation(portfolio_id)
        portfolio = get_portfolio(portfolio_id)
        holdings = get_holdings(portfolio_id)
        return {
            "report_type":    str(report_type),
            "portfolio_id":   portfolio_id,
            "portfolio":      portfolio,
            "holdings_count": len(holdings),
            "pcaf_summary":   pcaf,
            "generated_at":   _dt.datetime.utcnow().isoformat(),
        }


class PortfolioAggregationEngine:
    """
    Compatibility class preserving the interface expected by universal_exports.py.
    Delegates to the module-level functions introduced in the Sprint 2 rewrite.
    """

    def __init__(self) -> None:
        self.reports = _ReportSubEngine()

    def get_dashboard(self, portfolio_id: str) -> Dict[str, Any]:
        pcaf = run_pcaf_calculation(portfolio_id)
        return {"portfolio_id": portfolio_id, "pcaf": pcaf}

    def compare_scenarios(
        self, portfolio_id: str, scenario_ids: List[str]
    ) -> Dict[str, Any]:
        return {
            "portfolio_id": portfolio_id,
            "scenario_ids": scenario_ids,
            "comparison":   [run_pcaf_calculation(portfolio_id)],
        }
