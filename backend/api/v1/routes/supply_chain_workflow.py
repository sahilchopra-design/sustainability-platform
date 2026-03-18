"""
API Routes: Supply Chain Workflow Engine (E5)
=============================================
POST /api/v1/supply-chain-workflow/assess        — Full EUDR+CSDDD+ESRS E4 assessment
POST /api/v1/supply-chain-workflow/assess/batch  — Batch: multiple entities in one call
GET  /api/v1/supply-chain-workflow/ref/regulatory-mapping  — Cross-regulation obligation map
GET  /api/v1/supply-chain-workflow/ref/esrs-e4-disclosures — ESRS E4-1 to E4-8 descriptions
GET  /api/v1/supply-chain-workflow/ref/eudr-commodities    — EUDR Annex I commodities
GET  /api/v1/supply-chain-workflow/ref/country-tiers       — EUDR country risk tiers
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.supply_chain_workflow_engine import (
    SupplierInput,
    SupplyChainWorkflowEngine,
    _REGULATORY_MAPPING,
    _ESRS_E4_DISCLOSURES,
    _EUDR_COMMODITIES,
    _EUDR_HIGH_RISK_COUNTRIES,
    _EUDR_LOW_RISK_COUNTRIES,
)

router = APIRouter(
    prefix="/api/v1/supply-chain-workflow",
    tags=["Supply Chain Workflow"],
)

_ENGINE = SupplyChainWorkflowEngine()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class SupplierInputModel(BaseModel):
    supplier_id: str
    supplier_name: str
    country_of_origin: str = Field(..., description="ISO-3 country code, e.g. BRA")
    commodity: str = Field(..., description="e.g. soy, cattle, wood, cocoa")
    hs_code: Optional[str] = None
    annual_volume_tonnes: float = Field(0.0, ge=0)
    spend_eur: float = Field(0.0, ge=0)
    has_geolocation: bool = False
    certification_scheme: Optional[str] = None
    has_traceability_system: bool = False
    has_supplier_code_of_conduct: bool = False
    has_audit_programme: bool = False
    has_grievance_mechanism: bool = False
    has_biodiversity_impact_assessment: bool = False
    operates_in_sensitive_area: bool = False
    restoration_commitments: bool = False


class AssessmentRequest(BaseModel):
    entity_name: str
    suppliers: List[SupplierInputModel]
    assessment_date: Optional[str] = Field(
        None, description="ISO date YYYY-MM-DD (defaults to today)"
    )


class BatchAssessmentRequest(BaseModel):
    assessments: List[AssessmentRequest]


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _supplier_result_to_dict(r) -> Dict[str, Any]:
    return {
        "supplier_id": r.supplier_id,
        "supplier_name": r.supplier_name,
        "country": r.country,
        "commodity": r.commodity,
        "eudr": {
            "commodity_covered": r.eudr_commodity_covered,
            "country_risk_tier": r.eudr_country_risk_tier,
            "dd_required": r.eudr_dd_required,
            "traceability_score": r.eudr_traceability_score,
            "risk_score": r.eudr_risk_score,
        },
        "csddd": {
            "adverse_impact_count": r.csddd_adverse_impact_count,
            "dd_score": r.csddd_dd_score,
            "high_priority_impacts": r.csddd_high_priority_impacts,
        },
        "esrs_e4": {
            "biodiversity_risk": r.esrs_e4_biodiversity_risk,
            "sensitive_area": r.esrs_e4_sensitive_area,
            "disclosure_flags": r.esrs_e4_disclosure_flags,
        },
        "overall_risk_score": r.overall_risk_score,
        "supplier_status": r.supplier_status,
        "gaps": r.gaps,
        "recommended_actions": r.recommended_actions,
    }


def _assessment_to_dict(a) -> Dict[str, Any]:
    return {
        "run_id": a.run_id,
        "entity_name": a.entity_name,
        "assessment_date": a.assessment_date,
        "supplier_count": a.supplier_count,
        "commodity_count": a.commodity_count,
        "overall_workflow_score": a.overall_workflow_score,
        "workflow_status": a.workflow_status,
        "risk_breakdown": {
            "high_risk_suppliers": a.high_risk_suppliers,
            "medium_risk_suppliers": a.medium_risk_suppliers,
            "low_risk_suppliers": a.low_risk_suppliers,
        },
        "total_gaps": a.total_gaps,
        "critical_gaps": a.critical_gaps,
        "priority_actions": a.priority_actions,
        "regulatory_mapping": a.regulatory_mapping,
        "esrs_e4_disclosure_readiness": a.esrs_e4_disclosure_readiness,
        "suppliers": [_supplier_result_to_dict(r) for r in a.supplier_results],
        "metadata": a.metadata,
    }


def _to_domain(m: SupplierInputModel) -> SupplierInput:
    return SupplierInput(**m.model_dump())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full EUDR + CSDDD + ESRS E4 supply chain workflow assessment",
    description=(
        "Runs the unified supply chain compliance workflow for all supplied suppliers. "
        "Returns per-supplier risk scores (EUDR country tier, CSDDD DD score, ESRS E4 "
        "biodiversity risk), an aggregate workflow status, gap list, and priority actions."
    ),
)
def assess(req: AssessmentRequest):
    result = _ENGINE.assess(
        entity_name=req.entity_name,
        suppliers=[_to_domain(s) for s in req.suppliers],
        assessment_date=req.assessment_date,
    )
    return _assessment_to_dict(result)


@router.post(
    "/assess/batch",
    summary="Batch supply chain workflow — multiple entities",
    description="Run the supply chain workflow for multiple entities in a single request.",
)
def assess_batch(req: BatchAssessmentRequest):
    results = []
    for a_req in req.assessments:
        result = _ENGINE.assess(
            entity_name=a_req.entity_name,
            suppliers=[_to_domain(s) for s in a_req.suppliers],
            assessment_date=a_req.assessment_date,
        )
        results.append(_assessment_to_dict(result))
    return {
        "batch_count": len(results),
        "assessments": results,
    }


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/regulatory-mapping",
    summary="Cross-regulation obligation mapping (EUDR ↔ CSDDD ↔ ESRS E4)",
)
def ref_regulatory_mapping():
    return {
        "mapping_count": len(_REGULATORY_MAPPING),
        "regulatory_mapping": _REGULATORY_MAPPING,
        "reference": (
            "EUDR Regulation (EU) 2023/1115 | CSDDD Directive (EU) 2024/1760 | "
            "ESRS E4 (CSRD Delegated Reg. 2023/2772)"
        ),
    }


@router.get(
    "/ref/esrs-e4-disclosures",
    summary="ESRS E4 disclosure requirements E4-1 through E4-8",
)
def ref_esrs_e4():
    return {
        "disclosure_count": len(_ESRS_E4_DISCLOSURES),
        "disclosures": [
            {"id": dp_id, "description": desc}
            for dp_id, desc in _ESRS_E4_DISCLOSURES.items()
        ],
        "reference": "ESRS E4 — Biodiversity and Ecosystems (CSRD Delegated Reg. 2023/2772)",
    }


@router.get(
    "/ref/eudr-commodities",
    summary="EUDR Annex I commodities in scope",
)
def ref_eudr_commodities():
    return {
        "commodity_count": len(_EUDR_COMMODITIES),
        "commodities": sorted(_EUDR_COMMODITIES),
        "reference": "EUDR Regulation (EU) 2023/1115, Annex I",
    }


@router.get(
    "/ref/country-tiers",
    summary="EUDR Article 29 country risk tiers",
)
def ref_country_tiers():
    return {
        "high_risk": sorted(_EUDR_HIGH_RISK_COUNTRIES),
        "low_risk": sorted(_EUDR_LOW_RISK_COUNTRIES),
        "standard_risk": "All other countries not in high or low lists",
        "reference": "EUDR Art.29 — country benchmarking (Commission delegated acts pending)",
        "note": (
            "Final country lists will be determined by European Commission delegated acts. "
            "This reference table reflects current deforestation-risk country assessments."
        ),
    }
