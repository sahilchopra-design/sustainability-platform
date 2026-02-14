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
| `/browser` | Scenario Browser | Done |
| `/comparison` | Comparison & Gap Analysis | Done |
| `/impact` | Impact Calculator + **Report Export** | Done |
| `/portfolio-manager` | Portfolio Upload + Editor | Done |

## Completed Features (All Tested)

### Report Generator — Feb 14, 2026
- Professional PDF reports (reportlab): Cover page, executive summary, metrics tables, scenario details, multipliers
- Excel reports (openpyxl): Multi-sheet workbook with Summary, Impact Results, Multipliers, Scenario Details
- CSV reports: Flat data export for further analysis
- Frontend: PDF/Excel/CSV export buttons on Impact Calculator, opens download in new tab
- API: `POST /api/v1/analysis/reports/generate` + `GET /api/v1/analysis/reports/download/{filename}`
- Testing: 11/11 BE + 6/6 FE (iteration_9)

### Impact Calculator + Custom Builder + Portfolio Manager — Feb 14, 2026
- Testing: 15/15 BE + 12/12 FE (iteration_8)

### Scenario Browser — Feb 14, 2026
- Testing: 15/15 FE (iteration_7)

### Comparison & Analysis — Feb 14, 2026
- Testing: 18/18 BE (iteration_6)

### Data Hub (19 sources, 99+ scenarios, 875+ trajectories) — Feb 14, 2026
- Testing: 24/24 BE (iteration_5)

## Backlog
### P2
- User authentication
- Alert System UI (in-app notifications)
- Database unification (MongoDB → PostgreSQL)
### P3
- Live APIs for remaining 16 synthetic sources
- Scheduled sync jobs, Redis caching
