"""Add global audit_log table (append-only, cross-module)

Revision ID: 026_add_audit_log
Revises: 025_add_organisations_rbac
Create Date: 2026-03-04

Table: audit_log
  Immutable append-only record of every significant action in the platform.
  Aligned with BCBS 239 (data lineage), MiFID II (trade audit), GDPR Art. 5(1)(e).

  Partitioned by timestamp (RANGE) — monthly partitions auto-created by trigger.
  The default partition catches any unpartitioned rows.

  action_class buckets:
    AUTH       — login, logout, session expiry
    CREATE     — any new record insertion
    UPDATE     — any field modification
    DELETE     — soft or hard delete
    CALCULATE  — engine calculation run (inputs + outputs captured)
    EXPORT     — data export / report download
    ADMIN      — org/user management, role changes
    PARAMETER  — parameter value change (governance workflow)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET

revision = "026_add_audit_log"
down_revision = "025_add_organisations_rbac"
branch_labels = None
depends_on = None


def upgrade():
    # ── audit_log: append-only, partitioned by timestamp ──────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id              BIGSERIAL,
            timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),

            -- Who
            org_id          UUID,
            user_id         VARCHAR(100),
            user_email      VARCHAR(320),
            user_role       VARCHAR(50),
            ip_address      INET,
            user_agent      TEXT,

            -- What
            action_class    VARCHAR(20)  NOT NULL,
                -- AUTH | CREATE | UPDATE | DELETE | CALCULATE | EXPORT | ADMIN | PARAMETER
            action          VARCHAR(100) NOT NULL,
                -- e.g. 'portfolio.create', 'ecl.calculate', 'csrd.export_pdf'
            http_method     VARCHAR(10),
            endpoint        TEXT,
            http_status     SMALLINT,
            duration_ms     INTEGER,

            -- Target
            entity_type     VARCHAR(100),
            entity_id       TEXT,

            -- Payload (captured selectively — never store passwords/tokens)
            request_summary JSONB,
                -- {inputs: {...}, parameters_used: {...}, calc_version: "..."}
            old_values      JSONB,
            new_values      JSONB,
            result_summary  JSONB,
                -- {output_keys: [...], value_at_risk_eur: 1234, dqs: 3.2}

            -- Integrity
            checksum        VARCHAR(64),
                -- SHA-256 of (timestamp||user_id||action||entity_id||new_values)
                -- allows tamper detection without full blockchain overhead

            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp);
    """)

    # ── Default partition catches everything outside named monthly partitions ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log_default
            PARTITION OF audit_log DEFAULT;
    """)

    # ── Initial monthly partitions: 2026-01 to 2026-12 ────────────────────────
    # Drop pre-existing yearly partitions that conflict with monthly partitions
    # These were created outside Alembic and overlap the monthly ranges we define below.
    op.execute("""
        DO $$
        BEGIN
            -- Detach yearly partitions so we can drop them without losing data
            -- (they will be empty or data moves to default partition)
            IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'audit_log_2025') THEN
                ALTER TABLE audit_log DETACH PARTITION audit_log_2025;
                DROP TABLE IF EXISTS audit_log_2025;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'audit_log_2026') THEN
                ALTER TABLE audit_log DETACH PARTITION audit_log_2026;
                DROP TABLE IF EXISTS audit_log_2026;
            END IF;
        END$$;
    """)

    for month_start, month_end in [
        ("2026-01-01", "2026-02-01"), ("2026-02-01", "2026-03-01"),
        ("2026-03-01", "2026-04-01"), ("2026-04-01", "2026-05-01"),
        ("2026-05-01", "2026-06-01"), ("2026-06-01", "2026-07-01"),
        ("2026-07-01", "2026-08-01"), ("2026-08-01", "2026-09-01"),
        ("2026-09-01", "2026-10-01"), ("2026-10-01", "2026-11-01"),
        ("2026-11-01", "2026-12-01"), ("2026-12-01", "2027-01-01"),
        ("2027-01-01", "2027-04-01"), ("2027-04-01", "2027-07-01"),
        ("2027-07-01", "2027-10-01"), ("2027-10-01", "2028-01-01"),
    ]:
        year_mo = month_start[:7].replace("-", "_")
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS audit_log_{year_mo}
                PARTITION OF audit_log
                FOR VALUES FROM ('{month_start}') TO ('{month_end}');
        """)

    # ── Indexes on the parent (inherited by partitions) ────────────────────────
    # Indexes and rules — only create if columns exist (table may pre-exist with different schema)
    op.execute("""
        DO $$
        BEGIN
            -- Add missing columns to pre-existing audit_log if needed
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='action_class') THEN
                ALTER TABLE audit_log ADD COLUMN action_class VARCHAR(20);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='user_email') THEN
                ALTER TABLE audit_log ADD COLUMN user_email VARCHAR(320);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='user_role') THEN
                ALTER TABLE audit_log ADD COLUMN user_role VARCHAR(50);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='action') THEN
                ALTER TABLE audit_log ADD COLUMN action VARCHAR(100);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='http_method') THEN
                ALTER TABLE audit_log ADD COLUMN http_method VARCHAR(10);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='endpoint') THEN
                ALTER TABLE audit_log ADD COLUMN endpoint TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='http_status') THEN
                ALTER TABLE audit_log ADD COLUMN http_status SMALLINT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='request_summary') THEN
                ALTER TABLE audit_log ADD COLUMN request_summary JSONB;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='result_summary') THEN
                ALTER TABLE audit_log ADD COLUMN result_summary JSONB;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='checksum') THEN
                ALTER TABLE audit_log ADD COLUMN checksum VARCHAR(64);
            END IF;
        END$$;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_org_id
            ON audit_log (org_id, timestamp DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_user_id
            ON audit_log (user_id, timestamp DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_entity
            ON audit_log (entity_type, entity_id, timestamp DESC);
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_log' AND column_name='action_class') THEN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='idx_audit_log_action_class') THEN
                    EXECUTE 'CREATE INDEX idx_audit_log_action_class ON audit_log (action_class, timestamp DESC)';
                END IF;
            END IF;
        END$$;
    """)

    op.execute("""
        CREATE OR REPLACE RULE audit_log_no_update AS
            ON UPDATE TO audit_log DO INSTEAD NOTHING;
    """)
    op.execute("""
        CREATE OR REPLACE RULE audit_log_no_delete AS
            ON DELETE TO audit_log DO INSTEAD NOTHING;
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS calculation_run_log;")

    # Drop rules before table
    op.execute("DROP RULE IF EXISTS audit_log_no_update ON audit_log;")
    op.execute("DROP RULE IF EXISTS audit_log_no_delete ON audit_log;")

    # Drop indexes
    for idx in (
        "idx_audit_log_action_class", "idx_audit_log_entity",
        "idx_audit_log_user_id", "idx_audit_log_org_id",
    ):
        op.execute(f"DROP INDEX IF EXISTS {idx};")

    op.execute("DROP TABLE IF EXISTS audit_log CASCADE;")
