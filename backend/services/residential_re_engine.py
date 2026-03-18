"""
Residential Real Estate Engine
================================
Gap 5.2.8 — dedicated residential property assessment module covering:

1. Residential Subtypes: Single Family, Multi-Family, Social Housing, PBSA
2. Comparable Sales Valuation (hedonic regression, AVM-style)
3. Mortgage Portfolio Climate Risk (LTV climate stress, EPC distribution)
4. Affordable Housing Decarbonisation Pathways
5. EPC-based transition risk for residential stock

References:
  - RICS Red Book 2022, VPS 5 (Residential valuation)
  - RICS VPGA 12 (ESG and sustainability considerations)
  - UK MEES Regulations 2015 (min EPC E, moving to C by 2030)
  - EU EPBD Recast 2024/1275 (ZEB standard for new build by 2030)
  - CRREM v2.3 residential pathways
  - EPC rating methodology (SAP for UK, NTA 8800 for NL, DIN V 18599 for DE)
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("platform.residential_re")


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

# EPC rating → estimated kWh/m²/yr (UK SAP-based central estimates)
EPC_ENERGY_INTENSITY: dict[str, float] = {
    "A": 25,    # ≤25 kWh/m²/yr
    "B": 55,    # 26–55
    "C": 80,    # 56–80
    "D": 110,   # 81–110
    "E": 145,   # 111–145
    "F": 195,   # 146–195
    "G": 280,   # >195
}

# MEES (Minimum Energy Efficiency Standards) regulatory timelines
MEES_TIMELINES: dict[str, list[dict]] = {
    "GB": [
        {"year": 2018, "min_rating": "E", "scope": "new_lettings"},
        {"year": 2020, "min_rating": "E", "scope": "all_lettings"},
        {"year": 2025, "min_rating": "C", "scope": "new_lettings_proposed"},
        {"year": 2028, "min_rating": "C", "scope": "all_lettings_proposed"},
    ],
    "NL": [
        {"year": 2023, "min_rating": "D", "scope": "office"},
        {"year": 2030, "min_rating": "A", "scope": "office"},
    ],
    "FR": [
        {"year": 2025, "min_rating": "G_banned", "scope": "all_lettings"},
        {"year": 2028, "min_rating": "F_banned", "scope": "all_lettings"},
        {"year": 2034, "min_rating": "E_banned", "scope": "all_lettings"},
    ],
    "DE": [
        {"year": 2030, "min_rating": "D", "scope": "proposed"},
        {"year": 2045, "min_rating": "A", "scope": "target"},
    ],
}

# Retrofit cost per EPC band improvement (EUR/m²) — UK averages
RETROFIT_COST_PER_M2: dict[str, dict[str, float]] = {
    "G_to_F": {"low": 30, "mid": 55, "high": 80},
    "F_to_E": {"low": 40, "mid": 65, "high": 100},
    "E_to_D": {"low": 60, "mid": 100, "high": 160},
    "D_to_C": {"low": 120, "mid": 200, "high": 320},
    "C_to_B": {"low": 200, "mid": 350, "high": 550},
    "B_to_A": {"low": 350, "mid": 600, "high": 900},
}

EPC_ORDER = ["A", "B", "C", "D", "E", "F", "G"]

# Residential hedonic regression coefficients (normalised)
HEDONIC_COEFFICIENTS: dict[str, float] = {
    "floor_area_m2": 2800,        # EUR per m²
    "bedrooms": 15000,            # EUR per bedroom
    "bathrooms": 12000,           # EUR per bathroom
    "age_years_penalty": -500,    # EUR per year of age
    "garden_m2": 120,             # EUR per m² garden
    "parking_spaces": 20000,      # EUR per space
    "epc_premium_per_band": 0.03, # 3% value premium per EPC band above D
    "flood_risk_discount": -0.08, # 8% discount if in flood zone
    "proximity_transport_km": -5000,  # EUR per km to nearest station
}

# CRREM 1.5°C residential pathway — target kWh/m²/yr by year (EU avg)
CRREM_RESIDENTIAL_PATHWAY: dict[int, float] = {
    2020: 120,
    2025: 100,
    2030: 75,
    2035: 55,
    2040: 40,
    2045: 28,
    2050: 18,
}

# Social housing stock EPC distribution (UK illustrative)
SOCIAL_HOUSING_EPC_DIST: dict[str, float] = {
    "A": 0.01, "B": 0.05, "C": 0.35, "D": 0.40,
    "E": 0.13, "F": 0.04, "G": 0.02,
}

# Affordable housing decarbonisation measures
DECARB_MEASURES: list[dict[str, Any]] = [
    {"measure": "Loft insulation (270mm)", "cost_eur_m2": 8, "energy_saving_pct": 0.12,
     "applicable_epc": ["D", "E", "F", "G"], "lifetime_years": 42},
    {"measure": "Cavity wall insulation", "cost_eur_m2": 12, "energy_saving_pct": 0.18,
     "applicable_epc": ["D", "E", "F", "G"], "lifetime_years": 42},
    {"measure": "External wall insulation (EWI)", "cost_eur_m2": 95, "energy_saving_pct": 0.30,
     "applicable_epc": ["E", "F", "G"], "lifetime_years": 30},
    {"measure": "Air source heat pump (ASHP)", "cost_eur_m2": 65, "energy_saving_pct": 0.45,
     "applicable_epc": ["D", "E", "F", "G"], "lifetime_years": 20},
    {"measure": "Solar PV (4 kWp)", "cost_eur_m2": 22, "energy_saving_pct": 0.15,
     "applicable_epc": ["C", "D", "E", "F", "G"], "lifetime_years": 25},
    {"measure": "Double → triple glazing", "cost_eur_m2": 55, "energy_saving_pct": 0.10,
     "applicable_epc": ["D", "E", "F", "G"], "lifetime_years": 30},
    {"measure": "Smart heating controls", "cost_eur_m2": 3, "energy_saving_pct": 0.08,
     "applicable_epc": ["C", "D", "E", "F", "G"], "lifetime_years": 15},
]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ResidentialPropertyInput:
    property_id: str
    property_type: str = "single_family"  # single_family | multi_family | social_housing | pbsa
    address: str = ""
    country: str = "GB"
    floor_area_m2: float = 0
    bedrooms: int = 0
    bathrooms: int = 0
    age_years: int = 0
    garden_m2: float = 0
    parking_spaces: int = 0
    epc_rating: str = "D"
    energy_kwh_m2_yr: float = 0  # actual if metered; else derived from EPC
    in_flood_zone: bool = False
    proximity_transport_km: float = 1.0
    market_value_eur: float = 0  # if known
    mortgage_ltv: float = 0.75
    mortgage_balance_eur: float = 0


@dataclass
class ResidentialValuationResult:
    property_id: str
    property_type: str
    # Hedonic valuation
    hedonic_value_eur: float = 0
    value_per_m2_eur: float = 0
    epc_premium_pct: float = 0
    flood_discount_pct: float = 0
    # EPC transition risk
    current_epc: str = ""
    energy_intensity_kwh_m2: float = 0
    crrem_stranding_year: int | None = None
    years_to_stranding: int | None = None
    mees_compliant: bool = True
    mees_compliance_year: int | None = None
    retrofit_cost_to_c_eur: float = 0
    retrofit_cost_to_b_eur: float = 0
    # Climate-adjusted LTV
    climate_adjusted_value_eur: float = 0
    climate_ltv: float = 0
    ltv_stress_bps: float = 0
    # Recommendations
    recommendations: list[str] = field(default_factory=list)


@dataclass
class MortgagePortfolioInput:
    portfolio_id: str
    properties: list[ResidentialPropertyInput]
    carbon_price_eur_tco2: float = 80
    stress_scenario: str = "moderate"  # moderate | severe | extreme


@dataclass
class MortgagePortfolioResult:
    portfolio_id: str
    total_properties: int = 0
    total_mortgage_exposure_eur: float = 0
    avg_ltv: float = 0
    avg_climate_ltv: float = 0
    ltv_stress_avg_bps: float = 0
    epc_distribution: dict[str, int] = field(default_factory=dict)
    below_mees_count: int = 0
    below_mees_pct: float = 0
    stranding_before_2030_count: int = 0
    stranding_before_2030_pct: float = 0
    total_retrofit_cost_to_c_eur: float = 0
    avg_energy_intensity_kwh_m2: float = 0
    weighted_avg_epc_band: str = ""
    risk_band: str = ""  # low | medium | high | critical
    property_results: list[dict] = field(default_factory=list)


@dataclass
class DecarbPathwayResult:
    total_units: int = 0
    current_avg_energy_kwh_m2: float = 0
    target_energy_kwh_m2: float = 0
    energy_gap_kwh_m2: float = 0
    recommended_measures: list[dict] = field(default_factory=list)
    total_capex_eur: float = 0
    annual_energy_savings_eur: float = 0
    payback_years: float = 0
    co2_reduction_tco2_yr: float = 0
    units_by_current_epc: dict[str, int] = field(default_factory=dict)
    units_reaching_target: int = 0
    units_remaining_gap: int = 0


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ResidentialRealEstateEngine:
    """Residential RE valuation, mortgage climate risk, and decarbonisation planning."""

    # ── Hedonic Valuation ─────────────────────────────────────────────────

    def value_property(self, inp: ResidentialPropertyInput) -> ResidentialValuationResult:
        """
        Hedonic regression-based valuation with EPC premium/discount,
        CRREM stranding year, MEES compliance, and climate-adjusted LTV.
        """
        coeff = HEDONIC_COEFFICIENTS
        area = max(inp.floor_area_m2, 30)

        # Base hedonic value
        base = (
            area * coeff["floor_area_m2"]
            + inp.bedrooms * coeff["bedrooms"]
            + inp.bathrooms * coeff["bathrooms"]
            + inp.age_years * coeff["age_years_penalty"]
            + inp.garden_m2 * coeff["garden_m2"]
            + inp.parking_spaces * coeff["parking_spaces"]
            + inp.proximity_transport_km * coeff["proximity_transport_km"]
        )
        base = max(base, area * 500)  # floor: at least 500 EUR/m²

        # EPC premium/discount relative to D
        epc_idx = EPC_ORDER.index(inp.epc_rating) if inp.epc_rating in EPC_ORDER else 3
        d_idx = EPC_ORDER.index("D")
        band_diff = d_idx - epc_idx  # positive = better than D
        epc_pct = band_diff * coeff["epc_premium_per_band"]
        base *= (1 + epc_pct)

        # Flood zone discount
        flood_pct = coeff["flood_risk_discount"] if inp.in_flood_zone else 0
        base *= (1 + flood_pct)

        hedonic_value = round(base, 2)
        value_m2 = round(hedonic_value / area, 2) if area else 0

        # Energy intensity
        energy_kwh = inp.energy_kwh_m2_yr if inp.energy_kwh_m2_yr > 0 else EPC_ENERGY_INTENSITY.get(inp.epc_rating, 110)

        # CRREM stranding year
        stranding_year = None
        years_to_strand = None
        for yr in sorted(CRREM_RESIDENTIAL_PATHWAY.keys()):
            if energy_kwh > CRREM_RESIDENTIAL_PATHWAY[yr]:
                stranding_year = yr
                break
        if stranding_year:
            years_to_strand = max(0, stranding_year - 2026)

        # MEES compliance (GB)
        mees_ok = True
        mees_year = None
        if inp.country.upper() in ("GB", "UK"):
            for rule in MEES_TIMELINES.get("GB", []):
                min_epc = rule["min_rating"].replace("_banned", "")
                if min_epc in EPC_ORDER:
                    min_idx = EPC_ORDER.index(min_epc)
                    if epc_idx > min_idx and rule["year"] >= 2026:
                        mees_ok = False
                        mees_year = rule["year"]
                        break

        # Retrofit cost estimation
        retrofit_c = self._estimate_retrofit_cost(inp.epc_rating, "C", area)
        retrofit_b = self._estimate_retrofit_cost(inp.epc_rating, "B", area)

        # Climate-adjusted value (transition risk haircut)
        transition_haircut = 0.0
        if stranding_year and stranding_year <= 2035:
            transition_haircut = 0.05 + (2035 - stranding_year) * 0.01
        if not mees_ok:
            transition_haircut += 0.03
        transition_haircut = min(transition_haircut, 0.25)

        climate_adj_value = round(hedonic_value * (1 - transition_haircut), 2)

        # Climate-adjusted LTV
        actual_value = inp.market_value_eur if inp.market_value_eur > 0 else hedonic_value
        mortgage = inp.mortgage_balance_eur if inp.mortgage_balance_eur > 0 else actual_value * inp.mortgage_ltv
        climate_ltv = round(mortgage / climate_adj_value, 4) if climate_adj_value > 0 else 0
        base_ltv = round(mortgage / actual_value, 4) if actual_value > 0 else 0
        ltv_stress = round((climate_ltv - base_ltv) * 10000, 1)  # bps

        recs = []
        if not mees_ok:
            recs.append(f"MEES non-compliant: EPC {inp.epc_rating} below minimum by {mees_year}")
        if stranding_year and stranding_year <= 2030:
            recs.append(f"CRREM stranding by {stranding_year} — urgent retrofit needed")
        if epc_idx >= 4:  # E or worse
            recs.append("Consider deep retrofit (EWI + ASHP) for EPC improvement")
        if inp.in_flood_zone:
            recs.append("Flood zone: consider flood resilience measures and insurance review")

        return ResidentialValuationResult(
            property_id=inp.property_id,
            property_type=inp.property_type,
            hedonic_value_eur=hedonic_value,
            value_per_m2_eur=value_m2,
            epc_premium_pct=round(epc_pct * 100, 2),
            flood_discount_pct=round(flood_pct * 100, 2),
            current_epc=inp.epc_rating,
            energy_intensity_kwh_m2=energy_kwh,
            crrem_stranding_year=stranding_year,
            years_to_stranding=years_to_strand,
            mees_compliant=mees_ok,
            mees_compliance_year=mees_year,
            retrofit_cost_to_c_eur=retrofit_c,
            retrofit_cost_to_b_eur=retrofit_b,
            climate_adjusted_value_eur=climate_adj_value,
            climate_ltv=climate_ltv,
            ltv_stress_bps=ltv_stress,
            recommendations=recs,
        )

    # ── Mortgage Portfolio Climate Risk ───────────────────────────────────

    def assess_mortgage_portfolio(self, inp: MortgagePortfolioInput) -> MortgagePortfolioResult:
        """
        Portfolio-level mortgage climate risk: EPC distribution, stranding
        exposure, LTV stress, and aggregate retrofit cost.
        """
        results = []
        epc_dist: dict[str, int] = {r: 0 for r in EPC_ORDER}
        total_mortgage = 0.0
        total_ltv = 0.0
        total_climate_ltv = 0.0
        total_stress = 0.0
        total_retrofit_c = 0.0
        total_energy = 0.0
        below_mees = 0
        strand_2030 = 0

        stress_mult = {"moderate": 1.0, "severe": 1.5, "extreme": 2.0}.get(inp.stress_scenario, 1.0)

        for prop in inp.properties:
            res = self.value_property(prop)

            # Apply stress scenario multiplier to transition haircut
            if stress_mult > 1.0 and res.ltv_stress_bps > 0:
                res.ltv_stress_bps = round(res.ltv_stress_bps * stress_mult, 1)

            epc_dist[res.current_epc] = epc_dist.get(res.current_epc, 0) + 1
            mortgage_bal = prop.mortgage_balance_eur if prop.mortgage_balance_eur > 0 else (
                prop.market_value_eur * prop.mortgage_ltv if prop.market_value_eur > 0 else
                res.hedonic_value_eur * prop.mortgage_ltv
            )
            total_mortgage += mortgage_bal
            total_ltv += prop.mortgage_ltv
            total_climate_ltv += res.climate_ltv
            total_stress += res.ltv_stress_bps
            total_retrofit_c += res.retrofit_cost_to_c_eur
            total_energy += res.energy_intensity_kwh_m2
            if not res.mees_compliant:
                below_mees += 1
            if res.crrem_stranding_year and res.crrem_stranding_year <= 2030:
                strand_2030 += 1

            results.append({
                "property_id": res.property_id,
                "property_type": res.property_type,
                "hedonic_value_eur": res.hedonic_value_eur,
                "current_epc": res.current_epc,
                "energy_intensity_kwh_m2": res.energy_intensity_kwh_m2,
                "crrem_stranding_year": res.crrem_stranding_year,
                "mees_compliant": res.mees_compliant,
                "climate_ltv": res.climate_ltv,
                "ltv_stress_bps": res.ltv_stress_bps,
                "retrofit_cost_to_c_eur": res.retrofit_cost_to_c_eur,
            })

        n = len(inp.properties) or 1
        avg_ltv = round(total_ltv / n, 4)
        avg_climate_ltv = round(total_climate_ltv / n, 4)
        avg_stress = round(total_stress / n, 1)
        avg_energy = round(total_energy / n, 1)
        below_pct = round(below_mees / n * 100, 1)
        strand_pct = round(strand_2030 / n * 100, 1)

        # Weighted average EPC band
        total_area = sum(max(p.floor_area_m2, 50) for p in inp.properties) or 1
        weighted_epc_idx = sum(
            EPC_ORDER.index(p.epc_rating if p.epc_rating in EPC_ORDER else "D") * max(p.floor_area_m2, 50)
            for p in inp.properties
        ) / total_area
        weighted_band = EPC_ORDER[min(round(weighted_epc_idx), 6)]

        # Risk band
        if avg_stress > 200 or strand_pct > 30:
            risk = "critical"
        elif avg_stress > 100 or strand_pct > 15:
            risk = "high"
        elif avg_stress > 50 or below_pct > 20:
            risk = "medium"
        else:
            risk = "low"

        return MortgagePortfolioResult(
            portfolio_id=inp.portfolio_id,
            total_properties=n,
            total_mortgage_exposure_eur=round(total_mortgage, 2),
            avg_ltv=avg_ltv,
            avg_climate_ltv=avg_climate_ltv,
            ltv_stress_avg_bps=avg_stress,
            epc_distribution=epc_dist,
            below_mees_count=below_mees,
            below_mees_pct=below_pct,
            stranding_before_2030_count=strand_2030,
            stranding_before_2030_pct=strand_pct,
            total_retrofit_cost_to_c_eur=round(total_retrofit_c, 2),
            avg_energy_intensity_kwh_m2=avg_energy,
            weighted_avg_epc_band=weighted_band,
            risk_band=risk,
            property_results=results,
        )

    # ── Affordable Housing Decarbonisation Pathway ────────────────────────

    def decarb_pathway(
        self,
        units: list[dict],
        target_epc: str = "C",
        energy_cost_eur_kwh: float = 0.28,
        grid_ef_kgco2_kwh: float = 0.233,
    ) -> DecarbPathwayResult:
        """
        Generate decarbonisation pathway for a social/affordable housing stock.

        units: list of {"unit_id", "floor_area_m2", "epc_rating", "property_type"}
        """
        target_energy = EPC_ENERGY_INTENSITY.get(target_epc, 80)
        total_units = len(units)
        epc_counts: dict[str, int] = {r: 0 for r in EPC_ORDER}
        total_energy_sum = 0.0
        total_capex = 0.0
        total_savings = 0.0
        total_co2_reduction = 0.0
        units_ok = 0
        units_gap = 0
        all_measures: dict[str, dict] = {}

        for u in units:
            epc = u.get("epc_rating", "D")
            area = u.get("floor_area_m2", 70)
            epc_counts[epc] = epc_counts.get(epc, 0) + 1
            current_energy = EPC_ENERGY_INTENSITY.get(epc, 110)
            total_energy_sum += current_energy

            if current_energy <= target_energy:
                units_ok += 1
                continue

            units_gap += 1
            energy_gap = current_energy - target_energy

            # Select applicable measures
            for m in DECARB_MEASURES:
                if epc in m["applicable_epc"]:
                    cost = m["cost_eur_m2"] * area
                    saving_kwh = current_energy * m["energy_saving_pct"] * area
                    saving_eur = saving_kwh * energy_cost_eur_kwh
                    co2_saved = saving_kwh * grid_ef_kgco2_kwh / 1000  # tCO2

                    name = m["measure"]
                    if name not in all_measures:
                        all_measures[name] = {
                            "measure": name,
                            "units_applicable": 0,
                            "total_capex_eur": 0,
                            "annual_energy_savings_kwh": 0,
                            "annual_cost_savings_eur": 0,
                            "annual_co2_reduction_tco2": 0,
                            "avg_lifetime_years": m["lifetime_years"],
                        }
                    all_measures[name]["units_applicable"] += 1
                    all_measures[name]["total_capex_eur"] += cost
                    all_measures[name]["annual_energy_savings_kwh"] += saving_kwh
                    all_measures[name]["annual_cost_savings_eur"] += saving_eur
                    all_measures[name]["annual_co2_reduction_tco2"] += co2_saved

                    total_capex += cost
                    total_savings += saving_eur
                    total_co2_reduction += co2_saved

        avg_energy = total_energy_sum / total_units if total_units else 0
        payback = total_capex / total_savings if total_savings > 0 else 0

        # Round measures
        measures_list = []
        for m_data in sorted(all_measures.values(), key=lambda x: -x["annual_co2_reduction_tco2"]):
            m_data["total_capex_eur"] = round(m_data["total_capex_eur"], 2)
            m_data["annual_energy_savings_kwh"] = round(m_data["annual_energy_savings_kwh"], 1)
            m_data["annual_cost_savings_eur"] = round(m_data["annual_cost_savings_eur"], 2)
            m_data["annual_co2_reduction_tco2"] = round(m_data["annual_co2_reduction_tco2"], 3)
            measures_list.append(m_data)

        return DecarbPathwayResult(
            total_units=total_units,
            current_avg_energy_kwh_m2=round(avg_energy, 1),
            target_energy_kwh_m2=target_energy,
            energy_gap_kwh_m2=round(max(0, avg_energy - target_energy), 1),
            recommended_measures=measures_list,
            total_capex_eur=round(total_capex, 2),
            annual_energy_savings_eur=round(total_savings, 2),
            payback_years=round(payback, 1),
            co2_reduction_tco2_yr=round(total_co2_reduction, 3),
            units_by_current_epc=epc_counts,
            units_reaching_target=units_ok,
            units_remaining_gap=units_gap,
        )

    # ── Reference Data Accessors ──────────────────────────────────────────

    def get_epc_energy_map(self) -> dict:
        return dict(EPC_ENERGY_INTENSITY)

    def get_mees_timelines(self) -> dict:
        return dict(MEES_TIMELINES)

    def get_crrem_residential_pathway(self) -> dict:
        return dict(CRREM_RESIDENTIAL_PATHWAY)

    def get_retrofit_cost_matrix(self) -> dict:
        return dict(RETROFIT_COST_PER_M2)

    def get_decarb_measures(self) -> list:
        return list(DECARB_MEASURES)

    def get_hedonic_coefficients(self) -> dict:
        return dict(HEDONIC_COEFFICIENTS)

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _estimate_retrofit_cost(self, from_epc: str, to_epc: str, area_m2: float) -> float:
        """Estimate total retrofit cost to improve from one EPC band to another."""
        if from_epc not in EPC_ORDER or to_epc not in EPC_ORDER:
            return 0
        from_idx = EPC_ORDER.index(from_epc)
        to_idx = EPC_ORDER.index(to_epc)
        if from_idx <= to_idx:
            return 0  # already at or better than target

        total = 0.0
        for i in range(from_idx, to_idx, -1):
            key = f"{EPC_ORDER[i]}_to_{EPC_ORDER[i-1]}"
            step_cost = RETROFIT_COST_PER_M2.get(key, {}).get("mid", 150)
            total += step_cost * area_m2
        return round(total, 2)
