# A2 Intelligence by AA Impact Inc. — Climate Risk Analytics Platform

## Architecture
- Backend: FastAPI + **PostgreSQL only** (Supabase)
- Frontend: React + shadcn/ui + Recharts + Zustand
- Auth: Google OAuth (Emergent) + JWT — PostgreSQL
- Data: IIASA (real) + 20 sources + 24 NGFS + custom scenarios

## All Tests (14 iterations, 280+ tests, 100% pass rate)
- iter_14: Enhanced Sub-Parameter (54/54 BE, all FE)
- iter_13: Sub-Parameter (30/30 BE)
- iter_12: Custom Builder (23/23 BE)
- iter_11: NGFS (29/29 BE)
- iter_10: Auth (12/12 BE)
- iter_9-5: Reports, Impact, Browser, Comparison, Hub

## Latest: Enhanced Sub-Parameter Analysis
- 7 calculation methods: Tornado, Elasticity, Partial Correlation, OLS Regression, Shapley Values, What-If, Attribution
- Export to Excel/PDF/JSON
- Scenario Builder integration (auto-analysis + key drivers)
- Frontend: 7-tab dashboard with charts for each method
