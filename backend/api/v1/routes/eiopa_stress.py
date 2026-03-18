"""
API Routes: EIOPA ORSA Climate Stress Test Engine (E7)
======================================================
POST /api/v1/eiopa-stress/assess              — Full EIOPA climate stress test (all 4 scenarios)
POST /api/v1/eiopa-stress/assess/batch        — Batch: multiple insurers in one call
POST /api/v1/eiopa-stress/assess/scenario     — Single-scenario stress test
GET  /api/v1/eiopa-stress/ref/scenarios       — EIOPA climate scenario registry
GET  /api/v1/eiopa-stress/ref/orsa-checklist  — Art 45a ORSA climate checklist (12 items)
GET  /api/v1/eiopa-stress/ref/insurer-types   — Insurer type profiles
GET  /api/v1/eiopa-stress/ref/frameworks      — Solvency II / EIOPA / NGFS cross-reference
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.eiopa_stress_engine import (
    EiopaStressEngine,
    InsurerInput,
    EIOPA_SCENARIOS,
    ORSA_CLIMATE_CHECKLIST,
    INSURER_TYPE_PROFILES,
)

router = APIRouter(prefix="/api/v1/eiopa-stress", tags=["EIOPA Stress Test"])

_ENGINE = EiopaStressEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class InsurerInputModel(BaseModel):
    entity_id: str
    entity_name: str
    insurer_type: str = Field(
        "composite",
        description="life | non_life | composite | reinsurer | captive",
    )
    domicile: str = Field("DE", description="ISO-2 country code")

    # Balance sheet (EUR)
    total_assets_eur: float = Field(0.0, ge=0)
    total_tp_eur: float = Field(0.0, ge=0, description="Technical Provisions (best estimate + RM)")
    eligible_own_funds_eur: float = Field(0.0, ge=0)
    scr_eur: float = Field(0.0, ge=0, description="Current Solvency Capital Requirement")
    mcr_eur: float = Field(0.0, ge=0, description="Current Minimum Capital Requirement")

    # Investment portfolio breakdown (% of invested assets)
    equity_listed_pct: float = Field(15.0, ge=0, le=100)
    equity_fossil_fuel_pct: float = Field(3.0, ge=0, le=100, description="Subset of equity_listed")
    re_commercial_pct: float = Field(8.0, ge=0, le=100)
    re_residential_pct: float = Field(4.0, ge=0, le=100)
    sovereign_bonds_pct: float = Field(35.0, ge=0, le=100)
    ig_corp_bonds_pct: float = Field(25.0, ge=0, le=100)
    hy_corp_bonds_pct: float = Field(5.0, ge=0, le=100)
    infrastructure_pct: float = Field(3.0, ge=0, le=100)
    alternatives_pct: float = Field(2.0, ge=0, le=100)

    # Underwriting / liability data
    annual_natcat_exposure_eur: float = Field(0.0, ge=0)
    technical_provision_adequacy_pct: float = Field(100.0, ge=0)
    annual_premium_eur: float = Field(0.0, ge=0)

    # Life-specific
    in_force_sum_assured_eur: float = Field(0.0, ge=0)
    lapse_sensitive_reserves_pct: float = Field(20.0, ge=0, le=100)

    # ORSA completeness flags
    has_board_climate_oversight: bool = False
    has_climate_scenario_analysis: bool = False
    has_long_term_scenarios: bool = False
    has_natcat_climate_assessment: bool = False
    has_life_climate_adjustment: bool = False
    has_management_actions_plan: bool = False
    has_data_quality_disclosure: bool = False
    has_nca_orsa_submission: bool = False
    has_double_materiality: bool = False


class AssessRequest(BaseModel):
    insurer: InsurerInputModel
    scenarios: Optional[List[str]] = Field(
        None,
        description=(
            "Scenario IDs to run. Defaults to all four: "
            "sudden_transition | orderly_transition | hot_house_world | below_2c"
        ),
    )
    assessment_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class SingleScenarioRequest(BaseModel):
    insurer: InsurerInputModel
    scenario_id: str = Field(
        ...,
        description="sudden_transition | orderly_transition | hot_house_world | below_2c",
    )
    assessment_date: Optional[str] = None


class BatchAssessRequest(BaseModel):
    assessments: List[AssessRequest]


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _asset_shock_to_dict(r) -> Dict[str, Any]:
    return {
        "equity_loss_eur": r.equity_loss_eur,
        "re_loss_eur": r.re_loss_eur,
        "sovereign_bond_loss_eur": r.sovereign_bond_loss_eur,
        "ig_corp_bond_loss_eur": r.ig_corp_bond_loss_eur,
        "hy_corp_bond_loss_eur": r.hy_corp_bond_loss_eur,
        "infrastructure_loss_eur": r.infrastructure_loss_eur,
        "alternatives_loss_eur": r.alternatives_loss_eur,
        "total_asset_loss_eur": r.total_asset_loss_eur,
        "total_asset_loss_pct": r.total_asset_loss_pct,
    }


def _uw_shock_to_dict(r) -> Dict[str, Any]:
    return {
        "natcat_additional_loss_eur": r.natcat_additional_loss_eur,
        "reserve_deterioration_eur": r.reserve_deterioration_eur,
        "lapse_loss_eur": r.lapse_loss_eur,
        "mortality_additional_loss_eur": r.mortality_additional_loss_eur,
        "morbidity_additional_loss_eur": r.morbidity_additional_loss_eur,
        "total_uw_shock_eur": r.total_uw_shock_eur,
    }


def _capital_to_dict(r) -> Dict[str, Any]:
    return {
        "pre_stress": {
            "scr_eur": r.pre_stress_scr_eur,
            "own_funds_eur": r.pre_stress_own_funds_eur,
            "solvency_ratio_pct": r.pre_stress_solvency_ratio_pct,
        },
        "post_stress": {
            "scr_eur": r.post_stress_scr_eur,
            "own_funds_eur": r.post_stress_own_funds_eur,
            "solvency_ratio_pct": r.post_stress_solvency_ratio_pct,
        },
        "scr_breach": r.scr_breach,
        "mcr_breach": r.mcr_breach,
        "capital_shortfall_eur": r.capital_shortfall_eur,
        "solvency_ratio_change_pp": r.scr_coverage_change_pp,
    }


def _scenario_to_dict(r) -> Dict[str, Any]:
    return {
        "scenario_id": r.scenario_id,
        "scenario_name": r.scenario_name,
        "scenario_description": r.scenario_description,
        "ngfs_equivalent": r.ngfs_equivalent,
        "temp_outcome_c": r.temp_outcome_c,
        "horizon_years": r.horizon_years,
        "asset_shock": _asset_shock_to_dict(r.asset_shock),
        "underwriting_shock": _uw_shock_to_dict(r.underwriting_shock),
        "capital_impact": _capital_to_dict(r.capital_impact),
        "total_stress_loss_eur": r.total_stress_loss_eur,
        "total_stress_loss_pct_of_own_funds": r.total_stress_loss_pct_of_own_funds,
        "stress_severity": r.stress_severity,
        "key_drivers": r.key_drivers,
        "management_actions_capacity_eur": r.management_actions_capacity_eur,
        "recovery_feasible": r.recovery_feasible,
        "narrative": r.narrative,
    }


def _orsa_checklist_to_dict(r) -> Dict[str, Any]:
    return {
        "items_met": r.items_met,
        "items_total": r.items_total,
        "orsa_completeness_pct": r.orsa_completeness_pct,
        "checklist": r.checklist,
        "gaps": r.gaps,
        "priority_actions": r.priority_actions,
    }


def _result_to_dict(r) -> Dict[str, Any]:
    return {
        "run_id": r.run_id,
        "entity_id": r.entity_id,
        "entity_name": r.entity_name,
        "insurer_type": r.insurer_type,
        "assessment_date": r.assessment_date,
        "headline": {
            "worst_scenario": r.worst_scenario_id,
            "worst_solvency_ratio_pct": r.worst_solvency_ratio_pct,
            "worst_capital_shortfall_eur": r.worst_capital_shortfall_eur,
            "any_scr_breach": r.any_scr_breach,
            "any_mcr_breach": r.any_mcr_breach,
            "overall_resilience": r.overall_resilience,
        },
        "scenario_results": [_scenario_to_dict(s) for s in r.scenario_results],
        "orsa_checklist": _orsa_checklist_to_dict(r.orsa_checklist),
        "gaps": r.gaps,
        "priority_actions": r.priority_actions,
        "metadata": r.metadata,
    }


def _to_domain(m: InsurerInputModel) -> InsurerInput:
    return InsurerInput(**m.model_dump())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full EIOPA climate stress test — all scenarios",
    description=(
        "Runs all four EIOPA/NGFS climate scenarios (sudden transition, orderly transition, "
        "hot house world, below 2°C) against the insurer's balance sheet. Returns per-scenario "
        "SCR/MCR impact, solvency ratio change, asset and underwriting shocks, and the "
        "12-item Art 45a ORSA completeness checklist. "
        "Framework: Solvency II Art 45a, EIOPA 2022/2023 Stress Test, NGFS Phase IV."
    ),
)
def assess(req: AssessRequest):
    result = _ENGINE.assess(
        insurer=_to_domain(req.insurer),
        scenarios=req.scenarios,
        assessment_date=req.assessment_date,
    )
    return _result_to_dict(result)


@router.post(
    "/assess/scenario",
    summary="Single-scenario EIOPA climate stress test",
    description="Run one specific EIOPA scenario against the insurer.",
)
def assess_single_scenario(req: SingleScenarioRequest):
    result = _ENGINE.assess(
        insurer=_to_domain(req.insurer),
        scenarios=[req.scenario_id],
        assessment_date=req.assessment_date,
    )
    return _result_to_dict(result)


@router.post(
    "/assess/batch",
    summary="Batch EIOPA climate stress test — multiple insurers",
    description="Run the full EIOPA climate stress test for multiple (re)insurers in one call.",
)
def assess_batch(req: BatchAssessRequest):
    results = []
    for a in req.assessments:
        r = _ENGINE.assess(
            insurer=_to_domain(a.insurer),
            scenarios=a.scenarios,
            assessment_date=a.assessment_date,
        )
        results.append(_result_to_dict(r))
    return {
        "batch_count": len(results),
        "any_scr_breach": any(r["headline"]["any_scr_breach"] for r in results),
        "any_mcr_breach": any(r["headline"]["any_mcr_breach"] for r in results),
        "assessments": results,
    }


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/scenarios",
    summary="EIOPA climate scenario registry",
    description="Four EIOPA/NGFS climate scenarios with shock parameters.",
)
def ref_scenarios():
    return {
        "count": len(EIOPA_SCENARIOS),
        "scenarios": [
            {
                "scenario_id": sc_id,
                "name": sc["name"],
                "description": sc["description"],
                "ngfs_equivalent": sc["ngfs_equivalent"],
                "temp_outcome_c": sc["temp_outcome_c"],
                "horizon_years": sc["horizon_years"],
                "shocks": {
                    "equity_listed_shock_pct": sc["equity_listed_shock_pct"],
                    "equity_fossil_fuel_shock_pct": sc["equity_fossil_fuel_shock_pct"],
                    "re_commercial_shock_pct": sc["re_commercial_shock_pct"],
                    "re_residential_shock_pct": sc["re_residential_shock_pct"],
                    "sovereign_bond_spread_bps": sc["sovereign_bond_spread_bps"],
                    "ig_corp_bond_spread_bps": sc["ig_corp_bond_spread_bps"],
                    "hy_corp_bond_spread_bps": sc["hy_corp_bond_spread_bps"],
                    "natcat_amplifier": sc["natcat_amplifier"],
                    "reserve_adequacy_shock_pct": sc["reserve_adequacy_shock_pct"],
                    "lapse_shock_pct": sc["lapse_shock_pct"],
                },
            }
            for sc_id, sc in EIOPA_SCENARIOS.items()
        ],
        "reference": (
            "EIOPA 2022 Insurance Stress Test | "
            "EIOPA 2023 Insurance Stress Test | "
            "NGFS Phase IV Climate Scenarios (2023)"
        ),
    }


@router.get(
    "/ref/orsa-checklist",
    summary="Art 45a ORSA climate checklist — 12 items",
    description=(
        "EIOPA Art 45a Solvency II ORSA climate checklist. "
        "Covers governance, scenario analysis, quantification, NatCat, life adjustments, "
        "management actions, data quality, NCA submission, and double materiality."
    ),
)
def ref_orsa_checklist():
    return {
        "count": len(ORSA_CLIMATE_CHECKLIST),
        "checklist": ORSA_CLIMATE_CHECKLIST,
        "reference": (
            "Solvency II Art 45a (OMNIBUS II / Climate Risk Amendment) | "
            "EIOPA Opinion EIOPA-BoS-21/127 | "
            "EIOPA Guidelines on ORSA (GL 01/2018)"
        ),
    }


@router.get(
    "/ref/insurer-types",
    summary="Insurer type profiles (life, non-life, composite, reinsurer, captive)",
)
def ref_insurer_types():
    return {
        "count": len(INSURER_TYPE_PROFILES),
        "insurer_types": [
            {"type_id": tid, **profile}
            for tid, profile in INSURER_TYPE_PROFILES.items()
        ],
    }


@router.get(
    "/ref/frameworks",
    summary="Solvency II / EIOPA / NGFS cross-reference for climate stress testing",
)
def ref_frameworks():
    return {
        "frameworks": {
            "Solvency_II_Art45a": {
                "title": "Solvency II Article 45a — Climate change in ORSA",
                "requirement": (
                    "Insurers must integrate short-term and long-term climate risk "
                    "scenarios in their ORSA. At least one orderly + one disorderly "
                    "transition scenario required."
                ),
                "effective": "2024 (phased application)",
                "reference": "Directive 2009/138/EC Art 45a (as amended by Omnibus II)",
            },
            "EIOPA_Opinion_2021": {
                "title": "EIOPA Opinion on Supervision of Use of Climate Scenarios",
                "reference": "EIOPA-BoS-21/127",
                "key_requirements": [
                    "Board-level oversight of climate risk",
                    "Material risk identification across all SII risk categories",
                    "Quantitative climate stress test in ORSA",
                    "Long-term scenario horizon (10–30 years)",
                ],
            },
            "EIOPA_Stress_Test_2022": {
                "title": "EIOPA 2022 Insurance Stress Test",
                "scenarios": ["Sudden transition", "NatCat amplification"],
                "modules": ["M1 Market", "M2 NatCat", "M3 Life", "M4 Reserve"],
            },
            "EIOPA_Stress_Test_2023": {
                "title": "EIOPA 2023 Insurance Stress Test",
                "enhancement": "Expanded physical risk + transition cross-effects",
                "reporting": "Quantitative assessment template submitted to NCA",
            },
            "NGFS_Phase_IV": {
                "title": "NGFS Phase IV Scenarios (2023)",
                "eiopa_mapping": {
                    "Net Zero 2050": "orderly_transition",
                    "Divergent Net Zero": "sudden_transition",
                    "Below 2°C": "below_2c",
                    "Current Policies": "hot_house_world",
                },
                "reference": "NGFS Climate Scenarios for Central Banks and Supervisors — Phase IV (2023)",
            },
            "TCFD_Insurers": {
                "title": "TCFD for Insurers — Scenario Analysis",
                "alignment": "EIOPA ST scenarios fully TCFD-aligned",
                "reference": "TCFD Guidance on Scenario Analysis for Non-Financial Companies (2020)",
            },
        },
        "reference": (
            "EIOPA-BoS-21/127 | Solvency II Art 45a | "
            "EIOPA ST 2022/2023 | NGFS Phase IV | TCFD (2020)"
        ),
    }
