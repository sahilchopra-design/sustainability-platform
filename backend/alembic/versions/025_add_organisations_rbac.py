"""Add organisations table + RBAC columns to users_pg

Revision ID: 025_add_organisations_rbac
Revises: 024_engagement_tracker
Create Date: 2026-03-04

Tables created:
  organisations         — multi-tenant organisation registry (bank, insurer, AM, energy, RE)
  user_roles            — ENUM: admin | portfolio_manager | risk_analyst | viewer | compliance | data_engineer

Columns added to existing tables (all idempotent DO $$ guards):
  users_pg.org_id          UUID FK → organisations.id  (nullable — existing users unassigned)
  users_pg.role            TEXT    default 'viewer'
  users_pg.is_active       BOOLEAN default true
  users_pg.last_login      TIMESTAMPTZ nullable
  portfolios_pg.org_id     UUID FK → organisations.id  (nullable — no forced migration of live data)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "025_add_organisations_rbac"
down_revision = "024_engagement_tracker"
branch_labels = None
depends_on = None

_VALID_ORG_TYPES = (
    "bank", "investment_bank", "insurance", "asset_manager", "pension_fund",
    "energy_developer", "real_estate", "supply_chain", "technology",
    "regulator", "consultancy", "other",
)

_VALID_ROLES = (
    "admin", "portfolio_manager", "risk_analyst", "viewer", "compliance", "data_engineer",
)


def upgrade():
    # ── organisations ──────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS organisations (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name           VARCHAR(500)  NOT NULL,
            org_type       VARCHAR(50)   NOT NULL DEFAULT 'other',
                               -- bank | insurance | asset_manager | energy_developer |
                               -- real_estate | supply_chain | technology | regulator | other
            jurisdiction   CHAR(3),                               -- ISO 3166-1 alpha-3
            subscription_tier VARCHAR(20) DEFAULT 'professional', -- basic | professional | institutional
            is_active      BOOLEAN NOT NULL DEFAULT true,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_organisations_org_type ON organisations (org_type);
    """)

    # ── Add org_id + role + is_active + last_login to users_pg ────────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users_pg' AND column_name = 'org_id'
            ) THEN
                ALTER TABLE users_pg ADD COLUMN org_id UUID REFERENCES organisations(id) ON DELETE SET NULL;
            END IF;
        END
        $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users_pg' AND column_name = 'role'
            ) THEN
                ALTER TABLE users_pg ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'viewer';
                COMMENT ON COLUMN users_pg.role IS
                    'RBAC role: admin | portfolio_manager | risk_analyst | viewer | compliance | data_engineer';
            END IF;
        END
        $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users_pg' AND column_name = 'is_active'
            ) THEN
                ALTER TABLE users_pg ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
            END IF;
        END
        $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users_pg' AND column_name = 'last_login'
            ) THEN
                ALTER TABLE users_pg ADD COLUMN last_login TIMESTAMPTZ;
            END IF;
        END
        $$;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_pg_org_id ON users_pg (org_id);
        CREATE INDEX IF NOT EXISTS idx_users_pg_role   ON users_pg (role);
    """)

    # ── Add org_id to portfolios_pg (row-level tenant isolation) ──────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'portfolios_pg' AND column_name = 'org_id'
            ) THEN
                ALTER TABLE portfolios_pg ADD COLUMN org_id UUID REFERENCES organisations(id) ON DELETE SET NULL;
                COMMENT ON COLUMN portfolios_pg.org_id IS 'Tenant isolation: all portfolio queries should filter by org_id';
            END IF;
        END
        $$;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_portfolios_pg_org_id ON portfolios_pg (org_id);
    """)

    # ── Add org_id to csrd_entity_registry for tenant scope ───────────────────
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name = 'csrd_entity_registry'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'csrd_entity_registry' AND column_name = 'org_id'
            ) THEN
                ALTER TABLE csrd_entity_registry
                    ADD COLUMN org_id UUID REFERENCES organisations(id) ON DELETE SET NULL;
            END IF;
        END
        $$;
    """)

    # ── Default "platform" organisation so existing data remains accessible ───
    op.execute("""
        INSERT INTO organisations (id, name, org_type, subscription_tier)
        VALUES ('00000000-0000-0000-0000-000000000001', 'Platform Default', 'other', 'institutional')
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade():
    # Remove org_id from csrd_entity_registry
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'csrd_entity_registry' AND column_name = 'org_id')
            THEN ALTER TABLE csrd_entity_registry DROP COLUMN org_id;
            END IF;
        END $$;
    """)

    # Remove org_id from portfolios_pg
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'portfolios_pg' AND column_name = 'org_id')
            THEN
                DROP INDEX IF EXISTS idx_portfolios_pg_org_id;
                ALTER TABLE portfolios_pg DROP COLUMN org_id;
            END IF;
        END $$;
    """)

    # Remove columns from users_pg
    op.execute("""
        DO $$
        BEGIN
            DROP INDEX IF EXISTS idx_users_pg_org_id;
            DROP INDEX IF EXISTS idx_users_pg_role;
        END $$;
    """)
    for col in ("last_login", "is_active", "role", "org_id"):
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name = 'users_pg' AND column_name = '{col}')
                THEN ALTER TABLE users_pg DROP COLUMN {col};
                END IF;
            END $$;
        """)

    op.execute("DROP INDEX IF EXISTS idx_organisations_org_type;")
    op.execute("DROP TABLE IF EXISTS organisations;")
