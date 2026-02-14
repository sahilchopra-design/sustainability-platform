# Climate Credit Risk Intelligence Platform - PRD

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) + MongoDB
- Frontend: React + shadcn/ui + Recharts + Zustand
- Auth: Google OAuth (Emergent) + JWT email/password
- Data: IIASA Scenario Explorer (real) + 19 hub sources + 24 NGFS dedicated

## Pages (14 routes, all auth-gated)
| Route | Page | Latest Test |
|-------|------|-------------|
| `/` | Dashboard | Done |
| `/portfolios` | Portfolios | Done |
| `/analysis` | Run Analysis | Done |
| `/scenario-data` | Scenario Data | Done |
| `/scenario-builder` | Legacy Scenario Builder | Done |
| `/data-hub` | Data Hub (20 sources, 102 scenarios) | iter_5 |
| `/browser` | Scenario Browser | iter_7 |
| `/comparison` | Comparison & Gap Analysis | iter_6 |
| `/impact` | Impact Calculator + Reports | iter_9 |
| `/portfolio-manager` | Portfolio Upload + Editor | iter_8 |
| `/alerts` | Scenario Alerts | Done |
| `/ngfs` | NGFS Scenario Catalog (24 scenarios) | iter_11 |
| `/custom-builder` | **Custom Scenario Builder** | **iter_12** |

## Latest: Custom Scenario Builder (Feb 14, 2026)
- Customize ANY of 102 hub scenarios (all 20 sources, not just NGFS)
- Parameter adjustment with year-by-year values (2030/2040/2050)
- Real-time impact preview: temperature projection (TCRE), emissions trajectory, risk scores, economic impact
- Monte Carlo simulation (100-10000 iterations): probability distributions, P(<1.5°C), P(<2°C)
- Validation engine with physical/economic constraints
- Full CRUD + fork for saved custom scenarios
- Testing: 23/23 BE + all FE (iteration_12)

## All Tests (12 iterations, 200+ total tests)
- iter_12: Custom Builder (23/23 BE)
- iter_11: NGFS Module (29/29 BE)
- iter_10: Authentication (12/12 BE, 7/7 FE)
- iter_9: Reports (11/11 BE, 6/6 FE)
- iter_8: Impact+Upload (15/15 BE, 12/12 FE)
- iter_7: Browser (15/15 FE)
- iter_6: Comparison (18/18 BE)
- iter_5: Data Hub (24/24 BE)

## Backlog
- Database unification (MongoDB → PostgreSQL)
- Role-based access control
- Live APIs for remaining synthetic sources
- Scheduled sync, Redis caching
