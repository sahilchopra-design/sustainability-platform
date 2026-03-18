"""
Commercial Real Estate Climate Engine
======================================
CRREM 2.0 · EPC/EPBD 2024 · GRESB Real Estate (2024) · REFI Protocol ·
NABERS · Green Lease · Retrofit NPV/IRR

Sub-modules:
  1. CRREM 2.0 Assessment     — Stranding year and decarbonisation pathway
  2. EPC / EPBD 2024          — Energy performance certificate & directive compliance
  3. GRESB Scoring            — Real Estate assessment score (1-5 stars)
  4. REFI Protocol            — Real Estate Finance risk tiering
  5. NABERS Rating            — National Australian Built Environment Rating System
  6. Green Lease Assessment   — Standard green lease clause scoring
  7. Retrofit NPV/IRR         — Measure-level retrofit financial modelling
  8. Full Assessment          — Consolidated property report with green/brown premium

References:
  - CRREM v2.0 (Carbon Risk Real Estate Monitor, 2022)
  - EPBD Recast Directive 2024/1275/EU
  - GRESB Real Estate Assessment 2024
  - REFI Protocol (Real Estate Finance) v1.0, 2020
  - NABERS Energy for Offices (2021)
  - RICS Building Sustainability Toolkit
  - JLL Green Building Premium Research 2023
"""
from __future__ import annotations

import math
import uuid
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# CRREM 2.0 carbon intensity pathways kgCO2/m²/yr
# Asset types: office, retail, logistics, hotel, industrial, residential
# Countries: UK, DE, FR, NL, US, AU
CRREM_PATHWAYS: dict[str, dict[str, dict[str, float]]] = {
    "office": {
        "UK": {"2025": 28.0, "2030": 18.0, "2035": 12.0, "2040": 7.0, "2050": 2.0},
        "DE": {"2025": 22.0, "2030": 15.0, "2035": 9.0,  "2040": 5.0, "2050": 1.5},
        "FR": {"2025": 18.0, "2030": 12.0, "2035": 7.0,  "2040": 4.0, "2050": 1.2},
        "NL": {"2025": 20.0, "2030": 13.0, "2035": 8.0,  "2040": 4.5, "2050": 1.3},
        "US": {"2025": 45.0, "2030": 30.0, "2035": 18.0, "2040": 10.0,"2050": 3.0},
        "AU": {"2025": 50.0, "2030": 35.0, "2035": 22.0, "2040": 12.0,"2050": 4.0},
    },
    "retail": {
        "UK": {"2025": 32.0, "2030": 21.0, "2035": 13.0, "2040": 7.5, "2050": 2.2},
        "DE": {"2025": 26.0, "2030": 17.0, "2035": 11.0, "2040": 6.0, "2050": 1.8},
        "FR": {"2025": 22.0, "2030": 14.0, "2035": 9.0,  "2040": 5.0, "2050": 1.5},
        "NL": {"2025": 24.0, "2030": 15.5, "2035": 9.5,  "2040": 5.5, "2050": 1.6},
        "US": {"2025": 52.0, "2030": 35.0, "2035": 22.0, "2040": 12.0,"2050": 4.0},
        "AU": {"2025": 58.0, "2030": 40.0, "2035": 25.0, "2040": 14.0,"2050": 5.0},
    },
    "logistics": {
        "UK": {"2025": 15.0, "2030": 9.5, "2035": 6.0,  "2040": 3.5, "2050": 1.0},
        "DE": {"2025": 12.0, "2030": 7.5, "2035": 4.5,  "2040": 2.5, "2050": 0.8},
        "FR": {"2025": 10.0, "2030": 6.0, "2035": 3.5,  "2040": 2.0, "2050": 0.6},
        "NL": {"2025": 11.0, "2030": 7.0, "2035": 4.2,  "2040": 2.3, "2050": 0.7},
        "US": {"2025": 28.0, "2030": 18.0, "2035": 11.0, "2040": 6.0, "2050": 2.0},
        "AU": {"2025": 32.0, "2030": 21.0, "2035": 13.0, "2040": 7.0, "2050": 2.5},
    },
    "hotel": {
        "UK": {"2025": 42.0, "2030": 28.0, "2035": 17.0, "2040": 10.0,"2050": 3.0},
        "DE": {"2025": 35.0, "2030": 23.0, "2035": 14.0, "2040": 8.0, "2050": 2.5},
        "FR": {"2025": 30.0, "2030": 19.0, "2035": 12.0, "2040": 6.5, "2050": 2.0},
        "NL": {"2025": 32.0, "2030": 21.0, "2035": 13.0, "2040": 7.0, "2050": 2.2},
        "US": {"2025": 65.0, "2030": 44.0, "2035": 27.0, "2040": 15.0,"2050": 5.0},
        "AU": {"2025": 72.0, "2030": 49.0, "2035": 30.0, "2040": 17.0,"2050": 6.0},
    },
    "industrial": {
        "UK": {"2025": 38.0, "2030": 25.0, "2035": 15.0, "2040": 8.5, "2050": 2.8},
        "DE": {"2025": 30.0, "2030": 19.0, "2035": 12.0, "2040": 6.5, "2050": 2.0},
        "FR": {"2025": 25.0, "2030": 16.0, "2035": 10.0, "2040": 5.5, "2050": 1.7},
        "NL": {"2025": 28.0, "2030": 18.0, "2035": 11.0, "2040": 6.0, "2050": 1.9},
        "US": {"2025": 55.0, "2030": 37.0, "2035": 23.0, "2040": 12.0,"2050": 4.5},
        "AU": {"2025": 62.0, "2030": 42.0, "2035": 26.0, "2040": 14.0,"2050": 5.0},
    },
    "residential": {
        "UK": {"2025": 22.0, "2030": 14.0, "2035": 8.5,  "2040": 5.0, "2050": 1.5},
        "DE": {"2025": 18.0, "2030": 11.5, "2035": 7.0,  "2040": 4.0, "2050": 1.2},
        "FR": {"2025": 15.0, "2030": 9.5,  "2035": 5.8,  "2040": 3.2, "2050": 0.9},
        "NL": {"2025": 16.0, "2030": 10.0, "2035": 6.0,  "2040": 3.4, "2050": 1.0},
        "US": {"2025": 35.0, "2030": 22.0, "2035": 14.0, "2040": 7.5, "2050": 2.5},
        "AU": {"2025": 40.0, "2030": 26.0, "2035": 16.0, "2040": 9.0, "2050": 3.0},
    },
}

EPC_THRESHOLDS: dict[str, dict[str, float]] = {
    "UK": {"A": 50.0, "B": 75.0, "C": 100.0, "D": 125.0, "E": 150.0, "F": 175.0, "G": 999.0},
    "DE": {"A+": 30.0, "A": 50.0, "B": 75.0, "C": 100.0, "D": 130.0, "E": 160.0, "F": 200.0, "G": 250.0, "H": 999.0},
    "FR": {"A": 50.0, "B": 90.0, "C": 150.0, "D": 230.0, "E": 330.0, "F": 450.0, "G": 999.0},
    "NL": {"A++": 0.0, "A+": 50.0, "A": 75.0, "B": 100.0, "C": 150.0, "D": 200.0, "E": 250.0, "F": 300.0, "G": 999.0},
    "US": {"A": 50.0, "B": 75.0, "C": 100.0, "D": 130.0, "E": 160.0, "F": 200.0, "G": 999.0},
    "AU": {"A": 45.0, "B": 80.0, "C": 120.0, "D": 160.0, "E": 200.0, "F": 250.0, "G": 999.0},
}

EPBD_2024_REQUIREMENTS: dict[str, dict] = {
    "commercial": {
        "minimum_epc_by_2030": "E",
        "minimum_epc_by_2033": "D",
        "renovation_trigger": "major_renovation_or_sale",
    },
    "residential": {
        "minimum_epc_by_2030": "E",
        "minimum_epc_by_2033": "D",
        "renovation_trigger": "sale_or_rental",
    },
    "public": {
        "minimum_epc_by_2030": "C",
        "minimum_epc_by_2033": "B",
        "renovation_trigger": "renovation_over_25pct_value",
    },
    "industrial": {
        "minimum_epc_by_2030": "E",
        "minimum_epc_by_2033": "D",
        "renovation_trigger": "major_renovation",
    },
}

# GRESB scoring weights (total 100)
GRESB_SCORING: dict[str, dict] = {
    "management_criteria": {
        "leadership": {"weight": 5.0, "max_score": 10},
        "policies": {"weight": 8.0, "max_score": 10},
        "reporting": {"weight": 7.0, "max_score": 10},
        "risk_management": {"weight": 8.0, "max_score": 10},
        "stakeholder_engagement": {"weight": 5.0, "max_score": 10},
    },
    "performance_criteria": {
        "energy": {"weight": 22.0, "max_score": 100},
        "ghg": {"weight": 18.0, "max_score": 100},
        "water": {"weight": 10.0, "max_score": 100},
        "waste": {"weight": 8.0, "max_score": 100},
        "land_ecosystem": {"weight": 9.0, "max_score": 100},
    },
}

REFI_RISK_TIERS: dict[str, dict] = {
    "tier1": {"composite_min": 0,   "composite_max": 20,  "label": "Very Low Risk"},
    "tier2": {"composite_min": 20,  "composite_max": 40,  "label": "Low Risk"},
    "tier3": {"composite_min": 40,  "composite_max": 60,  "label": "Medium Risk"},
    "tier4": {"composite_min": 60,  "composite_max": 80,  "label": "High Risk"},
    "tier5": {"composite_min": 80,  "composite_max": 100, "label": "Very High Risk"},
}

NABERS_BENCHMARKS: dict[str, dict] = {
    "office":       {"1_star_kwh_m2": 400.0, "3_star_kwh_m2": 250.0, "5_star_kwh_m2": 150.0, "6_star_kwh_m2": 100.0},
    "retail":       {"1_star_kwh_m2": 500.0, "3_star_kwh_m2": 300.0, "5_star_kwh_m2": 180.0, "6_star_kwh_m2": 120.0},
    "hotel":        {"1_star_kwh_m2": 600.0, "3_star_kwh_m2": 380.0, "5_star_kwh_m2": 220.0, "6_star_kwh_m2": 150.0},
    "industrial":   {"1_star_kwh_m2": 300.0, "3_star_kwh_m2": 180.0, "5_star_kwh_m2": 110.0, "6_star_kwh_m2": 75.0},
    "residential":  {"1_star_kwh_m2": 200.0, "3_star_kwh_m2": 120.0, "5_star_kwh_m2": 70.0,  "6_star_kwh_m2": 45.0},
    "logistics":    {"1_star_kwh_m2": 180.0, "3_star_kwh_m2": 110.0, "5_star_kwh_m2": 65.0,  "6_star_kwh_m2": 42.0},
}

GREEN_LEASE_CLAUSES: list[dict] = [
    {"name": "energy_metering",          "category": "energy",      "score_weight": 10.0},
    {"name": "energy_reporting_sharing",  "category": "energy",      "score_weight": 8.0},
    {"name": "sub_metering",              "category": "energy",      "score_weight": 7.0},
    {"name": "water_metering",            "category": "water",       "score_weight": 7.0},
    {"name": "waste_management_plan",     "category": "waste",       "score_weight": 8.0},
    {"name": "green_fit_out_guide",       "category": "works",       "score_weight": 6.0},
    {"name": "no_objection_renewable",    "category": "energy",      "score_weight": 8.0},
    {"name": "epc_maintenance",           "category": "compliance",  "score_weight": 9.0},
    {"name": "ev_charging_provision",     "category": "transport",   "score_weight": 6.0},
    {"name": "biodiversity_commitments",  "category": "ecology",     "score_weight": 5.0},
    {"name": "tenant_reporting_kpis",     "category": "reporting",   "score_weight": 9.0},
    {"name": "lease_review_sustainability","category": "governance",  "score_weight": 7.0},
]

RETROFIT_MEASURES: dict[str, dict] = {
    "insulation":    {"typical_capex_per_m2": 45.0,  "energy_saving_pct": 20.0, "co2_saving_pct": 22.0, "lifetime_yrs": 30},
    "HVAC":          {"typical_capex_per_m2": 80.0,  "energy_saving_pct": 25.0, "co2_saving_pct": 25.0, "lifetime_yrs": 20},
    "LED":           {"typical_capex_per_m2": 18.0,  "energy_saving_pct": 12.0, "co2_saving_pct": 12.0, "lifetime_yrs": 15},
    "solar_PV":      {"typical_capex_per_m2": 150.0, "energy_saving_pct": 18.0, "co2_saving_pct": 30.0, "lifetime_yrs": 25},
    "heat_pump":     {"typical_capex_per_m2": 95.0,  "energy_saving_pct": 30.0, "co2_saving_pct": 40.0, "lifetime_yrs": 20},
    "glazing":       {"typical_capex_per_m2": 200.0, "energy_saving_pct": 10.0, "co2_saving_pct": 10.0, "lifetime_yrs": 25},
    "BMS":           {"typical_capex_per_m2": 25.0,  "energy_saving_pct": 15.0, "co2_saving_pct": 15.0, "lifetime_yrs": 15},
    "EV_charging":   {"typical_capex_per_m2": 12.0,  "energy_saving_pct": 0.0,  "co2_saving_pct": 5.0,  "lifetime_yrs": 15},
    "cool_roof":     {"typical_capex_per_m2": 30.0,  "energy_saving_pct": 8.0,  "co2_saving_pct": 8.0,  "lifetime_yrs": 20},
    "air_tightness": {"typical_capex_per_m2": 20.0,  "energy_saving_pct": 7.0,  "co2_saving_pct": 7.0,  "lifetime_yrs": 20},
}

GREEN_PREMIUM_EVIDENCE: dict[str, dict[str, dict]] = {
    "UK": {
        "office":    {"premium_pct": 8.5,  "brown_discount_pct": 6.0},
        "retail":    {"premium_pct": 5.0,  "brown_discount_pct": 4.0},
        "logistics": {"premium_pct": 6.0,  "brown_discount_pct": 5.0},
        "hotel":     {"premium_pct": 4.5,  "brown_discount_pct": 3.5},
    },
    "DE": {
        "office":    {"premium_pct": 7.0,  "brown_discount_pct": 8.0},
        "retail":    {"premium_pct": 4.5,  "brown_discount_pct": 5.0},
        "logistics": {"premium_pct": 5.5,  "brown_discount_pct": 6.0},
        "hotel":     {"premium_pct": 4.0,  "brown_discount_pct": 4.0},
    },
    "FR": {
        "office":    {"premium_pct": 6.0,  "brown_discount_pct": 5.5},
        "retail":    {"premium_pct": 3.5,  "brown_discount_pct": 3.0},
        "logistics": {"premium_pct": 4.5,  "brown_discount_pct": 4.5},
        "hotel":     {"premium_pct": 3.5,  "brown_discount_pct": 3.0},
    },
    "US": {
        "office":    {"premium_pct": 10.0, "brown_discount_pct": 7.0},
        "retail":    {"premium_pct": 6.0,  "brown_discount_pct": 4.5},
        "logistics": {"premium_pct": 7.5,  "brown_discount_pct": 5.5},
        "hotel":     {"premium_pct": 5.5,  "brown_discount_pct": 4.0},
    },
    "AU": {
        "office":    {"premium_pct": 9.5,  "brown_discount_pct": 8.5},
        "retail":    {"premium_pct": 5.5,  "brown_discount_pct": 5.0},
        "logistics": {"premium_pct": 6.5,  "brown_discount_pct": 6.0},
        "hotel":     {"premium_pct": 5.0,  "brown_discount_pct": 4.5},
    },
    "NL": {
        "office":    {"premium_pct": 8.0,  "brown_discount_pct": 9.0},
        "retail":    {"premium_pct": 5.0,  "brown_discount_pct": 5.5},
        "logistics": {"premium_pct": 6.0,  "brown_discount_pct": 7.0},
        "hotel":     {"premium_pct": 4.5,  "brown_discount_pct": 4.5},
    },
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CRREMResult:
    entity_id: str
    asset_type: str
    country: str
    current_co2_kgco2_m2: float
    stranding_year: Optional[int]
    stranding_risk: str
    overconsumption_gap: float
    pathway_2030: float
    pathway_2050: float
    years_to_stranding: Optional[int]

@dataclass
class EPCResult:
    entity_id: str
    country: str
    building_type: str
    primary_energy_kwh_m2: float
    epc_rating: str
    epbd_renovation_required: bool
    minimum_threshold: str
    compliance_deadline: int
    current_meets_2030: bool
    current_meets_2033: bool

@dataclass
class GRESBResult:
    entity_id: str
    management_score: float
    performance_score: float
    total_score: float
    star_rating: int
    peer_percentile: float
    component_scores: dict

@dataclass
class REFIResult:
    entity_id: str
    physical_score: float
    transition_score: float
    composite_score: float
    risk_tier: str
    risk_label: str

@dataclass
class NABERSResult:
    entity_id: str
    asset_type: str
    annual_energy_kwh: float
    gross_area_m2: float
    energy_intensity_kwh_m2: float
    energy_stars: float
    water_stars: float
    indoor_stars: float

@dataclass
class GreenLeaseResult:
    entity_id: str
    clauses_present: list[str]
    clauses_missing: list[str]
    score: float
    grade: str
    total_weight_present: float

@dataclass
class RetrofitResult:
    entity_id: str
    measures: list[dict]
    total_capex: float
    total_energy_saving_kwh_pa: float
    total_co2_saving_kgpa: float
    crrem_year_improvement: int
    portfolio_irr: float
    portfolio_npv: float

# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class CommercialREEngine:
    """Pure computation — no DB calls."""

    # ------------------------------------------------------------------
    # 1. CRREM Assessment
    # ------------------------------------------------------------------
    def assess_crrem(
        self,
        entity_id: str,
        asset_type: str,
        country: str,
        energy_intensity_kwh_m2: float,
        co2_intensity_kgco2_m2: float,
    ) -> CRREMResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        country_pathways = CRREM_PATHWAYS.get(asset_type, CRREM_PATHWAYS["office"]).get(
            country, CRREM_PATHWAYS.get(asset_type, CRREM_PATHWAYS["office"]).get("UK", {})
        )

        pathway_2030 = country_pathways.get("2030", 20.0)
        pathway_2050 = country_pathways.get("2050", 3.0)

        # Find stranding year: when current intensity exceeds pathway
        stranding_year: Optional[int] = None
        years_to_stranding: Optional[int] = None
        for yr in [2025, 2030, 2035, 2040, 2050]:
            path_val = country_pathways.get(str(yr), pathway_2050)
            if co2_intensity_kgco2_m2 > path_val:
                stranding_year = yr
                years_to_stranding = yr - 2025
                break

        overconsumption_gap = max(0.0, co2_intensity_kgco2_m2 - pathway_2030)

        if stranding_year is None:
            stranding_risk = "low"
        elif stranding_year <= 2030:
            stranding_risk = "critical"
        elif stranding_year <= 2035:
            stranding_risk = "high"
        elif stranding_year <= 2040:
            stranding_risk = "medium"
        else:
            stranding_risk = "low"

        return CRREMResult(
            entity_id=entity_id,
            asset_type=asset_type,
            country=country,
            current_co2_kgco2_m2=round(co2_intensity_kgco2_m2, 3),
            stranding_year=stranding_year,
            stranding_risk=stranding_risk,
            overconsumption_gap=round(overconsumption_gap, 3),
            pathway_2030=pathway_2030,
            pathway_2050=pathway_2050,
            years_to_stranding=years_to_stranding,
        )

    # ------------------------------------------------------------------
    # 2. EPC / EPBD 2024
    # ------------------------------------------------------------------
    def assess_epc_epbd(
        self,
        entity_id: str,
        country: str,
        building_type: str,
        primary_energy_kwh_m2: float,
    ) -> EPCResult:
        thresholds = EPC_THRESHOLDS.get(country, EPC_THRESHOLDS["UK"])
        epbd = EPBD_2024_REQUIREMENTS.get(building_type, EPBD_2024_REQUIREMENTS["commercial"])

        # Determine EPC rating
        epc_rating = list(thresholds.keys())[-1]  # worst rating by default
        for rating, max_kwh in thresholds.items():
            if primary_energy_kwh_m2 <= max_kwh:
                epc_rating = rating
                break

        # Check EPBD compliance
        min_2030 = epbd["minimum_epc_by_2030"]
        min_2033 = epbd["minimum_epc_by_2033"]

        rating_order = list(thresholds.keys())
        current_idx = rating_order.index(epc_rating) if epc_rating in rating_order else len(rating_order) - 1
        min_2030_idx = rating_order.index(min_2030) if min_2030 in rating_order else 0
        min_2033_idx = rating_order.index(min_2033) if min_2033 in rating_order else 0

        current_meets_2030 = current_idx <= min_2030_idx
        current_meets_2033 = current_idx <= min_2033_idx

        renovation_required = not current_meets_2033
        compliance_deadline = 2033 if not current_meets_2033 else (2030 if not current_meets_2030 else 9999)

        return EPCResult(
            entity_id=entity_id,
            country=country,
            building_type=building_type,
            primary_energy_kwh_m2=round(primary_energy_kwh_m2, 1),
            epc_rating=epc_rating,
            epbd_renovation_required=renovation_required,
            minimum_threshold=min_2033,
            compliance_deadline=compliance_deadline,
            current_meets_2030=current_meets_2030,
            current_meets_2033=current_meets_2033,
        )

    # ------------------------------------------------------------------
    # 3. GRESB Score
    # ------------------------------------------------------------------
    def calculate_gresb_score(
        self,
        entity_id: str,
        management_data: dict,
        performance_data: dict,
    ) -> GRESBResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        component_scores = {}
        management_score = 0.0
        performance_score = 0.0

        for criterion, cfg in GRESB_SCORING["management_criteria"].items():
            raw = management_data.get(criterion, rng.uniform(4.0, 9.0))
            weighted = raw * cfg["weight"] / 10.0
            component_scores[f"mgmt_{criterion}"] = round(weighted, 2)
            management_score += weighted

        for metric, cfg in GRESB_SCORING["performance_criteria"].items():
            raw = performance_data.get(metric, rng.uniform(50.0, 90.0))
            weighted = raw * cfg["weight"] / 100.0
            component_scores[f"perf_{metric}"] = round(weighted, 2)
            performance_score += weighted

        total_score = management_score + performance_score
        total_score = min(total_score, 100.0)

        # Star rating: 1-5 based on score
        if total_score >= 80:
            star_rating = 5
        elif total_score >= 65:
            star_rating = 4
        elif total_score >= 50:
            star_rating = 3
        elif total_score >= 35:
            star_rating = 2
        else:
            star_rating = 1

        peer_percentile = min(99.0, max(1.0, total_score * 0.95 + rng.uniform(-5, 5)))

        return GRESBResult(
            entity_id=entity_id,
            management_score=round(management_score, 2),
            performance_score=round(performance_score, 2),
            total_score=round(total_score, 2),
            star_rating=star_rating,
            peer_percentile=round(peer_percentile, 1),
            component_scores=component_scores,
        )

    # ------------------------------------------------------------------
    # 4. REFI Protocol
    # ------------------------------------------------------------------
    def assess_refi(
        self,
        entity_id: str,
        physical_risk_inputs: dict,
        transition_risk_inputs: dict,
    ) -> REFIResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Physical risk scoring (0-100)
        flood_risk = physical_risk_inputs.get("flood_risk_score", rng.uniform(10.0, 60.0))
        heat_stress = physical_risk_inputs.get("heat_stress_score", rng.uniform(10.0, 50.0))
        subsidence = physical_risk_inputs.get("subsidence_score", rng.uniform(5.0, 30.0))
        wind_risk = physical_risk_inputs.get("wind_risk_score", rng.uniform(5.0, 25.0))
        physical_score = (flood_risk * 0.35 + heat_stress * 0.30 + subsidence * 0.20 + wind_risk * 0.15)

        # Transition risk scoring (0-100)
        epc_risk = transition_risk_inputs.get("epc_compliance_risk", rng.uniform(10.0, 70.0))
        stranding_risk_val = transition_risk_inputs.get("stranding_risk_score", rng.uniform(10.0, 60.0))
        carbon_tax_exp = transition_risk_inputs.get("carbon_tax_exposure", rng.uniform(5.0, 40.0))
        retrofit_cost = transition_risk_inputs.get("retrofit_cost_score", rng.uniform(10.0, 55.0))
        transition_score = (epc_risk * 0.30 + stranding_risk_val * 0.30 + carbon_tax_exp * 0.20 + retrofit_cost * 0.20)

        composite_score = physical_score * 0.5 + transition_score * 0.5
        composite_score = min(100.0, max(0.0, composite_score))

        risk_tier = "tier3"
        risk_label = "Medium Risk"
        for tier, bounds in REFI_RISK_TIERS.items():
            if bounds["composite_min"] <= composite_score < bounds["composite_max"]:
                risk_tier = tier
                risk_label = bounds["label"]
                break

        return REFIResult(
            entity_id=entity_id,
            physical_score=round(physical_score, 2),
            transition_score=round(transition_score, 2),
            composite_score=round(composite_score, 2),
            risk_tier=risk_tier,
            risk_label=risk_label,
        )

    # ------------------------------------------------------------------
    # 5. NABERS Rating
    # ------------------------------------------------------------------
    def calculate_nabers(
        self,
        entity_id: str,
        asset_type: str,
        annual_energy_kwh: float,
        gross_area_m2: float,
        hours_pa: float = 2500.0,
    ) -> NABERSResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        energy_intensity = annual_energy_kwh / max(gross_area_m2, 1.0)  # kWh/m²
        benchmarks = NABERS_BENCHMARKS.get(asset_type, NABERS_BENCHMARKS["office"])

        # Interpolate stars (1 to 6)
        if energy_intensity >= benchmarks["1_star_kwh_m2"]:
            energy_stars = 1.0
        elif energy_intensity >= benchmarks["3_star_kwh_m2"]:
            # Between 1 and 3 stars
            t = (benchmarks["1_star_kwh_m2"] - energy_intensity) / max(benchmarks["1_star_kwh_m2"] - benchmarks["3_star_kwh_m2"], 1.0)
            energy_stars = 1.0 + t * 2.0
        elif energy_intensity >= benchmarks["5_star_kwh_m2"]:
            t = (benchmarks["3_star_kwh_m2"] - energy_intensity) / max(benchmarks["3_star_kwh_m2"] - benchmarks["5_star_kwh_m2"], 1.0)
            energy_stars = 3.0 + t * 2.0
        elif energy_intensity >= benchmarks["6_star_kwh_m2"]:
            t = (benchmarks["5_star_kwh_m2"] - energy_intensity) / max(benchmarks["5_star_kwh_m2"] - benchmarks["6_star_kwh_m2"], 1.0)
            energy_stars = 5.0 + t * 1.0
        else:
            energy_stars = 6.0

        energy_stars = round(min(6.0, max(1.0, energy_stars)), 1)

        # Water and indoor environment: seeded estimates
        water_stars = round(rng.uniform(2.5, 5.5), 1)
        indoor_stars = round(rng.uniform(3.0, 5.5), 1)

        return NABERSResult(
            entity_id=entity_id,
            asset_type=asset_type,
            annual_energy_kwh=round(annual_energy_kwh, 0),
            gross_area_m2=round(gross_area_m2, 0),
            energy_intensity_kwh_m2=round(energy_intensity, 2),
            energy_stars=energy_stars,
            water_stars=water_stars,
            indoor_stars=indoor_stars,
        )

    # ------------------------------------------------------------------
    # 6. Green Lease Assessment
    # ------------------------------------------------------------------
    def assess_green_lease(
        self,
        entity_id: str,
        lease_clauses_present: list[str],
    ) -> GreenLeaseResult:
        present_set = set(lease_clauses_present)
        total_weight = sum(c["score_weight"] for c in GREEN_LEASE_CLAUSES)
        present_weight = 0.0
        clauses_missing = []

        for clause in GREEN_LEASE_CLAUSES:
            if clause["name"] in present_set:
                present_weight += clause["score_weight"]
            else:
                clauses_missing.append(clause["name"])

        score = present_weight / max(total_weight, 1.0) * 100.0

        if score >= 85:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 55:
            grade = "C"
        elif score >= 40:
            grade = "D"
        else:
            grade = "E"

        return GreenLeaseResult(
            entity_id=entity_id,
            clauses_present=list(present_set),
            clauses_missing=clauses_missing,
            score=round(score, 2),
            grade=grade,
            total_weight_present=round(present_weight, 2),
        )

    # ------------------------------------------------------------------
    # 7. Retrofit NPV/IRR Modelling
    # ------------------------------------------------------------------
    def model_retrofit(
        self,
        entity_id: str,
        asset_type: str,
        current_energy_kwh_m2: float,
        floor_area_m2: float,
        discount_rate: float = 0.07,
        energy_price_kwh: float = 0.20,
    ) -> RetrofitResult:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Carbon intensity estimate (grid average 0.25 kgCO2/kWh)
        grid_co2_factor = 0.25

        measure_results = []
        total_capex = 0.0
        total_energy_saving = 0.0
        total_co2_saving = 0.0

        current_energy_total = current_energy_kwh_m2 * floor_area_m2

        for measure, props in RETROFIT_MEASURES.items():
            capex = props["typical_capex_per_m2"] * floor_area_m2
            energy_saving_pa = current_energy_total * props["energy_saving_pct"] / 100.0
            co2_saving_pa = current_energy_total * props["co2_saving_pct"] / 100.0 * grid_co2_factor * 1000.0  # kg

            annual_saving_value = energy_saving_pa * energy_price_kwh
            lifetime = props["lifetime_yrs"]

            # NPV
            npv = -capex
            for yr in range(1, lifetime + 1):
                npv += annual_saving_value / ((1.0 + discount_rate) ** yr)

            # Simple payback
            payback = capex / max(annual_saving_value, 0.01)

            # IRR approximation (Newton-Raphson)
            irr = 0.0
            if annual_saving_value > 0 and capex > 0:
                irr_guess = annual_saving_value / capex
                for _ in range(50):
                    npv_irr = -capex
                    dnpv = 0.0
                    for yr in range(1, lifetime + 1):
                        disc = (1.0 + irr_guess) ** yr
                        npv_irr += annual_saving_value / disc
                        dnpv -= yr * annual_saving_value / ((1.0 + irr_guess) ** (yr + 1))
                    if abs(dnpv) < 1e-10:
                        break
                    irr_guess -= npv_irr / dnpv
                irr = max(0.0, irr_guess)

            measure_results.append({
                "measure": measure,
                "capex": round(capex, 0),
                "energy_saving_pa_kwh": round(energy_saving_pa, 0),
                "co2_saving_pa_kg": round(co2_saving_pa, 0),
                "annual_saving_value_usd": round(annual_saving_value, 0),
                "npv": round(npv, 0),
                "irr_pct": round(irr * 100.0, 2),
                "payback_yrs": round(payback, 1),
                "lifetime_yrs": lifetime,
            })

            total_capex += capex
            total_energy_saving += energy_saving_pa
            total_co2_saving += co2_saving_pa

        # Sort by IRR descending
        measure_results.sort(key=lambda x: x["irr_pct"], reverse=True)

        # Estimate CRREM pathway year improvement
        crrem_year_improvement = int(total_co2_saving / max(floor_area_m2, 1.0) / 5.0)  # rough years

        # Portfolio NPV and IRR for top 5 measures
        top5 = measure_results[:5]
        total_capex_top5 = sum(m["capex"] for m in top5)
        total_annual_value_top5 = sum(m["annual_saving_value_usd"] for m in top5)
        avg_life = 20
        portfolio_npv = -total_capex_top5
        for yr in range(1, avg_life + 1):
            portfolio_npv += total_annual_value_top5 / ((1.0 + discount_rate) ** yr)

        portfolio_irr = total_annual_value_top5 / max(total_capex_top5, 1.0)

        return RetrofitResult(
            entity_id=entity_id,
            measures=measure_results,
            total_capex=round(total_capex, 0),
            total_energy_saving_kwh_pa=round(total_energy_saving, 0),
            total_co2_saving_kgpa=round(total_co2_saving, 0),
            crrem_year_improvement=max(0, crrem_year_improvement),
            portfolio_irr=round(portfolio_irr * 100.0, 2),
            portfolio_npv=round(portfolio_npv, 0),
        )

    # ------------------------------------------------------------------
    # 8. Full Assessment
    # ------------------------------------------------------------------
    def generate_full_assessment(
        self,
        entity_id: str,
        asset_data: dict,
    ) -> dict:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        asset_type = asset_data.get("asset_type", "office")
        country = asset_data.get("country", "UK")
        co2_intensity = asset_data.get("co2_intensity_kgco2_m2", 35.0)
        energy_intensity = asset_data.get("energy_intensity_kwh_m2", 180.0)
        floor_area = asset_data.get("floor_area_m2", 5000.0)
        primary_energy = asset_data.get("primary_energy_kwh_m2", 200.0)
        building_type = asset_data.get("building_type", "commercial")
        lease_clauses = asset_data.get("lease_clauses_present", [])
        annual_energy = energy_intensity * floor_area
        mgmt_data = asset_data.get("gresb_management", {})
        perf_data = asset_data.get("gresb_performance", {})

        crrem = self.assess_crrem(entity_id, asset_type, country, energy_intensity, co2_intensity)
        epc = self.assess_epc_epbd(entity_id, country, building_type, primary_energy)
        gresb = self.calculate_gresb_score(entity_id, mgmt_data, perf_data)
        refi = self.assess_refi(entity_id, asset_data.get("physical_risk", {}), asset_data.get("transition_risk", {}))
        nabers = self.calculate_nabers(entity_id, asset_type, annual_energy, floor_area)
        green_lease = self.assess_green_lease(entity_id, lease_clauses)
        retrofit = self.model_retrofit(entity_id, asset_type, energy_intensity, floor_area)

        # Green/brown premium
        gp_data = GREEN_PREMIUM_EVIDENCE.get(country, GREEN_PREMIUM_EVIDENCE.get("UK", {})).get(
            asset_type, {"premium_pct": 5.0, "brown_discount_pct": 4.0}
        )

        # Overall climate risk score
        climate_risk_score = round(
            (crrem.overconsumption_gap / max(co2_intensity, 1.0)) * 40.0
            + refi.composite_score * 0.30
            + (100.0 - gresb.total_score) * 0.30,
            2,
        )

        return {
            "assessment_id": str(uuid.uuid4()),
            "entity_id": entity_id,
            "asset_type": asset_type,
            "country": country,
            "crrem": {
                "stranding_year": crrem.stranding_year,
                "stranding_risk": crrem.stranding_risk,
                "overconsumption_gap": crrem.overconsumption_gap,
                "pathway_2030": crrem.pathway_2030,
            },
            "epc": {
                "rating": epc.epc_rating,
                "renovation_required": epc.epbd_renovation_required,
                "compliance_deadline": epc.compliance_deadline,
            },
            "gresb": {
                "total_score": gresb.total_score,
                "star_rating": gresb.star_rating,
                "peer_percentile": gresb.peer_percentile,
            },
            "refi": {
                "composite_score": refi.composite_score,
                "risk_tier": refi.risk_tier,
                "risk_label": refi.risk_label,
            },
            "nabers": {
                "energy_stars": nabers.energy_stars,
                "energy_intensity_kwh_m2": nabers.energy_intensity_kwh_m2,
            },
            "green_lease": {
                "score": green_lease.score,
                "grade": green_lease.grade,
                "clauses_missing_count": len(green_lease.clauses_missing),
            },
            "retrofit": {
                "total_capex": retrofit.total_capex,
                "portfolio_npv": retrofit.portfolio_npv,
                "portfolio_irr_pct": retrofit.portfolio_irr,
                "crrem_year_improvement": retrofit.crrem_year_improvement,
                "top_measure": retrofit.measures[0]["measure"] if retrofit.measures else None,
            },
            "green_premium_pct": gp_data["premium_pct"],
            "brown_discount_pct": gp_data["brown_discount_pct"],
            "climate_risk_score": climate_risk_score,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
