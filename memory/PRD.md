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
  - PostgreSQL (SQLAlchemy): Scenarios, Scenario Versions, Impact Previews, NGFS Sources
- **Location**: `/app/backend/`
- **Key Services**:
  - `services/ngfs_sync_service.py` - NGFS data synchronization
  - `services/scenario_builder_service.py` - Scenario CRUD & versioning
  - `services/scenario_impact_service.py` - Impact calculations
  - `services/calculation_engine.py` - Risk calculations

### Frontend (React + shadcn/ui)
- **Location**: `/app/frontend/`
- **Key Pages**:
  - Dashboard, Portfolios, Portfolio Detail
  - Run Analysis, Results
  - Scenario Data, Scenario Builder

---

## What's Been Implemented

### ✅ Completed (Feb 14, 2026)

#### Scenario Builder Backend (P0)
- **NGFS Integration**: 6 Phase V scenarios synced and stored
  - Net Zero 2050, Below 2°C, Delayed Transition
  - Current Policies, NDCs, Fragmented World
- **Scenario CRUD**: Create, Read, Update, Delete operations
- **Versioning**: Full version history with change tracking
- **Approval Workflow**: Draft → Pending → Approved/Rejected → Published
- **Impact Calculations**: Expected loss calculations with sectoral multipliers
- **API Endpoints** (all at `/api/v1/scenarios`):
  - `GET /` - List scenarios
  - `GET /templates` - Get NGFS templates
  - `GET /ngfs/sources` - Get data sources
  - `POST /ngfs/sources` - Create source
  - `POST /ngfs/sync` - Sync NGFS data
  - `POST /` - Create scenario
  - `GET /{id}` - Get scenario
  - `PATCH /{id}` - Update scenario
  - `DELETE /{id}` - Delete draft scenario
  - `POST /{id}/fork` - Fork scenario
  - `POST /{id}/submit-for-approval` - Submit for approval
  - `POST /{id}/approve` - Approve/reject
  - `POST /{id}/publish` - Publish
  - `GET /{id}/versions` - Get version history
  - `POST /{id}/preview` - Calculate impact preview

#### Scenario Builder Frontend (P0)
- **ScenarioBuilder.js Page**:
  - Stats cards (Templates, Custom, Pending, Sources)
  - NGFS Templates tab with parameter previews
  - Custom Scenarios tab with data table
  - Approval Queue tab
  - Fork dialog for customization
  - Sync NGFS Data button

#### Previously Completed
- Basic Portfolio CRUD (MongoDB)
- Analysis engine with Monte Carlo simulation
- Sample data generation
- Scenario Data page
- Risk Engine integration

---

## Prioritized Backlog

### P0 - Critical (Immediate)
- None remaining from current sprint

### P1 - High Priority
1. **Portfolio File Upload System**
   - FileUploadZone component
   - Column mapping wizard
   - Validation results panel
   - Import history tracking

2. **Portfolio Editor**
   - Holdings manager with CRUD
   - Bulk edit toolbar
   - Change history log
   - Portfolio metrics summary

3. **Scenario Impact Preview UI**
   - Connect to `/api/v1/scenarios/{id}/preview` endpoint
   - Impact visualization charts
   - Sector/rating breakdown views

### P2 - Medium Priority
1. **Core v1 API Routes** (portfolios, counterparties full CRUD with PostgreSQL)
2. **Data export functionality**
3. **User authentication/authorization**

### P3 - Future
1. Real NGFS data fetch from IIASA portal
2. Enhanced visualization (trajectory charts, heatmaps)
3. Report generation
4. Scheduled sync jobs

---

## Key Files Reference

### Backend
- `/app/backend/server.py` - Main FastAPI app
- `/app/backend/api/v1/routes/scenarios.py` - Scenario routes
- `/app/backend/services/` - Business logic services
- `/app/backend/db/models/scenario.py` - SQLAlchemy models
- `/app/backend/schemas/scenario.py` - Pydantic schemas
- `/app/backend/.env` - Environment variables

### Frontend
- `/app/frontend/src/App.js` - Main router
- `/app/frontend/src/pages/ScenarioBuilder.js` - Scenario Builder UI
- `/app/frontend/src/components/ui/` - shadcn components
- `/app/frontend/.env` - Frontend config

---

## Database Schema

### PostgreSQL (Scenarios)
```sql
scenarios:
  - id, name, description, source, ngfs_scenario_type, ngfs_version
  - base_scenario_id, approval_status, current_version, is_published
  - parameters (JSON), created_at, updated_at
  - created_by, submitted_by, approved_by, submitted_at, approved_at

scenario_versions:
  - id, scenario_id, version_number, parameters (JSON)
  - change_summary, changed_by, created_at

scenario_impact_previews:
  - id, scenario_id, portfolio_id, impact_summary (JSON)
  - calculated_at, calculation_version

ngfs_data_sources:
  - id, name, url, version, release_date
  - last_synced_at, last_sync_status, sync_count, data_hash
```

### MongoDB (Portfolios)
- Portfolio, Asset, Company collections
- ScenarioSeries, AnalysisRun collections

---

## Testing

### Test Reports
- `/app/test_reports/iteration_2.json` - Latest comprehensive test
- Backend: 100% pass rate (19/19 tests)
- Frontend: All UI components functional

### Test Coverage
- All CRUD operations
- Approval workflow (submit → approve/reject → publish)
- Fork functionality
- Version history
- NGFS sync

---

## Notes
- NGFS data is embedded for reliability (not fetched from external API)
- Impact calculations use sample portfolio data (needs production integration)
- PostgreSQL via Supabase for scenario data
- MongoDB for portfolio/analysis data
