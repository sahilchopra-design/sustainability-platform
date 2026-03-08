"""
Tests for XBRL Export & Ingestion API
=======================================
Tests cover:
- XBRL export (fact generation, iXBRL HTML, XBRL XML, ESEF validation)
- XBRL ingestion (iXBRL parsing, XBRL XML parsing, auto-detection, mapping)
- Reference data endpoints
"""
import pytest
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.xbrl_export_engine import (
    XBRLExportEngine,
    ESRS_XBRL_TAXONOMY,
    ESEF_VALIDATION_RULES,
)
from services.xbrl_ingestion_engine import (
    XBRLIngestionEngine,
    SUPPORTED_SCHEMAS,
    CONCEPT_TO_DP,
)

_export = XBRLExportEngine()
_ingest = XBRLIngestionEngine()


# ═══════════════════════════════════════════════════════════════════════════
# XBRL Export Engine Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestXBRLExport:
    """Test XBRL export with valid data points."""

    def test_basic_export(self):
        res = _export.export(
            entity_name="Test Corp",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 50000},
        )
        assert res.entity_name == "Test Corp"
        assert res.fact_count == 1
        assert res.facts[0].concept == "esrs:GrossScope1GHGEmissions"
        assert res.facts[0].value == 50000

    def test_multi_dp_export(self):
        dps = {
            "E1-6_scope1_gross": 50000,
            "E1-6_scope2_location": 20000,
            "E1-6_scope3_total": 150000,
            "E1-6_total_ghg": 220000,
        }
        res = _export.export(
            entity_name="Multi Corp",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points=dps,
        )
        assert res.fact_count == 4
        assert res.coverage_by_esrs.get("E1") == 4

    def test_unknown_dp_ignored(self):
        res = _export.export(
            entity_name="Test",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"nonexistent_dp": 999},
        )
        assert res.fact_count == 0

    def test_empty_data_points(self):
        res = _export.export(
            entity_name="Empty",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={},
        )
        assert res.fact_count == 0
        assert res.validation_passed  # No facts = no concept/duplicate errors

    def test_period_in_result(self):
        res = _export.export(
            entity_name="Period Test",
            entity_lei="5299001ABCDEFGHIJ012",
            period_start="2023-01-01",
            period_end="2023-12-31",
            data_points={"E1-6_scope1_gross": 1000},
        )
        assert "2023-01-01" in res.reporting_period
        assert "2023-12-31" in res.reporting_period

    def test_coverage_by_esrs(self):
        dps = {
            "E1-6_scope1_gross": 100,
            "E2-4_pollutants_air": 50,
            "E3-4_water_consumption": 2000,
        }
        res = _export.export(
            entity_name="Coverage Corp",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points=dps,
        )
        assert res.coverage_by_esrs["E1"] == 1
        assert res.coverage_by_esrs["E2"] == 1
        assert res.coverage_by_esrs["E3"] == 1

    def test_taxonomy_version(self):
        res = _export.export(
            entity_name="Version",
            entity_lei="5299001ABCDEFGHIJ012",
        )
        assert "ESRS" in res.taxonomy_version

    def test_issb_s2_concept(self):
        res = _export.export(
            entity_name="ISSB Corp",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"S2_scope1_ghg": 75000},
        )
        assert res.fact_count == 1
        assert res.facts[0].concept == "ifrs-s2:AbsoluteGrossScope1GHGEmissions"
        assert res.coverage_by_esrs.get("S2") == 1


class TestIXBRLGeneration:
    """Test iXBRL HTML output."""

    def test_ixbrl_contains_html(self):
        res = _export.export(
            entity_name="HTML Corp",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 30000},
        )
        assert "<!DOCTYPE html>" in res.ixbrl_html
        assert "<ix:nonFraction" in res.ixbrl_html
        assert "HTML Corp" in res.ixbrl_html

    def test_ixbrl_has_schema_ref(self):
        res = _export.export(
            entity_name="Schema",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 100},
        )
        assert "esrs-2024.xsd" in res.ixbrl_html

    def test_ixbrl_table_rows(self):
        dps = {"E1-6_scope1_gross": 100, "E1-6_scope2_location": 200}
        res = _export.export(
            entity_name="Table",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points=dps,
        )
        assert res.ixbrl_html.count("<ix:nonFraction") == 2

    def test_ixbrl_entity_name_escaped(self):
        res = _export.export(
            entity_name="A&B <Corp>",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 100},
        )
        assert "&amp;" in res.ixbrl_html
        assert "&lt;" in res.ixbrl_html

    def test_ixbrl_period_shown(self):
        res = _export.export(
            entity_name="Period",
            entity_lei="5299001ABCDEFGHIJ012",
            period_start="2024-01-01",
            period_end="2024-12-31",
            data_points={"E1-6_scope1_gross": 100},
        )
        assert "2024-01-01" in res.ixbrl_html
        assert "2024-12-31" in res.ixbrl_html


class TestXBRLXMLGeneration:
    """Test XBRL XML output."""

    def test_xml_has_xbrl_root(self):
        res = _export.export(
            entity_name="XML Corp",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 40000},
        )
        assert '<?xml version="1.0"' in res.xbrl_xml
        assert "<xbrli:xbrl" in res.xbrl_xml

    def test_xml_has_context(self):
        res = _export.export(
            entity_name="Ctx",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 100},
        )
        assert "<xbrli:context" in res.xbrl_xml
        assert "<xbrli:startDate>" in res.xbrl_xml

    def test_xml_instant_context(self):
        res = _export.export(
            entity_name="Instant",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-9_internal_carbon_price": 50},
        )
        assert "<xbrli:instant>" in res.xbrl_xml

    def test_xml_unit_elements(self):
        res = _export.export(
            entity_name="Unit",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 100},
        )
        assert "<xbrli:unit" in res.xbrl_xml
        assert "<xbrli:measure>" in res.xbrl_xml

    def test_xml_fact_element(self):
        res = _export.export(
            entity_name="Fact",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 12345},
        )
        assert "12345" in res.xbrl_xml
        assert "esrs:GrossScope1GHGEmissions" in res.xbrl_xml


class TestESEFValidation:
    """Test ESEF validation rules."""

    def test_valid_lei_passes(self):
        res = _export.export(
            entity_name="Valid",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 100},
        )
        lei_result = next(v for v in res.validation_results if v.rule_id == "ESEF-001")
        assert lei_result.passed is True

    def test_invalid_lei_fails(self):
        res = _export.export(
            entity_name="Invalid",
            entity_lei="SHORT",
            data_points={"E1-6_scope1_gross": 100},
        )
        lei_result = next(v for v in res.validation_results if v.rule_id == "ESEF-001")
        assert lei_result.passed is False
        assert not res.validation_passed

    def test_valid_period_passes(self):
        res = _export.export(
            entity_name="Period",
            entity_lei="5299001ABCDEFGHIJ012",
            period_start="2024-01-01",
            period_end="2024-12-31",
        )
        period_result = next(v for v in res.validation_results if v.rule_id == "ESEF-002")
        assert period_result.passed is True

    def test_invalid_period_fails(self):
        res = _export.export(
            entity_name="Bad Period",
            entity_lei="5299001ABCDEFGHIJ012",
            period_start="2024-12-31",
            period_end="2024-01-01",
        )
        period_result = next(v for v in res.validation_results if v.rule_id == "ESEF-002")
        assert period_result.passed is False

    def test_concept_validation(self):
        res = _export.export(
            entity_name="Concept",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 100},
        )
        concept_checks = [v for v in res.validation_results if v.rule_id == "ESEF-005"]
        assert all(v.passed for v in concept_checks)

    def test_no_duplicates(self):
        res = _export.export(
            entity_name="NoDup",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points={"E1-6_scope1_gross": 100, "E1-6_scope2_location": 200},
        )
        dup_checks = [v for v in res.validation_results if v.rule_id == "ESEF-007"]
        assert all(v.passed for v in dup_checks)

    def test_errors_count(self):
        res = _export.export(
            entity_name="Errors",
            entity_lei="BAD_LEI",
            period_start="2025-01-01",
            period_end="2024-01-01",
        )
        assert res.errors_count >= 2  # LEI + Period


# ═══════════════════════════════════════════════════════════════════════════
# XBRL Ingestion Engine Tests
# ═══════════════════════════════════════════════════════════════════════════

def _make_sample_ixbrl() -> str:
    """Build a minimal iXBRL document for testing."""
    return """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:esrs="http://xbrl.efrag.org/taxonomy/esrs/2024">
<head><title>ESRS Report — Ingestion Test Corp</title></head>
<body>
<ix:header>
  <ix:hidden>
    <ix:nonNumeric name="esrs:EntityName" contextRef="ctx_entity">Ingestion Test Corp</ix:nonNumeric>
  </ix:hidden>
  <ix:references>
    <link:schemaRef xlink:href="esrs-2024.xsd"/>
  </ix:references>
</ix:header>
<xbrli:context id="ctx_001">
  <xbrli:entity><xbrli:identifier scheme="http://standards.iso.org/iso/17442">5299001ABCDEFGHIJ012</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-12-31</xbrli:endDate></xbrli:period>
</xbrli:context>
<table>
<tr><td>Scope 1</td><td><ix:nonFraction name="esrs:GrossScope1GHGEmissions" contextRef="ctx_001" unitRef="u_tco2e" decimals="0">50000</ix:nonFraction></td></tr>
<tr><td>Scope 2</td><td><ix:nonFraction name="esrs:GrossScope2GHGEmissionsLocationBased" contextRef="ctx_001" unitRef="u_tco2e" decimals="0">20000</ix:nonFraction></td></tr>
<tr><td>Unknown</td><td><ix:nonFraction name="custom:SomethingElse" contextRef="ctx_001" unitRef="u_tco2e" decimals="0">999</ix:nonFraction></td></tr>
</table>
</body></html>"""


def _make_sample_xbrl_xml() -> str:
    """Build a minimal XBRL XML instance for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl
  xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:esrs="http://xbrl.efrag.org/taxonomy/esrs/2024"
  xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
  xmlns:xlink="http://www.w3.org/1999/xlink">

  <xbrli:schemaRef xlink:href="esrs-2024.xsd" xlink:type="simple"/>

  <xbrli:context id="ctx_001">
    <xbrli:entity><xbrli:identifier scheme="http://standards.iso.org/iso/17442">5299001ABCDEFGHIJ012</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-12-31</xbrli:endDate></xbrli:period>
  </xbrli:context>
  <xbrli:context id="ctx_002">
    <xbrli:entity><xbrli:identifier scheme="http://standards.iso.org/iso/17442">5299001ABCDEFGHIJ012</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:instant>2024-12-31</xbrli:instant></xbrli:period>
  </xbrli:context>

  <xbrli:unit id="u_pure"><xbrli:measure>xbrli:pure</xbrli:measure></xbrli:unit>
  <xbrli:unit id="u_eur"><xbrli:measure>iso4217:EUR</xbrli:measure></xbrli:unit>

  <esrs:GrossScope1GHGEmissions contextRef="ctx_001" unitRef="u_pure" decimals="0">75000</esrs:GrossScope1GHGEmissions>
  <esrs:TotalScope3GHGEmissions contextRef="ctx_001" unitRef="u_pure" decimals="0">300000</esrs:TotalScope3GHGEmissions>
  <esrs:InternalCarbonPrice contextRef="ctx_002" unitRef="u_eur" decimals="0">85</esrs:InternalCarbonPrice>
</xbrli:xbrl>"""


class TestIXBRLIngestion:
    """Test iXBRL document parsing."""

    def test_parse_entity_name(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.entity_name == "Ingestion Test Corp"

    def test_parse_entity_id(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.entity_id == "5299001ABCDEFGHIJ012"

    def test_parse_period(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.period_start == "2024-01-01"
        assert res.period_end == "2024-12-31"

    def test_extract_facts_count(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.total_facts_extracted == 3  # 2 known + 1 unknown

    def test_mapped_facts(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.mapped_facts == 2

    def test_unmapped_facts(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.unmapped_facts == 1
        assert "custom:SomethingElse" in res.unmapped_concepts

    def test_mapping_rate(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.mapping_rate_pct == pytest.approx(66.7, abs=0.1)

    def test_taxonomy_coverage(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.taxonomy_coverage.get("E1") == 2

    def test_format_detected(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.source_format == "ixbrl"

    def test_detected_taxonomy(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.detected_taxonomy == "esrs_2024"

    def test_ready_for_db(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        assert res.ready_for_db is True

    def test_fact_values(self):
        res = _ingest.ingest_ixbrl(_make_sample_ixbrl())
        scope1 = next(f for f in res.facts if f.dp_id == "E1-6_scope1_gross")
        assert scope1.value == 50000
        scope2 = next(f for f in res.facts if f.dp_id == "E1-6_scope2_location")
        assert scope2.value == 20000


class TestXBRLXMLIngestion:
    """Test XBRL XML instance parsing."""

    def test_parse_entity_id(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        assert res.entity_id == "5299001ABCDEFGHIJ012"

    def test_parse_period(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        assert res.period_start == "2024-01-01"
        assert res.period_end == "2024-12-31"

    def test_extract_facts_count(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        assert res.total_facts_extracted == 3

    def test_all_mapped(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        assert res.mapped_facts == 3
        assert res.mapping_rate_pct == 100.0

    def test_scope1_value(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        scope1 = next(f for f in res.facts if f.dp_id == "E1-6_scope1_gross")
        assert scope1.value == 75000

    def test_instant_context_parsed(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        carbon = next(f for f in res.facts if f.dp_id == "E1-9_internal_carbon_price")
        assert carbon.value == 85
        assert carbon.period_type == "instant"

    def test_format_detected(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        assert res.source_format == "xbrl_xml"

    def test_detected_taxonomy(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        assert res.detected_taxonomy == "esrs_2024"

    def test_ready_for_db(self):
        res = _ingest.ingest_xbrl_xml(_make_sample_xbrl_xml())
        assert res.ready_for_db is True


class TestAutoDetect:
    """Test auto-detection of XBRL format."""

    def test_auto_detects_ixbrl(self):
        res = _ingest.ingest_auto(_make_sample_ixbrl())
        assert res.source_format == "ixbrl"
        assert res.total_facts_extracted == 3

    def test_auto_detects_xbrl_xml(self):
        res = _ingest.ingest_auto(_make_sample_xbrl_xml())
        assert res.source_format == "xbrl_xml"
        assert res.total_facts_extracted == 3

    def test_empty_content(self):
        res = _ingest.ingest_auto("<xbrli:xbrl></xbrli:xbrl>")
        assert res.total_facts_extracted == 0
        assert res.ready_for_db is False


class TestIngestionRoundTrip:
    """Test export→ingest round-trip fidelity."""

    def test_export_then_ingest_ixbrl(self):
        dps = {
            "E1-6_scope1_gross": 50000,
            "E1-6_scope2_location": 20000,
        }
        export_res = _export.export(
            entity_name="RoundTrip Corp",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points=dps,
        )
        # Ingest the exported iXBRL
        ingest_res = _ingest.ingest_ixbrl(export_res.ixbrl_html)
        assert ingest_res.total_facts_extracted == 2
        assert ingest_res.mapped_facts == 2
        scope1 = next(f for f in ingest_res.facts if f.dp_id == "E1-6_scope1_gross")
        assert scope1.value == 50000

    def test_export_then_ingest_xml(self):
        dps = {
            "E1-6_scope1_gross": 75000,
            "E1-6_scope3_total": 300000,
            "E1-9_internal_carbon_price": 85,
        }
        export_res = _export.export(
            entity_name="XML RT",
            entity_lei="5299001ABCDEFGHIJ012",
            data_points=dps,
        )
        ingest_res = _ingest.ingest_xbrl_xml(export_res.xbrl_xml)
        assert ingest_res.total_facts_extracted == 3
        assert ingest_res.mapped_facts == 3


# ═══════════════════════════════════════════════════════════════════════════
# Reference Data Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestExportReferenceData:
    """Test export reference data methods."""

    def test_taxonomy_count(self):
        tax = _export.get_taxonomy()
        assert len(tax) >= 17

    def test_validation_rules(self):
        rules = _export.get_validation_rules()
        assert len(rules) == 7

    def test_supported_standards(self):
        standards = _export.get_supported_standards()
        assert "E1" in standards
        assert "S2" in standards


class TestIngestionReferenceData:
    """Test ingestion reference data methods."""

    def test_supported_schemas(self):
        schemas = _ingest.get_supported_schemas()
        assert len(schemas) >= 6
        assert "esrs_2024" in schemas
        assert "us_gaap_2024" in schemas
        assert "ifrs_full_2024" in schemas

    def test_concept_mappings(self):
        mappings = _ingest.get_concept_mappings()
        assert len(mappings) >= 20
        assert "esrs:GrossScope1GHGEmissions" in mappings
        assert "us-gaap:Revenues" in mappings

    def test_mapped_concept_count(self):
        count = _ingest.get_mapped_concept_count()
        assert count >= 20

    def test_schema_has_required_fields(self):
        for sid, schema in SUPPORTED_SCHEMAS.items():
            assert "label" in schema
            assert "namespace" in schema
            assert "prefix" in schema
            assert "report_types" in schema
            assert "region" in schema

    def test_concept_mapping_has_required_fields(self):
        for concept, mapping in CONCEPT_TO_DP.items():
            assert "dp_id" in mapping
            assert "esrs" in mapping
            assert "label" in mapping
            assert "unit" in mapping
