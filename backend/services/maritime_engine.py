"""
Maritime Climate Risk & Regulatory Compliance Engine

Standards implemented:
- IMO GHG Strategy 2023 (revised 50% reduction by 2050 → net-zero by 2050)
- CII (Carbon Intensity Indicator) — MARPOL Annex VI Regulation 28
- EEXI (Energy Efficiency Existing Ship Index) — MARPOL Annex VI Regulation 25
- EU ETS Shipping — Regulation (EU) 2023/957 (amending EU ETS Directive 2003/87/EC)
- FuelEU Maritime — Regulation (EU) 2023/1805
- Alternative fuels: LNG, methanol, ammonia, hydrogen
- Ship asset stranding risk modelling
"""

import random
import math
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

SHIP_TYPES: Dict[str, Dict[str, float]] = {
    "bulk_carrier":   {"baseline_cii_ref": 4.745,  "eexi_ref_kW_per_GT": 0.0, "fuel_consumption_factor": 0.042},
    "tanker":         {"baseline_cii_ref": 5.247,  "eexi_ref_kW_per_GT": 0.0, "fuel_consumption_factor": 0.048},
    "container":      {"baseline_cii_ref": 1.984,  "eexi_ref_kW_per_GT": 0.0, "fuel_consumption_factor": 0.055},
    "gas_carrier":    {"baseline_cii_ref": 6.131,  "eexi_ref_kW_per_GT": 0.0, "fuel_consumption_factor": 0.038},
    "ro_ro":          {"baseline_cii_ref": 2.673,  "eexi_ref_kW_per_GT": 0.0, "fuel_consumption_factor": 0.051},
    "cruise":         {"baseline_cii_ref": 2.333,  "eexi_ref_kW_per_GT": 0.0, "fuel_consumption_factor": 0.062},
    "ferry":          {"baseline_cii_ref": 3.456,  "eexi_ref_kW_per_GT": 0.0, "fuel_consumption_factor": 0.058},
}

# EEXI reference values by ship type (W/tonne-nm or gCO2/tonne-nm proxy)
EEXI_REFERENCE: Dict[str, float] = {
    "bulk_carrier":  3.0,
    "tanker":        3.8,
    "container":     5.5,
    "gas_carrier":   4.2,
    "ro_ro":         6.1,
    "cruise":        9.5,
    "ferry":         7.8,
}

FUEL_EMISSION_FACTORS: Dict[str, Dict[str, float]] = {
    "HFO":      {"cf_t_co2_t_fuel": 3.114, "ghg_intensity_gco2e_mj": 91.16, "imo_wtt_factor": 1.04},
    "LSFO":     {"cf_t_co2_t_fuel": 3.151, "ghg_intensity_gco2e_mj": 89.50, "imo_wtt_factor": 1.04},
    "MDO":      {"cf_t_co2_t_fuel": 3.206, "ghg_intensity_gco2e_mj": 88.00, "imo_wtt_factor": 1.05},
    "LNG":      {"cf_t_co2_t_fuel": 2.750, "ghg_intensity_gco2e_mj": 75.20, "imo_wtt_factor": 1.22},
    "methanol": {"cf_t_co2_t_fuel": 1.375, "ghg_intensity_gco2e_mj": 42.30, "imo_wtt_factor": 1.10},
    "ammonia":  {"cf_t_co2_t_fuel": 0.0,   "ghg_intensity_gco2e_mj": 0.50,  "imo_wtt_factor": 1.15},
    "hydrogen": {"cf_t_co2_t_fuel": 0.0,   "ghg_intensity_gco2e_mj": 0.30,  "imo_wtt_factor": 1.25},
}

# CII annual reduction factors from 2019 baseline (MARPOL Annex VI Reg 28.6)
CII_REDUCTION_TARGETS: Dict[int, float] = {
    2023: 0.95,
    2024: 0.93,
    2025: 0.91,
    2026: 0.89,
    2027: 0.87,
    2028: 0.85,
    2029: 0.83,
    2030: 0.80,
}

# CII rating thresholds (ratio of attained/required)
CII_RATING_THRESHOLDS: Dict[str, float] = {
    "A": 0.85,
    "B": 0.95,
    "C": 1.05,
    "D": 1.15,
    "E": 999.0,
}

# EU ETS phase-in coverage (fraction of verified CO2 surrendered)
EU_ETS_PHASE_COVERAGE: Dict[int, float] = {
    2024: 0.40,
    2025: 0.70,
    2026: 1.00,
}

# FuelEU Maritime GHG intensity targets (gCO2e/MJ, WtW)
FUELEU_GHG_TARGETS_GCO2E_MJ: Dict[int, float] = {
    2025: 89.34,
    2030: 80.43,
    2035: 69.76,
    2040: 53.94,
    2045: 31.12,
    2050: 1.89,
}

ALTERNATIVE_FUEL_CAPEX_USD_PER_KW: Dict[str, float] = {
    "LNG":      350.0,
    "methanol": 420.0,
    "ammonia":  680.0,
    "hydrogen": 850.0,
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _clamp(lo: float, hi: float, val: float) -> float:
    return max(lo, min(hi, val))


def _cii_rating(ratio: float) -> str:
    if ratio <= CII_RATING_THRESHOLDS["A"]:
        return "A"
    elif ratio <= CII_RATING_THRESHOLDS["B"]:
        return "B"
    elif ratio <= CII_RATING_THRESHOLDS["C"]:
        return "C"
    elif ratio <= CII_RATING_THRESHOLDS["D"]:
        return "D"
    return "E"


def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(entity_id) & 0xFFFFFFFF)


def _eu_ets_cost(co2: float, coverage: float, route_share: float, price: float) -> float:
    return round(co2 * coverage * (route_share / 100.0) * price, 2)


def _get_fueleu_target(year: int) -> float:
    milestones = sorted(FUELEU_GHG_TARGETS_GCO2E_MJ.keys())
    for m in milestones:
        if year <= m:
            return FUELEU_GHG_TARGETS_GCO2E_MJ[m]
    return FUELEU_GHG_TARGETS_GCO2E_MJ[2050]


# ---------------------------------------------------------------------------
# Maritime Engine
# ---------------------------------------------------------------------------

class MaritimeEngine:
    """IMO/EU maritime decarbonisation compliance engine."""

    # ------------------------------------------------------------------
    # 1. CII Assessment
    # ------------------------------------------------------------------
    def assess_cii(
        self,
        entity_id: str,
        ship_type: str,
        deadweight_tonnes: float,
        annual_fuel_consumption_t: float,
        annual_distance_nm: float,
        annual_cargo_tonnes: float,
        fuel_type: str,
        year: int,
    ) -> dict:
        rng = _rng(entity_id)
        ship = SHIP_TYPES.get(ship_type, SHIP_TYPES["bulk_carrier"])
        fuel = FUEL_EMISSION_FACTORS.get(fuel_type, FUEL_EMISSION_FACTORS["HFO"])

        cf = fuel["cf_t_co2_t_fuel"]
        annual_co2_t = annual_fuel_consumption_t * cf

        # Capacity measure for CII: DWT for most ship types
        capacity = max(deadweight_tonnes, 1.0)
        distance = max(annual_distance_nm, 1.0)

        # Attained CII (gCO2 / capacity-nm)
        cii_attained = round((annual_co2_t * 1e6) / (capacity * distance), 4)

        # Required CII from reference line × year reduction factor
        reduction_factor = CII_REDUCTION_TARGETS.get(year, CII_REDUCTION_TARGETS[2030])
        cii_ref = ship["baseline_cii_ref"]
        cii_required = round(cii_ref * reduction_factor, 4)

        cii_ratio = round(cii_attained / max(cii_required, 0.001), 4)
        cii_rating = _cii_rating(cii_ratio)

        improvement_needed_pct = round(max(0.0, (cii_ratio - 1.0) * 100.0), 2)

        # Corrective action deadline: D/E rating → 1 year; C → 3 years
        if cii_rating in ("D", "E"):
            deadline_year = year + 1
        elif cii_rating == "C":
            deadline_year = year + 3
        else:
            deadline_year = None

        return {
            "entity_id": entity_id,
            "ship_type": ship_type,
            "fuel_type": fuel_type,
            "year": year,
            "cii_attained": cii_attained,
            "cii_required": cii_required,
            "cii_ratio": cii_ratio,
            "cii_rating": cii_rating,
            "annual_co2_tonnes": round(annual_co2_t, 2),
            "improvement_needed_pct": improvement_needed_pct,
            "corrective_action_deadline": deadline_year,
            "regulatory_basis": "MARPOL Annex VI Regulation 28",
        }

    # ------------------------------------------------------------------
    # 2. EEXI Assessment
    # ------------------------------------------------------------------
    def assess_eexi(
        self,
        entity_id: str,
        ship_type: str,
        gross_tonnage: float,
        installed_power_kw: float,
        design_fuel_consumption_g_kwh: float,
        fuel_type: str,
    ) -> dict:
        rng = _rng(entity_id)
        fuel = FUEL_EMISSION_FACTORS.get(fuel_type, FUEL_EMISSION_FACTORS["HFO"])
        cf = fuel["cf_t_co2_t_fuel"]

        # EEXI = (P_ME × SFC_ME × CF) / (DWT × V_ref) — simplified proxy
        # Using gross tonnage as capacity proxy and 13 knots Vref
        v_ref = 13.0  # knots reference speed
        p_ae = installed_power_kw * 0.05  # auxiliary engine ≈ 5% of ME
        sfcme = design_fuel_consumption_g_kwh
        sfcae = sfcme * 1.1

        numerator = ((installed_power_kw * sfcme) + (p_ae * sfcae)) * cf
        denominator = max(gross_tonnage * v_ref, 1.0)
        eexi_attained = round(numerator / denominator, 4)

        eexi_required = round(EEXI_REFERENCE.get(ship_type, 5.0), 4)

        reduction_needed_pct = round(max(0.0, (eexi_attained - eexi_required) / max(eexi_required, 0.001) * 100.0), 2)
        compliant = eexi_attained <= eexi_required

        # EEDI comparable (older metric for reference)
        eedi_comparable = round(eexi_attained * 0.92 + rng.uniform(-0.05, 0.05), 4)

        return {
            "entity_id": entity_id,
            "ship_type": ship_type,
            "fuel_type": fuel_type,
            "gross_tonnage": gross_tonnage,
            "installed_power_kw": installed_power_kw,
            "eexi_attained": eexi_attained,
            "eexi_required": eexi_required,
            "eexi_compliant": compliant,
            "reduction_needed_pct": reduction_needed_pct,
            "eedi_comparable": eedi_comparable,
            "regulatory_basis": "MARPOL Annex VI Regulation 25",
            "compliance_status": "compliant" if compliant else "non_compliant",
        }

    # ------------------------------------------------------------------
    # 3. EU ETS Assessment
    # ------------------------------------------------------------------
    def assess_eu_ets(
        self,
        entity_id: str,
        ship_type: str,
        annual_co2_tonnes: float,
        eu_route_share_pct: float,
        year: int,
    ) -> dict:
        rng = _rng(entity_id)

        coverage = EU_ETS_PHASE_COVERAGE.get(year, 1.0)
        route_share = _clamp(0.0, 100.0, eu_route_share_pct) / 100.0

        allowances_required = round(annual_co2_tonnes * coverage * route_share, 2)

        # EUA price scenarios
        price_base = 65.0 + rng.uniform(-5.0, 5.0)
        price_high = price_base * 1.50
        price_stress = price_base * 2.0

        cost_base = round(allowances_required * price_base, 2)
        cost_high = round(allowances_required * price_high, 2)
        cost_stress = round(allowances_required * price_stress, 2)

        # Phase schedule
        if year < 2024:
            compliance_deadline = "2024-01-01"
        elif year == 2024:
            compliance_deadline = "2025-03-31"
        else:
            compliance_deadline = f"{year + 1}-03-31"

        return {
            "entity_id": entity_id,
            "ship_type": ship_type,
            "year": year,
            "annual_co2_tonnes": round(annual_co2_tonnes, 2),
            "eu_route_share_pct": eu_route_share_pct,
            "phase_coverage_pct": round(coverage * 100.0, 1),
            "allowances_required": allowances_required,
            "eua_price_base_eur": round(price_base, 2),
            "cost_eur_base": cost_base,
            "cost_eur_high": cost_high,
            "cost_eur_stress": cost_stress,
            "compliance_deadline": compliance_deadline,
            "regulatory_basis": "Regulation (EU) 2023/957",
        }

    # ------------------------------------------------------------------
    # 4. FuelEU Maritime Assessment
    # ------------------------------------------------------------------
    def assess_fueleu(
        self,
        entity_id: str,
        ship_type: str,
        fuel_type: str,
        annual_energy_mj: float,
        year: int,
    ) -> dict:
        rng = _rng(entity_id)
        fuel = FUEL_EMISSION_FACTORS.get(fuel_type, FUEL_EMISSION_FACTORS["HFO"])

        # WtW GHG intensity (tank-to-wake + well-to-tank)
        ttw = fuel["ghg_intensity_gco2e_mj"]
        wtt = ttw * (fuel["imo_wtt_factor"] - 1.0)
        ghg_intensity = round(ttw + wtt, 4)

        target = _get_fueleu_target(year)
        intensity_gap = round(ghg_intensity - target, 4)
        compliant = intensity_gap <= 0.0

        # Penalty: €2400 per GJ of surplus GHG intensity (Art 23)
        penalty_eur = 0.0
        if not compliant:
            surplus_gj = (intensity_gap / 1000.0) * (annual_energy_mj / 1e3)
            penalty_eur = round(max(0.0, surplus_gj * 2400.0), 2)

        # Compliance pathway recommendation
        if ghg_intensity > 85:
            pathway = "switch_to_lng_or_low_sulphur_fuel_immediate"
        elif ghg_intensity > 75:
            pathway = "blended_methanol_or_lng_by_2030"
        elif ghg_intensity > 50:
            pathway = "ammonia_hydrogen_pathway_by_2040"
        else:
            pathway = "compliant_monitor_2050_targets"

        return {
            "entity_id": entity_id,
            "ship_type": ship_type,
            "fuel_type": fuel_type,
            "year": year,
            "ghg_intensity_gco2e_mj": ghg_intensity,
            "ttw_intensity": round(ttw, 4),
            "wtt_intensity": round(wtt, 4),
            "target_intensity": round(target, 4),
            "compliant": compliant,
            "intensity_gap": intensity_gap,
            "annual_energy_mj": round(annual_energy_mj, 2),
            "penalty_eur": penalty_eur,
            "compliance_pathway": pathway,
            "regulatory_basis": "Regulation (EU) 2023/1805",
        }

    # ------------------------------------------------------------------
    # 5. Stranding Risk Assessment
    # ------------------------------------------------------------------
    def assess_stranding(
        self,
        entity_id: str,
        ship_type: str,
        build_year: int,
        fuel_type: str,
        gross_tonnage: float,
    ) -> dict:
        rng = _rng(entity_id)
        ship = SHIP_TYPES.get(ship_type, SHIP_TYPES["bulk_carrier"])
        current_year = 2024

        ship_age = current_year - build_year
        typical_lifespan = 25  # years

        # Project CII trajectory: ships on HFO/LSFO will hit D/E rating
        high_carbon_fuels = {"HFO", "LSFO", "MDO"}
        if fuel_type in high_carbon_fuels:
            # CII worsens ~1.5% per year of age, targets tighten 2% per year
            annual_deterioration = 0.015
            annual_tightening = 0.020
            combined_annual_stress = annual_deterioration + annual_tightening
            years_to_d_rating = max(1, int(0.20 / combined_annual_stress))
            stranding_year = min(current_year + years_to_d_rating, build_year + typical_lifespan)
        else:
            # Lower carbon fuels buy more time
            stranding_year = min(build_year + typical_lifespan, 2045)

        years_to_stranding = max(0, stranding_year - current_year)

        # Retrofit cost (engine conversion, scrubbers, etc.)
        retrofit_cost_usd = round(gross_tonnage * 120.0 * (1 + rng.uniform(-0.1, 0.1)), 2)

        # Alternative fuel CAPEX
        if fuel_type in high_carbon_fuels:
            target_alt = "LNG"
        elif fuel_type == "LNG":
            target_alt = "ammonia"
        else:
            target_alt = "hydrogen"

        alt_capex_per_kw = ALTERNATIVE_FUEL_CAPEX_USD_PER_KW.get(target_alt, 400.0)
        estimated_power_kw = gross_tonnage * 0.08  # rough proxy
        alt_fuel_capex_usd = round(estimated_power_kw * alt_capex_per_kw, 2)

        # NPV stranding loss (book value decay)
        replacement_value = gross_tonnage * 800.0
        remaining_life_fraction = max(0.0, years_to_stranding / typical_lifespan)
        npv_stranding_loss_usd = round(replacement_value * (1.0 - remaining_life_fraction) * 0.4, 2)

        if years_to_stranding <= 3:
            risk_rating = "critical"
        elif years_to_stranding <= 7:
            risk_rating = "high"
        elif years_to_stranding <= 12:
            risk_rating = "medium"
        else:
            risk_rating = "low"

        return {
            "entity_id": entity_id,
            "ship_type": ship_type,
            "fuel_type": fuel_type,
            "build_year": build_year,
            "ship_age_years": ship_age,
            "gross_tonnage": gross_tonnage,
            "stranding_year": stranding_year,
            "years_to_stranding": years_to_stranding,
            "retrofit_cost_usd": retrofit_cost_usd,
            "recommended_alt_fuel": target_alt,
            "alt_fuel_capex_usd": alt_fuel_capex_usd,
            "npv_stranding_loss_usd": npv_stranding_loss_usd,
            "risk_rating": risk_rating,
            "regulatory_drivers": ["CII_tightening", "FuelEU_Maritime", "EU_ETS"],
        }

    # ------------------------------------------------------------------
    # 6. Fleet Assessment
    # ------------------------------------------------------------------
    def assess_fleet(self, entity_id: str, ships: List[Dict[str, Any]]) -> dict:
        rng = _rng(entity_id)

        if not ships:
            return {"entity_id": entity_id, "error": "no ships provided"}

        cii_ratings = []
        eu_ets_total = 0.0
        fueleu_compliant_count = 0
        transition_capex_total = 0.0
        risk_scores = []

        for ship in ships:
            ship_entity = ship.get("ship_id", entity_id + "_ship")
            ship_type = ship.get("ship_type", "bulk_carrier")
            fuel_type = ship.get("fuel_type", "HFO")
            gt = float(ship.get("gross_tonnage", 50000))
            dwt = float(ship.get("deadweight_tonnes", gt * 0.85))
            fuel_t = float(ship.get("annual_fuel_consumption_t", dwt * 0.042))
            dist_nm = float(ship.get("annual_distance_nm", 60000))
            cargo_t = float(ship.get("annual_cargo_tonnes", dwt * 0.80))
            build_year = int(ship.get("build_year", 2010))
            year = int(ship.get("year", 2024))
            co2_t = fuel_t * FUEL_EMISSION_FACTORS.get(fuel_type, FUEL_EMISSION_FACTORS["HFO"])["cf_t_co2_t_fuel"]
            eu_share = float(ship.get("eu_route_share_pct", 35.0))
            energy_mj = fuel_t * 40000.0  # approx MJ per tonne fuel

            # CII
            cii_res = self.assess_cii(ship_entity, ship_type, dwt, fuel_t, dist_nm, cargo_t, fuel_type, year)
            cii_ratings.append(cii_res["cii_rating"])

            # EU ETS
            ets_res = self.assess_eu_ets(ship_entity, ship_type, co2_t, eu_share, year)
            eu_ets_total += ets_res["cost_eur_base"]

            # FuelEU
            feu_res = self.assess_fueleu(ship_entity, ship_type, fuel_type, energy_mj, year)
            if feu_res["compliant"]:
                fueleu_compliant_count += 1

            # Stranding
            str_res = self.assess_stranding(ship_entity, ship_type, build_year, fuel_type, gt)
            transition_capex_total += str_res["alt_fuel_capex_usd"]

            risk_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            risk_scores.append(risk_map.get(str_res["risk_rating"], 2))

        n = len(ships)
        fueleu_compliance_rate = round(fueleu_compliant_count / n * 100.0, 2)

        rating_order = ["A", "B", "C", "D", "E"]
        rating_counts = {r: cii_ratings.count(r) for r in rating_order}
        worst_rating = "A"
        for r in reversed(rating_order):
            if rating_counts[r] > 0:
                worst_rating = r
                break
        fleet_cii_rating = worst_rating

        avg_risk = sum(risk_scores) / n
        if avg_risk >= 3.5:
            portfolio_risk_score = "critical"
        elif avg_risk >= 2.5:
            portfolio_risk_score = "high"
        elif avg_risk >= 1.5:
            portfolio_risk_score = "medium"
        else:
            portfolio_risk_score = "low"

        return {
            "entity_id": entity_id,
            "fleet_size": n,
            "fleet_cii_rating": fleet_cii_rating,
            "cii_rating_distribution": rating_counts,
            "eu_ets_total_cost_eur": round(eu_ets_total, 2),
            "fueleu_compliance_rate": fueleu_compliance_rate,
            "transition_capex_usd": round(transition_capex_total, 2),
            "portfolio_risk_score": portfolio_risk_score,
            "regulatory_exposure": ["IMO_GHG_2023", "MARPOL_VI", "EU_ETS", "FuelEU_Maritime"],
        }
