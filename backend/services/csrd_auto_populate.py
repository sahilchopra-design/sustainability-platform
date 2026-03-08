"""
CSRD Auto-Population Engine
=============================
Automatically populates CSRD / ESRS disclosure data points from existing
module outputs. Maps calculated KPIs from climate risk, ECL, PCAF, nature
risk, and other engines into ESRS E1-E5, S1, G1 data point slots.

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
}

# Required minimum DPs for each ESRS standard
ESRS_MINIMUMS: dict[str, int] = {
    "E1": 15, "E2": 6, "E3": 5, "E4": 8, "E5": 5,
    "S1": 10, "G1": 4,
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
