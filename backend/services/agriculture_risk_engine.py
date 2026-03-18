"""
Agriculture Risk Engine (Expanded)
====================================
Comprehensive agriculture finance risk analytics covering crop, livestock,
and land-use sub-sectors. Extends the base agriculture_risk_calculator with
three additional sub-modules: Livestock Methane Intensity, Disease Outbreak
Risk, and Biodiversity Net Gain.

Sub-Modules:
  1. Weather-Indexed Risk       — crop yield volatility, parametric triggers (from base calculator)
  2. EUDR Compliance            — EU 2023/1115 deforestation risk scoring (from base calculator)
  3. Methane Intensity          — livestock enteric + manure CH4, abatement options (NEW)
  4. Disease Outbreak Risk      — biosecurity scoring, economic loss scenarios (NEW)
  5. Soil Carbon                — regenerative sequestration, credit potential (from base calculator)
  6. Biodiversity Net Gain      — DEFRA Metric 4.0, habitat unit accounting (NEW)

Data Flow:
  Farm/land data → climate scenario overlay → sector-specific risk modules →
  financial impact quantification → regulatory compliance check → adaptation plan

References:
  - IPCC AR6 WGIII Ch.7 — Agriculture, Forestry and Other Land Use
  - IPCC 2019 Refinement to 2006 Guidelines (Tier 1/2 livestock)
  - FAO GLEAM v3.0 — Global Livestock Environmental Assessment Model
  - EU Regulation 2023/1115 (EUDR) — Deforestation-free supply chains
  - Natural England BNG Metric 4.0 — Biodiversity Net Gain Calculations
  - Environment Act 2021 (UK) Schedule 14 — mandatory 10% BNG
  - OIE/WOAH Terrestrial Animal Health Code (disease classification)
  - Verra VM0042 — Improved Agricultural Land Management
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Re-export base calculator functions for backward compatibility
from services.agriculture_risk_calculator import (
    AgricultureRiskInput,
    AgricultureRiskResult,
    calculate_agriculture_risk,
    get_reference_data as get_base_reference_data,
)

logger = logging.getLogger("platform.agriculture_risk_engine")


# ═══════════════════════════════════════════════════════════════════════════
#  Reference Data — Livestock Methane
# ═══════════════════════════════════════════════════════════════════════════

# Enteric fermentation emission factors (kg CH4 / head / year)
# Source: IPCC 2019 Refinement, Table 10.11 (Tier 1 defaults, global average)
_ENTERIC_CH4_KG_HEAD_YR: Dict[str, float] = {
    "dairy_cattle":     128.0,
    "beef_cattle":       66.0,
    "buffalo":           55.0,
    "sheep":              8.0,
    "goat":               5.0,
    "camel":             46.0,
    "horse":             18.0,
    "swine":              1.5,
    "poultry":            0.0,   # negligible enteric
    "other":             10.0,
}

# Manure management emission factors (kg CH4 / head / year)
# Source: IPCC 2019 Refinement, Table 10.14 (Tier 1, temperate climate)
_MANURE_CH4_KG_HEAD_YR: Dict[str, float] = {
    "dairy_cattle":      16.0,
    "beef_cattle":        4.0,
    "buffalo":            3.0,
    "sheep":              0.3,
    "goat":               0.2,
    "camel":              2.0,
    "horse":              2.5,
    "swine":              7.0,
    "poultry":            0.02,
    "other":              1.0,
}

# CH4 Global Warming Potential (AR6 100-year)
_CH4_GWP_100 = 27.9   # IPCC AR6 WGI Table 7.15

# Methane abatement options with cost and reduction potential
_ABATEMENT_OPTIONS: List[Dict] = [
    {"name": "Feed additives (3-NOP)", "reduction_pct": 30.0, "cost_eur_head_yr": 25.0,
     "applicability": ["dairy_cattle", "beef_cattle"], "maturity": "commercial"},
    {"name": "Improved feed quality", "reduction_pct": 15.0, "cost_eur_head_yr": 10.0,
     "applicability": ["dairy_cattle", "beef_cattle", "sheep", "goat"], "maturity": "proven"},
    {"name": "Anaerobic digestion (manure)", "reduction_pct": 60.0, "cost_eur_head_yr": 40.0,
     "applicability": ["dairy_cattle", "beef_cattle", "swine"], "maturity": "commercial"},
    {"name": "Covered lagoon (manure)", "reduction_pct": 40.0, "cost_eur_head_yr": 15.0,
     "applicability": ["dairy_cattle", "beef_cattle", "swine"], "maturity": "proven"},
    {"name": "Genetic selection (low-CH4)", "reduction_pct": 10.0, "cost_eur_head_yr": 5.0,
     "applicability": ["dairy_cattle", "beef_cattle"], "maturity": "emerging"},
    {"name": "Red seaweed supplement", "reduction_pct": 50.0, "cost_eur_head_yr": 35.0,
     "applicability": ["dairy_cattle", "beef_cattle"], "maturity": "pilot"},
    {"name": "Pasture management", "reduction_pct": 8.0, "cost_eur_head_yr": 3.0,
     "applicability": ["dairy_cattle", "beef_cattle", "sheep", "goat"], "maturity": "proven"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  Reference Data — Disease Outbreak
# ═══════════════════════════════════════════════════════════════════════════

# OIE/WOAH listed diseases with base annual outbreak probability and
# economic impact multiplier (fraction of herd value at risk)
_DISEASE_PROFILES: Dict[str, Dict] = {
    "foot_and_mouth":    {"base_prob": 0.02, "mortality_pct": 5.0, "cull_pct": 50.0, "trade_ban_days": 90, "species": ["cattle", "sheep", "goat", "swine"]},
    "avian_influenza":   {"base_prob": 0.05, "mortality_pct": 80.0, "cull_pct": 100.0, "trade_ban_days": 60, "species": ["poultry"]},
    "african_swine_fever":{"base_prob": 0.03, "mortality_pct": 90.0, "cull_pct": 100.0, "trade_ban_days": 120, "species": ["swine"]},
    "bovine_tb":         {"base_prob": 0.04, "mortality_pct": 2.0, "cull_pct": 15.0, "trade_ban_days": 30, "species": ["cattle"]},
    "lumpy_skin_disease":{"base_prob": 0.015, "mortality_pct": 5.0, "cull_pct": 10.0, "trade_ban_days": 45, "species": ["cattle"]},
    "bluetongue":        {"base_prob": 0.03, "mortality_pct": 30.0, "cull_pct": 5.0, "trade_ban_days": 30, "species": ["sheep", "cattle"]},
    "newcastle_disease": {"base_prob": 0.04, "mortality_pct": 70.0, "cull_pct": 100.0, "trade_ban_days": 30, "species": ["poultry"]},
    "porcine_reproductive_respiratory": {"base_prob": 0.08, "mortality_pct": 10.0, "cull_pct": 5.0, "trade_ban_days": 0, "species": ["swine"]},
}

# Biosecurity score modifiers
_BIOSECURITY_ADJUSTMENTS: Dict[str, float] = {
    "excellent": 0.3,   # 70% reduction in outbreak probability
    "good":     0.6,
    "moderate": 0.9,
    "poor":     1.4,
    "none":     2.0,
}

# Regional disease history multiplier
_REGIONAL_RISK: Dict[str, float] = {
    "low":     0.5,
    "moderate":1.0,
    "high":    2.0,
    "endemic": 3.0,
}


# ═══════════════════════════════════════════════════════════════════════════
#  Reference Data — Biodiversity Net Gain
# ═══════════════════════════════════════════════════════════════════════════

# Habitat types and baseline biodiversity units per hectare
# Source: Natural England Biodiversity Metric 4.0 (Technical Supplement)
_HABITAT_UNITS_PER_HA: Dict[str, float] = {
    "cropland":                    2.0,
    "improved_grassland":          4.0,
    "semi_natural_grassland":      6.0,
    "mixed_woodland":              12.0,
    "native_woodland":             14.0,
    "heathland":                   8.0,
    "wetland":                     10.0,
    "scrub":                       4.0,
    "hedgerow_per_km":             8.0,   # linear habitat, per km
    "river_per_km":                12.0,
    "urban_greenspace":            3.0,
    "brownfield":                  1.0,
    "arable_field_margin":         5.0,
    "orchard":                     7.0,
    "pond":                        6.0,
    "bare_ground":                 0.5,
}

# Condition multipliers (Natural England condition assessment)
_CONDITION_MULTIPLIER: Dict[str, float] = {
    "good":     1.0,
    "moderate": 0.67,
    "poor":     0.33,
}

# Strategic significance multiplier
_SIGNIFICANCE_MULTIPLIER: Dict[str, float] = {
    "high":    1.15,
    "medium":  1.10,
    "low":     1.0,
}

# BNG credit market price (GBP per biodiversity unit)
# Source: Market data 2024-2025 (wide range, using midpoint)
_BNG_CREDIT_PRICE_GBP = 42_000.0

# Mandatory minimum net gain (Environment Act 2021)
_MANDATORY_NET_GAIN_PCT = 10.0


# ═══════════════════════════════════════════════════════════════════════════
#  3. Methane Intensity Module
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class LivestockMethaneInput:
    entity_id: str
    entity_name: str
    livestock_type: str = "dairy_cattle"
    herd_size: int = 500
    feed_system: str = "mixed"          # grazing | feedlot | mixed
    region: str = "temperate"           # tropical | temperate | boreal
    manure_management: str = "pasture"  # pasture | pit | lagoon | digester
    current_abatement: List[str] = field(default_factory=list)


@dataclass
class LivestockMethaneResult:
    entity_id: str
    entity_name: str
    livestock_type: str
    herd_size: int
    # Emissions
    enteric_ch4_tonnes_yr: float
    manure_ch4_tonnes_yr: float
    total_ch4_tonnes_yr: float
    total_tco2e_yr: float
    intensity_kgch4_per_head: float
    intensity_tco2e_per_head: float
    # Abatement
    abatement_options: List[Dict]
    max_abatement_potential_pct: float
    cost_per_tco2e_abated_eur: float
    # Benchmarks
    sector_avg_intensity_kgch4: float
    intensity_vs_sector_pct: float
    methodology_ref: str


def calculate_methane_intensity(inp: LivestockMethaneInput) -> LivestockMethaneResult:
    """
    Calculate livestock methane emissions (enteric + manure) using IPCC Tier 1
    defaults and identify applicable abatement options with costs.
    """
    lt = inp.livestock_type.lower()
    enteric_ef = _ENTERIC_CH4_KG_HEAD_YR.get(lt, _ENTERIC_CH4_KG_HEAD_YR["other"])
    manure_ef = _MANURE_CH4_KG_HEAD_YR.get(lt, _MANURE_CH4_KG_HEAD_YR["other"])

    # Regional adjustment for enteric (tropical = +10%, boreal = -10%)
    region_adj = {"tropical": 1.10, "temperate": 1.0, "boreal": 0.90}.get(inp.region, 1.0)
    enteric_ef *= region_adj

    # Feed system adjustment
    feed_adj = {"grazing": 1.05, "feedlot": 0.85, "mixed": 1.0}.get(inp.feed_system, 1.0)
    enteric_ef *= feed_adj

    # Manure management adjustment
    manure_adj = {"pasture": 0.5, "pit": 1.5, "lagoon": 2.0, "digester": 0.3}.get(inp.manure_management, 1.0)
    manure_ef *= manure_adj

    # Total emissions
    enteric_total = enteric_ef * inp.herd_size / 1000.0  # tonnes CH4/yr
    manure_total = manure_ef * inp.herd_size / 1000.0
    total_ch4 = enteric_total + manure_total
    total_co2e = total_ch4 * _CH4_GWP_100

    # Intensity
    intensity_kg = (enteric_ef + manure_ef)
    intensity_tco2e = intensity_kg * _CH4_GWP_100 / 1000.0

    # Sector average (generic livestock)
    base_enteric = _ENTERIC_CH4_KG_HEAD_YR.get(lt, 10.0)
    base_manure = _MANURE_CH4_KG_HEAD_YR.get(lt, 1.0)
    sector_avg = base_enteric + base_manure
    intensity_vs_sector = ((intensity_kg / sector_avg) - 1.0) * 100 if sector_avg > 0 else 0

    # Abatement options
    applicable = []
    species_key = lt.replace("dairy_", "").replace("beef_", "")
    for opt in _ABATEMENT_OPTIONS:
        if lt in opt["applicability"] or species_key in [a.replace("dairy_", "").replace("beef_", "") for a in opt["applicability"]]:
            already_applied = opt["name"] in inp.current_abatement
            applicable.append({
                "name": opt["name"],
                "reduction_pct": opt["reduction_pct"],
                "cost_eur_head_yr": opt["cost_eur_head_yr"],
                "cost_eur_tco2e": round(
                    opt["cost_eur_head_yr"] / max(intensity_tco2e * opt["reduction_pct"] / 100, 0.001), 1
                ),
                "maturity": opt["maturity"],
                "already_applied": already_applied,
            })

    max_abatement = sum(o["reduction_pct"] for o in applicable if not o.get("already_applied"))
    max_abatement = min(max_abatement, 85.0)  # cap at 85% total

    avg_cost = (
        sum(o["cost_eur_tco2e"] for o in applicable if not o.get("already_applied"))
        / max(len([o for o in applicable if not o.get("already_applied")]), 1)
    )

    return LivestockMethaneResult(
        entity_id=inp.entity_id,
        entity_name=inp.entity_name,
        livestock_type=lt,
        herd_size=inp.herd_size,
        enteric_ch4_tonnes_yr=round(enteric_total, 3),
        manure_ch4_tonnes_yr=round(manure_total, 3),
        total_ch4_tonnes_yr=round(total_ch4, 3),
        total_tco2e_yr=round(total_co2e, 1),
        intensity_kgch4_per_head=round(intensity_kg, 2),
        intensity_tco2e_per_head=round(intensity_tco2e, 3),
        abatement_options=applicable,
        max_abatement_potential_pct=round(max_abatement, 1),
        cost_per_tco2e_abated_eur=round(avg_cost, 1),
        sector_avg_intensity_kgch4=round(sector_avg, 2),
        intensity_vs_sector_pct=round(intensity_vs_sector, 1),
        methodology_ref="IPCC 2019 Refinement Tier 1 | FAO GLEAM v3.0 | GWP-100 AR6 (27.9)",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  4. Disease Outbreak Risk Module
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class DiseaseOutbreakInput:
    entity_id: str
    entity_name: str
    herd_value_eur: float = 1_000_000.0
    herd_size: int = 500
    species: str = "cattle"             # cattle | sheep | goat | swine | poultry
    biosecurity_level: str = "moderate" # excellent | good | moderate | poor | none
    regional_disease_history: str = "moderate"  # low | moderate | high | endemic
    insurance_coverage_pct: float = 50.0
    vaccination_programme: bool = True
    climate_warming_c: float = 1.5      # affects vector-borne disease spread


@dataclass
class DiseaseOutbreakResult:
    entity_id: str
    entity_name: str
    species: str
    herd_value_eur: float
    # Per-disease risk
    disease_risks: List[Dict]
    # Aggregated
    combined_outbreak_prob_annual: float
    expected_annual_loss_eur: float
    worst_case_loss_eur: float
    insurance_gap_eur: float
    supply_disruption_days_expected: float
    # Scores
    biosecurity_score: float            # 0-100
    overall_disease_risk_score: float   # 0-100
    risk_category: str
    recommendations: List[str]
    methodology_ref: str


def calculate_disease_outbreak_risk(inp: DiseaseOutbreakInput) -> DiseaseOutbreakResult:
    """
    Assess disease outbreak risk for livestock operations using OIE/WOAH
    disease profiles, biosecurity scoring, and climate-adjusted probabilities.
    """
    biosec_adj = _BIOSECURITY_ADJUSTMENTS.get(inp.biosecurity_level, 1.0)
    regional_adj = _REGIONAL_RISK.get(inp.regional_disease_history, 1.0)
    vacc_adj = 0.6 if inp.vaccination_programme else 1.0

    # Climate adjustment: warming increases vector-borne disease transmission
    climate_adj = 1.0 + max(0, inp.climate_warming_c - 1.0) * 0.15

    species_map = {
        "cattle": ["cattle"],
        "dairy_cattle": ["cattle"],
        "beef_cattle": ["cattle"],
        "sheep": ["sheep"],
        "goat": ["goat"],
        "swine": ["swine"],
        "poultry": ["poultry"],
    }
    target_species = species_map.get(inp.species, [inp.species])

    disease_risks = []
    combined_no_outbreak = 1.0
    total_expected_loss = 0.0
    worst_case = 0.0
    total_disruption = 0.0

    for disease_name, profile in _DISEASE_PROFILES.items():
        # Check if disease affects this species
        if not any(s in profile["species"] for s in target_species):
            continue

        # Adjusted probability
        adj_prob = profile["base_prob"] * biosec_adj * regional_adj * vacc_adj * climate_adj
        adj_prob = min(0.95, adj_prob)

        # Economic loss if outbreak occurs
        mortality_loss = inp.herd_value_eur * (profile["mortality_pct"] / 100.0)
        cull_loss = inp.herd_value_eur * (profile["cull_pct"] / 100.0) * 0.5  # partial compensation
        trade_loss = inp.herd_value_eur * 0.1 * (profile["trade_ban_days"] / 365.0)
        total_if_outbreak = mortality_loss + cull_loss + trade_loss

        expected_loss = adj_prob * total_if_outbreak
        total_expected_loss += expected_loss

        combined_no_outbreak *= (1 - adj_prob)
        worst_case = max(worst_case, total_if_outbreak)
        total_disruption += adj_prob * profile["trade_ban_days"]

        disease_risks.append({
            "disease": disease_name,
            "adjusted_probability": round(adj_prob, 4),
            "loss_if_outbreak_eur": round(total_if_outbreak, 0),
            "expected_annual_loss_eur": round(expected_loss, 0),
            "mortality_pct": profile["mortality_pct"],
            "cull_pct": profile["cull_pct"],
            "trade_ban_days": profile["trade_ban_days"],
        })

    combined_prob = 1 - combined_no_outbreak

    # Insurance gap
    insured_amount = inp.herd_value_eur * (inp.insurance_coverage_pct / 100.0)
    insurance_gap = max(0, worst_case - insured_amount)

    # Biosecurity score (0-100)
    biosec_scores = {"excellent": 95, "good": 75, "moderate": 50, "poor": 25, "none": 5}
    biosec_score = biosec_scores.get(inp.biosecurity_level, 50)

    # Overall risk score
    risk_score = min(100, combined_prob * 100 * 2 + (100 - biosec_score) * 0.3)

    if risk_score >= 70:
        risk_cat = "critical"
    elif risk_score >= 50:
        risk_cat = "high"
    elif risk_score >= 30:
        risk_cat = "moderate"
    else:
        risk_cat = "low"

    # Recommendations
    recs = []
    if biosec_score < 60:
        recs.append(f"Upgrade biosecurity from '{inp.biosecurity_level}' — target 'good' or 'excellent'")
    if not inp.vaccination_programme:
        recs.append("Implement vaccination programme for priority diseases")
    if inp.insurance_coverage_pct < 70:
        recs.append(f"Insurance covers {inp.insurance_coverage_pct}% — gap of EUR {insurance_gap:,.0f} in worst case")
    if inp.regional_disease_history in ("high", "endemic"):
        recs.append("High regional disease prevalence — enhanced surveillance recommended")
    if inp.climate_warming_c > 2.0:
        recs.append("Vector-borne disease risk elevated under >2°C warming — monitor emerging threats")

    disease_risks.sort(key=lambda d: d["expected_annual_loss_eur"], reverse=True)

    return DiseaseOutbreakResult(
        entity_id=inp.entity_id,
        entity_name=inp.entity_name,
        species=inp.species,
        herd_value_eur=inp.herd_value_eur,
        disease_risks=disease_risks,
        combined_outbreak_prob_annual=round(combined_prob, 4),
        expected_annual_loss_eur=round(total_expected_loss, 0),
        worst_case_loss_eur=round(worst_case, 0),
        insurance_gap_eur=round(insurance_gap, 0),
        supply_disruption_days_expected=round(total_disruption, 1),
        biosecurity_score=biosec_score,
        overall_disease_risk_score=round(risk_score, 1),
        risk_category=risk_cat,
        recommendations=recs,
        methodology_ref="OIE/WOAH Terrestrial Code | IPCC AR6 climate-health | FAO EMPRES",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  6. Biodiversity Net Gain Module
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BNGHabitatParcel:
    """A parcel of habitat for BNG calculation."""
    habitat_type: str
    area_ha: float = 0.0
    length_km: float = 0.0              # for linear habitats (hedgerow, river)
    condition: str = "moderate"         # good | moderate | poor
    strategic_significance: str = "low" # high | medium | low


@dataclass
class BNGInput:
    entity_id: str
    entity_name: str
    site_area_ha: float
    baseline_habitats: List[BNGHabitatParcel] = field(default_factory=list)
    proposed_habitats: List[BNGHabitatParcel] = field(default_factory=list)
    development_type: str = "residential"   # residential | commercial | infrastructure | agriculture
    local_planning_authority: str = ""
    mandatory_gain_pct: float = 10.0        # Environment Act 2021 default


@dataclass
class BNGResult:
    entity_id: str
    entity_name: str
    # Baseline
    baseline_habitat_units: float
    baseline_area_breakdown: Dict[str, float]
    # Proposed
    proposed_habitat_units: float
    proposed_area_breakdown: Dict[str, float]
    # Net gain
    net_change_units: float
    net_gain_pct: float
    meets_mandatory_requirement: bool
    # Credits
    bng_credits_required: float         # if net gain < 10%, credits needed
    credit_cost_eur: float
    # Per-habitat detail
    habitat_details: List[Dict]
    # Planning
    risk_rating: str
    recommendations: List[str]
    methodology_ref: str


def _calc_habitat_units(parcels: List[BNGHabitatParcel]) -> Tuple[float, Dict[str, float], List[Dict]]:
    """Calculate total biodiversity units for a set of habitat parcels."""
    total = 0.0
    breakdown: Dict[str, float] = {}
    details = []
    for p in parcels:
        base = _HABITAT_UNITS_PER_HA.get(p.habitat_type, 2.0)
        cond = _CONDITION_MULTIPLIER.get(p.condition, 0.67)
        sig = _SIGNIFICANCE_MULTIPLIER.get(p.strategic_significance, 1.0)

        if p.length_km > 0:
            # Linear habitat
            base_linear = _HABITAT_UNITS_PER_HA.get(p.habitat_type, 4.0)
            units = base_linear * p.length_km * cond * sig
        else:
            units = base * p.area_ha * cond * sig

        total += units
        breakdown[p.habitat_type] = breakdown.get(p.habitat_type, 0.0) + units
        details.append({
            "habitat_type": p.habitat_type,
            "area_ha": p.area_ha,
            "length_km": p.length_km,
            "condition": p.condition,
            "significance": p.strategic_significance,
            "biodiversity_units": round(units, 2),
        })

    return total, {k: round(v, 2) for k, v in breakdown.items()}, details


def calculate_biodiversity_net_gain(inp: BNGInput) -> BNGResult:
    """
    Calculate Biodiversity Net Gain using DEFRA Metric 4.0 methodology.
    Compares baseline vs proposed habitat units and identifies credit requirements.
    """
    baseline_units, baseline_breakdown, baseline_details = _calc_habitat_units(inp.baseline_habitats)
    proposed_units, proposed_breakdown, proposed_details = _calc_habitat_units(inp.proposed_habitats)

    net_change = proposed_units - baseline_units
    net_gain_pct = (net_change / baseline_units * 100) if baseline_units > 0 else 0.0

    meets_req = net_gain_pct >= inp.mandatory_gain_pct

    # Credits required if shortfall
    required_gain_units = baseline_units * (inp.mandatory_gain_pct / 100.0)
    shortfall = max(0, required_gain_units - net_change)
    credit_cost_gbp = shortfall * _BNG_CREDIT_PRICE_GBP
    credit_cost_eur = credit_cost_gbp * 1.17  # approximate GBP→EUR

    recs = []
    if not meets_req:
        recs.append(f"Shortfall of {shortfall:.1f} biodiversity units — purchase {shortfall:.1f} BNG credits "
                     f"(est. EUR {credit_cost_eur:,.0f})")
    if any(p.condition == "poor" for p in inp.proposed_habitats):
        recs.append("Proposed habitats include 'poor' condition parcels — improve condition for more units")
    if not any(p.strategic_significance == "high" for p in inp.proposed_habitats):
        recs.append("No high-significance habitats in proposal — consider strategic locations for 15% bonus")
    if net_gain_pct > 20:
        recs.append(f"Net gain {net_gain_pct:.0f}% exceeds requirement — surplus credits may be tradeable")

    # Combine details
    all_details = [{"phase": "baseline", **d} for d in baseline_details]
    all_details += [{"phase": "proposed", **d} for d in proposed_details]

    if net_gain_pct < 0:
        risk = "critical"
    elif not meets_req:
        risk = "high"
    elif net_gain_pct < inp.mandatory_gain_pct * 1.5:
        risk = "moderate"
    else:
        risk = "low"

    return BNGResult(
        entity_id=inp.entity_id,
        entity_name=inp.entity_name,
        baseline_habitat_units=round(baseline_units, 2),
        baseline_area_breakdown=baseline_breakdown,
        proposed_habitat_units=round(proposed_units, 2),
        proposed_area_breakdown=proposed_breakdown,
        net_change_units=round(net_change, 2),
        net_gain_pct=round(net_gain_pct, 1),
        meets_mandatory_requirement=meets_req,
        bng_credits_required=round(shortfall, 2),
        credit_cost_eur=round(credit_cost_eur, 0),
        habitat_details=all_details,
        risk_rating=risk,
        recommendations=recs,
        methodology_ref="Natural England BNG Metric 4.0 | Environment Act 2021 Sched.14 | DEFRA Habitat Classification",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Combined Reference Data
# ═══════════════════════════════════════════════════════════════════════════

def get_agriculture_engine_reference_data() -> dict:
    """Return all reference data used by the expanded Agriculture Risk Engine."""
    base = get_base_reference_data()
    base.update({
        # Methane
        "enteric_ch4_kg_head_yr": _ENTERIC_CH4_KG_HEAD_YR,
        "manure_ch4_kg_head_yr": _MANURE_CH4_KG_HEAD_YR,
        "ch4_gwp_100": _CH4_GWP_100,
        "abatement_options": [
            {"name": o["name"], "reduction_pct": o["reduction_pct"],
             "cost_eur_head_yr": o["cost_eur_head_yr"], "maturity": o["maturity"]}
            for o in _ABATEMENT_OPTIONS
        ],
        # Disease
        "disease_profiles": {
            k: {"base_prob": v["base_prob"], "mortality_pct": v["mortality_pct"],
                "trade_ban_days": v["trade_ban_days"]}
            for k, v in _DISEASE_PROFILES.items()
        },
        "biosecurity_adjustments": _BIOSECURITY_ADJUSTMENTS,
        # BNG
        "habitat_units_per_ha": _HABITAT_UNITS_PER_HA,
        "condition_multipliers": _CONDITION_MULTIPLIER,
        "bng_credit_price_gbp": _BNG_CREDIT_PRICE_GBP,
        "mandatory_net_gain_pct": _MANDATORY_NET_GAIN_PCT,
        "sources": base.get("sources", []) + [
            "IPCC 2019 Refinement — Tier 1 Livestock Emission Factors",
            "FAO GLEAM v3.0 — Global Livestock Environmental Assessment Model",
            "OIE/WOAH Terrestrial Animal Health Code",
            "Natural England Biodiversity Metric 4.0",
            "UK Environment Act 2021 Schedule 14 (Biodiversity Net Gain)",
        ],
    })
    return base
