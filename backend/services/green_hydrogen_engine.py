"""
Green Hydrogen & RFNBO Compliance Engine  (E98)
================================================
EU Delegated Act 2023/1184 (RFNBOs — Renewable Fuels of Non-Biological Origin),
ISO 14040/14044 GHG intensity, REPowerEU / EU Hydrogen Strategy 10+10 Mt targets,
IEA Hydrogen Economics (LCOH), EU H2 Bank / H2 Contract for Difference framework,
and certification scheme recognition.

References:
  - Commission Delegated Regulation (EU) 2023/1184 (RFNBO GHG methodology)
  - Commission Delegated Regulation (EU) 2023/1185 (RFNBO additionality & correlations)
  - ISO 14040:2006 / ISO 14044:2006 (Life Cycle Assessment methodology)
  - EU Hydrogen Strategy COM(2020) 301 final
  - REPowerEU Plan COM(2022) 230 final (10 Mt domestic + 10 Mt imports by 2030)
  - IEA Global Hydrogen Review 2023
  - EU H2 Bank Pilot Auction 2023 (Innovation Fund)
  - German H2Global / AusH2 / H2auftrag tender models
  - Hydrogen Council Global Hydrogen Flows 2023
"""
from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# Reference Data — Country Grid Emission Factors + RE Share + REPowerEU
# ---------------------------------------------------------------------------

COUNTRY_GRID_FACTORS: dict[str, dict] = {
    "Germany": {
        "grid_ef_kg_co2_kwh": 0.38,
        "re_share_pct": 52.0,
        "bidding_zone": "DE-AT-LU",
        "repowereu_target_mt": 1.0,
        "current_capacity_mw": 120.0,
        "pipeline_mw": 3200.0,
    },
    "France": {
        "grid_ef_kg_co2_kwh": 0.06,
        "re_share_pct": 24.0,
        "bidding_zone": "FR",
        "repowereu_target_mt": 0.6,
        "current_capacity_mw": 45.0,
        "pipeline_mw": 1800.0,
    },
    "Spain": {
        "grid_ef_kg_co2_kwh": 0.18,
        "re_share_pct": 55.0,
        "bidding_zone": "ES",
        "repowereu_target_mt": 0.8,
        "current_capacity_mw": 210.0,
        "pipeline_mw": 4500.0,
    },
    "United Kingdom": {
        "grid_ef_kg_co2_kwh": 0.23,
        "re_share_pct": 42.0,
        "bidding_zone": "GB",
        "repowereu_target_mt": 0.0,
        "current_capacity_mw": 55.0,
        "pipeline_mw": 1500.0,
    },
    "Poland": {
        "grid_ef_kg_co2_kwh": 0.72,
        "re_share_pct": 22.0,
        "bidding_zone": "PL",
        "repowereu_target_mt": 0.2,
        "current_capacity_mw": 8.0,
        "pipeline_mw": 500.0,
    },
    "Norway": {
        "grid_ef_kg_co2_kwh": 0.02,
        "re_share_pct": 98.0,
        "bidding_zone": "NO1",
        "repowereu_target_mt": 0.0,
        "current_capacity_mw": 30.0,
        "pipeline_mw": 800.0,
    },
    "Netherlands": {
        "grid_ef_kg_co2_kwh": 0.30,
        "re_share_pct": 40.0,
        "bidding_zone": "NL",
        "repowereu_target_mt": 0.5,
        "current_capacity_mw": 90.0,
        "pipeline_mw": 2000.0,
    },
    "Denmark": {
        "grid_ef_kg_co2_kwh": 0.17,
        "re_share_pct": 68.0,
        "bidding_zone": "DK1",
        "repowereu_target_mt": 0.3,
        "current_capacity_mw": 75.0,
        "pipeline_mw": 1200.0,
    },
    "Portugal": {
        "grid_ef_kg_co2_kwh": 0.12,
        "re_share_pct": 62.0,
        "bidding_zone": "PT",
        "repowereu_target_mt": 0.4,
        "current_capacity_mw": 35.0,
        "pipeline_mw": 2200.0,
    },
    "Italy": {
        "grid_ef_kg_co2_kwh": 0.29,
        "re_share_pct": 38.0,
        "bidding_zone": "IT-North",
        "repowereu_target_mt": 0.5,
        "current_capacity_mw": 50.0,
        "pipeline_mw": 1600.0,
    },
    "Belgium": {
        "grid_ef_kg_co2_kwh": 0.15,
        "re_share_pct": 33.0,
        "bidding_zone": "BE",
        "repowereu_target_mt": 0.2,
        "current_capacity_mw": 20.0,
        "pipeline_mw": 600.0,
    },
    "Sweden": {
        "grid_ef_kg_co2_kwh": 0.04,
        "re_share_pct": 66.0,
        "bidding_zone": "SE1",
        "repowereu_target_mt": 0.15,
        "current_capacity_mw": 15.0,
        "pipeline_mw": 400.0,
    },
    "Finland": {
        "grid_ef_kg_co2_kwh": 0.08,
        "re_share_pct": 55.0,
        "bidding_zone": "FI",
        "repowereu_target_mt": 0.1,
        "current_capacity_mw": 10.0,
        "pipeline_mw": 350.0,
    },
    "Austria": {
        "grid_ef_kg_co2_kwh": 0.08,
        "re_share_pct": 79.0,
        "bidding_zone": "DE-AT-LU",
        "repowereu_target_mt": 0.1,
        "current_capacity_mw": 12.0,
        "pipeline_mw": 300.0,
    },
    "Czech Republic": {
        "grid_ef_kg_co2_kwh": 0.46,
        "re_share_pct": 18.0,
        "bidding_zone": "CZ",
        "repowereu_target_mt": 0.1,
        "current_capacity_mw": 5.0,
        "pipeline_mw": 200.0,
    },
    "Romania": {
        "grid_ef_kg_co2_kwh": 0.28,
        "re_share_pct": 42.0,
        "bidding_zone": "RO",
        "repowereu_target_mt": 0.1,
        "current_capacity_mw": 8.0,
        "pipeline_mw": 400.0,
    },
    "Greece": {
        "grid_ef_kg_co2_kwh": 0.35,
        "re_share_pct": 45.0,
        "bidding_zone": "GR",
        "repowereu_target_mt": 0.15,
        "current_capacity_mw": 12.0,
        "pipeline_mw": 500.0,
    },
    "Hungary": {
        "grid_ef_kg_co2_kwh": 0.19,
        "re_share_pct": 20.0,
        "bidding_zone": "HU",
        "repowereu_target_mt": 0.05,
        "current_capacity_mw": 3.0,
        "pipeline_mw": 100.0,
    },
    "Morocco": {
        "grid_ef_kg_co2_kwh": 0.58,
        "re_share_pct": 38.0,
        "bidding_zone": "MA",
        "repowereu_target_mt": 0.0,
        "current_capacity_mw": 200.0,
        "pipeline_mw": 5000.0,
    },
    "Chile": {
        "grid_ef_kg_co2_kwh": 0.38,
        "re_share_pct": 55.0,
        "bidding_zone": "SIC",
        "repowereu_target_mt": 0.0,
        "current_capacity_mw": 50.0,
        "pipeline_mw": 3000.0,
    },
}

# ---------------------------------------------------------------------------
# Dedicated RE Emission Factors  (kgCO2eq/kWh — lifecycle, ISO 14040/14044)
# ---------------------------------------------------------------------------

DEDICATED_RE_FACTORS: dict[str, float] = {
    "wind_onshore":  0.009,
    "wind_offshore": 0.009,
    "solar_pv":      0.025,
    "solar_csp":     0.020,
    "hydro":         0.004,
    "nuclear":       0.012,
    "geothermal":    0.038,
    "biomass":       0.230,   # excluded from RFNBO eligibility per Art 2(36)
}

# ---------------------------------------------------------------------------
# Electrolyser Benchmarks
# ---------------------------------------------------------------------------

ELECTROLYSER_BENCHMARKS: dict[str, dict] = {
    "PEM": {
        "full_name": "Proton Exchange Membrane",
        "electricity_consumption_kwh_kgH2": 55.0,
        "efficiency_lhv_pct": 65.0,
        "capex_low_usd_kw": 900.0,
        "capex_high_usd_kw": 1500.0,
        "capex_2030_mid_usd_kw": 600.0,
        "capex_2050_mid_usd_kw": 300.0,
        "opex_pct_capex": 0.03,
        "stack_lifetime_hrs": 80_000,
        "stack_replacement_pct_capex": 0.15,
        "ramp_rate_pct_per_sec": 10.0,
        "cold_start_min": 5.0,
        "water_consumption_litre_kgH2": 9.0,
        "suitable_for_variable_re": True,
        "tech_readiness_level": 9,
        "notes": "Best suited for variable RE; fast dynamic response; dominant commercial technology.",
    },
    "ALK": {
        "full_name": "Alkaline Electrolysis",
        "electricity_consumption_kwh_kgH2": 60.0,
        "efficiency_lhv_pct": 60.0,
        "capex_low_usd_kw": 600.0,
        "capex_high_usd_kw": 1000.0,
        "capex_2030_mid_usd_kw": 450.0,
        "capex_2050_mid_usd_kw": 250.0,
        "opex_pct_capex": 0.02,
        "stack_lifetime_hrs": 100_000,
        "stack_replacement_pct_capex": 0.10,
        "ramp_rate_pct_per_sec": 0.5,
        "cold_start_min": 30.0,
        "water_consumption_litre_kgH2": 10.0,
        "suitable_for_variable_re": False,
        "tech_readiness_level": 9,
        "notes": "Lowest CAPEX; best for baseload/grid-connected; mature technology since 1920s.",
    },
    "SOEC": {
        "full_name": "Solid Oxide Electrolysis Cell",
        "electricity_consumption_kwh_kgH2": 45.0,
        "efficiency_lhv_pct": 75.0,
        "capex_low_usd_kw": 2000.0,
        "capex_high_usd_kw": 4000.0,
        "capex_2030_mid_usd_kw": 1200.0,
        "capex_2050_mid_usd_kw": 600.0,
        "opex_pct_capex": 0.04,
        "stack_lifetime_hrs": 40_000,
        "stack_replacement_pct_capex": 0.25,
        "ramp_rate_pct_per_sec": 0.2,
        "cold_start_min": 60.0,
        "water_consumption_litre_kgH2": 8.5,
        "suitable_for_variable_re": False,
        "tech_readiness_level": 7,
        "notes": "Highest electrical efficiency; requires 700-850°C operating temperature; synergy with industrial waste heat.",
    },
    "AEM": {
        "full_name": "Anion Exchange Membrane",
        "electricity_consumption_kwh_kgH2": 58.0,
        "efficiency_lhv_pct": 62.0,
        "capex_low_usd_kw": 700.0,
        "capex_high_usd_kw": 1200.0,
        "capex_2030_mid_usd_kw": 500.0,
        "capex_2050_mid_usd_kw": 280.0,
        "opex_pct_capex": 0.03,
        "stack_lifetime_hrs": 60_000,
        "stack_replacement_pct_capex": 0.12,
        "ramp_rate_pct_per_sec": 5.0,
        "cold_start_min": 10.0,
        "water_consumption_litre_kgH2": 9.5,
        "suitable_for_variable_re": True,
        "tech_readiness_level": 6,
        "notes": "Emerging technology combining PEM flexibility with ALK cost advantage; no platinum group metals.",
    },
}

# ---------------------------------------------------------------------------
# RFNBO 4 Criteria — Full Legal Descriptions
# ---------------------------------------------------------------------------

RFNBO_CRITERIA: dict[str, dict] = {
    "ghg_intensity": {
        "criterion_id": "C1",
        "name": "GHG Intensity Threshold",
        "legal_basis": "EU Delegated Regulation (EU) 2023/1184, Article 3",
        "description": (
            "The lifecycle GHG intensity of the RFNBO must not exceed 3.38 kgCO2eq/kgH2 "
            "(70% GHG reduction vs fossil fuel comparator of 94 gCO2eq/MJ). "
            "Calculated using the counterfactual / additionality marginal electricity method "
            "per ISO 14040/14044. Scope: well-to-gate electrolysis."
        ),
        "threshold_kg_co2_kgh2": 3.38,
        "fossil_comparator_g_co2_mj": 94.0,
        "reduction_vs_fossil_pct": 70.0,
        "calculation_method": "counterfactual marginal electricity; ISO 14040/14044",
        "scope": "well-to-gate (electrolysis + water treatment + compression)",
        "effective_date": "2023-06-20",
        "review_date": "2028-06-20",
    },
    "additionality": {
        "criterion_id": "C2",
        "name": "Additionality of Renewable Electricity",
        "legal_basis": "EU Delegated Regulation (EU) 2023/1185, Article 4",
        "description": (
            "Electricity used for RFNBO production must come from additional renewable sources. "
            "Three compliant routes: (a) new renewable capacity commissioned ≤36 months before "
            "the electrolyser; (b) grid electricity in a bidding zone where annual RE share >90%; "
            "or (c) a Power Purchase Agreement (PPA) with a dedicated newly commissioned RE asset."
        ),
        "routes": {
            "new_capacity": {
                "description": "Renewable installation ≤36 months older than electrolyser commissioning date",
                "max_age_months": 36,
                "documentation": "Construction permit + commissioning certificate",
            },
            "high_re_grid": {
                "description": "Bidding zone annual RE share >90% in the accounting period",
                "threshold_pct": 90.0,
                "documentation": "TSO certification or ENTSO-E statistics",
            },
            "dedicated_ppa": {
                "description": "Long-term PPA (≥10yr recommended) with a dedicated newly commissioned RE asset",
                "documentation": "PPA contract + RE commissioning certificate + GO tracking",
            },
        },
        "effective_date": "2023-06-20",
    },
    "temporal_correlation": {
        "criterion_id": "C3",
        "name": "Temporal Correlation",
        "legal_basis": "EU Delegated Regulation (EU) 2023/1185, Article 5",
        "description": (
            "Guarantees of Origin (GOs) for the renewable electricity consumed must match "
            "production within the same calendar month until 31 December 2029. "
            "From 1 January 2030, hourly matching is required (within the same clock hour)."
        ),
        "monthly_matching_until": "2029-12-31",
        "hourly_matching_from": "2030-01-01",
        "go_registry": "EECS (European Energy Certificate System) / AIB GO register",
        "go_standard": "CEN EN 16325 (Guarantees of Origin standard)",
        "effective_date": "2023-06-20",
    },
    "geographical_correlation": {
        "criterion_id": "C4",
        "name": "Geographical Correlation",
        "legal_basis": "EU Delegated Regulation (EU) 2023/1185, Article 6",
        "description": (
            "The renewable electricity source and the electrolyser must be in the same bidding zone. "
            "Adjacent bidding zones are permitted if no structural congestion exists on the "
            "interconnector (≥99% of hours congestion-free in the preceding calendar year)."
        ),
        "same_bidding_zone_compliant": True,
        "adjacent_zone_threshold_pct": 99.0,
        "congestion_assessment": "Based on ENTSO-E market coupling data (preceding calendar year)",
        "effective_date": "2023-06-20",
    },
}

# ---------------------------------------------------------------------------
# H2 CfD Framework Reference
# ---------------------------------------------------------------------------

H2_CFD_FRAMEWORK: dict[str, Any] = {
    "name": "EU H2 Bank / Hydrogen Contract for Difference",
    "legal_basis": (
        "EU Innovation Fund Regulation (EU) 2019/631 Art 10a; "
        "German AusH2 Regulation; State Aid SA.104606"
    ),
    "mechanism": (
        "Producer receives a guaranteed 'strike price' (EUR/kgH2) via competitive auction. "
        "If the prevailing hydrogen market price exceeds the strike price in a given period, "
        "the producer refunds the difference. Net public support = max(strike − market, 0) per kg H2 delivered."
    ),
    "eligibility_criteria": {
        "rfnbo_certified": True,
        "domestic_eu_production": True,
        "minimum_capacity_mw": 5.0,
        "minimum_contract_duration_yr": 10,
        "certification_required": ["REGreen", "TÜV SÜD", "DNV", "Bureau Veritas"],
        "commissioning_deadline": "2030-12-31",
    },
    "auction_parameters": {
        "support_duration_yr_min": 10,
        "support_duration_yr_max": 15,
        "reference_price_basis": "Natural gas parity (EUR/kgH2, weekly TTF index)",
        "natural_gas_parity_eur_kgH2": 2.5,
        "pilot_auction_budget_EUR": 800_000_000,
        "pilot_auction_year": 2023,
        "second_auction_budget_EUR": 3_000_000_000,
        "max_support_eur_kgH2": 4.0,
        "bidding_cap_eur_kgH2": 6.0,
    },
    "german_h2global_model": {
        "mechanism": "H2auftrag — split-contract: government buys green H2 internationally at high price, "
                     "sells domestically at market price; spread covered by public budget.",
        "partner_countries": ["Chile", "Morocco", "Namibia", "United Arab Emirates", "Australia", "South Africa"],
        "volumes_planned_tpa": 50_000,
        "funding_EUR": 900_000_000,
    },
    "certification_recognition": {
        "REGreen": {
            "issuer": "CertifHy / European Commission",
            "recognition_level": "Full — primary EU RFNBO label",
            "scope": "Green H2 + RFNBO label + Low-Carbon H2",
            "mutual_recognition": ["TÜV SÜD", "DNV"],
            "fee_eur_per_tonne": 0.50,
        },
        "TÜV SÜD": {
            "issuer": "TÜV SÜD AG (Germany)",
            "recognition_level": "Full",
            "scope": "Green H2 + RFNBO + Low-Carbon H2 + Blue H2",
            "mutual_recognition": ["REGreen", "Bureau Veritas"],
            "fee_eur_per_tonne": 0.80,
        },
        "DNV": {
            "issuer": "DNV AS (Norway)",
            "recognition_level": "Full",
            "scope": "Green H2 + RFNBO + Blue H2 + offshore production",
            "mutual_recognition": ["REGreen", "TÜV SÜD"],
            "fee_eur_per_tonne": 0.75,
        },
        "Bureau Veritas": {
            "issuer": "Bureau Veritas SA (France)",
            "recognition_level": "Full",
            "scope": "Green H2 + RFNBO + supply chain traceability",
            "mutual_recognition": ["TÜV SÜD"],
            "fee_eur_per_tonne": 0.70,
        },
        "IRENA GO": {
            "issuer": "IRENA (International Renewable Energy Agency)",
            "recognition_level": "Partial — not yet EU-recognised for RFNBO compliance",
            "scope": "Renewable energy attribute certificates (global)",
            "mutual_recognition": [],
            "fee_eur_per_tonne": None,
        },
    },
}

# ---------------------------------------------------------------------------
# REPowerEU National Targets
# ---------------------------------------------------------------------------

REPOWEREU_TARGETS: dict[str, Any] = {
    "eu_strategy_headline": {
        "domestic_production_mt_2030": 10.0,
        "import_target_mt_2030": 10.0,
        "total_target_mt_2030": 20.0,
        "electrolysis_capacity_gw_2030": 40.0,
        "offshore_wind_linked_gw": 10.0,
        "investment_eur_bn": 335.0,
        "legal_basis": "REPowerEU Plan COM(2022) 230 + EU Hydrogen Strategy COM(2020) 301 final",
        "update": "2030 target upgraded from 5 Mt (2020 strategy) to 10 Mt domestic + 10 Mt imports",
        "2024_installed_gw": 0.5,
        "gap_to_target_gw": 39.5,
    },
    "country_targets": {
        c: {
            "repowereu_target_mt_2030": v["repowereu_target_mt"],
            "current_capacity_mw": v["current_capacity_mw"],
            "pipeline_projects_mw": v["pipeline_mw"],
            "re_share_pct": v["re_share_pct"],
            "grid_ef_kg_co2_kwh": v["grid_ef_kg_co2_kwh"],
        }
        for c, v in COUNTRY_GRID_FACTORS.items()
    },
    "import_corridors": [
        {
            "corridor": "H2Med — Iberian Peninsula → Central Europe",
            "capacity_tpa_2030": 2_000_000,
            "infrastructure": "Repurposed gas pipeline + new H2 backbone",
            "status": "Under development; EU-PCI designation",
        },
        {
            "corridor": "North Africa → Southern Europe (via Italy/Greece)",
            "capacity_tpa_2030": 1_500_000,
            "infrastructure": "New offshore pipeline + ammonia terminals",
            "status": "Feasibility studies ongoing",
        },
        {
            "corridor": "Baltic → Scandinavia → North Sea Green H2 Hub",
            "capacity_tpa_2030": 800_000,
            "infrastructure": "Baltic Sea offshore wind + dedicated H2 pipeline",
            "status": "Planning phase",
        },
        {
            "corridor": "Ukraine / Eastern Europe → EU (EastMed H2 corridor)",
            "capacity_tpa_2030": 500_000,
            "infrastructure": "Existing gas network repurposing",
            "status": "War-dependent; long-term planning",
        },
    ],
    "hydrogen_valleys": [
        {"name": "Rotterdam H2 Hub", "country": "Netherlands", "capacity_mw": 500},
        {"name": "Hamburg H2 Hub", "country": "Germany", "capacity_mw": 400},
        {"name": "Hydrogen Valleys Catalonia", "country": "Spain", "capacity_mw": 350},
        {"name": "Humberside H2 Cluster", "country": "United Kingdom", "capacity_mw": 300},
    ],
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RFNBO_GHG_THRESHOLD_KG_CO2_KGH2: float = 3.38
WATER_TREATMENT_KG_CO2_KGH2: float = 0.05
COMPRESSION_KG_CO2_KGH2: float = 0.15
HIGH_RE_GRID_THRESHOLD_PCT: float = 90.0
ADDITIONALITY_MAX_AGE_MONTHS: int = 36
H2_LHV_KWH_PER_KG: float = 33.33
H2_LHV_MJ_PER_KG: float = 120.0
EUR_USD_RATE: float = 0.92


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _get_electricity_ef(electricity_source: str, country: str) -> tuple[float, str]:
    """Return (kgCO2eq/kWh, description) for the given electricity source."""
    src = electricity_source.lower().replace(" ", "_").replace("-", "_")
    country_data = COUNTRY_GRID_FACTORS.get(country, {})

    if src in ("grid", "grid_average", "national_grid", "grid_mix"):
        ef = country_data.get("grid_ef_kg_co2_kwh", 0.35)
        return ef, f"National grid average — {country} ({ef} kgCO2/kWh)"

    for re_key, re_ef in DEDICATED_RE_FACTORS.items():
        if re_key in src:
            return re_ef, f"Dedicated RE: {re_key} ({re_ef} kgCO2/kWh)"

    if "wind" in src:
        ef = DEDICATED_RE_FACTORS["wind_onshore"]
        return ef, f"Dedicated RE: wind_onshore (assumed) — {ef} kgCO2/kWh"
    if "solar" in src or "pv" in src:
        ef = DEDICATED_RE_FACTORS["solar_pv"]
        return ef, f"Dedicated RE: solar_pv (assumed) — {ef} kgCO2/kWh"
    if "hydro" in src:
        ef = DEDICATED_RE_FACTORS["hydro"]
        return ef, f"Dedicated RE: hydro — {ef} kgCO2/kWh"
    if "nuclear" in src:
        ef = DEDICATED_RE_FACTORS["nuclear"]
        return ef, f"Nuclear (low-carbon, not classified as RE) — {ef} kgCO2/kWh"
    if "ppa" in src:
        ef = DEDICATED_RE_FACTORS["wind_onshore"]
        return ef, f"PPA (wind onshore assumed default) — {ef} kgCO2/kWh"

    # Fallback
    ef = country_data.get("grid_ef_kg_co2_kwh", 0.35)
    return ef, f"Unrecognised source '{electricity_source}'; fallback to grid — {ef} kgCO2/kWh"


def _calculate_ghg_intensity(
    electrolyser_type: str,
    electricity_ef_kg_co2_kwh: float,
    include_compression: bool = True,
    include_water_treatment: bool = True,
) -> dict[str, Any]:
    """Well-to-gate GHG intensity per ISO 14040/14044 approach (kgCO2eq/kgH2)."""
    bench = ELECTROLYSER_BENCHMARKS.get(electrolyser_type.upper(), ELECTROLYSER_BENCHMARKS["PEM"])
    kwh_per_kgh2: float = bench["electricity_consumption_kwh_kgH2"]

    electrolysis_ghg = kwh_per_kgh2 * electricity_ef_kg_co2_kwh
    water_ghg = WATER_TREATMENT_KG_CO2_KGH2 if include_water_treatment else 0.0
    compression_ghg = COMPRESSION_KG_CO2_KGH2 if include_compression else 0.0
    total_ghg = electrolysis_ghg + water_ghg + compression_ghg

    reduction_vs_fossil_pct = (1.0 - total_ghg / (94.0 * H2_LHV_MJ_PER_KG / 1000.0)) * 100.0

    return {
        "electrolysis_kg_co2_kgh2": round(electrolysis_ghg, 4),
        "water_treatment_kg_co2_kgh2": round(water_ghg, 4),
        "compression_kg_co2_kgh2": round(compression_ghg, 4),
        "total_ghg_intensity_kg_co2_kgh2": round(total_ghg, 4),
        "rfnbo_threshold_kg_co2_kgh2": RFNBO_GHG_THRESHOLD_KG_CO2_KGH2,
        "below_threshold": total_ghg < RFNBO_GHG_THRESHOLD_KG_CO2_KGH2,
        "reduction_vs_fossil_pct": round(reduction_vs_fossil_pct, 1),
        "kwh_per_kgh2": kwh_per_kgh2,
        "electricity_ef_kg_co2_kwh": round(electricity_ef_kg_co2_kwh, 5),
    }


def _assess_additionality(
    electricity_source: str,
    country: str,
    commissioning_year: int,
    re_installation_year: int | None,
    has_ppa: bool,
    ppa_dedicated_new_asset: bool,
) -> dict[str, Any]:
    """Score RFNBO additionality criterion (2023/1185 Art 4). Returns score 0-1 + compliance flag."""
    country_data = COUNTRY_GRID_FACTORS.get(country, {})
    re_share = country_data.get("re_share_pct", 0.0)
    src = electricity_source.lower()

    # Route B — High RE grid (>90%)
    if re_share >= HIGH_RE_GRID_THRESHOLD_PCT:
        return {
            "route": "high_re_grid",
            "score": 1.0,
            "compliant": True,
            "re_share_pct": re_share,
            "detail": (
                f"{country} grid RE share {re_share}% ≥ 90% threshold (Art 4(1)(b)). "
                "Additionality satisfied."
            ),
        }

    # Route C — Dedicated PPA with new RE asset
    if has_ppa and ppa_dedicated_new_asset:
        return {
            "route": "dedicated_ppa",
            "score": 1.0,
            "compliant": True,
            "re_share_pct": re_share,
            "detail": "Long-term PPA with newly commissioned dedicated RE asset (Art 4(1)(c)). Additionality satisfied.",
        }

    # Route A — New renewable capacity ≤36 months before electrolyser
    if re_installation_year is not None:
        age_months = (commissioning_year - re_installation_year) * 12
        if age_months <= ADDITIONALITY_MAX_AGE_MONTHS:
            return {
                "route": "new_capacity",
                "score": 1.0,
                "compliant": True,
                "age_months": age_months,
                "re_share_pct": re_share,
                "detail": (
                    f"RE installation commissioned {age_months} months before electrolyser "
                    f"(≤36 months threshold, Art 4(1)(a)). Additionality satisfied."
                ),
            }
        else:
            penalty = min((age_months - ADDITIONALITY_MAX_AGE_MONTHS) / 120.0, 1.0)
            score = round(max(0.0, 1.0 - penalty), 3)
            return {
                "route": "new_capacity_exceeded",
                "score": score,
                "compliant": False,
                "age_months": age_months,
                "re_share_pct": re_share,
                "detail": (
                    f"RE installation {age_months} months before electrolyser exceeds 36-month "
                    "threshold (Art 4(1)(a)). Additionality NOT met via this route. "
                    "Consider PPA arrangement or high-RE-share grid zone."
                ),
            }

    # Grid with RE share but below 90% threshold
    if any(g in src for g in ("grid", "national_grid", "grid_average")):
        partial_score = round(min(re_share / HIGH_RE_GRID_THRESHOLD_PCT, 1.0) * 0.5, 3)
        return {
            "route": "grid_partial",
            "score": partial_score,
            "compliant": False,
            "re_share_pct": re_share,
            "detail": (
                f"{country} grid RE share {re_share}% < 90% threshold. "
                "Additionality NOT satisfied via grid route. Explore new capacity or PPA."
            ),
        }

    # Dedicated RE source stated but year/PPA not provided
    if any(k in src for k in ["wind", "solar", "hydro", "geothermal"]):
        return {
            "route": "dedicated_re_unverified",
            "score": 0.7,
            "compliant": False,
            "re_share_pct": re_share,
            "detail": (
                "Dedicated RE source identified but commissioning year data absent. "
                "Provide re_installation_year to verify ≤36-month rule, or confirm PPA structure."
            ),
        }

    return {
        "route": "unknown",
        "score": 0.0,
        "compliant": False,
        "re_share_pct": re_share,
        "detail": "Insufficient data for additionality assessment. Provide electricity source, year, or PPA details.",
    }


def _assess_temporal_correlation(accounting_year: int, matching_granularity: str) -> dict[str, Any]:
    """Score temporal correlation criterion (2023/1185 Art 5)."""
    gran = matching_granularity.lower().strip()
    required = "hourly" if accounting_year >= 2030 else "monthly"

    if gran == "hourly":
        return {
            "required_granularity": required,
            "provided_granularity": "hourly",
            "score": 1.0,
            "compliant": True,
            "detail": f"Hourly GO matching meets {'2030+ mandatory' if accounting_year >= 2030 else 'pre-2030'} requirement.",
        }
    if gran == "monthly":
        if accounting_year < 2030:
            return {
                "required_granularity": required,
                "provided_granularity": "monthly",
                "score": 1.0,
                "compliant": True,
                "detail": f"Monthly GO matching meets pre-2030 temporal correlation requirement (year {accounting_year}).",
            }
        return {
            "required_granularity": required,
            "provided_granularity": "monthly",
            "score": 0.0,
            "compliant": False,
            "detail": f"Monthly matching insufficient from 2030 onwards (Art 5(2)). Hourly GO matching required. Year: {accounting_year}.",
        }
    if gran in ("annual", "yearly"):
        return {
            "required_granularity": required,
            "provided_granularity": "annual",
            "score": 0.3,
            "compliant": False,
            "detail": "Annual GO matching does not satisfy temporal correlation. Monthly (pre-2030) or hourly (2030+) required.",
        }
    return {
        "required_granularity": required,
        "provided_granularity": gran,
        "score": 0.0,
        "compliant": False,
        "detail": f"Unrecognised matching granularity '{matching_granularity}'. Must be: hourly / monthly.",
    }


def _assess_geographical_correlation(
    country: str,
    re_location_country: str,
    same_bidding_zone: bool,
    adjacent_zone_congestion_free_pct: float | None,
) -> dict[str, Any]:
    """Score geographical correlation criterion (2023/1185 Art 6)."""
    elec_zone = COUNTRY_GRID_FACTORS.get(country, {}).get("bidding_zone", "UNKNOWN")
    re_zone = COUNTRY_GRID_FACTORS.get(re_location_country, {}).get("bidding_zone", "UNKNOWN")

    if same_bidding_zone or elec_zone == re_zone:
        return {
            "electrolyser_bidding_zone": elec_zone,
            "re_bidding_zone": re_zone,
            "score": 1.0,
            "compliant": True,
            "detail": f"Same bidding zone ({elec_zone}). Geographical correlation fully satisfied (Art 6(1)).",
        }

    congestion_free = adjacent_zone_congestion_free_pct or 0.0
    threshold = RFNBO_CRITERIA["geographical_correlation"]["adjacent_zone_threshold_pct"]

    if congestion_free >= threshold:
        return {
            "electrolyser_bidding_zone": elec_zone,
            "re_bidding_zone": re_zone,
            "score": 1.0,
            "compliant": True,
            "congestion_free_pct": congestion_free,
            "detail": (
                f"Adjacent zones ({elec_zone}/{re_zone}). Interconnector congestion-free "
                f"{congestion_free}% ≥ {threshold}% threshold (Art 6(2)). Compliant."
            ),
        }
    if congestion_free > 0.0:
        score = round((congestion_free / threshold) * 0.8, 3)
        return {
            "electrolyser_bidding_zone": elec_zone,
            "re_bidding_zone": re_zone,
            "score": score,
            "compliant": False,
            "congestion_free_pct": congestion_free,
            "detail": (
                f"Adjacent zones ({elec_zone}/{re_zone}) but congestion-free only "
                f"{congestion_free}% < {threshold}% threshold. NOT compliant (Art 6(2))."
            ),
        }

    return {
        "electrolyser_bidding_zone": elec_zone,
        "re_bidding_zone": re_zone,
        "score": 0.0,
        "compliant": False,
        "detail": (
            f"Different bidding zones ({elec_zone} vs {re_zone}). "
            "No congestion data provided. Geographical correlation cannot be confirmed."
        ),
    }


# ---------------------------------------------------------------------------
# Public API Functions
# ---------------------------------------------------------------------------


def calculate_rfnbo_compliance(
    electricity_source: str,
    country: str,
    electrolyser_type: str = "PEM",
    commissioning_year: int = 2024,
    re_installation_year: int | None = None,
    has_ppa: bool = False,
    ppa_dedicated_new_asset: bool = False,
    accounting_year: int = 2025,
    matching_granularity: str = "monthly",
    re_location_country: str | None = None,
    same_bidding_zone: bool = True,
    adjacent_zone_congestion_free_pct: float | None = None,
    include_compression: bool = True,
    include_water_treatment: bool = True,
) -> dict[str, Any]:
    """
    Assess RFNBO compliance against all 4 EU criteria (2023/1184 + 2023/1185).

    Returns individual criterion scores (0-1), composite score, and RFNBO eligibility flag.
    RFNBO eligible only when ALL 4 criteria are compliant.
    """
    re_country = re_location_country or country
    et = electrolyser_type.upper()

    # Criterion 1 — GHG Intensity
    ef, ef_desc = _get_electricity_ef(electricity_source, country)
    ghg = _calculate_ghg_intensity(et, ef, include_compression, include_water_treatment)
    c1_compliant = ghg["below_threshold"]
    if c1_compliant:
        c1_score = 1.0
    else:
        excess = ghg["total_ghg_intensity_kg_co2_kgh2"] - RFNBO_GHG_THRESHOLD_KG_CO2_KGH2
        c1_score = round(max(0.0, 1.0 - excess / RFNBO_GHG_THRESHOLD_KG_CO2_KGH2), 3)

    # Criterion 2 — Additionality
    c2 = _assess_additionality(
        electricity_source, country, commissioning_year,
        re_installation_year, has_ppa, ppa_dedicated_new_asset,
    )

    # Criterion 3 — Temporal Correlation
    c3 = _assess_temporal_correlation(accounting_year, matching_granularity)

    # Criterion 4 — Geographical Correlation
    c4 = _assess_geographical_correlation(
        country, re_country, same_bidding_zone, adjacent_zone_congestion_free_pct,
    )

    all_compliant = c1_compliant and c2["compliant"] and c3["compliant"] and c4["compliant"]
    composite = (c1_score + c2["score"] + c3["score"] + c4["score"]) / 4.0

    eligible_certs = [
        s for s, d in H2_CFD_FRAMEWORK["certification_recognition"].items()
        if d["recognition_level"].startswith("Full")
    ]

    return {
        "rfnbo_eligible": all_compliant,
        "composite_score": round(composite, 4),
        "criteria": {
            "C1_ghg_intensity": {
                "name": "GHG Intensity < 3.38 kgCO2eq/kgH2",
                "score": c1_score,
                "compliant": c1_compliant,
                "electricity_ef_description": ef_desc,
                "ghg_detail": ghg,
            },
            "C2_additionality": {
                "name": "Additionality of Renewable Electricity",
                **c2,
            },
            "C3_temporal_correlation": {
                "name": "Temporal Correlation (GO matching)",
                **c3,
            },
            "C4_geographical_correlation": {
                "name": "Geographical Correlation (bidding zone)",
                **c4,
            },
        },
        "summary": (
            "RFNBO eligible — all 4 criteria satisfied per EU 2023/1184 + 2023/1185."
            if all_compliant
            else "RFNBO NOT eligible — one or more criteria not met. Review individual criteria."
        ),
        "eligible_certification_bodies": eligible_certs if all_compliant else [],
        "inputs": {
            "electricity_source": electricity_source,
            "country": country,
            "electrolyser_type": et,
            "commissioning_year": commissioning_year,
            "accounting_year": accounting_year,
            "matching_granularity": matching_granularity,
        },
    }


def calculate_lcoh(
    electrolyser_type: str = "PEM",
    country: str = "Germany",
    capacity_mw: float = 100.0,
    capex_usd_kw: float | None = None,
    capacity_factor: float = 0.45,
    discount_rate: float = 0.08,
    lifetime_yr: int = 20,
    electricity_price_usd_mwh: float | None = None,
    opex_pct_capex: float | None = None,
    projection_year: int = 2024,
) -> dict[str, Any]:
    """
    Calculate Levelised Cost of Hydrogen (USD/kgH2) per IEA Global Hydrogen Review 2023.

    LCOH = (CAPEX × CRF + OPEX_annual + stack_replacement_annual) / annual_H2_kg + electricity_cost/kgH2
    CRF  = r / (1 − (1+r)^(−n))
    """
    et = electrolyser_type.upper()
    bench = ELECTROLYSER_BENCHMARKS.get(et, ELECTROLYSER_BENCHMARKS["PEM"])

    # CAPEX — IEA trajectory
    if capex_usd_kw is None:
        mid_2024 = (bench["capex_low_usd_kw"] + bench["capex_high_usd_kw"]) / 2.0
        if projection_year <= 2024:
            capex_usd_kw = mid_2024
        elif projection_year <= 2030:
            frac = (projection_year - 2024) / 6.0
            capex_usd_kw = mid_2024 + frac * (bench["capex_2030_mid_usd_kw"] - mid_2024)
        else:
            frac = min((projection_year - 2030) / 20.0, 1.0)
            capex_usd_kw = bench["capex_2030_mid_usd_kw"] + frac * (
                bench["capex_2050_mid_usd_kw"] - bench["capex_2030_mid_usd_kw"]
            )

    opex_frac = opex_pct_capex if opex_pct_capex is not None else bench["opex_pct_capex"]
    kwh_per_kgh2: float = bench["electricity_consumption_kwh_kgH2"]
    efficiency_lhv: float = bench["efficiency_lhv_pct"] / 100.0
    stack_lifetime_hr: float = float(bench["stack_lifetime_hrs"])

    # Capital cost
    capex_total_usd = capex_usd_kw * capacity_mw * 1000.0

    # CRF
    crf = (discount_rate / (1.0 - (1.0 + discount_rate) ** (-lifetime_yr))
           if discount_rate > 0 else 1.0 / lifetime_yr)

    # Annual figures
    operating_hours_yr = capacity_factor * 8760.0
    annual_energy_kwh = capacity_mw * 1000.0 * operating_hours_yr
    # H2 production: electrical energy × LHV efficiency / LHV energy content
    annual_h2_kg = annual_energy_kwh * efficiency_lhv / H2_LHV_KWH_PER_KG

    # Stack replacement — annualised
    replacements_over_life = (lifetime_yr * operating_hours_yr) / stack_lifetime_hr
    annual_stack_usd = (
        bench["stack_replacement_pct_capex"] * capex_usd_kw * capacity_mw * 1000.0
        * replacements_over_life / lifetime_yr
    )

    # Electricity price default (IEA dedicated RE PPA trajectory)
    if electricity_price_usd_mwh is None:
        if projection_year <= 2024:
            electricity_price_usd_mwh = 45.0
        elif projection_year <= 2030:
            electricity_price_usd_mwh = 38.0
        else:
            electricity_price_usd_mwh = 28.0

    # Cost components (USD/kgH2)
    lcoh_capex = (capex_total_usd * crf) / annual_h2_kg
    lcoh_opex = (capex_total_usd * opex_frac) / annual_h2_kg
    lcoh_stack = annual_stack_usd / annual_h2_kg
    lcoh_electricity = (annual_energy_kwh / 1000.0) * electricity_price_usd_mwh / annual_h2_kg
    lcoh_total = lcoh_capex + lcoh_opex + lcoh_stack + lcoh_electricity

    # Benchmarks
    ng_parity_usd_kgh2 = 8.0 * H2_LHV_MJ_PER_KG / 1000.0  # USD 8/GJ TTF → USD/kgH2

    return {
        "electrolyser_type": et,
        "country": country,
        "capacity_mw": capacity_mw,
        "projection_year": projection_year,
        "inputs": {
            "capex_usd_kw": round(capex_usd_kw, 2),
            "capacity_factor": capacity_factor,
            "discount_rate": discount_rate,
            "lifetime_yr": lifetime_yr,
            "electricity_price_usd_mwh": round(electricity_price_usd_mwh, 2),
            "opex_pct_capex": opex_frac,
        },
        "annual_production": {
            "operating_hours_yr": round(operating_hours_yr, 0),
            "annual_energy_kwh": round(annual_energy_kwh, 0),
            "annual_h2_kg": round(annual_h2_kg, 0),
            "annual_h2_tonne": round(annual_h2_kg / 1000.0, 1),
        },
        "lcoh_usd_kgh2": {
            "capex_component": round(lcoh_capex, 4),
            "opex_component": round(lcoh_opex, 4),
            "stack_replacement_component": round(lcoh_stack, 4),
            "electricity_component": round(lcoh_electricity, 4),
            "total_lcoh": round(lcoh_total, 4),
            "total_lcoh_eur_kgh2": round(lcoh_total * EUR_USD_RATE, 4),
        },
        "economics": {
            "crf": round(crf, 6),
            "capex_total_usd_mn": round(capex_total_usd / 1e6, 2),
            "annual_capex_usd_mn": round(capex_total_usd * crf / 1e6, 3),
            "annual_opex_usd_mn": round(capex_total_usd * opex_frac / 1e6, 3),
            "annual_electricity_cost_usd_mn": round(
                (annual_energy_kwh / 1000.0) * electricity_price_usd_mwh / 1e6, 3
            ),
        },
        "benchmarks": {
            "natural_gas_parity_usd_kgh2": round(ng_parity_usd_kgh2, 3),
            "h2cfd_reference_price_eur_kgh2": H2_CFD_FRAMEWORK["auction_parameters"]["natural_gas_parity_eur_kgH2"],
            "iea_green_h2_range_2024_usd": "3.0 – 6.0",
            "iea_green_h2_range_2030_usd": "2.0 – 4.0",
            "iea_green_h2_range_2050_usd": "1.0 – 2.0",
            "premium_vs_ng_parity_usd_kgh2": round(lcoh_total - ng_parity_usd_kgh2, 3),
            "h2cfd_eligible": lcoh_total > ng_parity_usd_kgh2,
        },
    }


def assess_green_hydrogen(
    facility_name: str,
    country: str,
    production_capacity_mw: float,
    electrolyser_type: str = "PEM",
    electricity_source: str = "wind_onshore",
    commissioning_year: int = 2024,
    re_installation_year: int | None = None,
    has_ppa: bool = False,
    ppa_dedicated_new_asset: bool = False,
    accounting_year: int = 2025,
    matching_granularity: str = "monthly",
    re_location_country: str | None = None,
    same_bidding_zone: bool = True,
    adjacent_zone_congestion_free_pct: float | None = None,
    capex_usd_kw: float | None = None,
    capacity_factor: float = 0.45,
    discount_rate: float = 0.08,
    lifetime_yr: int = 20,
    electricity_price_usd_mwh: float | None = None,
    certifications: list[str] | None = None,
    projection_year: int = 2024,
) -> dict[str, Any]:
    """
    Full facility-level green hydrogen assessment.

    Combines:
    - RFNBO compliance (all 4 criteria, EU 2023/1184 + 2023/1185)
    - GHG intensity (ISO 14040/14044 lifecycle)
    - LCOH economics (IEA methodology)
    - H2 CfD eligibility + indicative support
    - Certification gap analysis
    - REPowerEU country context
    """
    rfnbo = calculate_rfnbo_compliance(
        electricity_source=electricity_source,
        country=country,
        electrolyser_type=electrolyser_type,
        commissioning_year=commissioning_year,
        re_installation_year=re_installation_year,
        has_ppa=has_ppa,
        ppa_dedicated_new_asset=ppa_dedicated_new_asset,
        accounting_year=accounting_year,
        matching_granularity=matching_granularity,
        re_location_country=re_location_country,
        same_bidding_zone=same_bidding_zone,
        adjacent_zone_congestion_free_pct=adjacent_zone_congestion_free_pct,
    )

    lcoh = calculate_lcoh(
        electrolyser_type=electrolyser_type,
        country=country,
        capacity_mw=production_capacity_mw,
        capex_usd_kw=capex_usd_kw,
        capacity_factor=capacity_factor,
        discount_rate=discount_rate,
        lifetime_yr=lifetime_yr,
        electricity_price_usd_mwh=electricity_price_usd_mwh,
        projection_year=projection_year,
    )

    # H2 CfD support estimate
    cfd_eligible = rfnbo["rfnbo_eligible"]
    cfd_support_eur_kgh2: float | None = None
    if cfd_eligible:
        lcoh_eur = lcoh["lcoh_usd_kgh2"]["total_lcoh_eur_kgh2"]
        ng_parity_eur = H2_CFD_FRAMEWORK["auction_parameters"]["natural_gas_parity_eur_kgH2"]
        max_support = H2_CFD_FRAMEWORK["auction_parameters"]["max_support_eur_kgH2"]
        cfd_support_eur_kgh2 = round(max(0.0, min(lcoh_eur - ng_parity_eur, max_support)), 3)

    # Certification gap
    certs_held = certifications or []
    recognised = [
        s for s, d in H2_CFD_FRAMEWORK["certification_recognition"].items()
        if d["recognition_level"].startswith("Full")
    ]
    certs_missing = [c for c in recognised if c not in certs_held]
    is_certified = any(c in certs_held for c in recognised)

    # REPowerEU context
    country_data = COUNTRY_GRID_FACTORS.get(country, {})
    repowereu_target = country_data.get("repowereu_target_mt", 0.0)
    annual_h2_t = lcoh["annual_production"]["annual_h2_tonne"]

    # Rating
    score = rfnbo["composite_score"]
    if score >= 0.90:
        rating, rating_label = "A", "Fully Compliant Green H2 / RFNBO Eligible"
    elif score >= 0.70:
        rating, rating_label = "B", "Substantially Compliant (minor gaps)"
    elif score >= 0.50:
        rating, rating_label = "C", "Partially Compliant (material gaps)"
    else:
        rating, rating_label = "D", "Non-Compliant / Insufficient Data"

    return {
        "facility_name": facility_name,
        "country": country,
        "electrolyser_type": electrolyser_type.upper(),
        "production_capacity_mw": production_capacity_mw,
        "electricity_source": electricity_source,
        "overall_rating": f"{rating} — {rating_label}",
        "rfnbo_assessment": rfnbo,
        "lcoh_assessment": lcoh,
        "h2cfd": {
            "eligible": cfd_eligible,
            "indicative_support_eur_kgh2": cfd_support_eur_kgh2,
            "support_duration_yr": H2_CFD_FRAMEWORK["auction_parameters"]["support_duration_yr_max"],
            "mechanism_description": H2_CFD_FRAMEWORK["mechanism"],
            "legal_basis": H2_CFD_FRAMEWORK["legal_basis"],
        },
        "certification": {
            "certifications_held": certs_held,
            "recognised_eu_certs": recognised,
            "certifications_missing": certs_missing,
            "is_certified_by_recognised_body": is_certified,
            "recommendation": (
                "Pursue REGreen or TÜV SÜD certification to unlock H2 CfD and EU H2 Bank access."
                if not is_certified and cfd_eligible else
                ("Maintain certification renewal cycle." if is_certified else
                 "Resolve RFNBO compliance gaps before pursuing certification.")
            ),
        },
        "repowereu_context": {
            "country_target_mt_2030": repowereu_target,
            "country_current_capacity_mw": country_data.get("current_capacity_mw", 0.0),
            "country_pipeline_mw": country_data.get("pipeline_mw", 0.0),
            "facility_annual_h2_tonne": annual_h2_t,
            "facility_contribution_pct_target": (
                round(annual_h2_t / (repowereu_target * 1e6) * 100.0, 4)
                if repowereu_target > 0 else None
            ),
        },
        "electrolyser_profile": ELECTROLYSER_BENCHMARKS.get(electrolyser_type.upper(), {}),
    }


def get_h2_benchmarks() -> dict[str, Any]:
    """Return consolidated benchmark and reference data for green hydrogen analysis."""
    return {
        "electrolyser_benchmarks": ELECTROLYSER_BENCHMARKS,
        "country_grid_factors": COUNTRY_GRID_FACTORS,
        "dedicated_re_factors": DEDICATED_RE_FACTORS,
        "rfnbo_criteria": RFNBO_CRITERIA,
        "h2cfd_framework": H2_CFD_FRAMEWORK,
        "repowereu_targets": REPOWEREU_TARGETS,
        "iea_cost_trajectory": {
            "2024": {"low_usd_kgh2": 3.0, "high_usd_kgh2": 6.0, "median_usd_kgh2": 4.5},
            "2030": {"low_usd_kgh2": 2.0, "high_usd_kgh2": 4.0, "median_usd_kgh2": 3.0},
            "2050": {"low_usd_kgh2": 1.0, "high_usd_kgh2": 2.0, "median_usd_kgh2": 1.5},
        },
        "ghg_thresholds": {
            "rfnbo_threshold_kg_co2_kgh2": RFNBO_GHG_THRESHOLD_KG_CO2_KGH2,
            "fossil_fuel_comparator_g_co2_mj": 94.0,
            "reduction_required_pct": 70.0,
            "water_treatment_kg_co2_kgh2": WATER_TREATMENT_KG_CO2_KGH2,
            "compression_kg_co2_kgh2": COMPRESSION_KG_CO2_KGH2,
        },
        "h2_physical_properties": {
            "lhv_kwh_per_kg": H2_LHV_KWH_PER_KG,
            "hhv_kwh_per_kg": 39.39,
            "lhv_mj_per_kg": H2_LHV_MJ_PER_KG,
            "density_kg_m3_at_350bar": 23.5,
            "density_kg_m3_at_700bar": 40.2,
            "density_lh2_kg_m3": 70.8,
            "boiling_point_celsius": -252.9,
        },
    }
