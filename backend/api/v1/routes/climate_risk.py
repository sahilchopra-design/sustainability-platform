"""
Climate Risk API Routes
========================
Unified endpoint surface for the Climate Risk Engine:
  /api/v1/climate-risk/physical/assess       — single-entity physical risk
  /api/v1/climate-risk/transition/assess     — single-entity transition risk
  /api/v1/climate-risk/integrated/assess     — combined score
  /api/v1/climate-risk/methodologies         — CRUD + list
  /api/v1/climate-risk/methodologies/{id}/publish   — lifecycle
  /api/v1/climate-risk/methodologies/{id}/retire    — lifecycle
  /api/v1/climate-risk/methodologies/{id}/archive   — lifecycle
  /api/v1/climate-risk/methodologies/{id}/clone     — clone to draft
  /api/v1/climate-risk/methodologies/{id}/export    — JSON export
  /api/v1/climate-risk/methodologies/{id}/diff      — diff two methodologies
  /api/v1/climate-risk/templates             — list 9 pre-calibrated templates
  /api/v1/climate-risk/assessments/run       — launch assessment run
  /api/v1/climate-risk/assessments           — list runs
  /api/v1/climate-risk/assessments/{id}      — get run + results
  /api/v1/climate-risk/assessments/{id}/drill-down — entity drill-down
  /api/v1/climate-risk/reports/generate      — regulatory report generation

References:
  - EBA GL/2025/01 — ESG Risk Management
  - NGFS Phase 5 Scenarios
  - TCFD / ISSB S2 / CSRD ESRS E1
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/climate-risk", tags=["Climate Risk"])


# ---------------------------------------------------------------------------
# Lazy imports (avoid circular import at module load time)
# ---------------------------------------------------------------------------

def _get_method_manager():
    from services.assessment_methodology_manager import get_manager
    return get_manager()


def _get_runner():
    from services.assessment_runner import get_runner
    return get_runner()


def _get_physical_engine():
    from services.climate_physical_risk_engine import PhysicalRiskEngine
    return PhysicalRiskEngine()


def _get_transition_engine():
    from services.climate_transition_risk_engine import TransitionRiskEngine
    return TransitionRiskEngine()


def _get_integrator():
    from services.climate_integrated_risk import IntegratedRiskCalculator
    return IntegratedRiskCalculator()


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class PhysicalAssessRequest(BaseModel):
    entity_id: str
    sector_nace: str = "G.47"
    country_iso: str = "DE"
    asset_value: float = 0.0
    latitude: Optional[float] = 51.5
    longitude: Optional[float] = 0.0
    elevation_m: Optional[float] = 50.0
    coastal_proximity_km: Optional[float] = 50.0
    scenario: str = "Below 2°C"
    time_horizon: int = 10
    enabled_hazards: Optional[List[str]] = None
    damage_function: str = "sigmoid"
    adaptation_discount: float = 0.1
    cascading_multiplier: float = 1.2
    cvar_confidence: float = 0.95


class TransitionAssessRequest(BaseModel):
    entity_id: str
    sector_nace: str = "G.47"
    country_iso: str = "DE"
    revenue: float = 0.0
    scope1_emissions: float = 0.0
    scope2_emissions: float = 0.0
    scope3_emissions: float = 0.0
    scenario: str = "Below 2°C"
    time_horizon: int = 10
    include_scope3_carbon: bool = False
    cbam_rate: float = 0.85
    writedown_curve: str = "sigmoid"
    residual_value_floor: float = 0.05
    alignment_pathway: str = "IEA_NZE_2050"


class IntegratedAssessRequest(BaseModel):
    physical: PhysicalAssessRequest
    transition: TransitionAssessRequest
    physical_weight: float = 0.5
    transition_weight: float = 0.5
    interaction_mode: str = "additive"
    interaction_alpha: float = 0.1
    nature_risk_amplifier: bool = False
    nature_amplifier_cap: float = 1.5


class MethodologyCreateRequest(BaseModel):
    name: str
    description: str
    config: Dict[str, Any]
    target_sectors: Optional[List[str]] = None
    created_by: str = "api_user"


class MethodologyUpdateRequest(BaseModel):
    updates: Dict[str, Any]
    changed_by: str = "api_user"


class MethodologyCloneRequest(BaseModel):
    new_name: str
    cloned_by: str = "api_user"


class MethodologyPublishRequest(BaseModel):
    approved_by: str = "api_user"


class MethodologyRetireRequest(BaseModel):
    retired_by: str = "api_user"
    reason: str = ""


class MethodologyImportRequest(BaseModel):
    json_str: str
    imported_by: str = "api_user"


class EntityInputSchema(BaseModel):
    entity_id: str
    entity_type: str = "portfolio"
    entity_name: str = ""
    sector_nace_code: str = "G.47"
    country_iso: str = "DE"
    asset_value: float = 0.0
    annual_revenue: float = 0.0
    scope1_emissions: float = 0.0
    scope2_emissions: float = 0.0
    scope3_emissions: float = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None
    coastal_proximity_km: Optional[float] = None
    epc_rating: Optional[str] = None
    construction_year: Optional[int] = None
    children: List["EntityInputSchema"] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

EntityInputSchema.model_rebuild()


class RunAssessmentRequest(BaseModel):
    methodology_id: str
    targets: List[EntityInputSchema]
    scope: str = "full_hierarchy"
    scenarios: Optional[List[str]] = None
    time_horizons: Optional[List[int]] = None
    delta_against_run_id: Optional[str] = None
    delta_threshold: float = 0.05
    triggered_by: str = "api_user"
    run_label: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    run_id: str
    template: str = "tcfd_four_pillar"
    # tcfd_four_pillar | eba_pillar3 | csrd_esrs_e1 | issb_s2 | internal_summary
    entity_id: Optional[str] = None   # None = portfolio level
    format: str = "json"
    # json | xlsx | pdf (pdf deferred)


# ---------------------------------------------------------------------------
# Physical Risk
# ---------------------------------------------------------------------------

@router.post("/physical/assess", summary="Assess physical climate risk for a single entity")
async def assess_physical_risk(req: PhysicalAssessRequest):
    engine = _get_physical_engine()
    try:
        inputs = req.model_dump()
        result = engine.assess(inputs)
        return {"status": "ok", "data": result}
    except Exception as exc:
        logger.error("Physical risk assessment failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Transition Risk
# ---------------------------------------------------------------------------

@router.post("/transition/assess", summary="Assess transition climate risk for a single entity")
async def assess_transition_risk(req: TransitionAssessRequest):
    engine = _get_transition_engine()
    try:
        inputs = req.model_dump()
        result = engine.assess(inputs)
        return {"status": "ok", "data": result}
    except Exception as exc:
        logger.error("Transition risk assessment failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Integrated Risk
# ---------------------------------------------------------------------------

@router.post("/integrated/assess", summary="Assess combined physical + transition risk")
async def assess_integrated_risk(req: IntegratedAssessRequest):
    phys_engine = _get_physical_engine()
    trans_engine = _get_transition_engine()
    integrator = _get_integrator()
    try:
        phys_result = phys_engine.assess(req.physical.model_dump())
        trans_result = trans_engine.assess(req.transition.model_dump())
        phys_score = phys_result.get("composite_score", 0.0) if isinstance(phys_result, dict) else 0.0
        trans_score = trans_result.get("composite_score", 0.0) if isinstance(trans_result, dict) else 0.0

        wp = req.physical_weight
        wt = req.transition_weight
        alpha = req.interaction_alpha
        mode = req.interaction_mode

        if mode == "additive":
            interaction = alpha * (phys_score + trans_score) / 2
        elif mode == "multiplicative":
            interaction = alpha * phys_score * trans_score / 100
        elif mode == "max":
            interaction = alpha * max(phys_score, trans_score)
        else:
            import math
            interaction = alpha * math.sqrt(max(phys_score * trans_score, 0))

        integrated = min(wp * phys_score + wt * trans_score + interaction, 100.0)

        return {
            "status": "ok",
            "data": {
                "entity_id": req.physical.entity_id,
                "integrated_score": round(integrated, 4),
                "physical_score": phys_score,
                "transition_score": trans_score,
                "interaction_term": round(interaction, 4),
                "physical_detail": phys_result,
                "transition_detail": trans_result,
            },
        }
    except Exception as exc:
        logger.error("Integrated risk assessment failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Methodologies — CRUD
# ---------------------------------------------------------------------------

@router.get("/methodologies", summary="List methodologies")
async def list_methodologies(
    status: Optional[str] = Query(None, description="Filter by status"),
    sector: Optional[str] = Query(None, description="Filter by NACE section"),
    include_templates: bool = Query(True),
):
    manager = _get_method_manager()
    from services.assessment_methodology_manager import MethodologyStatus
    status_enum = MethodologyStatus(status) if status else None
    results = manager.list_all(
        status=status_enum,
        sector=sector,
        include_templates=include_templates,
    )
    return {
        "status": "ok",
        "count": len(results),
        "data": [m.to_dict() for m in results],
    }


@router.post("/methodologies", summary="Create a new DRAFT methodology", status_code=201)
async def create_methodology(req: MethodologyCreateRequest):
    manager = _get_method_manager()
    from services.assessment_methodology_manager import MethodologyConfig, _config_from_dict, MethodologyValidationError
    try:
        config = _config_from_dict(req.config)
        m = manager.create_draft(
            name=req.name,
            description=req.description,
            config=config,
            created_by=req.created_by,
            target_sectors=req.target_sectors,
        )
        return {"status": "ok", "data": m.to_dict()}
    except MethodologyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/methodologies/{methodology_id}", summary="Get a methodology by ID")
async def get_methodology(methodology_id: str):
    manager = _get_method_manager()
    m = manager.get(methodology_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Methodology {methodology_id} not found")
    return {"status": "ok", "data": m.to_dict()}


@router.patch("/methodologies/{methodology_id}", summary="Update a DRAFT methodology")
async def update_methodology(methodology_id: str, req: MethodologyUpdateRequest):
    manager = _get_method_manager()
    from services.assessment_methodology_manager import MethodologyValidationError
    try:
        m = manager.update_draft(methodology_id, req.updates, req.changed_by)
        return {"status": "ok", "data": m.to_dict()}
    except MethodologyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/methodologies/{methodology_id}/publish", summary="Publish a DRAFT methodology")
async def publish_methodology(methodology_id: str, req: MethodologyPublishRequest):
    manager = _get_method_manager()
    from services.assessment_methodology_manager import MethodologyValidationError
    try:
        m = manager.publish(methodology_id, approved_by=req.approved_by)
        return {"status": "ok", "data": m.to_dict()}
    except MethodologyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/methodologies/{methodology_id}/retire", summary="Retire a PUBLISHED methodology")
async def retire_methodology(methodology_id: str, req: MethodologyRetireRequest):
    manager = _get_method_manager()
    try:
        m = manager.retire(methodology_id, retired_by=req.retired_by, reason=req.reason)
        return {"status": "ok", "data": m.to_dict()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/methodologies/{methodology_id}/archive", summary="Archive a RETIRED methodology")
async def archive_methodology(methodology_id: str, archived_by: str = "api_user"):
    manager = _get_method_manager()
    try:
        m = manager.archive(methodology_id, archived_by=archived_by)
        return {"status": "ok", "data": m.to_dict()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/methodologies/{methodology_id}/clone", summary="Clone to new DRAFT")
async def clone_methodology(methodology_id: str, req: MethodologyCloneRequest):
    manager = _get_method_manager()
    try:
        m = manager.clone(methodology_id, req.new_name, req.cloned_by)
        return {"status": "ok", "data": m.to_dict()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/methodologies/{methodology_id}/export", summary="Export methodology as JSON")
async def export_methodology(methodology_id: str):
    manager = _get_method_manager()
    try:
        json_str = manager.export_json(methodology_id)
        return {"status": "ok", "data": json_str}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/methodologies/import", summary="Import methodology from JSON")
async def import_methodology(req: MethodologyImportRequest):
    manager = _get_method_manager()
    from services.assessment_methodology_manager import MethodologyValidationError
    try:
        m = manager.import_json(req.json_str, imported_by=req.imported_by)
        return {"status": "ok", "data": m.to_dict()}
    except MethodologyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/methodologies/{id_a}/diff/{id_b}", summary="Diff two methodology configs")
async def diff_methodologies(id_a: str, id_b: str):
    manager = _get_method_manager()
    try:
        diff = manager.diff(id_a, id_b)
        return {"status": "ok", "changed_fields": len(diff), "data": diff}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@router.get("/templates", summary="List all 9 pre-calibrated methodology templates")
async def list_templates():
    manager = _get_method_manager()
    templates = manager.list_templates()
    return {
        "status": "ok",
        "count": len(templates),
        "data": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "template_name": t.template_name,
                "target_sectors": t.target_sectors,
                "version": t.version,
            }
            for t in templates
        ],
    }


# ---------------------------------------------------------------------------
# Assessment Runs
# ---------------------------------------------------------------------------

@router.post("/assessments/run", summary="Launch an assessment run", status_code=202)
async def run_assessment(req: RunAssessmentRequest):
    runner = _get_runner()
    from services.assessment_runner import AssessmentRunConfig, EntityInput

    def _to_entity(e) -> EntityInput:
        children = [_to_entity(c) for c in (e.children or [])]
        return EntityInput(
            entity_id=e.entity_id,
            entity_type=e.entity_type,
            entity_name=e.entity_name,
            sector_nace_code=e.sector_nace_code,
            country_iso=e.country_iso,
            asset_value=e.asset_value,
            annual_revenue=e.annual_revenue,
            scope1_emissions=e.scope1_emissions,
            scope2_emissions=e.scope2_emissions,
            scope3_emissions=e.scope3_emissions,
            latitude=e.latitude,
            longitude=e.longitude,
            elevation_m=e.elevation_m,
            coastal_proximity_km=e.coastal_proximity_km,
            epc_rating=e.epc_rating,
            construction_year=e.construction_year,
            children=children,
            metadata=e.metadata,
        )

    run_cfg = AssessmentRunConfig(
        methodology_id=req.methodology_id,
        targets=[_to_entity(t) for t in req.targets],
        scope=req.scope,
        scenarios=req.scenarios,
        time_horizons=req.time_horizons,
        delta_against_run_id=req.delta_against_run_id,
        delta_threshold=req.delta_threshold,
        triggered_by=req.triggered_by,
        run_label=req.run_label,
    )
    try:
        result = runner.run_assessment(run_cfg)
        return _serialize_run(result)
    except Exception as exc:
        logger.error("Assessment run failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/assessments", summary="List assessment runs")
async def list_runs(
    status: Optional[str] = Query(None),
    methodology_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    runner = _get_runner()
    from services.assessment_runner import RunStatus
    status_enum = RunStatus(status) if status else None
    runs = runner.list_runs(status=status_enum, methodology_id=methodology_id, limit=limit)
    return {
        "status": "ok",
        "count": len(runs),
        "data": [_serialize_run(r) for r in runs],
    }


@router.get("/assessments/{run_id}", summary="Get assessment run results")
async def get_run(run_id: str):
    runner = _get_runner()
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {"status": "ok", "data": _serialize_run(run)}


@router.get("/assessments/{run_id}/drill-down", summary="Drill down into entity-level results")
async def drill_down(
    run_id: str,
    entity_id: Optional[str] = Query(None),
    scenario: Optional[str] = Query(None),
    time_horizon: Optional[int] = Query(None),
):
    runner = _get_runner()
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    results = run.results
    if entity_id:
        results = [r for r in results if r.entity_id == entity_id]
    if scenario:
        results = [r for r in results if r.scenario == scenario]
    if time_horizon is not None:
        results = [r for r in results if r.time_horizon == time_horizon]

    return {
        "status": "ok",
        "count": len(results),
        "data": [_serialize_result(r) for r in results],
    }


@router.delete("/assessments/{run_id}/cancel", summary="Cancel a running assessment")
async def cancel_run(run_id: str):
    runner = _get_runner()
    cancelled = runner.cancel_run(run_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail=f"Run {run_id} cannot be cancelled")
    return {"status": "ok", "message": f"Run {run_id} cancelled"}


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

@router.post("/reports/generate", summary="Generate regulatory climate risk report")
async def generate_report(req: ReportGenerateRequest):
    runner = _get_runner()
    run = runner.get_run(req.run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {req.run_id} not found")

    results = run.results
    if req.entity_id:
        results = [r for r in results if r.entity_id == req.entity_id]

    if req.template == "tcfd_four_pillar":
        report = _generate_tcfd_report(run, results)
    elif req.template == "eba_pillar3":
        report = _generate_eba_pillar3_report(run, results)
    elif req.template == "issb_s2":
        report = _generate_issb_s2_report(run, results)
    elif req.template == "csrd_esrs_e1":
        report = _generate_csrd_esrs_report(run, results)
    else:
        report = _generate_internal_summary(run, results)

    return {"status": "ok", "template": req.template, "format": req.format, "data": report}


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_run(run) -> Dict[str, Any]:
    from dataclasses import asdict
    return {
        "run_id": run.run_id,
        "methodology_id": run.methodology_id,
        "methodology_name": run.methodology_name,
        "methodology_version": run.methodology_version,
        "status": run.status.value if hasattr(run.status, "value") else run.status,
        "triggered_by": run.triggered_by,
        "run_label": run.run_label,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "duration_seconds": run.duration_seconds,
        "entity_count": run.entity_count,
        "scenario_count": run.scenario_count,
        "horizon_count": run.horizon_count,
        "portfolio_aggregate": run.portfolio_aggregate,
        "delta_report": [asdict(d) for d in run.delta_report] if run.delta_report else None,
        "error": run.error,
        "result_count": len(run.results),
    }


def _serialize_result(r) -> Dict[str, Any]:
    from dataclasses import asdict
    return {
        "entity_id": r.entity_id,
        "entity_name": r.entity_name,
        "entity_type": r.entity_type,
        "integrated_score": r.integrated_score,
        "physical": asdict(r.physical),
        "transition": asdict(r.transition),
        "nature_amplifier_applied": r.nature_amplifier_applied,
        "scenario": r.scenario,
        "time_horizon": r.time_horizon,
        "child_count": len(r.children),
    }


# ---------------------------------------------------------------------------
# Report templates
# ---------------------------------------------------------------------------

def _generate_tcfd_report(run, results) -> Dict[str, Any]:
    avg_integrated = (
        sum(r.integrated_score for r in results) / len(results) if results else 0.0
    )
    avg_physical = (
        sum(r.physical.composite_score for r in results) / len(results) if results else 0.0
    )
    avg_transition = (
        sum(r.transition.composite_score for r in results) / len(results) if results else 0.0
    )
    return {
        "framework": "TCFD",
        "pillars": {
            "governance": {
                "methodology_name": run.methodology_name,
                "methodology_version": run.methodology_version,
                "run_id": run.run_id,
                "assessed_at": run.completed_at,
            },
            "strategy": {
                "scenarios": list({r.scenario for r in results}),
                "time_horizons": sorted({r.time_horizon for r in results}),
                "avg_integrated_score": round(avg_integrated, 4),
            },
            "risk_management": {
                "avg_physical_score": round(avg_physical, 4),
                "avg_transition_score": round(avg_transition, 4),
                "entity_count": len({r.entity_id for r in results}),
                "top_risks": _top_n_risks(results, n=5),
            },
            "metrics_targets": {
                "portfolio_aggregate": run.portfolio_aggregate,
            },
        },
    }


def _generate_eba_pillar3_report(run, results) -> Dict[str, Any]:
    return {
        "framework": "EBA Pillar 3 ESG",
        "reference": "EBA GL/2025/01",
        "run_id": run.run_id,
        "assessed_at": run.completed_at,
        "summary": run.portfolio_aggregate,
        "entities": [
            {
                "entity_id": r.entity_id,
                "scenario": r.scenario,
                "time_horizon": r.time_horizon,
                "physical_score": r.physical.composite_score,
                "transition_score": r.transition.composite_score,
                "integrated_score": r.integrated_score,
            }
            for r in results
        ],
    }


def _generate_issb_s2_report(run, results) -> Dict[str, Any]:
    return {
        "framework": "ISSB S2",
        "standard": "IFRS S2 Climate-related Disclosures",
        "run_id": run.run_id,
        "assessed_at": run.completed_at,
        "scenario_analysis": {
            "scenarios_used": list({r.scenario for r in results}),
            "time_horizons": sorted({r.time_horizon for r in results}),
        },
        "risks_opportunities": {
            "physical_risks": {
                "avg_score": round(sum(r.physical.composite_score for r in results) / max(len(results), 1), 4),
                "cvar_total": round(sum(r.physical.cvar for r in results), 2),
            },
            "transition_risks": {
                "avg_score": round(sum(r.transition.composite_score for r in results) / max(len(results), 1), 4),
                "policy_legal_avg": round(sum(r.transition.policy_legal_score for r in results) / max(len(results), 1), 4),
                "technology_avg": round(sum(r.transition.technology_score for r in results) / max(len(results), 1), 4),
            },
        },
    }


def _generate_csrd_esrs_report(run, results) -> Dict[str, Any]:
    return {
        "framework": "CSRD ESRS E1",
        "disclosure_points": ["E1-9 (Physical risks)", "E1-10 (Transition risks)"],
        "run_id": run.run_id,
        "assessed_at": run.completed_at,
        "e1_9_physical_risks": {
            "acute_avg": round(sum(r.physical.acute_score for r in results) / max(len(results), 1), 4),
            "chronic_avg": round(sum(r.physical.chronic_score for r in results) / max(len(results), 1), 4),
            "cvar_portfolio": round(sum(r.physical.cvar for r in results), 2),
        },
        "e1_10_transition_risks": {
            "composite_avg": round(sum(r.transition.composite_score for r in results) / max(len(results), 1), 4),
            "by_scenario": run.portfolio_aggregate.get("by_scenario") if run.portfolio_aggregate else {},
        },
    }


def _generate_internal_summary(run, results) -> Dict[str, Any]:
    return {
        "framework": "Internal Summary",
        "run_id": run.run_id,
        "run_label": run.run_label,
        "assessed_at": run.completed_at,
        "duration_seconds": run.duration_seconds,
        "portfolio_aggregate": run.portfolio_aggregate,
        "entity_scores": [
            {
                "entity_id": r.entity_id,
                "entity_name": r.entity_name,
                "scenario": r.scenario,
                "time_horizon": r.time_horizon,
                "integrated_score": r.integrated_score,
                "physical": r.physical.composite_score,
                "transition": r.transition.composite_score,
            }
            for r in results
        ],
    }


def _top_n_risks(results, n: int = 5) -> List[Dict[str, Any]]:
    sorted_results = sorted(results, key=lambda r: r.integrated_score, reverse=True)
    return [
        {
            "entity_id": r.entity_id,
            "entity_name": r.entity_name,
            "integrated_score": r.integrated_score,
            "scenario": r.scenario,
            "time_horizon": r.time_horizon,
        }
        for r in sorted_results[:n]
    ]
