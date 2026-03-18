"""
Data Preview & Inter-Table Relationship API
=============================================
Endpoints for:
  1. Listing all database tables with row counts and column metadata
  2. Fetching first 100 rows of any table (data preview)
  3. Discovering foreign key relationships (inter-table links)
  4. Building inter-module datapoint-level mapping with relationship categories
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

router = APIRouter(prefix="/api/v1/data-preview", tags=["Data Preview"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    row_count: int
    column_count: int
    columns: list[dict]  # [{name, type, nullable, is_pk}]
    size_bytes: Optional[int] = None


class TablePreview(BaseModel):
    schema_name: str
    table_name: str
    columns: list[str]
    column_types: list[str]
    rows: list[dict]
    total_rows: int
    preview_rows: int


class ForeignKeyRelation(BaseModel):
    constraint_name: str
    source_schema: str
    source_table: str
    source_column: str
    target_schema: str
    target_table: str
    target_column: str
    relationship_type: str  # "belongs_to", "has_many", "many_to_many", "references"
    module_source: str
    module_target: str


class DatapointMapping(BaseModel):
    source_table: str
    source_column: str
    source_type: str
    target_table: str
    target_column: str
    target_type: str
    relationship_category: str  # "identity_link", "financial_metric", "risk_indicator", "temporal_join", "spatial_join", "classification", "aggregation_source"
    mapping_confidence: str  # "exact_fk", "inferred_name", "semantic_match"
    module_source: str
    module_target: str


# ---------------------------------------------------------------------------
# Module classification for tables
# ---------------------------------------------------------------------------

TABLE_MODULE_MAP: dict[str, str] = {
    # Portfolio
    "portfolios_pg": "portfolio", "assets_pg": "portfolio", "analysis_runs_pg": "portfolio",
    "portfolios": "portfolio",
    # Carbon
    "carbon_methodologies": "carbon", "carbon_emission_factors": "carbon",
    "carbon_portfolios": "carbon", "carbon_projects": "carbon",
    "carbon_scenarios": "carbon", "carbon_calculations": "carbon", "carbon_reports": "carbon",
    # CBAM
    "cbam_product_categories": "cbam", "cbam_suppliers": "cbam",
    "cbam_embedded_emissions": "cbam", "cbam_cost_projections": "cbam",
    "cbam_compliance_reports": "cbam", "cbam_country_risks": "cbam",
    # ECL / Financial Risk
    "ecl_assessments": "ecl", "ecl_exposures": "ecl",
    "ecl_scenario_results": "ecl", "ecl_climate_overlays": "ecl",
    "pcaf_portfolios": "pcaf", "pcaf_investees": "pcaf", "pcaf_results": "pcaf",
    "temperature_scores": "pcaf",
    # Supply Chain
    "sc_entities": "supply_chain", "scope3_assessments": "supply_chain",
    "scope3_activities": "supply_chain", "sbti_targets": "supply_chain",
    "sbti_trajectories": "supply_chain", "emission_factor_library": "supply_chain",
    "supply_chain_tiers": "supply_chain",
    # Sector Assessments
    "data_centre_facilities": "sector", "data_centre_assessments": "sector",
    "cat_risk_properties": "sector", "cat_risk_assessments": "sector",
    "cat_risk_climate_scenarios": "sector",
    "power_plants": "sector", "power_plant_assessments": "sector",
    "power_plant_trajectories": "sector",
    # Regulatory
    "regulatory_entities": "regulatory", "sfdr_pai_disclosures": "regulatory",
    "eu_taxonomy_assessments": "regulatory", "eu_taxonomy_activities": "regulatory",
    "tcfd_assessments": "regulatory", "csrd_readiness": "regulatory",
    "issb_assessments": "regulatory", "brsr_disclosures": "regulatory",
    "sf_taxonomy_alignments": "regulatory", "regulatory_action_plans": "regulatory",
    # Valuation
    "valuation_assets": "valuation", "unified_valuations": "valuation",
    "method_results": "valuation", "esg_adjustments": "valuation",
    "comparable_sales": "valuation",
    # Nature
    "nature_assessments": "nature",
    # CSRD
    "csrd_entity_registry": "csrd", "csrd_framework_applicability": "csrd",
    "csrd_esrs_catalog": "csrd", "csrd_kpi_values": "csrd",
    "csrd_materiality_topics": "csrd", "csrd_disclosure_index": "csrd",
    "csrd_peer_benchmarks": "csrd", "csrd_gap_tracker": "csrd",
    "csrd_data_lineage": "csrd", "csrd_assurance_log": "csrd",
    "csrd_action_tracker": "csrd", "csrd_target_registry": "csrd",
    "csrd_transition_plan": "csrd", "csrd_report_uploads": "csrd",
    # ESRS / ISSB
    "esrs2_general_disclosures": "esrs", "esrs_e1_energy": "esrs",
    "esrs_e1_ghg_emissions": "esrs", "esrs_e1_ghg_removals": "esrs",
    "esrs_e1_carbon_price": "esrs", "esrs_e1_financial_effects": "esrs",
    "esrs_e2_pollution": "esrs", "esrs_e3_water": "esrs",
    "esrs_e4_biodiversity": "esrs", "esrs_e5_circular": "esrs",
    "esrs_s1_workforce": "esrs", "esrs_g1_conduct": "esrs",
    "issb_s1_general": "issb", "issb_s2_climate": "issb",
    "issb_sasb_industry_metrics": "issb", "issb_s2_scenario_analysis": "issb",
    "issb_s2_offset_plan": "issb", "issb_disclosure_relief_tracker": "issb",
    "issb_risk_opportunity_register": "issb", "issb_s2_time_horizons": "issb",
    # Financial Institutions
    "fi_entities": "fi", "fi_financials": "fi", "fi_loan_books": "fi",
    "fi_green_finance": "fi", "fi_financed_emissions": "fi",
    "fi_paris_alignment": "fi", "fi_csrd_e1_climate": "fi",
    "fi_csrd_s1_workforce": "fi", "fi_csrd_g1_governance": "fi",
    "fi_eu_taxonomy_kpis": "fi",
    # Energy
    "energy_entities": "energy", "energy_financials": "energy",
    "energy_generation_mix": "energy",
    "energy_csrd_e1_climate": "energy", "energy_csrd_e2_pollution": "energy",
    "energy_csrd_e3_water": "energy", "energy_csrd_e4_biodiversity": "energy",
    "energy_csrd_e5_circular": "energy", "energy_csrd_s1_workforce": "energy",
    "energy_csrd_g1_governance": "energy",
    "energy_renewable_pipeline": "energy", "energy_stranded_assets_register": "energy",
    # Data Hub
    "data_hub_sources": "data_hub", "data_hub_scenarios": "data_hub",
    "data_hub_trajectories": "data_hub",
    # Scenarios
    "scenarios": "scenario", "scenario_versions": "scenario",
    "ngfs_data_sources": "scenario", "ngfs_scenarios": "scenario",
    # Auth
    "users_pg": "auth", "user_sessions_pg": "auth",
    # Audit
    "audit_log": "audit",
    # Alembic
    "alembic_version": "system",
}


def _classify_module(table_name: str) -> str:
    """Classify a table into its module based on naming convention."""
    if table_name in TABLE_MODULE_MAP:
        return TABLE_MODULE_MAP[table_name]
    # Fallback heuristics
    prefixes = [
        ("csrd_", "csrd"), ("esrs_", "esrs"), ("issb_", "issb"),
        ("fi_", "fi"), ("energy_", "energy"), ("ecl_", "ecl"),
        ("pcaf_", "pcaf"), ("cbam_", "cbam"), ("carbon_", "carbon"),
        ("sc_", "supply_chain"), ("scope3_", "supply_chain"),
        ("sbti_", "supply_chain"), ("cat_risk_", "sector"),
        ("data_hub_", "data_hub"), ("ngfs_", "scenario"),
        ("re_", "real_estate"), ("valuation_", "valuation"),
    ]
    for prefix, module in prefixes:
        if table_name.startswith(prefix):
            return module
    return "other"


def _classify_relationship(source_col: str, target_col: str, source_table: str, target_table: str) -> str:
    """Categorize the relationship type based on column/table names."""
    col_lower = source_col.lower()
    # Identity links
    if col_lower.endswith("_id") and ("entity" in col_lower or "registry" in col_lower):
        return "identity_link"
    if col_lower in ("entity_id", "entity_registry_id", "company_id", "counterparty_id"):
        return "identity_link"
    # Temporal
    if any(t in col_lower for t in ("date", "timestamp", "period", "year", "quarter")):
        return "temporal_join"
    # Financial metrics
    if any(t in col_lower for t in ("amount", "eur", "usd", "premium", "exposure", "loss")):
        return "financial_metric"
    # Risk indicators
    if any(t in col_lower for t in ("risk", "pd", "lgd", "ead", "ecl", "var", "score")):
        return "risk_indicator"
    # Classification
    if any(t in col_lower for t in ("type", "category", "sector", "class", "tier", "rating")):
        return "classification"
    # Spatial
    if any(t in col_lower for t in ("country", "region", "lat", "lng", "location")):
        return "spatial_join"
    # Default
    return "aggregation_source"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/tables", summary="List all database tables with metadata")
def list_tables(schema: str = "public", db: Session = Depends(get_db)):
    """List all tables in the given schema with row counts and column info."""
    # Get tables
    tables_query = text("""
        SELECT
            t.table_schema,
            t.table_name,
            (SELECT count(*) FROM information_schema.columns c
             WHERE c.table_schema = t.table_schema AND c.table_name = t.table_name) as col_count
        FROM information_schema.tables t
        WHERE t.table_schema = :schema AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name
    """)
    tables = db.execute(tables_query, {"schema": schema}).fetchall()

    result = []
    for row in tables:
        table_name = row[1]
        col_count = row[2]

        # Get row count (approximate for speed)
        try:
            count_q = text(f'SELECT count(*) FROM "{schema}"."{table_name}"')
            row_count = db.execute(count_q).scalar() or 0
        except Exception:
            row_count = 0

        # Get column details
        cols_query = text("""
            SELECT column_name, data_type, is_nullable,
                   CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_pk
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = :schema
                  AND tc.table_name = :table
                  AND tc.constraint_type = 'PRIMARY KEY'
            ) pk ON pk.column_name = c.column_name
            WHERE c.table_schema = :schema AND c.table_name = :table
            ORDER BY c.ordinal_position
        """)
        cols = db.execute(cols_query, {"schema": schema, "table": table_name}).fetchall()
        columns = [
            {"name": c[0], "type": c[1], "nullable": c[2] == "YES", "is_pk": c[3]}
            for c in cols
        ]

        # Get table size
        try:
            size_q = text(f"SELECT pg_total_relation_size('{schema}.{table_name}')")
            size_bytes = db.execute(size_q).scalar() or 0
        except Exception:
            size_bytes = 0

        result.append({
            "schema_name": schema,
            "table_name": table_name,
            "module": _classify_module(table_name),
            "row_count": row_count,
            "column_count": col_count,
            "columns": columns,
            "size_bytes": size_bytes,
        })

    return {"tables": result, "total_tables": len(result)}


@router.get("/tables/{table_name}/preview", summary="Preview first 100 rows of a table")
def preview_table(table_name: str, schema: str = "public", limit: int = 100, db: Session = Depends(get_db)):
    """Fetch the first N rows (max 100) from a database table."""
    if limit > 100:
        limit = 100

    # Validate table exists
    check = text("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = :schema AND table_name = :table AND table_type = 'BASE TABLE'
    """)
    exists = db.execute(check, {"schema": schema, "table": table_name}).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Table '{schema}.{table_name}' not found")

    # Get columns
    cols_query = text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
        ORDER BY ordinal_position
    """)
    cols = db.execute(cols_query, {"schema": schema, "table": table_name}).fetchall()
    col_names = [c[0] for c in cols]
    col_types = [c[1] for c in cols]

    # Get total count
    count_q = text(f'SELECT count(*) FROM "{schema}"."{table_name}"')
    total_rows = db.execute(count_q).scalar() or 0

    # Fetch rows
    data_q = text(f'SELECT * FROM "{schema}"."{table_name}" LIMIT :lim')
    rows = db.execute(data_q, {"lim": limit}).fetchall()

    # Convert to list of dicts
    row_dicts = []
    for r in rows:
        row_dict = {}
        for i, val in enumerate(r):
            key = col_names[i] if i < len(col_names) else f"col_{i}"
            # Serialize non-JSON types
            if val is not None and not isinstance(val, (str, int, float, bool)):
                row_dict[key] = str(val)
            else:
                row_dict[key] = val
        row_dicts.append(row_dict)

    return {
        "schema_name": schema,
        "table_name": table_name,
        "module": _classify_module(table_name),
        "columns": col_names,
        "column_types": col_types,
        "rows": row_dicts,
        "total_rows": total_rows,
        "preview_rows": len(row_dicts),
    }


@router.get("/relationships", summary="Discover all foreign key relationships")
def get_relationships(schema: str = "public", db: Session = Depends(get_db)):
    """Get all FK relationships between tables, classified by module and type."""
    fk_query = text("""
        SELECT
            tc.constraint_name,
            tc.table_schema AS source_schema,
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_schema AS target_schema,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name
          AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = :schema
        ORDER BY tc.table_name, kcu.column_name
    """)
    fks = db.execute(fk_query, {"schema": schema}).fetchall()

    relationships = []
    for fk in fks:
        source_table = fk[2]
        target_table = fk[5]
        source_col = fk[3]
        target_col = fk[6]

        source_module = _classify_module(source_table)
        target_module = _classify_module(target_table)

        # Determine relationship type
        if source_module == target_module:
            rel_type = "has_many"  # intra-module parent-child
        else:
            rel_type = "references"  # cross-module FK

        relationships.append({
            "constraint_name": fk[0],
            "source_schema": fk[1],
            "source_table": source_table,
            "source_column": source_col,
            "target_schema": fk[4],
            "target_table": target_table,
            "target_column": target_col,
            "relationship_type": rel_type,
            "module_source": source_module,
            "module_target": target_module,
            "is_cross_module": source_module != target_module,
        })

    # Build module adjacency
    module_links = {}
    for r in relationships:
        key = f"{r['module_source']} -> {r['module_target']}"
        if key not in module_links:
            module_links[key] = {"source": r["module_source"], "target": r["module_target"], "link_count": 0, "tables": []}
        module_links[key]["link_count"] += 1
        module_links[key]["tables"].append(f"{r['source_table']}.{r['source_column']} -> {r['target_table']}.{r['target_column']}")

    return {
        "relationships": relationships,
        "total_relationships": len(relationships),
        "cross_module_count": sum(1 for r in relationships if r["is_cross_module"]),
        "module_adjacency": list(module_links.values()),
    }


@router.get("/datapoint-mappings", summary="Get inter-table datapoint-level mappings with categories")
def get_datapoint_mappings(schema: str = "public", db: Session = Depends(get_db)):
    """
    Build datapoint-level mapping between tables:
    1. Exact FK matches
    2. Inferred name-based matches (columns sharing names across tables)
    3. Semantic matches (columns with related business meaning)

    Each mapping is categorized:
    - identity_link: entity/counterparty IDs
    - financial_metric: monetary amounts, rates
    - risk_indicator: PD, LGD, VaR, scores
    - temporal_join: date/period columns
    - spatial_join: country/region/coordinates
    - classification: sector, type, category
    - aggregation_source: roll-up / summary links
    """
    # 1. FK-based exact mappings
    fk_query = text("""
        SELECT
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            (SELECT data_type FROM information_schema.columns c
             WHERE c.table_schema = :schema AND c.table_name = tc.table_name AND c.column_name = kcu.column_name) AS source_type,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column,
            (SELECT data_type FROM information_schema.columns c
             WHERE c.table_schema = :schema AND c.table_name = ccu.table_name AND c.column_name = ccu.column_name) AS target_type
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = :schema
    """)
    fks = db.execute(fk_query, {"schema": schema}).fetchall()

    mappings = []
    seen_pairs = set()

    for fk in fks:
        src_table, src_col, src_type, tgt_table, tgt_col, tgt_type = fk
        pair_key = f"{src_table}.{src_col}->{tgt_table}.{tgt_col}"
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        category = _classify_relationship(src_col, tgt_col, src_table, tgt_table)
        mappings.append({
            "source_table": src_table,
            "source_column": src_col,
            "source_type": src_type or "unknown",
            "target_table": tgt_table,
            "target_column": tgt_col,
            "target_type": tgt_type or "unknown",
            "relationship_category": category,
            "mapping_confidence": "exact_fk",
            "module_source": _classify_module(src_table),
            "module_target": _classify_module(tgt_table),
        })

    # 2. Name-based inferred mappings (same column name across different tables)
    name_query = text("""
        SELECT c1.table_name, c1.column_name, c1.data_type,
               c2.table_name, c2.column_name, c2.data_type
        FROM information_schema.columns c1
        JOIN information_schema.columns c2
          ON c1.column_name = c2.column_name
          AND c1.table_schema = c2.table_schema
          AND c1.table_name < c2.table_name
        WHERE c1.table_schema = :schema
          AND c1.column_name NOT IN ('id', 'created_at', 'updated_at')
          AND c1.column_name LIKE '%_id'
        ORDER BY c1.column_name, c1.table_name
        LIMIT 500
    """)
    name_matches = db.execute(name_query, {"schema": schema}).fetchall()

    for nm in name_matches:
        pair_key = f"{nm[0]}.{nm[1]}->{nm[3]}.{nm[4]}"
        reverse_key = f"{nm[3]}.{nm[4]}->{nm[0]}.{nm[1]}"
        if pair_key in seen_pairs or reverse_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        category = _classify_relationship(nm[1], nm[4], nm[0], nm[3])
        mappings.append({
            "source_table": nm[0],
            "source_column": nm[1],
            "source_type": nm[2] or "unknown",
            "target_table": nm[3],
            "target_column": nm[4],
            "target_type": nm[5] or "unknown",
            "relationship_category": category,
            "mapping_confidence": "inferred_name",
            "module_source": _classify_module(nm[0]),
            "module_target": _classify_module(nm[3]),
        })

    # Aggregate by category
    category_summary = {}
    for m in mappings:
        cat = m["relationship_category"]
        category_summary[cat] = category_summary.get(cat, 0) + 1

    # Aggregate by module pair
    module_pair_summary = {}
    for m in mappings:
        pair = f"{m['module_source']} <-> {m['module_target']}"
        if pair not in module_pair_summary:
            module_pair_summary[pair] = {"count": 0, "categories": set()}
        module_pair_summary[pair]["count"] += 1
        module_pair_summary[pair]["categories"].add(m["relationship_category"])

    # Serialize sets to lists
    for k in module_pair_summary:
        module_pair_summary[k]["categories"] = list(module_pair_summary[k]["categories"])

    return {
        "mappings": mappings,
        "total_mappings": len(mappings),
        "by_category": category_summary,
        "by_confidence": {
            "exact_fk": sum(1 for m in mappings if m["mapping_confidence"] == "exact_fk"),
            "inferred_name": sum(1 for m in mappings if m["mapping_confidence"] == "inferred_name"),
        },
        "module_pair_summary": module_pair_summary,
    }


@router.get("/modules", summary="List all modules and their tables")
def get_modules(schema: str = "public", db: Session = Depends(get_db)):
    """Get all modules with their constituent tables."""
    tables_query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = db.execute(tables_query, {"schema": schema}).fetchall()

    modules = {}
    for row in tables:
        table_name = row[0]
        module = _classify_module(table_name)
        if module not in modules:
            modules[module] = {"module": module, "tables": [], "table_count": 0}
        modules[module]["tables"].append(table_name)
        modules[module]["table_count"] += 1

    return {"modules": list(modules.values()), "total_modules": len(modules)}
