"""
MiFID II Sustainability Preferences Engine (E12)
=================================================

EC Delegated Regulation 2021/1253 amending MiFID II Delegated Regulation 2017/565,
Art 2(7) sustainability preference categories and Art 25(2) suitability process.

Covers:
  - 3 preference categories: Category A (EU Taxonomy), Category B (SFDR Sustainable
    Investments), Category C (PAI Consideration)
  - Art 25(2) suitability assessment process (5-step)
  - Product ESG type mapping (Art 6 / Art 8 / Art 9 SFDR)
  - Preference matching and gap analysis
  - Suitability report text generation
  - Cross-framework linkage to SFDR, EU Taxonomy, CSRD, EBA ESG

E12 in the engine series (E11=UK SDR → E12=MiFID II SPT → E13=...).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

PREFERENCE_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "category_a": {
        "id": "category_a",
        "name": "EU Taxonomy-Aligned",
        "description": "Minimum % of investments to be taxonomy-aligned per Regulation (EU) 2020/852",
        "article": "Art 2(7)(a) MiFID II + Art 2(1) EU Taxonomy Regulation",
        "metric": "taxonomy_alignment_pct",
        "min_threshold_pct": 0.0,
        "effective_date": "2022-08-02",
    },
    "category_b": {
        "id": "category_b",
        "name": "SFDR Sustainable Investments",
        "description": "Minimum % of sustainable investments per Art 2(17) SFDR",
        "article": "Art 2(7)(b) MiFID II + Art 2(17) SFDR 2019/2088",
        "metric": "sfdr_sustainable_investment_pct",
        "min_threshold_pct": 0.0,
        "effective_date": "2022-08-02",
    },
    "category_c": {
        "id": "category_c",
        "name": "PAI Consideration",
        "description": "Products considering principal adverse impacts on sustainability factors per SFDR RTS Annex I",
        "article": "Art 2(7)(c) MiFID II + Art 4 SFDR",
        "metric": "considers_pais",
        "min_threshold_pct": None,
        "effective_date": "2022-08-02",
    },
}

PRODUCT_ESG_TYPES: Dict[str, Dict[str, Any]] = {
    "article_9": {
        "sfdr_article": "art_9",
        "min_sustainable_pct": 100,
        "pais_considered": True,
        "typical_taxonomy_pct": 15,
    },
    "article_8_with_commitment": {
        "sfdr_article": "art_8",
        "min_sustainable_pct": 10,
        "pais_considered": True,
        "typical_taxonomy_pct": 5,
    },
    "article_8_without_commitment": {
        "sfdr_article": "art_8",
        "min_sustainable_pct": 0,
        "pais_considered": False,
        "typical_taxonomy_pct": 0,
    },
    "article_6": {
        "sfdr_article": "art_6",
        "min_sustainable_pct": 0,
        "pais_considered": False,
        "typical_taxonomy_pct": 0,
    },
}

SUITABILITY_PROCESS_STEPS: List[Dict[str, Any]] = [
    {
        "step": 1,
        "name": "Collect client preferences",
        "description": "Gather client preferences across all 3 categories (A/B/C)",
        "mandatory": True,
    },
    {
        "step": 2,
        "name": "Screen product universe",
        "description": "Filter products meeting minimum preference thresholds",
        "mandatory": True,
    },
    {
        "step": 3,
        "name": "Assess financial suitability",
        "description": "Overlay traditional suitability (knowledge, experience, capacity for loss)",
        "mandatory": True,
    },
    {
        "step": 4,
        "name": "Preference adjustment",
        "description": "If no match: offer to adjust preferences with full disclosure and documentation",
        "mandatory": False,
    },
    {
        "step": 5,
        "name": "Documentation",
        "description": "Record preference collection and matching rationale in suitability report",
        "mandatory": True,
    },
]

MIFID_CROSS_FRAMEWORK: Dict[str, str] = {
    "sfdr_art_8_9": "SFDR sustainable investment % maps to Category B",
    "eu_taxonomy": "Taxonomy-aligned % maps to Category A",
    "pai_sfdr_rts": "PAI consideration maps to Category C",
    "csrd_esrs_e1": "CSRD climate disclosure informs taxonomy alignment evidence",
    "eba_esg_risk": "EBA ESG risk guidelines complement MiFID II product categorisation",
}

MIFID_TIMELINE: List[Dict[str, str]] = [
    {
        "date": "2021-07-02",
        "event": "Delegated Regulation 2021/1253 published in OJEU",
        "article": "All",
    },
    {
        "date": "2022-08-02",
        "event": "Application date — sustainability preferences integration into suitability process",
        "article": "Art 2(7) + Art 25(2)",
    },
    {
        "date": "2023-06-30",
        "event": "ESMA Q&A on MiFID II sustainability preferences published",
        "article": "Art 25(2)",
    },
    {
        "date": "2024-01-01",
        "event": "ESMA Guidelines on suitability assessment fully applicable",
        "article": "Art 25",
    },
    {
        "date": "2025-01-01",
        "event": "Review of Delegated Regulation scope under SFDR review alignment",
        "article": "Art 2(7)",
    },
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ClientPreferences:
    client_id: str
    name: str
    preference_category_a_min_pct: float = 0.0
    preference_category_b_min_pct: float = 0.0
    preference_category_c: bool = False
    investor_type: str = "retail"
    risk_profile: str = "balanced"


@dataclass
class ProductProfile:
    product_id: str
    product_name: str
    product_type: str
    taxonomy_alignment_pct: float
    sfdr_sustainable_investment_pct: float
    considers_pais: bool
    sfdr_article: str
    domicile: str = "IE"


@dataclass
class PreferenceMatchResult:
    product_id: str
    product_name: str
    matches_category_a: bool
    matches_category_b: bool
    matches_category_c: bool
    overall_match: bool
    match_score: float
    gap_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "matches_category_a": self.matches_category_a,
            "matches_category_b": self.matches_category_b,
            "matches_category_c": self.matches_category_c,
            "overall_match": self.overall_match,
            "match_score": round(self.match_score, 2),
            "gap_notes": self.gap_notes,
        }


@dataclass
class MiFIDSPTResult:
    assessment_id: str
    client_id: str
    client_name: str
    preferences: Dict[str, Any]
    matched_products: List[Dict[str, Any]]
    total_products_assessed: int
    matched_count: int
    match_rate_pct: float
    suitability_notes: List[str]
    adjustment_recommended: bool
    cross_framework: Dict[str, str]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "preferences": self.preferences,
            "matched_products": self.matched_products,
            "total_products_assessed": self.total_products_assessed,
            "matched_count": self.matched_count,
            "match_rate_pct": round(self.match_rate_pct, 2),
            "suitability_notes": self.suitability_notes,
            "adjustment_recommended": self.adjustment_recommended,
            "cross_framework": self.cross_framework,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class MiFIDSPTEngine:
    """MiFID II Sustainability Preferences Tool (SPT) assessment engine."""

    # Weights for match score computation
    _WEIGHT_A = 0.40
    _WEIGHT_B = 0.40
    _WEIGHT_C = 0.20

    def assess_client_preferences(
        self,
        client: ClientPreferences,
        products: List[ProductProfile],
    ) -> MiFIDSPTResult:
        """
        Run Art 25(2) suitability preference matching for a client against a
        product universe.  Returns a MiFIDSPTResult with per-product match detail
        and portfolio-level statistics.
        """
        logger.info(
            "MiFID SPT assess_client_preferences: client=%s products=%d",
            client.client_id,
            len(products),
        )

        matched_products: List[Dict[str, Any]] = []
        matched_count = 0

        requires_a = client.preference_category_a_min_pct > 0.0
        requires_b = client.preference_category_b_min_pct > 0.0
        requires_c = client.preference_category_c

        for product in products:
            gap_notes: List[str] = []

            # --- Category A: taxonomy alignment ---
            matches_a = product.taxonomy_alignment_pct >= client.preference_category_a_min_pct
            if not matches_a:
                gap_notes.append(
                    f"Category A gap: product taxonomy_alignment_pct "
                    f"({product.taxonomy_alignment_pct:.1f}%) < required "
                    f"({client.preference_category_a_min_pct:.1f}%)"
                )

            # --- Category B: SFDR sustainable investment % ---
            matches_b = (
                product.sfdr_sustainable_investment_pct
                >= client.preference_category_b_min_pct
            )
            if not matches_b:
                gap_notes.append(
                    f"Category B gap: product sfdr_sustainable_investment_pct "
                    f"({product.sfdr_sustainable_investment_pct:.1f}%) < required "
                    f"({client.preference_category_b_min_pct:.1f}%)"
                )

            # --- Category C: PAI consideration ---
            # Client preference_category_c=True means client requires PAI consideration.
            # Product satisfies C if it considers PAIs (or client doesn't require C).
            matches_c = (not client.preference_category_c) or product.considers_pais
            if client.preference_category_c and not product.considers_pais:
                gap_notes.append(
                    "Category C gap: client requires PAI consideration but product "
                    "does not consider principal adverse impacts"
                )

            # --- Weighted match score ---
            score_a = 100.0 if matches_a else max(
                0.0,
                (product.taxonomy_alignment_pct / max(client.preference_category_a_min_pct, 1e-9)) * 100.0,
            )
            score_b = 100.0 if matches_b else max(
                0.0,
                (product.sfdr_sustainable_investment_pct / max(client.preference_category_b_min_pct, 1e-9)) * 100.0,
            )
            score_c = 100.0 if matches_c else 0.0

            # Cap individual component scores at 100
            score_a = min(score_a, 100.0)
            score_b = min(score_b, 100.0)

            match_score = (
                self._WEIGHT_A * score_a
                + self._WEIGHT_B * score_b
                + self._WEIGHT_C * score_c
            )

            # Overall match: all *required* preferences must be satisfied
            required_checks: List[bool] = []
            if requires_a:
                required_checks.append(matches_a)
            if requires_b:
                required_checks.append(matches_b)
            if requires_c:
                required_checks.append(matches_c)
            # If client has no preferences at all, any product matches
            overall_match = all(required_checks) if required_checks else True

            if overall_match:
                matched_count += 1

            result = PreferenceMatchResult(
                product_id=product.product_id,
                product_name=product.product_name,
                matches_category_a=matches_a,
                matches_category_b=matches_b,
                matches_category_c=matches_c,
                overall_match=overall_match,
                match_score=match_score,
                gap_notes=gap_notes,
            )
            matched_products.append(result.to_dict())

        total = len(products)
        match_rate_pct = (matched_count / total * 100.0) if total > 0 else 0.0

        has_any_preference = requires_a or requires_b or requires_c
        adjustment_recommended = (matched_count == 0) and has_any_preference

        suitability_notes = self._build_suitability_notes(
            client, matched_count, total, adjustment_recommended
        )

        return MiFIDSPTResult(
            assessment_id=str(uuid.uuid4()),
            client_id=client.client_id,
            client_name=client.name,
            preferences={
                "category_a_min_pct": client.preference_category_a_min_pct,
                "category_b_min_pct": client.preference_category_b_min_pct,
                "category_c_required": client.preference_category_c,
                "investor_type": client.investor_type,
                "risk_profile": client.risk_profile,
            },
            matched_products=matched_products,
            total_products_assessed=total,
            matched_count=matched_count,
            match_rate_pct=match_rate_pct,
            suitability_notes=suitability_notes,
            adjustment_recommended=adjustment_recommended,
            cross_framework=MIFID_CROSS_FRAMEWORK,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Suitability report text
    # ------------------------------------------------------------------

    def generate_suitability_report_text(self, result: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate human-readable suitability report text blocks from a
        MiFIDSPTResult dict (as returned by MiFIDSPTResult.to_dict()).
        """
        client_name = result.get("client_name", "Client")
        client_id = result.get("client_id", "")
        prefs = result.get("preferences", {})
        matched_count = result.get("matched_count", 0)
        total = result.get("total_products_assessed", 0)
        match_rate = result.get("match_rate_pct", 0.0)
        adjustment_recommended = result.get("adjustment_recommended", False)

        cat_a = prefs.get("category_a_min_pct", 0.0)
        cat_b = prefs.get("category_b_min_pct", 0.0)
        cat_c = prefs.get("category_c_required", False)

        client_summary = (
            f"Client: {client_name} (ID: {client_id}). "
            f"Investor type: {prefs.get('investor_type', 'retail')}. "
            f"Risk profile: {prefs.get('risk_profile', 'balanced')}."
        )

        preference_summary = (
            f"Sustainability preferences collected per Art 2(7) MiFID II "
            f"(Delegated Regulation 2021/1253): "
            f"Category A (EU Taxonomy-aligned) minimum {cat_a:.1f}%; "
            f"Category B (SFDR sustainable investments) minimum {cat_b:.1f}%; "
            f"Category C (PAI consideration) {'required' if cat_c else 'not required'}."
        )

        match_summary = (
            f"Product screening completed across {total} product(s). "
            f"{matched_count} product(s) satisfy all stated sustainability preferences "
            f"(match rate: {match_rate:.1f}%). "
            f"Assessment performed in accordance with Art 25(2) MiFID II suitability process."
        )

        recommendation_text = (
            f"{matched_count} suitable product(s) identified for {client_name} "
            f"meeting all Category A, B, and C preference thresholds. "
            f"Financial suitability assessment (knowledge, experience, capacity for loss) "
            f"must be completed prior to recommendation."
        ) if matched_count > 0 else (
            f"No products in the assessed universe meet all sustainability preferences "
            f"stated by {client_name}. Refer to preference adjustment procedure."
        )

        output: Dict[str, str] = {
            "client_summary": client_summary,
            "preference_summary": preference_summary,
            "match_summary": match_summary,
            "recommendation_text": recommendation_text,
            "disclosure_statement": (
                "This suitability assessment has been conducted in accordance with "
                "Art 25(2) of MiFID II as amended by EC Delegated Regulation 2021/1253. "
                "Sustainability preferences were collected and matched prior to financial "
                "suitability assessment. All preference collection and matching rationale "
                "has been documented in accordance with Art 25(6) MiFID II record-keeping "
                "obligations."
            ),
        }

        if adjustment_recommended:
            output["adjustment_text"] = (
                f"No products in the current product universe meet {client_name}'s stated "
                f"sustainability preferences. In accordance with Art 25(2) MiFID II and ESMA "
                f"Q&A (2023-06-30), the client has been informed that their preferences cannot "
                f"currently be satisfied. The client is offered the opportunity to adjust their "
                f"stated preferences. Any adjustment must be documented with full disclosure of "
                f"the reasons, and cannot be initiated by the investment firm."
            )

        return output

    # ------------------------------------------------------------------
    # Reference data accessors
    # ------------------------------------------------------------------

    def get_preference_categories(self) -> Dict[str, Any]:
        return PREFERENCE_CATEGORIES

    def get_suitability_process(self) -> List[Dict[str, Any]]:
        return SUITABILITY_PROCESS_STEPS

    def get_cross_framework(self) -> Dict[str, str]:
        return MIFID_CROSS_FRAMEWORK

    def get_product_esg_types(self) -> Dict[str, Any]:
        return PRODUCT_ESG_TYPES

    def get_timeline(self) -> List[Dict[str, str]]:
        return MIFID_TIMELINE

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_suitability_notes(
        client: ClientPreferences,
        matched_count: int,
        total: int,
        adjustment_recommended: bool,
    ) -> List[str]:
        notes: List[str] = []
        notes.append(
            f"Suitability process completed per Art 25(2) MiFID II "
            f"(Delegated Reg 2021/1253) effective 2022-08-02."
        )
        if client.investor_type == "retail":
            notes.append(
                "Retail client: enhanced suitability disclosure obligations apply "
                "per Art 25(6) MiFID II (written suitability report required)."
            )
        if client.preference_category_c:
            notes.append(
                "Category C (PAI) preference active: only products with explicit "
                "PAI consideration statements per SFDR RTS Annex I qualify."
            )
        if client.preference_category_a_min_pct > 50.0:
            notes.append(
                f"Category A threshold ({client.preference_category_a_min_pct:.1f}%) "
                f"is above typical Art 9 product taxonomy-alignment levels. "
                f"Product universe may be severely constrained."
            )
        if adjustment_recommended:
            notes.append(
                "Preference adjustment procedure triggered: no matching products found. "
                "Client must be informed and adjustment documented per ESMA guidance."
            )
        notes.append(
            f"Products assessed: {total}. Matching products: {matched_count}."
        )
        return notes
