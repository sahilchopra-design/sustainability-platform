"""
Sustainability-Linked Finance Engine (E17)
==========================================

ICMA Sustainability-Linked Bond Principles (2023) +
LMA/APLMA/LSTA Sustainability-Linked Loan Principles (2023).

Covers:
  - KPI selection framework (SMART criteria)
  - SPT calibration against science-based benchmarks
  - Coupon / margin adjustment mechanics (step-up triggered on SPT miss)
  - Second Party Opinion (SPO) requirements
  - ICMA 5-component SLB compliance check
  - LMA 5-component SLL compliance check
  - Batch assessment for bond/loan programmes
  - Cross-framework: CSRD ESRS, SBTi, TCFD, GRI, EU Taxonomy

E17 in the engine series.
"""
from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

KPI_LIBRARY: Dict[str, Any] = {
    "ghg_scope1_2_intensity": {
        "id": "ghg_scope1_2_intensity",
        "name": "GHG Scope 1+2 Intensity",
        "unit": "tCO2e/unit",
        "category": "environmental",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 25,
        "benchmark_sources": ["SBTi", "IEA sector pathways", "CRREM"],
    },
    "ghg_scope3_intensity": {
        "id": "ghg_scope3_intensity",
        "name": "GHG Scope 3 Intensity",
        "unit": "tCO2e/unit",
        "category": "environmental",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 20,
        "benchmark_sources": ["PCAF", "CDP"],
    },
    "renewable_energy_pct": {
        "id": "renewable_energy_pct",
        "name": "Renewable Energy Consumption %",
        "unit": "%",
        "category": "environmental",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 20,
        "benchmark_sources": ["RE100", "IEA"],
    },
    "water_intensity": {
        "id": "water_intensity",
        "name": "Water Intensity",
        "unit": "m3/unit",
        "category": "environmental",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 15,
        "benchmark_sources": ["AWS", "CDP Water Security"],
    },
    "waste_recycling_pct": {
        "id": "waste_recycling_pct",
        "name": "Waste Recycling/Reuse Rate",
        "unit": "%",
        "category": "environmental",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 10,
        "benchmark_sources": ["EU Circular Economy Action Plan"],
    },
    "women_in_leadership_pct": {
        "id": "women_in_leadership_pct",
        "name": "Women in Leadership %",
        "unit": "%",
        "category": "social",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 10,
        "benchmark_sources": ["30% Club", "WEF Gender Parity"],
    },
    "employee_injury_rate": {
        "id": "employee_injury_rate",
        "name": "Total Recordable Injury Rate",
        "unit": "per 200k hours",
        "category": "social",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 20,
        "benchmark_sources": ["OSHA", "ISO 45001"],
    },
    "supply_chain_sustainability_pct": {
        "id": "supply_chain_sustainability_pct",
        "name": "Sustainable Supply Chain %",
        "unit": "%",
        "category": "social",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 15,
        "benchmark_sources": ["CDP Supply Chain", "SEDEX"],
    },
    "board_diversity_pct": {
        "id": "board_diversity_pct",
        "name": "Board Diversity %",
        "unit": "%",
        "category": "governance",
        "widely_recognized": True,
        "measurable": True,
        "typical_spt_improvement_pct": 10,
        "benchmark_sources": ["30% Club", "governance codes"],
    },
    "esg_rating_score": {
        "id": "esg_rating_score",
        "name": "ESG Rating Score",
        "unit": "score",
        "category": "governance",
        "widely_recognized": False,
        "measurable": True,
        "typical_spt_improvement_pct": 5,
        "benchmark_sources": ["MSCI", "Sustainalytics", "ISS"],
    },
}

ICMA_SLB_COMPONENTS: List[Dict[str, Any]] = [
    {
        "id": "slb_c1",
        "name": "KPI Selection",
        "description": (
            "KPIs must be material to core business, measurable/quantifiable, "
            "externally verifiable, and able to be benchmarked"
        ),
        "blocking": True,
        "article": "ICMA SLB Principles 2023 §1",
    },
    {
        "id": "slb_c2",
        "name": "SPT Calibration",
        "description": (
            "Sustainability Performance Targets must be ambitious, consistent with "
            "science/sector benchmarks, set within a predefined timeline, and "
            "compared to a baseline"
        ),
        "blocking": True,
        "article": "ICMA SLB Principles 2023 §2",
    },
    {
        "id": "slb_c3",
        "name": "Bond Characteristics",
        "description": (
            "Coupon step-up (or other financial/structural impacts) triggered if "
            "SPTs not met on trigger dates"
        ),
        "blocking": True,
        "article": "ICMA SLB Principles 2023 §3",
    },
    {
        "id": "slb_c4",
        "name": "Reporting",
        "description": (
            "Annual disclosure of KPI performance and verification; update on SPT "
            "progress and any events that may affect achievement"
        ),
        "blocking": False,
        "article": "ICMA SLB Principles 2023 §4",
    },
    {
        "id": "slb_c5",
        "name": "Verification",
        "description": (
            "Annual independent external verification of KPI performance; second "
            "party opinion recommended at issuance"
        ),
        "blocking": False,
        "article": "ICMA SLB Principles 2023 §5",
    },
]

LMA_SLL_COMPONENTS: List[Dict[str, Any]] = [
    {
        "id": "sll_c1",
        "name": "Relationship to Borrower's Sustainability Strategy",
        "description": (
            "KPIs aligned with borrower's overall ESG strategy and sector context"
        ),
        "blocking": True,
        "article": "LMA SLL Principles 2023 §1",
    },
    {
        "id": "sll_c2",
        "name": "Target Setting (SPTs)",
        "description": (
            "Ambitious, material, measured against recent performance or comparable "
            "external reference point"
        ),
        "blocking": True,
        "article": "LMA SLL Principles 2023 §2",
    },
    {
        "id": "sll_c3",
        "name": "Documentation & Covenants",
        "description": (
            "Margin adjustment terms and KPI measurement mechanics clearly documented "
            "in loan agreement"
        ),
        "blocking": True,
        "article": "LMA SLL Principles 2023 §3",
    },
    {
        "id": "sll_c4",
        "name": "Reporting",
        "description": (
            "Annual KPI performance update to lender; publicly available if listed"
        ),
        "blocking": False,
        "article": "LMA SLL Principles 2023 §4",
    },
    {
        "id": "sll_c5",
        "name": "Verification",
        "description": (
            "External verification at least once a year for each SPT assessment date"
        ),
        "blocking": False,
        "article": "LMA SLL Principles 2023 §5",
    },
]

SL_CROSS_FRAMEWORK: Dict[str, str] = {
    "csrd_esrs": (
        "SLB/SLL KPIs should be aligned with CSRD ESRS material topic disclosures "
        "(E1 climate, S1 workforce, G1 governance)"
    ),
    "sbti": (
        "GHG intensity KPIs with SPTs should reference SBTi sector pathways for "
        "ambition calibration"
    ),
    "tcfd": (
        "KPI baseline and target-setting should be informed by TCFD scenario analysis "
        "(S3 resilience)"
    ),
    "gri": (
        "KPI measurement methodologies should reference GRI Topic Standards "
        "(GRI 305 emissions, GRI 306 waste)"
    ),
    "eu_taxonomy": (
        "Bond proceeds (if green-earmarked) or underlying assets should consider "
        "taxonomy alignment as a complementary metric"
    ),
}

COUPON_STEP_UP_GUIDANCE: Dict[str, Any] = {
    "typical_range_bps": "12.5–25 bps increase per missed SPT",
    "max_step_up_bps": 50,
    "trigger_mechanism": "SPT assessment date (typically 1-2 dates over bond tenor)",
    "remedy_period": (
        "Some structures allow cure period; ICMA recommends no cure for GHG targets"
    ),
    "use_of_step_up": (
        "Step-up coupon proceeds ideally directed to ESG/sustainability initiatives; "
        "issuer may donate to climate fund"
    ),
}

# KPIs where improvement means a DECREASE in value (lower is better)
_LOWER_IS_BETTER = {"ghg_scope1_2_intensity", "ghg_scope3_intensity", "water_intensity", "employee_injury_rate"}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class KPIInput:
    kpi_id: str
    kpi_name: str
    baseline_value: float
    baseline_year: int
    target_value: float
    target_year: int
    current_value: float = 0.0
    unit: str = ""
    external_verified: bool = False
    verification_provider: str = ""


@dataclass
class SLBInput:
    instrument_id: str
    issuer_name: str
    instrument_type: str  # "slb" or "sll"
    tenor_years: int = 5
    issuance_amount: float = 0.0
    currency: str = "EUR"
    kpis: List[KPIInput] = field(default_factory=list)
    has_spo: bool = False
    spo_provider: str = ""
    coupon_step_up_bps: float = 25.0
    has_annual_reporting: bool = False
    has_annual_verification: bool = False


@dataclass
class KPIAssessment:
    kpi_id: str
    kpi_name: str
    baseline_value: float
    target_value: float
    current_value: float
    improvement_required_pct: float
    improvement_achieved_pct: float
    on_track: bool
    smart_score: float
    spt_ambition_rating: str
    verified: bool

    def dict(self) -> Dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "baseline_value": self.baseline_value,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "improvement_required_pct": self.improvement_required_pct,
            "improvement_achieved_pct": self.improvement_achieved_pct,
            "on_track": self.on_track,
            "smart_score": self.smart_score,
            "spt_ambition_rating": self.spt_ambition_rating,
            "verified": self.verified,
        }


@dataclass
class SLFinanceResult:
    assessment_id: str
    instrument_id: str
    issuer_name: str
    instrument_type: str
    component_assessments: Dict[str, Any]
    kpi_assessments: List[Dict[str, Any]]
    overall_score: float
    principles_compliant: bool
    blocking_gaps: List[str]
    coupon_step_up_bps: float
    step_up_triggered: bool
    spo_required: bool
    spo_status: str
    cross_framework: Dict[str, str]
    recommendations: List[str]
    generated_at: str

    def dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "instrument_id": self.instrument_id,
            "issuer_name": self.issuer_name,
            "instrument_type": self.instrument_type,
            "component_assessments": self.component_assessments,
            "kpi_assessments": self.kpi_assessments,
            "overall_score": self.overall_score,
            "principles_compliant": self.principles_compliant,
            "blocking_gaps": self.blocking_gaps,
            "coupon_step_up_bps": self.coupon_step_up_bps,
            "step_up_triggered": self.step_up_triggered,
            "spo_required": self.spo_required,
            "spo_status": self.spo_status,
            "cross_framework": self.cross_framework,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SLFinanceEngine:
    """Sustainability-Linked Finance Engine (E17) — ICMA SLB + LMA SLL Principles 2023."""

    def validate_kpi(self, kpi: KPIInput) -> KPIAssessment:
        """Assess a single KPI against SMART criteria and SPT trajectory."""
        lib_entry = KPI_LIBRARY.get(kpi.kpi_id, {})
        typical_improvement = lib_entry.get("typical_spt_improvement_pct", 10)
        lower_better = kpi.kpi_id in _LOWER_IS_BETTER

        # Improvement required
        if kpi.baseline_value != 0:
            improvement_required_pct = (
                abs(kpi.target_value - kpi.baseline_value) / abs(kpi.baseline_value) * 100
            )
        else:
            improvement_required_pct = 0.0

        # Improvement achieved (current vs baseline→target trajectory)
        if kpi.baseline_value != 0:
            if lower_better:
                achieved = (kpi.baseline_value - kpi.current_value) / abs(kpi.baseline_value) * 100
            else:
                achieved = (kpi.current_value - kpi.baseline_value) / abs(kpi.baseline_value) * 100
            improvement_achieved_pct = max(achieved, 0.0)
        else:
            improvement_achieved_pct = 0.0

        on_track = improvement_achieved_pct >= improvement_required_pct * 0.5

        # SMART score
        smart_score = 0.0
        smart_score += 20.0 if kpi.kpi_name else 0.0           # Specific
        smart_score += 20.0 if kpi.unit else 0.0               # Measurable
        smart_score += 20.0 if improvement_required_pct >= typical_improvement else 0.0  # Ambitious
        smart_score += 20.0 if kpi.kpi_id in KPI_LIBRARY else 0.0   # Relevant
        smart_score += 20.0 if kpi.target_year > kpi.baseline_year else 0.0  # Time-bound

        if smart_score >= 80:
            ambition = "high"
        elif smart_score >= 60:
            ambition = "medium"
        elif smart_score >= 40:
            ambition = "low"
        else:
            ambition = "insufficient"

        return KPIAssessment(
            kpi_id=kpi.kpi_id,
            kpi_name=kpi.kpi_name,
            baseline_value=kpi.baseline_value,
            target_value=kpi.target_value,
            current_value=kpi.current_value,
            improvement_required_pct=round(improvement_required_pct, 2),
            improvement_achieved_pct=round(improvement_achieved_pct, 2),
            on_track=on_track,
            smart_score=round(smart_score, 2),
            spt_ambition_rating=ambition,
            verified=kpi.external_verified,
        )

    def _assess_components(self, inp: SLBInput, kpi_results: List[KPIAssessment]) -> Dict[str, Any]:
        """Assess ICMA or LMA principles components."""
        components = ICMA_SLB_COMPONENTS if inp.instrument_type == "slb" else LMA_SLL_COMPONENTS
        assessments: Dict[str, Any] = {}

        kpi_ids = [k.kpi_id for k in inp.kpis]
        any_kpi_lib = any(k in KPI_LIBRARY for k in kpi_ids)
        all_smart = all(ka.smart_score >= 60 for ka in kpi_results) if kpi_results else False
        all_on_track = all(ka.on_track for ka in kpi_results) if kpi_results else False

        for comp in components:
            cid = comp["id"]
            blocking = comp["blocking"]
            score = 0.0
            gaps: List[str] = []

            if cid in ("slb_c1", "sll_c1"):
                # KPI selection / alignment
                if any_kpi_lib:
                    score = 80.0
                else:
                    score = 40.0
                    gaps.append("No KPIs found in recognised ICMA/LMA KPI library")
                if all_smart:
                    score = min(score + 20.0, 100.0)
                else:
                    gaps.append("One or more KPIs do not meet SMART criteria (score <60)")

            elif cid in ("slb_c2", "sll_c2"):
                # SPT calibration
                if kpi_results:
                    avg_smart = sum(ka.smart_score for ka in kpi_results) / len(kpi_results)
                    score = min(avg_smart, 100.0)
                    high_ambition = sum(1 for ka in kpi_results if ka.spt_ambition_rating in ("high", "medium"))
                    if high_ambition < len(kpi_results):
                        gaps.append("Some SPTs rated 'low' or 'insufficient' ambition — strengthen targets")
                else:
                    score = 0.0
                    gaps.append("No KPIs defined")

            elif cid in ("slb_c3", "sll_c3"):
                # Bond/loan characteristics
                score = 80.0 if inp.coupon_step_up_bps > 0 else 0.0
                if inp.coupon_step_up_bps <= 0:
                    gaps.append("No coupon/margin step-up defined — required for SLB/SLL structure")
                elif inp.coupon_step_up_bps > COUPON_STEP_UP_GUIDANCE["max_step_up_bps"]:
                    gaps.append(
                        f"Step-up {inp.coupon_step_up_bps} bps exceeds typical max "
                        f"{COUPON_STEP_UP_GUIDANCE['max_step_up_bps']} bps"
                    )
                    score = 60.0

            elif cid in ("slb_c4", "sll_c4"):
                # Reporting
                score = 100.0 if inp.has_annual_reporting else 30.0
                if not inp.has_annual_reporting:
                    gaps.append("Annual KPI performance reporting not confirmed")

            elif cid in ("slb_c5", "sll_c5"):
                # Verification
                verified_kpis = sum(1 for ka in kpi_results if ka.verified)
                if inp.has_annual_verification and verified_kpis == len(kpi_results):
                    score = 100.0
                elif inp.has_annual_verification:
                    score = 70.0
                    gaps.append(f"Only {verified_kpis}/{len(kpi_results)} KPIs externally verified")
                else:
                    score = 20.0
                    gaps.append("No annual external verification confirmed")

            assessments[cid] = {
                "compliant": score >= 70.0,
                "score": round(score, 2),
                "gaps": gaps,
                "blocking": blocking,
                "article": comp["article"],
            }

        return assessments

    def assess(self, inp: SLBInput) -> SLFinanceResult:
        """Full SLB/SLL principles compliance assessment."""
        assessment_id = str(uuid.uuid4())
        kpi_results = [self.validate_kpi(k) for k in inp.kpis]

        component_assessments = self._assess_components(inp, kpi_results)

        # Overall score: weighted by blocking (1.5x)
        total_weight = 0.0
        weighted_sum = 0.0
        for ca in component_assessments.values():
            w = 1.5 if ca["blocking"] else 1.0
            total_weight += w
            weighted_sum += ca["score"] * w
        overall_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0

        # Principles compliant = all blocking components pass
        principles_compliant = all(
            ca["compliant"] for ca in component_assessments.values() if ca["blocking"]
        )

        # Blocking gaps
        blocking_gaps: List[str] = []
        for cid, ca in component_assessments.items():
            if ca["blocking"] and not ca["compliant"]:
                blocking_gaps.extend([f"[{cid}] {g}" for g in ca["gaps"]])

        # Step-up triggered if any KPI not on track
        step_up_triggered = any(not ka.on_track for ka in kpi_results)

        # SPO
        spo_required = inp.instrument_type == "slb"  # always True for SLB
        if inp.has_spo and inp.spo_provider:
            spo_status = f"SPO obtained from {inp.spo_provider}"
        elif inp.has_spo:
            spo_status = "SPO obtained (provider not specified)"
        else:
            spo_status = "SPO not obtained — recommended for SLB; required for market credibility"

        # Recommendations
        recs: List[str] = []
        if not principles_compliant:
            recs.append("Address blocking gaps before issuance/signing to meet principles compliance.")
        if not inp.has_spo and inp.instrument_type == "slb":
            recs.append(
                "Obtain a Second Party Opinion (SPO) from a recognised provider "
                "(e.g. Vigeo Eiris, ISS ESG, Sustainalytics) before SLB issuance."
            )
        if step_up_triggered:
            recs.append(
                f"One or more KPIs are off-track; coupon step-up of "
                f"{inp.coupon_step_up_bps} bps will apply at next assessment date."
            )
        if not inp.has_annual_reporting:
            recs.append("Implement annual KPI performance reporting in investor materials.")
        if not inp.has_annual_verification:
            recs.append(
                "Arrange annual third-party verification of KPI data per "
                "ICMA SLB §5 / LMA SLL §5."
            )
        if principles_compliant and not blocking_gaps:
            recs.append(
                "Instrument is principles-compliant. Maintain annual verification and "
                "reporting cadence; update SPTs at next review if already achieved."
            )

        return SLFinanceResult(
            assessment_id=assessment_id,
            instrument_id=inp.instrument_id,
            issuer_name=inp.issuer_name,
            instrument_type=inp.instrument_type,
            component_assessments=component_assessments,
            kpi_assessments=[ka.dict() for ka in kpi_results],
            overall_score=round(overall_score, 2),
            principles_compliant=principles_compliant,
            blocking_gaps=blocking_gaps,
            coupon_step_up_bps=inp.coupon_step_up_bps,
            step_up_triggered=step_up_triggered,
            spo_required=spo_required,
            spo_status=spo_status,
            cross_framework=SL_CROSS_FRAMEWORK,
            recommendations=recs,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def calibrate_spt(
        self,
        kpi_id: str,
        baseline: float,
        target_pct_improvement: float,
        baseline_year: int,
        target_year: int,
    ) -> Dict[str, Any]:
        """Calculate target value and ambition assessment for a given SPT."""
        lib_entry = KPI_LIBRARY.get(kpi_id, {})
        lower_better = kpi_id in _LOWER_IS_BETTER
        typical = lib_entry.get("typical_spt_improvement_pct", 10)

        if lower_better:
            target_value = baseline * (1 - target_pct_improvement / 100)
        else:
            target_value = baseline * (1 + target_pct_improvement / 100)

        if target_pct_improvement >= typical * 1.25:
            ambition = "high"
        elif target_pct_improvement >= typical:
            ambition = "medium"
        elif target_pct_improvement >= typical * 0.5:
            ambition = "low"
        else:
            ambition = "insufficient"

        benchmarks = lib_entry.get("benchmark_sources", [])
        return {
            "kpi_id": kpi_id,
            "kpi_name": lib_entry.get("name", kpi_id),
            "baseline_value": baseline,
            "baseline_year": baseline_year,
            "target_value": round(target_value, 4),
            "target_year": target_year,
            "target_pct_improvement": target_pct_improvement,
            "ambition_assessment": ambition,
            "typical_spt_improvement_pct": typical,
            "benchmark_comparison": (
                f"Target improvement {target_pct_improvement:.1f}% vs typical "
                f"{typical:.0f}% per {', '.join(benchmarks) if benchmarks else 'market benchmarks'}"
            ),
            "direction": "decrease" if lower_better else "increase",
        }

    # ------------------------------------------------------------------
    # Reference accessors
    # ------------------------------------------------------------------

    def get_kpi_library(self) -> Dict[str, Any]:
        return KPI_LIBRARY

    def get_icma_components(self) -> List[Dict[str, Any]]:
        return ICMA_SLB_COMPONENTS

    def get_lma_components(self) -> List[Dict[str, Any]]:
        return LMA_SLL_COMPONENTS

    def get_cross_framework(self) -> Dict[str, str]:
        return SL_CROSS_FRAMEWORK

    def get_coupon_guidance(self) -> Dict[str, Any]:
        return COUPON_STEP_UP_GUIDANCE
