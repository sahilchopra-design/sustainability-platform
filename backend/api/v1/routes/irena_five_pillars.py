"""
IRENA Five Pillars Energy Transition Assessment
Based on: IRENA World Energy Transitions Outlook 2023
           IRENA Energy Transition Readiness Assessment Framework

Five Pillars:
  1. Physical Infrastructure (grid, storage, interconnectors)
  2. Policy & Regulation (RE targets, carbon pricing, subsidy reform)
  3. Financing & Investment (green bonds, blended finance, risk mitigation)
  4. Human Capital & Institutional Capacity (skills, R&D, workforce)
  5. Technology & Innovation (RE deployment, efficiency, digitalisation)
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/irena-five-pillars", tags=["IRENA Five Pillars"])


# -- Scoring rubrics (simplified from IRENA ETAF) --
PILLARS = [
    {
        "id": "infrastructure",
        "name": "Physical Infrastructure",
        "weight": 0.25,
        "criteria": [
            {"id": "grid_capacity", "label": "Grid Capacity & Reliability", "max": 10},
            {"id": "storage_deployment", "label": "Energy Storage Deployment", "max": 10},
            {"id": "interconnectors", "label": "Cross-border Interconnectors", "max": 10},
            {"id": "ev_charging", "label": "EV Charging Infrastructure", "max": 10},
            {"id": "smart_grid", "label": "Smart Grid & Digitalisation", "max": 10},
        ],
    },
    {
        "id": "policy",
        "name": "Policy & Regulation",
        "weight": 0.25,
        "criteria": [
            {"id": "re_target", "label": "Renewable Energy Target (NDC)", "max": 10},
            {"id": "carbon_pricing", "label": "Carbon Pricing Mechanism", "max": 10},
            {"id": "fossil_subsidy_reform", "label": "Fossil Fuel Subsidy Reform", "max": 10},
            {"id": "permitting", "label": "Permitting & Grid Access", "max": 10},
            {"id": "auction_framework", "label": "RE Auction Framework", "max": 10},
        ],
    },
    {
        "id": "financing",
        "name": "Financing & Investment",
        "weight": 0.20,
        "criteria": [
            {"id": "re_investment_flow", "label": "RE Investment Volume", "max": 10},
            {"id": "green_bond_market", "label": "Green Bond Market", "max": 10},
            {"id": "blended_finance", "label": "Blended Finance Availability", "max": 10},
            {"id": "risk_mitigation", "label": "Risk Mitigation Instruments", "max": 10},
            {"id": "private_sector", "label": "Private Sector Participation", "max": 10},
        ],
    },
    {
        "id": "human_capital",
        "name": "Human Capital & Institutional Capacity",
        "weight": 0.15,
        "criteria": [
            {"id": "workforce_skills", "label": "RE Workforce & Skills", "max": 10},
            {"id": "rd_spending", "label": "Energy R&D Spending", "max": 10},
            {"id": "institutional_capacity", "label": "Institutional Capacity", "max": 10},
            {"id": "just_transition", "label": "Just Transition Planning", "max": 10},
            {"id": "gender_inclusion", "label": "Gender & Inclusion in Energy", "max": 10},
        ],
    },
    {
        "id": "technology",
        "name": "Technology & Innovation",
        "weight": 0.15,
        "criteria": [
            {"id": "re_share_generation", "label": "RE Share in Generation (%)", "max": 10},
            {"id": "efficiency_improvement", "label": "Energy Efficiency Progress", "max": 10},
            {"id": "green_hydrogen", "label": "Green Hydrogen Readiness", "max": 10},
            {"id": "electrification", "label": "Sector Electrification Rate", "max": 10},
            {"id": "innovation_ecosystem", "label": "Innovation Ecosystem", "max": 10},
        ],
    },
]


class PillarScoreInput(BaseModel):
    """Scores for a single pillar (each criterion: 0-10)."""
    pillar_id: str
    scores: Dict[str, float]  # criterion_id -> score (0-10)


class FivePillarsRequest(BaseModel):
    entity_name: str = "Country / Organisation"
    entity_type: str = Field("country", description="country | organisation | project")
    country_iso2: str = "DE"
    assessment_year: int = 2025
    pillar_scores: List[PillarScoreInput]
    notes: Optional[str] = None


class CriterionResult(BaseModel):
    id: str
    label: str
    score: float
    max_score: float
    pct: float


class PillarResult(BaseModel):
    id: str
    name: str
    weight: float
    criteria: List[CriterionResult]
    raw_score: float
    max_score: float
    pct: float
    weighted_score: float
    rating: str


class FivePillarsResponse(BaseModel):
    entity_name: str
    entity_type: str
    country_iso2: str
    assessment_year: int
    pillar_results: List[PillarResult]
    overall_score: float
    overall_max: float
    overall_pct: float
    overall_rating: str
    transition_readiness: str
    gap_analysis: List[Dict[str, Any]]
    recommendations: List[str]
    country_benchmarks: Dict[str, Any]


def _rating(pct: float) -> str:
    if pct >= 80:
        return "Advanced"
    if pct >= 60:
        return "Progressing"
    if pct >= 40:
        return "Emerging"
    return "Early Stage"


def _readiness(pct: float) -> str:
    if pct >= 80:
        return "Transition-Ready"
    if pct >= 60:
        return "On Track"
    if pct >= 40:
        return "Needs Acceleration"
    return "Significant Gaps"


@router.get("/framework")
def get_framework():
    """Return the IRENA Five Pillars scoring framework (criteria, weights, max scores)."""
    return {"pillars": PILLARS}


@router.post("/assess", response_model=FivePillarsResponse)
def assess_five_pillars(req: FivePillarsRequest, db: Session = Depends(get_db)):
    """Run the IRENA Five Pillars transition readiness assessment."""

    # Build lookup: pillar_id -> {criterion_id -> score}
    input_map = {ps.pillar_id: ps.scores for ps in req.pillar_scores}

    pillar_results = []
    total_weighted = 0.0
    total_max_weighted = 0.0
    gap_analysis = []

    for pillar in PILLARS:
        pid = pillar["id"]
        scores_in = input_map.get(pid, {})

        criteria_out = []
        raw = 0.0
        max_s = 0.0

        for crit in pillar["criteria"]:
            val = min(max(scores_in.get(crit["id"], 0), 0), crit["max"])
            pct = round(val / crit["max"] * 100, 1) if crit["max"] > 0 else 0
            criteria_out.append(CriterionResult(
                id=crit["id"], label=crit["label"],
                score=val, max_score=crit["max"], pct=pct,
            ))
            raw += val
            max_s += crit["max"]

            # Gap: anything below 50% is flagged
            if pct < 50:
                gap_analysis.append({
                    "pillar": pillar["name"],
                    "criterion": crit["label"],
                    "score": val,
                    "max": crit["max"],
                    "pct": pct,
                    "gap_to_50pct": round(crit["max"] * 0.5 - val, 1),
                })

        pct = round(raw / max_s * 100, 1) if max_s > 0 else 0
        weighted = pct * pillar["weight"]
        total_weighted += weighted
        total_max_weighted += 100 * pillar["weight"]

        pillar_results.append(PillarResult(
            id=pid, name=pillar["name"], weight=pillar["weight"],
            criteria=criteria_out,
            raw_score=round(raw, 1), max_score=max_s,
            pct=pct, weighted_score=round(weighted, 2),
            rating=_rating(pct),
        ))

    overall_pct = round(total_weighted / total_max_weighted * 100, 1) if total_max_weighted > 0 else 0
    overall_max = sum(sum(c["max"] for c in p["criteria"]) for p in PILLARS)
    overall_raw = sum(pr.raw_score for pr in pillar_results)

    # Sort gaps by severity
    gap_analysis.sort(key=lambda g: g["pct"])

    # Recommendations
    recs = []
    weakest = sorted(pillar_results, key=lambda p: p.pct)
    for p in weakest[:2]:
        if p.pct < 60:
            recs.append(f"Priority: Strengthen {p.name} (currently {p.pct}% - {p.rating})")
    for g in gap_analysis[:3]:
        recs.append(f"Address gap: {g['criterion']} under {g['pillar']} ({g['pct']}%)")
    if overall_pct >= 60:
        recs.append("Maintain momentum on strongest pillars to achieve transition-readiness")

    # Country benchmarks from DB (CPI, FSI, Freedom House)
    country_benchmarks = {}
    try:
        iso3_row = db.execute(text(
            "SELECT country_iso3, country_name FROM dh_country_risk_indices "
            "WHERE country_iso2 = :iso2 LIMIT 1"
        ), {"iso2": req.country_iso2}).fetchone()
        if iso3_row:
            iso3 = iso3_row[0]
            rows = db.execute(text(
                "SELECT index_name, score, rank FROM dh_country_risk_indices "
                "WHERE country_iso3 = :iso3 ORDER BY year DESC"
            ), {"iso3": iso3}).fetchall()
            for r in rows:
                if r[0] not in country_benchmarks:
                    country_benchmarks[r[0]] = {"score": float(r[1]) if r[1] else None, "rank": r[2]}
            country_benchmarks["country_name"] = iso3_row[1]
    except Exception:
        pass

    return FivePillarsResponse(
        entity_name=req.entity_name,
        entity_type=req.entity_type,
        country_iso2=req.country_iso2,
        assessment_year=req.assessment_year,
        pillar_results=pillar_results,
        overall_score=round(overall_raw, 1),
        overall_max=overall_max,
        overall_pct=overall_pct,
        overall_rating=_rating(overall_pct),
        transition_readiness=_readiness(overall_pct),
        gap_analysis=gap_analysis,
        recommendations=recs,
        country_benchmarks=country_benchmarks,
    )
