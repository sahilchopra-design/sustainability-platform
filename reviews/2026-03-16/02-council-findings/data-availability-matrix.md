# 02 — Data Availability Matrix
**Date:** 2026-03-16

---

## Overview: Data Layer Architecture

The platform has three data layers:
1. **Reference Data** — static tables embedded in service files (emission factors, sector benchmarks, framework mappings)
2. **Seeded/Synthetic Data** — deterministic `seededRand()` in frontend JSX for UI display
3. **Live DB Data** — real PostgreSQL records from user-submitted or ingested data

**Critical Finding:** The vast majority of analytics outputs depend on Layer 1 (reference data in Python services). Layer 3 (live DB) is populated only for portfolios and a subset of CSRD entities. Layer 2 (seeded) makes the UI appear functional even when Layer 3 is empty.

---

## Sector: Finance (Banking / Asset Management / PE / Insurance)

### What Reference Data Exists

| Data Type | Source in Code | Coverage | Quality |
|-----------|---------------|----------|---------|
| Sector avg PD, LGD, Scope 1/2/3 intensity | `portfolio_analytics_engine_v2.py` SECTOR_REFERENCE_DATA | 10 GICS sectors | Estimated, not calibrated to actual portfolio |
| Country sovereign spreads | `portfolio_analytics_engine_v2.py` COUNTRY_REFERENCE_DATA | 8 countries | Minimal — US, UK, DE, FR, JP, CN, BR, IN only |
| NGFS Phase IV scenario multipliers | `sovereign_climate_risk_engine.py` | 5 scenarios, 2 time horizons (2030/2050) | Hardcoded multipliers, not NGFS Phase V |
| Basel III/IV RWA weights | `banking_risk_engine.py`, `basel_capital_engine.py` | Pillar 1 SA and IRB | Accurate regulatory reference |
| IFRS 9 ECL staging rules | `ecl_climate_engine.py` | Stage 1/2/3 | Accurate per IFRS 9 §5.5 |
| PCAF attribution fractions | `facilitated_emissions_engine.py` | All deal types in Parts B & C | Accurate per PCAF v2.0 |
| S&P rating scale (22 points) | `sovereign_climate_risk_engine.py` | Full scale | Accurate |

### What Is Ingested from External Sources

| Source | Status | Route to Production |
|--------|--------|---------------------|
| GLEIF LEI Registry | Not live — listed in FALLBACK_INGESTERS | WORK_PLAN A3 (not built) |
| SEC EDGAR XBRL | Not live — FALLBACK shows "running" | WORK_PLAN A8 (not built) |
| yfinance EVIC data | Not live | WORK_PLAN A9 (not built) |
| NGFS Scenarios Portal | Not live | WORK_PLAN A6 (not built) |
| SBTi Target Registry | Not live | WORK_PLAN A14 (not built) |

### What Is Synthetic/Seeded

| Component | Evidence | Impact |
|-----------|----------|--------|
| GAR/ETS dashboard KPIs | `GarEtsPage.jsx` line 30: `seededRand(seed)` for all chart data | Investment Lead sees fabricated GAR numbers |
| Portfolio Analytics charts | `InteractiveDashboard.jsx` — seed-based data generation described in MEMORY.md | Critical — all portfolio risk metrics are synthetic |
| Data Ingestion status | `DataHubIngestionPage.jsx` FALLBACK_INGESTERS (lines 35-48) | Platform data health dashboard is fake |
| Project Finance KPIs | `ProjectFinancePage.jsx` seededRand for all tabs | DSCR/IRR outputs are illustrative only |
| Energy Finance | `EnergyFinancePage` | All renewable energy cost/revenue data seeded |

### Critically Missing Data

| Gap | DQS Impact | Personas Most Impacted |
|-----|-----------|----------------------|
| No live EVIC data (company valuations) | PCAF DQS 4-5 (worst tier) for financed emissions | Analytics Lead, Investment Lead |
| No actual loan book data from DB | ECL calculations use aggregate parameters only | Analytics Lead (Banking) |
| No live carbon price data | Transition risk calculations use fixed price paths | All personas, Energy sector |
| Country reference data covers only 8 countries | Sovereign risk, PCAF country factor limited | Analytics Lead, Investment Lead |
| No FX rate data | Multi-currency portfolio analytics impossible | Investment Lead |

---

## Sector: Energy (Utilities, Renewables, O&G)

### What Reference Data Exists

| Data Type | Source in Code | Coverage | Quality |
|-----------|---------------|----------|---------|
| NGFS carbon price paths | `ngfs_v2.py`, `scenario_analysis_engine.py` | 5 scenarios to 2100 | NGFS Phase II; Phase V not confirmed |
| Grid emission factors | `grid_ef_trajectory.py` | Service exists | Live IEA data not ingested (WORK_PLAN A13 pending) |
| CRREM pathways | `crrem_stranding_engine.py` | Service exists | Live CRREM data not ingested (WORK_PLAN F5 pending) |
| IRENA LCOE data | Referenced in FALLBACK_INGESTERS | Not live | WORK_PLAN A13 pending |
| EU ETS allocation benchmarks | `eu_ets_engine.py` | Service exists | Static benchmarks, no live ETS registry |
| Green hydrogen RFNBO criteria | `green_hydrogen_calculator.py` | EU RFNBO rules | Static; no live electrolyser cost data |

### What Is Missing Critically

| Gap | DQS Impact | Personas Most Impacted |
|-----|-----------|----------------------|
| No live ETS price data (EUA prices) | All ETS compliance cost calculations use modelled prices | Energy Analytics Lead, Investment Lead |
| No live power purchase agreement market data | PPA risk scoring uses fixed merchant price assumptions | Investment Lead |
| Grid emission factors not updated | Scope 2 market-based calculations may use stale EFs | Analytics Lead (Regulatory Lead for CSRD E1) |
| No gas price / commodity price data | Stranded asset calculations for O&G need market prices | Investment Lead |

---

## Sector: Supply Chain

### What Reference Data Exists

| Data Type | Source in Code | Coverage |
|-----------|---------------|----------|
| EUDR commodity list (7 commodities) | `eudr_engine.py` | 7 commodities, 63 HS codes |
| EUDR country risk tiers | `eudr_engine.py` | 55 countries across 3 tiers |
| GHG Protocol Scope 3 category emission factors | `supply_chain_scope3_engine.py` | 15 categories |
| NACE to CPRS sector mapping | `nace_cprs_mapper.py` | Full NACE Rev 2 |
| CSDDD high-risk sectors | `csddd_engine.py` | 8 sectors with NACE codes |

### What Is Missing Critically

| Gap | DQS Impact | Personas Most Impacted |
|-----|-----------|----------------------|
| No live GFW deforestation alerts | EUDR traceability relies on static polygon validation only | Sustainability Regulatory Lead |
| No live Violation Tracker data | FALLBACK_INGESTERS shows `last_status: 'failed'` | Sustainability Regulatory Lead, Analytics Lead |
| Ecoinvent/DEFRA emission factor vintage unknown | Supply chain Scope 3 accuracy unverifiable | Analytics Lead |
| No supplier financial data integration | Supply chain financing ESG screening has no live data | Investment Lead |

---

## Sector: Manufacturing

### What Reference Data Exists

| Data Type | Source in Code | Coverage |
|-----------|---------------|----------|
| CBAM product categories + default values | `cbam_calculator.py` | Articles 7/21/31 products |
| IPCC AR5/AR6 GWP values | `carbon_calculator_v2.py` | CO2, CH4, N2O, F-gases |
| DEFRA emission conversion factors | Referenced in MODULE_SIGNATURES | Not confirmed as live updated |
| Steel production emission benchmarks | `steel_calculator.py` | Exists |
| Mining risk parameters | `mining_risk_calculator.py` | Exists |

### What Is Missing Critically

| Gap | DQS Impact | Personas Most Impacted |
|-----|-----------|----------------------|
| No live CBAM carbon price data for certificate pricing | CBAM cost calculations are based on EU ETS modelled price | Analytics Lead, Regulatory Lead |
| No Eurostat industrial production data | Sector benchmarks use internal estimates | Analytics Lead |
| IPCC AR6 WG2 regional damage functions | Physical risk to industrial assets uses simplified scoring | Analytics Lead |
| No CDM/VCS registry API | Carbon credit methodology validation cannot check current registry status | Analytics Lead |

---

## DQS Summary Table

| Module | Typical DQS Tier | Reason |
|--------|-----------------|--------|
| Carbon Calculator (with activity data) | DQS 2-3 | Uses DEFRA/IEA EFs; no direct measurement |
| PCAF Financed Emissions (with EVIC) | DQS 3 | EVIC from yfinance (not live); emissions estimated |
| PCAF Financed Emissions (without EVIC) | DQS 4-5 | Falls back to sector averages |
| ECL Climate (with real loan data) | DQS 2 | IFRS 9 compliant calculation |
| ECL Climate (without loan data) | DQS 4 | Uses aggregate sector parameters |
| Portfolio Analytics (live DB) | DQS 2 | When data is present |
| Portfolio Analytics (empty DB) | DQS 5 | Falls back to zeros / sector reference data |
| Nature Risk | DQS 4 | Float lat/lng, no PostGIS, no live WDPA |
| EU ETS compliance | DQS 4 | No live ETS registry connection |
| EUDR compliance | DQS 3 | Static country tiers; no live GFW |

---

## Platform-Wide Data Quality Risks

1. **DQS inflation risk** — the platform reports DQS scores computed within each engine, but without live external data validation, these scores cannot be independently verified. A PCAF auditor would reject DQS 2 if EVIC comes from a non-live source.

2. **Stale reference data risk** — NGFS Phase II scenarios are referenced in `ngfs_seeder.py` but NGFS Phase V was released. If the seeder uses old data, all scenario-linked outputs are materially misstated.

3. **Synthetic UI data misleads users** — `seededRand()` throughout the frontend creates a plausible-looking UI that does not reflect real data. An Investment Lead shown the portfolio dashboard will believe the KPIs are real.

4. **No data freshness metadata** — no UI indicator of "data last updated on [date]" for any reference data set. Users cannot assess how stale the calculation basis is.

5. **No cross-module data lineage visibility in the UI** — the `data_lineage.py` service tracks this server-side, but the `PlatformIntelligencePage` is the only frontend surface, and it is not prominently linked from any calculation result.
