"""
Seed script: loads all 103 data sources from the Excel export JSON,
seeds 50 platform KPIs, then runs assessment on each source.

Usage:
  python scripts/seed.py
"""
import asyncio, sys, os, json, uuid, re
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ["DATABASE_URL"]
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DB_URL.startswith("postgresql://"):
    DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


# ── KPI catalogue ─────────────────────────────────────────────────────────────

KPIS = [
    # Emissions
    {"slug": "scope1_ghg_emissions",      "name": "Scope 1 GHG Emissions",             "category": "emissions",   "sub_category": "direct",      "unit": "tCO2e", "data_type": "number", "is_required": True,  "target_modules": ["carbon_calculator","pcaf_financed_emissions","csrd_issb_disclosure"], "tags": ["scope1","ghg","emissions","carbon"]},
    {"slug": "scope2_ghg_emissions",      "name": "Scope 2 GHG Emissions",             "category": "emissions",   "sub_category": "indirect",    "unit": "tCO2e", "data_type": "number", "is_required": True,  "target_modules": ["carbon_calculator","pcaf_financed_emissions","csrd_issb_disclosure"], "tags": ["scope2","ghg","emissions","carbon"]},
    {"slug": "scope3_ghg_emissions",      "name": "Scope 3 GHG Emissions",             "category": "emissions",   "sub_category": "value_chain", "unit": "tCO2e", "data_type": "number", "is_required": True,  "target_modules": ["carbon_calculator","pcaf_financed_emissions","supply_chain","csrd_issb_disclosure"], "tags": ["scope3","ghg","emissions","carbon","value_chain"]},
    {"slug": "total_ghg_emissions",       "name": "Total GHG Emissions (Scope 1+2+3)", "category": "emissions",   "sub_category": "total",       "unit": "tCO2e", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","pcaf_financed_emissions","csrd_issb_disclosure"], "tags": ["total","ghg","emissions","carbon"]},
    {"slug": "carbon_intensity_revenue",  "name": "Carbon Intensity (Revenue-based)",  "category": "emissions",   "sub_category": "intensity",   "unit": "tCO2e/MUSD", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","cbam_calculator","csrd_issb_disclosure"], "tags": ["carbon_intensity","intensity","waci"]},
    {"slug": "carbon_intensity_asset",    "name": "Carbon Intensity (Asset-based)",    "category": "emissions",   "sub_category": "intensity",   "unit": "tCO2e/MUSD_assets", "data_type": "number", "is_required": False, "target_modules": ["portfolio_analytics","pcaf_financed_emissions"], "tags": ["carbon_intensity","intensity","pcaf"]},
    {"slug": "waci",                      "name": "Weighted Average Carbon Intensity",  "category": "emissions",   "sub_category": "portfolio",   "unit": "tCO2e/MUSD_revenue", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","csrd_issb_disclosure"], "tags": ["waci","portfolio","carbon"]},
    {"slug": "grid_emission_factor",      "name": "Grid Emission Factor",              "category": "emissions",   "sub_category": "energy",      "unit": "tCO2e/MWh", "data_type": "number", "is_required": False, "target_modules": ["carbon_calculator","stranded_assets"], "tags": ["grid","emission_factor","scope2","energy"]},
    # Financial
    {"slug": "market_cap",                "name": "Market Capitalisation",             "category": "financial",   "sub_category": "valuation",   "unit": "USD",   "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","pcaf_financed_emissions"], "tags": ["market_cap","equity","valuation"]},
    {"slug": "enterprise_value",          "name": "Enterprise Value",                  "category": "financial",   "sub_category": "valuation",   "unit": "USD",   "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","pcaf_financed_emissions","real_estate_valuation"], "tags": ["ev","enterprise_value","valuation"]},
    {"slug": "evic",                      "name": "Enterprise Value Including Cash",   "category": "financial",   "sub_category": "valuation",   "unit": "USD",   "data_type": "number", "is_required": True,  "target_modules": ["pcaf_financed_emissions"], "tags": ["evic","pcaf","attribution"]},
    {"slug": "revenue",                   "name": "Revenue",                           "category": "financial",   "sub_category": "income",      "unit": "USD",   "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","pcaf_financed_emissions","csrd_issb_disclosure"], "tags": ["revenue","income","financials"]},
    {"slug": "total_assets",              "name": "Total Assets",                      "category": "financial",   "sub_category": "balance_sheet","unit": "USD",  "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","pcaf_financed_emissions"], "tags": ["total_assets","balance_sheet","financials"]},
    {"slug": "ebitda",                    "name": "EBITDA",                            "category": "financial",   "sub_category": "income",      "unit": "USD",   "data_type": "number", "is_required": False, "target_modules": ["portfolio_analytics","ecl_calculator"], "tags": ["ebitda","profitability","financials"]},
    {"slug": "stock_price",               "name": "Stock Price",                       "category": "financial",   "sub_category": "market",      "unit": "USD",   "data_type": "number", "is_required": False, "target_modules": ["portfolio_analytics"], "tags": ["stock","price","market_data"]},
    # ESG
    {"slug": "esg_score_overall",         "name": "ESG Score (Overall)",               "category": "esg",         "sub_category": "rating",      "unit": "0-100", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","sustainability_calculator","csrd_issb_disclosure"], "tags": ["esg","score","rating"]},
    {"slug": "environmental_score",       "name": "Environmental Score (E pillar)",    "category": "esg",         "sub_category": "rating",      "unit": "0-100", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","csrd_issb_disclosure"], "tags": ["esg","environmental","pillar"]},
    {"slug": "social_score",              "name": "Social Score (S pillar)",           "category": "esg",         "sub_category": "rating",      "unit": "0-100", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","csrd_issb_disclosure"], "tags": ["esg","social","pillar"]},
    {"slug": "governance_score",          "name": "Governance Score (G pillar)",       "category": "esg",         "sub_category": "rating",      "unit": "0-100", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","csrd_issb_disclosure"], "tags": ["esg","governance","pillar"]},
    {"slug": "esg_controversy_score",     "name": "ESG Controversy Score",            "category": "esg",         "sub_category": "controversy", "unit": "0-100", "data_type": "number", "is_required": False, "target_modules": ["portfolio_analytics","sustainability_calculator"], "tags": ["esg","controversy","reputational_risk"]},
    {"slug": "cdp_climate_score",         "name": "CDP Climate Disclosure Score",      "category": "esg",         "sub_category": "disclosure",  "unit": "A-D",   "data_type": "string", "is_required": False, "target_modules": ["sustainability_calculator","csrd_issb_disclosure"], "tags": ["cdp","climate","disclosure"]},
    {"slug": "msci_esg_rating",           "name": "MSCI ESG Rating",                  "category": "esg",         "sub_category": "rating",      "unit": "AAA-CCC","data_type": "string","is_required": False, "target_modules": ["portfolio_analytics","sustainability_calculator"], "tags": ["msci","esg","rating"]},
    # Risk
    {"slug": "probability_of_default",   "name": "Probability of Default (PD)",       "category": "risk",        "sub_category": "credit",      "unit": "%",     "data_type": "number", "is_required": True,  "target_modules": ["pd_calculator","ecl_calculator","portfolio_analytics"], "tags": ["pd","credit_risk","default"]},
    {"slug": "expected_credit_loss",     "name": "Expected Credit Loss (ECL)",        "category": "risk",        "sub_category": "credit",      "unit": "USD",   "data_type": "number", "is_required": True,  "target_modules": ["ecl_calculator","portfolio_analytics"], "tags": ["ecl","credit_risk","ifrs9"]},
    {"slug": "physical_risk_score",      "name": "Physical Climate Risk Score",       "category": "risk",        "sub_category": "climate",     "unit": "0-100", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","scenario_analysis","stranded_assets"], "tags": ["physical_risk","climate","ngfs"]},
    {"slug": "transition_risk_score",    "name": "Transition Climate Risk Score",     "category": "risk",        "sub_category": "climate",     "unit": "0-100", "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","scenario_analysis","stranded_assets"], "tags": ["transition_risk","climate","ngfs"]},
    {"slug": "stranded_asset_value_at_risk","name": "Stranded Asset Value at Risk",   "category": "risk",        "sub_category": "stranded",    "unit": "USD",   "data_type": "number", "is_required": False, "target_modules": ["stranded_assets","portfolio_analytics"], "tags": ["stranded","var","asset"]},
    {"slug": "water_risk_score",         "name": "Water Risk Score",                  "category": "risk",        "sub_category": "nature",      "unit": "0-5",   "data_type": "number", "is_required": False, "target_modules": ["nature_risk_tnfd","portfolio_analytics"], "tags": ["water","nature","tnfd","aqueduct"]},
    {"slug": "biodiversity_risk_score",  "name": "Biodiversity Risk Score",           "category": "risk",        "sub_category": "nature",      "unit": "0-5",   "data_type": "number", "is_required": False, "target_modules": ["nature_risk_tnfd","portfolio_analytics"], "tags": ["biodiversity","nature","tnfd","wdpa"]},
    {"slug": "sanctions_flag",           "name": "Sanctions Flag",                    "category": "risk",        "sub_category": "compliance",  "unit": "boolean","data_type":"boolean","is_required": True,  "target_modules": ["regulatory_compliance","portfolio_analytics"], "tags": ["sanctions","ofac","compliance","aml"]},
    # Regulatory / alignment
    {"slug": "temperature_alignment",    "name": "Temperature Alignment (°C)",        "category": "regulatory",  "sub_category": "climate",     "unit": "°C",    "data_type": "number", "is_required": True,  "target_modules": ["portfolio_analytics","csrd_issb_disclosure","scenario_analysis"], "tags": ["temperature","alignment","paris","sbti"]},
    {"slug": "sbti_target_status",       "name": "SBTi Target Status",               "category": "regulatory",  "sub_category": "climate",     "unit": "status","data_type": "string", "is_required": False, "target_modules": ["sustainability_calculator","csrd_issb_disclosure"], "tags": ["sbti","target","net_zero"]},
    {"slug": "eu_taxonomy_aligned_pct",  "name": "EU Taxonomy Alignment (%)",        "category": "regulatory",  "sub_category": "eu_taxonomy", "unit": "%",     "data_type": "number", "is_required": False, "target_modules": ["csrd_issb_disclosure","regulatory_compliance"], "tags": ["eu_taxonomy","sfdr","green_finance"]},
    {"slug": "sfdr_pai_value",           "name": "SFDR PAI Indicator Value",         "category": "regulatory",  "sub_category": "sfdr",        "unit": "varies","data_type": "number", "is_required": False, "target_modules": ["csrd_issb_disclosure","regulatory_compliance"], "tags": ["sfdr","pai","disclosure"]},
    {"slug": "csrd_esrs_dp_value",       "name": "CSRD / ESRS Datapoint Value",      "category": "regulatory",  "sub_category": "csrd",        "unit": "varies","data_type": "string", "is_required": False, "target_modules": ["csrd_issb_disclosure"], "tags": ["csrd","esrs","disclosure"]},
    {"slug": "cbam_embedded_carbon",     "name": "CBAM Embedded Carbon",             "category": "regulatory",  "sub_category": "cbam",        "unit": "tCO2e", "data_type": "number", "is_required": False, "target_modules": ["cbam_calculator","regulatory_compliance"], "tags": ["cbam","eu","carbon_border"]},
    {"slug": "tcfd_alignment_score",     "name": "TCFD Alignment Score",             "category": "regulatory",  "sub_category": "tcfd",        "unit": "0-100", "data_type": "number", "is_required": False, "target_modules": ["csrd_issb_disclosure","regulatory_compliance"], "tags": ["tcfd","disclosure","climate"]},
    # Carbon price / scenario
    {"slug": "carbon_price",             "name": "Carbon Price",                      "category": "scenario",    "sub_category": "macro",       "unit": "USD/tCO2e","data_type":"number","is_required": True,  "target_modules": ["scenario_analysis","carbon_calculator","stranded_assets"], "tags": ["carbon_price","macro","ngfs"]},
    {"slug": "ngfs_scenario_variable",   "name": "NGFS Scenario Variable",           "category": "scenario",    "sub_category": "ngfs",        "unit": "varies","data_type": "number", "is_required": True,  "target_modules": ["scenario_analysis","portfolio_analytics"], "tags": ["ngfs","scenario","climate"]},
    {"slug": "crrem_glidepath",          "name": "CRREM Decarbonisation Glidepath",  "category": "scenario",    "sub_category": "real_estate", "unit": "kgCO2/m²","data_type":"number","is_required": False, "target_modules": ["real_estate_valuation","stranded_assets"], "tags": ["crrem","real_estate","glidepath"]},
    # Supply chain / nature
    {"slug": "scope3_upstream_intensity","name": "Scope 3 Upstream Intensity",        "category": "supply_chain","sub_category": "emissions",   "unit": "tCO2e/unit","data_type":"number","is_required": False,"target_modules": ["supply_chain","carbon_calculator"], "tags": ["scope3","upstream","supply_chain"]},
    {"slug": "deforestation_risk",       "name": "Deforestation Risk Score",          "category": "nature",      "sub_category": "biodiversity","unit": "0-5",   "data_type": "number", "is_required": False, "target_modules": ["nature_risk_tnfd","supply_chain"], "tags": ["deforestation","eudr","nature"]},
    {"slug": "tnfd_leap_score",          "name": "TNFD LEAP Assessment Score",       "category": "nature",      "sub_category": "tnfd",        "unit": "0-100", "data_type": "number", "is_required": False, "target_modules": ["nature_risk_tnfd"], "tags": ["tnfd","leap","biodiversity","nature"]},
    # Energy sector
    {"slug": "lcoe",                     "name": "Levelised Cost of Energy (LCOE)",  "category": "energy",      "sub_category": "cost",        "unit": "USD/MWh","data_type":"number","is_required": False, "target_modules": ["stranded_assets","sector_assessments"], "tags": ["lcoe","energy","irena","power_plant"]},
    {"slug": "capacity_factor",          "name": "Plant Capacity Factor",            "category": "energy",      "sub_category": "operations",  "unit": "%",     "data_type": "number", "is_required": False, "target_modules": ["stranded_assets","sector_assessments"], "tags": ["capacity","power_plant","energy"]},
    # Social / workforce
    {"slug": "gender_pay_gap",           "name": "Gender Pay Gap",                   "category": "social",      "sub_category": "workforce",   "unit": "%",     "data_type": "number", "is_required": False, "target_modules": ["csrd_issb_disclosure","sustainability_calculator"], "tags": ["gender","pay_gap","social","csrd"]},
    {"slug": "employee_satisfaction",    "name": "Employee Satisfaction Score",      "category": "social",      "sub_category": "workforce",   "unit": "0-5",   "data_type": "number", "is_required": False, "target_modules": ["sustainability_calculator"], "tags": ["employee","glassdoor","social"]},
    {"slug": "board_diversity_pct",      "name": "Board Gender Diversity (%)",       "category": "governance",  "sub_category": "board",       "unit": "%",     "data_type": "number", "is_required": False, "target_modules": ["csrd_issb_disclosure","sustainability_calculator"], "tags": ["board","diversity","governance"]},
    {"slug": "news_esg_sentiment",       "name": "ESG News Sentiment Score",         "category": "esg",         "sub_category": "sentiment",   "unit": "-1 to 1","data_type":"number","is_required": False, "target_modules": ["portfolio_analytics","controversy_screening"], "tags": ["news","sentiment","esg","controversy"]},
    {"slug": "lei_number",               "name": "Legal Entity Identifier (LEI)",    "category": "reference",   "sub_category": "entity",      "unit": "LEI",   "data_type": "string", "is_required": True,  "target_modules": ["pcaf_financed_emissions","portfolio_analytics","entity_resolution"], "tags": ["lei","gleif","entity","reference"]},
    {"slug": "adverse_media_flag",       "name": "Adverse Media / Controversy Flag", "category": "compliance",  "sub_category": "screening",   "unit": "boolean","data_type":"boolean","is_required": False, "target_modules": ["regulatory_compliance","portfolio_analytics"], "tags": ["adverse_media","controversy","compliance"]},
]

# ── Source record normaliser ──────────────────────────────────────────────────

def _norm(source_row: dict) -> dict:
    """Map Excel column names → DB column names and clean values."""
    def v(key: str, alt: str = "") -> str | None:
        val = source_row.get(key) or source_row.get(alt)
        if val is None or (isinstance(val, float) and val != val):  # NaN
            return None
        s = str(val).strip()
        return s if s and s not in ("nan", "None", "N/A", "n/a") else None

    def num(key: str, alt: str = "") -> float | None:
        val = source_row.get(key) or source_row.get(alt)
        try:
            f = float(val)
            return None if f != f else f
        except (TypeError, ValueError):
            return None

    # Map API/Access → access_type
    raw_access = v("API/Access", "access_type") or ""
    if "Web Scrape" in raw_access or "Puppeteer" in raw_access:
        access_type = "Web Scrape"
    elif "Apify" in raw_access:
        access_type = "Apify Scraper"
    elif "CSV" in raw_access:
        access_type = "CSV Download"
    elif "Python" in raw_access:
        access_type = "Python Library"
    elif "OAuth" in raw_access:
        access_type = "OAuth API"
    elif "S3" in raw_access:
        access_type = "S3 Download"
    elif "REST" in raw_access or "API" in raw_access:
        access_type = "REST API"
    elif "MANUAL" in raw_access or "Manual" in raw_access:
        access_type = "Manual"
    else:
        access_type = raw_access or "REST API"

    return {
        "id":              str(uuid.uuid4()),
        "name":            v("Source Name", "name"),
        "category":        v("Category", "category"),
        "sub_category":    v("Sub-Category", "sub_category"),
        "rationale":       v("Rationale", "rationale"),
        "access_type":     access_type,
        "base_url":        v("Base URL", "base_url"),
        "key_endpoints":   v("Key Endpoints", "key_endpoints"),
        "auth_method":     v("Auth", "auth_method"),
        "auth_detail":     v("Auth Method (Detail)", "auth_detail"),
        "auth_signup_url": v("Auth/Signup URL", "auth_signup_url"),
        "sample_request":  v("Sample Request", "sample_request"),
        "sdk_library":     v("SDK / Library", "sdk_library"),
        "docs_url":        v("Docs URL", "docs_url"),
        "integration_notes": v("Integration Notes", "integration_notes"),
        "response_format": v("Response Format (Detail)", "response_format"),
        "cost":            v("Cost", "cost"),
        "rate_limit":      v("Rate Limit", "rate_limit"),
        "rate_limit_detail": v("Rate Limit (Detail)", "rate_limit_detail"),
        "data_format":     v("Data Format", "data_format"),
        "update_freq":     v("Update Freq", "update_freq"),
        "geographic":      v("Geographic", "geographic"),
        "quality_rating":  v("Quality", "quality_rating"),
        "batch":           int(source_row.get("Batch", 0) or 0) or None,
        "status":          (v("Status", "status") or "planned").lower(),
        "credentials":     {},
        "est_rows_month":  int(source_row.get("Est Rows/Month", 0) or 0) or None,
        "est_gb_month":    num("Est GB/Month"),
        "sync_enabled":    False,
    }


Optional = type(None)  # workaround for bare Optional usage above


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    from database import Base
    from models.models import DataSource, ApplicationKpi, SourceAssessment
    from services.assessment_engine import assess_source

    engine = create_async_engine(DB_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created / verified.")

    # Load raw source JSON
    json_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "sources_all.json")
    alt_path  = "C:/Users/SahilChopra/AppData/Local/Temp/sources_all.json"
    raw_path  = json_path if os.path.exists(json_path) else alt_path

    if not os.path.exists(raw_path):
        print(f"ERROR: sources JSON not found at {raw_path}. Run the Excel extraction step first.")
        return

    with open(raw_path) as f:
        raw_sources = json.load(f)
    print(f"Loaded {len(raw_sources)} raw source rows.")

    async with Session() as session:
        # ── Seed KPIs ────────────────────────────────────────────────────────
        kpi_count = 0
        for kpi_data in KPIS:
            existing = await session.execute(
                select(ApplicationKpi).where(ApplicationKpi.slug == kpi_data["slug"])
            )
            if existing.scalar_one_or_none():
                continue
            kpi = ApplicationKpi(id=str(uuid.uuid4()), **kpi_data)
            session.add(kpi)
            kpi_count += 1
        await session.commit()
        print(f"KPIs seeded: {kpi_count} new.")

        # ── Seed sources ─────────────────────────────────────────────────────
        src_count = 0
        for raw in raw_sources:
            normed = _norm(raw)
            if not normed.get("name"):
                continue

            existing = await session.execute(
                select(DataSource).where(DataSource.name == normed["name"])
            )
            if existing.scalar_one_or_none():
                continue

            # Run assessment
            assessment_result = assess_source({**raw, **normed})
            normed["priority"]         = assessment_result["priority"]
            normed["utility"]          = assessment_result["utility"]
            normed["assessment_score"] = assessment_result["total_score"]

            source = DataSource(**normed)
            session.add(source)
            await session.flush()

            # Persist assessment
            assessment = SourceAssessment(
                id=str(uuid.uuid4()),
                source_id=source.id,
                **assessment_result,
                assessed_by="auto",
            )
            session.add(assessment)
            src_count += 1

        await session.commit()
        print(f"Sources seeded: {src_count} new.")

    # Summary
    async with Session() as session:
        from sqlalchemy import func
        total_s = (await session.execute(select(func.count()).select_from(DataSource))).scalar()
        total_k = (await session.execute(select(func.count()).select_from(ApplicationKpi))).scalar()
        p0 = (await session.execute(select(func.count()).where(DataSource.priority == "P0"))).scalar()
        p1 = (await session.execute(select(func.count()).where(DataSource.priority == "P1"))).scalar()
        p2 = (await session.execute(select(func.count()).where(DataSource.priority == "P2"))).scalar()

    print(f"\n=== Seed complete ===")
    print(f"  Total sources : {total_s}")
    print(f"  Total KPIs    : {total_k}")
    print(f"  P0 sources    : {p0}")
    print(f"  P1 sources    : {p1}")
    print(f"  P2 sources    : {p2}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
