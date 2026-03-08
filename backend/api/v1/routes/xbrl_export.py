"""
XBRL Export & Ingestion API
=============================
Endpoints for XBRL/iXBRL export (CSRD/ISSB filing) and XBRL document
ingestion (parse uploaded XBRL/iXBRL reports into structured data).
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.xbrl_export_engine import (
    XBRLExportEngine,
    ESRS_XBRL_TAXONOMY,
    ESEF_VALIDATION_RULES,
)
from services.xbrl_ingestion_engine import (
    XBRLIngestionEngine,
    SUPPORTED_SCHEMAS,
    CONCEPT_TO_DP,
)

router = APIRouter(prefix="/api/v1/xbrl", tags=["XBRL Export & Ingestion"])

_export = XBRLExportEngine()
_ingest = XBRLIngestionEngine()


# ---------------------------------------------------------------------------
# Request Models — Export
# ---------------------------------------------------------------------------

class DataPointEntry(BaseModel):
    dp_id: str
    value: float


class XBRLExportRequest(BaseModel):
    entity_name: str
    entity_lei: str = Field(..., min_length=20, max_length=20)
    period_start: str = "2024-01-01"
    period_end: str = "2024-12-31"
    data_points: list[DataPointEntry] = []
    currency: str = "EUR"
    decimals: int = 0


# ---------------------------------------------------------------------------
# Request Models — Ingestion
# ---------------------------------------------------------------------------

class XBRLIngestRequest(BaseModel):
    content: str = Field(..., min_length=10, description="Raw iXBRL HTML or XBRL XML content")
    format_hint: Optional[str] = Field(None, description="'ixbrl' or 'xbrl_xml' — auto-detected if omitted")


# ---------------------------------------------------------------------------
# Serialisers — Export
# ---------------------------------------------------------------------------

def _ser_fact(f) -> dict:
    return {
        "dp_id": f.dp_id,
        "concept": f.concept,
        "value": f.value,
        "unit": f.unit,
        "xbrl_unit": f.xbrl_unit,
        "decimals": f.decimals,
        "period_start": f.period_start,
        "period_end": f.period_end,
        "period_type": f.period_type,
        "entity_lei": f.entity_lei,
        "context_id": f.context_id,
        "label": f.label,
        "esrs": f.esrs,
        "dr": f.dr,
    }


def _ser_validation(v) -> dict:
    return {
        "rule_id": v.rule_id,
        "description": v.description,
        "passed": v.passed,
        "details": v.details,
    }


def _ser_export(r) -> dict:
    return {
        "entity_name": r.entity_name,
        "entity_lei": r.entity_lei,
        "reporting_period": r.reporting_period,
        "taxonomy_version": r.taxonomy_version,
        "facts": [_ser_fact(f) for f in r.facts],
        "fact_count": r.fact_count,
        "ixbrl_html": r.ixbrl_html,
        "xbrl_xml": r.xbrl_xml,
        "validation_results": [_ser_validation(v) for v in r.validation_results],
        "validation_passed": r.validation_passed,
        "errors_count": r.errors_count,
        "warnings_count": r.warnings_count,
        "coverage_by_esrs": r.coverage_by_esrs,
    }


# ---------------------------------------------------------------------------
# Serialisers — Ingestion
# ---------------------------------------------------------------------------

def _ser_extracted_fact(f) -> dict:
    return {
        "concept": f.concept,
        "value": f.value,
        "unit": f.unit,
        "context_id": f.context_id,
        "period_start": f.period_start,
        "period_end": f.period_end,
        "period_type": f.period_type,
        "decimals": f.decimals,
        "entity_id": f.entity_id,
        "dp_id": f.dp_id,
        "esrs": f.esrs,
        "dr": f.dr,
        "label": f.label,
        "mapped": f.mapped,
    }


def _ser_ingestion(r) -> dict:
    return {
        "source_format": r.source_format,
        "detected_taxonomy": r.detected_taxonomy,
        "entity_name": r.entity_name,
        "entity_id": r.entity_id,
        "reporting_period": r.reporting_period,
        "period_start": r.period_start,
        "period_end": r.period_end,
        "total_facts_extracted": r.total_facts_extracted,
        "mapped_facts": r.mapped_facts,
        "unmapped_facts": r.unmapped_facts,
        "mapping_rate_pct": r.mapping_rate_pct,
        "facts": [_ser_extracted_fact(f) for f in r.facts],
        "taxonomy_coverage": r.taxonomy_coverage,
        "unmapped_concepts": r.unmapped_concepts,
        "warnings": r.warnings,
        "ready_for_db": r.ready_for_db,
    }


# ---------------------------------------------------------------------------
# Endpoints — Export
# ---------------------------------------------------------------------------

@router.post("/export", summary="Generate XBRL/iXBRL export package")
def xbrl_export(req: XBRLExportRequest):
    dp_dict = {dp.dp_id: dp.value for dp in req.data_points}
    res = _export.export(
        entity_name=req.entity_name,
        entity_lei=req.entity_lei,
        period_start=req.period_start,
        period_end=req.period_end,
        data_points=dp_dict,
        currency=req.currency,
        decimals=req.decimals,
    )
    return _ser_export(res)


# ---------------------------------------------------------------------------
# Endpoints — Ingestion
# ---------------------------------------------------------------------------

@router.post("/ingest", summary="Parse XBRL/iXBRL document and extract facts")
def xbrl_ingest(req: XBRLIngestRequest):
    if req.format_hint == "ixbrl":
        res = _ingest.ingest_ixbrl(req.content)
    elif req.format_hint == "xbrl_xml":
        res = _ingest.ingest_xbrl_xml(req.content)
    else:
        res = _ingest.ingest_auto(req.content)
    return _ser_ingestion(res)


@router.post("/ingest/ixbrl", summary="Parse iXBRL HTML document")
def xbrl_ingest_ixbrl(req: XBRLIngestRequest):
    res = _ingest.ingest_ixbrl(req.content)
    return _ser_ingestion(res)


@router.post("/ingest/xbrl-xml", summary="Parse XBRL XML instance document")
def xbrl_ingest_xml(req: XBRLIngestRequest):
    res = _ingest.ingest_xbrl_xml(req.content)
    return _ser_ingestion(res)


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/taxonomy", summary="ESRS XBRL taxonomy mappings")
def ref_taxonomy():
    return _export.get_taxonomy()


@router.get("/ref/validation-rules", summary="ESEF validation rules")
def ref_validation_rules():
    return _export.get_validation_rules()


@router.get("/ref/supported-standards", summary="Supported ESRS/ISSB standards")
def ref_supported_standards():
    return _export.get_supported_standards()


@router.get("/ref/supported-schemas", summary="Supported XBRL schemas for ingestion")
def ref_supported_schemas():
    return _ingest.get_supported_schemas()


@router.get("/ref/concept-mappings", summary="XBRL concept to platform DP mappings")
def ref_concept_mappings():
    return _ingest.get_concept_mappings()


@router.get("/ref/ingestion-stats", summary="Ingestion engine statistics")
def ref_ingestion_stats():
    return {
        "supported_schemas": len(SUPPORTED_SCHEMAS),
        "mapped_concepts": _ingest.get_mapped_concept_count(),
        "export_taxonomy_concepts": len(ESRS_XBRL_TAXONOMY),
        "validation_rules": len(ESEF_VALIDATION_RULES),
    }
