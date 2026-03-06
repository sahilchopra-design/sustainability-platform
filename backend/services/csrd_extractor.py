"""
CSRD / ESRS PDF extraction engine.

Parses sustainability reports (PDFs) and extracts ESRS-coded KPI values using:
  1. pdfplumber text + table extraction
  2. Regex pattern matching against 35+ ESRS indicator definitions
  3. Confidence scoring (0.0–1.0)
  4. Mandatory gap detection

Returns a structured dict with extracted KPIs, mandatory gaps, and entity metadata.
"""

import re
import io
import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not installed. Run: pip install pdfplumber")


# ---------------------------------------------------------------------------
# ESRS Indicator catalog — 36 KPIs covering E1–E5, S1–S4, G1, EU Taxonomy
# keys: description, unit, standard, mandatory, patterns, unit_conv
# ---------------------------------------------------------------------------
ESRS_INDICATORS: Dict[str, Dict] = {

    # ===== ESRS E1: Climate Change =====
    "E1-5.EnergyConsumptionTotal": {
        "description": "Total energy consumption",
        "unit": "MWh",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"total\s+energy\s+consumption[^0-9]{0,100}([\d,\.]+)\s*(TWh|GWh|MWh|PJ|TJ|GJ)",
            r"energy\s+consumption[^0-9]{0,80}([\d,\.]+)\s*(TWh|GWh|MWh)",
            r"([\d,\.]+)\s*(TWh|GWh|MWh)[^a-z]{0,40}energy\s+consumption",
        ],
        "unit_conv": {"TWh": 1e6, "GWh": 1e3, "MWh": 1.0, "PJ": 277778.0, "TJ": 277.78, "GJ": 0.27778},
    },
    "E1-5.EnergyConsumptionRenewable": {
        "description": "Energy from renewable sources",
        "unit": "MWh",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"renewable\s+(?:energy|sources?)[^0-9]{0,80}([\d,\.]+)\s*(TWh|GWh|MWh)",
            r"([\d,\.]+)\s*(TWh|GWh|MWh)[^a-z]{0,40}renewable",
        ],
        "unit_conv": {"TWh": 1e6, "GWh": 1e3, "MWh": 1.0},
    },
    "E1-5.RenewableEnergyPct": {
        "description": "% of total energy from renewables",
        "unit": "%",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"renewable\s+energy\s+(?:share|percentage)[^0-9]{0,80}([\d,\.]+)\s*%",
            r"([\d,\.]+)\s*%\s+(?:of\s+(?:energy|electricity)\s+from\s+)?renewables?",
        ],
        "unit_conv": {},
    },
    "E1-6.Scope1GHG": {
        "description": "Gross Scope 1 GHG emissions",
        "unit": "tCO2e",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"scope\s*1\s*(?:ghg\s+)?emissions?[^0-9]{0,100}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?|Mt|kt)\b",
            r"gross\s+scope\s*1[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"direct\s+(?:ghg\s+)?emissions?[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
        ],
        "unit_conv": {
            "MtCO2e": 1e6, "ktCO2e": 1e3, "tCO2e": 1.0,
            "MtCO2": 1e6, "ktCO2": 1e3, "tCO2": 1.0, "Mt": 1e6, "kt": 1e3,
        },
    },
    "E1-6.Scope2GHGMarketBased": {
        "description": "Gross Scope 2 GHG emissions (market-based)",
        "unit": "tCO2e",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"market.based[^0-9]{0,80}scope\s*2[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"scope\s*2[^0-9]{0,40}market.based[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"scope\s*2\s*(?:ghg\s+)?emissions?[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
        ],
        "unit_conv": {"MtCO2e": 1e6, "ktCO2e": 1e3, "tCO2e": 1.0},
    },
    "E1-6.Scope2GHGLocationBased": {
        "description": "Gross Scope 2 GHG emissions (location-based)",
        "unit": "tCO2e",
        "standard": "E1",
        "mandatory": False,
        "patterns": [
            r"location.based[^0-9]{0,80}scope\s*2[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"scope\s*2[^0-9]{0,40}location.based[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
        ],
        "unit_conv": {"MtCO2e": 1e6, "ktCO2e": 1e3, "tCO2e": 1.0},
    },
    "E1-6.Scope3GHGTotal": {
        "description": "Gross Scope 3 GHG emissions (total)",
        "unit": "tCO2e",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"total\s+scope\s*3[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"scope\s*3\s*(?:total|all\s+categories?)[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"scope\s*3\s*(?:ghg\s+)?emissions?[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
        ],
        "unit_conv": {"MtCO2e": 1e6, "ktCO2e": 1e3, "tCO2e": 1.0},
    },
    "E1-6.TotalGHGEmissions": {
        "description": "Total GHG emissions (Scope 1+2+3)",
        "unit": "tCO2e",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"total\s+(?:ghg|greenhouse\s+gas)\s+emissions?[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"overall\s+(?:ghg|carbon)\s+footprint[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
        ],
        "unit_conv": {"MtCO2e": 1e6, "ktCO2e": 1e3, "tCO2e": 1.0},
    },
    "E1-6.GHGIntensityRevenue": {
        "description": "GHG emissions intensity per unit revenue",
        "unit": "tCO2e/MEUR",
        "standard": "E1",
        "mandatory": True,
        "patterns": [
            r"(?:ghg|carbon|emissions?)\s+intensity[^0-9]{0,80}([\d,\.]+)\s*(?:tCO2e/EUR|tCO2e/M€|tCO2e/MEUR)",
            r"emissions?\s+intensity[^0-9]{0,80}([\d,\.]+)",
        ],
        "unit_conv": {},
    },
    "E1-7.GHGRemovals": {
        "description": "GHG removals and carbon storage",
        "unit": "tCO2e",
        "standard": "E1",
        "mandatory": False,
        "patterns": [
            r"(?:ghg\s+)?removals?[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"carbon\s+removal[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
        ],
        "unit_conv": {"MtCO2e": 1e6, "ktCO2e": 1e3, "tCO2e": 1.0},
    },
    "E1-4.SBTiTarget": {
        "description": "Science-Based Target validated by SBTi",
        "unit": "boolean",
        "standard": "E1",
        "mandatory": False,
        "patterns": [
            r"science.based\s+target[^a-z]{0,80}(yes|validated|committed|approved|in\s+place)",
            r"\bSBTi\b[^a-z]{0,80}(yes|validated|committed|approved|target)",
        ],
        "unit_conv": {},
    },

    # ===== ESRS E3: Water =====
    "E3-4.WaterConsumption": {
        "description": "Total water consumption",
        "unit": "m3",
        "standard": "E3",
        "mandatory": True,
        "patterns": [
            r"total\s+water\s+consumption[^0-9]{0,100}([\d,\.]+)\s*(m3|m³|ML|GL|Mm3)",
            r"water\s+consumption[^0-9]{0,80}([\d,\.]+)\s*(m3|m³|ML|GL)",
        ],
        "unit_conv": {"m3": 1.0, "m³": 1.0, "ML": 1000.0, "GL": 1e6, "Mm3": 1e6},
    },
    "E3-4.WaterWithdrawal": {
        "description": "Total water withdrawal",
        "unit": "m3",
        "standard": "E3",
        "mandatory": True,
        "patterns": [
            r"water\s+withdrawal[^0-9]{0,80}([\d,\.]+)\s*(m3|m³|ML|GL)",
            r"water\s+(?:abstraction|intake)[^0-9]{0,80}([\d,\.]+)\s*(m3|m³|ML)",
        ],
        "unit_conv": {"m3": 1.0, "m³": 1.0, "ML": 1000.0, "GL": 1e6},
    },
    "E3-4.WaterRecycledPct": {
        "description": "% water recycled / reused",
        "unit": "%",
        "standard": "E3",
        "mandatory": False,
        "patterns": [
            r"water\s+(?:recycled|reused)[^0-9]{0,80}([\d,\.]+)\s*%",
            r"([\d,\.]+)\s*%\s+(?:of\s+)?water\s+(?:recycled|reused)",
        ],
        "unit_conv": {},
    },

    # ===== ESRS E5: Resource Use and Circular Economy =====
    "E5-5.WasteGeneratedTotal": {
        "description": "Total waste generated",
        "unit": "tonnes",
        "standard": "E5",
        "mandatory": True,
        "patterns": [
            r"total\s+waste\s+(?:generated|produced)[^0-9]{0,80}([\d,\.]+)\s*(?:tonnes?|t\b|kt\b|metric\s+tons?)",
            r"waste\s+generated[^0-9]{0,80}([\d,\.]+)\s*(?:tonnes?|t\b|kt\b)",
        ],
        "unit_conv": {"tonnes": 1.0, "t": 1.0, "kt": 1000.0, "metric tons": 1.0},
    },
    "E5-5.WasteHazardous": {
        "description": "Hazardous waste generated",
        "unit": "tonnes",
        "standard": "E5",
        "mandatory": False,
        "patterns": [
            r"hazardous\s+waste[^0-9]{0,80}([\d,\.]+)\s*(?:tonnes?|t\b|kt\b)",
        ],
        "unit_conv": {"tonnes": 1.0, "t": 1.0, "kt": 1000.0},
    },
    "E5-5.WasteRecycledPct": {
        "description": "% waste recycled or reused",
        "unit": "%",
        "standard": "E5",
        "mandatory": False,
        "patterns": [
            r"(?:waste\s+)?recycling\s+rate[^0-9]{0,80}([\d,\.]+)\s*%",
            r"([\d,\.]+)\s*%\s+(?:of\s+)?waste\s+(?:recycled|diverted)",
        ],
        "unit_conv": {},
    },

    # ===== ESRS S1: Own Workforce =====
    "S1-7.TotalEmployeesHeadcount": {
        "description": "Total employees (headcount)",
        "unit": "headcount",
        "standard": "S1",
        "mandatory": True,
        "patterns": [
            r"total\s+(?:number\s+of\s+)?employees?[^0-9]{0,80}([\d,\.]+)",
            r"(?:number|count)\s+of\s+employees?[^0-9]{0,80}([\d,\.]+)",
            r"headcount[^0-9]{0,80}([\d,\.]+)",
            r"workforce\s+(?:of|:)[^0-9]{0,40}([\d,\.]+)",
        ],
        "unit_conv": {},
    },
    "S1-7.FemaleEmployeesPct": {
        "description": "% female employees",
        "unit": "%",
        "standard": "S1",
        "mandatory": True,
        "patterns": [
            r"(?:female|women)\s+employees?[^0-9]{0,80}([\d,\.]+)\s*%",
            r"women\s+in\s+(?:the\s+)?(?:workforce|total)[^0-9]{0,80}([\d,\.]+)\s*%",
            r"([\d,\.]+)\s*%\s+(?:female|women)",
        ],
        "unit_conv": {},
    },
    "S1-7.FemaleManagementPct": {
        "description": "% women in management / leadership",
        "unit": "%",
        "standard": "S1",
        "mandatory": True,
        "patterns": [
            r"women\s+in\s+(?:senior\s+)?(?:management|leadership)[^0-9]{0,80}([\d,\.]+)\s*%",
            r"female\s+(?:senior\s+)?(?:managers?|leaders?)[^0-9]{0,80}([\d,\.]+)\s*%",
        ],
        "unit_conv": {},
    },
    "S1-7.PermanentEmployeesPct": {
        "description": "% employees on permanent contracts",
        "unit": "%",
        "standard": "S1",
        "mandatory": False,
        "patterns": [
            r"permanent\s+(?:contract\s+)?employees?[^0-9]{0,80}([\d,\.]+)\s*%",
            r"([\d,\.]+)\s*%\s+permanent\s+(?:contract\s+)?employees?",
        ],
        "unit_conv": {},
    },
    "S1-11.TRIR": {
        "description": "Total Recordable Injury Rate",
        "unit": "per 200k hours",
        "standard": "S1",
        "mandatory": True,
        "patterns": [
            r"(?:total\s+)?recordable\s+injur(?:y|ies)\s+rate[^0-9]{0,80}([\d,\.]+)",
            r"\bTRIR\b[^0-9]{0,40}([\d,\.]+)",
            r"(?:total\s+)?injury\s+rate[^0-9]{0,80}([\d,\.]+)",
        ],
        "unit_conv": {},
    },
    "S1-11.LTIR": {
        "description": "Lost Time Injury Rate",
        "unit": "per 200k hours",
        "standard": "S1",
        "mandatory": True,
        "patterns": [
            r"lost.time\s+injur(?:y|ies)\s+(?:frequency\s+)?rate[^0-9]{0,80}([\d,\.]+)",
            r"\bLTIR\b[^0-9]{0,40}([\d,\.]+)",
            r"\bLTIFR?\b[^0-9]{0,40}([\d,\.]+)",
        ],
        "unit_conv": {},
    },
    "S1-11.Fatalities": {
        "description": "Work-related fatalities",
        "unit": "count",
        "standard": "S1",
        "mandatory": True,
        "patterns": [
            r"(?:work.related\s+)?fatal(?:ities?|ity)[^0-9]{0,80}(\d+)",
            r"deaths?\s+(?:at\s+work|in\s+the\s+workplace)[^0-9]{0,80}(\d+)",
            r"(\d+)\s+(?:work.related\s+)?fatal(?:ities?|ity)",
        ],
        "unit_conv": {},
    },
    "S1-16.GenderPayGapPct": {
        "description": "Gender pay gap (%)",
        "unit": "%",
        "standard": "S1",
        "mandatory": True,
        "patterns": [
            r"gender\s+pay\s+gap[^0-9]{0,80}([\d,\.]+)\s*%",
            r"pay\s+gap[^0-9]{0,40}(?:gender|male.female|men.women)[^0-9]{0,80}([\d,\.]+)\s*%",
        ],
        "unit_conv": {},
    },

    # ===== ESRS G1: Business Conduct =====
    "G1-4.AntiCorruptionTrainingPct": {
        "description": "% employees trained on anti-corruption",
        "unit": "%",
        "standard": "G1",
        "mandatory": True,
        "patterns": [
            r"anti.corruption\s+(?:and\s+anti.bribery\s+)?training[^0-9]{0,80}([\d,\.]+)\s*%",
            r"(?:employees?|staff)\s+(?:trained\s+on\s+)?anti.corruption[^0-9]{0,80}([\d,\.]+)\s*%",
            r"([\d,\.]+)\s*%\s+(?:of\s+employees?\s+trained\s+on\s+)?anti.corruption",
        ],
        "unit_conv": {},
    },
    "G1-4.CorruptionIncidents": {
        "description": "Confirmed incidents of corruption / bribery",
        "unit": "count",
        "standard": "G1",
        "mandatory": True,
        "patterns": [
            r"confirmed\s+(?:incidents?\s+of\s+)?corruption[^0-9]{0,80}(\d+)",
            r"bribery\s+(?:and\s+corruption\s+)?incidents?[^0-9]{0,80}(\d+)",
        ],
        "unit_conv": {},
    },

    # ===== ESRS2: General Disclosures =====
    "ESRS2.TotalRevenueMEUR": {
        "description": "Net revenue / net turnover",
        "unit": "MEUR",
        "standard": "ESRS2",
        "mandatory": True,
        "patterns": [
            r"(?:net\s+)?(?:revenue|turnover)[^0-9]{0,80}([\d,\.]+)\s*(?:M€|MEUR|EUR\s*m|€\s*m)",
            r"(?:net\s+)?(?:revenue|turnover)[^0-9]{0,80}([\d,\.]+)\s*(?:€\s*billion|EUR\s*bn|€\s*bn)",
            r"revenue[^0-9]{0,40}€\s*([\d,\.]+)\s*(?:billion|m)\b",
        ],
        "unit_conv": {"MEUR": 1.0, "M€": 1.0, "EUR m": 1.0, "€ m": 1.0,
                      "€ billion": 1000.0, "EUR bn": 1000.0, "€ bn": 1000.0},
    },
    "ESRS2.BalanceSheetMEUR": {
        "description": "Total assets / balance sheet total",
        "unit": "MEUR",
        "standard": "ESRS2",
        "mandatory": False,
        "patterns": [
            r"total\s+assets?[^0-9]{0,80}([\d,\.]+)\s*(?:M€|MEUR|EUR\s*m|€\s*m|€\s*bn|EUR\s*bn)",
            r"balance\s+sheet\s+total[^0-9]{0,80}([\d,\.]+)",
        ],
        "unit_conv": {"MEUR": 1.0, "M€": 1.0, "EUR m": 1.0, "€ m": 1.0,
                      "€ bn": 1000.0, "EUR bn": 1000.0},
    },
    "ESRS2.EmployeeCountFTE": {
        "description": "Total employees (FTE)",
        "unit": "FTE",
        "standard": "ESRS2",
        "mandatory": True,
        "patterns": [
            r"FTE[^0-9]{0,80}([\d,\.]+)",
            r"full.time\s+equivalent[^0-9]{0,80}([\d,\.]+)",
            r"([\d,\.]+)\s+FTE",
        ],
        "unit_conv": {},
    },

    # ===== EU Taxonomy =====
    "EUTaxonomy.AlignedRevenuePct": {
        "description": "% revenue aligned with EU Taxonomy",
        "unit": "%",
        "standard": "EU_TAXONOMY",
        "mandatory": True,
        "patterns": [
            r"taxonomy.aligned\s+(?:revenue|turnover)[^0-9]{0,80}([\d,\.]+)\s*%",
            r"(?:revenue|turnover)[^0-9]{0,40}taxonomy.aligned[^0-9]{0,80}([\d,\.]+)\s*%",
            r"eu\s+taxonomy[^0-9]{0,40}(?:revenue|turnover)[^0-9]{0,80}([\d,\.]+)\s*%",
            r"taxonomy\s+alignment[^0-9]{0,40}(?:revenue|turnover)[^0-9]{0,80}([\d,\.]+)\s*%",
        ],
        "unit_conv": {},
    },
    "EUTaxonomy.AlignedCapexPct": {
        "description": "% CapEx aligned with EU Taxonomy",
        "unit": "%",
        "standard": "EU_TAXONOMY",
        "mandatory": True,
        "patterns": [
            r"taxonomy.aligned\s+capex[^0-9]{0,80}([\d,\.]+)\s*%",
            r"capex[^0-9]{0,40}taxonomy.aligned[^0-9]{0,80}([\d,\.]+)\s*%",
            r"eu\s+taxonomy[^0-9]{0,40}capex[^0-9]{0,80}([\d,\.]+)\s*%",
        ],
        "unit_conv": {},
    },
    "EUTaxonomy.AlignedOpexPct": {
        "description": "% OpEx aligned with EU Taxonomy",
        "unit": "%",
        "standard": "EU_TAXONOMY",
        "mandatory": False,
        "patterns": [
            r"taxonomy.aligned\s+opex[^0-9]{0,80}([\d,\.]+)\s*%",
            r"eu\s+taxonomy[^0-9]{0,40}opex[^0-9]{0,80}([\d,\.]+)\s*%",
        ],
        "unit_conv": {},
    },

    # ===== Financial Institution specific (PCAF / SFDR) =====
    "FI.FinancedEmissions": {
        "description": "Financed emissions (Scope 3 Category 15)",
        "unit": "tCO2e",
        "standard": "PCAF",
        "mandatory": False,
        "patterns": [
            r"financed\s+emissions?[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"(?:scope\s*3\s+)?category\s*15[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
            r"portfolio\s+(?:carbon\s+)?footprint[^0-9]{0,80}([\d,\.]+)\s*(MtCO2e?|ktCO2e?|tCO2e?)",
        ],
        "unit_conv": {"MtCO2e": 1e6, "ktCO2e": 1e3, "tCO2e": 1.0},
    },
    "FI.WACI": {
        "description": "Weighted Average Carbon Intensity",
        "unit": "tCO2e/MEUR",
        "standard": "PCAF",
        "mandatory": False,
        "patterns": [
            r"\bWACI\b[^0-9]{0,80}([\d,\.]+)\s*(?:tCO2e/EUR|tCO2e/MEUR|tCO2e/€M)",
            r"weighted.average\s+carbon\s+intensity[^0-9]{0,80}([\d,\.]+)",
        ],
        "unit_conv": {},
    },
}

MANDATORY_INDICATORS = [k for k, v in ESRS_INDICATORS.items() if v.get("mandatory", False)]


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------
class CSRDExtractor:
    """Extract ESRS KPI values from ESG/Sustainability PDF reports."""

    def __init__(self):
        self.indicators = ESRS_INDICATORS
        self.mandatory = MANDATORY_INDICATORS

    # -----------------------------------------------------------------------
    # Public entry points
    # -----------------------------------------------------------------------

    def extract_from_bytes(self, pdf_bytes: bytes, filename: str = "report.pdf") -> dict:
        """
        Extract ESRS KPIs from raw PDF bytes.

        Returns:
            {
              "entity_name": str | None,
              "reporting_year": int | None,
              "extracted_kpis": {indicator_code: {...}},
              "mandatory_gaps": [indicator_code, ...],
              "total_pages": int,
              "extraction_timestamp": ISO str,
              "pdf_available": bool,
              "errors": [str],
              "validation_summary": {...}
            }
        """
        result = {
            "entity_name": None,
            "reporting_year": None,
            "extracted_kpis": {},
            "mandatory_gaps": [],
            "total_pages": 0,
            "total_text_length": 0,
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "pdf_available": _PDFPLUMBER_AVAILABLE,
            "errors": [],
            "filename": filename,
        }

        if not _PDFPLUMBER_AVAILABLE:
            result["errors"].append(
                "pdfplumber not installed. Run: pip install pdfplumber"
            )
            result["mandatory_gaps"] = self.mandatory[:]
            result["validation_summary"] = self._build_validation_summary(result)
            return result

        try:
            full_text, pages_text, total_pages = self._extract_text(pdf_bytes)
            result["total_pages"] = total_pages
            result["total_text_length"] = len(full_text)

            # Entity and year from cover
            result["entity_name"] = self._detect_entity_name(full_text[:3000], filename)
            result["reporting_year"] = self._detect_reporting_year(full_text[:5000])

            # Run all indicator patterns
            full_text_lower = full_text.lower()
            for indicator_code, config in self.indicators.items():
                match = self._extract_indicator(
                    full_text_lower, full_text, pages_text, indicator_code, config
                )
                if match:
                    result["extracted_kpis"][indicator_code] = match

            # Gaps = mandatory not found
            found = set(result["extracted_kpis"].keys())
            result["mandatory_gaps"] = [c for c in self.mandatory if c not in found]

        except Exception as e:
            logger.exception(f"CSRD extraction failed for {filename}: {e}")
            result["errors"].append(str(e))
            result["mandatory_gaps"] = self.mandatory[:]

        result["validation_summary"] = self._build_validation_summary(result)
        return result

    def extract_from_path(self, pdf_path: str) -> dict:
        """Extract from a file path on disk."""
        with open(pdf_path, "rb") as f:
            return self.extract_from_bytes(f.read(), filename=pdf_path)

    # -----------------------------------------------------------------------
    # PDF text extraction
    # -----------------------------------------------------------------------

    def _extract_text(
        self, pdf_bytes: bytes
    ) -> Tuple[str, List[Tuple[int, str]], int]:
        """
        Extract full text and per-page text.
        Returns (full_text_with_newlines, [(page_num, text), ...], total_pages)
        """
        pages_text: List[Tuple[int, str]] = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            total_pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                # Append table text as space-separated rows
                try:
                    for table in (page.extract_tables() or []):
                        for row in (table or []):
                            if row:
                                row_text = " ".join(
                                    str(c) if c else "" for c in row
                                )
                                page_text += "\n" + row_text
                except Exception:
                    pass
                pages_text.append((page_num, page_text))

        full_text = "\n".join(t for _, t in pages_text)
        return full_text, pages_text, total_pages

    # -----------------------------------------------------------------------
    # Entity / year detection
    # -----------------------------------------------------------------------

    # Well-known company names keyed by lowercase filename fragment
    _KNOWN_ENTITIES = {
        "bnp_paribas": "BNP Paribas",
        "bnp": "BNP Paribas",
        "rabobank": "Rabobank",
        "abn_amro": "ABN AMRO",
        "abn": "ABN AMRO",
        "ing_groep": "ING Group",
        "ing": "ING Group",
        "orsted": "Ørsted",
        "rwe": "RWE Group",
        "engie": "ENGIE",
        "edp": "EDP Energias de Portugal",
        "iberdrola": "Iberdrola",
        "enel": "Enel",
        "totalenergies": "TotalEnergies",
        "shell": "Shell",
        "bp": "BP",
        "hsbc": "HSBC",
        "barclays": "Barclays",
        "lloyds": "Lloyds Banking Group",
        "natwest": "NatWest",
        "deutsche_bank": "Deutsche Bank",
        "commerzbank": "Commerzbank",
        "societe_generale": "Société Générale",
        "bnpp": "BNP Paribas",
        # ── North America ──────────────────────────────────────────────────
        "jpmorgan": "JPMorgan Chase",
        "jp_morgan": "JPMorgan Chase",
        "jpmorganchase": "JPMorgan Chase",
        "goldman_sachs": "Goldman Sachs",
        "goldman": "Goldman Sachs",
        "gs_sustainability": "Goldman Sachs",
        "royal_bank": "Royal Bank of Canada",
        "rbc": "Royal Bank of Canada",
        "rbc_climate": "Royal Bank of Canada",
        # ── India ──────────────────────────────────────────────────────────
        "icici": "ICICI Bank",
        "icici_bank": "ICICI Bank",
        # ── Japan ──────────────────────────────────────────────────────────
        "smbc": "Sumitomo Mitsui Banking Corporation",
        "sumitomo_mitsui": "Sumitomo Mitsui Banking Corporation",
        "smbc_group": "Sumitomo Mitsui Banking Corporation",
        # ── Korea ──────────────────────────────────────────────────────────
        "kb_financial": "KB Financial Group",
        "kb_kookmin": "KB Financial Group",
        "kbfg": "KB Financial Group",
        "shinhan": "Shinhan Financial Group",
        "shinhan_financial": "Shinhan Financial Group",
        "hana_financial": "Hana Financial Group",
        # ── Hong Kong ──────────────────────────────────────────────────────
        "hsbc_hk": "HSBC (Hong Kong)",
        "bochk": "Bank of China (Hong Kong)",
        "bank_of_china_hk": "Bank of China (Hong Kong)",
        "hang_seng": "Hang Seng Bank",
        # ── Taiwan ─────────────────────────────────────────────────────────
        "cathay_financial": "Cathay Financial Holdings",
        "cathay_life": "Cathay Financial Holdings",
        "fubon": "Fubon Financial Holdings",
        "fubon_financial": "Fubon Financial Holdings",
        "ctbc": "CTBC Financial Holding",
        "ctbc_financial": "CTBC Financial Holding",
        "esun": "E.SUN Financial Holdings",
        # ── Infrastructure PE ──────────────────────────────────────────────
        "brookfield_renewable": "Brookfield Renewable Partners",
        "brookfield": "Brookfield Renewable Partners",
        "bep_sustainability": "Brookfield Renewable Partners",
    }

    # Words that should NOT be the first word of an entity name
    _INVALID_LEAD_WORDS = {
        "sustainability", "annual", "esg", "climate", "integrated", "non-financial",
        "at", "in", "with", "the", "our", "this", "for", "from", "as", "by",
        "about", "how", "we", "it", "of", "and", "or", "is", "are", "was",
    }

    def _detect_entity_name(self, cover_text: str, filename: str = "") -> Optional[str]:
        # 1. Filename keyword lookup (most reliable)
        fn_lower = filename.lower().replace(" ", "_").replace("-", "_")
        # Try longest match first
        for key in sorted(self._KNOWN_ENTITIES, key=len, reverse=True):
            if key in fn_lower:
                return self._KNOWN_ENTITIES[key]

        # 2. Regex from PDF cover text — normalise whitespace first
        cover_clean = re.sub(r"\s+", " ", cover_text).strip()

        patterns = [
            # Company name before "Annual/Sustainability/ESG Report"
            r"([A-Z][A-Za-z\s&,\.]{3,60}(?:Group|Inc\.|Corp\.|Ltd\.|PLC|AG|SE|NV|SA|GmbH|Plc|S\.A\.))\s+(?:Sustainability|Annual|ESG|Climate|Integrated)",
            # Company name after "Report by/from ..."
            r"(?:Annual|Sustainability|ESG)\s+Report\s+(?:\d{4}\s+)?(?:by\s+|of\s+)?([A-Z][A-Za-z\s&\.]{3,40})",
            # Company name with legal suffix (no newlines in match)
            r"\b([A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]+){0,4}\s+(?:Group|Inc|Corp|Ltd|PLC|AG|SE|NV|GmbH|Plc|S\.A\.))\b",
        ]
        for p in patterns:
            m = re.search(p, cover_clean)
            if m:
                name = re.sub(r"\s+", " ", m.group(1)).strip()
                lead = name.split()[0].lower() if name else ""
                if (4 <= len(name) <= 80
                        and lead not in self._INVALID_LEAD_WORDS
                        and "\n" not in name):
                    return name
        return None

    def _detect_reporting_year(self, text: str) -> Optional[int]:
        current_year = datetime.utcnow().year
        specific = [
            r"(?:Sustainability|Annual|ESG|Climate)\s+Report\s+(\d{4})",
            r"(?:fiscal|financial|reporting)\s+year\s+(\d{4})",
            r"(?:FY|Year)\s*(\d{4})",
            r"(\d{4})\s+(?:Sustainability|Annual|ESG|Climate)\s+Report",
        ]
        for p in specific:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                yr = int(m.group(1))
                if 2015 <= yr <= current_year + 1:
                    return yr
        # Fallback: most common year in first 3000 chars
        years = [
            int(y) for y in re.findall(r"\b(20\d{2})\b", text[:3000])
            if 2015 <= int(y) <= current_year + 1
        ]
        if years:
            return Counter(years).most_common(1)[0][0]
        return None

    # -----------------------------------------------------------------------
    # Indicator extraction
    # -----------------------------------------------------------------------

    def _extract_indicator(
        self,
        full_text_lower: str,
        full_text_original: str,
        pages_text: List[Tuple[int, str]],
        indicator_code: str,
        config: dict,
    ) -> Optional[dict]:
        """Run all patterns; return highest-confidence match or None."""
        best: Optional[dict] = None
        best_conf = 0.0

        for i, pattern in enumerate(config["patterns"]):
            for m in re.finditer(pattern, full_text_lower, re.IGNORECASE | re.DOTALL):
                groups = m.groups()
                if not groups:
                    continue

                raw_val_str = groups[0]
                raw_unit = groups[1].strip() if len(groups) > 1 and groups[1] else ""

                # Boolean / text patterns
                if config["unit"] == "boolean" and raw_val_str:
                    conf = max(0.3, 0.75 - i * 0.1)
                    if conf > best_conf:
                        best_conf = conf
                        snippet = full_text_original[max(0, m.start() - 50): m.end() + 80]
                        best = {
                            "indicator_code": indicator_code,
                            "numeric_value": None,
                            "text_value": raw_val_str,
                            "unit": config["unit"],
                            "raw_value_str": raw_val_str,
                            "raw_unit": "",
                            "confidence": round(conf, 2),
                            "page_number": self._find_page(m.start(), pages_text),
                            "text_snippet": snippet[:300],
                            "extraction_method": "regex_text",
                        }
                    continue

                numeric = self._parse_numeric(raw_val_str)
                if numeric is None:
                    continue

                # Unit normalization + conversion
                unit_conv = config.get("unit_conv", {})
                multiplier = unit_conv.get(
                    raw_unit, unit_conv.get(raw_unit.replace(" ", ""), 1.0)
                )
                base_val = numeric * multiplier

                if not self._is_reasonable(base_val, indicator_code):
                    continue

                conf = max(0.2, 0.85 - i * 0.08)
                if raw_unit and raw_unit in unit_conv:
                    conf = min(0.95, conf + 0.05)

                if conf > best_conf:
                    best_conf = conf
                    snippet = full_text_original[max(0, m.start() - 50): m.end() + 80]
                    best = {
                        "indicator_code": indicator_code,
                        "numeric_value": round(base_val, 4),
                        "text_value": None,
                        "unit": config["unit"],
                        "raw_value_str": raw_val_str,
                        "raw_unit": raw_unit,
                        "confidence": round(conf, 2),
                        "page_number": self._find_page(m.start(), pages_text),
                        "text_snippet": snippet[:300],
                        "extraction_method": "regex_numeric",
                        "multiplier_applied": multiplier,
                    }

        return best

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _parse_numeric(self, s: str) -> Optional[float]:
        """Parse '1,234.56' or '1.234,56' → float."""
        if not s:
            return None
        cleaned = re.sub(r"[^\d\.,]", "", s.strip())
        if not cleaned:
            return None
        if cleaned.count(",") > 1:
            cleaned = cleaned.replace(",", "")
        elif cleaned.count(".") > 1:
            cleaned = cleaned.replace(".", "")
        elif "," in cleaned and "." in cleaned:
            if cleaned.rfind(".") > cleaned.rfind(","):
                cleaned = cleaned.replace(",", "")
            else:
                cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) == 3:
                cleaned = cleaned.replace(",", "")
            else:
                cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _is_reasonable(self, value: float, code: str) -> bool:
        if value < 0:
            return False
        if "Pct" in code or code.endswith("%"):
            return 0 <= value <= 100
        if "Headcount" in code or "Employee" in code or "FTE" in code:
            return 1 <= value <= 5_000_000
        if "GHG" in code or "Scope" in code or "Emissions" in code:
            return 0 < value < 5e10
        if "Energy" in code:
            return 0 < value < 1e13
        if "Revenue" in code or "Balance" in code or "MEUR" in code:
            return 0 < value < 5_000_000
        if "Fatalities" in code or "Incidents" in code:
            return 0 <= value <= 10_000
        return True

    def _find_page(self, char_pos: int, pages_text: List[Tuple[int, str]]) -> int:
        cumulative = 0
        for page_num, text in pages_text:
            cumulative += len(text) + 1
            if char_pos < cumulative:
                return page_num
        return len(pages_text)

    def _build_validation_summary(self, result: dict) -> dict:
        extracted = result.get("extracted_kpis", {})
        gaps = result.get("mandatory_gaps", [])
        by_std: Dict[str, int] = {}
        gap_by_std: Dict[str, int] = {}

        for code in extracted:
            std = ESRS_INDICATORS.get(code, {}).get("standard", "Unknown")
            by_std[std] = by_std.get(std, 0) + 1
        for code in gaps:
            std = ESRS_INDICATORS.get(code, {}).get("standard", "Unknown")
            gap_by_std[std] = gap_by_std.get(std, 0) + 1

        confs = [v.get("confidence", 0) for v in extracted.values() if v.get("numeric_value") is not None]
        return {
            "total_indicators_attempted": len(self.indicators),
            "total_extracted": len(extracted),
            "total_mandatory_gaps": len(gaps),
            "extraction_rate_pct": round(len(extracted) / max(len(self.indicators), 1) * 100, 1),
            "mandatory_coverage_pct": round(
                (len(self.mandatory) - len(gaps)) / max(len(self.mandatory), 1) * 100, 1
            ),
            "high_confidence_count": sum(1 for c in confs if c >= 0.75),
            "avg_confidence": round(sum(confs) / max(len(confs), 1), 3),
            "by_standard_extracted": by_std,
            "by_standard_gaps": gap_by_std,
            "input_parameters": {
                "total_pages": result.get("total_pages", 0),
                "total_text_chars": result.get("total_text_length", 0),
                "entity_name": result.get("entity_name"),
                "reporting_year": result.get("reporting_year"),
            },
            "output_parameters": {
                "kpis_with_numeric_value": sum(
                    1 for v in extracted.values() if v.get("numeric_value") is not None
                ),
                "kpis_with_text_value": sum(
                    1 for v in extracted.values() if v.get("text_value") is not None
                ),
            },
        }
