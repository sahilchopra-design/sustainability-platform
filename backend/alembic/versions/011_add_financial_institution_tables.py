"""
Add Financial Institution Tables

Revision ID: 011_add_financial_institution_tables
Revises: 010_add_unified_valuation_tables
Create Date: 2026-03-01

Tables covering financial institutions (banks, insurers, asset managers):
- fi_entities                     : Institution master record
- fi_financials                   : P&L, balance sheet, capital ratios (annual)
- fi_loan_books                   : Sector/geography loan portfolio decomposition
- fi_green_finance                 : Green / sustainable / social / transition finance volumes (LBP taxonomy)
- fi_financed_emissions            : PCAF financed emissions by asset class (replaces/extends pcaf_portfolios for FI)
- fi_paris_alignment              : Portfolio alignment metrics (PACTA / SBTi / IEA NZE)
- fi_csrd_e1_climate              : ESRS E1 climate disclosures — own ops + financed emissions
- fi_csrd_s1_workforce            : ESRS S1 own workforce KPIs
- fi_csrd_s2_supply_chain_workers : ESRS S2 value chain workers
- fi_csrd_g1_governance           : ESRS G1 business conduct KPIs
- fi_risk_exposures               : Climate/ESG risk exposures (physical, transition, social, nature)
- fi_taxonomy_kpis                : EU Taxonomy KPIs for credit institutions (CRR Article 449a)
- fi_remuneration                 : Executive pay, gender pay gap, ESG-linked pay

Based on CSRD disclosures: ING Groep NV (2024), ABN AMRO (2024),
BNP Paribas (2024), Société Générale (2024)
ESRS standards: ESRS 2, E1, E2, E3, E4, E5, S1, S2, S3, S4, G1
EU Taxonomy CRR Article 449a (Green Asset Ratio, Banking Book Taxonomy Alignment Ratio)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '011_add_financial_institution_tables'
down_revision = '010_add_unified_valuation_tables'
branch_labels = None
depends_on = None


def upgrade():

    # =========================================================================
    # 1. FI ENTITIES  (institution master)
    # =========================================================================
    op.create_table(
        'fi_entities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trading_name', sa.String(255)),
        sa.Column('lei', sa.String(20)),
        sa.Column('swift_bic', sa.String(11)),
        sa.Column('institution_type', sa.String(40), nullable=False),   # universal_bank | investment_bank | savings_bank | cooperative_bank | insurer | asset_manager | pension_fund | development_bank
        sa.Column('supervision_type', sa.String(20), default='SSM'),    # SSM | PRA | ACPR | BaFin | DNB | FI | FSA
        sa.Column('headquarters_country', sa.String(3), nullable=False),
        sa.Column('listing_exchange', sa.String(20)),
        sa.Column('isin', sa.String(12)),
        sa.Column('stock_ticker', sa.String(20)),
        sa.Column('csrd_first_mandatory_year', sa.Integer, default=2024),  # ING/ABN/BNP/SocGen = 2024
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.CheckConstraint("institution_type IN ('universal_bank','investment_bank','savings_bank','cooperative_bank','insurer','asset_manager','pension_fund','development_bank','fintech','other')", name='ck_fi_entities_type'),
    )
    op.create_index('ix_fi_entities_lei', 'fi_entities', ['lei'], unique=True)
    op.create_index('ix_fi_entities_country', 'fi_entities', ['headquarters_country'])
    op.create_index('ix_fi_entities_type', 'fi_entities', ['institution_type'])

    # =========================================================================
    # 2. FI FINANCIALS  (P&L, balance sheet, capital — annual)
    # =========================================================================
    op.create_table(
        'fi_financials',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('reporting_period', sa.String(10), default='FY'),     # FY | H1 | H2 | Q1 | Q2 | Q3 | Q4
        sa.Column('currency', sa.String(3), default='EUR'),

        # --- P&L ---
        sa.Column('net_interest_income', sa.Numeric(18, 2)),            # EUR millions
        sa.Column('non_interest_income', sa.Numeric(18, 2)),
        sa.Column('net_fee_commission_income', sa.Numeric(18, 2)),
        sa.Column('trading_income', sa.Numeric(18, 2)),
        sa.Column('total_operating_income', sa.Numeric(18, 2)),
        sa.Column('total_operating_expenses', sa.Numeric(18, 2)),
        sa.Column('cost_income_ratio', sa.Numeric(5, 2)),               # %
        sa.Column('staff_costs', sa.Numeric(18, 2)),
        sa.Column('impairment_charges', sa.Numeric(18, 2)),             # ECL P&L charge
        sa.Column('profit_before_tax', sa.Numeric(18, 2)),
        sa.Column('income_tax', sa.Numeric(18, 2)),
        sa.Column('net_profit', sa.Numeric(18, 2)),
        sa.Column('attributable_to_shareholders', sa.Numeric(18, 2)),
        sa.Column('eps_diluted', sa.Numeric(8, 4)),
        sa.Column('roe', sa.Numeric(6, 3)),                            # Return on Equity %
        sa.Column('rote', sa.Numeric(6, 3)),                            # Return on Tangible Equity %
        sa.Column('roa', sa.Numeric(6, 4)),                            # Return on Assets %

        # --- Balance Sheet ---
        sa.Column('total_assets', sa.Numeric(18, 2)),
        sa.Column('loans_and_advances_gross', sa.Numeric(18, 2)),
        sa.Column('loans_and_advances_net', sa.Numeric(18, 2)),
        sa.Column('loan_loss_provisions', sa.Numeric(18, 2)),
        sa.Column('investment_securities', sa.Numeric(18, 2)),
        sa.Column('trading_assets', sa.Numeric(18, 2)),
        sa.Column('total_customer_deposits', sa.Numeric(18, 2)),
        sa.Column('total_equity', sa.Numeric(18, 2)),
        sa.Column('tangible_equity', sa.Numeric(18, 2)),
        sa.Column('total_debt', sa.Numeric(18, 2)),
        sa.Column('aum', sa.Numeric(18, 2)),                           # Assets Under Management (for AM divisions)

        # --- Capital Adequacy (Basel III/IV + CRR) ---
        sa.Column('cet1_ratio_pct', sa.Numeric(5, 2)),                 # Common Equity Tier 1
        sa.Column('tier1_ratio_pct', sa.Numeric(5, 2)),
        sa.Column('total_capital_ratio_pct', sa.Numeric(5, 2)),
        sa.Column('cet1_fully_loaded_pct', sa.Numeric(5, 2)),          # excluding transitional arrangements
        sa.Column('leverage_ratio_pct', sa.Numeric(5, 2)),
        sa.Column('rwa', sa.Numeric(18, 2)),                           # Risk-Weighted Assets
        sa.Column('lcr_pct', sa.Numeric(6, 2)),                        # Liquidity Coverage Ratio
        sa.Column('nsfr_pct', sa.Numeric(6, 2)),                       # Net Stable Funding Ratio
        sa.Column('mrel_ratio_pct', sa.Numeric(5, 2)),                  # Minimum Requirement for Eligible Liabilities

        # --- Asset Quality ---
        sa.Column('npl_ratio_pct', sa.Numeric(5, 2)),                  # Non-Performing Loans
        sa.Column('npl_coverage_ratio_pct', sa.Numeric(5, 2)),
        sa.Column('cost_of_risk_bps', sa.Numeric(6, 1)),               # Impairments / avg net loans (basis points)
        sa.Column('stage1_loans_pct', sa.Numeric(5, 2)),               # % of book in IFRS 9 Stage 1
        sa.Column('stage2_loans_pct', sa.Numeric(5, 2)),
        sa.Column('stage3_loans_pct', sa.Numeric(5, 2)),

        # --- Market ---
        sa.Column('market_cap', sa.Numeric(18, 2)),
        sa.Column('price_to_book', sa.Numeric(6, 3)),
        sa.Column('dividend_per_share', sa.Numeric(8, 4)),
        sa.Column('dividend_payout_ratio_pct', sa.Numeric(5, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_financials_entity', 'fi_financials', ['entity_id'])
    op.create_index('ix_fi_financials_year', 'fi_financials', ['reporting_year'])

    # =========================================================================
    # 3. FI LOAN BOOKS  (lending portfolio by sector/geography/product)
    # =========================================================================
    op.create_table(
        'fi_loan_books',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='EUR'),

        # --- Sector decomposition (EUR millions EAD) ---
        sa.Column('sector_breakdown', JSONB),                           # [{sector_gics, sector_nace, ead_meur, npl_ratio_pct, coverage_ratio_pct, stage_mix}]

        # Top sectors (denormalized for quick querying — based on ING/BNP/SocGen disclosures)
        sa.Column('real_estate_commercial_ead', sa.Numeric(15, 2)),
        sa.Column('real_estate_residential_ead', sa.Numeric(15, 2)),
        sa.Column('energy_oil_gas_ead', sa.Numeric(15, 2)),
        sa.Column('energy_renewables_ead', sa.Numeric(15, 2)),
        sa.Column('utilities_ead', sa.Numeric(15, 2)),
        sa.Column('chemicals_ead', sa.Numeric(15, 2)),
        sa.Column('industrials_ead', sa.Numeric(15, 2)),
        sa.Column('transport_ead', sa.Numeric(15, 2)),
        sa.Column('agriculture_ead', sa.Numeric(15, 2)),
        sa.Column('mining_ead', sa.Numeric(15, 2)),
        sa.Column('consumer_discretionary_ead', sa.Numeric(15, 2)),
        sa.Column('consumer_staples_ead', sa.Numeric(15, 2)),
        sa.Column('financials_ead', sa.Numeric(15, 2)),
        sa.Column('technology_ead', sa.Numeric(15, 2)),
        sa.Column('healthcare_ead', sa.Numeric(15, 2)),
        sa.Column('government_public_ead', sa.Numeric(15, 2)),
        sa.Column('sme_ead', sa.Numeric(15, 2)),
        sa.Column('retail_mortgage_ead', sa.Numeric(15, 2)),
        sa.Column('retail_consumer_ead', sa.Numeric(15, 2)),

        # --- Geographic decomposition ---
        sa.Column('geography_breakdown', JSONB),                        # [{country_iso, region, ead_meur, pct_of_total}]

        # --- Product breakdown ---
        sa.Column('product_breakdown', JSONB),                          # [{product, ead_meur, avg_maturity_years, avg_spread_bps}]

        # --- Climate high-risk sector exposures (ESRS E1 / EBA Pillar 3 ESG) ---
        sa.Column('fossil_fuel_extraction_ead', sa.Numeric(15, 2)),     # coal + oil + gas extraction
        sa.Column('coal_mining_ead', sa.Numeric(15, 2)),
        sa.Column('thermal_power_ead', sa.Numeric(15, 2)),
        sa.Column('carbon_intensive_sectors_ead', sa.Numeric(15, 2)),   # all NACE Sections B, C, D, F, H, L
        sa.Column('carbon_intensive_sectors_pct', sa.Numeric(5, 2)),    # % of total loan book

        # --- ESRS E1 — Climate aligned lending ---
        sa.Column('green_loans_ead', sa.Numeric(15, 2)),                # LMA GLP aligned
        sa.Column('sustainability_linked_loans_ead', sa.Numeric(15, 2)), # LMA SLLP aligned
        sa.Column('paris_aligned_ead', sa.Numeric(15, 2)),
        sa.Column('paris_aligned_pct', sa.Numeric(5, 2)),

        # --- Physical risk exposures ---
        sa.Column('flood_zone_re_ead', sa.Numeric(15, 2)),
        sa.Column('coastal_re_ead', sa.Numeric(15, 2)),
        sa.Column('wildfire_risk_ead', sa.Numeric(15, 2)),
        sa.Column('physical_risk_high_ead', sa.Numeric(15, 2)),
        sa.Column('physical_risk_high_pct', sa.Numeric(5, 2)),

        sa.Column('total_ead', sa.Numeric(18, 2)),                      # total book EAD
        sa.Column('total_loans_gross', sa.Numeric(18, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_loan_books_entity', 'fi_loan_books', ['entity_id'])
    op.create_index('ix_fi_loan_books_year', 'fi_loan_books', ['reporting_year'])

    # =========================================================================
    # 4. FI GREEN FINANCE  (sustainable finance volumes — LBP, GBP, SLLP, SBP)
    # =========================================================================
    op.create_table(
        'fi_green_finance',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='EUR'),

        # --- Mobilised / Facilitated volumes (EUR billions) ---
        sa.Column('sustainable_finance_total_bn', sa.Numeric(10, 2)),   # total cumulative or annual
        sa.Column('sustainable_finance_annual_bn', sa.Numeric(10, 2)),  # new in this year
        sa.Column('green_loans_bn', sa.Numeric(10, 2)),                 # LMA Green Loan Principles
        sa.Column('green_bonds_underwritten_bn', sa.Numeric(10, 2)),
        sa.Column('green_bonds_issued_bn', sa.Numeric(10, 2)),          # bank's own green bond issuance
        sa.Column('sustainability_linked_loans_bn', sa.Numeric(10, 2)),
        sa.Column('sustainability_linked_bonds_bn', sa.Numeric(10, 2)),
        sa.Column('social_loans_bn', sa.Numeric(10, 2)),
        sa.Column('social_bonds_bn', sa.Numeric(10, 2)),
        sa.Column('transition_finance_bn', sa.Numeric(10, 2)),          # for brown-to-green transition
        sa.Column('blended_finance_bn', sa.Numeric(10, 2)),             # MDB/DFI blended structures
        sa.Column('climate_finance_bn', sa.Numeric(10, 2)),             # per OECD DAC definition
        sa.Column('nature_finance_bn', sa.Numeric(10, 2)),              # NbS / biodiversity
        sa.Column('affordable_housing_bn', sa.Numeric(10, 2)),          # social housing
        sa.Column('sme_sustainability_bn', sa.Numeric(10, 2)),          # SME sustainability lending

        # Taxonomy alignment of green finance book
        sa.Column('eu_taxonomy_aligned_green_bn', sa.Numeric(10, 2)),
        sa.Column('eu_taxonomy_eligible_green_bn', sa.Numeric(10, 2)),
        sa.Column('eu_taxonomy_aligned_pct', sa.Numeric(5, 2)),

        # Cumulative targets (bank-level commitments)
        sa.Column('cumulative_target_bn', sa.Numeric(10, 2)),           # e.g. ING: €125bn by 2025
        sa.Column('target_year', sa.Integer),
        sa.Column('progress_pct', sa.Numeric(5, 2)),

        # Use of proceeds (ICMA categories)
        sa.Column('use_of_proceeds_breakdown', JSONB),                  # [{category, amount_bn, pct}]
        # Categories: RE_energy_efficiency, renewable_energy, clean_transport, water, biodiversity, circular_economy, clean_energy, sustainable_food_land

        # Framework certifications
        sa.Column('has_green_bond_framework', sa.Boolean, default=False),
        sa.Column('green_bond_framework_verifier', sa.String(100)),     # Sustainalytics | ISS | Vigeo | S&P | DNV
        sa.Column('has_sustainable_finance_framework', sa.Boolean, default=False),

        # Exclusions and controversies
        sa.Column('coal_phase_out_committed', sa.Boolean, default=False),
        sa.Column('coal_phase_out_year', sa.Integer),
        sa.Column('new_coal_mines_committed', sa.Boolean, default=False), # committed to no new coal mines

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_green_finance_entity', 'fi_green_finance', ['entity_id'])
    op.create_index('ix_fi_green_finance_year', 'fi_green_finance', ['reporting_year'])

    # =========================================================================
    # 5. FI FINANCED EMISSIONS  (PCAF per asset class, ESRS E1 + GHG Protocol)
    # =========================================================================
    op.create_table(
        'fi_financed_emissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('pcaf_methodology_version', sa.String(20), default='PCAF_v2'),

        # --- Own operations emissions (ESRS E1) ---
        sa.Column('own_scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('own_scope2_market_tco2e', sa.Numeric(14, 4)),
        sa.Column('own_scope2_location_tco2e', sa.Numeric(14, 4)),
        sa.Column('own_scope3_total_tco2e', sa.Numeric(14, 4)),
        sa.Column('own_scope3_by_category', JSONB),                     # {cat1: x, cat2: x, ...cat15: x}
        sa.Column('own_total_tco2e', sa.Numeric(14, 4)),
        sa.Column('own_energy_consumption_mwh', sa.Numeric(14, 2)),
        sa.Column('own_renewable_energy_pct', sa.Numeric(5, 2)),
        sa.Column('own_offices_m2', sa.Numeric(12, 2)),
        sa.Column('own_energy_intensity_kwh_m2', sa.Numeric(10, 3)),
        sa.Column('own_carbon_intensity_kgco2_m2', sa.Numeric(10, 3)),
        sa.Column('own_business_travel_km', sa.Numeric(14, 2)),
        sa.Column('own_fleet_vehicles', sa.Integer),
        sa.Column('own_electric_vehicles_pct', sa.Numeric(5, 2)),

        # --- Financed emissions (PCAF Category 15 proxy for banks) ---
        sa.Column('financed_scope1_tco2e', sa.Numeric(18, 4)),
        sa.Column('financed_scope2_tco2e', sa.Numeric(18, 4)),
        sa.Column('financed_scope3_tco2e', sa.Numeric(18, 4)),
        sa.Column('total_financed_tco2e', sa.Numeric(18, 4)),

        # PCAF asset class breakdown (tCO2e + attribution factor + DQ)
        sa.Column('listed_equity_emissions', JSONB),                    # {abs_tco2e, attributed_tco2e, avg_dq, coverage_pct}
        sa.Column('corporate_bonds_emissions', JSONB),
        sa.Column('business_loans_emissions', JSONB),
        sa.Column('commercial_re_loans_emissions', JSONB),
        sa.Column('mortgages_emissions', JSONB),
        sa.Column('project_finance_emissions', JSONB),
        sa.Column('sovereign_bonds_emissions', JSONB),
        sa.Column('motor_vehicle_loans_emissions', JSONB),

        # PCAF portfolio-level metrics
        sa.Column('waci_tco2e_per_mrevenue', sa.Numeric(12, 4)),        # Weighted Average Carbon Intensity
        sa.Column('carbon_footprint_tco2e_per_meur_invested', sa.Numeric(12, 4)),
        sa.Column('portfolio_coverage_pct', sa.Numeric(5, 2)),
        sa.Column('weighted_avg_dq', sa.Numeric(3, 1)),

        # Temperature alignment (SBTi FI Guidance / PACTA)
        sa.Column('portfolio_temperature_c', sa.Numeric(4, 2)),
        sa.Column('aligned_1_5c_pct', sa.Numeric(5, 2)),
        sa.Column('aligned_2c_pct', sa.Numeric(5, 2)),
        sa.Column('misaligned_pct', sa.Numeric(5, 2)),
        sa.Column('no_target_pct', sa.Numeric(5, 2)),
        sa.Column('pacta_technology_mix', JSONB),                       # {sector: {low_carbon_pct, high_carbon_pct}}

        # Sector-level financed emissions
        sa.Column('sector_financed_emissions', JSONB),                  # {sector: {attributed_tco2e, waci, pct_of_total}}

        # Targets
        sa.Column('net_zero_target_year', sa.Integer),
        sa.Column('intermediate_target_year', sa.Integer),
        sa.Column('intermediate_reduction_vs_base_pct', sa.Numeric(5, 2)),
        sa.Column('base_year', sa.Integer),
        sa.Column('base_year_financed_emissions_tco2e', sa.Numeric(18, 4)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_financed_emissions_entity', 'fi_financed_emissions', ['entity_id'])
    op.create_index('ix_fi_financed_emissions_year', 'fi_financed_emissions', ['reporting_year'])

    # =========================================================================
    # 6. FI PARIS ALIGNMENT  (PACTA / SBTi FI / IEA NZE sector targets)
    # =========================================================================
    op.create_table(
        'fi_paris_alignment',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),
        sa.Column('methodology', sa.String(30), default='PACTA'),       # PACTA | SBTi_FI | IEA_NZE | CRREM | PCAF_IG

        # Sector-level alignment (IEA NZE / PACTA benchmarks)
        # For each high-impact sector: aligned volume, non-aligned, reduction needed
        sa.Column('power_sector_alignment', JSONB),                     # {aligned_ead_meur, not_aligned_meur, avg_ci_gco2_kwh, target_ci, alignment_pct}
        sa.Column('oil_gas_alignment', JSONB),
        sa.Column('coal_alignment', JSONB),
        sa.Column('automotive_alignment', JSONB),
        sa.Column('steel_alignment', JSONB),
        sa.Column('cement_alignment', JSONB),
        sa.Column('aviation_alignment', JSONB),
        sa.Column('shipping_alignment', JSONB),
        sa.Column('real_estate_alignment', JSONB),                      # CRREM pathway

        # Overall portfolio alignment score
        sa.Column('portfolio_alignment_score', sa.Numeric(5, 2)),       # 0-100
        sa.Column('portfolio_alignment_category', sa.String(20)),       # Aligned | Partially_Aligned | Not_Aligned

        # Engagement and stewardship
        sa.Column('engaged_companies_count', sa.Integer),
        sa.Column('engagement_topics', JSONB),                          # [{topic, companies_count, success_rate}]
        sa.Column('voted_resolutions_climate_count', sa.Integer),
        sa.Column('voted_for_climate_pct', sa.Numeric(5, 2)),
        sa.Column('escalation_actions_count', sa.Integer),
        sa.Column('divestment_count', sa.Integer),                      # companies divested due to misalignment

        # Exclusion policies
        sa.Column('thermal_coal_threshold_revenue_pct', sa.Numeric(5, 2), default=5.0),  # e.g. ING <5%
        sa.Column('oil_sands_excluded', sa.Boolean, default=False),
        sa.Column('arctic_drilling_excluded', sa.Boolean, default=False),
        sa.Column('mountaintop_removal_excluded', sa.Boolean, default=False),
        sa.Column('new_coal_power_excluded', sa.Boolean, default=False),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_paris_alignment_entity', 'fi_paris_alignment', ['entity_id'])
    op.create_index('ix_fi_paris_alignment_year', 'fi_paris_alignment', ['reporting_year'])

    # =========================================================================
    # 7. FI CSRD E1 CLIMATE  (ESRS E1 mandatory disclosures for FIs)
    # =========================================================================
    op.create_table(
        'fi_csrd_e1_climate',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # ESRS E1-1: Transition plan for climate change mitigation
        sa.Column('has_transition_plan', sa.Boolean, default=False),
        sa.Column('transition_plan_aligned_paris', sa.Boolean),
        sa.Column('transition_plan_scope', sa.String(200)),
        sa.Column('transition_plan_base_year', sa.Integer),
        sa.Column('transition_plan_target_year', sa.Integer, default=2050),
        sa.Column('sbti_committed', sa.Boolean, default=False),
        sa.Column('sbti_approval_date', sa.Date),
        sa.Column('net_zero_target_year', sa.Integer),

        # ESRS E1-2: Policies related to climate change mitigation and adaptation
        sa.Column('climate_policy_in_place', sa.Boolean, default=True),
        sa.Column('climate_policy_board_approved', sa.Boolean),
        sa.Column('sector_policies', JSONB),                            # [{sector, policy_description, threshold, exclusion}]

        # ESRS E1-4: Targets for climate change mitigation and adaptation
        sa.Column('absolute_scope1_target_pct', sa.Numeric(5, 2)),     # % reduction vs base year
        sa.Column('absolute_scope2_target_pct', sa.Numeric(5, 2)),
        sa.Column('absolute_scope3_target_pct', sa.Numeric(5, 2)),
        sa.Column('financed_emissions_target_pct', sa.Numeric(5, 2)),  # % reduction in financed emissions
        sa.Column('intensity_target_tco2e_per_meur_invested', sa.Numeric(8, 4)),
        sa.Column('renewable_energy_target_pct', sa.Numeric(5, 2)),

        # ESRS E1-5: Energy consumption and mix
        sa.Column('total_energy_consumption_mwh', sa.Numeric(14, 2)),
        sa.Column('fossil_fuel_consumption_mwh', sa.Numeric(14, 2)),
        sa.Column('nuclear_consumption_mwh', sa.Numeric(14, 2)),
        sa.Column('renewable_consumption_mwh', sa.Numeric(14, 2)),
        sa.Column('renewable_energy_pct', sa.Numeric(5, 2)),
        sa.Column('has_100pct_renewable_electricity', sa.Boolean, default=False),
        sa.Column('re100_committed', sa.Boolean, default=False),
        sa.Column('ppa_capacity_mw', sa.Numeric(8, 3)),

        # ESRS E1-6: GHG emissions (own operations)
        sa.Column('scope1_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope2_market_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope2_location_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope3_total_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope3_cat15_financed_tco2e', sa.Numeric(18, 4)),   # Cat 15 = investments
        sa.Column('biogenic_co2_tco2e', sa.Numeric(12, 4)),
        sa.Column('ghg_removals_tco2e', sa.Numeric(12, 4)),
        sa.Column('carbon_credits_retired_tco2e', sa.Numeric(12, 4)),
        sa.Column('carbon_credit_standard', sa.String(50)),             # GS | VCS | CRU | UK_ETS

        # ESRS E1-7: Carbon credits and removal
        sa.Column('scope1_base_year', sa.Integer),
        sa.Column('scope1_base_year_tco2e', sa.Numeric(14, 4)),
        sa.Column('scope1_yoy_change_pct', sa.Numeric(7, 3)),
        sa.Column('scope2_yoy_change_pct', sa.Numeric(7, 3)),
        sa.Column('financed_yoy_change_pct', sa.Numeric(7, 3)),

        # Physical risk exposures (ESRS E1-9)
        sa.Column('physical_risk_assessment_completed', sa.Boolean, default=False),
        sa.Column('acute_risk_high_ead_meur', sa.Numeric(15, 2)),
        sa.Column('chronic_risk_high_ead_meur', sa.Numeric(15, 2)),
        sa.Column('flood_exposed_re_ead_meur', sa.Numeric(15, 2)),
        sa.Column('heat_stress_exposed_ead_meur', sa.Numeric(15, 2)),

        # Internal carbon price
        sa.Column('has_internal_carbon_price', sa.Boolean, default=False),
        sa.Column('internal_carbon_price_eur_t', sa.Numeric(8, 2)),
        sa.Column('shadow_carbon_price_eur_t', sa.Numeric(8, 2)),       # used in scenario modelling

        # Climate scenario analysis (ESRS E1-3)
        sa.Column('climate_scenarios_used', JSONB),                     # [{name, type, horizon, source}]
        sa.Column('transition_risk_quantified', sa.Boolean, default=False),
        sa.Column('transition_risk_max_impact_pct_cet1', sa.Numeric(5, 2)),
        sa.Column('physical_risk_max_impact_pct_cet1', sa.Numeric(5, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_csrd_e1_entity', 'fi_csrd_e1_climate', ['entity_id'])
    op.create_index('ix_fi_csrd_e1_year', 'fi_csrd_e1_climate', ['reporting_year'])

    # =========================================================================
    # 8. FI CSRD S1 WORKFORCE  (ESRS S1 own workforce — banks employ 50k–300k)
    # =========================================================================
    op.create_table(
        'fi_csrd_s1_workforce',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # ESRS S1-6: Headcount characteristics
        sa.Column('total_headcount', sa.Integer),
        sa.Column('total_fte', sa.Numeric(10, 1)),
        sa.Column('permanent_employees', sa.Integer),
        sa.Column('temporary_employees', sa.Integer),
        sa.Column('contractors', sa.Integer),
        sa.Column('full_time_pct', sa.Numeric(5, 2)),
        sa.Column('part_time_pct', sa.Numeric(5, 2)),
        sa.Column('female_pct', sa.Numeric(5, 2)),
        sa.Column('male_pct', sa.Numeric(5, 2)),
        sa.Column('under30_pct', sa.Numeric(5, 2)),
        sa.Column('age30_50_pct', sa.Numeric(5, 2)),
        sa.Column('over50_pct', sa.Numeric(5, 2)),
        sa.Column('headcount_by_country', JSONB),                       # [{country_iso, headcount, pct}]
        sa.Column('headcount_by_division', JSONB),                      # [{division, headcount, female_pct}]

        # ESRS S1-7: Collective bargaining and social protection
        sa.Column('union_membership_pct', sa.Numeric(5, 2)),
        sa.Column('collective_bargaining_coverage_pct', sa.Numeric(5, 2)),
        sa.Column('work_council_in_place', sa.Boolean, default=True),

        # ESRS S1-8: Adequate wages
        sa.Column('living_wage_compliant', sa.Boolean),
        sa.Column('minimum_wage_countries', JSONB),                     # [{country_iso, min_wage_ratio_to_living_wage}]

        # ESRS S1-9: Social protection coverage
        sa.Column('social_protection_coverage_pct', sa.Numeric(5, 2)),

        # ESRS S1-10: Gender pay gap
        sa.Column('unadjusted_gender_pay_gap_pct', sa.Numeric(5, 2)),  # female median pay / male median pay − 1
        sa.Column('adjusted_gender_pay_gap_pct', sa.Numeric(5, 2)),    # like-for-like
        sa.Column('gender_pay_gap_by_level', JSONB),                   # [{level, gap_pct}]
        sa.Column('equal_pay_certification', sa.Boolean, default=False),

        # ESRS S1-11: Work-life balance
        sa.Column('parental_leave_entitlement_weeks', sa.Integer),
        sa.Column('parental_leave_return_rate_pct', sa.Numeric(5, 2)),

        # ESRS S1-13: Training and skills development
        sa.Column('avg_training_hours_pa', sa.Numeric(6, 2)),
        sa.Column('total_training_hours', sa.Numeric(14, 2)),
        sa.Column('training_spend_per_fte_eur', sa.Numeric(8, 2)),
        sa.Column('digital_skills_training_pct', sa.Numeric(5, 2)),    # % who received digital/AI upskilling

        # ESRS S1-14: Diversity and inclusion
        sa.Column('women_in_leadership_pct', sa.Numeric(5, 2)),        # Senior VP and above
        sa.Column('women_on_board_pct', sa.Numeric(5, 2)),
        sa.Column('women_in_executive_committee_pct', sa.Numeric(5, 2)),
        sa.Column('nationality_diversity_score', sa.Numeric(4, 2)),    # number of nationalities / total headcount proxy
        sa.Column('has_dei_programme', sa.Boolean, default=True),
        sa.Column('has_reverse_mentoring', sa.Boolean, default=False),

        # ESRS S1-15: Incidents
        sa.Column('fatal_accidents_employees', sa.Integer, default=0),
        sa.Column('ltir_per_million_hours', sa.Numeric(6, 3)),         # Lost Time Injury Rate
        sa.Column('trir_per_million_hours', sa.Numeric(6, 3)),         # Total Recordable Incident Rate
        sa.Column('absenteeism_rate_pct', sa.Numeric(5, 2)),
        sa.Column('work_related_illnesses', sa.Integer),

        # ESRS S1-16: Remuneration
        sa.Column('ceo_pay_ratio', sa.Numeric(6, 1)),                   # CEO total pay / median employee pay
        sa.Column('cfo_pay_ratio', sa.Numeric(6, 1)),
        sa.Column('esg_linked_exec_pay_pct', sa.Numeric(5, 2)),        # % of exec variable pay linked to ESG

        # Employee engagement
        sa.Column('employee_engagement_score_pct', sa.Numeric(5, 2)),
        sa.Column('employee_nps', sa.SmallInteger),                    # eNPS −100 to +100
        sa.Column('voluntary_attrition_rate_pct', sa.Numeric(5, 2)),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_csrd_s1_entity', 'fi_csrd_s1_workforce', ['entity_id'])
    op.create_index('ix_fi_csrd_s1_year', 'fi_csrd_s1_workforce', ['reporting_year'])

    # =========================================================================
    # 9. FI CSRD G1 GOVERNANCE  (ESRS G1 business conduct)
    # =========================================================================
    op.create_table(
        'fi_csrd_g1_governance',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Board composition
        sa.Column('board_members_total', sa.SmallInteger),
        sa.Column('board_independent_pct', sa.Numeric(5, 2)),
        sa.Column('board_female_pct', sa.Numeric(5, 2)),
        sa.Column('board_avg_tenure_years', sa.Numeric(4, 1)),
        sa.Column('board_meetings_per_year', sa.SmallInteger),
        sa.Column('board_esg_committee', sa.Boolean, default=False),
        sa.Column('board_climate_expertise_pct', sa.Numeric(5, 2)),

        # ESRS G1-1: Corporate culture and business conduct policies
        sa.Column('code_of_conduct_in_place', sa.Boolean, default=True),
        sa.Column('anti_corruption_policy', sa.Boolean, default=True),
        sa.Column('anti_bribery_policy', sa.Boolean, default=True),
        sa.Column('supplier_code_of_conduct', sa.Boolean, default=True),
        sa.Column('whistleblower_mechanism', sa.Boolean, default=True),
        sa.Column('whistleblower_reports_received', sa.Integer),
        sa.Column('whistleblower_substantiated_pct', sa.Numeric(5, 2)),

        # ESRS G1-4: Incidents of corruption and bribery
        sa.Column('corruption_incidents', sa.Integer, default=0),
        sa.Column('bribery_incidents', sa.Integer, default=0),
        sa.Column('fines_for_misconduct_meur', sa.Numeric(10, 2)),
        sa.Column('regulatory_sanctions_count', sa.Integer, default=0),

        # ESRS G1-5: Political engagement and lobbying
        sa.Column('lobbying_spend_meur', sa.Numeric(10, 2)),
        sa.Column('political_donations_meur', sa.Numeric(10, 2)),
        sa.Column('industry_associations', JSONB),                      # [{name, role, dues_meur}]

        # ESRS G1-6: Payment practices
        sa.Column('avg_payment_days_supplier', sa.Numeric(5, 1)),
        sa.Column('overdue_payments_pct', sa.Numeric(5, 2)),

        # Tax transparency
        sa.Column('effective_tax_rate_pct', sa.Numeric(5, 2)),
        sa.Column('tax_paid_meur', sa.Numeric(14, 2)),
        sa.Column('tax_country_by_country_published', sa.Boolean, default=False),
        sa.Column('tax_havens_operations_count', sa.Integer),

        # Risk management and internal audit
        sa.Column('risk_management_framework', sa.String(50)),           # three_lines | COSO | ISO31000
        sa.Column('internal_audit_esg_reviews', sa.Integer),
        sa.Column('material_weaknesses_identified', sa.Integer, default=0),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_csrd_g1_entity', 'fi_csrd_g1_governance', ['entity_id'])
    op.create_index('ix_fi_csrd_g1_year', 'fi_csrd_g1_governance', ['reporting_year'])

    # =========================================================================
    # 10. FI EU TAXONOMY KPIs  (CRR Article 449a — Green Asset Ratio, BTAR)
    # =========================================================================
    op.create_table(
        'fi_eu_taxonomy_kpis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('fi_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reporting_year', sa.Integer, nullable=False),

        # Green Asset Ratio (GAR) — on-balance sheet
        sa.Column('gar_total_pct', sa.Numeric(5, 2)),                   # Taxonomy-aligned assets / total assets
        sa.Column('gar_flow_pct', sa.Numeric(5, 2)),                    # new green finance in year / total new finance
        sa.Column('gar_stock_numerator_meur', sa.Numeric(15, 2)),
        sa.Column('gar_denominator_meur', sa.Numeric(15, 2)),

        # GAR by environmental objective
        sa.Column('gar_climate_mitigation_pct', sa.Numeric(5, 2)),
        sa.Column('gar_climate_adaptation_pct', sa.Numeric(5, 2)),
        sa.Column('gar_water_pct', sa.Numeric(5, 2)),
        sa.Column('gar_circular_economy_pct', sa.Numeric(5, 2)),
        sa.Column('gar_pollution_pct', sa.Numeric(5, 2)),
        sa.Column('gar_biodiversity_pct', sa.Numeric(5, 2)),

        # GAR by asset class
        sa.Column('gar_re_loans_pct', sa.Numeric(5, 2)),
        sa.Column('gar_corporate_loans_pct', sa.Numeric(5, 2)),
        sa.Column('gar_project_finance_pct', sa.Numeric(5, 2)),

        # Banking Book Taxonomy Alignment Ratio (BTAR) — off-balance sheet
        sa.Column('btar_total_pct', sa.Numeric(5, 2)),

        # EU Taxonomy eligible but not aligned
        sa.Column('taxonomy_eligible_not_aligned_pct', sa.Numeric(5, 2)),

        # DNSH compliance rate across portfolio
        sa.Column('dnsh_compliant_pct', sa.Numeric(5, 2)),

        # Covered assets for Taxonomy (denominator scope)
        sa.Column('covered_assets_meur', sa.Numeric(15, 2)),
        sa.Column('covered_assets_pct_of_total', sa.Numeric(5, 2)),
        sa.Column('excluded_assets', JSONB),                            # [{asset_type, meur, reason}] — sovereigns, central banks, etc.

        # Target GAR
        sa.Column('gar_target_pct', sa.Numeric(5, 2)),
        sa.Column('gar_target_year', sa.Integer),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_fi_eu_tax_kpis_entity', 'fi_eu_taxonomy_kpis', ['entity_id'])
    op.create_index('ix_fi_eu_tax_kpis_year', 'fi_eu_taxonomy_kpis', ['reporting_year'])


def downgrade():
    op.drop_table('fi_eu_taxonomy_kpis')
    op.drop_table('fi_csrd_g1_governance')
    op.drop_table('fi_csrd_s1_workforce')
    op.drop_table('fi_csrd_e1_climate')
    op.drop_table('fi_paris_alignment')
    op.drop_table('fi_financed_emissions')
    op.drop_table('fi_green_finance')
    op.drop_table('fi_loan_books')
    op.drop_table('fi_financials')
    op.drop_table('fi_entities')
