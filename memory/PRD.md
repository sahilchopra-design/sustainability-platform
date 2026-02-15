# A2 Intelligence by AA Impact Inc.

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) — unified single DB
- Frontend: React + shadcn/ui + Recharts + Zustand + **Redux Toolkit**
- Auth: Google OAuth + JWT — PostgreSQL
- Data: IIASA (real) + 20 sources + 24 NGFS + CBAM + **Carbon Credits**
- Maps: Mapbox GL

## Pages (17 routes)
| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/impact` | Impact Calculator + Reports |
| `/sub-analysis` | Sub-Parameter Analysis (7 methods) |
| `/cbam` | CBAM Module |
| `/carbon` | **Carbon Credits Module (NEW)** |
| `/browser` | Scenario Browser |
| `/data-hub` | Data Hub (20 sources) |
| `/ngfs` | NGFS Catalog (24 scenarios) |
| `/comparison` | Comparison & Gap Analysis |
| `/custom-builder` | Custom Builder |
| `/portfolios` | Portfolios |
| `/portfolio-manager` | Upload & Edit |
| `/analysis` | Run Analysis |
| `/alerts` | Alerts |

## Latest: Carbon Credits Module (Dec 2025)
- 7 PostgreSQL tables: CarbonMethodology, CarbonEmissionFactor, CarbonPortfolio, CarbonProject, CarbonScenario, CarbonCalculation, CarbonReport
- Full CRUD API for portfolios, projects, scenarios
- Calculation engine with risk-adjusted credits, NPV, Monte Carlo simulation
- Dashboard with 4 KPI cards, credits projection chart, risk heat map
- Interactive Mapbox map showing global project distribution
- Scenario builder with risk sliders (permanence, delivery, regulatory, market)
- 6 seeded methodologies (VCS, Gold Standard, CDM standards)
- 8 country emission factors (US, CN, IN, DE, BR, GB, JP, AU)
- Redux Toolkit state management for complex scenario state
- Testing: 32/32 BE + all FE verified (iteration_16)

## Previous: CBAM Module
- 8 PostgreSQL tables for product categories, suppliers, emissions, projections, compliance, country risk, certificate prices, verifiers
- 15 EU CBAM product categories (Cement, Iron & Steel, Aluminium, Fertilizers, Electricity, Hydrogen) with default emission factors
- 20 country risk profiles with carbon pricing data
- Cost projection engine: EU ETS price × emissions - domestic credit - free allocation
- 3 ETS price scenarios (Current Trend, Ambitious, Conservative) with 2025-2050 projections
- Free allocation phase-out schedule (97.5% in 2026 → 0% in 2034)
- Testing: 34/34 BE + all FE (iteration_15)

## All Tests (16 iterations, 340+ tests, 100% pass)
