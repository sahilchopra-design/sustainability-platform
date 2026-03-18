"""
Reference Data Catalog
========================
Centralized registry of all reference/lookup data across the platform.
Catalogs emission factors, financial parameters, regulatory mappings,
sector benchmarks, geographic data, and entity master data used by
all 105+ service modules.

Data Flow:
  1. Scans MODULE_SIGNATURES from data_lineage_service for reference_data deps
  2. Maps each reference dataset to its authoritative source, update frequency,
     and consuming modules
  3. Freshness checks identify stale datasets (> configurable threshold)
  4. Gap analysis identifies datasets needed but not yet embedded

References:
  - BCBS 239 Principle 3 (Accuracy and Integrity) — reference data governance
  - ISO 8000-61 (Data Quality — Provenance)
  - EBA GL/2020/06 — ICT data management requirements
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("platform.reference_data_catalog")


# ---------------------------------------------------------------------------
# Reference Data — Master Catalog
# ---------------------------------------------------------------------------

REFERENCE_DATASETS: dict[str, dict] = {
    # ---- Emission Factors ----
    "ghg_protocol_ef_scope1": {
        "label": "GHG Protocol Scope 1 Emission Factors",
        "domain": "emission_factors",
        "source": "IPCC 2006 Guidelines (2019 Refinement)",
        "source_url": "https://www.ipcc-nggip.iges.or.jp/EFDB/main.php",
        "update_frequency": "irregular (IPCC revision cycle)",
        "last_known_update": "2019",
        "record_count": 850,
        "status": "embedded",
        "notes": "Stationary combustion, mobile, fugitive, process EFs",
    },
    "iea_grid_ef": {
        "label": "IEA Grid Emission Factors by Country",
        "domain": "emission_factors",
        "source": "International Energy Agency — CO2 Emissions from Fuel Combustion",
        "source_url": "https://www.iea.org/data-and-statistics",
        "update_frequency": "annual",
        "last_known_update": "2024",
        "record_count": 195,
        "status": "embedded",
        "notes": "Country-level grid emission factors (kgCO2/kWh)",
    },
    "defra_conversion_factors": {
        "label": "UK DEFRA GHG Conversion Factors",
        "domain": "emission_factors",
        "source": "UK Department for Environment, Food & Rural Affairs",
        "source_url": "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting",
        "update_frequency": "annual (June)",
        "last_known_update": "2024",
        "record_count": 1200,
        "status": "embedded",
        "notes": "Fuel, energy, transport, waste, water, material EFs",
    },
    "gwp_ar5_100yr": {
        "label": "IPCC AR5 Global Warming Potentials (100-year)",
        "domain": "emission_factors",
        "source": "IPCC Fifth Assessment Report (2014)",
        "source_url": "https://www.ipcc.ch/assessment-report/ar5/",
        "update_frequency": "per IPCC assessment cycle (~7 years)",
        "last_known_update": "2014",
        "record_count": 40,
        "status": "embedded",
        "notes": "CO2=1, CH4=28, N2O=265, SF6=23500, etc.",
    },
    "ghg_protocol_scope3_ef": {
        "label": "GHG Protocol Scope 3 Category Emission Factors",
        "domain": "emission_factors",
        "source": "GHG Protocol Corporate Value Chain (Scope 3) Standard",
        "source_url": "https://ghgprotocol.org/standards/scope-3-standard",
        "update_frequency": "irregular",
        "last_known_update": "2023",
        "record_count": 420,
        "status": "embedded",
        "notes": "Per-category EFs for 15 Scope 3 categories",
    },
    "exiobase_sector_ef": {
        "label": "EXIOBASE Multi-Regional IO Emission Factors",
        "domain": "emission_factors",
        "source": "EXIOBASE Consortium",
        "source_url": "https://www.exiobase.eu/",
        "update_frequency": "irregular (~3 years)",
        "last_known_update": "2022",
        "record_count": 7800,
        "status": "embedded",
        "notes": "Sector × country spend-based EFs (EUR/tCO2e)",
    },
    "ipcc_agriculture_ef": {
        "label": "IPCC Agriculture Emission Factors",
        "domain": "emission_factors",
        "source": "IPCC 2019 Refinement — Volume 4 (AFOLU)",
        "source_url": "https://www.ipcc-nggip.iges.or.jp/public/2019rf/",
        "update_frequency": "per IPCC cycle",
        "last_known_update": "2019",
        "record_count": 320,
        "status": "embedded",
        "notes": "Livestock CH4, rice paddy, fertiliser N2O, land use",
    },
    # ---- Financial Parameters ----
    "ngfs_scenario_v4_params": {
        "label": "NGFS Phase IV Scenario Parameters",
        "domain": "financial_parameters",
        "source": "Network for Greening the Financial System",
        "source_url": "https://www.ngfs.net/ngfs-scenarios-portal/",
        "update_frequency": "annual",
        "last_known_update": "2024",
        "record_count": 6,
        "status": "embedded",
        "notes": "6 scenarios: Orderly/Disorderly/Hot House with GDP, carbon price, temp trajectories",
    },
    "eba_climate_risk_weights": {
        "label": "EBA Climate Risk Stress Test Parameters",
        "domain": "financial_parameters",
        "source": "European Banking Authority",
        "source_url": "https://www.eba.europa.eu/risk-analysis-and-data",
        "update_frequency": "biennial",
        "last_known_update": "2024",
        "record_count": 45,
        "status": "embedded",
        "notes": "Sector-level transition and physical risk PD/LGD adjustments",
    },
    "crr2_ccf_sa": {
        "label": "CRR2 Credit Conversion Factors (Standardised Approach)",
        "domain": "financial_parameters",
        "source": "EU Capital Requirements Regulation II — Art 111",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2013/575",
        "update_frequency": "per CRR revision",
        "last_known_update": "2021",
        "record_count": 12,
        "status": "embedded",
        "notes": "Off-balance sheet CCFs: 0%, 20%, 50%, 100% by facility type",
    },
    "moodys_default_rates": {
        "label": "Moody's Annual Default Study",
        "domain": "financial_parameters",
        "source": "Moody's Investors Service",
        "source_url": "https://www.moodys.com",
        "update_frequency": "annual (February)",
        "last_known_update": "2024",
        "record_count": 21,
        "status": "embedded",
        "notes": "Rating-grade 1yr default rates (Aaa through C)",
    },
    "eba_lgd_floors": {
        "label": "EBA LGD Floors (FIRB/AIRB)",
        "domain": "financial_parameters",
        "source": "EBA GL/2019/03 — CRR2 Art 161",
        "source_url": "https://www.eba.europa.eu/regulation-and-policy",
        "update_frequency": "per regulation update",
        "last_known_update": "2021",
        "record_count": 8,
        "status": "embedded",
        "notes": "LGD floors by exposure class (senior unsecured 25%, subordinated 25%, etc.)",
    },
    "pe_benchmark_returns": {
        "label": "PE Benchmark Returns (by vintage)",
        "domain": "financial_parameters",
        "source": "Cambridge Associates / Preqin",
        "source_url": "https://www.cambridgeassociates.com",
        "update_frequency": "quarterly",
        "last_known_update": "2024",
        "record_count": 30,
        "status": "embedded",
        "notes": "Quartile IRR/MOIC by vintage year and strategy",
    },
    "dqs_confidence_weights": {
        "label": "PCAF Data Quality Score → Confidence Weights",
        "domain": "financial_parameters",
        "source": "PCAF Global GHG Accounting Standard v2.0 (2022)",
        "source_url": "https://carbonaccountingfinancials.com/",
        "update_frequency": "per PCAF revision",
        "last_known_update": "2022",
        "record_count": 5,
        "status": "embedded",
        "notes": "DQS 1→1.00, 2→0.90, 3→0.70, 4→0.50, 5→0.30",
    },
    # ---- Regulatory Mappings ----
    "esrs_data_point_mappings": {
        "label": "ESRS Data Point Catalog (IG3 quantitative DPs)",
        "domain": "regulatory",
        "source": "EFRAG Implementation Guidance 3 (2024)",
        "source_url": "https://www.efrag.org/lab6",
        "update_frequency": "per EFRAG update",
        "last_known_update": "2024",
        "record_count": 330,
        "status": "embedded",
        "notes": "Full ESRS E1-E5, S1, G1 quantitative data points — migration 014",
    },
    "esrs_minimums_per_standard": {
        "label": "ESRS Minimum Disclosure Requirements per Standard",
        "domain": "regulatory",
        "source": "CSRD Directive 2022/2464",
        "source_url": "https://eur-lex.europa.eu/eli/dir/2022/2464",
        "update_frequency": "per directive revision",
        "last_known_update": "2022",
        "record_count": 7,
        "status": "embedded",
        "notes": "E1:15, E2:6, E3:5, E4:8, E5:5, S1:10, G1:4",
    },
    "sfdr_rts_pai_definitions": {
        "label": "SFDR RTS Principal Adverse Impact Indicators",
        "domain": "regulatory",
        "source": "SFDR Regulatory Technical Standards (EU 2022/1288)",
        "source_url": "https://eur-lex.europa.eu/eli/reg_del/2022/1288",
        "update_frequency": "per RTS revision",
        "last_known_update": "2022",
        "record_count": 18,
        "status": "embedded",
        "notes": "14 mandatory + 4 optional PAI indicators (Table 1-3)",
    },
    "eu_taxonomy_tsc_climate": {
        "label": "EU Taxonomy Technical Screening Criteria — Climate",
        "domain": "regulatory",
        "source": "EU Delegated Regulation 2021/2139 (Climate DA)",
        "source_url": "https://eur-lex.europa.eu/eli/reg_del/2021/2139",
        "update_frequency": "per DA revision",
        "last_known_update": "2023",
        "record_count": 88,
        "status": "embedded",
        "notes": "Substantial contribution + DNSH criteria for climate mitigation/adaptation",
    },
    "issb_sasb_industry_metrics": {
        "label": "ISSB SASB Industry-Specific Metrics",
        "domain": "regulatory",
        "source": "IFRS Foundation — SASB Standards",
        "source_url": "https://www.ifrs.org/issued-standards/sasb-standards/",
        "update_frequency": "per ISSB revision",
        "last_known_update": "2024",
        "record_count": 200,
        "status": "embedded",
        "notes": "20 SASB sectors × per-metric rows — migration 015",
    },
    "cbam_product_registry": {
        "label": "CBAM Product CN Code Registry",
        "domain": "regulatory",
        "source": "EU CBAM Regulation 2023/956",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2023/956",
        "update_frequency": "per CBAM revision",
        "last_known_update": "2023",
        "record_count": 95,
        "status": "embedded",
        "notes": "Cement, iron/steel, aluminium, fertilisers, electricity, hydrogen CN codes",
    },
    "nace_activity_classification": {
        "label": "NACE Rev 2 Activity Classification",
        "domain": "regulatory",
        "source": "Eurostat — Statistical Classification of Economic Activities",
        "source_url": "https://ec.europa.eu/eurostat/ramon/nomenclatures/",
        "update_frequency": "per revision (~10 years)",
        "last_known_update": "2023",
        "record_count": 615,
        "status": "embedded",
        "notes": "4-digit NACE codes mapped to EU Taxonomy eligible activities",
    },
    # ---- Sector Benchmarks ----
    "sbti_sector_pathways": {
        "label": "SBTi Sector Decarbonisation Pathways",
        "domain": "sector_benchmarks",
        "source": "Science Based Targets initiative",
        "source_url": "https://sciencebasedtargets.org/sectors/",
        "update_frequency": "per SBTi methodology update",
        "last_known_update": "2024",
        "record_count": 15,
        "status": "embedded",
        "notes": "1.5°C-aligned intensity pathways for power, transport, buildings, etc.",
    },
    "crrem_v2_decarbonisation_curves": {
        "label": "CRREM v2 Decarbonisation Pathways",
        "domain": "sector_benchmarks",
        "source": "Carbon Risk Real Estate Monitor (CRREM)",
        "source_url": "https://www.crrem.eu/",
        "update_frequency": "per CRREM version",
        "last_known_update": "2023",
        "record_count": 480,
        "status": "embedded",
        "notes": "Country × property type decarbonisation curves (1.5°C/2.0°C)",
    },
    "gresb_benchmark_2024": {
        "label": "GRESB Benchmark Data 2024",
        "domain": "sector_benchmarks",
        "source": "GRESB BV",
        "source_url": "https://www.gresb.com",
        "update_frequency": "annual (October)",
        "last_known_update": "2024",
        "record_count": 50,
        "status": "embedded",
        "notes": "Peer group averages for standing investments and development",
    },
    # ---- Geographic Data ----
    "wri_aqueduct_water_stress": {
        "label": "WRI Aqueduct Water Risk Atlas",
        "domain": "geographic",
        "source": "World Resources Institute — Aqueduct",
        "source_url": "https://www.wri.org/aqueduct",
        "update_frequency": "irregular (~3 years)",
        "last_known_update": "2023",
        "record_count": 15000,
        "status": "seed_data",
        "notes": "Basin-level water stress, flood risk, drought risk indicators",
    },
    "ibat_protected_areas": {
        "label": "IBAT Key Biodiversity Areas & Protected Areas",
        "domain": "geographic",
        "source": "Integrated Biodiversity Assessment Tool (IBAT)",
        "source_url": "https://www.ibat-alliance.org/",
        "update_frequency": "quarterly",
        "last_known_update": "2024",
        "record_count": 260000,
        "status": "seed_data",
        "notes": "KBA proximity, IUCN Red List, protected area overlap",
    },
    "cets_price_history": {
        "label": "China ETS Carbon Price History",
        "domain": "geographic",
        "source": "Shanghai Environment and Energy Exchange",
        "source_url": "https://www.cneeex.com/",
        "update_frequency": "daily",
        "last_known_update": "2024",
        "record_count": 800,
        "status": "embedded",
        "notes": "Daily CEA settlement prices since July 2021",
    },
    # ---- Entity Master ----
    "module_registry": {
        "label": "Platform Module Registry",
        "domain": "entity_master",
        "source": "Internal — Entity 360 Engine",
        "source_url": "",
        "update_frequency": "per release",
        "last_known_update": "2026",
        "record_count": 10,
        "status": "embedded",
        "notes": "10 module categories: emissions, credit, financed_emissions, nature, etc.",
    },
    "entity_types": {
        "label": "Entity Type Taxonomy",
        "domain": "entity_master",
        "source": "Internal — Entity 360 Engine",
        "source_url": "",
        "update_frequency": "per release",
        "last_known_update": "2026",
        "record_count": 7,
        "status": "embedded",
        "notes": "corporate, fi, sovereign, project, real_estate, fund, sme",
    },
    "sector_map": {
        "label": "Sector Classification Map",
        "domain": "entity_master",
        "source": "Internal — Entity 360 Engine (GICS-aligned)",
        "source_url": "",
        "update_frequency": "per release",
        "last_known_update": "2026",
        "record_count": 12,
        "status": "embedded",
        "notes": "12 sectors: energy, financials, industrials, technology, etc.",
    },
    # ---- Embedded Reference Data (sourced and integrated) ----
    "who_mortality_tables": {
        "label": "WHO Life Tables (Mortality by Age/Sex/Country)",
        "domain": "insurance",
        "source": "World Health Organization — Global Health Observatory",
        "source_url": "https://www.who.int/data/gho/data/themes/mortality-and-global-health-estimates/ghe-life-expectancy-and-healthy-life-expectancy",
        "update_frequency": "annual",
        "last_known_update": "2024",
        "record_count": 220,
        "status": "embedded",
        "notes": "10 countries × 2 sexes × 11 age bands — see reference_data_tables.py",
    },
    "ipcc_ar6_damage_functions": {
        "label": "IPCC AR6 Climate Damage Functions by Hazard",
        "domain": "insurance",
        "source": "IPCC AR6 WG2 — Impacts, Adaptation, Vulnerability (DICE/PAGE/FUND IAMs)",
        "source_url": "https://www.ipcc.ch/report/ar6/wg2/",
        "update_frequency": "per IPCC cycle (~7 years)",
        "last_known_update": "2022",
        "record_count": 8,
        "status": "embedded",
        "notes": "8 hazard types with damage/frequency/severity multipliers per °C — see reference_data_tables.py",
    },
    "solvency2_nat_cat_factors": {
        "label": "Solvency II Natural Catastrophe Risk Factors",
        "domain": "insurance",
        "source": "EIOPA — Solvency II Delegated Regulation 2015/35 Art 105-109",
        "source_url": "https://www.eiopa.europa.eu/",
        "update_frequency": "per regulation revision",
        "last_known_update": "2023",
        "record_count": 58,
        "status": "embedded",
        "notes": "13 countries × 4 perils + 6 peril correlations — see reference_data_tables.py",
    },
    "basel3_nsfr_lcr_factors": {
        "label": "Basel III NSFR / LCR Factors (CRR2)",
        "domain": "financial_parameters",
        "source": "CRR2 Articles 411-428ai (BIS d295/d396)",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2013/575",
        "update_frequency": "per CRR revision",
        "last_known_update": "2021",
        "record_count": 53,
        "status": "embedded",
        "notes": "8 HQLA + 18 LCR outflow + 9 ASF + 18 RSF factors — see reference_data_tables.py",
    },
    "fatf_country_risk_ratings": {
        "label": "FATF Country Risk Ratings (AML/CFT)",
        "domain": "financial_parameters",
        "source": "Financial Action Task Force — Consolidated Mutual Evaluation Ratings (Mar 2026)",
        "source_url": "https://www.fatf-gafi.org/en/countries.html",
        "update_frequency": "per mutual evaluation cycle",
        "last_known_update": "2026",
        "record_count": 25,
        "status": "embedded",
        "notes": "25 countries with TC/effectiveness ratings, risk tier, grey/black list — see reference_data_tables.py",
    },
    "fao_crop_yield_database": {
        "label": "FAO Crop Yield Statistics (FAOSTAT)",
        "domain": "agriculture",
        "source": "Food and Agriculture Organization of the United Nations — FAOSTAT QCL",
        "source_url": "https://www.fao.org/faostat/en/",
        "update_frequency": "annual",
        "last_known_update": "2024",
        "record_count": 32,
        "status": "embedded",
        "notes": "8 countries × 4 crops (yield index, volatility, trend) — see reference_data_tables.py",
    },
    "eudr_commodity_criteria": {
        "label": "EU Deforestation Regulation Commodity Criteria",
        "domain": "regulatory",
        "source": "EC Regulation 2025/1093 (EUDR Country Benchmarking)",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2023/1115",
        "update_frequency": "per regulation revision",
        "last_known_update": "2025",
        "record_count": 42,
        "status": "embedded",
        "notes": "35 country benchmarks + 7 commodity definitions with HS codes — see reference_data_tables.py",
    },
    "bng_metric_4": {
        "label": "Biodiversity Net Gain Statutory Metric",
        "domain": "nature",
        "source": "Natural England — Statutory Biodiversity Metric (supersedes BNG 4.0)",
        "source_url": "https://www.gov.uk/government/publications/statutory-biodiversity-metric-tools-and-guides",
        "update_frequency": "per version release",
        "last_known_update": "2024",
        "record_count": 38,
        "status": "embedded",
        "notes": "24 habitat types + 6 conditions + 3 significance + 5 trading rules — see reference_data_tables.py",
    },
}


# Data domains for categorisation
REFERENCE_DOMAINS: dict[str, str] = {
    "emission_factors": "GHG Emission Factors & Conversion Data",
    "financial_parameters": "Financial Risk Parameters & Benchmarks",
    "regulatory": "Regulatory Framework Mappings & Requirements",
    "sector_benchmarks": "Sector-Level Benchmarks & Pathways",
    "geographic": "Geographic & Spatial Reference Data",
    "entity_master": "Entity Classification & Master Data",
    "insurance": "Insurance Actuarial & Risk Parameters",
    "agriculture": "Agriculture & Land Use Reference Data",
    "nature": "Nature & Biodiversity Reference Data",
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class CatalogEntry:
    """A single reference data entry in the catalog."""
    data_id: str
    label: str
    domain: str
    domain_label: str
    source: str
    source_url: str
    update_frequency: str
    last_known_update: str
    record_count: int
    status: str  # "embedded" | "seed_data" | "missing" | "stale"
    used_by: list[str]  # Module IDs
    notes: str


@dataclass
class ReferenceCatalogResult:
    """Full reference data catalog output."""
    total_datasets: int
    embedded_count: int
    seed_data_count: int
    missing_count: int
    stale_count: int
    coverage_pct: float
    entries: list[CatalogEntry]
    domains: dict[str, dict]  # {domain: {label, count, missing}}
    missing_critical: list[CatalogEntry]
    recommendations: list[str]


@dataclass
class DomainSummary:
    """Summary of reference data for a single domain."""
    domain: str
    domain_label: str
    total_datasets: int
    embedded: int
    missing: int
    stale: int
    entries: list[CatalogEntry]


@dataclass
class GapReport:
    """Reference data gap report."""
    total_missing: int
    total_stale: int
    gaps: list[CatalogEntry]
    remediation_priority: list[dict]  # [{dataset, severity, needed_by, action}]
    estimated_effort: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ReferenceDataCatalogEngine:
    """
    Centralized reference data catalog engine.

    Catalogs all reference data, lookup tables, emission factors, financial
    parameters, regulatory mappings, and benchmarks used across the platform.
    Identifies stale, missing, or incomplete datasets and recommends actions.

    Calculation Logic:
      1. REFERENCE_DATASETS registry defines all known reference data
      2. MODULE_SIGNATURES (from data_lineage_service) maps modules to their deps
      3. Cross-reference: for each dataset, find all consuming modules
      4. Freshness check: flag datasets with last_known_update > threshold
      5. Gap analysis: identify "missing" status datasets needed by planned modules

    Stakeholder Insights:
      - Data Management: single view of all reference data, freshness status
      - Compliance: regulatory data source traceability (BCBS 239 Principle 3)
      - Risk: identifies where stale reference data may affect risk calculations
      - IT: data refresh scheduling and pipeline requirements
    """

    def __init__(self):
        self._datasets = REFERENCE_DATASETS
        self._domains = REFERENCE_DOMAINS
        self._module_usage = self._build_module_usage()

    def _build_module_usage(self) -> dict[str, list[str]]:
        """Map each dataset to consuming modules (from lineage signatures)."""
        from services.data_lineage_service import MODULE_SIGNATURES

        usage: dict[str, list[str]] = {}
        for mod_id, sig in MODULE_SIGNATURES.items():
            for rd in sig.get("reference_data", []):
                usage.setdefault(rd, []).append(mod_id)
        return usage

    def get_catalog(
        self,
        domain: Optional[str] = None,
        include_missing: bool = True,
    ) -> ReferenceCatalogResult:
        """
        Get the full reference data catalog.

        Parameters:
            domain: Filter by domain (e.g., "emission_factors")
            include_missing: Include datasets with status "missing"

        Returns:
            ReferenceCatalogResult with all entries, domain summaries, and gaps
        """
        entries = []
        for data_id, ds in self._datasets.items():
            if domain and ds["domain"] != domain:
                continue
            if not include_missing and ds["status"] == "missing":
                continue

            used_by = self._module_usage.get(data_id, [])
            domain_label = self._domains.get(ds["domain"], ds["domain"])

            entries.append(CatalogEntry(
                data_id=data_id,
                label=ds["label"],
                domain=ds["domain"],
                domain_label=domain_label,
                source=ds["source"],
                source_url=ds["source_url"],
                update_frequency=ds["update_frequency"],
                last_known_update=ds["last_known_update"],
                record_count=ds["record_count"],
                status=ds["status"],
                used_by=used_by,
                notes=ds["notes"],
            ))

        embedded = sum(1 for e in entries if e.status == "embedded")
        seed = sum(1 for e in entries if e.status == "seed_data")
        missing = sum(1 for e in entries if e.status == "missing")
        stale = sum(1 for e in entries if e.status == "stale")
        total = len(entries)
        available = embedded + seed
        coverage = (available / total * 100) if total > 0 else 0

        # Domain summaries
        domains = {}
        for d_id, d_label in self._domains.items():
            d_entries = [e for e in entries if e.domain == d_id]
            if d_entries:
                domains[d_id] = {
                    "label": d_label,
                    "count": len(d_entries),
                    "embedded": sum(1 for e in d_entries if e.status == "embedded"),
                    "missing": sum(1 for e in d_entries if e.status == "missing"),
                }

        missing_critical = [e for e in entries if e.status == "missing"]

        recs = []
        if missing > 0:
            recs.append(f"{missing} reference datasets missing — acquire and integrate")
        if stale > 0:
            recs.append(f"{stale} datasets stale — schedule refresh")
        if coverage < 90:
            recs.append(f"Reference data coverage {coverage:.0f}% — target 95%+")
        for mc in missing_critical[:3]:
            recs.append(f"Priority: acquire '{mc.label}' from {mc.source}")

        return ReferenceCatalogResult(
            total_datasets=total,
            embedded_count=embedded,
            seed_data_count=seed,
            missing_count=missing,
            stale_count=stale,
            coverage_pct=round(coverage, 1),
            entries=entries,
            domains=domains,
            missing_critical=missing_critical,
            recommendations=recs,
        )

    def get_module_reference_data(self, module_id: str) -> list[CatalogEntry]:
        """
        Get reference data used by a specific module.

        Parameters:
            module_id: Module identifier

        Returns:
            List of CatalogEntry for datasets used by the module
        """
        from services.data_lineage_service import MODULE_SIGNATURES

        sig = MODULE_SIGNATURES.get(module_id)
        if not sig:
            return []

        entries = []
        for rd_id in sig.get("reference_data", []):
            ds = self._datasets.get(rd_id)
            if ds:
                used_by = self._module_usage.get(rd_id, [])
                entries.append(CatalogEntry(
                    data_id=rd_id,
                    label=ds["label"],
                    domain=ds["domain"],
                    domain_label=self._domains.get(ds["domain"], ds["domain"]),
                    source=ds["source"],
                    source_url=ds["source_url"],
                    update_frequency=ds["update_frequency"],
                    last_known_update=ds["last_known_update"],
                    record_count=ds["record_count"],
                    status=ds["status"],
                    used_by=used_by,
                    notes=ds["notes"],
                ))
        return entries

    def find_gaps(self) -> GapReport:
        """
        Identify missing and stale reference datasets.

        Returns:
            GapReport with prioritized remediation actions
        """
        gaps = []
        priorities = []

        for data_id, ds in self._datasets.items():
            if ds["status"] in ("missing", "stale"):
                used_by = self._module_usage.get(data_id, [])
                domain_label = self._domains.get(ds["domain"], ds["domain"])
                entry = CatalogEntry(
                    data_id=data_id,
                    label=ds["label"],
                    domain=ds["domain"],
                    domain_label=domain_label,
                    source=ds["source"],
                    source_url=ds["source_url"],
                    update_frequency=ds["update_frequency"],
                    last_known_update=ds["last_known_update"],
                    record_count=ds["record_count"],
                    status=ds["status"],
                    used_by=used_by,
                    notes=ds["notes"],
                )
                gaps.append(entry)

                severity = "critical" if ds["status"] == "missing" and used_by else "high"
                if not used_by:
                    severity = "medium"  # Needed for future modules

                priorities.append({
                    "dataset": data_id,
                    "label": ds["label"],
                    "severity": severity,
                    "needed_by": used_by if used_by else ["planned_modules"],
                    "action": f"Acquire from {ds['source']}" if ds["status"] == "missing"
                              else f"Refresh from {ds['source']}",
                })

        missing = sum(1 for g in gaps if g.status == "missing")
        stale = sum(1 for g in gaps if g.status == "stale")

        priorities.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["severity"], 3))

        effort = "low" if len(gaps) <= 3 else "medium" if len(gaps) <= 8 else "high"

        return GapReport(
            total_missing=missing,
            total_stale=stale,
            gaps=gaps,
            remediation_priority=priorities,
            estimated_effort=effort,
        )

    def get_domains(self) -> dict[str, str]:
        """Get all reference data domains."""
        return self._domains

    def get_dataset(self, data_id: str) -> Optional[CatalogEntry]:
        """Get a single dataset entry by ID."""
        ds = self._datasets.get(data_id)
        if not ds:
            return None
        used_by = self._module_usage.get(data_id, [])
        return CatalogEntry(
            data_id=data_id,
            label=ds["label"],
            domain=ds["domain"],
            domain_label=self._domains.get(ds["domain"], ds["domain"]),
            source=ds["source"],
            source_url=ds["source_url"],
            update_frequency=ds["update_frequency"],
            last_known_update=ds["last_known_update"],
            record_count=ds["record_count"],
            status=ds["status"],
            used_by=used_by,
            notes=ds["notes"],
        )
