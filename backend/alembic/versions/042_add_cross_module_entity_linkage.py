"""Add cross-module entity linkage — company_profiles as universal anchor

Revision ID: 042
Revises: 041
Create Date: 2026-03-08

Promotes company_profiles as the canonical entity master by adding nullable
FK columns (company_profile_id) to all sector entity tables.  Also adds
enforced FK constraints on csrd_entity_registry soft pointers and creates
a LEI uniqueness index on company_profiles.

Tables altered:
  - fi_entities          + company_profile_id UUID → company_profiles(id)
  - energy_entities      + company_profile_id UUID → company_profiles(id)
  - sc_entities          + company_profile_id UUID → company_profiles(id)
  - regulatory_entities  + company_profile_id UUID → company_profiles(id)
  - csrd_entity_registry + company_profile_id UUID → company_profiles(id)
  - csrd_entity_registry: enforce FK on fi_entity_id, energy_entity_id, sc_entity_id
  - company_profiles:     unique index on entity_lei (canonical LEI anchor)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. LEI uniqueness on company_profiles ───────────────────────────────
    op.create_index(
        "ix_cp_entity_lei_unique",
        "company_profiles",
        ["entity_lei"],
        unique=True,
        postgresql_where=sa.text("entity_lei IS NOT NULL"),
    )

    # ── 2. Add company_profile_id FK to sector entity tables ────────────────

    # fi_entities
    op.add_column(
        "fi_entities",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_fi_entities_company_profile",
        "fi_entities", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_fi_cp_id", "fi_entities", ["company_profile_id"])

    # energy_entities
    op.add_column(
        "energy_entities",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_energy_entities_company_profile",
        "energy_entities", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_energy_cp_id", "energy_entities", ["company_profile_id"])

    # sc_entities
    op.add_column(
        "sc_entities",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_sc_entities_company_profile",
        "sc_entities", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_sc_cp_id", "sc_entities", ["company_profile_id"])

    # regulatory_entities
    op.add_column(
        "regulatory_entities",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_reg_entities_company_profile",
        "regulatory_entities", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_reg_cp_id", "regulatory_entities", ["company_profile_id"])

    # csrd_entity_registry
    op.add_column(
        "csrd_entity_registry",
        sa.Column("company_profile_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_csrd_entity_company_profile",
        "csrd_entity_registry", "company_profiles",
        ["company_profile_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_csrd_cp_id", "csrd_entity_registry", ["company_profile_id"])

    # ── 3. Enforce FK on csrd_entity_registry soft pointers ─────────────────
    #    These columns already exist as bare UUID — add FK constraints.

    op.create_foreign_key(
        "fk_csrd_fi_entity",
        "csrd_entity_registry", "fi_entities",
        ["fi_entity_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_csrd_energy_entity",
        "csrd_entity_registry", "energy_entities",
        ["energy_entity_id"], ["id"],
        ondelete="SET NULL",
    )
    # sc_entities PK is Integer — csrd_entity_registry.sc_entity_id is UUID
    # Type mismatch: skip FK enforcement for sc_entity_id (would need column type change)

    # ── 4. Backfill: link existing records by LEI match ─────────────────────
    #    Auto-populate company_profile_id where entity_lei / lei matches.
    #    This is idempotent — runs only where company_profile_id IS NULL.

    for table, lei_col in [
        ("fi_entities",          "lei"),
        ("energy_entities",      "lei"),
        ("sc_entities",          "lei"),
        ("regulatory_entities",  "lei"),
        ("csrd_entity_registry", "lei"),
    ]:
        op.execute(f"""
            UPDATE {table} t
            SET company_profile_id = cp.id
            FROM company_profiles cp
            WHERE cp.entity_lei = t.{lei_col}
              AND t.{lei_col} IS NOT NULL
              AND t.company_profile_id IS NULL
        """)

    # ── 5. Also backfill csrd_entity_registry.entity_registry_id → company_profiles
    op.execute("""
        UPDATE company_profiles cp
        SET entity_registry_id = cr.id::text
        FROM csrd_entity_registry cr
        WHERE cr.lei = cp.entity_lei
          AND cp.entity_lei IS NOT NULL
          AND cp.entity_registry_id IS NULL
    """)


def downgrade() -> None:
    # Drop FK constraints
    op.drop_constraint("fk_csrd_energy_entity", "csrd_entity_registry", type_="foreignkey")
    op.drop_constraint("fk_csrd_fi_entity", "csrd_entity_registry", type_="foreignkey")

    # Drop company_profile_id columns and their FKs/indexes
    for table, fk_name, ix_name in [
        ("csrd_entity_registry", "fk_csrd_entity_company_profile", "ix_csrd_cp_id"),
        ("regulatory_entities",  "fk_reg_entities_company_profile", "ix_reg_cp_id"),
        ("sc_entities",          "fk_sc_entities_company_profile",  "ix_sc_cp_id"),
        ("energy_entities",      "fk_energy_entities_company_profile", "ix_energy_cp_id"),
        ("fi_entities",          "fk_fi_entities_company_profile",  "ix_fi_cp_id"),
    ]:
        op.drop_constraint(fk_name, table, type_="foreignkey")
        op.drop_index(ix_name, table_name=table)
        op.drop_column(table, "company_profile_id")

    op.drop_index("ix_cp_entity_lei_unique", table_name="company_profiles")
