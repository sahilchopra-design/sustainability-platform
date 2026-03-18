"""
Critical Minerals & Transition Metals Risk Routes — E93
Prefix: /api/v1/critical-minerals
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from services.critical_minerals_engine import (
    assess_critical_minerals,
    map_supply_chain,
    get_mineral_profile,
    CriticalMineralsAssessRequest,
    SupplyChainMapRequest,
    IEA_CRITICAL_MINERALS_2024,
    EU_CRM_ACT_MINERALS,
    EU_CRM_ACT_COMPLIANCE_OBLIGATIONS,
    IRMA_STANDARD_CRITERIA,
    IRMA_TIER_THRESHOLDS,
    OECD_5_STEP_FRAMEWORK,
    CONFLICT_MINERAL_HIGH_RISK_COUNTRIES,
    TRANSITION_TECHNOLOGY_MINERAL_INTENSITY,
)

router = APIRouter(prefix="/api/v1/critical-minerals", tags=["Critical Minerals — E93"])


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------

@router.post("/assess")
async def assess_critical_minerals_endpoint(request: CriticalMineralsAssessRequest) -> Dict[str, Any]:
    """
    Full critical minerals risk assessment.

    Computes:
    - IEA CRM 2024 composite criticality (demand growth, supply concentration, geopolitical risk, substitutability)
    - EU CRM Act 2024/1252 compliance score, strategic/critical mineral counts, audit status, compliance gaps
    - IRMA Standard v1.0 score across 6 chapters, tier (not_rated/tier_1/tier_2/tier_3), gaps
    - OECD DDG 5-step compliance score, conflict mineral risk tier, conflict region exposure flag
    - Transition technology financial exposure: EV batteries, solar PV, wind turbines, grid storage (USD million)
    - Supply chain metrics: price volatility score, supply disruption probability, HHI, top-3 country share
    - Overall crm_risk_score (0-100) and crm_risk_tier (low/medium/high/critical)
    """
    try:
        result = assess_critical_minerals(request.dict())
        return {
            "status": "success",
            "entity_id": result.entity_id,
            "entity_name": result.entity_name,
            "sector": result.sector,
            "minerals_assessed": result.minerals_assessed,
            "iea_crm_2024": {
                "demand_growth_score": result.iea_demand_growth_score,
                "supply_concentration": result.iea_supply_concentration,
                "geopolitical_risk": result.iea_geopolitical_risk,
                "substitutability": result.iea_substitutability,
                "criticality_composite": result.iea_criticality_composite,
            },
            "eu_crm_act": {
                "applicable": result.eu_crm_act_applicable,
                "strategic_mineral_count": result.eu_crm_strategic_mineral_count,
                "critical_mineral_count": result.eu_crm_critical_mineral_count,
                "audit_required": result.eu_crm_audit_required,
                "compliance_score": result.eu_crm_compliance_score,
                "gaps": result.eu_crm_gaps,
            },
            "irma": {
                "applicable": result.irma_applicable,
                "score": result.irma_score,
                "tier": result.irma_tier,
                "gaps": result.irma_gaps,
            },
            "oecd_ddg": {
                "composite_score": result.oecd_ddg_score,
                "5step_compliance": result.oecd_5step_compliance,
                "conflict_mineral_risk": result.conflict_mineral_risk,
                "conflict_region_exposure": result.conflict_region_exposure,
            },
            "transition_exposure": {
                "ev_battery_exposure_m": result.ev_battery_exposure_m,
                "solar_pv_exposure_m": result.solar_pv_exposure_m,
                "wind_turbine_exposure_m": result.wind_turbine_exposure_m,
                "grid_storage_exposure_m": result.grid_storage_exposure_m,
                "total_transition_exposure_m": result.total_transition_exposure_m,
            },
            "supply_chain_metrics": {
                "price_volatility_score": result.price_volatility_score,
                "supply_disruption_prob_pct": result.supply_disruption_prob_pct,
                "concentration_hhi": result.concentration_hhi,
                "top3_country_share_pct": result.top3_country_share_pct,
            },
            "overall": {
                "crm_risk_score": result.crm_risk_score,
                "crm_risk_tier": result.crm_risk_tier,
            },
            "key_findings": result.key_findings,
            "recommendations": result.recommendations,
            "standards_applied": result.standards_applied,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supply-chain-map")
async def supply_chain_map_endpoint(request: SupplyChainMapRequest) -> Dict[str, Any]:
    """
    Map mineral supply chain tiers for a specific mineral and technology application.

    Returns:
    - Mineral IEA CRM 2024 profile
    - Tier 1 country-level conflict risk assessment (OECD Annex II)
    - Conflict region exposure flag
    - RMAP smelter audit recommendation
    - OECD Annex II overall risk rating
    - Sourcing recommendations
    """
    try:
        result = map_supply_chain(request.dict())
        return {
            "status": "success",
            "entity_id": result.entity_id,
            "entity_name": result.entity_name,
            "mineral": result.mineral,
            "technology_application": result.technology_application,
            "annual_volume_tonnes": result.annual_volume_tonnes,
            "mineral_profile": result.mineral_profile,
            "supply_chain_assessment": {
                "tier1_country_risks": result.tier1_country_risks,
                "conflict_region_flag": result.conflict_region_flag,
                "smelter_audit_completed": result.smelter_audit_completed,
                "certification_scheme": result.certification_scheme,
                "rmap_recommended": result.rmap_recommended,
                "oecd_annex_ii_risk": result.oecd_annex_ii_risk,
            },
            "sourcing_recommendations": result.sourcing_recommendations,
            "relevant_standards": [
                "OECD DDG — Annex II Adverse Impact Indicators",
                "RMAP — Responsible Minerals Assurance Process",
                "EU Regulation 2017/821 (3TG conflict minerals)",
                "EU CRM Act 2024/1252 Art 14 — Supply chain due diligence",
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/iea-minerals")
async def get_iea_minerals() -> Dict[str, Any]:
    """
    IEA Critical Minerals 2024 — full mineral profiles for 15 key transition metals.
    Includes demand growth score, supply concentration HHI, geopolitical risk score,
    substitutability, transition technology dependence, recycling rate, and IEA criticality composite.
    """
    return {
        "status": "success",
        "source": "IEA Critical Minerals 2024 — https://www.iea.org/reports/critical-minerals-2024",
        "reference_year": 2024,
        "mineral_count": len(IEA_CRITICAL_MINERALS_2024),
        "minerals": IEA_CRITICAL_MINERALS_2024,
        "transition_mineral_intensity": TRANSITION_TECHNOLOGY_MINERAL_INTENSITY,
        "criticality_composite_methodology": {
            "components": ["demand_growth_score (IEA)", "supply_concentration_HHI", "geopolitical_risk_score", "substitutability_score (inverted)"],
            "weights": "IEA proprietary composite; scores reported 0-100",
            "threshold_critical": 70,
            "threshold_strategic": 80,
        },
    }


@router.get("/ref/eu-crm-act")
async def get_eu_crm_act() -> Dict[str, Any]:
    """
    EU Critical Raw Materials Act 2024/1252 — full list of 34 strategic and critical minerals.
    Includes EU domestic benchmark targets (extraction 10%, processing 40%, recycling 15%),
    audit requirements, and compliance obligations per article.
    """
    strategic_list = [k for k, v in EU_CRM_ACT_MINERALS.items() if v.get("strategic")]
    critical_list  = [k for k, v in EU_CRM_ACT_MINERALS.items() if v.get("critical")]
    return {
        "status": "success",
        "source": "EU Critical Raw Materials Act — Regulation (EU) 2024/1252",
        "effective_date": "2024-05-23",
        "strategic_mineral_count": len(strategic_list),
        "critical_mineral_count": len(critical_list),
        "strategic_minerals": strategic_list,
        "critical_minerals": critical_list,
        "eu_benchmark_targets": {
            "extraction_pct": "At least 10% of EU annual consumption from EU domestic extraction",
            "processing_pct": "At least 40% of EU annual consumption from EU domestic processing",
            "recycling_pct": "At least 15% of EU annual consumption from EU recycled sources",
            "single_country_max_pct": "No single non-EU country to supply more than 65% of any strategic CRM",
        },
        "mineral_detail": EU_CRM_ACT_MINERALS,
        "compliance_obligations": EU_CRM_ACT_COMPLIANCE_OBLIGATIONS,
    }


@router.get("/ref/irma-criteria")
async def get_irma_criteria() -> Dict[str, Any]:
    """
    IRMA Standard for Responsible Mining v1.0 — 6-chapter assessment framework
    with weighted criteria, key requirements, and three certification tiers
    (Tier 1 basic commitments / Tier 2 established practice / Tier 3 leadership).
    """
    return {
        "status": "success",
        "source": "IRMA Standard for Responsible Mining v1.0 — https://responsiblemining.net",
        "standard_version": "v1.0",
        "chapter_count": len(IRMA_STANDARD_CRITERIA),
        "certification_tiers": IRMA_TIER_THRESHOLDS,
        "chapters": IRMA_STANDARD_CRITERIA,
        "applicability": "Applicable to mining operations supplying critical minerals for transition technologies",
        "third_party_verification": "Required for Tier 2 and Tier 3 certification",
        "conflict_mineral_overlap": "IRMA Ch3 corporate responsibility aligns with OECD DDG Step 1-2; Ch4 Indigenous Rights aligns with FPIC requirements",
    }


@router.get("/ref/oecd-5step")
async def get_oecd_5step() -> Dict[str, Any]:
    """
    OECD Due Diligence Guidance for Responsible Mineral Supply Chains — 5-step framework.
    Includes step descriptions, weights, key requirements, recognised certification schemes,
    and conflict-affected and high-risk area (CAHRA) Annex II risk indicators.
    """
    return {
        "status": "success",
        "source": "OECD DDG for Responsible Mineral Supply Chains — 3rd Edition (2016) + 2023 Update",
        "regulatory_underpinning": [
            "US Dodd-Frank Act Section 1502 (SEC Form SD — 3TG conflict minerals)",
            "EU Regulation 2017/821 — Union due diligence framework (3TG)",
            "EU Critical Raw Materials Act 2024/1252 Art 14 — Expanded to all strategic CRMs",
        ],
        "step_count": len(OECD_5_STEP_FRAMEWORK),
        "steps": OECD_5_STEP_FRAMEWORK,
        "conflict_high_risk_countries": CONFLICT_MINERAL_HIGH_RISK_COUNTRIES,
        "recognised_certification_schemes": {
            "RMAP":  "Responsible Minerals Assurance Process (Responsible Minerals Initiative)",
            "RJC":   "Responsible Jewellery Council Chain of Custody",
            "LBMA":  "London Bullion Market Association Responsible Sourcing",
            "LPPM":  "London Platinum and Palladium Market Responsible Sourcing",
            "iTSCi": "ITRI Tin Supply Chain Initiative (DRC cobalt/tin/tantalum)",
        },
        "minimum_compliance_score": 0.70,
    }


@router.get("/ref/country-concentration")
async def get_country_concentration() -> Dict[str, Any]:
    """
    Top producer country shares by mineral — IEA CRM 2024 data.
    Includes supply concentration HHI, top-3 country shares, conflict region flags,
    and EU 65% single-source concentration limit breach analysis.
    """
    concentration_analysis: Dict[str, Any] = {}
    eu_concentration_breaches: List[Dict] = []

    for mineral, profile in IEA_CRITICAL_MINERALS_2024.items():
        top3 = profile.get("top3_country_share_pct", {})
        hhi  = profile.get("supply_concentration_hhi", 0)
        breaches = [{"country": c, "share_pct": s} for c, s in top3.items() if s > 65]

        concentration_analysis[mineral] = {
            "top3_country_share_pct": top3,
            "supply_concentration_hhi": hhi,
            "hhi_classification": "highly_concentrated" if hhi >= 2500 else "moderately_concentrated" if hhi >= 1500 else "competitive",
            "eu_65pct_breach": bool(breaches),
            "breaching_countries": breaches,
            "primary_ore": profile.get("primary_ore", "N/A"),
            "recycling_rate_pct": profile.get("recycling_rate_pct", 0),
        }
        if breaches:
            for b in breaches:
                eu_concentration_breaches.append({
                    "mineral": mineral,
                    "country": b["country"],
                    "share_pct": b["share_pct"],
                    "eu_crm_act_article": "Art 5 — Single-source concentration limit (>65%)",
                })

    return {
        "status": "success",
        "source": "IEA Critical Minerals 2024; EU CRM Act 2024/1252 Art 5",
        "mineral_count": len(concentration_analysis),
        "concentration_analysis": concentration_analysis,
        "eu_65pct_limit_breaches": eu_concentration_breaches,
        "breach_count": len(eu_concentration_breaches),
        "hhi_classification_thresholds": {
            "competitive": "HHI < 1500",
            "moderately_concentrated": "HHI 1500-2500",
            "highly_concentrated": "HHI > 2500 — EU/DOJ merger threshold equivalent",
        },
        "conflict_high_risk_countries": list(CONFLICT_MINERAL_HIGH_RISK_COUNTRIES.keys()),
    }


@router.get("/ref/mineral-profile/{mineral_name}")
async def get_single_mineral_profile(mineral_name: str) -> Dict[str, Any]:
    """
    Detailed profile for a single mineral — IEA CRM 2024 data,
    EU CRM Act 2024/1252 strategic/critical classification,
    transition technology mineral intensity, and conflict country exposure.
    """
    try:
        profile = get_mineral_profile(mineral_name)
        if "error" in profile:
            raise HTTPException(status_code=404, detail=profile["error"])
        return {"status": "success", **profile}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
