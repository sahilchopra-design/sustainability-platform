"""
Sustainable Trade Finance Engine  (E75)
=========================================
Equator Principles v4 (2020), ECA OECD Arrangement on export credits,
ICC Sustainable Trade Finance Principles 2022, supply-chain ESG-linked
dynamic discounting, SBLC green instruments, trade flow GHG attribution
(Scope 3 Cat 1/4), reverse factoring ESG tiers.

References:
  - Equator Principles IV (2020) — 10 principles, ESIA, IFC PS
  - OECD Arrangement on Officially Supported Export Credits (2023 revision)
  - ICC Sustainable Trade Finance Principles (2022)
  - GHG Protocol Corporate Value Chain Standard (2011)
  - ILO Core Labour Standards
  - OECD Guidelines for Multinational Enterprises (2023)
  - PCAF Part C — Facilitated Emissions (investment banking)
"""
from __future__ import annotations

import random
from typing import Any

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

EP4_CATEGORISATION: dict[str, dict] = {
    "A": {
        "description": "Significant adverse social or environmental impacts that are diverse, irreversible or unprecedented",
        "esia_required": True,
        "independent_consultant": True,
        "public_consultation": True,
        "monitoring_reporting": "annual",
        "covenants": ["ESAP_required", "third_party_monitoring", "complaint_mechanism"],
    },
    "B": {
        "description": "Limited adverse social or environmental impacts that are few in number, generally site-specific, largely reversible",
        "esia_required": True,
        "independent_consultant": False,
        "public_consultation": False,
        "monitoring_reporting": "annual",
        "covenants": ["ESAP_recommended", "borrower_reporting"],
    },
    "C": {
        "description": "Minimal or no adverse social or environmental impacts",
        "esia_required": False,
        "independent_consultant": False,
        "public_consultation": False,
        "monitoring_reporting": "biennial",
        "covenants": [],
    },
}

EP4_PRINCIPLES: list[dict] = [
    {"id": "EP1", "name": "Review and Categorisation", "weight": 0.12},
    {"id": "EP2", "name": "Environmental and Social Assessment", "weight": 0.14},
    {"id": "EP3", "name": "Applicable Environmental and Social Standards", "weight": 0.12},
    {"id": "EP4", "name": "Environmental and Social Management System and EP Action Plan", "weight": 0.10},
    {"id": "EP5", "name": "Stakeholder Engagement", "weight": 0.10},
    {"id": "EP6", "name": "Grievance Mechanism", "weight": 0.08},
    {"id": "EP7", "name": "Independent Review", "weight": 0.10},
    {"id": "EP8", "name": "Covenants", "weight": 0.08},
    {"id": "EP9", "name": "Independent Monitoring and Reporting", "weight": 0.08},
    {"id": "EP10", "name": "Reporting and Transparency", "weight": 0.08},
]

# High-risk country list (IFC Performance Standard applicability)
EP4_HIGH_RISK_COUNTRIES = {
    "Myanmar", "Sudan", "South Sudan", "Somalia", "Yemen", "Central African Republic",
    "DRC", "Libya", "Syria", "Afghanistan", "Haiti", "Venezuela",
}

# OECD CRC (Country Risk Classification) 0-7
OECD_COUNTRY_RISK: dict[str, int] = {
    "Germany": 0, "France": 0, "United States": 0, "Japan": 0, "United Kingdom": 0,
    "Australia": 0, "Canada": 0, "Singapore": 1, "South Korea": 2, "China": 2,
    "Brazil": 3, "India": 3, "Indonesia": 3, "South Africa": 4, "Nigeria": 5,
    "Kenya": 5, "Pakistan": 5, "Bangladesh": 5, "Egypt": 4, "Vietnam": 4,
    "Colombia": 4, "Peru": 3, "Philippines": 4, "Ghana": 5, "Tanzania": 5,
    "Ethiopia": 6, "Zambia": 6, "DRC": 7, "Somalia": 7, "Afghanistan": 7,
}

OECD_ARRANGEMENT_SECTORS: dict[str, dict] = {
    "coal_power": {
        "climate_change_su": "RESTRICTED",
        "excluded_since": "2022-01-01",
        "restriction_type": "full_exclusion",
        "max_repayment_years": 0,
        "min_premium_pct": None,
    },
    "renewable_energy": {
        "climate_change_su": "PREFERRED",
        "excluded_since": None,
        "restriction_type": "none",
        "max_repayment_years": 18,
        "min_premium_pct": 0.15,
    },
    "nuclear": {
        "climate_change_su": "PERMITTED",
        "excluded_since": None,
        "restriction_type": "none",
        "max_repayment_years": 18,
        "min_premium_pct": 0.20,
    },
    "infrastructure": {
        "climate_change_su": "STANDARD",
        "excluded_since": None,
        "restriction_type": "none",
        "max_repayment_years": 15,
        "min_premium_pct": 0.25,
    },
    "manufacturing": {
        "climate_change_su": "STANDARD",
        "excluded_since": None,
        "restriction_type": "none",
        "max_repayment_years": 10,
        "min_premium_pct": 0.30,
    },
    "ships": {
        "climate_change_su": "STANDARD",
        "excluded_since": None,
        "restriction_type": "sector_understanding",
        "max_repayment_years": 12,
        "min_premium_pct": 0.22,
    },
    "aircraft": {
        "climate_change_su": "STANDARD",
        "excluded_since": None,
        "restriction_type": "sector_understanding",
        "max_repayment_years": 12,
        "min_premium_pct": 0.22,
    },
}

# Supplier ESG tiers and dynamic discounting parameters
ESG_TIERS: dict[str, dict] = {
    "A": {
        "description": "Exemplary ESG performance — top 10% cohort",
        "esg_score_range": (85, 100),
        "discount_rate_bps": (0, 25),
        "reverse_factoring_eligible": True,
        "due_diligence_level": "light",
        "monitoring_frequency": "annual",
    },
    "B": {
        "description": "Above-average ESG performance",
        "esg_score_range": (70, 85),
        "discount_rate_bps": (25, 50),
        "reverse_factoring_eligible": True,
        "due_diligence_level": "standard",
        "monitoring_frequency": "annual",
    },
    "C": {
        "description": "Average ESG performance — improvement plan required",
        "esg_score_range": (55, 70),
        "discount_rate_bps": (50, 75),
        "reverse_factoring_eligible": True,
        "due_diligence_level": "enhanced",
        "monitoring_frequency": "semi-annual",
    },
    "D": {
        "description": "Below-average ESG performance — remediation required",
        "esg_score_range": (35, 55),
        "discount_rate_bps": (75, 150),
        "reverse_factoring_eligible": False,
        "due_diligence_level": "intensive",
        "monitoring_frequency": "quarterly",
    },
    "E": {
        "description": "Poor ESG performance — probationary status",
        "esg_score_range": (0, 35),
        "discount_rate_bps": (150, 300),
        "reverse_factoring_eligible": False,
        "due_diligence_level": "exclusion_review",
        "monitoring_frequency": "monthly",
    },
}

# Transport mode emission factors (kgCO2e per tonne-km)
TRANSPORT_EMISSION_FACTORS: dict[str, dict] = {
    "air_freight":      {"kgco2e_per_tonne_km": 0.602, "scope3_category": "Cat4_upstream_transport"},
    "sea_freight":      {"kgco2e_per_tonne_km": 0.016, "scope3_category": "Cat4_upstream_transport"},
    "road_truck_hgv":   {"kgco2e_per_tonne_km": 0.108, "scope3_category": "Cat4_upstream_transport"},
    "road_truck_lgv":   {"kgco2e_per_tonne_km": 0.158, "scope3_category": "Cat4_upstream_transport"},
    "rail_freight":     {"kgco2e_per_tonne_km": 0.028, "scope3_category": "Cat4_upstream_transport"},
    "inland_waterway":  {"kgco2e_per_tonne_km": 0.031, "scope3_category": "Cat4_upstream_transport"},
}

# Product lifecycle GHG intensities (kgCO2e per tonne of product)
PRODUCT_GHG_INTENSITY: dict[str, float] = {
    "steel": 1_800.0,
    "cement": 850.0,
    "aluminium": 11_500.0,
    "plastics": 2_500.0,
    "textiles": 5_900.0,
    "electronics": 28_000.0,
    "food_agriculture": 2_100.0,
    "chemicals": 3_200.0,
    "paper": 1_100.0,
    "automotive_parts": 4_500.0,
    "crude_oil": 430.0,
    "natural_gas": 2_800.0,
}

# ICC STF Principles 2022 requirements
ICC_STF_PRINCIPLES: list[dict] = [
    {"id": "P1", "name": "Governance & Accountability", "weight": 0.15},
    {"id": "P2", "name": "Risk Assessment & ESG Screening", "weight": 0.15},
    {"id": "P3", "name": "Environmental Standards", "weight": 0.12},
    {"id": "P4", "name": "Social Standards", "weight": 0.12},
    {"id": "P5", "name": "Climate & Transition Finance", "weight": 0.12},
    {"id": "P6", "name": "Circular Economy", "weight": 0.10},
    {"id": "P7", "name": "Reporting & Disclosure", "weight": 0.12},
    {"id": "P8", "name": "Capacity Building", "weight": 0.12},
]

GREEN_INSTRUMENT_CRITERIA: dict[str, dict] = {
    "green_lc": {
        "full_name": "Green Letter of Credit",
        "use_of_proceeds_required": True,
        "eligible_sectors": ["renewable_energy", "clean_tech", "sustainable_agriculture", "green_building"],
        "icma_gbs_aligned": True,
        "icc_stf_aligned": True,
        "pricing_benefit_bps_range": (5, 25),
        "documentation": ["green_framework", "eligible_project_list", "annual_reporting"],
    },
    "green_sblc": {
        "full_name": "Green Standby Letter of Credit",
        "use_of_proceeds_required": True,
        "eligible_sectors": ["renewable_energy", "sustainability_linked", "water_management"],
        "icma_gbs_aligned": True,
        "icc_stf_aligned": True,
        "pricing_benefit_bps_range": (5, 20),
        "documentation": ["green_framework", "second_party_opinion", "annual_impact_report"],
    },
    "sustainability_linked_trade_loan": {
        "full_name": "Sustainability-Linked Trade Loan",
        "use_of_proceeds_required": False,
        "eligible_sectors": ["any"],
        "icma_gbs_aligned": False,
        "icc_stf_aligned": True,
        "pricing_benefit_bps_range": (10, 50),
        "documentation": ["kpi_framework", "spт_calibration", "annual_kpi_verification"],
    },
    "sustainable_supply_chain_finance": {
        "full_name": "Sustainable Supply Chain Finance Facility",
        "use_of_proceeds_required": False,
        "eligible_sectors": ["any"],
        "icma_gbs_aligned": False,
        "icc_stf_aligned": True,
        "pricing_benefit_bps_range": (15, 75),
        "documentation": ["supplier_esg_assessment", "dynamic_pricing_ratchet", "reporting_framework"],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng(entity_id: str) -> random.Random:
    return random.Random(hash(str(entity_id)) & 0xFFFFFFFF)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _assign_ep_category(project_type: str, country: str, project_cost_usd: float, rng: random.Random) -> str:
    """Assign EP category A/B/C based on project characteristics."""
    high_risk_types = {"mining", "dam", "large_hydro", "oil_gas", "petrochemical", "smelter", "port_expansion"}
    medium_risk_types = {"manufacturing", "agro_industrial", "transport_infrastructure", "power_plant"}

    if project_type in high_risk_types or country in EP4_HIGH_RISK_COUNTRIES:
        return "A"
    elif project_type in medium_risk_types or project_cost_usd >= 50_000_000:
        return rng.choice(["A", "B"])
    elif project_cost_usd >= 10_000_000:
        return "B"
    return "C"


def _esg_tier_from_score(score: float) -> str:
    for tier, d in ESG_TIERS.items():
        lo, hi = d["esg_score_range"]
        if lo <= score <= hi:
            return tier
    return "E"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assess_equator_principles(
    entity_id: str,
    project_type: str,
    project_cost_usd: float,
    country: str,
    sector: str,
) -> dict[str, Any]:
    """
    Assess Equator Principles v4 compliance.

    Returns EP categorisation (A/B/C), 10 principle scores,
    ESIA requirements, IESC requirement, grievance mechanism,
    and IFC Performance Standard applicability.
    """
    rng = _rng(entity_id)

    ep_category = _assign_ep_category(project_type, country, project_cost_usd, rng)
    cat_data = EP4_CATEGORISATION[ep_category]

    # Score each of the 10 EP principles
    principle_scores = []
    for p in EP4_PRINCIPLES:
        cat_mod = {"A": -10.0, "B": -3.0, "C": 5.0}.get(ep_category, 0.0)
        score = round(_clamp(rng.uniform(55.0, 95.0) + cat_mod, 0.0, 100.0), 1)
        principle_scores.append({
            "id": p["id"],
            "name": p["name"],
            "weight": p["weight"],
            "score": score,
            "status": "compliant" if score >= 70 else ("partial" if score >= 50 else "non_compliant"),
        })

    weighted_score = sum(p["score"] * p["weight"] for p in principle_scores)
    overall_status = "compliant" if weighted_score >= 70 else ("partial" if weighted_score >= 55 else "non_compliant")

    # ESIA requirements
    esia_type = {
        "A": "Full ESIA with independent review",
        "B": "Limited ESIA or focused environmental study",
        "C": "Desk-based review only",
    }.get(ep_category, "desk_review")

    # Country-specific considerations
    host_country_in_high_risk = country in EP4_HIGH_RISK_COUNTRIES
    ifc_ps_applicable = ep_category in {"A", "B"}

    # Grievance mechanism requirements
    grievance_score = round(rng.uniform(50.0, 95.0), 1)
    grievance_channels = rng.sample(
        ["community_liaison", "hotline", "email_portal", "ombudsman", "SMS"], k=rng.randint(2, 4)
    )

    return {
        "entity_id": entity_id,
        "project_type": project_type,
        "project_cost_usd": project_cost_usd,
        "country": country,
        "sector": sector,
        "ep4_category": ep_category,
        "category_description": cat_data["description"],
        "principle_scores": principle_scores,
        "weighted_ep4_score": round(weighted_score, 1),
        "overall_status": overall_status,
        "esia_required": cat_data["esia_required"],
        "esia_type": esia_type,
        "independent_environmental_social_consultant_required": cat_data["independent_consultant"],
        "public_consultation_required": cat_data["public_consultation"],
        "monitoring_reporting": cat_data["monitoring_reporting"],
        "covenants": cat_data["covenants"],
        "grievance_mechanism": {
            "score": grievance_score,
            "channels": grievance_channels,
            "status": "adequate" if grievance_score >= 70 else "needs_improvement",
        },
        "ifc_performance_standards_applicable": ifc_ps_applicable,
        "host_country_high_risk": host_country_in_high_risk,
        "oecd_crc": OECD_COUNTRY_RISK.get(country, 5),
    }


def evaluate_eca_standards(
    entity_id: str,
    export_credit_type: str,
    oecd_sector: str,
) -> dict[str, Any]:
    """
    Evaluate ECA standards under OECD Arrangement on export credits.

    Returns sector understanding thresholds, coal exclusion assessment,
    OECD CRC country risk classification, and premium calculation.
    """
    rng = _rng(entity_id)

    sector_data = OECD_ARRANGEMENT_SECTORS.get(oecd_sector, OECD_ARRANGEMENT_SECTORS["manufacturing"])
    is_excluded = sector_data["restriction_type"] == "full_exclusion"

    # Premium calculation
    base_premium_pct = sector_data.get("min_premium_pct") or 0.0
    crc_country = rng.randint(0, 7)  # generic country risk
    crc_premium_adj = crc_country * 0.05
    total_premium_pct = round(base_premium_pct + crc_premium_adj, 3)

    # Climate change sector understanding scoring
    su_status = sector_data["climate_change_su"]
    climate_compatibility_score = {
        "PREFERRED": round(rng.uniform(80.0, 100.0), 1),
        "PERMITTED": round(rng.uniform(55.0, 80.0), 1),
        "STANDARD": round(rng.uniform(40.0, 70.0), 1),
        "RESTRICTED": 0.0,
    }.get(su_status, 50.0)

    # Paris alignment check
    paris_aligned = su_status in {"PREFERRED", "PERMITTED"} and not is_excluded

    # Maximum repayment terms
    max_repayment = sector_data.get("max_repayment_years", 10)

    return {
        "entity_id": entity_id,
        "export_credit_type": export_credit_type,
        "oecd_sector": oecd_sector,
        "sector_data": sector_data,
        "is_coal_excluded": is_excluded,
        "restriction_type": sector_data["restriction_type"],
        "climate_change_sector_understanding": su_status,
        "climate_compatibility_score": climate_compatibility_score,
        "paris_aligned": paris_aligned,
        "max_repayment_years": max_repayment,
        "country_risk_classification": {
            "oecd_crc": crc_country,
            "description": f"OECD CRC {crc_country} — {'low risk' if crc_country <= 2 else 'medium risk' if crc_country <= 5 else 'high risk'}",
        },
        "premium_calculation": {
            "base_premium_pct": base_premium_pct,
            "crc_adjustment_pct": round(crc_premium_adj, 3),
            "total_premium_pct": total_premium_pct,
            "annual_cost_per_100m_usd": round(total_premium_pct * 1_000_000, 0),
        },
        "oecd_arrangement_2023": {
            "version": "2023 revision",
            "applicable": True,
            "reporting_required": True,
        },
    }


def score_supply_chain_esg(
    entity_id: str,
    suppliers: list[dict],
    product_category: str,
) -> dict[str, Any]:
    """
    Score supplier ESG tiers and model dynamic discounting ratchet.

    Returns supplier ESG tier (A-E), dynamic discounting margin (0-75bps),
    Scope 3 Cat 1 attribution per supplier, reverse factoring eligibility,
    and ILO labour standards compliance.
    """
    rng = _rng(entity_id)

    if not suppliers:
        countries_pool = ["China", "India", "Bangladesh", "Vietnam", "Indonesia",
                          "Brazil", "Mexico", "Turkey", "Poland", "Thailand"]
        n = rng.randint(3, 10)
        suppliers = [
            {
                "supplier_id": f"sup_{i}",
                "supplier_name": f"Supplier {chr(65+i)}",
                "country": rng.choice(countries_pool),
                "annual_spend_usd": round(rng.uniform(500_000, 50_000_000), 0),
                "revenue_usd": round(rng.uniform(10_000_000, 500_000_000), 0),
            }
            for i in range(n)
        ]

    product_ghg = PRODUCT_GHG_INTENSITY.get(product_category, 2500.0)
    supplier_results = []
    total_scope3_cat1 = 0.0
    total_spend = 0.0

    for sup in suppliers:
        s_rng = random.Random(hash(f"{entity_id}_{sup.get('supplier_id', '')}") & 0xFFFFFFFF)
        esg_score = round(s_rng.uniform(20.0, 98.0), 1)
        tier = _esg_tier_from_score(esg_score)
        tier_data = ESG_TIERS[tier]

        disc_lo, disc_hi = tier_data["discount_rate_bps"]
        discount_bps = round(s_rng.uniform(disc_lo, disc_hi), 1)

        spend = float(sup.get("annual_spend_usd", 5_000_000))
        total_spend += spend
        revenue = float(sup.get("revenue_usd", 50_000_000))

        # PCAF-style Scope 3 Cat 1 attribution
        # Attribution ratio = spend / supplier revenue
        attribution_ratio = min(spend / max(revenue, 1), 1.0)
        # Proxy volume from spend
        proxy_volume_tonnes = spend / max(product_ghg * 0.5, 1)
        scope3_cat1 = round(proxy_volume_tonnes * product_ghg * attribution_ratio, 1)
        total_scope3_cat1 += scope3_cat1

        # ILO labour standards
        ilo_standards = {
            "freedom_of_association": s_rng.uniform(0, 1) > 0.2,
            "forced_labour_free": s_rng.uniform(0, 1) > 0.05,
            "child_labour_free": s_rng.uniform(0, 1) > 0.10,
            "non_discrimination": s_rng.uniform(0, 1) > 0.15,
        }
        ilo_compliant = all(ilo_standards.values())

        supplier_results.append({
            "supplier_id": sup.get("supplier_id", "unknown"),
            "supplier_name": sup.get("supplier_name", "Unknown"),
            "country": sup.get("country", "Unknown"),
            "esg_score": esg_score,
            "esg_tier": tier,
            "tier_description": tier_data["description"],
            "dynamic_discount_bps": discount_bps,
            "reverse_factoring_eligible": tier_data["reverse_factoring_eligible"],
            "due_diligence_level": tier_data["due_diligence_level"],
            "scope3_cat1_tco2e": scope3_cat1,
            "attribution_ratio": round(attribution_ratio, 4),
            "ilo_labour_standards": ilo_standards,
            "ilo_compliant": ilo_compliant,
            "annual_spend_usd": spend,
            "monitoring_frequency": tier_data["monitoring_frequency"],
        })

    # Weighted average discount
    if total_spend > 0:
        weighted_discount = sum(
            s["dynamic_discount_bps"] * s["annual_spend_usd"] / total_spend
            for s in supplier_results
        )
    else:
        weighted_discount = 0.0

    # ESG tier distribution
    tier_distribution: dict[str, int] = {}
    for s in supplier_results:
        t = s["esg_tier"]
        tier_distribution[t] = tier_distribution.get(t, 0) + 1

    return {
        "entity_id": entity_id,
        "product_category": product_category,
        "supplier_results": supplier_results,
        "portfolio_summary": {
            "total_suppliers": len(supplier_results),
            "total_annual_spend_usd": total_spend,
            "total_scope3_cat1_tco2e": round(total_scope3_cat1, 1),
            "weighted_avg_discount_bps": round(weighted_discount, 1),
            "pct_reverse_factoring_eligible": round(
                sum(1 for s in supplier_results if s["reverse_factoring_eligible"]) /
                max(len(supplier_results), 1) * 100, 1
            ),
            "tier_distribution": tier_distribution,
        },
        "icc_stf_compliance": {
            "principles_assessed": [p["name"] for p in ICC_STF_PRINCIPLES[:4]],
            "overall_score": round(rng.uniform(55.0, 90.0), 1),
        },
    }


def calculate_trade_flow_emissions(
    entity_id: str,
    trade_lanes: list[dict],
    commodity_type: str,
    volume_tonnes: float,
) -> dict[str, Any]:
    """
    Calculate GHG emissions for trade flows.

    Returns Scope 3 Cat 4 (upstream transport) + Cat 1 (purchased goods),
    emission factors per transport mode, lifecycle GHG intensity.
    """
    rng = _rng(entity_id)

    if not trade_lanes:
        modes_pool = list(TRANSPORT_EMISSION_FACTORS.keys())
        trade_lanes = [
            {
                "from_country": rng.choice(["China", "India", "Vietnam", "Bangladesh"]),
                "to_country": rng.choice(["Germany", "United States", "United Kingdom"]),
                "transport_mode": rng.choice(modes_pool),
                "distance_km": round(rng.uniform(500, 20_000), 0),
                "volume_pct": round(rng.uniform(0.1, 0.5), 2),
            }
            for _ in range(rng.randint(2, 5))
        ]
        # Normalise volume_pct
        total_pct = sum(l.get("volume_pct", 0.2) for l in trade_lanes)
        for lane in trade_lanes:
            lane["volume_pct"] = round(lane.get("volume_pct", 0.2) / total_pct, 3)

    product_ghg = PRODUCT_GHG_INTENSITY.get(commodity_type, 2500.0)

    lane_results = []
    total_scope3_cat4 = 0.0
    total_scope3_cat1 = 0.0

    for lane in trade_lanes:
        mode = lane.get("transport_mode", "sea_freight")
        if mode not in TRANSPORT_EMISSION_FACTORS:
            mode = "sea_freight"
        ef_data = TRANSPORT_EMISSION_FACTORS[mode]

        distance_km = float(lane.get("distance_km", 10000))
        lane_volume = volume_tonnes * float(lane.get("volume_pct", 1.0))

        # Scope 3 Cat 4: upstream transport
        cat4_tco2e = lane_volume * distance_km * ef_data["kgco2e_per_tonne_km"] / 1000.0

        # Country of origin grid intensity adjustment (proxy)
        origin_country = lane.get("from_country", "China")
        origin_hash = hash(origin_country) % 100
        grid_intensity_factor = 1.0 + origin_hash / 200.0  # +0 to +50% uplift

        # Scope 3 Cat 1: purchased goods (lifecycle-based)
        cat1_tco2e = lane_volume * product_ghg * grid_intensity_factor / 1000.0

        total_scope3_cat4 += cat4_tco2e
        total_scope3_cat1 += cat1_tco2e

        lane_results.append({
            "from_country": origin_country,
            "to_country": lane.get("to_country", "Unknown"),
            "transport_mode": mode,
            "distance_km": distance_km,
            "volume_tonnes": round(lane_volume, 1),
            "volume_pct": lane.get("volume_pct", 1.0),
            "emission_factor_kgco2e_per_tkm": ef_data["kgco2e_per_tonne_km"],
            "scope3_cat4_transport_tco2e": round(cat4_tco2e, 2),
            "scope3_cat1_purchased_goods_tco2e": round(cat1_tco2e, 2),
            "grid_intensity_factor": round(grid_intensity_factor, 3),
        })

    # Mode comparison (what if all sea freight)
    best_mode = min(TRANSPORT_EMISSION_FACTORS.items(), key=lambda x: x[1]["kgco2e_per_tonne_km"])
    avg_distance = sum(l["distance_km"] for l in lane_results) / max(len(lane_results), 1)
    min_cat4 = volume_tonnes * avg_distance * best_mode[1]["kgco2e_per_tonne_km"] / 1000.0

    return {
        "entity_id": entity_id,
        "commodity_type": commodity_type,
        "total_volume_tonnes": volume_tonnes,
        "product_ghg_intensity_kgco2e_tonne": product_ghg,
        "trade_lanes": lane_results,
        "summary": {
            "total_scope3_cat4_tco2e": round(total_scope3_cat4, 2),
            "total_scope3_cat1_tco2e": round(total_scope3_cat1, 2),
            "combined_tco2e": round(total_scope3_cat4 + total_scope3_cat1, 2),
            "emission_intensity_tco2e_per_tonne": round(
                (total_scope3_cat4 + total_scope3_cat1) / max(volume_tonnes, 1), 4
            ),
        },
        "optimisation": {
            "current_cat4_tco2e": round(total_scope3_cat4, 2),
            "minimum_possible_cat4_tco2e": round(min_cat4, 2),
            "reduction_potential_pct": round(
                (total_scope3_cat4 - min_cat4) / max(total_scope3_cat4, 1) * 100, 1
            ),
            "recommended_mode": best_mode[0],
        },
        "ghg_protocol_references": ["GHG Protocol Corporate Value Chain Std 2011", "ISO 14083:2023"],
    }


def generate_green_instrument(
    entity_id: str,
    instrument_type: str,
    use_of_proceeds: str,
    counterparty_country: str,
) -> dict[str, Any]:
    """
    Generate green trade finance instrument assessment.

    Returns green LC/SBLC/trade loan criteria, ICC STF Principles alignment,
    ICMA Green Bond linkage, documentation requirements, pricing benefit.
    """
    rng = _rng(entity_id)

    if instrument_type not in GREEN_INSTRUMENT_CRITERIA:
        instrument_type = rng.choice(list(GREEN_INSTRUMENT_CRITERIA.keys()))
    instrument = GREEN_INSTRUMENT_CRITERIA[instrument_type]

    # Eligibility check
    eligible_sectors = instrument["eligible_sectors"]
    eligible = "any" in eligible_sectors or use_of_proceeds in eligible_sectors

    # ICC STF Principles scoring
    stf_scores = []
    for principle in ICC_STF_PRINCIPLES:
        score = round(rng.uniform(50.0, 95.0), 1)
        stf_scores.append({
            "id": principle["id"],
            "name": principle["name"],
            "weight": principle["weight"],
            "score": score,
        })
    stf_weighted = sum(s["score"] * s["weight"] for s in stf_scores)
    stf_aligned = stf_weighted >= 70

    # Pricing benefit
    bps_lo, bps_hi = instrument["pricing_benefit_bps_range"]
    pricing_benefit_bps = round(rng.uniform(bps_lo, bps_hi), 1) if eligible else 0.0

    # ICMA Green Bond linkage
    icma_eligible_use_of_proceeds = use_of_proceeds in [
        "renewable_energy", "energy_efficiency", "clean_transport", "sustainable_water",
        "green_building", "sustainable_agriculture", "climate_adaptation",
    ]
    icma_category = (
        "Green" if icma_eligible_use_of_proceeds
        else "Sustainability-Linked" if not instrument["use_of_proceeds_required"]
        else "Not Eligible"
    )

    # Country risk and documentation requirements
    counterparty_crc = OECD_COUNTRY_RISK.get(counterparty_country, 4)
    additional_docs = []
    if counterparty_crc >= 5:
        additional_docs.append("Enhanced KYC / country risk assessment")
    if counterparty_crc >= 6:
        additional_docs.append("Export control compliance sign-off")
    if not eligible:
        additional_docs.append("Use of proceeds re-assessment required")

    return {
        "entity_id": entity_id,
        "instrument_type": instrument_type,
        "instrument_name": instrument["full_name"],
        "use_of_proceeds": use_of_proceeds,
        "counterparty_country": counterparty_country,
        "eligibility": {
            "eligible": eligible,
            "eligible_sectors": eligible_sectors,
            "ineligibility_reason": None if eligible else f"{use_of_proceeds} not in eligible sector list",
        },
        "pricing": {
            "pricing_benefit_bps": pricing_benefit_bps,
            "use_of_proceeds_required": instrument["use_of_proceeds_required"],
            "icma_gbs_aligned": instrument["icma_gbs_aligned"],
        },
        "icc_stf_principles": {
            "principle_scores": stf_scores,
            "weighted_score": round(stf_weighted, 1),
            "aligned": stf_aligned,
        },
        "icma_classification": icma_category,
        "documentation_requirements": instrument["documentation"] + additional_docs,
        "counterparty_risk": {
            "country": counterparty_country,
            "oecd_crc": counterparty_crc,
            "risk_level": "low" if counterparty_crc <= 2 else ("medium" if counterparty_crc <= 5 else "high"),
        },
    }
