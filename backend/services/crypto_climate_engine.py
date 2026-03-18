"""
E76 — Digital Assets & Crypto Climate Risk Engine
==================================================
Covers:
  - Cambridge CBECI methodology (Bitcoin energy estimation)
  - Consensus mechanism GHG intensity (PoW / PoS / DPoS / PoA / PoH)
  - Mining geography energy mix (15 country profiles)
  - EU MiCA Regulation 2023/1114 Art 66 sustainability indicators
  - Tokenised Green Assets (RWA) — green bond / carbon credit tokenisation
  - PCAF Emerging Methodology for Crypto financed emissions
  - DeFi Protocol Carbon Intensity
  - Crypto Portfolio Assessment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Module-level reference data
# ---------------------------------------------------------------------------

# Consensus mechanism GHG intensity (gCO2e per transaction)
# Sources: Cambridge CBECI (PoW), Ethereum Foundation post-Merge (PoS),
#          academic estimates for DPoS/PoA/PoH.
CONSENSUS_GHG_INTENSITY: Dict[str, Dict[str, Any]] = {
    "PoW": {
        "label": "Proof of Work",
        "representative_assets": ["BTC", "LTC", "XMR"],
        "gco2e_per_tx_low": 300.0,
        "gco2e_per_tx_central": 600.0,
        "gco2e_per_tx_high": 900.0,
        "energy_per_tx_kwh_central": 1.2,
        "source": "Cambridge CBECI 2024",
        "notes": (
            "BTC central estimate ~600 gCO2e/tx based on annualised "
            "network consumption ~120 TWh/yr and ~300M tx/yr."
        ),
    },
    "PoS": {
        "label": "Proof of Stake",
        "representative_assets": ["ETH", "ADA", "DOT", "SOL"],
        "gco2e_per_tx_low": 0.005,
        "gco2e_per_tx_central": 0.01,
        "gco2e_per_tx_high": 0.05,
        "energy_per_tx_kwh_central": 0.000035,
        "source": "Ethereum Foundation 2023 (post-Merge)",
        "notes": "ETH reduced energy consumption ~99.95% after the Merge (Sept 2022).",
    },
    "DPoS": {
        "label": "Delegated Proof of Stake",
        "representative_assets": ["EOS", "TRX", "STEEM"],
        "gco2e_per_tx_low": 0.001,
        "gco2e_per_tx_central": 0.01,
        "gco2e_per_tx_high": 0.05,
        "energy_per_tx_kwh_central": 0.000030,
        "source": "Academic estimates 2022-2024",
        "notes": "Small validator set reduces energy vs broad PoS.",
    },
    "PoA": {
        "label": "Proof of Authority",
        "representative_assets": ["VET", "XDAI", "BSC_validators"],
        "gco2e_per_tx_low": 0.001,
        "gco2e_per_tx_central": 0.005,
        "gco2e_per_tx_high": 0.02,
        "energy_per_tx_kwh_central": 0.000015,
        "source": "Network operator disclosures",
        "notes": "Permissioned validator set; very low per-tx footprint.",
    },
    "PoH": {
        "label": "Proof of History (Solana variant)",
        "representative_assets": ["SOL"],
        "gco2e_per_tx_low": 0.0005,
        "gco2e_per_tx_central": 0.002,
        "gco2e_per_tx_high": 0.01,
        "energy_per_tx_kwh_central": 0.000006,
        "source": "Solana Foundation Energy Use Report 2023",
        "notes": "Solana Foundation reports ~0.00051 kWh/tx.",
    },
}

# Mining geography profiles — renewable share and grid carbon intensity
# Sources: IEA 2023, Ember Climate 2024, Cambridge Centre for Alternative Finance
MINING_COUNTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "US": {
        "name": "United States",
        "renewable_pct": 25.0,
        "grid_carbon_intensity_gco2_kwh": 386.0,
        "mining_share_pct": 38.0,  # % of global BTC hashrate
        "primary_energy_sources": ["natural_gas", "coal", "nuclear", "wind", "hydro"],
        "source": "EIA 2023 / CCAF 2024",
    },
    "CN": {
        "name": "China",
        "renewable_pct": 40.0,
        "grid_carbon_intensity_gco2_kwh": 580.0,
        "mining_share_pct": 21.0,
        "primary_energy_sources": ["coal", "hydro", "wind", "solar"],
        "source": "NEA 2023 / CCAF 2024",
        "notes": "Banned in 2021 but activity persists; mix varies by season.",
    },
    "KZ": {
        "name": "Kazakhstan",
        "renewable_pct": 8.0,
        "grid_carbon_intensity_gco2_kwh": 682.0,
        "mining_share_pct": 13.0,
        "primary_energy_sources": ["coal", "natural_gas"],
        "source": "KEGOC 2023 / CCAF 2024",
    },
    "RU": {
        "name": "Russia",
        "renewable_pct": 18.0,
        "grid_carbon_intensity_gco2_kwh": 451.0,
        "mining_share_pct": 9.0,
        "primary_energy_sources": ["natural_gas", "nuclear", "hydro", "coal"],
        "source": "Rosenergoatom 2023",
    },
    "CA": {
        "name": "Canada",
        "renewable_pct": 60.0,
        "grid_carbon_intensity_gco2_kwh": 150.0,
        "mining_share_pct": 6.5,
        "primary_energy_sources": ["hydro", "nuclear", "natural_gas"],
        "source": "Canada Energy Regulator 2023",
    },
    "IS": {
        "name": "Iceland",
        "renewable_pct": 99.0,
        "grid_carbon_intensity_gco2_kwh": 28.0,
        "mining_share_pct": 2.0,
        "primary_energy_sources": ["geothermal", "hydro"],
        "source": "Landsvirkjun 2023",
    },
    "NO": {
        "name": "Norway",
        "renewable_pct": 97.0,
        "grid_carbon_intensity_gco2_kwh": 18.0,
        "mining_share_pct": 1.5,
        "primary_energy_sources": ["hydro", "wind"],
        "source": "Statnett 2023",
    },
    "SE": {
        "name": "Sweden",
        "renewable_pct": 97.0,
        "grid_carbon_intensity_gco2_kwh": 13.0,
        "mining_share_pct": 1.0,
        "primary_energy_sources": ["hydro", "nuclear", "wind"],
        "source": "Energimyndigheten 2023",
    },
    "DE": {
        "name": "Germany",
        "renewable_pct": 46.0,
        "grid_carbon_intensity_gco2_kwh": 311.0,
        "mining_share_pct": 1.2,
        "primary_energy_sources": ["wind", "solar", "natural_gas", "coal"],
        "source": "Bundesnetzagentur 2023",
    },
    "IE": {
        "name": "Ireland",
        "renewable_pct": 42.0,
        "grid_carbon_intensity_gco2_kwh": 303.0,
        "mining_share_pct": 0.5,
        "primary_energy_sources": ["wind", "natural_gas"],
        "source": "Eirgrid 2023",
    },
    "FR": {
        "name": "France",
        "renewable_pct": 90.0,
        "grid_carbon_intensity_gco2_kwh": 56.0,
        "mining_share_pct": 0.8,
        "primary_energy_sources": ["nuclear", "hydro", "wind"],
        "source": "RTE 2023",
    },
    "AU": {
        "name": "Australia",
        "renewable_pct": 30.0,
        "grid_carbon_intensity_gco2_kwh": 620.0,
        "mining_share_pct": 0.8,
        "primary_energy_sources": ["coal", "natural_gas", "solar", "wind"],
        "source": "AEMO 2023",
    },
    "MY": {
        "name": "Malaysia",
        "renewable_pct": 22.0,
        "grid_carbon_intensity_gco2_kwh": 571.0,
        "mining_share_pct": 0.7,
        "primary_energy_sources": ["natural_gas", "coal", "hydro"],
        "source": "Suruhanjaya Tenaga 2023",
    },
    "SG": {
        "name": "Singapore",
        "renewable_pct": 37.0,
        "grid_carbon_intensity_gco2_kwh": 380.0,
        "mining_share_pct": 0.4,
        "primary_energy_sources": ["natural_gas", "solar"],
        "source": "EMA 2023",
    },
    "other": {
        "name": "Rest of World",
        "renewable_pct": 35.0,
        "grid_carbon_intensity_gco2_kwh": 450.0,
        "mining_share_pct": 3.6,
        "primary_energy_sources": ["mixed"],
        "source": "CCAF weighted average",
    },
}

# EU MiCA Regulation 2023/1114 — Art 66 sustainability requirements
MICA_REQUIREMENTS: Dict[str, Any] = {
    "regulation": "EU MiCA Regulation (EU) 2023/1114",
    "article": "Article 66",
    "effective_date": "2024-12-30",
    "competent_authority": "European Securities and Markets Authority (ESMA)",
    "compliance_levels": {
        "basic": {
            "label": "Basic Disclosure",
            "threshold_market_cap_eur": None,  # applies to all issuers
            "requirements": [
                "energy_consumption_annual_disclosure",
                "renewable_energy_pct_disclosure",
                "consensus_mechanism_description",
            ],
            "frequency": "annual",
            "format": "white_paper_annex",
        },
        "enhanced": {
            "label": "Enhanced Reporting",
            "threshold_market_cap_eur": 100_000_000,  # >€100M market cap
            "requirements": [
                "energy_consumption_annual_disclosure",
                "renewable_energy_pct_disclosure",
                "consensus_mechanism_description",
                "ghg_emissions_scope1_scope2",
                "environmental_impact_assessment",
                "waste_electrical_equipment_disclosure",
            ],
            "frequency": "annual",
            "format": "standalone_sustainability_report",
        },
        "full": {
            "label": "Full Sustainability Indicators",
            "threshold_market_cap_eur": 500_000_000,  # >€500M market cap
            "requirements": [
                "energy_consumption_annual_disclosure",
                "renewable_energy_pct_disclosure",
                "consensus_mechanism_description",
                "ghg_emissions_scope1_scope2",
                "environmental_impact_assessment",
                "waste_electrical_equipment_disclosure",
                "water_consumption_disclosure",
                "biodiversity_impact_assessment",
                "scope3_value_chain_emissions",
                "paris_alignment_statement",
                "third_party_assurance",
            ],
            "frequency": "annual",
            "format": "standalone_sustainability_report_assured",
        },
    },
    "esma_technical_standards": "RTS under Art 66(5) — expected Q1 2025",
    "cross_reference": {
        "CSRD": "ESRS E1 GHG emissions, E2 pollution",
        "EU_Taxonomy": "Do No Significant Harm — climate change mitigation",
        "SFDR": "PAI indicator 14 (exposure to controversial weapons) — analogy",
    },
}

# ---------------------------------------------------------------------------
# Cambridge CBECI constants
# ---------------------------------------------------------------------------
# Annualised Bitcoin network consumption assumptions (TWh/yr, Q1 2024 estimate)
CBECI_NETWORK_TWH_CENTRAL = 120.0
CBECI_NETWORK_TWH_LOW = 80.0
CBECI_NETWORK_TWH_HIGH = 180.0

# Assumed hardware efficiency bounds (J/TH) for lower/central/upper estimates
CBECI_EFFICIENCY_LOW_J_TH = 20.0    # best available ASIC (e.g., Antminer S19 XP)
CBECI_EFFICIENCY_CENTRAL_J_TH = 40.0
CBECI_EFFICIENCY_HIGH_J_TH = 80.0   # older hardware still in service

# Bitcoin annual transactions (approx)
BTC_ANNUAL_TX = 300_000_000


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CryptoAssetInput:
    """Input for a single crypto asset climate assessment."""
    asset_symbol: str                       # e.g. "BTC", "ETH", "SOL"
    consensus_mechanism: str                # "PoW" | "PoS" | "DPoS" | "PoA" | "PoH"
    annual_transaction_count: Optional[float] = None  # override network default
    network_energy_twh_yr: Optional[float] = None     # override CBECI default
    mining_country_distribution: Optional[Dict[str, float]] = None  # {country_code: pct}
    market_cap_usd: Optional[float] = None
    outstanding_value_usd: Optional[float] = None     # for PCAF financed emissions
    # MiCA fields
    issuer_incorporated_eu: bool = False
    has_white_paper: bool = False
    discloses_energy_consumption: bool = False
    discloses_renewable_pct: bool = False
    discloses_ghg_emissions: bool = False
    # Tokenised RWA fields
    is_tokenised_green_asset: bool = False
    underlying_asset_type: Optional[str] = None  # "green_bond" | "carbon_credit" | "green_certificate"
    underlying_face_value_usd: Optional[float] = None
    on_chain_verification: bool = False
    certification_standard: Optional[str] = None  # "ICMA_GBP" | "EU_GBS" | "VCS" | "Art6_ITMO"


@dataclass
class MiningGeographyInput:
    """Input for a mining geography carbon footprint assessment."""
    hashrate_eh_s: float                    # Exahash per second
    country_distribution: Dict[str, float]  # {country_code: pct_of_hashrate}
    hardware_efficiency_j_th: float = 40.0  # Joules per TeraHash
    assessment_year: int = 2024


@dataclass
class CryptoPortfolioInput:
    """Input for a multi-asset crypto portfolio assessment."""
    portfolio_id: str
    holdings: List[Dict[str, Any]]          # list of {symbol, consensus, value_usd, ...}
    total_portfolio_value_usd: float
    investor_name: Optional[str] = None
    reporting_period: str = "2024"
    include_defi_protocols: bool = False
    defi_tvl_usd: Optional[float] = None


@dataclass
class CryptoClimateResult:
    """Result of a single crypto asset climate assessment."""
    asset_symbol: str
    consensus_mechanism: str
    # Energy
    network_energy_twh_yr_low: float
    network_energy_twh_yr_central: float
    network_energy_twh_yr_high: float
    energy_per_tx_kwh: float
    # Emissions
    gco2e_per_tx_low: float
    gco2e_per_tx_central: float
    gco2e_per_tx_high: float
    annual_network_tco2e: float
    # Geography
    effective_renewable_pct: float
    effective_grid_carbon_gco2_kwh: float
    # Compliance
    mica_compliance_level: str          # "basic" | "enhanced" | "full" | "non_compliant"
    mica_score: float                   # 0-100
    mica_gaps: List[str]
    # Tokenised green asset
    tokenisation_premium_bps: Optional[float]
    green_asset_verified: bool
    # PCAF
    financed_emissions_tco2e: Optional[float]
    pcaf_dqs: int                       # 3 or 4
    # Summary
    climate_risk_tier: str              # "very_high" | "high" | "medium" | "low"
    summary: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CryptoClimateEngine:
    """
    Digital Assets & Crypto Climate Risk Engine (E76).

    Implements Cambridge CBECI methodology, EU MiCA Art 66, PCAF crypto
    financed emissions, and tokenised green asset (RWA) assessment.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess_crypto_asset(self, asset_input: CryptoAssetInput) -> CryptoClimateResult:
        """
        Full climate assessment for a single crypto asset.

        Combines energy estimation, GHG intensity, geography-adjusted
        emissions, MiCA compliance, and optional PCAF financed emissions.
        """
        mechanism = asset_input.consensus_mechanism
        ghg_profile = CONSENSUS_GHG_INTENSITY.get(mechanism, CONSENSUS_GHG_INTENSITY["PoS"])

        # 1. Network energy (TWh/yr)
        if asset_input.network_energy_twh_yr is not None:
            energy_central = asset_input.network_energy_twh_yr
            energy_low = energy_central * 0.65
            energy_high = energy_central * 1.5
        elif mechanism == "PoW":
            energy_low = CBECI_NETWORK_TWH_LOW
            energy_central = CBECI_NETWORK_TWH_CENTRAL
            energy_high = CBECI_NETWORK_TWH_HIGH
        else:
            # PoS and others have dramatically lower energy
            factor = {"PoS": 0.0008, "DPoS": 0.0005, "PoA": 0.0003, "PoH": 0.0002}.get(mechanism, 0.001)
            energy_central = CBECI_NETWORK_TWH_CENTRAL * factor
            energy_low = energy_central * 0.7
            energy_high = energy_central * 1.4

        # 2. Geography-adjusted grid carbon intensity
        eff_renewable, eff_grid_carbon = self._geography_adjusted_intensity(
            asset_input.mining_country_distribution
        )

        # 3. Annual network tCO2e
        # energy_central in TWh → convert to kWh → multiply by gCO2/kWh → convert to tCO2e
        annual_tco2e = (energy_central * 1e9) * (eff_grid_carbon / 1e6)

        # 4. Per-transaction energy and emissions
        tx_count = asset_input.annual_transaction_count
        if tx_count is None:
            tx_count = BTC_ANNUAL_TX if mechanism == "PoW" else 1_000_000_000

        energy_per_tx_kwh = (energy_central * 1e9) / tx_count if tx_count > 0 else 0.0
        gco2e_central = energy_per_tx_kwh * eff_grid_carbon
        gco2e_low = gco2e_central * 0.5
        gco2e_high = gco2e_central * 1.5

        # Clamp to consensus-level reference bounds for plausibility
        ref_low = ghg_profile["gco2e_per_tx_low"]
        ref_high = ghg_profile["gco2e_per_tx_high"]
        gco2e_central = max(ref_low, min(gco2e_central, ref_high))

        # 5. MiCA compliance
        mica_result = self.check_mica_compliance(asset_input)
        mica_level = mica_result["compliance_level"]
        mica_score = mica_result["score"]
        mica_gaps = mica_result["gaps"]

        # 6. Tokenised green asset
        token_premium = None
        green_verified = False
        if asset_input.is_tokenised_green_asset:
            token_result = self.assess_tokenised_green_asset(asset_input)
            token_premium = token_result.get("tokenisation_premium_bps")
            green_verified = token_result.get("verification_status") == "verified"

        # 7. PCAF financed emissions
        financed_tco2e = None
        pcaf_dqs = 4
        if asset_input.outstanding_value_usd and asset_input.market_cap_usd:
            pcaf_result = self._compute_pcaf_single(
                outstanding_value=asset_input.outstanding_value_usd,
                market_cap=asset_input.market_cap_usd,
                network_energy_twh=energy_central,
                grid_factor_gco2_kwh=eff_grid_carbon,
            )
            financed_tco2e = pcaf_result["financed_emissions_tco2e"]
            pcaf_dqs = pcaf_result["dqs"]

        # 8. Climate risk tier
        risk_tier = self._classify_climate_risk(mechanism, eff_grid_carbon, eff_renewable)

        summary = (
            f"{asset_input.asset_symbol} ({mechanism}): "
            f"~{energy_central:.1f} TWh/yr network energy, "
            f"~{gco2e_central:.1f} gCO2e/tx, "
            f"MiCA: {mica_level}, Risk tier: {risk_tier}."
        )

        return CryptoClimateResult(
            asset_symbol=asset_input.asset_symbol,
            consensus_mechanism=mechanism,
            network_energy_twh_yr_low=round(energy_low, 4),
            network_energy_twh_yr_central=round(energy_central, 4),
            network_energy_twh_yr_high=round(energy_high, 4),
            energy_per_tx_kwh=round(energy_per_tx_kwh, 8),
            gco2e_per_tx_low=round(gco2e_low, 4),
            gco2e_per_tx_central=round(gco2e_central, 4),
            gco2e_per_tx_high=round(gco2e_high, 4),
            annual_network_tco2e=round(annual_tco2e, 0),
            effective_renewable_pct=round(eff_renewable, 2),
            effective_grid_carbon_gco2_kwh=round(eff_grid_carbon, 1),
            mica_compliance_level=mica_level,
            mica_score=round(mica_score, 1),
            mica_gaps=mica_gaps,
            tokenisation_premium_bps=token_premium,
            green_asset_verified=green_verified,
            financed_emissions_tco2e=round(financed_tco2e, 2) if financed_tco2e else None,
            pcaf_dqs=pcaf_dqs,
            climate_risk_tier=risk_tier,
            summary=summary,
        )

    def assess_mining_geography(self, geo_input: MiningGeographyInput) -> Dict[str, Any]:
        """
        Carbon footprint of a mining operation based on location distribution.

        Uses hashrate × efficiency to derive annual energy, then weights
        by country grid carbon intensity for total tCO2e/yr.
        """
        # Annualised energy from hashrate
        # hashrate (EH/s) → TH/s → energy in J/s → Watts → kWh/yr → TWh/yr
        hashrate_th_s = geo_input.hashrate_eh_s * 1e6  # EH to TH
        power_watts = hashrate_th_s * geo_input.hardware_efficiency_j_th  # W
        energy_kwh_yr = power_watts * 8_760 / 1_000  # hours per year
        energy_twh_yr = energy_kwh_yr / 1e9

        country_breakdown: List[Dict[str, Any]] = []
        total_tco2e = 0.0
        weighted_renewable = 0.0
        weighted_grid_carbon = 0.0
        total_pct = 0.0

        for country_code, share_pct in geo_input.country_distribution.items():
            profile = MINING_COUNTRY_PROFILES.get(country_code, MINING_COUNTRY_PROFILES["other"])
            country_energy_kwh = energy_kwh_yr * (share_pct / 100.0)
            country_tco2e = country_energy_kwh * profile["grid_carbon_intensity_gco2_kwh"] / 1e6

            country_breakdown.append({
                "country_code": country_code,
                "country_name": profile["name"],
                "share_pct": share_pct,
                "energy_kwh_yr": round(country_energy_kwh, 0),
                "renewable_pct": profile["renewable_pct"],
                "grid_carbon_gco2_kwh": profile["grid_carbon_intensity_gco2_kwh"],
                "tco2e_yr": round(country_tco2e, 2),
            })

            total_tco2e += country_tco2e
            weighted_renewable += profile["renewable_pct"] * share_pct
            weighted_grid_carbon += profile["grid_carbon_intensity_gco2_kwh"] * share_pct
            total_pct += share_pct

        if total_pct > 0:
            weighted_renewable /= total_pct
            weighted_grid_carbon /= total_pct

        # Counterfactual: if fully renewable
        renewable_tco2e = energy_kwh_yr * 28.0 / 1e6  # Iceland-equivalent grid (28 gCO2/kWh)
        avoided_tco2e = total_tco2e - renewable_tco2e

        return {
            "hashrate_eh_s": geo_input.hashrate_eh_s,
            "hardware_efficiency_j_th": geo_input.hardware_efficiency_j_th,
            "annual_energy_kwh_yr": round(energy_kwh_yr, 0),
            "annual_energy_twh_yr": round(energy_twh_yr, 6),
            "total_tco2e_yr": round(total_tco2e, 2),
            "weighted_renewable_pct": round(weighted_renewable, 2),
            "weighted_grid_carbon_gco2_kwh": round(weighted_grid_carbon, 1),
            "country_breakdown": country_breakdown,
            "renewable_counterfactual_tco2e": round(renewable_tco2e, 2),
            "additional_tco2e_vs_renewable": round(avoided_tco2e, 2),
            "assessment_year": geo_input.assessment_year,
            "methodology": "Cambridge CBECI approach: hashrate × efficiency → energy × grid factor",
        }

    def check_mica_compliance(self, asset_input: CryptoAssetInput) -> Dict[str, Any]:
        """
        EU MiCA Regulation 2023/1114 Art 66 compliance check.

        Determines the required compliance level based on market cap and
        scores the issuer against disclosed sustainability indicators.
        """
        market_cap = asset_input.market_cap_usd or 0.0
        market_cap_eur = market_cap * 0.92  # approximate USD→EUR

        # Determine required level
        if market_cap_eur >= 500_000_000:
            required_level = "full"
            required_reqs = MICA_REQUIREMENTS["compliance_levels"]["full"]["requirements"]
        elif market_cap_eur >= 100_000_000:
            required_level = "enhanced"
            required_reqs = MICA_REQUIREMENTS["compliance_levels"]["enhanced"]["requirements"]
        else:
            required_level = "basic"
            required_reqs = MICA_REQUIREMENTS["compliance_levels"]["basic"]["requirements"]

        # Map disclosed attributes to requirements
        disclosed: Dict[str, bool] = {
            "energy_consumption_annual_disclosure": asset_input.discloses_energy_consumption,
            "renewable_energy_pct_disclosure": asset_input.discloses_renewable_pct,
            "consensus_mechanism_description": asset_input.has_white_paper,
            "ghg_emissions_scope1_scope2": asset_input.discloses_ghg_emissions,
            "environmental_impact_assessment": asset_input.discloses_ghg_emissions,
            "waste_electrical_equipment_disclosure": False,  # rarely disclosed
            "water_consumption_disclosure": False,
            "biodiversity_impact_assessment": False,
            "scope3_value_chain_emissions": False,
            "paris_alignment_statement": False,
            "third_party_assurance": False,
        }

        gaps: List[str] = []
        met = 0
        for req in required_reqs:
            if disclosed.get(req, False):
                met += 1
            else:
                gaps.append(req)

        score = (met / len(required_reqs) * 100) if required_reqs else 0.0

        # Determine achieved level
        if score >= 100:
            achieved_level = required_level
        elif score >= 67:
            achieved_level = "partial"
        else:
            achieved_level = "non_compliant"

        return {
            "required_level": required_level,
            "compliance_level": achieved_level,
            "score": round(score, 1),
            "requirements_met": met,
            "requirements_total": len(required_reqs),
            "gaps": gaps,
            "market_cap_eur_approx": round(market_cap_eur, 0),
            "issuer_incorporated_eu": asset_input.issuer_incorporated_eu,
            "regulation": "EU MiCA Regulation (EU) 2023/1114 Art 66",
            "effective_date": "2024-12-30",
        }

    def assess_tokenised_green_asset(self, asset_input: CryptoAssetInput) -> Dict[str, Any]:
        """
        Tokenised Green Assets (RWA) assessment.

        Evaluates tokenisation premium, on-chain verification quality, and
        alignment with green finance standards (ICMA GBP, EU GBS, Art 6 ITMOs).
        """
        underlying = asset_input.underlying_asset_type or "unknown"
        cert_standard = asset_input.certification_standard or "none"

        # Base tokenisation premium by asset type (bps over comparable conventional instrument)
        premium_map = {
            "green_bond": 5.0,          # greenium from DLT efficiency
            "carbon_credit": 20.0,       # liquidity/transparency uplift
            "green_certificate": 10.0,   # REC / REGO tokenised
            "unknown": 0.0,
        }
        base_premium = premium_map.get(underlying, 0.0)

        # Certification quality multiplier
        cert_quality = {
            "ICMA_GBP": 1.0,
            "EU_GBS": 1.2,          # EU GBS 2023/2631 — stricter taxonomy alignment
            "VCS": 0.9,
            "Gold_Standard": 1.0,
            "Art6_ITMO": 1.3,       # Article 6 Paris Agreement ITMOs — highest quality
            "CDM": 0.6,             # legacy, discount
            "none": 0.5,
        }
        quality_mult = cert_quality.get(cert_standard, 0.7)

        # On-chain verification uplift
        verification_uplift = 3.0 if asset_input.on_chain_verification else 0.0
        total_premium = base_premium * quality_mult + verification_uplift

        # Verification status
        if asset_input.on_chain_verification and cert_standard in ("EU_GBS", "Art6_ITMO", "ICMA_GBP"):
            verification_status = "verified"
        elif asset_input.on_chain_verification or cert_standard != "none":
            verification_status = "partial"
        else:
            verification_status = "unverified"

        # Framework alignment
        framework_alignment: List[str] = []
        if cert_standard == "EU_GBS":
            framework_alignment += ["EU Taxonomy Regulation", "MiCA Art 66", "CSRD ESRS E1"]
        if cert_standard == "Art6_ITMO":
            framework_alignment += ["Paris Agreement Art 6.4", "UNFCCC CMA rules", "CORSIA"]
        if cert_standard in ("VCS", "Gold_Standard"):
            framework_alignment += ["ICVCM CCP 2023", "PCAF Carbon Credit Accounting"]

        return {
            "underlying_asset_type": underlying,
            "certification_standard": cert_standard,
            "underlying_face_value_usd": asset_input.underlying_face_value_usd,
            "on_chain_verification": asset_input.on_chain_verification,
            "tokenisation_premium_bps": round(total_premium, 2),
            "verification_status": verification_status,
            "certification_quality_score": round(quality_mult * 100, 0),
            "framework_alignment": framework_alignment,
            "blockchain_network": asset_input.consensus_mechanism,
            "recommended_standards": [
                "EU Green Bond Standard (EU) 2023/2631",
                "ICMA Green Bond Principles 2021",
                "UNFCCC Article 6 ITMO registry linkage",
                "ISO 14064-2 for carbon credits",
            ],
            "notes": (
                "Tokenisation premium reflects DLT-driven transparency, "
                "reduced settlement friction, and improved traceability. "
                "Art 6 ITMOs carry highest premium due to Paris Agreement linkage."
            ),
        }

    def calculate_financed_emissions(self, portfolio_input: CryptoPortfolioInput) -> Dict[str, Any]:
        """
        PCAF Emerging Methodology for Crypto financed emissions.

        Attribution formula (PCAF Part D analogy):
          Financed emissions = (outstanding_value / market_cap) × network_energy × grid_factor

        DQS 3 (estimated data with supporting evidence) or 4 (estimated, limited evidence).
        """
        total_financed_tco2e = 0.0
        holding_results: List[Dict[str, Any]] = []

        for holding in portfolio_input.holdings:
            symbol = holding.get("symbol", "UNKNOWN")
            mechanism = holding.get("consensus_mechanism", "PoS")
            outstanding_value = holding.get("value_usd", 0.0)
            market_cap = holding.get("market_cap_usd", 0.0)
            network_energy_twh = holding.get("network_energy_twh_yr", None)

            # Determine network energy
            if network_energy_twh is None:
                if mechanism == "PoW":
                    network_energy_twh = CBECI_NETWORK_TWH_CENTRAL
                else:
                    factor = {"PoS": 0.0008, "DPoS": 0.0005, "PoA": 0.0003, "PoH": 0.0002}.get(
                        mechanism, 0.001
                    )
                    network_energy_twh = CBECI_NETWORK_TWH_CENTRAL * factor

            # Country distribution → grid carbon
            country_dist = holding.get("mining_country_distribution", {"other": 100.0})
            _, grid_carbon = self._geography_adjusted_intensity(country_dist)

            result = self._compute_pcaf_single(
                outstanding_value=outstanding_value,
                market_cap=market_cap,
                network_energy_twh=network_energy_twh,
                grid_factor_gco2_kwh=grid_carbon,
            )
            total_financed_tco2e += result["financed_emissions_tco2e"]

            holding_results.append({
                "symbol": symbol,
                "consensus_mechanism": mechanism,
                "outstanding_value_usd": outstanding_value,
                "market_cap_usd": market_cap,
                "attribution_factor": result["attribution_factor"],
                "network_energy_twh_yr": round(network_energy_twh, 4),
                "grid_carbon_gco2_kwh": round(grid_carbon, 1),
                "financed_emissions_tco2e": result["financed_emissions_tco2e"],
                "dqs": result["dqs"],
            })

        portfolio_attribution = (
            portfolio_input.total_portfolio_value_usd
            / max(1.0, sum(h.get("market_cap_usd", 1.0) for h in portfolio_input.holdings))
        )

        return {
            "portfolio_id": portfolio_input.portfolio_id,
            "reporting_period": portfolio_input.reporting_period,
            "total_financed_emissions_tco2e": round(total_financed_tco2e, 2),
            "portfolio_financed_emissions_intensity_tco2e_per_musd": round(
                total_financed_tco2e / max(1.0, portfolio_input.total_portfolio_value_usd / 1e6), 2
            ),
            "holding_breakdown": holding_results,
            "pcaf_methodology": "PCAF Emerging Methodology for Crypto Assets (Part D analogy, 2024)",
            "data_quality_score": 3,
            "dqs_rationale": (
                "DQS 3: Estimated financed emissions using network-level energy "
                "data (CBECI) and portfolio-level attribution. Market cap data "
                "sourced from public exchanges."
            ),
            "limitations": [
                "Attribution assumes proportional ownership of network emissions",
                "Grid carbon factor based on geographic mining distribution estimates",
                "Does not capture intraday energy price arbitrage by miners",
                "PoW/PoS mix may change with network upgrades",
            ],
        }

    def aggregate_portfolio(self, portfolio_input: CryptoPortfolioInput) -> Dict[str, Any]:
        """
        Full crypto portfolio climate aggregation.

        Returns weighted-average gCO2e/tx, total MWh/yr, total tCO2e/yr,
        MiCA compliance status, and climate risk tier distribution.
        """
        total_value = portfolio_input.total_portfolio_value_usd or 1.0
        total_energy_mwh = 0.0
        total_tco2e = 0.0
        weighted_gco2e_per_tx = 0.0
        mica_scores: List[float] = []
        risk_tiers: Dict[str, float] = {}
        holding_summaries: List[Dict[str, Any]] = []

        for holding in portfolio_input.holdings:
            symbol = holding.get("symbol", "UNKNOWN")
            mechanism = holding.get("consensus_mechanism", "PoS")
            value = holding.get("value_usd", 0.0)
            weight = value / total_value

            # Build a minimal CryptoAssetInput for sub-assessment
            asset = CryptoAssetInput(
                asset_symbol=symbol,
                consensus_mechanism=mechanism,
                network_energy_twh_yr=holding.get("network_energy_twh_yr"),
                mining_country_distribution=holding.get("mining_country_distribution"),
                market_cap_usd=holding.get("market_cap_usd"),
                outstanding_value_usd=value,
                has_white_paper=holding.get("has_white_paper", False),
                discloses_energy_consumption=holding.get("discloses_energy_consumption", False),
                discloses_renewable_pct=holding.get("discloses_renewable_pct", False),
                discloses_ghg_emissions=holding.get("discloses_ghg_emissions", False),
            )
            result = self.assess_crypto_asset(asset)

            # Annualised energy contribution
            holding_energy_mwh = result.network_energy_twh_yr_central * 1e6 * weight
            holding_tco2e = result.annual_network_tco2e * weight
            total_energy_mwh += holding_energy_mwh
            total_tco2e += holding_tco2e
            weighted_gco2e_per_tx += result.gco2e_per_tx_central * weight
            mica_scores.append(result.mica_score)

            tier = result.climate_risk_tier
            risk_tiers[tier] = risk_tiers.get(tier, 0.0) + weight * 100

            holding_summaries.append({
                "symbol": symbol,
                "weight_pct": round(weight * 100, 2),
                "consensus_mechanism": mechanism,
                "energy_mwh_yr_attributed": round(holding_energy_mwh, 2),
                "tco2e_yr_attributed": round(holding_tco2e, 2),
                "gco2e_per_tx": round(result.gco2e_per_tx_central, 4),
                "mica_compliance": result.mica_compliance_level,
                "climate_risk_tier": tier,
            })

        # DeFi protocol overlay
        defi_result = None
        if portfolio_input.include_defi_protocols and portfolio_input.defi_tvl_usd:
            defi_result = self._assess_defi_protocols(portfolio_input.defi_tvl_usd)

        avg_mica = sum(mica_scores) / len(mica_scores) if mica_scores else 0.0
        portfolio_tier = self._portfolio_risk_tier(risk_tiers)

        return {
            "portfolio_id": portfolio_input.portfolio_id,
            "investor_name": portfolio_input.investor_name,
            "reporting_period": portfolio_input.reporting_period,
            "total_portfolio_value_usd": portfolio_input.total_portfolio_value_usd,
            "total_energy_mwh_yr": round(total_energy_mwh, 2),
            "total_tco2e_yr": round(total_tco2e, 2),
            "weighted_avg_gco2e_per_tx": round(weighted_gco2e_per_tx, 4),
            "portfolio_carbon_intensity_tco2e_per_musd": round(
                total_tco2e / max(1.0, total_value / 1e6), 2
            ),
            "avg_mica_score": round(avg_mica, 1),
            "portfolio_climate_risk_tier": portfolio_tier,
            "risk_tier_distribution_pct": {k: round(v, 1) for k, v in risk_tiers.items()},
            "holding_summaries": holding_summaries,
            "defi_assessment": defi_result,
            "recommendations": self._portfolio_recommendations(portfolio_tier, avg_mica),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _geography_adjusted_intensity(
        self, country_dist: Optional[Dict[str, float]]
    ) -> tuple[float, float]:
        """Return (weighted_renewable_pct, weighted_grid_carbon_gco2_kwh)."""
        if not country_dist:
            default = MINING_COUNTRY_PROFILES["other"]
            return default["renewable_pct"], default["grid_carbon_intensity_gco2_kwh"]

        weighted_re = 0.0
        weighted_ci = 0.0
        total = 0.0
        for code, pct in country_dist.items():
            profile = MINING_COUNTRY_PROFILES.get(code, MINING_COUNTRY_PROFILES["other"])
            weighted_re += profile["renewable_pct"] * pct
            weighted_ci += profile["grid_carbon_intensity_gco2_kwh"] * pct
            total += pct

        if total <= 0:
            return 35.0, 450.0
        return weighted_re / total, weighted_ci / total

    def _compute_pcaf_single(
        self,
        outstanding_value: float,
        market_cap: float,
        network_energy_twh: float,
        grid_factor_gco2_kwh: float,
    ) -> Dict[str, Any]:
        """Core PCAF attribution formula for a single crypto holding."""
        if market_cap <= 0:
            attribution = 0.0
            dqs = 4
        else:
            attribution = outstanding_value / market_cap
            dqs = 3 if market_cap > 1_000_000_000 else 4  # lower DQS for large-cap (better data)

        # Network emissions: TWh → kWh → tCO2e
        total_network_tco2e = (network_energy_twh * 1e9) * (grid_factor_gco2_kwh / 1e6)
        financed_tco2e = attribution * total_network_tco2e

        return {
            "attribution_factor": round(attribution, 8),
            "financed_emissions_tco2e": round(financed_tco2e, 4),
            "total_network_tco2e": round(total_network_tco2e, 2),
            "dqs": dqs,
        }

    def _classify_climate_risk(
        self, mechanism: str, grid_carbon: float, renewable_pct: float
    ) -> str:
        """Classify climate risk tier based on consensus mechanism and energy mix."""
        if mechanism == "PoW":
            if grid_carbon > 600:
                return "very_high"
            elif grid_carbon > 400:
                return "high"
            elif renewable_pct > 70:
                return "medium"
            else:
                return "high"
        elif mechanism in ("PoS", "DPoS", "PoA", "PoH"):
            if renewable_pct > 80:
                return "low"
            elif renewable_pct > 50:
                return "low"
            else:
                return "medium"
        return "medium"

    def _assess_defi_protocols(self, tvl_usd: float) -> Dict[str, Any]:
        """
        DeFi Protocol Carbon Intensity — TVL-weighted emissions.

        Assumes Ethereum PoS as base network (0.01 gCO2e/tx equivalent).
        Gas fees proxy for relative compute intensity.
        """
        # Estimate annual transactions from TVL (empirical ratio: ~1 tx per $1,000 TVL/day)
        estimated_daily_tx = tvl_usd / 1_000
        annual_tx = estimated_daily_tx * 365
        base_gco2e_per_tx = 0.01  # ETH PoS

        # Protocol categories with relative gas multiplier
        protocols = [
            {"name": "AMM DEX (e.g., Uniswap)", "gas_multiplier": 1.5, "tvl_share_pct": 35},
            {"name": "Lending (e.g., Aave)", "gas_multiplier": 1.2, "tvl_share_pct": 25},
            {"name": "Yield Aggregator", "gas_multiplier": 2.0, "tvl_share_pct": 15},
            {"name": "Derivatives (e.g., dYdX)", "gas_multiplier": 1.8, "tvl_share_pct": 15},
            {"name": "Bridge / L2", "gas_multiplier": 0.8, "tvl_share_pct": 10},
        ]

        weighted_multiplier = sum(p["gas_multiplier"] * p["tvl_share_pct"] / 100 for p in protocols)
        effective_gco2e_per_tx = base_gco2e_per_tx * weighted_multiplier
        annual_tco2e = annual_tx * effective_gco2e_per_tx / 1e6

        return {
            "tvl_usd": tvl_usd,
            "estimated_annual_tx": round(annual_tx, 0),
            "base_network": "Ethereum PoS",
            "base_gco2e_per_tx": base_gco2e_per_tx,
            "tvl_weighted_gco2e_per_tx": round(effective_gco2e_per_tx, 4),
            "annual_defi_tco2e": round(annual_tco2e, 4),
            "protocol_breakdown": protocols,
            "notes": (
                "DeFi emissions are negligible relative to PoW networks. "
                "Main risk is indirect: capital allocation to high-emission chains."
            ),
        }

    def _portfolio_risk_tier(self, risk_tiers: Dict[str, float]) -> str:
        """Determine portfolio-level risk tier from weighted distribution."""
        if risk_tiers.get("very_high", 0) > 20:
            return "very_high"
        elif risk_tiers.get("very_high", 0) + risk_tiers.get("high", 0) > 30:
            return "high"
        elif risk_tiers.get("very_high", 0) + risk_tiers.get("high", 0) > 10:
            return "medium"
        else:
            return "low"

    def _portfolio_recommendations(self, tier: str, mica_score: float) -> List[str]:
        """Generate actionable portfolio-level recommendations."""
        recs: List[str] = []
        if tier in ("very_high", "high"):
            recs.append("Consider reducing PoW exposure and increasing PoS/PoA allocation.")
            recs.append("Engage miners to disclose renewable energy purchase agreements (RECs).")
            recs.append("Evaluate transition to tokenised carbon credits to offset PoW footprint.")
        if mica_score < 50:
            recs.append("Request MiCA Art 66 sustainability disclosures from issuers.")
            recs.append("Prioritise assets with white papers disclosing consensus mechanism details.")
        if tier == "low":
            recs.append("Portfolio demonstrates low crypto climate risk — maintain PoS tilt.")
        recs.append("Publish PCAF-aligned financed emissions disclosure in annual ESG report.")
        return recs
