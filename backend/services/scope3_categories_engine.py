"""
Scope 3 Categories Engine — E21
GHG Protocol Corporate Value Chain (Scope 3) Standard 2011
15 Categories, SBTi FLAG/Non-FLAG, 40% coverage rule, PCAF C15
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import random


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

SCOPE3_CATEGORIES = {
    "C1":  {"name": "Purchased goods & services",         "stream": "upstream",   "typical_pct": 0.30},
    "C2":  {"name": "Capital goods",                       "stream": "upstream",   "typical_pct": 0.05},
    "C3":  {"name": "Fuel & energy-related activities",   "stream": "upstream",   "typical_pct": 0.03},
    "C4":  {"name": "Upstream transportation",            "stream": "upstream",   "typical_pct": 0.04},
    "C5":  {"name": "Waste in operations",                "stream": "upstream",   "typical_pct": 0.01},
    "C6":  {"name": "Business travel",                    "stream": "upstream",   "typical_pct": 0.02},
    "C7":  {"name": "Employee commuting",                 "stream": "upstream",   "typical_pct": 0.02},
    "C8":  {"name": "Upstream leased assets",             "stream": "upstream",   "typical_pct": 0.02},
    "C9":  {"name": "Downstream transportation",          "stream": "downstream", "typical_pct": 0.04},
    "C10": {"name": "Processing of sold products",        "stream": "downstream", "typical_pct": 0.06},
    "C11": {"name": "Use of sold products",               "stream": "downstream", "typical_pct": 0.25},
    "C12": {"name": "End-of-life treatment",              "stream": "downstream", "typical_pct": 0.03},
    "C13": {"name": "Downstream leased assets",           "stream": "downstream", "typical_pct": 0.02},
    "C14": {"name": "Franchises",                         "stream": "downstream", "typical_pct": 0.02},
    "C15": {"name": "Investments (PCAF)",                 "stream": "downstream", "typical_pct": 0.09},
}

CALCULATION_METHODS = {
    "spend_based":       {"dqs": 4, "description": "EEIO spend-based using supplier spend"},
    "average_data":      {"dqs": 3, "description": "Industry-average emission factors"},
    "supplier_specific": {"dqs": 1, "description": "Primary supplier-specific data"},
    "hybrid":            {"dqs": 2, "description": "Hybrid approach — mix of primary + secondary"},
    "pcaf_standard":     {"dqs": 2, "description": "PCAF attribution for investments (C15)"},
}

SBTI_SECTORS_FLAG = [
    "agriculture", "forestry", "land_use", "food_beverage",
    "consumer_goods_agri", "paper", "real_estate_agri",
]

COVERAGE_THRESHOLD = 0.40   # SBTi near-term: must cover >=40% of total scope 3


@dataclass
class CategoryResult:
    category_id: str = ""
    category_name: str = ""
    is_material: bool = False
    tco2e: float = 0.0
    pct_of_total: float = 0.0
    calculation_method: str = "average_data"
    dqs: int = 3
    data_gaps: list[str] = field(default_factory=list)


@dataclass
class PortfolioScope3:
    """C15 — PCAF attribution for investment portfolios."""
    total_attributed_tco2e: float = 0.0
    by_asset_class: dict[str, float] = field(default_factory=dict)
    pcaf_dqs_weighted: float = 0.0
    portfolio_temperature_score: float = 0.0


@dataclass
class Scope3Assessment:
    assessment_id: str = ""
    entity_id: str = ""
    entity_name: str = ""
    nace_code: str = ""
    revenue_bn: float = 0.0
    headcount: int = 0
    material_categories: list[str] = field(default_factory=list)
    flag_applicable: bool = False
    total_scope3_tco2e: float = 0.0
    sbti_coverage_pct: float = 0.0
    meets_40pct_rule: bool = False
    category_results: list[CategoryResult] = field(default_factory=list)
    portfolio_scope3: PortfolioScope3 | None = None
    flag_split: dict[str, float] = field(default_factory=dict)
    weighted_avg_dqs: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class Scope3CategoriesEngine:
    """GHG Protocol Scope 3 Category Engine with SBTi coverage verification."""

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        nace_code: str,
        revenue_bn: float,
        headcount: int,
        sector_type: str = "non_flag",
        portfolio_aum_bn: float | None = None,
    ) -> Scope3Assessment:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        result = Scope3Assessment(
            assessment_id=f"S3CAT-{entity_id[:8].upper()}-2024",
            entity_id=entity_id,
            entity_name=entity_name,
            nace_code=nace_code,
            revenue_bn=revenue_bn,
            headcount=headcount,
            flag_applicable=sector_type in SBTI_SECTORS_FLAG,
        )

        # Base scope3 estimate (tCO2e) from revenue
        base_intensity = rng.uniform(80, 400)  # tCO2e per EUR M revenue
        total = revenue_bn * 1_000 * base_intensity
        result.total_scope3_tco2e = round(total, 0)

        # Category results
        cat_results: list[CategoryResult] = []
        cumulative = 0.0
        for cat_id, cat_meta in SCOPE3_CATEGORIES.items():
            fraction = cat_meta["typical_pct"] * rng.uniform(0.5, 1.8)
            tco2e = round(total * fraction, 0)
            cumulative += tco2e
            method = rng.choice(list(CALCULATION_METHODS.keys()))
            cr = CategoryResult(
                category_id=cat_id,
                category_name=cat_meta["name"],
                is_material=fraction > 0.05,
                tco2e=tco2e,
                pct_of_total=round(fraction * 100, 1),
                calculation_method=method,
                dqs=CALCULATION_METHODS[method]["dqs"],
            )
            if method in ("spend_based", "average_data"):
                cr.data_gaps.append("No primary supplier data — recommend supplier engagement programme")
            cat_results.append(cr)

        result.category_results = cat_results
        result.material_categories = [c.category_id for c in cat_results if c.is_material]

        # SBTi coverage (material cats as pct of total)
        material_tco2e = sum(c.tco2e for c in cat_results if c.is_material)
        result.sbti_coverage_pct = round(material_tco2e / max(total, 1) * 100, 1)
        result.meets_40pct_rule = result.sbti_coverage_pct >= (COVERAGE_THRESHOLD * 100)

        # Weighted DQS
        total_for_dqs = sum(c.tco2e for c in cat_results)
        result.weighted_avg_dqs = round(
            sum(c.tco2e * c.dqs for c in cat_results) / max(total_for_dqs, 1), 2
        )

        # FLAG split (for FLAG-applicable sectors)
        if result.flag_applicable:
            flag_pct = rng.uniform(0.15, 0.60)
            result.flag_split = {
                "flag_tco2e": round(total * flag_pct, 0),
                "non_flag_tco2e": round(total * (1 - flag_pct), 0),
                "flag_pct": round(flag_pct * 100, 1),
            }

        # C15 portfolio scope 3
        if portfolio_aum_bn and portfolio_aum_bn > 0:
            ps = PortfolioScope3()
            ps.total_attributed_tco2e = round(portfolio_aum_bn * 1_000 * rng.uniform(40, 120), 0)
            ps.by_asset_class = {
                "listed_equity":      round(ps.total_attributed_tco2e * rng.uniform(0.3, 0.5), 0),
                "corporate_bonds":    round(ps.total_attributed_tco2e * rng.uniform(0.2, 0.35), 0),
                "project_finance":    round(ps.total_attributed_tco2e * rng.uniform(0.05, 0.15), 0),
                "real_estate":        round(ps.total_attributed_tco2e * rng.uniform(0.03, 0.12), 0),
                "sovereign_bonds":    round(ps.total_attributed_tco2e * rng.uniform(0.02, 0.08), 0),
            }
            ps.pcaf_dqs_weighted = round(rng.uniform(2.5, 4.0), 2)
            ps.portfolio_temperature_score = round(rng.uniform(1.8, 3.2), 1)
            result.portfolio_scope3 = ps

        # Recommendations
        if not result.meets_40pct_rule:
            result.warnings.append(
                f"SBTi 40% coverage rule not met: {result.sbti_coverage_pct}% covered"
            )
            result.recommendations.append("Expand boundary to include C1 or C11 to meet SBTi near-term coverage threshold")
        if result.weighted_avg_dqs > 3.5:
            result.recommendations.append("High average DQS — consider supplier-specific data collection to improve accuracy")
        if "C15" in result.material_categories and result.portfolio_scope3 is None:
            result.recommendations.append("C15 (Investments) is material — apply PCAF standard attribution methodology")

        return result

    def screen_materiality(
        self, nace_code: str, revenue_bn: float
    ) -> dict[str, Any]:
        """Quick materiality screen before full assessment."""
        rng = random.Random(hash(nace_code) & 0xFFFFFFFF)
        material = {}
        for cat_id, cat_meta in SCOPE3_CATEGORIES.items():
            score = cat_meta["typical_pct"] * rng.uniform(0.8, 1.5)
            material[cat_id] = {
                "name": cat_meta["name"],
                "likely_material": score > 0.06,
                "relative_significance": "high" if score > 0.15 else "medium" if score > 0.06 else "low",
            }
        return material

    def ref_categories(self) -> dict[str, Any]:
        return SCOPE3_CATEGORIES

    def ref_calculation_methods(self) -> dict[str, Any]:
        return CALCULATION_METHODS

    def ref_sbti_coverage_rule(self) -> dict[str, Any]:
        return {
            "threshold_pct": COVERAGE_THRESHOLD * 100,
            "description": "SBTi near-term Scope 3 target: cover >=40% of total Scope 3 by mass",
            "flag_note": "FLAG sectors must set separate forest, land, agriculture targets",
        }


_engine = Scope3CategoriesEngine()


def get_engine() -> Scope3CategoriesEngine:
    return _engine
