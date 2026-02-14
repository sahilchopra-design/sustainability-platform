# Climate Credit Risk Intelligence Platform - PRD

## Original Problem Statement
Comprehensive portfolio analysis and scenario building application for climate risk assessment.

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) + MongoDB
- Frontend: React + shadcn/ui + Recharts + Zustand
- Real Data: IIASA Scenario Explorer (pyam-iamc) for NGFS, IPCC AR6, IAMC 1.5C

## Pages & Routes
| Route | Page | Status |
|-------|------|--------|
| `/` | Dashboard | Done |
| `/portfolios` | Portfolios | Done |
| `/analysis` | Run Analysis | Done |
| `/scenario-data` | Scenario Data | Done |
| `/scenario-builder` | Scenario Builder | Done |
| `/data-hub` | Data Hub (19 sources) | Done |
| `/browser` | Scenario Browser (filters, drawer, compare) | Done |
| `/comparison` | Comparison & Gap Analysis | Done |
| `/impact` | **Impact Calculator** | Done (New) |
| `/portfolio-manager` | **Portfolio Manager (Upload + Editor)** | Done (New) |

## Completed Features

### Impact Calculator (P0) — Feb 14, 2026
- Connects hub scenarios to portfolios via calculation engine
- Maps scenario categories → engine types (Orderly/Disorderly/Hot House)
- Calculates PD/LGD adjustments, Expected Loss, VaR 95%/99%, rating migrations
- Extracts scenario multipliers (carbon price, emissions, temperature)
- Frontend: Portfolio + Scenario selectors, EL/VaR cards, bar + line charts

### Custom Scenario Builder (P0) — Feb 14, 2026
- Blend trajectories from multiple scenarios
- Select base scenario, override specific variable+region combinations
- Lineage tracking in parameters JSON
- Creates new entries in hub_scenarios with "custom" source

### Portfolio Upload & Editor (P1) — Feb 14, 2026
- CSV upload with auto-column detection (name, sector, exposure, rating, pd, lgd, maturity)
- Validation with error reporting
- Create portfolio from parsed assets
- Editor: Select portfolio, add/remove assets, edit fields inline, save

### Previously Completed
- Scenario Browser: sidebar filters, grid/list, detail drawer, compare workspace, favorites, analytics
- Comparison Engine: multi-scenario overlay, gap analysis, consistency checks
- Data Hub: 19 sources, 99+ scenarios, 875+ trajectories, 3 real IIASA sources

## Key Backend Files
- `/app/backend/services/impact_calculator.py`
- `/app/backend/services/custom_scenario_builder.py`
- `/app/backend/services/portfolio_upload.py`
- `/app/backend/api/v1/routes/analysis.py`
- `/app/backend/api/v1/routes/data_hub.py`
- `/app/backend/services/scenario_comparison_service.py`

## Testing
- iteration_8: Impact + Custom Builder + Portfolio Upload (15/15 BE, 12/12 FE)
- iteration_7: Scenario Browser (15/15 FE)
- iteration_6: Comparison & Analysis (18/18 BE)
- iteration_5: Expanded Data Hub (24/24 BE)

## Backlog
### P2
- User authentication
- Report generation (PDF/Excel export)
- Alert System UI
- Database unification (MongoDB → PostgreSQL)
### P3
- Live APIs for remaining 16 synthetic sources
- Scheduled sync jobs, Redis caching
- Additional regional data sources
