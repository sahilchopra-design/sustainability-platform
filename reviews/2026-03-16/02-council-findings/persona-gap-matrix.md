# 02 — Persona × Sector Gap Matrix
**Date:** 2026-03-16

## Persona Definitions
| Persona | Role | Primary Needs |
|---------|------|---------------|
| **Analytics Lead** | Quantitative analyst, risk modeller | Calculation accuracy, data pipelines, model validation, API quality |
| **Investment Lead** | Portfolio manager, CIO, PE/AM deal lead | Portfolio views, scenario impact on NAV/returns, investment decision support |
| **Sustainability Regulatory Lead** | ESG/compliance officer, regulatory reporting head | Framework compliance, disclosure completeness, audit-ready outputs |

---

## Sector: Finance — Banking

### Analytics Lead × Banking
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| IFRS 9 ECL with climate overlays | `ecl_climate_engine.py` — full IFRS 9 Stage 1/2/3 with EBA GL/2022/16 | LGD/EAD inputs are model parameters, not drawn from live loan book DB records | P1 |
| Basel III/IV RWA calculation | `banking_risk_engine.py`, `basel_capital_engine.py` — full Pillar 1 | Climate RWA add-on is an estimate, not Basel IV SA/IRB compliant | P1 |
| PD backtesting and validation | `pd_backtester.py`, `model_validation_framework.py` exist | No confirmed test data set; model validation results not persisted | P2 |
| Stress test scenario impact | `stress_test_runner.py` | No Pillar 2 ICAAP document output | P2 |
| PCAF DQS weighted aggregation | `pcaf_waci_engine.py` exists | DQS weighted avg at portfolio level confirmed pending (WORK_PLAN B4) | P1 |

**UX Friction:** No analyst workbench with loan-book drill-down. Results are per-request only; no persistent assessment history with versioning.

---

### Investment Lead × Banking
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Portfolio climate risk dashboard | `PortfolioAnalyticsPage` with `portfolio_analytics_engine_v2.py` | Falls back to zeros when DB is empty; reference data is hardcoded | P0 |
| Scenario comparison (orderly vs. hot-house) | Scenario comparison endpoint in portfolio analytics | Comparison uses estimated sector averages, not actual portfolio holdings from DB | P1 |
| Credit VaR under climate scenarios | VaR endpoint in portfolio analytics | VaR calculation uses seed-based spreads not real credit spreads | P1 |
| Counterparty climate scoring | `counterparty_climate_scorer.py` | No integration with live GLEIF LEI data for entity matching | P1 |

**UX Friction:** Dashboard KPI cards show zeros without data. No guided data loading flow before analytics are usable.

---

### Sustainability Regulatory Lead × Banking
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| GAR (Green Asset Ratio) calculation | `gar_calculator.py`, `GarEtsPage.jsx` | Frontend KPIs are seeded — actual GAR requires EU Taxonomy assessment per loan | P0 |
| PCAF financed emissions reporting | `pcaf_unified.py`, `pcaf_asset_classes.py` | Listed Equity asset class pending (WORK_PLAN B6); DQS portfolio aggregation pending | P1 |
| CSRD reporting for bank entity | `regulatory_report_compiler.py` | Output is JSON only; no PDF/XBRL submission format | P1 |
| EBA Art 449a Pillar 3 climate disclosures | `gar.py` exists | No structured Pillar 3 template output; no validation against EBA ITS templates | P1 |
| SFDR PAI statement for fund products | `sfdr_pai.py` complete | Annex III/IV/V formatted output not confirmed | P1 |

**UX Friction:** Regulatory Lead has to navigate 30+ nav items to find related modules. No "regulatory dashboard" that groups all open regulatory obligations in one view.

---

## Sector: Finance — Asset Management

### Analytics Lead × Asset Management
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Paris Alignment tracking (PACTA) | `am_engine.py` — PACTA temperature scoring | No live SBTi target data integration (WORK_PLAN A14 pending for live feed) | P1 |
| ESG factor attribution | `am_engine.py` — Fama-French + ESG factor | Factor returns are modelled estimates, not live factor data from Bloomberg/MSCI | P1 |
| Green bond screening ICMA/EU GBS | `am_engine.py` — ICMA GBS + EU GBS 2023/2631 | No greenium market data feed; coupon spread data is hardcoded | P2 |
| ESG-constrained portfolio optimisation | `am_engine.py` — mean-variance with ESG tilts | No live covariance matrix; uses estimated sector correlations | P1 |

---

### Investment Lead × Asset Management
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Fund product classification (Art 8/9) | `sfdr_exclusion.py` | No end-to-end fund product registration workflow | P1 |
| SFDR PAI monitoring dashboard | `SFDRPAIPage` exists | PAI inputs are manually provided — no automatic pull from portfolio data | P1 |
| Glidepath tracking vs. 1.5°C | `GlidepathTrackerPage` | WORK_PLAN F4 lists "wire to time-series API" as pending | P1 |
| Climate-adjusted spread analysis | `am_engine.py` — climate-adjusted spreads | No live credit spread data; spread delta is calculated not market-observed | P2 |

---

### Sustainability Regulatory Lead × Asset Management
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| SFDR Periodic Disclosure (Art 11) | `sfdr_report_generator.py` | Annex format output not confirmed; no workflow for legal sign-off | P1 |
| EU Taxonomy alignment per fund | `eu_taxonomy_engine.py` | No fund-level taxonomy KPI aggregation from individual holdings | P1 |
| CSRD supply chain disclosure | `supply_chain_scope3_engine.py` | S2 (workers in value chain) data points absent from CSRD auto-populate mappings | P1 |
| Double Materiality Assessment | `double_materiality_engine.py` | No stakeholder engagement capture; audit evidence missing | P1 |

---

## Sector: Finance — Private Equity

### Analytics Lead × PE
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| DSCR / LLCR / IRR modelling | `project_finance_engine.py`, `pe_irr_sensitivity.py` | Frontend uses seeded data; API call confirmed but data freshness unclear | P2 |
| Climate-adjusted exit valuations | `unified_valuation_engine.py` | Climate adjustment methodology for PE exits not standardised | P2 |
| Portfolio company emissions tracking | `supply_chain_scope3_engine.py` | No automatic data pull from portfolio company filings | P1 |

### Investment Lead × PE
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Deal pipeline with ESG scoring | `PEDealsPage` → `pe_deal_engine.py` | ESG score inputs are manual; no automated data enrichment from entity profiles | P1 |
| Impact framework measurement | `pe_impact_framework.py` | Impact metrics are free-form inputs, not mapped to standard taxonomies (IMP/IRIS+) | P2 |
| ILPA reporting template | `FundManagementPage` → ILPA Reporting tab | ILPA template output format not confirmed | P2 |

### Sustainability Regulatory Lead × PE
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| SFDR Art 9 product compliance | `sfdr_exclusion.py` | No Art 9 investment strategy compliance checker | P1 |
| Portfolio company CSRD readiness | `csrd_entity_service.py` | No automated gap assessment across portfolio companies | P1 |

---

## Sector: Finance — Insurance

### Analytics Lead × Insurance
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| CAT risk modelling | `sector_assessments` → CATRiskPanel | Backend `insurance_risk_engine.py` exists | No integration with commercial CAT model vendors (RMS, AIR); parametric pricing is modelled | P1 |
| Climate-adjusted reserve adequacy | `insurance_climate_risk.py` | Solvency II SCR for climate risk not confirmed | P1 |
| PCAF Part B insurance emissions | `facilitated_emissions_engine.py` — InsuranceLineOfBusiness | Implementation confirmed for motor/property/commercial/life | No gap identified at P0/P1 | P2 |

### Sustainability Regulatory Lead × Insurance
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| EIOPA climate stress testing | Not found in route or service files | Missing entirely | P1 |
| Solvency II climate risk ORSA disclosure | Not found | Missing entirely | P1 |
| TCFD for insurers | `regulatory_report_compiler.py` — TCFD | JSON output only; insurer-specific TCFD guidance (IAIS) not referenced | P2 |

---

## Sector: Energy (Utilities, Renewables, O&G)

### Analytics Lead × Energy
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| CRREM pathway stranding analysis | `crrem_stranding_engine.py`, `epc_transition_engine.py` | CRREM data wiring to real Data Hub endpoint pending (WORK_PLAN F5) | P1 |
| LCOE modelling (wind/solar/green H2/geothermal) | `renewable_project_engine.py`, `green_hydrogen_calculator.py`, `EnergyFinancePage`, `GeothermalPage` | IRENA LCOE data integration pending (WORK_PLAN A13) | P1 |
| Grid emission factor trajectories | `grid_ef_trajectory.py` | Live IEA grid EF data not ingested | P1 |
| Methane OGMP2.0 compliance | `methane_ogmp.py` | Route file exists; OGMP reporting level assessment unclear | P2 |

### Investment Lead × Energy
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Renewable PPA risk scoring | `ppa_risk_scorer.py`, `renewable_ppa.py` | PPA merchant price risk uses modelled prices, not live power market data | P1 |
| Green bond structuring for project finance | `ProjectFinancePage` — Green Bond Alignment tab | ICMA alignment check is static reference, not live bond universe data | P2 |
| Blended finance / DFI tranche structuring | `BlendedFinancePanel` exists | Calculations use seeded data; no live development bank rate data | P2 |

### Sustainability Regulatory Lead × Energy
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| CSRD E1-E5 full disclosure | `energy_csrd_e1_climate` through `energy_csrd_e5_circular` (migration 012) | Energy sector CSRD tables exist; ESRS_MAPPINGS in csrd_auto_populate confirm E1 mapping; E3/E4/E5 source modules unclear | P1 |
| EU ETS compliance management | `eu_ets_engine.py`, `GarEtsPage.jsx` | Frontend is seeded; actual ETS registry integration absent | P0 |
| IRENA Five Pillars assessment | `irena_five_pillars.py` route exists | WORK_PLAN F7 lists frontend as pending | P2 |

**UX Friction:** Energy module pages (Energy Finance, Energy Transition) are new but disconnected from the core portfolio analytics dashboard. Energy users have no unified view.

---

## Sector: Supply Chain

### Analytics Lead × Supply Chain
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Scope 3 Category 1-15 calculation | `supply_chain_scope3_engine.py` | Emission factor library is static; no live DEFRA/ecoinvent update | P1 |
| SBTi FLAG target assessment | `agriculture_risk_engine.py` for ag; supply chain for others | SBTi FLAG (Forest, Land, Agriculture) methodology not confirmed separate from SBTi Corporate | P1 |
| EUDR due diligence workflow | `eudr_engine.py` — complete | No integration with live GFW deforestation monitoring | P1 |

### Investment Lead × Supply Chain
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Supplier risk scoring dashboard | No dedicated supplier risk scoring page | Missing as standalone UX module | P1 |
| Supply chain financing ESG screening | `china_trade_engine.py` exists | Scope limited to China trade; global supply chain financing ESG not covered | P2 |

### Sustainability Regulatory Lead × Supply Chain
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| CSDDD value chain mapping | `csddd_engine.py` — Art 14 | No supplier data ingestion wizard; tier mapping is manual input | P1 |
| EUDR DDS filing workflow | `eudr_engine.py` — DDS generation | No EU trade authority submission integration | P2 |
| CSRD ESRS G1 supply chain due diligence | Double materiality covers G1 | G1 supply chain DD narrative output not structured | P2 |

---

## Sector: Manufacturing (Heavy Industry, Chemicals, Steel)

### Analytics Lead × Manufacturing
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| CBAM embedded carbon calculation | `cbam_calculator.py` — full Articles 7/21/31 | CBAM calculator confirmed complete | No live CBAM registry integration for certificate pricing | P2 |
| Steel sector GHG intensity | `steel_calculator.py` | Confirmed service file exists | No ISSB SASB industry-specific metrics for basic materials sector in live data | P1 |
| Carbon credit methodology validation | `methodology_engine.py` — 56+ methodologies | VCS/Gold Standard registry API not integrated | P1 |

### Investment Lead × Manufacturing
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| Stranded asset risk for heavy industry | `stranded_asset_calculator.py` | Complete per MEMORY.md | No forward transition cost modelling for CapEx-heavy industries | P2 |
| Just Transition risk scoring | `just_transition_calculator.py` | Service exists | No investment decision framework linking JT risk to portfolio allocation | P2 |

### Sustainability Regulatory Lead × Manufacturing
| Workflow Needed | Available | Gap | Severity |
|----------------|-----------|-----|----------|
| CBAM CBAM Operator compliance | `cbam.py`, `cbam_calculator.py` | Confirmed Articles 7/21/31; default values per Art 4 missing | P1 |
| CSRD ESRS E1 GHG reporting | `carbon_calculator_v2.py` + CSRD auto-populate | Full pipeline confirmed | No third-party verification attestation workflow | P1 |
| Mining sector ESG | `mining_risk_calculator.py` | Service exists | No ICMM Mining Principles framework mapping | P2 |

---

## Cross-Cutting UX Friction Points

### Analytics Lead
- No unified **analyst workbench** with calculation history, versioning, and comparison
- `seededRand()` data in frontend means analysts cannot distinguish live results from demo data
- No API documentation UI (Swagger is present at `/docs` but not surfaced in the navigation)
- No **model validation dashboard** showing calibration results and backtest performance

### Investment Lead
- 89 pages in the navigation create severe information overload — no role-based navigation filtering
- Portfolio dashboard shows zeros when DB is unpopulated — no guided onboarding to populate data
- No **investment action** outputs: cannot generate a trade ticket, an allocation recommendation, or a term sheet from any calculation result
- Scenario comparison requires understanding 5 NGFS scenario names — no plain-English risk summary

### Sustainability Regulatory Lead
- **No regulatory obligation calendar** — which disclosures are due when, per jurisdiction
- Multiple regulatory frameworks are scattered across separate pages with no consolidated compliance tracker
- All report outputs are JSON — no PDF, no XBRL, no Word; the last mile to actual filing is entirely absent
- No **assurance readiness score** that aggregates data quality, completeness, and methodology soundness into a single filing confidence indicator
