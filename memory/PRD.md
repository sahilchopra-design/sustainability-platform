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

#### Portfolio Scenario Analysis Dashboard Components (P0)
All 9 components created, integrated, and tested:

1. **PortfolioSelector** (`/app/frontend/src/components/dashboard/PortfolioSelector.jsx`)
   - Searchable dropdown with portfolio list
   - Portfolio summary (assets count, total exposure)
   - Create new portfolio dialog

2. **ScenarioSelector** (`/app/frontend/src/components/dashboard/ScenarioSelector.jsx`)
   - Multi-select dropdown for NGFS scenarios
   - Quick select buttons (Orderly, Disorderly, Hot House, All)
   - Time horizon selector (2030, 2040, 2050)

3. **PortfolioMetricsCard** (`/app/frontend/src/components/dashboard/PortfolioMetricsCard.jsx`)
   - Key metrics: Total Exposure, Expected Loss, Avg PD, Avg LGD, Holdings
   - Trend indicators with delta comparison
   - Info tooltips for each metric

4. **ExposureBreakdownChart** (`/app/frontend/src/components/dashboard/ExposureBreakdownChart.jsx`)
   - Interactive donut chart
   - Tabs: Sector, Geography, Rating breakdown
   - Hover tooltips and drill-down support

5. **ScenarioComparisonChart** (`/app/frontend/src/components/dashboard/ScenarioComparisonChart.jsx`)
   - Horizontal bar chart comparing scenarios
   - Metric selector (Expected Loss, PD Change, LGD Change)
   - Horizon filter and CSV export

6. **HeatmapVisualization** (`/app/frontend/src/components/dashboard/HeatmapVisualization.jsx`)
   - Sector × Geography risk matrix
   - Configurable color scales (Risk, Exposure, Neutral)
   - Hover tooltips for cell details

7. **CounterpartyTable** (`/app/frontend/src/components/dashboard/CounterpartyTable.jsx`)
   - Sortable columns (Counterparty, Rating, Exposure, PD, LGD, Expected Loss)
   - Search filter and pagination
   - CSV export functionality

8. **AnalysisRunButton** (`/app/frontend/src/components/dashboard/AnalysisRunButton.jsx`)
   - Triggers scenario analysis
   - Progress indicator during analysis
   - Toast notifications for status

9. **ReportExportButton** (`/app/frontend/src/components/dashboard/ReportExportButton.jsx`)
   - Format dropdown (PDF, Excel, CSV, JSON)
   - Section selection dialog
   - Download functionality

#### Supporting Files:
- **Store**: `/app/frontend/src/store/dashboardStore.js` (Zustand)
- **Hooks**: `/app/frontend/src/hooks/usePortfolio.js`, `useScenarioAnalysis.js`

#### Scenario Builder Backend (P0)
- **NGFS Integration**: 6 Phase V scenarios synced
- **Scenario CRUD**: Create, Read, Update, Delete operations
- **Versioning**: Full version history with change tracking
- **Approval Workflow**: Draft → Pending → Approved → Published
- **API Endpoints**: `/api/v1/scenarios/*`

#### Scenario Builder Frontend (P0)
- **ScenarioBuilder.js Page**: Templates, Custom scenarios, Approval queue

---

## Prioritized Backlog

### P1 - High Priority
1. **Portfolio File Upload System**
   - FileUploadZone component
   - Column mapping wizard
   - Validation results panel

2. **Portfolio Editor**
   - Holdings manager with CRUD
   - Bulk edit toolbar
   - Change history log

3. **Populate Company Country Data**
   - Geography breakdown shows "Unknown" because company.country is not populated

### P2 - Medium Priority
1. **Core v1 API Routes** (portfolios, counterparties full CRUD with PostgreSQL)
2. **Data export functionality enhancements**
3. **User authentication/authorization**

### P3 - Future
1. Real NGFS data fetch from IIASA portal
2. Enhanced visualization (trajectory charts)
3. Report generation (actual PDF/Excel export)
4. Scheduled sync jobs

---

## Key Files Reference

### Dashboard Components
- `/app/frontend/src/components/dashboard/` - All 9 components
- `/app/frontend/src/components/dashboard/index.js` - Export barrel
- `/app/frontend/src/store/dashboardStore.js` - Zustand state management
- `/app/frontend/src/hooks/usePortfolio.js` - Portfolio data hooks
- `/app/frontend/src/hooks/useScenarioAnalysis.js` - Analysis hooks

### Backend
- `/app/backend/server.py` - Main FastAPI app
- `/app/backend/api/v1/routes/scenarios.py` - Scenario routes
- `/app/backend/services/` - Business logic services

---

## Testing

### Test Reports
- `/app/test_reports/iteration_3.json` - Dashboard components test
- `/app/test_reports/iteration_2.json` - Scenario Builder test
- Frontend: 100% pass rate (all 9 components functional)
- Backend: 100% pass rate (19/19 tests)

### Bugs Fixed in This Session
1. Holdings metric showing '--' → Fixed: Changed numCounterparties to numAssets
2. Geography tab empty → Fixed: Added geoBreakdown calculation
3. Analysis results $0/N/A → Fixed: Updated API response format handling

---

## Notes
- Dashboard uses Zustand for state management
- Charts use recharts library
- Table uses @tanstack/react-table
- Geography breakdown shows "Unknown" due to missing company.country data (DATA issue)
