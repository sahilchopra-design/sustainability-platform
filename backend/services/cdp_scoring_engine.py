"""
CDP Climate & Water Scoring Engine
====================================
Comprehensive CDP (Carbon Disclosure Project) scoring engine for Climate Change
and Water Security questionnaires. Implements the four-level scoring methodology
(Disclosure, Awareness, Management, Leadership) and maps responses to letter
grades (A through D-).

Coverage:
  - 15 CDP Climate Change questionnaire modules (C0-C14)
  - 9 CDP Water Security questionnaire modules (W0-W8)
  - 4-level scoring methodology with weighted aggregation
  - 8 letter-grade bands (A, A-, B, B-, C, C-, D, D-)
  - 12 CDP Activity Group classifications
  - Cross-framework mapping to TCFD, GRI, ISSB S2, SASB
  - Peer benchmarking against activity group medians
  - SBTi alignment status check
  - Verification status tracking

References:
  - CDP Scoring Methodology 2024 (Climate Change & Water Security)
  - CDP Activity Classification System (ACS) 2023
  - TCFD Recommendations (2017) and Guidance (2021)
  - IFRS S2 Climate-related Disclosures (2023)
  - GRI 305: Emissions 2016
  - SASB Climate-related disclosure topics

API routes (planned):
  POST /api/v1/cdp/assess-climate
  POST /api/v1/cdp/assess-water
  POST /api/v1/cdp/compare-peers
  GET  /api/v1/cdp/climate-modules
  GET  /api/v1/cdp/water-modules
  GET  /api/v1/cdp/scoring-methodology
  GET  /api/v1/cdp/score-bands
  GET  /api/v1/cdp/activity-groups
  GET  /api/v1/cdp/cross-framework-map
  GET  /api/v1/cdp/peer-benchmarks
  GET  /api/v1/cdp/module-catalog
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("platform.cdp_scoring")


# ---------------------------------------------------------------------------
# CDP Climate Change Questionnaire Modules (C0-C14)
# ---------------------------------------------------------------------------

CDP_CLIMATE_MODULES = [
    {"code": "C0", "title": "Introduction", "category": "governance", "disclosures": 3},
    {"code": "C1", "title": "Governance", "category": "governance", "disclosures": 8},
    {"code": "C2", "title": "Risks and Opportunities", "category": "risks_opportunities", "disclosures": 6},
    {"code": "C3", "title": "Business Strategy", "category": "strategy", "disclosures": 5},
    {"code": "C4", "title": "Targets and Performance", "category": "targets", "disclosures": 7},
    {"code": "C5", "title": "Emissions Methodology", "category": "emissions", "disclosures": 3},
    {"code": "C6", "title": "Emissions Data", "category": "emissions", "disclosures": 10},
    {"code": "C7", "title": "Emissions Breakdowns", "category": "emissions", "disclosures": 5},
    {"code": "C8", "title": "Energy", "category": "energy", "disclosures": 4},
    {"code": "C9", "title": "Additional Metrics", "category": "performance", "disclosures": 2},
    {"code": "C10", "title": "Verification", "category": "assurance", "disclosures": 3},
    {"code": "C11", "title": "Carbon Pricing", "category": "strategy", "disclosures": 4},
    {"code": "C12", "title": "Engagement", "category": "engagement", "disclosures": 5},
    {"code": "C13", "title": "Other Land Management Impacts", "category": "land_use", "disclosures": 2},
    {"code": "C14", "title": "Signoff", "category": "governance", "disclosures": 1},
]

# ---------------------------------------------------------------------------
# CDP Water Security Questionnaire Modules (W0-W8)
# ---------------------------------------------------------------------------

CDP_WATER_MODULES = [
    {"code": "W0", "title": "Introduction", "category": "governance", "disclosures": 3},
    {"code": "W1", "title": "Current State", "category": "context", "disclosures": 5},
    {"code": "W2", "title": "Business Impacts", "category": "risks", "disclosures": 4},
    {"code": "W3", "title": "Procedures", "category": "management", "disclosures": 5},
    {"code": "W4", "title": "Risks and Opportunities", "category": "risks_opportunities", "disclosures": 6},
    {"code": "W5", "title": "Facility-Level Water Accounting", "category": "performance", "disclosures": 3},
    {"code": "W6", "title": "Governance", "category": "governance", "disclosures": 6},
    {"code": "W7", "title": "Business Strategy", "category": "strategy", "disclosures": 4},
    {"code": "W8", "title": "Targets", "category": "targets", "disclosures": 3},
]

# ---------------------------------------------------------------------------
# CDP Scoring Methodology — 4 Levels
# ---------------------------------------------------------------------------

CDP_SCORING_METHODOLOGY = {
    "disclosure": {
        "label": "Disclosure",
        "weight": 0.25,
        "description": "Completeness and quality of information provided",
        "min_score_for_level": 0,
    },
    "awareness": {
        "label": "Awareness",
        "weight": 0.25,
        "description": "Evidence of understanding environmental issues",
        "min_score_for_level": 30,
    },
    "management": {
        "label": "Management",
        "weight": 0.25,
        "description": "Evidence of actions to address environmental issues",
        "min_score_for_level": 50,
    },
    "leadership": {
        "label": "Leadership",
        "weight": 0.25,
        "description": "Evidence of best practice and leadership",
        "min_score_for_level": 75,
    },
}

# ---------------------------------------------------------------------------
# CDP Score Bands — Letter Grades A through D-
# ---------------------------------------------------------------------------

CDP_SCORE_BANDS = [
    {"grade": "A", "label": "Leadership", "min_pct": 80, "description": "Best practice environmental stewardship"},
    {"grade": "A-", "label": "Leadership", "min_pct": 70, "description": "Implementing current best practices"},
    {"grade": "B", "label": "Management", "min_pct": 60, "description": "Taking coordinated action on climate"},
    {"grade": "B-", "label": "Management", "min_pct": 50, "description": "Managing environmental impact"},
    {"grade": "C", "label": "Awareness", "min_pct": 40, "description": "Knowledge of environmental impact"},
    {"grade": "C-", "label": "Awareness", "min_pct": 30, "description": "Some awareness of environmental impact"},
    {"grade": "D", "label": "Disclosure", "min_pct": 10, "description": "Incomplete disclosure"},
    {"grade": "D-", "label": "Disclosure", "min_pct": 0, "description": "Minimum disclosure"},
]

# ---------------------------------------------------------------------------
# CDP Activity Group Classifications
# ---------------------------------------------------------------------------

CDP_ACTIVITY_GROUPS = [
    {"code": "AG01", "name": "Financial Services", "sectors": ["Banking", "Insurance", "Investment Management"]},
    {"code": "AG02", "name": "Fossil Fuels", "sectors": ["Oil & Gas", "Coal"]},
    {"code": "AG03", "name": "Power Generation", "sectors": ["Electric Utilities", "Independent Power"]},
    {"code": "AG04", "name": "Transport", "sectors": ["Airlines", "Shipping", "Road Transport", "Rail"]},
    {"code": "AG05", "name": "Materials", "sectors": ["Cement", "Steel", "Chemicals", "Paper"]},
    {"code": "AG06", "name": "Agriculture & Food", "sectors": ["Agriculture", "Food & Beverage", "Tobacco"]},
    {"code": "AG07", "name": "Real Estate", "sectors": ["REIT", "Real Estate Management", "Construction"]},
    {"code": "AG08", "name": "Technology", "sectors": ["Hardware", "Software", "Semiconductors", "Telecoms"]},
    {"code": "AG09", "name": "Consumer Goods", "sectors": ["Retail", "Apparel", "Personal Care"]},
    {"code": "AG10", "name": "Healthcare", "sectors": ["Pharmaceuticals", "Medical Equipment", "Healthcare Providers"]},
    {"code": "AG11", "name": "Infrastructure", "sectors": ["Water Utilities", "Waste Management", "Diversified Infrastructure"]},
    {"code": "AG12", "name": "Mining & Metals", "sectors": ["Mining", "Metals & Steel"]},
]

# ---------------------------------------------------------------------------
# Cross-Framework Mapping — CDP modules to TCFD / GRI / ISSB S2 / SASB
# ---------------------------------------------------------------------------

CDP_CROSS_FRAMEWORK_MAP = [
    {
        "cdp_module": "C1",
        "cdp_title": "Governance",
        "tcfd": "Governance a) and b)",
        "gri": "GRI 2-9 to 2-21 (Governance)",
        "issb_s2": "IFRS S2 para 5-6 (Governance)",
        "sasb": "—",
    },
    {
        "cdp_module": "C2",
        "cdp_title": "Risks and Opportunities",
        "tcfd": "Strategy a) and Risk Management a)",
        "gri": "GRI 201-2 (Financial implications of climate change)",
        "issb_s2": "IFRS S2 para 10-12 (Climate-related risks and opportunities)",
        "sasb": "Industry-specific risk topics",
    },
    {
        "cdp_module": "C3",
        "cdp_title": "Business Strategy",
        "tcfd": "Strategy b) and c)",
        "gri": "GRI 2-22 (Strategy), GRI 201-2",
        "issb_s2": "IFRS S2 para 13-22 (Strategy — business model, value chain, resilience)",
        "sasb": "—",
    },
    {
        "cdp_module": "C4",
        "cdp_title": "Targets and Performance",
        "tcfd": "Metrics and Targets a) and b)",
        "gri": "GRI 305-5 (Reduction of GHG emissions)",
        "issb_s2": "IFRS S2 para 33-36 (Climate-related targets)",
        "sasb": "Industry-specific performance metrics",
    },
    {
        "cdp_module": "C6",
        "cdp_title": "Emissions Data",
        "tcfd": "Metrics and Targets a)",
        "gri": "GRI 305-1 to 305-4 (Scope 1/2/3 emissions, intensity)",
        "issb_s2": "IFRS S2 para 29 (Scope 1/2/3 GHG emissions)",
        "sasb": "GHG Emissions (cross-industry metric EM-xxx)",
    },
    {
        "cdp_module": "C7",
        "cdp_title": "Emissions Breakdowns",
        "tcfd": "Metrics and Targets a)",
        "gri": "GRI 305-1 to 305-3 (breakdown by source/category)",
        "issb_s2": "IFRS S2 para 29(a) (disaggregated disclosures)",
        "sasb": "Industry-specific emissions breakdowns",
    },
    {
        "cdp_module": "C8",
        "cdp_title": "Energy",
        "tcfd": "Metrics and Targets a)",
        "gri": "GRI 302-1 to 302-5 (Energy)",
        "issb_s2": "IFRS S2 Appendix B (energy consumption metrics)",
        "sasb": "Energy Management (IF-EU-000.D, etc.)",
    },
    {
        "cdp_module": "C10",
        "cdp_title": "Verification",
        "tcfd": "—",
        "gri": "GRI 2-5 (External assurance)",
        "issb_s2": "IFRS S2 para 29(a)(vi) — verification of Scope 1/2",
        "sasb": "—",
    },
    {
        "cdp_module": "C11",
        "cdp_title": "Carbon Pricing",
        "tcfd": "Strategy b) — financial planning, carbon price assumptions",
        "gri": "GRI 201-2 (Financial implications, incl. carbon costs)",
        "issb_s2": "IFRS S2 para 22 (Resilience — scenario assumptions incl. carbon price)",
        "sasb": "—",
    },
    {
        "cdp_module": "C12",
        "cdp_title": "Engagement",
        "tcfd": "Strategy b) — value chain engagement",
        "gri": "GRI 308 (Supplier environmental assessment), GRI 2-29 (Stakeholder engagement)",
        "issb_s2": "IFRS S2 para 29(a)(vi)(2) — Scope 3 value chain engagement",
        "sasb": "Industry-specific supply chain topics",
    },
]

# ---------------------------------------------------------------------------
# Peer Benchmark Medians by Activity Group
# ---------------------------------------------------------------------------

CDP_PEER_BENCHMARK_MEDIANS = [
    {
        "activity_group": "AG01",
        "median_score_pct": 58.0,
        "median_grade": "B-",
        "avg_disclosure_pct": 72.0,
        "avg_scope12_verified_pct": 65.0,
        "avg_target_coverage_pct": 55.0,
    },
    {
        "activity_group": "AG02",
        "median_score_pct": 52.0,
        "median_grade": "B-",
        "avg_disclosure_pct": 68.0,
        "avg_scope12_verified_pct": 70.0,
        "avg_target_coverage_pct": 48.0,
    },
    {
        "activity_group": "AG03",
        "median_score_pct": 55.0,
        "median_grade": "B-",
        "avg_disclosure_pct": 70.0,
        "avg_scope12_verified_pct": 72.0,
        "avg_target_coverage_pct": 52.0,
    },
    {
        "activity_group": "AG05",
        "median_score_pct": 48.0,
        "median_grade": "C",
        "avg_disclosure_pct": 64.0,
        "avg_scope12_verified_pct": 58.0,
        "avg_target_coverage_pct": 40.0,
    },
    {
        "activity_group": "AG08",
        "median_score_pct": 62.0,
        "median_grade": "B",
        "avg_disclosure_pct": 76.0,
        "avg_scope12_verified_pct": 60.0,
        "avg_target_coverage_pct": 58.0,
    },
    {
        "activity_group": "AG12",
        "median_score_pct": 45.0,
        "median_grade": "C",
        "avg_disclosure_pct": 60.0,
        "avg_scope12_verified_pct": 55.0,
        "avg_target_coverage_pct": 35.0,
    },
]

# Lookup dict for fast peer lookups
_PEER_BENCHMARK_BY_AG: dict[str, dict] = {
    b["activity_group"]: b for b in CDP_PEER_BENCHMARK_MEDIANS
}

# ---------------------------------------------------------------------------
# Module-Level Scoring Weights by Category
# ---------------------------------------------------------------------------

_CATEGORY_SCORING_WEIGHTS: dict[str, dict[str, float]] = {
    "governance": {"disclosure": 0.40, "awareness": 0.30, "management": 0.20, "leadership": 0.10},
    "risks_opportunities": {"disclosure": 0.20, "awareness": 0.30, "management": 0.30, "leadership": 0.20},
    "strategy": {"disclosure": 0.20, "awareness": 0.25, "management": 0.30, "leadership": 0.25},
    "targets": {"disclosure": 0.15, "awareness": 0.20, "management": 0.30, "leadership": 0.35},
    "emissions": {"disclosure": 0.35, "awareness": 0.25, "management": 0.25, "leadership": 0.15},
    "energy": {"disclosure": 0.30, "awareness": 0.25, "management": 0.25, "leadership": 0.20},
    "performance": {"disclosure": 0.30, "awareness": 0.30, "management": 0.25, "leadership": 0.15},
    "assurance": {"disclosure": 0.25, "awareness": 0.20, "management": 0.30, "leadership": 0.25},
    "engagement": {"disclosure": 0.20, "awareness": 0.25, "management": 0.30, "leadership": 0.25},
    "land_use": {"disclosure": 0.35, "awareness": 0.30, "management": 0.25, "leadership": 0.10},
    "context": {"disclosure": 0.35, "awareness": 0.30, "management": 0.25, "leadership": 0.10},
    "risks": {"disclosure": 0.20, "awareness": 0.30, "management": 0.30, "leadership": 0.20},
    "management": {"disclosure": 0.20, "awareness": 0.20, "management": 0.35, "leadership": 0.25},
}


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CDPModuleScore:
    """Score result for a single CDP questionnaire module."""
    module_code: str
    module_title: str
    category: str
    disclosure_score: float  # 0-100
    awareness_score: float
    management_score: float
    leadership_score: float
    overall_score: float
    status: str  # "complete", "partial", "not_disclosed"


@dataclass
class CDPClimateAssessment:
    """Full CDP Climate Change questionnaire assessment result."""
    id: str
    entity_name: str
    reporting_year: int
    questionnaire: str  # "climate"
    overall_score_pct: float
    grade: str  # A to D-
    grade_label: str  # Leadership / Management / Awareness / Disclosure
    module_scores: list  # list of CDPModuleScore dicts
    scoring_breakdown: dict  # disclosure / awareness / management / leadership percentages
    activity_group: str
    verification_status: dict
    sbti_alignment: dict
    cross_framework_mapping: dict
    peer_comparison: dict
    gaps: list
    recommendations: list
    created_at: str


@dataclass
class CDPWaterAssessment:
    """Full CDP Water Security questionnaire assessment result."""
    id: str
    entity_name: str
    reporting_year: int
    overall_score_pct: float
    grade: str
    grade_label: str
    module_scores: list
    water_risk_exposure: dict
    facility_water_accounting: dict
    cross_framework_mapping: dict
    gaps: list
    recommendations: list
    created_at: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CDPScoringEngine:
    """CDP Climate Change & Water Security scoring engine.

    Implements the CDP four-level scoring methodology across all questionnaire
    modules and produces letter-grade assessments with peer comparison,
    cross-framework mapping, gap analysis, and improvement recommendations.
    """

    # ── Climate Change Assessment ─────────────────────────────────────────

    def assess_climate(
        self,
        entity_name: str,
        reporting_year: int,
        activity_group: str | None = None,
        responses: dict | None = None,
    ) -> CDPClimateAssessment:
        """Score the CDP Climate Change questionnaire for an entity.

        Args:
            entity_name: Legal name of the reporting entity.
            reporting_year: The CDP reporting cycle year (e.g. 2025).
            activity_group: CDP Activity Group code (e.g. "AG01"). If None,
                defaults to "AG08" (Technology).
            responses: Optional dict keyed by module code (e.g. "C1") with
                sub-keys per scoring level:
                  {"C1": {"disclosure": 80, "awareness": 65, ...}, ...}
                Values are 0-100 scores. Missing modules default to 0.

        Returns:
            CDPClimateAssessment with module scores, grade, peer comparison,
            gaps, and recommendations.
        """
        responses = responses or {}
        activity_group = activity_group or "AG08"

        uid = hashlib.sha256(
            f"cdp-climate:{entity_name}:{reporting_year}".encode()
        ).hexdigest()[:16]

        # Score each module
        module_scores: list[dict] = []
        level_sums = {"disclosure": 0.0, "awareness": 0.0, "management": 0.0, "leadership": 0.0}
        module_count = len(CDP_CLIMATE_MODULES)

        for mod in CDP_CLIMATE_MODULES:
            code = mod["code"]
            category = mod["category"]
            resp = responses.get(code, {})
            ms = self._score_module(code, mod["title"], category, resp)
            module_scores.append({
                "module_code": ms.module_code,
                "module_title": ms.module_title,
                "category": ms.category,
                "disclosure_score": ms.disclosure_score,
                "awareness_score": ms.awareness_score,
                "management_score": ms.management_score,
                "leadership_score": ms.leadership_score,
                "overall_score": ms.overall_score,
                "status": ms.status,
            })
            level_sums["disclosure"] += ms.disclosure_score
            level_sums["awareness"] += ms.awareness_score
            level_sums["management"] += ms.management_score
            level_sums["leadership"] += ms.leadership_score

        # Aggregate scoring breakdown (average across modules)
        scoring_breakdown = {
            level: round(level_sums[level] / module_count, 1) if module_count > 0 else 0.0
            for level in level_sums
        }

        # Overall score: weighted average of the four levels
        overall_pct = sum(
            scoring_breakdown[level] * CDP_SCORING_METHODOLOGY[level]["weight"]
            for level in scoring_breakdown
        )
        overall_pct = round(overall_pct, 1)

        # Determine grade
        grade, grade_label = self._pct_to_grade(overall_pct)

        # Verification status from C10 response
        c10_resp = responses.get("C10", {})
        verification_status = {
            "scope_1_verified": c10_resp.get("disclosure", 0) >= 50,
            "scope_2_verified": c10_resp.get("disclosure", 0) >= 50,
            "scope_3_verified": c10_resp.get("awareness", 0) >= 40,
            "verification_standard": "ISO 14064-3" if c10_resp.get("disclosure", 0) >= 50 else "not_verified",
            "assurance_level": "limited" if c10_resp.get("management", 0) >= 50 else "none",
        }

        # SBTi alignment from C4 response
        c4_resp = responses.get("C4", {})
        sbti_alignment = {
            "has_sbti_target": c4_resp.get("management", 0) >= 60,
            "target_status": "approved" if c4_resp.get("management", 0) >= 70 else (
                "committed" if c4_resp.get("management", 0) >= 50 else "no_target"
            ),
            "near_term_target": c4_resp.get("leadership", 0) >= 60,
            "net_zero_target": c4_resp.get("leadership", 0) >= 75,
            "target_coverage_pct": min(c4_resp.get("management", 0) * 1.2, 100),
        }

        # Cross-framework mapping (filter to relevant modules with responses)
        responded_modules = {m["module_code"] for m in module_scores if m["status"] != "not_disclosed"}
        xfw = {
            "mappings": [
                cfm for cfm in CDP_CROSS_FRAMEWORK_MAP
                if cfm["cdp_module"] in responded_modules
            ],
            "total_mapped": len([
                cfm for cfm in CDP_CROSS_FRAMEWORK_MAP
                if cfm["cdp_module"] in responded_modules
            ]),
            "total_available": len(CDP_CROSS_FRAMEWORK_MAP),
        }

        # Peer comparison
        peer_comparison = self.compare_to_peers(entity_name, activity_group, overall_pct)

        # Gap analysis
        gaps = self._identify_climate_gaps(module_scores, verification_status, sbti_alignment)

        # Recommendations
        recommendations = self._generate_climate_recommendations(
            grade, scoring_breakdown, gaps, sbti_alignment, verification_status
        )

        return CDPClimateAssessment(
            id=f"cdp-clim-{uid}",
            entity_name=entity_name,
            reporting_year=reporting_year,
            questionnaire="climate",
            overall_score_pct=overall_pct,
            grade=grade,
            grade_label=grade_label,
            module_scores=module_scores,
            scoring_breakdown=scoring_breakdown,
            activity_group=activity_group,
            verification_status=verification_status,
            sbti_alignment=sbti_alignment,
            cross_framework_mapping=xfw,
            peer_comparison=peer_comparison,
            gaps=gaps,
            recommendations=recommendations,
            created_at=datetime.utcnow().isoformat(),
        )

    # ── Water Security Assessment ─────────────────────────────────────────

    def assess_water(
        self,
        entity_name: str,
        reporting_year: int,
        responses: dict | None = None,
    ) -> CDPWaterAssessment:
        """Score the CDP Water Security questionnaire for an entity.

        Args:
            entity_name: Legal name of the reporting entity.
            reporting_year: The CDP reporting cycle year.
            responses: Optional dict keyed by module code (e.g. "W1") with
                sub-keys per scoring level. Missing modules default to 0.

        Returns:
            CDPWaterAssessment with module scores, grade, water risk profile,
            gaps, and recommendations.
        """
        responses = responses or {}

        uid = hashlib.sha256(
            f"cdp-water:{entity_name}:{reporting_year}".encode()
        ).hexdigest()[:16]

        # Score each module
        module_scores: list[dict] = []
        level_sums = {"disclosure": 0.0, "awareness": 0.0, "management": 0.0, "leadership": 0.0}
        module_count = len(CDP_WATER_MODULES)

        for mod in CDP_WATER_MODULES:
            code = mod["code"]
            category = mod["category"]
            resp = responses.get(code, {})
            ms = self._score_module(code, mod["title"], category, resp)
            module_scores.append({
                "module_code": ms.module_code,
                "module_title": ms.module_title,
                "category": ms.category,
                "disclosure_score": ms.disclosure_score,
                "awareness_score": ms.awareness_score,
                "management_score": ms.management_score,
                "leadership_score": ms.leadership_score,
                "overall_score": ms.overall_score,
                "status": ms.status,
            })
            level_sums["disclosure"] += ms.disclosure_score
            level_sums["awareness"] += ms.awareness_score
            level_sums["management"] += ms.management_score
            level_sums["leadership"] += ms.leadership_score

        # Aggregate
        scoring_breakdown = {
            level: round(level_sums[level] / module_count, 1) if module_count > 0 else 0.0
            for level in level_sums
        }
        overall_pct = sum(
            scoring_breakdown[level] * CDP_SCORING_METHODOLOGY[level]["weight"]
            for level in scoring_breakdown
        )
        overall_pct = round(overall_pct, 1)

        grade, grade_label = self._pct_to_grade(overall_pct)

        # Water risk exposure profile (derived from W1 and W2 responses)
        w1_resp = responses.get("W1", {})
        w2_resp = responses.get("W2", {})
        water_risk_exposure = {
            "overall_risk_level": self._water_risk_level(w1_resp, w2_resp),
            "water_stressed_operations_pct": min(w1_resp.get("awareness", 0) * 0.8, 100),
            "revenue_at_risk_pct": min(w2_resp.get("awareness", 0) * 0.5, 100),
            "substantive_financial_impact": w2_resp.get("management", 0) >= 50,
            "watershed_risk_assessed": w1_resp.get("management", 0) >= 40,
        }

        # Facility-level water accounting (derived from W5 response)
        w5_resp = responses.get("W5", {})
        facility_water_accounting = {
            "facility_level_data_available": w5_resp.get("disclosure", 0) >= 50,
            "facilities_in_water_stress": w5_resp.get("awareness", 0) >= 40,
            "withdrawal_metered_pct": min(w5_resp.get("management", 0) * 1.1, 100),
            "discharge_quality_monitored": w5_resp.get("management", 0) >= 60,
            "water_recycling_rate_pct": min(w5_resp.get("leadership", 0) * 0.8, 100),
        }

        # Cross-framework mapping (water-specific subset)
        xfw = {
            "mappings": [
                {"cdp_module": "W1", "gri": "GRI 303-3 (Water withdrawal)", "issb_s2": "IFRS S2 physical risk — water scarcity"},
                {"cdp_module": "W2", "gri": "GRI 303-4/5 (Water discharge/consumption)", "issb_s2": "IFRS S2 para 10 — physical risks"},
                {"cdp_module": "W4", "gri": "GRI 201-2 (Financial implications)", "issb_s2": "IFRS S2 para 10-12 (Risks & Opportunities)"},
                {"cdp_module": "W6", "gri": "GRI 2-12 to 2-21 (Governance)", "issb_s2": "IFRS S2 para 5-6 (Governance)"},
                {"cdp_module": "W8", "gri": "GRI 303-1 (Water interactions)", "issb_s2": "IFRS S2 para 33-36 (Targets)"},
            ],
            "total_mapped": 5,
        }

        # Gap analysis
        gaps = self._identify_water_gaps(module_scores, water_risk_exposure, facility_water_accounting)

        # Recommendations
        recommendations = self._generate_water_recommendations(
            grade, scoring_breakdown, gaps, water_risk_exposure
        )

        return CDPWaterAssessment(
            id=f"cdp-wtr-{uid}",
            entity_name=entity_name,
            reporting_year=reporting_year,
            overall_score_pct=overall_pct,
            grade=grade,
            grade_label=grade_label,
            module_scores=module_scores,
            water_risk_exposure=water_risk_exposure,
            facility_water_accounting=facility_water_accounting,
            cross_framework_mapping=xfw,
            gaps=gaps,
            recommendations=recommendations,
            created_at=datetime.utcnow().isoformat(),
        )

    # ── Peer Comparison ───────────────────────────────────────────────────

    def compare_to_peers(
        self,
        entity_name: str,
        activity_group: str,
        entity_score_pct: float,
    ) -> dict:
        """Compare an entity's CDP score against activity group median benchmarks.

        Args:
            entity_name: Legal name of the entity.
            activity_group: CDP Activity Group code (e.g. "AG01").
            entity_score_pct: The entity's overall score percentage.

        Returns:
            Dict with rank_label, delta_vs_median, peer benchmark details.
        """
        benchmark = _PEER_BENCHMARK_BY_AG.get(activity_group)

        if not benchmark:
            # If no benchmark data exists for this activity group, return limited info
            ag_info = next((ag for ag in CDP_ACTIVITY_GROUPS if ag["code"] == activity_group), None)
            return {
                "entity_name": entity_name,
                "activity_group": activity_group,
                "activity_group_name": ag_info["name"] if ag_info else "Unknown",
                "entity_score_pct": entity_score_pct,
                "benchmark_available": False,
                "rank_label": "no_benchmark_data",
                "note": f"No peer benchmark data available for activity group {activity_group}",
            }

        median = benchmark["median_score_pct"]
        delta = round(entity_score_pct - median, 1)

        if delta > 5:
            rank_label = "above_median"
        elif delta >= -5:
            rank_label = "at_median"
        else:
            rank_label = "below_median"

        ag_info = next((ag for ag in CDP_ACTIVITY_GROUPS if ag["code"] == activity_group), None)

        return {
            "entity_name": entity_name,
            "activity_group": activity_group,
            "activity_group_name": ag_info["name"] if ag_info else "Unknown",
            "entity_score_pct": entity_score_pct,
            "benchmark_available": True,
            "median_score_pct": median,
            "median_grade": benchmark["median_grade"],
            "delta_vs_median": delta,
            "rank_label": rank_label,
            "peer_avg_disclosure_pct": benchmark["avg_disclosure_pct"],
            "peer_avg_scope12_verified_pct": benchmark["avg_scope12_verified_pct"],
            "peer_avg_target_coverage_pct": benchmark["avg_target_coverage_pct"],
        }

    # ── Internal Scoring Helpers ──────────────────────────────────────────

    def _score_module(
        self,
        code: str,
        title: str,
        category: str,
        resp: dict,
    ) -> CDPModuleScore:
        """Score a single questionnaire module across all four levels."""
        disc = float(resp.get("disclosure", 0))
        awar = float(resp.get("awareness", 0))
        mgmt = float(resp.get("management", 0))
        lead = float(resp.get("leadership", 0))

        # Clamp to 0-100
        disc = max(0.0, min(100.0, disc))
        awar = max(0.0, min(100.0, awar))
        mgmt = max(0.0, min(100.0, mgmt))
        lead = max(0.0, min(100.0, lead))

        # Weighted overall for this module using category-specific weights
        cat_weights = _CATEGORY_SCORING_WEIGHTS.get(category, {
            "disclosure": 0.25, "awareness": 0.25, "management": 0.25, "leadership": 0.25,
        })
        overall = (
            disc * cat_weights["disclosure"]
            + awar * cat_weights["awareness"]
            + mgmt * cat_weights["management"]
            + lead * cat_weights["leadership"]
        )
        overall = round(overall, 1)

        # Determine status
        total_input = disc + awar + mgmt + lead
        if total_input == 0:
            status = "not_disclosed"
        elif disc < 30 or overall < 20:
            status = "partial"
        else:
            status = "complete"

        return CDPModuleScore(
            module_code=code,
            module_title=title,
            category=category,
            disclosure_score=round(disc, 1),
            awareness_score=round(awar, 1),
            management_score=round(mgmt, 1),
            leadership_score=round(lead, 1),
            overall_score=overall,
            status=status,
        )

    @staticmethod
    def _pct_to_grade(pct: float) -> tuple[str, str]:
        """Convert a percentage score to a CDP letter grade and label."""
        for band in CDP_SCORE_BANDS:
            if pct >= band["min_pct"]:
                return band["grade"], band["label"]
        return "D-", "Disclosure"

    @staticmethod
    def _water_risk_level(w1_resp: dict, w2_resp: dict) -> str:
        """Derive overall water risk level from W1 and W2 module responses."""
        avg = (
            w1_resp.get("awareness", 0) * 0.4
            + w2_resp.get("awareness", 0) * 0.3
            + w2_resp.get("management", 0) * 0.3
        )
        if avg >= 70:
            return "high"
        elif avg >= 40:
            return "medium"
        else:
            return "low"

    # ── Gap Analysis ──────────────────────────────────────────────────────

    @staticmethod
    def _identify_climate_gaps(
        module_scores: list[dict],
        verification_status: dict,
        sbti_alignment: dict,
    ) -> list[str]:
        """Identify disclosure and performance gaps in climate assessment."""
        gaps = []

        # Module-level gaps
        not_disclosed = [m for m in module_scores if m["status"] == "not_disclosed"]
        partial = [m for m in module_scores if m["status"] == "partial"]

        for m in not_disclosed:
            gaps.append(f"{m['module_code']} ({m['module_title']}): Not disclosed — "
                        f"entire module missing")
        for m in partial:
            if m["disclosure_score"] < 30:
                gaps.append(f"{m['module_code']} ({m['module_title']}): Disclosure score "
                            f"{m['disclosure_score']}% — below minimum threshold for Awareness level")

        # Emissions-specific gaps
        emissions_modules = [m for m in module_scores if m["category"] == "emissions"]
        for em in emissions_modules:
            if em["status"] == "not_disclosed":
                gaps.append(f"Critical: {em['module_code']} ({em['module_title']}) — "
                            f"emissions data not disclosed; will cap score at D band")

        # Verification gaps
        if not verification_status.get("scope_1_verified"):
            gaps.append("C10: Scope 1 emissions not third-party verified — "
                        "required for A/A- grade")
        if not verification_status.get("scope_2_verified"):
            gaps.append("C10: Scope 2 emissions not third-party verified — "
                        "required for A/A- grade")

        # Target gaps
        if not sbti_alignment.get("has_sbti_target"):
            gaps.append("C4: No science-based target set — "
                        "SBTi-approved target required for Leadership band")
        if not sbti_alignment.get("net_zero_target"):
            gaps.append("C4: No net-zero target — "
                        "net-zero commitment increasingly expected by investors and CDP")

        return gaps

    @staticmethod
    def _identify_water_gaps(
        module_scores: list[dict],
        water_risk: dict,
        facility_accounting: dict,
    ) -> list[str]:
        """Identify disclosure and performance gaps in water assessment."""
        gaps = []

        not_disclosed = [m for m in module_scores if m["status"] == "not_disclosed"]
        for m in not_disclosed:
            gaps.append(f"{m['module_code']} ({m['module_title']}): Not disclosed")

        if not facility_accounting.get("facility_level_data_available"):
            gaps.append("W5: Facility-level water data not available — "
                        "required for Management level and above")
        if not facility_accounting.get("discharge_quality_monitored"):
            gaps.append("W5: Water discharge quality not monitored — "
                        "essential for demonstrating responsible water management")
        if water_risk.get("overall_risk_level") == "high" and not water_risk.get("watershed_risk_assessed"):
            gaps.append("W1: High water risk exposure but watershed-level risk assessment "
                        "not conducted — critical gap for water-stressed operations")
        if not water_risk.get("substantive_financial_impact"):
            gaps.append("W2: Substantive financial impact of water risks not quantified — "
                        "increasingly required by investors and TCFD/ISSB")

        return gaps

    # ── Recommendations ───────────────────────────────────────────────────

    @staticmethod
    def _generate_climate_recommendations(
        grade: str,
        scoring_breakdown: dict,
        gaps: list[str],
        sbti_alignment: dict,
        verification_status: dict,
    ) -> list[str]:
        """Generate prioritised improvement recommendations for climate score."""
        recs = []

        # Grade-specific pathway
        if grade in ("D", "D-"):
            recs.append("Priority: Complete all core disclosure modules (C0-C8, C14) to move "
                        "from Disclosure to Awareness band")
            recs.append("Establish board-level climate governance (C1) and conduct a climate "
                        "risk and opportunity assessment (C2)")
        elif grade in ("C", "C-"):
            recs.append("To reach Management band: set quantified emissions reduction targets (C4) "
                        "and implement a transition plan aligned with Paris Agreement")
            recs.append("Obtain third-party verification of Scope 1 and Scope 2 emissions (C10)")
        elif grade in ("B", "B-"):
            recs.append("To reach Leadership band: achieve SBTi-approved near-term and net-zero "
                        "targets, obtain limited assurance on all scope emissions")
            recs.append("Demonstrate supply chain engagement (C12) covering at least 70% of "
                        "Scope 3 emissions by category")
        elif grade in ("A-",):
            recs.append("To reach A grade: demonstrate best-practice leadership across all modules "
                        "with full verification, net-zero pathway, and value chain engagement")

        # Level-specific improvements
        if scoring_breakdown.get("disclosure", 0) < 60:
            recs.append("Disclosure gap: increase completeness of responses — target 80%+ "
                        "disclosure score across all modules")
        if scoring_breakdown.get("awareness", 0) < 50:
            recs.append("Awareness gap: demonstrate understanding of climate risks via "
                        "scenario analysis (C3) and risk quantification (C2)")
        if scoring_breakdown.get("management", 0) < 50:
            recs.append("Management gap: implement emissions reduction initiatives and "
                        "integrate climate into business strategy (C3, C4)")
        if scoring_breakdown.get("leadership", 0) < 40:
            recs.append("Leadership gap: adopt best practices including internal carbon pricing (C11), "
                        "full value chain engagement (C12), and verified SBTi targets (C4)")

        # Specific action items
        if not verification_status.get("scope_1_verified"):
            recs.append("Action: engage an accredited verification body (e.g. ISO 14064-3) "
                        "for Scope 1 and Scope 2 emissions")
        if not sbti_alignment.get("has_sbti_target"):
            recs.append("Action: commit to the Science Based Targets initiative and submit "
                        "targets for validation within 24 months")
        if not sbti_alignment.get("net_zero_target"):
            recs.append("Action: develop a credible net-zero transition plan aligned with "
                        "SBTi Net-Zero Standard or GFANZ guidance")

        # Cap at reasonable number
        return recs[:10]

    @staticmethod
    def _generate_water_recommendations(
        grade: str,
        scoring_breakdown: dict,
        gaps: list[str],
        water_risk: dict,
    ) -> list[str]:
        """Generate prioritised improvement recommendations for water score."""
        recs = []

        if grade in ("D", "D-"):
            recs.append("Priority: Complete core disclosure modules (W0-W3, W6) to move "
                        "from Disclosure to Awareness band")
            recs.append("Conduct a company-wide water risk assessment using tools such as "
                        "WRI Aqueduct or WWF Water Risk Filter")
        elif grade in ("C", "C-"):
            recs.append("To reach Management band: implement facility-level water accounting (W5) "
                        "and set context-based water targets (W8)")
            recs.append("Quantify the financial impact of water risks (W2) and integrate "
                        "water risk into enterprise risk management")
        elif grade in ("B", "B-"):
            recs.append("To reach Leadership band: implement water stewardship programmes in "
                        "water-stressed basins and demonstrate measurable outcomes")
            recs.append("Achieve third-party assurance on water withdrawal and discharge data")

        if water_risk.get("overall_risk_level") == "high":
            recs.append("High water risk: prioritise water efficiency investments in "
                        "water-stressed facilities and engage basin-level collective action")
        if scoring_breakdown.get("disclosure", 0) < 60:
            recs.append("Disclosure gap: increase completeness of water security responses "
                        "to at least 80% across all modules")
        if scoring_breakdown.get("management", 0) < 50:
            recs.append("Management gap: implement water reduction targets and track "
                        "progress against context-based water goals")

        return recs[:8]

    # ── Static Reference Methods ──────────────────────────────────────────

    @staticmethod
    def get_climate_modules() -> list[dict]:
        """Return all 15 CDP Climate Change questionnaire modules."""
        return CDP_CLIMATE_MODULES

    @staticmethod
    def get_water_modules() -> list[dict]:
        """Return all 9 CDP Water Security questionnaire modules."""
        return CDP_WATER_MODULES

    @staticmethod
    def get_scoring_methodology() -> dict:
        """Return the CDP four-level scoring methodology."""
        return CDP_SCORING_METHODOLOGY

    @staticmethod
    def get_score_bands() -> list[dict]:
        """Return all CDP letter-grade score bands (A through D-)."""
        return CDP_SCORE_BANDS

    @staticmethod
    def get_activity_groups() -> list[dict]:
        """Return all 12 CDP Activity Group classifications."""
        return CDP_ACTIVITY_GROUPS

    @staticmethod
    def get_cross_framework_map() -> list[dict]:
        """Return CDP-to-TCFD/GRI/ISSB/SASB cross-framework mapping."""
        return CDP_CROSS_FRAMEWORK_MAP

    @staticmethod
    def get_peer_benchmarks() -> list[dict]:
        """Return activity group peer benchmark medians."""
        return CDP_PEER_BENCHMARK_MEDIANS

    @staticmethod
    def get_module_catalog() -> list[dict]:
        """Flat combined catalog of all Climate + Water modules for UI dropdowns."""
        catalog = []
        for mod in CDP_CLIMATE_MODULES:
            catalog.append({
                "questionnaire": "climate",
                "module_code": mod["code"],
                "module_title": mod["title"],
                "category": mod["category"],
                "disclosure_count": mod["disclosures"],
            })
        for mod in CDP_WATER_MODULES:
            catalog.append({
                "questionnaire": "water",
                "module_code": mod["code"],
                "module_title": mod["title"],
                "category": mod["category"],
                "disclosure_count": mod["disclosures"],
            })
        return catalog
