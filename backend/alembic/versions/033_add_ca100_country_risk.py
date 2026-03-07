"""033 – CA100+ assessments + country risk/governance indices.

Creates:
  - dh_ca100_assessments      : Climate Action 100+ Net Zero Company Benchmark scores
  - dh_country_risk_indices   : Unified country-level risk & governance indices
                                (CPI, FSI, Freedom House FIW, UNDP GII)

Registers 7 new data sources in dh_data_sources.
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

revision = "033_add_ca100_country_risk"
down_revision = "032_add_gdelt_controversy_tables"
branch_labels = None
depends_on = None


def upgrade():
    # ── dh_ca100_assessments ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS dh_ca100_assessments (
            id                  TEXT PRIMARY KEY,
            source_id           TEXT,
            company_name        TEXT NOT NULL,
            isin                TEXT,
            hq_location         TEXT,
            hq_region           TEXT,
            sector_cluster      TEXT,
            sector              TEXT,
            secondary_sector    TEXT,
            scope3_category     TEXT,
            indicator_1_score   TEXT,
            indicator_2_score   TEXT,
            indicator_3_score   TEXT,
            indicator_4_score   TEXT,
            indicator_5_score   TEXT,
            indicator_6_score   TEXT,
            indicator_7_score   TEXT,
            indicator_8_score   TEXT,
            indicator_9_score   TEXT,
            indicator_10_score  TEXT,
            overall_assessment  TEXT,
            assessment_year     INTEGER DEFAULT 2025,
            raw_record          JSONB,
            ingested_at         TIMESTAMPTZ DEFAULT now(),
            updated_at          TIMESTAMPTZ DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ca100_isin ON dh_ca100_assessments (isin);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ca100_sector ON dh_ca100_assessments (sector_cluster, sector);
    """)

    # ── dh_country_risk_indices ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS dh_country_risk_indices (
            id              TEXT PRIMARY KEY,
            source_id       TEXT,
            country_name    TEXT NOT NULL,
            country_iso3    VARCHAR(3),
            country_iso2    VARCHAR(2),
            index_name      TEXT NOT NULL,
            year            INTEGER NOT NULL,
            score           DOUBLE PRECISION,
            rank            INTEGER,
            subcategories   JSONB,
            source_name     TEXT,
            ingested_at     TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now(),
            UNIQUE(country_iso3, index_name, year)
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_cri_country ON dh_country_risk_indices (country_iso3);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_cri_index ON dh_country_risk_indices (index_name, year);
    """)

    # ── Register data sources ────────────────────────────────────────────────
    sources = [
        ("ds-sbti-companies-xlsx", "SBTi Companies (XLSX)", "ESG", "API/File"),
        ("ds-ca100-benchmark-2025", "Climate Action 100+ Benchmark 2025", "ESG", "File"),
        ("ds-gem-coal-tracker-country", "GEM Coal Plant Tracker (Country)", "Energy", "File"),
        ("ds-ti-cpi-2023", "Transparency International CPI 2023", "Governance", "File"),
        ("ds-fsi-2023", "Fragile States Index 2023", "Governance", "File"),
        ("ds-freedom-house-fiw", "Freedom House FIW 2013-2024", "Governance", "File"),
        ("ds-undp-hdr-gii", "UNDP HDR Gender Inequality Index", "Social", "File"),
    ]
    for sid, name, cat, access in sources:
        op.execute(f"""
            INSERT INTO dh_data_sources (id, name, category, access_type, sync_enabled, created_at, updated_at)
            VALUES ('{sid}', '{name}', '{cat}', '{access}', false, now(), now())
            ON CONFLICT (id) DO NOTHING;
        """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS dh_country_risk_indices CASCADE;")
    op.execute("DROP TABLE IF EXISTS dh_ca100_assessments CASCADE;")
    for sid in [
        "ds-sbti-companies-xlsx", "ds-ca100-benchmark-2025",
        "ds-gem-coal-tracker-country", "ds-ti-cpi-2023",
        "ds-fsi-2023", "ds-freedom-house-fiw", "ds-undp-hdr-gii",
    ]:
        op.execute(f"DELETE FROM dh_data_sources WHERE id = '{sid}';")
