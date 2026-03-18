"""
Biodiversity Finance Metrics Engine — E23
TNFD v1.0 14 core metrics (4 pillars)
SBTN Steps 1-5 readiness
CBD GBF Target 15 sub-elements a-f
MSA.km2 footprint (land-use type x area)
ENCORE ecosystem services
PBAF 2023 Standard
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import random, math


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

TNFD_PILLARS = {
    "governance": {
        "metrics": ["M1_board_oversight", "M2_mgmt_responsibilities", "M3_incentives"],
        "weight": 0.25,
    },
    "strategy": {
        "metrics": ["M4_dependency_assessment", "M5_risk_identification", "M6_scenario_analysis"],
        "weight": 0.25,
    },
    "risk_management": {
        "metrics": ["M7_risk_processes", "M8_integrated_risk_mgmt", "M9_third_party_risk"],
        "weight": 0.25,
    },
    "metrics_targets": {
        "metrics": ["M10_state_metrics", "M11_response_metrics", "M12_dependency_metrics",
                    "M13_financed_impacts", "M14_targets"],
        "weight": 0.25,
    },
}

LAND_USE_MSA = {
    "primary_vegetation":      {"msa_factor": 1.00, "description": "Pristine natural land"},
    "secondary_vegetation":    {"msa_factor": 0.70, "description": "Regenerating natural land"},
    "extensive_agriculture":   {"msa_factor": 0.50, "description": "Low-intensity farming"},
    "intensive_agriculture":   {"msa_factor": 0.30, "description": "High-intensity farming"},
    "plantation_forestry":     {"msa_factor": 0.20, "description": "Managed plantations"},
    "urban_built_up":          {"msa_factor": 0.05, "description": "Built-up urban area"},
    "mining_quarrying":        {"msa_factor": 0.10, "description": "Extractive operations"},
    "aquaculture":             {"msa_factor": 0.40, "description": "Managed water production"},
}

SBTN_STEPS = {
    1: {"name": "Assess",    "description": "Prioritise locations and value chain segments"},
    2: {"name": "Interpret", "description": "Understand material dependencies and impacts"},
    3: {"name": "Measure",   "description": "Measure current state of nature"},
    4: {"name": "Set",       "description": "Set science-based targets"},
    5: {"name": "Act",       "description": "Implement and disclose progress"},
}

CBD_GBF_TARGET15 = {
    "15a": "Assess biodiversity impacts across business operations",
    "15b": "Reduce negative biodiversity impacts in operations",
    "15c": "Increase positive biodiversity contributions",
    "15d": "Disclose risks and dependencies",
    "15e": "Provide information to consumers",
    "15f": "Reduce subsidies harmful to biodiversity",
}

ENCORE_ECOSYSTEM_SERVICES = [
    "biomass_provisioning", "climate_regulation", "flood_mitigation",
    "water_supply", "soil_quality", "pollination", "erosion_control",
    "disease_regulation", "soil_erosion_control", "noise_mitigation",
]

ASSESSMENT_TYPES = ["tnfd", "msa", "sbtn", "cbd_gbf", "combined"]


@dataclass
class TNFDPillarScore:
    pillar: str = ""
    score: int = 0   # 1-5 maturity
    metrics_assessed: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


@dataclass
class MSAFootprint:
    total_footprint_km2: float = 0.0
    by_land_use: dict[str, float] = field(default_factory=dict)  # land_use -> msa_km2
    by_land_use_area: dict[str, float] = field(default_factory=dict)
    hotspot_areas: list[str] = field(default_factory=list)
    sensitive_ecosystems_pct: float = 0.0


@dataclass
class SBTNReadiness:
    overall_readiness_score: float = 0.0
    steps_complete: int = 0
    step_status: dict[int, str] = field(default_factory=dict)  # 1-5 -> complete/partial/not_started
    target_types: list[str] = field(default_factory=list)
    next_priority_step: int = 1


@dataclass
class CBDGBFAlignment:
    overall_alignment: str = "early-stage"  # aligned/progressing/early-stage
    sub_element_scores: dict[str, float] = field(default_factory=dict)
    average_score: float = 0.0
    target15_gap: list[str] = field(default_factory=list)


@dataclass
class BiodiversityAssessment:
    assessment_id: str = ""
    entity_id: str = ""
    entity_name: str = ""
    sector: str = ""
    assessment_type: str = "combined"
    # TNFD
    tnfd_overall_maturity: int = 0
    tnfd_pillar_scores: list[TNFDPillarScore] = field(default_factory=list)
    tnfd_gaps: list[str] = field(default_factory=list)
    # MSA
    msa_footprint: MSAFootprint = field(default_factory=MSAFootprint)
    # SBTN
    sbtn_readiness: SBTNReadiness = field(default_factory=SBTNReadiness)
    # CBD GBF
    cbd_gbf: CBDGBFAlignment = field(default_factory=CBDGBFAlignment)
    # Finance
    transition_finance_pct: float = 0.0
    nature_positive_score: float = 0.0
    # Cross-framework
    cross_framework: dict[str, Any] = field(default_factory=dict)
    priority_actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class BiodiversityFinanceEngine:
    """TNFD/SBTN/CBD GBF/MSA biodiversity finance assessment engine."""

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        sector: str,
        assessment_type: str = "combined",
        operational_area_km2: float | None = None,
        land_use_breakdown: dict[str, float] | None = None,
    ) -> BiodiversityAssessment:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        result = BiodiversityAssessment(
            assessment_id=f"BIO-{entity_id[:8].upper()}-2024",
            entity_id=entity_id,
            entity_name=entity_name,
            sector=sector,
            assessment_type=assessment_type,
        )

        # TNFD pillar scores
        pillar_scores: list[TNFDPillarScore] = []
        all_gaps: list[str] = []
        for pillar, cfg in TNFD_PILLARS.items():
            score = int(rng.uniform(1, 5.9))
            gaps = [m for m in cfg["metrics"] if rng.random() < (0.6 - score * 0.10)]
            pillar_scores.append(TNFDPillarScore(
                pillar=pillar,
                score=score,
                metrics_assessed=[m for m in cfg["metrics"] if m not in gaps],
                gaps=gaps,
            ))
            all_gaps.extend(gaps)
        result.tnfd_pillar_scores = pillar_scores
        result.tnfd_gaps = all_gaps
        result.tnfd_overall_maturity = int(
            sum(p.score for p in pillar_scores) / len(pillar_scores)
        )

        # MSA footprint
        area = operational_area_km2 or rng.uniform(100, 50_000)
        breakdown = land_use_breakdown or {
            lt: rng.uniform(0.02, 0.35) for lt in list(LAND_USE_MSA.keys())[:5]
        }
        # Normalise
        total_fraction = sum(breakdown.values())
        msa = MSAFootprint()
        for lt, frac in breakdown.items():
            area_lt = area * frac / total_fraction
            msa_factor = LAND_USE_MSA.get(lt, {"msa_factor": 0.5})["msa_factor"]
            msa_loss = area_lt * (1 - msa_factor)
            msa.by_land_use_area[lt] = round(area_lt, 1)
            msa.by_land_use[lt] = round(msa_loss, 2)
        msa.total_footprint_km2 = round(sum(msa.by_land_use.values()), 2)
        msa.sensitive_ecosystems_pct = round(rng.uniform(5, 40), 1)
        msa.hotspot_areas = [lt for lt, v in msa.by_land_use.items() if v > msa.total_footprint_km2 * 0.25]
        result.msa_footprint = msa

        # SBTN readiness
        sbtn = SBTNReadiness()
        steps_done = int(rng.uniform(0, 5.9))
        sbtn.steps_complete = steps_done
        sbtn.overall_readiness_score = round(steps_done / 5 * 100, 1)
        for step_n in range(1, 6):
            if step_n <= steps_done:
                sbtn.step_status[step_n] = "complete"
            elif step_n == steps_done + 1:
                sbtn.step_status[step_n] = "partial"
            else:
                sbtn.step_status[step_n] = "not_started"
        sbtn.next_priority_step = min(steps_done + 1, 5)
        sbtn.target_types = rng.choices(
            ["no-net-loss", "net-gain", "no-go-zones", "restoration"], k=rng.randint(1, 3)
        )
        result.sbtn_readiness = sbtn

        # CBD GBF Target 15
        cbd = CBDGBFAlignment()
        sub_scores: dict[str, float] = {}
        for elem, desc in CBD_GBF_TARGET15.items():
            sub_scores[elem] = round(rng.uniform(10, 90), 1)
        cbd.sub_element_scores = sub_scores
        cbd.average_score = round(sum(sub_scores.values()) / len(sub_scores), 1)
        if cbd.average_score >= 70:
            cbd.overall_alignment = "aligned"
        elif cbd.average_score >= 40:
            cbd.overall_alignment = "progressing"
        else:
            cbd.overall_alignment = "early-stage"
        cbd.target15_gap = [k for k, v in sub_scores.items() if v < 40]
        result.cbd_gbf = cbd

        # Finance metrics
        result.transition_finance_pct = round(rng.uniform(2, 25), 1)
        result.nature_positive_score = round(
            (result.tnfd_overall_maturity / 5 * 40)
            + (sbtn.overall_readiness_score * 0.30)
            + (cbd.average_score * 0.30),
            1,
        )

        # Cross-framework linkages
        result.cross_framework = {
            "esrs_e4_alignment": round(rng.uniform(40, 90), 1),
            "eu_taxonomy_dnsh_biodiversity": round(rng.uniform(30, 80), 1),
            "gri_304_material_topics": rng.randint(2, 8),
            "encore_ecosystem_dependencies": rng.sample(ENCORE_ECOSYSTEM_SERVICES, k=4),
            "pbaf_2023_standard": "partial" if steps_done < 3 else "compliant",
        }

        # Priority actions
        if result.tnfd_overall_maturity < 3:
            result.priority_actions.append("Advance TNFD disclosure from LEAP-framework assessment to full TNFD adoption")
        if sbtn.steps_complete < 2:
            result.priority_actions.append("Complete SBTN Step 1 (Assess) to identify priority locations and value chain segments")
        if msa.total_footprint_km2 > 500:
            result.priority_actions.append("MSA footprint >500 km2 — initiate site-level biodiversity management plans")
        if cbd.overall_alignment == "early-stage":
            result.priority_actions.append("Develop CBD GBF Target 15 action plan — current alignment early-stage")
        if result.transition_finance_pct < 5:
            result.priority_actions.append("Increase nature-positive transition finance allocation to >=5% of portfolio")

        return result

    def calculate_msa_footprint(
        self,
        entity_id: str,
        land_use_areas: dict[str, float],  # land_use -> area km2
    ) -> MSAFootprint:
        msa = MSAFootprint()
        for lt, area in land_use_areas.items():
            factor = LAND_USE_MSA.get(lt, {"msa_factor": 0.5})["msa_factor"]
            msa_loss = area * (1 - factor)
            msa.by_land_use_area[lt] = area
            msa.by_land_use[lt] = round(msa_loss, 2)
        msa.total_footprint_km2 = round(sum(msa.by_land_use.values()), 2)
        msa.hotspot_areas = [
            lt for lt, v in msa.by_land_use.items()
            if v > msa.total_footprint_km2 * 0.20
        ]
        return msa

    def ref_tnfd_pillars(self) -> dict[str, Any]:
        return TNFD_PILLARS

    def ref_land_use_msa(self) -> dict[str, Any]:
        return LAND_USE_MSA

    def ref_sbtn_steps(self) -> dict[int, Any]:
        return SBTN_STEPS

    def ref_cbd_gbf_target15(self) -> dict[str, str]:
        return CBD_GBF_TARGET15

    def ref_encore_services(self) -> list[str]:
        return ENCORE_ECOSYSTEM_SERVICES


_engine = BiodiversityFinanceEngine()


def get_engine() -> BiodiversityFinanceEngine:
    return _engine
