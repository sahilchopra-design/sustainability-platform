"""
Migration 029 — China Trade Platform (CTP)

Prefix: ctp_
Tables (11):
  ctp_entities                — exporters / importers / traders registry
  ctp_china_esg_disclosures   — SSE/SZSE 2024 mandatory ESG guidelines
  ctp_ets_positions           — China national ETS (CETS) positions + compliance
  ctp_ndc_pathways            — sectoral decarbonisation vs 2030 peak / 2060 neutrality
  ctp_export_products         — product-level HS code + embedded carbon intensity
  ctp_cbam_liabilities        — CBAM liability per exporter × product × destination
  ctp_trade_corridors         — bilateral trade corridor metadata + carbon regime
  ctp_supplier_requirements   — importer-side sustainability expectations
  ctp_marketplace_listings    — carbon credit / allowance / certificate listings
  ctp_marketplace_orders      — buy / sell orders
  ctp_marketplace_transactions — executed trades (audit trail)

Cross-module FKs:
  ctp_cbam_liabilities.cbam_calc_id → (no direct FK; join via hs_code + entity_name)
  ctp_export_products.pboc_category → references GBEPC category codes

Revision chain: 029 → down_revision = '028_asia_regulatory_cbi'
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = '029_china_trade_platform'
down_revision = '028_asia_regulatory_cbi'
branch_labels = None
depends_on = None


def upgrade():

    # -------------------------------------------------------------------------
    # 1. CTP ENTITIES  (exporters, importers, traders — extensible beyond China)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_entities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('entity_name_zh', sa.String(255)),                    # Chinese name
        sa.Column('entity_type', sa.String(30), nullable=False),        # exporter | importer | trader | regulator
        sa.Column('country_code', sa.CHAR(2), nullable=False),          # ISO-2
        sa.Column('province', sa.String(100)),
        sa.Column('city', sa.String(100)),
        sa.Column('sector', sa.String(100)),
        sa.Column('sub_sector', sa.String(100)),
        sa.Column('hs_codes', JSONB),                                   # product HS codes
        sa.Column('annual_revenue_usd_mn', sa.Numeric(14, 2)),
        sa.Column('annual_export_volume_usd_mn', sa.Numeric(14, 2)),
        sa.Column('primary_export_destinations', JSONB),                # [DE,FR,NL]
        sa.Column('is_ets_covered', sa.Boolean, default=False),
        sa.Column('ets_registration_id', sa.String(50)),
        sa.Column('sse_stock_code', sa.String(10)),
        sa.Column('szse_stock_code', sa.String(10)),
        sa.Column('hkex_stock_code', sa.String(10)),
        sa.Column('lei', sa.String(20)),
        sa.Column('website', sa.String(255)),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint(
            "entity_type IN ('exporter','importer','trader','regulator','both')",
            name='ck_ctp_entities_type'),
    )
    op.create_index('ix_ctp_entities_name',    'ctp_entities', ['entity_name'])
    op.create_index('ix_ctp_entities_country', 'ctp_entities', ['country_code'])
    op.create_index('ix_ctp_entities_sector',  'ctp_entities', ['sector'])
    op.create_index('ix_ctp_entities_ets',     'ctp_entities', ['is_ets_covered'])

    # -------------------------------------------------------------------------
    # 2. CHINA ESG DISCLOSURES  (SSE / SZSE 2024 mandatory guidelines)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_china_esg_disclosures',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('exchange', sa.String(10)),                           # SSE | SZSE | HKEX
        sa.Column('disclosure_tier', sa.String(30)),                    # mandatory_key | recommended | voluntary

        # Environmental
        sa.Column('e_ghg_scope1_tco2e', sa.Numeric(14, 2)),
        sa.Column('e_ghg_scope2_tco2e', sa.Numeric(14, 2)),
        sa.Column('e_ghg_scope3_tco2e', sa.Numeric(14, 2)),
        sa.Column('e_ghg_intensity_tco2e_per_cny10k', sa.Numeric(10, 4)),
        sa.Column('e_energy_total_gj', sa.Numeric(14, 2)),
        sa.Column('e_renewable_pct', sa.Numeric(5, 2)),
        sa.Column('e_water_m3', sa.Numeric(14, 2)),
        sa.Column('e_waste_tonne', sa.Numeric(14, 2)),
        sa.Column('e_env_incidents', sa.Integer),
        sa.Column('e_env_penalties_cny', sa.Numeric(14, 2)),
        sa.Column('e_score', sa.Numeric(5, 2)),                         # 0-100

        # Social
        sa.Column('s_employees_total', sa.Integer),
        sa.Column('s_women_pct', sa.Numeric(5, 2)),
        sa.Column('s_injury_rate', sa.Numeric(8, 4)),
        sa.Column('s_training_hours_avg', sa.Numeric(6, 2)),
        sa.Column('s_community_investment_cny_mn', sa.Numeric(12, 2)),
        sa.Column('s_supply_chain_audits', sa.Integer),
        sa.Column('s_score', sa.Numeric(5, 2)),

        # Governance
        sa.Column('g_board_independence_pct', sa.Numeric(5, 2)),
        sa.Column('g_board_meetings', sa.SmallInteger),
        sa.Column('g_audit_committee', sa.Boolean),
        sa.Column('g_anti_corruption_training_pct', sa.Numeric(5, 2)),
        sa.Column('g_data_breaches', sa.Integer),
        sa.Column('g_score', sa.Numeric(5, 2)),

        sa.Column('overall_esg_score', sa.Numeric(5, 2)),               # 0-100
        sa.Column('esg_tier', sa.String(20)),                           # Leader|Advanced|Developing|Emerging
        sa.Column('assurance_provider', sa.String(100)),
        sa.Column('carbon_neutral_target_year', sa.Integer),
        sa.Column('extra_indicators', JSONB),
        sa.Column('status', sa.String(20), default='published'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_esg_entity',  'ctp_china_esg_disclosures', ['entity_id'])
    op.create_index('ix_ctp_esg_year',    'ctp_china_esg_disclosures', ['reporting_year'])
    op.create_index('ix_ctp_esg_tier',    'ctp_china_esg_disclosures', ['esg_tier'])

    # -------------------------------------------------------------------------
    # 3. CHINA ETS POSITIONS  (CETS — national carbon market)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_ets_positions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('sector', sa.String(100)),                            # Power|Steel|Cement|Aluminium|Chemicals|Paper|Aviation
        sa.Column('phase', sa.String(10)),                              # Phase1 | Phase2
        sa.Column('allocation_allowances_tco2', sa.Numeric(14, 2)),
        sa.Column('verified_emissions_tco2', sa.Numeric(14, 2)),
        sa.Column('surplus_deficit_tco2', sa.Numeric(14, 2)),          # allocation − verified
        sa.Column('compliance_status', sa.String(20)),                  # compliant | deficit | surplus
        sa.Column('carbon_price_cny_per_tco2', sa.Numeric(8, 2)),
        sa.Column('carbon_price_usd_per_tco2', sa.Numeric(8, 2)),
        sa.Column('compliance_cost_cny_mn', sa.Numeric(14, 2)),
        sa.Column('abatement_cost_cny_per_tco2', sa.Numeric(8, 2)),
        sa.Column('benchmark_tco2_per_mwh', sa.Numeric(8, 4)),         # sector-specific
        sa.Column('free_allocation_pct', sa.Numeric(5, 2)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_ets_entity', 'ctp_ets_positions', ['entity_id'])
    op.create_index('ix_ctp_ets_year',   'ctp_ets_positions', ['year'])
    op.create_index('ix_ctp_ets_sector', 'ctp_ets_positions', ['sector'])

    # -------------------------------------------------------------------------
    # 4. NDC SECTORAL PATHWAYS  (2030 peak → 2060 carbon neutral)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_ndc_pathways',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('sector', sa.String(100), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('baseline_emissions_mtco2', sa.Numeric(10, 2)),       # 2020 baseline
        sa.Column('pathway_emissions_mtco2', sa.Numeric(10, 2)),        # NDC-aligned path
        sa.Column('current_emissions_mtco2', sa.Numeric(10, 2)),        # actual if available
        sa.Column('reduction_vs_baseline_pct', sa.Numeric(6, 2)),
        sa.Column('on_track', sa.Boolean),
        sa.Column('milestone_type', sa.String(50)),                     # peak | decline | neutrality | interim
        sa.Column('key_technologies', JSONB),
        sa.Column('policy_driver', sa.String(255)),
        sa.Column('carbon_price_implied_cny', sa.Numeric(8, 2)),
        sa.Column('notes', sa.Text),
    )
    op.create_index('ix_ctp_ndc_sector', 'ctp_ndc_pathways', ['sector'])
    op.create_index('ix_ctp_ndc_year',   'ctp_ndc_pathways', ['year'])

    # -------------------------------------------------------------------------
    # 5. EXPORT PRODUCTS  (product-level carbon intensity by HS code)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_export_products',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255)),
        sa.Column('hs_code', sa.String(10), nullable=False),
        sa.Column('hs_description', sa.String(255)),
        sa.Column('product_name', sa.String(255)),
        sa.Column('product_category', sa.String(100)),                  # steel|cement|aluminium|fertiliser|power|hydrogen|ev|solar
        sa.Column('cbam_sector', sa.String(50)),                        # CBAM Annex I category
        sa.Column('cbam_applicable', sa.Boolean, default=False),

        # Volume & value
        sa.Column('annual_volume_tonnes', sa.Numeric(14, 2)),
        sa.Column('annual_value_usd_mn', sa.Numeric(14, 2)),
        sa.Column('primary_destination', sa.CHAR(2)),
        sa.Column('destination_markets', JSONB),                        # [{country:DE,pct:35.0}]

        # Carbon intensity
        sa.Column('embedded_carbon_tco2_per_tonne', sa.Numeric(10, 4), nullable=False),
        sa.Column('production_process', sa.String(100)),                # BF-BOF|EAF|wet_kiln|dry_kiln|Hall-Heroult|Soderberg
        sa.Column('carbon_intensity_vs_eu_benchmark_pct', sa.Numeric(8, 2)),  # % above/below EU reference
        sa.Column('carbon_intensity_vs_sector_avg_pct', sa.Numeric(8, 2)),
        sa.Column('green_certified', sa.Boolean, default=False),
        sa.Column('green_certification_type', sa.String(50)),           # PBoC|CBI|ISO14064|ResponsibleSteel

        # Cost
        sa.Column('production_cost_usd_per_tonne', sa.Numeric(10, 2)),
        sa.Column('carbon_cost_cny_per_tonne', sa.Numeric(10, 2)),

        # PBoC GBEPC linkage (cross-module)
        sa.Column('pboc_category', sa.String(5)),                       # CE|CT|EC|EE|GU|GS

        sa.Column('reporting_year', sa.Integer),
        sa.Column('data_source', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_products_entity',  'ctp_export_products', ['entity_id'])
    op.create_index('ix_ctp_products_hs',      'ctp_export_products', ['hs_code'])
    op.create_index('ix_ctp_products_cbam',    'ctp_export_products', ['cbam_applicable'])
    op.create_index('ix_ctp_products_category','ctp_export_products', ['product_category'])

    # -------------------------------------------------------------------------
    # 6. CBAM LIABILITIES  (per exporter × product × destination year)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_cbam_liabilities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('product_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_export_products.id', ondelete='SET NULL')),
        sa.Column('hs_code', sa.String(10)),
        sa.Column('product_category', sa.String(100)),
        sa.Column('destination_country', sa.CHAR(2)),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Volume
        sa.Column('export_volume_tonnes', sa.Numeric(14, 2)),
        sa.Column('export_value_eur_mn', sa.Numeric(14, 2)),

        # Carbon
        sa.Column('embedded_carbon_tco2', sa.Numeric(14, 4)),           # volume × intensity
        sa.Column('eu_free_allocation_tco2', sa.Numeric(14, 4)),
        sa.Column('eu_benchmark_tco2', sa.Numeric(14, 4)),              # EU reference value
        sa.Column('excess_carbon_tco2', sa.Numeric(14, 4)),             # max(0, embedded - benchmark - allocation)
        sa.Column('china_ets_price_eur_per_tco2', sa.Numeric(8, 2)),
        sa.Column('eu_ets_price_eur_per_tco2', sa.Numeric(8, 2)),
        sa.Column('carbon_price_differential_eur', sa.Numeric(8, 2)),   # EU − China

        # Liability
        sa.Column('cbam_certificates_required', sa.Numeric(14, 4)),
        sa.Column('cbam_liability_eur', sa.Numeric(14, 2)),
        sa.Column('cbam_liability_usd', sa.Numeric(14, 2)),
        sa.Column('carbon_cost_already_paid_eur', sa.Numeric(14, 2)),   # CETS cost credit
        sa.Column('net_cbam_liability_eur', sa.Numeric(14, 2)),         # after CETS deduction

        # Competitive impact
        sa.Column('price_impact_pct', sa.Numeric(6, 2)),               # CBAM / export value
        sa.Column('competitiveness_risk', sa.String(20)),               # low|medium|high|critical
        sa.Column('transition_phase', sa.String(20)),                   # reporting|transitional|full

        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_cbam_entity',  'ctp_cbam_liabilities', ['entity_id'])
    op.create_index('ix_ctp_cbam_year',    'ctp_cbam_liabilities', ['reporting_year'])
    op.create_index('ix_ctp_cbam_hs',      'ctp_cbam_liabilities', ['hs_code'])
    op.create_index('ix_ctp_cbam_dest',    'ctp_cbam_liabilities', ['destination_country'])

    # -------------------------------------------------------------------------
    # 7. TRADE CORRIDORS  (bilateral metadata + carbon border regime)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_trade_corridors',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('origin_country', sa.CHAR(2), nullable=False),
        sa.Column('destination_country', sa.CHAR(2), nullable=False),
        sa.Column('corridor_name', sa.String(100)),                     # e.g. China → EU
        sa.Column('trade_value_usd_bn', sa.Numeric(10, 2)),
        sa.Column('trade_volume_mn_tonnes', sa.Numeric(10, 2)),
        sa.Column('carbon_intensity_avg_tco2_per_tonne', sa.Numeric(8, 4)),
        sa.Column('total_embedded_carbon_mtco2', sa.Numeric(10, 2)),
        sa.Column('cbam_applicable', sa.Boolean, default=False),
        sa.Column('carbon_border_regime', sa.String(50)),               # EU_CBAM|UK_CBAM|US_CCA|CA_CBAM
        sa.Column('regime_transition_start', sa.Date),
        sa.Column('regime_full_implementation', sa.Date),
        sa.Column('key_product_categories', JSONB),                     # [steel,aluminium,cement]
        sa.Column('top_hs_codes', JSONB),
        sa.Column('annual_cbam_liability_est_eur_mn', sa.Numeric(12, 2)),
        sa.Column('data_year', sa.Integer),
        sa.Column('notes', sa.Text),
    )
    op.create_index('ix_ctp_corridors_origin', 'ctp_trade_corridors', ['origin_country'])
    op.create_index('ix_ctp_corridors_dest',   'ctp_trade_corridors', ['destination_country'])

    # -------------------------------------------------------------------------
    # 8. SUPPLIER REQUIREMENTS  (importer-side sustainability expectations)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_supplier_requirements',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('importer_entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('importer_name', sa.String(255), nullable=False),
        sa.Column('framework', sa.String(50)),                          # CBAM|CSDDD|UK_CBT|SFDR|custom
        sa.Column('requirement_type', sa.String(50)),                   # carbon_intensity|certification|disclosure|audit
        sa.Column('product_category', sa.String(100)),
        sa.Column('hs_codes_in_scope', JSONB),
        sa.Column('max_carbon_intensity_tco2_per_tonne', sa.Numeric(10, 4)),
        sa.Column('required_certifications', JSONB),                    # [ISO14064,ResponsibleSteel]
        sa.Column('reporting_frequency', sa.String(20)),                # annual|quarterly|monthly
        sa.Column('verified_data_required', sa.Boolean, default=False),
        sa.Column('third_party_audit_required', sa.Boolean, default=False),
        sa.Column('compliance_deadline', sa.Date),
        sa.Column('penalty_clause', sa.Text),
        sa.Column('preferred_supplier_discount_pct', sa.Numeric(5, 2)),  # commercial incentive
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_supplier_req_importer', 'ctp_supplier_requirements', ['importer_entity_id'])

    # -------------------------------------------------------------------------
    # 9. MARKETPLACE LISTINGS  (carbon credits, ETS allowances, certificates)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_marketplace_listings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('seller_entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('seller_name', sa.String(255), nullable=False),
        sa.Column('listing_type', sa.String(50)),                       # carbon_credit|ets_allowance|green_cert|cbam_cert|offset
        sa.Column('product_description', sa.Text),
        sa.Column('hs_code', sa.String(10)),                            # if product-level credit
        sa.Column('product_category', sa.String(100)),
        sa.Column('vintage_year', sa.Integer),
        sa.Column('standard', sa.String(50)),                           # CETS|VCS|Gold Standard|CBI|CDM|CORSIA
        sa.Column('volume_tco2', sa.Numeric(14, 2), nullable=False),
        sa.Column('asking_price_usd_per_tco2', sa.Numeric(10, 2)),
        sa.Column('asking_price_cny_per_tco2', sa.Numeric(10, 2)),
        sa.Column('currency', sa.CHAR(3), default='USD'),
        sa.Column('geography_origin', sa.CHAR(2)),
        sa.Column('project_location', sa.String(255)),
        sa.Column('sector', sa.String(100)),
        sa.Column('co_benefits', JSONB),                                # {biodiversity:true,community:true}
        sa.Column('verification_status', sa.String(20)),                # verified|pending|unverified
        sa.Column('registry_serial', sa.String(100)),
        sa.Column('listing_status', sa.String(20), default='active'),   # active|sold|expired|withdrawn
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('listed_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_listings_seller',  'ctp_marketplace_listings', ['seller_entity_id'])
    op.create_index('ix_ctp_listings_type',    'ctp_marketplace_listings', ['listing_type'])
    op.create_index('ix_ctp_listings_status',  'ctp_marketplace_listings', ['listing_status'])
    op.create_index('ix_ctp_listings_standard','ctp_marketplace_listings', ['standard'])

    # -------------------------------------------------------------------------
    # 10. MARKETPLACE ORDERS
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_marketplace_orders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('buyer_entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('listing_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_marketplace_listings.id', ondelete='SET NULL')),
        sa.Column('order_type', sa.CHAR(4)),                            # buy | sell
        sa.Column('volume_tco2', sa.Numeric(14, 2)),
        sa.Column('bid_price_usd_per_tco2', sa.Numeric(10, 2)),
        sa.Column('compliance_purpose', sa.String(50)),                 # CBAM|ETS|voluntary|offset|retirement
        sa.Column('status', sa.String(20), default='pending'),          # pending|matched|executed|cancelled
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_orders_buyer',   'ctp_marketplace_orders', ['buyer_entity_id'])
    op.create_index('ix_ctp_orders_listing', 'ctp_marketplace_orders', ['listing_id'])

    # -------------------------------------------------------------------------
    # 11. MARKETPLACE TRANSACTIONS  (executed trade audit trail)
    # -------------------------------------------------------------------------
    op.create_table(
        'ctp_marketplace_transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('listing_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_marketplace_listings.id', ondelete='SET NULL')),
        sa.Column('buyer_entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('seller_entity_id', UUID(as_uuid=True),
                  sa.ForeignKey('ctp_entities.id', ondelete='SET NULL')),
        sa.Column('volume_tco2', sa.Numeric(14, 2), nullable=False),
        sa.Column('price_usd_per_tco2', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_value_usd', sa.Numeric(14, 2)),
        sa.Column('platform_fee_usd', sa.Numeric(10, 2)),
        sa.Column('compliance_purpose', sa.String(50)),
        sa.Column('settlement_date', sa.Date),
        sa.Column('compliance_registry_ref', sa.String(100)),
        sa.Column('retirement_serial', sa.String(100)),
        sa.Column('executed_at', sa.DateTime(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ctp_txn_buyer',   'ctp_marketplace_transactions', ['buyer_entity_id'])
    op.create_index('ix_ctp_txn_seller',  'ctp_marketplace_transactions', ['seller_entity_id'])
    op.create_index('ix_ctp_txn_listing', 'ctp_marketplace_transactions', ['listing_id'])


def downgrade():
    op.drop_table('ctp_marketplace_transactions')
    op.drop_table('ctp_marketplace_orders')
    op.drop_table('ctp_marketplace_listings')
    op.drop_table('ctp_supplier_requirements')
    op.drop_table('ctp_trade_corridors')
    op.drop_table('ctp_cbam_liabilities')
    op.drop_table('ctp_export_products')
    op.drop_table('ctp_ndc_pathways')
    op.drop_table('ctp_ets_positions')
    op.drop_table('ctp_china_esg_disclosures')
    op.drop_table('ctp_entities')
