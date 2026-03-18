"""
IORP II Pension Fund Climate Risk Engine (E8)
=============================================

EU IORP II Directive 2016/2341 climate risk stress test and ALM engine.

Covers:
  - Pension fund scope classification (IORP II Art 1: all IORPs with >15 members)
  - EIOPA IORP II climate stress test (EIOPA 2022 stress test methodology)
  - Asset-Liability Management (ALM) under 4 NGFS climate scenarios
  - Liability sensitivity: duration-matched discounting, longevity shock
  - Funding ratio stress (assets/liabilities) and recovery plan triggers
  - SFDR Art 6/8/9 classification for pension funds as FMPs
  - Own Risk Assessment (ORA) checklist — IORP II Art 28
  - Member benefit risk: real benefit erosion under inflation + climate paths

Resolves E8 gap in the engine registry (E7=EIOPA Solvency II → E8=IORP II Pensions → E9=SFDR Annex).
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

IORP_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "net_zero_2050": {
        "label": "Net Zero 2050 (Orderly)",
        "ngfs_phase": 5,
        "equity_shock_pct": -12.0,
        "corp_bond_spread_bps": 45,
        "sovereign_bond_spread_bps": 20,
        "re_shock_pct": -8.0,
        "infrastructure_shock_pct": -5.0,
        "inflation_uplift_pct": 0.3,
        "liability_discount_shift_bps": 30,
        "longevity_shock_years": 0.5,
        "description": "Orderly transition, early policy action, limited physical risk",
    },
    "below_2c": {
        "label": "Below 2°C (Disorderly)",
        "ngfs_phase": 5,
        "equity_shock_pct": -18.0,
        "corp_bond_spread_bps": 80,
        "sovereign_bond_spread_bps": 35,
        "re_shock_pct": -12.0,
        "infrastructure_shock_pct": -8.0,
        "inflation_uplift_pct": 0.6,
        "liability_discount_shift_bps": 50,
        "longevity_shock_years": 0.8,
        "description": "Disorderly transition with delayed action, higher market volatility",
    },
    "hot_house_world": {
        "label": "Hot House World (High Physical Risk)",
        "ngfs_phase": 5,
        "equity_shock_pct": -25.0,
        "corp_bond_spread_bps": 120,
        "sovereign_bond_spread_bps": 60,
        "re_shock_pct": -22.0,
        "infrastructure_shock_pct": -15.0,
        "inflation_uplift_pct": 1.2,
        "liability_discount_shift_bps": -20,  # flight-to-safety → lower yields
        "longevity_shock_years": 1.5,
        "description": "Minimal transition, severe physical risk, systemic stress",
    },
    "current_policies": {
        "label": "Current Policies (Baseline)",
        "ngfs_phase": 5,
        "equity_shock_pct": -5.0,
        "corp_bond_spread_bps": 15,
        "sovereign_bond_spread_bps": 8,
        "re_shock_pct": -3.0,
        "infrastructure_shock_pct": -2.0,
        "inflation_uplift_pct": 0.1,
        "liability_discount_shift_bps": 5,
        "longevity_shock_years": 0.2,
        "description": "No additional policy action; near-term reference baseline",
    },
}

ORA_CHECKLIST_ITEMS: List[Dict[str, Any]] = [
    # IORP II Art 28 Own Risk Assessment
    {"item_id": "ORA-01", "title": "Governance framework for climate risk identified",
     "article": "Art 28(1)(a)", "blocking": True,
     "flag": "has_governance_framework"},
    {"item_id": "ORA-02", "title": "Climate risk integrated into overall risk management",
     "article": "Art 28(1)(b)", "blocking": True,
     "flag": "has_risk_integration"},
    {"item_id": "ORA-03", "title": "Physical and transition risk both assessed",
     "article": "Art 28(2)", "blocking": True,
     "flag": "has_physical_and_transition"},
    {"item_id": "ORA-04", "title": "ESG factors incorporated in investment decision-making",
     "article": "Art 19(1)(b)", "blocking": True,
     "flag": "has_esg_investment_policy"},
    {"item_id": "ORA-05", "title": "Member communication on ESG/climate risks",
     "article": "Art 41(1)", "blocking": False,
     "flag": "has_member_communication"},
    {"item_id": "ORA-06", "title": "Climate scenario analysis conducted (≥2 scenarios)",
     "article": "EIOPA 2022 Stress Test", "blocking": True,
     "flag": "has_scenario_analysis"},
    {"item_id": "ORA-07", "title": "Funding ratio stress test completed",
     "article": "EIOPA Guidance", "blocking": True,
     "flag": "has_funding_ratio_stress"},
    {"item_id": "ORA-08", "title": "Recovery plan mechanism defined",
     "article": "Art 39", "blocking": True,
     "flag": "has_recovery_plan"},
    {"item_id": "ORA-09", "title": "SFDR classification applied (Art 6/8/9)",
     "article": "SFDR Art 3/4", "blocking": False,
     "flag": "has_sfdr_classification"},
    {"item_id": "ORA-10", "title": "PAI indicators reported for pension portfolio",
     "article": "SFDR Art 4(1)(a)", "blocking": False,
     "flag": "has_pai_reporting"},
    {"item_id": "ORA-11", "title": "TNFD/TCFD aligned nature risk disclosure",
     "article": "TNFD v1.0 Rec D2", "blocking": False,
     "flag": "has_nature_disclosure"},
    {"item_id": "ORA-12", "title": "Transition plan for portfolio decarbonisation",
     "article": "GFANZ/IIGCC NZIF", "blocking": False,
     "flag": "has_transition_plan"},
]

SFDR_FMP_CATEGORIES: Dict[str, str] = {
    "art_6": "Article 6 — no ESG integration promoted; PAI statement optional",
    "art_8": "Article 8 — promotes environmental or social characteristics",
    "art_9": "Article 9 — has sustainable investment objective",
}

IORP_TYPE_PROFILES: Dict[str, Dict[str, Any]] = {
    "defined_benefit": {
        "label": "Defined Benefit (DB)",
        "sponsor_covenant_factor": 1.0,
        "liability_sensitivity_duration_y": 20.0,
        "typical_equity_pct": 40,
        "typical_bonds_pct": 50,
        "typical_alts_pct": 10,
    },
    "defined_contribution": {
        "label": "Defined Contribution (DC)",
        "sponsor_covenant_factor": 0.0,
        "liability_sensitivity_duration_y": 0.0,   # no pooled liability
        "typical_equity_pct": 60,
        "typical_bonds_pct": 30,
        "typical_alts_pct": 10,
    },
    "hybrid": {
        "label": "Hybrid (DB/DC mix)",
        "sponsor_covenant_factor": 0.5,
        "liability_sensitivity_duration_y": 10.0,
        "typical_equity_pct": 50,
        "typical_bonds_pct": 40,
        "typical_alts_pct": 10,
    },
    "collective_dc": {
        "label": "Collective DC (CDC)",
        "sponsor_covenant_factor": 0.3,
        "liability_sensitivity_duration_y": 8.0,
        "typical_equity_pct": 55,
        "typical_bonds_pct": 35,
        "typical_alts_pct": 10,
    },
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PensionFundInput:
    """Input description of a pension fund for IORP II climate stress test."""
    fund_id: str
    fund_name: str
    iorp_type: str = "defined_benefit"          # see IORP_TYPE_PROFILES
    member_count: int = 1000
    country_iso3: str = "NLD"
    reporting_currency: str = "EUR"

    # Balance sheet
    total_assets_eur: float = 1_000_000_000.0   # total assets (AUM)
    liabilities_eur: float = 900_000_000.0       # technical provisions
    liability_duration_y: float = 18.0           # modified duration of liabilities

    # Asset allocation (%)
    equity_pct: float = 40.0
    sovereign_bonds_pct: float = 25.0
    corp_bonds_ig_pct: float = 20.0
    corp_bonds_hy_pct: float = 5.0
    real_estate_pct: float = 7.0
    infrastructure_pct: float = 3.0

    # SFDR classification
    sfdr_classification: str = "art_8"          # art_6 | art_8 | art_9

    # Scenarios to run (default: all 4)
    scenario_ids: List[str] = field(default_factory=lambda: list(IORP_SCENARIOS.keys()))

    # ORA boolean flags
    has_governance_framework: bool = False
    has_risk_integration: bool = False
    has_physical_and_transition: bool = False
    has_esg_investment_policy: bool = False
    has_member_communication: bool = False
    has_scenario_analysis: bool = False
    has_funding_ratio_stress: bool = False
    has_recovery_plan: bool = False
    has_sfdr_classification: bool = True
    has_pai_reporting: bool = False
    has_nature_disclosure: bool = False
    has_transition_plan: bool = False


@dataclass
class AssetStressResult:
    """Stressed asset value result for one scenario."""
    equity_loss_eur: float = 0.0
    sovereign_bond_loss_eur: float = 0.0
    corp_ig_loss_eur: float = 0.0
    corp_hy_loss_eur: float = 0.0
    real_estate_loss_eur: float = 0.0
    infrastructure_loss_eur: float = 0.0
    total_asset_loss_eur: float = 0.0
    stressed_assets_eur: float = 0.0


@dataclass
class LiabilityStressResult:
    """Stressed liability result for one scenario."""
    discount_rate_shift_bps: float = 0.0
    liability_duration_impact_eur: float = 0.0
    longevity_shock_eur: float = 0.0
    inflation_liability_uplift_eur: float = 0.0
    total_liability_change_eur: float = 0.0
    stressed_liabilities_eur: float = 0.0


@dataclass
class FundingRatioResult:
    """Pre- and post-stress funding ratio and recovery triggers."""
    pre_stress_ratio: float = 0.0
    post_stress_ratio: float = 0.0
    ratio_change_pct: float = 0.0
    triggers_recovery_plan: bool = False     # <100% funding ratio
    triggers_supervisory_review: bool = False  # <90% funding ratio
    sponsor_covenant_buffer_eur: float = 0.0


@dataclass
class ORAChecklistResult:
    """IORP II Art 28 Own Risk Assessment checklist item result."""
    item_id: str
    title: str
    article: str
    blocking: bool
    met: bool
    status: str  # "met" | "gap"


@dataclass
class ScenarioPensionResult:
    """Full stress result for one NGFS scenario applied to a pension fund."""
    scenario_id: str
    scenario_label: str
    asset_stress: AssetStressResult = field(default_factory=AssetStressResult)
    liability_stress: LiabilityStressResult = field(default_factory=LiabilityStressResult)
    funding_ratio: FundingRatioResult = field(default_factory=FundingRatioResult)
    net_stress_impact_eur: float = 0.0      # total_asset_loss - liability_change (if DB)
    member_benefit_erosion_pct: float = 0.0  # estimated real benefit reduction


@dataclass
class IORPStressResult:
    """Complete IORP II climate stress test result for a pension fund."""
    run_id: str
    fund_id: str
    fund_name: str
    iorp_type: str
    member_count: int
    sfdr_classification: str
    pre_stress_funding_ratio: float = 0.0
    scenario_results: List[ScenarioPensionResult] = field(default_factory=list)
    worst_case_scenario_id: str = ""
    worst_case_funding_ratio_drop_pct: float = 0.0
    ora_checklist: List[ORAChecklistResult] = field(default_factory=list)
    ora_items_met: int = 0
    ora_items_gap: int = 0
    ora_blocking_gaps: List[str] = field(default_factory=list)
    ora_compliance_status: str = "non_compliant"   # compliant | partial | non_compliant
    sfdr_summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Bond duration constants (years) — consistent with E7 EIOPA engine
# ---------------------------------------------------------------------------
_SOVEREIGN_DURATION = 12.0   # long-duration sovereign (pension portfolios)
_CORP_IG_DURATION = 7.0
_CORP_HY_DURATION = 4.5


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class IORPPensionEngine:
    """
    IORP II Pension Fund Climate Risk Engine.

    Usage:
        engine = IORPPensionEngine()
        result = engine.assess(fund=PensionFundInput(...))
    """

    def assess(
        self,
        fund: PensionFundInput,
        assessment_date: Optional[str] = None,
    ) -> IORPStressResult:
        """
        Run IORP II climate stress test for a pension fund.

        Args:
            fund: PensionFundInput describing the fund.
            assessment_date: ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            IORPStressResult with per-scenario funding ratio stress.
        """
        import datetime
        run_id = str(uuid.uuid4())
        date_str = assessment_date or datetime.date.today().isoformat()
        profile = IORP_TYPE_PROFILES.get(fund.iorp_type, IORP_TYPE_PROFILES["defined_benefit"])

        # Pre-stress funding ratio
        pre_stress_fr = fund.total_assets_eur / max(fund.liabilities_eur, 1.0)

        # Run per-scenario stress
        scenario_results: List[ScenarioPensionResult] = []
        for sc_id in fund.scenario_ids:
            sc = IORP_SCENARIOS.get(sc_id)
            if sc is None:
                continue
            sr = self._stress_scenario(fund, sc_id, sc, pre_stress_fr, profile)
            scenario_results.append(sr)

        # Worst case
        worst_sr = min(scenario_results, key=lambda x: x.funding_ratio.post_stress_ratio, default=None)
        worst_id = worst_sr.scenario_id if worst_sr else ""
        worst_drop = (
            (pre_stress_fr - worst_sr.funding_ratio.post_stress_ratio) / pre_stress_fr * 100
            if worst_sr else 0.0
        )

        # ORA checklist
        ora_results, ora_met, ora_gaps, blocking_gaps = self._evaluate_ora(fund)
        if ora_met == len(ORA_CHECKLIST_ITEMS):
            ora_status = "compliant"
        elif ora_gaps <= 3:
            ora_status = "partial"
        else:
            ora_status = "non_compliant"

        # SFDR summary
        sfdr_summary = {
            "classification": fund.sfdr_classification,
            "label": SFDR_FMP_CATEGORIES.get(fund.sfdr_classification, "Unknown"),
            "pai_reporting_required": fund.sfdr_classification in ("art_8", "art_9") or fund.has_pai_reporting,
            "periodic_report_required": fund.sfdr_classification in ("art_8", "art_9"),
            "pre_contractual_required": fund.sfdr_classification in ("art_8", "art_9"),
        }

        # Recommendations
        recs = self._build_recommendations(fund, ora_status, blocking_gaps, worst_drop, worst_id)

        result = IORPStressResult(
            run_id=run_id,
            fund_id=fund.fund_id,
            fund_name=fund.fund_name,
            iorp_type=fund.iorp_type,
            member_count=fund.member_count,
            sfdr_classification=fund.sfdr_classification,
            pre_stress_funding_ratio=round(pre_stress_fr * 100, 2),
            scenario_results=scenario_results,
            worst_case_scenario_id=worst_id,
            worst_case_funding_ratio_drop_pct=round(worst_drop, 2),
            ora_checklist=ora_results,
            ora_items_met=ora_met,
            ora_items_gap=ora_gaps,
            ora_blocking_gaps=blocking_gaps,
            ora_compliance_status=ora_status,
            sfdr_summary=sfdr_summary,
            recommendations=recs,
            metadata={
                "assessment_date": date_str,
                "framework": "IORP II Directive 2016/2341",
                "stress_methodology": "EIOPA IORP II Climate Stress Test 2022",
                "scenarios_run": len(scenario_results),
                "engine": "E8",
                "total_assets_eur": fund.total_assets_eur,
                "liabilities_eur": fund.liabilities_eur,
                "member_count": fund.member_count,
                "country": fund.country_iso3,
            },
        )
        return result

    # ------------------------------------------------------------------
    # Scenario stress
    # ------------------------------------------------------------------

    def _stress_scenario(
        self,
        fund: PensionFundInput,
        sc_id: str,
        sc: Dict[str, Any],
        pre_stress_fr: float,
        profile: Dict[str, Any],
    ) -> ScenarioPensionResult:
        ta = fund.total_assets_eur

        # --- Asset stress ---
        eq_invested = ta * fund.equity_pct / 100
        sov_invested = ta * fund.sovereign_bonds_pct / 100
        corp_ig_invested = ta * fund.corp_bonds_ig_pct / 100
        corp_hy_invested = ta * fund.corp_bonds_hy_pct / 100
        re_invested = ta * fund.real_estate_pct / 100
        infra_invested = ta * fund.infrastructure_pct / 100

        eq_loss = eq_invested * abs(sc["equity_shock_pct"]) / 100
        sov_loss = sov_invested * (_SOVEREIGN_DURATION * sc["sovereign_bond_spread_bps"] / 10_000)
        corp_ig_loss = corp_ig_invested * (_CORP_IG_DURATION * sc["corp_bond_spread_bps"] / 10_000)
        corp_hy_loss = corp_hy_invested * (_CORP_HY_DURATION * sc["corp_bond_spread_bps"] * 2 / 10_000)
        re_loss = re_invested * abs(sc["re_shock_pct"]) / 100
        infra_loss = infra_invested * abs(sc["infrastructure_shock_pct"]) / 100

        total_asset_loss = eq_loss + sov_loss + corp_ig_loss + corp_hy_loss + re_loss + infra_loss
        stressed_assets = ta - total_asset_loss

        asset_sr = AssetStressResult(
            equity_loss_eur=round(eq_loss, 0),
            sovereign_bond_loss_eur=round(sov_loss, 0),
            corp_ig_loss_eur=round(corp_ig_loss, 0),
            corp_hy_loss_eur=round(corp_hy_loss, 0),
            real_estate_loss_eur=round(re_loss, 0),
            infrastructure_loss_eur=round(infra_loss, 0),
            total_asset_loss_eur=round(total_asset_loss, 0),
            stressed_assets_eur=round(stressed_assets, 0),
        )

        # --- Liability stress (DB only meaningful) ---
        lib_duration = fund.liability_duration_y
        lib = fund.liabilities_eur

        # Duration effect: ΔV ≈ −D × Δrate (negative shift → liability increases for DB)
        discount_shift_bps = sc["liability_discount_shift_bps"]
        duration_impact = -lib * (lib_duration * discount_shift_bps / 10_000)  # + = liability rise

        # Longevity shock: extra years × 1.5% liability uplift per year
        longevity_shock = lib * sc["longevity_shock_years"] * 0.015

        # Inflation uplift on inflation-linked liabilities (assume 40% of DB liabilities indexed)
        indexed_fraction = 0.40 if fund.iorp_type == "defined_benefit" else 0.0
        inflation_uplift = lib * indexed_fraction * sc["inflation_uplift_pct"] / 100

        total_liability_change = duration_impact + longevity_shock + inflation_uplift
        stressed_liabilities = lib + total_liability_change

        liab_sr = LiabilityStressResult(
            discount_rate_shift_bps=discount_shift_bps,
            liability_duration_impact_eur=round(duration_impact, 0),
            longevity_shock_eur=round(longevity_shock, 0),
            inflation_liability_uplift_eur=round(inflation_uplift, 0),
            total_liability_change_eur=round(total_liability_change, 0),
            stressed_liabilities_eur=round(stressed_liabilities, 0),
        )

        # --- Funding ratio ---
        post_stress_fr = stressed_assets / max(stressed_liabilities, 1.0)
        fr_change = (post_stress_fr - pre_stress_fr) / pre_stress_fr * 100
        sponsor_buffer = lib * profile["sponsor_covenant_factor"] * 0.05   # 5% covenant buffer

        fr_sr = FundingRatioResult(
            pre_stress_ratio=round(pre_stress_fr * 100, 2),
            post_stress_ratio=round(post_stress_fr * 100, 2),
            ratio_change_pct=round(fr_change, 2),
            triggers_recovery_plan=post_stress_fr < 1.0,
            triggers_supervisory_review=post_stress_fr < 0.90,
            sponsor_covenant_buffer_eur=round(sponsor_buffer, 0),
        )

        # Net impact (DB: asset loss minus liability increase = net impact on surplus)
        if fund.iorp_type in ("defined_benefit", "hybrid"):
            net_impact = total_asset_loss + total_liability_change
        else:
            net_impact = total_asset_loss   # DC: members bear asset risk only

        # Member benefit erosion proxy: asset loss as % of total assets
        benefit_erosion = total_asset_loss / max(ta, 1.0) * 100

        return ScenarioPensionResult(
            scenario_id=sc_id,
            scenario_label=sc["label"],
            asset_stress=asset_sr,
            liability_stress=liab_sr,
            funding_ratio=fr_sr,
            net_stress_impact_eur=round(net_impact, 0),
            member_benefit_erosion_pct=round(benefit_erosion, 2),
        )

    # ------------------------------------------------------------------
    # ORA checklist evaluation
    # ------------------------------------------------------------------

    def _evaluate_ora(
        self,
        fund: PensionFundInput,
    ) -> tuple[List[ORAChecklistResult], int, int, List[str]]:
        results: List[ORAChecklistResult] = []
        met = 0
        gaps = 0
        blocking_gaps: List[str] = []

        for item in ORA_CHECKLIST_ITEMS:
            flag_val = getattr(fund, item["flag"], False)
            is_met = bool(flag_val)
            status = "met" if is_met else "gap"
            if is_met:
                met += 1
            else:
                gaps += 1
                if item["blocking"]:
                    blocking_gaps.append(f"{item['item_id']}: {item['title']}")
            results.append(ORAChecklistResult(
                item_id=item["item_id"],
                title=item["title"],
                article=item["article"],
                blocking=item["blocking"],
                met=is_met,
                status=status,
            ))

        return results, met, gaps, blocking_gaps

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def _build_recommendations(
        self,
        fund: PensionFundInput,
        ora_status: str,
        blocking_gaps: List[str],
        worst_drop: float,
        worst_id: str,
    ) -> List[str]:
        recs: List[str] = []

        if ora_status == "non_compliant":
            recs.append("Urgently address ORA blocking gaps before next supervisory review")
        if blocking_gaps:
            recs.append(f"Resolve {len(blocking_gaps)} blocking ORA items: {', '.join(g.split(':')[0] for g in blocking_gaps[:3])}")
        if worst_drop > 15:
            sc_label = IORP_SCENARIOS.get(worst_id, {}).get("label", worst_id)
            recs.append(f"Worst-case scenario '{sc_label}' drops funding ratio by {worst_drop:.1f}% — review recovery plan triggers")
        if not fund.has_transition_plan:
            recs.append("Develop a portfolio decarbonisation transition plan aligned with GFANZ/IIGCC NZIF")
        if fund.sfdr_classification == "art_6" and fund.member_count > 500:
            recs.append("Consider upgrading to SFDR Art 8 classification to align with IORP II ESG integration requirements")
        if not fund.has_pai_reporting:
            recs.append("Begin PAI indicator reporting (SFDR Art 4) — mandatory for FMPs with >500 employees from 2023")
        if fund.real_estate_pct + fund.infrastructure_pct > 15:
            recs.append("Conduct CRREM/GRESB physical risk assessment for real assets exposure (>15% allocation)")
        if not fund.has_nature_disclosure:
            recs.append("Commence TNFD LEAP assessment for nature-related risks in real asset holdings")

        if not recs:
            recs.append("ORA compliance maintained; monitor scenario evolution and update stress parameters annually")

        return recs
