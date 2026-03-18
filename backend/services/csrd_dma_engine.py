"""
CSRD Double Materiality Assessment (DMA) Engine
================================================
ESRS 1 Sections 42-49 — Double materiality methodology.

Models both dimensions of materiality:
- Impact materiality (inside-out): company's impacts on people and environment
- Financial materiality (outside-in): sustainability matters that generate
  financial risks and opportunities for the company

Cross-framework linkage:
- TCFD (materiality basis for climate risks)
- GRI 3 (material topics process)
- ISSB S1 (significance vs materiality thresholds)
- EU Taxonomy (environmental material topics)
- OECD Guidelines (due diligence for adverse impacts)
"""
from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

ESRS_TOPICS = {
    "E1": {
        "name": "Climate Change",
        "standard": "ESRS E1",
        "sub_topics": ["climate_adaptation", "climate_mitigation", "energy"],
    },
    "E2": {
        "name": "Pollution",
        "standard": "ESRS E2",
        "sub_topics": ["air_pollution", "water_pollution", "soil_pollution", "microplastics"],
    },
    "E3": {
        "name": "Water and Marine",
        "standard": "ESRS E3",
        "sub_topics": ["water_consumption", "water_withdrawal", "marine_ecosystems"],
    },
    "E4": {
        "name": "Biodiversity",
        "standard": "ESRS E4",
        "sub_topics": ["land_use_change", "species_loss", "ecosystem_degradation"],
    },
    "E5": {
        "name": "Circular Economy",
        "standard": "ESRS E5",
        "sub_topics": ["resource_inflows", "resource_outflows", "waste"],
    },
    "S1": {
        "name": "Own Workforce",
        "standard": "ESRS S1",
        "sub_topics": ["working_conditions", "equal_treatment", "other_work_rights"],
    },
    "S2": {
        "name": "Workers in Value Chain",
        "standard": "ESRS S2",
        "sub_topics": ["working_conditions_vc", "human_rights_vc"],
    },
    "S3": {
        "name": "Affected Communities",
        "standard": "ESRS S3",
        "sub_topics": ["community_economic_impacts", "civil_political_rights", "cultural_rights"],
    },
    "S4": {
        "name": "Consumers and End-users",
        "standard": "ESRS S4",
        "sub_topics": ["information_impacts", "personal_safety", "social_inclusion"],
    },
    "G1": {
        "name": "Business Conduct",
        "standard": "ESRS G1",
        "sub_topics": ["corporate_culture", "whistleblower", "corruption_bribery", "supplier_relations"],
    },
}

# ESRS 1 section 43 — Severity criteria for negative impacts
SEVERITY_CRITERIA = {
    "scale": {
        "weight": 0.35,
        "description": "Breadth of impact — how many affected",
    },
    "scope": {
        "weight": 0.35,
        "description": "Depth of impact — how seriously affected",
    },
    "irremediability": {
        "weight": 0.30,
        "description": "Ease of remediation — irreversibility",
    },
}

# ESRS 1 section 47 — Financial materiality risk types
FINANCIAL_RISK_TYPES = {
    "physical_risk": "Chronic or acute physical climate risk affecting asset value or operations",
    "transition_risk": "Policy, regulatory, technology or market shift risk",
    "systemic_risk": "Broader systemic risks (biodiversity loss, social instability)",
    "legal_risk": "Litigation, liability, enforcement risk",
    "reputational_risk": "Stakeholder perception and brand value risk",
}

# Stakeholder types for engagement
STAKEHOLDER_TYPES = {
    "employees":         {"salience_weight": 0.20},
    "investors":         {"salience_weight": 0.20},
    "customers":         {"salience_weight": 0.15},
    "suppliers":         {"salience_weight": 0.10},
    "local_communities": {"salience_weight": 0.10},
    "ngos":              {"salience_weight": 0.10},
    "regulators":        {"salience_weight": 0.10},
    "media":             {"salience_weight": 0.05},
}

# NACE sector materiality profiles — typical material topics per sector
SECTOR_MATERIALITY = {
    "financial_services": ["E1", "S1", "G1", "S2"],
    "energy":             ["E1", "E2", "E3", "S1", "G1"],
    "manufacturing":      ["E1", "E2", "E5", "S1", "S2", "G1"],
    "real_estate":        ["E1", "E3", "E4", "S1", "S3"],
    "agriculture":        ["E1", "E2", "E3", "E4", "S2", "S3"],
    "technology":         ["E1", "S1", "S4", "G1"],
    "retail":             ["E1", "E5", "S1", "S2", "S4"],
    "healthcare":         ["E1", "S1", "S4", "G1"],
    "transport":          ["E1", "E2", "S1", "S3"],
    "mining":             ["E1", "E2", "E3", "E4", "S1", "S2", "S3", "G1"],
}

# Impact type taxonomy
IMPACT_TYPES = ["actual_negative", "potential_negative", "actual_positive", "potential_positive"]

# Value chain locations
VALUE_CHAIN_LOCATIONS = ["own_operations", "upstream", "downstream", "all"]

# DMA process steps
DMA_PROCESS_STEPS = [
    "context_setting",
    "impact_identification",
    "impact_assessment",
    "topic_prioritisation",
]

# Cross-framework mapping
CROSS_FRAMEWORK_MAP = {
    "TCFD": "DMA climate topics align with TCFD Governance, Strategy, Risk Management, Metrics pillars",
    "GRI_3": "GRI 3 material topics process requires stakeholder engagement and impact assessment",
    "ISSB_S1": "ISSB S1 uses significance threshold (investor focus) vs ESRS double materiality",
    "EU_Taxonomy": "Material E topics feed into EU Taxonomy substantial contribution assessment",
    "OECD_Guidelines": "OECD Guidelines Ch II-VI inform adverse impact identification (ESRS 1 section 43)",
}

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class CSRDDMAEngine:
    """CSRD Double Materiality Assessment engine per ESRS 1 sections 42-49."""

    IMPACT_MATERIALITY_THRESHOLD = 40.0
    FINANCIAL_MATERIALITY_THRESHOLD = 40.0

    # -----------------------------------------------------------------------
    # 1. Impact Materiality Assessment
    # -----------------------------------------------------------------------

    def assess_impact_materiality(
        self,
        entity_id: str,
        sector: str,
        topic_id: str,
        impact_data: dict,
    ) -> dict:
        """
        Score impact materiality per ESRS 1 section 43.

        Severity = weighted average of scale, scope, irremediability (0-100 each).
        Positive impacts use likelihood x magnitude instead of severity.
        """
        rng = random.Random(hash(entity_id + topic_id) & 0xFFFFFFFF)

        scale_score = float(impact_data.get("scale_score", rng.uniform(20, 85)))
        scope_score = float(impact_data.get("scope_score", rng.uniform(20, 85)))
        irremediability_score = float(
            impact_data.get("irremediability_score", rng.uniform(10, 80))
        )
        likelihood_pct = float(impact_data.get("likelihood_pct", rng.uniform(30, 90)))
        impact_type = impact_data.get("impact_type", rng.choice(IMPACT_TYPES))
        value_chain_location = impact_data.get(
            "value_chain_location", rng.choice(VALUE_CHAIN_LOCATIONS)
        )

        # Severity for negative impacts (ESRS 1 section 43(a))
        severity_score = (
            scale_score * SEVERITY_CRITERIA["scale"]["weight"]
            + scope_score * SEVERITY_CRITERIA["scope"]["weight"]
            + irremediability_score * SEVERITY_CRITERIA["irremediability"]["weight"]
        )

        # For potential impacts multiply severity by likelihood
        if "potential" in impact_type:
            impact_materiality_score = severity_score * (likelihood_pct / 100)
        elif "positive" in impact_type:
            # Positive impacts: magnitude x likelihood
            magnitude = float(impact_data.get("magnitude_score", rng.uniform(20, 80)))
            impact_materiality_score = magnitude * (likelihood_pct / 100)
        else:
            impact_materiality_score = severity_score

        impact_materiality_score = min(100.0, round(impact_materiality_score, 2))
        is_material = impact_materiality_score >= self.IMPACT_MATERIALITY_THRESHOLD

        # Check sector-typical materiality
        sector_typical = SECTOR_MATERIALITY.get(sector, [])
        sector_flag = topic_id in sector_typical

        return {
            "entity_id": entity_id,
            "topic_id": topic_id,
            "topic_name": ESRS_TOPICS.get(topic_id, {}).get("name", "Unknown"),
            "sector": sector,
            "scale_score": round(scale_score, 2),
            "scope_score": round(scope_score, 2),
            "irremediability_score": round(irremediability_score, 2),
            "severity_score": round(severity_score, 2),
            "likelihood_pct": round(likelihood_pct, 2),
            "impact_type": impact_type,
            "value_chain_location": value_chain_location,
            "impact_materiality_score": impact_materiality_score,
            "is_material": is_material,
            "sector_typical_material": sector_flag,
            "assessment_basis": "ESRS_1_section_43",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 2. Financial Materiality Assessment
    # -----------------------------------------------------------------------

    def assess_financial_materiality(
        self,
        entity_id: str,
        topic_id: str,
        financial_data: dict,
    ) -> dict:
        """
        Score financial materiality per ESRS 1 section 47.

        financial_materiality_score = magnitude x likelihood (0-100 each).
        """
        rng = random.Random(hash(entity_id + topic_id + "fin") & 0xFFFFFFFF)

        financial_magnitude_score = float(
            financial_data.get("financial_magnitude_score", rng.uniform(20, 90))
        )
        financial_likelihood_score = float(
            financial_data.get("financial_likelihood_score", rng.uniform(20, 90))
        )
        financial_risk_type = financial_data.get(
            "financial_risk_type",
            rng.choice(list(FINANCIAL_RISK_TYPES.keys())),
        )
        time_horizon = financial_data.get("time_horizon", rng.choice(["short", "medium", "long"]))
        revenue_at_risk_pct = float(financial_data.get("revenue_at_risk_pct", rng.uniform(1, 20)))
        capex_implications_mn = float(
            financial_data.get("capex_implications_mn", rng.uniform(0.5, 50))
        )

        financial_materiality_score = min(
            100.0,
            round(financial_magnitude_score * financial_likelihood_score / 100, 2),
        )
        is_material = financial_materiality_score >= self.FINANCIAL_MATERIALITY_THRESHOLD

        return {
            "entity_id": entity_id,
            "topic_id": topic_id,
            "topic_name": ESRS_TOPICS.get(topic_id, {}).get("name", "Unknown"),
            "financial_magnitude_score": round(financial_magnitude_score, 2),
            "financial_likelihood_score": round(financial_likelihood_score, 2),
            "financial_materiality_score": financial_materiality_score,
            "financial_risk_type": financial_risk_type,
            "financial_risk_description": FINANCIAL_RISK_TYPES.get(financial_risk_type, ""),
            "time_horizon": time_horizon,
            "revenue_at_risk_pct": round(revenue_at_risk_pct, 2),
            "capex_implications_mn": round(capex_implications_mn, 2),
            "is_material": is_material,
            "assessment_basis": "ESRS_1_section_47",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 3. Stakeholder Engagement
    # -----------------------------------------------------------------------

    def run_stakeholder_engagement(
        self,
        entity_id: str,
        stakeholder_data: dict,
    ) -> dict:
        """
        Score stakeholder engagement quality across 5 elements:
        identification, dialogue, documentation, integration, feedback.
        """
        rng = random.Random(hash(entity_id + "stkh") & 0xFFFFFFFF)

        engaged_types: list = stakeholder_data.get("engaged_types", [])
        if not engaged_types:
            all_types = list(STAKEHOLDER_TYPES.keys())
            k = rng.randint(3, len(all_types))
            engaged_types = rng.sample(all_types, k)

        # Five engagement quality elements (0-100 each, averaged)
        element_scores = {
            "identification": float(
                stakeholder_data.get("identification_score", rng.uniform(40, 95))
            ),
            "dialogue": float(stakeholder_data.get("dialogue_score", rng.uniform(40, 95))),
            "documentation": float(
                stakeholder_data.get("documentation_score", rng.uniform(35, 90))
            ),
            "integration": float(
                stakeholder_data.get("integration_score", rng.uniform(30, 85))
            ),
            "feedback": float(stakeholder_data.get("feedback_score", rng.uniform(25, 80))),
        }

        engagement_quality_score = round(
            sum(element_scores.values()) / len(element_scores), 2
        )

        # Salience-weighted coverage
        total_salience = sum(
            STAKEHOLDER_TYPES.get(t, {}).get("salience_weight", 0.05)
            for t in engaged_types
        )
        coverage_pct = round(min(100.0, total_salience * 100 / 1.0), 2)

        return {
            "entity_id": entity_id,
            "stakeholders_engaged": len(engaged_types),
            "stakeholder_types": engaged_types,
            "coverage_pct": coverage_pct,
            "element_scores": {k: round(v, 2) for k, v in element_scores.items()},
            "engagement_quality_score": engagement_quality_score,
            "engagement_quality_tier": (
                "excellent" if engagement_quality_score >= 80
                else "good" if engagement_quality_score >= 60
                else "adequate" if engagement_quality_score >= 40
                else "insufficient"
            ),
            "assessment_basis": "ESRS_1_section_45_stakeholder_engagement",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 4. Topic Prioritisation
    # -----------------------------------------------------------------------

    def prioritise_topics(
        self,
        entity_id: str,
        sector: str,
        impact_scores: dict,
        financial_scores: dict,
        stakeholder_scores: dict,
    ) -> dict:
        """
        Rank topics by combined score and assign materiality_basis.

        combined_score = max(impact_score, financial_score) x stakeholder_weight
        """
        rng = random.Random(hash(entity_id + "prio") & 0xFFFFFFFF)

        all_topics = list(ESRS_TOPICS.keys())
        ranked: list[dict] = []

        for topic_id in all_topics:
            imp = float(impact_scores.get(topic_id, rng.uniform(20, 85)))
            fin = float(financial_scores.get(topic_id, rng.uniform(20, 85)))
            stk = float(stakeholder_scores.get(topic_id, rng.uniform(30, 90)))

            # Double materiality: material if either dimension is material
            imp_material = imp >= self.IMPACT_MATERIALITY_THRESHOLD
            fin_material = fin >= self.FINANCIAL_MATERIALITY_THRESHOLD

            if imp_material and fin_material:
                materiality_basis = "both"
            elif imp_material:
                materiality_basis = "impact_only"
            elif fin_material:
                materiality_basis = "financial_only"
            else:
                materiality_basis = "neither"

            # Combined score: average of both dimensions, weighted by stakeholder salience
            combined_score = round(
                ((imp + fin) / 2) * (0.7 + 0.3 * stk / 100), 2
            )

            ranked.append(
                {
                    "topic_id": topic_id,
                    "topic_name": ESRS_TOPICS[topic_id]["name"],
                    "standard": ESRS_TOPICS[topic_id]["standard"],
                    "impact_score": round(imp, 2),
                    "financial_score": round(fin, 2),
                    "stakeholder_score": round(stk, 2),
                    "combined_score": combined_score,
                    "impact_material": imp_material,
                    "financial_material": fin_material,
                    "materiality_basis": materiality_basis,
                    "sector_typical": topic_id in SECTOR_MATERIALITY.get(sector, []),
                    "is_material": materiality_basis != "neither",
                }
            )

        ranked.sort(key=lambda x: x["combined_score"], reverse=True)
        for i, row in enumerate(ranked, start=1):
            row["priority_rank"] = i

        material_topics = [r for r in ranked if r["is_material"]]

        return {
            "entity_id": entity_id,
            "sector": sector,
            "total_topics_assessed": len(ranked),
            "material_topics_count": len(material_topics),
            "prioritised_topics": ranked,
            "top5_material_topics": [r["topic_id"] for r in ranked[:5]],
            "assessment_basis": "ESRS_1_section_49_topic_prioritisation",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 5. DMA Process Assessment
    # -----------------------------------------------------------------------

    def assess_dma_process(
        self,
        entity_id: str,
        process_data: dict,
    ) -> dict:
        """
        Assess completeness of the DMA process across 4 steps (25% each).

        Also derives applicable ESRS standards and assurance readiness.
        """
        rng = random.Random(hash(entity_id + "proc") & 0xFFFFFFFF)

        step_scores: dict[str, float] = {}
        for step in DMA_PROCESS_STEPS:
            step_scores[step] = float(
                process_data.get(f"{step}_score", rng.uniform(40, 95))
            )

        dma_process_completeness_pct = round(
            sum(step_scores.values()) / len(step_scores), 2
        )

        sector = process_data.get("sector", "financial_services")
        material_topics = process_data.get(
            "material_topics",
            SECTOR_MATERIALITY.get(sector, ["E1", "S1", "G1"]),
        )

        # Derive applicable ESRS standards
        esrs_standards_applicable = sorted(
            {ESRS_TOPICS[t]["standard"] for t in material_topics if t in ESRS_TOPICS}
        )

        # Assurance readiness — based on documentation and completeness
        documentation_score = float(
            process_data.get("documentation_score", rng.uniform(40, 90))
        )
        assurance_readiness_pct = round(
            (dma_process_completeness_pct * 0.6 + documentation_score * 0.4), 2
        )

        return {
            "entity_id": entity_id,
            "step_scores": {k: round(v, 2) for k, v in step_scores.items()},
            "dma_process_completeness_pct": dma_process_completeness_pct,
            "process_tier": (
                "advanced" if dma_process_completeness_pct >= 80
                else "developing" if dma_process_completeness_pct >= 60
                else "initial" if dma_process_completeness_pct >= 40
                else "not_started"
            ),
            "sector": sector,
            "material_topics": material_topics,
            "esrs_standards_applicable": esrs_standards_applicable,
            "documentation_score": round(documentation_score, 2),
            "assurance_readiness_pct": assurance_readiness_pct,
            "assessment_basis": "ESRS_1_sections_42_to_49",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 6. Full Assessment
    # -----------------------------------------------------------------------

    def full_assessment(
        self,
        entity_id: str,
        entity_name: str,
        sector: str,
        nace_code: str,
        reporting_period: str,
        full_data: dict,
    ) -> dict:
        """
        Comprehensive DMA covering both materiality dimensions, stakeholder
        engagement, topic prioritisation and process completeness.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        sector_topics = SECTOR_MATERIALITY.get(sector, ["E1", "S1", "G1"])
        all_topics = list(ESRS_TOPICS.keys())

        # Generate impact and financial scores for all topics
        impact_scores: dict[str, float] = {}
        financial_scores: dict[str, float] = {}
        stakeholder_scores_map: dict[str, float] = {}

        for t in all_topics:
            base = 65.0 if t in sector_topics else 35.0
            impact_scores[t] = round(base + rng.uniform(-15, 20), 2)
            financial_scores[t] = round(base + rng.uniform(-15, 20), 2)
            stakeholder_scores_map[t] = round(50.0 + rng.uniform(-10, 30), 2)

        # Override with any provided data
        impact_scores.update(full_data.get("impact_scores", {}))
        financial_scores.update(full_data.get("financial_scores", {}))
        stakeholder_scores_map.update(full_data.get("stakeholder_scores", {}))

        prioritisation = self.prioritise_topics(
            entity_id, sector, impact_scores, financial_scores, stakeholder_scores_map
        )

        stakeholder_result = self.run_stakeholder_engagement(
            entity_id, full_data.get("stakeholder_data", {})
        )

        process_result = self.assess_dma_process(
            entity_id,
            {
                "sector": sector,
                "material_topics": [
                    r["topic_id"]
                    for r in prioritisation["prioritised_topics"]
                    if r["is_material"]
                ],
                **full_data.get("process_data", {}),
            },
        )

        material_topics = [
            r for r in prioritisation["prioritised_topics"] if r["is_material"]
        ]

        overall_dma_score = round(
            (
                process_result["dma_process_completeness_pct"] * 0.4
                + stakeholder_result["engagement_quality_score"] * 0.3
                + min(100.0, len(material_topics) / len(all_topics) * 100) * 0.3
            ),
            2,
        )

        cross_framework = {
            "TCFD": CROSS_FRAMEWORK_MAP["TCFD"],
            "GRI_3": CROSS_FRAMEWORK_MAP["GRI_3"],
            "ISSB_S1": CROSS_FRAMEWORK_MAP["ISSB_S1"],
            "EU_Taxonomy": CROSS_FRAMEWORK_MAP["EU_Taxonomy"],
            "OECD_Guidelines": CROSS_FRAMEWORK_MAP["OECD_Guidelines"],
        }

        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "sector": sector,
            "nace_code": nace_code,
            "reporting_period": reporting_period,
            "assessment_standard": "ESRS_1_Double_Materiality",
            "overall_dma_score": overall_dma_score,
            "dma_tier": (
                "advanced" if overall_dma_score >= 75
                else "developing" if overall_dma_score >= 55
                else "initial"
            ),
            "material_topics_count": len(material_topics),
            "top_material_topics": prioritisation["top5_material_topics"],
            "esrs_standards_applicable": process_result["esrs_standards_applicable"],
            "impact_materiality": {
                "scores": impact_scores,
                "material_topics": [
                    r["topic_id"]
                    for r in prioritisation["prioritised_topics"]
                    if r["impact_material"]
                ],
            },
            "financial_materiality": {
                "scores": financial_scores,
                "material_topics": [
                    r["topic_id"]
                    for r in prioritisation["prioritised_topics"]
                    if r["financial_material"]
                ],
            },
            "stakeholder_engagement": stakeholder_result,
            "topic_prioritisation": prioritisation,
            "dma_process": process_result,
            "cross_framework": cross_framework,
            "sector_typical_material_topics": sector_topics,
            "assurance_readiness_pct": process_result["assurance_readiness_pct"],
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # Static reference methods
    # -----------------------------------------------------------------------

    @staticmethod
    def get_esrs_topics() -> dict:
        return ESRS_TOPICS

    @staticmethod
    def get_severity_criteria() -> dict:
        return SEVERITY_CRITERIA

    @staticmethod
    def get_financial_risk_types() -> dict:
        return FINANCIAL_RISK_TYPES

    @staticmethod
    def get_sector_materiality() -> dict:
        return SECTOR_MATERIALITY
