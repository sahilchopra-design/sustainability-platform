"""
API Routes: EU Deforestation Regulation (EUDR) 2023/1115
=========================================================
POST /api/v1/eudr/due-diligence           — Full due diligence assessment
POST /api/v1/eudr/commodity-screening      — Screen product for EUDR commodity scope
POST /api/v1/eudr/country-risk             — Country risk classification (Art 29)
POST /api/v1/eudr/traceability-check       — Supply chain traceability verification (Art 9)
POST /api/v1/eudr/compliance-gap           — Compliance gap analysis with remediation plan
POST /api/v1/eudr/due-diligence-statement  — Generate DDS per Art 4(2)
GET  /api/v1/eudr/ref/commodities          — EUDR commodity definitions (Annex I)
GET  /api/v1/eudr/ref/country-benchmarks   — Country risk tier benchmarks (Art 29)
GET  /api/v1/eudr/ref/enforcement-timeline — Enforcement milestones
GET  /api/v1/eudr/ref/certifications       — Recognised certification schemes
GET  /api/v1/eudr/ref/requirements         — Due diligence requirement definitions
GET  /api/v1/eudr/ref/cross-framework      — EUDR ↔ ESRS E4 / EU Taxonomy / GRI map
GET  /api/v1/eudr/ref/hs-codes             — HS code → commodity lookup
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.eudr_engine import EUDREngine

router = APIRouter(prefix="/api/v1/eudr", tags=["EUDR"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CommodityScreenRequest(BaseModel):
    product_name: str
    hs_code: str


class CountryRiskRequest(BaseModel):
    country_iso2: str
    commodity: str = ""


class TraceabilityRequest(BaseModel):
    operator_id: str
    commodity: str
    geolocation_provided: bool = False
    geolocation_type: str = ""
    plot_area_ha: Optional[float] = None
    supplier_name: str = ""
    supplier_address: str = ""
    production_date: str = ""
    quantity_kg: float = Field(0, ge=0)
    local_law_evidence: bool = False
    deforestation_free_evidence: bool = False


class DueDiligenceRequest(BaseModel):
    operator_id: str
    operator_name: str
    operator_type: str = "operator"
    commodities: list[str] = []
    countries_of_origin: list[str] = []
    certifications: list[str] = []
    # Traceability inputs
    geolocation_provided: bool = False
    geolocation_type: str = ""
    plot_area_ha: Optional[float] = None
    supplier_name: str = ""
    supplier_address: str = ""
    production_date: str = ""
    quantity_kg: float = Field(0, ge=0)
    local_law_evidence: bool = False
    deforestation_free_evidence: bool = False
    # Risk mitigation
    independent_audit: bool = False
    satellite_monitoring: bool = False
    third_party_verification: bool = False


class ComplianceGapRequest(BaseModel):
    """Runs full DD then generates gap analysis."""
    operator_id: str
    operator_name: str
    operator_type: str = "operator"
    commodities: list[str] = []
    countries_of_origin: list[str] = []
    certifications: list[str] = []
    geolocation_provided: bool = False
    geolocation_type: str = ""
    plot_area_ha: Optional[float] = None
    supplier_name: str = ""
    supplier_address: str = ""
    production_date: str = ""
    quantity_kg: float = Field(0, ge=0)
    local_law_evidence: bool = False
    deforestation_free_evidence: bool = False
    independent_audit: bool = False
    satellite_monitoring: bool = False
    third_party_verification: bool = False


class DDSRequest(BaseModel):
    """Generate Due Diligence Statement — same inputs as DD assessment."""
    operator_id: str
    operator_name: str
    operator_type: str = "operator"
    commodities: list[str] = []
    countries_of_origin: list[str] = []
    certifications: list[str] = []
    geolocation_provided: bool = False
    geolocation_type: str = ""
    plot_area_ha: Optional[float] = None
    supplier_name: str = ""
    supplier_address: str = ""
    production_date: str = ""
    quantity_kg: float = Field(0, ge=0)
    local_law_evidence: bool = False
    deforestation_free_evidence: bool = False
    independent_audit: bool = False
    satellite_monitoring: bool = False
    third_party_verification: bool = False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/commodity-screening")
def screen_commodity(req: CommodityScreenRequest):
    """Screen a product by HS code for EUDR Annex I scope."""
    engine = EUDREngine()
    r = engine.screen_commodity(req.product_name, req.hs_code)
    return {
        "product_name": r.product_name,
        "hs_code": r.hs_code,
        "in_scope": r.in_scope,
        "matched_commodity": r.matched_commodity,
        "deforestation_cutoff": r.deforestation_cutoff,
        "derived_products": r.derived_products,
        "notes": r.notes,
    }


@router.post("/country-risk")
def classify_country_risk(req: CountryRiskRequest):
    """Classify country risk tier under Article 29."""
    engine = EUDREngine()
    r = engine.classify_country_risk(req.country_iso2, req.commodity)
    return {
        "country_iso2": r.country_iso2,
        "country_name": r.country_name,
        "risk_tier": r.risk_tier,
        "commodities_at_risk": r.commodities_at_risk,
        "due_diligence_level": r.due_diligence_level,
        "article_reference": r.article_reference,
        "notes": r.notes,
    }


@router.post("/traceability-check")
def verify_traceability(req: TraceabilityRequest):
    """Verify supply chain traceability per Article 9."""
    engine = EUDREngine()
    r = engine.verify_traceability(
        operator_id=req.operator_id,
        commodity=req.commodity,
        geolocation_provided=req.geolocation_provided,
        geolocation_type=req.geolocation_type,
        plot_area_ha=req.plot_area_ha,
        supplier_name=req.supplier_name,
        supplier_address=req.supplier_address,
        production_date=req.production_date,
        quantity_kg=req.quantity_kg,
        local_law_evidence=req.local_law_evidence,
        deforestation_free_evidence=req.deforestation_free_evidence,
    )
    return {
        "operator_id": r.operator_id,
        "commodity": r.commodity,
        "traceability_score": r.traceability_score,
        "geolocation_compliant": r.geolocation_compliant,
        "supplier_identified": r.supplier_identified,
        "production_date_verified": r.production_date_verified,
        "quantity_verified": r.quantity_verified,
        "local_law_compliance": r.local_law_compliance,
        "deforestation_free_verified": r.deforestation_free_verified,
        "gaps": r.gaps,
        "article_references": r.article_references,
    }


@router.post("/due-diligence")
def assess_due_diligence(req: DueDiligenceRequest):
    """Full due diligence assessment per Articles 4-12."""
    engine = EUDREngine()
    r = engine.assess_due_diligence(
        operator_id=req.operator_id,
        operator_name=req.operator_name,
        operator_type=req.operator_type,
        commodities=req.commodities,
        countries_of_origin=req.countries_of_origin,
        certifications=req.certifications,
        geolocation_provided=req.geolocation_provided,
        geolocation_type=req.geolocation_type,
        plot_area_ha=req.plot_area_ha,
        supplier_name=req.supplier_name,
        supplier_address=req.supplier_address,
        production_date=req.production_date,
        quantity_kg=req.quantity_kg,
        local_law_evidence=req.local_law_evidence,
        deforestation_free_evidence=req.deforestation_free_evidence,
        independent_audit=req.independent_audit,
        satellite_monitoring=req.satellite_monitoring,
        third_party_verification=req.third_party_verification,
    )
    return {
        "operator_id": r.operator_id,
        "operator_name": r.operator_name,
        "operator_type": r.operator_type,
        "assessment_date": r.assessment_date,
        "commodities_assessed": r.commodities_assessed,
        "countries_of_origin": r.countries_of_origin,
        "information_score": r.information_score,
        "risk_assessment_score": r.risk_assessment_score,
        "risk_mitigation_score": r.risk_mitigation_score,
        "overall_compliance_score": r.overall_compliance_score,
        "compliance_status": r.compliance_status,
        "due_diligence_level": r.due_diligence_level,
        "country_risk_results": r.country_risk_results,
        "traceability_results": r.traceability_results,
        "gaps": r.gaps,
        "recommendations": r.recommendations,
        "certifications": r.certifications,
        "esrs_e4_linkage": r.esrs_e4_linkage,
        "eu_taxonomy_biodiversity_dnsh": r.eu_taxonomy_biodiversity_dnsh,
        "enforcement_deadline": r.enforcement_deadline,
        "days_until_deadline": r.days_until_deadline,
        "statement_ready": r.statement_ready,
    }


@router.post("/compliance-gap")
def analyse_compliance_gaps(req: ComplianceGapRequest):
    """Compliance gap analysis with remediation plan."""
    engine = EUDREngine()
    dd = engine.assess_due_diligence(
        operator_id=req.operator_id,
        operator_name=req.operator_name,
        operator_type=req.operator_type,
        commodities=req.commodities,
        countries_of_origin=req.countries_of_origin,
        certifications=req.certifications,
        geolocation_provided=req.geolocation_provided,
        geolocation_type=req.geolocation_type,
        plot_area_ha=req.plot_area_ha,
        supplier_name=req.supplier_name,
        supplier_address=req.supplier_address,
        production_date=req.production_date,
        quantity_kg=req.quantity_kg,
        local_law_evidence=req.local_law_evidence,
        deforestation_free_evidence=req.deforestation_free_evidence,
        independent_audit=req.independent_audit,
        satellite_monitoring=req.satellite_monitoring,
        third_party_verification=req.third_party_verification,
    )
    gap = engine.analyse_compliance_gaps(req.operator_id, dd)
    return {
        "operator_id": gap.operator_id,
        "total_gaps": gap.total_gaps,
        "critical_gaps": gap.critical_gaps,
        "major_gaps": gap.major_gaps,
        "minor_gaps": gap.minor_gaps,
        "gap_details": gap.gap_details,
        "remediation_plan": gap.remediation_plan,
        "estimated_remediation_weeks": gap.estimated_remediation_weeks,
        "readiness_pct": gap.readiness_pct,
    }


@router.post("/due-diligence-statement")
def generate_dds(req: DDSRequest):
    """Generate Due Diligence Statement per Article 4(2)."""
    engine = EUDREngine()
    dd = engine.assess_due_diligence(
        operator_id=req.operator_id,
        operator_name=req.operator_name,
        operator_type=req.operator_type,
        commodities=req.commodities,
        countries_of_origin=req.countries_of_origin,
        certifications=req.certifications,
        geolocation_provided=req.geolocation_provided,
        geolocation_type=req.geolocation_type,
        plot_area_ha=req.plot_area_ha,
        supplier_name=req.supplier_name,
        supplier_address=req.supplier_address,
        production_date=req.production_date,
        quantity_kg=req.quantity_kg,
        local_law_evidence=req.local_law_evidence,
        deforestation_free_evidence=req.deforestation_free_evidence,
        independent_audit=req.independent_audit,
        satellite_monitoring=req.satellite_monitoring,
        third_party_verification=req.third_party_verification,
    )
    return engine.generate_dds(dd)


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/commodities")
def ref_commodities():
    """EUDR commodity definitions (Annex I)."""
    return {"eudr_commodities": EUDREngine.get_commodities()}


@router.get("/ref/country-benchmarks")
def ref_country_benchmarks():
    """Country risk tier benchmarks (Art 29)."""
    return {"country_benchmarks": EUDREngine.get_country_benchmarks()}


@router.get("/ref/enforcement-timeline")
def ref_enforcement_timeline():
    """EUDR enforcement milestones."""
    return {"enforcement_timeline": EUDREngine.get_enforcement_timeline()}


@router.get("/ref/certifications")
def ref_certifications():
    """Recognised certification schemes."""
    return {"certification_schemes": EUDREngine.get_certification_schemes()}


@router.get("/ref/requirements")
def ref_requirements():
    """Due diligence requirement definitions by article."""
    return {"due_diligence_requirements": EUDREngine.get_due_diligence_requirements()}


@router.get("/ref/cross-framework")
def ref_cross_framework():
    """EUDR ↔ ESRS E4 / EU Taxonomy / GRI cross-reference map."""
    return {"cross_framework_map": EUDREngine.get_cross_framework_map()}


@router.get("/ref/hs-codes")
def ref_hs_codes():
    """HS code → commodity lookup."""
    return {"hs_code_lookup": EUDREngine.get_hs_code_lookup()}
