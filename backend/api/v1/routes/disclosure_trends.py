"""
Disclosure Completeness & Trend Analytics API
================================================
Endpoints for cross-framework disclosure gap analysis and multi-year
KPI trend analytics with peer benchmarking.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.disclosure_completeness import (
    DisclosureCompletenessEngine,
    FRAMEWORK_REQUIREMENTS,
)
from services.trend_analytics import (
    TrendAnalyticsEngine,
    KPI_DEFINITIONS,
    PEER_BENCHMARKS,
)

router = APIRouter(prefix="/api/v1/disclosure-trends", tags=["Disclosure & Trends"])

_disclosure = DisclosureCompletenessEngine()
_trends = TrendAnalyticsEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ProvidedDP(BaseModel):
    dp_id: str
    value: float = 1.0  # 1.0 for narrative = "provided"


class CompletenessRequest(BaseModel):
    entity_name: str
    provided_dps: list[ProvidedDP] = []
    frameworks: Optional[list[str]] = None
    reporting_year: int = 2024


class YearValue(BaseModel):
    year: int
    value: float


class KPISeries(BaseModel):
    kpi_id: str
    values: list[YearValue]


class KPITarget(BaseModel):
    kpi_id: str
    target_value: float


class TrendRequest(BaseModel):
    entity_name: str
    kpi_series: list[KPISeries]
    sector: str = "financial_institutions"
    targets: list[KPITarget] = []


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_dp_status(s) -> dict:
    return {
        "dp_id": s.dp_id,
        "label": s.label,
        "dp_type": s.dp_type,
        "provided": s.provided,
        "value": s.value,
        "quality": s.quality,
    }


def _ser_framework(fr) -> dict:
    return {
        "framework_id": fr.framework_id,
        "framework": fr.framework,
        "standard": fr.standard,
        "total_required": fr.total_required,
        "provided_count": fr.provided_count,
        "missing_count": fr.missing_count,
        "completeness_pct": fr.completeness_pct,
        "data_points": [_ser_dp_status(dp) for dp in fr.data_points],
        "missing_dps": fr.missing_dps,
        "readiness": fr.readiness,
    }


def _ser_completeness(r) -> dict:
    return {
        "entity_name": r.entity_name,
        "reporting_year": r.reporting_year,
        "frameworks_assessed": r.frameworks_assessed,
        "overall_completeness_pct": r.overall_completeness_pct,
        "overall_readiness": r.overall_readiness,
        "framework_results": [_ser_framework(fr) for fr in r.framework_results],
        "priority_gaps": r.priority_gaps,
        "cross_framework_coverage": r.cross_framework_coverage,
    }


def _ser_kpi_trend(t) -> dict:
    return {
        "kpi_id": t.kpi_id,
        "label": t.label,
        "unit": t.unit,
        "direction": t.direction,
        "category": t.category,
        "data_points": [{"year": dp.year, "value": dp.value} for dp in t.data_points],
        "latest_value": t.latest_value,
        "earliest_value": t.earliest_value,
        "yoy_changes": t.yoy_changes,
        "cagr_pct": t.cagr_pct,
        "trend_direction": t.trend_direction,
        "years_covered": t.years_covered,
        "target_value": t.target_value,
        "on_track": t.on_track,
        "peer_benchmark": t.peer_benchmark,
        "vs_peer_pct": t.vs_peer_pct,
    }


def _ser_trends(r) -> dict:
    return {
        "entity_name": r.entity_name,
        "sector": r.sector,
        "years_range": r.years_range,
        "kpi_count": r.kpi_count,
        "kpi_trends": [_ser_kpi_trend(t) for t in r.kpi_trends],
        "improving_count": r.improving_count,
        "worsening_count": r.worsening_count,
        "stable_count": r.stable_count,
        "overall_trajectory": r.overall_trajectory,
        "highlight_improvements": r.highlight_improvements,
        "highlight_concerns": r.highlight_concerns,
    }


# ---------------------------------------------------------------------------
# Endpoints — Disclosure Completeness
# ---------------------------------------------------------------------------

@router.post("/completeness", summary="Assess disclosure completeness across frameworks")
def assess_completeness(req: CompletenessRequest):
    dp_dict = {dp.dp_id: dp.value for dp in req.provided_dps}
    res = _disclosure.assess(
        entity_name=req.entity_name,
        provided_dps=dp_dict,
        frameworks=req.frameworks,
        reporting_year=req.reporting_year,
    )
    return _ser_completeness(res)


# ---------------------------------------------------------------------------
# Endpoints — Trend Analytics
# ---------------------------------------------------------------------------

@router.post("/trends", summary="Multi-year KPI trend analysis with peer benchmarks")
def analyse_trends(req: TrendRequest):
    series = {
        ks.kpi_id: [{"year": v.year, "value": v.value} for v in ks.values]
        for ks in req.kpi_series
    }
    targets = {t.kpi_id: t.target_value for t in req.targets}
    res = _trends.analyse(
        entity_name=req.entity_name,
        kpi_series=series,
        sector=req.sector,
        targets=targets,
    )
    return _ser_trends(res)


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/framework-requirements", summary="All framework DP requirements")
def ref_framework_requirements():
    return _disclosure.get_framework_requirements()


@router.get("/ref/framework-list", summary="Summary list of frameworks")
def ref_framework_list():
    return _disclosure.get_framework_list()


@router.get("/ref/kpi-definitions", summary="KPI definitions for trend analysis")
def ref_kpi_definitions():
    return _trends.get_kpi_definitions()


@router.get("/ref/peer-benchmarks", summary="Peer benchmark averages by sector")
def ref_peer_benchmarks():
    return _trends.get_peer_benchmarks()


@router.get("/ref/sectors", summary="Available sectors for benchmarking")
def ref_sectors():
    return _trends.get_sectors()
