# Phase 2: Real Estate / REIT Completions
## Product Documentation — User Guide, Value Propositions & User Stories

---

## Phase Overview

| Attribute | Detail |
|-----------|--------|
| Phase | 2 — Real Estate / REIT Completions |
| Sessions | 2A (RE Portfolio NAV), 2B (EPC Transition Risk + Retrofit CapEx), 2C (Green Premium + Tenant ESG) |
| Tests | 147/147 passed |
| API Prefix | `/api/v1/re-portfolio`, `/api/v1/epc-retrofit`, `/api/v1/green-premium-tenant` |
| Regulatory Alignment | CRREM v2, EPBD Recast 2024 (MEPS), INREV NAV, RICS Red Book, GRESB, LEED, BREEAM, NABERS |

---

## Session 2A: RE Portfolio NAV Roll-Up + CRREM Stranding

### Functionality

Aggregates property-level real estate valuations to portfolio/fund-level NAV with integrated CRREM decarbonisation pathway analysis and MEPS regulatory compliance assessment. Provides weighted-average carbon metrics, EPC distribution analytics, and stranding year projections.

### Capabilities

- **GAV/NAV Calculation**: Gross asset value, debt overlay, net asset value per property and portfolio
- **Yield Metrics**: Weighted-average cap rate, NOI yield, occupancy across portfolio
- **ESG-Adjusted NAV**: Green premium uplift / climate discount applied to market values
- **Carbon Metrics**: Total portfolio emissions (tCO2e), carbon intensity per m2
- **EPC Distribution**: Count and GAV breakdown by rating (A+ through G), green/brown split
- **MEPS Compliance**: Exposure quantification against 2030 and 2033 EU regulatory deadlines
- **CRREM Stranding**: Per-property stranding year, gap to 1.5C/2C pathway, annual reduction required, portfolio stranding risk percentage

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/re-portfolio/nav` | Calculate portfolio NAV with full ESG overlay |
| POST | `/api/v1/re-portfolio/crrem` | Run CRREM stranding analysis |
| GET | `/api/v1/re-portfolio/meps-deadlines` | Return country-specific MEPS regulatory timelines |

### Value Proposition

| Stakeholder | Value |
|------------|-------|
| Portfolio Manager | Single-click portfolio NAV with built-in climate risk overlay — eliminates manual spreadsheet consolidation |
| Risk Manager | Forward-looking stranding year projections per asset — identify capital-at-risk before regulatory deadlines |
| Fund Administrator | INREV-compliant NAV calculation with standardised ESG adjustments — reduces audit queries |
| Investor Relations | EPC distribution and CRREM compliance metrics ready for GRESB submission and LP reporting |

### Competitive Advantage

1. **Integrated NAV + Climate**: Unlike standalone valuation tools (Argus, MSCI RCA), this engine embeds CRREM pathway analysis directly into NAV calculations
2. **Regulatory Forward-Looking**: Proactively flags MEPS non-compliance years before regulatory deadlines, giving 4-8 year lead time for CapEx planning
3. **Multi-Country MEPS**: Covers NL, GB, FR, DE, and EU default timelines — critical for pan-European fund managers
4. **Carbon Cost Monetisation**: Translates tCO2e gap into EUR impact using configurable carbon price (default EUR 90/tCO2e)

---

## Session 2B: EPC Transition Risk + Retrofit CapEx Planner

### Functionality

Scores properties against country-specific MEPS regulatory timelines from the EU EPBD Directive recast 2024. Quantifies EPC transition risk (0-100 composite score), gap-to-compliance, financial penalty exposure, and retrofit CapEx NPV/payback analysis.

### Capabilities

- **Composite Risk Scoring**: 0-100 score using weighted formula — gap severity (35%), time urgency (30%), penalty exposure (20%), regulatory certainty (15%)
- **Risk Banding**: Low / Medium / High / Critical classification per property
- **Deadline Exposure**: Per-property compliance status against each country MEPS deadline
- **Penalty Quantification**: Annual penalty-at-risk in EUR/m2 per non-compliant deadline
- **Portfolio Transition Summary**: Compliant now %, at-risk 2030/2033 %, GAV at risk, worst 5 properties
- **Retrofit CapEx Planning**: NPV and payback period for EPC upgrade pathways (planned for retrofit module)

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/epc-retrofit/assess-property` | Single property EPC transition risk |
| POST | `/api/v1/epc-retrofit/assess-portfolio` | Portfolio-wide transition risk summary |
| GET | `/api/v1/epc-retrofit/country-timelines` | Available country MEPS deadline data |

### Value Proposition

| Stakeholder | Value |
|------------|-------|
| Asset Manager | Prioritise retrofit spend — composite score identifies which assets need immediate attention vs. 5+ year runway |
| CIO / Investment Committee | GAV-at-risk metric for 2030 and 2033 — quantifies regulatory exposure in EUR for board reporting |
| Sustainability Officer | Country-specific compliance mapping eliminates manual regulatory tracking across 5+ jurisdictions |
| Acquisition Team | Pre-acquisition EPC due diligence — risk score feeds directly into bid pricing models |

### Competitive Advantage

1. **Country-Granular Timelines**: NL, GB, FR, DE with jurisdiction-specific deadlines (not one-size-fits-all EU)
2. **Multi-Factor Composite Score**: Combines gap severity, time urgency, penalty, and regulatory certainty — more nuanced than binary pass/fail
3. **Penalty Monetisation**: Converts compliance gap into EUR/m2 annual penalty — language CFOs understand
4. **Stranding Probability**: Probabilistic stranding estimate per property per deadline — connects to TCFD scenario analysis

---

## Session 2C: Green Premium / Brown Discount + Tenant ESG Tracker

### Functionality

Quantifies empirical rent and cap-rate differentials by EPC rating and sustainability certification (LEED, BREEAM, NABERS, GRESB). Outputs green premium uplift and brown discount at property and portfolio level.

### Capabilities

- **Certification Premium**: Rent uplift % and EUR/m2 by certification level (LEED Platinum 12%, BREEAM Outstanding 10%, NABERS 6-star 12%, GRESB 5-star 6%)
- **EPC Cap Rate Adjustment**: A+ (-30bps) through G (+80bps) cap rate shift
- **EPC Rent Discount**: D (-2%) through G (-12%) rent reduction
- **Brown Vacancy Premium**: Additional void months per year by EPC rating (D: 0.5mo, E: 1mo, F: 2mo, G: 3mo)
- **Portfolio Green/Brown Split**: Green (A+/A/B) vs Brown (E/F/G) count, GAV, and percentage
- **Value Impact**: Base vs adjusted market value per property and total portfolio

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/green-premium-tenant/assess-property` | Single property green premium / brown discount |
| POST | `/api/v1/green-premium-tenant/assess-portfolio` | Portfolio-wide green/brown summary |
| GET | `/api/v1/green-premium-tenant/reference-data` | Certification premium and EPC adjustment tables |

### Value Proposition

| Stakeholder | Value |
|------------|-------|
| Valuation Team | Empirical green premium / brown discount data replaces subjective adjustments — RICS Red Book compatible |
| Leasing Team | Quantified rent uplift per certification level — justifies sustainability CapEx to tenants |
| Fund Manager | Portfolio-level value impact in EUR — demonstrates ESG alpha to LPs |
| Acquisition Team | Pre-acquisition green premium assessment — avoids overpaying for brown assets |

### Competitive Advantage

1. **Multi-Scheme Coverage**: LEED, BREEAM, NABERS, GRESB with granular level-specific premiums — not just binary certified/uncertified
2. **Cap Rate + Rent + Vacancy**: Three-dimensional impact assessment (not just rent premium)
3. **EUR Monetisation**: Translates % adjustments into absolute EUR impact — boardroom-ready
4. **Brown Discount Realism**: Explicitly models brown penalty (vacancy, rent discount, cap rate expansion) — critical for MEPS transition planning

---

## Phase 2 User Stories

### User Persona 1: RE Portfolio Manager

**Story**: _As a portfolio manager at a EUR 2B pan-European real estate fund, I need to generate a consolidated portfolio NAV report with embedded climate risk metrics for our quarterly LP update._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Property register (ID, name, type, country, floor area m2, market value, debt, NOI, cap rate, occupancy, EPC rating, certifications, annual emissions tCO2e) |
| **Lineage** | Property valuations from RICS Red Book appraisals; EPC certificates from national registries; emissions from utility meter data or energy audits |
| **Reference Data** | CRREM 1.5C/2C decarbonisation pathways by property type and country; MEPS country deadlines; certification premium tables (LEED/BREEAM/NABERS/GRESB); carbon price (EUR/tCO2e) |
| **Output** | Portfolio NAV (GAV, debt, NAV), weighted-average cap rate, portfolio WACI (kgCO2e/m2), EPC distribution (A+ to G count + GAV), green/brown split %, MEPS exposure (2030/2033 GAV at risk), CRREM stranding year per property, portfolio stranding risk % |
| **Insights** | Which properties strand before 2030? What is the GAV at risk from MEPS? How does the green premium offset retrofit CapEx? What is the carbon cost gap to 1.5C? |

### User Persona 2: RE Sustainability / ESG Officer

**Story**: _As the sustainability officer, I need to assess our portfolio's EPC transition risk, identify the 5 worst properties, and quantify the annual penalty exposure for each MEPS deadline._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Property register with EPC rating, country, floor area, market value, annual rent, building age, property type, lease status |
| **Lineage** | EPC certificates from national registries (NL: EP-online, GB: EPC Register, FR: DPE, DE: EnEV); building age from title deeds or cadastral records |
| **Reference Data** | Country-specific MEPS deadlines (NL 2023/2030/2050, GB 2025/2030, FR 2025/2028/2034, DE 2027/2030/2033); penalty EUR/m2 by jurisdiction; composite score weighting (gap 35%, urgency 30%, penalty 20%, certainty 15%) |
| **Output** | Per-property: composite risk score (0-100), risk band, first non-compliant year, worst gap steps, annual penalty EUR. Portfolio: compliant now %, at-risk 2030/2033 count + %, total annual penalty exposure, GAV at risk, top 5 worst properties |
| **Insights** | Which properties need immediate retrofit? What is the total penalty exposure by 2030? Which countries pose the highest regulatory risk? Where should CapEx be prioritised? |

### User Persona 3: RE Acquisitions Analyst

**Story**: _As an acquisitions analyst evaluating a EUR 150M office portfolio in the Netherlands, I need to assess the green premium/brown discount impact on asset values and feed this into our bid model._

**Data Requirements**:

| Category | Detail |
|----------|--------|
| **Input** | Target property details: EPC rating, base rent EUR/m2, floor area, market value, NOI, cap rate, certifications (BREEAM Excellent), country, property type |
| **Lineage** | Vendor data room (rent roll, EPC certificates, sustainability reports); BREEAM/LEED certificates from scheme operators |
| **Reference Data** | Green premium tables (LEED/BREEAM/NABERS/GRESB by level), EPC cap rate adjustments (A+ -30bps to G +80bps), EPC rent discounts (D -2% to G -12%), brown vacancy months (D 0.5 to G 3.0) |
| **Output** | Per-property: is_green/is_brown flag, certification premium % and EUR/m2, EPC rent adjustment %, cap rate shift bps, brown vacancy months, base vs adjusted market value, value impact EUR and %. Portfolio: green/neutral/brown split, total value impact EUR |
| **Insights** | What is the real value of this BREEAM Excellent certificate? How much should we discount the F-rated warehouse? Does the green premium justify the asking price? What is the portfolio-level brown discount exposure? |

---

## Phase 2 Test Coverage Summary

| Session | Test File | Tests | Coverage Focus |
|---------|-----------|-------|----------------|
| 2A | `test_re_portfolio.py` | 58 | NAV calc, yield metrics, ESG-adjusted NAV, carbon metrics, EPC distribution, MEPS compliance, CRREM stranding, multi-property aggregation |
| 2B | `test_epc_retrofit.py` | 47 | Composite scoring, risk banding, country timelines, deadline exposure, penalty calc, portfolio summary, edge cases (missing country, future-proof EPC) |
| 2C | `test_green_premium_tenant.py` | 42 | Certification premiums (LEED/BREEAM/NABERS/GRESB), EPC adjustments, brown discount, vacancy, portfolio aggregation, green/brown split |
| **Total** | | **147** | |

---

## Technical Architecture (Phase 2)

```
api/v1/routes/
  re_portfolio.py          POST /nav, POST /crrem, GET /meps-deadlines
  epc_retrofit.py          POST /assess-property, POST /assess-portfolio, GET /country-timelines
  green_premium_tenant.py  POST /assess-property, POST /assess-portfolio, GET /reference-data

services/
  re_portfolio_engine.py       PortfolioNAVResult — GAV/NAV + CRREM + MEPS
  epc_transition_engine.py     PropertyTransitionRisk — composite score + deadlines
  green_premium_engine.py      PropertyGreenResult — premium/discount + value impact

tests/
  test_re_portfolio.py         58 tests
  test_epc_retrofit.py         47 tests
  test_green_premium_tenant.py 42 tests
```

### Data Flow

```
Property Register (CSV/API)
  |
  v
PropertyAsset / PropertyEPCInput / PropertyGreenInput   [Input Models]
  |
  v
Engine (re_portfolio / epc_transition / green_premium)   [Business Logic]
  |
  v
PortfolioNAVResult / PortfolioTransitionSummary / PortfolioGreenSummary   [Output Models]
  |
  v
API Serialiser → JSON Response                          [REST API]
```

---

## Market / Business Development Use Cases

### Target Segments
1. **Pan-European RE Fund Managers** (AUM EUR 500M+): Portfolio NAV with CRREM and MEPS compliance
2. **REITs with GRESB Reporting Obligations**: Green/brown split analytics for GRESB submission
3. **Insurance Companies with RE Exposure**: Stranding risk quantification for Solvency II
4. **Pension Funds with RE Allocation**: MEPS transition risk for fiduciary duty compliance
5. **RE Advisory Firms**: Client portfolio due diligence and transition planning

### Differentiators for Sales Conversations
- "Our platform is the only tool that integrates INREV NAV, CRREM stranding, and MEPS compliance in a single API call"
- "We cover 5 country-specific MEPS timelines (NL, GB, FR, DE, EU) — not a one-size-fits-all approach"
- "Green premium is quantified across 4 certification schemes at granular level (e.g., LEED Platinum vs Gold) — not just certified/uncertified"
- "Brown discount includes cap rate expansion, rent discount, AND vacancy — the full economic picture"
- "Every metric is monetised in EUR — ready for board and LP reporting"
