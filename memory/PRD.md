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
| `/carbon` | **Carbon Credits Module** |
| `/browser` | Scenario Browser |
| `/data-hub` | Data Hub (20 sources) |
| `/ngfs` | NGFS Catalog (24 scenarios) |
| `/comparison` | Comparison & Gap Analysis |
| `/custom-builder` | Custom Builder |
| `/portfolios` | Portfolios |
| `/portfolio-manager` | Upload & Edit |
| `/analysis` | Run Analysis |
| `/alerts` | Alerts |

## Latest Update: Methodology Engine Integration (Feb 2026)
### 40+ Carbon Credit Methodologies Implemented

**Backend** (`/app/backend/services/methodology_engine.py`):
- 40+ certified methodologies from 6 standards: CDM (ACM, AMS, AM, AR), VCS, Gold Standard, CAR, ACR, GCC
- Real calculation formulas based on official methodology documents
- Covers 10 sectors: Energy, Forestry, Waste, Agriculture, Industrial, Transport, Buildings, Household, Mining, Blue Carbon

**API Endpoints** (`/api/v1/carbon/`):
- `GET /methodology-list` - All 40+ methodologies with metadata
- `GET /methodology-list/{sector}` - Filter by sector
- `POST /calculate/methodology` - Single methodology calculation
- `POST /calculate/batch` - Batch calculations
- `GET /data/grid-emission-factor` - Country emission factors (20+ countries)
- `GET /methodology-details/{code}` - Methodology documentation
- `GET /methodology-inputs/{code}` - Required inputs with defaults

**Frontend** (`/app/frontend/src/features/carbon/`):
- Methodology Calculator component with sector tabs and input forms
- Real-time calculation results display
- Yearly projections for forestry methodologies
- Integrated in Carbon Dashboard as "Calculator" tab

**Testing**: 63/63 backend tests + all frontend tests passed (iteration_17)

### Key Methodologies by Sector

**Energy (10)**:
- ACM0002: Grid-Connected Renewable Energy
- ACM0006: Biomass Electricity & Heat
- ACM0009: Coal to Gas Switch
- AMS-I.A/C/D: Small-scale Renewables

**Forestry (5)**:
- AR-ACM0003: Afforestation/Reforestation
- VM0047: ARR (VCS)
- VM0048: REDD+
- CAR-Forest, ACR-IFM

**Waste (7)**:
- ACM0001: Landfill Gas Capture
- ACM0022: Composting
- AMS-III.B/C/D: Wastewater & Solid Waste

**Agriculture (5)**:
- ACM0010: Manure Methane
- VM0022: Agricultural N2O
- VM0042: Agricultural Land Management
- VM0044: Biochar

**Household (2)**:
- TPDDTEC: Clean Cookstoves
- TPDDTEC-SWH: Solar Water Heaters

## Previous: Carbon Credits Module Base (Dec 2025)
- 7 PostgreSQL tables: CarbonMethodology, CarbonEmissionFactor, CarbonPortfolio, CarbonProject, CarbonScenario, CarbonCalculation, CarbonReport
- Full CRUD API for portfolios, projects, scenarios
- Calculation engine with risk-adjusted credits, NPV, Monte Carlo simulation
- Dashboard with 4 KPI cards, credits projection chart, risk heat map
- Interactive Mapbox map showing global project distribution
- Scenario builder with risk sliders (permanence, delivery, regulatory, market)
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

## All Tests Summary
- 17 iterations total
- 400+ tests passed
- 100% pass rate

## Upcoming / Future Tasks
1. **Sector Input Forms (P1)**: Create detailed input forms for remaining sectors (Transport, Buildings, Mining)
2. **Methodology Documentation (P2)**: Add detailed applicability criteria and step-by-step calculation guides
3. **Project Integration (P2)**: Allow saving methodology calculations as new projects
4. **Export Features (P2)**: PDF/Excel export of calculation results
5. **Comparison Tool (P3)**: Compare multiple methodologies for the same project scenario
