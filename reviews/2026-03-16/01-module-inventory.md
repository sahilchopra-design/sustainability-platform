# 01 — Module Inventory
**Date:** 2026-03-16 | Evidence-led inventory of all major platform modules.

---

## Group A: Compliance & Reporting

### A1. CSRD / ESRS Disclosure Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Auto-populate ESRS E1-E5, S1, G1 data points from module outputs; generate CSRD report |
| **Primary Users** | Sustainability Regulatory Lead |
| **Key Service Files** | `csrd_auto_populate.py`, `csrd_entity_service.py`, `csrd_extractor.py`, `csrd_ingest_service.py` |
| **Route Files** | `csrd_reports.py` |
| **Key DB Tables** | `csrd_entity_registry`, `csrd_kpi_values`, `csrd_gap_tracker`, `csrd_disclosure_index`, `csrd_materiality_topics`, `csrd_report_uploads` (migration 016) |
| **Frameworks Served** | CSRD 2022/2464, ESRS Set 1, EFRAG IG3 |
| **Business Criticality** | Critical |
| **Implementation Completeness** | Partial |
| **Evidence** | `csrd_auto_populate.py` ESRS_MAPPINGS cover E1-E5 data points with source_module/source_field wiring. PDF extraction via `csrd_extractor.py` exists. Worker task `process_csrd_report_task` referenced but worker directory not confirmed. |
| **Analytics Lead Gap** | No dashboard for cross-entity CSRD benchmark comparison; gap tracker has no trend charts |
| **Investment Lead Gap** | No CSRD-linked portfolio scoring (e.g., percentage of portfolio with complete E1 disclosures) |
| **Sustainability Regulatory Lead Gap** | ESRS S2-S4 (Social: workers in value chain, affected communities, consumers) are not in ESRS_MAPPINGS; G1 governance limited; assurance-ready PDF output unconfirmed |

---

### A2. SFDR PAI Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Calculate all 18 mandatory + additional PAI indicators per SFDR RTS; generate Art 4/Art 8/Art 9 periodic disclosures |
| **Primary Users** | Sustainability Regulatory Lead, Investment Lead (Art 8/9 fund classification) |
| **Key Service Files** | `sfdr_pai_engine.py`, `sfdr_report_generator.py` |
| **Route Files** | `sfdr_pai.py`, `sfdr_exclusion.py` |
| **Key DB Tables** | `sfdr_pai_disclosures` (migration 009), `sfdr_pai_assessments` (migration 052) |
| **Frameworks Served** | SFDR Regulation (EU) 2019/2088, Delegated Regulation (EU) 2022/1288 RTS Annexes III-V |
| **Business Criticality** | Critical |
| **Implementation Completeness** | Complete (calculation engine), Partial (filing output) |
| **Evidence** | `sfdr_pai.py` accepts `Holding` model with full PAI fields (scope1/2 emissions, renewable share, gender pay gap, board female pct, etc.). `sfdr_report_generator.py` exists. Frontend `SFDRPAIPage` exists. |
| **Analytics Lead Gap** | No time-series PAI trend comparison year-over-year |
| **Investment Lead Gap** | Fund-level Art 8/9 classification workflow incomplete; DNSH check integration with EU Taxonomy unclear |
| **Sustainability Regulatory Lead Gap** | No structured Annex III/IV/V output format; no XBRL tagging of PAI disclosures |

---

### A3. EU Taxonomy Alignment Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Assess NACE activity alignment to 6 Environmental Objectives; compute GAR, BTAR for FIs |
| **Primary Users** | Sustainability Regulatory Lead, Investment Lead |
| **Key Service Files** | `eu_taxonomy_engine.py` |
| **Route Files** | `eu_taxonomy.py` |
| **Key DB Tables** | `eu_taxonomy_assessments`, `eu_taxonomy_activities` (migration 009), `fi_eu_taxonomy_kpis` (migration 011), `energy_csrd_e1_climate` (migration 012) |
| **Frameworks Served** | EU Taxonomy Regulation 2020/852, Delegated Acts 2021/2139 + 2023/2486 |
| **Business Criticality** | Critical |
| **Implementation Completeness** | Complete |
| **Evidence** | `eu_taxonomy.py` exposes 10 endpoints including `/assess-activity`, `/assess-entity`, `/assess-portfolio`, 8 reference GET endpoints. DNSH matrix, transitional/enabling activities, GAR/BTAR definitions all present. |
| **Analytics Lead Gap** | No sector-level taxonomy alignment benchmarking vs. peers |
| **Investment Lead Gap** | No portfolio-level taxonomy heatmap in the frontend |
| **Sustainability Regulatory Lead Gap** | No full DNSH evidence upload workflow; Article 18 minimum safeguards (OECD, UNGPs) are reference data only, not verified against entity records |

---

### A4. XBRL Filing & Ingestion Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate iXBRL-tagged HTML and XBRL XML for ESRS/ISSB regulatory filing; ingest third-party XBRL filings |
| **Primary Users** | Sustainability Regulatory Lead |
| **Key Service Files** | `xbrl_export_engine.py`, `xbrl_ingestion_engine.py` |
| **Route Files** | `xbrl_export.py` |
| **Key DB Tables** | No dedicated XBRL persistence table identified |
| **Frameworks Served** | EFRAG ESRS XBRL Taxonomy 2024, ESMA ESEF, IFRS S1/S2 Taxonomy |
| **Business Criticality** | High |
| **Implementation Completeness** | Partial |
| **Evidence** | `xbrl_export_engine.py` has ESRS_XBRL_TAXONOMY mapping ESRS data point IDs to XBRL concepts. Data type `monetaryItemType` vs `decimalItemType` mapping contains a bug: E1-6_scope1_gross uses `iso4217:EUR` as XBRL unit but scope 1 emissions are tCO2e, not EUR — unit mismatch. |
| **Analytics Lead Gap** | No XBRL validation against ESMA filing rules before submission |
| **Investment Lead Gap** | Not applicable |
| **Sustainability Regulatory Lead Gap** | No filing workflow (draft → review → approve → submit); unit mapping bug on scope 1 tagging; no ESMA inline XBRL viewer integration |

---

### A5. Double Materiality Assessment (DMA)
| Attribute | Value |
|-----------|-------|
| **Purpose** | EFRAG IG1/IG3 double materiality assessment: impact materiality + financial materiality across all 10 ESRS topics |
| **Primary Users** | Sustainability Regulatory Lead |
| **Key Service Files** | `double_materiality_engine.py` |
| **Route Files** | `double_materiality.py` |
| **Key DB Tables** | `dma_assessments`, `dma_topic_scores` (migration 052) |
| **Frameworks Served** | CSRD, ESRS 1, EFRAG IG1, ISSB S1/S2 cross-mapping |
| **Business Criticality** | High |
| **Implementation Completeness** | Complete (engine), Partial (stakeholder engagement workflow missing) |
| **Evidence** | `double_materiality_engine.py` covers all 10 ESRS topics (E1-E5, S1-S4, G1) with impact/financial scoring, cross-framework mappings to GRI/TCFD/ISSB/SDGs. |
| **Analytics Lead Gap** | No peer DMA comparison (what percentage of sector considers E3 water material?) |
| **Investment Lead Gap** | No materiality-to-investment thesis linkage |
| **Sustainability Regulatory Lead Gap** | Stakeholder engagement evidence not captured; IRO-1/IRO-2 narrative outputs not structured for audit |

---

### A6. SEC Climate Disclosure Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Assess SEC Reg S-K 1500-1505 and Reg S-X 14-02 compliance; GHG attestation readiness |
| **Primary Users** | Sustainability Regulatory Lead (US filers), Investment Lead |
| **Key Service Files** | `sec_climate_engine.py` |
| **Route Files** | `sec_climate.py` |
| **Key DB Tables** | `sec_climate_assessments` (migration 047) |
| **Frameworks Served** | SEC Release 33-11275 (March 2024), Reg S-K §§229.1500-1507, Reg S-X 14-02 |
| **Business Criticality** | High |
| **Implementation Completeness** | Complete |
| **Evidence** | `sec_climate_engine.py` covers 5 filer categories (LAF, AF, NAF, SRC, EGC), 5 Reg S-K items, 3 Reg S-X items, PSLRA safe harbor, attestation requirements. 4 POST + 6 GET ref endpoints. |
| **Analytics Lead Gap** | No cross-company SEC filing comparison |
| **Investment Lead Gap** | No materiality bridge from SEC disclosures to portfolio impact |
| **Sustainability Regulatory Lead Gap** | SEC disclosure stayed in federal court (March 2025) — engine reflects original March 2024 rule but not stayed requirements; this creates a compliance mismatch risk |

---

### A7. CSRD PDF Extraction Pipeline
| Attribute | Value |
|-----------|-------|
| **Purpose** | Upload third-party CSRD PDFs, extract KPIs using NLP, populate gap tracker |
| **Primary Users** | Sustainability Regulatory Lead, Analytics Lead |
| **Key Service Files** | `csrd_extractor.py`, `csrd_ingest_service.py` |
| **Route Files** | `csrd_reports.py` (also ingestion endpoints) |
| **Key DB Tables** | `csrd_report_uploads` (migration 016) |
| **Frameworks Served** | CSRD |
| **Business Criticality** | High |
| **Implementation Completeness** | Stub |
| **Evidence** | `csrd_reports.py` imports `from workers.tasks.csrd_tasks import process_csrd_report_task` — worker directory not confirmed in file listing. PDF upload endpoint exists. Extraction logic unknown completeness. |
| **Analytics Lead Gap** | Entire pipeline unverifiable without worker confirmation |
| **Sustainability Regulatory Lead Gap** | If worker is absent, PDF ingestion is broken at upload |

---

### A8. EUDR Compliance Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | EU Deforestation Regulation compliance: commodity screening, Art 29 country risk, traceability, DDS generation |
| **Primary Users** | Sustainability Regulatory Lead (supply chain operators) |
| **Key Service Files** | `eudr_engine.py` |
| **Route Files** | `eudr.py` |
| **Key DB Tables** | `eudr_operators`, `eudr_due_diligence`, `eudr_commodity_lots` (migration 045) |
| **Frameworks Served** | EUDR Regulation (EU) 2023/1115 |
| **Business Criticality** | High |
| **Implementation Completeness** | Complete |
| **Evidence** | 7 commodities, 63 HS/CN codes, 55 countries across 3 risk tiers, 6 certification schemes, DDS generation per Art 4(2). 6 POST + 7 GET endpoints. |
| **Analytics Lead Gap** | No commodity lot tracking dashboard |
| **Sustainability Regulatory Lead Gap** | Geolocation validation uses simple polygon check — no integration with live GFW deforestation alerts |

---

### A9. CSDDD Compliance Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | EU CSDDD Art 2 scope assessment, Art 6 adverse impacts, Art 5-13 due diligence, Art 22 climate transition plan |
| **Primary Users** | Sustainability Regulatory Lead |
| **Key Service Files** | `csddd_engine.py` |
| **Route Files** | `csddd.py` |
| **Key DB Tables** | `csddd_entities`, `csddd_assessments`, `csddd_adverse_impacts` (migration 046) |
| **Frameworks Served** | Directive (EU) 2024/1760 |
| **Business Criticality** | High |
| **Implementation Completeness** | Complete |
| **Evidence** | 6 phased scope groups, 18 adverse impact categories, 9 DD obligations with weighted scoring, Art 14 value chain mapping. |
| **Sustainability Regulatory Lead Gap** | Grievance mechanism (Art 9) tracking is a table only — no case management UI workflow |

---

### A10. Regulatory Report Compiler
| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate structured SFDR, TCFD, CSRD, ISSB, SEC, GRI 305, UK TCFD, APRA CPG229, BRSR reports |
| **Primary Users** | Sustainability Regulatory Lead |
| **Key Service Files** | `regulatory_report_compiler.py` |
| **Route Files** | `regulatory_reports.py` |
| **Key DB Tables** | `compiled_regulatory_reports`, `compiled_report_sections` (migration 044) |
| **Frameworks Served** | 10 frameworks |
| **Business Criticality** | Critical |
| **Implementation Completeness** | Partial |
| **Evidence** | TCFD_RECOMMENDATIONS, SFDR framework present. 10 frameworks covered in service. No confirmed PDF/Word output pipeline — generates structured JSON only. |
| **Sustainability Regulatory Lead Gap** | JSON output is not submission-ready; no PDF renderer, no XBRL auto-attach, no digital signature |

---

## Group B: Carbon Accounting

### B1. Carbon Calculator v1 / v2
| Attribute | Value |
|-----------|-------|
| **Purpose** | GHG Protocol Scope 1/2/3 corporate emissions calculation |
| **Key Service Files** | `carbon_calculator.py`, `carbon_calculator_v2.py` |
| **Route Files** | `carbon.py` |
| **Key DB Tables** | `carbon` model in `db/models/carbon.py` |
| **Frameworks Served** | GHG Protocol, ESRS E1-6, ISO 14064-1 |
| **Business Criticality** | Critical |
| **Completeness** | Complete |
| **Evidence** | v2 listed in MODULE_SIGNATURES with full I/O including scope1/2/3, intensity per revenue/FTE, GWP AR5 reference data. DEFRA conversion factors, IEA grid EFs referenced. |
| **Key Gap** | No activity-level audit trail; emission factor vintage tracking absent; no third-party verification integration |

---

### B2. CBAM Calculator
| Attribute | Value |
|-----------|-------|
| **Purpose** | EU Carbon Border Adjustment Mechanism compliance: Articles 7, 21, 31 |
| **Key Service Files** | `cbam_calculator.py`, `cbam_service.py` |
| **Route Files** | `cbam.py` |
| **Frameworks Served** | CBAM Regulation (EU) 2023/956 |
| **Business Criticality** | High |
| **Completeness** | Complete |

---

### B3. PCAF Unified Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | PCAF Parts A (financed), B (insurance), C (facilitated) emissions; WACI, DQS scoring |
| **Key Service Files** | `pcaf_unified_engine.py`, `pcaf_waci_engine.py`, `facilitated_emissions_engine.py`, `pcaf_quality_engine.py` |
| **Route Files** | `pcaf_unified.py`, `pcaf_advanced.py`, `pcaf_asset_classes.py`, `pcaf_quality.py` |
| **Key DB Tables** | `facilitated_emissions_v2`, `insurance_emissions` (migration 041) |
| **Frameworks Served** | PCAF Global GHG Standard v2.0 Parts A, B, C; SFDR PAI #1 |
| **Business Criticality** | Critical |
| **Completeness** | Partial |
| **Key Gap** | PCAF Listed Equity asset class confirmed pending (WORK_PLAN.md B6). DQS weighted aggregation at portfolio level (B4) pending. |

---

### B4. Methodology Engine (CDM/VCS/Gold Standard)
| Attribute | Value |
|-----------|-------|
| **Purpose** | 56+ carbon credit methodologies validation and calculation |
| **Key Service Files** | `methodology_engine.py`, `cdm_tools_engine.py` |
| **Route Files** | `cdm_tools.py` |
| **Frameworks Served** | CDM, VCS, Gold Standard |
| **Business Criticality** | Medium |
| **Completeness** | Complete |

---

## Group C: Climate Risk

### C1. ECL Climate Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | IFRS 9 ECL with climate overlays per EBA GL/2022/16, BCBS 2022 |
| **Key Service Files** | `ecl_climate_engine.py` |
| **Route Files** | `ecl_climate.py` |
| **Key DB Tables** | `ecl_assessments`, `ecl_exposures`, `ecl_scenario_results`, `ecl_climate_overlays` (migration 006) |
| **Frameworks Served** | IFRS 9 §5.5.1-5.5.20, EBA GL/2022/16, BCBS Principles |
| **Business Criticality** | Critical |
| **Completeness** | Complete (engine), Partial (production wiring) |
| **Evidence** | Full IFRS 9 Stage 1/2/3 classification, SICR assessment with climate drivers, forward-looking PD with scenario weights. STAGE_1 = 12m ECL, STAGE_2/3 = lifetime ECL per para 5.5.5/5.5.3/5.5.4. |
| **Key Gap** | LGD/EAD inputs are engine parameters not DB-backed from actual loan book records |

---

### C2. Physical & Transition Climate Risk Engines
| Attribute | Value |
|-----------|-------|
| **Purpose** | Physical hazard scoring (flood, heat, drought, wildfire, sea-level) and transition risk (carbon price, policy, technology) |
| **Key Service Files** | `climate_physical_risk_engine.py`, `climate_transition_risk_engine.py` |
| **Route Files** | `climate_risk.py` |
| **Frameworks Served** | NGFS Phase IV, TCFD, ECB Guide Nov 2020 |
| **Business Criticality** | Critical |
| **Completeness** | Complete |

---

### C3. Sovereign Climate Risk Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Climate-adjusted sovereign creditworthiness; 51 country profiles, 5 NGFS scenarios |
| **Key Service Files** | `sovereign_climate_risk_engine.py` |
| **Route Files** | `sovereign_climate_risk.py` |
| **Key DB Tables** | `sovereign_climate_assessments`, `sovereign_portfolio_assessments` (migration 046) |
| **Frameworks Served** | NGFS, S&P 22-point rating scale |
| **Business Criticality** | High |
| **Completeness** | Complete |

---

### C4. Stress Testing Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | EBA stress test scenarios, ECL sensitivity, VaR under climate shocks |
| **Key Service Files** | `stress_test_runner.py` |
| **Route Files** | `stress_testing.py` |
| **Frameworks Served** | EBA 2025 stress test methodology, Basel III Pillar 2 |
| **Business Criticality** | High |
| **Completeness** | Complete |

---

### C5. Banking Risk Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Credit (IFRS 9 ECL), Liquidity (LCR/NSFR), Market (VaR/FRTB), Operational (BIA/TSA), AML, Capital (Basel III/IV) |
| **Key Service Files** | `banking_risk_engine.py`, `basel_capital_engine.py` |
| **Route Files** | `banking_risk.py`, `basel_capital.py` |
| **Frameworks Served** | Basel III/IV, CRR3, EBA FINREP, FRTB |
| **Business Criticality** | Critical |
| **Completeness** | Complete |

---

### C6. Scenario Analysis Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | NGFS v2/v4 scenario analysis, custom scenario builder, trajectory comparison |
| **Key Service Files** | `scenario_analysis_engine.py`, `custom_scenario_builder.py` |
| **Route Files** | `scenario_analysis.py`, `scenario_builder_v2.py`, `ngfs_v2.py` |
| **Key DB Tables** | `ngfs_scenarios`, `scenario_trajectories` (DB models `scenario.py`, `ngfs_v2.py`) |
| **Frameworks Served** | NGFS Phase II/IV, IPCC AR6 |
| **Business Criticality** | Critical |
| **Completeness** | Complete |

---

## Group D: Nature / Biodiversity

### D1. Nature Risk Calculator (TNFD LEAP)
| Attribute | Value |
|-----------|-------|
| **Purpose** | TNFD LEAP methodology: Locate, Evaluate, Assess, Prepare for nature-related risk |
| **Key Service Files** | `nature_risk_calculator.py`, `tnfd_assessment_engine.py` |
| **Route Files** | `nature_risk.py`, `tnfd_assessment.py` |
| **Key DB Tables** | `nature_assessments` (migration 010), `nature_re_assessments`, `spatial_hazard_profiles` (migration 043) |
| **Frameworks Served** | TNFD v1.0, ENCORE, CSDDD ENV categories, ESRS E4 |
| **Business Criticality** | High |
| **Completeness** | Partial |
| **Key Gap** | No PostGIS; spatial queries use float lat/lng not polygon geometry; WDPA/GFW data is listed in ingester catalog but not confirmed live |

---

### D2. Agriculture Risk Engine (Methane, Disease, BNG)
| Attribute | Value |
|-----------|-------|
| **Purpose** | Methane intensity (IPCC Tier 1), disease outbreak (OIE/WOAH), Biodiversity Net Gain (DEFRA Metric 4.0) |
| **Key Service Files** | `agriculture_risk_engine.py` |
| **Route Files** | `agriculture_expanded.py` |
| **Frameworks Served** | IPCC GWP-100, OIE/WOAH, DEFRA BNG Metric 4.0 |
| **Business Criticality** | Medium |
| **Completeness** | Complete |

---

## Group E: Materiality

### E1. Dynamic Materiality Engine (DME)
| Attribute | Value |
|-----------|-------|
| **Purpose** | Velocity-weighted ESG scoring, controversy detection, policy change tracking, NLP sentiment pulse |
| **Key Service Files** | `dme_dmi_engine.py`, `dme_alert_engine.py`, `dme_contagion_engine.py`, `dme_velocity_engine.py`, `dme_nlp_pulse_engine.py`, `dme_policy_tracker_engine.py`, `dme_greenwashing_engine.py` |
| **Route Files** | `dme_dmi.py`, `dme_alerts.py`, `dme_contagion.py`, `dme_velocity.py`, `dme_nlp_pulse.py`, `dme_policy_tracker.py`, `dme_greenwashing.py`, `dme_factor_registry.py` |
| **Key DB Tables** | `dme_integration_tables` (migration 053) |
| **Frameworks Served** | PCAF DQS, BCBS 239 |
| **Business Criticality** | High |
| **Completeness** | Partial |
| **Key Gap** | NLP pulse depends on live news feeds; without real GDELT integration the sentiment engine has no live signal |

---

## Group F: Supply Chain ESG

### F1. Supply Chain Scope 3 Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Category 1-15 Scope 3 calculations, SBTi target alignment, CSDDD value chain mapping |
| **Key Service Files** | `supply_chain_scope3_engine.py` |
| **Route Files** | `supply_chain.py` |
| **Key DB Tables** | `sc_entities`, `scope3_assessments`, `sbti_targets`, `emission_factor_library` (migration 007) |
| **Frameworks Served** | GHG Protocol Scope 3, SBTi Corporate Standard, CSDDD |
| **Business Criticality** | High |
| **Completeness** | Complete |

---

## Group G: Finance / Investment

### G1. Portfolio Analytics Engine v2
| Attribute | Value |
|-----------|-------|
| **Purpose** | Portfolio-level climate risk dashboard: VaR, ECL, WACI, sector heatmap, scenario comparison |
| **Key Service Files** | `portfolio_analytics_engine_v2.py` |
| **Route Files** | `portfolio_analytics.py` |
| **Key DB Tables** | `portfolio_climate_risk`, `financial_instruments`, `portfolios_pg`, `portfolio_holdings` |
| **Business Criticality** | Critical |
| **Completeness** | Partial |
| **Key Gap** | Falls back to empty/zero when tables are empty. SECTOR_REFERENCE_DATA hardcoded (not from live market data). |

---

### G2. ECL / PD / LGD Pipeline
| Attribute | Value |
|-----------|-------|
| **Purpose** | Full IFRS 9 ECL pipeline: PD calculation, LGD estimation, EAD, staging |
| **Key Service Files** | `pd_calculator.py`, `lgd_calculator.py`, `ead_calculator.py`, `ecl_climate_engine.py` |
| **Route Files** | `ecl_climate.py`, `ead.py`, `lgd_vintage.py` |
| **Frameworks Served** | IFRS 9, Basel III/IV, EBA GL/2020/06 |
| **Business Criticality** | Critical |
| **Completeness** | Partial |
| **Key Gap** | PD Calculator is a standalone engine. LGD has a separate service. EAD has a route. These three are NOT confirmed to be orchestrated into a single unified ECL pipeline per IFRS 9 §5.5.17. |

---

### G3. Asset Management Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | ESG attribution (Fama-French), Paris alignment (PACTA), green bond screening (ICMA/EU GBS), climate-adjusted spreads, LP analytics, ESG-constrained optimisation |
| **Key Service Files** | `am_engine.py` |
| **Route Files** | `am.py` |
| **Key DB Tables** | `am_assessments` (migration 040) |
| **Business Criticality** | High |
| **Completeness** | Complete |

---

### G4. PE Deal Pipeline Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Deal pipeline, portfolio monitor, value creation tracking, IRR sensitivity, impact framework |
| **Key Service Files** | `pe_deal_engine.py`, `pe_portfolio_monitor.py`, `pe_irr_sensitivity.py` |
| **Route Files** | `pe_deals.py`, `pe_portfolio.py`, `pe_reporting.py` |
| **Key DB Tables** | `pe_deals`, `pe_portfolio_companies`, `pe_impact_metrics` (migration 038) |
| **Business Criticality** | High |
| **Completeness** | Complete |

---

### G5. Banking Capital / Basel Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Basel III/IV Pillar 1 RWA, Pillar 2 ICAAP, LCR, NSFR, FRTB, GAR calculation |
| **Key Service Files** | `basel_capital_engine.py`, `gar_calculator.py` |
| **Route Files** | `basel_capital.py`, `gar.py` |
| **Key DB Tables** | `pcaf_quality`, `basel_capital_tables` (migration 050) |
| **Frameworks Served** | CRR3/CRD VI, EBA Art 449a GAR |
| **Business Criticality** | Critical |
| **Completeness** | Complete |

---

### G6. Insurance Risk Engine
| Attribute | Value |
|-----------|-------|
| **Purpose** | Climate-adjusted technical pricing, cat risk, PCAF Part B insurance-associated emissions |
| **Key Service Files** | `insurance_risk_engine.py`, `insurance_climate_risk.py` |
| **Route Files** | `insurance.py`, `insurance_risk.py` |
| **Frameworks Served** | PCAF Part B, Solvency II, EIOPA climate guidance |
| **Business Criticality** | High |
| **Completeness** | Partial |
| **Key Gap** | Solvency II SCR calculation for climate risk not confirmed; EIOPA Opinion on climate stress testing integration absent |

---

### G7. Facilitated Emissions Engine (PCAF Part C)
| Attribute | Value |
|-----------|-------|
| **Purpose** | Capital markets facilitated emissions: bond underwriting, equity placement, securitisation, syndicated loans, IPO, M&A advisory |
| **Key Service Files** | `facilitated_emissions_engine.py` |
| **Route Files** | `facilitated_emissions.py` |
| **Key DB Tables** | `facilitated_emissions_v2` (migration 041) |
| **Frameworks Served** | PCAF Parts B & C, SFDR PAI #1-#4 |
| **Business Criticality** | High (investment banks, asset managers) |
| **Completeness** | Complete |

---

## Group H: UX / Workflow

### H1. Data Intake Workflows
| Attribute | Value |
|-----------|-------|
| **Purpose** | Structured data upload wizards: loan portfolio CSV, counterparty emissions, real estate EUI, shipping fleet, steel borrowers, project finance |
| **Route Files** | Frontend only — `DataIntakeDashboard`, `LoanPortfolioUpload`, `CounterpartyEmissionsWizard`, etc. |
| **Business Criticality** | High |
| **Completeness** | Stub |
| **Key Gap** | WORK_PLAN.md F3: data intake status wiring to real DB counts not done; intake completeness percentage is mocked |

---

### H2. Interactive Analytics Dashboard
| Attribute | Value |
|-----------|-------|
| **Purpose** | Collapsible filter sidebar, KPI cards, 5-tab analytics, What-If parameter studio, scenario heatmap |
| **File** | `frontend/src/pages/InteractiveDashboard.jsx` (1248 lines) |
| **Business Criticality** | High |
| **Completeness** | Complete (UI), Partial (data — seed-based, not live API) |

---

## Group I: Platform / Integration / Security

### I1. Data Lineage Service
| Attribute | Value |
|-----------|-------|
| **Purpose** | DAG-based cross-module dependency tracking, BCBS 239 compliance score, DQS propagation |
| **Key Service Files** | `data_lineage_service.py`, `lineage_orchestrator.py` |
| **Route Files** | `data_lineage.py` |
| **Business Criticality** | High (compliance assurance) |
| **Completeness** | Complete (105 modules, 65+ edges) |

---

### I2. Auth / RBAC
| Attribute | Value |
|-----------|-------|
| **Purpose** | Google OAuth session, org-scoped access, role-based permissions |
| **Route Files** | `organisations.py`, `audit_log.py` (use `require_role()`) |
| **DB** | `organisations`, `user_roles`, `users_pg` (migration 025) |
| **Business Criticality** | Critical |
| **Completeness** | Stub — WORK_PLAN.md B2 explicitly lists RBAC middleware as pending |
| **Key Gap** | `require_role()` dependency exists in 2 routes but is NOT enforced across 139 routes. Any anonymous user can call any calculation endpoint. |

---

### I3. Audit Log
| Attribute | Value |
|-----------|-------|
| **Purpose** | Append-only audit trail for all write operations |
| **Route Files** | `audit_log.py` |
| **DB** | `audit_log` table (migration 026) |
| **Business Criticality** | Critical (BCBS 239, CSRD assurance) |
| **Completeness** | Partial — DB table and read endpoints exist; WORK_PLAN.md B3 lists audit middleware wiring as pending |

---

### I4. Entity Resolution & Company Profiles
| Attribute | Value |
|-----------|-------|
| **Purpose** | LEI-based entity deduplication, 360-degree entity view |
| **Key Service Files** | `entity_resolution_service.py`, `entity360_engine.py` |
| **Route Files** | `entity_resolution.py`, `entity360.py` |
| **Key DB Tables** | `cross_module_entity_linkage` (migration 042) |
| **Business Criticality** | High |
| **Completeness** | Partial — GLEIF LEI ingester is planned (WORK_PLAN.md A3) but not confirmed live |

---

### I5. Data Hub
| Attribute | Value |
|-----------|-------|
| **Purpose** | Universal scenario data hub: source registry, trajectory storage, sync orchestration |
| **Key Service Files** | `data_hub_service.py`, `sync_orchestrator.py` |
| **Route Files** | `data_hub.py` |
| **Key DB Tables** | `data_hub` models in `db/models/data_hub.py` |
| **Business Criticality** | High |
| **Completeness** | Partial — ingestion pipeline (17 tasks per WORK_PLAN.md) not built; frontend shows FALLBACK_ arrays |
