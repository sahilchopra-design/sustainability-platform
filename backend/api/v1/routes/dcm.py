"""
DCM (Complete Carbon Credit Methodology) API Routes
=====================================================
Exposes the full DCM engine: 60+ methodologies across CDM, VCS/Verra,
Gold Standard, Nature-based Solutions, CDR, Article 6.4, and CORSIA.

All endpoints follow the pattern:
  POST /api/v1/dcm/calculate       — run a single methodology
  POST /api/v1/dcm/batch           — run multiple methodologies
  GET  /api/v1/dcm/methodologies   — catalogue (filterable)
  GET  /api/v1/dcm/sectors         — sector list
  GET  /api/v1/dcm/standards       — standard list
  POST /api/v1/dcm/compare         — compare two methodologies side-by-side
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.dcm_engine import (
    ALL_METHODOLOGIES,
    calculate,
    list_methodologies,
    get_sectors,
    get_standards,
    batch_calculate,
)

router = APIRouter(prefix="/api/v1/dcm", tags=["Carbon DCM Methodology"])


# ── Request / Response schemas ────────────────────────────────────────────────

class CalculateRequest(BaseModel):
    methodology_code: str = Field(..., description="e.g. VM0007, CDR-DACCS, GS-ICS, CORSIA")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Methodology-specific input parameters")


class BatchItem(BaseModel):
    methodology_code: str
    inputs: Dict[str, Any] = Field(default_factory=dict)


class BatchRequest(BaseModel):
    items: List[BatchItem] = Field(..., min_length=1, max_length=50)


class CompareRequest(BaseModel):
    methodology_a: str
    methodology_b: str
    inputs_a: Dict[str, Any] = Field(default_factory=dict)
    inputs_b: Dict[str, Any] = Field(default_factory=dict)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/calculate")
def run_calculation(body: CalculateRequest) -> Dict[str, Any]:
    """
    Run a single carbon credit methodology calculation.

    Supply the `methodology_code` (e.g. `VM0007`, `CDR-DACCS`, `GS-ICS`)
    and an `inputs` dict with project parameters. All inputs have sensible
    defaults so you can call with `{}` to get a representative estimate.
    """
    try:
        return calculate(body.methodology_code, body.inputs)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Calculation error: {e}")


@router.post("/batch")
def run_batch(body: BatchRequest) -> List[Dict[str, Any]]:
    """
    Run multiple methodology calculations in a single request (up to 50).
    Returns one result per item; failed items include `status: error`.
    """
    requests = [{"methodology_code": item.methodology_code, "inputs": item.inputs}
                for item in body.items]
    return batch_calculate(requests)


@router.get("/methodologies")
def get_methodologies(
    sector: Optional[str] = None,
    standard: Optional[str] = None,
    project_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return the methodology catalogue.  Filterable by `sector`, `standard`,
    or `project_type` (partial match on project_type).

    Example filters:
      ?sector=Forestry
      ?standard=VCS
      ?project_type=REDD
    """
    return list_methodologies(sector=sector, standard=standard, project_type=project_type)


@router.get("/sectors")
def get_sector_list() -> List[str]:
    """Return all sectors represented in the methodology catalogue."""
    return get_sectors()


@router.get("/standards")
def get_standard_list() -> List[str]:
    """Return all standards represented in the methodology catalogue."""
    return get_standards()


@router.get("/methodologies/{code}")
def get_methodology_detail(code: str) -> Dict[str, Any]:
    """Return metadata for a single methodology by code."""
    entry = ALL_METHODOLOGIES.get(code.upper()) or ALL_METHODOLOGIES.get(code)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Methodology '{code}' not found")
    return {
        "code": code,
        "name": entry["name"],
        "sector": entry["sector"],
        "standard": entry["standard"],
        "project_type": entry["project_type"],
    }


@router.post("/compare")
def compare_methodologies(body: CompareRequest) -> Dict[str, Any]:
    """
    Run two methodology calculations and return a side-by-side comparison.
    Useful for evaluating which standard/methodology is most suitable.
    """
    try:
        result_a = calculate(body.methodology_a, body.inputs_a)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Methodology A error: {e}")

    try:
        result_b = calculate(body.methodology_b, body.inputs_b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Methodology B error: {e}")

    def _pick(r: Dict[str, Any], field: str) -> float:
        return float(r.get(field) or 0.0)

    return {
        "methodology_a": result_a,
        "methodology_b": result_b,
        "comparison": {
            "net_climate_benefit_delta_tco2e": round(
                _pick(result_a, "net_climate_benefit") - _pick(result_b, "net_climate_benefit"), 2
            ),
            "emission_reductions_delta_tco2e": round(
                _pick(result_a, "emission_reductions") - _pick(result_b, "emission_reductions"), 2
            ),
            "removal_delta_tco2e": round(
                _pick(result_a, "emission_removals") - _pick(result_b, "emission_removals"), 2
            ),
            "preferred_by_ncb": (
                body.methodology_a
                if _pick(result_a, "net_climate_benefit") >= _pick(result_b, "net_climate_benefit")
                else body.methodology_b
            ),
        },
    }


@router.get("/ref/project-types")
def get_project_types() -> List[Dict[str, str]]:
    """Return all distinct project types with their sector and standard mapping."""
    seen = set()
    result = []
    for code, meta in ALL_METHODOLOGIES.items():
        key = (meta["project_type"], meta["sector"])
        if key not in seen:
            seen.add(key)
            result.append({
                "project_type": meta["project_type"],
                "sector": meta["sector"],
                "example_standard": meta["standard"],
                "example_code": code,
            })
    return sorted(result, key=lambda x: (x["sector"], x["project_type"]))


@router.get("/ref/cdr-pathways")
def get_cdr_pathways() -> List[Dict[str, Any]]:
    """
    Return CDR-specific pathway catalogue with cost and permanence reference data.
    """
    return [
        {
            "pathway": "DACCS",
            "code": "CDR-DACCS",
            "current_cost_usd_per_t": "400–1000",
            "2030_cost_projection_usd_per_t": "200–400",
            "permanence": "1000+ years (geological)",
            "co_benefits": "none",
            "readiness": "Commercial (Climeworks, Carbon Engineering)",
        },
        {
            "pathway": "BECCS",
            "code": "CDR-BECCS",
            "current_cost_usd_per_t": "100–300",
            "2030_cost_projection_usd_per_t": "80–200",
            "permanence": "1000+ years (geological)",
            "co_benefits": "bioenergy production",
            "readiness": "Pilot to commercial",
        },
        {
            "pathway": "Enhanced Rock Weathering",
            "code": "CDR-ERW",
            "current_cost_usd_per_t": "80–200",
            "2030_cost_projection_usd_per_t": "50–100",
            "permanence": "10,000+ years (carbonate minerals)",
            "co_benefits": "soil fertility, crop yield improvement",
            "readiness": "Pilot (Arca, Lithos Carbon)",
        },
        {
            "pathway": "Ocean Alkalinity Enhancement",
            "code": "CDR-OAE",
            "current_cost_usd_per_t": "100–300",
            "2030_cost_projection_usd_per_t": "50–150",
            "permanence": "10,000+ years (ocean carbonate system)",
            "co_benefits": "ocean de-acidification",
            "readiness": "Research to pilot",
        },
        {
            "pathway": "Biochar",
            "code": "CDR-Biochar",
            "current_cost_usd_per_t": "100–250",
            "2030_cost_projection_usd_per_t": "80–150",
            "permanence": "100–1000 years (soil)",
            "co_benefits": "soil improvement, water retention",
            "readiness": "Commercial (Puro.earth, Bioatmos)",
        },
    ]


@router.get("/ref/article6-guidance")
def get_article6_guidance() -> Dict[str, Any]:
    """Return Article 6.2/6.4 rulebook reference summary."""
    return {
        "article_6_2": {
            "description": "Bilateral/cooperative transfers of ITMOs between Parties",
            "key_requirements": [
                "Corresponding adjustments must be applied by host country",
                "Reporting to UNFCCC central accounting and reporting tool (CART)",
                "First transfer from host country = first transfer date",
                "NDC coverage: ITMO must be inside host country NDC boundary",
            ],
        },
        "article_6_4": {
            "description": "UN supervised crediting mechanism (replaces CDM for Paris era)",
            "key_requirements": [
                "Activities authorised by national authorities",
                "Share of Proceeds: 5% adaptation fund + 2% cancellation for overall mitigation",
                "Methodologies approved by Art 6.4 Supervisory Body",
                "Periodic review of additionality (5-year crediting periods)",
                "Transition: CDM projects can transition to Art 6.4 mechanism",
            ],
        },
        "corresponding_adjustments": {
            "formula": "Adjusted NDC = Reported NDC + ITMOs transferred - ITMOs acquired",
            "timing": "At issuance for first transfer; at retirement for final use",
        },
        "corsia": {
            "phase": "Implementation Phase (2024+)",
            "eligible_offsets": "CORSIA eligible units: VCS REDD+, Gold Standard, ACR, CAR, GCC",
            "saf_incentive": "2:1 carbon credit ratio for SAF below 10% lifecycle emission threshold",
        },
    }
