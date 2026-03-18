"""
Banking Risk Engine
====================
Comprehensive banking risk analytics covering all Basel III/IV pillars:
  - Credit Risk: PD term structure, LGD, EAD/CCF, IFRS 9 ECL (3-stage), climate overlay
  - Liquidity Risk: LCR, NSFR using embedded Basel III factors (CRR2)
  - Market Risk: Parametric VaR, Stressed VaR, Interest Rate Risk (EVE/NII)
  - Operational Risk: Basic Indicator Approach (BIA), Standardised Approach (TSA)
  - AML/CFT Risk: FATF-based country risk, counterparty screening
  - Capital Adequacy: Pillar 1 + Pillar 2 aggregation, leverage ratio

Inputs:
  - Loan book / exposure data (notional, maturity, collateral)
  - HQLA / funding composition for liquidity ratios
  - P&L / gross income for operational risk
  - FATF country risk ratings for AML screening
  - Climate warming scenario for stress overlays

Outputs:
  - Per-module risk metrics (ECL, LCR, NSFR, VaR, OpRisk charge)
  - Capital adequacy ratios (CET1, Tier 1, Total Capital, Leverage)
  - Comprehensive bank risk profile with recommendations

References:
  - Basel III: BIS d424 (credit), d295 (LCR), d396 (NSFR), d457 (market risk FRTB)
  - IFRS 9 Financial Instruments (ECL impairment)
  - CRR2/CRD V (EU implementation)
  - EBA GL/2020/06, GL/2017/16 (stress testing)
  - FATF 40 Recommendations (AML/CFT)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field as dc_field
from typing import Optional

from services.reference_data_tables import (
    BASEL3_HQLA_CLASSIFICATION,
    BASEL3_LCR_OUTFLOW_RATES,
    BASEL3_NSFR_ASF_FACTORS,
    BASEL3_NSFR_RSF_FACTORS,
    FATF_COUNTRY_RISK_RATINGS,
    get_fatf_rating,
)


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CreditRiskResult:
    """IFRS 9 ECL calculation result."""
    portfolio_size: int
    total_exposure_eur: float
    weighted_avg_pd_pct: float
    weighted_avg_lgd_pct: float
    avg_ead_eur: float
    ecl_stage1_eur: float
    ecl_stage2_eur: float
    ecl_stage3_eur: float
    total_ecl_eur: float
    ecl_coverage_ratio_pct: float
    climate_overlay_eur: float
    risk_weighted_assets_eur: float
    credit_risk_capital_eur: float
    stage_distribution: dict  # {stage: count}


@dataclass
class LiquidityRiskResult:
    """LCR + NSFR calculation result."""
    total_hqla_eur: float
    hqla_composition: dict  # {level: amount}
    total_net_outflows_eur: float
    lcr_pct: float
    lcr_compliant: bool
    total_asf_eur: float
    total_rsf_eur: float
    nsfr_pct: float
    nsfr_compliant: bool
    liquidity_buffer_days: float
    concentration_risk_pct: float


@dataclass
class MarketRiskResult:
    """VaR / FRTB market risk result."""
    trading_book_eur: float
    var_99_1d_eur: float
    var_99_10d_eur: float
    stressed_var_99_10d_eur: float
    expected_shortfall_97_5_eur: float
    interest_rate_risk_eve_eur: float
    interest_rate_risk_nii_eur: float
    fx_risk_eur: float
    equity_risk_eur: float
    market_risk_rwa_eur: float
    market_risk_capital_eur: float


@dataclass
class OperationalRiskResult:
    """Operational risk charge (BIA/TSA)."""
    approach: str  # "BIA" or "TSA"
    gross_income_avg_3yr_eur: float
    alpha_factor_pct: float
    bia_charge_eur: float
    business_line_charges: dict  # {line: charge}
    tsa_charge_eur: float
    operational_risk_capital_eur: float
    loss_event_buffer_pct: float


@dataclass
class AMLRiskResult:
    """AML/CFT risk screening result."""
    total_counterparties: int
    countries_screened: int
    high_risk_count: int
    very_high_risk_count: int
    grey_list_exposures: list
    black_list_exposures: list
    overall_aml_risk_score: float  # 0-100
    risk_tier_distribution: dict  # {tier: count}
    recommended_actions: list


@dataclass
class CapitalAdequacyResult:
    """Pillar 1 + Pillar 2 capital adequacy."""
    cet1_capital_eur: float
    at1_capital_eur: float
    tier2_capital_eur: float
    total_capital_eur: float
    credit_rwa_eur: float
    market_rwa_eur: float
    operational_rwa_eur: float
    total_rwa_eur: float
    cet1_ratio_pct: float
    tier1_ratio_pct: float
    total_capital_ratio_pct: float
    leverage_ratio_pct: float
    leverage_exposure_eur: float
    countercyclical_buffer_pct: float
    combined_buffer_requirement_pct: float
    surplus_to_mda_eur: float
    compliant: bool


@dataclass
class BankRiskSummary:
    """Full bank risk assessment across all sub-modules."""
    entity_name: str
    credit_risk: Optional[CreditRiskResult]
    liquidity_risk: Optional[LiquidityRiskResult]
    market_risk: Optional[MarketRiskResult]
    operational_risk: Optional[OperationalRiskResult]
    aml_risk: Optional[AMLRiskResult]
    capital_adequacy: Optional[CapitalAdequacyResult]
    overall_risk_rating: str  # "low", "moderate", "elevated", "high", "critical"
    total_capital_requirement_eur: float
    recommendations: list


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class BankingRiskEngine:
    """
    Comprehensive banking risk analytics engine.

    Uses embedded Basel III reference data from reference_data_tables.py
    for liquidity (LCR/NSFR) and AML/CFT (FATF) calculations.
    """

    # Basel III minimum capital ratios
    MIN_CET1_PCT = 4.5
    MIN_TIER1_PCT = 6.0
    MIN_TOTAL_CAPITAL_PCT = 8.0
    MIN_LEVERAGE_PCT = 3.0
    CAPITAL_CONSERVATION_BUFFER_PCT = 2.5
    GSIB_BUFFER_PCT = 1.0  # default G-SIB surcharge

    # BIA alpha factor
    BIA_ALPHA_PCT = 15.0

    # TSA beta factors by business line (Basel II/III Art 316)
    TSA_BETA_FACTORS: dict[str, float] = {
        "corporate_finance": 18.0,
        "trading_and_sales": 18.0,
        "retail_banking": 12.0,
        "commercial_banking": 15.0,
        "payment_and_settlement": 18.0,
        "agency_services": 15.0,
        "asset_management": 12.0,
        "retail_brokerage": 12.0,
    }

    # IFRS 9 PD term structure: annual PD for investment-grade and sub-investment
    PD_TERM_STRUCTURES: dict[str, list[float]] = {
        "AAA": [0.01, 0.03, 0.06, 0.10, 0.15],
        "AA":  [0.02, 0.05, 0.10, 0.18, 0.28],
        "A":   [0.05, 0.12, 0.22, 0.35, 0.50],
        "BBB": [0.15, 0.40, 0.72, 1.10, 1.55],
        "BB":  [0.60, 1.50, 2.70, 4.00, 5.40],
        "B":   [2.00, 5.00, 8.50, 12.00, 15.50],
        "CCC": [8.00, 16.00, 23.00, 28.00, 32.00],
    }

    # Standard LGD by collateral type
    LGD_BY_COLLATERAL: dict[str, float] = {
        "sovereign_guarantee": 5.0,
        "cash_collateral": 10.0,
        "residential_mortgage": 20.0,
        "commercial_mortgage": 30.0,
        "receivables": 35.0,
        "other_physical": 40.0,
        "unsecured_senior": 45.0,
        "unsecured_subordinated": 75.0,
    }

    # Basel III/IV risk weight by exposure class
    RISK_WEIGHTS: dict[str, float] = {
        "sovereign_0": 0.0,
        "sovereign_20": 20.0,
        "bank_20": 20.0,
        "bank_50": 50.0,
        "corporate_ig": 65.0,
        "corporate_standard": 100.0,
        "corporate_high_risk": 150.0,
        "retail": 75.0,
        "residential_mortgage": 35.0,
        "commercial_re": 100.0,
        "equity": 250.0,
        "defaulted": 150.0,
    }

    # Climate stress PD multipliers by warming scenario
    CLIMATE_PD_MULTIPLIERS: dict[str, float] = {
        "1.5": 1.05,
        "2.0": 1.12,
        "2.5": 1.22,
        "3.0": 1.35,
        "4.0": 1.55,
    }

    def assess_credit_risk(
        self,
        total_exposure_eur: float = 10_000_000_000,
        portfolio_size: int = 5000,
        avg_rating: str = "BBB",
        collateral_type: str = "unsecured_senior",
        avg_maturity_years: int = 3,
        stage2_pct: float = 8.0,
        stage3_pct: float = 2.0,
        warming_c: float = 1.5,
    ) -> CreditRiskResult:
        """
        Calculate IFRS 9 ECL across 3 stages with climate overlay.

        Stage 1: 12-month ECL (performing, no SICR)
        Stage 2: Lifetime ECL (performing, SICR triggered)
        Stage 3: Lifetime ECL (credit-impaired / defaulted)
        """
        # PD term structure lookup
        pd_curve = self.PD_TERM_STRUCTURES.get(avg_rating, self.PD_TERM_STRUCTURES["BBB"])
        year_idx = min(avg_maturity_years - 1, len(pd_curve) - 1)
        annual_pd_pct = pd_curve[0]  # 1-year PD for Stage 1
        lifetime_pd_pct = pd_curve[year_idx]  # maturity-matched PD for Stage 2

        # LGD
        lgd_pct = self.LGD_BY_COLLATERAL.get(collateral_type, 45.0)

        # Stage distribution
        stage1_pct = 100.0 - stage2_pct - stage3_pct
        stage1_exposure = total_exposure_eur * stage1_pct / 100.0
        stage2_exposure = total_exposure_eur * stage2_pct / 100.0
        stage3_exposure = total_exposure_eur * stage3_pct / 100.0

        # ECL = EAD x PD x LGD
        ecl_stage1 = stage1_exposure * (annual_pd_pct / 100.0) * (lgd_pct / 100.0)
        ecl_stage2 = stage2_exposure * (lifetime_pd_pct / 100.0) * (lgd_pct / 100.0)
        ecl_stage3 = stage3_exposure * 1.0 * (lgd_pct / 100.0)  # PD=100% for Stage 3

        total_ecl = ecl_stage1 + ecl_stage2 + ecl_stage3

        # Climate overlay
        warming_key = str(warming_c)
        climate_mult = self.CLIMATE_PD_MULTIPLIERS.get(warming_key, 1.0 + (warming_c - 1.0) * 0.10)
        climate_overlay = total_ecl * (climate_mult - 1.0)

        # Risk-weighted assets (standardised approach)
        avg_ead = total_exposure_eur / portfolio_size if portfolio_size > 0 else 0
        rw = self.RISK_WEIGHTS.get("corporate_standard", 100.0)
        rwa = total_exposure_eur * rw / 100.0

        # Credit risk capital (8% of RWA)
        credit_capital = rwa * 0.08

        stage_distribution = {
            "stage1": int(portfolio_size * stage1_pct / 100),
            "stage2": int(portfolio_size * stage2_pct / 100),
            "stage3": int(portfolio_size * stage3_pct / 100),
        }

        ecl_coverage = (total_ecl + climate_overlay) / total_exposure_eur * 100 if total_exposure_eur > 0 else 0

        return CreditRiskResult(
            portfolio_size=portfolio_size,
            total_exposure_eur=total_exposure_eur,
            weighted_avg_pd_pct=annual_pd_pct,
            weighted_avg_lgd_pct=lgd_pct,
            avg_ead_eur=avg_ead,
            ecl_stage1_eur=round(ecl_stage1, 2),
            ecl_stage2_eur=round(ecl_stage2, 2),
            ecl_stage3_eur=round(ecl_stage3, 2),
            total_ecl_eur=round(total_ecl, 2),
            ecl_coverage_ratio_pct=round(ecl_coverage, 4),
            climate_overlay_eur=round(climate_overlay, 2),
            risk_weighted_assets_eur=round(rwa, 2),
            credit_risk_capital_eur=round(credit_capital, 2),
            stage_distribution=stage_distribution,
        )

    def assess_liquidity_risk(
        self,
        hqla_holdings: Optional[dict[str, float]] = None,
        funding_sources: Optional[dict[str, float]] = None,
        asset_book: Optional[dict[str, float]] = None,
    ) -> LiquidityRiskResult:
        """
        Calculate LCR and NSFR using embedded Basel III factors.

        LCR = Stock of HQLA / Total net cash outflows over 30 days >= 100%
        NSFR = Available stable funding / Required stable funding >= 100%
        """
        # Default HQLA portfolio if none provided
        if hqla_holdings is None:
            hqla_holdings = {
                "central_bank_reserves": 50_000_000_000,
                "sovereign_0pct_rw": 30_000_000_000,
                "sovereign_20pct_rw": 10_000_000_000,
                "covered_bonds_aa_minus": 8_000_000_000,
                "corporate_bonds_aa_minus": 5_000_000_000,
                "rmbs_aa": 3_000_000_000,
                "corporate_bonds_a_bbb": 2_000_000_000,
            }

        # Calculate HQLA after haircuts and caps
        total_hqla = 0.0
        hqla_by_level = {"1": 0.0, "2A": 0.0, "2B": 0.0}
        for asset_type, amount in hqla_holdings.items():
            classification = BASEL3_HQLA_CLASSIFICATION.get(asset_type)
            if classification:
                haircut = classification["haircut_pct"] / 100.0
                adj_amount = amount * (1.0 - haircut)
                level = classification["level"]
                hqla_by_level[level] = hqla_by_level.get(level, 0.0) + adj_amount
                total_hqla += adj_amount

        # Apply 2A cap (40%) and 2B cap (15%)
        level1 = hqla_by_level.get("1", 0.0)
        level2a = min(hqla_by_level.get("2A", 0.0), total_hqla * 0.40)
        level2b = min(hqla_by_level.get("2B", 0.0), total_hqla * 0.15)
        total_hqla = level1 + level2a + level2b

        hqla_composition = {"level_1": round(level1, 2), "level_2a": round(level2a, 2), "level_2b": round(level2b, 2)}

        # Default funding sources for net outflows
        if funding_sources is None:
            funding_sources = {
                "retail_stable_deposits": 80_000_000_000,
                "retail_less_stable_deposits": 40_000_000_000,
                "operational_deposits_clearing": 20_000_000_000,
                "non_operational_unsecured_nfi": 15_000_000_000,
                "committed_credit_facilities_nfi": 10_000_000_000,
                "trade_finance_obligations": 5_000_000_000,
            }

        # Calculate net cash outflows (30-day stress)
        total_outflows = 0.0
        for source_type, amount in funding_sources.items():
            outflow_data = BASEL3_LCR_OUTFLOW_RATES.get(source_type)
            if outflow_data:
                outflow_rate = outflow_data["outflow_pct"] / 100.0
                total_outflows += amount * outflow_rate

        # LCR
        lcr_pct = (total_hqla / total_outflows * 100) if total_outflows > 0 else 999.0
        lcr_compliant = lcr_pct >= 100.0

        # NSFR — ASF calculation
        if asset_book is None:
            asset_book = {
                "tier1_capital": 25_000_000_000,
                "tier2_capital_over_1yr": 8_000_000_000,
                "other_funding_over_1yr": 30_000_000_000,
                "stable_retail_deposits": 80_000_000_000,
                "less_stable_retail_deposits": 40_000_000_000,
                "wholesale_operational_deposits": 20_000_000_000,
            }

        total_asf = 0.0
        for fund_type, amount in asset_book.items():
            asf_data = BASEL3_NSFR_ASF_FACTORS.get(fund_type)
            if asf_data:
                total_asf += amount * asf_data["asf_factor_pct"] / 100.0

        # RSF calculation (default asset composition)
        rsf_assets = {
            "coins_banknotes": 2_000_000_000,
            "central_bank_reserves": 50_000_000_000,
            "unencumbered_level1_hqla": 30_000_000_000,
            "unencumbered_level2a_hqla": 15_000_000_000,
            "performing_loans_retail_lt_1yr": 60_000_000_000,
            "performing_mortgages_over_1yr_rw_lt35": 80_000_000_000,
            "performing_loans_over_1yr_rw_gt35": 40_000_000_000,
        }

        total_rsf = 0.0
        for asset_type, amount in rsf_assets.items():
            rsf_data = BASEL3_NSFR_RSF_FACTORS.get(asset_type)
            if rsf_data:
                total_rsf += amount * rsf_data["rsf_factor_pct"] / 100.0

        nsfr_pct = (total_asf / total_rsf * 100) if total_rsf > 0 else 999.0
        nsfr_compliant = nsfr_pct >= 100.0

        # Liquidity buffer in days
        daily_outflow = total_outflows / 30.0 if total_outflows > 0 else 1.0
        buffer_days = total_hqla / daily_outflow if daily_outflow > 0 else 999.0

        # Concentration: largest single source as % of total funding
        largest_source = max(funding_sources.values()) if funding_sources else 0
        total_funding = sum(funding_sources.values()) if funding_sources else 1
        concentration = largest_source / total_funding * 100 if total_funding > 0 else 0

        return LiquidityRiskResult(
            total_hqla_eur=round(total_hqla, 2),
            hqla_composition=hqla_composition,
            total_net_outflows_eur=round(total_outflows, 2),
            lcr_pct=round(lcr_pct, 2),
            lcr_compliant=lcr_compliant,
            total_asf_eur=round(total_asf, 2),
            total_rsf_eur=round(total_rsf, 2),
            nsfr_pct=round(nsfr_pct, 2),
            nsfr_compliant=nsfr_compliant,
            liquidity_buffer_days=round(buffer_days, 1),
            concentration_risk_pct=round(concentration, 2),
        )

    def assess_market_risk(
        self,
        trading_book_eur: float = 5_000_000_000,
        equity_exposure_eur: float = 1_000_000_000,
        fx_exposure_eur: float = 2_000_000_000,
        interest_rate_dv01_eur: float = 5_000_000,
        portfolio_volatility_pct: float = 12.0,
        stressed_volatility_pct: float = 25.0,
        rate_shock_bps: int = 200,
    ) -> MarketRiskResult:
        """
        Calculate VaR, Stressed VaR, and IRRBB (EVE/NII).

        VaR (parametric) = Position x Volatility x Z-score x sqrt(holding period)
        Z(99%) = 2.326
        """
        z_99 = 2.326
        z_97_5 = 1.960

        vol_daily = portfolio_volatility_pct / 100.0 / math.sqrt(252)
        stressed_vol_daily = stressed_volatility_pct / 100.0 / math.sqrt(252)

        # 1-day VaR at 99%
        var_1d = trading_book_eur * vol_daily * z_99

        # 10-day VaR (square-root-of-time scaling)
        var_10d = var_1d * math.sqrt(10)

        # Stressed VaR
        stressed_var_10d = trading_book_eur * stressed_vol_daily * z_99 * math.sqrt(10)

        # Expected Shortfall at 97.5% (approximation: ES ~= VaR x 1.4 for normal dist)
        es_97_5 = var_10d * 1.4

        # Interest rate risk in banking book (IRRBB)
        # EVE: change in economic value of equity under rate shock
        eve_impact = interest_rate_dv01_eur * rate_shock_bps
        # NII: impact on net interest income (simplified)
        nii_impact = eve_impact * 0.3  # ~30% flows through P&L in year 1

        # FX risk (simplified: 8% of net open position)
        fx_risk = fx_exposure_eur * 0.08

        # Equity risk (simplified: VaR-based)
        equity_risk = equity_exposure_eur * (portfolio_volatility_pct / 100.0) * z_99 * math.sqrt(10)

        # Market risk RWA = (VaR + SVaR) x multiplier (3.0 minimum)
        market_rwa = (var_10d + stressed_var_10d) * 3.0 * 12.5

        market_capital = market_rwa * 0.08

        return MarketRiskResult(
            trading_book_eur=trading_book_eur,
            var_99_1d_eur=round(var_1d, 2),
            var_99_10d_eur=round(var_10d, 2),
            stressed_var_99_10d_eur=round(stressed_var_10d, 2),
            expected_shortfall_97_5_eur=round(es_97_5, 2),
            interest_rate_risk_eve_eur=round(eve_impact, 2),
            interest_rate_risk_nii_eur=round(nii_impact, 2),
            fx_risk_eur=round(fx_risk, 2),
            equity_risk_eur=round(equity_risk, 2),
            market_risk_rwa_eur=round(market_rwa, 2),
            market_risk_capital_eur=round(market_capital, 2),
        )

    def assess_operational_risk(
        self,
        gross_income_year1_eur: float = 8_000_000_000,
        gross_income_year2_eur: float = 7_500_000_000,
        gross_income_year3_eur: float = 8_200_000_000,
        business_line_income: Optional[dict[str, float]] = None,
    ) -> OperationalRiskResult:
        """
        Calculate operational risk capital under BIA and TSA.

        BIA: K = alpha x GI_avg (alpha = 15%)
        TSA: K = sum(beta_i x GI_i) for each business line
        """
        incomes = [gross_income_year1_eur, gross_income_year2_eur, gross_income_year3_eur]
        positive_incomes = [i for i in incomes if i > 0]
        avg_gi = sum(positive_incomes) / len(positive_incomes) if positive_incomes else 0

        # BIA
        bia_charge = avg_gi * self.BIA_ALPHA_PCT / 100.0

        # TSA
        if business_line_income is None:
            business_line_income = {
                "corporate_finance": avg_gi * 0.10,
                "trading_and_sales": avg_gi * 0.20,
                "retail_banking": avg_gi * 0.30,
                "commercial_banking": avg_gi * 0.25,
                "payment_and_settlement": avg_gi * 0.08,
                "agency_services": avg_gi * 0.03,
                "asset_management": avg_gi * 0.03,
                "retail_brokerage": avg_gi * 0.01,
            }

        bl_charges = {}
        tsa_total = 0.0
        for line, income in business_line_income.items():
            beta = self.TSA_BETA_FACTORS.get(line, 15.0)
            charge = max(income * beta / 100.0, 0)
            bl_charges[line] = round(charge, 2)
            tsa_total += charge

        # Use the higher of BIA and TSA as the final charge
        op_capital = max(bia_charge, tsa_total)
        approach = "TSA" if tsa_total >= bia_charge else "BIA"

        # Loss event buffer (10% above the calculated charge)
        loss_buffer_pct = 10.0

        return OperationalRiskResult(
            approach=approach,
            gross_income_avg_3yr_eur=round(avg_gi, 2),
            alpha_factor_pct=self.BIA_ALPHA_PCT,
            bia_charge_eur=round(bia_charge, 2),
            business_line_charges=bl_charges,
            tsa_charge_eur=round(tsa_total, 2),
            operational_risk_capital_eur=round(op_capital, 2),
            loss_event_buffer_pct=loss_buffer_pct,
        )

    def assess_aml_risk(
        self,
        counterparty_countries: Optional[list[str]] = None,
        exposure_by_country: Optional[dict[str, float]] = None,
    ) -> AMLRiskResult:
        """
        Screen counterparties against FATF country risk ratings.

        Uses ISO2 country codes. Returns risk distribution and flagged exposures.
        """
        if counterparty_countries is None:
            counterparty_countries = ["US", "GB", "DE", "FR", "JP", "BR", "CN", "IN", "ZA", "NG", "TR", "AE"]

        if exposure_by_country is None:
            exposure_by_country = {c: 1_000_000_000 for c in counterparty_countries}

        tier_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        grey_list = []
        black_list = []
        total_risk_score = 0.0
        countries_screened = 0

        for country in counterparty_countries:
            rating = get_fatf_rating(country)
            if rating:
                countries_screened += 1
                tier = rating["risk_tier"]
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

                exposure = exposure_by_country.get(country, 0)
                total_risk_score += tier * (exposure / 1_000_000_000)

                if rating.get("grey_list"):
                    grey_list.append({"country": country, "exposure_eur": exposure, "risk_tier": tier})
                if rating.get("black_list"):
                    black_list.append({"country": country, "exposure_eur": exposure, "risk_tier": tier})
            else:
                countries_screened += 1
                tier_distribution[2] = tier_distribution.get(2, 0) + 1  # unknown = standard

        # Normalize risk score to 0-100
        max_possible = 4 * len(counterparty_countries)
        overall_score = min((total_risk_score / max_possible * 100) if max_possible > 0 else 0, 100)

        # Recommended actions
        actions = []
        if black_list:
            actions.append("CRITICAL: Terminate relationships with black-listed country exposures")
        if grey_list:
            actions.append("Enhanced Due Diligence required for grey-listed country exposures")
        if tier_distribution.get(3, 0) > 0:
            actions.append("Increase monitoring frequency for high-risk tier (tier 3) counterparties")
        if overall_score > 50:
            actions.append("Consider portfolio rebalancing to reduce AML concentration risk")
        if not actions:
            actions.append("AML risk profile within acceptable parameters")

        return AMLRiskResult(
            total_counterparties=len(counterparty_countries),
            countries_screened=countries_screened,
            high_risk_count=tier_distribution.get(3, 0),
            very_high_risk_count=tier_distribution.get(4, 0),
            grey_list_exposures=grey_list,
            black_list_exposures=black_list,
            overall_aml_risk_score=round(overall_score, 2),
            risk_tier_distribution=tier_distribution,
            recommended_actions=actions,
        )

    def assess_capital_adequacy(
        self,
        cet1_capital_eur: float = 25_000_000_000,
        at1_capital_eur: float = 5_000_000_000,
        tier2_capital_eur: float = 8_000_000_000,
        credit_rwa_eur: float = 150_000_000_000,
        market_rwa_eur: float = 20_000_000_000,
        operational_rwa_eur: float = 15_000_000_000,
        leverage_exposure_eur: float = 500_000_000_000,
        countercyclical_buffer_pct: float = 0.5,
    ) -> CapitalAdequacyResult:
        """
        Assess bank capital adequacy under Basel III/IV framework.

        Checks CET1, Tier 1, Total Capital, and Leverage ratios against
        minimum requirements plus buffers.
        """
        total_capital = cet1_capital_eur + at1_capital_eur + tier2_capital_eur
        tier1_capital = cet1_capital_eur + at1_capital_eur
        total_rwa = credit_rwa_eur + market_rwa_eur + operational_rwa_eur

        # Ratios
        cet1_ratio = (cet1_capital_eur / total_rwa * 100) if total_rwa > 0 else 0
        tier1_ratio = (tier1_capital / total_rwa * 100) if total_rwa > 0 else 0
        total_ratio = (total_capital / total_rwa * 100) if total_rwa > 0 else 0
        leverage_ratio = (tier1_capital / leverage_exposure_eur * 100) if leverage_exposure_eur > 0 else 0

        # Combined buffer requirement
        combined_buffer = (
            self.CAPITAL_CONSERVATION_BUFFER_PCT
            + countercyclical_buffer_pct
            + self.GSIB_BUFFER_PCT
        )

        # MDA (Maximum Distributable Amount) threshold
        mda_cet1_requirement = self.MIN_CET1_PCT + combined_buffer
        surplus_to_mda = (cet1_ratio - mda_cet1_requirement) * total_rwa / 100.0

        # Compliance check
        compliant = (
            cet1_ratio >= self.MIN_CET1_PCT
            and tier1_ratio >= self.MIN_TIER1_PCT
            and total_ratio >= self.MIN_TOTAL_CAPITAL_PCT
            and leverage_ratio >= self.MIN_LEVERAGE_PCT
            and cet1_ratio >= mda_cet1_requirement
        )

        return CapitalAdequacyResult(
            cet1_capital_eur=cet1_capital_eur,
            at1_capital_eur=at1_capital_eur,
            tier2_capital_eur=tier2_capital_eur,
            total_capital_eur=total_capital,
            credit_rwa_eur=credit_rwa_eur,
            market_rwa_eur=market_rwa_eur,
            operational_rwa_eur=operational_rwa_eur,
            total_rwa_eur=total_rwa,
            cet1_ratio_pct=round(cet1_ratio, 2),
            tier1_ratio_pct=round(tier1_ratio, 2),
            total_capital_ratio_pct=round(total_ratio, 2),
            leverage_ratio_pct=round(leverage_ratio, 2),
            leverage_exposure_eur=leverage_exposure_eur,
            countercyclical_buffer_pct=countercyclical_buffer_pct,
            combined_buffer_requirement_pct=round(combined_buffer, 2),
            surplus_to_mda_eur=round(surplus_to_mda, 2),
            compliant=compliant,
        )

    def comprehensive_assessment(
        self,
        entity_name: str = "BankCo",
        total_exposure_eur: float = 200_000_000_000,
        cet1_capital_eur: float = 25_000_000_000,
        trading_book_eur: float = 5_000_000_000,
        gross_income_eur: float = 8_000_000_000,
        warming_c: float = 1.5,
    ) -> BankRiskSummary:
        """Run all sub-modules and aggregate into a comprehensive bank risk profile."""
        # Credit risk
        credit = self.assess_credit_risk(
            total_exposure_eur=total_exposure_eur,
            warming_c=warming_c,
        )

        # Liquidity risk (defaults)
        liquidity = self.assess_liquidity_risk()

        # Market risk
        market = self.assess_market_risk(trading_book_eur=trading_book_eur)

        # Operational risk
        operational = self.assess_operational_risk(
            gross_income_year1_eur=gross_income_eur,
            gross_income_year2_eur=gross_income_eur * 0.95,
            gross_income_year3_eur=gross_income_eur * 1.02,
        )

        # AML risk (defaults)
        aml = self.assess_aml_risk()

        # Capital adequacy
        capital = self.assess_capital_adequacy(
            cet1_capital_eur=cet1_capital_eur,
            credit_rwa_eur=credit.risk_weighted_assets_eur,
            market_rwa_eur=market.market_risk_rwa_eur,
            operational_rwa_eur=operational.operational_risk_capital_eur * 12.5,
        )

        total_capital_req = (
            credit.credit_risk_capital_eur
            + market.market_risk_capital_eur
            + operational.operational_risk_capital_eur
        )

        # Overall rating
        if capital.cet1_ratio_pct >= 14:
            rating = "low"
        elif capital.cet1_ratio_pct >= 11:
            rating = "moderate"
        elif capital.cet1_ratio_pct >= 8.5:
            rating = "elevated"
        elif capital.cet1_ratio_pct >= 4.5:
            rating = "high"
        else:
            rating = "critical"

        # Recommendations
        recs = []
        if not capital.compliant:
            recs.append("URGENT: Capital ratios below minimum requirements — raise capital or reduce RWA")
        if not liquidity.lcr_compliant:
            recs.append("LCR below 100% — increase HQLA holdings or reduce outflow obligations")
        if not liquidity.nsfr_compliant:
            recs.append("NSFR below 100% — extend funding tenor or reduce RSF-heavy assets")
        if credit.ecl_coverage_ratio_pct > 2.0:
            recs.append("ECL coverage elevated — review credit quality of Stage 2/3 exposures")
        if aml.very_high_risk_count > 0:
            recs.append("Black-list country exposures detected — immediate remediation required")
        if aml.overall_aml_risk_score > 40:
            recs.append("AML risk score elevated — enhance counterparty due diligence procedures")
        if not recs:
            recs.append("All risk metrics within acceptable parameters")

        return BankRiskSummary(
            entity_name=entity_name,
            credit_risk=credit,
            liquidity_risk=liquidity,
            market_risk=market,
            operational_risk=operational,
            aml_risk=aml,
            capital_adequacy=capital,
            overall_risk_rating=rating,
            total_capital_requirement_eur=round(total_capital_req, 2),
            recommendations=recs,
        )

    # --- Convenience accessors ---

    def get_pd_term_structures(self) -> dict:
        """Return available PD term structures by rating."""
        return dict(self.PD_TERM_STRUCTURES)

    def get_lgd_collateral_types(self) -> dict:
        """Return LGD by collateral type."""
        return dict(self.LGD_BY_COLLATERAL)

    def get_risk_weights(self) -> dict:
        """Return Basel III/IV risk weights by exposure class."""
        return dict(self.RISK_WEIGHTS)

    def get_tsa_beta_factors(self) -> dict:
        """Return TSA beta factors by business line."""
        return dict(self.TSA_BETA_FACTORS)
