# Climate Credit Risk Intelligence Platform - PRD

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) + MongoDB
- Frontend: React + shadcn/ui + Recharts + Zustand
- Auth: Google OAuth (Emergent) + JWT
- Data: IIASA (real) + 20 hub sources + 24 NGFS dedicated

## Pages (15 routes, all auth-gated)
| Route | Page | Test |
|-------|------|------|
| `/` | Dashboard | Done |
| `/portfolios` | Portfolios | Done |
| `/analysis` | Run Analysis | Done |
| `/scenario-data` | Scenario Data | Done |
| `/scenario-builder` | Legacy Builder | Done |
| `/data-hub` | Data Hub (20 sources, 102 scenarios) | iter_5 |
| `/browser` | Scenario Browser | iter_7 |
| `/comparison` | Comparison & Gap Analysis | iter_6 |
| `/impact` | Impact Calculator + Reports | iter_9 |
| `/portfolio-manager` | Portfolio Upload + Editor | iter_8 |
| `/alerts` | Alerts | Done |
| `/ngfs` | NGFS Catalog (24 scenarios) | iter_11 |
| `/custom-builder` | Custom Builder | iter_12 |
| `/sub-analysis` | **Sub-Parameter Analysis** | **iter_13** |

## Latest: Sub-Parameter Analysis (Feb 14, 2026)
- Sensitivity analysis: tornado charts showing which parameters drive most impact
- What-if testing: change parameter, compare baseline vs modified with insights
- Shapley attribution: parameter contribution percentages to outcome
- Pairwise interaction analysis: synergistic/antagonistic/independent classification
- Visualization endpoints: tornado, waterfall chart data
- Testing: 30/30 BE + all FE (iteration_13)

## All Tests (13 iterations, 230+ tests)
iter_13: Sub-Parameter (30/30), iter_12: Custom Builder (23/23), iter_11: NGFS (29/29),
iter_10: Auth (12/12), iter_9: Reports (11/11), iter_8: Impact (15/15),
iter_7: Browser (15/15), iter_6: Comparison (18/18), iter_5: Hub (24/24)
