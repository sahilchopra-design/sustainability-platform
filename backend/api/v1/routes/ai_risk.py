"""
ai_risk.py — E76 AI & ML Risk Finance Routes
EU AI Act 2024/1689 | NIST AI RMF 1.0 | GDPR Art 22 | AI Liability Directive 2022
"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

from services.ai_risk_engine import (
    classify_ai_system,
    assess_nist_rmf,
    detect_algorithmic_bias,
    score_explainability,
    calculate_ai_liability,
    ANNEX3_HIGH_RISK_CATEGORIES,
    PROHIBITED_PRACTICES,
    NIST_RMF_FUNCTIONS,
    BIAS_METRICS,
    ENFORCEMENT_TIMELINE,
)

router = APIRouter(prefix="/api/v1/ai-risk", tags=["E76 AI & ML Risk Finance"])


# ── Request Models ─────────────────────────────────────────────────────────────

class ClassifySystemRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    system_name: str = Field(..., description="Name of the AI system")
    use_case: str = Field(..., description="Describe the AI system's use case and functionality")
    sector: str = Field(..., description="Sector of deployment (banking, healthcare, recruitment, etc.)")
    automated_decision_making: bool = Field(False, description="Does the system make automated decisions affecting individuals?")


class AssessNistRmfRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    system_name: str = Field(..., description="Name of the AI system")
    functions: list[str] = Field(default_factory=list, description="NIST RMF functions implemented: GOVERN, MAP, MEASURE, MANAGE")


class DetectBiasRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    model_type: str = Field(..., description="Type of ML model (classification, regression, ranking, etc.)")
    protected_attributes: list[str] = Field(..., description="Protected attributes to test (gender, race, age, disability, etc.)")
    performance_metrics: dict[str, float] = Field(default_factory=dict, description="Model performance metrics by group")


class ScoreExplainabilityRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    model_type: str = Field(..., description="Type of ML model")
    explanation_methods: list[str] = Field(default_factory=list, description="XAI methods available (SHAP, LIME, attention, gradient, counterfactual, prototype, rule_extraction)")


class CalculateLiabilityRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    system_type: str = Field(..., description="Type of AI system (high_risk, limited_risk, gpai)")
    harm_scenarios: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of harm scenarios with: name, harm_type (physical/property/psychological/fundamental_rights/data_loss), probability (0-1), harm_magnitude_usd"
    )


# ── Response Models ────────────────────────────────────────────────────────────

class ClassifySystemResponse(BaseModel):
    entity_id: str
    system_name: str
    ai_act_risk_category: str
    prohibited_practice_flags: list[dict[str, Any]]
    high_risk_requirements: dict[str, Any]
    transparency_obligations: list[str]
    applicable_annex3_categories: list[dict[str, Any]]
    gpai_model_flag: bool
    gpai_systemic_risk_flag: bool
    ce_marking_required: bool
    gdpr_art22_applicable: bool
    regulatory_overlap: list[str]
    max_penalty_pct_global_turnover: float
    max_penalty_usd: float
    enforcement_timeline: list[dict[str, Any]]
    assessed_at: str


class AssessNistRmfResponse(BaseModel):
    entity_id: str
    system_name: str
    nist_rmf_version: str
    overall_score: float
    risk_tier: str
    maturity_level: int
    function_scores: dict[str, Any]
    total_subcategories_assessed: int
    gap_analysis: dict[str, Any]
    recommended_actions: list[dict[str, Any]]
    certification_readiness: dict[str, Any]
    assessed_at: str


class DetectBiasResponse(BaseModel):
    entity_id: str
    model_type: str
    protected_attributes: list[str]
    overall_bias_score: float
    disparate_impact_ratio: float
    intersectionality_score: float
    gdpr_article22_profiling_flag: bool
    bias_results_by_attribute: list[dict[str, Any]]
    bias_metrics_used: list[str]
    total_violations: int
    regulatory_exposure: dict[str, Any]
    assessed_at: str


class ScoreExplainabilityResponse(BaseModel):
    entity_id: str
    model_type: str
    explanation_methods_provided: list[str]
    available_xai_methods: dict[str, bool]
    method_coverage_score: float
    overall_explainability_score: float
    xai_maturity_level: int
    xai_maturity_label: str
    intrinsic_interpretability: bool
    annex12_transparency: dict[str, Any]
    gdpr_recital71: dict[str, Any]
    recommendations: list[Optional[str]]
    assessed_at: str


class CalculateLiabilityResponse(BaseModel):
    entity_id: str
    system_type: str
    liability_frameworks: dict[str, Any]
    total_expected_liability_usd: float
    scenario_assessments: list[dict[str, Any]]
    insurance: dict[str, Any]
    do_exposure: dict[str, Any]
    mitigation_actions: list[str]
    assessed_at: str


# ── POST Endpoints ─────────────────────────────────────────────────────────────

@router.post("/classify-system", response_model=ClassifySystemResponse, summary="EU AI Act Risk Classification")
async def classify_system(req: ClassifySystemRequest) -> ClassifySystemResponse:
    """
    Classify an AI system under EU AI Act 2024/1689.
    Returns: prohibited/high_risk/limited_risk/minimal_risk category, Annex III applicability,
    prohibited practice flags, CE marking requirements, GPAI model flag, penalty exposure.
    """
    result = classify_ai_system(
        entity_id=req.entity_id,
        system_name=req.system_name,
        use_case=req.use_case,
        sector=req.sector,
        automated_decision_making=req.automated_decision_making,
    )
    return ClassifySystemResponse(**result)


@router.post("/assess-nist-rmf", response_model=AssessNistRmfResponse, summary="NIST AI RMF 1.0 Assessment")
async def assess_nist_rmf_endpoint(req: AssessNistRmfRequest) -> AssessNistRmfResponse:
    """
    Assess AI system governance against NIST AI RMF 1.0.
    Scores all 4 functions (GOVERN/MAP/MEASURE/MANAGE) across 75 subcategories.
    Returns risk tier, maturity level, gap analysis, and recommended actions.
    """
    result = assess_nist_rmf(
        entity_id=req.entity_id,
        system_name=req.system_name,
        functions=req.functions,
    )
    return AssessNistRmfResponse(**result)


@router.post("/detect-bias", response_model=DetectBiasResponse, summary="Algorithmic Bias Detection")
async def detect_bias(req: DetectBiasRequest) -> DetectBiasResponse:
    """
    Detect algorithmic bias across protected attributes.
    Computes 6 fairness metrics: demographic parity, equalised odds, calibration,
    counterfactual fairness, individual fairness, statistical parity difference.
    Flags GDPR Article 22 profiling concerns and intersectionality.
    """
    result = detect_algorithmic_bias(
        entity_id=req.entity_id,
        model_type=req.model_type,
        protected_attributes=req.protected_attributes,
        performance_metrics=req.performance_metrics,
    )
    return DetectBiasResponse(**result)


@router.post("/score-explainability", response_model=ScoreExplainabilityResponse, summary="XAI Explainability Scoring")
async def score_explainability_endpoint(req: ScoreExplainabilityRequest) -> ScoreExplainabilityResponse:
    """
    Score AI system explainability against EU AI Act Annex XII and GDPR Recital 71.
    Assesses SHAP/LIME/attention/gradient availability, XAI maturity (1-5),
    right-to-explanation compliance, and transparency documentation.
    """
    result = score_explainability(
        entity_id=req.entity_id,
        model_type=req.model_type,
        explanation_methods=req.explanation_methods,
    )
    return ScoreExplainabilityResponse(**result)


@router.post("/calculate-liability", response_model=CalculateLiabilityResponse, summary="AI Liability Exposure Calculation")
async def calculate_liability(req: CalculateLiabilityRequest) -> CalculateLiabilityResponse:
    """
    Calculate AI liability exposure under EU AI Liability Directive 2022 and
    Product Liability Directive 2023/2853. Assesses fault-based and strict liability,
    insurance coverage gap, and D&O exposure from AI governance failures.
    """
    result = calculate_ai_liability(
        entity_id=req.entity_id,
        system_type=req.system_type,
        harm_scenarios=req.harm_scenarios,
    )
    return CalculateLiabilityResponse(**result)


# ── GET Reference Endpoints ────────────────────────────────────────────────────

@router.get("/ref/annex3-categories", summary="EU AI Act Annex III High-Risk Categories")
async def get_annex3_categories() -> dict[str, Any]:
    """
    Return all 23 EU AI Act Annex III high-risk system categories with descriptions and examples.
    """
    return {
        "regulation": "EU AI Act Regulation (EU) 2024/1689",
        "annex": "Annex III — High-Risk AI Systems",
        "categories_count": len(ANNEX3_HIGH_RISK_CATEGORIES),
        "categories": ANNEX3_HIGH_RISK_CATEGORIES,
    }


@router.get("/ref/prohibited-practices", summary="EU AI Act Prohibited AI Practices")
async def get_prohibited_practices() -> dict[str, Any]:
    """
    Return all 8 prohibited AI practices under EU AI Act Article 5.
    Effective from 2 February 2025.
    """
    return {
        "regulation": "EU AI Act Regulation (EU) 2024/1689",
        "article": "Article 5 — Prohibited AI Practices",
        "effective_date": "2025-02-02",
        "practices_count": len(PROHIBITED_PRACTICES),
        "practices": PROHIBITED_PRACTICES,
    }


@router.get("/ref/nist-functions", summary="NIST AI RMF 1.0 Functions and Subcategories")
async def get_nist_functions() -> dict[str, Any]:
    """
    Return NIST AI RMF 1.0 framework with all 4 functions and subcategory IDs.
    """
    total_subcategories = sum(len(v["subcategories"]) for v in NIST_RMF_FUNCTIONS.values())
    return {
        "framework": "NIST AI Risk Management Framework",
        "version": "1.0",
        "published": "2023-01-26",
        "total_subcategories": total_subcategories,
        "functions": {
            name: {
                "description": data["description"],
                "subcategory_count": len(data["subcategories"]),
                "subcategories": data["subcategories"],
            }
            for name, data in NIST_RMF_FUNCTIONS.items()
        },
    }


@router.get("/ref/bias-metrics", summary="Algorithmic Fairness Metrics Reference")
async def get_bias_metrics() -> dict[str, Any]:
    """
    Return 6 algorithmic bias/fairness metrics with descriptions, thresholds and GDPR relevance.
    """
    return {
        "framework": "NIST SP 1270 Towards a Standard for Identifying and Managing Bias in AI + IEEE P7003",
        "regulatory_basis": "GDPR Article 22, EU AI Act Articles 9-10, EU Equal Treatment Directives",
        "metrics_count": len(BIAS_METRICS),
        "metrics": BIAS_METRICS,
        "intersectionality_note": "Intersectionality score captures amplified bias at intersection of multiple protected attributes",
    }


@router.get("/ref/enforcement-timeline", summary="EU AI Act Enforcement Timeline 2024-2027")
async def get_enforcement_timeline() -> dict[str, Any]:
    """
    Return EU AI Act phased enforcement timeline from August 2024 to August 2027,
    including EU AI Office establishment and AI Liability Directive milestones.
    """
    return {
        "regulation": "Regulation (EU) 2024/1689 — EU AI Act",
        "entry_into_force": "2024-08-01",
        "general_application": "2026-08-02",
        "milestones": ENFORCEMENT_TIMELINE,
        "penalty_regime": {
            "prohibited_practices_max_pct": 7.0,
            "high_risk_max_pct": 3.0,
            "other_infringements_max_pct": 1.5,
            "sme_cap_eur_m": 7.5,
        },
    }
