"""
ai_risk_engine.py — E76 AI & ML Risk Finance
EU AI Act 2024/1689 | NIST AI RMF 1.0 | GDPR Art 22 | EU AI Liability Directive 2022
EU Product Liability Directive 2023/2853 | EU AI Office Enforcement Timeline 2024-2027
"""
from __future__ import annotations
import random
from datetime import datetime, timezone
from typing import Any

# ── Reference Data ─────────────────────────────────────────────────────────────

ANNEX3_HIGH_RISK_CATEGORIES = [
    {"id": "A3-01", "category": "Critical Infrastructure", "description": "Safety components of infrastructure (water, gas, electricity, transport)", "examples": ["SCADA safety systems", "traffic management", "grid balancing"]},
    {"id": "A3-02", "category": "Education & Vocational Training", "description": "Determining access or admission to educational institutions", "examples": ["exam scoring", "student assessment", "dropout prediction"]},
    {"id": "A3-03", "category": "Employment & Workers Management", "description": "Recruitment, promotion, dismissal, task allocation, performance monitoring", "examples": ["CV screening", "interview ranking", "productivity scoring"]},
    {"id": "A3-04", "category": "Essential Private/Public Services", "description": "Creditworthiness, life/health insurance, emergency services dispatch", "examples": ["credit scoring", "insurance risk", "emergency triage"]},
    {"id": "A3-05", "category": "Law Enforcement", "description": "Individual risk assessment, polygraphs, crime analytics, evidence evaluation", "examples": ["predictive policing", "facial recognition", "crime risk scoring"]},
    {"id": "A3-06", "category": "Migration & Asylum", "description": "Authenticity checks, application assessment, risk classification, border control", "examples": ["visa risk scoring", "travel document verification", "border surveillance"]},
    {"id": "A3-07", "category": "Administration of Justice", "description": "Research, interpretation, evidence analysis in judicial proceedings", "examples": ["legal document analysis", "sentencing tools", "case outcome prediction"]},
    {"id": "A3-08", "category": "Democratic Processes", "description": "Election and voting integrity, political campaigning micro-targeting", "examples": ["voter fraud detection", "ballot counting", "political profiling"]},
    {"id": "A3-09", "category": "Biometric Identification", "description": "Remote biometric identification and categorisation of natural persons", "examples": ["facial recognition", "gait analysis", "emotion recognition"]},
    {"id": "A3-10", "category": "Medical Devices (Safety Component)", "description": "AI safety components of medical devices per Directive 2017/745", "examples": ["diagnostic AI", "surgical robotics", "drug dosage systems"]},
    {"id": "A3-11", "category": "Vehicles (Safety Component)", "description": "Safety components of vehicles per Directives 2018/858 and 2019/2144", "examples": ["autonomous driving", "ADAS", "fatigue detection"]},
    {"id": "A3-12", "category": "Industrial Machinery (Safety)", "description": "Safety functions in machinery per Directive 2006/42/EC", "examples": ["collision avoidance", "pressure safety", "operator monitoring"]},
    {"id": "A3-13", "category": "Toys with AI (Safety)", "description": "AI components in toys posing safety risks to children", "examples": ["interactive AI toys", "children chat systems"]},
    {"id": "A3-14", "category": "Lifts & Pressure Equipment", "description": "AI safety components per Directives 2014/33/EU and 2014/68/EU", "examples": ["lift control systems", "pressure vessel monitoring"]},
    {"id": "A3-15", "category": "Personal Protective Equipment", "description": "AI in PPE per Regulation (EU) 2016/425", "examples": ["smart helmet sensors", "exoskeleton control"]},
    {"id": "A3-16", "category": "Radio Equipment", "description": "AI in radio equipment per Directive 2014/53/EU", "examples": ["smart radio systems", "interference detection"]},
    {"id": "A3-17", "category": "Marine Equipment", "description": "AI components per Directive 2014/90/EU", "examples": ["navigation AI", "collision avoidance maritime"]},
    {"id": "A3-18", "category": "Civil Aviation", "description": "AI components per Regulations (EU) 2018/1139", "examples": ["flight management AI", "ATC support systems"]},
    {"id": "A3-19", "category": "Agricultural Machinery", "description": "AI in agricultural equipment per Regulation (EU) 2016/1628", "examples": ["autonomous tractors", "spray drones"]},
    {"id": "A3-20", "category": "Two/Three-Wheel Vehicles", "description": "AI safety components per Regulation (EU) 168/2013", "examples": ["e-bike control systems", "motorcycle stability AI"]},
    {"id": "A3-21", "category": "Explosives", "description": "AI in civilian explosives per Directive 2014/28/EU", "examples": ["detonation systems", "mining safety AI"]},
    {"id": "A3-22", "category": "Pyrotechnic Articles", "description": "AI components per Directive 2013/29/EU", "examples": ["fireworks ignition AI", "safety interlocks"]},
    {"id": "A3-23", "category": "Cableways & Ropeways", "description": "AI safety components per Regulation (EU) 2016/424", "examples": ["cable car control", "ski lift safety AI"]},
]

PROHIBITED_PRACTICES = [
    {"id": "PP-01", "practice": "Subliminal Manipulation", "article": "Art 5(1)(a)", "description": "AI techniques beyond a person's consciousness to distort behaviour causing harm", "example": "Subliminal advertising in recommendation systems"},
    {"id": "PP-02", "practice": "Vulnerability Exploitation", "article": "Art 5(1)(b)", "description": "Exploiting specific group vulnerabilities (age, disability) to distort behaviour", "example": "Targeting elderly with manipulative financial offers"},
    {"id": "PP-03", "practice": "Social Scoring by Public Authorities", "article": "Art 5(1)(c)", "description": "General purpose social scoring leading to detrimental treatment", "example": "Government citizen scoring for social benefits"},
    {"id": "PP-04", "practice": "Real-Time Remote Biometric ID (Public Spaces)", "article": "Art 5(1)(d)", "description": "Real-time remote biometric identification in publicly accessible spaces by law enforcement", "example": "Live facial recognition at public events"},
    {"id": "PP-05", "practice": "Retrospective Remote Biometric ID", "article": "Art 5(1)(e)", "description": "Retrospective biometric identification except for targeted criminal investigations", "example": "Mass retrospective facial recognition in CCTV"},
    {"id": "PP-06", "practice": "Emotion Recognition (Workplace/Education)", "article": "Art 5(1)(f)", "description": "Emotion recognition in workplace or educational institutions", "example": "Employee mood tracking for performance assessment"},
    {"id": "PP-07", "practice": "Biometric Categorisation (Protected Characteristics)", "article": "Art 5(1)(g)", "description": "Biometric categorisation inferring race, political opinions, religion, sexual orientation", "example": "Camera systems inferring religion from appearance"},
    {"id": "PP-08", "practice": "AI for Criminal Offence Prediction (Individual)", "article": "Art 5(1)(h)", "description": "Predictive policing based solely on profiling or personality traits", "example": "Predictive crime scoring based on social media without prior offence"},
]

NIST_RMF_FUNCTIONS = {
    "GOVERN": {
        "description": "Establish AI risk governance culture and oversight",
        "subcategories": [
            "GOV-1.1", "GOV-1.2", "GOV-1.3", "GOV-1.4", "GOV-1.5", "GOV-1.6", "GOV-1.7",
            "GOV-2.1", "GOV-2.2",
            "GOV-3.1", "GOV-3.2",
            "GOV-4.1", "GOV-4.2",
            "GOV-5.1", "GOV-5.2",
            "GOV-6.1", "GOV-6.2",
        ],
    },
    "MAP": {
        "description": "Identify and categorise AI risks in context",
        "subcategories": [
            "MAP-1.1", "MAP-1.2", "MAP-1.3", "MAP-1.4", "MAP-1.5", "MAP-1.6",
            "MAP-2.1", "MAP-2.2", "MAP-2.3",
            "MAP-3.1", "MAP-3.2", "MAP-3.3", "MAP-3.4", "MAP-3.5",
            "MAP-4.1", "MAP-4.2",
            "MAP-5.1", "MAP-5.2",
        ],
    },
    "MEASURE": {
        "description": "Analyse and assess AI risks with measurement tools",
        "subcategories": [
            "MEA-1.1", "MEA-1.2", "MEA-1.3",
            "MEA-2.1", "MEA-2.2", "MEA-2.3", "MEA-2.4", "MEA-2.5", "MEA-2.6", "MEA-2.7", "MEA-2.8",
            "MEA-3.1", "MEA-3.2", "MEA-3.3",
            "MEA-4.1", "MEA-4.2",
        ],
    },
    "MANAGE": {
        "description": "Prioritise and address AI risks throughout lifecycle",
        "subcategories": [
            "MNG-1.1", "MNG-1.2", "MNG-1.3", "MNG-1.4",
            "MNG-2.1", "MNG-2.2", "MNG-2.3", "MNG-2.4",
            "MNG-3.1", "MNG-3.2",
            "MNG-4.1", "MNG-4.2",
        ],
    },
}

BIAS_METRICS = [
    {"metric": "demographic_parity", "description": "P(Y_hat=1|A=0) = P(Y_hat=1|A=1)", "threshold": 0.1, "gdpr_relevant": True},
    {"metric": "equalised_odds", "description": "Equal TPR and FPR across protected groups", "threshold": 0.1, "gdpr_relevant": True},
    {"metric": "calibration", "description": "Predicted probability matches observed outcome rate by group", "threshold": 0.05, "gdpr_relevant": False},
    {"metric": "counterfactual_fairness", "description": "Prediction unchanged in counterfactual world where protected attribute differs", "threshold": 0.15, "gdpr_relevant": True},
    {"metric": "individual_fairness", "description": "Similar individuals receive similar predictions (Lipschitz condition)", "threshold": 0.2, "gdpr_relevant": True},
    {"metric": "statistical_parity_difference", "description": "Absolute difference in positive outcome rates between groups", "threshold": 0.1, "gdpr_relevant": True},
]

SECTOR_AI_RISK_PROFILES = {
    "banking": {"baseline_risk": "high_risk", "primary_categories": ["A3-04", "A3-05"], "regulatory_overlap": ["CRR", "EBA_ML_Guidelines", "GDPR"]},
    "insurance": {"baseline_risk": "high_risk", "primary_categories": ["A3-04"], "regulatory_overlap": ["Solvency_II", "IDD", "GDPR"]},
    "healthcare": {"baseline_risk": "high_risk", "primary_categories": ["A3-10"], "regulatory_overlap": ["MDR_2017/745", "GDPR", "AI_Act"]},
    "automotive": {"baseline_risk": "high_risk", "primary_categories": ["A3-11"], "regulatory_overlap": ["UNECE_WP29", "Type_Approval"]},
    "recruitment": {"baseline_risk": "high_risk", "primary_categories": ["A3-03"], "regulatory_overlap": ["GDPR", "Equal_Treatment_Directive"]},
    "education": {"baseline_risk": "high_risk", "primary_categories": ["A3-02"], "regulatory_overlap": ["GDPR", "FERPA_equivalent"]},
    "ecommerce": {"baseline_risk": "limited_risk", "primary_categories": [], "regulatory_overlap": ["GDPR", "DSA"]},
    "manufacturing": {"baseline_risk": "minimal_risk", "primary_categories": ["A3-12"], "regulatory_overlap": ["Machinery_Directive"]},
    "agriculture": {"baseline_risk": "minimal_risk", "primary_categories": ["A3-19"], "regulatory_overlap": []},
    "energy": {"baseline_risk": "limited_risk", "primary_categories": ["A3-01"], "regulatory_overlap": ["NIS2", "CER_Directive"]},
    "logistics": {"baseline_risk": "limited_risk", "primary_categories": [], "regulatory_overlap": ["GDPR"]},
    "public_sector": {"baseline_risk": "high_risk", "primary_categories": ["A3-03", "A3-05", "A3-06"], "regulatory_overlap": ["GDPR", "AI_Act", "DSA"]},
}

ENFORCEMENT_TIMELINE = [
    {"date": "2024-08-01", "milestone": "AI Act entry into force", "detail": "Regulation (EU) 2024/1689 published in OJ; 24-month general application countdown begins"},
    {"date": "2025-02-02", "milestone": "Prohibited practices apply", "detail": "6-month phase: Art 5 prohibitions on subliminal manipulation, social scoring, real-time biometric ID enforceable"},
    {"date": "2025-08-02", "milestone": "GPAI obligations apply", "detail": "12-month phase: General Purpose AI model obligations (Art 51-56), EU AI Office supervision begins"},
    {"date": "2026-08-02", "milestone": "Full application", "detail": "24-month phase: All provisions apply including high-risk system requirements (Art 6-51), notified bodies operational"},
    {"date": "2027-08-02", "milestone": "Annex I embedded systems", "detail": "36-month phase: High-risk AI embedded in products under existing harmonisation legislation (Annex I) fully apply"},
    {"date": "2025-05-01", "milestone": "EU AI Office established", "detail": "EU AI Office under European Commission operational; GPAI model oversight, codes of practice"},
    {"date": "2025-01-01", "milestone": "AI Liability Directive application", "detail": "Proposed AI Liability Directive (COM/2022/496) — disclosure/presumption of causality for AI-caused damage"},
    {"date": "2024-12-09", "milestone": "Product Liability Directive", "detail": "Directive 2023/2853 applies — AI software treated as 'product'; strict liability for defective AI"},
]


# ── Core Engine Functions ──────────────────────────────────────────────────────

def classify_ai_system(
    entity_id: str,
    system_name: str,
    use_case: str,
    sector: str,
    automated_decision_making: bool,
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)
    sector_lower = sector.lower()
    profile = SECTOR_AI_RISK_PROFILES.get(sector_lower, SECTOR_AI_RISK_PROFILES["ecommerce"])

    # Check prohibited practices
    prohibited_flags: list[dict] = []
    use_case_lower = use_case.lower()
    if any(kw in use_case_lower for kw in ["social scoring", "social credit", "citizen score"]):
        prohibited_flags.append(PROHIBITED_PRACTICES[2])
    if any(kw in use_case_lower for kw in ["biometric", "facial recognition", "face recognition"]):
        prohibited_flags.append(PROHIBITED_PRACTICES[3])
    if any(kw in use_case_lower for kw in ["emotion", "mood detection", "affective computing"]):
        prohibited_flags.append(PROHIBITED_PRACTICES[5])
    if any(kw in use_case_lower for kw in ["subliminal", "manipulat"]):
        prohibited_flags.append(PROHIBITED_PRACTICES[0])

    # Determine risk category
    if prohibited_flags:
        risk_category = "prohibited"
    elif profile["baseline_risk"] == "high_risk" or any(
        kw in use_case_lower for kw in ["credit", "hiring", "recruiting", "medical diagnosis", "safety critical", "border control", "law enforcement"]
    ):
        risk_category = "high_risk"
    elif any(kw in use_case_lower for kw in ["chatbot", "recommendation", "spam filter", "search"]):
        risk_category = "limited_risk"
    else:
        risk_category = "minimal_risk"

    # GPAI flag: systems trained with >10^25 FLOPS
    gpai_flag = any(kw in use_case_lower for kw in ["foundation model", "large language", "gpt", "llm", "generative ai", "diffusion"])
    gpai_systemic_risk = gpai_flag and rng.random() > 0.5

    # Applicable Annex III categories
    applicable_annex3 = [c for c in ANNEX3_HIGH_RISK_CATEGORIES if c["id"] in profile["primary_categories"]]

    # High-risk requirements (if high_risk)
    high_risk_requirements: dict[str, Any] = {}
    if risk_category == "high_risk":
        high_risk_requirements = {
            "conformity_assessment_required": True,
            "technical_documentation": True,
            "eu_declaration_of_conformity": True,
            "ce_marking_required": True,
            "post_market_monitoring": True,
            "serious_incident_reporting": True,
            "quality_management_system": True,
            "risk_management_system": True,
            "data_governance": True,
            "transparency_obligations": True,
            "human_oversight_measures": True,
            "accuracy_robustness_cybersecurity": True,
            "notified_body_required": rng.random() > 0.4,
            "fundamental_rights_impact_assessment": automated_decision_making,
        }

    # Limited risk transparency obligations
    transparency_obligations: list[str] = []
    if risk_category == "limited_risk":
        transparency_obligations = ["disclose_ai_interaction", "inform_synthetic_content", "label_deepfakes"]
    elif risk_category == "high_risk":
        transparency_obligations = [
            "provide_instructions_for_use", "disclose_high_risk_classification",
            "enable_human_oversight", "log_decisions_automatically",
            "fundamental_rights_impact_assessment" if automated_decision_making else "standard_impact_assessment",
        ]

    # GDPR Art 22 applicability
    gdpr_art22_applicable = automated_decision_making and risk_category in ("high_right", "high_risk", "limited_risk")

    # Penalty exposure
    max_penalty_pct_global_turnover = {
        "prohibited": 7.0,
        "high_risk": 3.0,
        "limited_risk": 1.5,
        "minimal_risk": 0.0,
    }[risk_category]
    estimated_global_turnover_usd = rng.uniform(50e6, 5e9)
    max_penalty_usd = estimated_global_turnover_usd * max_penalty_pct_global_turnover / 100

    return {
        "entity_id": entity_id,
        "system_name": system_name,
        "use_case": use_case,
        "sector": sector,
        "automated_decision_making": automated_decision_making,
        "ai_act_risk_category": risk_category,
        "prohibited_practice_flags": prohibited_flags,
        "high_risk_requirements": high_risk_requirements,
        "transparency_obligations": transparency_obligations,
        "applicable_annex3_categories": applicable_annex3,
        "gpai_model_flag": gpai_flag,
        "gpai_systemic_risk_flag": gpai_systemic_risk,
        "ce_marking_required": risk_category == "high_risk",
        "gdpr_art22_applicable": gdpr_art22_applicable,
        "regulatory_overlap": profile["regulatory_overlap"],
        "max_penalty_pct_global_turnover": max_penalty_pct_global_turnover,
        "max_penalty_usd": round(max_penalty_usd, 0),
        "enforcement_timeline": ENFORCEMENT_TIMELINE,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def assess_nist_rmf(
    entity_id: str,
    system_name: str,
    functions: list[str],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    function_scores: dict[str, Any] = {}
    all_subcategory_scores: dict[str, float] = {}
    total_score = 0.0
    total_count = 0

    for func_name, func_data in NIST_RMF_FUNCTIONS.items():
        implemented = func_name in [f.upper() for f in functions] or rng.random() > 0.3
        subcategory_scores: dict[str, float] = {}
        for subcat in func_data["subcategories"]:
            base = rng.uniform(0.4, 1.0) if implemented else rng.uniform(0.1, 0.5)
            score = round(base, 3)
            subcategory_scores[subcat] = score
            all_subcategory_scores[subcat] = score
            total_score += score
            total_count += 1

        func_avg = sum(subcategory_scores.values()) / len(subcategory_scores)
        function_scores[func_name] = {
            "description": func_data["description"],
            "implemented": implemented,
            "average_score": round(func_avg, 3),
            "subcategory_scores": subcategory_scores,
        }

    overall_score = total_score / total_count if total_count else 0

    # Determine risk tier
    if overall_score >= 0.8:
        risk_tier = "low"
    elif overall_score >= 0.6:
        risk_tier = "medium"
    elif overall_score >= 0.4:
        risk_tier = "high"
    else:
        risk_tier = "critical"

    # Gap analysis — identify lowest scoring subcategories
    sorted_gaps = sorted(all_subcategory_scores.items(), key=lambda x: x[1])
    top_gaps = sorted_gaps[:10]

    recommended_actions = []
    for subcat, score in top_gaps:
        func_key = subcat.split("-")[0].upper()
        func_key_map = {"GOV": "GOVERN", "MAP": "MAP", "MEA": "MEASURE", "MNG": "MANAGE"}
        func_name = func_key_map.get(func_key, func_key)
        recommended_actions.append({
            "subcategory": subcat,
            "current_score": score,
            "target_score": min(score + 0.3, 1.0),
            "function": func_name,
            "action": f"Improve {func_name} practice {subcat}: implement documented controls, evidence collection, and periodic review cycles",
            "priority": "high" if score < 0.4 else "medium",
        })

    maturity_levels = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }

    return {
        "entity_id": entity_id,
        "system_name": system_name,
        "nist_rmf_version": "1.0",
        "overall_score": round(overall_score, 3),
        "risk_tier": risk_tier,
        "maturity_level": maturity_levels[risk_tier],
        "function_scores": function_scores,
        "total_subcategories_assessed": total_count,
        "gap_analysis": {"top_10_gaps": [{"subcategory": s, "score": sc} for s, sc in top_gaps]},
        "recommended_actions": recommended_actions,
        "certification_readiness": {
            "iso_42001_gap_pct": round((1 - overall_score) * 100, 1),
            "nist_ai_rmf_conformance_pct": round(overall_score * 100, 1),
        },
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def detect_algorithmic_bias(
    entity_id: str,
    model_type: str,
    protected_attributes: list[str],
    performance_metrics: dict[str, float],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    bias_results: list[dict] = []
    overall_bias_score = 0.0

    for attr in protected_attributes:
        attr_seed = rng.random()
        attr_rng = random.Random(hash(f"{entity_id}_{attr}") & 0xFFFFFFFF)

        metric_results: list[dict] = []
        attr_bias_sum = 0.0

        for bm in BIAS_METRICS:
            metric = bm["metric"]
            threshold = bm["threshold"]
            # Simulate metric value
            raw_value = attr_rng.uniform(0.0, 0.35)
            violation = raw_value > threshold
            severity = "critical" if raw_value > threshold * 3 else "high" if raw_value > threshold * 2 else "medium" if violation else "low"
            attr_bias_sum += raw_value

            mitigation = []
            if violation:
                if "parity" in metric:
                    mitigation = ["Resampling (SMOTE/undersampling)", "Reweighing training data", "Threshold adjustment by group"]
                elif "odds" in metric:
                    mitigation = ["Post-processing equalised odds correction (Hardt et al. 2016)", "In-processing adversarial debiasing"]
                elif "calibration" in metric:
                    mitigation = ["Platt scaling by subgroup", "isotonic regression calibration"]
                elif "counterfactual" in metric:
                    mitigation = ["Counterfactual data augmentation", "Causal model constraints"]
                else:
                    mitigation = ["Individual fairness regularisation", "Metric-aware training objective"]

            metric_results.append({
                "metric": metric,
                "description": bm["description"],
                "value": round(raw_value, 4),
                "threshold": threshold,
                "violation": violation,
                "severity": severity,
                "gdpr_art22_relevant": bm["gdpr_relevant"],
                "mitigation_recommendations": mitigation,
            })

        attr_avg_bias = attr_bias_sum / len(BIAS_METRICS)
        overall_bias_score += attr_avg_bias
        bias_results.append({
            "protected_attribute": attr,
            "attribute_bias_score": round(attr_avg_bias, 4),
            "metrics": metric_results,
        })

    overall_bias_score = overall_bias_score / len(protected_attributes) if protected_attributes else 0
    disparate_impact_ratio = round(rng.uniform(0.6, 1.0), 3)
    intersectionality_score = round(rng.uniform(0.0, 0.4), 4) if len(protected_attributes) > 1 else 0.0

    gdpr_art22_flag = any(
        m["gdpr_art22_relevant"] and m["violation"]
        for group in bias_results
        for m in group["metrics"]
    )

    return {
        "entity_id": entity_id,
        "model_type": model_type,
        "protected_attributes": protected_attributes,
        "overall_bias_score": round(overall_bias_score, 4),
        "disparate_impact_ratio": disparate_impact_ratio,
        "intersectionality_score": intersectionality_score,
        "gdpr_article22_profiling_flag": gdpr_art22_flag,
        "bias_results_by_attribute": bias_results,
        "bias_metrics_used": [bm["metric"] for bm in BIAS_METRICS],
        "total_violations": sum(
            1 for group in bias_results for m in group["metrics"] if m["violation"]
        ),
        "regulatory_exposure": {
            "gdpr_art22_automated_decision": gdpr_art22_flag,
            "eu_ai_act_fundamental_rights": overall_bias_score > 0.15,
            "eu_equality_directive": disparate_impact_ratio < 0.8,
            "max_fine_gdpr_eur": 20_000_000 if gdpr_art22_flag else 0,
        },
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def score_explainability(
    entity_id: str,
    model_type: str,
    explanation_methods: list[str],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    method_lower = [m.lower() for m in explanation_methods]
    available_methods: dict[str, bool] = {
        "shap": any("shap" in m for m in method_lower),
        "lime": any("lime" in m for m in method_lower),
        "attention": any("attention" in m for m in method_lower),
        "gradient": any("gradient" in m or "gradcam" in m or "saliency" in m for m in method_lower),
        "counterfactual": any("counterfactual" in m or "cf" in m for m in method_lower),
        "prototype": any("prototype" in m or "example" in m for m in method_lower),
        "rule_extraction": any("rule" in m or "tree" in m for m in method_lower),
    }

    method_count = sum(available_methods.values())
    method_coverage_score = min(method_count / 4, 1.0)

    # Annex XII transparency requirements (EU AI Act)
    annex12_requirements = {
        "technical_transparency_doc": True,
        "instructions_for_use": rng.random() > 0.2,
        "intended_purpose_documented": rng.random() > 0.15,
        "performance_metrics_disclosed": rng.random() > 0.25,
        "training_data_described": rng.random() > 0.3,
        "limitations_and_risks": rng.random() > 0.2,
        "human_oversight_measures": rng.random() > 0.25,
        "technical_accuracy_metrics": rng.random() > 0.2,
    }
    annex12_score = sum(annex12_requirements.values()) / len(annex12_requirements)

    # GDPR Recital 71 — right to explanation
    gdpr_rec71_compliance = {
        "meaningful_information_provided": available_methods.get("shap") or available_methods.get("lime"),
        "logic_of_processing_explained": method_count >= 2,
        "significance_and_consequences_explained": rng.random() > 0.3,
        "right_to_contest_supported": rng.random() > 0.4,
        "human_review_available": rng.random() > 0.3,
    }
    gdpr_rec71_score = sum(gdpr_rec71_compliance.values()) / len(gdpr_rec71_compliance)

    # XAI maturity level (1-5)
    combined_score = (method_coverage_score * 0.4 + annex12_score * 0.35 + gdpr_rec71_score * 0.25)
    if combined_score >= 0.85:
        xai_maturity = 5
        maturity_label = "Optimised"
    elif combined_score >= 0.7:
        xai_maturity = 4
        maturity_label = "Quantitatively Managed"
    elif combined_score >= 0.55:
        xai_maturity = 3
        maturity_label = "Defined"
    elif combined_score >= 0.35:
        xai_maturity = 2
        maturity_label = "Developing"
    else:
        xai_maturity = 1
        maturity_label = "Initial"

    intrinsic_interpretability = model_type.lower() in ["decision_tree", "linear_regression", "logistic_regression", "rule_based", "scorecard"]

    return {
        "entity_id": entity_id,
        "model_type": model_type,
        "explanation_methods_provided": explanation_methods,
        "available_xai_methods": available_methods,
        "method_coverage_score": round(method_coverage_score, 3),
        "overall_explainability_score": round(combined_score, 3),
        "xai_maturity_level": xai_maturity,
        "xai_maturity_label": maturity_label,
        "intrinsic_interpretability": intrinsic_interpretability,
        "annex12_transparency": {
            "requirements": annex12_requirements,
            "compliance_score": round(annex12_score, 3),
        },
        "gdpr_recital71": {
            "compliance_items": gdpr_rec71_compliance,
            "compliance_score": round(gdpr_rec71_score, 3),
            "right_to_explanation_met": gdpr_rec71_score >= 0.6,
        },
        "recommendations": [
            f"Implement SHAP explanations for feature attribution" if not available_methods["shap"] else None,
            f"Add counterfactual explanations for actionable recourse" if not available_methods["counterfactual"] else None,
            f"Document training data sources per Annex XII" if not annex12_requirements["training_data_described"] else None,
            f"Establish human review process for automated decisions (GDPR Rec 71)" if not gdpr_rec71_compliance["human_review_available"] else None,
        ],
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def calculate_ai_liability(
    entity_id: str,
    system_type: str,
    harm_scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    rng = random.Random(hash(str(entity_id)) & 0xFFFFFFFF)

    # Liability frameworks
    frameworks = {
        "eu_ai_liability_directive_2022": {
            "type": "fault_based",
            "presumption_of_causality": True,
            "disclosure_obligation": True,
            "burden_of_proof_reversal": True,
            "limitation_period_years": 5,
            "applicable_to": ["high_risk_ai", "gpai_models"],
        },
        "product_liability_directive_2023_2853": {
            "type": "strict_liability",
            "ai_software_as_product": True,
            "defect_types": ["design_defect", "manufacturing_defect", "failure_to_warn"],
            "damage_categories": ["physical", "property", "psychological", "fundamental_rights", "data_loss"],
            "limitation_period_years": 10,
            "longstop_period_years": 25,
        },
    }

    # Damage assessment by scenario
    total_liability_usd = 0.0
    scenario_assessments: list[dict] = []

    damage_category_rates = {
        "physical": rng.uniform(0.3, 0.8),
        "property": rng.uniform(0.2, 0.6),
        "psychological": rng.uniform(0.1, 0.4),
        "fundamental_rights": rng.uniform(0.15, 0.5),
        "data_loss": rng.uniform(0.1, 0.3),
    }

    for scenario in harm_scenarios:
        scenario_rng = random.Random(hash(f"{entity_id}_{scenario.get('name', '')}") & 0xFFFFFFFF)
        probability = scenario.get("probability", scenario_rng.uniform(0.05, 0.4))
        harm_magnitude_usd = scenario.get("harm_magnitude_usd", scenario_rng.uniform(100_000, 10_000_000))
        harm_type = scenario.get("harm_type", "physical")

        rate = damage_category_rates.get(harm_type, 0.3)
        expected_loss = probability * harm_magnitude_usd * rate
        strict_liability_exposure = harm_magnitude_usd * rate  # no fault needed
        total_liability_usd += expected_loss

        scenario_assessments.append({
            "scenario": scenario.get("name", f"Scenario_{len(scenario_assessments)+1}"),
            "harm_type": harm_type,
            "probability": probability,
            "harm_magnitude_usd": harm_magnitude_usd,
            "expected_loss_usd": round(expected_loss, 0),
            "strict_liability_exposure_usd": round(strict_liability_exposure, 0),
            "fault_based_likely": harm_type in ["fundamental_rights", "psychological"],
            "strict_liable_under_pld": harm_type in ["physical", "property", "data_loss"],
        })

    # Insurance gap
    standard_coverage_usd = rng.uniform(1e6, 20e6)
    coverage_gap_usd = max(0, total_liability_usd - standard_coverage_usd)

    # D&O exposure
    do_exposure = {
        "personal_liability_directors": rng.random() > 0.4,
        "ai_governance_failure_exposure": True,
        "estimated_do_claim_usd": round(rng.uniform(500_000, 5_000_000), 0),
        "coverage_adequate": rng.random() > 0.5,
        "recommended_ai_riders": ["AI liability extension", "Cyber-AI combined rider", "Regulatory defence costs"],
    }

    return {
        "entity_id": entity_id,
        "system_type": system_type,
        "liability_frameworks": frameworks,
        "total_expected_liability_usd": round(total_liability_usd, 0),
        "scenario_assessments": scenario_assessments,
        "insurance": {
            "standard_policy_coverage_usd": round(standard_coverage_usd, 0),
            "coverage_gap_usd": round(coverage_gap_usd, 0),
            "gap_exists": coverage_gap_usd > 0,
            "recommended_additional_coverage_usd": round(coverage_gap_usd * 1.2, 0),
        },
        "do_exposure": do_exposure,
        "mitigation_actions": [
            "Implement AI governance committee with board-level AI risk reporting",
            "Conduct fundamental rights impact assessments pre-deployment",
            "Maintain comprehensive AI system logs for causality evidence",
            "Purchase AI-specific professional indemnity and product liability extensions",
            "Establish clear human oversight protocols and override mechanisms",
        ],
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }
