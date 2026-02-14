# A2 Intelligence by AA Impact Inc.

## Architecture
- Backend: FastAPI + PostgreSQL (Supabase) — unified single DB
- Frontend: React + shadcn/ui + Recharts + Zustand
- Auth: Google OAuth + JWT — PostgreSQL
- Data: IIASA (real) + 20 sources + 24 NGFS + CBAM

## Pages (16 routes)
| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/impact` | Impact Calculator + Reports |
| `/sub-analysis` | Sub-Parameter Analysis (7 methods) |
| `/cbam` | **CBAM Module** |
| `/browser` | Scenario Browser |
| `/data-hub` | Data Hub (20 sources) |
| `/ngfs` | NGFS Catalog (24 scenarios) |
| `/comparison` | Comparison & Gap Analysis |
| `/custom-builder` | Custom Builder |
| `/portfolios` | Portfolios |
| `/portfolio-manager` | Upload & Edit |
| `/analysis` | Run Analysis |
| `/alerts` | Alerts |

## Latest: CBAM Module
- 8 PostgreSQL tables for product categories, suppliers, emissions, projections, compliance, country risk, certificate prices, verifiers
- 15 EU CBAM product categories (Cement, Iron & Steel, Aluminium, Fertilizers, Electricity, Hydrogen) with default emission factors
- 20 country risk profiles with carbon pricing data
- Cost projection engine: EU ETS price × emissions - domestic credit - free allocation
- 3 ETS price scenarios (Current Trend, Ambitious, Conservative) with 2025-2050 projections
- Free allocation phase-out schedule (97.5% in 2026 → 0% in 2034)
- Testing: 34/34 BE + all FE (iteration_15)

## All Tests (15 iterations, 310+ tests, 100% pass)
