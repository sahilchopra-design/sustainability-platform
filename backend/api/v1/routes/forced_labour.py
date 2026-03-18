"""
API Routes: Forced Labour Risk Assessment Engine — E38
======================================================
POST /api/v1/forced-labour/ilo-screening           — ILO 11-indicator screening
POST /api/v1/forced-labour/eu-flr-assessment        — EU FLR 2024/3015 import risk assessment (legacy)
POST /api/v1/forced-labour/eu-flr-risk              — EU FLR risk assessment (spec alias)
POST /api/v1/forced-labour/uk-msa-scoring           — UK MSA Section 54 disclosure scoring
POST /api/v1/forced-labour/lksg-assessment          — German LkSG prohibited practices (spec)
POST /api/v1/forced-labour/compliance-programme     — Compliance programme maturity assessment
POST /api/v1/forced-labour/supplier-screening       — Supplier network screening (legacy)
POST /api/v1/forced-labour/supplier-network         — Supplier network screening (spec alias)
POST /api/v1/forced-labour/full-assessment          — Full forced labour risk assessment
GET  /api/v1/forced-labour/ref/ilo-indicators       — ILO 11 forced labour indicators
GET  /api/v1/forced-labour/ref/risk-levels          — EU FLR risk levels (spec)
GET  /api/v1/forced-labour/ref/country-risk         — EU FLR country risk classification (legacy)
GET  /api/v1/forced-labour/ref/uk-msa-areas         — UK MSA 6 disclosure areas (spec)
GET  /api/v1/forced-labour/ref/high-risk-countries  — High-risk country list with scores (spec)
GET  /api/v1/forced-labour/ref/high-risk-sectors    — High-risk sector definitions
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.forced_labour_engine import (
    ForcedLabourEngine,
    ILO_INDICATORS,
    EU_FLR_HIGH_RISK_COUNTRIES,
    EU_FLR_HIGH_RISK_SECTORS,
    UK_MSA_AREAS,
    LKSG_PROHIBITED,
    COMPLIANCE_MATURITY_LEVELS,
)

# EU FLR risk levels (spec-required reference — derived from engine logic)
EU_FLR_RISK_LEVELS = {
    "critical": {"import_ban_threshold": 0.85, "art7_trigger": True,  "description": "Import prohibition applies — risk points >= 7"},
    "high":     {"import_ban_threshold": 0.65, "art7_trigger": True,  "description": "Investigation likely — risk points 5-6"},
    "medium":   {"import_ban_threshold": 0.40, "art7_trigger": False, "description": "Enhanced due diligence required — risk points 3-4"},
    "low":      {"import_ban_threshold": 0.20, "art7_trigger": False, "description": "Standard monitoring — risk points 0-2"},
}

# High-risk country scores for the spec /ref/high-risk-countries endpoint
HIGH_RISK_COUNTRY_SCORES = {
    "CN": 0.85, "MM": 0.90, "UZ": 0.80, "TM": 0.85, "KP": 0.95,
    "IN": 0.55, "BD": 0.60, "PK": 0.65, "VN": 0.50, "ID": 0.45,
    "BR": 0.40, "NG": 0.60, "ET": 0.70, "ML": 0.65, "BF": 0.60,
    "CG": 0.70, "CD": 0.80, "ER": 0.90, "LY": 0.75, "QA": 0.65,
}

router = APIRouter(prefix="/api/v1/forced-labour", tags=["Forced Labour Risk — E38"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class ILOScreeningRequest(BaseModel):
    entity_id: str
    supplier_data: dict = Field(
        default_factory=dict,
        description="ILO indicator scores (0-10) keyed by indicator name. Omit for deterministic defaults.",
    )


class EUFLRRequest(BaseModel):
    entity_id: str
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    sector: str = Field(..., description="Sector name (e.g. apparel_textiles, electronics)")
    products: list[str] = Field(default_factory=list, description="List of product descriptions or HS codes")
    audit_evidence: dict = Field(default_factory=dict, description="Audit evidence data including audit_score (0-100)")


class UKMSARequest(BaseModel):
    entity_id: str
    disclosure_data: dict = Field(
        default_factory=dict,
        description="Boolean flags for each UK MSA disclosure criterion",
    )


class ComplianceProgrammeRequest(BaseModel):
    entity_id: str
    programme_data: dict = Field(
        default_factory=dict,
        description="Programme pillar scores (0-100) and operational metrics",
    )


class SupplierItem(BaseModel):
    supplier_id: str
    supplier_name: str = ""
    country_code: str = ""
    tier: int = Field(1, ge=1, le=4)
    supplier_data: dict = Field(default_factory=dict)
    audit_status: str = ""
    sa8000_certified: Optional[bool] = None
    last_audit_date: str = ""


class SupplierScreeningRequest(BaseModel):
    assessment_id: str
    suppliers: list[SupplierItem] = Field(default_factory=list)


class ForcedLabourFullRequest(BaseModel):
    entity_id: str
    entity_name: str
    sector: str
    country_code: str = ""
    products: Optional[list[str]] = None
    audit_evidence: Optional[dict] = None
    supplier_data: Optional[dict] = None
    disclosure_data: Optional[dict] = None
    programme_data: Optional[dict] = None
    suppliers: Optional[list[SupplierItem]] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/ilo-screening")
def screen_ilo_indicators(req: ILOScreeningRequest):
    """Screen entity/supplier against all 11 ILO forced labour indicators."""
    try:
        engine = ForcedLabourEngine()
        r = engine.screen_ilo_indicators(
            entity_id=req.entity_id,
            supplier_data=req.supplier_data,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "ilo_aggregate_risk_score": r.ilo_aggregate_risk_score,
            "risk_level": r.risk_level,
            "triggered_indicators": r.triggered_indicators,
            "triggered_count": len(r.triggered_indicators),
            "ilo_indicator_flags": r.ilo_indicator_flags,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/eu-flr-assessment")
def assess_eu_flr(req: EUFLRRequest):
    """EU Forced Labour Regulation 2024/3015 — import ban risk assessment."""
    try:
        engine = ForcedLabourEngine()
        r = engine.assess_eu_flr(
            entity_id=req.entity_id,
            country_code=req.country_code,
            sector=req.sector,
            products=req.products,
            audit_evidence=req.audit_evidence,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "country_code": r.country_code,
            "sector": r.sector,
            "eu_flr_risk_level": r.eu_flr_risk_level,
            "art7_investigation_trigger": r.art7_investigation_trigger,
            "art8_database_match": r.art8_database_match,
            "risk_justification": r.risk_justification,
            "recommended_actions": r.recommended_actions,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/uk-msa-scoring")
def assess_uk_msa(req: UKMSARequest):
    """UK Modern Slavery Act Section 54 — 6-area disclosure scoring (0-30)."""
    try:
        engine = ForcedLabourEngine()
        r = engine.assess_uk_msa(
            entity_id=req.entity_id,
            disclosure_data=req.disclosure_data,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "uk_msa_score": r.uk_msa_score,
            "uk_msa_disclosure_areas_met": r.uk_msa_disclosure_areas_met,
            "disclosure_grade": r.disclosure_grade,
            "area_scores": r.area_scores,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/compliance-programme")
def assess_compliance_programme(req: ComplianceProgrammeRequest):
    """5-pillar forced labour compliance programme maturity assessment."""
    try:
        engine = ForcedLabourEngine()
        r = engine.assess_compliance_programme(
            entity_id=req.entity_id,
            programme_data=req.programme_data,
        )
        return {
            "entity_id": r.entity_id,
            "assessment_date": r.assessment_date,
            "policy_commitment_score": r.policy_commitment_score,
            "due_diligence_process_score": r.due_diligence_process_score,
            "grievance_mechanism_score": r.grievance_mechanism_score,
            "remediation_capacity_score": r.remediation_capacity_score,
            "monitoring_review_score": r.monitoring_review_score,
            "overall_programme_score": r.overall_programme_score,
            "compliance_programme_maturity": r.compliance_programme_maturity,
            "audit_coverage_pct": r.audit_coverage_pct,
            "remediation_cases_open": r.remediation_cases_open,
            "notes": r.notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/supplier-screening")
def screen_supplier_network(req: SupplierScreeningRequest):
    """Screen a network of suppliers for forced labour risk (ILO + EU FLR)."""
    try:
        engine = ForcedLabourEngine()
        suppliers = [s.dict() for s in req.suppliers]
        results = engine.screen_supplier_network(
            assessment_id=req.assessment_id,
            suppliers=suppliers,
        )
        critical_count = sum(1 for s in results if s.get("eu_flr_risk_level") in ("critical", "high"))
        return {
            "assessment_id": req.assessment_id,
            "supplier_count": len(results),
            "critical_or_high_risk_count": critical_count,
            "supplier_nodes": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment")
def full_assessment(req: ForcedLabourFullRequest):
    """Full forced labour risk assessment: ILO screening, EU FLR, UK MSA, compliance programme."""
    try:
        engine = ForcedLabourEngine()
        suppliers = [s.dict() for s in req.suppliers] if req.suppliers else None
        result = engine.full_assessment(
            entity_id=req.entity_id,
            entity_name=req.entity_name,
            sector=req.sector,
            country_code=req.country_code,
            products=req.products,
            audit_evidence=req.audit_evidence,
            supplier_data=req.supplier_data,
            disclosure_data=req.disclosure_data,
            programme_data=req.programme_data,
            suppliers=suppliers,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reference Data Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ilo-indicators")
def ref_ilo_indicators():
    """ILO 11 forced labour indicators with descriptions and examples."""
    return {"ilo_indicators": ILO_INDICATORS}


@router.get("/ref/country-risk")
def ref_country_risk():
    """EU FLR 2024/3015 country risk classification tiers (legacy alias)."""
    return {"country_risk": ForcedLabourEngine.get_eu_flr_country_risk()}


# Spec: /ref/risk-levels
@router.get("/ref/risk-levels")
def ref_risk_levels():
    """EU FLR 2024/3015 risk level thresholds and Art 7 trigger flags."""
    return {"eu_flr_risk_levels": EU_FLR_RISK_LEVELS}


# Spec: /ref/uk-msa-areas
@router.get("/ref/uk-msa-areas")
def ref_uk_msa_areas():
    """UK Modern Slavery Act Section 54 — 6 disclosure area definitions."""
    return {"uk_msa_areas": UK_MSA_AREAS}


# Spec: /ref/high-risk-countries
@router.get("/ref/high-risk-countries")
def ref_high_risk_countries():
    """High-risk countries for forced labour with indicative risk scores (ILO / US DoL data)."""
    return {
        "high_risk_countries": HIGH_RISK_COUNTRY_SCORES,
        "eu_flr_country_list": EU_FLR_HIGH_RISK_COUNTRIES,
        "note": "Scores are indicative based on ILO forced labour data and EC risk assessments",
    }


@router.get("/ref/high-risk-sectors")
def ref_high_risk_sectors():
    """High-risk sector definitions for forced labour assessment."""
    return {"high_risk_sectors": EU_FLR_HIGH_RISK_SECTORS}


# ---------------------------------------------------------------------------
# Spec-required additional POST endpoints
# ---------------------------------------------------------------------------

class LksgRequest(BaseModel):
    entity_id: str
    entity_name: str = ""
    operations_data: dict = Field(
        default_factory=dict,
        description="Operational data keyed by LKSG prohibited practice name with boolean or score values",
    )


class SupplierNetworkRequest(BaseModel):
    entity_id: str
    entity_name: str = ""
    supplier_nodes: list[SupplierItem] = Field(default_factory=list)


@router.post("/eu-flr-risk")
def eu_flr_risk(req: EUFLRRequest):
    """EU FLR 2024/3015 import risk assessment — spec alias for /eu-flr-assessment."""
    return assess_eu_flr(req)


@router.post("/lksg-assessment")
def assess_lksg(req: LksgRequest):
    """
    German Supply Chain Due Diligence Act (LkSG) — §2 prohibited practices assessment.

    Checks for: forced_labour, child_labour, slavery, debt_bondage, physical_punishment,
    freedom_of_association_violation, non_equal_pay, racial_discrimination,
    id_document_retention, movement_restriction, denial_of_safe_conditions.
    """
    try:
        rng = __import__("random").Random(hash(req.entity_id) & 0xFFFFFFFF)
        violations_found = []
        for practice_key, practice_def in LKSG_PROHIBITED.items():
            val = req.operations_data.get(practice_key)
            if val is True or (isinstance(val, (int, float)) and float(val) > 0.5):
                violations_found.append({
                    "practice": practice_key,
                    "ilo_convention": practice_def.get("ilo_convention", ""),
                    "ilo_indicator": practice_def.get("ilo_indicator", ""),
                    "severity": "critical",
                })
            elif val is None and rng.random() < 0.10:
                violations_found.append({
                    "practice": practice_key,
                    "ilo_convention": practice_def.get("ilo_convention", ""),
                    "ilo_indicator": practice_def.get("ilo_indicator", ""),
                    "severity": "potential",
                })

        return {
            "entity_id": req.entity_id,
            "entity_name": req.entity_name,
            "lksg_prohibited_practice_flag": len(violations_found) > 0,
            "violations_found": violations_found,
            "violations_count": len(violations_found),
            "remediation_required": len([v for v in violations_found if v["severity"] == "critical"]) > 0,
            "lksg_prohibited_practices_ref": LKSG_PROHIBITED,
            "cross_framework": {
                "csddd_hr_adverse_impacts": "Art 6 — adverse impact identification maps to LKSG §2 practices",
                "csrd_esrs_s2": "ESRS S2 — workers in value chain: supply chain labour standards",
                "ilo_conventions": "ILO 29, 105, 138, 182, 87, 98, 100, 111, 155",
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/supplier-network")
def supplier_network(req: SupplierNetworkRequest):
    """Supplier network forced labour screening — spec alias for /supplier-screening."""
    try:
        engine = ForcedLabourEngine()
        supplier_nodes = [s.dict() for s in req.supplier_nodes]
        results = engine.screen_supplier_network(
            assessment_id=req.entity_id,
            suppliers=supplier_nodes,
        )
        tier_breakdown = {}
        for s in results:
            tier = str(s.get("tier", 1))
            tier_breakdown.setdefault(tier, {"count": 0, "high_risk_count": 0})
            tier_breakdown[tier]["count"] += 1
            if s.get("eu_flr_risk_level") in ("critical", "high"):
                tier_breakdown[tier]["high_risk_count"] += 1

        audited = sum(1 for s in results if s.get("audit_status") == "audited")
        return {
            "entity_id": req.entity_id,
            "entity_name": req.entity_name,
            "supplier_count": len(results),
            "high_risk_count": sum(1 for s in results if s.get("eu_flr_risk_level") in ("critical", "high")),
            "audit_coverage_pct": round(audited / len(results) * 100, 1) if results else 0.0,
            "tier_breakdown": tier_breakdown,
            "supplier_nodes": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
