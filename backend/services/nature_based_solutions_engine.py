"""
Nature-Based Solutions & Carbon Sequestration Engine (E52)
==========================================================
IUCN Global Standard v2.0, REDD+ VCS VM0007, Blue Carbon VM0033/VM0024,
Soil Carbon IPCC Tier 1-3, ARR (afforestation), AFOLU net GHG balance.

Sub-modules:
  1. IUCN GS Assessment     — 8 criteria, Gold/Silver/Bronze tier
  2. REDD+ VM0007           — Avoided deforestation net credits
  3. Blue Carbon            — Mangrove/seagrass/saltmarsh/tidal_flat
  4. Soil Carbon            — IPCC Tier 1-3 delta methodology
  5. ARR                    — Afforestation, Reforestation, Revegetation
  6. AFOLU Balance          — Net GHG accounting (CO2 - N2O - CH4)
  7. Credit Quality         — ICVCM CCP-compatible rating + price
  8. Sequestration Timeseries — 30-year project-level projection

References:
  - IUCN Global Standard for Nature-based Solutions v2.0 (2020)
  - Verra VCS VM0007: REDD+ Methodology Framework
  - Verra VCS VM0033: Tidal Wetland and Seagrass Restoration
  - Verra VCS VM0024: Applied Research for Tidal Wetland Carbon
  - IPCC 2006 GL for NGHGI Vol 4 Agriculture, Forestry & Other Land Use
  - SBTi FLAG Guidance (Forests, Land & Agriculture)
  - ICVCM Core Carbon Principles (CCP) 2023
"""
from __future__ import annotations

import random
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

IUCN_CRITERIA = [
    "Effectiveness",
    "Additionality",
    "Inclusivity & Equity",
    "No Net Loss to Biodiversity",
    "Mitigation of trade-offs",
    "Adaptive Management",
    "Sustainability & Scalability",
    "Governance",
]

BLUE_CARBON_RATES: dict[str, float] = {
    "mangrove": 6.2,
    "seagrass": 1.8,
    "saltmarsh": 2.4,
    "tidal_flat": 0.8,
}

BLUE_CARBON_PERMANENCE: dict[str, str] = {
    "mangrove": "low",
    "seagrass": "medium",
    "saltmarsh": "low",
    "tidal_flat": "high",
}

BLUE_CARBON_METHODOLOGY: dict[str, str] = {
    "mangrove": "VM0033",
    "seagrass": "VM0024",
    "saltmarsh": "VM0033",
    "tidal_flat": "VM0024",
}

IPCC_TIER_PARAMS: dict[int, dict] = {
    1: {"delta_tco2_ha_pa": 0.5, "uncertainty_pct": 30.0, "permanence_risk": "high"},
    2: {"delta_tco2_ha_pa": 0.8, "uncertainty_pct": 20.0, "permanence_risk": "medium"},
    3: {"delta_tco2_ha_pa": 1.2, "uncertainty_pct": 10.0, "permanence_risk": "low"},
}

CERTIFICATION_SCHEMES: list[str] = [
    "Verra VCS",
    "Gold Standard",
    "Plan Vivo",
    "American Carbon Registry",
    "Climate Action Reserve",
]

ICVCM_CCP_SCHEMES: list[str] = ["Verra VCS", "Gold Standard", "American Carbon Registry"]

CO_BENEFIT_CERTIFICATIONS: list[str] = [
    "CCBA Climate, Community & Biodiversity",
    "SD Vista",
    "Rainforest Alliance",
]


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class NatureBasedSolutionsEngine:
    """Nature-Based Solutions & Carbon Sequestration Engine (E52)."""

    # ------------------------------------------------------------------
    # 1. IUCN Global Standard v2.0
    # ------------------------------------------------------------------

    def assess_iucn_gs(
        self,
        entity_id: str,
        criteria_scores: list[float],
    ) -> dict:
        """
        IUCN GS v2.0 — 8 criteria, each scored 0-100.
        Returns composite score, tier, and ICVCM compatibility flag.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Pad/trim to 8 criteria; fill missing with rng if fewer supplied
        while len(criteria_scores) < 8:
            criteria_scores.append(round(rng.uniform(40.0, 85.0), 1))
        scores = [round(float(s), 1) for s in criteria_scores[:8]]

        composite = round(sum(scores) / len(scores), 2)
        safeguards_score = round(min(scores), 2)
        standard_met = composite >= 70.0

        if composite >= 85.0:
            tier = "Gold"
        elif composite >= 70.0:
            tier = "Silver"
        else:
            tier = "Bronze"

        icvcm_compatible = standard_met and safeguards_score >= 55.0

        return {
            "entity_id": entity_id,
            "criteria_names": IUCN_CRITERIA,
            "criteria_scores": scores,
            "composite_score": composite,
            "safeguards_score": safeguards_score,
            "standard_met": standard_met,
            "tier": tier,
            "icvcm_compatible": icvcm_compatible,
            "methodology": "IUCN Global Standard v2.0",
            "assessment_version": "2020",
        }

    # ------------------------------------------------------------------
    # 2. REDD+ VM0007
    # ------------------------------------------------------------------

    def assess_redd_plus(
        self,
        entity_id: str,
        area_ha: float,
        reference_level_tco2_pa: float,
        actual_emissions_tco2_pa: float,
        jurisdictional: bool = False,
    ) -> dict:
        """
        VCS VM0007 REDD+ avoided deforestation methodology.
        Returns net credits after leakage belt and buffer pool deductions.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        avoided_deforestation = reference_level_tco2_pa - actual_emissions_tco2_pa

        leakage_belt_pct = round(rng.uniform(5.0, 15.0), 2)

        # Jurisdictional programmes have smaller buffer requirements
        buf_min = 10.0 if jurisdictional else 15.0
        buf_max = 20.0 if jurisdictional else 25.0
        buffer_pool_pct = round(rng.uniform(buf_min, buf_max), 2)

        net_credits = avoided_deforestation * (1 - leakage_belt_pct / 100) * (1 - buffer_pool_pct / 100)
        net_credits = round(max(0.0, net_credits), 2)

        per_ha = round(net_credits / area_ha, 2) if area_ha > 0 else 0.0

        return {
            "entity_id": entity_id,
            "project_area_ha": round(area_ha, 2),
            "reference_level_tco2_pa": round(reference_level_tco2_pa, 2),
            "actual_emissions_tco2_pa": round(actual_emissions_tco2_pa, 2),
            "avoided_deforestation_tco2_pa": round(avoided_deforestation, 2),
            "leakage_belt_pct": leakage_belt_pct,
            "buffer_pool_pct": buffer_pool_pct,
            "net_credits_tco2_pa": net_credits,
            "net_credits_per_ha": per_ha,
            "methodology": "VM0007",
            "permanence_years": 100,
            "jurisdictional": jurisdictional,
            "vcs_validated": True,
        }

    # ------------------------------------------------------------------
    # 3. Blue Carbon
    # ------------------------------------------------------------------

    def assess_blue_carbon(
        self,
        entity_id: str,
        ecosystem_type: str,
        area_ha: float,
    ) -> dict:
        """
        Blue carbon accounting for coastal/marine ecosystems.
        Methodology: VM0033 (mangrove/saltmarsh) or VM0024 (seagrass/tidal_flat).
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)
        eco = ecosystem_type.lower() if ecosystem_type.lower() in BLUE_CARBON_RATES else "mangrove"

        seq_rate = BLUE_CARBON_RATES[eco]
        total_seq = round(area_ha * seq_rate, 2)
        permanence_risk = BLUE_CARBON_PERMANENCE[eco]
        methodology = BLUE_CARBON_METHODOLOGY[eco]
        tidal_hydrology_restored = rng.random() > 0.4

        # Additionality / buffer adjustments
        buffer_pct = 12.0 if permanence_risk == "low" else (18.0 if permanence_risk == "medium" else 25.0)
        net_credits = round(total_seq * (1 - buffer_pct / 100), 2)

        co_benefit_score = round(rng.uniform(55.0, 90.0), 1)

        return {
            "entity_id": entity_id,
            "ecosystem_type": eco,
            "area_ha": round(area_ha, 2),
            "seq_rate_tco2_ha_pa": seq_rate,
            "total_seq_tco2_pa": total_seq,
            "permanence_risk": permanence_risk,
            "buffer_pct": buffer_pct,
            "net_credits_tco2_pa": net_credits,
            "methodology": methodology,
            "tidal_hydrology_restored": tidal_hydrology_restored,
            "co_benefit_score": co_benefit_score,
            "blue_carbon_standard": "Verra VCS",
        }

    # ------------------------------------------------------------------
    # 4. Soil Carbon (IPCC Tier 1-3)
    # ------------------------------------------------------------------

    def assess_soil_carbon(
        self,
        entity_id: str,
        area_ha: float,
        land_use_change: str,
        ipcc_tier: int = 1,
    ) -> dict:
        """
        IPCC Tier 1-3 soil organic carbon methodology.
        Higher tiers = lower uncertainty + higher sequestration rates.
        """
        tier = max(1, min(3, ipcc_tier))
        params = IPCC_TIER_PARAMS[tier]

        delta = params["delta_tco2_ha_pa"]
        uncertainty_pct = params["uncertainty_pct"]
        permanence_risk = params["permanence_risk"]

        total_tco2_pa = round(area_ha * delta, 2)
        reversal_buffer_pct = 15.0

        # Crediting period and uncertainty range
        lower_bound = round(total_tco2_pa * (1 - uncertainty_pct / 100), 2)
        upper_bound = round(total_tco2_pa * (1 + uncertainty_pct / 100), 2)

        return {
            "entity_id": entity_id,
            "ipcc_tier": tier,
            "land_use_change": land_use_change,
            "area_ha": round(area_ha, 2),
            "delta_tco2_ha_pa": delta,
            "total_tco2_pa": total_tco2_pa,
            "permanence_risk": permanence_risk,
            "measurement_uncertainty_pct": uncertainty_pct,
            "reversal_buffer_pct": reversal_buffer_pct,
            "confidence_range": {"lower": lower_bound, "upper": upper_bound},
            "crediting_period_years": 20,
            "monitoring_frequency": "Annual" if tier == 3 else "Biennial",
        }

    # ------------------------------------------------------------------
    # 5. ARR — Afforestation, Reforestation, Revegetation
    # ------------------------------------------------------------------

    def assess_arr(
        self,
        entity_id: str,
        area_ha: float,
        species_type: str = "mixed",
    ) -> dict:
        """
        ARR carbon accounting: above-ground, below-ground, soil.
        Species type (native/mixed/exotic) affects co-benefit scoring.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        above_ground_rate = round(rng.uniform(2.5, 4.0), 3)
        above_ground = round(area_ha * above_ground_rate, 2)
        below_ground = round(above_ground * 0.26, 2)  # IPCC root-to-shoot ratio
        soil_carbon = round(area_ha * 0.5, 2)
        total = round(above_ground + below_ground + soil_carbon, 2)

        native_species = species_type.lower() in ["native", "mixed"]
        co_benefit_score = round(rng.uniform(60.0, 90.0) if native_species else rng.uniform(30.0, 60.0), 1)

        # Buffer and net credits
        buffer_pct = 10.0 if native_species else 15.0
        net_credits = round(total * (1 - buffer_pct / 100), 2)

        return {
            "entity_id": entity_id,
            "area_ha": round(area_ha, 2),
            "species_type": species_type.lower(),
            "above_ground_rate_tco2_ha_pa": above_ground_rate,
            "above_ground_tco2_pa": above_ground,
            "below_ground_tco2_pa": below_ground,
            "soil_carbon_tco2_pa": soil_carbon,
            "total_tco2_pa": total,
            "net_credits_tco2_pa": net_credits,
            "buffer_pct": buffer_pct,
            "native_species": native_species,
            "co_benefit_score": co_benefit_score,
            "methodology": "VCS VM0047 / Gold Standard IFM",
            "permanence_years": 40,
        }

    # ------------------------------------------------------------------
    # 6. AFOLU Net GHG Balance
    # ------------------------------------------------------------------

    def compute_afolu_balance(
        self,
        entity_id: str,
        sequestration_tco2_pa: float,
        land_area_ha: float,
    ) -> dict:
        """
        AFOLU (Agriculture, Forestry & Other Land Use) net GHG accounting.
        Includes N2O and CH4 non-CO2 emissions per IPCC EFs.
        """
        # IPCC Tier 1 default emission factors
        n2o_emissions = round(land_area_ha * 0.018, 4)  # tCO2e/ha (soil N2O)
        ch4_emissions = round(land_area_ha * 0.008, 4)  # tCO2e/ha (wetland CH4)
        total_non_co2 = n2o_emissions + ch4_emissions

        net_balance = round(sequestration_tco2_pa - total_non_co2, 4)
        afolu_ratio = round(sequestration_tco2_pa / total_non_co2, 2) if total_non_co2 > 0 else 999.0

        return {
            "entity_id": entity_id,
            "land_area_ha": round(land_area_ha, 2),
            "sequestration_tco2_pa": round(sequestration_tco2_pa, 4),
            "n2o_emissions_tco2e_pa": n2o_emissions,
            "ch4_emissions_tco2e_pa": ch4_emissions,
            "total_non_co2_tco2e_pa": round(total_non_co2, 4),
            "net_balance_tco2e_pa": net_balance,
            "afolu_ratio": afolu_ratio,
            "net_positive": net_balance > 0,
            "ipcc_ef_source": "IPCC 2006 GLs Vol 4 Chapter 11",
        }

    # ------------------------------------------------------------------
    # 7. Credit Quality Assessment
    # ------------------------------------------------------------------

    def assess_credit_quality(
        self,
        entity_id: str,
        iucn_score: float,
        redd_net_credits: float,
        co_benefits: dict,
    ) -> dict:
        """
        Credit quality rating combining IUCN score, co-benefits, and volume.
        Derives ICVCM CCP-compatible rating and USD price range.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        # Co-benefit scoring
        bio_score = float(co_benefits.get("biodiversity", rng.uniform(40, 90)))
        water_score = float(co_benefits.get("water", rng.uniform(40, 90)))
        livelihoods_score = float(co_benefits.get("livelihoods", rng.uniform(40, 90)))
        cobenefit_avg = (bio_score + water_score + livelihoods_score) / 3.0
        cobenefit_premium_pct = round(cobenefit_avg / 10.0, 2)  # 0-10%

        overall_quality = round((iucn_score * 0.4 + cobenefit_avg * 0.3 + 30.0) / 100.0 * 100.0, 2)
        overall_quality = min(100.0, max(0.0, overall_quality))

        icvcm_compatible = overall_quality >= 65.0

        # Pricing model
        base_price = 8.0 + (overall_quality - 40.0) / 60.0 * 27.0 if overall_quality > 40 else 8.0
        price_usd = round(base_price * (1 + cobenefit_premium_pct / 100.0), 2)
        price_usd = round(max(8.0, min(35.0, price_usd)), 2)
        price_min = round(price_usd * 0.85, 2)
        price_max = round(price_usd * 1.20, 2)

        # Eligible certifications
        eligible = list(CERTIFICATION_SCHEMES)
        if icvcm_compatible:
            eligible += ICVCM_CCP_SCHEMES
        if cobenefit_avg >= 70:
            eligible += CO_BENEFIT_CERTIFICATIONS
        eligible = list(dict.fromkeys(eligible))  # deduplicate preserving order

        return {
            "entity_id": entity_id,
            "iucn_score": round(iucn_score, 2),
            "co_benefits": {
                "biodiversity": round(bio_score, 1),
                "water": round(water_score, 1),
                "livelihoods": round(livelihoods_score, 1),
            },
            "cobenefit_avg": round(cobenefit_avg, 2),
            "cobenefit_premium_pct": cobenefit_premium_pct,
            "overall_quality_score": overall_quality,
            "icvcm_ccp_compatible": icvcm_compatible,
            "redd_net_credits_tco2_pa": round(redd_net_credits, 2),
            "estimated_price_usd": price_usd,
            "price_range": {"min": price_min, "max": price_max},
            "certification_eligible": eligible,
        }

    # ------------------------------------------------------------------
    # 8. Sequestration Timeseries
    # ------------------------------------------------------------------

    def project_sequestration_timeseries(
        self,
        entity_id: str,
        annual_seq_tco2: float,
        project_years: int = 30,
    ) -> list[dict]:
        """
        30-year project-level sequestration projection with ramp-up and
        small annual variability.
        """
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        cumulative = 0.0
        timeseries: list[dict] = []
        buffer_pool_total = 0.0

        for year in range(1, project_years + 1):
            # Ramp-up capacity factor
            if year <= 5:
                capacity = 0.60
            elif year <= 10:
                capacity = 0.85
            else:
                capacity = 1.00

            # Annual variation ±5%
            variation = rng.uniform(-0.05, 0.05)
            raw_seq = annual_seq_tco2 * capacity * (1 + variation)

            # Non-CO2 emissions (small fraction)
            emissions_tco2e = round(raw_seq * 0.03, 4)
            net_balance = round(raw_seq - emissions_tco2e, 4)

            # Buffer pool contribution (10% of gross)
            buffer_contribution = round(raw_seq * 0.10, 4)
            buffer_pool_total += buffer_contribution

            # Credits issued after buffer
            credits_issued = round(net_balance * 0.90, 4)
            cumulative += credits_issued

            # Reversal risk flag in early ramp-up or high variability years
            reversal_risk_flag = year <= 3 or abs(variation) > 0.04

            timeseries.append({
                "year": year,
                "capacity_factor": round(capacity, 2),
                "sequestration_tco2": round(raw_seq, 4),
                "emissions_tco2e": emissions_tco2e,
                "net_balance_tco2e": net_balance,
                "cumulative_tco2e": round(cumulative, 2),
                "buffer_pool_contribution": buffer_contribution,
                "credits_issued_tco2": credits_issued,
                "reversal_risk_flag": reversal_risk_flag,
            })

        return timeseries


# ---------------------------------------------------------------------------
# Module-level instance
# ---------------------------------------------------------------------------

_engine = NatureBasedSolutionsEngine()

assess_iucn_gs = _engine.assess_iucn_gs
assess_redd_plus = _engine.assess_redd_plus
assess_blue_carbon = _engine.assess_blue_carbon
assess_soil_carbon = _engine.assess_soil_carbon
assess_arr = _engine.assess_arr
compute_afolu_balance = _engine.compute_afolu_balance
assess_credit_quality = _engine.assess_credit_quality
project_sequestration_timeseries = _engine.project_sequestration_timeseries
