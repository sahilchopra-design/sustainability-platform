"""
Factor Overlay Engine
=====================
Cross-cutting overlay engine adding ESG, geopolitical, and technology
risk dimensions to every analytics module on the platform.

Data Flow
---------
  Existing Module Output  ──►  Factor Overlay Engine  ──►  Enhanced Output
                                 │  ESG factors
                                 │  Geopolitical factors
                                 │  Technology factors

Key References
--------------
  - MSCI ESG Ratings Methodology (2024)
  - World Bank Worldwide Governance Indicators (WGI)
  - OECD Country Risk Classifications (CRC, Jan 2024)
  - Verisk Maplecroft Climate Change Vulnerability Index
  - Global Innovation Index 2024 (WIPO)
  - EU Sustainable Finance Taxonomy – Delegated Act 2023
  - NGFS Phase IV scenario variables
  - IPCC AR6 WG2 regional impact tables
  - BIS/Basel stress-testing guidance (2023)
  - PRI Inevitable Policy Response 2024
  - IEA World Energy Outlook 2024
  - FAO State of Food & Agriculture 2024

Input Parameters (per overlay call)
------------------------------------
  entity_id       : str   – unique entity / counterparty / asset identifier
  country_code    : str   – ISO-3166-1 alpha-2 (e.g. "DE", "CN")
  sector_nace     : str   – NACE Rev 2 section letter (A–U)
  base_metrics    : dict  – module-specific metrics to overlay
  scenario        : str   – optional NGFS scenario key
  as_of_date      : str   – valuation / assessment date  (YYYY-MM-DD)

Transformations
---------------
  1. Look up ESG factor scores for (sector, country, scenario).
  2. Look up geopolitical factor scores for (country, scenario).
  3. Look up technology factor scores for (sector, country).
  4. Apply multiplicative / additive adjustments to base_metrics.
  5. Return enhanced metrics + factor decomposition audit trail.

Output Results
--------------
  enhanced_metrics : dict   – base metrics with factor adjustments applied
  factor_breakdown : dict   – per-factor contribution (ESG / Geo / Tech)
  audit_trail      : list   – step-by-step calculation log
  confidence       : float  – 0-1 weighted confidence in overlay quality
  warnings         : list   – data-quality or coverage warnings

Stakeholder Insights
--------------------
  Bank Credit       : Climate-adjusted ECL with country & tech risk overlays
  Bank Treasury     : Forward-looking ALM with ESG / macro overlays
  Bank Compliance   : Multi-jurisdiction regulatory readiness
  Insurer UW        : Climate-adjusted technical pricing (P&C)
  Insurer Actuarial : Climate-adjusted life reserves
  AM PM             : ESG-attributed performance (alpha decomposition)
  AM Risk           : Enhanced risk reporting (climate VaR, concentration)
  PE Deals          : ESG-integrated deal scoring
  RE Valuations     : Enhanced property valuation with green premium
  Energy Strategy   : Transition pathway optimisation
  Agri Finance      : Sustainable agriculture finance overlays
  Geopolitical      : Integrated trade risk overlays

FI Type × LOB Matrix
---------------------
  12 combinations — see IMPLEMENTATION_PLAN_V2.md Chunk 6 table.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════
# 1. ESG Factor Registry
# ═══════════════════════════════════════════════════════════════════════

# Sector-level ESG transition risk PD multiplier (NACE section → multiplier)
# Source: PRI Inevitable Policy Response 2024 + NGFS implied curves
ESG_TRANSITION_PD_MULTIPLIER: dict[str, float] = {
    "A": 1.08,   # Agriculture — moderate land-use transition risk
    "B": 1.35,   # Mining — high stranded-asset risk
    "C": 1.18,   # Manufacturing — energy-intensity dependent
    "D": 1.40,   # Electricity/gas — highest transition risk
    "E": 1.05,   # Water/waste — low transition, some methane
    "F": 1.12,   # Construction — embodied carbon regulation
    "G": 1.04,   # Wholesale/retail — low direct risk
    "H": 1.22,   # Transport — fleet electrification cost
    "I": 1.03,   # Accommodation/food — minor
    "J": 0.97,   # ICT — net beneficiary of transition
    "K": 1.02,   # Financial services — pass-through only
    "L": 1.06,   # Real estate — building efficiency regulation
    "M": 0.98,   # Professional services — net beneficiary
    "N": 1.01,   # Admin services — negligible
    "O": 1.00,   # Public admin — benchmark
    "P": 0.99,   # Education — negligible
    "Q": 1.01,   # Health — minor energy cost
    "R": 1.00,   # Arts/recreation — negligible
    "S": 1.00,   # Other services — negligible
    "T": 1.00,   # Households — negligible
    "U": 1.00,   # Extraterritorial — negligible
}

# Green bond premium curve (bps tightening) by credit quality tier
# Source: Climate Bonds Initiative 2024 State of the Market
GREEN_BOND_PREMIUM_BPS: dict[str, float] = {
    "AAA": -3.0,
    "AA":  -5.0,
    "A":   -8.0,
    "BBB": -12.0,
    "BB":  -15.0,
    "B":   -18.0,
    "CCC": -10.0,  # liquidity premium offsets some greenium
}

# Biodiversity loss → nat-cat frequency amplifier by biome
# Source: IPBES Global Assessment 2024 + Swiss Re sigma 2024
BIODIVERSITY_NATCAT_AMPLIFIER: dict[str, float] = {
    "tropical_forest":   1.25,
    "temperate_forest":  1.10,
    "boreal_forest":     1.05,
    "grassland":         1.08,
    "wetland":           1.30,  # highest — flood buffer loss
    "coral_reef":        1.20,  # coastal storm surge
    "mangrove":          1.35,  # coastal protection loss
    "urban":             1.02,
    "arid":              1.06,
    "tundra":            1.03,
}

# ESG alpha decomposition factors (sector-level % of return attributable)
# Source: MSCI ESG-adjusted factor model 2024
ESG_ALPHA_DECOMPOSITION: dict[str, dict[str, float]] = {
    "E": {"A": 0.08, "B": 0.15, "C": 0.10, "D": 0.18, "E": 0.06,
          "F": 0.07, "G": 0.03, "H": 0.09, "J": 0.02, "K": 0.04, "L": 0.06},
    "S": {"A": 0.04, "B": 0.06, "C": 0.07, "D": 0.03, "E": 0.03,
          "F": 0.05, "G": 0.06, "H": 0.04, "J": 0.05, "K": 0.03, "L": 0.02},
    "G": {"A": 0.03, "B": 0.05, "C": 0.04, "D": 0.04, "E": 0.02,
          "F": 0.03, "G": 0.03, "H": 0.03, "J": 0.04, "K": 0.06, "L": 0.03},
}

# Air quality → mortality adjustment factor (WHO PM2.5 bands)
# Source: WHO Global Air Quality Guidelines 2021 + Lancet Commission 2024
AIR_QUALITY_MORTALITY: dict[str, float] = {
    "very_low":   1.00,   # < 5 µg/m³ — WHO interim target 4
    "low":        1.02,   # 5–10 µg/m³
    "moderate":   1.06,   # 10–25 µg/m³
    "high":       1.12,   # 25–50 µg/m³
    "very_high":  1.20,   # > 50 µg/m³
}

# Carbon reduction → PE valuation uplift (tCO2e reduction % → EV/EBITDA multiple uplift)
CARBON_REDUCTION_VALUATION_UPLIFT: dict[str, float] = {
    "0-10":    0.0,
    "10-25":   0.3,
    "25-50":   0.6,
    "50-75":   1.0,
    "75-100":  1.5,
}

# Green premium percentages for real estate by certification tier
# Source: JLL Green Premium Study 2024 + CBRE ESG & Real Estate 2024
GREEN_PREMIUM_PCT: dict[str, float] = {
    "LEED_platinum":  12.0,
    "LEED_gold":       8.5,
    "LEED_silver":     5.0,
    "BREEAM_outstanding": 11.0,
    "BREEAM_excellent":    7.5,
    "BREEAM_very_good":    4.0,
    "NABERS_6star":   10.0,
    "NABERS_5star":    6.5,
    "WELL_platinum":   6.0,
    "WELL_gold":       4.0,
    "EPC_A":           7.0,
    "EPC_B":           3.5,
    "EPC_C":           0.0,
    "EPC_D":          -2.0,
    "EPC_E":          -5.0,
    "EPC_F":          -8.0,
    "EPC_G":         -12.0,
    "none":            0.0,
}

# Methane abatement cost curve (USD/tCO2e) by technology
# Source: IEA Global Methane Tracker 2024
METHANE_ABATEMENT_CURVE: dict[str, dict[str, float]] = {
    "ldar_upstream":       {"cost_per_tco2e": -5.0,  "potential_pct": 0.15},
    "flare_to_capture":    {"cost_per_tco2e": -3.0,  "potential_pct": 0.10},
    "compressor_seal":     {"cost_per_tco2e": 2.0,   "potential_pct": 0.08},
    "pneumatic_replace":   {"cost_per_tco2e": 5.0,   "potential_pct": 0.12},
    "anaerobic_digestion": {"cost_per_tco2e": 15.0,  "potential_pct": 0.10},
    "enteric_supplement":  {"cost_per_tco2e": 25.0,  "potential_pct": 0.20},
    "rice_awd":            {"cost_per_tco2e": 8.0,   "potential_pct": 0.05},
    "landfill_capture":    {"cost_per_tco2e": 10.0,  "potential_pct": 0.07},
}

# Deforestation-free certification premium (% value uplift)
DEFORESTATION_FREE_PREMIUM: dict[str, float] = {
    "RSPO_certified":    3.5,
    "FSC_certified":     4.0,
    "Rainforest_Alliance": 2.8,
    "EUDR_compliant":    5.0,  # EU Deforestation Regulation compliance
    "none":              0.0,
}

# CSRD automated gap closure rates by ESG pillar
CSRD_GAP_CLOSURE_RATES: dict[str, float] = {
    "E1_climate":      0.72,
    "E2_pollution":    0.55,
    "E3_water":        0.48,
    "E4_biodiversity": 0.35,
    "E5_circular":     0.42,
    "S1_workforce":    0.60,
    "S2_value_chain":  0.38,
    "S3_communities":  0.30,
    "S4_consumers":    0.33,
    "G1_conduct":      0.65,
    "G2_lobbying":     0.40,
}


# ═══════════════════════════════════════════════════════════════════════
# 2. Geopolitical Factor Registry
# ═══════════════════════════════════════════════════════════════════════

# Sovereign risk passthrough scores (ISO-2 → 0-100 composite)
# Source: World Bank WGI 2024 + OECD CRC + Maplecroft
SOVEREIGN_RISK_SCORES: dict[str, float] = {
    "US": 22, "GB": 18, "DE": 15, "FR": 20, "JP": 16,
    "CN": 48, "IN": 42, "BR": 45, "RU": 72, "ZA": 50,
    "AU": 14, "CA": 16, "SG": 10, "CH": 8,  "NL": 12,
    "SE": 9,  "NO": 7,  "KR": 24, "MX": 52, "ID": 40,
    "NG": 62, "SA": 38, "AE": 28, "TR": 55, "EG": 58,
    "PL": 30, "CZ": 22, "HU": 35, "RO": 38, "BG": 40,
    "AR": 65, "CL": 32, "CO": 48, "PE": 45, "VN": 38,
    "TH": 35, "MY": 30, "PH": 42, "KE": 55, "GH": 52,
    "TZ": 48, "ET": 60, "BD": 55, "PK": 65, "LK": 58,
}

# FX-climate correlation coefficients (how much climate events affect currency)
# Source: BIS Working Paper 2024 + IMF Climate & FX study
FX_CLIMATE_CORRELATION: dict[str, float] = {
    "US": 0.05, "GB": 0.08, "DE": 0.06, "FR": 0.07, "JP": 0.04,
    "CN": 0.15, "IN": 0.22, "BR": 0.25, "RU": 0.18, "ZA": 0.20,
    "AU": 0.18, "CA": 0.12, "SG": 0.06, "ID": 0.28, "MX": 0.20,
    "NG": 0.30, "PH": 0.32, "BD": 0.35, "PK": 0.30, "VN": 0.22,
}

# Sanctions cascade exposure (0-1 probability of secondary sanctions hitting sector)
SANCTIONS_CASCADE: dict[str, dict[str, float]] = {
    "RU": {"B": 0.90, "D": 0.85, "K": 0.70, "H": 0.60, "C": 0.50, "G": 0.40},
    "CN": {"J": 0.35, "C": 0.30, "H": 0.25, "B": 0.20, "K": 0.15},
    "IR": {"B": 0.95, "D": 0.90, "K": 0.80, "H": 0.70},
    "KP": {"B": 0.99, "C": 0.95, "K": 0.90},
    "BY": {"B": 0.70, "D": 0.65, "K": 0.55, "C": 0.45},
    "VE": {"B": 0.75, "D": 0.70, "K": 0.50},
}

# Political stability index (0 = very stable, 100 = failed state)
# Source: Fund for Peace Fragile States Index 2024
POLITICAL_STABILITY: dict[str, float] = {
    "US": 35, "GB": 28, "DE": 22, "FR": 30, "JP": 25,
    "CN": 55, "IN": 50, "BR": 48, "RU": 70, "ZA": 52,
    "AU": 20, "CA": 22, "SG": 18, "CH": 15, "NL": 20,
    "SE": 16, "NO": 12, "KR": 32, "MX": 58, "ID": 45,
    "NG": 72, "SA": 50, "AE": 35, "TR": 60, "EG": 62,
}

# Food security index (0 = fully secure, 100 = crisis)
# Source: Global Food Security Index (EIU/Corteva) 2024
FOOD_SECURITY_INDEX: dict[str, float] = {
    "US": 12, "GB": 15, "DE": 14, "FR": 13, "JP": 18,
    "CN": 28, "IN": 42, "BR": 25, "RU": 30, "ZA": 45,
    "AU": 10, "CA": 11, "SG": 22, "NG": 65, "EG": 55,
    "BD": 58, "PK": 55, "ET": 72, "KE": 52, "GH": 48,
}

# Energy independence score (0 = fully import-dependent, 100 = net exporter)
ENERGY_INDEPENDENCE: dict[str, float] = {
    "US": 85, "GB": 55, "DE": 35, "FR": 50, "JP": 12,
    "CN": 60, "IN": 30, "BR": 75, "RU": 95, "ZA": 70,
    "AU": 90, "CA": 92, "SG": 5,  "NO": 98, "SA": 97,
    "AE": 95, "NG": 88, "QA": 96, "ID": 72, "MX": 60,
}

# Cross-jurisdiction regulatory complexity multiplier
REGULATORY_COMPLEXITY: dict[str, float] = {
    "EU":     1.35,  # CSRD + SFDR + Taxonomy + CSDDD
    "US":     1.15,  # SEC climate + state-level
    "GB":     1.20,  # TCFD mandatory + SDR
    "CH":     1.10,  # FINMA climate
    "SG":     1.12,  # MAS environmental risk
    "AU":     1.18,  # ASRS climate standard
    "JP":     1.08,  # SSBJ standards
    "CN":     1.05,  # ISSB adoption pending
    "IN":     1.10,  # BRSR mandatory
    "BR":     1.08,  # CVM + BCB
    "other":  1.00,
}

# Migration pattern impact on life actuarial assumptions
MIGRATION_MORTALITY_ADJUSTMENT: dict[str, float] = {
    "net_inflow_high":    0.97,  # younger population → lower mortality
    "net_inflow_moderate": 0.99,
    "stable":              1.00,
    "net_outflow_moderate": 1.01,
    "net_outflow_high":    1.04,  # brain drain → healthcare decline
}

# Carbon border alignment scores for trade (0 = fully exposed, 1 = fully aligned)
CARBON_BORDER_ALIGNMENT: dict[str, float] = {
    "EU":    0.90,
    "GB":    0.75,
    "CA":    0.60,
    "US":    0.35,
    "AU":    0.45,
    "JP":    0.55,
    "KR":    0.50,
    "CN":    0.25,
    "IN":    0.20,
    "BR":    0.30,
    "RU":    0.10,
    "other": 0.15,
}


# ═══════════════════════════════════════════════════════════════════════
# 3. Technology Factor Registry
# ═══════════════════════════════════════════════════════════════════════

# Automation disruption score by NACE sector (0-1; 1 = fully automatable)
# Source: McKinsey Global Institute Automation Potential 2024 + OECD AI Index
AUTOMATION_DISRUPTION: dict[str, float] = {
    "A": 0.55,  # Agriculture — precision ag, autonomous equipment
    "B": 0.45,  # Mining — autonomous vehicles, remote ops
    "C": 0.62,  # Manufacturing — robotics, Industry 4.0
    "D": 0.40,  # Electricity — grid automation, smart meters
    "E": 0.35,  # Water/waste — process automation
    "F": 0.42,  # Construction — modular, 3D printing
    "G": 0.50,  # Wholesale/retail — checkout, warehouse
    "H": 0.58,  # Transport — autonomous vehicles
    "I": 0.38,  # Accommodation — service robots
    "J": 0.25,  # ICT — AI augments rather than replaces
    "K": 0.48,  # Finance — algorithmic, RPA
    "L": 0.20,  # Real estate — PropTech but relationship-heavy
    "M": 0.30,  # Professional services — AI copilots
    "N": 0.55,  # Admin services — highly automatable back-office
    "O": 0.22,  # Public admin — policy complexity
    "P": 0.18,  # Education — EdTech but human-centric
    "Q": 0.28,  # Health — diagnostics AI, but human care
    "R": 0.15,  # Arts — creative resistance
    "S": 0.25,  # Other services — mixed
}

# Fintech disruption to NIM (bps erosion per year, negative = erosion)
FINTECH_NIM_DISRUPTION: dict[str, float] = {
    "retail_banking":      -8.0,
    "commercial_banking":  -4.0,
    "investment_banking":  -2.0,
    "wealth_management":   -3.0,
    "insurance":           -5.0,
    "payments":           -12.0,
    "trade_finance":       -6.0,
    "mortgage":            -7.0,
}

# AI adoption scoring by sector (0-1; 1 = full AI integration)
AI_ADOPTION_SCORE: dict[str, float] = {
    "A": 0.20,  "B": 0.25,  "C": 0.45,  "D": 0.40,
    "E": 0.22,  "F": 0.18,  "G": 0.48,  "H": 0.35,
    "I": 0.15,  "J": 0.75,  "K": 0.60,  "L": 0.28,
    "M": 0.55,  "N": 0.42,  "O": 0.20,  "P": 0.30,
    "Q": 0.38,  "R": 0.22,  "S": 0.18,
}

# Smart building score uplift (%) by technology tier
SMART_BUILDING_UPLIFT: dict[str, float] = {
    "tier_4_cognitive":  8.0,   # AI-optimised, predictive
    "tier_3_automated":  5.5,   # BMS + automated controls
    "tier_2_connected":  3.0,   # IoT sensors, dashboards
    "tier_1_basic":      1.0,   # basic BMS
    "tier_0_none":       0.0,
}

# Digital readiness scoring (0-100) by country
# Source: IMD World Digital Competitiveness Ranking 2024
DIGITAL_READINESS: dict[str, float] = {
    "US": 88, "SG": 92, "CH": 85, "SE": 87, "DK": 86,
    "NL": 84, "KR": 83, "GB": 80, "FI": 82, "AU": 78,
    "DE": 76, "CA": 79, "JP": 74, "FR": 72, "IL": 81,
    "CN": 65, "IN": 50, "BR": 48, "MX": 42, "ZA": 45,
    "NG": 30, "EG": 35, "ID": 42, "VN": 48, "TH": 52,
}

# Parametric insurance pricing adjustment (% change)
PARAMETRIC_PRICING_ADJ: dict[str, float] = {
    "wind_speed":       -15.0,  # lower basis risk → cheaper
    "rainfall":         -12.0,
    "earthquake":       -10.0,
    "drought_index":     -8.0,
    "flood_depth":      -14.0,
    "wildfire_index":    -6.0,
    "traditional_only":   0.0,
}

# H2 blending economics (USD/MWh cost differential vs. natural gas)
H2_BLENDING_ECONOMICS: dict[str, dict[str, float]] = {
    "green_h2":  {"cost_premium": 45.0, "co2_reduction_pct": 0.95, "tech_readiness": 0.65},
    "blue_h2":   {"cost_premium": 18.0, "co2_reduction_pct": 0.55, "tech_readiness": 0.80},
    "grey_h2":   {"cost_premium": 0.0,  "co2_reduction_pct": 0.00, "tech_readiness": 1.00},
    "pink_h2":   {"cost_premium": 30.0, "co2_reduction_pct": 0.90, "tech_readiness": 0.50},
}

# Precision agriculture adoption uplift (% yield improvement)
PRECISION_AG_ADOPTION: dict[str, float] = {
    "full_precision":       15.0,  # GPS, VRT, drones, AI
    "partial_precision":     8.0,  # some components
    "conventional_improved": 3.0,  # improved inputs only
    "conventional":          0.0,
}

# Supply chain digitisation score (trade finance)
SUPPLY_CHAIN_DIGITISATION: dict[str, float] = {
    "full_digital":     0.85,  # blockchain + IoT + API
    "partial_digital":  0.55,  # e-invoicing + ERP
    "paper_hybrid":     0.25,  # some paper
    "fully_paper":      0.05,  # legacy paper-based
}

# AI assurance confidence for regulatory compliance
AI_ASSURANCE_CONFIDENCE: dict[str, float] = {
    "high":    0.90,  # automated extraction + human review
    "medium":  0.70,  # automated extraction, limited review
    "low":     0.45,  # manual-heavy, error-prone
    "none":    0.20,  # no systematic assurance
}

# Medical advancement longevity factor (years added to life expectancy)
MEDICAL_ADVANCEMENT_LONGEVITY: dict[str, float] = {
    "gene_therapy":          2.5,
    "ai_diagnostics":        1.8,
    "precision_medicine":    2.0,
    "telemedicine":          0.8,
    "wearable_monitoring":   1.0,
    "baseline":              0.0,
}

# Stranded asset technology filter thresholds
STRANDED_ASSET_TECH_FILTER: dict[str, dict[str, float]] = {
    "coal_power":        {"stranding_probability": 0.85, "horizon_years": 8},
    "oil_refining":      {"stranding_probability": 0.55, "horizon_years": 15},
    "gas_power_ccgt":    {"stranding_probability": 0.30, "horizon_years": 22},
    "ice_manufacturing": {"stranding_probability": 0.65, "horizon_years": 12},
    "steel_bof":         {"stranding_probability": 0.50, "horizon_years": 18},
    "cement_wet":        {"stranding_probability": 0.45, "horizon_years": 20},
    "shipping_hfo":      {"stranding_probability": 0.40, "horizon_years": 18},
    "aviation_kerosene": {"stranding_probability": 0.35, "horizon_years": 25},
}


# ═══════════════════════════════════════════════════════════════════════
# 4. Data Classes
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class FactorScore:
    """Individual factor contribution."""
    factor_type: str        # "esg", "geopolitical", "technology"
    factor_name: str
    raw_value: float
    adjustment: float       # multiplicative or additive delta
    unit: str               # "multiplier", "bps", "pct", "score"
    source: str             # reference data source
    confidence: float       # 0–1


@dataclass
class OverlayResult:
    """Result of applying factor overlays to a module output."""
    entity_id: str
    module_id: str
    overlay_type: str          # "ecl_credit", "alm_treasury", etc.
    base_metrics: dict
    enhanced_metrics: dict
    esg_factors: list[FactorScore]
    geo_factors: list[FactorScore]
    tech_factors: list[FactorScore]
    composite_adjustment: float
    confidence: float
    warnings: list[str]
    audit_trail: list[str]
    as_of_date: str


# ═══════════════════════════════════════════════════════════════════════
# 5. Factor Overlay Engine
# ═══════════════════════════════════════════════════════════════════════

class FactorOverlayEngine:
    """
    Cross-cutting overlay engine.

    Applies ESG, geopolitical, and technology factor adjustments
    to base analytics produced by any module on the platform.

    Methods (one per FI Type × LOB combination):
        overlay_ecl_credit()            — Bank Credit
        overlay_alm_treasury()          — Bank Treasury
        overlay_regulatory_compliance() — Bank Compliance
        overlay_insurance_uw()          — Insurer UW (P&C)
        overlay_insurance_actuarial()   — Insurer Actuarial (Life)
        overlay_portfolio_management()  — AM PM (Equity)
        overlay_risk_management()       — AM Risk (Multi-Asset)
        overlay_pe_deal()               — PE Deals (Buyout)
        overlay_real_estate_valuation() — RE Valuations (Commercial)
        overlay_energy_strategy()       — Energy Strategy (Generation)
        overlay_agriculture_finance()   — Agriculture Finance
        overlay_trade_advisory()        — Geopolitical Advisory (Trade)
    """

    # ---------------------------------------------------------------
    # Helper: lookup with fallback
    # ---------------------------------------------------------------
    @staticmethod
    def _lookup(registry: dict, key: str, default=None):
        return registry.get(key, registry.get("other", default if default is not None else 0.0))

    # ---------------------------------------------------------------
    # 5.1  Bank — Credit: Climate-adjusted ECL
    # ---------------------------------------------------------------
    def overlay_ecl_credit(
        self,
        entity_id: str,
        country_code: str,
        sector_nace: str,
        base_pd: float,
        base_lgd: float,
        base_ead: float,
        scenario: str = "current_policies",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply ESG transition risk PD uplift, sovereign risk pass-through,
        and automation disruption score to ECL components.

        Transformations:
          1. ESG: PD_adj = PD_base × ESG_TRANSITION_PD_MULTIPLIER[sector]
          2. Geo: PD_adj *= (1 + sovereign_risk / 1000)
          3. Tech: LGD_adj = LGD × (1 + automation_disruption × 0.15)
          4. ECL_enhanced = PD_adj × LGD_adj × EAD
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # --- ESG: transition risk PD uplift ---
        esg_mult = ESG_TRANSITION_PD_MULTIPLIER.get(sector_nace, 1.0)
        pd_esg = base_pd * esg_mult
        esg_factor = FactorScore("esg", "transition_risk_pd_uplift", esg_mult,
                                  esg_mult - 1.0, "multiplier",
                                  "PRI IPR 2024", 0.85)
        audit.append(f"ESG: PD {base_pd:.4f} × {esg_mult:.2f} = {pd_esg:.4f}")

        # --- Geo: sovereign risk pass-through ---
        sov_risk = self._lookup(SOVEREIGN_RISK_SCORES, country_code, 50.0)
        sov_adj = 1 + sov_risk / 1000
        pd_adj = pd_esg * sov_adj
        geo_factor = FactorScore("geopolitical", "sovereign_risk_passthrough",
                                  sov_risk, sov_adj - 1.0, "multiplier",
                                  "WB WGI 2024", 0.80)
        audit.append(f"Geo: PD {pd_esg:.4f} × {sov_adj:.4f} = {pd_adj:.4f}")

        # --- Tech: automation disruption → LGD stress ---
        auto_score = AUTOMATION_DISRUPTION.get(sector_nace, 0.3)
        lgd_adj = base_lgd * (1 + auto_score * 0.15)
        tech_factor = FactorScore("technology", "automation_disruption",
                                   auto_score, auto_score * 0.15, "multiplier",
                                   "McKinsey 2024", 0.75)
        audit.append(f"Tech: LGD {base_lgd:.4f} × (1+{auto_score:.2f}×0.15) = {lgd_adj:.4f}")

        # --- Combined ECL ---
        ecl_base = base_pd * base_lgd * base_ead
        ecl_enhanced = pd_adj * lgd_adj * base_ead
        composite = ecl_enhanced / ecl_base if ecl_base > 0 else 1.0
        audit.append(f"ECL base={ecl_base:,.2f}  enhanced={ecl_enhanced:,.2f}  ratio={composite:.4f}")

        if sov_risk > 60:
            warnings.append(f"High sovereign risk ({sov_risk}) for {country_code}")
        if esg_mult > 1.25:
            warnings.append(f"High transition risk sector ({sector_nace}, mult={esg_mult})")

        return OverlayResult(
            entity_id=entity_id, module_id="ecl_climate_engine",
            overlay_type="ecl_credit",
            base_metrics={"pd": base_pd, "lgd": base_lgd, "ead": base_ead, "ecl": ecl_base},
            enhanced_metrics={"pd": pd_adj, "lgd": lgd_adj, "ead": base_ead, "ecl": ecl_enhanced},
            esg_factors=[esg_factor], geo_factors=[geo_factor], tech_factors=[tech_factor],
            composite_adjustment=composite, confidence=0.80,
            warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.2  Bank — Treasury: ALM with ESG/macro overlays
    # ---------------------------------------------------------------
    def overlay_alm_treasury(
        self,
        entity_id: str,
        country_code: str,
        credit_quality: str,
        base_nim_bps: float,
        base_duration_gap: float,
        fx_exposure_pct: float = 0.0,
        scenario: str = "current_policies",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply green bond premium curve, FX-climate correlation,
        and fintech NIM disruption to ALM metrics.

        Transformations:
          1. ESG: NIM_adj = NIM_base + green_bond_premium_bps
          2. Geo: duration_adj = duration_gap × (1 + fx_climate_corr × fx_exposure)
          3. Tech: NIM_adj -= fintech_nim_disruption
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: green bond premium
        greenium = GREEN_BOND_PREMIUM_BPS.get(credit_quality, -5.0)
        nim_esg = base_nim_bps + greenium
        esg_f = FactorScore("esg", "green_bond_premium", greenium, greenium,
                            "bps", "CBI 2024", 0.82)
        audit.append(f"ESG: NIM {base_nim_bps:.1f} + greenium {greenium:.1f} = {nim_esg:.1f} bps")

        # Geo: FX-climate correlation
        fx_corr = self._lookup(FX_CLIMATE_CORRELATION, country_code, 0.10)
        dur_adj = base_duration_gap * (1 + fx_corr * fx_exposure_pct)
        geo_f = FactorScore("geopolitical", "fx_climate_correlation", fx_corr,
                            fx_corr * fx_exposure_pct, "multiplier",
                            "BIS 2024", 0.70)
        audit.append(f"Geo: dur gap {base_duration_gap:.2f} × (1+{fx_corr:.2f}×{fx_exposure_pct:.2f}) = {dur_adj:.2f}")

        # Tech: fintech NIM disruption
        fintech_ero = FINTECH_NIM_DISRUPTION.get("retail_banking", -5.0)
        nim_final = nim_esg + fintech_ero  # fintech_ero is negative
        tech_f = FactorScore("technology", "fintech_nim_disruption", fintech_ero,
                             fintech_ero, "bps", "McKinsey 2024", 0.72)
        audit.append(f"Tech: NIM {nim_esg:.1f} + fintech {fintech_ero:.1f} = {nim_final:.1f} bps")

        composite = nim_final / base_nim_bps if base_nim_bps else 1.0

        return OverlayResult(
            entity_id=entity_id, module_id="scenario_analysis_engine",
            overlay_type="alm_treasury",
            base_metrics={"nim_bps": base_nim_bps, "duration_gap": base_duration_gap},
            enhanced_metrics={"nim_bps": nim_final, "duration_gap": dur_adj},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=composite, confidence=0.75,
            warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.3  Bank — Compliance: Multi-jurisdiction regulatory readiness
    # ---------------------------------------------------------------
    def overlay_regulatory_compliance(
        self,
        entity_id: str,
        jurisdiction: str,
        current_gap_count: int,
        esrs_pillars: list[str] | None = None,
        assurance_level: str = "medium",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply automated gap closure, cross-jurisdiction complexity,
        and AI assurance confidence to regulatory compliance metrics.

        Transformations:
          1. ESG: closeable_gaps = sum(gap_closure_rate[pillar]) × current_gaps
          2. Geo: effort_multiplier = regulatory_complexity[jurisdiction]
          3. Tech: confidence = ai_assurance_confidence[level]
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())
        pillars = esrs_pillars or ["E1_climate", "S1_workforce", "G1_conduct"]

        # ESG: automated gap closure
        avg_closure = sum(CSRD_GAP_CLOSURE_RATES.get(p, 0.4) for p in pillars) / len(pillars)
        closeable = int(current_gap_count * avg_closure)
        remaining = current_gap_count - closeable
        esg_f = FactorScore("esg", "automated_gap_closure", avg_closure,
                            -closeable, "count", "CSRD IG 2024", 0.78)
        audit.append(f"ESG: {current_gap_count} gaps × {avg_closure:.2f} closure = {closeable} auto-closeable, {remaining} remaining")

        # Geo: cross-jurisdiction complexity
        reg_mult = self._lookup(REGULATORY_COMPLEXITY, jurisdiction, 1.0)
        effort_adjusted = remaining * reg_mult
        geo_f = FactorScore("geopolitical", "regulatory_complexity", reg_mult,
                            reg_mult - 1.0, "multiplier", "Multi-reg 2024", 0.82)
        audit.append(f"Geo: {remaining} remaining × {reg_mult:.2f} complexity = {effort_adjusted:.1f} adjusted effort")

        # Tech: AI assurance confidence
        ai_conf = AI_ASSURANCE_CONFIDENCE.get(assurance_level, 0.45)
        tech_f = FactorScore("technology", "ai_assurance_confidence", ai_conf,
                             ai_conf, "score", "Big4 survey 2024", 0.70)
        audit.append(f"Tech: assurance confidence = {ai_conf:.2f}")

        if reg_mult > 1.25:
            warnings.append(f"High regulatory complexity ({jurisdiction}, mult={reg_mult})")

        return OverlayResult(
            entity_id=entity_id, module_id="csrd_auto_populate",
            overlay_type="regulatory_compliance",
            base_metrics={"gap_count": current_gap_count},
            enhanced_metrics={"closeable_gaps": closeable, "remaining_gaps": remaining,
                              "effort_multiplier": reg_mult, "ai_confidence": ai_conf,
                              "adjusted_effort": effort_adjusted},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=remaining / current_gap_count if current_gap_count else 1.0,
            confidence=0.76, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.4  Insurer — UW: Climate-adjusted technical pricing (P&C)
    # ---------------------------------------------------------------
    def overlay_insurance_uw(
        self,
        entity_id: str,
        country_code: str,
        biome: str,
        base_premium: float,
        base_loss_ratio: float,
        parametric_trigger: str = "traditional_only",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply biodiversity nat-cat amplifier, supply chain BI claims,
        and parametric pricing adjustment.

        Transformations:
          1. ESG: loss_ratio_adj = loss_ratio × biodiversity_amplifier[biome]
          2. Geo: BI_loading = sovereign_risk / 200 (supply chain disruption)
          3. Tech: premium_adj = premium × (1 + parametric_adj / 100)
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: biodiversity → nat-cat frequency
        bio_amp = BIODIVERSITY_NATCAT_AMPLIFIER.get(biome, 1.05)
        lr_adj = base_loss_ratio * bio_amp
        esg_f = FactorScore("esg", "biodiversity_natcat_amplifier", bio_amp,
                            bio_amp - 1.0, "multiplier", "IPBES 2024", 0.72)
        audit.append(f"ESG: loss ratio {base_loss_ratio:.4f} × {bio_amp:.2f} = {lr_adj:.4f}")

        # Geo: supply chain → BI claims loading
        sov = self._lookup(SOVEREIGN_RISK_SCORES, country_code, 40.0)
        bi_loading = sov / 200
        lr_with_bi = lr_adj + bi_loading
        geo_f = FactorScore("geopolitical", "supply_chain_bi_claims", sov,
                            bi_loading, "pct", "WB WGI 2024", 0.68)
        audit.append(f"Geo: BI loading = {sov:.0f}/200 = {bi_loading:.4f}, LR = {lr_with_bi:.4f}")

        # Tech: parametric pricing
        param_adj = PARAMETRIC_PRICING_ADJ.get(parametric_trigger, 0.0)
        premium_adj = base_premium * (1 + param_adj / 100)
        tech_f = FactorScore("technology", "parametric_pricing", param_adj,
                             param_adj, "pct", "Swiss Re 2024", 0.75)
        audit.append(f"Tech: premium {base_premium:,.2f} × (1 + {param_adj:.1f}%) = {premium_adj:,.2f}")

        if bio_amp > 1.20:
            warnings.append(f"High biodiversity loss risk in {biome} biome")

        return OverlayResult(
            entity_id=entity_id, module_id="insurance_risk_engine",
            overlay_type="insurance_uw",
            base_metrics={"premium": base_premium, "loss_ratio": base_loss_ratio},
            enhanced_metrics={"premium": premium_adj, "loss_ratio": lr_with_bi},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=premium_adj / base_premium if base_premium else 1.0,
            confidence=0.72, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.5  Insurer — Actuarial: Climate-adjusted life reserves
    # ---------------------------------------------------------------
    def overlay_insurance_actuarial(
        self,
        entity_id: str,
        country_code: str,
        air_quality_band: str,
        base_mortality_rate: float,
        migration_pattern: str = "stable",
        medical_tech: str = "baseline",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply air quality mortality factor, migration mortality adjustment,
        and medical advancement longevity factor.

        Transformations:
          1. ESG: mortality_adj = base × air_quality_mortality[band]
          2. Geo: mortality_adj *= migration_adjustment[pattern]
          3. Tech: longevity_offset = medical_advancement[tech] (years)
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: air quality
        aq_mult = AIR_QUALITY_MORTALITY.get(air_quality_band, 1.0)
        mort_esg = base_mortality_rate * aq_mult
        esg_f = FactorScore("esg", "air_quality_mortality", aq_mult,
                            aq_mult - 1.0, "multiplier", "WHO 2021", 0.80)
        audit.append(f"ESG: mortality {base_mortality_rate:.6f} × {aq_mult:.2f} = {mort_esg:.6f}")

        # Geo: migration patterns
        mig_adj = MIGRATION_MORTALITY_ADJUSTMENT.get(migration_pattern, 1.0)
        mort_adj = mort_esg * mig_adj
        geo_f = FactorScore("geopolitical", "migration_mortality", mig_adj,
                            mig_adj - 1.0, "multiplier", "UN Population 2024", 0.65)
        audit.append(f"Geo: mortality × {mig_adj:.3f} migration = {mort_adj:.6f}")

        # Tech: medical advancement
        longevity_yrs = MEDICAL_ADVANCEMENT_LONGEVITY.get(medical_tech, 0.0)
        tech_f = FactorScore("technology", "medical_advancement", longevity_yrs,
                             longevity_yrs, "years", "Lancet 2024", 0.60)
        audit.append(f"Tech: longevity offset = +{longevity_yrs:.1f} years")

        return OverlayResult(
            entity_id=entity_id, module_id="insurance_risk_engine",
            overlay_type="insurance_actuarial",
            base_metrics={"mortality_rate": base_mortality_rate},
            enhanced_metrics={"mortality_rate": mort_adj, "longevity_offset_years": longevity_yrs},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=mort_adj / base_mortality_rate if base_mortality_rate else 1.0,
            confidence=0.68, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.6  AM — PM: ESG-attributed performance
    # ---------------------------------------------------------------
    def overlay_portfolio_management(
        self,
        entity_id: str,
        sector_nace: str,
        base_return_pct: float,
        base_alpha_pct: float,
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply ESG alpha decomposition, tariff impact, and AI adoption scoring.

        Transformations:
          1. ESG: alpha_esg = base_alpha × (E+S+G decomposition factors)
          2. Geo: tariff_drag = sovereign_risk × 0.001
          3. Tech: ai_boost = ai_adoption_score × 0.02 (2% max)
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: alpha decomposition
        e_pct = ESG_ALPHA_DECOMPOSITION["E"].get(sector_nace, 0.05)
        s_pct = ESG_ALPHA_DECOMPOSITION["S"].get(sector_nace, 0.03)
        g_pct = ESG_ALPHA_DECOMPOSITION["G"].get(sector_nace, 0.03)
        total_esg_alpha = base_alpha_pct * (e_pct + s_pct + g_pct)
        residual_alpha = base_alpha_pct - total_esg_alpha
        esg_f = FactorScore("esg", "alpha_decomposition", e_pct + s_pct + g_pct,
                            total_esg_alpha, "pct", "MSCI 2024", 0.78)
        audit.append(f"ESG: alpha {base_alpha_pct:.2f}% → E={e_pct:.2f} S={s_pct:.2f} G={g_pct:.2f}, ESG alpha={total_esg_alpha:.4f}%")

        # Geo: tariff impact (generic proxy using sovereign risk)
        # Note: in production, would use entity-level country exposure
        tariff_drag = 0.0  # placeholder; real version uses holding-level country weights
        geo_f = FactorScore("geopolitical", "tariff_impact", tariff_drag,
                            -tariff_drag, "pct", "OECD Trade 2024", 0.55)
        audit.append(f"Geo: tariff drag = {tariff_drag:.4f}%")

        # Tech: AI adoption uplift
        ai_score = AI_ADOPTION_SCORE.get(sector_nace, 0.3)
        ai_boost = ai_score * 0.02  # max 2% return boost for full AI adoption
        return_adj = base_return_pct + ai_boost - tariff_drag
        tech_f = FactorScore("technology", "ai_adoption_scoring", ai_score,
                             ai_boost, "pct", "WIPO GII 2024", 0.68)
        audit.append(f"Tech: AI score={ai_score:.2f}, return boost={ai_boost:.4f}%")

        return OverlayResult(
            entity_id=entity_id, module_id="portfolio_analytics",
            overlay_type="portfolio_management",
            base_metrics={"return_pct": base_return_pct, "alpha_pct": base_alpha_pct},
            enhanced_metrics={"return_pct": return_adj, "esg_alpha_pct": total_esg_alpha,
                              "residual_alpha_pct": residual_alpha, "e_attribution": e_pct,
                              "s_attribution": s_pct, "g_attribution": g_pct},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=return_adj / base_return_pct if base_return_pct else 1.0,
            confidence=0.72, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.7  AM — Risk: Enhanced risk reporting
    # ---------------------------------------------------------------
    def overlay_risk_management(
        self,
        entity_id: str,
        country_code: str,
        sector_nace: str,
        base_var_pct: float,
        base_cvar_pct: float,
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply climate VaR overlay, country concentration risk,
        and stranded asset filter.

        Transformations:
          1. ESG: VaR_climate = VaR × esg_transition_mult[sector]
          2. Geo: VaR_geo = VaR_climate × (1 + sov_risk / 500)
          3. Tech: stranded_flag = stranded_asset_tech_filter check
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: climate VaR overlay
        esg_mult = ESG_TRANSITION_PD_MULTIPLIER.get(sector_nace, 1.0)
        var_climate = base_var_pct * esg_mult
        esg_f = FactorScore("esg", "climate_var_overlay", esg_mult,
                            esg_mult - 1.0, "multiplier", "NGFS 2024", 0.80)
        audit.append(f"ESG: VaR {base_var_pct:.4f}% × {esg_mult:.2f} = {var_climate:.4f}%")

        # Geo: country concentration
        sov = self._lookup(SOVEREIGN_RISK_SCORES, country_code, 40.0)
        conc_mult = 1 + sov / 500
        var_adj = var_climate * conc_mult
        geo_f = FactorScore("geopolitical", "country_concentration", sov,
                            conc_mult - 1.0, "multiplier", "WB WGI 2024", 0.75)
        audit.append(f"Geo: VaR × {conc_mult:.4f} country conc = {var_adj:.4f}%")

        # Tech: stranded asset filter
        # Check if sector has significant stranding risk
        stranding_risk = 0.0
        for _tech, vals in STRANDED_ASSET_TECH_FILTER.items():
            if sector_nace in ("B", "D", "C"):  # mining, electricity, manufacturing
                stranding_risk = max(stranding_risk, vals["stranding_probability"])
        tech_f = FactorScore("technology", "stranded_asset_filter", stranding_risk,
                             stranding_risk, "probability", "IEA WEO 2024", 0.70)
        audit.append(f"Tech: stranding risk = {stranding_risk:.2f}")

        if stranding_risk > 0.5:
            warnings.append(f"High stranding risk ({stranding_risk:.0%}) for sector {sector_nace}")

        # CVaR scales proportionally
        cvar_adj = base_cvar_pct * (var_adj / base_var_pct) if base_var_pct else base_cvar_pct

        return OverlayResult(
            entity_id=entity_id, module_id="portfolio_analytics",
            overlay_type="risk_management",
            base_metrics={"var_pct": base_var_pct, "cvar_pct": base_cvar_pct},
            enhanced_metrics={"var_pct": var_adj, "cvar_pct": cvar_adj,
                              "stranding_probability": stranding_risk},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=var_adj / base_var_pct if base_var_pct else 1.0,
            confidence=0.74, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.8  PE — Deals: ESG-integrated deal scoring
    # ---------------------------------------------------------------
    def overlay_pe_deal(
        self,
        entity_id: str,
        country_code: str,
        sector_nace: str,
        base_ev_ebitda: float,
        carbon_reduction_pct: float = 0.0,
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply carbon reduction valuation uplift, political stability,
        and digital readiness to deal scoring.

        Transformations:
          1. ESG: EV/EBITDA += carbon_reduction_valuation_uplift[band]
          2. Geo: political_discount = (stability_index - 30) × 0.02 if > 30
          3. Tech: digital_premium = digital_readiness × 0.01
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: carbon reduction valuation uplift
        band = "0-10"
        if carbon_reduction_pct >= 75:
            band = "75-100"
        elif carbon_reduction_pct >= 50:
            band = "50-75"
        elif carbon_reduction_pct >= 25:
            band = "25-50"
        elif carbon_reduction_pct >= 10:
            band = "10-25"
        uplift = CARBON_REDUCTION_VALUATION_UPLIFT[band]
        ev_esg = base_ev_ebitda + uplift
        esg_f = FactorScore("esg", "carbon_reduction_uplift", carbon_reduction_pct,
                            uplift, "multiple", "BCG 2024", 0.72)
        audit.append(f"ESG: EV/EBITDA {base_ev_ebitda:.1f}x + {uplift:.1f} uplift = {ev_esg:.1f}x")

        # Geo: political stability discount
        stability = self._lookup(POLITICAL_STABILITY, country_code, 40.0)
        pol_discount = max(0.0, (stability - 30) * 0.02)
        ev_geo = ev_esg - pol_discount
        geo_f = FactorScore("geopolitical", "political_stability", stability,
                            -pol_discount, "multiple", "FFP FSI 2024", 0.70)
        audit.append(f"Geo: stability={stability:.0f}, discount={pol_discount:.2f}x, EV={ev_geo:.1f}x")

        # Tech: digital readiness premium
        digital = self._lookup(DIGITAL_READINESS, country_code, 50.0)
        digital_prem = digital * 0.01
        ev_final = ev_geo + digital_prem
        tech_f = FactorScore("technology", "digital_readiness", digital,
                             digital_prem, "multiple", "IMD 2024", 0.68)
        audit.append(f"Tech: digital={digital:.0f}, premium={digital_prem:.2f}x, EV={ev_final:.1f}x")

        if stability > 55:
            warnings.append(f"High political risk ({stability:.0f}) for {country_code}")

        return OverlayResult(
            entity_id=entity_id, module_id="pe_deal_engine",
            overlay_type="pe_deal",
            base_metrics={"ev_ebitda": base_ev_ebitda, "carbon_reduction_pct": carbon_reduction_pct},
            enhanced_metrics={"ev_ebitda": ev_final, "esg_uplift": uplift,
                              "political_discount": pol_discount, "digital_premium": digital_prem},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=ev_final / base_ev_ebitda if base_ev_ebitda else 1.0,
            confidence=0.70, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.9  RE — Valuations: Enhanced property valuation
    # ---------------------------------------------------------------
    def overlay_real_estate_valuation(
        self,
        entity_id: str,
        country_code: str,
        certification: str,
        smart_building_tier: str,
        base_value: float,
        base_noi: float,
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply green premium, climate zone adjustment, and smart building
        score to property valuation.

        Transformations:
          1. ESG: value_adj = value × (1 + green_premium_pct / 100)
          2. Geo: climate_zone_adj = (100 - sov_risk) / 100  (proxy for resilience)
          3. Tech: smart_uplift = smart_building_uplift[tier] / 100
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: green premium
        green_pct = GREEN_PREMIUM_PCT.get(certification, 0.0)
        value_esg = base_value * (1 + green_pct / 100)
        esg_f = FactorScore("esg", "green_premium", green_pct, green_pct,
                            "pct", "JLL/CBRE 2024", 0.82)
        audit.append(f"ESG: value {base_value:,.0f} × (1 + {green_pct:.1f}%) = {value_esg:,.0f}")

        # Geo: climate zone / resilience (using sovereign risk as proxy)
        sov = self._lookup(SOVEREIGN_RISK_SCORES, country_code, 30.0)
        resilience = (100 - sov) / 100
        value_geo = value_esg * resilience
        geo_f = FactorScore("geopolitical", "climate_zone_adjustment", resilience,
                            resilience - 1.0, "multiplier", "Maplecroft 2024", 0.65)
        audit.append(f"Geo: resilience={resilience:.3f}, value={value_geo:,.0f}")

        # Tech: smart building
        smart_pct = SMART_BUILDING_UPLIFT.get(smart_building_tier, 0.0)
        value_final = value_geo * (1 + smart_pct / 100)
        tech_f = FactorScore("technology", "smart_building_score", smart_pct,
                             smart_pct, "pct", "CBRE PropTech 2024", 0.72)
        audit.append(f"Tech: smart {smart_pct:.1f}%, value={value_final:,.0f}")

        noi_adj = base_noi * (value_final / base_value) if base_value else base_noi

        if green_pct < 0:
            warnings.append(f"Negative green premium ({green_pct}%) — poor EPC rating")

        return OverlayResult(
            entity_id=entity_id, module_id="real_estate_valuation_engine",
            overlay_type="real_estate_valuation",
            base_metrics={"value": base_value, "noi": base_noi},
            enhanced_metrics={"value": value_final, "noi": noi_adj,
                              "green_premium_pct": green_pct, "smart_uplift_pct": smart_pct},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=value_final / base_value if base_value else 1.0,
            confidence=0.75, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.10  Energy — Strategy: Transition pathway optimisation
    # ---------------------------------------------------------------
    def overlay_energy_strategy(
        self,
        entity_id: str,
        country_code: str,
        base_generation_gwh: float,
        base_co2_intensity: float,
        h2_pathway: str = "grey_h2",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply methane abatement curve, energy independence factor,
        and H2 blending economics.

        Transformations:
          1. ESG: abatement_potential = weighted sum of abatement techs
          2. Geo: independence = energy_independence[country] / 100
          3. Tech: h2_premium = h2_blending_economics[pathway]
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: methane abatement
        total_potential = sum(v["potential_pct"] for v in METHANE_ABATEMENT_CURVE.values())
        weighted_cost = sum(v["cost_per_tco2e"] * v["potential_pct"]
                           for v in METHANE_ABATEMENT_CURVE.values()) / total_potential
        co2_reduction = base_co2_intensity * total_potential
        co2_adj = base_co2_intensity - co2_reduction
        esg_f = FactorScore("esg", "methane_abatement_curve", total_potential,
                            -co2_reduction, "tCO2e/GWh", "IEA GMT 2024", 0.78)
        audit.append(f"ESG: abatement potential={total_potential:.2f}, weighted cost={weighted_cost:.1f} $/tCO2e")
        audit.append(f"  CO2 intensity {base_co2_intensity:.1f} → {co2_adj:.1f} tCO2e/GWh")

        # Geo: energy independence
        indep = self._lookup(ENERGY_INDEPENDENCE, country_code, 50.0)
        indep_score = indep / 100
        geo_f = FactorScore("geopolitical", "energy_independence", indep,
                            indep_score, "score", "IEA WEO 2024", 0.75)
        audit.append(f"Geo: energy independence = {indep:.0f}%")

        # Tech: H2 blending
        h2 = H2_BLENDING_ECONOMICS.get(h2_pathway, H2_BLENDING_ECONOMICS["grey_h2"])
        h2_premium = h2["cost_premium"]
        h2_co2_red = h2["co2_reduction_pct"]
        tech_f = FactorScore("technology", "h2_blending_economics", h2_premium,
                             h2_co2_red, "pct", "IRENA 2024", 0.65)
        audit.append(f"Tech: H2 pathway={h2_pathway}, premium={h2_premium:.0f} $/MWh, CO2 reduction={h2_co2_red:.0%}")

        co2_final = co2_adj * (1 - h2_co2_red)

        return OverlayResult(
            entity_id=entity_id, module_id="scenario_analysis_engine",
            overlay_type="energy_strategy",
            base_metrics={"generation_gwh": base_generation_gwh,
                          "co2_intensity": base_co2_intensity},
            enhanced_metrics={"co2_intensity_adjusted": co2_final,
                              "abatement_potential_pct": total_potential,
                              "h2_cost_premium_mwh": h2_premium,
                              "energy_independence_pct": indep},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=co2_final / base_co2_intensity if base_co2_intensity else 1.0,
            confidence=0.70, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.11  Agriculture — Finance: Sustainable agriculture finance
    # ---------------------------------------------------------------
    def overlay_agriculture_finance(
        self,
        entity_id: str,
        country_code: str,
        certification: str,
        base_loan_value: float,
        precision_ag_level: str = "conventional",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply deforestation-free certification premium, food security
        index, and precision agriculture adoption uplift.

        Transformations:
          1. ESG: cert_premium = deforestation_free_premium[cert] / 100
          2. Geo: food_risk = food_security_index[country] / 100
          3. Tech: yield_uplift = precision_ag_adoption[level] / 100
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # ESG: deforestation-free certification
        cert_prem = DEFORESTATION_FREE_PREMIUM.get(certification, 0.0)
        value_adj = base_loan_value * (1 + cert_prem / 100)
        esg_f = FactorScore("esg", "deforestation_free_cert", cert_prem,
                            cert_prem, "pct", "RSPO/FSC 2024", 0.75)
        audit.append(f"ESG: cert={certification}, premium={cert_prem:.1f}%, value={value_adj:,.0f}")

        # Geo: food security risk
        fs = self._lookup(FOOD_SECURITY_INDEX, country_code, 40.0)
        food_risk = fs / 100
        risk_discount = 1 - food_risk * 0.1  # max 10% discount for food insecure regions
        value_geo = value_adj * risk_discount
        geo_f = FactorScore("geopolitical", "food_security_index", fs,
                            risk_discount - 1.0, "multiplier", "EIU GFS 2024", 0.72)
        audit.append(f"Geo: food security={fs:.0f}, risk discount={risk_discount:.3f}")

        # Tech: precision agriculture
        yield_pct = PRECISION_AG_ADOPTION.get(precision_ag_level, 0.0)
        value_final = value_geo * (1 + yield_pct / 100)
        tech_f = FactorScore("technology", "precision_ag_adoption", yield_pct,
                             yield_pct, "pct", "FAO 2024", 0.68)
        audit.append(f"Tech: precision={precision_ag_level}, yield uplift={yield_pct:.1f}%")

        if fs > 55:
            warnings.append(f"High food insecurity ({fs:.0f}) for {country_code}")

        return OverlayResult(
            entity_id=entity_id, module_id="agriculture_risk_calculator",
            overlay_type="agriculture_finance",
            base_metrics={"loan_value": base_loan_value},
            enhanced_metrics={"loan_value": value_final, "cert_premium_pct": cert_prem,
                              "food_security_score": fs, "yield_uplift_pct": yield_pct},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=value_final / base_loan_value if base_loan_value else 1.0,
            confidence=0.70, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # 5.12  Geopolitical — Advisory: Integrated trade risk
    # ---------------------------------------------------------------
    def overlay_trade_advisory(
        self,
        entity_id: str,
        country_code: str,
        sector_nace: str,
        base_trade_value: float,
        supply_chain_digital_level: str = "paper_hybrid",
        as_of_date: Optional[str] = None,
    ) -> OverlayResult:
        """
        Apply carbon border alignment, sanctions cascade,
        and supply chain digitisation to trade risk.

        Transformations:
          1. ESG: cbam_exposure = (1 - carbon_border_alignment[country]) × transition_mult
          2. Geo: sanctions_prob = sanctions_cascade[country][sector] or 0
          3. Tech: digital_efficiency = supply_chain_digitisation[level]
        """
        audit = []
        warnings = []
        _date = as_of_date or str(date.today())

        # Determine region key for carbon border
        region = country_code
        if country_code in ("DE", "FR", "NL", "SE", "NO", "PL", "CZ", "HU", "RO", "BG",
                            "IT", "ES", "PT", "AT", "BE", "IE", "FI", "DK", "LU", "GR",
                            "HR", "SK", "SI", "LT", "LV", "EE", "CY", "MT"):
            region = "EU"

        # ESG: carbon border alignment
        cba = CARBON_BORDER_ALIGNMENT.get(region, CARBON_BORDER_ALIGNMENT.get("other", 0.15))
        transition_mult = ESG_TRANSITION_PD_MULTIPLIER.get(sector_nace, 1.0)
        cbam_exposure = (1 - cba) * (transition_mult - 1.0)  # exposure only for risky sectors
        esg_f = FactorScore("esg", "carbon_border_alignment", cba,
                            cbam_exposure, "pct", "EU CBAM 2024", 0.80)
        audit.append(f"ESG: CBA={cba:.2f}, transition mult={transition_mult:.2f}, CBAM exposure={cbam_exposure:.4f}")

        # Geo: sanctions cascade
        sanctions_map = SANCTIONS_CASCADE.get(country_code, {})
        sanc_prob = sanctions_map.get(sector_nace, 0.0)
        sanc_discount = 1 - sanc_prob * 0.5  # up to 50% value-at-risk from sanctions
        value_geo = base_trade_value * sanc_discount
        geo_f = FactorScore("geopolitical", "sanctions_cascade", sanc_prob,
                            sanc_discount - 1.0, "multiplier", "OFAC/EU 2024", 0.85)
        audit.append(f"Geo: sanctions prob={sanc_prob:.2f}, discount={sanc_discount:.3f}")

        # Tech: supply chain digitisation
        digital_eff = SUPPLY_CHAIN_DIGITISATION.get(supply_chain_digital_level, 0.25)
        efficiency_gain = digital_eff * 0.05  # max 4.25% cost reduction
        value_final = value_geo * (1 + efficiency_gain)
        tech_f = FactorScore("technology", "supply_chain_digitisation", digital_eff,
                             efficiency_gain, "pct", "WTO DT 2024", 0.72)
        audit.append(f"Tech: digitisation={digital_eff:.2f}, efficiency gain={efficiency_gain:.4f}")

        if sanc_prob > 0.3:
            warnings.append(f"Significant sanctions risk ({sanc_prob:.0%}) for {country_code}/{sector_nace}")

        return OverlayResult(
            entity_id=entity_id, module_id="china_trade_engine",
            overlay_type="trade_advisory",
            base_metrics={"trade_value": base_trade_value},
            enhanced_metrics={"trade_value": value_final, "cbam_exposure": cbam_exposure,
                              "sanctions_probability": sanc_prob, "digital_efficiency": digital_eff},
            esg_factors=[esg_f], geo_factors=[geo_f], tech_factors=[tech_f],
            composite_adjustment=value_final / base_trade_value if base_trade_value else 1.0,
            confidence=0.76, warnings=warnings, audit_trail=audit, as_of_date=_date,
        )

    # ---------------------------------------------------------------
    # Universal: multi-factor overlay summary
    # ---------------------------------------------------------------
    def get_factor_summary(
        self,
        country_code: str,
        sector_nace: str,
    ) -> dict:
        """
        Return a high-level summary of all factor scores for a
        country/sector combination without applying to specific metrics.
        """
        return {
            "country_code": country_code,
            "sector_nace": sector_nace,
            "esg_factors": {
                "transition_pd_multiplier": ESG_TRANSITION_PD_MULTIPLIER.get(sector_nace, 1.0),
                "alpha_decomposition_total": sum(
                    ESG_ALPHA_DECOMPOSITION[p].get(sector_nace, 0.03) for p in ("E", "S", "G")
                ),
            },
            "geopolitical_factors": {
                "sovereign_risk": self._lookup(SOVEREIGN_RISK_SCORES, country_code, 50.0),
                "political_stability": self._lookup(POLITICAL_STABILITY, country_code, 40.0),
                "food_security": self._lookup(FOOD_SECURITY_INDEX, country_code, 40.0),
                "energy_independence": self._lookup(ENERGY_INDEPENDENCE, country_code, 50.0),
                "fx_climate_correlation": self._lookup(FX_CLIMATE_CORRELATION, country_code, 0.10),
            },
            "technology_factors": {
                "automation_disruption": AUTOMATION_DISRUPTION.get(sector_nace, 0.3),
                "ai_adoption": AI_ADOPTION_SCORE.get(sector_nace, 0.3),
                "digital_readiness": self._lookup(DIGITAL_READINESS, country_code, 50.0),
            },
        }

    def get_available_overlays(self) -> list[dict]:
        """Return metadata for every overlay method."""
        return [
            {"id": "ecl_credit", "label": "Bank Credit — Climate-adjusted ECL",
             "module": "ecl_climate_engine", "fi_type": "Bank", "lob": "Credit"},
            {"id": "alm_treasury", "label": "Bank Treasury — ALM ESG/Macro",
             "module": "scenario_analysis_engine", "fi_type": "Bank", "lob": "Treasury"},
            {"id": "regulatory_compliance", "label": "Bank Compliance — Multi-jurisdiction",
             "module": "csrd_auto_populate", "fi_type": "Bank", "lob": "Compliance"},
            {"id": "insurance_uw", "label": "Insurer UW — P&C Technical Pricing",
             "module": "insurance_risk_engine", "fi_type": "Insurer", "lob": "UW"},
            {"id": "insurance_actuarial", "label": "Insurer Actuarial — Life Reserves",
             "module": "insurance_risk_engine", "fi_type": "Insurer", "lob": "Actuarial"},
            {"id": "portfolio_management", "label": "AM PM — ESG Alpha Decomposition",
             "module": "portfolio_analytics", "fi_type": "AM", "lob": "PM"},
            {"id": "risk_management", "label": "AM Risk — Enhanced Risk Reporting",
             "module": "portfolio_analytics", "fi_type": "AM", "lob": "Risk"},
            {"id": "pe_deal", "label": "PE Deals — ESG Deal Scoring",
             "module": "pe_deal_engine", "fi_type": "PE", "lob": "Deals"},
            {"id": "real_estate_valuation", "label": "RE Valuations — Green Premium",
             "module": "real_estate_valuation_engine", "fi_type": "RE", "lob": "Valuations"},
            {"id": "energy_strategy", "label": "Energy Strategy — Transition Pathway",
             "module": "scenario_analysis_engine", "fi_type": "Energy", "lob": "Strategy"},
            {"id": "agriculture_finance", "label": "Agriculture Finance — Sustainable Ag",
             "module": "agriculture_risk_calculator", "fi_type": "Agriculture", "lob": "Finance"},
            {"id": "trade_advisory", "label": "Geopolitical Advisory — Trade Risk",
             "module": "china_trade_engine", "fi_type": "Geopolitical", "lob": "Advisory"},
        ]

    def get_factor_registries(self) -> dict:
        """Return all factor registry metadata for data lineage tracing."""
        return {
            "esg_registries": {
                "ESG_TRANSITION_PD_MULTIPLIER": {"sectors": len(ESG_TRANSITION_PD_MULTIPLIER), "source": "PRI IPR 2024"},
                "GREEN_BOND_PREMIUM_BPS": {"tiers": len(GREEN_BOND_PREMIUM_BPS), "source": "CBI 2024"},
                "BIODIVERSITY_NATCAT_AMPLIFIER": {"biomes": len(BIODIVERSITY_NATCAT_AMPLIFIER), "source": "IPBES 2024"},
                "ESG_ALPHA_DECOMPOSITION": {"pillars": 3, "sectors": 11, "source": "MSCI 2024"},
                "AIR_QUALITY_MORTALITY": {"bands": len(AIR_QUALITY_MORTALITY), "source": "WHO 2021"},
                "CARBON_REDUCTION_VALUATION_UPLIFT": {"bands": len(CARBON_REDUCTION_VALUATION_UPLIFT), "source": "BCG 2024"},
                "GREEN_PREMIUM_PCT": {"certs": len(GREEN_PREMIUM_PCT), "source": "JLL/CBRE 2024"},
                "METHANE_ABATEMENT_CURVE": {"techs": len(METHANE_ABATEMENT_CURVE), "source": "IEA GMT 2024"},
                "DEFORESTATION_FREE_PREMIUM": {"certs": len(DEFORESTATION_FREE_PREMIUM), "source": "RSPO/FSC 2024"},
                "CSRD_GAP_CLOSURE_RATES": {"pillars": len(CSRD_GAP_CLOSURE_RATES), "source": "CSRD IG 2024"},
            },
            "geopolitical_registries": {
                "SOVEREIGN_RISK_SCORES": {"countries": len(SOVEREIGN_RISK_SCORES), "source": "WB WGI 2024"},
                "FX_CLIMATE_CORRELATION": {"countries": len(FX_CLIMATE_CORRELATION), "source": "BIS 2024"},
                "SANCTIONS_CASCADE": {"countries": len(SANCTIONS_CASCADE), "source": "OFAC/EU 2024"},
                "POLITICAL_STABILITY": {"countries": len(POLITICAL_STABILITY), "source": "FFP FSI 2024"},
                "FOOD_SECURITY_INDEX": {"countries": len(FOOD_SECURITY_INDEX), "source": "EIU 2024"},
                "ENERGY_INDEPENDENCE": {"countries": len(ENERGY_INDEPENDENCE), "source": "IEA WEO 2024"},
                "REGULATORY_COMPLEXITY": {"jurisdictions": len(REGULATORY_COMPLEXITY), "source": "Multi-reg 2024"},
                "MIGRATION_MORTALITY_ADJUSTMENT": {"patterns": len(MIGRATION_MORTALITY_ADJUSTMENT), "source": "UN Pop 2024"},
                "CARBON_BORDER_ALIGNMENT": {"regions": len(CARBON_BORDER_ALIGNMENT), "source": "EU CBAM 2024"},
            },
            "technology_registries": {
                "AUTOMATION_DISRUPTION": {"sectors": len(AUTOMATION_DISRUPTION), "source": "McKinsey 2024"},
                "FINTECH_NIM_DISRUPTION": {"segments": len(FINTECH_NIM_DISRUPTION), "source": "McKinsey 2024"},
                "AI_ADOPTION_SCORE": {"sectors": len(AI_ADOPTION_SCORE), "source": "WIPO GII 2024"},
                "SMART_BUILDING_UPLIFT": {"tiers": len(SMART_BUILDING_UPLIFT), "source": "CBRE 2024"},
                "DIGITAL_READINESS": {"countries": len(DIGITAL_READINESS), "source": "IMD 2024"},
                "PARAMETRIC_PRICING_ADJ": {"triggers": len(PARAMETRIC_PRICING_ADJ), "source": "Swiss Re 2024"},
                "H2_BLENDING_ECONOMICS": {"pathways": len(H2_BLENDING_ECONOMICS), "source": "IRENA 2024"},
                "PRECISION_AG_ADOPTION": {"levels": len(PRECISION_AG_ADOPTION), "source": "FAO 2024"},
                "SUPPLY_CHAIN_DIGITISATION": {"levels": len(SUPPLY_CHAIN_DIGITISATION), "source": "WTO 2024"},
                "AI_ASSURANCE_CONFIDENCE": {"levels": len(AI_ASSURANCE_CONFIDENCE), "source": "Big4 2024"},
                "MEDICAL_ADVANCEMENT_LONGEVITY": {"techs": len(MEDICAL_ADVANCEMENT_LONGEVITY), "source": "Lancet 2024"},
                "STRANDED_ASSET_TECH_FILTER": {"techs": len(STRANDED_ASSET_TECH_FILTER), "source": "IEA WEO 2024"},
            },
        }
