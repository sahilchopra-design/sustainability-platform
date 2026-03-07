"""032 – GDELT events + controversy scoring tables.

Creates:
  - dh_gdelt_events       : GDELT event records (conflict, cooperation, protests, etc.)
  - dh_gdelt_gkg          : GDELT Global Knowledge Graph entries (themes, tone, entities)
  - dh_controversy_scores : Aggregated entity-level controversy scores from GDELT + other feeds
  - Registers 2 data sources in dh_data_sources

Revision ID: 032_add_gdelt_controversy_tables
Revises: 031_add_reference_violations_tables
"""

from alembic import op
import sqlalchemy as sa

revision = "032_add_gdelt_controversy_tables"
down_revision = "031_add_reference_violations_tables"
branch_labels = None
depends_on = None


def upgrade():
    # ── GDELT Events ───────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS dh_gdelt_events (
        id              VARCHAR(64) PRIMARY KEY,
        global_event_id VARCHAR(32),
        event_date      DATE,
        year            INT,
        month           INT,

        -- Actor 1
        actor1_name     VARCHAR(256),
        actor1_country  VARCHAR(8),
        actor1_type     VARCHAR(64),

        -- Actor 2
        actor2_name     VARCHAR(256),
        actor2_country  VARCHAR(8),
        actor2_type     VARCHAR(64),

        -- Event classification (CAMEO)
        event_code      VARCHAR(8),
        event_base_code VARCHAR(8),
        event_root_code VARCHAR(4),
        quad_class       INT,              -- 1=Verbal Coop, 2=Material Coop, 3=Verbal Conflict, 4=Material Conflict
        goldstein_scale  NUMERIC(6,2),     -- -10 to +10

        -- Quantitative
        num_mentions    INT,
        num_sources     INT,
        num_articles    INT,
        avg_tone        NUMERIC(8,4),

        -- Geography
        action_geo_country VARCHAR(8),
        action_geo_lat     NUMERIC(10,6),
        action_geo_lon     NUMERIC(10,6),
        action_geo_name    VARCHAR(256),

        -- Source
        source_url      TEXT,
        date_added      DATE,

        -- Matched entity (our enrichment)
        matched_entity_name VARCHAR(256),
        matched_entity_lei  VARCHAR(20),

        -- Metadata
        data_source     VARCHAR(64) DEFAULT 'gdelt-events',
        ingested_at     TIMESTAMPTZ DEFAULT now(),
        updated_at      TIMESTAMPTZ DEFAULT now()
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_events_date ON dh_gdelt_events (event_date);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_events_actor1 ON dh_gdelt_events (actor1_name);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_events_actor2 ON dh_gdelt_events (actor2_name);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_events_matched ON dh_gdelt_events (matched_entity_name);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_events_quad ON dh_gdelt_events (quad_class);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_events_country ON dh_gdelt_events (action_geo_country);")

    # ── GDELT Global Knowledge Graph ───────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS dh_gdelt_gkg (
        id              VARCHAR(64) PRIMARY KEY,
        gkg_record_id   VARCHAR(64),
        publish_date    TIMESTAMPTZ,
        source_name     VARCHAR(256),
        source_url      TEXT,
        document_tone   NUMERIC(8,4),      -- overall tone of the document
        positive_score  NUMERIC(8,4),
        negative_score  NUMERIC(8,4),
        polarity        NUMERIC(8,4),

        -- Themes & taxonomies
        themes          TEXT,               -- semicolon-separated GDELT themes
        locations       TEXT,               -- semicolon-separated locations
        persons         TEXT,               -- semicolon-separated person names
        organizations   TEXT,               -- semicolon-separated org names
        gcam_codes      TEXT,               -- GCAM analysis codes

        -- ESG relevance scoring (our enrichment)
        esg_relevance_score NUMERIC(6,4),   -- 0.0 to 1.0
        esg_category        VARCHAR(32),    -- E, S, G, or null
        controversy_flag    BOOLEAN DEFAULT false,

        -- Matched entity
        matched_entity_name VARCHAR(256),
        matched_entity_lei  VARCHAR(20),

        -- Metadata
        data_source     VARCHAR(64) DEFAULT 'gdelt-gkg',
        ingested_at     TIMESTAMPTZ DEFAULT now(),
        updated_at      TIMESTAMPTZ DEFAULT now()
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_gkg_date ON dh_gdelt_gkg (publish_date);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_gkg_entity ON dh_gdelt_gkg (matched_entity_name);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gdelt_gkg_controversy ON dh_gdelt_gkg (controversy_flag) WHERE controversy_flag = true;")

    # ── Controversy Scores ─────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS dh_controversy_scores (
        id                VARCHAR(64) PRIMARY KEY,
        entity_name       VARCHAR(256) NOT NULL,
        entity_lei        VARCHAR(20),
        country_iso3      VARCHAR(3),
        sector            VARCHAR(128),

        -- Scoring
        period_start      DATE NOT NULL,
        period_end        DATE NOT NULL,
        controversy_score NUMERIC(6,3),       -- 0-100 composite
        severity_level    VARCHAR(16),         -- Low / Medium / High / Critical
        trend             VARCHAR(16),         -- Improving / Stable / Deteriorating

        -- Breakdown
        env_score         NUMERIC(6,3),        -- environmental controversy
        social_score      NUMERIC(6,3),        -- social controversy
        governance_score  NUMERIC(6,3),        -- governance controversy

        -- Drivers
        total_events      INT DEFAULT 0,
        negative_events   INT DEFAULT 0,
        positive_events   INT DEFAULT 0,
        avg_tone          NUMERIC(8,4),
        avg_goldstein     NUMERIC(6,2),
        media_mentions    INT DEFAULT 0,
        top_themes        TEXT,                 -- comma-separated

        -- Metadata
        data_source       VARCHAR(64) DEFAULT 'gdelt-controversy',
        ingested_at       TIMESTAMPTZ DEFAULT now(),
        updated_at        TIMESTAMPTZ DEFAULT now(),

        UNIQUE(entity_name, period_start, period_end)
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_controversy_entity ON dh_controversy_scores (entity_name);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_controversy_severity ON dh_controversy_scores (severity_level);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_controversy_period ON dh_controversy_scores (period_start, period_end);")

    # ── Register data sources ──────────────────────────────────────────────
    op.execute("""
    INSERT INTO dh_data_sources (id, name, category, sub_category, description, access_type, base_url, sync_enabled, sync_schedule, status, priority)
    VALUES
        ('gdelt-events', 'GDELT Event Database', 'controversy', 'events',
         'Global Database of Events, Language, and Tone — real-time event monitoring for geopolitical and corporate controversy tracking.',
         'public_api', 'https://api.gdeltproject.org/api/v2/', true, 'daily', 'active', 4),
        ('gdelt-controversy', 'GDELT Controversy Scores', 'controversy', 'scores',
         'Aggregated ESG controversy scores derived from GDELT event streams and Global Knowledge Graph analysis.',
         'derived', NULL, true, 'weekly', 'active', 4)
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now();
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS dh_controversy_scores CASCADE;")
    op.execute("DROP TABLE IF EXISTS dh_gdelt_gkg CASCADE;")
    op.execute("DROP TABLE IF EXISTS dh_gdelt_events CASCADE;")
    op.execute("DELETE FROM dh_data_sources WHERE id IN ('gdelt-events', 'gdelt-controversy');")
