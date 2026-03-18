import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import numpy as np

from models import (
    Asset, Company, AssetType, Sector,
    ScenarioResult, Scenario
)
from db.base import get_db
# Use the PG models (portfolios_pg / assets_pg / analysis_runs_pg tables)
from db.models.portfolio_pg import PortfolioPG, AssetPG, AnalysisRunPG
# Scenario series still live in scenario_series table (models_sql)
from db.models_sql import ScenarioSeries as ScenarioSeriesSQL
from sqlalchemy.orm import Session
from risk_engine import RiskEngine, SECTOR_MULTIPLIERS
from services.calculation_engine import ClimateRiskCalculationEngine
from services.engine_integration import assets_to_inputs, engine_results_to_models

# Import v1 scenario routes
from api.v1.routes.scenarios import router as scenarios_router
from api.v1.routes.data_hub import router as data_hub_router
from api.v1.routes.analysis import router as analysis_router
from api.v1.routes.ngfs_v2 import router as ngfs_v2_router
from api.v1.routes.scenario_builder_v2 import router as builder_v2_router
from api.v1.routes.sub_parameter import router as sub_param_router
from api.v1.routes.cbam import router as cbam_router
from api.v1.routes.carbon import router as carbon_router
from api.v1.routes.nature_risk import router as nature_risk_router
from api.v1.routes.stranded_assets import router as stranded_assets_router
from api.v1.routes.real_estate_valuation import router as valuation_router
from api.v1.routes.sustainability import router as sustainability_router
from api.v1.routes.scenario_analysis import router as scenario_router
from api.v1.routes.scenario_analysis import sensitivity_router, whatif_router
from api.auth_pg import router as auth_router
from api.v1.routes.portfolio_pg import router as portfolio_pg_router
from api.v1.routes.portfolio_analytics import router as portfolio_analytics_router
from api.v1.routes.universal_exports import router as exports_router
from api.v1.routes.scheduled_reports import router as scheduled_reports_router
from api.v1.routes.re_clvar import router as re_clvar_router
from api.v1.routes.ecl_climate import router as ecl_climate_router
from api.v1.routes.pcaf_regulatory import router as pcaf_regulatory_router
from api.v1.routes.supply_chain import router as supply_chain_router
from api.v1.routes.sector_assessments import router as sector_assessments_router
from api.v1.routes.unified_valuation import router as unified_valuation_router
from api.v1.routes.csrd_reports import router as csrd_router
from api.v1.routes.portfolio_reporting import router as portfolio_reporting_router
from api.v1.routes.portfolio_health import router as portfolio_health_router
from api.v1.routes.project_finance import router as project_finance_router
from api.v1.routes.glidepath import router as glidepath_router
from api.v1.routes.sector_calculators import router as sector_calculators_router
from api.v1.routes.mas_regulatory import router as mas_regulatory_router
from api.v1.routes.peer_benchmark import router as peer_benchmark_router
from api.v1.routes.analyst_portfolios import router as analyst_portfolios_router
from api.v1.routes.company_profiles import router as company_profiles_router
from api.v1.routes.entity_data import router as entity_data_router
from api.v1.routes.data_intake import router as data_intake_router
from api.v1.routes.facilitated_emissions import router as facilitated_emissions_router
from api.v1.routes.engagement import router as engagement_router
from api.v1.routes.just_transition import router as just_transition_router
from api.v1.routes.green_hydrogen import router as green_hydrogen_router
from api.v1.routes.insurance import router as insurance_router
from api.v1.routes.agriculture import router as agriculture_router
from api.v1.routes.mining import router as mining_router
from api.v1.routes.parameter_governance import router as parameter_governance_router
from api.v1.routes.monte_carlo import router as monte_carlo_router
from api.v1.routes.asia_regulatory import router as asia_regulatory_router
from api.v1.routes.china_trade import router as china_trade_router
from api.v1.routes.audit_log import router as audit_log_router
from api.v1.routes.organisations import router as organisations_router
from api.v1.routes.ingestion import router as ingestion_router
from api.v1.routes.entity_resolution import router as entity_resolution_router
from api.v1.routes.emissions_data import router as emissions_data_router
from api.v1.routes.scenario_data import router as scenario_data_router
from api.v1.routes.financial_data import router as financial_data_router
from api.v1.routes.data_hub_catalog import router as data_hub_catalog_router
from api.v1.routes.glidepath_serve import router as glidepath_serve_router
from api.v1.routes.carbon_prices import router as carbon_prices_router
from api.v1.routes.benchmarks import router as benchmarks_router
from api.v1.routes.nature_data import router as nature_data_router
from api.v1.routes.energy_data import router as energy_data_router
from api.v1.routes.reference_data import router as reference_data_router
from api.v1.routes.violations import router as violations_router
from api.v1.routes.gdelt_controversy import router as gdelt_controversy_router
from api.v1.routes.geothermal import router as geothermal_router
from api.v1.routes.irena_five_pillars import router as irena_five_pillars_router
from api.v1.routes.pcaf_asset_classes import router as pcaf_asset_classes_router
from api.v1.routes.pcaf_advanced import router as pcaf_advanced_router
from api.v1.routes.sat_coal_checker import router as sat_coal_checker_router
from api.v1.routes.ca100 import router as ca100_router
from api.v1.routes.country_risk import router as country_risk_router
from api.v1.routes.dashboard_analytics import router as dashboard_analytics_router
from api.v1.routes.cdm_tools import router as cdm_tools_router
from api.v1.routes.pcaf_ecl_bridge import router as pcaf_ecl_bridge_router
from api.v1.routes.ead import router as ead_router
from api.v1.routes.gar import router as gar_router
from api.v1.routes.stress_testing import router as stress_testing_router
from api.v1.routes.lgd_vintage import router as lgd_vintage_router
from api.v1.routes.re_portfolio import router as re_portfolio_router
from api.v1.routes.epc_retrofit import router as epc_retrofit_router
from api.v1.routes.green_premium_tenant import router as green_premium_tenant_router
from api.v1.routes.fund_management import router as fund_management_router
from api.v1.routes.attribution_benchmark import router as attribution_benchmark_router
from api.v1.routes.sfdr_exclusion import router as sfdr_exclusion_router
from api.v1.routes.pe_deals import router as pe_deals_router
from api.v1.routes.pe_portfolio import router as pe_portfolio_router
from api.v1.routes.pe_reporting import router as pe_reporting_router
from api.v1.routes.renewable_ppa import router as renewable_ppa_router
from api.v1.routes.energy_transition import router as energy_transition_router
from api.v1.routes.energy_emissions import router as energy_emissions_router
from api.v1.routes.xbrl_export import router as xbrl_export_router
from api.v1.routes.disclosure_trends import router as disclosure_trends_router
from api.v1.routes.entity360 import router as entity360_router
from api.v1.routes.data_lineage import router as data_lineage_router
from api.v1.routes.reference_catalog import router as reference_catalog_router
from api.v1.routes.insurance_risk import router as insurance_risk_router
from api.v1.routes.banking_risk import router as banking_risk_router
from api.v1.routes.data_preview import router as data_preview_router
from api.v1.routes.climate_risk import router as climate_risk_router
from api.v1.routes.am import router as am_router
from api.v1.routes.agriculture_expanded import router as agriculture_expanded_router
from api.v1.routes.factor_overlays import router as factor_overlays_router
from api.v1.routes.technology import router as technology_router
from api.v1.routes.residential_re import router as residential_re_router
from api.v1.routes.rics_esg import router as rics_esg_router
from api.v1.routes.validation_summary import router as validation_summary_router
from api.v1.routes.nature_re_integration import router as nature_re_router
from api.v1.routes.spatial_hazard import router as spatial_hazard_router
from api.v1.routes.regulatory_reports import router as regulatory_reports_router
from api.v1.routes.eu_ets import router as eu_ets_router
from api.v1.routes.eudr import router as eudr_router
from api.v1.routes.csddd import router as csddd_router
from api.v1.routes.sovereign_climate_risk import router as sovereign_climate_risk_router
from api.v1.routes.sec_climate import router as sec_climate_router
from api.v1.routes.ecl_gar_pillar3 import router as ecl_gar_pillar3_router
from api.v1.routes.regulatory_calendar import router as regulatory_calendar_router  # E3
from api.v1.routes.supply_chain_workflow import router as supply_chain_workflow_router  # E5
from api.v1.routes.stewardship import router as stewardship_router  # E6
from api.v1.routes.eiopa_stress import router as eiopa_stress_router  # E7
from api.v1.routes.iorp_pension import router as iorp_pension_router  # E8
from api.v1.routes.sfdr_annex import router as sfdr_annex_router      # E9
from api.v1.routes.assurance_readiness import router as assurance_readiness_router  # E10
from api.v1.routes.uk_sdr import router as uk_sdr_router                            # E11
from api.v1.routes.spatial import router as spatial_router                          # P1-8 PostGIS
from api.v1.routes.gri_standards import router as gri_standards_router
from api.v1.routes.sasb_industry import router as sasb_industry_router
from api.v1.routes.model_validation import router as model_validation_router
from api.v1.routes.tnfd_assessment import router as tnfd_assessment_router
from api.v1.routes.cdp_scoring import router as cdp_scoring_router
from api.v1.routes.pcaf_quality import router as pcaf_quality_router
from api.v1.routes.basel_capital import router as basel_capital_router
from api.v1.routes.eu_taxonomy import router as eu_taxonomy_router
from api.v1.routes.transition_plan import router as transition_plan_router
from api.v1.routes.double_materiality import router as double_materiality_router
from api.v1.routes.sfdr_pai import router as sfdr_pai_router
# DME (Dynamic Materiality Engine) — integrated modules
from api.v1.routes.dme_velocity import router as dme_velocity_router
from api.v1.routes.dme_greenwashing import router as dme_greenwashing_router
from api.v1.routes.dme_nlp_pulse import router as dme_nlp_pulse_router
from api.v1.routes.dme_policy_tracker import router as dme_policy_tracker_router
from api.v1.routes.dme_contagion import router as dme_contagion_router
from api.v1.routes.dme_alerts import router as dme_alerts_router
from api.v1.routes.dme_dmi import router as dme_dmi_router
from api.v1.routes.dme_factor_registry import router as dme_factor_registry_router
from api.v1.routes.sentiment_analysis import router as sentiment_analysis_router
from api.v1.routes.pcaf_unified import router as pcaf_unified_router
from api.v1.routes.dcm import router as dcm_router           # DCM — complete carbon credit methodology engine
from api.v1.routes.mifid_spt import router as mifid_spt_router        # E12 MiFID II SPT
from api.v1.routes.tcfd_metrics import router as tcfd_metrics_router   # E13 TCFD Metrics & Targets
from api.v1.routes.eu_gbs import router as eu_gbs_router               # E14 EU Green Bond Standard
from api.v1.routes.priips_kid import router as priips_kid_router       # E15 PRIIPs KID ESG
from api.v1.routes.esma_fund_names import router as esma_fund_names_router  # E16 ESMA Fund Names ESG Guidelines
from api.v1.routes.sl_finance import router as sl_finance_router             # E17 Sustainability-Linked Finance (SLB/SLL)
from api.v1.routes.ifrs_s1 import router as ifrs_s1_router                  # E18 IFRS S1 General Sustainability Disclosures
from api.v1.routes.eu_taxonomy_gar import router as eu_taxonomy_gar_router  # E19 EU Taxonomy GAR/BTAR Reporter
from api.v1.routes.eba_pillar3 import router as eba_pillar3_router              # E20 EBA Pillar 3 ESG Disclosures
from api.v1.routes.scope3_categories import router as scope3_categories_router  # E21 Scope 3 Categories Engine
from api.v1.routes.sfdr_product_reporting import router as sfdr_product_reporting_router  # E22 SFDR Product Periodic Reporting
from api.v1.routes.biodiversity_finance import router as biodiversity_finance_router      # E23 Biodiversity Finance Metrics
from api.v1.routes.issb_s2 import router as issb_s2_router                              # E24 ISSB S2 Climate-Related Disclosures
from api.v1.routes.gri_standards import router as gri_standards_router                  # E25 GRI Universal Standards 2021
from api.v1.routes.tpt_transition_plan import router as tpt_transition_plan_router      # E26 TPT Transition Plan Framework
from api.v1.routes.pcaf_sovereign import router as pcaf_sovereign_router                # E27 PCAF Sovereign Bonds Part D
from api.v1.routes.esrs_e2_e5 import router as esrs_e2_e5_router                        # E28 CSRD ESRS E2-E5 Pollution/Water/Biodiversity/Circular
from api.v1.routes.greenwashing import router as greenwashing_router                    # E29 Greenwashing Risk & Substantiation
from api.v1.routes.carbon_credit_quality import router as carbon_credit_quality_router  # E30 Carbon Credit Quality & Integrity (ICVCM CCP)
from api.v1.routes.climate_stress_test import router as climate_stress_test_router      # E31 Climate Stress Testing ECB/EBA 2022/2023
from api.v1.routes.tnfd_leap import router as tnfd_leap_router                          # E32 TNFD LEAP Process (Locate/Evaluate/Assess/Prepare)
from api.v1.routes.net_zero_targets import router as net_zero_targets_router            # E33 Net Zero Target Setting (SBTi/NZBA/NZAMI/NZAOA)
from api.v1.routes.esg_data_quality import router as esg_data_quality_router            # E34 ESG Data Quality Scoring & Provider Divergence
from api.v1.routes.regulatory_penalties import router as regulatory_penalties_router    # E35 Regulatory Penalty & Enforcement Calculator
from api.v1.routes.basel3_liquidity import router as basel3_liquidity_router            # E36 Basel III Liquidity — LCR/NSFR/IRRBB/ALM gap
from api.v1.routes.social_taxonomy import router as social_taxonomy_router              # E37 Social Taxonomy & Impact — EU Social Tax / IMP / IRIS+
from api.v1.routes.forced_labour import router as forced_labour_router                  # E38 Forced Labour — EU FLR 2024/3015 / ILO / UK MSA / LkSG
from api.v1.routes.transition_finance import router as transition_finance_router        # E39 Transition Finance — GFANZ / TPT / ICMA CTF / GAR
from api.v1.routes.csrd_dma import router as csrd_dma_router                            # E40 CSRD Double Materiality — ESRS 1 DMA impact + financial materiality
from api.v1.routes.physical_hazard import router as physical_hazard_router              # E41 Physical Climate Hazard — IPCC AR6 flood/wildfire/heat/sea-level
from api.v1.routes.avoided_emissions import router as avoided_emissions_router          # E42 Scope 4 Avoided Emissions — GHG Protocol 2022 / Article 6 / BVCM
from api.v1.routes.green_hydrogen_engine import router as green_hydrogen_e43_router    # E43 Green Hydrogen — EU Delegated Act 2023/1184 / LCOH / RFNBO / IRA 45V
from api.v1.routes.biodiversity_finance_v2 import router as biodiversity_finance_v2_router  # E44 Biodiversity Finance v2 — TNFD LEAP / PBAF / ENCORE / GBF COP15 30×30 / BFFI / BNG
from api.v1.routes.prudential_climate_risk import router as prudential_climate_risk_router  # E45 Prudential Climate Risk — BOE/PRA BES 2025 / ECB DFAST / NGFS v4 / ICAAP Pillar 2
from api.v1.routes.carbon_markets_intel import router as carbon_markets_intel_router        # E46 Carbon Markets Intel — Art 6.2/6.4 / VCMI Claims / ICVCM CCP / CORSIA Phase 2
from api.v1.routes.just_transition_engine import router as just_transition_router           # E47 Just Transition & Social Risk — ILO JT / ESRS S1-S4 / Living Wage / Worker Displacement
from api.v1.routes.shipping_maritime import router as shipping_maritime_router              # E48 Shipping & Maritime — IMO GHG 2023 / CII A-E / EEXI / Poseidon Principles / FuelEU / EU ETS
from api.v1.routes.aviation_climate import router as aviation_climate_router                # E49 Aviation Climate Risk — CORSIA Phase 2 / SAF ReFuelEU / IRA 45Z / EU ETS Aviation / IATA NZC
from api.v1.routes.commercial_re import router as commercial_re_router                      # E50 Commercial RE Net Zero — CRREM 2.0 / EPC / EPBD 2024 / GRESB RE / REFI / NABERS / Retrofit
from api.v1.routes.infrastructure_finance import router as infrastructure_finance_router    # E51 Infrastructure Climate Finance — EP4 / IFC PS 1-8 / OECD / Paris Alignment / Blended Finance
from api.v1.routes.nature_based_solutions import router as nbs_router                      # E52 Nature-Based Solutions — IUCN GS v2 / REDD+ / Blue Carbon / Soil Carbon / ARR / AFOLU
from api.v1.routes.water_risk import router as water_risk_router                            # E53 Water Risk & Security — WRI Aqueduct 4.0 / CDP Water / CSRD ESRS E3 / TNFD Water
from api.v1.routes.food_system import router as food_system_router                          # E54 Food System & Land Use — SBTi FLAG / FAO Crop Yield / TNFD Food LEAP / EUDR / ICTI
from api.v1.routes.circular_economy import router as circular_economy_router                # E55 Circular Economy Finance — CSRD ESRS E5 / EMF MCI / WBCSD CTI / EPR / CRM Act 2023
from api.v1.routes.climate_litigation import router as climate_litigation_router            # E56 Climate Litigation & Legal Risk — TCFD Liability / D&O Exposure / Greenwashing Enforcement / SEC
from api.v1.routes.esg_ratings import router as esg_ratings_router                        # E57 ESG Ratings Reform — EU ESRA 2024/3005 / MSCI-Sustainalytics Divergence / Bias Analysis
from api.v1.routes.methane_fugitive import router as methane_fugitive_router               # E58 Methane & Fugitive Emissions — EU Methane Reg 2024/1787 / OGMP 2.0 / Super-emitter / GWP-20
from api.v1.routes.health_climate import router as health_climate_router                   # E59 Health-Climate Nexus — Heat Stress / Air Quality WHO / Vector Disease / WHO CCS
from api.v1.routes.maritime import router as maritime_router                               # E60 Maritime & Shipping Decarbonisation — IMO GHG 2023 / CII / EEXI / EU ETS / FuelEU Maritime
from api.v1.routes.hydrogen import router as hydrogen_router                               # E61 Hydrogen Economy Finance — RFNBO / EU H2 Bank / LCOH / Green-Blue-Grey / Demand Sectors
from api.v1.routes.just_transition import router as just_transition_finance_router         # E62 Just Transition Finance — ILO Guidelines 2015 / World Bank JT Framework / ICMA SBP / JETP
from api.v1.routes.cdr import router as cdr_router                                        # E63 Carbon Removal & CDR Finance — IPCC AR6 CDR / BeZero / Oxford Principles / VCMI / Art 6.4
from api.v1.routes.transition_finance import router as transition_finance_router           # E64 Transition Finance Alignment — GFANZ / SBTi NZ Standard / TPT / CA100+ / PACTA
from api.v1.routes.biodiversity_credits import router as biodiversity_credits_router       # E65 Biodiversity Credits & Nature Markets — UK BNG / EU NRL / SBTN / TNFD Advanced
from api.v1.routes.climate_stress_test import router as climate_stress_test_router         # E66 Climate Stress Testing — BCBS 517 / BoE CBES / ECB CST / APRA CLT / NGFS Phase 4
from api.v1.routes.scope3_analytics import router as scope3_analytics_router               # E67 Scope 3 Deep-Dive — GHG Protocol Cat 1-15 / FLAG / Avoided Emissions / DQS / PCAF
from api.v1.routes.blue_economy import router as blue_economy_router                       # E68 Blue Economy & Ocean Finance — ICMA Blue Bond / SOF / Blue Carbon / BBNJ 2023
from api.v1.routes.sovereign_debt_climate import router as sovereign_debt_climate_router   # E69 Climate-Linked Sovereign Debt — CRDC / Debt-for-Nature / IMF RST / Paris Club / SIDS
from api.v1.routes.loss_damage import router as loss_damage_router                         # E70 Loss & Damage Finance — COP28 FRLD / WIM / Global Shield v2 / V20 / Parametric
from api.v1.routes.carbon_price_ets import router as carbon_price_ets_router               # E71 Carbon Price & ETS Analytics — EU ETS Phase 4 / UK ETS / California / China / RGGI
from api.v1.routes.blended_finance import router as blended_finance_router              # E72 Blended Finance & DFI — IFC/MIGA/EBRD/ADB/Convergence/concessional/first-loss
from api.v1.routes.mrv import router as mrv_router                                      # E73 Climate Data & MRV — ISO 14064-3/satellite/CDP/AI-quality/digital MRV tiers
from api.v1.routes.real_asset_decarb import router as real_asset_decarb_router          # E74 Real Asset Decarbonisation — CRREM/lock-in risk/capex/brown-to-green/retrofit NPV
from api.v1.routes.trade_finance_esg import router as trade_finance_esg_router          # E75 Sustainable Trade Finance — EP4/ECA/ICC STF/supply-chain ESG/trade-flow GHG
from api.v1.routes.crypto_climate import router as crypto_climate_router                # E76 Digital Assets & Crypto Climate — Cambridge CBECI/MiCA 2023/PoW-PoS/PCAF Crypto
from api.v1.routes.ai_governance import router as ai_governance_router                  # E77 AI Governance ESG — EU AI Act 2024/NIST RMF/OECD AI/AI Energy/Algorithmic Bias
from api.v1.routes.carbon_accounting_ai import router as carbon_accounting_ai_router    # E78 Carbon Accounting AI — GHG Protocol AI/EF Matching/Scope3 Auto-classify/XBRL
from api.v1.routes.climate_insurance import router as climate_insurance_router          # E79 Climate Insurance — IAIS AP 2021/Parametric/NatCat/Climate VaR/ORSA
from api.v1.routes.ai_risk import router as ai_risk_router                          # E76 AI & ML Risk Finance — EU AI Act 2024/1689 / NIST RMF / Bias Detection / AI Liability Directive
from api.v1.routes.nature_capital import router as nature_capital_router            # E77 Nature Capital Accounting — SEEA EA 2021 / TNFD / ENCORE / TEEB / Natural Capital Balance Sheet
from api.v1.routes.climate_finance import router as climate_finance_router          # E78 Climate Finance Flows — OECD CRS / UNFCCC Art 2.1(c) / CPI / NCQG $300bn / MDB Tracking
from api.v1.routes.esg_ma import router as esg_ma_router                            # E79 ESG M&A Due Diligence — UNGP 31 Principles / CSDDD Art 3 / ESG Valuation / Post-Merger Integration
from api.v1.routes.corporate_nature_strategy import router as corporate_nature_strategy_router  # E80 Corporate Nature Strategy — SBTN v1.0 / TNFD v1.0 / EU NRL 2024/1991 / GBF Target 3 / ENCORE
from api.v1.routes.green_securitisation import router as green_securitisation_router            # E81 Green Securitisation — EU GBS Art 19 / ABS-RMBS Climate VaR / ECBC Covered Bond / ESRS SPV
from api.v1.routes.digital_product_passport import router as digital_product_passport_router    # E82 Digital Product Passport — EU ESPR 2024/1781 / Battery Reg 2023/1542 / EPR / LCA / DPP
from api.v1.routes.adaptation_finance import router as adaptation_finance_router                # E83 Adaptation Finance — GFMA Taxonomy / GARI / MDB Facilities / NAP/NDC / Resilience Delta
from api.v1.routes.internal_carbon_price import router as internal_carbon_price_router          # E84 Internal Carbon Pricing — SBTi ICP Guidance / EU ETS Phase4+ETS2 / MAC Curve / NZE Economics
from api.v1.routes.social_bond import router as social_bond_router                              # E85 Social Bond — ICMA SBP 2023 / UN SDG / Social KPIs / Target Population / Impact Finance
from api.v1.routes.climate_financial_statements import router as climate_financial_statements_router  # E86 Climate Financial Statements — IFRS S2 Effects / IAS36 Impairment / IAS37 Carbon Provision / TCFD
from api.v1.routes.em_climate_risk import router as em_climate_risk_router                      # E87 EM Climate Risk — IFC PS6 / MSCI EM / GEMS Loss / NDC Gaps / Concessional Finance
from api.v1.routes.biodiversity_credits import router as biodiversity_credits_router            # E88 Biodiversity Credits — BNG DEFRA Metric 4.0 / Verra VM0033 / TNFD v1 / GBF T15 / Plan Vivo
from api.v1.routes.just_transition import router as just_transition_router                      # E89 Just Transition Finance — ILO 2015 / EU JTF 2021/1056 / PPCA / CIF / Coal Communities
from api.v1.routes.carbon_removal import router as carbon_removal_router                        # E90 Carbon Removal — IPCC AR6 CDR / Oxford Principles / Article 6.4 / BECCS/DACS/EW / Frontier
from api.v1.routes.climate_litigation import router as climate_litigation_router                # E91 Climate Litigation — UNEP v3 / Sabin Center / Duties X / D&O / Attribution Science
from api.v1.routes.water_stewardship import router as water_stewardship_router                  # E92 Water Risk & Stewardship — WRI AQUEDUCT 4.0 / CDP Water A-List / TNFD E3 / AWS Standard v2 / CEO Water Mandate
from api.v1.routes.critical_minerals import router as critical_minerals_router                  # E93 Critical Minerals — IEA CRM 2024 / EU CRM Act 2024/1252 / IRMA Standard / OECD DDG / Conflict Minerals DRC
from api.v1.routes.nbs_finance import router as nbs_finance_router                              # E94 NbS Finance — IUCN NbS Global Standard v2 / ICROA / VCMI Core Claims / REDD+ VCS / GBF KM Target 2
from api.v1.routes.sfdr_art9 import router as sfdr_art9_router                                  # E95 SFDR Art 9 — RTS 2022/1288 / ESMA SFDR Q&A 2023 / 14 PAI indicators / DNSH all-6 / Art 9 Eligibility
from api.v1.routes.vcm_integrity import router as vcm_integrity_router                          # E96 VCM Integrity — ICVCM CCP 2023 / VCMI Claims / Oxford Offsetting Principles / Verra GS ACR CAR registries
from api.v1.routes.social_taxonomy import router as social_taxonomy_router                      # E97 Social Taxonomy — EU SocTax 2022/2023 / ILO 8 core conventions / UNGP HRDD / CSDDD social / Decent Work SDG 8
from api.v1.routes.green_hydrogen import router as green_hydrogen_router                        # E98 Green Hydrogen — EU Del. Act 2023/1184 RFNBO / GHG <3.38 kg / Additionality / H2 CfD / IEA / REPowerEU
from api.v1.routes.transition_finance import router as transition_finance_router                # E99 Transition Finance Credibility — GFANZ/TPT / SBTi / Race to Zero / TNFD LEAP / Portfolio temperature

# Sprint 35 — E100–E103
from api.v1.routes.stress_test_orchestrator import router as stress_test_orchestrator_router    # E100 Multi-Regulatory Stress Test — NGFS Phase IV / ECB/EBA/BoE/APRA/MAS/RBI / CET1 depletion / PD migration
from api.v1.routes.sscf import router as sscf_router                                            # E101 Sustainable Supply Chain Finance — LMA SSCF / ICC SCF / GSCFF / 40 KPIs / OECD DDG / CSDDD cascade
from api.v1.routes.double_materiality import router as double_materiality_router                # E102 CSRD Double Materiality — ESRS 1 DMA / IRO identification / materiality matrix / ESRS omissions
from api.v1.routes.temperature_alignment import router as temperature_alignment_router          # E103 Temperature Alignment — PCAF + SBTi FI / PACTA / WACI / ITR / sector pathways


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize PostgreSQL tables
    try:
        from db.base import init_db as init_postgres_db
        init_postgres_db()
    except Exception as e:
        print(f"[WARN] PostgreSQL init failed: {e}")

    # Startup: register concrete ingesters (GLEIF, Sanctions, etc.)
    try:
        from ingestion import register_all_ingesters
        register_all_ingesters()
        print("[OK] Ingesters registered")
    except Exception as e:
        print(f"[WARN] Ingester registration failed: {e}")

    # Startup: start ingestion scheduler (APScheduler)
    _scheduler = None
    try:
        from ingestion.scheduler import get_scheduler
        _scheduler = get_scheduler()
        _scheduler.start()
        print("[OK] Ingestion scheduler started")
    except Exception as e:
        print(f"[WARN] Ingestion scheduler not started: {e}")

    yield

    # Shutdown: stop ingestion scheduler
    if _scheduler:
        try:
            _scheduler.stop()
            print("[OK] Ingestion scheduler stopped")
        except Exception:
            pass


app = FastAPI(
    title="Climate Credit Risk Intelligence Platform",
    description="Portfolio Scenario Analysis with NGFS Climate Data",
    version="1.0.0",
    lifespan=lifespan
)

# Include Scenario Analysis routes (must be BEFORE scenarios_router to avoid route conflicts)
# These routes have specific paths like /dashboard, /properties that would otherwise
# be matched by the {scenario_id} catch-all pattern in scenarios_router
app.include_router(scenario_router)
app.include_router(sensitivity_router)
app.include_router(whatif_router)
# Include scenario builder routes
app.include_router(scenarios_router)
# Include data hub routes
app.include_router(data_hub_router)
# Include analysis routes
app.include_router(analysis_router)
# Include auth routes (PostgreSQL)
app.include_router(auth_router)
# Include PG portfolio routes
app.include_router(portfolio_pg_router)
# Include NGFS v2 routes
app.include_router(ngfs_v2_router)
# Include scenario builder v2 routes
app.include_router(builder_v2_router)
# Include sub-parameter analysis routes
app.include_router(sub_param_router)
# Include CBAM routes
app.include_router(cbam_router)
# Include Carbon Credits routes
app.include_router(carbon_router)
# Include CDM Methodological Tools & Activity Guide routes
app.include_router(cdm_tools_router)
# Include Nature Risk routes
app.include_router(nature_risk_router)
# Include Stranded Assets routes
app.include_router(stranded_assets_router)
# Include Real Estate Valuation routes
app.include_router(valuation_router)
# Include Sustainability Frameworks routes
app.include_router(sustainability_router)
# Include Portfolio Analytics routes
app.include_router(portfolio_analytics_router)
# Include Universal Export routes
app.include_router(exports_router)
# Include Scheduled Reports routes
app.include_router(scheduled_reports_router)
# Include Real Estate CLVaR and CRREM routes
app.include_router(re_clvar_router)
# Include IFRS 9 ECL Climate routes
app.include_router(ecl_climate_router)
# Include PCAF / SFDR / EU Taxonomy routes
app.include_router(pcaf_regulatory_router)
# Include Supply Chain Scope 3 routes
app.include_router(supply_chain_router)
# Include Sector ESG Assessment routes
app.include_router(sector_assessments_router)
# Include Unified Valuation Engine routes
app.include_router(unified_valuation_router)
# Include CSRD PDF extraction + ESRS KPI query routes
app.include_router(csrd_router)
# Include Portfolio Reporting routes (PCAF, SFDR PAI, ECL stress, EU Taxonomy, Paris alignment)
app.include_router(portfolio_reporting_router)
# Include Portfolio Health (Sustainability Pulse scores + alert engine)
app.include_router(portfolio_health_router)
# Include Project Finance (DSCR / LLCR / IRR / PPA engine)
app.include_router(project_finance_router)
# Include Glidepath Tracker (NZBA / CRREM sector glidepath)
app.include_router(glidepath_router)
# Include Sector Calculators (Shipping CII / Steel BF-BOF)
app.include_router(sector_calculators_router)
# Include MAS Regulatory (ERM / Notice 637 / SGT / SLGS)
app.include_router(mas_regulatory_router)
# Include Peer Benchmark Gap Assessment (TCFD / ISSB / ESRS / PCAF peer matrix)
app.include_router(peer_benchmark_router)
app.include_router(analyst_portfolios_router)  # 10 analyst demo portfolios + gap assessment
app.include_router(company_profiles_router)    # Company profiles — identity, prudential, Pillar 3
app.include_router(entity_data_router)         # CSRD Entity Data Bridge — real data to module inputs
app.include_router(data_intake_router)         # Category C — Client Proprietary Data Intake
app.include_router(facilitated_emissions_router)  # Category D — PCAF Capital Markets Facilitated Emissions
app.include_router(engagement_router)             # Category D — Client Engagement Tracker (PRI AO2.0 / CA100+)
app.include_router(just_transition_router)        # Category D — Just Transition + ETM (ILO / ADB ETM Framework)
app.include_router(green_hydrogen_router)         # Category D — Green Hydrogen LCOH + Carbon Intensity (IRENA / IEA / RFNBO)
app.include_router(insurance_router)              # P1 — Insurance Climate Risk (CAT / Solvency II / reserve adequacy)
app.include_router(agriculture_router)            # P1 — Agriculture Risk (EUDR / crop yield / soil carbon / water stress)
app.include_router(mining_router)                 # P1 — Mining/Extractives (GISTM tailings / closure cost / critical minerals)
app.include_router(parameter_governance_router)   # P2 — Parameter Governance (versioned calc params + approval workflow)
app.include_router(monte_carlo_router)            # P2 — Monte Carlo Simulation (P5/P25/P50/P75/P95 portfolio risk distribution)
app.include_router(asia_regulatory_router)        # Asia Regulatory — BRSR / HKMA / BoJ / ASEAN Taxonomy v3 / PBoC / CBI
app.include_router(china_trade_router)            # China Trade Platform — Exporter / CBAM / Supplier / ESG / ETS / Corridors / Marketplace
app.include_router(audit_log_router)              # Audit Log — admin read-only query endpoints
app.include_router(organisations_router)          # Organisations — multi-tenant CRUD + member management
app.include_router(ingestion_router)              # Ingestion — data source sync, job history, scheduler
app.include_router(entity_resolution_router)      # Entity Resolution -- LEI lookup, sanctions screening
app.include_router(emissions_data_router)          # Emissions Data -- Climate TRACE + OWID CO2/energy queries
app.include_router(scenario_data_router)           # Scenario Data -- NGFS scenarios + SBTi targets
app.include_router(financial_data_router)          # Financial Data -- SEC EDGAR + yfinance/FMP
app.include_router(data_hub_catalog_router)        # Data Hub Catalog -- cross-source search, entity 360, coverage
app.include_router(glidepath_serve_router)         # Glidepaths -- NZBA + CRREM pathway serve
app.include_router(carbon_prices_router)           # Carbon Prices -- NGFS carbon price projections
app.include_router(benchmarks_router)              # Benchmarks -- sector WACI + financial benchmarks
app.include_router(nature_data_router)             # Nature Data -- WDPA protected areas + GFW tree cover loss
app.include_router(energy_data_router)             # Energy Data -- GEM Global Coal Plant Tracker
app.include_router(reference_data_router)          # Reference Data -- IRENA LCOE, CRREM, Grid EFs
app.include_router(violations_router)              # Violations -- Corporate penalty tracker
app.include_router(gdelt_controversy_router)       # GDELT -- Events, GKG, Controversy Scores
app.include_router(geothermal_router)              # Geothermal -- LCOE, viability, seismicity, NPV/IRR
app.include_router(irena_five_pillars_router)      # IRENA Five Pillars -- Transition readiness assessment
app.include_router(pcaf_asset_classes_router)      # PCAF v2.0 -- All 7 asset class financed emissions (investor-grade)
app.include_router(pcaf_advanced_router)           # PCAF Advanced -- Security/Fund/Portfolio/Index multi-level analytics
app.include_router(sat_coal_checker_router)        # SAT Coal -- IEA NZE / NZBA coal phase-out criteria checker
app.include_router(ca100_router)                   # CA100+ Net Zero Company Benchmark
app.include_router(country_risk_router)            # Country Risk & Governance Indices
app.include_router(dashboard_analytics_router)     # Dashboard Analytics -- real-data aggregation
app.include_router(pcaf_ecl_bridge_router)         # PCAF -> ECL Bridge -- financed emissions to credit risk
app.include_router(ead_router)                     # EAD Calculator -- Basel III/IV CCF + maturity adjustment
app.include_router(gar_router)                     # GAR & Climate Scoring -- EU Taxonomy Art.449a + counterparty climate score
app.include_router(stress_testing_router)           # Stress Testing & PD Backtesting -- multi-scenario ECL + EBA GL/2017/16
app.include_router(lgd_vintage_router)             # LGD Downturn & Vintage Analysis -- CRR2/EBA GL/2019/03 + IFRS 9 vintage
app.include_router(re_portfolio_router)            # RE Portfolio NAV Roll-Up -- INREV NAV + CRREM v2 + EPC/MEPS
app.include_router(epc_retrofit_router)            # EPC Transition Risk + Retrofit CapEx Planner -- MEPS + NPV/payback
app.include_router(green_premium_tenant_router)    # Green Premium / Brown Discount + Tenant ESG Tracker
app.include_router(fund_management_router)         # Fund Structure + Holdings-Level Analytics (SFDR/WACI/Active Share)
app.include_router(attribution_benchmark_router)   # ESG Attribution (Brinson-Fachler) + Benchmark Analytics (CTB/PAB)
app.include_router(sfdr_exclusion_router)          # SFDR Periodic Report + Exclusion Screening + Compliance
app.include_router(pe_deals_router)                # PE Deal Pipeline + ESG Screening + Sector Heatmap
app.include_router(pe_portfolio_router)            # PE Portfolio Monitoring (ILPA KPIs) + Value Creation Plans
app.include_router(pe_reporting_router)            # PE GP/LP Reporting + Impact Framework + IRR Sensitivity
app.include_router(renewable_ppa_router)           # Renewable Project Finance (P50/P90) + PPA Risk Scoring
app.include_router(energy_transition_router)       # Generation Transition Planner + Grid EF Trajectory
app.include_router(energy_emissions_router)        # Methane OGMP 2.0 + Scope 3 Cat 11 + CSRD Auto-Population
app.include_router(xbrl_export_router)             # XBRL/iXBRL Export (CSRD/ISSB) + XBRL Ingestion (multi-schema)
app.include_router(disclosure_trends_router)       # Disclosure Completeness (9 frameworks) + Multi-Year Trend Analytics
app.include_router(entity360_router)               # Entity 360 Profile + Counterparty Master (dedup, quality scoring)
app.include_router(data_lineage_router)            # Data Lineage — cross-module dependency graph, gap analysis, quality propagation
app.include_router(reference_catalog_router)       # Reference Data Catalog — centralized registry, freshness, gap identification
app.include_router(insurance_risk_router)          # Insurance Risk Engine — Life/P&C/Reinsurance/Health with climate overlays
app.include_router(banking_risk_router)            # Banking Risk Engine — Credit/Liquidity/Market/OpRisk/AML/Capital Adequacy
app.include_router(data_preview_router)            # Data Preview — table browser, FK relationships, datapoint mappings
app.include_router(climate_risk_router)            # Climate Risk Engine — Physical/Transition/Integrated risk + Methodology Manager + Assessment Runner
app.include_router(am_router)                      # AM Engine — ESG Attribution, Paris Alignment, Green Bond, Climate Spreads, LP Analytics, Optimisation
app.include_router(agriculture_expanded_router)    # Agriculture Engine (Expanded) — Methane Intensity, Disease Outbreak, Biodiversity Net Gain
app.include_router(factor_overlays_router)         # Factor Overlay Engine — ESG/Geopolitical/Tech cross-cutting overlays (12 FI×LOB)
app.include_router(technology_router)              # Technology Sector — Data Centre/Cloud/AI/Semiconductor/E-Waste + EU EED Art.12 + SCI
app.include_router(residential_re_router)          # Residential RE — Hedonic valuation, mortgage climate risk, decarb pathway
app.include_router(rics_esg_router)                # RICS Red Book ESG — PS1/PS2/VPS4/VPGA12/VPG3/IVS compliance + narrative
app.include_router(validation_summary_router)      # Validation Summary — per-calculation audit envelope (BCBS 239)
app.include_router(nature_re_router)              # Nature-RE Integration — TNFD LEAP/water/biodiversity → RE valuation
app.include_router(spatial_hazard_router)         # Spatial Hazard — location-based physical risk auto-population
app.include_router(regulatory_reports_router)     # Regulatory Report Compiler — TCFD/SFDR/GRI305/SEC/ISSB/APRA/BRSR
app.include_router(eu_ets_router)                 # EU ETS Phase 4 — free allocation, compliance, carbon price, cap trajectory, ETS2
app.include_router(eudr_router)                   # EUDR 2023/1115 — due diligence, commodity screening, traceability, country risk, compliance gaps
app.include_router(csddd_router)                  # CSDDD 2024/1760 — scope, adverse impacts, DD compliance, value chain, climate plan
app.include_router(sovereign_climate_risk_router)  # Sovereign Climate Risk — climate-adjusted ratings, spread delta, portfolio
app.include_router(sec_climate_router)              # SEC Climate Disclosure — Reg S-K 1500-1505, S-X 14-02, filer assessment, attestation
app.include_router(ecl_gar_pillar3_router)          # ECL→GAR→Pillar3 orchestration — IFRS9 + EU Taxonomy GAR + CRR Art.449a (E1)
app.include_router(regulatory_calendar_router)      # Regulatory Obligation Calendar — 13 frameworks, 22+ deadlines, urgency alerts (E3)
app.include_router(supply_chain_workflow_router)    # Supply Chain Workflow — EUDR+CSDDD+ESRS E4 unified assessment (E5)
app.include_router(stewardship_router)              # Stewardship Engine — GFANZ/NZAMI/CA100+/NZIF engagement, proxy voting, escalation (E6)
app.include_router(eiopa_stress_router)             # EIOPA ORSA Climate Stress Test — Solvency II Art 45a, 4 NGFS scenarios, SCR/MCR impact, ORSA checklist (E7)
app.include_router(iorp_pension_router)             # IORP II Pension Climate Risk — EIOPA stress, ALM, funding ratio, ORA Art 28, SFDR FMP classification (E8)
app.include_router(sfdr_annex_router)               # SFDR Annex Disclosures — RTS 2022/1288 Annexes I–V pre-contractual + periodic templates, PAI statement, validator (E9)
app.include_router(assurance_readiness_router)      # Assurance Readiness Dashboard — 26 criteria, 8 domains, ISAE/ISSA/CSRD Art 26a, blocking gap detection (E10)
app.include_router(uk_sdr_router)                   # UK SDR Engine — FCA PS 23/16, 4 labels, AGR, naming rules, ICIS proxy, SFDR/ISSB cross-mapping (E11)
app.include_router(spatial_router)                  # Spatial Query Engine — PostGIS P1-8: protected areas, flood zones, wildfire, SLR, EUDR plot overlap
app.include_router(gri_standards_router)            # GRI Standards 2021 — content index, emissions (305), material topics, SDG/ESRS linkage
app.include_router(sasb_industry_router)            # SASB Industry Standards — IFRS S1 para 55, SICS sectors, materiality, peer comparison
app.include_router(model_validation_router)         # Model Validation Framework — BCBS 239, EBA GL/2023/04, backtesting, champion-challenger
app.include_router(tnfd_assessment_router)           # TNFD Nature-Related Disclosures — LEAP, ENCORE, 14 disclosures, double materiality
app.include_router(cdp_scoring_router)               # CDP Climate & Water Scoring — 15 climate modules, 9 water modules, A-D grades
app.include_router(pcaf_quality_router)              # PCAF Data Quality Scoring — DQS 1-5, 6 asset classes, SFDR PAI, confidence bands
app.include_router(basel_capital_router)              # Basel III/IV Regulatory Capital — CRR Art 92/153, IRB, LCR, NSFR, climate add-ons
app.include_router(eu_taxonomy_router)               # EU Taxonomy Alignment — Reg 2020/852, 6 objectives, 30+ NACE activities, GAR/BTAR
app.include_router(transition_plan_router)            # Climate Transition Plan — TPT/GFANZ/IIGCC/CSDDD Art 22/ESRS E1/CDP C4, 50+ datapoint mapping
app.include_router(double_materiality_router)         # Double Materiality Assessment — CSRD/ESRS impact + financial materiality, DMA matrix
app.include_router(sfdr_pai_router)                   # SFDR PAI — 18 mandatory + 46 optional indicators, Art 4 disclosure, DNSH, Art 6/8/9 classification
# DME (Dynamic Materiality Engine) — velocity, greenwashing, NLP pulse, policy tracker, contagion, alerts, DMI
app.include_router(dme_velocity_router)                # DME Velocity — EWMA 6-stage pipeline, regime classification (NORMAL/ELEVATED/CRITICAL/EXTREME)
app.include_router(dme_greenwashing_router)            # DME Greenwashing — CUSUM change detection, credibility-weighted divergence, 3-condition trigger
app.include_router(dme_nlp_pulse_router)               # DME NLP Pulse — sentiment signal processing, source credibility, signal decay
app.include_router(dme_policy_tracker_router)          # DME Policy Tracker — carbon price / regulatory / enforcement / disclosure velocity
app.include_router(dme_contagion_router)               # DME Contagion — Hawkes process 3-layer systemic risk, EL/VaR/ES amplification
app.include_router(dme_alerts_router)                  # DME Alerts — 4-tier framework (WATCH/ELEVATED/CRITICAL/EXTREME), priority scoring
app.include_router(dme_dmi_router)                     # DME DMI — Dynamic Materiality Index, PCAF confidence, concentration penalty
app.include_router(dme_factor_registry_router)         # DME Factor Registry — unified 627+31 factor taxonomy
app.include_router(sentiment_analysis_router)          # Sentiment Analysis — multi-stakeholder signal processing
app.include_router(pcaf_unified_router)                # PCAF Unified Module — Parts A/B/C orchestrator, regulatory disclosures, DQS, bridges
app.include_router(dcm_router)                         # DCM — 60+ carbon credit methodologies (CDM/VCS/GS/CDR/Art6.4/CORSIA)
app.include_router(mifid_spt_router)                   # E12 MiFID II SPT — Art 2(7) sustainability preference categories A/B/C, suitability assessment
app.include_router(tcfd_metrics_router)                # E13 TCFD Metrics & Targets — 11 recommendations, 4 pillars, sector supplements, maturity scoring
app.include_router(eu_gbs_router)                      # E14 EU Green Bond Standard — Regulation 2023/2631, GBFS, allocation/impact reports, ER requirements
app.include_router(priips_kid_router)                  # E15 PRIIPs KID ESG — SRI 1-7, 4 performance scenarios, ESG inserts per SFDR classification
app.include_router(esma_fund_names_router)             # E16 ESMA Fund Names — ESMA/2024/249, 80% threshold, PAB exclusions, term detection
app.include_router(sl_finance_router)                  # E17 SL Finance — ICMA SLB + LMA SLL, KPI SMART, SPT calibration, coupon step-up
app.include_router(ifrs_s1_router)                     # E18 IFRS S1 — General sustainability disclosures, 4 pillars, SASB industry mapping
app.include_router(eu_taxonomy_gar_router)             # E19 EU Taxonomy GAR — Art 8 Del. Act, GAR/BTAR/BSAR, DNSH 6 objectives, min safeguards
app.include_router(eba_pillar3_router)                 # E20 EBA Pillar 3 ESG — GL/2022/03, CRR Art 449a, 10 templates, physical risk heatmap
app.include_router(scope3_categories_router)           # E21 Scope 3 Categories — GHG Protocol 15 categories, FLAG/non-FLAG, SBTi coverage
app.include_router(sfdr_product_reporting_router)      # E22 SFDR Product Reporting — RTS 2022/1288 Annex III/V periodic reports, PAI product-level
app.include_router(biodiversity_finance_router)        # E23 Biodiversity Finance — TNFD v1.0, SBTN, CBD GBF Target 15, MSA footprint
app.include_router(issb_s2_router)                     # E24 ISSB S2 — IFRS S2 climate disclosures, 4 pillars, scenario analysis, SASB industry metrics
app.include_router(gri_standards_router)               # E25 GRI Standards — GRI 1/2/3 Universal 2021, GRI 300 environment series, content index
app.include_router(tpt_transition_plan_router)         # E26 TPT — Transition Plan Taskforce 2023, 6 elements, quality tier, interim targets
app.include_router(pcaf_sovereign_router)              # E27 PCAF Sovereign — Part D sovereign bonds, GDP attribution, NDC alignment
app.include_router(esrs_e2_e5_router)                  # E28 ESRS E2-E5 — Pollution, Water & Marine, Biodiversity, Circular Economy
app.include_router(greenwashing_router)                # E29 Greenwashing — EU Reg 2023/2441, FCA Consumer Duty, claim substantiation
app.include_router(carbon_credit_quality_router)       # E30 Carbon Credit Quality — ICVCM CCP, VCS, Gold Standard, CORSIA, Article 6
app.include_router(climate_stress_test_router)         # E31 Climate Stress Test — ECB/EBA 2022/2023, 3 scenarios, PD migration, CET1
app.include_router(tnfd_leap_router)                   # E32 TNFD LEAP — Locate/Evaluate/Assess/Prepare, sector-location screening, ENCORE
app.include_router(net_zero_targets_router)            # E33 Net Zero Targets — SBTi corporate/FLAG, NZBA, NZAMI, NZAOA, temperature score
app.include_router(esg_data_quality_router)            # E34 ESG Data Quality — coverage scoring, DQS, provider divergence, BCBS 239
app.include_router(regulatory_penalties_router)        # E35 Regulatory Penalties — CSRD/SFDR/Taxonomy/EUDR/CSDDD enforcement & fines
app.include_router(basel3_liquidity_router)            # E36 Basel III Liquidity — LCR/NSFR/IRRBB/ALM gap/climate HQLA haircut
app.include_router(social_taxonomy_router)             # E37 Social Taxonomy & Impact — EU Social Tax, IMP 5-dim, IRIS+, SFDR Art2(17)
app.include_router(forced_labour_router)               # E38 Forced Labour — EU FLR 2024/3015, ILO 11 indicators, UK MSA, LkSG
app.include_router(transition_finance_router)          # E39 Transition Finance — GFANZ 4-category, TPT, ICMA CTF, TFR vs GAR
app.include_router(csrd_dma_router)                    # E40 CSRD DMA — ESRS 1 §§42-49 impact + financial materiality, stakeholder mapping
app.include_router(physical_hazard_router)             # E41 Physical Hazard — flood/wildfire/heat/sea-level/cyclone IPCC AR6 asset-level
app.include_router(avoided_emissions_router)           # E42 Avoided Emissions — Scope 4 enablement/substitution, Article 6 ITMOs, BVCM
app.include_router(green_hydrogen_e43_router)          # E43 Green Hydrogen — EU Delegated Act 2023/1184, LCOH, RFNBO criteria, IRA 45V
app.include_router(biodiversity_finance_v2_router)     # E44 Biodiversity Finance v2 — TNFD LEAP, PBAF, ENCORE, GBF COP15 30×30, MSA, BFFI, BNG
app.include_router(prudential_climate_risk_router)     # E45 Prudential Climate Risk — BOE/PRA BES 2025, ECB DFAST 2024, NGFS v4, ICAAP Pillar 2a/2b
app.include_router(carbon_markets_intel_router)        # E46 Carbon Markets Intel — Art 6.2/6.4, VCMI Claims Code, ICVCM CCPs, CORSIA Phase 2
app.include_router(just_transition_router)             # E47 Just Transition — ILO JT Guidelines, ESRS S1-S4, SEC Human Capital, Living Wage, CBI
app.include_router(shipping_maritime_router)           # E48 Shipping & Maritime — IMO GHG 2023, CII A-E, EEXI, Poseidon Principles, FuelEU Maritime
app.include_router(aviation_climate_router)            # E49 Aviation Climate — CORSIA Phase 2, SAF mandates, EU ETS Aviation, IATA NZC
app.include_router(commercial_re_router)               # E50 Commercial RE Net Zero — CRREM 2.0, EPC/EPBD 2024, GRESB RE, REFI, retrofit NPV
app.include_router(infrastructure_finance_router)      # E51 Infrastructure Climate Finance — EP4, IFC PS 1-8, OECD, Paris Alignment, blended finance
app.include_router(nbs_router)                         # E52 Nature-Based Solutions — IUCN GS v2.0, REDD+ VM0007, Blue Carbon VM0033, Soil Carbon IPCC, ARR, AFOLU
app.include_router(water_risk_router)                  # E53 Water Risk & Security — WRI Aqueduct 4.0, CDP Water A-List, CSRD ESRS E3, TNFD Water Dependency
app.include_router(food_system_router)                 # E54 Food System & Land Use — SBTi FLAG, FAO Crop Yield RCP, TNFD Food LEAP, EUDR, ICTI, FOLU
app.include_router(circular_economy_router)            # E55 Circular Economy Finance — CSRD ESRS E5, EMF MCI, WBCSD CTI, EPR schemes, EU CRM Act 2023
app.include_router(climate_litigation_router)          # E56 Climate Litigation & Legal Risk — TCFD liability, greenwashing enforcement, D&O exposure, SEC
app.include_router(esg_ratings_router)                 # E57 ESG Ratings Reform — EU ESRA 2024/3005, MSCI/Sustainalytics divergence, bias analysis
app.include_router(methane_fugitive_router)            # E58 Methane & Fugitive Emissions — EU Methane Reg 2024/1787, OGMP 2.0, super-emitter, GWP-20
app.include_router(health_climate_router)              # E59 Health-Climate Nexus — heat stress, air quality WHO, vector disease, WHO CCS
app.include_router(maritime_router)                    # E60 Maritime & Shipping Decarbonisation — IMO GHG 2023, CII/EEXI, EU ETS shipping, FuelEU Maritime
app.include_router(hydrogen_router)                    # E61 Hydrogen Economy Finance — RFNBO Delegated Act, EU H2 Bank, LCOH, green/blue/grey/pink taxonomy
# Note: E62 just_transition_finance routes registered via line 65 early import (same file as just_transition.py)
app.include_router(cdr_router)                         # E63 Carbon Removal & CDR Finance — IPCC AR6 CDR, BeZero AAA-CCC, Oxford Principles, VCMI Claims, Art 6.4
app.include_router(transition_finance_router)          # E64 Transition Finance Alignment — GFANZ, SBTi Net-Zero Standard, TPT Disclosure, CA100+, PACTA
app.include_router(biodiversity_credits_router)        # E65 Biodiversity Credits & Nature Markets — UK BNG DEFRA 4.0, EU NRL 2024/1991, SBTN v1.1, TNFD Advanced
app.include_router(climate_stress_test_router)         # E66 Climate Stress Testing — BCBS 517, BoE CBES, ECB CST 2022, APRA CLT, NGFS Phase 4
app.include_router(scope3_analytics_router)            # E67 Scope 3 Deep-Dive — GHG Protocol Cat 1-15, FLAG, Avoided Emissions, PCAF DQS, SBTi Scope 3
app.include_router(blue_economy_router)                # E68 Blue Economy & Ocean Finance — ICMA Blue Bond, SOF, Blue Carbon, BBNJ High Seas Treaty 2023
app.include_router(sovereign_debt_climate_router)      # E69 Climate-Linked Sovereign Debt — CRDC, Debt-for-Nature Swaps, IMF RST, Paris Club, SIDS
app.include_router(loss_damage_router)                 # E70 Loss & Damage Finance — COP28 FRLD, WIM Santiago Network, Global Shield v2, V20, Parametric
app.include_router(carbon_price_ets_router)            # E71 Carbon Price & ETS Analytics — EU ETS Phase 4, UK ETS, California, China ETS, RGGI, IEA SDS
app.include_router(blended_finance_router)           # E72 Blended Finance & DFI
app.include_router(mrv_router)                       # E73 Climate Data & MRV
app.include_router(real_asset_decarb_router)         # E74 Real Asset Decarbonisation
app.include_router(trade_finance_esg_router)         # E75 Sustainable Trade Finance
app.include_router(crypto_climate_router)            # E76 Digital Assets & Crypto Climate Risk
app.include_router(ai_governance_router)             # E77 AI Governance & ESG
app.include_router(carbon_accounting_ai_router)      # E78 Carbon Accounting AI & Automation
app.include_router(climate_insurance_router)         # E79 Climate Insurance & Parametric Risk
app.include_router(ai_risk_router)              # E76 AI & ML Risk Finance
app.include_router(nature_capital_router)       # E77 Nature Capital Accounting
app.include_router(climate_finance_router)      # E78 Climate Finance Flows
app.include_router(esg_ma_router)               # E79 ESG M&A Due Diligence
app.include_router(corporate_nature_strategy_router)   # E80 Corporate Nature Strategy & SBTN
app.include_router(green_securitisation_router)        # E81 Green Securitisation & ESG Structured Finance
app.include_router(digital_product_passport_router)    # E82 Digital Product Passport (EU ESPR)
app.include_router(adaptation_finance_router)          # E83 Adaptation Finance & Resilience Economics
app.include_router(internal_carbon_price_router)       # E84 Internal Carbon Pricing & Net-Zero Economics
app.include_router(social_bond_router)                 # E85 Social Bond & Impact Finance
app.include_router(climate_financial_statements_router) # E86 Climate Financial Statement Adjustments
app.include_router(em_climate_risk_router)             # E87 EM Climate & Transition Risk
app.include_router(biodiversity_credits_router)        # E88 Biodiversity Credits & Nature Markets
app.include_router(just_transition_router)             # E89 Just Transition Finance
app.include_router(carbon_removal_router)              # E90 Carbon Removal & CDR Finance
app.include_router(climate_litigation_router)          # E91 Climate Litigation Risk
app.include_router(water_stewardship_router)           # E92 Water Risk & Stewardship Finance
app.include_router(critical_minerals_router)           # E93 Critical Minerals & Transition Metals Risk
app.include_router(nbs_finance_router)                 # E94 Nature-Based Solutions Finance
app.include_router(sfdr_art9_router)                   # E95 SFDR Article 9 Impact Fund Assessment
app.include_router(vcm_integrity_router)               # E96 VCM Integrity — ICVCM CCP / VCMI / Oxford Offsetting
app.include_router(social_taxonomy_router)             # E97 EU Social Taxonomy & HRDD — ILO / UNGP / CSDDD
app.include_router(green_hydrogen_router)              # E98 Green Hydrogen & RFNBO Compliance
app.include_router(transition_finance_router)          # E99 Transition Finance Credibility — GFANZ/TPT/SBTi
app.include_router(stress_test_orchestrator_router)   # E100 Multi-Regulatory Stress Test Orchestrator
app.include_router(sscf_router)                       # E101 Sustainable Supply Chain Finance
app.include_router(double_materiality_router)         # E102 CSRD Double Materiality Assessment
app.include_router(temperature_alignment_router)      # E103 Financed Emissions Temperature Alignment

# ── Global error handlers ─────────────────────────────────────────────────────
from middleware.error_handler import register_error_handlers
register_error_handlers(app)

# ── Middleware stack (order matters: outermost = first to execute) ─────────────
# CORS → RateLimit → RequestLogger → AuthMiddleware → AuditMiddleware → [Route Handlers]

from middleware.audit_middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)

from middleware.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

from middleware.request_logger import RequestLoggerMiddleware
app.add_middleware(RequestLoggerMiddleware)

from middleware.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# CORS — must be outermost so CORS headers reach the client on ALL responses (including 429)
_cors_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:4000,http://127.0.0.1:4000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


# Pydantic schemas
class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    assets: Optional[List[Asset]] = None


class AssetAdd(BaseModel):
    asset: Asset


class AnalysisRequest(BaseModel):
    portfolio_id: str
    scenarios: List[str]
    horizons: List[int]


class ScenarioDataRefresh(BaseModel):
    force: bool = False


# Helper functions for SQLAlchemy → dict conversion
def _sql_asset_to_dict(a: AssetPG) -> dict:
    return {
        "id": a.id,
        "asset_type": a.asset_type.value if hasattr(a.asset_type, 'value') else a.asset_type,
        "company": {
            "name": a.company_name,
            "sector": a.company_sector.value if hasattr(a.company_sector, 'value') else a.company_sector,
            "subsector": a.company_subsector,
        },
        "exposure": a.exposure,
        "market_value": a.market_value,
        "base_pd": a.base_pd,
        "base_lgd": a.base_lgd,
        "rating": a.rating,
        "maturity_years": a.maturity_years,
    }



# Health check
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Portfolio endpoints
@app.get("/api/portfolios")
def get_portfolios(db: Session = Depends(get_db)):
    """Get all portfolios"""
    portfolios = db.query(PortfolioPG).order_by(PortfolioPG.created_at.desc()).limit(100).all()
    return {
        "portfolios": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "num_assets": len(p.assets),
                "total_exposure": sum(a.exposure for a in p.assets),
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in portfolios
        ]
    }


@app.post("/api/portfolios")
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio"""
    p = PortfolioPG(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "assets": [],
        "created_at": p.created_at.isoformat(),
    }


@app.get("/api/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Get portfolio details"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "assets": [_sql_asset_to_dict(a) for a in p.assets],
        "total_exposure": sum(a.exposure for a in p.assets),
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@app.put("/api/portfolios/{portfolio_id}")
def update_portfolio(portfolio_id: str, data: PortfolioUpdate, db: Session = Depends(get_db)):
    """Update portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if data.name is not None:
        p.name = data.name
    if data.description is not None:
        p.description = data.description
    if data.assets is not None:
        # Replace all assets: delete existing, re-insert from request
        for existing in list(p.assets):
            db.delete(existing)
        db.flush()
        for asset in data.assets:
            db.add(AssetPG(
                id=asset.id or str(uuid.uuid4()),
                portfolio_id=portfolio_id,
                asset_type=asset.asset_type,
                company_name=asset.company.name,
                company_sector=asset.company.sector,
                company_subsector=asset.company.subsector,
                exposure=asset.exposure,
                market_value=asset.market_value,
                base_pd=asset.base_pd,
                base_lgd=asset.base_lgd,
                rating=asset.rating,
                maturity_years=asset.maturity_years,
            ))
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "assets": [_sql_asset_to_dict(a) for a in p.assets],
        "updated_at": p.updated_at.isoformat(),
    }


@app.delete("/api/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Delete portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p)
    db.commit()
    return {"message": "Portfolio deleted", "id": portfolio_id}


@app.post("/api/portfolios/{portfolio_id}/assets")
def add_asset_to_portfolio(portfolio_id: str, data: AssetAdd, db: Session = Depends(get_db)):
    """Add asset to portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    asset = data.asset
    sql_asset = AssetPG(
        id=asset.id if asset.id else str(uuid.uuid4()),
        portfolio_id=portfolio_id,
        asset_type=asset.asset_type,
        company_name=asset.company.name,
        company_sector=asset.company.sector,
        company_subsector=asset.company.subsector,
        exposure=asset.exposure,
        market_value=asset.market_value,
        base_pd=asset.base_pd,
        base_lgd=asset.base_lgd,
        rating=asset.rating,
        maturity_years=asset.maturity_years,
    )
    db.add(sql_asset)
    p.updated_at = datetime.utcnow()
    db.commit()
    return {
        "message": "Asset added",
        "asset": _sql_asset_to_dict(sql_asset),
        "portfolio_id": portfolio_id,
    }


@app.delete("/api/portfolios/{portfolio_id}/assets/{asset_id}")
def remove_asset_from_portfolio(portfolio_id: str, asset_id: str, db: Session = Depends(get_db)):
    """Remove asset from portfolio"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    asset = db.query(AssetPG).filter(
        AssetPG.id == asset_id, AssetPG.portfolio_id == portfolio_id
    ).first()
    if asset:
        db.delete(asset)
    p.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Asset removed", "asset_id": asset_id}


# Scenario data endpoints
@app.get("/api/scenario-data")
def get_scenario_data(db: Session = Depends(get_db)):
    """Get overview of available scenario data"""
    from sqlalchemy import distinct
    scenarios = [r[0] for r in db.query(distinct(ScenarioSeriesSQL.scenario)).all()]
    variables = [r[0] for r in db.query(distinct(ScenarioSeriesSQL.variable)).all()]
    regions = [r[0] for r in db.query(distinct(ScenarioSeriesSQL.region)).all()]
    years = sorted([r[0] for r in db.query(distinct(ScenarioSeriesSQL.year)).all()])
    total = db.query(ScenarioSeriesSQL).count()
    return {
        "scenarios": scenarios,
        "variables": variables,
        "regions": regions,
        "years": years,
        "total_records": total,
    }


@app.post("/api/scenario-data/refresh")
def refresh_scenario_data(data: ScenarioDataRefresh, db: Session = Depends(get_db)):
    """Refresh scenario data from NGFS sources"""
    from datetime import datetime as dt
    existing_count = db.query(ScenarioSeriesSQL).count()
    if existing_count > 0 and not data.force:
        return {
            "message": "Scenario data already exists. Use force=true to refresh.",
            "existing_records": existing_count,
        }

    SCENARIOS = ['Orderly', 'Disorderly', 'Hot house world']
    HORIZONS = [2030, 2040, 2050]
    scenario_profiles = {
        'Orderly': {
            'carbon_price_mult': [2.0, 3.5, 5.0],
            'gdp_growth': [0.98, 0.95, 0.93],
            'emissions_mult': [0.7, 0.4, 0.2],
            'coal_mult': [0.5, 0.2, 0.05],
            'temp_increase': [1.6, 1.7, 1.8],
        },
        'Disorderly': {
            'carbon_price_mult': [1.5, 4.0, 6.0],
            'gdp_growth': [0.95, 0.90, 0.85],
            'emissions_mult': [0.8, 0.5, 0.25],
            'coal_mult': [0.7, 0.3, 0.1],
            'temp_increase': [1.8, 2.0, 2.1],
        },
        'Hot house world': {
            'carbon_price_mult': [1.0, 1.2, 1.3],
            'gdp_growth': [1.0, 0.92, 0.80],
            'emissions_mult': [1.0, 1.1, 1.2],
            'coal_mult': [0.95, 0.85, 0.75],
            'temp_increase': [2.5, 3.2, 4.0],
        },
    }
    regions = ['World', 'United States', 'European Union', 'China']
    model_name = 'NGFS_Phase5_Synthetic'
    source_version = f"NGFS_Phase5_{dt.utcnow().strftime('%Y%m%d')}"
    baseline = {
        'carbon_price': 30,
        'gdp': 100,
        'emissions': 50,
        'temperature': 1.2,
    }

    if data.force:
        db.query(ScenarioSeriesSQL).delete()
        db.commit()

    records = []
    for scenario in SCENARIOS:
        profile = scenario_profiles[scenario]
        for idx, year in enumerate(HORIZONS):
            for region in regions:
                if region == 'United States':
                    region_mult = 0.9
                elif region == 'European Union':
                    region_mult = 0.85
                elif region == 'China':
                    region_mult = 1.1
                else:
                    region_mult = 1.0
                records.extend([
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='Price|Carbon', unit='USD/tCO2',
                        value=baseline['carbon_price'] * profile['carbon_price_mult'][idx] * region_mult,
                        source_version=source_version,
                    ),
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='GDP|PPP', unit='Index (2020=100)',
                        value=baseline['gdp'] * profile['gdp_growth'][idx] * region_mult,
                        source_version=source_version,
                    ),
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='Emissions|CO2', unit='GtCO2',
                        value=baseline['emissions'] * profile['emissions_mult'][idx] * region_mult,
                        source_version=source_version,
                    ),
                    ScenarioSeriesSQL(
                        year=year, scenario=scenario, model=model_name, region=region,
                        variable='Temperature|Global Mean', unit='degC',
                        value=baseline['temperature'] + profile['temp_increase'][idx],
                        source_version=source_version,
                    ),
                ])

    db.bulk_save_objects(records)
    db.commit()
    return {
        "message": "Scenario data refreshed successfully",
        "records_inserted": len(records),
        "source_version": source_version,
    }


# Analysis endpoints
@app.post("/api/analysis/run")
def run_analysis(data: AnalysisRequest, db: Session = Depends(get_db)):
    """Run scenario analysis on a portfolio using the calculation engine"""
    p = db.query(PortfolioPG).filter(PortfolioPG.id == data.portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if len(p.assets) == 0:
        raise HTTPException(status_code=400, detail="Portfolio has no assets")

    # Convert SQL assets to Pydantic Asset objects for the calculation engine
    pydantic_assets = [
        Asset(
            id=a.id,
            asset_type=a.asset_type,
            company=Company(
                name=a.company_name,
                sector=a.company_sector,
                subsector=a.company_subsector,
            ),
            exposure=a.exposure,
            market_value=a.market_value,
            base_pd=a.base_pd,
            base_lgd=a.base_lgd,
            rating=a.rating,
            maturity_years=a.maturity_years,
        )
        for a in p.assets
    ]

    asset_inputs = assets_to_inputs(pydantic_assets)
    engine = ClimateRiskCalculationEngine(
        n_simulations=10000,
        correlation=0.3,
        var_method='monte_carlo',
        base_return=0.05,
        random_seed=42,
    )
    engine_results = engine.calculate_multiple_scenarios(
        assets=asset_inputs,
        scenarios=data.scenarios,
        horizons=data.horizons,
        include_sector_breakdown=False,
    )
    results = engine_results_to_models(engine_results)

    results_json = [r.model_dump() for r in results]
    analysis = AnalysisRunPG(
        id=str(uuid.uuid4()),
        portfolio_id=p.id,
        portfolio_name=p.name,
        scenarios=data.scenarios,
        horizons=data.horizons,
        results=results_json,
        status="completed",
        completed_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return {
        "id": analysis.id,
        "portfolio_id": p.id,
        "portfolio_name": p.name,
        "scenarios": data.scenarios,
        "horizons": data.horizons,
        "results": results_json,
        "status": "completed",
        "created_at": analysis.created_at.isoformat(),
    }


@app.get("/api/analysis/runs")
def get_analysis_runs(portfolio_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all analysis runs, optionally filtered by portfolio"""
    q = db.query(AnalysisRunPG).order_by(AnalysisRunPG.created_at.desc())
    if portfolio_id:
        q = q.filter(AnalysisRunPG.portfolio_id == portfolio_id)
    runs = q.limit(100).all()
    return {
        "runs": [
            {
                "id": r.id,
                "portfolio_id": r.portfolio_id,
                "portfolio_name": r.portfolio_name,
                "scenarios": r.scenarios,
                "horizons": r.horizons,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]
    }


@app.get("/api/analysis/runs/{run_id}")
def get_analysis_run(run_id: str, db: Session = Depends(get_db)):
    """Get detailed analysis run results"""
    run = db.query(AnalysisRunPG).filter(AnalysisRunPG.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return {
        "id": run.id,
        "portfolio_id": run.portfolio_id,
        "portfolio_name": run.portfolio_name,
        "scenarios": run.scenarios,
        "horizons": run.horizons,
        "results": run.results or [],
        "status": run.status,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message,
    }


@app.delete("/api/analysis/runs/{run_id}")
def delete_analysis_run(run_id: str, db: Session = Depends(get_db)):
    """Delete analysis run"""
    run = db.query(AnalysisRunPG).filter(AnalysisRunPG.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    db.delete(run)
    db.commit()
    return {"message": "Analysis run deleted", "id": run_id}


# Sample data generation
@app.post("/api/sample-data/generate")
def generate_sample_data(db: Session = Depends(get_db)):
    """Generate sample portfolio for demo purposes"""
    existing = db.query(PortfolioPG).filter(
        PortfolioPG.name == "Sample Climate Risk Portfolio"
    ).first()
    if existing:
        return {"message": "Sample portfolio already exists", "portfolio_id": existing.id}

    companies_data = [
        {'name': 'MegaCoal Energy', 'sector': Sector.POWER_GENERATION, 'subsector': 'Coal'},
        {'name': 'SolarWind Power', 'sector': Sector.POWER_GENERATION, 'subsector': 'Renewables'},
        {'name': 'PetroGiant Inc', 'sector': Sector.OIL_GAS, 'subsector': 'Integrated'},
        {'name': 'SteelWorks Global', 'sector': Sector.METALS_MINING, 'subsector': 'Steel'},
        {'name': 'AutoFuture Motors', 'sector': Sector.AUTOMOTIVE, 'subsector': 'ICE Vehicles'},
        {'name': 'ElectricDrive Co', 'sector': Sector.AUTOMOTIVE, 'subsector': 'EV'},
        {'name': 'GlobalAir Airlines', 'sector': Sector.AIRLINES, 'subsector': 'Passenger'},
        {'name': 'GreenBuildings REIT', 'sector': Sector.REAL_ESTATE, 'subsector': 'Commercial'},
    ]
    asset_types = [AssetType.BOND, AssetType.LOAN, AssetType.EQUITY]

    portfolio_id = str(uuid.uuid4())
    p = PortfolioPG(
        id=portfolio_id,
        name="Sample Climate Risk Portfolio",
        description="Diversified portfolio across climate-sensitive sectors for demonstration",
    )
    db.add(p)
    db.flush()

    sql_assets = []
    total_exposure = 0.0
    for company_data in companies_data:
        for j in range(2):
            asset_type = asset_types[j % len(asset_types)]
            base_pd_map = {
                Sector.POWER_GENERATION: 0.02 if 'Coal' in company_data['subsector'] else 0.01,
                Sector.OIL_GAS: 0.025,
                Sector.METALS_MINING: 0.03,
                Sector.AUTOMOTIVE: 0.02 if 'ICE' in company_data['subsector'] else 0.015,
                Sector.AIRLINES: 0.04,
                Sector.REAL_ESTATE: 0.015,
            }
            base_pd = base_pd_map[company_data['sector']]
            lgd_map = {AssetType.BOND: 0.45, AssetType.LOAN: 0.40, AssetType.EQUITY: 0.90}
            lgd = lgd_map[asset_type]
            if base_pd < 0.01:
                rating = 'AAA'
            elif base_pd < 0.02:
                rating = 'A'
            elif base_pd < 0.03:
                rating = 'BBB'
            else:
                rating = 'BB'
            exposure = float(np.random.uniform(1e6, 10e6))
            total_exposure += exposure
            a = AssetPG(
                id=str(uuid.uuid4()),
                portfolio_id=portfolio_id,
                asset_type=asset_type,
                company_name=company_data['name'],
                company_sector=company_data['sector'],
                company_subsector=company_data['subsector'],
                exposure=exposure,
                market_value=float(np.random.uniform(1e6, 10e6)),
                base_pd=base_pd,
                base_lgd=lgd,
                rating=rating,
                maturity_years=int(np.random.randint(3, 10)),
            )
            db.add(a)
            sql_assets.append(a)

    scenario_count = db.query(ScenarioSeriesSQL).count()
    db.commit()

    if scenario_count == 0:
        refresh_scenario_data(ScenarioDataRefresh(force=False), db)

    return {
        "message": "Sample portfolio created successfully",
        "portfolio_id": portfolio_id,
        "num_assets": len(sql_assets),
        "total_exposure": total_exposure,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
