"""
Lineage Orchestrator
======================
Cross-module data lineage completion service. Wires ALL platform services into
the lineage graph, fills gaps, performs reference data gap analysis, propagates
quality scores through chains, and integrates with the audit subsystem.

This orchestrator extends the DataLineageEngine (data_lineage_service.py) with:
  1. Complete bridge wiring — PCAF→ECL, CSRD auto-populate, Entity 360, China trade
  2. Reference data gap analysis — identifies 8+ MISSING datasets per IMPLEMENTATION_PLAN_V2
  3. DQS→confidence weighted quality propagation
  4. Lineage-aware audit event emission
  5. Cross-module impact analysis (what-if a module degrades)
  6. Module health dashboard (summary across all lineage chains)

References:
  - BCBS 239 Principle 3 (Accuracy and Integrity)
  - BCBS 239 Principle 6 (Adaptability)
  - ISO 8000 (Data Quality)
  - PCAF Data Quality Score (DQS 1-5)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from services.data_lineage_service import (
    DataLineageEngine,
    MODULE_SIGNATURES,
    MODULE_DEPENDENCIES,
    DQS_TO_CONFIDENCE,
    LineageGap,
)

logger = logging.getLogger("platform.lineage_orchestrator")


# ---------------------------------------------------------------------------
# Reference Data Gap Registry
# ---------------------------------------------------------------------------
# Per IMPLEMENTATION_PLAN_V2.md Chunk 5 — datasets identified as MISSING
# that would complete broken lineage chains.

REFERENCE_DATA_GAP_REGISTRY: list[dict] = [
    {
        "dataset": "who_mortality_tables",
        "display_name": "WHO / National Mortality Tables",
        "source": "WHO Life Tables, national statistics offices",
        "needed_by": ["insurance_risk_engine"],
        "category": "insurance",
        "status": "missing",
        "impact": "Mortality delta calculations use placeholder rates; "
                  "climate-adjusted life expectancy lacks actuarial precision",
        "priority": "high",
        "estimated_fields": 12,
    },
    {
        "dataset": "natcat_loss_database",
        "display_name": "NatCat Historical Loss Database",
        "source": "Munich Re NatCatSERVICE / Swiss Re sigma",
        "needed_by": ["insurance_risk_engine", "climate_physical_risk_engine"],
        "category": "insurance",
        "status": "missing",
        "impact": "NatCat SCR and AAL use simplified frequency/severity; "
                  "historical calibration unavailable",
        "priority": "high",
        "estimated_fields": 18,
    },
    {
        "dataset": "ipcc_ar6_damage_functions",
        "display_name": "IPCC AR6 Damage Functions (WG2)",
        "source": "IPCC AR6 Working Group 2",
        "needed_by": ["insurance_risk_engine", "climate_physical_risk_engine",
                      "scenario_analysis_engine"],
        "category": "climate",
        "status": "missing",
        "impact": "Physical risk damage curves use parameterised approximations; "
                  "sector-specific IPCC damage functions would improve granularity",
        "priority": "high",
        "estimated_fields": 25,
    },
    {
        "dataset": "basel3_nsfr_lcr_factors",
        "display_name": "Basel III NSFR / LCR Regulatory Factors",
        "source": "CRR2 / CRD V (EU Capital Requirements Regulation)",
        "needed_by": ["banking_risk_engine"],
        "category": "banking",
        "status": "missing",
        "impact": "LCR outflow rates and NSFR ASF/RSF factors use simplified tiers; "
                  "full CRR2 granularity (50+ line items) not implemented",
        "priority": "medium",
        "estimated_fields": 55,
    },
    {
        "dataset": "fatf_country_risk_ratings",
        "display_name": "FATF Country Risk Ratings",
        "source": "FATF Mutual Evaluations / Jurisdictional Risk Assessments",
        "needed_by": ["banking_risk_engine"],
        "category": "banking",
        "status": "missing",
        "impact": "AML country risk uses simplified grey/black list; "
                  "FATF Effectiveness scores (IO 1-11) not captured",
        "priority": "medium",
        "estimated_fields": 15,
    },
    {
        "dataset": "fao_crop_yield_database",
        "display_name": "FAO Crop Yield Database (FAOSTAT)",
        "source": "FAO / FAOSTAT",
        "needed_by": ["agriculture_risk_calculator", "agriculture_methane_intensity"],
        "category": "agriculture",
        "status": "missing",
        "impact": "Crop yield risk uses generic climate adjustment factors; "
                  "FAO historical yields would enable country×crop calibration",
        "priority": "medium",
        "estimated_fields": 20,
    },
    {
        "dataset": "eudr_commodity_criteria",
        "display_name": "EUDR Commodity Due Diligence Criteria",
        "source": "EU Regulation 2023/1115 (Deforestation-free Products)",
        "needed_by": ["agriculture_risk_calculator", "supply_chain_scope3"],
        "category": "agriculture",
        "status": "missing",
        "impact": "EUDR compliance assessment not available; "
                  "7 commodities (cattle, cocoa, coffee, oil palm, rubber, soya, wood) "
                  "require deforestation-free supply chain verification",
        "priority": "high",
        "estimated_fields": 30,
    },
    {
        "dataset": "defra_bng_metric_4_full",
        "display_name": "DEFRA Biodiversity Net Gain Metric 4.0 (Full)",
        "source": "Natural England / DEFRA",
        "needed_by": ["agriculture_bng"],
        "category": "agriculture",
        "status": "partial",
        "impact": "BNG uses simplified habitat unit multipliers; "
                  "full Metric 4.0 has 100+ habitat types, temporal multipliers, "
                  "and spatial risk factors not yet embedded",
        "priority": "medium",
        "estimated_fields": 40,
    },
]


# ---------------------------------------------------------------------------
# Bridge Registry — all cross-module bridge wiring
# ---------------------------------------------------------------------------

BRIDGE_REGISTRY: list[dict] = [
    {
        "bridge_id": "pcaf_ecl_bridge",
        "name": "PCAF → ECL Climate Bridge",
        "source_modules": ["pcaf_waci_engine"],
        "target_modules": ["ecl_climate_engine"],
        "field_mappings": 5,
        "description": "Translates PCAF financed emissions (DQS, WACI, temperature) "
                       "into ECL climate overlay parameters (scenario weights, "
                       "confidence-weighted adjustments)",
        "status": "wired",
    },
    {
        "bridge_id": "csrd_auto_populate",
        "name": "CSRD Auto-Population Bridge",
        "source_modules": [
            "carbon_calculator", "carbon_calculator_v2", "supply_chain_scope3",
            "pcaf_waci_engine", "scenario_analysis_engine", "nature_risk_calculator",
            "insurance_risk_engine", "banking_risk_engine",
            "climate_physical_risk_engine", "climate_transition_risk_engine",
            "am_paris_alignment", "agriculture_methane_intensity",
            "agriculture_bng", "cbam_calculator", "china_trade_engine",
        ],
        "target_modules": ["csrd_auto_populate"],
        "field_mappings": 56,
        "description": "Maps outputs from 15+ modules to 330+ ESRS data points. "
                       "Covers E1-E5, S1, G1 disclosures.",
        "status": "wired",
    },
    {
        "bridge_id": "entity360_aggregation",
        "name": "Entity 360 Aggregation Bridge",
        "source_modules": [
            "carbon_calculator", "ecl_climate_engine", "scenario_analysis_engine",
            "nature_risk_calculator", "crrem_stranding_engine", "gar_calculator",
            "sfdr_report_generator", "stranded_asset_calculator", "pe_deal_engine",
            "insurance_risk_engine", "banking_risk_engine",
            "climate_physical_risk_engine", "climate_transition_risk_engine",
            "am_esg_attribution", "am_paris_alignment", "am_green_bond_screening",
            "am_lp_analytics", "am_optimisation",
            "agriculture_methane_intensity", "agriculture_disease_outbreak",
            "agriculture_bng", "assessment_runner",
        ],
        "target_modules": ["entity360"],
        "field_mappings": 42,
        "description": "Aggregates outputs from 22+ modules into unified Entity 360 "
                       "composite risk score, ESG rating, and data completeness.",
        "status": "wired",
    },
    {
        "bridge_id": "china_trade_bridge",
        "name": "China Trade Cross-Module Bridge",
        "source_modules": ["china_trade_engine"],
        "target_modules": ["supply_chain_scope3", "ecl_climate_engine",
                          "csrd_auto_populate"],
        "field_mappings": 6,
        "description": "Routes CBAM exposure, tariff risk, and regulatory alignment "
                       "from China Trade Engine to SC Scope 3, ECL, and CSRD modules.",
        "status": "wired",
    },
    {
        "bridge_id": "climate_risk_integration",
        "name": "Climate Risk Integration Bridge",
        "source_modules": ["climate_physical_risk_engine", "climate_transition_risk_engine"],
        "target_modules": ["climate_integrated_risk", "ecl_climate_engine",
                          "entity360", "csrd_auto_populate"],
        "field_mappings": 18,
        "description": "Routes physical and transition risk scores to integrated view, "
                       "ECL overlays, Entity 360, and CSRD E1 disclosures.",
        "status": "wired",
    },
]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ReferenceDataGapReport:
    """Analysis of missing reference data across the platform."""
    total_datasets_catalogued: int
    datasets_embedded: int
    datasets_missing: int
    datasets_partial: int
    completeness_pct: float
    missing_datasets: list[dict]
    priority_high: list[dict]
    priority_medium: list[dict]
    total_estimated_fields_missing: int
    affected_modules: list[str]
    recommendations: list[str]


@dataclass
class BridgeHealthReport:
    """Health check on all cross-module bridges."""
    total_bridges: int
    wired_bridges: int
    broken_bridges: int
    total_field_mappings: int
    bridges: list[dict]
    recommendations: list[str]


@dataclass
class ModuleImpactAnalysis:
    """What-if analysis: impact of degrading a single module."""
    degraded_module: str
    affected_downstream: list[str]
    affected_chains: int
    quality_impact: dict[str, float]  # {module_id: quality_delta}
    regulatory_impact: list[str]
    recommendations: list[str]


@dataclass
class PlatformHealthDashboard:
    """Cross-cutting lineage health dashboard."""
    timestamp: str
    total_modules: int
    total_edges: int
    total_bridges: int
    lineage_completeness_pct: float
    reference_data_completeness_pct: float
    average_quality_score: float
    orphan_modules: list[str]
    critical_gaps: int
    high_gaps: int
    medium_gaps: int
    missing_reference_datasets: int
    bcbs239_compliance_score: float  # 0-100
    recommendations: list[str]


@dataclass
class AuditLineageEvent:
    """Lineage event for audit trail integration."""
    event_id: str
    timestamp: str
    event_type: str  # "lineage_trace" | "gap_detected" | "quality_degradation" | "bridge_break"
    module_id: str
    entity_id: str
    details: dict
    severity: str  # "info" | "warning" | "critical"


# ---------------------------------------------------------------------------
# Lineage Orchestrator Engine
# ---------------------------------------------------------------------------

class LineageOrchestrator:
    """
    Cross-module lineage orchestration engine.

    Extends DataLineageEngine with bridge wiring, reference data gap analysis,
    impact analysis, and audit integration. This is the Chunk 5 deliverable
    per IMPLEMENTATION_PLAN_V2.md.

    Stakeholder Insights:
      - CRO: Platform-wide data lineage health; BCBS 239 compliance score
      - Data Officer: Reference data gaps blocking complete lineage chains
      - Audit: Every lineage trace and gap detection is audit-loggable
      - Portfolio Managers: Quality propagation shows data reliability per module
      - Regulatory: Which modules feed which CSRD/SFDR/ISSB disclosures
    """

    def __init__(self):
        self._engine = DataLineageEngine()
        self._ref_gaps = REFERENCE_DATA_GAP_REGISTRY
        self._bridges = BRIDGE_REGISTRY
        self._audit_events: list[AuditLineageEvent] = []

    @property
    def engine(self) -> DataLineageEngine:
        """Access the underlying DataLineageEngine."""
        return self._engine

    # ----- Reference Data Gap Analysis -----

    def analyse_reference_data_gaps(self) -> ReferenceDataGapReport:
        """
        Analyse all reference data dependencies across the platform.

        Cross-references MODULE_SIGNATURES reference_data fields with the
        REFERENCE_DATA_GAP_REGISTRY to identify:
          - Embedded datasets (available)
          - Missing datasets (blocking lineage chains)
          - Partial datasets (incomplete coverage)

        Returns:
            ReferenceDataGapReport with prioritised gap list
        """
        # Collect all reference data from signatures
        all_ref_data = self._engine.get_all_reference_data()
        total_catalogued = len(all_ref_data)

        missing = [g for g in self._ref_gaps if g["status"] == "missing"]
        partial = [g for g in self._ref_gaps if g["status"] == "partial"]
        embedded = total_catalogued - len(missing) - len(partial)

        total_fields_missing = sum(g["estimated_fields"] for g in self._ref_gaps)

        affected = set()
        for g in self._ref_gaps:
            affected.update(g["needed_by"])

        high_priority = [g for g in self._ref_gaps if g["priority"] == "high"]
        med_priority = [g for g in self._ref_gaps if g["priority"] == "medium"]

        pct = (embedded / total_catalogued * 100) if total_catalogued > 0 else 0

        recs = []
        if high_priority:
            recs.append(
                f"{len(high_priority)} high-priority datasets missing — "
                f"blocking {sum(len(g['needed_by']) for g in high_priority)} module chains"
            )
        for g in high_priority[:3]:
            recs.append(f"Acquire {g['display_name']} from {g['source']}")
        if med_priority:
            recs.append(
                f"{len(med_priority)} medium-priority datasets would improve "
                f"lineage completeness by ~{len(med_priority) * 5}%"
            )

        self._emit_audit("ref_data_gap_analysis", "platform", "platform", {
            "missing_count": len(missing),
            "partial_count": len(partial),
            "completeness_pct": round(pct, 1),
        }, "info" if not high_priority else "warning")

        return ReferenceDataGapReport(
            total_datasets_catalogued=total_catalogued,
            datasets_embedded=embedded,
            datasets_missing=len(missing),
            datasets_partial=len(partial),
            completeness_pct=round(pct, 1),
            missing_datasets=self._ref_gaps,
            priority_high=high_priority,
            priority_medium=med_priority,
            total_estimated_fields_missing=total_fields_missing,
            affected_modules=sorted(affected),
            recommendations=recs,
        )

    # ----- Bridge Health Check -----

    def check_bridge_health(self) -> BridgeHealthReport:
        """
        Verify all cross-module bridges are correctly wired.

        Cross-references BRIDGE_REGISTRY with actual MODULE_DEPENDENCIES
        to confirm each bridge has corresponding dependency edges.

        Returns:
            BridgeHealthReport with per-bridge status
        """
        # Build edge lookup from actual dependencies
        edge_set = set()
        for dep in self._engine.get_dependencies():
            edge_set.add((dep.get("source"), dep.get("target")))

        wired = 0
        broken = 0
        bridge_details = []
        total_mappings = 0

        for bridge in self._bridges:
            total_mappings += bridge["field_mappings"]
            # Check if at least one edge exists for each source→target pair
            all_wired = True
            for src in bridge["source_modules"]:
                for tgt in bridge["target_modules"]:
                    if (src, tgt) not in edge_set:
                        all_wired = False
                        break

            status = "wired" if all_wired else "broken"
            if all_wired:
                wired += 1
            else:
                broken += 1

            bridge_details.append({
                **bridge,
                "verified_status": status,
            })

        recs = []
        if broken > 0:
            recs.append(f"{broken} bridges have missing dependency edges — verify wiring")
        for bd in bridge_details:
            if bd["verified_status"] == "broken":
                recs.append(f"Fix bridge '{bd['name']}': add missing edges")

        return BridgeHealthReport(
            total_bridges=len(self._bridges),
            wired_bridges=wired,
            broken_bridges=broken,
            total_field_mappings=total_mappings,
            bridges=bridge_details,
            recommendations=recs,
        )

    # ----- Module Impact Analysis -----

    def analyse_module_impact(
        self,
        module_id: str,
        degradation_factor: float = 0.0,
    ) -> ModuleImpactAnalysis:
        """
        What-if analysis: what happens if a module's quality degrades?

        Traces all downstream consumers of the given module and computes
        the quality impact at each node using weakest-link propagation.

        Parameters:
            module_id: Module to simulate degradation for
            degradation_factor: New quality score (0.0 = complete failure)

        Returns:
            ModuleImpactAnalysis with downstream impact map
        """
        # Find all downstream modules via BFS
        downstream = []
        visited = set()
        queue = [module_id]

        while queue:
            mod = queue.pop(0)
            if mod in visited:
                continue
            visited.add(mod)
            for edge in self._engine._adj_forward.get(mod, []):
                tgt = edge["target"]
                if tgt not in visited:
                    downstream.append(tgt)
                    queue.append(tgt)

        # Compute quality impact
        quality_impact = {}
        for dm in downstream:
            # Original quality (default 0.7) vs degraded
            original = 0.7
            new_quality = min(original, degradation_factor)
            quality_impact[dm] = round(original - new_quality, 2)

        # Identify regulatory impact
        regulatory_modules = {"csrd_auto_populate", "gar_calculator",
                              "sfdr_report_generator", "cbam_calculator"}
        reg_impact = [dm for dm in downstream if dm in regulatory_modules]
        reg_descriptions = []
        if "csrd_auto_populate" in reg_impact:
            reg_descriptions.append("CSRD E1-G1 disclosures may have reduced data quality")
        if "sfdr_report_generator" in reg_impact:
            reg_descriptions.append("SFDR PAI indicators may show degraded confidence")
        if "gar_calculator" in reg_impact:
            reg_descriptions.append("EU Taxonomy GAR calculation may be affected")

        # Count affected chains
        graph = self._engine.get_module_graph()
        affected_chains = sum(1 for e in graph.edges if e.source == module_id)

        recs = []
        if len(downstream) > 5:
            recs.append(f"{module_id} is a high-fan-out module — "
                        f"degradation impacts {len(downstream)} downstream modules")
        if reg_impact:
            recs.append("Regulatory disclosure modules affected — "
                        "prioritise data quality restoration")
        recs.append(f"Minimum quality threshold: ensure DQS ≥ 3 "
                    f"(confidence {DQS_TO_CONFIDENCE.get(3, 0.7):.0%})")

        self._emit_audit("impact_analysis", module_id, "platform", {
            "downstream_count": len(downstream),
            "degradation_factor": degradation_factor,
            "regulatory_impact": reg_descriptions,
        }, "warning" if reg_impact else "info")

        return ModuleImpactAnalysis(
            degraded_module=module_id,
            affected_downstream=downstream,
            affected_chains=affected_chains,
            quality_impact=quality_impact,
            regulatory_impact=reg_descriptions,
            recommendations=recs,
        )

    # ----- Platform Health Dashboard -----

    def get_platform_health(self) -> PlatformHealthDashboard:
        """
        Comprehensive platform-wide lineage health dashboard.

        Aggregates:
          - Module graph topology
          - Gap analysis
          - Bridge health
          - Reference data gaps
          - Quality propagation (all modules at default quality)
          - BCBS 239 compliance estimate

        Returns:
            PlatformHealthDashboard with all metrics
        """
        graph = self._engine.get_module_graph()
        gap_analysis = self._engine.find_gaps()
        bridge_health = self.check_bridge_health()
        ref_gaps = self.analyse_reference_data_gaps()

        # Quality propagation at default scores
        default_quality = {mod_id: 0.7 for mod_id in MODULE_SIGNATURES}
        quality = self._engine.propagate_quality("platform", default_quality)

        # BCBS 239 compliance score (simplified)
        # Based on: completeness, accuracy, timeliness, adaptability
        completeness_score = gap_analysis.completeness_pct  # 0-100
        ref_score = ref_gaps.completeness_pct  # 0-100
        quality_score = quality.overall_quality * 100  # 0-100
        bridge_score = (bridge_health.wired_bridges / max(bridge_health.total_bridges, 1)) * 100

        bcbs239 = round(
            (completeness_score * 0.30 +
             ref_score * 0.25 +
             quality_score * 0.25 +
             bridge_score * 0.20),
            1
        )

        critical = len(gap_analysis.critical_gaps)
        high = len([g for g in gap_analysis.gaps if g.severity == "high"])
        medium = len([g for g in gap_analysis.gaps if g.severity == "medium"])

        recs = []
        if bcbs239 < 70:
            recs.append(f"BCBS 239 compliance {bcbs239:.0f}% — below 70% target; "
                        f"prioritise gap remediation")
        if critical > 0:
            recs.append(f"{critical} critical gaps — register missing module signatures")
        if ref_gaps.datasets_missing > 0:
            recs.append(f"{ref_gaps.datasets_missing} reference datasets missing — "
                        f"acquire high-priority data sources")
        if graph.orphan_modules:
            recs.append(f"{len(graph.orphan_modules)} orphan modules — "
                        f"assess integration need: {', '.join(graph.orphan_modules[:5])}")

        return PlatformHealthDashboard(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_modules=graph.total_modules,
            total_edges=graph.total_edges,
            total_bridges=bridge_health.total_bridges,
            lineage_completeness_pct=gap_analysis.completeness_pct,
            reference_data_completeness_pct=ref_gaps.completeness_pct,
            average_quality_score=quality.overall_quality,
            orphan_modules=graph.orphan_modules,
            critical_gaps=critical,
            high_gaps=high,
            medium_gaps=medium,
            missing_reference_datasets=ref_gaps.datasets_missing,
            bcbs239_compliance_score=bcbs239,
            recommendations=recs,
        )

    # ----- DQS-Weighted Quality Propagation -----

    def propagate_dqs_quality(
        self,
        entity_id: str,
        module_dqs: dict[str, int],
    ) -> dict:
        """
        Propagate quality using PCAF Data Quality Score (DQS 1-5).

        Converts DQS scores to confidence weights using DQS_TO_CONFIDENCE
        mapping, then delegates to DataLineageEngine quality propagation.

        Parameters:
            entity_id: Entity identifier
            module_dqs: {module_id: DQS score (1-5)}

        Returns:
            QualityPropagationResult dict with DQS-weighted scores
        """
        # Convert DQS → confidence
        module_quality = {}
        for mod_id, dqs in module_dqs.items():
            dqs_clamped = max(1, min(5, dqs))
            module_quality[mod_id] = DQS_TO_CONFIDENCE.get(dqs_clamped, 0.5)

        result = self._engine.propagate_quality(entity_id, module_quality)

        # Enrich with DQS context
        return {
            "entity_id": result.entity_id,
            "module_quality": result.module_quality,
            "dqs_input": module_dqs,
            "dqs_confidence_map": DQS_TO_CONFIDENCE,
            "weakest_links": result.weakest_links,
            "overall_quality": result.overall_quality,
            "quality_label": result.quality_label,
            "recommendations": result.recommendations,
        }

    # ----- Lineage Chain for Regulatory Disclosure -----

    def trace_regulatory_lineage(self, disclosure_framework: str) -> dict:
        """
        Trace the complete data lineage chain feeding a regulatory disclosure.

        Supported frameworks: CSRD, SFDR, EU_TAXONOMY, ISSB, CBAM

        Parameters:
            disclosure_framework: One of the supported frameworks

        Returns:
            Dict with lineage chain, feeding modules, quality, and gaps
        """
        framework_modules = {
            "CSRD": "csrd_auto_populate",
            "SFDR": "sfdr_report_generator",
            "EU_TAXONOMY": "gar_calculator",
            "ISSB": "csrd_auto_populate",  # ISSB maps through CSRD for now
            "CBAM": "cbam_calculator",
        }

        target = framework_modules.get(disclosure_framework.upper())
        if not target:
            return {
                "error": f"Unknown framework: {disclosure_framework}",
                "supported": list(framework_modules.keys()),
            }

        chain = self._engine.trace_lineage(target)

        self._emit_audit("regulatory_lineage_trace", target, "platform", {
            "framework": disclosure_framework,
            "chain_length": chain.total_chain_length,
            "has_gaps": not chain.has_complete_lineage,
        }, "info")

        return {
            "framework": disclosure_framework,
            "target_module": target,
            "chain_length": chain.total_chain_length,
            "root_sources": chain.root_sources,
            "data_quality_score": chain.data_quality_score,
            "quality_label": chain.quality_label,
            "has_complete_lineage": chain.has_complete_lineage,
            "gaps": [
                {
                    "source": g.source_module,
                    "target": g.target_module,
                    "missing_fields": g.missing_fields,
                    "severity": g.severity,
                    "remediation": g.remediation,
                }
                for g in chain.gaps
            ],
            "reference_data_used": chain.reference_data_used,
            "nodes": [
                {
                    "module_id": n.module_id,
                    "label": n.module_label,
                    "category": n.category,
                    "quality_score": n.quality_score,
                    "depth": n.depth,
                }
                for n in chain.nodes
            ],
        }

    # ----- Module Coverage Summary -----

    def get_module_coverage(self) -> dict:
        """
        Summary of all registered modules grouped by category.

        Returns:
            Dict with category breakdown, counts, and coverage metrics
        """
        categories: dict[str, list] = {}
        for mod_id, sig in MODULE_SIGNATURES.items():
            cat = sig.get("category", "uncategorised")
            categories.setdefault(cat, []).append({
                "module_id": mod_id,
                "label": sig.get("label", mod_id),
                "inputs": len(sig.get("inputs", [])),
                "outputs": len(sig.get("outputs", [])),
                "reference_data": len(sig.get("reference_data", [])),
            })

        return {
            "total_modules": len(MODULE_SIGNATURES),
            "total_categories": len(categories),
            "categories": {
                cat: {
                    "count": len(mods),
                    "modules": mods,
                }
                for cat, mods in sorted(categories.items())
            },
        }

    # ----- Audit Integration -----

    def _emit_audit(
        self,
        event_type: str,
        module_id: str,
        entity_id: str,
        details: dict,
        severity: str = "info",
    ) -> None:
        """Emit a lineage audit event (in-memory; can be wired to audit_log table)."""
        event = AuditLineageEvent(
            event_id=f"lin_{len(self._audit_events) + 1:06d}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            module_id=module_id,
            entity_id=entity_id,
            details=details,
            severity=severity,
        )
        self._audit_events.append(event)
        if severity == "critical":
            logger.error("LINEAGE AUDIT [%s] %s: %s", event_type, module_id, details)
        elif severity == "warning":
            logger.warning("LINEAGE AUDIT [%s] %s: %s", event_type, module_id, details)
        else:
            logger.info("LINEAGE AUDIT [%s] %s: %s", event_type, module_id, details)

    def get_audit_events(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
    ) -> list[dict]:
        """
        Retrieve lineage audit events.

        Parameters:
            limit: Max events to return
            severity: Filter by severity (info/warning/critical)

        Returns:
            List of audit event dicts, newest first
        """
        events = self._audit_events
        if severity:
            events = [e for e in events if e.severity == severity]
        events = events[-limit:]
        events.reverse()
        return [
            {
                "event_id": e.event_id,
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "module_id": e.module_id,
                "entity_id": e.entity_id,
                "details": e.details,
                "severity": e.severity,
            }
            for e in events
        ]

    # ----- Convenience: Get All Reference Data -----

    def get_reference_data_inventory(self) -> dict:
        """
        Complete inventory of all reference data: embedded + missing + partial.

        Returns:
            Dict with embedded data from signatures plus gap registry
        """
        embedded = self._engine.get_all_reference_data()
        return {
            "embedded": embedded,
            "embedded_count": len(embedded),
            "missing": [g for g in self._ref_gaps if g["status"] == "missing"],
            "missing_count": len([g for g in self._ref_gaps if g["status"] == "missing"]),
            "partial": [g for g in self._ref_gaps if g["status"] == "partial"],
            "partial_count": len([g for g in self._ref_gaps if g["status"] == "partial"]),
            "total_gap_fields": sum(g["estimated_fields"] for g in self._ref_gaps),
        }
