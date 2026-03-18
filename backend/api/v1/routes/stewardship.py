"""
API Routes: Stewardship Engine (E6)
=====================================
POST /api/v1/stewardship/portfolio           — Full portfolio stewardship assessment
POST /api/v1/stewardship/engagement          — Single-company engagement assessment
POST /api/v1/stewardship/proxy-votes         — Proxy voting alignment analysis
POST /api/v1/stewardship/escalation          — Escalation plan for a company
GET  /api/v1/stewardship/ref/engagement-types  — GFANZ engagement type registry
GET  /api/v1/stewardship/ref/proxy-resolutions — Climate proxy resolution types
GET  /api/v1/stewardship/ref/initiatives       — Collaborative initiative registry
GET  /api/v1/stewardship/ref/escalation-ladder — Escalation ladder (GFANZ-E-2)
GET  /api/v1/stewardship/ref/frameworks        — GFANZ/NZAMI/NZIF/CA100+ reference
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.stewardship_engine import (
    StewardshipEngine,
    EngagementInput,
    ProxyVoteInput,
    ENGAGEMENT_TYPES,
    PROXY_RESOLUTION_TYPES,
    COLLABORATIVE_INITIATIVES,
    ESCALATION_LADDER,
    CA100_FOCUS_SECTORS,
    GFANZ_MILESTONES,
)

router = APIRouter(prefix="/api/v1/stewardship", tags=["Stewardship"])

_ENGINE = StewardshipEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class EngagementInputModel(BaseModel):
    company_id: str
    company_name: str
    sector_nace: str = Field("C24", description="NACE sector code, e.g. D35 for Electric Utilities")
    exposure_eur: float = Field(..., ge=0)
    engagement_start_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")
    engagement_types: List[str] = Field(
        default_factory=list,
        description="List of engagement types from /ref/engagement-types"
    )
    objectives_set: bool = False
    milestone_achieved: bool = False
    engagement_outcome: str = Field(
        "ongoing", description="ongoing | positive | stalled | failed"
    )
    months_since_last_contact: int = Field(0, ge=0)
    is_ca100_focus: bool = False
    portfolio_weight_pct: float = Field(0.0, ge=0, le=100)


class ProxyVoteInputModel(BaseModel):
    company_id: str
    company_name: str
    agm_date: str = Field(..., description="AGM date ISO YYYY-MM-DD")
    resolutions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of resolutions: {type, description, management_recommendation, voted_for}"
    )


class PortfolioStewardshipRequest(BaseModel):
    entity_name: str
    engagements: List[EngagementInputModel]
    proxy_votes: Optional[List[ProxyVoteInputModel]] = None
    initiative_memberships: Optional[Dict[str, str]] = Field(
        None,
        description="Dict {initiative_id: status} e.g. {\"CA100_PLUS\": \"member\"}"
    )
    assessment_date: Optional[str] = None


class SingleEngagementRequest(BaseModel):
    engagement: EngagementInputModel


class EscalationRequest(BaseModel):
    engagement: EngagementInputModel


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _eng_result_to_dict(r) -> Dict[str, Any]:
    return {
        "company_id": r.company_id,
        "company_name": r.company_name,
        "sector": r.sector,
        "exposure_eur": r.exposure_eur,
        "engagement_score": r.engagement_score,
        "effectiveness_rating": r.effectiveness_rating,
        "engagement_types": r.engagement_types,
        "total_actions": r.total_actions,
        "escalation_recommended": r.escalation_recommended,
        "recommended_next_action": r.recommended_next_action,
        "escalation_level": r.escalation_level,
        "gfanz_milestone": r.gfanz_milestone,
        "ca100_relevant": r.ca100_relevant,
        "gaps": r.gaps,
        "notes": r.notes,
    }


def _proxy_result_to_dict(r) -> Dict[str, Any]:
    return {
        "company_id": r.company_id,
        "company_name": r.company_name,
        "agm_date": r.agm_date,
        "total_resolutions": r.total_resolutions,
        "climate_resolutions": r.climate_resolutions,
        "alignment_score": r.alignment_score,
        "nzami_aligned_votes": r.nzami_aligned_votes,
        "nzami_misaligned_votes": r.nzami_misaligned_votes,
        "vote_breakdown": r.vote_breakdown,
        "recommendations": r.recommendations,
    }


def _initiative_to_dict(r) -> Dict[str, Any]:
    return {
        "initiative_id": r.initiative_id,
        "initiative_name": r.initiative_name,
        "participation_status": r.participation_status,
        "min_actions_required": r.min_actions_required,
        "actions_completed": r.actions_completed,
        "coverage_pct": r.coverage_pct,
        "gaps": r.gaps,
        "recommendations": r.recommendations,
    }


def _escalation_to_dict(r) -> Dict[str, Any]:
    return {
        "company_id": r.company_id,
        "company_name": r.company_name,
        "current_escalation_level": r.current_escalation_level,
        "recommended_escalation_level": r.recommended_escalation_level,
        "trigger_met": r.trigger_met,
        "months_stalled": r.months_stalled,
        "recommended_action": r.recommended_action,
        "action_deadline": r.action_deadline,
        "regulatory_rationale": r.regulatory_rationale,
        "escalation_ladder": r.escalation_ladder,
    }


def _portfolio_result_to_dict(r) -> Dict[str, Any]:
    return {
        "run_id": r.run_id,
        "entity_name": r.entity_name,
        "assessment_date": r.assessment_date,
        "total_companies": r.total_companies,
        "total_exposure_eur": r.total_exposure_eur,
        "headline": {
            "engaged_companies": r.engaged_companies,
            "engagement_coverage_pct": r.engagement_coverage_pct,
            "gfanz_milestone": r.gfanz_milestone,
            "avg_engagement_score": r.avg_engagement_score,
            "advanced_engagements": r.advanced_engagements,
            "escalations_recommended": r.escalations_recommended,
        },
        "proxy_voting": {
            "proxy_alignment_score": r.proxy_alignment_score,
            "nzami_aligned_votes_pct": r.nzami_aligned_votes_pct,
        },
        "initiative_participations": [_initiative_to_dict(i) for i in r.initiative_participations],
        "company_results": [_eng_result_to_dict(c) for c in r.company_results],
        "escalation_plans": [_escalation_to_dict(e) for e in r.escalation_plans],
        "gaps": r.gaps,
        "priority_actions": r.priority_actions,
        "framework_coverage": r.framework_coverage,
        "metadata": r.metadata,
    }


def _to_eng_domain(m: EngagementInputModel) -> EngagementInput:
    return EngagementInput(**m.model_dump())


def _to_proxy_domain(m: ProxyVoteInputModel) -> ProxyVoteInput:
    return ProxyVoteInput(**m.model_dump())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/portfolio",
    summary="Full portfolio stewardship assessment",
    description=(
        "Assesses engagement effectiveness, proxy voting alignment, "
        "collaborative initiative participation, and escalation plans "
        "across all portfolio companies. Aligned to GFANZ-E-1/E-2, NZAMI, NZIF-4.2, CA100+."
    ),
)
def assess_portfolio(req: PortfolioStewardshipRequest):
    result = _ENGINE.assess_portfolio(
        entity_name=req.entity_name,
        engagements=[_to_eng_domain(e) for e in req.engagements],
        proxy_votes=[_to_proxy_domain(v) for v in req.proxy_votes] if req.proxy_votes else None,
        initiative_memberships=req.initiative_memberships,
        assessment_date=req.assessment_date,
    )
    return _portfolio_result_to_dict(result)


@router.post(
    "/engagement",
    summary="Single-company engagement effectiveness assessment",
)
def assess_single_engagement(req: SingleEngagementRequest):
    result = _ENGINE.assess_engagement(_to_eng_domain(req.engagement))
    return _eng_result_to_dict(result)


@router.post(
    "/proxy-votes",
    summary="Proxy voting alignment analysis for an AGM",
    description=(
        "Scores proxy votes against expected climate-aligned positions "
        "per NZAMI commitments and GFANZ-E-1. Returns NZAMI-critical vote alignment."
    ),
)
def assess_proxy_votes(req: ProxyVoteInputModel):
    result = _ENGINE.assess_proxy_votes(_to_proxy_domain(req))
    return _proxy_result_to_dict(result)


@router.post(
    "/escalation",
    summary="Escalation plan for a portfolio company",
    description=(
        "Determines if assertive stewardship escalation is required per GFANZ-E-2. "
        "Returns current escalation level, trigger status, and recommended next action."
    ),
)
def assess_escalation(req: EscalationRequest):
    result = _ENGINE.assess_escalation(_to_eng_domain(req.engagement))
    return _escalation_to_dict(result)


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/engagement-types", summary="GFANZ engagement type registry")
def ref_engagement_types():
    return {
        "count": len(ENGAGEMENT_TYPES),
        "engagement_types": ENGAGEMENT_TYPES,
        "reference": "GFANZ Net Zero Implementation Guide — Stewardship (2023)",
    }


@router.get("/ref/proxy-resolutions", summary="Climate proxy resolution types and expected votes")
def ref_proxy_resolutions():
    return {
        "count": len(PROXY_RESOLUTION_TYPES),
        "resolution_types": PROXY_RESOLUTION_TYPES,
        "reference": "NZAMI — Voting and Engagement Guidelines (2023) / UNPRI Principle 2",
    }


@router.get("/ref/initiatives", summary="Collaborative investor initiative registry")
def ref_initiatives():
    return {
        "count": len(COLLABORATIVE_INITIATIVES),
        "initiatives": COLLABORATIVE_INITIATIVES,
        "reference": "GFANZ / CA100+ / NZIF / UNPRI",
    }


@router.get("/ref/escalation-ladder", summary="Stewardship escalation ladder (GFANZ-E-2)")
def ref_escalation_ladder():
    return {
        "steps": len(ESCALATION_LADDER),
        "escalation_ladder": ESCALATION_LADDER,
        "engagement_type_details": {
            step["action"]: ENGAGEMENT_TYPES.get(step["action"], {})
            for step in ESCALATION_LADDER
        },
        "reference": "GFANZ Net Zero Implementation Guide — Escalation to Assertive Stewardship",
    }


@router.get("/ref/frameworks", summary="Stewardship framework cross-reference")
def ref_frameworks():
    return {
        "frameworks": {
            "GFANZ-E-1": {
                "title": "Active stewardship with portfolio companies",
                "metric": "% portfolio companies engaged",
                "milestones": GFANZ_MILESTONES,
            },
            "GFANZ-E-2": {
                "title": "Escalation to assertive stewardship",
                "trigger": "Company not progressing after 6–18 months of engagement",
                "escalation_ladder": ESCALATION_LADDER,
            },
            "NZAMI": {
                "title": "Net Zero Asset Managers Initiative — stewardship commitment",
                "requirement": "Vote in line with net zero commitments at all AGMs",
                "nzami_critical_resolutions": [
                    k for k, v in PROXY_RESOLUTION_TYPES.items() if v.get("nzami_critical")
                ],
            },
            "NZIF_4_2": {
                "title": "Net Zero Investment Framework — Objective 4.2",
                "requirement": "Corporate bonds: issuer alignment + stewardship",
                "engagement_score_threshold": 50,
            },
            "CA100_PLUS": {
                "title": "Climate Action 100+ — focus sectors",
                "focus_sectors": CA100_FOCUS_SECTORS,
                "approach": "Collaborative engagement with 170+ systemically important emitters",
            },
            "UNPRI_P2": {
                "title": "UN Principles for Responsible Investment — Principle 2",
                "requirement": "Active owners — incorporate ESG into ownership policies and practices",
            },
        },
        "reference": (
            "GFANZ Net Zero Implementation Guide (2023) | "
            "NZAMI Commitment Document (2021) | "
            "CA100+ Engagement Framework (2023) | "
            "UNPRI Principles (2022)"
        ),
    }
