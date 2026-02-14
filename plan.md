# plan.md

## 1) Objectives
- Deliver an MVP Portfolio Scenario Analysis module that ingests **real NGFS climate scenario data**, stores it as time-series in **PostgreSQL + TimescaleDB**, and runs **multi-method** climate-to-credit analytics on portfolios of **asset-level exposures** (bonds/loans/equity) aggregated to company/sector/portfolio.
- Produce scenario outputs for **Orderly / Disorderly / Hot House World** across **2030/2040/2050** with metrics: **Expected Loss & risk-adjusted returns**, **PD changes & rating migrations**, **VaR / stress tests / concentration risk**.
- Provide a React dashboard with Recharts for scenario comparisons and drill-downs (portfolio → sector → company → asset).
- Ship full local dev setup (Docker compose), tests, linting, OpenAPI docs, and a clear README.

## 2) Implementation Steps

### Phase 1 — Core POC (isolation): climate data + scenario engine (no auth)
**Goal:** prove the hardest parts work end-to-end: external scenario data → normalized storage → analytics run → reproducible outputs.

**User stories (POC)**
1. As a risk analyst, I can fetch NGFS scenario variables for a sector and verify coverage for 2030/2040/2050.
2. As a developer, I can persist scenario time-series into TimescaleDB and query efficiently by scenario/variable/horizon.
3. As a risk analyst, I can run a portfolio through 3 methodologies and get consistent, explainable results.
4. As a risk analyst, I can reproduce the same result given the same inputs (versioned scenario dataset + parameters).
5. As a QA, I can run a single command to execute the POC script and see a pass/fail summary.

**Steps**
- Web research + decision: pick external climate data sources (target: NGFS scenario dataset API/file endpoints; fallback: IIASA NGFS public data download + scripted refresh).
- Write `scripts/poc_climate_ingest.py`:
  - download/refresh NGFS data (min set of variables needed: e.g., GDP, carbon price, energy mix, emissions; map to sectors via lookup).
  - normalize to schema: `(scenario, model, region, variable, unit, year, value, source_version)`.
  - load into Timescale hypertable with idempotent upsert.
- Write `scripts/poc_risk_engine.py`:
  - define small synthetic portfolio (assets→companies→sectors) with EAD/market value, base PD/LGD, rating.
  - implement 3 methods (MVP versions):
    1) Sector risk multipliers by (scenario,horizon,sector)
    2) PD adjustment function using scenario drivers (e.g., carbon price/GDP deltas) with caps/floors
    3) Expected Loss: `EL = EAD * PD * LGD` + return impact using spread/discount shock
  - rating migration: map PD bands to rating buckets and show transitions.
  - compute VaR (historical/simulated) using scenario shock distributions; add simple stress test (worst-case horizon).
  - concentration: HHI / top-N exposures by sector/company.
- POC acceptance gate (do not proceed until green):
  - ingestion retrieves real NGFS dataset and stores/query returns expected rows.
  - engine runs all scenarios/horizons and outputs a JSON report with all metric families.
  - pytest “contract tests” for calculations (monotonicity sanity checks; bounds).

### Phase 2 — V1 App Development (core app, no auth yet)
**Goal:** build working product around proven core; minimal but complete UX.

**User stories (V1)**
1. As a user, I can create a portfolio and upload/add assets (bond/loan/equity) linked to a company and sector.
2. As a user, I can run scenario analysis for my portfolio and see results for 2030/2040/2050.
3. As a user, I can compare Orderly vs Disorderly vs Hot House in charts and a results table.
4. As a user, I can drill down from portfolio → sector → company → asset to see drivers and contributions.
5. As a user, I can export results (JSON/CSV) for reporting.

**Backend (FastAPI)**
- Repository structure with app-factory:
  - `app/main.py` (factory), `app/api/v1/*`, `app/core/*`, `app/models/*`, `app/schemas/*`, `app/services/*`.
- DB schema (SQLAlchemy): Users (later), Portfolios, Companies, Assets, ScenarioDatasets, ScenarioSeries, AnalysisRun, AnalysisResult.
- TimescaleDB:
  - hypertable for scenario series; optional hypertable for analysis outputs by run/time.
- Services:
  - `climate_data_service` (refresh/query), `risk_engine_service` (wrap POC engine), `aggregation_service`.
- API endpoints (v1):
  - CRUD: portfolios/companies/assets
  - Scenario data: list datasets/variables, refresh
  - Analysis: create run, get run status, fetch results (portfolio/sector/company/asset views)
- OpenAPI documented responses + Pydantic v2 models.

**Frontend (React/Vite)**
- Pages: Portfolio list/create, Portfolio detail (holdings grid), Scenario Analysis runner, Results dashboard.
- Components: scenario selector, horizon tabs, drilldown breadcrumb, charts (Recharts), tables.
- State/data: TanStack Query for API calls; form validation.
- UX: loading/error/empty states for every query.

**DevOps/Tooling**
- `docker-compose.yml`: api + web + postgres(timescaledb) + migration job.
- Alembic migrations.
- Pre-commit: black, ruff, eslint.
- Tests: pytest for services/routes; Vitest + RTL smoke tests for pages.

**Phase 2 checkpoint testing**
- Run docker compose; create portfolio + assets; run analysis; verify charts render; export works.

### Phase 3 — Auth + multi-user + permissions (and hardening)
**Goal:** add multi-user isolation last (auth complicates testing).

**User stories (Auth)**
1. As a user, I can sign up/sign in and only see my portfolios.
2. As a user, I can reset my password and regain access.
3. As an admin, I can deactivate a user.
4. As a user, I can share a portfolio read-only with another user.
5. As a user, I can audit my analysis runs history.

**Steps**
- JWT auth (access/refresh), password hashing, user tables.
- Row-level scoping in queries (owner_id; optional sharing table).
- Frontend auth flows, protected routes.
- Add rate limits + request validation; background job for long runs (RQ/Celery-lite) if needed.
- E2E test pass for multi-user isolation.

### Phase 4 — Production polish (performance, governance, observability)
**User stories (Polish)**
1. As a user, I can schedule scenario data refresh and see dataset versions.
2. As a model risk user, I can view methodology parameters and provenance for every run.
3. As a user, I can download a PDF/HTML report.
4. As an operator, I can monitor API health and slow queries.
5. As a user, I can handle large portfolios without timeouts.

**Steps**
- Dataset/version governance (source hash, effective date, changelog).
- Caching for scenario queries; indexes/continuous aggregates in Timescale.
- Observability: structured logs, metrics endpoint.
- Load/perf tests on aggregation + analysis.

## 3) Next Actions
1. Confirm preferred NGFS source: direct API vs public download mirror (I’ll implement both with fallback).
2. Define minimal variable set for POC (carbon price, GDP, emissions/energy) and region scope (e.g., World + EU + US).
3. Implement Phase 1 scripts + Timescale schema and run until POC gates are green.
4. Once POC is stable, scaffold repos (backend/frontend), wire end-to-end V1, then add auth.

## 4) Success Criteria
- POC: real NGFS data successfully ingested; scenario queries fast; risk engine outputs complete metrics for all scenarios/horizons with repeatability.
- V1: user can create portfolio/assets, run analysis, drill down results, and export.
- Auth: multi-user isolation verified; sharing works (if enabled).
- Quality: docker-compose up works; tests pass; lint hooks pass; OpenAPI docs accurate; README enables clean setup.
