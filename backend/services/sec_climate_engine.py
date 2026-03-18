"""
SEC Climate Disclosure Engine
==============================

Structured disclosure engine for the SEC's climate-related disclosure rules
under Regulation S-K and S-X (final rule adopted March 2024, effective for
accelerated filers FY 2025+).

Key provisions modelled:
- Reg S-K Item 1500: Definitions (registrant, Scope 1/2, GHG)
- Reg S-K Item 1501: Governance of climate-related risks
- Reg S-K Item 1502: Strategy — material climate risks & opportunities
- Reg S-K Item 1503: Risk management process
- Reg S-K Item 1504: Climate targets and goals
- Reg S-K Item 1505: GHG emissions disclosure (Scope 1 & 2)
- Reg S-X §14-02:   Financial statement effects of severe weather events
                     and transition activities

Phase-in timeline:
- Large Accelerated Filers (LAF): FY 2025 (filed 2026)
- Accelerated Filers (AF):       FY 2026 (filed 2027)
- Non-Accelerated / SRC / EGC:   exempt from Scope 1/2 GHG,
                                   but climate risk disclosures required

Attestation:
- LAF: limited assurance FY 2027, reasonable assurance FY 2029
- AF:  limited assurance FY 2028, reasonable assurance FY 2031

Cross-framework linkage:
- TCFD (governance, strategy, risk management, metrics) — near-full overlap
- ISSB IFRS S2 — scope 1/2 disclosure, scenario analysis
- GHG Protocol — Scope 1/2 methodology (required)
- EPA MRR — US facility-level data source
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Rule Status Advisory (P1-10)
# ---------------------------------------------------------------------------

# The SEC's final climate disclosure rule (Release 33-11275, March 2024) was:
#   1. Voluntarily stayed by the SEC in April 2024 pending 5th Circuit review.
#   2. RESCINDED by SEC vote on 27 March 2025 — the rule no longer exists as law.
#
# What this means for users:
#   • No US public company has a current legal obligation under this rule.
#   • Scores/compliance figures produced by this engine are INFORMATIONAL ONLY.
#   • They remain useful for voluntary TCFD-aligned disclosure and ISSB S2 prep.
#   • Do NOT cite outputs as SEC compliance evidence in SEC filings or investor docs.
#   • Cross-framework mappings (TCFD, ISSB S2) are unaffected and remain valid.
#
# This engine is maintained as an educational/voluntary-disclosure framework.
# It will be updated if the SEC re-proposes a climate rule.

SEC_RULE_STATUS = {
    "rule_reference": "SEC Release 33-11275",
    "rule_title": "The Enhancement and Standardization of Climate-Related Disclosures for Investors",
    "adopted_date": "2024-03-06",
    "stayed_date": "2024-04-04",
    "rescinded_date": "2025-03-27",
    "current_status": "RESCINDED",
    "legal_force": False,
    "advisory_only": True,
    "rationale": (
        "SEC voted 3-2 to rescind the rule on 27 March 2025, citing litigation uncertainty "
        "following the 8th Circuit consolidation and the change in Commission composition. "
        "The rule never became effective."
    ),
    "voluntary_frameworks_still_valid": ["TCFD", "ISSB S2", "GHG Protocol", "CDP"],
    "engine_use_guidance": (
        "This engine produces VOLUNTARY DISCLOSURE scores only. "
        "Outputs must not be presented as SEC-mandated compliance results."
    ),
}


# ---------------------------------------------------------------------------
# Reference Data Constants
# ---------------------------------------------------------------------------

# Filer categories & phase-in (as adopted March 2024; rule rescinded March 2025)
FILER_CATEGORIES = {
    "large_accelerated_filer": {
        "label": "Large Accelerated Filer (LAF)",
        "public_float_min_usd": 700_000_000,
        "ghg_disclosure_start_fy": 2025,
        "limited_assurance_fy": 2027,
        "reasonable_assurance_fy": 2029,
        "climate_risk_disclosure_required": True,
        "scope_12_required": True,
        "scope_3_required": False,
        "financial_statement_effects": True,
    },
    "accelerated_filer": {
        "label": "Accelerated Filer (AF)",
        "public_float_min_usd": 75_000_000,
        "ghg_disclosure_start_fy": 2026,
        "limited_assurance_fy": 2028,
        "reasonable_assurance_fy": 2031,
        "climate_risk_disclosure_required": True,
        "scope_12_required": True,
        "scope_3_required": False,
        "financial_statement_effects": True,
    },
    "non_accelerated_filer": {
        "label": "Non-Accelerated Filer (NAF)",
        "public_float_min_usd": 0,
        "ghg_disclosure_start_fy": None,
        "limited_assurance_fy": None,
        "reasonable_assurance_fy": None,
        "climate_risk_disclosure_required": True,
        "scope_12_required": False,
        "scope_3_required": False,
        "financial_statement_effects": True,
    },
    "smaller_reporting_company": {
        "label": "Smaller Reporting Company (SRC)",
        "public_float_min_usd": 0,
        "ghg_disclosure_start_fy": None,
        "limited_assurance_fy": None,
        "reasonable_assurance_fy": None,
        "climate_risk_disclosure_required": True,
        "scope_12_required": False,
        "scope_3_required": False,
        "financial_statement_effects": True,
    },
    "emerging_growth_company": {
        "label": "Emerging Growth Company (EGC)",
        "public_float_min_usd": 0,
        "ghg_disclosure_start_fy": None,
        "limited_assurance_fy": None,
        "reasonable_assurance_fy": None,
        "climate_risk_disclosure_required": True,
        "scope_12_required": False,
        "scope_3_required": False,
        "financial_statement_effects": True,
    },
}

# Regulation S-K disclosure items
REG_SK_ITEMS = [
    {
        "item": "1501",
        "title": "Governance",
        "description": "Board oversight and management role in climate-related risk governance",
        "sub_items": [
            "1501(a) Board oversight of climate risks",
            "1501(b) Management role in assessing/managing climate risks",
        ],
        "required_for": ["all_filers"],
    },
    {
        "item": "1502",
        "title": "Strategy",
        "description": "Material climate-related risks, impacts on strategy, business model, and outlook",
        "sub_items": [
            "1502(a) Material climate risks (physical & transition)",
            "1502(b) Actual & reasonably likely material impacts",
            "1502(c) Resilience of strategy (scenario analysis, if used)",
            "1502(d) Internal carbon price, if maintained",
        ],
        "required_for": ["all_filers"],
    },
    {
        "item": "1503",
        "title": "Risk Management",
        "description": "Process for identifying, assessing, and managing material climate-related risks",
        "sub_items": [
            "1503(a) Process for identifying material climate risks",
            "1503(b) How climate risks are prioritised",
            "1503(c) Integration into overall risk management",
        ],
        "required_for": ["all_filers"],
    },
    {
        "item": "1504",
        "title": "Targets and Goals",
        "description": "Climate targets, goals, and transition plans (if adopted)",
        "sub_items": [
            "1504(a) Target/goal description",
            "1504(b) Scope of activities covered",
            "1504(c) Time horizon and interim targets",
            "1504(d) How the entity plans to meet targets",
            "1504(e) Progress against targets",
            "1504(f) Carbon offsets or RECs (if material to target)",
        ],
        "required_for": ["all_filers"],
    },
    {
        "item": "1505",
        "title": "GHG Emissions",
        "description": "Scope 1 and Scope 2 GHG emissions disclosure",
        "sub_items": [
            "1505(a) Scope 1 emissions (direct, in CO2e)",
            "1505(b) Scope 2 emissions (location-based, in CO2e)",
            "1505(c) Methodology description (GHG Protocol)",
            "1505(d) Organisational & operational boundaries",
            "1505(e) Significant changes in methodology or boundary",
        ],
        "required_for": ["large_accelerated_filer", "accelerated_filer"],
    },
]

# Reg S-X 14-02: Financial statement effects
REG_SX_ITEMS = [
    {
        "item": "14-02(a)",
        "title": "Severe weather events & natural conditions",
        "description": "Expenditures and losses from severe weather events if material (>1% pre-tax income or equity)",
        "threshold_pct": 1.0,
    },
    {
        "item": "14-02(b)",
        "title": "Transition activities",
        "description": "Expenses and capitalised costs related to carbon offsets, RECs, or transition activities if material (>1%)",
        "threshold_pct": 1.0,
    },
    {
        "item": "14-02(c)",
        "title": "Financial estimates & assumptions",
        "description": "Climate-related impacts on financial estimates (impairments, useful lives, fair value, contingencies)",
        "threshold_pct": 1.0,
    },
]

# Attestation standards
ATTESTATION_REQUIREMENTS = {
    "limited_assurance": {
        "standard": "AICPA AT-C 105/210 or PCAOB equivalent",
        "level": "limited",
        "description": "Limited assurance on Scope 1 & 2 GHG emissions",
    },
    "reasonable_assurance": {
        "standard": "AICPA AT-C 105/205 or PCAOB equivalent",
        "level": "reasonable",
        "description": "Reasonable assurance on Scope 1 & 2 GHG emissions (audit-level)",
    },
}

# Safe harbor applicability
SAFE_HARBOR = {
    "forward_looking": True,
    "covered_items": [
        "Transition plans",
        "Climate targets and goals (Item 1504)",
        "Scenario analysis (Item 1502(c))",
        "Internal carbon price (Item 1502(d))",
    ],
    "not_covered": [
        "Historical GHG emissions (Item 1505)",
        "Financial statement effects (Reg S-X 14-02)",
    ],
    "note": "PSLRA safe harbor applies to forward-looking statements about "
            "climate risks, targets, and transition plans.",
}

# Cross-framework mapping
SEC_CROSS_FRAMEWORK_MAP = [
    {
        "sec_item": "Item 1501 (Governance)",
        "tcfd": "Governance (a)(b)",
        "issb_s2": "IFRS S2 para 5-6",
        "csrd_esrs": "ESRS 2 GOV-1, GOV-2",
    },
    {
        "sec_item": "Item 1502 (Strategy)",
        "tcfd": "Strategy (a)(b)(c)",
        "issb_s2": "IFRS S2 para 8-15",
        "csrd_esrs": "ESRS E1 SBM-3",
    },
    {
        "sec_item": "Item 1503 (Risk Management)",
        "tcfd": "Risk Management (a)(b)(c)",
        "issb_s2": "IFRS S2 para 16-19",
        "csrd_esrs": "ESRS 2 IRO-1",
    },
    {
        "sec_item": "Item 1504 (Targets & Goals)",
        "tcfd": "Metrics & Targets (c)",
        "issb_s2": "IFRS S2 para 33-36",
        "csrd_esrs": "ESRS E1 E1-4 (Targets)",
    },
    {
        "sec_item": "Item 1505 (GHG Emissions)",
        "tcfd": "Metrics & Targets (a)(b)",
        "issb_s2": "IFRS S2 para 29",
        "csrd_esrs": "ESRS E1 E1-6 (GHG emissions)",
    },
    {
        "sec_item": "Reg S-X 14-02 (Financial Effects)",
        "tcfd": "Metrics & Targets (financial impact)",
        "issb_s2": "IFRS S2 para 20-28",
        "csrd_esrs": "ESRS E1 E1-9 (Financial effects)",
    },
]


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FilerAssessmentResult:
    registrant_name: str
    cik: str
    filer_category: str
    fiscal_year: int
    # Phase-in status
    ghg_disclosure_required: bool = False
    ghg_disclosure_start_fy: int | None = None
    assurance_required: bool = False
    assurance_level: str = ""
    assurance_start_fy: int | None = None
    financial_effects_required: bool = False
    # Compliance status per item
    item_compliance: list = field(default_factory=list)
    overall_compliance_pct: float = 0.0
    gaps: list = field(default_factory=list)
    critical_gaps: int = 0
    recommendations: list = field(default_factory=list)
    safe_harbor_items: list = field(default_factory=list)
    cross_framework_mapping: list = field(default_factory=list)
    attestation_status: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


@dataclass
class GHGDisclosureResult:
    registrant_name: str
    fiscal_year: int
    # Scope 1
    scope_1_total_co2e_mt: float = 0.0
    scope_1_by_gas: dict = field(default_factory=dict)
    scope_1_methodology: str = ""
    # Scope 2
    scope_2_location_co2e_mt: float = 0.0
    scope_2_market_co2e_mt: float = 0.0
    scope_2_methodology: str = ""
    # Boundaries
    org_boundary: str = ""
    operational_boundary: str = ""
    consolidation_approach: str = ""
    # Year-over-year
    prior_year_scope_1: float = 0.0
    prior_year_scope_2: float = 0.0
    yoy_change_scope_1_pct: float = 0.0
    yoy_change_scope_2_pct: float = 0.0
    # Intensity
    intensity_metric: str = ""
    intensity_value: float = 0.0
    # Attestation readiness
    attestation_readiness_score: float = 0.0
    attestation_gaps: list = field(default_factory=list)
    # Data quality
    data_quality_score: float = 0.0
    data_quality_notes: list = field(default_factory=list)


@dataclass
class FinancialEffectsResult:
    registrant_name: str
    fiscal_year: int
    pre_tax_income_usd: float = 0.0
    total_equity_usd: float = 0.0
    materiality_threshold_usd: float = 0.0
    # Severe weather
    severe_weather_losses_usd: float = 0.0
    severe_weather_material: bool = False
    severe_weather_events: list = field(default_factory=list)
    # Transition activities
    transition_expenses_usd: float = 0.0
    transition_capex_usd: float = 0.0
    transition_material: bool = False
    transition_details: list = field(default_factory=list)
    # Estimates & assumptions
    climate_impairments_usd: float = 0.0
    climate_contingencies_usd: float = 0.0
    estimates_material: bool = False
    estimate_details: list = field(default_factory=list)
    # Total
    total_climate_financial_impact_usd: float = 0.0
    disclosure_required: bool = False


@dataclass
class MaterialityAssessmentResult:
    registrant_name: str
    fiscal_year: int
    material_physical_risks: list = field(default_factory=list)
    material_transition_risks: list = field(default_factory=list)
    immaterial_risks: list = field(default_factory=list)
    total_risks_assessed: int = 0
    material_count: int = 0
    time_horizons: dict = field(default_factory=dict)
    strategy_impact: dict = field(default_factory=dict)
    scenario_analysis_used: bool = False
    internal_carbon_price: float | None = None
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SECClimateEngine:
    """SEC Climate Disclosure compliance engine (Reg S-K Items 1500-1505, Reg S-X 14-02)."""

    # ── Filer Assessment ──────────────────────────────────────────────────

    def assess_filer(
        self,
        registrant_name: str,
        cik: str,
        filer_category: str,
        fiscal_year: int,
        # Compliance evidence per disclosure item (0-100)
        governance_score: float = 0.0,
        strategy_score: float = 0.0,
        risk_management_score: float = 0.0,
        targets_goals_score: float = 0.0,
        ghg_emissions_score: float = 0.0,
        financial_effects_score: float = 0.0,
        # Attestation
        has_limited_assurance: bool = False,
        has_reasonable_assurance: bool = False,
    ) -> FilerAssessmentResult:
        """Assess SEC climate disclosure compliance for a registrant."""

        cat = FILER_CATEGORIES.get(filer_category, FILER_CATEGORIES["non_accelerated_filer"])
        notes: list[str] = []

        # Phase-in determination
        ghg_start = cat.get("ghg_disclosure_start_fy")
        ghg_required = cat["scope_12_required"] and ghg_start is not None and fiscal_year >= ghg_start
        fin_effects_required = cat["financial_statement_effects"]

        # Assurance phase-in
        limited_fy = cat.get("limited_assurance_fy")
        reasonable_fy = cat.get("reasonable_assurance_fy")
        assurance_required = False
        assurance_level = ""
        assurance_start_fy = None

        if reasonable_fy and fiscal_year >= reasonable_fy:
            assurance_required = True
            assurance_level = "reasonable"
            assurance_start_fy = reasonable_fy
        elif limited_fy and fiscal_year >= limited_fy:
            assurance_required = True
            assurance_level = "limited"
            assurance_start_fy = limited_fy

        # Compliance per item
        item_scores = [
            ("1501", "Governance", governance_score, True),
            ("1502", "Strategy", strategy_score, True),
            ("1503", "Risk Management", risk_management_score, True),
            ("1504", "Targets & Goals", targets_goals_score, True),
            ("1505", "GHG Emissions", ghg_emissions_score, ghg_required),
            ("S-X 14-02", "Financial Effects", financial_effects_score, fin_effects_required),
        ]

        item_compliance = []
        gaps = []
        for item_id, title, score, required in item_scores:
            score = min(100.0, max(0.0, score))
            if not required:
                status = "not_applicable"
            elif score >= 80:
                status = "compliant"
            elif score >= 50:
                status = "partial"
            else:
                status = "non_compliant"

            item_gaps = []
            if required and score < 80:
                gap_desc = f"Item {item_id} ({title}): score {score:.0f}/100"
                severity = "critical" if score < 30 else "major" if score < 60 else "minor"
                item_gaps.append(gap_desc)
                gaps.append({
                    "item": item_id,
                    "title": title,
                    "gap": gap_desc,
                    "severity": severity,
                    "score": score,
                })

            item_compliance.append({
                "item": item_id,
                "title": title,
                "score": round(score, 1),
                "required": required,
                "status": status,
                "gaps": item_gaps,
            })

        # Overall compliance (weighted equally among required items)
        required_items = [ic for ic in item_compliance if ic["required"]]
        if required_items:
            overall = sum(ic["score"] for ic in required_items) / len(required_items)
        else:
            overall = 0.0

        critical_count = sum(1 for g in gaps if g["severity"] == "critical")

        # Attestation status
        attestation = {
            "required": assurance_required,
            "level": assurance_level,
            "has_limited": has_limited_assurance,
            "has_reasonable": has_reasonable_assurance,
            "compliant": (
                not assurance_required or
                (assurance_level == "limited" and has_limited_assurance) or
                (assurance_level == "reasonable" and has_reasonable_assurance)
            ),
        }
        if assurance_required and not attestation["compliant"]:
            gaps.append({
                "item": "Attestation",
                "title": f"{assurance_level.title()} Assurance",
                "gap": f"{assurance_level.title()} assurance required from FY {assurance_start_fy}",
                "severity": "critical",
                "score": 0,
            })
            critical_count += 1

        # Recommendations
        recs = self._generate_recommendations(
            gaps, ghg_required, assurance_required, assurance_level,
            has_limited_assurance, has_reasonable_assurance
        )

        # Safe harbor items
        safe_items = SAFE_HARBOR["covered_items"] if targets_goals_score > 0 else []

        # P1-10: Prepend rescission advisory to every assessment result
        rescission_note = (
            "⚠️  SEC RULE RESCINDED (27 March 2025): Release 33-11275 was voluntarily "
            "stayed in April 2024 and formally rescinded by the SEC on 27 March 2025. "
            "This engine produces VOLUNTARY/INFORMATIONAL scores only — not SEC-mandated "
            "compliance evidence. Cross-framework mappings to TCFD and ISSB S2 remain valid."
        )
        notes = [rescission_note] + notes

        return FilerAssessmentResult(
            registrant_name=registrant_name,
            cik=cik,
            filer_category=filer_category,
            fiscal_year=fiscal_year,
            ghg_disclosure_required=ghg_required,
            ghg_disclosure_start_fy=ghg_start,
            assurance_required=assurance_required,
            assurance_level=assurance_level,
            assurance_start_fy=assurance_start_fy,
            financial_effects_required=fin_effects_required,
            item_compliance=item_compliance,
            overall_compliance_pct=round(overall, 1),
            gaps=gaps,
            critical_gaps=critical_count,
            recommendations=recs,
            safe_harbor_items=safe_items,
            cross_framework_mapping=SEC_CROSS_FRAMEWORK_MAP,
            attestation_status=attestation,
            notes=notes,
        )

    # ── GHG Emissions Disclosure (Item 1505) ──────────────────────────────

    def assess_ghg_disclosure(
        self,
        registrant_name: str,
        fiscal_year: int,
        scope_1_total_co2e_mt: float = 0.0,
        scope_1_by_gas: dict | None = None,
        scope_1_methodology: str = "GHG Protocol Corporate Standard",
        scope_2_location_co2e_mt: float = 0.0,
        scope_2_market_co2e_mt: float = 0.0,
        scope_2_methodology: str = "GHG Protocol Scope 2 Guidance",
        org_boundary: str = "operational_control",
        operational_boundary: str = "direct_emissions",
        consolidation_approach: str = "operational_control",
        prior_year_scope_1: float = 0.0,
        prior_year_scope_2: float = 0.0,
        intensity_metric: str = "revenue_usd_m",
        revenue_or_denominator: float = 0.0,
        data_sources_documented: bool = False,
        emission_factors_documented: bool = False,
        methodology_changes_disclosed: bool = True,
        third_party_verified: bool = False,
    ) -> GHGDisclosureResult:
        """Assess GHG emissions disclosure completeness and attestation readiness."""

        scope_1_by_gas = scope_1_by_gas or {}

        # YoY change
        yoy_s1 = ((scope_1_total_co2e_mt - prior_year_scope_1) / prior_year_scope_1 * 100
                   if prior_year_scope_1 > 0 else 0.0)
        yoy_s2 = ((scope_2_location_co2e_mt - prior_year_scope_2) / prior_year_scope_2 * 100
                   if prior_year_scope_2 > 0 else 0.0)

        # Intensity
        intensity_value = 0.0
        if revenue_or_denominator > 0:
            total_ghg = scope_1_total_co2e_mt + scope_2_location_co2e_mt
            intensity_value = round(total_ghg / revenue_or_denominator, 2)

        # Attestation readiness (0-100)
        readiness = 0.0
        att_gaps = []
        checks = [
            (scope_1_total_co2e_mt > 0, 15, "Scope 1 emissions quantified"),
            (scope_2_location_co2e_mt > 0, 15, "Scope 2 location-based quantified"),
            (len(scope_1_by_gas) > 0, 10, "GHG breakdown by gas provided"),
            (data_sources_documented, 15, "Data sources documented"),
            (emission_factors_documented, 15, "Emission factors documented"),
            (methodology_changes_disclosed, 5, "Methodology changes disclosed"),
            (org_boundary != "", 10, "Organisational boundary defined"),
            (third_party_verified, 15, "Third-party verification obtained"),
        ]
        for met, pts, desc in checks:
            if met:
                readiness += pts
            else:
                att_gaps.append(desc)

        # Data quality score
        dq = 0.0
        dq_notes = []
        if scope_1_total_co2e_mt > 0:
            dq += 25
        else:
            dq_notes.append("Scope 1 emissions not reported")
        if scope_2_location_co2e_mt > 0:
            dq += 20
        else:
            dq_notes.append("Scope 2 location-based not reported")
        if scope_2_market_co2e_mt > 0:
            dq += 10
        if data_sources_documented:
            dq += 20
        else:
            dq_notes.append("Data sources not documented")
        if emission_factors_documented:
            dq += 15
        else:
            dq_notes.append("Emission factors not documented")
        if third_party_verified:
            dq += 10

        return GHGDisclosureResult(
            registrant_name=registrant_name,
            fiscal_year=fiscal_year,
            scope_1_total_co2e_mt=scope_1_total_co2e_mt,
            scope_1_by_gas=scope_1_by_gas,
            scope_1_methodology=scope_1_methodology,
            scope_2_location_co2e_mt=scope_2_location_co2e_mt,
            scope_2_market_co2e_mt=scope_2_market_co2e_mt,
            scope_2_methodology=scope_2_methodology,
            org_boundary=org_boundary,
            operational_boundary=operational_boundary,
            consolidation_approach=consolidation_approach,
            prior_year_scope_1=prior_year_scope_1,
            prior_year_scope_2=prior_year_scope_2,
            yoy_change_scope_1_pct=round(yoy_s1, 2),
            yoy_change_scope_2_pct=round(yoy_s2, 2),
            intensity_metric=intensity_metric,
            intensity_value=intensity_value,
            attestation_readiness_score=round(readiness, 1),
            attestation_gaps=att_gaps,
            data_quality_score=round(dq, 1),
            data_quality_notes=dq_notes,
        )

    # ── Financial Statement Effects (Reg S-X 14-02) ─────────────────────

    def assess_financial_effects(
        self,
        registrant_name: str,
        fiscal_year: int,
        pre_tax_income_usd: float = 0.0,
        total_equity_usd: float = 0.0,
        # Severe weather (14-02(a))
        severe_weather_losses_usd: float = 0.0,
        severe_weather_events: list | None = None,
        # Transition (14-02(b))
        carbon_offset_expenses_usd: float = 0.0,
        rec_expenses_usd: float = 0.0,
        transition_capex_usd: float = 0.0,
        other_transition_expenses_usd: float = 0.0,
        transition_details: list | None = None,
        # Estimates (14-02(c))
        climate_impairments_usd: float = 0.0,
        climate_contingencies_usd: float = 0.0,
        estimate_details: list | None = None,
    ) -> FinancialEffectsResult:
        """Assess Reg S-X 14-02 financial statement effects of climate events."""

        severe_weather_events = severe_weather_events or []
        transition_details = transition_details or []
        estimate_details = estimate_details or []

        # 1% materiality threshold
        base = max(abs(pre_tax_income_usd), abs(total_equity_usd))
        threshold = base * 0.01 if base > 0 else 0

        # Severe weather
        sw_material = severe_weather_losses_usd >= threshold and threshold > 0

        # Transition
        total_transition = (carbon_offset_expenses_usd + rec_expenses_usd +
                            other_transition_expenses_usd)
        trans_material = total_transition >= threshold and threshold > 0

        # Estimates
        total_estimates = climate_impairments_usd + climate_contingencies_usd
        est_material = total_estimates >= threshold and threshold > 0

        total_impact = severe_weather_losses_usd + total_transition + total_estimates + transition_capex_usd
        disclosure_required = sw_material or trans_material or est_material

        return FinancialEffectsResult(
            registrant_name=registrant_name,
            fiscal_year=fiscal_year,
            pre_tax_income_usd=pre_tax_income_usd,
            total_equity_usd=total_equity_usd,
            materiality_threshold_usd=round(threshold, 2),
            severe_weather_losses_usd=severe_weather_losses_usd,
            severe_weather_material=sw_material,
            severe_weather_events=severe_weather_events,
            transition_expenses_usd=round(total_transition, 2),
            transition_capex_usd=transition_capex_usd,
            transition_material=trans_material,
            transition_details=transition_details,
            climate_impairments_usd=climate_impairments_usd,
            climate_contingencies_usd=climate_contingencies_usd,
            estimates_material=est_material,
            estimate_details=estimate_details,
            total_climate_financial_impact_usd=round(total_impact, 2),
            disclosure_required=disclosure_required,
        )

    # ── Climate Risk Materiality Assessment (Items 1502-1503) ────────────

    def assess_materiality(
        self,
        registrant_name: str,
        fiscal_year: int,
        # Physical risks (list of dicts: {risk, description, time_horizon, likelihood, magnitude_usd, material})
        physical_risks: list | None = None,
        # Transition risks
        transition_risks: list | None = None,
        # Strategy
        scenario_analysis_used: bool = False,
        internal_carbon_price_usd_per_tco2e: float | None = None,
        strategy_resilience_assessment: str = "",
    ) -> MaterialityAssessmentResult:
        """Assess materiality of climate risks under SEC Items 1502 and 1503."""

        physical_risks = physical_risks or []
        transition_risks = transition_risks or []

        all_risks = physical_risks + transition_risks
        material_physical = [r for r in physical_risks if r.get("material", False)]
        material_transition = [r for r in transition_risks if r.get("material", False)]
        immaterial = [r for r in all_risks if not r.get("material", False)]

        # Time horizon buckets
        horizons = {"short_term": 0, "medium_term": 0, "long_term": 0}
        for r in all_risks:
            h = r.get("time_horizon", "medium_term")
            horizons[h] = horizons.get(h, 0) + 1

        # Strategy impact summary
        total_material_magnitude = sum(
            r.get("magnitude_usd", 0) for r in material_physical + material_transition
        )
        strategy_impact = {
            "total_material_risks": len(material_physical) + len(material_transition),
            "total_material_magnitude_usd": total_material_magnitude,
            "scenario_analysis_used": scenario_analysis_used,
            "strategy_resilience_note": strategy_resilience_assessment,
        }

        notes = []
        if not material_physical and not material_transition:
            notes.append("No material climate risks identified. "
                         "SEC guidance states registrants must still disclose the process "
                         "used to determine materiality (Item 1503).")
        if scenario_analysis_used:
            notes.append("Scenario analysis is voluntary but recommended by SEC. "
                         "If disclosed, must describe scenarios, assumptions, and financial impact.")

        return MaterialityAssessmentResult(
            registrant_name=registrant_name,
            fiscal_year=fiscal_year,
            material_physical_risks=material_physical,
            material_transition_risks=material_transition,
            immaterial_risks=immaterial,
            total_risks_assessed=len(all_risks),
            material_count=len(material_physical) + len(material_transition),
            time_horizons=horizons,
            strategy_impact=strategy_impact,
            scenario_analysis_used=scenario_analysis_used,
            internal_carbon_price=internal_carbon_price_usd_per_tco2e,
            notes=notes,
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _generate_recommendations(
        self, gaps, ghg_required, assurance_required, assurance_level,
        has_limited, has_reasonable,
    ) -> list[str]:
        recs = []
        for g in gaps:
            if g["severity"] == "critical":
                recs.append(f"CRITICAL: Address {g['title']} — {g['gap']}")
        if ghg_required:
            has_ghg_gap = any(g["item"] == "1505" for g in gaps)
            if has_ghg_gap:
                recs.append("Scope 1 & 2 GHG emissions disclosure required — "
                            "ensure GHG Protocol methodology documented, data sources auditable")
        if assurance_required:
            if assurance_level == "reasonable" and not has_reasonable:
                recs.append("Reasonable assurance on Scope 1/2 required — "
                            "engage PCAOB-registered or equivalent attestation provider")
            elif assurance_level == "limited" and not has_limited:
                recs.append("Limited assurance on Scope 1/2 required — "
                            "engage attestation provider under AT-C 210")
        if not any(g["item"] == "1504" for g in gaps):
            recs.append("Consider voluntary Scope 3 disclosure with PSLRA safe harbor protection")
        return recs

    # ── Static Reference Data ─────────────────────────────────────────────

    @staticmethod
    def get_filer_categories() -> dict:
        return FILER_CATEGORIES

    @staticmethod
    def get_reg_sk_items() -> list[dict]:
        return REG_SK_ITEMS

    @staticmethod
    def get_reg_sx_items() -> list[dict]:
        return REG_SX_ITEMS

    @staticmethod
    def get_attestation_requirements() -> dict:
        return ATTESTATION_REQUIREMENTS

    @staticmethod
    def get_safe_harbor() -> dict:
        return SAFE_HARBOR

    @staticmethod
    def get_cross_framework_map() -> list[dict]:
        return SEC_CROSS_FRAMEWORK_MAP

    @staticmethod
    def get_rule_status() -> dict:
        """Return P1-10 advisory: rule rescission status for UI/API consumers."""
        return SEC_RULE_STATUS
