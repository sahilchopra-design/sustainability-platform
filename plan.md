# plan.md

## Objectives
- Deliver a production-ready, high-performance Scenario Calculation Engine (PD/LGD + portfolio metrics + VaR) that can run on realistic portfolios quickly and deterministically.
- Replace existing `/api/analysis/run` logic with the new engine while keeping API responses compatible with the current frontend.
- Migrate persistence from MongoDB/Beanie to PostgreSQL (+ TimescaleDB where it actually adds value) without breaking core user flows.
- Defer authentication until after core engine + DB migration are stable.

---

## Implementation Phases

### Phase 1: Complete Calculation Engine (Status: In Progress)
**User stories**
1. As a risk analyst, I can run PD/LGD adjustments for a list of assets for a given scenario+horizon and get stable outputs.
2. As a risk analyst, I can compute portfolio expected loss from adjusted PD/LGD and EAD.
3. As a risk analyst, I can compute VaR(95/99) from simulated/bootstrapped loss distribution.
4. As a developer, I can run the engine locally via a single script and see performance stats (runtime, vectorization).
5. As a product owner, I can validate outputs against the legacy `risk_engine.py` directionally (not identical) on the sample portfolio.

**Steps**
- Add missing engine modules in `backend/services/`:
  - `var_calculator.py` (loss distribution + VaR95/VaR99)
  - `portfolio_metrics.py` (EL, EL%, risk-adjusted return proxy, HHI)
  - `engine.py` orchestrator to run scenario×horizon loops and aggregate results
- Implement a minimal **POC script** (e.g., `backend/scripts/engine_poc.py`):
  - Load sample portfolio from DB (current Mongo) or from a JSON fixture
  - Pull scenario params (carbon price, GDP index) from ScenarioSeries
  - Run engine for 1–2 scenarios × 1–2 horizons; print JSON and timings
- Iterate until:
  - Outputs are consistent, bounded (0..1), and no NaNs
  - Runtime acceptable on sample portfolio (define target)

**Notes**
- Keep PD/LGD calculators as the “single source of truth” for adjustments.
- Prefer vectorized/batch paths for PD/LGD and loss simulation.

---

### Phase 2: Integration into API Endpoints (Status: Not Started)
**User stories**
1. As a user, I can run analysis from the UI and see results without API errors.
2. As a user, I see results for each scenario+horizon with EL, EL%, VaR, HHI, and rating migrations.
3. As a user, rerunning analysis with the same inputs produces consistent results.
4. As a user, empty portfolios or missing scenario data show clear error messages.
5. As a user, analysis runs are saved and retrievable from “Runs” history.

**Steps**
- Replace logic in `server.py:/api/analysis/run`:
  - Build scenario_params from `ScenarioSeries`
  - Call new orchestrator engine
  - Map engine output into existing `AnalysisRun` + `ScenarioResult` models (keep frontend-compatible fields)
- Add unit tests for calculators + orchestrator; add one API-level test for `/api/analysis/run`.
- Run end-to-end smoke test from frontend (sample data → run analysis → view results).

---

### Phase 3: PostgreSQL Migration Setup (Status: Not Started)
**User stories**
1. As a developer, I can start Postgres+Timescale locally and connect from FastAPI.
2. As a developer, I can create/read a portfolio with assets persisted in Postgres.
3. As a developer, I can store scenario time-series in a table optimized for time queries.
4. As a developer, I can run one analysis and persist the run + results in Postgres.
5. As a user, I can still use the app normally after switching DB.

**Steps**
- Add Postgres service + env vars; enable Timescale extension.
- Create SQLAlchemy models + Alembic migrations for:
  - portfolios, assets (or holdings), scenario_series (candidate hypertable), analysis_runs, scenario_results
- Write a minimal `backend/scripts/pg_poc.py`:
  - Insert scenario_series rows, query by scenario+year+region+variable
  - Insert portfolio+assets, read back, run engine on loaded data
- Decide Timescale scope:
  - Use hypertable for `scenario_series` only if queries benefit (year/time dimension); otherwise plain Postgres.

---

### Phase 4: Data Layer Migration (Status: Not Started)
**User stories**
1. As a user, I can create/edit/delete portfolios and assets with no behavioral change.
2. As a user, scenario-data refresh populates Postgres and the Scenario Data page still works.
3. As a user, analysis runs history persists and results load correctly.
4. As an operator, I can run a one-time migration from existing Mongo data.
5. As a developer, I can run all tests against Postgres in CI/local.

**Steps**
- Introduce repository/service layer for persistence (portfolios/scenarios/analysis) to decouple API from ODM/ORM.
- Switch endpoints to repositories backed by SQLAlchemy.
- Implement one-time migration script: Mongo → Postgres (best-effort; id mapping preserved).
- Remove/disable Mongo dependencies after parity achieved.
- End-to-end regression test all core flows.

---

### Phase 5: Testing & Verification (Status: Not Started)
**User stories**
1. As a user, analysis completes fast enough for interactive use on larger portfolios.
2. As a user, failures are actionable (missing scenario points, invalid inputs).
3. As a user, results are numerically stable and bounded.
4. As an operator, I can observe timings and error rates.
5. As a developer, I can change calculators without breaking API contracts.

**Steps**
- Add basic performance instrumentation (timings per scenario/horizon, batch sizes).
- Add deterministic seeding for VaR simulation.
- Add validation: clamp PD/LGD, handle missing scenario params with explicit defaults + warnings.
- Expand tests: golden-file style outputs for sample portfolio.

---

## Next Actions
1. Implement `engine.py` orchestrator + `var_calculator.py` + `portfolio_metrics.py`.
2. Add `backend/scripts/engine_poc.py` and run it against generated sample data.
3. Integrate orchestrator into `/api/analysis/run` and run UI smoke test.
4. Stand up Postgres+Timescale, add Alembic, and run `pg_poc.py` to validate schema + core queries.

---

## Success Criteria
- Engine POC script runs successfully and produces complete metrics for scenario×horizon with stable outputs.
- `/api/analysis/run` uses the new engine and the frontend Results/Runs pages work unchanged.
- Postgres migration POC proves: schema works, scenario queries are efficient, and one analysis can be persisted.
- Full app runs on Postgres with parity for: portfolios, scenario-data, analysis runs, and results retrieval.
- Automated tests pass; one end-to-end regression run completes without manual fixes.
