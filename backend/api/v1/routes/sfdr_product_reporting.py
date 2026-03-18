"""SFDR Product Periodic Reporting — E22 routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from services.sfdr_product_reporting_engine import get_engine

router = APIRouter(prefix="/api/v1/sfdr-product-reporting", tags=["SFDR Product Reporting"])
engine = get_engine()


class GenerateReportRequest(BaseModel):
    product_id: str
    product_name: str
    sfdr_article: str = "8"
    reporting_period: str
    sections_completed: Optional[list[str]] = None
    benchmark_index: str = ""
    aum_mn: float = 100.0


class VerifyRequest(BaseModel):
    product_id: str
    holdings: list[dict[str, Any]] = []


@router.post("/generate-report")
def generate_report(req: GenerateReportRequest):
    try:
        import dataclasses
        result = engine.generate_report(
            product_id=req.product_id,
            product_name=req.product_name,
            sfdr_article=req.sfdr_article,
            reporting_period=req.reporting_period,
            sections_completed=req.sections_completed,
            benchmark_index=req.benchmark_index,
            aum_mn=req.aum_mn,
        )
        return {"status": "ok", "report": dataclasses.asdict(result)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/verify-sustainable-investment")
def verify_sustainable_investment(req: VerifyRequest):
    try:
        import dataclasses
        result = engine.verify_sustainable_investment(
            product_id=req.product_id,
            holdings=req.holdings,
        )
        return {"status": "ok", "verification": dataclasses.asdict(result)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/pai-indicators")
def ref_pai_indicators():
    return engine.ref_pai_indicators()


@router.get("/ref/sfdr-articles")
def ref_sfdr_articles():
    return engine.ref_sfdr_articles()


@router.get("/ref/sustainable-investment-criteria")
def ref_sustainable_investment_criteria():
    return {"criteria": engine.ref_sustainable_investment_criteria()}


@router.get("/ref/rts-sections/{article}")
def ref_rts_sections(article: str):
    articles = engine.ref_sfdr_articles()
    if article not in articles:
        raise HTTPException(status_code=404, detail=f"SFDR Article {article} not found")
    return articles[article]


@router.get("/ref/reporting-timeline")
def ref_reporting_timeline():
    return {
        "regulation": "SFDR RTS 2022/1288 (Commission Delegated Regulation)",
        "applies_from": "2023-01-01",
        "periodic_report_deadline": "4 months after financial year end",
        "article_8_annex": "Annex III",
        "article_9_annex": "Annex V",
        "pai_statement_deadline": "30 June each year",
        "website_disclosure": "Permanent — must be kept up to date",
    }


@router.get("/ref/dnsh-objectives")
def ref_dnsh_objectives():
    return {
        "objectives": [
            {"id": 1, "name": "Climate change mitigation"},
            {"id": 2, "name": "Climate change adaptation"},
            {"id": 3, "name": "Sustainable use of water and marine resources"},
            {"id": 4, "name": "Transition to circular economy"},
            {"id": 5, "name": "Pollution prevention and control"},
            {"id": 6, "name": "Protection and restoration of biodiversity"},
        ],
        "rule": "An investment must not significantly harm any of the 6 objectives to qualify as sustainable",
    }
