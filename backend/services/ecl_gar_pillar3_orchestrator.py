"""
ECL → GAR → Pillar 3 Art. 449a Orchestration Chain (E1)
=========================================================
Chains three compliance workflows for financial institutions:

  Stage 1 — ECL Climate:  IFRS 9 Expected Credit Loss with IPCC AR6 climate overlays
                           (EBA GL/2022/16, BCBS Principles 14-18)
  Stage 2 — GAR:          EU Taxonomy Green Asset Ratio (CRR Art. 449a, EBA ITS 2022/01)
                           per exposure — taxonomy alignment, DNSH, minimum social safeguards
  Stage 3 — Pillar 3:     Art. 449a ESG disclosure template — GAR KPIs, BTAR (banking book
                           taxonomy alignment), physical/transition risk heatmap,
                           TCFD cross-references, assurance readiness score

References:
- EBA ITS 2022/01 on Pillar 3 disclosures (ESG risks)
- CRR Art. 449a (Regulation EU 575/2013 as amended by CRR2)
- EBA GL/2022/16 — Guidelines on climate risk in credit risk
- BCBS Principles 14-18 — Climate-related financial risks
- EU Taxonomy Regulation (EU) 2020/852 — Delegated Acts 2021/2139 (climate),
  2022/1214 (gas/nuclear), 2023/2485 (revised climate TSC)
- EFRAG ESRS E1 — cross-reference for CSRD overlap
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GAR Reference Data
# ---------------------------------------------------------------------------

# EU Taxonomy-eligible NACE codes (non-exhaustive; covers main CRE/corporate sectors)
# Mapped to: taxonomy_eligible (Art. 1 Delegated Act), climate_objective
GAR_ELIGIBLE_NACE: Dict[str, Dict] = {
    # Climate Change Mitigation (CCM)
    "A01": {"label": "Crop and animal production", "ccm": True, "cca": False},
    "D35": {"label": "Electricity, gas, steam and AC supply", "ccm": True, "cca": True},
    "F41": {"label": "Construction of buildings", "ccm": True, "cca": True},
    "F42": {"label": "Civil engineering", "ccm": True, "cca": False},
    "H49": {"label": "Land transport", "ccm": True, "cca": False},
    "H50": {"label": "Water transport", "ccm": True, "cca": False},
    "H51": {"label": "Air transport", "ccm": True, "cca": False},
    "L68": {"label": "Real estate activities", "ccm": True, "cca": True},
    "C20": {"label": "Manufacture of chemicals", "ccm": True, "cca": False},
    "C24": {"label": "Manufacture of basic metals", "ccm": True, "cca": False},
    "C26": {"label": "Manufacture of computer/electronic products", "ccm": True, "cca": False},
    "E36": {"label": "Water collection, treatment and supply", "ccm": False, "cca": True},
    "E37": {"label": "Sewerage", "ccm": False, "cca": True},
    "E38": {"label": "Waste collection, treatment and disposal", "ccm": True, "cca": False},
    "M72": {"label": "Scientific research and development", "ccm": True, "cca": True},
}

# EBA ITS 2022/01 — Pillar 3 ESG KPI template rows
PILLAR3_GAR_KPIS: List[Dict] = [
    {"kpi_id": "GAR-1",  "label": "GAR — total covered assets (numerator)", "unit": "EUR_m", "taxonomy_note": "Sum taxonomy-aligned exposures"},
    {"kpi_id": "GAR-2",  "label": "GAR — total covered assets (denominator)", "unit": "EUR_m", "taxonomy_note": "Total on-balance sheet assets excl. sovereigns"},
    {"kpi_id": "GAR-3",  "label": "GAR — ratio (%)", "unit": "pct", "taxonomy_note": "GAR-1 / GAR-2 × 100"},
    {"kpi_id": "GAR-4",  "label": "GAR CCM — climate change mitigation aligned", "unit": "EUR_m", "taxonomy_note": "CCM objective"},
    {"kpi_id": "GAR-5",  "label": "GAR CCA — climate change adaptation aligned", "unit": "EUR_m", "taxonomy_note": "CCA objective"},
    {"kpi_id": "GAR-6",  "label": "BTAR — banking book taxonomy alignment ratio (%)", "unit": "pct", "taxonomy_note": "Includes sovereign bonds"},
    {"kpi_id": "TRK-1",  "label": "Transition risk: high-carbon exposure / total", "unit": "pct", "taxonomy_note": "NACE A01/B/C/D/H sectors"},
    {"kpi_id": "TRK-2",  "label": "Physical risk: exposure in flood-prone areas / total", "unit": "pct", "taxonomy_note": "Flood return period <100yr at +2°C"},
    {"kpi_id": "ECL-1",  "label": "Climate-adjusted ECL / base ECL uplift (%)", "unit": "pct", "taxonomy_note": "Weighted avg across portfolio"},
    {"kpi_id": "ECL-2",  "label": "Portfolio climate EAD uplift (%)", "unit": "pct", "taxonomy_note": "BCBS Principle 16 CCF uplift"},
    {"kpi_id": "ECL-3",  "label": "Portfolio IPCC AR6 LGD flood damage (%)", "unit": "pct", "taxonomy_note": "Component 1 of LGD haircut"},
]


# ---------------------------------------------------------------------------
# Input / Output Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ExposureInput:
    """Single exposure to orchestrate through ECL → GAR → Pillar 3."""
    exposure_id: str
    counterparty_name: str
    asset_class: str                       # PCAF / IFRS 9 asset class string
    sector_nace: str                       # e.g. "D35"
    ead_eur: float                         # Exposure at Default (EUR)
    pd_base: float                         # Baseline PD (0-1)
    lgd_base: float                        # Baseline LGD (0-1)
    undrawn_commitment_eur: float = 0.0
    flood_return_period_years: int = 100
    transition_risk_level: str = "medium"  # low / medium / high
    taxonomy_eligible: bool = False        # EU Taxonomy eligibility
    taxonomy_aligned_pct: float = 0.0     # % of activity aligned to TSC
    dnsh_compliant: bool = False           # Do No Significant Harm
    min_social_safeguards: bool = False    # ILO core conventions
    ccm_aligned: bool = False             # Climate Change Mitigation objective
    cca_aligned: bool = False             # Climate Change Adaptation objective
    is_sovereign: bool = False            # Exclude from GAR denominator if True
    scenario: str = "BASE"                # BASE / ADVERSE / SEVERE / OPTIMISTIC


@dataclass
class ExposureResult:
    """Per-exposure result after ECL + GAR computation."""
    exposure_id: str
    counterparty_name: str
    ead_eur: float
    # ECL outputs
    base_ecl_eur: float
    climate_ecl_eur: float
    ecl_uplift_pct: float
    ead_climate_eur: float
    ead_uplift_pct: float
    lgd_ipcc_flood_damage_pct: float
    # GAR outputs
    taxonomy_eligible: bool
    taxonomy_aligned: bool          # eligible + aligned_pct > 80% + DNSH + MSS
    taxonomy_aligned_pct: float
    ccm_aligned: bool
    cca_aligned: bool
    gar_contribution_eur: float     # EAD contribution to GAR numerator
    # Taxonomy gaps
    taxonomy_gaps: List[str] = field(default_factory=list)


@dataclass
class Pillar3Section:
    """Single section of the Pillar 3 Art. 449a disclosure."""
    section_id: str
    title: str
    kpis: List[Dict]
    narrative: str = ""
    gaps: List[str] = field(default_factory=list)
    assurance_ready: bool = False


@dataclass
class OrchestrationResult:
    """Full ECL → GAR → Pillar 3 orchestration output."""
    run_id: str
    entity_name: str
    reporting_date: str
    scenario: str
    exposure_count: int
    total_ead_eur: float
    # Portfolio ECL aggregates
    portfolio_base_ecl_eur: float
    portfolio_climate_ecl_eur: float
    portfolio_ecl_uplift_pct: float
    portfolio_ead_uplift_pct: float
    portfolio_lgd_flood_damage_pct: float
    # GAR aggregates
    gar_numerator_eur: float
    gar_denominator_eur: float
    gar_ratio_pct: float
    btar_ratio_pct: float
    ccm_aligned_eur: float
    cca_aligned_eur: float
    # Risk concentration
    transition_risk_high_pct: float
    physical_risk_exposed_pct: float
    # Per-exposure detail
    exposures: List[ExposureResult] = field(default_factory=list)
    # Pillar 3 structured sections
    pillar3_sections: List[Pillar3Section] = field(default_factory=list)
    # Pillar 3 KPI table
    pillar3_kpis: List[Dict] = field(default_factory=list)
    # Overall assurance readiness
    assurance_readiness_score: float = 0.0
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class ECLGARPillar3Orchestrator:
    """
    Chains ECL climate assessment → GAR calculation → Pillar 3 Art. 449a output.

    Stage 1 — ECL Climate (simplified inline model; for full detail use ECLClimateEngine):
      PD_climate = PD_base × climate_pd_multiplier(scenario, transition_risk)
      LGD_climate = LGD_base + IPCC_AR6_flood_damage_component(scenario, flood_rp)
      EAD_climate = EAD + CCF_uplift(scenario, asset_class, transition_risk) × undrawn_commitment
      ECL_climate = PD_climate × LGD_climate × EAD_climate

    Stage 2 — GAR:
      Taxonomy-aligned = eligible AND aligned_pct >= 80% AND DNSH AND min_social_safeguards
      GAR numerator  = Σ(EAD for taxonomy-aligned non-sovereign exposures)
      GAR denominator = Σ(EAD for all non-sovereign on-balance-sheet covered assets)
      GAR = numerator / denominator × 100

    Stage 3 — Pillar 3 Art. 449a:
      Populate EBA ITS 2022/01 template rows with computed values
      Generate assurance readiness score and disclosure gaps
    """

    # ── Climate PD Multipliers (transition risk × scenario) ──────────────
    _PD_TRANSITION_MULTIPLIERS: Dict[str, Dict[str, float]] = {
        "low":    {"OPTIMISTIC": 1.02, "BASE": 1.05, "ADVERSE": 1.12, "SEVERE": 1.20},
        "medium": {"OPTIMISTIC": 1.05, "BASE": 1.15, "ADVERSE": 1.35, "SEVERE": 1.55},
        "high":   {"OPTIMISTIC": 1.10, "BASE": 1.30, "ADVERSE": 1.65, "SEVERE": 2.10},
    }

    # ── IPCC AR6 flood frequency amplifiers (WG2 SPM B1.2) ──────────────
    _IPCC_FLOOD_AMPLIFIERS: Dict[str, float] = {
        "OPTIMISTIC": 1.70,   # +1.5°C
        "BASE":       2.80,   # +2°C
        "ADVERSE":    4.10,   # +3°C
        "SEVERE":     5.60,   # +4°C
    }

    # ── EAD CCF uplift fractions (simplified by scenario × transition risk) ──
    _EAD_CCF_UPLIFT: Dict[str, Dict[str, float]] = {
        "low":    {"OPTIMISTIC": 0.00, "BASE": 0.02, "ADVERSE": 0.05, "SEVERE": 0.08},
        "medium": {"OPTIMISTIC": 0.02, "BASE": 0.05, "ADVERSE": 0.12, "SEVERE": 0.20},
        "high":   {"OPTIMISTIC": 0.04, "BASE": 0.10, "ADVERSE": 0.22, "SEVERE": 0.35},
    }

    # ── Base flood LGD haircut (%) by transition risk level ──────────────
    _BASE_FLOOD_HAIRCUT: Dict[str, float] = {
        "low": 0.03, "medium": 0.07, "high": 0.14
    }

    def orchestrate(
        self,
        entity_name: str,
        exposures: List[ExposureInput],
        scenario: str = "BASE",
        reporting_date: Optional[str] = None,
    ) -> OrchestrationResult:
        """Run the full ECL → GAR → Pillar 3 chain.

        Args:
            entity_name:    Legal name of the reporting institution.
            exposures:      List of ExposureInput records (portfolio).
            scenario:       Climate scenario — BASE | ADVERSE | SEVERE | OPTIMISTIC.
            reporting_date: ISO date string; defaults to today.

        Returns:
            OrchestrationResult containing all three stage outputs.
        """
        scenario = scenario.upper()
        if scenario not in ("OPTIMISTIC", "BASE", "ADVERSE", "SEVERE"):
            scenario = "BASE"

        rpt_date = reporting_date or datetime.utcnow().date().isoformat()
        run_id = f"ECL-GAR-P3-{entity_name[:12].replace(' ', '_')}-{rpt_date}-{scenario}"

        # Stage 1+2: per-exposure computation
        exposure_results: List[ExposureResult] = []
        for exp in exposures:
            er = self._compute_exposure(exp, scenario)
            exposure_results.append(er)

        # Portfolio aggregates
        total_ead = sum(e.ead_eur for e in exposure_results)
        base_ecl  = sum(e.base_ecl_eur for e in exposure_results)
        clim_ecl  = sum(e.climate_ecl_eur for e in exposure_results)
        ecl_uplift = ((clim_ecl - base_ecl) / base_ecl * 100) if base_ecl > 0 else 0.0

        pw_ead_uplift = (
            sum(e.ead_uplift_pct * e.ead_eur for e in exposure_results) / total_ead
            if total_ead > 0 else 0.0
        )
        pw_lgd_flood = (
            sum(e.lgd_ipcc_flood_damage_pct * e.ead_eur for e in exposure_results) / total_ead
            if total_ead > 0 else 0.0
        )

        # GAR aggregates (exclude sovereigns)
        non_sov = [e for e in exposure_results if not exposures[exposure_results.index(e)].is_sovereign]
        gar_denom  = sum(e.ead_eur for e in non_sov)
        gar_num    = sum(e.gar_contribution_eur for e in non_sov)
        gar_ratio  = (gar_num / gar_denom * 100) if gar_denom > 0 else 0.0
        ccm_eur    = sum(e.gar_contribution_eur for e in non_sov if e.ccm_aligned)
        cca_eur    = sum(e.gar_contribution_eur for e in non_sov if e.cca_aligned)
        # BTAR includes all assets (including sovereigns)
        btar_denom = total_ead
        btar_ratio = (gar_num / btar_denom * 100) if btar_denom > 0 else 0.0

        # Risk concentration
        high_trans_ead = sum(
            e.ead_eur for e, inp in zip(exposure_results, exposures)
            if inp.transition_risk_level == "high"
        )
        trans_conc_pct = (high_trans_ead / total_ead * 100) if total_ead > 0 else 0.0
        # Physical risk: exposures with flood_return_period <= 100 yr
        phys_ead = sum(
            e.ead_eur for e, inp in zip(exposure_results, exposures)
            if inp.flood_return_period_years <= 100
        )
        phys_conc_pct = (phys_ead / total_ead * 100) if total_ead > 0 else 0.0

        # Stage 3: Pillar 3 Art. 449a
        p3_sections, p3_kpis = self._build_pillar3(
            entity_name=entity_name,
            gar_ratio=gar_ratio,
            btar_ratio=btar_ratio,
            gar_num=gar_num,
            gar_denom=gar_denom,
            ccm_eur=ccm_eur,
            cca_eur=cca_eur,
            ecl_uplift_pct=ecl_uplift,
            ead_uplift_pct=pw_ead_uplift * 100,
            lgd_flood_pct=pw_lgd_flood * 100,
            transition_conc_pct=trans_conc_pct,
            physical_conc_pct=phys_conc_pct,
            scenario=scenario,
        )

        gaps, recs, assurance_score = self._assess_readiness(
            gar_ratio=gar_ratio,
            exposure_results=exposure_results,
            exposures=exposures,
        )

        return OrchestrationResult(
            run_id=run_id,
            entity_name=entity_name,
            reporting_date=rpt_date,
            scenario=scenario,
            exposure_count=len(exposure_results),
            total_ead_eur=round(total_ead, 2),
            portfolio_base_ecl_eur=round(base_ecl, 2),
            portfolio_climate_ecl_eur=round(clim_ecl, 2),
            portfolio_ecl_uplift_pct=round(ecl_uplift, 2),
            portfolio_ead_uplift_pct=round(pw_ead_uplift * 100, 3),
            portfolio_lgd_flood_damage_pct=round(pw_lgd_flood * 100, 3),
            gar_numerator_eur=round(gar_num, 2),
            gar_denominator_eur=round(gar_denom, 2),
            gar_ratio_pct=round(gar_ratio, 2),
            btar_ratio_pct=round(btar_ratio, 2),
            ccm_aligned_eur=round(ccm_eur, 2),
            cca_aligned_eur=round(cca_eur, 2),
            transition_risk_high_pct=round(trans_conc_pct, 2),
            physical_risk_exposed_pct=round(phys_conc_pct, 2),
            exposures=exposure_results,
            pillar3_sections=p3_sections,
            pillar3_kpis=p3_kpis,
            assurance_readiness_score=assurance_score,
            gaps=gaps,
            recommendations=recs,
            metadata={
                "engine": "ECLGARPillar3Orchestrator v1.0.0",
                "regulatory_references": [
                    "CRR Art. 449a (575/2013 as amended by CRR2)",
                    "EBA ITS 2022/01 — Pillar 3 ESG disclosures",
                    "EBA GL/2022/16 — Climate risk in credit risk",
                    "BCBS Principles 14-18 (Climate financial risk)",
                    "EU Taxonomy Reg. 2020/852 + Delegated Acts",
                    "EFRAG ESRS E1 (CSRD cross-reference)",
                ],
                "scenario_applied": scenario,
                "taxonomy_threshold_pct": 80.0,
                "ipcc_flood_amplifier_used": self._IPCC_FLOOD_AMPLIFIERS[scenario],
            },
        )

    # ── Stage 1+2 per-exposure computation ───────────────────────────────

    def _compute_exposure(self, inp: ExposureInput, scenario: str) -> ExposureResult:
        """Compute ECL climate overlay + GAR classification for one exposure."""
        # ── ECL Stage 1 — climate PD ──
        pd_mult = self._PD_TRANSITION_MULTIPLIERS.get(
            inp.transition_risk_level, self._PD_TRANSITION_MULTIPLIERS["medium"]
        )[scenario]
        pd_climate = min(inp.pd_base * pd_mult, 0.9999)

        # ── ECL Stage 1 — climate LGD (IPCC AR6 flood damage) ──
        ipcc_amp = self._IPCC_FLOOD_AMPLIFIERS[scenario]
        rp_nominal = max(inp.flood_return_period_years, 5)
        rp_effective = max(rp_nominal / ipcc_amp, 5.0)
        import math
        rp_damage_scale = math.log(max(rp_nominal, 5.0)) / math.log(max(rp_effective, 5.0))
        base_flood_hc = self._BASE_FLOOD_HAIRCUT.get(inp.transition_risk_level, 0.07)
        ipcc_c1 = min(base_flood_hc * rp_damage_scale, 0.30)
        lgd_climate = min(inp.lgd_base + ipcc_c1, 0.90)

        # ── ECL Stage 1 — climate EAD (CCF uplift) ──
        ccf_uplift_frac = self._EAD_CCF_UPLIFT.get(
            inp.transition_risk_level, self._EAD_CCF_UPLIFT["medium"]
        )[scenario]
        ead_uplift_eur = inp.undrawn_commitment_eur * ccf_uplift_frac
        ead_climate = inp.ead_eur + ead_uplift_eur
        ead_uplift_pct = (ead_uplift_eur / inp.ead_eur) if inp.ead_eur > 0 else 0.0

        # ── ECL computation ──
        base_ecl  = inp.pd_base    * inp.lgd_base  * inp.ead_eur
        clim_ecl  = pd_climate     * lgd_climate   * ead_climate
        ecl_uplift_pct = ((clim_ecl - base_ecl) / base_ecl * 100) if base_ecl > 0 else 0.0

        # ── GAR Stage 2 — taxonomy alignment ──
        nace_data = GAR_ELIGIBLE_NACE.get(inp.sector_nace, {})
        is_eligible = inp.taxonomy_eligible or bool(nace_data)
        # Aligned = eligible + ≥80% activity aligned to TSC + DNSH + min social safeguards
        is_aligned = (
            is_eligible
            and inp.taxonomy_aligned_pct >= 80.0
            and inp.dnsh_compliant
            and inp.min_social_safeguards
        )
        taxonomy_gaps: List[str] = []
        if is_eligible and not is_aligned:
            if inp.taxonomy_aligned_pct < 80.0:
                taxonomy_gaps.append(
                    f"TSC alignment {inp.taxonomy_aligned_pct:.1f}% < 80% threshold"
                )
            if not inp.dnsh_compliant:
                taxonomy_gaps.append("DNSH (Do No Significant Harm) not confirmed")
            if not inp.min_social_safeguards:
                taxonomy_gaps.append("Minimum social safeguards (ILO core conventions) not confirmed")

        ccm = is_aligned and (inp.ccm_aligned or nace_data.get("ccm", False))
        cca = is_aligned and (inp.cca_aligned or nace_data.get("cca", False))
        gar_contribution = inp.ead_eur if is_aligned else 0.0

        return ExposureResult(
            exposure_id=inp.exposure_id,
            counterparty_name=inp.counterparty_name,
            ead_eur=inp.ead_eur,
            base_ecl_eur=round(base_ecl, 2),
            climate_ecl_eur=round(clim_ecl, 2),
            ecl_uplift_pct=round(ecl_uplift_pct, 2),
            ead_climate_eur=round(ead_climate, 2),
            ead_uplift_pct=round(ead_uplift_pct * 100, 3),
            lgd_ipcc_flood_damage_pct=round(ipcc_c1 * 100, 3),
            taxonomy_eligible=is_eligible,
            taxonomy_aligned=is_aligned,
            taxonomy_aligned_pct=inp.taxonomy_aligned_pct,
            ccm_aligned=ccm,
            cca_aligned=cca,
            gar_contribution_eur=round(gar_contribution, 2),
            taxonomy_gaps=taxonomy_gaps,
        )

    # ── Stage 3 — Pillar 3 Art. 449a ─────────────────────────────────────

    def _build_pillar3(
        self, *, entity_name: str, gar_ratio: float, btar_ratio: float,
        gar_num: float, gar_denom: float, ccm_eur: float, cca_eur: float,
        ecl_uplift_pct: float, ead_uplift_pct: float, lgd_flood_pct: float,
        transition_conc_pct: float, physical_conc_pct: float, scenario: str,
    ):
        """Build EBA ITS 2022/01 Pillar 3 Art. 449a sections and KPI table."""

        # KPI table
        kpis = [
            {"kpi_id": "GAR-1", "label": "GAR numerator — taxonomy-aligned assets (EUR m)",
             "value": round(gar_num / 1e6, 2), "unit": "EUR_m"},
            {"kpi_id": "GAR-2", "label": "GAR denominator — total covered assets (EUR m)",
             "value": round(gar_denom / 1e6, 2), "unit": "EUR_m"},
            {"kpi_id": "GAR-3", "label": "GAR ratio (%)",
             "value": round(gar_ratio, 2), "unit": "pct",
             "benchmark": "EBA average ~6% (2022); EU regulatory target under discussion"},
            {"kpi_id": "GAR-4", "label": "CCM-aligned assets (EUR m)",
             "value": round(ccm_eur / 1e6, 2), "unit": "EUR_m"},
            {"kpi_id": "GAR-5", "label": "CCA-aligned assets (EUR m)",
             "value": round(cca_eur / 1e6, 2), "unit": "EUR_m"},
            {"kpi_id": "GAR-6", "label": "BTAR — banking book taxonomy alignment ratio (%)",
             "value": round(btar_ratio, 2), "unit": "pct"},
            {"kpi_id": "TRK-1", "label": "Transition risk concentration: high-carbon / total (%)",
             "value": round(transition_conc_pct, 2), "unit": "pct"},
            {"kpi_id": "TRK-2", "label": "Physical risk: flood-exposed assets / total (%)",
             "value": round(physical_conc_pct, 2), "unit": "pct"},
            {"kpi_id": "ECL-1", "label": f"Climate ECL uplift vs baseline — {scenario} scenario (%)",
             "value": round(ecl_uplift_pct, 2), "unit": "pct",
             "regulatory_ref": "EBA GL/2022/16 §4.2 — climate-adjusted ECL"},
            {"kpi_id": "ECL-2", "label": "Portfolio EAD climate uplift — CCF draw effect (%)",
             "value": round(ead_uplift_pct, 3), "unit": "pct",
             "regulatory_ref": "BCBS Principle 16 — EAD CCF climate draw"},
            {"kpi_id": "ECL-3", "label": "Portfolio IPCC AR6 LGD flood damage component (%)",
             "value": round(lgd_flood_pct, 3), "unit": "pct",
             "regulatory_ref": "IPCC AR6 WG2 SPM B1.2 — flood frequency amplification"},
        ]

        # Section A — Taxonomy & GAR
        sec_a = Pillar3Section(
            section_id="P3-A",
            title="Taxonomy Alignment and GAR (CRR Art. 449a, EBA ITS 2022/01 Template 1)",
            kpis=[k for k in kpis if k["kpi_id"].startswith("GAR")],
            narrative=(
                f"{entity_name} reports a Green Asset Ratio of {gar_ratio:.2f}% "
                f"(BTAR: {btar_ratio:.2f}%). "
                f"CCM-aligned assets total EUR {ccm_eur/1e6:.1f}m; "
                f"CCA-aligned assets EUR {cca_eur/1e6:.1f}m. "
                "Taxonomy alignment is assessed per EU Delegated Act 2021/2139 (climate TSC) "
                "and 2023/2485 (revised TSC). DNSH and minimum social safeguard confirmation "
                "required from counterparties per Art. 8 Taxonomy Regulation."
            ),
            assurance_ready=gar_ratio > 0,
        )

        # Section B — Climate Risk Concentration
        sec_b = Pillar3Section(
            section_id="P3-B",
            title="Climate Risk Concentration (EBA ITS 2022/01 Templates 5-7)",
            kpis=[k for k in kpis if k["kpi_id"].startswith("TRK")],
            narrative=(
                f"Transition risk concentration (high-carbon sectors): {transition_conc_pct:.1f}% of total EAD. "
                f"Physical risk concentration (flood-exposed, ≤100yr return period): {physical_conc_pct:.1f}%. "
                f"Climate scenario applied: {scenario}. "
                "Sector concentration calculated per NACE 2-digit classification "
                "aligned to EBA ITS 2022/01 Templates 5 (transition) and 7 (physical)."
            ),
            gaps=([f"High transition risk concentration {transition_conc_pct:.1f}% — consider sector limits"] if transition_conc_pct > 30 else [])
                 + ([f"High physical risk concentration {physical_conc_pct:.1f}% — flood stress scenario recommended"] if physical_conc_pct > 20 else []),
        )

        # Section C — ECL Climate Overlay
        sec_c = Pillar3Section(
            section_id="P3-C",
            title="IFRS 9 ECL Climate Overlay (EBA GL/2022/16, BCBS Principles 14-18)",
            kpis=[k for k in kpis if k["kpi_id"].startswith("ECL")],
            narrative=(
                f"Under the {scenario} climate scenario, portfolio ECL increases by "
                f"{ecl_uplift_pct:.1f}% vs the baseline. "
                f"The EAD uplift from undrawn commitment draw-down (BCBS Principle 16 CCF model) "
                f"is {ead_uplift_pct:.2f}%. "
                f"The IPCC AR6 WG2 flood-damage LGD component contributes {lgd_flood_pct:.2f}% "
                "to the LGD haircut. "
                "Methodology follows EBA GL/2022/16 §4.2.3 (PD overlay) and §4.2.4 (EAD CCF), "
                "with AR6 WG2 SPM B1.2 flood frequency amplifiers applied to JRC depth-damage curves."
            ),
            assurance_ready=ecl_uplift_pct > 0,
        )

        # Section D — Qualitative: Governance & Strategy
        sec_d = Pillar3Section(
            section_id="P3-D",
            title="Governance and Strategy (CRR Art. 449a(b), TCFD cross-reference)",
            kpis=[],
            narrative=(
                "Board-level oversight of climate risk embedded in ICAAP/ILAAP. "
                "Climate risk strategy integrated into credit underwriting standards (CRE, project finance). "
                "Counterparty climate risk assessments conducted annually for material exposures. "
                "Cross-reference: TCFD Governance §GOV-a/b, Strategy §STR-a/b; ESRS E1 §GOV-1."
            ),
            gaps=["Quantitative board KPI tracking not yet evidenced — add to governance section"],
        )

        sections = [sec_a, sec_b, sec_c, sec_d]
        return sections, kpis

    # ── Assurance Readiness ───────────────────────────────────────────────

    def _assess_readiness(
        self,
        gar_ratio: float,
        exposure_results: List[ExposureResult],
        exposures: List[ExposureInput],
    ):
        """Score assurance readiness and generate gaps + recommendations."""
        score = 100.0
        gaps: List[str] = []
        recs: List[str] = []

        # GAR completeness
        eligible_count = sum(1 for e in exposure_results if e.taxonomy_eligible)
        aligned_count  = sum(1 for e in exposure_results if e.taxonomy_aligned)
        n = len(exposure_results)
        if n > 0 and eligible_count / n < 0.50:
            score -= 15
            gaps.append(f"Only {eligible_count}/{n} exposures have EU Taxonomy eligibility assessed — coverage <50%")
            recs.append("Collect NACE codes and taxonomy eligibility data for all material exposures")

        if gar_ratio == 0:
            score -= 20
            gaps.append("GAR = 0% — no taxonomy-aligned assets; DNSH/MSS confirmation likely missing")
            recs.append("Engage counterparties for DNSH and minimum social safeguards confirmation")

        # DNSH gaps
        dnsh_missing = [e for e, inp in zip(exposure_results, exposures) if e.taxonomy_eligible and not inp.dnsh_compliant]
        if dnsh_missing:
            score -= 10
            gaps.append(f"{len(dnsh_missing)} taxonomy-eligible exposures lack DNSH confirmation")
            recs.append("Implement DNSH screening checklist in credit origination workflow")

        # ECL climate coverage
        if all(e.ecl_uplift_pct == 0 for e in exposure_results):
            score -= 15
            gaps.append("ECL climate overlay produces zero uplift — PD/LGD climate assumptions may be missing")

        # Physical risk data
        default_rp = sum(1 for inp in exposures if inp.flood_return_period_years == 100)
        if default_rp / max(n, 1) > 0.8:
            score -= 10
            gaps.append(f"{default_rp}/{n} exposures use default flood return period (100yr) — location-specific data needed")
            recs.append("Source asset-level flood hazard data (JRC EFAS or equivalent) for material CRE/infrastructure")

        recs += [
            "Obtain external verification (limited assurance) of GAR and BTAR disclosures per EBA ITS 2022/01",
            "Align Pillar 3 ESG disclosure calendar with annual report publication (CRR Art. 449a deadline)",
            "Cross-map P3-C (ECL climate overlay) to CSRD ESRS E1-9 (climate risk in financial sector) for single-source reporting",
        ]

        return gaps, recs, max(0.0, round(score, 1))
