# Phase 5 — Energy Sector Completions

## Overview

Phase 5 delivers six new analytical engines covering the full energy transition lifecycle: renewable project finance, PPA risk, generation fleet transition, grid decarbonisation trajectories, methane monitoring, downstream emissions (Scope 3 Cat 11), and CSRD auto-population from module outputs.

**Test Results**: 141/141 passed (59 + 42 + 40)

---

## Session 5A — Renewable Project Finance + PPA Risk

### Services
- `services/renewable_project_engine.py` — Wind/solar yield (P50/P75/P90), LCOE, project finance (IRR/NPV)
- `services/ppa_risk_scorer.py` — 5-dimension PPA risk scoring with bankability rating

### API: `/api/v1/renewable-ppa/`

| Endpoint | Method | Description |
|---|---|---|
| `/wind-yield` | POST | Wind energy yield with Weibull distribution |
| `/solar-yield` | POST | Solar energy yield with GHI model |
| `/lcoe` | POST | Levelised Cost of Energy |
| `/project-assess` | POST | Full project finance (IRR/NPV/LCOE) |
| `/ppa-risk` | POST | PPA risk scoring (5 dimensions) |
| `/ref/turbine-classes` | GET | 5 turbine class definitions |
| `/ref/wind-regions` | GET | 15 wind resource regions (Weibull k/lambda) |
| `/ref/solar-ghi` | GET | 20 countries solar irradiance data |
| `/ref/solar-defaults` | GET | Solar system default parameters |
| `/ref/credit-ratings` | GET | 12 counterparty credit tiers |
| `/ref/price-structures` | GET | 9 PPA price structure risk scores |
| `/ref/ppa-risk-weights` | GET | Risk dimension weights |
| `/ref/curtailment-risk` | GET | 4 curtailment risk levels |
| `/ref/regulatory-risk` | GET | 4 regulatory risk levels |

### User Stories

#### US-5.1: Renewable Energy Project Developer
**Persona**: Project Finance Analyst at a wind/solar developer

**Input**: Turbine class, wind region (or country + capacity for solar), PPA price, carbon price, WACC, capex/opex overrides

**Reference Data**: 5 turbine classes (onshore 2/4 MW, offshore 5/8/12 MW), 15 Weibull wind regions, 20 country GHI values, solar performance defaults

**Output**: P50/P75/P90 generation (MWh), capacity factor, LCOE (EUR/MWh), project IRR/NPV (with/without carbon revenue), payback years, lifetime CO2 avoided

**Insights**: Which regions offer best risk-adjusted returns; carbon revenue uplift quantification; LCOE competitiveness vs grid price

#### US-5.2: PPA Structurer / Risk Manager
**Persona**: Energy trading desk analyst assessing offtake agreements

**Input**: Offtaker credit rating, price structure, tenor, curtailment zone, regulatory jurisdiction, merchant exposure %, subsidy dependence %

**Reference Data**: 12 credit rating tiers, 9 price structures, tenor risk bands, curtailment/regulatory risk levels, dimension weights

**Output**: 5-dimension risk scores (counterparty credit, price structure, tenor, curtailment, regulatory), composite score (0-100), risk band, bankability rating, risk factors, mitigation suggestions

**Insights**: Which PPAs are bankable; key risk drivers; recommended risk mitigants; merchant exposure impact quantification

---

## Session 5B — Generation Transition + Grid EF Trajectory

### Services
- `services/generation_transition.py` — Coal-to-clean fleet transition planner
- `services/grid_ef_trajectory.py` — Grid emission factor projections (IEA NZE / NGFS scenarios)

### API: `/api/v1/energy-transition/`

| Endpoint | Method | Description |
|---|---|---|
| `/fleet-transition` | POST | Fleet coal-to-clean transition plan |
| `/grid-ef-projection` | POST | Grid EF trajectory by country/scenario |
| `/avoided-emissions` | POST | Avoided emissions from renewable project |
| `/country-comparison` | POST | Compare grid EFs across countries |
| `/ref/fuel-types` | GET | 14 fuel type emission factors + costs |
| `/ref/nze-milestones` | GET | IEA NZE power sector milestones |
| `/ref/replacement-options` | GET | Technology replacement priority list |
| `/ref/grid-ef-countries` | GET | 25 countries baseline grid EF |
| `/ref/grid-ef-scenarios` | GET | 6 decarbonisation scenarios |

### User Stories

#### US-5.3: Generation Fleet Transition Planner
**Persona**: Head of Strategy at a utility or energy company

**Input**: Fleet of plants (fuel type, capacity MW, commissioning year, book value, planned retirement), target year, replacement technology preference, carbon price

**Reference Data**: 14 fuel types with emission factors/capex/opex, IEA NZE milestones, decommissioning costs per MW, replacement technology priority list

**Output**: Year-by-year retirement schedule (dirtiest first), stranded book value, decommissioning costs, replacement capex, emissions trajectory vs NZE target, NZE alignment assessment

**Insights**: Total transition cost; stranded asset exposure; NZE gap quantification; optimal retirement sequencing; replacement technology selection

#### US-5.4: Climate Risk Analyst (Grid Decarbonisation)
**Persona**: Portfolio analyst assessing location-based Scope 2 and avoided emissions

**Input**: Country, scenario (Current Policies / STEPS / NZE / NGFS variants), project generation MWh, lifetime years

**Reference Data**: 25 countries baseline grid EF (2023), 6 scenario reduction pathways (target factors for 2030/2050)

**Output**: Year-by-year grid EF trajectory, EF values at 2030/2040/2050, total reduction %, avoided emissions over project lifetime, multi-country comparison (cleanest/dirtiest/fastest decarboniser)

**Insights**: Which countries decarbonise fastest; avoided emissions sensitivity to scenario choice; location-based vs market-based Scope 2 implications

---

## Session 5C — Methane OGMP + Scope 3 Cat 11 + CSRD Auto-Population

### Services
- `services/methane_ogmp.py` — Oil & gas methane monitoring (OGMP 2.0 / EU Methane Regulation)
- `services/scope3_cat11.py` — Scope 3 Category 11 (Use of Sold Products)
- `services/csrd_auto_populate.py` — ESRS data point auto-population from platform modules

### API: `/api/v1/energy-emissions/`

| Endpoint | Method | Description |
|---|---|---|
| `/methane-facility` | POST | Facility methane assessment (OGMP 2.0) |
| `/scope3-cat11` | POST | Scope 3 Category 11 assessment |
| `/csrd-auto-populate` | POST | Auto-populate ESRS data points |
| `/ref/methane-source-categories` | GET | 10 methane source categories |
| `/ref/ogmp-levels` | GET | 5 OGMP 2.0 reporting levels |
| `/ref/abatement-measures` | GET | 6 methane abatement measures |
| `/ref/fuel-combustion-efs` | GET | 10 fuel combustion EFs |
| `/ref/product-use-profiles` | GET | 8 energy-using product profiles |
| `/ref/esrs-mappings` | GET | 14 ESRS data point mappings |
| `/ref/esrs-minimums` | GET | Required DPs per ESRS standard |

### User Stories

#### US-5.5: Upstream O&G Methane Reporting Analyst
**Persona**: ESG/EHS analyst at an oil & gas company reporting under OGMP 2.0

**Input**: Facility sources (category, OGMP level, activity BCM/yr, measured tCH4/yr), production volume

**Reference Data**: 10 source categories with typical EFs and abatement potential, 5 OGMP levels, 6 abatement measures with cost per tCH4, GWP-100/GWP-20 conversion factors

**Output**: Per-source emissions (tCH4, tCO2e GWP-100, tCO2e GWP-20), facility totals, methane intensity (tCH4/BCM), weighted OGMP level, EU Methane Regulation compliance flag, prioritised reduction pathway (sorted by cost-effectiveness)

**Insights**: Cheapest abatement opportunities; EU compliance gaps; GWP-20 vs GWP-100 disclosure impact; OGMP level upgrade roadmap

#### US-5.6: Product Carbon Footprint Analyst (Scope 3 Cat 11)
**Persona**: Sustainability analyst at a manufacturer or energy company

**Input**: Fuel sales volumes by type, product sales by type, grid EF for electricity-using products, revenue

**Reference Data**: 10 fuel combustion EFs, 8 product use profiles (lifetime years, annual energy/fuel consumption), GHG Protocol Category 11 methodology

**Output**: Per-fuel emissions, per-product lifetime emissions, total Category 11 tCO2, top contributor, emissions intensity per EUR M revenue

**Insights**: ICE vs BEV emissions comparison; grid cleanliness impact on EV footprint; fuel vs product split; revenue intensity benchmarking

#### US-5.7: CSRD Reporting Lead (Auto-Population)
**Persona**: Head of Sustainability Reporting preparing ESRS disclosures

**Input**: Module outputs (key-value pairs from carbon calculator, climate risk, PCAF, nature risk engines)

**Reference Data**: 14 ESRS data point mappings (E1-E5 + financed emissions), required minimum DPs per standard

**Output**: Populated data points with confidence level, population rate %, gap list with missing module/field, ESRS-level coverage breakdown, readiness rating (high/medium/low)

**Insights**: Which ESRS standards have coverage gaps; which modules need to be run; reporting readiness score; data lineage from calculation to disclosure

---

## Technical Summary

### Files Created (Phase 5)

| Category | File | Lines | Description |
|---|---|---|---|
| Service | `services/renewable_project_engine.py` | ~550 | Wind/solar yield + LCOE + project finance |
| Service | `services/ppa_risk_scorer.py` | ~240 | PPA 5-dimension risk scoring |
| Service | `services/generation_transition.py` | ~280 | Fleet transition planning |
| Service | `services/grid_ef_trajectory.py` | ~270 | Grid EF trajectories |
| Service | `services/methane_ogmp.py` | ~290 | OGMP 2.0 methane monitoring |
| Service | `services/scope3_cat11.py` | ~280 | Scope 3 Cat 11 calculator |
| Service | `services/csrd_auto_populate.py` | ~250 | CSRD/ESRS auto-population |
| Route | `api/v1/routes/renewable_ppa.py` | ~280 | 14 endpoints |
| Route | `api/v1/routes/energy_transition.py` | ~230 | 9 endpoints |
| Route | `api/v1/routes/energy_emissions.py` | ~260 | 10 endpoints |
| Test | `tests/test_renewable_ppa.py` | ~310 | 59 tests |
| Test | `tests/test_energy_transition.py` | ~230 | 42 tests |
| Test | `tests/test_energy_emissions.py` | ~310 | 40 tests |

### Reference Data Coverage

| Dataset | Items | Source |
|---|---|---|
| Turbine classes | 5 | IEC 61400 / IRENA |
| Wind regions (Weibull) | 15 | DNV / IEA |
| Solar GHI countries | 20 | IRENA / Ember |
| PPA credit ratings | 12 | EFET / S&P |
| PPA price structures | 9 | Pexapark / IRENA |
| Fuel emission factors | 14 | IEA / GHG Protocol |
| IEA NZE milestones | 5 | IEA NZE 2050 |
| Grid EF countries | 25 | Ember / IEA WEO |
| Grid EF scenarios | 6 | IEA / NGFS Phase IV |
| Methane source categories | 10 | OGMP 2.0 / EPA GHGRP |
| OGMP reporting levels | 5 | UNEP CCAC |
| Abatement measures | 6 | IEA / CCAC |
| Fuel combustion EFs | 10 | GHG Protocol |
| Product use profiles | 8 | GHG Protocol Product Standard |
| ESRS data point mappings | 14 | EFRAG IG3 |

### Total Endpoints: 33 (14 + 9 + 10)
### Total Tests: 141 (59 + 42 + 40)
