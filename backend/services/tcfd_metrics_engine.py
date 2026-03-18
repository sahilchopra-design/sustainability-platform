"""
TCFD Metrics & Targets Disclosure Engine (E13)
===============================================

Full coverage of the 11 TCFD recommendations across 4 pillars
(TCFD Final Recommendations 2017 + 2021 Annex).

Covers:
  - 4 pillars: Governance, Strategy, Risk Management, Metrics & Targets
  - 11 recommendations (G1/G2, S1/S2/S3, RM1/RM2/RM3, MT1/MT2/MT3)
  - Blocking vs. non-blocking recommendation classification
  - Per-pillar scoring with blocking-recommendation weighting (1.5x)
  - Overall maturity scoring (1-5 scale) with TCFD maturity level mapping
  - Sector supplements: Financial Institutions, Energy, Transport, Buildings, Agriculture
  - Cross-framework linkage: CSRD ESRS E1, ISSB S2, CDP, GRI 305, SEC Reg S-K

E13 in the engine series (E12=MiFID II SPT → E13=TCFD Metrics → E14=...).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

TCFD_PILLARS: Dict[str, Dict[str, Any]] = {
    "governance": {
        "pillar_id": "governance",
        "name": "Governance",
        "description": (
            "Board and management oversight of climate-related risks and opportunities"
        ),
        "recommendations": ["G1", "G2"],
    },
    "strategy": {
        "pillar_id": "strategy",
        "name": "Strategy",
        "description": (
            "Actual and potential impacts of climate-related risks and opportunities "
            "on strategy and financial planning"
        ),
        "recommendations": ["S1", "S2", "S3"],
    },
    "risk_management": {
        "pillar_id": "risk_management",
        "name": "Risk Management",
        "description": (
            "Processes for identifying, assessing, and managing climate-related risks"
        ),
        "recommendations": ["RM1", "RM2", "RM3"],
    },
    "metrics_targets": {
        "pillar_id": "metrics_targets",
        "name": "Metrics & Targets",
        "description": (
            "Metrics and targets used to assess and manage climate-related risks "
            "and opportunities"
        ),
        "recommendations": ["MT1", "MT2", "MT3"],
    },
}

TCFD_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "G1": {
        "id": "G1", "pillar": "governance", "name": "Board Oversight",
        "description": "Describe the board's oversight of climate-related risks and opportunities",
        "disclosure_elements": [
            "Board responsibility structure",
            "Frequency of board briefings",
            "Board skills and competencies on climate",
        ],
        "blocking": True,
    },
    "G2": {
        "id": "G2", "pillar": "governance", "name": "Management Role",
        "description": "Describe management's role in assessing and managing climate-related risks",
        "disclosure_elements": [
            "Management-level committees",
            "Positions responsible",
            "Monitoring processes",
        ],
        "blocking": True,
    },
    "S1": {
        "id": "S1", "pillar": "strategy", "name": "Risks & Opportunities Identified",
        "description": (
            "Describe climate-related risks and opportunities the organization has identified "
            "over short/medium/long-term"
        ),
        "disclosure_elements": [
            "Physical risks",
            "Transition risks",
            "Climate-related opportunities",
            "Time horizons defined",
        ],
        "blocking": True,
    },
    "S2": {
        "id": "S2", "pillar": "strategy", "name": "Business Strategy Impact",
        "description": (
            "Describe the impact of climate-related risks and opportunities on business, "
            "strategy and financial planning"
        ),
        "disclosure_elements": [
            "Impact on products/services",
            "Impact on supply chain/value chain",
            "Impact on financial planning",
            "Impact on capital allocation",
        ],
        "blocking": True,
    },
    "S3": {
        "id": "S3", "pillar": "strategy", "name": "Scenario Resilience",
        "description": (
            "Describe the resilience of the organization's strategy, taking into consideration "
            "different climate-related scenarios"
        ),
        "disclosure_elements": [
            "Scenario methodology",
            "Scenarios used (2°C or below)",
            "Strategic resilience assessment",
            "Identified vulnerabilities",
        ],
        "blocking": False,
    },
    "RM1": {
        "id": "RM1", "pillar": "risk_management", "name": "Risk Identification Process",
        "description": (
            "Describe the organization's processes for identifying and assessing climate-related risks"
        ),
        "disclosure_elements": [
            "Risk identification process",
            "Risk categories used",
            "Tools and methodologies",
        ],
        "blocking": True,
    },
    "RM2": {
        "id": "RM2", "pillar": "risk_management", "name": "Risk Management Process",
        "description": (
            "Describe the organization's processes for managing climate-related risks"
        ),
        "disclosure_elements": [
            "Mitigation measures",
            "Risk appetite statement",
            "Escalation procedures",
        ],
        "blocking": True,
    },
    "RM3": {
        "id": "RM3", "pillar": "risk_management",
        "name": "Integration into Overall Risk Management",
        "description": (
            "Describe how processes for identifying, assessing and managing climate-related risks "
            "are integrated into the organization's overall risk management"
        ),
        "disclosure_elements": [
            "Enterprise risk management integration",
            "Board-level risk frameworks",
            "Cross-functional risk ownership",
        ],
        "blocking": False,
    },
    "MT1": {
        "id": "MT1", "pillar": "metrics_targets", "name": "Climate-Related Metrics",
        "description": "Disclose the metrics used to assess climate-related risks and opportunities",
        "disclosure_elements": [
            "Physical risk metrics",
            "Transition risk metrics",
            "Climate-related opportunities metrics",
            "Data quality disclosure",
        ],
        "blocking": True,
    },
    "MT2": {
        "id": "MT2", "pillar": "metrics_targets", "name": "Scope 1/2/3 GHG Emissions",
        "description": (
            "Disclose Scope 1, Scope 2, and if appropriate, Scope 3 GHG emissions and related risks"
        ),
        "disclosure_elements": [
            "Scope 1 emissions (tCO2e)",
            "Scope 2 market-based (tCO2e)",
            "Scope 3 material categories (tCO2e)",
            "Intensity metrics (tCO2e/revenue or unit)",
        ],
        "blocking": True,
    },
    "MT3": {
        "id": "MT3", "pillar": "metrics_targets", "name": "Climate-Related Targets",
        "description": (
            "Describe the targets used to manage climate-related risks and opportunities "
            "and performance against targets"
        ),
        "disclosure_elements": [
            "Absolute vs intensity targets",
            "Base year",
            "Target year",
            "Progress to date",
            "Science-based target alignment",
        ],
        "blocking": True,
    },
}

SECTOR_SUPPLEMENTS: Dict[str, Dict[str, Any]] = {
    "financial_institutions": {
        "sector": "financial_institutions",
        "name": "Financial Institutions",
        "sub_sectors": ["banks", "insurance", "asset_management"],
        "additional_metrics": [
            "financed_emissions_scope3_cat15",
            "portfolio_temperature_alignment",
            "climate_var_pct",
            "green_loan_pct",
            "physical_risk_exposure_pct",
        ],
        "reference": "TCFD 2020 Guidance for Financial Sector",
    },
    "energy": {
        "sector": "energy",
        "name": "Energy",
        "additional_metrics": [
            "carbon_intensity_mwh",
            "renewable_energy_pct",
            "stranded_asset_risk_pct",
            "capex_aligned_pct",
        ],
        "reference": "TCFD Annex 2021 — Energy Sector",
    },
    "transport": {
        "sector": "transport",
        "name": "Transport",
        "additional_metrics": [
            "fleet_co2_intensity_gkm",
            "low_carbon_revenue_pct",
            "physical_risk_infrastructure_pct",
        ],
        "reference": "TCFD Annex 2021 — Transport Sector",
    },
    "buildings": {
        "sector": "buildings",
        "name": "Buildings/Real Estate",
        "additional_metrics": [
            "energy_intensity_kwh_m2",
            "epc_distribution",
            "crrem_alignment_pct",
            "green_certified_pct",
        ],
        "reference": "TCFD Annex 2021 — Buildings Sector",
    },
    "agriculture": {
        "sector": "agriculture",
        "name": "Agriculture/Food/Forests",
        "additional_metrics": [
            "land_use_change_ha",
            "water_consumption_intensity",
            "biodiversity_net_gain",
            "deforestation_free_pct",
        ],
        "reference": "TCFD Annex 2021 — Agriculture/Food/Forest Products Sector",
    },
}

TCFD_MATURITY_LEVELS: Dict[int, Dict[str, Any]] = {
    1: {
        "level": 1, "name": "Initial",
        "description": "Ad hoc, inconsistent, limited board involvement",
        "score_range": [0, 30],
    },
    2: {
        "level": 2, "name": "Emerging",
        "description": "Some processes defined, partial disclosure",
        "score_range": [30, 55],
    },
    3: {
        "level": 3, "name": "Defined",
        "description": "Consistent processes, quantitative metrics, scenario analysis",
        "score_range": [55, 75],
    },
    4: {
        "level": 4, "name": "Advanced",
        "description": "Integrated into strategy, board-level, external assurance",
        "score_range": [75, 90],
    },
    5: {
        "level": 5, "name": "Leading",
        "description": "Best-in-class, forward-looking, fully integrated, SBTs",
        "score_range": [90, 100],
    },
}

TCFD_CROSS_FRAMEWORK: Dict[str, str] = {
    "csrd_esrs_e1": (
        "TCFD 4 pillars map to ESRS E1-1 to E1-9 "
        "(near 1:1 for S3 = E1-6 scenario analysis)"
    ),
    "issb_s2": (
        "IFRS S2 directly incorporates all 11 TCFD recommendations as its foundation"
    ),
    "cdp_c_modules": (
        "CDP C1=G1/G2, C2/C3=S1/S2, C3=S3 scenarios, C4=MT3 targets, C6=MT2 GHG"
    ),
    "gri_305": (
        "GRI 305 (Emissions) covers MT2 Scope 1/2/3; GRI 201 covers S2 financial planning"
    ),
    "sec_reg_sk_1501": (
        "SEC Reg S-K 1501=G1/G2, 1502=S1/S2, 1503=RM1/RM2/RM3, 1504=MT3, 1505=MT2"
    ),
}

# Pillar weights for overall score
_PILLAR_WEIGHTS: Dict[str, float] = {
    "governance": 0.20,
    "strategy": 0.30,
    "risk_management": 0.25,
    "metrics_targets": 0.25,
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RecommendationAssessment:
    rec_id: str
    disclosed: bool
    disclosure_quality: str  # "none" | "partial" | "full"
    elements_covered: List[str]
    elements_missing: List[str]
    completeness_pct: float
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "disclosed": self.disclosed,
            "disclosure_quality": self.disclosure_quality,
            "elements_covered": self.elements_covered,
            "elements_missing": self.elements_missing,
            "completeness_pct": round(self.completeness_pct, 2),
            "notes": self.notes,
        }


@dataclass
class PillarResult:
    pillar_id: str
    pillar_name: str
    total_recommendations: int
    fully_disclosed: int
    partially_disclosed: int
    not_disclosed: int
    pillar_score: float
    blocking_gaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pillar_id": self.pillar_id,
            "pillar_name": self.pillar_name,
            "total_recommendations": self.total_recommendations,
            "fully_disclosed": self.fully_disclosed,
            "partially_disclosed": self.partially_disclosed,
            "not_disclosed": self.not_disclosed,
            "pillar_score": round(self.pillar_score, 2),
            "blocking_gaps": self.blocking_gaps,
        }


@dataclass
class TCFDResult:
    assessment_id: str
    entity_id: str
    entity_name: str
    sector: str
    disclosure_year: int
    pillar_results: Dict[str, Any]
    recommendation_assessments: Dict[str, Any]
    overall_score: float
    maturity_level: int
    maturity_name: str
    blocking_gaps: List[str]
    sector_supplement: Optional[Dict[str, Any]]
    cross_framework: Dict[str, str]
    priority_actions: List[str]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "sector": self.sector,
            "disclosure_year": self.disclosure_year,
            "pillar_results": self.pillar_results,
            "recommendation_assessments": self.recommendation_assessments,
            "overall_score": round(self.overall_score, 2),
            "maturity_level": self.maturity_level,
            "maturity_name": self.maturity_name,
            "blocking_gaps": self.blocking_gaps,
            "sector_supplement": self.sector_supplement,
            "cross_framework": self.cross_framework,
            "priority_actions": self.priority_actions,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TCFDMetricsEngine:
    """TCFD 11-recommendation disclosure assessment engine."""

    _BLOCKING_WEIGHT = 1.5

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        sector: str,
        disclosure_year: int,
        recommendation_inputs: Dict[str, Dict[str, Any]],
    ) -> TCFDResult:
        """
        Full 11-recommendation TCFD assessment.

        recommendation_inputs keys: G1/G2/S1/S2/S3/RM1/RM2/RM3/MT1/MT2/MT3
        Each value: {
            "disclosed": bool,
            "disclosure_quality": str ("none"|"partial"|"full"),
            "elements_covered": list[str]
        }
        """
        logger.info(
            "TCFDMetricsEngine assess: entity=%s sector=%s year=%d",
            entity_id, sector, disclosure_year,
        )

        # Build RecommendationAssessment for every known recommendation
        rec_assessments: Dict[str, RecommendationAssessment] = {}
        for rec_id, rec_def in TCFD_RECOMMENDATIONS.items():
            raw = recommendation_inputs.get(rec_id, {})
            ra = self._build_rec_assessment(rec_id, rec_def, raw)
            rec_assessments[rec_id] = ra

        # Build PillarResult for each pillar
        pillar_results: Dict[str, PillarResult] = {}
        for pillar_id, pillar_def in TCFD_PILLARS.items():
            pr = self._build_pillar_result(
                pillar_id, pillar_def, rec_assessments
            )
            pillar_results[pillar_id] = pr

        # Overall score (weighted average of pillar scores)
        overall_score = sum(
            _PILLAR_WEIGHTS[pid] * pr.pillar_score
            for pid, pr in pillar_results.items()
        )

        # Blocking gaps across all pillars
        blocking_gaps: List[str] = []
        for pr in pillar_results.values():
            blocking_gaps.extend(pr.blocking_gaps)

        # Maturity level
        maturity_level, maturity_name = self._resolve_maturity(overall_score)

        # Priority actions: top 3 lowest-scored blocking recs
        blocking_recs = [
            (rec_id, ra)
            for rec_id, ra in rec_assessments.items()
            if TCFD_RECOMMENDATIONS[rec_id]["blocking"] and ra.completeness_pct < 80.0
        ]
        blocking_recs.sort(key=lambda x: x[1].completeness_pct)
        priority_actions: List[str] = []
        for rec_id, ra in blocking_recs[:3]:
            rec_name = TCFD_RECOMMENDATIONS[rec_id]["name"]
            priority_actions.append(
                f"Improve {rec_id} ({rec_name}): "
                f"current completeness {ra.completeness_pct:.0f}%. "
                f"Missing elements: {', '.join(ra.elements_missing[:2]) or 'see detail'}."
            )

        sector_supplement = SECTOR_SUPPLEMENTS.get(sector)

        return TCFDResult(
            assessment_id=str(uuid.uuid4()),
            entity_id=entity_id,
            entity_name=entity_name,
            sector=sector,
            disclosure_year=disclosure_year,
            pillar_results={pid: pr.to_dict() for pid, pr in pillar_results.items()},
            recommendation_assessments={
                rid: ra.to_dict() for rid, ra in rec_assessments.items()
            },
            overall_score=overall_score,
            maturity_level=maturity_level,
            maturity_name=maturity_name,
            blocking_gaps=blocking_gaps,
            sector_supplement=sector_supplement,
            cross_framework=TCFD_CROSS_FRAMEWORK,
            priority_actions=priority_actions,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def assess_pillar(
        self,
        pillar_id: str,
        entity_id: str,
        entity_name: str,
        rec_inputs: Dict[str, Dict[str, Any]],
    ) -> PillarResult:
        """Single-pillar assessment."""
        pillar_def = TCFD_PILLARS.get(pillar_id)
        if pillar_def is None:
            raise ValueError(f"Unknown pillar_id: {pillar_id}")

        rec_assessments: Dict[str, RecommendationAssessment] = {}
        for rec_id in pillar_def["recommendations"]:
            rec_def = TCFD_RECOMMENDATIONS[rec_id]
            raw = rec_inputs.get(rec_id, {})
            rec_assessments[rec_id] = self._build_rec_assessment(rec_id, rec_def, raw)

        return self._build_pillar_result(pillar_id, pillar_def, rec_assessments)

    # ------------------------------------------------------------------
    # Reference data accessors
    # ------------------------------------------------------------------

    def get_recommendations(self) -> Dict[str, Any]:
        return TCFD_RECOMMENDATIONS

    def get_pillars(self) -> Dict[str, Any]:
        return TCFD_PILLARS

    def get_sector_supplements(self) -> Dict[str, Any]:
        return SECTOR_SUPPLEMENTS

    def get_maturity_levels(self) -> Dict[str, Any]:
        return TCFD_MATURITY_LEVELS

    def get_cross_framework(self) -> Dict[str, str]:
        return TCFD_CROSS_FRAMEWORK

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_rec_assessment(
        self,
        rec_id: str,
        rec_def: Dict[str, Any],
        raw: Dict[str, Any],
    ) -> RecommendationAssessment:
        all_elements: List[str] = rec_def["disclosure_elements"]
        disclosed: bool = raw.get("disclosed", False)
        quality: str = raw.get("disclosure_quality", "none")
        elements_covered: List[str] = raw.get("elements_covered", [])

        # Only count elements that are actually defined for this recommendation
        valid_covered = [e for e in elements_covered if e in all_elements]
        elements_missing = [e for e in all_elements if e not in valid_covered]

        total = len(all_elements)
        completeness_pct = (len(valid_covered) / total * 100.0) if total > 0 else 0.0

        # Ensure consistency: if not disclosed, force completeness to 0
        if not disclosed:
            completeness_pct = 0.0
            valid_covered = []
            elements_missing = list(all_elements)
            quality = "none"

        # Auto-upgrade quality label from completeness if not supplied
        if disclosed and quality == "none":
            if completeness_pct >= 80.0:
                quality = "full"
            elif completeness_pct >= 30.0:
                quality = "partial"

        return RecommendationAssessment(
            rec_id=rec_id,
            disclosed=disclosed,
            disclosure_quality=quality,
            elements_covered=valid_covered,
            elements_missing=elements_missing,
            completeness_pct=completeness_pct,
        )

    def _build_pillar_result(
        self,
        pillar_id: str,
        pillar_def: Dict[str, Any],
        rec_assessments: Dict[str, RecommendationAssessment],
    ) -> PillarResult:
        rec_ids: List[str] = pillar_def["recommendations"]
        fully_disclosed = 0
        partially_disclosed = 0
        not_disclosed = 0
        blocking_gaps: List[str] = []

        weighted_score_sum = 0.0
        weight_sum = 0.0

        for rec_id in rec_ids:
            ra = rec_assessments.get(rec_id)
            if ra is None:
                continue
            is_blocking = TCFD_RECOMMENDATIONS[rec_id]["blocking"]
            weight = self._BLOCKING_WEIGHT if is_blocking else 1.0

            if ra.completeness_pct >= 80.0:
                fully_disclosed += 1
            elif ra.completeness_pct >= 30.0:
                partially_disclosed += 1
            else:
                not_disclosed += 1

            if is_blocking and ra.completeness_pct < 80.0:
                rec_name = TCFD_RECOMMENDATIONS[rec_id]["name"]
                blocking_gaps.append(
                    f"{rec_id} ({rec_name}): {ra.completeness_pct:.0f}% complete — "
                    f"blocking gap (Art TCFD {rec_id})"
                )

            weighted_score_sum += weight * ra.completeness_pct
            weight_sum += weight

        pillar_score = (weighted_score_sum / weight_sum) if weight_sum > 0 else 0.0

        return PillarResult(
            pillar_id=pillar_id,
            pillar_name=pillar_def["name"],
            total_recommendations=len(rec_ids),
            fully_disclosed=fully_disclosed,
            partially_disclosed=partially_disclosed,
            not_disclosed=not_disclosed,
            pillar_score=pillar_score,
            blocking_gaps=blocking_gaps,
        )

    @staticmethod
    def _resolve_maturity(score: float) -> tuple:
        for level in sorted(TCFD_MATURITY_LEVELS.keys(), reverse=True):
            meta = TCFD_MATURITY_LEVELS[level]
            lo, hi = meta["score_range"]
            if score >= lo:
                return level, meta["name"]
        return 1, TCFD_MATURITY_LEVELS[1]["name"]
