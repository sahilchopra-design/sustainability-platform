"""
Social Bond & Impact Finance Engine — E85 API Router
Prefix: /api/v1/social-bond
Standards: ICMA Social Bond Principles (SBP) June 2023;
ICMA Impact Reporting Handbook 2023; UN SDG Agenda 2030;
IRIS+ v5.3 (GIIN 2023); IMP Five Dimensions of Impact (2018).
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.social_bond_engine import (
    ICMA_SBP_PROJECT_CATEGORIES,
    IMPACT_MEASUREMENT_STANDARDS,
    SDG_SOCIAL_MAPPING,
    SOCIAL_KPI_LIBRARY,
    SPO_PROVIDERS,
    TARGET_POPULATION_GROUPS,
    SocialBondEngine,
    # E85 named constants (required by spec)
    ICMA_SBP_COMPONENTS,
    SOCIAL_PROJECT_CATEGORIES,
    # E85 module-level functions (required by spec)
    assess_icma_sbp_compliance,
    map_use_of_proceeds,
    assess_target_population,
    score_social_kpis,
    compute_sdg_alignment,
    run_full_assessment,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/social-bond", tags=["E85 Social Bond & Impact Finance"])

_engine = SocialBondEngine()


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ProjectCategoryItem(BaseModel):
    model_config = {"protected_namespaces": ()}
    category: str = Field(..., description="ICMA SBP project category key")
    amount_m: float = Field(..., ge=0, description="Allocation amount €M")
    description: Optional[str] = Field(None, description="Brief description of funded projects")


class PopulationItem(BaseModel):
    model_config = {"protected_namespaces": ()}
    group: str = Field(..., description="Target population group key")
    count: int = Field(0, ge=0, description="Estimated beneficiary count")
    geography: Optional[str] = Field(None, description="Geographic area of beneficiaries")
    measurement_method: Optional[str] = Field(None, description="How beneficiaries are counted/identified")


class KPIItem(BaseModel):
    model_config = {"protected_namespaces": ()}
    name: str = Field(..., description="KPI name")
    value: Optional[float] = Field(None, description="Reported KPI value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    baseline: Optional[float] = Field(None, description="Baseline value for comparison")
    target: Optional[float] = Field(None, description="Target value to be achieved")
    sdg_target: Optional[str] = Field(None, description="Linked SDG target (e.g. '8.5')")


class ICMASBPComplianceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str = Field(..., description="Issuer entity identifier")
    bond_name: str = Field(..., description="Name or ISIN of the social bond")
    total_issuance_m: float = Field(..., ge=0, description="Total bond issuance amount €M")
    currency: str = Field("EUR", description="Bond currency (ISO 4217)")
    has_framework: bool = Field(False, description="Social Bond Framework documented and published")
    has_allocation_reporting: bool = Field(False, description="Committed to annual allocation reporting (ICMA SBP §4)")
    has_impact_reporting: bool = Field(False, description="Committed to impact/outcome reporting (ICMA SBP §4)")
    has_spo: bool = Field(False, description="Second Party Opinion obtained from recognised provider")
    has_dedicated_account: bool = Field(True, description="Net proceeds tracked in dedicated account (ICMA SBP §3)")
    unallocated_proceeds_policy: bool = Field(True, description="Documented policy for unallocated proceeds")
    has_internal_audit: bool = Field(False, description="Internal/external audit of proceeds management")
    excluded_activities_screened: bool = Field(False, description="Excluded activities formally screened")
    project_categories: List[str] = Field(default_factory=list, description="ICMA SBP project category keys")
    target_populations: List[str] = Field(default_factory=list, description="Target population group keys")


class UseOfProceedsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    bond_name: str
    categories: List[ProjectCategoryItem] = Field(..., description="Project categories with allocation amounts")
    total_issuance_m: float = Field(..., ge=0, description="Total issuance €M")


class TargetPopulationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    bond_name: str
    populations: List[PopulationItem] = Field(..., description="Target population group data")
    additionality_evidence: Optional[str] = Field(
        None,
        description="Description of additionality evidence (counterfactual, baseline comparison etc.)",
    )


class SocialKPIRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    bond_name: str
    project_category: str = Field(..., description="Primary ICMA SBP project category")
    kpis: List[KPIItem] = Field(..., description="KPIs submitted in impact report")


class SDGAlignmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    bond_name: str
    project_categories: List[str] = Field(..., description="ICMA SBP project category keys")
    kpis: Optional[List[KPIItem]] = Field(default_factory=list, description="KPIs with SDG target references")


class SocialBondFullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    bond_name: str
    total_issuance_m: float = Field(..., ge=0)
    currency: str = Field("EUR")
    # Framework flags
    has_framework: bool = Field(False)
    has_allocation_reporting: bool = Field(False)
    has_impact_reporting: bool = Field(False)
    has_spo: bool = Field(False)
    has_dedicated_account: bool = Field(True)
    unallocated_proceeds_policy: bool = Field(True)
    has_internal_audit: bool = Field(False)
    excluded_activities_screened: bool = Field(False)
    # Core data
    project_categories: List[str] = Field(default_factory=list)
    target_populations: List[str] = Field(default_factory=list)
    categories: Optional[List[ProjectCategoryItem]] = None
    populations: Optional[List[PopulationItem]] = None
    kpis: Optional[List[KPIItem]] = None
    primary_category: Optional[str] = None
    additionality_evidence: Optional[str] = None


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/icma-sbp-compliance", summary="ICMA SBP 4-component compliance assessment")
async def icma_sbp_compliance(req: ICMASBPComplianceRequest) -> Dict[str, Any]:
    """
    Score the four ICMA Social Bond Principles components:

    1. Use of Proceeds (30%) — eligible project categories + excluded activities screen
    2. Process for Project Evaluation & Selection (25%) — framework, target population, SPO
    3. Management of Proceeds (25%) — dedicated account, unallocated policy, audit
    4. Reporting (20%) — allocation + impact reporting commitment

    Returns overall SBP score, alignment status, gaps, and SPO provider recommendations.

    Reference: ICMA Social Bond Principles (SBP) June 2023.
    """
    try:
        bond_data = req.model_dump()
        result = _engine.assess_icma_sbp_compliance(bond_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("icma_sbp_compliance error: %s", exc)
        raise HTTPException(status_code=500, detail="ICMA SBP compliance assessment failed")


@router.post("/use-of-proceeds", summary="Social bond use of proceeds eligibility and allocation")
async def use_of_proceeds(req: UseOfProceedsRequest) -> Dict[str, Any]:
    """
    Assess project category eligibility against ICMA SBP Appendix 1,
    proceeds allocation completeness, and excluded activities screen.

    Returns allocation table, primary/secondary category assignment,
    and ICMA HS/CN code mapping where applicable.

    Reference: ICMA SBP 2023 §1 — Use of Proceeds; Appendix 1.
    """
    try:
        categories_list = [c.model_dump() for c in req.categories]
        result = _engine.assess_use_of_proceeds(
            entity_id=req.entity_id,
            bond_name=req.bond_name,
            categories=categories_list,
            total_issuance_m=req.total_issuance_m,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("use_of_proceeds error: %s", exc)
        raise HTTPException(status_code=500, detail="Use of proceeds assessment failed")


@router.post("/target-population", summary="Social bond beneficiary and additionality assessment")
async def target_population(req: TargetPopulationRequest) -> Dict[str, Any]:
    """
    Validate target population groups against ICMA SBP recognised definitions,
    assess beneficiary count methodology quality, additionality evidence,
    and geographic coverage.

    Reference: ICMA SBP 2023 §2 — Process for Project Evaluation and Selection;
    UN SDG definitions; ILO labour standards.
    """
    try:
        populations_list = [p.model_dump() for p in req.populations]
        result = _engine.assess_target_population(
            entity_id=req.entity_id,
            bond_name=req.bond_name,
            populations_data=populations_list,
            additionality_evidence=req.additionality_evidence,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("target_population error: %s", exc)
        raise HTTPException(status_code=500, detail="Target population assessment failed")


@router.post("/social-kpis", summary="Social bond KPI quality scoring")
async def social_kpis(req: SocialKPIRequest) -> Dict[str, Any]:
    """
    Score submitted KPIs on quality dimensions:
    - Quantification (value reported)
    - Baseline availability
    - Target setting
    - SDG target linkage
    - ICMA KPI library alignment

    Returns overall KPI quality score (0-100), quality tier (Gold/Silver/Bronze),
    and suggestions for additional KPIs.

    Reference: ICMA Impact Reporting Handbook 2023; IRIS+ v5.3 (GIIN 2023).
    """
    try:
        kpis_list = [k.model_dump() for k in req.kpis]
        result = _engine.score_social_kpis(
            entity_id=req.entity_id,
            bond_name=req.bond_name,
            project_category=req.project_category,
            kpis_list=kpis_list,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("social_kpis error: %s", exc)
        raise HTTPException(status_code=500, detail="Social KPI scoring failed")


@router.post("/sdg-alignment", summary="SDG mapping and contribution score for social bond")
async def sdg_alignment(req: SDGAlignmentRequest) -> Dict[str, Any]:
    """
    Map project categories and KPIs to UN SDG goals and targets.

    Returns SDG matrix (goals addressed, weight, targets), primary and secondary SDGs,
    SDG contribution score (0-100), and breadth tier (comprehensive/broad/focused).

    Reference: UN SDG Agenda 2030; ICMA SDG Mapping to SBP 2023.
    """
    try:
        kpis_list = [k.model_dump() for k in (req.kpis or [])]
        result = _engine.map_sdg_alignment(
            entity_id=req.entity_id,
            bond_name=req.bond_name,
            project_categories=req.project_categories,
            kpis=kpis_list,
        )
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("sdg_alignment error: %s", exc)
        raise HTTPException(status_code=500, detail="SDG alignment mapping failed")


@router.post("/full-assessment", summary="Complete social bond assessment — all components")
async def full_assessment(req: SocialBondFullAssessmentRequest) -> Dict[str, Any]:
    """
    Orchestrate all social bond sub-assessments:
    - ICMA SBP 4-component compliance
    - Use of Proceeds eligibility
    - Target population validation and additionality
    - KPI quality scoring
    - SDG alignment mapping
    - Composite impact score

    Returns bond_tier: Gold (≥80) | Silver (≥65) | Bronze (≥50) | Standard (<50).

    Reference: ICMA Social Bond Principles (SBP) June 2023; UN SDG Agenda 2030;
    IRIS+ v5.3 (GIIN 2023); IMP Five Dimensions (2018).
    """
    try:
        bond_data = req.model_dump()
        entity_id = bond_data.pop("entity_id")

        # Convert nested Pydantic sub-models
        if bond_data.get("categories"):
            bond_data["categories"] = [
                c if isinstance(c, dict) else c.model_dump() for c in req.categories or []
            ]
        if bond_data.get("populations"):
            bond_data["populations"] = [
                p if isinstance(p, dict) else p.model_dump() for p in req.populations or []
            ]
        if bond_data.get("kpis"):
            bond_data["kpis"] = [
                k if isinstance(k, dict) else k.model_dump() for k in req.kpis or []
            ]

        result = _engine.run_full_assessment(entity_id=entity_id, bond_data=bond_data)
        return {"status": "success", "data": result}
    except Exception as exc:
        logger.exception("full_assessment error: %s", exc)
        raise HTTPException(status_code=500, detail="Full social bond assessment failed")


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/project-categories", summary="9 ICMA SBP project categories")
async def ref_project_categories() -> Dict[str, Any]:
    """
    Return the 9 ICMA Social Bond Principles project categories with
    ICMA codes, eligible activities, typical KPIs and primary SDG alignment.

    Reference: ICMA SBP June 2023 Appendix 1.
    """
    return {
        "status": "success",
        "count": len(ICMA_SBP_PROJECT_CATEGORIES),
        "data": ICMA_SBP_PROJECT_CATEGORIES,
        "ref": "ICMA Social Bond Principles (SBP) June 2023 — Appendix 1",
    }


@router.get("/ref/target-populations", summary="10 ICMA SBP target population groups")
async def ref_target_populations() -> Dict[str, Any]:
    """
    Return the 10 recognised target population groups with ICMA definitions,
    measurement approaches, proxy indicators and UN SDG references.

    Reference: ICMA SBP 2023 §2; UN SDG definitions; ILO Convention 169.
    """
    return {
        "status": "success",
        "count": len(TARGET_POPULATION_GROUPS),
        "data": TARGET_POPULATION_GROUPS,
        "ref": "ICMA SBP June 2023 §2 — Process for Project Evaluation; UN SDG Agenda 2030",
    }


@router.get("/ref/kpi-library", summary="40 social impact KPIs mapped to categories and SDGs")
async def ref_kpi_library() -> Dict[str, Any]:
    """
    Return the 40-KPI social impact library mapped to project category,
    target population, SDG target, unit and measurement guidance.

    Reference: ICMA Impact Reporting Handbook 2023; IRIS+ v5.3 (GIIN 2023).
    """
    # Group by category for convenience
    by_category: Dict[str, List] = {}
    for kpi in SOCIAL_KPI_LIBRARY:
        cat = kpi["category"]
        by_category.setdefault(cat, []).append(kpi)

    return {
        "status": "success",
        "total_kpis": len(SOCIAL_KPI_LIBRARY),
        "categories_covered": len(by_category),
        "kpis_by_category": by_category,
        "all_kpis": SOCIAL_KPI_LIBRARY,
        "ref": "ICMA Impact Reporting Handbook 2023; IRIS+ v5.3 (GIIN 2023)",
    }


@router.get("/ref/sdg-mapping", summary="SDG-to-social-bond project category mapping")
async def ref_sdg_mapping() -> Dict[str, Any]:
    """
    Return SDG goals 1, 2, 3, 4, 5, 6, 8, 10, 11 and 16 mapped to
    relevant ICMA SBP project categories and SDG targets.

    Reference: ICMA SDG Mapping to SBP 2023; UN SDG Agenda 2030.
    """
    summary = []
    for goal_num, data in SDG_SOCIAL_MAPPING.items():
        summary.append({
            "sdg_goal": goal_num,
            "sdg_title": data["title"],
            "relevant_categories": data["categories"],
            "target_ids": data["target_ids"],
        })

    return {
        "status": "success",
        "sdgs_covered": len(SDG_SOCIAL_MAPPING),
        "data": summary,
        "impact_measurement_frameworks": {
            k: {"framework": v["framework"], "url": v["url"]}
            for k, v in IMPACT_MEASUREMENT_STANDARDS.items()
        },
        "spo_providers": {
            k: {"full_name": v["full_name"], "focus": v["focus"], "turnaround_weeks": v["turnaround_weeks"]}
            for k, v in SPO_PROVIDERS.items()
        },
        "ref": "ICMA SDG Mapping to SBP 2023; UN SDG Agenda 2030",
    }

