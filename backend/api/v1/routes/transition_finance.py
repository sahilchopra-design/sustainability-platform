"""
Transition Finance Credibility Routes  —  E99
==============================================
Prefix: /api/v1/transition-finance
Tags:   Transition Finance — E99

Standards:
  - TPT Disclosure Framework (Oct 2023) + GFANZ Expectations (Nov 2023)
  - SBTi Corporate Net-Zero Standard v1.1 (Sep 2023)
  - Race to Zero 2023 Criteria (UNFCCC)
  - TNFD Recommendations v1.0 (Sep 2023) — LEAP + SBTN
  - ICMA Climate Transition Finance Handbook (Dec 2023)
  - LMA SLL Principles 2023 / LMA Transition Guidance 2023
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.transition_finance_engine import (
    assess_transition_finance_credibility,
    calculate_portfolio_temperature,
    screen_transition_instrument,
    get_transition_benchmarks,
    TPT_ELEMENTS,
    QUALITY_TIERS,
    SBTI_CRITERIA,
    SECTOR_PATHWAYS,
    RACE_TO_ZERO_CRITERIA,
    RTZ_MEMBERSHIP_CATEGORIES,
    GFANZ_EXPECTATIONS,
    TRANSITION_INSTRUMENT_CRITERIA,
)

router = APIRouter(prefix="/api/v1/transition-finance", tags=["Transition Finance — E99"])


# ── Pydantic Request Models ────────────────────────────────────────────────────

class CredibilityAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_name: str = Field(..., description="Name of the entity being assessed")
    sector: str = Field(..., description="Sector key (e.g. 'steel', 'banking_finance'). Use /ref/sector-pathways for options.")
    tpt_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "TPT element inputs. Keys: foundations / implementation / engagement / "
            "metrics_targets / governance / finance. Each value: {score: 0-1} or {tier: 'developing'} "
            "or {sub_scores: [0.8, 0.7, ...]}."
        ),
    )
    sbti_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "SBTi criterion inputs. Keys match SBTI_CRITERIA (near_term_scope12, near_term_scope3, "
            "long_term_scope12, long_term_scope3, net_zero_target, flag_sector). "
            "Each value: {score: 0-1, status: 'validated'|'committed'|'not_applicable'}."
        ),
    )
    rtz_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Race to Zero criterion inputs. Keys: commit / countable / consistent / credible / communicate. "
            "Each value: {score: 0-1}. Also accepts memberships: {gfanz: true, sbti: true, ...}."
        ),
    )
    portfolio_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Portfolio holdings for WACI/temperature. "
            "Provide holdings: [{name, weight, tco2e, revenue_usd_mn, has_sbti, sbti_temperature}]."
        ),
    )
    tnfd_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "TNFD LEAP inputs. "
            "leap_stages_completed: ['L1','L2','L3','L4'], "
            "sbtn_steps_completed: ['Assess','Prioritise','Measure','Set','Disclose'], "
            "nature_targets_set: bool."
        ),
    )


class PortfolioTemperatureRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    holdings: list[dict[str, Any]] = Field(
        ...,
        description=(
            "List of holdings: [{name: str, weight: float, tco2e: float, revenue_usd_mn: float, "
            "has_sbti: bool, sbti_temperature: float}]. Weights need not sum to 1 (normalised internally)."
        ),
        min_length=1,
    )
    engagement_coverage_pct: float | None = Field(None, ge=0, le=100)
    paris_aligned_pct: float | None = Field(None, ge=0, le=100)


class InstrumentScreenRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    instrument_type: str = Field(
        ...,
        description=(
            "transition_bond / sustainability_linked_loan / "
            "transition_loan_facility / blended_finance_transition"
        ),
    )
    entity_name: str = Field(..., description="Issuer or borrower name")
    sector: str = Field(..., description="Borrower/issuer sector key")
    kpis: list[dict[str, Any]] | None = Field(
        None,
        description="KPIs for SLL (e.g. [{name: 'GHG intensity', unit: 'tCO2/revenue', base_value: 50}])",
    )
    spts: list[dict[str, Any]] | None = Field(
        None,
        description="SPTs for SLL (e.g. [{year: 2030, reduction_pct: 30, ambitious: true}])",
    )
    has_transition_plan: bool = Field(False)
    transition_plan_tier: str = Field("developing", description="initial / developing / advanced / leading")
    sbti_status: str = Field(
        "not_committed",
        description="not_committed / committed / validated_near_term / validated_net_zero",
    )
    use_of_proceeds_aligned: bool = Field(False, description="For transition bonds: proceeds fund eligible activities")
    external_reviewer: bool = Field(False, description="Independent external review obtained")


# ── POST Routes ───────────────────────────────────────────────────────────────

@router.post("/assess", summary="Full transition finance credibility assessment")
async def assess_credibility(req: CredibilityAssessmentRequest) -> dict[str, Any]:
    """
    Full credibility assessment covering:
    - TPT 6-element scoring (weighted composite)
    - SBTi Corporate Net-Zero Standard v1.1 criteria
    - Race to Zero 5 Cs (Commit / Countable / Consistent / Credible / Communicate)
    - Portfolio WACI temperature alignment
    - TNFD LEAP nature integration (4 stages + SBTN 5 steps)
    - Overall credibility composite + red flag / greenwash detection
    """
    try:
        return assess_transition_finance_credibility(
            entity_name=req.entity_name,
            sector=req.sector,
            tpt_inputs=req.tpt_inputs,
            sbti_inputs=req.sbti_inputs,
            rtz_inputs=req.rtz_inputs,
            portfolio_inputs=req.portfolio_inputs,
            tnfd_inputs=req.tnfd_inputs,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/portfolio-temperature", summary="Portfolio WACI and implied temperature calculation")
async def portfolio_temperature(req: PortfolioTemperatureRequest) -> dict[str, Any]:
    """
    Calculate:
    - WACI (Weighted Average Carbon Intensity) = Σ(weight_i × tCO2e_i / revenue_i_M)
    - Implied portfolio temperature (°C) via WACI-temperature mapping
    - SBTi-weighted temperature (where SBTi data provided)
    - Engagement coverage % and Paris-aligned holdings %
    """
    try:
        return calculate_portfolio_temperature(
            holdings=req.holdings,
            engagement_coverage_pct=req.engagement_coverage_pct,
            paris_aligned_pct=req.paris_aligned_pct,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/instrument-screen", summary="Transition instrument credibility screen")
async def instrument_screen(req: InstrumentScreenRequest) -> dict[str, Any]:
    """
    Screen a transition finance instrument against credibility criteria:
    - Transition Bond (ICMA Climate Transition Finance Handbook 2023)
    - Sustainability-Linked Loan (LMA SLL Principles 2023)
    - Transition Loan Facility (LMA Transition Guidance 2023)
    - Blended Finance — Transition (Convergence / OECD DAC)
    """
    try:
        return screen_transition_instrument(
            instrument_type=req.instrument_type,
            entity_name=req.entity_name,
            sector=req.sector,
            kpis=req.kpis,
            spts=req.spts,
            has_transition_plan=req.has_transition_plan,
            transition_plan_tier=req.transition_plan_tier,
            sbti_status=req.sbti_status,
            use_of_proceeds_aligned=req.use_of_proceeds_aligned,
            external_reviewer=req.external_reviewer,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ── GET Reference Routes ──────────────────────────────────────────────────────

@router.get("/ref/tpt-elements", summary="TPT 6 elements + weights + quality tiers")
async def ref_tpt_elements() -> dict[str, Any]:
    """
    Return the 6 TPT Disclosure Framework elements with weights, sub-elements,
    and quality tier descriptions (initial / developing / advanced / leading).
    """
    return {
        "source": "Transition Plan Taskforce Disclosure Framework, October 2023",
        "elements": TPT_ELEMENTS,
        "quality_tiers": QUALITY_TIERS,
        "total_weight": sum(e["weight"] for e in TPT_ELEMENTS.values()),
        "element_weights_summary": {
            e_id: {"name": e["name"], "weight": e["weight"]}
            for e_id, e in TPT_ELEMENTS.items()
        },
        "composite_scoring": "weighted sum of 6 elements; ≥80% = leading; 60-80% = advanced; 40-60% = developing; <40% = initial",
    }


@router.get("/ref/sbti-criteria", summary="SBTi validation criteria + sector pathways")
async def ref_sbti_criteria() -> dict[str, Any]:
    """
    Return SBTi Corporate Net-Zero Standard v1.1 validation criteria including:
    near-term (Scope 1+2 ≥42% by 2030; S3 ≥25%), long-term (S1+2 ≥90% by 2050),
    net-zero target, and FLAG sector guidance.
    """
    return {
        "source": "SBTi Corporate Net-Zero Standard v1.1, September 2023",
        "standard_version": "v1.1",
        "criteria": SBTI_CRITERIA,
        "validation_process": {
            "step_1": "Submit letter of commitment (SBTi Committed — 24-month window)",
            "step_2": "Submit targets for validation (SBTi target submission)",
            "step_3": "SBTi reviews against sector pathways and ambition criteria",
            "step_4": "Targets approved → 'SBTi Validated' status",
            "step_5": "Annual progress disclosure; re-validation every 5 years",
        },
        "near_term_requirements": {
            "scope12_reduction_pct": 42,
            "scope12_target_year": 2030,
            "scope3_reduction_pct": 25,
            "scope3_trigger_pct": 40,
            "scope3_target_year": 2030,
        },
        "long_term_requirements": {
            "scope12_reduction_pct": 90,
            "scope3_reduction_pct": 90,
            "target_year": 2050,
            "max_residual_pct": 10,
        },
        "sector_specific_pathways": {
            s: {"pathway_source": d["pathway_source"], "2030_target_pct": d["targets"][2030]}
            for s, d in SECTOR_PATHWAYS.items()
        },
    }


@router.get("/ref/race-to-zero", summary="Race to Zero 5 Cs + membership categories")
async def ref_race_to_zero() -> dict[str, Any]:
    """
    Return Race to Zero 2023 criteria (5 Cs: Commit, Countable, Consistent,
    Credible, Communicate) and GFANZ sub-alliance membership categories.
    """
    return {
        "source": "Race to Zero Campaign 2023 Criteria, UNFCCC High-Level Champions",
        "overview": (
            "Race to Zero is the global UN-backed campaign rallying non-state actors "
            "to achieve net-zero emissions by 2050 at the latest, requiring credible "
            "near-term actions and independently validated targets."
        ),
        "five_cs": RACE_TO_ZERO_CRITERIA,
        "membership_categories": RTZ_MEMBERSHIP_CATEGORIES,
        "key_requirements_summary": [
            "Net-zero pledge by 2050 (Scope 1+2+3)",
            "2030 interim target ≥50% vs base year",
            "Scope 3 covered",
            "Annual GHG disclosure (CDP/TCFD/ISSB aligned)",
            "SBTi or equivalent validation",
            "No new unabated coal investments",
        ],
        "total_members_2023": "~9,000 entities globally",
        "financial_assets_committed_usd_tn": 130,
    }


@router.get("/ref/sector-pathways", summary="20 sector GHG reduction trajectories")
async def ref_sector_pathways() -> dict[str, Any]:
    """
    Return 20 sector transition pathways with 2030/2040/2050 GHG reduction targets,
    key decarbonisation levers, pathway sources, and temperature alignment thresholds.
    """
    return {
        "source": "IEA NZE2050, IPCC AR6, Mission Possible Partnership, SBTi sector guidance, sector-specific initiatives",
        "note": "Targets expressed as % reduction vs 2019 base year (unless stated). High-climate-impact sectors identified per GFANZ.",
        "pathways": SECTOR_PATHWAYS,
        "high_climate_impact_sectors": GFANZ_EXPECTATIONS["high_climate_impact_sectors"],
        "sector_count": len(SECTOR_PATHWAYS),
        "key_milestones": {
            "2025": "Near-term action plans due; interim progress disclosure",
            "2030": "50% reduction milestone (Race to Zero); SBTi near-term targets",
            "2040": "Deep decarbonisation phase; hard-to-abate sectors",
            "2050": "Net-zero economy; residuals neutralised",
        },
    }


@router.get("/ref/gfanz-expectations", summary="GFANZ real-economy transition plan guidance")
async def ref_gfanz_expectations() -> dict[str, Any]:
    """
    Return GFANZ Expectations for Real-economy Transition Plans (November 2023):
    5 components (ambition, action, accountability, fairness, credibility),
    high-climate-impact sectors, and financial institution portfolio alignment expectations.
    """
    return {
        "source": "Glasgow Financial Alliance for Net Zero (GFANZ), November 2023",
        "version": "November 2023",
        "expectations": GFANZ_EXPECTATIONS,
        "transition_instrument_criteria": TRANSITION_INSTRUMENT_CRITERIA,
        "credibility_framework_weights": {
            "tpt_composite": "40% of overall credibility score",
            "sbti_validation": "30%",
            "race_to_zero": "15%",
            "portfolio_temperature": "10%",
            "tnfd_nature": "5%",
        },
        "greenwash_red_flags": [
            "Net-zero pledge without credible transition plan (score <30%)",
            "SBTi committed but targets not validated within 24 months",
            "Net-zero claim with Scope 3 coverage <40%",
            "Offset reliance >50% of total GHG reduction target",
            "No 2030 interim targets despite 2050 net-zero pledge",
        ],
    }
