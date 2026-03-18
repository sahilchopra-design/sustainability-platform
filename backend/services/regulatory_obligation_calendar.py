"""
Regulatory Obligation Calendar (E3)
======================================
Tracks filing deadlines and compliance milestones across all regulatory
frameworks supported by the platform.  Provides deadline alerts, urgency
scoring, and per-entity obligation filtering.

Frameworks covered (13):
  CSRD / ESRS        — EFRAG / EU 2022/2464
  SFDR               — EU 2019/2088 + RTS 2022/1288
  EU Taxonomy        — EU 2020/852 (Art. 8 KPIs)
  ETS Phase 4        — EU ETS Directive 2003/87/EC (amended)
  ETS2               — Directive 2023/959 (buildings + transport)
  CBAM               — EU 2023/956
  ISSB S1/S2         — IFRS Foundation (effective Jan 2024)
  SEC Climate        — Release 33-11275 (RESCINDED March 2025)
  BRSR               — SEBI (India)
  TCFD               — voluntary (FSB framework, adopted in IFRS S2)
  EUDR               — EU 2023/1115
  CSDDD              — EU 2024/1760
  EIOPA ORSA Climate — EIOPA Opinion (Insurers)

Each obligation has:
  - deadline (ISO date)
  - entity_scope (who it applies to: e.g. "large_EU_company", "UCITS_fund")
  - urgency (critical / high / medium / low)
  - auto_computed_urgency_days (days until deadline from today)
  - related_platform_modules (which platform modules generate the evidence)
  - penalty_risk (max fine / consequence if missed)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Deadline Definitions
# ---------------------------------------------------------------------------

@dataclass
class RegulatoryObligation:
    """A single filing deadline or compliance milestone."""
    obligation_id: str
    framework: str
    short_name: str
    description: str
    deadline: str                     # ISO date string "YYYY-MM-DD"
    recurrence: str                   # "annual" | "quarterly" | "one_time" | "ongoing"
    entity_scope: List[str]           # who it applies to
    jurisdiction: str                 # "EU" | "Global" | "IN" | "US" | "AU"
    urgency: str                      # critical / high / medium / low (static label)
    penalty_risk: str                 # short description of non-compliance consequence
    platform_modules: List[str]       # modules that generate required evidence
    regulatory_reference: str         # article / paragraph citation
    notes: str = ""
    is_rescinded: bool = False        # True for SEC rule


# All obligations keyed by obligation_id
OBLIGATIONS: Dict[str, RegulatoryObligation] = {}

def _reg(o: RegulatoryObligation):
    OBLIGATIONS[o.obligation_id] = o
    return o


# ── CSRD / ESRS ─────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="CSRD-001",
    framework="CSRD",
    short_name="CSRD FY2024 First Report — Large PIEs",
    description=(
        "Large public-interest entities (PIEs) with >500 employees must publish "
        "their first CSRD sustainability report for FY2024 alongside their financial "
        "statements (ESRS 2 + mandatory topical standards E1, G1 at minimum)."
    ),
    deadline="2025-01-31",
    recurrence="annual",
    entity_scope=["large_PIE_EU", "listed_company_EU_500plus"],
    jurisdiction="EU",
    urgency="critical",
    penalty_risk="National competent authority enforcement; potential delisting risk. "
                 "ESMA Guidelines on enforcement apply.",
    platform_modules=["csrd_auto_populate", "xbrl_export_engine", "regulatory_report_compiler"],
    regulatory_reference="CSRD Art. 19a, ESRS Set 1 (Commission Delegated Reg 2023/2772)",
))

_reg(RegulatoryObligation(
    obligation_id="CSRD-002",
    framework="CSRD",
    short_name="CSRD FY2025 — Large Non-PIEs + Listed SMEs",
    description=(
        "Large non-listed companies (>250 employees OR >EUR 50m turnover OR >EUR 25m "
        "balance sheet — 2 of 3 criteria) and listed SMEs must first report for FY2025."
    ),
    deadline="2026-01-31",
    recurrence="annual",
    entity_scope=["large_EU_non_PIE", "listed_SME_EU"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="Same as CSRD-001. Member state civil liability under CSRD Art. 22.",
    platform_modules=["csrd_auto_populate", "xbrl_export_engine", "csrd_extractor"],
    regulatory_reference="CSRD Art. 5(1)(b), Commission Delegated Reg 2023/2772",
))

_reg(RegulatoryObligation(
    obligation_id="CSRD-003",
    framework="CSRD",
    short_name="CSRD FY2028 — Non-EU Companies (Art. 40a)",
    description=(
        "Non-EU parent companies with EU turnover >EUR 150m must publish a group "
        "sustainability report (or equivalent) for FY2028."
    ),
    deadline="2029-01-31",
    recurrence="annual",
    entity_scope=["non_EU_parent_150m_EU_turnover"],
    jurisdiction="EU",
    urgency="medium",
    penalty_risk="Market access sanctions; reputational risk with EU counterparties.",
    platform_modules=["csrd_auto_populate", "regulatory_report_compiler"],
    regulatory_reference="CSRD Art. 40a (as amended by Omnibus Dir — monitor for changes)",
    notes="Omnibus I Directive (COM/2025/80) may defer to FY2030 — monitor EFRAG guidance.",
))

_reg(RegulatoryObligation(
    obligation_id="CSRD-004",
    framework="CSRD",
    short_name="ESRS Limited Assurance — Year 1",
    description=(
        "External limited assurance on CSRD sustainability reports required from "
        "the same year as the first CSRD report obligation."
    ),
    deadline="2025-12-31",
    recurrence="annual",
    entity_scope=["large_PIE_EU"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="Defective assurance voids report compliance; regulatory enforcement.",
    platform_modules=["csrd_auto_populate", "xbrl_export_engine"],
    regulatory_reference="CSRD Art. 26a — ISSA 5000 / EU Sustainability Assurance Standard",
))

# ── SFDR ─────────────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="SFDR-001",
    framework="SFDR",
    short_name="SFDR PAI Statement — Annual (30 June)",
    description=(
        "Financial market participants (FMPs) with >500 employees must publish their "
        "annual Principal Adverse Impact (PAI) statement by 30 June for the prior year."
    ),
    deadline="2025-06-30",
    recurrence="annual",
    entity_scope=["FMP_EU_500plus", "AIFM_EU", "UCITS_ManCo_EU"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="ESAs supervisory powers; national regulator enforcement action.",
    platform_modules=["sfdr_pai_engine", "pcaf_waci_engine", "regulatory_report_compiler"],
    regulatory_reference="SFDR Art. 4(1)(a); RTS Annex I (Commission Delegated Reg 2022/1288)",
))

_reg(RegulatoryObligation(
    obligation_id="SFDR-002",
    framework="SFDR",
    short_name="SFDR Article 8/9 Periodic Reports",
    description=(
        "Art. 8 (ESG characteristics) and Art. 9 (sustainable investment) funds must "
        "include sustainability disclosures in annual and semi-annual periodic reports."
    ),
    deadline="2025-12-31",
    recurrence="annual",
    entity_scope=["UCITS_Art8", "UCITS_Art9", "AIF_Art8", "AIF_Art9"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="Mis-selling / greenwashing risk; ESMA supervisory convergence actions.",
    platform_modules=["sfdr_pai_engine", "regulatory_report_compiler"],
    regulatory_reference="SFDR Art. 11; RTS Annexes III, IV, V (2022/1288)",
))

_reg(RegulatoryObligation(
    obligation_id="SFDR-003",
    framework="SFDR",
    short_name="SFDR Product Classification Review",
    description=(
        "ESMA taxonomy review of Art. 8/9 fund classification — anticipated changes "
        "to product categories following SFDR review consultation (2023/2024)."
    ),
    deadline="2026-06-30",
    recurrence="one_time",
    entity_scope=["FMP_EU"],
    jurisdiction="EU",
    urgency="medium",
    penalty_risk="Mandatory re-classification; product prospectus amendments.",
    platform_modules=["sfdr_pai_engine", "regulatory_report_compiler"],
    regulatory_reference="ESMA SFDR Review CP (March 2024) — awaiting final Level 1 revision",
    notes="Monitor European Commission SFDR targeted review — timeline may shift.",
))

# ── EU Taxonomy ───────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="TAXONOMY-001",
    framework="EU Taxonomy",
    short_name="EU Taxonomy Art. 8 KPI Disclosure — Full",
    description=(
        "Large EU companies subject to CSRD must disclose full EU Taxonomy KPIs: "
        "turnover, capex, and opex aligned to taxonomy activities. "
        "FY2023 was first year for turnover + capex; FY2024 adds opex."
    ),
    deadline="2025-06-30",
    recurrence="annual",
    entity_scope=["large_PIE_EU", "large_EU_non_PIE"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="Greenwashing enforcement; ESMA/national NCA action.",
    platform_modules=["eu_taxonomy_engine", "regulatory_report_compiler"],
    regulatory_reference="EU Taxonomy Reg 2020/852 Art. 8; Commission Delegated Reg 2021/2178",
))

_reg(RegulatoryObligation(
    obligation_id="TAXONOMY-002",
    framework="EU Taxonomy",
    short_name="Bank GAR/BTAR Pillar 3 Disclosure",
    description=(
        "Credit institutions must disclose Green Asset Ratio (GAR) and Banking Book "
        "Taxonomy Alignment Ratio (BTAR) in Pillar 3 reports annually."
    ),
    deadline="2025-12-31",
    recurrence="annual",
    entity_scope=["credit_institution_EU", "investment_firm_EU"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="EBA supervisory review; Pillar 2 capital add-on risk.",
    platform_modules=["ecl_gar_pillar3_orchestrator", "regulatory_report_compiler"],
    regulatory_reference="CRR Art. 449a; EBA ITS 2022/01 (ESG Pillar 3 disclosures)",
))

# ── EU ETS Phase 4 ────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="ETS-001",
    framework="EU ETS",
    short_name="ETS Annual Emissions Report Submission",
    description=(
        "ETS operators must submit verified annual emissions report to national "
        "competent authority by 31 March each year."
    ),
    deadline="2025-03-31",
    recurrence="annual",
    entity_scope=["EU_ETS_installation_operator"],
    jurisdiction="EU",
    urgency="critical",
    penalty_risk="EUR 100/tCO2e penalty for each unverified tonne; public disclosure of non-compliance.",
    platform_modules=["eu_ets_engine"],
    regulatory_reference="EU ETS Directive 2003/87/EC Art. 14; MRR 601/2012",
))

_reg(RegulatoryObligation(
    obligation_id="ETS-002",
    framework="EU ETS",
    short_name="ETS Allowance Surrender Deadline",
    description=(
        "ETS operators must surrender allowances equal to verified emissions by 30 April."
    ),
    deadline="2025-04-30",
    recurrence="annual",
    entity_scope=["EU_ETS_installation_operator"],
    jurisdiction="EU",
    urgency="critical",
    penalty_risk="EUR 100/tCO2e penalty; name published on national registry.",
    platform_modules=["eu_ets_engine"],
    regulatory_reference="EU ETS Directive Art. 12(2a)",
))

# ── ETS2 ─────────────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="ETS2-001",
    framework="ETS2",
    short_name="ETS2 Monitoring Plan Submission",
    description=(
        "Regulated entities under ETS2 (fuel distributors for buildings + road transport) "
        "must submit a monitoring plan to their competent authority."
    ),
    deadline="2025-01-01",
    recurrence="one_time",
    entity_scope=["ETS2_fuel_distributor_EU"],
    jurisdiction="EU",
    urgency="critical",
    penalty_risk="Exclusion from ETS2 registry; inability to surrender allowances from 2027.",
    platform_modules=["eu_ets_engine"],
    regulatory_reference="Directive 2023/959 Art. 30c §2",
))

_reg(RegulatoryObligation(
    obligation_id="ETS2-002",
    framework="ETS2",
    short_name="ETS2 Registry Registration",
    description="Regulated entities must open an ETS2 registry account before trading begins.",
    deadline="2026-12-31",
    recurrence="one_time",
    entity_scope=["ETS2_fuel_distributor_EU"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="Cannot receive, hold, or surrender ETS2 allowances.",
    platform_modules=["eu_ets_engine"],
    regulatory_reference="Directive 2023/959 Art. 30d",
))

_reg(RegulatoryObligation(
    obligation_id="ETS2-003",
    framework="ETS2",
    short_name="ETS2 First Surrender Deadline",
    description="First ETS2 allowance surrender for emissions in 2027.",
    deadline="2028-05-31",
    recurrence="annual",
    entity_scope=["ETS2_fuel_distributor_EU"],
    jurisdiction="EU",
    urgency="medium",
    penalty_risk="EUR 100/tCO2 + public disclosure; repeat offenders face licence revocation.",
    platform_modules=["eu_ets_engine"],
    regulatory_reference="Directive 2023/959 Art. 30d §4",
))

# ── CBAM ─────────────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="CBAM-001",
    framework="CBAM",
    short_name="CBAM Quarterly Embedded Emissions Report",
    description=(
        "CBAM declarants must file quarterly reports on embedded emissions in "
        "imported CBAM goods (steel, cement, aluminium, fertilisers, electricity, hydrogen)."
    ),
    deadline="2025-07-31",
    recurrence="quarterly",
    entity_scope=["EU_CBAM_declarant", "importer_CBAM_goods_EU"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="EUR 10-50/tCO2 penalty; import suspension for repeat non-compliance.",
    platform_modules=["cbam_calculator", "regulatory_report_compiler"],
    regulatory_reference="CBAM Reg 2023/956 Art. 35; Commission Impl. Reg 2023/1773",
))

_reg(RegulatoryObligation(
    obligation_id="CBAM-002",
    framework="CBAM",
    short_name="CBAM Annual Declaration + Certificate Surrender",
    description=(
        "CBAM authorised declarants must submit annual CBAM declaration and surrender "
        "CBAM certificates equal to embedded emissions for the prior calendar year."
    ),
    deadline="2026-05-31",
    recurrence="annual",
    entity_scope=["EU_CBAM_authorised_declarant"],
    jurisdiction="EU",
    urgency="critical",
    penalty_risk="EUR 10-50/tCO2; suspension of authorised declarant status.",
    platform_modules=["cbam_calculator"],
    regulatory_reference="CBAM Reg 2023/956 Art. 6, 22",
    notes="Full CBAM regime starts 2026 (transitional period ends 31 Dec 2025).",
))

# ── ISSB ─────────────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="ISSB-001",
    framework="ISSB",
    short_name="IFRS S1/S2 Mandatory Reporting — Australia (AASB)",
    description=(
        "Australian entities (large listed) must report under IFRS S1/S2 as adopted by "
        "AASB from FY2025 under Australian Sustainability Reporting Standards (ASRS)."
    ),
    deadline="2026-03-31",
    recurrence="annual",
    entity_scope=["ASX_listed_large_AU", "registered_scheme_AU"],
    jurisdiction="AU",
    urgency="high",
    penalty_risk="ASIC enforcement; prospectus liability for listed entities.",
    platform_modules=["issb_engine", "regulatory_report_compiler"],
    regulatory_reference="ASRS 1/2 (AASB Jan 2024); Treasury Laws Amendment 2024",
))

_reg(RegulatoryObligation(
    obligation_id="ISSB-002",
    framework="ISSB",
    short_name="IFRS S1/S2 — UK Sustainability Disclosure Standards",
    description=(
        "UK-endorsed SDS (based on ISSB S1/S2) expected mandatory for UK listed "
        "premium segment from FY2026."
    ),
    deadline="2027-03-31",
    recurrence="annual",
    entity_scope=["UK_premium_listed", "UK_large_company"],
    jurisdiction="UK",
    urgency="medium",
    penalty_risk="FCA enforcement; TCFD-equivalent mandatory compliance.",
    platform_modules=["issb_engine", "regulatory_report_compiler"],
    regulatory_reference="FRC UK SDS consultation (2024); BEIS endorsement process",
    notes="Timeline subject to UK government SDS endorsement announcement.",
))

# ── SEC Climate (rescinded) ───────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="SEC-001",
    framework="SEC Climate",
    short_name="SEC Climate Disclosure Rule — RESCINDED",
    description=(
        "The SEC's final climate disclosure rule (Release 33-11275, March 2024) was "
        "voluntarily stayed in April 2024 and formally rescinded on 27 March 2025. "
        "No US company has a current SEC climate disclosure obligation under this rule."
    ),
    deadline="2026-01-01",
    recurrence="one_time",
    entity_scope=["US_public_company"],
    jurisdiction="US",
    urgency="low",
    penalty_risk="NONE — rule rescinded. Voluntary TCFD/ISSB S2 alignment recommended.",
    platform_modules=["sec_climate_engine"],
    regulatory_reference="SEC Release 33-11275 (adopted 2024-03-06, rescinded 2025-03-27)",
    is_rescinded=True,
    notes="Maintain voluntary TCFD/ISSB S2 alignment. Monitor for re-proposal.",
))

# ── BRSR ─────────────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="BRSR-001",
    framework="BRSR",
    short_name="BRSR Full Disclosure — Top 1000 Listed Entities",
    description="Top 1000 NSE/BSE listed entities must file BRSR with annual report.",
    deadline="2025-09-30",
    recurrence="annual",
    entity_scope=["IN_listed_top1000_NSE_BSE"],
    jurisdiction="IN",
    urgency="high",
    penalty_risk="SEBI enforcement action; stock exchange compliance notices.",
    platform_modules=["regulatory_report_compiler"],
    regulatory_reference="SEBI Circular SEBI/HO/CFD/CMD-2/P/CIR/2023/18",
))

_reg(RegulatoryObligation(
    obligation_id="BRSR-002",
    framework="BRSR",
    short_name="BRSR Core — Reasonable Assurance (Top 150)",
    description=(
        "Top 150 NSE/BSE listed entities must obtain reasonable assurance on "
        "BRSR Core (9 ESG attributes) from FY2023-24."
    ),
    deadline="2025-09-30",
    recurrence="annual",
    entity_scope=["IN_listed_top150_NSE_BSE"],
    jurisdiction="IN",
    urgency="high",
    penalty_risk="SEBI enforcement; potential suspension of trading in securities.",
    platform_modules=["regulatory_report_compiler"],
    regulatory_reference="SEBI BRSR Core Circular (Annexure I), FY2023-24 mandatory",
))

# ── EUDR ─────────────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="EUDR-001",
    framework="EUDR",
    short_name="EUDR Due Diligence Statement (DDS) — Large Operators",
    description=(
        "Large operators and traders placing deforestation-linked commodities "
        "(cattle, cocoa, coffee, palm oil, soy, wood, rubber) on the EU market "
        "must submit a Due Diligence Statement before market placement."
    ),
    deadline="2025-12-30",
    recurrence="ongoing",
    entity_scope=["EU_operator_EUDR_commodity", "EU_trader_EUDR"],
    jurisdiction="EU",
    urgency="critical",
    penalty_risk=(
        "Fine ≥4% of annual EU turnover; market confiscation; exclusion from "
        "public procurement. Art. 25 enforcement."
    ),
    platform_modules=["eudr_engine", "supply_chain_workflow_engine"],
    regulatory_reference="EUDR Reg 2023/1115 Art. 4, 9; Commission Implementing Reg 2023/1 (DDS format)",
    notes="Deferred to Dec 2025 for large operators (was Dec 2024). SMEs: Jun 2026.",
))

_reg(RegulatoryObligation(
    obligation_id="EUDR-002",
    framework="EUDR",
    short_name="EUDR DDS — SMEs (Small Operators/Traders)",
    description="SME operators and traders: same DDS obligation as EUDR-001 but deferred timeline.",
    deadline="2026-06-30",
    recurrence="ongoing",
    entity_scope=["EU_SME_operator_EUDR"],
    jurisdiction="EU",
    urgency="medium",
    penalty_risk="Same as EUDR-001 (proportionate to size).",
    platform_modules=["eudr_engine"],
    regulatory_reference="EUDR Reg 2023/1115 Art. 38 (deferral instrument)",
))

# ── CSDDD ─────────────────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="CSDDD-001",
    framework="CSDDD",
    short_name="CSDDD Group 1 — Large EU Companies (>1000 employees, >EUR 450m)",
    description=(
        "EU companies with >1000 employees AND >EUR 450m turnover must comply with "
        "CSDDD due diligence obligations from 26 July 2027."
    ),
    deadline="2027-07-26",
    recurrence="ongoing",
    entity_scope=["EU_company_group1_CSDDD"],
    jurisdiction="EU",
    urgency="medium",
    penalty_risk="Fine up to 5% of worldwide turnover (Art. 30); civil liability (Art. 29).",
    platform_modules=["csddd_engine", "supply_chain_workflow_engine"],
    regulatory_reference="CSDDD 2024/1760 Art. 2, 37(1) — phased timeline",
))

_reg(RegulatoryObligation(
    obligation_id="CSDDD-002",
    framework="CSDDD",
    short_name="CSDDD Climate Transition Plan (Art. 22)",
    description=(
        "CSDDD entities must adopt and implement a climate transition plan aligned "
        "with the Paris Agreement (1.5°C pathway), updated annually."
    ),
    deadline="2027-07-26",
    recurrence="annual",
    entity_scope=["EU_company_group1_CSDDD"],
    jurisdiction="EU",
    urgency="medium",
    penalty_risk="Enforcement as part of overall CSDDD DD obligation (5% turnover max).",
    platform_modules=["csddd_engine", "csrd_auto_populate"],
    regulatory_reference="CSDDD 2024/1760 Art. 22",
))

# ── EIOPA ORSA Climate ────────────────────────────────────────────────────────

_reg(RegulatoryObligation(
    obligation_id="EIOPA-001",
    framework="EIOPA ORSA",
    short_name="Solvency II ORSA Climate Scenario Analysis",
    description=(
        "Insurers must integrate climate risk scenarios into their ORSA (Own Risk and "
        "Solvency Assessment), including physical and transition risk stress tests."
    ),
    deadline="2025-12-31",
    recurrence="annual",
    entity_scope=["EU_insurer_solvency_II", "EU_reinsurer"],
    jurisdiction="EU",
    urgency="high",
    penalty_risk="EIOPA/NCA supervisory review; Pillar 2 solvency capital add-on.",
    platform_modules=["insurance_engine", "scenario_analysis_engine"],
    regulatory_reference=(
        "EIOPA Opinion on Sustainability (EIOPA-BoS-21-127); "
        "Solvency II Delegated Reg 2015/35 Art. 262"
    ),
))


# ---------------------------------------------------------------------------
# Calendar Service
# ---------------------------------------------------------------------------

@dataclass
class ObligationAlert:
    """A deadline alert with urgency scoring."""
    obligation: RegulatoryObligation
    days_until: int
    computed_urgency: str   # overrides static urgency based on days_until
    alert_message: str


class RegulatoryObligationCalendar:
    """
    Queries and filters regulatory obligations with deadline alerts.

    Usage:
        cal = RegulatoryObligationCalendar()
        alerts = cal.get_upcoming_alerts(days_ahead=90)
        obligations = cal.filter(frameworks=["CSRD", "SFDR"], jurisdictions=["EU"])
    """

    def __init__(self, reference_date: Optional[date] = None):
        self._today = reference_date or date.today()

    # ── Queries ──────────────────────────────────────────────────────────────

    def get_all(self, include_rescinded: bool = False) -> List[RegulatoryObligation]:
        obs = list(OBLIGATIONS.values())
        if not include_rescinded:
            obs = [o for o in obs if not o.is_rescinded]
        return sorted(obs, key=lambda o: o.deadline)

    def filter(
        self,
        frameworks: Optional[List[str]] = None,
        jurisdictions: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        include_rescinded: bool = False,
    ) -> List[RegulatoryObligation]:
        obs = self.get_all(include_rescinded=include_rescinded)
        if frameworks:
            fw_upper = {f.upper() for f in frameworks}
            obs = [o for o in obs if o.framework.upper() in fw_upper]
        if jurisdictions:
            jur_upper = {j.upper() for j in jurisdictions}
            obs = [o for o in obs if o.jurisdiction.upper() in jur_upper]
        if entity_types:
            et_lower = {e.lower() for e in entity_types}
            obs = [o for o in obs if any(e.lower() in et_lower for e in o.entity_scope)]
        return obs

    def get_upcoming_alerts(
        self,
        days_ahead: int = 90,
        frameworks: Optional[List[str]] = None,
        jurisdictions: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
    ) -> List[ObligationAlert]:
        """Return obligations with deadlines within *days_ahead* days, with urgency scoring."""
        obs = self.filter(
            frameworks=frameworks,
            jurisdictions=jurisdictions,
            entity_types=entity_types,
        )
        alerts: List[ObligationAlert] = []
        for o in obs:
            try:
                dl = date.fromisoformat(o.deadline)
            except ValueError:
                continue
            days_until = (dl - self._today).days
            if days_until < 0 or days_until > days_ahead:
                continue
            computed = self._compute_urgency(days_until)
            msg = self._build_message(o, days_until, computed)
            alerts.append(ObligationAlert(
                obligation=o,
                days_until=days_until,
                computed_urgency=computed,
                alert_message=msg,
            ))
        return sorted(alerts, key=lambda a: a.days_until)

    def get_obligation(self, obligation_id: str) -> Optional[RegulatoryObligation]:
        return OBLIGATIONS.get(obligation_id)

    def get_platform_module_coverage(self) -> Dict[str, List[str]]:
        """Return dict: {module_name: [obligation_ids that depend on it]}."""
        coverage: Dict[str, List[str]] = {}
        for o in OBLIGATIONS.values():
            for mod in o.platform_modules:
                coverage.setdefault(mod, []).append(o.obligation_id)
        return {m: sorted(ids) for m, ids in sorted(coverage.items())}

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of all obligations by framework and urgency."""
        obs = self.get_all(include_rescinded=False)
        by_framework: Dict[str, int] = {}
        by_urgency: Dict[str, int] = {}
        overdue: List[str] = []
        for o in obs:
            by_framework[o.framework] = by_framework.get(o.framework, 0) + 1
            by_urgency[o.urgency] = by_urgency.get(o.urgency, 0) + 1
            try:
                if date.fromisoformat(o.deadline) < self._today:
                    overdue.append(o.obligation_id)
            except ValueError:
                pass
        return {
            "total_obligations": len(obs),
            "rescinded_obligations": sum(1 for o in OBLIGATIONS.values() if o.is_rescinded),
            "by_framework": by_framework,
            "by_urgency": by_urgency,
            "overdue_obligation_ids": overdue,
            "frameworks_covered": sorted(set(o.framework for o in obs)),
            "jurisdictions_covered": sorted(set(o.jurisdiction for o in obs)),
            "reference_date": self._today.isoformat(),
        }

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_urgency(days_until: int) -> str:
        if days_until <= 14:
            return "critical"
        if days_until <= 45:
            return "high"
        if days_until <= 90:
            return "medium"
        return "low"

    @staticmethod
    def _build_message(o: RegulatoryObligation, days_until: int, urgency: str) -> str:
        if days_until == 0:
            timing = "TODAY"
        elif days_until < 0:
            timing = f"OVERDUE by {abs(days_until)} days"
        elif days_until == 1:
            timing = "TOMORROW"
        else:
            timing = f"in {days_until} days"
        return (
            f"[{urgency.upper()}] {o.framework}: {o.short_name} — deadline {o.deadline} ({timing}). "
            f"Penalty: {o.penalty_risk[:80]}..."
        )
