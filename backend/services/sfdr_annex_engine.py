"""
SFDR Annex Disclosure Template Engine (E9)
==========================================

Generates structured pre-contractual and periodic disclosure outputs conforming
to the RTS templates in EU Delegated Regulation 2022/1288 (SFDR Level 2).

Complements the existing sfdr_pai_engine.py (PAI calculation) and
sfdr_report_generator.py (periodic report analytics) by producing the
formal document-ready template structures required for:

  Annex I   — PAI Statement (Art 4 SFDR — website transparency, entity-level)
  Annex II  — Art 8 Pre-contractual disclosure (prospectus / KID insert)
  Annex III — Art 8 Periodic disclosure report template
  Annex IV  — Art 9 Pre-contractual disclosure
  Annex V   — Art 9 Periodic disclosure report template

For each annex the engine:
  1. Maps input data to required template sections/fields per the RTS
  2. Computes completeness scores (% of mandatory fields populated)
  3. Flags missing/non-compliant fields with remediation notes
  4. Generates a structured JSON representation suitable for downstream
     rendering to PDF/Word (via XBRL iXBRL tagging at reporting layer)

References:
  - SFDR Regulation (EU) 2019/2088
  - RTS Delegated Regulation (EU) 2022/1288 (Annexes I–V)
  - ESMA Q&A on SFDR application (2023/ESMA36-43-2498)
  - EBA/EIOPA/ESMA Joint Opinion on SFDR (2021/ESMA30-379-471)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Reference: Mandatory vs Optional disclosure fields per annex
# ---------------------------------------------------------------------------

# ---- Annex I (PAI Statement — Art 4 entity-level) -------------------------
ANNEX_I_MANDATORY_FIELDS = [
    "entity_name",
    "statement_date",
    "reference_period_start",
    "reference_period_end",
    "total_investments_covered_eur",
    "pai_policy_description",
    "pai_consideration_summary",
    # Mandatory PAI indicators (at least indicators 1–14 for investments)
    "indicator_1_scope1_2_ghg_intensity",
    "indicator_2_carbon_footprint",
    "indicator_3_ghg_intensity_eevalue",
    "indicator_4_fossil_fuel_exposure",
    "indicator_5_non_renewable_energy_consumption",
    "indicator_6_non_renewable_energy_production",
    "indicator_7_energy_intensity_high_impact",
    "indicator_8_biodiversity",
    "indicator_9_water_emissions",
    "indicator_10_hazardous_waste",
    "indicator_14_gender_pay_gap",
    "indicator_15_board_gender_diversity",
    "indicator_16_controversial_weapons",
    "engagement_policy_summary",
    "international_standards_alignment",
    "historical_comparison",
]

ANNEX_I_OPTIONAL_FIELDS = [
    "indicator_11_emissions_to_water",
    "indicator_12_hazardous_waste_ratio",
    "indicator_13_uunadjusted_gender_pay_gap",
    "indicator_17_executive_pay_ratio",
    "indicator_18_co2_emissions_real_estate",
    "selected_additional_climate_indicators",
    "selected_additional_social_indicators",
    "future_targets_description",
    "reference_benchmark",
]

# ---- Annex II (Art 8 Pre-contractual) ------------------------------------
ANNEX_II_MANDATORY_FIELDS = [
    "fund_name",
    "legal_entity_identifier",
    "sfdr_classification",
    "isin",
    "summary_esg_characteristics",
    "no_significant_harm_statement",
    "dnsh_methodology",
    "environmental_characteristics",
    "social_characteristics",
    "investment_strategy_description",
    "proportion_sustainable_investments_pct",
    "proportion_taxonomy_aligned_pct",
    "asset_allocation_categories",     # must show pie chart breakdown
    "engagement_policy",
    "data_sources",
    "data_quality_limitations",
    "due_diligence_description",
]

ANNEX_II_OPTIONAL_FIELDS = [
    "reference_benchmark_name",
    "reference_benchmark_alignment_explanation",
    "taxonomy_objectives_targeted",
    "minimum_taxonomy_alignment_commitment",
    "sovereign_supranational_exclusions_rationale",
    "derivatives_use_explanation",
    "best_effort_taxonomy_note",
]

# ---- Annex III (Art 8 Periodic) ------------------------------------------
ANNEX_III_MANDATORY_FIELDS = [
    "fund_name",
    "isin",
    "reference_period_start",
    "reference_period_end",
    "sfdr_classification",
    "esg_characteristics_attained",
    "esg_characteristics_summary",
    "top_investments_list",            # Top 15 investments table
    "asset_allocation_pct_breakdown",  # Pie chart data
    "proportion_sustainable_pct_achieved",
    "taxonomy_aligned_pct_achieved",
    "pai_summary_table",               # mandatory PAI indicators with values
    "sustainability_indicators_used",
    "data_sources_and_processing",
    "data_limitations_description",
    "due_diligence_actions",
    "engagement_policy_applied",
    "index_used_as_reference",         # if any; "none" acceptable
]

ANNEX_III_OPTIONAL_FIELDS = [
    "taxonomy_contribution_details",
    "historical_comparison_table",
    "sector_breakdown_table",
    "geography_breakdown_table",
]

# ---- Annex IV (Art 9 Pre-contractual) ------------------------------------
ANNEX_IV_MANDATORY_FIELDS = ANNEX_II_MANDATORY_FIELDS + [
    "sustainable_investment_objective",
    "sustainable_investment_min_pct",
    "taxonomy_aligned_min_pct",
    "dnsh_binding_criteria",
    "good_governance_assessment_methodology",
    "reference_benchmark_sustainability_features",
    "taxonomy_environmental_objectives_list",
]

ANNEX_IV_OPTIONAL_FIELDS = [
    "benchmark_methodology_url",
    "impact_measurement_methodology",
    "carbon_reduction_pathway",
]

# ---- Annex V (Art 9 Periodic) --------------------------------------------
ANNEX_V_MANDATORY_FIELDS = ANNEX_III_MANDATORY_FIELDS + [
    "sustainable_investment_objective_achieved",
    "sustainable_investment_pct_achieved",
    "taxonomy_alignment_pct_achieved",
    "dnsh_compliance_confirmation",
    "good_governance_confirmation",
    "reference_benchmark_comparison",
    "sustainability_indicators_results",
]

ANNEX_V_OPTIONAL_FIELDS = ANNEX_III_OPTIONAL_FIELDS + [
    "impact_results_table",
]

# ---------------------------------------------------------------------------
# Reference: PAI Indicator Registry (Annex I Table 1 — mandatory for investments)
# ---------------------------------------------------------------------------

PAI_INDICATOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "1": {
        "description": "GHG emissions — Scope 1, 2 and 3",
        "metric": "tCO₂e / EUR million invested (EVIC)",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "2": {
        "description": "Carbon footprint",
        "metric": "tCO₂e / EUR million invested",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "3": {
        "description": "GHG intensity of investee companies",
        "metric": "tCO₂e / EUR million revenue",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "4": {
        "description": "Exposure to companies active in the fossil fuel sector",
        "metric": "% share of investments in companies with fossil fuel activities",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "5": {
        "description": "Share of non-renewable energy consumption and production",
        "metric": "% non-renewable energy (consumption)",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "6": {
        "description": "Energy consumption intensity per high-impact sector",
        "metric": "GWh / EUR million revenue (high-impact sectors)",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "7": {
        "description": "Activities negatively affecting biodiversity-sensitive areas",
        "metric": "% investments in companies with sites in/near protected areas",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "8": {
        "description": "Emissions to water",
        "metric": "tonne / EUR million invested",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "9": {
        "description": "Hazardous waste and radioactive waste ratio",
        "metric": "tonne / EUR million invested",
        "mandatory": True,
        "category": "climate_environment",
        "art4_table": 1,
    },
    "10": {
        "description": "Violations of UN Global Compact principles and OECD Guidelines",
        "metric": "% investments in companies with breaches",
        "mandatory": True,
        "category": "social_governance",
        "art4_table": 1,
    },
    "11": {
        "description": "Lack of processes to monitor compliance with UN GC / OECD Guidelines",
        "metric": "% investments in companies without monitoring processes",
        "mandatory": True,
        "category": "social_governance",
        "art4_table": 1,
    },
    "12": {
        "description": "Unadjusted gender pay gap",
        "metric": "% (mean gap between male/female average gross hourly pay)",
        "mandatory": True,
        "category": "social_governance",
        "art4_table": 1,
    },
    "13": {
        "description": "Board gender diversity",
        "metric": "% female board members",
        "mandatory": True,
        "category": "social_governance",
        "art4_table": 1,
    },
    "14": {
        "description": "Exposure to controversial weapons",
        "metric": "% investments in companies manufacturing controversial weapons",
        "mandatory": True,
        "category": "social_governance",
        "art4_table": 1,
    },
    # Additional climate indicators (Table 2 — optional but frequently selected)
    "15": {
        "description": "GHG intensity of real estate assets",
        "metric": "kgCO₂e / m²",
        "mandatory": False,
        "category": "additional_climate",
        "art4_table": 2,
    },
    "16": {
        "description": "Energy consumption intensity of real estate assets",
        "metric": "kWh / m²",
        "mandatory": False,
        "category": "additional_climate",
        "art4_table": 2,
    },
    "17": {
        "description": "Exposure to fossil fuels through real estate assets",
        "metric": "% real estate assets with fossil fuel heating",
        "mandatory": False,
        "category": "additional_climate",
        "art4_table": 2,
    },
    "18": {
        "description": "Exposure to energy-inefficient real estate assets",
        "metric": "% real estate with EPC below C",
        "mandatory": False,
        "category": "additional_climate",
        "art4_table": 2,
    },
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PAIIndicatorValue:
    indicator_id: str               # "1" to "18"
    value: Optional[float] = None
    unit: str = ""
    reference_period: str = ""
    coverage_pct: float = 0.0       # % of portfolio covered by this data
    data_source: str = ""
    data_quality_score: int = 3     # 1 (best) to 5 (worst) per PCAF DQS
    actions_taken: str = ""
    target_value: Optional[float] = None
    target_date: str = ""


@dataclass
class FundDisclosureInput:
    """Input data for generating any SFDR Annex disclosure."""
    fund_id: str
    fund_name: str
    legal_entity_identifier: str = ""
    isin: str = ""
    sfdr_classification: str = "art8"      # art6 | art8 | art8plus | art9
    fund_manager: str = ""
    jurisdiction: str = "EU"

    # Reference period
    reference_period_start: str = ""
    reference_period_end: str = ""
    report_date: str = ""

    # Fund characteristics
    total_aum_eur: float = 0.0
    investment_universe: str = ""

    # Sustainability commitments
    proportion_sustainable_investments_pct: float = 0.0
    proportion_taxonomy_aligned_pct: float = 0.0
    sustainable_investment_min_pct: float = 0.0     # Art 9 minimum commitment
    taxonomy_aligned_min_pct: float = 0.0

    # ESG characteristics (Art 8)
    environmental_characteristics: List[str] = field(default_factory=list)
    social_characteristics: List[str] = field(default_factory=list)
    taxonomy_objectives: List[str] = field(default_factory=list)   # CCM, CCA, WTR, CE, PPE, BIO

    # Strategy and policy
    investment_strategy_description: str = ""
    engagement_policy: str = ""
    good_governance_assessment_methodology: str = ""
    dnsh_methodology: str = ""

    # Data
    data_sources: List[str] = field(default_factory=list)
    data_limitations: str = ""
    due_diligence_description: str = ""

    # Asset allocation (for pie chart)
    pct_sustainable_environmental: float = 0.0
    pct_sustainable_social: float = 0.0
    pct_taxonomy_aligned_environmental: float = 0.0
    pct_other_investments: float = 100.0

    # PAI indicator values (for periodic reports and PAI statement)
    pai_indicators: List[PAIIndicatorValue] = field(default_factory=list)

    # Top investments (for periodic reports)
    top_investments: List[Dict[str, Any]] = field(default_factory=list)

    # Reference benchmark
    reference_benchmark_name: str = ""
    reference_benchmark_isin: str = ""
    reference_benchmark_explanation: str = ""

    # Sustainable investment objective (Art 9)
    sustainable_investment_objective: str = ""

    # Entity-level (for PAI statement)
    entity_name: str = ""
    total_investments_covered_eur: float = 0.0
    historical_pai_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DisclosureSection:
    """A single template section within an annex disclosure."""
    section_id: str
    section_title: str
    is_mandatory: bool
    is_populated: bool
    content: Dict[str, Any] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    compliance_notes: List[str] = field(default_factory=list)


@dataclass
class AnnexDisclosureResult:
    """Structured output of a generated SFDR annex disclosure."""
    run_id: str = ""
    annex_id: str = ""                  # "I" | "II" | "III" | "IV" | "V"
    annex_title: str = ""
    fund_id: str = ""
    fund_name: str = ""
    sfdr_classification: str = ""
    report_date: str = ""

    sections: List[DisclosureSection] = field(default_factory=list)

    # Completeness
    mandatory_fields_total: int = 0
    mandatory_fields_populated: int = 0
    optional_fields_total: int = 0
    optional_fields_populated: int = 0
    completeness_pct: float = 0.0
    compliance_status: str = ""         # compliant | partial | non_compliant

    # PAI indicators (for Annex I and periodic reports)
    pai_coverage: Dict[str, Any] = field(default_factory=dict)

    gaps: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SFDRannexEngine:
    """
    SFDR Annex Disclosure Template Engine.

    Generates structured disclosure outputs per RTS 2022/1288 Annexes I–V.
    """

    def generate_annex_i(
        self,
        fund: FundDisclosureInput,
        report_date: Optional[str] = None,
    ) -> AnnexDisclosureResult:
        """
        Generate Annex I — PAI Statement (entity-level, Art 4 SFDR).
        Published on the firm's website; covers all principal adverse impacts
        on sustainability factors at entity level.
        """
        report_date = report_date or date.today().isoformat()
        run_id = f"SFDR-AI-{uuid.uuid4().hex[:8].upper()}"
        sections = []

        # Section 1: Summary
        s1_content = {
            "entity_name": fund.entity_name or fund.fund_manager,
            "statement_date": report_date,
            "reference_period_start": fund.reference_period_start,
            "reference_period_end": fund.reference_period_end,
            "total_investments_covered_eur": fund.total_investments_covered_eur or fund.total_aum_eur,
            "statement_type": "Principal Adverse Impacts on Sustainability Factors",
            "article_reference": "Art 4(1)(a) SFDR + Annex I RTS 2022/1288",
        }
        s1_missing = self._check_fields(s1_content, ["entity_name", "reference_period_start", "reference_period_end", "total_investments_covered_eur"])
        sections.append(DisclosureSection(
            section_id="I.1",
            section_title="Summary",
            is_mandatory=True,
            is_populated=len(s1_missing) == 0,
            content=s1_content,
            missing_fields=s1_missing,
        ))

        # Section 2: PAI Indicator Table (Table 1 — mandatory)
        pai_rows = self._build_pai_table(fund.pai_indicators, mandatory_only=True)
        s2_content = {
            "pai_table_1_mandatory": pai_rows,
            "indicators_covered": len(pai_rows),
            "indicators_required": 14,
        }
        s2_missing = [] if len(pai_rows) >= 14 else [f"Missing PAI indicators 1–14 ({14 - len(pai_rows)} absent)"]
        sections.append(DisclosureSection(
            section_id="I.2",
            section_title="Principal Adverse Impacts — Table 1 (Mandatory Indicators)",
            is_mandatory=True,
            is_populated=len(s2_missing) == 0,
            content=s2_content,
            missing_fields=s2_missing,
        ))

        # Section 3: Additional climate indicators (Table 2 — optional)
        opt_rows = self._build_pai_table(fund.pai_indicators, mandatory_only=False)
        sections.append(DisclosureSection(
            section_id="I.3",
            section_title="Additional Climate + Social Indicators (Table 2/3 — Optional)",
            is_mandatory=False,
            is_populated=len(opt_rows) > 0,
            content={"optional_indicators": opt_rows},
        ))

        # Section 4: Policies to identify and prioritise PAIs
        s4_content = {
            "pai_policy_description": fund.investment_strategy_description,
            "engagement_policy_summary": fund.engagement_policy,
            "international_standards_alignment": "UNPRI, UN Global Compact, OECD Guidelines",
            "due_diligence_description": fund.due_diligence_description,
        }
        s4_missing = self._check_fields(s4_content, ["pai_policy_description", "engagement_policy_summary"])
        sections.append(DisclosureSection(
            section_id="I.4",
            section_title="PAI Policies — Identification and Prioritisation",
            is_mandatory=True,
            is_populated=len(s4_missing) == 0,
            content=s4_content,
            missing_fields=s4_missing,
        ))

        # Section 5: Engagement + historical comparison
        s5_content = {
            "engagement_actions_summary": fund.engagement_policy,
            "historical_comparison": fund.historical_pai_data,
            "future_reduction_targets": "To be populated per entity target-setting",
        }
        sections.append(DisclosureSection(
            section_id="I.5",
            section_title="Engagement and Historical Comparison",
            is_mandatory=True,
            is_populated=bool(fund.engagement_policy),
            content=s5_content,
            missing_fields=[] if fund.engagement_policy else ["engagement_policy"],
        ))

        return self._finalise(
            run_id, "I", "PAI Statement (Art 4 SFDR — Entity Level)",
            fund, report_date, sections, ANNEX_I_MANDATORY_FIELDS, ANNEX_I_OPTIONAL_FIELDS
        )

    def generate_annex_ii(
        self,
        fund: FundDisclosureInput,
        report_date: Optional[str] = None,
    ) -> AnnexDisclosureResult:
        """
        Generate Annex II — Art 8 Pre-contractual Disclosure.
        Inserted into fund prospectus / KID.
        """
        report_date = report_date or date.today().isoformat()
        run_id = f"SFDR-AII-{uuid.uuid4().hex[:8].upper()}"
        sections = []

        # Section 1: Summary (with visual aid — pie chart data)
        s1 = DisclosureSection(
            section_id="II.1",
            section_title="Summary — ESG Characteristics and Asset Allocation",
            is_mandatory=True,
            is_populated=bool(fund.environmental_characteristics or fund.social_characteristics),
            content={
                "fund_name": fund.fund_name,
                "sfdr_classification": fund.sfdr_classification,
                "isin": fund.isin,
                "legal_entity_identifier": fund.legal_entity_identifier,
                "summary_esg_characteristics": (
                    fund.environmental_characteristics + fund.social_characteristics
                ),
                "proportion_sustainable_investments_pct": fund.proportion_sustainable_investments_pct,
                "proportion_taxonomy_aligned_pct": fund.proportion_taxonomy_aligned_pct,
                "asset_allocation_visual": self._build_asset_allocation(fund),
            },
            missing_fields=self._check_fields(
                {"env": fund.environmental_characteristics, "isin": fund.isin, "lei": fund.legal_entity_identifier},
                ["env", "isin", "lei"],
            ),
        )
        sections.append(s1)

        # Section 2: No Significant Harm (DNSH)
        s2 = DisclosureSection(
            section_id="II.2",
            section_title="Does this Financial Product Consider Principal Adverse Impacts (DNSH)?",
            is_mandatory=True,
            is_populated=bool(fund.dnsh_methodology),
            content={
                "dnsh_considered": bool(fund.dnsh_methodology),
                "dnsh_methodology": fund.dnsh_methodology,
                "pai_considered": True,
                "good_governance_assessment": fund.good_governance_assessment_methodology,
            },
            missing_fields=[] if fund.dnsh_methodology else ["dnsh_methodology"],
        )
        sections.append(s2)

        # Section 3: ESG Characteristics
        s3 = DisclosureSection(
            section_id="II.3",
            section_title="Environmental or Social Characteristics",
            is_mandatory=True,
            is_populated=bool(fund.environmental_characteristics or fund.social_characteristics),
            content={
                "environmental_characteristics": fund.environmental_characteristics,
                "social_characteristics": fund.social_characteristics,
                "taxonomy_environmental_objectives": fund.taxonomy_objectives,
            },
            missing_fields=[] if (fund.environmental_characteristics or fund.social_characteristics) else ["environmental_or_social_characteristics"],
        )
        sections.append(s3)

        # Section 4: Investment Strategy
        s4 = DisclosureSection(
            section_id="II.4",
            section_title="Investment Strategy",
            is_mandatory=True,
            is_populated=bool(fund.investment_strategy_description),
            content={
                "investment_strategy_description": fund.investment_strategy_description,
                "binding_esg_criteria": fund.dnsh_methodology,
                "exclusions_applied": "Per fund-level exclusion policy",
            },
            missing_fields=[] if fund.investment_strategy_description else ["investment_strategy_description"],
        )
        sections.append(s4)

        # Section 5: Proportion of Investments (pie chart)
        s5_content = self._build_asset_allocation(fund)
        s5 = DisclosureSection(
            section_id="II.5",
            section_title="Proportion of Investments — Asset Allocation Breakdown",
            is_mandatory=True,
            is_populated=fund.total_aum_eur > 0,
            content=s5_content,
            missing_fields=[] if fund.total_aum_eur > 0 else ["total_aum_eur"],
        )
        sections.append(s5)

        # Section 6: Monitoring
        s6 = DisclosureSection(
            section_id="II.6",
            section_title="Monitoring of ESG Characteristics",
            is_mandatory=True,
            is_populated=bool(fund.engagement_policy or fund.due_diligence_description),
            content={
                "monitoring_methodology": fund.due_diligence_description,
                "sustainability_indicators_used": [
                    ind.indicator_id for ind in fund.pai_indicators
                ] if fund.pai_indicators else [],
                "frequency": "At least annual",
            },
            missing_fields=[] if fund.due_diligence_description else ["monitoring_methodology"],
        )
        sections.append(s6)

        # Section 7: Methodologies
        s7 = DisclosureSection(
            section_id="II.7",
            section_title="Methodologies for ESG Characteristics",
            is_mandatory=True,
            is_populated=bool(fund.dnsh_methodology and fund.data_sources),
            content={
                "dnsh_methodology": fund.dnsh_methodology,
                "data_sources": fund.data_sources,
                "data_limitations": fund.data_limitations,
                "due_diligence": fund.due_diligence_description,
            },
            missing_fields=self._check_fields(
                {"dnsh": fund.dnsh_methodology, "data_sources": fund.data_sources},
                ["dnsh", "data_sources"],
            ),
        )
        sections.append(s7)

        # Section 8: Reference benchmark (optional for Art 8)
        s8 = DisclosureSection(
            section_id="II.8",
            section_title="Reference Benchmark (if designated)",
            is_mandatory=False,
            is_populated=bool(fund.reference_benchmark_name),
            content={
                "benchmark_name": fund.reference_benchmark_name,
                "benchmark_isin": fund.reference_benchmark_isin,
                "alignment_explanation": fund.reference_benchmark_explanation,
            },
        )
        sections.append(s8)

        return self._finalise(
            run_id, "II", "Art 8 Pre-contractual Disclosure (RTS Annex II)",
            fund, report_date, sections, ANNEX_II_MANDATORY_FIELDS, ANNEX_II_OPTIONAL_FIELDS
        )

    def generate_annex_iii(
        self,
        fund: FundDisclosureInput,
        report_date: Optional[str] = None,
    ) -> AnnexDisclosureResult:
        """
        Generate Annex III — Art 8 Periodic Disclosure Report.
        Published post-period alongside fund annual report.
        """
        report_date = report_date or date.today().isoformat()
        run_id = f"SFDR-AIII-{uuid.uuid4().hex[:8].upper()}"
        sections = self._build_periodic_sections(fund, is_art9=False, annex="III")

        return self._finalise(
            run_id, "III", "Art 8 Periodic Disclosure Report (RTS Annex III)",
            fund, report_date, sections, ANNEX_III_MANDATORY_FIELDS, ANNEX_III_OPTIONAL_FIELDS
        )

    def generate_annex_iv(
        self,
        fund: FundDisclosureInput,
        report_date: Optional[str] = None,
    ) -> AnnexDisclosureResult:
        """
        Generate Annex IV — Art 9 Pre-contractual Disclosure.
        Inserted into prospectus / KID for sustainable investment objective funds.
        """
        report_date = report_date or date.today().isoformat()
        run_id = f"SFDR-AIV-{uuid.uuid4().hex[:8].upper()}"

        # Start with Annex II sections, then add Art 9 specific sections
        base_result = self.generate_annex_ii(fund, report_date)
        sections = base_result.sections.copy()

        # Art 9 additional section: Sustainable Investment Objective
        s_obj = DisclosureSection(
            section_id="IV.9",
            section_title="Sustainable Investment Objective",
            is_mandatory=True,
            is_populated=bool(fund.sustainable_investment_objective),
            content={
                "sustainable_investment_objective": fund.sustainable_investment_objective,
                "sustainable_investment_min_pct": fund.sustainable_investment_min_pct,
                "taxonomy_aligned_min_pct": fund.taxonomy_aligned_min_pct,
                "taxonomy_objectives": fund.taxonomy_objectives,
            },
            missing_fields=[] if fund.sustainable_investment_objective else ["sustainable_investment_objective"],
        )
        sections.append(s_obj)

        # Art 9: DNSH binding criteria (stronger requirement than Art 8)
        s_dnsh = DisclosureSection(
            section_id="IV.10",
            section_title="Do No Significant Harm — Binding Criteria (Art 9)",
            is_mandatory=True,
            is_populated=bool(fund.dnsh_methodology),
            content={
                "dnsh_binding_criteria": fund.dnsh_methodology,
                "good_governance_assessment": fund.good_governance_assessment_methodology,
                "taxonomy_environmental_objectives": fund.taxonomy_objectives,
                "minimum_sustainable_investment_pct": fund.sustainable_investment_min_pct,
            },
            missing_fields=self._check_fields(
                {"dnsh": fund.dnsh_methodology, "obj": fund.sustainable_investment_objective},
                ["dnsh", "obj"],
            ),
        )
        sections.append(s_dnsh)

        return self._finalise(
            run_id, "IV", "Art 9 Pre-contractual Disclosure (RTS Annex IV)",
            fund, report_date, sections, ANNEX_IV_MANDATORY_FIELDS, ANNEX_IV_OPTIONAL_FIELDS
        )

    def generate_annex_v(
        self,
        fund: FundDisclosureInput,
        report_date: Optional[str] = None,
    ) -> AnnexDisclosureResult:
        """
        Generate Annex V — Art 9 Periodic Disclosure Report.
        Published post-period alongside fund annual report.
        """
        report_date = report_date or date.today().isoformat()
        run_id = f"SFDR-AV-{uuid.uuid4().hex[:8].upper()}"
        sections = self._build_periodic_sections(fund, is_art9=True, annex="V")

        return self._finalise(
            run_id, "V", "Art 9 Periodic Disclosure Report (RTS Annex V)",
            fund, report_date, sections, ANNEX_V_MANDATORY_FIELDS, ANNEX_V_OPTIONAL_FIELDS
        )

    def validate_disclosure(
        self,
        fund: FundDisclosureInput,
        annex_id: str,
    ) -> Dict[str, Any]:
        """
        Validate completeness and RTS compliance of a disclosure without generating
        the full output. Returns field-level validation results.
        """
        annex_gen = {
            "I": self.generate_annex_i,
            "II": self.generate_annex_ii,
            "III": self.generate_annex_iii,
            "IV": self.generate_annex_iv,
            "V": self.generate_annex_v,
        }
        if annex_id not in annex_gen:
            return {"error": f"Unknown annex_id '{annex_id}'. Use I, II, III, IV, or V."}

        result = annex_gen[annex_id](fund)
        return {
            "annex_id": annex_id,
            "fund_name": fund.fund_name,
            "sfdr_classification": fund.sfdr_classification,
            "completeness_pct": result.completeness_pct,
            "compliance_status": result.compliance_status,
            "mandatory_populated": result.mandatory_fields_populated,
            "mandatory_total": result.mandatory_fields_total,
            "optional_populated": result.optional_fields_populated,
            "optional_total": result.optional_fields_total,
            "missing_mandatory": result.gaps,
            "priority_actions": result.priority_actions,
            "section_detail": [
                {
                    "section_id": s.section_id,
                    "title": s.section_title,
                    "mandatory": s.is_mandatory,
                    "populated": s.is_populated,
                    "missing_fields": s.missing_fields,
                }
                for s in result.sections
            ],
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _build_periodic_sections(
        self, fund: FundDisclosureInput, is_art9: bool, annex: str
    ) -> List[DisclosureSection]:
        sections = []
        prefix = annex

        # Summary
        sections.append(DisclosureSection(
            section_id=f"{prefix}.1",
            section_title="To What Extent Were the ESG Characteristics / Sustainable Investment Objective Attained?",
            is_mandatory=True,
            is_populated=bool(fund.reference_period_start),
            content={
                "reference_period_start": fund.reference_period_start,
                "reference_period_end": fund.reference_period_end,
                "esg_characteristics_attained": fund.environmental_characteristics + fund.social_characteristics,
                "proportion_sustainable_pct_achieved": fund.proportion_sustainable_investments_pct,
                "taxonomy_aligned_pct_achieved": fund.proportion_taxonomy_aligned_pct,
                "sustainable_investment_objective_achieved": fund.sustainable_investment_objective if is_art9 else None,
            },
            missing_fields=[] if fund.reference_period_start else ["reference_period_start"],
        ))

        # Top investments
        sections.append(DisclosureSection(
            section_id=f"{prefix}.2",
            section_title="Top Investments (Top 15 by weight)",
            is_mandatory=True,
            is_populated=bool(fund.top_investments),
            content={"top_investments": fund.top_investments[:15]},
            missing_fields=[] if fund.top_investments else ["top_investments_list"],
        ))

        # Asset allocation pie chart
        sections.append(DisclosureSection(
            section_id=f"{prefix}.3",
            section_title="Asset Allocation — Proportion Breakdown",
            is_mandatory=True,
            is_populated=fund.total_aum_eur > 0,
            content=self._build_asset_allocation(fund),
            missing_fields=[] if fund.total_aum_eur > 0 else ["asset_allocation_data"],
        ))

        # PAI summary table (mandatory 14 indicators)
        pai_rows = self._build_pai_table(fund.pai_indicators, mandatory_only=True)
        sections.append(DisclosureSection(
            section_id=f"{prefix}.4",
            section_title="Sustainability Indicators — PAI Summary Table",
            is_mandatory=True,
            is_populated=len(pai_rows) >= 1,
            content={"pai_summary": pai_rows, "indicators_reported": len(pai_rows)},
            missing_fields=[] if pai_rows else ["pai_indicator_values"],
        ))

        # Data sources + limitations
        sections.append(DisclosureSection(
            section_id=f"{prefix}.5",
            section_title="Data Sources, Processing and Limitations",
            is_mandatory=True,
            is_populated=bool(fund.data_sources),
            content={
                "data_sources": fund.data_sources,
                "limitations": fund.data_limitations,
                "due_diligence": fund.due_diligence_description,
            },
            missing_fields=[] if fund.data_sources else ["data_sources"],
        ))

        # Engagement
        sections.append(DisclosureSection(
            section_id=f"{prefix}.6",
            section_title="Engagement Policies Applied",
            is_mandatory=True,
            is_populated=bool(fund.engagement_policy),
            content={"engagement_policy": fund.engagement_policy},
            missing_fields=[] if fund.engagement_policy else ["engagement_policy"],
        ))

        # Art 9 specific: DNSH confirmation + sustainable investment results
        if is_art9:
            sections.append(DisclosureSection(
                section_id=f"{prefix}.7",
                section_title="Sustainable Investment Results — DNSH and Good Governance Confirmation",
                is_mandatory=True,
                is_populated=bool(fund.sustainable_investment_objective),
                content={
                    "sustainable_investment_objective_achieved": fund.sustainable_investment_objective,
                    "sustainable_investment_pct_achieved": fund.proportion_sustainable_investments_pct,
                    "taxonomy_alignment_pct_achieved": fund.proportion_taxonomy_aligned_pct,
                    "dnsh_compliance_confirmation": bool(fund.dnsh_methodology),
                    "good_governance_confirmation": bool(fund.good_governance_assessment_methodology),
                },
                missing_fields=[] if fund.sustainable_investment_objective else ["sustainable_investment_objective"],
            ))

        return sections

    @staticmethod
    def _build_asset_allocation(fund: FundDisclosureInput) -> Dict[str, Any]:
        """Build the RTS-required pie chart data for asset allocation section."""
        total = fund.total_aum_eur or 1.0
        tax_aligned = fund.proportion_taxonomy_aligned_pct
        sus_env = max(fund.pct_sustainable_environmental - tax_aligned, 0)
        sus_soc = fund.pct_sustainable_social
        other = max(100 - tax_aligned - sus_env - sus_soc, 0)

        return {
            "taxonomy_aligned_environmental_pct": round(tax_aligned, 1),
            "other_environmental_pct": round(sus_env, 1),
            "sustainable_social_pct": round(sus_soc, 1),
            "other_investments_pct": round(other, 1),
            "total_aum_eur": total,
            "rts_reference": "RTS Annex II/III/IV/V — Proportionality section",
        }

    @staticmethod
    def _build_pai_table(
        indicators: List[PAIIndicatorValue],
        mandatory_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Render PAI indicators into the RTS table format."""
        rows = []
        ind_idx = {ind.indicator_id: ind for ind in indicators}

        for ind_id, meta in PAI_INDICATOR_REGISTRY.items():
            if mandatory_only and not meta["mandatory"]:
                continue
            ind = ind_idx.get(ind_id)
            rows.append({
                "indicator_id": ind_id,
                "description": meta["description"],
                "metric": meta["metric"],
                "value": ind.value if ind else None,
                "unit": meta["metric"].split("(")[0].strip() if ind and ind.value is not None else "",
                "data_quality_score_pcaf": ind.data_quality_score if ind else None,
                "coverage_pct": ind.coverage_pct if ind else 0.0,
                "data_source": ind.data_source if ind else "",
                "actions_taken": ind.actions_taken if ind else "",
                "target_value": ind.target_value if ind else None,
                "target_date": ind.target_date if ind else "",
                "populated": ind is not None and ind.value is not None,
                "mandatory": meta["mandatory"],
            })
        return rows

    @staticmethod
    def _check_fields(content: Dict[str, Any], required_keys: List[str]) -> List[str]:
        missing = []
        for k in required_keys:
            v = content.get(k)
            if v is None or v == "" or v == [] or v == {}:
                missing.append(k)
        return missing

    def _finalise(
        self,
        run_id: str,
        annex_id: str,
        annex_title: str,
        fund: FundDisclosureInput,
        report_date: str,
        sections: List[DisclosureSection],
        mandatory_fields: List[str],
        optional_fields: List[str],
    ) -> AnnexDisclosureResult:
        mandatory_pop = sum(1 for s in sections if s.is_mandatory and s.is_populated)
        mandatory_total = sum(1 for s in sections if s.is_mandatory)
        optional_pop = sum(1 for s in sections if not s.is_mandatory and s.is_populated)
        optional_total = sum(1 for s in sections if not s.is_mandatory)

        completeness = (
            mandatory_pop / max(mandatory_total, 1) * 100
            if mandatory_total > 0 else 0.0
        )
        compliance_status = (
            "compliant" if completeness >= 95
            else "partial" if completeness >= 60
            else "non_compliant"
        )

        gaps: List[str] = []
        actions: List[str] = []
        for s in sections:
            if s.is_mandatory and s.missing_fields:
                for mf in s.missing_fields:
                    gaps.append(f"[{s.section_id}] {mf}")
                    actions.append(f"Populate mandatory field '{mf}' in section {s.section_id} ({s.section_title})")

        # PAI coverage
        mandatory_pais = [r for r in self._build_pai_table(fund.pai_indicators, True)]
        populated_pais = [r for r in mandatory_pais if r["populated"]]
        pai_coverage = {
            "mandatory_indicators_total": len(mandatory_pais),
            "mandatory_indicators_populated": len(populated_pais),
            "pai_coverage_pct": round(len(populated_pais) / max(len(mandatory_pais), 1) * 100, 1),
        }

        return AnnexDisclosureResult(
            run_id=run_id,
            annex_id=annex_id,
            annex_title=annex_title,
            fund_id=fund.fund_id,
            fund_name=fund.fund_name,
            sfdr_classification=fund.sfdr_classification,
            report_date=report_date,
            sections=sections,
            mandatory_fields_total=mandatory_total,
            mandatory_fields_populated=mandatory_pop,
            optional_fields_total=optional_total,
            optional_fields_populated=optional_pop,
            completeness_pct=round(completeness, 1),
            compliance_status=compliance_status,
            pai_coverage=pai_coverage,
            gaps=gaps[:10],
            priority_actions=actions[:6],
            metadata={
                "regulation": "SFDR (EU) 2019/2088 + RTS (EU) 2022/1288",
                "annex_reference": f"Annex {annex_id} — {annex_title}",
                "engine_version": "E9.1",
                "reference": (
                    "EU Regulation 2019/2088 (SFDR) | "
                    "EU Delegated Regulation 2022/1288 (RTS) | "
                    "ESMA Q&A SFDR 2023/ESMA36-43-2498"
                ),
            },
        )
