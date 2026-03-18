"""
E78 — Carbon Accounting AI & Automation Routes
===============================================
FastAPI routes for AI-assisted carbon accounting services.

Prefix: /api/v1/carbon-accounting-ai
Tag:    E78 Carbon Accounting AI
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.carbon_accounting_ai_engine import (
    EMISSION_FACTOR_DATABASES,
    EMISSION_FACTOR_LOOKUP,
    SCOPE3_CLASSIFICATION_RULES,
    XBRL_ESRS_CONCEPTS,
    CDP_QUESTIONNAIRE_STRUCTURE,
    CarbonAccountingAIEngine,
    EmissionFactorQuery,
    GHGDisclosureInput,
    Scope3TransactionInput,
    carbon_accounting_ai_engine,
)

router = APIRouter(
    prefix="/api/v1/carbon-accounting-ai",
    tags=["E78 Carbon Accounting AI"],
)


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class GHGDisclosureRequest(BaseModel):
    entity_name: str = Field(..., description="Legal entity name")
    reporting_year: int = Field(..., ge=2000, le=2100, description="Reporting year (e.g. 2024)")
    scope1_tco2e: Optional[float] = Field(None, ge=0, description="Gross Scope 1 emissions (tCO2e)")
    scope2_location_tco2e: Optional[float] = Field(None, ge=0, description="Scope 2 location-based (tCO2e)")
    scope2_market_tco2e: Optional[float] = Field(None, ge=0, description="Scope 2 market-based (tCO2e)")
    scope3_categories: Optional[Dict[int, float]] = Field(
        None, description="Scope 3 by category number (1-15) in tCO2e"
    )
    base_year: Optional[int] = Field(None, ge=1990, le=2100, description="GHG base year")
    consolidation_approach: Optional[str] = Field(
        None, description="equity_share | operational_control | financial_control"
    )
    boundary_description: Optional[str] = Field(None, description="Organisational boundary description")
    verification_status: Optional[str] = Field(
        None, description="none | limited | reasonable"
    )
    biogenic_emissions_tco2e: Optional[float] = Field(None, ge=0, description="Biogenic CO2 (tCO2e)")
    uncertainty_pct: Optional[float] = Field(None, ge=0, le=100, description="Uncertainty range (±%)")
    ghg_reduction_target_pct: Optional[float] = Field(None, ge=0, le=100, description="GHG reduction target (%)")
    target_year: Optional[int] = Field(None, description="GHG target year")
    sbti_status: Optional[str] = Field(None, description="committed | approved | not_committed")
    cdp_responses: Optional[Dict[str, Any]] = Field(None, description="CDP questionnaire section responses")
    industry_sector: Optional[str] = Field(None, description="Industry sector for materiality scoring")
    revenue_eur_m: Optional[float] = Field(None, description="Net revenue (EUR millions)")
    fte_count: Optional[int] = Field(None, description="Full-time equivalent employees")
    energy_mwh: Optional[float] = Field(None, description="Total energy consumption (MWh)")
    renewable_energy_pct: Optional[float] = Field(None, ge=0, le=100, description="Renewable energy (%)")


class EmissionFactorRequest(BaseModel):
    activity_description: str = Field(..., description="Description of the emitting activity")
    quantity: float = Field(..., gt=0, description="Activity quantity")
    unit: Optional[str] = Field(None, description="Unit of activity (e.g. kWh, litre, km)")
    country: Optional[str] = Field(None, description="Country code for geography-specific EF")
    year: Optional[int] = Field(None, description="Year of activity (for time-sensitive EFs)")
    preferred_database: Optional[str] = Field(
        None, description="Preferred EF database: IPCC_AR6 | EPA_EGRID | DEFRA_2023 | ECOINVENT_39 | IEA_WEO_2023"
    )


class Scope3TransactionRequest(BaseModel):
    supplier_name: str = Field(..., description="Supplier / counterparty name")
    spend_amount: float = Field(..., gt=0, description="Transaction spend amount")
    currency: str = Field("USD", description="Currency code")
    sic_code: Optional[int] = Field(None, description="SIC industry code of supplier")
    description: Optional[str] = Field(None, description="Transaction or line item description")
    transaction_type: Optional[str] = Field(None, description="purchase | capex | lease | investment | travel")


class DQSMetadataRequest(BaseModel):
    data_source: str = Field(
        "estimate",
        description="primary_measurement | supplier_specific | industry_average | spend_based | estimate"
    )
    verification_status: str = Field(
        "unverified",
        description="third_party_reasonable | third_party_limited | internal_review | unverified"
    )
    measurement_approach: str = Field(
        "spend_proxy",
        description="direct_measurement | calculation_primary | calculation_secondary | spend_proxy"
    )
    coverage_pct: float = Field(50.0, ge=0, le=100, description="Activity coverage (%)")
    recency_yrs: float = Field(1.0, ge=0, description="Years since data was collected")


class CDPScoringRequest(BaseModel):
    responses: Dict[str, Any] = Field(
        default_factory=dict,
        description="CDP section responses keyed by section ID (C1-C12). Each value: {completeness, quality_score, has_quantitative_evidence}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "responses": {
                    "C1": {"completeness": 0.9, "quality_score": 0.8, "has_quantitative_evidence": True},
                    "C4": {"completeness": 0.7, "quality_score": 0.65, "has_quantitative_evidence": True},
                    "C6": {"completeness": 1.0, "quality_score": 0.85, "has_quantitative_evidence": True},
                }
            }
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/assess",
    summary="Full AI-Assisted Carbon Accounting Assessment",
    description=(
        "Run all E78 sub-engines: GHG Protocol compliance check, XBRL auto-tagging, "
        "CDP response scoring, DQS derivation, emission factor matching, Scope 3 classification, "
        "and data gap intelligence. Returns a consolidated readiness score and priority actions."
    ),
)
def full_assessment(request: GHGDisclosureRequest) -> Dict[str, Any]:
    """Execute all Carbon Accounting AI sub-modules for a single entity."""
    try:
        d = GHGDisclosureInput(
            entity_name=request.entity_name,
            reporting_year=request.reporting_year,
            scope1_tco2e=request.scope1_tco2e,
            scope2_location_tco2e=request.scope2_location_tco2e,
            scope2_market_tco2e=request.scope2_market_tco2e,
            scope3_categories=request.scope3_categories,
            base_year=request.base_year,
            consolidation_approach=request.consolidation_approach,
            boundary_description=request.boundary_description,
            verification_status=request.verification_status,
            biogenic_emissions_tco2e=request.biogenic_emissions_tco2e,
            uncertainty_pct=request.uncertainty_pct,
            ghg_reduction_target_pct=request.ghg_reduction_target_pct,
            target_year=request.target_year,
            sbti_status=request.sbti_status,
            cdp_responses=request.cdp_responses,
            industry_sector=request.industry_sector,
            revenue_eur_m=request.revenue_eur_m,
            fte_count=request.fte_count,
            energy_mwh=request.energy_mwh,
            renewable_energy_pct=request.renewable_energy_pct,
        )
        result = carbon_accounting_ai_engine.full_assessment(d)
        return {
            "entity_name": result.entity_name,
            "reporting_year": result.reporting_year,
            "overall_readiness_score": result.overall_readiness_score,
            "priority_actions": result.priority_actions,
            "ghg_compliance": result.ghg_compliance,
            "ef_matching": result.ef_matching,
            "scope3_classification": result.scope3_classification,
            "dqs_score": result.dqs_score,
            "xbrl_tagging": result.xbrl_tagging,
            "cdp_scoring": result.cdp_scoring,
            "data_gaps": result.data_gaps,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/ghg-compliance",
    summary="GHG Protocol Compliance Check",
    description=(
        "Check completeness and quality of GHG disclosures against GHG Protocol Corporate Standard. "
        "Scores: boundary setting, base year, Scope 1/2/3 completeness, verification, biogenic carbon, "
        "uncertainty. Returns compliance %, criterion scores, and gap list."
    ),
)
def ghg_compliance(request: GHGDisclosureRequest) -> Dict[str, Any]:
    """GHG Protocol compliance scoring with gap identification."""
    try:
        d = GHGDisclosureInput(
            entity_name=request.entity_name,
            reporting_year=request.reporting_year,
            scope1_tco2e=request.scope1_tco2e,
            scope2_location_tco2e=request.scope2_location_tco2e,
            scope2_market_tco2e=request.scope2_market_tco2e,
            scope3_categories=request.scope3_categories,
            base_year=request.base_year,
            consolidation_approach=request.consolidation_approach,
            boundary_description=request.boundary_description,
            verification_status=request.verification_status,
            biogenic_emissions_tco2e=request.biogenic_emissions_tco2e,
            uncertainty_pct=request.uncertainty_pct,
            ghg_reduction_target_pct=request.ghg_reduction_target_pct,
            target_year=request.target_year,
            sbti_status=request.sbti_status,
            industry_sector=request.industry_sector,
        )
        return carbon_accounting_ai_engine.check_ghg_compliance(d)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/ef-matching",
    summary="Emission Factor Auto-Matching",
    description=(
        "Match an activity description to the best available emission factor across IPCC AR6, "
        "US EPA eGRID 2022, DEFRA 2023, ecoinvent 3.9, and IEA WEO 2023 databases. "
        "Returns EF (kgCO2e/unit), confidence score, DQS tier, and alternative EFs."
    ),
)
def ef_matching(request: EmissionFactorRequest) -> Dict[str, Any]:
    """Keyword-based emission factor matching across 5 databases, 40 activity categories."""
    try:
        query = EmissionFactorQuery(
            activity_description=request.activity_description,
            quantity=request.quantity,
            unit=request.unit,
            country=request.country,
            year=request.year,
            preferred_database=request.preferred_database,
        )
        return carbon_accounting_ai_engine.match_emission_factor(query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/scope3-classify",
    summary="Scope 3 Category Auto-Classification",
    description=(
        "Classify a financial transaction into GHG Protocol Scope 3 Category 1-15 using "
        "supplier name, spend, SIC code, and description. Returns primary category, confidence, "
        "FLAG/non-FLAG split, DQS auto-assignment, and alternative categories."
    ),
)
def scope3_classify(request: Scope3TransactionRequest) -> Dict[str, Any]:
    """Auto-classify transaction spend into Scope 3 GHG Protocol category."""
    try:
        tx = Scope3TransactionInput(
            supplier_name=request.supplier_name,
            spend_amount=request.spend_amount,
            currency=request.currency,
            sic_code=request.sic_code,
            description=request.description,
            transaction_type=request.transaction_type,
        )
        return carbon_accounting_ai_engine.classify_scope3_category(tx)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/dqs-derivation",
    summary="ML-Based DQS Score Derivation",
    description=(
        "Derive PCAF Data Quality Score (DQS 1-5) from metadata features: "
        "data source, verification status, measurement approach, coverage %, and recency. "
        "Returns DQS, composite quality index, dimension breakdown, and improvement pathway."
    ),
)
def dqs_derivation(request: DQSMetadataRequest) -> Dict[str, Any]:
    """Weighted 5-feature DQS derivation engine."""
    try:
        metadata = {
            "data_source": request.data_source,
            "verification_status": request.verification_status,
            "measurement_approach": request.measurement_approach,
            "coverage_pct": request.coverage_pct,
            "recency_yrs": request.recency_yrs,
        }
        return carbon_accounting_ai_engine.derive_dqs_score(metadata)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/xbrl-tagging",
    summary="XBRL Auto-Tagging of GHG Disclosures",
    description=(
        "Map GHG disclosure fields to ESRS XBRL taxonomy concepts (ESRS 2023 digital taxonomy). "
        "Tags 45+ GHG-related XBRL concepts. Returns tagged concepts with confidence, "
        "mandatory coverage %, and untagged mandatory fields."
    ),
)
def xbrl_tagging(request: GHGDisclosureRequest) -> Dict[str, Any]:
    """Auto-tag GHG disclosure fields to ESRS XBRL concepts."""
    try:
        d = GHGDisclosureInput(
            entity_name=request.entity_name,
            reporting_year=request.reporting_year,
            scope1_tco2e=request.scope1_tco2e,
            scope2_location_tco2e=request.scope2_location_tco2e,
            scope2_market_tco2e=request.scope2_market_tco2e,
            scope3_categories=request.scope3_categories,
            base_year=request.base_year,
            consolidation_approach=request.consolidation_approach,
            boundary_description=request.boundary_description,
            verification_status=request.verification_status,
            biogenic_emissions_tco2e=request.biogenic_emissions_tco2e,
            uncertainty_pct=request.uncertainty_pct,
            ghg_reduction_target_pct=request.ghg_reduction_target_pct,
            target_year=request.target_year,
            sbti_status=request.sbti_status,
            energy_mwh=request.energy_mwh,
            renewable_energy_pct=request.renewable_energy_pct,
        )
        return carbon_accounting_ai_engine.auto_tag_xbrl(d)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/cdp-scoring",
    summary="CDP Response Quality Scoring",
    description=(
        "Score CDP Climate questionnaire C1-C12 responses for A-list gap analysis. "
        "Each section scored on completeness, quality, and evidence. "
        "Returns overall CDP band (A/B/C/D), section scores, gaps, and priority improvements."
    ),
)
def cdp_scoring(request: CDPScoringRequest) -> Dict[str, Any]:
    """CDP Climate questionnaire response scoring and A-list gap analysis."""
    try:
        return carbon_accounting_ai_engine.score_cdp_response({"responses": request.responses})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/data-gaps",
    summary="Data Gap Intelligence Analysis",
    description=(
        "Identify missing GHG data fields, recommend proxy methodologies, "
        "estimate DQS improvement potential, and calculate materiality-weighted gap score. "
        "Returns gap list, readiness %, quick wins, and effort estimate."
    ),
)
def data_gaps(request: GHGDisclosureRequest) -> Dict[str, Any]:
    """Identify missing GHG data fields and recommend remediation pathways."""
    try:
        d = GHGDisclosureInput(
            entity_name=request.entity_name,
            reporting_year=request.reporting_year,
            scope1_tco2e=request.scope1_tco2e,
            scope2_location_tco2e=request.scope2_location_tco2e,
            scope2_market_tco2e=request.scope2_market_tco2e,
            scope3_categories=request.scope3_categories,
            base_year=request.base_year,
            consolidation_approach=request.consolidation_approach,
            boundary_description=request.boundary_description,
            verification_status=request.verification_status,
            biogenic_emissions_tco2e=request.biogenic_emissions_tco2e,
            uncertainty_pct=request.uncertainty_pct,
            ghg_reduction_target_pct=request.ghg_reduction_target_pct,
            target_year=request.target_year,
            sbti_status=request.sbti_status,
            industry_sector=request.industry_sector,
        )
        return carbon_accounting_ai_engine.analyse_data_gaps(d)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Reference endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/ef-databases",
    summary="Emission Factor Database Registry",
    description=(
        "List all supported emission factor databases: IPCC AR6, US EPA eGRID 2022, "
        "DEFRA 2023, ecoinvent 3.9, IEA WEO 2023. Includes coverage, version, and DQS tier."
    ),
)
def ref_ef_databases() -> Dict[str, Any]:
    """Return emission factor database registry with metadata."""
    return {
        "databases": EMISSION_FACTOR_DATABASES,
        "total_databases": len(EMISSION_FACTOR_DATABASES),
        "total_activity_categories": len(EMISSION_FACTOR_LOOKUP),
        "note": "DQS tier 1 = highest quality; tier 5 = estimate/proxy",
    }


@router.get(
    "/ref/scope3-classification-rules",
    summary="Scope 3 Auto-Classification Rules",
    description=(
        "Return the full Scope 3 category classification rule set: "
        "15 GHG Protocol categories with keywords, SIC code ranges, "
        "default calculation methods, and FLAG/non-FLAG flags."
    ),
)
def ref_scope3_classification_rules() -> Dict[str, Any]:
    """Return Scope 3 auto-classification rule registry."""
    return {
        "categories": SCOPE3_CLASSIFICATION_RULES,
        "total_categories": len(SCOPE3_CLASSIFICATION_RULES),
        "reference": "GHG Protocol Corporate Value Chain (Scope 3) Accounting and Reporting Standard (2011)",
        "flag_note": "FLAG = Forest, Land, and Agriculture emissions per GHG Protocol FLAG Guidance (2022)",
    }


@router.get(
    "/ref/xbrl-concepts",
    summary="ESRS XBRL Concept List",
    description=(
        "Return the full list of 45 GHG-related XBRL concepts from the ESRS 2023 "
        "digital taxonomy. Includes datatype, unit, mandatory flag, and ESRS reference."
    ),
)
def ref_xbrl_concepts() -> Dict[str, Any]:
    """Return ESRS XBRL GHG concept registry."""
    mandatory = {k: v for k, v in XBRL_ESRS_CONCEPTS.items() if v["mandatory"]}
    optional = {k: v for k, v in XBRL_ESRS_CONCEPTS.items() if not v["mandatory"]}
    return {
        "total_concepts": len(XBRL_ESRS_CONCEPTS),
        "mandatory_count": len(mandatory),
        "optional_count": len(optional),
        "mandatory_concepts": mandatory,
        "optional_concepts": optional,
        "taxonomy_reference": "ESRS XBRL Digital Taxonomy 2023 (EFRAG)",
        "format": "iXBRL inline XBRL",
    }


@router.get(
    "/ref/cdp-questionnaire",
    summary="CDP Questionnaire Structure Reference",
    description=(
        "Return the full CDP Climate Questionnaire structure (C0-C12): "
        "sections, question IDs, scoring weights, mandatory flags, and scoring criteria."
    ),
)
def ref_cdp_questionnaire() -> Dict[str, Any]:
    """Return CDP Climate questionnaire structure and scoring weights."""
    return {
        "questionnaire": CDP_QUESTIONNAIRE_STRUCTURE,
        "total_sections": len(CDP_QUESTIONNAIRE_STRUCTURE),
        "scoring_reference": "CDP Climate Change Questionnaire 2024 Technical Note on Scoring",
        "a_list_threshold_pct": 90.0,
        "bands": {
            "A": ">=90%",
            "A-": "75-89%",
            "B": "60-74%",
            "B-": "45-59%",
            "C": "30-44%",
            "D": "15-29%",
            "D-": "<15%",
        },
    }
