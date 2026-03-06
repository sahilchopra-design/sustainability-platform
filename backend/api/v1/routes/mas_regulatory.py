"""MAS Regulatory Module API — ERM, Notice 637, Singapore Green Finance Taxonomy, SLGS."""
from __future__ import annotations

import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/mas-regulatory", tags=["MAS Regulatory"])


# ─────────────────────────────────────────────────────────
# ERM Guidelines — MAS Guidelines on Environmental Risk Management (Banks) 2022
# ─────────────────────────────────────────────────────────
MAS_ERM_PRINCIPLES = [
    {"id": "erm_1", "section": "1", "title": "Board and Senior Management Oversight",
     "description": "Board sets risk appetite for environmental risk; Senior management implements policies and procedures"},
    {"id": "erm_2", "section": "2", "title": "Environmental Risk Policies and Procedures",
     "description": "Documented policies for environmental risk identification, assessment and monitoring"},
    {"id": "erm_3", "section": "3", "title": "Risk Assessment — Client & Counterparty",
     "description": "Environmental due diligence for credit, investment, and insurance activities"},
    {"id": "erm_4", "section": "4", "title": "Scenario Analysis & Stress Testing",
     "description": "Climate scenario analysis covering physical and transition risks; integration into ICAAP"},
    {"id": "erm_5", "section": "5", "title": "Disclosure",
     "description": "Public disclosure aligned to TCFD; MAS expects annual climate reporting by 2025"},
    {"id": "erm_6", "section": "6", "title": "Data & Metrics",
     "description": "Financed emissions, climate VaR, sector exposure limits — tracked and reported"},
]

# Notice 637 Pillar 2 (Environmental Risk in ICAAP/ILAAP)
MAS_NOTICE_637_ITEMS = [
    {"id": "n637_1", "pillar": "Pillar 2 — ICAAP", "item": "Environmental risk identification in ICAAP",
     "requirement": "Banks must assess physical and transition risks as part of the Internal Capital Adequacy Assessment Process"},
    {"id": "n637_2", "pillar": "Pillar 2 — ICAAP", "item": "Climate stress testing",
     "requirement": "Scenario-based stress tests covering ≥2 climate scenarios (e.g. orderly, disorderly, hot house)"},
    {"id": "n637_3", "pillar": "Pillar 2 — ILAAP", "item": "Liquidity risk from stranded assets",
     "requirement": "Assessment of sudden repricing / liquidity drying up on climate-exposed collateral"},
    {"id": "n637_4", "pillar": "Pillar 3 — Disclosure", "item": "Climate-related disclosures",
     "requirement": "Qualitative & quantitative TCFD-aligned disclosures; financed emissions by sector"},
    {"id": "n637_5", "pillar": "Supervisory Review", "item": "MAS SREP environmental risk assessment",
     "requirement": "MAS will assess environmental risk management maturity as part of annual SREP cycle from 2024"},
]

# Singapore Green and Transition Taxonomy (SGT v2.0, 2024)
SGT_SECTORS = [
    {"sector": "Energy", "activities": ["Solar PV generation", "Wind generation", "Hydropower", "Green hydrogen",
                                         "Bioenergy (certified)", "Nuclear (conditional)", "CCUS-enabled fossil fuels (transition)"]},
    {"sector": "Transport", "activities": ["Electric vehicles", "Hydrogen fuel cell vehicles",
                                            "Zero-emission shipping", "SAF-powered aviation", "Low-carbon rail"]},
    {"sector": "Buildings", "activities": ["Green buildings (BCA Green Mark)", "Retrofitting to net-zero standards",
                                            "Embodied carbon reduction", "Low-carbon materials"]},
    {"sector": "Waste & Water", "activities": ["Circular economy processing", "Waste-to-energy (certified)",
                                               "Water efficiency", "Wastewater treatment"]},
    {"sector": "IT & Data Centres", "activities": ["PUE <1.3 data centres", "Renewable-powered facilities",
                                                    "Circular hardware lifecycle"]},
    {"sector": "Agriculture & Forestry", "activities": ["Sustainable agriculture", "Reforestation/afforestation",
                                                          "Peatland restoration", "Mangrove conservation"]},
    {"sector": "Industrial", "activities": ["Industrial process decarbonisation", "Energy efficiency",
                                             "Low-carbon materials production", "CCUS at industrial facilities"]},
]

# SLGS — Singapore Green Lane for Sustainability (simplified tracking)
SLGS_STAGES = [
    {"stage": 1, "name": "Pre-qualification", "description": "Entity meets MAS baseline ESG disclosure requirements"},
    {"stage": 2, "name": "Application", "description": "Submit SLGS application with climate risk strategy and net-zero plan"},
    {"stage": 3, "name": "Assessment", "description": "MAS reviews TCFD alignment, transition credibility, financed emissions baseline"},
    {"stage": 4, "name": "Provisional Approval", "description": "Granted subject to annual reporting milestones"},
    {"stage": 5, "name": "Full Designation", "description": "Full SLGS designation — eligible for MAS incentive schemes"},
]


# ─────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────
class ERMSelfAssessment(BaseModel):
    responses: Dict[str, str] = Field(
        description="ERM principle ID → status (Compliant / Partial / Not Started)",
        example={"erm_1": "Compliant", "erm_2": "Partial", "erm_3": "Not Started"}
    )
    notes: Optional[Dict[str, str]] = Field(default=None, description="ERM principle ID → free text note")


class SLGSApplication(BaseModel):
    entity_name: str
    current_stage: int = Field(ge=1, le=5)
    tcfd_report_year: Optional[int] = None
    financed_emissions_baseline_year: Optional[int] = None
    net_zero_commitment_year: Optional[int] = None
    notes: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={"example": {
        "entity_name": "Example Bank Singapore",
        "current_stage": 2,
        "tcfd_report_year": 2023,
        "financed_emissions_baseline_year": 2022,
        "net_zero_commitment_year": 2050,
    }})


class SGTActivityCheck(BaseModel):
    sector: str
    activity: str
    entity_name: str

    model_config = ConfigDict(json_schema_extra={"example": {
        "sector": "Energy",
        "activity": "Solar PV generation",
        "entity_name": "Acme Solar Pte Ltd",
    }})


# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────
@router.get("/erm/principles", summary="MAS ERM principles checklist")
async def get_erm_principles():
    return {
        "framework": "MAS Guidelines on Environmental Risk Management (Banks) 2022",
        "url": "https://www.mas.gov.sg/regulation/guidelines/guidelines-on-environmental-risk-management",
        "principles": MAS_ERM_PRINCIPLES,
    }


@router.post("/erm/self-assessment", summary="Submit ERM self-assessment and receive compliance score")
async def submit_erm_assessment(assessment: ERMSelfAssessment):
    compliant = sum(1 for v in assessment.responses.values() if v == "Compliant")
    partial = sum(1 for v in assessment.responses.values() if v == "Partial")
    total = len(MAS_ERM_PRINCIPLES)
    score_pct = round((compliant + 0.5 * partial) / total * 100, 1)

    if score_pct >= 80:
        status = "Largely Compliant"
        rag = "GREEN"
    elif score_pct >= 50:
        status = "Partially Compliant"
        rag = "AMBER"
    else:
        status = "Not Compliant"
        rag = "RED"

    gaps = [
        p for p in MAS_ERM_PRINCIPLES
        if assessment.responses.get(p["id"]) in (None, "Not Started")
    ]

    return {
        "score_pct": score_pct,
        "status": status,
        "rag": rag,
        "compliant_count": compliant,
        "partial_count": partial,
        "not_started_count": total - compliant - partial,
        "gaps": gaps,
    }


@router.get("/notice-637/requirements", summary="MAS Notice 637 Pillar 2 environmental risk requirements")
async def get_notice_637():
    return {
        "framework": "MAS Notice 637 — Risk Based Capital Adequacy Requirements (incl. Pillar 2 env. risk)",
        "items": MAS_NOTICE_637_ITEMS,
    }


@router.get("/sgt/sectors", summary="Singapore Green and Transition Taxonomy sectors")
async def get_sgt_sectors():
    return {
        "taxonomy": "Singapore Green and Transition Taxonomy v2.0 (2024)",
        "url": "https://www.mas.gov.sg/development/sustainable-finance/singapore-green-and-transition-taxonomy",
        "sectors": SGT_SECTORS,
    }


@router.post("/sgt/check-activity", summary="Check if an activity qualifies under SGT")
async def check_sgt_activity(request: SGTActivityCheck):
    sector_data = next((s for s in SGT_SECTORS if s["sector"].lower() == request.sector.lower()), None)
    if not sector_data:
        raise HTTPException(status_code=404, detail=f"Sector '{request.sector}' not found in SGT taxonomy")

    matched = any(
        request.activity.lower() in a.lower() or a.lower() in request.activity.lower()
        for a in sector_data["activities"]
    )

    return {
        "entity_name": request.entity_name,
        "sector": request.sector,
        "activity": request.activity,
        "qualifies": matched,
        "status": "GREEN — qualifies for SGT classification" if matched else "RED — activity not in SGT eligible list. Review taxonomy criteria.",
        "eligible_activities_in_sector": sector_data["activities"],
    }


@router.get("/slgs/stages", summary="SLGS application stages")
async def get_slgs_stages():
    return {
        "programme": "Singapore Green Lane for Sustainability (SLGS)",
        "description": "MAS incentive programme for financial institutions demonstrating strong climate action",
        "stages": SLGS_STAGES,
    }


@router.post("/slgs/application", summary="Track SLGS application progress")
async def track_slgs_application(application: SLGSApplication):
    current = next((s for s in SLGS_STAGES if s["stage"] == application.current_stage), None)
    next_stage = next((s for s in SLGS_STAGES if s["stage"] == application.current_stage + 1), None)

    checklist = []
    if not application.tcfd_report_year:
        checklist.append("Publish TCFD-aligned annual report")
    if not application.financed_emissions_baseline_year:
        checklist.append("Establish financed emissions baseline (PCAF methodology)")
    if not application.net_zero_commitment_year:
        checklist.append("Make public net-zero commitment with interim 2030 target")

    return {
        "entity_name": application.entity_name,
        "current_stage": current,
        "next_stage": next_stage,
        "completion_pct": round(application.current_stage / len(SLGS_STAGES) * 100, 0),
        "outstanding_checklist": checklist,
        "on_track": len(checklist) == 0,
    }
