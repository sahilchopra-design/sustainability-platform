"""
Green Hydrogen (GH2) LCOH & Carbon Intensity Calculator
Aligned with:
  IRENA Green Hydrogen Cost Reduction (2020)
  IEA Global Hydrogen Review 2023
  IPHE Methodology for Determining the GHG Emissions (2022)
  EU Delegated Regulation 2023/1184 (Renewable Fuels of Non-Biological Origin — RFNBO)
  Hydrogen Council Global Hydrogen Flows 2023
  DOE Hydrogen Shot: $1/kg by 2031

Colours:
  Green H2:      Electrolysis + ≥100% renewable electricity (certified)
  Pink H2:       Electrolysis + nuclear electricity
  Blue H2:       SMR/ATR with CCS (captured ≥85%)
  Turquoise H2:  Methane pyrolysis (solid carbon by-product)
  Grey H2:       SMR without CCS
  Brown H2:      Coal gasification (no CCS)
  Black H2:      Coal gasification (no CCS, high-carbon coal)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── Constants ──────────────────────────────────────────────────────────────────
CO2_INTENSITY_ELECTRICITY: dict[str, float] = {
    # kg CO2e / kWh
    "grid_eu_avg": 0.276,
    "grid_us_avg": 0.386,
    "grid_china": 0.555,
    "grid_india": 0.713,
    "grid_australia": 0.540,
    "grid_uk": 0.233,
    "solar_pv_lcoe": 0.048,
    "onshore_wind": 0.011,
    "offshore_wind": 0.012,
    "nuclear": 0.012,
    "hydro": 0.024,
    "dedicated_vre_ppa": 0.018,  # blended contracted RE
}

# kWh of electricity per kg H2 (electrolyser efficiency)
ELECTROLYSER_EFFICIENCY: dict[str, float] = {
    "PEM": 55.0,       # kWh/kg H2
    "Alkaline": 53.5,
    "SOEC": 45.0,      # High-temp SOEC (best case)
    "AEM": 57.0,       # Anion Exchange Membrane
}

# SMR CH4 consumption: approx 4.0 kg CH4 per kg H2; CH4 = 2.75 kg CO2/kg
SMR_CO2_GREY = 9.0       # kg CO2 / kg H2 (grey)
SMR_CO2_BLUE_MIN = 1.4   # kg CO2 / kg H2 (with CCS ≥90% capture)
SMR_CO2_BLUE_MAX = 2.5   # kg CO2 / kg H2 (with CCS 85% capture)
COAL_CO2_BROWN = 20.0    # kg CO2 / kg H2 (coal gasification)

# EU RFNBO threshold (Delegated Regulation 2023/1184): 3.38 kg CO2e / kg H2 (lifecycle)
EU_RFNBO_THRESHOLD = 3.38

# IEA Green H2 definition: < 0.5 kg CO2 / kg H2 (very stringent)
IEA_GREEN_THRESHOLD = 0.5

# Hydrogen Council / general industry threshold for "low-carbon": < 4 kg CO2 / kg H2
LOW_CARBON_THRESHOLD = 4.0

# Cost reference data (USD/kg H2, 2024)
REFERENCE_COSTS: dict[str, dict] = {
    "green_solar_mena": {"range_low": 2.0, "range_high": 4.5, "ref_year": 2024, "source": "IRENA 2023"},
    "green_wind_north_sea": {"range_low": 3.5, "range_high": 6.5, "ref_year": 2024, "source": "IRENA 2023"},
    "green_solar_australia": {"range_low": 2.5, "range_high": 5.0, "ref_year": 2024, "source": "IRENA 2023"},
    "blue_smr_ccs": {"range_low": 1.5, "range_high": 2.5, "ref_year": 2024, "source": "IEA 2023"},
    "grey_smr": {"range_low": 1.0, "range_high": 2.0, "ref_year": 2024, "source": "IEA 2023"},
    "doe_hydrogen_shot_2031": {"range_low": 1.0, "range_high": 1.0, "ref_year": 2031, "source": "DOE H2Shot"},
}


# ── Dataclasses ────────────────────────────────────────────────────────────────
@dataclass
class GreenHydrogenInput:
    """Input parameters for LCOH and carbon intensity calculation."""
    # Project identity
    project_name: str = "Green H2 Project — NEOM"
    country: str = "Saudi Arabia"
    production_pathway: str = "PEM"          # PEM, Alkaline, SOEC, AEM, SMR_CCS, SMR_Grey, Coal_Gasification

    # Scale
    capacity_mw_electrolyser: float = 100.0   # MW electrolyser (for electrolysis pathways)
    capacity_factor_pct: float = 50.0          # % (electrolysis uses when renewable available)
    annual_production_kt: Optional[float] = None  # override; if None, computed

    # Electrolysis-specific
    electricity_source: str = "dedicated_vre_ppa"
    electricity_price_usd_per_kwh: float = 0.035
    electrolyser_capex_usd_per_kw: float = 800.0  # USD/kW (2024 benchmark)
    electrolyser_opex_pct_capex: float = 3.0       # % of capex pa
    stack_lifetime_years: float = 10.0             # stack replacement cycle
    stack_replacement_cost_pct: float = 40.0       # % of electrolyser capex
    project_lifetime_years: float = 20.0
    wacc_pct: float = 7.0

    # Water input
    water_cost_usd_per_tonne: float = 3.5
    water_consumption_l_per_kg_h2: float = 9.0     # IEA: ~9 L/kg H2 (electrolysis)
    water_desalination_included: bool = False
    desalination_cost_usd_per_m3: float = 0.8

    # Compression / storage / transport
    compression_storage_usd_per_kg: float = 0.30
    transport_mode: str = "pipeline"               # pipeline, ammonia_conversion, liquid_h2
    transport_cost_usd_per_kg: float = 0.50

    # SMR-specific (only for blue/grey pathways)
    natural_gas_price_usd_per_mmbtu: float = 6.0
    ccs_capex_usd_per_tco2: float = 80.0
    ccs_capture_rate_pct: float = 90.0

    # Carbon pricing
    carbon_price_usd_per_tco2: float = 85.0       # EU ETS mid-2024

    # Government support
    subsidy_usd_per_kg: float = 0.0               # e.g. IRA Section 45V credit, EU H2 bank
    ira_45v_eligible: bool = False                  # US Inflation Reduction Act H2 tax credit


@dataclass
class GreenHydrogenResult:
    """Result of LCOH + carbon intensity computation."""
    project_name: str
    production_pathway: str
    colour: str

    # Production
    annual_production_t: float
    annual_production_kt: float

    # LCOH components (USD/kg H2)
    lcoh_electricity: float
    lcoh_electrolyser_capex: float
    lcoh_opex: float
    lcoh_water: float
    lcoh_compression_storage: float
    lcoh_transport: float
    lcoh_stack_replacement: float
    lcoh_total: float
    lcoh_after_subsidy: float

    # Carbon intensity
    co2_intensity_kg_per_kgh2: float
    co2_intensity_gco2_per_mj: float    # gCO2e/MJ (IPHE standard)

    # Certification / compliance
    eu_rfnbo_eligible: bool            # < 3.38 kg CO2/kg H2
    iea_green_eligible: bool           # < 0.5 kg CO2/kg H2
    low_carbon_label: bool             # < 4 kg CO2/kg H2

    # Carbon cost
    embedded_carbon_cost_usd_per_kg: float
    carbon_abatement_vs_grey_usd_per_tco2: Optional[float]

    # Cost benchmark
    vs_doe_target_pct: float           # % vs $1/kg DOE target
    vs_grey_premium_pct: float         # % premium vs grey H2 (~$1.5/kg)

    # Narrative
    colour_definition: str
    feasibility: str
    narrative: str


# ── Colour classifier ─────────────────────────────────────────────────────────
def _classify_colour(pathway: str, co2_kg_per_kgh2: float, electricity_source: str,
                     ccs_capture_rate: float) -> tuple[str, str]:
    """Returns (colour, definition)."""
    p = pathway.lower()
    if "coal" in p:
        return "Brown/Black", "Coal gasification without CCS — highest emission pathway"
    if "smr" in p and "grey" in p:
        return "Grey", "Steam methane reforming (SMR) without CCS — 9–12 kg CO2/kg H2"
    if "smr" in p and "ccs" in p:
        if ccs_capture_rate >= 85:
            return "Blue", f"SMR with CCS ({ccs_capture_rate:.0f}% capture rate)"
        return "Light Blue", f"SMR with partial CCS ({ccs_capture_rate:.0f}% capture — insufficient for blue label)"
    if electricity_source == "nuclear":
        return "Pink", "Electrolysis powered by nuclear electricity"
    if "pyrolysis" in p:
        return "Turquoise", "Methane pyrolysis — solid carbon by-product, no CCS required"
    # Electrolysis
    if co2_kg_per_kgh2 <= IEA_GREEN_THRESHOLD:
        return "Green", "Electrolysis powered by certified renewable electricity — <0.5 kg CO2/kg H2 (IEA definition)"
    if co2_kg_per_kgh2 <= EU_RFNBO_THRESHOLD:
        return "Green (EU RFNBO)", f"EU RFNBO eligible — {co2_kg_per_kgh2:.2f} kg CO2/kg H2 < 3.38 threshold (EU Delegated Reg 2023/1184)"
    if co2_kg_per_kgh2 <= LOW_CARBON_THRESHOLD:
        return "Low-Carbon", f"Below 4 kg CO2/kg H2 — qualifies as low-carbon but not fully green"
    return "Grey/High-Carbon Electrolysis", f"CO2 intensity {co2_kg_per_kgh2:.1f} kg/kg H2 exceeds low-carbon threshold"


# ── Main calculation ──────────────────────────────────────────────────────────
def calculate_lcoh(inp: GreenHydrogenInput) -> GreenHydrogenResult:
    """Compute Levelised Cost of Hydrogen (LCOH) and carbon intensity."""
    p = inp.production_pathway.lower()
    is_electrolysis = all(x not in p for x in ["smr", "coal", "pyrolysis"])

    # ── Annual production ──────────────────────────────────────────────────
    if is_electrolysis:
        eff = ELECTROLYSER_EFFICIENCY.get(inp.production_pathway, 55.0)  # kWh/kg H2
        annual_kwh = inp.capacity_mw_electrolyser * 1000 * 8760 * (inp.capacity_factor_pct / 100)
        annual_production_kg = annual_kwh / eff
    elif "smr" in p:
        # SMR: ~8,000 operating hours/yr; typical output 1,000 kg H2/hr per 50 MW input
        annual_production_kg = inp.capacity_mw_electrolyser * 1000 * 8000 / 50_000  # rough: 1 t H2 / MWth
        annual_production_kg = max(annual_production_kg, 1000)  # floor
    elif "coal" in p:
        annual_production_kg = inp.capacity_mw_electrolyser * 800 * 8000  # rough
        annual_production_kg = max(annual_production_kg, 1000)
    else:
        annual_production_kg = inp.annual_production_kt * 1e3 if inp.annual_production_kt else 5000

    if inp.annual_production_kt:
        annual_production_kg = inp.annual_production_kt * 1000

    annual_production_t = annual_production_kg / 1000

    # ── Carbon intensity ───────────────────────────────────────────────────
    elec_co2 = CO2_INTENSITY_ELECTRICITY.get(inp.electricity_source, 0.05)  # kg CO2/kWh

    if is_electrolysis:
        eff_kwh_per_kg = ELECTROLYSER_EFFICIENCY.get(inp.production_pathway, 55.0)
        co2_from_elec = eff_kwh_per_kg * elec_co2  # kg CO2 / kg H2
        co2_intensity = co2_from_elec  # ignore minor upstream
    elif "coal" in p:
        co2_intensity = COAL_CO2_BROWN
    elif "smr" in p and "ccs" in p:
        capture = inp.ccs_capture_rate_pct / 100
        co2_intensity = SMR_CO2_GREY * (1 - capture) + 0.5  # residual + upstream CH4
        co2_intensity = max(co2_intensity, SMR_CO2_BLUE_MIN)
    elif "smr" in p:
        co2_intensity = SMR_CO2_GREY
    else:
        co2_intensity = 0.5  # pyrolysis / other

    # gCO2e/MJ: H2 LHV = 120 MJ/kg; so (kg CO2/kg H2) / 120 * 1000
    co2_gco2_per_mj = (co2_intensity / 120) * 1000

    # ── LCOH — Capital ─────────────────────────────────────────────────────
    if is_electrolysis:
        total_electrolyser_capex = inp.electrolyser_capex_usd_per_kw * inp.capacity_mw_electrolyser * 1000
        # Annualised capex using CRF
        wacc = inp.wacc_pct / 100
        n = inp.project_lifetime_years
        crf = wacc * (1 + wacc) ** n / ((1 + wacc) ** n - 1)
        annual_capex = total_electrolyser_capex * crf

        # Stack replacement (every stack_lifetime_years)
        replacements = max(0, int(inp.project_lifetime_years / inp.stack_lifetime_years) - 1)
        stack_cost = total_electrolyser_capex * (inp.stack_replacement_cost_pct / 100)
        annual_stack = (replacements * stack_cost) / inp.project_lifetime_years if replacements > 0 else 0

        lcoh_capex = annual_capex / annual_production_kg if annual_production_kg > 0 else 0
        lcoh_stack = annual_stack / annual_production_kg if annual_production_kg > 0 else 0

        # Opex
        annual_opex_cost = total_electrolyser_capex * (inp.electrolyser_opex_pct_capex / 100)
        lcoh_opex = annual_opex_cost / annual_production_kg if annual_production_kg > 0 else 0

        # Electricity
        eff = ELECTROLYSER_EFFICIENCY.get(inp.production_pathway, 55.0)
        lcoh_electricity = eff * inp.electricity_price_usd_per_kwh
    else:
        # SMR / coal: simplified
        if "smr" in p:
            ng_cost_per_kg_h2 = inp.natural_gas_price_usd_per_mmbtu * 0.137  # ~0.137 MMBtu/kg H2
            lcoh_electricity = ng_cost_per_kg_h2
            ccs_capex_per_kg = (inp.ccs_capex_usd_per_tco2 * co2_intensity * (inp.ccs_capture_rate_pct / 100)) / 1000
            lcoh_capex = 0.4 + ccs_capex_per_kg if "ccs" in p else 0.3
        else:
            lcoh_electricity = 0.5  # coal
            lcoh_capex = 0.6
        lcoh_opex = 0.2
        lcoh_stack = 0.0

    # Water
    water_per_kg = inp.water_consumption_l_per_kg_h2 / 1000  # m3
    water_cost = water_per_kg * inp.water_cost_usd_per_tonne  # rough: 1 t water ≈ 1 m3
    if inp.water_desalination_included:
        water_cost += water_per_kg * inp.desalination_cost_usd_per_m3
    lcoh_water = water_cost

    # Compression / storage / transport
    lcoh_cs = inp.compression_storage_usd_per_kg
    lcoh_transport = inp.transport_cost_usd_per_kg

    # Total
    lcoh_total = (
        lcoh_electricity + lcoh_capex + lcoh_opex +
        lcoh_water + lcoh_cs + lcoh_transport + lcoh_stack
    )
    lcoh_after_subsidy = max(0, lcoh_total - inp.subsidy_usd_per_kg)

    # IRA 45V credit (up to $3/kg for <0.45 kg CO2/kg H2, tiered)
    if inp.ira_45v_eligible:
        ira_credit = 3.0 if co2_intensity < 0.45 else (1.0 if co2_intensity < 1.5 else 0.33)
        lcoh_after_subsidy = max(0, lcoh_after_subsidy - ira_credit)

    # ── Embedded carbon cost ───────────────────────────────────────────────
    embedded_carbon = co2_intensity * inp.carbon_price_usd_per_tco2 / 1000  # USD/kg H2
    # Abatement vs grey SMR
    co2_avoided = max(0, SMR_CO2_GREY - co2_intensity)  # kg CO2 / kg H2
    lcoh_premium_vs_grey = max(0, lcoh_total - REFERENCE_COSTS["grey_smr"]["range_high"])
    abatement_cost = (lcoh_premium_vs_grey / co2_avoided * 1000) if co2_avoided > 0 else None

    # ── Colour + certification ─────────────────────────────────────────────
    colour, colour_def = _classify_colour(
        inp.production_pathway, co2_intensity,
        inp.electricity_source, inp.ccs_capture_rate_pct
    )

    eu_rfnbo_eligible = co2_intensity <= EU_RFNBO_THRESHOLD
    iea_green_eligible = co2_intensity <= IEA_GREEN_THRESHOLD
    low_carbon = co2_intensity <= LOW_CARBON_THRESHOLD

    # ── vs benchmarks ──────────────────────────────────────────────────────
    doe_target = 1.0
    grey_ref = 1.5
    vs_doe = ((lcoh_after_subsidy - doe_target) / doe_target) * 100
    vs_grey = ((lcoh_after_subsidy - grey_ref) / grey_ref) * 100

    # ── Feasibility / narrative ────────────────────────────────────────────
    if lcoh_after_subsidy <= 2.0 and iea_green_eligible:
        feasibility = "competitive"
        narrative = (f"{colour} hydrogen at ${lcoh_after_subsidy:.2f}/kg — approaching cost parity with fossil pathways. "
                     f"CO2 intensity {co2_intensity:.2f} kg/kg H2 qualifies under IEA green definition.")
    elif lcoh_after_subsidy <= 4.0 and eu_rfnbo_eligible:
        feasibility = "developing"
        narrative = (f"{colour} hydrogen at ${lcoh_after_subsidy:.2f}/kg — EU RFNBO eligible. "
                     f"Cost reduction through electrolyser scale-up and lower electricity prices required for competitiveness.")
    elif not iea_green_eligible and not eu_rfnbo_eligible:
        feasibility = "high_carbon"
        narrative = (f"CO2 intensity {co2_intensity:.2f} kg/kg H2 exceeds green thresholds. "
                     f"Switch to certified renewable electricity or add CCS to qualify for green labelling.")
    else:
        feasibility = "transition"
        narrative = (f"{colour} hydrogen at ${lcoh_after_subsidy:.2f}/kg. "
                     f"Eligible for some certification schemes but above cost parity with fossil H2.")

    return GreenHydrogenResult(
        project_name=inp.project_name,
        production_pathway=inp.production_pathway,
        colour=colour,
        annual_production_t=annual_production_t,
        annual_production_kt=annual_production_t / 1000,
        lcoh_electricity=round(lcoh_electricity, 4),
        lcoh_electrolyser_capex=round(lcoh_capex if is_electrolysis else 0, 4),
        lcoh_opex=round(lcoh_opex, 4),
        lcoh_water=round(lcoh_water, 4),
        lcoh_compression_storage=round(lcoh_cs, 4),
        lcoh_transport=round(lcoh_transport, 4),
        lcoh_stack_replacement=round(lcoh_stack, 4),
        lcoh_total=round(lcoh_total, 3),
        lcoh_after_subsidy=round(lcoh_after_subsidy, 3),
        co2_intensity_kg_per_kgh2=round(co2_intensity, 3),
        co2_intensity_gco2_per_mj=round(co2_gco2_per_mj, 2),
        eu_rfnbo_eligible=eu_rfnbo_eligible,
        iea_green_eligible=iea_green_eligible,
        low_carbon_label=low_carbon,
        embedded_carbon_cost_usd_per_kg=round(embedded_carbon, 4),
        carbon_abatement_vs_grey_usd_per_tco2=round(abatement_cost, 0) if abatement_cost else None,
        vs_doe_target_pct=round(vs_doe, 1),
        vs_grey_premium_pct=round(vs_grey, 1),
        colour_definition=colour_def,
        feasibility=feasibility,
        narrative=narrative,
    )
