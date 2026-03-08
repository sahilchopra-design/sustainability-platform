"""
XBRL Ingestion Engine
======================
Parses iXBRL (inline XBRL in HTML) and XBRL XML instance documents,
extracts structured facts, and maps them to platform data-point IDs
for direct database storage.

Supports multiple taxonomies:
- EFRAG ESRS (2024) — EU CSRD sustainability reports
- IFRS S1/S2 (ISSB) — Global baseline sustainability disclosures
- IFRS Full / SME — Financial statements (ESEF filings)
- US GAAP — SEC EDGAR filings
- GRI Standards — Global Reporting Initiative

References:
- XBRL 2.1 Specification — fact extraction model
- iXBRL Specification (Inline XBRL 1.1) — HTML-embedded tags
- ESMA ESEF Reporting Manual — European single electronic format
- SEC EDGAR XBRL Technical Specification — US filing format
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import re
import html as html_mod


# ---------------------------------------------------------------------------
# Supported Taxonomies / Report Schemas
# ---------------------------------------------------------------------------

SUPPORTED_SCHEMAS: dict[str, dict] = {
    "esrs_2024": {
        "label": "EFRAG ESRS XBRL Taxonomy 2024",
        "namespace": "http://xbrl.efrag.org/taxonomy/esrs/2024",
        "prefix": "esrs",
        "report_types": ["CSRD Annual Report", "ESRS Sustainability Statement"],
        "region": "EU",
        "standards": ["E1", "E2", "E3", "E4", "E5", "S1", "S2", "S3", "S4", "G1", "ESRS2"],
    },
    "ifrs_s1s2_2024": {
        "label": "IFRS S1/S2 Sustainability Taxonomy 2024",
        "namespace": "http://xbrl.ifrs.org/taxonomy/ifrs-s2/2024",
        "prefix": "ifrs-s2",
        "report_types": ["ISSB Sustainability Disclosure", "Climate-related Financial Disclosure"],
        "region": "Global",
        "standards": ["S1-General", "S2-Climate"],
    },
    "ifrs_full_2024": {
        "label": "IFRS Accounting Taxonomy 2024",
        "namespace": "http://xbrl.ifrs.org/taxonomy/2024",
        "prefix": "ifrs-full",
        "report_types": ["ESEF Annual Financial Report", "IFRS Financial Statements"],
        "region": "Global (140+ jurisdictions)",
        "standards": ["IAS/IFRS"],
    },
    "us_gaap_2024": {
        "label": "US GAAP XBRL Taxonomy 2024",
        "namespace": "http://fasb.org/us-gaap/2024",
        "prefix": "us-gaap",
        "report_types": ["SEC 10-K", "SEC 10-Q", "SEC 20-F", "SEC 8-K"],
        "region": "United States",
        "standards": ["US GAAP / ASC"],
    },
    "gri_2024": {
        "label": "GRI Standards Taxonomy 2024",
        "namespace": "http://xbrl.globalreporting.org/taxonomy/gri/2024",
        "prefix": "gri",
        "report_types": ["GRI Sustainability Report"],
        "region": "Global",
        "standards": ["GRI 200/300/400"],
    },
    "esef_lei": {
        "label": "ESEF Entity Identification (LEI-based)",
        "namespace": "http://standards.iso.org/iso/17442",
        "prefix": "lei",
        "report_types": ["European Annual Financial Report"],
        "region": "EU/EEA",
        "standards": ["ESEF Delegated Regulation 2019/815"],
    },
}

# Known concept → dp_id reverse map (for ESRS taxonomy)
# This allows ingested XBRL facts to be mapped back to platform DPs
CONCEPT_TO_DP: dict[str, dict] = {
    "esrs:GrossScope1GHGEmissions": {
        "dp_id": "E1-6_scope1_gross", "esrs": "E1", "dr": "E1-6",
        "label": "Gross Scope 1 GHG emissions", "unit": "tCO2e",
    },
    "esrs:GrossScope2GHGEmissionsLocationBased": {
        "dp_id": "E1-6_scope2_location", "esrs": "E1", "dr": "E1-6",
        "label": "Gross Scope 2 GHG emissions (location-based)", "unit": "tCO2e",
    },
    "esrs:GrossScope2GHGEmissionsMarketBased": {
        "dp_id": "E1-6_scope2_market", "esrs": "E1", "dr": "E1-6",
        "label": "Gross Scope 2 GHG emissions (market-based)", "unit": "tCO2e",
    },
    "esrs:TotalScope3GHGEmissions": {
        "dp_id": "E1-6_scope3_total", "esrs": "E1", "dr": "E1-6",
        "label": "Total Scope 3 GHG emissions", "unit": "tCO2e",
    },
    "esrs:TotalGHGEmissions": {
        "dp_id": "E1-6_total_ghg", "esrs": "E1", "dr": "E1-6",
        "label": "Total GHG emissions (Scope 1+2+3)", "unit": "tCO2e",
    },
    "esrs:GHGIntensityPerNetRevenue": {
        "dp_id": "E1-6_ghg_intensity_revenue", "esrs": "E1", "dr": "E1-6",
        "label": "GHG intensity per net revenue", "unit": "tCO2e/EUR M",
    },
    "esrs:TotalEnergyConsumption": {
        "dp_id": "E1-5_energy_consumption_total", "esrs": "E1", "dr": "E1-5",
        "label": "Total energy consumption", "unit": "MWh",
    },
    "esrs:ShareOfRenewableEnergy": {
        "dp_id": "E1-5_renewable_share", "esrs": "E1", "dr": "E1-5",
        "label": "Share of renewable energy", "unit": "%",
    },
    "esrs:InternalCarbonPrice": {
        "dp_id": "E1-9_internal_carbon_price", "esrs": "E1", "dr": "E1-9",
        "label": "Internal carbon price applied", "unit": "EUR/tCO2e",
    },
    "esrs:FinancialEffectsTransitionRisks": {
        "dp_id": "E1-9_transition_risk_amount", "esrs": "E1", "dr": "E1-9",
        "label": "Potential financial effects — transition risks", "unit": "EUR",
    },
    "esrs:FinancialEffectsPhysicalRisks": {
        "dp_id": "E1-9_physical_risk_amount", "esrs": "E1", "dr": "E1-9",
        "label": "Potential financial effects — physical risks", "unit": "EUR",
    },
    "esrs:PollutantsEmittedToAir": {
        "dp_id": "E2-4_pollutants_air", "esrs": "E2", "dr": "E2-4",
        "label": "Pollutants emitted to air", "unit": "tonnes",
    },
    "esrs:TotalWaterConsumption": {
        "dp_id": "E3-4_water_consumption", "esrs": "E3", "dr": "E3-4",
        "label": "Total water consumption", "unit": "m3",
    },
    "esrs:TotalLandUseChange": {
        "dp_id": "E4-5_land_use_change", "esrs": "E4", "dr": "E4-5",
        "label": "Total land-use change", "unit": "hectares",
    },
    "esrs:TotalWasteGenerated": {
        "dp_id": "E5-5_waste_generated", "esrs": "E5", "dr": "E5-5",
        "label": "Total waste generated", "unit": "tonnes",
    },
    # ISSB S2
    "ifrs-s2:AbsoluteGrossScope1GHGEmissions": {
        "dp_id": "S2_scope1_ghg", "esrs": "S2", "dr": "S2-Metrics",
        "label": "Absolute gross Scope 1 GHG emissions (ISSB S2)", "unit": "tCO2e",
    },
    "ifrs-s2:AbsoluteGrossScope2GHGEmissions": {
        "dp_id": "S2_scope2_ghg", "esrs": "S2", "dr": "S2-Metrics",
        "label": "Absolute gross Scope 2 GHG emissions (ISSB S2)", "unit": "tCO2e",
    },
    # IFRS financial items (common ESEF tags)
    "ifrs-full:Revenue": {
        "dp_id": "IFRS_revenue", "esrs": "IFRS", "dr": "IAS1",
        "label": "Revenue", "unit": "EUR",
    },
    "ifrs-full:ProfitLoss": {
        "dp_id": "IFRS_profit_loss", "esrs": "IFRS", "dr": "IAS1",
        "label": "Profit (loss)", "unit": "EUR",
    },
    "ifrs-full:Assets": {
        "dp_id": "IFRS_total_assets", "esrs": "IFRS", "dr": "IAS1",
        "label": "Total assets", "unit": "EUR",
    },
    "ifrs-full:Equity": {
        "dp_id": "IFRS_equity", "esrs": "IFRS", "dr": "IAS1",
        "label": "Total equity", "unit": "EUR",
    },
    # US GAAP common items
    "us-gaap:Revenues": {
        "dp_id": "USGAAP_revenues", "esrs": "USGAAP", "dr": "ASC606",
        "label": "Revenues", "unit": "USD",
    },
    "us-gaap:NetIncomeLoss": {
        "dp_id": "USGAAP_net_income", "esrs": "USGAAP", "dr": "ASC220",
        "label": "Net Income (Loss)", "unit": "USD",
    },
    "us-gaap:Assets": {
        "dp_id": "USGAAP_total_assets", "esrs": "USGAAP", "dr": "ASC210",
        "label": "Total Assets", "unit": "USD",
    },
    "us-gaap:StockholdersEquity": {
        "dp_id": "USGAAP_equity", "esrs": "USGAAP", "dr": "ASC210",
        "label": "Stockholders Equity", "unit": "USD",
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ExtractedFact:
    """A fact extracted from an XBRL/iXBRL document."""
    concept: str
    value: float
    unit: str
    context_id: str
    period_start: str
    period_end: str
    period_type: str  # "duration" | "instant"
    decimals: int
    entity_id: str
    # Mapping info (populated if concept is known)
    dp_id: Optional[str] = None
    esrs: Optional[str] = None
    dr: Optional[str] = None
    label: Optional[str] = None
    mapped: bool = False


@dataclass
class IngestionResult:
    """Complete result of XBRL document ingestion."""
    source_format: str  # "ixbrl" | "xbrl_xml"
    detected_taxonomy: str
    entity_name: str
    entity_id: str  # LEI or CIK
    reporting_period: str
    period_start: str
    period_end: str
    total_facts_extracted: int
    mapped_facts: int
    unmapped_facts: int
    mapping_rate_pct: float
    facts: list[ExtractedFact]
    taxonomy_coverage: dict[str, int]  # {esrs_standard: count}
    unmapped_concepts: list[str]
    warnings: list[str]
    ready_for_db: bool  # True if >= 1 mapped fact


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class XBRLIngestionEngine:
    """Parse and extract structured data from XBRL/iXBRL documents."""

    def ingest_ixbrl(self, html_content: str) -> IngestionResult:
        """Parse an iXBRL (inline XBRL in HTML) document."""
        facts = []
        warnings = []
        entity_name = ""
        entity_id = ""
        period_start = ""
        period_end = ""

        # Extract entity name from ix:nonNumeric
        name_match = re.search(
            r'<ix:nonNumeric[^>]*name="[^"]*EntityName"[^>]*>(.*?)</ix:nonNumeric>',
            html_content, re.DOTALL
        )
        if name_match:
            entity_name = html_mod.unescape(name_match.group(1).strip())

        # Extract LEI from identifier
        lei_match = re.search(
            r'<xbrli:identifier[^>]*>(.*?)</xbrli:identifier>',
            html_content, re.DOTALL
        )
        if lei_match:
            entity_id = html_mod.unescape(lei_match.group(1).strip())

        # Extract period from contexts
        period_matches = re.findall(
            r'<xbrli:startDate>([\d-]+)</xbrli:startDate>\s*<xbrli:endDate>([\d-]+)</xbrli:endDate>',
            html_content
        )
        if period_matches:
            period_start = period_matches[0][0]
            period_end = period_matches[0][1]

        instant_matches = re.findall(
            r'<xbrli:instant>([\d-]+)</xbrli:instant>',
            html_content
        )

        # Extract numeric facts from ix:nonFraction
        fact_pattern = re.compile(
            r'<ix:nonFraction\s+'
            r'name="([^"]+)"\s+'
            r'contextRef="([^"]+)"\s+'
            r'unitRef="([^"]+)"\s+'
            r'decimals="([^"]*)">'
            r'([^<]+)</ix:nonFraction>',
            re.DOTALL
        )

        for m in fact_pattern.finditer(html_content):
            concept = m.group(1)
            ctx_id = m.group(2)
            unit_ref = m.group(3)
            decimals_str = m.group(4)
            value_str = m.group(5).strip()

            try:
                value = float(value_str.replace(",", ""))
            except ValueError:
                warnings.append(f"Non-numeric value for {concept}: '{value_str}'")
                continue

            decimals = int(decimals_str) if decimals_str.lstrip("-").isdigit() else 0

            # Look up mapping
            mapping = CONCEPT_TO_DP.get(concept)
            p_type = "duration" if period_start else "instant"

            facts.append(ExtractedFact(
                concept=concept,
                value=value,
                unit=unit_ref,
                context_id=ctx_id,
                period_start=period_start,
                period_end=period_end if p_type == "duration" else (instant_matches[0] if instant_matches else period_end),
                period_type=p_type,
                decimals=decimals,
                entity_id=entity_id,
                dp_id=mapping["dp_id"] if mapping else None,
                esrs=mapping["esrs"] if mapping else None,
                dr=mapping["dr"] if mapping else None,
                label=mapping["label"] if mapping else concept,
                mapped=mapping is not None,
            ))

        return self._build_result("ixbrl", entity_name, entity_id,
                                   period_start, period_end, facts, warnings, html_content)

    def ingest_xbrl_xml(self, xml_content: str) -> IngestionResult:
        """Parse an XBRL XML instance document."""
        facts = []
        warnings = []
        entity_name = ""
        entity_id = ""
        period_start = ""
        period_end = ""

        # Extract entity identifier
        lei_match = re.search(
            r'<xbrli:identifier[^>]*>(.*?)</xbrli:identifier>',
            xml_content, re.DOTALL
        )
        if lei_match:
            entity_id = html_mod.unescape(lei_match.group(1).strip())

        # Extract contexts: map context_id -> (period_start, period_end, period_type)
        contexts: dict[str, tuple] = {}

        # Extract individual context blocks first, then parse each
        ctx_block_pattern = re.compile(
            r'<xbrli:context\s+id="([^"]+)">(.*?)</xbrli:context>',
            re.DOTALL
        )
        for m in ctx_block_pattern.finditer(xml_content):
            ctx_id = m.group(1)
            block = m.group(2)

            dur_match = re.search(
                r'<xbrli:startDate>([\d-]+)</xbrli:startDate>\s*<xbrli:endDate>([\d-]+)</xbrli:endDate>',
                block
            )
            inst_match = re.search(
                r'<xbrli:instant>([\d-]+)</xbrli:instant>',
                block
            )

            if dur_match:
                contexts[ctx_id] = (dur_match.group(1), dur_match.group(2), "duration")
                if not period_start:
                    period_start = dur_match.group(1)
                    period_end = dur_match.group(2)
            elif inst_match:
                contexts[ctx_id] = ("", inst_match.group(1), "instant")
                if not period_end:
                    period_end = inst_match.group(1)

        # Extract units: map unit_id -> measure
        units: dict[str, str] = {}
        unit_pattern = re.compile(
            r'<xbrli:unit\s+id="([^"]+)">\s*<xbrli:measure>([^<]+)</xbrli:measure>',
            re.DOTALL
        )
        for m in unit_pattern.finditer(xml_content):
            units[m.group(1)] = m.group(2)

        # Extract fact elements — look for prefixed elements with contextRef
        fact_pattern = re.compile(
            r'<([\w-]+:[\w]+)\s+contextRef="([^"]+)"\s+unitRef="([^"]+)"\s+'
            r'decimals="([^"]*)">([\d.eE+\-,]+)</\1>',
            re.DOTALL
        )

        for m in fact_pattern.finditer(xml_content):
            concept = m.group(1)
            ctx_id = m.group(2)
            unit_ref = m.group(3)
            decimals_str = m.group(4)
            value_str = m.group(5).strip()

            try:
                value = float(value_str.replace(",", ""))
            except ValueError:
                warnings.append(f"Non-numeric value for {concept}: '{value_str}'")
                continue

            decimals = int(decimals_str) if decimals_str.lstrip("-").isdigit() else 0

            ctx = contexts.get(ctx_id, ("", "", "duration"))
            mapping = CONCEPT_TO_DP.get(concept)

            facts.append(ExtractedFact(
                concept=concept,
                value=value,
                unit=units.get(unit_ref, unit_ref),
                context_id=ctx_id,
                period_start=ctx[0],
                period_end=ctx[1],
                period_type=ctx[2],
                decimals=decimals,
                entity_id=entity_id,
                dp_id=mapping["dp_id"] if mapping else None,
                esrs=mapping["esrs"] if mapping else None,
                dr=mapping["dr"] if mapping else None,
                label=mapping["label"] if mapping else concept,
                mapped=mapping is not None,
            ))

        return self._build_result("xbrl_xml", entity_name, entity_id,
                                   period_start, period_end, facts, warnings, xml_content)

    def ingest_auto(self, content: str) -> IngestionResult:
        """Auto-detect format (iXBRL HTML vs XBRL XML) and parse."""
        content_stripped = content.strip()
        if content_stripped.startswith("<?xml") or content_stripped.startswith("<xbrli:xbrl"):
            return self.ingest_xbrl_xml(content)
        elif "<ix:nonFraction" in content or "<ix:header" in content:
            return self.ingest_ixbrl(content)
        elif "<html" in content.lower()[:200]:
            return self.ingest_ixbrl(content)
        else:
            return self.ingest_xbrl_xml(content)

    def _build_result(
        self, fmt: str, entity_name: str, entity_id: str,
        period_start: str, period_end: str,
        facts: list[ExtractedFact], warnings: list[str],
        raw_content: str,
    ) -> IngestionResult:
        """Build final ingestion result with coverage stats."""
        mapped = [f for f in facts if f.mapped]
        unmapped = [f for f in facts if not f.mapped]

        total = len(facts)
        mapped_count = len(mapped)
        rate = (mapped_count / total * 100) if total > 0 else 0

        # Taxonomy coverage
        coverage: dict[str, int] = {}
        for f in mapped:
            if f.esrs:
                coverage[f.esrs] = coverage.get(f.esrs, 0) + 1

        # Detect taxonomy from namespace
        detected = "unknown"
        for schema_id, schema in SUPPORTED_SCHEMAS.items():
            if schema["namespace"] in raw_content or schema["prefix"] + ":" in raw_content:
                detected = schema_id
                break

        unmapped_concepts = list(set(f.concept for f in unmapped))

        # If entity_name not found, try title
        if not entity_name:
            title_match = re.search(r'<title>(.*?)</title>', raw_content, re.DOTALL | re.IGNORECASE)
            if title_match:
                entity_name = html_mod.unescape(title_match.group(1).strip())
                # Clean up common suffixes
                for suffix in [" — ESRS Report", " - XBRL Instance"]:
                    entity_name = entity_name.replace(suffix, "")

        rp = f"{period_start} / {period_end}" if period_start and period_end else period_end or "unknown"

        return IngestionResult(
            source_format=fmt,
            detected_taxonomy=detected,
            entity_name=entity_name,
            entity_id=entity_id,
            reporting_period=rp,
            period_start=period_start,
            period_end=period_end,
            total_facts_extracted=total,
            mapped_facts=mapped_count,
            unmapped_facts=len(unmapped),
            mapping_rate_pct=round(rate, 1),
            facts=facts,
            taxonomy_coverage=coverage,
            unmapped_concepts=unmapped_concepts,
            warnings=warnings,
            ready_for_db=mapped_count > 0,
        )

    def get_supported_schemas(self) -> dict[str, dict]:
        return SUPPORTED_SCHEMAS

    def get_concept_mappings(self) -> dict[str, dict]:
        return CONCEPT_TO_DP

    def get_mapped_concept_count(self) -> int:
        return len(CONCEPT_TO_DP)
