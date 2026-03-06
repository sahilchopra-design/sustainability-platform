"""
OWID CO2 & Energy Ingester -- country-level emissions and energy time-series.

Data source: Our World in Data GitHub repository
  - Raw CSV: https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv
  - JSON:    https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.json
  - Codebook: https://github.com/owid/co2-data/blob/master/owid-co2-codebook.csv

Coverage:
  - 200+ countries, 1750-2023 (varies by indicator)
  - CO2 emissions (total, per-capita, by fuel, cumulative)
  - Other GHGs (methane, N2O, total GHG)
  - Energy (primary consumption, electricity, renewables mix)
  - Temperature (contribution from CO2 and GHG)
  - Aggregates from GCP, BP, EMBER, EIA, UNFCCC

Strategy:
  - Fetch the full JSON file from GitHub (single HTTP GET, ~35 MB)
  - JSON format: { "country_name": [ {year: ..., co2: ..., ...}, ... ] }
  - Filter to relevant years (>= since parameter, default 1990)
  - Upsert on (country_iso3, year) composite unique constraint
  - Default schedule: weekly (Sunday 5 AM UTC)
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from ingestion.base_ingester import BaseIngester, IngestionResult

# OWID source_id in dh_data_sources
OWID_SOURCE_ID = "a1c7e3d9-4b2f-4e8a-9d6c-3f5a7b8e1c2d"
OWID_CSV_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
OWID_JSON_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.json"

# Columns we extract from OWID dataset (maps to our DB columns)
OWID_COLUMNS = [
    "iso_code", "country", "year", "population", "gdp",
    "co2", "co2_per_capita", "co2_per_gdp", "co2_growth_prct",
    "cumulative_co2", "share_global_co2",
    "coal_co2", "oil_co2", "gas_co2", "cement_co2", "flaring_co2", "other_industry_co2",
    "methane", "nitrous_oxide", "total_ghg", "total_ghg_excluding_lucf",
    "primary_energy_consumption", "energy_per_capita", "energy_per_gdp",
    "electricity_generation",
    "renewables_share_energy", "renewables_share_elec",
    "fossil_share_energy", "nuclear_share_energy",
    "solar_share_energy", "wind_share_energy", "hydro_share_energy",
    "temperature_change_from_co2", "temperature_change_from_ghg",
]


class OwidIngester(BaseIngester):
    """
    Fetches country-level CO2, energy, and climate data from Our World in Data.

    Supports:
      - Full dataset load from GitHub JSON
      - Year filtering (since parameter)
      - Country filtering (optional ISO3 list)
    """

    source_id = OWID_SOURCE_ID
    display_name = "Our World in Data (OWID CO2)"
    default_schedule = "0 5 * * 0"  # Sunday 5 AM UTC

    # Configuration
    timeout_seconds = 300
    batch_size = 500
    max_records = 100000  # Safety cap

    def __init__(self, since: int = 1990,
                 countries: Optional[List[str]] = None,
                 max_records: int = 100000):
        super().__init__()
        self.since = since
        self.countries = countries  # Optional ISO3 filter
        self.max_records = max_records

    # -- Stage 1: Fetch -------------------------------------------------------

    def fetch(self, db: Session) -> Any:
        """
        Download the full OWID CO2 JSON from GitHub.

        The JSON file is ~35 MB with structure:
          { "Afghanistan": [ {year: 1949, co2: 0.015, ...}, ... ],
            "Albania": [ ... ], ... }
        """
        self.log("Fetching OWID CO2 dataset from GitHub...")

        try:
            resp = requests.get(
                OWID_JSON_URL,
                timeout=120,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            self.log(f"Failed to fetch OWID dataset: {exc}", "error")
            raise

        data = resp.json()
        self.log(f"Fetch complete: {len(data)} countries in OWID dataset")
        return data

    # -- Stage 2: Validate ----------------------------------------------------

    def validate(self, raw_data: Any) -> Any:
        """
        Validate OWID data -- filter countries and years.

        Input: dict of { country_name: [records] }
        Output: flat list of records with country name tagged
        """
        valid = []

        for country_name, records in raw_data.items():
            if not isinstance(records, list):
                continue

            for rec in records:
                if not isinstance(rec, dict):
                    continue

                year = rec.get("year")
                if not year or int(year) < self.since:
                    continue

                iso3 = rec.get("iso_code")

                # Skip aggregate entries (OWID_xxx, World, etc.) unless iso_code is 3 chars
                if not iso3 or len(iso3) != 3 or iso3.startswith("OWID"):
                    continue

                # Optional country filter
                if self.countries and iso3 not in self.countries:
                    continue

                # Must have at least co2 or total_ghg data
                if rec.get("co2") is None and rec.get("total_ghg") is None:
                    continue

                rec["_country_name"] = country_name
                valid.append(rec)

                if len(valid) >= self.max_records:
                    break

            if len(valid) >= self.max_records:
                break

        self.log(f"Validation: {len(valid)} records (since {self.since}, "
                 f"countries={'all' if not self.countries else len(self.countries)})")
        return valid

    # -- Stage 3: Transform ---------------------------------------------------

    def transform(self, validated_data: Any) -> List[Dict[str, Any]]:
        """Transform OWID records into dh_owid_co2_energy rows."""
        rows = []

        for rec in validated_data:
            iso3 = rec.get("iso_code", "")
            year = int(rec.get("year", 0))
            country_name = rec.get("_country_name", rec.get("country", ""))

            # Deterministic ID
            row_id = f"owid:{iso3}:{year}"

            row = {
                "id": row_id,
                "source_id": OWID_SOURCE_ID,
                "country_iso3": iso3,
                "country_name": country_name,
                "year": year,
                "population": _safe_int(rec.get("population")),
                "gdp": _safe_float(rec.get("gdp")),
                # CO2
                "co2": _safe_float(rec.get("co2")),
                "co2_per_capita": _safe_float(rec.get("co2_per_capita")),
                "co2_per_gdp": _safe_float(rec.get("co2_per_gdp")),
                "co2_growth_pct": _safe_float(rec.get("co2_growth_prct")),
                "cumulative_co2": _safe_float(rec.get("cumulative_co2")),
                "share_global_co2": _safe_float(rec.get("share_global_co2")),
                # CO2 by fuel
                "coal_co2": _safe_float(rec.get("coal_co2")),
                "oil_co2": _safe_float(rec.get("oil_co2")),
                "gas_co2": _safe_float(rec.get("gas_co2")),
                "cement_co2": _safe_float(rec.get("cement_co2")),
                "flaring_co2": _safe_float(rec.get("flaring_co2")),
                "other_co2": _safe_float(rec.get("other_industry_co2")),
                # Other GHGs
                "methane": _safe_float(rec.get("methane")),
                "nitrous_oxide": _safe_float(rec.get("nitrous_oxide")),
                "total_ghg": _safe_float(rec.get("total_ghg")),
                "total_ghg_excl_lucf": _safe_float(rec.get("total_ghg_excluding_lucf")),
                # Energy
                "primary_energy_consumption": _safe_float(rec.get("primary_energy_consumption")),
                "energy_per_capita": _safe_float(rec.get("energy_per_capita")),
                "energy_per_gdp": _safe_float(rec.get("energy_per_gdp")),
                # Electricity
                "electricity_generation": _safe_float(rec.get("electricity_generation")),
                "renewables_share_energy": _safe_float(rec.get("renewables_share_energy")),
                "renewables_share_elec": _safe_float(rec.get("renewables_share_elec")),
                "fossil_share_energy": _safe_float(rec.get("fossil_share_energy")),
                "nuclear_share_energy": _safe_float(rec.get("nuclear_share_energy")),
                "solar_share_energy": _safe_float(rec.get("solar_share_energy")),
                "wind_share_energy": _safe_float(rec.get("wind_share_energy")),
                "hydro_share_energy": _safe_float(rec.get("hydro_share_energy")),
                # Temperature
                "temperature_change_from_co2": _safe_float(rec.get("temperature_change_from_co2")),
                "temperature_change_from_ghg": _safe_float(rec.get("temperature_change_from_ghg")),
                # Raw
                "raw_record": None,  # Skip to save space; original is in GitHub
            }
            rows.append(row)

        self.log(f"Transform: {len(rows)} OWID rows produced")
        return rows

    # -- Stage 4: Load --------------------------------------------------------

    def load(self, db: Session, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert OWID records into dh_owid_co2_energy."""
        inserted = 0
        updated = 0
        failed = 0

        for i in range(0, len(rows), self.batch_size):
            batch = rows[i:i + self.batch_size]

            for row in batch:
                try:
                    sql = text("""
                        INSERT INTO dh_owid_co2_energy (
                            id, source_id, country_iso3, country_name, year,
                            population, gdp,
                            co2, co2_per_capita, co2_per_gdp, co2_growth_pct,
                            cumulative_co2, share_global_co2,
                            coal_co2, oil_co2, gas_co2, cement_co2, flaring_co2, other_co2,
                            methane, nitrous_oxide, total_ghg, total_ghg_excl_lucf,
                            primary_energy_consumption, energy_per_capita, energy_per_gdp,
                            electricity_generation,
                            renewables_share_energy, renewables_share_elec,
                            fossil_share_energy, nuclear_share_energy,
                            solar_share_energy, wind_share_energy, hydro_share_energy,
                            temperature_change_from_co2, temperature_change_from_ghg,
                            raw_record,
                            ingested_at, updated_at
                        ) VALUES (
                            :id, :source_id, :country_iso3, :country_name, :year,
                            :population, :gdp,
                            :co2, :co2_per_capita, :co2_per_gdp, :co2_growth_pct,
                            :cumulative_co2, :share_global_co2,
                            :coal_co2, :oil_co2, :gas_co2, :cement_co2, :flaring_co2, :other_co2,
                            :methane, :nitrous_oxide, :total_ghg, :total_ghg_excl_lucf,
                            :primary_energy_consumption, :energy_per_capita, :energy_per_gdp,
                            :electricity_generation,
                            :renewables_share_energy, :renewables_share_elec,
                            :fossil_share_energy, :nuclear_share_energy,
                            :solar_share_energy, :wind_share_energy, :hydro_share_energy,
                            :temperature_change_from_co2, :temperature_change_from_ghg,
                            :raw_record::jsonb,
                            NOW(), NOW()
                        )
                        ON CONFLICT (country_iso3, year) DO UPDATE SET
                            country_name = EXCLUDED.country_name,
                            population = EXCLUDED.population,
                            gdp = EXCLUDED.gdp,
                            co2 = EXCLUDED.co2,
                            co2_per_capita = EXCLUDED.co2_per_capita,
                            co2_per_gdp = EXCLUDED.co2_per_gdp,
                            co2_growth_pct = EXCLUDED.co2_growth_pct,
                            cumulative_co2 = EXCLUDED.cumulative_co2,
                            share_global_co2 = EXCLUDED.share_global_co2,
                            coal_co2 = EXCLUDED.coal_co2,
                            oil_co2 = EXCLUDED.oil_co2,
                            gas_co2 = EXCLUDED.gas_co2,
                            cement_co2 = EXCLUDED.cement_co2,
                            flaring_co2 = EXCLUDED.flaring_co2,
                            other_co2 = EXCLUDED.other_co2,
                            methane = EXCLUDED.methane,
                            nitrous_oxide = EXCLUDED.nitrous_oxide,
                            total_ghg = EXCLUDED.total_ghg,
                            total_ghg_excl_lucf = EXCLUDED.total_ghg_excl_lucf,
                            primary_energy_consumption = EXCLUDED.primary_energy_consumption,
                            energy_per_capita = EXCLUDED.energy_per_capita,
                            energy_per_gdp = EXCLUDED.energy_per_gdp,
                            electricity_generation = EXCLUDED.electricity_generation,
                            renewables_share_energy = EXCLUDED.renewables_share_energy,
                            renewables_share_elec = EXCLUDED.renewables_share_elec,
                            fossil_share_energy = EXCLUDED.fossil_share_energy,
                            nuclear_share_energy = EXCLUDED.nuclear_share_energy,
                            solar_share_energy = EXCLUDED.solar_share_energy,
                            wind_share_energy = EXCLUDED.wind_share_energy,
                            hydro_share_energy = EXCLUDED.hydro_share_energy,
                            temperature_change_from_co2 = EXCLUDED.temperature_change_from_co2,
                            temperature_change_from_ghg = EXCLUDED.temperature_change_from_ghg,
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
                        self.log(f"Failed to upsert OWID {row.get('id')}: {exc}", "warning")

            db.commit()
            self.log(f"Batch committed: {min(i + self.batch_size, len(rows))}/{len(rows)}")

        return {"inserted": inserted, "updated": updated, "skipped": 0, "failed": failed}


# -- Module-level helpers -----------------------------------------------------

def _safe_float(val: Any) -> Optional[float]:
    """Convert to float, returning None for missing/invalid values."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None  # NaN check
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    """Convert to int, returning None for missing/invalid values."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
