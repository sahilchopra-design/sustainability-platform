"""
Insurance Climate Risk Calculator
Aligned with: Solvency II Article 44a (2024 amendment) / EIOPA ORSA Climate Guide 2022 /
              Swiss Re sigma Physical Risk Model / Lloyd's RDS (Reference Disaster Scenarios)

Calculates:
  1. CAT risk — gross/net P&L loss at 1-in-100, 1-in-250 AEPs under climate scenarios
  2. Climate-adjusted technical provisions (TP uplift) under 1.5C / 2C / 3C
  3. SCR climate add-on (Pillar 2 capital buffer)
  4. Reserve adequacy assessment across scenarios
  5. Protection gap (insured vs. economic loss)
  6. Reinsurance sufficiency check
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── CAT loss multiplier by peril and scenario (vs. current climate baseline) ──
# Source: Swiss Re sigma 2023 / EIOPA CCRST 2022 / Lloyd's MRC
_CAT_LOSS_MULTIPLIER: Dict[str, Dict[str, float]] = {
    "tropical_cyclone": {"1.5C": 1.08, "2C": 1.20, "3C": 1.45},
    "flood":            {"1.5C": 1.15, "2C": 1.35, "3C": 1.80},
    "wildfire":         {"1.5C": 1.25, "2C": 1.55, "3C": 2.20},
    "drought":          {"1.5C": 1.12, "2C": 1.30, "3C": 1.65},
    "winter_storm":     {"1.5C": 0.95, "2C": 0.90, "3C": 0.85},  # decreasing trend
    "hail":             {"1.5C": 1.10, "2C": 1.22, "3C": 1.40},
    "earthquake":       {"1.5C": 1.00, "2C": 1.00, "3C": 1.00},  # climate-independent
}
# ── Solvency II natural catastrophe CAT SCR shock factors ─────────────────────
# Source: Solvency II Delegated Regulation (EU) 2015/35, Annex XIII
_SOLVENCY_II_CAT_SCR_FACTOR: Dict[str, float] = {
    "tropical_cyclone": 0.0150,   # 1.5% of gross premium income (Europe wind proxy)
    "flood":            0.0097,
    "wildfire":         0.0080,
    "drought":          0.0060,
    "winter_storm":     0.0150,
    "hail":             0.0080,
    "earthquake":       0.0090,
}

# ── TP uplift table: additional % loading on technical provisions by scenario ──
# Source: EIOPA Supervisory Statement on Climate Risk 2024
_TP_UPLIFT_PCT: Dict[str, float] = {
    "1.5C": 0.04,   # +4% to TPs
    "2C":   0.09,   # +9% to TPs
    "3C":   0.18,   # +18% to TPs
}


@dataclass
class InsuranceCATInput:
    entity_id: str
    entity_name: str
    insurer_type: str                   # primary | reinsurer | captive
    cat_peril: str                      # flood | tropical_cyclone | wildfire | ...
    gross_written_premium_eur: float
    technical_provisions_eur: float
    scr_eur: float
    own_funds_eur: float

    # Baseline loss estimates (current climate, pre-climate adjustment)
    gross_loss_1in100_baseline_eur: float
    gross_loss_1in250_baseline_eur: float
    average_annual_loss_baseline_eur: float
    probable_max_loss_baseline_eur: float

    # Reinsurance structure
    reinsurance_retention_pct: float = 0.30  # 30% retained
    reinsurance_limit_eur: Optional[float] = None

    # Underwriting policies
    coal_exclusion: bool = False
    oil_sands_exclusion: bool = False
    arctic_drilling_exclusion: bool = False
    fossil_fuel_new_business_cap_pct: float = 100.0  # % of current fossil fuel premium

    # Protection gap context
    total_economic_loss_baseline_eur: Optional[float] = None


@dataclass
class InsuranceCATResult:
    entity_id: str
    entity_name: str
    peril: str
    scenario: str
    horizon_year: int

    # Climate-adjusted CAT losses
    gross_loss_1in100_eur: float
    gross_loss_1in250_eur: float
    net_loss_1in100_eur: float      # post-reinsurance
    net_loss_1in250_eur: float
    average_annual_loss_eur: float
    probable_max_loss_eur: float
    cat_loss_change_pct: float      # % change vs. baseline

    # Technical provisions
    technical_provisions_eur: float
    climate_adjusted_tp_eur: float
    tp_uplift_pct: float

    # SCR
    scr_baseline_eur: float
    scr_climate_addon_eur: float
    total_scr_eur: float
    solvency_ratio_pre_addon: float   # own_funds / scr_baseline
    solvency_ratio_post_addon: float  # own_funds / total_scr

    # Reserve adequacy
    reserve_adequacy: str           # adequate | marginal | deficient
    reserve_deficiency_eur: float   # 0 if adequate

    # Protection gap
    insured_loss_eur: float
    economic_loss_eur: float
    protection_gap_eur: float
    protection_gap_pct: float

    # ESG underwriting
    esg_underwriting_score: float   # 0-100

    # Reinsurance
    reinsurance_adequate: bool
    reinsurance_gap_eur: float

    methodology_ref: str
    warnings: List[str]


def calculate_insurance_climate_risk(
    inp: InsuranceCATInput,
    scenario: str = "2C",
    horizon_year: int = 2050,
) -> InsuranceCATResult:
    """
    Full insurance climate risk assessment.

    Steps:
      1. Apply peril × scenario CAT loss multiplier to baseline loss estimates
      2. Net for reinsurance retention
      3. Compute Solvency II CAT SCR add-on
      4. Compute TP uplift under scenario
      5. Assess reserve adequacy (TP vs. climate-adjusted loss)
      6. Compute protection gap
      7. Score ESG underwriting policy
    """
    warnings: list[str] = []

    # ── 1. Climate-adjusted CAT losses ────────────────────────────────────
    peril_norm = inp.cat_peril.lower().replace(" ", "_")
    multipliers = _CAT_LOSS_MULTIPLIER.get(peril_norm, {})
    multiplier = multipliers.get(scenario, 1.0)

    if not multipliers:
        warnings.append(f"Peril '{inp.cat_peril}' not in reference table; using multiplier 1.0")

    gross_1in100 = inp.gross_loss_1in100_baseline_eur * multiplier
    gross_1in250 = inp.gross_loss_1in250_baseline_eur * multiplier
    aal          = inp.average_annual_loss_baseline_eur * multiplier
    pml          = inp.probable_max_loss_baseline_eur * multiplier

    cat_change_pct = (multiplier - 1.0) * 100.0

    # ── 2. Net for reinsurance ───────────────────────────────────────
    ret = inp.reinsurance_retention_pct
    net_1in100 = gross_1in100 * ret
    net_1in250 = gross_1in250 * ret

    # Check if reinsurance limit covers 1-in-250 gross loss
    ri_limit = inp.reinsurance_limit_eur or (gross_1in250 * (1 - ret) * 1.1)
    ri_gap    = max(0.0, gross_1in250 * (1 - ret) - ri_limit)
    ri_adequate = ri_gap == 0.0

    # ── 3. SCR CAT add-on (Solvency II Delegated Reg.) ────────────────────
    base_cat_scr_factor = _SOLVENCY_II_CAT_SCR_FACTOR.get(peril_norm, 0.008)
    # Climate uplift: SCR add-on scales with CAT loss multiplier beyond baseline
    climate_scr_factor = base_cat_scr_factor * max(0, multiplier - 1.0)
    scr_addon = inp.gross_written_premium_eur * climate_scr_factor
    total_scr  = inp.scr_eur + scr_addon

    sol_ratio_pre  = inp.own_funds_eur / inp.scr_eur if inp.scr_eur > 0 else 0.0
    sol_ratio_post = inp.own_funds_eur / total_scr    if total_scr > 0  else 0.0

    if sol_ratio_post < 1.0:
        warnings.append(
            f"Solvency ratio falls below 100% ({sol_ratio_post:.1%}) after climate SCR add-on"
        )
    elif sol_ratio_post < 1.2:
        warnings.append(
            f"Solvency ratio under 120% ({sol_ratio_post:.1%}) post-addon — consider capital buffer"
        )

    # ── 4. Technical provisions uplift ──────────────────────────────
    tp_uplift_frac   = _TP_UPLIFT_PCT.get(scenario, 0.09)
    climate_adj_tp   = inp.technical_provisions_eur * (1 + tp_uplift_frac)
    tp_uplift_pct    = tp_uplift_frac * 100.0

    # ── 5. Reserve adequacy ──────────────────────────────────────────
    # Benchmark: TPs should cover AAL with 15% margin, and net 1-in-100 as stress test
    reserve_benchmark = max(aal * 1.15, net_1in100 * 0.5)
    if climate_adj_tp >= reserve_benchmark * 1.1:
        reserve_adequacy = "adequate"
        reserve_deficiency = 0.0
    elif climate_adj_tp >= reserve_benchmark:
        reserve_adequacy = "marginal"
        reserve_deficiency = 0.0
        warnings.append("Technical provisions are marginal — consider additional reserving")
    else:
        reserve_adequacy = "deficient"
        reserve_deficiency = reserve_benchmark - climate_adj_tp
        warnings.append(
            f"Technical provisions deficient by EUR {reserve_deficiency:,.0f} under {scenario} scenario"
        )

    # ── 6. Protection gap ───────────────────────────────────────────
    econ_loss = (
        inp.total_economic_loss_baseline_eur * multiplier
        if inp.total_economic_loss_baseline_eur
        else gross_1in100 * 1.6   # typical insured fraction proxy
    )
    insured_loss  = gross_1in100
    prot_gap_eur  = max(0.0, econ_loss - insured_loss)
    prot_gap_pct  = prot_gap_eur / econ_loss * 100.0 if econ_loss > 0 else 0.0

    # ── 7. ESG underwriting score (0–100) ───────────────────────────────────
    esg_score = 60.0
    if inp.coal_exclusion:
        esg_score += 15.0
    if inp.oil_sands_exclusion:
        esg_score += 10.0
    if inp.arctic_drilling_exclusion:
        esg_score += 10.0
    if inp.fossil_fuel_new_business_cap_pct <= 50:
        esg_score += 5.0
    esg_score = min(100.0, esg_score)

    return InsuranceCATResult(
        entity_id              = inp.entity_id,
        entity_name            = inp.entity_name,
        peril                  = inp.cat_peril,
        scenario               = scenario,
        horizon_year           = horizon_year,
        gross_loss_1in100_eur  = gross_1in100,
        gross_loss_1in250_eur  = gross_1in250,
        net_loss_1in100_eur    = net_1in100,
        net_loss_1in250_eur    = net_1in250,
        average_annual_loss_eur= aal,
        probable_max_loss_eur  = pml,
        cat_loss_change_pct    = cat_change_pct,
        technical_provisions_eur = inp.technical_provisions_eur,
        climate_adjusted_tp_eur  = climate_adj_tp,
        tp_uplift_pct            = tp_uplift_pct,
        scr_baseline_eur         = inp.scr_eur,
        scr_climate_addon_eur    = scr_addon,
        total_scr_eur            = total_scr,
        solvency_ratio_pre_addon = round(sol_ratio_pre, 4),
        solvency_ratio_post_addon= round(sol_ratio_post, 4),
        reserve_adequacy         = reserve_adequacy,
        reserve_deficiency_eur   = reserve_deficiency,
        insured_loss_eur         = insured_loss,
        economic_loss_eur        = econ_loss,
        protection_gap_eur       = prot_gap_eur,
        protection_gap_pct       = round(prot_gap_pct, 2),
        esg_underwriting_score   = round(esg_score, 1),
        reinsurance_adequate     = ri_adequate,
        reinsurance_gap_eur      = ri_gap,
        methodology_ref = (
            "Solvency II Delegated Reg. 2015/35 Annex XIII | "
            "EIOPA ORSA Climate Guide 2022 | "
            "Swiss Re sigma Physical Risk 2023 | "
            "EIOPA CCRST 2022"
        ),
        warnings = warnings,
    )


def get_reference_data() -> dict:
    return {
        "cat_loss_multipliers":    _CAT_LOSS_MULTIPLIER,
        "solvency_ii_cat_factors": _SOLVENCY_II_CAT_SCR_FACTOR,
        "tp_uplift_by_scenario":   _TP_UPLIFT_PCT,
        "supported_perils": list(_CAT_LOSS_MULTIPLIER.keys()),
        "supported_scenarios": ["1.5C", "2C", "3C"],
        "sources": [
            "Solvency II Delegated Regulation (EU) 2015/35",
            "EIOPA Supervisory Statement on Inclusion of Climate Change Risk in ORSA (2022)",
            "Swiss Re sigma — Natural Catastrophes and Climate Change 2023",
            "EIOPA Climate Change Risk Stress Test (CCRST) 2022",
        ],
    }
