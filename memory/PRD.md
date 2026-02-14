# Climate Credit Risk Intelligence Platform - PRD

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) + MongoDB
- Frontend: React + shadcn/ui + Recharts + Zustand
- Auth: Google OAuth (Emergent) + JWT email/password
- Real Data: IIASA Scenario Explorer (pyam-iamc) + NGFS catalog

## Pages (12 routes, all auth-gated)
| Route | Page | Tests |
|-------|------|-------|
| `/` | Dashboard | Done |
| `/portfolios` | Portfolios | Done |
| `/analysis` | Run Analysis | Done |
| `/scenario-data` | Scenario Data | Done |
| `/scenario-builder` | Scenario Builder | Done |
| `/data-hub` | Data Hub (19 sources) | 24/24 BE |
| `/browser` | Scenario Browser | 15/15 FE |
| `/comparison` | Comparison & Gap Analysis | 18/18 BE |
| `/impact` | Impact Calculator + Reports | 11/11 BE |
| `/portfolio-manager` | Portfolio Upload + Editor | 15/15 BE |
| `/alerts` | Scenario Alerts | Done |
| `/ngfs` | **NGFS Scenario Catalog (24 scenarios)** | **29/29 BE** |

## Latest Feature: NGFS Scenario Module (Feb 14, 2026)
- All 24 NGFS scenarios across 3 phases (2020: 6, 2021: 10, 2023: 8)
- Dedicated PostgreSQL tables: ngfs_scenarios_v2, ngfs_scenario_parameters, ngfs_scenario_timeseries
- 4 parameters per scenario (carbon_price, emissions, temperature, gdp_impact) with 76-year interpolated time series
- Full API: list, filter, search, phase summary, temperature ranges, detail, parameters, time-series, compare
- Frontend: 3-column card grid, phase/search filters, detail drawer with parameter charts, multi-scenario comparison
- Standard response format: {data: ..., meta: {total_scenarios, phase_count, temperature_range, version}}

## All Testing
- iteration_11: NGFS Module (29/29 BE, all FE)
- iteration_10: Authentication (12/12 BE, 7/7 FE)
- iteration_9: Reports (11/11 BE, 6/6 FE)
- iteration_8: Impact+Upload (15/15 BE, 12/12 FE)
- iteration_7: Browser (15/15 FE)
- iteration_6: Comparison (18/18 BE)
- iteration_5: Data Hub (24/24 BE)

## Backlog
- Database unification (MongoDB → PostgreSQL)
- Live APIs for remaining synthetic sources
- Scheduled sync, Redis caching
- Role-based access control
