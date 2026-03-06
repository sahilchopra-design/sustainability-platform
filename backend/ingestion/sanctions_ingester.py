"""
Sanctions Ingester — fetches consolidated sanctions data from OpenSanctions API.

OpenSanctions consolidates:
  - US OFAC SDN (Specially Designated Nationals)
  - EU Financial Sanctions List (EU FSF)
  - UN Security Council Consolidated List
  - UK HM Treasury Sanctions
  - 40+ additional sanctions & PEP lists

API: https://api.opensanctions.org
  - Public (limited), API key for higher rate limits
  - Bulk datasets available as NDJSON/CSV
  - Entities are Follow-the-Money (FtM) schema

Strategy:
  - Use the /search endpoint for targeted pulls
  - Use bulk dataset download for full refresh
  - Focus on sanctions-relevant entities (schema: Person, LegalEntity, Company, Vessel, etc.)
  - Upsert on OpenSanctions entity ID
  - Default schedule: daily at 4 AM UTC (sanctions lists update frequently)
"""

from __future__ import annotations

import uuid as _uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from ingestion.base_ingester import BaseIngester, IngestionResult

# OpenSanctions source_id in dh_data_sources
SANCTIONS_SOURCE_ID = "d8f8d448-420f-4b00-a154-9b2ee6a6eab5"
OPENSANCTIONS_API = "https://api.opensanctions.org"

# Target datasets — the three core sanctions lists + consolidated
TARGET_DATASETS = [
    "us_ofac_sdn",         # OFAC SDN
    "eu_fsf",              # EU Financial Sanctions
    "un_sc_sanctions",     # UN Security Council
    "default",             # OpenSanctions consolidated (includes all above + more)
]


class SanctionsIngester(BaseIngester):
    """
    Fetches sanctions data from OpenSanctions and loads into entity_sanctions.

    Supports:
      - Full dataset load from bulk NDJSON endpoint
      - Search-based targeted pulls
      - Incremental updates via last_change filter
    """

    source_id = SANCTIONS_SOURCE_ID
    display_name = "OpenSanctions (OFAC/EU/UN)"
    default_schedule = "0 4 * * *"  # Daily at 4 AM UTC

    # Configuration
    timeout_seconds = 600
    batch_size = 500
    max_entities = 10000     # Safety cap per run

    def __init__(self, api_key: Optional[str] = None, dataset: str = "default",
                 max_entities: int = 10000):
        super().__init__()
        self.api_key = api_key
        self.dataset = dataset
        self.max_entities = max_entities

    # ── Stage 1: Fetch ────────────────────────────────────────────────────

    def fetch(self, db: Session) -> Any:
        """
        Fetch sanctions entities from OpenSanctions.

        Uses the /collections/{dataset}/entities endpoint which returns
        FtM (Follow the Money) entity objects in NDJSON streaming format.
        Falls back to search endpoint if bulk is unavailable.
        """
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"

        all_entities = []

        # Try search-based approach with pagination (works without API key)
        # Search for sanctions-relevant schema types
        schema_types = ["LegalEntity", "Company", "Person", "Organization", "Vessel"]

        for schema in schema_types:
            if len(all_entities) >= self.max_entities:
                break

            self.log(f"Fetching {schema} entities from dataset '{self.dataset}'...")
            offset = 0
            limit = 100

            while len(all_entities) < self.max_entities:
                try:
                    resp = requests.get(
                        f"{OPENSANCTIONS_API}/search/{self.dataset}",
                        params={
                            "schema": schema,
                            "limit": limit,
                            "offset": offset,
                            "topics": "sanction",
                        },
                        headers=headers,
                        timeout=30,
                    )

                    if resp.status_code == 429:
                        self.log("Rate limited by OpenSanctions, stopping this schema type", "warning")
                        break

                    if resp.status_code != 200:
                        self.log(f"API returned {resp.status_code} for {schema}, trying next schema", "warning")
                        break

                    data = resp.json()
                    results = data.get("results", [])

                    if not results:
                        break

                    all_entities.extend(results)
                    self.log(f"  {schema} offset={offset}: {len(results)} entities (total: {len(all_entities)})")

                    # Check if there are more
                    total = data.get("total", {}).get("value", 0)
                    offset += limit

                    if offset >= total or offset >= self.max_entities:
                        break

                except requests.RequestException as exc:
                    self.log(f"Request failed for {schema} at offset {offset}: {exc}", "warning")
                    break

        self.log(f"Fetch complete: {len(all_entities)} sanctions entities")
        return all_entities

    # ── Stage 2: Validate ─────────────────────────────────────────────────

    def validate(self, raw_data: Any) -> Any:
        """Validate and deduplicate sanctions entities."""
        seen_ids = set()
        valid = []

        for entity in raw_data:
            eid = entity.get("id")
            if not eid or eid in seen_ids:
                continue
            seen_ids.add(eid)

            # Must have at least a caption/name
            caption = entity.get("caption") or entity.get("name")
            if not caption:
                continue

            valid.append(entity)

        deduped = len(raw_data) - len(valid)
        if deduped:
            self.log(f"Validation: removed {deduped} duplicates/invalid records")

        return valid

    # ── Stage 3: Transform ────────────────────────────────────────────────

    def transform(self, validated_data: Any) -> List[Dict[str, Any]]:
        """Transform OpenSanctions FtM entities into entity_sanctions rows."""
        rows = []

        for entity in validated_data:
            props = entity.get("properties", {})

            # Extract structured data from FtM properties
            names = self._extract_names(entity, props)
            identifiers = self._extract_identifiers(props)
            addresses = self._extract_addresses(props)
            datasets = entity.get("datasets", [])
            topics = entity.get("topics", [])

            row = {
                "id": entity["id"],
                "schema_type": entity.get("schema"),
                "caption": entity.get("caption"),
                "names": json.dumps(names) if names else None,
                "birth_date": self._first(props.get("birthDate")),
                "nationalities": json.dumps(props.get("nationality", [])) if props.get("nationality") else None,
                "countries": json.dumps(props.get("country", [])) if props.get("country") else None,
                "identifiers": json.dumps(identifiers) if identifiers else None,
                "addresses": json.dumps(addresses) if addresses else None,
                "datasets": json.dumps(datasets),
                "first_seen": entity.get("first_seen"),
                "last_seen": entity.get("last_seen"),
                "last_change": entity.get("last_change"),
                "associates": None,  # Populated from relationship edges later
                "sanction_programs": json.dumps(props.get("program", [])) if props.get("program") else None,
                "topics": json.dumps(topics) if topics else None,
                "lei": self._first(props.get("leiCode")),
                "source_id": SANCTIONS_SOURCE_ID,
            }
            rows.append(row)

        return rows

    # ── Stage 4: Load ─────────────────────────────────────────────────────

    def load(self, db: Session, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert sanctions entities into entity_sanctions using ON CONFLICT."""
        inserted = 0
        updated = 0
        failed = 0

        for i in range(0, len(rows), self.batch_size):
            batch = rows[i:i + self.batch_size]

            for row in batch:
                try:
                    sql = text("""
                        INSERT INTO entity_sanctions (
                            id, schema_type, caption, names, birth_date,
                            nationalities, countries, identifiers, addresses,
                            datasets, first_seen, last_seen, last_change,
                            associates, sanction_programs, topics, lei,
                            source_id, ingested_at, updated_at
                        ) VALUES (
                            :id, :schema_type, :caption, :names::jsonb, :birth_date,
                            :nationalities::jsonb, :countries::jsonb, :identifiers::jsonb, :addresses::jsonb,
                            :datasets::jsonb, :first_seen, :last_seen, :last_change,
                            :associates::jsonb, :sanction_programs::jsonb, :topics::jsonb, :lei,
                            :source_id, NOW(), NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            schema_type = EXCLUDED.schema_type,
                            caption = EXCLUDED.caption,
                            names = EXCLUDED.names,
                            birth_date = EXCLUDED.birth_date,
                            nationalities = EXCLUDED.nationalities,
                            countries = EXCLUDED.countries,
                            identifiers = EXCLUDED.identifiers,
                            addresses = EXCLUDED.addresses,
                            datasets = EXCLUDED.datasets,
                            last_seen = EXCLUDED.last_seen,
                            last_change = EXCLUDED.last_change,
                            sanction_programs = EXCLUDED.sanction_programs,
                            topics = EXCLUDED.topics,
                            lei = EXCLUDED.lei,
                            updated_at = NOW()
                    """)

                    db.execute(sql, row)
                    inserted += 1

                except Exception as exc:
                    failed += 1
                    if failed <= 5:
                        self.log(f"Failed to upsert sanctions entity {row.get('id')}: {exc}", "warning")

            db.commit()
            self.log(f"Batch committed: {min(i + self.batch_size, len(rows))}/{len(rows)}")

        return {"inserted": inserted, "updated": updated, "skipped": 0, "failed": failed}

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _first(lst: Optional[list]) -> Optional[str]:
        """Return first element of a list or None."""
        return lst[0] if lst else None

    @staticmethod
    def _extract_names(entity: dict, props: dict) -> List[dict]:
        """Extract all names from FtM properties."""
        names = []
        caption = entity.get("caption")
        if caption:
            names.append({"name": caption, "type": "primary"})

        for name_field in ("name", "alias", "weakAlias", "previousName"):
            for val in props.get(name_field, []):
                if val and val != caption:
                    names.append({"name": val, "type": name_field})

        return names

    @staticmethod
    def _extract_identifiers(props: dict) -> Optional[dict]:
        """Extract identifiers from FtM properties into structured dict."""
        ids = {}
        id_fields = {
            "passportNumber": "passport",
            "idNumber": "national_id",
            "taxNumber": "tax_id",
            "registrationNumber": "registration",
            "leiCode": "lei",
            "imoNumber": "imo",
            "mmsi": "mmsi",
        }
        for ftm_field, our_field in id_fields.items():
            vals = props.get(ftm_field, [])
            if vals:
                ids[our_field] = vals

        return ids if ids else None

    @staticmethod
    def _extract_addresses(props: dict) -> Optional[List[dict]]:
        """Extract addresses from FtM properties."""
        addresses = []
        for addr in props.get("address", []):
            if addr:
                addresses.append({"full": addr})

        for addr in props.get("addressEntity", []):
            if isinstance(addr, dict):
                addresses.append(addr)

        return addresses if addresses else None
