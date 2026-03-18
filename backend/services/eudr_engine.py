"""
EU Deforestation Regulation (EUDR) 2023/1115 — Compliance Engine
=================================================================
Full due diligence, traceability, and compliance assessment engine for
Regulation (EU) 2023/1115 on deforestation-free supply chains.

Sub-modules:
  1. Due Diligence Assessment — Articles 4-12 operator/trader obligations
  2. Commodity Screening — Annex I commodity scope & HS/CN code verification
  3. Country Risk Classification — Article 29 three-tier benchmarking
  4. Traceability Verification — Article 9 geolocation & supply chain mapping
  5. Compliance Gap Analysis — Evidence-based gap scoring with remediation plans
  6. Due Diligence Statement — Article 4(2) statement generation
  7. Cross-Framework Linkage — CSRD ESRS E4, EU Taxonomy biodiversity DNSH

References:
  - Regulation (EU) 2023/1115 (Deforestation-free products)
  - Commission Implementing Regulation (EU) 2025/1093 (country benchmarking)
  - Annex I — Relevant commodities and derived products
  - EC FAQ — EUDR implementation guidance (Dec 2024)
  - ESRS E4 — Biodiversity and ecosystems (cross-reference)
  - EU Taxonomy — Biodiversity DNSH criteria (cross-reference)

Enforcement timeline:
  - 30 Jun 2023: Entry into force
  - 30 Dec 2024: Application date for large operators/traders (deferred to 30 Dec 2025)
  - 30 Jun 2025: Application date for SMEs (deferred to 30 Jun 2026)
  - Ongoing: Country benchmarking updates by European Commission
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — 7 EUDR Commodities (Annex I)
# ---------------------------------------------------------------------------

EUDR_COMMODITIES: dict[str, dict] = {
    "cattle": {
        "description": "Cattle (live animals and derived products)",
        "hs_chapters": ["0102", "0201", "0202", "4101", "4104", "4107"],
        "derived_products": ["beef", "leather", "tallow", "gelatin"],
        "deforestation_cutoff": "2020-12-31",
        "degradation_included": True,
    },
    "cocoa": {
        "description": "Cocoa beans and derived products",
        "hs_chapters": ["1801", "1802", "1803", "1804", "1805", "1806"],
        "derived_products": ["cocoa_butter", "cocoa_powder", "chocolate"],
        "deforestation_cutoff": "2020-12-31",
        "degradation_included": True,
    },
    "coffee": {
        "description": "Coffee beans and derived products",
        "hs_chapters": ["0901", "2101"],
        "derived_products": ["roasted_coffee", "instant_coffee", "coffee_extract"],
        "deforestation_cutoff": "2020-12-31",
        "degradation_included": True,
    },
    "oil_palm": {
        "description": "Oil palm fruit and derived products",
        "hs_chapters": ["1207", "1511", "1513", "3823", "3826"],
        "derived_products": ["palm_oil", "palm_kernel_oil", "oleochemicals", "biodiesel"],
        "deforestation_cutoff": "2020-12-31",
        "degradation_included": True,
    },
    "rubber": {
        "description": "Natural rubber and derived products",
        "hs_chapters": ["4001", "4005", "4006", "4007", "4008", "4011", "4012", "4013"],
        "derived_products": ["natural_rubber", "latex", "tyres"],
        "deforestation_cutoff": "2020-12-31",
        "degradation_included": True,
    },
    "soya": {
        "description": "Soybeans and derived products",
        "hs_chapters": ["1201", "1208", "1507", "2304"],
        "derived_products": ["soybean_oil", "soy_meal", "soy_flour", "soy_protein"],
        "deforestation_cutoff": "2020-12-31",
        "degradation_included": True,
    },
    "wood": {
        "description": "Wood and derived products (incl. printed paper, charcoal)",
        "hs_chapters": ["4401", "4403", "4406", "4407", "4408", "4409", "4410",
                         "4411", "4412", "4418", "4421", "4707", "4801", "4802",
                         "4803", "4804", "4805", "4806", "4807", "4808", "4809",
                         "4810", "4811", "4813", "4814", "4817", "4818", "4819",
                         "4820", "4821", "4823", "9403"],
        "derived_products": ["timber", "plywood", "pulp", "paper", "charcoal",
                             "furniture", "printed_paper"],
        "deforestation_cutoff": "2020-12-31",
        "degradation_included": True,  # Only for wood: degradation also covered
    },
}


# ---------------------------------------------------------------------------
# Reference Data — Country Risk Benchmarking (Article 29)
# Source: Commission Implementing Regulation (EU) 2025/1093
# ---------------------------------------------------------------------------

COUNTRY_RISK_TIERS: dict[str, dict] = {
    # HIGH RISK — Enhanced due diligence required (Art 10(2))
    "BR": {"tier": "high",     "name": "Brazil",             "commodities": ["soya", "cattle", "coffee", "wood", "cocoa"]},
    "ID": {"tier": "high",     "name": "Indonesia",          "commodities": ["oil_palm", "rubber", "wood", "cocoa", "coffee"]},
    "MY": {"tier": "high",     "name": "Malaysia",           "commodities": ["oil_palm", "rubber", "wood"]},
    "CD": {"tier": "high",     "name": "DR Congo",           "commodities": ["wood", "cocoa", "rubber", "coffee"]},
    "CO": {"tier": "high",     "name": "Colombia",           "commodities": ["coffee", "oil_palm", "cattle", "cocoa"]},
    "PY": {"tier": "high",     "name": "Paraguay",           "commodities": ["soya", "cattle", "wood"]},
    "BO": {"tier": "high",     "name": "Bolivia",            "commodities": ["soya", "cattle", "wood"]},
    "PE": {"tier": "high",     "name": "Peru",               "commodities": ["coffee", "cocoa", "wood", "oil_palm"]},
    "MM": {"tier": "high",     "name": "Myanmar",            "commodities": ["rubber", "wood"]},
    "CG": {"tier": "high",     "name": "Congo Republic",     "commodities": ["wood", "cocoa"]},
    "CM": {"tier": "high",     "name": "Cameroon",           "commodities": ["cocoa", "wood", "rubber", "oil_palm"]},
    "NG": {"tier": "high",     "name": "Nigeria",            "commodities": ["cocoa", "oil_palm", "rubber", "wood"]},
    "GH": {"tier": "high",     "name": "Ghana",              "commodities": ["cocoa", "wood"]},
    "CI": {"tier": "high",     "name": "Cote d'Ivoire",      "commodities": ["cocoa", "rubber", "oil_palm", "coffee"]},
    "LA": {"tier": "high",     "name": "Laos",               "commodities": ["rubber", "wood", "coffee"]},
    "PG": {"tier": "high",     "name": "Papua New Guinea",   "commodities": ["oil_palm", "wood", "cocoa", "coffee"]},
    "MG": {"tier": "high",     "name": "Madagascar",         "commodities": ["wood", "cocoa", "coffee"]},

    # STANDARD RISK — Normal due diligence (Art 10(1))
    "AR": {"tier": "standard", "name": "Argentina",          "commodities": ["soya", "cattle", "wood"]},
    "VN": {"tier": "standard", "name": "Vietnam",            "commodities": ["coffee", "rubber", "wood"]},
    "TH": {"tier": "standard", "name": "Thailand",           "commodities": ["rubber", "oil_palm", "wood"]},
    "IN": {"tier": "standard", "name": "India",              "commodities": ["coffee", "rubber", "wood", "soya"]},
    "CN": {"tier": "standard", "name": "China",              "commodities": ["wood", "rubber", "soya"]},
    "EC": {"tier": "standard", "name": "Ecuador",            "commodities": ["cocoa", "coffee", "oil_palm", "wood"]},
    "HN": {"tier": "standard", "name": "Honduras",           "commodities": ["coffee", "oil_palm", "cocoa"]},
    "GT": {"tier": "standard", "name": "Guatemala",          "commodities": ["coffee", "oil_palm", "rubber"]},
    "UG": {"tier": "standard", "name": "Uganda",             "commodities": ["coffee", "cocoa", "wood"]},
    "ET": {"tier": "standard", "name": "Ethiopia",           "commodities": ["coffee", "wood"]},
    "TZ": {"tier": "standard", "name": "Tanzania",           "commodities": ["coffee", "cocoa", "wood"]},
    "KE": {"tier": "standard", "name": "Kenya",              "commodities": ["coffee", "wood"]},
    "MX": {"tier": "standard", "name": "Mexico",             "commodities": ["coffee", "cattle", "soya", "wood"]},
    "PH": {"tier": "standard", "name": "Philippines",        "commodities": ["cocoa", "oil_palm", "rubber", "wood"]},
    "RU": {"tier": "standard", "name": "Russia",             "commodities": ["wood", "soya"]},
    "UA": {"tier": "standard", "name": "Ukraine",            "commodities": ["soya", "wood"]},
    "UY": {"tier": "standard", "name": "Uruguay",            "commodities": ["cattle", "soya", "wood"]},
    "NI": {"tier": "standard", "name": "Nicaragua",          "commodities": ["coffee", "cattle", "cocoa"]},
    "CR": {"tier": "standard", "name": "Costa Rica",         "commodities": ["coffee", "oil_palm", "cocoa"]},
    "SL": {"tier": "standard", "name": "Sierra Leone",       "commodities": ["cocoa", "oil_palm", "wood"]},
    "GN": {"tier": "standard", "name": "Guinea",             "commodities": ["cocoa", "wood", "coffee"]},
    "LR": {"tier": "standard", "name": "Liberia",            "commodities": ["rubber", "oil_palm", "wood", "cocoa"]},

    # LOW RISK — Simplified due diligence allowed (Art 13)
    "US": {"tier": "low",      "name": "United States",      "commodities": ["soya", "cattle", "wood"]},
    "CA": {"tier": "low",      "name": "Canada",             "commodities": ["wood", "soya"]},
    "AU": {"tier": "low",      "name": "Australia",          "commodities": ["cattle", "wood"]},
    "NZ": {"tier": "low",      "name": "New Zealand",        "commodities": ["wood", "cattle"]},
    "CL": {"tier": "low",      "name": "Chile",              "commodities": ["wood"]},
    "JP": {"tier": "low",      "name": "Japan",              "commodities": ["wood"]},
    "KR": {"tier": "low",      "name": "South Korea",        "commodities": ["wood"]},
    "SE": {"tier": "low",      "name": "Sweden",             "commodities": ["wood"]},
    "FI": {"tier": "low",      "name": "Finland",            "commodities": ["wood"]},
    "DE": {"tier": "low",      "name": "Germany",            "commodities": ["wood"]},
    "FR": {"tier": "low",      "name": "France",             "commodities": ["wood"]},
    "AT": {"tier": "low",      "name": "Austria",            "commodities": ["wood"]},
    "PL": {"tier": "low",      "name": "Poland",             "commodities": ["wood"]},
    "NO": {"tier": "low",      "name": "Norway",             "commodities": ["wood"]},
}


# ---------------------------------------------------------------------------
# Due Diligence Requirements by Article
# ---------------------------------------------------------------------------

DUE_DILIGENCE_REQUIREMENTS: dict[str, dict] = {
    "art_4_general": {
        "title": "General due diligence obligation",
        "article": "4",
        "description": "Operators must exercise due diligence before placing, making available, or exporting relevant commodities/products",
        "applies_to": ["operator", "trader_non_sme"],
        "checks": [
            "information_collection",
            "risk_assessment",
            "risk_mitigation",
        ],
    },
    "art_9_information": {
        "title": "Information collection requirements",
        "article": "9",
        "sub_requirements": {
            "9_1_a": "Description of commodity/product including trade name and type",
            "9_1_b": "Quantity (net mass kg / volume / number of items)",
            "9_1_c": "Country of production and geolocation of plots of land",
            "9_1_d": "Geolocation: polygon if plot >4ha, single point if <=4ha",
            "9_1_e": "Date or time range of production",
            "9_1_f": "Name/address of supplier and recipient",
            "9_1_g": "Adequate verifiable info that products are deforestation-free",
            "9_1_h": "Adequate verifiable info that production complies with local law",
        },
    },
    "art_10_risk_assessment": {
        "title": "Risk assessment",
        "article": "10",
        "criteria": [
            "country_risk_tier",
            "complexity_of_supply_chain",
            "risk_of_mixing_with_unknown_origin",
            "deforestation_prevalence_in_country_region",
            "indigenous_peoples_land_concerns",
            "supplier_reliability_and_complaints",
            "satellite_monitoring_alerts",
            "armed_conflict_in_region",
        ],
    },
    "art_11_risk_mitigation": {
        "title": "Risk mitigation measures",
        "article": "11",
        "measures": [
            "independent_survey_or_audit",
            "additional_documentation_from_supplier",
            "third_party_verification",
            "satellite_monitoring",
            "isotope_testing",
            "on_site_inspections",
            "other_risk_mitigation_measures",
        ],
    },
    "art_12_enhanced_due_diligence": {
        "title": "Enhanced due diligence for high-risk countries",
        "article": "12",
        "applies_to_country_tier": "high",
        "additional_measures": [
            "gather_additional_geolocation",
            "independent_third_party_audit",
            "satellite_image_analysis",
            "field_verification",
        ],
    },
    "art_13_simplified": {
        "title": "Simplified due diligence for low-risk countries",
        "article": "13",
        "applies_to_country_tier": "low",
        "allowed_simplifications": [
            "reduced_information_collection",
            "simplified_risk_assessment",
            "no_mandatory_third_party_audit",
        ],
    },
}


# ---------------------------------------------------------------------------
# EUDR ↔ Cross-Framework Mapping
# ---------------------------------------------------------------------------

EUDR_CROSS_FRAMEWORK_MAP: list[dict] = [
    {"eudr_article": "Art 4 (due diligence)",
     "esrs": "ESRS E4-4 (Biodiversity action plans)",
     "eu_taxonomy": "Forestry DNSH (Climate Adaptation)",
     "gri": "GRI 304-2 (Significant impacts on biodiversity)"},
    {"eudr_article": "Art 9 (information / geolocation)",
     "esrs": "ESRS E4-5 (Metrics: land-use change)",
     "eu_taxonomy": "Forestry screening (Substantial Contribution)",
     "gri": "GRI 304-1 (Sites in/near protected areas)"},
    {"eudr_article": "Art 10 (risk assessment)",
     "esrs": "ESRS E4-1 (Transition plan biodiversity)",
     "eu_taxonomy": "Art 17 DNSH (Biodiversity)",
     "gri": "GRI 304-3 (Habitats protected/restored)"},
    {"eudr_article": "Art 29 (country benchmarking)",
     "esrs": "ESRS E4 IRO-1 (Material impacts identification)",
     "eu_taxonomy": "N/A",
     "gri": "GRI 308-1/2 (Supplier environmental assessment)"},
    {"eudr_article": "Annex I (commodities)",
     "esrs": "ESRS E4-6 (Biodiversity metrics: deforestation)",
     "eu_taxonomy": "Forestry NACE codes (A02)",
     "gri": "GRI 301-1 (Materials by weight/volume)"},
    {"eudr_article": "Art 11-12 (risk mitigation / enhanced DD)",
     "esrs": "ESRS S3-4 (Affected communities actions)",
     "eu_taxonomy": "Minimum Safeguards (OECD Guidelines)",
     "gri": "GRI 411-1 (Indigenous peoples rights)"},
]


# ---------------------------------------------------------------------------
# Enforcement Timeline
# ---------------------------------------------------------------------------

ENFORCEMENT_TIMELINE: list[dict] = [
    {"date": "2023-06-29", "event": "EUDR enters into force",
     "article": "Reg 2023/1115"},
    {"date": "2024-12-30", "event": "Original application date for large operators (deferred)",
     "article": "Art 38(1)"},
    {"date": "2025-06-30", "event": "Original application date for SMEs (deferred)",
     "article": "Art 38(2)"},
    {"date": "2025-12-30", "event": "Revised application date for large operators/traders",
     "article": "Amending Reg 2025/XXX"},
    {"date": "2026-06-30", "event": "Revised application date for SMEs and micro-enterprises",
     "article": "Amending Reg 2025/XXX"},
    {"date": "2025-12-30", "event": "Country benchmarking list first publication deadline",
     "article": "Art 29(2)"},
    {"date": "2028-06-29", "event": "Commission review of EUDR scope and effectiveness",
     "article": "Art 34(1)"},
]


# ---------------------------------------------------------------------------
# Certification Schemes (recognised / indicative for risk mitigation)
# ---------------------------------------------------------------------------

CERTIFICATION_SCHEMES: dict[str, dict] = {
    "RSPO":  {"name": "Roundtable on Sustainable Palm Oil",
              "commodities": ["oil_palm"], "credibility_tier": "high",
              "eudr_recognition": "indicative_not_substitute"},
    "FSC":   {"name": "Forest Stewardship Council",
              "commodities": ["wood"], "credibility_tier": "high",
              "eudr_recognition": "indicative_not_substitute"},
    "PEFC":  {"name": "Programme for Endorsement of Forest Certification",
              "commodities": ["wood"], "credibility_tier": "high",
              "eudr_recognition": "indicative_not_substitute"},
    "RA":    {"name": "Rainforest Alliance",
              "commodities": ["cocoa", "coffee", "oil_palm"],
              "credibility_tier": "medium",
              "eudr_recognition": "indicative_not_substitute"},
    "UTZ":   {"name": "UTZ Certified (now Rainforest Alliance)",
              "commodities": ["cocoa", "coffee"], "credibility_tier": "medium",
              "eudr_recognition": "indicative_not_substitute"},
    "RTRS":  {"name": "Round Table on Responsible Soy",
              "commodities": ["soya"], "credibility_tier": "medium",
              "eudr_recognition": "indicative_not_substitute"},
    "ISCC":  {"name": "International Sustainability & Carbon Certification",
              "commodities": ["oil_palm", "soya"], "credibility_tier": "medium",
              "eudr_recognition": "indicative_not_substitute"},
    "GRSB":  {"name": "Global Roundtable for Sustainable Beef",
              "commodities": ["cattle"], "credibility_tier": "medium",
              "eudr_recognition": "indicative_not_substitute"},
    "SAN":   {"name": "Sustainable Agriculture Network",
              "commodities": ["coffee", "cocoa"], "credibility_tier": "medium",
              "eudr_recognition": "indicative_not_substitute"},
}


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CommodityScreenResult:
    """Result of screening a product for EUDR commodity scope."""
    product_name: str
    hs_code: str
    in_scope: bool
    matched_commodity: Optional[str] = None
    deforestation_cutoff: Optional[str] = None
    derived_products: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class CountryRiskResult:
    """Country risk classification result."""
    country_iso2: str
    country_name: str
    risk_tier: str           # high / standard / low
    commodities_at_risk: list[str] = field(default_factory=list)
    due_diligence_level: str = "standard"   # simplified / standard / enhanced
    article_reference: str = ""
    notes: str = ""


@dataclass
class TraceabilityCheckResult:
    """Supply chain traceability verification result."""
    operator_id: str
    commodity: str
    geolocation_provided: bool = False
    geolocation_type: str = ""          # point / polygon
    plot_area_ha: Optional[float] = None
    geolocation_compliant: bool = False
    supplier_identified: bool = False
    production_date_verified: bool = False
    quantity_verified: bool = False
    local_law_compliance: bool = False
    deforestation_free_verified: bool = False
    traceability_score: float = 0.0     # 0-100
    gaps: list[str] = field(default_factory=list)
    article_references: list[str] = field(default_factory=list)


@dataclass
class DueDiligenceResult:
    """Full due diligence assessment result."""
    operator_id: str
    operator_name: str
    operator_type: str          # operator / trader / trader_sme
    assessment_date: str
    # Scope
    commodities_assessed: list[str] = field(default_factory=list)
    countries_of_origin: list[str] = field(default_factory=list)
    # Scores (0-100)
    information_score: float = 0.0
    risk_assessment_score: float = 0.0
    risk_mitigation_score: float = 0.0
    overall_compliance_score: float = 0.0
    # Status
    compliance_status: str = "non_compliant"  # compliant / at_risk / non_compliant
    due_diligence_level: str = "standard"     # simplified / standard / enhanced
    # Country risk
    country_risk_results: list[dict] = field(default_factory=list)
    # Traceability
    traceability_results: list[dict] = field(default_factory=list)
    # Gaps & recommendations
    gaps: list[dict] = field(default_factory=list)
    recommendations: list[dict] = field(default_factory=list)
    # Certifications
    certifications: list[dict] = field(default_factory=list)
    # Cross-framework
    esrs_e4_linkage: list[str] = field(default_factory=list)
    eu_taxonomy_biodiversity_dnsh: Optional[bool] = None
    # Enforcement
    enforcement_deadline: str = ""
    days_until_deadline: int = 0
    # Due diligence statement fields (Art 4(2))
    statement_ready: bool = False
    statement_reference_number: str = ""


@dataclass
class ComplianceGapResult:
    """Detailed compliance gap analysis."""
    operator_id: str
    total_gaps: int = 0
    critical_gaps: int = 0
    major_gaps: int = 0
    minor_gaps: int = 0
    gap_details: list[dict] = field(default_factory=list)
    remediation_plan: list[dict] = field(default_factory=list)
    estimated_remediation_weeks: int = 0
    readiness_pct: float = 0.0


# ---------------------------------------------------------------------------
# EUDR Compliance Engine
# ---------------------------------------------------------------------------

class EUDREngine:
    """EU Deforestation Regulation 2023/1115 — Compliance Engine."""

    # ── 1. Commodity Screening ──────────────────────────────────────────────

    def screen_commodity(
        self,
        product_name: str,
        hs_code: str,
    ) -> CommodityScreenResult:
        """Screen a product by HS code to determine EUDR scope."""
        hs_prefix = hs_code[:4] if len(hs_code) >= 4 else hs_code

        for commodity, data in EUDR_COMMODITIES.items():
            if hs_prefix in data["hs_chapters"]:
                return CommodityScreenResult(
                    product_name=product_name,
                    hs_code=hs_code,
                    in_scope=True,
                    matched_commodity=commodity,
                    deforestation_cutoff=data["deforestation_cutoff"],
                    derived_products=data["derived_products"],
                    notes=f"Matched EUDR Annex I commodity: {data['description']}",
                )

        return CommodityScreenResult(
            product_name=product_name,
            hs_code=hs_code,
            in_scope=False,
            notes="HS code not in EUDR Annex I scope",
        )

    # ── 2. Country Risk Classification ──────────────────────────────────────

    def classify_country_risk(
        self,
        country_iso2: str,
        commodity: str = "",
    ) -> CountryRiskResult:
        """Classify country risk tier under Article 29."""
        country_iso2 = country_iso2.upper()
        entry = COUNTRY_RISK_TIERS.get(country_iso2)

        if entry:
            tier = entry["tier"]
            dd_level = {
                "high": "enhanced",
                "standard": "standard",
                "low": "simplified",
            }[tier]
            art_ref = {
                "high": "Art 10(2), Art 12",
                "standard": "Art 10(1)",
                "low": "Art 13",
            }[tier]

            commodities_at_risk = entry.get("commodities", [])
            if commodity and commodity in commodities_at_risk:
                notes = f"{commodity} is a known commodity sourced from {entry['name']} ({tier} risk)"
            elif commodity:
                notes = f"{commodity} not in primary risk commodity list for {entry['name']}"
            else:
                notes = f"{entry['name']} classified as {tier} risk"

            return CountryRiskResult(
                country_iso2=country_iso2,
                country_name=entry["name"],
                risk_tier=tier,
                commodities_at_risk=commodities_at_risk,
                due_diligence_level=dd_level,
                article_reference=art_ref,
                notes=notes,
            )

        # Unknown country → default to standard
        return CountryRiskResult(
            country_iso2=country_iso2,
            country_name=country_iso2,
            risk_tier="standard",
            due_diligence_level="standard",
            article_reference="Art 10(1) (default)",
            notes=f"Country {country_iso2} not in benchmarking list; defaulting to standard risk",
        )

    # ── 3. Traceability Verification ────────────────────────────────────────

    def verify_traceability(
        self,
        operator_id: str,
        commodity: str,
        geolocation_provided: bool = False,
        geolocation_type: str = "",
        plot_area_ha: Optional[float] = None,
        supplier_name: str = "",
        supplier_address: str = "",
        production_date: str = "",
        quantity_kg: float = 0.0,
        local_law_evidence: bool = False,
        deforestation_free_evidence: bool = False,
    ) -> TraceabilityCheckResult:
        """Verify supply chain traceability per Article 9."""
        gaps: list[str] = []
        refs: list[str] = []
        score = 100.0

        # Art 9(1)(c)(d) — geolocation
        geo_compliant = False
        if not geolocation_provided:
            gaps.append("No geolocation of production plot provided")
            refs.append("Art 9(1)(c)-(d)")
            score -= 25.0
        else:
            if plot_area_ha is not None and plot_area_ha > 4.0:
                if geolocation_type != "polygon":
                    gaps.append("Plot >4ha requires polygon geolocation, not point")
                    refs.append("Art 9(1)(d)")
                    score -= 10.0
                else:
                    geo_compliant = True
            else:
                geo_compliant = True  # <=4ha: point is acceptable

        # Art 9(1)(f) — supplier identification
        supplier_identified = bool(supplier_name and supplier_address)
        if not supplier_identified:
            gaps.append("Supplier name and/or address not provided")
            refs.append("Art 9(1)(f)")
            score -= 15.0

        # Art 9(1)(e) — production date
        prod_date_verified = bool(production_date)
        if not prod_date_verified:
            gaps.append("Production date/time range not provided")
            refs.append("Art 9(1)(e)")
            score -= 10.0

        # Art 9(1)(b) — quantity
        quantity_verified = quantity_kg > 0
        if not quantity_verified:
            gaps.append("Quantity not specified or zero")
            refs.append("Art 9(1)(b)")
            score -= 10.0

        # Art 9(1)(h) — local law compliance
        if not local_law_evidence:
            gaps.append("No evidence of compliance with local laws of country of production")
            refs.append("Art 9(1)(h)")
            score -= 15.0

        # Art 9(1)(g) — deforestation-free
        if not deforestation_free_evidence:
            gaps.append("No verifiable evidence that product is deforestation-free since 31 Dec 2020")
            refs.append("Art 9(1)(g)")
            score -= 25.0

        score = max(0.0, score)

        return TraceabilityCheckResult(
            operator_id=operator_id,
            commodity=commodity,
            geolocation_provided=geolocation_provided,
            geolocation_type=geolocation_type,
            plot_area_ha=plot_area_ha,
            geolocation_compliant=geo_compliant,
            supplier_identified=supplier_identified,
            production_date_verified=prod_date_verified,
            quantity_verified=quantity_verified,
            local_law_compliance=local_law_evidence,
            deforestation_free_verified=deforestation_free_evidence,
            traceability_score=round(score, 1),
            gaps=gaps,
            article_references=refs,
        )

    # ── 4. Full Due Diligence Assessment ────────────────────────────────────

    def assess_due_diligence(
        self,
        operator_id: str,
        operator_name: str,
        operator_type: str = "operator",
        commodities: list[str] | None = None,
        countries_of_origin: list[str] | None = None,
        certifications: list[str] | None = None,
        # Traceability inputs (per lot — simplified: one lot per commodity)
        geolocation_provided: bool = False,
        geolocation_type: str = "",
        plot_area_ha: Optional[float] = None,
        supplier_name: str = "",
        supplier_address: str = "",
        production_date: str = "",
        quantity_kg: float = 0.0,
        local_law_evidence: bool = False,
        deforestation_free_evidence: bool = False,
        # Risk mitigation
        independent_audit: bool = False,
        satellite_monitoring: bool = False,
        third_party_verification: bool = False,
    ) -> DueDiligenceResult:
        """Full due diligence assessment per Articles 4-12."""
        commodities = commodities or []
        countries_of_origin = countries_of_origin or []
        certifications = certifications or []
        today_str = date.today().isoformat()

        # Determine enforcement deadline based on operator type
        if operator_type in ("trader_sme", "sme"):
            enforcement_deadline = "2026-06-30"
        else:
            enforcement_deadline = "2025-12-30"

        deadline_date = date.fromisoformat(enforcement_deadline)
        days_until = (deadline_date - date.today()).days

        # ── Step 1: Country risk classification ────────────────────────────
        country_results = []
        max_risk_tier = "low"
        tier_order = {"low": 0, "standard": 1, "high": 2}
        for country in countries_of_origin:
            for c in commodities:
                cr = self.classify_country_risk(country, c)
                country_results.append({
                    "country": cr.country_iso2,
                    "country_name": cr.country_name,
                    "commodity": c,
                    "risk_tier": cr.risk_tier,
                    "due_diligence_level": cr.due_diligence_level,
                    "article": cr.article_reference,
                })
                if tier_order.get(cr.risk_tier, 1) > tier_order.get(max_risk_tier, 0):
                    max_risk_tier = cr.risk_tier

        dd_level = {"high": "enhanced", "standard": "standard", "low": "simplified"}[max_risk_tier]

        # ── Step 2: Traceability verification per commodity ────────────────
        traceability_results = []
        for c in commodities:
            tr = self.verify_traceability(
                operator_id=operator_id,
                commodity=c,
                geolocation_provided=geolocation_provided,
                geolocation_type=geolocation_type,
                plot_area_ha=plot_area_ha,
                supplier_name=supplier_name,
                supplier_address=supplier_address,
                production_date=production_date,
                quantity_kg=quantity_kg,
                local_law_evidence=local_law_evidence,
                deforestation_free_evidence=deforestation_free_evidence,
            )
            traceability_results.append({
                "commodity": c,
                "traceability_score": tr.traceability_score,
                "gaps": tr.gaps,
                "article_references": tr.article_references,
                "geolocation_compliant": tr.geolocation_compliant,
            })

        # ── Step 3: Scoring ────────────────────────────────────────────────

        # Information score (Art 9) — average traceability scores
        info_scores = [t["traceability_score"] for t in traceability_results]
        information_score = sum(info_scores) / len(info_scores) if info_scores else 0.0

        # Risk assessment score (Art 10) — based on country risk analysis
        risk_assessment_score = 100.0
        if not countries_of_origin:
            risk_assessment_score -= 40.0  # No country of origin identified
        if max_risk_tier == "high":
            risk_assessment_score -= 20.0  # High-risk country inherently harder
        if not commodities:
            risk_assessment_score -= 30.0  # No commodities screened

        # Risk mitigation score (Art 11) — measures taken
        risk_mitigation_score = 30.0   # Baseline for declaring commodities
        if independent_audit:
            risk_mitigation_score += 25.0
        if satellite_monitoring:
            risk_mitigation_score += 20.0
        if third_party_verification:
            risk_mitigation_score += 15.0

        # Certification bonus (indicative, not substitute — Art 10(3))
        cert_results = []
        for cert_code in certifications:
            scheme = CERTIFICATION_SCHEMES.get(cert_code)
            if scheme:
                risk_mitigation_score += 5.0  # Minor credit per certification
                cert_results.append({
                    "code": cert_code,
                    "name": scheme["name"],
                    "credibility": scheme["credibility_tier"],
                    "note": scheme["eudr_recognition"],
                })

        risk_mitigation_score = min(100.0, risk_mitigation_score)

        # Enhanced DD requirements (Art 12) — reduce score if not met
        if dd_level == "enhanced":
            if not independent_audit:
                risk_mitigation_score -= 15.0
            if not satellite_monitoring:
                risk_mitigation_score -= 10.0

        risk_mitigation_score = max(0.0, risk_mitigation_score)

        # Overall compliance score (weighted)
        overall = (
            information_score * 0.45
            + risk_assessment_score * 0.25
            + risk_mitigation_score * 0.30
        )
        overall = round(overall, 1)

        # Status
        if overall >= 80:
            status = "compliant"
        elif overall >= 50:
            status = "at_risk"
        else:
            status = "non_compliant"

        # ── Step 4: Gap analysis ───────────────────────────────────────────
        all_gaps = []
        for tr in traceability_results:
            for i, gap in enumerate(tr["gaps"]):
                ref = tr["article_references"][i] if i < len(tr["article_references"]) else ""
                severity = "critical" if "geolocation" in gap.lower() or "deforestation" in gap.lower() else "major"
                all_gaps.append({
                    "commodity": tr["commodity"],
                    "gap": gap,
                    "article": ref,
                    "severity": severity,
                })
        if not countries_of_origin:
            all_gaps.append({
                "commodity": "all",
                "gap": "No country of origin identified for risk assessment",
                "article": "Art 10(1)",
                "severity": "critical",
            })
        if dd_level == "enhanced" and not independent_audit:
            all_gaps.append({
                "commodity": "all",
                "gap": "Independent audit required for high-risk country sourcing",
                "article": "Art 12",
                "severity": "critical",
            })

        # ── Step 5: Recommendations ────────────────────────────────────────
        recs = self._generate_recommendations(
            dd_level, all_gaps, certifications, max_risk_tier,
            geolocation_provided, satellite_monitoring,
        )

        # ── Step 6: Cross-framework linkage ────────────────────────────────
        esrs_links = [
            "ESRS E4-4: Disclose EUDR due diligence in biodiversity action plans",
            "ESRS E4-5: Report land-use change metrics from EUDR commodity sourcing",
            "ESRS E4-6: Quantify deforestation-free supply chain percentage",
        ]
        taxonomy_dnsh = overall >= 70  # Indicative: DNSH biodiversity pass if score >= 70

        # Statement readiness
        statement_ready = (status == "compliant" and len(all_gaps) == 0)

        return DueDiligenceResult(
            operator_id=operator_id,
            operator_name=operator_name,
            operator_type=operator_type,
            assessment_date=today_str,
            commodities_assessed=commodities,
            countries_of_origin=countries_of_origin,
            information_score=round(information_score, 1),
            risk_assessment_score=round(risk_assessment_score, 1),
            risk_mitigation_score=round(risk_mitigation_score, 1),
            overall_compliance_score=overall,
            compliance_status=status,
            due_diligence_level=dd_level,
            country_risk_results=country_results,
            traceability_results=traceability_results,
            gaps=all_gaps,
            recommendations=recs,
            certifications=cert_results,
            esrs_e4_linkage=esrs_links,
            eu_taxonomy_biodiversity_dnsh=taxonomy_dnsh,
            enforcement_deadline=enforcement_deadline,
            days_until_deadline=days_until,
            statement_ready=statement_ready,
            statement_reference_number=f"EUDR-DDS-{operator_id}-{today_str}" if statement_ready else "",
        )

    # ── 5. Compliance Gap Analysis ──────────────────────────────────────────

    def analyse_compliance_gaps(
        self,
        operator_id: str,
        dd_result: DueDiligenceResult,
    ) -> ComplianceGapResult:
        """Produce detailed compliance gap analysis with remediation plan."""
        gap_details = dd_result.gaps
        critical = sum(1 for g in gap_details if g.get("severity") == "critical")
        major = sum(1 for g in gap_details if g.get("severity") == "major")
        minor = sum(1 for g in gap_details if g.get("severity") == "minor")

        # Remediation plan
        remed: list[dict] = []
        weeks_estimate = 0

        for g in gap_details:
            action, wks = self._gap_to_remediation(g)
            remed.append({
                "gap": g["gap"],
                "article": g.get("article", ""),
                "severity": g.get("severity", "major"),
                "remediation_action": action,
                "estimated_weeks": wks,
            })
            weeks_estimate = max(weeks_estimate, wks)

        readiness = dd_result.overall_compliance_score

        return ComplianceGapResult(
            operator_id=operator_id,
            total_gaps=len(gap_details),
            critical_gaps=critical,
            major_gaps=major,
            minor_gaps=minor,
            gap_details=gap_details,
            remediation_plan=remed,
            estimated_remediation_weeks=weeks_estimate,
            readiness_pct=round(readiness, 1),
        )

    # ── 6. Due Diligence Statement (Art 4(2)) ──────────────────────────────

    def generate_dds(
        self,
        dd_result: DueDiligenceResult,
    ) -> dict:
        """Generate Due Diligence Statement per Article 4(2)."""
        return {
            "reference_number": dd_result.statement_reference_number or f"EUDR-DDS-{dd_result.operator_id}-{dd_result.assessment_date}",
            "operator_id": dd_result.operator_id,
            "operator_name": dd_result.operator_name,
            "operator_type": dd_result.operator_type,
            "date_issued": dd_result.assessment_date,
            "commodities": dd_result.commodities_assessed,
            "countries_of_origin": dd_result.countries_of_origin,
            "due_diligence_level": dd_result.due_diligence_level,
            "compliance_status": dd_result.compliance_status,
            "overall_score": dd_result.overall_compliance_score,
            "statement_ready": dd_result.statement_ready,
            "declaration": (
                "The operator/trader declares that due diligence has been exercised "
                "in accordance with Regulation (EU) 2023/1115 and that the relevant "
                "commodities and products are deforestation-free and have been produced "
                "in compliance with the relevant legislation of the country of production."
                if dd_result.statement_ready
                else "Due diligence is INCOMPLETE. Gaps must be remediated before a valid "
                     "due diligence statement can be issued."
            ),
            "gaps_remaining": len(dd_result.gaps),
            "enforcement_deadline": dd_result.enforcement_deadline,
            "days_until_deadline": dd_result.days_until_deadline,
            "certifications": dd_result.certifications,
            "cross_framework": {
                "esrs_e4": dd_result.esrs_e4_linkage,
                "eu_taxonomy_biodiversity_dnsh": dd_result.eu_taxonomy_biodiversity_dnsh,
            },
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _generate_recommendations(
        self,
        dd_level: str,
        gaps: list[dict],
        certifications: list[str],
        max_risk_tier: str,
        geolocation_provided: bool,
        satellite_monitoring: bool,
    ) -> list[dict]:
        recs: list[dict] = []

        if not geolocation_provided:
            recs.append({
                "priority": "critical",
                "recommendation": "Obtain plot-level geolocation (GPS coordinates or polygon) from all direct suppliers",
                "article": "Art 9(1)(c)-(d)",
                "estimated_effort": "4-8 weeks",
            })

        if max_risk_tier == "high" and not satellite_monitoring:
            recs.append({
                "priority": "high",
                "recommendation": "Implement satellite monitoring for high-risk sourcing regions (e.g., Global Forest Watch alerts)",
                "article": "Art 12",
                "estimated_effort": "2-4 weeks",
            })

        if dd_level == "enhanced" and not any(g.get("gap", "").startswith("Independent") for g in gaps):
            recs.append({
                "priority": "high",
                "recommendation": "Engage independent third-party auditor for enhanced due diligence",
                "article": "Art 12",
                "estimated_effort": "6-12 weeks",
            })

        if not certifications:
            recs.append({
                "priority": "medium",
                "recommendation": "Pursue recognised certification schemes (FSC, RSPO, RA) as indicative risk mitigation evidence",
                "article": "Art 10(3)",
                "estimated_effort": "12-24 weeks",
            })

        has_defor_gap = any("deforestation" in g.get("gap", "").lower() for g in gaps)
        if has_defor_gap:
            recs.append({
                "priority": "critical",
                "recommendation": "Establish deforestation-free verification system using satellite imagery and supplier attestations with cutoff date 31 Dec 2020",
                "article": "Art 9(1)(g)",
                "estimated_effort": "8-16 weeks",
            })

        has_law_gap = any("local law" in g.get("gap", "").lower() for g in gaps)
        if has_law_gap:
            recs.append({
                "priority": "high",
                "recommendation": "Collect and verify documentation of compliance with legislation of country of production (land tenure, environmental, labour)",
                "article": "Art 9(1)(h)",
                "estimated_effort": "4-8 weeks",
            })

        # Cross-framework recommendation
        recs.append({
            "priority": "medium",
            "recommendation": "Integrate EUDR findings into CSRD/ESRS E4 biodiversity disclosures and EU Taxonomy DNSH assessment",
            "article": "ESRS E4 / EU Taxonomy Art 17",
            "estimated_effort": "2-4 weeks",
        })

        return recs

    def _gap_to_remediation(self, gap: dict) -> tuple[str, int]:
        """Map a gap to a remediation action and estimated weeks."""
        g = gap.get("gap", "").lower()
        if "geolocation" in g:
            return "Obtain GPS/polygon coordinates from direct suppliers and map to production plots", 8
        if "deforestation" in g:
            return "Implement deforestation-free verification using satellite data and cutoff date (31 Dec 2020)", 12
        if "local law" in g:
            return "Collect and verify country-of-production legal compliance documentation", 6
        if "supplier" in g:
            return "Map full supply chain with supplier name, address, and business registration", 4
        if "production date" in g:
            return "Obtain production date or time-range records from suppliers", 2
        if "quantity" in g:
            return "Verify and record net mass/volume for each commodity lot", 2
        if "audit" in g:
            return "Engage accredited third-party auditor for independent verification", 10
        if "country" in g:
            return "Identify and document all countries of origin for sourced commodities", 3
        return "Address the identified gap with appropriate documentation and controls", 4

    # ── Static Reference Methods ─────────────────────────────────────────────

    @staticmethod
    def get_commodities() -> dict:
        """Return EUDR commodity definitions (Annex I)."""
        return EUDR_COMMODITIES

    @staticmethod
    def get_country_benchmarks() -> dict:
        """Return country risk tier benchmarks (Art 29)."""
        return COUNTRY_RISK_TIERS

    @staticmethod
    def get_enforcement_timeline() -> list[dict]:
        """Return EUDR enforcement timeline milestones."""
        return ENFORCEMENT_TIMELINE

    @staticmethod
    def get_certification_schemes() -> dict:
        """Return recognised certification schemes."""
        return CERTIFICATION_SCHEMES

    @staticmethod
    def get_due_diligence_requirements() -> dict:
        """Return due diligence requirement definitions by article."""
        return DUE_DILIGENCE_REQUIREMENTS

    @staticmethod
    def get_cross_framework_map() -> list[dict]:
        """Return EUDR ↔ ESRS E4 / EU Taxonomy / GRI cross-reference."""
        return EUDR_CROSS_FRAMEWORK_MAP

    @staticmethod
    def get_hs_code_lookup() -> dict[str, list[str]]:
        """Return HS code → commodity mapping for quick lookup."""
        lookup: dict[str, str] = {}
        for commodity, data in EUDR_COMMODITIES.items():
            for hs in data["hs_chapters"]:
                lookup[hs] = commodity
        return lookup
