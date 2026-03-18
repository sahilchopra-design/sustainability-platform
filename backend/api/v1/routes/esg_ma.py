"""
esg_ma.py — E79 ESG M&A Due Diligence Routes
UNGP 31 Guiding Principles | CSDDD Art 3 Supply Chain Scope
OECD RBC Due Diligence | ESG Valuation Adjustments | Post-Merger Integration
"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

from services.esg_ma_engine import (
    assess_esg_due_diligence,
    score_ungp_alignment,
    calculate_esg_valuation_impact,
    plan_post_merger_integration,
    generate_dd_report,
    UNGP_PRINCIPLES,
    ESG_DD_CHECKLIST,
    DEAL_BREAKER_CRITERIA,
    CSDDD_SCOPE_THRESHOLDS,
    ESG_VALUATION_RANGES,
    ILO_CORE_CONVENTIONS,
)

router = APIRouter(prefix="/api/v1/esg-ma", tags=["E79 ESG M&A Due Diligence"])


# ── Request Models ─────────────────────────────────────────────────────────────

class DueDiligenceRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier (acquirer)")
    deal_name: str = Field(..., description="Name or code of the M&A deal")
    target_sector: str = Field(..., description="Target company sector (industrials, technology, agriculture, energy, etc.)")
    target_country: str = Field(..., description="Target company country of incorporation (ISO 2-letter code)")
    deal_value_usd: float = Field(..., gt=0, description="Deal enterprise value in USD")


class UngpAlignmentRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    target_company: str = Field(..., description="Target company name")
    sector: str = Field(..., description="Target company sector for HRIA risk assessment")


class ValuationImpactRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    base_valuation_usd: float = Field(..., gt=0, description="Base deal valuation (EV) in USD")
    esg_findings: dict[str, Any] = Field(
        default_factory=dict,
        description="ESG findings keyed by finding type with severity/adjustment values. Keys: climate_positive, climate_negative, human_rights_positive, human_rights_negative, governance_positive, governance_negative, biodiversity_negative, reporting_positive, labour_negative"
    )


class IntegrationPlanRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier (acquirer)")
    acquirer_profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Acquirer profile: esg_maturity (0-1), has_sbti (bool), csrd_filer (bool), sfdr_article (6/8/9)"
    )
    target_profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Target profile: esg_maturity (0-1), revenue_share (fraction of acquirer), sector, employees"
    )
    close_date: str = Field(..., description="Expected deal close date in ISO format (YYYY-MM-DD)")


class DdReportRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    deal_name: str = Field(..., description="Deal name for IC report")


# ── POST Endpoints ─────────────────────────────────────────────────────────────

@router.post("/due-diligence", summary="ESG Due Diligence Assessment (85-Item Checklist)")
async def due_diligence_endpoint(req: DueDiligenceRequest) -> dict[str, Any]:
    """
    Comprehensive ESG due diligence assessment across 85 checklist items in 15 categories.
    Covers E/S/G three pillars, red flag identification, ESG valuation adjustment (±5-25%),
    CSDDD Art 3 supply chain scope, and UNGP requirement trigger.
    """
    return assess_esg_due_diligence(
        entity_id=req.entity_id,
        deal_name=req.deal_name,
        target_sector=req.target_sector,
        target_country=req.target_country,
        deal_value_usd=req.deal_value_usd,
    )


@router.post("/ungp-alignment", summary="UNGP 31 Principles Alignment Scoring")
async def ungp_alignment_endpoint(req: UngpAlignmentRequest) -> dict[str, Any]:
    """
    Score alignment with UNGP 31 Guiding Principles across all 3 pillars:
    Pillar I (State Duty to Protect), Pillar II (Business Responsibility to Respect),
    Pillar III (Access to Remedy). Also checks ILO 8 core conventions, HRIA flag,
    and OECD RBC Due Diligence 6-step process.
    """
    return score_ungp_alignment(
        entity_id=req.entity_id,
        target_company=req.target_company,
        sector=req.sector,
    )


@router.post("/valuation-impact", summary="ESG Valuation Impact Calculation")
async def valuation_impact_endpoint(req: ValuationImpactRequest) -> dict[str, Any]:
    """
    Calculate ESG purchase price adjustments from DD findings.
    Quantifies: climate liability (stranded assets + carbon cost + litigation),
    S pillar adjustments (wage gap, turnover), G pillar adjustments (board, ownership),
    W&I coverage gaps for ESG reps, and integration cost estimates.
    """
    return calculate_esg_valuation_impact(
        entity_id=req.entity_id,
        base_valuation_usd=req.base_valuation_usd,
        esg_findings=req.esg_findings,
    )


@router.post("/integration-plan", summary="100-Day Post-Merger ESG Integration Plan")
async def integration_plan_endpoint(req: IntegrationPlanRequest) -> dict[str, Any]:
    """
    Generate a 100-day post-merger ESG integration plan.
    Covers governance alignment (D1-30), reporting harmonisation (D31-60),
    policy adoption and supply chain onboarding (D61-100), and systems integration (M6-12).
    Assesses cultural ESG gap, SBTi revision requirements, CSRD boundary expansion.
    """
    return plan_post_merger_integration(
        entity_id=req.entity_id,
        acquirer_profile=req.acquirer_profile,
        target_profile=req.target_profile,
        close_date=req.close_date,
    )


@router.post("/dd-report", summary="Investment Committee ESG DD Summary Report")
async def dd_report_endpoint(req: DdReportRequest) -> dict[str, Any]:
    """
    Generate full investment committee ESG due diligence summary report.
    Includes: material findings RAG dashboard, deal-breaker assessment (12 criteria),
    value creation opportunities, regulatory risk flags (CSDDD/EUDR/SFDR),
    comparable deal ESG benchmarks, and recommended W&I ESG representations.
    """
    return generate_dd_report(
        entity_id=req.entity_id,
        deal_name=req.deal_name,
    )


# ── GET Reference Endpoints ────────────────────────────────────────────────────

@router.get("/ref/dd-checklist", summary="85-Item ESG DD Checklist Reference")
async def get_dd_checklist() -> dict[str, Any]:
    """
    Return full 85-item ESG due diligence checklist across 15 categories
    (GHG/Climate, Biodiversity, Water, Pollution, Supply Chain, Human Rights,
    Labour, Community, Product Safety, Board Governance, Anti-Corruption,
    Reporting, Tax, Regulatory/Legal, Integration).
    """
    categories = {}
    for item in ESG_DD_CHECKLIST:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    return {
        "total_items": len(ESG_DD_CHECKLIST),
        "categories_count": len(categories),
        "categories": categories,
        "all_items": ESG_DD_CHECKLIST,
    }


@router.get("/ref/ungp-principles", summary="UNGP 31 Guiding Principles Reference")
async def get_ungp_principles() -> dict[str, Any]:
    """
    Return all 31 UN Guiding Principles on Business and Human Rights
    across 3 pillars (State Protect / Business Respect / Access Remedy).
    Includes ILO 8 core conventions reference.
    """
    pillars: dict[str, list] = {"I": [], "II": [], "III": []}
    for p in UNGP_PRINCIPLES:
        pillars[p["pillar"]].append(p)
    return {
        "framework": "UN Guiding Principles on Business and Human Rights (UNGPs)",
        "endorsed": "UN Human Rights Council Resolution 17/4 (June 2011)",
        "total_principles": len(UNGP_PRINCIPLES),
        "pillar_I_count": len(pillars["I"]),
        "pillar_II_count": len(pillars["II"]),
        "pillar_III_count": len(pillars["III"]),
        "pillars": {
            "Pillar_I_State_Duty_to_Protect": pillars["I"],
            "Pillar_II_Business_Responsibility_to_Respect": pillars["II"],
            "Pillar_III_Access_to_Remedy": pillars["III"],
        },
        "ilo_core_conventions": ILO_CORE_CONVENTIONS,
    }


@router.get("/ref/valuation-ranges", summary="ESG Valuation Adjustment Ranges by Finding Type")
async def get_valuation_ranges() -> dict[str, Any]:
    """
    Return ESG valuation adjustment ranges by finding type.
    Based on PwC/EY/Deloitte deal advisory benchmarks and academic studies
    on ESG premium/discount in M&A transactions.
    """
    return {
        "methodology": "ESG purchase price adjustment — EBITDA multiple impact",
        "data_sources": ["PwC M&A ESG Due Diligence 2023", "EY Sustainability DD Guide 2024", "KPMG ESG in M&A Report"],
        "adjustment_types_count": len(ESG_VALUATION_RANGES),
        "ranges": [
            {
                "finding_type": k,
                "range_pct": v["range_pct"],
                "typical_pct": v["typical_pct"],
                "driver": v["driver"],
            }
            for k, v in ESG_VALUATION_RANGES.items()
        ],
    }


@router.get("/ref/deal-breakers", summary="12 ESG M&A Deal-Breaker Criteria")
async def get_deal_breakers() -> dict[str, Any]:
    """
    Return 12 ESG M&A deal-breaker criteria — findings that trigger mandatory
    board escalation and typically require pre-close remediation or deal termination.
    """
    categories = {}
    for db in DEAL_BREAKER_CRITERIA:
        cat = db["category"]
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "total_criteria": len(DEAL_BREAKER_CRITERIA),
        "category_breakdown": categories,
        "threshold": "Any single deal-breaker trigger requires board ESG committee escalation before close",
        "criteria": DEAL_BREAKER_CRITERIA,
    }


@router.get("/ref/csddd-scope", summary="EU CSDDD Article 3 Scope Thresholds")
async def get_csddd_scope() -> dict[str, Any]:
    """
    Return EU CSDDD (Directive 2024/1760) Article 3 scope thresholds for phased application
    by company group (EU_group_1/2/3, non_EU_group_1/2/3) with employee/turnover thresholds
    and phased application dates 2027-2029.
    """
    return {
        "directive": "EU Corporate Sustainability Due Diligence Directive (CSDDD)",
        "reference": "Directive (EU) 2024/1760 — Article 3 Scope",
        "published": "2024-07-05",
        "transposition_deadline": "2026-07-26",
        "scope_note": "Applies to EU and non-EU companies meeting thresholds; financial sector targeted application follows",
        "thresholds": CSDDD_SCOPE_THRESHOLDS,
        "value_chain_obligations": {
            "tier1_suppliers": "Full CSDDD due diligence obligations",
            "beyond_tier1": "Risk-based assessment for higher-risk links",
            "financial_sector": "Targeted obligations for loan/credit/insurance/reinsurance services",
        },
        "civil_liability": {
            "article": "Art 29",
            "basis": "Compensation for damage caused by failure to comply with DD obligations",
            "limitation_period_years": 5,
        },
    }
