"""
E77 — AI Governance & ESG Routes
=================================
Prefix: /api/v1/ai-governance
Tags:   E77 AI Governance ESG
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai_governance_engine import (
    EU_AI_ACT_HIGH_RISK_CATEGORIES,
    MODEL_ENERGY_PROFILES,
    NIST_RMF_CATEGORIES,
    _OECD_PRINCIPLES,
    AIGovernanceEngine,
    AIPortfolioInput,
    AISystemInput,
    BiasAssessmentInput,
)

router = APIRouter(prefix="/api/v1/ai-governance", tags=["E77 AI Governance ESG"])
_engine = AIGovernanceEngine()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AISystemRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    system_id: str = Field(..., example="AI_SYS_001")
    system_name: str = Field(..., example="Credit Scoring Model v3")
    ai_act_category: Optional[str] = Field(
        None, example="essential_services",
        description="Key from EU AI Act high-risk categories (e.g. essential_services, employment_hr)"
    )
    is_gpai: bool = Field(False, description="Is this a General Purpose AI model?")
    is_in_scope_eu_ai_act: bool = True
    parameter_scale: str = Field(
        "1b_10b", example="1b_10b",
        description="sub_1b | 1b_10b | 10b_100b | over_100b"
    )
    daily_queries: Optional[float] = Field(None, example=50_000)
    deployment_region: str = Field("EU", example="EU")
    deployment_grid_carbon_gco2_kwh: float = Field(
        311.0, example=311.0,
        description="Grid carbon intensity of deployment data centre (gCO2e/kWh)"
    )
    training_complete: bool = True
    nist_rmf_scores: Optional[Dict[str, float]] = Field(
        None,
        example={"GV-1": 1.0, "GV-2": 0.5, "MP-1": 1.0, "MS-1": 0.5, "MG-1": 0.0},
        description="Dict of {category_id: score} where score in {0, 0.5, 1}"
    )
    oecd_scores: Optional[Dict[str, float]] = Field(
        None,
        example={"ig_1": 0.5, "hc_1": 1.0, "tp_1": 0.5, "rb_1": 0.0, "ac_1": 0.5},
        description="Dict of {sub_indicator_id: score} where score in {0, 0.5, 1}"
    )
    model_card_fields: Optional[Dict[str, bool]] = Field(
        None,
        example={
            "model_details": True,
            "intended_use": True,
            "factors": False,
            "metrics": True,
            "evaluation_data": True,
            "training_data": False,
            "ethical_considerations": True,
            "out_of_scope_uses": True,
            "environmental_impact": False,
        }
    )
    sector: Optional[str] = Field(None, example="financial_services")
    description: Optional[str] = Field(None, example="Credit risk assessment for retail lending.")
    developer_name: Optional[str] = Field(None, example="FinTech Analytics Ltd")


class EUAIActRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    system_id: str = Field(..., example="AI_SYS_001")
    system_name: str = Field(..., example="Hiring AI")
    ai_act_category: Optional[str] = Field(None, example="employment_hr")
    is_gpai: bool = False
    is_in_scope_eu_ai_act: bool = True
    model_card_fields: Optional[Dict[str, bool]] = None


class NISTRMFRequest(BaseModel):
    system_id: str = Field(..., example="AI_SYS_001")
    system_name: str = Field(..., example="Credit Scoring Model")
    nist_rmf_scores: Optional[Dict[str, float]] = Field(
        None,
        example={
            "GV-1": 1.0, "GV-2": 1.0, "GV-3": 0.5, "GV-4": 0.0, "GV-5": 0.5, "GV-6": 1.0,
            "MP-1": 1.0, "MP-2": 0.5, "MP-3": 0.5, "MP-4": 0.0, "MP-5": 0.5,
            "MS-1": 1.0, "MS-2": 0.5, "MS-3": 0.0, "MS-4": 0.5,
            "MG-1": 1.0, "MG-2": 0.5, "MG-3": 0.0, "MG-4": 0.0,
        }
    )


class BiasAssessmentRequest(BaseModel):
    system_id: str = Field(..., example="AI_SYS_001")
    protected_characteristics: List[str] = Field(
        default_factory=list,
        example=["gender", "race_ethnicity", "age"],
        description="Subset of: gender, race_ethnicity, age, disability, religion, sexual_orientation, nationality"
    )
    metric_values: Optional[Dict[str, Dict[str, float]]] = Field(
        None,
        example={
            "gender": {"disparate_impact_ratio": 0.76, "statistical_parity_difference": -0.08},
            "race_ethnicity": {"disparate_impact_ratio": 0.65, "statistical_parity_difference": -0.15},
        },
        description="Per-characteristic metric dict: {char: {metric_name: value}}"
    )
    sample_size: Optional[int] = Field(None, example=5000)
    assessment_date: Optional[str] = Field(None, example="2024-06-01")
    test_dataset_description: Optional[str] = Field(
        None, example="Hold-out test set from 2023 loan applications."
    )


class EnergyFootprintRequest(BaseModel):
    system_id: str = Field(..., example="AI_SYS_001")
    system_name: str = Field(..., example="LLM Inference Service")
    parameter_scale: str = Field(
        "10b_100b", example="10b_100b",
        description="sub_1b | 1b_10b | 10b_100b | over_100b"
    )
    daily_queries: Optional[float] = Field(100_000, example=100_000)
    deployment_grid_carbon_gco2_kwh: float = Field(
        311.0, example=311.0,
        description="Grid carbon intensity of deployment (gCO2e/kWh)"
    )
    training_complete: bool = True
    deployment_region: str = "EU"


class ModelCardRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    system_id: str = Field(..., example="AI_SYS_001")
    system_name: str = Field(..., example="Fraud Detection Model")
    model_card_fields: Optional[Dict[str, bool]] = Field(
        None,
        example={
            "model_details": True,
            "intended_use": True,
            "factors": True,
            "metrics": True,
            "evaluation_data": False,
            "training_data": False,
            "quantitative_analysis": False,
            "ethical_considerations": True,
            "caveats_recommendations": False,
            "out_of_scope_uses": True,
            "technical_specifications": False,
            "environmental_impact": False,
        }
    )


class AIPortfolioRequest(BaseModel):
    portfolio_id: str = Field(..., example="AI_PORT_001")
    systems: List[Dict[str, Any]] = Field(
        ...,
        example=[
            {
                "system_id": "AI_001",
                "system_name": "Credit Scoring Model",
                "ai_act_category": "essential_services",
                "parameter_scale": "sub_1b",
                "daily_queries": 20000,
                "deployment_grid_carbon_gco2_kwh": 56.0,
                "model_card_fields": {"model_details": True, "intended_use": True},
            },
            {
                "system_id": "AI_002",
                "system_name": "HR Screening AI",
                "ai_act_category": "employment_hr",
                "parameter_scale": "1b_10b",
                "daily_queries": 5000,
                "deployment_grid_carbon_gco2_kwh": 311.0,
            },
        ]
    )
    organisation_name: Optional[str] = Field(None, example="FinCorp ESG Analytics")
    reporting_period: str = Field("2024", example="2024")
    organisation_sector: Optional[str] = Field(None, example="financial_services")


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full AI system ESG governance assessment",
    response_model=Dict[str, Any],
)
def assess_ai_system(request: AISystemRequest) -> Dict[str, Any]:
    """
    Full ESG governance assessment for a single AI system.

    Integrates:
    - EU AI Act 2024/1689 risk tier classification and compliance scoring
    - NIST AI RMF 1.0 scoring (Govern/Map/Measure/Manage)
    - OECD AI Principles 2023 scoring
    - AI energy and Scope 2 emissions (training + inference)
    - Algorithmic bias severity (default conservative without explicit metrics)
    - Model card completeness (12-field NIST/Google standard)
    - ESG composite score: Governance 35% / Environmental 30% / Social 35%

    Returns overall ESG composite score (0-100) and tier
    (leading/advanced/developing/initial).
    """
    try:
        sys_input = AISystemInput(
            system_id=request.system_id,
            system_name=request.system_name,
            ai_act_category=request.ai_act_category,
            is_gpai=request.is_gpai,
            is_in_scope_eu_ai_act=request.is_in_scope_eu_ai_act,
            parameter_scale=request.parameter_scale,
            daily_queries=request.daily_queries,
            deployment_region=request.deployment_region,
            deployment_grid_carbon_gco2_kwh=request.deployment_grid_carbon_gco2_kwh,
            training_complete=request.training_complete,
            nist_rmf_scores=request.nist_rmf_scores,
            oecd_scores=request.oecd_scores,
            model_card_fields=request.model_card_fields,
            sector=request.sector,
            description=request.description,
            developer_name=request.developer_name,
        )
        result = _engine.assess_ai_system(sys_input)
        return {
            "system_id": result.system_id,
            "system_name": result.system_name,
            "eu_ai_act": {
                "risk_tier": result.eu_ai_act_risk_tier,
                "score": result.eu_ai_act_score,
                "gaps": result.eu_ai_act_gaps,
            },
            "nist_rmf": {
                "score": result.nist_rmf_score,
                "tier": result.nist_rmf_tier,
            },
            "oecd_principles": {
                "score": result.oecd_score,
            },
            "energy_emissions": {
                "training_energy_mwh": result.training_energy_mwh,
                "inference_annual_energy_mwh": result.inference_annual_energy_mwh,
                "annual_scope2_tco2e": result.annual_scope2_tco2e,
            },
            "bias": {
                "severity": result.bias_severity,
                "flags": result.bias_flags,
            },
            "model_card": {
                "completeness_pct": result.model_card_completeness_pct,
                "gaps": result.model_card_gaps,
            },
            "esg_composite": {
                "governance_score": result.governance_score,
                "environmental_score": result.environmental_score,
                "social_score": result.social_score,
                "composite_score": result.esg_composite_score,
                "tier": result.esg_tier,
            },
            "summary": result.summary,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/eu-ai-act",
    summary="EU AI Act 2024/1689 risk tier classification",
    response_model=Dict[str, Any],
)
def classify_eu_ai_act(request: EUAIActRequest) -> Dict[str, Any]:
    """
    Classify an AI system under EU AI Act 2024/1689.

    Determines risk tier:
    - unacceptable: Art 5 prohibited practices (social scoring, subliminal manipulation, etc.)
    - high_risk: Annex III / Art 6 systems (biometrics, critical infrastructure, employment, etc.)
    - limited_risk: Art 50 transparency obligations (chatbots, deepfakes)
    - minimal_risk: No mandatory obligations

    For high-risk systems, derives applicable Art 9/10/11/13/14/15/17/43/49 requirements
    and scores compliance based on available documentation evidence.
    """
    try:
        sys_input = AISystemInput(
            system_id=request.system_id,
            system_name=request.system_name,
            ai_act_category=request.ai_act_category,
            is_gpai=request.is_gpai,
            is_in_scope_eu_ai_act=request.is_in_scope_eu_ai_act,
            model_card_fields=request.model_card_fields,
        )
        return _engine.classify_eu_ai_act_risk(sys_input)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/nist-rmf",
    summary="NIST AI RMF 1.0 scoring",
    response_model=Dict[str, Any],
)
def score_nist_rmf(request: NISTRMFRequest) -> Dict[str, Any]:
    """
    Score an AI system against NIST AI Risk Management Framework 1.0 (January 2023).

    Evaluates 4 core functions with 19 sub-categories:
    - Govern (GV-1 to GV-6): AI risk culture, policies, accountability
    - Map (MP-1 to MP-5): Context, categorisation, lifecycle risk identification
    - Measure (MS-1 to MS-4): Metrics, performance, fairness, adversarial testing
    - Manage (MG-1 to MG-4): Prioritisation, mitigation, monitoring, incident response

    Provide nist_rmf_scores dict with values in {0, 0.5, 1} for full scoring.
    Returns overall score (0-100), RMF maturity tier, and improvement gaps.
    """
    try:
        sys_input = AISystemInput(
            system_id=request.system_id,
            system_name=request.system_name,
            nist_rmf_scores=request.nist_rmf_scores,
        )
        return _engine.score_nist_rmf(sys_input)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/bias-assessment",
    summary="Algorithmic bias assessment (7 protected characteristics)",
    response_model=Dict[str, Any],
)
def assess_algorithmic_bias(request: BiasAssessmentRequest) -> Dict[str, Any]:
    """
    Algorithmic bias assessment across up to 7 protected characteristics.

    Evaluates three fairness metrics per characteristic:
    - Disparate Impact Ratio (DIR): adverse if < 0.80 (4/5 Rule, EEOC / EU case law)
    - Statistical Parity Difference (SPD): adverse if < -0.10
    - Equalized Odds parity gap: adverse if |gap| > 0.10

    Severity tiers: critical (DIR < 0.60), high (DIR < 0.70), medium (DIR < 0.80), low.

    Characteristics: gender, race_ethnicity, age, disability, religion,
    sexual_orientation, nationality.
    """
    try:
        bias_input = BiasAssessmentInput(
            system_id=request.system_id,
            protected_characteristics=request.protected_characteristics,
            metric_values=request.metric_values,
            sample_size=request.sample_size,
            assessment_date=request.assessment_date,
            test_dataset_description=request.test_dataset_description,
        )
        return _engine.assess_algorithmic_bias(bias_input)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/energy-footprint",
    summary="AI system energy and Scope 2 emissions calculation",
    response_model=Dict[str, Any],
)
def calculate_energy_footprint(request: EnergyFootprintRequest) -> Dict[str, Any]:
    """
    Calculate annual energy consumption and Scope 2 GHG emissions for an AI system.

    Training energy by parameter scale:
    - < 1B params: 0.5 MWh (one-time)
    - 1–10B params: 5 MWh
    - 10–100B params: 50 MWh
    - > 100B params: 500 MWh

    Inference energy = daily_queries × energy_per_query (Wh) × 365 / 1,000

    Annual Scope 2 tCO2e = (training + inference MWh) × grid carbon factor.
    Benchmarked against EU average grid (475 gCO2/kWh).
    """
    try:
        sys_input = AISystemInput(
            system_id=request.system_id,
            system_name=request.system_name,
            parameter_scale=request.parameter_scale,
            daily_queries=request.daily_queries,
            deployment_grid_carbon_gco2_kwh=request.deployment_grid_carbon_gco2_kwh,
            training_complete=request.training_complete,
            deployment_region=request.deployment_region,
        )
        return _engine.calculate_ai_energy(sys_input)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/model-card",
    summary="Model card completeness assessment (12-field standard)",
    response_model=Dict[str, Any],
)
def score_model_card(request: ModelCardRequest) -> Dict[str, Any]:
    """
    Assess completeness of an AI model card against the 12-field
    NIST AI RMF / Google Model Card standard (Mitchell et al. 2019).

    Required fields:
    model_details, intended_use, factors, metrics, evaluation_data,
    training_data, quantitative_analysis, ethical_considerations,
    caveats_recommendations, out_of_scope_uses, technical_specifications,
    environmental_impact.

    Returns completeness % (0-100), missing fields, blocking gaps
    (required for EU AI Act Art 11 technical documentation), and
    EU AI Act Art 11 readiness flag.
    """
    try:
        sys_input = AISystemInput(
            system_id=request.system_id,
            system_name=request.system_name,
            model_card_fields=request.model_card_fields,
        )
        return _engine.score_model_card(sys_input)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/portfolio",
    summary="Portfolio-level AI governance ESG assessment",
    response_model=Dict[str, Any],
)
def aggregate_ai_portfolio(request: AIPortfolioRequest) -> Dict[str, Any]:
    """
    Portfolio-level AI governance and ESG assessment.

    Aggregates individual AI system assessments to produce:
    - Portfolio average ESG composite score and tier
    - Total annual Scope 2 tCO2e across all AI systems
    - EU AI Act risk tier distribution
    - High-risk systems requiring compliance programme
    - Portfolio-level bias flags
    - Organisational recommendations

    Each system in the `systems` list accepts the same fields as the
    /assess endpoint. Unscored fields default to 0.
    """
    try:
        portfolio_input = AIPortfolioInput(
            portfolio_id=request.portfolio_id,
            systems=request.systems,
            organisation_name=request.organisation_name,
            reporting_period=request.reporting_period,
            organisation_sector=request.organisation_sector,
        )
        return _engine.aggregate_ai_portfolio(portfolio_input)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/eu-ai-act-tiers",
    summary="Reference: EU AI Act risk tier definitions",
    response_model=Dict[str, Any],
)
def get_eu_ai_act_tiers() -> Dict[str, Any]:
    """
    Return EU AI Act 2024/1689 risk tier definitions and all 12 high-risk
    AI system categories (Annex III + Art 5 prohibited practices).

    Includes applicable articles, examples, prohibited subsets, and
    additional obligations per category. Also returns timeline of key
    application dates (Art 5: Feb 2025; GPAI: Aug 2025; High-risk: Aug 2026).
    """
    return {
        "regulation": "EU AI Act (EU) 2024/1689",
        "risk_tiers": {
            "unacceptable": {
                "label": "Unacceptable Risk (Prohibited)",
                "article": "Art 5",
                "description": "AI practices that pose unacceptable risk to fundamental rights.",
                "examples": [
                    "Social scoring by governments (Art 5(1)(c))",
                    "Subliminal manipulation (Art 5(1)(a))",
                    "Exploitation of vulnerable groups (Art 5(1)(b))",
                    "Real-time remote biometric ID in public spaces (Art 5(1)(d), with exceptions)",
                    "Facial recognition database scraping (Art 5(1)(e))",
                    "Emotion recognition in workplace/education (Art 5(1)(f))",
                    "Predictive policing based solely on profiling (Art 5(1)(g))",
                    "Biometric categorisation by sensitive attributes (Art 5(1)(h))",
                ],
                "application_date": "2025-02-02",
            },
            "high_risk": {
                "label": "High Risk",
                "articles": ["Art 6", "Art 9", "Art 10", "Art 11", "Art 13", "Art 14", "Art 15", "Art 17"],
                "description": "AI systems listed in Annex III or as safety components (Art 6).",
                "mandatory_requirements": [
                    "Risk management system (Art 9)",
                    "Data governance (Art 10)",
                    "Technical documentation (Art 11)",
                    "Logging / record-keeping (Art 12)",
                    "Transparency to users (Art 13)",
                    "Human oversight measures (Art 14)",
                    "Accuracy, robustness, cybersecurity (Art 15)",
                    "Quality management (Art 17)",
                    "Conformity assessment (Art 43)",
                    "EU database registration (Art 49)",
                ],
                "application_date": "2026-08-02",
            },
            "limited_risk": {
                "label": "Limited Risk",
                "article": "Art 50",
                "description": "AI systems with specific transparency obligations (chatbots, deepfakes).",
                "requirements": [
                    "Disclose AI interaction to users (Art 50(a))",
                    "Label AI-generated content (Art 50(c))",
                    "Emotion recognition disclosure (Art 50(d))",
                ],
                "application_date": "2026-08-02",
            },
            "minimal_risk": {
                "label": "Minimal Risk",
                "description": "All other AI systems — no mandatory obligations under EU AI Act.",
                "examples": ["AI spam filters", "AI video games", "AI inventory management"],
                "voluntary": "Commission to encourage voluntary codes of conduct (Art 95)",
            },
        },
        "high_risk_categories": EU_AI_ACT_HIGH_RISK_CATEGORIES,
        "gpai_thresholds": {
            "systemic_risk_threshold_flops": "10^25 FLOPs (Art 51)",
            "additional_obligations": "Art 53-55",
        },
        "key_dates": {
            "prohibited_practices": "2025-02-02",
            "gpai_rules": "2025-08-02",
            "high_risk_systems": "2026-08-02",
            "full_application": "2027-08-02",
        },
    }


@router.get(
    "/ref/nist-rmf-functions",
    summary="Reference: NIST AI RMF 1.0 functions and categories",
    response_model=Dict[str, Any],
)
def get_nist_rmf_functions() -> Dict[str, Any]:
    """
    Return NIST AI RMF 1.0 (January 2023) complete structure.

    Covers 4 core functions (Govern/Map/Measure/Manage) and all 19
    sub-categories with descriptions, weights, and scoring guidance.
    Scoring: 1 = fully met, 0.5 = partially met, 0 = not met.
    """
    return {
        "framework": "NIST AI RMF 1.0",
        "published": "January 2023",
        "publisher": "National Institute of Standards and Technology (NIST)",
        "url": "https://airc.nist.gov/RMF",
        "functions": NIST_RMF_CATEGORIES,
        "scoring_guidance": {
            "1.0": "Fully met — documented evidence and implementation in place",
            "0.5": "Partially met — some evidence or implementation but gaps remain",
            "0.0": "Not met — no evidence of implementation",
        },
        "maturity_tiers": {
            "optimising": "Score ≥ 80 — continuously improving AI risk management",
            "managed": "Score 60–79 — formal AI risk management with metrics",
            "repeatable": "Score 40–59 — documented and repeatable AI risk processes",
            "partial": "Score 20–39 — ad hoc AI risk management",
            "initial": "Score < 20 — minimal AI risk management in place",
        },
        "cross_reference": {
            "EU_AI_Act": "NIST RMF Govern ↔ EU AI Act Art 9 (Risk Management), Art 17 (QMS)",
            "ISO_42001": "NIST RMF ↔ ISO/IEC 42001:2023 AI Management System",
            "OECD": "NIST RMF Map/Measure ↔ OECD AI Principle 4 (Robustness, Security)",
        },
    }


@router.get(
    "/ref/oecd-principles",
    summary="Reference: OECD AI Principles 2023",
    response_model=Dict[str, Any],
)
def get_oecd_principles() -> Dict[str, Any]:
    """
    Return OECD AI Principles 2023 structure with 5 principles and 12 sub-indicators.

    All 5 principles are equally weighted at 20%.
    Scoring guidance: 1.0 = fully met, 0.5 = partially met, 0.0 = not met.
    Adopted by G20 Leaders (2019), updated 2023.
    """
    return {
        "framework": "OECD AI Principles",
        "adopted": "2019 (updated 2023)",
        "publisher": "OECD",
        "url": "https://oecd.ai/en/ai-principles",
        "principles": _OECD_PRINCIPLES,
        "weighting": "Each of the 5 principles equally weighted at 20%",
        "scoring_guidance": {
            "1.0": "Fully implemented with documented evidence",
            "0.5": "Partially implemented — some gaps or limited documentation",
            "0.0": "Not implemented",
        },
        "cross_reference": {
            "EU_AI_Act": "OECD Principle 3 (Transparency) ↔ Art 13; Principle 5 (Accountability) ↔ Art 17",
            "NIST_RMF": "OECD Principle 4 (Robustness) ↔ NIST Measure MS-4; Principle 2 (Human-centred) ↔ NIST Govern GV-3",
            "IFRS_S1": "OECD Principle 1 (Inclusive growth) ↔ IFRS S1 Strategy/Risk Management pillars",
        },
        "g20_endorsed": True,
        "signatory_countries": 46,
    }


@router.get(
    "/ref/bias-metrics",
    summary="Reference: Algorithmic bias assessment methodology",
    response_model=Dict[str, Any],
)
def get_bias_metrics() -> Dict[str, Any]:
    """
    Return algorithmic bias assessment methodology reference.

    Covers 3 primary fairness metrics, 7 protected characteristics,
    severity thresholds, legal basis (EEOC 4/5 Rule, EU directives),
    and references to academic fairness literature.
    """
    return {
        "protected_characteristics": [
            {"id": "gender", "legal_basis": "EU Directive 2006/54/EC; ECHR Art 14"},
            {"id": "race_ethnicity", "legal_basis": "EU Directive 2000/43/EC; ECHR Protocol 12"},
            {"id": "age", "legal_basis": "EU Directive 2000/78/EC (Employment)"},
            {"id": "disability", "legal_basis": "EU Directive 2000/78/EC; UNCRPD"},
            {"id": "religion", "legal_basis": "EU Directive 2000/78/EC; ECHR Art 9"},
            {"id": "sexual_orientation", "legal_basis": "EU Directive 2000/78/EC"},
            {"id": "nationality", "legal_basis": "TFEU Art 18; ECHR Protocol 12"},
        ],
        "fairness_metrics": {
            "disparate_impact_ratio": {
                "formula": "P(Y=1 | group=minority) / P(Y=1 | group=majority)",
                "threshold_adverse": 0.80,
                "rule": "EEOC 4/5 (80%) Rule — Uniform Guidelines on Employee Selection Procedures (1978)",
                "severity": {
                    "critical": "DIR < 0.60",
                    "high": "0.60 ≤ DIR < 0.70",
                    "medium": "0.70 ≤ DIR < 0.80",
                    "low": "DIR ≥ 0.80",
                },
            },
            "statistical_parity_difference": {
                "formula": "P(Y=1 | group=1) - P(Y=1 | group=0)",
                "threshold_adverse": -0.10,
                "interpretation": "Negative values indicate minority group receives fewer positive outcomes",
            },
            "equalized_odds": {
                "description": "TPR and FPR are equal across groups",
                "formula": "|TPR_group1 - TPR_group0| < threshold AND |FPR_group1 - FPR_group0| < threshold",
                "threshold_adverse": 0.10,
            },
        },
        "eu_ai_act_requirements": {
            "article": "Art 9 (Risk Management) + Art 10 (Data Governance)",
            "obligation": (
                "High-risk AI systems must undergo bias testing pre-deployment "
                "and during post-market monitoring."
            ),
        },
        "references": [
            "Barocas, Hardt, Narayanan — Fairness and Machine Learning (2023)",
            "Mitchell et al. — Model Cards for Model Reporting (2019)",
            "Mehrabi et al. — A Survey on Bias and Fairness in Machine Learning (2021)",
            "EU FRA — Artificial Intelligence and Fundamental Rights (2020)",
        ],
        "tools": ["Fairlearn (Microsoft)", "AIF360 (IBM)", "What-If Tool (Google)", "Aequitas"],
    }
