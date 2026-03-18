"""
Greenwashing Risk & Substantiation Engine.
Regulatory basis:
  - EU Anti-Greenwashing / Green Claims Directive (COM/2023/166)
  - FCA Consumer Duty PS22/9 (effective Jul 2023) + SDR Anti-Greenwashing Rule (31 May 2024)
  - ESMA Supervisory Briefing on Greenwashing (May 2023)
  - UK Sustainability Disclosure Requirements (SDR) FCA PS23/16
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

MISLEADING_TERMS: list[dict[str, Any]] = [
    {"term": "eco-friendly", "risk_level": "high", "substantiation": "LCA required; comparative baseline needed"},
    {"term": "green", "risk_level": "high", "substantiation": "Specific environmental benefit must be proven with data"},
    {"term": "sustainable", "risk_level": "high", "substantiation": "Three pillars (E/S/G) evidence required; no vague usage"},
    {"term": "carbon neutral", "risk_level": "very_high", "substantiation": "ISO 14064-1 GHG inventory + third-party verification; offsets must meet CCP/Gold Standard"},
    {"term": "net zero", "risk_level": "very_high", "substantiation": "SBTi Net-Zero Standard or equivalent; full value chain coverage; residual offset quality"},
    {"term": "climate positive", "risk_level": "very_high", "substantiation": "Requires demonstrably negative lifecycle GHG balance with verified data"},
    {"term": "nature positive", "risk_level": "very_high", "substantiation": "TNFD/SBTN target alignment; biodiversity impact measurement required"},
    {"term": "biodiversity friendly", "risk_level": "high", "substantiation": "ENCORE dependency mapping; species/habitat impact assessment"},
    {"term": "zero emissions", "risk_level": "very_high", "substantiation": "Operational Scope 1 & 2 data required; Scope 3 coverage must be stated"},
    {"term": "100% renewable", "risk_level": "medium", "substantiation": "Additionality evidence or I-REC/REGO certificates required; bundled vs unbundled"},
    {"term": "responsibly sourced", "risk_level": "medium", "substantiation": "Supply chain audit; recognised certification (FSC, RSPO, Rainforest Alliance)"},
    {"term": "ethical", "risk_level": "medium", "substantiation": "Code of conduct; independent social audit; ILO standard alignment"},
    {"term": "circular", "risk_level": "medium", "substantiation": "Material flow accounting; recycled/recyclable content % disclosed"},
    {"term": "plastic free", "risk_level": "medium", "substantiation": "Full product/packaging composition; bioplastic disclosure required"},
    {"term": "low carbon", "risk_level": "high", "substantiation": "Sector benchmark carbon intensity comparison required"},
    {"term": "carbon offset", "risk_level": "high", "substantiation": "Offset type, registry, vintage, additionality, permanence must be disclosed"},
    {"term": "paris aligned", "risk_level": "high", "substantiation": "Temperature pathway (SBTi/GFANZ) with sector decarbonisation trajectory"},
    {"term": "ESG leader", "risk_level": "high", "substantiation": "Peer group definition and methodology of rating/ranking must be disclosed"},
    {"term": "best-in-class ESG", "risk_level": "high", "substantiation": "Criteria, universe, methodology, and rebalancing frequency required"},
    {"term": "impact investing", "risk_level": "high", "substantiation": "Additionality, intentionality, measurability per IRIS+/IFC PS required"},
    {"term": "green bond", "risk_level": "medium", "substantiation": "ICMA GBP or EU GBS alignment; use of proceeds ring-fencing; external review"},
    {"term": "sustainable bond", "risk_level": "medium", "substantiation": "ICMA SBP framework; KPI disclosure; verification report"},
    {"term": "Article 9 fund", "risk_level": "very_high", "substantiation": "SFDR Art 9 — sustainable investment objective; principal adverse impacts; product disclosure required"},
    {"term": "Article 8 fund", "risk_level": "high", "substantiation": "SFDR Art 8 — E/S characteristics; PAI consideration; SFDR AIFMD/UCITS disclosures"},
    {"term": "EU Taxonomy aligned", "risk_level": "very_high", "substantiation": "EU Taxonomy Reg 2020/852 — Do No Significant Harm; Minimum Social Safeguards; technical screening criteria"},
    {"term": "decarbonising", "risk_level": "high", "substantiation": "Historical GHG trend + forward trajectory with interim milestones required"},
    {"term": "clean energy", "risk_level": "medium", "substantiation": "Lifecycle emissions per kWh; nuclear/gas labelling per EU Taxonomy must be clear"},
    {"term": "environmentally responsible", "risk_level": "high", "substantiation": "ISO 14001 or EMAS; quantitative environmental KPIs"},
    {"term": "planet friendly", "risk_level": "very_high", "substantiation": "Lifecycle assessment across planetary boundaries required"},
    {"term": "deforestation free", "risk_level": "high", "substantiation": "EUDR Regulation (EU) 2023/1115 due diligence; geolocation evidence"},
    {"term": "water neutral", "risk_level": "very_high", "substantiation": "Water accounting per AWS/CDP Water; replenishment evidence"},
    {"term": "scope 3 neutral", "risk_level": "very_high", "substantiation": "Full GHG Protocol Scope 3 inventory across all 15 categories; verified offsets"},
    {"term": "regenerative", "risk_level": "high", "substantiation": "Soil carbon sequestration data; biodiversity net gain measurement"},
    {"term": "clean tech", "risk_level": "medium", "substantiation": "Taxonomy eligible revenue % vs activity description required"},
    {"term": "responsible investment", "risk_level": "high", "substantiation": "UN PRI alignment; stewardship policy; engagement outcomes"},
    {"term": "SDG aligned", "risk_level": "medium", "substantiation": "Specific SDG target mapping with quantitative contribution metrics"},
    {"term": "TCFD aligned", "risk_level": "medium", "substantiation": "All 4 TCFD pillars (Governance/Strategy/Risk Mgmt/Metrics) disclosed; scenario analysis"},
    {"term": "science based targets", "risk_level": "high", "substantiation": "SBTi validation letter; approved target must be current and not lapsed"},
    {"term": "just transition", "risk_level": "medium", "substantiation": "Workers/community impact plan; retraining expenditure; union engagement records"},
    {"term": "beyond compliance", "risk_level": "medium", "substantiation": "Specific regulatory baseline; quantified performance above that baseline"},
]

CLAIM_TYPES: dict[str, dict[str, Any]] = {
    "quantitative": {
        "description": "Claims backed by numerical data (e.g. '30% emissions reduction')",
        "requirements": ["data_source", "methodology", "boundary", "baseline_year", "third_party_verification"],
        "min_substantiation_score": 0.75,
    },
    "qualitative": {
        "description": "Descriptive environmental claims without specific numbers",
        "requirements": ["evidence_basis", "scope_limitation_stated", "verification_or_audit"],
        "min_substantiation_score": 0.60,
    },
    "label": {
        "description": "Use of a certification label or mark",
        "requirements": ["certification_body", "scope_of_certification", "certificate_validity", "permitted_usage_rights"],
        "min_substantiation_score": 0.85,
    },
    "comparative": {
        "description": "Claims comparing to competitors, prior periods or industry averages",
        "requirements": ["baseline_defined", "comparison_methodology", "comparable_scope", "date_of_comparison"],
        "min_substantiation_score": 0.80,
    },
    "forward_looking": {
        "description": "Claims about future environmental performance or targets",
        "requirements": ["target_date", "interim_milestones", "governance_oversight", "probability_qualified"],
        "min_substantiation_score": 0.65,
    },
}

EU_REG_REQUIREMENTS: list[dict[str, Any]] = [
    {
        "id": "EU-GCD-1",
        "article": "COM/2023/166 Art 5",
        "requirement": "Pre-contractual substantiation",
        "description": "All green claims must be substantiated before being made public; documentation ready on request.",
    },
    {
        "id": "EU-GCD-2",
        "article": "COM/2023/166 Art 5(1)(a)",
        "requirement": "Lifecycle assessment coverage",
        "description": "Environmental claims must cover significant lifecycle impacts; cherry-picking lifecycle stages is prohibited.",
    },
    {
        "id": "EU-GCD-3",
        "article": "COM/2023/166 Art 5(1)(c)",
        "requirement": "Comparative claims baseline",
        "description": "Comparative claims must use equivalent methodology and timeframe to competitor/benchmark.",
    },
    {
        "id": "EU-GCD-4",
        "article": "COM/2023/166 Art 5(1)(e)",
        "requirement": "Forward-looking claims probability",
        "description": "Future claims must reflect genuine probability; aspirational statements without plans are prohibited.",
    },
    {
        "id": "EU-GCD-5",
        "article": "COM/2023/166 Art 10",
        "requirement": "Third-party verification",
        "description": "Explicit claims must be independently verified by accredited body before publication.",
    },
    {
        "id": "EU-GCD-6",
        "article": "COM/2023/166 Art 8",
        "requirement": "Label usage rules",
        "description": "Only EU-approved sustainability labels or nationally recognised schemes may be used for labelling.",
    },
    {
        "id": "EU-GCD-7",
        "article": "COM/2023/166 Art 6",
        "requirement": "Material omission test",
        "description": "Omitting significant negative environmental impacts that would alter consumer understanding is prohibited.",
    },
    {
        "id": "EU-GCD-8",
        "article": "COM/2023/166 Art 5(1)(g)",
        "requirement": "Prominence of limitations",
        "description": "Scope limitations (e.g. 'only manufacturing phase') must be displayed with equal prominence to the claim.",
    },
]

FCA_REQUIREMENTS: list[dict[str, Any]] = [
    {
        "id": "FCA-AGR-1",
        "source": "FCA SDR PS23/16 — Anti-Greenwashing Rule (31 May 2024)",
        "requirement": "Clear, fair and not misleading",
        "description": "Sustainability-related claims must be clear, fair, not misleading and consistent with the product's actual sustainability characteristics.",
    },
    {
        "id": "FCA-AGR-2",
        "source": "FCA PS23/16 §§ 3.21-3.28",
        "requirement": "Sustainability characteristics match portfolio",
        "description": "Claimed sustainability features must be present in the portfolio to a material extent; headline claims must reflect the full portfolio.",
    },
    {
        "id": "FCA-AGR-3",
        "source": "FCA PS22/9 Consumer Duty",
        "requirement": "Prominence of limitations",
        "description": "Any limitations on sustainability features (exclusions, best-efforts only) must be clearly disclosed and appropriately prominent.",
    },
    {
        "id": "FCA-AGR-4",
        "source": "FCA PS23/16 § 4.15",
        "requirement": "Comparative claim substantiation",
        "description": "Comparative claims (e.g. 'greener than peers') must define the comparison group and methodology explicitly.",
    },
    {
        "id": "FCA-AGR-5",
        "source": "FCA PS23/16 — Ongoing Monitoring",
        "requirement": "Ongoing monitoring of claims",
        "description": "Firms must have processes to monitor that claims remain accurate over time as portfolios and methodologies evolve.",
    },
    {
        "id": "FCA-AGR-6",
        "source": "FCA PS23/16 — Governance",
        "requirement": "Claims governance",
        "description": "Board or senior management must approve and periodically review sustainability claims; documented governance trail required.",
    },
]

LABEL_VERIFICATION_RULES: dict[str, Any] = {
    "sfdr_article_8": {
        "label": "SFDR Article 8",
        "description": "Fund promotes environmental or social characteristics",
        "checks": [
            "At least one binding E/S characteristic disclosed in pre-contractual document",
            "PAI consideration statement included (Art 7 SFDR)",
            "No sustainable investment objective claimed (else must be Art 9)",
            "Taxonomy alignment % disclosed if claimed",
        ],
        "taxonomy_alignment_required": False,
    },
    "sfdr_article_9": {
        "label": "SFDR Article 9",
        "description": "Fund has sustainable investment as its objective",
        "checks": [
            "Sustainable investment definition adopted (Art 2(17) SFDR)",
            "DNSH assessment methodology documented",
            "Minimum Social Safeguards (OECD MNE, UNGP) confirmed",
            "PAI mandatory consideration on all investments",
            "Taxonomy aligned % or best-efforts statement",
        ],
        "taxonomy_alignment_required": True,
    },
    "sdr_focus": {
        "label": "UK SDR — Sustainability Focus",
        "description": "At least 70% of assets meet sustainability standard",
        "checks": [
            ">=70% portfolio meets defined robust, evidence-based standard",
            "Standard must be independently verified or externally recognised",
            "Ongoing stewardship policy for non-qualifying assets",
        ],
        "taxonomy_alignment_required": False,
    },
    "sdr_improvers": {
        "label": "UK SDR — Sustainability Improvers",
        "description": "Assets selected for sustainability improvement potential",
        "checks": [
            "Credible improvement pathway defined for each asset",
            "Time-bound milestones with stewardship plan",
            "At least some evidence of improvement tracked",
        ],
        "taxonomy_alignment_required": False,
    },
    "sdr_impact": {
        "label": "UK SDR — Sustainability Impact",
        "description": "Funds aiming to achieve positive sustainability outcomes",
        "checks": [
            "Theory of change documented",
            "Additionality demonstrated",
            "Impact measured against defined KPIs",
            "Annual impact report published",
        ],
        "taxonomy_alignment_required": False,
    },
    "sdr_mixed_goals": {
        "label": "UK SDR — Mixed Goals",
        "description": "Combination of focus/improvers/impact approaches",
        "checks": [
            "Each allocation portion clearly labelled with applicable sub-label",
            "Proportions disclosed in fund documentation",
        ],
        "taxonomy_alignment_required": False,
    },
    "eu_taxonomy_aligned": {
        "label": "EU Taxonomy Aligned",
        "description": "Investment activity meets EU Taxonomy Technical Screening Criteria",
        "checks": [
            "Substantial contribution to >=1 of 6 environmental objectives",
            "DNSH to remaining 5 objectives verified",
            "Minimum Social Safeguards (OECD MNE, UNGP, ILO) confirmed",
            "Taxonomy-eligible vs taxonomy-aligned distinction made clear",
            "Taxonomy disclosure (Art 8 NFRD/CSRD or SFDR) published",
        ],
        "taxonomy_alignment_required": True,
    },
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class GreenwashingAssessment:
    entity_id: str
    entity_name: str
    overall_risk_level: str
    overall_risk_score: float
    claims_assessed: list[dict]
    label_assessment: dict
    eu_compliance_score: float
    fca_compliance_score: float
    eu_gaps: list[str]
    fca_gaps: list[str]
    high_risk_claims: list[str]
    remediation_actions: list[str]
    regulatory_refs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GreenwashingEngine:
    """Greenwashing Risk & Substantiation Engine."""

    _instance: "GreenwashingEngine | None" = None

    def __init__(self) -> None:
        self._rng_base = 42

    @classmethod
    def get_instance(cls) -> "GreenwashingEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Claim screening
    # ------------------------------------------------------------------

    def screen_claim(self, claim_text: str, claim_type: str) -> dict[str, Any]:
        claim_lower = claim_text.lower()
        matched_terms: list[dict] = []
        for entry in MISLEADING_TERMS:
            if entry["term"].lower() in claim_lower:
                matched_terms.append(entry)

        issues: list[str] = []
        risk_levels = {"low": 1, "medium": 2, "high": 3, "very_high": 4}
        max_risk = "low"
        for mt in matched_terms:
            lvl = mt["risk_level"]
            if risk_levels.get(lvl, 0) > risk_levels.get(max_risk, 0):
                max_risk = lvl
            issues.append(f"Term '{mt['term']}' — {mt['substantiation']}")

        claim_cfg = CLAIM_TYPES.get(claim_type, CLAIM_TYPES["qualitative"])
        missing_reqs = claim_cfg["requirements"]

        substantiation_score = max(0.0, 1.0 - (len(issues) * 0.12) - (len(missing_reqs) * 0.08))
        substantiation_score = round(substantiation_score, 2)

        regulatory_refs = [r["id"] for r in EU_REG_REQUIREMENTS[:3]]
        if max_risk in ("high", "very_high"):
            regulatory_refs += [r["id"] for r in FCA_REQUIREMENTS[:2]]

        return {
            "claim_text": claim_text,
            "claim_type": claim_type,
            "risk_level": max_risk,
            "matched_problematic_terms": [m["term"] for m in matched_terms],
            "issues": issues,
            "required_substantiation": claim_cfg["requirements"],
            "min_substantiation_score_required": claim_cfg["min_substantiation_score"],
            "current_substantiation_score": substantiation_score,
            "passes_threshold": substantiation_score >= claim_cfg["min_substantiation_score"],
            "regulatory_refs": regulatory_refs,
        }

    # ------------------------------------------------------------------
    # Label verification
    # ------------------------------------------------------------------

    def verify_labels(
        self,
        entity_id: str,
        labels: list[str],
        sfdr_art: str,
        taxonomy_pct: float,
    ) -> dict[str, Any]:
        results: list[dict] = []
        overall_pass = True

        for label in labels:
            label_key = label.lower().replace("-", "_").replace(" ", "_")
            rule = LABEL_VERIFICATION_RULES.get(label_key)
            if rule is None:
                results.append({
                    "label": label,
                    "status": "UNRECOGNISED",
                    "issues": ["Label not found in verification ruleset — may constitute greenwashing if unsubstantiated"],
                    "checks_passed": [],
                    "checks_failed": ["Label recognition"],
                })
                overall_pass = False
                continue

            passed: list[str] = []
            failed: list[str] = []

            if rule.get("taxonomy_alignment_required") and taxonomy_pct < 10:
                failed.append(f"EU Taxonomy alignment: claimed {taxonomy_pct}% but label requires material alignment")
            else:
                passed.append("Taxonomy alignment threshold")

            if label_key == "sfdr_article_9" and sfdr_art not in ("9", "Article 9"):
                failed.append(f"SFDR classification mismatch: entity classified as Art {sfdr_art}, not Art 9")
            elif label_key == "sfdr_article_8" and sfdr_art not in ("8", "Article 8"):
                failed.append(f"SFDR classification mismatch: entity classified as Art {sfdr_art}, not Art 8")
            else:
                passed.append("SFDR classification consistency")

            status = "PASS" if not failed else "FAIL"
            if failed:
                overall_pass = False

            results.append({
                "label": label,
                "status": status,
                "description": rule["description"],
                "checks_passed": passed,
                "checks_failed": failed,
                "required_checks": rule["checks"],
            })

        return {
            "entity_id": entity_id,
            "labels_assessed": labels,
            "sfdr_classification": sfdr_art,
            "taxonomy_alignment_pct": taxonomy_pct,
            "label_results": results,
            "overall_label_compliance": "PASS" if overall_pass else "FAIL",
        }

    # ------------------------------------------------------------------
    # Full assessment
    # ------------------------------------------------------------------

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        claims: list[dict],
        product_labels: list[str],
        sfdr_classification: str,
        taxonomy_alignment_pct: float,
    ) -> GreenwashingAssessment:
        rng = random.Random(hash(entity_id) & 0xFFFFFFFF)

        claims_assessed: list[dict] = []
        high_risk_claims: list[str] = []
        total_claim_risk = 0.0

        for c in claims:
            screened = self.screen_claim(c.get("text", ""), c.get("type", "qualitative"))
            claims_assessed.append(screened)
            risk_map = {"low": 0.1, "medium": 0.3, "high": 0.65, "very_high": 0.9}
            total_claim_risk += risk_map.get(screened["risk_level"], 0.3)
            if screened["risk_level"] in ("high", "very_high"):
                high_risk_claims.append(c.get("text", "")[:80])

        avg_claim_risk = total_claim_risk / len(claims) if claims else rng.uniform(0.1, 0.4)
        label_result = self.verify_labels(entity_id, product_labels, sfdr_classification, taxonomy_alignment_pct)

        # EU compliance scoring
        eu_gaps: list[str] = []
        if avg_claim_risk > 0.6:
            eu_gaps.append("EU-GCD-1: High-risk claims lack pre-contractual substantiation documentation")
        if taxonomy_alignment_pct > 0 and taxonomy_alignment_pct < 5:
            eu_gaps.append("EU-GCD-2: Taxonomy alignment claim with <5% alignment — lifecycle coverage insufficient")
        if label_result["overall_label_compliance"] == "FAIL":
            eu_gaps.append("EU-GCD-6: Label usage does not comply with recognised scheme requirements")
        eu_compliance_score = round(max(0.0, 100.0 - len(eu_gaps) * 18 - avg_claim_risk * 20), 1)

        # FCA compliance scoring
        fca_gaps: list[str] = []
        if high_risk_claims:
            fca_gaps.append("FCA-AGR-1: High-risk sustainability claims present — clarity/fairness standards may not be met")
        if sfdr_classification in ("9", "Article 9") and taxonomy_alignment_pct < 20:
            fca_gaps.append("FCA-AGR-2: Art 9 claim but <20% taxonomy alignment — characteristics mismatch risk")
        fca_compliance_score = round(max(0.0, 100.0 - len(fca_gaps) * 20 - avg_claim_risk * 15), 1)

        overall_score = round((avg_claim_risk * 0.5 + (1 - eu_compliance_score / 100) * 0.3 + (1 - fca_compliance_score / 100) * 0.2), 2)
        if overall_score > 0.7:
            overall_risk = "very_high"
        elif overall_score > 0.5:
            overall_risk = "high"
        elif overall_score > 0.3:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        remediation: list[str] = []
        if eu_gaps:
            remediation.append("Obtain independent third-party verification for all material sustainability claims (EU-GCD-5)")
        if fca_gaps:
            remediation.append("Conduct FCA Anti-Greenwashing Rule review of all consumer-facing materials prior to publication")
        if high_risk_claims:
            remediation.append("Replace vague sustainability terms with specific, quantified, scope-limited claims")
        if label_result["overall_label_compliance"] == "FAIL":
            remediation.append("Review and correct sustainability label usage against applicable certification/regulatory rules")

        return GreenwashingAssessment(
            entity_id=entity_id,
            entity_name=entity_name,
            overall_risk_level=overall_risk,
            overall_risk_score=overall_score,
            claims_assessed=claims_assessed,
            label_assessment=label_result,
            eu_compliance_score=eu_compliance_score,
            fca_compliance_score=fca_compliance_score,
            eu_gaps=eu_gaps,
            fca_gaps=fca_gaps,
            high_risk_claims=high_risk_claims,
            remediation_actions=remediation,
            regulatory_refs=[r["id"] for r in EU_REG_REQUIREMENTS] + [r["id"] for r in FCA_REQUIREMENTS],
        )

    # ------------------------------------------------------------------
    # Reference getters
    # ------------------------------------------------------------------

    def ref_misleading_terms(self) -> list[dict]:
        return MISLEADING_TERMS

    def ref_claim_types(self) -> dict:
        return CLAIM_TYPES

    def ref_eu_requirements(self) -> list[dict]:
        return EU_REG_REQUIREMENTS

    def ref_fca_requirements(self) -> list[dict]:
        return FCA_REQUIREMENTS

    def ref_label_rules(self) -> dict:
        return LABEL_VERIFICATION_RULES


def get_engine() -> GreenwashingEngine:
    return GreenwashingEngine.get_instance()
