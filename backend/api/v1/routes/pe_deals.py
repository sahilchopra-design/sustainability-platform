"""
API Routes: PE Deal Pipeline + ESG Screening
==============================================
POST /api/v1/pe-deals/screen           — Screen single deal ESG
POST /api/v1/pe-deals/compare          — Side-by-side deal comparison
POST /api/v1/pe-deals/pipeline-summary — Pipeline analytics
GET  /api/v1/pe-deals/sector-heatmap   — Sector ESG risk reference
GET  /api/v1/pe-deals/sub-dimensions   — ESG screening sub-dimensions

DB-Powered (pe_* tables):
POST /api/v1/pe-deals/db/screen-and-persist — Screen deal + persist to DB
GET  /api/v1/pe-deals/db/deals              — List deals from DB
GET  /api/v1/pe-deals/db/deals/{deal_id}    — Get single deal
PATCH /api/v1/pe-deals/db/deals/{deal_id}/stage — Advance deal stage
GET  /api/v1/pe-deals/db/pipeline-summary   — Pipeline analytics from DB
GET  /api/v1/pe-deals/db/sector-heatmap     — Sector heatmap from DB
POST /api/v1/pe-deals/db/seed-heatmap       — Seed sector heatmap
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from services.pe_deal_engine import (
    PEDealEngine,
    DealInput,
    SECTOR_ESG_RISK,
    ESG_SUB_DIMENSIONS,
)

router = APIRouter(prefix="/api/v1/pe-deals", tags=["PE Deal Pipeline"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class DealRequest(BaseModel):
    deal_id: str
    company_name: str
    sector: str = "Other"
    sub_sector: str = ""
    country: str = "US"
    stage: str = Field("sourcing", pattern=r"^(sourcing|screening|dd|ic|closing|portfolio|exited)$")
    deal_type: str = Field("buyout", pattern=r"^(buyout|growth|venture|secondary|co_invest)$")
    deal_size_eur: float = Field(0, ge=0)
    equity_ticket_eur: float = Field(0, ge=0)
    enterprise_value_eur: float = Field(0, ge=0)
    revenue_eur: float = Field(0, ge=0)
    ebitda_eur: float = Field(0, ge=0)
    entry_multiple: float = Field(0, ge=0)
    source: str = "proprietary"
    lead_partner: str = ""
    fund_id: str = ""
    esg_scores: dict[str, dict[str, int]] = Field(default_factory=dict)
    has_transition_plan: bool = True
    ungc_violation: bool = False
    sanctions_hit: bool = False
    controversial_weapons: bool = False
    severe_environmental_incident: bool = False
    child_labor_risk: bool = False
    tax_haven_structure: bool = False


class CompareRequest(BaseModel):
    deals: list[DealRequest]


class PipelineRequest(BaseModel):
    deals: list[DealRequest]


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_deal(req: DealRequest) -> DealInput:
    return DealInput(
        deal_id=req.deal_id,
        company_name=req.company_name,
        sector=req.sector,
        sub_sector=req.sub_sector,
        country=req.country,
        stage=req.stage,
        deal_type=req.deal_type,
        deal_size_eur=req.deal_size_eur,
        equity_ticket_eur=req.equity_ticket_eur,
        enterprise_value_eur=req.enterprise_value_eur,
        revenue_eur=req.revenue_eur,
        ebitda_eur=req.ebitda_eur,
        entry_multiple=req.entry_multiple,
        source=req.source,
        lead_partner=req.lead_partner,
        fund_id=req.fund_id,
        esg_scores=req.esg_scores,
        has_transition_plan=req.has_transition_plan,
        ungc_violation=req.ungc_violation,
        sanctions_hit=req.sanctions_hit,
        controversial_weapons=req.controversial_weapons,
        severe_environmental_incident=req.severe_environmental_incident,
        child_labor_risk=req.child_labor_risk,
        tax_haven_structure=req.tax_haven_structure,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_dim_score(ds) -> dict:
    return {
        "dimension": ds.dimension,
        "sub_scores": ds.sub_scores,
        "avg_score": ds.avg_score,
        "assessed_count": ds.assessed_count,
    }


def _ser_red_flag(rf) -> dict:
    return {
        "flag_id": rf.flag_id,
        "severity": rf.severity,
        "category": rf.category,
        "description": rf.description,
        "recommendation": rf.recommendation,
    }


def _ser_screening(r) -> dict:
    return {
        "deal_id": r.deal_id,
        "company_name": r.company_name,
        "sector": r.sector,
        "stage": r.stage,
        "dimension_scores": [_ser_dim_score(ds) for ds in r.dimension_scores],
        "composite_esg_score": r.composite_esg_score,
        "esg_risk_band": r.esg_risk_band,
        "red_flags": [_ser_red_flag(rf) for rf in r.red_flags],
        "hard_flag_count": r.hard_flag_count,
        "soft_flag_count": r.soft_flag_count,
        "has_deal_breaker": r.has_deal_breaker,
        "sector_risk": r.sector_risk,
        "sector_overall_risk": r.sector_overall_risk,
        "screening_recommendation": r.screening_recommendation,
        "conditions": r.conditions,
    }


def _ser_comparison(c) -> dict:
    return {
        "deal_id": c.deal_id,
        "company_name": c.company_name,
        "sector": c.sector,
        "deal_size_eur": c.deal_size_eur,
        "entry_multiple": c.entry_multiple,
        "composite_esg_score": c.composite_esg_score,
        "esg_risk_band": c.esg_risk_band,
        "red_flag_count": c.red_flag_count,
        "has_deal_breaker": c.has_deal_breaker,
        "dimension_scores": c.dimension_scores,
    }


def _ser_pipeline(p) -> dict:
    return {
        "total_deals": p.total_deals,
        "deals_by_stage": p.deals_by_stage,
        "deals_by_sector": p.deals_by_sector,
        "avg_deal_size_eur": p.avg_deal_size_eur,
        "avg_esg_score": p.avg_esg_score,
        "red_flag_deals": p.red_flag_deals,
        "deal_breaker_deals": p.deal_breaker_deals,
        "comparison_table": [_ser_comparison(c) for c in p.comparison_table],
        "sector_heatmap": p.sector_heatmap,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/screen")
def screen_deal(req: DealRequest):
    """Screen a single deal for ESG risk and red flags."""
    engine = PEDealEngine()
    deal = _to_deal(req)
    result = engine.screen_deal(deal)
    return _ser_screening(result)


@router.post("/compare")
def compare_deals(req: CompareRequest):
    """Side-by-side ESG comparison of multiple deals for IC discussion."""
    engine = PEDealEngine()
    deals = [_to_deal(d) for d in req.deals]
    rows = engine.compare_deals(deals)
    return {"deals": [_ser_comparison(r) for r in rows]}


@router.post("/pipeline-summary")
def pipeline_summary(req: PipelineRequest):
    """Aggregate pipeline analytics with ESG screening overlay."""
    engine = PEDealEngine()
    deals = [_to_deal(d) for d in req.deals]
    summary = engine.pipeline_summary(deals)
    return _ser_pipeline(summary)


@router.get("/sector-heatmap")
def get_sector_heatmap():
    """Return sector ESG risk heatmap reference data."""
    engine = PEDealEngine()
    return {"sectors": engine.get_sector_heatmap()}


@router.get("/sub-dimensions")
def get_sub_dimensions():
    """Return ESG screening sub-dimensions for scorecard template."""
    engine = PEDealEngine()
    return {"dimensions": engine.get_sub_dimensions()}


# ---------------------------------------------------------------------------
# DB-Powered Endpoints  (pe_deals / pe_screening_scores / pe_sector_risk_heatmap)
# ---------------------------------------------------------------------------

def _get_pe_db():
    """Lazy-load PEDBService with DB engine."""
    from services.pe_db_service import PEDBService
    from db.base import engine as db_engine
    return PEDBService(db_engine)


class DBDealCreateRequest(BaseModel):
    """Minimal deal creation — fields map to pe_deals columns."""
    company_name: str
    sector: str = "Other"
    sub_sector: str = ""
    country: str = "US"
    stage: str = Field("sourcing", pattern=r"^(sourcing|screening|dd|ic|closing|portfolio|exited)$")
    deal_type: str = Field("buyout", pattern=r"^(buyout|growth|venture|secondary|co_invest)$")
    deal_size_eur: float = Field(0, ge=0)
    equity_ticket_eur: float = Field(0, ge=0)
    enterprise_value_eur: float = Field(0, ge=0)
    revenue_eur: float = Field(0, ge=0)
    ebitda_eur: float = Field(0, ge=0)
    entry_multiple: float = Field(0, ge=0)
    source: str = "proprietary"
    lead_partner: str = ""
    fund_id: str = ""
    notes: str = ""


class ScreenAndPersistRequest(BaseModel):
    """Deal creation data + ESG screening input for combined workflow."""
    deal: DBDealCreateRequest
    esg_scores: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Optional manual ESG scores: {dimension: {sub: rating}}",
    )
    has_transition_plan: bool = True
    ungc_violation: bool = False
    sanctions_hit: bool = False
    controversial_weapons: bool = False
    severe_environmental_incident: bool = False
    child_labor_risk: bool = False
    tax_haven_structure: bool = False


class StageUpdateRequest(BaseModel):
    new_stage: str = Field(..., pattern=r"^(sourcing|screening|dd|ic|closing|portfolio|exited)$")


@router.post("/db/screen-and-persist", summary="Screen deal + persist to DB")
def db_screen_and_persist(req: ScreenAndPersistRequest) -> Dict[str, Any]:
    """
    Combined workflow: creates deal in pe_deals, runs ESG screening engine,
    persists dimension scores to pe_screening_scores, and updates deal status.
    """
    svc = _get_pe_db()
    deal_data = req.deal.model_dump()
    screening_input = {
        "esg_scores": req.esg_scores,
        "has_transition_plan": req.has_transition_plan,
        "ungc_violation": req.ungc_violation,
        "sanctions_hit": req.sanctions_hit,
        "controversial_weapons": req.controversial_weapons,
        "severe_environmental_incident": req.severe_environmental_incident,
        "child_labor_risk": req.child_labor_risk,
        "tax_haven_structure": req.tax_haven_structure,
    }
    return svc.screen_and_persist_deal(deal_data, screening_input)


@router.get("/db/deals", summary="List deals from DB")
def db_list_deals(
    fund_id: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """List deals from pe_deals table with optional filters."""
    svc = _get_pe_db()
    deals = svc.list_deals(fund_id=fund_id, stage=stage, sector=sector)
    return {"count": len(deals), "deals": deals}


@router.get("/db/deals/{deal_id}", summary="Get single deal from DB")
def db_get_deal(deal_id: str) -> Dict[str, Any]:
    """Get a single deal by ID."""
    svc = _get_pe_db()
    deal = svc.get_deal(deal_id)
    if not deal:
        raise HTTPException(404, f"Deal {deal_id} not found")
    return deal


@router.patch("/db/deals/{deal_id}/stage", summary="Update deal stage")
def db_update_stage(deal_id: str, req: StageUpdateRequest) -> Dict[str, Any]:
    """Advance a deal to a new pipeline stage."""
    svc = _get_pe_db()
    result = svc.update_deal_stage(deal_id, req.new_stage)
    if not result:
        raise HTTPException(404, f"Deal {deal_id} not found")
    return result


@router.get("/db/pipeline-summary", summary="Pipeline analytics from DB")
def db_pipeline_summary(
    fund_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Aggregate pipeline analytics from pe_deals table."""
    svc = _get_pe_db()
    return svc.pipeline_summary(fund_id=fund_id)


@router.get("/db/sector-heatmap", summary="Sector heatmap from DB")
def db_sector_heatmap() -> Dict[str, Any]:
    """Return sector risk heatmap from pe_sector_risk_heatmap table."""
    svc = _get_pe_db()
    rows = svc.get_sector_heatmap()
    return {"count": len(rows), "sectors": rows}


@router.post("/db/seed-heatmap", summary="Seed sector heatmap from engine reference data")
def db_seed_heatmap() -> Dict[str, Any]:
    """Idempotent: inserts engine's SECTOR_ESG_RISK into pe_sector_risk_heatmap."""
    svc = _get_pe_db()
    count = svc.seed_sector_heatmap()
    return {"message": f"Seeded {count} sectors into pe_sector_risk_heatmap"}
