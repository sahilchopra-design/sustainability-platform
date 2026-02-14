# A2 Intelligence by AA Impact Inc. — Climate Risk Analytics Platform

## Architecture
- Backend: FastAPI + **PostgreSQL** (Supabase) — unified single DB
- Frontend: React + shadcn/ui + Recharts + Zustand
- Auth: Google OAuth (Emergent) + JWT — **PostgreSQL-backed**
- Data: IIASA Scenario Explorer (real) + 20 hub sources + 24 NGFS dedicated
- Branding: A2 Intelligence (tool) by AA Impact Inc. (organization)

## Database Unification Complete
- Portfolios, Assets, AnalysisRuns migrated from MongoDB to PostgreSQL
- Auth (Users, Sessions) migrated from MongoDB to PostgreSQL
- All API endpoints now use PostgreSQL via SQLAlchemy
- MongoDB kept only for legacy compatibility (can be removed)

## Pages (15 routes, all auth-gated)
| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/impact` | Impact Calculator + Reports |
| `/sub-analysis` | Sub-Parameter Analysis |
| `/browser` | Scenario Browser |
| `/data-hub` | Data Hub (20 sources) |
| `/ngfs` | NGFS Catalog (24 scenarios) |
| `/comparison` | Comparison & Gap Analysis |
| `/custom-builder` | Custom Builder |
| `/portfolios` | Portfolios |
| `/portfolio-manager` | Upload & Edit |
| `/analysis` | Run Analysis |
| `/alerts` | Alerts |
| `/scenario-builder` | Legacy Builder |
| `/scenario-data` | Scenario Data |

## UI/Branding
- Dark navy sidebar (#0f2137) with cyan accent highlights
- Grouped navigation: Analytics, Scenarios, Portfolio, System
- A2 Intelligence logo in header, AA Impact Inc. in footer
- Login page with branded gradient background
- Investor-grade professional aesthetic

## All Tests (13+ iterations, 230+ tests)
All passing at 100%
