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

### Calculation Engine (Dec 2025)

**File**: `backend/services/stranded_asset_calculator.py`

**5 Calculator Classes**:

1. **ReserveImpairmentCalculator**
   - `calculate_impairment()`: Full reserve NPV analysis under climate scenarios
   - Calculates stranded volume, NPV impact, risk score
   - Generates yearly impairment forecasts for target years
   - Identifies key drivers and recommendations

2. **PowerPlantValuator**
   - `value_plant()`: Complete plant valuation with repurposing options
   - NPV analysis with carbon cost integration
   - Optimal retirement year calculation
   - Repurposing options: CCS, hydrogen, storage, retirement
   - Capacity factor and wholesale price projections

3. **InfrastructureValuator**
   - `value_infrastructure()`: Pipeline, LNG terminal, refinery valuation
   - Utilization decline modeling
   - Contract exposure at risk calculation
   - Transition readiness assessment (H2, ammonia, CCS)

4. **TechnologyDisruptionTracker**
   - `ev_adoption_s_curve()`: Logistic S-curve for EV adoption
   - `calculate_oil_displacement()`: Oil demand reduction from EVs
   - `heat_pump_adoption_curve()`: Heat pump adoption modeling
   - `calculate_gas_displacement()`: Gas demand reduction
   - `green_hydrogen_cost_curve()`: Learning curve for green H2
   - `battery_cost_curve()`: Battery cost projections
   - `get_disruption_summary()`: Comprehensive disruption metrics

5. **PortfolioStrandingAnalyzer**
   - `analyze_portfolio()`: Portfolio-level stranding analysis
   - Aggregates reserves, plants, and infrastructure
   - Risk distribution across portfolio
   - Top risk assets identification
   - Portfolio-level recommendations

**Key Features**:
- Risk scoring (0-1) with LOW/MEDIUM/HIGH/CRITICAL categories
- Carbon price trajectory integration (EU ETS style)
- Demand reduction modeling from transition pathways
- NPV discounting with configurable rates
- Comprehensive recommendations engine

### API Routes (Dec 2025)

**File**: `backend/api/v1/routes/stranded_assets.py`

**Endpoints Implemented**:

**Dashboard**:
- `GET /api/v1/stranded-assets/dashboard` - Dashboard KPIs (total assets, risk distribution, exposure)

**Asset CRUD**:
- `GET /api/v1/stranded-assets/reserves` - List reserves with filtering
- `GET /api/v1/stranded-assets/reserves/{id}` - Get reserve by ID
- `POST /api/v1/stranded-assets/reserves` - Create reserve
- `GET /api/v1/stranded-assets/power-plants` - List power plants
- `GET /api/v1/stranded-assets/power-plants/{id}` - Get plant by ID
- `POST /api/v1/stranded-assets/power-plants` - Create plant
- `GET /api/v1/stranded-assets/infrastructure` - List infrastructure
- `GET /api/v1/stranded-assets/infrastructure/{id}` - Get asset by ID
- `POST /api/v1/stranded-assets/infrastructure` - Create asset

**Calculations**:
- `POST /api/v1/stranded-assets/calculate/reserve-impairment` - Reserve NPV analysis
- `POST /api/v1/stranded-assets/calculate/power-plant-valuation` - Plant valuation
- `POST /api/v1/stranded-assets/calculate/infrastructure-valuation` - Infrastructure valuation

**Technology Disruption**:
- `GET /api/v1/stranded-assets/technology-disruption/{type}` - EV, hydrogen, battery metrics

**Transition Pathways**:
- `GET /api/v1/stranded-assets/transition-pathways` - List pathways
- `GET /api/v1/stranded-assets/transition-pathways/{id}` - Get pathway

**Analysis & Alerts**:
- `POST /api/v1/stranded-assets/scenario-comparison` - Multi-scenario comparison
- `GET /api/v1/stranded-assets/critical-assets` - Critical asset alerts
- `POST /api/v1/stranded-assets/portfolio-analysis` - Portfolio stranding analysis
- `GET /api/v1/stranded-assets/map-data` - Geographic data for mapping

**Sample Data Included**:
- 3 fossil fuel reserves (oil, gas, coal)
- 3 power plants (coal, gas CCGT, gas OCGT)
- 3 infrastructure assets (pipeline, LNG terminal, refinery)
- 3 transition scenarios (IEA NZE, APS, STEPS)
- 3 transition pathways (oil, gas, coal demand)

### Frontend Components (Dec 2025)

**Directory**: `frontend/src/features/stranded-assets/`

**Structure**:
```
stranded-assets/
├── api/strandedAssetsApi.js        # API client for all endpoints
├── hooks/useStrandedAssets.js      # React hooks for data fetching
├── components/
│   ├── dashboard/StrandedAssetDashboard.jsx
│   ├── calculator/ReserveImpairmentCalculator.jsx
│   ├── calculator/PowerPlantValuationTool.jsx
│   └── charts/TechnologyDisruptionChart.jsx
└── pages/StrandedAssetsPage.jsx
```

**Components Implemented**:

1. **StrandedAssetDashboard**
   - KPI cards (Total Exposure, Value at Risk, High Risk Assets, Avg Risk Score)
   - Asset type breakdown (Reserves, Plants, Infrastructure)
   - Risk distribution bar chart
   - Critical Asset Alerts panel

2. **ReserveImpairmentCalculator**
   - Multi-select reserve picker with type badges (Oil/Gas/Coal)
   - Scenario dropdown (IEA NZE, APS, STEPS)
   - Target years toggle buttons (2030-2050)
   - Discount rate slider
   - Results panel with risk gauge, stranded %, NPV impact
   - Recommendations list

3. **PowerPlantValuationTool**
   - Technology filter buttons
   - Plant multi-select with capacity display
   - NPV comparison (baseline vs scenario)
   - Repurposing options grid (CCS, Hydrogen, Storage, Retirement)
   - Optimal retirement year indicator

4. **TechnologyDisruptionChart**
   - Metric selector (EV, Heat Pump, Hydrogen, Battery)
   - Region dropdown
   - Interactive area chart with Recharts
   - Key projections panel (2030, 2040, 2050)
   - CAGR badge

5. **CriticalAssetsPanel** (in StrandedAssetsPage)
   - Risk threshold filter
   - Summary cards (critical/high/total)
   - Sortable alerts table

**Routing**: Added `/stranded-assets` route in App.js
**Navigation**: Added "Stranded Assets" link in sidebar

## Latest Update: Interactive Asset Map Visualization (Feb 16, 2026)

### NEW Feature: Mapbox Interactive Map for Stranded Assets ✅ COMPLETED

**Implementation**:
- Integrated `AssetMapViewer` component into `StrandedAssetDashboard`
- Uses Mapbox GL with dark theme (`mapbox://styles/mapbox/dark-v11`)
- Fetches data from `/api/v1/stranded-assets/map-data` endpoint (9 assets with coordinates)

**Features**:
- Color-coded markers by risk level (Critical: red, High: orange, Medium: yellow, Low: green)
- Asset type filters: Reserves, Power Plants, Infrastructure, Nature Risk, Carbon Projects
- Risk level filters: Critical, High, Medium, Low
- Interactive popups on marker hover/click with asset details
- Stats panel showing High Risk vs Lower Risk counts
- Legend with risk level counts
- Zoom controls (in, out, reset)
- Fullscreen toggle

**Files Modified**:
- `frontend/src/components/shared/AssetMapViewer.jsx` - Fixed import paths
- `frontend/src/features/stranded-assets/components/dashboard/StrandedAssetDashboard.jsx` - Integrated map component

**Testing**: 13/13 backend tests passed, all frontend UI elements verified (iteration_20)

## Latest Update: Real Estate Valuation Engine (Feb 16, 2026)

### NEW Module: Comprehensive Real Estate Valuation Engine ✅ COMPLETED

**Implementation**:
- Full-stack module with 3 traditional valuation approaches
- Backend: FastAPI routes + Pydantic schemas + Calculation engine
- Frontend: React with 5 tabs (Dashboard, Direct Cap, DCF, Cost, Sales Comp)

**Backend Components**:
- `/app/backend/api/v1/routes/real_estate_valuation.py` - 12+ API endpoints
- `/app/backend/services/real_estate_valuation_engine.py` - Core calculation logic
- `/app/backend/schemas/real_estate_valuation.py` - Pydantic models
- `/app/backend/alembic/versions/004_add_real_estate_valuation_tables.py` - DB migration

**Frontend Components**:
- `ValuationPage.jsx` - Main page with tabbed interface
- `ValuationDashboard.jsx` - Portfolio KPIs and property table
- `DirectCapCalculator.jsx` - Income approach (NOI / Cap Rate)
- `DCFCalculator.jsx` - Discounted Cash Flow analysis
- `CostApproachCalculator.jsx` - Replacement cost less depreciation
- `SalesComparisonCalculator.jsx` - Comparable sales adjustments

**Valuation Approaches**:
1. **Income Approach - Direct Capitalization**: PGI → EGI → NOI → Value
2. **Income Approach - DCF**: 10-year projections, NPV, IRR, Equity Multiple
3. **Cost Approach**: Land + (RCN - Depreciation)
4. **Sales Comparison**: Adjusts comparables for time, size, age, quality, condition, location

**API Endpoints**:
- `GET /api/v1/valuation/dashboard` - Portfolio KPIs
- `GET /api/v1/valuation/properties` - List properties
- `POST /api/v1/valuation/income/direct-capitalization` - Direct cap calculation
- `POST /api/v1/valuation/income/dcf` - DCF analysis
- `POST /api/v1/valuation/cost/replacement` - Cost approach
- `POST /api/v1/valuation/sales-comparison` - Sales comparison
- `GET /api/v1/valuation/comparables` - List comparable sales
- `GET /api/v1/valuation/market/cap-rates` - Market cap rates

**Testing**: 29/29 backend tests passed, all frontend UI verified (iteration_21)

**Note**: Uses SAMPLE/HARDCODED data for properties and comparables. Calculations are real.

## Latest Update: Sustainability Frameworks Integration Module (Feb 16, 2026)

### NEW Module: Sustainability Frameworks Integration ✅ COMPLETED

**Implementation**:
- Full-stack module for analyzing green certification value impact
- Backend: FastAPI routes + Pydantic schemas + Calculation engines
- Frontend: React with 4 tabs (Dashboard, GRESB, LEED, Value Impact)
- Data sources: Academic research (Eichholtz, Fuerst & McAllister), Industry reports (JLL, CBRE, RICS)

**Backend Components**:
- `/app/backend/api/v1/routes/sustainability.py` - 15+ API endpoints
- `/app/backend/services/sustainability_calculator.py` - GRESB, LEED, BREEAM, Value Impact calculators
- `/app/backend/schemas/sustainability.py` - 50+ Pydantic models and enums

**Frontend Components** (`/app/frontend/src/features/sustainability/`):
- `pages/SustainabilityPage.jsx` - Main page with tabbed interface
- `components/SustainabilityDashboard.jsx` - KPIs, certification charts, properties table
- `components/GRESBCalculator.jsx` - Portfolio-level ESG assessment
- `components/LEEDCalculator.jsx` - Property-level certification calculator
- `components/ValueImpactCalculator.jsx` - Financial impact analysis

**Certification Frameworks Supported**:
- **GRESB**: 1-5 Star ratings, 5 component scores, benchmark comparison
- **LEED**: Certified/Silver/Gold/Platinum, 9 category scores
- **BREEAM**: Pass to Outstanding, 10 category scores
- **Energy Star**: Score-based certification
- **WELL**: Health-focused certification

**API Endpoints**:
- `GET /api/v1/sustainability/dashboard` - Portfolio sustainability KPIs
- `GET /api/v1/sustainability/certifications` - List certified properties
- `POST /api/v1/sustainability/gresb/assess` - GRESB assessment calculation
- `POST /api/v1/sustainability/leed/assess` - LEED certification analysis
- `POST /api/v1/sustainability/breeam/assess` - BREEAM assessment
- `POST /api/v1/sustainability/value-impact` - Value/rent premium calculation
- `POST /api/v1/sustainability/portfolio/analyze` - Portfolio sustainability analysis
- `POST /api/v1/sustainability/compare` - Certification comparison tool
- `GET /api/v1/sustainability/benchmarks` - Research benchmark data
- `GET /api/v1/sustainability/enums` - Available enum values

**Value Impact Analysis**:
- Rent premiums: 2-20% based on certification type/level
- Value premiums: 1.7x rent premiums (cap rate compression effect)
- Operating cost savings: 3-12% depending on certification
- Cap rate compression: 10-70 bps by certification level
- Regional adjustments: Europe +10%, Asia Pacific -10%
- Sector adjustments: Office baseline, Industrial -30%, Retail -15%

**Testing**: 32/32 backend tests passed, all frontend UI verified (iteration_22)

**Note**: Uses SAMPLE/HARDCODED data for certifications. Calculation engines are real based on academic research.

## Latest Update: Scenario Analysis Module (Feb 16, 2026)

### NEW Module: Interactive Scenario Builder & Sensitivity Analysis ✅ COMPLETED

**Implementation**:
- Full-stack module for real-time what-if analysis, scenario comparison, and sensitivity testing
- Backend: FastAPI routes + Pydantic schemas + Calculation engines
- Frontend: React with 5 tabs (Dashboard, Builder, Sensitivity, What-If, Compare)

**Backend Components**:
- `/app/backend/api/v1/routes/scenario_analysis.py` - 15+ API endpoints
- `/app/backend/services/scenario_analysis_engine.py` - Scenario, Sensitivity, What-If engines
- `/app/backend/schemas/scenario_analysis.py` - Comprehensive Pydantic models

**Frontend Components** (`/app/frontend/src/features/scenarios/`):
- `pages/ScenarioAnalysisPage.jsx` - Main page with 5-tab interface
- `components/ScenarioBuilder.jsx` - Custom scenario creation with modifications
- `components/SensitivityAnalysis.jsx` - Tornado & Spider chart visualizations
- `components/WhatIfAnalysis.jsx` - Real-time parameter changes with cascading effects
- `components/ScenarioComparison.jsx` - Multi-scenario comparison with charts

**Features**:
1. **Scenario Builder**:
   - Select base property and add multiple modifications
   - Modification types: rent_growth, vacancy, expenses, cap_rate, exit_cap_rate, discount_rate, certification, retrofit, climate
   - Quick templates: Optimistic Growth, Recession Stress Test, Green Building Upgrade, Rising Interest Rates
   - Returns: base_value, adjusted_value, value_change_pct, component_impacts

2. **Sensitivity Analysis**:
   - Configurable variable ranges (cap_rate, rent_growth, vacancy, expense_ratio, etc.)
   - Tornado Chart (sorted by impact swing)
   - Spider/Radar Chart (Base vs Optimistic vs Pessimistic)
   - Presets: Standard Analysis, DCF Focus, Operating Performance

3. **What-If Analysis**:
   - Real-time parameter changes (absolute or percentage)
   - Cascading effects (e.g., higher vacancy → increased collection loss)
   - Detailed change breakdown with direct and cascading impacts

4. **Scenario Comparison**:
   - Compare multiple scenarios side-by-side
   - Value comparison bar chart
   - Best/worst scenario identification
   - Key differentiators

**API Endpoints**:
- `GET /api/v1/scenarios/dashboard` - Analysis KPIs and recent scenarios
- `POST /api/v1/scenarios/build` - Build custom scenario with modifications
- `GET /api/v1/scenarios/list` - List saved scenarios
- `POST /api/v1/scenarios/compare` - Compare multiple scenarios
- `GET /api/v1/scenarios/templates/list` - Get predefined templates
- `POST /api/v1/sensitivity/analyze` - Run sensitivity analysis
- `POST /api/v1/sensitivity/tornado` - Generate tornado chart data
- `POST /api/v1/sensitivity/spider` - Generate spider chart data
- `POST /api/v1/what-if/analyze` - What-if analysis with cascading effects

**Testing**: 30/30 backend tests passed, all 5 frontend tabs verified (iteration_23)

**Note**: Uses SAMPLE/HARDCODED property data (3 sample properties). Calculation engines are real.

## Latest Update: Portfolio Aggregation and Reporting Module (Feb 16, 2026)

### NEW Module: Portfolio Analytics Dashboard & Reporting ✅ COMPLETED

**Implementation**:
- Full-stack module consolidating property valuations into portfolio-level analytics
- Backend: FastAPI routes + Pydantic schemas + Analytics engine with sample data
- Frontend: React with 4 tabs (Dashboard, Holdings, Scenarios, Reports)

**Backend Components**:
- `/app/backend/api/v1/routes/portfolio_analytics.py` - 15+ API endpoints
- `/app/backend/services/portfolio_analytics_engine.py` - Analytics, Dashboard, Report engines
- `/app/backend/schemas/portfolio_analytics.py` - Comprehensive Pydantic models (50+ classes)

**Frontend Components** (`/app/frontend/src/features/portfolio-analytics/`):
- `pages/PortfolioAnalyticsPage.jsx` - Main page with 4-tab interface
- `components/PortfolioDashboard.jsx` - KPI cards, charts (Sector, Geographic, Risk distribution)
- `components/PortfolioSelector.jsx` - Portfolio dropdown with details panel
- `components/HoldingsTable.jsx` - Property holdings table with search/sort
- `components/ScenarioComparison.jsx` - Multi-scenario comparison with charts
- `components/ReportGenerator.jsx` - Report type selection and generation

**Features**:
1. **Executive Dashboard**:
   - 8 KPI cards (Total Value, Properties, Risk Score, VaR 95%, Stranded Assets, GRESB Score, Certified %, Yield)
   - Sector Allocation pie chart
   - Geographic Distribution bar chart
   - Risk Distribution bar chart
   - Alerts & Notifications panel

2. **Holdings Table**:
   - Property list with Type, Value, Income, Ownership, Gain/Loss
   - Search by name, location, type
   - Sortable columns (value, income, gain/loss)

3. **Scenario Comparison**:
   - Select multiple scenarios (Optimistic, Recession, Climate, Green Premium, Rising Rates)
   - Best/Worst scenario identification
   - Value spread analysis
   - Comparison bar chart
   - Key insights

4. **Report Generator**:
   - 6 report types: Valuation, Climate Risk, Sustainability, TCFD, Investor, Executive
   - Configurable time horizon (1-30 years)
   - Include charts and property details options
   - Executive summary with key findings

**API Endpoints**:
- `GET /api/v1/portfolio-analytics/portfolios` - List portfolios with metrics
- `GET /api/v1/portfolio-analytics/portfolios/{id}` - Portfolio details
- `POST /api/v1/portfolio-analytics/portfolios` - Create portfolio
- `PATCH /api/v1/portfolio-analytics/portfolios/{id}` - Update portfolio
- `GET /api/v1/portfolio-analytics/portfolios/{id}/holdings` - List holdings
- `GET /api/v1/portfolio-analytics/portfolios/{id}/analytics` - Full analytics
- `GET /api/v1/portfolio-analytics/portfolios/{id}/dashboard` - Dashboard data
- `POST /api/v1/portfolio-analytics/portfolios/{id}/scenarios/compare` - Compare scenarios
- `POST /api/v1/portfolio-analytics/portfolios/{id}/reports/generate` - Generate report
- `GET /api/v1/portfolio-analytics/enums` - Available enum values

**Testing**: 36/36 backend tests passed, all 4 frontend tabs verified (iteration_24)

**Note**: Uses IN-MEMORY SAMPLE data (3 portfolios with holdings). Data not persisted to PostgreSQL - this is by design for demonstration.

## Latest Update: BREEAM Calculator & Universal Export (Feb 16, 2026)

### NEW Feature: BREEAM Certification Calculator with LEED Comparison

**Backend Implementation**:
- Existing BREEAM API at `/api/v1/sustainability/breeam/assess` already functional
- Returns: weighted_score, rating, category_weighted_scores, estimated_rent_premium_percent, estimated_value_premium_percent, improvement_priorities

**Frontend Implementation** (`/app/frontend/src/features/sustainability/`):

1. **BREEAMCalculator.jsx** (NEW):
   - **BREEAM Calculator Tab**: Full form with property details and 10 category sliders (Management, Health & Wellbeing, Energy, Transport, Water, Materials, Waste, Land Use & Ecology, Pollution, Innovation)
   - **Live Score Preview**: Real-time weighted score calculation with rating badge
   - **BREEAM Rating Scale**: Pass (30%), Good (45%), Very Good (55%), Excellent (70%), Outstanding (85%)
   - **Assessment Results**: Weighted Score, Rating Level, Rent Premium, Value Premium, Estimated Value Impact
   - **Category Performance Chart**: Radar chart comparing scores to benchmark
   - **Weighted Score Breakdown**: Horizontal bar chart
   - **Improvement Priorities**: High/medium priority categories with potential gains
   - **Export Button**: PDF/Excel export dropdown for assessment results

2. **BREEAM vs LEED Comparison Tab**:
   - Side-by-side category sliders for BREEAM and LEED
   - Compare Certifications button
   - Side-by-Side Comparison: BREEAM (percentage-based) vs LEED (points-based)
   - Rent Premium, Value Premium, Market Focus comparisons
   - Regional Recommendation (BREEAM for Europe, LEED for Americas)

**SustainabilityPage.jsx Updated**:
- Added 5th tab: BREEAM (with Building2 icon)
- Grid columns updated from 4 to 5

### NEW Feature: Universal PDF/Excel Export

**Backend Implementation**:

1. **Export Service** (`/app/backend/services/export_service.py`):
   - PDF generation using ReportLab (A4 format, styled templates)
   - Excel generation using xlsxwriter (formatted worksheets with colors)
   - Module-specific generators:
     - `generate_portfolio_analytics_pdf/excel` - Executive summary, property details
     - `generate_sustainability_pdf/excel` - Assessment results, value impact
     - `generate_stranded_assets_pdf/excel` - Risk summary, key drivers
     - `generate_scenario_analysis_pdf/excel` - Scenario comparison tables

2. **Universal Export API** (`/app/backend/api/v1/routes/universal_exports.py`):
   - `GET /api/v1/exports/portfolio-analytics/{portfolio_id}` - Portfolio reports
   - `POST /api/v1/exports/sustainability/assessment` - GRESB/LEED/BREEAM exports
   - `POST /api/v1/exports/stranded-assets/analysis` - Stranded asset reports
   - `POST /api/v1/exports/scenario-analysis/comparison` - Scenario comparisons
   - `POST /api/v1/exports/nature-risk/assessment` - Nature risk reports
   - `POST /api/v1/exports/valuation/analysis` - Valuation reports
   - `POST /api/v1/exports/carbon/calculation` - Carbon credit reports
   - `GET /api/v1/exports/bulk` - List all available exports

**Frontend Implementation**:
- `sustainabilityApi.js` updated with `exportSustainabilityAssessment()` and `downloadFile()` helper
- `useSustainability.js` updated with `useExportAssessment()` hook
- Export dropdown added to BREEAMCalculator results section

**Testing**: 20/20 backend tests passed (iteration_25), frontend verified

## Latest Update: Portfolio Analytics DB Persistence & Universal Export Extension (Feb 16, 2026)

### COMPLETED: Portfolio Analytics PostgreSQL Persistence

**Backend Implementation**:
1. **Database Tables Created**:
   - `portfolio_analytics` - Portfolio metadata (id, name, description, type, strategy, AUM, currency)
   - `portfolio_property_holdings` - Property holdings with valuations, certifications, risk scores
   - `portfolio_reports` - Generated report storage

2. **Storage Layer Refactored** (`/app/backend/services/portfolio_analytics_engine.py`):
   - Replaced in-memory storage with PostgreSQL queries using SQLAlchemy
   - Functions: `get_portfolio()`, `get_holdings()`, `save_portfolio()`, `save_holding()`, `remove_holding()`, `list_portfolios()`, `save_report()`, `get_report()`
   - Auto-seeds sample data on module load via `init_sample_data()`
   - 3 sample portfolios with 5 holdings each persisted

### COMPLETED: Universal Export for All Modules

**Frontend Implementation** - Added export buttons to ALL major dashboards:

1. **Reusable Components Created**:
   - `/app/frontend/src/components/shared/ExportButton.jsx` - Dropdown with PDF/Excel options
   - `/app/frontend/src/lib/exportUtils.js` - Export utility functions for all modules

2. **Export Buttons Added To**:
   - Portfolio Analytics Dashboard (`PortfolioDashboard.jsx`)
   - Carbon Credits Dashboard (`CarbonDashboard.jsx`)
   - Stranded Assets Dashboard (`StrandedAssetDashboard.jsx`)
   - Nature Risk Dashboard (`NatureRiskDashboard.jsx`)
   - RE Valuation Dashboard (`ValuationDashboard.jsx`)
   - Scenario Comparison (`ScenarioComparison.jsx`)

**Export API Endpoints**:
| Module | Endpoint | Methods |
|--------|----------|---------|
| Portfolio Analytics | `GET /api/v1/exports/portfolio-analytics/{id}` | PDF, Excel |
| Sustainability | `POST /api/v1/exports/sustainability/assessment` | PDF, Excel |
| Stranded Assets | `POST /api/v1/exports/stranded-assets/analysis` | PDF, Excel |
| Nature Risk | `POST /api/v1/exports/nature-risk/assessment` | PDF, Excel |
| RE Valuation | `POST /api/v1/exports/valuation/analysis` | PDF, Excel |
| Carbon | `POST /api/v1/exports/carbon/calculation` | PDF, Excel |
| Scenarios | `POST /api/v1/exports/scenario-analysis/comparison` | PDF, Excel |

**Testing**: 26/26 backend tests passed, all export buttons verified in 5 dashboards (iteration_26)

## Upcoming / Future Tasks
1. **Report Template Customization**: Allow users to customize report layouts and branding
2. **Email Integration**: Connect scheduled reports to email delivery service (e.g., SendGrid)
3. **Advanced Map Features**: Add heatmap layer, polygon overlays for watersheds
4. **Full end-to-end regression testing**

## Latest Update: P3 Features Complete (Feb 16, 2026)

### COMPLETED: Water Risk Map with Mapbox (P3)

**Frontend Implementation** (`/app/frontend/src/features/nature-risk/components/water/WaterRiskMap.jsx`):
1. **Features**:
   - Interactive Mapbox GL map with risk-colored markers
   - Popup details on marker click (location name, water stress score, country)
   - Legend showing risk level color coding
   - Map controls: zoom, layer toggle (light/dark), reset view
   - Pulse animation for high-risk locations

2. **Integration**:
   - Added to Water Risk tab with Map/List toggle view
   - 10 sample locations with demo coordinates

### COMPLETED: Scheduled Reports System (P3)

**Backend Implementation**:
- Service: `/app/backend/services/scheduled_reports_service.py`
- API Routes: `/app/backend/api/v1/routes/scheduled_reports.py`

**Features**:
- Full CRUD operations for scheduled reports
- 4 frequencies: daily, weekly, monthly, quarterly
- 7 report types: portfolio_analytics, carbon_credits, stranded_assets, nature_risk, sustainability, valuation, scenario_analysis
- Automatic next_run calculation based on frequency
- Toggle active/paused status

**Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/scheduled-reports` | Create scheduled report |
| GET | `/api/v1/scheduled-reports` | List all reports |
| GET | `/api/v1/scheduled-reports/{id}` | Get report by ID |
| PATCH | `/api/v1/scheduled-reports/{id}` | Update report |
| DELETE | `/api/v1/scheduled-reports/{id}` | Delete report |
| POST | `/api/v1/scheduled-reports/{id}/toggle` | Toggle active status |

**Frontend**: Added "Scheduled" tab to Portfolio Analytics page with full CRUD UI

### COMPLETED: Enhanced LEAP Visualization (P3)

**Frontend Implementation** (`/app/frontend/src/features/nature-risk/components/leap/LEAPResultsVisualization.jsx`):
1. **Charts**:
   - Radar chart: LEAP score profile across 4 steps
   - Pie chart: Risk distribution (Low/Medium/High/Critical)
   - Bar chart: Scenario comparison (stacked by LEAP step)

2. **Summary Cards**:
   - Overall risk score with rating badge
   - Individual step scores with progress bars
   - Recommendations section

**Testing**: 21/21 backend tests passed, all frontend features verified (iteration_28)

## Mocked Services (Demo Data)
- `stranded_asset_calculator.py` - Uses sample asset data for reserves, power plants, infrastructure
- `real_estate_valuation_engine.py` - Uses reference data for construction costs and cap rates (this is appropriate for static reference data)
- LEAP calculation - Falls back to demo scores if API fails

## Latest Update: Scenario Persistence & LEAP Wizard (Feb 16, 2026)

### COMPLETED: Scenario Persistence to PostgreSQL (P2)

**Backend Implementation** (`/app/backend/services/scenario_analysis_engine.py`):
1. **Database Functions Added**:
   - `save_scenario()` - Saves scenarios to PostgreSQL with source='CUSTOM', approval_status='DRAFT'
   - `get_scenario()` - Retrieves scenario by ID with full parameters
   - `list_scenarios()` - Lists all custom scenarios ordered by updated_at
   - `delete_scenario()` - Removes scenario from database

2. **API Endpoints Working**:
   - `POST /api/v1/scenarios/build` - Creates scenario and persists to DB
   - `GET /api/v1/scenarios/list` - Lists all custom scenarios
   - `GET /api/v1/scenarios/{id}` - Retrieves specific scenario

### COMPLETED: LEAP Assessment Wizard (P3)

**Frontend Implementation** (`/app/frontend/src/features/nature-risk/components/leap/LEAPAssessmentWizard.jsx`):
1. **4-Step Wizard**:
   - **Locate**: Entity name, sector, site information, coordinates
   - **Evaluate**: Ecosystem service dependencies, ENCORE dependencies
   - **Assess**: Climate/Nature scenario selection, risk exposure sliders
   - **Prepare**: Mitigation strategies, notes, TNFD disclosure readiness

2. **Features**:
   - Progress indicator and step navigation
   - Form validation across steps
   - Integration with LEAP calculation API
   - Fallback to demo results if API fails

**Testing**: 30/30 backend tests passed, LEAP wizard UI verified (iteration_27)

## Implemented Carbon Sector Calculator Forms
All sector input forms are implemented in `/app/frontend/src/features/carbon/components/calculator/MethodologyCalculator.jsx`:

| Sector | Methodologies | Status |
|--------|--------------|--------|
| Energy | ACM0002, ACM0006, AMS-I.D | ✅ Complete |
| Forestry | AR-AM0014, VM0045, VM0047 | ✅ Complete |
| Waste | ACM0001, AMS-III.E, AMS-III.G | ✅ Complete |
| Agriculture | VM0017, VM0019, VM0042 | ✅ Complete |
| Industrial | ACM0007, AM0009, AMS-III.N | ✅ Complete |
| Transport | ACM0023, AMS-III.C | ✅ Complete |
| Buildings | MMECD, AMS-II.E | ✅ Complete |
| Household | AMS-II.G, AMS-I.E | ✅ Complete |
| Mining | ACM0008, VM0032 | ✅ Complete |
| Blue Carbon | VM0033, VM0048 | ✅ Complete |

