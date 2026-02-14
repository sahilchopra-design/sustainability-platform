# Climate Credit Risk Intelligence Platform - PRD

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) + MongoDB
- Frontend: React + shadcn/ui + Recharts + Zustand
- Auth: Google OAuth (Emergent) + JWT email/password
- Real Data: IIASA Scenario Explorer (pyam-iamc)

## Pages (11 routes, all auth-gated)
| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/portfolios` | Portfolios |
| `/analysis` | Run Analysis |
| `/scenario-data` | Scenario Data |
| `/scenario-builder` | Scenario Builder |
| `/data-hub` | Data Hub (19 sources) |
| `/browser` | Scenario Browser |
| `/comparison` | Comparison & Gap Analysis |
| `/impact` | Impact Calculator + Report Export |
| `/portfolio-manager` | Portfolio Upload + Editor |
| `/alerts` | Scenario Alerts |

## All Completed Features

### Authentication — Feb 14, 2026
- Google OAuth via Emergent Auth (primary) + JWT email/password (fallback)
- Session tokens in MongoDB (users + user_sessions collections)
- Auth gates all pages, user profile in sidebar with logout
- Testing: 12/12 BE + 7/7 FE (iteration_10)

### Alert System UI — Feb 14, 2026
- In-app notifications for scenario updates, revisions, trend changes
- Unread badges, mark read/all read, unread-only filter
- POST/GET/PATCH endpoints for alert CRUD
- Route: `/alerts`

### Report Generator — Feb 14, 2026
- PDF (reportlab), Excel (openpyxl), CSV export from Impact Calculator
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
- Database unification (MongoDB → PostgreSQL)
### P3
- Live APIs for remaining 16 synthetic sources
- Scheduled sync jobs, Redis caching
- Role-based access control
