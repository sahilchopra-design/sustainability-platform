"""
China Trade Platform API — router prefix /api/v1/china-trade

Stakeholder-oriented endpoints:
  Exporter Intelligence  — /exporters/*
  CBAM Cross-Module      — /cbam/*  (auto-fill for CBAM Calculator)
  Supplier Framework     — /suppliers/*
  China ESG & ETS        — /esg-ets/*
  Trade Corridors        — /corridors/*
  Carbon Marketplace     — /marketplace/*
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/china-trade", tags=["China Trade Platform"])


# ─── Lazy engine import ────────────────────────────────────────────────────────

def _engine():
    from services.china_trade_engine import ChinaTradeEngine
    return ChinaTradeEngine()


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTER INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/exporters/search")
def search_exporters(
    query:              Optional[str]  = Query(default=None, description="Name or sector search"),
    sector:             Optional[str]  = Query(default=None, description="Steel|Aluminium|Cement|Chemicals|Power|Renewables"),
    cbam_applicable:    Optional[bool] = Query(default=None, description="Filter to CBAM-applicable sectors only"),
    min_cbam_readiness: Optional[int]  = Query(default=None, description="Minimum CBAM readiness score 0-100"),
    limit:              int            = Query(default=20, le=100),
):
    """
    Search Chinese exporters.
    Returns entity list with CBAM readiness score, carbon intensity, ETS registration.
    """
    try:
        return _engine().exporter.search_exporters(
            query=query, sector=sector,
            cbam_applicable=cbam_applicable,
            min_cbam_readiness=min_cbam_readiness,
            limit=limit,
        )
    except Exception as exc:
        logger.exception("exporter search error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/exporters/cbam-readiness-summary")
def exporter_cbam_readiness_summary():
    """
    Aggregate CBAM readiness distribution across Chinese exporters.
    Returns band counts (Leader / Advanced / Developing / Emerging) + avg score.
    """
    try:
        return _engine().exporter.get_cbam_readiness_summary()
    except Exception as exc:
        logger.exception("cbam readiness summary error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/exporters/{entity_name}/profile")
def get_exporter_profile(entity_name: str):
    """
    Full profile for a single Chinese exporter.
    Includes ESG tier, ETS position, CBAM readiness, export destinations.
    """
    try:
        return _engine().exporter.get_exporter_profile(entity_name)
    except Exception as exc:
        logger.exception("exporter profile error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# CBAM CROSS-MODULE (auto-fill endpoint for the existing CBAM Calculator)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/cbam/supplier-lookup")
def cbam_supplier_lookup(
    entity_name: Optional[str] = Query(default=None, description="Chinese counterparty name"),
    hs_code:     Optional[str] = Query(default=None, description="HS-6/HS-4 code, e.g. 720810"),
):
    """
    **Cross-module endpoint — CBAM Calculator auto-fill.**

    Given entity_name and/or hs_code, returns:
    - embedded_carbon_tco2_per_tonne
    - eu_benchmark_tco2_per_tonne
    - vs_eu_benchmark_pct
    - cets_price_eur_per_tco2
    - production_process
    - cbam_auto_fill dict (ready to inject into CBAM Calculator form)

    Called by the frontend CBAMPage when user clicks "Auto-fill from China Trade".
    """
    try:
        return _engine().cbam.supplier_lookup(entity_name=entity_name, hs_code=hs_code)
    except Exception as exc:
        logger.exception("cbam supplier lookup error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cbam/hs-benchmarks")
def cbam_hs_benchmarks():
    """EU CBAM Annex III embedded carbon benchmarks by HS-4 code. Includes current CETS price."""
    try:
        return _engine().cbam.get_hs_benchmark_table()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class CBAMLiabilityRequest(BaseModel):
    entity_name: str
    hs_code: str
    export_volume_tonnes: float
    eu_ets_price_eur: float = 65.0
    export_value_eur_mn: Optional[float] = None


@router.post("/cbam/calculate-liability")
def calculate_cbam_liability(req: CBAMLiabilityRequest):
    """
    Calculate net CBAM liability for a Chinese exporter × product × volume.
    Deducts CETS carbon costs already paid (EU CBAM Art.9).
    Returns: gross liability, CETS deduction, net liability, competitiveness risk band.
    """
    try:
        return _engine().cbam.calculate_cbam_liability(
            entity_name=req.entity_name,
            hs_code=req.hs_code,
            export_volume_tonnes=req.export_volume_tonnes,
            eu_ets_price_eur=req.eu_ets_price_eur,
            export_value_eur_mn=req.export_value_eur_mn,
        )
    except Exception as exc:
        logger.exception("cbam liability calc error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLIER FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/suppliers/requirements")
def get_supplier_requirements(
    framework:        Optional[str] = Query(default=None, description="CBAM|CSDDD|UK_CBT|SFDR"),
    product_category: Optional[str] = Query(default=None, description="Steel|Aluminium|Cement|Chemicals"),
):
    """
    Importer sustainability requirements (VW, ArcelorMittal, Airbus, BASF).
    Filterable by framework and product category.
    """
    try:
        return _engine().supplier.get_requirements(framework=framework, product_category=product_category)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/suppliers/rank")
def rank_suppliers(
    product_category: str            = Query(description="Steel|Aluminium|Cement|Chemicals"),
    max_intensity:    Optional[float] = Query(default=None, description="Max tCO2/tonne"),
    require_certified: bool           = Query(default=False, description="Require green certification"),
):
    """
    Rank Chinese exporters for a product category against importer requirements.
    Returns ranked list with readiness scores, carbon intensity, certifications.
    """
    try:
        return _engine().supplier.rank_suppliers(
            product_category=product_category,
            max_intensity=max_intensity,
            require_certified=require_certified,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# CHINA ESG & ETS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/esg-ets/dashboard")
def esg_dashboard(
    sector:   Optional[str] = Query(default=None),
    esg_tier: Optional[str] = Query(default=None, description="Leader|Advanced|Developing|Emerging"),
):
    """
    SSE/SZSE 2024 mandatory ESG disclosure dashboard.
    E/S/G pillar scores, overall ESG score, tier distribution.
    """
    try:
        return _engine().esg_ets.get_esg_dashboard(sector=sector, esg_tier=esg_tier)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/esg-ets/ndc-alignment")
def ndc_alignment(sector: Optional[str] = Query(default=None)):
    """
    China NDC sectoral pathway alignment.
    2030 CO2 peak + 2060 carbon neutrality targets vs current trajectory.
    """
    try:
        return _engine().esg_ets.get_ndc_alignment(sector=sector)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/esg-ets/ets-positions")
def ets_positions(sector: Optional[str] = Query(default=None)):
    """
    CETS (China national ETS) position summary.
    Allocation vs verified emissions, compliance status, price history 2021-2026.
    """
    try:
        return _engine().esg_ets.get_ets_positions(sector=sector)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/esg-ets/cets-price")
def cets_price():
    """Current CETS spot price (CNY and EUR) + 6-year history."""
    try:
        engine = _engine()
        return {
            "current_price_cny": engine.cbam.CETS_PRICE_CNY,
            "current_price_eur": engine.cbam.CETS_PRICE_EUR,
            "cny_eur_rate": engine.cbam.CNY_EUR_RATE,
            "eu_ets_price_eur": 65.0,
            "arbitrage_eur_per_tco2": round(65.0 - engine.cbam.CETS_PRICE_EUR, 2),
            "history": engine.esg_ets.CETS_PRICE_HISTORY,
            "as_of": "2026-03-05",
            "source": "CBEEX",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# TRADE CORRIDORS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/corridors")
def list_corridors():
    """
    All China bilateral trade corridors with embedded carbon and CBAM regime metadata.
    Returns: corridor list with trade value, volume, CBAM liability estimate.
    """
    try:
        return _engine().corridor.get_all_corridors()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/corridors/{origin}/{destination}")
def get_corridor(origin: str, destination: str):
    """Single corridor detail. origin/destination = ISO-2 country codes (e.g. CN/EU)."""
    try:
        return _engine().corridor.get_corridor(origin=origin, destination=destination)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/corridors/pl-impact/{sector}")
def corridor_pl_impact(
    sector: str,
    eu_ets_price_eur: float = Query(default=65.0, description="EU ETS price scenario"),
):
    """
    P&L CBAM impact for a sector across 6 EU ETS price scenarios (€40–€90).
    Returns net CBAM cost per tonne after CETS deduction and price impact %.
    """
    try:
        return _engine().corridor.get_pl_impact(sector=sector, eu_ets_price_eur=eu_ets_price_eur)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# CARBON MARKETPLACE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/marketplace/listings")
def marketplace_listings(
    listing_type: Optional[str] = Query(default=None, description="carbon_credit|ets_allowance|green_cert|cbam_cert|offset"),
    standard:     Optional[str] = Query(default=None, description="CETS|CCER|VCS|Gold Standard|CBI|CDM|CORSIA|ASI|EU_CBAM"),
    sector:       Optional[str] = Query(default=None),
    limit:        int           = Query(default=50, le=500),
):
    """
    Active carbon credit / ETS allowance / certificate listings.
    Filterable by type, standard, sector.
    """
    try:
        return _engine().marketplace.get_listings(
            listing_type=listing_type, standard=standard, sector=sector, limit=limit
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/marketplace/price-discovery")
def marketplace_price_discovery():
    """
    Carbon price benchmarks across 7 standards (CETS, CCER, VCS, CDM, EU ETS, CORSIA, Gold Standard).
    Spot + 1-year forward. Spread analysis + CBAM arbitrage note.
    """
    try:
        return _engine().marketplace.get_price_discovery()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/marketplace/stats")
def marketplace_stats():
    """China voluntary carbon market overview. Trading volume, CCER pipeline, active listings."""
    try:
        return _engine().marketplace.get_market_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM SUMMARY (dashboard card data)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/summary")
def platform_summary():
    """
    Cross-module platform summary for the China Trade dashboard landing card.
    Returns: exporter count, avg CBAM readiness, total marketplace volume,
             CETS price, top corridor CBAM liability, NDC on-track %.
    """
    try:
        eng = _engine()
        exporter_summary = eng.exporter.get_cbam_readiness_summary()
        market_stats     = eng.marketplace.get_market_stats()
        corridors        = eng.corridor.get_all_corridors()
        ndc              = eng.esg_ets.get_ndc_alignment()

        on_track = sum(1 for p in ndc.get("pathways", []) if p.get("on_track") is True)
        total_p  = len(ndc.get("pathways", []))

        top_corridor = corridors["corridors"][0] if corridors.get("corridors") else {}

        return {
            "exporter_count": exporter_summary.get("total_exporters", 12),
            "avg_cbam_readiness_score": exporter_summary.get("avg_cbam_readiness", 60.4),
            "marketplace_listings_active": market_stats.get("active_listings", 6),
            "total_listed_volume_tco2": market_stats.get("total_volume_listed_tco2", 0),
            "cets_price_cny": eng.cbam.CETS_PRICE_CNY,
            "cets_price_eur": eng.cbam.CETS_PRICE_EUR,
            "eu_ets_price_eur": 65.0,
            "cbam_arbitrage_eur_per_tco2": round(65.0 - eng.cbam.CETS_PRICE_EUR, 2),
            "top_corridor_name": top_corridor.get("corridor_name", "China → EU"),
            "top_corridor_cbam_liability_eur_mn": top_corridor.get("annual_cbam_liability_est_eur_mn", 4280.0),
            "ndc_on_track_pct": round(on_track / total_p * 100, 1) if total_p else 0,
            "china_ndc_peak_year": 2030,
            "china_ndc_neutrality_year": 2060,
        }
    except Exception as exc:
        logger.exception("platform summary error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-MODULE INTEGRATION
# Bridges China Trade data into CBAM Calculator, Supply Chain, Financial Risk,
# Regulatory, Scenario Analysis, and Portfolio Analytics modules.
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/cross-module/entity-hub/{entity_name}")
def entity_hub(entity_name: str):
    """
    **Cross-module entity hub.**
    Returns a unified data card for a Chinese entity aggregating:
    CBAM readiness, ETS position, ESG score, export products, CBAM liability.
    Includes deep-link hrefs for all connected platform modules.
    """
    try:
        return _engine().cross_module.get_entity_hub(entity_name)
    except Exception as exc:
        logger.exception("entity hub error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cross-module/scope3-cat1")
def cross_module_scope3_cat1(sector: Optional[str] = Query(default=None)):
    """
    **Cross-module — Supply Chain (Scope 3 Cat 1).**
    GHG Protocol Category 1 emission factors for Chinese exported goods,
    sourced from CETS verified emissions. Consumed by the Supply Chain module
    Scope 3 calculator for purchased-goods emission factor lookup.
    """
    try:
        return _engine().cross_module.get_scope3_cat1(sector=sector)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cross-module/ecl-cbam-overlay")
def cross_module_ecl_cbam():
    """
    **Cross-module — Financial Risk (IFRS 9 ECL).**
    Maps Chinese exporter CBAM readiness scores to IFRS 9 PD/LGD uplift bands.
    Used by the Financial Risk module to overlay CBAM transition risk onto
    ECL staging for China-exposed lending/investment portfolios.
    """
    try:
        return _engine().cross_module.get_ecl_cbam_overlay()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cross-module/regulatory-csrd")
def cross_module_regulatory_csrd():
    """
    **Cross-module — Regulatory (CSRD / SFDR / ISSB).**
    Maps SSE/SZSE 2024 mandatory ESG disclosures to CSRD ESRS E1, SFDR PAI,
    and ISSB S2 data points.  Consumed by the Regulatory module China ESG panel
    to show coverage gaps and cross-standard alignment.
    """
    try:
        return _engine().cross_module.get_regulatory_csrd()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cross-module/scenario-cets-ngfs")
def cross_module_scenario_ngfs():
    """
    **Cross-module — Scenario Analysis (NGFS × CETS).**
    CETS price trajectories under NGFS v4 Net Zero 2050, Delayed Transition,
    Below 2 Degrees, and Current Policies scenarios.
    Used by the Scenario Analysis module for China transition risk overlays.
    """
    try:
        return _engine().cross_module.get_scenario_cets_ngfs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cross-module/portfolio-cbam")
def cross_module_portfolio_cbam():
    """
    **Cross-module — Portfolio Analytics (CBAM exposure roll-up).**
    Sector-level aggregation of CBAM gross/net liability across all tracked
    Chinese exporters.  Consumed by Portfolio Analytics for China CBAM risk
    roll-up cards and heatmaps.
    """
    try:
        return _engine().cross_module.get_portfolio_cbam()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
