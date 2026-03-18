"""
Nature-RE Integration Engine
=============================
Bridges TNFD nature risk outputs (LEAP, water risk, biodiversity overlap)
into real estate valuation adjustments.

Standards & References
- TNFD LEAP Framework (v1.0, 2023)
- WRI Aqueduct Water Risk Atlas (score 0-5 → CLVaR water_stress_score)
- DEFRA Biodiversity Metric 4.0 (BNG credit estimator)
- EU Taxonomy Article 11 — Nature-related DNSH criteria
- RICS VPGA 12 — ESG matters requiring consideration
- IPBES Global Assessment (nature dependency valuation)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import math


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# TNFD LEAP overall_score (0-5) → valuation haircut %
# Derived from IPBES/ENCORE dependency-materiality mapping
NATURE_HAIRCUT_TABLE: dict[str, dict[str, float]] = {
    # property_type → {risk_band: haircut_pct}
    "office": {
        "low": 0.0, "medium_low": 0.5, "medium": 1.5,
        "medium_high": 3.0, "high": 5.0, "critical": 8.0,
    },
    "retail": {
        "low": 0.0, "medium_low": 0.5, "medium": 1.5,
        "medium_high": 3.5, "high": 6.0, "critical": 10.0,
    },
    "industrial": {
        "low": 0.0, "medium_low": 1.0, "medium": 2.5,
        "medium_high": 5.0, "high": 8.0, "critical": 14.0,
    },
    "multifamily": {
        "low": 0.0, "medium_low": 0.3, "medium": 1.0,
        "medium_high": 2.0, "high": 4.0, "critical": 7.0,
    },
    "hotel": {
        "low": 0.0, "medium_low": 0.5, "medium": 2.0,
        "medium_high": 4.0, "high": 7.0, "critical": 12.0,
    },
    "single_family": {
        "low": 0.0, "medium_low": 0.2, "medium": 0.8,
        "medium_high": 1.5, "high": 3.0, "critical": 5.0,
    },
}

# Water stress score → NOI adjustment %
# WRI Aqueduct: 0-1 low, 1-2 low-medium, 2-3 medium-high, 3-4 high, 4-5 extremely high
WATER_NOI_ADJUSTMENT: dict[str, dict[str, float]] = {
    "office": {
        "low": 0.0, "low_medium": -0.3, "medium_high": -1.0,
        "high": -2.5, "extremely_high": -5.0,
    },
    "retail": {
        "low": 0.0, "low_medium": -0.2, "medium_high": -0.8,
        "high": -2.0, "extremely_high": -4.0,
    },
    "industrial": {
        "low": 0.0, "low_medium": -0.5, "medium_high": -2.0,
        "high": -5.0, "extremely_high": -10.0,
    },
    "multifamily": {
        "low": 0.0, "low_medium": -0.2, "medium_high": -0.5,
        "high": -1.5, "extremely_high": -3.0,
    },
    "hotel": {
        "low": 0.0, "low_medium": -0.5, "medium_high": -1.5,
        "high": -4.0, "extremely_high": -8.0,
    },
    "single_family": {
        "low": 0.0, "low_medium": -0.1, "medium_high": -0.3,
        "high": -1.0, "extremely_high": -2.0,
    },
}

# Biodiversity impact (0-5) → cap rate adjustment (bps)
# Higher impact = wider cap rate = lower value
BIODIVERSITY_CAP_RATE_BPS: list[tuple[float, float, int]] = [
    (0.0, 1.0, 0),      # negligible
    (1.0, 2.0, 5),
    (2.0, 3.0, 15),
    (3.0, 4.0, 30),
    (4.0, 5.0, 50),      # severe: regulatory/litigation risk
]

# BNG cost estimator — DEFRA Metric 4.0 habitat unit costs (GBP per unit)
BNG_UNIT_COSTS: dict[str, float] = {
    "grassland": 18_000,
    "woodland": 25_000,
    "wetland": 30_000,
    "hedgerow_per_km": 15_000,
    "urban_habitat": 20_000,
    "default": 22_000,
}

# EU Taxonomy DNSH Nature criteria thresholds
EU_TAX_NATURE_DNSH: dict[str, Any] = {
    "max_water_stress_score": 3.0,         # WRI Aqueduct
    "max_biodiversity_impact": 2.0,         # overlap score
    "requires_eia": True,                   # if impact > 2
    "no_net_deforestation": True,
    "wetland_buffer_m": 50,
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class NatureREInput:
    """Combined input for nature-adjusted RE valuation."""
    property_id: str
    property_type: str = "office"
    market_value_eur: float = 0.0
    noi_eur: float = 0.0
    cap_rate_pct: float = 5.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Nature risk outputs (from nature_risk_calculator)
    leap_overall_score: float = 0.0
    leap_risk_rating: str = "low"
    water_baseline_score: float = 0.0
    water_projected_2030: float = 0.0
    water_projected_2050: float = 0.0
    biodiversity_impact_score: float = 0.0
    biodiversity_direct_overlaps: int = 0
    biodiversity_key_sites: list[str] = field(default_factory=list)
    nature_key_risks: list[dict] = field(default_factory=list)
    # Optional BNG fields
    site_area_hectares: float = 0.0
    habitat_type: str = "default"
    bng_units_required: float = 0.0


@dataclass
class NatureREResult:
    """Nature-adjusted RE valuation result."""
    property_id: str
    property_type: str
    # Baseline
    market_value_eur: float
    noi_eur: float
    cap_rate_pct: float
    # Nature adjustments
    nature_haircut_pct: float
    water_noi_adjustment_pct: float
    biodiversity_cap_rate_adj_bps: int
    bng_capex_estimate_eur: float
    # Adjusted values
    nature_adjusted_value_eur: float
    nature_adjusted_noi_eur: float
    nature_adjusted_cap_rate_pct: float
    total_nature_discount_pct: float
    # Scores
    composite_nature_score: float      # 0-5
    composite_nature_band: str
    # EU Taxonomy DNSH
    eu_taxonomy_nature_dnsh_pass: bool
    eu_taxonomy_nature_flags: list[str]
    # Water stress forward-looking
    water_stress_band: str
    water_stress_2030_band: str
    water_stress_2050_band: str
    # Narrative
    nature_narrative: str
    recommendations: list[str]


@dataclass
class PortfolioNatureREResult:
    """Portfolio-level nature-RE integration result."""
    portfolio_id: str
    total_properties: int
    total_market_value_eur: float
    total_nature_adjusted_value_eur: float
    avg_nature_discount_pct: float
    avg_composite_nature_score: float
    eu_taxonomy_dnsh_pass_count: int
    eu_taxonomy_dnsh_fail_count: int
    total_bng_capex_eur: float
    nature_band_distribution: dict[str, int]
    high_risk_properties: list[dict]
    property_results: list[dict]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class NatureREIntegrationEngine:
    """Bridge TNFD nature risk outputs to RE valuation adjustments."""

    # --- Score Band Helpers ---

    @staticmethod
    def _nature_score_to_band(score: float) -> str:
        if score <= 1.0:
            return "low"
        if score <= 2.0:
            return "medium_low"
        if score <= 3.0:
            return "medium"
        if score <= 3.5:
            return "medium_high"
        if score <= 4.0:
            return "high"
        return "critical"

    @staticmethod
    def _water_score_to_band(score: float) -> str:
        if score < 1.0:
            return "low"
        if score < 2.0:
            return "low_medium"
        if score < 3.0:
            return "medium_high"
        if score < 4.0:
            return "high"
        return "extremely_high"

    # --- Core Calculation ---

    def assess_nature_adjusted_valuation(self, inp: NatureREInput) -> NatureREResult:
        """Full nature-adjusted RE valuation."""
        ptype = inp.property_type if inp.property_type in NATURE_HAIRCUT_TABLE else "office"

        # 1. Nature haircut from LEAP overall score
        nature_band = self._nature_score_to_band(inp.leap_overall_score)
        haircut_table = NATURE_HAIRCUT_TABLE.get(ptype, NATURE_HAIRCUT_TABLE["office"])
        nature_haircut_pct = haircut_table.get(nature_band, 0.0)

        # 2. Water stress NOI adjustment
        water_band = self._water_score_to_band(inp.water_baseline_score)
        water_noi_table = WATER_NOI_ADJUSTMENT.get(ptype, WATER_NOI_ADJUSTMENT["office"])
        water_noi_adj_pct = water_noi_table.get(water_band, 0.0)

        # 3. Biodiversity cap rate adjustment
        bio_cap_bps = 0
        for low, high, bps in BIODIVERSITY_CAP_RATE_BPS:
            if low <= inp.biodiversity_impact_score < high:
                bio_cap_bps = bps
                break
        if inp.biodiversity_impact_score >= 5.0:
            bio_cap_bps = 50

        # 4. BNG cost estimate (DEFRA Metric 4.0)
        bng_units = inp.bng_units_required
        if bng_units == 0 and inp.biodiversity_impact_score > 2.0 and inp.site_area_hectares > 0:
            # Estimate: impact score > 2 triggers mandatory 10% BNG (Environment Act 2021)
            bng_units = inp.site_area_hectares * 0.10 * (1 + inp.biodiversity_impact_score * 0.1)
        unit_cost = BNG_UNIT_COSTS.get(inp.habitat_type, BNG_UNIT_COSTS["default"])
        bng_capex_eur = round(bng_units * unit_cost * 1.17, 2)  # GBP→EUR approx

        # 5. Apply adjustments
        adj_noi = inp.noi_eur * (1 + water_noi_adj_pct / 100)
        adj_cap_rate = inp.cap_rate_pct + bio_cap_bps / 100
        if adj_cap_rate <= 0:
            adj_cap_rate = 0.5

        # Nature-adjusted value = adjusted NOI / adjusted cap rate, then apply haircut
        if adj_noi > 0 and adj_cap_rate > 0:
            income_based_value = adj_noi / (adj_cap_rate / 100)
        else:
            income_based_value = inp.market_value_eur

        nature_adj_value = income_based_value * (1 - nature_haircut_pct / 100)

        total_discount = 0.0
        if inp.market_value_eur > 0:
            total_discount = round((1 - nature_adj_value / inp.market_value_eur) * 100, 2)

        # 6. Composite nature score (weighted: LEAP 50%, water 30%, biodiversity 20%)
        composite = (
            inp.leap_overall_score * 0.50
            + inp.water_baseline_score * 0.30
            + inp.biodiversity_impact_score * 0.20
        )
        composite_band = self._nature_score_to_band(composite)

        # 7. EU Taxonomy DNSH nature check
        eu_flags = []
        eu_pass = True
        if inp.water_baseline_score > EU_TAX_NATURE_DNSH["max_water_stress_score"]:
            eu_flags.append(f"Water stress score {inp.water_baseline_score:.1f} exceeds threshold {EU_TAX_NATURE_DNSH['max_water_stress_score']}")
            eu_pass = False
        if inp.biodiversity_impact_score > EU_TAX_NATURE_DNSH["max_biodiversity_impact"]:
            eu_flags.append(f"Biodiversity impact {inp.biodiversity_impact_score:.1f} exceeds threshold {EU_TAX_NATURE_DNSH['max_biodiversity_impact']}")
            eu_pass = False
        if inp.biodiversity_direct_overlaps > 0:
            eu_flags.append(f"{inp.biodiversity_direct_overlaps} direct overlaps with protected sites (EIA required)")
            eu_pass = False

        # 8. Water stress forward-looking bands
        water_band_2030 = self._water_score_to_band(inp.water_projected_2030)
        water_band_2050 = self._water_score_to_band(inp.water_projected_2050)

        # 9. Narrative
        narrative = self._generate_narrative(inp, nature_haircut_pct, water_noi_adj_pct,
                                              bio_cap_bps, composite, eu_pass)

        # 10. Recommendations
        recs = self._generate_recommendations(inp, nature_band, water_band, composite)

        return NatureREResult(
            property_id=inp.property_id,
            property_type=inp.property_type,
            market_value_eur=inp.market_value_eur,
            noi_eur=inp.noi_eur,
            cap_rate_pct=inp.cap_rate_pct,
            nature_haircut_pct=round(nature_haircut_pct, 2),
            water_noi_adjustment_pct=round(water_noi_adj_pct, 2),
            biodiversity_cap_rate_adj_bps=bio_cap_bps,
            bng_capex_estimate_eur=bng_capex_eur,
            nature_adjusted_value_eur=round(nature_adj_value, 2),
            nature_adjusted_noi_eur=round(adj_noi, 2),
            nature_adjusted_cap_rate_pct=round(adj_cap_rate, 2),
            total_nature_discount_pct=total_discount,
            composite_nature_score=round(composite, 2),
            composite_nature_band=composite_band,
            eu_taxonomy_nature_dnsh_pass=eu_pass,
            eu_taxonomy_nature_flags=eu_flags,
            water_stress_band=water_band,
            water_stress_2030_band=water_band_2030,
            water_stress_2050_band=water_band_2050,
            nature_narrative=narrative,
            recommendations=recs,
        )

    # --- Portfolio ---

    def assess_portfolio(self, portfolio_id: str,
                         properties: list[NatureREInput]) -> PortfolioNatureREResult:
        """Assess nature-adjusted valuations across a portfolio."""
        results = []
        high_risk = []

        for p in properties:
            r = self.assess_nature_adjusted_valuation(p)
            rd = {
                "property_id": r.property_id,
                "property_type": r.property_type,
                "market_value_eur": r.market_value_eur,
                "nature_adjusted_value_eur": r.nature_adjusted_value_eur,
                "total_nature_discount_pct": r.total_nature_discount_pct,
                "composite_nature_score": r.composite_nature_score,
                "composite_nature_band": r.composite_nature_band,
                "eu_taxonomy_nature_dnsh_pass": r.eu_taxonomy_nature_dnsh_pass,
                "bng_capex_estimate_eur": r.bng_capex_estimate_eur,
            }
            results.append(rd)
            if r.composite_nature_score >= 3.0:
                high_risk.append(rd)

        total_mv = sum(p.market_value_eur for p in properties)
        total_adj = sum(r["nature_adjusted_value_eur"] for r in results)
        avg_discount = round((1 - total_adj / total_mv) * 100, 2) if total_mv else 0.0
        avg_score = round(sum(r["composite_nature_score"] for r in results) / max(len(results), 1), 2)
        dnsh_pass = sum(1 for r in results if r["eu_taxonomy_nature_dnsh_pass"])
        total_bng = sum(r["bng_capex_estimate_eur"] for r in results)

        band_dist: dict[str, int] = {}
        for r in results:
            b = r["composite_nature_band"]
            band_dist[b] = band_dist.get(b, 0) + 1

        return PortfolioNatureREResult(
            portfolio_id=portfolio_id,
            total_properties=len(properties),
            total_market_value_eur=round(total_mv, 2),
            total_nature_adjusted_value_eur=round(total_adj, 2),
            avg_nature_discount_pct=avg_discount,
            avg_composite_nature_score=avg_score,
            eu_taxonomy_dnsh_pass_count=dnsh_pass,
            eu_taxonomy_dnsh_fail_count=len(results) - dnsh_pass,
            total_bng_capex_eur=round(total_bng, 2),
            nature_band_distribution=band_dist,
            high_risk_properties=high_risk,
            property_results=results,
        )

    # --- Reference Data Accessors ---

    @staticmethod
    def get_nature_haircut_table() -> dict:
        return NATURE_HAIRCUT_TABLE

    @staticmethod
    def get_water_noi_adjustments() -> dict:
        return WATER_NOI_ADJUSTMENT

    @staticmethod
    def get_biodiversity_cap_rate_schedule() -> list:
        return [{"min_score": lo, "max_score": hi, "cap_rate_adj_bps": bps}
                for lo, hi, bps in BIODIVERSITY_CAP_RATE_BPS]

    @staticmethod
    def get_bng_unit_costs() -> dict:
        return BNG_UNIT_COSTS

    @staticmethod
    def get_eu_taxonomy_nature_dnsh() -> dict:
        return EU_TAX_NATURE_DNSH

    # --- Internal Helpers ---

    def _generate_narrative(self, inp: NatureREInput,
                            haircut: float, water_adj: float,
                            bio_bps: int, composite: float,
                            eu_pass: bool) -> str:
        parts = [
            f"Nature-adjusted valuation for property {inp.property_id} ({inp.property_type})."
        ]
        if composite <= 1.0:
            parts.append("Nature risk exposure is negligible; no material valuation impact identified.")
        elif composite <= 2.5:
            parts.append(
                f"Moderate nature risk (composite score {composite:.1f}/5). "
                f"A {haircut:.1f}% nature haircut applies based on TNFD LEAP assessment."
            )
        else:
            parts.append(
                f"Elevated nature risk (composite score {composite:.1f}/5). "
                f"A {haircut:.1f}% nature-related haircut applies reflecting dependency "
                f"on ecosystem services and regulatory exposure."
            )

        if water_adj < 0:
            parts.append(
                f"Water stress (score {inp.water_baseline_score:.1f}/5) reduces projected NOI "
                f"by {abs(water_adj):.1f}% reflecting operational cost escalation "
                f"(WRI Aqueduct baseline)."
            )
            if inp.water_projected_2050 > inp.water_baseline_score + 0.5:
                parts.append(
                    f"Forward-looking water stress worsens to {inp.water_projected_2050:.1f}/5 by 2050, "
                    "signalling increasing materiality under climate scenarios."
                )

        if bio_bps > 0:
            parts.append(
                f"Biodiversity proximity (impact score {inp.biodiversity_impact_score:.1f}/5) "
                f"adds {bio_bps} bps to cap rate reflecting regulatory and litigation risk "
                f"(TNFD / Environment Act 2021)."
            )

        if not eu_pass:
            parts.append(
                "Property does NOT pass EU Taxonomy nature-related DNSH criteria (Article 11). "
                "Taxonomy alignment for substantial contribution to climate objectives is at risk."
            )

        parts.append(
            f"Overall nature-adjusted discount: {abs(inp.market_value_eur - inp.market_value_eur * (1 - haircut / 100)):,.0f} EUR "
            f"({haircut:.1f}% haircut). "
            f"Assessment per TNFD LEAP v1.0, RICS VPGA 12, EU Taxonomy Reg. 2020/852."
        )
        return " ".join(parts)

    def _generate_recommendations(self, inp: NatureREInput,
                                   nature_band: str, water_band: str,
                                   composite: float) -> list[str]:
        recs = []
        if composite > 2.5:
            recs.append("Commission detailed TNFD LEAP assessment to quantify nature dependencies and impacts.")
        if water_band in ("high", "extremely_high"):
            recs.append("Conduct water efficiency audit; consider rainwater harvesting and greywater recycling.")
            recs.append("Evaluate water risk insurance or parametric cover for drought events.")
        if inp.biodiversity_impact_score > 2.0:
            recs.append("Engage ecological consultant for Biodiversity Net Gain (BNG) assessment (DEFRA Metric 4.0).")
            if inp.biodiversity_direct_overlaps > 0:
                recs.append("Direct protected site overlap detected — Environmental Impact Assessment (EIA) required.")
        if nature_band in ("high", "critical"):
            recs.append("Nature risk is material to valuation — disclose per TNFD Recommend pillar and RICS VPGA 12.")
            recs.append("Consider nature-based solutions (NbS) to reduce dependency and improve resilience.")
        if inp.water_projected_2050 > 3.5:
            recs.append("2050 water stress projection is high — factor into long-term hold/dispose strategy.")
        if not inp.latitude or not inp.longitude:
            recs.append("Provide geospatial coordinates to enable biodiversity overlap analysis.")
        return recs
