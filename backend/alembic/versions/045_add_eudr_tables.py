"""Add EUDR compliance tables

Revision ID: 045
Revises: 044
Create Date: 2026-03-09

New tables:
1. eudr_operators — Operator/trader registry for EUDR scope
2. eudr_due_diligence — Due diligence assessment records
3. eudr_commodity_lots — Commodity lot traceability (Art 9)
4. eudr_supply_chain_links — Supply chain mapping
5. eudr_geolocation_proofs — Geolocation evidence store (Art 9(1)(c)-(d))
6. eudr_compliance_evidence — General compliance evidence repository

Indexes for common join paths + updated_at trigger.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "045"
down_revision = "044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. EUDR Operators ──────────────────────────────────────────────────
    op.create_table(
        "eudr_operators",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", sa.String(100), nullable=False, unique=True),
        sa.Column("operator_name", sa.String(300), nullable=False),
        sa.Column("operator_type", sa.String(30), nullable=False,
                  server_default="operator"),        # operator / trader / trader_sme
        sa.Column("country_iso2", sa.String(3)),
        sa.Column("eori_number", sa.String(30)),     # EU Customs EORI
        sa.Column("commodities_in_scope", JSONB),    # List of EUDR commodities handled
        sa.Column("countries_sourced_from", JSONB),   # List of country ISO2 codes
        sa.Column("certifications", JSONB),           # Certification codes held
        sa.Column("competent_authority", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["company_profile_id"], ["company_profiles.id"],
                                name="fk_eudr_op_company_profile", ondelete="SET NULL"),
    )
    op.create_index("ix_eudr_op_id", "eudr_operators", ["operator_id"])
    op.create_index("ix_eudr_op_type", "eudr_operators", ["operator_type"])
    op.create_index("ix_eudr_op_cp", "eudr_operators", ["company_profile_id"])

    # ── 2. EUDR Due Diligence Assessments ──────────────────────────────────
    op.create_table(
        "eudr_due_diligence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("operator_id", sa.String(100), nullable=False),
        sa.Column("assessment_date", sa.Date, nullable=False),
        sa.Column("due_diligence_level", sa.String(20)),  # simplified/standard/enhanced
        sa.Column("commodities_assessed", JSONB),
        sa.Column("countries_of_origin", JSONB),
        # Scores
        sa.Column("information_score", sa.Numeric(6, 2)),
        sa.Column("risk_assessment_score", sa.Numeric(6, 2)),
        sa.Column("risk_mitigation_score", sa.Numeric(6, 2)),
        sa.Column("overall_compliance_score", sa.Numeric(6, 2)),
        sa.Column("compliance_status", sa.String(20)),  # compliant/at_risk/non_compliant
        # Gap summary
        sa.Column("total_gaps", sa.Integer),
        sa.Column("critical_gaps", sa.Integer),
        sa.Column("gaps_detail", JSONB),
        sa.Column("recommendations", JSONB),
        sa.Column("remediation_plan", JSONB),
        sa.Column("estimated_remediation_weeks", sa.Integer),
        # Cross-framework
        sa.Column("esrs_e4_linkage", JSONB),
        sa.Column("eu_taxonomy_biodiversity_dnsh", sa.Boolean),
        # Statement
        sa.Column("statement_ready", sa.Boolean, server_default="false"),
        sa.Column("statement_reference_number", sa.String(100)),
        sa.Column("enforcement_deadline", sa.Date),
        # Metadata
        sa.Column("certifications_used", JSONB),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_eudr_dd_operator", "eudr_due_diligence", ["operator_id"])
    op.create_index("ix_eudr_dd_status", "eudr_due_diligence", ["compliance_status"])
    op.create_index("ix_eudr_dd_date", "eudr_due_diligence", ["assessment_date"])
    op.create_index("ix_eudr_dd_stmt", "eudr_due_diligence", ["statement_ready"])

    # ── 3. EUDR Commodity Lots ─────────────────────────────────────────────
    op.create_table(
        "eudr_commodity_lots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("due_diligence_id", UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", sa.String(100), nullable=False),
        sa.Column("commodity", sa.String(30), nullable=False),
        sa.Column("product_description", sa.String(300)),
        sa.Column("hs_code", sa.String(12)),
        sa.Column("quantity_kg", sa.Numeric(16, 4)),
        sa.Column("country_of_production", sa.String(3)),
        sa.Column("production_date", sa.Date),
        sa.Column("production_date_end", sa.Date),
        # Supplier
        sa.Column("supplier_name", sa.String(300)),
        sa.Column("supplier_address", sa.Text),
        sa.Column("supplier_country", sa.String(3)),
        # Geolocation (Art 9(1)(c)-(d))
        sa.Column("geolocation_latitude", sa.Numeric(10, 7)),
        sa.Column("geolocation_longitude", sa.Numeric(11, 7)),
        sa.Column("geolocation_type", sa.String(10)),  # point / polygon
        sa.Column("plot_area_ha", sa.Numeric(10, 4)),
        sa.Column("geolocation_polygon", JSONB),  # GeoJSON polygon for >4ha
        # Verification flags
        sa.Column("deforestation_free_verified", sa.Boolean, server_default="false"),
        sa.Column("local_law_compliance_verified", sa.Boolean, server_default="false"),
        sa.Column("traceability_score", sa.Numeric(6, 2)),
        sa.Column("verification_notes", sa.Text),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["due_diligence_id"], ["eudr_due_diligence.id"],
                                name="fk_eudr_lot_dd", ondelete="SET NULL"),
    )
    op.create_index("ix_eudr_lot_operator", "eudr_commodity_lots", ["operator_id"])
    op.create_index("ix_eudr_lot_commodity", "eudr_commodity_lots", ["commodity"])
    op.create_index("ix_eudr_lot_country", "eudr_commodity_lots", ["country_of_production"])
    op.create_index("ix_eudr_lot_dd", "eudr_commodity_lots", ["due_diligence_id"])

    # ── 4. EUDR Supply Chain Links ─────────────────────────────────────────
    op.create_table(
        "eudr_supply_chain_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("operator_id", sa.String(100), nullable=False),
        sa.Column("commodity", sa.String(30), nullable=False),
        sa.Column("tier", sa.Integer, nullable=False, server_default="1"),
        sa.Column("supplier_name", sa.String(300), nullable=False),
        sa.Column("supplier_address", sa.Text),
        sa.Column("supplier_country", sa.String(3)),
        sa.Column("supplier_type", sa.String(30)),  # producer / processor / trader
        sa.Column("certification_code", sa.String(20)),
        sa.Column("certification_valid_until", sa.Date),
        sa.Column("risk_tier", sa.String(20)),
        sa.Column("last_audit_date", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_eudr_sc_operator", "eudr_supply_chain_links", ["operator_id"])
    op.create_index("ix_eudr_sc_commodity", "eudr_supply_chain_links", ["commodity"])
    op.create_index("ix_eudr_sc_tier", "eudr_supply_chain_links", ["tier"])
    op.create_index("ix_eudr_sc_country", "eudr_supply_chain_links", ["supplier_country"])

    # ── 5. EUDR Geolocation Proofs ─────────────────────────────────────────
    op.create_table(
        "eudr_geolocation_proofs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("commodity_lot_id", UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", sa.String(100), nullable=False),
        sa.Column("proof_type", sa.String(30), nullable=False),  # gps_point / polygon / satellite
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(11, 7)),
        sa.Column("polygon_geojson", JSONB),
        sa.Column("plot_area_ha", sa.Numeric(10, 4)),
        sa.Column("capture_date", sa.Date),
        sa.Column("source", sa.String(100)),  # GPS device / satellite provider / field survey
        sa.Column("satellite_provider", sa.String(100)),
        sa.Column("resolution_m", sa.Numeric(8, 2)),
        sa.Column("deforestation_alert", sa.Boolean, server_default="false"),
        sa.Column("verification_status", sa.String(20), server_default="pending"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["commodity_lot_id"], ["eudr_commodity_lots.id"],
                                name="fk_eudr_geo_lot", ondelete="SET NULL"),
    )
    op.create_index("ix_eudr_geo_operator", "eudr_geolocation_proofs", ["operator_id"])
    op.create_index("ix_eudr_geo_lot", "eudr_geolocation_proofs", ["commodity_lot_id"])
    op.create_index("ix_eudr_geo_alert", "eudr_geolocation_proofs", ["deforestation_alert"])

    # ── 6. EUDR Compliance Evidence ────────────────────────────────────────
    op.create_table(
        "eudr_compliance_evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("due_diligence_id", UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", sa.String(100), nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        # Types: certification, audit_report, satellite_analysis, supplier_attestation,
        #        legal_compliance_doc, field_inspection, lab_test, third_party_verification
        sa.Column("evidence_reference", sa.String(200)),
        sa.Column("description", sa.Text),
        sa.Column("article_reference", sa.String(30)),
        sa.Column("commodity", sa.String(30)),
        sa.Column("country_iso2", sa.String(3)),
        sa.Column("valid_from", sa.Date),
        sa.Column("valid_until", sa.Date),
        sa.Column("verified_by", sa.String(200)),
        sa.Column("verification_date", sa.Date),
        sa.Column("document_url", sa.Text),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        # FK
        sa.ForeignKeyConstraint(["due_diligence_id"], ["eudr_due_diligence.id"],
                                name="fk_eudr_evidence_dd", ondelete="SET NULL"),
    )
    op.create_index("ix_eudr_ev_operator", "eudr_compliance_evidence", ["operator_id"])
    op.create_index("ix_eudr_ev_type", "eudr_compliance_evidence", ["evidence_type"])
    op.create_index("ix_eudr_ev_dd", "eudr_compliance_evidence", ["due_diligence_id"])
    op.create_index("ix_eudr_ev_commodity", "eudr_compliance_evidence", ["commodity"])


def downgrade() -> None:
    op.drop_table("eudr_compliance_evidence")
    op.drop_table("eudr_geolocation_proofs")
    op.drop_table("eudr_supply_chain_links")
    op.drop_table("eudr_commodity_lots")
    op.drop_table("eudr_due_diligence")
    op.drop_table("eudr_operators")
