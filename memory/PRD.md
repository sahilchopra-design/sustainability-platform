# Climate Credit Risk Intelligence Platform - PRD

## Original Problem Statement
A comprehensive portfolio analysis and scenario building application for climate risk assessment. The platform enables risk analysts to analyze credit portfolios against NGFS climate scenarios, create custom scenarios, and run impact analyses.

## User Personas
- **Bank Risk Analysts**: Primary users who need to assess climate risk impact on credit portfolios
- **Portfolio Managers**: Users managing asset allocations and risk exposures
- **Asset Managers**: Users responsible for investment decisions based on climate risk

## Core Architecture

### Backend (FastAPI + PostgreSQL/MongoDB)
- Real Data Integration: IIASA Scenario Explorer via `pyam-iamc` for NGFS, IPCC AR6, IAMC 1.5C
- 19 data sources, 99 scenarios, 875 trajectories, 62 variables, 13 regions

### Frontend (React + shadcn/ui + Recharts + Zustand)
- **Pages**: Dashboard, Portfolios, Analysis, Scenario Builder, Data Hub, **Scenario Browser**, Comparison

---

## What's Been Implemented

### Completed (Feb 14, 2026) — Latest

#### Scenario Browser UI (P0)
Professional financial-grade scenario browser with:
- **Sidebar Filters**: Temperature slider (1-5°C), source checkboxes grouped by 6 tiers, category multi-select
- **Grid/List Views**: Toggle between card grid (4 cols) and compact list
- **Detail Drawer**: Right-side slide-out with full metadata, trajectory chart preview, favorite/compare/check buttons, tags, regions
- **Compare Workspace**: Add scenarios from cards, variable/region selectors, overlay charts with statistics
- **Favorites**: Star scenarios, view in dedicated tab
- **Analytics Dashboard**: Temperature distribution, tier pie chart, category breakdown, stat cards
- **Filter Chips**: Active filters displayed as removable badges
- **Search**: Sidebar search with real-time results
- **Sort**: Name, Temperature, Data Size

Components: ScenarioBrowserPage, FilterSidebar, ScenarioCard (grid+list), ScenarioDetailDrawer, CompareWorkspace
Store: scenarioBrowserStore (Zustand)
Route: `/browser`

Testing: 15/15 features passed (iteration_7)

#### Scenario Comparison & Analysis Engine (P0)
- Multi-scenario comparison with diff calculations and statistics
- Gap analysis (policy/ambition/implementation)
- Consistency checks (carbon budget, energy balance, tech deployment, economic feasibility)
Route: `/comparison`
Testing: 18/18 backend + all frontend passed (iteration_6)

#### Universal Scenario Data Hub (P0)
- 19 sources, 6 tiers, 3 real IIASA + 16 synthetic
Route: `/data-hub`
Testing: 24/24 backend passed (iteration_5)

#### Scenario Builder (P0) + Portfolio Analysis Dashboard (P0) — Previously completed

---

## Prioritized Backlog

### P1 - High Priority
1. Scenario Impact Calculator (connect scenarios to portfolios for PD/LGD/EL)
2. Portfolio File Upload System
3. Portfolio Editor

### P2 - Medium Priority
1. Custom Scenario Builder (blend trajectories)
2. Alert System UI
3. User authentication
4. Report generation

### P3 - Future
1. Live APIs for remaining sources
2. Scheduled sync jobs, Redis caching

---

## Key Files

### Scenario Browser
- `/app/frontend/src/pages/ScenarioBrowserPage.js`
- `/app/frontend/src/store/scenarioBrowserStore.js`
- `/app/frontend/src/components/scenario-browser/ScenarioCard.js`
- `/app/frontend/src/components/scenario-browser/FilterSidebar.js`
- `/app/frontend/src/components/scenario-browser/ScenarioDetailDrawer.js`
- `/app/frontend/src/components/scenario-browser/CompareWorkspace.js`

### Comparison & Analysis
- `/app/backend/api/v1/routes/analysis.py`
- `/app/backend/services/scenario_comparison_service.py`
- `/app/frontend/src/pages/ComparisonPage.js`

### Data Hub
- `/app/backend/api/v1/routes/data_hub.py`
- `/app/backend/services/data_hub_service.py`
- `/app/frontend/src/pages/DataHub.js`

---

## Testing
- iteration_7: Scenario Browser (15/15 frontend)
- iteration_6: Comparison & Analysis (18/18 backend, all frontend)
- iteration_5: Expanded Data Hub (24/24 backend)

## Tech Stack
- Backend: FastAPI, SQLAlchemy, Pydantic, pyam-iamc
- Frontend: React, Recharts, Zustand, shadcn/ui, TanStack Table
- DB: PostgreSQL (Supabase), MongoDB (legacy)
