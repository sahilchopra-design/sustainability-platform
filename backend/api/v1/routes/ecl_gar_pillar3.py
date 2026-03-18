"""
API Routes: ECL → GAR → Pillar 3 Orchestration Chain (E1)
==========================================================
POST /api/v1/ecl-gar-pillar3/orchestrate    — Full chain: ECL climate + GAR + Art. 449a output
POST /api/v1/ecl-gar-pillar3/ecl-only       — Stage 1 only: ECL climate overlay
POST /api/v1/ecl-gar-pillar3/gar-only       — Stage 2 only: GAR / BTAR calculation
GET  /api/v1/ecl-gar-pillar3/ref/kpis       — EBA ITS 2022/01 Pillar 3 KPI template
GET  /api/v1/ecl-gar-pillar3/ref/nace-eligible — EU Taxonomy-eligible NACE codes
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from services.ecl_gar_pillar3_orchestrator import (
    ECLGARPillar3Orchestrator,
    ExposureInput,
    PILLAR3_GAR_KPIS,
    GAR_ELIGIBLE_NACE,
)

router = APIRouter(prefix="/api/v1/ecl-gar-pillar3", tags=["ECL-GAR-Pillar3"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ExposureInputModel(BaseModel):
    exposure_id: str
    counterparty_name: str = ""
    asset_class: str = "corporate_loan"
    sector_nace: str = "C26"
    ead_eur: float = Field(..., ge=0)
    pd_base: float = Field(..., ge=0, le=1)
    lgd_base: float = Field(..., ge=0, le=1)
    undrawn_commitment_eur: float = Field(0.0, ge=0)
    flood_return_period_years: int = Field(100, ge=5, le=500)
    transition_risk_level: str = Field("medium", description="low | medium | high")
    taxonomy_eligible: bool = False
    taxonomy_aligned_pct: float = Field(0.0, ge=0, le=100)
    dnsh_compliant: bool = False
    min_social_safeguards: bool = False
    ccm_aligned: bool = False
    cca_aligned: bool = False
    is_sovereign: bool = False
    scenario: str = "BASE"


class OrchestrationRequest(BaseModel):
    entity_name: str
    exposures: List[ExposureInputModel]
    scenario: str = Field("BASE", description="BASE | ADVERSE | SEVERE | OPTIMISTIC")
    reporting_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_domain(m: ExposureInputModel) -> ExposureInput:
    return ExposureInput(**m.model_dump())


def _result_to_dict(r) -> Dict[str, Any]:
    def _sec(s):
        return {
            "section_id": s.section_id,
            "title": s.title,
            "kpis": s.kpis,
            "narrative": s.narrative,
            "gaps": s.gaps,
            "assurance_ready": s.assurance_ready,
        }
    def _exp(e):
        return {
            "exposure_id": e.exposure_id,
            "counterparty_name": e.counterparty_name,
            "ead_eur": e.ead_eur,
            "base_ecl_eur": e.base_ecl_eur,
            "climate_ecl_eur": e.climate_ecl_eur,
            "ecl_uplift_pct": e.ecl_uplift_pct,
            "ead_climate_eur": e.ead_climate_eur,
            "ead_uplift_pct": e.ead_uplift_pct,
            "lgd_ipcc_flood_damage_pct": e.lgd_ipcc_flood_damage_pct,
            "taxonomy_eligible": e.taxonomy_eligible,
            "taxonomy_aligned": e.taxonomy_aligned,
            "taxonomy_aligned_pct": e.taxonomy_aligned_pct,
            "ccm_aligned": e.ccm_aligned,
            "cca_aligned": e.cca_aligned,
            "gar_contribution_eur": e.gar_contribution_eur,
            "taxonomy_gaps": e.taxonomy_gaps,
        }
    return {
        "run_id": r.run_id,
        "entity_name": r.entity_name,
        "reporting_date": r.reporting_date,
        "scenario": r.scenario,
        "exposure_count": r.exposure_count,
        "total_ead_eur": r.total_ead_eur,
        "ecl": {
            "portfolio_base_ecl_eur": r.portfolio_base_ecl_eur,
            "portfolio_climate_ecl_eur": r.portfolio_climate_ecl_eur,
            "portfolio_ecl_uplift_pct": r.portfolio_ecl_uplift_pct,
            "portfolio_ead_uplift_pct": r.portfolio_ead_uplift_pct,
            "portfolio_lgd_flood_damage_pct": r.portfolio_lgd_flood_damage_pct,
        },
        "gar": {
            "gar_numerator_eur": r.gar_numerator_eur,
            "gar_denominator_eur": r.gar_denominator_eur,
            "gar_ratio_pct": r.gar_ratio_pct,
            "btar_ratio_pct": r.btar_ratio_pct,
            "ccm_aligned_eur": r.ccm_aligned_eur,
            "cca_aligned_eur": r.cca_aligned_eur,
        },
        "risk_concentration": {
            "transition_risk_high_pct": r.transition_risk_high_pct,
            "physical_risk_exposed_pct": r.physical_risk_exposed_pct,
        },
        "pillar3_sections": [_sec(s) for s in r.pillar3_sections],
        "pillar3_kpis": r.pillar3_kpis,
        "assurance_readiness_score": r.assurance_readiness_score,
        "gaps": r.gaps,
        "recommendations": r.recommendations,
        "metadata": r.metadata,
        "exposures": [_exp(e) for e in r.exposures],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/orchestrate",
    summary="Full ECL → GAR → Pillar 3 Art. 449a chain",
    description=(
        "Runs all three stages: (1) IFRS 9 ECL with IPCC AR6 climate overlays per EBA GL/2022/16, "
        "(2) EU Taxonomy Green Asset Ratio per CRR Art. 449a + EBA ITS 2022/01, "
        "(3) Pillar 3 Art. 449a disclosure template with assurance readiness scoring."
    ),
)
def orchestrate(req: OrchestrationRequest):
    """Run the full ECL→GAR→Pillar 3 chain for a portfolio."""
    orch = ECLGARPillar3Orchestrator()
    result = orch.orchestrate(
        entity_name=req.entity_name,
        exposures=[_to_domain(e) for e in req.exposures],
        scenario=req.scenario,
        reporting_date=req.reporting_date,
    )
    return _result_to_dict(result)


@router.post(
    "/ecl-only",
    summary="Stage 1 only: ECL climate overlay",
    description="Run just the IFRS 9 ECL climate overlay stage without GAR/Pillar 3 computation.",
)
def ecl_only(req: OrchestrationRequest):
    """Run ECL climate overlay and return per-exposure ECL results."""
    orch = ECLGARPillar3Orchestrator()
    result = orch.orchestrate(
        entity_name=req.entity_name,
        exposures=[_to_domain(e) for e in req.exposures],
        scenario=req.scenario,
        reporting_date=req.reporting_date,
    )
    full = _result_to_dict(result)
    return {
        "run_id": full["run_id"],
        "entity_name": full["entity_name"],
        "scenario": full["scenario"],
        "ecl": full["ecl"],
        "exposures": [
            {k: v for k, v in e.items() if k in (
                "exposure_id", "counterparty_name", "ead_eur",
                "base_ecl_eur", "climate_ecl_eur", "ecl_uplift_pct",
                "ead_climate_eur", "ead_uplift_pct", "lgd_ipcc_flood_damage_pct"
            )}
            for e in full["exposures"]
        ],
    }


@router.post(
    "/gar-only",
    summary="Stage 2 only: GAR / BTAR calculation",
    description="Run only the EU Taxonomy GAR/BTAR classification. Returns taxonomy alignment per exposure.",
)
def gar_only(req: OrchestrationRequest):
    """Run GAR calculation and return per-exposure taxonomy classification."""
    orch = ECLGARPillar3Orchestrator()
    result = orch.orchestrate(
        entity_name=req.entity_name,
        exposures=[_to_domain(e) for e in req.exposures],
        scenario=req.scenario,
        reporting_date=req.reporting_date,
    )
    full = _result_to_dict(result)
    return {
        "run_id": full["run_id"],
        "entity_name": full["entity_name"],
        "gar": full["gar"],
        "exposures": [
            {k: v for k, v in e.items() if k in (
                "exposure_id", "counterparty_name", "ead_eur",
                "taxonomy_eligible", "taxonomy_aligned", "taxonomy_aligned_pct",
                "ccm_aligned", "cca_aligned", "gar_contribution_eur", "taxonomy_gaps"
            )}
            for e in full["exposures"]
        ],
    }


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/kpis", summary="EBA ITS 2022/01 Pillar 3 Art. 449a KPI template")
def ref_kpis():
    """Return the EBA ITS 2022/01 Pillar 3 ESG KPI template rows."""
    return {"pillar3_kpi_template": PILLAR3_GAR_KPIS}


@router.get("/ref/nace-eligible", summary="EU Taxonomy-eligible NACE codes")
def ref_nace():
    """Return EU Taxonomy-eligible NACE sector codes with CCM/CCA flags."""
    return {
        "taxonomy_eligible_nace": {
            nace: {**data, "nace_code": nace}
            for nace, data in GAR_ELIGIBLE_NACE.items()
        },
        "reference": "EU Taxonomy Regulation 2020/852 + Delegated Act 2021/2139",
    }
