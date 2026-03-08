"""
Disclosure Completeness Engine
================================
Assesses completeness of sustainability disclosures against regulatory
frameworks (CSRD/ESRS, ISSB S1/S2, TCFD, SFDR PAI). Identifies gaps,
calculates coverage rates, and produces a readiness score per framework.

References:
- EFRAG ESRS Set 1 (2023) — mandatory data point catalogue
- IFRS S1/S2 (2023) — ISSB disclosure requirements
- TCFD Recommendations (2017) — 11 recommended disclosures
- SFDR RTS (2022) — PAI indicators
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — Framework Requirements
# ---------------------------------------------------------------------------

FRAMEWORK_REQUIREMENTS: dict[str, dict] = {
    "ESRS_E1": {
        "framework": "CSRD/ESRS", "standard": "E1 — Climate Change",
        "required_dps": [
            {"dp_id": "E1-1_transition_plan", "label": "Transition plan for climate change mitigation", "type": "narrative"},
            {"dp_id": "E1-2_policies", "label": "Policies related to climate change mitigation and adaptation", "type": "narrative"},
            {"dp_id": "E1-3_actions", "label": "Actions and resources related to climate change", "type": "narrative"},
            {"dp_id": "E1-4_targets", "label": "Targets related to climate change mitigation and adaptation", "type": "quantitative"},
            {"dp_id": "E1-5_energy_consumption", "label": "Energy consumption and mix", "type": "quantitative"},
            {"dp_id": "E1-5_renewable_share", "label": "Share of renewable energy", "type": "quantitative"},
            {"dp_id": "E1-6_scope1", "label": "Gross Scope 1 GHG emissions", "type": "quantitative"},
            {"dp_id": "E1-6_scope2_lb", "label": "Gross Scope 2 GHG (location-based)", "type": "quantitative"},
            {"dp_id": "E1-6_scope2_mb", "label": "Gross Scope 2 GHG (market-based)", "type": "quantitative"},
            {"dp_id": "E1-6_scope3", "label": "Total Scope 3 GHG emissions", "type": "quantitative"},
            {"dp_id": "E1-6_total", "label": "Total GHG emissions", "type": "quantitative"},
            {"dp_id": "E1-6_intensity", "label": "GHG intensity per net revenue", "type": "quantitative"},
            {"dp_id": "E1-7_removals", "label": "GHG removals and storage from operations/value chain", "type": "quantitative"},
            {"dp_id": "E1-8_carbon_credits", "label": "Internal carbon pricing", "type": "quantitative"},
            {"dp_id": "E1-9_financial_effects", "label": "Anticipated financial effects from climate risks/opportunities", "type": "quantitative"},
        ],
        "total_dps": 15,
    },
    "ESRS_E2": {
        "framework": "CSRD/ESRS", "standard": "E2 — Pollution",
        "required_dps": [
            {"dp_id": "E2-1_policies", "label": "Policies related to pollution", "type": "narrative"},
            {"dp_id": "E2-2_actions", "label": "Actions and resources — pollution", "type": "narrative"},
            {"dp_id": "E2-3_targets", "label": "Targets related to pollution", "type": "quantitative"},
            {"dp_id": "E2-4_air", "label": "Pollution of air", "type": "quantitative"},
            {"dp_id": "E2-4_water", "label": "Pollution of water", "type": "quantitative"},
            {"dp_id": "E2-4_soil", "label": "Pollution of soil", "type": "quantitative"},
        ],
        "total_dps": 6,
    },
    "ESRS_E3": {
        "framework": "CSRD/ESRS", "standard": "E3 — Water and Marine Resources",
        "required_dps": [
            {"dp_id": "E3-1_policies", "label": "Policies — water/marine", "type": "narrative"},
            {"dp_id": "E3-2_actions", "label": "Actions — water/marine", "type": "narrative"},
            {"dp_id": "E3-3_targets", "label": "Targets — water/marine", "type": "quantitative"},
            {"dp_id": "E3-4_consumption", "label": "Water consumption", "type": "quantitative"},
            {"dp_id": "E3-4_withdrawal", "label": "Water withdrawal", "type": "quantitative"},
        ],
        "total_dps": 5,
    },
    "ESRS_E4": {
        "framework": "CSRD/ESRS", "standard": "E4 — Biodiversity and Ecosystems",
        "required_dps": [
            {"dp_id": "E4-1_transition_plan", "label": "Transition plan for biodiversity", "type": "narrative"},
            {"dp_id": "E4-2_policies", "label": "Policies — biodiversity", "type": "narrative"},
            {"dp_id": "E4-3_actions", "label": "Actions — biodiversity", "type": "narrative"},
            {"dp_id": "E4-4_targets", "label": "Targets — biodiversity", "type": "quantitative"},
            {"dp_id": "E4-5_impact_metrics", "label": "Impact metrics — land-use change", "type": "quantitative"},
            {"dp_id": "E4-6_financial_effects", "label": "Anticipated financial effects — biodiversity", "type": "quantitative"},
        ],
        "total_dps": 6,
    },
    "ESRS_E5": {
        "framework": "CSRD/ESRS", "standard": "E5 — Resource Use and Circular Economy",
        "required_dps": [
            {"dp_id": "E5-1_policies", "label": "Policies — circular economy", "type": "narrative"},
            {"dp_id": "E5-2_actions", "label": "Actions — circular economy", "type": "narrative"},
            {"dp_id": "E5-3_targets", "label": "Targets — circular economy", "type": "quantitative"},
            {"dp_id": "E5-4_resource_inflows", "label": "Resource inflows", "type": "quantitative"},
            {"dp_id": "E5-5_resource_outflows", "label": "Resource outflows (waste)", "type": "quantitative"},
        ],
        "total_dps": 5,
    },
    "ISSB_S1": {
        "framework": "ISSB", "standard": "S1 — General Sustainability",
        "required_dps": [
            {"dp_id": "S1_governance", "label": "Governance — sustainability oversight", "type": "narrative"},
            {"dp_id": "S1_strategy", "label": "Strategy — risks and opportunities", "type": "narrative"},
            {"dp_id": "S1_risk_mgmt", "label": "Risk management processes", "type": "narrative"},
            {"dp_id": "S1_metrics_targets", "label": "Metrics and targets", "type": "quantitative"},
        ],
        "total_dps": 4,
    },
    "ISSB_S2": {
        "framework": "ISSB", "standard": "S2 — Climate-related Disclosures",
        "required_dps": [
            {"dp_id": "S2_governance", "label": "Climate governance", "type": "narrative"},
            {"dp_id": "S2_strategy_risks", "label": "Climate-related risks and opportunities", "type": "narrative"},
            {"dp_id": "S2_scenario_analysis", "label": "Climate resilience — scenario analysis", "type": "quantitative"},
            {"dp_id": "S2_scope1", "label": "Absolute gross Scope 1 GHG emissions", "type": "quantitative"},
            {"dp_id": "S2_scope2", "label": "Absolute gross Scope 2 GHG emissions", "type": "quantitative"},
            {"dp_id": "S2_scope3", "label": "Scope 3 GHG emissions", "type": "quantitative"},
            {"dp_id": "S2_cross_industry_metrics", "label": "Cross-industry metric disclosures", "type": "quantitative"},
            {"dp_id": "S2_transition_plan", "label": "Transition plan disclosures", "type": "narrative"},
        ],
        "total_dps": 8,
    },
    "TCFD": {
        "framework": "TCFD", "standard": "Task Force on Climate-related Financial Disclosures",
        "required_dps": [
            {"dp_id": "TCFD_gov_board", "label": "Governance — Board oversight", "type": "narrative"},
            {"dp_id": "TCFD_gov_mgmt", "label": "Governance — Management role", "type": "narrative"},
            {"dp_id": "TCFD_str_risks", "label": "Strategy — Climate risks and opportunities", "type": "narrative"},
            {"dp_id": "TCFD_str_impact", "label": "Strategy — Impact on business/strategy", "type": "narrative"},
            {"dp_id": "TCFD_str_resilience", "label": "Strategy — Resilience of strategy", "type": "narrative"},
            {"dp_id": "TCFD_rm_identify", "label": "Risk management — Identifying risks", "type": "narrative"},
            {"dp_id": "TCFD_rm_manage", "label": "Risk management — Managing risks", "type": "narrative"},
            {"dp_id": "TCFD_rm_integrate", "label": "Risk management — Integration", "type": "narrative"},
            {"dp_id": "TCFD_mt_metrics", "label": "Metrics — Climate-related metrics", "type": "quantitative"},
            {"dp_id": "TCFD_mt_scope123", "label": "Metrics — Scope 1, 2, 3 emissions", "type": "quantitative"},
            {"dp_id": "TCFD_mt_targets", "label": "Metrics — Climate targets", "type": "quantitative"},
        ],
        "total_dps": 11,
    },
    "SFDR_PAI": {
        "framework": "SFDR", "standard": "Principal Adverse Impact Indicators",
        "required_dps": [
            {"dp_id": "PAI_1_ghg_scope123", "label": "PAI 1 — GHG emissions (Scope 1+2+3)", "type": "quantitative"},
            {"dp_id": "PAI_2_carbon_footprint", "label": "PAI 2 — Carbon footprint", "type": "quantitative"},
            {"dp_id": "PAI_3_ghg_intensity", "label": "PAI 3 — GHG intensity of investees", "type": "quantitative"},
            {"dp_id": "PAI_4_fossil_fuel", "label": "PAI 4 — Exposure to fossil fuel companies", "type": "quantitative"},
            {"dp_id": "PAI_5_energy_non_renewable", "label": "PAI 5 — Non-renewable energy share", "type": "quantitative"},
            {"dp_id": "PAI_6_energy_intensity", "label": "PAI 6 — Energy consumption intensity per sector", "type": "quantitative"},
            {"dp_id": "PAI_7_biodiversity", "label": "PAI 7 — Activities affecting biodiversity", "type": "quantitative"},
            {"dp_id": "PAI_8_water_emissions", "label": "PAI 8 — Emissions to water", "type": "quantitative"},
            {"dp_id": "PAI_9_hazardous_waste", "label": "PAI 9 — Hazardous waste ratio", "type": "quantitative"},
            {"dp_id": "PAI_10_ungc_oecd", "label": "PAI 10 — UN GC / OECD violations", "type": "quantitative"},
            {"dp_id": "PAI_11_ungc_processes", "label": "PAI 11 — Lack of compliance processes", "type": "quantitative"},
            {"dp_id": "PAI_12_gender_pay_gap", "label": "PAI 12 — Gender pay gap", "type": "quantitative"},
            {"dp_id": "PAI_13_board_diversity", "label": "PAI 13 — Board gender diversity", "type": "quantitative"},
            {"dp_id": "PAI_14_controversial_weapons", "label": "PAI 14 — Controversial weapons exposure", "type": "quantitative"},
        ],
        "total_dps": 14,
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class DataPointStatus:
    """Status of a single disclosure data point."""
    dp_id: str
    label: str
    dp_type: str  # "narrative" | "quantitative"
    provided: bool
    value: Optional[float] = None
    quality: str = "not_assessed"  # "high" | "medium" | "low" | "not_assessed"


@dataclass
class FrameworkAssessment:
    """Assessment for a single framework."""
    framework_id: str
    framework: str
    standard: str
    total_required: int
    provided_count: int
    missing_count: int
    completeness_pct: float
    data_points: list[DataPointStatus]
    missing_dps: list[dict]
    readiness: str  # "compliant" | "near_compliant" | "partial" | "early_stage"


@dataclass
class CompletenessResult:
    """Overall disclosure completeness assessment."""
    entity_name: str
    reporting_year: int
    frameworks_assessed: int
    overall_completeness_pct: float
    overall_readiness: str
    framework_results: list[FrameworkAssessment]
    priority_gaps: list[dict]  # Top gaps sorted by regulatory urgency
    cross_framework_coverage: dict[str, float]  # {framework: pct}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class DisclosureCompletenessEngine:
    """Assess completeness of sustainability disclosures across frameworks."""

    def assess(
        self,
        entity_name: str,
        provided_dps: dict[str, float],  # {dp_id: value_or_1_for_narrative}
        frameworks: list[str] = None,  # None = all
        reporting_year: int = 2024,
    ) -> CompletenessResult:
        """Assess disclosure completeness."""
        if frameworks is None:
            frameworks = list(FRAMEWORK_REQUIREMENTS.keys())

        framework_results = []
        all_missing = []

        for fw_id in frameworks:
            fw = FRAMEWORK_REQUIREMENTS.get(fw_id)
            if not fw:
                continue

            dps = []
            missing = []
            provided_count = 0

            for req_dp in fw["required_dps"]:
                dp_id = req_dp["dp_id"]
                has_value = dp_id in provided_dps

                if has_value:
                    provided_count += 1
                    quality = "high" if provided_dps[dp_id] > 0 else "low"
                else:
                    missing.append({
                        "dp_id": dp_id,
                        "label": req_dp["label"],
                        "framework_id": fw_id,
                        "framework": fw["framework"],
                        "type": req_dp["type"],
                    })
                    quality = "not_assessed"

                dps.append(DataPointStatus(
                    dp_id=dp_id,
                    label=req_dp["label"],
                    dp_type=req_dp["type"],
                    provided=has_value,
                    value=provided_dps.get(dp_id),
                    quality=quality,
                ))

            total = fw["total_dps"]
            pct = (provided_count / total * 100) if total > 0 else 0

            if pct >= 90:
                readiness = "compliant"
            elif pct >= 70:
                readiness = "near_compliant"
            elif pct >= 40:
                readiness = "partial"
            else:
                readiness = "early_stage"

            framework_results.append(FrameworkAssessment(
                framework_id=fw_id,
                framework=fw["framework"],
                standard=fw["standard"],
                total_required=total,
                provided_count=provided_count,
                missing_count=len(missing),
                completeness_pct=round(pct, 1),
                data_points=dps,
                missing_dps=missing,
                readiness=readiness,
            ))

            all_missing.extend(missing)

        # Overall stats
        total_req = sum(fr.total_required for fr in framework_results)
        total_prov = sum(fr.provided_count for fr in framework_results)
        overall_pct = (total_prov / total_req * 100) if total_req > 0 else 0

        if overall_pct >= 85:
            overall_readiness = "compliant"
        elif overall_pct >= 60:
            overall_readiness = "near_compliant"
        elif overall_pct >= 30:
            overall_readiness = "partial"
        else:
            overall_readiness = "early_stage"

        # Priority gaps — regulatory urgency weighting
        urgency = {"CSRD/ESRS": 4, "ISSB": 3, "SFDR": 3, "TCFD": 2}
        priority_gaps = sorted(
            all_missing,
            key=lambda g: urgency.get(g["framework"], 1),
            reverse=True,
        )[:20]

        cross_fw = {fr.framework_id: fr.completeness_pct for fr in framework_results}

        return CompletenessResult(
            entity_name=entity_name,
            reporting_year=reporting_year,
            frameworks_assessed=len(framework_results),
            overall_completeness_pct=round(overall_pct, 1),
            overall_readiness=overall_readiness,
            framework_results=framework_results,
            priority_gaps=priority_gaps,
            cross_framework_coverage=cross_fw,
        )

    def get_framework_requirements(self) -> dict[str, dict]:
        return FRAMEWORK_REQUIREMENTS

    def get_framework_list(self) -> list[dict]:
        return [
            {"id": k, "framework": v["framework"], "standard": v["standard"], "total_dps": v["total_dps"]}
            for k, v in FRAMEWORK_REQUIREMENTS.items()
        ]
