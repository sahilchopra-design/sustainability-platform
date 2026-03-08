# Phase 3: Asset Manager Completions
## Product Documentation — User Guide, Value Propositions & User Stories

---

## Phase Overview

| Attribute | Detail |
|-----------|--------|
| Phase | 3 — Asset Manager Completions |
| Sessions | 3A (Fund Structure + Holdings Analytics), 3B (ESG Attribution + Benchmark Analytics), 3C (SFDR Periodic Report + Exclusion Screening) |
| Tests | 93/93 passed (37 + 29 + 27) |
| API Prefix | `/api/v1/fund-management`, `/api/v1/attribution-benchmark`, `/api/v1/sfdr-exclusion` |
| Regulatory Alignment | SFDR (EU 2019/2088), Delegated Regulation RTS (2022/1288), EU Taxonomy (2020/852), EU BMR (CTB/PAB), TCFD, GIPS |

---

## Session 3A: Fund Structure + Holdings-Level Analytics

### Functionality

Comprehensive fund-level analytics engine that processes holdings, share classes, benchmark data, and LP/investor information to produce a complete fund analytics report. Covers carbon metrics, ESG scoring, benchmark comparison, concentration risk, exclusion compliance, and LP waterfall metrics.

### Capabilities

- **NAV Calculation**: From share classes (NAV/share x total shares) or AUM fallback
- **Asset Class Breakdown**: Holdings categorised by equity, fixed income, cash, alternative, derivative with weight and market value
- **WACI (Weighted Average Carbon Intensity)**: Weight-adjusted carbon intensity across portfolio (tCO2e/MEUR)
- **Carbon Footprint**: Total financed emissions = sum(weight x carbon_intensity x AUM)
- **ESG Score**: Weighted-average ESG score (0-100 scale) across holdings
- **Taxonomy Alignment**: Weighted-average EU Taxonomy aligned percentage
- **Sustainable Investment %**: Combined taxonomy + environmental + social sustainable investment
- **DNSH Compliance**: Percentage of holdings meeting Do No Significant Harm criteria
- **Benchmark Comparison**: Portfolio WACI vs benchmark WACI, ESG delta, active share, tracking error estimate
- **Concentration Risk**: Top-10 holdings weight concentration
- **Sector Allocation**: Per-sector portfolio vs benchmark weight, active weight, carbon intensity comparison
- **Exclusion Breach Detection**: Holdings flagged for exclusion criteria violations
- **LP Waterfall**: Total commitment, called, distributed, DPI (Distributions/Paid-In), TVPI (Total Value/Paid-In)
- **Weight Normalisation**: Automatic normalisation of holdings to 100% if portfolio is not fully invested

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fund-management/analyse` | Full fund analytics with all metrics |
| GET | `/api/v1/fund-management/sfdr-summary` | SFDR classification reference data |

### Value Proposition

| Stakeholder | Value |
|------------|-------|
| Portfolio Manager | Single API call produces 25+ fund-level metrics — replaces 5+ separate spreadsheet calculations |
| Risk Manager | Active share, tracking error, and concentration metrics in real-time — no manual benchmark reconciliation |
| Fund Administrator | NAV from share classes + AUM fallback + weight normalisation — handles incomplete data gracefully |
| LP Relations | DPI and TVPI calculated automatically from investor records — ready for quarterly LP reporting |
| Compliance Officer | Exclusion breach detection with holding-level detail — immediate flagging of non-compliant positions |

### Competitive Advantage

1. **Unified Analytics**: Carbon, ESG, benchmark, concentration, exclusion, and LP metrics in a single engine — no data hand-off between siloed tools
2. **SFDR-Native**: Classifications (Art.6/8/8+/9) drive metric requirements — not bolted on as an afterthought
3. **Graceful Degradation**: Missing benchmark data, incomplete weights, zero AUM — engine handles edge cases without crashing
4. **LP Integration**: PE-style DPI/TVPI alongside listed-fund WACI/ESG — works for multi-asset fund managers

---

## Session 3B: ESG Attribution (Brinson-Fachler) + Benchmark Analytics

### Functionality

Decomposes portfolio ESG and carbon performance into attribution effects using the Brinson-Fachler framework adapted for sustainability metrics. Includes peer rankings, period-over-period comparison, and EU Climate Benchmark Regulation (CTB/PAB) compliance checking.

### Capabilities

#### ESG Attribution Engine
- **Brinson-Fachler Carbon Attribution**: Sector-level decomposition of WACI difference vs benchmark into allocation, selection, and interaction effects
- **Brinson-Fachler ESG Attribution**: Same framework applied to ESG scores (higher is better)
- **Brinson-Fachler Taxonomy Attribution**: Attribution of taxonomy alignment difference vs benchmark
- **Active Share**: ISIN-based overlap measurement between portfolio and benchmark
- **Tracking Error Proxy**: Sector active-weight based estimate (heuristic without covariance matrix)
- **Information Ratio**: Carbon IR (negative active / TE) and ESG IR (positive active / TE)
- **PAI Comparison**: Portfolio vs benchmark on 18 mandatory PAI indicators with outperformance count
- **YoY Changes**: Period-over-period WACI and ESG score change percentages

#### Benchmark Analytics Engine
- **Peer Rankings**: Rank fund against peer group on WACI, ESG score, taxonomy alignment, active share with percentile, median, mean, min, max
- **Period Comparison**: Current vs prior period with absolute and percentage change, improvement flag
- **EU Climate Benchmark Compliance**:
  - CTB (Climate Transition Benchmark): >= 30% WACI reduction vs parent benchmark + 7% annual decarbonisation
  - PAB (Paris-Aligned Benchmark): >= 50% WACI reduction + fossil fuel exclusion + controversial weapons exclusion + 7% annual decarbonisation
- **18 Mandatory PAI Indicators**: Complete reference data per SFDR RTS Annex I

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/attribution-benchmark/esg-attribution` | Full Brinson-Fachler ESG/carbon/taxonomy attribution |
| POST | `/api/v1/attribution-benchmark/benchmark-report` | Peer rankings + period comparison + CTB/PAB compliance |
| GET | `/api/v1/attribution-benchmark/pai-indicators` | 18 mandatory PAI indicators reference data |

### Value Proposition

| Stakeholder | Value |
|------------|-------|
| Portfolio Manager | Brinson-Fachler attribution explains WHY the portfolio has lower/higher carbon than benchmark — not just that it does |
| CIO | Information ratio quantifies ESG alpha per unit of tracking error — directly comparable to financial IR |
| Head of ESG | CTB/PAB compliance check — answers "can we label this fund as Paris-aligned?" with regulatory precision |
| Marketing / Product | Peer percentile rankings — "top quartile ESG score" claim backed by auditable methodology |
| Board / Trustees | PAI outperformance count — "outperforming benchmark on 14 of 18 mandatory indicators" |

### Competitive Advantage

1. **Brinson-Fachler for ESG**: Traditional return attribution framework applied to sustainability metrics — familiar to quant PMs, rigorous, and decomposable
2. **Direction-Aware**: Engine handles "lower is better" (carbon) and "higher is better" (ESG, taxonomy) correctly — no sign errors
3. **CTB + PAB in One Call**: Both EU Climate Benchmark compliance checks with detailed pass/fail reasons — saves manual regulatory interpretation
4. **18 PAI Indicators**: Complete SFDR mandatory PAI reference data with units and direction — no external lookup needed

---

## Session 3C: SFDR Periodic Report + Exclusion List Screening

### Functionality

Generates SFDR periodic disclosure data for Art.8 and Art.9 funds per RTS Annex II/IV templates. Includes exclusion list screening engine with 7 default categories, SFDR-classification-dependent rule applicability, and custom rule support.

### Capabilities

#### SFDR Report Generator
- **Proportion Breakdown**: Taxonomy-aligned %, other environmental %, social %, not sustainable % — core SFDR periodic template
- **Top 15 Investments**: Largest holdings by weight with sector and country — Annex II/IV required
- **Sector Breakdown**: Per-sector taxonomy alignment and sustainable investment percentage
- **Geography Breakdown**: Per-country weight allocation
- **PAI Summary with YoY**: Current vs prior period PAI values with year-over-year change
- **Art.8 Compliance Check**: Taxonomy target met? Sustainable investment target met?
- **Art.9 Compliance Check**: >= 90% sustainable investment requirement
- **Applicable Sections**: Dynamically selects which SFDR template sections apply (Art.8 vs Art.9)

#### Exclusion List Engine
- **7 Default Categories**: Controversial weapons (0% tolerance), tobacco (>5%), thermal coal mining (>10%), coal power generation (>30%), Arctic oil/gas (>5%), oil sands (>5%), nuclear weapons (0%), UNGC violations
- **SFDR-Dependent Applicability**: Art.6 only screens controversial weapons; Art.8 adds tobacco + UNGC; Art.8+ adds fossil fuels; Art.9 applies all categories
- **Hard vs Soft Breaches**: Zero-tolerance categories are "hard" breaches; threshold-based are "soft"
- **Custom Exclusion Rules**: User-defined rules with custom flag keys (e.g., gambling, animal testing, private prisons)
- **Category Summary**: Breach count per exclusion category for reporting
- **Breached Weight**: Total portfolio weight in non-compliant positions

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/sfdr-exclusion/periodic-report` | Generate SFDR periodic disclosure data |
| POST | `/api/v1/sfdr-exclusion/screen` | Screen portfolio against exclusion lists |
| GET | `/api/v1/sfdr-exclusion/exclusion-rules` | Default + custom exclusion rules by SFDR classification |
| GET | `/api/v1/sfdr-exclusion/pai-reference` | PAI indicator reference data |

### Value Proposition

| Stakeholder | Value |
|------------|-------|
| Regulatory Reporting Team | SFDR periodic template data generated automatically — reduces manual reporting from days to minutes |
| Compliance Officer | Exclusion screening with SFDR-classification-aware rule applicability — no manual rule mapping per fund type |
| Portfolio Manager | Real-time compliance monitoring — breach alerts before regulatory deadlines |
| Product Development | Custom exclusion rules — launch bespoke ESG strategies without code changes |
| External Auditor | Complete audit trail: which rules applied, what threshold was exceeded, holding-level detail |

### Competitive Advantage

1. **Template-Ready Output**: Proportion breakdown, top investments, sector/geo — maps directly to SFDR RTS Annex II/IV fields
2. **SFDR-Classification Routing**: Rules automatically adjust based on Art.6/8/8+/9 — not a static one-size-fits-all exclusion list
3. **Hard/Soft Severity**: Distinguishes zero-tolerance breaches (weapons) from threshold breaches (tobacco >5%) — proportionate compliance response
4. **Custom Rules as First-Class Citizens**: Custom exclusion categories slot in alongside regulatory defaults — extensible without forking the engine
5. **YoY PAI Comparison**: Period-over-period PAI improvement/deterioration — required by SFDR RTS for all Art.8+ funds

---

## Phase 3 User Stories

### User Persona 1: Asset Manager — Portfolio Manager

**Story**: _As a portfolio manager running a EUR 500M Art.8 UCITS fund, I need to generate my fund's quarterly analytics report covering carbon footprint, ESG score, benchmark attribution, and exclusion compliance._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Holdings register (holding_id, security_name, ISIN, ticker, asset_class, sector, country, weight_pct, market_value, carbon_intensity, esg_score, taxonomy_aligned_pct, dnsh_compliant, exclusion_flag). Benchmark holdings (same fields without acquisition cost). Share classes (class_id, NAV/share, total shares, TER, fees). LP/investor records (commitment, called, distributed, NAV share). |
| **Lineage** | Holdings from OMS/PMS (Bloomberg AIM, Charles River, Aladdin). Carbon intensity from MSCI ESG, Trucost, or ISS ESG. ESG scores from MSCI, Sustainalytics, or internal model. Taxonomy alignment from EU Taxonomy Compass or proprietary assessment. Benchmark from index provider (MSCI, FTSE, S&P). |
| **Reference Data** | SFDR classification (Art.6/8/8+/9), GICS/ICB sector mapping, ISO country codes, EU Taxonomy environmental objectives, PAI indicator definitions (SFDR RTS Annex I) |
| **Output** | Fund analytics: NAV, AUM, WACI, carbon footprint, financed emissions, avg ESG score, taxonomy %, sustainable investment %, DNSH %, benchmark delta, active share, tracking error, top-10 concentration, sector allocation, exclusion breach count, DPI, TVPI |
| **Insights** | Is the portfolio outperforming the benchmark on carbon? Which sectors are driving the ESG delta? Are there any exclusion breaches that need immediate remediation? What is the LP DPI/TVPI trajectory? |

### User Persona 2: Asset Manager — Head of ESG / Sustainability

**Story**: _As head of ESG at a fund management company with 12 funds across Art.6/8/9, I need to understand the Brinson-Fachler attribution of our carbon performance vs benchmark and assess whether our Art.8+ funds qualify for CTB/PAB labelling._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Portfolio holdings with sector, weight, carbon intensity, ESG score, taxonomy %. Benchmark holdings with same metrics. Prior period WACI and ESG scores. Peer fund metrics (WACI, ESG score, taxonomy %, active share) for 10-20 peer funds. Fossil fuel revenue % and controversial weapons exposure for PAB check. |
| **Lineage** | Carbon intensity: Trucost/MSCI ESG (Scope 1+2 or Scope 1+2+3). ESG scores: provider-specific (MSCI 0-10, Sustainalytics 0-100, mapped to 0-100). Benchmark: index constituent file from MSCI/FTSE. Peer data: from Bloomberg PORT, Morningstar Direct, or internal peer group definition. |
| **Reference Data** | GICS sector classification, Brinson-Fachler attribution methodology, CTB requirement (>=30% WACI reduction + 7% p.a. decarbonisation), PAB requirement (>=50% + fossil exclusion + weapons exclusion), 18 mandatory PAI indicators per SFDR RTS |
| **Output** | Carbon attribution: per-sector allocation, selection, interaction effects, total active metric. ESG attribution: same decomposition. Active share, tracking error, carbon IR, ESG IR. Peer ranking: percentile, median, mean. Period comparison: absolute and % change. CTB/PAB compliance: pass/fail with detailed reasons. PAI outperformance count. |
| **Insights** | Is the carbon outperformance coming from sector allocation (overweight clean sectors) or stock selection (picking lower-carbon stocks within sectors)? Do our funds qualify for CTB or PAB labelling? Where do we rank vs peers? Which PAI indicators are we underperforming on? |

### User Persona 3: Asset Manager — Regulatory Reporting / Compliance

**Story**: _As the compliance officer responsible for SFDR periodic disclosures, I need to generate the Annex II (Art.8) and Annex IV (Art.9) template data for 8 funds, run exclusion screening, and identify any breaches before the annual reporting deadline._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Fund definition: fund_id, SFDR classification, reporting period, reference benchmark, AUM, promoted characteristics, ESG strategy, minimum taxonomy %, minimum sustainable %. Holdings: security_name, ISIN, sector, country, weight, market value, taxonomy_aligned_pct, sustainable_environmental_pct, sustainable_social_pct, esg_score, dnsh_compliant, carbon_intensity. PAI values: current period dictionary (PAI_1 through PAI_18). Prior PAI values for YoY comparison. Exclusion screening: controversial weapons revenue %, tobacco revenue %, thermal coal revenue %, coal power generation %, Arctic oil revenue %, oil sands revenue %, nuclear weapons involvement (bool), UNGC violation (bool), custom flags. |
| **Lineage** | SFDR classification: fund prospectus/KIID. Holdings: fund administrator NAV package. Taxonomy alignment: EU Taxonomy eligibility and alignment assessment (per Delegated Acts). PAI values: portfolio-level calculation from holding-level data (GHG emissions, water, waste, social metrics). Exclusion data: ESG data provider (MSCI ESG Controversies, ISS ESG Norms, Bloomberg UNGC). |
| **Reference Data** | SFDR RTS Annex II/IV template field definitions, PAI indicator names and units (SFDR RTS Annex I Table 1-3), exclusion category thresholds per regulatory standard (GPFG, SVVK-ASIR), SFDR classification-to-rule mapping, Art.8 section list, Art.9 section list |
| **Output** | SFDR Periodic Report: proportion breakdown (taxonomy/environmental/social/not sustainable %), top 15 investments, sector breakdown with taxonomy %, geography breakdown, PAI summary with YoY change, compliance flags (taxonomy target met, sustainable target met, Art.8/9 compliant), applicable template sections. Exclusion Screening: per-holding breach list with category, severity (hard/soft), actual exposure, threshold, category summary, total breached weight %, compliance flag. |
| **Insights** | Are all 8 funds meeting their stated SFDR targets? Which funds have exclusion breaches? Are the PAI indicators improving year-over-year? Which Art.9 funds are at risk of falling below the 90% sustainable threshold? Do we need to divest any holdings before the reporting deadline? |

### User Persona 4: Asset Manager — Investment Analyst / ESG Integration

**Story**: _As an ESG integration analyst, I need to screen a proposed trade against our exclusion policy before execution and assess the impact on fund-level metrics._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Single holding: security_name, ISIN, sector, country, weight, revenue exposures (weapons, tobacco, coal, Arctic oil, oil sands), UNGC violation flag, custom flags. Fund SFDR classification for rule applicability. |
| **Lineage** | Revenue exposures: MSCI ESG Business Involvement Screening (BISR), ISS ESG Norms, Sustainalytics Product Involvement. UNGC violation: UN Global Compact participant list, ISS ESG Norms-Based screening. |
| **Reference Data** | Exclusion category thresholds, SFDR classification rule mapping, custom exclusion rules (fund-specific policy) |
| **Output** | Screening result: compliant/non-compliant, breach list with category, severity, actual exposure vs threshold. Category summary. |
| **Insights** | Can this stock be added to our Art.9 fund? Does it breach any exclusion criteria? What is the specific threshold it exceeds? Is this a hard breach (must sell) or soft breach (review required)? |

### User Persona 5: Asset Owner — Pension Fund CIO / Trustee

**Story**: _As a pension fund CIO allocating to external asset managers, I need to compare fund manager ESG performance and verify their SFDR claims are backed by auditable data._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Multiple fund metrics for peer comparison: fund_id, SFDR classification, WACI, ESG score, taxonomy %, active share, exclusion breach count. Period-over-period metrics for trend analysis. |
| **Lineage** | Fund metrics from manager reporting (EET files, SFDR periodic disclosures). Independently verified by asset owner's ESG data provider. |
| **Reference Data** | Peer group definition (by strategy, geography, asset class), CTB/PAB benchmark requirements, PAI indicator benchmarks |
| **Output** | Peer rankings with percentile, median, min/max per metric. Period comparison showing improvement/deterioration. CTB/PAB compliance verification. |
| **Insights** | Which manager delivers the best carbon-adjusted returns? Are they improving year-over-year? Do their CTB/PAB claims hold up against our independent data? How do they rank vs the peer group on each PAI indicator? |

---

## Phase 3 Test Coverage Summary

| Session | Test File | Tests | Coverage Focus |
|---------|-----------|-------|----------------|
| 3A | `test_fund_structure.py` | 37 | NAV, asset class, WACI, ESG, benchmark, active share, TE, concentration, sectors, exclusions, LP DPI/TVPI, weight normalisation, SFDR enum, integration |
| 3B | `test_attribution_benchmark.py` | 29 | Brinson-Fachler (carbon, ESG, taxonomy), active share, TE, IR, PAI, YoY, peer ranking, period comparison, CTB/PAB compliance, full report, reference data |
| 3C | `test_sfdr_exclusion.py` | 27 | Proportions, top investments, sector/geo breakdown, Art.8/9 compliance, PAI YoY, template sections, clean portfolio, weapons/tobacco/coal/UNGC screening, SFDR applicability, custom rules, reference data |
| **Total** | | **93** | |

---

## Technical Architecture (Phase 3)

```
api/v1/routes/
  fund_management.py         POST /analyse, GET /sfdr-summary
  attribution_benchmark.py   POST /esg-attribution, POST /benchmark-report, GET /pai-indicators
  sfdr_exclusion.py          POST /periodic-report, POST /screen, GET /exclusion-rules, GET /pai-reference

services/
  fund_structure_engine.py     FundAnalyticsResult — NAV + WACI + ESG + benchmark + LP
  esg_attribution_engine.py    BenchmarkAnalyticsResult — Brinson-Fachler + active share + IR + PAI
  benchmark_analytics.py       PortfolioBenchmarkReport — peer ranking + period comparison + CTB/PAB
  sfdr_report_generator.py     SFDRPeriodicReport — Annex II/IV + proportions + compliance
  exclusion_list_engine.py     FundScreeningResult — 7 categories + custom + hard/soft severity

tests/
  test_fund_structure.py       37 tests
  test_attribution_benchmark.py 29 tests
  test_sfdr_exclusion.py       27 tests
```

### Data Flow

```
Holdings + Benchmark + Share Classes + Investors
  |
  +---> FundStructureEngine          --> FundAnalyticsResult (NAV, WACI, ESG, LP)
  |
  +---> ESGAttributionEngine         --> BenchmarkAnalyticsResult (Brinson-Fachler)
  |       |
  |       +---> BenchmarkAnalytics   --> PortfolioBenchmarkReport (Peers, CTB/PAB)
  |
  +---> SFDRReportGenerator          --> SFDRPeriodicReport (Annex II/IV)
  |
  +---> ExclusionListEngine          --> FundScreeningResult (Breaches)
```

### Integration Points

| Engine | Feeds Into | Use Case |
|--------|-----------|----------|
| FundStructureEngine | ESGAttributionEngine | Portfolio WACI/ESG as input to attribution |
| FundStructureEngine | SFDRReportGenerator | Holdings data enriched with fund metadata |
| ExclusionListEngine | FundStructureEngine | Breach count feeds into fund analytics |
| BenchmarkAnalytics | Client reporting | Peer rankings for LP updates |
| SFDRReportGenerator | Regulatory filing | Annex II/IV template population |

---

## Market / Business Development Use Cases

### Target Segments
1. **UCITS Fund Managers** (Art.8/Art.9): SFDR periodic reporting + exclusion compliance
2. **Multi-Asset Fund Houses**: Cross-asset-class fund analytics (equity + FI + alternatives)
3. **Asset Owners / Pension Funds**: Manager oversight, peer comparison, SFDR verification
4. **Private Equity / VC Fund Managers**: LP waterfall metrics (DPI/TVPI) alongside ESG
5. **Index / ETF Providers**: CTB/PAB benchmark compliance verification
6. **Fund Administrators**: NAV calculation with ESG overlay for client reporting
7. **ESG Data Providers**: Attribution engine as white-label analytics layer

### Differentiators for Sales Conversations

- "Our Brinson-Fachler attribution engine answers the WHY behind your carbon outperformance — not just the WHAT. Is it sector allocation or stock selection driving the result?"
- "SFDR periodic report data is generated in one API call — proportion breakdown, top 15 investments, PAI summary with YoY, compliance flags — all Annex II/IV fields covered"
- "Exclusion screening automatically adjusts rules based on SFDR classification — Art.6 gets weapons-only, Art.9 gets all 7 categories. No manual configuration per fund."
- "CTB and PAB compliance checks include the 7% annual decarbonisation requirement that most competitors miss — this catches funds that meet the static threshold but fail the trajectory test"
- "Custom exclusion rules are first-class citizens — launch a tobacco-free, gambling-free, or palm-oil-free fund variant without any code changes"
- "LP waterfall (DPI/TVPI) alongside listed-fund metrics (WACI/active share) — built for multi-strategy fund managers, not just long-only equity"

### ROI Estimates for Prospects

| Current Manual Process | Time Saved | Risk Reduced |
|-----------------------|------------|--------------|
| Quarterly SFDR periodic report preparation | 3-5 days per fund per quarter -> minutes | Eliminates manual data assembly errors |
| Exclusion list screening (pre-trade + periodic) | 2-4 hours per screening cycle -> seconds | Zero tolerance breaches caught in real-time |
| Brinson-Fachler ESG attribution (bespoke Excel) | 1-2 days per fund per quarter -> seconds | Methodology consistency across all funds |
| CTB/PAB compliance assessment | 0.5-1 day per benchmark -> seconds | Regulatory claim backed by auditable logic |
| Peer group comparison | 1-2 days per quarter -> seconds | Standardised methodology, no cherry-picking |

---

## Expansion Roadmap (Technical Refinement)

### Near-Term (Phase 4+)
1. **Portfolio Optimisation**: Mean-variance with carbon constraints — maximise ESG score subject to tracking error budget
2. **Scenario-Based Attribution**: Attribute performance under NGFS scenarios (Net Zero 2050, Delayed Transition, Current Policies)
3. **Real-Time Exclusion Monitoring**: WebSocket feed for live breach alerts on trade execution
4. **EET (European ESG Template) Import/Export**: Direct ingestion and output of EET v1.1 data format
5. **Multi-Period Attribution**: Rolling 1Y/3Y/5Y Brinson-Fachler with time-series decomposition

### Medium-Term
1. **Factor Attribution**: Fama-French + carbon factor model
2. **Transition Plan Assessment**: Fund-level transition plan scoring per GFANZ framework
3. **Biodiversity PAI Extension**: TNFD-aligned nature-risk PAI indicators (beyond current 18)
4. **Sovereign Bond ESG**: Country-level ESG scoring for fixed income attribution
5. **Multi-Currency NAV**: FX overlay for multi-currency share classes

### Long-Term
1. **AI-Assisted SFDR Narrative Generation**: LLM-powered commentary for Annex II/IV periodic reports
2. **Predictive Compliance**: ML model predicting which holdings are likely to breach exclusion criteria in next 12 months
3. **Carbon Pathway Optimisation**: Dynamic portfolio rebalancing to meet SBTi-aligned decarbonisation glide path
