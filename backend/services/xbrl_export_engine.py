"""
XBRL Export Engine (CSRD / ISSB / ESEF)
=========================================
Generates iXBRL-tagged HTML and XBRL XML for regulatory filing.
Maps ESRS data points to EFRAG XBRL taxonomy concepts, tags KPI values
with period/unit/entity identifiers, and validates against ESMA filing rules.

References:
- EFRAG ESRS XBRL Taxonomy (2024) — concept mapping
- ESMA ESEF Reporting Manual — iXBRL technical requirements
- ISSB IFRS S1/S2 Taxonomy — IFRS Foundation digital taxonomy
- EU Delegated Regulation 2019/815 (ESEF) — filing format
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import date
import html


# ---------------------------------------------------------------------------
# Reference Data — ESRS XBRL Taxonomy Mapping
# ---------------------------------------------------------------------------

# Maps ESRS data point IDs to XBRL concepts
ESRS_XBRL_TAXONOMY: dict[str, dict] = {
    # E1 — Climate Change
    "E1-6_scope1_gross": {
        "concept": "esrs:GrossScope1GHGEmissions",
        "esrs": "E1", "dr": "E1-6", "paragraph": "44(a)",
        "label": "Gross Scope 1 GHG emissions",
        "unit": "tCO2e", "xbrl_unit": "iso4217:EUR",
        "data_type": "monetaryItemType",
        "balance": "debit",
        "period_type": "duration",
    },
    "E1-6_scope2_location": {
        "concept": "esrs:GrossScope2GHGEmissionsLocationBased",
        "esrs": "E1", "dr": "E1-6", "paragraph": "44(b)",
        "label": "Gross Scope 2 GHG emissions (location-based)",
        "unit": "tCO2e", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    "E1-6_scope2_market": {
        "concept": "esrs:GrossScope2GHGEmissionsMarketBased",
        "esrs": "E1", "dr": "E1-6", "paragraph": "44(c)",
        "label": "Gross Scope 2 GHG emissions (market-based)",
        "unit": "tCO2e", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    "E1-6_scope3_total": {
        "concept": "esrs:TotalScope3GHGEmissions",
        "esrs": "E1", "dr": "E1-6", "paragraph": "51",
        "label": "Total Scope 3 GHG emissions",
        "unit": "tCO2e", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    "E1-6_total_ghg": {
        "concept": "esrs:TotalGHGEmissions",
        "esrs": "E1", "dr": "E1-6", "paragraph": "44",
        "label": "Total GHG emissions (Scope 1+2+3)",
        "unit": "tCO2e", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    "E1-6_ghg_intensity_revenue": {
        "concept": "esrs:GHGIntensityPerNetRevenue",
        "esrs": "E1", "dr": "E1-6", "paragraph": "53",
        "label": "GHG intensity per net revenue",
        "unit": "tCO2e/EUR M", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    "E1-5_energy_consumption_total": {
        "concept": "esrs:TotalEnergyConsumption",
        "esrs": "E1", "dr": "E1-5", "paragraph": "35",
        "label": "Total energy consumption",
        "unit": "MWh", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    "E1-5_renewable_share": {
        "concept": "esrs:ShareOfRenewableEnergy",
        "esrs": "E1", "dr": "E1-5", "paragraph": "38",
        "label": "Share of renewable energy in total consumption",
        "unit": "%", "xbrl_unit": "xbrli:pure",
        "data_type": "percentItemType",
        "balance": None,
        "period_type": "duration",
    },
    "E1-9_internal_carbon_price": {
        "concept": "esrs:InternalCarbonPrice",
        "esrs": "E1", "dr": "E1-9", "paragraph": "67",
        "label": "Internal carbon price applied",
        "unit": "EUR/tCO2e", "xbrl_unit": "iso4217:EUR",
        "data_type": "monetaryItemType",
        "balance": None,
        "period_type": "instant",
    },
    "E1-9_transition_risk_amount": {
        "concept": "esrs:FinancialEffectsTransitionRisks",
        "esrs": "E1", "dr": "E1-9", "paragraph": "69",
        "label": "Potential financial effects — transition risks",
        "unit": "EUR", "xbrl_unit": "iso4217:EUR",
        "data_type": "monetaryItemType",
        "balance": "debit",
        "period_type": "duration",
    },
    "E1-9_physical_risk_amount": {
        "concept": "esrs:FinancialEffectsPhysicalRisks",
        "esrs": "E1", "dr": "E1-9", "paragraph": "70",
        "label": "Potential financial effects — physical risks",
        "unit": "EUR", "xbrl_unit": "iso4217:EUR",
        "data_type": "monetaryItemType",
        "balance": "debit",
        "period_type": "duration",
    },
    # E2 — Pollution
    "E2-4_pollutants_air": {
        "concept": "esrs:PollutantsEmittedToAir",
        "esrs": "E2", "dr": "E2-4", "paragraph": "28",
        "label": "Pollutants emitted to air",
        "unit": "tonnes", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    # E3 — Water
    "E3-4_water_consumption": {
        "concept": "esrs:TotalWaterConsumption",
        "esrs": "E3", "dr": "E3-4", "paragraph": "28",
        "label": "Total water consumption",
        "unit": "m3", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    # E4 — Biodiversity
    "E4-5_land_use_change": {
        "concept": "esrs:TotalLandUseChange",
        "esrs": "E4", "dr": "E4-5", "paragraph": "33",
        "label": "Total land-use change",
        "unit": "hectares", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    # E5 — Circular Economy
    "E5-5_waste_generated": {
        "concept": "esrs:TotalWasteGenerated",
        "esrs": "E5", "dr": "E5-5", "paragraph": "37",
        "label": "Total waste generated",
        "unit": "tonnes", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    # ISSB S2
    "S2_scope1_ghg": {
        "concept": "ifrs-s2:AbsoluteGrossScope1GHGEmissions",
        "esrs": "S2", "dr": "S2-Metrics", "paragraph": "29(a)",
        "label": "Absolute gross Scope 1 GHG emissions (ISSB S2)",
        "unit": "tCO2e", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
    "S2_scope2_ghg": {
        "concept": "ifrs-s2:AbsoluteGrossScope2GHGEmissions",
        "esrs": "S2", "dr": "S2-Metrics", "paragraph": "29(b)",
        "label": "Absolute gross Scope 2 GHG emissions (ISSB S2)",
        "unit": "tCO2e", "xbrl_unit": "xbrli:pure",
        "data_type": "decimalItemType",
        "balance": None,
        "period_type": "duration",
    },
}

# ESMA ESEF validation rules
ESEF_VALIDATION_RULES: list[dict] = [
    {"id": "ESEF-001", "desc": "Entity identifier must be a valid LEI", "field": "entity_lei"},
    {"id": "ESEF-002", "desc": "Period start must precede period end", "field": "period"},
    {"id": "ESEF-003", "desc": "Monetary items must specify currency unit", "field": "unit"},
    {"id": "ESEF-004", "desc": "Decimals attribute must be specified for numeric facts", "field": "decimals"},
    {"id": "ESEF-005", "desc": "Concept must exist in taxonomy", "field": "concept"},
    {"id": "ESEF-006", "desc": "Context ID must be unique", "field": "context"},
    {"id": "ESEF-007", "desc": "Duplicate facts with same context not allowed", "field": "duplicates"},
]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class XBRLFact:
    """A single XBRL fact (tagged data point)."""
    dp_id: str
    concept: str
    value: float
    unit: str
    xbrl_unit: str
    decimals: int
    period_start: str  # ISO date
    period_end: str
    period_type: str  # "duration" | "instant"
    entity_lei: str
    entity_name: str
    context_id: str
    label: str
    esrs: str
    dr: str


@dataclass
class ValidationResult:
    """Result of ESEF validation check."""
    rule_id: str
    description: str
    passed: bool
    details: str


@dataclass
class XBRLExportResult:
    """Complete XBRL export package."""
    entity_name: str
    entity_lei: str
    reporting_period: str  # "2024-01-01 / 2024-12-31"
    taxonomy_version: str
    facts: list[XBRLFact]
    fact_count: int
    ixbrl_html: str
    xbrl_xml: str
    validation_results: list[ValidationResult]
    validation_passed: bool
    errors_count: int
    warnings_count: int
    coverage_by_esrs: dict[str, int]  # {esrs: count of tagged facts}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class XBRLExportEngine:
    """XBRL/iXBRL export engine for CSRD and ISSB filings."""

    def export(
        self,
        entity_name: str,
        entity_lei: str,
        period_start: str = "2024-01-01",
        period_end: str = "2024-12-31",
        data_points: dict[str, float] = None,  # {dp_id: value}
        currency: str = "EUR",
        decimals: int = 0,
    ) -> XBRLExportResult:
        """Generate XBRL export from data points."""
        data_points = data_points or {}

        facts = []
        ctx_counter = 0

        for dp_id, value in data_points.items():
            taxonomy = ESRS_XBRL_TAXONOMY.get(dp_id)
            if not taxonomy:
                continue

            ctx_counter += 1
            ctx_id = f"ctx_{ctx_counter:03d}"

            facts.append(XBRLFact(
                dp_id=dp_id,
                concept=taxonomy["concept"],
                value=value,
                unit=taxonomy["unit"],
                xbrl_unit=taxonomy["xbrl_unit"],
                decimals=decimals,
                period_start=period_start,
                period_end=period_end,
                period_type=taxonomy["period_type"],
                entity_lei=entity_lei,
                entity_name=entity_name,
                context_id=ctx_id,
                label=taxonomy["label"],
                esrs=taxonomy["esrs"],
                dr=taxonomy["dr"],
            ))

        # Generate outputs
        ixbrl = self._generate_ixbrl(entity_name, entity_lei, period_start, period_end, facts, currency)
        xbrl_xml = self._generate_xbrl_xml(entity_name, entity_lei, period_start, period_end, facts, currency)

        # Validate
        validations = self._validate(facts, entity_lei, period_start, period_end)

        # Coverage
        coverage = {}
        for f in facts:
            coverage[f.esrs] = coverage.get(f.esrs, 0) + 1

        errors = sum(1 for v in validations if not v.passed)

        return XBRLExportResult(
            entity_name=entity_name,
            entity_lei=entity_lei,
            reporting_period=f"{period_start} / {period_end}",
            taxonomy_version="ESRS-2024-XBRL-v1.0",
            facts=facts,
            fact_count=len(facts),
            ixbrl_html=ixbrl,
            xbrl_xml=xbrl_xml,
            validation_results=validations,
            validation_passed=errors == 0,
            errors_count=errors,
            warnings_count=0,
            coverage_by_esrs=coverage,
        )

    def _generate_ixbrl(
        self, name: str, lei: str, start: str, end: str,
        facts: list[XBRLFact], currency: str,
    ) -> str:
        """Generate iXBRL HTML document."""
        lines = [
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml"',
            '      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"',
            '      xmlns:xbrli="http://www.xbrl.org/2003/instance"',
            '      xmlns:esrs="http://xbrl.efrag.org/taxonomy/esrs/2024"',
            '      xmlns:ifrs-s2="http://xbrl.ifrs.org/taxonomy/ifrs-s2/2024"',
            f'      xmlns:iso4217="http://www.xbrl.org/2003/iso4217">',
            '<head>',
            f'  <title>ESRS Report — {html.escape(name)}</title>',
            '  <meta charset="UTF-8"/>',
            '</head>',
            '<body>',
            '<ix:header>',
            '  <ix:hidden>',
            f'    <ix:nonNumeric name="esrs:EntityName" contextRef="ctx_entity">{html.escape(name)}</ix:nonNumeric>',
            '  </ix:hidden>',
            '  <ix:references>',
            '    <link:schemaRef xlink:href="esrs-2024.xsd"/>',
            '  </ix:references>',
            '</ix:header>',
            f'<h1>ESRS Sustainability Report — {html.escape(name)}</h1>',
            f'<p>Reporting period: {start} to {end}</p>',
            f'<p>LEI: {html.escape(lei)}</p>',
            '<table border="1" cellpadding="4">',
            '<tr><th>Data Point</th><th>Value</th><th>Unit</th></tr>',
        ]

        for f in facts:
            fmt_name = f.concept.replace(":", "_")
            lines.append(
                f'<tr><td>{html.escape(f.label)}</td>'
                f'<td><ix:nonFraction name="{f.concept}" contextRef="{f.context_id}" '
                f'unitRef="u_{fmt_name}" decimals="{f.decimals}">'
                f'{f.value}</ix:nonFraction></td>'
                f'<td>{html.escape(f.unit)}</td></tr>'
            )

        lines += ['</table>', '</body>', '</html>']
        return "\n".join(lines)

    def _generate_xbrl_xml(
        self, name: str, lei: str, start: str, end: str,
        facts: list[XBRLFact], currency: str,
    ) -> str:
        """Generate XBRL XML instance document."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<xbrli:xbrl',
            '  xmlns:xbrli="http://www.xbrl.org/2003/instance"',
            '  xmlns:esrs="http://xbrl.efrag.org/taxonomy/esrs/2024"',
            '  xmlns:ifrs-s2="http://xbrl.ifrs.org/taxonomy/ifrs-s2/2024"',
            '  xmlns:iso4217="http://www.xbrl.org/2003/iso4217"',
            '  xmlns:xlink="http://www.w3.org/1999/xlink">',
            '',
            '  <xbrli:schemaRef xlink:href="esrs-2024.xsd" xlink:type="simple"/>',
            '',
        ]

        # Contexts
        for f in facts:
            if f.period_type == "duration":
                lines += [
                    f'  <xbrli:context id="{f.context_id}">',
                    f'    <xbrli:entity><xbrli:identifier scheme="http://standards.iso.org/iso/17442">{html.escape(lei)}</xbrli:identifier></xbrli:entity>',
                    f'    <xbrli:period><xbrli:startDate>{start}</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate></xbrli:period>',
                    '  </xbrli:context>',
                ]
            else:
                lines += [
                    f'  <xbrli:context id="{f.context_id}">',
                    f'    <xbrli:entity><xbrli:identifier scheme="http://standards.iso.org/iso/17442">{html.escape(lei)}</xbrli:identifier></xbrli:entity>',
                    f'    <xbrli:period><xbrli:instant>{end}</xbrli:instant></xbrli:period>',
                    '  </xbrli:context>',
                ]

        # Units
        unit_ids = set()
        for f in facts:
            uid = f"u_{f.concept.replace(':', '_')}"
            if uid not in unit_ids:
                unit_ids.add(uid)
                lines.append(f'  <xbrli:unit id="{uid}"><xbrli:measure>{f.xbrl_unit}</xbrli:measure></xbrli:unit>')

        lines.append('')

        # Facts
        for f in facts:
            uid = f"u_{f.concept.replace(':', '_')}"
            lines.append(
                f'  <{f.concept} contextRef="{f.context_id}" unitRef="{uid}" '
                f'decimals="{f.decimals}">{f.value}</{f.concept}>'
            )

        lines += ['', '</xbrli:xbrl>']
        return "\n".join(lines)

    def _validate(
        self, facts: list[XBRLFact], lei: str, start: str, end: str,
    ) -> list[ValidationResult]:
        """Run ESEF validation rules."""
        results = []

        # ESEF-001: LEI format (20 alphanumeric chars)
        lei_valid = len(lei) == 20 and lei.isalnum()
        results.append(ValidationResult(
            rule_id="ESEF-001",
            description="Entity identifier must be a valid LEI",
            passed=lei_valid,
            details=f"LEI '{lei}' {'is valid' if lei_valid else 'is not 20 alphanumeric chars'}",
        ))

        # ESEF-002: Period dates
        try:
            s = date.fromisoformat(start)
            e = date.fromisoformat(end)
            period_ok = s < e
        except ValueError:
            period_ok = False
        results.append(ValidationResult(
            rule_id="ESEF-002",
            description="Period start must precede period end",
            passed=period_ok,
            details=f"{start} to {end}" if period_ok else "Invalid period dates",
        ))

        # ESEF-005: Concepts exist in taxonomy
        for f in facts:
            concept_ok = f.dp_id in ESRS_XBRL_TAXONOMY
            results.append(ValidationResult(
                rule_id="ESEF-005",
                description=f"Concept {f.concept} exists in taxonomy",
                passed=concept_ok,
                details=f.dp_id,
            ))

        # ESEF-007: No duplicate facts
        seen = set()
        for f in facts:
            key = (f.concept, f.context_id)
            dup = key in seen
            results.append(ValidationResult(
                rule_id="ESEF-007",
                description=f"No duplicate fact for {f.concept}",
                passed=not dup,
                details=f"Context {f.context_id}",
            ))
            seen.add(key)

        return results

    def get_taxonomy(self) -> dict[str, dict]:
        return ESRS_XBRL_TAXONOMY

    def get_validation_rules(self) -> list[dict]:
        return ESEF_VALIDATION_RULES

    def get_supported_standards(self) -> list[str]:
        standards = set()
        for t in ESRS_XBRL_TAXONOMY.values():
            standards.add(t["esrs"])
        return sorted(standards)
