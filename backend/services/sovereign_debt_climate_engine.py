"""
Climate-Linked Sovereign Debt Engine — E69
Standards: Climate Resilience Debt Clauses (CRDC, Commonwealth Secretariat 2022),
Debt-for-Nature Swaps (DfN, IMF/World Bank 2023), IMF Resilience & Sustainability Trust,
Paris Club MOU on Climate 2021, SIDS Vulnerability Index (UN-OHRLLS),
Catastrophe-Deferred Payment Clauses (CDPC)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import random
import math

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

SIDS_LIST: Dict[str, Dict] = {
    "ATG": {"name": "Antigua and Barbuda", "vulnerability_score": 0.78, "region": "Caribbean", "gdp_usd_bn": 1.7},
    "BHS": {"name": "Bahamas", "vulnerability_score": 0.71, "region": "Caribbean", "gdp_usd_bn": 12.0},
    "BRB": {"name": "Barbados", "vulnerability_score": 0.74, "region": "Caribbean", "gdp_usd_bn": 5.0},
    "BLZ": {"name": "Belize", "vulnerability_score": 0.70, "region": "Caribbean", "gdp_usd_bn": 2.5},
    "COM": {"name": "Comoros", "vulnerability_score": 0.85, "region": "Indian Ocean", "gdp_usd_bn": 1.3},
    "CPV": {"name": "Cape Verde", "vulnerability_score": 0.76, "region": "Atlantic", "gdp_usd_bn": 2.0},
    "CUB": {"name": "Cuba", "vulnerability_score": 0.62, "region": "Caribbean", "gdp_usd_bn": 107.0},
    "DMA": {"name": "Dominica", "vulnerability_score": 0.82, "region": "Caribbean", "gdp_usd_bn": 0.6},
    "DOM": {"name": "Dominican Republic", "vulnerability_score": 0.65, "region": "Caribbean", "gdp_usd_bn": 94.0},
    "FJI": {"name": "Fiji", "vulnerability_score": 0.77, "region": "Pacific", "gdp_usd_bn": 4.6},
    "GRD": {"name": "Grenada", "vulnerability_score": 0.79, "region": "Caribbean", "gdp_usd_bn": 1.2},
    "GNB": {"name": "Guinea-Bissau", "vulnerability_score": 0.88, "region": "Atlantic", "gdp_usd_bn": 1.7},
    "GUY": {"name": "Guyana", "vulnerability_score": 0.68, "region": "Caribbean", "gdp_usd_bn": 15.0},
    "HTI": {"name": "Haiti", "vulnerability_score": 0.92, "region": "Caribbean", "gdp_usd_bn": 21.0},
    "JAM": {"name": "Jamaica", "vulnerability_score": 0.72, "region": "Caribbean", "gdp_usd_bn": 17.0},
    "KIR": {"name": "Kiribati", "vulnerability_score": 0.95, "region": "Pacific", "gdp_usd_bn": 0.2},
    "MDV": {"name": "Maldives", "vulnerability_score": 0.90, "region": "Indian Ocean", "gdp_usd_bn": 5.7},
    "MHL": {"name": "Marshall Islands", "vulnerability_score": 0.93, "region": "Pacific", "gdp_usd_bn": 0.3},
    "MUS": {"name": "Mauritius", "vulnerability_score": 0.60, "region": "Indian Ocean", "gdp_usd_bn": 13.0},
    "FSM": {"name": "Micronesia", "vulnerability_score": 0.87, "region": "Pacific", "gdp_usd_bn": 0.4},
    "NRU": {"name": "Nauru", "vulnerability_score": 0.85, "region": "Pacific", "gdp_usd_bn": 0.1},
    "NIU": {"name": "Niue", "vulnerability_score": 0.82, "region": "Pacific", "gdp_usd_bn": 0.02},
    "PLW": {"name": "Palau", "vulnerability_score": 0.80, "region": "Pacific", "gdp_usd_bn": 0.3},
    "PNG": {"name": "Papua New Guinea", "vulnerability_score": 0.75, "region": "Pacific", "gdp_usd_bn": 30.0},
    "LCA": {"name": "Saint Lucia", "vulnerability_score": 0.78, "region": "Caribbean", "gdp_usd_bn": 2.3},
    "VCT": {"name": "Saint Vincent & Grenadines", "vulnerability_score": 0.80, "region": "Caribbean", "gdp_usd_bn": 0.9},
    "WSM": {"name": "Samoa", "vulnerability_score": 0.81, "region": "Pacific", "gdp_usd_bn": 0.8},
    "STP": {"name": "Sao Tome & Principe", "vulnerability_score": 0.84, "region": "Atlantic", "gdp_usd_bn": 0.5},
    "SYC": {"name": "Seychelles", "vulnerability_score": 0.65, "region": "Indian Ocean", "gdp_usd_bn": 1.6},
    "SLB": {"name": "Solomon Islands", "vulnerability_score": 0.88, "region": "Pacific", "gdp_usd_bn": 1.6},
    "SUR": {"name": "Suriname", "vulnerability_score": 0.70, "region": "Caribbean", "gdp_usd_bn": 3.6},
    "TLS": {"name": "Timor-Leste", "vulnerability_score": 0.80, "region": "Pacific", "gdp_usd_bn": 3.1},
    "TON": {"name": "Tonga", "vulnerability_score": 0.86, "region": "Pacific", "gdp_usd_bn": 0.5},
    "TTO": {"name": "Trinidad and Tobago", "vulnerability_score": 0.58, "region": "Caribbean", "gdp_usd_bn": 23.0},
    "TUV": {"name": "Tuvalu", "vulnerability_score": 0.97, "region": "Pacific", "gdp_usd_bn": 0.06},
    "VUT": {"name": "Vanuatu", "vulnerability_score": 0.89, "region": "Pacific", "gdp_usd_bn": 1.0},
    "VEN": {"name": "Venezuela", "vulnerability_score": 0.68, "region": "Caribbean", "gdp_usd_bn": 98.0},
    "MDG": {"name": "Madagascar", "vulnerability_score": 0.83, "region": "Indian Ocean", "gdp_usd_bn": 15.0},
    "MOZ": {"name": "Mozambique", "vulnerability_score": 0.86, "region": "Indian Ocean", "gdp_usd_bn": 16.0},
}

IMF_RST_ELIGIBILITY: Dict[str, Dict] = {
    "BHS": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "BRB": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "CRI": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "ECU": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": False},
    "EGY": {"access_limit_pct_quota": 150, "reform_area": "energy_transition", "approved": True},
    "FJI": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "GHA": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": False},
    "JAM": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "KEN": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "MDV": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "MAR": {"access_limit_pct_quota": 150, "reform_area": "energy_transition", "approved": True},
    "MUS": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "MNG": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": False},
    "NIC": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": False},
    "NGA": {"access_limit_pct_quota": 150, "reform_area": "energy_transition", "approved": False},
    "PAK": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "PNG": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": False},
    "PHL": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "RWA": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "SEN": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "LCA": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "TZA": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "TTO": {"access_limit_pct_quota": 150, "reform_area": "energy_transition", "approved": True},
    "UGA": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "URY": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": True},
    "ZMB": {"access_limit_pct_quota": 150, "reform_area": "climate_resilience", "approved": False},
}

CRDC_TRIGGER_TYPES: Dict[str, Dict] = {
    "cyclone_wind_speed": {
        "description": "Tropical cyclone maximum sustained wind speed",
        "unit": "km/h",
        "typical_threshold": 119,  # Category 1 threshold
        "deferred_period_months": 24,
        "source": "WMO / National Met Services",
        "basis_risk": "low",
    },
    "rainfall_deficit": {
        "description": "Cumulative rainfall below seasonal mean (drought trigger)",
        "unit": "mm",
        "typical_threshold": -30,  # 30% below seasonal mean
        "deferred_period_months": 12,
        "source": "CHIRPS / GPCP satellite data",
        "basis_risk": "medium",
    },
    "temperature_anomaly": {
        "description": "Annual average temperature deviation above baseline",
        "unit": "degrees_C",
        "typical_threshold": 1.5,
        "deferred_period_months": 12,
        "source": "HadCRUT5 / NOAA",
        "basis_risk": "medium",
    },
    "sea_level": {
        "description": "Annual mean sea level above pre-industrial baseline",
        "unit": "cm",
        "typical_threshold": 20,
        "deferred_period_months": 36,
        "source": "PSMSL tide gauge / satellite altimetry",
        "basis_risk": "low",
    },
    "drought_index": {
        "description": "Standardised Precipitation-Evapotranspiration Index (SPEI-12)",
        "unit": "SPEI_score",
        "typical_threshold": -1.5,  # Severe drought
        "deferred_period_months": 18,
        "source": "Global Drought Observatory",
        "basis_risk": "medium-high",
    },
}

DFN_SWAP_FRAMEWORKS: Dict[str, Dict] = {
    "bilateral": {
        "description": "Creditor government to debtor swap with conservation earmark",
        "precedents": ["Seychelles 2016 (TNC/NatWest)", "Belize 2021 (TNC)"],
        "discount_range_pct": [15, 40],
        "conservation_commitment_min_pct_gdp": 1.0,
        "mdb_involvement": False,
        "typical_size_usd_mn": [50, 500],
        "carbon_credit_linkage": False,
    },
    "multilateral": {
        "description": "IMF/World Bank facilitated swap with policy conditionality",
        "precedents": ["Ecuador 2023 (Galapagos)", "Sri Lanka ongoing"],
        "discount_range_pct": [20, 50],
        "conservation_commitment_min_pct_gdp": 1.5,
        "mdb_involvement": True,
        "typical_size_usd_mn": [200, 2000],
        "carbon_credit_linkage": True,
    },
    "commercial": {
        "description": "Commercial bank debt restructured through conservation trust",
        "precedents": ["Seychelles 2015 (DBSA)"],
        "discount_range_pct": [10, 25],
        "conservation_commitment_min_pct_gdp": 0.5,
        "mdb_involvement": False,
        "typical_size_usd_mn": [20, 200],
        "carbon_credit_linkage": False,
    },
    "paris_club": {
        "description": "Paris Club bilateral creditor group climate MOU debt treatment",
        "precedents": ["MOU on Climate 2021 (G7)"],
        "discount_range_pct": [5, 20],
        "conservation_commitment_min_pct_gdp": 0.5,
        "mdb_involvement": True,
        "typical_size_usd_mn": [100, 5000],
        "carbon_credit_linkage": True,
    },
}

PARIS_CLUB_CATEGORIES: Dict[str, Dict] = {
    "poorest": {
        "description": "IDA-eligible, HIPC countries — most concessional treatment",
        "per_capita_gni_threshold_usd": 1135,
        "debt_service_relief_pct": 90,
        "climate_conditionality": "NDC_update + NbS_commitment",
        "cutoff_date_policy": "pre_cutoff_only",
    },
    "vulnerable_middle_income": {
        "description": "Middle income with high climate vulnerability (MVI or SIDS)",
        "per_capita_gni_threshold_usd": 4465,
        "debt_service_relief_pct": 50,
        "climate_conditionality": "CRDC_incorporation + climate_action_plan",
        "cutoff_date_policy": "case_by_case",
    },
    "standard": {
        "description": "Standard Paris Club debtor terms with climate addendum",
        "per_capita_gni_threshold_usd": 99999,
        "debt_service_relief_pct": 20,
        "climate_conditionality": "voluntary_CRDC",
        "cutoff_date_policy": "post_cutoff_eligible",
    },
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CRDCAssessment:
    country_iso: str
    country_name: str
    debt_amount_usd: float
    crdc_eligible: bool
    trigger_type: str
    trigger_threshold: float
    trigger_probability_pct: float
    deferred_amount_usd: float
    deferred_period_months: int
    basis_risk_rating: str
    climate_event_return_period_years: float
    debt_relief_score: float
    implementation_cost_usd: float
    recommendations: List[str]


@dataclass
class DebtForNatureResult:
    country_iso: str
    country_name: str
    total_debt_usd: float
    swap_framework: str
    swap_amount_usd: float
    discount_pct: float
    conservation_fund_usd: float
    conservation_commitment_text: str
    co2_sequestration_tco2_yr: float
    mdb_guarantee_usd: float
    carbon_credit_revenue_usd_yr: float
    biodiversity_targets: List[str]
    imf_rst_linkage: bool
    net_debt_reduction_usd: float


@dataclass
class IMFRSTAssessment:
    country_iso: str
    rst_eligible: bool
    access_limit_pct_quota: float
    reform_area: str
    resilience_score: float
    reform_measures: List[str]
    indicative_drawing_usd: float
    conditionality_met: bool
    disbursement_timeline: str


@dataclass
class SIDSVulnerabilityResult:
    country_iso: str
    country_name: str
    vulnerability_score: float
    vulnerability_tier: str  # critical | high | medium
    inform_component: float
    nd_gain_component: float
    fiscal_resilience_component: float
    cdpc_eligible: bool
    cdpc_deferred_pct: float
    paris_club_category: str
    climate_debt_relief_score: float
    priority_interventions: List[str]


@dataclass
class SovereignClimatePortfolioResult:
    portfolio_id: str
    total_sovereign_exposure_usd: float
    climate_adjusted_exposure_usd: float
    weighted_vulnerability_score: float
    weighted_debt_relief_score: float
    crdc_eligible_exposure_usd: float
    dfn_eligible_exposure_usd: float
    sids_exposure_pct: float
    high_risk_country_concentration: float
    portfolio_climate_var_usd: float
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Engine Functions
# ---------------------------------------------------------------------------

def assess_crdc_eligibility(country_data: Dict[str, Any], debt_terms: Dict[str, Any]) -> CRDCAssessment:
    """Assess eligibility and design of Climate Resilience Debt Clauses."""
    country_iso = country_data.get("country_iso", "MDV")
    rng = random.Random(hash(str(country_iso)) & 0xFFFFFFFF)

    country_name = country_data.get("country_name", SIDS_LIST.get(country_iso, {}).get("name", country_iso))
    debt_amount = float(debt_terms.get("debt_amount_usd", rng.uniform(1e8, 5e9)))
    trigger_type = debt_terms.get("trigger_type", "cyclone_wind_speed")
    if trigger_type not in CRDC_TRIGGER_TYPES:
        trigger_type = "cyclone_wind_speed"

    trigger_info = CRDC_TRIGGER_TYPES[trigger_type]
    trigger_threshold = float(debt_terms.get("trigger_threshold", trigger_info["typical_threshold"]))

    # Climate event probability based on vulnerability
    vuln_score = SIDS_LIST.get(country_iso, {}).get("vulnerability_score", 0.70)
    return_period = rng.uniform(5, 25) * (1 - vuln_score + 0.2)
    trigger_prob_pct = round(100 / return_period, 2)

    # Deferred amount: typically 20-40% of annual debt service
    annual_debt_service = debt_amount * rng.uniform(0.04, 0.08)
    deferred_pct = rng.uniform(0.20, 0.40)
    deferred_amount = annual_debt_service * deferred_pct * trigger_info["deferred_period_months"] / 12

    # CRDC eligibility: climate-vulnerable countries with Commonwealth/bilateral creditors
    is_eligible = (
        country_iso in SIDS_LIST
        or vuln_score >= 0.65
        or country_data.get("is_sids", False)
        or country_data.get("is_ldc", False)
    )

    debt_relief_score = round(min(1.0, vuln_score * 0.6 + (deferred_pct) * 0.4), 4)
    implementation_cost = debt_amount * rng.uniform(0.001, 0.005)  # legal/structuring cost

    recommendations = []
    if not is_eligible:
        recommendations.append("Country does not meet CRDC eligibility; consider standard CDPC")
    if return_period > 20:
        recommendations.append(f"Long return period ({return_period:.1f} yr) — consider dual-trigger design")
    if trigger_info["basis_risk"] in ["medium", "medium-high"]:
        recommendations.append(f"Mitigate {trigger_info['basis_risk']} basis risk with parametric index verification")
    recommendations.append(f"Incorporate {trigger_type} trigger at {trigger_threshold} threshold per Commonwealth Secretariat CRDC template")

    return CRDCAssessment(
        country_iso=country_iso,
        country_name=country_name,
        debt_amount_usd=round(debt_amount, 2),
        crdc_eligible=is_eligible,
        trigger_type=trigger_type,
        trigger_threshold=trigger_threshold,
        trigger_probability_pct=trigger_prob_pct,
        deferred_amount_usd=round(deferred_amount, 2),
        deferred_period_months=trigger_info["deferred_period_months"],
        basis_risk_rating=trigger_info["basis_risk"],
        climate_event_return_period_years=round(return_period, 1),
        debt_relief_score=debt_relief_score,
        implementation_cost_usd=round(implementation_cost, 2),
        recommendations=recommendations,
    )


def assess_debt_for_nature(country_data: Dict[str, Any], deal_terms: Dict[str, Any]) -> DebtForNatureResult:
    """Assess and design a Debt-for-Nature swap transaction."""
    country_iso = country_data.get("country_iso", "SYC")
    rng = random.Random(hash(str(country_iso) + "dfn") & 0xFFFFFFFF)

    country_name = country_data.get("country_name", SIDS_LIST.get(country_iso, {}).get("name", country_iso))
    total_debt = float(deal_terms.get("total_eligible_debt_usd", rng.uniform(5e8, 5e9)))
    framework = deal_terms.get("swap_framework", "multilateral")
    if framework not in DFN_SWAP_FRAMEWORKS:
        framework = "multilateral"
    fw = DFN_SWAP_FRAMEWORKS[framework]

    discount_pct = rng.uniform(fw["discount_range_pct"][0], fw["discount_range_pct"][1])
    swap_amount = total_debt * rng.uniform(0.05, 0.20)
    conservation_fund = swap_amount * (discount_pct / 100)

    gdp = SIDS_LIST.get(country_iso, {}).get("gdp_usd_bn", 5.0) * 1e9
    commitment_pct_gdp = conservation_fund / gdp * 100

    co2_seq = conservation_fund / 1e6 * rng.uniform(50, 200)  # rough conversion
    mdb_guarantee = conservation_fund * rng.uniform(0.3, 0.7) if fw["mdb_involvement"] else 0
    carbon_revenue = co2_seq * rng.uniform(10, 30) if fw["carbon_credit_linkage"] else 0

    biodiversity_targets = [
        "30x30 Kunming-Montreal MPA target coverage",
        f"Protect {rng.randint(50, 200)}k ha marine and terrestrial habitat",
        "Restore degraded mangrove/coral reef ecosystems",
        "Eliminate IUU fishing in EEZ within 5 years",
    ]

    imf_rst_linked = country_iso in IMF_RST_ELIGIBILITY and IMF_RST_ELIGIBILITY[country_iso]["approved"]

    return DebtForNatureResult(
        country_iso=country_iso,
        country_name=country_name,
        total_debt_usd=round(total_debt, 2),
        swap_framework=framework,
        swap_amount_usd=round(swap_amount, 2),
        discount_pct=round(discount_pct, 2),
        conservation_fund_usd=round(conservation_fund, 2),
        conservation_commitment_text=(
            f"Commit {commitment_pct_gdp:.2f}% of GDP to conservation per {fw['description']}"
        ),
        co2_sequestration_tco2_yr=round(co2_seq, 2),
        mdb_guarantee_usd=round(mdb_guarantee, 2),
        carbon_credit_revenue_usd_yr=round(carbon_revenue, 2),
        biodiversity_targets=biodiversity_targets,
        imf_rst_linkage=imf_rst_linked,
        net_debt_reduction_usd=round(swap_amount * discount_pct / 100, 2),
    )


def assess_imf_rst(country_data: Dict[str, Any]) -> IMFRSTAssessment:
    """Assess IMF Resilience and Sustainability Trust access and reform requirements."""
    country_iso = country_data.get("country_iso", "JAM")
    rng = random.Random(hash(str(country_iso) + "rst") & 0xFFFFFFFF)

    rst_info = IMF_RST_ELIGIBILITY.get(country_iso)
    is_eligible = rst_info is not None
    access_limit = rst_info["access_limit_pct_quota"] if rst_info else 0
    reform_area = rst_info["reform_area"] if rst_info else "not_eligible"

    # Resilience score: proxy for RST scoring
    vuln = SIDS_LIST.get(country_iso, {}).get("vulnerability_score", 0.60)
    resilience_score = round(rng.uniform(0.40, 0.75) + vuln * 0.15, 4)

    quota_usd = float(country_data.get("imf_quota_usd", rng.uniform(5e8, 5e9)))
    indicative_drawing = quota_usd * access_limit / 100

    reform_measures = []
    if reform_area == "climate_resilience":
        reform_measures = [
            "Develop and implement National Adaptation Plan aligned with IPCC AR6",
            "Establish climate contingency fund (>=2% GDP)",
            "Reform disaster risk management legislation",
            "Carbon pricing mechanism or equivalent fiscal instrument",
        ]
    elif reform_area == "energy_transition":
        reform_measures = [
            "Renewable energy target >=40% by 2030",
            "Fossil fuel subsidy reform with social protection safeguards",
            "Grid modernisation investment plan",
            "Green hydrogen feasibility study",
        ]
    else:
        reform_measures = ["Country not currently RST-eligible; engage IMF Article IV dialogue"]

    conditionality_met = is_eligible and rst_info.get("approved", False) and resilience_score >= 0.55

    return IMFRSTAssessment(
        country_iso=country_iso,
        rst_eligible=is_eligible,
        access_limit_pct_quota=access_limit,
        reform_area=reform_area,
        resilience_score=resilience_score,
        reform_measures=reform_measures,
        indicative_drawing_usd=round(indicative_drawing, 2),
        conditionality_met=conditionality_met,
        disbursement_timeline="12-18 months from LOI submission" if conditionality_met else "Not currently eligible",
    )


def assess_sids_vulnerability(country_iso: str) -> SIDSVulnerabilityResult:
    """Assess SIDS vulnerability and CDPC eligibility using composite index."""
    rng = random.Random(hash(str(country_iso) + "sids") & 0xFFFFFFFF)

    sids_data = SIDS_LIST.get(country_iso)
    if not sids_data:
        return SIDSVulnerabilityResult(
            country_iso=country_iso,
            country_name=country_iso,
            vulnerability_score=0.0,
            vulnerability_tier="not_sids",
            inform_component=0.0,
            nd_gain_component=0.0,
            fiscal_resilience_component=0.0,
            cdpc_eligible=False,
            cdpc_deferred_pct=0.0,
            paris_club_category="standard",
            climate_debt_relief_score=0.0,
            priority_interventions=[],
        )

    vuln = sids_data["vulnerability_score"]
    inform = round(rng.uniform(vuln - 0.1, vuln + 0.05), 4)
    nd_gain = round(rng.uniform(0.3, 0.7) * (1 - vuln), 4)  # lower ND-GAIN for more vulnerable
    gdp = sids_data["gdp_usd_bn"]
    fiscal_res = round(rng.uniform(0.2, 0.6) * (1 - vuln) + (0.05 if gdp < 5 else 0.15), 4)

    composite = round(inform * 0.35 + (1 - nd_gain) * 0.35 + (1 - fiscal_res) * 0.30, 4)

    if composite >= 0.75:
        tier = "critical"
        cdpc_deferred = 40.0
    elif composite >= 0.55:
        tier = "high"
        cdpc_deferred = 25.0
    else:
        tier = "medium"
        cdpc_deferred = 10.0

    cdpc_eligible = composite >= 0.55
    gdp_per_capita = gdp * 1e9 / rng.randint(50_000, 3_000_000)
    paris_cat = (
        "poorest" if gdp_per_capita < PARIS_CLUB_CATEGORIES["poorest"]["per_capita_gni_threshold_usd"]
        else "vulnerable_middle_income" if gdp_per_capita < PARIS_CLUB_CATEGORIES["vulnerable_middle_income"]["per_capita_gni_threshold_usd"]
        else "standard"
    )

    relief_score = round(composite * 0.6 + (cdpc_deferred / 40) * 0.4, 4)

    interventions = []
    if fiscal_res < 0.35:
        interventions.append("Establish climate contingency fund (IMF RST Article IV recommendation)")
    if inform > 0.75:
        interventions.append("Priority access to FRLD/Global Shield financing instruments")
    if nd_gain < 0.40:
        interventions.append("ND-GAIN adaptation readiness investment — governance and infrastructure")
    if cdpc_eligible:
        interventions.append(f"Incorporate CDPC in {cdpc_deferred}% of new bilateral debt instruments")

    return SIDSVulnerabilityResult(
        country_iso=country_iso,
        country_name=sids_data["name"],
        vulnerability_score=round(composite, 4),
        vulnerability_tier=tier,
        inform_component=round(inform, 4),
        nd_gain_component=round(nd_gain, 4),
        fiscal_resilience_component=round(fiscal_res, 4),
        cdpc_eligible=cdpc_eligible,
        cdpc_deferred_pct=cdpc_deferred,
        paris_club_category=paris_cat,
        climate_debt_relief_score=round(relief_score, 4),
        priority_interventions=interventions,
    )


def aggregate_sovereign_climate_portfolio(holdings: List[Dict[str, Any]]) -> SovereignClimatePortfolioResult:
    """Aggregate climate-linked sovereign debt metrics across a portfolio of sovereign holdings."""
    portfolio_id = "portfolio_default"
    if holdings:
        portfolio_id = str(hash(tuple(h.get("country_iso", "") for h in holdings)) & 0xFFFFFFFF)
    rng = random.Random(hash(portfolio_id) & 0xFFFFFFFF)

    total_exposure = sum(float(h.get("exposure_usd", 0)) for h in holdings)
    if total_exposure == 0:
        total_exposure = rng.uniform(1e9, 5e10)

    weighted_vuln = 0.0
    weighted_relief = 0.0
    crdc_eligible = 0.0
    dfn_eligible = 0.0
    sids_exposure = 0.0
    high_risk_exposure = 0.0

    for h in holdings:
        iso = h.get("country_iso", "")
        exp = float(h.get("exposure_usd", 0))
        w = exp / total_exposure
        sids_data = SIDS_LIST.get(iso)

        vuln = sids_data["vulnerability_score"] if sids_data else rng.uniform(0.3, 0.7)
        weighted_vuln += vuln * w

        relief = min(1.0, vuln * 0.7 + rng.uniform(0, 0.2))
        weighted_relief += relief * w

        if sids_data or vuln >= 0.65:
            crdc_eligible += exp * 0.6
            dfn_eligible += exp * 0.3
        if sids_data:
            sids_exposure += exp
        if vuln >= 0.80:
            high_risk_exposure += exp

    climate_adjusted = total_exposure * (1 - weighted_vuln * 0.15)
    climate_var = total_exposure * weighted_vuln * rng.uniform(0.05, 0.15)

    recommendations = []
    if sids_exposure / total_exposure > 0.30:
        recommendations.append("High SIDS concentration — diversify or hedge with catastrophe instruments")
    if crdc_eligible / total_exposure > 0.50:
        recommendations.append("Proactively incorporate CRDC clauses in primary market issuance")
    if weighted_vuln > 0.70:
        recommendations.append("Portfolio-level vulnerability above threshold — engage Paris Club MOU")
    if dfn_eligible > 5e8:
        recommendations.append(f"USD {dfn_eligible/1e6:.0f}M eligible for Debt-for-Nature structuring")

    return SovereignClimatePortfolioResult(
        portfolio_id=portfolio_id,
        total_sovereign_exposure_usd=round(total_exposure, 2),
        climate_adjusted_exposure_usd=round(climate_adjusted, 2),
        weighted_vulnerability_score=round(weighted_vuln, 4),
        weighted_debt_relief_score=round(weighted_relief, 4),
        crdc_eligible_exposure_usd=round(crdc_eligible, 2),
        dfn_eligible_exposure_usd=round(dfn_eligible, 2),
        sids_exposure_pct=round(sids_exposure / total_exposure * 100, 2) if total_exposure else 0,
        high_risk_country_concentration=round(high_risk_exposure / total_exposure, 4) if total_exposure else 0,
        portfolio_climate_var_usd=round(climate_var, 2),
        recommendations=recommendations,
    )
