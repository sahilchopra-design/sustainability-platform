"""
EPC Transition Risk Engine
==========================
Scores properties by EPC rating against country-specific MEPS regulatory
timelines (EU Energy Performance of Buildings Directive recast 2024).

Key outputs:
- Transition risk score (0-100) per property
- Years to non-compliance
- Required EPC upgrade gap (rating steps)
- Portfolio-level MEPS exposure summary
- Stranding probability by regulatory deadline

References:
- EU MEPS Directive (EPBD recast 2024)
- Netherlands: EPC C (2023 — done), EPC A (2030 offices), EPC A+ (2050 all)
- UK: MEES EPC B (2030 commercial), EPC C (2030 domestic, proposed)
- France: DPE E (2025), D (2028), C (2034)
- Germany: EPC milestones by building age (GEG 2024)
- EU default: EPC E (2030), D (2033) for non-residential
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EPCRating(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


EPC_RANK: dict[str, int] = {
    "A+": 1, "A": 2, "B": 3, "C": 4,
    "D": 5, "E": 6, "F": 7, "G": 8,
}


# ---------------------------------------------------------------------------
# Regulatory Timelines
# ---------------------------------------------------------------------------

# Each entry: { year: int, minimum_epc: str, scope: str, penalty_eur_m2: float }
MEPS_TIMELINES: dict[str, list[dict]] = {
    "NL": [
        {"year": 2023, "minimum_epc": "C", "scope": "office > 100m2", "penalty_eur_m2": 0},
        {"year": 2030, "minimum_epc": "A", "scope": "office all", "penalty_eur_m2": 25.0},
        {"year": 2050, "minimum_epc": "A+", "scope": "all non-residential", "penalty_eur_m2": 50.0},
    ],
    "GB": [
        {"year": 2025, "minimum_epc": "E", "scope": "commercial leased", "penalty_eur_m2": 15.0},
        {"year": 2030, "minimum_epc": "B", "scope": "commercial all", "penalty_eur_m2": 30.0},
    ],
    "FR": [
        {"year": 2025, "minimum_epc": "E", "scope": "residential rental", "penalty_eur_m2": 10.0},
        {"year": 2028, "minimum_epc": "D", "scope": "residential rental", "penalty_eur_m2": 20.0},
        {"year": 2034, "minimum_epc": "C", "scope": "residential rental", "penalty_eur_m2": 35.0},
    ],
    "DE": [
        {"year": 2027, "minimum_epc": "E", "scope": "non-residential pre-1980", "penalty_eur_m2": 10.0},
        {"year": 2030, "minimum_epc": "D", "scope": "non-residential all", "penalty_eur_m2": 20.0},
        {"year": 2033, "minimum_epc": "C", "scope": "all buildings", "penalty_eur_m2": 35.0},
    ],
    "EU": [  # Default for countries not explicitly listed
        {"year": 2030, "minimum_epc": "E", "scope": "non-residential", "penalty_eur_m2": 15.0},
        {"year": 2033, "minimum_epc": "D", "scope": "non-residential", "penalty_eur_m2": 25.0},
    ],
}


# Risk weights for score composition
SCORE_WEIGHTS = {
    "gap_severity": 0.35,        # How many EPC steps below requirement
    "time_urgency": 0.30,        # How close the deadline is
    "penalty_exposure": 0.20,    # Financial penalty magnitude
    "regulatory_certainty": 0.15 # How firm the regulation is
}

# Regulatory certainty by country (0-1; 1 = legislated and enforced)
REGULATORY_CERTAINTY = {
    "NL": 0.95,  # Enforced since 2023
    "GB": 0.85,  # MEES active but 2030 proposals still under consultation
    "FR": 0.90,  # Loi Climat enacted
    "DE": 0.80,  # GEG 2024 enacted but enforcement details pending
    "EU": 0.70,  # EPBD recast adopted but member-state transposition varies
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class PropertyEPCInput:
    """Input for a single property's EPC transition risk assessment."""
    property_id: str
    name: str
    country: str              # ISO 2-letter
    epc_rating: str           # A+ through G
    floor_area_m2: Decimal    # GIA
    market_value: Decimal     # Current market value (EUR)
    annual_rent: Decimal      # Gross annual rent (EUR)
    building_age: int = 2000  # Year built
    property_type: str = "office"
    is_leased: bool = True


@dataclass
class DeadlineExposure:
    """Exposure at a single regulatory deadline."""
    year: int
    minimum_epc: str
    scope: str
    is_compliant: bool
    gap_steps: int            # 0 if compliant; positive = steps below minimum
    years_remaining: int      # Years until this deadline
    penalty_eur_m2: float
    annual_penalty_estimate: float   # penalty_eur_m2 * floor_area_m2
    stranding_probability: float     # 0-1: likelihood property can't be let/sold


@dataclass
class PropertyTransitionRisk:
    """Full transition risk profile for a single property."""
    property_id: str
    name: str
    country: str
    current_epc: str
    composite_risk_score: float       # 0-100
    risk_band: str                    # Low / Medium / High / Critical
    deadlines: list[DeadlineExposure]
    first_non_compliant_year: Optional[int]
    worst_gap_steps: int              # Largest gap across all deadlines
    total_annual_penalty_at_risk: float
    regulatory_certainty: float


@dataclass
class PortfolioTransitionSummary:
    """Portfolio-level EPC transition risk summary."""
    total_properties: int
    compliant_now_count: int
    compliant_now_pct: float
    at_risk_2030_count: int
    at_risk_2030_pct: float
    at_risk_2033_count: int
    at_risk_2033_pct: float
    total_annual_penalty_exposure: float
    avg_composite_score: float
    risk_distribution: dict[str, int]   # Low/Medium/High/Critical -> count
    worst_properties: list[dict]        # Top 5 highest risk
    gav_at_risk_2030: float             # GAV of non-compliant properties by 2030
    gav_at_risk_pct_2030: float
    property_results: list[PropertyTransitionRisk]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EPCTransitionEngine:
    """Score properties against EPC regulatory timelines."""

    CURRENT_YEAR = 2025

    def assess_property(self, prop: PropertyEPCInput) -> PropertyTransitionRisk:
        """Assess a single property's EPC transition risk."""
        country = prop.country.upper()
        timeline = MEPS_TIMELINES.get(country, MEPS_TIMELINES["EU"])
        cert = REGULATORY_CERTAINTY.get(country, REGULATORY_CERTAINTY["EU"])

        current_rank = EPC_RANK.get(prop.epc_rating, 8)

        deadlines: list[DeadlineExposure] = []
        first_non_compliant: Optional[int] = None
        worst_gap = 0

        for milestone in timeline:
            required_rank = EPC_RANK.get(milestone["minimum_epc"], 8)
            gap = max(0, current_rank - required_rank)
            is_compliant = current_rank <= required_rank
            years_remaining = max(0, milestone["year"] - self.CURRENT_YEAR)
            penalty = milestone.get("penalty_eur_m2", 0.0)
            annual_penalty = float(prop.floor_area_m2) * penalty if not is_compliant else 0.0

            # Stranding probability: higher gap + sooner deadline + higher certainty = more likely
            if is_compliant:
                strand_prob = 0.0
            else:
                time_factor = max(0, 1.0 - years_remaining / 15.0)
                gap_factor = min(1.0, gap / 5.0)
                strand_prob = round(min(1.0, (time_factor * 0.4 + gap_factor * 0.4 + cert * 0.2)), 3)

            de = DeadlineExposure(
                year=milestone["year"],
                minimum_epc=milestone["minimum_epc"],
                scope=milestone["scope"],
                is_compliant=is_compliant,
                gap_steps=gap,
                years_remaining=years_remaining,
                penalty_eur_m2=penalty,
                annual_penalty_estimate=round(annual_penalty, 2),
                stranding_probability=strand_prob,
            )
            deadlines.append(de)

            if not is_compliant:
                worst_gap = max(worst_gap, gap)
                if first_non_compliant is None:
                    first_non_compliant = milestone["year"]

        # Composite risk score (0-100)
        score = self._calculate_composite_score(deadlines, cert)

        # Risk band
        if score >= 75:
            band = "Critical"
        elif score >= 50:
            band = "High"
        elif score >= 25:
            band = "Medium"
        else:
            band = "Low"

        total_penalty = sum(d.annual_penalty_estimate for d in deadlines)

        return PropertyTransitionRisk(
            property_id=prop.property_id,
            name=prop.name,
            country=country,
            current_epc=prop.epc_rating,
            composite_risk_score=score,
            risk_band=band,
            deadlines=deadlines,
            first_non_compliant_year=first_non_compliant,
            worst_gap_steps=worst_gap,
            total_annual_penalty_at_risk=round(total_penalty, 2),
            regulatory_certainty=cert,
        )

    def assess_portfolio(
        self, properties: list[PropertyEPCInput]
    ) -> PortfolioTransitionSummary:
        """Assess EPC transition risk across a portfolio."""
        if not properties:
            return PortfolioTransitionSummary(
                total_properties=0, compliant_now_count=0, compliant_now_pct=0,
                at_risk_2030_count=0, at_risk_2030_pct=0,
                at_risk_2033_count=0, at_risk_2033_pct=0,
                total_annual_penalty_exposure=0, avg_composite_score=0,
                risk_distribution={"Low": 0, "Medium": 0, "High": 0, "Critical": 0},
                worst_properties=[], gav_at_risk_2030=0, gav_at_risk_pct_2030=0,
                property_results=[],
            )

        results = [self.assess_property(p) for p in properties]
        n = len(results)

        # Count compliant now (all deadlines)
        compliant_now = sum(
            1 for r in results if all(d.is_compliant for d in r.deadlines)
        )

        # At risk by 2030 / 2033
        at_risk_2030 = 0
        at_risk_2033 = 0
        gav_at_risk_2030 = Decimal("0")
        total_gav = Decimal("0")

        for r, p in zip(results, properties):
            total_gav += p.market_value
            for d in r.deadlines:
                if d.year <= 2030 and not d.is_compliant:
                    at_risk_2030 += 1
                    gav_at_risk_2030 += p.market_value
                    break
            for d in r.deadlines:
                if d.year <= 2033 and not d.is_compliant:
                    at_risk_2033 += 1
                    break

        # Risk distribution
        dist = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
        for r in results:
            dist[r.risk_band] = dist.get(r.risk_band, 0) + 1

        # Worst 5
        sorted_results = sorted(results, key=lambda r: r.composite_risk_score, reverse=True)
        worst = [
            {
                "property_id": r.property_id,
                "name": r.name,
                "score": r.composite_risk_score,
                "band": r.risk_band,
                "current_epc": r.current_epc,
                "first_non_compliant_year": r.first_non_compliant_year,
            }
            for r in sorted_results[:5]
        ]

        avg_score = round(sum(r.composite_risk_score for r in results) / n, 1)
        total_penalty = sum(r.total_annual_penalty_at_risk for r in results)
        gav_pct = (
            float(gav_at_risk_2030 / total_gav * 100)
            if total_gav > 0 else 0.0
        )

        return PortfolioTransitionSummary(
            total_properties=n,
            compliant_now_count=compliant_now,
            compliant_now_pct=round(compliant_now / n * 100, 1),
            at_risk_2030_count=at_risk_2030,
            at_risk_2030_pct=round(at_risk_2030 / n * 100, 1),
            at_risk_2033_count=at_risk_2033,
            at_risk_2033_pct=round(at_risk_2033 / n * 100, 1),
            total_annual_penalty_exposure=round(total_penalty, 2),
            avg_composite_score=avg_score,
            risk_distribution=dist,
            worst_properties=worst,
            gav_at_risk_2030=round(float(gav_at_risk_2030), 2),
            gav_at_risk_pct_2030=round(gav_pct, 1),
            property_results=results,
        )

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _calculate_composite_score(
        self, deadlines: list[DeadlineExposure], certainty: float
    ) -> float:
        """Weighted composite risk score 0-100."""
        if not deadlines:
            return 0.0

        # If fully compliant with all deadlines, score is 0
        non_compliant = [d for d in deadlines if not d.is_compliant]
        if not non_compliant:
            return 0.0

        # Use worst (highest risk) non-compliant deadline for scoring
        worst = max(non_compliant, key=lambda d: d.gap_steps * (1 / max(d.years_remaining, 1)))

        # Gap severity (0-100): 1 step = 15, max out at ~6 steps
        gap_score = min(100.0, worst.gap_steps * 16.67)

        # Time urgency (0-100): 0 years = 100, 10+ years = 0
        if worst.years_remaining <= 0:
            time_score = 100.0
        else:
            time_score = max(0.0, 100.0 - worst.years_remaining * 10.0)

        # Penalty exposure (0-100): normalise against 50 EUR/m2 max
        penalty_score = min(100.0, worst.penalty_eur_m2 / 50.0 * 100.0)

        # Regulatory certainty (0-100)
        cert_score = certainty * 100.0

        composite = (
            gap_score * SCORE_WEIGHTS["gap_severity"]
            + time_score * SCORE_WEIGHTS["time_urgency"]
            + penalty_score * SCORE_WEIGHTS["penalty_exposure"]
            + cert_score * SCORE_WEIGHTS["regulatory_certainty"]
        )
        return round(min(100.0, max(0.0, composite)), 1)
