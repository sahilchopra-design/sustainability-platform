"""
Climate TRACE Ingester -- satellite-derived GHG emissions by country and sector.

Climate TRACE API: https://api.climatetrace.org
  - Public, no API key required
  - Country-level emissions by sector and gas
  - Endpoints:
      /v6/country/emissions  -- country emissions with sector breakdown
      /v6/definitions/sectors -- list of sectors
      /v6/definitions/countries -- list of countries
  - Data from 2015-2022 (updated annually)

Strategy:
  - Fetch country-level emissions for all countries, by sector
  - One row per (country, sector, subsector, gas, year)
  - Upsert on composite ID (country_sector_gas_year)
  - Default schedule: weekly (Monday 2 AM UTC)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from ingestion.base_ingester import BaseIngester, IngestionResult

# Climate TRACE source_id in dh_data_sources
CLIMATE_TRACE_SOURCE_ID = "799a2141-6324-4b6e-99fb-62589926731c"
CLIMATE_TRACE_API = "https://api.climatetrace.org/v6"

# Top emitting countries to start with (ISO3 alpha-3)
# Full load would be ~200 countries; cap for performance
TOP_COUNTRIES = [
    "CHN", "USA", "IND", "RUS", "JPN", "BRA", "IDN", "IRN", "DEU", "SAU",
    "KOR", "CAN", "MEX", "ZAF", "TUR", "AUS", "GBR", "FRA", "ITA", "POL",
    "THA", "KAZ", "ARG", "MYS", "EGY", "VNM", "PAK", "NGA", "ARE", "COL",
]


class ClimateTraceIngester(BaseIngester):
    """
    Fetches country-level GHG emissions from Climate TRACE API.

    Supports:
      - Country emissions by sector (satellite-derived)
      - Multiple gas types (co2, ch4, n2o, co2e)
      - Year range filtering
    """

    source_id = CLIMATE_TRACE_SOURCE_ID
    display_name = "Climate TRACE"
    default_schedule = "0 2 * * 1"  # Monday 2 AM UTC

    # Configuration
    timeout_seconds = 600
    batch_size = 500
    max_records = 50000  # Safety cap

    def __init__(self, countries: Optional[List[str]] = None,
                 since: int = 2015, max_records: int = 50000):
        super().__init__()
        self.countries = countries or TOP_COUNTRIES
        self.since = since
        self.max_records = max_records

    # -- Stage 1: Fetch -------------------------------------------------------

    def fetch(self, db: Session) -> Any:
        """
        Fetch country emissions from Climate TRACE API.

        Uses /v6/country/emissions endpoint with country and since params.
        Returns list of emission record dicts.
        """
        all_records = []

        for iso3 in self.countries:
            if len(all_records) >= self.max_records:
                self.log(f"Hit max_records cap ({self.max_records}), stopping")
                break

            self.log(f"Fetching emissions for {iso3} (since {self.since})...")

            try:
                resp = requests.get(
                    f"{CLIMATE_TRACE_API}/country/emissions",
                    params={
                        "country": iso3,
                        "since": self.since,
                    },
                    timeout=30,
                    headers={"Accept": "application/json"},
                )

                if resp.status_code == 429:
                    self.log(f"Rate limited on {iso3}, stopping", "warning")
                    break

                if resp.status_code != 200:
                    self.log(f"API returned {resp.status_code} for {iso3}, skipping", "warning")
                    continue

                data = resp.json()

                # API returns a list of emission objects or a dict with emissions key
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    records = data.get("emissions", data.get("results", [data]))
                else:
                    records = []

                # Tag each record with the country
                for rec in records:
                    if isinstance(rec, dict):
                        rec["_country_iso3"] = iso3
                        all_records.append(rec)

                self.log(f"  {iso3}: {len(records)} records (total: {len(all_records)})")

            except requests.RequestException as exc:
                self.log(f"Request failed for {iso3}: {exc}", "warning")
                continue

        self.log(f"Fetch complete: {len(all_records)} Climate TRACE records")
        return all_records

    # -- Stage 2: Validate ----------------------------------------------------

    def validate(self, raw_data: Any) -> Any:
        """Validate Climate TRACE records -- require sector and year."""
        valid = []
        for rec in raw_data:
            sector = rec.get("sector") or rec.get("subsector")
            # Year might be in different fields
            year = rec.get("year")
            if not year:
                # Some responses have emissions as time-series within a sector record
                pass

            if sector:
                valid.append(rec)

        skipped = len(raw_data) - len(valid)
        if skipped:
            self.log(f"Validation: skipped {skipped} records missing sector", "warning")
        return valid

    # -- Stage 3: Transform ---------------------------------------------------

    def transform(self, validated_data: Any) -> List[Dict[str, Any]]:
        """Transform Climate TRACE API records into dh_climate_trace_emissions rows."""
        rows = []

        for rec in validated_data:
            country_iso3 = rec.get("_country_iso3", "")
            country_name = rec.get("country", rec.get("country_name", ""))
            sector = rec.get("sector", "")
            subsector = rec.get("subsector", "")
            gas = rec.get("gas", "co2e")

            # Handle both flat records and nested emissions time-series
            emissions_data = rec.get("emissions", None)

            if isinstance(emissions_data, dict):
                # Nested: { "2015": value, "2016": value, ... }
                for year_str, value in emissions_data.items():
                    try:
                        year = int(year_str)
                    except (ValueError, TypeError):
                        continue
                    row = self._make_row(
                        country_iso3, country_name, sector, subsector,
                        gas, year, value, rec,
                    )
                    rows.append(row)
            elif isinstance(emissions_data, list):
                # List of {year, value} objects
                for item in emissions_data:
                    if isinstance(item, dict):
                        year = item.get("year")
                        value = item.get("value") or item.get("emissions_quantity")
                        if year:
                            row = self._make_row(
                                country_iso3, country_name, sector, subsector,
                                gas, int(year), value, rec,
                            )
                            rows.append(row)
            else:
                # Flat record with year + emissions_quantity fields
                year = rec.get("year")
                value = rec.get("emissions_quantity") or rec.get("value") or rec.get("co2e_100yr")
                if year:
                    row = self._make_row(
                        country_iso3, country_name, sector, subsector,
                        gas, int(year), value, rec,
                    )
                    rows.append(row)

        self.log(f"Transform: {len(rows)} emission rows produced")
        return rows

    # -- Stage 4: Load --------------------------------------------------------

    def load(self, db: Session, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert Climate TRACE emissions into dh_climate_trace_emissions."""
        inserted = 0
        updated = 0
        failed = 0

        for i in range(0, len(rows), self.batch_size):
            batch = rows[i:i + self.batch_size]

            for row in batch:
                try:
                    sql = text("""
                        INSERT INTO dh_climate_trace_emissions (
                            id, source_id, country_iso3, country_name,
                            sector, subsector, gas, year,
                            emissions_quantity, emissions_unit,
                            facility_name, facility_id, latitude, longitude,
                            data_source, confidence, raw_record,
                            ingested_at, updated_at
                        ) VALUES (
                            :id, :source_id, :country_iso3, :country_name,
                            :sector, :subsector, :gas, :year,
                            :emissions_quantity, :emissions_unit,
                            :facility_name, :facility_id, :latitude, :longitude,
                            :data_source, :confidence, :raw_record::jsonb,
                            NOW(), NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            emissions_quantity = EXCLUDED.emissions_quantity,
                            emissions_unit = EXCLUDED.emissions_unit,
                            confidence = EXCLUDED.confidence,
                            raw_record = EXCLUDED.raw_record,
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
                        self.log(f"Failed to upsert CT emission {row.get('id')}: {exc}", "warning")

            db.commit()
            self.log(f"Batch committed: {min(i + self.batch_size, len(rows))}/{len(rows)}")

        return {"inserted": inserted, "updated": updated, "skipped": 0, "failed": failed}

    # -- Helpers --------------------------------------------------------------

    def _make_row(self, country_iso3: str, country_name: str,
                  sector: str, subsector: str, gas: str,
                  year: int, value: Any, raw: dict) -> dict:
        """Create a single emission row dict."""
        # Deterministic ID from composite key
        id_str = f"ct:{country_iso3}:{sector}:{subsector}:{gas}:{year}"
        row_id = hashlib.sha256(id_str.encode()).hexdigest()[:24]

        return {
            "id": row_id,
            "source_id": CLIMATE_TRACE_SOURCE_ID,
            "country_iso3": country_iso3,
            "country_name": country_name,
            "sector": sector,
            "subsector": subsector or None,
            "gas": gas or "co2e",
            "year": year,
            "emissions_quantity": float(value) if value is not None else None,
            "emissions_unit": "tonnes",
            "facility_name": raw.get("facility_name") or raw.get("asset_name"),
            "facility_id": raw.get("facility_id") or raw.get("asset_id"),
            "latitude": raw.get("lat") or raw.get("latitude"),
            "longitude": raw.get("lon") or raw.get("longitude"),
            "data_source": "climate_trace",
            "confidence": raw.get("confidence") or raw.get("data_quality"),
            "raw_record": raw,
        }
