"""
CSRD Auto-Population Engine
=============================
Automatically populates CSRD / ESRS disclosure data points from existing
module outputs. Maps calculated KPIs from climate risk, ECL, PCAF, nature
risk, supply chain, social registry, and consumer protection modules into
ESRS E1-E5, S1-S4, G1 data point slots.

Sprint 2 — P1-4: Added ESRS S2 (Workers in Value Chain, 12 DPs),
S3 (Affected Communities, 8 DPs), S4 (Consumers and End-Users, 6 DPs).
Source modules: supply_chain, social_registry, consumer_protection.

References:
- ESRS Implementation Guidance 3 (IG3) — quantitative data points
- EFRAG ESRS Set 1 (2023) — disclosure requirements
- CSRD Directive 2022/2464 — double materiality
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — ESRS Data Point Mappings
# ---------------------------------------------------------------------------

# Maps platform module outputs → ESRS data points
ESRS_MAPPINGS: dict[str, dict] = {
    # E1 — Climate Change
    "E1-6_GHG_scope1": {
        "esrs": "E1", "dr": "E1-6", "paragraph": "44(a)",
        "label": "Gross Scope 1 GHG emissions",
        "unit": "tCO2e",
        "source_module": "carbon_calculator",
        "source_field": "scope1_total_tco2e",
    },
    "E1-6_GHG_scope2_lb": {
        "esrs": "E1", "dr": "E1-6", "paragraph": "44(b)",
        "label": "Gross Scope 2 GHG emissions (location-based)",
        "unit": "tCO2e",
        "source_module": "carbon_calculator",
        "source_field": "scope2_location_tco2e",
    },
    "E1-6_GHG_scope2_mb": {
        "esrs": "E1", "dr": "E1-6", "paragraph": "44(c)",
        "label": "Gross Scope 2 GHG emissions (market-based)",
        "unit": "tCO2e",
        "source_module": "carbon_calculator",
        "source_field": "scope2_market_tco2e",
    },
    "E1-6_GHG_scope3_total": {
        "esrs": "E1", "dr": "E1-6", "paragraph": "51",
        "label": "Total Scope 3 GHG emissions",
        "unit": "tCO2e",
        "source_module": "carbon_calculator",
        "source_field": "scope3_total_tco2e",
    },
    "E1-6_GHG_intensity_revenue": {
        "esrs": "E1", "dr": "E1-6", "paragraph": "53",
        "label": "GHG intensity per net revenue",
        "unit": "tCO2e/EUR M",
        "source_module": "carbon_calculator",
        "source_field": "intensity_tco2e_per_m_revenue",
    },
    "E1-9_carbon_price_internal": {
        "esrs": "E1", "dr": "E1-9", "paragraph": "67",
        "label": "Internal carbon price applied",
        "unit": "EUR/tCO2e",
        "source_module": "scenario_analysis",
        "source_field": "carbon_price_eur_tco2e",
    },
    # E1 financial effects
    "E1-9_transition_risk_eur": {
        "esrs": "E1", "dr": "E1-9", "paragraph": "69",
        "label": "Potential financial effects — transition risks",
        "unit": "EUR",
        "source_module": "climate_risk",
        "source_field": "transition_risk_eur",
    },
    "E1-9_physical_risk_eur": {
        "esrs": "E1", "dr": "E1-9", "paragraph": "70",
        "label": "Potential financial effects — physical risks",
        "unit": "EUR",
        "source_module": "climate_risk",
        "source_field": "physical_risk_eur",
    },
    # E2 — Pollution
    "E2-4_pollutant_air": {
        "esrs": "E2", "dr": "E2-4", "paragraph": "28",
        "label": "Pollutants emitted to air",
        "unit": "tonnes",
        "source_module": "pollution_register",
        "source_field": "air_pollutants_tonnes",
    },
    # E3 — Water
    "E3-4_water_consumption": {
        "esrs": "E3", "dr": "E3-4", "paragraph": "28",
        "label": "Total water consumption",
        "unit": "m3",
        "source_module": "nature_risk",
        "source_field": "water_consumption_m3",
    },
    # E4 — Biodiversity
    "E4-5_land_use_change": {
        "esrs": "E4", "dr": "E4-5", "paragraph": "33",
        "label": "Total land-use change",
        "unit": "hectares",
        "source_module": "nature_risk",
        "source_field": "land_use_change_ha",
    },
    # E5 — Circular Economy
    "E5-5_waste_generated": {
        "esrs": "E5", "dr": "E5-5", "paragraph": "37",
        "label": "Total waste generated",
        "unit": "tonnes",
        "source_module": "waste_register",
        "source_field": "total_waste_tonnes",
    },
    # PCAF / Financed Emissions
    "E1_financed_emissions": {
        "esrs": "E1", "dr": "E1-6", "paragraph": "financed",
        "label": "Financed emissions (PCAF)",
        "unit": "tCO2e",
        "source_module": "pcaf_calculator",
        "source_field": "total_financed_tco2e",
    },
    "E1_waci": {
        "esrs": "E1", "dr": "E1-6", "paragraph": "waci",
        "label": "Weighted Average Carbon Intensity",
        "unit": "tCO2e/EUR M revenue",
        "source_module": "pcaf_calculator",
        "source_field": "waci_tco2e_per_m",
    },

    # ── S2 — Workers in the Value Chain (ESRS S2, EFRAG IG3) ──────────────
    # S2-1: Policies related to value chain workers
    "S2-1_policy_coverage_pct": {
        "esrs": "S2", "dr": "S2-1", "paragraph": "11",
        "label": "Share of value chain workers covered by supplier code of conduct",
        "unit": "%",
        "source_module": "supply_chain",
        "source_field": "supplier_code_of_conduct_coverage_pct",
    },
    "S2-1_audit_coverage_pct": {
        "esrs": "S2", "dr": "S2-1", "paragraph": "12",
        "label": "Share of tier-1 suppliers audited on labour standards",
        "unit": "%",
        "source_module": "supply_chain",
        "source_field": "supplier_labour_audit_pct",
    },
    # S2-4: Taking action on material impacts — working conditions
    "S2-4_work_related_injuries": {
        "esrs": "S2", "dr": "S2-4", "paragraph": "35(a)",
        "label": "Number of work-related injuries (value chain workers)",
        "unit": "count",
        "source_module": "supply_chain",
        "source_field": "vc_work_related_injuries_count",
    },
    "S2-4_injury_rate_per_mhrs": {
        "esrs": "S2", "dr": "S2-4", "paragraph": "35(b)",
        "label": "Rate of recordable work-related injuries per million hours worked",
        "unit": "per million hours",
        "source_module": "supply_chain",
        "source_field": "vc_injury_rate_per_m_hours",
    },
    "S2-4_work_related_fatalities": {
        "esrs": "S2", "dr": "S2-4", "paragraph": "35(c)",
        "label": "Number of work-related fatalities (value chain workers)",
        "unit": "count",
        "source_module": "supply_chain",
        "source_field": "vc_work_related_fatalities",
    },
    "S2-4_days_lost_per_injury": {
        "esrs": "S2", "dr": "S2-4", "paragraph": "35(d)",
        "label": "Average days lost per work-related injury",
        "unit": "days",
        "source_module": "supply_chain",
        "source_field": "vc_avg_days_lost_per_injury",
    },
    "S2-4_contract_worker_pct": {
        "esrs": "S2", "dr": "S2-4", "paragraph": "36",
        "label": "Percentage of contract workers in material value chain operations",
        "unit": "%",
        "source_module": "supply_chain",
        "source_field": "vc_contract_worker_pct",
    },
    "S2-4_living_wage_coverage_pct": {
        "esrs": "S2", "dr": "S2-4", "paragraph": "37",
        "label": "Share of value chain workers earning above living wage",
        "unit": "%",
        "source_module": "supply_chain",
        "source_field": "vc_living_wage_coverage_pct",
    },
    # S2-5: Targets — diversity and social dialogue
    "S2-5_gender_pay_gap_vc": {
        "esrs": "S2", "dr": "S2-5", "paragraph": "43",
        "label": "Unadjusted gender pay gap — key value chain categories",
        "unit": "%",
        "source_module": "supply_chain",
        "source_field": "vc_gender_pay_gap_pct",
    },
    "S2-5_social_dialogue_coverage_pct": {
        "esrs": "S2", "dr": "S2-5", "paragraph": "44",
        "label": "Percentage of value chain workers covered by collective agreements",
        "unit": "%",
        "source_module": "supply_chain",
        "source_field": "vc_collective_agreement_coverage_pct",
    },
    # S2-3: Processes for remediation
    "S2-3_grievance_cases_resolved": {
        "esrs": "S2", "dr": "S2-3", "paragraph": "25",
        "label": "Number of grievance cases raised and resolved (value chain)",
        "unit": "count",
        "source_module": "supply_chain",
        "source_field": "vc_grievance_cases_resolved",
    },
    "S2-3_grievance_resolution_rate_pct": {
        "esrs": "S2", "dr": "S2-3", "paragraph": "26",
        "label": "Grievance resolution rate — value chain workers",
        "unit": "%",
        "source_module": "supply_chain",
        "source_field": "vc_grievance_resolution_rate_pct",
    },

    # ── S3 — Affected Communities (ESRS S3, EFRAG IG3) ────────────────────
    # S3-1: Material impacts and dependencies on affected communities
    "S3-1_significant_ops_pct": {
        "esrs": "S3", "dr": "S3-1", "paragraph": "15",
        "label": "Percentage of operations assessed for significant community impact",
        "unit": "%",
        "source_module": "social_registry",
        "source_field": "ops_assessed_community_impact_pct",
    },
    "S3-1_indigenous_land_ops_pct": {
        "esrs": "S3", "dr": "S3-1", "paragraph": "16",
        "label": "Share of operations on or adjacent to indigenous peoples' land",
        "unit": "%",
        "source_module": "social_registry",
        "source_field": "ops_indigenous_land_pct",
    },
    # S3-2: Processes for engaging with affected communities
    "S3-2_community_engagement_pct": {
        "esrs": "S3", "dr": "S3-2", "paragraph": "22",
        "label": "Percentage of affected operations with formal community engagement",
        "unit": "%",
        "source_module": "social_registry",
        "source_field": "community_engagement_ops_pct",
    },
    "S3-2_fpic_operations_pct": {
        "esrs": "S3", "dr": "S3-2", "paragraph": "23",
        "label": "Share of relevant operations with FPIC processes applied",
        "unit": "%",
        "source_module": "social_registry",
        "source_field": "fpic_operations_pct",
    },
    # S3-3: Processes for remediation
    "S3-3_community_grievances_received": {
        "esrs": "S3", "dr": "S3-3", "paragraph": "28",
        "label": "Number of community grievances received in reporting period",
        "unit": "count",
        "source_module": "social_registry",
        "source_field": "community_grievances_received",
    },
    "S3-3_community_grievances_resolved": {
        "esrs": "S3", "dr": "S3-3", "paragraph": "29",
        "label": "Number of community grievances resolved in reporting period",
        "unit": "count",
        "source_module": "social_registry",
        "source_field": "community_grievances_resolved",
    },
    "S3-3_human_rights_incidents": {
        "esrs": "S3", "dr": "S3-3", "paragraph": "30",
        "label": "Number of confirmed human rights incidents in communities",
        "unit": "count",
        "source_module": "social_registry",
        "source_field": "community_human_rights_incidents",
    },
    # S3-4: Targets related to managing material impacts
    "S3-4_community_investment_eur": {
        "esrs": "S3", "dr": "S3-4", "paragraph": "35",
        "label": "Total community investment / social contributions (EUR)",
        "unit": "EUR",
        "source_module": "social_registry",
        "source_field": "community_investment_eur",
    },

    # ── S4 — Consumers and End-Users (ESRS S4, EFRAG IG3) ─────────────────
    # S4-1: Material impacts and dependencies on consumers
    "S4-1_product_safety_incidents": {
        "esrs": "S4", "dr": "S4-1", "paragraph": "14",
        "label": "Number of product safety incidents reported in period",
        "unit": "count",
        "source_module": "consumer_protection",
        "source_field": "product_safety_incidents",
    },
    "S4-1_product_recall_events": {
        "esrs": "S4", "dr": "S4-1", "paragraph": "15",
        "label": "Number of product recall events",
        "unit": "count",
        "source_module": "consumer_protection",
        "source_field": "product_recall_events",
    },
    # S4-2: Processes for engaging with consumers
    "S4-2_consumer_satisfaction_score": {
        "esrs": "S4", "dr": "S4-2", "paragraph": "22",
        "label": "Consumer satisfaction score (NPS or equivalent, 0-100)",
        "unit": "score",
        "source_module": "consumer_protection",
        "source_field": "consumer_satisfaction_score",
    },
    # S4-3: Processes for remediation of negative impacts on consumers
    "S4-3_substantiated_complaints": {
        "esrs": "S4", "dr": "S4-3", "paragraph": "27",
        "label": "Number of substantiated consumer complaints in period",
        "unit": "count",
        "source_module": "consumer_protection",
        "source_field": "substantiated_consumer_complaints",
    },
    "S4-3_complaint_resolution_rate_pct": {
        "esrs": "S4", "dr": "S4-3", "paragraph": "28",
        "label": "Consumer complaint resolution rate",
        "unit": "%",
        "source_module": "consumer_protection",
        "source_field": "consumer_complaint_resolution_rate_pct",
    },
    # S4-4: Targets — data privacy and consumer rights
    "S4-4_data_privacy_breaches": {
        "esrs": "S4", "dr": "S4-4", "paragraph": "33",
        "label": "Number of personal data breaches reported to supervisory authority",
        "unit": "count",
        "source_module": "consumer_protection",
        "source_field": "personal_data_breaches_reported",
    },
    "S4-4_data_subjects_affected": {
        "esrs": "S4", "dr": "S4-4", "paragraph": "34",
        "label": "Number of data subjects affected by personal data breaches",
        "unit": "count",
        "source_module": "consumer_protection",
        "source_field": "data_subjects_affected_by_breach",
    },
    "S4-4_regulatory_fines_data_eur": {
        "esrs": "S4", "dr": "S4-4", "paragraph": "35",
        "label": "Fines for data protection violations (EUR)",
        "unit": "EUR",
        "source_module": "consumer_protection",
        "source_field": "data_protection_fines_eur",
    },
}

# Required minimum DPs for each ESRS standard (EFRAG IG3 phase-in minimums)
ESRS_MINIMUMS: dict[str, int] = {
    "E1": 15, "E2": 6, "E3": 5, "E4": 8, "E5": 5,
    "S1": 10, "S2": 12, "S3": 8, "S4": 6, "G1": 4,
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ModuleOutput:
    """Key-value output from a platform module."""
    module: str
    field: str
    value: float
    unit: str = ""
    year: int = 2024


@dataclass
class PopulatedDataPoint:
    """An ESRS data point populated from module output."""
    dp_id: str
    esrs: str
    dr: str
    paragraph: str
    label: str
    unit: str
    value: float
    source_module: str
    source_field: str
    confidence: str  # "high" (direct match) | "medium" (derived) | "low" (estimated)
    year: int


@dataclass
class AutoPopulateResult:
    """CSRD auto-population assessment."""
    entity_name: str
    reporting_year: int
    populated_dps: list[PopulatedDataPoint]
    total_mappable_dps: int
    populated_count: int
    population_rate_pct: float
    gaps: list[dict]  # [{dp_id, label, esrs, reason}]
    esrs_coverage: dict[str, dict]  # {esrs: {total, populated, pct}}
    readiness_rating: str  # "high" | "medium" | "low"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CSRDAutoPopulateEngine:
    """Auto-populate CSRD/ESRS disclosures from platform module outputs."""

    def populate(
        self,
        entity_name: str,
        module_outputs: list[ModuleOutput],
        reporting_year: int = 2024,
    ) -> AutoPopulateResult:
        """Map module outputs to ESRS data points."""
        # Build lookup: (module, field) -> ModuleOutput
        output_map = {}
        for mo in module_outputs:
            output_map[(mo.module, mo.field)] = mo

        populated = []
        gaps = []

        for dp_id, mapping in ESRS_MAPPINGS.items():
            key = (mapping["source_module"], mapping["source_field"])
            mo = output_map.get(key)

            if mo is not None:
                populated.append(PopulatedDataPoint(
                    dp_id=dp_id,
                    esrs=mapping["esrs"],
                    dr=mapping["dr"],
                    paragraph=mapping["paragraph"],
                    label=mapping["label"],
                    unit=mapping["unit"],
                    value=mo.value,
                    source_module=mo.module,
                    source_field=mo.field,
                    confidence="high",
                    year=mo.year,
                ))
            else:
                gaps.append({
                    "dp_id": dp_id,
                    "label": mapping["label"],
                    "esrs": mapping["esrs"],
                    "dr": mapping["dr"],
                    "source_module": mapping["source_module"],
                    "reason": f"No data from {mapping['source_module']}.{mapping['source_field']}",
                })

        total = len(ESRS_MAPPINGS)
        pop_count = len(populated)
        rate = (pop_count / total * 100) if total > 0 else 0

        # ESRS-level coverage
        esrs_cov = {}
        for esrs in set(m["esrs"] for m in ESRS_MAPPINGS.values()):
            esrs_total = sum(1 for m in ESRS_MAPPINGS.values() if m["esrs"] == esrs)
            esrs_pop = sum(1 for p in populated if p.esrs == esrs)
            esrs_cov[esrs] = {
                "total": esrs_total,
                "populated": esrs_pop,
                "pct": round(esrs_pop / esrs_total * 100, 1) if esrs_total > 0 else 0,
            }

        # Readiness
        if rate >= 70:
            readiness = "high"
        elif rate >= 40:
            readiness = "medium"
        else:
            readiness = "low"

        return AutoPopulateResult(
            entity_name=entity_name,
            reporting_year=reporting_year,
            populated_dps=populated,
            total_mappable_dps=total,
            populated_count=pop_count,
            population_rate_pct=round(rate, 1),
            gaps=gaps,
            esrs_coverage=esrs_cov,
            readiness_rating=readiness,
        )

    def get_mappings(self) -> dict[str, dict]:
        return ESRS_MAPPINGS

    def get_esrs_minimums(self) -> dict[str, int]:
        return ESRS_MINIMUMS
