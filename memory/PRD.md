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
  - PostgreSQL (SQLAlchemy): Scenarios, Scenario Versions, Impact Previews, NGFS Sources, Data Hub
- **Location**: `/app/backend/`
- **Key Services**:
  - `services/ngfs_sync_service.py` - NGFS data synchronization
  - `services/scenario_builder_service.py` - Scenario CRUD & versioning
  - `services/scenario_impact_service.py` - Impact calculations
  - `services/calculation_engine.py` - Risk calculations
  - `services/data_hub_service.py` - Data Hub CRUD
  - `services/sync_orchestrator.py` - Multi-source sync orchestrator
  - `services/scenario_fetchers/fetchers.py` - Tier 1 data fetchers

### Frontend (React + shadcn/ui)
- **Location**: `/app/frontend/`
- **Key Pages**:
  - Dashboard, Portfolios, Portfolio Detail
  - Run Analysis, Results
  - Scenario Data, Scenario Builder
  - **Data Hub** (NEW)

---

## What's Been Implemented

### Completed (Feb 14, 2026)

#### Universal Scenario Data Hub (P0) - Full Stack
Backend:
- 6 new PostgreSQL tables: `hub_sources`, `hub_scenarios`, `hub_trajectories`, `hub_comparisons`, `hub_sync_logs`, `hub_favorites`
- Full REST API at `/api/v1/data-hub/*` with 20+ endpoints
- Tier 1 data fetchers for NGFS (6 scenarios), IPCC (5), IEA (3), IRENA (2) = 16 scenarios, 342 trajectories
- Sync orchestrator with seed/sync-all/sync-per-source
- Scenario search, comparison save/delete, favorites

Frontend:
- `DataHub.js` page with stats cards, source/category filters, scenario browser
- `TrajectoryViewer.js` with multi-line chart (Recharts), variable/region selectors, Chart+Table toggle
- `dataHubStore.js` Zustand store
- Navigation integrated in sidebar

Testing: 19/19 backend tests passed, all frontend UI tests passed (iteration_4)

**Note: Data fetchers use SYNTHETIC data. Not connected to live NGFS/IPCC/IEA/IRENA APIs.**

#### Portfolio Scenario Analysis Dashboard Components (P0)
All 9 components created, integrated, and tested.

#### Scenario Builder Backend & Frontend (P0)
- NGFS Integration, Scenario CRUD, Versioning, Approval Workflow

---

## Prioritized Backlog

### P1 - High Priority
1. **Portfolio File Upload System** - FileUploadZone, Column mapping wizard, Validation results panel
2. **Portfolio Editor** - Holdings manager with CRUD, Bulk edit toolbar, Change history log
3. **Populate Company Country Data** - Geography breakdown shows "Unknown"

### P2 - Medium Priority
1. Core v1 API Routes (portfolios, counterparties full CRUD with PostgreSQL)
2. Data export functionality enhancements
3. User authentication/authorization
4. Data Hub Tier 2-6 fetchers (World Bank, IMF, OECD, etc.)

### P3 - Future
1. Live NGFS/IPCC/IEA/IRENA API integration (replace synthetic fetchers)
2. Enhanced visualization (trajectory comparison across sources)
3. Report generation (actual PDF/Excel export)
4. Scheduled sync jobs
5. Database Unification (migrate MongoDB to PostgreSQL)

---

## Key Files Reference

### Data Hub
- `/app/backend/db/models/data_hub.py` - 6 SQLAlchemy models
- `/app/backend/schemas/data_hub.py` - Pydantic schemas
- `/app/backend/api/v1/routes/data_hub.py` - API routes
- `/app/backend/services/data_hub_service.py` - CRUD service
- `/app/backend/services/sync_orchestrator.py` - Sync orchestrator
- `/app/backend/services/scenario_fetchers/fetchers.py` - 4 Tier 1 fetchers
- `/app/frontend/src/pages/DataHub.js` - Main page
- `/app/frontend/src/components/data-hub/TrajectoryViewer.js` - Chart component
- `/app/frontend/src/store/dataHubStore.js` - Zustand store

### Dashboard Components
- `/app/frontend/src/components/dashboard/` - All 9 components
- `/app/frontend/src/store/dashboardStore.js` - Zustand state management

### Backend
- `/app/backend/server.py` - Main FastAPI app
- `/app/backend/api/v1/routes/scenarios.py` - Scenario routes
- `/app/backend/services/` - Business logic services

---

## Testing
- `/app/test_reports/iteration_4.json` - Data Hub test (19/19 backend, all frontend pass)
- `/app/test_reports/iteration_3.json` - Dashboard components test
- `/app/test_reports/iteration_2.json` - Scenario Builder test

## Notes
- Dashboard uses Zustand for state management
- Charts use recharts library
- Table uses @tanstack/react-table
- Data Hub fetchers use synthetic data (MOCKED)
