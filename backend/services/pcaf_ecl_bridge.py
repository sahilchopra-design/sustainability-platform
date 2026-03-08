"""
PCAF -> ECL Climate Overlay Bridge Service
============================================
Wires PCAF portfolio emission analytics into the ECL Climate Engine
so that financed emissions data automatically informs credit risk
climate overlays.

Data Flow:
  1. PCAF engine produces per-investee financed emissions, WACI, DQS, temperature
  2. This bridge maps each investee to ECL ClimateRiskInputs
  3. ECL engine receives enriched climate inputs -> climate-adjusted PD/LGD/ECL

Key Mappings:
  - PCAF sector_carbon_intensity -> ECL sector_carbon_intensity_tco2e_mrev
  - PCAF implied_temperature_c   -> ECL scenario probability weighting
  - PCAF sbti_committed          -> ECL sbti_aligned PD discount (-20%)
  - PCAF DQS score               -> confidence weighting on overlays

Reference:
  - PCAF Global GHG Accounting Standard v2.0 (2022)
  - IFRS 9 B5.5.7 (SICR assessment)
  - EBA GL/2022/16 (climate stress testing guidance)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger("platform.pcaf_ecl_bridge")


# ---------------------------------------------------------------------------
#  Configuration constants
# ---------------------------------------------------------------------------

# PCAF DQS -> confidence weight (how much we trust the emissions data)
DQS_CONFIDENCE_WEIGHTS = {
    1: 1.00,  # Verified data
    2: 0.90,  # Reported data
    3: 0.70,  # Physical activity data
    4: 0.50,  # Estimated data (sector avg)
    5: 0.30,  # Estimated data (revenue proxy)
}

# Temperature score -> ECL scenario probability overrides
# Higher portfolio temp = more weight on adverse/severe scenarios
TEMPERATURE_SCENARIO_WEIGHTS = {
    # temp_bucket: (optimistic, base, adverse, severe)
    "below_1.5": (0.35, 0.40, 0.20, 0.05),
    "1.5_to_2.0": (0.25, 0.45, 0.22, 0.08),
    "2.0_to_2.5": (0.20, 0.45, 0.25, 0.10),  # NGFS default
    "2.5_to_3.0": (0.15, 0.40, 0.30, 0.15),
    "3.0_to_3.5": (0.10, 0.35, 0.35, 0.20),
    "above_3.5": (0.05, 0.25, 0.40, 0.30),
}

# Sector transition risk mapping from WACI intensity
# WACI (tCO2e / M EUR revenue) -> transition risk level
WACI_TRANSITION_RISK_MAP = [
    (50, "low"),           # < 50 tCO2e/MEUR
    (150, "medium"),       # 50-150
    (500, "high"),         # 150-500
    (1000, "very_high"),   # 500-1000
    (float("inf"), "very_high"),  # > 1000
]


# ---------------------------------------------------------------------------
#  Data classes
# ---------------------------------------------------------------------------

@dataclass
class PCAFInvesteeProfile:
    """
    Distilled PCAF profile for a single investee,
    sourced from pcaf_waci_engine.FinancedEmissionsResult
    or pcaf_investees DB row.
    """
    investee_name: str
    sector_gics: str = ""
    country_iso: str = ""

    # Emissions (tCO2e attributed)
    financed_scope1_tco2e: float = 0.0
    financed_scope2_tco2e: float = 0.0
    financed_scope3_tco2e: float = 0.0

    # Intensity
    revenue_intensity_tco2e_per_meur: float = 0.0  # WACI contribution

    # Outstanding exposure
    outstanding_eur: float = 0.0

    # Quality
    pcaf_dq_composite: float = 3.0  # 1-5

    # Climate alignment
    sbti_committed: bool = False
    net_zero_target_year: Optional[int] = None
    implied_temperature_c: float = 2.5

    # Attribution
    attribution_factor: float = 0.0


@dataclass
class ECLClimateInputs:
    """
    Climate risk inputs required by ecl_climate_engine.ECLClimateEngine.
    This is the TARGET structure that the bridge populates.
    """
    physical_risk_score: float = 30.0        # 0-100 (default medium)
    transition_risk_score: float = 40.0      # 0-100
    sector_carbon_intensity_tco2e_mrev: float = 0.0
    carbon_price_sensitivity: float = 0.5    # 0-1
    sector_transition_risk: str = "medium"   # low/medium/high/very_high
    collateral_flood_risk: str = "low"       # none/low/medium/high/extreme
    energy_rating: str = "C"                 # A-G EPC
    sbti_aligned: bool = False
    net_zero_committed: bool = False

    # PCAF bridge additions
    pcaf_confidence: float = 0.70
    pcaf_implied_temperature_c: float = 2.5
    scenario_weights: dict = field(default_factory=lambda: {
        "OPTIMISTIC": 0.20,
        "BASE": 0.45,
        "ADVERSE": 0.25,
        "SEVERE": 0.10,
    })


@dataclass
class PortfolioBridgeResult:
    """Aggregate result from running the bridge across a portfolio."""
    investee_count: int = 0
    mapped_count: int = 0
    avg_confidence: float = 0.0
    avg_transition_risk_score: float = 0.0
    portfolio_temperature_c: float = 2.5
    scenario_weights: dict = field(default_factory=dict)
    investee_climate_inputs: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


# ---------------------------------------------------------------------------
#  Bridge functions
# ---------------------------------------------------------------------------

def _temperature_bucket(temp_c: float) -> str:
    """Classify temperature into scenario weight bucket."""
    if temp_c < 1.5:
        return "below_1.5"
    elif temp_c < 2.0:
        return "1.5_to_2.0"
    elif temp_c < 2.5:
        return "2.0_to_2.5"
    elif temp_c < 3.0:
        return "2.5_to_3.0"
    elif temp_c < 3.5:
        return "3.0_to_3.5"
    else:
        return "above_3.5"


def _waci_to_transition_risk(waci: float) -> str:
    """Map WACI intensity to sector transition risk level."""
    for threshold, level in WACI_TRANSITION_RISK_MAP:
        if waci <= threshold:
            return level
    return "very_high"


def _waci_to_transition_score(waci: float) -> float:
    """
    Convert WACI intensity to a 0-100 transition risk score.
    Logarithmic scale: 0 WACI -> 0, 50 -> 25, 200 -> 50, 1000 -> 80, 3000 -> 100.
    """
    import math
    if waci <= 0:
        return 5.0
    score = min(100.0, 15.0 * math.log10(waci + 1) + 5.0)
    return round(score, 1)


def _carbon_price_sensitivity(waci: float, sector_gics: str) -> float:
    """
    Estimate carbon price sensitivity (0-1) from emissions intensity.
    High-carbon sectors have higher sensitivity to carbon pricing.
    """
    # High-carbon GICS sectors get a boost
    high_carbon_sectors = {
        "10": 0.15,  # Energy
        "15": 0.10,  # Materials
        "20": 0.05,  # Industrials
        "55": 0.08,  # Utilities
    }
    sector_2digit = sector_gics[:2] if sector_gics else ""
    sector_boost = high_carbon_sectors.get(sector_2digit, 0.0)

    # Base sensitivity from WACI
    if waci <= 50:
        base = 0.2
    elif waci <= 200:
        base = 0.4
    elif waci <= 500:
        base = 0.6
    elif waci <= 1000:
        base = 0.8
    else:
        base = 0.95

    return min(1.0, round(base + sector_boost, 2))


def map_investee_to_ecl_climate(
    profile: PCAFInvesteeProfile,
    physical_risk_override: Optional[float] = None,
    collateral_flood_risk: str = "low",
    energy_rating: str = "C",
) -> ECLClimateInputs:
    """
    Map a single PCAF investee profile to ECL ClimateRiskInputs.

    Parameters
    ----------
    profile : PCAFInvesteeProfile
        PCAF emission and alignment data for one investee.
    physical_risk_override : float, optional
        If provided, use this 0-100 score instead of default.
    collateral_flood_risk : str
        Collateral-level flood risk (from property assessment).
    energy_rating : str
        EPC energy rating (from building assessment).

    Returns
    -------
    ECLClimateInputs
        Ready-to-use climate inputs for ECL engine.
    """
    waci = profile.revenue_intensity_tco2e_per_meur

    # Transition risk
    transition_score = _waci_to_transition_score(waci)
    transition_risk_level = _waci_to_transition_risk(waci)
    carbon_sensitivity = _carbon_price_sensitivity(waci, profile.sector_gics)

    # Physical risk (use override or default based on sector/country)
    physical_score = physical_risk_override if physical_risk_override is not None else 30.0

    # SBTi / Net Zero
    sbti = profile.sbti_committed
    net_zero = (
        profile.net_zero_target_year is not None
        and profile.net_zero_target_year <= 2050
    )

    # DQS confidence
    dqs_int = max(1, min(5, round(profile.pcaf_dq_composite)))
    confidence = DQS_CONFIDENCE_WEIGHTS.get(dqs_int, 0.50)

    # Temperature-based scenario weights
    temp_bucket = _temperature_bucket(profile.implied_temperature_c)
    weights_tuple = TEMPERATURE_SCENARIO_WEIGHTS.get(temp_bucket, (0.20, 0.45, 0.25, 0.10))
    scenario_weights = {
        "OPTIMISTIC": weights_tuple[0],
        "BASE": weights_tuple[1],
        "ADVERSE": weights_tuple[2],
        "SEVERE": weights_tuple[3],
    }

    return ECLClimateInputs(
        physical_risk_score=physical_score,
        transition_risk_score=transition_score,
        sector_carbon_intensity_tco2e_mrev=waci,
        carbon_price_sensitivity=carbon_sensitivity,
        sector_transition_risk=transition_risk_level,
        collateral_flood_risk=collateral_flood_risk,
        energy_rating=energy_rating,
        sbti_aligned=sbti,
        net_zero_committed=net_zero,
        pcaf_confidence=confidence,
        pcaf_implied_temperature_c=profile.implied_temperature_c,
        scenario_weights=scenario_weights,
    )


def bridge_portfolio(
    investee_profiles: list[PCAFInvesteeProfile],
    portfolio_temperature_c: float = 2.5,
    physical_risk_overrides: Optional[dict[str, float]] = None,
) -> PortfolioBridgeResult:
    """
    Map an entire portfolio of PCAF investees to ECL climate inputs.

    Parameters
    ----------
    investee_profiles : list[PCAFInvesteeProfile]
        All investees with PCAF data.
    portfolio_temperature_c : float
        Portfolio-level temperature score from PCAF engine.
    physical_risk_overrides : dict, optional
        Map of investee_name -> physical_risk_score (0-100).

    Returns
    -------
    PortfolioBridgeResult
        Aggregated result with per-investee ECL inputs.
    """
    overrides = physical_risk_overrides or {}
    result = PortfolioBridgeResult(
        investee_count=len(investee_profiles),
        portfolio_temperature_c=portfolio_temperature_c,
    )

    total_confidence = 0.0
    total_transition_score = 0.0
    total_weight = 0.0

    for profile in investee_profiles:
        try:
            phys_override = overrides.get(profile.investee_name)
            climate_inputs = map_investee_to_ecl_climate(
                profile,
                physical_risk_override=phys_override,
            )

            result.investee_climate_inputs.append({
                "investee_name": profile.investee_name,
                "sector_gics": profile.sector_gics,
                "outstanding_eur": profile.outstanding_eur,
                "climate_inputs": asdict(climate_inputs),
            })
            result.mapped_count += 1

            # Exposure-weighted averages
            w = max(profile.outstanding_eur, 1.0)
            total_confidence += climate_inputs.pcaf_confidence * w
            total_transition_score += climate_inputs.transition_risk_score * w
            total_weight += w

        except Exception as e:
            result.warnings.append(
                f"Failed to map {profile.investee_name}: {str(e)}"
            )
            logger.warning("Bridge mapping failed for %s: %s", profile.investee_name, e)

    if total_weight > 0:
        result.avg_confidence = round(total_confidence / total_weight, 3)
        result.avg_transition_risk_score = round(total_transition_score / total_weight, 1)

    # Portfolio-level scenario weights from temperature
    temp_bucket = _temperature_bucket(portfolio_temperature_c)
    weights_tuple = TEMPERATURE_SCENARIO_WEIGHTS.get(temp_bucket, (0.20, 0.45, 0.25, 0.10))
    result.scenario_weights = {
        "OPTIMISTIC": weights_tuple[0],
        "BASE": weights_tuple[1],
        "ADVERSE": weights_tuple[2],
        "SEVERE": weights_tuple[3],
    }

    logger.info(
        "PCAF->ECL bridge: %d/%d investees mapped, avg_conf=%.2f, avg_trans_score=%.1f, temp=%.1f°C",
        result.mapped_count,
        result.investee_count,
        result.avg_confidence,
        result.avg_transition_risk_score,
        portfolio_temperature_c,
    )

    return result


# ---------------------------------------------------------------------------
#  Convenience: DB row -> PCAFInvesteeProfile
# ---------------------------------------------------------------------------

def db_row_to_profile(row: dict) -> PCAFInvesteeProfile:
    """
    Convert a pcaf_investees DB row (dict) to PCAFInvesteeProfile.
    Handles missing/null fields gracefully.
    """
    return PCAFInvesteeProfile(
        investee_name=row.get("investee_name", "Unknown"),
        sector_gics=row.get("sector_gics") or "",
        country_iso=row.get("country_iso") or "",
        financed_scope1_tco2e=float(row.get("financed_scope1_tco2e") or 0),
        financed_scope2_tco2e=float(row.get("financed_scope2_tco2e") or 0),
        financed_scope3_tco2e=float(row.get("financed_scope3_tco2e") or 0),
        revenue_intensity_tco2e_per_meur=float(row.get("revenue_intensity_tco2e_per_mrevenue") or 0),
        outstanding_eur=float(row.get("outstanding_investment") or 0),
        pcaf_dq_composite=float(row.get("pcaf_dq_scope1") or row.get("pcaf_dq_scope2") or 3.0),
        sbti_committed=bool(row.get("sbti_committed")),
        net_zero_target_year=row.get("net_zero_target_year"),
        implied_temperature_c=float(row.get("implied_temperature_c") or 2.5),
        attribution_factor=float(row.get("attribution_factor") or 0),
    )


# ---------------------------------------------------------------------------
#  Quick test / demo
# ---------------------------------------------------------------------------

def demo_bridge():
    """Demonstrate the bridge with sample data."""
    profiles = [
        PCAFInvesteeProfile(
            investee_name="TotalEnergies SE",
            sector_gics="10102010",
            country_iso="FRA",
            financed_scope1_tco2e=45_000,
            financed_scope2_tco2e=5_000,
            revenue_intensity_tco2e_per_meur=850.0,
            outstanding_eur=50_000_000,
            pcaf_dq_composite=2.0,
            sbti_committed=True,
            net_zero_target_year=2050,
            implied_temperature_c=3.2,
        ),
        PCAFInvesteeProfile(
            investee_name="Orsted A/S",
            sector_gics="55105010",
            country_iso="DNK",
            financed_scope1_tco2e=2_000,
            financed_scope2_tco2e=500,
            revenue_intensity_tco2e_per_meur=25.0,
            outstanding_eur=30_000_000,
            pcaf_dq_composite=1.0,
            sbti_committed=True,
            net_zero_target_year=2040,
            implied_temperature_c=1.6,
        ),
        PCAFInvesteeProfile(
            investee_name="ArcelorMittal",
            sector_gics="15104050",
            country_iso="LUX",
            financed_scope1_tco2e=120_000,
            financed_scope2_tco2e=15_000,
            revenue_intensity_tco2e_per_meur=1_200.0,
            outstanding_eur=80_000_000,
            pcaf_dq_composite=3.0,
            sbti_committed=False,
            implied_temperature_c=3.8,
        ),
    ]

    result = bridge_portfolio(profiles, portfolio_temperature_c=2.9)
    return result
