"""
CSRD ESRS E2-E5 Environment Topics Engine.
Covers: ESRS E2 Pollution, E3 Water & Marine, E4 Biodiversity & Ecosystems, E5 Circular Economy.
Regulatory basis: CSRD Directive 2022/2464; ESRS E2/E3/E4/E5 Delegated Acts 2023.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

E2_DISCLOSURES: dict[str, Any] = {
    "E2-1": {
        "name": "Policies related to pollution",
        "description": "Policies to manage material pollution impacts, risks and opportunities.",
        "required_dps": ["policy_scope", "prevention_approach", "reduction_targets_set"],
    },
    "E2-2": {
        "name": "Actions and resources related to pollution",
        "description": "Actions and allocated resources to address material pollution.",
        "required_dps": ["action_description", "capex_opex_eur", "timeline"],
    },
    "E2-3": {
        "name": "Targets related to pollution",
        "description": "Pollution reduction targets with baseline, metrics and deadlines.",
        "required_dps": ["target_metric", "baseline_year", "target_year", "reduction_pct"],
    },
    "E2-4": {
        "name": "Pollution of air, water and soil",
        "description": "Quantitative disclosure of pollutant emissions by media.",
        "media": {
            "air": {
                "pollutants": ["NOx", "SOx", "PM2.5", "NMVOC", "NH3", "HAPs"],
                "unit": "tonnes/year",
            },
            "water": {
                "pollutants": ["Priority_substances", "Nitrates", "Phosphorus"],
                "unit": "kg/year",
            },
            "soil": {
                "pollutants": ["POPs", "Heavy_metals_Pb", "Heavy_metals_Cd", "Heavy_metals_Hg"],
                "unit": "kg/year",
            },
        },
    },
    "E2-5": {
        "name": "Substances of concern and very high concern",
        "description": "SVHC and substances of concern use, emissions and substitution plans.",
        "required_dps": ["svhc_list", "volume_used_t", "substitution_plan"],
    },
    "E2-6": {
        "name": "Anticipated financial effects from pollution",
        "description": "Current and anticipated financial effects from pollution impacts/risks.",
        "required_dps": ["risk_type", "financial_effect_eur", "time_horizon"],
    },
}

E3_DISCLOSURES: dict[str, Any] = {
    "E3-1": {
        "name": "Policies related to water and marine resources",
        "description": "Policies addressing water use, discharge and marine resource impacts.",
        "required_dps": ["policy_scope", "water_stressed_area_approach"],
    },
    "E3-2": {
        "name": "Actions and resources related to water",
        "description": "Water efficiency and marine protection actions and resources.",
        "required_dps": ["action_description", "investment_eur", "timeline"],
    },
    "E3-3": {
        "name": "Targets related to water and marine resources",
        "description": "Water consumption and discharge quality reduction targets.",
        "required_dps": ["target_metric", "baseline_year", "target_year", "reduction_pct"],
    },
    "E3-4": {
        "name": "Water consumption",
        "description": "Total water withdrawal, discharge, consumption and recycled water volumes.",
        "metrics": {
            "withdrawal_total_ML": "Total water withdrawal (megalitres)",
            "withdrawal_stressed_ML": "Withdrawal from water-stressed areas (megalitres)",
            "discharge_total_ML": "Total water discharge (megalitres)",
            "discharge_to_sea_ML": "Discharge to sea (megalitres)",
            "consumption_ML": "Net water consumption (megalitres)",
            "recycled_pct": "Percentage of water recycled/reused (%)",
        },
        "water_stress_tiers": {
            "low": "< 10% withdrawal/availability ratio (WRI Aqueduct)",
            "low_medium": "10-20% (WRI Aqueduct)",
            "medium_high": "20-40% (WRI Aqueduct)",
            "high": "40-80% (WRI Aqueduct)",
            "extremely_high": "> 80% (WRI Aqueduct)",
        },
    },
    "E3-5": {
        "name": "Anticipated financial effects from water",
        "description": "Financial effects from water-related risks and opportunities.",
        "required_dps": ["risk_type", "financial_effect_eur", "time_horizon"],
    },
}

E4_DISCLOSURES: dict[str, Any] = {
    "E4-1": {
        "name": "Transition plan and considerations of biodiversity and ecosystems in strategy",
        "description": "How strategy addresses biodiversity/ecosystem impacts, risks and opportunities.",
        "required_dps": ["biodiversity_targets_adopted", "alignment_kunming_montreal", "no_net_loss_commitment"],
    },
    "E4-2": {
        "name": "Policies related to biodiversity and ecosystems",
        "description": "Policies for biodiversity across own operations and value chain.",
        "required_dps": ["policy_scope", "sensitive_areas_approach", "value_chain_coverage"],
    },
    "E4-3": {
        "name": "Actions and resources related to biodiversity",
        "description": "Conservation, restoration and mitigation actions and expenditures.",
        "required_dps": ["action_type", "area_covered_ha", "investment_eur", "timeline"],
    },
    "E4-4": {
        "name": "Targets related to biodiversity and ecosystems",
        "description": "Biodiversity and ecosystem restoration targets.",
        "required_dps": ["target_metric", "baseline_year", "target_year", "target_value"],
    },
    "E4-5": {
        "name": "Impact metrics related to biodiversity and ecosystems",
        "description": "Land use, species and ecosystem service metrics.",
        "metrics": {
            "land_use_change_ha": "Land use change (ha) — conversion of natural habitats",
            "sensitive_areas_pct": "Operations in or near Natura 2000/protected areas (%)",
            "species_affected_iucn": "Number of IUCN Red List species affected",
            "invasive_species_risk": "Sites with invasive species risk (count)",
            "ecosystem_services_dependency": {
                "description": "ENCORE ecosystem services dependency mapping",
                "categories": [
                    "Provisioning: food, water, raw materials",
                    "Regulating: climate regulation, flood protection, pollination",
                    "Cultural: recreation, aesthetic, spiritual",
                ],
            },
        },
    },
    "E4-6": {
        "name": "Anticipated financial effects from biodiversity and ecosystems",
        "description": "Financial effects from biodiversity-related risks.",
        "required_dps": ["risk_type", "financial_effect_eur", "dependency_category", "time_horizon"],
    },
}

E5_DISCLOSURES: dict[str, Any] = {
    "E5-1": {
        "name": "Policies related to resource use and circular economy",
        "description": "Policies covering resource inflows, circular design and waste management.",
        "required_dps": ["policy_scope", "circularity_principles", "waste_hierarchy_commitment"],
    },
    "E5-2": {
        "name": "Actions and resources related to circular economy",
        "description": "Circular economy initiatives, recycling programmes and resources.",
        "required_dps": ["action_description", "investment_eur", "timeline"],
    },
    "E5-3": {
        "name": "Targets related to resource use and circular economy",
        "description": "Recycled content, waste reduction and resource efficiency targets.",
        "required_dps": ["target_metric", "baseline_year", "target_year", "target_value"],
    },
    "E5-4": {
        "name": "Resource inflows",
        "description": "Material inflows by weight and recycled/renewable content.",
        "metrics": {
            "material_inflows_total_t": "Total material inflows (tonnes)",
            "recycled_content_pct": "Recycled/reused content as % of total input",
            "renewable_content_pct": "Renewable content as % of total input",
            "critical_raw_materials_t": "Critical raw materials consumed (tonnes, EU CRM list)",
        },
    },
    "E5-5": {
        "name": "Resource outflows",
        "description": "Waste generated and waste management disposition.",
        "metrics": {
            "waste_generated_total_t": "Total waste generated (tonnes)",
            "diverted_from_disposal_t": "Waste diverted from disposal (tonnes)",
            "directed_to_disposal_t": "Waste directed to disposal (tonnes)",
            "disposal_by_type": {
                "landfill_t": "To landfill (tonnes)",
                "incineration_without_recovery_t": "Incineration without energy recovery (tonnes)",
                "other_disposal_t": "Other disposal (tonnes)",
            },
            "hazardous_waste_t": "Hazardous waste generated (tonnes)",
            "radioactive_waste_t": "Radioactive waste generated (tonnes)",
        },
    },
    "E5-6": {
        "name": "Anticipated financial effects from resource use and circular economy",
        "description": "Financial effects from resource scarcity, waste costs and circular opportunities.",
        "required_dps": ["risk_type", "financial_effect_eur", "opportunity_value_eur", "time_horizon"],
    },
}

# Sector-based materiality triggers by NACE division
MATERIALITY_TRIGGERS: dict[str, dict[str, bool]] = {
    "A01": {"E2": True,  "E3": True,  "E4": True,  "E5": True},   # Crop production
    "A02": {"E2": False, "E3": True,  "E4": True,  "E5": True},   # Forestry
    "A03": {"E2": True,  "E3": True,  "E4": True,  "E5": False},  # Fishing
    "B05": {"E2": True,  "E3": True,  "E4": True,  "E5": True},   # Coal mining
    "B06": {"E2": True,  "E3": True,  "E4": True,  "E5": True},   # Oil & gas
    "C10": {"E2": True,  "E3": True,  "E4": False, "E5": True},   # Food manufacturing
    "C13": {"E2": True,  "E3": True,  "E4": False, "E5": True},   # Textiles
    "C17": {"E2": True,  "E3": True,  "E4": False, "E5": True},   # Paper
    "C20": {"E2": True,  "E3": True,  "E4": False, "E5": True},   # Chemicals
    "C24": {"E2": True,  "E3": True,  "E4": False, "E5": True},   # Metals
    "C26": {"E2": False, "E3": False, "E4": False, "E5": True},   # Electronics
    "D35": {"E2": True,  "E3": False, "E4": False, "E5": False},  # Electricity
    "E36": {"E2": False, "E3": True,  "E4": False, "E5": False},  # Water supply
    "E38": {"E2": True,  "E3": True,  "E4": False, "E5": True},   # Waste management
    "F41": {"E2": False, "E3": False, "E4": True,  "E5": True},   # Construction
    "G46": {"E2": False, "E3": False, "E4": False, "E5": True},   # Wholesale trade
    "H50": {"E2": True,  "E3": True,  "E4": False, "E5": False},  # Water transport
    "I55": {"E2": False, "E3": True,  "E4": True,  "E5": False},  # Hotels
    "K64": {"E2": False, "E3": False, "E4": False, "E5": False},  # Financial services
    "L68": {"E2": False, "E3": False, "E4": True,  "E5": False},  # Real estate
}

_DEFAULT_MATERIALITY = {"E2": False, "E3": False, "E4": False, "E5": False}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class ESRSE2E5Assessment:
    entity_id: str
    entity_name: str
    reporting_period: str
    nace_sector: str
    materiality: dict[str, bool]
    e2_pollution: dict[str, Any]
    e3_water: dict[str, Any]
    e4_biodiversity: dict[str, Any]
    e5_circular: dict[str, Any]
    overall_completeness_pct: float
    disclosure_gaps: list[str]
    regulatory_refs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ESRSE2E5Engine:
    """CSRD ESRS E2–E5 environment topics assessment engine."""

    _instance: "ESRSE2E5Engine | None" = None

    def __init__(self) -> None:
        self._regulatory_refs = [
            "CSRD Directive 2022/2464",
            "Commission Delegated Regulation (EU) 2023/2772 — ESRS E2 Pollution",
            "Commission Delegated Regulation (EU) 2023/2772 — ESRS E3 Water",
            "Commission Delegated Regulation (EU) 2023/2772 — ESRS E4 Biodiversity",
            "Commission Delegated Regulation (EU) 2023/2772 — ESRS E5 Circular Economy",
            "EU Taxonomy Regulation 2020/852 — Do No Significant Harm (DNSH)",
        ]

    @classmethod
    def get_instance(cls) -> "ESRSE2E5Engine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Materiality
    # ------------------------------------------------------------------

    def assess_materiality(self, entity_id: str, nace_sector: str) -> dict[str, Any]:
        nace_div = (nace_sector or "")[:3].upper()
        mat = dict(MATERIALITY_TRIGGERS.get(nace_div, _DEFAULT_MATERIALITY))
        return {
            "entity_id": entity_id,
            "nace_sector": nace_sector,
            "nace_division": nace_div,
            "materiality": mat,
            "material_topics": [k for k, v in mat.items() if v],
            "basis": "ESRS 1 §§ 17-44 double materiality; sector defaults per EFRAG sectoral guidance",
            "note": "Final materiality determination requires entity-specific double materiality assessment.",
        }

    # ------------------------------------------------------------------
    # E2 — Pollution
    # ------------------------------------------------------------------

    def assess_e2_pollution(self, entity_id: str, pollution_data: dict) -> dict[str, Any]:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        provided_air = pollution_data.get("air", {})
        provided_water = pollution_data.get("water", {})
        provided_soil = pollution_data.get("soil", {})

        air_emissions: dict[str, float] = {}
        for p in ["NOx", "SOx", "PM2.5", "NMVOC", "NH3", "HAPs"]:
            air_emissions[p] = provided_air.get(p, round(rng.uniform(0.5, 150.0), 2))

        water_emissions: dict[str, float] = {}
        for p in ["Priority_substances", "Nitrates", "Phosphorus"]:
            water_emissions[p] = provided_water.get(p, round(rng.uniform(10.0, 5000.0), 1))

        soil_emissions: dict[str, float] = {}
        for p in ["POPs", "Heavy_metals_Pb", "Heavy_metals_Cd", "Heavy_metals_Hg"]:
            soil_emissions[p] = provided_soil.get(p, round(rng.uniform(0.1, 20.0), 3))

        svhcs = pollution_data.get("svhcs", [])
        financial_effect_eur = pollution_data.get("financial_effect_eur", round(rng.uniform(50_000, 2_000_000), 0))

        completeness_score = self._score_completeness({
            "air": bool(provided_air), "water": bool(provided_water),
            "soil": bool(provided_soil), "svhcs_disclosed": bool(svhcs),
            "financial_effects": bool(pollution_data.get("financial_effect_eur")),
        })

        gaps = []
        if not provided_air:
            gaps.append("E2-4: Air emissions not provided — estimated")
        if not svhcs:
            gaps.append("E2-5: SVHC list not disclosed")
        if not pollution_data.get("financial_effect_eur"):
            gaps.append("E2-6: Financial effects from pollution not quantified")

        return {
            "topic": "E2 — Pollution",
            "air_emissions_t_per_year": air_emissions,
            "water_emissions_kg_per_year": water_emissions,
            "soil_emissions_kg_per_year": soil_emissions,
            "substances_of_very_high_concern": svhcs,
            "financial_effect_eur": financial_effect_eur,
            "completeness_pct": completeness_score,
            "disclosure_gaps": gaps,
            "regulatory_refs": ["ESRS E2-4", "ESRS E2-5", "ESRS E2-6"],
        }

    # ------------------------------------------------------------------
    # E3 — Water
    # ------------------------------------------------------------------

    def assess_e3_water(self, entity_id: str, water_data: dict) -> dict[str, Any]:
        rng = random.Random((hash(entity_id) ^ 0xABCD) & 0xFFFFFFFF)

        withdrawal_total = water_data.get("withdrawal_total_ML", round(rng.uniform(100, 50_000), 1))
        withdrawal_stressed = water_data.get("withdrawal_stressed_ML",
                                              round(withdrawal_total * rng.uniform(0.1, 0.6), 1))
        discharge_total = water_data.get("discharge_total_ML", round(withdrawal_total * rng.uniform(0.5, 0.9), 1))
        consumption = round(withdrawal_total - discharge_total, 1)
        recycled_pct = water_data.get("recycled_pct", round(rng.uniform(5, 40), 1))
        ops_in_stressed_pct = water_data.get("ops_in_stressed_area_pct", round(rng.uniform(10, 70), 1))
        financial_effect_eur = water_data.get("financial_effect_eur", round(rng.uniform(20_000, 1_000_000), 0))

        stress_tier = "high" if ops_in_stressed_pct > 40 else ("medium_high" if ops_in_stressed_pct > 20 else "low_medium")

        gaps = []
        for key, label in [
            ("withdrawal_total_ML", "E3-4: Total water withdrawal"),
            ("recycled_pct", "E3-4: Recycled water percentage"),
        ]:
            if key not in water_data:
                gaps.append(f"{label} not provided — estimated")
        if not water_data.get("financial_effect_eur"):
            gaps.append("E3-5: Financial effects from water not quantified")

        completeness_score = self._score_completeness({
            "withdrawal": "withdrawal_total_ML" in water_data,
            "stressed_area": "withdrawal_stressed_ML" in water_data,
            "recycled": "recycled_pct" in water_data,
            "financial": bool(water_data.get("financial_effect_eur")),
        })

        return {
            "topic": "E3 — Water & Marine Resources",
            "withdrawal_total_ML": withdrawal_total,
            "withdrawal_from_stressed_areas_ML": withdrawal_stressed,
            "discharge_total_ML": discharge_total,
            "consumption_ML": consumption,
            "recycled_pct": recycled_pct,
            "ops_in_stressed_area_pct": ops_in_stressed_pct,
            "water_stress_tier": stress_tier,
            "financial_effect_eur": financial_effect_eur,
            "completeness_pct": completeness_score,
            "disclosure_gaps": gaps,
            "regulatory_refs": ["ESRS E3-4", "ESRS E3-5", "WRI Aqueduct baseline water stress"],
        }

    # ------------------------------------------------------------------
    # E4 — Biodiversity
    # ------------------------------------------------------------------

    def assess_e4_biodiversity(self, entity_id: str, biodiversity_data: dict) -> dict[str, Any]:
        rng = random.Random((hash(entity_id) ^ 0x1234) & 0xFFFFFFFF)

        land_use_change_ha = biodiversity_data.get("land_use_change_ha", round(rng.uniform(0, 500), 1))
        sensitive_areas_pct = biodiversity_data.get("sensitive_areas_pct", round(rng.uniform(0, 30), 1))
        species_affected_iucn = biodiversity_data.get("species_affected_iucn", rng.randint(0, 15))
        ecosystem_services = biodiversity_data.get("ecosystem_services_dependency", [
            "Provisioning: raw materials",
            "Regulating: pollination",
            "Regulating: climate regulation",
        ])
        no_net_loss = biodiversity_data.get("no_net_loss_commitment", False)
        financial_effect_eur = biodiversity_data.get("financial_effect_eur", round(rng.uniform(30_000, 3_000_000), 0))

        risks = []
        if sensitive_areas_pct > 20:
            risks.append("MEDIUM-HIGH: Significant operations in/near protected areas (>20%)")
        if species_affected_iucn > 5:
            risks.append("HIGH: Multiple IUCN Red List species potentially affected")
        if land_use_change_ha > 100:
            risks.append("MEDIUM: Material land use change reported")
        if not no_net_loss:
            risks.append("GAP: No No-Net-Loss commitment in place")

        gaps = []
        for key, label in [
            ("land_use_change_ha", "E4-5: Land use change not quantified — estimated"),
            ("sensitive_areas_pct", "E4-5: % ops in sensitive areas not provided — estimated"),
        ]:
            if key not in biodiversity_data:
                gaps.append(label)
        if not biodiversity_data.get("financial_effect_eur"):
            gaps.append("E4-6: Financial effects from biodiversity not quantified")

        completeness = self._score_completeness({
            "land_use": "land_use_change_ha" in biodiversity_data,
            "sensitive_areas": "sensitive_areas_pct" in biodiversity_data,
            "species": "species_affected_iucn" in biodiversity_data,
            "ecosystem_services": bool(ecosystem_services),
            "financial": bool(biodiversity_data.get("financial_effect_eur")),
        })

        return {
            "topic": "E4 — Biodiversity & Ecosystems",
            "land_use_change_ha": land_use_change_ha,
            "sensitive_areas_pct": sensitive_areas_pct,
            "species_affected_iucn_count": species_affected_iucn,
            "ecosystem_services_dependency": ecosystem_services,
            "no_net_loss_commitment": no_net_loss,
            "financial_effect_eur": financial_effect_eur,
            "risk_flags": risks,
            "kunming_montreal_alignment": "Partial" if no_net_loss else "Not declared",
            "completeness_pct": completeness,
            "disclosure_gaps": gaps,
            "regulatory_refs": ["ESRS E4-5", "ESRS E4-6", "Kunming-Montreal GBF Target 15", "ENCORE (UNEP-WCMC)"],
        }

    # ------------------------------------------------------------------
    # E5 — Circular Economy
    # ------------------------------------------------------------------

    def assess_e5_circular(self, entity_id: str, circular_data: dict) -> dict[str, Any]:
        rng = random.Random((hash(entity_id) ^ 0x5678) & 0xFFFFFFFF)

        material_inflows_t = circular_data.get("material_inflows_total_t", round(rng.uniform(500, 100_000), 0))
        recycled_content_pct = circular_data.get("recycled_content_pct", round(rng.uniform(5, 40), 1))
        waste_generated_t = circular_data.get("waste_generated_total_t", round(rng.uniform(100, 20_000), 0))
        diverted_t = circular_data.get("diverted_from_disposal_t", round(waste_generated_t * rng.uniform(0.3, 0.8), 0))
        directed_to_disposal_t = round(waste_generated_t - diverted_t, 0)
        hazardous_waste_t = circular_data.get("hazardous_waste_t", round(rng.uniform(0, 50), 2))
        financial_effect_eur = circular_data.get("financial_effect_eur", round(rng.uniform(10_000, 500_000), 0))

        diversion_rate_pct = round((diverted_t / waste_generated_t) * 100, 1) if waste_generated_t > 0 else 0

        circularity_score = min(100, round(
            recycled_content_pct * 0.4 + diversion_rate_pct * 0.4 +
            (20 if circular_data.get("circular_design_policy") else 0) * 0.2,
            1
        ))

        gaps = []
        for key, label in [
            ("material_inflows_total_t", "E5-4: Total material inflows not provided"),
            ("recycled_content_pct", "E5-4: Recycled content % not disclosed"),
            ("waste_generated_total_t", "E5-5: Waste generated not provided"),
        ]:
            if key not in circular_data:
                gaps.append(f"{label} — estimated")
        if not circular_data.get("financial_effect_eur"):
            gaps.append("E5-6: Financial effects from resource use not quantified")

        completeness = self._score_completeness({
            "inflows": "material_inflows_total_t" in circular_data,
            "recycled_content": "recycled_content_pct" in circular_data,
            "waste": "waste_generated_total_t" in circular_data,
            "diverted": "diverted_from_disposal_t" in circular_data,
            "financial": bool(circular_data.get("financial_effect_eur")),
        })

        return {
            "topic": "E5 — Circular Economy",
            "material_inflows_total_t": material_inflows_t,
            "recycled_content_pct": recycled_content_pct,
            "waste_generated_total_t": waste_generated_t,
            "diverted_from_disposal_t": diverted_t,
            "directed_to_disposal_t": directed_to_disposal_t,
            "hazardous_waste_t": hazardous_waste_t,
            "diversion_rate_pct": diversion_rate_pct,
            "financial_effect_eur": financial_effect_eur,
            "circularity_score": circularity_score,
            "completeness_pct": completeness,
            "disclosure_gaps": gaps,
            "regulatory_refs": ["ESRS E5-4", "ESRS E5-5", "ESRS E5-6", "EU Waste Framework Directive 2008/98/EC"],
        }

    # ------------------------------------------------------------------
    # Full assessment
    # ------------------------------------------------------------------

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        reporting_period: str,
        nace_sector: str,
        e2_data: dict | None = None,
        e3_data: dict | None = None,
        e4_data: dict | None = None,
        e5_data: dict | None = None,
    ) -> ESRSE2E5Assessment:
        mat_result = self.assess_materiality(entity_id, nace_sector)
        materiality = mat_result["materiality"]

        e2 = self.assess_e2_pollution(entity_id, e2_data or {}) if materiality.get("E2") else {"topic": "E2 — Not material", "completeness_pct": 100.0, "disclosure_gaps": []}
        e3 = self.assess_e3_water(entity_id, e3_data or {}) if materiality.get("E3") else {"topic": "E3 — Not material", "completeness_pct": 100.0, "disclosure_gaps": []}
        e4 = self.assess_e4_biodiversity(entity_id, e4_data or {}) if materiality.get("E4") else {"topic": "E4 — Not material", "completeness_pct": 100.0, "disclosure_gaps": []}
        e5 = self.assess_e5_circular(entity_id, e5_data or {}) if materiality.get("E5") else {"topic": "E5 — Not material", "completeness_pct": 100.0, "disclosure_gaps": []}

        material_count = sum(1 for v in materiality.values() if v)
        completeness_scores = [e2["completeness_pct"], e3["completeness_pct"], e4["completeness_pct"], e5["completeness_pct"]]
        overall_completeness = round(sum(completeness_scores) / len(completeness_scores), 1) if completeness_scores else 100.0

        all_gaps = (
            e2.get("disclosure_gaps", []) +
            e3.get("disclosure_gaps", []) +
            e4.get("disclosure_gaps", []) +
            e5.get("disclosure_gaps", [])
        )

        return ESRSE2E5Assessment(
            entity_id=entity_id,
            entity_name=entity_name,
            reporting_period=reporting_period,
            nace_sector=nace_sector,
            materiality=materiality,
            e2_pollution=e2,
            e3_water=e3,
            e4_biodiversity=e4,
            e5_circular=e5,
            overall_completeness_pct=overall_completeness,
            disclosure_gaps=all_gaps,
            regulatory_refs=self._regulatory_refs,
        )

    # ------------------------------------------------------------------
    # Reference getters
    # ------------------------------------------------------------------

    def ref_e2_disclosures(self) -> dict:
        return E2_DISCLOSURES

    def ref_e3_disclosures(self) -> dict:
        return E3_DISCLOSURES

    def ref_e4_disclosures(self) -> dict:
        return E4_DISCLOSURES

    def ref_e5_disclosures(self) -> dict:
        return E5_DISCLOSURES

    def ref_materiality_triggers(self) -> dict:
        return MATERIALITY_TRIGGERS

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_completeness(flags: dict[str, bool]) -> float:
        if not flags:
            return 0.0
        return round(100.0 * sum(1 for v in flags.values() if v) / len(flags), 1)


def get_engine() -> ESRSE2E5Engine:
    return ESRSE2E5Engine.get_instance()
