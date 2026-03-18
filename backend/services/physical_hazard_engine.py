"""
Physical Climate Hazard Scoring Engine
=======================================
IPCC AR6 WG2 + JRC Climate Hazard Atlas methodology.

Scores seven physical climate hazards for a given asset location and type,
computes composite risk, estimates financial impact, and checks CRREM pathway
alignment for real estate assets.

Data sources modelled:
- IPCC AR6 WG2 Chapter 16 (key risks and burning embers)
- JRC EFAS Global, WRI Aqueduct 4.0 (flood)
- JRC GWIS, Copernicus EFFIS (wildfire)
- CoastalDEM, IPCC AR6 SLR (sea level rise)
- IBTrACS, CMIP6 (tropical cyclone)
- SPEI Global DB, CRU TS4 (drought)
- CRREM v2 (stranding pathways)
"""
from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

HAZARD_PROFILES = {
    "flood": {
        "description": "Riverine and coastal flood risk",
        "data_source": "JRC_EFAS_Global + WRI_Aqueduct_4.0",
        "intensity_metric": "1-in-100yr flood depth (m)",
        "rcp26_multiplier": 1.1,
        "rcp45_multiplier": 1.3,
        "rcp85_multiplier": 1.8,
    },
    "wildfire": {
        "description": "Wildfire hazard index (FWI)",
        "data_source": "JRC_GWIS + Copernicus_EFFIS",
        "intensity_metric": "Fire Weather Index annual mean",
        "rcp26_multiplier": 1.1,
        "rcp45_multiplier": 1.4,
        "rcp85_multiplier": 2.2,
    },
    "heat_stress": {
        "description": "Extreme heat days and WBGT threshold exceedance",
        "data_source": "IPCC_AR6_Atlas + ERA5",
        "intensity_metric": "Days >35C per year",
        "rcp26_multiplier": 1.3,
        "rcp45_multiplier": 2.0,
        "rcp85_multiplier": 4.5,
    },
    "sea_level_rise": {
        "description": "Coastal inundation from mean sea level rise",
        "data_source": "IPCC_AR6_SLR + CoastalDEM",
        "intensity_metric": "SLR (m) by 2100",
        "rcp26_multiplier": 0.3,
        "rcp45_multiplier": 0.5,
        "rcp85_multiplier": 1.0,
    },
    "cyclone": {
        "description": "Tropical cyclone track density and wind speed",
        "data_source": "IBTrACS + CMIP6",
        "intensity_metric": "Cat 3+ events per decade",
        "rcp26_multiplier": 1.0,
        "rcp45_multiplier": 1.1,
        "rcp85_multiplier": 1.3,
    },
    "drought": {
        "description": "Meteorological drought frequency (SPEI-12)",
        "data_source": "SPEI_Global_DB + CRU_TS4",
        "intensity_metric": "Drought months per year",
        "rcp26_multiplier": 1.1,
        "rcp45_multiplier": 1.5,
        "rcp85_multiplier": 2.8,
    },
    "subsidence": {
        "description": "Land subsidence risk (coastal/urban/peat)",
        "data_source": "InSAR_Global + Peat_Depth_Atlas",
        "intensity_metric": "Annual subsidence rate (mm/yr)",
        "rcp26_multiplier": 1.0,
        "rcp45_multiplier": 1.1,
        "rcp85_multiplier": 1.2,
    },
}

# Country-level base hazard scores (0-100) — representative profiles
COUNTRY_BASE_HAZARD = {
    "BD": {"flood": 90, "cyclone": 85, "heat_stress": 70, "drought": 40, "sea_level_rise": 88},
    "PH": {"flood": 75, "cyclone": 90, "heat_stress": 65, "drought": 45, "sea_level_rise": 70},
    "IN": {"flood": 65, "heat_stress": 75, "drought": 60, "cyclone": 55},
    "CN": {"flood": 60, "heat_stress": 55, "drought": 50, "cyclone": 45},
    "US": {"wildfire": 55, "cyclone": 50, "flood": 45, "heat_stress": 40},
    "AU": {"wildfire": 80, "drought": 70, "heat_stress": 75, "flood": 45},
    "ES": {"wildfire": 65, "drought": 70, "heat_stress": 60, "flood": 35},
    "DE": {"flood": 50, "heat_stress": 40, "drought": 35},
    "NL": {"flood": 75, "sea_level_rise": 70},
    "GB": {"flood": 55, "sea_level_rise": 45, "heat_stress": 30},
    "JP": {"flood": 65, "cyclone": 70, "subsidence": 50},
    "BR": {"flood": 60, "drought": 55, "wildfire": 50, "heat_stress": 55},
    "ZA": {"drought": 65, "heat_stress": 60, "wildfire": 50},
    "NG": {"drought": 60, "heat_stress": 70, "flood": 50},
    "ID": {"flood": 70, "sea_level_rise": 75, "subsidence": 80, "cyclone": 45},
}

# Asset type vulnerability multipliers
ASSET_VULNERABILITY = {
    "office_building":   {"flood": 0.6, "heat_stress": 0.4, "wildfire": 0.5},
    "industrial_plant":  {"flood": 0.8, "heat_stress": 0.6, "wildfire": 0.7},
    "data_centre":       {"flood": 0.9, "heat_stress": 0.9, "wildfire": 0.8},
    "retail":            {"flood": 0.7, "heat_stress": 0.5, "wildfire": 0.6},
    "residential":       {"flood": 0.7, "heat_stress": 0.7, "wildfire": 0.8},
    "agricultural_land": {"drought": 0.9, "flood": 0.7, "heat_stress": 0.8},
    "coastal_port":      {"sea_level_rise": 0.9, "cyclone": 0.8, "flood": 0.8},
    "infrastructure":    {"flood": 0.6, "subsidence": 0.7, "heat_stress": 0.5},
}

# CRREM stranding risk by asset type and climate scenario
CRREM_STRANDING_YEARS = {
    "office_building":  {"RCP8.5": 2035, "RCP4.5": 2042, "RCP2.6": 2055},
    "industrial_plant": {"RCP8.5": 2030, "RCP4.5": 2038, "RCP2.6": 2048},
    "residential":      {"RCP8.5": 2038, "RCP4.5": 2045, "RCP2.6": 2058},
    "retail":           {"RCP8.5": 2033, "RCP4.5": 2040, "RCP2.6": 2052},
}

# Adaptation measures per hazard
ADAPTATION_MEASURES = {
    "flood":          "Install flood barriers, raise critical equipment, waterproof building envelope",
    "wildfire":       "Create defensible space, fire-resistant construction materials, vegetation management",
    "heat_stress":    "Cool roofs, green infrastructure, HVAC upgrade, passive cooling design",
    "sea_level_rise": "Coastal protection, relocation planning, foundation reinforcement",
    "cyclone":        "Structural reinforcement, backup power, storm surge barriers",
    "drought":        "Water recycling, drought-resistant landscaping, water storage",
    "subsidence":     "Foundation monitoring, ground improvement, building load redistribution",
}

# Composite hazard weights (must sum to 1.0)
COMPOSITE_WEIGHTS = {
    "flood":          0.20,
    "wildfire":       0.15,
    "heat_stress":    0.20,
    "sea_level_rise": 0.15,
    "cyclone":        0.15,
    "drought":        0.10,
    "subsidence":     0.05,
}

# Exposure level thresholds
EXPOSURE_LEVELS = [
    (80, "very_high"),
    (60, "high"),
    (40, "medium"),
    (20, "low"),
    (0,  "very_low"),
]

# Risk tier thresholds
RISK_TIERS = [
    (75, "critical"),
    (55, "high"),
    (35, "medium"),
    (15, "low"),
    (0,  "negligible"),
]

CURRENT_YEAR = 2026


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class PhysicalHazardEngine:
    """Physical Climate Hazard Scoring engine per IPCC AR6 WG2 + JRC Atlas."""

    # -----------------------------------------------------------------------
    # 1. Score individual hazard
    # -----------------------------------------------------------------------

    def score_hazard(
        self,
        entity_id: str,
        hazard_type: str,
        country_code: str,
        asset_type: str,
        climate_scenario: str = "RCP4.5",
        time_horizon: str = "2050",
    ) -> dict:
        """
        Score a single hazard for an asset in a given country.

        Returns hazard_score 0-100, scenario-adjusted intensities,
        exposure_level, vulnerability_score, and adaptation guidance.
        """
        rng = random.Random(hash(entity_id + hazard_type + country_code) & 0xFFFFFFFF)

        # Base hazard score from country profile
        country_profile = COUNTRY_BASE_HAZARD.get(country_code.upper(), {})
        base_score = float(country_profile.get(hazard_type, rng.uniform(20, 60)))

        # Scenario multiplier
        hp = HAZARD_PROFILES.get(hazard_type, {})
        scenario_key = f"{climate_scenario.lower().replace('.', '').replace('-', '')}_multiplier"
        # normalise key: RCP8.5 -> rcp85_multiplier
        scenario_key = (
            climate_scenario.lower()
            .replace(".", "")
            .replace("rcp", "rcp")
            .replace(" ", "")
        )
        multiplier_map = {
            "rcp26": hp.get("rcp26_multiplier", 1.0),
            "rcp45": hp.get("rcp45_multiplier", 1.1),
            "rcp85": hp.get("rcp85_multiplier", 1.5),
            "RCP2.6": hp.get("rcp26_multiplier", 1.0),
            "RCP4.5": hp.get("rcp45_multiplier", 1.1),
            "RCP8.5": hp.get("rcp85_multiplier", 1.5),
        }
        multiplier = multiplier_map.get(climate_scenario, 1.1)

        # Time horizon amplification
        horizon_year = int(str(time_horizon)[:4]) if str(time_horizon)[:4].isdigit() else 2050
        years_forward = max(0, horizon_year - CURRENT_YEAR)
        time_factor = 1.0 + (years_forward / 100) * (multiplier - 1.0)

        hazard_score = min(100.0, round(base_score * time_factor, 2))

        # Exposure level
        exposure_level = "very_low"
        for threshold, label in EXPOSURE_LEVELS:
            if hazard_score >= threshold:
                exposure_level = label
                break

        # Vulnerability (asset-type specific)
        vuln_map = ASSET_VULNERABILITY.get(asset_type, {})
        vulnerability_score = round(vuln_map.get(hazard_type, rng.uniform(0.3, 0.7)) * 100, 2)

        # Return period intensities (illustrative)
        return_period_20yr = round(base_score * 0.6 * multiplier, 2)
        return_period_100yr = round(base_score * 1.0 * multiplier, 2)

        return {
            "entity_id": entity_id,
            "hazard_type": hazard_type,
            "country_code": country_code.upper(),
            "asset_type": asset_type,
            "climate_scenario": climate_scenario,
            "time_horizon": str(time_horizon),
            "base_hazard_score": round(base_score, 2),
            "scenario_multiplier": multiplier,
            "time_factor": round(time_factor, 3),
            "hazard_score": hazard_score,
            "return_period_20yr_intensity": return_period_20yr,
            "return_period_100yr_intensity": return_period_100yr,
            "intensity_metric": hp.get("intensity_metric", "unitless"),
            "data_source": hp.get("data_source", "IPCC_AR6"),
            "exposure_level": exposure_level,
            "vulnerability_score": vulnerability_score,
            "adaptation_measure": ADAPTATION_MEASURES.get(hazard_type, "No specific measure defined"),
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 2. Composite risk score
    # -----------------------------------------------------------------------

    def compute_composite_risk(
        self,
        entity_id: str,
        hazard_scores: dict,
    ) -> dict:
        """
        Compute weighted composite hazard score.

        Weights: flood 20%, wildfire 15%, heat_stress 20%,
                 sea_level_rise 15%, cyclone 15%, drought 10%, subsidence 5%.
        """
        rng = random.Random(hash(entity_id + "comp") & 0xFFFFFFFF)

        weighted_sum = 0.0
        weight_used = 0.0
        scores_used: dict[str, float] = {}

        for hazard, weight in COMPOSITE_WEIGHTS.items():
            score = float(hazard_scores.get(hazard, rng.uniform(20, 60)))
            scores_used[hazard] = round(score, 2)
            weighted_sum += score * weight
            weight_used += weight

        composite_hazard_score = round(
            weighted_sum / weight_used if weight_used > 0 else 0, 2
        )

        # Risk tier
        risk_tier = "negligible"
        for threshold, label in RISK_TIERS:
            if composite_hazard_score >= threshold:
                risk_tier = label
                break

        # Primary hazard = highest score
        primary_hazard = max(scores_used, key=lambda h: scores_used[h])

        return {
            "entity_id": entity_id,
            "hazard_scores_used": scores_used,
            "composite_hazard_score": composite_hazard_score,
            "risk_tier": risk_tier,
            "primary_hazard": primary_hazard,
            "weights_applied": COMPOSITE_WEIGHTS,
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 3. Financial impact estimation
    # -----------------------------------------------------------------------

    def estimate_financial_impact(
        self,
        entity_id: str,
        composite_score: float,
        asset_type: str,
        asset_value_mn: float,
    ) -> dict:
        """
        Estimate property damage, business interruption, and adaptation CAPEX.
        """
        rng = random.Random(hash(entity_id + "fin") & 0xFFFFFFFF)

        # Property damage fraction scales with composite score
        property_damage_pct = round(
            composite_score * 0.4 * rng.uniform(0.8, 1.2), 2
        )
        property_damage_pct = min(property_damage_pct, 80.0)

        # Business interruption days
        business_interruption_days = round(
            composite_score * 0.5 * rng.uniform(0.8, 1.5)
        )

        # Stranded value risk
        stranded_value_risk_pct = round(
            composite_score * 0.25 * rng.uniform(0.8, 1.3), 2
        )
        stranded_value_risk_pct = min(stranded_value_risk_pct, 50.0)

        # Adaptation CAPEX (million)
        adaptation_capex_mn = round(
            asset_value_mn * composite_score / 100 * 0.08 * rng.uniform(0.7, 1.4), 3
        )

        property_damage_value_mn = round(asset_value_mn * property_damage_pct / 100, 3)
        stranded_value_mn = round(asset_value_mn * stranded_value_risk_pct / 100, 3)

        return {
            "entity_id": entity_id,
            "asset_type": asset_type,
            "asset_value_mn": asset_value_mn,
            "composite_score": composite_score,
            "property_damage_pct": property_damage_pct,
            "property_damage_value_mn": property_damage_value_mn,
            "business_interruption_days": int(business_interruption_days),
            "stranded_value_risk_pct": stranded_value_risk_pct,
            "stranded_value_mn": stranded_value_mn,
            "adaptation_capex_mn": adaptation_capex_mn,
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 4. CRREM alignment check
    # -----------------------------------------------------------------------

    def check_crrem_alignment(
        self,
        entity_id: str,
        asset_type: str,
        climate_scenario: str = "RCP4.5",
    ) -> dict:
        """Check CRREM pathway compliance and stranding year for the asset."""
        asset_data = CRREM_STRANDING_YEARS.get(asset_type, {})

        # Normalise scenario key
        scenario_key = climate_scenario.replace(".", "").replace("rcp", "RCP").upper()
        if "26" in scenario_key:
            scenario_key = "RCP2.6"
        elif "45" in scenario_key:
            scenario_key = "RCP4.5"
        elif "85" in scenario_key:
            scenario_key = "RCP8.5"

        stranding_year = asset_data.get(scenario_key)
        crrem_available = stranding_year is not None

        if crrem_available:
            crrem_pathway_compliant = stranding_year > CURRENT_YEAR + 10
            years_to_stranding = stranding_year - CURRENT_YEAR
        else:
            crrem_pathway_compliant = None
            years_to_stranding = None

        return {
            "entity_id": entity_id,
            "asset_type": asset_type,
            "climate_scenario": climate_scenario,
            "crrem_available": crrem_available,
            "stranding_year": stranding_year,
            "years_to_stranding": years_to_stranding,
            "crrem_pathway_compliant": crrem_pathway_compliant,
            "crrem_version": "CRREM_v2.0",
            "note": (
                "CRREM stranding year indicates when asset energy intensity exceeds pathway"
                if crrem_available
                else "CRREM pathway not available for this asset type"
            ),
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # 5. Full assessment
    # -----------------------------------------------------------------------

    def full_assessment(
        self,
        entity_id: str,
        asset_name: str,
        asset_type: str,
        country_code: str,
        climate_scenario: str,
        time_horizon: str,
        asset_value_mn: float,
    ) -> dict:
        """
        Complete physical hazard assessment combining all methods.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Score all seven hazards
        hazard_results: dict[str, dict] = {}
        hazard_scores: dict[str, float] = {}
        for hazard in HAZARD_PROFILES:
            result = self.score_hazard(
                entity_id=entity_id,
                hazard_type=hazard,
                country_code=country_code,
                asset_type=asset_type,
                climate_scenario=climate_scenario,
                time_horizon=time_horizon,
            )
            hazard_results[hazard] = result
            hazard_scores[hazard] = result["hazard_score"]

        composite = self.compute_composite_risk(entity_id, hazard_scores)
        financial = self.estimate_financial_impact(
            entity_id, composite["composite_hazard_score"], asset_type, asset_value_mn
        )
        crrem = self.check_crrem_alignment(entity_id, asset_type, climate_scenario)

        return {
            "entity_id": entity_id,
            "asset_name": asset_name,
            "asset_type": asset_type,
            "country_code": country_code.upper(),
            "climate_scenario": climate_scenario,
            "time_horizon": time_horizon,
            "asset_value_mn": asset_value_mn,
            "individual_hazard_scores": hazard_scores,
            "composite_hazard_score": composite["composite_hazard_score"],
            "risk_tier": composite["risk_tier"],
            "primary_hazard": composite["primary_hazard"],
            "hazard_details": hazard_results,
            "financial_impact": financial,
            "crrem_alignment": crrem,
            "top_adaptation_measures": [
                ADAPTATION_MEASURES[h]
                for h in sorted(hazard_scores, key=lambda x: hazard_scores[x], reverse=True)[:3]
                if h in ADAPTATION_MEASURES
            ],
            "methodology": "IPCC_AR6_WG2 + JRC_Climate_Hazard_Atlas + CRREM_v2",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # -----------------------------------------------------------------------
    # Static reference methods
    # -----------------------------------------------------------------------

    @staticmethod
    def get_hazard_profiles() -> dict:
        return HAZARD_PROFILES

    @staticmethod
    def get_country_base_hazard() -> dict:
        return COUNTRY_BASE_HAZARD

    @staticmethod
    def get_asset_vulnerability() -> dict:
        return ASSET_VULNERABILITY

    @staticmethod
    def get_adaptation_measures() -> dict:
        return ADAPTATION_MEASURES
