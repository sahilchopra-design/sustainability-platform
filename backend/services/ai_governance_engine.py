"""
E77 — AI Governance & ESG Engine
=================================
Covers:
  - EU AI Act 2024/1689 — 4 risk tiers, 12 high-risk categories, Art 5/6/9/13/17/41
  - NIST AI RMF 1.0 (2023) — Govern/Map/Measure/Manage functions, 19 sub-categories
  - OECD AI Principles 2023 — 5 principles, weighted scoring
  - AI Energy Consumption — training + inference Scope 2 emissions
  - Algorithmic Bias Assessment — 7 protected characteristics, disparate impact
  - Model Card Completeness — 12 required fields (NIST/Google standard)
  - AI ESG Composite Score — Governance 35% / Environmental 30% / Social 35%
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Module-level reference data
# ---------------------------------------------------------------------------

# EU AI Act 2024/1689 — high-risk AI system categories (Annex III + Art 6)
EU_AI_ACT_HIGH_RISK_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "biometric_identification": {
        "label": "Biometric Identification & Categorisation",
        "annex": "Annex III (1)",
        "articles": ["Art 6", "Art 9", "Art 13", "Art 17"],
        "examples": ["Real-time remote biometric ID", "Emotion recognition in workplace/education"],
        "prohibited_subset": ["Real-time remote biometric ID in public spaces (Art 5(1)(d))"],
        "additional_obligations": ["human_oversight", "accuracy_testing", "logging"],
    },
    "critical_infrastructure": {
        "label": "Critical Infrastructure Management",
        "annex": "Annex III (2)",
        "articles": ["Art 6", "Art 9", "Art 41"],
        "examples": ["AI in road/rail/water/energy networks", "Digital infrastructure AI"],
        "prohibited_subset": [],
        "additional_obligations": ["cybersecurity", "robustness", "incident_reporting"],
    },
    "education_vocational": {
        "label": "Education & Vocational Training",
        "annex": "Annex III (3)",
        "articles": ["Art 6", "Art 9", "Art 13"],
        "examples": ["Student assessment AI", "Admission decisions", "Proctoring systems"],
        "prohibited_subset": [],
        "additional_obligations": ["explainability", "human_review", "non_discrimination"],
    },
    "employment_hr": {
        "label": "Employment & HR Management",
        "annex": "Annex III (4)",
        "articles": ["Art 6", "Art 9", "Art 17"],
        "examples": ["CV screening", "Performance monitoring", "Promotion decisions"],
        "prohibited_subset": [],
        "additional_obligations": ["bias_testing", "human_oversight", "transparency_to_workers"],
    },
    "essential_services": {
        "label": "Essential Private & Public Services",
        "annex": "Annex III (5)",
        "articles": ["Art 6", "Art 9", "Art 13", "Art 17"],
        "examples": ["Credit scoring", "Insurance pricing", "Social benefits eligibility"],
        "prohibited_subset": [],
        "additional_obligations": ["explainability", "appeal_mechanism", "non_discrimination"],
    },
    "law_enforcement": {
        "label": "Law Enforcement",
        "annex": "Annex III (6)",
        "articles": ["Art 6", "Art 9", "Art 13", "Art 17", "Art 41"],
        "examples": ["Predictive policing", "Lie detection", "Crime analytics"],
        "prohibited_subset": ["Untargeted scraping for facial recognition databases (Art 5(1)(e))"],
        "additional_obligations": ["fundamental_rights_impact", "data_governance", "logging"],
    },
    "migration_asylum": {
        "label": "Migration, Asylum & Border Control",
        "annex": "Annex III (7)",
        "articles": ["Art 6", "Art 9", "Art 13"],
        "examples": ["Risk assessment of applicants", "Document authenticity AI", "Interview analysis"],
        "prohibited_subset": [],
        "additional_obligations": ["fundamental_rights_impact", "human_oversight"],
    },
    "justice_democracy": {
        "label": "Administration of Justice & Democratic Processes",
        "annex": "Annex III (8)",
        "articles": ["Art 6", "Art 9", "Art 13"],
        "examples": ["Legal case outcome prediction", "Court scheduling AI", "Judicial assistance"],
        "prohibited_subset": [],
        "additional_obligations": ["explainability", "human_review_mandatory"],
    },
    "safety_components": {
        "label": "Safety Components of Products (Annex I)",
        "annex": "Art 6(1) — product safety legislation",
        "articles": ["Art 6", "Art 9"],
        "examples": ["AI in medical devices (MDR/IVDR)", "AI in machinery", "AI in aviation"],
        "prohibited_subset": [],
        "additional_obligations": ["third_party_conformity_assessment", "CE_marking"],
    },
    "medical_devices": {
        "label": "Medical Devices & In Vitro Diagnostics",
        "annex": "Art 6(1) cross-ref MDR/IVDR",
        "articles": ["Art 6", "Art 9", "Art 41"],
        "examples": ["Diagnostic AI", "Surgical robots", "Drug interaction prediction"],
        "prohibited_subset": [],
        "additional_obligations": ["clinical_validation", "EMA_coordination", "post_market_surveillance"],
    },
    "general_purpose_ai_systemic": {
        "label": "General Purpose AI — Systemic Risk (GPAI)",
        "annex": "Art 51 — >10^25 FLOPs training",
        "articles": ["Art 51", "Art 53", "Art 55"],
        "examples": ["GPT-4 class models", "Gemini Ultra", "Claude Opus class"],
        "prohibited_subset": [],
        "additional_obligations": ["adversarial_testing", "incident_reporting", "cybersecurity"],
    },
    "social_scoring": {
        "label": "Social Scoring (Prohibited)",
        "annex": "Art 5 (Prohibited Practices)",
        "articles": ["Art 5(1)(c)"],
        "examples": ["Government social credit systems", "Private behaviour scoring affecting rights"],
        "prohibited_subset": ["ALL uses prohibited — Art 5(1)(c)"],
        "additional_obligations": [],
    },
}

# NIST AI RMF 1.0 (2023) — four core functions with categories
NIST_RMF_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "GOVERN": {
        "label": "Govern",
        "description": "Cultivate and implement AI risk management culture, policies, and accountability.",
        "weight": 0.25,
        "categories": {
            "GV-1": "AI risk management is integrated into enterprise risk management.",
            "GV-2": "Accountability structures for AI risk are defined.",
            "GV-3": "Organizational teams are committed to AI risk management.",
            "GV-4": "AI risk management frameworks are reviewed and updated.",
            "GV-5": "Processes for AI risk are in place for procured/deployed AI.",
            "GV-6": "AI risk management policies exist and are communicated.",
        },
    },
    "MAP": {
        "label": "Map",
        "description": "Context is established and understood; risks are identified.",
        "weight": 0.25,
        "categories": {
            "MP-1": "Context for AI deployment is documented (use case, stakeholders).",
            "MP-2": "Categorisation of AI risks (technical, operational, societal).",
            "MP-3": "AI lifecycle phases are identified and risks mapped per phase.",
            "MP-4": "Scientific and technical data inputs are inventoried.",
            "MP-5": "Impacts to individuals and society are enumerated.",
        },
    },
    "MEASURE": {
        "label": "Measure",
        "description": "AI risks are analysed, assessed, ranked, and tracked.",
        "weight": 0.25,
        "categories": {
            "MS-1": "AI risk metrics and KPIs are defined and tracked.",
            "MS-2": "AI system performance is evaluated against defined metrics.",
            "MS-3": "AI fairness and bias assessments are conducted.",
            "MS-4": "AI system robustness and adversarial testing is performed.",
        },
    },
    "MANAGE": {
        "label": "Manage",
        "description": "AI risks are prioritised, responded to, and monitored.",
        "weight": 0.25,
        "categories": {
            "MG-1": "Risks are prioritised based on likelihood and impact.",
            "MG-2": "Mitigation strategies are deployed and documented.",
            "MG-3": "Residual risks are monitored and escalated.",
            "MG-4": "AI incident response plan exists and is tested.",
        },
    },
}

# AI model energy profiles by parameter scale
# Sources: Patterson et al. 2021, Lottick et al. 2019, Samsi et al. 2023
MODEL_ENERGY_PROFILES: Dict[str, Dict[str, Any]] = {
    "sub_1b": {
        "label": "Sub-1B parameters",
        "param_range": "< 1 billion",
        "training_energy_mwh": 0.5,
        "inference_energy_per_query_wh": 0.0001,
        "examples": ["BERT-base (110M)", "DistilBERT", "Small classification models"],
        "source": "Patterson et al. 2021",
    },
    "1b_10b": {
        "label": "1B–10B parameters",
        "param_range": "1–10 billion",
        "training_energy_mwh": 5.0,
        "inference_energy_per_query_wh": 0.001,
        "examples": ["GPT-2 XL (1.5B)", "Llama 7B", "Mistral 7B"],
        "source": "Patterson et al. 2021; Samsi et al. 2023",
    },
    "10b_100b": {
        "label": "10B–100B parameters",
        "param_range": "10–100 billion",
        "training_energy_mwh": 50.0,
        "inference_energy_per_query_wh": 0.003,
        "examples": ["GPT-3 (175B ceiling of class)", "Llama 65B", "PaLM 62B"],
        "source": "Patterson et al. 2021; Google sustainability reports",
    },
    "over_100b": {
        "label": "Over-100B parameters",
        "param_range": "> 100 billion",
        "training_energy_mwh": 500.0,
        "inference_energy_per_query_wh": 0.010,
        "examples": ["GPT-4 (~1T MoE est.)", "Gemini Ultra", "Claude Opus class"],
        "source": "Estimates from published energy and carbon analyses",
    },
}

# OECD AI Principles 2023 — 5 principles with sub-indicators
_OECD_PRINCIPLES: Dict[str, Dict[str, Any]] = {
    "inclusive_growth": {
        "label": "Inclusive Growth, Sustainable Development & Well-being",
        "weight": 0.20,
        "sub_indicators": {
            "ig_1": "AI benefits are accessible to all groups, including marginalised communities.",
            "ig_2": "AI deployment considers long-term sustainability and environmental impact.",
        },
    },
    "human_centred": {
        "label": "Human-Centred Values & Fairness",
        "weight": 0.20,
        "sub_indicators": {
            "hc_1": "AI systems respect the rule of law, human rights and democratic values.",
            "hc_2": "AI systems embed diversity, non-discrimination and fairness.",
            "hc_3": "AI protects privacy and data of individuals.",
        },
    },
    "transparency": {
        "label": "Transparency & Explainability",
        "weight": 0.20,
        "sub_indicators": {
            "tp_1": "AI actors provide meaningful information about AI systems to stakeholders.",
            "tp_2": "AI systems provide explanations for decisions that affect individuals.",
            "tp_3": "AI systems are contestable and individuals can seek redress.",
        },
    },
    "robustness": {
        "label": "Robustness, Security & Safety",
        "weight": 0.20,
        "sub_indicators": {
            "rb_1": "AI systems are technically robust and secure against adversarial attacks.",
            "rb_2": "AI lifecycle includes regular testing, monitoring and incident response.",
        },
    },
    "accountability": {
        "label": "Accountability",
        "weight": 0.20,
        "sub_indicators": {
            "ac_1": "AI actors are accountable for proper functioning across lifecycle.",
            "ac_2": "Mechanisms exist for oversight, audit and redress of AI systems.",
        },
    },
}

# Model card required fields — NIST/Google model card standard (12 fields)
_MODEL_CARD_FIELDS: List[Dict[str, Any]] = [
    {"id": "model_details", "label": "Model Details", "blocking": True,
     "description": "Name, version, type, training date, licence, contact."},
    {"id": "intended_use", "label": "Intended Use", "blocking": True,
     "description": "Primary intended uses, out-of-scope uses, recommended users."},
    {"id": "factors", "label": "Relevant Factors", "blocking": False,
     "description": "Relevant factors (demographic, technical) that may affect performance."},
    {"id": "metrics", "label": "Evaluation Metrics", "blocking": True,
     "description": "Performance metrics used, selection rationale, decision thresholds."},
    {"id": "evaluation_data", "label": "Evaluation Data", "blocking": True,
     "description": "Datasets used for evaluation, pre-processing, dataset access."},
    {"id": "training_data", "label": "Training Data", "blocking": True,
     "description": "Datasets used in training (or reference if confidential)."},
    {"id": "quantitative_analysis", "label": "Quantitative Analysis", "blocking": False,
     "description": "Disaggregated evaluation results across relevant factors."},
    {"id": "ethical_considerations", "label": "Ethical Considerations", "blocking": True,
     "description": "Ethical challenges and mitigation strategies for deployment."},
    {"id": "caveats_recommendations", "label": "Caveats & Recommendations", "blocking": False,
     "description": "Known limitations, caveats, and recommendations for users."},
    {"id": "out_of_scope_uses", "label": "Out-of-Scope Uses", "blocking": True,
     "description": "Explicit list of uses the model is not designed or safe for."},
    {"id": "technical_specifications", "label": "Technical Specifications", "blocking": False,
     "description": "Architecture, parameter count, hardware requirements, inference specs."},
    {"id": "environmental_impact", "label": "Environmental Impact", "blocking": False,
     "description": "Training energy (MWh), carbon footprint (tCO2e), deployment emissions."},
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AISystemInput:
    """Input for a single AI system governance assessment."""
    system_id: str
    system_name: str
    # Classification
    ai_act_category: Optional[str] = None   # key from EU_AI_ACT_HIGH_RISK_CATEGORIES
    is_gpai: bool = False                    # General Purpose AI
    is_in_scope_eu_ai_act: bool = True
    # Scale
    parameter_scale: str = "1b_10b"         # key from MODEL_ENERGY_PROFILES
    daily_queries: Optional[float] = None
    deployment_region: str = "EU"
    deployment_grid_carbon_gco2_kwh: float = 311.0  # default: Germany grid
    training_complete: bool = True
    # NIST RMF — dict of {category_id: score} where score in {0, 0.5, 1}
    nist_rmf_scores: Optional[Dict[str, float]] = None
    # OECD Principles — dict of {sub_indicator_id: score} where score in {0, 0.5, 1}
    oecd_scores: Optional[Dict[str, float]] = None
    # Model card completeness — dict of {field_id: bool}
    model_card_fields: Optional[Dict[str, bool]] = None
    # Context
    sector: Optional[str] = None
    description: Optional[str] = None
    developer_name: Optional[str] = None


@dataclass
class BiasAssessmentInput:
    """Input for algorithmic bias assessment."""
    system_id: str
    # Protected characteristics assessed
    protected_characteristics: List[str] = field(default_factory=list)
    # Per-characteristic metric values: {characteristic: {metric_name: value}}
    metric_values: Optional[Dict[str, Dict[str, float]]] = None
    sample_size: Optional[int] = None
    assessment_date: Optional[str] = None
    test_dataset_description: Optional[str] = None


@dataclass
class AIPortfolioInput:
    """Input for portfolio-level AI governance assessment."""
    portfolio_id: str
    systems: List[Dict[str, Any]]           # list of AI system descriptors
    organisation_name: Optional[str] = None
    reporting_period: str = "2024"
    organisation_sector: Optional[str] = None


@dataclass
class AIGovernanceResult:
    """Result of a full AI system ESG governance assessment."""
    system_id: str
    system_name: str
    # EU AI Act
    eu_ai_act_risk_tier: str                # "unacceptable" | "high_risk" | "limited_risk" | "minimal_risk"
    eu_ai_act_score: float                   # 0-100
    eu_ai_act_gaps: List[str]
    # NIST RMF
    nist_rmf_score: float                    # 0-100
    nist_rmf_tier: str                       # "optimising" | "managed" | "repeatable" | "partial" | "initial"
    # OECD Principles
    oecd_score: float                        # 0-100
    # Energy & Emissions
    training_energy_mwh: float
    inference_annual_energy_mwh: float
    annual_scope2_tco2e: float
    # Bias
    bias_severity: Optional[str]             # "low" | "medium" | "high" | "critical"
    bias_flags: List[str]
    # Model Card
    model_card_completeness_pct: float
    model_card_gaps: List[str]
    # ESG Composite
    governance_score: float                  # 0-100
    environmental_score: float               # 0-100
    social_score: float                      # 0-100
    esg_composite_score: float               # 0-100
    esg_tier: str                            # "leading" | "advanced" | "developing" | "initial"
    summary: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AIGovernanceEngine:
    """
    AI Governance & ESG Engine (E77).

    Implements EU AI Act 2024/1689, NIST AI RMF 1.0, OECD AI Principles 2023,
    AI energy/emissions, algorithmic bias assessment, model card completeness,
    and AI ESG composite scoring.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess_ai_system(self, system_input: AISystemInput) -> AIGovernanceResult:
        """
        Full AI system ESG governance assessment.

        Integrates EU AI Act risk classification, NIST RMF scoring,
        OECD Principles scoring, energy/emissions calculation,
        model card completeness, and ESG composite scoring.
        """
        # 1. EU AI Act
        eu_result = self.classify_eu_ai_act_risk(system_input)
        eu_score = eu_result["compliance_score"]
        eu_tier = eu_result["risk_tier"]
        eu_gaps = eu_result["compliance_gaps"]

        # 2. NIST RMF
        nist_result = self.score_nist_rmf(system_input)
        nist_score = nist_result["overall_score"]
        nist_tier = nist_result["rmf_tier"]

        # 3. OECD Principles
        oecd_result = self.score_oecd_principles(system_input)
        oecd_score = oecd_result["overall_score"]

        # 4. Energy & emissions
        energy_result = self.calculate_ai_energy(system_input)
        training_mwh = energy_result["training_energy_mwh"]
        inference_mwh = energy_result["inference_annual_energy_mwh"]
        annual_tco2e = energy_result["annual_scope2_tco2e"]

        # 5. Model card
        card_result = self.score_model_card(system_input)
        card_pct = card_result["completeness_pct"]
        card_gaps = card_result["missing_fields"]

        # 6. Bias assessment (from system_input defaults — no metric values)
        # Build a minimal bias input from system context
        bias_input = BiasAssessmentInput(
            system_id=system_input.system_id,
            protected_characteristics=[],
        )
        bias_result = self.assess_algorithmic_bias(bias_input)
        bias_severity = bias_result.get("overall_bias_severity", "low")
        bias_flags = bias_result.get("adverse_impact_flags", [])

        # 7. ESG composite
        gov_score = self._governance_pillar(eu_score, nist_score)
        env_score = self._environmental_pillar(annual_tco2e, system_input)
        soc_score = self._social_pillar(bias_severity, card_pct, oecd_score)
        esg_composite = 0.35 * gov_score + 0.30 * env_score + 0.35 * soc_score
        esg_tier = self._esg_tier(esg_composite)

        summary = (
            f"{system_input.system_name} — EU AI Act: {eu_tier} ({eu_score:.0f}/100), "
            f"NIST RMF: {nist_tier} ({nist_score:.0f}/100), "
            f"Energy: {annual_tco2e:.2f} tCO2e/yr, "
            f"ESG: {esg_tier} ({esg_composite:.1f}/100)."
        )

        return AIGovernanceResult(
            system_id=system_input.system_id,
            system_name=system_input.system_name,
            eu_ai_act_risk_tier=eu_tier,
            eu_ai_act_score=round(eu_score, 1),
            eu_ai_act_gaps=eu_gaps,
            nist_rmf_score=round(nist_score, 1),
            nist_rmf_tier=nist_tier,
            oecd_score=round(oecd_score, 1),
            training_energy_mwh=round(training_mwh, 4),
            inference_annual_energy_mwh=round(inference_mwh, 4),
            annual_scope2_tco2e=round(annual_tco2e, 4),
            bias_severity=bias_severity,
            bias_flags=bias_flags,
            model_card_completeness_pct=round(card_pct, 1),
            model_card_gaps=card_gaps,
            governance_score=round(gov_score, 1),
            environmental_score=round(env_score, 1),
            social_score=round(soc_score, 1),
            esg_composite_score=round(esg_composite, 1),
            esg_tier=esg_tier,
            summary=summary,
        )

    def classify_eu_ai_act_risk(self, system_input: AISystemInput) -> Dict[str, Any]:
        """
        EU AI Act 2024/1689 risk tier classification.

        Determines risk tier (unacceptable/high_risk/limited_risk/minimal_risk)
        based on AI category and derives compliance requirements and score.

        Art 5: Prohibited practices → unacceptable
        Annex III + Art 6: High-risk systems → mandatory requirements
        Art 50: Limited risk → transparency obligations only
        Remainder: Minimal risk → no mandatory obligations
        """
        category = system_input.ai_act_category
        cat_profile = EU_AI_ACT_HIGH_RISK_CATEGORIES.get(category or "", {})

        # Determine tier
        if category == "social_scoring":
            risk_tier = "unacceptable"
            base_score = 0.0
            tier_description = "Art 5(1)(c): Prohibited. System must not be deployed."
        elif category in EU_AI_ACT_HIGH_RISK_CATEGORIES and category != "social_scoring":
            risk_tier = "high_risk"
            base_score = 50.0
            tier_description = f"Annex III / Art 6: High-risk system. Mandatory requirements apply."
        elif system_input.is_gpai:
            risk_tier = "high_risk"
            base_score = 55.0
            tier_description = "Art 51: GPAI model with potential systemic risk."
        elif not system_input.is_in_scope_eu_ai_act:
            risk_tier = "minimal_risk"
            base_score = 90.0
            tier_description = "Out of scope or minimal risk — no mandatory obligations."
        else:
            risk_tier = "limited_risk"
            base_score = 75.0
            tier_description = "Art 50: Limited risk — transparency obligations only."

        # Compliance obligations per tier
        tier_requirements: Dict[str, List[str]] = {
            "unacceptable": [],
            "high_risk": [
                "risk_management_system_art9",
                "data_governance_art10",
                "technical_documentation_art11",
                "record_keeping_logs_art12",
                "transparency_users_art13",
                "human_oversight_art14",
                "accuracy_robustness_art15",
                "quality_management_art17",
                "conformity_assessment_art43",
                "eu_database_registration_art49",
            ],
            "limited_risk": [
                "transparency_disclosure_art50",
                "chatbot_disclosure_art50b",
                "deepfake_labelling_art50c",
            ],
            "minimal_risk": [],
        }
        requirements = tier_requirements.get(risk_tier, [])

        # Score based on what the system provides (default assumptions without full audit)
        # In practice, caller would pass audit evidence; we score conservatively
        compliance_gaps: List[str] = []
        met = 0
        total = len(requirements)

        # Heuristic: score based on model card and disclosure fields
        has_docs = (system_input.model_card_fields or {}).get("model_details", False)
        has_intended_use = (system_input.model_card_fields or {}).get("intended_use", False)
        has_ethical = (system_input.model_card_fields or {}).get("ethical_considerations", False)
        has_env = (system_input.model_card_fields or {}).get("environmental_impact", False)

        if risk_tier == "high_risk" and total > 0:
            provision_map = {
                "risk_management_system_art9": has_ethical,
                "data_governance_art10": has_docs,
                "technical_documentation_art11": has_docs,
                "record_keeping_logs_art12": False,  # requires runtime logging — default no
                "transparency_users_art13": has_intended_use,
                "human_oversight_art14": False,
                "accuracy_robustness_art15": False,
                "quality_management_art17": has_docs,
                "conformity_assessment_art43": False,
                "eu_database_registration_art49": False,
            }
            for req in requirements:
                if provision_map.get(req, False):
                    met += 1
                else:
                    compliance_gaps.append(req)
            compliance_score = base_score + (met / total) * 50.0
        elif risk_tier == "limited_risk":
            compliance_score = base_score if has_intended_use else base_score - 15.0
            compliance_gaps = [] if has_intended_use else ["transparency_disclosure_art50"]
        else:
            compliance_score = base_score
            compliance_gaps = []

        # GPAI systemic risk additional obligations
        gpai_obligations: List[str] = []
        if system_input.is_gpai:
            gpai_obligations = [
                "adversarial_testing_art55",
                "incident_reporting_art55",
                "cybersecurity_art55",
                "energy_consumption_reporting_art55",
                "model_card_publication_art53",
                "copyright_policy_art53",
            ]

        return {
            "system_id": system_input.system_id,
            "ai_act_category": category,
            "risk_tier": risk_tier,
            "tier_description": tier_description,
            "compliance_score": round(compliance_score, 1),
            "requirements_applicable": requirements,
            "requirements_met": met,
            "requirements_total": total,
            "compliance_gaps": compliance_gaps,
            "is_gpai": system_input.is_gpai,
            "gpai_obligations": gpai_obligations,
            "category_profile": cat_profile if cat_profile else {},
            "regulation": "EU AI Act (EU) 2024/1689",
            "effective_date_high_risk": "2026-08-02",
            "effective_date_prohibited": "2025-02-02",
        }

    def score_nist_rmf(self, system_input: AISystemInput) -> Dict[str, Any]:
        """
        NIST AI RMF 1.0 (2023) scoring.

        Scores the AI system against 4 functions (Govern/Map/Measure/Manage),
        19 sub-categories. Scores: 1 = fully met, 0.5 = partially met, 0 = not met.
        Returns overall score (0-100), tier, and per-function breakdown.
        """
        provided = system_input.nist_rmf_scores or {}

        function_scores: Dict[str, Dict[str, Any]] = {}
        total_weighted = 0.0

        for func_id, func_data in NIST_RMF_CATEGORIES.items():
            cats = func_data["categories"]
            func_total = len(cats)
            func_met = 0.0
            cat_results: Dict[str, Any] = {}

            for cat_id, cat_desc in cats.items():
                score = provided.get(cat_id, 0.0)  # default: not assessed
                func_met += score
                cat_results[cat_id] = {
                    "description": cat_desc,
                    "score": score,
                    "status": "met" if score == 1.0 else ("partial" if score == 0.5 else "not_met"),
                }

            func_score_pct = (func_met / func_total) * 100 if func_total > 0 else 0.0
            function_scores[func_id] = {
                "label": func_data["label"],
                "weight": func_data["weight"],
                "score_pct": round(func_score_pct, 1),
                "categories_met": func_met,
                "categories_total": func_total,
                "category_details": cat_results,
            }
            total_weighted += func_score_pct * func_data["weight"]

        overall_score = total_weighted  # weights sum to 1.0

        # RMF maturity tier
        if overall_score >= 80:
            tier = "optimising"
        elif overall_score >= 60:
            tier = "managed"
        elif overall_score >= 40:
            tier = "repeatable"
        elif overall_score >= 20:
            tier = "partial"
        else:
            tier = "initial"

        # Current vs target profile gap
        gaps: List[str] = []
        for func_id, func_res in function_scores.items():
            if func_res["score_pct"] < 50:
                gaps.append(f"{func_id} ({func_res['label']}): {func_res['score_pct']:.0f}%")

        return {
            "system_id": system_input.system_id,
            "overall_score": round(overall_score, 1),
            "rmf_tier": tier,
            "function_scores": function_scores,
            "improvement_gaps": gaps,
            "framework": "NIST AI RMF 1.0 (January 2023)",
            "profile_note": (
                "Scores default to 0 for unassessed categories. "
                "Provide nist_rmf_scores dict to enable full scoring."
            ),
        }

    def score_oecd_principles(self, system_input: AISystemInput) -> Dict[str, Any]:
        """
        OECD AI Principles 2023 scoring.

        Scores across 5 principles (inclusive_growth, human_centred, transparency,
        robustness, accountability), each weighted 20%. Sub-indicator scores:
        1 = met, 0.5 = partial, 0 = not met.
        """
        provided = system_input.oecd_scores or {}

        principle_scores: Dict[str, Any] = {}
        total_weighted = 0.0

        for principle_id, principle_data in _OECD_PRINCIPLES.items():
            subs = principle_data["sub_indicators"]
            sub_total = len(subs)
            sub_met = 0.0
            sub_details: Dict[str, Any] = {}

            for sub_id, sub_desc in subs.items():
                score = provided.get(sub_id, 0.0)
                sub_met += score
                sub_details[sub_id] = {
                    "description": sub_desc,
                    "score": score,
                    "status": "met" if score == 1.0 else ("partial" if score == 0.5 else "not_met"),
                }

            p_score = (sub_met / sub_total) * 100 if sub_total > 0 else 0.0
            principle_scores[principle_id] = {
                "label": principle_data["label"],
                "weight": principle_data["weight"],
                "score_pct": round(p_score, 1),
                "sub_indicators": sub_details,
            }
            total_weighted += p_score * principle_data["weight"]

        overall_score = total_weighted

        return {
            "system_id": system_input.system_id,
            "overall_score": round(overall_score, 1),
            "principle_scores": principle_scores,
            "framework": "OECD AI Principles (updated 2023)",
            "note": "Scores default to 0 for unassessed sub-indicators.",
        }

    def calculate_ai_energy(self, system_input: AISystemInput) -> Dict[str, Any]:
        """
        AI Energy Consumption and Scope 2 Emissions calculation.

        Training energy by model parameter scale (one-time, amortised to reporting year).
        Inference energy: daily_queries × energy_per_query × 365.
        Annual Scope 2 = (training + inference) × grid carbon factor.
        """
        profile = MODEL_ENERGY_PROFILES.get(
            system_input.parameter_scale, MODEL_ENERGY_PROFILES["1b_10b"]
        )

        training_mwh = profile["training_energy_mwh"] if system_input.training_complete else 0.0
        energy_per_query_wh = profile["inference_energy_per_query_wh"]

        daily_queries = system_input.daily_queries or 10_000  # default: 10K queries/day
        inference_annual_kwh = daily_queries * energy_per_query_wh * 365 / 1_000
        inference_annual_mwh = inference_annual_kwh / 1_000

        total_annual_mwh = training_mwh + inference_annual_mwh
        grid_carbon = system_input.deployment_grid_carbon_gco2_kwh

        # Scope 2 tCO2e = MWh × 1000 kWh/MWh × gCO2/kWh / 1,000,000 g/t
        annual_tco2e = total_annual_mwh * 1_000 * grid_carbon / 1_000_000

        # Benchmark comparison (data centre average: 475 gCO2/kWh → typical EU mix)
        benchmark_tco2e = total_annual_mwh * 1_000 * 475.0 / 1_000_000

        # Renewable energy required for net-zero
        renewable_target_mwh = total_annual_mwh  # 1:1 renewable match (market-based)

        return {
            "system_id": system_input.system_id,
            "parameter_scale": system_input.parameter_scale,
            "model_profile": profile,
            "training_energy_mwh": round(training_mwh, 4),
            "inference_daily_queries": daily_queries,
            "inference_energy_per_query_wh": energy_per_query_wh,
            "inference_annual_energy_mwh": round(inference_annual_mwh, 4),
            "total_annual_energy_mwh": round(total_annual_mwh, 4),
            "deployment_grid_carbon_gco2_kwh": grid_carbon,
            "annual_scope2_tco2e": round(annual_tco2e, 6),
            "benchmark_scope2_tco2e_eu_avg": round(benchmark_tco2e, 6),
            "renewable_energy_target_mwh": round(renewable_target_mwh, 4),
            "scope": "Scope 2 (location-based or market-based per GHG Protocol)",
            "notes": [
                "Training energy is a one-time cost; amortise over expected model lifetime for annual reporting.",
                "Inference energy scales linearly with query volume.",
                "Scope 3 includes supply chain manufacturing of hardware (Scope 3 Cat 2).",
                "Source: Patterson et al. 2021; Samsi et al. 2023; model operator sustainability reports.",
            ],
        }

    def assess_algorithmic_bias(self, bias_input: BiasAssessmentInput) -> Dict[str, Any]:
        """
        Algorithmic Bias Assessment across 7 protected characteristics.

        Metrics:
          - Disparate Impact Ratio (DIR) = minority_positive_rate / majority_positive_rate
            Adverse if DIR < 0.80 (4/5 Rule, US EEOC / EU non-discrimination case law)
          - Statistical Parity Difference (SPD) = P(Y=1|group=1) - P(Y=1|group=0)
            Adverse if SPD < -0.10
          - Equalized Odds — whether TPR and FPR are equal across groups

        Bias severity: critical (DIR<0.6), high (DIR<0.7), medium (DIR<0.8), low (DIR≥0.8)
        """
        all_characteristics = [
            "gender", "race_ethnicity", "age", "disability",
            "religion", "sexual_orientation", "nationality"
        ]
        characteristics = bias_input.protected_characteristics or all_characteristics
        metrics = bias_input.metric_values or {}

        char_results: Dict[str, Any] = {}
        adverse_flags: List[str] = []
        max_severity_rank = 0
        severity_rank_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}

        for char in characteristics:
            char_metrics = metrics.get(char, {})
            dir_value = char_metrics.get("disparate_impact_ratio", None)
            spd_value = char_metrics.get("statistical_parity_difference", None)
            eq_odds = char_metrics.get("equalized_odds_parity", None)

            flags: List[str] = []
            severity = "low"

            if dir_value is not None:
                if dir_value < 0.60:
                    severity = "critical"
                    flags.append(f"DIR={dir_value:.3f} < 0.60 (critical adverse impact)")
                elif dir_value < 0.70:
                    severity = "high"
                    flags.append(f"DIR={dir_value:.3f} < 0.70 (high adverse impact)")
                elif dir_value < 0.80:
                    severity = "medium"
                    flags.append(f"DIR={dir_value:.3f} < 0.80 (adverse per 4/5 Rule)")
                else:
                    flags.append(f"DIR={dir_value:.3f} ≥ 0.80 (acceptable)")

            if spd_value is not None and spd_value < -0.10:
                flags.append(f"SPD={spd_value:.3f} < -0.10 (adverse statistical parity)")
                if severity == "low":
                    severity = "medium"

            if eq_odds is not None and abs(eq_odds) > 0.10:
                flags.append(f"Equalized Odds parity gap={eq_odds:.3f} > 0.10")
                if severity == "low":
                    severity = "medium"

            if not char_metrics:
                flags.append("No bias metrics provided — assessment required")
                severity = "low"

            if severity in ("high", "critical"):
                adverse_flags.append(f"{char}: {severity}")

            rank = severity_rank_map.get(severity, 1)
            max_severity_rank = max(max_severity_rank, rank)

            char_results[char] = {
                "metrics": char_metrics,
                "flags": flags,
                "severity": severity,
            }

        severity_rank_reverse = {v: k for k, v in severity_rank_map.items()}
        overall_severity = severity_rank_reverse.get(max_severity_rank, "low")

        return {
            "system_id": bias_input.system_id,
            "characteristics_assessed": characteristics,
            "characteristic_results": char_results,
            "adverse_impact_flags": adverse_flags,
            "overall_bias_severity": overall_severity,
            "sample_size": bias_input.sample_size,
            "assessment_date": bias_input.assessment_date,
            "methodology": {
                "disparate_impact_threshold": 0.80,
                "rule": "EEOC 4/5 Rule; EU Equal Treatment Directives",
                "metrics": ["Disparate Impact Ratio", "Statistical Parity Difference", "Equalized Odds"],
                "references": [
                    "US EEOC Uniform Guidelines on Employee Selection Procedures (1978)",
                    "EU Directive 2000/43/EC — Racial Equality",
                    "EU Directive 2006/54/EC — Gender Equality",
                    "Barocas et al. Fairness and Machine Learning (2023)",
                ],
            },
            "recommendations": self._bias_recommendations(overall_severity, adverse_flags),
        }

    def score_model_card(self, system_input: AISystemInput) -> Dict[str, Any]:
        """
        Model Card Completeness assessment (NIST/Google standard — 12 fields).

        Checks which of the 12 required model card fields are present.
        Returns completeness % and list of missing fields, flagging
        blocking fields (those required for EU AI Act Art 11/13 compliance).
        """
        provided = system_input.model_card_fields or {}
        total = len(_MODEL_CARD_FIELDS)
        met = 0
        missing: List[str] = []
        blocking_gaps: List[str] = []
        field_results: List[Dict[str, Any]] = []

        for field_def in _MODEL_CARD_FIELDS:
            fid = field_def["id"]
            present = provided.get(fid, False)
            if present:
                met += 1
            else:
                missing.append(fid)
                if field_def["blocking"]:
                    blocking_gaps.append(fid)

            field_results.append({
                "field_id": fid,
                "label": field_def["label"],
                "description": field_def["description"],
                "present": present,
                "blocking": field_def["blocking"],
            })

        completeness_pct = (met / total) * 100 if total > 0 else 0.0

        return {
            "system_id": system_input.system_id,
            "completeness_pct": round(completeness_pct, 1),
            "fields_met": met,
            "fields_total": total,
            "missing_fields": missing,
            "blocking_gaps": blocking_gaps,
            "field_details": field_results,
            "eu_ai_act_art11_readiness": len(blocking_gaps) == 0,
            "standard": "NIST AI RMF Model Card + Google Model Card (Mitchell et al. 2019)",
            "note": "Blocking fields are required for EU AI Act Art 11 (Technical documentation) & Art 13 (Transparency).",
        }

    def aggregate_ai_portfolio(self, portfolio_input: AIPortfolioInput) -> Dict[str, Any]:
        """
        Portfolio-level AI governance assessment.

        Aggregates ESG scores, energy footprints, EU AI Act risk distributions,
        and bias flags across all AI systems in the portfolio. Returns portfolio
        averages, highest-risk systems, and organisational recommendations.
        """
        total_systems = len(portfolio_input.systems)
        if total_systems == 0:
            return {"error": "No systems provided for portfolio assessment."}

        system_results: List[Dict[str, Any]] = []
        total_tco2e = 0.0
        total_training_mwh = 0.0
        esg_scores: List[float] = []
        nist_scores: List[float] = []
        risk_tier_counts: Dict[str, int] = {}
        high_risk_systems: List[str] = []
        bias_flags_all: List[str] = []

        for sys_desc in portfolio_input.systems:
            # Build AISystemInput from descriptor
            sys_input = AISystemInput(
                system_id=sys_desc.get("system_id", "UNKNOWN"),
                system_name=sys_desc.get("system_name", "Unknown System"),
                ai_act_category=sys_desc.get("ai_act_category"),
                is_gpai=sys_desc.get("is_gpai", False),
                is_in_scope_eu_ai_act=sys_desc.get("is_in_scope_eu_ai_act", True),
                parameter_scale=sys_desc.get("parameter_scale", "1b_10b"),
                daily_queries=sys_desc.get("daily_queries"),
                deployment_region=sys_desc.get("deployment_region", "EU"),
                deployment_grid_carbon_gco2_kwh=sys_desc.get(
                    "deployment_grid_carbon_gco2_kwh", 311.0
                ),
                training_complete=sys_desc.get("training_complete", True),
                nist_rmf_scores=sys_desc.get("nist_rmf_scores"),
                oecd_scores=sys_desc.get("oecd_scores"),
                model_card_fields=sys_desc.get("model_card_fields"),
                sector=sys_desc.get("sector"),
                description=sys_desc.get("description"),
                developer_name=sys_desc.get("developer_name"),
            )
            result = self.assess_ai_system(sys_input)

            total_tco2e += result.annual_scope2_tco2e
            total_training_mwh += result.training_energy_mwh
            esg_scores.append(result.esg_composite_score)
            nist_scores.append(result.nist_rmf_score)

            tier = result.eu_ai_act_risk_tier
            risk_tier_counts[tier] = risk_tier_counts.get(tier, 0) + 1
            if tier in ("unacceptable", "high_risk"):
                high_risk_systems.append(result.system_name)

            bias_flags_all.extend([f"{result.system_name}: {f}" for f in result.bias_flags])

            system_results.append({
                "system_id": result.system_id,
                "system_name": result.system_name,
                "eu_ai_act_risk_tier": tier,
                "eu_ai_act_score": result.eu_ai_act_score,
                "nist_rmf_score": result.nist_rmf_score,
                "esg_composite_score": result.esg_composite_score,
                "esg_tier": result.esg_tier,
                "annual_scope2_tco2e": result.annual_scope2_tco2e,
                "bias_severity": result.bias_severity,
                "model_card_completeness_pct": result.model_card_completeness_pct,
            })

        avg_esg = sum(esg_scores) / total_systems
        avg_nist = sum(nist_scores) / total_systems
        portfolio_esg_tier = self._esg_tier(avg_esg)

        return {
            "portfolio_id": portfolio_input.portfolio_id,
            "organisation_name": portfolio_input.organisation_name,
            "reporting_period": portfolio_input.reporting_period,
            "total_ai_systems": total_systems,
            "portfolio_avg_esg_score": round(avg_esg, 1),
            "portfolio_esg_tier": portfolio_esg_tier,
            "portfolio_avg_nist_rmf_score": round(avg_nist, 1),
            "total_annual_scope2_tco2e": round(total_tco2e, 4),
            "total_training_energy_mwh": round(total_training_mwh, 4),
            "eu_ai_act_risk_distribution": risk_tier_counts,
            "high_risk_systems": high_risk_systems,
            "portfolio_bias_flags": bias_flags_all,
            "system_results": system_results,
            "portfolio_recommendations": self._portfolio_recommendations(
                portfolio_esg_tier, high_risk_systems, total_tco2e
            ),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _governance_pillar(self, eu_score: float, nist_score: float) -> float:
        """Governance pillar: EU AI Act 50% + NIST RMF 50%."""
        return (eu_score * 0.50) + (nist_score * 0.50)

    def _environmental_pillar(self, annual_tco2e: float, system_input: AISystemInput) -> float:
        """
        Environmental pillar score (0-100).

        Lower emissions → higher score. Benchmarked against a typical
        enterprise software workload (~10 tCO2e/yr for large deployments).
        Rewards low-emission grids and small model sizes.
        """
        # Benchmark: 10 tCO2e/yr → 50 score; 0 tCO2e → 100; 100+ tCO2e → 0
        if annual_tco2e <= 0:
            return 100.0
        elif annual_tco2e >= 100:
            return 0.0
        else:
            score = 100 - (annual_tco2e / 100.0) * 100.0
            # Bonus for low-carbon grid (<100 gCO2/kWh)
            if system_input.deployment_grid_carbon_gco2_kwh < 100:
                score = min(100, score + 10)
            return score

    def _social_pillar(self, bias_severity: Optional[str], card_pct: float, oecd_score: float) -> float:
        """
        Social pillar: Bias assessment 40% + Model Card 30% + OECD Social 30%.

        Bias maps: critical=0, high=30, medium=60, low=90.
        """
        bias_map = {"critical": 0, "high": 30, "medium": 60, "low": 90, None: 70}
        bias_score = bias_map.get(bias_severity, 70)
        return (bias_score * 0.40) + (card_pct * 0.30) + (oecd_score * 0.30)

    def _esg_tier(self, score: float) -> str:
        """Map ESG composite score to tier label."""
        if score >= 75:
            return "leading"
        elif score >= 55:
            return "advanced"
        elif score >= 35:
            return "developing"
        else:
            return "initial"

    def _bias_recommendations(
        self, severity: str, adverse_flags: List[str]
    ) -> List[str]:
        """Generate bias remediation recommendations."""
        recs: List[str] = []
        if severity == "critical":
            recs.append("IMMEDIATE: Suspend deployment pending bias remediation.")
            recs.append("Conduct root cause analysis on training data composition.")
            recs.append("Engage external fairness auditor (ISO/IEC 24027).")
        elif severity == "high":
            recs.append("Prioritise bias remediation before next model release.")
            recs.append("Implement adversarial debiasing or reweighting techniques.")
            recs.append("Expand evaluation dataset for under-represented groups.")
        elif severity == "medium":
            recs.append("Document bias risk in model card ethical considerations section.")
            recs.append("Monitor DIR metrics in production with monthly cadence.")
        else:
            recs.append("Maintain regular bias monitoring cadence.")
        if adverse_flags:
            recs.append(f"Flagged characteristics: {', '.join([f.split(':')[0] for f in adverse_flags])}.")
        recs.append("Reference: EU AI Act Art 9/10 (data governance), NIST AI RMF MS-3.")
        return recs

    def _portfolio_recommendations(
        self,
        esg_tier: str,
        high_risk_systems: List[str],
        total_tco2e: float,
    ) -> List[str]:
        """Portfolio-level governance recommendations."""
        recs: List[str] = []
        if high_risk_systems:
            recs.append(
                f"EU AI Act compliance programme required for: {', '.join(high_risk_systems[:3])}."
            )
        if esg_tier in ("initial", "developing"):
            recs.append("Implement NIST AI RMF Govern function — establish AI risk policy.")
            recs.append("Complete model cards for all deployed AI systems.")
        if total_tco2e > 50:
            recs.append("Consider renewable energy procurement (PPAs/RECs) for AI workloads.")
            recs.append("Evaluate model distillation or efficient architectures to reduce compute.")
        recs.append("Publish annual AI ESG report aligned with NIST AI RMF and EU AI Act requirements.")
        recs.append("Register applicable high-risk systems in EU AI database (Art 49).")
        return recs
