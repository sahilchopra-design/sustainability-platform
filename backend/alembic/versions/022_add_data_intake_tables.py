"""Add data_intake tables — Category C client proprietary data intake

Revision ID: 022_add_data_intake_tables
Revises: 021_add_company_profiles
Create Date: 2026-03-04

Covers:
  - di_loan_portfolio_uploads   : CSV upload job tracking
  - di_loan_portfolio_rows      : individual loan/asset rows with validation
  - di_counterparty_emissions   : Scope 1/2/3 per counterparty with PCAF DQS
  - di_real_estate_assets       : building EUI + CRREM pathway data
  - di_shipping_fleet           : vessel-level CII emissions data
  - di_steel_borrowers          : steel production route + CO2 intensity
  - di_project_finance          : project finance assessments with quick metrics
  - di_internal_config          : key-value config store for platform settings
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "022_add_data_intake_tables"
down_revision = "021_add_company_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Loan Portfolio Upload (job tracking) ──────────────────────────────────
    op.create_table(
        "di_loan_portfolio_uploads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("upload_name", sa.Text, nullable=False),
        sa.Column("filename", sa.Text),
        sa.Column("status", sa.Text, default="pending"),           # pending | processing | complete | failed
        sa.Column("total_rows", sa.Integer, default=0),
        sa.Column("valid_rows", sa.Integer, default=0),
        sa.Column("error_rows", sa.Integer, default=0),
        sa.Column("uploaded_by", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── Loan Portfolio Rows ───────────────────────────────────────────────────
    op.create_table(
        "di_loan_portfolio_rows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("upload_id", sa.Integer, sa.ForeignKey("di_loan_portfolio_uploads.id", ondelete="CASCADE")),
        sa.Column("counterparty_id", sa.Text),
        sa.Column("counterparty_name", sa.Text),
        sa.Column("instrument_type", sa.Text),          # loan | bond | equity | guarantee
        sa.Column("outstanding_amount", sa.Numeric(20, 4)),
        sa.Column("currency", sa.Text, default="USD"),
        sa.Column("sector_gics", sa.Text),
        sa.Column("country_iso2", sa.Text),
        sa.Column("maturity_date", sa.Date),
        sa.Column("stage_ifrs9", sa.Integer),           # 1 | 2 | 3
        sa.Column("pd_1yr", sa.Numeric(10, 6)),
        sa.Column("lgd", sa.Numeric(10, 6)),
        sa.Column("reported_emissions_tco2e", sa.Numeric(20, 4)),
        sa.Column("pcaf_dqs", sa.Integer),              # 1-5
        sa.Column("data_year", sa.Integer),
        sa.Column("is_valid", sa.Boolean, default=True),
        sa.Column("validation_errors", JSONB),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # ── Counterparty Emissions ────────────────────────────────────────────────
    op.create_table(
        "di_counterparty_emissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("counterparty_id", sa.Text, nullable=False),
        sa.Column("counterparty_name", sa.Text),
        sa.Column("reporting_year", sa.Integer, nullable=False),
        sa.Column("scope1_tco2e", sa.Numeric(20, 4)),
        sa.Column("scope2_market_tco2e", sa.Numeric(20, 4)),
        sa.Column("scope2_location_tco2e", sa.Numeric(20, 4)),
        sa.Column("scope3_total_tco2e", sa.Numeric(20, 4)),
        sa.Column("scope3_cat1_purchased_goods", sa.Numeric(20, 4)),
        sa.Column("scope3_cat11_use_of_sold_products", sa.Numeric(20, 4)),
        sa.Column("scope3_cat15_investments", sa.Numeric(20, 4)),
        sa.Column("data_source_type", sa.Text),         # direct_measurement | audited_report | self_reported | sector_average
        sa.Column("pcaf_dqs", sa.Integer),              # 1-5 derived from data_source_type
        sa.Column("evidence_url", sa.Text),
        sa.Column("assurance_level", sa.Text),          # none | limited | reasonable
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.UniqueConstraint("counterparty_id", "reporting_year", name="uq_di_counterparty_year"),
    )

    # ── Real Estate Assets ────────────────────────────────────────────────────
    op.create_table(
        "di_real_estate_assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_ref", sa.Text),
        sa.Column("property_name", sa.Text),
        sa.Column("address_line1", sa.Text),
        sa.Column("city", sa.Text),
        sa.Column("country_iso2", sa.Text),
        sa.Column("property_type", sa.Text),            # office | retail | industrial | residential | mixed
        sa.Column("gross_floor_area_m2", sa.Numeric(12, 2)),
        sa.Column("eui_kwh_m2_yr", sa.Numeric(10, 2)),  # Energy Use Intensity
        sa.Column("crrem_pathway_2030", sa.Numeric(10, 2)),
        sa.Column("crrem_pathway_2050", sa.Numeric(10, 2)),
        sa.Column("stranding_year", sa.Integer),
        sa.Column("energy_star_score", sa.Integer),
        sa.Column("gresb_score", sa.Integer),
        sa.Column("certifications", JSONB),             # ["LEED Gold","BREEAM Very Good"]
        sa.Column("data_year", sa.Integer),
        sa.Column("upload_batch", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # ── Shipping Fleet ────────────────────────────────────────────────────────
    op.create_table(
        "di_shipping_fleet",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vessel_imo", sa.Text, nullable=False, unique=True),
        sa.Column("vessel_name", sa.Text),
        sa.Column("vessel_type", sa.Text),              # bulk_carrier | tanker | container | ro_ro | other
        sa.Column("flag_state", sa.Text),
        sa.Column("dwt_tonnes", sa.Numeric(14, 2)),
        sa.Column("gross_tonnage", sa.Numeric(14, 2)),
        sa.Column("build_year", sa.Integer),
        sa.Column("propulsion_type", sa.Text),          # HFO | MDO | LNG | methanol | ammonia | hybrid
        sa.Column("annual_fuel_consumption_mt", sa.Numeric(14, 4)),
        sa.Column("annual_co2_tco2e", sa.Numeric(14, 4)),
        sa.Column("annual_distance_nm", sa.Numeric(14, 2)),
        sa.Column("cii_rating", sa.Text),               # A | B | C | D | E
        sa.Column("cii_score", sa.Numeric(10, 4)),
        sa.Column("eexi_value", sa.Numeric(10, 4)),
        sa.Column("data_year", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # ── Steel Borrowers ───────────────────────────────────────────────────────
    op.create_table(
        "di_steel_borrowers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("borrower_id", sa.Text, nullable=False, unique=True),
        sa.Column("borrower_name", sa.Text),
        sa.Column("country_iso2", sa.Text),
        sa.Column("crude_steel_production_mt", sa.Numeric(14, 4)),
        sa.Column("bf_bof_share_pct", sa.Numeric(6, 2), default=0),   # Blast Furnace – Basic Oxygen Furnace
        sa.Column("eaf_share_pct", sa.Numeric(6, 2), default=0),      # Electric Arc Furnace
        sa.Column("dri_share_pct", sa.Numeric(6, 2), default=0),      # Direct Reduced Iron
        sa.Column("blended_co2_intensity_tco2_tcs", sa.Numeric(10, 4)),  # computed server-side
        sa.Column("total_co2_tco2e", sa.Numeric(20, 4)),
        sa.Column("energy_source_mix", JSONB),          # {"coal":60,"gas":20,"electric":20}
        sa.Column("sbti_committed", sa.Boolean, default=False),
        sa.Column("data_year", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # ── Project Finance ───────────────────────────────────────────────────────
    op.create_table(
        "di_project_finance",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_ref", sa.Text, unique=True),
        sa.Column("project_name", sa.Text, nullable=False),
        sa.Column("project_type", sa.Text),             # solar | wind | hydro | storage | ccs | other
        sa.Column("country_iso2", sa.Text),
        sa.Column("capacity_mw", sa.Numeric(12, 4)),
        sa.Column("total_capex_musd", sa.Numeric(14, 4)),
        sa.Column("debt_musd", sa.Numeric(14, 4)),
        sa.Column("equity_musd", sa.Numeric(14, 4)),
        sa.Column("annual_revenue_musd", sa.Numeric(14, 4)),
        sa.Column("annual_opex_musd", sa.Numeric(14, 4)),
        sa.Column("annual_debt_service_musd", sa.Numeric(14, 4)),
        sa.Column("project_life_yrs", sa.Integer),
        sa.Column("capacity_factor_pct", sa.Numeric(6, 2)),
        sa.Column("include_carbon_credits", sa.Boolean, default=False),
        sa.Column("carbon_credit_price_usd", sa.Numeric(10, 4)),
        sa.Column("annual_co2_avoided_tco2e", sa.Numeric(20, 4)),
        sa.Column("discount_rate_pct", sa.Numeric(6, 4)),
        # Quick metrics computed server-side
        sa.Column("preliminary_dscr", sa.Numeric(10, 4)),
        sa.Column("preliminary_lcoe_usd_mwh", sa.Numeric(10, 4)),
        sa.Column("preliminary_equity_irr_pct", sa.Numeric(8, 4)),
        sa.Column("equator_principles_category", sa.Text),  # A | B | C
        sa.Column("paris_alignment_status", sa.Text),       # aligned | misaligned | under_review
        sa.Column("status", sa.Text, default="draft"),      # draft | under_review | approved | rejected
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # ── Internal Config ───────────────────────────────────────────────────────
    op.create_table(
        "di_internal_config",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("config_key", sa.Text, nullable=False, unique=True),
        sa.Column("config_value", sa.Text),
        sa.Column("display_name", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("config_group", sa.Text),            # emissions | thresholds | reporting | integration
        sa.Column("data_type", sa.Text, default="string"),  # string | number | boolean | json
        sa.Column("updated_by", sa.Text),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    # Seed default config keys
    op.execute("""
        INSERT INTO di_internal_config (config_key, config_value, display_name, description, config_group, data_type)
        VALUES
          ('default_currency',         'USD',    'Default Currency',          'Reporting currency for all monetary values',                'reporting',   'string'),
          ('default_pcaf_dqs',         '3',      'Default PCAF DQS',          'Default data quality score when not specified (1=best)',     'emissions',   'number'),
          ('carbon_price_usd_tco2',    '85',     'Carbon Price (USD/tCO2)',   'Internal carbon price used for transition risk estimates',   'emissions',   'number'),
          ('crrem_pathway_version',    '2.0',    'CRREM Pathway Version',     'Version of CRREM decarbonisation pathways in use',          'reporting',   'string'),
          ('scope3_materiality_pct',   '40',     'Scope 3 Materiality %',     'Scope 3 is material if >40% of total emissions',            'emissions',   'number'),
          ('sbti_target_year',         '2030',   'SBTi Near-term Target Year','Near-term SBTi target year for sector alignment checks',    'emissions',   'number'),
          ('pcaf_benchmark_year',      '2019',   'PCAF Benchmark Year',       'Base year for financed emissions benchmarking',             'emissions',   'number'),
          ('reporting_framework',      'PCAF',   'Primary Reporting Framework','Primary framework for financed emissions (PCAF or TCFD)',   'reporting',   'string')
        ON CONFLICT (config_key) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table("di_internal_config")
    op.drop_table("di_project_finance")
    op.drop_table("di_steel_borrowers")
    op.drop_table("di_shipping_fleet")
    op.drop_table("di_real_estate_assets")
    op.drop_table("di_counterparty_emissions")
    op.drop_table("di_loan_portfolio_rows")
    op.drop_table("di_loan_portfolio_uploads")
