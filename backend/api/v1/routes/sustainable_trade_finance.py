"""
Sustainable Trade Finance Routes — E75
=========================================
Prefix: /api/v1/sustainable-trade-finance
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from services.sustainable_trade_finance_engine import (
    assess_ep4_compliance,
    score_eca_green_classification,
    calculate_esg_linked_margin,
    screen_supply_chain_esg,
    generate_trade_finance_report,
    EP4_CATEGORIES,
    IFC_PERFORMANCE_STANDARDS,
    HIGH_RISK_SECTORS,
    ECA_COUNTRY_RISK_RATINGS,
    COMMODITY_SUPPLY_CHAIN_RISKS,
    ICC_STF_PRINCIPLES,
    SECTOR_SUSTAINABILITY_STANDARDS,
)

router = APIRouter(
    prefix="/api/v1/sustainable-trade-finance",
    tags=["Sustainable Trade Finance — E75"],
)

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class EP4ComplianceRequest(BaseModel):
    entity_id: str
    project_name: Optional[str] = "Trade Finance Project"
    sector: Optional[str] = "manufacturing"
    country: Optional[str] = "NG"
    total_cost_usd: Optional[float] = 25_000_000.0

    class Config:
        extra = "allow"


class ECAGreenRequest(BaseModel):
    entity_id: str
    sector: Optional[str] = "power"
    technology: Optional[str] = "solar_pv"
    country: Optional[str] = "IN"
    oecd_classification: Optional[str] = "Category_B"

    class Config:
        extra = "allow"


class ESGLinkedMarginRequest(BaseModel):
    entity_id: str
    base_margin_bps: Optional[float] = 200.0
    kpis: Optional[List[Dict[str, Any]]] = None
    performance_data: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class SupplyChainESGRequest(BaseModel):
    entity_id: str
    commodity: Optional[str] = "cocoa"
    origin_country: Optional[str] = "CI"
    tier1_supplier: Optional[str] = "Supplier A"
    certifications: Optional[List[str]] = None

    class Config:
        extra = "allow"


class TradeFinanceReportRequest(BaseModel):
    entity_id: str

    class Config:
        extra = "allow"


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess-ep4-compliance")
async def post_assess_ep4_compliance(req: EP4ComplianceRequest):
    """
    Assess EP4 compliance: category A/B/C determination, IFC Performance Standards
    1-8 applicability, 10-principle compliance checklist, ESAP requirements,
    independent review requirement. Persists to trade_finance_assessments table.
    """
    try:
        result = assess_ep4_compliance(
            entity_id=req.entity_id,
            project_name=req.project_name,
            sector=req.sector,
            country=req.country,
            total_cost_usd=req.total_cost_usd,
        )
        # DB persist (best-effort)
        try:
            from db.base import get_db_session
            from sqlalchemy import text
            import json
            async with get_db_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO trade_finance_assessments
                          (entity_id, transaction_name, transaction_type,
                           counterparty_country, sector, transaction_value,
                           equator_principles_category, ep4_compliance_score,
                           ep4_conditions)
                        VALUES (:entity_id, :transaction_name, :transaction_type,
                           :counterparty_country, :sector, :transaction_value,
                           :equator_principles_category, :ep4_compliance_score,
                           :ep4_conditions::jsonb)
                    """),
                    {
                        "entity_id": req.entity_id,
                        "transaction_name": result["project_name"],
                        "transaction_type": "project_finance",
                        "counterparty_country": req.country,
                        "sector": result["sector"],
                        "transaction_value": req.total_cost_usd,
                        "equator_principles_category": result["ep4_category"],
                        "ep4_compliance_score": result["overall_score"],
                        "ep4_conditions": json.dumps(result["esap_requirements"]),
                    },
                )
                await session.commit()
        except Exception:
            pass
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score-eca-green")
async def post_score_eca_green_classification(req: ECAGreenRequest):
    """
    Score ECA green classification: OECD Common Approaches 2016 tier,
    OECD CRE Arrangement 2023 applicability, sector sustainability standard (SSS),
    ECA environmental review score.
    """
    try:
        result = score_eca_green_classification(
            entity_id=req.entity_id,
            sector=req.sector,
            technology=req.technology,
            country=req.country,
            oecd_classification=req.oecd_classification,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-esg-margin")
async def post_calculate_esg_linked_margin(req: ESGLinkedMarginRequest):
    """
    Calculate ESG-linked margin adjustment: KPI materiality scoring,
    margin step-up/step-down (±5-15 bps), SPT calibration (ambitious/credible),
    ICC STF Principles 4 components assessment.
    Persists covenants to trade_finance_esg_covenants table.
    """
    try:
        result = calculate_esg_linked_margin(
            entity_id=req.entity_id,
            base_margin_bps=req.base_margin_bps,
            kpis=req.kpis,
            performance_data=req.performance_data,
        )
        # Persist ESG covenants
        try:
            from db.base import get_db_session
            from sqlalchemy import text
            async with get_db_session() as session:
                for kpi_res in result["kpi_results"]:
                    await session.execute(
                        text("""
                            INSERT INTO trade_finance_esg_covenants
                              (assessment_id, covenant_type, kpi_name,
                               baseline_value, target_value, margin_step_bps, status)
                            VALUES (:assessment_id, :covenant_type, :kpi_name,
                               :baseline_value, :target_value, :margin_step_bps, :status)
                        """),
                        {
                            "assessment_id": req.entity_id,
                            "covenant_type": "esg_kpi",
                            "kpi_name": kpi_res["name"],
                            "baseline_value": kpi_res["baseline"],
                            "target_value": kpi_res["target"],
                            "margin_step_bps": kpi_res["margin_adjustment_bps"],
                            "status": "active",
                        },
                    )
                await session.commit()
        except Exception:
            pass
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screen-supply-chain")
async def post_screen_supply_chain_esg(req: SupplyChainESGRequest):
    """
    Screen supply chain ESG: OECD Due Diligence Guidance for RBC,
    EUDR (Regulation 2023/1115) overlay, modern slavery risk (UK MSA / Australia MSA),
    deforestation risk, conflict minerals (3TG + cobalt), Responsible Business Alliance.
    """
    try:
        result = screen_supply_chain_esg(
            entity_id=req.entity_id,
            commodity=req.commodity,
            origin_country=req.origin_country,
            tier1_supplier=req.tier1_supplier,
            certifications=req.certifications,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report")
async def post_generate_trade_finance_report(req: TradeFinanceReportRequest):
    """
    Generate comprehensive sustainable trade finance report: ICC STF Principles (2019),
    WTO Aid for Trade, OECD Arrangement on Export Credits,
    IFC Performance Standards cross-reference, UNCTAD sustainable trade metrics.
    """
    try:
        result = generate_trade_finance_report(entity_id=req.entity_id)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ep4-categories")
async def get_ep4_categories():
    """EP4 categories A/B/C with thresholds and applicable standards."""
    return {
        "status": "success",
        "data": [
            {
                "category": cat,
                "description": info["description"],
                "threshold_usd": info["threshold_usd"],
                "ifc_ps_required": info["ifc_ps_required"],
                "independent_review": info["independent_review"],
                "esap_required": info["esap_required"],
                "examples": info["examples"],
            }
            for cat, info in EP4_CATEGORIES.items()
        ],
        "source": "Equator Principles 4 (July 2020)",
    }


@router.get("/ref/ifc-performance-standards")
async def get_ifc_performance_standards():
    """8 IFC Performance Standards on Environmental and Social Sustainability."""
    return {
        "status": "success",
        "data": [
            {
                "standard": ps_num,
                "name": info["name"],
                "mandatory_cat_a": info["mandatory"],
            }
            for ps_num, info in IFC_PERFORMANCE_STANDARDS.items()
        ],
        "source": "IFC Performance Standards on Environmental and Social Sustainability (2012)",
        "count": 8,
    }


@router.get("/ref/high-risk-sectors")
async def get_high_risk_sectors():
    """15 high-risk sectors for EP4/OECD Common Approaches enhanced due diligence."""
    return {
        "status": "success",
        "data": HIGH_RISK_SECTORS,
        "count": len(HIGH_RISK_SECTORS),
        "note": "These sectors trigger Category A or B assessment under EP4",
    }


@router.get("/ref/eca-country-risk-ratings")
async def get_eca_country_risk_ratings():
    """55 country ECA risk ratings (OECD 0-7 scale)."""
    return {
        "status": "success",
        "data": [
            {"country_iso2": country, "risk_rating": rating}
            for country, rating in ECA_COUNTRY_RISK_RATINGS.items()
        ],
        "count": len(ECA_COUNTRY_RISK_RATINGS),
        "scale": "0 (lowest risk) to 7 (highest risk) — OECD Country Risk Classification",
        "source": "OECD Country Risk Classifications of the Participants to the Arrangement",
    }


@router.get("/ref/commodity-supply-chain-risks")
async def get_commodity_supply_chain_risks():
    """8 commodity supply chain ESG risk profiles."""
    return {
        "status": "success",
        "data": [
            {"commodity": name, **info}
            for name, info in COMMODITY_SUPPLY_CHAIN_RISKS.items()
        ],
        "count": len(COMMODITY_SUPPLY_CHAIN_RISKS),
    }


@router.get("/ref/icc-stf-principles")
async def get_icc_stf_principles():
    """ICC Sustainable Trade Finance 4 Principles (ICC Pub. No. 908E, 2019)."""
    return {
        "status": "success",
        "data": [
            {
                "principle_number": num,
                "principle": info["principle"],
                "description": info["description"],
                "requirements": info["requirements"],
            }
            for num, info in ICC_STF_PRINCIPLES.items()
        ],
        "source": "ICC Sustainable Trade Finance Principles (ICC Publication No. 908E, 2019)",
        "count": 4,
    }


@router.get("/ref/oecd-sector-sustainability-standards")
async def get_oecd_sector_sustainability_standards():
    """OECD sector sustainability standards (SSS) and due diligence guidance by sector."""
    return {
        "status": "success",
        "data": [
            {"sector": sector, "standard": standard}
            for sector, standard in SECTOR_SUSTAINABILITY_STANDARDS.items()
        ],
        "source": "OECD Common Approaches 2016 / OECD CRE Arrangement 2023",
    }
