"""
SFDR Article 9 Impact Fund Assessment — E95 Routes
====================================================
Prefix: /api/v1/sfdr-art9
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from services.sfdr_art9_engine import (
    Art9AssessmentRequest,
    PortfolioHoldingsRequest,
    PAIAggregateRequest,
    DNSHRequest,
    assess_art9_eligibility,
    analyse_portfolio_holdings,
    calculate_pai_aggregate,
    check_dnsh,
    PAI_MANDATORY,
    PAI_OPTIONAL,
    DNSH_OBJECTIVES,
    ART9_REQUIREMENTS,
    ESMA_QA_2023,
)

router = APIRouter(prefix="/api/v1/sfdr-art9", tags=["SFDR Art 9 — E95"])


# ── POST /assess ─────────────────────────────────────────────────────────────

@router.post("/assess", summary="Full SFDR Article 9 fund eligibility assessment")
def assess_art9(req: Art9AssessmentRequest) -> dict[str, Any]:
    """
    Performs a comprehensive SFDR Article 9 fund eligibility assessment:
    - RTS 2022/1288 Annex I/II pre-contractual template completeness scoring
    - Sustainable investment % calculation vs 100% Art 9 threshold (SFDR Art 2(17))
    - EU Taxonomy alignment % disclosure
    - DNSH verification across all 6 environmental objectives
    - 14 mandatory PAI indicator aggregation (Annex I Table 1)
    - Good governance screen (UNGC violations, controversial weapons)
    - VCMI additionality claim level assessment
    - ESMA SFDR Q&A 2023 compliance check
    - Downgrade risk scoring with specific trigger identification
    - Impact KPI framework (IRIS+/GII aligned)
    - Overall Art 9 eligibility score (0-100) and compliance tier
    """
    valid_strategies = ["impact", "thematic", "best_in_class", "engagement"]
    if req.fund_strategy not in valid_strategies:
        raise HTTPException(
            status_code=422,
            detail=f"fund_strategy must be one of {valid_strategies}",
        )
    valid_additionality = ["real", "likely", "plausible", "none"]
    if req.additionality_claim not in valid_additionality:
        raise HTTPException(
            status_code=422,
            detail=f"additionality_claim must be one of {valid_additionality}",
        )
    try:
        return assess_art9_eligibility(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── POST /portfolio-holdings ─────────────────────────────────────────────────

@router.post("/portfolio-holdings", summary="Analyse portfolio holdings for Art 9 sustainable investment classification")
def portfolio_holdings(req: PortfolioHoldingsRequest) -> dict[str, Any]:
    """
    Analyses each portfolio holding against SFDR Art 2(17) sustainable investment criteria:
    - Three-part test: (1) contribution to E/S objective, (2) DNSH all 6 objectives, (3) good governance
    - Holding-level DNSH objective breakdown
    - Governance screen: UNGC violations, controversial weapons, governance_screen_pass flag
    - Portfolio-level sustainable investment % vs 100% Art 9 threshold
    - EU Taxonomy alignment weighted portfolio %
    - Compliance flags per holding (UNGC_VIOLATION, CONTROVERSIAL_WEAPONS, DNSH_FAIL)

    Per ESMA Q&A 2023 Q12: cash and derivatives excluded from denominator.
    Per ESMA Q&A 2023 Q18: UNGC violations = presumptive governance screen failure.
    """
    if req.total_aum_eur_m <= 0:
        raise HTTPException(status_code=422, detail="total_aum_eur_m must be > 0")
    try:
        return analyse_portfolio_holdings(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── POST /pai-aggregate ──────────────────────────────────────────────────────

@router.post("/pai-aggregate", summary="Aggregate 14 mandatory PAI indicators across portfolio")
def pai_aggregate(req: PAIAggregateRequest) -> dict[str, Any]:
    """
    Aggregates all 14 mandatory PAI indicators (SFDR RTS 2022/1288 Annex I Table 1) across
    portfolio holdings using weighted-average methodology:

    - PAI 1-3: GHG emissions, carbon footprint, GHG intensity (tCO2e / €M metrics)
    - PAI 4-6: Fossil fuel exposure, non-renewable energy, energy intensity by sector
    - PAI 7-9: Biodiversity-sensitive areas, water emissions, hazardous waste
    - PAI 10-11: UNGC/OECD violations and compliance processes
    - PAI 12-13: Gender pay gap, board gender diversity
    - PAI 14: Controversial weapons exposure

    Data quality scored per PCAF DQS 1-5; proxy data acceptability per RTS Annex I.
    Optional PAI (OPT 1-4) available when include_optional_pai=true.
    """
    if req.total_aum_eur_m <= 0:
        raise HTTPException(status_code=422, detail="total_aum_eur_m must be > 0")
    try:
        return calculate_pai_aggregate(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── POST /dnsh ───────────────────────────────────────────────────────────────

@router.post("/dnsh-check", summary="DNSH verification across all 6 EU Taxonomy objectives")
def dnsh_check(req: DNSHRequest) -> dict[str, Any]:
    """
    Verifies Do No Significant Harm (DNSH) compliance per EU Taxonomy Art 17 for each
    holding across all 6 environmental objectives:

    1. Climate Change Mitigation (EU Taxonomy Delegated Act 2021/4987)
    2. Climate Change Adaptation
    3. Sustainable Use and Protection of Water and Marine Resources
    4. Transition to a Circular Economy
    5. Pollution Prevention and Control
    6. Protection and Restoration of Biodiversity and Ecosystems

    Assessment approaches: investee_level / country_level (per ESMA Q21) / proxy.
    Returns portfolio-level pass/fail summary + per-holding detail.
    """
    valid_approaches = ["investee_level", "country_level", "proxy"]
    if req.assessment_approach not in valid_approaches:
        raise HTTPException(
            status_code=422,
            detail=f"assessment_approach must be one of {valid_approaches}",
        )
    try:
        return check_dnsh(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── GET /ref/pai-indicators ──────────────────────────────────────────────────

@router.get("/ref/pai-indicators", summary="14 mandatory + 4 optional PAI indicator definitions (RTS Annex I)")
def ref_pai_indicators() -> dict[str, Any]:
    """
    Returns the complete PAI indicator reference data from SFDR RTS 2022/1288 Annex I Table 1:
    - 14 mandatory PAI indicators with metrics, units, calculation methodology
    - 4 optional PAI indicators
    - PCAF DQS data quality benchmarks per indicator
    - ESRS cross-reference links
    Source: Commission Delegated Regulation (EU) 2022/1288, Annex I.
    """
    return {
        "regulation": "SFDR Commission Delegated Regulation (EU) 2022/1288 — Annex I Table 1",
        "reporting_frequency": "Annual (reference period 1 Jan – 31 Dec; published by 30 June)",
        "entity_level_pai_threshold": "Financial market participants with >500 employees subject to mandatory entity-level PAI",
        "mandatory_pai_count": len(PAI_MANDATORY),
        "optional_pai_count": len(PAI_OPTIONAL),
        "mandatory_pai": PAI_MANDATORY,
        "optional_pai": PAI_OPTIONAL,
        "data_quality_note": (
            "PCAF DQS 1 = reported data (highest quality); DQS 5 = sector proxy (lowest quality). "
            "PAI_1, 2, 4, 10, 14 require reported or verified data (DQS ≤ 2)."
        ),
    }


# ── GET /ref/dnsh-criteria ───────────────────────────────────────────────────

@router.get("/ref/dnsh-criteria", summary="DNSH screening criteria for all 6 EU Taxonomy environmental objectives")
def ref_dnsh_criteria() -> dict[str, Any]:
    """
    Returns DNSH screening criteria for all 6 EU Taxonomy environmental objectives per
    EU Taxonomy Regulation (EU) 2020/852 Article 17 and Delegated Acts:
    - Key requirements per objective
    - Screening criteria methodology
    - Worst-case exclusions that automatically fail DNSH
    Source: EU Taxonomy Delegated Regulation 2021/4987 + Climate Delegated Act 2023/2486.
    """
    return {
        "regulation": "EU Taxonomy Regulation (EU) 2020/852 Art 17",
        "delegated_acts": [
            "Commission Delegated Regulation (EU) 2021/4987 (Climate + Environment)",
            "Commission Delegated Regulation (EU) 2023/2486 (Environment — DNSH update)",
        ],
        "dnsh_principle": (
            "An economic activity does no significant harm to an environmental objective if it does not "
            "significantly impede the achievement of one or more of the six environmental objectives "
            "set out in Article 9 of the EU Taxonomy Regulation."
        ),
        "objectives": DNSH_OBJECTIVES,
        "sfdr_linkage": (
            "All 'sustainable investments' per SFDR Art 2(17) must pass DNSH across all 6 objectives. "
            "Failure of any single objective disqualifies the investment from sustainable investment status."
        ),
    }


# ── GET /ref/art9-requirements ───────────────────────────────────────────────

@router.get("/ref/art9-requirements", summary="SFDR Art 9 eligibility requirements checklist")
def ref_art9_requirements() -> dict[str, Any]:
    """
    Returns the complete SFDR Article 9 eligibility requirements checklist:
    - Hard rules (mandatory conditions for Art 9 designation)
    - Best practice requirements (ESMA guidance)
    - Regulatory references per requirement
    - ESMA Q&A 2023 clarifications per requirement
    Source: SFDR Regulation (EU) 2019/2088 Art 9 + RTS 2022/1288.
    """
    return {
        "regulation": "SFDR Regulation (EU) 2019/2088 Article 9",
        "level_2_rts": "Commission Delegated Regulation (EU) 2022/1288",
        "effective_date": "10 March 2021 (SFDR); 1 January 2023 (RTS Level 2)",
        "key_distinction": (
            "Art 9 ('dark green') funds have sustainable investment as their OBJECTIVE — "
            "they 'have' sustainability as an objective, not merely 'promote' characteristics "
            "(as under Art 8). The 100% sustainable investment threshold is derived from ESMA guidance."
        ),
        "requirements": ART9_REQUIREMENTS,
        "compliance_tiers": {
            "exemplary": "Score ≥90, all hard rules met, downgrade risk <10%",
            "compliant": "Score ≥70, all hard rules met",
            "partial": "Score ≥50, some hard rules borderline",
            "non_compliant": "Core hard rules not met — reclassification recommended",
        },
    }


# ── GET /ref/esma-qa-2023 ────────────────────────────────────────────────────

@router.get("/ref/esma-qa-2023", summary="ESMA SFDR Q&A 2023 key clarifications")
def ref_esma_qa_2023() -> dict[str, Any]:
    """
    Returns key ESMA SFDR Q&A 2023 clarifications relevant to Art 9 funds:
    - Cash and derivative treatment (Q12, Q14)
    - Governance screen minimum requirements (Q18)
    - Sovereign bond DNSH approach (Q21)
    - Downgrade procedures and NCА notification (Q25)
    - EU Taxonomy vs SFDR sustainable investment distinction (Q29)
    - Additionality and impact claim requirements (Q33)
    Source: ESMA SFDR Q&A — ESMA34-45-1272 (updated 2023).
    """
    return {
        "document": "ESMA Questions and Answers on the Application of the SFDR",
        "reference": "ESMA34-45-1272",
        "last_updated": "2023",
        "applicable_to": "All financial market participants and financial advisers under SFDR",
        "key_qa_items": ESMA_QA_2023,
        "regulatory_status": (
            "ESMA Q&A are not legally binding but represent supervisory expectations. "
            "NCAs are expected to apply these interpretations in supervisory practice."
        ),
        "greenwashing_risk_note": (
            "ESMA has indicated Art 9 funds claiming impact without demonstrable sustainable "
            "investment qualification are subject to scrutiny under ESMA Anti-Greenwashing "
            "Guidelines (ESMA/2023/1047). Downgrade from Art 9 to Art 8 triggers MiFID II "
            "suitability reassessment obligations for distributors."
        ),
    }
