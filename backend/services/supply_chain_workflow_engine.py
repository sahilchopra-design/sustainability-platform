"""
Supply Chain Workflow Engine (E5)
===================================
Unified orchestration of EUDR + CSDDD + ESRS E4 obligations into a single
end-to-end supply chain compliance workflow.

Three input layers are combined:
  1. EUDR (Regulation (EU) 2023/1115)  — deforestation-free due diligence
  2. CSDDD (Directive (EU) 2024/1760)  — human-rights & environmental DD
  3. ESRS E4 (CSRD)                    — biodiversity & ecosystems disclosure

Output: a unified `SupplyChainAssessment` dataclass containing:
  - per-supplier risk matrix (EUDR + CSDDD risk score)
  - overall workflow compliance status
  - gap list with obligation source
  - recommended actions with priority & deadline mapping
  - regulatory cross-reference (EUDR Art.→CSDDD Art.→ESRS E4-x)
  - XBRL-ready disclosure flags (E4-1 through E4-8)

Design:
  - All three engines are called inline (no external HTTP).
  - Risk scores are normalised to 0–100.
  - Overall status: COMPLIANT (≥75) | PARTIAL (≥45) | NON_COMPLIANT (<45).
  - The engine is deterministic given the same inputs.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4

# ── Import sub-engines (graceful if not yet installed) ────────────────────────
try:
    from services.eudr_engine import EUDREngine
    _EUDR_AVAILABLE = True
except ImportError:
    _EUDR_AVAILABLE = False

try:
    from services.csddd_engine import CSDDDEngine
    _CSDDD_AVAILABLE = True
except ImportError:
    _CSDDD_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class SupplierInput:
    """Single supplier / commodity lot input for the workflow."""
    supplier_id: str
    supplier_name: str
    country_of_origin: str          # ISO-3 e.g. "BRA"
    commodity: str                  # e.g. "soy", "cattle", "wood"
    hs_code: Optional[str] = None
    annual_volume_tonnes: float = 0.0
    spend_eur: float = 0.0
    has_geolocation: bool = False   # plot-level polygon / GPS point available
    certification_scheme: Optional[str] = None   # "FSC" | "RSPO" | "PEFC" | None
    has_traceability_system: bool = False
    # CSDDD signals
    has_supplier_code_of_conduct: bool = False
    has_audit_programme: bool = False
    has_grievance_mechanism: bool = False
    # ESRS E4 signals
    has_biodiversity_impact_assessment: bool = False
    operates_in_sensitive_area: bool = False     # KBA / Natura 2000 / WDPA
    restoration_commitments: bool = False


@dataclass
class SupplierRiskResult:
    supplier_id: str
    supplier_name: str
    country: str
    commodity: str

    # EUDR
    eudr_country_risk_tier: str = "unknown"       # high | standard | low
    eudr_commodity_covered: bool = False
    eudr_traceability_score: float = 0.0          # 0–100
    eudr_dd_required: bool = True
    eudr_risk_score: float = 0.0                  # 0–100 (higher = riskier)

    # CSDDD
    csddd_adverse_impact_count: int = 0
    csddd_dd_score: float = 0.0                   # 0–100 (higher = more compliant)
    csddd_high_priority_impacts: List[str] = field(default_factory=list)

    # ESRS E4
    esrs_e4_biodiversity_risk: str = "not_assessed"   # low | medium | high | not_assessed
    esrs_e4_sensitive_area: bool = False
    esrs_e4_disclosure_flags: Dict[str, bool] = field(default_factory=dict)

    # Combined
    overall_risk_score: float = 0.0              # 0–100 (higher = riskier)
    supplier_status: str = "needs_review"         # compliant | needs_review | high_risk
    gaps: List[str] = field(default_factory=list)
    recommended_actions: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class WorkflowAssessment:
    """Top-level result returned by SupplyChainWorkflowEngine.assess()."""
    run_id: str
    entity_name: str
    assessment_date: str
    supplier_count: int
    commodity_count: int

    # Aggregate scores
    overall_workflow_score: float = 0.0          # 0–100 (higher = more compliant)
    workflow_status: str = "non_compliant"        # compliant | partial | non_compliant

    # Per-supplier breakdown
    supplier_results: List[SupplierRiskResult] = field(default_factory=list)

    # Summary by risk tier
    high_risk_suppliers: int = 0
    medium_risk_suppliers: int = 0
    low_risk_suppliers: int = 0

    # Gap & action summary
    total_gaps: int = 0
    critical_gaps: List[str] = field(default_factory=list)
    priority_actions: List[Dict[str, str]] = field(default_factory=list)

    # Regulatory cross-reference
    regulatory_mapping: Dict[str, Any] = field(default_factory=dict)

    # ESRS E4 disclosure readiness
    esrs_e4_disclosure_readiness: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Country Risk Reference (EUDR Article 29 — abbreviated)
# ---------------------------------------------------------------------------

_EUDR_HIGH_RISK_COUNTRIES = {
    "BRA", "IDN", "MMR", "COD", "PNG", "COG", "CMR", "BOL",
    "ARG", "PRY", "GUY", "SUR", "GIN", "GHA", "NGA",
}
_EUDR_LOW_RISK_COUNTRIES = {
    "FIN", "SWE", "NOR", "AUT", "CHE", "NZL", "AUS", "CAN",
    "GBR", "DEU", "FRA", "NLD", "BEL",
}

# EUDR Annex I commodities
_EUDR_COMMODITIES = {"cattle", "cocoa", "coffee", "oil_palm", "rubber", "soy", "wood"}

# ESRS E4 disclosure requirements (E4-1 to E4-8)
_ESRS_E4_DISCLOSURES = {
    "E4-1": "Transition plan and consideration of biodiversity",
    "E4-2": "Policies related to biodiversity and ecosystems",
    "E4-3": "Actions and resources related to biodiversity and ecosystems",
    "E4-4": "Targets related to biodiversity and ecosystems",
    "E4-5": "Impact metrics related to biodiversity and ecosystems",
    "E4-6": "Pollution-related impacts on biodiversity",
    "E4-7": "Ecosystems degradation and conversion",
    "E4-8": "Financial effects from biodiversity and ecosystem change",
}

# CSDDD ENV adverse impact categories linked to supply chain
_CSDDD_SC_IMPACTS = {
    "ENV-01": "Deforestation / forest degradation",
    "ENV-02": "Land conversion / habitat destruction",
    "ENV-03": "Biodiversity loss (species)",
    "ENV-04": "Pollution of soil / groundwater",
    "ENV-05": "Water over-extraction",
    "HR-01": "Forced labour in supply chain",
    "HR-02": "Child labour in supply chain",
    "HR-04": "Unsafe working conditions",
}

# Regulatory cross-reference map
_REGULATORY_MAPPING = {
    "EUDR_Art_3": {
        "obligation": "No deforestation: commodities must not contribute to deforestation/forest degradation",
        "csddd_link": "CSDDD Art.6 ENV-01/ENV-02",
        "esrs_link": "ESRS E4-7 ecosystems conversion",
        "platform_module": "eudr_engine",
    },
    "EUDR_Art_9": {
        "obligation": "Due diligence: geolocation, risk assessment, risk mitigation",
        "csddd_link": "CSDDD Art.7 risk identification + Art.8 prevention",
        "esrs_link": "ESRS E4-3 actions / E4-4 targets",
        "platform_module": "eudr_engine + csddd_engine",
    },
    "EUDR_Art_29": {
        "obligation": "Country benchmarking: classify country risk (high/standard/low)",
        "csddd_link": "CSDDD Art.6 country-of-origin risk assessment",
        "esrs_link": "ESRS E4-5 impact metrics",
        "platform_module": "eudr_engine",
    },
    "CSDDD_Art_6": {
        "obligation": "Identify actual and potential adverse impacts in own operations and supply chain",
        "eudr_link": "EUDR Art.9(1)(b) risk assessment",
        "esrs_link": "ESRS E4-5 + E4-7 impact disclosure",
        "platform_module": "csddd_engine",
    },
    "CSDDD_Art_8": {
        "obligation": "Take prevention/mitigation action including supplier codes of conduct",
        "eudr_link": "EUDR Art.9(1)(c) risk mitigation",
        "esrs_link": "ESRS E4-3 actions",
        "platform_module": "csddd_engine",
    },
    "ESRS_E4_4": {
        "obligation": "Set measurable biodiversity targets (area, species, ecosystem services)",
        "eudr_link": "EUDR Art.3 no-deforestation target",
        "csddd_link": "CSDDD Art.22 transition plan (ENV targets)",
        "platform_module": "csrd_engine",
    },
}


# ---------------------------------------------------------------------------
# Workflow Engine
# ---------------------------------------------------------------------------

class SupplyChainWorkflowEngine:
    """
    Orchestrates EUDR + CSDDD + ESRS E4 into a unified supply chain
    compliance assessment.

    Usage:
        engine = SupplyChainWorkflowEngine()
        result = engine.assess(entity_name="Acme Corp", suppliers=[...])
    """

    def assess(
        self,
        entity_name: str,
        suppliers: List[SupplierInput],
        assessment_date: Optional[str] = None,
    ) -> WorkflowAssessment:
        """
        Run the full supply chain workflow for *entity_name* across *suppliers*.

        Returns a WorkflowAssessment with per-supplier risk results, aggregate
        scores, gap list, and regulatory cross-reference table.
        """
        _date = assessment_date or date.today().isoformat()
        run_id = str(uuid4())

        supplier_results: List[SupplierRiskResult] = []
        for supplier in suppliers:
            result = self._assess_supplier(supplier)
            supplier_results.append(result)

        assessment = self._aggregate(
            run_id=run_id,
            entity_name=entity_name,
            assessment_date=_date,
            supplier_results=supplier_results,
            suppliers=suppliers,
        )
        return assessment

    # ── Per-Supplier Assessment ────────────────────────────────────────────

    def _assess_supplier(self, s: SupplierInput) -> SupplierRiskResult:
        result = SupplierRiskResult(
            supplier_id=s.supplier_id,
            supplier_name=s.supplier_name,
            country=s.country_of_origin,
            commodity=s.commodity,
        )

        # --- EUDR Layer ---
        result.eudr_commodity_covered = s.commodity.lower() in _EUDR_COMMODITIES
        result.eudr_country_risk_tier = self._eudr_country_tier(s.country_of_origin)
        result.eudr_dd_required = result.eudr_commodity_covered
        result.eudr_traceability_score = self._eudr_traceability_score(s)
        result.eudr_risk_score = self._eudr_risk_score(result, s)

        # --- CSDDD Layer ---
        impacts, priority_impacts = self._csddd_impacts(s)
        result.csddd_adverse_impact_count = len(impacts)
        result.csddd_high_priority_impacts = priority_impacts
        result.csddd_dd_score = self._csddd_dd_score(s)

        # --- ESRS E4 Layer ---
        result.esrs_e4_sensitive_area = s.operates_in_sensitive_area
        result.esrs_e4_biodiversity_risk = self._esrs_e4_risk_level(s)
        result.esrs_e4_disclosure_flags = self._esrs_e4_flags(s)

        # --- Combined ---
        result.overall_risk_score = self._combined_risk(result)
        result.supplier_status = (
            "compliant" if result.overall_risk_score <= 30
            else "high_risk" if result.overall_risk_score >= 65
            else "needs_review"
        )
        result.gaps = self._build_gaps(result, s)
        result.recommended_actions = self._build_actions(result, s)

        return result

    # ── EUDR Scoring Helpers ───────────────────────────────────────────────

    def _eudr_country_tier(self, country: str) -> str:
        if country.upper() in _EUDR_HIGH_RISK_COUNTRIES:
            return "high"
        if country.upper() in _EUDR_LOW_RISK_COUNTRIES:
            return "low"
        return "standard"

    def _eudr_traceability_score(self, s: SupplierInput) -> float:
        score = 0.0
        if s.has_geolocation:
            score += 40.0
        if s.has_traceability_system:
            score += 30.0
        if s.certification_scheme:
            score += 20.0
        if s.hs_code:
            score += 10.0
        return min(score, 100.0)

    def _eudr_risk_score(self, r: SupplierRiskResult, s: SupplierInput) -> float:
        """Higher score = higher EUDR non-compliance risk (0–100)."""
        if not r.eudr_commodity_covered:
            return 0.0
        base = {"high": 70.0, "standard": 40.0, "low": 15.0}.get(
            r.eudr_country_risk_tier, 40.0
        )
        # Traceability reduces risk
        traceability_discount = r.eudr_traceability_score * 0.5
        return max(0.0, min(100.0, base - traceability_discount))

    # ── CSDDD Scoring Helpers ──────────────────────────────────────────────

    def _csddd_impacts(self, s: SupplierInput) -> tuple[list, list]:
        impacts = []
        priority = []
        tier = self._eudr_country_tier(s.country_of_origin)

        if s.commodity.lower() in _EUDR_COMMODITIES and tier in ("high", "standard"):
            impacts.append("ENV-01")
            impacts.append("ENV-02")
            if tier == "high":
                priority.extend(["ENV-01", "ENV-02"])

        if s.operates_in_sensitive_area:
            impacts.append("ENV-03")
            priority.append("ENV-03")

        if not s.has_supplier_code_of_conduct:
            impacts.append("HR-01")
            impacts.append("HR-04")

        if not s.has_audit_programme and tier == "high":
            impacts.append("HR-02")
            priority.append("HR-02")

        # ENV-04/05 in high-risk agri
        if s.commodity.lower() in ("soy", "oil_palm", "cattle", "coffee"):
            impacts.append("ENV-04")
            if tier == "high":
                impacts.append("ENV-05")

        return impacts, priority

    def _csddd_dd_score(self, s: SupplierInput) -> float:
        """Higher score = better CSDDD due diligence posture (0–100)."""
        score = 30.0  # baseline (entity has a policy)
        if s.has_supplier_code_of_conduct:
            score += 25.0
        if s.has_audit_programme:
            score += 20.0
        if s.has_grievance_mechanism:
            score += 15.0
        if s.has_traceability_system:
            score += 10.0
        return min(score, 100.0)

    # ── ESRS E4 Helpers ────────────────────────────────────────────────────

    def _esrs_e4_risk_level(self, s: SupplierInput) -> str:
        tier = self._eudr_country_tier(s.country_of_origin)
        if s.operates_in_sensitive_area or tier == "high":
            return "high"
        if tier == "standard" and s.commodity.lower() in _EUDR_COMMODITIES:
            return "medium"
        return "low"

    def _esrs_e4_flags(self, s: SupplierInput) -> Dict[str, bool]:
        """Returns which ESRS E4 disclosures are triggered for this supplier."""
        flags: Dict[str, bool] = {}
        for dp_id in _ESRS_E4_DISCLOSURES:
            flags[dp_id] = False

        # E4-2 always triggered if supplier covered
        flags["E4-2"] = True
        # E4-7 if commodity in EUDR scope
        flags["E4-7"] = s.commodity.lower() in _EUDR_COMMODITIES
        # E4-5 if has biodiversity impact assessment
        flags["E4-5"] = s.has_biodiversity_impact_assessment
        # E4-3 if has restoration commitments
        flags["E4-3"] = s.restoration_commitments
        # E4-1 if company has a transition plan (heuristic: code of conduct present)
        flags["E4-1"] = s.has_supplier_code_of_conduct
        # E4-8 if sensitive area (financial effects likely material)
        flags["E4-8"] = s.operates_in_sensitive_area

        return flags

    # ── Combined Score ─────────────────────────────────────────────────────

    def _combined_risk(self, r: SupplierRiskResult) -> float:
        """
        Weighted combined risk score (higher = higher non-compliance risk).
        EUDR 40% + CSDDD (inverted) 40% + ESRS E4 20%
        """
        eudr_weight = 0.40
        csddd_weight = 0.40   # csddd_dd_score is compliance (invert)
        esrs_weight = 0.20

        eudr_component = r.eudr_risk_score * eudr_weight
        csddd_component = (100.0 - r.csddd_dd_score) * csddd_weight
        esrs_component = (
            {"high": 75.0, "medium": 45.0, "low": 15.0, "not_assessed": 50.0}.get(
                r.esrs_e4_biodiversity_risk, 50.0
            )
            * esrs_weight
        )

        return round(eudr_component + csddd_component + esrs_component, 1)

    # ── Gap & Action Builders ──────────────────────────────────────────────

    def _build_gaps(self, r: SupplierRiskResult, s: SupplierInput) -> List[str]:
        gaps = []
        if r.eudr_commodity_covered and not s.has_geolocation:
            gaps.append(
                f"[EUDR Art.9] Missing geolocation data for {s.commodity} from {s.country_of_origin}"
            )
        if r.eudr_commodity_covered and not s.has_traceability_system:
            gaps.append(
                "[EUDR Art.9(1)(a)] No traceability system — cannot demonstrate supply chain mapping"
            )
        if r.eudr_country_risk_tier == "high" and not s.certification_scheme:
            gaps.append(
                "[EUDR Art.9(1)(c)] High-risk country sourcing without recognised certification scheme"
            )
        if not s.has_supplier_code_of_conduct:
            gaps.append(
                "[CSDDD Art.8] No supplier code of conduct — prevention measures incomplete"
            )
        if not s.has_audit_programme:
            gaps.append(
                "[CSDDD Art.8(3)] No supplier audit programme — verification of prevention missing"
            )
        if not s.has_grievance_mechanism:
            gaps.append(
                "[CSDDD Art.9] No grievance mechanism accessible to affected persons"
            )
        if not s.has_biodiversity_impact_assessment and s.operates_in_sensitive_area:
            gaps.append(
                "[ESRS E4-5] No biodiversity impact assessment despite operations in sensitive area"
            )
        if s.operates_in_sensitive_area and not s.restoration_commitments:
            gaps.append(
                "[ESRS E4-3/E4-4] No restoration commitments in/near sensitive biodiversity area"
            )
        return gaps

    def _build_actions(
        self, r: SupplierRiskResult, s: SupplierInput
    ) -> List[Dict[str, str]]:
        actions = []
        if r.eudr_commodity_covered and not s.has_geolocation:
            actions.append({
                "priority": "critical",
                "action": "Obtain plot-level GPS coordinates from supplier",
                "regulation": "EUDR Art.9(1)(a)",
                "deadline": "2025-12-30",
                "module": "eudr_engine",
            })
        if not s.has_traceability_system:
            actions.append({
                "priority": "high",
                "action": "Implement supply chain traceability system (e.g. blockchain, GS1)",
                "regulation": "EUDR Art.9 + CSDDD Art.8",
                "deadline": "2026-06-30",
                "module": "supply_chain_workflow",
            })
        if not s.has_supplier_code_of_conduct:
            actions.append({
                "priority": "high",
                "action": "Issue supplier code of conduct covering CSDDD adverse impact categories",
                "regulation": "CSDDD Art.8(3)(a)",
                "deadline": "2026-03-31",
                "module": "csddd_engine",
            })
        if not s.has_audit_programme:
            actions.append({
                "priority": "medium",
                "action": "Establish supplier audit programme with annual verification cycle",
                "regulation": "CSDDD Art.8(3)(b)",
                "deadline": "2026-06-30",
                "module": "csddd_engine",
            })
        if not s.has_grievance_mechanism:
            actions.append({
                "priority": "medium",
                "action": "Deploy accessible grievance mechanism (whistle-blower channel / web form)",
                "regulation": "CSDDD Art.9",
                "deadline": "2026-09-30",
                "module": "csddd_engine",
            })
        if s.operates_in_sensitive_area and not s.has_biodiversity_impact_assessment:
            actions.append({
                "priority": "high",
                "action": "Commission biodiversity impact assessment (TNFD LEAP / BNG Metric 4.0)",
                "regulation": "ESRS E4-5",
                "deadline": "2025-12-31",
                "module": "tnfd_assessment + agriculture_bng",
            })
        return actions

    # ── Portfolio Aggregation ──────────────────────────────────────────────

    def _aggregate(
        self,
        run_id: str,
        entity_name: str,
        assessment_date: str,
        supplier_results: List[SupplierRiskResult],
        suppliers: List[SupplierInput],
    ) -> WorkflowAssessment:
        high_risk = sum(1 for r in supplier_results if r.supplier_status == "high_risk")
        medium_risk = sum(1 for r in supplier_results if r.supplier_status == "needs_review")
        low_risk = sum(1 for r in supplier_results if r.supplier_status == "compliant")

        all_gaps = []
        critical_gaps = []
        priority_actions: List[Dict[str, str]] = []
        for r in supplier_results:
            all_gaps.extend(r.gaps)
            critical_gaps.extend(
                [g for g in r.gaps if "EUDR Art.9" in g or "critical" in g.lower()]
            )
            priority_actions.extend(
                [a for a in r.recommended_actions if a.get("priority") in ("critical", "high")]
            )

        # De-duplicate actions by action text
        seen_actions: set = set()
        deduped_actions = []
        for a in priority_actions:
            key = a.get("action", "")
            if key not in seen_actions:
                seen_actions.add(key)
                deduped_actions.append(a)

        # Overall workflow score: 100 − (avg individual risk scores)
        avg_risk = (
            sum(r.overall_risk_score for r in supplier_results) / len(supplier_results)
            if supplier_results else 0.0
        )
        workflow_score = round(100.0 - avg_risk, 1)

        status = (
            "compliant" if workflow_score >= 75
            else "non_compliant" if workflow_score < 45
            else "partial"
        )

        # ESRS E4 disclosure readiness: aggregate flags across all suppliers
        e4_all_triggered: Dict[str, int] = {dp: 0 for dp in _ESRS_E4_DISCLOSURES}
        for r in supplier_results:
            for dp, triggered in r.esrs_e4_disclosure_flags.items():
                if triggered:
                    e4_all_triggered[dp] += 1

        esrs_e4_readiness = {
            dp: {
                "description": _ESRS_E4_DISCLOSURES[dp],
                "triggered_by_supplier_count": count,
                "disclosure_required": count > 0,
            }
            for dp, count in e4_all_triggered.items()
        }

        commodities = list({s.commodity.lower() for s in suppliers})

        return WorkflowAssessment(
            run_id=run_id,
            entity_name=entity_name,
            assessment_date=assessment_date,
            supplier_count=len(supplier_results),
            commodity_count=len(commodities),
            overall_workflow_score=workflow_score,
            workflow_status=status,
            supplier_results=supplier_results,
            high_risk_suppliers=high_risk,
            medium_risk_suppliers=medium_risk,
            low_risk_suppliers=low_risk,
            total_gaps=len(all_gaps),
            critical_gaps=list(set(critical_gaps)),
            priority_actions=deduped_actions,
            regulatory_mapping=_REGULATORY_MAPPING,
            esrs_e4_disclosure_readiness=esrs_e4_readiness,
            metadata={
                "run_id": run_id,
                "engine_version": "E5-1.0",
                "frameworks_applied": ["EUDR_2023/1115", "CSDDD_2024/1760", "ESRS_E4"],
                "commodities_screened": commodities,
                "eudr_engine_available": _EUDR_AVAILABLE,
                "csddd_engine_available": _CSDDD_AVAILABLE,
                "assessment_date": assessment_date,
                "note": (
                    "Scores are computed from supplier-provided signals. "
                    "Physical geolocation verification and third-party audit "
                    "results may further adjust risk classifications."
                ),
            },
        )
