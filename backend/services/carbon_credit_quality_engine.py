"""
Carbon Credit Quality & Integrity Engine.
Regulatory basis:
  - ICVCM Core Carbon Principles (CCP) Assessment Framework v2.0, 2023
  - Verra Verified Carbon Standard (VCS) v4.0
  - Gold Standard for the Global Goals v4.3
  - CDM (UNFCCC Clean Development Mechanism) — legacy
  - Paris Agreement Article 6 ITMOs (corresponding adjustments)
  - CORSIA (ICAO CORSIA Eligible Fuels and Carbon Units, 2023 Cycle)
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

STANDARDS: dict[str, dict[str, Any]] = {
    "vcs": {
        "name": "Verified Carbon Standard (VCS)",
        "body": "Verra",
        "version": "v4.0",
        "registry": "Verra Registry",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "notes": "Largest voluntary carbon market standard; REDD+ and nature-based solution leader",
    },
    "gold_standard": {
        "name": "Gold Standard for the Global Goals",
        "body": "Gold Standard Foundation",
        "version": "v4.3",
        "registry": "Gold Standard Impact Registry",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "notes": "Strong co-benefit and SDG impact requirements; cookstoves and WASH projects",
    },
    "cdm": {
        "name": "Clean Development Mechanism",
        "body": "UNFCCC",
        "version": "Legacy",
        "registry": "UNFCCC CDM Registry",
        "corsia_eligible": False,
        "ccp_label_eligible": False,
        "notes": "Legacy Kyoto Protocol mechanism; most credits pre-2020; transition to Art 6 ITMOs",
    },
    "art6_itmo": {
        "name": "Article 6 ITMOs",
        "body": "UNFCCC Article 6 Supervisory Body",
        "version": "Paris Agreement 2015",
        "registry": "UNFCCC International Registry",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "notes": "Internationally Transferred Mitigation Outcomes; corresponding adjustment required",
    },
    "ccp": {
        "name": "ICVCM CCP Label",
        "body": "Integrity Council for the Voluntary Carbon Market (ICVCM)",
        "version": "CCP Assessment Framework v2.0, 2023",
        "registry": "ICVCM Approved Programme Registry",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "notes": "Highest-integrity label; requires programme-level + category-level assessment",
    },
    "plan_vivo": {
        "name": "Plan Vivo Standard",
        "body": "Plan Vivo Foundation",
        "version": "2013 (update in progress)",
        "registry": "Markit Environmental Registry",
        "corsia_eligible": False,
        "ccp_label_eligible": False,
        "notes": "Community forestry and land-use; strong livelihood co-benefits",
    },
    "american_carbon_registry": {
        "name": "American Carbon Registry (ACR)",
        "body": "Winrock International",
        "version": "v13.0",
        "registry": "ACR Registry",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "notes": "US-focused; forestry, soil, and industrial avoidance methodologies",
    },
    "climate_action_reserve": {
        "name": "Climate Action Reserve (CAR)",
        "body": "Climate Action Reserve",
        "version": "2023",
        "registry": "CAR Registry",
        "corsia_eligible": True,
        "ccp_label_eligible": True,
        "notes": "Protocol-based; strong US compliance linkage; soil carbon and forestry",
    },
}

ICVCM_CCP_CRITERIA: list[dict[str, Any]] = [
    {
        "id": "CCP-1",
        "criterion": "Governance",
        "description": "Programme has effective governance, operational management and accountability.",
        "assessment_level": "programme",
    },
    {
        "id": "CCP-2",
        "criterion": "Tracking",
        "description": "Unique serialisation of carbon credits in public registry to prevent double issuance.",
        "assessment_level": "programme",
    },
    {
        "id": "CCP-3",
        "criterion": "Transparency",
        "description": "Programme methodology, validation/verification reports and data publicly accessible.",
        "assessment_level": "programme",
    },
    {
        "id": "CCP-4",
        "criterion": "Robust Independent Third-Party Validation & Verification",
        "description": "Accredited third-party VVB validates and verifies to programme standards.",
        "assessment_level": "programme",
    },
    {
        "id": "CCP-5",
        "criterion": "Additionality",
        "description": "Emission reductions would not have occurred in the absence of the project.",
        "assessment_level": "category",
    },
    {
        "id": "CCP-6",
        "criterion": "Permanence",
        "description": "Risks to permanence are identified, assessed and mitigated (buffer pool or insurance).",
        "assessment_level": "category",
    },
    {
        "id": "CCP-7",
        "criterion": "Robust Quantification of Emission Reductions and Removals",
        "description": "Conservative, complete and consistent GHG accounting with uncertainty analysis.",
        "assessment_level": "category",
    },
    {
        "id": "CCP-8",
        "criterion": "No Double Counting",
        "description": "Corresponding adjustment applied or robust host-country/programme double-counting prevention.",
        "assessment_level": "category",
    },
    {
        "id": "CCP-9",
        "criterion": "Sustainable Development Co-benefits",
        "description": "Programme or category contributes to sustainable development in host country.",
        "assessment_level": "category",
    },
    {
        "id": "CCP-10",
        "criterion": "Transition to Net Zero",
        "description": "Programme supports long-term transition to net zero; avoidance projects have phase-out path.",
        "assessment_level": "programme",
    },
]

METHODOLOGIES: dict[str, dict[str, Any]] = {
    "AM0014": {"standard": "cdm", "type": "afforestation_reforestation", "name": "Natural forest management"},
    "AR-ACM0003": {"standard": "cdm", "type": "afforestation_reforestation", "name": "Afforestation & reforestation — blanket/mosaic"},
    "VM0015": {"standard": "vcs", "type": "redd_plus", "name": "REDD+ (deforestation & forest degradation)"},
    "VM0007": {"standard": "vcs", "type": "redd_plus", "name": "REDD+ Methodology Framework (REDD-MF)"},
    "AMS-II.G": {"standard": "cdm", "type": "improved_cookstoves", "name": "Energy efficiency measures in thermal applications"},
    "GS_TPDDTEC": {"standard": "gold_standard", "type": "improved_cookstoves", "name": "Technologies & Practices for Displaced Deforestation Emissions — Cookstoves"},
    "ACM0002": {"standard": "cdm", "type": "renewable_energy", "name": "Grid-connected renewable electricity generation"},
    "AMS-I.D": {"standard": "cdm", "type": "renewable_energy", "name": "Renewable energy — user-level electricity generation"},
    "ACM0001": {"standard": "cdm", "type": "methane_capture", "name": "Flaring or use of landfill gas"},
    "AMS-III.D": {"standard": "cdm", "type": "methane_capture", "name": "Methane recovery in animal manure management"},
    "AMS-II.C": {"standard": "cdm", "type": "industrial_efficiency", "name": "Demand-side energy efficiency activities for specific technologies"},
    "VM0042": {"standard": "vcs", "type": "soil_carbon", "name": "Improved agricultural land management (soil carbon)"},
    "VM0033": {"standard": "vcs", "type": "blue_carbon", "name": "Tidal wetland and seagrass restoration"},
    "VM0024": {"standard": "vcs", "type": "blue_carbon", "name": "Blue carbon — mangrove restoration"},
    "ACR_SCA": {"standard": "american_carbon_registry", "type": "soil_carbon", "name": "Soil Carbon Quantification Methodology"},
    "CAR_IFM": {"standard": "climate_action_reserve", "type": "afforestation_reforestation", "name": "Improved Forest Management (IFM)"},
    "GS_ICS": {"standard": "gold_standard", "type": "improved_cookstoves", "name": "Metered Energy Cooking (Gold Standard)"},
    "ART_TREES": {"standard": "art6_itmo", "type": "redd_plus", "name": "Architecture for REDD+ Transactions (ART TREES) v2.0"},
    "VM0041": {"standard": "vcs", "type": "renewable_energy", "name": "Methodology for the Reduction of GHG Emissions from Grid-Connected Electricity"},
    "DAC_PILOT": {"standard": "vcs", "type": "direct_air_capture", "name": "Direct Air Capture — Pilot (not yet methodologically mature)"},
}

PERMANENCE_RISK_BY_TYPE: dict[str, dict[str, Any]] = {
    "afforestation_reforestation": {
        "risk_score": 0.7,
        "level": "high",
        "description": "High reversal risk due to fire, disease, pest, illegal logging",
        "mitigation": "Buffer pool (typically 10-30% of issued credits withheld)",
    },
    "redd_plus": {
        "risk_score": 0.6,
        "level": "high",
        "description": "REDD+ leakage and permanence risks; deforestation pressure displacement",
        "mitigation": "Jurisdictional accounting; insurance; buffer pool; ER programme design",
    },
    "soil_carbon": {
        "risk_score": 0.8,
        "level": "very_high",
        "description": "Very high reversal risk from tillage reversion, drought, land-use change",
        "mitigation": "Conservative crediting; 5-year monitoring cycles; buffer contributions",
    },
    "blue_carbon": {
        "risk_score": 0.5,
        "level": "high",
        "description": "Sea level rise, storm damage, and human disturbance risks",
        "mitigation": "Protected area designation; insurance; 40-year monitoring",
    },
    "improved_cookstoves": {
        "risk_score": 0.2,
        "level": "low",
        "description": "Low permanence risk — activity-based emission reduction (no carbon stored)",
        "mitigation": "Metering and monitoring of stove adoption rates",
    },
    "renewable_energy": {
        "risk_score": 0.1,
        "level": "very_low",
        "description": "Minimal permanence risk — grid emission displacement",
        "mitigation": "Standard additionality and grid emission factor updates",
    },
    "methane_capture": {
        "risk_score": 0.1,
        "level": "very_low",
        "description": "Minimal permanence risk — destroyed methane cannot reverse",
        "mitigation": "Operational monitoring of flare/capture system",
    },
    "industrial_efficiency": {
        "risk_score": 0.1,
        "level": "very_low",
        "description": "Minimal permanence risk — technology-based efficiency gains",
        "mitigation": "Annual M&V reports",
    },
    "direct_air_capture": {
        "risk_score": 0.05,
        "level": "very_low",
        "description": "Engineered geological or mineralisation storage — very durable",
        "mitigation": "Storage site monitoring; geological survey",
    },
}

CORSIA_ELIGIBLE: dict[str, Any] = {
    "phase_2024_2026": {
        "eligible_programmes": [
            "vcs", "gold_standard", "american_carbon_registry",
            "climate_action_reserve", "art6_itmo",
        ],
        "vintage_requirement": "Issued from 2016 onwards",
        "unit_criteria": "Must meet CORSIA Eligible Emissions Unit criteria (ICAO Doc 9501)",
        "footnote": "CDM credits NOT eligible for CORSIA Phase 2; Art 6 ITMOs subject to corresponding adjustment",
    },
    "ccp_premium": {
        "description": "ICVCM CCP-labelled credits command premium recognition across frameworks",
        "eligible_frameworks": ["CORSIA", "VCMI Claims Code", "SBTi Beyond Value Chain", "Net Zero Insurance Alliance"],
    },
}

PRICE_BENCHMARKS: dict[str, dict[str, Any]] = {
    "nature_based_removal": {
        "min_usd_per_t": 15,
        "max_usd_per_t": 60,
        "median_usd_per_t": 28,
        "description": "Afforestation, REDD+, blue carbon, soil — high co-benefit premium possible",
    },
    "tech_removal": {
        "min_usd_per_t": 100,
        "max_usd_per_t": 500,
        "median_usd_per_t": 200,
        "description": "Direct air capture, BECCS — durable removal; premium for long-term contracts",
    },
    "avoidance": {
        "min_usd_per_t": 2,
        "max_usd_per_t": 15,
        "median_usd_per_t": 7,
        "description": "Renewable energy, cookstoves, methane — lowest price; additionality scrutiny high",
    },
    "ccp_label_premium": {
        "premium_pct_over_unlabelled": 20,
        "max_premium_pct": 30,
        "description": "ICVCM CCP label typically commands 20-30% premium over equivalent unlabelled credits",
    },
}

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class CarbonCreditQuality:
    entity_id: str
    project_id: str
    project_name: str
    standard: str
    methodology: str
    project_type: str
    vintage_year: int
    volume_tco2e: float
    overall_quality_score: float
    quality_grade: str
    ccp_criteria_results: list[dict]
    ccp_eligible: bool
    corsia_eligible: bool
    permanence_risk: dict
    additionality_risk: str
    double_counting_risk: str
    price_range_usd: dict
    issues: list[str]
    regulatory_refs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CarbonCreditQualityEngine:
    """Carbon Credit Quality & Integrity assessment engine."""

    _instance: "CarbonCreditQualityEngine | None" = None

    def __init__(self) -> None:
        self._refs = [
            "ICVCM Core Carbon Principles Assessment Framework v2.0, 2023",
            "Verra VCS Standard v4.0",
            "Gold Standard for the Global Goals v4.3",
            "UNFCCC Clean Development Mechanism Methodologies",
            "Paris Agreement Article 6 §§ 6.2, 6.4",
            "ICAO CORSIA Eligible Emissions Unit Criteria (Doc 9501, 2023)",
            "VCMI Claims Code of Practice 2023",
        ]

    @classmethod
    def get_instance(cls) -> "CarbonCreditQualityEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # CCP eligibility
    # ------------------------------------------------------------------

    def check_ccp_eligibility(self, standard: str, methodology: str, project_type: str) -> dict[str, Any]:
        std_info = STANDARDS.get(standard, {})
        method_info = METHODOLOGIES.get(methodology, {})
        perm = PERMANENCE_RISK_BY_TYPE.get(project_type, {})

        criteria_results = []
        for crit in ICVCM_CCP_CRITERIA:
            # Heuristic pass/fail based on standard
            if standard in ("vcs", "gold_standard", "american_carbon_registry", "climate_action_reserve", "art6_itmo"):
                if crit["id"] in ("CCP-1", "CCP-2", "CCP-3", "CCP-4"):
                    result = "pass"
                elif crit["id"] == "CCP-6" and perm.get("risk_score", 0.5) > 0.7:
                    result = "partial"
                elif crit["id"] == "CCP-8" and standard == "cdm":
                    result = "fail"
                else:
                    result = "pass"
            elif standard == "cdm":
                result = "partial" if crit["id"] not in ("CCP-2", "CCP-3") else "pass"
            else:
                result = "partial"

            criteria_results.append({
                "id": crit["id"],
                "criterion": crit["criterion"],
                "result": result,
                "assessment_level": crit["assessment_level"],
            })

        passed = sum(1 for c in criteria_results if c["result"] == "pass")
        ccp_eligible = passed >= 8 and standard in ("vcs", "gold_standard", "american_carbon_registry", "climate_action_reserve", "art6_itmo")

        return {
            "standard": standard,
            "methodology": methodology,
            "project_type": project_type,
            "ccp_eligible": ccp_eligible,
            "criteria_results": criteria_results,
            "criteria_passed": passed,
            "criteria_total": len(ICVCM_CCP_CRITERIA),
            "corsia_eligible": std_info.get("corsia_eligible", False),
            "permanence_risk": perm,
        }

    # ------------------------------------------------------------------
    # Score single project
    # ------------------------------------------------------------------

    def score_project(
        self,
        entity_id: str,
        project_id: str,
        project_name: str,
        standard: str,
        methodology: str,
        project_type: str,
        vintage_year: int,
        volume_tco2e: float,
    ) -> CarbonCreditQuality:
        rng = random.Random(hash(f"{entity_id}_{project_id}") & 0xFFFFFFFF)

        ccp_result = self.check_ccp_eligibility(standard, methodology, project_type)
        perm = PERMANENCE_RISK_BY_TYPE.get(project_type, {"risk_score": 0.5, "level": "medium"})
        std_info = STANDARDS.get(standard, {})

        # Quality scoring
        base_score = 70.0
        if std_info.get("ccp_label_eligible"):
            base_score += 10
        if ccp_result["ccp_eligible"]:
            base_score += 10
        if vintage_year >= 2020:
            base_score += 5
        elif vintage_year < 2015:
            base_score -= 15
        if perm.get("risk_score", 0.5) > 0.6:
            base_score -= 10
        if standard == "cdm" and vintage_year < 2015:
            base_score -= 10
        base_score += rng.uniform(-5, 5)
        quality_score = round(min(100.0, max(0.0, base_score)), 1)

        if quality_score >= 85:
            grade = "A"
        elif quality_score >= 70:
            grade = "B"
        elif quality_score >= 55:
            grade = "C"
        else:
            grade = "D"

        # Price range
        if project_type in ("direct_air_capture",):
            pbench = PRICE_BENCHMARKS["tech_removal"]
        elif project_type in ("renewable_energy", "methane_capture", "industrial_efficiency", "improved_cookstoves"):
            pbench = PRICE_BENCHMARKS["avoidance"]
        else:
            pbench = PRICE_BENCHMARKS["nature_based_removal"]

        ccp_mult = 1.0 + (PRICE_BENCHMARKS["ccp_label_premium"]["premium_pct_over_unlabelled"] / 100) if ccp_result["ccp_eligible"] else 1.0
        price_range = {
            "min_usd_per_t": round(pbench["min_usd_per_t"] * ccp_mult, 1),
            "max_usd_per_t": round(pbench["max_usd_per_t"] * ccp_mult, 1),
            "ccp_premium_applied": ccp_result["ccp_eligible"],
        }

        # Issues
        issues: list[str] = []
        if vintage_year < 2015:
            issues.append("Pre-2015 vintage — additionality and CDM over-crediting concerns")
        if standard == "cdm":
            issues.append("CDM credits: not CORSIA-eligible; double counting risk under Art 6")
        if perm.get("risk_score", 0) > 0.6:
            issues.append(f"High permanence risk ({project_type}) — buffer pool adequacy must be verified")
        if not ccp_result["ccp_eligible"]:
            issues.append("Not CCP-labelled — may not meet VCMI Claims Code of Practice requirements")

        additionality_risk = "low" if standard in ("vcs", "gold_standard") and vintage_year >= 2018 else ("high" if vintage_year < 2015 else "medium")
        double_counting_risk = "high" if standard == "cdm" else ("low" if standard == "art6_itmo" else "medium")

        return CarbonCreditQuality(
            entity_id=entity_id,
            project_id=project_id,
            project_name=project_name,
            standard=standard,
            methodology=methodology,
            project_type=project_type,
            vintage_year=vintage_year,
            volume_tco2e=volume_tco2e,
            overall_quality_score=quality_score,
            quality_grade=grade,
            ccp_criteria_results=ccp_result["criteria_results"],
            ccp_eligible=ccp_result["ccp_eligible"],
            corsia_eligible=std_info.get("corsia_eligible", False),
            permanence_risk=perm,
            additionality_risk=additionality_risk,
            double_counting_risk=double_counting_risk,
            price_range_usd=price_range,
            issues=issues,
            regulatory_refs=self._refs,
        )

    # ------------------------------------------------------------------
    # Portfolio scoring
    # ------------------------------------------------------------------

    def score_portfolio(self, entity_id: str, portfolio: list[dict]) -> dict[str, Any]:
        results = []
        for item in portfolio:
            r = self.score_project(
                entity_id=entity_id,
                project_id=item.get("project_id", "UNKNOWN"),
                project_name=item.get("project_name", "Unknown Project"),
                standard=item.get("standard", "vcs"),
                methodology=item.get("methodology", "VM0015"),
                project_type=item.get("project_type", "redd_plus"),
                vintage_year=item.get("vintage_year", 2020),
                volume_tco2e=item.get("volume_tco2e", 1000),
            )
            results.append(asdict(r))

        total_volume = sum(p.get("volume_tco2e", 0) for p in portfolio) or 1
        weighted_quality = sum(
            r["overall_quality_score"] * p.get("volume_tco2e", 1000)
            for r, p in zip(results, portfolio)
        ) / total_volume

        ccp_volume = sum(p.get("volume_tco2e", 0) for r, p in zip(results, portfolio) if r["ccp_eligible"])
        corsia_volume = sum(p.get("volume_tco2e", 0) for r, p in zip(results, portfolio) if r["corsia_eligible"])

        grades = [r["quality_grade"] for r in results]
        grade_dist = {g: grades.count(g) for g in ("A", "B", "C", "D")}

        return {
            "entity_id": entity_id,
            "portfolio_size": len(portfolio),
            "total_volume_tco2e": total_volume,
            "weighted_average_quality_score": round(weighted_quality, 1),
            "ccp_labelled_volume_tco2e": ccp_volume,
            "ccp_pct": round(100 * ccp_volume / total_volume, 1),
            "corsia_eligible_volume_tco2e": corsia_volume,
            "corsia_pct": round(100 * corsia_volume / total_volume, 1),
            "grade_distribution": grade_dist,
            "project_results": results,
        }

    # ------------------------------------------------------------------
    # Reference getters
    # ------------------------------------------------------------------

    def ref_standards(self) -> dict:
        return STANDARDS

    def ref_icvcm_criteria(self) -> list[dict]:
        return ICVCM_CCP_CRITERIA

    def ref_methodologies(self) -> dict:
        return METHODOLOGIES

    def ref_corsia_eligibility(self) -> dict:
        return CORSIA_ELIGIBLE

    def ref_price_benchmarks(self) -> dict:
        return PRICE_BENCHMARKS


def get_engine() -> CarbonCreditQualityEngine:
    return CarbonCreditQualityEngine.get_instance()
