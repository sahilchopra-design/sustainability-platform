"""
Facilitated Emissions & Insurance-Associated Emissions Engine
PCAF Global GHG Accounting Standard v2.0 — Parts B & C

Part C: Capital Markets (Facilitated Emissions)
  Covers underwriting of bonds, equity issuance, securitisation, syndicated
  loan arrangement, and advisory mandates.  Attribution differs from financed:
    - Debt underwriting:   AF = underwritten_amount / (total_issuance × 3)
    - Equity underwriting: AF = shares_placed / (market_cap × 3)
    - Securitisation:      AF = tranche_held / total_securitised_pool
    - Syndicated loan:     AF = arranged_amount / total_facility
    - Advisory (M&A):      AF = 0 (disclosure-only per PCAF 2022 guidance)

Part B: Insurance-Associated Emissions
  Motor:       premium-weighted vehicle fleet emissions
  Property:    premium-weighted building emissions
  Commercial:  sector-avg revenue-based emissions
  Life/Health: disclosure-only (no direct attribution)

References:
  - PCAF Global GHG Accounting Standard v2.0 (2022), Parts B & C
  - PCAF Insurance-Associated Emissions Standard (2022)
  - EU Delegated Regulation 2022/1288 (SFDR PAI #1-#4)
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Enumerations
# ═══════════════════════════════════════════════════════════════════════════════

class FacilitatedDealType(str, Enum):
    """Capital markets deal types per PCAF Part C."""
    BOND_UNDERWRITING        = "bond_underwriting"
    EQUITY_PLACEMENT         = "equity_placement"
    CONVERTIBLE_UNDERWRITING = "convertible_underwriting"
    SECURITISATION           = "securitisation"       # MBS, ABS, CLO
    SYNDICATED_LOAN          = "syndicated_loan"       # arranger role
    IPO_UNDERWRITING         = "ipo_underwriting"
    ADVISORY_MNA             = "advisory_mna"          # M&A advisory
    ADVISORY_RESTRUCTURING   = "advisory_restructuring"


class InsuranceLineOfBusiness(str, Enum):
    """Insurance lines of business per PCAF Part B."""
    MOTOR_PERSONAL    = "motor_personal"
    MOTOR_COMMERCIAL  = "motor_commercial"
    PROPERTY_RESI     = "property_residential"
    PROPERTY_COMM     = "property_commercial"
    COMMERCIAL_LIAB   = "commercial_liability"
    COMMERCIAL_MARINE = "commercial_marine"
    COMMERCIAL_ENERGY = "commercial_energy"
    COMMERCIAL_OTHER  = "commercial_other"
    LIFE              = "life"
    HEALTH            = "health"


class BondType(str, Enum):
    CORPORATE     = "corporate"
    SOVEREIGN     = "sovereign"
    MUNICIPAL     = "municipal"
    GREEN         = "green"
    SOCIAL        = "social"
    SUSTAINABILITY = "sustainability"
    TRANSITION    = "transition"


class SecuritisationType(str, Enum):
    RMBS = "rmbs"    # Residential MBS
    CMBS = "cmbs"    # Commercial MBS
    ABS  = "abs"     # Asset-backed
    CLO  = "clo"     # Collateralised loan obligation
    CDO  = "cdo"     # Collateralised debt obligation


class VehicleFuelType(str, Enum):
    PETROL  = "petrol"
    DIESEL  = "diesel"
    HYBRID  = "hybrid"
    PHEV    = "phev"
    BEV     = "bev"
    LPG     = "lpg"
    CNG     = "cng"
    H2_FCEV = "h2_fcev"


class BuildingEPCRating(str, Enum):
    A_PLUS = "A+"
    A      = "A"
    B      = "B"
    C      = "C"
    D      = "D"
    E      = "E"
    F      = "F"
    G      = "G"


class DataQualityScore(int, Enum):
    """PCAF DQS 1-5 (lower = better)."""
    VERIFIED_PRIMARY     = 1
    UNVERIFIED_PRIMARY   = 2
    AUDITED_SECONDARY    = 3
    SECTOR_AVERAGE       = 4
    ESTIMATED_PROXY      = 5


# ═══════════════════════════════════════════════════════════════════════════════
# Reference Data Registries
# ═══════════════════════════════════════════════════════════════════════════════

# -- Sector emission intensities (tCO2e per $M revenue), GICS L2 ----
SECTOR_EMISSION_INTENSITIES: Dict[str, float] = {
    "Energy":                     820.0,
    "Materials":                  410.0,
    "Industrials":                180.0,
    "Consumer Discretionary":      85.0,
    "Consumer Staples":           110.0,
    "Health Care":                 55.0,
    "Financials":                  12.0,
    "Information Technology":      28.0,
    "Communication Services":      22.0,
    "Utilities":                  950.0,
    "Real Estate":                 95.0,
    "Sovereign":                  320.0,  # per $M GDP
    "Unknown":                    150.0,
}

# -- Vehicle emission factors (gCO2/km) by fuel type ----
VEHICLE_EMISSION_FACTORS: Dict[str, Dict[str, float]] = {
    VehicleFuelType.PETROL.value:  {"gco2_per_km": 170.0, "annual_km_default": 12000},
    VehicleFuelType.DIESEL.value:  {"gco2_per_km": 155.0, "annual_km_default": 18000},
    VehicleFuelType.HYBRID.value:  {"gco2_per_km": 105.0, "annual_km_default": 12000},
    VehicleFuelType.PHEV.value:    {"gco2_per_km":  60.0, "annual_km_default": 12000},
    VehicleFuelType.BEV.value:     {"gco2_per_km":   0.0, "annual_km_default": 12000},  # scope 1 = 0
    VehicleFuelType.LPG.value:     {"gco2_per_km": 145.0, "annual_km_default": 15000},
    VehicleFuelType.CNG.value:     {"gco2_per_km": 135.0, "annual_km_default": 15000},
    VehicleFuelType.H2_FCEV.value: {"gco2_per_km":   0.0, "annual_km_default": 12000},
}

# -- Building emission factors (kgCO2/m² p.a.) by EPC rating ----
BUILDING_EMISSION_FACTORS: Dict[str, Dict[str, float]] = {
    BuildingEPCRating.A_PLUS.value: {"kgco2_per_m2": 8.0,   "kwh_per_m2": 25.0},
    BuildingEPCRating.A.value:      {"kgco2_per_m2": 15.0,  "kwh_per_m2": 50.0},
    BuildingEPCRating.B.value:      {"kgco2_per_m2": 30.0,  "kwh_per_m2": 100.0},
    BuildingEPCRating.C.value:      {"kgco2_per_m2": 50.0,  "kwh_per_m2": 150.0},
    BuildingEPCRating.D.value:      {"kgco2_per_m2": 75.0,  "kwh_per_m2": 225.0},
    BuildingEPCRating.E.value:      {"kgco2_per_m2": 100.0, "kwh_per_m2": 300.0},
    BuildingEPCRating.F.value:      {"kgco2_per_m2": 135.0, "kwh_per_m2": 400.0},
    BuildingEPCRating.G.value:      {"kgco2_per_m2": 180.0, "kwh_per_m2": 550.0},
}

# -- Insurance LoB default emission multipliers (tCO2e per $M premium) --
INSURANCE_LOB_FACTORS: Dict[str, float] = {
    InsuranceLineOfBusiness.MOTOR_PERSONAL.value:    42.0,
    InsuranceLineOfBusiness.MOTOR_COMMERCIAL.value:  85.0,
    InsuranceLineOfBusiness.PROPERTY_RESI.value:     28.0,
    InsuranceLineOfBusiness.PROPERTY_COMM.value:     55.0,
    InsuranceLineOfBusiness.COMMERCIAL_LIAB.value:   35.0,
    InsuranceLineOfBusiness.COMMERCIAL_MARINE.value: 120.0,
    InsuranceLineOfBusiness.COMMERCIAL_ENERGY.value: 450.0,
    InsuranceLineOfBusiness.COMMERCIAL_OTHER.value:  65.0,
    InsuranceLineOfBusiness.LIFE.value:              5.0,   # disclosure-only proxy
    InsuranceLineOfBusiness.HEALTH.value:            5.0,
}

# PCAF ÷3 factor for capital markets time-in-year attribution
_PCAF_TIME_FACTOR = Decimal("0.333333")


# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses — Inputs
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IssuerEmissions:
    """Issuer-level emissions data required for attribution."""
    scope1_tco2e: float = 0.0
    scope2_tco2e: float = 0.0
    scope3_tco2e: float = 0.0
    include_scope3: bool = False
    data_source: str = "self_reported"    # direct_measurement | audited_report | self_reported | sector_average | estimated
    reporting_year: int = 2024
    verification_status: str = "unverified"

    @property
    def total_scope12(self) -> float:
        return self.scope1_tco2e + self.scope2_tco2e

    @property
    def total_all_scopes(self) -> float:
        base = self.total_scope12
        return base + self.scope3_tco2e if self.include_scope3 else base


@dataclass
class FacilitatedDealInput:
    """Complete deal-level input for facilitated emissions calculation."""
    deal_id: str = ""
    deal_type: str = "bond_underwriting"
    # Issuer / counterparty
    issuer_name: str = ""
    issuer_id: Optional[str] = None          # LEI or internal
    issuer_sector_gics: str = "Unknown"
    issuer_country_iso2: str = "US"
    issuer_revenue_musd: Optional[float] = None
    # Deal economics
    underwritten_amount_musd: float = 0.0     # bank's participation
    total_deal_size_musd: float = 0.0         # total issuance / facility
    shares_placed_value_musd: float = 0.0     # equity only
    market_cap_musd: float = 0.0              # equity only
    tranche_held_musd: float = 0.0            # securitisation only
    total_pool_musd: float = 0.0              # securitisation only
    arranged_amount_musd: float = 0.0         # syndicated loan only
    total_facility_musd: float = 0.0          # syndicated loan only
    # Bond details
    bond_type: str = "corporate"
    coupon_rate_pct: Optional[float] = None
    maturity_years: Optional[int] = None
    credit_rating: Optional[str] = None
    # Equity details
    ipo_or_secondary: str = "secondary"       # ipo | secondary | block_trade
    offer_price: Optional[float] = None
    shares_offered: Optional[int] = None
    overallotment_pct: float = 0.0            # green-shoe option %
    # Securitisation details
    securitisation_type: str = "rmbs"
    underlying_asset_count: Optional[int] = None
    weighted_avg_life_years: Optional[float] = None
    # Green / sustainable classification
    green_bond: bool = False
    use_of_proceeds: str = "general"          # general | green | social | sustainability | transition
    eu_taxonomy_aligned_pct: float = 0.0
    # Issuer emissions
    emissions: Optional[IssuerEmissions] = None
    # Override DQS
    pcaf_dqs_override: Optional[int] = None
    # Metadata
    transaction_date: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class InsurancePolicyInput:
    """Complete policy-level input for insurance-associated emissions."""
    policy_id: str = ""
    line_of_business: str = "motor_personal"
    # Policyholder
    policyholder_name: str = ""
    policyholder_id: Optional[str] = None
    policyholder_sector_gics: str = "Unknown"
    policyholder_country_iso2: str = "US"
    # Premium & claims
    gross_written_premium_musd: float = 0.0
    net_earned_premium_musd: float = 0.0
    claims_paid_musd: float = 0.0
    loss_ratio_pct: Optional[float] = None
    # Motor-specific
    vehicle_count: int = 0
    fuel_type: str = "petrol"
    annual_km_per_vehicle: Optional[float] = None
    avg_engine_cc: Optional[int] = None
    # Property-specific
    insured_property_area_m2: float = 0.0
    epc_rating: str = "D"
    building_type: str = "commercial"          # residential | commercial | industrial
    building_year: Optional[int] = None
    # Commercial-specific
    insured_revenue_musd: Optional[float] = None
    nace_sector: Optional[str] = None
    # Direct emissions data (overrides defaults)
    policyholder_scope1_tco2e: Optional[float] = None
    policyholder_scope2_tco2e: Optional[float] = None
    # Data quality
    data_source: str = "sector_average"
    pcaf_dqs_override: Optional[int] = None
    # Metadata
    policy_inception_date: Optional[str] = None
    policy_expiry_date: Optional[str] = None
    reporting_year: int = 2024
    notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses — Results
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FacilitatedEmissionsResult:
    """Per-deal facilitated emissions result."""
    deal_id: str
    deal_type: str
    issuer_name: str
    # Attribution
    attribution_factor: Optional[float] = None
    attribution_method: str = ""
    # Emissions attributed
    facilitated_scope1_tco2e: Optional[float] = None
    facilitated_scope2_tco2e: Optional[float] = None
    facilitated_scope3_tco2e: Optional[float] = None
    facilitated_total_tco2e: Optional[float] = None
    # Issuer totals (context)
    issuer_total_scope12_tco2e: float = 0.0
    issuer_total_scope3_tco2e: float = 0.0
    # Deal economics summary
    bank_participation_musd: float = 0.0
    total_deal_musd: float = 0.0
    # Quality & classification
    pcaf_dqs: int = 5
    green_classification: str = "general"
    eu_taxonomy_aligned_pct: float = 0.0
    # Audit
    methodology_note: str = ""
    warnings: List[str] = field(default_factory=list)
    calculated_at: str = ""


@dataclass
class InsuranceEmissionsResult:
    """Per-policy insurance-associated emissions result."""
    policy_id: str
    line_of_business: str
    policyholder_name: str
    # Attribution
    attribution_factor: Optional[float] = None
    attribution_method: str = ""
    # Emissions attributed
    insured_scope1_tco2e: Optional[float] = None
    insured_scope2_tco2e: Optional[float] = None
    insured_total_tco2e: Optional[float] = None
    # Economic context
    gross_premium_musd: float = 0.0
    emission_intensity_per_m_premium: Optional[float] = None
    # Quality
    pcaf_dqs: int = 5
    # Audit
    methodology_note: str = ""
    warnings: List[str] = field(default_factory=list)
    calculated_at: str = ""


@dataclass
class PortfolioFacilitatedSummary:
    """Portfolio-level facilitated emissions summary."""
    total_deals: int = 0
    total_facilitated_tco2e: float = 0.0
    total_scope1_facilitated: float = 0.0
    total_scope2_facilitated: float = 0.0
    total_scope3_facilitated: float = 0.0
    total_bank_participation_musd: float = 0.0
    avg_pcaf_dqs: float = 5.0
    by_deal_type: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    by_sector: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    green_bond_count: int = 0
    green_bond_facilitated_tco2e: float = 0.0
    methodology: str = "PCAF Global GHG Accounting Standard v2.0 — Part C: Capital Markets"


@dataclass
class PortfolioInsuranceSummary:
    """Portfolio-level insurance-associated emissions summary."""
    total_policies: int = 0
    total_insured_tco2e: float = 0.0
    total_scope1_insured: float = 0.0
    total_scope2_insured: float = 0.0
    total_gwp_musd: float = 0.0
    avg_pcaf_dqs: float = 5.0
    by_lob: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    by_sector: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    methodology: str = "PCAF Insurance-Associated Emissions Standard (2022)"


# ═══════════════════════════════════════════════════════════════════════════════
# DQS Derivation
# ═══════════════════════════════════════════════════════════════════════════════

_DQS_SOURCE_MAP = {
    "direct_measurement": 1,
    "audited_report":     2,
    "self_reported":      3,
    "sector_average":     4,
    "estimated":          5,
}


def derive_dqs(data_source: str, override: Optional[int] = None,
               has_scope1: bool = False, has_scope2: bool = False,
               verified: bool = False) -> int:
    """Derive PCAF Data Quality Score from available information."""
    if override and 1 <= override <= 5:
        return override
    base = _DQS_SOURCE_MAP.get(data_source, 5)
    # Improve if verified primary data present
    if has_scope1 and has_scope2 and verified:
        base = min(base, 2)
    elif has_scope1 and has_scope2:
        base = min(base, 3)
    return max(1, min(5, base))


# ═══════════════════════════════════════════════════════════════════════════════
# Core Calculation Engine
# ═══════════════════════════════════════════════════════════════════════════════

class FacilitatedEmissionsEngine:
    """
    Comprehensive engine for PCAF Part C (facilitated) and Part B
    (insurance-associated) emissions calculation.
    """

    # ────────────────────────────────────────────────────────────────────────
    # PCAF PART C — FACILITATED EMISSIONS
    # ────────────────────────────────────────────────────────────────────────

    def calculate_facilitated(self, deal: FacilitatedDealInput) -> FacilitatedEmissionsResult:
        """Calculate facilitated emissions for a single deal."""
        now = datetime.now(timezone.utc).isoformat()
        warnings: List[str] = []

        # Default emissions if not provided
        emissions = deal.emissions or IssuerEmissions()

        # If no direct emissions, estimate from sector intensity
        if emissions.scope1_tco2e == 0 and emissions.scope2_tco2e == 0:
            if deal.issuer_revenue_musd and deal.issuer_revenue_musd > 0:
                intensity = SECTOR_EMISSION_INTENSITIES.get(
                    deal.issuer_sector_gics, 150.0
                )
                estimated_total = deal.issuer_revenue_musd * intensity
                emissions.scope1_tco2e = estimated_total * 0.6  # assume 60/40 split
                emissions.scope2_tco2e = estimated_total * 0.4
                warnings.append(
                    f"Issuer emissions estimated from sector intensity "
                    f"({intensity} tCO2e/$M) × revenue (${deal.issuer_revenue_musd}M)"
                )
            else:
                warnings.append("No issuer emissions or revenue data — attribution not possible")

        # Compute attribution factor
        af, method = self._compute_attribution_factor(deal, warnings)

        # DQS
        dqs = derive_dqs(
            emissions.data_source,
            deal.pcaf_dqs_override,
            has_scope1=(emissions.scope1_tco2e > 0),
            has_scope2=(emissions.scope2_tco2e > 0),
            verified=(emissions.verification_status == "verified"),
        )

        # Compute facilitated emissions
        s1_fac = s2_fac = s3_fac = total_fac = None
        if af is not None:
            s1_fac = round(af * emissions.scope1_tco2e, 4)
            s2_fac = round(af * emissions.scope2_tco2e, 4)
            if emissions.include_scope3 and emissions.scope3_tco2e > 0:
                s3_fac = round(af * emissions.scope3_tco2e, 4)
            total_fac = round(
                af * emissions.total_all_scopes, 4
            )

        # Green classification
        green_class = deal.use_of_proceeds if deal.green_bond else "general"

        # Bank participation amount (for summary)
        bank_part = self._get_bank_participation(deal)

        return FacilitatedEmissionsResult(
            deal_id=deal.deal_id or f"FE-{uuid4().hex[:8].upper()}",
            deal_type=deal.deal_type,
            issuer_name=deal.issuer_name,
            attribution_factor=round(af, 6) if af is not None else None,
            attribution_method=method,
            facilitated_scope1_tco2e=s1_fac,
            facilitated_scope2_tco2e=s2_fac,
            facilitated_scope3_tco2e=s3_fac,
            facilitated_total_tco2e=total_fac,
            issuer_total_scope12_tco2e=emissions.total_scope12,
            issuer_total_scope3_tco2e=emissions.scope3_tco2e,
            bank_participation_musd=bank_part,
            total_deal_musd=deal.total_deal_size_musd or deal.total_pool_musd or deal.total_facility_musd or 0.0,
            pcaf_dqs=dqs,
            green_classification=green_class,
            eu_taxonomy_aligned_pct=deal.eu_taxonomy_aligned_pct,
            methodology_note=method,
            warnings=warnings,
            calculated_at=now,
        )

    def calculate_facilitated_batch(
        self, deals: List[FacilitatedDealInput]
    ) -> Tuple[List[FacilitatedEmissionsResult], PortfolioFacilitatedSummary]:
        """Calculate facilitated emissions for multiple deals and produce summary."""
        results = [self.calculate_facilitated(d) for d in deals]
        summary = self._aggregate_facilitated(results)
        return results, summary

    # ────────────────────────────────────────────────────────────────────────
    # PCAF PART B — INSURANCE-ASSOCIATED EMISSIONS
    # ────────────────────────────────────────────────────────────────────────

    def calculate_insurance(self, policy: InsurancePolicyInput) -> InsuranceEmissionsResult:
        """Calculate insurance-associated emissions for a single policy."""
        now = datetime.now(timezone.utc).isoformat()
        warnings: List[str] = []
        lob = policy.line_of_business

        # DQS
        dqs = derive_dqs(
            policy.data_source,
            policy.pcaf_dqs_override,
            has_scope1=(policy.policyholder_scope1_tco2e is not None),
            has_scope2=(policy.policyholder_scope2_tco2e is not None),
        )

        af = None
        method = ""
        s1_ins = s2_ins = total_ins = None
        intensity = None

        # ── Motor insurance ────────────────────────────────────
        if lob in (InsuranceLineOfBusiness.MOTOR_PERSONAL.value,
                   InsuranceLineOfBusiness.MOTOR_COMMERCIAL.value):
            s1_ins, s2_ins, total_ins, af, method = self._calc_motor(policy, warnings)

        # ── Property insurance ─────────────────────────────────
        elif lob in (InsuranceLineOfBusiness.PROPERTY_RESI.value,
                     InsuranceLineOfBusiness.PROPERTY_COMM.value):
            s1_ins, s2_ins, total_ins, af, method = self._calc_property(policy, warnings)

        # ── Commercial lines ───────────────────────────────────
        elif lob in (InsuranceLineOfBusiness.COMMERCIAL_LIAB.value,
                     InsuranceLineOfBusiness.COMMERCIAL_MARINE.value,
                     InsuranceLineOfBusiness.COMMERCIAL_ENERGY.value,
                     InsuranceLineOfBusiness.COMMERCIAL_OTHER.value):
            s1_ins, s2_ins, total_ins, af, method = self._calc_commercial(policy, warnings)

        # ── Life / Health (disclosure only) ────────────────────
        elif lob in (InsuranceLineOfBusiness.LIFE.value,
                     InsuranceLineOfBusiness.HEALTH.value):
            method = "PCAF Part B: Life/Health — disclosure-only, no direct attribution"
            warnings.append("Life/health lines: PCAF provides disclosure-only guidance; proxy estimate used")
            factor = INSURANCE_LOB_FACTORS.get(lob, 5.0)
            gwp = policy.gross_written_premium_musd
            total_ins = round(gwp * factor, 4) if gwp > 0 else 0.0
            s1_ins = round(total_ins * 0.3, 4)
            s2_ins = round(total_ins * 0.7, 4)
            af = factor
            intensity = factor

        if total_ins is not None and policy.gross_written_premium_musd > 0:
            intensity = round(total_ins / policy.gross_written_premium_musd, 4)

        return InsuranceEmissionsResult(
            policy_id=policy.policy_id or f"INS-{uuid4().hex[:8].upper()}",
            line_of_business=lob,
            policyholder_name=policy.policyholder_name,
            attribution_factor=round(af, 6) if af is not None else None,
            attribution_method=method,
            insured_scope1_tco2e=s1_ins,
            insured_scope2_tco2e=s2_ins,
            insured_total_tco2e=total_ins,
            gross_premium_musd=policy.gross_written_premium_musd,
            emission_intensity_per_m_premium=intensity,
            pcaf_dqs=dqs,
            methodology_note=method,
            warnings=warnings,
            calculated_at=now,
        )

    def calculate_insurance_batch(
        self, policies: List[InsurancePolicyInput]
    ) -> Tuple[List[InsuranceEmissionsResult], PortfolioInsuranceSummary]:
        """Calculate insurance emissions for multiple policies and produce summary."""
        results = [self.calculate_insurance(p) for p in policies]
        summary = self._aggregate_insurance(results)
        return results, summary

    # ────────────────────────────────────────────────────────────────────────
    # Reference Data Lookups
    # ────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_sector_intensities() -> Dict[str, float]:
        """Return the full sector emission intensity registry."""
        return dict(SECTOR_EMISSION_INTENSITIES)

    @staticmethod
    def get_vehicle_factors() -> Dict[str, Dict[str, float]]:
        return {k: dict(v) for k, v in VEHICLE_EMISSION_FACTORS.items()}

    @staticmethod
    def get_building_factors() -> Dict[str, Dict[str, float]]:
        return {k: dict(v) for k, v in BUILDING_EMISSION_FACTORS.items()}

    @staticmethod
    def get_insurance_lob_factors() -> Dict[str, float]:
        return dict(INSURANCE_LOB_FACTORS)

    @staticmethod
    def get_deal_types() -> List[Dict[str, str]]:
        return [
            {"value": dt.value, "label": dt.name.replace("_", " ").title()}
            for dt in FacilitatedDealType
        ]

    @staticmethod
    def get_insurance_lobs() -> List[Dict[str, str]]:
        return [
            {"value": lob.value, "label": lob.name.replace("_", " ").title()}
            for lob in InsuranceLineOfBusiness
        ]

    # ────────────────────────────────────────────────────────────────────────
    # Private Helpers — Attribution Factor
    # ────────────────────────────────────────────────────────────────────────

    def _compute_attribution_factor(
        self, deal: FacilitatedDealInput, warnings: List[str]
    ) -> Tuple[Optional[float], str]:
        """Compute AF based on deal type per PCAF Part C methodology."""
        dt = deal.deal_type

        # -- Bond / Convertible underwriting --
        if dt in (FacilitatedDealType.BOND_UNDERWRITING.value,
                  FacilitatedDealType.CONVERTIBLE_UNDERWRITING.value):
            if deal.underwritten_amount_musd > 0 and deal.total_deal_size_musd > 0:
                af = (deal.underwritten_amount_musd / deal.total_deal_size_musd) * float(_PCAF_TIME_FACTOR)
                method = (
                    f"PCAF Part C Debt: AF = ({deal.underwritten_amount_musd}M / "
                    f"{deal.total_deal_size_musd}M) x (1/3) = {af:.6f}"
                )
                return af, method
            warnings.append("Missing underwritten/total amounts for bond AF calculation")
            return None, "Insufficient data for debt underwriting AF"

        # -- Equity placement / IPO --
        if dt in (FacilitatedDealType.EQUITY_PLACEMENT.value,
                  FacilitatedDealType.IPO_UNDERWRITING.value):
            placed = deal.shares_placed_value_musd
            mcap = deal.market_cap_musd
            if placed > 0 and mcap > 0:
                # Account for overallotment
                effective_placed = placed * (1 + deal.overallotment_pct / 100.0)
                af = (effective_placed / mcap) * float(_PCAF_TIME_FACTOR)
                method = (
                    f"PCAF Part C Equity: AF = ({effective_placed:.2f}M placed / "
                    f"{mcap}M market cap) x (1/3) = {af:.6f}"
                )
                return af, method
            warnings.append("Missing placed value/market cap for equity AF calculation")
            return None, "Insufficient data for equity AF"

        # -- Securitisation --
        if dt == FacilitatedDealType.SECURITISATION.value:
            if deal.tranche_held_musd > 0 and deal.total_pool_musd > 0:
                af = deal.tranche_held_musd / deal.total_pool_musd
                method = (
                    f"PCAF Part C Securitisation: AF = {deal.tranche_held_musd}M / "
                    f"{deal.total_pool_musd}M pool = {af:.6f} (no ÷3 time factor)"
                )
                return af, method
            warnings.append("Missing tranche/pool data for securitisation AF")
            return None, "Insufficient data for securitisation AF"

        # -- Syndicated loan arrangement --
        if dt == FacilitatedDealType.SYNDICATED_LOAN.value:
            if deal.arranged_amount_musd > 0 and deal.total_facility_musd > 0:
                af = deal.arranged_amount_musd / deal.total_facility_musd
                method = (
                    f"PCAF Part C Syndicated: AF = {deal.arranged_amount_musd}M / "
                    f"{deal.total_facility_musd}M facility = {af:.6f}"
                )
                return af, method
            warnings.append("Missing arranged/facility amounts for syndicated loan AF")
            return None, "Insufficient data for syndicated loan AF"

        # -- Advisory (M&A / Restructuring) --
        if dt in (FacilitatedDealType.ADVISORY_MNA.value,
                  FacilitatedDealType.ADVISORY_RESTRUCTURING.value):
            warnings.append(
                "PCAF 2022: Advisory mandates — AF = 0 (disclosure-only). "
                "Issuer emissions reported for transparency."
            )
            return 0.0, "PCAF Part C Advisory: AF = 0 (disclosure-only per 2022 guidance)"

        warnings.append(f"Unknown deal type: {dt}")
        return None, f"No AF methodology for deal type '{dt}'"

    def _get_bank_participation(self, deal: FacilitatedDealInput) -> float:
        """Return the bank's $ participation in the deal."""
        dt = deal.deal_type
        if dt in (FacilitatedDealType.BOND_UNDERWRITING.value,
                  FacilitatedDealType.CONVERTIBLE_UNDERWRITING.value):
            return deal.underwritten_amount_musd
        if dt in (FacilitatedDealType.EQUITY_PLACEMENT.value,
                  FacilitatedDealType.IPO_UNDERWRITING.value):
            return deal.shares_placed_value_musd
        if dt == FacilitatedDealType.SECURITISATION.value:
            return deal.tranche_held_musd
        if dt == FacilitatedDealType.SYNDICATED_LOAN.value:
            return deal.arranged_amount_musd
        return 0.0

    # ────────────────────────────────────────────────────────────────────────
    # Private Helpers — Insurance LoB Calculations
    # ────────────────────────────────────────────────────────────────────────

    def _calc_motor(
        self, p: InsurancePolicyInput, warnings: List[str]
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], str]:
        """Motor insurance emissions — vehicle-count × km × gCO2/km."""
        if p.policyholder_scope1_tco2e is not None:
            # Direct data
            s1 = p.policyholder_scope1_tco2e
            s2 = p.policyholder_scope2_tco2e or 0.0
            total = s1 + s2
            af = 1.0  # direct attribution
            method = "PCAF Part B Motor: Direct policyholder emissions data"
            return s1, s2, total, af, method

        fuel_data = VEHICLE_EMISSION_FACTORS.get(p.fuel_type, VEHICLE_EMISSION_FACTORS["petrol"])
        gco2_km = fuel_data["gco2_per_km"]
        annual_km = p.annual_km_per_vehicle or fuel_data["annual_km_default"]
        vehicles = max(p.vehicle_count, 1)

        # Total fleet emissions (scope 1 = tailpipe, scope 2 = charging for BEV/PHEV)
        total_gco2 = vehicles * annual_km * gco2_km
        total_tco2e = total_gco2 / 1_000_000  # g → t

        if p.fuel_type in (VehicleFuelType.BEV.value, VehicleFuelType.H2_FCEV.value):
            s1 = 0.0
            s2 = round(total_tco2e, 4)  # grid electricity
        elif p.fuel_type == VehicleFuelType.PHEV.value:
            s1 = round(total_tco2e * 0.5, 4)
            s2 = round(total_tco2e * 0.5, 4)
        else:
            s1 = round(total_tco2e, 4)
            s2 = 0.0

        total = round(s1 + s2, 4)
        af = gco2_km / 1000.0  # effective factor per km
        method = (
            f"PCAF Part B Motor: {vehicles} vehicles × {annual_km:.0f} km/yr × "
            f"{gco2_km} gCO2/km ({p.fuel_type}) = {total:.2f} tCO2e"
        )
        return s1, s2, total, af, method

    def _calc_property(
        self, p: InsurancePolicyInput, warnings: List[str]
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], str]:
        """Property insurance emissions — area × kgCO2/m²."""
        if p.policyholder_scope1_tco2e is not None:
            s1 = p.policyholder_scope1_tco2e
            s2 = p.policyholder_scope2_tco2e or 0.0
            total = s1 + s2
            method = "PCAF Part B Property: Direct policyholder emissions data"
            return s1, s2, total, 1.0, method

        area = p.insured_property_area_m2
        if area <= 0:
            # Fallback: premium-based
            factor = INSURANCE_LOB_FACTORS.get(p.line_of_business, 40.0)
            total = round(p.gross_written_premium_musd * factor, 4)
            s1 = round(total * 0.4, 4)  # heating/gas
            s2 = round(total * 0.6, 4)  # electricity
            warnings.append("No insured area — used premium-based proxy")
            method = f"PCAF Part B Property: Premium proxy — {factor} tCO2e/$M GWP"
            return s1, s2, total, factor, method

        bld_data = BUILDING_EMISSION_FACTORS.get(p.epc_rating, BUILDING_EMISSION_FACTORS["D"])
        kgco2_m2 = bld_data["kgco2_per_m2"]

        total_kgco2 = area * kgco2_m2
        total_tco2e = total_kgco2 / 1000.0

        # Split: gas heating ~40% scope1, electricity ~60% scope2
        s1 = round(total_tco2e * 0.4, 4)
        s2 = round(total_tco2e * 0.6, 4)
        total = round(s1 + s2, 4)
        af = kgco2_m2 / 1000.0
        method = (
            f"PCAF Part B Property: {area:.0f} m² × {kgco2_m2} kgCO2/m² "
            f"(EPC {p.epc_rating}) = {total:.2f} tCO2e"
        )
        return s1, s2, total, af, method

    def _calc_commercial(
        self, p: InsurancePolicyInput, warnings: List[str]
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], str]:
        """Commercial lines — sector-based revenue intensity or premium proxy."""
        if p.policyholder_scope1_tco2e is not None:
            s1 = p.policyholder_scope1_tco2e
            s2 = p.policyholder_scope2_tco2e or 0.0
            total = s1 + s2
            method = "PCAF Part B Commercial: Direct policyholder emissions data"
            return s1, s2, total, 1.0, method

        # Revenue-based approach
        if p.insured_revenue_musd and p.insured_revenue_musd > 0:
            sector = p.policyholder_sector_gics or "Unknown"
            intensity = SECTOR_EMISSION_INTENSITIES.get(sector, 150.0)
            total = round(p.insured_revenue_musd * intensity, 4)
            s1 = round(total * 0.6, 4)
            s2 = round(total * 0.4, 4)
            af = intensity
            method = (
                f"PCAF Part B Commercial: ${p.insured_revenue_musd}M revenue × "
                f"{intensity} tCO2e/$M ({sector}) = {total:.2f} tCO2e"
            )
            return s1, s2, total, af, method

        # Premium-based proxy
        factor = INSURANCE_LOB_FACTORS.get(p.line_of_business, 65.0)
        total = round(p.gross_written_premium_musd * factor, 4)
        s1 = round(total * 0.6, 4)
        s2 = round(total * 0.4, 4)
        warnings.append("No revenue data — used premium-based LoB proxy")
        method = f"PCAF Part B Commercial: Premium proxy — {factor} tCO2e/$M GWP"
        return s1, s2, total, factor, method

    # ────────────────────────────────────────────────────────────────────────
    # Private Helpers — Aggregation
    # ────────────────────────────────────────────────────────────────────────

    def _aggregate_facilitated(
        self, results: List[FacilitatedEmissionsResult]
    ) -> PortfolioFacilitatedSummary:
        """Aggregate deal-level results into portfolio summary."""
        s = PortfolioFacilitatedSummary()
        s.total_deals = len(results)
        dqs_vals = []
        for r in results:
            s1 = r.facilitated_scope1_tco2e or 0.0
            s2 = r.facilitated_scope2_tco2e or 0.0
            s3 = r.facilitated_scope3_tco2e or 0.0
            tot = r.facilitated_total_tco2e or 0.0
            s.total_facilitated_tco2e += tot
            s.total_scope1_facilitated += s1
            s.total_scope2_facilitated += s2
            s.total_scope3_facilitated += s3
            s.total_bank_participation_musd += r.bank_participation_musd
            dqs_vals.append(r.pcaf_dqs)

            # By deal type
            dt = r.deal_type
            if dt not in s.by_deal_type:
                s.by_deal_type[dt] = {"count": 0, "facilitated_tco2e": 0.0, "participation_musd": 0.0}
            s.by_deal_type[dt]["count"] += 1
            s.by_deal_type[dt]["facilitated_tco2e"] += tot
            s.by_deal_type[dt]["participation_musd"] += r.bank_participation_musd

            # Green bonds
            if r.green_classification != "general":
                s.green_bond_count += 1
                s.green_bond_facilitated_tco2e += tot

        s.avg_pcaf_dqs = round(sum(dqs_vals) / len(dqs_vals), 2) if dqs_vals else 5.0
        s.total_facilitated_tco2e = round(s.total_facilitated_tco2e, 4)
        s.total_scope1_facilitated = round(s.total_scope1_facilitated, 4)
        s.total_scope2_facilitated = round(s.total_scope2_facilitated, 4)
        s.total_scope3_facilitated = round(s.total_scope3_facilitated, 4)
        return s

    def _aggregate_insurance(
        self, results: List[InsuranceEmissionsResult]
    ) -> PortfolioInsuranceSummary:
        """Aggregate policy-level results into portfolio summary."""
        s = PortfolioInsuranceSummary()
        s.total_policies = len(results)
        dqs_vals = []
        for r in results:
            s1 = r.insured_scope1_tco2e or 0.0
            s2 = r.insured_scope2_tco2e or 0.0
            tot = r.insured_total_tco2e or 0.0
            s.total_insured_tco2e += tot
            s.total_scope1_insured += s1
            s.total_scope2_insured += s2
            s.total_gwp_musd += r.gross_premium_musd
            dqs_vals.append(r.pcaf_dqs)

            # By LoB
            lob = r.line_of_business
            if lob not in s.by_lob:
                s.by_lob[lob] = {"count": 0, "insured_tco2e": 0.0, "gwp_musd": 0.0}
            s.by_lob[lob]["count"] += 1
            s.by_lob[lob]["insured_tco2e"] += tot
            s.by_lob[lob]["gwp_musd"] += r.gross_premium_musd

        s.avg_pcaf_dqs = round(sum(dqs_vals) / len(dqs_vals), 2) if dqs_vals else 5.0
        s.total_insured_tco2e = round(s.total_insured_tco2e, 4)
        s.total_scope1_insured = round(s.total_scope1_insured, 4)
        s.total_scope2_insured = round(s.total_scope2_insured, 4)
        return s
