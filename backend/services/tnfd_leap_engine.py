"""TNFD LEAP Process Assessment Engine (E32)
Implements the full 4-step LEAP approach from TNFD Framework v1.0 (September 2023):
  L — Locate: interfaces with nature; priority locations; value chain scope
  E — Evaluate: dependencies & impacts using ENCORE
  A — Assess: material risks & opportunities; risk/opportunity magnitude
  P — Prepare: strategy response; targets; disclosure completeness
"""

import random
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

BIOMES: List[str] = [
    # Terrestrial (12)
    "Tropical moist forests",
    "Tropical dry forests",
    "Temperate broadleaf forests",
    "Temperate conifer forests",
    "Boreal forests / Taiga",
    "Tropical grasslands & savannas",
    "Temperate grasslands & shrublands",
    "Flooded grasslands & savannas",
    "Montane grasslands & shrublands",
    "Tundra",
    "Mediterranean forests & scrublands",
    "Deserts & xeric shrublands",
    # Marine (5)
    "Coral reefs",
    "Seagrass beds",
    "Mangroves",
    "Open ocean",
    "Coastal & shelf seas",
]

ENCORE_DEPENDENCIES: List[str] = [
    "Water regulation",
    "Climate regulation",
    "Pollination",
    "Soil formation",
    "Pest & disease control",
    "Flood & storm protection",
    "Erosion control",
    "Timber",
    "Freshwater",
    "Wild plants & animals (food)",
    "Wild plants (medicines)",
    "Genetic materials",
    "Fibre & other materials",
    "Marine fish & shellfish",
    "Groundwater",
    "Noise attenuation",
    "Air filtration",
    "Bioremediation",
    "Dilution by atmosphere & ecosystems",
    "Decomposition & fixing",
    "Aesthetic values",
]

ENCORE_IMPACT_DRIVERS: List[str] = [
    "GHG emissions",
    "Water use",
    "Land use change",
    "Soil pollution",
    "Water pollution",
    "Marine pollution",
    "Solid waste",
    "Noise & light pollution",
]

SECTOR_NATURE_MATERIALITY: Dict[str, Dict] = {
    "A01": {
        "sector_name": "Crop & animal production",
        "high_risk_biomes": ["Tropical moist forests", "Tropical grasslands & savannas", "Temperate grasslands & shrublands"],
        "key_dependencies": ["Pollination", "Soil formation", "Water regulation", "Pest & disease control"],
        "key_impacts": ["Land use change", "Water use", "Soil pollution", "Water pollution"],
    },
    "A02": {
        "sector_name": "Forestry & logging",
        "high_risk_biomes": ["Tropical moist forests", "Boreal forests / Taiga", "Temperate broadleaf forests"],
        "key_dependencies": ["Timber", "Climate regulation", "Erosion control", "Flood & storm protection"],
        "key_impacts": ["Land use change", "GHG emissions", "Solid waste"],
    },
    "B05": {
        "sector_name": "Mining of coal",
        "high_risk_biomes": ["Tundra", "Boreal forests / Taiga", "Montane grasslands & shrublands"],
        "key_dependencies": ["Groundwater", "Freshwater", "Soil formation"],
        "key_impacts": ["Land use change", "Water pollution", "Soil pollution", "GHG emissions"],
    },
    "C10": {
        "sector_name": "Food manufacturing",
        "high_risk_biomes": ["Tropical moist forests", "Tropical grasslands & savannas"],
        "key_dependencies": ["Freshwater", "Wild plants & animals (food)", "Pollination", "Climate regulation"],
        "key_impacts": ["Water use", "Water pollution", "Solid waste", "Land use change"],
    },
    "D35": {
        "sector_name": "Electricity & gas supply",
        "high_risk_biomes": ["Coral reefs", "Mangroves", "Seagrass beds", "Boreal forests / Taiga"],
        "key_dependencies": ["Water regulation", "Climate regulation", "Freshwater"],
        "key_impacts": ["GHG emissions", "Water use", "Land use change", "Noise & light pollution"],
    },
    "E36": {
        "sector_name": "Water collection & supply",
        "high_risk_biomes": ["Flooded grasslands & savannas", "Temperate broadleaf forests"],
        "key_dependencies": ["Water regulation", "Freshwater", "Groundwater", "Climate regulation"],
        "key_impacts": ["Water use", "Water pollution", "Land use change"],
    },
    "F41": {
        "sector_name": "Construction",
        "high_risk_biomes": ["Temperate broadleaf forests", "Tropical dry forests", "Mediterranean forests & scrublands"],
        "key_dependencies": ["Erosion control", "Flood & storm protection", "Soil formation"],
        "key_impacts": ["Land use change", "Soil pollution", "Noise & light pollution", "Solid waste"],
    },
    "G46": {
        "sector_name": "Wholesale trade",
        "high_risk_biomes": ["Tropical moist forests", "Tropical grasslands & savannas"],
        "key_dependencies": ["Wild plants & animals (food)", "Timber", "Genetic materials"],
        "key_impacts": ["GHG emissions", "Solid waste", "Water pollution"],
    },
    "H50": {
        "sector_name": "Water transport",
        "high_risk_biomes": ["Coral reefs", "Seagrass beds", "Open ocean", "Coastal & shelf seas"],
        "key_dependencies": ["Marine fish & shellfish", "Climate regulation"],
        "key_impacts": ["Marine pollution", "GHG emissions", "Noise & light pollution"],
    },
    "K64": {
        "sector_name": "Financial services",
        "high_risk_biomes": ["Tropical moist forests", "Coral reefs", "Mangroves"],
        "key_dependencies": ["Climate regulation", "Flood & storm protection", "Freshwater"],
        "key_impacts": ["GHG emissions", "Land use change"],  # financed impacts
    },
    "L68": {
        "sector_name": "Real estate",
        "high_risk_biomes": ["Temperate broadleaf forests", "Flooded grasslands & savannas", "Mediterranean forests & scrublands"],
        "key_dependencies": ["Flood & storm protection", "Air filtration", "Climate regulation"],
        "key_impacts": ["Land use change", "Noise & light pollution", "Soil pollution"],
    },
    "M72": {
        "sector_name": "Scientific research",
        "high_risk_biomes": ["Tundra", "Tropical moist forests", "Montane grasslands & shrublands"],
        "key_dependencies": ["Genetic materials", "Wild plants (medicines)", "Climate regulation"],
        "key_impacts": ["GHG emissions", "Noise & light pollution"],
    },
    "N77": {
        "sector_name": "Rental & leasing",
        "high_risk_biomes": ["Temperate grasslands & shrublands"],
        "key_dependencies": ["Climate regulation", "Freshwater"],
        "key_impacts": ["GHG emissions", "Solid waste"],
    },
    "C20": {
        "sector_name": "Chemical manufacturing",
        "high_risk_biomes": ["Coral reefs", "Coastal & shelf seas", "Flooded grasslands & savannas"],
        "key_dependencies": ["Freshwater", "Bioremediation", "Decomposition & fixing", "Dilution by atmosphere & ecosystems"],
        "key_impacts": ["Water pollution", "Soil pollution", "GHG emissions", "Marine pollution"],
    },
    "C24": {
        "sector_name": "Basic metals",
        "high_risk_biomes": ["Tundra", "Boreal forests / Taiga", "Montane grasslands & shrublands"],
        "key_dependencies": ["Freshwater", "Groundwater", "Soil formation"],
        "key_impacts": ["Land use change", "Water pollution", "Soil pollution", "GHG emissions"],
    },
}

LEAP_MATURITY_LEVELS: List[Dict] = [
    {"level": "initial",     "min_score": 0,  "description": "Ad-hoc nature-related disclosures; no systematic LEAP process"},
    {"level": "developing",  "min_score": 40, "description": "LEAP initiated; partial data; some priority locations identified"},
    {"level": "established", "min_score": 60, "description": "Full LEAP cycle completed; targets set; TNFD disclosure aligned"},
    {"level": "leading",     "min_score": 80, "description": "Best-in-class; third-party verified; Science-Based Targets for Nature"},
]

RISK_MAGNITUDE_LABELS: List[Dict] = [
    {"label": "low",       "min_score": 0},
    {"label": "medium",    "min_score": 25},
    {"label": "high",      "min_score": 55},
    {"label": "very_high", "min_score": 75},
]

CROSS_FRAMEWORK_MAP: Dict[str, Any] = {
    "ESRS_E4": {
        "name": "CSRD ESRS E4 — Biodiversity & Ecosystems",
        "alignment": "LEAP underpins ESRS E4 double materiality; DR-E4-4 location data, DR-E4-7 dependencies & impacts",
        "mandatory_dps": ["E4-1", "E4-2", "E4-3", "E4-4", "E4-5"],
    },
    "EU_TAXONOMY_DNSH": {
        "name": "EU Taxonomy — Do No Significant Harm (Biodiversity criterion)",
        "alignment": "LEAP location & evaluate steps map to DNSH biodiversity screening for all 6 objectives",
        "articles": ["Art 17(b)", "Annex I-VI DNSH criteria"],
    },
    "CSRD": {
        "name": "CSRD — Corporate Sustainability Reporting Directive",
        "alignment": "LEAP Prepare step feeds CSRD double materiality assessment for nature topics",
        "effective_date": "FY2024 (large PIEs), FY2025 (large companies), FY2026 (SMEs)",
    },
    "TNFD_SFDR_ART9": {
        "name": "SFDR Article 9 — Nature-themed financial products",
        "alignment": "TNFD LEAP outputs satisfy Art 9 PAI indicators 7-14 (biodiversity-sensitive areas)",
        "pai_indicators": [7, 8, 9, 10, 11, 12, 13, 14],
    },
    "GRI_304": {
        "name": "GRI 304 — Biodiversity",
        "alignment": "LEAP Locate maps to GRI 304-1; Evaluate to GRI 304-2; Assess to GRI 304-4",
        "disclosures": ["304-1", "304-2", "304-3", "304-4"],
    },
    "GRI_101_BIODIVERSITY": {
        "name": "GRI 101 — Biodiversity 2024 (updated standard)",
        "alignment": "LEAP full cycle aligns with GRI 101 material topic identification and management approach",
        "effective_date": "2026",
    },
}


# ── Engine ────────────────────────────────────────────────────────────────────

class TNFDLEAPEngine:
    """TNFD LEAP Process Assessment Engine.

    All outputs are deterministic for a given entity_id using a seeded RNG.
    No external data sources required; constants provide the reference framework.
    """

    def __init__(self) -> None:
        pass

    def _rng(self, entity_id: str) -> random.Random:
        seed = hash(entity_id) & 0xFFFFFFFF
        return random.Random(seed)

    def _get_sector_profile(self, sector: str) -> Dict:
        return SECTOR_NATURE_MATERIALITY.get(
            sector,
            {
                "sector_name": "General",
                "high_risk_biomes": ["Tropical moist forests", "Coral reefs"],
                "key_dependencies": ["Climate regulation", "Freshwater", "Pollination"],
                "key_impacts": ["GHG emissions", "Land use change", "Water use"],
            },
        )

    def _score_to_magnitude(self, score: float) -> str:
        label = "low"
        for entry in RISK_MAGNITUDE_LABELS:
            if score >= entry["min_score"]:
                label = entry["label"]
        return label

    def _score_to_maturity(self, score: float) -> str:
        level = "initial"
        for entry in LEAP_MATURITY_LEVELS:
            if score >= entry["min_score"]:
                level = entry["level"]
        return level

    # ── Step L: Locate ────────────────────────────────────────────────────────

    def locate_assessment(
        self,
        entity_id: str,
        sector: str,
        value_chain_scope: Optional[Dict] = None,
        locations: Optional[List] = None,
    ) -> Dict:
        """Step L — Locate: identify interfaces with nature across value chain."""
        rng = self._rng(f"{entity_id}:locate")
        profile = self._get_sector_profile(sector)

        locate_score = rng.uniform(30, 95)

        # Priority locations
        num_locations = rng.randint(3, 5)
        sensitivity_options = ["Very High", "High", "Medium", "Low"]
        countries = ["Brazil", "Indonesia", "DR Congo", "Australia", "India", "China", "USA", "Germany", "Vietnam", "Peru"]
        priority_locations = []
        for i in range(num_locations):
            biome = rng.choice(profile["high_risk_biomes"] + BIOMES[:4])
            priority_locations.append({
                "location_id": f"LOC-{i+1:03d}",
                "location_name": f"Site {chr(65+i)} — {rng.choice(countries)}",
                "country": rng.choice(countries),
                "biome": biome,
                "sensitivity": rng.choice(sensitivity_options),
                "protected_area_overlap": rng.choice([True, False]),
                "key_biodiversity_area": rng.random() > 0.6,
                "proximity_km": round(rng.uniform(0.5, 50.0), 1),
            })

        # Value chain scope
        vc = value_chain_scope or {
            "upstream_coverage_pct": round(rng.uniform(30, 85), 1),
            "operations_coverage_pct": round(rng.uniform(60, 98), 1),
            "downstream_coverage_pct": round(rng.uniform(15, 60), 1),
        }

        sensitive_ecosystems = rng.sample(BIOMES, min(4, rng.randint(2, 4)))

        return {
            "step": "L",
            "step_name": "Locate",
            "locate_score": round(locate_score, 1),
            "priority_locations": priority_locations,
            "num_priority_locations": len(priority_locations),
            "value_chain_scope": vc,
            "sensitive_ecosystems": sensitive_ecosystems,
            "data_sources_used": ["Company site register", "IBAT (Integrated Biodiversity Assessment Tool)", "WDPA (Protected Planet)"],
            "completeness_notes": "Upstream Tier 2+ suppliers not fully mapped" if vc.get("upstream_coverage_pct", 100) < 70 else "Coverage adequate",
        }

    # ── Step E: Evaluate ─────────────────────────────────────────────────────

    def evaluate_assessment(
        self,
        entity_id: str,
        sector: str,
        locate_result: Dict,
    ) -> Dict:
        """Step E — Evaluate: assess dependencies and impacts using ENCORE."""
        rng = self._rng(f"{entity_id}:evaluate")
        profile = self._get_sector_profile(sector)

        evaluate_score = rng.uniform(25, 90)

        # Dependencies
        dep_levels = ["Critical", "High", "Medium", "Low"]
        num_deps = rng.randint(5, 8)
        selected_deps = rng.sample(profile["key_dependencies"] + ENCORE_DEPENDENCIES[:6], min(num_deps, len(profile["key_dependencies"]) + 6))
        dependencies = []
        for dep in selected_deps:
            dependencies.append({
                "ecosystem_service": dep,
                "dependency_level": rng.choice(dep_levels),
                "business_process": rng.choice(["Core production", "Supply chain", "Operations", "Product delivery"]),
                "substitutability": rng.choice(["Non-substitutable", "Partially substitutable", "Substitutable"]),
                "encore_materiality": rng.choice(["High", "Medium", "Low"]),
            })

        # Impacts
        scope_options = ["Local", "Sub-national", "National", "Global"]
        num_impacts = rng.randint(4, 7)
        selected_drivers = rng.sample(profile["key_impacts"] + ENCORE_IMPACT_DRIVERS, min(num_impacts, len(ENCORE_IMPACT_DRIVERS)))
        impacts = []
        for driver in selected_drivers:
            mag = rng.uniform(10, 90)
            impacts.append({
                "impact_driver": driver,
                "magnitude": round(mag, 1),
                "magnitude_label": self._score_to_magnitude(mag),
                "scope": rng.choice(scope_options),
                "irreversibility": rng.choice(["Reversible", "Partially reversible", "Irreversible"]),
                "value_chain_stage": rng.choice(["Upstream", "Own operations", "Downstream"]),
            })

        # Ecosystem condition
        condition_states = ["Good", "Fair", "Poor", "Critical"]
        ecosystem_condition = {
            loc["biome"]: rng.choice(condition_states)
            for loc in locate_result.get("priority_locations", [])
        }

        return {
            "step": "E",
            "step_name": "Evaluate",
            "evaluate_score": round(evaluate_score, 1),
            "dependencies": dependencies,
            "num_dependencies": len(dependencies),
            "impacts": impacts,
            "num_impacts": len(impacts),
            "ecosystem_condition": ecosystem_condition,
            "encore_tool_version": "ENCORE 2.0",
            "assessment_method": "TNFD ENCORE Methodology v1.1",
        }

    # ── Step A: Assess ────────────────────────────────────────────────────────

    def assess_material_risks(
        self,
        entity_id: str,
        sector: str,
        evaluate_result: Dict,
    ) -> Dict:
        """Step A — Assess: identify material nature-related risks and opportunities."""
        rng = self._rng(f"{entity_id}:assess")

        assess_score = rng.uniform(25, 92)

        risk_types = ["Physical — acute", "Physical — chronic", "Transition — policy", "Transition — market", "Systemic — tipping point"]
        time_horizons = ["Short-term (0-3y)", "Medium-term (3-10y)", "Long-term (10y+)"]
        likelihood_levels = ["Likely", "Possible", "Unlikely", "Remote"]

        num_risks = rng.randint(3, 5)
        material_risks = []
        for i in range(num_risks):
            mag = rng.uniform(20, 95)
            material_risks.append({
                "risk_id": f"R{i+1:02d}",
                "description": rng.choice([
                    "Freshwater scarcity impacting operational cooling and processing",
                    "Regulatory expansion of protected area corridors restricting site access",
                    "Pollinator decline reducing crop yields in supply base",
                    "Mangrove loss increasing coastal flood exposure at key facilities",
                    "Soil degradation curtailing raw material availability",
                    "Marine ecosystem collapse disrupting fishery supply chains",
                    "Government nature-related taxes and levies on land use",
                    "Loss of disease regulation services increasing biosecurity costs",
                ]),
                "risk_type": rng.choice(risk_types),
                "time_horizon": rng.choice(time_horizons),
                "likelihood": rng.choice(likelihood_levels),
                "magnitude": round(mag, 1),
                "magnitude_label": self._score_to_magnitude(mag),
                "financial_impact_mn": round(rng.uniform(0.5, 50.0), 2),
                "affected_assets": rng.randint(1, 8),
            })

        opp_types = ["Resource efficiency", "New market", "Resilience", "Green premium", "Regulatory incentive"]
        num_opps = rng.randint(2, 3)
        material_opportunities = []
        for i in range(num_opps):
            material_opportunities.append({
                "opp_id": f"O{i+1:02d}",
                "description": rng.choice([
                    "Nature-based solutions reducing carbon liability and regulatory exposure",
                    "Ecosystem restoration credits generating new revenue stream",
                    "Water stewardship reducing operational costs and community risk",
                    "Biodiversity net gain (BNG) credits from habitat enhancement",
                    "Supply chain resilience premium from nature-positive sourcing",
                ]),
                "opportunity_type": rng.choice(opp_types),
                "time_horizon": rng.choice(time_horizons),
                "estimated_value_mn": round(rng.uniform(0.2, 20.0), 2),
                "implementation_readiness": rng.choice(["Ready", "Requires investment", "Long-term"]),
            })

        avg_risk_mag = sum(r["magnitude"] for r in material_risks) / len(material_risks)

        return {
            "step": "A",
            "step_name": "Assess",
            "assess_score": round(assess_score, 1),
            "material_risks": material_risks,
            "material_opportunities": material_opportunities,
            "risk_magnitude": self._score_to_magnitude(avg_risk_mag),
            "risk_magnitude_score": round(avg_risk_mag, 1),
            "opportunity_magnitude": rng.choice(["low", "medium", "high"]),
            "total_financial_exposure_mn": round(sum(r["financial_impact_mn"] for r in material_risks), 2),
            "total_opportunity_value_mn": round(sum(o["estimated_value_mn"] for o in material_opportunities), 2),
            "double_materiality_confirmed": rng.random() > 0.3,
        }

    # ── Step P: Prepare ───────────────────────────────────────────────────────

    def prepare_response(
        self,
        entity_id: str,
        assess_result: Dict,
    ) -> Dict:
        """Step P — Prepare: strategy, targets, and disclosure completeness."""
        rng = self._rng(f"{entity_id}:prepare")

        prepare_score = rng.uniform(20, 88)

        strategy_response = {
            "nature_policy_adopted": rng.random() > 0.4,
            "board_oversight": rng.choice(["Full board", "Board committee", "Management only", "None"]),
            "nature_in_risk_register": rng.random() > 0.5,
            "nature_in_strategy": rng.random() > 0.45,
            "engagement_plan": rng.random() > 0.55,
            "nature_positive_commitment": rng.random() > 0.35,
            "third_party_verification": rng.random() > 0.6,
        }

        target_types = [
            "No net deforestation by 2025 across direct operations",
            "50% reduction in freshwater withdrawal intensity by 2030",
            "Net positive impact on biodiversity for new developments by 2027",
            "Zero conversion of natural ecosystems in supply base by 2026",
            "Science-Based Targets for Nature aligned pathway adopted by 2025",
            "Achieve biodiversity net gain of 10% on all construction projects by 2030",
        ]
        num_targets = rng.randint(2, 3)
        targets_set = []
        for t in rng.sample(target_types, num_targets):
            targets_set.append({
                "target_description": t,
                "target_year": rng.choice([2025, 2026, 2027, 2028, 2030]),
                "baseline_year": rng.choice([2019, 2020, 2021, 2022]),
                "progress_pct": round(rng.uniform(0, 70), 1),
                "sbtn_aligned": rng.random() > 0.5,
                "verified": rng.random() > 0.6,
            })

        disclosure_completeness_pct = round(rng.uniform(35, 92), 1)

        return {
            "step": "P",
            "step_name": "Prepare",
            "prepare_score": round(prepare_score, 1),
            "strategy_response": strategy_response,
            "targets_set": targets_set,
            "num_targets": len(targets_set),
            "disclosure_completeness_pct": disclosure_completeness_pct,
            "tnfd_recommended_disclosures_met": int(disclosure_completeness_pct / 100 * 14),
            "tnfd_recommended_disclosures_total": 14,
            "improvement_areas": rng.sample([
                "Formalise nature policy with board sign-off",
                "Expand ENCORE assessment to Tier 2 suppliers",
                "Set quantitative biodiversity targets",
                "Commission third-party verification of LEAP process",
                "Integrate nature risks into financial risk management",
                "Engage investors on TNFD disclosure timeline",
            ], rng.randint(2, 4)),
        }

    # ── Full LEAP ─────────────────────────────────────────────────────────────

    def run_full_leap(
        self,
        entity_id: str,
        sector: str,
        reporting_period: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """Run all 4 LEAP steps and return comprehensive assessment dict."""
        rng = self._rng(entity_id)

        period = reporting_period or str(date.today().year - 1)
        assessment_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Run each step
        locate = self.locate_assessment(entity_id, sector, **{k: v for k, v in kwargs.items() if k in ("value_chain_scope", "locations")})
        evaluate = self.evaluate_assessment(entity_id, sector, locate)
        assess = self.assess_material_risks(entity_id, sector, evaluate)
        prepare = self.prepare_response(entity_id, assess)

        # Overall score
        step_scores = [
            locate["locate_score"],
            evaluate["evaluate_score"],
            assess["assess_score"],
            prepare["prepare_score"],
        ]
        overall_score = round(sum(step_scores) / 4, 1)
        maturity = self._score_to_maturity(overall_score)

        # Priority actions
        priority_actions = [
            {
                "action": action,
                "priority": rng.choice(["Critical", "High", "Medium"]),
                "effort": rng.choice(["Low", "Medium", "High"]),
                "timeframe": rng.choice(["Immediate (0-6m)", "Short-term (6-18m)", "Medium-term (18-36m)"]),
            }
            for action in rng.sample([
                "Complete biodiversity baseline survey for all Tier 1 sites",
                "Integrate TNFD disclosures into annual report",
                "Establish nature-related KPIs and board reporting cadence",
                "Conduct ENCORE dependency mapping for top 20 suppliers",
                "Develop nature-positive transition plan",
                "Assess exposure to high biodiversity value areas in supply chain",
                "Set science-based targets for nature (SBTN)",
                "Commission third-party LEAP process audit",
            ], rng.randint(3, 5))
        ]

        return {
            "assessment_id": assessment_id,
            "entity_id": entity_id,
            "entity_name": kwargs.get("entity_name", entity_id),
            "sector": sector,
            "reporting_period": period,
            "assessment_date": now,
            # Step results
            "locate_score": locate["locate_score"],
            "evaluate_score": evaluate["evaluate_score"],
            "assess_score": assess["assess_score"],
            "prepare_score": prepare["prepare_score"],
            "overall_leap_score": overall_score,
            "leap_maturity": maturity,
            # Key outputs
            "num_priority_locations": locate["num_priority_locations"],
            "num_dependencies": evaluate["num_dependencies"],
            "num_impacts": evaluate["num_impacts"],
            "num_material_risks": len(assess["material_risks"]),
            "num_material_opportunities": len(assess["material_opportunities"]),
            "risk_magnitude": assess["risk_magnitude"],
            "opportunity_magnitude": assess["opportunity_magnitude"],
            "total_financial_exposure_mn": assess["total_financial_exposure_mn"],
            "disclosure_completeness_pct": prepare["disclosure_completeness_pct"],
            "num_targets_set": prepare["num_targets"],
            # Detail sections
            "locate_detail": locate,
            "evaluate_detail": evaluate,
            "assess_detail": assess,
            "prepare_detail": prepare,
            # Meta
            "priority_actions": priority_actions,
            "cross_framework": CROSS_FRAMEWORK_MAP,
            "framework_version": "TNFD v1.0 (September 2023)",
            "created_at": now,
            "updated_at": now,
        }

    def get_reference_data(self) -> Dict:
        """Return all reference constants for front-end consumption."""
        return {
            "biomes": BIOMES,
            "impact_drivers": ENCORE_IMPACT_DRIVERS,
            "encore_dependencies": ENCORE_DEPENDENCIES,
            "sector_materiality": SECTOR_NATURE_MATERIALITY,
            "leap_maturity_levels": LEAP_MATURITY_LEVELS,
            "risk_magnitude_labels": RISK_MAGNITUDE_LABELS,
            "cross_framework": CROSS_FRAMEWORK_MAP,
        }
