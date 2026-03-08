"""
Methane Monitoring Engine (OGMP 2.0)
=====================================
Oil & gas methane emissions reporting aligned with OGMP 2.0 framework.
Covers source-level measurement, Tier classification (1-5), intensity
metrics, and reduction pathway tracking.

References:
- OGMP 2.0 Framework — UNEP / CCAC (Level 1-5)
- EU Methane Regulation (2024/1787) — MRV requirements
- GHG Protocol — CH4 to CO2e conversion (GWP-100 = 28, GWP-20 = 82.5)
- EPA GHGRP Subpart W — O&G facility reporting
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# Methane GWP conversion
GWP_100: float = 28.0  # IPCC AR5
GWP_20: float = 82.5   # IPCC AR6 (short-term potency)

# OGMP 2.0 reporting levels
OGMP_LEVELS: dict[int, dict] = {
    1: {"label": "Level 1 — Emission factors", "method": "Generic EFs", "accuracy": "low"},
    2: {"label": "Level 2 — Activity-based EFs", "method": "Country/region EFs", "accuracy": "moderate"},
    3: {"label": "Level 3 — Facility modelling", "method": "Engineering estimates", "accuracy": "moderate-high"},
    4: {"label": "Level 4 — Site measurement", "method": "OGI / drone / continuous monitors", "accuracy": "high"},
    5: {"label": "Level 5 — Source-level measurement", "method": "Direct measurement per source", "accuracy": "very_high"},
}

# Methane emission source categories (Oil & Gas)
SOURCE_CATEGORIES: dict[str, dict] = {
    "venting": {"label": "Process Venting", "typical_ef_tch4_bcm": 0.40, "abatement_potential_pct": 90},
    "flaring": {"label": "Incomplete Flaring", "typical_ef_tch4_bcm": 0.05, "abatement_potential_pct": 95},
    "fugitive_wellhead": {"label": "Fugitive — Wellhead", "typical_ef_tch4_bcm": 0.15, "abatement_potential_pct": 70},
    "fugitive_processing": {"label": "Fugitive — Processing", "typical_ef_tch4_bcm": 0.10, "abatement_potential_pct": 80},
    "fugitive_transmission": {"label": "Fugitive — Transmission", "typical_ef_tch4_bcm": 0.08, "abatement_potential_pct": 75},
    "fugitive_distribution": {"label": "Fugitive — Distribution", "typical_ef_tch4_bcm": 0.12, "abatement_potential_pct": 60},
    "pneumatic_devices": {"label": "Pneumatic Devices", "typical_ef_tch4_bcm": 0.06, "abatement_potential_pct": 95},
    "compressor_seals": {"label": "Compressor Seals", "typical_ef_tch4_bcm": 0.04, "abatement_potential_pct": 85},
    "tanks_loading": {"label": "Tank & Loading Losses", "typical_ef_tch4_bcm": 0.03, "abatement_potential_pct": 90},
    "other": {"label": "Other / Unaccounted", "typical_ef_tch4_bcm": 0.02, "abatement_potential_pct": 50},
}

# Abatement measures
ABATEMENT_MEASURES: dict[str, dict] = {
    "ldar": {"label": "LDAR Program", "cost_eur_tch4": 2500, "reduction_pct": 60, "applicable": ["fugitive_wellhead", "fugitive_processing", "fugitive_transmission", "fugitive_distribution"]},
    "vapour_recovery": {"label": "Vapour Recovery Unit", "cost_eur_tch4": 4000, "reduction_pct": 90, "applicable": ["venting", "tanks_loading"]},
    "instrument_air": {"label": "Instrument Air Conversion", "cost_eur_tch4": 3000, "reduction_pct": 95, "applicable": ["pneumatic_devices"]},
    "dry_seal": {"label": "Dry Gas Seal Retrofit", "cost_eur_tch4": 5000, "reduction_pct": 85, "applicable": ["compressor_seals"]},
    "enclosed_flare": {"label": "Enclosed Combustion", "cost_eur_tch4": 1500, "reduction_pct": 98, "applicable": ["flaring"]},
    "continuous_monitoring": {"label": "Continuous Monitoring", "cost_eur_tch4": 1000, "reduction_pct": 30, "applicable": ["fugitive_wellhead", "fugitive_processing", "other"]},
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class MethaneSource:
    """A single methane emission source."""
    source_id: str
    category: str  # key into SOURCE_CATEGORIES
    facility_name: str
    ogmp_level: int = 2
    measured_tch4_yr: float = 0  # Direct measurement (Level 4/5)
    activity_bcm_yr: float = 0  # Activity data (Level 2/3)
    custom_ef_tch4_bcm: float = 0  # Custom EF (Level 3)


@dataclass
class MethaneSourceResult:
    """Assessed emissions for one source."""
    source_id: str
    category: str
    category_label: str
    facility_name: str
    ogmp_level: int
    ogmp_level_label: str
    emissions_tch4: float
    emissions_tco2e_gwp100: float
    emissions_tco2e_gwp20: float
    method_used: str
    abatement_potential_tch4: float
    recommended_measures: list[str]


@dataclass
class FacilityMethaneResult:
    """Complete facility methane assessment."""
    facility_name: str
    source_results: list[MethaneSourceResult]
    total_tch4: float
    total_tco2e_gwp100: float
    total_tco2e_gwp20: float
    methane_intensity_tch4_bcm: float
    total_activity_bcm: float
    abatement_potential_tch4: float
    abatement_potential_pct: float
    weighted_ogmp_level: float
    eu_methane_reg_compliant: bool  # Requires Level 3+ by 2027
    reduction_pathway: list[dict]  # [{measure, reduction_tch4, cost_eur}]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class MethaneOGMPEngine:
    """Methane emissions assessment and OGMP 2.0 compliance engine."""

    def assess_facility(
        self,
        facility_name: str,
        sources: list[MethaneSource],
        production_bcm_yr: float = 0,
    ) -> FacilityMethaneResult:
        """Assess methane emissions for a facility."""
        results = []
        total_activity = 0

        for src in sources:
            cat = SOURCE_CATEGORIES.get(src.category, SOURCE_CATEGORIES["other"])
            level_info = OGMP_LEVELS.get(src.ogmp_level, OGMP_LEVELS[2])

            # Calculate emissions based on OGMP level
            if src.ogmp_level >= 4 and src.measured_tch4_yr > 0:
                tch4 = src.measured_tch4_yr
                method = "Direct measurement"
            elif src.custom_ef_tch4_bcm > 0 and src.activity_bcm_yr > 0:
                tch4 = src.activity_bcm_yr * src.custom_ef_tch4_bcm
                method = "Custom emission factor"
            elif src.activity_bcm_yr > 0:
                tch4 = src.activity_bcm_yr * cat["typical_ef_tch4_bcm"]
                method = "Default emission factor"
            else:
                tch4 = 0
                method = "No data"

            total_activity += src.activity_bcm_yr

            co2e_100 = tch4 * GWP_100
            co2e_20 = tch4 * GWP_20

            abatement = tch4 * cat["abatement_potential_pct"] / 100

            # Recommended measures
            measures = [
                m_id for m_id, m in ABATEMENT_MEASURES.items()
                if src.category in m["applicable"]
            ]

            results.append(MethaneSourceResult(
                source_id=src.source_id,
                category=src.category,
                category_label=cat["label"],
                facility_name=src.facility_name,
                ogmp_level=src.ogmp_level,
                ogmp_level_label=level_info["label"],
                emissions_tch4=round(tch4, 3),
                emissions_tco2e_gwp100=round(co2e_100, 1),
                emissions_tco2e_gwp20=round(co2e_20, 1),
                method_used=method,
                abatement_potential_tch4=round(abatement, 3),
                recommended_measures=measures,
            ))

        total_tch4 = sum(r.emissions_tch4 for r in results)
        total_co2e_100 = sum(r.emissions_tco2e_gwp100 for r in results)
        total_co2e_20 = sum(r.emissions_tco2e_gwp20 for r in results)
        total_abatement = sum(r.abatement_potential_tch4 for r in results)

        activity_total = total_activity if total_activity > 0 else production_bcm_yr
        intensity = total_tch4 / activity_total if activity_total > 0 else 0
        abatement_pct = (total_abatement / total_tch4 * 100) if total_tch4 > 0 else 0

        # Weighted OGMP level
        if total_tch4 > 0:
            weighted_level = sum(r.ogmp_level * r.emissions_tch4 for r in results) / total_tch4
        else:
            weighted_level = sum(s.ogmp_level for s in sources) / len(sources) if sources else 0

        # EU Methane Regulation: Level 3+ required by 2027
        eu_compliant = all(s.ogmp_level >= 3 for s in sources)

        # Reduction pathway
        pathway = self._build_pathway(results)

        return FacilityMethaneResult(
            facility_name=facility_name,
            source_results=results,
            total_tch4=round(total_tch4, 3),
            total_tco2e_gwp100=round(total_co2e_100, 1),
            total_tco2e_gwp20=round(total_co2e_20, 1),
            methane_intensity_tch4_bcm=round(intensity, 4),
            total_activity_bcm=round(activity_total, 2),
            abatement_potential_tch4=round(total_abatement, 3),
            abatement_potential_pct=round(abatement_pct, 1),
            weighted_ogmp_level=round(weighted_level, 1),
            eu_methane_reg_compliant=eu_compliant,
            reduction_pathway=pathway,
        )

    def _build_pathway(self, results: list[MethaneSourceResult]) -> list[dict]:
        """Build prioritised reduction pathway (cheapest abatement first)."""
        pathway = []
        for r in results:
            if r.emissions_tch4 <= 0:
                continue
            for m_id in r.recommended_measures:
                measure = ABATEMENT_MEASURES[m_id]
                reduction = r.emissions_tch4 * measure["reduction_pct"] / 100
                cost = reduction * measure["cost_eur_tch4"]
                pathway.append({
                    "source_id": r.source_id,
                    "category": r.category,
                    "measure": m_id,
                    "measure_label": measure["label"],
                    "reduction_tch4": round(reduction, 3),
                    "reduction_tco2e": round(reduction * GWP_100, 1),
                    "cost_eur": round(cost, 2),
                    "cost_eur_per_tco2e": round(cost / (reduction * GWP_100), 2) if reduction > 0 else 0,
                })

        # Sort by cost-effectiveness (cheapest per tCO2e first)
        pathway.sort(key=lambda x: x["cost_eur_per_tco2e"])
        return pathway

    def get_source_categories(self) -> dict[str, dict]:
        return SOURCE_CATEGORIES

    def get_ogmp_levels(self) -> dict[int, dict]:
        return OGMP_LEVELS

    def get_abatement_measures(self) -> dict[str, dict]:
        return ABATEMENT_MEASURES
