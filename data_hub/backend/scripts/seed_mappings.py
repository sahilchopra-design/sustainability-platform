"""
Normalization model: maps all 51 platform KPIs through available data source
schemas to their primary, fallback-1, and fallback-2 sources.

Each mapping specifies:
  - kpi_slug         → which application KPI
  - source_name      → which data source
  - priority_order   → 1=primary, 2=fallback-1, 3=fallback-2
  - method           → approximation method (direct/peer_average/sector_proxy/ratio/regression)
  - assumption       → key modelling assumption
  - confidence       → 0.0–1.0 confidence score
  - formula          → optional transform formula
  - note             → lineage / rationale note

Run:
  python scripts/seed_mappings.py [--reset]

Options:
  --reset  Delete all existing mappings before seeding (idempotent re-run).
"""

import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select, delete
from dotenv import load_dotenv
load_dotenv()

from database import engine, AsyncSessionLocal
from models.models import ApplicationKpi, DataSource, KpiMapping

# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZATION MAPPING TABLE
# Format per entry:
#   (kpi_slug, source_name, priority, method, assumption, confidence, formula, note)
# ─────────────────────────────────────────────────────────────────────────────

MAPPINGS: list[tuple] = [

    # ── EMISSIONS ─────────────────────────────────────────────────────────────

    # Scope 1 GHG
    ("scope1_ghg_emissions", "CDP",                   1, "direct",       "Company-reported via CDP questionnaire",              0.90, None, "CDP Q4.1a company-level Scope 1"),
    ("scope1_ghg_emissions", "MSCI ESG Ratings",      2, "peer_average",  "MSCI modelled where CDP response absent",             0.70, None, "MSCI Climate pillar Scope 1 model"),
    ("scope1_ghg_emissions", "Climate TRACE",          3, "sector_proxy",  "Satellite-derived Scope 1 estimate by facility",     0.60, None, "Climate TRACE asset-level gross emissions"),

    # Scope 2 GHG
    ("scope2_ghg_emissions", "CDP",                   1, "direct",       "Market-based Scope 2 per CDP Q4.3",                   0.88, None, "CDP Q4.3 market-based Scope 2"),
    ("scope2_ghg_emissions", "MSCI ESG Ratings",      2, "peer_average",  "MSCI location-based Scope 2 model",                  0.68, None, "MSCI Climate Scope 2 model"),
    ("scope2_ghg_emissions", "IEA Open Data",          3, "ratio",        "Country grid intensity × energy consumption",         0.55, "value * grid_ef", "IEA grid EF × consumed MWh"),

    # Scope 3 GHG
    ("scope3_ghg_emissions", "CDP",                   1, "direct",       "CDP Q5 Scope 3 categories 1–15 combined",             0.82, None, "CDP Q5 Scope 3 total"),
    ("scope3_ghg_emissions", "MSCI ESG Ratings",      2, "peer_average",  "MSCI Scope 3 modelled using sector I/O tables",       0.60, None, "MSCI Scope 3 model"),

    # Total GHG
    ("total_ghg_emissions",  "CDP",                   1, "direct",       "Scope 1 + 2 + 3 from CDP disclosure",                0.88, "s1+s2+s3", "Sum of CDP Scopes 1–3"),
    ("total_ghg_emissions",  "MSCI ESG Ratings",      2, "peer_average",  "MSCI total GHG model",                               0.68, None, "MSCI total GHG pillar"),
    ("total_ghg_emissions",  "Climate TRACE",          3, "sector_proxy",  "Climate TRACE facility-level aggregation",           0.58, None, "Climate TRACE country/facility aggregation"),

    # Carbon Intensity (Revenue)
    ("carbon_intensity_revenue", "CDP",               1, "ratio",        "Scope 1+2 divided by revenue (CDP + Finnhub)",        0.85, "total_ghg/revenue*1e6", "CDP Scope 1+2 / revenue (USD)"),
    ("carbon_intensity_revenue", "MSCI ESG Ratings",  2, "ratio",        "MSCI carbon intensity metric",                        0.70, None, "MSCI carbon intensity per revenue"),
    ("carbon_intensity_revenue", "Climate TRACE",      3, "sector_proxy",  "Sector-average carbon intensity applied",            0.50, None, "Sector peer average CI"),

    # Carbon Intensity (Asset)
    ("carbon_intensity_asset",   "CDP",               1, "ratio",        "Scope 1+2 / total assets (CDP + yfinance)",           0.82, "total_ghg/total_assets*1e6", "CDP Scope 1+2 / total assets"),
    ("carbon_intensity_asset",   "MSCI ESG Ratings",  2, "ratio",        "MSCI asset-based carbon intensity model",             0.68, None, "MSCI asset CI"),

    # WACI
    ("waci",                 "CDP",                   1, "ratio",        "WACI = portfolio weighted avg of entity CI revenue",  0.85, "sum(weight*ci_revenue)", "CDP Scope 1+2 CI × PCAF weight"),
    ("waci",                 "MSCI ESG Ratings",      2, "peer_average",  "MSCI WACI aligned to SFDR PAI #1",                  0.72, None, "MSCI WACI metric"),

    # Grid Emission Factor
    ("grid_emission_factor", "IEA Open Data",          1, "direct",       "IEA country-level grid EF (tCO2e/MWh)",              0.90, None, "IEA Emissions Factors dataset"),
    ("grid_emission_factor", "EMBER Climate",          2, "direct",       "EMBER monthly grid carbon intensity",                0.85, None, "EMBER electricity carbon intensity"),

    # ── FINANCIAL ─────────────────────────────────────────────────────────────

    ("market_cap",           "yfinance",               1, "direct",       "Real-time market cap from Yahoo Finance",             0.90, None, "yfinance fast_info.market_cap"),
    ("market_cap",           "Finnhub API",            2, "direct",       "Finnhub quote × shares outstanding",                 0.88, "price*shares", "Finnhub /stock/profile2 + /quote"),

    ("enterprise_value",     "yfinance",               1, "direct",       "yfinance info.enterpriseValue",                       0.88, None, "yfinance info enterpriseValue"),
    ("enterprise_value",     "Finnhub API",            2, "ratio",        "Market cap + net debt (Finnhub financials)",          0.80, "market_cap+net_debt", "Finnhub /stock/metric"),

    ("evic",                 "yfinance",               1, "direct",       "EV incl. cash = market cap + debt",                  0.85, "market_cap+debt+minority-cash", "yfinance EVIC per PCAF standard"),
    ("evic",                 "Finnhub API",            2, "ratio",        "Finnhub basic financials EVIC approximation",         0.75, "market_cap+total_debt", "Finnhub /stock/metric"),

    ("revenue",              "yfinance",               1, "direct",       "Annual revenue from yfinance income statement",       0.90, None, "yfinance financials.loc['Total Revenue']"),
    ("revenue",              "Finnhub API",            2, "direct",       "Finnhub /stock/financials revenue",                  0.88, None, "Finnhub basic financials"),
    ("revenue",              "SEC EDGAR",              3, "direct",       "10-K/10-Q XBRL revenue for US filers",               0.92, None, "EDGAR XBRL us-gaap:Revenues"),

    ("total_assets",         "yfinance",               1, "direct",       "Balance sheet total assets via yfinance",             0.90, None, "yfinance balance_sheet.loc['Total Assets']"),
    ("total_assets",         "Finnhub API",            2, "direct",       "Finnhub /stock/financials total assets",              0.87, None, "Finnhub financial statements"),
    ("total_assets",         "SEC EDGAR",              3, "direct",       "10-K XBRL us-gaap:Assets for US public cos",          0.92, None, "EDGAR XBRL us-gaap:Assets"),

    ("ebitda",               "yfinance",               1, "direct",       "yfinance EBITDA from income statement",               0.88, None, "yfinance financials EBITDA"),
    ("ebitda",               "Finnhub API",            2, "direct",       "Finnhub /stock/metric ebitda",                       0.85, None, "Finnhub /stock/metric"),
    ("ebitda",               "SEC EDGAR",              3, "ratio",        "Operating income + D&A from EDGAR XBRL",             0.88, "ebit+da", "EDGAR XBRL EBIT + D&A"),

    ("stock_price",          "Finnhub API",            1, "direct",       "Real-time bid/ask via Finnhub WebSocket",             0.95, None, "Finnhub /quote c (current price)"),
    ("stock_price",          "yfinance",               2, "direct",       "yfinance fast_info.last_price (delayed)",             0.90, None, "yfinance fast_info"),

    # ── ESG ───────────────────────────────────────────────────────────────────

    ("esg_score_overall",    "MSCI ESG Ratings",       1, "direct",       "MSCI ESG composite score (0-10 normalised to 0-100)", 0.88, "value*10", "MSCI ESG Ratings /esg-ratings"),
    ("esg_score_overall",    "GRI Sustainability Database", 2, "peer_average", "GRI disclosure completeness as ESG proxy",       0.55, None, "GRI disclosure score approximation"),
    ("esg_score_overall",    "CDP",                    3, "peer_average",  "CDP A-D score mapped to 0-100 scale",               0.65, "score_map[rating]", "CDP score A=100 B=75 C=50 D=25"),

    ("environmental_score",  "MSCI ESG Ratings",       1, "direct",       "MSCI E-pillar score (0-10)",                         0.88, "value*10", "MSCI E pillar"),
    ("environmental_score",  "CDP",                    2, "peer_average",  "CDP climate score as E-pillar proxy",                0.72, None, "CDP score → E pillar proxy"),

    ("social_score",         "MSCI ESG Ratings",       1, "direct",       "MSCI S-pillar score (0-10)",                         0.85, "value*10", "MSCI S pillar"),
    ("social_score",         "ILO Statistics",          2, "sector_proxy",  "ILO country labour indicators as sector S proxy",   0.48, None, "ILO sector-level social benchmarks"),

    ("governance_score",     "MSCI ESG Ratings",       1, "direct",       "MSCI G-pillar score (0-10)",                         0.85, "value*10", "MSCI G pillar"),
    ("governance_score",     "ISS Governance QualityScore", 2, "direct",  "ISS QualityScore 1-10 normalised",                  0.82, "(10-value)*10", "ISS QualityScore (lower=better → invert)"),

    ("esg_controversy_score","MSCI ESG Ratings",       1, "direct",       "MSCI controversy severity 0-10",                     0.85, "value*10", "MSCI controversy monitor"),
    ("esg_controversy_score","ShareAction",            2, "peer_average",  "ShareAction engagement outcome score",              0.58, None, "ShareAction voting outcomes"),

    ("cdp_climate_score",    "CDP",                    1, "direct",       "CDP Climate Change questionnaire A/A- → D/D-",       0.95, None, "CDP /responses climate score"),

    ("msci_esg_rating",      "MSCI ESG Ratings",       1, "direct",       "MSCI AAA–CCC letter rating",                         0.95, None, "MSCI ESG Ratings letter"),

    ("news_esg_sentiment",   "GDELT Project",          1, "direct",       "GDELT article tone → ESG sentiment",                 0.72, "avg_tone/10", "GDELT GKG V2 themes + average tone"),
    ("news_esg_sentiment",   "News API",               2, "direct",       "News API ESG keyword relevance + sentiment",          0.65, None, "News API sentiment model"),
    ("news_esg_sentiment",   "The Guardian API",       3, "direct",       "Guardian environment section sentiment",              0.60, None, "Guardian API environment tag tone"),

    # ── RISK ──────────────────────────────────────────────────────────────────

    ("probability_of_default","World Bank Open Data",  1, "sector_proxy",  "Sovereign PD via World Bank fiscal risk indicators",  0.52, None, "World Bank fiscal + sovereign credit proxy"),
    ("probability_of_default","IMF Data",              2, "sector_proxy",  "IMF WEO debt/GDP + current account as PD proxy",     0.50, None, "IMF WEO fiscal stress indicator"),

    ("expected_credit_loss", "MSCI ESG Ratings",       1, "peer_average",  "ECL = PD × LGD × EAD; LGD=45% Basel default",       0.60, "pd*0.45*ead", "ECL approximation using MSCI PD estimate"),
    ("expected_credit_loss", "World Bank Open Data",   2, "sector_proxy",  "Country-level ECL proxy for sovereign exposures",    0.48, None, "World Bank sovereign risk proxy"),

    ("physical_risk_score",  "Natural Hazards (NOAA)", 1, "direct",       "NOAA multi-hazard index: flood/wind/quake/fire",      0.78, None, "NOAA hazard frequency × exposure"),
    ("physical_risk_score",  "NASA Earthdata",         2, "direct",       "NASA FIRMS fire, SEDAC flood hazard maps",           0.74, None, "NASA multi-hazard gridded exposure"),
    ("physical_risk_score",  "WRI Aqueduct",           3, "ratio",        "WRI physical water + flood risk as partial proxy",    0.65, None, "WRI Aqueduct flood hazard score"),

    ("transition_risk_score","NGFS Scenarios",         1, "direct",       "NGFS NZE/DT scenario carbon cost stranding",         0.82, None, "NGFS Phase 4 transition risk variables"),
    ("transition_risk_score","Transition Pathway Initiative", 2, "direct", "TPI management quality + carbon performance",       0.78, None, "TPI carbon performance assessment"),
    ("transition_risk_score","Carbon Tracker",         3, "peer_average",  "Carbon Tracker stranded cost as transition proxy",   0.72, None, "Carbon Tracker 2-degree stress test"),

    ("stranded_asset_value_at_risk", "Carbon Tracker", 1, "direct",       "Carbon Tracker unburnable carbon $ stranded value", 0.80, None, "Carbon Tracker stressed NPV"),
    ("stranded_asset_value_at_risk", "NGFS Scenarios", 2, "ratio",        "NGFS carbon price path × residual reserve value",   0.72, "carbon_price*reserves_tco2", "NGFS carbon price × reserve exposure"),

    ("water_risk_score",     "WRI Aqueduct",           1, "direct",       "WRI Aqueduct water stress score 0-5",                0.88, None, "WRI Aqueduct v4 baseline water stress"),

    ("biodiversity_risk_score","Global Forest Watch",  1, "direct",       "GFW tree cover loss index within 50km buffer",       0.78, None, "GFW annual deforestation rate"),
    ("biodiversity_risk_score","WRI Aqueduct",         2, "ratio",        "Water stress as biodiversity pressure proxy",         0.58, None, "WRI water depletion as biodiversity proxy"),

    ("sanctions_flag",       "OpenSanctions",          1, "direct",       "OpenSanctions consolidated OFAC/EU/UN watchlist",    0.95, None, "OpenSanctions /search entity match"),
    ("sanctions_flag",       "FATF Mutual Evaluations",2, "sector_proxy",  "FATF jurisdiction risk as entity flag proxy",        0.60, None, "FATF AML risk country of incorporation"),

    # ── REGULATORY ────────────────────────────────────────────────────────────

    ("temperature_alignment","SBTi Target Dashboard",  1, "direct",       "SBTi validated target → implied temperature path",   0.88, None, "SBTi target → IEA/IPCC temperature alignment"),
    ("temperature_alignment","Transition Pathway Initiative", 2, "direct", "TPI carbon performance vs IEA benchmarks",          0.80, None, "TPI benchmark temperature score"),
    ("temperature_alignment","Climate Action 100+",    3, "peer_average",  "CA100+ net-zero benchmark alignment score",         0.72, None, "CA100+ net-zero indicator"),

    ("sbti_target_status",   "SBTi Target Dashboard",  1, "direct",       "SBTi approved/committed/removed status",             0.95, None, "SBTi public dashboard target status"),
    ("sbti_target_status",   "Transition Pathway Initiative", 2, "peer_average", "TPI management quality as SBTi proxy",        0.60, None, "TPI Level 4+ ≈ SBTi-aligned"),

    ("eu_taxonomy_aligned_pct","EU Taxonomy Compass",  1, "direct",       "EU Taxonomy eligible + aligned activities %",         0.85, None, "EU Taxonomy Compass API eligible/aligned"),
    ("eu_taxonomy_aligned_pct","MSCI ESG Ratings",     2, "peer_average",  "MSCI EU Taxonomy alignment estimate",               0.68, None, "MSCI EU Taxonomy model"),

    ("sfdr_pai_value",       "MSCI ESG Ratings",       1, "direct",       "MSCI SFDR PAI data package (14 mandatory PIs)",      0.82, None, "MSCI SFDR PAI data"),
    ("sfdr_pai_value",       "CDP",                    2, "direct",       "CDP data feeds SFDR PAI #1 GHG, #4 fossil",          0.80, None, "CDP → SFDR PAI 1/4/14 crosswalk"),

    ("csrd_esrs_dp_value",   "GRI Sustainability Database", 1, "direct",  "GRI Standards → ESRS crosswalk, reported values",   0.72, None, "GRI/ESRS interoperability mapping"),
    ("csrd_esrs_dp_value",   "CDP",                    2, "direct",       "CDP questionnaire answers → ESRS E1 datapoints",     0.75, None, "CDP→ESRS E1 climate crosswalk"),

    ("cbam_embedded_carbon", "EDGAR (EU JRC)",         1, "direct",       "EDGAR sector default emission factors for CBAM",     0.82, None, "EDGAR IEF industrial process EFs for CBAM goods"),
    ("cbam_embedded_carbon", "CDP",                    2, "peer_average",  "CDP facility-level emission intensity as CBAM EF",  0.68, None, "CDP facility EF proxy for CBAM embedded carbon"),

    ("tcfd_alignment_score", "CDP",                    1, "direct",       "CDP full TCFD disclosure score (Gov/Risk/Metrics)",  0.88, None, "CDP TCFD mapping score"),
    ("tcfd_alignment_score", "Transition Pathway Initiative", 2, "direct", "TPI TCFD-aligned management quality score",        0.75, None, "TPI management quality (TCFD-aligned)"),
    ("tcfd_alignment_score", "MSCI ESG Ratings",       3, "peer_average",  "MSCI climate disclosure quality as TCFD proxy",     0.65, None, "MSCI TCFD disclosure quality"),

    # ── SCENARIO ──────────────────────────────────────────────────────────────

    ("carbon_price",         "ICE Carbon Futures",     1, "direct",       "ICE EUA/CCA futures spot + forward curve",           0.95, None, "ICE EUA front-month price (EUR/tCO2)"),
    ("carbon_price",         "EU ETS Prices",          2, "direct",       "EU ETS Sandbag historical EUA price series",         0.90, None, "EU ETS Sandbag price tracker"),
    ("carbon_price",         "NGFS Scenarios",          3, "direct",       "NGFS carbon price pathway by scenario",              0.85, None, "NGFS Phase 4 carbon price by scenario/year"),

    ("ngfs_scenario_variable","NGFS Scenarios",         1, "direct",       "NGFS Phase 4 macro/climate variables by scenario",   0.90, None, "NGFS IAM output variables (REMIND/MESSAGEix)"),

    ("crrem_glidepath",      "IRENA",                  1, "peer_average",  "IRENA RE cost + CRREM sector benchmark approximation",0.65, None, "IRENA data → CRREM glidepath benchmark"),
    ("crrem_glidepath",      "IEA Open Data",          2, "sector_proxy",  "IEA Net Zero scenario → building sector glidepath", 0.62, None, "IEA NZE building sector decarbonisation path"),

    # ── ENERGY ────────────────────────────────────────────────────────────────

    ("lcoe",                 "IRENA",                  1, "direct",       "IRENA renewable power generation cost by technology",0.90, None, "IRENA Renewable Cost Database LCOE"),
    ("lcoe",                 "IEA Open Data",          2, "direct",       "IEA projected LCOE by technology and region",        0.85, None, "IEA World Energy Outlook LCOE projections"),
    ("lcoe",                 "Global Coal Plant Tracker",3,"direct",      "GCPT coal plant LCOE for stranded asset analysis",   0.80, None, "GCPT coal LCOE + remaining life"),

    ("capacity_factor",      "IRENA",                  1, "direct",       "IRENA capacity factor by technology/country",        0.88, None, "IRENA renewable capacity factor data"),
    ("capacity_factor",      "Global Coal Plant Tracker",2,"direct",      "GCPT historical coal plant capacity factors",        0.82, None, "GCPT operating hours / capacity"),
    ("capacity_factor",      "IEA Open Data",          3, "direct",       "IEA electricity generation / capacity ratio",        0.80, None, "IEA electricity statistics CF calculation"),

    # ── SOCIAL / GOVERNANCE ───────────────────────────────────────────────────

    ("gender_pay_gap",       "ILO Statistics",         1, "direct",       "ILO gender wage gap by country/sector (%)",          0.82, None, "ILO SDG indicator 8.5.1 gender pay gap"),
    ("gender_pay_gap",       "WHO Global Health Observatory",2,"sector_proxy","WHO country gender equality indicators",          0.55, None, "WHO gender health equity as social proxy"),
    ("gender_pay_gap",       "Gender Inequality Index (UNDP)",3,"direct",  "UNDP GII income sub-index as pay gap proxy",        0.50, None, "UNDP GII income dimension"),

    ("employee_satisfaction","Glassdoor (Apify)",      1, "direct",       "Glassdoor employer rating 1-5 scrape",               0.78, "value/5*100", "Glassdoor overall company rating"),
    ("employee_satisfaction","Indeed Job Trends (Apify)",2,"peer_average", "Indeed employer review score as satisfaction proxy", 0.65, None, "Indeed employer ratings"),

    ("board_diversity_pct",  "ISS Governance QualityScore",1,"direct",    "ISS board gender diversity %",                       0.88, None, "ISS board composition data"),
    ("board_diversity_pct",  "MSCI ESG Ratings",       2, "direct",       "MSCI G-pillar board gender diversity metric",        0.82, None, "MSCI governance board diversity"),

    # ── NATURE ────────────────────────────────────────────────────────────────

    ("deforestation_risk",   "Global Forest Watch",    1, "direct",       "GFW annual forest cover loss within asset footprint",0.85, None, "GFW tree cover loss alert system"),
    ("deforestation_risk",   "EUDR Compliance Data",   2, "direct",       "EUDR due diligence deforestation flag by commodity",  0.80, None, "EUDR JRC global forest change layer"),

    ("tnfd_leap_score",      "WRI Aqueduct",           1, "ratio",        "TNFD LEAP: water stress + flood risk sub-score",     0.68, "(water_stress+flood_risk)/2", "WRI Aqueduct multi-risk TNFD approximation"),
    ("tnfd_leap_score",      "Global Forest Watch",    2, "ratio",        "TNFD LEAP: biodiversity/forest intactness sub-score", 0.65, None, "GFW habitat intactness layer"),

    # ── SUPPLY CHAIN ──────────────────────────────────────────────────────────

    ("scope3_upstream_intensity","CDP",                1, "ratio",        "CDP Cat.1 purchased goods / spend (EEIO method)",    0.72, "scope3_cat1/spend", "CDP Scope 3 Category 1 upstream intensity"),
    ("scope3_upstream_intensity","PCAF Database",      2, "peer_average",  "PCAF sector emission factor for financed Scope 3",  0.65, None, "PCAF Scope 3 attribution factors"),

    # ── REFERENCE ─────────────────────────────────────────────────────────────

    ("lei_number",           "GLEIF",                  1, "direct",       "GLEIF golden copy LEI for all legal entities",       0.99, None, "GLEIF /lei-records API direct match"),

    # ── COMPLIANCE ────────────────────────────────────────────────────────────

    ("adverse_media_flag",   "GDELT Project",          1, "direct",       "GDELT negative sentiment + entity mention flag",     0.75, "tone<-3 AND mention_count>5", "GDELT GKG adverse tone threshold"),
    ("adverse_media_flag",   "News API",               2, "direct",       "News API negative keyword + entity match",           0.68, None, "News API adverse media screening"),
    ("adverse_media_flag",   "OpenSanctions",          3, "direct",       "OpenSanctions adverse flag (PEP/sanction/criminal)",  0.90, None, "OpenSanctions entity adverse flag"),
]

# ─────────────────────────────────────────────────────────────────────────────

async def seed():
    reset = "--reset" in sys.argv

    async with AsyncSessionLocal() as db:
        # Load lookup maps
        kpi_map: dict[str, str] = {}
        for row in (await db.execute(select(ApplicationKpi))).scalars():
            kpi_map[row.slug] = row.id

        src_map: dict[str, str] = {}
        for row in (await db.execute(select(DataSource))).scalars():
            src_map[row.name] = row.id

        if reset:
            await db.execute(delete(KpiMapping))
            await db.commit()
            print("Existing mappings cleared.")

        created = skipped = missing = 0
        for (kpi_slug, source_name, priority, method, assumption, confidence, formula, note) in MAPPINGS:
            kpi_id = kpi_map.get(kpi_slug)
            src_id = src_map.get(source_name)

            if not kpi_id:
                print(f"  SKIP — KPI not found: {kpi_slug}")
                missing += 1
                continue
            if not src_id:
                print(f"  SKIP — Source not found: {source_name}")
                missing += 1
                continue

            # Check for existing current mapping (idempotent)
            existing = (await db.execute(
                select(KpiMapping).where(
                    KpiMapping.kpi_id == kpi_id,
                    KpiMapping.source_id == src_id,
                    KpiMapping.priority_order == priority,
                    KpiMapping.is_current == True,
                )
            )).scalar_one_or_none()

            if existing:
                skipped += 1
                continue

            db.add(KpiMapping(
                kpi_id=kpi_id,
                source_id=src_id,
                priority_order=priority,
                is_active=True,
                approximation_method=method,
                approximation_assumption=assumption,
                confidence_score=confidence,
                transform_formula=formula,
                change_note=note,
                version=1,
                is_current=True,
                created_by="normalization_model_v1",
            ))
            created += 1

        await db.commit()

    print(f"\n=== Normalization model applied ===")
    print(f"  Mappings created : {created}")
    print(f"  Already existed  : {skipped}")
    print(f"  Missing ref data : {missing}")
    print(f"  Total definitions: {len(MAPPINGS)}")


if __name__ == "__main__":
    asyncio.run(seed())
