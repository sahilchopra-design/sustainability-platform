"""
Digital Product Passport & Lifecycle Finance Engine (EU ESPR) — E82
====================================================================
Covers the full regulatory and lifecycle-economics scope of:
  - Regulation (EU) 2024/1781 (Ecodesign for Sustainable Products Regulation — ESPR)
  - Regulation (EU) 2023/1542 (EU Battery Regulation)
  - Commission Delegated Regulation on DPP schema (forthcoming — draft Q1 2025)
  - ISO 14044:2006 / ISO 14067:2018 — LCA and product carbon footprint
  - EN 15804:2012+A2:2019 — EPD methodology for construction products
  - PEF Category Rules (European Commission, various versions)
  - Extended Producer Responsibility (EPR) schemes under Directive 2008/98/EC
    as transposed by Member States (2021 onward)

Sub-modules:
  1. ESPR Compliance Assessment  — product category scoping, requirements, gaps
  2. DPP Schema Builder          — completeness, mandatory-field mapping
  3. Lifecycle GHG Calculator    — ISO 14044/PEF cradle-to-grave emissions
  4. Circularity Index           — 5-dimension scoring
  5. EU Battery Regulation       — Art 38-65 DPP + recycled content + supply-chain DD
  6. EPR Levy Calculator         — 20 EU Member State EPR levies
  7. Full Assessment Orchestrator — composite dpp_readiness_score + espr_tier
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. ESPR Product Categories — 15 categories
# ---------------------------------------------------------------------------

ESPR_PRODUCT_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "textiles": {
        "regulation_ref": "ESPR Delegated Act — Textiles (priority group, Annex I)",
        "dpp_mandatory_year": 2026,
        "key_requirements": [
            "recycled content declaration",
            "microplastic release info",
            "durability and care instructions",
            "hazardous substance restrictions",
            "repairability information",
        ],
        "eu_reg_basis": "Regulation (EU) 2024/1781 Art 5, 8, 9",
        "pef_category_rule": "PEF CR Apparel & Footwear v3.0",
    },
    "electronics": {
        "regulation_ref": "ESPR Delegated Act — Electronics & ICT (priority group)",
        "dpp_mandatory_year": 2027,
        "key_requirements": [
            "spare-parts availability commitment",
            "software update support period",
            "disassembly instructions",
            "critical raw material content",
            "energy efficiency label",
        ],
        "eu_reg_basis": "Regulation (EU) 2024/1781 Art 5, 8; Regulation (EU) 2019/2021 (displays)",
        "pef_category_rule": "PEF CR ICT — Laptop/Tablet v1.0",
    },
    "furniture": {
        "regulation_ref": "ESPR Delegated Act — Furniture (priority group)",
        "dpp_mandatory_year": 2028,
        "key_requirements": [
            "recycled and bio-based content",
            "formaldehyde / VOC emission class",
            "wood origin traceability (EUDR linkage)",
            "end-of-life disassembly",
        ],
        "eu_reg_basis": "Regulation (EU) 2024/1781 Art 5",
        "pef_category_rule": "N/A — sector-specific EPD",
    },
    "toys": {
        "regulation_ref": "Toy Safety Directive 2009/48/EC + ESPR linkage",
        "dpp_mandatory_year": 2028,
        "key_requirements": [
            "chemical safety (SVHC list)",
            "age appropriateness labelling",
            "recycled content",
            "CE marking",
        ],
        "eu_reg_basis": "Directive 2009/48/EC; Regulation (EU) 2024/1781",
        "pef_category_rule": "N/A",
    },
    "batteries": {
        "regulation_ref": "Regulation (EU) 2023/1542 (EU Battery Regulation)",
        "dpp_mandatory_year": 2026,
        "key_requirements": [
            "carbon footprint declaration (Art 7)",
            "recycled content (Art 8)",
            "supply chain due diligence (Art 52-54)",
            "state of health / QR passport (Art 38-65)",
            "battery management system data access",
        ],
        "eu_reg_basis": "Regulation (EU) 2023/1542",
        "pef_category_rule": "PEF CR Batteries v2.0",
    },
    "vehicles": {
        "regulation_ref": "ESPR linkage + End-of-Life Vehicles Directive revision",
        "dpp_mandatory_year": 2027,
        "key_requirements": [
            "recycled content at EoL",
            "critical raw material content declaration",
            "CO2 per km lifecycle disclosure",
            "fluid hazardousness",
        ],
        "eu_reg_basis": "Regulation (EU) 2024/1781; Directive 2000/53/EC (ELV revision)",
        "pef_category_rule": "PEF CR Automotive v1.0",
    },
    "construction_products": {
        "regulation_ref": "Construction Products Regulation (EU) 305/2011 + ESPR",
        "dpp_mandatory_year": 2027,
        "key_requirements": [
            "EPD (EN 15804+A2)",
            "SVHC content declaration (>0.1 wt%)",
            "fire/structural performance",
            "recycled aggregate content",
        ],
        "eu_reg_basis": "Regulation (EU) 305/2011; Regulation (EU) 2024/1781",
        "pef_category_rule": "EN 15804:2012+A2:2019",
    },
    "tyres": {
        "regulation_ref": "Tyre Labelling Regulation (EU) 2020/740 + ESPR",
        "dpp_mandatory_year": 2027,
        "key_requirements": [
            "rolling resistance class (A-E)",
            "wet grip class",
            "external rolling noise",
            "recycled rubber content",
        ],
        "eu_reg_basis": "Regulation (EU) 2020/740; Regulation (EU) 2024/1781",
        "pef_category_rule": "N/A",
    },
    "detergents": {
        "regulation_ref": "Detergents Regulation (EC) 648/2004 + ESPR",
        "dpp_mandatory_year": 2028,
        "key_requirements": [
            "biodegradability data",
            "surfactant ingredient disclosure",
            "dosage optimisation info",
            "concentrated format preference",
        ],
        "eu_reg_basis": "Regulation (EC) 648/2004; Regulation (EU) 2024/1781",
        "pef_category_rule": "PEF CR Household and Institutional Cleaning",
    },
    "steel": {
        "regulation_ref": "ESPR Delegated Act — Steel (priority group, Annex I)",
        "dpp_mandatory_year": 2026,
        "key_requirements": [
            "recycled content by product grade",
            "energy intensity per tonne",
            "scope 1/2 GHG per tonne",
            "CO2 trajectory to net zero",
        ],
        "eu_reg_basis": "Regulation (EU) 2024/1781; CBAM linkage",
        "pef_category_rule": "PEF CR Intermediate Steel Products",
    },
    "cement": {
        "regulation_ref": "ESPR Delegated Act — Cement (priority group)",
        "dpp_mandatory_year": 2027,
        "key_requirements": [
            "clinker-to-cement ratio",
            "CO2 per tonne clinker",
            "alternative fuel rate",
            "CCUS readiness declaration",
        ],
        "eu_reg_basis": "Regulation (EU) 2024/1781; CBAM linkage",
        "pef_category_rule": "EN 15804+A2 (construction sector)",
    },
    "aluminium": {
        "regulation_ref": "ESPR Delegated Act — Aluminium (priority group)",
        "dpp_mandatory_year": 2026,
        "key_requirements": [
            "primary vs recycled content split",
            "electricity source (GHG footprint)",
            "fluoride emission profile",
            "critical raw material (lithium) mapping",
        ],
        "eu_reg_basis": "Regulation (EU) 2024/1781; CBAM linkage",
        "pef_category_rule": "PEF CR Aluminium v3.0",
    },
    "chemicals": {
        "regulation_ref": "REACH Regulation (EC) 1907/2006 + ESPR + CLP",
        "dpp_mandatory_year": 2027,
        "key_requirements": [
            "SVHC presence >0.1 wt% (REACH Art 59)",
            "safety data sheet (SDS) linkage",
            "safe-use information",
            "substance of very high concern disclosure",
        ],
        "eu_reg_basis": "Regulation (EC) 1907/2006; Regulation (EU) 2024/1781",
        "pef_category_rule": "PEF CR Specific Chemical Sector Rules",
    },
    "packaging": {
        "regulation_ref": "Packaging and Packaging Waste Regulation (EU) 2025/40",
        "dpp_mandatory_year": 2026,
        "key_requirements": [
            "recycled content by packaging category",
            "recyclability tier (A-E)",
            "unnecessary packaging prohibition compliance",
            "reusable packaging ratio",
        ],
        "eu_reg_basis": "Regulation (EU) 2025/40; Regulation (EU) 2024/1781",
        "pef_category_rule": "PEF CR Packaging v4.0",
    },
    "food_contact_materials": {
        "regulation_ref": "Regulation (EC) 1935/2004 + ESPR",
        "dpp_mandatory_year": 2028,
        "key_requirements": [
            "migration test compliance",
            "food-contact substance declaration",
            "recycled material safety verification",
            "compostability / recyclability label accuracy",
        ],
        "eu_reg_basis": "Regulation (EC) 1935/2004; Regulation (EU) 2024/1781",
        "pef_category_rule": "N/A",
    },
}

# ---------------------------------------------------------------------------
# 2. DPP Mandatory Fields — 25 fields per EU DPP schema (draft 2025)
# ---------------------------------------------------------------------------

DPP_MANDATORY_FIELDS: List[Dict[str, str]] = [
    {"field_id": "DPP-01", "name": "unique_product_identifier",     "section": "product_identity",   "format": "GS1/EPCIS URI"},
    {"field_id": "DPP-02", "name": "gtin_or_ean_code",              "section": "product_identity",   "format": "GTIN-14"},
    {"field_id": "DPP-03", "name": "product_name_description",      "section": "product_identity",   "format": "text"},
    {"field_id": "DPP-04", "name": "product_category_espr",         "section": "product_identity",   "format": "ESPR category code"},
    {"field_id": "DPP-05", "name": "manufacturer_name",             "section": "manufacturer",       "format": "text"},
    {"field_id": "DPP-06", "name": "manufacturer_address",          "section": "manufacturer",       "format": "ISO 3166-1 country + address"},
    {"field_id": "DPP-07", "name": "manufacturer_economic_id",      "section": "manufacturer",       "format": "VAT / EORI / LEI"},
    {"field_id": "DPP-08", "name": "country_of_origin",             "section": "manufacturer",       "format": "ISO 3166-1 alpha-2"},
    {"field_id": "DPP-09", "name": "materials_composition",         "section": "materials",          "format": "wt% per material class"},
    {"field_id": "DPP-10", "name": "recycled_content_pct",          "section": "materials",          "format": "percent (pre + post consumer)"},
    {"field_id": "DPP-11", "name": "critical_raw_materials",        "section": "materials",          "format": "EU CRM list reference"},
    {"field_id": "DPP-12", "name": "hazardous_substances",          "section": "materials",          "format": "CAS No. + SVHC list ref"},
    {"field_id": "DPP-13", "name": "product_carbon_footprint_kg",   "section": "carbon_footprint",   "format": "kg CO2e per unit (ISO 14067)"},
    {"field_id": "DPP-14", "name": "lca_scope_boundary",            "section": "carbon_footprint",   "format": "cradle-to-gate / -grave / -grave w/recycling"},
    {"field_id": "DPP-15", "name": "carbon_footprint_methodology",  "section": "carbon_footprint",   "format": "ISO 14044 / PEF / EPD"},
    {"field_id": "DPP-16", "name": "recyclability_rate_pct",        "section": "recyclability",      "format": "percent"},
    {"field_id": "DPP-17", "name": "end_of_life_instructions",      "section": "recyclability",      "format": "text / waste code"},
    {"field_id": "DPP-18", "name": "disassembly_instructions",      "section": "recyclability",      "format": "URL or QR link"},
    {"field_id": "DPP-19", "name": "expected_lifetime_years",       "section": "durability",         "format": "years"},
    {"field_id": "DPP-20", "name": "warranty_period_years",         "section": "durability",         "format": "years"},
    {"field_id": "DPP-21", "name": "repairability_score",           "section": "repairability",      "format": "0-10 scale"},
    {"field_id": "DPP-22", "name": "spare_parts_availability_years","section": "repairability",      "format": "years"},
    {"field_id": "DPP-23", "name": "supply_chain_tier1_country",    "section": "supply_chain",       "format": "ISO 3166-1 alpha-2"},
    {"field_id": "DPP-24", "name": "certification_scheme",          "section": "supply_chain",       "format": "scheme name + certificate ID"},
    {"field_id": "DPP-25", "name": "dpp_schema_version",            "section": "product_identity",   "format": "semver (e.g. 1.0.0)"},
]

# ---------------------------------------------------------------------------
# 3. LCA Emission Factors (kg CO2e per unit of activity)
#    Indexed by [product_category][lifecycle_stage]
# ---------------------------------------------------------------------------

LCA_EMISSION_FACTORS: Dict[str, Dict[str, float]] = {
    "textiles":              {"raw_materials": 12.4, "manufacturing": 8.2,  "transport": 1.8,  "use_phase": 5.6,  "end_of_life": 2.1},
    "electronics":           {"raw_materials": 60.0, "manufacturing": 45.0, "transport": 4.5,  "use_phase": 80.0, "end_of_life": 8.0},
    "furniture":             {"raw_materials": 25.0, "manufacturing": 15.0, "transport": 6.0,  "use_phase": 0.5,  "end_of_life": 4.0},
    "toys":                  {"raw_materials": 3.5,  "manufacturing": 2.1,  "transport": 0.8,  "use_phase": 0.2,  "end_of_life": 1.0},
    "batteries":             {"raw_materials": 85.0, "manufacturing": 55.0, "transport": 5.0,  "use_phase": 10.0, "end_of_life": 12.0},
    "vehicles":              {"raw_materials": 5200, "manufacturing": 3800, "transport": 200,  "use_phase": 28000,"end_of_life": 900},
    "construction_products": {"raw_materials": 180,  "manufacturing": 120,  "transport": 25.0, "use_phase": 15.0, "end_of_life": 30.0},
    "tyres":                 {"raw_materials": 15.0, "manufacturing": 10.0, "transport": 2.0,  "use_phase": 8.0,  "end_of_life": 3.5},
    "detergents":            {"raw_materials": 1.8,  "manufacturing": 1.2,  "transport": 0.5,  "use_phase": 0.8,  "end_of_life": 0.3},
    "steel":                 {"raw_materials": 400,  "manufacturing": 950,  "transport": 40.0, "use_phase": 5.0,  "end_of_life": -80.0},
    "cement":                {"raw_materials": 250,  "manufacturing": 600,  "transport": 30.0, "use_phase": 10.0, "end_of_life": 5.0},
    "aluminium":             {"raw_materials": 500,  "manufacturing": 1400, "transport": 50.0, "use_phase": 5.0,  "end_of_life": -200.0},
    "chemicals":             {"raw_materials": 120,  "manufacturing": 200,  "transport": 15.0, "use_phase": 30.0, "end_of_life": 10.0},
    "packaging":             {"raw_materials": 1.5,  "manufacturing": 0.8,  "transport": 0.3,  "use_phase": 0.1,  "end_of_life": 0.5},
    "food_contact_materials":{"raw_materials": 2.0,  "manufacturing": 1.1,  "transport": 0.4,  "use_phase": 0.2,  "end_of_life": 0.6},
    "_default":              {"raw_materials": 20.0, "manufacturing": 15.0, "transport": 3.0,  "use_phase": 10.0, "end_of_life": 3.0},
}

# ---------------------------------------------------------------------------
# 4. EU Battery Regulation 2023/1542 Requirements (Art 38-65)
# ---------------------------------------------------------------------------

EU_BATTERY_REGULATION_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "carbon_footprint_declaration": {
        "article": "Art 7 — Carbon footprint declaration",
        "effective_date": "2025-08-18",
        "applicability": ["EV batteries", "industrial batteries ≥2 kWh", "LMT batteries"],
        "description": "Lifecycle carbon footprint declaration (cradle-to-gate minimum; cradle-to-grave preferred)",
        "performance_classes": ["A", "B", "C", "D", "E", "F"],
    },
    "recycled_content_declaration": {
        "article": "Art 8 — Recycled content",
        "targets": {
            "2025": {"cobalt": 16, "lead": 85, "lithium": 6,  "nickel": 6},
            "2030": {"cobalt": 26, "lead": 85, "lithium": 12, "nickel": 15},
            "2035": {"cobalt": 26, "lead": 85, "lithium": 20, "nickel": 15},
        },
        "description": "Minimum recycled content thresholds for active materials (% by weight)",
    },
    "supply_chain_due_diligence": {
        "article": "Art 52-54 — Economic operator due diligence",
        "effective_date": "2025-08-18",
        "priority_substances": ["cobalt", "natural_graphite", "lithium", "nickel"],
        "description": "OECD-aligned supply chain DD policy + implementation + third-party audit + disclosure",
    },
    "battery_passport": {
        "article": "Art 38-42 — Battery passport",
        "effective_date": "2027-02-18",
        "applicability": ["EV batteries", "industrial batteries ≥2 kWh"],
        "description": "Unique battery identifier + QR code linking to Passport data set",
    },
    "state_of_health": {
        "article": "Art 14 — State of health and expected lifetime",
        "description": "SoH indicator accessible to owners, independent aggregators, repair/re-use operators",
    },
    "performance_durability": {
        "article": "Art 10 — Performance and durability parameters",
        "description": "Minimum capacity retention (80% at 1000 cycles for portable; 70% at 700 cycles for EV)",
    },
    "labelling": {
        "article": "Art 13 — Labelling",
        "effective_date": "2026-02-18",
        "description": "Carbon footprint class label, recycled content label, capacity, chemistry, QR code",
    },
    "end_of_life_management": {
        "article": "Art 60-65 — Collection, treatment, recycling",
        "description": (
            "Recovery efficiency targets: Li 70% by 2027, 80% by 2031; Co/Ni/Cu 90%; Pb 95%; "
            "collection rate 45% by 2023, 63% by 2027, 73% by 2030"
        ),
    },
}

# ---------------------------------------------------------------------------
# 5. EPR Levy Rates (EUR per tonne) — 20 EU Member States
#    Source: national EPR scheme data (textiles/electronics/packaging 2024 rates)
# ---------------------------------------------------------------------------

EPR_LEVY_RATES: Dict[str, Dict[str, float]] = {
    "DE": {"textiles": 450, "electronics": 380, "packaging": 280, "furniture": 200},
    "FR": {"textiles": 380, "electronics": 340, "packaging": 250, "furniture": 180},
    "IT": {"textiles": 310, "electronics": 290, "packaging": 210, "furniture": 150},
    "ES": {"textiles": 290, "electronics": 270, "packaging": 195, "furniture": 140},
    "NL": {"textiles": 420, "electronics": 360, "packaging": 265, "furniture": 190},
    "BE": {"textiles": 400, "electronics": 350, "packaging": 260, "furniture": 185},
    "SE": {"textiles": 480, "electronics": 410, "packaging": 300, "furniture": 215},
    "PL": {"textiles": 220, "electronics": 200, "packaging": 150, "furniture": 110},
    "AT": {"textiles": 390, "electronics": 340, "packaging": 255, "furniture": 175},
    "DK": {"textiles": 460, "electronics": 395, "packaging": 290, "furniture": 205},
    "FI": {"textiles": 440, "electronics": 375, "packaging": 280, "furniture": 200},
    "PT": {"textiles": 260, "electronics": 240, "packaging": 175, "furniture": 125},
    "CZ": {"textiles": 195, "electronics": 180, "packaging": 140, "furniture": 100},
    "RO": {"textiles": 165, "electronics": 155, "packaging": 120, "furniture": 85},
    "HU": {"textiles": 180, "electronics": 165, "packaging": 130, "furniture": 95},
    "GR": {"textiles": 230, "electronics": 215, "packaging": 160, "furniture": 115},
    "SK": {"textiles": 175, "electronics": 160, "packaging": 125, "furniture": 90},
    "HR": {"textiles": 155, "electronics": 145, "packaging": 115, "furniture": 82},
    "IE": {"textiles": 360, "electronics": 315, "packaging": 235, "furniture": 165},
    "LU": {"textiles": 430, "electronics": 370, "packaging": 275, "furniture": 195},
}

# ---------------------------------------------------------------------------
# 6. Circularity Scoring Criteria — 5 dimensions + weights
# ---------------------------------------------------------------------------

CIRCULARITY_SCORING_CRITERIA: Dict[str, Dict[str, Any]] = {
    "recycled_content": {
        "weight": 0.25,
        "description": "Share of recycled/secondary material in total product weight",
        "benchmark_high": 50,   # % to score 90+
        "benchmark_low": 5,     # % to score <30
        "eu_target_ref": "ESPR Annex I; Packaging Reg (EU) 2025/40",
    },
    "recyclability": {
        "weight": 0.25,
        "description": "Technical recyclability of product at end of life (design for recycling)",
        "benchmark_high": 80,
        "benchmark_low": 20,
        "eu_target_ref": "ESPR Art 5(1)(d); ISO 14021",
    },
    "durability": {
        "weight": 0.20,
        "description": "Expected functional lifetime vs category benchmark",
        "benchmark_high": 15,   # years for score 90+
        "benchmark_low": 2,
        "eu_target_ref": "ESPR Art 5(1)(b)",
    },
    "repairability": {
        "weight": 0.20,
        "description": "Repairability score (access to spare parts, repair manuals, diagnostics)",
        "benchmark_high": 8.0,  # out of 10
        "benchmark_low": 2.0,
        "eu_target_ref": "ESPR Art 5(1)(c); Ecodesign Reg (EU) 2019/2021",
    },
    "material_efficiency": {
        "weight": 0.10,
        "description": "Material yield / product-to-waste ratio in manufacturing",
        "benchmark_high": 95,   # %
        "benchmark_low": 50,
        "eu_target_ref": "ESPR Art 5(1)(a)",
    },
}


# ---------------------------------------------------------------------------
# Engine Class
# ---------------------------------------------------------------------------

class DigitalProductPassportEngine:
    """
    E82 — Digital Product Passport & Lifecycle Finance Engine (EU ESPR).

    All public methods return a plain Python dict that maps directly to
    migration 078 table columns.
    """

    # ------------------------------------------------------------------
    # 1. ESPR Compliance Assessment
    # ------------------------------------------------------------------

    def assess_espr_compliance(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess ESPR (Regulation (EU) 2024/1781) applicability and compliance
        for a given product.

        Args:
            product_data: must include 'product_category', optionally
                          'gtin_ean', 'market_regions', 'existing_certifications'.

        Returns:
            dict with fields: espr_applicable, regulation_ref, applicable_requirements,
                               compliance_score (0-100), compliance_gaps, dpp_mandatory_year,
                               priority_group, current_year_gap_years, assessed_at.
        """
        category = product_data.get("product_category", "").lower()
        cat_data = ESPR_PRODUCT_CATEGORIES.get(category)

        if cat_data is None:
            return {
                "espr_applicable": False,
                "regulation_ref": "Regulation (EU) 2024/1781",
                "applicable_requirements": [],
                "compliance_score": 0,
                "compliance_gaps": [f"Product category '{category}' not yet in ESPR scope"],
                "dpp_mandatory_year": None,
                "priority_group": None,
                "current_year_gap_years": None,
                "assessed_at": datetime.utcnow().isoformat(),
            }

        existing_certs = product_data.get("existing_certifications", [])
        requirements = cat_data["key_requirements"]
        met_requirements: List[str] = []
        gaps: List[str] = []

        # Simple heuristic — real implementations would check evidence docs
        cert_coverage = min(len(existing_certs) * 20, 60)
        base_score = cert_coverage

        # Check for explicitly provided data points
        for req in requirements:
            if any(k in req for k in ["recycled content", "carbon footprint", "labelling"]):
                if product_data.get("recycled_content_pct") or product_data.get("carbon_footprint_kg"):
                    met_requirements.append(req)
                    base_score += 8
                else:
                    gaps.append(f"Missing data: {req}")
            elif "hazardous" in req or "SVHC" in req:
                if product_data.get("hazardous_substance_list"):
                    met_requirements.append(req)
                    base_score += 5
                else:
                    gaps.append(f"Missing data: {req}")
            else:
                gaps.append(f"Not yet assessed: {req}")

        compliance_score = min(round(base_score), 100)
        current_year = 2026
        mandatory_year = cat_data["dpp_mandatory_year"]

        return {
            "espr_applicable": True,
            "regulation_ref": cat_data["regulation_ref"],
            "eu_reg_basis": cat_data["eu_reg_basis"],
            "pef_category_rule": cat_data["pef_category_rule"],
            "applicable_requirements": requirements,
            "requirements_met": met_requirements,
            "compliance_score": compliance_score,
            "compliance_gaps": gaps,
            "dpp_mandatory_year": mandatory_year,
            "priority_group": category in ["textiles", "electronics", "batteries", "steel", "aluminium", "packaging"],
            "current_year_gap_years": max(0, mandatory_year - current_year),
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 2. DPP Schema Builder
    # ------------------------------------------------------------------

    def build_dpp_schema(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate completeness of a product's Digital Product Passport data
        against the 25 mandatory DPP fields.

        Args:
            product_data: dict where keys may include field names from DPP_MANDATORY_FIELDS.
                          May also include 'available_data' (dict field_id → bool).

        Returns:
            dict with completeness_pct, mandatory_fields_completed, missing_fields,
                 schema_version, gap_list, dpp_readiness_level.
        """
        available = product_data.get("available_data", {})

        completed: List[str] = []
        missing: List[Dict[str, str]] = []

        for field in DPP_MANDATORY_FIELDS:
            fid = field["field_id"]
            fname = field["name"]

            if available.get(fid) or available.get(fname) or product_data.get(fname):
                completed.append(fid)
            else:
                missing.append({"field_id": fid, "name": fname, "section": field["section"]})

        total = len(DPP_MANDATORY_FIELDS)
        completeness_pct = round(len(completed) / total * 100, 1)

        if completeness_pct >= 90:
            readiness_level = "DPP-Ready"
        elif completeness_pct >= 70:
            readiness_level = "DPP-In-Progress"
        elif completeness_pct >= 40:
            readiness_level = "DPP-Partial"
        else:
            readiness_level = "DPP-Not-Started"

        gap_list = [f"{f['field_id']}: {f['name']} ({f['section']})" for f in missing]

        return {
            "completeness_pct": completeness_pct,
            "mandatory_fields_total": total,
            "mandatory_fields_completed": len(completed),
            "completed_field_ids": completed,
            "missing_fields": missing,
            "gap_list": gap_list,
            "schema_version": "DPP-EU-v1.0-draft-2025",
            "dpp_readiness_level": readiness_level,
            "eu_reg_basis": "Regulation (EU) 2024/1781 Art 8; Commission DPP schema draft Q1 2025",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 3. Lifecycle GHG Calculator
    # ------------------------------------------------------------------

    def calculate_lifecycle_ghg(
        self,
        product_data: Dict[str, Any],
        lifecycle_stages: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate product carbon footprint per ISO 14067:2018 / PEF methodology.

        Args:
            product_data: must include 'product_category', 'annual_units'.
                          Optionally 'product_weight_kg', 'transport_km'.
            lifecycle_stages: optional override of kg CO2e per unit per stage.
                              Keys: raw_materials, manufacturing, transport,
                                    use_phase, end_of_life.

        Returns:
            dict with stage breakdown, total_kg_co2e_per_unit, scope classification,
                 annual_total_tco2e, lca_method, system_boundary.
        """
        category = product_data.get("product_category", "_default").lower()
        efs = LCA_EMISSION_FACTORS.get(category, LCA_EMISSION_FACTORS["_default"])

        annual_units = max(1, float(product_data.get("annual_units", 1000)))

        # Use override or defaults
        stage_override = lifecycle_stages or {}
        stages = {k: stage_override.get(k, efs[k]) for k in efs}

        # Weight adjustment if product_weight_kg provided
        weight_factor = float(product_data.get("product_weight_kg", 1.0))

        stage_emissions: Dict[str, float] = {}
        for stage, base_ef in stages.items():
            # For product categories where EF is already per-unit, weight_factor = 1
            # For material categories (steel, cement) where EF is per tonne, scale by weight
            if category in ["steel", "cement", "aluminium", "chemicals"]:
                stage_emissions[stage] = round(base_ef * weight_factor / 1000, 4)  # convert kg→tonne
            else:
                stage_emissions[stage] = round(base_ef, 4)

        total_per_unit = sum(stage_emissions.values())

        # GHG Protocol / PEF scope allocation
        scope1 = stage_emissions.get("manufacturing", 0) * 0.3
        scope2 = stage_emissions.get("manufacturing", 0) * 0.7 + stage_emissions.get("use_phase", 0) * 0.8
        scope3 = (
            stage_emissions.get("raw_materials", 0)
            + stage_emissions.get("transport", 0)
            + stage_emissions.get("use_phase", 0) * 0.2
            + stage_emissions.get("end_of_life", 0)
        )

        annual_total_tco2e = round(total_per_unit * annual_units / 1000, 2)

        return {
            "product_category": category,
            "lifecycle_stage_emissions_kg_co2e": stage_emissions,
            "total_kg_co2e_per_unit": round(total_per_unit, 4),
            "scope1_kg_co2e_per_unit": round(scope1, 4),
            "scope2_kg_co2e_per_unit": round(scope2, 4),
            "scope3_kg_co2e_per_unit": round(scope3, 4),
            "annual_units": int(annual_units),
            "annual_total_tco2e": annual_total_tco2e,
            "lca_method": "ISO 14044:2006 / ISO 14067:2018 / EU PEF",
            "system_boundary": "cradle-to-grave",
            "biogenic_carbon_included": False,
            "data_quality_tier": "Tier 2 — industry average EFs (PEF database)",
            "eu_reg_basis": "Regulation (EU) 2024/1781 Art 7(2)(d); ISO 14067; EU PEF methodology",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 4. Circularity Assessment
    # ------------------------------------------------------------------

    def assess_circularity(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute a circularity index (0-100) across 5 weighted dimensions.

        Args:
            product_data: must include recycled_content_pct, recyclability_score,
                          durability_years, repairability_score, material_efficiency_pct.

        Returns:
            dict with dimension_scores, circularity_index, improvement_potential,
                 improvement_actions.
        """
        inputs = {
            "recycled_content":   float(product_data.get("recycled_content_pct",    0)),
            "recyclability":      float(product_data.get("recyclability_score",       0)),
            "durability":         float(product_data.get("durability_years",           0)),
            "repairability":      float(product_data.get("repairability_score",        0)),
            "material_efficiency":float(product_data.get("material_efficiency_pct",   0)),
        }

        dimension_scores: Dict[str, float] = {}
        weighted_total = 0.0
        improvement_actions: List[str] = []

        for dim, criteria in CIRCULARITY_SCORING_CRITERIA.items():
            raw_val = inputs[dim]
            high = criteria["benchmark_high"]
            low = criteria["benchmark_low"]
            weight = criteria["weight"]

            # Normalise to 0-100
            if high == low:
                score = 50.0
            else:
                score = max(0.0, min(100.0, (raw_val - low) / (high - low) * 100))

            dimension_scores[dim] = round(score, 1)
            weighted_total += score * weight

            if score < 50:
                improvement_actions.append(
                    f"Improve {dim.replace('_', ' ')}: current score {score:.0f}/100 "
                    f"(target ≥80). Ref: {criteria['eu_target_ref']}"
                )

        circularity_index = round(weighted_total, 1)
        improvement_potential = round(100 - circularity_index, 1)

        if circularity_index >= 75:
            circularity_tier = "Circular Leader"
        elif circularity_index >= 55:
            circularity_tier = "Transitioning"
        elif circularity_index >= 35:
            circularity_tier = "Linear with Pockets"
        else:
            circularity_tier = "Linear"

        return {
            "dimension_scores": dimension_scores,
            "dimension_weights": {k: v["weight"] for k, v in CIRCULARITY_SCORING_CRITERIA.items()},
            "circularity_index": circularity_index,
            "circularity_tier": circularity_tier,
            "improvement_potential": improvement_potential,
            "improvement_actions": improvement_actions,
            "eu_reg_basis": "Regulation (EU) 2024/1781 Art 5; EU Circular Economy Action Plan 2020",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 5. EU Battery Regulation Assessment
    # ------------------------------------------------------------------

    def assess_battery_regulation(self, battery_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess compliance with EU Battery Regulation 2023/1542.

        Args:
            battery_data: battery_chemistry, capacity_kwh, carbon_footprint_kg_per_kwh,
                          recycled_li_pct, recycled_co_pct, recycled_ni_pct,
                          recycled_pb_pct, has_supply_chain_dd, has_battery_passport,
                          soh_accessible.

        Returns:
            dict with requirement-by-requirement compliance, recycled content gaps,
                 overall_score, compliance_tier.
        """
        chemistry = battery_data.get("battery_chemistry", "unknown")
        capacity_kwh = float(battery_data.get("capacity_kwh", 0))
        cf_kg_kwh = float(battery_data.get("carbon_footprint_kg_per_kwh", 0))

        # Recycled content — 2025 targets
        targets_2025 = EU_BATTERY_REGULATION_REQUIREMENTS["recycled_content_declaration"]["targets"]["2025"]
        targets_2030 = EU_BATTERY_REGULATION_REQUIREMENTS["recycled_content_declaration"]["targets"]["2030"]

        recycled = {
            "lithium": float(battery_data.get("recycled_li_pct",  0)),
            "cobalt":  float(battery_data.get("recycled_co_pct",  0)),
            "nickel":  float(battery_data.get("recycled_ni_pct",  0)),
            "lead":    float(battery_data.get("recycled_pb_pct",  0)),
        }

        recycled_content_checks: Dict[str, Dict[str, Any]] = {}
        for material, actual in recycled.items():
            t2025 = targets_2025[material]
            t2030 = targets_2030[material]
            compliant_2025 = actual >= t2025
            compliant_2030 = actual >= t2030
            recycled_content_checks[material] = {
                "actual_pct": actual,
                "target_2025_pct": t2025,
                "target_2030_pct": t2030,
                "compliant_2025": compliant_2025,
                "compliant_2030": compliant_2030,
                "gap_2025_pct": max(0.0, t2025 - actual),
            }

        # Supply chain DD
        has_dd = battery_data.get("has_supply_chain_dd", False)

        # Battery passport (required for EV / industrial ≥2 kWh from Feb 2027)
        has_passport = battery_data.get("has_battery_passport", False)
        passport_required = capacity_kwh >= 2.0

        # SoH accessibility
        soh_accessible = battery_data.get("soh_accessible", False)

        # Compliance score
        checks_passed = sum([
            cf_kg_kwh > 0,                                      # carbon footprint declared
            all(v["compliant_2025"] for v in recycled_content_checks.values()),  # recycled content
            has_dd,                                             # supply chain DD
            (has_passport or not passport_required),            # battery passport
            soh_accessible,                                     # SoH accessible
        ])

        overall_score = round(checks_passed / 5 * 100)

        if overall_score >= 80:
            compliance_tier = "Compliant"
        elif overall_score >= 60:
            compliance_tier = "Partially Compliant"
        else:
            compliance_tier = "Non-Compliant"

        return {
            "battery_chemistry": chemistry,
            "capacity_kwh": capacity_kwh,
            "carbon_footprint_declared": cf_kg_kwh > 0,
            "carbon_footprint_kg_per_kwh": cf_kg_kwh,
            "recycled_content_checks": recycled_content_checks,
            "supply_chain_dd_present": has_dd,
            "battery_passport_required": passport_required,
            "battery_passport_present": has_passport,
            "soh_accessible": soh_accessible,
            "overall_score": overall_score,
            "compliance_tier": compliance_tier,
            "eu_reg_basis": "Regulation (EU) 2023/1542 Art 7, 8, 14, 38-65",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 6. EPR Levy Calculator
    # ------------------------------------------------------------------

    def calculate_epr_levy(
        self, product_data: Dict[str, Any], countries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate EPR scheme levy exposure across EU Member States.

        Args:
            product_data: product_category, annual_volume_tonnes.
            countries: list of ISO 3166-1 alpha-2 country codes (default: all 20).

        Returns:
            dict with per_country_levy_eur, total_eu_exposure_eur,
                 exemption_assessment, highest_levy_country.
        """
        category = product_data.get("product_category", "packaging").lower()
        annual_tonnes = float(product_data.get("annual_volume_tonnes", 100))
        target_countries = countries or list(EPR_LEVY_RATES.keys())

        per_country: Dict[str, float] = {}
        for cc in target_countries:
            rates = EPR_LEVY_RATES.get(cc.upper())
            if rates is None:
                continue
            rate = rates.get(category, rates.get("packaging", 250))
            per_country[cc.upper()] = round(rate * annual_tonnes, 2)

        total_eu = round(sum(per_country.values()), 2)
        highest = max(per_country, key=per_country.get) if per_country else None

        # SME exemption check (rough threshold — varies by state)
        annual_turnover = float(product_data.get("annual_turnover_eur", 10_000_000))
        sme_exemption_eligible = annual_turnover < 2_000_000 or annual_tonnes < 1.0

        return {
            "product_category": category,
            "annual_volume_tonnes": annual_tonnes,
            "per_country_levy_eur": per_country,
            "total_eu_exposure_eur": total_eu,
            "highest_levy_country": highest,
            "highest_levy_eur": per_country.get(highest, 0) if highest else 0,
            "sme_exemption_eligible": sme_exemption_eligible,
            "exemption_note": (
                "SME exemption thresholds vary by Member State. "
                "Confirm with national EPR scheme operator."
            ),
            "eu_reg_basis": "Directive 2008/98/EC Art 8a; national EPR transpositions (2021-2024)",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 7. Full Assessment Orchestrator
    # ------------------------------------------------------------------

    def run_full_assessment(
        self, entity_id: str, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate all sub-modules and compute composite dpp_readiness_score.

        Weighting:
            ESPR compliance    40%
            DPP schema         25%
            LCA / carbon       20%
            Circularity        15%

        Returns:
            full_result dict with all sub-results + composite scores + espr_tier.
        """
        assessment_id = str(uuid.uuid4())
        logger.info(
            "DPP full assessment started: entity=%s assessment=%s category=%s",
            entity_id,
            assessment_id,
            product_data.get("product_category"),
        )

        espr = self.assess_espr_compliance(product_data)
        dpp = self.build_dpp_schema(product_data)
        lca = self.calculate_lifecycle_ghg(product_data)
        circ = self.assess_circularity(product_data)

        # Battery sub-assessment if applicable
        battery_result: Optional[Dict] = None
        if product_data.get("product_category") == "batteries" or product_data.get("battery_chemistry"):
            battery_result = self.assess_battery_regulation(product_data)

        # EPR levy if volume provided
        epr_result: Optional[Dict] = None
        if product_data.get("annual_volume_tonnes"):
            epr_result = self.calculate_epr_levy(product_data)

        # Composite dpp_readiness_score
        espr_score = espr.get("compliance_score", 0) * 0.40
        dpp_score = dpp.get("completeness_pct", 0) * 0.25
        # LCA score — penalise if missing data (no annual_units)
        lca_score_raw = min(100, max(0, 100 - lca.get("total_kg_co2e_per_unit", 0) / 10))
        lca_score = lca_score_raw * 0.20
        circ_score = circ.get("circularity_index", 0) * 0.15

        dpp_readiness_score = round(espr_score + dpp_score + lca_score + circ_score, 1)

        if dpp_readiness_score >= 75:
            espr_tier = "Ready"
        elif dpp_readiness_score >= 55:
            espr_tier = "In Progress"
        elif dpp_readiness_score >= 35:
            espr_tier = "At Risk"
        else:
            espr_tier = "Non-Compliant"

        result: Dict[str, Any] = {
            "assessment_id": assessment_id,
            "entity_id": entity_id,
            "product_name": product_data.get("product_name", ""),
            "product_category": product_data.get("product_category", ""),
            "dpp_readiness_score": dpp_readiness_score,
            "espr_tier": espr_tier,
            "component_scores": {
                "espr_compliance_40pct": round(espr_score, 1),
                "dpp_schema_25pct": round(dpp_score, 1),
                "lca_20pct": round(lca_score, 1),
                "circularity_15pct": round(circ_score, 1),
            },
            "espr_assessment": espr,
            "dpp_schema_assessment": dpp,
            "lifecycle_ghg_assessment": lca,
            "circularity_assessment": circ,
            "battery_regulation_assessment": battery_result,
            "epr_levy_assessment": epr_result,
            "regulation_refs": [
                "Regulation (EU) 2024/1781 (ESPR)",
                "Regulation (EU) 2023/1542 (Battery Regulation)",
                "ISO 14044:2006; ISO 14067:2018",
                "Packaging Regulation (EU) 2025/40",
                "Directive 2008/98/EC (EPR)",
            ],
            "assessed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "DPP full assessment complete: entity=%s readiness_score=%.1f tier=%s",
            entity_id,
            dpp_readiness_score,
            espr_tier,
        )
        return result
