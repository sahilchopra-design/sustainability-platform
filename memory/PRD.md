# Climate Credit Risk Intelligence Platform - PRD

## Original Problem Statement
A comprehensive portfolio analysis and scenario building application for climate risk assessment. The platform enables risk analysts to analyze credit portfolios against NGFS climate scenarios, create custom scenarios, and run impact analyses.

## User Personas
- **Bank Risk Analysts**: Primary users who need to assess climate risk impact on credit portfolios
- **Portfolio Managers**: Users managing asset allocations and risk exposures
- **Asset Managers**: Users responsible for investment decisions based on climate risk

## Core Architecture

### Backend (FastAPI)
- **Database**: Dual database setup
  - MongoDB (Beanie ODM): Portfolios, Assets, Analysis Runs, Scenario Series
  - PostgreSQL (SQLAlchemy): Scenarios, Scenario Versions, Data Hub (19 sources, 99 scenarios, 875 trajectories)
- **Location**: `/app/backend/`
- **Real Data Integration**: IIASA Scenario Explorer via `pyam-iamc` library for NGFS, IPCC AR6, IAMC 1.5C

### Frontend (React + shadcn/ui)
- **Location**: `/app/frontend/`
- **Key Pages**: Dashboard, Portfolios, Analysis, Scenario Builder, **Data Hub**

---

## What's Been Implemented

### Completed (Feb 14, 2026)

#### Universal Scenario Data Hub — Full Expansion (P0)
**19 sources across 6 tiers — 99 scenarios — 875 trajectories — 62 variables — 13 regions**

Backend:
- Extended PostgreSQL models with: display_name, carbon_neutral_year, variable_code, sector, data_quality_score, interpolation_method, sync_type
- 3 REAL DATA fetchers (IIASA pyam): NGFS Phase V (27 scenarios), IPCC AR6 (8), IAMC 1.5C (10)
- 16 Synthetic fetchers: IEA, IRENA, REMIND, GCAM, MESSAGEix, IMAGE, WITCH, TIAM, EU Ref, UK CCC, US EIA, China, Japan, IEA Sectors, Carbon Pricing, Physical Risk
- Analytics endpoints: /analytics/coverage, /analytics/temperature-range, /analytics/carbon-price-range, /trajectories/available-variables
- 25+ API endpoints at `/api/v1/data-hub/*`

Frontend:
- DataHub page with Browse, Data Sources (grouped by tier), Analytics, Sync History tabs
- Source filter pills with tier badges (T1-T6)
- "REAL DATA" badge on IIASA-sourced scenarios
- Analytics tab: Temperature distribution chart, Scenarios by Tier pie, Category breakdown bar
- Scenario detail: Data quality indicator, net zero year, expanded metadata
- TrajectoryViewer with Chart+Table toggle, variable/region selectors

Testing: 24/24 backend + all frontend = 100% (iteration_5)

#### Scenario Builder (P0) — Previously completed
#### Portfolio Analysis Dashboard (P0) — Previously completed

---

## Prioritized Backlog

### P1 - High Priority
1. Portfolio File Upload System
2. Portfolio Editor
3. Scenario Comparison Builder (select 2-3 scenarios, overlay trajectories)

### P2 - Medium Priority
1. Live API for remaining sources (when APIs become available)
2. User authentication/authorization
3. Report generation (PDF/Excel export)
4. Database unification (MongoDB to PostgreSQL)

### P3 - Future
1. Scheduled sync jobs
2. Redis caching for trajectories
3. Data quality scoring improvements
4. Additional regional sources (ASEAN, Latin America)

---

## Key Files

### Data Hub
- `/app/backend/db/models/data_hub.py` — 6 SQLAlchemy models
- `/app/backend/schemas/data_hub.py` — Pydantic schemas
- `/app/backend/api/v1/routes/data_hub.py` — API routes
- `/app/backend/services/data_hub_service.py` — CRUD + analytics service
- `/app/backend/services/sync_orchestrator.py` — 19-source orchestrator
- `/app/backend/services/scenario_fetchers/fetchers.py` — All fetchers (real + synthetic)
- `/app/frontend/src/pages/DataHub.js` — Main page (browse + analytics)
- `/app/frontend/src/components/data-hub/TrajectoryViewer.js` — Chart component
- `/app/frontend/src/store/dataHubStore.js` — Zustand store

---

## Testing
- `/app/test_reports/iteration_5.json` — Expanded Data Hub (24/24 backend, all frontend)
- `/app/test_reports/iteration_4.json` — Initial Data Hub (19/19 backend)
- `/app/test_reports/iteration_3.json` — Dashboard
- `/app/test_reports/iteration_2.json` — Scenario Builder

## Tech Stack
- Backend: FastAPI, SQLAlchemy, Pydantic, pyam-iamc (IIASA data)
- Frontend: React, Recharts, Zustand, shadcn/ui, TanStack Table
- DB: PostgreSQL (Supabase), MongoDB (legacy)
