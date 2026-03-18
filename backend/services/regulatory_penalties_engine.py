"""Regulatory Penalty & Enforcement Engine (E35)
EU ESG enforcement framework:
- CSRD (Directive 2022/2464): Art 19a/29a penalties (member state transposition, up to 10M€ or 5% turnover)
- SFDR (Regulation 2019/2088): Art 14 enforcement (national CA, up to 10% revenue)
- EU Taxonomy (Regulation 2020/852): Art 22 misleading classification
- EUDR (Regulation 2023/1115): Art 24-25 penalties (up to 4% EU annual turnover)
- CSDDD (Directive 2024/1760): Art 29-33 (up to 5% worldwide net turnover)
"""

import random
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid
import math

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

REGULATION_CONFIGS: Dict[str, Dict] = {
    "csrd": {
        "name": "Corporate Sustainability Reporting Directive",
        "short": "CSRD",
        "regulation": "Directive (EU) 2022/2464",
        "max_penalty_pct_turnover": 5.0,
        "fixed_max_mn": 10.0,
        "supervisory_authority": "National Competent Authority (NCA) / Auditor oversight body",
        "enforcement_start_date": "2025-01-01",
        "articles": ["Art 19a (large PIEs)", "Art 29a (parent entities)", "Art 33b (penalties)"],
        "scope": "Large PIEs FY2024; large companies FY2025; SMEs FY2026",
        "penalty_basis": "Per violation / per disclosure period",
        "notes": "Member states set exact penalty levels within directive ceiling",
    },
    "sfdr": {
        "name": "Sustainable Finance Disclosure Regulation",
        "short": "SFDR",
        "regulation": "Regulation (EU) 2019/2088",
        "max_penalty_pct_turnover": 10.0,
        "fixed_max_mn": 5.0,
        "supervisory_authority": "National Competent Authority (NCA) / ESMA Level 2",
        "enforcement_start_date": "2021-03-10",
        "articles": ["Art 3 (sustainability risk policies)", "Art 4 (PAI)", "Art 6 (pre-contractual)", "Art 14 (enforcement)"],
        "scope": "Financial market participants & financial advisers",
        "penalty_basis": "Per product / per disclosure period",
        "notes": "Greenwashing enforcement increasing via ECB/ESMA supervisory convergence",
    },
    "taxonomy": {
        "name": "EU Taxonomy Regulation",
        "short": "EU Taxonomy",
        "regulation": "Regulation (EU) 2020/852",
        "max_penalty_pct_turnover": 4.0,
        "fixed_max_mn": 8.0,
        "supervisory_authority": "National Competent Authority (varies by member state)",
        "enforcement_start_date": "2022-01-01",
        "articles": ["Art 8 (disclosure)", "Art 22 (misleading classification)", "Art 23 (amendments)"],
        "scope": "Non-financial entities subject to CSRD; financial product providers",
        "penalty_basis": "Per misclassification incident",
        "notes": "Delegated Acts Climate (2021/2139) and Social (pending) extend scope",
    },
    "eudr": {
        "name": "EU Deforestation Regulation",
        "short": "EUDR",
        "regulation": "Regulation (EU) 2023/1115",
        "max_penalty_pct_turnover": 4.0,
        "fixed_max_mn": None,  # percentage-based only
        "supervisory_authority": "Member state CA (customs & market surveillance)",
        "enforcement_start_date": "2025-12-30",
        "articles": ["Art 24 (penalties)", "Art 25 (confiscation)", "Art 26 (market exclusion)"],
        "scope": "Operators and traders of 7 regulated commodities",
        "penalty_basis": "Per infringement; proportional to environmental harm",
        "notes": "3% minimum fine for recidivists; public market exclusion up to 12 months",
    },
    "csddd": {
        "name": "Corporate Sustainability Due Diligence Directive",
        "short": "CSDDD",
        "regulation": "Directive (EU) 2024/1760",
        "max_penalty_pct_turnover": 5.0,
        "fixed_max_mn": None,
        "supervisory_authority": "National supervisory authority (NFCA equivalent)",
        "enforcement_start_date": "2027-07-26",
        "articles": ["Art 29 (civil liability)", "Art 30 (supervisory authorities)", "Art 33 (penalties)"],
        "scope": "EU companies: >1000 FTE and >450M€ net turnover",
        "penalty_basis": "Per infringement of due diligence obligations",
        "notes": "Phased application: Group 1 (2027), Group 2 (2028), Group 3 (2029)",
    },
}

SUPERVISORY_AUTHORITY_MAP: Dict[str, Dict] = {
    "csrd": {
        "EU_level": "EFRAG (standard setter); national enforcement bodies",
        "DE": "Bundesamt für Justiz + APAS (audit oversight)",
        "FR": "AMF + H3C (audit oversight)",
        "UK": "FCA / Financial Reporting Council",
        "NL": "AFM",
        "IT": "CONSOB",
        "ES": "CNMV",
        "SE": "Finansinspektionen",
        "PL": "KNF",
    },
    "sfdr": {
        "EU_level": "ESMA (co-ordination) + Joint Committee ESAs",
        "DE": "BaFin",
        "FR": "AMF",
        "UK": "FCA (UK SFDR equivalent pending)",
        "NL": "AFM",
        "IT": "CONSOB + Bank of Italy",
        "ES": "CNMV",
        "LU": "CSSF (main fund domicile)",
        "IE": "Central Bank of Ireland",
    },
    "taxonomy": {
        "EU_level": "European Commission + Platform on Sustainable Finance",
        "DE": "BaFin",
        "FR": "AMF",
        "NL": "AFM",
        "IT": "CONSOB",
    },
    "eudr": {
        "EU_level": "European Commission (DG ENVI) + TRACES system",
        "DE": "Bundeszollverwaltung (customs)",
        "FR": "Douanes françaises",
        "NL": "Netherlands Food and Consumer Product Safety Authority (NVWA)",
        "all": "Member state customs & market surveillance authorities",
    },
    "csddd": {
        "EU_level": "European Commission (DG JUST) + Network of supervisory authorities",
        "all": "National due diligence supervisory authority (to be designated per member state)",
    },
}

VIOLATION_SEVERITY: Dict[str, float] = {
    "critical":  1.00,  # Systemic; intentional; public harm
    "major":     0.60,  # Significant; repeated; material misstatement
    "moderate":  0.30,  # Notable but isolated; first offence
    "minor":     0.10,  # Technical; immaterial; self-reported
}

WHISTLEBLOWER_RISK_THRESHOLDS: Dict[str, Dict] = {
    "low":    {"max_score": 30, "description": "Strong compliance culture; minimal exposure"},
    "medium": {"max_score": 60, "description": "Gaps identified; moderate enforcement risk"},
    "high":   {"max_score": 100, "description": "Material non-compliance; elevated whistleblower probability"},
}

ENFORCEMENT_TIMELINE_2024_2030: List[Dict] = [
    {"date": "2024-01-01", "event": "CSRD applies to large PIEs (FY2024 reporting)"},
    {"date": "2024-07-25", "event": "CSDDD published in Official Journal of EU"},
    {"date": "2025-01-01", "event": "CSRD first reports due (PIEs with >500 employees)"},
    {"date": "2025-03-10", "event": "SFDR Level 2 RTS full application"},
    {"date": "2025-06-30", "event": "EUDR original entry into force (large operators)"},
    {"date": "2025-12-30", "event": "EUDR enforcement start (delayed from June 2025)"},
    {"date": "2026-01-01", "event": "CSRD large non-PIE companies (FY2025 reports due)"},
    {"date": "2026-06-30", "event": "EUDR entry into force for SMEs"},
    {"date": "2027-07-26", "event": "CSDDD transposition deadline; Group 1 applies"},
    {"date": "2028-07-26", "event": "CSDDD Group 2 applies"},
    {"date": "2028-01-01", "event": "CSRD listed SMEs (FY2026 reports)"},
    {"date": "2029-07-26", "event": "CSDDD Group 3 applies"},
    {"date": "2030-01-01", "event": "SFDR Product Categories (Art 5/6/7/8/9) full reclassification"},
]

HIGH_RISK_JURISDICTIONS: List[str] = [
    "DE",  # Germany — BaFin active SFDR enforcement; proactive CSRD audit
    "FR",  # France — AMF greenwashing enforcement; DPEF precedents
    "NL",  # Netherlands — AFM greenwashing task force; EUDR customs scrutiny
    "SE",  # Sweden — Finansinspektionen PAI monitoring; consumer protection active
    "DK",  # Denmark — FSA aggressive green claims enforcement
    "AT",  # Austria — FMA SFDR enforcement; consumer ombudsman active
    "BE",  # Belgium — FSMA green bonds; EUDR port enforcement
    "IT",  # Italy — CONSOB; AGCM green claims; EUDR customs
]


# ── Engine ────────────────────────────────────────────────────────────────────

class RegulatoryPenaltiesEngine:
    """Regulatory Penalty & Enforcement Engine.

    Calculates expected penalties across CSRD, SFDR, EU Taxonomy, EUDR, and CSDDD
    based on compliance scores and entity turnover. All outputs are deterministic
    for a given entity_id.
    """

    def __init__(self) -> None:
        pass

    def _rng(self, entity_id: str) -> random.Random:
        seed = hash(entity_id) & 0xFFFFFFFF
        return random.Random(seed)

    def _compliance_to_violation_severity(self, compliance_pct: float) -> str:
        if compliance_pct < 30:
            return "critical"
        if compliance_pct < 55:
            return "major"
        if compliance_pct < 75:
            return "moderate"
        return "minor"

    def _expected_penalty_factor(self, compliance_pct: float, rng: random.Random) -> float:
        """Fraction of max penalty likely to be imposed, given compliance level."""
        base_non_compliance = max(0, (100 - compliance_pct) / 100)
        # Regulators typically impose 20-60% of max when non-compliance is demonstrated
        enforcement_factor = rng.uniform(0.15, 0.65) * base_non_compliance
        return enforcement_factor

    # ── calculate_regulation_penalty ─────────────────────────────────────────

    def calculate_regulation_penalty(
        self,
        entity_id: str,
        regulation: str,
        annual_turnover_mn: float,
        compliance_pct: float,
        violation_details: Optional[Dict] = None,
    ) -> Dict:
        """Calculate penalty exposure for a single regulation."""
        rng = self._rng(f"{entity_id}:{regulation}")
        cfg = REGULATION_CONFIGS.get(regulation, REGULATION_CONFIGS["csrd"])

        severity_label = self._compliance_to_violation_severity(compliance_pct)
        severity_mult = VIOLATION_SEVERITY[severity_label]

        max_pct_penalty = (annual_turnover_mn * cfg["max_penalty_pct_turnover"] / 100)
        max_fixed = cfg.get("fixed_max_mn")
        max_penalty_mn = min(max_pct_penalty, max_fixed) if max_fixed else max_pct_penalty

        enforcement_factor = self._expected_penalty_factor(compliance_pct, rng)
        expected_penalty_mn = round(max_penalty_mn * enforcement_factor * severity_mult, 3)

        # Violation count estimate
        violation_count = violation_details.get("count", 0) if violation_details else int(
            max(0, (100 - compliance_pct) / 10) + rng.randint(0, 3)
        )

        return {
            "regulation": regulation,
            "regulation_name": cfg["name"],
            "compliance_pct": compliance_pct,
            "violation_severity": severity_label,
            "max_penalty_mn": round(max_penalty_mn, 3),
            "expected_penalty_mn": expected_penalty_mn,
            "penalty_pct_of_turnover": round(expected_penalty_mn / annual_turnover_mn * 100, 4) if annual_turnover_mn > 0 else 0,
            "violation_count": violation_count,
            "supervisory_authority": cfg["supervisory_authority"],
            "enforcement_start_date": cfg["enforcement_start_date"],
            "key_articles": cfg["articles"],
            "enforcement_probability": round(max(0.02, min(0.95, enforcement_factor * 2)), 3),
            "currency": "EUR",
        }

    # ── assess_all_regulations ────────────────────────────────────────────────

    def assess_all_regulations(
        self,
        entity_id: str,
        annual_turnover_mn: float,
        compliance_scores: Dict[str, float],
    ) -> Dict:
        """Assess penalty exposure across all 5 regulations."""
        rng = self._rng(f"{entity_id}:all")

        results = {}
        total_max = 0.0
        total_expected = 0.0
        violations_found = []

        for reg in ["csrd", "sfdr", "taxonomy", "eudr", "csddd"]:
            comp = compliance_scores.get(reg, rng.uniform(40, 90))
            result = self.calculate_regulation_penalty(entity_id, reg, annual_turnover_mn, comp)
            results[reg] = result
            total_max += result["max_penalty_mn"]
            total_expected += result["expected_penalty_mn"]
            if comp < 75:
                violations_found.append({
                    "regulation": reg,
                    "compliance_pct": comp,
                    "severity": result["violation_severity"],
                    "expected_penalty_mn": result["expected_penalty_mn"],
                })

        # Cap total — regulators typically don't pile on full maxima
        effective_total = min(total_expected, annual_turnover_mn * 0.10)

        return {
            "entity_id": entity_id,
            "annual_turnover_mn": annual_turnover_mn,
            "penalty_by_regulation": results,
            "total_max_penalty_mn": round(total_max, 3),
            "total_expected_penalty_mn": round(effective_total, 3),
            "total_pct_of_turnover": round(effective_total / annual_turnover_mn * 100, 4) if annual_turnover_mn > 0 else 0,
            "violations_found": violations_found,
            "num_violations": len(violations_found),
            "highest_risk_regulation": max(results, key=lambda r: results[r]["expected_penalty_mn"]) if results else None,
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ── assess_whistleblower_risk ─────────────────────────────────────────────

    def assess_whistleblower_risk(
        self,
        entity_id: str,
        compliance_scores: Dict[str, float],
        sector: Optional[str] = None,
    ) -> Dict:
        """Assess whistleblower / internal reporting risk."""
        rng = self._rng(f"{entity_id}:whistleblower")

        avg_compliance = (
            sum(compliance_scores.values()) / len(compliance_scores)
            if compliance_scores else rng.uniform(50, 80)
        )

        # Risk score inversely proportional to compliance
        base_risk = 100 - avg_compliance
        sector_premium = 15 if sector in ["financial", "energy", "chemicals", "retail"] else 5
        jurisdiction_premium = rng.choice([0, 5, 10, 15])
        risk_score = min(100, base_risk + sector_premium * rng.uniform(0.5, 1.5) + jurisdiction_premium)

        tier = "low"
        for t, cfg in WHISTLEBLOWER_RISK_THRESHOLDS.items():
            if risk_score <= cfg["max_score"]:
                tier = t
                break

        risk_factors = []
        if avg_compliance < 60:
            risk_factors.append("Material non-compliance across multiple frameworks creates internal reporting incentive")
        if compliance_scores.get("sfdr", 100) < 70:
            risk_factors.append("SFDR PAI gaps — greenwashing allegations likely from activist investors")
        if compliance_scores.get("csrd", 100) < 65:
            risk_factors.append("CSRD disclosure gaps may be flagged by external auditors or civil society")
        if sector in ["financial", "energy"]:
            risk_factors.append(f"Sector '{sector}' under enhanced supervisory scrutiny in 2025-2026")
        if not risk_factors:
            risk_factors.append("No material whistleblower risk factors identified at current compliance levels")

        mitigation_actions = rng.sample([
            "Establish anonymous ESG compliance hotline (EU Whistleblower Directive 2019/1937)",
            "Conduct internal ESG compliance audit before regulatory deadline",
            "Engage external legal counsel for SFDR / CSRD gap review",
            "Brief board audit committee on ESG compliance exposure",
            "Develop remediation roadmap with regulator-facing timeline",
            "Subscribe to regulatory enforcement tracker for early-warning alerts",
        ], rng.randint(2, 4))

        return {
            "entity_id": entity_id,
            "whistleblower_risk": tier,
            "risk_score": round(risk_score, 1),
            "average_compliance_pct": round(avg_compliance, 1),
            "risk_factors": risk_factors,
            "mitigation_actions": mitigation_actions,
            "eu_directive_coverage": "EU Whistleblower Directive (2019/1937) — mandatory reporting channels for >50 FTE",
            "assessed_at": datetime.utcnow().isoformat(),
        }

    # ── generate_remediation_priorities ──────────────────────────────────────

    def generate_remediation_priorities(
        self,
        entity_id: str,
        penalty_assessment: Dict,
    ) -> List[Dict]:
        """Generate prioritised remediation actions from penalty assessment."""
        rng = self._rng(f"{entity_id}:remediation")

        actions = []
        violations = penalty_assessment.get("violations_found", [])

        # Sort by expected penalty descending
        violations_sorted = sorted(violations, key=lambda v: v.get("expected_penalty_mn", 0), reverse=True)

        remediation_map = {
            "csrd": [
                "Commission ESRS gap analysis and appoint sustainability controller",
                "Implement double materiality assessment process (IRO identification)",
                "Ensure Scope 3 GHG data collection covers all material categories",
                "Engage statutory auditor for limited assurance readiness assessment",
            ],
            "sfdr": [
                "Update pre-contractual disclosures with SFDR Level 2 RTS templates",
                "Implement PAI data collection for all 18 mandatory indicators",
                "Review Art 8/9 product classifications against new ESMA Q&A",
                "Document sustainability risk integration in investment process",
            ],
            "taxonomy": [
                "Map revenue/CAPEX/OPEX to EU Taxonomy eligible activities",
                "Complete DNSH technical screening criteria assessment",
                "Obtain supporting evidence for substantial contribution claims",
                "Review taxonomy disclosure in CSRD ESRS E1 context",
            ],
            "eudr": [
                "Implement geolocation verification for all regulated commodity suppliers",
                "Obtain due diligence statements (DDS) for all commodity imports",
                "Map supply chain to plot level for high-risk sourcing countries",
                "Register as operator in EU TRACES system before enforcement date",
            ],
            "csddd": [
                "Commission human rights and environmental risk mapping (Art 6)",
                "Develop adverse impact prevention action plan (Art 7)",
                "Establish grievance mechanism for affected stakeholders (Art 9)",
                "Prepare value chain mapping at Tier 1 and Tier 2 level",
            ],
        }

        for v in violations_sorted:
            reg = v.get("regulation", "")
            reg_actions = remediation_map.get(reg, [])
            if reg_actions:
                action = rng.choice(reg_actions)
                effort_map = {"critical": "High", "major": "High", "moderate": "Medium", "minor": "Low"}
                impact_map = {"critical": 90, "major": 70, "moderate": 40, "minor": 15}
                severity = v.get("severity", "moderate")
                actions.append({
                    "action_id": str(uuid.uuid4())[:8],
                    "regulation": reg,
                    "action": action,
                    "priority": severity.capitalize(),
                    "effort": effort_map.get(severity, "Medium"),
                    "impact_score": impact_map.get(severity, 40) + rng.randint(-5, 10),
                    "expected_penalty_avoided_mn": round(v.get("expected_penalty_mn", 0) * rng.uniform(0.5, 0.9), 3),
                    "timeframe": rng.choice(["Immediate (0-3m)", "Short-term (3-6m)", "Medium-term (6-12m)"]),
                })

        # Add generic actions if few violations
        if len(actions) < 3:
            actions.append({
                "action_id": str(uuid.uuid4())[:8],
                "regulation": "all",
                "action": "Establish cross-functional ESG compliance steering committee",
                "priority": "Medium",
                "effort": "Medium",
                "impact_score": 55,
                "expected_penalty_avoided_mn": 0,
                "timeframe": "Short-term (3-6m)",
            })

        return sorted(actions, key=lambda a: a["impact_score"], reverse=True)

    # ── run_full_assessment ───────────────────────────────────────────────────

    def run_full_assessment(
        self,
        entity_id: str,
        entity_name: str,
        annual_turnover_mn: float,
        compliance_scores: Dict[str, float],
        **kwargs,
    ) -> Dict:
        """Orchestrate full penalty assessment."""
        rng = self._rng(entity_id)
        assessment_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        sector = kwargs.get("sector", "general")
        jurisdiction = kwargs.get("jurisdiction", rng.choice(HIGH_RISK_JURISDICTIONS))

        # Main assessments
        all_regs = self.assess_all_regulations(entity_id, annual_turnover_mn, compliance_scores)
        whistleblower = self.assess_whistleblower_risk(entity_id, compliance_scores, sector)
        remediation = self.generate_remediation_priorities(entity_id, all_regs)

        avg_compliance = round(
            sum(compliance_scores.values()) / max(1, len(compliance_scores)), 1
        )

        overall_risk = (
            "Critical" if avg_compliance < 40 else
            ("High" if avg_compliance < 60 else
             ("Medium" if avg_compliance < 80 else "Low"))
        )

        return {
            "assessment_id": assessment_id,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "annual_turnover_mn": annual_turnover_mn,
            "reporting_period": kwargs.get("reporting_period", str(date.today().year - 1)),
            "sector": sector,
            "jurisdiction": jurisdiction,
            "compliance_scores": compliance_scores,
            "avg_compliance_pct": avg_compliance,
            "overall_risk_level": overall_risk,
            # Penalty summary
            "total_max_penalty_mn": all_regs["total_max_penalty_mn"],
            "total_expected_penalty_mn": all_regs["total_expected_penalty_mn"],
            "total_pct_of_turnover": all_regs["total_pct_of_turnover"],
            "num_violations": all_regs["num_violations"],
            "highest_risk_regulation": all_regs["highest_risk_regulation"],
            # Whistleblower
            "whistleblower_risk": whistleblower["whistleblower_risk"],
            "whistleblower_risk_score": whistleblower["risk_score"],
            # Detail sections
            "penalty_by_regulation": all_regs["penalty_by_regulation"],
            "violations_found": all_regs["violations_found"],
            "whistleblower_detail": whistleblower,
            "remediation_priorities": remediation,
            "high_risk_jurisdiction": jurisdiction in HIGH_RISK_JURISDICTIONS,
            "assessment_date": now,
            "created_at": now,
            "updated_at": now,
        }

    def get_reference_data(self) -> Dict:
        """Return all reference constants."""
        return {
            "regulations": REGULATION_CONFIGS,
            "authorities": SUPERVISORY_AUTHORITY_MAP,
            "enforcement_timeline": ENFORCEMENT_TIMELINE_2024_2030,
            "violation_severity": VIOLATION_SEVERITY,
            "whistleblower_thresholds": WHISTLEBLOWER_RISK_THRESHOLDS,
            "high_risk_jurisdictions": HIGH_RISK_JURISDICTIONS,
        }
