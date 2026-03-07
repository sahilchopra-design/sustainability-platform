"""
SAT Coal Phase-Out Criteria Checker
IEA Net Zero Emissions by 2050 Scenario / IPCC AR6 / NZBA Guidelines

Evaluates counterparties and power assets against coal phase-out criteria
aligned with:
  - IEA NZE 2050: No new unabated coal plants from 2021; OECD phase-out by 2030
  - IPCC AR6: Coal power must fall ~80% by 2030 (from 2020 levels)
  - NZBA: No new project-level coal financing; phase-out by 2030/2040
  - Powering Past Coal Alliance (PPCA) commitment benchmarks

Includes:
  - Entity-level coal exposure assessment
  - Revenue dependency scoring (thermal coal as % of total)
  - Expansion pipeline check (new mines / plants post-2021)
  - Just Transition adequacy scoring
  - Portfolio-level coal concentration risk
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sat-coal", tags=["SAT Coal Phase-Out"])


# ── Thresholds (IEA NZE + NZBA) ───────────────────────────────────────

COAL_REVENUE_THRESHOLDS = {
    "exclusion": 25.0,        # >25% thermal coal revenue = exclusion candidate
    "watchlist": 10.0,        # 10-25% = watchlist / engagement
    "acceptable": 5.0,        # <5% = generally acceptable (declining)
}

PHASE_OUT_DEADLINES = {
    "OECD": 2030,
    "non_OECD": 2040,
    "IEA_NZE_no_new": 2021,   # No new unabated coal from 2021
}

# Coal capacity pipeline status categories (GEM tracker)
PIPELINE_RISK = {
    "announced":     "HIGH -- New capacity announced",
    "pre-permit":    "HIGH -- Pre-permit development",
    "permitted":     "HIGH -- Permitted, not yet constructed",
    "construction":  "CRITICAL -- Under construction",
    "operating":     "MEDIUM -- Existing operation",
    "mothballed":    "LOW -- Mothballed/suspended",
    "retired":       "NONE -- Retired",
    "cancelled":     "NONE -- Cancelled",
    "shelved":       "LOW -- Shelved",
}


# ── Models ─────────────────────────────────────────────────────────────

class CoalExposureInput(BaseModel):
    """Single counterparty / asset coal exposure data."""
    entity_id: str
    entity_name: str
    country_iso: str = "DE"
    is_oecd: bool = True
    sector: str = Field("Utilities", description="Utilities | Mining | Diversified | Other")

    # Revenue & production
    total_revenue_eur: float = Field(..., gt=0)
    thermal_coal_revenue_eur: float = Field(0, ge=0)
    thermal_coal_revenue_pct: Optional[float] = None  # Auto-calculated if not provided
    coal_production_mt: float = Field(0, ge=0, description="Annual thermal coal production (Mt)")

    # Power fleet
    total_generation_capacity_mw: float = Field(0, ge=0)
    coal_capacity_mw: float = Field(0, ge=0)
    coal_capacity_pct: Optional[float] = None
    coal_generation_gwh: float = Field(0, ge=0)
    total_generation_gwh: float = Field(0, ge=0)

    # Phase-out criteria (IEA NZE / NZBA)
    no_new_coal_since_2021: bool = False
    has_phase_out_commitment: bool = False
    phase_out_target_year: Optional[int] = None
    has_transition_plan: bool = False
    transition_plan_verified: bool = False
    has_just_transition_plan: bool = False
    coal_revenue_declining_yoy: bool = False

    # Expansion pipeline
    new_coal_projects_announced: int = Field(0, ge=0)
    coal_expansion_capex_eur: float = Field(0, ge=0)

    # CCS / abatement
    has_ccs: bool = False
    ccs_capture_rate_pct: float = Field(0, ge=0, le=100)

    # Financial exposure
    fi_outstanding_eur: Optional[float] = Field(None, ge=0, description="FI loan/bond exposure")


class CoalCriterionResult(BaseModel):
    criterion_id: str
    criterion_name: str
    met: bool
    score: float     # 0-10
    max_score: float  # 10
    detail: str
    source: str


class CoalEntityResult(BaseModel):
    entity_id: str
    entity_name: str
    country_iso: str
    sector: str

    # Revenue scoring
    thermal_coal_revenue_pct: float
    revenue_classification: str   # "Exclusion" | "Watchlist" | "Engagement" | "Acceptable"

    # Capacity scoring
    coal_capacity_pct: float
    coal_generation_pct: float

    # Phase-out criteria (5 IEA/NZBA checkpoints)
    criteria_results: List[CoalCriterionResult]
    criteria_met: int
    criteria_total: int

    # Overall
    overall_score: float          # 0-100
    rag_status: str               # GREEN | AMBER | RED
    rag_detail: str
    phase_out_aligned: bool
    recommendation: str

    # Pipeline risk
    expansion_risk: str
    expansion_detail: str


class CoalCheckerRequest(BaseModel):
    entities: List[CoalExposureInput]
    assessment_year: int = 2025
    apply_nzba_policy: bool = True
    apply_iea_nze: bool = True


class CoalCheckerResponse(BaseModel):
    assessment_year: int
    total_entities: int
    entities_aligned: int
    entities_watchlist: int
    entities_exclusion: int
    portfolio_coal_exposure_pct: float
    portfolio_rag: str
    entity_results: List[CoalEntityResult]
    policy_reference: Dict[str, Any]
    gem_coal_data: Optional[Dict[str, Any]] = None


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/check", response_model=CoalCheckerResponse)
def check_coal_phase_out(req: CoalCheckerRequest, db: Session = Depends(get_db)):
    """
    Evaluate counterparties against IEA NZE / NZBA coal phase-out criteria.
    Returns per-entity RAG status and portfolio-level coal concentration.
    """
    if not req.entities:
        raise HTTPException(400, "At least one entity required")

    entity_results = []
    total_exposure = 0.0
    coal_exposure = 0.0
    aligned_count = 0
    watchlist_count = 0
    exclusion_count = 0

    for e in req.entities:
        result = _assess_entity(e, req.assessment_year, req.apply_nzba_policy, req.apply_iea_nze)
        entity_results.append(result)

        fi_exp = e.fi_outstanding_eur or e.total_revenue_eur
        total_exposure += fi_exp
        coal_exposure += fi_exp * (result.thermal_coal_revenue_pct / 100)

        if result.rag_status == "GREEN":
            aligned_count += 1
        elif result.rag_status == "AMBER":
            watchlist_count += 1
        else:
            exclusion_count += 1

    portfolio_coal_pct = round(coal_exposure / total_exposure * 100, 2) if total_exposure > 0 else 0

    if exclusion_count > 0 or portfolio_coal_pct > 10:
        portfolio_rag = "RED"
    elif watchlist_count > 0 or portfolio_coal_pct > 5:
        portfolio_rag = "AMBER"
    else:
        portfolio_rag = "GREEN"

    # GEM Coal Plant Tracker data from DB
    gem_data = _get_gem_coal_summary(db)

    return CoalCheckerResponse(
        assessment_year=req.assessment_year,
        total_entities=len(req.entities),
        entities_aligned=aligned_count,
        entities_watchlist=watchlist_count,
        entities_exclusion=exclusion_count,
        portfolio_coal_exposure_pct=portfolio_coal_pct,
        portfolio_rag=portfolio_rag,
        entity_results=entity_results,
        policy_reference={
            "iea_nze": "IEA Net Zero Emissions by 2050 Scenario (2021 update)",
            "ipcc_ar6": "IPCC AR6 WGIII: coal power -80% by 2030 from 2020",
            "nzba": "Net Zero Banking Alliance Guidelines (UNEP FI, 2022)",
            "ppca": "Powering Past Coal Alliance",
            "thresholds": COAL_REVENUE_THRESHOLDS,
            "deadlines": PHASE_OUT_DEADLINES,
        },
        gem_coal_data=gem_data,
    )


@router.get("/thresholds")
def get_thresholds():
    """Return coal phase-out thresholds and policy benchmarks."""
    return {
        "revenue_thresholds": COAL_REVENUE_THRESHOLDS,
        "phase_out_deadlines": PHASE_OUT_DEADLINES,
        "pipeline_risk_categories": PIPELINE_RISK,
        "criteria": [
            {"id": "no_new_coal", "name": "No New Coal (IEA NZE)", "source": "IEA NZE 2050",
             "description": "No new unabated coal mine/power plant approvals since 2021"},
            {"id": "phase_out_timeline", "name": "Phase-Out Commitment", "source": "IEA NZE + NZBA",
             "description": "Commitment to phase out by 2030 (OECD) or 2040 (non-OECD)"},
            {"id": "transition_plan", "name": "Credible Transition Plan", "source": "NZBA / GFANZ",
             "description": "Published, verified transition plan with milestones"},
            {"id": "just_transition", "name": "Just Transition", "source": "ILO / PPCA",
             "description": "Worker support, community fund, reskilling programs"},
            {"id": "revenue_declining", "name": "Revenue Declining", "source": "NZBA",
             "description": "Thermal coal revenue < 25% and declining year-on-year"},
        ],
    }


@router.get("/gem-summary")
def get_gem_summary(db: Session = Depends(get_db)):
    """Return GEM Global Coal Plant Tracker summary from reference data."""
    data = _get_gem_coal_summary(db)
    return data or {"message": "No GEM coal data loaded"}


# ── Assessment Logic ───────────────────────────────────────────────────

def _assess_entity(e: CoalExposureInput, year: int, nzba: bool, iea: bool) -> CoalEntityResult:
    """Run 5-criterion coal phase-out assessment for a single entity."""

    # Revenue %
    if e.thermal_coal_revenue_pct is not None:
        coal_rev_pct = e.thermal_coal_revenue_pct
    elif e.total_revenue_eur > 0:
        coal_rev_pct = round(e.thermal_coal_revenue_eur / e.total_revenue_eur * 100, 2)
    else:
        coal_rev_pct = 0.0

    # Revenue classification
    if coal_rev_pct >= COAL_REVENUE_THRESHOLDS["exclusion"]:
        rev_class = "Exclusion"
    elif coal_rev_pct >= COAL_REVENUE_THRESHOLDS["watchlist"]:
        rev_class = "Watchlist"
    elif coal_rev_pct >= COAL_REVENUE_THRESHOLDS["acceptable"]:
        rev_class = "Engagement"
    else:
        rev_class = "Acceptable"

    # Capacity %
    coal_cap_pct = round(e.coal_capacity_mw / e.total_generation_capacity_mw * 100, 2) \
        if e.total_generation_capacity_mw > 0 else 0
    if e.coal_capacity_pct is not None:
        coal_cap_pct = e.coal_capacity_pct

    coal_gen_pct = round(e.coal_generation_gwh / e.total_generation_gwh * 100, 2) \
        if e.total_generation_gwh > 0 else 0

    # ── 5 Phase-Out Criteria ──
    criteria = []

    # C1: No new coal since 2021
    c1_met = e.no_new_coal_since_2021 and e.new_coal_projects_announced == 0
    c1_score = 10.0 if c1_met else (5.0 if e.new_coal_projects_announced <= 1 else 0.0)
    criteria.append(CoalCriterionResult(
        criterion_id="no_new_coal",
        criterion_name="No New Coal (IEA NZE 2050)",
        met=c1_met, score=c1_score, max_score=10.0,
        detail=f"{'No' if c1_met else str(e.new_coal_projects_announced)} new projects since 2021"
               + (f"; CAPEX EUR {e.coal_expansion_capex_eur:,.0f}" if e.coal_expansion_capex_eur > 0 else ""),
        source="IEA NZE by 2050 Scenario, Section 3.2",
    ))

    # C2: Phase-out timeline commitment
    deadline = PHASE_OUT_DEADLINES["OECD"] if e.is_oecd else PHASE_OUT_DEADLINES["non_OECD"]
    c2_met = e.has_phase_out_commitment and (e.phase_out_target_year or 9999) <= deadline
    c2_score = 10.0 if c2_met else (5.0 if e.has_phase_out_commitment else 0.0)
    criteria.append(CoalCriterionResult(
        criterion_id="phase_out_timeline",
        criterion_name=f"Phase-Out by {deadline} ({'OECD' if e.is_oecd else 'non-OECD'})",
        met=c2_met, score=c2_score, max_score=10.0,
        detail=f"Target: {e.phase_out_target_year or 'None'} vs deadline {deadline}"
               + (" -- COMMITTED" if e.has_phase_out_commitment else " -- NO COMMITMENT"),
        source="IEA NZE 2050 + NZBA Guidelines",
    ))

    # C3: Credible transition plan
    c3_met = e.has_transition_plan and e.transition_plan_verified
    c3_score = 10.0 if c3_met else (6.0 if e.has_transition_plan else 0.0)
    criteria.append(CoalCriterionResult(
        criterion_id="transition_plan",
        criterion_name="Credible Transition Plan",
        met=c3_met, score=c3_score, max_score=10.0,
        detail=f"Plan: {'Yes' if e.has_transition_plan else 'No'}"
               + (", Verified" if e.transition_plan_verified else ", Not verified"),
        source="NZBA / GFANZ Transition Plan Framework",
    ))

    # C4: Just Transition
    c4_met = e.has_just_transition_plan
    c4_score = 10.0 if c4_met else 0.0
    criteria.append(CoalCriterionResult(
        criterion_id="just_transition",
        criterion_name="Just Transition Fund / Worker Support",
        met=c4_met, score=c4_score, max_score=10.0,
        detail="Just Transition plan in place" if c4_met else "No Just Transition provisions identified",
        source="ILO Guidelines for a Just Transition / PPCA",
    ))

    # C5: Revenue declining
    c5_met = coal_rev_pct < COAL_REVENUE_THRESHOLDS["exclusion"] and e.coal_revenue_declining_yoy
    c5_score = 10.0 if c5_met else (5.0 if e.coal_revenue_declining_yoy else 0.0)
    criteria.append(CoalCriterionResult(
        criterion_id="revenue_declining",
        criterion_name="Thermal Coal Revenue < 25% & Declining",
        met=c5_met, score=c5_score, max_score=10.0,
        detail=f"Coal revenue: {coal_rev_pct:.1f}%"
               + (" -- declining YoY" if e.coal_revenue_declining_yoy else " -- NOT declining"),
        source="NZBA Sub-Sector Guidelines (Coal)",
    ))

    # Overall
    criteria_met = sum(1 for c in criteria if c.met)
    total_score = sum(c.score for c in criteria)
    overall = round(total_score / (len(criteria) * 10) * 100, 1)

    # RAG
    if criteria_met >= 5:
        rag = "GREEN"
        rag_detail = "Coal Phase-Out Aligned -- all criteria met"
    elif criteria_met >= 3:
        rag = "AMBER"
        rag_detail = f"Partially Aligned -- {criteria_met}/5 criteria met; gaps in phase-out commitment"
    else:
        rag = "RED"
        rag_detail = f"Significant Phase-Out Gaps -- only {criteria_met}/5 criteria met"

    # Override to RED if expansion pipeline
    if e.new_coal_projects_announced > 0 and e.coal_expansion_capex_eur > 0:
        rag = "RED"
        rag_detail += " | ACTIVE COAL EXPANSION DETECTED"

    # Override to RED if revenue > exclusion threshold
    if coal_rev_pct >= COAL_REVENUE_THRESHOLDS["exclusion"] and not e.coal_revenue_declining_yoy:
        rag = "RED"
        rag_detail += f" | Coal revenue {coal_rev_pct:.1f}% exceeds {COAL_REVENUE_THRESHOLDS['exclusion']}% exclusion threshold"

    # Expansion risk
    if e.new_coal_projects_announced > 0:
        exp_risk = "HIGH"
        exp_detail = f"{e.new_coal_projects_announced} new coal projects announced"
    elif e.coal_expansion_capex_eur > 0:
        exp_risk = "MEDIUM"
        exp_detail = f"Coal expansion CAPEX: EUR {e.coal_expansion_capex_eur:,.0f}"
    else:
        exp_risk = "LOW"
        exp_detail = "No coal expansion pipeline detected"

    # Recommendation
    if rag == "GREEN":
        rec = "Maintain engagement. Monitor annual disclosures for continued alignment."
    elif rag == "AMBER":
        failed = [c.criterion_name for c in criteria if not c.met]
        rec = f"Escalated engagement required. Address: {'; '.join(failed[:3])}"
    else:
        if coal_rev_pct >= COAL_REVENUE_THRESHOLDS["exclusion"]:
            rec = f"EXCLUSION CANDIDATE: Coal revenue {coal_rev_pct:.1f}% exceeds threshold. " \
                  f"Divest or set binding engagement timeline (max 2 years)."
        else:
            rec = "Intensive engagement with time-bound milestones. " \
                  "Escalate to Board if no progress within 12 months."

    return CoalEntityResult(
        entity_id=e.entity_id,
        entity_name=e.entity_name,
        country_iso=e.country_iso,
        sector=e.sector,
        thermal_coal_revenue_pct=coal_rev_pct,
        revenue_classification=rev_class,
        coal_capacity_pct=coal_cap_pct,
        coal_generation_pct=coal_gen_pct,
        criteria_results=criteria,
        criteria_met=criteria_met,
        criteria_total=5,
        overall_score=overall,
        rag_status=rag,
        rag_detail=rag_detail,
        phase_out_aligned=criteria_met >= 5,
        recommendation=rec,
        expansion_risk=exp_risk,
        expansion_detail=exp_detail,
    )


def _get_gem_coal_summary(db: Session) -> Optional[Dict[str, Any]]:
    """Retrieve GEM Coal Plant Tracker summary from dh_reference_data."""
    try:
        rows = db.execute(text(
            "SELECT entity_name, kpi_name, value "
            "FROM dh_reference_data "
            "WHERE source_name = 'GEM Coal Plant Tracker' "
            "ORDER BY entity_name, kpi_name"
        )).fetchall()
        if not rows:
            return None
        summary = {}
        for r in rows:
            country = r[0]
            if country not in summary:
                summary[country] = {}
            summary[country][r[1]] = float(r[2]) if r[2] else 0
        return {
            "source": "Global Energy Monitor -- Global Coal Plant Tracker",
            "countries": len(summary),
            "data": summary,
        }
    except Exception:
        return None
