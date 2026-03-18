"""Add RE / Nature / Spatial FK linkage — extend cross-module anchoring

Revision ID: 043
Revises: 042
Create Date: 2026-03-09

Extends cross-module FK linkage from migration 042 to cover:
1. Real estate assets → company_profiles (property owner/entity)
2. Nature risk assessments → valuation_assets (property-level nature risk)
3. Climate assessment results → company_profiles (entity-level climate scores)
4. ECL assessments → company_profiles (entity-level credit risk)
5. PCAF portfolio results → company_profiles
6. Nature-RE integration assessment table (new)
7. Spatial hazard profiles table (new)

Also adds indexes for common join paths and a trigger for
updated_at auto-maintenance.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "043"
down_revision = "042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Nature-RE Integration Assessments (new table) ──────────────────
    op.create_table(
        "nature_re_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", sa.String(100), nullable=False),
        sa.Column("valuation_asset_id", UUID(as_uuid=True), nullable=True),
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("property_type", sa.String(50), nullable=False, server_default="office"),
        sa.Column("market_value_eur", sa.Numeric(18, 2)),
        sa.Column("noi_eur", sa.Numeric(18, 2)),
        sa.Column("cap_rate_pct", sa.Numeric(6, 3)),
        # Nature inputs
        sa.Column("leap_overall_score", sa.Numeric(4, 2)),
        sa.Column("water_baseline_score", sa.Numeric(4, 2)),
        sa.Column("water_projected_2030", sa.Numeric(4, 2)),
        sa.Column("water_projected_2050", sa.Numeric(4, 2)),
        sa.Column("biodiversity_impact_score", sa.Numeric(4, 2)),
        sa.Column("biodiversity_direct_overlaps", sa.Integer, server_default="0"),
        sa.Column("bng_units_required", sa.Numeric(10, 2)),
        sa.Column("habitat_type", sa.String(50)),
        # Computed outputs
        sa.Column("nature_haircut_pct", sa.Numeric(6, 3)),
        sa.Column("water_noi_adjustment_pct", sa.Numeric(6, 3)),
        sa.Column("biodiversity_cap_rate_adj_bps", sa.Integer),
        sa.Column("bng_capex_estimate_eur", sa.Numeric(14, 2)),
        sa.Column("nature_adjusted_value_eur", sa.Numeric(18, 2)),
        sa.Column("composite_nature_score", sa.Numeric(4, 2)),
        sa.Column("composite_nature_band", sa.String(20)),
        sa.Column("eu_taxonomy_nature_dnsh_pass", sa.Boolean),
        sa.Column("nature_narrative", sa.Text),
        sa.Column("recommendations", JSONB),
        # Audit
        sa.Column("assessed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("assessed_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK constraints
        sa.ForeignKeyConstraint(["valuation_asset_id"], ["valuation_assets.id"],
                                name="fk_nature_re_valuation_asset", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_profile_id"], ["company_profiles.id"],
                                name="fk_nature_re_company_profile", ondelete="SET NULL"),
    )
    op.create_index("ix_nature_re_property", "nature_re_assessments", ["property_id"])
    op.create_index("ix_nature_re_val_asset", "nature_re_assessments", ["valuation_asset_id"])
    op.create_index("ix_nature_re_cp", "nature_re_assessments", ["company_profile_id"])
    op.create_index("ix_nature_re_band", "nature_re_assessments", ["composite_nature_band"])

    # ── 2. Spatial Hazard Profiles (new table) ────────────────────────────
    op.create_table(
        "spatial_hazard_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", sa.String(100), nullable=False),
        sa.Column("valuation_asset_id", UUID(as_uuid=True), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(11, 7)),
        sa.Column("country", sa.String(3)),
        # Hazard fields
        sa.Column("flood_zone", sa.String(10)),
        sa.Column("flood_depth_100yr_m", sa.Numeric(6, 2)),
        sa.Column("heat_days_above_35c", sa.Integer),
        sa.Column("wildfire_proximity_km", sa.Numeric(8, 1)),
        sa.Column("coastal_proximity_km", sa.Numeric(8, 1)),
        sa.Column("subsidence_risk", sa.String(20)),
        sa.Column("water_stress_score", sa.Numeric(4, 2)),
        sa.Column("sea_level_rise_cm_2050", sa.Numeric(6, 1)),
        sa.Column("cyclone_exposure", sa.String(20)),
        sa.Column("permafrost_risk", sa.String(20)),
        # Metadata
        sa.Column("data_source", sa.String(50)),
        sa.Column("spatial_precision", sa.String(30)),
        sa.Column("confidence_band", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK constraints
        sa.ForeignKeyConstraint(["valuation_asset_id"], ["valuation_assets.id"],
                                name="fk_spatial_hazard_val_asset", ondelete="SET NULL"),
    )
    op.create_index("ix_shp_property", "spatial_hazard_profiles", ["property_id"])
    op.create_index("ix_shp_val_asset", "spatial_hazard_profiles", ["valuation_asset_id"])
    op.create_index("ix_shp_country", "spatial_hazard_profiles", ["country"])

    # ── 3. Residential RE Valuations (new table) ──────────────────────────
    op.create_table(
        "residential_re_valuations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", sa.String(100), nullable=False),
        sa.Column("valuation_asset_id", UUID(as_uuid=True), nullable=True),
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("property_type", sa.String(30)),
        sa.Column("country", sa.String(3)),
        sa.Column("floor_area_m2", sa.Numeric(10, 2)),
        sa.Column("bedrooms", sa.Integer),
        sa.Column("epc_rating", sa.String(2)),
        sa.Column("energy_kwh_m2_yr", sa.Numeric(8, 2)),
        # Valuation outputs
        sa.Column("hedonic_value_eur", sa.Numeric(18, 2)),
        sa.Column("epc_premium_pct", sa.Numeric(6, 3)),
        sa.Column("flood_discount_pct", sa.Numeric(6, 3)),
        sa.Column("crrem_stranding_year", sa.Integer),
        sa.Column("mees_compliant", sa.Boolean),
        sa.Column("retrofit_cost_to_c_eur", sa.Numeric(14, 2)),
        sa.Column("climate_adjusted_value_eur", sa.Numeric(18, 2)),
        sa.Column("climate_ltv", sa.Numeric(6, 4)),
        sa.Column("ltv_stress_bps", sa.Integer),
        sa.Column("recommendations", JSONB),
        # Audit
        sa.Column("assessed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK constraints
        sa.ForeignKeyConstraint(["valuation_asset_id"], ["valuation_assets.id"],
                                name="fk_res_re_val_asset", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_profile_id"], ["company_profiles.id"],
                                name="fk_res_re_company_profile", ondelete="SET NULL"),
    )
    op.create_index("ix_res_re_property", "residential_re_valuations", ["property_id"])
    op.create_index("ix_res_re_val_asset", "residential_re_valuations", ["valuation_asset_id"])
    op.create_index("ix_res_re_cp", "residential_re_valuations", ["company_profile_id"])
    op.create_index("ix_res_re_epc", "residential_re_valuations", ["epc_rating"])

    # ── 4. RICS ESG Compliance (new table) ────────────────────────────────
    op.create_table(
        "rics_esg_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", sa.String(100), nullable=False),
        sa.Column("valuation_asset_id", UUID(as_uuid=True), nullable=True),
        sa.Column("property_type", sa.String(30)),
        sa.Column("country", sa.String(3)),
        sa.Column("valuation_purpose", sa.String(30)),
        # Compliance outputs
        sa.Column("total_items", sa.Integer),
        sa.Column("compliant_count", sa.Integer),
        sa.Column("partial_count", sa.Integer),
        sa.Column("non_compliant_count", sa.Integer),
        sa.Column("compliance_pct", sa.Numeric(6, 2)),
        sa.Column("compliance_band", sa.String(20)),
        sa.Column("checklist", JSONB),
        sa.Column("esg_narrative", sa.Text),
        sa.Column("materiality_scores", JSONB),
        sa.Column("uncertainty_pct", sa.Numeric(6, 3)),
        sa.Column("uncertainty_band", sa.String(20)),
        sa.Column("recommendations", JSONB),
        # Audit
        sa.Column("assessed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["valuation_asset_id"], ["valuation_assets.id"],
                                name="fk_rics_esg_val_asset", ondelete="SET NULL"),
    )
    op.create_index("ix_rics_esg_property", "rics_esg_assessments", ["property_id"])
    op.create_index("ix_rics_esg_val_asset", "rics_esg_assessments", ["valuation_asset_id"])
    op.create_index("ix_rics_esg_band", "rics_esg_assessments", ["compliance_band"])

    # ── 5. Add company_profile_id FK to valuation_assets ──────────────────
    #    Links RE properties to their owner entity.
    op.add_column(
        "valuation_assets",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_val_assets_company_profile",
        "valuation_assets", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_val_assets_cp", "valuation_assets", ["company_profile_id"])

    # ── 6. Add company_profile_id FK to ecl_assessments ───────────────────
    op.add_column(
        "ecl_assessments",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ecl_company_profile",
        "ecl_assessments", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_ecl_cp", "ecl_assessments", ["company_profile_id"])

    # ── 7. Add company_profile_id FK to pcaf_portfolios ───────────────────
    op.add_column(
        "pcaf_portfolios",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_pcaf_port_company_profile",
        "pcaf_portfolios", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_pcaf_port_cp", "pcaf_portfolios", ["company_profile_id"])

    # ── 8. Add company_profile_id FK to climate_assessment_runs ───────────
    op.add_column(
        "climate_assessment_runs",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_climate_run_company_profile",
        "climate_assessment_runs", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_climate_run_cp", "climate_assessment_runs", ["company_profile_id"])


def downgrade() -> None:
    # Drop FK columns added to existing tables
    for table, fk_name, ix_name in [
        ("climate_assessment_runs", "fk_climate_run_company_profile", "ix_climate_run_cp"),
        ("pcaf_portfolios", "fk_pcaf_port_company_profile", "ix_pcaf_port_cp"),
        ("ecl_assessments", "fk_ecl_company_profile", "ix_ecl_cp"),
        ("valuation_assets", "fk_val_assets_company_profile", "ix_val_assets_cp"),
    ]:
        op.drop_constraint(fk_name, table, type_="foreignkey")
        op.drop_index(ix_name, table_name=table)
        op.drop_column(table, "company_profile_id")

    # Drop new tables
    op.drop_table("rics_esg_assessments")
    op.drop_table("residential_re_valuations")
    op.drop_table("spatial_hazard_profiles")
    op.drop_table("nature_re_assessments")
