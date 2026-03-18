"""
API Routes: SFDR Annex Disclosure Template Engine (E9)
=======================================================
POST /api/v1/sfdr-annex/generate/annex-i        — PAI Statement (Art 4 — entity-level website)
POST /api/v1/sfdr-annex/generate/annex-ii       — Art 8 Pre-contractual disclosure (prospectus)
POST /api/v1/sfdr-annex/generate/annex-iii      — Art 8 Periodic report template
POST /api/v1/sfdr-annex/generate/annex-iv       — Art 9 Pre-contractual disclosure
POST /api/v1/sfdr-annex/generate/annex-v        — Art 9 Periodic report template
POST /api/v1/sfdr-annex/validate                — Validate disclosure completeness
GET  /api/v1/sfdr-annex/ref/pai-indicators      — PAI indicator registry (mandatory + optional)
GET  /api/v1/sfdr-annex/ref/template-fields     — Mandatory/optional fields per annex
GET  /api/v1/sfdr-annex/ref/frameworks          — SFDR RTS cross-reference
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.sfdr_annex_engine import (
    SFDRannexEngine,
    FundDisclosureInput,
    PAIIndicatorValue,
    PAI_INDICATOR_REGISTRY,
    ANNEX_I_MANDATORY_FIELDS, ANNEX_I_OPTIONAL_FIELDS,
    ANNEX_II_MANDATORY_FIELDS, ANNEX_II_OPTIONAL_FIELDS,
    ANNEX_III_MANDATORY_FIELDS, ANNEX_III_OPTIONAL_FIELDS,
    ANNEX_IV_MANDATORY_FIELDS, ANNEX_IV_OPTIONAL_FIELDS,
    ANNEX_V_MANDATORY_FIELDS, ANNEX_V_OPTIONAL_FIELDS,
)

router = APIRouter(prefix="/api/v1/sfdr-annex", tags=["SFDR Annex Disclosures"])

_ENGINE = SFDRannexEngine()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class PAIIndicatorModel(BaseModel):
    indicator_id: str = Field(..., description="'1' to '18' per RTS Annex I Table 1/2/3")
    value: Optional[float] = None
    unit: str = ""
    reference_period: str = ""
    coverage_pct: float = Field(0.0, ge=0, le=100)
    data_source: str = ""
    data_quality_score: int = Field(3, ge=1, le=5, description="PCAF DQS 1 (best) to 5 (worst)")
    actions_taken: str = ""
    target_value: Optional[float] = None
    target_date: str = ""


class FundDisclosureInputModel(BaseModel):
    fund_id: str
    fund_name: str
    legal_entity_identifier: str = ""
    isin: str = ""
    sfdr_classification: str = Field(
        "art8",
        description="art6 | art8 | art8plus | art9",
    )
    fund_manager: str = ""
    jurisdiction: str = "EU"

    # Reference period
    reference_period_start: str = ""
    reference_period_end: str = ""
    report_date: str = ""

    # Financials
    total_aum_eur: float = Field(0.0, ge=0)

    # Sustainability commitments
    proportion_sustainable_investments_pct: float = Field(0.0, ge=0, le=100)
    proportion_taxonomy_aligned_pct: float = Field(0.0, ge=0, le=100)
    sustainable_investment_min_pct: float = Field(0.0, ge=0, le=100, description="Art 9 only")
    taxonomy_aligned_min_pct: float = Field(0.0, ge=0, le=100)

    # ESG characteristics
    environmental_characteristics: List[str] = Field(default_factory=list)
    social_characteristics: List[str] = Field(default_factory=list)
    taxonomy_objectives: List[str] = Field(
        default_factory=list,
        description="e.g. ['CCM','CCA','WTR','CE','PPE','BIO']",
    )

    # Strategy and policy
    investment_strategy_description: str = ""
    engagement_policy: str = ""
    good_governance_assessment_methodology: str = ""
    dnsh_methodology: str = ""

    # Data
    data_sources: List[str] = Field(default_factory=list)
    data_limitations: str = ""
    due_diligence_description: str = ""
    investment_universe: str = ""

    # Asset allocation %
    pct_sustainable_environmental: float = Field(0.0, ge=0, le=100)
    pct_sustainable_social: float = Field(0.0, ge=0, le=100)
    pct_taxonomy_aligned_environmental: float = Field(0.0, ge=0, le=100)
    pct_other_investments: float = Field(100.0, ge=0, le=100)

    # PAI indicators
    pai_indicators: List[PAIIndicatorModel] = Field(default_factory=list)

    # Top investments (for periodic reports)
    top_investments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {name, isin, weight_pct, sector, country}",
    )

    # Reference benchmark
    reference_benchmark_name: str = ""
    reference_benchmark_isin: str = ""
    reference_benchmark_explanation: str = ""

    # Art 9 only
    sustainable_investment_objective: str = ""

    # Entity-level (Annex I PAI Statement)
    entity_name: str = ""
    total_investments_covered_eur: float = Field(0.0, ge=0)
    historical_pai_data: List[Dict[str, Any]] = Field(default_factory=list)


class GenerateAnnexRequest(BaseModel):
    fund: FundDisclosureInputModel
    report_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class ValidateRequest(BaseModel):
    fund: FundDisclosureInputModel
    annex_id: str = Field(
        ...,
        description="Annex to validate: I | II | III | IV | V",
    )


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def _section_to_dict(s) -> Dict[str, Any]:
    return {
        "section_id": s.section_id,
        "section_title": s.section_title,
        "mandatory": s.is_mandatory,
        "populated": s.is_populated,
        "content": s.content,
        "missing_fields": s.missing_fields,
        "compliance_notes": s.compliance_notes,
    }


def _result_to_dict(r) -> Dict[str, Any]:
    return {
        "run_id": r.run_id,
        "annex_id": r.annex_id,
        "annex_title": r.annex_title,
        "fund_id": r.fund_id,
        "fund_name": r.fund_name,
        "sfdr_classification": r.sfdr_classification,
        "report_date": r.report_date,
        "completeness": {
            "completeness_pct": r.completeness_pct,
            "compliance_status": r.compliance_status,
            "mandatory_fields_populated": r.mandatory_fields_populated,
            "mandatory_fields_total": r.mandatory_fields_total,
            "optional_fields_populated": r.optional_fields_populated,
            "optional_fields_total": r.optional_fields_total,
        },
        "sections": [_section_to_dict(s) for s in r.sections],
        "pai_coverage": r.pai_coverage,
        "gaps": r.gaps,
        "priority_actions": r.priority_actions,
        "metadata": r.metadata,
    }


def _to_pai_domain(m: PAIIndicatorModel) -> PAIIndicatorValue:
    return PAIIndicatorValue(**m.model_dump())


def _to_domain(m: FundDisclosureInputModel) -> FundDisclosureInput:
    d = m.model_dump()
    d["pai_indicators"] = [PAIIndicatorValue(**p) for p in d["pai_indicators"]]
    return FundDisclosureInput(**d)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/generate/annex-i",
    summary="Generate Annex I — PAI Statement (Art 4 SFDR entity-level)",
    description=(
        "Generates the structured PAI Statement template per Annex I of RTS 2022/1288. "
        "Covers 14 mandatory indicators (Table 1), additional climate/social indicators "
        "(Tables 2/3), engagement and historical comparison sections. "
        "Published on the firm's website annually per Art 4(1)(a) SFDR."
    ),
)
def generate_annex_i(req: GenerateAnnexRequest):
    result = _ENGINE.generate_annex_i(_to_domain(req.fund), req.report_date)
    return _result_to_dict(result)


@router.post(
    "/generate/annex-ii",
    summary="Generate Annex II — Art 8 Pre-contractual Disclosure",
    description=(
        "Generates the Art 8 pre-contractual disclosure template per Annex II of RTS 2022/1288. "
        "Inserted into fund prospectus / KID. Covers DNSH, ESG characteristics, investment strategy, "
        "asset allocation proportionality, monitoring, methodologies, and data limitations."
    ),
)
def generate_annex_ii(req: GenerateAnnexRequest):
    result = _ENGINE.generate_annex_ii(_to_domain(req.fund), req.report_date)
    return _result_to_dict(result)


@router.post(
    "/generate/annex-iii",
    summary="Generate Annex III — Art 8 Periodic Disclosure Report",
    description=(
        "Generates the Art 8 periodic disclosure template per Annex III of RTS 2022/1288. "
        "Published post-period alongside the fund annual report. Covers ESG attainment, "
        "top investments table, asset allocation breakdown, PAI summary, and data sources."
    ),
)
def generate_annex_iii(req: GenerateAnnexRequest):
    result = _ENGINE.generate_annex_iii(_to_domain(req.fund), req.report_date)
    return _result_to_dict(result)


@router.post(
    "/generate/annex-iv",
    summary="Generate Annex IV — Art 9 Pre-contractual Disclosure",
    description=(
        "Generates the Art 9 pre-contractual disclosure template per Annex IV of RTS 2022/1288. "
        "Includes all Art 8 sections plus sustainable investment objective, binding DNSH criteria, "
        "taxonomy minimum commitments, and good governance assessment methodology. "
        "Required in fund prospectus / KID for sustainable investment objective funds."
    ),
)
def generate_annex_iv(req: GenerateAnnexRequest):
    result = _ENGINE.generate_annex_iv(_to_domain(req.fund), req.report_date)
    return _result_to_dict(result)


@router.post(
    "/generate/annex-v",
    summary="Generate Annex V — Art 9 Periodic Disclosure Report",
    description=(
        "Generates the Art 9 periodic disclosure template per Annex V of RTS 2022/1288. "
        "Includes Art 8 periodic sections plus sustainable investment results, "
        "DNSH compliance confirmation, good governance confirmation, and "
        "reference benchmark comparison."
    ),
)
def generate_annex_v(req: GenerateAnnexRequest):
    result = _ENGINE.generate_annex_v(_to_domain(req.fund), req.report_date)
    return _result_to_dict(result)


@router.post(
    "/validate",
    summary="Validate SFDR disclosure completeness",
    description=(
        "Validates completeness and RTS compliance of a fund's disclosure data "
        "for a specified annex (I–V) without generating the full template output. "
        "Returns field-level validation with mandatory/optional gaps and priority actions."
    ),
)
def validate_disclosure(req: ValidateRequest):
    return _ENGINE.validate_disclosure(_to_domain(req.fund), req.annex_id)


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/ref/pai-indicators",
    summary="PAI indicator registry — mandatory and optional indicators per RTS Annex I",
)
def ref_pai_indicators():
    mandatory = {k: v for k, v in PAI_INDICATOR_REGISTRY.items() if v["mandatory"]}
    optional = {k: v for k, v in PAI_INDICATOR_REGISTRY.items() if not v["mandatory"]}
    return {
        "mandatory_count": len(mandatory),
        "optional_count": len(optional),
        "mandatory_indicators": [
            {"indicator_id": k, **v} for k, v in mandatory.items()
        ],
        "optional_indicators": [
            {"indicator_id": k, **v} for k, v in optional.items()
        ],
        "reference": (
            "RTS (EU) 2022/1288 Annex I — Table 1 (mandatory), "
            "Table 2 (additional climate), Table 3 (additional social)"
        ),
    }


@router.get(
    "/ref/template-fields",
    summary="Mandatory and optional template fields per SFDR annex",
)
def ref_template_fields():
    return {
        "annex_I": {
            "title": "PAI Statement (Art 4 entity-level)",
            "mandatory_fields": ANNEX_I_MANDATORY_FIELDS,
            "optional_fields": ANNEX_I_OPTIONAL_FIELDS,
        },
        "annex_II": {
            "title": "Art 8 Pre-contractual Disclosure",
            "mandatory_fields": ANNEX_II_MANDATORY_FIELDS,
            "optional_fields": ANNEX_II_OPTIONAL_FIELDS,
        },
        "annex_III": {
            "title": "Art 8 Periodic Disclosure Report",
            "mandatory_fields": ANNEX_III_MANDATORY_FIELDS,
            "optional_fields": ANNEX_III_OPTIONAL_FIELDS,
        },
        "annex_IV": {
            "title": "Art 9 Pre-contractual Disclosure",
            "mandatory_fields": ANNEX_IV_MANDATORY_FIELDS,
            "optional_fields": ANNEX_IV_OPTIONAL_FIELDS,
        },
        "annex_V": {
            "title": "Art 9 Periodic Disclosure Report",
            "mandatory_fields": ANNEX_V_MANDATORY_FIELDS,
            "optional_fields": ANNEX_V_OPTIONAL_FIELDS,
        },
        "reference": "RTS (EU) 2022/1288 Annexes I–V",
    }


@router.get(
    "/ref/frameworks",
    summary="SFDR regulatory framework cross-reference",
)
def ref_frameworks():
    return {
        "frameworks": {
            "SFDR_Level1": {
                "title": "SFDR — Sustainable Finance Disclosure Regulation",
                "regulation": "EU Regulation 2019/2088",
                "key_articles": {
                    "Art_3": "Transparency of sustainability risk policies",
                    "Art_4": "Transparency of adverse sustainability impacts — PAI Statement",
                    "Art_6": "Sustainability risk integration in pre-contractual disclosures",
                    "Art_8": "Environmental/social characteristic promotion",
                    "Art_9": "Sustainable investment objective",
                    "Art_10": "Website disclosures — Annex I",
                    "Art_11": "Periodic reports — Annex III (Art 8) / Annex V (Art 9)",
                },
            },
            "SFDR_RTS_Level2": {
                "title": "SFDR Delegated Regulation (RTS)",
                "regulation": "EU Delegated Regulation 2022/1288",
                "annexes": {
                    "Annex_I": "PAI Statement template — Art 4 entity-level website",
                    "Annex_II": "Art 8 pre-contractual disclosure template",
                    "Annex_III": "Art 8 periodic report template",
                    "Annex_IV": "Art 9 pre-contractual disclosure template",
                    "Annex_V": "Art 9 periodic report template",
                },
                "effective_date": "2023-01-01",
            },
            "EU_Taxonomy": {
                "title": "EU Taxonomy Regulation",
                "regulation": "EU Regulation 2020/852",
                "sfdr_linkage": (
                    "Art 5 (Art 9 funds) and Art 6 (Art 8 funds) require disclosure "
                    "of taxonomy-aligned investment percentage in SFDR templates"
                ),
            },
            "ESMA_QA": {
                "title": "ESMA Supervisory Q&A on SFDR",
                "reference": "2023/ESMA36-43-2498 (updated)",
                "key_clarifications": [
                    "Taxonomy-aligned investments must be disclosed separately from sustainable investments",
                    "Best-effort approach permitted where Taxonomy data unavailable (Art 8)",
                    "Sovereign bonds generally excluded from Taxonomy alignment denominator",
                ],
            },
        },
        "reference": (
            "EU Regulation 2019/2088 (SFDR) | "
            "EU Delegated Regulation 2022/1288 (RTS) | "
            "EU Regulation 2020/852 (EU Taxonomy) | "
            "ESMA Q&A SFDR 2023/ESMA36-43-2498"
        ),
    }
