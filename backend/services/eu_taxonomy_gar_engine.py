"""
EU Taxonomy Green Finance KPI Reporter (E19)
============================================

Article 8 Delegated Act (Commission Delegated Regulation 2021/4987
amending 2021/2178). Covers GAR (Green Asset Ratio) for credit
institutions, BTAR (Banking Book Taxonomy Alignment Ratio), BSAR
(Off-Balance Sheet), and automated DNSH / Minimum Safeguards checks
per Taxonomy Regulation 2020/852.

Covers:
  - 11 asset classes with GAR/BTAR eligibility flags
  - 6 DNSH objectives automated assessment
  - 5 Minimum Safeguards checks (UNGC, OECD MNE, UNGP, ILO, UDHR)
  - GAR numerator/denominator calculation per Art 8 Delegated Act Annex V
  - BTAR for banking book asset classes
  - BSAR placeholder (off-balance-sheet)
  - Phase 1 (eligibility 2022-23) vs Phase 2 (alignment 2024+)
  - Cross-framework: CSRD ESRS E1, EU GBS, SFDR PAI 14, MiFID II, CBI

E19 in the engine series.
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

GAR_ASSET_CLASSES: Dict[str, Any] = {
    "financial_corporations_eq": {
        "name": "Equities in financial corporations",
        "gar_eligible": True,
        "btar_eligible": False,
        "numerator_condition": "Taxonomy-aligned activities of the financial corporation",
        "article": "Art 8 Del. Act Annex V §1.1",
    },
    "financial_corporations_debt": {
        "name": "Debt securities in financial corporations",
        "gar_eligible": True,
        "btar_eligible": False,
        "numerator_condition": "Taxonomy-aligned activities",
        "article": "Art 8 Del. Act Annex V §1.2",
    },
    "non_financial_corporations_eq": {
        "name": "Equities in non-financial corporations",
        "gar_eligible": True,
        "btar_eligible": True,
        "numerator_condition": "Taxonomy-aligned turnover, capex, or opex of NFC",
        "article": "Art 8 Del. Act Annex V §1.3",
    },
    "non_financial_corporations_debt": {
        "name": "Debt securities in non-financial corporations",
        "gar_eligible": True,
        "btar_eligible": True,
        "numerator_condition": "Taxonomy-aligned turnover, capex, or opex of NFC",
        "article": "Art 8 Del. Act Annex V §1.4",
    },
    "project_finance": {
        "name": "Specialised lending / Project Finance",
        "gar_eligible": True,
        "btar_eligible": True,
        "numerator_condition": (
            "Project activity taxonomy-aligned per relevant Delegated Act NACE activity"
        ),
        "article": "Art 8 Del. Act Annex V §1.6",
    },
    "mortgages": {
        "name": "Mortgage loans to households",
        "gar_eligible": True,
        "btar_eligible": True,
        "numerator_condition": "EPC A/B or NZEB compliance; CRREM pathway alignment",
        "article": "Art 8 Del. Act Annex V §1.7",
    },
    "auto_loans": {
        "name": "Motor vehicle loans",
        "gar_eligible": True,
        "btar_eligible": True,
        "numerator_condition": "Electric or hydrogen vehicle; EURO 6d equivalent",
        "article": "Art 8 Del. Act Annex V §1.8",
    },
    "home_renovation_loans": {
        "name": "Renovation loans",
        "gar_eligible": True,
        "btar_eligible": True,
        "numerator_condition": "Primary energy demand improvement ≥30%",
        "article": "Art 8 Del. Act Annex V §1.9",
    },
    "local_government_debt": {
        "name": "Local government debt",
        "gar_eligible": True,
        "btar_eligible": False,
        "numerator_condition": "Taxonomy-aligned capex or opex of issuer",
        "article": "Art 8 Del. Act Annex V §1.10",
    },
    "sovereigns": {
        "name": "Central government bonds",
        "gar_eligible": False,
        "btar_eligible": False,
        "numerator_condition": "Excluded from GAR numerator",
        "article": "Art 8 Del. Act §7",
    },
    "derivatives": {
        "name": "Derivatives",
        "gar_eligible": False,
        "btar_eligible": False,
        "numerator_condition": "Excluded",
        "article": "Art 8 Del. Act §7",
    },
}

DNSH_OBJECTIVES: Dict[str, str] = {
    "CCM": "Climate Change Mitigation — no significant harm to mitigation (GHG emissions threshold check)",
    "CCA": "Climate Change Adaptation — no significant harm to adaptation (climate risk assessment required)",
    "WMR": "Water and Marine Resources — water use, marine ecosystems not significantly harmed",
    "CE": "Circular Economy — waste prevention, reuse, recycling; no significant increase in waste",
    "PPE": "Pollution Prevention and Control — air, water, soil pollution not significantly increased",
    "BIO": "Biodiversity and Ecosystems — not significantly harming habitats, species, ecosystems",
}

MINIMUM_SAFEGUARDS: Dict[str, Any] = {
    "ungc": {
        "name": "UN Global Compact",
        "description": (
            "Entity not in violation of UNGC Ten Principles "
            "(human rights, labour, environment, anti-corruption)"
        ),
        "blocking": True,
    },
    "oecd_mne": {
        "name": "OECD Guidelines for MNEs",
        "description": (
            "Entity compliant with OECD Guidelines for Multinational Enterprises"
        ),
        "blocking": True,
    },
    "ungp": {
        "name": "UN Guiding Principles on Business & Human Rights",
        "description": "Entity applies UNGP Pillar II due diligence",
        "blocking": True,
    },
    "ilo_core": {
        "name": "ILO Core Conventions",
        "description": (
            "No violation of ILO core labour conventions (forced labour, child labour, "
            "discrimination, freedom of association)"
        ),
        "blocking": True,
    },
    "udhr": {
        "name": "UN Declaration of Human Rights",
        "description": "Entity respects fundamental human rights per UDHR",
        "blocking": False,
    },
}

GAR_PHASES: Dict[str, Any] = {
    "phase_1": {
        "period": "2022-2023",
        "scope": "Disclosure of KPIs: taxonomy eligible vs non-eligible",
        "mandatory": True,
    },
    "phase_2": {
        "period": "2024+",
        "scope": "Full GAR/BTAR/BSAR disclosure with taxonomy-aligned vs eligible split",
        "mandatory": True,
    },
}

TAXONOMY_CROSS_FRAMEWORK: Dict[str, str] = {
    "csrd_esrs_e1": (
        "ESRS E1-3 (energy) and E1-5 (GHG) inform CCM taxonomy technical screening criteria"
    ),
    "eu_gbs": (
        "EU GBS issuances require 100% taxonomy-aligned use of proceeds; "
        "GAR supports issuer eligibility"
    ),
    "sfdr_pai": (
        "SFDR PAI 14 (taxonomy alignment) directly pulls from EU Taxonomy GAR calculations"
    ),
    "mifid_spt": (
        "MiFID II Category A preference (taxonomy-aligned %) uses taxonomy alignment % from GAR/BTAR"
    ),
    "cbi": (
        "Climate Bonds Initiative certification complements taxonomy alignment for green bond verification"
    ),
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AssetExposure:
    asset_id: str
    asset_class: str
    total_exposure: float
    taxonomy_eligible_pct: float = 0.0
    taxonomy_aligned_pct: float = 0.0
    dnsh_confirmed: List[str] = field(default_factory=list)
    min_safeguards_confirmed: bool = False
    environmental_objective: str = "CCM"
    nace_code: str = ""
    notes: str = ""


@dataclass
class DNSHAssessment:
    asset_id: str
    objectives_assessed: List[str]
    objectives_passed: List[str]
    objectives_failed: List[str]
    dnsh_compliant: bool
    gaps: List[str]

    def dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "objectives_assessed": self.objectives_assessed,
            "objectives_passed": self.objectives_passed,
            "objectives_failed": self.objectives_failed,
            "dnsh_compliant": self.dnsh_compliant,
            "gaps": self.gaps,
        }


@dataclass
class MinSafeguardsAssessment:
    entity_id: str
    ungc_compliant: bool
    oecd_compliant: bool
    ungp_compliant: bool
    ilo_compliant: bool
    udhr_compliant: bool
    overall_compliant: bool
    blocking_gaps: List[str]

    def dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "ungc_compliant": self.ungc_compliant,
            "oecd_compliant": self.oecd_compliant,
            "ungp_compliant": self.ungp_compliant,
            "ilo_compliant": self.ilo_compliant,
            "udhr_compliant": self.udhr_compliant,
            "overall_compliant": self.overall_compliant,
            "blocking_gaps": self.blocking_gaps,
        }


@dataclass
class GARResult:
    entity_id: str
    entity_name: str
    reporting_year: int
    total_covered_assets: float
    gar_numerator: float
    gar_pct: float
    btar_numerator: float
    btar_covered_assets: float
    btar_pct: float
    bsar_pct: float
    taxonomy_eligible_pct: float
    taxonomy_aligned_pct: float
    asset_breakdown: List[Dict[str, Any]]
    dnsh_assessments: List[Dict[str, Any]]
    min_safeguards: Dict[str, Any]
    gaps: List[str]
    recommendations: List[str]
    cross_framework: Dict[str, str]
    generated_at: str

    def dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "reporting_year": self.reporting_year,
            "total_covered_assets": self.total_covered_assets,
            "gar_numerator": self.gar_numerator,
            "gar_pct": self.gar_pct,
            "btar_numerator": self.btar_numerator,
            "btar_covered_assets": self.btar_covered_assets,
            "btar_pct": self.btar_pct,
            "bsar_pct": self.bsar_pct,
            "taxonomy_eligible_pct": self.taxonomy_eligible_pct,
            "taxonomy_aligned_pct": self.taxonomy_aligned_pct,
            "asset_breakdown": self.asset_breakdown,
            "dnsh_assessments": self.dnsh_assessments,
            "min_safeguards": self.min_safeguards,
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "cross_framework": self.cross_framework,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EUTaxonomyGAREngine:
    """EU Taxonomy Green Finance KPI Reporter (E19) — Art 8 Delegated Act."""

    def assess_dnsh(self, assets: List[AssetExposure]) -> List[DNSHAssessment]:
        """Assess DNSH compliance for each asset."""
        results: List[DNSHAssessment] = []
        all_objectives = list(DNSH_OBJECTIVES.keys())

        for asset in assets:
            objectives_passed = [obj for obj in all_objectives if obj in asset.dnsh_confirmed]
            objectives_failed = [obj for obj in all_objectives if obj not in asset.dnsh_confirmed]
            dnsh_compliant = len(objectives_failed) == 0
            gaps = [
                f"DNSH objective {obj} not confirmed: {DNSH_OBJECTIVES[obj]}"
                for obj in objectives_failed
            ]
            results.append(DNSHAssessment(
                asset_id=asset.asset_id,
                objectives_assessed=all_objectives,
                objectives_passed=objectives_passed,
                objectives_failed=objectives_failed,
                dnsh_compliant=dnsh_compliant,
                gaps=gaps,
            ))
        return results

    def assess_min_safeguards(
        self,
        entity_id: str,
        entity_name: str,
        ungc: bool,
        oecd: bool,
        ungp: bool,
        ilo: bool,
        udhr: bool,
    ) -> MinSafeguardsAssessment:
        """Assess Minimum Safeguards compliance."""
        blocking_map = {"ungc": ungc, "oecd_mne": oecd, "ungp": ungp, "ilo_core": ilo}
        blocking_gaps = [
            f"{k} — {MINIMUM_SAFEGUARDS[k]['name']}: non-compliant"
            for k, v in blocking_map.items()
            if not v
        ]
        overall_compliant = len(blocking_gaps) == 0
        return MinSafeguardsAssessment(
            entity_id=entity_id,
            ungc_compliant=ungc,
            oecd_compliant=oecd,
            ungp_compliant=ungp,
            ilo_compliant=ilo,
            udhr_compliant=udhr,
            overall_compliant=overall_compliant,
            blocking_gaps=blocking_gaps,
        )

    def calculate_gar(
        self,
        entity_id: str,
        entity_name: str,
        reporting_year: int,
        assets: List[AssetExposure],
    ) -> GARResult:
        """Calculate GAR, BTAR, and taxonomy alignment metrics."""
        dnsh_results = self.assess_dnsh(assets)
        dnsh_by_id = {d.asset_id: d for d in dnsh_results}

        total_covered_assets = 0.0
        gar_numerator = 0.0
        btar_covered_assets = 0.0
        btar_numerator = 0.0
        eligible_weighted_sum = 0.0
        aligned_weighted_sum = 0.0
        asset_breakdown: List[Dict[str, Any]] = []
        gaps: List[str] = []

        for asset in assets:
            ac_cfg = GAR_ASSET_CLASSES.get(asset.asset_class, {})
            gar_eligible = ac_cfg.get("gar_eligible", False)
            btar_eligible = ac_cfg.get("btar_eligible", False)
            dnsh = dnsh_by_id.get(asset.asset_id)
            dnsh_ok = dnsh.dnsh_compliant if dnsh else False
            ms_ok = asset.min_safeguards_confirmed

            if gar_eligible:
                total_covered_assets += asset.total_exposure
                eligible_contribution = asset.total_exposure * asset.taxonomy_eligible_pct / 100
                eligible_weighted_sum += eligible_contribution

                # GAR numerator: taxonomy-aligned AND all DNSH confirmed AND min safeguards
                if dnsh_ok and ms_ok:
                    contribution = asset.total_exposure * asset.taxonomy_aligned_pct / 100
                    gar_numerator += contribution
                    aligned_weighted_sum += contribution
                else:
                    if not dnsh_ok:
                        gaps.append(
                            f"Asset {asset.asset_id}: DNSH incomplete — excluded from GAR numerator"
                        )
                    if not ms_ok:
                        gaps.append(
                            f"Asset {asset.asset_id}: Minimum Safeguards not confirmed — excluded from GAR numerator"
                        )

            if btar_eligible:
                btar_covered_assets += asset.total_exposure
                if dnsh_ok and ms_ok:
                    btar_numerator += asset.total_exposure * asset.taxonomy_aligned_pct / 100

            asset_breakdown.append({
                "asset_id": asset.asset_id,
                "asset_class": asset.asset_class,
                "asset_class_name": ac_cfg.get("name", asset.asset_class),
                "total_exposure": asset.total_exposure,
                "gar_eligible": gar_eligible,
                "btar_eligible": btar_eligible,
                "taxonomy_eligible_pct": asset.taxonomy_eligible_pct,
                "taxonomy_aligned_pct": asset.taxonomy_aligned_pct,
                "dnsh_compliant": dnsh_ok,
                "min_safeguards_confirmed": ms_ok,
                "included_in_gar_numerator": gar_eligible and dnsh_ok and ms_ok,
                "environmental_objective": asset.environmental_objective,
                "nace_code": asset.nace_code,
            })

        gar_pct = (gar_numerator / total_covered_assets * 100) if total_covered_assets > 0 else 0.0
        btar_pct = (btar_numerator / btar_covered_assets * 100) if btar_covered_assets > 0 else 0.0
        taxonomy_eligible_pct = (
            eligible_weighted_sum / total_covered_assets * 100
        ) if total_covered_assets > 0 else 0.0
        taxonomy_aligned_pct = gar_pct  # Same calculation basis

        # Recommendations
        recs: List[str] = []
        if gar_pct < 10.0:
            recs.append(
                f"GAR of {gar_pct:.1f}% is below typical EU Green Deal ambition levels. "
                "Consider increasing taxonomy-aligned lending/investment."
            )
        missing_dnsh = [a.asset_id for a in assets if not dnsh_by_id.get(a.asset_id, DNSHAssessment("","","","",False,[])).dnsh_compliant]
        if missing_dnsh:
            recs.append(
                f"{len(missing_dnsh)} asset(s) lack complete DNSH confirmation — obtain technical "
                "screening criteria evidence per Taxonomy Climate Delegated Act Annex I/II."
            )
        missing_ms = [a.asset_id for a in assets if not a.min_safeguards_confirmed]
        if missing_ms:
            recs.append(
                f"{len(missing_ms)} asset(s) missing Minimum Safeguards confirmation — "
                "conduct UNGC/OECD/UNGP/ILO due diligence on counterparties."
            )
        if not gaps:
            recs.append(
                "All assets have complete DNSH and Minimum Safeguards confirmations. "
                "Ensure annual review and Phase 2 aligned disclosure in annual report."
            )

        return GARResult(
            entity_id=entity_id,
            entity_name=entity_name,
            reporting_year=reporting_year,
            total_covered_assets=round(total_covered_assets, 2),
            gar_numerator=round(gar_numerator, 2),
            gar_pct=round(gar_pct, 4),
            btar_numerator=round(btar_numerator, 2),
            btar_covered_assets=round(btar_covered_assets, 2),
            btar_pct=round(btar_pct, 4),
            bsar_pct=0.0,  # Off-balance-sheet placeholder
            taxonomy_eligible_pct=round(taxonomy_eligible_pct, 4),
            taxonomy_aligned_pct=round(taxonomy_aligned_pct, 4),
            asset_breakdown=asset_breakdown,
            dnsh_assessments=[d.dict() for d in dnsh_results],
            min_safeguards={},  # Populated by caller or separate assess_min_safeguards call
            gaps=gaps,
            recommendations=recs,
            cross_framework=TAXONOMY_CROSS_FRAMEWORK,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Reference accessors
    # ------------------------------------------------------------------

    def get_asset_classes(self) -> Dict[str, Any]:
        return GAR_ASSET_CLASSES

    def get_dnsh_objectives(self) -> Dict[str, str]:
        return DNSH_OBJECTIVES

    def get_min_safeguards(self) -> Dict[str, Any]:
        return MINIMUM_SAFEGUARDS

    def get_gar_phases(self) -> Dict[str, Any]:
        return GAR_PHASES

    def get_cross_framework(self) -> Dict[str, str]:
        return TAXONOMY_CROSS_FRAMEWORK
