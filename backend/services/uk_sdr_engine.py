"""
UK Sustainability Disclosure Requirements (SDR) Engine (E11)
=============================================================

FCA PS 23/16 — UK SDR and investment labels regime.

Covers:
  - 4 sustainability labels: Sustainable Focus, Sustainable Improvers,
    Sustainable Impact, Mixed Goals (FCA SDR Policy Statement PS 23/16)
  - Anti-Greenwashing Rule (FCA AGR, effective 31 May 2024)
  - Naming and Marketing Requirements (Dec 2024)
  - Consumer-facing disclosure obligations (ongoing/periodic)
  - Product-level sustainability characteristics disclosure
  - ICIS (Independent Claims Integrity Score) proxy scoring
  - Cross-reference to SFDR, ISSB S1/S2, EU Taxonomy (Great Britain / onshored)
  - FCA Sustainability Reporting Standard (SRS) alignment map

E11 in the engine series (E10=Assurance → E11=UK SDR → E12=...).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

SDR_LABELS: Dict[str, Dict[str, Any]] = {
    "sustainable_focus": {
        "label_id": "sustainable_focus",
        "label_name": "Sustainable Focus",
        "description": (
            "Invests primarily in assets that are environmentally and/or socially sustainable. "
            "At least 70% of assets must qualify as sustainable (per product's own criteria). "
            "Must have robust, evidence-based standard. No 'on a pathway' assets qualify."
        ),
        "key_threshold": "70% qualifying sustainable assets",
        "asset_pathway_allowed": False,
        "min_qualifying_pct": 70.0,
        "icis_weight_multiplier": 1.0,
        "applicable_to": ["equity_fund", "bond_fund", "mixed_asset_fund", "etf"],
        "reference": "FCA PS 23/16 §3.14–3.22",
    },
    "sustainable_improvers": {
        "label_id": "sustainable_improvers",
        "label_name": "Sustainable Improvers",
        "description": (
            "Invests primarily in assets with potential to become more environmentally and/or "
            "socially sustainable over time. At least 70% must have credible, time-bound targets "
            "or commitments to improve. Includes 'on a pathway' companies."
        ),
        "key_threshold": "70% assets with credible improvement targets",
        "asset_pathway_allowed": True,
        "min_qualifying_pct": 70.0,
        "icis_weight_multiplier": 0.85,
        "applicable_to": ["equity_fund", "bond_fund", "mixed_asset_fund", "etf", "private_equity"],
        "reference": "FCA PS 23/16 §3.23–3.30",
    },
    "sustainable_impact": {
        "label_id": "sustainable_impact",
        "label_name": "Sustainable Impact",
        "description": (
            "Invests with the aim of achieving a predefined positive, measurable impact on "
            "environmental and/or social outcomes. Requires genuine additionality (not just "
            "ESG screening). Measurable impact KPIs mandatory."
        ),
        "key_threshold": "Measurable, additional positive impact",
        "asset_pathway_allowed": False,
        "min_qualifying_pct": 70.0,
        "icis_weight_multiplier": 1.15,
        "applicable_to": ["equity_fund", "bond_fund", "infrastructure_fund", "private_debt"],
        "reference": "FCA PS 23/16 §3.31–3.40",
    },
    "mixed_goals": {
        "label_id": "mixed_goals",
        "label_name": "Mixed Goals",
        "description": (
            "Combines multiple sustainability objectives: at least some assets qualify under "
            "Sustainable Focus and/or Sustainable Impact criteria, while others are "
            "Sustainable Improvers. Clear disclosure of proportions required."
        ),
        "key_threshold": "Mix of qualifying assets across Focus/Impact/Improvers criteria",
        "asset_pathway_allowed": True,
        "min_qualifying_pct": 70.0,
        "icis_weight_multiplier": 0.95,
        "applicable_to": ["equity_fund", "mixed_asset_fund", "multi-strategy_fund"],
        "reference": "FCA PS 23/16 §3.41–3.48",
    },
}

AGR_REQUIREMENTS: List[Dict[str, Any]] = [
    # Anti-Greenwashing Rule — FCA COBS 4.15 (effective 31 May 2024)
    {"req_id": "AGR-01", "title": "Claims are fair, clear and not misleading", "source": "COBS 4.2.1R", "blocking": True},
    {"req_id": "AGR-02", "title": "Sustainability claims are consistent with actual characteristics", "source": "FCA AGR §2.4", "blocking": True},
    {"req_id": "AGR-03", "title": "Claims are proportionate — no exaggeration", "source": "FCA AGR §2.5", "blocking": True},
    {"req_id": "AGR-04", "title": "Claims supported by robust evidence at time of publication", "source": "FCA AGR §2.6", "blocking": True},
    {"req_id": "AGR-05", "title": "Claims updated when underlying sustainability characteristics change", "source": "FCA AGR §2.7", "blocking": True},
    {"req_id": "AGR-06", "title": "Sustainability terms in product name meet label criteria (or clearly qualified)", "source": "FCA NMR §4", "blocking": True},
    {"req_id": "AGR-07", "title": "Pre-contractual consumer-facing disclosure produced", "source": "COBS 9B.3R", "blocking": False},
    {"req_id": "AGR-08", "title": "Ongoing product-level disclosure produced (annual/bi-annual)", "source": "COBS 9B.4R", "blocking": False},
    {"req_id": "AGR-09", "title": "Entity-level disclosure produced (annual)", "source": "COBS 9B.6R", "blocking": False},
    {"req_id": "AGR-10", "title": "Reference benchmark (if any) is sustainability-related", "source": "FCA PS 23/16 §5.12", "blocking": False},
]

SDR_NAMING_RULES: Dict[str, List[str]] = {
    "prohibited_without_label": [
        "sustainable", "sustainability", "ESG", "responsible", "green",
        "climate", "impact", "ethical", "net zero", "decarbonisation",
        "biodiversity", "social", "environmental",
    ],
    "allowed_with_label": [
        # Use of the label name itself is the primary permitted use
    ],
    "always_permitted": [
        "index",  # passive replication of non-sustainability index
    ],
}

SDR_CROSS_FRAMEWORK: Dict[str, Dict[str, str]] = {
    "sfdr_art8": {
        "uk_sdr_label": "sustainable_focus OR sustainable_improvers",
        "note": "Art 8 is not a 1:1 map; label depends on qualifying asset %; EU Article 8 funds may not qualify for UK SDR label",
    },
    "sfdr_art9": {
        "uk_sdr_label": "sustainable_impact",
        "note": "Art 9 aligns most closely with Sustainable Impact label; impact additionality test required",
    },
    "eu_taxonomy": {
        "uk_sdr_label": "sustainable_focus OR sustainable_impact",
        "note": "GB Taxonomy (onshored) can contribute to qualifying asset %; UK has own taxonomy under development (GTAG)",
    },
    "issb_s1_s2": {
        "uk_sdr_label": "entity_level_disclosure",
        "note": "UK SRS (based on ISSB) covers entity-level disclosures; product-level label uses separate SDR criteria",
    },
    "tcfd": {
        "uk_sdr_label": "entity_level_disclosure",
        "note": "TCFD requirements already mandatory for UK large entities; SDR entity-level disclosure builds on TCFD",
    },
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ProductInput:
    """Input for a UK SDR label eligibility assessment."""
    product_id: str
    product_name: str
    product_type: str = "equity_fund"       # equity_fund, bond_fund, mixed_asset_fund, etf, private_equity, etc.
    aum_gbp: float = 100_000_000.0
    domicile: str = "UK"                     # UK | IE | LU | etc.
    fca_authorised: bool = True
    distributor_type: str = "retail"         # retail | professional | institutional

    # Sustainability characteristics
    qualifying_sustainable_pct: float = 0.0  # % of assets meeting the label's threshold
    has_improvement_targets: bool = False     # relevant for Improvers
    has_measurable_impact_kpis: bool = False  # relevant for Impact
    impact_additionality: bool = False        # genuine additionality for Impact label
    uses_sustainability_terms_in_name: bool = False

    # Evidence quality
    sustainability_evidence_quality: str = "none"  # none | weak | adequate | strong
    methodology_published: bool = False
    third_party_verified: bool = False
    data_coverage_pct: float = 0.0           # % of portfolio with sustainability data

    # AGR / naming compliance flags
    claims_reviewed_by_legal: bool = False
    claims_updated_on_change: bool = False
    pre_contractual_disclosure_produced: bool = False
    ongoing_disclosure_produced: bool = False
    entity_disclosure_produced: bool = False

    # Cross-framework
    sfdr_classification: Optional[str] = None   # art_6 | art_8 | art_9
    eu_taxonomy_alignment_pct: Optional[float] = None


@dataclass
class LabelEligibilityResult:
    """Eligibility assessment for a single SDR label."""
    label_id: str
    label_name: str
    eligible: bool
    qualifying_pct: float
    threshold_pct: float
    gaps: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)


@dataclass
class AGRCheckResult:
    """Anti-Greenwashing Rule check result for one requirement."""
    req_id: str
    title: str
    source: str
    blocking: bool
    compliant: bool
    status: str  # "compliant" | "gap"


@dataclass
class NamingAssessmentResult:
    """Naming and Marketing Requirements assessment."""
    product_name: str
    contains_sustainability_terms: bool
    prohibited_terms_found: List[str]
    label_held: Optional[str]
    naming_compliant: bool
    required_actions: List[str]


@dataclass
class UKSDRResult:
    """Full UK SDR label eligibility + AGR + naming assessment result."""
    run_id: str
    product_id: str
    product_name: str
    product_type: str
    aum_gbp: float

    # Label eligibility
    recommended_label: Optional[str]
    label_eligibility: List[LabelEligibilityResult] = field(default_factory=list)

    # AGR
    agr_results: List[AGRCheckResult] = field(default_factory=list)
    agr_compliant: bool = False
    agr_blocking_gaps: int = 0

    # Naming
    naming_assessment: Optional[NamingAssessmentResult] = None

    # ICIS proxy score (0–100)
    icis_score: float = 0.0
    icis_tier: str = "not_assessed"   # exemplary (≥80) | robust (60-79) | developing (40-59) | inadequate (<40)

    # Cross-framework
    sfdr_comparison: Optional[Dict[str, str]] = None

    # Overall
    overall_status: str = "non_compliant"  # compliant | partial | non_compliant
    disclosure_obligations: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class UKSDREngine:
    """
    UK Sustainability Disclosure Requirements Engine.

    Usage:
        engine = UKSDREngine()
        result = engine.assess(product=ProductInput(...))
    """

    def assess(
        self,
        product: ProductInput,
        assessment_date: Optional[str] = None,
    ) -> UKSDRResult:
        import datetime
        run_id = str(uuid.uuid4())
        date_str = assessment_date or datetime.date.today().isoformat()

        # Label eligibility
        label_results = self._assess_labels(product)
        recommended = self._recommend_label(label_results)

        # AGR
        agr_results, agr_compliant, agr_blocking = self._assess_agr(product)

        # Naming
        naming = self._assess_naming(product, recommended)

        # ICIS proxy score
        icis_score, icis_tier = self._calculate_icis(product, recommended)

        # SFDR comparison
        sfdr_comp = SDR_CROSS_FRAMEWORK.get(f"sfdr_{product.sfdr_classification}") if product.sfdr_classification else None

        # Overall status
        if agr_compliant and recommended and not naming.required_actions:
            overall = "compliant"
        elif agr_blocking == 0 and recommended:
            overall = "partial"
        else:
            overall = "non_compliant"

        # Disclosure obligations
        disclosures = self._disclosure_obligations(product, recommended)

        # Priority actions
        actions = self._priority_actions(product, label_results, agr_results, naming, recommended)

        return UKSDRResult(
            run_id=run_id,
            product_id=product.product_id,
            product_name=product.product_name,
            product_type=product.product_type,
            aum_gbp=product.aum_gbp,
            recommended_label=recommended,
            label_eligibility=label_results,
            agr_results=agr_results,
            agr_compliant=agr_compliant,
            agr_blocking_gaps=agr_blocking,
            naming_assessment=naming,
            icis_score=icis_score,
            icis_tier=icis_tier,
            sfdr_comparison=sfdr_comp,
            overall_status=overall,
            disclosure_obligations=disclosures,
            priority_actions=actions,
            metadata={
                "assessment_date": date_str,
                "framework": "FCA PS 23/16 — UK SDR and Investment Labels",
                "agr_effective": "31 May 2024",
                "naming_effective": "2 December 2024",
                "label_effective": "31 July 2024 (optional from launch)",
                "engine": "E11",
                "aum_gbp": product.aum_gbp,
                "fca_authorised": product.fca_authorised,
                "distributor_type": product.distributor_type,
            },
        )

    # ------------------------------------------------------------------
    # Label assessment
    # ------------------------------------------------------------------

    def _assess_labels(self, product: ProductInput) -> List[LabelEligibilityResult]:
        results: List[LabelEligibilityResult] = []

        for lbl_id, lbl in SDR_LABELS.items():
            gaps: List[str] = []
            conditions: List[str] = []

            # Check product type eligibility
            if product.product_type not in lbl["applicable_to"]:
                gaps.append(f"Product type '{product.product_type}' not eligible for this label")

            # Check qualifying %
            threshold = lbl["min_qualifying_pct"]
            if product.qualifying_sustainable_pct < threshold:
                gaps.append(
                    f"Qualifying sustainable assets {product.qualifying_sustainable_pct:.1f}% "
                    f"< {threshold:.0f}% threshold"
                )

            # Label-specific checks
            if lbl_id == "sustainable_improvers":
                if not product.has_improvement_targets:
                    gaps.append("Assets must have credible, time-bound improvement targets")
            elif lbl_id == "sustainable_impact":
                if not product.has_measurable_impact_kpis:
                    gaps.append("Measurable impact KPIs with ongoing reporting required")
                if not product.impact_additionality:
                    gaps.append("Genuine additionality must be demonstrated (not purely secondary market)")
            elif lbl_id == "mixed_goals":
                if product.qualifying_sustainable_pct < 70:
                    gaps.append("Combined qualifying assets must be ≥70%")

            # Evidence quality check
            if product.sustainability_evidence_quality in ("none", "weak"):
                gaps.append("Robust, evidence-based sustainability assessment methodology required")
            elif product.sustainability_evidence_quality == "adequate":
                conditions.append("Evidence quality is adequate; consider strengthening to 'strong' for resilience")

            # FCA authorisation
            if not product.fca_authorised and product.domicile == "UK":
                gaps.append("Product must be FCA-authorised to use UK SDR labels")

            eligible = len(gaps) == 0
            results.append(LabelEligibilityResult(
                label_id=lbl_id,
                label_name=lbl["label_name"],
                eligible=eligible,
                qualifying_pct=product.qualifying_sustainable_pct,
                threshold_pct=threshold,
                gaps=gaps,
                conditions=conditions,
            ))

        return results

    def _recommend_label(self, label_results: List[LabelEligibilityResult]) -> Optional[str]:
        """Return the most appropriate eligible label (Impact > Focus > Improvers > Mixed)."""
        priority = ["sustainable_impact", "sustainable_focus", "sustainable_improvers", "mixed_goals"]
        for lbl_id in priority:
            match = next((r for r in label_results if r.label_id == lbl_id and r.eligible), None)
            if match:
                return lbl_id
        return None

    # ------------------------------------------------------------------
    # AGR assessment
    # ------------------------------------------------------------------

    def _assess_agr(
        self,
        product: ProductInput,
    ) -> tuple[List[AGRCheckResult], bool, int]:
        flag_map = {
            "AGR-01": product.sustainability_evidence_quality in ("adequate", "strong"),
            "AGR-02": product.data_coverage_pct >= 70 and product.sustainability_evidence_quality in ("adequate", "strong"),
            "AGR-03": not product.uses_sustainability_terms_in_name or product.qualifying_sustainable_pct >= 70,
            "AGR-04": product.methodology_published,
            "AGR-05": product.claims_updated_on_change,
            "AGR-06": product.claims_reviewed_by_legal,
            "AGR-07": product.pre_contractual_disclosure_produced,
            "AGR-08": product.ongoing_disclosure_produced,
            "AGR-09": product.entity_disclosure_produced,
            "AGR-10": True,   # Benchmark requirement — pass by default unless benchmark specified
        }
        results: List[AGRCheckResult] = []
        blocking_gaps = 0
        for req in AGR_REQUIREMENTS:
            compliant = flag_map.get(req["req_id"], False)
            if not compliant and req["blocking"]:
                blocking_gaps += 1
            results.append(AGRCheckResult(
                req_id=req["req_id"],
                title=req["title"],
                source=req["source"],
                blocking=req["blocking"],
                compliant=compliant,
                status="compliant" if compliant else "gap",
            ))
        all_compliant = blocking_gaps == 0 and all(r.compliant for r in results if r.blocking)
        return results, all_compliant, blocking_gaps

    # ------------------------------------------------------------------
    # Naming assessment
    # ------------------------------------------------------------------

    def _assess_naming(
        self,
        product: ProductInput,
        recommended_label: Optional[str],
    ) -> NamingAssessmentResult:
        name_lower = product.product_name.lower()
        prohibited_found = [
            term for term in SDR_NAMING_RULES["prohibited_without_label"]
            if term.lower() in name_lower
        ]
        naming_compliant = True
        required_actions: List[str] = []

        if prohibited_found and not recommended_label:
            naming_compliant = False
            required_actions.append(
                f"Product name contains sustainability-related terms "
                f"({', '.join(prohibited_found)}) but does not hold a qualifying SDR label. "
                "Either obtain a label or rename the product."
            )
        elif prohibited_found and recommended_label:
            # Has label — permitted but must disclose label in all marketing
            required_actions.append(
                f"Product uses sustainability terms in name — ensure SDR label is prominently "
                "displayed in all consumer-facing materials (FCA NMR §4.9)."
            )

        return NamingAssessmentResult(
            product_name=product.product_name,
            contains_sustainability_terms=len(prohibited_found) > 0,
            prohibited_terms_found=prohibited_found,
            label_held=recommended_label,
            naming_compliant=naming_compliant,
            required_actions=required_actions,
        )

    # ------------------------------------------------------------------
    # ICIS proxy score
    # ------------------------------------------------------------------

    def _calculate_icis(
        self,
        product: ProductInput,
        recommended_label: Optional[str],
    ) -> tuple[float, str]:
        """
        Proxy for the Independent Claims Integrity Score (ICIS).
        Not an FCA-defined metric — internal scoring proxy based on:
          - Evidence quality (30 pts)
          - Data coverage (25 pts)
          - Third-party verification (20 pts)
          - Methodology publication (15 pts)
          - Claims review / update process (10 pts)
        """
        score = 0.0
        ev_map = {"none": 0, "weak": 10, "adequate": 22, "strong": 30}
        score += ev_map.get(product.sustainability_evidence_quality, 0)
        score += min(product.data_coverage_pct / 100 * 25, 25)
        if product.third_party_verified:
            score += 20
        if product.methodology_published:
            score += 15
        if product.claims_reviewed_by_legal:
            score += 5
        if product.claims_updated_on_change:
            score += 5

        # Label multiplier
        if recommended_label:
            multiplier = SDR_LABELS[recommended_label].get("icis_weight_multiplier", 1.0)
            score = min(score * multiplier, 100)

        score = round(score, 1)
        if score >= 80:
            tier = "exemplary"
        elif score >= 60:
            tier = "robust"
        elif score >= 40:
            tier = "developing"
        else:
            tier = "inadequate"
        return score, tier

    # ------------------------------------------------------------------
    # Disclosure obligations
    # ------------------------------------------------------------------

    def _disclosure_obligations(
        self,
        product: ProductInput,
        label: Optional[str],
    ) -> List[str]:
        obls: List[str] = []
        if product.fca_authorised:
            obls.append("Entity-level sustainability disclosure (annual) — COBS 9B.6R")
            if product.distributor_type in ("retail", "institutional"):
                obls.append("Pre-contractual consumer-facing disclosure — COBS 9B.3R")
                obls.append("Ongoing product-level disclosure (bi-annual for retail) — COBS 9B.4R")
            if label:
                obls.append(f"SDR label '{SDR_LABELS[label]['label_name']}' must appear on all consumer-facing materials")
                obls.append("Key investor document / fund factsheet must reference label and methodology")
        return obls

    # ------------------------------------------------------------------
    # Priority actions
    # ------------------------------------------------------------------

    def _priority_actions(
        self,
        product: ProductInput,
        label_results: List[LabelEligibilityResult],
        agr_results: List[AGRCheckResult],
        naming: NamingAssessmentResult,
        label: Optional[str],
    ) -> List[str]:
        actions: List[str] = []

        if label is None:
            actions.append(
                "No SDR label currently qualifies — increase qualifying sustainable assets "
                f"to ≥70% to be eligible for Sustainable Focus or Sustainable Improvers"
            )
        if product.sustainability_evidence_quality in ("none", "weak"):
            actions.append("Develop and publish a robust, evidence-based sustainability assessment methodology")
        agr_gaps = [r for r in agr_results if not r.compliant and r.blocking]
        if agr_gaps:
            actions.append(
                f"Resolve {len(agr_gaps)} blocking AGR requirements: "
                + "; ".join(r.req_id for r in agr_gaps)
            )
        if naming.required_actions:
            actions.extend(naming.required_actions)
        if not product.pre_contractual_disclosure_produced:
            actions.append("Produce pre-contractual consumer-facing disclosure (COBS 9B.3R) — mandatory for retail")
        if not product.third_party_verified:
            actions.append("Commission third-party verification of sustainability claims (strengthens AGR defence)")
        if product.data_coverage_pct < 70:
            actions.append(
                f"Improve sustainability data coverage from {product.data_coverage_pct:.0f}% to ≥70% "
                "to support robust claims"
            )
        return actions
