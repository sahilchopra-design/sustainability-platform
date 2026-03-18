"""
API Routes: EU Taxonomy Alignment Engine
==========================================
POST /api/v1/eu-taxonomy/assess-activity          — Assess single NACE activity alignment
POST /api/v1/eu-taxonomy/assess-entity             — Full entity taxonomy alignment (turnover/capex/opex KPIs)
POST /api/v1/eu-taxonomy/assess-portfolio           — Portfolio-level taxonomy alignment (GAR, BTAR)
GET  /api/v1/eu-taxonomy/ref/objectives             — 6 Environmental Objectives (Article 9)
GET  /api/v1/eu-taxonomy/ref/nace-activities        — NACE activities with TSC summaries
GET  /api/v1/eu-taxonomy/ref/dnsh-matrix            — 6×6 DNSH cross-check matrix
GET  /api/v1/eu-taxonomy/ref/minimum-safeguards     — Article 18 safeguards (OECD, UNGPs, ILO)
GET  /api/v1/eu-taxonomy/ref/kpi-definitions        — Turnover/CapEx/OpEx KPI rules
GET  /api/v1/eu-taxonomy/ref/transitional-activities — Transitional activities (Art 10(2))
GET  /api/v1/eu-taxonomy/ref/enabling-activities     — Enabling activities (Art 10(1))
GET  /api/v1/eu-taxonomy/ref/cross-framework        — CSRD/SFDR/ISSB/GRI/CDP cross-mapping
GET  /api/v1/eu-taxonomy/ref/financial-kpis          — GAR, BTAR for financial undertakings
GET  /api/v1/eu-taxonomy/ref/sector-thresholds       — Key quantitative thresholds by sector
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.eu_taxonomy_engine import EUTaxonomyEngine

router = APIRouter(prefix="/api/v1/eu-taxonomy", tags=["EU Taxonomy Alignment"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class AssessActivityRequest(BaseModel):
    nace_code: str = "D35.11"
    objective: str = "CCM"
    evidence_data: dict = Field(default_factory=dict)


class AssessEntityRequest(BaseModel):
    entity_name: str
    reporting_year: int = 2025
    activities_data: list[dict] = Field(default_factory=list)
    financials: dict = Field(default_factory=dict)


class AssessPortfolioRequest(BaseModel):
    portfolio_id: str = "PF001"
    portfolio_name: str
    reporting_year: int = 2025
    investees_data: list[dict] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assess-activity")
def assess_activity(req: AssessActivityRequest):
    """Assess single NACE activity alignment per Regulation (EU) 2020/852 Article 3."""
    engine = EUTaxonomyEngine()
    r = engine.assess_activity(
        nace_code=req.nace_code,
        objective=req.objective,
        evidence_data=req.evidence_data,
    )
    return r.__dict__


@router.post("/assess-entity")
def assess_entity(req: AssessEntityRequest):
    """Full entity taxonomy alignment — turnover/capex/opex KPIs per Art 8 + DR 2021/2178."""
    engine = EUTaxonomyEngine()
    r = engine.assess_entity(
        entity_name=req.entity_name,
        reporting_year=req.reporting_year,
        activities_data=req.activities_data,
        financials=req.financials,
    )
    result = r.__dict__.copy()
    # Flatten nested dataclasses in activity_assessments
    if r.activity_assessments:
        result["activity_assessments"] = [a.__dict__ for a in r.activity_assessments]
    return result


@router.post("/assess-portfolio")
def assess_portfolio(req: AssessPortfolioRequest):
    """Portfolio-level taxonomy alignment — GAR, BTAR, SFDR article suggestion."""
    engine = EUTaxonomyEngine()
    r = engine.assess_portfolio(
        portfolio_id=req.portfolio_id,
        portfolio_name=req.portfolio_name,
        investees_data=req.investees_data,
    )
    result = r.__dict__.copy()
    # Flatten nested investee assessments
    if r.investee_assessments:
        result["investee_assessments"] = [i.__dict__ for i in r.investee_assessments]
    return result


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/objectives")
def ref_objectives():
    """6 Environmental Objectives per Article 9 of Regulation (EU) 2020/852."""
    return {"environmental_objectives": EUTaxonomyEngine.get_environmental_objectives()}


@router.get("/ref/nace-activities")
def ref_nace_activities():
    """NACE economic activities with technical screening criteria summaries."""
    return {"nace_activities": EUTaxonomyEngine.get_nace_activities()}


@router.get("/ref/dnsh-matrix")
def ref_dnsh_matrix():
    """6×6 Do No Significant Harm cross-check matrix."""
    return {"dnsh_matrix": EUTaxonomyEngine.get_dnsh_matrix()}


@router.get("/ref/minimum-safeguards")
def ref_minimum_safeguards():
    """Article 18 Minimum Safeguards — OECD, UNGPs, ILO Core Conventions."""
    return {"minimum_safeguards": EUTaxonomyEngine.get_minimum_safeguards()}


@router.get("/ref/kpi-definitions")
def ref_kpi_definitions():
    """Turnover, CapEx, OpEx KPI definitions per Delegated Reg 2021/2178."""
    return {"kpi_definitions": EUTaxonomyEngine.get_kpi_definitions()}


@router.get("/ref/transitional-activities")
def ref_transitional_activities():
    """Transitional activities per Article 10(2) with sunset dates."""
    return {"transitional_activities": EUTaxonomyEngine.get_transitional_activities()}


@router.get("/ref/enabling-activities")
def ref_enabling_activities():
    """Enabling activities per Article 10(1) — technologies enabling substantial contribution."""
    return {"enabling_activities": EUTaxonomyEngine.get_enabling_activities()}


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """Cross-framework mapping: EU Taxonomy → CSRD/SFDR/ISSB/GRI/CDP."""
    return {"cross_framework_map": EUTaxonomyEngine.get_cross_framework_map()}


@router.get("/ref/financial-kpis")
def ref_financial_kpis():
    """Financial undertaking KPIs — Green Asset Ratio (GAR), BTAR."""
    return {"financial_kpi_definitions": EUTaxonomyEngine.get_financial_kpi_definitions()}


@router.get("/ref/sector-thresholds")
def ref_sector_thresholds():
    """Key quantitative thresholds by sector from Climate Delegated Act."""
    return {"sector_thresholds": EUTaxonomyEngine.get_sector_thresholds()}
