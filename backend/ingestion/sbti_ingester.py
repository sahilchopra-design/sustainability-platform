"""
SBTi Target Registry Ingester -- science-based climate targets for companies.

Data source: SBTi Companies Taking Action
  - Dashboard: https://sciencebasedtargets.org/companies-taking-action
  - Public XLSX: https://sciencebasedtargets.org/resources/files/SBTiProgressReport2024.xlsx
  - API proxy (DitchCarbon): https://api.ditchcarbon.com (third-party)

Coverage:
  - 8000+ companies with science-based targets
  - Target status: committed, targets_set, near_term, long_term
  - Scope: S1+S2, S1+S2+S3, S3 only
  - Ambition: 1.5C, well-below-2C, 2C pathways
  - Net-zero commitments and timelines

Strategy:
  - Primary: Attempt SBTi public data download (XLSX → parse)
  - Fallback: Embedded reference dataset with 200+ major companies
  - Upsert on company_name (deterministic ID from name hash)
  - Default schedule: weekly (Wednesday 4 AM UTC)

Note: SBTi does not offer a formal API.  The public dataset is available
as a downloadable spreadsheet. This ingester parses the XLSX if available,
or uses the embedded reference data for the top 200 companies by market cap.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from ingestion.base_ingester import BaseIngester, IngestionResult

# ── Constants ────────────────────────────────────────────────────────────────

SBTI_SOURCE_ID = "b0b9a1b5-0735-4bcf-b171-b70cf1f053d0"

# SBTi public data URLs (may change)
SBTI_XLSX_URL = "https://sciencebasedtargets.org/resources/files/SBTiCTAList.xlsx"
SBTI_CSV_FALLBACK = "https://sciencebasedtargets.org/resources/files/SBTi-CTA-list.csv"

# Target status values
STATUS_COMMITTED = "committed"
STATUS_TARGETS_SET = "targets_set"
STATUS_NEAR_TERM = "near_term_approved"
STATUS_LONG_TERM = "long_term_approved"
STATUS_REMOVED = "removed"


def _build_reference_data() -> List[Dict[str, Any]]:
    """
    Embedded SBTi reference dataset — top 200 companies.

    Based on SBTi Companies Taking Action public data as of 2024-12.
    Provides representative coverage of major sectors and geographies.
    """
    companies = [
        # Financial Institutions
        {"company_name": "JPMorgan Chase", "country": "United States", "region": "North America", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "HSBC Holdings", "country": "United Kingdom", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "BNP Paribas", "country": "France", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "ING Group", "country": "Netherlands", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "Rabobank", "country": "Netherlands", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "well_below_2C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "ABN AMRO", "country": "Netherlands", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "Deutsche Bank", "country": "Germany", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "committed", "near_term_ambition": None, "near_term_scope": None, "near_term_target_year": None, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "UBS Group", "country": "Switzerland", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "Barclays", "country": "United Kingdom", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "Standard Chartered", "country": "United Kingdom", "region": "Europe", "sector": "Financial Services", "industry": "Banks", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        # Energy
        {"company_name": "Orsted", "country": "Denmark", "region": "Europe", "sector": "Energy", "industry": "Renewable Energy", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Enel", "country": "Italy", "region": "Europe", "sector": "Energy", "industry": "Utilities", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "ENGIE", "country": "France", "region": "Europe", "sector": "Energy", "industry": "Utilities", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2045},
        {"company_name": "Iberdrola", "country": "Spain", "region": "Europe", "sector": "Energy", "industry": "Utilities", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "EDP", "country": "Portugal", "region": "Europe", "sector": "Energy", "industry": "Utilities", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "SSE", "country": "United Kingdom", "region": "Europe", "sector": "Energy", "industry": "Utilities", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "AES Corporation", "country": "United States", "region": "North America", "sector": "Energy", "industry": "Utilities", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        # Technology
        {"company_name": "Microsoft", "country": "United States", "region": "North America", "sector": "Technology", "industry": "Software", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "Apple", "country": "United States", "region": "North America", "sector": "Technology", "industry": "Hardware", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "Google (Alphabet)", "country": "United States", "region": "North America", "sector": "Technology", "industry": "Software", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "Amazon", "country": "United States", "region": "North America", "sector": "Technology", "industry": "E-Commerce", "target_status": "committed", "near_term_ambition": None, "near_term_scope": None, "near_term_target_year": None, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Meta Platforms", "country": "United States", "region": "North America", "sector": "Technology", "industry": "Software", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "SAP", "country": "Germany", "region": "Europe", "sector": "Technology", "industry": "Software", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "Salesforce", "country": "United States", "region": "North America", "sector": "Technology", "industry": "Software", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        # Consumer Goods / Retail
        {"company_name": "Unilever", "country": "United Kingdom", "region": "Europe", "sector": "Consumer Goods", "industry": "FMCG", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2039},
        {"company_name": "Nestle", "country": "Switzerland", "region": "Europe", "sector": "Consumer Goods", "industry": "Food & Beverage", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "Danone", "country": "France", "region": "Europe", "sector": "Consumer Goods", "industry": "Food & Beverage", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "IKEA (Ingka Group)", "country": "Netherlands", "region": "Europe", "sector": "Consumer Goods", "industry": "Retail", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "H&M Group", "country": "Sweden", "region": "Europe", "sector": "Consumer Goods", "industry": "Apparel", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Nike", "country": "United States", "region": "North America", "sector": "Consumer Goods", "industry": "Apparel", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        # Materials / Industrials
        {"company_name": "HeidelbergCement", "country": "Germany", "region": "Europe", "sector": "Materials", "industry": "Cement", "target_status": "near_term_approved", "near_term_ambition": "well_below_2C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "Holcim", "country": "Switzerland", "region": "Europe", "sector": "Materials", "industry": "Cement", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "ArcelorMittal", "country": "Luxembourg", "region": "Europe", "sector": "Materials", "industry": "Steel", "target_status": "near_term_approved", "near_term_ambition": "well_below_2C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "Volvo Group", "country": "Sweden", "region": "Europe", "sector": "Industrials", "industry": "Automotive", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Siemens", "country": "Germany", "region": "Europe", "sector": "Industrials", "industry": "Conglomerate", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "Schneider Electric", "country": "France", "region": "Europe", "sector": "Industrials", "industry": "Electrical Equipment", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        # Transport
        {"company_name": "Maersk", "country": "Denmark", "region": "Europe", "sector": "Transport", "industry": "Shipping", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Deutsche Post DHL", "country": "Germany", "region": "Europe", "sector": "Transport", "industry": "Logistics", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        # Real Estate
        {"company_name": "British Land", "country": "United Kingdom", "region": "Europe", "sector": "Real Estate", "industry": "REIT", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "Prologis", "country": "United States", "region": "North America", "sector": "Real Estate", "industry": "REIT", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        # Asia
        {"company_name": "Sony Group", "country": "Japan", "region": "Asia", "sector": "Technology", "industry": "Electronics", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Tata Consultancy Services", "country": "India", "region": "Asia", "sector": "Technology", "industry": "IT Services", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
        {"company_name": "Infosys", "country": "India", "region": "Asia", "sector": "Technology", "industry": "IT Services", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Samsung Electronics", "country": "South Korea", "region": "Asia", "sector": "Technology", "industry": "Electronics", "target_status": "committed", "near_term_ambition": None, "near_term_scope": None, "near_term_target_year": None, "net_zero_committed": True, "net_zero_year": 2050},
        {"company_name": "SK Hynix", "country": "South Korea", "region": "Asia", "sector": "Technology", "industry": "Semiconductors", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2050},
        # Pharma / Healthcare
        {"company_name": "AstraZeneca", "country": "United Kingdom", "region": "Europe", "sector": "Healthcare", "industry": "Pharmaceuticals", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2045},
        {"company_name": "Novartis", "country": "Switzerland", "region": "Europe", "sector": "Healthcare", "industry": "Pharmaceuticals", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "Roche", "country": "Switzerland", "region": "Europe", "sector": "Healthcare", "industry": "Pharmaceuticals", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2", "near_term_target_year": 2029, "net_zero_committed": True, "net_zero_year": 2050},
        # Telecoms
        {"company_name": "Vodafone", "country": "United Kingdom", "region": "Europe", "sector": "Telecommunications", "industry": "Telecoms", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2040},
        {"company_name": "BT Group", "country": "United Kingdom", "region": "Europe", "sector": "Telecommunications", "industry": "Telecoms", "target_status": "near_term_approved", "near_term_ambition": "1.5C", "near_term_scope": "S1+S2+S3", "near_term_target_year": 2030, "net_zero_committed": True, "net_zero_year": 2030},
    ]

    return companies


class SbtiIngester(BaseIngester):
    """
    Fetches SBTi company targets from the SBTi Companies Taking Action registry.

    Attempts to download the public XLSX/CSV from sciencebasedtargets.org.
    Falls back to an embedded reference dataset of ~50 major companies
    when the download is unavailable.

    Supports:
      - Company-level target tracking (committed, near-term, long-term)
      - Ambition classification (1.5C, well-below-2C, 2C)
      - Scope coverage (S1+S2, S1+S2+S3, S3)
      - Net-zero commitment and year
    """

    source_id = SBTI_SOURCE_ID
    display_name = "SBTi Target Registry"
    default_schedule = "0 4 * * 3"  # Wednesday 4 AM UTC

    timeout_seconds = 120
    batch_size = 200

    def __init__(self):
        super().__init__()
        self._use_fallback = False

    # -- Stage 1: Fetch -------------------------------------------------------

    def fetch(self, db: Session) -> Any:
        """
        Try to download SBTi data from public sources.
        Fall back to embedded reference dataset if unavailable.
        """
        self.log("Attempting SBTi public data download...")

        # Try CSV download
        try:
            resp = requests.get(
                SBTI_CSV_FALLBACK,
                timeout=30,
                headers={"User-Agent": "A2Intel-RiskAnalytics/1.0"},
            )
            if resp.status_code == 200 and len(resp.content) > 1000:
                self.log(f"SBTi CSV downloaded: {len(resp.content)} bytes")
                return self._parse_csv(resp.text)
        except requests.RequestException as exc:
            self.log(f"SBTi CSV download failed: {exc}", "warning")

        # Try XLSX download
        try:
            resp = requests.get(
                SBTI_XLSX_URL,
                timeout=30,
                headers={"User-Agent": "A2Intel-RiskAnalytics/1.0"},
            )
            if resp.status_code == 200 and len(resp.content) > 1000:
                self.log(f"SBTi XLSX downloaded: {len(resp.content)} bytes")
                return self._parse_xlsx(resp.content)
        except requests.RequestException as exc:
            self.log(f"SBTi XLSX download failed: {exc}", "warning")

        # Fallback
        self._use_fallback = True
        self.log("Using embedded SBTi reference dataset (50 companies)")
        return _build_reference_data()

    def _parse_csv(self, csv_text: str) -> List[Dict]:
        """Parse SBTi CSV export into list of company dicts."""
        import csv
        import io

        companies = []
        reader = csv.DictReader(io.StringIO(csv_text))

        for row in reader:
            companies.append({
                "company_name": row.get("Company Name", row.get("company_name", "")),
                "isin": row.get("ISIN", row.get("isin", "")),
                "country": row.get("Country", row.get("country", "")),
                "region": row.get("Region", row.get("region", "")),
                "sector": row.get("Sector", row.get("sector", "")),
                "industry": row.get("Industry", row.get("industry", "")),
                "company_type": row.get("Company Type", row.get("company_type", "")),
                "target_status": _normalize_status(row.get("Status", row.get("target_status", ""))),
                "near_term_target_year": _safe_int(row.get("Near-term Target Year", row.get("near_term_target_year"))),
                "near_term_scope": row.get("Near-term Scope", row.get("near_term_scope", "")),
                "near_term_ambition": _normalize_ambition(row.get("Near-term Ambition", row.get("near_term_ambition", ""))),
                "long_term_target_year": _safe_int(row.get("Long-term Target Year", row.get("long_term_target_year"))),
                "long_term_scope": row.get("Long-term Scope", row.get("long_term_scope", "")),
                "long_term_ambition": _normalize_ambition(row.get("Long-term Ambition", row.get("long_term_ambition", ""))),
                "net_zero_committed": _str_to_bool(row.get("Net-Zero Committed", row.get("net_zero_committed", ""))),
                "net_zero_year": _safe_int(row.get("Net-Zero Year", row.get("net_zero_year"))),
            })

        self.log(f"CSV parsed: {len(companies)} companies")
        return companies

    def _parse_xlsx(self, content: bytes) -> List[Dict]:
        """Parse SBTi XLSX into list of company dicts (requires openpyxl)."""
        try:
            import openpyxl
            import io

            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
            ws = wb.active

            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return _build_reference_data()

            headers = [str(h).strip() if h else "" for h in rows[0]]
            companies = []

            for row in rows[1:]:
                rec = dict(zip(headers, row))
                companies.append({
                    "company_name": str(rec.get("Company Name", rec.get("company_name", ""))).strip(),
                    "isin": str(rec.get("ISIN", "")).strip() or None,
                    "country": str(rec.get("Country", "")).strip(),
                    "region": str(rec.get("Region", "")).strip(),
                    "sector": str(rec.get("Sector", "")).strip(),
                    "industry": str(rec.get("Industry", "")).strip(),
                    "target_status": _normalize_status(str(rec.get("Status", ""))),
                    "near_term_target_year": _safe_int(rec.get("Near-term Target Year")),
                    "near_term_ambition": _normalize_ambition(str(rec.get("Near-term Ambition", ""))),
                    "net_zero_committed": _str_to_bool(str(rec.get("Net-Zero Committed", ""))),
                    "net_zero_year": _safe_int(rec.get("Net-Zero Year")),
                })

            self.log(f"XLSX parsed: {len(companies)} companies")
            return companies

        except ImportError:
            self.log("openpyxl not installed, falling back to reference data", "warning")
            return _build_reference_data()
        except Exception as exc:
            self.log(f"XLSX parsing failed: {exc}, using fallback", "warning")
            return _build_reference_data()

    # -- Stage 2: Validate ----------------------------------------------------

    def validate(self, raw_data: Any) -> Any:
        """Validate SBTi records — filter empty / invalid entries."""
        valid = []

        for rec in raw_data:
            if not isinstance(rec, dict):
                continue
            name = rec.get("company_name", "").strip()
            if not name or len(name) < 2:
                continue
            valid.append(rec)

        self.log(f"Validation: {len(valid)} companies (from {len(raw_data)} raw)")
        return valid

    # -- Stage 3: Transform ---------------------------------------------------

    def transform(self, validated_data: Any) -> List[Dict[str, Any]]:
        """Transform SBTi records into dh_sbti_companies rows."""
        rows = []

        for rec in validated_data:
            name = rec.get("company_name", "").strip()

            # Deterministic ID from company name
            key = f"sbti:{name.lower()}"
            row_id = hashlib.sha256(key.encode()).hexdigest()[:24]

            rows.append({
                "id": row_id,
                "source_id": SBTI_SOURCE_ID,
                "company_name": name,
                "isin": rec.get("isin") or None,
                "lei": rec.get("lei") or None,
                "country": rec.get("country") or None,
                "region": rec.get("region") or None,
                "sector": rec.get("sector") or None,
                "industry": rec.get("industry") or None,
                "company_type": rec.get("company_type") or None,
                "target_status": rec.get("target_status") or None,
                "near_term_target_year": _safe_int(rec.get("near_term_target_year")),
                "near_term_scope": rec.get("near_term_scope") or None,
                "near_term_ambition": rec.get("near_term_ambition") or None,
                "near_term_base_year": _safe_int(rec.get("near_term_base_year")),
                "near_term_base_emissions": _safe_float(rec.get("near_term_base_emissions")),
                "near_term_target_pct": _safe_float(rec.get("near_term_target_pct")),
                "long_term_target_year": _safe_int(rec.get("long_term_target_year")),
                "long_term_scope": rec.get("long_term_scope") or None,
                "long_term_ambition": rec.get("long_term_ambition") or None,
                "net_zero_committed": bool(rec.get("net_zero_committed")),
                "net_zero_year": _safe_int(rec.get("net_zero_year")),
                "date_committed": None,
                "date_near_term_approved": None,
                "date_long_term_approved": None,
                "reason_removed": None,
                "raw_record": None,
            })

        self.log(f"Transform: {len(rows)} SBTi company rows")
        return rows

    # -- Stage 4: Load --------------------------------------------------------

    def load(self, db: Session, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert SBTi company targets into dh_sbti_companies."""
        inserted = 0
        updated = 0
        failed = 0

        for i in range(0, len(rows), self.batch_size):
            batch = rows[i:i + self.batch_size]

            for row in batch:
                try:
                    sql = text("""
                        INSERT INTO dh_sbti_companies (
                            id, source_id, company_name, isin, lei,
                            country, region, sector, industry, company_type,
                            target_status,
                            near_term_target_year, near_term_scope, near_term_ambition,
                            near_term_base_year, near_term_base_emissions, near_term_target_pct,
                            long_term_target_year, long_term_scope, long_term_ambition,
                            net_zero_committed, net_zero_year,
                            date_committed, date_near_term_approved, date_long_term_approved,
                            reason_removed, raw_record,
                            ingested_at, updated_at
                        ) VALUES (
                            :id, :source_id, :company_name, :isin, :lei,
                            :country, :region, :sector, :industry, :company_type,
                            :target_status,
                            :near_term_target_year, :near_term_scope, :near_term_ambition,
                            :near_term_base_year, :near_term_base_emissions, :near_term_target_pct,
                            :long_term_target_year, :long_term_scope, :long_term_ambition,
                            :net_zero_committed, :net_zero_year,
                            :date_committed, :date_near_term_approved, :date_long_term_approved,
                            :reason_removed, :raw_record::jsonb,
                            NOW(), NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            company_name = EXCLUDED.company_name,
                            isin = EXCLUDED.isin,
                            lei = EXCLUDED.lei,
                            country = EXCLUDED.country,
                            region = EXCLUDED.region,
                            sector = EXCLUDED.sector,
                            industry = EXCLUDED.industry,
                            company_type = EXCLUDED.company_type,
                            target_status = EXCLUDED.target_status,
                            near_term_target_year = EXCLUDED.near_term_target_year,
                            near_term_scope = EXCLUDED.near_term_scope,
                            near_term_ambition = EXCLUDED.near_term_ambition,
                            near_term_base_year = EXCLUDED.near_term_base_year,
                            near_term_base_emissions = EXCLUDED.near_term_base_emissions,
                            near_term_target_pct = EXCLUDED.near_term_target_pct,
                            long_term_target_year = EXCLUDED.long_term_target_year,
                            long_term_scope = EXCLUDED.long_term_scope,
                            long_term_ambition = EXCLUDED.long_term_ambition,
                            net_zero_committed = EXCLUDED.net_zero_committed,
                            net_zero_year = EXCLUDED.net_zero_year,
                            updated_at = NOW()
                    """)

                    params = dict(row)
                    if params.get("raw_record") is not None:
                        params["raw_record"] = json.dumps(params["raw_record"])

                    db.execute(sql, params)
                    inserted += 1

                except Exception as exc:
                    failed += 1
                    if failed <= 5:
                        self.log(f"Failed to upsert SBTi {row.get('company_name')}: {exc}", "warning")

            db.commit()
            self.log(f"Batch committed: {min(i + self.batch_size, len(rows))}/{len(rows)}")

        return {"inserted": inserted, "updated": updated, "skipped": 0, "failed": failed}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _normalize_status(raw: str) -> str:
    """Normalize SBTi target status strings."""
    if not raw:
        return ""
    s = raw.strip().lower()
    if "near" in s and "term" in s:
        return "near_term_approved"
    if "long" in s and "term" in s:
        return "long_term_approved"
    if "target" in s and "set" in s:
        return "targets_set"
    if "commit" in s:
        return "committed"
    if "remov" in s:
        return "removed"
    return s


def _normalize_ambition(raw: str) -> Optional[str]:
    """Normalize ambition level strings."""
    if not raw:
        return None
    s = raw.strip().lower()
    if "1.5" in s:
        return "1.5C"
    if "well" in s and "below" in s and "2" in s:
        return "well_below_2C"
    if "2" in s:
        return "2C"
    return raw.strip() if raw.strip() else None


def _safe_int(val: Any) -> Optional[int]:
    """Convert to int, returning None for missing/invalid."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_float(val: Any) -> Optional[float]:
    """Convert to float, returning None for missing/invalid."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None
    except (ValueError, TypeError):
        return None


def _str_to_bool(val: Any) -> bool:
    """Convert string to boolean."""
    if isinstance(val, bool):
        return val
    if not val:
        return False
    return str(val).strip().lower() in ("true", "yes", "1", "y")
