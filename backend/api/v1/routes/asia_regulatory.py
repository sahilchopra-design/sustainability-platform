"""
Asia Regulatory API — router prefix /api/v1/asia-regulatory

Frameworks:
  • BRSR Core   (India / SEBI)              — /brsr/*
  • HKMA GS-1   (Hong Kong)                — /hkma/*
  • BoJ Scenarios (Japan)                   — /boj/*
  • ASEAN Taxonomy v3                       — /asean/*
  • PBoC Green Finance (GBEPC 2021)        — /pboc/*
  • CBI Market (Climate Bond Initiative)   — /cbi/*
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/asia-regulatory", tags=["Asia Regulatory"])

# ─── Lazy engine imports ───────────────────────────────────────────────────────

def _engine():
    from services.asia_regulatory_engine import AsiaRegulatoryEngine
    return AsiaRegulatoryEngine()


def _cbi():
    from services.cbi_data_client import CBIDataClient
    return CBIDataClient()


# ═══════════════════════════════════════════════════════════════════════════════
# BRSR (India — SEBI LODR)
# NOTE: static route /brsr/top-1000 MUST precede /brsr/{entity_id}
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/brsr/top-1000")
def brsr_top_1000_summary():
    """
    Summary across all BRSR disclosures in DB (SEBI Top 1000 listed companies).
    Returns: total entities, complete-reporting count, assurance %, avg P6 env score.
    """
    try:
        return _engine().brsr.get_top_1000_summary()
    except Exception as exc:
        logger.exception("brsr top1000 error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/brsr/{entity_id}/scorecard")
def get_brsr_scorecard(entity_id: str):
    """
    Computed BRSR scorecard:
    - Weighted overall score (0-100)
    - Readiness band (Initial → Leader)
    - Per-principle scores (P1–P9)
    - Core KPI availability
    - Assurance status
    """
    try:
        return _engine().brsr.get_brsr_scorecard(entity_id)
    except Exception as exc:
        logger.exception("brsr scorecard error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/brsr/{entity_id}")
def get_brsr_disclosure(entity_id: str):
    """Full BRSR disclosure record for an entity."""
    try:
        return _engine().brsr.get_brsr_disclosure(entity_id)
    except Exception as exc:
        logger.exception("brsr disclosure error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# HKMA GS-1 (Hong Kong)
# NOTE: static route /hkma/sector-benchmark MUST precede /hkma/{entity_id}
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/hkma/sector-benchmark")
def hkma_sector_benchmark():
    """Aggregate HKMA maturity by entity type (bank / insurer / securities)."""
    try:
        return _engine().hkma.get_sector_benchmark()
    except Exception as exc:
        logger.exception("hkma benchmark error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/hkma/{entity_id}")
def get_hkma_assessment(entity_id: str):
    """
    HKMA GS-1 climate risk assessment for a HK-supervised entity.
    Returns 4-pillar maturity scores (Governance, Strategy, Risk Mgmt, Metrics),
    overall maturity, GAR, TCFD status.
    """
    try:
        return _engine().hkma.get_assessment(entity_id)
    except Exception as exc:
        logger.exception("hkma assessment error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/hkma/{entity_id}/stress-test")
def run_hkma_stress_test(
    entity_id: str,
    scenarios: Optional[List[str]] = Query(default=None),
):
    """
    Run HKMA climate stress test for <2°C / 2–3°C / >3°C scenarios.
    Returns sector-level credit loss %, PD change, LGD change, NII impact, CAR impact.
    """
    try:
        return _engine().hkma.run_stress_test(entity_id, scenarios)
    except Exception as exc:
        logger.exception("hkma stress test error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# Bank of Japan (Japan)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/boj/{entity_id}/scenarios")
def get_boj_entity_scenarios(entity_id: str):
    """
    BoJ climate scenario results for a Japanese FI.
    Covers: Transition_1.5C, Transition_2C, Physical_2C, Physical_4C
    × horizons 2030 / 2050 / 2100
    × sectors (Energy, Manufacturing, Transport, Real Estate, Agriculture).
    """
    try:
        return _engine().boj.get_entity_scenarios(entity_id)
    except Exception as exc:
        logger.exception("boj scenarios error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/boj/sector-impact/{sector}")
def get_boj_sector_impact(sector: str):
    """
    BoJ reference impact parameters for a given sector across all scenarios and horizons.
    Sector names: Energy | Manufacturing | Transport | Real Estate | Agriculture
    """
    try:
        return _engine().boj.get_sector_impact(sector)
    except Exception as exc:
        logger.exception("boj sector impact error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# ASEAN Taxonomy v3
# NOTE: static routes /asean/member-states and /asean/focus-areas MUST precede
#       /asean/{entity_id}/taxonomy and /asean/member-state/{country_code}
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/asean/member-states")
def list_asean_member_states():
    """List all supported ASEAN member state codes."""
    return {"member_states": _engine().asean.MEMBER_STATES}


@router.get("/asean/focus-areas")
def list_asean_focus_areas():
    """List all 5 ASEAN Taxonomy focus areas."""
    return {"focus_areas": _engine().asean.FOCUS_AREAS}


@router.get("/asean/member-state/{country_code}")
def get_asean_member_state_coverage(country_code: str):
    """
    ASEAN Taxonomy coverage for a member state (SG/MY/TH/ID/PH/VN/MM/BN/LA/KH).
    Returns: total activities, Green/Amber/Red %, top activities.
    """
    try:
        return _engine().asean.get_member_state_coverage(country_code)
    except Exception as exc:
        logger.exception("asean member state error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/asean/{entity_id}/taxonomy")
def get_asean_entity_taxonomy(entity_id: str):
    """
    ASEAN Taxonomy v3 assessment for an entity.
    Returns activities with Foundation/Plus tier and Green/Amber/Red traffic light.
    """
    try:
        return _engine().asean.get_entity_taxonomy(entity_id)
    except Exception as exc:
        logger.exception("asean taxonomy error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# PBoC Green Finance (China)
# NOTE: static routes /pboc/catalogue and /pboc/categories MUST precede
#       /pboc/{entity_id}/green-finance
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/pboc/catalogue")
def pboc_gbepc_catalogue():
    """
    PBoC Green Bond Endorsed Project Catalogue (GBEPC 2021) — 6 categories.
    Returns issuance by category from DB or reference labels.
    """
    try:
        return _engine().pboc.get_gbepc_catalogue()
    except Exception as exc:
        logger.exception("pboc catalogue error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/pboc/categories")
def pboc_categories():
    """GBEPC 2021 category codes and labels."""
    return {
        "categories": {
            "CE": "Clean Energy",
            "CT": "Clean Transportation",
            "EC": "Energy Conservation and Environmental Protection",
            "EE": "Ecological Environment",
            "GU": "Green Upgrading of Industry",
            "GS": "Green Services",
        },
        "version": "GBEPC 2021",
        "authority": "People's Bank of China / NDRC / CSRC",
    }


@router.get("/pboc/{entity_id}/green-finance")
def get_pboc_green_finance(entity_id: str):
    """
    PBoC green finance records for an entity.
    GBEPC 2021 category breakdown, CGT alignment, green asset/credit ratios.
    """
    try:
        return _engine().pboc.get_entity_green_finance(entity_id)
    except Exception as exc:
        logger.exception("pboc green finance error")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# CBI Market (Climate Bond Initiative — live data)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/cbi/market-overview")
def cbi_market_overview():
    """
    CBI global sustainable finance market overview.
    Total issuance by type (Green/Social/SLB/Transition), by country, by sector.
    Checks DB cache → CBI API → curated reference snapshot.
    """
    try:
        return _cbi().get_market_overview()
    except Exception as exc:
        logger.exception("cbi market overview error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cbi/certified-bonds")
def cbi_certified_bonds(
    limit:   int           = Query(default=50, le=500),
    country: Optional[str] = Query(default=None, description="ISO-2 country code, e.g. US"),
    sector:  Optional[str] = Query(default=None, description="CBI taxonomy sector"),
    label:   Optional[str] = Query(default=None, description="CBI Certified | CBI Verified"),
    issuer:  Optional[str] = Query(default=None, description="Partial issuer name search"),
):
    """
    List CBI-certified and CBI-verified bonds.
    Filterable by country, taxonomy sector, CBI label, issuer name.
    Falls back to curated reference dataset when DB is empty.
    """
    try:
        return _cbi().get_certified_bonds(limit=limit, country=country, sector=sector, label=label, issuer=issuer)
    except Exception as exc:
        logger.exception("cbi certified bonds error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/cbi/refresh")
def cbi_refresh():
    """
    Force refresh from CBI API.
    Upserts to cbi_certified_bonds and cbi_market_snapshots.
    Returns: refreshed_at, bonds_upserted, market_updated.
    """
    try:
        return _cbi().refresh()
    except Exception as exc:
        logger.exception("cbi refresh error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cbi/sector-criteria")
def cbi_sector_criteria():
    """CBI Climate Bonds Taxonomy sector eligibility criteria (Energy, Buildings, Transport, Water, Land Use)."""
    try:
        return _cbi().get_sector_criteria()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cbi/pricing-report")
def cbi_pricing_report():
    """
    Green Bond Pricing in the Primary Market — greenium, oversubscription, CBI certified share.
    """
    try:
        return _cbi().get_pricing_report()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
