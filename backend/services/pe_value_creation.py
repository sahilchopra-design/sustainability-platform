"""
PE Value Creation Plan Engine
==============================
Identifies ESG improvement levers per sector, estimates cost/benefit,
generates implementation timelines with milestones, and projects
exit value impact from ESG improvements.

References:
- McKinsey — ESG value creation in PE
- BCG — ESG as a value driver in PE transactions
- ILPA — ESG integration in private markets
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference Data — ESG Improvement Levers by Sector
# ---------------------------------------------------------------------------

SECTOR_LEVERS: dict[str, list[dict]] = {
    "Technology": [
        {"lever_id": "TECH_1", "name": "Data Centre Energy Efficiency", "category": "environmental",
         "capex_eur_range": (200_000, 2_000_000), "annual_savings_pct": (5, 15),
         "ebitda_uplift_pct": (1, 3), "implementation_months": 12,
         "description": "Optimise PUE through cooling upgrades and renewable energy procurement"},
        {"lever_id": "TECH_2", "name": "Supply Chain Carbon Mapping", "category": "environmental",
         "capex_eur_range": (50_000, 300_000), "annual_savings_pct": (2, 5),
         "ebitda_uplift_pct": (0.5, 1.5), "implementation_months": 6,
         "description": "Map and reduce Scope 3 emissions in hardware supply chain"},
        {"lever_id": "TECH_3", "name": "DEI Programme", "category": "social",
         "capex_eur_range": (30_000, 150_000), "annual_savings_pct": (0, 2),
         "ebitda_uplift_pct": (0.5, 2), "implementation_months": 18,
         "description": "Diversity, equity & inclusion programme to improve retention and innovation"},
        {"lever_id": "TECH_4", "name": "Data Privacy & Governance", "category": "governance",
         "capex_eur_range": (100_000, 500_000), "annual_savings_pct": (0, 1),
         "ebitda_uplift_pct": (0, 1), "implementation_months": 9,
         "description": "ISO 27001 + GDPR compliance framework to reduce regulatory risk"},
    ],
    "Healthcare": [
        {"lever_id": "HC_1", "name": "Clinical Waste Reduction", "category": "environmental",
         "capex_eur_range": (100_000, 800_000), "annual_savings_pct": (3, 8),
         "ebitda_uplift_pct": (1, 2), "implementation_months": 12,
         "description": "Waste segregation, recycling, and incineration reduction"},
        {"lever_id": "HC_2", "name": "Patient Safety Programme", "category": "social",
         "capex_eur_range": (50_000, 400_000), "annual_savings_pct": (2, 6),
         "ebitda_uplift_pct": (1, 3), "implementation_months": 12,
         "description": "Reduce adverse events and improve outcomes tracking"},
        {"lever_id": "HC_3", "name": "Board & Ethics Committee", "category": "governance",
         "capex_eur_range": (20_000, 100_000), "annual_savings_pct": (0, 1),
         "ebitda_uplift_pct": (0, 1), "implementation_months": 6,
         "description": "Establish independent board and clinical ethics committee"},
    ],
    "Industrials": [
        {"lever_id": "IND_1", "name": "Energy Efficiency Retrofit", "category": "environmental",
         "capex_eur_range": (500_000, 5_000_000), "annual_savings_pct": (8, 20),
         "ebitda_uplift_pct": (2, 5), "implementation_months": 18,
         "description": "Equipment upgrades, heat recovery, LED lighting, building envelope"},
        {"lever_id": "IND_2", "name": "Health & Safety Programme", "category": "social",
         "capex_eur_range": (50_000, 300_000), "annual_savings_pct": (1, 4),
         "ebitda_uplift_pct": (0.5, 2), "implementation_months": 9,
         "description": "ISO 45001 implementation, incident reporting, training"},
        {"lever_id": "IND_3", "name": "Circular Economy Transition", "category": "environmental",
         "capex_eur_range": (200_000, 2_000_000), "annual_savings_pct": (5, 12),
         "ebitda_uplift_pct": (1, 4), "implementation_months": 24,
         "description": "Product redesign for recyclability, waste-to-resource programmes"},
        {"lever_id": "IND_4", "name": "Anti-Bribery & Compliance", "category": "governance",
         "capex_eur_range": (30_000, 200_000), "annual_savings_pct": (0, 1),
         "ebitda_uplift_pct": (0, 0.5), "implementation_months": 6,
         "description": "Anti-corruption framework, third-party due diligence, whistleblower policy"},
    ],
    "Consumer Staples": [
        {"lever_id": "CS_1", "name": "Sustainable Sourcing", "category": "environmental",
         "capex_eur_range": (100_000, 1_000_000), "annual_savings_pct": (2, 8),
         "ebitda_uplift_pct": (1, 3), "implementation_months": 18,
         "description": "Certified sustainable raw materials (palm oil, cocoa, soy)"},
        {"lever_id": "CS_2", "name": "Packaging Reduction", "category": "environmental",
         "capex_eur_range": (50_000, 500_000), "annual_savings_pct": (3, 10),
         "ebitda_uplift_pct": (1, 3), "implementation_months": 12,
         "description": "Reduce plastic packaging, increase recyclable content"},
        {"lever_id": "CS_3", "name": "Living Wage & Supply Chain Labour", "category": "social",
         "capex_eur_range": (0, 200_000), "annual_savings_pct": (0, 2),
         "ebitda_uplift_pct": (0.5, 1.5), "implementation_months": 12,
         "description": "Living wage verification and supply chain labour audits"},
    ],
    "Energy": [
        {"lever_id": "EN_1", "name": "Methane Leak Detection & Repair", "category": "environmental",
         "capex_eur_range": (300_000, 3_000_000), "annual_savings_pct": (5, 15),
         "ebitda_uplift_pct": (2, 5), "implementation_months": 12,
         "description": "LDAR programme + continuous monitoring to reduce fugitive emissions"},
        {"lever_id": "EN_2", "name": "Renewable Energy Transition Plan", "category": "environmental",
         "capex_eur_range": (1_000_000, 20_000_000), "annual_savings_pct": (0, 5),
         "ebitda_uplift_pct": (0, 2), "implementation_months": 36,
         "description": "SBTi-aligned transition plan with renewable capex roadmap"},
        {"lever_id": "EN_3", "name": "Community Engagement", "category": "social",
         "capex_eur_range": (50_000, 500_000), "annual_savings_pct": (0, 1),
         "ebitda_uplift_pct": (0, 1), "implementation_months": 12,
         "description": "Social licence to operate: local employment, community investment"},
    ],
}

# Default levers for sectors not in reference data
DEFAULT_LEVERS: list[dict] = [
    {"lever_id": "DEF_1", "name": "Carbon Footprint Measurement", "category": "environmental",
     "capex_eur_range": (20_000, 100_000), "annual_savings_pct": (0, 2),
     "ebitda_uplift_pct": (0, 0.5), "implementation_months": 3,
     "description": "Establish GHG inventory (Scope 1+2+3) as baseline for reduction targets"},
    {"lever_id": "DEF_2", "name": "ESG Governance Framework", "category": "governance",
     "capex_eur_range": (10_000, 80_000), "annual_savings_pct": (0, 1),
     "ebitda_uplift_pct": (0, 0.5), "implementation_months": 6,
     "description": "Board ESG committee, ESG policy, KPI reporting framework"},
    {"lever_id": "DEF_3", "name": "Employee Wellbeing Programme", "category": "social",
     "capex_eur_range": (10_000, 100_000), "annual_savings_pct": (1, 3),
     "ebitda_uplift_pct": (0.5, 1.5), "implementation_months": 6,
     "description": "Mental health, flexible working, engagement survey, retention improvement"},
]

# EBITDA multiple expansion from ESG improvement (basis points per ESG score improvement)
ESG_MULTIPLE_EXPANSION_BPS: int = 25  # 0.25x multiple per 1.0 ESG score improvement


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class LeverEstimate:
    """Estimated cost/benefit for a single ESG lever."""
    lever_id: str
    name: str
    category: str
    description: str
    capex_eur_low: float
    capex_eur_high: float
    capex_eur_mid: float
    annual_savings_pct_low: float
    annual_savings_pct_high: float
    annual_savings_eur_mid: float       # Mid-point savings in EUR
    ebitda_uplift_pct_low: float
    ebitda_uplift_pct_high: float
    ebitda_uplift_eur_mid: float        # Mid-point EBITDA uplift EUR
    implementation_months: int
    roi_multiple: float                 # annual_savings / capex


@dataclass
class Milestone:
    """Implementation milestone."""
    month: int
    description: str
    deliverable: str


@dataclass
class ValueCreationPlan:
    """Complete value creation plan for a portfolio company."""
    company_id: str
    company_name: str
    sector: str
    ebitda_eur: float
    entry_multiple: float
    levers: list[LeverEstimate]
    total_capex_mid_eur: float
    total_annual_savings_mid_eur: float
    total_ebitda_uplift_mid_eur: float
    milestones: list[Milestone]
    # Exit impact
    projected_esg_score_improvement: float
    projected_multiple_expansion: float  # x turns
    projected_exit_multiple: float
    projected_exit_ev_eur: float
    projected_value_creation_eur: float
    plan_duration_months: int


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PEValueCreationEngine:
    """Generates ESG value creation plans for PE portfolio companies."""

    def generate_plan(
        self,
        company_id: str,
        company_name: str,
        sector: str,
        ebitda_eur: float,
        entry_multiple: float,
        current_esg_score: float = 50.0,
        revenue_eur: float = 0.0,
    ) -> ValueCreationPlan:
        """Generate a value creation plan for a portfolio company."""
        # 1. Get sector-specific levers
        raw_levers = SECTOR_LEVERS.get(sector, DEFAULT_LEVERS)

        # 2. Estimate costs and benefits
        levers = []
        total_capex = 0.0
        total_savings = 0.0
        total_ebitda = 0.0

        for lev in raw_levers:
            capex_low, capex_high = lev["capex_eur_range"]
            capex_mid = (capex_low + capex_high) / 2

            sav_low, sav_high = lev["annual_savings_pct"]
            rev_base = revenue_eur if revenue_eur > 0 else ebitda_eur * 4  # rough estimate
            sav_mid_eur = rev_base * (sav_low + sav_high) / 2 / 100

            ebitda_low, ebitda_high = lev["ebitda_uplift_pct"]
            ebitda_mid_eur = ebitda_eur * (ebitda_low + ebitda_high) / 2 / 100

            roi = sav_mid_eur / capex_mid if capex_mid > 0 else 0.0

            levers.append(LeverEstimate(
                lever_id=lev["lever_id"],
                name=lev["name"],
                category=lev["category"],
                description=lev["description"],
                capex_eur_low=capex_low,
                capex_eur_high=capex_high,
                capex_eur_mid=round(capex_mid, 2),
                annual_savings_pct_low=sav_low,
                annual_savings_pct_high=sav_high,
                annual_savings_eur_mid=round(sav_mid_eur, 2),
                ebitda_uplift_pct_low=ebitda_low,
                ebitda_uplift_pct_high=ebitda_high,
                ebitda_uplift_eur_mid=round(ebitda_mid_eur, 2),
                implementation_months=lev["implementation_months"],
                roi_multiple=round(roi, 2),
            ))

            total_capex += capex_mid
            total_savings += sav_mid_eur
            total_ebitda += ebitda_mid_eur

        # 3. Milestones
        milestones = self._generate_milestones(levers)

        # 4. Exit impact
        plan_duration = max((l.implementation_months for l in levers), default=12)
        esg_improvement = min(len(levers) * 3.0, 20.0)  # ~3 points per lever, capped at 20
        multiple_expansion = round(esg_improvement * ESG_MULTIPLE_EXPANSION_BPS / 10000, 2)
        exit_mult = entry_multiple + multiple_expansion
        exit_ebitda = ebitda_eur + total_ebitda
        exit_ev = exit_ebitda * exit_mult
        entry_ev = ebitda_eur * entry_multiple
        value_creation = exit_ev - entry_ev

        return ValueCreationPlan(
            company_id=company_id,
            company_name=company_name,
            sector=sector,
            ebitda_eur=ebitda_eur,
            entry_multiple=entry_multiple,
            levers=levers,
            total_capex_mid_eur=round(total_capex, 2),
            total_annual_savings_mid_eur=round(total_savings, 2),
            total_ebitda_uplift_mid_eur=round(total_ebitda, 2),
            milestones=milestones,
            projected_esg_score_improvement=round(esg_improvement, 1),
            projected_multiple_expansion=multiple_expansion,
            projected_exit_multiple=round(exit_mult, 2),
            projected_exit_ev_eur=round(exit_ev, 2),
            projected_value_creation_eur=round(value_creation, 2),
            plan_duration_months=plan_duration,
        )

    def get_sector_levers(self, sector: str) -> list[dict]:
        """Return available ESG levers for a sector."""
        return SECTOR_LEVERS.get(sector, DEFAULT_LEVERS)

    def get_available_sectors(self) -> list[str]:
        """Return sectors with defined ESG lever sets."""
        return list(SECTOR_LEVERS.keys())

    # -------------------------------------------------------------------
    # Milestone Generation
    # -------------------------------------------------------------------

    def _generate_milestones(self, levers: list[LeverEstimate]) -> list[Milestone]:
        """Generate implementation milestones from levers."""
        milestones = []

        # Sort levers by implementation time
        sorted_levers = sorted(levers, key=lambda l: l.implementation_months)

        # Add kick-off
        milestones.append(Milestone(
            month=0,
            description="Value creation plan kick-off",
            deliverable="Baseline assessment and KPI framework",
        ))

        # Add milestone per lever completion
        for lev in sorted_levers:
            milestones.append(Milestone(
                month=lev.implementation_months,
                description=f"Complete: {lev.name}",
                deliverable=f"{lev.category.title()} improvement — est. EUR {lev.ebitda_uplift_eur_mid:,.0f} EBITDA uplift",
            ))

        # Add annual review
        max_months = max((l.implementation_months for l in levers), default=12)
        if max_months > 12:
            milestones.append(Milestone(
                month=12,
                description="Annual ESG progress review",
                deliverable="KPI dashboard review and plan adjustment",
            ))

        return sorted(milestones, key=lambda m: m.month)
