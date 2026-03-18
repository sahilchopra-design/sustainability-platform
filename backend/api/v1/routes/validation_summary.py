"""
API Routes: Validation Summary Engine
=======================================
GET  /api/v1/validation/methodology-registry — All engine methodology references
GET  /api/v1/validation/dqs-map              — PCAF DQS → confidence mapping
POST /api/v1/validation/wrap                 — Manually wrap a result with validation envelope
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

from services.validation_summary_engine import ValidationSummaryEngine, CalcMeta

router = APIRouter(prefix="/api/v1/validation", tags=["Validation Summary"])


class WrapRequest(BaseModel):
    """Manually wrap an arbitrary result dict with a validation envelope."""
    engine_name: str
    engine_version: str = ""
    methodology_reference: str = ""
    result: dict[str, Any]
    inputs_captured: dict[str, Any] = Field(default_factory=dict)
    parameters_applied: dict[str, Any] = Field(default_factory=dict)
    data_sources: list[str] = Field(default_factory=list)
    data_quality_flags: list[str] = Field(default_factory=list)
    dqs_scores: list[int] = Field(default_factory=list)
    input_completeness_pct: float = Field(100, ge=0, le=100)
    methodology_maturity: str = Field("established", pattern=r"^(established|evolving|experimental)$")
    user_id: Optional[str] = None


@router.get("/methodology-registry")
def methodology_registry():
    """Return the full methodology registry — standards and references per engine."""
    return ValidationSummaryEngine.get_methodology_registry()


@router.get("/dqs-map")
def dqs_confidence_map():
    """Return PCAF DQS → confidence weighting."""
    return ValidationSummaryEngine.get_dqs_confidence_map()


@router.post("/wrap")
def wrap_result(req: WrapRequest):
    """Wrap an arbitrary result dict with a BCBS 239-compliant validation envelope."""
    meta = CalcMeta(
        engine_name=req.engine_name,
        engine_version=req.engine_version,
        methodology_reference=req.methodology_reference,
        inputs_captured=req.inputs_captured,
        parameters_applied=req.parameters_applied,
        data_sources=req.data_sources,
        data_quality_flags=req.data_quality_flags,
        dqs_scores=req.dqs_scores,
        input_completeness_pct=req.input_completeness_pct,
        methodology_maturity=req.methodology_maturity,
    )
    return ValidationSummaryEngine.wrap(req.result, meta, req.user_id)
