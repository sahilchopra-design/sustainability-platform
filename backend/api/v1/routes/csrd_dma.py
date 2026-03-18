"""
API Routes: CSRD Double Materiality Assessment (DMA)
=====================================================
ESRS 1 Sections 42-49

POST /api/v1/csrd-dma/impact-assessment       — Impact materiality scoring
POST /api/v1/csrd-dma/financial-assessment    — Financial materiality scoring
POST /api/v1/csrd-dma/stakeholder-engagement  — Stakeholder engagement quality
POST /api/v1/csrd-dma/topic-prioritisation    — Rank all topics by combined score
POST /api/v1/csrd-dma/dma-process             — DMA process completeness
POST /api/v1/csrd-dma/full-assessment         — Full double materiality assessment
GET  /api/v1/csrd-dma/ref/topics              — ESRS topic catalog
GET  /api/v1/csrd-dma/ref/severity-criteria   — Severity criteria
GET  /api/v1/csrd-dma/ref/financial-risk-types — Financial risk types
GET  /api/v1/csrd-dma/ref/sector-materiality  — Sector materiality profiles
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.csrd_dma_engine import CSRDDMAEngine

router = APIRouter(
    prefix="/api/v1/csrd-dma",
    tags=["CSRD Double Materiality — E40"],
)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ImpactAssessmentRequest(BaseModel):
    entity_id: str
    entity_name: str
    sector: str = "financial_services"
    topic_id: str = "E1"
    impact_data: dict = {}


class FinancialAssessmentRequest(BaseModel):
    entity_id: str
    entity_name: str
    topic_id: str = "E1"
    financial_data: dict = {}


class StakeholderEngagementRequest(BaseModel):
    entity_id: str
    entity_name: str
    stakeholder_data: dict = {}


class TopicPrioritisationRequest(BaseModel):
    entity_id: str
    entity_name: str
    sector: str = "financial_services"
    topics: dict = Field(
        default={},
        description="Optional dict with impact_scores, financial_scores, stakeholder_scores sub-dicts",
    )


class DMAProcessRequest(BaseModel):
    entity_id: str
    entity_name: str
    sector: str = "financial_services"
    nace_code: str = ""
    process_data: dict = {}


class FullDMARequest(BaseModel):
    entity_id: str
    entity_name: str
    sector: str = "financial_services"
    nace_code: str = ""
    reporting_period: str = "2025"
    full_data: dict = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/impact-assessment")
def impact_assessment(req: ImpactAssessmentRequest):
    """Score impact materiality for a single ESRS topic (ESRS 1 section 43)."""
    try:
        engine = CSRDDMAEngine()
        return engine.assess_impact_materiality(
            entity_id=req.entity_id,
            sector=req.sector,
            topic_id=req.topic_id,
            impact_data=req.impact_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/financial-assessment")
def financial_assessment(req: FinancialAssessmentRequest):
    """Score financial materiality for a single ESRS topic (ESRS 1 section 47)."""
    try:
        engine = CSRDDMAEngine()
        return engine.assess_financial_materiality(
            entity_id=req.entity_id,
            topic_id=req.topic_id,
            financial_data=req.financial_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stakeholder-engagement")
def stakeholder_engagement(req: StakeholderEngagementRequest):
    """Score stakeholder engagement quality across 5 process elements."""
    try:
        engine = CSRDDMAEngine()
        return engine.run_stakeholder_engagement(
            entity_id=req.entity_id,
            stakeholder_data=req.stakeholder_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/topic-prioritisation")
def topic_prioritisation(req: TopicPrioritisationRequest):
    """Prioritise all ESRS topics by combined double materiality score."""
    try:
        engine = CSRDDMAEngine()
        topics = req.topics
        return engine.prioritise_topics(
            entity_id=req.entity_id,
            sector=req.sector,
            impact_scores=topics.get("impact_scores", {}),
            financial_scores=topics.get("financial_scores", {}),
            stakeholder_scores=topics.get("stakeholder_scores", {}),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/dma-process")
def dma_process(req: DMAProcessRequest):
    """Assess completeness of the 4-step DMA process and assurance readiness."""
    try:
        engine = CSRDDMAEngine()
        return engine.assess_dma_process(
            entity_id=req.entity_id,
            process_data={"sector": req.sector, **req.process_data},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment")
def full_assessment(req: FullDMARequest):
    """Complete CSRD Double Materiality Assessment covering both dimensions."""
    try:
        engine = CSRDDMAEngine()
        return engine.full_assessment(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            sector=req.sector,
            nace_code=req.nace_code,
            reporting_period=req.reporting_period,
            full_data=req.full_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/topics")
def ref_topics():
    """Return the full ESRS topic catalog."""
    return CSRDDMAEngine.get_esrs_topics()


@router.get("/ref/severity-criteria")
def ref_severity_criteria():
    """Return ESRS 1 section 43 severity criteria with weights."""
    return CSRDDMAEngine.get_severity_criteria()


@router.get("/ref/financial-risk-types")
def ref_financial_risk_types():
    """Return ESRS 1 section 47 financial materiality risk types."""
    return CSRDDMAEngine.get_financial_risk_types()


@router.get("/ref/sector-materiality")
def ref_sector_materiality():
    """Return typical material topics by NACE sector."""
    return CSRDDMAEngine.get_sector_materiality()
