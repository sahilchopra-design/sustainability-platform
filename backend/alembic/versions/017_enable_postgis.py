"""Enable PostGIS extension and add spatial columns to risk tables

Revision ID: 017
Revises: 016
Create Date: 2026-03-03

Adds:
  - PostGIS extension (idempotent — safe to run if already enabled)
  - GEOGRAPHY(POINT, 4326) column on nature_risk_sites
  - GEOGRAPHY(POINT, 4326) column on cat_risk_properties
  - GEOGRAPHY(POINT, 4326) column on power_plant_assets
  - GIST spatial indexes on each
"""
from alembic import op
import sqlalchemy as sa

revision = "017_enable_postgis"
down_revision = "016_add_csrd_report_uploads"
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS (idempotent — IF NOT EXISTS)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # ── nature_risk_sites ──────────────────────────────────────────────────────
    # Check and add location column only if the table exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'nature_risk_sites'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'nature_risk_sites' AND column_name = 'location'
            ) THEN
                ALTER TABLE nature_risk_sites
                    ADD COLUMN location GEOGRAPHY(POINT, 4326);
                CREATE INDEX idx_nature_risk_sites_location
                    ON nature_risk_sites USING GIST(location);
            END IF;
        END
        $$;
    """)

    # ── cat_risk_properties ────────────────────────────────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'cat_risk_properties'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'cat_risk_properties' AND column_name = 'location'
            ) THEN
                ALTER TABLE cat_risk_properties
                    ADD COLUMN location GEOGRAPHY(POINT, 4326);
                CREATE INDEX idx_cat_risk_properties_location
                    ON cat_risk_properties USING GIST(location);
            END IF;
        END
        $$;
    """)

    # ── power_plant_assets ─────────────────────────────────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'power_plant_assets'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'power_plant_assets' AND column_name = 'location'
            ) THEN
                ALTER TABLE power_plant_assets
                    ADD COLUMN location GEOGRAPHY(POINT, 4326);
                CREATE INDEX idx_power_plant_assets_location
                    ON power_plant_assets USING GIST(location);
            END IF;
        END
        $$;
    """)

    # ── real_estate valuation assets ───────────────────────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'valuation_assets'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'valuation_assets' AND column_name = 'location'
            ) THEN
                ALTER TABLE valuation_assets
                    ADD COLUMN location GEOGRAPHY(POINT, 4326);
                CREATE INDEX idx_valuation_assets_location
                    ON valuation_assets USING GIST(location);
            END IF;
        END
        $$;
    """)


def downgrade():
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'valuation_assets' AND column_name = 'location'
            ) THEN
                DROP INDEX IF EXISTS idx_valuation_assets_location;
                ALTER TABLE valuation_assets DROP COLUMN location;
            END IF;
        END
        $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'power_plant_assets' AND column_name = 'location'
            ) THEN
                DROP INDEX IF EXISTS idx_power_plant_assets_location;
                ALTER TABLE power_plant_assets DROP COLUMN location;
            END IF;
        END
        $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'cat_risk_properties' AND column_name = 'location'
            ) THEN
                DROP INDEX IF EXISTS idx_cat_risk_properties_location;
                ALTER TABLE cat_risk_properties DROP COLUMN location;
            END IF;
        END
        $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'nature_risk_sites' AND column_name = 'location'
            ) THEN
                DROP INDEX IF EXISTS idx_nature_risk_sites_location;
                ALTER TABLE nature_risk_sites DROP COLUMN location;
            END IF;
        END
        $$;
    """)
    # Note: do NOT drop the PostGIS extension as other tables may use it
