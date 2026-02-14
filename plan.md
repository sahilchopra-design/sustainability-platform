# plan.md

## Objectives
- ✅ Deliver a production-ready, high-performance Scenario Calculation Engine (PD/LGD + portfolio metrics + VaR) that runs quickly and deterministically.
- ✅ Replace existing `/api/analysis/run` logic with the new engine while keeping API responses compatible with the current frontend.
- 🔄 Migrate persistence from MongoDB/Beanie to **Supabase PostgreSQL** (TimescaleDB optional) without breaking core user flows.
- ⏳ Defer authentication until after DB migration and post-migration stabilization.

---

## Implementation Phases

### Phase 1: Complete Calculation Engine (Status: Completed)
**User stories**
1. As a risk analyst, I can run PD/LGD adjustments for a list of assets for a given scenario+horizon and get stable outputs.
2. As a risk analyst, I can compute portfolio expected loss from adjusted PD/LGD and EAD.
3. As a risk analyst, I can compute VaR(95/99) from simulated/bootstrapped loss distribution.
4. As a developer, I can run the engine locally via a single script and see performance stats (runtime, vectorization).
5. As a product owner, I can validate outputs against the legacy `risk_engine.py` directionally (not identical) on the sample portfolio.

**Steps (Completed)**
- ✅ Added missing engine modules in `backend/services/`:
  - ✅ `var_calculator.py` (Monte Carlo + parametric VaR95/VaR99 + Expected Shortfall)
  - ✅ `portfolio_metrics.py` (EL, EL%, risk-adjusted return proxy, HHI, rating migrations, sector breakdown)
  - ✅ `calculation_engine.py` orchestrator to run scenario×horizon loops and aggregate results
- ✅ Implemented POC script `backend/scripts/engine_poc.py`:
  - ✅ Loads sample portfolio from MongoDB (`climate_risk_platform`)
  - ✅ Pulls scenario inputs from `ScenarioSeries`
  - ✅ Runs multiple scenarios × horizons, prints metrics and timing, saves JSON output
- ✅ Validated engine quality and performance:
  - ✅ Outputs bounded/consistent (PD/LGD in [0,1], VaR ordering checks, no NaNs)
  - ✅ Performance acceptable (~48ms for 6 scenario-horizon combinations on sample portfolio)
  - ✅ Directional agreement with legacy engine on EL (within ~10–28%)
  - ✅ VaR is materially more realistic (Monte Carlo loss distribution vs single-asset percentile)

**Notes**
- PD/LGD calculators remain the “single source of truth” for adjustments.
- VaR uses deterministic seeding for reproducibility.

---

### Phase 2: Integration into API Endpoints (Status: Completed)
**User stories**
1. As a user, I can run analysis from the UI and see results without API errors.
2. As a user, I see results for each scenario+horizon with EL, EL%, VaR, HHI, and rating migrations.
3. As a user, rerunning analysis with the same inputs produces consistent results.
4. As a user, empty portfolios or missing scenario data show clear error messages.
5. As a user, analysis runs are saved and retrievable from “Runs” history.

**Steps (Completed)**
- ✅ Implemented engine integration/mapping layer:
  - ✅ Added `backend/services/engine_integration.py` with:
    - Asset → `AssetInput` mapping (with heuristic defaults for emissions/transition/physical risk)
    - `ScenarioHorizonResult` → `ScenarioResult` mapping for backwards-compatible API responses
  - ✅ Added `backend/services/__init__.py` to formalize services package
- ✅ Replaced `/api/analysis/run` logic in `backend/server.py`:
  - ✅ Removed dependency on legacy `RiskEngine` in the request path
  - ✅ Invokes `ClimateRiskCalculationEngine.calculate_multiple_scenarios()`
  - ✅ Persists `AnalysisRun` with `ScenarioResult` records as before
  - ✅ Maintains existing response JSON shape used by the React app
- ✅ Validation:
  - ✅ Tested `/api/analysis/run` via `curl` (correct fields + plausible values)
  - ✅ Frontend smoke test confirms key pages load correctly:
    - Dashboard, Portfolios, Portfolio Detail, Analysis, Results
  - ✅ Analysis runs complete successfully and results display

**Notes**
- The new engine is now the production implementation behind `/api/analysis/run`.
- Any future additions (e.g., VaR99/ES exposure in UI) should be additive to avoid breaking frontend.

---

### Phase 3: PostgreSQL Migration Setup (Status: In Progress)
**User stories**
1. As a developer, I can connect the FastAPI backend to **Supabase PostgreSQL**.
2. As a developer, I can create/read a portfolio with assets persisted in Postgres.
3. As a developer, I can store scenario time-series in Postgres (Timescale optional).
4. As a developer, I can run one analysis and persist the run + results in Postgres.
5. As a user, I can still use the app normally after switching DB.

**New information / constraints**
- Target Postgres is Supabase pooled endpoint:
  - `postgresql://postgres.kytzcbipsghprsqoalvi:[PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres`
- Password contains special characters and must be **URL-encoded** when used in `DATABASE_URL`.
  - Example: `Zeek@@2025@@` → `Zeek%40%402025%40%40`

**Steps (Revised / Execution-Ready)**
- Dependencies
  - Add SQLAlchemy 2.x
  - Add Alembic
  - Choose driver:
    - Prefer sync `psycopg` (psycopg3) for simplest integration, or
    - Use async (`asyncpg`) if we refactor DB IO to async.
- Configuration
  - Add `DATABASE_URL` env var (URL-encoded password)
  - Add SQLAlchemy engine/session factory
  - Add an application setting to switch DB backend (Mongo vs Postgres) during rollout.
- Schema & migrations (Alembic)
  - Create initial tables mirroring current Mongo models:
    - `portfolios`
    - `assets` (FK to `portfolios`)
    - `scenario_series`
    - `analysis_runs`
    - `scenario_results` (FK to `analysis_runs`)
  - Decide normalization:
    - store `analysis_runs.scenarios`/`analysis_runs.horizons` as JSON or ARRAY (Postgres supports both)
    - keep results normalized in `scenario_results`
- TimescaleDB decision (Supabase)
  - Confirm whether TimescaleDB extension is available/enabled on the project.
  - If not available, keep `scenario_series` as a standard Postgres table with proper indexes.
- POC
  - Create `backend/scripts/pg_poc.py`:
    - connect using `DATABASE_URL`
    - create/read portfolio + assets
    - insert/query `scenario_series` by (scenario, variable, region, year)
    - persist one `analysis_run` + `scenario_results`

**Deliverables**
- `backend/db/postgres.py` (engine/session)
- `backend/db/models_sql.py` (SQLAlchemy models)
- `alembic/` migrations
- `backend/scripts/pg_poc.py`

---

### Phase 4: Data Layer Migration (Status: Not Started)
**User stories**
1. As a user, I can create/edit/delete portfolios and assets with no behavioral change.
2. As a user, scenario-data refresh populates Postgres and the Scenario Data page still works.
3. As a user, analysis runs history persists and results load correctly.
4. As an operator, I can run a one-time migration from existing Mongo data.
5. As a developer, I can run all tests against Postgres in CI/local.

**Steps (Revised)**
- Introduce a repository/service layer for persistence (portfolios/scenarios/analysis) so endpoints are DB-agnostic.
- Implement Postgres-backed repositories using SQLAlchemy.
- Switch FastAPI endpoints to use repositories.
- Implement one-time migration tool (Mongo → Postgres):
  - Export from Mongo collections: `portfolios`, `scenario_series`, `analysis_runs`
  - Transform embedded arrays (Mongo `Portfolio.assets`) into relational `assets` rows
  - Import into Postgres preserving IDs where feasible
  - Verify referential integrity and record counts
- Cutover
  - Run with Postgres as primary, keep Mongo as fallback until stable.
  - Remove Beanie initialization and Mongo-only code after parity is proven.

---

### Phase 5: Testing & Verification (Status: Not Started)
**User stories**
1. As a user, analysis completes fast enough for interactive use on larger portfolios.
2. As a user, failures are actionable (missing scenario points, invalid inputs).
3. As a user, results are numerically stable and bounded.
4. As an operator, I can observe timings and error rates.
5. As a developer, I can change calculators without breaking API contracts.

**Steps (Revised)**
- Add regression tests for `/api/analysis/run` ensuring:
  - Correct persistence into Postgres
  - Backwards compatible API response shape
  - Deterministic VaR results with fixed seed
- Add DB-level tests:
  - migrations apply cleanly
  - indexes exist for core query patterns (scenario lookup)
- Add data validation and explicit defaults/warnings for missing scenario points.
- Add performance instrumentation:
  - per scenario/horizon timings
  - VaR simulation timings
- Add “golden” output fixtures for sample portfolio to detect unintended changes.

---

## Next Actions
1. Phase 3 (now):
   - Add SQLAlchemy + Alembic dependencies
   - Add Supabase `DATABASE_URL` (URL-encoded password)
   - Create SQLAlchemy models + initial migration
   - Run `pg_poc.py` to validate connectivity + persistence
2. Phase 4:
   - Build repository layer
   - Migrate endpoints from Mongo/Beanie → Postgres/SQLAlchemy
   - Run Mongo → Postgres migration script
3. Phase 5:
   - Full regression + performance validation
4. After stabilization:
   - Revisit authentication

---

## Success Criteria
- ✅ Engine POC script runs successfully and produces complete metrics for scenario×horizon with stable outputs.
- ✅ `/api/analysis/run` uses the new engine and the frontend Results/Runs pages work unchanged.
- 🔄 Postgres migration POC proves: schema works, queries are efficient, and one analysis can be persisted.
- 🔜 Full app runs on Postgres with parity for: portfolios, scenario-data, analysis runs, and results retrieval.
- Automated tests pass; one end-to-end regression run completes without manual fixes.
