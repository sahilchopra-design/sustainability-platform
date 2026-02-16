# A2 Intelligence by AA Impact Inc.

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) — unified single DB
- Frontend: React + shadcn/ui + Recharts + Zustand + **Redux Toolkit**
- Auth: Google OAuth + JWT — PostgreSQL
- Data: IIASA (real) + 20 sources + 24 NGFS + CBAM + **Carbon Credits** + **Nature Risk (TNFD)**
- Maps: Mapbox GL

## Pages (18 routes)
| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/impact` | Impact Calculator + Reports |
| `/sub-analysis` | Sub-Parameter Analysis (7 methods) |
| `/cbam` | CBAM Module |
| `/carbon` | Carbon Credits Module |
| `/nature-risk` | **Nature Risk Module (NEW)** |
| `/browser` | Scenario Browser |
| `/data-hub` | Data Hub (20 sources) |
| `/ngfs` | NGFS Catalog (24 scenarios) |
| `/comparison` | Comparison & Gap Analysis |
| `/custom-builder` | Custom Builder |
| `/portfolios` | Portfolios |
| `/portfolio-manager` | Upload & Edit |
| `/analysis` | Run Analysis |
| `/alerts` | Alerts |

## Latest Update: Nature Risk Module (Feb 16, 2026)

### NEW Feature: Comprehensive Nature Risk Module (TNFD LEAP Methodology)

**Backend Implementation** (`/app/backend/`):

1. **Schemas** (`schemas/nature_risk.py`):
   - 20+ Pydantic models for scenarios, LEAP assessments, ENCORE dependencies, water risk, biodiversity, GBF alignment
   - Comprehensive enums for risk ratings, entity types, site types, etc.

2. **Calculator Engine** (`services/nature_risk_calculator.py`):
   - `LEAPAssessmentCalculator`: Full TNFD LEAP methodology (Locate, Evaluate, Assess, Prepare)
   - `WaterRiskCalculator`: Water risk analysis using Aqueduct-style data
   - `BiodiversityOverlapCalculator`: Spatial overlap analysis with protected areas
   - `PortfolioNatureRiskCalculator`: Aggregated portfolio-level nature risk

3. **Seed Data** (`services/nature_risk_seed_data.py`):
   - Complete ENCORE database: 18 sectors, 60+ ecosystem dependencies
   - 6 climate/nature scenarios (TNFD, NCORE, IPBES)
   - 17 biodiversity sites (World Heritage, Ramsar, KBA, Protected Areas, IBAs)
   - 10 water risk locations with Aqueduct-style indicators

4. **API Routes** (`api/v1/routes/nature_risk.py`):
   - `/scenarios` - Scenario CRUD (6 built-in scenarios)
   - `/leap-assessments/calculate` - Run LEAP assessments
   - `/encore/sectors`, `/encore/dependencies` - ENCORE explorer
   - `/water-risk/locations`, `/water-risk/analyze`, `/risk-report` - Water risk analysis
   - `/biodiversity/sites`, `/overlaps/calculate` - Biodiversity analysis
   - `/portfolio/analyze`, `/nature-exposure` - Portfolio nature risk
   - `/gbf-targets`, `/gbf-alignment` - GBF compliance tracking
   - `/dashboard/summary` - Dashboard metrics
   - `/reports/tnfd-disclosure` - TNFD report generation

**Frontend Implementation** (`/app/frontend/src/features/nature-risk/`):

1. **Main Page** (`pages/NatureRiskPage.jsx`):
   - 6 tabs: Dashboard, Portfolio, Water Risk, Biodiversity, ENCORE, GBF
   - TNFD Framework, ENCORE Database, GBF Aligned badges

2. **Dashboard** (`components/dashboard/NatureRiskDashboard.jsx`):
   - 4 KPI cards: Total Assessments, High Risk Entities, Water Stress Locations, Biodiversity Overlaps
   - Sector Risk Distribution bar chart
   - GBF Target Alignment pie chart
   - Nature Risk Trend line chart

3. **Portfolio Analysis** (`components/portfolio/PortfolioNatureRisk.jsx`):
   - Scenario selection (6 scenarios with checkboxes)
   - Collateral impact toggle
   - Results: Holdings count, Avg LEAP Score, High Risk Count, Exposure at Risk
   - LEAP Score Distribution chart
   - Holdings table with risk ratings

4. **Water Risk** (`components/water/WaterRiskAnalysis.jsx`):
   - 10 locations with baseline water stress scores
   - Location detail panel with projections
   - Water Stress Projections chart (Baseline → 2050)
   - Risk indicators bar chart
   - Recommendations

5. **Biodiversity** (`components/biodiversity/BiodiversityOverlaps.jsx`):
   - 17 biodiversity sites browser
   - Filter by country, site type, search
   - Site detail panel with species, area, coordinates

6. **ENCORE Explorer** (`components/dashboard/ENCOREExplorer.jsx`):
   - 18 sector dropdown
   - Dependency scores visualization
   - Detailed dependency descriptions

7. **GBF Alignment** (`components/dashboard/GBFAlignment.jsx`):
   - 23 GBF targets
   - Alignment status: Aligned, Partial, Not Aligned
   - Overall Score progress

**Testing**: 36/36 backend tests + all frontend UI flows verified (iteration_19)

## Previous: Save Calculation as Project (Feb 16, 2026)
### Feature: Save Methodology Calculations as Projects ✅ COMPLETED

**Backend** (`/app/backend/api/v1/routes/carbon.py`):
- NEW endpoint: `POST /api/v1/carbon/projects/from-calculation`
- Auto-maps methodologies to project types and standards

**Frontend** (`/app/frontend/src/features/carbon/components/calculator/MethodologyCalculator.jsx`):
- "Save as Project" button in Calculation Results card
- Save dialog with Portfolio selector

**Testing**: 9/9 backend tests + all frontend UI flows verified (iteration_18)

## Previous: Methodology Engine Integration (Feb 2026)
### 40+ Carbon Credit Methodologies Implemented

- 40+ certified methodologies from 6 standards: CDM, VCS, Gold Standard, CAR, ACR, GCC
- Covers 10 sectors: Energy, Forestry, Waste, Agriculture, Industrial, Transport, Buildings, Household, Mining, Blue Carbon
- Testing: 63/63 backend tests + all frontend tests passed (iteration_17)

## Previous: Carbon Credits Module Base (Dec 2025)
- 7 PostgreSQL tables
- Full CRUD API for portfolios, projects, scenarios
- Dashboard with 4 KPI cards, Mapbox map
- Testing: 32/32 BE + all FE verified (iteration_16)

## Previous: CBAM Module
- 8 PostgreSQL tables
- 15 EU CBAM product categories
- Cost projection engine
- Testing: 34/34 BE + all FE (iteration_15)

## All Tests Summary
- 19 iterations total
- 450+ tests passed
- 100% pass rate

## Latest Update: Stranded Asset Module - Database Migration (Dec 2025)

### NEW Feature: Stranded Asset Module Database Schema

**Migration File**: `backend/alembic/versions/002_add_stranded_asset_tables.py`

**6 New Tables Created**:

1. **fossil_fuel_reserve** - Oil, gas, coal reserves
   - Tracks proven/probable/possible reserves (1P/2P/3P categories)
   - Breakeven prices, lifting costs, remaining CapEx
   - Carbon intensity, methane leakage rate
   - Production timeline (start, depletion, license expiry)
   - Geolocation (lat/long)

2. **power_plant** - Generation assets
   - Technology types: coal, gas_ccgt, gas_ocgt, nuclear, wind, solar
   - Capacity (MW), efficiency, heat rate
   - Emissions: CO2, NOx, SO2 intensity
   - CCS capability and capacity
   - Operating costs (fixed O&M, variable O&M, fuel)
   - Offtake: merchant, PPA, regulated
   - Repurposing options: CCS, hydrogen, storage, retirement

3. **infrastructure_asset** - Pipelines, LNG terminals, refineries
   - Asset types: pipeline_oil, pipeline_gas, lng_terminal, refinery
   - Capacity utilization, book value, replacement cost
   - Contract maturity profile (JSONB), take-or-pay exposure
   - Future-ready flags: hydrogen, ammonia, CCS compatible
   - Environmental permits (JSONB)

4. **stranded_asset_calculation** - Calculation results
   - Links to scenarios for scenario-based analysis
   - Stranding metrics: volume %, value USD, NPV impact
   - Risk scoring: stranding_risk_score (0-1), risk_category
   - Optimal retirement analysis
   - Key assumptions & sensitivity analysis (JSONB)

5. **technology_disruption_metric** - TimescaleDB time-series
   - Metric types: EV sales/stock share, heat pump adoption, green hydrogen
   - Regional breakdown, scenario alignment (IEA_NZE, STEPS, NGFS)
   - Data source tracking (IEA, BloombergNEF, IRENA)
   - Projection vs actual data distinction

6. **energy_transition_pathway** - Sector trajectories
   - Sectors: oil, gas, coal, power
   - Demand/price/capacity trajectories (JSONB)
   - Peak demand year, net zero year
   - Carbon price trajectories
   - Policy and technology assumptions

**Indexes**: Optimized for counterparty lookups, asset type filtering, geospatial queries, risk scoring, and time-series analysis.

**Note**: After migration, manually run for TimescaleDB:
```sql
SELECT create_hypertable('technology_disruption_metric', 'time', chunk_time_interval => INTERVAL '1 year');
```

### Pydantic Schemas (Dec 2025)

**File**: `backend/schemas/stranded_assets.py`

**8 Enums Defined**:
- `ReserveType`: oil, gas, coal
- `ReserveCategory`: 1P, 2P, 3P
- `PlantTechnology`: coal, gas_ccgt, gas_ocgt, nuclear, hydro, wind, solar, etc. (13 types)
- `InfrastructureType`: pipeline_oil, pipeline_gas, lng_terminal, refinery, etc. (6 types)
- `RiskCategory`: low, medium, high, critical
- `OfftakeType`: merchant, ppa, regulated
- `RepurposingType`: ccs, hydrogen, storage, retirement
- `AssetType`: reserve, power_plant, infrastructure

**Core Asset Schemas**:
- `FossilFuelReserve[Base/Create/Update/Response/ListResponse]`
- `PowerPlant[Base/Create/Update/Response/ListResponse]`
- `InfrastructureAsset[Base/Create/Update/Response/ListResponse]`

**Calculation Schemas**:
- `ReserveImpairmentRequest/Result/Response` - Reserve valuation with yearly impairments
- `PowerPlantValuationRequest/Result/Response` - Plant NPV with repurposing options
- `InfrastructureValuationRequest/Result/Response` - Infrastructure stranding analysis
- `StrandedAssetCalculationCreate/Response` - DB record for calculations
- `YearlyImpairment`, `YearlyValuation`, `RepurposingOption` - Supporting models

**Technology & Pathway Schemas**:
- `TechnologyDisruptionMetric[Create/Response/Summary]` - EV, hydrogen, etc. metrics
- `EnergyTransitionPathway[Base/Create/Update/Response/ListResponse]` - Sector trajectories

**Dashboard & Analysis Schemas**:
- `StrandedAssetDashboardKPIs` - Total assets, risk counts, exposure
- `PortfolioStrandingAnalysis[Request/Response]` - Portfolio-level stranding analysis
- `CriticalAssetAlert`, `CriticalAssetAlertList` - Risk alerts
- `ScenarioComparison[Request/Result/Response]` - Multi-scenario comparison

## Upcoming / Future Tasks
1. **Stranded Asset Module Backend (P0)**: Create Pydantic models, services, and API routes for the Stranded Asset Module
2. **Stranded Asset Module Frontend (P1)**: Build dashboard, asset management, and calculation UI
3. **Sector Input Forms (P2)**: Create detailed input forms for remaining Carbon sectors (Transport, Buildings, Mining)
4. **Export Features (P2)**: PDF/Excel export of calculation results and nature risk reports
5. **LEAP Assessment Wizard (P2)**: Multi-step wizard for comprehensive LEAP assessments
6. **Biodiversity Overlap Calculator (P3)**: Spatial analysis with asset coordinates
7. **Water Risk Map (P3)**: Mapbox integration for water risk visualization
8. **Comparison Tool (P3)**: Compare multiple methodologies for the same project scenario
