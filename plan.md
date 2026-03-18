# plan.md

## Objectives
- ✅ Deliver a production-ready, high-performance Scenario Calculation Engine (PD/LGD + portfolio metrics + VaR) that runs quickly and deterministically.
- ✅ Replace existing `/api/analysis/run` logic with the new engine while keeping API responses compatible with the current frontend.
- 🔄 Migrate persistence from MongoDB/Beanie to **Supabase PostgreSQL** (TimescaleDB optional) without breaking core user flows.
- ✅ Build a **Portfolio File Upload UI** (frontend) that supports drag-and-drop upload, column mapping, validation review, and import management.
- ⏳ Implement the **backend upload/validation/import APIs** required by the new Upload UI (currently UI is wired to expected endpoints; backend may be incomplete).
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

### Phase 6: Portfolio File Upload UI Components (Status: Completed)
**Scope (frontend)**
Build a comprehensive upload interface for portfolio holdings files with validation, column mapping, and import management. UI is wired to expected backend endpoints.

**User stories**
1. As a portfolio manager, I can drag-and-drop a CSV/XLSX file to upload holdings and see upload progress.
2. As a portfolio manager, I can map file columns to required holding fields using a step-by-step wizard with auto-suggestions and confidence scores.
3. As a portfolio manager, I can review validation results (valid/warning/error), filter issues, and fix errors with inline edits.
4. As a portfolio manager, I can preview data with pagination and row selection before importing.
5. As a portfolio manager, I can track the upload/import lifecycle with clear step descriptions and estimated time remaining.
6. As a portfolio manager, I can view previous imports with statuses and take quick actions.

**New information / constraints**
- Frontend is CRA + React Router; new upload feature implemented in **TypeScript (.ts/.tsx)**.
- Shadcn/UI components are used throughout; icons via `lucide-react`; Sonner for toasts.
- Global fonts updated per design guidelines:
  - Space Grotesk (headings)
  - IBM Plex Sans (body)
  - IBM Plex Mono (mono)
- Avoid `transition-all`; maintain targeted transitions.
- Every interactive and key informational element includes stable `data-testid` attributes.

**Steps (Completed)**
1. **Global styling**
   - ✅ Updated `src/index.css` to import Google Fonts and apply typography rules.
2. **Hooks**
   - ✅ `src/hooks/useFileUpload.ts`:
     - drag/drop + selection
     - file type/size validation
     - upload progress tracking
     - error handling + Sonner notifications
   - ✅ `src/hooks/useColumnMapping.ts`:
     - mapping state management
     - deterministic auto-suggestions + confidence scores
     - template save/load boundaries
3. **Components**
   - ✅ `src/components/upload/FileUploadZone.tsx`
   - ✅ `src/components/upload/UploadProgressTracker.tsx`
   - ✅ `src/components/upload/ColumnMappingWizard.tsx`
   - ✅ `src/components/upload/ValidationResultsPanel.tsx`
   - ✅ `src/components/upload/DataPreviewTable.tsx`
   - ✅ `src/components/upload/ImportHistoryList.tsx`
4. **Pages 6 routing**
   - ✅ `src/pages/UploadPage.tsx`
   - ✅ `src/pages/ReviewPage.tsx`
   - ✅ Added routes in `src/App.js`:
     - `/portfolios/:portfolioId/upload`
     - `/portfolios/:portfolioId/upload/:uploadId/review`
5. **Build verification**
   - ✅ Bundling verification completed (no build errors).

**Deliverables (Completed)**
- ✅ `components/upload/FileUploadZone.tsx`
- ✅ `components/upload/ColumnMappingWizard.tsx`
- ✅ `components/upload/ValidationResultsPanel.tsx`
- ✅ `components/upload/DataPreviewTable.tsx`
- ✅ `components/upload/UploadProgressTracker.tsx`
- ✅ `components/upload/ImportHistoryList.tsx`
- ✅ `hooks/useFileUpload.ts`
- ✅ `hooks/useColumnMapping.ts`
- ✅ `pages/UploadPage.tsx`
- ✅ `pages/ReviewPage.tsx`

**Notes / follow-ups**
- Backend endpoints referenced by the UI must be implemented to enable end-to-end upload:
  - `POST /api/v1/portfolios/{portfolioId}/upload`
  - `GET /api/v1/portfolios/{portfolioId}/uploads`
  - `GET /api/v1/portfolios/{portfolioId}/uploads/{uploadId}/preview`
  - `POST /api/v1/portfolios/{portfolioId}/uploads/{uploadId}/validate`
  - `POST /api/v1/portfolios/{portfolioId}/uploads/{uploadId}/process`
  - Optional templates:
    - `GET/POST /api/v1/mapping-templates`
- Inline editing handlers are scaffolded in UI; backend patch endpoints can be added later.

---

---

### Phase 7: Platform Enhancement Chunks (Status: Completed — Chunks 1-3 + UI)

#### Chunk 1: Data Lineage + Reference Catalog (✅ Completed)
- `services/data_lineage_service.py` — MODULE_SIGNATURES (I/O metadata for all engines) + MODULE_DEPENDENCIES graph
- `services/reference_catalog_service.py` — Embedded reference dataset registry across all engines
- `api/v1/routes/data_lineage.py` + `api/v1/routes/reference_catalog.py`
- `tests/test_data_lineage.py` + `tests/test_reference_catalog.py`

#### Chunk 2: Insurance Risk Engine + 8 Embedded Reference Datasets (✅ Completed — 187 tests)
- `services/insurance_risk_engine.py` — IFRS 17 BBA/PAA/VFA, Solvency II SCR, CAT Risk, Claims Analytics
- `api/v1/routes/insurance_risk.py` — 12 endpoints
- `tests/test_insurance_risk.py` — 87 tests across 8 test classes

#### Chunk 3: Banking Risk Engine + Data Preview UI (✅ Completed — 289 total tests)
- `services/banking_risk_engine.py` — IFRS 9 ECL 3-stage, Basel III/IV capital, LCR/NSFR, FRTB market risk, Op risk, AML/CFT
- `api/v1/routes/banking_risk.py` — 12 endpoints
- `api/v1/routes/data_preview.py` — 5 endpoints (DB schema introspection)
- `frontend/src/pages/DataPreviewPage.jsx` — 3-tab data explorer
- `tests/test_banking_risk.py` — 102 tests across 11 test classes

---

### Phase 8: Climate Physical Risk & ESG Transition Risk Engine (Status: In Progress)

**Spec**: `Climate Physical Risk & ESG Transition Risk Module — Complete Requirements Specification`
**Scope**: 57 configurable parameters, 5 physical risk stages, 6 transition risk stages, 9 pre-calibrated templates, 4-level entity hierarchy

**Integration map**: See `CLIMATE_RISK_INTEGRATION_PLAN.md` for full module-by-module mapping to existing services.

#### Chunk A: Physical Risk Engine + NACE-CPRS Mapper (⏳ In Progress)
**New files**:
- `services/climate_physical_risk_engine.py` (~500 lines) — HEV framework stages 1-4:
  - Stage 1 Hazard: intensity × frequency × duration per hazard/asset/scenario/horizon (7 acute + 6 chronic hazards)
  - Stage 2 Exposure: asset value × exposure fraction × concentration factor
  - Stage 3 Vulnerability: sector base × structural modifiers × adaptation discount × cascading multiplier
  - Stage 4 Damage/CVaR: Σ(H × E × V × DamageFunc) × weight; Linear/Sigmoid/Exponential/Step curves
  - 26 configurable params via PhysicalRiskConfig Pydantic model
  - Embedded: sector vulnerability matrix (20 sectors × 13 hazards), damage function coefficients
- `services/nace_cprs_mapper.py` (~200 lines) — NACE 4-digit → CPRS → IAM mapping (600+ entries), revenue-weighted multi-activity scoring, GHG intensity bucketing
- `tests/test_climate_physical_risk.py` (~300 lines, ~50 tests)

#### Chunk B: Transition Risk Engine (⏳ In Progress — parallel with A)
**New files**:
- `services/climate_transition_risk_engine.py` (~500 lines) — 6-stage orchestrator:
  - Stage 1: Sector classification via NACE-CPRS (calls nace_cprs_mapper)
  - Stage 2: Carbon pricing — Scope1×carbon_price + CBAM_exposure×CBAM_rate + Scope2×elec_uplift
  - Stage 3: Stranded assets — writedown curves (linear/sigmoid/S-curve/step), residual value floor
  - Stage 4: Portfolio alignment gap = current_intensity − pathway_target; transition readiness scoring
  - Stage 5: NGFS scenario stress — TransitionCVaR across 6 Phase 5 scenarios
  - Stage 6: Composite score = Σ(w_cat × CategoryScore) for Policy/Tech/Market/Reputation
  - 26 configurable params via TransitionRiskConfig Pydantic model
  - Embedded: NGFS Phase 5 scenario params, IEA NZE phase-out pathways, TCFD category weights
- `tests/test_climate_transition_risk.py` (~250 lines, ~45 tests)

#### Chunk C: Integrated Risk + Aggregator + Methodology Manager
**New files**:
- `services/climate_integrated_risk.py` (~200 lines) — w_p×Physical + w_t×Transition + α×InteractionTerm; nature risk amplifier
- `services/climate_risk_aggregator.py` (~250 lines) — Asset→Security→Fund→Portfolio roll-up; diversification benefit; contribution analysis
- `services/assessment_methodology_manager.py` (~350 lines) — CRUD lifecycle (DRAFT→PUBLISHED→RETIRED→ARCHIVED), 9 pre-calibrated templates, versioning, validation
- `tests/test_assessment_methodology.py` (~200 lines, ~30 tests)
- `tests/test_climate_integration.py` (~150 lines, ~25 tests)

#### Chunk D: Assessment Runner + API Routes + DB Migration
**New files**:
- `services/assessment_runner.py` (~400 lines) — Orchestrates methodology + entity hierarchy + calculation + storage; batch mode; delta reports
- `api/v1/routes/climate_risk.py` (~300 lines) — 11 endpoints under `/api/v1/climate-risk/`
- `alembic/versions/039_add_climate_risk_assessment_tables.py` — 6 new tables
- Wiring: server.py, data_lineage_service.py updates

#### Chunk E: Frontend Page + Navigation
**New files**:
- `frontend/src/pages/ClimateRiskPage.jsx` (~800 lines) — 6-tab layout: Physical Risk / Transition Risk / Integrated View / Methodology Builder / Assessment Runner / Reports
- App.js wiring: nav entry in "Risk & Sector" group + Route

**Deferred**: PostGIS spatial queries, ML model integration, Celery scheduled runs, Curve/Heatmap editor UI, Geographic Risk Map (Leaflet/Mapbox), auth-gated approval chains

---

### Phase 9: Regulatory & Analytical Engine Expansion (Status: Completed — 2026-03-09)
**Scope**: Build comprehensive regulatory disclosure engines and analytical modules to achieve institutional-grade coverage across all major sustainability/climate frameworks.

#### Completed Engines (all with services + routes + migrations + data lineage)

| # | Engine | Service File | Lines | Routes | Migration | Key Coverage |
|---|--------|-------------|-------|--------|-----------|-------------|
| 1 | EUDR Compliance | eudr_engine.py | ~580 | /api/v1/eudr (13) | 045 | 7 commodities, 63 HS codes, 55 countries, Art 4-12 DD |
| 2 | EU CSDDD | csddd_engine.py | ~520 | /api/v1/csddd (11) | 046 | Art 2/5-13/14/22/29-33, 18 adverse impacts, 9 DD obligations |
| 3 | Sovereign Climate Risk | sovereign_climate_risk_engine.py | ~430 | /api/v1/sovereign-climate-risk (5) | 046 | 51 countries, 5 NGFS, notch adjustment, spread delta |
| 4 | SEC Climate Disclosure | sec_climate_engine.py | ~530 | /api/v1/sec-climate (10) | 047 | Reg S-K 1501-1505, S-X 14-02, filer assessment, attestation |
| 5 | GRI Standards | gri_standards_engine.py | ~470 | /api/v1/gri (9) | 047 | 18 topic standards, 4 sectors, SDG/ESRS mapping |
| 6 | SASB Industry Standards | sasb_industry_engine.py | ~580 | /api/v1/sasb (10) | 048 | SICS 7 sectors, 20 industries, ISSB S2/GRI/ESRS mapping |
| 7 | Model Validation Framework | model_validation_framework.py | ~650 | /api/v1/model-validation (10) | 048 | 17 models, 12 stat tests, BCBS 239/EBA GL, lifecycle |
| 8 | TNFD Nature Disclosures | tnfd_assessment_engine.py | ~1096 | /api/v1/tnfd (11) | 049 | 14 disclosures, LEAP 16 components, ENCORE 21 services |
| 9 | CDP Climate & Water Scoring | cdp_scoring_engine.py | ~1023 | /api/v1/cdp (11) | 049 | 15 climate + 9 water modules, A-D grades, 12 activity groups |
| 10 | PCAF Data Quality Score | pcaf_quality_engine.py | ~1631 | /api/v1/pcaf-quality (11) | 050 | DQS 1-5, 6 asset classes, SFDR PAI 1/2/3, confidence bands |
| 11 | Basel III/IV Regulatory Capital | basel_capital_engine.py | ~1688 | /api/v1/basel-capital (15) | 050 | CRR Art 92/153, IRB, LCR, NSFR, climate add-ons, BCBS 239 |

**Totals**: ~9,198 lines of engine code, ~116 API endpoints, 6 migrations (045-050), ~55 modules in data lineage graph, ~134 dependency edges

#### Previously Completed Engines (Phase 7-8)
- Climate Physical Risk (HEV, 1154 lines) + Transition Risk (NGFS P5, 1345 lines)
- Insurance Risk (IFRS 17 BBA/PAA/VFA, Solvency II SCR, CAT Risk)
- Banking Risk (IFRS 9 ECL, Basel III, LCR/NSFR, FRTB, AML/CFT)
- AM Engine (6 sub-modules: ESG attribution, PACTA, green bonds, spreads, LP analytics, optimisation)
- Agriculture Risk (base + 3 expanded: methane, disease, BNG)
- Factor Overlay (31 registries, 12 overlay methods)
- Technology Risk, Residential RE, RICS ESG, EU ETS, Stress Testing
- Cross-Module Lineage Orchestrator, Regulatory Report Compiler

---

### Phase 10: Remaining Analytical Engines (Status: COMPLETE — 2026-03-09)
**Scope**: Final analytical engine modules to complete platform coverage.

#### Completed
- **EU Taxonomy Alignment Engine** — All 4 Delegated Acts (Climate 2021/2139, Complementary 2022/1214, Environmental 2023/2486, Amendments 2023/2485), 80+ NACE activities, 6 environmental objectives, Article 3 three-step test, DNSH 6x6, Minimum Safeguards, GAR/BTAR financial KPIs, 10 cross-framework mappings. Service ~600 lines, 3 POST + 10 GET endpoints, migration 051.
- **Climate Transition Plan Assessment Engine** — TPT (5 elements, 16 sub-elements), GFANZ (7 components + 4 sub-alliances), IIGCC NZIF v2 (7 steps), CSDDD Art 22 (8 requirements + phase-in), CSRD ESRS E1 (E1-1 to E1-10, ~60 datapoints), CDP C4 (C4.1-C4.5 + C1/C3), 55-datapoint inter-framework cross-mapping, 8 sector pathways. Service ~800 lines, 5 POST + 12 GET endpoints, migration 051.

#### Remaining (Lower Priority)
- PostGIS spatial queries for nature risk (infrastructure)
- TimescaleDB hypertables for time-series KPIs (infrastructure)
- Auth/RBAC enforcement (deferred per Phase 3 decision)
- Frontend pages for new engines (backend-first approach)

---

## Next Actions
1. ✅ Phase 7 Chunks 1-3 completed (289 tests passing)
2. ✅ Phase 8 Chunks A-E completed (climate risk engine — physical, transition, integrated, aggregator, methodology, runner, frontend)
3. ✅ Phase 9 completed (11 regulatory/analytical engines, 050 migrations, ~55 lineage modules)
4. ✅ Phase 10 complete (EU Taxonomy + Transition Plan engines — 2026-03-09)
5. ✅ Phase 11 complete (Double Materiality DMA + SFDR PAI engines + 6 frontend pages wired + digital skeleton theme — 2026-03-09)
6. Phase 3 (Postgres migration — deferred, DB structure stable)
7. After stabilization: Revisit authentication

---

## Success Criteria
- ✅ Engine POC script runs successfully and produces complete metrics for scenario×horizon with stable outputs.
- ✅ `/api/analysis/run` uses the new engine and the frontend Results/Runs pages work unchanged.
- 🔄 Postgres migration POC proves: schema works, queries are efficient, and one analysis can be persisted.
- 🔜 Full app runs on Postgres with parity for: portfolios, scenario-data, analysis runs, and results retrieval.
- ✅ Upload UI provides an audit-friendly end-to-end user workflow (upload → map → validate → preview/edit → import) **once backend endpoints are available**, with clear progress feedback and comprehensive `data-testid` coverage.
- ✅ Platform enhancement chunks 1-3 pass 289 tests (data lineage, insurance risk, banking risk, data preview).
- ✅ Climate risk engine completed — physical risk (5 stages), transition risk (6 stages), integrated scoring, methodology lifecycle, assessment runner, frontend 6-tab page.
- ✅ Phase 9 regulatory engines: 11 engines, ~9,198 lines, ~116 endpoints, 6 migrations applied to Supabase.
- ✅ Phase 10: EU Taxonomy Alignment (~600 lines, 80+ NACE activities, 4 Delegated Acts) + Climate Transition Plan Assessment (~800 lines, 55-datapoint cross-mapping, 6 frameworks). Migration 051 applied. ~57 lineage modules, ~149 dependency edges.
- ✅ Phase 11: Double Materiality Engine (~1525 lines, 10 ESRS topics, EFRAG IG 1) + SFDR PAI Engine (~2044 lines, 18 mandatory + 38 optional indicators, Art 6/8/9 classification). Migration 052 applied. 6 frontend hub pages wired. Digital skeleton white/black theme across 122+ files. ~59 lineage modules, ~164 dependency edges.
- Automated tests pass; one end-to-end regression run completes without manual fixes.
