"""
API Routes: ESG Attribution + Benchmark Analytics
===================================================
POST /api/v1/attribution/esg-attribution    — Brinson-Fachler ESG attribution
POST /api/v1/attribution/benchmark-report   — Full benchmark analytics report
GET  /api/v1/attribution/pai-indicators     — SFDR mandatory PAI reference
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.esg_attribution_engine import (
    ESGAttributionEngine,
    AttributionInput,
    HoldingAttribution,
    BenchmarkAttribution,
    PAIIndicator,
)
from services.benchmark_analytics import (
    BenchmarkAnalyticsService,
    PeerFundMetrics,
    MANDATORY_PAI_INDICATORS,
)

router = APIRouter(prefix="/api/v1/attribution", tags=["ESG Attribution & Benchmark"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class HoldingAttrInput(BaseModel):
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    weight_pct: float = Field(0, ge=0, le=100)
    carbon_intensity: float = Field(0, ge=0)
    esg_score: float = Field(0, ge=0, le=100)
    taxonomy_aligned_pct: float = Field(0, ge=0, le=100)


class BenchmarkAttrInput(BaseModel):
    security_name: str
    isin: Optional[str] = None
    sector: str = "Other"
    weight_pct: float = Field(0, ge=0, le=100)
    carbon_intensity: float = Field(0, ge=0)
    esg_score: float = Field(0, ge=0, le=100)
    taxonomy_aligned_pct: float = Field(0, ge=0, le=100)


class PAIInput(BaseModel):
    indicator_id: str
    indicator_name: str
    portfolio_value: float
    benchmark_value: float
    unit: str
    direction: str = "lower_is_better"


class ESGAttributionRequest(BaseModel):
    fund_id: str
    fund_name: str
    portfolio_holdings: list[HoldingAttrInput] = Field(..., min_length=1)
    benchmark_holdings: list[BenchmarkAttrInput] = Field(..., min_length=1)
    pai_indicators: list[PAIInput] = Field(default_factory=list)
    prior_waci: Optional[float] = None
    prior_esg_score: Optional[float] = None


class PeerFundInput(BaseModel):
    fund_id: str
    fund_name: str
    sfdr_classification: str = "art8"
    waci: float = Field(0, ge=0)
    esg_score: float = Field(0, ge=0, le=100)
    taxonomy_aligned_pct: float = Field(0, ge=0, le=100)
    active_share_pct: float = Field(0, ge=0, le=100)
    exclusion_breach_count: int = Field(0, ge=0)


class BenchmarkReportRequest(BaseModel):
    fund: PeerFundInput
    peers: list[PeerFundInput] = Field(..., min_length=1)
    current_metrics: dict[str, float]
    prior_metrics: dict[str, float] = Field(default_factory=dict)
    metric_directions: dict[str, str] = Field(default_factory=dict)
    benchmark_waci: float = Field(0, ge=0)
    fossil_fuel_pct: float = Field(0, ge=0, le=100)
    controversial_weapons_pct: float = Field(0, ge=0, le=100)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _to_holding_attr(m: HoldingAttrInput) -> HoldingAttribution:
    return HoldingAttribution(
        holding_id=m.holding_id, security_name=m.security_name,
        isin=m.isin, sector=m.sector, weight_pct=m.weight_pct,
        carbon_intensity=m.carbon_intensity, esg_score=m.esg_score,
        taxonomy_aligned_pct=m.taxonomy_aligned_pct,
    )


def _to_bench_attr(m: BenchmarkAttrInput) -> BenchmarkAttribution:
    return BenchmarkAttribution(
        security_name=m.security_name, isin=m.isin, sector=m.sector,
        weight_pct=m.weight_pct, carbon_intensity=m.carbon_intensity,
        esg_score=m.esg_score, taxonomy_aligned_pct=m.taxonomy_aligned_pct,
    )


def _to_pai(m: PAIInput) -> PAIIndicator:
    return PAIIndicator(
        indicator_id=m.indicator_id, indicator_name=m.indicator_name,
        portfolio_value=m.portfolio_value, benchmark_value=m.benchmark_value,
        unit=m.unit, direction=m.direction,
    )


def _to_peer(m: PeerFundInput) -> PeerFundMetrics:
    return PeerFundMetrics(
        fund_id=m.fund_id, fund_name=m.fund_name,
        sfdr_classification=m.sfdr_classification,
        waci=m.waci, esg_score=m.esg_score,
        taxonomy_aligned_pct=m.taxonomy_aligned_pct,
        active_share_pct=m.active_share_pct,
        exclusion_breach_count=m.exclusion_breach_count,
    )


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_sector_effect(s) -> dict:
    return {
        "sector": s.sector,
        "portfolio_weight_pct": s.portfolio_weight_pct,
        "benchmark_weight_pct": s.benchmark_weight_pct,
        "portfolio_metric": s.portfolio_metric,
        "benchmark_metric": s.benchmark_metric,
        "allocation_effect": s.allocation_effect,
        "selection_effect": s.selection_effect,
        "interaction_effect": s.interaction_effect,
        "total_effect": s.total_effect,
    }


def _ser_attribution(a) -> dict:
    return {
        "metric_name": a.metric_name,
        "portfolio_metric": a.portfolio_metric,
        "benchmark_metric": a.benchmark_metric,
        "active_metric": a.active_metric,
        "total_allocation_effect": a.total_allocation_effect,
        "total_selection_effect": a.total_selection_effect,
        "total_interaction_effect": a.total_interaction_effect,
        "total_active_effect": a.total_active_effect,
        "metric_direction": a.metric_direction,
        "is_outperforming": a.is_outperforming,
        "sector_effects": [_ser_sector_effect(s) for s in a.sector_effects],
    }


def _ser_ranking(r) -> dict:
    return {
        "metric_name": r.metric_name,
        "fund_value": r.fund_value,
        "peer_count": r.peer_count,
        "rank": r.rank,
        "percentile": r.percentile,
        "peer_median": r.peer_median,
        "peer_mean": r.peer_mean,
        "peer_min": r.peer_min,
        "peer_max": r.peer_max,
    }


def _ser_comparison(c) -> dict:
    return {
        "metric_name": c.metric_name,
        "current_value": c.current_value,
        "prior_value": c.prior_value,
        "absolute_change": c.absolute_change,
        "pct_change": c.pct_change,
        "improved": c.improved,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/esg-attribution")
def esg_attribution(req: ESGAttributionRequest):
    """Brinson-Fachler ESG/carbon attribution analysis."""
    engine = ESGAttributionEngine()
    inp = AttributionInput(
        fund_id=req.fund_id,
        fund_name=req.fund_name,
        portfolio_holdings=[_to_holding_attr(h) for h in req.portfolio_holdings],
        benchmark_holdings=[_to_bench_attr(b) for b in req.benchmark_holdings],
        pai_indicators=[_to_pai(p) for p in req.pai_indicators],
        prior_waci=req.prior_waci,
        prior_esg_score=req.prior_esg_score,
    )
    result = engine.analyse(inp)
    return {
        "fund_id": result.fund_id,
        "fund_name": result.fund_name,
        "carbon_attribution": _ser_attribution(result.carbon_attribution),
        "esg_attribution": _ser_attribution(result.esg_attribution),
        "taxonomy_attribution": _ser_attribution(result.taxonomy_attribution),
        "active_share_pct": result.active_share_pct,
        "tracking_error_pct": result.tracking_error_pct,
        "carbon_information_ratio": result.carbon_information_ratio,
        "esg_information_ratio": result.esg_information_ratio,
        "pai_outperformance_count": result.pai_outperformance_count,
        "pai_total_count": result.pai_total_count,
        "waci_yoy_change_pct": result.waci_yoy_change_pct,
        "esg_yoy_change_pct": result.esg_yoy_change_pct,
    }


@router.post("/benchmark-report")
def benchmark_report(req: BenchmarkReportRequest):
    """Full benchmark analytics report: peer rankings, YoY, compliance."""
    service = BenchmarkAnalyticsService()
    result = service.generate_report(
        fund=_to_peer(req.fund),
        peers=[_to_peer(p) for p in req.peers],
        current_metrics=req.current_metrics,
        prior_metrics=req.prior_metrics,
        metric_directions=req.metric_directions,
        benchmark_waci=req.benchmark_waci,
        fossil_fuel_pct=req.fossil_fuel_pct,
        controversial_weapons_pct=req.controversial_weapons_pct,
    )
    return {
        "fund_id": result.fund_id,
        "fund_name": result.fund_name,
        "peer_rankings": [_ser_ranking(r) for r in result.peer_rankings],
        "period_comparisons": [_ser_comparison(c) for c in result.period_comparisons],
        "benchmark_compliance": {
            "is_ctb_aligned": result.benchmark_compliance.is_ctb_aligned,
            "is_pab_aligned": result.benchmark_compliance.is_pab_aligned,
            "ctb_reasons": result.benchmark_compliance.ctb_reasons,
            "pab_reasons": result.benchmark_compliance.pab_reasons,
            "waci_reduction_pct": result.benchmark_compliance.waci_reduction_pct,
            "fossil_fuel_exclusion_met": result.benchmark_compliance.fossil_fuel_exclusion_met,
            "controversial_weapons_excluded": result.benchmark_compliance.controversial_weapons_excluded,
            "yoy_decarbonisation_pct": result.benchmark_compliance.yoy_decarbonisation_pct,
        },
        "overall_peer_percentile": result.overall_peer_percentile,
        "improvement_count": result.improvement_count,
        "deterioration_count": result.deterioration_count,
    }


@router.get("/pai-indicators")
def get_pai_indicators():
    """Return SFDR mandatory PAI indicator reference data."""
    return {"mandatory_pai_indicators": MANDATORY_PAI_INDICATORS}
