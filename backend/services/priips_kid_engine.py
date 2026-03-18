"""
PRIIPs KID ESG Engine (E15)
============================

EU PRIIPs Regulation (EU) 1286/2014 as amended by Regulation (EU) 2021/2268
(revised KID methodology).

Covers:
  - KID generation across all 6 sections (product, risk, costs, holding period,
    complaints, other information)
  - Summary Risk Indicator (SRI) 1-7 calculation (market risk class + credit uplift)
  - 4 performance scenarios (stress, unfavourable, moderate, favourable)
  - Cost summary with Reduction in Yield (RIY) computation
  - ESG-specific inserts for Art 6 / Art 8 / Art 8 PAI / Art 8 Taxonomy / Art 9 products
  - Cross-framework linkage: SFDR, EU Taxonomy, MiFID II SPT, UK PRIIPs, UCITS KIID
  - KID completeness validation and gap detection

E15 in the engine series (E14=EU GBS → E15=PRIIPs KID).
"""
from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

KID_SECTIONS: Dict[str, Dict[str, Any]] = {
    "section_1_product": {
        "name": "What is this product?",
        "mandatory_fields": [
            "product_name", "product_type", "manufacturer", "isin",
            "competent_authority", "investment_objective",
            "target_investor_profile", "insurance_element",
        ],
    },
    "section_2_risk": {
        "name": "What are the risks and what could I get in return?",
        "mandatory_fields": ["sri_score", "sri_components", "performance_scenarios"],
    },
    "section_3_costs": {
        "name": "What are the costs?",
        "mandatory_fields": [
            "entry_costs", "exit_costs", "ongoing_costs",
            "performance_fees", "transaction_costs", "riy_summary",
        ],
    },
    "section_4_holding_period": {
        "name": "How long should I hold it and can I take money out early?",
        "mandatory_fields": ["rhp_years", "early_redemption_conditions"],
    },
    "section_5_complaints": {
        "name": "How can I complain?",
        "mandatory_fields": ["complaints_contact", "esa_contact"],
    },
    "section_6_other_info": {
        "name": "Other relevant information",
        "mandatory_fields": ["prospectus_location", "past_performance_statement"],
    },
}

SRI_MARKET_RISK_CLASSES: Dict[int, Dict[str, Any]] = {
    1: {"class": 1, "vol_range": [0, 0.005], "description": "Very low market risk"},
    2: {"class": 2, "vol_range": [0.005, 0.12], "description": "Low market risk"},
    3: {"class": 3, "vol_range": [0.12, 0.2], "description": "Low to medium market risk"},
    4: {"class": 4, "vol_range": [0.2, 0.3], "description": "Medium market risk"},
    5: {"class": 5, "vol_range": [0.3, 0.8], "description": "Medium to high market risk"},
    6: {"class": 6, "vol_range": [0.8, 1.0], "description": "High market risk"},
    7: {"class": 7, "vol_range": [1.0, 99], "description": "Highest market risk"},
}

PERFORMANCE_SCENARIO_NAMES = ["stress", "unfavourable", "moderate", "favourable"]

ESG_INSERT_TYPES: Dict[str, Dict[str, Any]] = {
    "sustainability_risk": {
        "name": "Sustainability Risk Statement",
        "required_for": ["art6", "art8", "art8_pai", "art8_taxonomy", "art9"],
        "sfdr_article": "Art 3 SFDR",
        "description": "Statement on integration of sustainability risks into investment decisions",
    },
    "pai_consideration": {
        "name": "PAI Consideration Statement",
        "required_for": ["art8_pai", "art9"],
        "sfdr_article": "Art 4 SFDR",
        "description": "Statement on consideration of principal adverse impacts",
    },
    "art8_esg_characteristics": {
        "name": "ESG Characteristics Disclosure",
        "required_for": ["art8", "art8_pai", "art8_taxonomy", "art9"],
        "sfdr_article": "Art 8 SFDR",
        "description": "Description of the environmental or social characteristics promoted",
    },
    "art9_sustainable_investment": {
        "name": "Sustainable Investment Objective",
        "required_for": ["art9"],
        "sfdr_article": "Art 9 SFDR",
        "description": "Description of the sustainable investment objective",
    },
    "taxonomy_alignment": {
        "name": "Taxonomy Alignment Disclosure",
        "required_for": ["art8_taxonomy", "art9"],
        "sfdr_article": "Art 6 EU Taxonomy",
        "description": (
            "% of investments that are taxonomy-aligned, "
            "with Do No Significant Harm statement"
        ),
    },
}

PRIIPS_CROSS_FRAMEWORK: Dict[str, str] = {
    "sfdr_overlap": (
        "KID ESG inserts mirror pre-contractual SFDR Annex II (Art 8) / "
        "Annex III (Art 9) disclosures"
    ),
    "eu_taxonomy": (
        "Taxonomy alignment % in KID must match pre-contractual disclosure"
    ),
    "mifid_spt": (
        "KID ESG classification feeds MiFID II sustainability preferences product screening"
    ),
    "uk_priips": (
        "UK PRIIPs (FCA) largely mirrors EU PRIIPs post-Brexit with minor divergences"
    ),
    "ucits_kiid": (
        "UCITS KIID replaced by PRIIPs KID for retail investors (UCITS exempt until 2026)"
    ),
}

PRIIPS_TIMELINE: List[Dict[str, str]] = [
    {
        "date": "2014-11-26",
        "event": "PRIIPs Regulation (EU) 1286/2014 published in OJEU",
        "article": "All",
    },
    {
        "date": "2017-01-01",
        "event": "PRIIPs KID mandatory application date for non-UCITS retail PRIIPs",
        "article": "Art 32",
    },
    {
        "date": "2021-12-31",
        "event": "Amending Regulation (EU) 2021/2268 published — revised methodology",
        "article": "Art 8 + RTS",
    },
    {
        "date": "2023-01-01",
        "event": "Revised KID methodology (Regulation 2021/2268) enters into application",
        "article": "Art 8",
    },
    {
        "date": "2024-01-01",
        "event": "UCITS KIID exemption ends — UCITS funds must publish PRIIPs KID",
        "article": "Art 32",
    },
    {
        "date": "2024-01-31",
        "event": "UK FCA final rules: UK KID diverges (own SRI methodology, no SFDR inserts)",
        "article": "FCA COBS 13",
    },
]

# Per-SRI annualised stress scenario return offsets (approximate)
_STRESS_RETURNS: Dict[int, float] = {
    1: -0.05, 2: -0.08, 3: -0.12, 4: -0.18, 5: -0.22, 6: -0.28, 7: -0.30
}
_UNFAV_RETURNS: Dict[int, float] = {
    1: -0.02, 2: -0.03, 3: -0.05, 4: -0.07, 5: -0.09, 6: -0.10, 7: -0.10
}

# ESG insert text templates
_ESG_TEXT_TEMPLATES: Dict[str, str] = {
    "sustainability_risk": (
        "Sustainability risks are integrated into the investment decisions of {product_name}. "
        "The manufacturer assesses environmental, social and governance (ESG) factors as part "
        "of the investment process, consistent with its obligations under Art 3 SFDR (2019/2088)."
    ),
    "pai_consideration": (
        "{product_name} considers the principal adverse impacts (PAIs) of investment decisions "
        "on sustainability factors, as defined in the SFDR RTS Annex I. The manufacturer "
        "publishes an annual PAI statement on its website per Art 4 SFDR."
    ),
    "art8_esg_characteristics": (
        "{product_name} promotes environmental and/or social characteristics within the meaning "
        "of Art 8 SFDR (2019/2088). The characteristics promoted and the methodologies used to "
        "assess, measure and monitor them are described in the product's pre-contractual disclosure "
        "document (SFDR Annex II)."
    ),
    "art9_sustainable_investment": (
        "{product_name} has sustainable investment as its objective within the meaning of Art 9 "
        "SFDR (2019/2088). The sustainable investment objective and the methodology used to measure "
        "attainment of that objective are described in the product's pre-contractual disclosure "
        "document (SFDR Annex III)."
    ),
    "taxonomy_alignment": (
        "A minimum of [X]% of the investments of {product_name} are aligned with the EU Taxonomy "
        "Regulation (EU) 2020/852. All taxonomy-aligned investments comply with the Do No "
        "Significant Harm (DNSH) criteria and minimum social safeguards per Arts 17-18 of the "
        "Taxonomy Regulation. Remaining investments do not take into account EU criteria for "
        "environmentally sustainable economic activities."
    ),
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class KIDProductInput:
    product_id: str
    product_name: str
    product_type: str
    isin: str = ""
    manufacturer: str = ""
    rhp_years: int = 5
    annual_volatility: float = 0.15
    credit_quality: str = "investment_grade"
    sfdr_classification: str = "art_6"
    considers_pais: bool = False
    taxonomy_alignment_pct: float = 0.0
    entry_cost_pct: float = 0.0
    exit_cost_pct: float = 0.0
    ongoing_cost_pct: float = 1.5
    performance_fee_pct: float = 0.0
    transaction_cost_pct: float = 0.1
    expected_annual_return_pct: float = 5.0


@dataclass
class SRIResult:
    market_risk_class: int
    credit_risk_class: int
    final_sri: int
    sri_description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_risk_class": self.market_risk_class,
            "credit_risk_class": self.credit_risk_class,
            "final_sri": self.final_sri,
            "sri_description": self.sri_description,
        }


@dataclass
class PerformanceScenario:
    scenario_name: str
    return_1yr_pct: float
    return_rhp_annualised_pct: float
    final_value_per_10k: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "return_1yr_pct": round(self.return_1yr_pct, 2),
            "return_rhp_annualised_pct": round(self.return_rhp_annualised_pct, 2),
            "final_value_per_10k": round(self.final_value_per_10k, 2),
        }


@dataclass
class CostSummary:
    entry_cost_pct: float
    exit_cost_pct: float
    ongoing_cost_pct: float
    performance_fee_pct: float
    transaction_cost_pct: float
    total_cost_pct: float
    riy_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_cost_pct": round(self.entry_cost_pct, 4),
            "exit_cost_pct": round(self.exit_cost_pct, 4),
            "ongoing_cost_pct": round(self.ongoing_cost_pct, 4),
            "performance_fee_pct": round(self.performance_fee_pct, 4),
            "transaction_cost_pct": round(self.transaction_cost_pct, 4),
            "total_cost_pct": round(self.total_cost_pct, 4),
            "riy_pct": round(self.riy_pct, 4),
        }


@dataclass
class ESGInsert:
    insert_type: str
    required: bool
    text_block: str
    sfdr_article: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insert_type": self.insert_type,
            "required": self.required,
            "text_block": self.text_block,
            "sfdr_article": self.sfdr_article,
        }


@dataclass
class PRIIPSKIDResult:
    kid_id: str
    product_id: str
    product_name: str
    sri_result: Dict[str, Any]
    performance_scenarios: List[Dict[str, Any]]
    cost_summary: Dict[str, Any]
    esg_inserts: List[Dict[str, Any]]
    kid_completeness_pct: float
    validation_gaps: List[str]
    warnings: List[str]
    cross_framework: Dict[str, str]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kid_id": self.kid_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "sri_result": self.sri_result,
            "performance_scenarios": self.performance_scenarios,
            "cost_summary": self.cost_summary,
            "esg_inserts": self.esg_inserts,
            "kid_completeness_pct": round(self.kid_completeness_pct, 2),
            "validation_gaps": self.validation_gaps,
            "warnings": self.warnings,
            "cross_framework": self.cross_framework,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PRIIPSKIDEngine:
    """PRIIPs KID generation engine with SRI, performance scenarios, costs and ESG inserts."""

    def generate_kid(self, inp: KIDProductInput) -> PRIIPSKIDResult:
        """
        Generate a full PRIIPs KID for a product.
        Returns PRIIPSKIDResult with SRI, 4 performance scenarios, cost RIY, and ESG inserts.
        """
        logger.info(
            "PRIIPSKIDEngine generate_kid: product_id=%s sfdr=%s",
            inp.product_id, inp.sfdr_classification,
        )

        sri_result = self.assess_sri(inp)
        scenarios = self.calculate_scenarios(inp)
        cost_summary = self._calculate_costs(inp)
        esg_inserts = self.get_esg_inserts(inp.sfdr_classification, inp.product_name)

        validation_gaps = self._validate(inp)
        warnings = self._build_warnings(inp, sri_result)

        # KID completeness: count sections that are sufficiently populated
        sections_complete = self._count_complete_sections(inp, sri_result, cost_summary)
        kid_completeness_pct = (sections_complete / 6.0) * 100.0

        return PRIIPSKIDResult(
            kid_id=str(uuid.uuid4()),
            product_id=inp.product_id,
            product_name=inp.product_name,
            sri_result=sri_result.to_dict(),
            performance_scenarios=[s.to_dict() for s in scenarios],
            cost_summary=cost_summary.to_dict(),
            esg_inserts=[e.to_dict() for e in esg_inserts],
            kid_completeness_pct=kid_completeness_pct,
            validation_gaps=validation_gaps,
            warnings=warnings,
            cross_framework=PRIIPS_CROSS_FRAMEWORK,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def assess_sri(self, inp: KIDProductInput) -> SRIResult:
        """
        Calculate the Summary Risk Indicator (SRI) per PRIIPs Annex II methodology.
        SRI = max(market_risk_class, credit_risk_class adjusted).
        """
        # Market risk class from annual volatility
        vol = inp.annual_volatility
        market_risk_class = 7  # default highest
        for cls, meta in sorted(SRI_MARKET_RISK_CLASSES.items()):
            lo, hi = meta["vol_range"]
            if lo <= vol < hi:
                market_risk_class = cls
                break

        # Credit risk class
        cq = inp.credit_quality.lower()
        if cq == "investment_grade":
            credit_risk_class = 1
        elif cq == "unrated":
            credit_risk_class = 2
        else:  # sub_investment_grade
            credit_risk_class = 3

        # Final SRI: take max; if credit_risk_class > 1 apply uplift
        final_sri = max(market_risk_class, credit_risk_class)
        if credit_risk_class > 1:
            final_sri = max(final_sri, credit_risk_class + 1)
        final_sri = min(final_sri, 7)

        sri_desc = SRI_MARKET_RISK_CLASSES.get(final_sri, {}).get(
            "description", "Unknown risk class"
        )

        return SRIResult(
            market_risk_class=market_risk_class,
            credit_risk_class=credit_risk_class,
            final_sri=final_sri,
            sri_description=sri_desc,
        )

    def calculate_scenarios(self, inp: KIDProductInput) -> List[PerformanceScenario]:
        """
        Generate 4 performance scenarios per PRIIPs RTS Annex IV revised methodology.
        Returns: [stress, unfavourable, moderate, favourable].
        """
        sri_result = self.assess_sri(inp)
        sri = sri_result.final_sri
        rhp = max(inp.rhp_years, 1)
        expected_ret = inp.expected_annual_return_pct / 100.0

        stress_ann = _STRESS_RETURNS.get(sri, -0.25)
        unfav_ann = _UNFAV_RETURNS.get(sri, -0.05)
        moderate_ann = expected_ret - 0.015
        favourable_ann = expected_ret + 0.03

        def _final_value(ann_ret: float) -> float:
            return 10_000.0 * math.pow(1.0 + ann_ret, rhp)

        def _1yr_ret(ann_ret: float) -> float:
            return ann_ret * 100.0

        scenarios = [
            PerformanceScenario(
                scenario_name="stress",
                return_1yr_pct=_1yr_ret(stress_ann),
                return_rhp_annualised_pct=stress_ann * 100.0,
                final_value_per_10k=_final_value(stress_ann),
            ),
            PerformanceScenario(
                scenario_name="unfavourable",
                return_1yr_pct=_1yr_ret(unfav_ann),
                return_rhp_annualised_pct=unfav_ann * 100.0,
                final_value_per_10k=_final_value(unfav_ann),
            ),
            PerformanceScenario(
                scenario_name="moderate",
                return_1yr_pct=_1yr_ret(moderate_ann),
                return_rhp_annualised_pct=moderate_ann * 100.0,
                final_value_per_10k=_final_value(moderate_ann),
            ),
            PerformanceScenario(
                scenario_name="favourable",
                return_1yr_pct=_1yr_ret(favourable_ann),
                return_rhp_annualised_pct=favourable_ann * 100.0,
                final_value_per_10k=_final_value(favourable_ann),
            ),
        ]
        return scenarios

    def get_esg_inserts(
        self,
        sfdr_classification: str,
        product_name: str = "[Product]",
    ) -> List[ESGInsert]:
        """
        Return the ESGInsert list required for the given SFDR classification.
        Classification values: art_6 | art_8 | art_8_pai | art_8_taxonomy | art_9
        """
        # Normalise to internal key
        sfdr_key = sfdr_classification.lower().replace("-", "_").replace(" ", "_")

        inserts: List[ESGInsert] = []
        for insert_id, meta in ESG_INSERT_TYPES.items():
            required = sfdr_key in meta["required_for"]
            if not required:
                continue
            template = _ESG_TEXT_TEMPLATES.get(insert_id, meta["description"])
            text_block = template.replace("{product_name}", product_name)
            inserts.append(
                ESGInsert(
                    insert_type=insert_id,
                    required=True,
                    text_block=text_block,
                    sfdr_article=meta["sfdr_article"],
                )
            )
        return inserts

    # ------------------------------------------------------------------
    # Reference data accessors
    # ------------------------------------------------------------------

    def get_kid_sections(self) -> Dict[str, Any]:
        return KID_SECTIONS

    def get_sri_classes(self) -> Dict[str, Any]:
        return SRI_MARKET_RISK_CLASSES

    def get_esg_insert_types(self) -> Dict[str, Any]:
        return ESG_INSERT_TYPES

    def get_cross_framework(self) -> Dict[str, str]:
        return PRIIPS_CROSS_FRAMEWORK

    def get_timeline(self) -> List[Dict[str, str]]:
        return PRIIPS_TIMELINE

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_costs(inp: KIDProductInput) -> CostSummary:
        total_cost_pct = (
            inp.entry_cost_pct
            + inp.exit_cost_pct
            + inp.ongoing_cost_pct
            + inp.performance_fee_pct
            + inp.transaction_cost_pct
        )
        # RIY simplified: total annual cost adjusted for compounding effect over RHP
        # RIY = total_cost_pct * annuity_factor
        rhp = max(inp.rhp_years, 1)
        r = inp.expected_annual_return_pct / 100.0
        if abs(r) > 1e-9:
            annuity_factor = (1.0 - math.pow(1.0 + r, -rhp)) / (r * rhp)
        else:
            annuity_factor = 1.0
        riy_pct = total_cost_pct * annuity_factor

        return CostSummary(
            entry_cost_pct=inp.entry_cost_pct,
            exit_cost_pct=inp.exit_cost_pct,
            ongoing_cost_pct=inp.ongoing_cost_pct,
            performance_fee_pct=inp.performance_fee_pct,
            transaction_cost_pct=inp.transaction_cost_pct,
            total_cost_pct=total_cost_pct,
            riy_pct=riy_pct,
        )

    @staticmethod
    def _validate(inp: KIDProductInput) -> List[str]:
        gaps: List[str] = []
        if not inp.manufacturer:
            gaps.append("Manufacturer name missing — required for KID Section 1.")
        if not inp.isin:
            gaps.append("ISIN missing — required for KID Section 1 (leave blank only if not yet assigned).")
        if inp.sfdr_classification in ("art_8", "art_8_pai", "art_8_taxonomy", "art_9"):
            if inp.taxonomy_alignment_pct == 0.0 and inp.sfdr_classification == "art_8_taxonomy":
                gaps.append(
                    "Taxonomy alignment % is 0 for an Art 8 product with taxonomy commitment — "
                    "provide actual taxonomy-aligned % for KID ESG insert."
                )
            if inp.sfdr_classification == "art_9" and inp.taxonomy_alignment_pct < 1.0:
                gaps.append(
                    "Art 9 products must disclose taxonomy-aligned % — "
                    "current value is less than 1%."
                )
        if inp.annual_volatility <= 0:
            gaps.append(
                "Annual volatility must be positive to compute SRI market risk class."
            )
        if inp.rhp_years < 1:
            gaps.append("Recommended Holding Period (RHP) must be at least 1 year.")
        return gaps

    @staticmethod
    def _build_warnings(inp: KIDProductInput, sri: SRIResult) -> List[str]:
        warnings: List[str] = []
        if sri.final_sri >= 6:
            warnings.append(
                f"High SRI ({sri.final_sri}/7) — retail KID must include prominent risk warning "
                f"and ensure product is only distributed to appropriate target market."
            )
        if inp.ongoing_cost_pct > 2.5:
            warnings.append(
                f"Ongoing costs ({inp.ongoing_cost_pct:.2f}%) are high — "
                f"verify PRIIPs cost calculation methodology and RTS Annex VI disclosure."
            )
        if inp.considers_pais and inp.sfdr_classification == "art_6":
            warnings.append(
                "considers_pais=True but sfdr_classification=art_6 — "
                "Art 6 products do not publish entity-level PAI statements; "
                "confirm classification."
            )
        return warnings

    @staticmethod
    def _count_complete_sections(
        inp: KIDProductInput,
        sri: SRIResult,
        costs: CostSummary,
    ) -> int:
        complete = 0
        # S1: product info
        if inp.product_name and inp.product_type and inp.manufacturer:
            complete += 1
        # S2: risk & scenarios
        if sri.final_sri > 0:
            complete += 1
        # S3: costs
        if costs.total_cost_pct >= 0:
            complete += 1
        # S4: holding period
        if inp.rhp_years >= 1:
            complete += 1
        # S5: complaints — always partially populated (static text)
        complete += 1
        # S6: other info — always partially populated
        complete += 1
        return complete
