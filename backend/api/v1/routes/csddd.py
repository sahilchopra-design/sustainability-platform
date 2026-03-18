"""
API Routes: EU Corporate Sustainability Due Diligence Directive (CSDDD)
=======================================================================
Directive (EU) 2024/1760

POST /api/v1/csddd/scope-assessment        — Determine CSDDD scope applicability
POST /api/v1/csddd/adverse-impacts          — Identify adverse HR & environmental impacts
POST /api/v1/csddd/dd-compliance            — Full due diligence compliance assessment
POST /api/v1/csddd/value-chain-mapping      — Value chain mapping completeness check
GET  /api/v1/csddd/ref/scope-thresholds     — Scope thresholds by group
GET  /api/v1/csddd/ref/adverse-impacts      — Adverse impact categories (HR + ENV)
GET  /api/v1/csddd/ref/dd-obligations       — Due diligence obligation definitions
GET  /api/v1/csddd/ref/climate-plan         — Climate transition plan requirements (Art 22)
GET  /api/v1/csddd/ref/penalties            — Penalty framework (Art 30-33)
GET  /api/v1/csddd/ref/cross-framework      — CSDDD ↔ CSRD / UNGP / OECD map
GET  /api/v1/csddd/ref/high-risk-sectors    — High-risk sector definitions
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.csddd_engine import CSDDDEngine

router = APIRouter(prefix="/api/v1/csddd", tags=["CSDDD"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ScopeAssessmentRequest(BaseModel):
    entity_name: str
    is_eu_company: bool = True
    employees: int = Field(0, ge=0)
    net_turnover_eur: float = Field(0, ge=0)
    eu_generated_turnover_eur: float = Field(0, ge=0)
    nace_codes: list[str] = []


class AdverseImpactRequest(BaseModel):
    entity_name: str
    nace_codes: list[str] = []
    countries_of_operation: list[str] = []
    supplier_countries: list[str] = []
    forced_labour_risk: bool = False
    child_labour_risk: bool = False
    deforestation_exposure: bool = False
    conflict_minerals_exposure: bool = False
    osh_incidents_per_1000: float = Field(0.0, ge=0)
    water_stress_exposure: bool = False
    ghg_intensity_high: bool = False
    grievance_complaints_count: int = Field(0, ge=0)


class DDComplianceRequest(BaseModel):
    entity_name: str
    scope_group: str = "group_1"
    # DD obligation scores (0-100)
    dd_policy_integrated: float = Field(0, ge=0, le=100)
    impact_identification_score: float = Field(0, ge=0, le=100)
    prevention_mitigation_score: float = Field(0, ge=0, le=100)
    remediation_score: float = Field(0, ge=0, le=100)
    remediation_provided: bool = False
    stakeholder_engagement_score: float = Field(0, ge=0, le=100)
    grievance_mechanism_operational: bool = False
    monitoring_score: float = Field(0, ge=0, le=100)
    public_reporting_score: float = Field(0, ge=0, le=100)
    # Climate transition plan
    climate_plan_exists: bool = False
    climate_plan_paris_aligned: bool = False
    climate_targets_science_based: bool = False
    scope_123_covered: bool = False
    annual_progress_reported: bool = False
    board_oversight_climate: bool = False
    # Director duty
    director_sustainability_linked_remuneration: bool = False
    director_dd_oversight: bool = False
    # EUDR overlap
    eudr_commodities_in_scope: list[str] = []
    eudr_dd_completed: bool = False
    # Financials
    net_turnover_eur: float = Field(0, ge=0)


class ValueChainMappingRequest(BaseModel):
    entity_name: str
    upstream_supplier_count: int = Field(0, ge=0)
    upstream_countries: list[str] = []
    downstream_partner_count: int = Field(0, ge=0)
    downstream_countries: list[str] = []
    tier1_mapped: bool = False
    tier2_mapped: bool = False
    tier3_plus_mapped: bool = False
    contractual_cascading_pct: float = Field(0, ge=0, le=100)
    high_risk_links_identified: int = Field(0, ge=0)
    sector_breakdown: dict = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/scope-assessment")
def assess_scope(req: ScopeAssessmentRequest):
    """Determine whether entity falls within CSDDD scope (Art 2)."""
    engine = CSDDDEngine()
    r = engine.assess_scope(
        entity_name=req.entity_name,
        is_eu_company=req.is_eu_company,
        employees=req.employees,
        net_turnover_eur=req.net_turnover_eur,
        eu_generated_turnover_eur=req.eu_generated_turnover_eur,
        nace_codes=req.nace_codes,
    )
    return {
        "entity_name": r.entity_name,
        "is_eu_company": r.is_eu_company,
        "employees": r.employees,
        "net_turnover_eur": r.net_turnover_eur,
        "eu_generated_turnover_eur": r.eu_generated_turnover_eur,
        "in_scope": r.in_scope,
        "scope_group": r.scope_group,
        "applies_from": r.applies_from,
        "high_risk_sectors": r.high_risk_sectors,
        "nace_codes": r.nace_codes,
        "notes": r.notes,
    }


@router.post("/adverse-impacts")
def identify_adverse_impacts(req: AdverseImpactRequest):
    """Identify actual & potential adverse impacts (Art 6)."""
    engine = CSDDDEngine()
    r = engine.identify_adverse_impacts(
        entity_name=req.entity_name,
        nace_codes=req.nace_codes,
        countries_of_operation=req.countries_of_operation,
        supplier_countries=req.supplier_countries,
        forced_labour_risk=req.forced_labour_risk,
        child_labour_risk=req.child_labour_risk,
        deforestation_exposure=req.deforestation_exposure,
        conflict_minerals_exposure=req.conflict_minerals_exposure,
        osh_incidents_per_1000=req.osh_incidents_per_1000,
        water_stress_exposure=req.water_stress_exposure,
        ghg_intensity_high=req.ghg_intensity_high,
        grievance_complaints_count=req.grievance_complaints_count,
    )
    return {
        "entity_name": r.entity_name,
        "value_chain_tier": r.value_chain_tier,
        "total_impacts": r.total_impacts,
        "critical_impacts": r.critical_impacts,
        "high_impacts": r.high_impacts,
        "medium_impacts": r.medium_impacts,
        "low_impacts": r.low_impacts,
        "risk_score": r.risk_score,
        "identified_impacts": r.identified_impacts,
        "sector_risk_flags": r.sector_risk_flags,
    }


@router.post("/dd-compliance")
def assess_dd_compliance(req: DDComplianceRequest):
    """Full due diligence compliance assessment (Art 5-13)."""
    engine = CSDDDEngine()
    r = engine.assess_dd_compliance(
        entity_name=req.entity_name,
        scope_group=req.scope_group,
        dd_policy_integrated=req.dd_policy_integrated,
        impact_identification_score=req.impact_identification_score,
        prevention_mitigation_score=req.prevention_mitigation_score,
        remediation_score=req.remediation_score,
        remediation_provided=req.remediation_provided,
        stakeholder_engagement_score=req.stakeholder_engagement_score,
        grievance_mechanism_operational=req.grievance_mechanism_operational,
        monitoring_score=req.monitoring_score,
        public_reporting_score=req.public_reporting_score,
        climate_plan_exists=req.climate_plan_exists,
        climate_plan_paris_aligned=req.climate_plan_paris_aligned,
        climate_targets_science_based=req.climate_targets_science_based,
        scope_123_covered=req.scope_123_covered,
        annual_progress_reported=req.annual_progress_reported,
        board_oversight_climate=req.board_oversight_climate,
        director_sustainability_linked_remuneration=req.director_sustainability_linked_remuneration,
        director_dd_oversight=req.director_dd_oversight,
        eudr_commodities_in_scope=req.eudr_commodities_in_scope,
        eudr_dd_completed=req.eudr_dd_completed,
        net_turnover_eur=req.net_turnover_eur,
    )
    return {
        "entity_name": r.entity_name,
        "assessment_date": r.assessment_date,
        "scope_group": r.scope_group,
        "overall_score": r.overall_score,
        "compliance_status": r.compliance_status,
        "obligation_scores": r.obligation_scores,
        "climate_transition_plan_score": r.climate_transition_plan_score,
        "climate_transition_plan_gaps": r.climate_transition_plan_gaps,
        "director_duty_assessment": r.director_duty_assessment,
        "grievance_mechanism_status": r.grievance_mechanism_status,
        "total_gaps": r.total_gaps,
        "critical_gaps": r.critical_gaps,
        "recommendations": r.recommendations,
        "penalty_exposure": r.penalty_exposure,
        "cross_framework_linkage": r.cross_framework_linkage,
        "eudr_overlap": r.eudr_overlap,
    }


@router.post("/value-chain-mapping")
def assess_value_chain(req: ValueChainMappingRequest):
    """Value chain mapping completeness assessment (Art 6, Art 14)."""
    engine = CSDDDEngine()
    r = engine.assess_value_chain_mapping(
        entity_name=req.entity_name,
        upstream_supplier_count=req.upstream_supplier_count,
        upstream_countries=req.upstream_countries,
        downstream_partner_count=req.downstream_partner_count,
        downstream_countries=req.downstream_countries,
        tier1_mapped=req.tier1_mapped,
        tier2_mapped=req.tier2_mapped,
        tier3_plus_mapped=req.tier3_plus_mapped,
        contractual_cascading_pct=req.contractual_cascading_pct,
        high_risk_links_identified=req.high_risk_links_identified,
        sector_breakdown=req.sector_breakdown,
    )
    return {
        "entity_name": r.entity_name,
        "tiers_mapped": r.tiers_mapped,
        "upstream_suppliers": r.upstream_suppliers,
        "downstream_partners": r.downstream_partners,
        "high_risk_links": r.high_risk_links,
        "countries_covered": r.countries_covered,
        "sector_breakdown": r.sector_breakdown,
        "mapping_completeness_pct": r.mapping_completeness_pct,
        "gaps": r.gaps,
    }


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/scope-thresholds")
def ref_scope_thresholds():
    """CSDDD scope thresholds by group (Art 2)."""
    return {"scope_thresholds": CSDDDEngine.get_scope_thresholds()}


@router.get("/ref/adverse-impacts")
def ref_adverse_impacts():
    """Adverse impact categories — human rights & environmental."""
    return {"adverse_impact_categories": CSDDDEngine.get_adverse_impact_categories()}


@router.get("/ref/dd-obligations")
def ref_dd_obligations():
    """Due diligence obligation definitions (Art 5-13)."""
    return {"dd_obligations": CSDDDEngine.get_dd_obligations()}


@router.get("/ref/climate-plan")
def ref_climate_plan():
    """Climate transition plan requirements (Art 22)."""
    return {"climate_plan_requirements": CSDDDEngine.get_climate_transition_plan_requirements()}


@router.get("/ref/penalties")
def ref_penalties():
    """Penalty framework (Art 30-33)."""
    return {"penalty_framework": CSDDDEngine.get_penalty_framework()}


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """CSDDD ↔ CSRD ESRS / UNGP / OECD cross-reference map."""
    return {"cross_framework_map": CSDDDEngine.get_cross_framework_map()}


@router.get("/ref/high-risk-sectors")
def ref_high_risk_sectors():
    """High-risk sector definitions with NACE codes & risk areas."""
    return {"high_risk_sectors": CSDDDEngine.get_high_risk_sectors()}
