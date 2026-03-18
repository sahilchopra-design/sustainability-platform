"""
API Routes: IORP II Pension Fund Climate Risk Engine (E8)
=========================================================
POST /api/v1/iorp-pension/assess              — Full IORP II stress test (all scenarios)
POST /api/v1/iorp-pension/assess/scenario     — Single scenario stress
POST /api/v1/iorp-pension/assess/batch        — Batch: multiple pension funds
GET  /api/v1/iorp-pension/ref/scenarios       — NGFS/EIOPA scenario registry
GET  /api/v1/iorp-pension/ref/ora-checklist   — IORP II Art 28 ORA checklist (12 items)
GET  /api/v1/iorp-pension/ref/fund-types      — IORP fund type profiles
GET  /api/v1/iorp-pension/ref/sfdr-classes    — SFDR Art 6/8/9 reference for pension FMPs
GET  /api/v1/iorp-pension/ref/frameworks      — Regulatory framework reference
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import json
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.base import get_db

logger = logging.getLogger(__name__)

from services.iorp_pension_engine import (
    IORPPensionEngine,
    PensionFundInput,
    IORP_SCENARIOS,
    ORA_CHECKLIST_ITEMS,
    IORP_TYPE_PROFILES,
    SFDR_FMP_CATEGORIES,
    IORPStressResult,
    ScenarioPensionResult,
)

router = APIRouter(
    prefix="/api/v1/iorp-pension",
    tags=["IORP II Pension Climate Risk"],
)

_ENGINE = IORPPensionEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PensionFundInputModel(BaseModel):
    fund_id: str = Field(..., description="Unique fund identifier")
    fund_name: str = Field(..., description="Pension fund name")
    iorp_type: str = Field(
        "defined_benefit",
        description="defined_benefit | defined_contribution | hybrid | collective_dc",
    )
    member_count: int = Field(1000, description="Total active/deferred/pensioner members")
    country_iso3: str = Field("NLD", description="Home country ISO3")
    reporting_currency: str = "EUR"

    # Balance sheet
    total_assets_eur: float = Field(1_000_000_000.0, description="Total assets under management (EUR)")
    liabilities_eur: float = Field(900_000_000.0, description="Technical provisions / liabilities (EUR)")
    liability_duration_y: float = Field(18.0, description="Modified duration of liabilities (years)")

    # Asset allocation
    equity_pct: float = Field(40.0, ge=0, le=100)
    sovereign_bonds_pct: float = Field(25.0, ge=0, le=100)
    corp_bonds_ig_pct: float = Field(20.0, ge=0, le=100)
    corp_bonds_hy_pct: float = Field(5.0, ge=0, le=100)
    real_estate_pct: float = Field(7.0, ge=0, le=100)
    infrastructure_pct: float = Field(3.0, ge=0, le=100)

    # SFDR
    sfdr_classification: str = Field("art_8", description="art_6 | art_8 | art_9")

    # Scenarios
    scenario_ids: List[str] = Field(
        default_factory=lambda: list(IORP_SCENARIOS.keys()),
        description="Subset of scenario IDs to run",
    )

    # ORA flags
    has_governance_framework: bool = False
    has_risk_integration: bool = False
    has_physical_and_transition: bool = False
    has_esg_investment_policy: bool = False
    has_member_communication: bool = False
    has_scenario_analysis: bool = False
    has_funding_ratio_stress: bool = False
    has_recovery_plan: bool = False
    has_sfdr_classification: bool = True
    has_pai_reporting: bool = False
    has_nature_disclosure: bool = False
    has_transition_plan: bool = False


class AssessRequest(BaseModel):
    fund: PensionFundInputModel
    assessment_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class SingleScenarioRequest(BaseModel):
    fund: PensionFundInputModel
    scenario_id: str = Field(..., description="One of: net_zero_2050 | below_2c | hot_house_world | current_policies")
    assessment_date: Optional[str] = None


class BatchAssessRequest(BaseModel):
    funds: List[AssessRequest]


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _asset_stress_to_dict(a) -> Dict[str, Any]:
    return {
        "equity_loss_eur": a.equity_loss_eur,
        "sovereign_bond_loss_eur": a.sovereign_bond_loss_eur,
        "corp_ig_loss_eur": a.corp_ig_loss_eur,
        "corp_hy_loss_eur": a.corp_hy_loss_eur,
        "real_estate_loss_eur": a.real_estate_loss_eur,
        "infrastructure_loss_eur": a.infrastructure_loss_eur,
        "total_asset_loss_eur": a.total_asset_loss_eur,
        "stressed_assets_eur": a.stressed_assets_eur,
    }


def _liab_stress_to_dict(l) -> Dict[str, Any]:
    return {
        "discount_rate_shift_bps": l.discount_rate_shift_bps,
        "liability_duration_impact_eur": l.liability_duration_impact_eur,
        "longevity_shock_eur": l.longevity_shock_eur,
        "inflation_liability_uplift_eur": l.inflation_liability_uplift_eur,
        "total_liability_change_eur": l.total_liability_change_eur,
        "stressed_liabilities_eur": l.stressed_liabilities_eur,
    }


def _fr_to_dict(f) -> Dict[str, Any]:
    return {
        "pre_stress_ratio_pct": f.pre_stress_ratio,
        "post_stress_ratio_pct": f.post_stress_ratio,
        "ratio_change_pct": f.ratio_change_pct,
        "triggers_recovery_plan": f.triggers_recovery_plan,
        "triggers_supervisory_review": f.triggers_supervisory_review,
        "sponsor_covenant_buffer_eur": f.sponsor_covenant_buffer_eur,
    }


def _scenario_result_to_dict(sr: ScenarioPensionResult) -> Dict[str, Any]:
    return {
        "scenario_id": sr.scenario_id,
        "scenario_label": sr.scenario_label,
        "asset_stress": _asset_stress_to_dict(sr.asset_stress),
        "liability_stress": _liab_stress_to_dict(sr.liability_stress),
        "funding_ratio": _fr_to_dict(sr.funding_ratio),
        "net_stress_impact_eur": sr.net_stress_impact_eur,
        "member_benefit_erosion_pct": sr.member_benefit_erosion_pct,
    }


def _ora_to_dict(o) -> Dict[str, Any]:
    return {
        "item_id": o.item_id,
        "title": o.title,
        "article": o.article,
        "blocking": o.blocking,
        "met": o.met,
        "status": o.status,
    }


def _result_to_dict(r: IORPStressResult) -> Dict[str, Any]:
    return {
        "run_id": r.run_id,
        "fund_id": r.fund_id,
        "fund_name": r.fund_name,
        "iorp_type": r.iorp_type,
        "member_count": r.member_count,
        "sfdr_classification": r.sfdr_classification,
        "headline": {
            "pre_stress_funding_ratio_pct": r.pre_stress_funding_ratio,
            "worst_case_scenario_id": r.worst_case_scenario_id,
            "worst_case_funding_ratio_drop_pct": r.worst_case_funding_ratio_drop_pct,
            "ora_compliance_status": r.ora_compliance_status,
            "ora_items_met": r.ora_items_met,
            "ora_items_gap": r.ora_items_gap,
            "blocking_gaps_count": len(r.ora_blocking_gaps),
        },
        "scenario_results": [_scenario_result_to_dict(sr) for sr in r.scenario_results],
        "ora_checklist": [_ora_to_dict(o) for o in r.ora_checklist],
        "ora_blocking_gaps": r.ora_blocking_gaps,
        "sfdr_summary": r.sfdr_summary,
        "recommendations": r.recommendations,
        "metadata": r.metadata,
    }


def _to_domain(m: PensionFundInputModel) -> PensionFundInput:
    return PensionFundInput(**m.model_dump())


# ---------------------------------------------------------------------------
# DB Persistence helper
# ---------------------------------------------------------------------------

def _persist_run(db: Session, result: "IORPStressResult", fund: "PensionFundInput") -> None:
    """Persist IORP stress run summary + scenario results + ORA results to DB (fire-and-forget)."""
    import datetime

    run_id = result.run_id
    assessment_date = result.metadata.get("assessment_date") or datetime.date.today().isoformat()

    # 1. Insert run summary
    db.execute(text("""
        INSERT INTO iorp_stress_runs (
            id, fund_id, fund_name, iorp_type, member_count, country_iso3,
            reporting_currency, total_assets_eur, liabilities_eur, liability_duration_y,
            equity_pct, sovereign_bonds_pct, corp_bonds_ig_pct, corp_bonds_hy_pct,
            real_estate_pct, infrastructure_pct,
            pre_stress_funding_ratio_pct, worst_case_scenario_id,
            worst_case_funding_ratio_drop_pct, sfdr_classification, ora_compliance_status,
            ora_items_met, ora_items_gap, ora_blocking_gaps, scenarios_run,
            recommendations, assessment_date
        ) VALUES (
            :id, :fund_id, :fund_name, :iorp_type, :member_count, :country_iso3,
            :reporting_currency, :total_assets_eur, :liabilities_eur, :liability_duration_y,
            :equity_pct, :sovereign_bonds_pct, :corp_bonds_ig_pct, :corp_bonds_hy_pct,
            :real_estate_pct, :infrastructure_pct,
            :pre_stress_funding_ratio_pct, :worst_case_scenario_id,
            :worst_case_funding_ratio_drop_pct, :sfdr_classification, :ora_compliance_status,
            :ora_items_met, :ora_items_gap, :ora_blocking_gaps::jsonb, :scenarios_run,
            :recommendations::jsonb, :assessment_date
        ) ON CONFLICT (id) DO NOTHING
    """), {
        "id": run_id,
        "fund_id": result.fund_id,
        "fund_name": result.fund_name,
        "iorp_type": result.iorp_type,
        "member_count": result.member_count,
        "country_iso3": fund.country_iso3,
        "reporting_currency": fund.reporting_currency,
        "total_assets_eur": fund.total_assets_eur,
        "liabilities_eur": fund.liabilities_eur,
        "liability_duration_y": fund.liability_duration_y,
        "equity_pct": fund.equity_pct,
        "sovereign_bonds_pct": fund.sovereign_bonds_pct,
        "corp_bonds_ig_pct": fund.corp_bonds_ig_pct,
        "corp_bonds_hy_pct": fund.corp_bonds_hy_pct,
        "real_estate_pct": fund.real_estate_pct,
        "infrastructure_pct": fund.infrastructure_pct,
        "pre_stress_funding_ratio_pct": result.pre_stress_funding_ratio,
        "worst_case_scenario_id": result.worst_case_scenario_id,
        "worst_case_funding_ratio_drop_pct": result.worst_case_funding_ratio_drop_pct,
        "sfdr_classification": result.sfdr_classification,
        "ora_compliance_status": result.ora_compliance_status,
        "ora_items_met": result.ora_items_met,
        "ora_items_gap": result.ora_items_gap,
        "ora_blocking_gaps": json.dumps(result.ora_blocking_gaps),
        "scenarios_run": len(result.scenario_results),
        "recommendations": json.dumps(result.recommendations),
        "assessment_date": assessment_date,
    })

    # 2. Insert per-scenario results
    for sr in result.scenario_results:
        db.execute(text("""
            INSERT INTO iorp_scenario_results (
                run_id, scenario_id, scenario_label,
                equity_loss_eur, sovereign_bond_loss_eur, corp_ig_loss_eur, corp_hy_loss_eur,
                real_estate_loss_eur, infrastructure_loss_eur, total_asset_loss_eur, stressed_assets_eur,
                discount_rate_shift_bps, liability_duration_impact_eur, longevity_shock_eur,
                inflation_liability_uplift_eur, total_liability_change_eur, stressed_liabilities_eur,
                pre_stress_ratio_pct, post_stress_ratio_pct, ratio_change_pct,
                triggers_recovery_plan, triggers_supervisory_review, sponsor_covenant_buffer_eur,
                net_stress_impact_eur, member_benefit_erosion_pct
            ) VALUES (
                :run_id, :scenario_id, :scenario_label,
                :equity_loss_eur, :sovereign_bond_loss_eur, :corp_ig_loss_eur, :corp_hy_loss_eur,
                :real_estate_loss_eur, :infrastructure_loss_eur, :total_asset_loss_eur, :stressed_assets_eur,
                :discount_rate_shift_bps, :liability_duration_impact_eur, :longevity_shock_eur,
                :inflation_liability_uplift_eur, :total_liability_change_eur, :stressed_liabilities_eur,
                :pre_stress_ratio_pct, :post_stress_ratio_pct, :ratio_change_pct,
                :triggers_recovery_plan, :triggers_supervisory_review, :sponsor_covenant_buffer_eur,
                :net_stress_impact_eur, :member_benefit_erosion_pct
            )
        """), {
            "run_id": run_id,
            "scenario_id": sr.scenario_id,
            "scenario_label": sr.scenario_label,
            "equity_loss_eur": sr.asset_stress.equity_loss_eur,
            "sovereign_bond_loss_eur": sr.asset_stress.sovereign_bond_loss_eur,
            "corp_ig_loss_eur": sr.asset_stress.corp_ig_loss_eur,
            "corp_hy_loss_eur": sr.asset_stress.corp_hy_loss_eur,
            "real_estate_loss_eur": sr.asset_stress.real_estate_loss_eur,
            "infrastructure_loss_eur": sr.asset_stress.infrastructure_loss_eur,
            "total_asset_loss_eur": sr.asset_stress.total_asset_loss_eur,
            "stressed_assets_eur": sr.asset_stress.stressed_assets_eur,
            "discount_rate_shift_bps": sr.liability_stress.discount_rate_shift_bps,
            "liability_duration_impact_eur": sr.liability_stress.liability_duration_impact_eur,
            "longevity_shock_eur": sr.liability_stress.longevity_shock_eur,
            "inflation_liability_uplift_eur": sr.liability_stress.inflation_liability_uplift_eur,
            "total_liability_change_eur": sr.liability_stress.total_liability_change_eur,
            "stressed_liabilities_eur": sr.liability_stress.stressed_liabilities_eur,
            "pre_stress_ratio_pct": sr.funding_ratio.pre_stress_ratio,
            "post_stress_ratio_pct": sr.funding_ratio.post_stress_ratio,
            "ratio_change_pct": sr.funding_ratio.ratio_change_pct,
            "triggers_recovery_plan": sr.funding_ratio.triggers_recovery_plan,
            "triggers_supervisory_review": sr.funding_ratio.triggers_supervisory_review,
            "sponsor_covenant_buffer_eur": sr.funding_ratio.sponsor_covenant_buffer_eur,
            "net_stress_impact_eur": sr.net_stress_impact_eur,
            "member_benefit_erosion_pct": sr.member_benefit_erosion_pct,
        })

    # 3. Insert ORA checklist results
    for ora in result.ora_checklist:
        db.execute(text("""
            INSERT INTO iorp_ora_results (run_id, item_id, title, article, blocking, met, status)
            VALUES (:run_id, :item_id, :title, :article, :blocking, :met, :status)
        """), {
            "run_id": run_id,
            "item_id": ora.item_id,
            "title": ora.title,
            "article": ora.article,
            "blocking": ora.blocking,
            "met": ora.met,
            "status": ora.status,
        })

    db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full IORP II climate stress test (all configured scenarios)",
    description=(
        "Runs EIOPA IORP II climate stress test across up to 4 NGFS scenarios. "
        "Computes asset-side shocks (equity, bonds, RE, infrastructure), liability-side "
        "shocks (duration re-pricing, longevity, inflation), funding ratio stress, "
        "Art 28 ORA checklist, SFDR FMP classification, and remediation recommendations."
    ),
)
def assess(req: AssessRequest, db: Session = Depends(get_db)):
    fund = _to_domain(req.fund)
    result = _ENGINE.assess(fund=fund, assessment_date=req.assessment_date)
    d = _result_to_dict(result)

    # Persist run summary to DB (best-effort — never blocks response)
    try:
        _persist_run(db, result, fund)
    except Exception as exc:
        logger.debug("IORP run persistence skipped: %s", exc)

    return d


@router.post(
    "/assess/scenario",
    summary="Single-scenario IORP II stress",
    description="Run the IORP II climate stress test for a single NGFS scenario.",
)
def assess_scenario(req: SingleScenarioRequest):
    fund = _to_domain(req.fund)
    fund.scenario_ids = [req.scenario_id]
    result = _ENGINE.assess(fund=fund, assessment_date=req.assessment_date)
    d = _result_to_dict(result)
    # Return scenario result directly for single-scenario convenience
    d["scenario_result"] = d["scenario_results"][0] if d["scenario_results"] else {}
    return d


@router.post(
    "/assess/batch",
    summary="Batch IORP II stress test — multiple pension funds",
    description="Run climate stress tests for a list of pension funds in one call.",
)
def assess_batch(req: BatchAssessRequest):
    results = []
    for a in req.funds:
        r = _ENGINE.assess(
            fund=_to_domain(a.fund),
            assessment_date=a.assessment_date,
        )
        results.append(_result_to_dict(r))
    return {
        "batch_count": len(results),
        "funds_with_recovery_trigger": sum(
            1 for r in results
            if any(
                sr["funding_ratio"]["triggers_recovery_plan"]
                for sr in r["scenario_results"]
            )
        ),
        "funds_non_compliant_ora": sum(
            1 for r in results
            if r["headline"]["ora_compliance_status"] == "non_compliant"
        ),
        "assessments": results,
    }


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/scenarios",
    summary="NGFS / EIOPA IORP II climate scenario registry",
)
def ref_scenarios():
    return {
        "count": len(IORP_SCENARIOS),
        "framework": "NGFS Phase 5 + EIOPA IORP II Climate Stress Test 2022",
        "scenarios": [
            {"scenario_id": k, **v}
            for k, v in IORP_SCENARIOS.items()
        ],
    }


@router.get(
    "/ref/ora-checklist",
    summary="IORP II Art 28 Own Risk Assessment (ORA) checklist — 12 items",
)
def ref_ora_checklist():
    blocking_count = sum(1 for i in ORA_CHECKLIST_ITEMS if i["blocking"])
    return {
        "total_items": len(ORA_CHECKLIST_ITEMS),
        "blocking_items": blocking_count,
        "items": ORA_CHECKLIST_ITEMS,
        "reference": "IORP II Directive (EU) 2016/2341 — Art 28 Own Risk Assessment",
    }


@router.get(
    "/ref/fund-types",
    summary="IORP fund type profiles (DB/DC/Hybrid/CDC)",
)
def ref_fund_types():
    return {
        "count": len(IORP_TYPE_PROFILES),
        "fund_types": [
            {"fund_type_id": k, **v}
            for k, v in IORP_TYPE_PROFILES.items()
        ],
    }


@router.get(
    "/ref/sfdr-classes",
    summary="SFDR Art 6/8/9 reference for pension funds as FMPs",
)
def ref_sfdr_classes():
    return {
        "regulation": "SFDR (EU) 2019/2088",
        "applicable_to": "Pension funds as Financial Market Participants (FMPs)",
        "pai_reporting_threshold": "FMPs with >500 employees — mandatory from 2023-06-30",
        "classifications": [
            {"classification": k, "description": v}
            for k, v in SFDR_FMP_CATEGORIES.items()
        ],
        "reference": "SFDR Art 3 (transparency at entity level), Art 4 (PAI), Art 8-9 (product classification)",
    }


@router.get(
    "/ref/frameworks",
    summary="IORP II regulatory framework reference",
)
def ref_frameworks():
    return {
        "primary_directive": {
            "id": "IORP II",
            "name": "IORP II Directive (EU) 2016/2341",
            "scope": "Institutions for Occupational Retirement Provision with >15 members",
            "esg_articles": ["Art 19(1)(b) — ESG in investment policy", "Art 28 — Own Risk Assessment", "Art 41(1) — Member communication"],
            "key_requirements": [
                "ESG factors in investment decision-making (Art 19)",
                "Climate risk in Own Risk Assessment (Art 28)",
                "Transparent member communications on ESG risks (Art 41)",
                "Prudent person rule applied to long-term sustainability",
            ],
        },
        "stress_test": {
            "id": "EIOPA_IORP_STRESS_2022",
            "name": "EIOPA IORP II Climate Stress Test 2022",
            "scenarios": list(IORP_SCENARIOS.keys()),
            "methodology": "Asset-liability matching under NGFS climate scenarios; funding ratio impact",
            "publication": "EIOPA-BoS-22/xxx — Climate Stress Test for IORPs",
        },
        "related_frameworks": [
            {"id": "SFDR", "applicability": "Pension funds as FMPs — Art 6/8/9 classification, PAI reporting"},
            {"id": "IIGCC_NZIF_v2", "applicability": "Net zero investment framework for pension assets"},
            {"id": "TCFD", "applicability": "Climate-related financial disclosure aligned"},
            {"id": "TNFD_v1", "applicability": "Nature risk disclosure for real asset holdings"},
            {"id": "CSRD_ESRS", "applicability": "If pension entity qualifies as in-scope CSRD undertaking"},
        ],
    }


@router.get(
    "/history",
    summary="Recent IORP stress test runs from DB",
    description="Returns the last N IORP II stress assessment runs from iorp_stress_runs table.",
)
def run_history(
    fund_id: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    try:
        q = """
            SELECT id, fund_id, fund_name, iorp_type, member_count,
                   pre_stress_funding_ratio_pct, worst_case_scenario_id,
                   worst_case_funding_ratio_drop_pct, ora_compliance_status,
                   ora_items_met, ora_items_gap, sfdr_classification,
                   scenarios_run, assessment_date, created_at
            FROM iorp_stress_runs
            WHERE (:fund_id IS NULL OR fund_id = :fund_id)
            ORDER BY created_at DESC
            LIMIT :limit
        """
        rows = db.execute(text(q), {"fund_id": fund_id, "limit": limit}).mappings().all()
        return {
            "count": len(rows),
            "runs": [dict(r) for r in rows],
        }
    except Exception as exc:
        logger.warning("IORP history query failed: %s", exc)
        return {"count": 0, "runs": [], "error": str(exc)}
