"""
EU Corporate Sustainability Due Diligence Directive (CSDDD)
Directive (EU) 2024/1760
==========================================================

Comprehensive due diligence engine for human rights and environmental
adverse impacts across company value chains.

Key provisions modelled:
- Art 2:  Scope (employee & turnover thresholds, phased timelines)
- Art 6:  Identifying actual & potential adverse impacts
- Art 7:  Preventing potential adverse impacts
- Art 8:  Bringing actual adverse impacts to an end
- Art 9:  Remediation
- Art 10: Meaningful stakeholder engagement
- Art 11: Complaints / grievance mechanism
- Art 14: Contractual cascading
- Art 22: Climate transition plan (Paris-aligned)
- Art 25-26: Director duty of care
- Art 29: Civil liability
- Art 30-33: Supervisory authority & penalties

Cross-framework linkage:
- CSRD ESRS S1 (Own Workforce), S2 (Value Chain Workers)
- EUDR (deforestation commodities)
- UN Guiding Principles on Business and Human Rights
- OECD Guidelines for Multinational Enterprises
- ILO Declaration on Fundamental Principles and Rights at Work
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Reference Data Constants
# ---------------------------------------------------------------------------

# Art 2 — Scope thresholds (phased: Group 1 → Group 2 → Group 3)
SCOPE_THRESHOLDS = {
    "group_1": {
        "applies_from": "2027-07-26",
        "employees_min": 5000,
        "turnover_min_eur": 1_500_000_000,
        "description": "Large EU companies (>5000 employees AND >EUR 1.5bn turnover)",
    },
    "group_2": {
        "applies_from": "2028-07-26",
        "employees_min": 3000,
        "turnover_min_eur": 900_000_000,
        "description": "Medium-large EU companies (>3000 employees AND >EUR 900m turnover)",
    },
    "group_3": {
        "applies_from": "2029-07-26",
        "employees_min": 1000,
        "turnover_min_eur": 450_000_000,
        "description": "Mid-size EU companies (>1000 employees AND >EUR 450m turnover)",
    },
    "non_eu_group_1": {
        "applies_from": "2027-07-26",
        "turnover_in_eu_min_eur": 1_500_000_000,
        "description": "Non-EU companies with >EUR 1.5bn EU-generated turnover",
    },
    "non_eu_group_2": {
        "applies_from": "2028-07-26",
        "turnover_in_eu_min_eur": 900_000_000,
        "description": "Non-EU companies with >EUR 900m EU-generated turnover",
    },
    "non_eu_group_3": {
        "applies_from": "2029-07-26",
        "turnover_in_eu_min_eur": 450_000_000,
        "description": "Non-EU companies with >EUR 450m EU-generated turnover",
    },
}

# Art 3(1) — Adverse impact categories (human rights + environment)
ADVERSE_IMPACT_CATEGORIES = {
    "HR-01": {
        "category": "human_rights",
        "title": "Forced / compulsory labour",
        "instruments": ["ILO C29", "ILO C105"],
        "severity_weight": 1.0,
    },
    "HR-02": {
        "category": "human_rights",
        "title": "Child labour",
        "instruments": ["ILO C138", "ILO C182", "UNCRC Art 32"],
        "severity_weight": 1.0,
    },
    "HR-03": {
        "category": "human_rights",
        "title": "Freedom of association & collective bargaining",
        "instruments": ["ILO C87", "ILO C98"],
        "severity_weight": 0.8,
    },
    "HR-04": {
        "category": "human_rights",
        "title": "Discrimination in employment",
        "instruments": ["ILO C100", "ILO C111"],
        "severity_weight": 0.7,
    },
    "HR-05": {
        "category": "human_rights",
        "title": "Unsafe / unhealthy working conditions",
        "instruments": ["ILO C155", "ILO C187"],
        "severity_weight": 0.9,
    },
    "HR-06": {
        "category": "human_rights",
        "title": "Inadequate living wage",
        "instruments": ["UDHR Art 23", "ICESCR Art 7"],
        "severity_weight": 0.7,
    },
    "HR-07": {
        "category": "human_rights",
        "title": "Land rights & forced eviction",
        "instruments": ["ICESCR Art 11", "ILO C169"],
        "severity_weight": 0.9,
    },
    "HR-08": {
        "category": "human_rights",
        "title": "Indigenous peoples' rights (FPIC)",
        "instruments": ["UNDRIP", "ILO C169"],
        "severity_weight": 0.9,
    },
    "HR-09": {
        "category": "human_rights",
        "title": "Right to privacy & data protection",
        "instruments": ["ICCPR Art 17", "GDPR"],
        "severity_weight": 0.6,
    },
    "HR-10": {
        "category": "human_rights",
        "title": "Conflict-affected & high-risk areas (CAHRAs)",
        "instruments": ["EU Conflict Minerals Reg 2017/821"],
        "severity_weight": 0.9,
    },
    "ENV-01": {
        "category": "environment",
        "title": "GHG emissions & climate change",
        "instruments": ["Paris Agreement", "EU Climate Law"],
        "severity_weight": 0.9,
    },
    "ENV-02": {
        "category": "environment",
        "title": "Deforestation & ecosystem conversion",
        "instruments": ["EUDR 2023/1115", "CBD COP-15"],
        "severity_weight": 1.0,
    },
    "ENV-03": {
        "category": "environment",
        "title": "Biodiversity loss",
        "instruments": ["CBD", "Ramsar", "CITES"],
        "severity_weight": 0.9,
    },
    "ENV-04": {
        "category": "environment",
        "title": "Water pollution & depletion",
        "instruments": ["Basel Convention", "MARPOL", "WFD"],
        "severity_weight": 0.8,
    },
    "ENV-05": {
        "category": "environment",
        "title": "Air pollution (SOx, NOx, PM)",
        "instruments": ["Gothenburg Protocol", "Minamata Convention"],
        "severity_weight": 0.7,
    },
    "ENV-06": {
        "category": "environment",
        "title": "Soil contamination & degradation",
        "instruments": ["Stockholm Convention (POPs)"],
        "severity_weight": 0.7,
    },
    "ENV-07": {
        "category": "environment",
        "title": "Hazardous waste & chemicals",
        "instruments": ["Basel Convention", "Rotterdam Convention"],
        "severity_weight": 0.8,
    },
    "ENV-08": {
        "category": "environment",
        "title": "Marine & coastal ecosystem damage",
        "instruments": ["UNCLOS", "MARPOL"],
        "severity_weight": 0.8,
    },
}

# Art 22 — Climate Transition Plan requirements
CLIMATE_TRANSITION_PLAN_REQUIREMENTS = [
    {"id": "CTP-01", "requirement": "Paris-aligned GHG reduction targets (1.5C pathway)",
     "article": "Art 22(1)"},
    {"id": "CTP-02", "requirement": "Time-bound implementation actions",
     "article": "Art 22(1)"},
    {"id": "CTP-03", "requirement": "Description of decarbonisation levers",
     "article": "Art 22(1)"},
    {"id": "CTP-04", "requirement": "Key investments & financial planning",
     "article": "Art 22(1)"},
    {"id": "CTP-05", "requirement": "Role of offsets (limited / supplementary only)",
     "article": "Art 22(1)"},
    {"id": "CTP-06", "requirement": "Scope 1, 2, 3 coverage",
     "article": "Art 22(1)"},
    {"id": "CTP-07", "requirement": "Annual progress reporting",
     "article": "Art 22(2)"},
    {"id": "CTP-08", "requirement": "Board oversight of climate plan",
     "article": "Art 22(3)"},
]

# Due diligence obligation categories (Art 5-11)
DD_OBLIGATION_CATEGORIES = [
    {"id": "DD-01", "obligation": "Integrate due diligence into company policies",
     "article": "Art 5", "weight": 0.10},
    {"id": "DD-02", "obligation": "Identify actual & potential adverse impacts",
     "article": "Art 6", "weight": 0.20},
    {"id": "DD-03", "obligation": "Prevent & mitigate potential adverse impacts",
     "article": "Art 7", "weight": 0.20},
    {"id": "DD-04", "obligation": "Bring actual adverse impacts to an end / minimise",
     "article": "Art 8", "weight": 0.20},
    {"id": "DD-05", "obligation": "Provide remediation for actual impacts",
     "article": "Art 9", "weight": 0.10},
    {"id": "DD-06", "obligation": "Meaningful stakeholder engagement",
     "article": "Art 10", "weight": 0.05},
    {"id": "DD-07", "obligation": "Establish & maintain complaints mechanism",
     "article": "Art 11", "weight": 0.05},
    {"id": "DD-08", "obligation": "Monitor effectiveness of DD measures",
     "article": "Art 12", "weight": 0.05},
    {"id": "DD-09", "obligation": "Public communication & reporting",
     "article": "Art 13", "weight": 0.05},
]

# Penalty framework (Art 30-33)
PENALTY_FRAMEWORK = {
    "max_turnover_pct": 5.0,
    "description": "Up to 5% of worldwide net turnover",
    "injunctive_relief": True,
    "naming_and_shaming": True,
    "interim_measures": True,
    "civil_liability": {
        "article": "Art 29",
        "description": "Civil liability for failure to prevent / bring to end adverse impacts",
        "limitation_period_years": 5,
        "burden_of_proof": "claimant must prove damage + breach + causal link",
    },
}

# Cross-framework mapping
CSDDD_CROSS_FRAMEWORK_MAP = [
    {
        "csddd_article": "Art 6 (Impact identification)",
        "csrd_esrs": "ESRS S1 (Own Workforce), S2 (Value Chain Workers), S3 (Affected Communities)",
        "ungp": "Pillar II — Human Rights Due Diligence",
        "oecd": "Chapter IV — Human Rights",
    },
    {
        "csddd_article": "Art 7-8 (Prevention & remediation)",
        "csrd_esrs": "ESRS S1 DR S1-4 (Actions), S2 DR S2-4",
        "ungp": "Principles 17-21 (HRDD Process)",
        "oecd": "Chapter IV, II.A.10-13",
    },
    {
        "csddd_article": "Art 11 (Grievance mechanism)",
        "csrd_esrs": "ESRS S1 DR S1-3, S2 DR S2-3",
        "ungp": "Principle 29 (Operational grievance mechanisms)",
        "oecd": "Chapter IV, 46 (NCP complaints)",
    },
    {
        "csddd_article": "Art 22 (Climate transition plan)",
        "csrd_esrs": "ESRS E1 DR E1-1 (Transition plan for climate)",
        "ungp": "N/A",
        "oecd": "Chapter VI — Environment",
    },
    {
        "csddd_article": "Art 25-26 (Director duty of care)",
        "csrd_esrs": "ESRS 2 GOV-1 (Role of admin bodies)",
        "ungp": "Pillar I — State Duty to Protect",
        "oecd": "Chapter VI.A.1",
    },
    {
        "csddd_article": "EUDR linkage (Deforestation DD)",
        "csrd_esrs": "ESRS E4 (Biodiversity)",
        "ungp": "N/A (environmental specific)",
        "oecd": "Chapter VI — Environment",
    },
]

# High-risk sectors (recital 22 / delegated acts expected)
HIGH_RISK_SECTORS = {
    "textiles": {"nace": ["C13", "C14", "C15"], "risk_areas": ["HR-01", "HR-02", "HR-05", "HR-06"]},
    "agriculture_food": {"nace": ["A01", "A02", "C10", "C11"], "risk_areas": ["HR-01", "HR-02", "HR-07", "ENV-02"]},
    "extractives": {"nace": ["B05", "B06", "B07", "B08", "B09"], "risk_areas": ["HR-07", "HR-08", "HR-10", "ENV-04", "ENV-06"]},
    "construction": {"nace": ["F41", "F42", "F43"], "risk_areas": ["HR-05", "HR-06", "ENV-05", "ENV-06"]},
    "electronics": {"nace": ["C26", "C27"], "risk_areas": ["HR-01", "HR-02", "HR-10", "ENV-07"]},
    "chemicals": {"nace": ["C20", "C21"], "risk_areas": ["ENV-04", "ENV-05", "ENV-06", "ENV-07"]},
    "transport": {"nace": ["H49", "H50", "H51"], "risk_areas": ["ENV-01", "ENV-05", "HR-05"]},
    "financial_services": {"nace": ["K64", "K65", "K66"], "risk_areas": ["ENV-01", "HR-01", "HR-10"]},
}


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ScopeAssessmentResult:
    entity_name: str
    is_eu_company: bool
    employees: int
    net_turnover_eur: float
    eu_generated_turnover_eur: float
    in_scope: bool
    scope_group: str  # group_1/2/3 or non_eu_group_1/2/3 or out_of_scope
    applies_from: str
    high_risk_sectors: list = field(default_factory=list)
    nace_codes: list = field(default_factory=list)
    notes: list = field(default_factory=list)


@dataclass
class AdverseImpactResult:
    entity_name: str
    value_chain_tier: str  # upstream / own_operations / downstream
    identified_impacts: list = field(default_factory=list)
    # Each impact: {code, title, category, severity, likelihood, priority, value_chain_location}
    total_impacts: int = 0
    critical_impacts: int = 0
    high_impacts: int = 0
    medium_impacts: int = 0
    low_impacts: int = 0
    risk_score: float = 0.0
    sector_risk_flags: list = field(default_factory=list)


@dataclass
class DDComplianceResult:
    entity_name: str
    assessment_date: str
    scope_group: str
    obligation_scores: list = field(default_factory=list)
    # Each: {id, obligation, article, weight, score, status, gaps, evidence}
    overall_score: float = 0.0
    compliance_status: str = ""  # compliant / partially_compliant / non_compliant
    climate_transition_plan_score: float = 0.0
    climate_transition_plan_gaps: list = field(default_factory=list)
    director_duty_assessment: dict = field(default_factory=dict)
    grievance_mechanism_status: str = ""
    total_gaps: int = 0
    critical_gaps: int = 0
    recommendations: list = field(default_factory=list)
    penalty_exposure: dict = field(default_factory=dict)
    cross_framework_linkage: list = field(default_factory=list)
    eudr_overlap: dict = field(default_factory=dict)


@dataclass
class ValueChainMappingResult:
    entity_name: str
    tiers_mapped: int = 0
    upstream_suppliers: int = 0
    downstream_partners: int = 0
    high_risk_links: int = 0
    countries_covered: list = field(default_factory=list)
    sector_breakdown: dict = field(default_factory=dict)
    mapping_completeness_pct: float = 0.0
    gaps: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CSDDDEngine:
    """EU Corporate Sustainability Due Diligence Directive 2024/1760 engine."""

    # ── Scope Assessment (Art 2) ──────────────────────────────────────────

    def assess_scope(
        self,
        entity_name: str,
        is_eu_company: bool,
        employees: int,
        net_turnover_eur: float,
        eu_generated_turnover_eur: float = 0.0,
        nace_codes: list | None = None,
    ) -> ScopeAssessmentResult:
        """Determine whether the entity falls within CSDDD scope."""
        nace_codes = nace_codes or []
        notes: list[str] = []
        high_risk = []

        # Identify sector risk
        for sector, info in HIGH_RISK_SECTORS.items():
            if any(nc.startswith(tuple(info["nace"])) for nc in nace_codes):
                high_risk.append(sector)

        scope_group = "out_of_scope"
        applies_from = ""

        if is_eu_company:
            if employees >= 5000 and net_turnover_eur >= 1_500_000_000:
                scope_group = "group_1"
            elif employees >= 3000 and net_turnover_eur >= 900_000_000:
                scope_group = "group_2"
            elif employees >= 1000 and net_turnover_eur >= 450_000_000:
                scope_group = "group_3"
            else:
                notes.append("Below EU company thresholds (Art 2(1))")
        else:
            eu_t = eu_generated_turnover_eur
            if eu_t >= 1_500_000_000:
                scope_group = "non_eu_group_1"
            elif eu_t >= 900_000_000:
                scope_group = "non_eu_group_2"
            elif eu_t >= 450_000_000:
                scope_group = "non_eu_group_3"
            else:
                notes.append("Below non-EU turnover thresholds (Art 2(2))")

        in_scope = scope_group != "out_of_scope"
        if in_scope:
            applies_from = SCOPE_THRESHOLDS.get(scope_group, {}).get("applies_from", "")
            notes.append(f"Entity in scope under {scope_group}: "
                         f"applies from {applies_from}")
        if high_risk:
            notes.append(f"High-risk sectors identified: {', '.join(high_risk)}")

        return ScopeAssessmentResult(
            entity_name=entity_name,
            is_eu_company=is_eu_company,
            employees=employees,
            net_turnover_eur=net_turnover_eur,
            eu_generated_turnover_eur=eu_generated_turnover_eur,
            in_scope=in_scope,
            scope_group=scope_group,
            applies_from=applies_from,
            high_risk_sectors=high_risk,
            nace_codes=nace_codes,
            notes=notes,
        )

    # ── Adverse Impact Identification (Art 6) ─────────────────────────────

    def identify_adverse_impacts(
        self,
        entity_name: str,
        nace_codes: list | None = None,
        countries_of_operation: list | None = None,
        supplier_countries: list | None = None,
        forced_labour_risk: bool = False,
        child_labour_risk: bool = False,
        deforestation_exposure: bool = False,
        conflict_minerals_exposure: bool = False,
        osh_incidents_per_1000: float = 0.0,
        water_stress_exposure: bool = False,
        ghg_intensity_high: bool = False,
        grievance_complaints_count: int = 0,
    ) -> AdverseImpactResult:
        """Identify actual and potential adverse human rights & environmental impacts."""
        nace_codes = nace_codes or []
        countries_of_operation = countries_of_operation or []
        supplier_countries = supplier_countries or []

        impacts = []
        sector_flags = []

        # Sector-based risk flags
        for sector, info in HIGH_RISK_SECTORS.items():
            if any(nc.startswith(tuple(info["nace"])) for nc in nace_codes):
                sector_flags.append(sector)
                for risk_code in info["risk_areas"]:
                    cat = ADVERSE_IMPACT_CATEGORIES.get(risk_code, {})
                    if cat:
                        impacts.append({
                            "code": risk_code,
                            "title": cat["title"],
                            "category": cat["category"],
                            "severity_weight": cat["severity_weight"],
                            "source": f"sector_risk:{sector}",
                            "likelihood": "potential",
                            "value_chain_location": "upstream",
                        })

        # Specific risk indicators
        if forced_labour_risk:
            impacts.append({
                "code": "HR-01", "title": "Forced / compulsory labour",
                "category": "human_rights", "severity_weight": 1.0,
                "source": "indicator:forced_labour", "likelihood": "actual",
                "value_chain_location": "upstream",
            })
        if child_labour_risk:
            impacts.append({
                "code": "HR-02", "title": "Child labour",
                "category": "human_rights", "severity_weight": 1.0,
                "source": "indicator:child_labour", "likelihood": "actual",
                "value_chain_location": "upstream",
            })
        if deforestation_exposure:
            impacts.append({
                "code": "ENV-02", "title": "Deforestation & ecosystem conversion",
                "category": "environment", "severity_weight": 1.0,
                "source": "indicator:deforestation", "likelihood": "potential",
                "value_chain_location": "upstream",
            })
        if conflict_minerals_exposure:
            impacts.append({
                "code": "HR-10", "title": "Conflict-affected & high-risk areas (CAHRAs)",
                "category": "human_rights", "severity_weight": 0.9,
                "source": "indicator:conflict_minerals", "likelihood": "potential",
                "value_chain_location": "upstream",
            })
        if osh_incidents_per_1000 > 5.0:
            impacts.append({
                "code": "HR-05", "title": "Unsafe / unhealthy working conditions",
                "category": "human_rights", "severity_weight": 0.9,
                "source": "indicator:osh_incidents", "likelihood": "actual",
                "value_chain_location": "own_operations",
            })
        if water_stress_exposure:
            impacts.append({
                "code": "ENV-04", "title": "Water pollution & depletion",
                "category": "environment", "severity_weight": 0.8,
                "source": "indicator:water_stress", "likelihood": "potential",
                "value_chain_location": "upstream",
            })
        if ghg_intensity_high:
            impacts.append({
                "code": "ENV-01", "title": "GHG emissions & climate change",
                "category": "environment", "severity_weight": 0.9,
                "source": "indicator:ghg_intensity", "likelihood": "actual",
                "value_chain_location": "own_operations",
            })

        # Deduplicate by code (keep highest severity source)
        seen: dict[str, dict] = {}
        for imp in impacts:
            code = imp["code"]
            if code not in seen or imp["severity_weight"] > seen[code]["severity_weight"]:
                seen[code] = imp
        unique_impacts = list(seen.values())

        # Classify by priority
        for imp in unique_impacts:
            sw = imp["severity_weight"]
            if imp["likelihood"] == "actual" and sw >= 0.9:
                imp["priority"] = "critical"
            elif sw >= 0.8:
                imp["priority"] = "high"
            elif sw >= 0.6:
                imp["priority"] = "medium"
            else:
                imp["priority"] = "low"

        critical = sum(1 for i in unique_impacts if i.get("priority") == "critical")
        high = sum(1 for i in unique_impacts if i.get("priority") == "high")
        medium = sum(1 for i in unique_impacts if i.get("priority") == "medium")
        low = sum(1 for i in unique_impacts if i.get("priority") == "low")

        # Composite risk score (0-100)
        if unique_impacts:
            weighted = sum(i["severity_weight"] * (1.5 if i["likelihood"] == "actual" else 1.0)
                          for i in unique_impacts)
            risk_score = min(100.0, round(weighted / len(unique_impacts) * 100, 1))
        else:
            risk_score = 0.0

        return AdverseImpactResult(
            entity_name=entity_name,
            value_chain_tier="full_chain",
            identified_impacts=unique_impacts,
            total_impacts=len(unique_impacts),
            critical_impacts=critical,
            high_impacts=high,
            medium_impacts=medium,
            low_impacts=low,
            risk_score=risk_score,
            sector_risk_flags=sector_flags,
        )

    # ── Due Diligence Compliance Assessment (Art 5-13) ────────────────────

    def assess_dd_compliance(
        self,
        entity_name: str,
        scope_group: str,
        # DD obligation evidence (0-100 per obligation)
        dd_policy_integrated: float = 0.0,
        impact_identification_score: float = 0.0,
        prevention_mitigation_score: float = 0.0,
        remediation_score: float = 0.0,
        remediation_provided: bool = False,
        stakeholder_engagement_score: float = 0.0,
        grievance_mechanism_operational: bool = False,
        monitoring_score: float = 0.0,
        public_reporting_score: float = 0.0,
        # Climate transition plan
        climate_plan_exists: bool = False,
        climate_plan_paris_aligned: bool = False,
        climate_targets_science_based: bool = False,
        scope_123_covered: bool = False,
        annual_progress_reported: bool = False,
        board_oversight_climate: bool = False,
        # Director duty
        director_sustainability_linked_remuneration: bool = False,
        director_dd_oversight: bool = False,
        # EUDR overlap
        eudr_commodities_in_scope: list | None = None,
        eudr_dd_completed: bool = False,
        # Company financials for penalty calculation
        net_turnover_eur: float = 0.0,
    ) -> DDComplianceResult:
        """Full due diligence compliance assessment under CSDDD."""
        assessment_date = datetime.utcnow().strftime("%Y-%m-%d")
        eudr_commodities_in_scope = eudr_commodities_in_scope or []

        # Score each obligation
        score_map = {
            "DD-01": dd_policy_integrated,
            "DD-02": impact_identification_score,
            "DD-03": prevention_mitigation_score,
            "DD-04": prevention_mitigation_score * 0.9 if remediation_provided else prevention_mitigation_score * 0.5,
            "DD-05": remediation_score,
            "DD-06": stakeholder_engagement_score,
            "DD-07": 80.0 if grievance_mechanism_operational else 10.0,
            "DD-08": monitoring_score,
            "DD-09": public_reporting_score,
        }

        obligation_results = []
        gaps = []
        for ob in DD_OBLIGATION_CATEGORIES:
            ob_id = ob["id"]
            raw = min(100.0, max(0.0, score_map.get(ob_id, 0.0)))
            status = "compliant" if raw >= 70 else ("partial" if raw >= 40 else "non_compliant")
            ob_gaps = []
            if raw < 70:
                ob_gaps.append(f"{ob['obligation']} — score {raw:.0f}/100 (threshold: 70)")
                gaps.append({
                    "obligation_id": ob_id,
                    "article": ob["article"],
                    "gap": ob["obligation"],
                    "severity": "critical" if raw < 30 else "major" if raw < 50 else "minor",
                    "current_score": raw,
                })
            obligation_results.append({
                "id": ob_id,
                "obligation": ob["obligation"],
                "article": ob["article"],
                "weight": ob["weight"],
                "score": round(raw, 1),
                "status": status,
                "gaps": ob_gaps,
            })

        # Weighted overall
        overall = sum(o["score"] * o["weight"] for o in obligation_results)
        overall = round(overall, 1)

        if overall >= 75:
            compliance_status = "compliant"
        elif overall >= 50:
            compliance_status = "partially_compliant"
        else:
            compliance_status = "non_compliant"

        # Climate transition plan (Art 22)
        ctp_checks = [
            ("CTP-01", climate_plan_paris_aligned, "Paris-aligned targets"),
            ("CTP-02", climate_plan_exists, "Time-bound actions"),
            ("CTP-03", climate_plan_exists, "Decarbonisation levers described"),
            ("CTP-04", climate_plan_exists, "Investment planning"),
            ("CTP-05", True, "Offset role defined (or N/A)"),
            ("CTP-06", scope_123_covered, "Scope 1/2/3 coverage"),
            ("CTP-07", annual_progress_reported, "Annual progress reporting"),
            ("CTP-08", board_oversight_climate, "Board oversight"),
        ]
        ctp_score = sum(100 / len(ctp_checks) for _, met, _ in ctp_checks if met)
        ctp_score = round(ctp_score, 1)
        ctp_gaps = [desc for _, met, desc in ctp_checks if not met]

        # Director duty (Art 25-26)
        director_duty = {
            "dd_oversight": director_dd_oversight,
            "sustainability_linked_remuneration": director_sustainability_linked_remuneration,
            "compliance_level": "compliant" if (director_dd_oversight and director_sustainability_linked_remuneration) else "partial",
        }

        # Grievance mechanism
        gm_status = "operational" if grievance_mechanism_operational else "not_established"

        # Total gaps
        critical_count = sum(1 for g in gaps if g["severity"] == "critical")

        # Penalty exposure
        penalty = {
            "max_fine_eur": round(net_turnover_eur * PENALTY_FRAMEWORK["max_turnover_pct"] / 100, 2),
            "max_turnover_pct": PENALTY_FRAMEWORK["max_turnover_pct"],
            "civil_liability_exposure": compliance_status == "non_compliant",
            "limitation_period_years": PENALTY_FRAMEWORK["civil_liability"]["limitation_period_years"],
        }

        # EUDR overlap
        eudr_overlap = {}
        if eudr_commodities_in_scope:
            eudr_overlap = {
                "commodities_in_scope": eudr_commodities_in_scope,
                "eudr_dd_completed": eudr_dd_completed,
                "note": "CSDDD environmental DD overlaps with EUDR for deforestation-risk commodities (Art 6 ENV-02)",
            }

        # Recommendations
        recommendations = self._generate_recommendations(
            overall, gaps, ctp_gaps, gm_status, director_duty, eudr_overlap
        )

        return DDComplianceResult(
            entity_name=entity_name,
            assessment_date=assessment_date,
            scope_group=scope_group,
            obligation_scores=obligation_results,
            overall_score=overall,
            compliance_status=compliance_status,
            climate_transition_plan_score=ctp_score,
            climate_transition_plan_gaps=ctp_gaps,
            director_duty_assessment=director_duty,
            grievance_mechanism_status=gm_status,
            total_gaps=len(gaps),
            critical_gaps=critical_count,
            recommendations=recommendations,
            penalty_exposure=penalty,
            cross_framework_linkage=CSDDD_CROSS_FRAMEWORK_MAP,
            eudr_overlap=eudr_overlap,
        )

    # ── Value Chain Mapping (Art 6, Art 14) ───────────────────────────────

    def assess_value_chain_mapping(
        self,
        entity_name: str,
        upstream_supplier_count: int = 0,
        upstream_countries: list | None = None,
        downstream_partner_count: int = 0,
        downstream_countries: list | None = None,
        tier1_mapped: bool = False,
        tier2_mapped: bool = False,
        tier3_plus_mapped: bool = False,
        contractual_cascading_pct: float = 0.0,
        high_risk_links_identified: int = 0,
        sector_breakdown: dict | None = None,
    ) -> ValueChainMappingResult:
        """Assess value chain mapping completeness for CSDDD compliance."""
        upstream_countries = upstream_countries or []
        downstream_countries = downstream_countries or []
        sector_breakdown = sector_breakdown or {}

        tiers_mapped = sum([tier1_mapped, tier2_mapped, tier3_plus_mapped])
        all_countries = list(set(upstream_countries + downstream_countries))

        # Completeness scoring
        completeness = 0.0
        if tier1_mapped:
            completeness += 40.0
        if tier2_mapped:
            completeness += 30.0
        if tier3_plus_mapped:
            completeness += 15.0
        if contractual_cascading_pct >= 80:
            completeness += 15.0
        elif contractual_cascading_pct >= 50:
            completeness += 10.0
        elif contractual_cascading_pct >= 20:
            completeness += 5.0
        completeness = min(100.0, round(completeness, 1))

        gaps = []
        if not tier1_mapped:
            gaps.append("Tier 1 suppliers not fully mapped")
        if not tier2_mapped:
            gaps.append("Tier 2 suppliers not mapped — required for high-risk sectors (Art 6)")
        if not tier3_plus_mapped:
            gaps.append("Deep-tier (Tier 3+) suppliers not mapped — recommended for CAHRAs")
        if contractual_cascading_pct < 50:
            gaps.append(f"Contractual cascading only {contractual_cascading_pct:.0f}% — Art 14 requires DD obligations in contracts")
        if high_risk_links_identified == 0 and (upstream_supplier_count + downstream_partner_count) > 0:
            gaps.append("No high-risk value chain links identified — risk assessment may be incomplete")

        return ValueChainMappingResult(
            entity_name=entity_name,
            tiers_mapped=tiers_mapped,
            upstream_suppliers=upstream_supplier_count,
            downstream_partners=downstream_partner_count,
            high_risk_links=high_risk_links_identified,
            countries_covered=all_countries,
            sector_breakdown=sector_breakdown,
            mapping_completeness_pct=completeness,
            gaps=gaps,
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _generate_recommendations(
        self, overall: float, gaps: list, ctp_gaps: list,
        gm_status: str, director_duty: dict, eudr_overlap: dict,
    ) -> list[str]:
        recs = []
        if overall < 50:
            recs.append("URGENT: Overall DD compliance below 50% — initiate remediation programme immediately")
        for g in gaps:
            if g["severity"] == "critical":
                recs.append(f"Address critical gap: {g['gap']} ({g['article']})")
        if ctp_gaps:
            recs.append(f"Climate transition plan has {len(ctp_gaps)} gap(s): {', '.join(ctp_gaps[:3])}")
        if gm_status != "operational":
            recs.append("Establish operational grievance mechanism per Art 11 before CSDDD applies")
        if not director_duty.get("dd_oversight"):
            recs.append("Board must integrate DD oversight into governance structure (Art 25)")
        if not director_duty.get("sustainability_linked_remuneration"):
            recs.append("Consider linking director remuneration to sustainability KPIs (Art 26)")
        if eudr_overlap and not eudr_overlap.get("eudr_dd_completed"):
            recs.append("Complete EUDR due diligence for deforestation-risk commodities — overlaps with CSDDD Art 6 ENV-02")
        return recs

    # ── Static Reference Data ─────────────────────────────────────────────

    @staticmethod
    def get_scope_thresholds() -> dict:
        return SCOPE_THRESHOLDS

    @staticmethod
    def get_adverse_impact_categories() -> list[dict]:
        return [{"code": k, **v} for k, v in ADVERSE_IMPACT_CATEGORIES.items()]

    @staticmethod
    def get_dd_obligations() -> list[dict]:
        return DD_OBLIGATION_CATEGORIES

    @staticmethod
    def get_climate_transition_plan_requirements() -> list[dict]:
        return CLIMATE_TRANSITION_PLAN_REQUIREMENTS

    @staticmethod
    def get_penalty_framework() -> dict:
        return PENALTY_FRAMEWORK

    @staticmethod
    def get_cross_framework_map() -> list[dict]:
        return CSDDD_CROSS_FRAMEWORK_MAP

    @staticmethod
    def get_high_risk_sectors() -> dict:
        return HIGH_RISK_SECTORS
