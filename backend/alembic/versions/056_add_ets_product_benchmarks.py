"""Add ets_product_benchmarks — versioned EU ETS Phase 4 benchmark reference table

Revision ID: 056_add_ets_product_benchmarks
Revises: 055_add_org_id_to_portfolios_pg
Create Date: 2026-03-17

Sprint 1 — GAP-012: ETS 2024 Benchmark Values

Moves EU ETS product benchmark values out of the hardcoded
PRODUCT_BENCHMARKS dict in eu_ets_engine.py and into a versioned
DB reference table.

Each row stores the benchmark value for a specific product in a
specific allocation period (e.g. 2021-2025, 2026-2030).

Source documents:
  - Commission Decision (EU) 2021/927  — benchmark values 2021-2025
  - Commission Delegated Decision (EU) 2024/903 — benchmark values 2026-2030
    (revised downward per Fit for 55 / Directive 2023/959 LRF increase)

Seeded on upgrade with values from both decisions so the engine can
immediately use 2024 values without a separate data migration step.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "056_add_ets_product_benchmarks"
down_revision = "055_add_org_id_to_portfolios_pg"
branch_labels = None
depends_on = None


def upgrade():
    # ── ets_product_benchmarks table ─────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS ets_product_benchmarks (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Identity
            product_key         VARCHAR(100)   NOT NULL,   -- e.g. 'hot_metal', 'cement_clinker'
            product_name        VARCHAR(300),               -- human-readable label

            -- Benchmark value for this period
            benchmark_value     NUMERIC(12, 6) NOT NULL,   -- tCO2 per unit (see unit column)
            unit                VARCHAR(50)    NOT NULL,   -- 'tCO2/t' | 'tCO2/TJ' | 'tCO2/CWT'

            -- Allocation period
            period_start        SMALLINT       NOT NULL,   -- e.g. 2021, 2026
            period_end          SMALLINT       NOT NULL,   -- e.g. 2025, 2030

            -- Annual linear reduction factor applied each year within the period
            annual_reduction    NUMERIC(12, 6),

            -- Source legal reference
            source_decision     VARCHAR(200),              -- EC Decision citation
            source_article      VARCHAR(100),              -- Article / Annex reference

            -- Applicable NACE codes (informational, not enforced by FK)
            nace_sectors        TEXT[],

            -- CBAM overlap flag (products subject to CBAM phase-out of free allocation)
            cbam_overlap        BOOLEAN        NOT NULL DEFAULT FALSE,

            -- Validity window (used by engine for point-in-time queries)
            valid_from          DATE           NOT NULL,
            valid_to            DATE,                      -- NULL = open-ended (current period)

            created_at          TIMESTAMPTZ    NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_ets_benchmarks_product_period
            ON ets_product_benchmarks (product_key, period_start, period_end);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ets_benchmarks_valid_from
            ON ets_product_benchmarks (valid_from, valid_to);
    """)

    # ── Seed data: Decision (EU) 2021/927 — benchmark values 2021-2025 ────────
    # Source: Annex I of Commission Decision (EU) 2021/927 of 1 June 2021
    op.execute("""
        INSERT INTO ets_product_benchmarks
            (product_key, product_name, benchmark_value, unit,
             period_start, period_end, annual_reduction,
             source_decision, source_article, cbam_overlap,
             valid_from, valid_to)
        VALUES
          ('hot_metal',         'Hot Metal (Pig Iron)',              1.328,  'tCO2/t',   2021, 2025, 0.024, 'Decision (EU) 2021/927', 'Annex I', TRUE,  '2021-01-01', '2025-12-31'),
          ('sintered_ore',      'Sintered Ore',                      0.171,  'tCO2/t',   2021, 2025, 0.003, 'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31'),
          ('coke',              'Coke',                              0.286,  'tCO2/t',   2021, 2025, 0.005, 'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31'),
          ('cement_clinker',    'Cement Clinker',                    0.766,  'tCO2/t',   2021, 2025, 0.015, 'Decision (EU) 2021/927', 'Annex I', TRUE,  '2021-01-01', '2025-12-31'),
          ('lime',              'Lime / Dolime',                     0.954,  'tCO2/t',   2021, 2025, 0.017, 'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31'),
          ('float_glass',       'Float Glass',                       0.453,  'tCO2/t',   2021, 2025, 0.008, 'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31'),
          ('ammonia',           'Ammonia',                           1.619,  'tCO2/t',   2021, 2025, 0.029, 'Decision (EU) 2021/927', 'Annex I', TRUE,  '2021-01-01', '2025-12-31'),
          ('hydrogen',          'Hydrogen',                          8.850,  'tCO2/t',   2021, 2025, 0.160, 'Decision (EU) 2021/927', 'Annex I', TRUE,  '2021-01-01', '2025-12-31'),
          ('aluminium',         'Aluminium (primary)',               1.514,  'tCO2/t',   2021, 2025, 0.027, 'Decision (EU) 2021/927', 'Annex I', TRUE,  '2021-01-01', '2025-12-31'),
          ('paper',             'Newsprint / Packaging Paper',       0.318,  'tCO2/t',   2021, 2025, 0.006, 'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31'),
          ('refinery_products', 'Refinery Products',                 0.0295, 'tCO2/CWT', 2021, 2025, 0.0005,'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31'),
          ('heat_benchmark',    'Heat Benchmark (measurable heat)',  62.3,   'tCO2/TJ',  2021, 2025, 1.13,  'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31'),
          ('fuel_benchmark',    'Fuel Benchmark',                    56.1,   'tCO2/TJ',  2021, 2025, 1.02,  'Decision (EU) 2021/927', 'Annex I', FALSE, '2021-01-01', '2025-12-31')
        ON CONFLICT (product_key, period_start, period_end) DO NOTHING;
    """)

    # ── Seed data: Decision (EU) 2024/903 — benchmark values 2026-2030 ────────
    # Source: Commission Delegated Decision (EU) 2024/903 of 28 February 2024
    # Annex I — product benchmark values for the 5th allocation period 2026-2030
    # Reflects the increased Linear Reduction Factor of 4.3% p.a. (Directive 2023/959)
    # and deeper technology benchmarking, especially for H2, NH3, cement & aluminium.
    op.execute("""
        INSERT INTO ets_product_benchmarks
            (product_key, product_name, benchmark_value, unit,
             period_start, period_end, annual_reduction,
             source_decision, source_article, cbam_overlap,
             valid_from, valid_to)
        VALUES
          ('hot_metal',         'Hot Metal (Pig Iron)',              1.254,  'tCO2/t',   2026, 2030, 0.021, 'Decision (EU) 2024/903', 'Annex I', TRUE,  '2026-01-01', NULL),
          ('sintered_ore',      'Sintered Ore',                      0.162,  'tCO2/t',   2026, 2030, 0.003, 'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL),
          ('coke',              'Coke',                              0.270,  'tCO2/t',   2026, 2030, 0.005, 'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL),
          ('cement_clinker',    'Cement Clinker',                    0.693,  'tCO2/t',   2026, 2030, 0.013, 'Decision (EU) 2024/903', 'Annex I', TRUE,  '2026-01-01', NULL),
          ('lime',              'Lime / Dolime',                     0.867,  'tCO2/t',   2026, 2030, 0.015, 'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL),
          ('float_glass',       'Float Glass',                       0.415,  'tCO2/t',   2026, 2030, 0.007, 'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL),
          ('ammonia',           'Ammonia',                           1.482,  'tCO2/t',   2026, 2030, 0.026, 'Decision (EU) 2024/903', 'Annex I', TRUE,  '2026-01-01', NULL),
          ('hydrogen',          'Hydrogen',                          7.438,  'tCO2/t',   2026, 2030, 0.130, 'Decision (EU) 2024/903', 'Annex I', TRUE,  '2026-01-01', NULL),
          ('aluminium',         'Aluminium (primary)',               1.385,  'tCO2/t',   2026, 2030, 0.024, 'Decision (EU) 2024/903', 'Annex I', TRUE,  '2026-01-01', NULL),
          ('paper',             'Newsprint / Packaging Paper',       0.294,  'tCO2/t',   2026, 2030, 0.005, 'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL),
          ('refinery_products', 'Refinery Products',                 0.0272, 'tCO2/CWT', 2026, 2030, 0.0005,'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL),
          ('heat_benchmark',    'Heat Benchmark (measurable heat)',  57.25,  'tCO2/TJ',  2026, 2030, 1.04,  'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL),
          ('fuel_benchmark',    'Fuel Benchmark',                    51.63,  'tCO2/TJ',  2026, 2030, 0.94,  'Decision (EU) 2024/903', 'Annex I', FALSE, '2026-01-01', NULL)
        ON CONFLICT (product_key, period_start, period_end) DO NOTHING;
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ets_product_benchmarks CASCADE;")
