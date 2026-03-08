"""
Exclusion List Engine
======================
Maintains exclusion criteria and screens portfolio holdings against them.
Supports standard exclusion categories plus custom user-defined rules.

References:
- Norwegian Government Pension Fund Global (GPFG) exclusion guidelines
- Swiss Association for Responsible Investments (SVVK-ASIR)
- EU Delegated Regulation 2022/1288 (SFDR RTS) — PAI indicator 15
- SFDR Art.9 requirements on controversial weapons
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Exclusion Categories
# ---------------------------------------------------------------------------

class ExclusionCategory(str, Enum):
    CONTROVERSIAL_WEAPONS = "controversial_weapons"
    TOBACCO = "tobacco"
    THERMAL_COAL = "thermal_coal"
    ARCTIC_OIL_GAS = "arctic_oil_gas"
    OIL_SANDS = "oil_sands"
    NUCLEAR_WEAPONS = "nuclear_weapons"
    UNGC_VIOLATIONS = "ungc_violations"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Default Exclusion Rules
# ---------------------------------------------------------------------------

DEFAULT_EXCLUSION_RULES: dict[str, dict] = {
    ExclusionCategory.CONTROVERSIAL_WEAPONS.value: {
        "name": "Controversial Weapons",
        "description": "Cluster munitions, anti-personnel mines, biological weapons, chemical weapons",
        "revenue_threshold_pct": 0.0,  # Zero tolerance
        "applies_to": ["art6", "art8", "art8plus", "art9"],
        "regulatory_basis": "SFDR RTS PAI Indicator 15; Ottawa Treaty; Convention on Cluster Munitions",
    },
    ExclusionCategory.TOBACCO.value: {
        "name": "Tobacco Production",
        "description": "Companies deriving >5% revenue from tobacco production",
        "revenue_threshold_pct": 5.0,
        "applies_to": ["art8", "art8plus", "art9"],
        "regulatory_basis": "WHO FCTC; common ESG exclusion policy",
    },
    ExclusionCategory.THERMAL_COAL.value: {
        "name": "Thermal Coal",
        "description": "Mining: >10% revenue; Power: >30% generation from thermal coal",
        "revenue_threshold_pct": 10.0,
        "generation_threshold_pct": 30.0,
        "applies_to": ["art8plus", "art9"],
        "regulatory_basis": "Paris Agreement; IEA NZE 2050; EU PAB requirements",
    },
    ExclusionCategory.ARCTIC_OIL_GAS.value: {
        "name": "Arctic Oil & Gas",
        "description": "Companies with significant Arctic drilling operations",
        "revenue_threshold_pct": 5.0,
        "applies_to": ["art9"],
        "regulatory_basis": "Arctic Council; biodiversity risk; IUCN guidelines",
    },
    ExclusionCategory.OIL_SANDS.value: {
        "name": "Oil Sands",
        "description": "Companies with >5% revenue from oil sands extraction",
        "revenue_threshold_pct": 5.0,
        "applies_to": ["art9"],
        "regulatory_basis": "High-carbon extraction; Paris Agreement alignment",
    },
    ExclusionCategory.NUCLEAR_WEAPONS.value: {
        "name": "Nuclear Weapons",
        "description": "Companies involved in nuclear weapons production/maintenance",
        "revenue_threshold_pct": 0.0,
        "applies_to": ["art8plus", "art9"],
        "regulatory_basis": "Treaty on Non-Proliferation; common ESG policy",
    },
    ExclusionCategory.UNGC_VIOLATIONS.value: {
        "name": "UNGC / OECD Violations",
        "description": "Companies in verified violation of UN Global Compact / OECD Guidelines",
        "revenue_threshold_pct": 0.0,  # Violation-based, not revenue
        "applies_to": ["art8", "art8plus", "art9"],
        "regulatory_basis": "SFDR RTS PAI Indicator 12; UNGC 10 Principles; OECD MNE Guidelines",
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ExclusionRule:
    """A single exclusion criterion."""
    category: str
    name: str
    description: str
    revenue_threshold_pct: float = 0.0
    generation_threshold_pct: float = 0.0  # For coal power
    is_custom: bool = False
    applies_to_sfdr: list[str] = field(default_factory=lambda: ["art8", "art8plus", "art9"])


@dataclass
class HoldingScreenInput:
    """Holding data for exclusion screening."""
    holding_id: str
    security_name: str
    isin: Optional[str] = None
    weight_pct: float = 0.0
    # Revenue exposure flags
    controversial_weapons_revenue_pct: float = 0.0
    tobacco_revenue_pct: float = 0.0
    thermal_coal_revenue_pct: float = 0.0
    coal_power_generation_pct: float = 0.0
    arctic_oil_revenue_pct: float = 0.0
    oil_sands_revenue_pct: float = 0.0
    nuclear_weapons_involved: bool = False
    ungc_violation: bool = False
    # Custom flags
    custom_exclusion_flags: dict[str, bool] = field(default_factory=dict)


@dataclass
class ScreeningBreach:
    """A single exclusion breach."""
    holding_id: str
    security_name: str
    isin: Optional[str]
    weight_pct: float
    category: str
    category_name: str
    rule_description: str
    actual_exposure: float  # Revenue % or flag
    threshold: float
    severity: str  # "hard" (zero tolerance) / "soft" (threshold breach)


@dataclass
class FundScreeningResult:
    """Exclusion screening result for a fund."""
    fund_id: str
    fund_name: str
    sfdr_classification: str
    total_holdings_screened: int
    breaches: list[ScreeningBreach]
    breach_count: int
    breached_weight_pct: float
    is_compliant: bool
    hard_breach_count: int  # Zero-tolerance violations
    soft_breach_count: int  # Threshold violations
    category_summary: dict[str, int]  # category -> breach count


@dataclass
class CustomExclusionRule:
    """User-defined exclusion rule."""
    rule_id: str
    name: str
    description: str
    flag_key: str  # Key in custom_exclusion_flags
    applies_to_sfdr: list[str] = field(default_factory=lambda: ["art8", "art8plus", "art9"])


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ExclusionListEngine:
    """Screen holdings against exclusion criteria."""

    def __init__(
        self,
        custom_rules: list[CustomExclusionRule] | None = None,
    ):
        self.custom_rules = custom_rules or []

    def screen_fund(
        self,
        fund_id: str,
        fund_name: str,
        sfdr_classification: str,
        holdings: list[HoldingScreenInput],
    ) -> FundScreeningResult:
        """Screen all holdings against applicable exclusion rules."""
        breaches: list[ScreeningBreach] = []
        applicable_rules = self._get_applicable_rules(sfdr_classification)

        for h in holdings:
            holding_breaches = self._screen_holding(h, applicable_rules, sfdr_classification)
            breaches.extend(holding_breaches)

        # De-duplicate: a holding can breach multiple categories
        breach_holdings = set(b.holding_id for b in breaches)
        breached_weight = sum(
            h.weight_pct for h in holdings if h.holding_id in breach_holdings
        )

        hard = sum(1 for b in breaches if b.severity == "hard")
        soft = sum(1 for b in breaches if b.severity == "soft")

        cat_summary: dict[str, int] = {}
        for b in breaches:
            cat_summary[b.category] = cat_summary.get(b.category, 0) + 1

        return FundScreeningResult(
            fund_id=fund_id,
            fund_name=fund_name,
            sfdr_classification=sfdr_classification,
            total_holdings_screened=len(holdings),
            breaches=breaches,
            breach_count=len(breaches),
            breached_weight_pct=round(breached_weight, 2),
            is_compliant=len(breaches) == 0,
            hard_breach_count=hard,
            soft_breach_count=soft,
            category_summary=cat_summary,
        )

    def get_rules(self, sfdr_classification: str = "art8") -> list[dict]:
        """Return all applicable rules for a given SFDR classification."""
        return self._get_applicable_rules(sfdr_classification)

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _get_applicable_rules(self, sfdr: str) -> list[dict]:
        """Filter default + custom rules by SFDR classification."""
        rules = []
        for cat, rule in DEFAULT_EXCLUSION_RULES.items():
            if sfdr in rule.get("applies_to", []):
                rules.append({"category": cat, **rule})

        for cr in self.custom_rules:
            if sfdr in cr.applies_to_sfdr:
                rules.append({
                    "category": f"custom_{cr.rule_id}",
                    "name": cr.name,
                    "description": cr.description,
                    "flag_key": cr.flag_key,
                    "revenue_threshold_pct": 0.0,
                    "is_custom": True,
                })
        return rules

    def _screen_holding(
        self,
        h: HoldingScreenInput,
        rules: list[dict],
        sfdr: str,
    ) -> list[ScreeningBreach]:
        """Screen a single holding against all applicable rules."""
        breaches = []

        for rule in rules:
            cat = rule["category"]

            # Custom rules
            if rule.get("is_custom"):
                flag_key = rule.get("flag_key", "")
                if h.custom_exclusion_flags.get(flag_key, False):
                    breaches.append(ScreeningBreach(
                        holding_id=h.holding_id, security_name=h.security_name,
                        isin=h.isin, weight_pct=h.weight_pct,
                        category=cat, category_name=rule["name"],
                        rule_description=rule["description"],
                        actual_exposure=1.0, threshold=0.0,
                        severity="hard",
                    ))
                continue

            # Standard rules
            breach = self._check_standard_rule(h, cat, rule)
            if breach:
                breaches.append(breach)

        return breaches

    def _check_standard_rule(
        self, h: HoldingScreenInput, category: str, rule: dict
    ) -> Optional[ScreeningBreach]:
        """Check a single standard exclusion rule."""
        threshold = rule.get("revenue_threshold_pct", 0.0)
        exposure = 0.0
        breached = False

        if category == ExclusionCategory.CONTROVERSIAL_WEAPONS.value:
            exposure = h.controversial_weapons_revenue_pct
            breached = exposure > threshold

        elif category == ExclusionCategory.TOBACCO.value:
            exposure = h.tobacco_revenue_pct
            breached = exposure > threshold

        elif category == ExclusionCategory.THERMAL_COAL.value:
            gen_threshold = rule.get("generation_threshold_pct", 30.0)
            if h.thermal_coal_revenue_pct > threshold:
                exposure = h.thermal_coal_revenue_pct
                breached = True
            elif h.coal_power_generation_pct > gen_threshold:
                exposure = h.coal_power_generation_pct
                threshold = gen_threshold
                breached = True

        elif category == ExclusionCategory.ARCTIC_OIL_GAS.value:
            exposure = h.arctic_oil_revenue_pct
            breached = exposure > threshold

        elif category == ExclusionCategory.OIL_SANDS.value:
            exposure = h.oil_sands_revenue_pct
            breached = exposure > threshold

        elif category == ExclusionCategory.NUCLEAR_WEAPONS.value:
            breached = h.nuclear_weapons_involved
            exposure = 1.0 if breached else 0.0

        elif category == ExclusionCategory.UNGC_VIOLATIONS.value:
            breached = h.ungc_violation
            exposure = 1.0 if breached else 0.0

        if not breached:
            return None

        severity = "hard" if threshold == 0.0 else "soft"

        return ScreeningBreach(
            holding_id=h.holding_id,
            security_name=h.security_name,
            isin=h.isin,
            weight_pct=h.weight_pct,
            category=category,
            category_name=rule["name"],
            rule_description=rule["description"],
            actual_exposure=exposure,
            threshold=threshold,
            severity=severity,
        )
