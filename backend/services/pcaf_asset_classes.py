"""
PCAF Asset Class Registry (P1-6)
===================================
Provides per-asset-class DQS (Data Quality Score) tier tables, data source
guidance, and automatic DQS derivation from what's available — per PCAF
Global GHG Accounting & Reporting Standard v2.0 (November 2022).

Supplements pcaf_waci_engine.py with:
  1. DQS_TIER_TABLES — per-asset-class DQS 1-5 criteria and data sources
  2. derive_dqs()     — auto-infer DQS from available data fields
  3. LISTED_EQUITY_DQS_GUIDANCE — full Part A §3.2 listed equity methodology
  4. ATTRIBUTION_FACTOR_GUIDANCE — per-asset-class AF calculation summary
  5. DATA_SOURCE_REGISTRY — acceptable external data sources per DQS tier

References:
  PCAF Standard v2.0 Part A — Listed Equity and Corporate Bonds (§3.1–§3.5)
  PCAF Standard v2.0 Part B — Business Loans and Unlisted Equity (§4.1–§4.4)
  PCAF Standard v2.0 Part C — Project Finance (§5.1–§5.4)
  PCAF Standard v2.0 Part D — Commercial Real Estate (§6.1–§6.4)
  PCAF Standard v2.0 Part E — Mortgages (§7.1–§7.3)
  PCAF Standard v2.0 Part F — Motor Vehicle Loans (§8.1–§8.3)
  PCAF Standard v2.0 Part G — Sovereign Bonds (§9.1–§9.3)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# DQS Tier Tables — per asset class
# ---------------------------------------------------------------------------

DQS_TIER_TABLES: Dict[str, List[Dict]] = {

    # ── PCAF Part A — Listed Equity ──────────────────────────────────────
    "listed_equity": [
        {
            "tier": 1,
            "label": "Reported, third-party verified",
            "criteria": (
                "Company-reported Scope 1+2 (and ideally Scope 3) emissions, "
                "verified by an independent third party (CDP A/A- list, "
                "limited or reasonable assurance by accredited verifier)."
            ),
            "data_sources": ["CDP A/A-list", "Company ESG report with assurance", "Bloomberg ESG verified"],
            "attribution_method": "outstanding_amount / EVIC",
            "emission_basis": "Scope 1 + Scope 2 (market-based preferred)",
        },
        {
            "tier": 2,
            "label": "Reported, unverified",
            "criteria": (
                "Company-reported Scope 1+2 emissions without independent "
                "verification. Includes CDP self-reported, annual reports, "
                "sustainability reports without assurance."
            ),
            "data_sources": ["CDP self-reported", "Company sustainability report (no assurance)",
                             "Refinitiv ESG", "MSCI ESG"],
            "attribution_method": "outstanding_amount / EVIC",
            "emission_basis": "Scope 1 + Scope 2 (location-based if market-based unavailable)",
        },
        {
            "tier": 3,
            "label": "Estimated from reported activity data",
            "criteria": (
                "Emissions estimated using company-reported activity data "
                "(e.g. production volumes, energy consumption) and "
                "GHG Protocol-based emission factors."
            ),
            "data_sources": ["Company production data + GHG Protocol EF", "IEA EF + company energy data"],
            "attribution_method": "outstanding_amount / EVIC",
            "emission_basis": "Scope 1 + Scope 2 estimated from activity",
        },
        {
            "tier": 4,
            "label": "Sector-average emission factors",
            "criteria": (
                "Revenue-based emission factor from EXIOBASE MRIO or equivalent "
                "sector-level emission intensity, multiplied by company revenue."
            ),
            "data_sources": ["EXIOBASE v3 MRIO", "WIOD MRIO", "SBTi sector benchmarks"],
            "attribution_method": "outstanding_amount / EVIC",
            "emission_basis": "Scope 1 + Scope 2 estimated from sector × revenue",
        },
        {
            "tier": 5,
            "label": "Country/region average emission factors",
            "criteria": (
                "Lowest quality — emission factor based solely on country or "
                "region average; no company- or sector-specific information used."
            ),
            "data_sources": ["IEA country emission factors", "OECD STAN averages", "World Bank"],
            "attribution_method": "outstanding_amount / EVIC",
            "emission_basis": "Scope 1 + Scope 2 from country average intensity",
        },
    ],

    # ── PCAF Part A — Corporate Bonds ────────────────────────────────────
    "corporate_bonds": [
        {"tier": 1, "label": "Reported, verified", "criteria": "Same as Listed Equity DQS 1",
         "data_sources": ["CDP A/A-list", "Assurance report"], "attribution_method": "outstanding / EVIC"},
        {"tier": 2, "label": "Reported, unverified", "criteria": "Company-reported, no assurance",
         "data_sources": ["CDP self-reported", "Refinitiv", "Bloomberg"], "attribution_method": "outstanding / EVIC"},
        {"tier": 3, "label": "Estimated from activity", "criteria": "GHG Protocol + activity data",
         "data_sources": ["Company filings + GHG Protocol EF"], "attribution_method": "outstanding / EVIC"},
        {"tier": 4, "label": "Sector average", "criteria": "EXIOBASE / revenue-based",
         "data_sources": ["EXIOBASE v3", "WIOD"], "attribution_method": "outstanding / EVIC"},
        {"tier": 5, "label": "Country average", "criteria": "Country emission intensity only",
         "data_sources": ["IEA", "OECD STAN"], "attribution_method": "outstanding / EVIC"},
    ],

    # ── PCAF Part B — Business Loans & Unlisted Equity ───────────────────
    "business_loans": [
        {"tier": 1, "label": "Reported, verified by accredited third party",
         "criteria": "Audited sustainability report with reasonable/limited assurance",
         "data_sources": ["Audited ESG report", "CDP A"], "attribution_method": "outstanding / (equity + debt)"},
        {"tier": 2, "label": "Reported, unverified",
         "criteria": "Company sustainability/ESG report without assurance",
         "data_sources": ["Company ESG report", "Client-provided data"], "attribution_method": "outstanding / (equity + debt)"},
        {"tier": 3, "label": "Estimated from company activity",
         "criteria": "Activity data from loan appraisal × GHG Protocol EF",
         "data_sources": ["Loan due diligence data", "BEIS EF", "GHG Protocol"], "attribution_method": "outstanding / (equity + debt)"},
        {"tier": 4, "label": "Sector average per revenue",
         "criteria": "EXIOBASE or SBTi sector intensity × borrower revenue",
         "data_sources": ["EXIOBASE v3", "SBTi sector"], "attribution_method": "outstanding / (equity + debt)"},
        {"tier": 5, "label": "Country/sector fallback",
         "criteria": "No company data available; country × macro sector",
         "data_sources": ["IEA", "OECD STAN", "World Bank EF"], "attribution_method": "outstanding / (equity + debt)"},
    ],

    "unlisted_equity": [
        {"tier": 1, "label": "Reported, verified", "criteria": "Same as business_loans DQS 1",
         "data_sources": ["Audited ESG report"], "attribution_method": "outstanding / EVIC"},
        {"tier": 2, "label": "Reported, unverified", "criteria": "Company sustainability report",
         "data_sources": ["Company ESG report"], "attribution_method": "outstanding / EVIC"},
        {"tier": 3, "label": "Estimated from activity", "criteria": "Activity + GHG Protocol EF",
         "data_sources": ["Due diligence data"], "attribution_method": "outstanding / EVIC"},
        {"tier": 4, "label": "Sector average", "criteria": "EXIOBASE revenue-based",
         "data_sources": ["EXIOBASE v3"], "attribution_method": "outstanding / EVIC"},
        {"tier": 5, "label": "Country average", "criteria": "Country intensity only",
         "data_sources": ["IEA", "World Bank"], "attribution_method": "outstanding / EVIC"},
    ],

    # ── PCAF Part C — Project Finance ─────────────────────────────────────
    "project_finance": [
        {"tier": 1, "label": "Measured/verified project emissions",
         "criteria": "Actual metered emissions from operating project, verified by accredited body",
         "data_sources": ["Project MRV report", "UNFCCC CDM PDD", "Gold Standard MRV"],
         "attribution_method": "outstanding / total_project_cost"},
        {"tier": 2, "label": "Project-specific estimated",
         "criteria": "Project-level activity data × technology EF (IPCC, IEA)",
         "data_sources": ["Project design document", "IPCC EF", "IEA EF"],
         "attribution_method": "outstanding / total_project_cost"},
        {"tier": 3, "label": "Technology-type average",
         "criteria": "Lifecycle EF for technology type (IRENA, IEA)",
         "data_sources": ["IRENA lifecycle EF", "IEA technology EF"],
         "attribution_method": "outstanding / total_project_cost"},
        {"tier": 4, "label": "Sector average",
         "criteria": "EXIOBASE infrastructure sector average × project capex",
         "data_sources": ["EXIOBASE v3"],
         "attribution_method": "outstanding / total_project_cost"},
        {"tier": 5, "label": "Country average",
         "criteria": "Country average intensity only",
         "data_sources": ["IEA", "World Bank"],
         "attribution_method": "outstanding / total_project_cost"},
    ],

    "infrastructure": [
        {"tier": 1, "label": "Measured, verified", "criteria": "Metered operational emissions",
         "data_sources": ["MRV report"], "attribution_method": "outstanding / total_project_cost"},
        {"tier": 2, "label": "Project-specific estimated", "criteria": "Activity × technology EF",
         "data_sources": ["Project data + IPCC EF"], "attribution_method": "outstanding / total_project_cost"},
        {"tier": 3, "label": "Technology-type average", "criteria": "IRENA/IEA lifecycle EF",
         "data_sources": ["IRENA", "IEA"], "attribution_method": "outstanding / total_project_cost"},
        {"tier": 4, "label": "Sector average", "criteria": "EXIOBASE infrastructure",
         "data_sources": ["EXIOBASE v3"], "attribution_method": "outstanding / total_project_cost"},
        {"tier": 5, "label": "Country average", "criteria": "Country intensity only",
         "data_sources": ["IEA", "World Bank"], "attribution_method": "outstanding / total_project_cost"},
    ],

    # ── PCAF Part D — Commercial Real Estate ─────────────────────────────
    "commercial_real_estate": [
        {"tier": 1, "label": "Measured energy consumption",
         "criteria": "Actual meter-read energy (kWh/m²) with verified EF from local grid",
         "data_sources": ["Building energy certificate (EPC)", "Smart meter data", "EPD"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 2, "label": "Estimated from property characteristics",
         "criteria": "Floor area × CRREM benchmark intensity (kWh/m²/yr) for building type + location",
         "data_sources": ["CRREM pathway tool", "Building typology benchmarks"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 3, "label": "Sector average — building type",
         "criteria": "National average EI for building type (office, retail, industrial)",
         "data_sources": ["BPIE EU building stock", "RICS CRE benchmarks"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 4, "label": "Sector average — construction year proxy",
         "criteria": "Age-band average from national building census",
         "data_sources": ["National building census", "EPC national database averages"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 5, "label": "Country average",
         "criteria": "Country/region average only, no asset-level data",
         "data_sources": ["IEA buildings sector", "EU building stock observatory"],
         "attribution_method": "outstanding / property_value"},
    ],

    # ── PCAF Part E — Mortgages ───────────────────────────────────────────
    "mortgages": [
        {"tier": 1, "label": "Actual energy consumption (meter data)",
         "criteria": "Annual meter-read gas + electricity for the dwelling, EPC or smart meter",
         "data_sources": ["Smart meter", "EPC (Energy Performance Certificate)"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 2, "label": "EPC rating",
         "criteria": "EPC label (A to G) with building-type calibration",
         "data_sources": ["National EPC register", "Local authority EPC data"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 3, "label": "Postcode / vintage proxy",
         "criteria": "Postcode-level average EI or construction year band average",
         "data_sources": ["ONS/Eurostat housing stock", "Building Research Establishment"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 4, "label": "Regional average",
         "criteria": "Regional residential average energy intensity",
         "data_sources": ["BPIE regional data", "Eurostat NUTS2 energy"],
         "attribution_method": "outstanding / property_value"},
        {"tier": 5, "label": "National average",
         "criteria": "National residential average — no property-level data",
         "data_sources": ["IEA buildings", "EU building stock observatory"],
         "attribution_method": "outstanding / property_value"},
    ],

    # ── PCAF Part F — Motor Vehicle Loans ────────────────────────────────
    "vehicle_loans": [
        {"tier": 1, "label": "Actual fuel consumption",
         "criteria": "Odometer-verified fuel consumption + IPCC EF",
         "data_sources": ["Fleet telematics", "Fuel card data"],
         "attribution_method": "outstanding / vehicle_value"},
        {"tier": 2, "label": "Reported manufacturer data",
         "criteria": "Manufacturer WLTP/NEDC fuel economy × annual mileage estimate",
         "data_sources": ["WLTP vehicle type approval database", "NEDC data"],
         "attribution_method": "outstanding / vehicle_value"},
        {"tier": 3, "label": "Vehicle type average",
         "criteria": "Vehicle category (PCar/LCV/HGV) × national average mileage + EF",
         "data_sources": ["SMMT vehicle category averages", "ACEA fuel EF"],
         "attribution_method": "outstanding / vehicle_value"},
        {"tier": 4, "label": "National fleet average",
         "criteria": "National average per vehicle type",
         "data_sources": ["IEA road transport EF", "EEA vehicle CO2 database"],
         "attribution_method": "outstanding / vehicle_value"},
        {"tier": 5, "label": "Country transport average",
         "criteria": "Country-level road transport average only",
         "data_sources": ["IEA transport sector", "World Bank"],
         "attribution_method": "outstanding / vehicle_value"},
    ],

    # ── PCAF Part G — Sovereign Bonds ─────────────────────────────────────
    "sovereign_bonds": [
        {"tier": 1, "label": "Official national GHG inventory",
         "criteria": "Country GHG inventory submitted to UNFCCC (Annex I parties)",
         "data_sources": ["UNFCCC national inventory reports", "EEA GHG inventory"],
         "attribution_method": "outstanding / GDP_eur"},
        {"tier": 2, "label": "Satellite/estimation-adjusted inventory",
         "criteria": "UNFCCC inventory adjusted for incompleteness using satellite data",
         "data_sources": ["Global Carbon Project", "Climate TRACE", "EDGAR"],
         "attribution_method": "outstanding / GDP_eur"},
        {"tier": 3, "label": "IEA/EDGAR national dataset",
         "criteria": "IEA World Energy Balances or EDGAR national totals",
         "data_sources": ["IEA World Energy Balances", "JRC EDGAR"],
         "attribution_method": "outstanding / GDP_eur"},
        {"tier": 4, "label": "Regional proxy",
         "criteria": "Regional/continent average scaled by GDP",
         "data_sources": ["World Bank regional EF", "OECD national accounts"],
         "attribution_method": "outstanding / GDP_eur"},
        {"tier": 5, "label": "Global average",
         "criteria": "Global average emission intensity — no country data available",
         "data_sources": ["OWID CO2 global average", "IEA global average"],
         "attribution_method": "outstanding / GDP_eur"},
    ],
}


# ---------------------------------------------------------------------------
# Attribution Factor Guidance Summary (PCAF Standard v2.0)
# ---------------------------------------------------------------------------

ATTRIBUTION_FACTOR_GUIDANCE: Dict[str, Dict] = {
    "listed_equity": {
        "formula": "AF = outstanding_amount / EVIC",
        "denominator": "EVIC = market cap of equity + book value of debt + minority interest",
        "standard_ref": "PCAF Part A §3.2.2",
        "scope_coverage": ["Scope 1", "Scope 2", "Scope 3 (voluntary)"],
        "financed_emissions": "AF × (Scope 1 + Scope 2 [+ Scope 3])",
        "notes": "EVIC must be at the same reporting date as outstanding_amount",
    },
    "corporate_bonds": {
        "formula": "AF = outstanding_amount / EVIC",
        "denominator": "EVIC = same as listed equity",
        "standard_ref": "PCAF Part A §3.2.3",
        "scope_coverage": ["Scope 1", "Scope 2"],
        "financed_emissions": "AF × (Scope 1 + Scope 2)",
        "notes": "Use EVIC not book value of debt. If EVIC unavailable, use total assets.",
    },
    "business_loans": {
        "formula": "AF = outstanding_amount / (total_equity + total_debt)",
        "denominator": "Book value of equity + book value of total debt",
        "standard_ref": "PCAF Part B §4.2.2",
        "scope_coverage": ["Scope 1", "Scope 2"],
        "financed_emissions": "AF × (Scope 1 + Scope 2)",
        "notes": "Use most recent balance sheet. Outstanding = drawn facility amount.",
    },
    "unlisted_equity": {
        "formula": "AF = outstanding_amount / EVIC",
        "denominator": "Fair value of equity + book value of debt",
        "standard_ref": "PCAF Part B §4.2.3",
        "scope_coverage": ["Scope 1", "Scope 2"],
        "financed_emissions": "AF × (Scope 1 + Scope 2)",
        "notes": "Valuation approach consistent with fund NAV methodology",
    },
    "commercial_real_estate": {
        "formula": "AF = outstanding_amount / property_value",
        "denominator": "Current market value of the property",
        "standard_ref": "PCAF Part D §6.2.2",
        "scope_coverage": ["Scope 1", "Scope 2"],
        "financed_emissions": "AF × (operational_emissions_tco2e)",
        "notes": "Operational emissions only (energy). Embodied carbon optional.",
    },
    "mortgages": {
        "formula": "AF = outstanding_amount / property_value",
        "denominator": "Current market value of residential property",
        "standard_ref": "PCAF Part E §7.2.2",
        "scope_coverage": ["Scope 1", "Scope 2"],
        "financed_emissions": "AF × (annual_operational_tco2e)",
        "notes": "Use current valuation, not original purchase price",
    },
    "project_finance": {
        "formula": "AF = outstanding_amount / total_project_cost",
        "denominator": "Total project capital cost at financial close",
        "standard_ref": "PCAF Part C §5.2.2",
        "scope_coverage": ["Scope 1", "Scope 2", "Scope 3 (facilitated)"],
        "financed_emissions": "AF × (annual_project_emissions_tco2e)",
        "notes": "For construction phase: use construction emissions × construction AF",
    },
    "infrastructure": {
        "formula": "AF = outstanding_amount / total_project_cost",
        "denominator": "Total infrastructure asset value",
        "standard_ref": "PCAF Part C §5.2.2 (as extended to infrastructure)",
        "scope_coverage": ["Scope 1", "Scope 2"],
        "financed_emissions": "AF × (annual_operational_emissions_tco2e)",
        "notes": "Same as project finance; include construction emissions during build phase",
    },
    "vehicle_loans": {
        "formula": "AF = outstanding_amount / vehicle_value",
        "denominator": "Current market value of vehicle (not purchase price)",
        "standard_ref": "PCAF Part F §8.2.2",
        "scope_coverage": ["Scope 1", "Scope 2 (TTW)"],
        "financed_emissions": "AF × (annual_vehicle_emissions_tco2e)",
        "notes": "Tank-to-wheel (TTW) approach; well-to-wheel optional for EVs",
    },
    "sovereign_bonds": {
        "formula": "AF = outstanding_amount / GDP_eur",
        "denominator": "Sovereign country GDP in reporting currency",
        "standard_ref": "PCAF Part G §9.2.2",
        "scope_coverage": ["Scope 1", "Scope 2 (production-based)"],
        "financed_emissions": "AF × (national_emissions_tco2e)",
        "notes": "GDP at purchasing power parity (PPP) preferred for comparability",
    },
}


# ---------------------------------------------------------------------------
# Listed Equity DQS Guidance (PCAF Part A §3.2 — expanded)
# ---------------------------------------------------------------------------

LISTED_EQUITY_DQS_GUIDANCE: Dict = {
    "title": "PCAF Part A — Listed Equity Data Quality Scoring Guide",
    "standard_version": "PCAF Global GHG Accounting Standard v2.0 (November 2022)",
    "standard_ref": "Part A §3.2, Annex 2 Table A2.1",
    "scoring_principle": (
        "Score is applied at the investee level. Portfolio-level DQS is the "
        "exposure-weighted average of investee DQS scores (PCAF Standard v2.0 §4.3). "
        "Lower score = higher data quality."
    ),
    "tier_criteria": {
        1: {
            "label": "Verified",
            "emission_source": "Company-reported, independently verified",
            "acceptable_verification": [
                "Reasonable assurance (ISAE 3000 / ISAE 3410)",
                "Limited assurance",
                "CDP A or A- list",
                "EU CSRD regulated assurance (from FY2025 for LAFs)",
            ],
            "data_availability": "Scope 1 + Scope 2 (market-based preferred); Scope 3 optional",
            "key_signal": "Assurance opinion present in annual/sustainability report",
        },
        2: {
            "label": "Reported, no assurance",
            "emission_source": "Company self-reported via CDP, ESG report, or annual report",
            "acceptable_sources": [
                "CDP questionnaire (B or lower)",
                "Company sustainability report without assurance",
                "MSCI ESG Ratings — company-disclosed data",
                "Refinitiv ESG — company-disclosed data",
                "Bloomberg ESG — company-disclosed data",
            ],
            "key_signal": "GHG emissions explicitly stated in company disclosures",
        },
        3: {
            "label": "Estimated from activity",
            "emission_source": "GHG Protocol-based estimation from reported activity data",
            "methodology": "Activity data (energy, production) × IPCC / IEA emission factors",
            "acceptable_sources": ["Company energy consumption data", "Production volume reports"],
            "key_signal": "Activity data available but no direct GHG figure",
        },
        4: {
            "label": "Revenue-based sector average",
            "emission_source": "Sector emission intensity × company revenue",
            "methodology": "EXIOBASE v3 MRIO or WIOD emission intensity (tCO2e / EUR M revenue)",
            "acceptable_sources": ["EXIOBASE v3", "WIOD 2016", "SBTi sector benchmarks"],
            "key_signal": "Only company revenue and sector known; no GHG data",
        },
        5: {
            "label": "Country average fallback",
            "emission_source": "Country emission intensity only",
            "methodology": "National total emissions / GDP × company revenue",
            "acceptable_sources": ["IEA country EF", "OECD STAN", "World Bank EF"],
            "key_signal": "Only country/region and company size known",
        },
    },
    "portfolio_reporting_requirement": (
        "Institutions must report the exposure-weighted portfolio DQS alongside "
        "financed emissions (PCAF Standard §6.3). A portfolio DQS ≤ 2.5 is considered "
        "sufficient for PCAF certification."
    ),
    "improvement_pathway": [
        "Priority 1: Engage top-25 emitters (by financed tCO2e) to obtain verified data → DQS 1",
        "Priority 2: Screen all large caps (>EUR 1bn revenue) for CDP participation → DQS 2",
        "Priority 3: Use MSCI/Refinitiv disclosed-data feed for remaining large caps → DQS 2",
        "Priority 4: Apply EXIOBASE revenue-based for SMEs/unlisted → DQS 4",
        "Priority 5: Avoid DQS 5 for exposures >1% of portfolio AUM",
    ],
}


# ---------------------------------------------------------------------------
# Auto-DQS Derivation
# ---------------------------------------------------------------------------

@dataclass
class DQSDerivationResult:
    """Result of automatic DQS derivation from available data fields."""
    inferred_dqs: int
    confidence: str           # high / medium / low
    rationale: str
    improvement_action: str
    data_signals_found: list[str] = field(default_factory=list)
    data_signals_missing: list[str] = field(default_factory=list)


def derive_dqs(
    asset_class: str,
    has_verified_emissions: bool = False,
    has_reported_emissions: bool = False,
    has_activity_data: bool = False,
    has_revenue: bool = False,
    has_sector_code: bool = True,
    has_country: bool = True,
    assurance_level: Optional[str] = None,  # "reasonable" / "limited" / None
    data_source: Optional[str] = None,       # e.g. "CDP_A", "MSCI", "Bloomberg"
) -> DQSDerivationResult:
    """Automatically derive PCAF DQS from available data signals.

    Intended for use at data-ingestion time to auto-populate `data_quality`
    on `InvesteeData` when no explicit DQS is provided.

    Args:
        asset_class:           One of the PCAFAssetClass values.
        has_verified_emissions: Scope 1+2 present AND verified by 3rd party.
        has_reported_emissions: Scope 1+2 present in company disclosures (unverified).
        has_activity_data:     Energy or production activity data available.
        has_revenue:           Annual revenue available for sector-avg fallback.
        has_sector_code:       NACE/GICS sector code available.
        has_country:           Country ISO available.
        assurance_level:       'reasonable' or 'limited' if has_verified_emissions.
        data_source:           Originating data source string (used for DQS 2 refinement).

    Returns:
        DQSDerivationResult with inferred_dqs (1-5), confidence, and guidance.
    """
    found: list[str] = []
    missing: list[str] = []

    if has_verified_emissions and assurance_level in ("reasonable", "limited"):
        found.append("Verified Scope 1+2 emissions")
        return DQSDerivationResult(
            inferred_dqs=1,
            confidence="high",
            rationale=f"Scope 1+2 verified with {assurance_level} assurance",
            improvement_action="Extend to Scope 3 for higher completeness score",
            data_signals_found=found,
        )

    if has_verified_emissions:
        found.append("Verified emissions (assurance level unknown)")
        return DQSDerivationResult(
            inferred_dqs=1,
            confidence="medium",
            rationale="Verified emissions present but assurance level not specified",
            improvement_action="Confirm assurance level (reasonable vs limited) to lock DQS 1",
            data_signals_found=found,
        )

    if has_reported_emissions:
        found.append("Company-reported emissions (unverified)")
        # Check if source is a tier-2 acceptable provider
        tier2_sources = {"CDP", "CDP_A", "CDP_B", "MSCI", "Refinitiv", "Bloomberg", "ISS ESG"}
        if data_source and any(s in (data_source or "").upper() for s in tier2_sources):
            found.append(f"Recognised data source: {data_source}")
        return DQSDerivationResult(
            inferred_dqs=2,
            confidence="high",
            rationale="Scope 1+2 reported by company, no independent verification",
            improvement_action=(
                "Obtain limited assurance on Scope 1+2 to upgrade to DQS 1. "
                "Check CDP participation for FY reporting."
            ),
            data_signals_found=found,
        )

    if has_activity_data:
        found.append("Activity data (energy/production)")
        missing.append("Direct GHG emissions disclosure")
        return DQSDerivationResult(
            inferred_dqs=3,
            confidence="medium",
            rationale="Emissions estimated from company activity data + GHG Protocol EF",
            improvement_action=(
                "Engage company to disclose direct Scope 1+2 → upgrade to DQS 2. "
                "Cross-check activity estimate against EXIOBASE sector intensity."
            ),
            data_signals_found=found,
            data_signals_missing=missing,
        )

    if has_revenue and has_sector_code:
        found.append("Revenue + sector code available")
        missing.extend(["Scope 1+2 emissions", "Activity data"])
        return DQSDerivationResult(
            inferred_dqs=4,
            confidence="medium",
            rationale="Sector-average emission intensity (EXIOBASE) × revenue",
            improvement_action=(
                "Request CDP questionnaire participation or company ESG report. "
                "For large-cap positions (>1% AUM), escalate to direct engagement."
            ),
            data_signals_found=found,
            data_signals_missing=missing,
        )

    if has_country:
        found.append("Country code available")
        missing.extend(["Scope 1+2 emissions", "Activity data", "Revenue", "Sector code"])
        return DQSDerivationResult(
            inferred_dqs=5,
            confidence="low",
            rationale="Country-average emission intensity only; no company-level data",
            improvement_action=(
                "At minimum obtain sector code to apply EXIOBASE → DQS 4. "
                "Add to data-collection priority list."
            ),
            data_signals_found=found,
            data_signals_missing=missing,
        )

    # No data at all
    missing.extend(["All signals"])
    return DQSDerivationResult(
        inferred_dqs=5,
        confidence="low",
        rationale="No data signals — defaulting to worst-case DQS 5",
        improvement_action="Obtain at minimum country + sector code for DQS 4",
        data_signals_found=found,
        data_signals_missing=missing,
    )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_dqs_tier_table(asset_class: str) -> List[Dict]:
    """Return DQS tier table for a given asset class (5 tiers)."""
    key = asset_class.lower().replace(" ", "_")
    return DQS_TIER_TABLES.get(key, DQS_TIER_TABLES.get("listed_equity", []))


def get_attribution_factor_guidance(asset_class: str) -> Dict:
    """Return AF calculation guidance for a given asset class."""
    key = asset_class.lower().replace(" ", "_")
    return ATTRIBUTION_FACTOR_GUIDANCE.get(key, {})


def get_all_asset_classes() -> List[str]:
    """Return all supported PCAF asset class keys."""
    return list(DQS_TIER_TABLES.keys())
