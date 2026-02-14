# plan.md

## Objectives
- ✅ Deliver a production-ready, high-performance Scenario Calculation Engine (PD/LGD + portfolio metrics + VaR) that runs quickly and deterministically.
- 🔄 Replace existing `/api/analysis/run` logic with the new engine while keeping API responses compatible with the current frontend.
- 🔜 Migrate persistence from MongoDB/Beanie to PostgreSQL (+ TimescaleDB where it actually adds value) without breaking core user flows.
- ⏳ Defer authentication until after core engine integration + DB migration are stable.

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
- VaR now uses deterministic seeding for reproducibility.

---

### Phase 2: Integration into API Endpoints (Status: Not Started)
**User stories**
1. As a user, I can run analysis from the UI and see results without API errors.
2. As a user, I see results for each scenario+horizon with EL, EL%, VaR, HHI, and rating migrations.
3. As a user, rerunning analysis with the same inputs produces consistent results.
4. As a user, empty portfolios or missing scenario data show clear error messages.
5. As a user, analysis runs are saved and retrievable from “Runs” history.

**Steps (Revised)**
- Replace logic in `server.py:/api/analysis/run`:
  - Build scenario selection/horizon loop from request payload (`AnalysisRequest` currently uses `scenarios` + `horizons`).
  - Convert `Portfolio.assets` into `AssetInput` objects (mapping sector, exposure, base_pd/base_lgd, plus reasonable defaults for optional climate fields).
  - Call `ClimateRiskCalculationEngine.calculate_multiple_scenarios()` (or loop `calculate_scenario()`).
  - Map output to existing `AnalysisRun` + `ScenarioResult` models used by the current frontend:
    - expected_loss, expected_loss_pct
    - var_95 (and optionally persist var_99 / ES fields for future UI)
    - concentration_hhi (use `sector_hhi` to maintain semantic compatibility)
    - avg_pd_change_pct
    - risk_adjusted_return
    - rating_migrations
    - total_exposure
- Maintain backwards compatibility:
  - Keep response JSON shape stable for current React pages (`Results`, `Analysis`, `Runs`).
  - If adding new fields (VaR99, ES), make them additive (non-breaking).
- Add tests:
  - Unit tests for the new mapping layer (Portfolio→AssetInput; Engine→ScenarioResult).
  - One API-level test for `/api/analysis/run` ensuring successful run and persisted `AnalysisRun`.
- Run end-to-end smoke test from frontend:
  - Generate sample data → run analysis → open results page.

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
- Add SQLAlchemy 2.x + Alembic (or equivalent migration tooling).
- Create initial schema + migrations for:
  - portfolios, assets/holdings
  - scenario_series (candidate hypertable)
  - analysis_runs, scenario_results
- Create minimal `backend/scripts/pg_poc.py`:
  - Insert scenario_series rows; query by scenario+year+region+variable.
  - Insert portfolio+assets; read back; run engine on loaded data.
  - Persist one analysis run + results.
- Decide Timescale scope:
  - Use hypertable for `scenario_series` if it materially improves query patterns.

---

### Phase 4: Data Layer Migration (Status: Not Started)
**User stories**
1. As a user, I can create/edit/delete portfolios and assets with no behavioral change.
2. As a user, scenario-data refresh populates Postgres and the Scenario Data page still works.
3. As a user, analysis runs history persists and results load correctly.
4. As an operator, I can run a one-time migration from existing Mongo data.
5. As a developer, I can run all tests against Postgres in CI/local.

**Steps**
- Introduce a repository/service layer for persistence (portfolios/scenarios/analysis) to decouple API from ODM/ORM.
- Switch endpoints to repositories backed by SQLAlchemy.
- Implement one-time migration script: Mongo → Postgres (best-effort; preserve IDs).
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
- Ensure deterministic seeding for VaR simulation is consistent end-to-end.
- Add validation:
  - Clamp PD/LGD.
  - Handle missing scenario params with explicit defaults + warnings.
- Expand tests: golden-file style outputs for the sample portfolio.

---

## Next Actions
1. Integrate `ClimateRiskCalculationEngine` into `server.py:/api/analysis/run` (replace legacy `risk_engine.py` usage).
2. Keep response contract stable for frontend; add new fields only additively.
3. Add unit + API test coverage for the integration path.
4. Run UI smoke test on sample portfolio.
5. Begin Postgres/TimescaleDB setup (Phase 3) immediately after API integration is stable.

---

## Success Criteria
- ✅ Engine POC script runs successfully and produces complete metrics for scenario×horizon with stable outputs.
- `/api/analysis/run` uses the new engine and the frontend Results/Runs pages work unchanged.
- Postgres migration POC proves: schema works, scenario queries are efficient, and one analysis can be persisted.
- Full app runs on Postgres with parity for: portfolios, scenario-data, analysis runs, and results retrieval.
- Automated tests pass; one end-to-end regression run completes without manual fixes.
