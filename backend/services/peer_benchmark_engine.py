"""
Peer Benchmark Engine — Climate Disclosure Gap Assessment
=====================================================================
Knowledge-based gap assessment for 12 leading financial institutions
across TCFD / ISSB S1/S2 / ESRS / PCAF / TNFD / Paris Alignment frameworks.

Scoring: 0-100 per category.  RAG: ≥75 GREEN, ≥50 AMBER, <50 RED
Data sources: Public sustainability/annual reports, CDP responses,
NZBA target-setting templates, PCAF partner disclosures — as of 2023/2024
reporting cycle.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ─── Framework categories ─────────────────────────────────────────────────────

FRAMEWORK_CATEGORIES: dict[str, dict] = {
    "tcfd_governance":   {"label": "TCFD — Governance",             "group": "TCFD",             "weight": 1.0},
    "tcfd_strategy":     {"label": "TCFD — Strategy",               "group": "TCFD",             "weight": 1.5},
    "tcfd_risk_mgmt":    {"label": "TCFD — Risk Management",        "group": "TCFD",             "weight": 1.0},
    "tcfd_metrics":      {"label": "TCFD — Metrics & Targets",      "group": "TCFD",             "weight": 1.5},
    "issb_s1":           {"label": "ISSB S1 — General",             "group": "ISSB",             "weight": 1.0},
    "issb_s2":           {"label": "ISSB S2 — Climate",             "group": "ISSB",             "weight": 1.5},
    "esrs_e1":           {"label": "ESRS E1 — Climate Change",      "group": "ESRS/CSRD",        "weight": 2.0},
    "esrs_env_other":    {"label": "ESRS E2-E5 — Other Env.",       "group": "ESRS/CSRD",        "weight": 1.0},
    "esrs_social":       {"label": "ESRS S1-S4 — Social",           "group": "ESRS/CSRD",        "weight": 1.0},
    "esrs_governance":   {"label": "ESRS G1 — Governance",          "group": "ESRS/CSRD",        "weight": 1.0},
    "double_materiality":{"label": "Double Materiality Assessment", "group": "ESRS/CSRD",        "weight": 1.5},
    "pcaf_financed":     {"label": "PCAF Financed Emissions",       "group": "Financed Emissions","weight": 2.0},
    "scope3_cat15":      {"label": "Scope 3 Category 15",           "group": "Financed Emissions","weight": 1.5},
    "paris_alignment":   {"label": "Paris Alignment — Sectors",     "group": "Net Zero",         "weight": 2.0},
    "transition_plan":   {"label": "Credible Transition Plan",      "group": "Net Zero",         "weight": 1.5},
    "physical_risk":     {"label": "Physical Risk Quantification",  "group": "Climate Risk",     "weight": 1.5},
    "scenario_analysis": {"label": "Climate Scenario Analysis",     "group": "Climate Risk",     "weight": 1.5},
    "tnfd_nature":       {"label": "TNFD Nature & Biodiversity",    "group": "Nature",           "weight": 1.0},
}

RAG_GREEN  = 75
RAG_AMBER  = 50


def score_to_rag(score: int) -> str:
    if score >= RAG_GREEN:
        return "GREEN"
    if score >= RAG_AMBER:
        return "AMBER"
    return "RED"


# ─── Institution profiles ─────────────────────────────────────────────────────

@dataclass
class InstitutionProfile:
    slug: str
    name: str
    region: str
    country: str
    institution_type: str         # "Universal Bank" | "Investment Bank" | "Commercial Bank" | "Infrastructure PE"
    assets_usd_bn: float
    listed: bool
    exchange: Optional[str]
    nzba_member: bool
    pcaf_member: bool
    tnfd_supporter: bool
    net_zero_target_year: Optional[int]
    financed_sectors_nzba: int    # out of 9 NZBA sectors reported
    report_url: Optional[str]
    mandatory_frameworks: list[str]
    voluntary_frameworks: list[str]
    scores: dict[str, int]        # category_key → 0-100
    key_strengths: list[str]
    priority_gaps: list[str]
    analyst_note: str
    portfolio_details: dict = field(default_factory=dict)  # asset-level / portfolio breakdown data


# ─── Institution data ─────────────────────────────────────────────────────────

_INSTITUTIONS: list[InstitutionProfile] = [

    InstitutionProfile(
        slug="jpmorgan", name="JPMorgan Chase", region="North America",
        country="US", institution_type="Universal Bank", assets_usd_bn=3700,
        listed=True, exchange="NYSE",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=7,
        report_url="https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/documents/jpmc-esg-report-2023.pdf",
        mandatory_frameworks=["TCFD (voluntary US)", "SEC GHG Disclosure (stayed)"],
        voluntary_frameworks=["NZBA", "PCAF", "CDP", "TNFD (pilot)", "ISSB S2 (aligned)"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 80, "tcfd_metrics": 82,
            "issb_s1": 60, "issb_s2": 62,
            "esrs_e1": 25, "esrs_env_other": 15, "esrs_social": 55, "esrs_governance": 72,
            "double_materiality": 25,
            "pcaf_financed": 62, "scope3_cat15": 60,
            "paris_alignment": 72, "transition_plan": 68,
            "physical_risk": 58, "scenario_analysis": 65,
            "tnfd_nature": 22,
        },
        key_strengths=[
            "NZBA sector targets published for 7 sectors with 2030 interim milestones",
            "PCAF-aligned financed emissions methodology with external assurance",
            "Comprehensive TCFD 4-pillar disclosure with board-level climate governance",
            "$2.5 trillion sustainable finance commitment through 2030",
            "NGFS + proprietary scenario modelling for transition and physical risk",
        ],
        priority_gaps=[
            "ESRS E1 full suite not applicable — US domicile outside CSRD scope",
            "TNFD nature disclosure at early pilot stage only (LEAP not published)",
            "Double materiality assessment not conducted (single/financial materiality focus)",
            "Physical risk quantification lacks asset-level granularity",
            "Scope 3 Cat 15 coverage limited to 7 of 9 NZBA sectors",
        ],
        analyst_note="JPMorgan is broadly the US benchmark for climate disclosure. Strong NZBA "
                     "implementation with sector-specific 2030 decarbonisation targets. Primary gaps "
                     "are CSRD/ESRS (not in scope), nature/TNFD maturity, and US regulatory uncertainty "
                     "post-SEC climate rule stay.",
    ),

    InstitutionProfile(
        slug="goldman_sachs", name="Goldman Sachs", region="North America",
        country="US", institution_type="Investment Bank", assets_usd_bn=1600,
        listed=True, exchange="NYSE",
        nzba_member=True, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=4,
        report_url="https://www.goldmansachs.com/citizenship/esg-reporting/esg-report/index.html",
        mandatory_frameworks=["TCFD (voluntary US)"],
        voluntary_frameworks=["NZBA", "CDP (A-rated)", "ISSB S2 (partial alignment)"],
        scores={
            "tcfd_governance": 80, "tcfd_strategy": 75, "tcfd_risk_mgmt": 72, "tcfd_metrics": 70,
            "issb_s1": 55, "issb_s2": 55,
            "esrs_e1": 20, "esrs_env_other": 12, "esrs_social": 50, "esrs_governance": 70,
            "double_materiality": 22,
            "pcaf_financed": 48, "scope3_cat15": 45,
            "paris_alignment": 58, "transition_plan": 55,
            "physical_risk": 52, "scenario_analysis": 60,
            "tnfd_nature": 18,
        },
        key_strengths=[
            "CDP A-rated for climate transparency — top decile globally",
            "$750 billion sustainable finance target by 2030 (announced 2019)",
            "Strong TCFD governance narrative with dedicated climate risk function",
            "NZBA membership with 4 sector net-zero pathways published",
        ],
        priority_gaps=[
            "PCAF membership and structured financed emissions reporting absent",
            "Scope 3 Cat 15 disclosure covers fewer sectors than NZBA peers",
            "Transition plan lacks granular portfolio-level decarbonisation milestones",
            "TNFD not adopted; nature risk not systematically assessed",
            "Physical risk quantification limited compared to universal bank peers",
        ],
        analyst_note="Goldman Sachs leads on sustainable finance deal flow and CDP rating but lags "
                     "universal bank peers on structured financed emissions (no PCAF) and transition "
                     "plan granularity. Investment banking orientation means smaller balance sheet "
                     "financed-emissions footprint but also less systemic disclosure pressure.",
    ),

    InstitutionProfile(
        slug="barclays", name="Barclays", region="UK",
        country="UK", institution_type="Universal Bank", assets_usd_bn=1700,
        listed=True, exchange="LSE",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=7,
        report_url="https://home.barclays/investor-relations/esg-report/",
        mandatory_frameworks=["TCFD (UK mandatory 2022)", "UK Transition Plan (2026)", "ISSB S1/S2 (UK endorsement ~2026)"],
        voluntary_frameworks=["NZBA", "PCAF (Gold Standard)", "TNFD (beta tester)", "CDP"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85, "tcfd_metrics": 85,
            "issb_s1": 72, "issb_s2": 70,
            "esrs_e1": 50, "esrs_env_other": 40, "esrs_social": 65, "esrs_governance": 78,
            "double_materiality": 48,
            "pcaf_financed": 72, "scope3_cat15": 70,
            "paris_alignment": 78, "transition_plan": 75,
            "physical_risk": 68, "scenario_analysis": 72,
            "tnfd_nature": 30,
        },
        key_strengths=[
            "UK mandatory TCFD — among the most comprehensive 4-pillar disclosures globally",
            "PCAF Gold Standard aligned financed emissions with 7 sector coverage",
            "UK Transition Plan Taskforce (TPT) framework early adopter",
            "TNFD beta tester — nature-related disclosure ahead of most UK peers",
            "NGFS scenario analysis embedded in ICAAP and stress testing",
        ],
        priority_gaps=[
            "ESRS E1 partial — UK not in CSRD scope; EU subsidiary-level disclosure developing",
            "Double materiality not yet conducted to CSRD standard (single materiality only)",
            "TNFD LEAP process at pilot stage; not published as formal annual disclosure",
            "Physical risk quantification at portfolio level remains limited by data quality",
        ],
        analyst_note="Barclays is the UK benchmark for climate transition planning. Mandatory TCFD "
                     "and the TPT framework create strong institutional disclosure. Primary gap is "
                     "CSRD/ESRS (UK out of scope) and full double materiality. TNFD maturity "
                     "developing faster than most peers.",
    ),

    InstitutionProfile(
        slug="ing", name="ING Group", region="Europe",
        country="Netherlands", institution_type="Universal Bank", assets_usd_bn=1000,
        listed=True, exchange="Euronext",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=9,
        report_url="https://www.ing.com/Sustainability/Performance-and-reporting/Annual-report.htm",
        mandatory_frameworks=["CSRD/ESRS (FY2024)", "SFDR", "TCFD", "EU Taxonomy", "EBA Pillar 3 ESG", "ISSB S2 (via CSRD)"],
        voluntary_frameworks=["NZBA", "PCAF", "Terra Approach", "TNFD (pilot 2023, formal 2024)", "CDP"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82, "tcfd_metrics": 88,
            "issb_s1": 70, "issb_s2": 72,
            "esrs_e1": 88, "esrs_env_other": 72, "esrs_social": 80, "esrs_governance": 82,
            "double_materiality": 85,
            "pcaf_financed": 85, "scope3_cat15": 82,
            "paris_alignment": 90, "transition_plan": 80,
            "physical_risk": 72, "scenario_analysis": 80,
            "tnfd_nature": 42,
        },
        key_strengths=[
            "Terra Approach — 9-sector Paris alignment tracking updated quarterly, global standard",
            "First Dutch universal bank to publish full CSRD-compliant report (FY2024)",
            "Double materiality assessment completed to ESRS standard",
            "PCAF founding member; financed emissions published across all 9 NZBA sectors",
            "TNFD formal supporter with pilot 2023 + formal 2024 nature disclosure",
            "EBA Pillar 3 ESG disclosures compliant; EU Taxonomy Article 8 KPIs published",
        ],
        priority_gaps=[
            "Physical risk asset-level quantification — portfolio breadth creates data gaps",
            "TNFD LEAP full scope; biodiversity hotspot mapping not yet at asset level",
            "Scope 3 Cat 15 for some emerging-market client segments remains estimated",
        ],
        analyst_note="ING is the global benchmark for bank sustainability disclosure. The Terra Approach "
                     "is the most advanced sector-alignment methodology in banking. Full CSRD compliance "
                     "and PCAF leadership set the bar. Primary remaining gaps are TNFD granularity "
                     "and physical risk asset-level data quality.",
    ),

    InstitutionProfile(
        slug="rabobank", name="Rabobank", region="Europe",
        country="Netherlands", institution_type="Cooperative Bank", assets_usd_bn=720,
        listed=False, exchange=None,
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=7,
        report_url="https://www.rabobank.com/en/images/2023-annual-report.pdf",
        mandatory_frameworks=["CSRD/ESRS (FY2024)", "SFDR", "TCFD", "EU Taxonomy", "EBA Pillar 3 ESG"],
        voluntary_frameworks=["NZBA", "PCAF", "CDP", "TNFD (pilot)"],
        scores={
            "tcfd_governance": 78, "tcfd_strategy": 72, "tcfd_risk_mgmt": 70, "tcfd_metrics": 75,
            "issb_s1": 58, "issb_s2": 62,
            "esrs_e1": 78, "esrs_env_other": 42, "esrs_social": 65, "esrs_governance": 68,
            "double_materiality": 72,
            "pcaf_financed": 88, "scope3_cat15": 68,
            "paris_alignment": 74, "transition_plan": 70,
            "physical_risk": 55, "scenario_analysis": 68,
            "tnfd_nature": 35,
        },
        key_strengths=[
            "Deep agricultural finance expertise — food & agri sector PCAF reporting is sector-leading",
            "NZBA member with published sector pathways for food, land use, and agri value chains",
            "PCAF founding member; financed emissions methodology externally assured",
            "CSRD-compliant ESRS E1 disclosure published in 2024 annual report",
            "Cooperative ownership model reduces short-term yield pressure on transition pace",
        ],
        priority_gaps=[
            "Physical risk quantification limited to portfolio-level — asset granularity lacking",
            "TNFD LEAP approach not fully published; nature disclosure at pilot stage",
            "Scope 3 Cat 15 agri tail-end exposures difficult to verify with DQS 1-2 data",
            "ESRS E2-E5 disclosures relatively thin compared to ESRS E1",
        ],
        analyst_note="Rabobank is the global specialist lender in food & agriculture — uniquely "
                     "positioned on nature-related risk given its sector concentration. Strong PCAF "
                     "implementation. Real CSRD annual report processed in system.",
    ),

    InstitutionProfile(
        slug="bnp_paribas", name="BNP Paribas", region="Europe",
        country="France", institution_type="Universal Bank", assets_usd_bn=2900,
        listed=True, exchange="Euronext",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=8,
        report_url="https://invest.bnpparibas/documents/bnp-paribas-2023-universal-registration-document",
        mandatory_frameworks=["CSRD/ESRS (FY2024)", "SFDR", "TCFD", "EU Taxonomy", "EBA Pillar 3 ESG"],
        voluntary_frameworks=["NZBA", "PCAF", "TNFD (pilot)", "CDP", "SBTi (approved 2025)"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 78, "tcfd_risk_mgmt": 76, "tcfd_metrics": 80,
            "issb_s1": 65, "issb_s2": 68,
            "esrs_e1": 80, "esrs_env_other": 48, "esrs_social": 72, "esrs_governance": 74,
            "double_materiality": 80,
            "pcaf_financed": 85, "scope3_cat15": 72,
            "paris_alignment": 78, "transition_plan": 74,
            "physical_risk": 62, "scenario_analysis": 72,
            "tnfd_nature": 38,
        },
        key_strengths=[
            "Largest European bank by assets; PCAF financed emissions across 8 NZBA sectors",
            "SBTi target approved 2025 — covers both absolute and intensity-based metrics",
            "Full CSRD/ESRS compliance including double materiality assessment",
            "NZBA member with sector alignment targets published; green bond issuance leader",
            "EBA Pillar 3 ESG disclosures compliant with CRR Article 449a",
        ],
        priority_gaps=[
            "TNFD nature disclosure at pilot stage — LEAP not yet published",
            "Physical risk asset-level granularity limited vs. ING benchmark",
            "Scope 3 Cat 15 for trading book exposures remains estimated",
            "SME lending financed emissions DQS quality averaging 4.2 (model-estimated)",
        ],
        analyst_note="BNP Paribas is the French CSRD benchmark for banking. Strong PCAF adoption "
                     "and SBTi approval distinguish it from US peers. Real CSRD annual report "
                     "processed in system. Gap vs. ING: TNFD maturity and physical risk granularity.",
    ),

    InstitutionProfile(
        slug="abn_amro", name="ABN AMRO", region="Europe",
        country="Netherlands", institution_type="Retail & Commercial Bank", assets_usd_bn=440,
        listed=True, exchange="Euronext",
        nzba_member=True, pcaf_member=True, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=6,
        report_url="https://www.abnamro.com/en/investors/results-and-publications/annual-reports",
        mandatory_frameworks=["CSRD/ESRS (FY2024)", "SFDR", "TCFD", "EU Taxonomy", "EBA Pillar 3 ESG"],
        voluntary_frameworks=["NZBA", "PCAF", "CDP"],
        scores={
            "tcfd_governance": 72, "tcfd_strategy": 68, "tcfd_risk_mgmt": 65, "tcfd_metrics": 70,
            "issb_s1": 52, "issb_s2": 55,
            "esrs_e1": 72, "esrs_env_other": 38, "esrs_social": 60, "esrs_governance": 62,
            "double_materiality": 68,
            "pcaf_financed": 78, "scope3_cat15": 60,
            "paris_alignment": 68, "transition_plan": 65,
            "physical_risk": 48, "scenario_analysis": 60,
            "tnfd_nature": 28,
        },
        key_strengths=[
            "Strong Dutch real estate financed emissions — mortgage book PCAF DQS 2 achieved",
            "NZBA member; PCAF reporting covers residential real estate at DQS 2 quality",
            "ESRS E1 disclosure published; double materiality completed",
            "EBA Pillar 3 ESG Article 449a compliant; EU Taxonomy KPIs disclosed",
        ],
        priority_gaps=[
            "TNFD not adopted — nature risk assessment absent from public reporting",
            "Physical risk quantification at portfolio level only — no asset granularity",
            "Transition plan credibility assessment lacking third-party validation",
            "PCAF coverage for SME/corporate segments relies heavily on DQS 4-5 estimates",
            "Scope 3 Cat 15 sectors covered: 6 of 9 — shipping and oil & gas absent",
        ],
        analyst_note="ABN AMRO scores below ING and Rabobank on most categories — smaller "
                     "balance sheet and lower resource allocation to climate data quality. "
                     "Mortgage PCAF data is a genuine strength. Real CSRD annual report processed "
                     "in system. TNFD adoption and physical risk granularity are the priority gaps.",
    ),

    InstitutionProfile(
        slug="societe_generale", name="Société Générale", region="Europe",
        country="France", institution_type="Universal Bank", assets_usd_bn=1450,
        listed=True, exchange="Euronext",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=6,
        report_url="https://www.societegenerale.com/en/measuring-our-performance/esg-data",
        mandatory_frameworks=["CSRD/ESRS (FY2024)", "SFDR", "TCFD", "EU Taxonomy", "EBA Pillar 3 ESG"],
        voluntary_frameworks=["NZBA", "PCAF", "TNFD (pilot)", "CDP"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 78, "tcfd_metrics": 80,
            "issb_s1": 68, "issb_s2": 68,
            "esrs_e1": 82, "esrs_env_other": 68, "esrs_social": 78, "esrs_governance": 80,
            "double_materiality": 80,
            "pcaf_financed": 70, "scope3_cat15": 68,
            "paris_alignment": 75, "transition_plan": 72,
            "physical_risk": 62, "scenario_analysis": 70,
            "tnfd_nature": 35,
        },
        key_strengths=[
            "Full CSRD compliance from FY2024; double materiality assessment published",
            "SFDR Article 8/9 fund classification with PAI disclosures at fund level",
            "NZBA sector targets for 6 sectors with 2025/2030 interim milestones",
            "EBA Pillar 3 ESG disclosures; EU Taxonomy Green Asset Ratio published",
            "TNFD pilot participant 2023; nature risk framework under development",
        ],
        priority_gaps=[
            "Financed emissions sector coverage (6 vs ING's 9 NZBA sectors)",
            "Physical risk quantification — less granular than UK/Netherlands peers",
            "Transition plan milestones less granular than Barclays/ING benchmark",
            "TNFD formal disclosure not yet published (pilot only)",
        ],
        analyst_note="SocGen is a strong CSRD-era reporter with comprehensive double materiality and "
                     "SFDR compliance. Lags ING on Terra-equivalent sector alignment and PCAF breadth. "
                     "French regulatory environment (NFI Decree history) gives strong governance base "
                     "for CSRD transition.",
    ),

    InstitutionProfile(
        slug="rbc", name="Royal Bank of Canada", region="North America",
        country="Canada", institution_type="Universal Bank", assets_usd_bn=1700,
        listed=True, exchange="TSX/NYSE",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=7,
        report_url="https://www.rbc.com/community-social-impact/reporting-performance/esg-report.html",
        mandatory_frameworks=["OSFI B-15 (Climate Risk Guideline, FY2024)", "TCFD (mandatory OSC 2024)", "ISSB S1/S2 (OSFI-aligned)"],
        voluntary_frameworks=["NZBA", "PCAF", "TNFD (supporter)", "CDP"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 78, "tcfd_risk_mgmt": 75, "tcfd_metrics": 75,
            "issb_s1": 75, "issb_s2": 75,
            "esrs_e1": 20, "esrs_env_other": 15, "esrs_social": 55, "esrs_governance": 72,
            "double_materiality": 22,
            "pcaf_financed": 65, "scope3_cat15": 62,
            "paris_alignment": 68, "transition_plan": 65,
            "physical_risk": 65, "scenario_analysis": 68,
            "tnfd_nature": 28,
        },
        key_strengths=[
            "OSFI B-15 compliance — Canada-specific mandatory climate risk guideline (ISSB-based)",
            "TCFD mandatory under OSC guidance; strong 4-pillar implementation",
            "NZBA sector targets for 7 sectors; $500B sustainable finance commitment",
            "PCAF financed emissions — one of first Canadian banks to publish",
            "Physical risk scenario analysis integrated into OSFI-mandated ICAAP",
        ],
        priority_gaps=[
            "ESRS/CSRD not applicable (Canadian domicile); EU subsidiary disclosure limited",
            "Double materiality not conducted (single/financial materiality framework)",
            "TNFD formal adoption announced but LEAP framework not yet published",
            "Scope 3 Cat 15 — aviation, shipping sector coverage gaps vs NZBA peers",
            "Nature risk integration into credit risk framework at early stage",
        ],
        analyst_note="RBC leads Canadian peers on OSFI B-15 compliance and ISSB-aligned disclosure. "
                     "Strong alignment with JPMorgan on NZBA and PCAF. Key differentiator vs US peers "
                     "is mandatory nature of OSFI B-15 climate requirements. CSRD/ESRS not in scope.",
    ),

    InstitutionProfile(
        slug="icici_bank", name="ICICI Bank", region="India",
        country="India", institution_type="Commercial Bank", assets_usd_bn=295,
        listed=True, exchange="NSE/BSE/NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=None, financed_sectors_nzba=0,
        report_url="https://www.icicibank.com/sustainability",
        mandatory_frameworks=["BRSR (SEBI, FY2022 mandatory)", "BRSR Core (FY2024)", "Companies Act 2013 CSR"],
        voluntary_frameworks=["TCFD (voluntary)", "CDP (partial)", "ISSB S2 (SEBI roadmap 2026)"],
        scores={
            "tcfd_governance": 55, "tcfd_strategy": 45, "tcfd_risk_mgmt": 40, "tcfd_metrics": 42,
            "issb_s1": 40, "issb_s2": 38,
            "esrs_e1": 8, "esrs_env_other": 5, "esrs_social": 50, "esrs_governance": 65,
            "double_materiality": 30,
            "pcaf_financed": 30, "scope3_cat15": 28,
            "paris_alignment": 35, "transition_plan": 30,
            "physical_risk": 35, "scenario_analysis": 35,
            "tnfd_nature": 10,
        },
        key_strengths=[
            "BRSR (Business Responsibility and Sustainability Report) — comprehensive India-specific disclosure",
            "BRSR Core (FY2024) — 49 assured KPIs including GHG intensity, water, waste",
            "Scope 1/2 emissions published with third-party assurance",
            "Governance disclosures strong via Companies Act and SEBI requirements",
            "Renewable energy target for own operations; green building portfolio",
        ],
        priority_gaps=[
            "No NZBA membership; no net-zero banking commitment with sector targets",
            "PCAF financed emissions not published — largest gap vs global peers",
            "Scope 3 Category 15 (financed emissions) absent from disclosure",
            "TCFD implementation partial — strategy/risk pillars developing",
            "Climate scenario analysis not published; physical and transition risk quantification absent",
            "TNFD / nature risk not in scope of current reporting framework",
            "ISSB S2 adoption on SEBI 2026 roadmap — 2-year implementation lag",
        ],
        analyst_note="ICICI Bank's disclosure is shaped entirely by India's BRSR framework, which "
                     "is among the most prescriptive ESG regimes in Asia for the company's own "
                     "operations. However, financed emissions (Scope 3 Cat 15) and Paris-aligned "
                     "lending targets represent a significant gap relative to global peers. "
                     "SEBI's planned ISSB S2 adoption by 2026 will require substantial capability "
                     "building in climate risk measurement.",
    ),

    InstitutionProfile(
        slug="smbc", name="Sumitomo Mitsui Banking Corp. (SMBC Group)", region="Japan",
        country="Japan", institution_type="Universal Bank", assets_usd_bn=2100,
        listed=True, exchange="TSE Prime",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=5,
        report_url="https://www.smfg.co.jp/english/sustainability/report/",
        mandatory_frameworks=["TCFD (TSE Prime mandatory FY2022)", "SSBJ S1/S2 (from FY2024, ISSB-based)", "TNFD (FSA pilot)"],
        voluntary_frameworks=["NZBA", "PCAF (Japan)", "CDP", "TNFD formal supporter"],
        scores={
            "tcfd_governance": 80, "tcfd_strategy": 72, "tcfd_risk_mgmt": 70, "tcfd_metrics": 72,
            "issb_s1": 68, "issb_s2": 65,
            "esrs_e1": 18, "esrs_env_other": 15, "esrs_social": 60, "esrs_governance": 68,
            "double_materiality": 35,
            "pcaf_financed": 58, "scope3_cat15": 55,
            "paris_alignment": 62, "transition_plan": 60,
            "physical_risk": 58, "scenario_analysis": 62,
            "tnfd_nature": 45,
        },
        key_strengths=[
            "TCFD mandatory for TSE Prime Market — comprehensive 4-pillar implementation",
            "SSBJ (ISSB-based Japanese standards) adoption from FY2024 — regulatory first-mover",
            "TNFD formal supporter with FSA-led TNFD pilot; nature disclosure ahead of most global peers",
            "NZBA member with 2050 net-zero commitment; sector targets for 5 sectors",
            "PCAF Japan participation; financed emissions published with sector breakdown",
            "Physical risk scenario analysis using RCP 2.6/4.5/8.5 pathways",
        ],
        priority_gaps=[
            "ESRS/CSRD not applicable; EU subsidiary exposure limited",
            "NZBA sector coverage (5 of 9) lags ING/Barclays on breadth",
            "Double materiality at conceptual stage — SSBJ single-materiality focus",
            "Transition plan milestones less granular than European banking peers",
            "Nature risk LEAP framework published in pilot; full asset-level not yet available",
        ],
        analyst_note="SMBC is a regional leader in Asia-Pacific climate disclosure. Japan's mandatory "
                     "TCFD and the new SSBJ/ISSB adoption framework put SMBC ahead of most APAC peers. "
                     "TNFD engagement is notable — Japan FSA is actively pushing nature risk and SMBC "
                     "is a leading voice. Main gap versus European peers is ESRS not applicable and "
                     "NZBA sector breadth.",
    ),

    InstitutionProfile(
        slug="kb_financial", name="KB Financial Group", region="Korea",
        country="South Korea", institution_type="Universal Bank", assets_usd_bn=620,
        listed=True, exchange="KRX/NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=2,
        report_url="https://www.kbfg.com/Eng/ir/irEsgReport/list.do",
        mandatory_frameworks=["FSS ESG Disclosure Guidelines (2021)", "K-IFRS Sustainability (from 2026)", "KOSHA safety reporting"],
        voluntary_frameworks=["TCFD (published since 2021)", "CDP", "MSCI ESG rated (AA)", "GRI Standards"],
        scores={
            "tcfd_governance": 68, "tcfd_strategy": 62, "tcfd_risk_mgmt": 58, "tcfd_metrics": 60,
            "issb_s1": 52, "issb_s2": 50,
            "esrs_e1": 12, "esrs_env_other": 10, "esrs_social": 52, "esrs_governance": 62,
            "double_materiality": 28,
            "pcaf_financed": 42, "scope3_cat15": 40,
            "paris_alignment": 48, "transition_plan": 45,
            "physical_risk": 45, "scenario_analysis": 48,
            "tnfd_nature": 18,
        },
        key_strengths=[
            "MSCI ESG rating AA — top-decile for Korean financial sector",
            "TCFD disclosure published since 2021; improving year-on-year",
            "Net-zero 2050 commitment with interim 2030 carbon reduction target",
            "Green finance portfolio >KRW 50 trillion; ESG loan products growing",
            "FSS ESG disclosure guidelines compliance — Korea-specific benchmark",
        ],
        priority_gaps=[
            "No NZBA membership — largest governance gap vs global peers",
            "PCAF financed emissions not published; Scope 3 Cat 15 absent",
            "K-IFRS sustainability standards (ISSB-based) not yet mandatory until 2026",
            "Climate scenario analysis at qualitative stage; quantitative risk models underdeveloped",
            "Transition plan lacks sector-by-sector decarbonisation milestones",
            "TNFD not adopted; nature risk not in current disclosure framework",
        ],
        analyst_note="KB Financial is Korea's leading ESG financial institution by AUM and MSCI rating "
                     "but its disclosure framework lags global peers due to regulatory environment. "
                     "K-IFRS sustainability standard adoption from 2026 will be a significant forcing "
                     "function. NZBA membership and PCAF adoption are the priority near-term gaps.",
    ),

    InstitutionProfile(
        slug="hsbc_hk", name="HSBC (Hong Kong)", region="Hong Kong",
        country="Hong Kong", institution_type="Universal Bank", assets_usd_bn=800,
        listed=True, exchange="HKEX/LSE",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=7,
        report_url="https://www.hsbc.com/who-we-are/our-climate-strategy",
        mandatory_frameworks=["HKEX ESG Reporting Guide (2024 ISSB-based)", "HKFRS S1/S2 (HKEX mandate from 2025)", "TCFD (HKEX mandatory 2025)"],
        voluntary_frameworks=["NZBA", "PCAF", "TNFD (supporter)", "CDP"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 78, "tcfd_metrics": 80,
            "issb_s1": 72, "issb_s2": 70,
            "esrs_e1": 30, "esrs_env_other": 25, "esrs_social": 65, "esrs_governance": 72,
            "double_materiality": 38,
            "pcaf_financed": 68, "scope3_cat15": 65,
            "paris_alignment": 72, "transition_plan": 68,
            "physical_risk": 65, "scenario_analysis": 68,
            "tnfd_nature": 32,
        },
        key_strengths=[
            "HKEX ISSB-based ESG reform (2024) — HKFRS S1/S2 mandatory from 2025 (financial sector)",
            "HSBC Group NZBA targets for 7 sectors with granular 2030 milestones",
            "PCAF-aligned financed emissions with Asia-Pacific client coverage",
            "HKEX ESG Reporting Guide compliance — comprehensive Hong Kong benchmark",
            "Strong physical risk analysis given APAC climate exposure (typhoon, flooding, heat)",
        ],
        priority_gaps=[
            "ESRS/CSRD limited scope — EU subsidiary reporting developing but HK-parent not in scope",
            "Double materiality not to CSRD standard; HKFRS S1/S2 is single-materiality",
            "TNFD LEAP formal disclosure not yet published; nature exposure in APAC significant",
            "HKFRS S1/S2 mandatory only from 2025 — some disclosures still transitional",
        ],
        analyst_note="HSBC HK benefits from HSBC Group's global disclosure infrastructure while "
                     "navigating HKEX's accelerating ISSB adoption timeline. The 2025 HKFRS S1/S2 "
                     "mandate makes HK one of the most progressive APAC jurisdictions. Key gaps are "
                     "CSRD/ESRS (not in scope) and TNFD formal disclosure for APAC nature exposure.",
    ),

    InstitutionProfile(
        slug="cathay_financial", name="Cathay Financial Holdings", region="Taiwan",
        country="Taiwan", institution_type="Universal Bank", assets_usd_bn=370,
        listed=True, exchange="TWSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.cathayholdings.com/en/ESG/sustainability_report",
        mandatory_frameworks=["FSC Sustainability Roadmap (2022)", "TCFD (FSC mandatory financial sector 2023)", "GRI Standards (mandatory listed cos)"],
        voluntary_frameworks=["ISSB S1/S2 (FSC roadmap: financial sector 2026)", "CDP (partial)", "SASB"],
        scores={
            "tcfd_governance": 65, "tcfd_strategy": 58, "tcfd_risk_mgmt": 52, "tcfd_metrics": 55,
            "issb_s1": 48, "issb_s2": 45,
            "esrs_e1": 10, "esrs_env_other": 8, "esrs_social": 48, "esrs_governance": 60,
            "double_materiality": 25,
            "pcaf_financed": 35, "scope3_cat15": 32,
            "paris_alignment": 45, "transition_plan": 40,
            "physical_risk": 40, "scenario_analysis": 42,
            "tnfd_nature": 12,
        },
        key_strengths=[
            "FSC Taiwan sustainability roadmap — most structured APAC regulatory pathway outside Japan/HK",
            "TCFD mandatory for financial sector from 2023 — early in Asia emerging markets",
            "Net-zero 2050 commitment with operational carbon reduction targets",
            "ESG-linked products: green bonds, ESG ETFs, sustainability-linked loans",
            "GRI Standards compliance — annual sustainability report since 2008",
        ],
        priority_gaps=[
            "No NZBA membership; financed emissions Scope 3 Cat 15 not published",
            "PCAF methodology not adopted; investment portfolio emissions not quantified",
            "ISSB S1/S2 adoption on FSC roadmap for 2026 — significant data build required",
            "Climate scenario analysis at qualitative stage; physical risk not quantified",
            "Double materiality assessment not conducted",
            "TNFD / nature risk: Taiwan has significant biodiversity exposure but no disclosure",
            "Paris-alignment at portfolio level: no sector-specific decarbonisation targets",
        ],
        analyst_note="Cathay Financial is among the most advanced Taiwanese financial institutions on "
                     "sustainability but the FSC regulatory timeline (ISSB 2026, TCFD 2023) means it "
                     "is still 2-3 years behind global banking standards. Financed emissions and "
                     "Paris alignment represent the most material gaps. Taiwan's semiconductor supply "
                     "chain concentration creates unique physical risk exposure not yet fully disclosed.",
    ),

    InstitutionProfile(
        slug="brookfield_renewable", name="Brookfield Renewable Partners", region="North America",
        country="Canada (Global)", institution_type="Infrastructure PE",
        assets_usd_bn=100,
        listed=True, exchange="NYSE/TSX",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://bep.brookfield.com/sustainability",
        mandatory_frameworks=["TCFD (voluntary, comprehensive)", "OSFI B-15 (Canadian subsidiary)", "SEC GHG (stayed)"],
        voluntary_frameworks=["ISSB S2 (adopted voluntarily)", "TNFD (supporter)", "CDP A-rated", "GRI Standards", "GRESB (5-star rated)"],
        scores={
            "tcfd_governance": 75, "tcfd_strategy": 80, "tcfd_risk_mgmt": 72, "tcfd_metrics": 75,
            "issb_s1": 55, "issb_s2": 62,
            "esrs_e1": 35, "esrs_env_other": 30, "esrs_social": 50, "esrs_governance": 65,
            "double_materiality": 42,
            "pcaf_financed": 75, "scope3_cat15": 72,
            "paris_alignment": 85, "transition_plan": 80,
            "physical_risk": 72, "scenario_analysis": 68,
            "tnfd_nature": 38,
        },
        key_strengths=[
            "100% renewable energy mandate — business model IS the Paris-aligned glidepath",
            "CDP Climate A-rated; GRESB 5-star — industry-leading voluntary disclosure",
            "ISSB S2 voluntarily adopted; asset-level climate risk embedded in valuations",
            "Physical risk: hydrology, wind resource, solar irradiance modelled at asset level",
            "TNFD supporter — significant biodiversity dependencies (hydro, land-based wind/solar)",
            "Net-zero business model by design; portfolio avoids >100 million tCO₂e/year",
        ],
        priority_gaps=[
            "ESRS/CSRD partial — EU-based assets covered but Canadian HoldCo not in scope",
            "Double materiality not conducted to CSRD standard (impact materiality limited)",
            "TNFD LEAP formal disclosure not yet published despite significant nature dependencies",
            "Scope 3 (supply chain) emissions from manufacturing/construction not fully quantified",
            "SFDR Article 9 classification not sought for listed entity structure",
        ],
        analyst_note="Brookfield Renewable is the global benchmark for climate-aligned infrastructure "
                     "investment. Its Paris alignment is structural (100% renewables) rather than "
                     "transitional. Key gaps are CSRD/ESRS scope, TNFD formal adoption for hydro/land "
                     "assets, and supply-chain Scope 3. GRESB 5-star and CDP A distinguish it from "
                     "private PE peers who publish minimal ESG data.",
    ),

    # ─── European Energy Transition (from processed CSRD reports) ─────────────

    InstitutionProfile(
        slug="orsted", name="Ørsted", region="Europe",
        country="Denmark", institution_type="Renewable Energy Developer",
        assets_usd_bn=32,
        listed=True, exchange="OMX Copenhagen",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://orsted.com/en/sustainability-reports",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "EU Taxonomy (Article 8)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "TNFD (supporter)", "CDP A-rated", "SBTI (1.5°C)", "Science Based Targets — Power"],
        scores={
            "tcfd_governance": 92, "tcfd_strategy": 95, "tcfd_risk_mgmt": 90, "tcfd_metrics": 92,
            "issb_s1": 85, "issb_s2": 90,
            "esrs_e1": 88, "esrs_env_other": 75, "esrs_social": 72, "esrs_governance": 80,
            "double_materiality": 85,
            "pcaf_financed": 45, "scope3_cat15": 40,
            "paris_alignment": 95, "transition_plan": 92,
            "physical_risk": 82, "scenario_analysis": 88,
            "tnfd_nature": 62,
        },
        key_strengths=[
            "Business model is 99% offshore wind — structurally Paris-aligned by design",
            "CSRD early adopter — ESRS E1 full suite with asset-level GHG quantification",
            "CDP Climate A-rated for 8 consecutive years; SBTi 1.5°C power sector target",
            "Physical risk: offshore wind resource modelled under RCP 2.6/4.5/8.5",
            "EU Taxonomy: 99% of Capex/Opex aligned (wind generation)",
        ],
        priority_gaps=[
            "PCAF financed emissions N/A as energy developer (not financier)",
            "TNFD LEAP formal disclosure pending for offshore marine biodiversity",
            "Scope 3 upstream (supply chain manufacturing) emissions growing in materiality",
            "Just Transition plan for fossil fuel communities not yet quantified",
            "Land use and biodiversity impact from onshore wind expansion",
        ],
        analyst_note="Ørsted is the global benchmark for renewable energy corporate disclosure. "
                     "Its 2023 CSRD-ready report sets the template for what ESRS E1 looks like "
                     "for a pure-play renewable developer. Primary gaps: TNFD nature (marine), "
                     "just transition quantification, and supply chain Scope 3.",
    ),

    InstitutionProfile(
        slug="rwe", name="RWE AG", region="Europe",
        country="Germany", institution_type="Integrated Utility",
        assets_usd_bn=65,
        listed=True, exchange="Frankfurt (SDAX)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.rwe.com/en/responsibility/sustainability-reports",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "EU Taxonomy (Article 8)", "German CBAM reporting"],
        voluntary_frameworks=["ISSB S2 (aligned)", "CDP B", "SBTI (submitted)", "GRI Standards", "TNFD (supporter)"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 88, "tcfd_risk_mgmt": 82, "tcfd_metrics": 85,
            "issb_s1": 75, "issb_s2": 80,
            "esrs_e1": 82, "esrs_env_other": 68, "esrs_social": 65, "esrs_governance": 72,
            "double_materiality": 78,
            "pcaf_financed": 35, "scope3_cat15": 32,
            "paris_alignment": 80, "transition_plan": 85,
            "physical_risk": 75, "scenario_analysis": 80,
            "tnfd_nature": 52,
        },
        key_strengths=[
            "Coal exit 2030 (Germany) commitment backed by contractual decommissioning schedules",
            "€55 billion green capex 2024-2030 — largest renewables investment programme in Europe",
            "CSRD-compliant reporting with double materiality assessment completed",
            "EU Taxonomy aligned Capex growing from 42% (2022) to >80% target by 2030",
            "Physical risk quantification across 400+ generation assets (wind, solar, hydro)",
        ],
        priority_gaps=[
            "Transition from coal creates stranded asset risk not fully quantified in financial statements",
            "TNFD: lignite mining creates land disturbance and water dependencies requiring LEAP",
            "Scope 3 upstream coal supply chain emissions: methodology under revision",
            "Just transition: workforce reskilling cost and social licence disclosure immature",
            "PCAF financed emissions N/A (energy producer, not lender)",
        ],
        analyst_note="RWE represents Europe's most complex energy transition story — a coal major "
                     "becoming a renewable leader by 2030. CSRD-compliant reporting is strong but the "
                     "just transition, land rehabilitation, and scope 3 coal supply chain gaps "
                     "are the most material ESG risks for fixed income investors.",
    ),

    InstitutionProfile(
        slug="engie", name="ENGIE SA", region="Europe",
        country="France", institution_type="Integrated Utility",
        assets_usd_bn=90,
        listed=True, exchange="Euronext Paris (SBF 120)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2045, financed_sectors_nzba=0,
        report_url="https://www.engie.com/en/journalists/press-releases/integrated-report",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "EU Taxonomy (Article 8)", "French DPEF"],
        voluntary_frameworks=["ISSB S2 (aligned)", "CDP A-", "SBTI (1.5°C power)", "GRI Standards", "TNFD (supporter)", "SASB Energy"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 78, "issb_s2": 82,
            "esrs_e1": 85, "esrs_env_other": 72, "esrs_social": 75, "esrs_governance": 78,
            "double_materiality": 82,
            "pcaf_financed": 38, "scope3_cat15": 35,
            "paris_alignment": 82, "transition_plan": 80,
            "physical_risk": 78, "scenario_analysis": 82,
            "tnfd_nature": 58,
        },
        key_strengths=[
            "CSRD early adopter — comprehensive ESRS E1-G1 disclosure with assurance",
            "Net zero 2045 with 2030 interim targets (gross -58% vs. 2017) — SBTi 1.5°C aligned",
            "French DPEF mandatory reporting adds social/workforce disclosure depth",
            "Physical risk: 800+ asset portfolio modelled under IEA and NGFS scenarios",
            "Green bond framework aligns 95% of EU Taxonomy-eligible capex",
        ],
        priority_gaps=[
            "Gas infrastructure stranded asset risk: €20bn+ gas network valuation uncertainty",
            "TNFD: hydropower portfolio creates significant freshwater and biodiversity dependencies",
            "Scope 3 customer gas consumption (Cat 11) largest single emissions source — methodology evolving",
            "Just transition plan for gas workers in Europe lacks quantified reskilling cost",
            "Nuclear in France: lifecycle GHG, waste, and water intensity disclosure gaps",
        ],
        analyst_note="ENGIE is the European benchmark for large integrated utility CSRD reporting. "
                     "Comprehensive ESRS E1 with board-level accountability and external assurance. "
                     "Gas infrastructure stranded assets and nuclear lifecycle disclosure are the "
                     "most material undisclosed risks for institutional fixed income and equity holders.",
    ),

    InstitutionProfile(
        slug="edp", name="EDP — Energias de Portugal", region="Europe",
        country="Portugal", institution_type="Renewable Energy Utility",
        assets_usd_bn=48,
        listed=True, exchange="Euronext Lisbon",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.edp.com/en/sustainability/reports",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "EU Taxonomy (Article 8)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "CDP A", "SBTI (1.5°C power)", "GRI Standards", "TNFD (supporter)", "GRESB Infrastructure"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 92, "tcfd_risk_mgmt": 88, "tcfd_metrics": 90,
            "issb_s1": 82, "issb_s2": 88,
            "esrs_e1": 90, "esrs_env_other": 78, "esrs_social": 72, "esrs_governance": 80,
            "double_materiality": 88,
            "pcaf_financed": 42, "scope3_cat15": 38,
            "paris_alignment": 90, "transition_plan": 88,
            "physical_risk": 85, "scenario_analysis": 88,
            "tnfd_nature": 65,
        },
        key_strengths=[
            "CDP Climate A-rated — top-tier transparency with consistent 10-year disclosure track record",
            "80% renewable generation (2023) — ahead of most European peers on grid decarbonisation",
            "CSRD: ESRS E1 full suite published with KPMG limited assurance",
            "Physical risk: drought and hydrology modelled at asset level for all Iberian hydro",
            "SBTi 1.5°C power sector target — covers 100% of own-generation emissions",
        ],
        priority_gaps=[
            "TNFD: significant freshwater dependencies from Iberian hydro require LEAP formulation",
            "Just transition: coal plant closure in Spain/Portugal — community impact not quantified",
            "Scope 3 upstream (wind turbine/solar manufacturing supply chain) growing in materiality",
            "Brazilian operations: deforestation-free supply chain verification required for ESRS E4",
            "SASB Electric Utilities sector metrics not yet fully aligned",
        ],
        analyst_note="EDP is among the top-3 renewable utilities in Europe for climate disclosure quality. "
                     "Consistent CDP A rating, SBTi aligned, and early CSRD adopter. Key gaps: TNFD "
                     "freshwater (hydro dependencies), just transition quantification for Iberian coal "
                     "closures, and Brazilian deforestation supply chain.",
    ),

    # ─── GCC Region — Banks & Energy ──────────────────────────────────────────

    InstitutionProfile(
        slug="emirates_nbd", name="Emirates NBD", region="Middle East",
        country="UAE", institution_type="Universal Bank",
        assets_usd_bn=235,
        listed=True, exchange="Dubai Financial Market (DFM)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.emiratesnbd.com/en/investor-relations/sustainability",
        mandatory_frameworks=["UAE Central Bank Sustainable Finance Framework (2023)", "CBUAE ESG Guidance"],
        voluntary_frameworks=["TCFD (adopted)", "ISSB S2 (alignment planned)", "CDP (responding)", "UNEP FI NZBA (observer)", "GRI Standards"],
        scores={
            "tcfd_governance": 65, "tcfd_strategy": 58, "tcfd_risk_mgmt": 52, "tcfd_metrics": 55,
            "issb_s1": 42, "issb_s2": 45,
            "esrs_e1": 18, "esrs_env_other": 10, "esrs_social": 45, "esrs_governance": 58,
            "double_materiality": 22,
            "pcaf_financed": 25, "scope3_cat15": 20,
            "paris_alignment": 35, "transition_plan": 30,
            "physical_risk": 42, "scenario_analysis": 38,
            "tnfd_nature": 15,
        },
        key_strengths=[
            "Largest bank in UAE by assets — leading GCC financial institution on sustainability",
            "TCFD adopted and embedded in board risk committee agenda since 2022",
            "Green/sustainable loan portfolio growing — AED 75bn sustainable finance by 2030",
            "UAE Net Zero by 2050 national target creates regulatory tailwind for disclosure",
            "Operational net zero commitment for own operations by 2030",
        ],
        priority_gaps=[
            "PCAF financed emissions methodology not adopted — financed emissions not disclosed",
            "Scope 3 Category 15 (financed emissions) absent from all disclosures",
            "ISSB S1/S2 adoption only planned — no compliant disclosure yet",
            "Climate scenario analysis: NGFS or equivalent not yet applied to loan book",
            "TNFD nature disclosure absent — UAE coastal and desert ecosystem dependencies",
            "Double materiality assessment not conducted — single (financial) materiality only",
        ],
        analyst_note="Emirates NBD is the GCC's most advanced financial institution on sustainability "
                     "disclosure, but remains significantly behind European peers. The UAE Central "
                     "Bank's 2023 Sustainable Finance Framework will drive rapid improvement. "
                     "Financed emissions (PCAF) and ISSB S2 adoption are the critical near-term gaps.",
    ),

    InstitutionProfile(
        slug="al_rajhi_bank", name="Al Rajhi Bank", region="Middle East",
        country="Saudi Arabia", institution_type="Islamic Bank",
        assets_usd_bn=185,
        listed=True, exchange="Tadawul (Saudi Exchange)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2060, financed_sectors_nzba=0,
        report_url="https://www.alrajhibank.com.sa/en/investor-relations/sustainability-reports",
        mandatory_frameworks=["Saudi Arabia Vision 2030 ESG Guidance", "CMA ESG Disclosure Guidelines (2021)"],
        voluntary_frameworks=["GRI Standards (partial)", "TCFD (alignment in progress)", "CDP (partial respondent)"],
        scores={
            "tcfd_governance": 42, "tcfd_strategy": 38, "tcfd_risk_mgmt": 35, "tcfd_metrics": 38,
            "issb_s1": 28, "issb_s2": 30,
            "esrs_e1": 10, "esrs_env_other": 8, "esrs_social": 38, "esrs_governance": 48,
            "double_materiality": 15,
            "pcaf_financed": 12, "scope3_cat15": 10,
            "paris_alignment": 20, "transition_plan": 18,
            "physical_risk": 25, "scenario_analysis": 20,
            "tnfd_nature": 10,
        },
        key_strengths=[
            "World's largest Islamic bank — Sharia-compliant ESG integration unique to GCC context",
            "CMA ESG disclosure guidelines compliance improving annually since 2021",
            "Saudi Vision 2030 alignment: green products, renewable energy project financing",
            "Social finance strength: zakat (Islamic social tax) quantification and reporting",
            "Governance: independent board committees including sustainability sub-committee (2023)",
        ],
        priority_gaps=[
            "PCAF financed emissions absent — largest single gap for international investors",
            "TCFD alignment in progress only — full 4-pillar disclosure not yet published",
            "ISSB S1/S2: not adopted — CMA guidelines are significantly less prescriptive",
            "Climate scenario analysis absent — NGFS scenarios not applied to real estate/O&G loan book",
            "Scope 3 financed emissions from Saudi Aramco-related project finance not disclosed",
            "TNFD: water stress in Saudi Arabia is a severe physical risk — no disclosure",
            "Net zero 2060 target aligned to Saudi national target — interim 2030 milestones absent",
        ],
        analyst_note="Al Rajhi Bank is Saudi Arabia's largest bank and the GCC's leading Islamic "
                     "financial institution. ESG disclosure is maturing rapidly under Vision 2030 "
                     "pressure, but remains 5+ years behind European peers. Financed emissions from "
                     "oil & gas project finance and real estate (water-stressed markets) are the "
                     "most material undisclosed risks.",
    ),

    InstitutionProfile(
        slug="adnoc", name="ADNOC (Abu Dhabi National Oil Company)", region="Middle East",
        country="UAE", institution_type="National Oil Company",
        assets_usd_bn=290,
        listed=False, exchange=None,
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2045, financed_sectors_nzba=0,
        report_url="https://www.adnoc.ae/en/sustainability",
        mandatory_frameworks=["UAE ESG Reporting Guidance (MOEI 2023)", "CBUAE Climate Risk Guidance"],
        voluntary_frameworks=["TCFD (adopted)", "GRI Standards", "IOGP Reporting Framework", "OGCI (member)", "CDP (responding)"],
        scores={
            "tcfd_governance": 70, "tcfd_strategy": 65, "tcfd_risk_mgmt": 62, "tcfd_metrics": 68,
            "issb_s1": 48, "issb_s2": 50,
            "esrs_e1": 22, "esrs_env_other": 18, "esrs_social": 50, "esrs_governance": 60,
            "double_materiality": 20,
            "pcaf_financed": 15, "scope3_cat15": 12,
            "paris_alignment": 42, "transition_plan": 45,
            "physical_risk": 55, "scenario_analysis": 48,
            "tnfd_nature": 25,
        },
        key_strengths=[
            "ADNOC 2045 net zero commitment for Scope 1+2 — with 2030 GHG intensity reduction target",
            "World's lowest carbon intensity oil production (~6 kgCO₂e/bbl vs. global avg ~18)",
            "Carbon capture and storage: Al Reyadah CCS facility — 800,000 tCO₂/yr",
            "Flaring intensity: top quartile globally — gas flaring elimination by 2030",
            "OGCI member — Oil and Gas Climate Initiative — collective climate action framework",
        ],
        priority_gaps=[
            "Scope 3 (downstream combustion): largest GHG source — not disclosed or targeted",
            "Climate scenario analysis: IEA NZE scenario not modelled against oil/gas reserves",
            "Stranded asset risk: reserves valuation under 1.5°C pathway not disclosed",
            "TNFD: offshore extraction, Abu Dhabi coastal ecosystem dependencies not assessed",
            "ISSB S1/S2 adoption not committed — material risk for international bond investors",
            "Double materiality assessment absent — impact on climate not acknowledged as material",
        ],
        analyst_note="ADNOC is the world's low-carbon-intensity oil producer and UAE's anchor for "
                     "COP28 credibility. Its disclosure has improved substantially but Scope 3 "
                     "(downstream combustion) and stranded asset analysis under 1.5°C remain the "
                     "most material gaps for international institutional investors. ISSB S2 adoption "
                     "would be transformative for its international green bond programme.",
    ),

    InstitutionProfile(
        slug="saudi_aramco", name="Saudi Aramco", region="Middle East",
        country="Saudi Arabia", institution_type="National Oil Company",
        assets_usd_bn=610,
        listed=True, exchange="Tadawul (Saudi Exchange)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.aramco.com/en/sustainability",
        mandatory_frameworks=["Saudi CMA ESG Guidelines", "SEC GHG Disclosure (partial — US listing exempt)"],
        voluntary_frameworks=["TCFD (adopted)", "GRI Standards", "IOGP Framework", "OGCI (member)", "CDP (B)"],
        scores={
            "tcfd_governance": 72, "tcfd_strategy": 68, "tcfd_risk_mgmt": 65, "tcfd_metrics": 70,
            "issb_s1": 52, "issb_s2": 55,
            "esrs_e1": 20, "esrs_env_other": 15, "esrs_social": 55, "esrs_governance": 62,
            "double_materiality": 18,
            "pcaf_financed": 15, "scope3_cat15": 10,
            "paris_alignment": 38, "transition_plan": 40,
            "physical_risk": 58, "scenario_analysis": 52,
            "tnfd_nature": 22,
        },
        key_strengths=[
            "World's largest oil company — sets GCC ESG disclosure benchmark by scale",
            "Carbon intensity: industry-leading 10.4 kgCO₂e/boe (Scope 1+2, equity basis)",
            "Flaring: near-zero routine flaring since 2010 — global benchmark for NOCs",
            "CCS: CCUS projects underway at Uthmaniyah and Haradh plants",
            "Greenhouse gas management: 2030 GHG intensity reduction target (15% below 2018)",
            "OGCI membership and methane intensity commitments",
        ],
        priority_gaps=[
            "Scope 3 emissions (downstream combustion) not disclosed — largest GHG source by 5-10x",
            "Net zero 2050: only operational (Scope 1+2) — no Scope 3 pathway published",
            "Stranded asset analysis: 303 billion BOE reserves under IEA NZE scenario — not modelled",
            "ISSB S1/S2: not adopted — significant gap for international institutional fixed income",
            "Climate scenario analysis: limited to internal NGFS-aligned work, not publicly disclosed",
            "TNFD nature: Red Sea, Arabian Gulf offshore ecosystem impact from extraction not assessed",
            "Just transition: Saudi workforce and community dependence on oil economy undisclosed",
        ],
        analyst_note="Saudi Aramco is the world's most profitable company and GCC's ESG disclosure "
                     "benchmark. Its operational carbon intensity is genuinely world-class. However, "
                     "Scope 3 omission, absent stranded asset analysis, and no 1.5°C pathway make it "
                     "uninvestable for Paris-aligned mandates without significant disclosure improvement. "
                     "ISSB S2 adoption is the single most impactful step it could take.",
    ),

    # ─── LATAM — Top 5 by Market Cap + Sustainability Coverage ───────────────

    InstitutionProfile(
        slug="petrobras", name="Petrobras (Petróleo Brasileiro)", region="Latin America",
        country="Brazil", institution_type="National Oil Company",
        assets_usd_bn=245,
        listed=True, exchange="B3 / NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.petrobras.com.br/en/society-and-environment/sustainability/reports",
        mandatory_frameworks=["CVM ESG Disclosure Requirements (Brazil)", "TCFD (comprehensive)", "GHG Protocol Brazil"],
        voluntary_frameworks=["ISSB S2 (alignment in progress)", "CDP A-", "GRI Standards", "TNFD (supporter)", "UNGC"],
        scores={
            "tcfd_governance": 75, "tcfd_strategy": 72, "tcfd_risk_mgmt": 70, "tcfd_metrics": 75,
            "issb_s1": 58, "issb_s2": 62,
            "esrs_e1": 25, "esrs_env_other": 20, "esrs_social": 62, "esrs_governance": 65,
            "double_materiality": 35,
            "pcaf_financed": 18, "scope3_cat15": 15,
            "paris_alignment": 48, "transition_plan": 45,
            "physical_risk": 65, "scenario_analysis": 68,
            "tnfd_nature": 42,
        },
        key_strengths=[
            "CDP A- rated — most advanced disclosure among LATAM NOCs",
            "TCFD 4-pillar comprehensive: board climate committee, scenario analysis (IEA/NGFS), Scope 1+2 targets",
            "Pre-salt deepwater: lowest GHG intensity per BOE of any major NOC (~12 kgCO₂e/boe)",
            "TNFD supporter — significant Amazon biodiversity and freshwater dependency mapping",
            "Brazil GHG Protocol: independently verified Scope 1, 2, 3 inventory since 2010",
            "Net zero 2050 with 2030 Scope 1+2 intensity target (-30% vs. 2015)",
        ],
        priority_gaps=[
            "Scope 3 Cat 11 (downstream combustion): largest emissions source — partially disclosed only",
            "Stranded asset risk: pre-salt reserves valuation under 1.5°C scenario not published",
            "TNFD LEAP: Amazon basin drilling operations require formal biodiversity dependency mapping",
            "Just transition: refinery worker and community exposure in northeast Brazil undisclosed",
            "ISSB S1/S2: alignment in progress only — full compliance planned for 2025",
            "Anti-corruption and governance: legacy Lava Jato exposure requires enhanced G disclosure",
        ],
        analyst_note="Petrobras is LATAM's most sophisticated NOC on climate disclosure. CDP A- rating "
                     "and comprehensive TCFD put it ahead of peers. The Amazonian operational context "
                     "makes TNFD nature the most material emerging gap. Scope 3 Scope 11 and stranded "
                     "asset analysis are critical for Paris-aligned mandate compliance.",
    ),

    InstitutionProfile(
        slug="itau_unibanco", name="Itaú Unibanco", region="Latin America",
        country="Brazil", institution_type="Universal Bank",
        assets_usd_bn=355,
        listed=True, exchange="B3 / NYSE (ADR)",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=3,
        report_url="https://www.itau.com.br/relacoes-com-investidores/sustentabilidade",
        mandatory_frameworks=["CMN Resolution 4945/2021 (Brazil Social-Environmental Risk)", "BACEN PRSAC", "CVM Disclosure"],
        voluntary_frameworks=["NZBA (member)", "PCAF (member)", "TCFD (comprehensive)", "TNFD (supporter)", "CDP B", "GRI Standards", "ISSB S2 (alignment)"],
        scores={
            "tcfd_governance": 80, "tcfd_strategy": 78, "tcfd_risk_mgmt": 75, "tcfd_metrics": 78,
            "issb_s1": 62, "issb_s2": 65,
            "esrs_e1": 22, "esrs_env_other": 18, "esrs_social": 68, "esrs_governance": 72,
            "double_materiality": 45,
            "pcaf_financed": 62, "scope3_cat15": 60,
            "paris_alignment": 58, "transition_plan": 55,
            "physical_risk": 65, "scenario_analysis": 62,
            "tnfd_nature": 42,
        },
        key_strengths=[
            "LATAM's most advanced bank on PCAF financed emissions — absolute and intensity metrics",
            "NZBA member — sector-specific net zero targets for O&G, power, agri lending",
            "CMN 4945/2021: Brazilian mandatory social-environmental risk integration — ahead of global peers",
            "Amazon Fund and deforestation-linked lending: Cerrado, Amazon biome exclusion criteria",
            "TNFD supporter — significant deforestation-linked agri finance exposure requires LEAP",
        ],
        priority_gaps=[
            "PCAF coverage: 68% of financed portfolio covered — agri and SME segments underweighted",
            "Deforestation-free: soy, beef, paper/pulp supply chain linkage not yet fully mapped",
            "ISSB S1/S2: alignment in progress — full disclosure target 2025",
            "Physical risk: Brazil flooding and drought in Cerrado/agricultural regions not modelled",
            "Transition plan: sector-specific glidepaths not yet published for all 3 NZBA sectors",
            "TNFD LEAP not yet published despite material Amazon/Cerrado deforestation exposure",
        ],
        analyst_note="Itaú Unibanco is LATAM's benchmark bank for climate and nature finance disclosure. "
                     "PCAF membership and financed emissions disclosure sets it apart from regional peers. "
                     "Deforestation-linked lending (agri, beef, soy) and TNFD LEAP are the most material "
                     "gaps for biodiversity-focused institutional investors.",
    ),

    InstitutionProfile(
        slug="vale", name="Vale S.A.", region="Latin America",
        country="Brazil", institution_type="Mining & Metals",
        assets_usd_bn=98,
        listed=True, exchange="B3 / NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.vale.com/en/sustainability/reports",
        mandatory_frameworks=["CVM ESG Disclosure", "TCFD (comprehensive)", "GHG Protocol Brazil"],
        voluntary_frameworks=["CDP A", "GRI Standards", "TNFD (supporter, pilot)", "ICMM (member)", "SASB Metals/Mining", "ISSB S2 (aligned)"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 80, "tcfd_risk_mgmt": 78, "tcfd_metrics": 82,
            "issb_s1": 72, "issb_s2": 75,
            "esrs_e1": 28, "esrs_env_other": 32, "esrs_social": 58, "esrs_governance": 65,
            "double_materiality": 52,
            "pcaf_financed": 20, "scope3_cat15": 18,
            "paris_alignment": 62, "transition_plan": 65,
            "physical_risk": 78, "scenario_analysis": 75,
            "tnfd_nature": 68,
        },
        key_strengths=[
            "CDP Climate A-rated — among the best-in-class mining companies globally",
            "TNFD pilot participant — Amazon and Cerrado biodiversity dependency mapping advanced",
            "ICMM membership: Tailings dam standards (post-Mariana/Brumadinho) — safety & ESG disclosure",
            "Scope 3 steel customer decarbonisation: DRI-EAF green iron investment ($4.4bn)",
            "Physical risk: mine-level water stress and extreme weather modelling published",
            "2050 net zero with 2030 Scope 1+2 target (-33% absolute) and Scope 3 intensity target",
        ],
        priority_gaps=[
            "Scope 3 steel customer emissions: Cat 11 (use of products) — iron ore's decarbonisation role",
            "Tailings dam safety: post-Brumadinho reputational risk still embedded in ESG ratings",
            "TNFD LEAP: Amazon mining operations — freshwater and biodiversity formal LEAP not published",
            "Just transition: indigenous community engagement and free prior informed consent records",
            "Water: Mariana basin water restoration not fully quantified in 2030 targets",
            "Scope 2 electricity: grid carbon intensity in Brazil and Canada creates emissions volatility",
        ],
        analyst_note="Vale is LATAM's best-in-class mining ESG disclosure. CDP A-rating, TNFD pilot, "
                     "and ICMM membership distinguish it from peers. Post-Brumadinho dam failure legacy "
                     "requires enhanced social/safety disclosure. TNFD LEAP for Amazon operations and "
                     "Scope 3 steel transition (DRI-EAF) are the most material emerging gaps.",
    ),

    InstitutionProfile(
        slug="ecopetrol", name="Ecopetrol S.A.", region="Latin America",
        country="Colombia", institution_type="National Oil Company",
        assets_usd_bn=62,
        listed=True, exchange="BVC Bogotá / NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.ecopetrol.com.co/en/investors/sustainability",
        mandatory_frameworks=["Colombian SFC ESG Disclosure", "TCFD (adopted)"],
        voluntary_frameworks=["CDP B", "GRI Standards", "ISSB S2 (alignment planned)", "UNGC", "IPIECA"],
        scores={
            "tcfd_governance": 68, "tcfd_strategy": 65, "tcfd_risk_mgmt": 62, "tcfd_metrics": 65,
            "issb_s1": 48, "issb_s2": 52,
            "esrs_e1": 18, "esrs_env_other": 15, "esrs_social": 55, "esrs_governance": 60,
            "double_materiality": 28,
            "pcaf_financed": 12, "scope3_cat15": 10,
            "paris_alignment": 45, "transition_plan": 42,
            "physical_risk": 60, "scenario_analysis": 55,
            "tnfd_nature": 35,
        },
        key_strengths=[
            "LATAM's most important non-Brazilian NOC — leading Colombia's energy transition",
            "Renewable energy investments growing — wind, solar, and hydrogen pipeline",
            "Methane: flaring reduction programme below 1% of production",
            "Physical risk: Colombian Andean water risks modelled across upstream assets",
            "Social licence: community development investment quantified in GRI reports",
        ],
        priority_gaps=[
            "Scope 3 Cat 11 downstream combustion: absent from all public disclosures",
            "ISSB S1/S2: alignment planned only — no compliant disclosure published",
            "Climate scenario analysis: IEA NZE not applied to Colombian oil/gas reserves",
            "Stranded asset risk: Putumayo basin reserves valuation under 1.5°C undisclosed",
            "TNFD: Amazon/Orinoquia ecosystem biodiversity dependencies from operations not mapped",
            "Biodiversity: HF (hydraulic fracturing) moratorium in Colombia creates operational risk",
        ],
        analyst_note="Ecopetrol is Colombia's anchor company and LATAM's 5th-largest NOC by production. "
                     "Climate disclosure is improving rapidly but lags Brazilian peers significantly. "
                     "Scope 3, ISSB S2, and TNFD nature are priority gaps for international investors. "
                     "The Colombian energy transition context (coal phase-out, biodiversity) makes "
                     "nature risk disclosure particularly material.",
    ),

    InstitutionProfile(
        slug="bancolombia", name="Bancolombia S.A.", region="Latin America",
        country="Colombia", institution_type="Universal Bank",
        assets_usd_bn=42,
        listed=True, exchange="BVC Bogotá / NYSE (ADR)",
        nzba_member=True, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=2,
        report_url="https://www.bancolombia.com/personas/acerca-de-bancolombia/sostenibilidad",
        mandatory_frameworks=["Colombian SFC ESG Disclosure", "Colombian TCFD (SFC Circular 028/2021)"],
        voluntary_frameworks=["NZBA (member)", "GRI Standards", "CDP (responding)", "ISSB S2 (alignment planned)", "UNGC"],
        scores={
            "tcfd_governance": 68, "tcfd_strategy": 65, "tcfd_risk_mgmt": 62, "tcfd_metrics": 62,
            "issb_s1": 45, "issb_s2": 48,
            "esrs_e1": 15, "esrs_env_other": 12, "esrs_social": 60, "esrs_governance": 65,
            "double_materiality": 30,
            "pcaf_financed": 28, "scope3_cat15": 25,
            "paris_alignment": 40, "transition_plan": 38,
            "physical_risk": 52, "scenario_analysis": 45,
            "tnfd_nature": 28,
        },
        key_strengths=[
            "NZBA member — LATAM's only Colombian bank committed to Net Zero Banking Alliance",
            "SFC Circular 028 compliance: Colombia's mandatory climate risk disclosure since 2021",
            "Green bond programme: COP 500bn green/social bond framework (2022)",
            "Sustainable agriculture: coffee sector green lending — significant LATAM differentiation",
            "Scope 1+2 net zero for own operations committed by 2030",
        ],
        priority_gaps=[
            "PCAF financed emissions not yet adopted — financed portfolio emissions absent",
            "ISSB S1/S2 alignment planned 2025 — not yet compliant",
            "Climate scenario analysis: NGFS not applied to Colombian O&G, agri, real estate book",
            "Physical risk: Colombian flooding, drought, landslide risk to infrastructure loan book",
            "TNFD: biodiversity-linked agri lending (coffee, palm, banana) requires nature risk framework",
            "Transition plan: sector-specific glidepaths not published despite NZBA membership",
        ],
        analyst_note="Bancolombia is LATAM's most progressive Colombian bank on sustainability. "
                     "NZBA membership and SFC compliance distinguish it regionally. PCAF financed "
                     "emissions adoption is the critical near-term gap for international ESG "
                     "investors. Nature risk (agri lending + biodiversity) will become increasingly "
                     "material as TNFD adoption spreads to LATAM financial institutions.",
    ),

    # ─── India — Top 5 by Market Cap with BRSR Coverage ──────────────────────

    InstitutionProfile(
        slug="reliance_industries", name="Reliance Industries Limited", region="Asia Pacific",
        country="India", institution_type="Conglomerate (Energy / Retail / Digital)",
        assets_usd_bn=260,
        listed=True, exchange="BSE / NSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2035, financed_sectors_nzba=0,
        report_url="https://www.ril.com/Sustainability/SustainabilityReports",
        mandatory_frameworks=["SEBI BRSR (mandatory, FY2022-23 onwards)", "GHG Protocol India", "SEBI LODR (ESG disclosures)"],
        voluntary_frameworks=["TCFD (alignment in progress)", "GRI Standards", "CDP (C)", "ISSB S2 (alignment planned)", "UNGC"],
        scores={
            "tcfd_governance": 62, "tcfd_strategy": 65, "tcfd_risk_mgmt": 58, "tcfd_metrics": 65,
            "issb_s1": 48, "issb_s2": 52,
            "esrs_e1": 15, "esrs_env_other": 18, "esrs_social": 58, "esrs_governance": 65,
            "double_materiality": 28,
            "pcaf_financed": 10, "scope3_cat15": 8,
            "paris_alignment": 55, "transition_plan": 58,
            "physical_risk": 52, "scenario_analysis": 48,
            "tnfd_nature": 22,
        },
        key_strengths=[
            "India's largest company — net zero 2035 target (15 years ahead of India's NDC) sets benchmark",
            "New Energy investments: ₹75,000 crore (~$9bn) across solar, hydrogen, green chemicals",
            "BRSR Core: SEBI's mandatory framework with reasonable assurance — India's most comprehensive disclosure",
            "Green hydrogen: Dhirubhai Ambani Green Energy Giga Complex — world-scale commitment",
            "Scope 1+2 intensity reduction targets with 3rd party verification",
        ],
        priority_gaps=[
            "TCFD: alignment in progress — full 4-pillar disclosure not yet published",
            "Scope 3: petroleum products downstream (Cat 11) not disclosed — largest emissions source",
            "ISSB S2 adoption not committed — significant gap for international bond/equity investors",
            "Climate scenario analysis: IEA NZE not applied to O&G refining/petrochemical assets",
            "TNFD: Jamnagar refinery complex — coastal ecosystem, water, air quality dependencies",
            "Just transition: petrochemical and refinery workforce transition planning absent",
        ],
        analyst_note="Reliance Industries is India's most visible ESG story — net zero 2035 is "
                     "10 years ahead of India's national target and a credible strategic commitment. "
                     "BRSR compliance is comprehensive for India. Scope 3 downstream, ISSB S2, and "
                     "TNFD are the critical gaps for international Paris-aligned mandates. "
                     "The New Energy pivot makes it a unique emerging market transition story.",
    ),

    InstitutionProfile(
        slug="tata_consultancy", name="Tata Consultancy Services (TCS)", region="Asia Pacific",
        country="India", institution_type="Technology / IT Services",
        assets_usd_bn=55,
        listed=True, exchange="BSE / NSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://www.tcs.com/sustainability",
        mandatory_frameworks=["SEBI BRSR (mandatory)", "GHG Protocol India"],
        voluntary_frameworks=["TCFD (comprehensive)", "CDP A", "GRI Standards", "ISSB S2 (aligned)", "SBTI (1.5°C)", "UNGC", "RE100 (100% renewable electricity)"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 80, "tcfd_metrics": 85,
            "issb_s1": 75, "issb_s2": 78,
            "esrs_e1": 32, "esrs_env_other": 28, "esrs_social": 75, "esrs_governance": 80,
            "double_materiality": 55,
            "pcaf_financed": 8, "scope3_cat15": 5,
            "paris_alignment": 78, "transition_plan": 80,
            "physical_risk": 72, "scenario_analysis": 75,
            "tnfd_nature": 35,
        },
        key_strengths=[
            "CDP Climate A-rated — India's highest-scoring company on CDP climate disclosure",
            "SBTi 1.5°C aligned net zero 2030 — most aggressive climate target among Indian large-caps",
            "RE100 member: 100% renewable electricity across all global operations by 2025",
            "ISSB S2 alignment: climate-related financial risk disclosure at institutional grade",
            "BRSR Core: comprehensive India-mandatory disclosure with 3rd party assurance",
            "Carbon neutral since 2022 (Scope 1+2) — first Indian IT company to achieve this",
        ],
        priority_gaps=[
            "Scope 3 Cat 1/2 supply chain (hardware, cloud infrastructure procurement) growing in materiality",
            "TNFD: nature dependencies in data centre water usage and land for campuses not assessed",
            "Double materiality: impact materiality assessment limited — human rights in supply chain",
            "ESRS/CSRD: not in scope but EU clients requiring CSRD-aligned reporting creates indirect pressure",
            "AI energy consumption: growing inference/training workload GHG impact not yet quantified",
            "Scope 3 Cat 11: software/IT services Scope 3 methodology still developing industry-wide",
        ],
        analyst_note="TCS is India's benchmark for corporate climate disclosure — CDP A, SBTi 1.5°C, "
                     "carbon neutral, RE100. Its disclosure quality rivals European tech leaders. "
                     "Key gaps: Scope 3 supply chain (hardware), TNFD data centre water, and "
                     "AI/compute GHG methodology. As India's most internationally held stock, "
                     "its disclosure maturity directly influences India ESG perception globally.",
    ),

    InstitutionProfile(
        slug="hdfc_bank", name="HDFC Bank", region="Asia Pacific",
        country="India", institution_type="Universal Bank",
        assets_usd_bn=300,
        listed=True, exchange="BSE / NSE / NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2032, financed_sectors_nzba=0,
        report_url="https://www.hdfcbank.com/content/bbp/repositories/723fb80a-2dde-42a3-9793-7ae1be57c87f/ESG",
        mandatory_frameworks=["SEBI BRSR (mandatory)", "RBI Sustainable Finance Framework", "GHG Protocol India"],
        voluntary_frameworks=["TCFD (alignment)", "GRI Standards", "CDP (B)", "ISSB S2 (planned)", "UNGC"],
        scores={
            "tcfd_governance": 65, "tcfd_strategy": 62, "tcfd_risk_mgmt": 58, "tcfd_metrics": 62,
            "issb_s1": 45, "issb_s2": 48,
            "esrs_e1": 12, "esrs_env_other": 10, "esrs_social": 62, "esrs_governance": 72,
            "double_materiality": 25,
            "pcaf_financed": 22, "scope3_cat15": 18,
            "paris_alignment": 38, "transition_plan": 35,
            "physical_risk": 52, "scenario_analysis": 45,
            "tnfd_nature": 18,
        },
        key_strengths=[
            "India's largest private bank — BRSR compliance sets sector benchmark",
            "RBI Sustainable Finance Framework alignment: green and sustainable credit priority sectors",
            "Priority sector lending: agricultural and MSME green credit growing portfolio",
            "Operational net zero 2032: own operations with renewable energy transition underway",
            "SEBI BRSR Core: India's most comprehensive mandatory ESG disclosure for banking sector",
        ],
        priority_gaps=[
            "PCAF financed emissions: not adopted — largest single gap for international ESG investors",
            "Scope 3 Cat 15: financed emissions absent from all disclosures",
            "ISSB S1/S2: planned 2025 — significant gap for Indian ADR holders with ESG mandates",
            "Climate scenario analysis: RBI's NGFS pilot participation not yet reflected in public disclosure",
            "Physical risk: agriculture sector loan book exposed to monsoon variability, drought — not quantified",
            "TNFD: water risk in agricultural lending (India's most water-stressed economy) not disclosed",
            "Transition plan: sector-level decarbonisation targets absent despite RBI guidance",
        ],
        analyst_note="HDFC Bank is India's largest private bank and increasingly central to the "
                     "RBI sustainable finance agenda. BRSR compliance is strong for India. "
                     "PCAF financed emissions and ISSB S2 adoption are the critical gaps. "
                     "Agricultural lending exposure to climate physical risk (drought, flooding) "
                     "is the most material undisclosed financial risk.",
    ),

    InstitutionProfile(
        slug="infosys", name="Infosys Limited", region="Asia Pacific",
        country="India", institution_type="Technology / IT Services",
        assets_usd_bn=38,
        listed=True, exchange="BSE / NSE / NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.infosys.com/esg.html",
        mandatory_frameworks=["SEBI BRSR (mandatory)", "GHG Protocol India"],
        voluntary_frameworks=["TCFD (comprehensive)", "CDP A", "GRI Standards", "ISSB S2 (aligned)", "SBTI (1.5°C)", "RE100", "UNGC"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 80, "tcfd_risk_mgmt": 78, "tcfd_metrics": 82,
            "issb_s1": 72, "issb_s2": 75,
            "esrs_e1": 30, "esrs_env_other": 25, "esrs_social": 72, "esrs_governance": 78,
            "double_materiality": 52,
            "pcaf_financed": 5, "scope3_cat15": 4,
            "paris_alignment": 72, "transition_plan": 75,
            "physical_risk": 68, "scenario_analysis": 70,
            "tnfd_nature": 32,
        },
        key_strengths=[
            "CDP A-rated — joint-top with TCS among Indian companies on climate disclosure",
            "Carbon neutral since FY2020 (Scope 1+2) — world's first major IT company to achieve this",
            "SBTi 1.5°C net zero 2040: comprehensive scope including Scope 3 Cat 1-15",
            "RE100 member: 100% renewable electricity across all operations",
            "ISSB S2 aligned: climate risk financial disclosure at institutional grade",
            "Infosys ESG Vision 2030: 10-year sustainability strategy with quarterly KPI reporting",
        ],
        priority_gaps=[
            "Scope 3 Cat 1/2: supply chain hardware/IT procurement — growing as AI compute scales",
            "TNFD: data centre freshwater consumption for cooling — not formally assessed",
            "AI energy: generative AI training/inference workload GHG escalation not yet in targets",
            "ESRS E1: EU client-driven indirect CSRD pressure — supply chain Scope 3 methodology needed",
            "Double materiality: impact on communities and digital rights — incomplete assessment",
            "BRSR Core: reasonable assurance obtained but limited-scope supply chain verification",
        ],
        analyst_note="Infosys is co-equal with TCS as India's benchmark for climate disclosure — "
                     "carbon neutral since 2020, CDP A, SBTi 1.5°C, RE100. Disclosure quality "
                     "rivals global tech leaders. Emerging gap: AI compute energy escalation and "
                     "data centre water use are becoming material as generative AI workloads grow. "
                     "TNFD data centre LEAP would be industry-defining for Indian IT sector.",
    ),

    InstitutionProfile(
        slug="larsen_toubro", name="Larsen & Toubro (L&T)", region="Asia Pacific",
        country="India", institution_type="Engineering & Infrastructure Conglomerate",
        assets_usd_bn=52,
        listed=True, exchange="BSE / NSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.larsentoubro.com/corporate/sustainability",
        mandatory_frameworks=["SEBI BRSR (mandatory)", "GHG Protocol India"],
        voluntary_frameworks=["TCFD (adopted)", "GRI Standards", "CDP B+", "ISSB S2 (alignment planned)", "UNGC"],
        scores={
            "tcfd_governance": 70, "tcfd_strategy": 68, "tcfd_risk_mgmt": 65, "tcfd_metrics": 68,
            "issb_s1": 55, "issb_s2": 58,
            "esrs_e1": 22, "esrs_env_other": 20, "esrs_social": 65, "esrs_governance": 70,
            "double_materiality": 38,
            "pcaf_financed": 8, "scope3_cat15": 6,
            "paris_alignment": 52, "transition_plan": 55,
            "physical_risk": 62, "scenario_analysis": 58,
            "tnfd_nature": 28,
        },
        key_strengths=[
            "India's leading engineering-to-EPC conglomerate — positioned at heart of energy transition",
            "Green infrastructure EPC: solar, wind, water treatment, green hydrogen manufacturing",
            "BRSR Core compliance: India's most comprehensive mandatory ESG reporting for industrial conglomerates",
            "Net zero 2040 for Scope 1+2 with SBTi submission in progress",
            "Circular economy: construction waste reduction and material efficiency metrics published",
            "Water positive: multiple L&T facilities achieve water-positive status",
        ],
        priority_gaps=[
            "Scope 3 Cat 11: engineering/infrastructure products sold — life-cycle emissions of projects not assessed",
            "ISSB S1/S2: alignment planned — significant gap for international infrastructure bond investors",
            "Climate scenario analysis: NGFS/IEA NZE not applied to infrastructure asset portfolio",
            "TNFD: significant land use and freshwater impacts from construction operations across India",
            "Just transition: construction workforce safety and informal labour supply chain disclosure",
            "Physical risk: Gulf/Middle East projects exposed to extreme heat — not quantified in reports",
        ],
        analyst_note="L&T is India's most important infrastructure and engineering company — uniquely "
                     "positioned to enable OR to delay India's energy transition at scale. BRSR "
                     "disclosure is strong for Indian industrial. Scope 3 project lifecycle emissions, "
                     "ISSB S2, and Middle East heat stress (major export revenue) are the critical "
                     "gaps for ESG-aligned infrastructure investors.",
    ),

    # ─── Asset Management ─────────────────────────────────────────────────────

    InstitutionProfile(
        slug="blackrock", name="BlackRock Inc.", region="North America",
        country="US", institution_type="Asset Manager",
        assets_usd_bn=10000,  # AUM
        listed=True, exchange="NYSE",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.blackrock.com/corporate/responsibility/sustainability",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["PCAF (member)", "TNFD (supporter)", "ISSB S2 (aligned)", "CDP (A-list)", "NZAMI (member)", "SFDR (EU funds)", "Paris Aligned Benchmark"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82, "tcfd_metrics": 85,
            "issb_s1": 78, "issb_s2": 82,
            "esrs_e1": 30, "esrs_env_other": 20, "esrs_social": 62, "esrs_governance": 78,
            "double_materiality": 42,
            "pcaf_financed": 72, "scope3_cat15": 70,
            "paris_alignment": 75, "transition_plan": 72,
            "physical_risk": 78, "scenario_analysis": 80,
            "tnfd_nature": 52,
        },
        key_strengths=[
            "World's largest asset manager — $10tn AUM — sets industry disclosure standard",
            "PCAF member: financed emissions coverage across fixed income and equity AUM",
            "NZAMI member: Net Zero Asset Managers Initiative — 50% AUM aligned by 2030",
            "Aladdin Risk: physical climate risk modelling embedded in portfolio construction",
            "TNFD supporter — biodiversity data integrated into risk screening",
            "SFDR Article 8/9 funds: EU regulatory compliance across European fund range",
        ],
        priority_gaps=[
            "US political context: ESG commitment under pressure from anti-ESG state legislation",
            "PCAF coverage: not all $10tn AUM covered — private markets and alternatives gaps",
            "Double materiality: investment-grade impact assessment not yet published",
            "TNFD LEAP not published despite significant biodiversity mandate growth",
            "Transition plan stewardship: engagement escalation process for non-compliant issuers",
        ],
        analyst_note="BlackRock is the de facto standard-setter for asset manager climate disclosure. "
                     "PCAF membership, NZAMI, and Aladdin climate risk integration are industry-leading. "
                     "Political pressure from US anti-ESG sentiment is the primary reputational risk "
                     "for European institutional investors.",
    ),

    InstitutionProfile(
        slug="vanguard", name="The Vanguard Group", region="North America",
        country="US", institution_type="Asset Manager",
        assets_usd_bn=8100,  # AUM
        listed=False, exchange=None,
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=None, financed_sectors_nzba=0,
        report_url="https://corporate.vanguard.com/content/corporatesite/us/en/corp/who-we-are/esg.html",
        mandatory_frameworks=["TCFD (partial)", "SEC GHG Disclosure (stayed)"],
        voluntary_frameworks=["GRI Standards (partial)", "ISSB S2 (monitoring)"],
        scores={
            "tcfd_governance": 55, "tcfd_strategy": 48, "tcfd_risk_mgmt": 45, "tcfd_metrics": 48,
            "issb_s1": 38, "issb_s2": 40,
            "esrs_e1": 12, "esrs_env_other": 8, "esrs_social": 40, "esrs_governance": 55,
            "double_materiality": 18,
            "pcaf_financed": 20, "scope3_cat15": 18,
            "paris_alignment": 30, "transition_plan": 25,
            "physical_risk": 42, "scenario_analysis": 38,
            "tnfd_nature": 15,
        },
        key_strengths=[
            "World's 2nd-largest asset manager — passive indexing model creates unique ESG position",
            "Stewardship: proxy voting is primary climate lever — 1,000+ climate-related engagements/year",
            "Low-cost ETF model: democratises access to ESG/climate-themed indices",
            "Investment stewardship team: dedicated engagement programme with portfolio companies",
        ],
        priority_gaps=[
            "NZAMI: withdrew in 2022 — not committed to net zero asset management",
            "PCAF: financed emissions not adopted — significant gap vs. European peers",
            "Passive model tension: index replication limits active decarbonisation",
            "Climate stewardship: voted against majority of shareholder climate resolutions",
            "No formal net zero target for AUM — direct contrast with BlackRock and Schroders",
            "TNFD, double materiality, scenario analysis: all absent or minimal",
        ],
        analyst_note="Vanguard represents the most significant ESG disclosure gap among top-10 global "
                     "asset managers. NZAMI withdrawal and no PCAF adoption contrast sharply with peers. "
                     "Its passive model creates genuine tension: decarbonising AUM requires active "
                     "stewardship that conflicts with low-cost index tracking.",
    ),

    InstitutionProfile(
        slug="pimco", name="PIMCO (Pacific Investment Management)", region="North America",
        country="US", institution_type="Asset Manager (Fixed Income)",
        assets_usd_bn=1900,  # AUM
        listed=False, exchange=None,
        nzba_member=False, pcaf_member=True, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.pimco.com/en-us/our-firm/esg-investing",
        mandatory_frameworks=["TCFD (comprehensive — fixed income)", "SEC GHG Disclosure (stayed)"],
        voluntary_frameworks=["PCAF (member)", "NZAMI (member)", "ISSB S2 (aligned)", "SFDR (EU funds)", "Climate Bonds Initiative (partner)"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 80, "tcfd_risk_mgmt": 78, "tcfd_metrics": 80,
            "issb_s1": 70, "issb_s2": 75,
            "esrs_e1": 25, "esrs_env_other": 18, "esrs_social": 58, "esrs_governance": 72,
            "double_materiality": 38,
            "pcaf_financed": 68, "scope3_cat15": 65,
            "paris_alignment": 70, "transition_plan": 68,
            "physical_risk": 75, "scenario_analysis": 78,
            "tnfd_nature": 38,
        },
        key_strengths=[
            "World's largest active fixed income manager — most important voice in green bond markets",
            "PCAF member: fixed income WACI and financed emissions methodology leader",
            "Physical risk: municipal bond and sovereign credit physical risk integration pioneered",
            "Green/sustainable bond investment: $100bn+ managed in climate-themed fixed income",
            "NZAMI member: 100% AUM net zero aligned by 2050 commitment",
            "Climate scenario analysis: NGFS and proprietary models applied to sovereign and corporate credit",
        ],
        priority_gaps=[
            "TNFD: nature-related risks in sovereign credit (deforestation risk countries) not formalised",
            "Double materiality: impact on climate vs. climate impact on portfolio — investment-grade",
            "Engagement: fixed income investors have limited direct engagement leverage vs. equity",
            "Scope 3: supply chain and travel GHG from PIMCO operations not prioritised",
            "Climate voting: bond investor proxy voting rights are minimal vs. equity counterparts",
        ],
        analyst_note="PIMCO is the most important fixed income asset manager for climate finance. "
                     "PCAF financed emissions methodology for fixed income is industry-leading. "
                     "Physical risk in municipal bonds (flood, drought) is genuinely differentiated. "
                     "Nature risk in sovereign credit (deforestation, biodiversity) is the key emerging gap.",
    ),

    InstitutionProfile(
        slug="schroders", name="Schroders plc", region="Europe",
        country="UK", institution_type="Asset Manager",
        assets_usd_bn=980,  # AUM
        listed=True, exchange="London Stock Exchange",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.schroders.com/en-gb/uk/institutional/insights/sustainability-reports",
        mandatory_frameworks=["TCFD (comprehensive)", "UK SDR (SFDR equivalent)", "FCA Climate Disclosures"],
        voluntary_frameworks=["PCAF (member)", "NZAMI (member)", "TNFD (supporter)", "ISSB S2 (aligned)", "CDP A", "UK Stewardship Code"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 82, "issb_s2": 85,
            "esrs_e1": 45, "esrs_env_other": 30, "esrs_social": 70, "esrs_governance": 82,
            "double_materiality": 60,
            "pcaf_financed": 78, "scope3_cat15": 75,
            "paris_alignment": 80, "transition_plan": 78,
            "physical_risk": 82, "scenario_analysis": 85,
            "tnfd_nature": 62,
        },
        key_strengths=[
            "UK's leading active asset manager — Climate Progress Dashboard proprietary tool",
            "PCAF member: financed emissions across listed equity, fixed income, real estate",
            "TNFD supporter: biodiversity footprint of investment portfolios being quantified",
            "CDP A-rated — top-tier corporate climate disclosure among global asset managers",
            "SustainEx: proprietary social and environmental cost model for portfolio companies",
            "UK Stewardship Code signatory: highest engagement standards for company transition",
        ],
        priority_gaps=[
            "ESRS E1: UK-domiciled but EU clients create CSRD supply chain pressure",
            "TNFD LEAP: nature-related risk in real assets (agriculture, forestry) not yet published",
            "Double materiality: SustainEx captures impact but formal ESRS-standard DMA not completed",
            "Private markets: GHG and sustainability disclosure for private equity AUM limited",
            "Engagement escalation: published process but voting record on climate resolutions mixed",
        ],
        analyst_note="Schroders is the European benchmark for UK active asset manager climate disclosure. "
                     "PCAF, NZAMI, TNFD, CDP A — comprehensive commitment. SustainEx proprietary "
                     "tool and Climate Progress Dashboard are genuinely differentiated. TNFD LEAP for "
                     "real assets and ESRS E1 supply chain pressure are the key emerging gaps.",
    ),

    InstitutionProfile(
        slug="amundi", name="Amundi Asset Management", region="Europe",
        country="France", institution_type="Asset Manager",
        assets_usd_bn=2100,  # AUM
        listed=True, exchange="Euronext Paris",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.amundi.com/professional/insights/our-responsible-investment-approach",
        mandatory_frameworks=["CSRD (2024 — as corporate)", "TCFD (comprehensive)", "SFDR (full suite)", "French Greenfin/SRI labels"],
        voluntary_frameworks=["PCAF (member)", "NZAMI (member)", "TNFD (supporter)", "ISSB S2 (aligned)", "CDP A", "Climate Action 100+"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 80, "issb_s2": 85,
            "esrs_e1": 55, "esrs_env_other": 38, "esrs_social": 72, "esrs_governance": 80,
            "double_materiality": 65,
            "pcaf_financed": 80, "scope3_cat15": 78,
            "paris_alignment": 82, "transition_plan": 80,
            "physical_risk": 80, "scenario_analysis": 82,
            "tnfd_nature": 60,
        },
        key_strengths=[
            "Europe's largest asset manager — €2.1tn AUM — SFDR leadership sets EU standard",
            "CSRD corporate reporter: full ESRS E1 disclosure as an issuer — rare among asset managers",
            "PCAF member: financed emissions across equity, credit, infrastructure and real assets",
            "SFDR Article 8/9 classification leader: 80%+ of AUM in Article 8 or 9 funds",
            "Climate Action 100+: lead investor engagement on 30+ systemically important emitters",
            "Double materiality: completed for corporate disclosures — most advanced among asset managers",
        ],
        priority_gaps=[
            "TNFD LEAP: biodiversity in private equity, forestry and agriculture AUM",
            "Passive AUM: index tracking limits ability to decarbonise in line with NZAMI commitment",
            "Emerging market AUM: India, China, Brazil portfolio climate data quality (DQS 4/5)",
            "Scope 3 Cat 15: investee company emissions for private market holdings not fully covered",
            "Fixed income voting: limited stewardship leverage in fixed income mandates",
        ],
        analyst_note="Amundi is Europe's most comprehensive asset manager disclosure. CSRD as issuer, "
                     "SFDR leadership, PCAF, and double materiality put it ahead globally. The "
                     "combination of French regulatory environment and EU client base creates the "
                     "deepest disclosure requirements of any major asset manager worldwide.",
    ),

    # ─── Private Equity ───────────────────────────────────────────────────────

    InstitutionProfile(
        slug="tpg_rise", name="TPG Rise Climate Fund", region="North America",
        country="US", institution_type="Climate-Focused Private Equity",
        assets_usd_bn=7,  # Rise Climate Fund AUM
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.tpg.com/strategies/rise-climate",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["TCFD (comprehensive)", "ISSB S2 (aligned)", "TNFD (supporter)", "SBTI (portfolio companies)", "PCAF (partial)"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 90, "tcfd_risk_mgmt": 82, "tcfd_metrics": 85,
            "issb_s1": 72, "issb_s2": 78,
            "esrs_e1": 30, "esrs_env_other": 25, "esrs_social": 55, "esrs_governance": 72,
            "double_materiality": 52,
            "pcaf_financed": 55, "scope3_cat15": 50,
            "paris_alignment": 92, "transition_plan": 90,
            "physical_risk": 75, "scenario_analysis": 78,
            "tnfd_nature": 45,
        },
        key_strengths=[
            "Dedicated climate PE fund — 100% of AUM in climate solutions (cleantech, efficiency, nature)",
            "Portfolio impact quantification: annual tCO₂e avoided per dollar invested reported",
            "TPG's access to Fortune 500 relationships accelerates cleantech commercialisation",
            "Paris alignment: every portfolio company has decarbonisation plan as investment condition",
            "TNFD supporter — biodiversity-positive investments tracked in portfolio",
        ],
        priority_gaps=[
            "PE reporting: portfolio company sustainability data often not independently verified",
            "PCAF financed emissions: methodology for private equity still developing",
            "Scope 3 upstream: portfolio company supply chains not fully captured",
            "ESRS/CSRD: EU portfolio companies increasingly in scope — data quality variable",
            "Exit: sustainability performance of portfolio companies post-exit not tracked",
        ],
        analyst_note="TPG Rise Climate is the most sophisticated dedicated climate PE fund globally. "
                     "Its investment thesis IS decarbonisation — portfolio is structurally Paris-aligned. "
                     "PCAF PE methodology and post-exit tracking are the key gaps. As PE reporting "
                     "standards evolve (ILPA, EDCI), Rise Climate will be the sector benchmark.",
    ),

    InstitutionProfile(
        slug="kkr", name="KKR & Co. Inc.", region="North America",
        country="US", institution_type="Private Equity",
        assets_usd_bn=553,  # Total AUM
        listed=True, exchange="NYSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.kkr.com/our-firm/environmental-social-governance",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["TCFD (comprehensive)", "ISSB S2 (aligned)", "TNFD (supporter)", "EDCI (ESG Data Convergence Initiative)"],
        scores={
            "tcfd_governance": 80, "tcfd_strategy": 78, "tcfd_risk_mgmt": 75, "tcfd_metrics": 78,
            "issb_s1": 65, "issb_s2": 70,
            "esrs_e1": 22, "esrs_env_other": 18, "esrs_social": 62, "esrs_governance": 72,
            "double_materiality": 40,
            "pcaf_financed": 48, "scope3_cat15": 45,
            "paris_alignment": 60, "transition_plan": 62,
            "physical_risk": 70, "scenario_analysis": 68,
            "tnfd_nature": 40,
        },
        key_strengths=[
            "EDCI founding member — ESG Data Convergence Initiative standardising PE sustainability reporting",
            "Global Atlantic (insurance): embedded climate risk in long-duration insurance liabilities",
            "Infrastructure platform: significant renewable energy and energy transition exposure",
            "Scope 1+2 reporting for 95%+ of PE portfolio companies — industry-leading coverage",
            "Decarbonisation program: portfolio companies with GHG targets growing annually",
        ],
        priority_gaps=[
            "PCAF: financed emissions for PE methodology still not widely adopted",
            "Scope 3: PE supply chain emissions across diverse portfolio not yet aggregated",
            "Net zero: 2050 commitment without intermediate milestones for portfolio",
            "Nature: TNFD supporter but LEAP not yet conducted for infrastructure/real assets",
            "EU portfolio: CSRD in-scope companies creating data quality pressure",
            "Climate scenario analysis at portfolio company level not yet published",
        ],
        analyst_note="KKR is the most sophisticated large-cap PE firm on climate disclosure through "
                     "EDCI founding membership. Scope 1+2 portfolio coverage and infrastructure "
                     "transition exposure are strengths. Financed emissions (PCAF for PE) and "
                     "nature risk (TNFD) are the most material gaps for EU LPs.",
    ),

    InstitutionProfile(
        slug="carlyle", name="The Carlyle Group", region="North America",
        country="US", institution_type="Private Equity",
        assets_usd_bn=426,  # Total AUM
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.carlyle.com/our-firm/environmental-social-governance",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["TCFD (comprehensive)", "EDCI (ESG Data Convergence Initiative)", "ILPA ESG Template"],
        scores={
            "tcfd_governance": 75, "tcfd_strategy": 72, "tcfd_risk_mgmt": 70, "tcfd_metrics": 72,
            "issb_s1": 58, "issb_s2": 62,
            "esrs_e1": 20, "esrs_env_other": 15, "esrs_social": 58, "esrs_governance": 68,
            "double_materiality": 35,
            "pcaf_financed": 40, "scope3_cat15": 38,
            "paris_alignment": 55, "transition_plan": 52,
            "physical_risk": 65, "scenario_analysis": 60,
            "tnfd_nature": 32,
        },
        key_strengths=[
            "EDCI member — consistent ESG reporting across PE portfolio companies",
            "Renewable energy and infrastructure platform: green energy transitions a key strategy",
            "TCFD comprehensive: board-level climate oversight and risk committee",
            "Portfolio company carbon accounting: Scope 1+2 for 80%+ of buyout companies",
            "Diverse AUM: 500+ portfolio companies provides data on transition across industries",
        ],
        priority_gaps=[
            "PCAF financed emissions: not adopted for PE — significant gap for European LP base",
            "Net zero: 2050 target without published interim milestones",
            "TNFD: no formal biodiversity supporter status or LEAP conducted",
            "Climate scenario analysis: portfolio-level NGFS analysis not published",
            "Scope 3 portfolio: supply chain and product emissions for PE companies not disclosed",
            "Just transition: workforce impact across portfolio for operational emissions-intensive companies",
        ],
        analyst_note="Carlyle is a mid-tier PE firm on climate disclosure relative to global peers. "
                     "EDCI membership and TCFD adoption are solid. PCAF financed emissions and TNFD "
                     "nature adoption are the key gaps for EU-domiciled LPs with Paris-aligned mandates.",
    ),

    InstitutionProfile(
        slug="blackstone", name="Blackstone Inc.", region="North America",
        country="US", institution_type="Private Equity / Real Assets",
        assets_usd_bn=1100,  # Total AUM
        listed=True, exchange="NYSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=None, financed_sectors_nzba=0,
        report_url="https://www.blackstone.com/our-impact/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (partial)"],
        voluntary_frameworks=["EDCI (ESG Data Convergence Initiative)", "GRESB (real estate/infrastructure)", "CDP (partial)"],
        scores={
            "tcfd_governance": 62, "tcfd_strategy": 58, "tcfd_risk_mgmt": 55, "tcfd_metrics": 58,
            "issb_s1": 45, "issb_s2": 48,
            "esrs_e1": 15, "esrs_env_other": 12, "esrs_social": 50, "esrs_governance": 62,
            "double_materiality": 25,
            "pcaf_financed": 32, "scope3_cat15": 28,
            "paris_alignment": 38, "transition_plan": 35,
            "physical_risk": 58, "scenario_analysis": 50,
            "tnfd_nature": 22,
        },
        key_strengths=[
            "World's largest alternative asset manager — real estate GRESB participation industry-leading",
            "Data centre and logistics: energy efficiency commitments (100% renewable electricity target)",
            "EDCI member — portfolio company ESG data collection programme",
            "Real estate: GRESB Green Stars for flagship real estate funds",
            "Scale: leverage to drive ESG improvements across 250+ portfolio companies",
        ],
        priority_gaps=[
            "No net zero target — significant gap vs. all other top PE firms",
            "TCFD: partial only — strategy and risk management pillars incomplete",
            "PCAF financed emissions: not adopted despite large real estate and infrastructure AUM",
            "TNFD: nature dependencies in real estate, data centres, logistics not assessed",
            "Climate scenario analysis: not published at portfolio or fund level",
            "Data centre energy: hyperscale data centre acquisition creating material scope 2 risk",
            "Anti-ESG US political positioning creating European LP tension",
        ],
        analyst_note="Blackstone is the world's largest PE firm and the most significant laggard on "
                     "climate disclosure among top-5 PE managers. No net zero target and partial TCFD "
                     "are glaring gaps. Real estate GRESB and data centre energy are the most material "
                     "ESG issues for European LPs. Political pressure is driving anti-ESG posture.",
    ),

    InstitutionProfile(
        slug="partners_group", name="Partners Group AG", region="Europe",
        country="Switzerland", institution_type="Private Equity / Private Markets",
        assets_usd_bn=149,  # AUM
        listed=True, exchange="SIX Swiss Exchange",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.partnersgroup.com/en/responsibility/sustainability",
        mandatory_frameworks=["CSRD (Switzerland alignment)", "TCFD (comprehensive)", "SFDR (EU funds)", "Swiss Climate Disclosure (FINMA)"],
        voluntary_frameworks=["PCAF (member)", "TNFD (supporter)", "NZAMI (member)", "ISSB S2 (aligned)", "GRI Standards", "UN PRI"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82, "tcfd_metrics": 85,
            "issb_s1": 78, "issb_s2": 82,
            "esrs_e1": 48, "esrs_env_other": 35, "esrs_social": 68, "esrs_governance": 80,
            "double_materiality": 62,
            "pcaf_financed": 72, "scope3_cat15": 68,
            "paris_alignment": 78, "transition_plan": 75,
            "physical_risk": 80, "scenario_analysis": 78,
            "tnfd_nature": 58,
        },
        key_strengths=[
            "European PE benchmark — PCAF financed emissions leader for private markets",
            "SFDR Article 8/9 across full fund range — EU regulatory leadership",
            "Swiss FINMA climate disclosure: most advanced jurisdiction for private markets sustainability",
            "TNFD supporter: real assets biodiversity quantification under development",
            "NZAMI member: portfolio decarbonisation commitment with 2030 interim targets",
            "UN PRI A+ rated: highest private markets stewardship score",
        ],
        priority_gaps=[
            "TNFD LEAP: infrastructure and real estate nature risk formal disclosure not yet published",
            "Scope 3 portfolio companies: comprehensive upstream/downstream still incomplete",
            "Emerging markets PE: India, Brazil portfolio data quality variable",
            "Private credit: PCAF methodology for direct lending not yet fully applied",
            "Double materiality: impact materiality for PE portfolio companies — work in progress",
        ],
        analyst_note="Partners Group is the European benchmark for private markets sustainability "
                     "disclosure. Swiss regulatory environment + SFDR + PCAF + NZAMI creates the "
                     "most demanding disclosure framework among global PE firms. EU LP base and "
                     "Swiss listing drive higher standards than US-listed peers.",
    ),

    # ─── Insurance ────────────────────────────────────────────────────────────

    InstitutionProfile(
        slug="allianz", name="Allianz SE", region="Europe",
        country="Germany", institution_type="Insurance & Asset Management",
        assets_usd_bn=1050,  # investments
        listed=True, exchange="Frankfurt (DAX)",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.allianz.com/en/sustainability.html",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "Solvency II Climate Risk (EIOPA)", "SFDR (investment arm)"],
        voluntary_frameworks=["PCAF (member)", "NZAOA (founding member)", "TNFD (supporter)", "ISSB S2 (aligned)", "CDP A", "PSI (UN Principles for Sustainable Insurance)"],
        scores={
            "tcfd_governance": 92, "tcfd_strategy": 90, "tcfd_risk_mgmt": 88, "tcfd_metrics": 90,
            "issb_s1": 85, "issb_s2": 88,
            "esrs_e1": 72, "esrs_env_other": 55, "esrs_social": 75, "esrs_governance": 85,
            "double_materiality": 72,
            "pcaf_financed": 82, "scope3_cat15": 80,
            "paris_alignment": 85, "transition_plan": 82,
            "physical_risk": 92, "scenario_analysis": 90,
            "tnfd_nature": 62,
        },
        key_strengths=[
            "NZAOA founding member: Net Zero Asset Owners Alliance — gold standard for insurer investment",
            "CSRD early adopter — ESRS E1 full suite with physical risk integration in Solvency II",
            "Physical risk leader: natural catastrophe modelling drives insurance underwriting — data advantage",
            "PCAF member: investment portfolio financed emissions with external assurance",
            "CDP A-rated — 10-year consecutive A rating for climate disclosure",
            "PSI: UN Principles for Sustainable Insurance signatory — ESG in underwriting criteria",
        ],
        priority_gaps=[
            "Insurance underwriting Scope 3: premiums from fossil fuel/aviation underwriting not in PCAF",
            "TNFD: underwriting nature-related risks (biodiversity loss) not formally assessed",
            "Just transition: coal underwriting phase-out timeline and community disclosure",
            "Cyber: climate risk x cyber risk (physical infrastructure) emerging interdependency",
            "Liability risk: transition litigation exposure from directors & officers for investees",
        ],
        analyst_note="Allianz is the global benchmark for insurance/asset management climate disclosure. "
                     "NZAOA founding membership, CDP A, Solvency II physical risk, and CSRD together "
                     "create the most comprehensive insurance group climate disclosure globally. "
                     "TNFD nature in underwriting and insurance Scope 3 are the critical next frontiers.",
    ),

    InstitutionProfile(
        slug="munich_re", name="Munich Re Group", region="Europe",
        country="Germany", institution_type="Reinsurance",
        assets_usd_bn=290,  # investments
        listed=True, exchange="Frankfurt (DAX)",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.munichre.com/en/company/media-relations/publications/sustainability-report.html",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "Solvency II (EIOPA)", "German CBAM"],
        voluntary_frameworks=["PCAF (member)", "NZAOA (member)", "TNFD (supporter)", "CDP A", "PSI", "GRI Standards"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 92, "tcfd_risk_mgmt": 90, "tcfd_metrics": 92,
            "issb_s1": 85, "issb_s2": 90,
            "esrs_e1": 70, "esrs_env_other": 55, "esrs_social": 72, "esrs_governance": 82,
            "double_materiality": 70,
            "pcaf_financed": 80, "scope3_cat15": 78,
            "paris_alignment": 82, "transition_plan": 80,
            "physical_risk": 95, "scenario_analysis": 92,
            "tnfd_nature": 60,
        },
        key_strengths=[
            "World's leading reinsurer — NatCat data and climate risk modelling is best-in-class globally",
            "Physical risk: climate change economic loss modelling (trillion-dollar dataset) unmatched",
            "CSRD early adopter — ESRS E1 with Scope 1+2+3 including reinsurance underwriting",
            "CDP A-rated: joint-top with Allianz for insurance disclosure quality",
            "PCAF member: investment portfolio and reinsurance underwriting GHG methodology",
            "TNFD supporter: ecosystem services dependencies in NatCat modelling",
        ],
        priority_gaps=[
            "Reinsurance Scope 3: premiums from fossil fuel/aviation reinsurance — PCAF methodology nascent",
            "TNFD: biodiversity loss as systemic risk to NatCat loss frequency not fully formalised",
            "Transition risk in property: flood and wildfire-driven uninsurability in CRREM pathways",
            "Emerging markets: reinsurance exposure in India, Southeast Asia physical risk disclosure",
            "Agricultural reinsurance: weather derivative and crop insurance climate scenario analysis",
        ],
        analyst_note="Munich Re is the world's most important climate risk organisation — its NatCat "
                     "data and physical risk modelling are the foundation of the global insurance industry. "
                     "Disclosure quality is co-equal with Allianz. Reinsurance Scope 3 and TNFD nature "
                     "as systemic NatCat risk driver are the next frontiers.",
    ),

    InstitutionProfile(
        slug="zurich_insurance", name="Zurich Insurance Group", region="Europe",
        country="Switzerland", institution_type="Insurance",
        assets_usd_bn=220,  # investments
        listed=True, exchange="SIX Swiss Exchange",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.zurich.com/en/sustainability",
        mandatory_frameworks=["CSRD (2024 — EU subsidiaries)", "TCFD (comprehensive)", "Swiss FINMA Climate", "Solvency II (EIOPA)"],
        voluntary_frameworks=["PCAF (member)", "NZAOA (member)", "TNFD (supporter)", "CDP A", "PSI", "ISSB S2 (aligned)", "GRI Standards"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 80, "issb_s2": 85,
            "esrs_e1": 65, "esrs_env_other": 50, "esrs_social": 72, "esrs_governance": 82,
            "double_materiality": 68,
            "pcaf_financed": 78, "scope3_cat15": 75,
            "paris_alignment": 80, "transition_plan": 78,
            "physical_risk": 88, "scenario_analysis": 85,
            "tnfd_nature": 58,
        },
        key_strengths=[
            "Swiss regulatory leader: FINMA climate risk disclosure most advanced globally for insurers",
            "NZAOA member: net zero investment portfolio commitment with interim 2025/2030 targets",
            "PCAF: investment portfolio financed emissions with external assurance",
            "PSI: underwriting exclusions (coal, oil sands) operationalised with timeline",
            "CDP A-rated: consistent top-tier climate disclosure",
            "FloodResilience program: $10mn investment in community flood prevention (TNFD-linked)",
        ],
        priority_gaps=[
            "Underwriting Scope 3: fossil fuel premium income — PCAF extended scope not yet applied",
            "TNFD LEAP: formal biodiversity dependency assessment for underwriting book not published",
            "Double materiality: Swiss standard is strong but ESRS DMA not completed for all subsidiaries",
            "Emerging markets: Latin America and Asia Pacific underwriting climate exposure disclosure",
            "Climate litigation: D&O exposure from transition risk lawsuits against portfolio companies",
        ],
        analyst_note="Zurich is the Swiss benchmark for insurance climate disclosure — FINMA climate "
                     "framework, NZAOA, PCAF, and CDP A together represent the global standard. "
                     "Underwriting Scope 3 (fossil fuel premiums) and TNFD nature (biodiversity loss "
                     "as systemic insurance risk) are the most material disclosure frontiers.",
    ),

    InstitutionProfile(
        slug="swiss_re", name="Swiss Re Ltd.", region="Europe",
        country="Switzerland", institution_type="Reinsurance",
        assets_usd_bn=195,  # investments
        listed=True, exchange="SIX Swiss Exchange",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.swissre.com/sustainability.html",
        mandatory_frameworks=["CSRD (EU subsidiaries)", "TCFD (comprehensive)", "Swiss FINMA Climate", "Solvency II"],
        voluntary_frameworks=["PCAF (member)", "NZAOA (member)", "TNFD (supporter)", "CDP A", "PSI", "ISSB S2 (aligned)", "Taskforce on Nature-related Financial Disclosures (steering)"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 90, "tcfd_risk_mgmt": 88, "tcfd_metrics": 90,
            "issb_s1": 85, "issb_s2": 88,
            "esrs_e1": 68, "esrs_env_other": 52, "esrs_social": 70, "esrs_governance": 82,
            "double_materiality": 72,
            "pcaf_financed": 82, "scope3_cat15": 80,
            "paris_alignment": 85, "transition_plan": 82,
            "physical_risk": 92, "scenario_analysis": 90,
            "tnfd_nature": 68,
        },
        key_strengths=[
            "TNFD steering group member: co-designing nature-related financial disclosure framework",
            "Ecosystem services valuation: biodiversity economic value integrated in NatCat models",
            "PCAF: reinsurance treaty underwriting emissions — industry's most advanced methodology",
            "Net zero 2050 (investment + re/insurance operations): most comprehensive insurer scope",
            "Economics of Climate Change research: annually updated physical risk pricing publication",
            "Coal exclusion: 100% coal reinsurance exclusion by 2030",
        ],
        priority_gaps=[
            "TNFD LEAP: formal asset-level biodiversity impact assessment not yet published",
            "Agricultural reinsurance: crop failure and biodiversity loss dependency formalisation",
            "Emerging market nat cat: physical risk in Southeast Asia and LATAM not at global reinsurance scale",
            "Double materiality: combined financial + impact materiality not formally completed to ESRS standard",
            "Social: just transition in reinsurance markets (Pacific island states) climate loss allocation",
        ],
        analyst_note="Swiss Re is joint-top with Munich Re as the world's most important climate risk "
                     "knowledge organisation. TNFD steering group and reinsurance PCAF methodology are "
                     "genuinely industry-leading. The biodiversity-NatCat loss frequency nexus is the "
                     "most important systemic risk concept Swiss Re is pioneering.",
    ),

    InstitutionProfile(
        slug="axa", name="AXA S.A.", region="Europe",
        country="France", institution_type="Insurance & Asset Management",
        assets_usd_bn=870,  # investments
        listed=True, exchange="Euronext Paris (SBF 120)",
        nzba_member=False, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.axa.com/en/about-axa/climate-report",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "SFDR (investment arm)", "French DPEF", "Solvency II"],
        voluntary_frameworks=["PCAF (member)", "NZAOA (founding member)", "TNFD (supporter)", "CDP A", "PSI", "GRI Standards", "Climate Action 100+"],
        scores={
            "tcfd_governance": 92, "tcfd_strategy": 90, "tcfd_risk_mgmt": 88, "tcfd_metrics": 90,
            "issb_s1": 85, "issb_s2": 90,
            "esrs_e1": 75, "esrs_env_other": 58, "esrs_social": 78, "esrs_governance": 85,
            "double_materiality": 75,
            "pcaf_financed": 85, "scope3_cat15": 82,
            "paris_alignment": 88, "transition_plan": 85,
            "physical_risk": 90, "scenario_analysis": 88,
            "tnfd_nature": 65,
        },
        key_strengths=[
            "NZAOA founding member — co-designed net zero asset owner standard",
            "CSRD early adopter: ESRS E1-G1 with KPMG assurance — global insurance disclosure benchmark",
            "French DPEF + SFDR: dual French/EU mandatory climate reporting — deepest regulatory stack",
            "PCAF member: investment and underwriting emissions — most advanced insurer PCAF scope",
            "CDP A-rated: 8 consecutive years — most consistent insurer disclosure quality",
            "AXA Climate: dedicated subsidiary for climate risk consulting and advisory",
        ],
        priority_gaps=[
            "Insurance underwriting Scope 3: oil & gas premium income — PCAF underwriting methodology evolving",
            "TNFD LEAP: biodiversity in agricultural insurance and real asset AUM",
            "Emerging markets: Asia Pacific and LATAM operations with variable disclosure quality",
            "Climate litigation: D&O exposure from fossil fuel company transition failures",
            "Just transition in insurance: access to insurance in climate-stressed communities",
        ],
        analyst_note="AXA is co-equal with Allianz as the global benchmark for insurance/asset "
                     "management climate disclosure. French regulatory environment (DPEF, SFDR), "
                     "NZAOA, PCAF, and CSRD together create the richest climate disclosure framework "
                     "of any insurer worldwide. AXA Climate subsidiary creates commercial advantage.",
    ),

    # ─── Climate-Focused Venture Capital ─────────────────────────────────────

    InstitutionProfile(
        slug="breakthrough_energy", name="Breakthrough Energy Ventures", region="North America",
        country="US", institution_type="Climate Venture Capital",
        assets_usd_bn=3,  # AUM
        listed=False, exchange=None,
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=None, financed_sectors_nzba=0,
        report_url="https://www.breakthroughenergy.org/our-approach/our-progress",
        mandatory_frameworks=["SEC GHG Disclosure (stayed — PE exempt)"],
        voluntary_frameworks=["TCFD (partial)", "ISSB S2 (partial alignment)", "Impact metrics: tCO₂e avoided"],
        scores={
            "tcfd_governance": 72, "tcfd_strategy": 85, "tcfd_risk_mgmt": 65, "tcfd_metrics": 75,
            "issb_s1": 55, "issb_s2": 62,
            "esrs_e1": 15, "esrs_env_other": 12, "esrs_social": 40, "esrs_governance": 58,
            "double_materiality": 45,
            "pcaf_financed": 35, "scope3_cat15": 30,
            "paris_alignment": 88, "transition_plan": 85,
            "physical_risk": 55, "scenario_analysis": 65,
            "tnfd_nature": 32,
        },
        key_strengths=[
            "Bill Gates-backed — $3bn fund, investment mandate IS the climate solution universe",
            "Paris alignment by design: every investment targets ≥500 million tCO₂e reduction/year potential",
            "Portfolio impact: annual tCO₂e avoided per dollar invested is the primary KPI",
            "Technology leadership: H2, long-duration storage, green steel, direct air capture pipeline",
            "Policy influence: governments and multilaterals engaged on technology cost curves",
        ],
        priority_gaps=[
            "PCAF methodology for VC not yet applied — financed emissions not computed",
            "TCFD: partial only — risk management and metrics pillars less developed than strategy",
            "Social: just transition in portfolio company workforce — early stage limited disclosure",
            "TNFD: nature impact of portfolio technologies (land use, water for H2/solar) not assessed",
            "Exit: sustainability performance and GHG trajectory post-exit not tracked",
        ],
        analyst_note="Breakthrough Energy Ventures is the world's most important climate VC. "
                     "Its investment thesis is pure climate impact — every dollar targeting massively "
                     "scalable technologies. Standard financial ESG disclosure frameworks (PCAF, TNFD) "
                     "are poorly suited to early-stage climate tech — the key metric is tCO₂e avoided "
                     "per investment dollar, which BEV publishes.",
    ),

    InstitutionProfile(
        slug="congruent_ventures", name="Congruent Ventures", region="North America",
        country="US", institution_type="Climate Venture Capital",
        assets_usd_bn=0.8,  # AUM ~$800mn
        listed=False, exchange=None,
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=None, financed_sectors_nzba=0,
        report_url="https://www.congruentvc.com/impact",
        mandatory_frameworks=["SEC GHG Disclosure (stayed — PE exempt)"],
        voluntary_frameworks=["ISSB S2 (partial)", "EDCI-aligned impact metrics", "GIIRS Impact Rating"],
        scores={
            "tcfd_governance": 60, "tcfd_strategy": 78, "tcfd_risk_mgmt": 55, "tcfd_metrics": 65,
            "issb_s1": 45, "issb_s2": 55,
            "esrs_e1": 10, "esrs_env_other": 10, "esrs_social": 45, "esrs_governance": 55,
            "double_materiality": 38,
            "pcaf_financed": 22, "scope3_cat15": 18,
            "paris_alignment": 82, "transition_plan": 78,
            "physical_risk": 45, "scenario_analysis": 52,
            "tnfd_nature": 28,
        },
        key_strengths=[
            "Equity, Justice, Climate mandate: only major climate VC integrating justice and equity into thesis",
            "GIIRS impact rating: B Corp aligned investment criteria",
            "Focus on underrepresented founders and climate-justice communities",
            "Portfolio: cleantech, sustainable food, circular economy — breadth across transition sectors",
            "Annual Impact Report: tCO₂e avoided, jobs created, equity metrics",
        ],
        priority_gaps=[
            "Scale: $800mn AUM — significantly smaller than Breakthrough Energy or Lowercarbon",
            "PCAF: financed emissions methodology for VC seed/series A not applied",
            "TCFD: strategy pillar strong but risk/metrics pillars need development",
            "Portfolio company disclosure: early-stage companies have minimal sustainability reporting",
        ],
        analyst_note="Congruent is the ESG/impact leader among sub-$1bn climate VC funds. "
                     "Equity and justice integration into climate thesis is unique. GIIRS rating "
                     "and annual impact report set the benchmark for smaller climate-focused VCs. "
                     "Scale is the primary constraint vs. BEV or Lowercarbon.",
    ),

    InstitutionProfile(
        slug="lowercarbon", name="Lowercarbon Capital", region="North America",
        country="US", institution_type="Climate Venture Capital",
        assets_usd_bn=1.2,  # AUM
        listed=False, exchange=None,
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=None, financed_sectors_nzba=0,
        report_url="https://lowercarboncapital.com/companies",
        mandatory_frameworks=["SEC GHG Disclosure (stayed — PE exempt)"],
        voluntary_frameworks=["ISSB S2 (partial)", "Carbon-negative investment mandate"],
        scores={
            "tcfd_governance": 62, "tcfd_strategy": 82, "tcfd_risk_mgmt": 55, "tcfd_metrics": 68,
            "issb_s1": 45, "issb_s2": 58,
            "esrs_e1": 10, "esrs_env_other": 10, "esrs_social": 38, "esrs_governance": 52,
            "double_materiality": 35,
            "pcaf_financed": 25, "scope3_cat15": 20,
            "paris_alignment": 90, "transition_plan": 85,
            "physical_risk": 42, "scenario_analysis": 55,
            "tnfd_nature": 25,
        },
        key_strengths=[
            "Carbon negative mandate: only invest in technologies that can remove ≥1 Gt CO₂/year at scale",
            "Direct air capture, ocean-based CDR, enhanced weathering — most radical climate tech portfolio",
            "Founders-first: Chris Sacca's Silicon Valley network accelerates portfolio company growth",
            "Portfolio includes some of the most capital-efficient CDR companies globally (Heirloom, etc.)",
            "Speed: seed-to-series A in carbon removal — fastest deployment of climate capital",
        ],
        priority_gaps=[
            "Traditional ESG disclosure: PCAF, TCFD, TNFD not yet applied — non-standard metrics",
            "Social disclosure: workforce and community impact of CDR technology deployment",
            "TNFD: land use, water and biodiversity of enhanced weathering and direct air capture at scale",
            "Scale: $1.2bn AUM — BEV and TPG Rise are 5x+ larger",
            "Exit: portfolio company sustainability trajectory post-exit not tracked",
        ],
        analyst_note="Lowercarbon is the most radical climate VC — carbon negative mandate means "
                     "the entire portfolio is 1.5°C-aligned by design. Traditional ESG disclosure "
                     "frameworks are poorly suited to CDR venture investing — Lowercarbon's own "
                     "impact framework (Gt removed, $ per tonne) is the relevant metric.",
    ),

    # ─── Technology Companies ─────────────────────────────────────────────────

    InstitutionProfile(
        slug="microsoft", name="Microsoft Corporation", region="North America",
        country="US", institution_type="Technology",
        assets_usd_bn=485,
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://www.microsoft.com/en-us/corporate-responsibility/sustainability/report",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)", "EU Taxonomy (some EU operations)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTI (1.5°C)", "TNFD (supporter)", "RE100", "CDP A", "Science Based Targets for Nature (SBTN pilot)"],
        scores={
            "tcfd_governance": 92, "tcfd_strategy": 90, "tcfd_risk_mgmt": 88, "tcfd_metrics": 90,
            "issb_s1": 88, "issb_s2": 90,
            "esrs_e1": 45, "esrs_env_other": 38, "esrs_social": 75, "esrs_governance": 85,
            "double_materiality": 62,
            "pcaf_financed": 12, "scope3_cat15": 10,
            "paris_alignment": 88, "transition_plan": 85,
            "physical_risk": 82, "scenario_analysis": 85,
            "tnfd_nature": 65,
        },
        key_strengths=[
            "Carbon negative by 2030, water positive by 2030, zero waste by 2030 — most ambitious targets",
            "CDP A-rated — 8 consecutive years — tech sector's most consistent disclosure",
            "RE100 + PPAs: 100% renewable electricity globally (matching basis)",
            "SBTN Nature pilot: water replenishment and biodiversity positive commitments",
            "AI for sustainability: climate AI investment ($1bn Climate Innovation Fund)",
            "Scope 3 Cat 11 (Azure cloud/software emissions): disclosed and targeted — industry first",
        ],
        priority_gaps=[
            "AI energy: GPT-4/Copilot inference workloads creating material Scope 2 escalation",
            "Supply chain Scope 3 Cat 1/2: hardware and data centre construction supply chain",
            "TNFD LEAP: formal biodiversity dependency for data centre land use and water not published",
            "Double materiality: impact on society from AI systems (S1 digital rights) not in ESRS scope",
            "Physical risk: data centre concentration risk (natural disasters) at portfolio level",
        ],
        analyst_note="Microsoft is the global technology benchmark for climate disclosure. Carbon negative "
                     "2030 target, CDP A, SBTN water, and AI climate investment are genuinely "
                     "differentiated. AI energy escalation (GPT-4 inference) is the most material "
                     "emerging risk — Microsoft has acknowledged this and is the only hyperscaler "
                     "publishing AI-specific GHG methodology.",
    ),

    InstitutionProfile(
        slug="apple", name="Apple Inc.", region="North America",
        country="US", institution_type="Technology",
        assets_usd_bn=375,
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://www.apple.com/environment/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTI (1.5°C)", "RE100", "CDP A", "SASB Technology Hardware"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 82, "issb_s2": 85,
            "esrs_e1": 42, "esrs_env_other": 35, "esrs_social": 70, "esrs_governance": 82,
            "double_materiality": 55,
            "pcaf_financed": 8, "scope3_cat15": 6,
            "paris_alignment": 85, "transition_plan": 82,
            "physical_risk": 78, "scenario_analysis": 80,
            "tnfd_nature": 42,
        },
        key_strengths=[
            "Supply chain Scope 3 leader: 200+ suppliers committed to renewable energy through Supplier Clean Energy Programme",
            "Carbon neutral operations since 2020 — products by 2030",
            "RE100: 100% renewable electricity in Apple-operated facilities globally",
            "Material recovery: closed-loop recycling for 20+ materials; Daisy robot for iPhone disassembly",
            "CDP A-rated: consistent top-tier disclosure with product lifecycle emphasis",
            "iOS/macOS energy efficiency: device power management reduces user-phase emissions",
        ],
        priority_gaps=[
            "Scope 3 Cat 11: product use-phase emissions — iPhone and Mac lifetime energy use methodology",
            "TNFD: conflict minerals (coltan, cobalt, lithium) supply chain biodiversity impact",
            "Double materiality: App Store and digital platform social impact (S3 user wellbeing)",
            "ISSB S1: general sustainability risk disclosure less developed than climate (S2)",
            "China manufacturing: Scope 3 Cat 1 Taiwan/China supply chain emissions growing",
        ],
        analyst_note="Apple is the global benchmark for consumer technology climate disclosure. "
                     "Supply chain Scope 3 supplier programme is industry-leading — 200+ suppliers "
                     "in clean energy commitment. Carbon neutral products by 2030 requires Scope 3 "
                     "Cat 11 methodology innovation that Apple is pioneering. TNFD conflict minerals "
                     "and digital rights are the most material undisclosed ESG risks.",
    ),

    InstitutionProfile(
        slug="alphabet", name="Alphabet Inc. (Google)", region="North America",
        country="US", institution_type="Technology",
        assets_usd_bn=430,
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://sustainability.google/reports/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTI (1.5°C)", "TNFD (supporter)", "RE100 (24/7 CFE)", "CDP A"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 80, "issb_s2": 85,
            "esrs_e1": 40, "esrs_env_other": 32, "esrs_social": 68, "esrs_governance": 78,
            "double_materiality": 52,
            "pcaf_financed": 10, "scope3_cat15": 8,
            "paris_alignment": 85, "transition_plan": 82,
            "physical_risk": 80, "scenario_analysis": 82,
            "tnfd_nature": 55,
        },
        key_strengths=[
            "24/7 Carbon-Free Energy (CFE) by 2030 — most ambitious renewable electricity standard globally",
            "Carbon neutral since 2007; net zero by 2030 (Scope 1+2+3) — industry's earliest commitments",
            "Google AI for climate: AI applied to GHG inventory, wildfire mapping, flood forecasting",
            "TNFD supporter: biodiversity mapping using Google Earth Engine data",
            "CDP A-rated: consistent top-tier; water and forest stewardship also A-rated",
            "Supply chain: Google environmental requirements embedded in top-100 suppliers",
        ],
        priority_gaps=[
            "AI energy: data centre power consumption growing 20%+/year from generative AI training",
            "Water: data centre water consumption increasing — 24/7 CFE requires cooling water",
            "TNFD LEAP: formal biodiversity assessment for 23 data centre campuses globally",
            "Scope 3 Cat 11: Android device and Pixel lifetime emissions — lifecycle methodology",
            "Double materiality: AI platform societal impact (misinformation, privacy) — ESRS S4 equivalent",
        ],
        analyst_note="Google is the technology sector's most innovative climate disclosure company. "
                     "24/7 CFE is the most demanding renewable electricity standard globally. "
                     "AI climate tools (wildfire, flood) and Earth Engine biodiversity data are "
                     "unique assets. AI energy escalation (LLM training/inference) is the most "
                     "material emerging risk — Google has been the most transparent about this.",
    ),

    InstitutionProfile(
        slug="amazon", name="Amazon.com Inc.", region="North America",
        country="US", institution_type="Technology / E-Commerce",
        assets_usd_bn=465,
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://sustainability.aboutamazon.com/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["ISSB S2 (partial alignment)", "SBTI (1.5°C — submitted)", "RE100", "CDP B", "Climate Pledge (Amazon founder)"],
        scores={
            "tcfd_governance": 80, "tcfd_strategy": 78, "tcfd_risk_mgmt": 72, "tcfd_metrics": 75,
            "issb_s1": 65, "issb_s2": 70,
            "esrs_e1": 28, "esrs_env_other": 22, "esrs_social": 55, "esrs_governance": 65,
            "double_materiality": 38,
            "pcaf_financed": 8, "scope3_cat15": 6,
            "paris_alignment": 75, "transition_plan": 72,
            "physical_risk": 68, "scenario_analysis": 65,
            "tnfd_nature": 30,
        },
        key_strengths=[
            "The Climate Pledge: commitments from 400+ companies to net zero by 2040 — broader than Paris",
            "Largest corporate renewable energy purchaser globally: 100+ GW of wind and solar PPAs",
            "Right Now Climate Fund: $100mn for nature-based solutions",
            "AWS Sustainability: customers' GHG reduction through cloud migration quantified",
            "Delivery decarbonisation: 100,000 Rivian electric delivery vehicles ordered",
        ],
        priority_gaps=[
            "CDP B only: significantly below Apple, Google, Microsoft (all CDP A) on climate disclosure",
            "Scope 3: last-mile delivery and packaging supply chain Scope 3 disclosure incomplete",
            "TNFD: Amazon deforestation linkage (name/brand) creates material reputational risk",
            "Physical risk: AWS data centre physical climate risk by region not published",
            "Double materiality: labour rights in warehousing and delivery — S1 worker safety",
            "ISSB S1: general sustainability disclosure less developed than climate-focused peers",
            "Water: data centre cooling water consumption by location not disclosed",
        ],
        analyst_note="Amazon is the largest corporate renewable energy buyer globally but lags peers "
                     "on climate disclosure quality (CDP B vs. A for Microsoft/Google/Apple). "
                     "The TNFD Amazon deforestation brand risk is the most unusual ESG exposure "
                     "of any tech company. AWS energy and Scope 3 supply chain are the key gaps.",
    ),

    InstitutionProfile(
        slug="meta", name="Meta Platforms Inc.", region="North America",
        country="US", institution_type="Technology",
        assets_usd_bn=232,
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://sustainability.fb.com/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTI (1.5°C)", "RE100", "CDP A", "Water positive (2030)"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 80, "tcfd_metrics": 82,
            "issb_s1": 75, "issb_s2": 78,
            "esrs_e1": 35, "esrs_env_other": 28, "esrs_social": 55, "esrs_governance": 68,
            "double_materiality": 38,
            "pcaf_financed": 8, "scope3_cat15": 6,
            "paris_alignment": 78, "transition_plan": 75,
            "physical_risk": 72, "scenario_analysis": 70,
            "tnfd_nature": 32,
        },
        key_strengths=[
            "CDP A-rated: consistent top-tier climate disclosure despite corporate controversies",
            "RE100: 100% renewable electricity (matching basis) since 2020",
            "Net zero 2030: Scope 1+2+3 — aggressive timeline for hyperscaler",
            "Water positive by 2030: data centre water restoration commitment",
            "Custom silicon (MTIA): AI chip design for energy efficiency — reducing AI energy intensity",
        ],
        priority_gaps=[
            "AI energy: Llama/LLM training and inference — among fastest-growing data centre loads",
            "S1 workforce: content moderation and mental health impact of platform — material ESRS S4",
            "TNFD: formal biodiversity assessment absent despite significant data centre land use",
            "Double materiality: platform societal impact (misinformation, addiction) not in climate scope",
            "Scope 3: digital advertising supply chain emissions — category methodology developing",
            "Water: data centre cooling water — location-specific water stress disclosure",
        ],
        analyst_note="Meta's climate disclosure quality is strong (CDP A, RE100, net zero 2030) "
                     "but the platform's core social externalities (mental health, misinformation) "
                     "are becoming as material as climate. The tension between ESRS S4 (user wellbeing) "
                     "and Meta's business model is a unique ESG risk not captured in any climate framework.",
    ),

    InstitutionProfile(
        slug="nvidia", name="NVIDIA Corporation", region="North America",
        country="US", institution_type="Technology (Semiconductors / AI)",
        assets_usd_bn=65,
        listed=True, exchange="NASDAQ",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2025, financed_sectors_nzba=0,
        report_url="https://www.nvidia.com/en-us/csr/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTI (1.5°C)", "RE100", "CDP A-"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 80, "tcfd_risk_mgmt": 78, "tcfd_metrics": 80,
            "issb_s1": 70, "issb_s2": 75,
            "esrs_e1": 30, "esrs_env_other": 25, "esrs_social": 60, "esrs_governance": 72,
            "double_materiality": 42,
            "pcaf_financed": 5, "scope3_cat15": 4,
            "paris_alignment": 72, "transition_plan": 70,
            "physical_risk": 65, "scenario_analysis": 62,
            "tnfd_nature": 28,
        },
        key_strengths=[
            "Operations net zero 2025 — own emissions target ahead of most hardware peers",
            "Energy efficiency innovation: H100/H200 GPUs deliver 3x more AI compute per watt vs. A100",
            "Scope 3 Cat 11 (product use): NVIDIA GPU energy consumption is customers' largest AI emission",
            "RE100: renewable electricity for owned operations",
            "CDP A-: improving climate disclosure quality with each annual cycle",
        ],
        priority_gaps=[
            "Scope 3 Cat 11: customer GPU energy consumption is the most material ESG metric for NVIDIA — partially disclosed",
            "AI energy impact: H100 cluster power consumption enables AI capabilities that increase total energy use",
            "Supply chain Scope 3 Cat 1: TSMC manufacturing Scope 1+2 intensity is NVIDIA's largest supply chain emission",
            "Water: TSMC foundry water consumption (Taiwan water stress) — Scope 3 Cat 1 water use",
            "TNFD: semiconductor manufacturing rare earth and tantalum supply chain biodiversity",
            "Double materiality: AI enabling surveillance capitalism, autonomous weapons — ESRS S4 equivalent",
        ],
        analyst_note="NVIDIA is the single most important company for AI energy trajectory globally. "
                     "H100/H200 GPU efficiency gains are partially offset by exponential deployment growth. "
                     "NVIDIA's Scope 3 Cat 11 (customer GPU energy) is effectively a proxy for global "
                     "AI GHG emissions — publishing this methodology would be industry-defining. "
                     "The dual-use (civilian AI vs. autonomous weapons) materiality is unique.",
    ),

    InstitutionProfile(
        slug="samsung", name="Samsung Electronics", region="Asia Pacific",
        country="South Korea", institution_type="Technology (Semiconductors / Consumer Electronics)",
        assets_usd_bn=330,
        listed=True, exchange="Korea Stock Exchange (KRX)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.samsung.com/global/sustainability/",
        mandatory_frameworks=["Korea ESG Disclosure (FSC Regulations)", "K-TCFD (Korean mandatory)", "K-ESG Guidelines"],
        voluntary_frameworks=["TCFD (comprehensive)", "ISSB S2 (aligned)", "TNFD (supporter)", "CDP B+", "RE100 (committed — target 2050)", "GRI Standards"],
        scores={
            "tcfd_governance": 80, "tcfd_strategy": 78, "tcfd_risk_mgmt": 75, "tcfd_metrics": 78,
            "issb_s1": 68, "issb_s2": 72,
            "esrs_e1": 28, "esrs_env_other": 25, "esrs_social": 62, "esrs_governance": 70,
            "double_materiality": 42,
            "pcaf_financed": 8, "scope3_cat15": 6,
            "paris_alignment": 65, "transition_plan": 62,
            "physical_risk": 70, "scenario_analysis": 68,
            "tnfd_nature": 40,
        },
        key_strengths=[
            "K-TCFD: Korea's mandatory TCFD adoption creates world's 2nd most comprehensive regulatory requirement",
            "Semiconductor energy efficiency: each generation of NAND/DRAM reduces energy intensity",
            "RE100 committed: 100% renewable electricity target with regional deployment roadmap",
            "TNFD supporter: semiconductor manufacturing supply chain biodiversity mapping",
            "Water stewardship: semiconductor fabs in water-stressed Korea — advanced water reuse",
        ],
        priority_gaps=[
            "RE100 timeline: 2050 target is 20+ years behind Microsoft, Apple, Google",
            "Scope 2: semiconductor fabs remain majority coal-powered in Korea — K-ETS coverage",
            "CDP B+: below global tech peers on climate disclosure (Apple, Google, Microsoft = CDP A)",
            "Scope 3: EUV lithography tool energy, customer device lifetime use — industry standard needed",
            "TNFD LEAP: semiconductor manufacturing water use in Korea and Vietnam (river basin stress)",
            "Just transition: Samsung Lee family governance and labour rights in Korean chaebol context",
        ],
        analyst_note="Samsung is the most important semiconductor manufacturer in Asia Pacific for "
                     "climate disclosure. K-TCFD mandatory framework drives good governance disclosure. "
                     "RE100 2050 timeline and coal-heavy Korean grid are the most material climate gaps. "
                     "Water use in semiconductor fabrication is a highly material physical risk.",
    ),

    InstitutionProfile(
        slug="tsmc", name="Taiwan Semiconductor Manufacturing Company (TSMC)", region="Asia Pacific",
        country="Taiwan", institution_type="Technology (Semiconductors)",
        assets_usd_bn=148,
        listed=True, exchange="TWSE / NYSE (ADR)",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://esg.tsmc.com/en/",
        mandatory_frameworks=["Taiwan FSC Sustainability Disclosure (mandatory)", "TCFD (comprehensive)", "Taiwan ESG Stewardship Principles"],
        voluntary_frameworks=["ISSB S2 (aligned)", "TNFD (supporter)", "RE100 (committed)", "CDP A-", "GRI Standards", "SASB Semiconductors"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 80, "tcfd_metrics": 82,
            "issb_s1": 75, "issb_s2": 78,
            "esrs_e1": 32, "esrs_env_other": 28, "esrs_social": 62, "esrs_governance": 72,
            "double_materiality": 48,
            "pcaf_financed": 5, "scope3_cat15": 4,
            "paris_alignment": 72, "transition_plan": 70,
            "physical_risk": 80, "scenario_analysis": 78,
            "tnfd_nature": 52,
        },
        key_strengths=[
            "CDP A-: among best-in-class for semiconductor manufacturers on climate",
            "Water stewardship: most advanced water reuse programme in global semiconductors (90%+ reuse)",
            "RE100 committed: renewable electricity roadmap with PPA contracts in Taiwan",
            "TNFD supporter: water and chemical use biodiversity impact in supply chain",
            "Physical risk: Taiwan typhoon and earthquake risk modelled for all fab locations",
            "Taiwan FSC mandatory: most comprehensive Asia Pacific mandatory ESG framework",
        ],
        priority_gaps=[
            "Scope 2: Taiwan grid is 80%+ fossil fuel — RE100 timeline 2050 creates multi-decade exposure",
            "Geopolitical risk: Taiwan Strait tension is the most material physical/transition risk — not in TCFD scope",
            "TNFD LEAP: water stress and chemical contamination from fab operations — formal LEAP needed",
            "Scope 3 Cat 11: TSMC's chips enable AI/data centres — contribution to AI GHG growth",
            "Water: Hsinchu Science Park water stress — Taiwan drought of 2021 revealed operational vulnerability",
            "Chemical: PFAS and other semiconductor fab chemicals — emerging environmental liability",
        ],
        analyst_note="TSMC is the world's most important company for AI/semiconductor transition. "
                     "Water stewardship programme is genuinely best-in-class globally. The Taiwan "
                     "water stress and geopolitical risk are the most material undisclosed ESG factors. "
                     "AI chip manufacture making TSMC a critical node in global AI energy trajectory.",
    ),

    InstitutionProfile(
        slug="sap", name="SAP SE", region="Europe",
        country="Germany", institution_type="Technology (Enterprise Software)",
        assets_usd_bn=68,
        listed=True, exchange="Frankfurt (DAX) / NYSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://www.sap.com/sustainability.html",
        mandatory_frameworks=["CSRD (2024)", "TCFD (comprehensive)", "German EnEfG (Energy Efficiency Act)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTI (1.5°C)", "TNFD (supporter)", "RE100", "CDP A", "GRI Standards", "SASB Software"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 85, "issb_s2": 88,
            "esrs_e1": 72, "esrs_env_other": 55, "esrs_social": 75, "esrs_governance": 85,
            "double_materiality": 72,
            "pcaf_financed": 8, "scope3_cat15": 6,
            "paris_alignment": 85, "transition_plan": 82,
            "physical_risk": 78, "scenario_analysis": 80,
            "tnfd_nature": 55,
        },
        key_strengths=[
            "CSRD early adopter — ESRS E1-G1 with full double materiality (German domicile)",
            "Net zero 2030 — most aggressive tech sector timeline including Scope 3",
            "Sustainability products: SAP Green Ledger and ESG Reporting enable client decarbonisation",
            "CDP A-rated: consistent top-tier; SAP data feeds many institutional ESG databases",
            "Double materiality: formally completed — one of the few tech companies with CSRD-grade DMA",
            "TNFD supporter: forest and water in data centre and employee commuting",
        ],
        priority_gaps=[
            "Scope 3 Cat 11: SAP software enabling customer GHG — lifecycle methodology underdeveloped",
            "TNFD LEAP: formal assessment for data centre land use and water not yet published",
            "Customer GHG enablement: SAP helps clients disclose — own methodology for this value unclear",
            "Emerging markets: SAP India, China operations Scope 2 data quality",
            "Supply chain: SAP hardware procurement embedded in Scope 3 Cat 1/2 methodology",
        ],
        analyst_note="SAP is Europe's most comprehensive enterprise software company on climate disclosure. "
                     "CSRD compliance with double materiality, net zero 2030, and SAP Green Ledger are "
                     "genuinely differentiated. SAP is unique in that its core products (ERP/ESG "
                     "reporting software) directly enable its clients' sustainability disclosures — "
                     "making SAP a critical enabler of the global corporate ESG reporting stack.",
    ),

    InstitutionProfile(
        slug="salesforce", name="Salesforce Inc.", region="North America",
        country="US", institution_type="Technology (Enterprise Software / SaaS)",
        assets_usd_bn=63,
        listed=True, exchange="NYSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.salesforce.com/company/sustainability/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD (comprehensive)"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTI (1.5°C)", "RE100", "CDP A", "Net Zero Cloud (product)", "1t.org (trees pledge)"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 78, "tcfd_metrics": 82,
            "issb_s1": 78, "issb_s2": 80,
            "esrs_e1": 38, "esrs_env_other": 28, "esrs_social": 72, "esrs_governance": 80,
            "double_materiality": 48,
            "pcaf_financed": 5, "scope3_cat15": 4,
            "paris_alignment": 78, "transition_plan": 75,
            "physical_risk": 70, "scenario_analysis": 68,
            "tnfd_nature": 32,
        },
        key_strengths=[
            "CDP A-rated: consistent top-tier climate disclosure for SaaS companies",
            "Net Zero Cloud: Salesforce product enables enterprise Scope 3 measurement for clients",
            "1t.org: trillion tree initiative — nature-based solutions commitment",
            "RE100: 100% renewable electricity globally for own operations",
            "Stakeholder capitalism: Marc Benioff personal brand and advocacy amplify disclosure",
            "Employee sustainability: 1% for the Planet and Time, Equity, Product, Profit (TPEP)",
        ],
        priority_gaps=[
            "Net zero 2040: 10 years after Microsoft and Google — slower timeline for smaller footprint",
            "TNFD: formal biodiversity assessment absent despite 1t.org nature commitments",
            "Scope 3 Cat 11: Net Zero Cloud customer GHG enabled — reverse attribution methodology needed",
            "Physical risk: Salesforce Tower San Francisco — sea level rise disclosure",
            "Double materiality: platform data rights (CCPA/GDPR) and AI governance — ESRS S4 equivalent",
            "AI: Einstein AI energy consumption — SaaS AI inference GHG methodology",
        ],
        analyst_note="Salesforce is a strong performer among US SaaS companies but lags Microsoft and "
                     "Google on ambition and disclosure depth. Net Zero Cloud product creates a unique "
                     "position — Salesforce enables client decarbonisation as a business model. "
                     "TNFD adoption would be consistent with 1t.org nature commitment and deepen "
                     "the nature-climate nexus in its disclosure.",
    ),

    # ── Real Estate Companies (Top 5 by global significance) ──────────────────

    InstitutionProfile(
        slug="prologis", name="Prologis Inc.", region="North America",
        country="US", institution_type="REIT (Industrial / Logistics)",
        assets_usd_bn=187,
        listed=True, exchange="NYSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.prologis.com/about/corporate-responsibility/esg-reports",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD"],
        voluntary_frameworks=["GRESB (5-star)", "ISSB S2 (aligned)", "SBTi (1.5°C)",
                              "CDP B", "CRREM (logistics pathway)", "UN PRI"],
        scores={
            "tcfd_governance": 85, "tcfd_strategy": 85, "tcfd_risk_mgmt": 80, "tcfd_metrics": 85,
            "issb_s1": 72, "issb_s2": 75,
            "esrs_e1": 42, "esrs_env_other": 38, "esrs_social": 68, "esrs_governance": 80,
            "double_materiality": 50,
            "pcaf_financed": 35, "scope3_cat15": 30,
            "paris_alignment": 78, "transition_plan": 72,
            "physical_risk": 82, "scenario_analysis": 75,
            "tnfd_nature": 42,
        },
        key_strengths=[
            "World's largest logistics REIT — 1.2bn sq ft of industrial space under management",
            "GRESB 5-star: global benchmark leader in industrial real estate sustainability",
            "SBTi 1.5°C aligned: science-based near-term (2030) and long-term (2040) targets",
            "Solar programme: 1GW of rooftop solar deployed across logistics parks",
            "CRREM pathway: actively models stranding risk for the entire logistics portfolio",
            "PLD Essentials: renewable energy procurement for tenant occupiers",
        ],
        priority_gaps=[
            "Scope 3 Cat 15: financed emissions methodology for equity investments not yet PCAF-standard",
            "TNFD: formal dependency and impact assessment on nature not yet completed",
            "ESRS: non-EU entity — minimal ESRS coverage despite large EU logistics footprint",
            "Embodied carbon: construction-phase Scope 3 not yet consistently measured",
            "Tenant engagement: Scope 3 Cat 13 (downstream leased assets) growing but incomplete",
            "Double materiality: financial materiality of biodiversity loss on cold-chain real estate",
        ],
        analyst_note="Prologis is the global benchmark for logistics REIT sustainability. Its solar "
                     "programme and CRREM alignment set the standard for industrial real estate. "
                     "The key disclosure frontier is PCAF-standard financed emissions (equity "
                     "investments in JV structures) and formal TNFD dependency mapping.",
        portfolio_details={
            "asset_class": "Industrial / Logistics",
            "total_assets_count": 6700,
            "total_gla_sqm": 114_000_000,   # 1.2bn sq ft → ~114m sqm
            "total_gla_sqft": 1_200_000_000,
            "markets": 20,
            "countries": ["US", "EU", "JP", "MX", "BR", "CA", "AU", "KR", "CN"],
            "geographic_split_pct": {
                "Americas": 73, "Europe": 17, "Asia-Pacific": 10
            },
            "flagship_assets": [
                "Prologis Park Tracy (California, US) — 20m sqft mega-campus",
                "Prologis Park Tilburg (Netherlands) — EU logistics hub",
                "Prologis Park Zama (Tokyo, Japan) — urban last-mile",
                "Prologis Chill Park Chicago — cold-chain specialist",
            ],
            "occupancy_rate_pct": 97.2,
            "average_building_age_years": 12,
            "green_certified_sqft": 400_000_000,   # LEED / BREEAM / DGNB
            "green_certifications": ["LEED", "BREEAM", "DGNB", "Green Star"],
            "solar_installed_mw": 1_050,
            "solar_target_mw": 2_000,
            "ev_charging_ports": 3_200,
            "jv_assets_pct": 28,           # % of GLA in JV structures
            "development_pipeline_sqm": 8_500_000,
            "crrem_stranding_assessed": True,
            "gresb_score": 89,
            "gresb_stars": 5,
        },
    ),

    InstitutionProfile(
        slug="american_tower", name="American Tower Corporation", region="North America",
        country="US", institution_type="REIT (Infrastructure / Towers)",
        assets_usd_bn=69,
        listed=True, exchange="NYSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.americantower.com/esg/",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD"],
        voluntary_frameworks=["ISSB S2 (aligned)", "CDP C", "SBTi (committed)", "GRESB"],
        scores={
            "tcfd_governance": 75, "tcfd_strategy": 72, "tcfd_risk_mgmt": 70, "tcfd_metrics": 72,
            "issb_s1": 60, "issb_s2": 62,
            "esrs_e1": 30, "esrs_env_other": 28, "esrs_social": 62, "esrs_governance": 72,
            "double_materiality": 38,
            "pcaf_financed": 18, "scope3_cat15": 15,
            "paris_alignment": 58, "transition_plan": 52,
            "physical_risk": 70, "scenario_analysis": 60,
            "tnfd_nature": 22,
        },
        key_strengths=[
            "220,000+ tower sites globally — critical digital infrastructure with long asset lives",
            "Physical risk: assessed exposure of tower sites to hurricanes, floods, extreme heat",
            "Energy efficiency: diesel genset reduction programme across Africa and Asia towers",
            "SBTi committed: near-term target submitted (1.5°C)",
            "TCFD governance: Board-level Nominating and Corporate Governance Committee oversight",
        ],
        priority_gaps=[
            "Energy: diesel backup generators — Scope 1 from 220k sites is material and growing",
            "Scope 3 Cat 15: REIT structure — equity accounted investments not PCAF-measured",
            "TNFD: tower sites in biodiversity-sensitive areas (emerging markets) — no assessment",
            "CDP: rated C — significant improvement opportunity vs. REIT peers",
            "Transition plan: no sector-aligned CRREM equivalent for tower infrastructure",
            "ESRS: large EU footprint through CoreSite acquisition — CSRD in-scope preparation needed",
        ],
        analyst_note="American Tower faces a distinctive GHG challenge: diesel backup generators "
                     "across 220,000 sites in markets with unreliable grid power represent a growing "
                     "Scope 1 source. The strategic decarbonisation lever is grid solar + battery "
                     "for tower sites — a capital programme with 15-20 year IRR. Disclosure lags "
                     "Prologis in rigour.",
        portfolio_details={
            "asset_class": "Wireless Infrastructure / Towers",
            "total_tower_sites": 220_000,
            "countries": 25,
            "geographic_split_pct": {
                "US & Canada": 43, "Latin America": 25, "Europe": 14, "Africa": 10, "Asia-Pacific": 8
            },
            "key_markets": ["US", "India", "Brazil", "Germany", "France", "Mexico", "South Africa", "Kenya"],
            "flagship_assets": [
                "CoreSite Data Centers (US, acquired 2022) — 26 data centre campuses",
                "AtlasEdge (EU JV with Stonepeak) — European data centre expansion",
                "US tower portfolio: ~43,000 macro towers",
                "India: ~77,000 towers (ATC India) — largest non-US portfolio",
            ],
            "tenants": ["Verizon", "AT&T", "T-Mobile", "Deutsche Telekom", "Orange", "Airtel"],
            "average_tenant_per_tower": 1.8,
            "data_centre_sqft": 3_800_000,    # CoreSite
            "diesel_generator_sites_pct": 35,  # sites with diesel backup (mainly EM)
            "solar_powered_sites": 4_200,
            "battery_storage_sites": 1_100,
            "tower_average_height_m": 52,
            "colocation_revenue_pct": 68,
        },
    ),

    InstitutionProfile(
        slug="cbre_group", name="CBRE Group Inc.", region="North America",
        country="US", institution_type="Real Estate Services",
        assets_usd_bn=26,
        listed=True, exchange="NYSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.cbre.com/about-us/corporate-responsibility/reporting",
        mandatory_frameworks=["SEC GHG Disclosure (stayed)", "TCFD"],
        voluntary_frameworks=["ISSB S2 (aligned)", "SBTi (1.5°C)", "GRESB (partner)",
                              "CDP A", "UN PRI", "TNFD pilot"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 80, "tcfd_risk_mgmt": 78, "tcfd_metrics": 80,
            "issb_s1": 70, "issb_s2": 72,
            "esrs_e1": 38, "esrs_env_other": 32, "esrs_social": 72, "esrs_governance": 78,
            "double_materiality": 52,
            "pcaf_financed": 28, "scope3_cat15": 25,
            "paris_alignment": 68, "transition_plan": 65,
            "physical_risk": 72, "scenario_analysis": 68,
            "tnfd_nature": 40,
        },
        key_strengths=[
            "CDP A-rated: real estate services sector leader in climate disclosure",
            "GRESB partner: green building benchmarking across 2,500+ managed assets",
            "SBTi 1.5°C: validated near-term (2030) and net zero (2040) targets",
            "TNFD pilot: real estate sector dependency and impact disclosure pilot participant",
            "Scope 3 Cat 11 (sold products): CBRE client buildings — unique service sector approach",
            "Real Estate Investments (CBRE IM): $146bn AUM with dedicated RI strategy",
        ],
        priority_gaps=[
            "Managed buildings: Scope 3 Cat 13 (downstream leased assets) across 3bn sq ft managed — incomplete",
            "PCAF: CBRE Investment Management financed emissions not yet PCAF-standard",
            "Double materiality: ESRS double materiality assessment for EU operations needed",
            "ESRS: CSRD in-scope through EU subsidiary operations — not yet structured",
            "AI / data: climate data quality and AI model risk governance gaps",
        ],
        analyst_note="CBRE is the world's largest commercial real estate services firm and a strong "
                     "climate discloser for its sector. The critical gap is Scope 3 from the 3bn+ "
                     "sq ft of property it manages for clients — this represents the largest "
                     "Scope 3 Cat 13 exposure in global real estate but is not yet comprehensively "
                     "measured. CBRE IM financed emissions under PCAF is the second priority.",
        portfolio_details={
            "asset_class": "Real Estate Services + Investment Management",
            "managed_portfolio_sqft": 3_200_000_000,    # 3.2bn sqft managed
            "managed_portfolio_sqm": 297_000_000,
            "aum_usd_bn": 146,                          # CBRE Investment Management
            "offices_worldwide": 500,
            "employees": 130_000,
            "countries": 100,
            "service_lines": ["Advisory", "Global Workplace Solutions", "Real Estate Investments"],
            "geographic_split_aum_pct": {
                "North America": 58, "Europe": 28, "Asia-Pacific": 14
            },
            "managed_asset_types": {
                "Office": 35, "Industrial": 28, "Retail": 18, "Multifamily": 12, "Other": 7
            },
            "flagship_mandates": [
                "CBRE UK Core Fund — 30-asset diversified UK fund",
                "CBRE Clarion Global Real Estate Securities — listed REIT fund",
                "CBRE Global Impact Fund — social infrastructure",
                "CBRE Asia Logistics Fund",
            ],
            "gresb_rated_assets": 2500,
            "leed_certified_managed_assets": 680,
            "breeam_certified_managed_assets": 420,
            "data_centre_managed_sqft": 45_000_000,
        },
    ),

    InstitutionProfile(
        slug="vonovia", name="Vonovia SE", region="Europe",
        country="DE", institution_type="Real Estate (Residential)",
        assets_usd_bn=93,
        listed=True, exchange="XETRA",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2045, financed_sectors_nzba=0,
        report_url="https://vonovia.de/en/responsibility/sustainability-reports",
        mandatory_frameworks=["CSRD (Large Listed, FY2024)", "EU Taxonomy", "SFDR Art. 8",
                              "TCFD", "EPRA sBPR"],
        voluntary_frameworks=["GRESB (4-star)", "CDP B", "CRREM (residential pathway)",
                              "ISSB S2 (aligned)", "SBTi (committed)"],
        scores={
            "tcfd_governance": 80, "tcfd_strategy": 78, "tcfd_risk_mgmt": 76, "tcfd_metrics": 78,
            "issb_s1": 72, "issb_s2": 75,
            "esrs_e1": 78, "esrs_env_other": 70, "esrs_social": 75, "esrs_governance": 78,
            "double_materiality": 72,
            "pcaf_financed": 22, "scope3_cat15": 18,
            "paris_alignment": 75, "transition_plan": 70,
            "physical_risk": 78, "scenario_analysis": 72,
            "tnfd_nature": 45,
        },
        key_strengths=[
            "CSRD full scope: Germany's largest residential landlord — mandatory reporting FY2024",
            "EU Taxonomy: residential energy efficiency — significant capex/opex taxonomy eligible",
            "CRREM aligned: building-level stranding risk assessment for 550,000 residential units",
            "EPRA sBPR: European Public Real Estate Association sustainability best practice",
            "Social housing: rent affordability, climate justice — ESRS S2 community impacts",
            "Energy renovation: €3bn Klimaschutzprogramm — building retrofit programme",
        ],
        priority_gaps=[
            "SBTi: committed but not yet validated — SBTi buildings pathway submission needed",
            "PCAF Cat 4 (commercial real estate): mortgage book emissions not PCAF-standard",
            "TNFD: urban biodiversity in residential estates — no formal LEAP assessment",
            "Embodied carbon: major retrofit programme — Scope 3 Cat 11 construction materials growing",
            "Tenant engagement: Scope 3 Cat 13 electricity consumption in 550k apartments",
        ],
        analyst_note="Vonovia represents the European residential REIT disclosure model. CSRD "
                     "mandatory from FY2024, CRREM building-level stranding assessment, and the "
                     "€3bn climate retrofit programme are genuine disclosure and capital leaders. "
                     "The gap is PCAF Cat 4 mortgage financed emissions and formal SBTi target "
                     "validation — both are in progress.",
        portfolio_details={
            "asset_class": "Residential Real Estate",
            "total_residential_units": 548_000,
            "total_portfolio_sqm": 37_500_000,
            "countries": ["DE", "SE", "AT"],
            "geographic_split_pct": {
                "Germany": 88, "Sweden (Hembla)": 9, "Austria (Buwog)": 3
            },
            "german_portfolio_cities": {
                "Bochum": 35_000, "Berlin": 42_000, "Hamburg": 31_000,
                "Dusseldorf": 28_000, "Munich": 12_000, "Frankfurt": 18_000
            },
            "flagship_assets": [
                "Vonovia Berlin portfolio — 42,000 units; major urban residential landlord",
                "Bochum Ruhr Valley — 35,000 units; largest single-city concentration",
                "Deutsche Wohnen (acquired 2021) — 155,000 additional units",
                "Hembla AB (Sweden) — 21,000 units across Swedish cities",
            ],
            "average_monthly_rent_eur": 7.49,   # per sqm (cold rent)
            "vacancy_rate_pct": 2.0,
            "energy_label_breakdown_pct": {
                "A-B (efficient)": 12, "C-D": 38, "E-F": 35, "G-H (inefficient)": 15
            },
            "retrofit_programme_units_pa": 30_000,
            "klimaschutzprogramm_capex_eur_bn": 3.2,
            "average_epc_kwh_sqm_pa": 138,
            "crrem_assessed_units_pct": 85,
            "gresb_score": 80,
            "gresb_stars": 4,
            "social_housing_units": 82_000,      # rent-regulated units
        },
    ),

    InstitutionProfile(
        slug="segro", name="Segro PLC", region="Europe",
        country="GB", institution_type="REIT (Industrial / Logistics)",
        assets_usd_bn=20,
        listed=True, exchange="LSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.segro.com/responsibility/sustainability-reports",
        mandatory_frameworks=["UK TCFD (mandatory, 2022)", "CSRD (in-scope for EU operations)",
                              "EU Taxonomy", "EPRA sBPR"],
        voluntary_frameworks=["GRESB (5-star, Green Star)", "CDP A", "SBTi (1.5°C validated)",
                              "CRREM (logistics)", "TNFD pilot", "ISSB S2 (aligned)"],
        scores={
            "tcfd_governance": 92, "tcfd_strategy": 90, "tcfd_risk_mgmt": 88, "tcfd_metrics": 90,
            "issb_s1": 80, "issb_s2": 85,
            "esrs_e1": 72, "esrs_env_other": 65, "esrs_social": 72, "esrs_governance": 85,
            "double_materiality": 68,
            "pcaf_financed": 30, "scope3_cat15": 25,
            "paris_alignment": 85, "transition_plan": 82,
            "physical_risk": 88, "scenario_analysis": 82,
            "tnfd_nature": 58,
        },
        key_strengths=[
            "GRESB 5-star Green Star: European industrial REIT disclosure leader",
            "CDP A: highest rating achieved — consistent for 5 consecutive years",
            "SBTi validated 1.5°C: near-term and long-term targets covering all material scopes",
            "UK TCFD mandatory: comprehensive physical and transition risk quantification",
            "TNFD pilot: nature dependency mapping for logistics warehouses — sector leading",
            "CRREM logistics pathway: building-level stranding risk for entire portfolio",
        ],
        priority_gaps=[
            "PCAF: REIT structure — equity accounted JV assets not yet PCAF-standard measured",
            "Embodied carbon: major development pipeline — Scope 3 Cat 11 growing as % of footprint",
            "Tenant Scope 3 Cat 13: occupier consumption data coverage improving but incomplete",
            "ESRS double materiality: formal EU CSRD implementation for continental European assets",
            "Biodiversity: TNFD pilot is promising — formal TNFD disclosure needed FY2025",
        ],
        analyst_note="Segro is arguably the best European industrial REIT disclosure leader. "
                     "CDP A, GRESB 5-star, SBTi validated, and TNFD pilot participation set "
                     "the standard. The remaining frontier is PCAF-standard measurement of JV "
                     "assets and formal TNFD adoption, which will likely be completed in FY2025.",
        portfolio_details={
            "asset_class": "Industrial / Logistics / Urban Warehousing",
            "total_assets_count": 155,
            "total_gla_sqm": 10_400_000,
            "total_gla_sqft": 111_900_000,
            "total_portfolio_value_gbp_bn": 20.4,
            "countries": ["GB", "FR", "DE", "PL", "IT", "NL", "ES", "AT", "BE", "CZ"],
            "geographic_split_pct": {
                "UK": 52, "Continental Europe": 48
            },
            "flagship_assets": [
                "Slough Trading Estate (UK) — Europe's largest business park, 18m sqft",
                "Segro Logistics Park East Midlands (UK) — 4.9m sqft, Amazon & DHL anchor",
                "Segro European Logistics Partnership (SELP) — 6.3m sqm continental JV",
                "Parc des Docks, Saint-Denis (Paris) — urban logistics flagship",
                "Varsovia Business Park (Warsaw, Poland) — CEE gateway hub",
            ],
            "occupancy_rate_pct": 98.0,
            "average_building_age_years": 8,
            "breeam_excellent_pct": 72,
            "epc_a_b_pct": 68,
            "development_pipeline_sqm": 2_100_000,
            "pre_let_development_pct": 70,
            "urban_portfolio_pct": 35,    # proximity logistics
            "jv_gla_sqm": 6_300_000,     # SELP JV
            "gresb_score": 91,
            "gresb_stars": 5,
            "key_tenants": ["Amazon", "DHL", "Royal Mail", "Geodis", "DB Schenker", "H&M", "Zalando"],
            "avg_lease_length_years": 8.2,
            "solar_on_rooftop_mw": 68,
        },
    ),

    # ── REIT Funds (Top 5 by AUM / regional significance) ─────────────────────

    InstitutionProfile(
        slug="unibail_rodamco", name="Unibail-Rodamco-Westfield NV", region="Europe",
        country="NL", institution_type="REIT (Retail / Shopping Centres)",
        assets_usd_bn=52,
        listed=True, exchange="Euronext Amsterdam",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2040, financed_sectors_nzba=0,
        report_url="https://www.urw.com/en/csr/csr-reports",
        mandatory_frameworks=["CSRD (Large Listed, FY2024)", "EU Taxonomy", "SFDR Art. 8",
                              "EPRA sBPR", "French GHG decree (Art. 75 Grenelle II)"],
        voluntary_frameworks=["GRESB (5-star)", "CDP A", "SBTi (1.5°C)", "CRREM (retail)",
                              "TNFD pilot", "ISSB S2 (aligned)"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82, "tcfd_metrics": 85,
            "issb_s1": 75, "issb_s2": 78,
            "esrs_e1": 80, "esrs_env_other": 72, "esrs_social": 75, "esrs_governance": 82,
            "double_materiality": 75,
            "pcaf_financed": 28, "scope3_cat15": 22,
            "paris_alignment": 80, "transition_plan": 75,
            "physical_risk": 82, "scenario_analysis": 78,
            "tnfd_nature": 52,
        },
        key_strengths=[
            "CSRD mandatory pioneer: first European large-cap retail REIT to publish CSRD-aligned report",
            "EU Taxonomy: shopping centre energy efficiency — substantial eligible activity revenues",
            "CDP A: 8 consecutive years; European retail real estate climate disclosure benchmark",
            "GRESB 5-star: Global Real Estate Sustainability Benchmark — global retail sector lead",
            "Better Places 2030: flagship sustainability programme — net zero by 2030 for own operations",
            "Smart energy: district heating, green roof programmes, EV charging across 80+ flagships",
        ],
        priority_gaps=[
            "Visitor Scope 3: customer travel to 1bn+ annual shopping centre visits — largest unquantified Scope 3",
            "Retail tenant Scope 3 Cat 13: occupier energy consumption measurement improving",
            "Physical risk: coastal and flood zone retail assets — CRREM stranding growing",
            "TNFD: biodiversity mapping for urban flagship sites — formal LEAP not yet complete",
            "Divestment programme: URW is actively divesting US Westfield assets — residual ESG exposure",
        ],
        analyst_note="URW has set the European retail REIT sustainability disclosure standard. "
                     "Better Places 2030 is among the most ambitious own-operations targets in "
                     "the sector. The critical unresolved gap is visitor-induced Scope 3 from "
                     "1 billion annual shopping centre visits — this dwarfs building energy consumption "
                     "and has no established PCAF or ESRS precedent.",
        portfolio_details={
            "asset_class": "Retail / Shopping Centres",
            "total_assets_count": 82,
            "total_gla_sqm": 8_700_000,
            "annual_visitors_bn": 1.0,
            "countries": ["FR", "DE", "AT", "NL", "SE", "ES", "CZ", "SK", "PL", "US"],
            "geographic_split_pct": {
                "France": 28, "Germany & Austria": 22, "Continental Europe (other)": 28,
                "US (Westfield divesting)": 22
            },
            "flagship_assets": [
                "Westfield London (White City) — 2.6m sqft, Europe's busiest urban mall",
                "La Part-Dieu (Lyon, France) — 2.2m sqft, France's #1 shopping centre",
                "CentrO Oberhausen (Germany) — 2.4m sqft, Germany's largest shopping centre",
                "Westfield Century City (Los Angeles, US) — luxury flagship",
                "Westfield Valley Fair (San Jose, US) — Silicon Valley premium",
                "Mall of Scandinavia (Stockholm, Sweden) — 2.0m sqft, Nordic flagship",
            ],
            "anchor_brands": ["Zara", "H&M", "Apple", "Sephora", "Galeries Lafayette", "Primark"],
            "occupancy_rate_pct": 95.3,
            "average_tenant_sales_psf_usd": 890,
            "green_certified_gla_pct": 85,
            "breeam_excellent_assets": 28,
            "led_lighting_pct": 95,
            "renewable_energy_pct_common_areas": 72,
            "solar_installed_mw": 14,
            "ev_charging_bays": 8_400,
            "district_heating_assets": 12,
            "gresb_score": 87,
            "gresb_stars": 5,
            "divestment_programme": "US Westfield portfolio — partial sales ongoing (2022-2025)",
        },
    ),

    InstitutionProfile(
        slug="link_reit", name="Link Real Estate Investment Trust", region="Asia-Pacific",
        country="HK", institution_type="REIT (Diversified)",
        assets_usd_bn=24,
        listed=True, exchange="HKEX",
        nzba_member=False, pcaf_member=False, tnfd_supporter=False,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://www.linkreit.com/en/investor-relations/reporting-centre/",
        mandatory_frameworks=["HKEX ESG Reporting Guide (mandatory)", "TCFD"],
        voluntary_frameworks=["GRESB (4-star)", "CDP B", "ISSB S2 (aligned)", "UN PRI"],
        scores={
            "tcfd_governance": 75, "tcfd_strategy": 72, "tcfd_risk_mgmt": 68, "tcfd_metrics": 72,
            "issb_s1": 62, "issb_s2": 65,
            "esrs_e1": 28, "esrs_env_other": 25, "esrs_social": 62, "esrs_governance": 72,
            "double_materiality": 40,
            "pcaf_financed": 18, "scope3_cat15": 15,
            "paris_alignment": 60, "transition_plan": 55,
            "physical_risk": 68, "scenario_analysis": 58,
            "tnfd_nature": 28,
        },
        key_strengths=[
            "Asia's largest REIT: HK$220bn portfolio — retail, carparks, logistics across HK, mainland China, Australia, UK",
            "HKEX ESG mandatory: full climate disclosure aligned to HKEX ESG Reporting Guide",
            "GRESB 4-star: Asia-Pacific REIT peer benchmark leader",
            "Green finance: HK$6bn green bond issuance for certified green buildings",
            "Community: Link ToGather — social sustainability programme targeting low-income communities",
        ],
        priority_gaps=[
            "SBTi: no SBTi commitment — net zero 2050 target lacks sector-aligned pathway validation",
            "Physical risk: Hong Kong typhoon and sea-level rise exposure for coastal assets — limited quantification",
            "TNFD: no formal nature dependency assessment despite urban biodiversity opportunity in HK portfolio",
            "PCAF: no PCAF-standard financed emissions disclosure for real estate investments",
            "Mainland China assets: data quality and assurance for Chinese portfolio assets lags HK",
            "ISSB transition: HKEX mandating ISSB S1/S2 from 2025 — transition plan needed",
        ],
        analyst_note="Link REIT is the Asia-Pacific REIT sustainability leader but faces a "
                     "significant disclosure uplift as HKEX mandates ISSB S1/S2 from FY2025. "
                     "SBTi commitment and PCAF financed emissions are the two highest-priority "
                     "gaps given the 2025 regulatory deadline. Physical risk quantification for "
                     "Hong Kong typhoon and flooding exposure is material.",
        portfolio_details={
            "asset_class": "Diversified (Retail, Carparks, Logistics, Office)",
            "total_assets_count": 145,
            "total_gla_sqm": 1_050_000,
            "total_portfolio_value_hkd_bn": 220,
            "countries": ["HK", "CN", "AU", "GB"],
            "geographic_split_pct": {
                "Hong Kong": 55, "Mainland China": 20, "Australia": 15, "United Kingdom": 10
            },
            "asset_type_breakdown_pct": {
                "Retail": 52, "Carparks": 18, "Logistics": 18, "Office": 12
            },
            "flagship_assets": [
                "Link REIT — original HK portfolio: 72 retail properties, 60,000+ carpark spaces",
                "Pacific Place (HK partial) — luxury mixed-use Central district",
                "Qibao Vanke Plaza (Shanghai) — mainland China retail flagship",
                "Elizabeth Quay (Perth, Australia) — office and retail precinct",
                "The Cabot (London) — Canary Wharf Grade-A office tower",
            ],
            "hk_retail_properties": 72,
            "hk_carpark_spaces": 60_000,
            "mainland_china_retail_gla_sqm": 210_000,
            "green_building_certifications": ["BEAM Plus", "Green Star", "BREEAM"],
            "green_certified_pct": 62,
            "solar_installed_mw": 8.5,
            "ev_charging_bays": 1_200,
            "gresb_score": 75,
            "gresb_stars": 4,
            "occupancy_rate_pct": 97.5,
            "issb_mandatory_year": 2025,  # HKEX ISSB S1/S2 mandatory
        },
    ),

    InstitutionProfile(
        slug="dexus", name="Dexus Property Group", region="Asia-Pacific",
        country="AU", institution_type="REIT (Diversified / Office & Industrial)",
        assets_usd_bn=19,
        listed=True, exchange="ASX",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://www.dexus.com/our-approach/sustainability/reporting",
        mandatory_frameworks=["Australian TCFD (mandatory, ASIC)", "CSRD (not applicable)",
                              "EPRA sBPR (adopted)", "APRA CPS 229"],
        voluntary_frameworks=["GRESB (5-star, 13 years)", "CDP A", "SBTi (1.5°C)",
                              "TNFD pilot", "ISSB S2 (aligned)", "UN PRI"],
        scores={
            "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 85, "tcfd_metrics": 85,
            "issb_s1": 78, "issb_s2": 82,
            "esrs_e1": 35, "esrs_env_other": 32, "esrs_social": 68, "esrs_governance": 80,
            "double_materiality": 55,
            "pcaf_financed": 28, "scope3_cat15": 22,
            "paris_alignment": 82, "transition_plan": 80,
            "physical_risk": 88, "scenario_analysis": 82,
            "tnfd_nature": 55,
        },
        key_strengths=[
            "GRESB 5-star 13 years: Australia's most consistently rated REIT — global sector leader",
            "CDP A: Australian listed real estate benchmark; 2030 net zero for own operations",
            "SBTi validated 1.5°C: building sector pathway including Scope 3 Cat 13",
            "APRA CPS 229: climate risk management regulatory framework — financial regulator oversight",
            "TNFD pilot: nature risk mapping for office and industrial portfolios — Australia first",
            "Green Star: 6-star Green Star ratings across flagship office towers in Sydney CBD",
        ],
        priority_gaps=[
            "ISSB S1/S2 mandatory: Australian ISSB implementation (AASB S1/S2) from FY2025 — full adoption pending",
            "PCAF: managed fund financed emissions (wholesale capital partners) — not PCAF-standard",
            "Embodied carbon: major construction activity — whole-life carbon Scope 3 Cat 11 methodology",
            "Physical risk: coastal CBDs Sydney, Melbourne — sea level rise 1m scenario quantification",
            "Biodiversity: TNFD pilot promising — formal net positive biodiversity commitment pending",
        ],
        analyst_note="Dexus is the Australian REIT disclosure pacesetter — 13 consecutive GRESB "
                     "5-star ratings is a global benchmark. The APRA CPS 229 climate risk regulatory "
                     "framework adds financial regulator oversight unique to Australia. The key "
                     "frontiers are ISSB S1/S2 mandatory implementation (AASB, FY2025) and PCAF "
                     "financed emissions for its third-party capital management business.",
        portfolio_details={
            "asset_class": "Diversified (Office, Industrial, Healthcare, Retail)",
            "total_portfolio_value_aud_bn": 42,
            "owned_and_managed_aud_bn": 61,   # including third-party capital
            "countries": ["AU"],
            "cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
            "asset_type_breakdown_pct": {
                "Office": 58, "Industrial / Logistics": 28, "Healthcare": 8, "Retail": 6
            },
            "flagship_assets": [
                "1 Bligh Street (Sydney CBD) — 6-star Green Star; Australia's first WELL-certified tower",
                "Darling Square (Sydney) — mixed-use 5.4ha precinct",
                "8 Chifley Square (Sydney) — 5.5-star NABERS Energy office tower",
                "Gateway Sydney (Circular Quay) — heritage-adaptive commercial precinct",
                "Dexus Jandakot Airport (Perth WA) — industrial aviation park",
            ],
            "office_nabers_energy_avg": 5.4,  # out of 6
            "office_green_star_avg": 5.1,
            "nabers_water_avg": 4.8,
            "well_certified_assets": 4,
            "gresb_score": 93,
            "gresb_stars": 5,
            "consecutive_gresb_5star_years": 13,
            "total_sqm": 2_400_000,
            "occupancy_rate_pct": 95.3,
            "healthcare_assets_count": 12,
            "third_party_aum_aud_bn": 19,    # Dexus AHL fund management
            "development_pipeline_aud_bn": 15.4,
        },
    ),

    InstitutionProfile(
        slug="land_securities", name="Land Securities Group PLC", region="Europe",
        country="GB", institution_type="REIT (Diversified / UK)",
        assets_usd_bn=11,
        listed=True, exchange="LSE",
        nzba_member=False, pcaf_member=False, tnfd_supporter=True,
        net_zero_target_year=2030, financed_sectors_nzba=0,
        report_url="https://landsec.com/sustainability/reporting",
        mandatory_frameworks=["UK TCFD (mandatory)", "CSRD (in-scope for EU operations)",
                              "EPRA sBPR", "UK Streamlined Energy & Carbon Reporting"],
        voluntary_frameworks=["GRESB (5-star, Green Star)", "CDP A-", "SBTi (1.5°C validated)",
                              "TNFD pilot", "ISSB S2 (aligned)", "Race to Zero"],
        scores={
            "tcfd_governance": 90, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85, "tcfd_metrics": 88,
            "issb_s1": 78, "issb_s2": 82,
            "esrs_e1": 68, "esrs_env_other": 60, "esrs_social": 72, "esrs_governance": 85,
            "double_materiality": 70,
            "pcaf_financed": 25, "scope3_cat15": 20,
            "paris_alignment": 85, "transition_plan": 82,
            "physical_risk": 85, "scenario_analysis": 80,
            "tnfd_nature": 58,
        },
        key_strengths=[
            "Net zero 2030 — own operations: one of the most ambitious near-term targets in UK listed real estate",
            "GRESB 5-star Green Star: UK commercial REIT leader; 2023 'Listed Sector Leader' designation",
            "SBTi 1.5°C validated: covers Scope 1, 2, and Scope 3 Cat 13 (tenant emissions)",
            "UK TCFD mandatory: comprehensive physical and transition risk scenarios (1.5°C, 3°C)",
            "TNFD pilot participant: biodiversity and nature dependency mapping for London West End assets",
            "Embodied carbon: whole-life carbon policy — net zero embodied by 2030 for major developments",
        ],
        priority_gaps=[
            "Net zero 2030 (own ops) vs. 2040+ (whole portfolio): value chain net zero timeline gap",
            "PCAF: retail and office tenant financed emissions not yet PCAF-standard Cat 4 measured",
            "ESRS: limited EU presence but CSRD double materiality process beginning",
            "Embodied carbon: net zero embodied commitment is sector-leading but Scope 3 Cat 11 data quality",
            "Social materiality: London West End gentrification impacts — ESRS S2 equivalent needed",
        ],
        analyst_note="Land Securities leads UK commercial real estate sustainability disclosure. "
                     "Net zero for own operations by 2030, SBTi validated including Scope 3 Cat 13, "
                     "and TNFD pilot participation combine for a sector-leading profile. "
                     "The gap is the distinction between own-operations net zero (2030) and "
                     "whole-portfolio net zero — tenant supply chain emissions extend the timeline "
                     "and require PCAF Cat 4 financed emissions measurement.",
        portfolio_details={
            "asset_class": "Diversified (Retail, Office, Mixed-Use)",
            "total_portfolio_value_gbp_bn": 10.9,
            "total_sqm": 1_450_000,
            "countries": ["GB"],
            "cities": ["London", "Manchester", "Leeds", "Oxford", "Cambridge"],
            "asset_type_breakdown_pct": {
                "Retail Parks & Shopping": 48, "London Offices": 32, "Mixed-Use Urban": 20
            },
            "flagship_assets": [
                "Trinity Leeds — 1m sqft prime retail and leisure, Grade-A",
                "Bluewater (25% stake, Kent) — 1.6m sqft super-regional retail",
                "Piccadilly Lights (London West End) — iconic advertising and retail landmark",
                "New Street Square (London EC4) — 900,000 sqft mixed-use campus",
                "MediaCity UK (50% JV with Peel, Salford) — 37-acre digital media campus",
                "Westgate Oxford — 800,000 sqft urban retail and leisure",
            ],
            "breeam_excellent_or_outstanding_pct": 78,
            "epc_a_b_pct": 65,
            "nabers_uk_rated_assets": 8,
            "gresb_score": 88,
            "gresb_stars": 5,
            "occupancy_rate_pct": 97.1,
            "uk_retail_parks_count": 12,
            "london_office_sqm": 460_000,
            "development_pipeline_gbp_bn": 2.1,
            "solar_installed_mw": 4.2,
            "ev_charging_bays": 980,
            "avg_lease_length_years": 7.1,
            "key_office_tenants": ["KPMG", "Clifford Chance", "Transport for London", "HMRC"],
        },
    ),

    InstitutionProfile(
        slug="brookfield_asset_management", name="Brookfield Asset Management Ltd", region="North America",
        country="CA", institution_type="PE / Infrastructure (Real Assets)",
        assets_usd_bn=900,
        listed=True, exchange="NYSE / TSX",
        nzba_member=True, pcaf_member=True, tnfd_supporter=True,
        net_zero_target_year=2050, financed_sectors_nzba=0,
        report_url="https://bam.brookfield.com/esg",
        mandatory_frameworks=["TCFD (voluntary Canada)", "CSA ESG Disclosure Guidance",
                              "SFDR (for EU funds)", "CSRD (in-scope for EU real estate)"],
        voluntary_frameworks=["NZBA", "PCAF (real assets)", "GRESB (5-star)", "CDP B",
                              "TNFD pilot", "UN PRI", "GFANZ", "ISSB S2 (aligned)"],
        scores={
            "tcfd_governance": 82, "tcfd_strategy": 80, "tcfd_risk_mgmt": 78, "tcfd_metrics": 80,
            "issb_s1": 68, "issb_s2": 70,
            "esrs_e1": 42, "esrs_env_other": 38, "esrs_social": 65, "esrs_governance": 75,
            "double_materiality": 45,
            "pcaf_financed": 58, "scope3_cat15": 52,
            "paris_alignment": 72, "transition_plan": 68,
            "physical_risk": 75, "scenario_analysis": 70,
            "tnfd_nature": 48,
        },
        key_strengths=[
            "NZBA + PCAF member: financed emissions disclosure covering renewable energy, real estate, infrastructure",
            "World's largest owner of renewable power infrastructure: 33 GW installed capacity",
            "GFANZ founding member: Mark Carney-led initiative — policy influence in green finance",
            "GRESB 5-star: infrastructure and real estate fund benchmarking leader",
            "PCAF real assets: pioneering PCAF methodology for infrastructure private equity",
            "Transition finance: Brookfield Transition Fund — $15bn dedicated capital for decarbonisation",
        ],
        priority_gaps=[
            "PCAF private markets: infrastructure PE and private real estate — methodology gaps remain",
            "ESRS: large EU real estate and infrastructure footprint — CSRD readiness limited",
            "Double materiality: across 2,000+ portfolio companies globally — assessment scope challenge",
            "Scope 3: portfolio company financed emissions aggregation — data quality across private assets",
            "TNFD: formal nature dependency mapping across infrastructure assets (hydro, forestry, mines)",
            "ISSB: disclosure depth lags public REIT peers for private market real assets",
        ],
        analyst_note="Brookfield is the largest real assets alternative manager globally and a GFANZ "
                     "founding member. Its Transition Fund ($15bn) and 33GW renewable portfolio "
                     "give it unique credentials. The disclosure gap is private market data quality — "
                     "PCAF real assets methodology for 2,000+ portfolio companies is inherently "
                     "data-sparse. ESRS CSRD readiness for the EU portfolio is the near-term priority.",
        portfolio_details={
            "asset_class": "Real Assets (Renewable Power, Infrastructure, Real Estate, Private Equity)",
            "total_aum_usd_bn": 900,
            "fee_bearing_capital_usd_bn": 457,
            "countries": 30,
            "asset_type_breakdown_aum_pct": {
                "Renewable Power & Transition": 22, "Infrastructure": 28,
                "Real Estate": 25, "Private Equity": 20, "Credit": 5
            },
            "flagship_funds": [
                "Brookfield Global Transition Fund II (BGTF II) — $15bn climate capital",
                "Brookfield Infrastructure Fund V — $28bn global infrastructure PE",
                "Brookfield Real Estate Partners IV — office, retail, multifamily",
                "Brookfield Renewable Partners — listed, 33GW renewable energy",
                "Brookfield Business Partners — large-cap private equity",
            ],
            "renewable_power_gw": 33,
            "renewable_pipeline_gw": 150,
            "renewable_asset_types": ["Hydropower", "Wind", "Solar", "Storage", "Nuclear (small modular)"],
            "infrastructure_assets": {
                "Transport (ports, rail, toll roads)": "26 assets across 4 continents",
                "Data infrastructure": "Telecom towers, fibre, data centres",
                "Utilities": "Water, electricity distribution in 15+ countries",
                "Midstream energy": "US and Canadian gas pipelines",
            },
            "real_estate_sqft": 230_000_000,
            "real_estate_asset_types": ["Office", "Retail", "Multifamily", "Hospitality", "Triple Net"],
            "private_equity_portfolio_cos": 60,
            "transition_fund_sectors": ["Renewable power", "Nuclear", "Carbon capture", "Green hydrogen",
                                         "Sustainable solutions"],
            "gresb_infrastructure_score": 85,
            "gresb_real_estate_score": 78,
            "pcaf_methodology": "Real assets — PCAF Standard Part D (private equity) + Part E (real estate)",
        },
    ),
]

# ─── Engine ───────────────────────────────────────────────────────────────────

class PeerBenchmarkEngine:

    def __init__(self) -> None:
        self._index: dict[str, InstitutionProfile] = {inst.slug: inst for inst in _INSTITUTIONS}

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _weighted_score(scores: dict[str, int]) -> float:
        total_weight = sum(FRAMEWORK_CATEGORIES[k]["weight"] for k in scores)
        weighted_sum = sum(scores[k] * FRAMEWORK_CATEGORIES[k]["weight"] for k in scores)
        return round(weighted_sum / total_weight, 1) if total_weight else 0.0

    @staticmethod
    def _group_scores(scores: dict[str, int]) -> dict[str, float]:
        groups: dict[str, list] = {}
        for k, v in scores.items():
            g = FRAMEWORK_CATEGORIES[k]["group"]
            groups.setdefault(g, []).append(v)
        return {g: round(sum(vs) / len(vs), 1) for g, vs in groups.items()}

    # ── public API ────────────────────────────────────────────────────────────

    def get_all_institutions(self) -> list[dict]:
        return [self._to_summary(inst) for inst in _INSTITUTIONS]

    def get_institution(self, slug: str) -> dict | None:
        inst = self._index.get(slug)
        return self._to_detail(inst) if inst else None

    def get_comparison_table(
        self,
        slugs: list[str] | None = None,
        region: str | None = None,
        institution_type: str | None = None,
    ) -> list[dict]:
        institutions = list(_INSTITUTIONS)
        if slugs:
            institutions = [i for i in institutions if i.slug in slugs]
        if region:
            institutions = [i for i in institutions if i.region == region]
        if institution_type:
            institutions = [i for i in institutions if i.institution_type == institution_type]
        return [self._to_comparison_row(inst) for inst in institutions]

    def get_heatmap(self, slugs: list[str] | None = None) -> dict:
        institutions = list(_INSTITUTIONS)
        if slugs:
            institutions = [i for i in institutions if i.slug in slugs]
        rows = []
        for inst in institutions:
            row: dict = {"slug": inst.slug, "name": inst.name, "region": inst.region}
            for cat_key in FRAMEWORK_CATEGORIES:
                score = inst.scores.get(cat_key, 0)
                row[cat_key] = {"score": score, "rag": score_to_rag(score)}
            row["weighted_avg"] = self._weighted_score(inst.scores)
            rows.append(row)
        rows.sort(key=lambda r: -r["weighted_avg"])
        return {
            "rows": rows,
            "categories": [
                {"key": k, **v} for k, v in FRAMEWORK_CATEGORIES.items()
            ],
        }

    def get_regional_averages(self) -> list[dict]:
        by_region: dict[str, list[InstitutionProfile]] = {}
        for inst in _INSTITUTIONS:
            by_region.setdefault(inst.region, []).append(inst)
        result = []
        for region, institutions in sorted(by_region.items()):
            avg_scores: dict[str, float] = {}
            for cat_key in FRAMEWORK_CATEGORIES:
                vals = [inst.scores.get(cat_key, 0) for inst in institutions]
                avg_scores[cat_key] = round(sum(vals) / len(vals), 1)
            result.append({
                "region": region,
                "institution_count": len(institutions),
                "institutions": [i.name for i in institutions],
                "avg_scores": avg_scores,
                "group_averages": self._group_scores(avg_scores),
                "overall_avg": self._weighted_score(avg_scores),
            })
        return result

    def get_framework_coverage(self) -> list[dict]:
        """Which institutions have which mandatory / voluntary frameworks."""
        all_mandatory: set[str] = set()
        all_voluntary: set[str] = set()
        for inst in _INSTITUTIONS:
            all_mandatory.update(inst.mandatory_frameworks)
            all_voluntary.update(inst.voluntary_frameworks)
        rows = []
        for inst in _INSTITUTIONS:
            rows.append({
                "slug": inst.slug,
                "name": inst.name,
                "region": inst.region,
                "mandatory_frameworks": inst.mandatory_frameworks,
                "voluntary_frameworks": inst.voluntary_frameworks,
                "nzba_member": inst.nzba_member,
                "pcaf_member": inst.pcaf_member,
                "tnfd_supporter": inst.tnfd_supporter,
                "net_zero_target_year": inst.net_zero_target_year,
                "financed_sectors_nzba": inst.financed_sectors_nzba,
            })
        return rows

    def get_top_gaps(self, slug: str, top_n: int = 5) -> list[dict]:
        inst = self._index.get(slug)
        if not inst:
            return []
        sorted_cats = sorted(
            [(k, inst.scores.get(k, 0)) for k in FRAMEWORK_CATEGORIES],
            key=lambda x: x[1],
        )
        return [
            {
                "category_key": k,
                "category_label": FRAMEWORK_CATEGORIES[k]["label"],
                "group": FRAMEWORK_CATEGORIES[k]["group"],
                "score": s,
                "rag": score_to_rag(s),
            }
            for k, s in sorted_cats[:top_n]
        ]

    # ── serialisation ─────────────────────────────────────────────────────────

    def _to_summary(self, inst: InstitutionProfile) -> dict:
        return {
            "slug": inst.slug,
            "name": inst.name,
            "region": inst.region,
            "country": inst.country,
            "institution_type": inst.institution_type,
            "assets_usd_bn": inst.assets_usd_bn,
            "nzba_member": inst.nzba_member,
            "pcaf_member": inst.pcaf_member,
            "tnfd_supporter": inst.tnfd_supporter,
            "net_zero_target_year": inst.net_zero_target_year,
            "financed_sectors_nzba": inst.financed_sectors_nzba,
            "weighted_score": self._weighted_score(inst.scores),
            "group_scores": self._group_scores(inst.scores),
        }

    def _to_comparison_row(self, inst: InstitutionProfile) -> dict:
        d = self._to_summary(inst)
        d["scores"] = inst.scores
        d["score_rags"] = {k: score_to_rag(v) for k, v in inst.scores.items()}
        return d

    def _to_detail(self, inst: InstitutionProfile) -> dict:
        d = self._to_comparison_row(inst)
        d.update({
            "exchange": inst.exchange,
            "listed": inst.listed,
            "report_url": inst.report_url,
            "mandatory_frameworks": inst.mandatory_frameworks,
            "voluntary_frameworks": inst.voluntary_frameworks,
            "key_strengths": inst.key_strengths,
            "priority_gaps": inst.priority_gaps,
            "analyst_note": inst.analyst_note,
            "top_gaps": self.get_top_gaps(inst.slug, top_n=5),
            "portfolio_details": inst.portfolio_details,
        })
        return d


# ─── Module singleton ─────────────────────────────────────────────────────────

peer_benchmark_engine = PeerBenchmarkEngine()
