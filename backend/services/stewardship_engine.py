"""
Stewardship Engine (E6)
========================
Active ownership and engagement analytics covering:

  1. Engagement Assessment    — Evaluate engagement effectiveness per investee company
  2. Proxy Voting Analysis    — AGM proxy voting alignment with climate/ESG resolutions
  3. Collaborative Initiatives — Multi-investor initiative participation (CA100+, NZIF, GFANZ)
  4. Escalation Planning      — Determine when/how to escalate stewardship actions

Regulatory cross-references:
  - GFANZ (Glasgow Financial Alliance for Net Zero) — stewardship as climate lever
  - NZAM Initiative (NZAMI) — Net Zero Asset Managers stewardship commitment
  - NZIF (Net Zero Investment Framework) — Objective 4: Stewardship
  - CA100+ (Climate Action 100+) — collaborative engagement with 170+ companies
  - UNPRI (Principle 2) — active ownership obligation
  - CSRD ESRS S3 (SBM-3, MDR-A) — affected communities engagement
  - UK Stewardship Code 2020 — 12 principles, tiered applicability

Frameworks covered:
  - GFANZ-E-1: Active stewardship with portfolio companies (% engaged)
  - GFANZ-E-2: Escalation to assertive stewardship
  - NZIF-4.2: Corporate bonds — issuer alignment + stewardship
  - CA100+: Priority focus list (170 systemically important emitters)
  - UNPRI: Principle 2 engagement reporting
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4


# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

ENGAGEMENT_TYPES: Dict[str, Dict[str, Any]] = {
    "written_communication": {
        "label": "Written Communication",
        "description": "Letters, emails, formal notices to board/management",
        "intensity": "low",
        "typical_duration_months": 3,
        "gfanz_ref": "GFANZ-E-1",
    },
    "meeting_management": {
        "label": "Meeting with Management",
        "description": "Direct dialogue with CEO/CFO/IR team on ESG topics",
        "intensity": "medium",
        "typical_duration_months": 6,
        "gfanz_ref": "GFANZ-E-1",
    },
    "meeting_board": {
        "label": "Meeting with Board",
        "description": "Board-level engagement including Chair/NED on climate oversight",
        "intensity": "high",
        "typical_duration_months": 6,
        "gfanz_ref": "GFANZ-E-2",
    },
    "shareholder_resolution": {
        "label": "Shareholder Resolution Filing",
        "description": "Co-filing or supporting climate/ESG shareholder resolutions at AGM",
        "intensity": "high",
        "typical_duration_months": 12,
        "gfanz_ref": "GFANZ-E-2",
        "unpri_ref": "UNPRI Principle 2",
    },
    "collaborative_engagement": {
        "label": "Collaborative Engagement",
        "description": "Participating in investor coalitions (CA100+, NZIF, IIGCC)",
        "intensity": "medium",
        "typical_duration_months": 24,
        "gfanz_ref": "GFANZ-E-1",
        "ca100_ref": "CA100+ Focus Company",
    },
    "proxy_voting": {
        "label": "Proxy Voting Action",
        "description": "Voting AGAINST management on climate/ESG resolutions",
        "intensity": "medium",
        "typical_duration_months": 1,
        "gfanz_ref": "GFANZ-E-1",
        "unpri_ref": "UNPRI Principle 2",
    },
    "divestment_warning": {
        "label": "Divestment Warning",
        "description": "Formal notice that no-change will result in divestment",
        "intensity": "critical",
        "typical_duration_months": 6,
        "gfanz_ref": "GFANZ-E-2",
    },
    "divestment": {
        "label": "Divestment / Exclusion",
        "description": "Exit position following failed engagement",
        "intensity": "critical",
        "typical_duration_months": 0,
        "gfanz_ref": "GFANZ-E-2",
    },
}

# CA100+ focus companies (top 20 systemically important emitters — sample)
CA100_FOCUS_SECTORS = {
    "B06": "Oil & Gas",
    "C19": "Petroleum Refining",
    "C24": "Iron & Steel",
    "C20": "Basic Chemicals",
    "D35": "Electric Utilities",
    "H49": "Road Transport",
    "H51": "Air Transport",
    "B05": "Coal Mining",
    "C17": "Paper & Pulp",
    "C23": "Cement / Glass",
}

# GFANZ stewardship milestones (% portfolio engaged)
GFANZ_MILESTONES: Dict[str, float] = {
    "baseline_engagement_pct":  20.0,   # minimum to be considered active
    "intermediate_engagement_pct": 50.0,
    "advanced_engagement_pct":  75.0,
    "full_coverage_pct":       100.0,
}

# Proxy voting resolution types and expected alignment for climate-committed FI
PROXY_RESOLUTION_TYPES: Dict[str, Dict[str, Any]] = {
    "climate_transition_plan":    {"expected_support": True, "weight": 0.30, "nzami_critical": True},
    "ghg_reduction_target":       {"expected_support": True, "weight": 0.25, "nzami_critical": True},
    "climate_disclosure_request": {"expected_support": True, "weight": 0.20, "nzami_critical": False},
    "executive_pay_climate_link":  {"expected_support": True, "weight": 0.15, "nzami_critical": False},
    "board_climate_competency":   {"expected_support": True, "weight": 0.10, "nzami_critical": True},
    "anti_climate_action":        {"expected_support": False, "weight": 0.25, "nzami_critical": True},
}

# Collaborative initiatives
COLLABORATIVE_INITIATIVES: Dict[str, Dict[str, Any]] = {
    "CA100_PLUS": {
        "name": "Climate Action 100+",
        "focus": "Engagement with 170 systemically important emitters",
        "member_count": 700,
        "aum_trillion_usd": 68,
        "min_engagement_actions": 3,
        "nzami_compatible": True,
        "gfanz_ref": "GFANZ-E-1",
    },
    "NZIF": {
        "name": "Net Zero Investment Framework",
        "focus": "Paris-aligned investment and stewardship (IIGCC)",
        "member_count": 130,
        "aum_trillion_usd": 35,
        "min_engagement_actions": 2,
        "nzami_compatible": True,
        "gfanz_ref": "GFANZ-E-1",
    },
    "GFANZ": {
        "name": "Glasgow Financial Alliance for Net Zero",
        "focus": "Net zero stewardship across all asset classes",
        "member_count": 650,
        "aum_trillion_usd": 150,
        "min_engagement_actions": 4,
        "nzami_compatible": True,
        "gfanz_ref": "GFANZ-E-1",
    },
    "UNPRI": {
        "name": "UN Principles for Responsible Investment",
        "focus": "Principle 2: Active ownership / Stewardship",
        "member_count": 5300,
        "aum_trillion_usd": 121,
        "min_engagement_actions": 1,
        "nzami_compatible": True,
        "gfanz_ref": "GFANZ-E-1",
    },
    "TNFD_EARLYADO": {
        "name": "TNFD Early Adopters Coalition",
        "focus": "Nature-related disclosure and stewardship commitments",
        "member_count": 320,
        "aum_trillion_usd": 4.1,
        "min_engagement_actions": 2,
        "nzami_compatible": False,
        "gfanz_ref": None,
    },
}

# Escalation ladder (ordered by assertiveness)
ESCALATION_LADDER = [
    {"level": 1, "action": "written_communication",    "trigger_months_stalled": 3},
    {"level": 2, "action": "meeting_management",       "trigger_months_stalled": 6},
    {"level": 3, "action": "meeting_board",            "trigger_months_stalled": 9},
    {"level": 4, "action": "shareholder_resolution",   "trigger_months_stalled": 12},
    {"level": 5, "action": "divestment_warning",       "trigger_months_stalled": 18},
    {"level": 6, "action": "divestment",               "trigger_months_stalled": 24},
]


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class EngagementInput:
    company_id: str
    company_name: str
    sector_nace: str
    exposure_eur: float
    engagement_start_date: Optional[str] = None      # ISO date
    engagement_types: List[str] = field(default_factory=list)
    objectives_set: bool = False
    milestone_achieved: bool = False
    engagement_outcome: str = "ongoing"               # ongoing | positive | stalled | failed
    months_since_last_contact: int = 0
    is_ca100_focus: bool = False
    portfolio_weight_pct: float = 0.0


@dataclass
class EngagementResult:
    company_id: str
    company_name: str
    sector: str
    exposure_eur: float
    engagement_score: float              # 0–100 (higher = more effective)
    effectiveness_rating: str            # developing | progressing | advanced | achieved
    engagement_types: List[str] = field(default_factory=list)
    total_actions: int = 0
    escalation_recommended: bool = False
    recommended_next_action: str = ""
    escalation_level: int = 0
    gfanz_milestone: str = ""
    ca100_relevant: bool = False
    gaps: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ProxyVoteInput:
    company_id: str
    company_name: str
    agm_date: str                        # ISO date
    resolutions: List[Dict[str, Any]] = field(default_factory=list)
    # Each resolution: {type, description, management_recommendation, voted_for}


@dataclass
class ProxyVoteResult:
    company_id: str
    company_name: str
    agm_date: str
    total_resolutions: int = 0
    climate_resolutions: int = 0
    alignment_score: float = 0.0         # 0–100 vs expected climate-aligned votes
    nzami_aligned_votes: int = 0
    nzami_misaligned_votes: int = 0
    vote_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CollaborativeInitiativeResult:
    initiative_id: str
    initiative_name: str
    participation_status: str            # member | non_member | pending
    min_actions_required: int = 0
    actions_completed: int = 0
    coverage_pct: float = 0.0            # % portfolio companies engaged via this initiative
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class EscalationPlanResult:
    company_id: str
    company_name: str
    current_escalation_level: int = 0
    recommended_escalation_level: int = 0
    trigger_met: bool = False
    months_stalled: int = 0
    recommended_action: str = ""
    action_deadline: str = ""
    regulatory_rationale: str = ""
    escalation_ladder: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PortfolioStewardshipResult:
    run_id: str
    entity_name: str
    assessment_date: str
    total_companies: int = 0
    total_exposure_eur: float = 0.0

    # GFANZ headline metrics
    engaged_companies: int = 0
    engagement_coverage_pct: float = 0.0
    gfanz_milestone: str = ""

    # Score aggregates
    avg_engagement_score: float = 0.0
    advanced_engagements: int = 0
    escalations_recommended: int = 0

    # Proxy voting
    proxy_alignment_score: float = 0.0
    nzami_aligned_votes_pct: float = 0.0

    # Initiatives
    initiative_participations: List[CollaborativeInitiativeResult] = field(default_factory=list)

    # Per-company results
    company_results: List[EngagementResult] = field(default_factory=list)
    escalation_plans: List[EscalationPlanResult] = field(default_factory=list)

    # Gaps and actions
    gaps: List[str] = field(default_factory=list)
    priority_actions: List[Dict[str, str]] = field(default_factory=list)

    # Cross-framework
    framework_coverage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Stewardship Engine
# ---------------------------------------------------------------------------

class StewardshipEngine:
    """
    Active ownership and stewardship assessment engine (E6).

    Covers: engagement effectiveness, proxy voting alignment,
    collaborative initiative participation, and escalation planning.
    """

    # ── Public API ──────────────────────────────────────────────────────

    def assess_portfolio(
        self,
        entity_name: str,
        engagements: List[EngagementInput],
        proxy_votes: Optional[List[ProxyVoteInput]] = None,
        initiative_memberships: Optional[Dict[str, str]] = None,
        assessment_date: Optional[str] = None,
    ) -> PortfolioStewardshipResult:
        """
        Full portfolio stewardship assessment.

        Args:
            entity_name: Asset manager / FI name
            engagements: List of per-company engagement inputs
            proxy_votes: Optional list of proxy vote records
            initiative_memberships: Dict of {initiative_id: status}
                e.g. {"CA100_PLUS": "member", "NZIF": "pending"}
            assessment_date: ISO date (default today)
        """
        _date = assessment_date or date.today().isoformat()
        run_id = str(uuid4())

        company_results = [self.assess_engagement(e) for e in engagements]
        escalation_plans = [self.assess_escalation(e) for e in engagements]

        proxy_results = []
        if proxy_votes:
            proxy_results = [self.assess_proxy_votes(v) for v in proxy_votes]

        initiative_results = self._assess_initiatives(
            initiative_memberships or {},
            engagements=engagements,
        )

        return self._aggregate(
            run_id=run_id,
            entity_name=entity_name,
            assessment_date=_date,
            company_results=company_results,
            escalation_plans=escalation_plans,
            proxy_results=proxy_results,
            initiative_results=initiative_results,
            engagements=engagements,
        )

    def assess_engagement(self, e: EngagementInput) -> EngagementResult:
        """Assess engagement effectiveness for a single investee company."""
        score = self._engagement_score(e)
        rating = self._rating(score)
        escalation_rec, next_action, level = self._escalation_signal(e)
        ca100 = e.sector_nace[:3] in CA100_FOCUS_SECTORS or e.is_ca100_focus
        gfanz_ms = self._gfanz_milestone(e, score)
        gaps = self._engagement_gaps(e)

        return EngagementResult(
            company_id=e.company_id,
            company_name=e.company_name,
            sector=CA100_FOCUS_SECTORS.get(e.sector_nace[:3], e.sector_nace),
            exposure_eur=e.exposure_eur,
            engagement_score=score,
            effectiveness_rating=rating,
            engagement_types=e.engagement_types,
            total_actions=len(e.engagement_types),
            escalation_recommended=escalation_rec,
            recommended_next_action=next_action,
            escalation_level=level,
            gfanz_milestone=gfanz_ms,
            ca100_relevant=ca100,
            gaps=gaps,
            notes=(
                f"Engaged since {e.engagement_start_date}. "
                f"Outcome: {e.engagement_outcome}."
                if e.engagement_start_date else ""
            ),
        )

    def assess_proxy_votes(self, v: ProxyVoteInput) -> ProxyVoteResult:
        """Score proxy voting alignment for an AGM."""
        climate_resolutions = [
            r for r in v.resolutions
            if r.get("type") in PROXY_RESOLUTION_TYPES
        ]
        total = len(v.resolutions)
        alignment_score = 0.0
        nzami_aligned = 0
        nzami_misaligned = 0
        vote_breakdown = []

        for res in climate_resolutions:
            rt = res.get("type", "")
            cfg = PROXY_RESOLUTION_TYPES.get(rt, {})
            expected = cfg.get("expected_support", True)
            voted_for = res.get("voted_for", False)
            aligned = voted_for == expected
            weight = cfg.get("weight", 0.1)
            if aligned:
                alignment_score += weight * 100.0
            if cfg.get("nzami_critical"):
                if aligned:
                    nzami_aligned += 1
                else:
                    nzami_misaligned += 1
            vote_breakdown.append({
                "type": rt,
                "description": res.get("description", ""),
                "voted_for": voted_for,
                "expected": expected,
                "aligned": aligned,
                "weight": weight,
                "nzami_critical": cfg.get("nzami_critical", False),
            })

        total_weight = sum(
            PROXY_RESOLUTION_TYPES.get(r.get("type", ""), {}).get("weight", 0.0)
            for r in climate_resolutions
        )
        if total_weight > 0:
            alignment_score = min(100.0, alignment_score / total_weight)

        recs = []
        if nzami_misaligned > 0:
            recs.append(
                f"Review {nzami_misaligned} NZAMI-critical vote(s) that did not align "
                f"with climate commitments."
            )
        if not climate_resolutions:
            recs.append("No climate-related resolutions identified — verify resolution categorisation.")

        return ProxyVoteResult(
            company_id=v.company_id,
            company_name=v.company_name,
            agm_date=v.agm_date,
            total_resolutions=total,
            climate_resolutions=len(climate_resolutions),
            alignment_score=round(alignment_score, 1),
            nzami_aligned_votes=nzami_aligned,
            nzami_misaligned_votes=nzami_misaligned,
            vote_breakdown=vote_breakdown,
            recommendations=recs,
        )

    def assess_escalation(self, e: EngagementInput) -> EscalationPlanResult:
        """Determine current and recommended escalation level for a company."""
        months_stalled = (
            e.months_since_last_contact
            if e.engagement_outcome in ("stalled", "failed")
            else 0
        )

        current_level = 0
        for step in ESCALATION_LADDER:
            if step["action"] in e.engagement_types:
                current_level = max(current_level, step["level"])

        recommended_level = current_level
        trigger_met = False
        for step in ESCALATION_LADDER:
            if months_stalled >= step["trigger_months_stalled"] and step["level"] > current_level:
                recommended_level = step["level"]
                trigger_met = True
                break

        next_step = next(
            (s for s in ESCALATION_LADDER if s["level"] == recommended_level), None
        )
        action = next_step["action"] if next_step else ""
        deadline = ""
        if trigger_met and next_step:
            deadline = date.today().isoformat()

        rationale = ""
        if trigger_met:
            rationale = (
                f"GFANZ-E-2 requires escalation to assertive stewardship after "
                f"{months_stalled} months without progress. "
                f"Recommended: {ENGAGEMENT_TYPES.get(action, {}).get('label', action)}."
            )

        return EscalationPlanResult(
            company_id=e.company_id,
            company_name=e.company_name,
            current_escalation_level=current_level,
            recommended_escalation_level=recommended_level,
            trigger_met=trigger_met,
            months_stalled=months_stalled,
            recommended_action=action,
            action_deadline=deadline,
            regulatory_rationale=rationale,
            escalation_ladder=ESCALATION_LADDER,
        )

    # ── Private helpers ──────────────────────────────────────────────────

    def _engagement_score(self, e: EngagementInput) -> float:
        score = 0.0
        if e.engagement_types:
            score += 20.0  # baseline: any engagement
        # Intensity bonus
        max_intensity = 0
        for et in e.engagement_types:
            intensity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            cfg = ENGAGEMENT_TYPES.get(et, {})
            max_intensity = max(max_intensity, intensity_map.get(cfg.get("intensity", "low"), 0))
        score += max_intensity * 10.0

        if e.objectives_set:
            score += 20.0
        if e.milestone_achieved:
            score += 20.0
        if e.engagement_outcome == "positive":
            score += 15.0
        elif e.engagement_outcome == "stalled":
            score -= 10.0
        elif e.engagement_outcome == "failed":
            score -= 20.0

        # Multiple engagement types
        if len(e.engagement_types) >= 3:
            score += 5.0

        return max(0.0, min(100.0, round(score, 1)))

    def _rating(self, score: float) -> str:
        if score >= 75:
            return "advanced"
        if score >= 50:
            return "progressing"
        if score >= 25:
            return "developing"
        return "initial"

    def _escalation_signal(self, e: EngagementInput) -> tuple:
        months = e.months_since_last_contact
        outcome = e.engagement_outcome
        current = 0
        for step in ESCALATION_LADDER:
            if step["action"] in e.engagement_types:
                current = max(current, step["level"])

        if outcome in ("stalled", "failed") and months >= 6:
            next_level = current + 1
            for step in ESCALATION_LADDER:
                if step["level"] == next_level:
                    return True, step["action"], next_level
        return False, "", current

    def _gfanz_milestone(self, e: EngagementInput, score: float) -> str:
        if not e.engagement_types:
            return "not_engaged"
        if score >= 75:
            return "advanced_engagement"
        if score >= 50:
            return "intermediate_engagement"
        if score >= 25:
            return "baseline_engagement"
        return "initial"

    def _engagement_gaps(self, e: EngagementInput) -> List[str]:
        gaps = []
        if not e.engagement_types:
            gaps.append("[GFANZ-E-1] No engagement activities recorded — company not engaged")
        if not e.objectives_set:
            gaps.append("[NZIF-4.2] No engagement objectives set — outcome tracking impossible")
        ca100 = e.sector_nace[:3] in CA100_FOCUS_SECTORS or e.is_ca100_focus
        if ca100 and "collaborative_engagement" not in e.engagement_types:
            gaps.append("[CA100+] High-emitter company — collaborative engagement recommended")
        if e.engagement_outcome == "stalled" and e.months_since_last_contact >= 6:
            gaps.append(
                f"[GFANZ-E-2] Engagement stalled {e.months_since_last_contact}m — "
                "escalation to assertive stewardship required"
            )
        return gaps

    def _assess_initiatives(
        self,
        memberships: Dict[str, str],
        engagements: List[EngagementInput],
    ) -> List[CollaborativeInitiativeResult]:
        results = []
        for init_id, cfg in COLLABORATIVE_INITIATIVES.items():
            status = memberships.get(init_id, "non_member")
            actions = sum(
                1 for e in engagements
                if "collaborative_engagement" in e.engagement_types
            )
            coverage = (
                sum(1 for e in engagements if e.sector_nace[:3] in CA100_FOCUS_SECTORS)
                / max(len(engagements), 1)
            ) * 100 if init_id == "CA100_PLUS" else 0.0

            gaps, recs = [], []
            if status == "non_member":
                recs.append(f"Consider joining {cfg['name']} — {cfg['focus']}")
            elif actions < cfg["min_engagement_actions"]:
                gaps.append(
                    f"[{init_id}] Only {actions}/{cfg['min_engagement_actions']} "
                    "required engagement actions completed"
                )

            results.append(CollaborativeInitiativeResult(
                initiative_id=init_id,
                initiative_name=cfg["name"],
                participation_status=status,
                min_actions_required=cfg["min_engagement_actions"],
                actions_completed=actions,
                coverage_pct=round(coverage, 1),
                gaps=gaps,
                recommendations=recs,
            ))
        return results

    def _aggregate(
        self,
        run_id: str,
        entity_name: str,
        assessment_date: str,
        company_results: List[EngagementResult],
        escalation_plans: List[EscalationPlanResult],
        proxy_results: List[ProxyVoteResult],
        initiative_results: List[CollaborativeInitiativeResult],
        engagements: List[EngagementInput],
    ) -> PortfolioStewardshipResult:
        total_exp = sum(e.exposure_eur for e in engagements)
        engaged = sum(1 for r in company_results if r.total_actions > 0)
        coverage = (engaged / max(len(company_results), 1)) * 100
        avg_score = (
            sum(r.engagement_score for r in company_results) / max(len(company_results), 1)
        )
        advanced = sum(1 for r in company_results if r.effectiveness_rating == "advanced")
        escalations = sum(1 for r in company_results if r.escalation_recommended)

        # GFANZ milestone
        if coverage >= GFANZ_MILESTONES["full_coverage_pct"]:
            gfanz_ms = "full_coverage"
        elif coverage >= GFANZ_MILESTONES["advanced_engagement_pct"]:
            gfanz_ms = "advanced"
        elif coverage >= GFANZ_MILESTONES["intermediate_engagement_pct"]:
            gfanz_ms = "intermediate"
        elif coverage >= GFANZ_MILESTONES["baseline_engagement_pct"]:
            gfanz_ms = "baseline"
        else:
            gfanz_ms = "below_baseline"

        # Proxy alignment
        proxy_align = 0.0
        nzami_pct = 0.0
        if proxy_results:
            proxy_align = sum(p.alignment_score for p in proxy_results) / len(proxy_results)
            total_nzami = sum(
                p.nzami_aligned_votes + p.nzami_misaligned_votes for p in proxy_results
            )
            nzami_aligned = sum(p.nzami_aligned_votes for p in proxy_results)
            nzami_pct = (nzami_aligned / max(total_nzami, 1)) * 100

        # Portfolio gaps
        all_gaps = []
        for r in company_results:
            all_gaps.extend(r.gaps)
        if coverage < GFANZ_MILESTONES["baseline_engagement_pct"]:
            all_gaps.append(
                f"[GFANZ-E-1] Portfolio engagement coverage {coverage:.0f}% below "
                f"baseline target of {GFANZ_MILESTONES['baseline_engagement_pct']:.0f}%"
            )

        # Priority actions
        priority_actions = []
        for esc in escalation_plans:
            if esc.trigger_met:
                priority_actions.append({
                    "priority": "high",
                    "company": esc.company_name,
                    "action": ENGAGEMENT_TYPES.get(esc.recommended_action, {}).get("label", esc.recommended_action),
                    "regulatory_ref": "GFANZ-E-2 / NZAMI",
                    "deadline": esc.action_deadline,
                })

        return PortfolioStewardshipResult(
            run_id=run_id,
            entity_name=entity_name,
            assessment_date=assessment_date,
            total_companies=len(company_results),
            total_exposure_eur=total_exp,
            engaged_companies=engaged,
            engagement_coverage_pct=round(coverage, 1),
            gfanz_milestone=gfanz_ms,
            avg_engagement_score=round(avg_score, 1),
            advanced_engagements=advanced,
            escalations_recommended=escalations,
            proxy_alignment_score=round(proxy_align, 1),
            nzami_aligned_votes_pct=round(nzami_pct, 1),
            initiative_participations=initiative_results,
            company_results=company_results,
            escalation_plans=escalation_plans,
            gaps=list(set(all_gaps)),
            priority_actions=priority_actions,
            framework_coverage={
                "GFANZ-E-1": coverage >= GFANZ_MILESTONES["baseline_engagement_pct"],
                "GFANZ-E-2": escalations == 0,
                "NZIF-4.2": avg_score >= 50,
                "CA100_PLUS": any(r.ca100_relevant for r in company_results),
                "UNPRI_P2": engaged > 0,
            },
            metadata={
                "run_id": run_id,
                "engine_version": "E6-1.0",
                "frameworks": ["GFANZ", "NZAMI", "NZIF", "CA100+", "UNPRI"],
                "assessment_date": assessment_date,
                "proxy_votes_included": len(proxy_results) > 0,
            },
        )
