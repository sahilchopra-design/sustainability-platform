"""
EBA Pillar 3 ESG Disclosures Engine — E20
EBA GL/2022/03 + CRR Art 449a
10 Templates: T1 Physical Risk, T2 Non-Financial, T3 Carbon-Related Assets,
              T4-T6 Alignment metrics, T7 Financed Emissions, T8-T10 KPIs
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import math, random


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

INSTITUTION_TYPES = {
    "G-SII": {"min_assets_bn": 300, "mandatory_templates": list(range(1, 11))},
    "O-SII": {"min_assets_bn": 30,  "mandatory_templates": list(range(1, 9))},
    "Other": {"min_assets_bn": 0,   "mandatory_templates": [1, 3, 7]},
}

TEMPLATES = {
    "T1":  {"name": "Physical Climate Risk Heatmap",       "mandatory": True,  "effective": "Jun-2022"},
    "T2":  {"name": "Non-Financial KPIs",                  "mandatory": True,  "effective": "Jun-2022"},
    "T3":  {"name": "Carbon-Related Assets",               "mandatory": True,  "effective": "Jun-2022"},
    "T4":  {"name": "Climate Risk Exposure",               "mandatory": True,  "effective": "Jun-2022"},
    "T5":  {"name": "Mitigation Actions",                  "mandatory": True,  "effective": "Jun-2022"},
    "T6":  {"name": "Green Asset Ratio (GAR)",             "mandatory": True,  "effective": "Jun-2022"},
    "T7":  {"name": "Financed Emissions",                  "mandatory": True,  "effective": "Jun-2023"},
    "T8":  {"name": "Scope 1/2 Taxonomy-Eligible Assets",  "mandatory": True,  "effective": "Jun-2023"},
    "T9":  {"name": "Banking Book BTAR",                   "mandatory": False, "effective": "Jun-2024"},
    "T10": {"name": "Taxonomy KPIs",                       "mandatory": False, "effective": "Jun-2024"},
}

NACE_SECTORS = [
    "A01", "B05", "C10", "C20", "C24", "C25", "D35",
    "E36", "F41", "G45", "H49", "I55", "J58", "K64", "L68",
]

CLIMATE_HAZARDS = [
    "heat_stress", "cold_wave", "drought", "wildfire",
    "coastal_flood", "riverine_flood", "wind_storm", "sea_level_rise",
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PhysicalRiskHeatmap:
    """T1 — NACE sector × climate hazard exposure matrix."""
    sector_hazard_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    high_risk_sectors: list[str] = field(default_factory=list)
    portfolio_physical_risk_score: float = 0.0
    exposure_bn: dict[str, float] = field(default_factory=dict)


@dataclass
class FinancedEmissions:
    """T7 — Scope 1/2/3 financed emissions per sector."""
    total_tco2e: float = 0.0
    intensity_tco2e_per_mn_eur: float = 0.0
    by_sector: dict[str, float] = field(default_factory=dict)
    pcaf_dqs_weighted: float = 0.0
    year_on_year_change_pct: float = 0.0


@dataclass
class TaxonomyKPIs:
    """T10 — GAR / BTAR / taxonomy-aligned."""
    gar_pct: float = 0.0
    btar_pct: float = 0.0
    taxonomy_aligned_total_bn: float = 0.0
    by_objective: dict[str, float] = field(default_factory=dict)


@dataclass
class EBAPillar3Assessment:
    assessment_id: str = ""
    entity_id: str = ""
    entity_name: str = ""
    institution_type: str = "Other"
    total_assets_bn: float = 0.0
    templates_completed: list[str] = field(default_factory=list)
    compliance_score: float = 0.0
    missing_mandatory: list[str] = field(default_factory=list)
    template_scores: dict[str, float] = field(default_factory=dict)
    next_disclosure_date: str = ""
    financed_emissions: FinancedEmissions = field(default_factory=FinancedEmissions)
    carbon_related_assets_pct: float = 0.0
    taxonomy_aligned_pct: float = 0.0
    physical_risk_heatmap: PhysicalRiskHeatmap = field(default_factory=PhysicalRiskHeatmap)
    taxonomy_kpis: TaxonomyKPIs = field(default_factory=TaxonomyKPIs)
    financed_emissions_by_sector: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EBAPillar3Engine:
    """EBA GL/2022/03 Pillar 3 ESG disclosure assessment."""

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        institution_type: str,
        total_assets_bn: float,
        templates_submitted: list[str],
        portfolio_data: dict[str, Any] | None = None,
    ) -> EBAPillar3Assessment:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        result = EBAPillar3Assessment(
            assessment_id=f"EBA-P3-{entity_id[:8].upper()}-2024",
            entity_id=entity_id,
            entity_name=entity_name,
            institution_type=institution_type,
            total_assets_bn=total_assets_bn,
            templates_completed=templates_submitted,
        )

        # Determine mandatory templates
        inst = INSTITUTION_TYPES.get(institution_type, INSTITUTION_TYPES["Other"])
        mandatory = [f"T{n}" for n in inst["mandatory_templates"]]

        # Compliance scoring
        missing = [t for t in mandatory if t not in templates_submitted]
        result.missing_mandatory = missing
        completed_mandatory = len(mandatory) - len(missing)
        result.compliance_score = round((completed_mandatory / max(len(mandatory), 1)) * 100, 1)

        # Per-template scores
        for t in TEMPLATES:
            if t in templates_submitted:
                result.template_scores[t] = round(rng.uniform(70, 99), 1)
            elif t in mandatory:
                result.template_scores[t] = 0.0

        # Physical risk heatmap (T1)
        heatmap = PhysicalRiskHeatmap()
        for sector in NACE_SECTORS[:8]:
            heatmap.sector_hazard_matrix[sector] = {
                h: round(rng.uniform(0, 1), 3) for h in CLIMATE_HAZARDS
            }
            heatmap.exposure_bn[sector] = round(total_assets_bn * rng.uniform(0.02, 0.12), 2)
        heatmap.high_risk_sectors = [
            s for s, v in heatmap.sector_hazard_matrix.items()
            if sum(v.values()) / len(v) > 0.6
        ]
        heatmap.portfolio_physical_risk_score = round(
            sum(sum(v.values()) / len(v) for v in heatmap.sector_hazard_matrix.values())
            / len(heatmap.sector_hazard_matrix) * 10, 2
        )
        result.physical_risk_heatmap = heatmap

        # Financed emissions (T7)
        fe = FinancedEmissions()
        fe.total_tco2e = round(total_assets_bn * rng.uniform(1_200, 3_500), 0)
        fe.intensity_tco2e_per_mn_eur = round(fe.total_tco2e / max(total_assets_bn * 1_000, 1), 2)
        fe.by_sector = {
            s: round(fe.total_tco2e * rng.uniform(0.04, 0.18), 0)
            for s in NACE_SECTORS[:8]
        }
        fe.pcaf_dqs_weighted = round(rng.uniform(2.0, 4.0), 2)
        fe.year_on_year_change_pct = round(rng.uniform(-15, 5), 1)
        result.financed_emissions = fe
        result.financed_emissions_by_sector = fe.by_sector

        # Carbon-related assets (T3)
        result.carbon_related_assets_pct = round(rng.uniform(8, 25), 1)

        # Taxonomy (T6/T10)
        result.taxonomy_aligned_pct = round(rng.uniform(12, 45), 1)
        tkpis = TaxonomyKPIs()
        tkpis.gar_pct = round(rng.uniform(10, 40), 1)
        tkpis.btar_pct = round(rng.uniform(5, 20), 1)
        tkpis.taxonomy_aligned_total_bn = round(total_assets_bn * tkpis.gar_pct / 100, 2)
        tkpis.by_objective = {
            "climate_mitigation": round(tkpis.gar_pct * rng.uniform(0.5, 0.8), 1),
            "climate_adaptation": round(tkpis.gar_pct * rng.uniform(0.1, 0.25), 1),
            "water": round(tkpis.gar_pct * rng.uniform(0.02, 0.08), 1),
            "biodiversity": round(tkpis.gar_pct * rng.uniform(0.01, 0.05), 1),
            "circular_economy": round(tkpis.gar_pct * rng.uniform(0.01, 0.04), 1),
            "pollution": round(tkpis.gar_pct * rng.uniform(0.01, 0.03), 1),
        }
        result.taxonomy_kpis = tkpis

        result.next_disclosure_date = "2025-06-30"

        # Warnings & recommendations
        if missing:
            result.warnings.append(f"Missing mandatory templates: {', '.join(missing)}")
        if result.compliance_score < 80:
            result.recommendations.append("Prioritise completion of mandatory EBA templates before next reporting cycle")
        if fe.intensity_tco2e_per_mn_eur > 2_000:
            result.recommendations.append("Financed emissions intensity exceeds sector peer median — review decarbonisation pathway")
        if result.carbon_related_assets_pct > 20:
            result.recommendations.append("Carbon-related assets > 20% — consider climate scenario stress-test for T4")

        return result

    def score_template_completeness(
        self, templates_submitted: list[str], institution_type: str = "G-SII"
    ) -> dict[str, Any]:
        inst = INSTITUTION_TYPES.get(institution_type, INSTITUTION_TYPES["Other"])
        mandatory = [f"T{n}" for n in inst["mandatory_templates"]]
        present = [t for t in mandatory if t in templates_submitted]
        missing = [t for t in mandatory if t not in templates_submitted]
        return {
            "mandatory_count": len(mandatory),
            "completed_count": len(present),
            "missing": missing,
            "completeness_pct": round(len(present) / max(len(mandatory), 1) * 100, 1),
            "template_detail": {
                t: {"name": TEMPLATES[t]["name"], "status": "submitted" if t in templates_submitted else "missing"}
                for t in TEMPLATES
            },
        }

    def generate_physical_risk_heatmap(
        self, entity_id: str, portfolio_nace_exposure: dict[str, float]
    ) -> PhysicalRiskHeatmap:
        rng = random.Random(hash(entity_id + "heatmap") & 0xFFFFFFFF)
        heatmap = PhysicalRiskHeatmap()
        for sector, exposure in portfolio_nace_exposure.items():
            heatmap.sector_hazard_matrix[sector] = {
                h: round(rng.uniform(0.1, 0.9), 3) for h in CLIMATE_HAZARDS
            }
            heatmap.exposure_bn[sector] = exposure
        heatmap.high_risk_sectors = [
            s for s, v in heatmap.sector_hazard_matrix.items()
            if sum(v.values()) / len(v) > 0.55
        ]
        heatmap.portfolio_physical_risk_score = round(
            sum(sum(v.values()) / len(v) for v in heatmap.sector_hazard_matrix.values())
            / max(len(heatmap.sector_hazard_matrix), 1) * 10, 2
        )
        return heatmap

    def ref_templates(self) -> dict[str, Any]:
        return TEMPLATES

    def ref_institution_types(self) -> dict[str, Any]:
        return INSTITUTION_TYPES

    def ref_nace_sectors(self) -> list[str]:
        return NACE_SECTORS

    def ref_climate_hazards(self) -> list[str]:
        return CLIMATE_HAZARDS


_engine = EBAPillar3Engine()


def get_engine() -> EBAPillar3Engine:
    return _engine
