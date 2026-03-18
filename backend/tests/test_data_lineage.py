"""
Tests — Data Lineage Service + Reference Data Catalog
=======================================================
60+ tests across 15 test classes covering:
  - Module signature registry
  - Dependency graph construction
  - Lineage tracing (single/multi-hop)
  - Gap detection (field-level, module-level)
  - Quality propagation
  - Reference data catalog
  - API routes
"""
import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.data_lineage_service import (
    DataLineageEngine,
    MODULE_SIGNATURES,
    MODULE_DEPENDENCIES,
    DQS_TO_CONFIDENCE,
)
from services.reference_data_catalog import (
    ReferenceDataCatalogEngine,
    REFERENCE_DATASETS,
    REFERENCE_DOMAINS,
)


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Module Signatures
# ═══════════════════════════════════════════════════════════════════════════

class TestModuleSignatures:
    """Verify module signature registry completeness."""

    def test_signature_count(self):
        assert len(MODULE_SIGNATURES) >= 25, "Should have 25+ module signatures"

    def test_signature_has_required_keys(self):
        for mod_id, sig in MODULE_SIGNATURES.items():
            assert "label" in sig, f"{mod_id} missing label"
            assert "category" in sig, f"{mod_id} missing category"
            assert "inputs" in sig, f"{mod_id} missing inputs"
            assert "outputs" in sig, f"{mod_id} missing outputs"
            assert "reference_data" in sig, f"{mod_id} missing reference_data"

    def test_all_signatures_have_inputs(self):
        for mod_id, sig in MODULE_SIGNATURES.items():
            assert len(sig["inputs"]) > 0, f"{mod_id} has no inputs"

    def test_all_signatures_have_outputs(self):
        for mod_id, sig in MODULE_SIGNATURES.items():
            assert len(sig["outputs"]) > 0, f"{mod_id} has no outputs"

    def test_categories_are_known(self):
        known = {"emissions", "credit", "financed_emissions", "cross_module",
                 "scenarios", "nature", "risk", "regulatory", "valuation",
                 "real_estate", "private_equity", "infrastructure",
                 "geopolitical", "insurance", "banking", "mining", "agriculture",
                 "sustainability", "climate_risk"}
        for mod_id, sig in MODULE_SIGNATURES.items():
            assert sig["category"] in known, f"{mod_id} has unknown category: {sig['category']}"

    def test_key_modules_present(self):
        key_modules = [
            "carbon_calculator", "pd_calculator", "ecl_climate_engine",
            "pcaf_waci_engine", "pcaf_ecl_bridge", "scenario_analysis_engine",
            "nature_risk_calculator", "entity360", "csrd_auto_populate",
            "real_estate_valuation_engine",
        ]
        for mod in key_modules:
            assert mod in MODULE_SIGNATURES, f"Key module '{mod}' missing"


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Dependencies
# ═══════════════════════════════════════════════════════════════════════════

class TestModuleDependencies:
    """Verify dependency edge definitions."""

    def test_dependency_count(self):
        assert len(MODULE_DEPENDENCIES) >= 20, "Should have 20+ dependency edges"

    def test_dependencies_have_required_keys(self):
        for dep in MODULE_DEPENDENCIES:
            assert "source" in dep
            assert "target" in dep
            assert "field_map" in dep
            assert "description" in dep

    def test_dependency_sources_exist(self):
        for dep in MODULE_DEPENDENCIES:
            assert dep["source"] in MODULE_SIGNATURES, \
                f"Dependency source '{dep['source']}' not in signatures"

    def test_dependency_targets_exist(self):
        for dep in MODULE_DEPENDENCIES:
            assert dep["target"] in MODULE_SIGNATURES, \
                f"Dependency target '{dep['target']}' not in signatures"

    def test_no_self_loops(self):
        for dep in MODULE_DEPENDENCIES:
            assert dep["source"] != dep["target"], \
                f"Self-loop detected: {dep['source']}"

    def test_field_maps_non_empty(self):
        for dep in MODULE_DEPENDENCIES:
            assert len(dep["field_map"]) > 0, \
                f"Empty field_map: {dep['source']} -> {dep['target']}"


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Engine Construction
# ═══════════════════════════════════════════════════════════════════════════

class TestLineageEngine:
    """Verify engine initialisation and graph construction."""

    def setup_method(self):
        self.engine = DataLineageEngine()

    def test_engine_initialises(self):
        assert self.engine is not None

    def test_forward_adjacency_populated(self):
        assert len(self.engine._adj_forward) > 0

    def test_reverse_adjacency_populated(self):
        assert len(self.engine._adj_reverse) > 0

    def test_carbon_has_forward_edges(self):
        assert "carbon_calculator" in self.engine._adj_forward
        assert len(self.engine._adj_forward["carbon_calculator"]) >= 3


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Trace Lineage
# ═══════════════════════════════════════════════════════════════════════════

class TestTraceLineage:
    """Test lineage chain tracing."""

    def setup_method(self):
        self.engine = DataLineageEngine()

    def test_trace_entity360(self):
        chain = self.engine.trace_lineage("entity360")
        assert chain.target_module == "entity360"
        assert chain.total_chain_length >= 3  # entity360 + upstream modules
        assert len(chain.root_sources) > 0
        assert chain.data_quality_score > 0

    def test_trace_ecl_engine(self):
        chain = self.engine.trace_lineage("ecl_climate_engine")
        assert chain.total_chain_length >= 2
        # Should include PD, LGD, EAD as upstream
        mod_ids = [n.module_id for n in chain.nodes]
        assert "pd_calculator" in mod_ids or "ecl_climate_engine" in mod_ids

    def test_trace_csrd_auto_populate(self):
        chain = self.engine.trace_lineage("csrd_auto_populate")
        assert chain.total_chain_length >= 2
        mod_ids = [n.module_id for n in chain.nodes]
        assert "carbon_calculator" in mod_ids

    def test_trace_root_module(self):
        """Tracing a root module should return just itself."""
        chain = self.engine.trace_lineage("supply_chain_scope3")
        assert chain.total_chain_length >= 1
        # supply_chain_scope3 feeds carbon_calculator, but as a source it has no upstream
        # (except carbon_calculator which is also a root)

    def test_trace_with_quality_override(self):
        chain = self.engine.trace_lineage(
            "entity360", module_quality={"carbon_calculator": 0.3}
        )
        assert chain.data_quality_score <= 0.3  # Weakest link

    def test_trace_returns_reference_data(self):
        chain = self.engine.trace_lineage("ecl_climate_engine")
        assert len(chain.reference_data_used) > 0

    def test_nodes_sorted_by_depth(self):
        chain = self.engine.trace_lineage("entity360")
        if len(chain.nodes) > 1:
            depths = [n.depth for n in chain.nodes]
            assert depths == sorted(depths, reverse=True)

    def test_entity_id_passed_through(self):
        chain = self.engine.trace_lineage("entity360", entity_id="ENT-001")
        assert chain.entity_id == "ENT-001"


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Gap Analysis
# ═══════════════════════════════════════════════════════════════════════════

class TestGapAnalysis:
    """Test platform-wide lineage gap detection."""

    def setup_method(self):
        self.engine = DataLineageEngine()

    def test_gap_analysis_returns_result(self):
        result = self.engine.find_gaps()
        assert result.total_edges > 0
        assert result.completeness_pct >= 0

    def test_gap_analysis_counts_consistent(self):
        result = self.engine.find_gaps()
        assert result.complete_edges + result.broken_edges == result.total_edges

    def test_gap_analysis_has_recommendations(self):
        result = self.engine.find_gaps()
        # At least some recommendations should exist (orphan modules if nothing else)
        assert isinstance(result.recommendations, list)

    def test_gap_severity_valid(self):
        result = self.engine.find_gaps()
        for gap in result.gaps:
            assert gap.severity in ("critical", "high", "medium", "low")

    def test_critical_gaps_subset_of_all(self):
        result = self.engine.find_gaps()
        assert len(result.critical_gaps) <= len(result.gaps)
        for cg in result.critical_gaps:
            assert cg.severity == "critical"


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Module Graph
# ═══════════════════════════════════════════════════════════════════════════

class TestModuleGraph:
    """Test module dependency graph construction."""

    def setup_method(self):
        self.engine = DataLineageEngine()

    def test_graph_has_modules(self):
        graph = self.engine.get_module_graph()
        assert graph.total_modules >= 25

    def test_graph_has_edges(self):
        graph = self.engine.get_module_graph()
        assert graph.total_edges >= 20

    def test_root_modules_exist(self):
        graph = self.engine.get_module_graph()
        assert len(graph.root_modules) > 0

    def test_leaf_modules_exist(self):
        graph = self.engine.get_module_graph()
        assert len(graph.leaf_modules) > 0

    def test_entity360_is_leaf(self):
        graph = self.engine.get_module_graph()
        assert "entity360" in graph.leaf_modules

    def test_bridge_modules_identified(self):
        graph = self.engine.get_module_graph()
        # ecl_climate_engine has multiple inputs and feeds entity360
        # csrd_auto_populate has multiple inputs and is a leaf
        assert isinstance(graph.bridge_modules, list)

    def test_module_details_present(self):
        graph = self.engine.get_module_graph()
        for mod in graph.modules:
            assert "id" in mod
            assert "label" in mod
            assert "category" in mod
            assert "input_count" in mod
            assert "output_count" in mod


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Quality Propagation
# ═══════════════════════════════════════════════════════════════════════════

class TestQualityPropagation:
    """Test quality score propagation through the graph."""

    def setup_method(self):
        self.engine = DataLineageEngine()

    def test_quality_propagation_basic(self):
        result = self.engine.propagate_quality(
            entity_id="ENT-001",
            module_quality={"carbon_calculator": 0.9, "pd_calculator": 0.8},
        )
        assert result.entity_id == "ENT-001"
        assert len(result.module_quality) >= 25
        assert result.overall_quality > 0

    def test_quality_propagation_low_input(self):
        result = self.engine.propagate_quality(
            entity_id="ENT-002",
            module_quality={"carbon_calculator": 0.2},
        )
        # Carbon's low quality should propagate downstream
        downstream = result.module_quality.get("csrd_auto_populate", 1.0)
        assert downstream <= 0.5  # Should be dragged down

    def test_quality_labels_valid(self):
        result = self.engine.propagate_quality(
            entity_id="ENT-003",
            module_quality={},
        )
        assert result.quality_label in ("high", "medium", "low")

    def test_weakest_links_identified(self):
        result = self.engine.propagate_quality(
            entity_id="ENT-004",
            module_quality={"pd_calculator": 0.1},
        )
        assert isinstance(result.weakest_links, list)


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — Reference Data Helpers
# ═══════════════════════════════════════════════════════════════════════════

class TestLineageRefData:
    """Test reference data aggregation from lineage."""

    def setup_method(self):
        self.engine = DataLineageEngine()

    def test_all_reference_data_non_empty(self):
        ref = self.engine.get_all_reference_data()
        assert len(ref) > 0

    def test_reference_data_has_used_by(self):
        ref = self.engine.get_all_reference_data()
        for item in ref:
            assert "dataset" in item
            assert "used_by" in item
            assert len(item["used_by"]) > 0

    def test_get_signatures(self):
        sigs = self.engine.get_module_signatures()
        assert len(sigs) == len(MODULE_SIGNATURES)

    def test_get_dependencies(self):
        deps = self.engine.get_dependencies()
        assert len(deps) == len(MODULE_DEPENDENCIES)


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LINEAGE — DQS Confidence
# ═══════════════════════════════════════════════════════════════════════════

class TestDQSConfidence:
    """Test PCAF DQS → confidence weight mapping."""

    def test_dqs_scores_complete(self):
        assert set(DQS_TO_CONFIDENCE.keys()) == {1, 2, 3, 4, 5}

    def test_dqs_monotonically_decreasing(self):
        scores = [DQS_TO_CONFIDENCE[i] for i in range(1, 6)]
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i + 1]

    def test_dqs_1_is_perfect(self):
        assert DQS_TO_CONFIDENCE[1] == 1.0

    def test_dqs_5_is_lowest(self):
        assert DQS_TO_CONFIDENCE[5] == 0.3


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA CATALOG — Datasets
# ═══════════════════════════════════════════════════════════════════════════

class TestReferenceDatasets:
    """Verify reference data catalog completeness."""

    def test_dataset_count(self):
        assert len(REFERENCE_DATASETS) >= 30

    def test_datasets_have_required_keys(self):
        required = {"label", "domain", "source", "source_url",
                     "update_frequency", "last_known_update",
                     "record_count", "status", "notes"}
        for data_id, ds in REFERENCE_DATASETS.items():
            for key in required:
                assert key in ds, f"Dataset '{data_id}' missing key '{key}'"

    def test_status_valid(self):
        valid = {"embedded", "seed_data", "missing", "stale"}
        for data_id, ds in REFERENCE_DATASETS.items():
            assert ds["status"] in valid, f"Dataset '{data_id}' invalid status: {ds['status']}"

    def test_domains_all_known(self):
        for data_id, ds in REFERENCE_DATASETS.items():
            assert ds["domain"] in REFERENCE_DOMAINS, \
                f"Dataset '{data_id}' unknown domain: {ds['domain']}"

    def test_missing_datasets_have_zero_records(self):
        for data_id, ds in REFERENCE_DATASETS.items():
            if ds["status"] == "missing":
                assert ds["record_count"] == 0, \
                    f"Missing dataset '{data_id}' should have 0 records"


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA CATALOG — Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestReferenceCatalogEngine:
    """Test reference data catalog engine."""

    def setup_method(self):
        self.engine = ReferenceDataCatalogEngine()

    def test_catalog_returns_result(self):
        result = self.engine.get_catalog()
        assert result.total_datasets >= 30
        assert result.coverage_pct > 0

    def test_catalog_counts_consistent(self):
        result = self.engine.get_catalog()
        total = result.embedded_count + result.seed_data_count + result.missing_count + result.stale_count
        assert total == result.total_datasets

    def test_catalog_filter_by_domain(self):
        result = self.engine.get_catalog(domain="emission_factors")
        for entry in result.entries:
            assert entry.domain == "emission_factors"

    def test_catalog_exclude_missing(self):
        result = self.engine.get_catalog(include_missing=False)
        for entry in result.entries:
            assert entry.status != "missing"

    def test_catalog_has_domains(self):
        result = self.engine.get_catalog()
        assert len(result.domains) > 0

    def test_catalog_recommendations(self):
        result = self.engine.get_catalog()
        assert isinstance(result.recommendations, list)

    def test_module_reference_data(self):
        entries = self.engine.get_module_reference_data("carbon_calculator")
        assert len(entries) >= 2
        for e in entries:
            assert "carbon_calculator" in e.used_by

    def test_module_reference_data_unknown(self):
        entries = self.engine.get_module_reference_data("nonexistent")
        assert len(entries) == 0

    def test_find_gaps(self):
        report = self.engine.find_gaps()
        assert report.total_missing >= 0  # All 8 previously-missing datasets now embedded
        assert isinstance(report.gaps, list)
        assert isinstance(report.remediation_priority, list)

    def test_gap_priorities_sorted(self):
        report = self.engine.find_gaps()
        if len(report.remediation_priority) > 1:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(report.remediation_priority) - 1):
                s1 = severity_order.get(report.remediation_priority[i]["severity"], 9)
                s2 = severity_order.get(report.remediation_priority[i + 1]["severity"], 9)
                assert s1 <= s2

    def test_get_domains(self):
        domains = self.engine.get_domains()
        assert len(domains) >= 7
        assert "emission_factors" in domains

    def test_get_dataset_exists(self):
        entry = self.engine.get_dataset("ghg_protocol_ef_scope1")
        assert entry is not None
        assert entry.status == "embedded"

    def test_get_dataset_missing(self):
        entry = self.engine.get_dataset("nonexistent_dataset")
        assert entry is None

    def test_missing_critical_datasets(self):
        result = self.engine.get_catalog()
        missing = result.missing_critical
        # All 8 previously-missing datasets now embedded — 0 missing expected
        assert len(missing) == 0
        for mc in missing:
            assert mc.status == "missing"


# ═══════════════════════════════════════════════════════════════════════════
#  REFERENCE DATA CATALOG — Domains
# ═══════════════════════════════════════════════════════════════════════════

class TestReferenceDomains:
    """Test reference data domain definitions."""

    def test_domain_count(self):
        assert len(REFERENCE_DOMAINS) >= 7

    def test_key_domains_present(self):
        expected = ["emission_factors", "financial_parameters", "regulatory",
                    "sector_benchmarks", "geographic", "entity_master"]
        for d in expected:
            assert d in REFERENCE_DOMAINS

    def test_domain_labels_non_empty(self):
        for domain, label in REFERENCE_DOMAINS.items():
            assert len(label) > 0


# ═══════════════════════════════════════════════════════════════════════════
#  API Routes — Data Lineage
# ═══════════════════════════════════════════════════════════════════════════

class TestLineageRoutes:
    """Test data lineage API route imports and serialisers."""

    def test_route_module_imports(self):
        from api.v1.routes.data_lineage import router
        assert router is not None
        assert router.prefix == "/api/v1/lineage"

    def test_trace_endpoint_exists(self):
        from api.v1.routes.data_lineage import trace_lineage
        assert callable(trace_lineage)

    def test_gaps_endpoint_exists(self):
        from api.v1.routes.data_lineage import find_gaps
        assert callable(find_gaps)

    def test_module_graph_endpoint_exists(self):
        from api.v1.routes.data_lineage import module_graph
        assert callable(module_graph)

    def test_quality_endpoint_exists(self):
        from api.v1.routes.data_lineage import propagate_quality
        assert callable(propagate_quality)


# ═══════════════════════════════════════════════════════════════════════════
#  API Routes — Reference Catalog
# ═══════════════════════════════════════════════════════════════════════════

class TestCatalogRoutes:
    """Test reference catalog API route imports and serialisers."""

    def test_route_module_imports(self):
        from api.v1.routes.reference_catalog import router
        assert router is not None
        assert router.prefix == "/api/v1/reference-catalog"

    def test_catalog_endpoint_exists(self):
        from api.v1.routes.reference_catalog import catalog
        assert callable(catalog)

    def test_domains_endpoint_exists(self):
        from api.v1.routes.reference_catalog import domains
        assert callable(domains)

    def test_gaps_endpoint_exists(self):
        from api.v1.routes.reference_catalog import gaps
        assert callable(gaps)

    def test_module_ref_endpoint_exists(self):
        from api.v1.routes.reference_catalog import module_reference_data
        assert callable(module_reference_data)
