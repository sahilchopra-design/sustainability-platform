"""
Data Lineage API
==================
Endpoints for cross-module data lineage tracing, gap analysis,
module dependency graph, and quality propagation.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.data_lineage_service import DataLineageEngine
from services.lineage_orchestrator import LineageOrchestrator

router = APIRouter(prefix="/api/v1/lineage", tags=["Data Lineage"])

_engine = DataLineageEngine()
_orchestrator = LineageOrchestrator()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class LineageTraceRequest(BaseModel):
    target_module: str
    entity_id: str = "generic"
    module_quality: dict[str, float] = {}


class QualityPropagationRequest(BaseModel):
    entity_id: str
    module_quality: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_node(n) -> dict:
    return {
        "module_id": n.module_id,
        "module_label": n.module_label,
        "category": n.category,
        "operation": n.operation,
        "input_fields": n.input_fields,
        "output_fields": n.output_fields,
        "quality_score": n.quality_score,
        "quality_label": n.quality_label,
        "reference_data_used": n.reference_data_used,
        "depth": n.depth,
    }


def _ser_gap(g) -> dict:
    return {
        "source_module": g.source_module,
        "target_module": g.target_module,
        "missing_fields": g.missing_fields,
        "severity": g.severity,
        "remediation": g.remediation,
        "reference_data_needed": g.reference_data_needed,
    }


def _ser_edge(e) -> dict:
    return {
        "source": e.source,
        "target": e.target,
        "field_count": e.field_count,
        "description": e.description,
    }


def _ser_chain(c) -> dict:
    return {
        "entity_id": c.entity_id,
        "target_module": c.target_module,
        "nodes": [_ser_node(n) for n in c.nodes],
        "total_chain_length": c.total_chain_length,
        "root_sources": c.root_sources,
        "data_quality_score": c.data_quality_score,
        "quality_label": c.quality_label,
        "gaps": [_ser_gap(g) for g in c.gaps],
        "reference_data_used": c.reference_data_used,
        "has_complete_lineage": c.has_complete_lineage,
    }


def _ser_graph(g) -> dict:
    return {
        "total_modules": g.total_modules,
        "total_edges": g.total_edges,
        "modules": g.modules,
        "edges": [_ser_edge(e) for e in g.edges],
        "root_modules": g.root_modules,
        "leaf_modules": g.leaf_modules,
        "orphan_modules": g.orphan_modules,
        "bridge_modules": g.bridge_modules,
    }


def _ser_gap_analysis(ga) -> dict:
    return {
        "total_edges": ga.total_edges,
        "complete_edges": ga.complete_edges,
        "broken_edges": ga.broken_edges,
        "completeness_pct": ga.completeness_pct,
        "gaps": [_ser_gap(g) for g in ga.gaps],
        "critical_gaps": [_ser_gap(g) for g in ga.critical_gaps],
        "reference_data_missing": ga.reference_data_missing,
        "recommendations": ga.recommendations,
    }


def _ser_quality(q) -> dict:
    return {
        "entity_id": q.entity_id,
        "module_quality": q.module_quality,
        "weakest_links": q.weakest_links,
        "overall_quality": q.overall_quality,
        "quality_label": q.quality_label,
        "recommendations": q.recommendations,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/trace", summary="Trace upstream lineage for a target module")
def trace_lineage(req: LineageTraceRequest):
    res = _engine.trace_lineage(
        target_module=req.target_module,
        entity_id=req.entity_id,
        module_quality=req.module_quality if req.module_quality else None,
    )
    return _ser_chain(res)


@router.get("/gaps", summary="Find lineage gaps across the platform")
def find_gaps():
    res = _engine.find_gaps()
    return _ser_gap_analysis(res)


@router.get("/module-graph", summary="Full module dependency graph")
def module_graph():
    res = _engine.get_module_graph()
    return _ser_graph(res)


@router.post("/quality", summary="Propagate quality scores through module graph")
def propagate_quality(req: QualityPropagationRequest):
    res = _engine.propagate_quality(
        entity_id=req.entity_id,
        module_quality=req.module_quality,
    )
    return _ser_quality(res)


@router.get("/signatures", summary="All module I/O signatures")
def module_signatures():
    return _engine.get_module_signatures()


@router.get("/dependencies", summary="All module dependency edges")
def module_dependencies():
    return _engine.get_dependencies()


@router.get("/reference-data", summary="All reference data across modules")
def reference_data():
    return _engine.get_all_reference_data()


# ---------------------------------------------------------------------------
# Orchestrator Endpoints (Chunk 5)
# ---------------------------------------------------------------------------

class DQSPropagationRequest(BaseModel):
    entity_id: str
    module_dqs: dict[str, int] = {}  # {module_id: DQS 1-5}


class ImpactAnalysisRequest(BaseModel):
    module_id: str
    degradation_factor: float = 0.0


@router.get("/platform-health", summary="Platform-wide lineage health dashboard")
def platform_health():
    res = _orchestrator.get_platform_health()
    return {
        "timestamp": res.timestamp,
        "total_modules": res.total_modules,
        "total_edges": res.total_edges,
        "total_bridges": res.total_bridges,
        "lineage_completeness_pct": res.lineage_completeness_pct,
        "reference_data_completeness_pct": res.reference_data_completeness_pct,
        "average_quality_score": res.average_quality_score,
        "orphan_modules": res.orphan_modules,
        "critical_gaps": res.critical_gaps,
        "high_gaps": res.high_gaps,
        "medium_gaps": res.medium_gaps,
        "missing_reference_datasets": res.missing_reference_datasets,
        "bcbs239_compliance_score": res.bcbs239_compliance_score,
        "recommendations": res.recommendations,
    }


@router.get("/reference-data-gaps", summary="Reference data gap analysis")
def reference_data_gaps():
    res = _orchestrator.analyse_reference_data_gaps()
    return {
        "total_datasets_catalogued": res.total_datasets_catalogued,
        "datasets_embedded": res.datasets_embedded,
        "datasets_missing": res.datasets_missing,
        "datasets_partial": res.datasets_partial,
        "completeness_pct": res.completeness_pct,
        "missing_datasets": res.missing_datasets,
        "priority_high": res.priority_high,
        "priority_medium": res.priority_medium,
        "total_estimated_fields_missing": res.total_estimated_fields_missing,
        "affected_modules": res.affected_modules,
        "recommendations": res.recommendations,
    }


@router.get("/bridge-health", summary="Cross-module bridge health check")
def bridge_health():
    res = _orchestrator.check_bridge_health()
    return {
        "total_bridges": res.total_bridges,
        "wired_bridges": res.wired_bridges,
        "broken_bridges": res.broken_bridges,
        "total_field_mappings": res.total_field_mappings,
        "bridges": res.bridges,
        "recommendations": res.recommendations,
    }


@router.post("/impact-analysis", summary="Module degradation impact analysis")
def impact_analysis(req: ImpactAnalysisRequest):
    res = _orchestrator.analyse_module_impact(req.module_id, req.degradation_factor)
    return {
        "degraded_module": res.degraded_module,
        "affected_downstream": res.affected_downstream,
        "affected_chains": res.affected_chains,
        "quality_impact": res.quality_impact,
        "regulatory_impact": res.regulatory_impact,
        "recommendations": res.recommendations,
    }


@router.post("/dqs-quality", summary="DQS-weighted quality propagation")
def dqs_quality(req: DQSPropagationRequest):
    return _orchestrator.propagate_dqs_quality(req.entity_id, req.module_dqs)


@router.get("/regulatory-lineage/{framework}", summary="Regulatory disclosure lineage trace")
def regulatory_lineage(framework: str):
    return _orchestrator.trace_regulatory_lineage(framework)


@router.get("/module-coverage", summary="Module coverage by category")
def module_coverage():
    return _orchestrator.get_module_coverage()


@router.get("/reference-data-inventory", summary="Complete reference data inventory")
def reference_data_inventory():
    return _orchestrator.get_reference_data_inventory()


@router.get("/audit-events", summary="Lineage audit events")
def audit_events(limit: int = 100, severity: Optional[str] = None):
    return _orchestrator.get_audit_events(limit=limit, severity=severity)
