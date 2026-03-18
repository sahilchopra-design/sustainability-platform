"""
Basel III/IV Regulatory Capital Engine
=======================================
Comprehensive CRR / CRD IV/V regulatory capital calculation engine implementing
the full Basel III (Final) framework for credit institutions.

Regulatory Anchors
------------------
  - CRR (EU 575/2013) — Capital Requirements Regulation
  - CRR II (EU 2019/876) — Amendments: NSFR, TLAC, FRTB, leverage ratio
  - CRR III (EU 2024/1623) — Basel III.1 EU implementation (effective Jan 2025)
  - CRD IV (EU 2013/36/EU) — Capital Requirements Directive
  - CRD V (EU 2019/878/EU) — Amendments: buffers, Pillar 2, fit & proper
  - Basel III (Final) BCBS d424 (Dec 2017) — Revised SA, output floor, IRB constraints
  - EBA GL/2017/06 — Guidelines on credit risk assessment (ECAI mapping)
  - EBA GL/2022/02 — Guidelines on ESG risks in supervision
  - BCBS 239 — Principles for effective risk data aggregation and reporting
  - BCBS d295 (Jan 2013) — Liquidity Coverage Ratio
  - BCBS d396 (Oct 2014) — Net Stable Funding Ratio
  - BCBS d457 (Jan 2019) — Fundamental Review of the Trading Book (FRTB)
  - BCBS d563 (Dec 2022) — Standardised Measurement Approach for operational risk

Key Computations
----------------
  1. Standardised Approach (SA) risk weights per CRR Art. 114-134
  2. IRB risk weights per CRR Art. 153 (corporate/bank/sovereign)
  3. Capital ratios: CET1, Tier 1, Total Capital, Leverage (Art. 92)
  4. Capital buffers: CCB, CCyB, G-SIB, D-SIB, Systemic Risk (CRD V)
  5. LCR: HQLA / Net 30-day outflows (BCBS d295, CRR Art. 412)
  6. NSFR: ASF / RSF (BCBS d396, CRR II Art. 428a-428az)
  7. Operational risk: SMA (BCBS d563)
  8. Climate risk capital add-ons (EBA GL/2022/02)
  9. BCBS 239 compliance scoring

Input Parameters
----------------
  exposures   : list[dict]  — counterparty-level credit exposures
  capital     : dict        — CET1, AT1, Tier 2, total exposure measure
  assets      : dict        — HQLA composition by level
  liabilities : dict        — funding composition (retail, wholesale, secured)
  approach    : str         — "standardised" or "irb"

Output Results
--------------
  ExposureRiskWeight       — per-exposure SA/IRB risk weight + RWA
  CapitalRequirementResult — full capital adequacy with buffers + breaches
  LiquidityResult          — LCR + NSFR with stress scenarios
  CapitalAdequacyDashboard — orchestrated assessment with RAG status

Version: 1.0.0
Date: 2026-03-09
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  REFERENCE DATA — EXPOSURE CLASSES  (CRR Article 112)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_EXPOSURE_CLASSES: list[dict] = [
    {
        "class_id": "central_governments",
        "label": "Central governments or central banks",
        "crr_article": "Art. 114",
        "standard_risk_weight": 0.0,
        "description": "Exposures to central governments and central banks. "
                       "0% for OECD sovereigns with CQS 1; CQS-based otherwise.",
    },
    {
        "class_id": "regional_governments",
        "label": "Regional governments or local authorities",
        "crr_article": "Art. 115",
        "standard_risk_weight": 0.20,
        "description": "Exposures to regional or local governments. May be treated "
                       "as central government if domestic-currency funded and guaranteed.",
    },
    {
        "class_id": "public_sector_entities",
        "label": "Public sector entities",
        "crr_article": "Art. 116",
        "standard_risk_weight": 0.20,
        "description": "Non-commercial administrative bodies owned by governments. "
                       "Risk weight follows government or institution treatment.",
    },
    {
        "class_id": "multilateral_dev_banks",
        "label": "Multilateral development banks",
        "crr_article": "Art. 117",
        "standard_risk_weight": 0.0,
        "description": "MDBs listed in CRR Annex VI (IBRD, IFC, ADB, EBRD, etc.). "
                       "0% for qualifying MDBs; CQS-based for others.",
    },
    {
        "class_id": "international_organisations",
        "label": "International organisations",
        "crr_article": "Art. 118",
        "standard_risk_weight": 0.0,
        "description": "BIS, IMF, EU, ESM and similar. Assigned 0% risk weight.",
    },
    {
        "class_id": "institutions",
        "label": "Institutions (banks)",
        "crr_article": "Art. 119-121",
        "standard_risk_weight": 0.20,
        "description": "Exposures to credit institutions and investment firms. "
                       "CQS-based: 20-150%. Short-term claims may attract lower weights.",
    },
    {
        "class_id": "corporates",
        "label": "Corporates",
        "crr_article": "Art. 122",
        "standard_risk_weight": 1.00,
        "description": "Exposures to corporates. CQS-based: 20-150%. "
                       "Unrated corporates receive 100% risk weight.",
    },
    {
        "class_id": "retail",
        "label": "Retail exposures",
        "crr_article": "Art. 123",
        "standard_risk_weight": 0.75,
        "description": "Qualifying retail: natural persons or SMEs, granular portfolio, "
                       "individual exposure < EUR 1m. Fixed 75% risk weight.",
    },
    {
        "class_id": "secured_immovable_property",
        "label": "Secured by immovable property",
        "crr_article": "Art. 124-126",
        "standard_risk_weight": 0.35,
        "description": "Exposures secured by residential (35%) or commercial (50%) "
                       "real estate meeting CRR eligibility criteria.",
    },
    {
        "class_id": "past_due",
        "label": "Exposures in default",
        "crr_article": "Art. 127",
        "standard_risk_weight": 1.00,
        "description": "Past-due > 90 days or unlikely to pay. 100% if provisions >= 20% "
                       "of unsecured part; 150% otherwise.",
    },
    {
        "class_id": "high_risk",
        "label": "High-risk categories",
        "crr_article": "Art. 128",
        "standard_risk_weight": 1.50,
        "description": "Venture capital, private equity, speculative immovable property "
                       "financing. Fixed 150% risk weight.",
    },
    {
        "class_id": "covered_bonds",
        "label": "Covered bonds",
        "crr_article": "Art. 129",
        "standard_risk_weight": 0.10,
        "description": "Bonds backed by qualifying cover pools per CRR Art. 129. "
                       "Risk weights 10-50% based on issuer CQS.",
    },
    {
        "class_id": "equity",
        "label": "Equity exposures",
        "crr_article": "Art. 133",
        "standard_risk_weight": 1.00,
        "description": "Equity holdings in non-deducted instruments. 100% for listed, "
                       "250% for significant investments, 400% for venture capital.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  REFERENCE DATA — STANDARDISED APPROACH RISK WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

# CQS → risk weight mapping per exposure class (as decimal fractions)
# CQS 0 means "unrated"
BASEL_SA_RISK_WEIGHTS: dict[str, dict[int, float]] = {
    "central_governments": {
        1: 0.00,   # AAA to AA-
        2: 0.20,   # A+ to A-
        3: 0.50,   # BBB+ to BBB-
        4: 1.00,   # BB+ to BB-
        5: 1.00,   # B+ to B-
        6: 1.50,   # CCC+ and below
        0: 1.00,   # Unrated
    },
    "regional_governments": {
        1: 0.00, 2: 0.20, 3: 0.50, 4: 1.00, 5: 1.00, 6: 1.50, 0: 1.00,
    },
    "public_sector_entities": {
        1: 0.20, 2: 0.20, 3: 0.50, 4: 1.00, 5: 1.00, 6: 1.50, 0: 1.00,
    },
    "multilateral_dev_banks": {
        1: 0.00, 2: 0.20, 3: 0.50, 4: 1.00, 5: 1.00, 6: 1.50, 0: 0.50,
    },
    "international_organisations": {
        1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00, 5: 0.00, 6: 0.00, 0: 0.00,
    },
    "institutions": {
        1: 0.20,   # AAA to AA-
        2: 0.50,   # A+ to A-
        3: 0.50,   # BBB+ to BBB-
        4: 1.00,   # BB+ to BB-
        5: 1.00,   # B+ to B-
        6: 1.50,   # CCC+ and below
        0: 0.50,   # Unrated
    },
    "corporates": {
        1: 0.20,   # AAA to AA-
        2: 0.50,   # A+ to A-
        3: 1.00,   # BBB+ to BBB-
        4: 1.00,   # BB+ to BB-
        5: 1.50,   # B+ to B-
        6: 1.50,   # CCC+ and below
        0: 1.00,   # Unrated
    },
    "retail": {
        1: 0.75, 2: 0.75, 3: 0.75, 4: 0.75, 5: 0.75, 6: 0.75, 0: 0.75,
    },
    "secured_immovable_property": {
        # Residential default; commercial handled separately
        1: 0.35, 2: 0.35, 3: 0.35, 4: 0.35, 5: 0.35, 6: 0.35, 0: 0.35,
    },
    "past_due": {
        # 150% if specific provisions < 20%; 100% if >= 20%
        1: 1.00, 2: 1.00, 3: 1.00, 4: 1.50, 5: 1.50, 6: 1.50, 0: 1.50,
    },
    "high_risk": {
        1: 1.50, 2: 1.50, 3: 1.50, 4: 1.50, 5: 1.50, 6: 1.50, 0: 1.50,
    },
    "covered_bonds": {
        1: 0.10, 2: 0.20, 3: 0.20, 4: 0.50, 5: 0.50, 6: 1.00, 0: 0.50,
    },
    "equity": {
        1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.50, 6: 1.50, 0: 1.00,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  REFERENCE DATA — IRB PARAMETERS  (CRR Article 153)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_IRB_PARAMETERS: dict[str, object] = {
    "description": "Internal Ratings Based approach parameters per CRR Art. 153",
    "asset_correlation_formula": (
        "R = 0.12 * (1 - EXP(-50*PD)) / (1 - EXP(-50)) "
        "+ 0.24 * (1 - (1 - EXP(-50*PD)) / (1 - EXP(-50)))"
    ),
    "maturity_adjustment_formula": "b = (0.11852 - 0.05478 * ln(PD))^2",
    "capital_requirement_formula": (
        "K = [LGD * N((1/(1-R))^0.5 * G(PD) + (R/(1-R))^0.5 * G(0.999)) "
        "- PD * LGD] * (1 + (M - 2.5) * b) / (1 - 1.5 * b)"
    ),
    "rwa_formula": "RWA = K * 12.5 * EAD",
    "correlation_bounds": {"R_min": 0.12, "R_max": 0.24},
    "maturity_bounds": {"M_min": 1.0, "M_max": 5.0},
    "confidence_level": 0.999,
    "sme_firm_size_adjustment": (
        "R_adj = R - 0.04 * (1 - (min(max(S, 5), 50) - 5) / 45) "
        "where S = annual turnover in EUR million"
    ),
    "retail_correlations": {
        "residential_mortgage": {"R_fixed": 0.15},
        "qualifying_revolving": {"R_fixed": 0.04},
        "other_retail": {"R_min": 0.03, "R_max": 0.16},
    },
    "floor_pd": 0.0003,  # 3 bps PD floor for corporates under Basel III.1
    "floor_lgd_unsecured": 0.25,  # 25% LGD floor for unsecured corporate (FIRB)
    "floor_lgd_secured_re": 0.10,  # 10% LGD floor for residential mortgage
    "floor_lgd_secured_commercial": 0.15,  # 15% LGD floor for commercial RE
}


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  REFERENCE DATA — MINIMUM CAPITAL REQUIREMENTS  (CRR Article 92)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_CAPITAL_REQUIREMENTS: dict[str, float] = {
    "cet1_minimum_pct": 4.5,
    "tier1_minimum_pct": 6.0,
    "total_capital_minimum_pct": 8.0,
    "capital_conservation_buffer_pct": 2.5,
    "countercyclical_buffer_default_pct": 0.0,
    "leverage_ratio_minimum_pct": 3.0,
    "fully_loaded_cet1_pct": 7.0,       # 4.5% + 2.5% CCB
    "fully_loaded_tier1_pct": 8.5,       # 6.0% + 2.5% CCB
    "fully_loaded_total_pct": 10.5,      # 8.0% + 2.5% CCB
    "output_floor_pct": 72.5,            # Basel III.1 final (2028 phase-in target)
    "output_floor_transitional_2025_pct": 50.0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  REFERENCE DATA — CAPITAL BUFFERS  (CRD V)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_CAPITAL_BUFFERS: dict[str, object] = {
    "conservation_buffer_pct": 2.5,
    "countercyclical_buffer_range": (0.0, 2.5),
    "systemic_risk_buffer_range": (0.0, 5.0),
    "gsib_buckets": {
        1: 1.0,   # Bucket 1: 1.0% of RWA
        2: 1.5,   # Bucket 2: 1.5%
        3: 2.0,   # Bucket 3: 2.0%
        4: 2.5,   # Bucket 4: 2.5%
        5: 3.5,   # Bucket 5: 3.5% (empty bucket)
    },
    "dsib_range": (0.0, 3.0),
    "mda_trigger": (
        "Maximum Distributable Amount restrictions apply when CET1 falls "
        "below combined buffer requirement (CBR = CCB + CCyB + SRB + G-SIB/D-SIB)"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  REFERENCE DATA — LCR PARAMETERS  (BCBS d295 / CRR Art. 412)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_LCR_PARAMETERS: dict[str, object] = {
    "hqla_classification": {
        "level_1": {
            "description": "Central bank reserves, sovereign bonds (CQS 1), cash",
            "haircut_pct": 0.0,
            "cap_pct": None,  # unlimited
            "examples": ["central_bank_reserves", "sovereign_bonds_cqs1", "cash"],
        },
        "level_2a": {
            "description": "Corporate bonds AA- or better, covered bonds AA- or better",
            "haircut_pct": 15.0,
            "cap_pct": 40.0,  # max 40% of total HQLA
            "examples": ["corporate_bonds_aa", "covered_bonds_aa", "sovereign_bonds_cqs2"],
        },
        "level_2b": {
            "description": "Corporate bonds A+ to BBB-, RMBS, equities in major index",
            "haircut_pct": 50.0,
            "cap_pct": 15.0,  # max 15% of total HQLA
            "examples": ["corporate_bonds_bbb", "rmbs_aa", "listed_equities"],
        },
    },
    "outflow_rates": {
        "retail_deposits_stable": 0.05,            # 5%  — insured, operational
        "retail_deposits_less_stable": 0.10,        # 10% — uninsured retail
        "wholesale_unsecured_operational": 0.25,    # 25% — operational deposits
        "wholesale_unsecured_non_operational": 0.40, # 40% — non-operational
        "wholesale_unsecured_financial": 1.00,      # 100% — financial institution deposits
        "wholesale_secured_level1": 0.00,           # 0%  — secured by Level 1 HQLA
        "wholesale_secured_level2a": 0.15,          # 15% — secured by Level 2A
        "wholesale_secured_other": 1.00,            # 100% — secured by non-HQLA
        "credit_facilities_retail": 0.05,           # 5%  — undrawn retail credit lines
        "credit_facilities_corporate": 0.10,        # 10% — undrawn wholesale lines (non-fin)
        "credit_facilities_financial": 1.00,        # 100% — undrawn lines to financial inst.
        "derivative_outflows": 1.00,                # 100% — collateral calls
    },
    "inflow_rates": {
        "retail_lending": 0.50,             # 50% of contractual inflows
        "wholesale_lending_non_fin": 0.50,  # 50%
        "wholesale_lending_financial": 1.00, # 100%
        "securities_maturing": 1.00,        # 100%
    },
    "inflow_cap_pct": 75.0,  # inflows capped at 75% of total outflows
    "minimum_lcr_pct": 100.0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  REFERENCE DATA — NSFR PARAMETERS  (BCBS d396 / CRR II Art. 428a)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_NSFR_PARAMETERS: dict[str, object] = {
    "asf_factors": {
        "capital_instruments": 1.00,                # CET1, AT1, Tier 2 (residual > 1yr)
        "retail_deposits_stable": 0.95,             # insured, operational
        "retail_deposits_less_stable": 0.90,        # uninsured retail
        "wholesale_deposits_operational": 0.50,     # operational (financial inst. < 1yr)
        "wholesale_deposits_non_operational": 0.50, # non-operational < 1yr
        "wholesale_funding_gt1yr": 1.00,            # any funding > 1 year residual
        "other_liabilities_lt6m": 0.00,             # short-term non-deposit
        "other_liabilities_6m_1yr": 0.50,           # medium-term
    },
    "rsf_factors": {
        "cash": 0.00,
        "central_bank_reserves": 0.00,
        "sovereign_bonds_cqs1": 0.05,
        "sovereign_bonds_cqs2": 0.15,
        "corporate_bonds_aa": 0.15,
        "covered_bonds_aa": 0.15,
        "corporate_bonds_bbb": 0.50,
        "listed_equities": 0.50,
        "residential_mortgages_performing": 0.65,
        "retail_loans_performing": 0.65,
        "sme_loans_performing": 0.85,
        "corporate_loans_lt1yr": 0.50,
        "corporate_loans_gt1yr": 0.85,
        "non_performing_loans": 1.00,
        "fixed_assets": 1.00,
        "other_assets": 1.00,
    },
    "minimum_nsfr_pct": 100.0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  REFERENCE DATA — CLIMATE RISK CAPITAL ADJUSTMENTS  (EBA GL/2022/02)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_CLIMATE_ADJUSTMENTS: dict[str, object] = {
    "transition_risk_multiplier": {
        # NACE section letter -> RWA multiplier
        "A": 1.08,   # Agriculture — moderate deforestation / land-use
        "B": 1.25,   # Mining — high stranded-asset + carbon exposure
        "C": 1.15,   # Manufacturing — energy-intensity dependent
        "D": 1.25,   # Electricity/gas — fossil-fuel phase-out
        "E": 1.05,   # Water/waste — minor methane
        "F": 1.10,   # Construction — embodied carbon regulation
        "G": 1.02,   # Wholesale/retail — low direct risk
        "H": 1.18,   # Transport — fleet electrification cost
        "I": 1.02,   # Accommodation/food — minor
        "J": 0.98,   # ICT — net beneficiary
        "K": 1.00,   # Financial services — pass-through
        "L": 1.08,   # Real estate — MEPS / EPC regulations
        "M": 0.98,   # Professional services — net beneficiary
        "N": 1.00,   # Admin services
        "O": 1.00,   # Public admin — benchmark
        "P": 1.00,   # Education
        "Q": 1.00,   # Health
        "R": 1.00,   # Arts/recreation
        "S": 1.00,   # Other services
        "T": 1.00,   # Households
        "U": 1.00,   # Extraterritorial
    },
    "physical_risk_multiplier": {
        "high_risk": 1.20,    # coastal flood, extreme heat, wildfire zones
        "medium_risk": 1.10,  # moderate climate exposure
        "low_risk": 1.00,     # minimal physical risk
    },
    "green_supporting_factor": 0.7619,  # CRR Art. 501a — qualifying infra / SME green
    "brown_penalising_factor": 1.25,    # proposed for high-carbon exposures (EBA 2023)
    "green_asset_eligibility": (
        "Exposures qualifying under EU Taxonomy (Art. 3 Reg. 2020/852) "
        "and meeting DNSH + minimum social safeguards criteria"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  REFERENCE DATA — REGULATORY FRAMEWORKS
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_REGULATORY_FRAMEWORKS: list[dict] = [
    {"code": "CRR", "full_name": "Capital Requirements Regulation",
     "reference": "EU 575/2013", "scope": "Pillar 1 — prudential requirements"},
    {"code": "CRR_II", "full_name": "CRR II Amendments",
     "reference": "EU 2019/876", "scope": "NSFR, TLAC, FRTB, leverage ratio"},
    {"code": "CRR_III", "full_name": "CRR III — Basel III.1 EU implementation",
     "reference": "EU 2024/1623", "scope": "Output floor, revised SA, FRTB final"},
    {"code": "CRD_IV", "full_name": "Capital Requirements Directive IV",
     "reference": "EU 2013/36/EU", "scope": "Supervisory framework, buffers"},
    {"code": "CRD_V", "full_name": "CRD V Amendments",
     "reference": "EU 2019/878/EU", "scope": "Pillar 2 guidance, buffers, fit & proper"},
    {"code": "BASEL_III_FINAL", "full_name": "Basel III: Finalising post-crisis reforms",
     "reference": "BCBS d424 (Dec 2017)", "scope": "Output floor, revised IRB, SA credit"},
    {"code": "EBA_GL_CREDIT", "full_name": "EBA Guidelines on credit risk assessment",
     "reference": "EBA GL/2017/06", "scope": "ECAI mapping, CQS assignment"},
    {"code": "EBA_GL_ESG", "full_name": "EBA Guidelines on ESG risks",
     "reference": "EBA GL/2022/02", "scope": "ESG risk integration in supervision"},
    {"code": "BCBS_239", "full_name": "Principles for risk data aggregation",
     "reference": "BCBS 239 (Jan 2013)", "scope": "Data governance, accuracy, timeliness"},
    {"code": "BCBS_LCR", "full_name": "Liquidity Coverage Ratio",
     "reference": "BCBS d295 (Jan 2013)", "scope": "30-day stress liquidity"},
    {"code": "BCBS_NSFR", "full_name": "Net Stable Funding Ratio",
     "reference": "BCBS d396 (Oct 2014)", "scope": "Structural liquidity"},
    {"code": "BCBS_FRTB", "full_name": "Fundamental Review of the Trading Book",
     "reference": "BCBS d457 (Jan 2019)", "scope": "Market risk SA + IMA"},
    {"code": "BCBS_SMA", "full_name": "Standardised Measurement Approach",
     "reference": "BCBS d563 (Dec 2022)", "scope": "Operational risk capital"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# 10. REFERENCE DATA — OPERATIONAL RISK  (SMA — BCBS d563)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_OPERATIONAL_RISK: dict[str, object] = {
    "description": "Standardised Measurement Approach (SMA) per BCBS d563 / CRR III",
    "bic_components": {
        "interest_lease_dividend": (
            "ILDC = min(abs(interest_income - interest_expense), 2.25% * interest_earning_assets) "
            "+ dividend_income"
        ),
        "services": "SC = max(fee_income, fee_expense) + max(other_operating_income, other_operating_expense)",
        "financial": "FC = abs(net_trading_income) + abs(net_banking_book_income)",
    },
    "bic_buckets": [
        # (lower_bound_eur, upper_bound_eur, marginal_coefficient)
        (0,               1_000_000_000,  0.12),   # Bucket 1: 12%
        (1_000_000_000,   30_000_000_000, 0.15),   # Bucket 2: 15%
        (30_000_000_000,  float("inf"),   0.18),   # Bucket 3: 18%
    ],
    "ilm_formula": "ILM = ln(exp(1) - 1 + (LC / BIC)^0.8)",
    "ilm_floor": 1.0,  # supervisory discretion: ILM >= 1.0 in some jurisdictions
    "loss_component_multiplier": 15.0,  # LC = 15 × average annual losses (10 years)
}


# ═══════════════════════════════════════════════════════════════════════════════
# 11. REFERENCE DATA — MARKET RISK  (Simplified FRTB SA)
# ═══════════════════════════════════════════════════════════════════════════════

BASEL_MARKET_RISK: dict[str, object] = {
    "description": "Simplified FRTB Standardised Approach components",
    "sbm_risk_classes": [
        "GIRR",        # General interest rate risk
        "CSR_non_sec", # Credit spread risk (non-securitisations)
        "CSR_sec",     # Credit spread risk (securitisations non-CTP)
        "CSR_CTP",     # Credit spread risk (correlation trading portfolio)
        "equity",      # Equity risk
        "commodity",   # Commodity risk
        "fx",          # Foreign exchange risk
    ],
    "default_risk_charge": {
        "description": "Jump-to-default charge for credit instruments",
        "net_jtd_formula": "Net JTD = max(LGD * notional * max(1 + cumPnL, 0), 0)",
    },
    "residual_risk_addon": {
        "exotic_notional_pct": 0.01,   # 1.0% of notional for exotic underlyings
        "other_residual_pct": 0.001,   # 0.1% of notional for other residuals
    },
    "simplified_rwa_pct_of_trading_book": 0.08,  # fallback 8% if no detailed data
}


# ═══════════════════════════════════════════════════════════════════════════════
# 12. RESULT DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExposureRiskWeight:
    """Per-exposure risk weight and RWA result."""
    exposure_id: str
    counterparty_name: str
    exposure_class: str
    credit_quality_step: int           # 0 = unrated, 1-6 = CQS
    ead_eur: float                     # Exposure at Default
    pd: float                          # Probability of Default (0-1)
    lgd: float                         # Loss Given Default (0-1)
    maturity_years: float
    risk_weight: float                 # as decimal (e.g. 0.75 = 75%)
    rwa_eur: float                     # Risk-Weighted Assets
    approach: str                      # "standardised" or "irb"
    climate_adjustment: float          # multiplier applied
    sector: str                        # NACE section letter


@dataclass
class CapitalRequirementResult:
    """Full capital adequacy result per CRR Article 92."""
    entity_name: str
    reporting_date: str
    approach: str                      # "standardised", "irb", "mixed"
    # RWA breakdown
    total_rwa_credit: float
    total_rwa_market: float
    total_rwa_operational: float
    total_rwa: float
    # Capital components
    cet1_capital: float
    at1_capital: float
    tier1_capital: float
    tier2_capital: float
    total_capital: float
    # Ratios
    cet1_ratio: float                  # CET1 / RWA
    tier1_ratio: float                 # Tier 1 / RWA
    total_capital_ratio: float         # Total Capital / RWA
    leverage_ratio: float              # Tier 1 / Total Exposure Measure
    # Buffers
    capital_conservation_buffer: float
    countercyclical_buffer: float
    systemic_buffer: float
    combined_buffer_requirement: float
    # Surplus / deficit vs minimum + buffers
    cet1_surplus_deficit: float
    tier1_surplus_deficit: float
    total_surplus_deficit: float
    # Climate add-on
    climate_rwa_addon: float
    # Breakdown
    exposure_class_breakdown: list = field(default_factory=list)
    regulatory_breaches: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


@dataclass
class LiquidityResult:
    """LCR + NSFR liquidity assessment result."""
    entity_name: str
    reporting_date: str
    # LCR
    hqla_total: float
    total_net_cash_outflows: float
    lcr_ratio: float
    lcr_compliant: bool
    # NSFR
    available_stable_funding: float
    required_stable_funding: float
    nsfr_ratio: float
    nsfr_compliant: bool
    # Composition
    hqla_composition: dict = field(default_factory=dict)
    lcr_stress_scenarios: list = field(default_factory=list)


@dataclass
class CapitalAdequacyDashboard:
    """Orchestrated capital adequacy assessment with RAG status."""
    entity_name: str
    reporting_date: str
    capital_requirement: Optional[CapitalRequirementResult] = None
    liquidity: Optional[LiquidityResult] = None
    climate_stress_impact: dict = field(default_factory=dict)
    bcbs239_compliance_score: float = 0.0
    pillar2_recommendations: list = field(default_factory=list)
    overall_rag_status: str = "GREEN"
    cross_framework_mapping: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# 13. MATHS UTILITIES — Normal distribution (no scipy dependency)
# ═══════════════════════════════════════════════════════════════════════════════

def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_inv(p: float) -> float:
    """
    Inverse standard normal CDF (quantile function).

    Uses the rational approximation by Peter Acklam (2003) which is accurate
    to approximately 1.15e-9 in the full range (0, 1).

    Reference: Abramowitz & Stegun, Handbook of Mathematical Functions,
    refined by P.J. Acklam.
    """
    if p <= 0.0:
        return -10.0  # practical -infinity clamp
    if p >= 1.0:
        return 10.0   # practical +infinity clamp

    # Coefficients for rational approximation
    a1 = -3.969683028665376e+01
    a2 = 2.209460984245205e+02
    a3 = -2.759285104469687e+02
    a4 = 1.383577518672690e+02
    a5 = -3.066479806614716e+01
    a6 = 2.506628277459239e+00

    b1 = -5.447609879822406e+01
    b2 = 1.615858368580409e+02
    b3 = -1.556989798598866e+02
    b4 = 6.680131188771972e+01
    b5 = -1.328068155288572e+01

    c1 = -7.784894002430293e-03
    c2 = -3.223964580411365e-01
    c3 = -2.400758277161838e+00
    c4 = -2.549732539343734e+00
    c5 = 4.374664141464968e+00
    c6 = 2.938163982698783e+00

    d1 = 7.784695709041462e-03
    d2 = 3.224671290700398e-01
    d3 = 2.445134137142996e+00
    d4 = 3.754408661907416e+00

    p_low = 0.02425
    p_high = 1.0 - p_low

    if p < p_low:
        # Lower tail
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / \
               ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0)
    elif p <= p_high:
        # Central region
        q = p - 0.5
        r = q * q
        return (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q / \
               (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0)
    else:
        # Upper tail
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / \
                ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 14. BASEL CAPITAL ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class BaselCapitalEngine:
    """
    Basel III/IV Regulatory Capital Engine.

    Implements CRR Articles 92/112-153 for Standardised Approach and Foundation IRB
    credit risk capital, plus LCR/NSFR liquidity ratios, operational risk (SMA),
    simplified market risk, and climate risk capital add-ons (EBA GL/2022/02).
    """

    # -----------------------------------------------------------------------
    # 14.1  Standardised Approach Risk Weights  (CRR Art. 114-134)
    # -----------------------------------------------------------------------

    def calculate_sa_risk_weight(
        self,
        exposure_class: str,
        credit_quality_step: int = 0,
        secured_by_property: Optional[str] = None,
    ) -> float:
        """
        Return SA risk weight as decimal for a given exposure class and CQS.

        Parameters
        ----------
        exposure_class : str
            One of the 13 CRR Art. 112 exposure class IDs.
        credit_quality_step : int
            0 = unrated, 1-6 = external credit quality step (ECAI mapping).
        secured_by_property : str or None
            If the exposure is "secured_immovable_property", specify
            "residential" or "commercial" to select the appropriate weight.

        Returns
        -------
        float
            Risk weight as decimal (e.g. 0.35 for 35%).
        """
        # Property-secured exposures — Art. 124/125/126
        if exposure_class == "secured_immovable_property" or secured_by_property:
            if secured_by_property == "commercial":
                return 0.50
            return 0.35  # residential default

        # Past-due: 150% if CQS >= 4 or unrated; 100% if CQS 1-3 (well-provisioned)
        if exposure_class == "past_due":
            if credit_quality_step == 0 or credit_quality_step >= 4:
                return 1.50
            return 1.00

        # Look up in SA risk weight table
        class_weights = BASEL_SA_RISK_WEIGHTS.get(exposure_class)
        if class_weights is None:
            return 1.00  # fallback: 100%

        cqs = credit_quality_step if credit_quality_step in class_weights else 0
        return class_weights.get(cqs, 1.00)

    # -----------------------------------------------------------------------
    # 14.2  IRB Risk Weight  (CRR Article 153)
    # -----------------------------------------------------------------------

    def calculate_irb_risk_weight(
        self,
        pd: float,
        lgd: float,
        maturity: float = 2.5,
        exposure_class: str = "corporates",
    ) -> float:
        """
        Calculate IRB risk weight per CRR Article 153 (corporate formula).

        Implements:
          R  = 0.12 * f(PD) + 0.24 * (1 - f(PD))   where f(PD) = (1 - e^{-50*PD}) / (1 - e^{-50})
          b  = (0.11852 - 0.05478 * ln(PD))^2
          K  = [LGD * N(sqrt(1/(1-R)) * G(PD) + sqrt(R/(1-R)) * G(0.999)) - PD * LGD]
               * (1 + (M - 2.5) * b) / (1 - 1.5 * b)
          RW = K * 12.5

        Parameters
        ----------
        pd : float
            Probability of Default, range (0, 1).
        lgd : float
            Loss Given Default, range (0, 1).
        maturity : float
            Effective maturity in years (1-5, clamped).
        exposure_class : str
            "corporates", "institutions", "retail", etc.

        Returns
        -------
        float
            Risk weight as decimal. Multiply by EAD for RWA contribution.
        """
        # Apply PD floor (Basel III.1: 3 bps for corporates)
        pd = max(pd, 0.0003)

        # Clamp maturity
        maturity = max(1.0, min(maturity, 5.0))

        # Retail: use fixed correlation, no maturity adjustment
        if exposure_class == "retail":
            return self._irb_retail_rw(pd, lgd)

        # Corporate / institution / sovereign formula
        # Asset correlation R
        exp_neg50 = math.exp(-50.0)
        denom = 1.0 - exp_neg50
        f_pd = (1.0 - math.exp(-50.0 * pd)) / denom
        r = 0.12 * f_pd + 0.24 * (1.0 - f_pd)

        # Maturity adjustment b
        ln_pd = math.log(max(pd, 1e-10))
        b = (0.11852 - 0.05478 * ln_pd) ** 2

        # Capital requirement K
        g_pd = _norm_inv(pd)
        g_999 = _norm_inv(0.999)

        sqrt_1_over_1_minus_r = math.sqrt(1.0 / (1.0 - r))
        sqrt_r_over_1_minus_r = math.sqrt(r / (1.0 - r))

        conditional_pd = _norm_cdf(sqrt_1_over_1_minus_r * g_pd + sqrt_r_over_1_minus_r * g_999)

        k = (lgd * conditional_pd - pd * lgd) * \
            (1.0 + (maturity - 2.5) * b) / (1.0 - 1.5 * b)

        # Ensure non-negative
        k = max(k, 0.0)

        # Risk weight = K * 12.5
        return k * 12.5

    def _irb_retail_rw(self, pd: float, lgd: float) -> float:
        """IRB risk weight for qualifying retail (fixed correlation, no maturity adj)."""
        # Other retail correlation: R = 0.03 * f(PD) + 0.16 * (1 - f(PD))
        exp_neg35 = math.exp(-35.0)
        denom = 1.0 - exp_neg35
        f_pd = (1.0 - math.exp(-35.0 * pd)) / denom
        r = 0.03 * f_pd + 0.16 * (1.0 - f_pd)

        g_pd = _norm_inv(pd)
        g_999 = _norm_inv(0.999)

        sqrt_1_over_1_minus_r = math.sqrt(1.0 / (1.0 - r))
        sqrt_r_over_1_minus_r = math.sqrt(r / (1.0 - r))

        conditional_pd = _norm_cdf(sqrt_1_over_1_minus_r * g_pd + sqrt_r_over_1_minus_r * g_999)

        k = lgd * conditional_pd - pd * lgd
        k = max(k, 0.0)
        return k * 12.5

    # -----------------------------------------------------------------------
    # 14.3  Operational Risk — SMA  (BCBS d563)
    # -----------------------------------------------------------------------

    def calculate_operational_risk_rwa(
        self,
        business_indicator: float,
        average_annual_losses: float = 0.0,
    ) -> float:
        """
        Calculate operational risk RWA using the Standardised Measurement Approach.

        Parameters
        ----------
        business_indicator : float
            BIC = ILDC + SC + FC (EUR).
        average_annual_losses : float
            10-year average annual operational losses (EUR).

        Returns
        -------
        float
            Operational risk RWA (capital charge * 12.5).
        """
        # BIC marginal coefficients
        buckets = BASEL_OPERATIONAL_RISK["bic_buckets"]
        bic_component = 0.0
        remaining = business_indicator

        for lower, upper, coeff in buckets:
            if remaining <= 0:
                break
            bucket_amount = min(remaining, upper - lower)
            bic_component += bucket_amount * coeff
            remaining -= bucket_amount

        # Loss component
        lc = 15.0 * average_annual_losses

        # Internal Loss Multiplier
        if bic_component > 0 and lc > 0:
            ratio = (lc / bic_component) ** 0.8
            ilm = math.log(math.exp(1.0) - 1.0 + ratio)
            ilm = max(ilm, 1.0)  # ILM floor
        else:
            ilm = 1.0

        op_risk_capital = bic_component * ilm
        return op_risk_capital * 12.5

    # -----------------------------------------------------------------------
    # 14.4  Capital Requirement  (CRR Article 92)
    # -----------------------------------------------------------------------

    def calculate_capital_requirement(
        self,
        entity_name: str,
        reporting_date: str,
        exposures: list,
        capital: dict,
        approach: str = "standardised",
        climate_adjusted: bool = True,
        buffers: Optional[dict] = None,
        market_risk_rwa: float = 0.0,
        operational_risk_rwa: float = 0.0,
    ) -> CapitalRequirementResult:
        """
        Calculate full capital adequacy per CRR Article 92.

        Parameters
        ----------
        entity_name : str
            Legal entity name.
        reporting_date : str
            Reporting date (YYYY-MM-DD).
        exposures : list[dict]
            Each dict: counterparty_name, exposure_class, ead_eur, pd (0-1),
            lgd (0-1), maturity_years, credit_quality_step (0-6), sector (NACE letter),
            physical_risk_zone (optional: high_risk/medium_risk/low_risk),
            is_green (optional: bool).
        capital : dict
            Keys: cet1, at1, tier2, total_exposure_measure.
        approach : str
            "standardised" or "irb".
        climate_adjusted : bool
            Apply EBA GL/2022/02 climate risk multipliers.
        buffers : dict or None
            Override buffer rates: countercyclical_buffer_pct, systemic_buffer_pct,
            gsib_bucket (1-5), dsib_pct.
        market_risk_rwa : float
            Pre-calculated market risk RWA (or 0 for credit-only).
        operational_risk_rwa : float
            Pre-calculated operational risk RWA (or 0 for credit-only).

        Returns
        -------
        CapitalRequirementResult
        """
        buffers = buffers or {}
        exposure_results: list[ExposureRiskWeight] = []
        total_rwa_credit = 0.0
        total_climate_addon = 0.0

        # Per-exposure class aggregation
        class_agg: dict[str, dict] = {}

        for idx, exp in enumerate(exposures):
            exp_class = exp.get("exposure_class", "corporates")
            cqs = exp.get("credit_quality_step", 0)
            ead = exp.get("ead_eur", 0.0)
            pd_val = exp.get("pd", 0.01)
            lgd_val = exp.get("lgd", 0.45)
            mat = exp.get("maturity_years", 2.5)
            sector = exp.get("sector", "K")
            phys_zone = exp.get("physical_risk_zone", "low_risk")
            is_green = exp.get("is_green", False)
            cpty_name = exp.get("counterparty_name", f"Exposure_{idx+1}")

            # Risk weight
            if approach == "irb":
                rw = self.calculate_irb_risk_weight(pd_val, lgd_val, mat, exp_class)
            else:
                rw = self.calculate_sa_risk_weight(
                    exp_class, cqs,
                    secured_by_property=exp.get("secured_by_property"),
                )

            # Climate adjustment
            climate_mult = 1.0
            if climate_adjusted:
                trans_mult = BASEL_CLIMATE_ADJUSTMENTS["transition_risk_multiplier"].get(sector, 1.0)
                phys_mult = BASEL_CLIMATE_ADJUSTMENTS["physical_risk_multiplier"].get(phys_zone, 1.0)
                climate_mult = trans_mult * phys_mult

                # Green supporting factor
                if is_green:
                    climate_mult *= BASEL_CLIMATE_ADJUSTMENTS["green_supporting_factor"]

            rwa = ead * rw * climate_mult
            climate_addon = ead * rw * (climate_mult - 1.0) if climate_mult != 1.0 else 0.0

            total_rwa_credit += rwa
            total_climate_addon += climate_addon

            # Aggregate by class
            if exp_class not in class_agg:
                class_agg[exp_class] = {"ead": 0.0, "rwa": 0.0, "count": 0}
            class_agg[exp_class]["ead"] += ead
            class_agg[exp_class]["rwa"] += rwa
            class_agg[exp_class]["count"] += 1

            exposure_results.append(ExposureRiskWeight(
                exposure_id=f"EXP-{idx+1:05d}",
                counterparty_name=cpty_name,
                exposure_class=exp_class,
                credit_quality_step=cqs,
                ead_eur=round(ead, 2),
                pd=pd_val,
                lgd=lgd_val,
                maturity_years=mat,
                risk_weight=round(rw * climate_mult, 6),
                rwa_eur=round(rwa, 2),
                approach=approach,
                climate_adjustment=round(climate_mult, 6),
                sector=sector,
            ))

        # Exposure class breakdown
        ec_breakdown = []
        for cls_id, agg in class_agg.items():
            avg_rw = agg["rwa"] / agg["ead"] if agg["ead"] > 0 else 0.0
            ec_breakdown.append({
                "exposure_class": cls_id,
                "ead_eur": round(agg["ead"], 2),
                "rwa_eur": round(agg["rwa"], 2),
                "avg_risk_weight": round(avg_rw, 4),
                "count": agg["count"],
            })

        # Total RWA
        total_rwa = total_rwa_credit + market_risk_rwa + operational_risk_rwa

        # Capital components
        cet1 = capital.get("cet1", 0.0)
        at1 = capital.get("at1", 0.0)
        tier1 = cet1 + at1
        tier2 = capital.get("tier2", 0.0)
        total_cap = tier1 + tier2
        total_exposure_measure = capital.get("total_exposure_measure", total_rwa)

        # Ratios (guard against zero RWA)
        if total_rwa > 0:
            cet1_ratio = cet1 / total_rwa
            tier1_ratio = tier1 / total_rwa
            total_ratio = total_cap / total_rwa
        else:
            cet1_ratio = 1.0
            tier1_ratio = 1.0
            total_ratio = 1.0

        leverage_ratio = tier1 / total_exposure_measure if total_exposure_measure > 0 else 0.0

        # Buffers
        ccb = BASEL_CAPITAL_REQUIREMENTS["capital_conservation_buffer_pct"] / 100.0
        ccyb = buffers.get("countercyclical_buffer_pct", 0.0) / 100.0
        systemic = buffers.get("systemic_buffer_pct", 0.0) / 100.0
        gsib_bucket = buffers.get("gsib_bucket", 0)
        gsib_pct = BASEL_CAPITAL_BUFFERS["gsib_buckets"].get(gsib_bucket, 0.0) / 100.0
        dsib_pct = buffers.get("dsib_pct", 0.0) / 100.0
        combined_buffer = ccb + ccyb + systemic + max(gsib_pct, dsib_pct)

        # Minimum requirements (as fractions)
        min_cet1 = 0.045
        min_tier1 = 0.06
        min_total = 0.08

        # Surplus / deficit vs minimum + buffers
        cet1_surplus = (cet1_ratio - min_cet1 - combined_buffer) * total_rwa
        tier1_surplus = (tier1_ratio - min_tier1 - combined_buffer) * total_rwa
        total_surplus = (total_ratio - min_total - combined_buffer) * total_rwa

        # Regulatory breach detection
        breaches = []
        if cet1_ratio < min_cet1:
            breaches.append(f"CET1 ratio {cet1_ratio*100:.2f}% below minimum 4.50%")
        if tier1_ratio < min_tier1:
            breaches.append(f"Tier 1 ratio {tier1_ratio*100:.2f}% below minimum 6.00%")
        if total_ratio < min_total:
            breaches.append(f"Total capital ratio {total_ratio*100:.2f}% below minimum 8.00%")
        if leverage_ratio < 0.03:
            breaches.append(f"Leverage ratio {leverage_ratio*100:.2f}% below minimum 3.00%")
        if cet1_ratio < min_cet1 + combined_buffer:
            breaches.append(
                f"CET1 ratio {cet1_ratio*100:.2f}% below combined buffer "
                f"requirement {(min_cet1 + combined_buffer)*100:.2f}% — MDA restrictions apply"
            )

        # Recommendations
        recommendations = []
        if cet1_surplus < 0:
            shortfall_eur = abs(cet1_surplus)
            recommendations.append(
                f"Raise CET1 capital by EUR {shortfall_eur:,.0f} to clear combined buffer requirement"
            )
        if leverage_ratio < 0.035:
            recommendations.append(
                "Leverage ratio near minimum — consider reducing total exposure measure "
                "or increasing Tier 1 capital"
            )
        if total_climate_addon > 0:
            recommendations.append(
                f"Climate risk adds EUR {total_climate_addon:,.0f} to RWA — "
                "review high-carbon exposures for transition risk mitigation"
            )
        if not breaches and not recommendations:
            recommendations.append("All capital ratios above minimum + buffer requirements")

        return CapitalRequirementResult(
            entity_name=entity_name,
            reporting_date=reporting_date,
            approach=approach,
            total_rwa_credit=round(total_rwa_credit, 2),
            total_rwa_market=round(market_risk_rwa, 2),
            total_rwa_operational=round(operational_risk_rwa, 2),
            total_rwa=round(total_rwa, 2),
            cet1_capital=round(cet1, 2),
            at1_capital=round(at1, 2),
            tier1_capital=round(tier1, 2),
            tier2_capital=round(tier2, 2),
            total_capital=round(total_cap, 2),
            cet1_ratio=round(cet1_ratio, 6),
            tier1_ratio=round(tier1_ratio, 6),
            total_capital_ratio=round(total_ratio, 6),
            leverage_ratio=round(leverage_ratio, 6),
            capital_conservation_buffer=round(ccb, 4),
            countercyclical_buffer=round(ccyb, 4),
            systemic_buffer=round(systemic + max(gsib_pct, dsib_pct), 4),
            combined_buffer_requirement=round(combined_buffer, 4),
            cet1_surplus_deficit=round(cet1_surplus, 2),
            tier1_surplus_deficit=round(tier1_surplus, 2),
            total_surplus_deficit=round(total_surplus, 2),
            climate_rwa_addon=round(total_climate_addon, 2),
            exposure_class_breakdown=ec_breakdown,
            regulatory_breaches=breaches,
            recommendations=recommendations,
        )

    # -----------------------------------------------------------------------
    # 14.5  Liquidity — LCR + NSFR
    # -----------------------------------------------------------------------

    def calculate_liquidity(
        self,
        entity_name: str,
        reporting_date: str,
        assets: dict,
        liabilities: dict,
    ) -> LiquidityResult:
        """
        Calculate LCR and NSFR per BCBS d295/d396.

        Parameters
        ----------
        entity_name : str
            Legal entity name.
        reporting_date : str
            Reporting date (YYYY-MM-DD).
        assets : dict
            Keys: level1_hqla, level2a_assets, level2b_assets,
            residential_mortgages, retail_loans, wholesale_loans,
            corporate_loans_lt1yr, corporate_loans_gt1yr, other_assets,
            sovereign_bonds_cqs2, fixed_assets, sme_loans.
        liabilities : dict
            Keys: retail_deposits_stable, retail_deposits_less_stable,
            wholesale_unsecured_operational, wholesale_unsecured_non_operational,
            wholesale_unsecured_financial, wholesale_secured_level1,
            wholesale_secured_level2a, wholesale_secured_other,
            credit_facilities_corporate, credit_facilities_financial,
            capital_instruments, wholesale_funding_gt1yr,
            other_liabilities_lt6m, other_liabilities_6m_1yr.

        Returns
        -------
        LiquidityResult
        """
        # === LCR ===

        # HQLA with haircuts
        level1 = assets.get("level1_hqla", 0.0)
        level2a_raw = assets.get("level2a_assets", 0.0)
        level2b_raw = assets.get("level2b_assets", 0.0)

        level2a = level2a_raw * (1.0 - 0.15)  # 15% haircut
        level2b = level2b_raw * (1.0 - 0.50)  # 50% haircut

        # Caps: Level 2A max 40% of total HQLA (after haircuts)
        # Level 2B max 15% of total HQLA
        # Iterative cap calculation
        total_hqla_uncapped = level1 + level2a + level2b
        if total_hqla_uncapped > 0:
            level2b_cap = total_hqla_uncapped * 0.15
            level2b = min(level2b, level2b_cap)

            total_level2 = level2a + level2b
            level2_cap = (level1 + total_level2) * 0.40
            if total_level2 > level2_cap:
                scale = level2_cap / total_level2 if total_level2 > 0 else 1.0
                level2a *= scale
                level2b *= scale

        total_hqla = level1 + level2a + level2b

        # Cash outflows (30-day stress)
        outflow_rates = BASEL_LCR_PARAMETERS["outflow_rates"]
        outflows = 0.0
        outflows += liabilities.get("retail_deposits_stable", 0.0) * outflow_rates["retail_deposits_stable"]
        outflows += liabilities.get("retail_deposits_less_stable", 0.0) * outflow_rates["retail_deposits_less_stable"]
        outflows += liabilities.get("wholesale_unsecured_operational", 0.0) * outflow_rates["wholesale_unsecured_operational"]
        outflows += liabilities.get("wholesale_unsecured_non_operational", 0.0) * outflow_rates["wholesale_unsecured_non_operational"]
        outflows += liabilities.get("wholesale_unsecured_financial", 0.0) * outflow_rates["wholesale_unsecured_financial"]
        outflows += liabilities.get("wholesale_secured_level1", 0.0) * outflow_rates["wholesale_secured_level1"]
        outflows += liabilities.get("wholesale_secured_level2a", 0.0) * outflow_rates["wholesale_secured_level2a"]
        outflows += liabilities.get("wholesale_secured_other", 0.0) * outflow_rates["wholesale_secured_other"]
        outflows += liabilities.get("credit_facilities_corporate", 0.0) * outflow_rates["credit_facilities_corporate"]
        outflows += liabilities.get("credit_facilities_financial", 0.0) * outflow_rates["credit_facilities_financial"]

        # Cash inflows (capped at 75% of outflows)
        inflow_rates = BASEL_LCR_PARAMETERS["inflow_rates"]
        inflows = 0.0
        inflows += assets.get("retail_loans", 0.0) * 0.05 * inflow_rates["retail_lending"]
        inflows += assets.get("wholesale_loans", 0.0) * 0.05 * inflow_rates["wholesale_lending_non_fin"]
        inflow_cap = outflows * 0.75
        inflows = min(inflows, inflow_cap)

        net_outflows = max(outflows - inflows, outflows * 0.25)

        lcr_ratio = total_hqla / net_outflows if net_outflows > 0 else 999.0
        lcr_compliant = lcr_ratio >= 1.0

        # === NSFR ===

        asf_factors = BASEL_NSFR_PARAMETERS["asf_factors"]
        rsf_factors = BABEL_NSFR_RSF = BASEL_NSFR_PARAMETERS["rsf_factors"]

        # Available Stable Funding
        asf = 0.0
        asf += liabilities.get("capital_instruments", 0.0) * asf_factors["capital_instruments"]
        asf += liabilities.get("retail_deposits_stable", 0.0) * asf_factors["retail_deposits_stable"]
        asf += liabilities.get("retail_deposits_less_stable", 0.0) * asf_factors["retail_deposits_less_stable"]
        asf += liabilities.get("wholesale_unsecured_operational", 0.0) * asf_factors["wholesale_deposits_operational"]
        asf += liabilities.get("wholesale_unsecured_non_operational", 0.0) * asf_factors["wholesale_deposits_non_operational"]
        asf += liabilities.get("wholesale_funding_gt1yr", 0.0) * asf_factors["wholesale_funding_gt1yr"]
        asf += liabilities.get("other_liabilities_lt6m", 0.0) * asf_factors["other_liabilities_lt6m"]
        asf += liabilities.get("other_liabilities_6m_1yr", 0.0) * asf_factors["other_liabilities_6m_1yr"]

        # Required Stable Funding
        rsf = 0.0
        rsf += assets.get("level1_hqla", 0.0) * rsf_factors.get("cash", 0.0)
        rsf += assets.get("sovereign_bonds_cqs2", 0.0) * rsf_factors.get("sovereign_bonds_cqs2", 0.15)
        rsf += assets.get("level2a_assets", 0.0) * rsf_factors.get("corporate_bonds_aa", 0.15)
        rsf += assets.get("level2b_assets", 0.0) * rsf_factors.get("corporate_bonds_bbb", 0.50)
        rsf += assets.get("residential_mortgages", 0.0) * rsf_factors.get("residential_mortgages_performing", 0.65)
        rsf += assets.get("retail_loans", 0.0) * rsf_factors.get("retail_loans_performing", 0.65)
        rsf += assets.get("sme_loans", 0.0) * rsf_factors.get("sme_loans_performing", 0.85)
        rsf += assets.get("corporate_loans_lt1yr", 0.0) * rsf_factors.get("corporate_loans_lt1yr", 0.50)
        rsf += assets.get("corporate_loans_gt1yr", 0.0) * rsf_factors.get("corporate_loans_gt1yr", 0.85)
        rsf += assets.get("fixed_assets", 0.0) * rsf_factors.get("fixed_assets", 1.00)
        rsf += assets.get("other_assets", 0.0) * rsf_factors.get("other_assets", 1.00)

        nsfr_ratio = asf / rsf if rsf > 0 else 999.0
        nsfr_compliant = nsfr_ratio >= 1.0

        # HQLA composition
        hqla_composition = {
            "level_1_eur": round(level1, 2),
            "level_2a_eur": round(level2a, 2),
            "level_2b_eur": round(level2b, 2),
            "level_1_pct": round(level1 / total_hqla * 100, 2) if total_hqla > 0 else 0.0,
            "level_2a_pct": round(level2a / total_hqla * 100, 2) if total_hqla > 0 else 0.0,
            "level_2b_pct": round(level2b / total_hqla * 100, 2) if total_hqla > 0 else 0.0,
        }

        # Stress scenario: 25% additional outflow shock
        stress_outflows = outflows * 1.25
        stress_net = max(stress_outflows - inflows, stress_outflows * 0.25)
        stress_lcr = total_hqla / stress_net if stress_net > 0 else 999.0

        lcr_stress_scenarios = [
            {
                "scenario": "baseline",
                "outflows_eur": round(net_outflows, 2),
                "lcr_ratio": round(lcr_ratio, 4),
                "compliant": lcr_compliant,
            },
            {
                "scenario": "stress_25pct_shock",
                "outflows_eur": round(stress_net, 2),
                "lcr_ratio": round(stress_lcr, 4),
                "compliant": stress_lcr >= 1.0,
            },
        ]

        return LiquidityResult(
            entity_name=entity_name,
            reporting_date=reporting_date,
            hqla_total=round(total_hqla, 2),
            total_net_cash_outflows=round(net_outflows, 2),
            lcr_ratio=round(lcr_ratio, 4),
            lcr_compliant=lcr_compliant,
            available_stable_funding=round(asf, 2),
            required_stable_funding=round(rsf, 2),
            nsfr_ratio=round(nsfr_ratio, 4),
            nsfr_compliant=nsfr_compliant,
            hqla_composition=hqla_composition,
            lcr_stress_scenarios=lcr_stress_scenarios,
        )

    # -----------------------------------------------------------------------
    # 14.6  Capital Adequacy Dashboard (Orchestrator)
    # -----------------------------------------------------------------------

    def run_capital_adequacy(
        self,
        entity_name: str,
        reporting_date: str,
        exposures: list,
        capital: dict,
        assets: dict,
        liabilities: dict,
        approach: str = "standardised",
        climate_scenarios: Optional[dict] = None,
        buffers: Optional[dict] = None,
        market_risk_rwa: float = 0.0,
        operational_risk_rwa: float = 0.0,
    ) -> CapitalAdequacyDashboard:
        """
        Run full capital adequacy assessment: credit + liquidity + climate stress.

        Parameters
        ----------
        entity_name : str
            Legal entity name.
        reporting_date : str
            Reporting date (YYYY-MM-DD).
        exposures : list[dict]
            Credit exposures (see calculate_capital_requirement).
        capital : dict
            Capital components (see calculate_capital_requirement).
        assets : dict
            HQLA / asset composition (see calculate_liquidity).
        liabilities : dict
            Funding composition (see calculate_liquidity).
        approach : str
            "standardised" or "irb".
        climate_scenarios : dict or None
            If provided, run climate stress: keys "adverse", "severe" with
            cet1_haircut_pct and rwa_uplift_pct.
        buffers : dict or None
            Buffer overrides (see calculate_capital_requirement).
        market_risk_rwa : float
            Pre-calculated market risk RWA.
        operational_risk_rwa : float
            Pre-calculated operational risk RWA.

        Returns
        -------
        CapitalAdequacyDashboard
        """
        # 1. Capital requirement
        cap_result = self.calculate_capital_requirement(
            entity_name=entity_name,
            reporting_date=reporting_date,
            exposures=exposures,
            capital=capital,
            approach=approach,
            climate_adjusted=True,
            buffers=buffers,
            market_risk_rwa=market_risk_rwa,
            operational_risk_rwa=operational_risk_rwa,
        )

        # 2. Liquidity
        liq_result = self.calculate_liquidity(
            entity_name=entity_name,
            reporting_date=reporting_date,
            assets=assets,
            liabilities=liabilities,
        )

        # 3. Climate stress scenarios
        climate_impact = {}
        if climate_scenarios:
            for scenario_name, params in climate_scenarios.items():
                cet1_haircut = params.get("cet1_haircut_pct", 0.0) / 100.0
                rwa_uplift = params.get("rwa_uplift_pct", 0.0) / 100.0

                stressed_cet1 = cap_result.cet1_capital * (1.0 - cet1_haircut)
                stressed_rwa = cap_result.total_rwa * (1.0 + rwa_uplift)
                stressed_ratio = stressed_cet1 / stressed_rwa if stressed_rwa > 0 else 0.0

                climate_impact[scenario_name] = {
                    "cet1_haircut_pct": params.get("cet1_haircut_pct", 0.0),
                    "rwa_uplift_pct": params.get("rwa_uplift_pct", 0.0),
                    "stressed_cet1_eur": round(stressed_cet1, 2),
                    "stressed_rwa_eur": round(stressed_rwa, 2),
                    "stressed_cet1_ratio": round(stressed_ratio, 6),
                    "below_minimum": stressed_ratio < 0.045,
                    "below_buffer": stressed_ratio < 0.07,
                }
        else:
            # Default scenarios: adverse and severe
            for scenario_name, haircut, uplift in [("adverse", 0.15, 0.10), ("severe", 0.25, 0.20)]:
                stressed_cet1 = cap_result.cet1_capital * (1.0 - haircut)
                stressed_rwa = cap_result.total_rwa * (1.0 + uplift)
                stressed_ratio = stressed_cet1 / stressed_rwa if stressed_rwa > 0 else 0.0

                climate_impact[scenario_name] = {
                    "cet1_haircut_pct": haircut * 100,
                    "rwa_uplift_pct": uplift * 100,
                    "stressed_cet1_eur": round(stressed_cet1, 2),
                    "stressed_rwa_eur": round(stressed_rwa, 2),
                    "stressed_cet1_ratio": round(stressed_ratio, 6),
                    "below_minimum": stressed_ratio < 0.045,
                    "below_buffer": stressed_ratio < 0.07,
                }

        # 4. BCBS 239 compliance scoring
        bcbs239_score = self._score_bcbs239(exposures, capital, assets, liabilities)

        # 5. Pillar 2 recommendations
        p2_recs = self._generate_pillar2_recommendations(cap_result, liq_result, climate_impact)

        # 6. RAG status
        rag = self._determine_rag_status(cap_result, liq_result)

        # 7. Cross-framework mapping
        cross_map = {
            "CSRD_ESRS_E1": {
                "disclosure": "E1-6 Anticipated financial effects from material physical and transition risks",
                "data_from": "climate_rwa_addon, exposure_class_breakdown",
            },
            "ISSB_S2": {
                "disclosure": "S2 Climate-related Financial Disclosures",
                "data_from": "climate_stress_impact, capital ratios under stress",
            },
            "EBA_PILLAR3_ESG": {
                "disclosure": "EBA ITS on Pillar 3 ESG risk disclosures (Template 1-3)",
                "data_from": "exposure_class_breakdown with NACE sector, climate_adjustment",
            },
            "TCFD": {
                "disclosure": "Risk Management / Metrics and Targets",
                "data_from": "total_rwa, cet1_ratio, leverage_ratio, climate_rwa_addon",
            },
        }

        return CapitalAdequacyDashboard(
            entity_name=entity_name,
            reporting_date=reporting_date,
            capital_requirement=cap_result,
            liquidity=liq_result,
            climate_stress_impact=climate_impact,
            bcbs239_compliance_score=round(bcbs239_score, 1),
            pillar2_recommendations=p2_recs,
            overall_rag_status=rag,
            cross_framework_mapping=cross_map,
        )

    # -----------------------------------------------------------------------
    # 14.7  Internal helpers
    # -----------------------------------------------------------------------

    def _score_bcbs239(
        self,
        exposures: list,
        capital: dict,
        assets: dict,
        liabilities: dict,
    ) -> float:
        """
        Score BCBS 239 compliance (0-100) based on data completeness.

        Principles assessed:
          1. Governance (10 pts) — capital dict completeness
          2. Data architecture (15 pts) — exposure field coverage
          3. Accuracy (20 pts) — PD/LGD/CQS populated
          4. Completeness (20 pts) — sector / maturity / physical risk coverage
          5. Timeliness (10 pts) — assumed OK (static assessment)
          6. Adaptability (10 pts) — climate fields populated
          7. Reporting (15 pts) — assets / liabilities field coverage
        """
        score = 0.0

        # 1. Governance — capital dict
        cap_fields = {"cet1", "at1", "tier2", "total_exposure_measure"}
        cap_present = sum(1 for f in cap_fields if f in capital and capital[f] > 0)
        score += (cap_present / len(cap_fields)) * 10.0

        # 2. Data architecture — exposure field coverage
        required_exp_fields = {"exposure_class", "ead_eur", "pd", "lgd", "maturity_years", "sector"}
        if exposures:
            field_coverage = []
            for exp in exposures[:50]:  # sample first 50
                present = sum(1 for f in required_exp_fields if f in exp)
                field_coverage.append(present / len(required_exp_fields))
            score += (sum(field_coverage) / len(field_coverage)) * 15.0

        # 3. Accuracy — PD/LGD/CQS populated and within bounds
        if exposures:
            valid = 0
            for exp in exposures[:50]:
                pd_val = exp.get("pd", -1)
                lgd_val = exp.get("lgd", -1)
                if 0 <= pd_val <= 1 and 0 <= lgd_val <= 1:
                    valid += 1
            score += (valid / min(len(exposures), 50)) * 20.0

        # 4. Completeness — sector + maturity + physical risk
        if exposures:
            complete = 0
            for exp in exposures[:50]:
                has_sector = bool(exp.get("sector"))
                has_mat = exp.get("maturity_years", 0) > 0
                has_phys = bool(exp.get("physical_risk_zone"))
                complete += (int(has_sector) + int(has_mat) + int(has_phys)) / 3
            score += (complete / min(len(exposures), 50)) * 20.0

        # 5. Timeliness — static assessment assumes OK
        score += 8.0  # assume 80% timeliness

        # 6. Adaptability — climate fields
        if exposures:
            climate_fields = 0
            for exp in exposures[:50]:
                if exp.get("physical_risk_zone") or exp.get("is_green") is not None:
                    climate_fields += 1
            score += (climate_fields / min(len(exposures), 50)) * 10.0

        # 7. Reporting — assets / liabilities coverage
        asset_fields = {"level1_hqla", "level2a_assets", "level2b_assets",
                        "residential_mortgages", "retail_loans", "wholesale_loans"}
        liability_fields = {"retail_deposits_stable", "retail_deposits_less_stable",
                            "wholesale_unsecured_operational", "capital_instruments"}
        a_present = sum(1 for f in asset_fields if f in assets)
        l_present = sum(1 for f in liability_fields if f in liabilities)
        combined = (a_present + l_present) / (len(asset_fields) + len(liability_fields))
        score += combined * 15.0

        return min(score, 100.0)

    def _generate_pillar2_recommendations(
        self,
        cap: CapitalRequirementResult,
        liq: LiquidityResult,
        climate: dict,
    ) -> list:
        """Generate Pillar 2 supervisory recommendations."""
        recs = []

        # Concentration risk
        if cap.exposure_class_breakdown:
            max_class = max(cap.exposure_class_breakdown, key=lambda x: x["rwa_eur"])
            if cap.total_rwa > 0 and max_class["rwa_eur"] / cap.total_rwa > 0.40:
                recs.append(
                    f"Concentration risk: {max_class['exposure_class']} accounts for "
                    f"{max_class['rwa_eur']/cap.total_rwa*100:.1f}% of total RWA — "
                    "consider Pillar 2A add-on for single-name / sector concentration"
                )

        # Interest rate risk in banking book (IRRBB)
        if cap.leverage_ratio < 0.04:
            recs.append(
                "Low leverage ratio indicates high balance sheet leverage — "
                "supervisory review of IRRBB (Pillar 2A) recommended"
            )

        # Liquidity add-ons
        if not liq.lcr_compliant:
            recs.append(
                "LCR non-compliant — Pillar 2G specific liquidity requirement "
                "expected from supervisor"
            )
        if not liq.nsfr_compliant:
            recs.append(
                "NSFR non-compliant — structural funding mismatch must be addressed"
            )

        # Climate stress
        severe = climate.get("severe", {})
        if severe.get("below_minimum"):
            recs.append(
                "CET1 falls below minimum under severe climate stress — "
                "climate risk Pillar 2A add-on likely; green transition plan required"
            )
        elif severe.get("below_buffer"):
            recs.append(
                "CET1 falls below buffer under severe climate stress — "
                "supervisory dialogue on climate risk management expected"
            )

        if not recs:
            recs.append("No material Pillar 2 concerns identified")

        return recs

    def _determine_rag_status(
        self,
        cap: CapitalRequirementResult,
        liq: LiquidityResult,
    ) -> str:
        """
        Determine overall RAG status.

        GREEN: All ratios above minimum + combined buffer
        AMBER: All ratios above minimum but at least one below combined buffer
        RED:   At least one ratio below regulatory minimum
        """
        min_cet1 = 0.045
        min_tier1 = 0.06
        min_total = 0.08
        min_leverage = 0.03
        cbr = cap.combined_buffer_requirement

        # RED: below minimum
        if (cap.cet1_ratio < min_cet1 or
                cap.tier1_ratio < min_tier1 or
                cap.total_capital_ratio < min_total or
                cap.leverage_ratio < min_leverage or
                not liq.lcr_compliant or
                not liq.nsfr_compliant):
            return "RED"

        # AMBER: above minimum but below combined buffer
        if (cap.cet1_ratio < min_cet1 + cbr or
                cap.tier1_ratio < min_tier1 + cbr or
                cap.total_capital_ratio < min_total + cbr):
            return "AMBER"

        return "GREEN"

    # -----------------------------------------------------------------------
    # 14.8  Static Reference Getters
    # -----------------------------------------------------------------------

    @staticmethod
    def get_exposure_classes() -> list:
        """Return CRR Article 112 exposure class definitions."""
        return BASEL_EXPOSURE_CLASSES

    @staticmethod
    def get_sa_risk_weights() -> dict:
        """Return Standardised Approach CQS-to-risk-weight mapping tables."""
        return BASEL_SA_RISK_WEIGHTS

    @staticmethod
    def get_irb_parameters() -> dict:
        """Return IRB formula parameters per CRR Article 153."""
        return BASEL_IRB_PARAMETERS

    @staticmethod
    def get_capital_requirements() -> dict:
        """Return minimum capital ratio requirements per CRR Article 92."""
        return BASEL_CAPITAL_REQUIREMENTS

    @staticmethod
    def get_capital_buffers() -> dict:
        """Return capital buffer requirements per CRD V."""
        return BASEL_CAPITAL_BUFFERS

    @staticmethod
    def get_lcr_parameters() -> dict:
        """Return LCR parameters per BCBS d295 / CRR Art. 412."""
        return BASEL_LCR_PARAMETERS

    @staticmethod
    def get_nsfr_parameters() -> dict:
        """Return NSFR parameters per BCBS d396 / CRR II Art. 428a."""
        return BASEL_NSFR_PARAMETERS

    @staticmethod
    def get_climate_adjustments() -> dict:
        """Return climate risk capital adjustment parameters per EBA GL/2022/02."""
        return BASEL_CLIMATE_ADJUSTMENTS

    @staticmethod
    def get_regulatory_frameworks() -> list:
        """Return regulatory framework references."""
        return BASEL_REGULATORY_FRAMEWORKS

    @staticmethod
    def get_operational_risk_parameters() -> dict:
        """Return SMA operational risk parameters per BCBS d563."""
        return BASEL_OPERATIONAL_RISK
