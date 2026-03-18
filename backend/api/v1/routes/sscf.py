"""
E101 — Sustainable Supply Chain Finance (SSCF) Engine Routes
=============================================================
POST /api/v1/sscf/assess                  — Full SSCF programme assessment
POST /api/v1/sscf/supplier-score          — Single supplier ESG scorecard
POST /api/v1/sscf/margin-ratchet          — SPT-linked margin ratchet calculation
POST /api/v1/sscf/dynamic-discount        — Early payment dynamic discount
GET  /api/v1/sscf/ref/sscf-frameworks     — LMA / ICC / GSCFF framework profiles
GET  /api/v1/sscf/ref/kpi-library         — 40 ESG KPIs with definitions (SK001–SK040)
GET  /api/v1/sscf/ref/sector-risk-profiles— 15 sector supply chain risk profiles
GET  /api/v1/sscf/ref/oecd-ddg           — OECD DDG 5-step due diligence reference
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from services.sscf_engine import (
    SSCFRequest,
    SupplierScoreRequest,
    MarginRatchetRequest,
    DynamicDiscountRequest,
    SSCF_FRAMEWORKS,
    KPI_LIBRARY,
    SECTOR_SUPPLY_CHAIN_RISK_PROFILES,
    OECD_DDG_STEPS,
    CSDDD_ADVERSE_IMPACTS,
    assess_sscf_programme,
    score_supplier_esg,
    calculate_margin_ratchet,
    calculate_dynamic_discount,
    get_sscf_benchmarks,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/sscf",
    tags=["E101 — Sustainable Supply Chain Finance Engine"],
)


# ---------------------------------------------------------------------------
# GET — Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/sscf-frameworks", summary="LMA / ICC / GSCFF SSCF Framework Profiles")
async def get_sscf_frameworks_ref() -> Dict[str, Any]:
    """
    Return profiles for all 3 SSCF frameworks:
    - **LMA_SSCF_2023**: LMA / APLMA Sustainable Supply Chain Finance Framework 2023 — 4 GLP components, 7 eligibility criteria
    - **ICC_SCF_2022**: ICC Supply Chain Finance Guidelines 2022 — 5 principles, AML/KYC focus
    - **GSCFF_2023**: Global Supply Chain Finance Forum Standards 2023 — 6 standards, IAS 7 accounting treatment

    Includes eligibility criteria, documentation checklists, max margin discount and green bond overlap notes.
    """
    try:
        return {
            "frameworks": SSCF_FRAMEWORKS,
            "framework_count": len(SSCF_FRAMEWORKS),
            "framework_ids": list(SSCF_FRAMEWORKS.keys()),
        }
    except Exception as exc:
        logger.exception("Error fetching SSCF frameworks")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/kpi-library", summary="40 Supply Chain ESG KPIs (SK001–SK040)")
async def get_kpi_library_ref() -> Dict[str, Any]:
    """
    Return all 40 supply chain ESG KPIs (SK001–SK040) with full definitions including:
    - Environmental (SK001–SK015): GHG, water, waste, energy, biodiversity, deforestation, chemicals
    - Social (SK016–SK028): LTIFR, child/forced labour, living wage, gender pay gap, FPIC, training
    - Governance (SK029–SK040): anti-corruption, whistleblower, tax transparency, conflict minerals, cybersecurity

    Each KPI includes: unit of measurement, data source, materiality threshold,
    verification requirement, SBTi alignment flag and CSDDD/EU Taxonomy linkage.
    """
    try:
        # Group by category
        grouped = {"Environmental": {}, "Social": {}, "Governance": {}}
        for kpi_id, kpi in KPI_LIBRARY.items():
            grouped[kpi["group"]][kpi_id] = kpi

        return {
            "kpi_library": KPI_LIBRARY,
            "kpi_count": len(KPI_LIBRARY),
            "grouped_by_category": grouped,
            "environmental_kpi_count": len(grouped["Environmental"]),
            "social_kpi_count": len(grouped["Social"]),
            "governance_kpi_count": len(grouped["Governance"]),
            "verification_required_kpis": [k for k, v in KPI_LIBRARY.items() if v["verification_required"]],
            "sbt_aligned_kpis": [k for k, v in KPI_LIBRARY.items() if v["sbt_alignment"]],
        }
    except Exception as exc:
        logger.exception("Error fetching KPI library")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/sector-risk-profiles", summary="15 Sector Supply Chain Risk Profiles")
async def get_sector_risk_profiles_ref() -> Dict[str, Any]:
    """
    Return supply chain ESG risk profiles for 15 sectors:
    textiles, electronics, agriculture, mining, chemicals, automotive, food_beverage,
    pharma, construction, energy, retail, logistics, financial, tech, healthcare.

    Each profile includes: inherent risk tier, primary supply chain risks, CAHRA exposure,
    conflict mineral exposure, EUDR relevance, typical tier depth, Scope 3 Cat1 intensity
    and recommended KPIs for SSCF programme design.
    """
    try:
        risk_tier_distribution = {}
        for profile in SECTOR_SUPPLY_CHAIN_RISK_PROFILES.values():
            tier = profile["inherent_risk_tier"]
            risk_tier_distribution[tier] = risk_tier_distribution.get(tier, 0) + 1

        return {
            "sector_risk_profiles": SECTOR_SUPPLY_CHAIN_RISK_PROFILES,
            "sector_count": len(SECTOR_SUPPLY_CHAIN_RISK_PROFILES),
            "sector_ids": list(SECTOR_SUPPLY_CHAIN_RISK_PROFILES.keys()),
            "risk_tier_distribution": risk_tier_distribution,
            "eudr_exposed_sectors": [
                sid for sid, s in SECTOR_SUPPLY_CHAIN_RISK_PROFILES.items() if s["eudr_exposure"]
            ],
            "cahra_exposed_sectors": [
                sid for sid, s in SECTOR_SUPPLY_CHAIN_RISK_PROFILES.items() if s["cahra_exposure"]
            ],
            "conflict_mineral_sectors": [
                sid for sid, s in SECTOR_SUPPLY_CHAIN_RISK_PROFILES.items() if s["conflict_mineral_exposure"]
            ],
        }
    except Exception as exc:
        logger.exception("Error fetching sector risk profiles")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/oecd-ddg", summary="OECD DDG 5-Step Supply Chain Due Diligence Reference")
async def get_oecd_ddg_ref() -> Dict[str, Any]:
    """
    Return the OECD Due Diligence Guidance 5-step framework reference:

    1. **Step 1** (20%): Embed RBC into policies and management systems
    2. **Step 2** (25%): Identify and assess adverse impacts in supply chain
    3. **Step 3** (25%): Cease, prevent or mitigate adverse impacts
    4. **Step 4** (20%): Track implementation via third-party verification
    5. **Step 5** (10%): Communicate how impacts are addressed — public reporting

    Also includes all 18 CSDDD adverse impact categories (HR-01 to HR-10, ENV-01 to ENV-08)
    with supply chain cascade triggers and linked KPIs.
    """
    try:
        return {
            "oecd_ddg_5_steps": OECD_DDG_STEPS,
            "step_count": len(OECD_DDG_STEPS),
            "total_weight_pct": sum(s["weight_pct"] for s in OECD_DDG_STEPS.values()),
            "csddd_adverse_impact_categories": CSDDD_ADVERSE_IMPACTS,
            "csddd_human_rights_categories": {k: v for k, v in CSDDD_ADVERSE_IMPACTS.items() if v["type"] == "human_rights"},
            "csddd_environmental_categories": {k: v for k, v in CSDDD_ADVERSE_IMPACTS.items() if v["type"] == "environmental"},
            "cascade_applicable_categories": [k for k, v in CSDDD_ADVERSE_IMPACTS.items() if v["supply_chain_cascade"]],
            "reference_standards": [
                "OECD Due Diligence Guidance for Responsible Business Conduct (2018)",
                "OECD MNE Guidelines 2023 Update",
                "UNGP Reporting Framework",
                "EU CSDDD Directive (EU) 2024/1760",
                "ILO Core Labour Standards (C87, C98, C138, C182, C29, C105)",
            ],
        }
    except Exception as exc:
        logger.exception("Error fetching OECD DDG reference")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# POST — Computation endpoints
# ---------------------------------------------------------------------------

@router.post("/assess", summary="Full SSCF Programme Assessment")
async def assess_programme(request: SSCFRequest) -> Dict[str, Any]:
    """
    Execute a comprehensive Sustainable Supply Chain Finance programme assessment.

    **What it computes:**
    - Framework eligibility verification (LMA / ICC / GSCFF criteria checklist)
    - Per-supplier ESG scoring across all 40 KPIs (SK001–SK040)
    - Spend-weighted programme-level KPI scores
    - OECD DDG 5-step compliance score (weighted 100-point scale)
    - CSDDD adverse impact cascade check (HR-01–HR-10, ENV-01–ENV-08)
    - Scope 3 Category 1 supplier coverage assessment (PCAF Part C)
    - SPT-linked margin ratchet illustration (step-down / step-up mechanics)
    - Risk tier classification for each supplier (low / medium / high / critical)
    - CAHRA and conflict mineral red flag identification
    - Documentation checklist for programme sponsor bank

    **Supported frameworks:** LMA_SSCF_2023 | ICC_SCF_2022 | GSCFF_2023
    """
    if request.sscf_framework not in SSCF_FRAMEWORKS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown SSCF framework '{request.sscf_framework}'. Valid values: {list(SSCF_FRAMEWORKS.keys())}",
        )
    invalid_kpis = [k for k in request.kpi_selections if k not in KPI_LIBRARY]
    if invalid_kpis:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown KPI IDs: {invalid_kpis}. Valid range: SK001–SK040",
        )
    if not request.suppliers:
        raise HTTPException(status_code=422, detail="At least one supplier profile is required")
    try:
        result = assess_sscf_programme(request)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("SSCF programme assessment failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/supplier-score", summary="Single Supplier ESG Scorecard")
async def compute_supplier_score(request: SupplierScoreRequest) -> Dict[str, Any]:
    """
    Produce a detailed ESG scorecard for a single supplier.

    **Scoring methodology:**
    - Each KPI scored 0–100 (direction-aware: lower-is-better for GHG intensity, LTIFR etc.)
    - Group scores: Environmental (40% weight), Social (35%), Governance (25%)
    - Risk tier classification: low (≥80) / medium (≥60) / high (≥40) / critical (<40)
    - CAHRA red flag applied for conflict-affected and high-risk area countries
    - Conflict mineral flag applied for electronics / mining / automotive NACE codes
    - Recommended early-payment discount rate based on risk tier

    Returns per-KPI breakdown, group averages, risk tier, CSDDD triggers and recommended discount.
    """
    if not request.kpi_data:
        raise HTTPException(status_code=422, detail="At least one KPI value must be provided in kpi_data")
    try:
        result = score_supplier_esg(request)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Supplier ESG scoring failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/margin-ratchet", summary="SPT-Linked Margin Ratchet Calculation")
async def compute_margin_ratchet(request: MarginRatchetRequest) -> Dict[str, Any]:
    """
    Calculate the SPT (Sustainability Performance Target) linked margin adjustment
    for a sustainability-linked supply chain finance programme.

    **Step-down / step-up schedule (LMA SLLP aligned):**
    | Achievement | Tier | Adjustment |
    |------------|------|------------|
    | 100% SPTs met | Platinum | -50 bps |
    | 80–99% | Gold | -30 bps |
    | 60–79% | Silver | -15 bps |
    | 40–59% | Bronze | -5 bps |
    | 20–39% | Grace Period | 0 bps |
    | 1–19% | Step-Up Minor | +10 bps |
    | 0% | Step-Up Major | +25 bps |

    Maximum discount capped at **75 bps**. Grace period of **6 months** before step-up enforced.
    """
    if request.spts_met > request.spts_total:
        raise HTTPException(status_code=422, detail="spts_met cannot exceed spts_total")
    try:
        result = calculate_margin_ratchet(
            base_rate_bps=request.base_rate_bps,
            spts_met=request.spts_met,
            spts_total=request.spts_total,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Margin ratchet calculation failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/dynamic-discount", summary="Early Payment Dynamic Discount Calculation")
async def compute_dynamic_discount(request: DynamicDiscountRequest) -> Dict[str, Any]:
    """
    Calculate the early payment discount for a supplier invoice under a dynamic discounting programme.

    **Formula (GSCFF / LMA standard):**
    ```
    effective_rate = min(max(buyer_WACC, 0.5%), 8.0%)
    annualised_discount = effective_rate × (days_early / 360)
    discount_amount = invoice_amount × annualised_discount
    settlement_amount = invoice_amount - discount_amount
    ```

    The buyer shares the benefit of paying early — the discount rate reflects the buyer's
    WACC (cost of capital), floored at **0.5% p.a.** and capped at **8.0% p.a.** to protect
    supplier economics.

    Returns: effective rate, discount amount, settlement amount, supplier APR equivalent.
    """
    try:
        result = calculate_dynamic_discount(
            buyer_wacc_pct=request.buyer_wacc_pct,
            days_early=request.days_early,
            invoice_amount=request.invoice_amount,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Dynamic discount calculation failed")
        raise HTTPException(status_code=500, detail=str(exc))
