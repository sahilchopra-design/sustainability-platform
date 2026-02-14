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
  - PostgreSQL (SQLAlchemy): Scenarios, Data Hub (19 sources, 99 scenarios, 875 trajectories), Comparisons, Gap Analysis, Consistency Checks
- **Real Data Integration**: IIASA Scenario Explorer via `pyam-iamc` for NGFS, IPCC AR6, IAMC 1.5C

### Frontend (React + shadcn/ui)
- **Key Pages**: Dashboard, Portfolios, Analysis, Scenario Builder, Data Hub, **Comparison**

---

## What's Been Implemented

### Completed (Feb 14, 2026) — Latest

#### Scenario Comparison & Analysis Engine (P0)
Backend:
- 3 new DB models: GapAnalysis, ConsistencyCheck, ScenarioAlert
- ScenarioComparisonService with full comparison data builder, diff calculations, statistics
- Gap analysis: policy/ambition/implementation gaps at 2030/2040/2050
- Consistency checks: carbon budget, energy balance, tech deployment, economic feasibility
- 12+ new API endpoints at `/api/v1/analysis/*`

Frontend:
- ComparisonPage (`/comparison`) with 4 tabs: Builder, Results, Gap Analysis, Consistency
- Scenario picker with search (99 scenarios), colored badges, BASE/compare labels
- Multi-line overlay charts with statistics (min, max, mean, spread%)
- Gap Analysis table grouped by type (policy/ambition/implementation)
- Consistency view with overall score, per-check cards with pass/warning/fail

Testing: 18/18 backend + all frontend = 100% (iteration_6)

#### Universal Scenario Data Hub (P0) — Previously completed
- 19 sources, 6 tiers, 99 scenarios, 875 trajectories, 62 variables, 13 regions
- 3 REAL DATA sources (IIASA): NGFS, IPCC AR6, IAMC15
- Analytics tab, tier badges, temperature distribution

#### Scenario Builder (P0) — Previously completed
#### Portfolio Analysis Dashboard (P0) — Previously completed

---

## Prioritized Backlog

### P1 - High Priority
1. Portfolio File Upload System
2. Portfolio Editor
3. Scenario Impact Calculator (connect scenarios to portfolios for PD/LGD/EL)
4. Custom Scenario Builder (blend trajectories from multiple sources)

### P2 - Medium Priority
1. Scenario Alert System (in-app notifications for updates)
2. User authentication
3. Report generation (PDF/Excel export)
4. Database unification (MongoDB to PostgreSQL)

### P3 - Future
1. Live APIs for remaining 16 synthetic sources
2. Scheduled sync jobs, Redis caching
3. Additional regional sources

---

## Key Files

### Comparison & Analysis
- `/app/backend/api/v1/routes/analysis.py` — API routes
- `/app/backend/services/scenario_comparison_service.py` — Service
- `/app/frontend/src/pages/ComparisonPage.js` — Frontend page
- `/app/frontend/src/store/comparisonStore.js` — Zustand store

### Data Hub
- `/app/backend/api/v1/routes/data_hub.py` — API routes
- `/app/backend/services/data_hub_service.py` — Service
- `/app/backend/services/scenario_fetchers/fetchers.py` — Fetchers
- `/app/frontend/src/pages/DataHub.js` — Frontend page

---

## Testing
- `/app/test_reports/iteration_6.json` — Comparison & Analysis (18/18 backend, all frontend)
- `/app/test_reports/iteration_5.json` — Expanded Data Hub (24/24 backend)
- `/app/test_reports/iteration_4.json` — Initial Data Hub (19/19 backend)

## Tech Stack
- Backend: FastAPI, SQLAlchemy, Pydantic, pyam-iamc
- Frontend: React, Recharts, Zustand, shadcn/ui, TanStack Table
- DB: PostgreSQL (Supabase), MongoDB (legacy)
