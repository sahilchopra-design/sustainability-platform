"""
RICS Red Book ESG Integration Engine
=======================================
Gap 5.2.7 — RICS Professional Standards compliance for ESG valuation:

1. RICS PS 1 (Terms of Engagement) — ESG disclosure checklist
2. RICS PS 2 (Ethical Standards, Independence) — conflict of interest register
3. RICS VPS 1–5 (Valuation Standards) — ESG-adjusted valuation narrative
4. RICS VPS 4 (Bases of Value) — ESG factor documentation
5. RICS VPGA 12 (ESG Sustainability) — materiality assessment
6. RICS VPG3 — Uncertainty in valuations guidance
7. IVSC IVS 104/400 — ESG factor integration commentary

The engine produces a structured narrative and compliance checklist that
accompanies each real estate valuation, ensuring the valuation report meets
RICS Red Book standards for ESG disclosure and adjustment.

References:
  - RICS Valuation — Global Standards ("Red Book") effective 31 Jan 2022
  - RICS Professional Statement: ESG and Sustainability (2024 draft)
  - IVSC International Valuation Standards (IVS) 2024 — IVS 104 (Bases), IVS 400 (Real Property)
  - RICS VPGA 12: Valuation of properties in the context of ESG and sustainability
  - RICS VPG3: Dealing with uncertainty in valuation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("platform.rics_esg")


# ---------------------------------------------------------------------------
# RICS Compliance Checklist Templates
# ---------------------------------------------------------------------------

PS1_CHECKLIST: list[dict[str, Any]] = [
    {"item_id": "PS1-01", "section": "PS 1 — Terms of Engagement",
     "requirement": "Confirm scope of ESG considerations in engagement letter",
     "guidance": "State whether sustainability factors will be explicitly reflected in the valuation",
     "mandatory": True},
    {"item_id": "PS1-02", "section": "PS 1 — Terms of Engagement",
     "requirement": "Identify ESG data sources and their reliability",
     "guidance": "Specify EPC register, GRESB, CRREM, or other ESG datasets to be used",
     "mandatory": True},
    {"item_id": "PS1-03", "section": "PS 1 — Terms of Engagement",
     "requirement": "Disclose any limitations on ESG data availability",
     "guidance": "Flag data gaps (e.g., no metered energy data, no flood risk assessment)",
     "mandatory": True},
    {"item_id": "PS1-04", "section": "PS 1 — Terms of Engagement",
     "requirement": "Agree reporting requirements for ESG narrative",
     "guidance": "Confirm whether a standalone ESG annex is required",
     "mandatory": False},
]

PS2_CHECKLIST: list[dict[str, Any]] = [
    {"item_id": "PS2-01", "section": "PS 2 — Ethics and Independence",
     "requirement": "Declare any conflicts of interest related to green certification",
     "guidance": "Disclose if valuer has connection to BREEAM/LEED assessor or developer",
     "mandatory": True},
    {"item_id": "PS2-02", "section": "PS 2 — Ethics and Independence",
     "requirement": "Confirm valuer competence in ESG valuation matters",
     "guidance": "Demonstrate CPD in sustainability valuation (VPGA 12)",
     "mandatory": True},
]

VPS4_CHECKLIST: list[dict[str, Any]] = [
    {"item_id": "VPS4-01", "section": "VPS 4 — Bases of Value",
     "requirement": "State the basis of value and its relationship to ESG factors",
     "guidance": "Market Value (IVSC IVS 104 §30.1) — ESG reflected in market participant assumptions",
     "mandatory": True},
    {"item_id": "VPS4-02", "section": "VPS 4 — Bases of Value",
     "requirement": "Document ESG factors considered in comparable selection",
     "guidance": "Energy performance, green certification, flood risk, proximity to transport",
     "mandatory": True},
    {"item_id": "VPS4-03", "section": "VPS 4 — Bases of Value",
     "requirement": "Quantify ESG adjustments applied to value",
     "guidance": "State green premium/brown discount as %, with market evidence",
     "mandatory": True},
    {"item_id": "VPS4-04", "section": "VPS 4 — Bases of Value",
     "requirement": "Identify transition risk impact on value",
     "guidance": "EPC stranding risk, MEES compliance timeline, retrofit capex liability",
     "mandatory": True},
    {"item_id": "VPS4-05", "section": "VPS 4 — Bases of Value",
     "requirement": "Identify physical risk impact on value",
     "guidance": "Flood risk, heat stress, subsidence — quantified discount or qualitative note",
     "mandatory": True},
]

VPGA12_CHECKLIST: list[dict[str, Any]] = [
    {"item_id": "VPGA12-01", "section": "VPGA 12 — ESG and Sustainability",
     "requirement": "Conduct materiality assessment of ESG factors",
     "guidance": "Determine which E, S, G factors are material to the specific property/market",
     "mandatory": True},
    {"item_id": "VPGA12-02", "section": "VPGA 12 — ESG and Sustainability",
     "requirement": "Assess environmental factors: energy, carbon, water, biodiversity",
     "guidance": "EPC rating, Scope 1+2 emissions, water consumption, proximity to protected areas",
     "mandatory": True},
    {"item_id": "VPGA12-03", "section": "VPGA 12 — ESG and Sustainability",
     "requirement": "Assess social factors: health, wellbeing, community impact",
     "guidance": "Indoor air quality, daylight, accessibility, social value of affordable housing",
     "mandatory": True},
    {"item_id": "VPGA12-04", "section": "VPGA 12 — ESG and Sustainability",
     "requirement": "Assess governance factors: management, transparency, compliance",
     "guidance": "Building management certification, regulatory compliance history",
     "mandatory": True},
    {"item_id": "VPGA12-05", "section": "VPGA 12 — ESG and Sustainability",
     "requirement": "Document CRREM pathway alignment or stranding risk",
     "guidance": "Current energy intensity vs. CRREM 1.5°C pathway, projected stranding year",
     "mandatory": True},
    {"item_id": "VPGA12-06", "section": "VPGA 12 — ESG and Sustainability",
     "requirement": "Provide green building certification impact analysis",
     "guidance": "BREEAM/LEED/NABERS/WELL rating and its impact on rental/capital value",
     "mandatory": False},
]

VPG3_CHECKLIST: list[dict[str, Any]] = [
    {"item_id": "VPG3-01", "section": "VPG3 — Uncertainty in Valuations",
     "requirement": "State degree of uncertainty in ESG-related value adjustments",
     "guidance": "High uncertainty: limited market evidence for green premium; Medium: some transactions",
     "mandatory": True},
    {"item_id": "VPG3-02", "section": "VPG3 — Uncertainty in Valuations",
     "requirement": "Provide uncertainty range for valuation figure",
     "guidance": "±X% reflecting ESG data quality and market evidence availability",
     "mandatory": True},
    {"item_id": "VPG3-03", "section": "VPG3 — Uncertainty in Valuations",
     "requirement": "Distinguish between valuation uncertainty and market risk",
     "guidance": "Uncertainty in inputs (data quality) vs. market volatility (price movements)",
     "mandatory": True},
]

IVS_CHECKLIST: list[dict[str, Any]] = [
    {"item_id": "IVS104-01", "section": "IVS 104 — Bases of Value",
     "requirement": "ESG factors reflected in Market Value per IVS 104 §30",
     "guidance": "Market participants would consider ESG in their assessment of price",
     "mandatory": True},
    {"item_id": "IVS400-01", "section": "IVS 400 — Real Property Interests",
     "requirement": "Physical and environmental characteristics documented per IVS 400 §20",
     "guidance": "Location, environmental conditions, sustainability attributes",
     "mandatory": True},
    {"item_id": "IVS400-02", "section": "IVS 400 — Real Property Interests",
     "requirement": "Highest and best use analysis considers ESG constraints",
     "guidance": "Regulatory constraints (MEES, flood zones), physical limitations",
     "mandatory": True},
]

ALL_CHECKLISTS = {
    "PS1": PS1_CHECKLIST,
    "PS2": PS2_CHECKLIST,
    "VPS4": VPS4_CHECKLIST,
    "VPGA12": VPGA12_CHECKLIST,
    "VPG3": VPG3_CHECKLIST,
    "IVS": IVS_CHECKLIST,
}


# ---------------------------------------------------------------------------
# ESG Materiality Categories
# ---------------------------------------------------------------------------

MATERIALITY_FACTORS: dict[str, list[dict]] = {
    "environmental": [
        {"factor": "Energy performance (EPC rating)", "data_source": "EPC Register", "weight": 0.25},
        {"factor": "Carbon emissions (Scope 1+2)", "data_source": "CRREM / GHG Protocol", "weight": 0.20},
        {"factor": "Flood risk exposure", "data_source": "EA Flood Map / Fathom", "weight": 0.15},
        {"factor": "Heat stress / overheating risk", "data_source": "CIBSE TM59", "weight": 0.10},
        {"factor": "Water consumption", "data_source": "Metered / BREEAM Wat", "weight": 0.05},
        {"factor": "Biodiversity / nature proximity", "data_source": "WDPA / Natura 2000", "weight": 0.05},
        {"factor": "Green certification", "data_source": "BREEAM / LEED / NABERS", "weight": 0.10},
        {"factor": "CRREM pathway alignment", "data_source": "CRREM v2.3", "weight": 0.10},
    ],
    "social": [
        {"factor": "Indoor air quality / ventilation", "data_source": "WELL Standard", "weight": 0.25},
        {"factor": "Daylight / thermal comfort", "data_source": "CIBSE Guide A", "weight": 0.20},
        {"factor": "Accessibility (DDA / Part M)", "data_source": "Building regs", "weight": 0.15},
        {"factor": "Community impact / amenity", "data_source": "Planning authority", "weight": 0.15},
        {"factor": "Tenant satisfaction", "data_source": "GRESB / survey", "weight": 0.15},
        {"factor": "Health and safety compliance", "data_source": "H&S records", "weight": 0.10},
    ],
    "governance": [
        {"factor": "Building management certification", "data_source": "ISO 14001 / ISO 50001", "weight": 0.30},
        {"factor": "Regulatory compliance history", "data_source": "LA records", "weight": 0.25},
        {"factor": "ESG disclosure / reporting", "data_source": "GRESB submission", "weight": 0.20},
        {"factor": "Maintenance programme quality", "data_source": "Planned maintenance log", "weight": 0.15},
        {"factor": "Data transparency / metering", "data_source": "BMS / smart metering", "weight": 0.10},
    ],
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class RICSComplianceInput:
    """Input for RICS ESG compliance assessment."""
    property_id: str
    property_type: str = "office"
    country: str = "GB"
    valuation_purpose: str = "market_value"  # market_value | fair_value | investment_value
    # ESG data available
    epc_rating: str | None = None
    epc_score: float | None = None
    green_certification: str | None = None     # BREEAM Excellent, LEED Gold, etc.
    green_cert_level: str | None = None
    energy_kwh_m2_yr: float | None = None
    scope12_tco2e: float | None = None
    crrem_stranding_year: int | None = None
    flood_risk_zone: str | None = None         # none | low | medium | high
    heat_risk_score: float | None = None       # 0-100
    biodiversity_proximity: bool = False
    indoor_air_quality: str | None = None      # good | moderate | poor
    accessibility_compliant: bool = True
    iso14001_certified: bool = False
    gresb_score: float | None = None
    # Valuation adjustments applied
    green_premium_pct: float | None = None
    brown_discount_pct: float | None = None
    transition_risk_adjustment_pct: float | None = None
    physical_risk_adjustment_pct: float | None = None
    # Comparable evidence
    num_esg_comparables: int = 0
    comparable_evidence_quality: str = "limited"  # strong | moderate | limited | none


@dataclass
class ChecklistItem:
    item_id: str
    section: str
    requirement: str
    guidance: str
    mandatory: bool
    status: str = "not_assessed"  # compliant | partially_compliant | non_compliant | not_assessed | not_applicable
    evidence: str = ""
    notes: str = ""


@dataclass
class RICSComplianceResult:
    property_id: str
    # Compliance scores
    total_items: int = 0
    compliant_count: int = 0
    partial_count: int = 0
    non_compliant_count: int = 0
    not_assessed_count: int = 0
    compliance_pct: float = 0
    compliance_band: str = ""  # full | substantial | partial | non_compliant
    # Checklist detail
    checklist: list[dict] = field(default_factory=list)
    # ESG narrative
    esg_narrative: str = ""
    # Materiality assessment
    materiality_scores: dict[str, float] = field(default_factory=dict)
    material_factors: list[str] = field(default_factory=list)
    # Uncertainty assessment
    uncertainty_pct: float = 0
    uncertainty_band: str = ""  # low | medium | high | very_high
    uncertainty_narrative: str = ""
    # Recommendations
    recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RICSESGEngine:
    """RICS Red Book ESG compliance assessment and narrative generation."""

    def assess_compliance(self, inp: RICSComplianceInput) -> RICSComplianceResult:
        """
        Run full RICS ESG compliance assessment:
          1. Auto-assess each checklist item based on available data
          2. Generate ESG valuation narrative (VPS 4 / VPGA 12)
          3. Conduct materiality assessment
          4. Assess uncertainty (VPG3)
        """
        # 1. Build and auto-assess checklist
        checklist = self._auto_assess_checklist(inp)

        # Count statuses
        statuses = [c.status for c in checklist]
        compliant = statuses.count("compliant")
        partial = statuses.count("partially_compliant")
        non_comp = statuses.count("non_compliant")
        not_ass = statuses.count("not_assessed")
        total = len(checklist)
        mandatory_items = [c for c in checklist if c.mandatory]
        mandatory_compliant = sum(1 for c in mandatory_items if c.status == "compliant")

        comp_pct = round(compliant / total * 100, 1) if total else 0
        if comp_pct >= 90 and non_comp == 0:
            band = "full"
        elif comp_pct >= 70:
            band = "substantial"
        elif comp_pct >= 40:
            band = "partial"
        else:
            band = "non_compliant"

        # 2. Materiality assessment
        mat_scores, material_list = self._materiality_assessment(inp)

        # 3. ESG narrative
        narrative = self._generate_narrative(inp, mat_scores, material_list)

        # 4. Uncertainty assessment
        unc_pct, unc_band, unc_narrative = self._assess_uncertainty(inp)

        # 5. Recommendations
        recs = self._generate_recommendations(inp, checklist, mat_scores)

        return RICSComplianceResult(
            property_id=inp.property_id,
            total_items=total,
            compliant_count=compliant,
            partial_count=partial,
            non_compliant_count=non_comp,
            not_assessed_count=not_ass,
            compliance_pct=comp_pct,
            compliance_band=band,
            checklist=[{
                "item_id": c.item_id,
                "section": c.section,
                "requirement": c.requirement,
                "guidance": c.guidance,
                "mandatory": c.mandatory,
                "status": c.status,
                "evidence": c.evidence,
                "notes": c.notes,
            } for c in checklist],
            esg_narrative=narrative,
            materiality_scores=mat_scores,
            material_factors=material_list,
            uncertainty_pct=unc_pct,
            uncertainty_band=unc_band,
            uncertainty_narrative=unc_narrative,
            recommendations=recs,
        )

    def get_full_checklist(self) -> dict[str, list[dict]]:
        """Return all RICS ESG checklist templates."""
        return dict(ALL_CHECKLISTS)

    def get_materiality_factors(self) -> dict[str, list[dict]]:
        """Return ESG materiality factor catalogue."""
        return dict(MATERIALITY_FACTORS)

    # ── Internal: Auto-assess checklist ───────────────────────────────────

    def _auto_assess_checklist(self, inp: RICSComplianceInput) -> list[ChecklistItem]:
        items: list[ChecklistItem] = []

        for section_name, template_list in ALL_CHECKLISTS.items():
            for t in template_list:
                ci = ChecklistItem(
                    item_id=t["item_id"],
                    section=t["section"],
                    requirement=t["requirement"],
                    guidance=t["guidance"],
                    mandatory=t["mandatory"],
                )
                # Auto-assess based on available data
                self._assess_item(ci, inp)
                items.append(ci)

        return items

    def _assess_item(self, ci: ChecklistItem, inp: RICSComplianceInput) -> None:
        """Auto-populate status and evidence based on input data."""
        iid = ci.item_id

        # PS1 — Terms of Engagement
        if iid == "PS1-02":
            sources = []
            if inp.epc_rating:
                sources.append("EPC Register")
            if inp.green_certification:
                sources.append(inp.green_certification)
            if inp.gresb_score is not None:
                sources.append("GRESB")
            if inp.crrem_stranding_year is not None:
                sources.append("CRREM v2.3")
            if sources:
                ci.status = "compliant"
                ci.evidence = f"Data sources identified: {', '.join(sources)}"
            else:
                ci.status = "non_compliant"
                ci.notes = "No ESG data sources available"

        elif iid == "PS1-03":
            gaps = []
            if not inp.epc_rating:
                gaps.append("No EPC rating")
            if inp.energy_kwh_m2_yr is None:
                gaps.append("No metered energy data")
            if inp.flood_risk_zone is None:
                gaps.append("No flood risk assessment")
            if gaps:
                ci.status = "compliant"
                ci.evidence = f"Data gaps disclosed: {'; '.join(gaps)}"
            else:
                ci.status = "compliant"
                ci.evidence = "Full ESG data coverage — no material limitations"

        # VPS4 — ESG adjustments
        elif iid == "VPS4-03":
            adjustments = []
            if inp.green_premium_pct is not None:
                adjustments.append(f"Green premium: +{inp.green_premium_pct}%")
            if inp.brown_discount_pct is not None:
                adjustments.append(f"Brown discount: {inp.brown_discount_pct}%")
            if adjustments:
                ci.status = "compliant"
                ci.evidence = "; ".join(adjustments)
            elif inp.epc_rating and inp.num_esg_comparables > 0:
                ci.status = "partially_compliant"
                ci.notes = "ESG data available but adjustments not yet quantified"
            else:
                ci.status = "non_compliant"
                ci.notes = "No ESG adjustments documented"

        elif iid == "VPS4-04":
            if inp.crrem_stranding_year is not None or inp.transition_risk_adjustment_pct is not None:
                ci.status = "compliant"
                evidence_parts = []
                if inp.crrem_stranding_year:
                    evidence_parts.append(f"CRREM stranding: {inp.crrem_stranding_year}")
                if inp.transition_risk_adjustment_pct:
                    evidence_parts.append(f"Transition adjustment: {inp.transition_risk_adjustment_pct}%")
                ci.evidence = "; ".join(evidence_parts)
            elif inp.epc_rating:
                ci.status = "partially_compliant"
                ci.notes = "EPC available but transition risk not quantified"
            else:
                ci.status = "non_compliant"

        elif iid == "VPS4-05":
            if inp.flood_risk_zone and inp.flood_risk_zone != "none":
                if inp.physical_risk_adjustment_pct is not None:
                    ci.status = "compliant"
                    ci.evidence = f"Flood zone: {inp.flood_risk_zone}, adjustment: {inp.physical_risk_adjustment_pct}%"
                else:
                    ci.status = "partially_compliant"
                    ci.notes = f"Flood zone identified ({inp.flood_risk_zone}) but not quantified"
            elif inp.flood_risk_zone == "none":
                ci.status = "compliant"
                ci.evidence = "No material physical risk identified"
            else:
                ci.status = "non_compliant"
                ci.notes = "Physical risk not assessed"

        # VPGA12 — ESG materiality
        elif iid == "VPGA12-02":
            env_data = sum([
                1 if inp.epc_rating else 0,
                1 if inp.energy_kwh_m2_yr else 0,
                1 if inp.scope12_tco2e else 0,
                1 if inp.flood_risk_zone else 0,
                1 if inp.crrem_stranding_year else 0,
            ])
            if env_data >= 3:
                ci.status = "compliant"
                ci.evidence = f"Environmental data coverage: {env_data}/5 key metrics"
            elif env_data >= 1:
                ci.status = "partially_compliant"
                ci.evidence = f"Partial environmental data: {env_data}/5 metrics"
            else:
                ci.status = "non_compliant"

        elif iid == "VPGA12-05":
            if inp.crrem_stranding_year is not None:
                ci.status = "compliant"
                ci.evidence = f"CRREM stranding year: {inp.crrem_stranding_year}"
            elif inp.energy_kwh_m2_yr:
                ci.status = "partially_compliant"
                ci.notes = "Energy data available but CRREM pathway not applied"
            else:
                ci.status = "non_compliant"

        # VPG3 — Uncertainty
        elif iid == "VPG3-01":
            if inp.comparable_evidence_quality in ("strong", "moderate"):
                ci.status = "compliant"
                ci.evidence = f"ESG comparable evidence: {inp.comparable_evidence_quality}"
            else:
                ci.status = "partially_compliant"
                ci.notes = f"Evidence quality: {inp.comparable_evidence_quality}"

        elif iid == "VPG3-02":
            if inp.comparable_evidence_quality == "strong" and inp.num_esg_comparables >= 5:
                ci.status = "compliant"
                ci.evidence = f"Uncertainty range stated with {inp.num_esg_comparables} comparables"
            elif inp.num_esg_comparables > 0:
                ci.status = "partially_compliant"
                ci.notes = f"Only {inp.num_esg_comparables} ESG-adjusted comparables"
            else:
                ci.status = "non_compliant"
                ci.notes = "No ESG-adjusted comparables for uncertainty range"

        # Default: mark as compliant if it's a general procedural item (PS1-01, PS1-04, PS2-01, PS2-02, etc.)
        elif ci.status == "not_assessed":
            ci.status = "compliant"
            ci.evidence = "Procedural compliance assumed — manual review recommended"

    # ── Internal: Materiality Assessment ──────────────────────────────────

    def _materiality_assessment(self, inp: RICSComplianceInput) -> tuple[dict[str, float], list[str]]:
        scores: dict[str, float] = {}
        material: list[str] = []

        for pillar, factors in MATERIALITY_FACTORS.items():
            pillar_score = 0.0
            for f in factors:
                data_available = self._check_data_available(f["factor"], inp)
                score = f["weight"] * (1.0 if data_available else 0.3)
                pillar_score += score
                if data_available and f["weight"] >= 0.15:
                    material.append(f["factor"])
            scores[pillar] = round(pillar_score, 3)

        return scores, material

    def _check_data_available(self, factor_name: str, inp: RICSComplianceInput) -> bool:
        checks = {
            "Energy performance (EPC rating)": inp.epc_rating is not None,
            "Carbon emissions (Scope 1+2)": inp.scope12_tco2e is not None,
            "Flood risk exposure": inp.flood_risk_zone is not None,
            "Heat stress / overheating risk": inp.heat_risk_score is not None,
            "Water consumption": False,  # not in input
            "Biodiversity / nature proximity": inp.biodiversity_proximity,
            "Green certification": inp.green_certification is not None,
            "CRREM pathway alignment": inp.crrem_stranding_year is not None,
            "Indoor air quality / ventilation": inp.indoor_air_quality is not None,
            "Daylight / thermal comfort": False,
            "Accessibility (DDA / Part M)": True,
            "Community impact / amenity": False,
            "Tenant satisfaction": inp.gresb_score is not None,
            "Health and safety compliance": True,
            "Building management certification": inp.iso14001_certified,
            "Regulatory compliance history": True,
            "ESG disclosure / reporting": inp.gresb_score is not None,
            "Maintenance programme quality": False,
            "Data transparency / metering": inp.energy_kwh_m2_yr is not None,
        }
        return checks.get(factor_name, False)

    # ── Internal: ESG Narrative ───────────────────────────────────────────

    def _generate_narrative(
        self,
        inp: RICSComplianceInput,
        mat_scores: dict[str, float],
        material: list[str],
    ) -> str:
        """Generate RICS-compliant ESG valuation narrative per VPS 4 and VPGA 12."""
        sections = []

        sections.append(
            "ESG VALUATION NARRATIVE (per RICS VPS 4 / VPGA 12)\n" + "=" * 55
        )

        # Basis of value
        basis_map = {
            "market_value": "Market Value (IVS 104 §30.1)",
            "fair_value": "Fair Value (IFRS 13)",
            "investment_value": "Investment Value (IVS 104 §60.1)",
        }
        sections.append(
            f"\n1. Basis of Value: {basis_map.get(inp.valuation_purpose, inp.valuation_purpose)}\n"
            f"   ESG factors are reflected in the adopted basis as market participants\n"
            f"   would reasonably consider sustainability characteristics."
        )

        # Environmental factors
        env_parts = []
        if inp.epc_rating:
            env_parts.append(f"EPC Rating: {inp.epc_rating}")
        if inp.energy_kwh_m2_yr:
            env_parts.append(f"Energy Intensity: {inp.energy_kwh_m2_yr} kWh/m²/yr")
        if inp.crrem_stranding_year:
            env_parts.append(f"CRREM Stranding Year: {inp.crrem_stranding_year}")
        if inp.green_certification:
            cert = inp.green_certification
            if inp.green_cert_level:
                cert += f" ({inp.green_cert_level})"
            env_parts.append(f"Green Certification: {cert}")
        if inp.flood_risk_zone:
            env_parts.append(f"Flood Risk Zone: {inp.flood_risk_zone}")

        sections.append(
            f"\n2. Environmental Factors (weight: {mat_scores.get('environmental', 0):.1%} materiality)\n"
            + ("\n".join(f"   - {p}" for p in env_parts) if env_parts else "   - No environmental data available")
        )

        # Adjustments
        adj_parts = []
        if inp.green_premium_pct:
            adj_parts.append(f"Green premium: +{inp.green_premium_pct}% (market evidence)")
        if inp.brown_discount_pct:
            adj_parts.append(f"Brown discount: {inp.brown_discount_pct}% (sub-EPC-D penalty)")
        if inp.transition_risk_adjustment_pct:
            adj_parts.append(f"Transition risk: {inp.transition_risk_adjustment_pct}% (EPC/CRREM stranding)")
        if inp.physical_risk_adjustment_pct:
            adj_parts.append(f"Physical risk: {inp.physical_risk_adjustment_pct}% (flood/heat)")

        sections.append(
            "\n3. ESG Adjustments Applied\n"
            + ("\n".join(f"   - {a}" for a in adj_parts) if adj_parts else "   - No explicit ESG adjustments applied")
        )

        # Material factors
        sections.append(
            "\n4. Material ESG Factors (VPGA 12 Materiality Assessment)\n"
            + ("\n".join(f"   - {f}" for f in material) if material else "   - No material ESG factors identified")
        )

        # Comparable evidence
        sections.append(
            f"\n5. Comparable Evidence\n"
            f"   ESG-adjusted comparables: {inp.num_esg_comparables}\n"
            f"   Evidence quality: {inp.comparable_evidence_quality}"
        )

        return "\n".join(sections)

    # ── Internal: Uncertainty Assessment ──────────────────────────────────

    def _assess_uncertainty(self, inp: RICSComplianceInput) -> tuple[float, str, str]:
        """VPG3 uncertainty assessment."""
        base_unc = 10.0  # baseline ±10%

        # ESG data quality factors
        if inp.epc_rating is None:
            base_unc += 3
        if inp.energy_kwh_m2_yr is None:
            base_unc += 2
        if inp.flood_risk_zone is None:
            base_unc += 2
        if inp.crrem_stranding_year is None:
            base_unc += 1.5

        # Comparable evidence quality
        evidence_adj = {
            "strong": -3, "moderate": 0, "limited": 3, "none": 7,
        }
        base_unc += evidence_adj.get(inp.comparable_evidence_quality, 3)

        # Number of ESG comparables
        if inp.num_esg_comparables >= 10:
            base_unc -= 2
        elif inp.num_esg_comparables >= 5:
            base_unc -= 1
        elif inp.num_esg_comparables == 0:
            base_unc += 3

        unc_pct = round(max(5, min(30, base_unc)), 1)

        if unc_pct <= 10:
            band = "low"
        elif unc_pct <= 15:
            band = "medium"
        elif unc_pct <= 20:
            band = "high"
        else:
            band = "very_high"

        narrative = (
            f"UNCERTAINTY ASSESSMENT (per RICS VPG3)\n"
            f"Estimated valuation uncertainty: ±{unc_pct}% ({band})\n"
            f"ESG-adjusted comparables: {inp.num_esg_comparables} ({inp.comparable_evidence_quality} evidence)\n"
            f"This uncertainty reflects the quality of ESG data inputs and the availability "
            f"of market evidence for ESG-related value adjustments."
        )

        return unc_pct, band, narrative

    # ── Internal: Recommendations ─────────────────────────────────────────

    def _generate_recommendations(
        self,
        inp: RICSComplianceInput,
        checklist: list[ChecklistItem],
        mat_scores: dict[str, float],
    ) -> list[str]:
        recs = []
        non_compliant = [c for c in checklist if c.status == "non_compliant" and c.mandatory]
        if non_compliant:
            recs.append(
                f"{len(non_compliant)} mandatory RICS checklist items are non-compliant — "
                "address before finalising valuation report"
            )
        if inp.epc_rating is None:
            recs.append("Obtain EPC rating — required for VPGA 12 environmental assessment")
        if inp.crrem_stranding_year is None and inp.energy_kwh_m2_yr:
            recs.append("Run CRREM pathway analysis to determine stranding year")
        if inp.num_esg_comparables < 3:
            recs.append("Increase ESG-adjusted comparable evidence (minimum 3 recommended)")
        if inp.flood_risk_zone is None:
            recs.append("Conduct flood risk assessment (EA Flood Map / JBA / Fathom)")
        if mat_scores.get("governance", 0) < 0.5:
            recs.append("Improve governance data: consider ISO 14001/50001 certification status")
        return recs
