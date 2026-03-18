"""
TNFD Assessment Engine
========================
Structured disclosure-assessment engine for the Taskforce on Nature-related
Financial Disclosures (TNFD) framework.  Evaluates an entity's compliance
with the 14 TNFD recommended disclosures across four pillars (Governance,
Strategy, Risk & Impact Management, Metrics & Targets), scores LEAP
readiness, profiles nature-related risks (physical / transition / systemic),
and maps findings to peer frameworks (ISSB S1, CSRD ESRS E4, GRI 304,
CBD GBF Target 15).

Coverage:
  - 14 recommended disclosures (4 pillars)
  - LEAP assessment (Locate, Evaluate, Assess, Prepare) with 16 sub-components
  - 21 ENCORE ecosystem services
  - 3 nature-risk categories (10 sub-types)
  - 8 sector-specific guidance packages
  - 8 cross-framework mappings
  - Double materiality (financial + impact) for nature topics
  - Priority-area criteria (KBAs, protected areas, water-stressed basins)

References:
  - TNFD Recommendations v1.0 (September 2023)
  - TNFD LEAP Approach v1.0
  - ENCORE (Exploring Natural Capital Opportunities, Risks and Exposure)
  - ISSB IFRS S1 / S2
  - CSRD ESRS E4 (Biodiversity and ecosystems)
  - GRI 304 (Biodiversity)
  - CBD Kunming-Montreal Global Biodiversity Framework (GBF) Target 15
  - Science Based Targets Network (SBTN) guidance

API Routes (to be wired in api/v1/routes/tnfd.py):
  POST /api/v1/tnfd/assess-disclosures
  POST /api/v1/tnfd/assess-materiality
  POST /api/v1/tnfd/assess-leap-readiness
  GET  /api/v1/tnfd/recommended-disclosures
  GET  /api/v1/tnfd/leap-phases
  GET  /api/v1/tnfd/encore-ecosystem-services
  GET  /api/v1/tnfd/nature-risk-categories
  GET  /api/v1/tnfd/sector-guidance
  GET  /api/v1/tnfd/cross-framework-map
  GET  /api/v1/tnfd/disclosure-pillar-structure
  GET  /api/v1/tnfd/priority-area-criteria
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("platform.tnfd_assessment")


# ---------------------------------------------------------------------------
# Reference Data Constants
# ---------------------------------------------------------------------------

# 14 TNFD Recommended Disclosures across 4 pillars
TNFD_RECOMMENDED_DISCLOSURES: list[dict] = [
    # Governance (3 disclosures)
    {"id": "GOV-A", "pillar": "Governance", "title": "Board oversight",
     "description": "Board oversight of nature-related dependencies, impacts, risks and opportunities"},
    {"id": "GOV-B", "pillar": "Governance", "title": "Management's role",
     "description": "Management's role in assessing and managing nature-related dependencies, impacts, risks and opportunities"},
    {"id": "GOV-C", "pillar": "Governance", "title": "Human rights policies",
     "description": "Organisation's human rights policies and engagement activities with respect to nature-related issues"},
    # Strategy (4 disclosures)
    {"id": "STR-A", "pillar": "Strategy", "title": "Nature-related dependencies, impacts, risks and opportunities",
     "description": "Nature-related dependencies, impacts, risks and opportunities identified over short, medium, long term"},
    {"id": "STR-B", "pillar": "Strategy", "title": "Impact on business model",
     "description": "Effect on business model, value chain, strategy, financial planning"},
    {"id": "STR-C", "pillar": "Strategy", "title": "Resilience of strategy",
     "description": "Resilience under different nature/climate scenarios"},
    {"id": "STR-D", "pillar": "Strategy", "title": "Location of assets/operations",
     "description": "Location of assets and operations in priority areas"},
    # Risk & Impact Management (3 disclosures)
    {"id": "RIM-A", "pillar": "Risk & Impact Management", "title": "Processes for identifying risks",
     "description": "Processes for identifying and assessing nature-related dependencies, impacts, risks, opportunities"},
    {"id": "RIM-B", "pillar": "Risk & Impact Management", "title": "Processes for managing risks",
     "description": "Processes for managing nature-related dependencies, impacts, risks, opportunities"},
    {"id": "RIM-C", "pillar": "Risk & Impact Management", "title": "Integration into overall risk management",
     "description": "How nature-related risk identification, assessment, management is integrated into overall risk management"},
    # Metrics & Targets (4 disclosures)
    {"id": "MT-A", "pillar": "Metrics & Targets", "title": "Metrics used",
     "description": "Metrics used to assess and manage nature-related risks and opportunities in line with strategy"},
    {"id": "MT-B", "pillar": "Metrics & Targets", "title": "Dependencies & impacts",
     "description": "Metrics for dependencies and impacts on nature"},
    {"id": "MT-C", "pillar": "Metrics & Targets", "title": "Targets and performance",
     "description": "Targets used and performance against targets"},
    {"id": "MT-D", "pillar": "Metrics & Targets", "title": "Nature positive contribution",
     "description": "Nature positive contributions including restoration and conservation"},
]

# TNFD LEAP Phases with sub-components
TNFD_LEAP_PHASES: dict[str, dict] = {
    "LOCATE": {
        "label": "Locate interface with nature",
        "components": [
            {"id": "L1", "title": "Business footprint",
             "description": "Map direct operations, upstream, downstream locations"},
            {"id": "L2", "title": "Nature interface",
             "description": "Identify biomes and ecosystems at each location"},
            {"id": "L3", "title": "Priority location identification",
             "description": "Identify locations in or near sensitive areas (KBAs, protected areas, water-stressed)"},
            {"id": "L4", "title": "Sector-nature interaction",
             "description": "Map sector-specific nature interactions using ENCORE"},
        ],
    },
    "EVALUATE": {
        "label": "Evaluate dependencies and impacts",
        "components": [
            {"id": "E1", "title": "Environmental asset identification",
             "description": "Identify relevant environmental assets and ecosystem services"},
            {"id": "E2", "title": "Dependency identification",
             "description": "Identify nature dependencies using ENCORE classification"},
            {"id": "E3", "title": "Impact identification",
             "description": "Identify nature impacts (drivers of change)"},
            {"id": "E4", "title": "Dependency & impact measurement",
             "description": "Measure magnitude and scope of dependencies and impacts"},
        ],
    },
    "ASSESS": {
        "label": "Assess risks and opportunities",
        "components": [
            {"id": "A1", "title": "Risk identification",
             "description": "Identify corresponding nature-related risks (physical, transition, systemic)"},
            {"id": "A2", "title": "Existing risk mitigation",
             "description": "Assess existing risk mitigation and management actions"},
            {"id": "A3", "title": "Additional risk mitigation",
             "description": "Identify additional risk mitigation and management actions"},
            {"id": "A4", "title": "Materiality assessment",
             "description": "Assess materiality of nature-related risks and opportunities"},
        ],
    },
    "PREPARE": {
        "label": "Prepare to respond and report",
        "components": [
            {"id": "P1", "title": "Strategy and resource allocation",
             "description": "Align strategy and resource allocation with TNFD findings"},
            {"id": "P2", "title": "Target setting",
             "description": "Set targets for nature including science-based targets"},
            {"id": "P3", "title": "Reporting",
             "description": "Prepare TNFD-aligned disclosures"},
            {"id": "P4", "title": "Engagement",
             "description": "Present to investors and stakeholders; engage value chain"},
        ],
    },
}

# ENCORE Ecosystem Services (21 services)
ENCORE_ECOSYSTEM_SERVICES: list[dict] = [
    {"id": "ES01", "name": "Animal-based energy", "category": "Provisioning"},
    {"id": "ES02", "name": "Fibres and other materials", "category": "Provisioning"},
    {"id": "ES03", "name": "Genetic materials", "category": "Provisioning"},
    {"id": "ES04", "name": "Ground water", "category": "Provisioning"},
    {"id": "ES05", "name": "Maintain nursery habitats", "category": "Regulating"},
    {"id": "ES06", "name": "Surface water", "category": "Provisioning"},
    {"id": "ES07", "name": "Water flow maintenance", "category": "Regulating"},
    {"id": "ES08", "name": "Water quality", "category": "Regulating"},
    {"id": "ES09", "name": "Bio-remediation", "category": "Regulating"},
    {"id": "ES10", "name": "Buffering and attenuation of mass flows", "category": "Regulating"},
    {"id": "ES11", "name": "Climate regulation", "category": "Regulating"},
    {"id": "ES12", "name": "Dilution by atmosphere and ecosystems", "category": "Regulating"},
    {"id": "ES13", "name": "Disease control", "category": "Regulating"},
    {"id": "ES14", "name": "Filtration", "category": "Regulating"},
    {"id": "ES15", "name": "Flood and storm protection", "category": "Regulating"},
    {"id": "ES16", "name": "Mass stabilisation and erosion control", "category": "Regulating"},
    {"id": "ES17", "name": "Mediation of sensory impacts", "category": "Regulating"},
    {"id": "ES18", "name": "Pest control", "category": "Regulating"},
    {"id": "ES19", "name": "Pollination", "category": "Regulating"},
    {"id": "ES20", "name": "Soil quality", "category": "Regulating"},
    {"id": "ES21", "name": "Ventilation", "category": "Regulating"},
]

# Nature Risk Categories (3 categories, 10 sub-types)
NATURE_RISK_CATEGORIES: dict[str, dict] = {
    "physical": {
        "label": "Physical Risk",
        "sub_types": [
            "acute_ecosystem_degradation",
            "chronic_ecosystem_decline",
            "resource_depletion",
        ],
    },
    "transition": {
        "label": "Transition Risk",
        "sub_types": [
            "policy_regulation",
            "market_sentiment",
            "technology_substitution",
            "legal_liability",
        ],
    },
    "systemic": {
        "label": "Systemic Risk",
        "sub_types": [
            "ecosystem_collapse",
            "contagion_across_sectors",
            "financial_system_stability",
        ],
    },
}

# Sector-specific TNFD guidance (8 sectors)
TNFD_SECTOR_GUIDANCE: dict[str, dict] = {
    "agriculture": {
        "label": "Agriculture, Forestry and Fishing",
        "priority_nature_topics": [
            "Land use change and deforestation",
            "Water consumption and pollution",
            "Soil degradation and erosion",
            "Pollinator decline",
            "Pesticide and fertiliser runoff",
        ],
        "encore_dependencies": ["ES04", "ES06", "ES08", "ES19", "ES20"],
        "key_biomes": ["Tropical forests", "Grasslands", "Freshwater"],
    },
    "mining": {
        "label": "Mining and Metals",
        "priority_nature_topics": [
            "Habitat destruction from extraction",
            "Water contamination and acid mine drainage",
            "Tailings dam failure risk",
            "Biodiversity offsets adequacy",
            "Post-closure rehabilitation",
        ],
        "encore_dependencies": ["ES04", "ES06", "ES07", "ES08", "ES16"],
        "key_biomes": ["Tropical forests", "Mountains", "Freshwater"],
    },
    "energy": {
        "label": "Energy (Oil, Gas, Power Generation)",
        "priority_nature_topics": [
            "Emissions impact on climate regulation",
            "Pipeline and infrastructure footprint",
            "Cooling water extraction",
            "Marine and coastal habitat disruption",
            "Renewable energy siting conflicts",
        ],
        "encore_dependencies": ["ES06", "ES07", "ES08", "ES11", "ES15"],
        "key_biomes": ["Oceans", "Freshwater", "Coastal wetlands"],
    },
    "financial_services": {
        "label": "Financial Services",
        "priority_nature_topics": [
            "Nature-related financial risks in portfolios",
            "Financed deforestation and land-use change",
            "Exposure to water-stressed assets",
            "Stranded nature-dependent assets",
            "Stewardship and engagement on nature",
        ],
        "encore_dependencies": ["ES04", "ES06", "ES08", "ES11", "ES15"],
        "key_biomes": ["Determined by portfolio composition"],
    },
    "real_estate": {
        "label": "Real Estate and Construction",
        "priority_nature_topics": [
            "Land sealing and habitat fragmentation",
            "Urban ecosystem services loss",
            "Construction material sourcing impact",
            "Biodiversity net gain obligations",
            "Green infrastructure integration",
        ],
        "encore_dependencies": ["ES07", "ES08", "ES10", "ES15", "ES16"],
        "key_biomes": ["Urban", "Grasslands", "Freshwater"],
    },
    "infrastructure": {
        "label": "Infrastructure and Transport",
        "priority_nature_topics": [
            "Linear infrastructure habitat fragmentation",
            "Marine infrastructure impact",
            "Invasive species introduction through transport",
            "Noise and light pollution",
            "Ecosystem connectivity disruption",
        ],
        "encore_dependencies": ["ES05", "ES07", "ES10", "ES15", "ES16"],
        "key_biomes": ["Oceans", "Freshwater", "Forests", "Grasslands"],
    },
    "technology": {
        "label": "Technology and Telecommunications",
        "priority_nature_topics": [
            "Mineral extraction for electronics",
            "E-waste and toxic material disposal",
            "Data centre water consumption",
            "Submarine cable marine impact",
            "Rare earth supply chain nature risk",
        ],
        "encore_dependencies": ["ES04", "ES06", "ES08", "ES12", "ES14"],
        "key_biomes": ["Oceans", "Freshwater", "Tropical forests"],
    },
    "consumer_goods": {
        "label": "Consumer Goods and Retail",
        "priority_nature_topics": [
            "Agricultural commodity sourcing (palm oil, soy, cocoa)",
            "Deforestation-free supply chains",
            "Packaging waste and marine pollution",
            "Water footprint of production",
            "Animal welfare and biodiversity impact",
        ],
        "encore_dependencies": ["ES02", "ES04", "ES06", "ES08", "ES19"],
        "key_biomes": ["Tropical forests", "Oceans", "Freshwater"],
    },
}

# Cross-framework mapping (TNFD to peer standards)
TNFD_CROSS_FRAMEWORK_MAP: list[dict] = [
    {"tnfd_disclosure": "GOV-A", "issb_s1": "IFRS S1 para 26(a)",
     "csrd_esrs_e4": "ESRS 2 GOV-1", "gri": "GRI 2-12, 2-13",
     "cbd_gbf": "Target 15 (governance and disclosure)"},
    {"tnfd_disclosure": "GOV-B", "issb_s1": "IFRS S1 para 26(b)",
     "csrd_esrs_e4": "ESRS 2 GOV-1", "gri": "GRI 2-13",
     "cbd_gbf": "Target 15 (management processes)"},
    {"tnfd_disclosure": "STR-A", "issb_s1": "IFRS S1 para 29",
     "csrd_esrs_e4": "ESRS E4 SBM-3", "gri": "GRI 304-2",
     "cbd_gbf": "Target 15 (risks and opportunities assessment)"},
    {"tnfd_disclosure": "STR-B", "issb_s1": "IFRS S1 para 30-31",
     "csrd_esrs_e4": "ESRS E4 SBM-3", "gri": "GRI 3-3",
     "cbd_gbf": "Target 15 (business model impacts)"},
    {"tnfd_disclosure": "STR-D", "issb_s1": "IFRS S2 para 21",
     "csrd_esrs_e4": "ESRS E4-4 (sensitive areas)", "gri": "GRI 304-1",
     "cbd_gbf": "Target 3 (protected areas 30x30)"},
    {"tnfd_disclosure": "RIM-A", "issb_s1": "IFRS S1 para 34",
     "csrd_esrs_e4": "ESRS E4 IRO-1", "gri": "GRI 3-1",
     "cbd_gbf": "Target 15 (risk identification)"},
    {"tnfd_disclosure": "MT-B", "issb_s1": "IFRS S1 para 37",
     "csrd_esrs_e4": "ESRS E4-5, E4-6 (impact metrics)", "gri": "GRI 304-3, 304-4",
     "cbd_gbf": "Target 15 (dependency and impact metrics)"},
    {"tnfd_disclosure": "MT-C", "issb_s1": "IFRS S1 para 39",
     "csrd_esrs_e4": "ESRS E4-6 (targets)", "gri": "GRI 304-3",
     "cbd_gbf": "Target 15 (targets and performance tracking)"},
]

# Priority area criteria (used in STR-D and LEAP L3)
TNFD_PRIORITY_AREA_CRITERIA: list[dict] = [
    {"id": "PA01", "type": "Key Biodiversity Areas (KBAs)",
     "source": "IUCN / BirdLife / KBA Partnership",
     "description": "Sites contributing significantly to the global persistence of biodiversity"},
    {"id": "PA02", "type": "Protected areas (WDPA)",
     "source": "UN Environment / IUCN WCMC",
     "description": "Nationally or internationally designated protected areas"},
    {"id": "PA03", "type": "Ramsar wetlands",
     "source": "Ramsar Convention",
     "description": "Wetlands of international importance"},
    {"id": "PA04", "type": "UNESCO World Heritage Sites (natural)",
     "source": "UNESCO",
     "description": "Natural or mixed heritage sites of outstanding universal value"},
    {"id": "PA05", "type": "IUCN Red List species habitat",
     "source": "IUCN",
     "description": "Habitats of critically endangered, endangered, or vulnerable species"},
    {"id": "PA06", "type": "Water-stressed basins",
     "source": "WRI Aqueduct / WWF Water Risk Filter",
     "description": "River basins classified as high or extremely high baseline water stress"},
    {"id": "PA07", "type": "Intact Forest Landscapes (IFL)",
     "source": "Global Forest Watch / WRI",
     "description": "Remaining large areas of undisturbed forest ecosystems"},
    {"id": "PA08", "type": "High Carbon Stock (HCS) areas",
     "source": "HCS Approach Steering Group",
     "description": "Forest areas with high carbon stock that should not be cleared"},
]


# ---------------------------------------------------------------------------
# Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TNFDDisclosureScore:
    """Score for a single TNFD recommended disclosure."""
    disclosure_id: str
    pillar: str
    title: str
    compliance_level: str  # "full", "partial", "not_addressed"
    score: float  # 0-100
    findings: list = field(default_factory=list)


@dataclass
class TNFDLEAPPhaseResult:
    """Scoring result for one LEAP phase."""
    phase: str
    phase_label: str
    overall_score: float
    component_scores: list = field(default_factory=list)  # list of dicts
    gaps: list = field(default_factory=list)


@dataclass
class TNFDAssessment:
    """Full TNFD disclosure assessment result."""
    id: str
    entity_name: str
    reporting_year: int
    overall_compliance_pct: float
    disclosure_scores: list = field(default_factory=list)  # list of TNFDDisclosureScore dicts
    leap_results: list = field(default_factory=list)       # list of TNFDLEAPPhaseResult dicts
    nature_risk_profile: dict = field(default_factory=dict)
    priority_locations_count: int = 0
    ecosystem_services_at_risk: list = field(default_factory=list)
    sector_guidance_applied: str = ""
    cross_framework_mapping: dict = field(default_factory=dict)
    gaps: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    created_at: str = ""


@dataclass
class TNFDMaterialityResult:
    """Double-materiality assessment result for nature topics."""
    id: str
    entity_name: str
    reporting_year: int
    material_dependencies: list = field(default_factory=list)
    material_impacts: list = field(default_factory=list)
    financial_materiality_score: float = 0.0
    impact_materiality_score: float = 0.0
    double_materiality_topics: list = field(default_factory=list)
    priority_ecosystem_services: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    created_at: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TNFDAssessmentEngine:
    """TNFD v1.0 disclosure and LEAP readiness assessment engine."""

    # Pillar weights for overall compliance scoring
    _PILLAR_WEIGHTS: dict[str, float] = {
        "Governance": 0.20,
        "Strategy": 0.30,
        "Risk & Impact Management": 0.25,
        "Metrics & Targets": 0.25,
    }

    # LEAP phase weights for readiness scoring
    _LEAP_WEIGHTS: dict[str, float] = {
        "LOCATE": 0.20,
        "EVALUATE": 0.25,
        "ASSESS": 0.35,
        "PREPARE": 0.20,
    }

    # Compliance level thresholds
    _COMPLIANCE_THRESHOLDS: dict[str, tuple[float, float]] = {
        "full": (80.0, 100.0),
        "partial": (30.0, 79.99),
        "not_addressed": (0.0, 29.99),
    }

    # ── Disclosure Assessment ─────────────────────────────────────────────

    def assess_disclosures(
        self,
        entity_name: str,
        reporting_year: int,
        disclosure_data: dict | None = None,
        sector: str | None = None,
    ) -> TNFDAssessment:
        """
        Score each of the 14 TNFD recommended disclosures, run LEAP phase
        scoring, build a nature risk profile, generate cross-framework
        mapping, and identify gaps with recommendations.

        Parameters
        ----------
        entity_name : str
            Name of the reporting entity.
        reporting_year : int
            The fiscal / reporting year being assessed.
        disclosure_data : dict | None
            Mapping of disclosure ID (e.g. "GOV-A") to a dict with keys:
                - "status": "full" | "partial" | "not_addressed"
                - "evidence": list[str] (optional supporting evidence)
                - "priority_locations": int (optional, for STR-D)
                - "ecosystem_services": list[str] (optional, for MT-B)
                - "leap_data": dict (optional, LEAP sub-component statuses)
                - "risk_data": dict (optional, risk scores per category)
        sector : str | None
            One of the TNFD_SECTOR_GUIDANCE keys.
        """
        disclosure_data = disclosure_data or {}

        # --- Score each disclosure -------------------------------------------
        scored: list[dict] = []
        pillar_totals: dict[str, list[float]] = {}

        for disc in TNFD_RECOMMENDED_DISCLOSURES:
            did = disc["id"]
            pillar = disc["pillar"]
            entry = disclosure_data.get(did, {})
            status = entry.get("status", "not_addressed")
            evidence = entry.get("evidence", [])

            score = self._status_to_score(status)
            findings = self._build_disclosure_findings(did, status, evidence)

            scored.append({
                "disclosure_id": did,
                "pillar": pillar,
                "title": disc["title"],
                "compliance_level": status,
                "score": score,
                "findings": findings,
            })

            pillar_totals.setdefault(pillar, []).append(score)

        # --- Overall compliance % (weighted by pillar) -----------------------
        overall_pct = 0.0
        for pillar, scores in pillar_totals.items():
            avg = sum(scores) / len(scores) if scores else 0.0
            weight = self._PILLAR_WEIGHTS.get(pillar, 0.25)
            overall_pct += avg * weight
        overall_pct = round(overall_pct, 1)

        # --- LEAP phase scoring ----------------------------------------------
        leap_data = disclosure_data.get("__leap__", {})
        leap_results = self._score_leap_phases(leap_data)

        # --- Nature risk profile ---------------------------------------------
        risk_data = disclosure_data.get("__risk__", {})
        nature_risk_profile = self._build_risk_profile(risk_data)

        # --- Priority locations (from STR-D) ---------------------------------
        str_d_entry = disclosure_data.get("STR-D", {})
        priority_locations_count = str_d_entry.get("priority_locations", 0)

        # --- Ecosystem services at risk (from MT-B) --------------------------
        mt_b_entry = disclosure_data.get("MT-B", {})
        es_ids = mt_b_entry.get("ecosystem_services", [])
        es_at_risk = self._resolve_ecosystem_services(es_ids)

        # --- Sector guidance -------------------------------------------------
        sector_label = ""
        if sector and sector in TNFD_SECTOR_GUIDANCE:
            sector_label = TNFD_SECTOR_GUIDANCE[sector]["label"]

        # --- Cross-framework mapping -----------------------------------------
        cross_map = self._build_cross_framework_mapping(scored)

        # --- Gaps and recommendations ----------------------------------------
        gaps = self._identify_gaps(scored, leap_results, sector)
        recommendations = self._generate_recommendations(
            scored, leap_results, gaps, sector, overall_pct,
        )

        # --- Deterministic ID ------------------------------------------------
        raw = f"tnfd-assess-{entity_name}-{reporting_year}"
        assessment_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

        return TNFDAssessment(
            id=assessment_id,
            entity_name=entity_name,
            reporting_year=reporting_year,
            overall_compliance_pct=overall_pct,
            disclosure_scores=scored,
            leap_results=leap_results,
            nature_risk_profile=nature_risk_profile,
            priority_locations_count=priority_locations_count,
            ecosystem_services_at_risk=es_at_risk,
            sector_guidance_applied=sector_label,
            cross_framework_mapping=cross_map,
            gaps=gaps,
            recommendations=recommendations,
            created_at=datetime.utcnow().isoformat(),
        )

    # ── Nature Materiality Assessment ─────────────────────────────────────

    def assess_nature_materiality(
        self,
        entity_name: str,
        reporting_year: int,
        sector: str,
        dependencies: list[dict] | None = None,
        impacts: list[dict] | None = None,
    ) -> TNFDMaterialityResult:
        """
        Evaluate which ecosystem services are material, score financial vs
        impact materiality, identify double-materiality topics, and generate
        recommendations.

        Parameters
        ----------
        entity_name : str
        reporting_year : int
        sector : str
            Key in TNFD_SECTOR_GUIDANCE.
        dependencies : list[dict] | None
            Each dict: {"service_id": "ES04", "magnitude": "high", "scope": "direct"}
        impacts : list[dict] | None
            Each dict: {"driver": "land_use_change", "severity": "high", "reversibility": "low"}
        """
        dependencies = dependencies or []
        impacts = impacts or []

        # --- Resolve sector guidance ----------------------------------------
        guidance = TNFD_SECTOR_GUIDANCE.get(sector, {})
        sector_es = guidance.get("encore_dependencies", [])

        # --- Financial materiality (dependency-driven) -----------------------
        fin_scores: list[float] = []
        material_deps: list[dict] = []

        for dep in dependencies:
            sid = dep.get("service_id", "")
            magnitude = dep.get("magnitude", "low")
            mag_score = {"high": 90.0, "medium": 60.0, "low": 30.0}.get(magnitude, 30.0)

            # Boost if service is in sector priority list
            if sid in sector_es:
                mag_score = min(mag_score + 15.0, 100.0)

            fin_scores.append(mag_score)
            svc = self._find_ecosystem_service(sid)
            material_deps.append({
                "service_id": sid,
                "service_name": svc.get("name", sid) if svc else sid,
                "magnitude": magnitude,
                "financial_materiality_score": round(mag_score, 1),
            })

        fin_materiality = round(sum(fin_scores) / len(fin_scores), 1) if fin_scores else 0.0

        # --- Impact materiality (impact-driven) ------------------------------
        imp_scores: list[float] = []
        material_imps: list[dict] = []
        severity_map = {"high": 90.0, "medium": 60.0, "low": 30.0}
        reversibility_map = {"irreversible": 1.3, "low": 1.15, "medium": 1.0, "high": 0.85}

        for imp in impacts:
            driver = imp.get("driver", "unknown")
            severity = imp.get("severity", "low")
            reversibility = imp.get("reversibility", "medium")

            base = severity_map.get(severity, 30.0)
            mult = reversibility_map.get(reversibility, 1.0)
            adjusted = min(base * mult, 100.0)

            imp_scores.append(adjusted)
            material_imps.append({
                "driver": driver,
                "severity": severity,
                "reversibility": reversibility,
                "impact_materiality_score": round(adjusted, 1),
            })

        imp_materiality = round(sum(imp_scores) / len(imp_scores), 1) if imp_scores else 0.0

        # --- Double materiality topics (>=60 on both axes) -------------------
        double_topics: list[dict] = []
        if fin_materiality >= 60.0 and imp_materiality >= 60.0:
            double_topics.append({
                "topic": "Nature-related dependencies and impacts",
                "financial_score": fin_materiality,
                "impact_score": imp_materiality,
                "classification": "double_material",
            })
        elif fin_materiality >= 60.0:
            double_topics.append({
                "topic": "Nature-related dependencies",
                "financial_score": fin_materiality,
                "impact_score": imp_materiality,
                "classification": "financial_material_only",
            })
        elif imp_materiality >= 60.0:
            double_topics.append({
                "topic": "Nature-related impacts",
                "financial_score": fin_materiality,
                "impact_score": imp_materiality,
                "classification": "impact_material_only",
            })

        # Build priority ecosystem services list (sector-based)
        priority_es: list[dict] = []
        for sid in sector_es:
            svc = self._find_ecosystem_service(sid)
            if svc:
                priority_es.append(svc)

        # --- Recommendations -------------------------------------------------
        recs: list[str] = []
        if fin_materiality < 30.0 and len(dependencies) == 0:
            recs.append("No dependency data provided. Conduct ENCORE-based dependency "
                        "screening for your sector to identify material ecosystem services.")
        if imp_materiality < 30.0 and len(impacts) == 0:
            recs.append("No impact data provided. Map nature impact drivers using "
                        "the SBTN materiality screening tool.")
        if fin_materiality >= 60.0 and imp_materiality >= 60.0:
            recs.append("Double materiality confirmed. Prioritise TNFD disclosure "
                        "and align targets with Science Based Targets for Nature (SBTN).")
        if sector and sector in TNFD_SECTOR_GUIDANCE:
            topics = guidance.get("priority_nature_topics", [])
            if topics:
                recs.append(f"Sector guidance highlights these priority topics: "
                            f"{'; '.join(topics[:3])}.")
        if len(material_deps) > 0:
            high_deps = [d for d in material_deps if d["financial_materiality_score"] >= 80.0]
            if high_deps:
                names = [d["service_name"] for d in high_deps[:3]]
                recs.append(f"High financial dependency on: {', '.join(names)}. "
                            "Develop contingency plans and monitor ecosystem condition.")

        raw = f"tnfd-materiality-{entity_name}-{reporting_year}"
        mat_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

        return TNFDMaterialityResult(
            id=mat_id,
            entity_name=entity_name,
            reporting_year=reporting_year,
            material_dependencies=material_deps,
            material_impacts=material_imps,
            financial_materiality_score=fin_materiality,
            impact_materiality_score=imp_materiality,
            double_materiality_topics=double_topics,
            priority_ecosystem_services=priority_es,
            recommendations=recs,
            created_at=datetime.utcnow().isoformat(),
        )

    # ── LEAP Readiness Assessment ─────────────────────────────────────────

    def assess_leap_readiness(
        self,
        entity_name: str,
        reporting_year: int,
        leap_data: dict | None = None,
    ) -> dict:
        """
        Score each LEAP phase and sub-component and return an overall
        readiness level.

        Parameters
        ----------
        entity_name : str
        reporting_year : int
        leap_data : dict | None
            Mapping of component ID (e.g. "L1") to status string:
            "completed", "in_progress", "planned", "not_started"

        Returns
        -------
        dict with keys: entity_name, reporting_year, phase_results,
        overall_score, readiness_level, gaps, recommendations
        """
        leap_data = leap_data or {}

        phase_results = self._score_leap_phases(leap_data)

        # Weighted overall
        total_weighted = 0.0
        for pr in phase_results:
            phase_key = pr["phase"]
            weight = self._LEAP_WEIGHTS.get(phase_key, 0.25)
            total_weighted += pr["overall_score"] * weight
        overall_score = round(total_weighted, 1)

        # Readiness level
        if overall_score >= 80.0:
            readiness = "advanced"
        elif overall_score >= 55.0:
            readiness = "developing"
        elif overall_score >= 25.0:
            readiness = "early"
        else:
            readiness = "not_started"

        # Collect all gaps across phases
        all_gaps: list[str] = []
        for pr in phase_results:
            all_gaps.extend(pr.get("gaps", []))

        # Recommendations based on readiness level
        recs: list[str] = []
        if readiness == "not_started":
            recs.append("Begin with the LOCATE phase: map all operational sites "
                        "and identify biomes using the TNFD online tool.")
            recs.append("Review TNFD sector-specific guidance for your industry.")
        elif readiness == "early":
            incomplete_phases = [pr["phase"] for pr in phase_results
                                 if pr["overall_score"] < 50.0]
            if incomplete_phases:
                recs.append(f"Focus on completing these LEAP phases: "
                            f"{', '.join(incomplete_phases)}.")
            recs.append("Engage with ENCORE to systematically map nature "
                        "dependencies and impacts.")
        elif readiness == "developing":
            recs.append("Strengthen the ASSESS phase with quantitative risk "
                        "modelling (scenario analysis under different nature pathways).")
            recs.append("Begin preparing TNFD-aligned disclosures using the "
                        "recommended disclosure structure.")
        else:
            recs.append("Maintain annual LEAP cycle and update disclosures. "
                        "Consider external assurance of TNFD reporting.")
            recs.append("Engage value chain partners on nature-related data "
                        "collection and target alignment.")

        return {
            "entity_name": entity_name,
            "reporting_year": reporting_year,
            "phase_results": phase_results,
            "overall_score": overall_score,
            "readiness_level": readiness,
            "gaps": all_gaps,
            "recommendations": recs,
        }

    # ── Static Reference Data Methods ─────────────────────────────────────

    @staticmethod
    def get_recommended_disclosures() -> list[dict]:
        """Return the 14 TNFD recommended disclosures."""
        return TNFD_RECOMMENDED_DISCLOSURES

    @staticmethod
    def get_leap_phases() -> dict:
        """Return LEAP phases with sub-components."""
        return TNFD_LEAP_PHASES

    @staticmethod
    def get_encore_ecosystem_services() -> list[dict]:
        """Return the 21 ENCORE ecosystem services."""
        return ENCORE_ECOSYSTEM_SERVICES

    @staticmethod
    def get_nature_risk_categories() -> dict:
        """Return the 3 nature risk categories with sub-types."""
        return NATURE_RISK_CATEGORIES

    @staticmethod
    def get_sector_guidance() -> dict:
        """Return sector-specific TNFD guidance for 8 sectors."""
        return TNFD_SECTOR_GUIDANCE

    @staticmethod
    def get_cross_framework_map() -> list[dict]:
        """Return TNFD-to-peer-framework mapping."""
        return TNFD_CROSS_FRAMEWORK_MAP

    @staticmethod
    def get_disclosure_pillar_structure() -> dict:
        """Return pillar-grouped disclosure structure for UI rendering."""
        pillars: dict[str, list[dict]] = {}
        for disc in TNFD_RECOMMENDED_DISCLOSURES:
            pillar = disc["pillar"]
            pillars.setdefault(pillar, []).append({
                "id": disc["id"],
                "title": disc["title"],
                "description": disc["description"],
            })
        return pillars

    @staticmethod
    def get_priority_area_criteria() -> list[dict]:
        """Return priority area criteria (KBAs, protected areas, etc.)."""
        return TNFD_PRIORITY_AREA_CRITERIA

    # ── Internal Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _status_to_score(status: str) -> float:
        """Convert a compliance status string to a numeric score."""
        return {"full": 100.0, "partial": 50.0, "not_addressed": 0.0}.get(status, 0.0)

    @staticmethod
    def _build_disclosure_findings(
        disclosure_id: str,
        status: str,
        evidence: list[str],
    ) -> list[str]:
        """Build findings list for a single disclosure."""
        findings: list[str] = []
        if status == "full":
            findings.append(f"{disclosure_id}: Fully addressed with supporting evidence.")
        elif status == "partial":
            findings.append(f"{disclosure_id}: Partially addressed. "
                            "Additional detail required for full compliance.")
        else:
            findings.append(f"{disclosure_id}: Not addressed. "
                            "This disclosure must be included for TNFD alignment.")
        if evidence:
            findings.append(f"Evidence provided: {'; '.join(evidence[:5])}")
        return findings

    def _score_leap_phases(self, leap_data: dict) -> list[dict]:
        """Score each LEAP phase and its sub-components."""
        status_scores = {
            "completed": 100.0,
            "in_progress": 60.0,
            "planned": 25.0,
            "not_started": 0.0,
        }

        results: list[dict] = []
        for phase_key, phase_def in TNFD_LEAP_PHASES.items():
            comp_scores: list[dict] = []
            gaps: list[str] = []
            for comp in phase_def["components"]:
                cid = comp["id"]
                cstatus = leap_data.get(cid, "not_started")
                cscore = status_scores.get(cstatus, 0.0)
                comp_scores.append({
                    "component_id": cid,
                    "title": comp["title"],
                    "status": cstatus,
                    "score": cscore,
                })
                if cscore < 60.0:
                    gaps.append(f"{cid} ({comp['title']}): status={cstatus}")

            phase_avg = (
                sum(c["score"] for c in comp_scores) / len(comp_scores)
                if comp_scores else 0.0
            )
            results.append({
                "phase": phase_key,
                "phase_label": phase_def["label"],
                "overall_score": round(phase_avg, 1),
                "component_scores": comp_scores,
                "gaps": gaps,
            })
        return results

    @staticmethod
    def _build_risk_profile(risk_data: dict) -> dict:
        """
        Build a nature risk profile from provided risk scores.

        risk_data mapping: category -> score (0-100).
        """
        profile: dict = {}
        for cat, meta in NATURE_RISK_CATEGORIES.items():
            provided_score = risk_data.get(cat, 0.0)
            profile[cat] = {
                "label": meta["label"],
                "score": round(float(provided_score), 1),
                "sub_types": meta["sub_types"],
                "rating": (
                    "high" if provided_score >= 70.0
                    else "medium" if provided_score >= 40.0
                    else "low"
                ),
            }
        return profile

    @staticmethod
    def _resolve_ecosystem_services(service_ids: list[str]) -> list[dict]:
        """Resolve ES IDs to full ENCORE ecosystem service records."""
        lookup = {es["id"]: es for es in ENCORE_ECOSYSTEM_SERVICES}
        resolved = []
        for sid in service_ids:
            if sid in lookup:
                resolved.append(lookup[sid])
        return resolved

    @staticmethod
    def _find_ecosystem_service(service_id: str) -> dict | None:
        """Find a single ENCORE ecosystem service by ID."""
        for es in ENCORE_ECOSYSTEM_SERVICES:
            if es["id"] == service_id:
                return es
        return None

    def _build_cross_framework_mapping(self, scored: list[dict]) -> dict:
        """Map scored disclosures to equivalent requirements in peer frameworks."""
        lookup: dict[str, dict] = {m["tnfd_disclosure"]: m for m in TNFD_CROSS_FRAMEWORK_MAP}
        mapping: dict[str, dict] = {}
        for s in scored:
            did = s["disclosure_id"]
            if did in lookup:
                mapping[did] = {
                    "issb_s1": lookup[did].get("issb_s1", ""),
                    "csrd_esrs_e4": lookup[did].get("csrd_esrs_e4", ""),
                    "gri": lookup[did].get("gri", ""),
                    "cbd_gbf": lookup[did].get("cbd_gbf", ""),
                    "tnfd_compliance": s["compliance_level"],
                }
        return mapping

    @staticmethod
    def _identify_gaps(
        scored: list[dict],
        leap_results: list[dict],
        sector: str | None,
    ) -> list[str]:
        """Identify disclosure and LEAP gaps."""
        gaps: list[str] = []

        # Disclosure gaps
        not_addressed = [s for s in scored if s["compliance_level"] == "not_addressed"]
        partial = [s for s in scored if s["compliance_level"] == "partial"]

        for s in not_addressed:
            gaps.append(f"Disclosure {s['disclosure_id']} ({s['title']}): "
                        "Not addressed — required for TNFD alignment.")
        for s in partial:
            gaps.append(f"Disclosure {s['disclosure_id']} ({s['title']}): "
                        "Partially addressed — additional detail needed.")

        # LEAP component gaps (score < 60)
        for pr in leap_results:
            for comp in pr.get("component_scores", []):
                if comp["score"] < 60.0:
                    gaps.append(f"LEAP {comp['component_id']} ({comp['title']}): "
                                f"Status is '{comp['status']}' — needs progression.")

        # Sector-specific gap check
        if sector and sector in TNFD_SECTOR_GUIDANCE:
            guidance = TNFD_SECTOR_GUIDANCE[sector]
            topics = guidance.get("priority_nature_topics", [])
            if topics:
                gaps.append(f"Sector '{guidance['label']}' has {len(topics)} priority "
                            "nature topics — verify coverage in STR-A and MT-B disclosures.")

        return gaps

    @staticmethod
    def _generate_recommendations(
        scored: list[dict],
        leap_results: list[dict],
        gaps: list[str],
        sector: str | None,
        overall_pct: float,
    ) -> list[str]:
        """Generate prioritised recommendations based on assessment results."""
        recs: list[str] = []

        # Overall compliance tier
        if overall_pct < 25.0:
            recs.append(
                "TNFD alignment is at an early stage. Begin with governance "
                "disclosures (GOV-A, GOV-B) and the LOCATE phase of LEAP."
            )
        elif overall_pct < 50.0:
            recs.append(
                "Moderate gaps remain. Prioritise Strategy disclosures (STR-A "
                "through STR-D) and complete the EVALUATE phase."
            )
        elif overall_pct < 80.0:
            recs.append(
                "Good progress toward TNFD alignment. Focus on Metrics & Targets "
                "(MT-A through MT-D) and quantitative risk assessment."
            )
        else:
            recs.append(
                "Strong TNFD alignment. Consider external assurance and "
                "peer benchmarking to maintain leadership position."
            )

        # Pillar-specific recommendations
        pillar_avgs: dict[str, float] = {}
        for s in scored:
            pillar_avgs.setdefault(s["pillar"], [])
            pillar_avgs[s["pillar"]].append(s["score"])
        for pillar, scores_list in pillar_avgs.items():
            avg = sum(scores_list) / len(scores_list) if scores_list else 0.0
            if avg < 40.0:
                recs.append(f"Pillar '{pillar}' scores below 40%. "
                            "Allocate dedicated resources to address this gap.")

        # LEAP phase recommendations
        for pr in leap_results:
            if pr["overall_score"] < 30.0:
                recs.append(
                    f"LEAP phase '{pr['phase']}' ({pr['phase_label']}) has "
                    f"minimal progress (score {pr['overall_score']}%). "
                    "Initiate this phase using TNFD guidance documentation."
                )

        # Sector recommendation
        if sector and sector in TNFD_SECTOR_GUIDANCE:
            guidance = TNFD_SECTOR_GUIDANCE[sector]
            recs.append(
                f"Apply TNFD sector guidance for '{guidance['label']}'. "
                f"Key biomes to assess: {', '.join(guidance.get('key_biomes', []))}."
            )

        # Location disclosure check
        str_d = [s for s in scored if s["disclosure_id"] == "STR-D"]
        if str_d and str_d[0]["compliance_level"] == "not_addressed":
            recs.append(
                "STR-D (location of assets in priority areas) is not addressed. "
                "Use IBAT, WDPA, or WRI Aqueduct to screen operational locations "
                "against KBAs, protected areas, and water-stressed basins."
            )

        # Cross-framework alignment
        recs.append(
            "Map TNFD disclosures to CSRD ESRS E4 and ISSB S1 to reduce "
            "reporting burden through interoperability."
        )

        return recs
