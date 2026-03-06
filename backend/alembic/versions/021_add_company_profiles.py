"""Add company_profiles — comprehensive entity identity, sector, prudential and Pillar 3 datapoints

Revision ID: 021
Revises: 016
Create Date: 2026-03-04

Covers:
  - Core identity (LEI, ISIN, legal / trading name, jurisdiction, listing)
  - Sector classification (GICS, NACE, NAICS, SIC)
  - Financial institution type + regulatory perimeter (G-SIB, D-SIB)
  - Corporate reporting (revenue, assets, employees, fiscal year)
  - Basel III prudential metrics (CET1, T1, TCR, leverage, LCR, NSFR, RWA, NPL)
  - Pillar 3 ESG disclosures (GAR, BTAR, financed emissions, physical/transition risk exposure)
  - Solvency II metrics for insurers (SCR, MCR, own funds, combined ratio)
  - Asset manager metrics (AUM, RI AUM, engagement)
  - Climate / net-zero commitments (NZBA, PCAF, SBTi, TCFD, TNFD, CDP, UN PRB)
  - Links to csrd_entity_registry and csrd_report_uploads
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "021_add_company_profiles"
down_revision = "016_add_csrd_report_uploads"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "company_profiles",

        # ── Primary key & registry links ─────────────────────────────────
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_registry_id", sa.String(36), nullable=True,
                  comment="FK → csrd_entity_registry.id (if report processed)"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("data_source", sa.String(100), nullable=True,
                  comment="'csrd_report' | 'analyst_estimate' | 'manual'"),

        # ── Core identity ─────────────────────────────────────────────────
        sa.Column("legal_name", sa.String(300), nullable=False),
        sa.Column("trading_name", sa.String(300), nullable=True),
        sa.Column("entity_lei", sa.String(20), nullable=True, comment="GLEIF LEI 20-char"),
        sa.Column("isin_primary", sa.String(12), nullable=True),
        sa.Column("ticker_symbol", sa.String(20), nullable=True),
        sa.Column("bloomberg_ticker", sa.String(30), nullable=True),
        sa.Column("reuters_ric", sa.String(30), nullable=True),
        sa.Column("cusip", sa.String(9), nullable=True),
        sa.Column("stock_exchange", sa.String(50), nullable=True),
        sa.Column("listing_status", sa.String(20), nullable=True,
                  comment="'Listed' | 'Unlisted' | 'State-Owned' | 'Cooperative'"),
        sa.Column("incorporation_country", sa.String(3), nullable=True, comment="ISO 3166-1 alpha-3"),
        sa.Column("headquarters_city", sa.String(100), nullable=True),
        sa.Column("headquarters_country", sa.String(3), nullable=True, comment="ISO 3166-1 alpha-3"),
        sa.Column("registered_address", sa.Text, nullable=True),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("sustainability_report_url", sa.String(500), nullable=True),
        sa.Column("founded_year", sa.Integer, nullable=True),
        sa.Column("fiscal_year_end", sa.String(5), nullable=True, comment="MM-DD e.g. '12-31'"),
        sa.Column("parent_entity_lei", sa.String(20), nullable=True,
                  comment="GLEIF LEI of ultimate parent"),

        # ── Sector classification ─────────────────────────────────────────
        sa.Column("gics_sector", sa.String(100), nullable=True),
        sa.Column("gics_industry_group", sa.String(100), nullable=True),
        sa.Column("gics_industry", sa.String(100), nullable=True),
        sa.Column("gics_sub_industry", sa.String(100), nullable=True),
        sa.Column("nace_code", sa.String(10), nullable=True, comment="EU NACE Rev 2 code"),
        sa.Column("naics_code", sa.String(10), nullable=True, comment="6-digit NAICS"),
        sa.Column("sic_code", sa.String(6), nullable=True),
        sa.Column("primary_sector", sa.String(100), nullable=True,
                  comment="High-level sector for platform routing"),

        # ── Corporate financials (from ESRS2 / annual report) ────────────
        sa.Column("reporting_year", sa.Integer, nullable=True),
        sa.Column("total_assets_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("annual_revenue_eur_mn", sa.Numeric(18, 2), nullable=True),
        sa.Column("net_profit_eur_mn", sa.Numeric(18, 2), nullable=True),
        sa.Column("market_cap_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("enterprise_value_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("employees_fte", sa.Integer, nullable=True),
        sa.Column("employees_female_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("employees_management_female_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("credit_rating_sp", sa.String(10), nullable=True),
        sa.Column("credit_rating_moodys", sa.String(10), nullable=True),
        sa.Column("credit_rating_fitch", sa.String(10), nullable=True),

        # ── Regulatory perimeter ──────────────────────────────────────────
        sa.Column("is_financial_institution", sa.Boolean, server_default="false", nullable=False),
        sa.Column("institution_type", sa.String(60), nullable=True,
                  comment="'Bank' | 'Insurance' | 'Asset Manager' | 'Pension Fund' | 'Corporate' | 'Energy' | 'RE'"),
        sa.Column("regulatory_supervisor", sa.String(100), nullable=True,
                  comment="e.g. ECB/SSM, PRA, FCA, MAS, FINMA, APRA, HKMA, FSB"),
        sa.Column("regulatory_framework", sa.String(100), nullable=True,
                  comment="CRR/CRD6, Solvency II, AIFMD, MiFID II, MAS 637, APRA APS"),
        sa.Column("systemic_importance", sa.String(20), nullable=True,
                  comment="'G-SIB' | 'D-SIB' | 'G-SII' | 'D-SII' | 'None'"),
        sa.Column("systemic_importance_bucket", sa.Integer, nullable=True,
                  comment="FSB G-SIB bucket 1-5 (higher = more systemic)"),
        sa.Column("deposit_guarantee_scheme", sa.String(100), nullable=True),

        # ── Basel III / CRR Prudential Metrics (Banks) ───────────────────
        sa.Column("cet1_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Common Equity Tier 1 ratio (%)"),
        sa.Column("tier1_capital_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Tier 1 capital ratio (%)"),
        sa.Column("total_capital_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Total capital ratio (CRR Article 92)"),
        sa.Column("leverage_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Basel III leverage ratio — Tier 1 / total exposure (%)"),
        sa.Column("lcr_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Liquidity Coverage Ratio — HQLA / net outflows (%)"),
        sa.Column("nsfr_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Net Stable Funding Ratio — ASF / RSF (%)"),
        sa.Column("rwa_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="Risk-Weighted Assets (credit + market + operational)"),
        sa.Column("rwa_credit_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("rwa_market_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("rwa_operational_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("total_exposure_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="Total leverage exposure measure"),
        sa.Column("npl_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Non-Performing Loan ratio (%)"),
        sa.Column("npl_coverage_ratio_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("cost_of_risk_bps", sa.Numeric(8, 2), nullable=True,
                  comment="Loan loss provision / avg loans (basis points)"),
        sa.Column("roe_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Return on Equity (%)"),
        sa.Column("roa_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Return on Assets (%)"),
        sa.Column("nim_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Net Interest Margin (%)"),
        sa.Column("cost_income_ratio_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("loan_book_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("deposit_base_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("mreel_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="Minimum Requirement for Eligible Liabilities (MREL)"),
        sa.Column("mrel_met", sa.Boolean, nullable=True),
        sa.Column("pillar2_requirement_pct", sa.Numeric(6, 2), nullable=True,
                  comment="P2R — Pillar 2 requirement set by supervisor (%)"),
        sa.Column("combined_buffer_requirement_pct", sa.Numeric(6, 2), nullable=True,
                  comment="CCB + G-SIB/D-SIB + systemic risk buffer combined (%)"),
        sa.Column("icaap_passed", sa.Boolean, nullable=True,
                  comment="Internal Capital Adequacy Assessment Process result"),
        sa.Column("ilaap_passed", sa.Boolean, nullable=True,
                  comment="Internal Liquidity Adequacy Assessment Process result"),
        sa.Column("srep_composite_score", sa.Integer, nullable=True,
                  comment="ECB SREP composite score 1-4 (1=best)"),

        # ── Pillar 3 ESG Disclosures (EBA ITS, CRR Article 449a) ─────────
        sa.Column("p3_report_url", sa.String(500), nullable=True,
                  comment="URL to published Pillar 3 report"),
        sa.Column("p3_report_date", sa.Date, nullable=True),
        sa.Column("p3_gar_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Green Asset Ratio — Taxonomy-aligned assets / total covered assets (%)"),
        sa.Column("p3_btar_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Banking Book Taxonomy Alignment Ratio (%)"),
        sa.Column("p3_off_balance_sheet_gar_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("p3_transition_risk_exposure_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="Loans + debt securities to high-transition-risk sectors (CRR NACE mapping)"),
        sa.Column("p3_physical_risk_exposure_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="Exposure to assets in high physical risk areas"),
        sa.Column("p3_real_estate_collateral_physical_risk_pct", sa.Numeric(6, 2), nullable=True,
                  comment="% of real estate collateral in flood / heat stress zones"),
        sa.Column("p3_corporate_collateral_physical_risk_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("p3_scope1_tco2e", sa.Numeric(18, 2), nullable=True,
                  comment="Own operations Scope 1 GHG (tCO2e)"),
        sa.Column("p3_scope2_tco2e", sa.Numeric(18, 2), nullable=True,
                  comment="Own operations Scope 2 GHG (tCO2e)"),
        sa.Column("p3_scope3_tco2e", sa.Numeric(18, 2), nullable=True),
        sa.Column("p3_financed_emissions_tco2e", sa.Numeric(18, 2), nullable=True,
                  comment="PCAF-standard financed emissions (absolute, tCO2e)"),
        sa.Column("p3_waci_tco2e_meur", sa.Numeric(10, 4), nullable=True,
                  comment="Weighted Average Carbon Intensity (tCO2e / MEUR revenue)"),
        sa.Column("p3_temperature_alignment_c", sa.Numeric(4, 2), nullable=True,
                  comment="Implied Temperature Rise of loan book (°C)"),
        sa.Column("p3_fossil_fuel_exposure_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="On-balance-sheet exposure to fossil fuel companies"),
        sa.Column("p3_renewable_energy_exposure_eur_bn", sa.Numeric(18, 2), nullable=True),

        # ── ICMA / LMA Green & Sustainable Finance ────────────────────────
        sa.Column("green_bond_issuance_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("sustainability_linked_loans_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("social_bond_issuance_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("sustainable_finance_target_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("sustainable_finance_target_year", sa.Integer, nullable=True),
        sa.Column("sustainable_finance_achieved_eur_bn", sa.Numeric(18, 2), nullable=True),

        # ── Solvency II (Insurance / Reinsurance) ─────────────────────────
        sa.Column("solvency2_scr_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Solvency Capital Requirement coverage ratio (%)"),
        sa.Column("solvency2_mcr_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Minimum Capital Requirement coverage ratio (%)"),
        sa.Column("solvency2_own_funds_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("solvency2_scr_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("solvency2_best_estimate_liabilities_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("combined_ratio_pct", sa.Numeric(6, 2), nullable=True,
                  comment="Non-life: (claims + expenses) / premiums (%)"),
        sa.Column("loss_ratio_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("expense_ratio_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("investment_return_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("climate_nat_cat_exposure_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="Estimated nat-cat loss exposure from climate change"),
        sa.Column("sfcr_report_url", sa.String(500), nullable=True,
                  comment="Solvency & Financial Condition Report URL"),

        # ── Asset Manager / Pension Fund ──────────────────────────────────
        sa.Column("aum_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="Assets Under Management"),
        sa.Column("responsible_investment_aum_eur_bn", sa.Numeric(18, 2), nullable=True),
        sa.Column("responsible_investment_aum_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("article8_aum_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="SFDR Article 8 AUM"),
        sa.Column("article9_aum_eur_bn", sa.Numeric(18, 2), nullable=True,
                  comment="SFDR Article 9 AUM"),
        sa.Column("sfdr_fund_classification", sa.String(20), nullable=True,
                  comment="'Art 6' | 'Art 8' | 'Art 9' — dominant fund classification"),
        sa.Column("engagement_votes_total", sa.Integer, nullable=True),
        sa.Column("engagement_votes_esg_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("shareholder_resolutions_supported_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("stewardship_code_signatory", sa.Boolean, nullable=True),
        sa.Column("stewardship_code_name", sa.String(100), nullable=True,
                  comment="e.g. UK Stewardship Code, Japan Stewardship Code"),

        # ── Energy & Infrastructure Specific ─────────────────────────────
        sa.Column("installed_capacity_gw", sa.Numeric(10, 2), nullable=True),
        sa.Column("renewable_capacity_gw", sa.Numeric(10, 2), nullable=True),
        sa.Column("renewable_capacity_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("power_generation_twh", sa.Numeric(12, 2), nullable=True),
        sa.Column("eu_taxonomy_aligned_capex_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("eu_taxonomy_aligned_revenue_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("eu_taxonomy_aligned_opex_pct", sa.Numeric(6, 2), nullable=True),

        # ── GHG & Energy (own operations — ESRS E1) ───────────────────────
        sa.Column("scope1_tco2e", sa.Numeric(18, 2), nullable=True),
        sa.Column("scope2_tco2e_market", sa.Numeric(18, 2), nullable=True),
        sa.Column("scope2_tco2e_location", sa.Numeric(18, 2), nullable=True),
        sa.Column("scope3_tco2e_total", sa.Numeric(18, 2), nullable=True),
        sa.Column("ghg_intensity_tco2e_meur_revenue", sa.Numeric(10, 4), nullable=True),
        sa.Column("energy_consumption_mwh", sa.Numeric(18, 2), nullable=True),
        sa.Column("renewable_energy_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("water_consumption_m3", sa.Numeric(18, 2), nullable=True),
        sa.Column("waste_recycled_pct", sa.Numeric(6, 2), nullable=True),

        # ── Health & Safety (ESRS S1) ─────────────────────────────────────
        sa.Column("trir", sa.Numeric(8, 4), nullable=True,
                  comment="Total Recordable Injury Rate"),
        sa.Column("ltir", sa.Numeric(8, 4), nullable=True,
                  comment="Lost Time Injury Rate"),
        sa.Column("fatalities", sa.Integer, nullable=True),
        sa.Column("gender_pay_gap_pct", sa.Numeric(6, 2), nullable=True),

        # ── Governance (ESRS G1) ──────────────────────────────────────────
        sa.Column("corruption_incidents", sa.Integer, nullable=True),
        sa.Column("board_size", sa.Integer, nullable=True),
        sa.Column("board_independence_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("board_gender_diversity_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("ceo_pay_ratio", sa.Numeric(8, 1), nullable=True),
        sa.Column("executive_esg_pay_linkage", sa.Boolean, nullable=True),

        # ── Climate / Net-Zero Commitments ────────────────────────────────
        sa.Column("net_zero_target_year", sa.Integer, nullable=True),
        sa.Column("interim_target_year", sa.Integer, nullable=True,
                  comment="Primary interim target year (typically 2030)"),
        sa.Column("interim_emission_reduction_pct", sa.Numeric(6, 2), nullable=True,
                  comment="% reduction vs base year at interim target year"),
        sa.Column("base_year", sa.Integer, nullable=True),
        sa.Column("transition_plan_published", sa.Boolean, nullable=True),
        sa.Column("transition_plan_url", sa.String(500), nullable=True),
        sa.Column("assurance_provider", sa.String(200), nullable=True,
                  comment="Third-party GHG assurance provider name"),
        sa.Column("assurance_level", sa.String(30), nullable=True,
                  comment="'Limited' | 'Reasonable' | 'None'"),

        # ── ESG Memberships / Frameworks ──────────────────────────────────
        sa.Column("nzba_member", sa.Boolean, server_default="false"),
        sa.Column("nzba_commitment_date", sa.Date, nullable=True),
        sa.Column("nzba_financed_sectors", sa.Integer, nullable=True,
                  comment="Number of NZBA sectors with targets set"),
        sa.Column("pcaf_member", sa.Boolean, server_default="false"),
        sa.Column("sbti_committed", sa.Boolean, server_default="false"),
        sa.Column("sbti_approved", sa.Boolean, server_default="false"),
        sa.Column("sbti_approval_date", sa.Date, nullable=True),
        sa.Column("sbti_status", sa.String(50), nullable=True,
                  comment="'Approved' | 'Committed' | 'Not Committed' | 'Removed'"),
        sa.Column("sbti_target_year", sa.Integer, nullable=True),
        sa.Column("tcfd_supporter", sa.Boolean, server_default="false"),
        sa.Column("tnfd_supporter", sa.Boolean, server_default="false"),
        sa.Column("cdp_score", sa.String(5), nullable=True,
                  comment="A, A-, B, B-, C, D, F"),
        sa.Column("cdp_year", sa.Integer, nullable=True),
        sa.Column("un_prb_signatory", sa.Boolean, server_default="false",
                  comment="UN Principles for Responsible Banking"),
        sa.Column("nzaoa_member", sa.Boolean, server_default="false",
                  comment="Net Zero Asset Owner Alliance"),
        sa.Column("pact_signatory", sa.Boolean, server_default="false",
                  comment="Paris Agreement Capital Transition (PACT)"),
        sa.Column("equator_principles", sa.Boolean, server_default="false",
                  comment="Equator Principles (project finance)"),
        sa.Column("un_pri_signatory", sa.Boolean, server_default="false",
                  comment="UN Principles for Responsible Investment"),
        sa.Column("gfanz_member", sa.Boolean, server_default="false",
                  comment="Glasgow Financial Alliance for Net Zero"),

        # ── Regulatory reports & frameworks applicable ─────────────────────
        sa.Column("csrd_applicable", sa.Boolean, nullable=True),
        sa.Column("csrd_first_reporting_year", sa.Integer, nullable=True),
        sa.Column("issb_adopted", sa.Boolean, nullable=True,
                  comment="Whether entity's jurisdiction has mandated IFRS S1/S2"),
        sa.Column("tcfd_mandatory", sa.Boolean, nullable=True),
        sa.Column("brsr_applicable", sa.Boolean, nullable=True,
                  comment="India SEBI Business Responsibility and Sustainability Reporting"),
        sa.Column("mandatory_frameworks", postgresql.ARRAY(sa.Text), nullable=True,
                  comment="List of mandatory reporting frameworks"),
        sa.Column("voluntary_frameworks", postgresql.ARRAY(sa.Text), nullable=True,
                  comment="List of voluntary frameworks adopted"),

        # ── Flexible extension (additional KPIs / metadata) ───────────────
        sa.Column("extra_metadata", postgresql.JSONB, nullable=True,
                  comment="Overflow bucket for sector-specific or jurisdiction-specific fields"),
    )

    # Indexes
    op.create_index("ix_company_profiles_legal_name",
                    "company_profiles", ["legal_name"])
    op.create_index("ix_company_profiles_lei",
                    "company_profiles", ["entity_lei"])
    op.create_index("ix_company_profiles_isin",
                    "company_profiles", ["isin_primary"])
    op.create_index("ix_company_profiles_sector",
                    "company_profiles", ["primary_sector"])
    op.create_index("ix_company_profiles_institution_type",
                    "company_profiles", ["institution_type"])
    op.create_index("ix_company_profiles_country",
                    "company_profiles", ["headquarters_country"])
    op.create_index("ix_company_profiles_entity_registry",
                    "company_profiles", ["entity_registry_id"])


def downgrade():
    op.drop_table("company_profiles")
