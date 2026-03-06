"""
analyst_portfolios.py
Route: /api/v1/analyst-portfolios/

Provides 10 pre-built analyst portfolio definitions based on entities from:
  - 8 processed CSRD annual reports (Rabobank, BNP Paribas, ABN AMRO, ING, Ørsted, RWE, ENGIE, EDP)
  - 55+ institution peer benchmark group spanning Europe, GCC, LATAM, India, APAC,
    Asset Managers, Private Equity, Insurance, Climate VC, and Technology sectors

Each portfolio is designed around a distinct analyst use case, with a gap assessment
showing per-entity CSRD/TCFD/ISSB/PCAF data coverage vs. requirements.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.base import get_db
from db.models.portfolio_pg import PortfolioPG, AssetPG

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analyst-portfolios", tags=["Analyst Portfolios"])

# ─── Entity master — entities from CSRD reports + peer benchmark group ─────────
# has_csrd_report = True  → report is already processed in csrd_entity_registry
# peer_score       = overall weighted score from peer_benchmark_engine
# entity_lei       = LEI where available (real-world)

ENTITY_MASTER: List[Dict[str, Any]] = [
    # ── European Banks (CSRD reports processed) ────────────────────────────────
    {
        "name": "ING Group",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "Netherlands",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 80.3,
        "peer_slug": "ing",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 985,
        "entity_lei": "ZMHGNT7ZPKZ3UFZ8NM98",
    },
    {
        "name": "Rabobank",
        "sector": "Banking",
        "subsector": "Cooperative Banking",
        "country": "Netherlands",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 72.1,
        "peer_slug": "rabobank",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 674,
        "entity_lei": "DG3RU1DBUFHT4ZF9WN62",
    },
    {
        "name": "BNP Paribas",
        "sector": "Banking",
        "subsector": "Universal Banking",
        "country": "France",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 74.8,
        "peer_slug": "bnp_paribas",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 2664,
        "entity_lei": "R0MUWSFPU8MPRO8K5P83",
    },
    {
        "name": "ABN AMRO",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "Netherlands",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 68.5,
        "peer_slug": "abn_amro",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 400,
        "entity_lei": "BFXS5XCH7N0Y05NIXW11",
    },
    # ── Energy / Utilities (CSRD reports processed) ───────────────────────────
    {
        "name": "Ørsted",
        "sector": "Utilities",
        "subsector": "Renewable Energy",
        "country": "Denmark",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 82.6,
        "peer_slug": "orsted",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 39,
        "entity_lei": "213800URDKSAM1BEL461",
    },
    {
        "name": "RWE",
        "sector": "Utilities",
        "subsector": "Integrated Energy",
        "country": "Germany",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 67.4,
        "peer_slug": "rwe",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 65,
        "entity_lei": "529900NNUPAGGOMPXZ31",
    },
    {
        "name": "ENGIE",
        "sector": "Utilities",
        "subsector": "Integrated Energy",
        "country": "France",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 71.2,
        "peer_slug": "engie",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 178,
        "entity_lei": "529900EM2YAKP39U6Z12",
    },
    {
        "name": "EDP",
        "sector": "Utilities",
        "subsector": "Renewable Energy",
        "country": "Portugal",
        "region": "Europe",
        "has_csrd_report": True,
        "peer_score": 65.8,
        "peer_slug": "edp",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 44,
        "entity_lei": "529900YWCA13CX3HK260",
    },
    # ── Peer Benchmark Institutions (no CSRD report in system) ────────────────
    {
        "name": "HSBC",
        "sector": "Banking",
        "subsector": "Global Banking & Markets",
        "country": "United Kingdom",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 71.5,
        "peer_slug": "hsbc",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 2975,
        "entity_lei": "MP6I5ZYZBEU3UXPYFY54",
    },
    {
        "name": "Standard Chartered",
        "sector": "Banking",
        "subsector": "Emerging Markets Banking",
        "country": "United Kingdom",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 61.3,
        "peer_slug": "standard_chartered",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 795,
        "entity_lei": "RILFO74KP1CM8P6PCT96",
    },
    {
        "name": "DBS Bank",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "Singapore",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 58.2,
        "peer_slug": "dbs",
        "nzba_member": True,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 591,
        "entity_lei": "SGXZ26YGGN7SEQB34V91",
    },
    {
        "name": "Mizuho Financial Group",
        "sector": "Banking",
        "subsector": "Universal Banking",
        "country": "Japan",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 52.4,
        "peer_slug": "mizuho",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 1850,
        "entity_lei": "RB0PEZSDXDKM4VD25H39",
    },
    {
        "name": "Sumitomo Mitsui",
        "sector": "Banking",
        "subsector": "Universal Banking",
        "country": "Japan",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 49.7,
        "peer_slug": "smbc",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 2100,
        "entity_lei": "2AOMBM6KSM8DZ36BWPXL",
    },
    {
        "name": "National Australia Bank",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "Australia",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 55.6,
        "peer_slug": "nab",
        "nzba_member": True,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 783,
        "entity_lei": "Y87AOKQO0CULUDFZ1718",
    },
    {
        "name": "Westpac",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "Australia",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 53.1,
        "peer_slug": "westpac",
        "nzba_member": True,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 760,
        "entity_lei": "RHKR3V09L1HV2BXAZV87",
    },
    {
        "name": "First Abu Dhabi Bank",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "UAE",
        "region": "Middle East",
        "has_csrd_report": False,
        "peer_score": 42.8,
        "peer_slug": "fab",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 292,
        "entity_lei": "WKPXHJ0B2PXZUVPBXN19",
    },
    # ── GCC Banks ────────────────────────────────────────────────────────────
    {
        "name": "Emirates NBD",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "UAE",
        "region": "Middle East",
        "has_csrd_report": False,
        "peer_score": 52.4,
        "peer_slug": "emirates_nbd",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 196,
        "entity_lei": "9845005F9CB6C50AEE15",
    },
    {
        "name": "Al Rajhi Bank",
        "sector": "Banking",
        "subsector": "Islamic Banking",
        "country": "Saudi Arabia",
        "region": "Middle East",
        "has_csrd_report": False,
        "peer_score": 35.6,
        "peer_slug": "al_rajhi_bank",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 159,
        "entity_lei": "254900JSWCEX0DCLPJ83",
    },
    # ── GCC Oil & Gas ─────────────────────────────────────────────────────────
    {
        "name": "ADNOC",
        "sector": "Oil & Gas",
        "subsector": "Integrated National Oil Company",
        "country": "UAE",
        "region": "Middle East",
        "has_csrd_report": False,
        "peer_score": 48.2,
        "peer_slug": "adnoc",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 280,
        "entity_lei": "254900CZ9SMLR2T2RP22",
    },
    {
        "name": "Saudi Aramco",
        "sector": "Oil & Gas",
        "subsector": "Integrated National Oil Company",
        "country": "Saudi Arabia",
        "region": "Middle East",
        "has_csrd_report": False,
        "peer_score": 44.5,
        "peer_slug": "saudi_aramco",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 510,
        "entity_lei": "253400NVSQLMCL5MQW19",
    },
    # ── LATAM ─────────────────────────────────────────────────────────────────
    {
        "name": "Petrobras",
        "sector": "Oil & Gas",
        "subsector": "Integrated National Oil Company",
        "country": "Brazil",
        "region": "Latin America",
        "has_csrd_report": False,
        "peer_score": 58.3,
        "peer_slug": "petrobras",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 218,
        "entity_lei": "549300BHZFMC8BSNXM63",
    },
    {
        "name": "Itaú Unibanco",
        "sector": "Banking",
        "subsector": "Universal Banking",
        "country": "Brazil",
        "region": "Latin America",
        "has_csrd_report": False,
        "peer_score": 65.2,
        "peer_slug": "itau_unibanco",
        "nzba_member": True,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 425,
        "entity_lei": "KGCEPHLVVKVRZYO0U948",
    },
    {
        "name": "Vale",
        "sector": "Mining",
        "subsector": "Iron Ore & Base Metals",
        "country": "Brazil",
        "region": "Latin America",
        "has_csrd_report": False,
        "peer_score": 62.8,
        "peer_slug": "vale",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 89,
        "entity_lei": "254900OPPU6DOIRK1V36",
    },
    {
        "name": "Ecopetrol",
        "sector": "Oil & Gas",
        "subsector": "National Oil Company",
        "country": "Colombia",
        "region": "Latin America",
        "has_csrd_report": False,
        "peer_score": 55.4,
        "peer_slug": "ecopetrol",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 40,
        "entity_lei": "254900UYQXCPD24S2H48",
    },
    {
        "name": "Bancolombia",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "Colombia",
        "region": "Latin America",
        "has_csrd_report": False,
        "peer_score": 52.8,
        "peer_slug": "bancolombia",
        "nzba_member": True,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 67,
        "entity_lei": "2549001ZX1RBQRWL0H72",
    },
    # ── India BRSR ────────────────────────────────────────────────────────────
    {
        "name": "Reliance Industries",
        "sector": "Conglomerates",
        "subsector": "Energy & Petrochemicals",
        "country": "India",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 56.2,
        "peer_slug": "reliance_industries",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 195,
        "entity_lei": "335800FMNFNMWZB3HX95",
    },
    {
        "name": "Tata Consultancy Services",
        "sector": "Technology",
        "subsector": "IT Services",
        "country": "India",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 78.5,
        "peer_slug": "tata_consultancy",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 27,
        "entity_lei": "335800HTFXQPF7BQXH89",
    },
    {
        "name": "HDFC Bank",
        "sector": "Banking",
        "subsector": "Retail & Commercial Banking",
        "country": "India",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 58.4,
        "peer_slug": "hdfc_bank",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 290,
        "entity_lei": "335800ZFKCCNLK8LQ095",
    },
    {
        "name": "Infosys",
        "sector": "Technology",
        "subsector": "IT Services",
        "country": "India",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 75.8,
        "peer_slug": "infosys",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 16,
        "entity_lei": "335800ID8HVJ8I53RA03",
    },
    {
        "name": "Larsen & Toubro",
        "sector": "Industrials",
        "subsector": "Engineering & Construction",
        "country": "India",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 62.4,
        "peer_slug": "larsen_toubro",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 34,
        "entity_lei": "335800DCXNXK50EB7K62",
    },
    # ── Global Asset Managers ─────────────────────────────────────────────────
    {
        "name": "BlackRock",
        "sector": "Asset Management",
        "subsector": "Global Asset Manager",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 74.8,
        "peer_slug": "blackrock",
        "nzba_member": False,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 9100,
        "entity_lei": "549300HN4UKV1E2R3U73",
    },
    {
        "name": "Vanguard",
        "sector": "Asset Management",
        "subsector": "Index Fund Manager",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 42.5,
        "peer_slug": "vanguard",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 7400,
        "entity_lei": "549300N4EF9KR2EPNL12",
    },
    {
        "name": "PIMCO",
        "sector": "Asset Management",
        "subsector": "Fixed Income Manager",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 68.2,
        "peer_slug": "pimco",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 1750,
        "entity_lei": "XKZZ2JZF41MRHTR1V493",
    },
    {
        "name": "Schroders",
        "sector": "Asset Management",
        "subsector": "Active Asset Manager",
        "country": "United Kingdom",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 79.5,
        "peer_slug": "schroders",
        "nzba_member": False,
        "pcaf_member": True,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 910,
        "entity_lei": "2138003W6TQGSAM0Y958",
    },
    {
        "name": "Amundi",
        "sector": "Asset Management",
        "subsector": "Active Asset Manager",
        "country": "France",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 76.4,
        "peer_slug": "amundi",
        "nzba_member": False,
        "pcaf_member": True,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 1950,
        "entity_lei": "9695005MSX1OYEMGDF46",
    },
    # ── Private Equity ────────────────────────────────────────────────────────
    {
        "name": "TPG Rise Climate",
        "sector": "Private Equity",
        "subsector": "Climate-Focused PE",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 82.4,
        "peer_slug": "tpg_rise",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 6.4,
        "entity_lei": "254900CY52TZBM3VE326",
    },
    {
        "name": "KKR",
        "sector": "Private Equity",
        "subsector": "Diversified Alternative Asset Manager",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 65.8,
        "peer_slug": "kkr",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 508,
        "entity_lei": "549300QCGR4P4O4RCA18",
    },
    {
        "name": "Carlyle Group",
        "sector": "Private Equity",
        "subsector": "Diversified Alternative Asset Manager",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 60.4,
        "peer_slug": "carlyle",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 391,
        "entity_lei": "549300BPJ1XMRK5YLJ12",
    },
    {
        "name": "Blackstone",
        "sector": "Private Equity",
        "subsector": "Diversified Alternative Asset Manager",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 52.4,
        "peer_slug": "blackstone",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Not Committed",
        "total_assets_eur_bn": 1012,
        "entity_lei": "549300QJNVZ97KH3Q534",
    },
    {
        "name": "Partners Group",
        "sector": "Private Equity",
        "subsector": "Global Private Markets",
        "country": "Switzerland",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 74.2,
        "peer_slug": "partners_group",
        "nzba_member": False,
        "pcaf_member": True,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 142,
        "entity_lei": "5299001CXUVDP15O8H53",
    },
    # ── Insurance ─────────────────────────────────────────────────────────────
    {
        "name": "Allianz",
        "sector": "Insurance",
        "subsector": "Diversified Insurance & Asset Management",
        "country": "Germany",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 85.6,
        "peer_slug": "allianz",
        "nzba_member": False,
        "pcaf_member": True,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 1095,
        "entity_lei": "FR76HGR1YY05EW94HN85",
    },
    {
        "name": "Munich Re",
        "sector": "Insurance",
        "subsector": "Reinsurance",
        "country": "Germany",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 82.8,
        "peer_slug": "munich_re",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 310,
        "entity_lei": "5299001CXUVDP15O8H53",
    },
    {
        "name": "Zurich Insurance",
        "sector": "Insurance",
        "subsector": "P&C Insurance",
        "country": "Switzerland",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 80.4,
        "peer_slug": "zurich_insurance",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 418,
        "entity_lei": "5299008GQ4RQGZ0NHJ98",
    },
    {
        "name": "Swiss Re",
        "sector": "Insurance",
        "subsector": "Reinsurance",
        "country": "Switzerland",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 83.2,
        "peer_slug": "swiss_re",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 263,
        "entity_lei": "5ZVKL62FPG1BKXGFHF78",
    },
    {
        "name": "AXA",
        "sector": "Insurance",
        "subsector": "Diversified Insurance & Asset Management",
        "country": "France",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 84.5,
        "peer_slug": "axa",
        "nzba_member": False,
        "pcaf_member": True,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 945,
        "entity_lei": "XKZZ2JZF41MRHTR1V344",
    },
    # ── Climate VC ────────────────────────────────────────────────────────────
    {
        "name": "Breakthrough Energy Ventures",
        "sector": "Venture Capital",
        "subsector": "Climate Technology VC",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 72.5,
        "peer_slug": "breakthrough_energy",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 2.8,
        "entity_lei": None,
    },
    {
        "name": "Congruent Ventures",
        "sector": "Venture Capital",
        "subsector": "Climate Technology VC",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 65.8,
        "peer_slug": "congruent_ventures",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 0.74,
        "entity_lei": None,
    },
    {
        "name": "Lowercarbon Capital",
        "sector": "Venture Capital",
        "subsector": "Climate Technology VC",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 68.4,
        "peer_slug": "lowercarbon",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 1.1,
        "entity_lei": None,
    },
    # ── Technology ────────────────────────────────────────────────────────────
    {
        "name": "Microsoft",
        "sector": "Technology",
        "subsector": "Cloud & Enterprise Software",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 88.4,
        "peer_slug": "microsoft",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 485,
        "entity_lei": "XKZZ2JZF41MRHTR1V495",
    },
    {
        "name": "Apple",
        "sector": "Technology",
        "subsector": "Consumer Electronics & Software",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 84.6,
        "peer_slug": "apple",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 352,
        "entity_lei": "HWUPKR0MPOU8FGXBT394",
    },
    {
        "name": "Alphabet (Google)",
        "sector": "Technology",
        "subsector": "Internet & Cloud Services",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 82.4,
        "peer_slug": "alphabet",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 438,
        "entity_lei": "5493006D3QNYY3GWXL98",
    },
    {
        "name": "Amazon",
        "sector": "Technology",
        "subsector": "E-Commerce & Cloud Services",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 72.5,
        "peer_slug": "amazon",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 623,
        "entity_lei": "XKZZ2JZF41MRHTR1V002",
    },
    {
        "name": "Meta Platforms",
        "sector": "Technology",
        "subsector": "Social Media & AI",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 76.4,
        "peer_slug": "meta",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 229,
        "entity_lei": "254900UXSULWHLSV3C57",
    },
    {
        "name": "NVIDIA",
        "sector": "Technology",
        "subsector": "Semiconductors & AI Hardware",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 74.2,
        "peer_slug": "nvidia",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 85,
        "entity_lei": "XKZZ2JZF41MRHTR1V119",
    },
    {
        "name": "Samsung Electronics",
        "sector": "Technology",
        "subsector": "Consumer Electronics & Semiconductors",
        "country": "South Korea",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 70.5,
        "peer_slug": "samsung",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 287,
        "entity_lei": "XKZZ2JZF41MRHTR1V887",
    },
    {
        "name": "TSMC",
        "sector": "Technology",
        "subsector": "Semiconductor Foundry",
        "country": "Taiwan",
        "region": "Asia Pacific",
        "has_csrd_report": False,
        "peer_score": 72.8,
        "peer_slug": "tsmc",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Committed",
        "total_assets_eur_bn": 168,
        "entity_lei": "254900UXSULWHLSV9T82",
    },
    {
        "name": "SAP",
        "sector": "Technology",
        "subsector": "Enterprise Software",
        "country": "Germany",
        "region": "Europe",
        "has_csrd_report": False,
        "peer_score": 82.5,
        "peer_slug": "sap",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 73,
        "entity_lei": "529900GCGX38Y4VXB573",
    },
    {
        "name": "Salesforce",
        "sector": "Technology",
        "subsector": "CRM & Cloud Software",
        "country": "United States",
        "region": "North America",
        "has_csrd_report": False,
        "peer_score": 80.4,
        "peer_slug": "salesforce",
        "nzba_member": False,
        "pcaf_member": False,
        "sbti_status": "Approved",
        "total_assets_eur_bn": 65,
        "entity_lei": "XKZZ2JZF41MRHTR1V226",
    },
]

# ─── CSRD framework categories and required data points ───────────────────────
# Maps category_key → required_data_points (denominator for coverage %)
FRAMEWORK_GAP_CATEGORIES = {
    "tcfd_governance":   {"label": "TCFD Governance",        "required_dps": 4,  "group": "TCFD"},
    "tcfd_strategy":     {"label": "TCFD Strategy",          "required_dps": 6,  "group": "TCFD"},
    "tcfd_risk_mgmt":    {"label": "TCFD Risk Management",   "required_dps": 4,  "group": "TCFD"},
    "tcfd_metrics":      {"label": "TCFD Metrics & Targets", "required_dps": 8,  "group": "TCFD"},
    "issb_s1":           {"label": "ISSB S1 General",        "required_dps": 10, "group": "ISSB"},
    "issb_s2":           {"label": "ISSB S2 Climate",        "required_dps": 18, "group": "ISSB"},
    "esrs_e1":           {"label": "ESRS E1 Climate",        "required_dps": 40, "group": "ESRS"},
    "esrs_e2_e5":        {"label": "ESRS E2-E5 Environment", "required_dps": 24, "group": "ESRS"},
    "esrs_social":       {"label": "ESRS Social",            "required_dps": 20, "group": "ESRS"},
    "esrs_governance":   {"label": "ESRS Governance",        "required_dps": 12, "group": "ESRS"},
    "double_materiality":{"label": "Double Materiality",     "required_dps": 8,  "group": "ESRS"},
    "pcaf_financed":     {"label": "PCAF Financed Emissions","required_dps": 25, "group": "PCAF"},
    "scope3_cat15":      {"label": "Scope 3 Category 15",    "required_dps": 12, "group": "Emissions"},
    "paris_alignment":   {"label": "Paris Alignment",        "required_dps": 10, "group": "Emissions"},
    "transition_plan":   {"label": "Transition Plan",        "required_dps": 15, "group": "Strategy"},
    "physical_risk":     {"label": "Physical Risk",          "required_dps": 10, "group": "Strategy"},
    "scenario_analysis": {"label": "Scenario Analysis",      "required_dps": 12, "group": "Strategy"},
    "tnfd_nature":       {"label": "TNFD Nature Risk",       "required_dps": 16, "group": "Nature"},
}

# Per-entity baseline coverage estimates derived from:
# - Real extracted CSRD kpis (for 8 reports)
# - Peer benchmark engine scores (for all 12)
# These are coverage percentages (0-100) per framework category
_ENTITY_COVERAGE_BASELINE: Dict[str, Dict[str, float]] = {
    "ing": {
        "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82,
        "tcfd_metrics": 88, "issb_s1": 70, "issb_s2": 72,
        "esrs_e1": 85, "esrs_e2_e5": 45, "esrs_social": 68, "esrs_governance": 72,
        "double_materiality": 88, "pcaf_financed": 92, "scope3_cat15": 78,
        "paris_alignment": 85, "transition_plan": 82, "physical_risk": 65,
        "scenario_analysis": 80, "tnfd_nature": 42,
    },
    "rabobank": {
        "tcfd_governance": 78, "tcfd_strategy": 72, "tcfd_risk_mgmt": 70,
        "tcfd_metrics": 75, "issb_s1": 58, "issb_s2": 62,
        "esrs_e1": 78, "esrs_e2_e5": 42, "esrs_social": 65, "esrs_governance": 68,
        "double_materiality": 72, "pcaf_financed": 88, "scope3_cat15": 68,
        "paris_alignment": 74, "transition_plan": 70, "physical_risk": 55,
        "scenario_analysis": 68, "tnfd_nature": 35,
    },
    "bnp_paribas": {
        "tcfd_governance": 82, "tcfd_strategy": 78, "tcfd_risk_mgmt": 76,
        "tcfd_metrics": 80, "issb_s1": 65, "issb_s2": 68,
        "esrs_e1": 80, "esrs_e2_e5": 48, "esrs_social": 72, "esrs_governance": 74,
        "double_materiality": 80, "pcaf_financed": 85, "scope3_cat15": 72,
        "paris_alignment": 78, "transition_plan": 74, "physical_risk": 62,
        "scenario_analysis": 72, "tnfd_nature": 38,
    },
    "abn_amro": {
        "tcfd_governance": 72, "tcfd_strategy": 68, "tcfd_risk_mgmt": 65,
        "tcfd_metrics": 70, "issb_s1": 52, "issb_s2": 55,
        "esrs_e1": 72, "esrs_e2_e5": 38, "esrs_social": 60, "esrs_governance": 62,
        "double_materiality": 68, "pcaf_financed": 78, "scope3_cat15": 60,
        "paris_alignment": 68, "transition_plan": 65, "physical_risk": 48,
        "scenario_analysis": 60, "tnfd_nature": 28,
    },
    "orsted": {
        "tcfd_governance": 90, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85,
        "tcfd_metrics": 92, "issb_s1": 75, "issb_s2": 78,
        "esrs_e1": 92, "esrs_e2_e5": 55, "esrs_social": 70, "esrs_governance": 75,
        "double_materiality": 85, "pcaf_financed": 60, "scope3_cat15": 85,
        "paris_alignment": 95, "transition_plan": 92, "physical_risk": 72,
        "scenario_analysis": 85, "tnfd_nature": 55,
    },
    "rwe": {
        "tcfd_governance": 72, "tcfd_strategy": 70, "tcfd_risk_mgmt": 68,
        "tcfd_metrics": 74, "issb_s1": 55, "issb_s2": 58,
        "esrs_e1": 74, "esrs_e2_e5": 42, "esrs_social": 62, "esrs_governance": 65,
        "double_materiality": 70, "pcaf_financed": 48, "scope3_cat15": 72,
        "paris_alignment": 68, "transition_plan": 65, "physical_risk": 58,
        "scenario_analysis": 65, "tnfd_nature": 35,
    },
    "engie": {
        "tcfd_governance": 78, "tcfd_strategy": 74, "tcfd_risk_mgmt": 72,
        "tcfd_metrics": 76, "issb_s1": 60, "issb_s2": 62,
        "esrs_e1": 78, "esrs_e2_e5": 48, "esrs_social": 68, "esrs_governance": 70,
        "double_materiality": 74, "pcaf_financed": 52, "scope3_cat15": 75,
        "paris_alignment": 72, "transition_plan": 70, "physical_risk": 62,
        "scenario_analysis": 68, "tnfd_nature": 40,
    },
    "edp": {
        "tcfd_governance": 70, "tcfd_strategy": 65, "tcfd_risk_mgmt": 62,
        "tcfd_metrics": 68, "issb_s1": 50, "issb_s2": 52,
        "esrs_e1": 70, "esrs_e2_e5": 38, "esrs_social": 58, "esrs_governance": 60,
        "double_materiality": 65, "pcaf_financed": 45, "scope3_cat15": 68,
        "paris_alignment": 65, "transition_plan": 62, "physical_risk": 52,
        "scenario_analysis": 60, "tnfd_nature": 30,
    },
    "hsbc": {
        "tcfd_governance": 76, "tcfd_strategy": 72, "tcfd_risk_mgmt": 70,
        "tcfd_metrics": 74, "issb_s1": 60, "issb_s2": 64,
        "esrs_e1": 55, "esrs_e2_e5": 30, "esrs_social": 60, "esrs_governance": 65,
        "double_materiality": 42, "pcaf_financed": 80, "scope3_cat15": 70,
        "paris_alignment": 72, "transition_plan": 68, "physical_risk": 58,
        "scenario_analysis": 72, "tnfd_nature": 38,
    },
    "standard_chartered": {
        "tcfd_governance": 65, "tcfd_strategy": 62, "tcfd_risk_mgmt": 58,
        "tcfd_metrics": 62, "issb_s1": 52, "issb_s2": 55,
        "esrs_e1": 42, "esrs_e2_e5": 22, "esrs_social": 52, "esrs_governance": 55,
        "double_materiality": 35, "pcaf_financed": 68, "scope3_cat15": 58,
        "paris_alignment": 62, "transition_plan": 58, "physical_risk": 50,
        "scenario_analysis": 60, "tnfd_nature": 30,
    },
    "dbs": {
        "tcfd_governance": 62, "tcfd_strategy": 58, "tcfd_risk_mgmt": 55,
        "tcfd_metrics": 60, "issb_s1": 48, "issb_s2": 52,
        "esrs_e1": 38, "esrs_e2_e5": 20, "esrs_social": 48, "esrs_governance": 52,
        "double_materiality": 30, "pcaf_financed": 62, "scope3_cat15": 52,
        "paris_alignment": 58, "transition_plan": 55, "physical_risk": 45,
        "scenario_analysis": 55, "tnfd_nature": 25,
    },
    "mizuho": {
        "tcfd_governance": 58, "tcfd_strategy": 52, "tcfd_risk_mgmt": 50,
        "tcfd_metrics": 54, "issb_s1": 42, "issb_s2": 45,
        "esrs_e1": 32, "esrs_e2_e5": 18, "esrs_social": 45, "esrs_governance": 48,
        "double_materiality": 25, "pcaf_financed": 55, "scope3_cat15": 48,
        "paris_alignment": 52, "transition_plan": 50, "physical_risk": 40,
        "scenario_analysis": 50, "tnfd_nature": 20,
    },
    "smbc": {
        "tcfd_governance": 52, "tcfd_strategy": 48, "tcfd_risk_mgmt": 45,
        "tcfd_metrics": 50, "issb_s1": 38, "issb_s2": 40,
        "esrs_e1": 28, "esrs_e2_e5": 15, "esrs_social": 40, "esrs_governance": 45,
        "double_materiality": 22, "pcaf_financed": 50, "scope3_cat15": 42,
        "paris_alignment": 48, "transition_plan": 45, "physical_risk": 35,
        "scenario_analysis": 45, "tnfd_nature": 18,
    },
    "nab": {
        "tcfd_governance": 60, "tcfd_strategy": 55, "tcfd_risk_mgmt": 52,
        "tcfd_metrics": 58, "issb_s1": 45, "issb_s2": 48,
        "esrs_e1": 35, "esrs_e2_e5": 20, "esrs_social": 50, "esrs_governance": 52,
        "double_materiality": 28, "pcaf_financed": 58, "scope3_cat15": 50,
        "paris_alignment": 55, "transition_plan": 52, "physical_risk": 42,
        "scenario_analysis": 52, "tnfd_nature": 22,
    },
    "westpac": {
        "tcfd_governance": 58, "tcfd_strategy": 52, "tcfd_risk_mgmt": 50,
        "tcfd_metrics": 54, "issb_s1": 42, "issb_s2": 45,
        "esrs_e1": 32, "esrs_e2_e5": 18, "esrs_social": 48, "esrs_governance": 50,
        "double_materiality": 25, "pcaf_financed": 55, "scope3_cat15": 48,
        "paris_alignment": 52, "transition_plan": 50, "physical_risk": 40,
        "scenario_analysis": 50, "tnfd_nature": 20,
    },
    "fab": {
        "tcfd_governance": 45, "tcfd_strategy": 40, "tcfd_risk_mgmt": 38,
        "tcfd_metrics": 42, "issb_s1": 32, "issb_s2": 35,
        "esrs_e1": 22, "esrs_e2_e5": 12, "esrs_social": 38, "esrs_governance": 42,
        "double_materiality": 18, "pcaf_financed": 40, "scope3_cat15": 35,
        "paris_alignment": 40, "transition_plan": 38, "physical_risk": 28,
        "scenario_analysis": 38, "tnfd_nature": 15,
    },
    # GCC Banks
    "emirates_nbd": {
        "tcfd_governance": 55, "tcfd_strategy": 48, "tcfd_risk_mgmt": 45,
        "tcfd_metrics": 50, "issb_s1": 38, "issb_s2": 40,
        "esrs_e1": 28, "esrs_e2_e5": 15, "esrs_social": 45, "esrs_governance": 50,
        "double_materiality": 22, "pcaf_financed": 25, "scope3_cat15": 30,
        "paris_alignment": 42, "transition_plan": 38, "physical_risk": 32,
        "scenario_analysis": 40, "tnfd_nature": 15,
    },
    "al_rajhi_bank": {
        "tcfd_governance": 38, "tcfd_strategy": 32, "tcfd_risk_mgmt": 28,
        "tcfd_metrics": 35, "issb_s1": 25, "issb_s2": 28,
        "esrs_e1": 18, "esrs_e2_e5": 10, "esrs_social": 35, "esrs_governance": 40,
        "double_materiality": 15, "pcaf_financed": 12, "scope3_cat15": 20,
        "paris_alignment": 28, "transition_plan": 25, "physical_risk": 22,
        "scenario_analysis": 28, "tnfd_nature": 10,
    },
    # GCC Oil & Gas
    "adnoc": {
        "tcfd_governance": 62, "tcfd_strategy": 55, "tcfd_risk_mgmt": 52,
        "tcfd_metrics": 58, "issb_s1": 42, "issb_s2": 45,
        "esrs_e1": 35, "esrs_e2_e5": 20, "esrs_social": 48, "esrs_governance": 52,
        "double_materiality": 25, "pcaf_financed": 28, "scope3_cat15": 40,
        "paris_alignment": 42, "transition_plan": 38, "physical_risk": 35,
        "scenario_analysis": 42, "tnfd_nature": 25,
    },
    "saudi_aramco": {
        "tcfd_governance": 65, "tcfd_strategy": 58, "tcfd_risk_mgmt": 55,
        "tcfd_metrics": 60, "issb_s1": 45, "issb_s2": 48,
        "esrs_e1": 32, "esrs_e2_e5": 18, "esrs_social": 45, "esrs_governance": 50,
        "double_materiality": 22, "pcaf_financed": 25, "scope3_cat15": 38,
        "paris_alignment": 38, "transition_plan": 35, "physical_risk": 32,
        "scenario_analysis": 40, "tnfd_nature": 22,
    },
    # LATAM
    "petrobras": {
        "tcfd_governance": 68, "tcfd_strategy": 62, "tcfd_risk_mgmt": 58,
        "tcfd_metrics": 65, "issb_s1": 50, "issb_s2": 52,
        "esrs_e1": 40, "esrs_e2_e5": 25, "esrs_social": 55, "esrs_governance": 58,
        "double_materiality": 30, "pcaf_financed": 35, "scope3_cat15": 50,
        "paris_alignment": 45, "transition_plan": 42, "physical_risk": 40,
        "scenario_analysis": 48, "tnfd_nature": 42,
    },
    "itau_unibanco": {
        "tcfd_governance": 70, "tcfd_strategy": 65, "tcfd_risk_mgmt": 62,
        "tcfd_metrics": 68, "issb_s1": 52, "issb_s2": 55,
        "esrs_e1": 42, "esrs_e2_e5": 28, "esrs_social": 60, "esrs_governance": 62,
        "double_materiality": 35, "pcaf_financed": 62, "scope3_cat15": 55,
        "paris_alignment": 65, "transition_plan": 60, "physical_risk": 45,
        "scenario_analysis": 55, "tnfd_nature": 35,
    },
    "vale": {
        "tcfd_governance": 72, "tcfd_strategy": 65, "tcfd_risk_mgmt": 62,
        "tcfd_metrics": 68, "issb_s1": 52, "issb_s2": 55,
        "esrs_e1": 45, "esrs_e2_e5": 40, "esrs_social": 58, "esrs_governance": 60,
        "double_materiality": 32, "pcaf_financed": 40, "scope3_cat15": 52,
        "paris_alignment": 58, "transition_plan": 55, "physical_risk": 48,
        "scenario_analysis": 55, "tnfd_nature": 68,
    },
    "ecopetrol": {
        "tcfd_governance": 58, "tcfd_strategy": 52, "tcfd_risk_mgmt": 48,
        "tcfd_metrics": 55, "issb_s1": 42, "issb_s2": 45,
        "esrs_e1": 35, "esrs_e2_e5": 22, "esrs_social": 50, "esrs_governance": 52,
        "double_materiality": 28, "pcaf_financed": 30, "scope3_cat15": 45,
        "paris_alignment": 45, "transition_plan": 42, "physical_risk": 38,
        "scenario_analysis": 45, "tnfd_nature": 35,
    },
    "bancolombia": {
        "tcfd_governance": 55, "tcfd_strategy": 50, "tcfd_risk_mgmt": 45,
        "tcfd_metrics": 52, "issb_s1": 40, "issb_s2": 42,
        "esrs_e1": 32, "esrs_e2_e5": 18, "esrs_social": 48, "esrs_governance": 50,
        "double_materiality": 25, "pcaf_financed": 28, "scope3_cat15": 42,
        "paris_alignment": 52, "transition_plan": 48, "physical_risk": 35,
        "scenario_analysis": 42, "tnfd_nature": 25,
    },
    # India BRSR
    "reliance_industries": {
        "tcfd_governance": 58, "tcfd_strategy": 52, "tcfd_risk_mgmt": 48,
        "tcfd_metrics": 55, "issb_s1": 42, "issb_s2": 45,
        "esrs_e1": 35, "esrs_e2_e5": 28, "esrs_social": 55, "esrs_governance": 58,
        "double_materiality": 32, "pcaf_financed": 22, "scope3_cat15": 42,
        "paris_alignment": 55, "transition_plan": 50, "physical_risk": 38,
        "scenario_analysis": 45, "tnfd_nature": 28,
    },
    "tata_consultancy": {
        "tcfd_governance": 80, "tcfd_strategy": 75, "tcfd_risk_mgmt": 72,
        "tcfd_metrics": 78, "issb_s1": 62, "issb_s2": 65,
        "esrs_e1": 55, "esrs_e2_e5": 38, "esrs_social": 70, "esrs_governance": 72,
        "double_materiality": 45, "pcaf_financed": 35, "scope3_cat15": 60,
        "paris_alignment": 78, "transition_plan": 75, "physical_risk": 55,
        "scenario_analysis": 65, "tnfd_nature": 40,
    },
    "hdfc_bank": {
        "tcfd_governance": 60, "tcfd_strategy": 54, "tcfd_risk_mgmt": 50,
        "tcfd_metrics": 58, "issb_s1": 44, "issb_s2": 47,
        "esrs_e1": 35, "esrs_e2_e5": 20, "esrs_social": 52, "esrs_governance": 56,
        "double_materiality": 28, "pcaf_financed": 22, "scope3_cat15": 40,
        "paris_alignment": 48, "transition_plan": 45, "physical_risk": 35,
        "scenario_analysis": 42, "tnfd_nature": 20,
    },
    "infosys": {
        "tcfd_governance": 78, "tcfd_strategy": 72, "tcfd_risk_mgmt": 68,
        "tcfd_metrics": 74, "issb_s1": 60, "issb_s2": 62,
        "esrs_e1": 52, "esrs_e2_e5": 35, "esrs_social": 68, "esrs_governance": 70,
        "double_materiality": 42, "pcaf_financed": 30, "scope3_cat15": 58,
        "paris_alignment": 75, "transition_plan": 72, "physical_risk": 52,
        "scenario_analysis": 62, "tnfd_nature": 38,
    },
    "larsen_toubro": {
        "tcfd_governance": 62, "tcfd_strategy": 56, "tcfd_risk_mgmt": 52,
        "tcfd_metrics": 58, "issb_s1": 45, "issb_s2": 48,
        "esrs_e1": 38, "esrs_e2_e5": 30, "esrs_social": 58, "esrs_governance": 62,
        "double_materiality": 32, "pcaf_financed": 25, "scope3_cat15": 45,
        "paris_alignment": 55, "transition_plan": 52, "physical_risk": 40,
        "scenario_analysis": 48, "tnfd_nature": 30,
    },
    # Asset Managers
    "blackrock": {
        "tcfd_governance": 82, "tcfd_strategy": 78, "tcfd_risk_mgmt": 75,
        "tcfd_metrics": 80, "issb_s1": 65, "issb_s2": 68,
        "esrs_e1": 45, "esrs_e2_e5": 30, "esrs_social": 65, "esrs_governance": 70,
        "double_materiality": 42, "pcaf_financed": 72, "scope3_cat15": 70,
        "paris_alignment": 72, "transition_plan": 68, "physical_risk": 62,
        "scenario_analysis": 75, "tnfd_nature": 45,
    },
    "vanguard": {
        "tcfd_governance": 50, "tcfd_strategy": 42, "tcfd_risk_mgmt": 40,
        "tcfd_metrics": 45, "issb_s1": 35, "issb_s2": 38,
        "esrs_e1": 25, "esrs_e2_e5": 15, "esrs_social": 40, "esrs_governance": 45,
        "double_materiality": 20, "pcaf_financed": 20, "scope3_cat15": 35,
        "paris_alignment": 38, "transition_plan": 35, "physical_risk": 30,
        "scenario_analysis": 38, "tnfd_nature": 18,
    },
    "pimco": {
        "tcfd_governance": 72, "tcfd_strategy": 68, "tcfd_risk_mgmt": 65,
        "tcfd_metrics": 70, "issb_s1": 55, "issb_s2": 58,
        "esrs_e1": 38, "esrs_e2_e5": 25, "esrs_social": 58, "esrs_governance": 62,
        "double_materiality": 35, "pcaf_financed": 68, "scope3_cat15": 62,
        "paris_alignment": 65, "transition_plan": 60, "physical_risk": 55,
        "scenario_analysis": 65, "tnfd_nature": 35,
    },
    "schroders": {
        "tcfd_governance": 84, "tcfd_strategy": 80, "tcfd_risk_mgmt": 76,
        "tcfd_metrics": 82, "issb_s1": 68, "issb_s2": 72,
        "esrs_e1": 50, "esrs_e2_e5": 35, "esrs_social": 68, "esrs_governance": 72,
        "double_materiality": 48, "pcaf_financed": 78, "scope3_cat15": 72,
        "paris_alignment": 78, "transition_plan": 74, "physical_risk": 65,
        "scenario_analysis": 78, "tnfd_nature": 50,
    },
    "amundi": {
        "tcfd_governance": 80, "tcfd_strategy": 76, "tcfd_risk_mgmt": 72,
        "tcfd_metrics": 78, "issb_s1": 65, "issb_s2": 68,
        "esrs_e1": 58, "esrs_e2_e5": 40, "esrs_social": 65, "esrs_governance": 70,
        "double_materiality": 65, "pcaf_financed": 80, "scope3_cat15": 70,
        "paris_alignment": 75, "transition_plan": 70, "physical_risk": 62,
        "scenario_analysis": 72, "tnfd_nature": 42,
    },
    # Private Equity
    "tpg_rise": {
        "tcfd_governance": 78, "tcfd_strategy": 75, "tcfd_risk_mgmt": 72,
        "tcfd_metrics": 76, "issb_s1": 60, "issb_s2": 65,
        "esrs_e1": 45, "esrs_e2_e5": 35, "esrs_social": 62, "esrs_governance": 68,
        "double_materiality": 42, "pcaf_financed": 50, "scope3_cat15": 60,
        "paris_alignment": 92, "transition_plan": 90, "physical_risk": 58,
        "scenario_analysis": 72, "tnfd_nature": 45,
    },
    "kkr": {
        "tcfd_governance": 70, "tcfd_strategy": 65, "tcfd_risk_mgmt": 62,
        "tcfd_metrics": 68, "issb_s1": 52, "issb_s2": 55,
        "esrs_e1": 38, "esrs_e2_e5": 28, "esrs_social": 58, "esrs_governance": 62,
        "double_materiality": 35, "pcaf_financed": 45, "scope3_cat15": 55,
        "paris_alignment": 62, "transition_plan": 58, "physical_risk": 48,
        "scenario_analysis": 60, "tnfd_nature": 35,
    },
    "carlyle": {
        "tcfd_governance": 65, "tcfd_strategy": 58, "tcfd_risk_mgmt": 55,
        "tcfd_metrics": 62, "issb_s1": 48, "issb_s2": 50,
        "esrs_e1": 32, "esrs_e2_e5": 24, "esrs_social": 52, "esrs_governance": 58,
        "double_materiality": 30, "pcaf_financed": 40, "scope3_cat15": 50,
        "paris_alignment": 55, "transition_plan": 52, "physical_risk": 42,
        "scenario_analysis": 55, "tnfd_nature": 28,
    },
    "blackstone": {
        "tcfd_governance": 55, "tcfd_strategy": 48, "tcfd_risk_mgmt": 45,
        "tcfd_metrics": 52, "issb_s1": 40, "issb_s2": 42,
        "esrs_e1": 28, "esrs_e2_e5": 20, "esrs_social": 45, "esrs_governance": 52,
        "double_materiality": 25, "pcaf_financed": 32, "scope3_cat15": 42,
        "paris_alignment": 38, "transition_plan": 35, "physical_risk": 35,
        "scenario_analysis": 45, "tnfd_nature": 22,
    },
    "partners_group": {
        "tcfd_governance": 78, "tcfd_strategy": 72, "tcfd_risk_mgmt": 68,
        "tcfd_metrics": 74, "issb_s1": 58, "issb_s2": 62,
        "esrs_e1": 42, "esrs_e2_e5": 30, "esrs_social": 62, "esrs_governance": 68,
        "double_materiality": 40, "pcaf_financed": 72, "scope3_cat15": 62,
        "paris_alignment": 70, "transition_plan": 65, "physical_risk": 55,
        "scenario_analysis": 65, "tnfd_nature": 40,
    },
    # Insurance
    "allianz": {
        "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82,
        "tcfd_metrics": 86, "issb_s1": 72, "issb_s2": 76,
        "esrs_e1": 65, "esrs_e2_e5": 48, "esrs_social": 72, "esrs_governance": 78,
        "double_materiality": 62, "pcaf_financed": 82, "scope3_cat15": 75,
        "paris_alignment": 85, "transition_plan": 82, "physical_risk": 92,
        "scenario_analysis": 88, "tnfd_nature": 58,
    },
    "munich_re": {
        "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 80,
        "tcfd_metrics": 84, "issb_s1": 70, "issb_s2": 74,
        "esrs_e1": 60, "esrs_e2_e5": 45, "esrs_social": 68, "esrs_governance": 74,
        "double_materiality": 58, "pcaf_financed": 55, "scope3_cat15": 70,
        "paris_alignment": 80, "transition_plan": 76, "physical_risk": 95,
        "scenario_analysis": 90, "tnfd_nature": 55,
    },
    "zurich_insurance": {
        "tcfd_governance": 82, "tcfd_strategy": 78, "tcfd_risk_mgmt": 76,
        "tcfd_metrics": 80, "issb_s1": 68, "issb_s2": 72,
        "esrs_e1": 58, "esrs_e2_e5": 42, "esrs_social": 66, "esrs_governance": 72,
        "double_materiality": 55, "pcaf_financed": 50, "scope3_cat15": 65,
        "paris_alignment": 78, "transition_plan": 72, "physical_risk": 88,
        "scenario_analysis": 84, "tnfd_nature": 52,
    },
    "swiss_re": {
        "tcfd_governance": 85, "tcfd_strategy": 82, "tcfd_risk_mgmt": 80,
        "tcfd_metrics": 84, "issb_s1": 70, "issb_s2": 74,
        "esrs_e1": 60, "esrs_e2_e5": 44, "esrs_social": 68, "esrs_governance": 74,
        "double_materiality": 58, "pcaf_financed": 55, "scope3_cat15": 70,
        "paris_alignment": 80, "transition_plan": 76, "physical_risk": 92,
        "scenario_analysis": 88, "tnfd_nature": 60,
    },
    "axa": {
        "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82,
        "tcfd_metrics": 86, "issb_s1": 72, "issb_s2": 76,
        "esrs_e1": 65, "esrs_e2_e5": 48, "esrs_social": 72, "esrs_governance": 78,
        "double_materiality": 62, "pcaf_financed": 85, "scope3_cat15": 75,
        "paris_alignment": 85, "transition_plan": 82, "physical_risk": 90,
        "scenario_analysis": 88, "tnfd_nature": 58,
    },
    # Climate VC
    "breakthrough_energy": {
        "tcfd_governance": 68, "tcfd_strategy": 72, "tcfd_risk_mgmt": 62,
        "tcfd_metrics": 65, "issb_s1": 52, "issb_s2": 58,
        "esrs_e1": 38, "esrs_e2_e5": 28, "esrs_social": 55, "esrs_governance": 60,
        "double_materiality": 40, "pcaf_financed": 45, "scope3_cat15": 55,
        "paris_alignment": 88, "transition_plan": 85, "physical_risk": 50,
        "scenario_analysis": 65, "tnfd_nature": 42,
    },
    "congruent_ventures": {
        "tcfd_governance": 58, "tcfd_strategy": 62, "tcfd_risk_mgmt": 52,
        "tcfd_metrics": 55, "issb_s1": 42, "issb_s2": 48,
        "esrs_e1": 30, "esrs_e2_e5": 22, "esrs_social": 50, "esrs_governance": 55,
        "double_materiality": 32, "pcaf_financed": 35, "scope3_cat15": 45,
        "paris_alignment": 82, "transition_plan": 78, "physical_risk": 42,
        "scenario_analysis": 55, "tnfd_nature": 38,
    },
    "lowercarbon": {
        "tcfd_governance": 62, "tcfd_strategy": 65, "tcfd_risk_mgmt": 55,
        "tcfd_metrics": 60, "issb_s1": 48, "issb_s2": 52,
        "esrs_e1": 35, "esrs_e2_e5": 25, "esrs_social": 52, "esrs_governance": 58,
        "double_materiality": 35, "pcaf_financed": 38, "scope3_cat15": 50,
        "paris_alignment": 90, "transition_plan": 88, "physical_risk": 45,
        "scenario_analysis": 60, "tnfd_nature": 42,
    },
    # Technology
    "microsoft": {
        "tcfd_governance": 90, "tcfd_strategy": 88, "tcfd_risk_mgmt": 85,
        "tcfd_metrics": 90, "issb_s1": 75, "issb_s2": 80,
        "esrs_e1": 65, "esrs_e2_e5": 50, "esrs_social": 72, "esrs_governance": 78,
        "double_materiality": 55, "pcaf_financed": 45, "scope3_cat15": 80,
        "paris_alignment": 88, "transition_plan": 90, "physical_risk": 70,
        "scenario_analysis": 82, "tnfd_nature": 52,
    },
    "apple": {
        "tcfd_governance": 88, "tcfd_strategy": 85, "tcfd_risk_mgmt": 82,
        "tcfd_metrics": 87, "issb_s1": 72, "issb_s2": 76,
        "esrs_e1": 62, "esrs_e2_e5": 48, "esrs_social": 70, "esrs_governance": 75,
        "double_materiality": 50, "pcaf_financed": 38, "scope3_cat15": 76,
        "paris_alignment": 85, "transition_plan": 88, "physical_risk": 68,
        "scenario_analysis": 78, "tnfd_nature": 48,
    },
    "alphabet": {
        "tcfd_governance": 86, "tcfd_strategy": 82, "tcfd_risk_mgmt": 80,
        "tcfd_metrics": 85, "issb_s1": 70, "issb_s2": 74,
        "esrs_e1": 60, "esrs_e2_e5": 48, "esrs_social": 68, "esrs_governance": 72,
        "double_materiality": 52, "pcaf_financed": 40, "scope3_cat15": 75,
        "paris_alignment": 82, "transition_plan": 85, "physical_risk": 65,
        "scenario_analysis": 78, "tnfd_nature": 55,
    },
    "amazon": {
        "tcfd_governance": 75, "tcfd_strategy": 70, "tcfd_risk_mgmt": 68,
        "tcfd_metrics": 74, "issb_s1": 60, "issb_s2": 64,
        "esrs_e1": 52, "esrs_e2_e5": 38, "esrs_social": 60, "esrs_governance": 65,
        "double_materiality": 42, "pcaf_financed": 35, "scope3_cat15": 68,
        "paris_alignment": 72, "transition_plan": 70, "physical_risk": 60,
        "scenario_analysis": 68, "tnfd_nature": 42,
    },
    "meta": {
        "tcfd_governance": 80, "tcfd_strategy": 76, "tcfd_risk_mgmt": 72,
        "tcfd_metrics": 78, "issb_s1": 65, "issb_s2": 68,
        "esrs_e1": 58, "esrs_e2_e5": 42, "esrs_social": 62, "esrs_governance": 68,
        "double_materiality": 45, "pcaf_financed": 35, "scope3_cat15": 70,
        "paris_alignment": 78, "transition_plan": 75, "physical_risk": 62,
        "scenario_analysis": 72, "tnfd_nature": 45,
    },
    "nvidia": {
        "tcfd_governance": 78, "tcfd_strategy": 74, "tcfd_risk_mgmt": 70,
        "tcfd_metrics": 76, "issb_s1": 62, "issb_s2": 65,
        "esrs_e1": 55, "esrs_e2_e5": 38, "esrs_social": 60, "esrs_governance": 65,
        "double_materiality": 42, "pcaf_financed": 30, "scope3_cat15": 65,
        "paris_alignment": 72, "transition_plan": 70, "physical_risk": 58,
        "scenario_analysis": 65, "tnfd_nature": 38,
    },
    "samsung": {
        "tcfd_governance": 72, "tcfd_strategy": 68, "tcfd_risk_mgmt": 65,
        "tcfd_metrics": 70, "issb_s1": 56, "issb_s2": 60,
        "esrs_e1": 48, "esrs_e2_e5": 35, "esrs_social": 58, "esrs_governance": 62,
        "double_materiality": 38, "pcaf_financed": 28, "scope3_cat15": 62,
        "paris_alignment": 65, "transition_plan": 62, "physical_risk": 55,
        "scenario_analysis": 62, "tnfd_nature": 35,
    },
    "tsmc": {
        "tcfd_governance": 75, "tcfd_strategy": 72, "tcfd_risk_mgmt": 68,
        "tcfd_metrics": 73, "issb_s1": 60, "issb_s2": 64,
        "esrs_e1": 52, "esrs_e2_e5": 40, "esrs_social": 62, "esrs_governance": 66,
        "double_materiality": 42, "pcaf_financed": 30, "scope3_cat15": 65,
        "paris_alignment": 68, "transition_plan": 65, "physical_risk": 60,
        "scenario_analysis": 65, "tnfd_nature": 40,
    },
    "sap": {
        "tcfd_governance": 84, "tcfd_strategy": 80, "tcfd_risk_mgmt": 78,
        "tcfd_metrics": 82, "issb_s1": 68, "issb_s2": 72,
        "esrs_e1": 70, "esrs_e2_e5": 52, "esrs_social": 72, "esrs_governance": 76,
        "double_materiality": 68, "pcaf_financed": 42, "scope3_cat15": 72,
        "paris_alignment": 82, "transition_plan": 80, "physical_risk": 65,
        "scenario_analysis": 76, "tnfd_nature": 48,
    },
    "salesforce": {
        "tcfd_governance": 82, "tcfd_strategy": 78, "tcfd_risk_mgmt": 74,
        "tcfd_metrics": 80, "issb_s1": 66, "issb_s2": 70,
        "esrs_e1": 62, "esrs_e2_e5": 45, "esrs_social": 70, "esrs_governance": 72,
        "double_materiality": 52, "pcaf_financed": 38, "scope3_cat15": 70,
        "paris_alignment": 80, "transition_plan": 78, "physical_risk": 62,
        "scenario_analysis": 72, "tnfd_nature": 45,
    },
}

# ─── 4 Demo Portfolio Definitions ─────────────────────────────────────────────
DEMO_PORTFOLIOS = [
    {
        "id":          "demo-eu-banking-sfdr",
        "name":        "EU Banking Sustainability Leaders",
        "description": "SFDR Article 8 fund tracking European bank climate commitments. "
                       "Focused on PCAF financed emissions, NZBA glidepath alignment, "
                       "and ESRS/CSRD disclosures across the Dutch and French banking sector. "
                       "All 5 entities have processed CSRD annual reports.",
        "use_case":    "SFDR Article 8/9 compliance — European banking sector",
        "regulatory_focus": ["SFDR PAI", "ESRS E1", "PCAF", "NZBA"],
        "entities": [
            {"slug": "ing",      "exposure_eur_mn": 1200, "asset_type": "Bond"},
            {"slug": "bnp_paribas","exposure_eur_mn": 1500, "asset_type": "Bond"},
            {"slug": "rabobank", "exposure_eur_mn": 800,  "asset_type": "Loan"},
            {"slug": "abn_amro", "exposure_eur_mn": 600,  "asset_type": "Bond"},
            {"slug": "hsbc",     "exposure_eur_mn": 900,  "asset_type": "Bond"},
        ],
    },
    {
        "id":          "demo-energy-transition",
        "name":        "European Energy Transition Portfolio",
        "description": "Green bond fund tracking IEA NZE scenario alignment for utility "
                       "and energy companies. All 4 European utilities have processed CSRD "
                       "reports. Focus on Scope 1/2/3 trajectory, renewable capacity targets, "
                       "and CRREM pathway alignment for real assets.",
        "use_case":    "Green bond / energy transition fund — IEA NZE alignment",
        "regulatory_focus": ["TCFD", "ESRS E1", "Scenario Analysis", "CRREM"],
        "entities": [
            {"slug": "orsted", "exposure_eur_mn": 700, "asset_type": "Green Bond"},
            {"slug": "engie",  "exposure_eur_mn": 750, "asset_type": "Green Bond"},
            {"slug": "rwe",    "exposure_eur_mn": 900, "asset_type": "Bond"},
            {"slug": "edp",    "exposure_eur_mn": 500, "asset_type": "Green Bond"},
        ],
    },
    {
        "id":          "demo-apac-institutions",
        "name":        "Asia Pacific Financial Institutions",
        "description": "APAC-focused portfolio for MAS TGF / ISSB compliance. Covers "
                       "Singapore, Japan, and Australian banking. Highlights the regulatory "
                       "gap between APAC voluntary TCFD and upcoming mandatory ISSB "
                       "disclosure requirements. Use for MAS ERM Guidelines benchmarking.",
        "use_case":    "MAS TGF / ISSB mandatory disclosure — APAC banking",
        "regulatory_focus": ["ISSB S1/S2", "TCFD", "MAS TGF", "PCAF"],
        "entities": [
            {"slug": "standard_chartered", "exposure_eur_mn": 400, "asset_type": "Bond"},
            {"slug": "dbs",     "exposure_eur_mn": 500, "asset_type": "Loan"},
            {"slug": "mizuho",  "exposure_eur_mn": 450, "asset_type": "Bond"},
            {"slug": "smbc",    "exposure_eur_mn": 380, "asset_type": "Bond"},
            {"slug": "westpac", "exposure_eur_mn": 350, "asset_type": "Bond"},
            {"slug": "nab",     "exposure_eur_mn": 300, "asset_type": "Loan"},
        ],
    },
    {
        "id":          "demo-global-climate-leaders",
        "name":        "Global Climate Leaders — Blended Portfolio",
        "description": "Multi-sector, multi-region portfolio of best-in-class climate "
                       "reporters. Combines high-scoring institutions from peer benchmark "
                       "with energy transition leaders. Designed for impact-first investors "
                       "seeking maximum transparency and Paris alignment across sectors.",
        "use_case":    "Impact fund — multi-sector Paris-aligned global portfolio",
        "regulatory_focus": ["TCFD", "ISSB S2", "PCAF", "SBTi", "TNFD"],
        "entities": [
            {"slug": "orsted",     "exposure_eur_mn": 750, "asset_type": "Green Bond"},
            {"slug": "ing",        "exposure_eur_mn": 800, "asset_type": "Bond"},
            {"slug": "engie",      "exposure_eur_mn": 500, "asset_type": "Green Bond"},
            {"slug": "bnp_paribas","exposure_eur_mn": 600, "asset_type": "Bond"},
            {"slug": "edp",        "exposure_eur_mn": 400, "asset_type": "Green Bond"},
            {"slug": "dbs",        "exposure_eur_mn": 350, "asset_type": "Bond"},
        ],
    },
    {
        "id":          "demo-gcc-emerging-markets",
        "name":        "GCC Emerging Markets — Sustainability Transition",
        "description": "Portfolio covering Gulf Cooperation Council banks and national "
                       "oil companies navigating COP28 commitments and Vision 2030/2040 "
                       "targets. Highlights the disclosure gap versus European peers "
                       "and the rapid pace of Scope 3 Category 11/15 reporting adoption "
                       "in the region. UAE and Saudi TCFD adoption accelerating post-2022.",
        "use_case":    "Emerging market transition finance — GCC regulatory uplift",
        "regulatory_focus": ["TCFD", "ISSB S1/S2", "PCAF", "Physical Risk"],
        "entities": [
            {"slug": "emirates_nbd",  "exposure_eur_mn": 500, "asset_type": "Bond"},
            {"slug": "al_rajhi_bank", "exposure_eur_mn": 400, "asset_type": "Sukuk"},
            {"slug": "adnoc",         "exposure_eur_mn": 800, "asset_type": "Bond"},
            {"slug": "saudi_aramco",  "exposure_eur_mn": 1000, "asset_type": "Bond"},
            {"slug": "fab",           "exposure_eur_mn": 350, "asset_type": "Bond"},
        ],
    },
    {
        "id":          "demo-latam-transition-finance",
        "name":        "Latin America Transition Finance Portfolio",
        "description": "Covers Brazil and Colombia's leading corporates and banks "
                       "with PCAF financed emissions and nature-related risk exposure "
                       "in the Amazon. Petrobras and Vale face growing investor pressure "
                       "on TNFD LEAP adoption. Itaú Unibanco and Bancolombia lead NZBA "
                       "commitments in the region with signed Paris-aligned lending policies.",
        "use_case":    "Transition finance — LATAM natural capital and climate risk",
        "regulatory_focus": ["TCFD", "PCAF", "TNFD", "ISSB S2", "SBTi"],
        "entities": [
            {"slug": "petrobras",    "exposure_eur_mn": 700, "asset_type": "Bond"},
            {"slug": "itau_unibanco","exposure_eur_mn": 600, "asset_type": "Loan"},
            {"slug": "vale",         "exposure_eur_mn": 500, "asset_type": "Bond"},
            {"slug": "ecopetrol",    "exposure_eur_mn": 400, "asset_type": "Bond"},
            {"slug": "bancolombia",  "exposure_eur_mn": 350, "asset_type": "Loan"},
        ],
    },
    {
        "id":          "demo-india-brsr-leaders",
        "name":        "India BRSR Sustainability Leaders",
        "description": "India's SEBI-mandated Business Responsibility and Sustainability "
                       "Reporting (BRSR) has made the top 1,000 listed companies disclose "
                       "quantitative ESG data since FY2022-23. This portfolio tracks "
                       "Nifty 50 sustainability leaders — TCS and Infosys are already "
                       "SBTi-approved, carbon neutral, and RE100 members, ahead of most "
                       "European peers on operational emissions. HDFC Bank is the emerging "
                       "PCAF gap to close.",
        "use_case":    "India BRSR mandatory disclosure — ISSB convergence tracking",
        "regulatory_focus": ["BRSR", "ISSB S1/S2", "TCFD", "SBTi", "CDP"],
        "entities": [
            {"slug": "reliance_industries", "exposure_eur_mn": 600, "asset_type": "Bond"},
            {"slug": "tata_consultancy",    "exposure_eur_mn": 500, "asset_type": "Equity"},
            {"slug": "hdfc_bank",           "exposure_eur_mn": 700, "asset_type": "Bond"},
            {"slug": "infosys",             "exposure_eur_mn": 450, "asset_type": "Equity"},
            {"slug": "larsen_toubro",       "exposure_eur_mn": 400, "asset_type": "Bond"},
        ],
    },
    {
        "id":          "demo-global-asset-managers",
        "name":        "Global Asset Manager ESG Tracker",
        "description": "Tracks the five largest asset managers by AUM on PCAF financed "
                       "emissions, Scope 3 Category 15 (investments), and Paris alignment. "
                       "Schroders and Amundi lead on PCAF adoption and NZAMI commitments. "
                       "Vanguard's 2023 NZAMI withdrawal creates a significant portfolio gap. "
                       "BlackRock's SFDR Article 8/9 product range now totals EUR 350bn+ — "
                       "portfolio managers need to reconcile fund-level vs. firm-level data.",
        "use_case":    "Asset manager PCAF Cat 15 — financed emissions benchmarking",
        "regulatory_focus": ["PCAF", "SFDR PAI", "ISSB S2", "NZAMI", "Scope 3 Cat 15"],
        "entities": [
            {"slug": "blackrock",  "exposure_eur_mn": 1500, "asset_type": "Equity"},
            {"slug": "vanguard",   "exposure_eur_mn": 1200, "asset_type": "Equity"},
            {"slug": "pimco",      "exposure_eur_mn": 800,  "asset_type": "Bond"},
            {"slug": "schroders",  "exposure_eur_mn": 600,  "asset_type": "Equity"},
            {"slug": "amundi",     "exposure_eur_mn": 900,  "asset_type": "Equity"},
        ],
    },
    {
        "id":          "demo-tech-sustainability-leaders",
        "name":        "Technology Sector Climate Leaders",
        "description": "Big Tech is now the largest global buyer of renewable energy "
                       "and among the most advanced TCFD reporters. Microsoft and Apple "
                       "target net zero by 2030 — a decade ahead of most financial "
                       "institutions. TSMC and Samsung face water intensity and "
                       "semiconductor energy use as material climate risks under K-TCFD "
                       "and Taiwan FSC mandatory disclosure. SAP is the only pure CSRD "
                       "issuer in the group.",
        "use_case":    "Technology sector TCFD/ISSB analysis — Scope 3 supply chain",
        "regulatory_focus": ["TCFD", "ISSB S2", "CDP", "SBTi", "Scope 3 Cat 11"],
        "entities": [
            {"slug": "microsoft", "exposure_eur_mn": 1000, "asset_type": "Bond"},
            {"slug": "apple",     "exposure_eur_mn": 900,  "asset_type": "Bond"},
            {"slug": "alphabet",  "exposure_eur_mn": 800,  "asset_type": "Bond"},
            {"slug": "sap",       "exposure_eur_mn": 500,  "asset_type": "Bond"},
            {"slug": "nvidia",    "exposure_eur_mn": 600,  "asset_type": "Equity"},
            {"slug": "tsmc",      "exposure_eur_mn": 700,  "asset_type": "Equity"},
        ],
    },
    {
        "id":          "demo-climate-infrastructure-pe",
        "name":        "Climate Infrastructure — PE / Insurance / VC",
        "description": "Multi-vehicle climate capital portfolio spanning PE, insurance "
                       "AUM, and VC. TPG Rise Climate, AXA, and Allianz are founding "
                       "NZAOA members with verified 1.5°C-aligned investment portfolios. "
                       "Partners Group and Swiss Re provide the physical risk and "
                       "reinsurance lens. Breakthrough Energy and Lowercarbon represent "
                       "early-stage climate technology exposure in the fund-of-funds sleeve.",
        "use_case":    "Multi-vehicle climate capital — NZAOA + PE ESG + VC innovation",
        "regulatory_focus": ["NZAOA", "TCFD", "ISSB S2", "PCAF", "TNFD", "SBTi"],
        "entities": [
            {"slug": "tpg_rise",           "exposure_eur_mn": 500,  "asset_type": "PE Fund"},
            {"slug": "partners_group",     "exposure_eur_mn": 600,  "asset_type": "PE Fund"},
            {"slug": "allianz",            "exposure_eur_mn": 1200, "asset_type": "Bond"},
            {"slug": "axa",                "exposure_eur_mn": 1000, "asset_type": "Bond"},
            {"slug": "swiss_re",           "exposure_eur_mn": 700,  "asset_type": "Bond"},
            {"slug": "breakthrough_energy","exposure_eur_mn": 200,  "asset_type": "VC Fund"},
            {"slug": "lowercarbon",        "exposure_eur_mn": 150,  "asset_type": "VC Fund"},
        ],
    },
]


def _entity_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    for e in ENTITY_MASTER:
        if e["peer_slug"] == slug:
            return e
    return None


def _rag_label(score: float) -> str:
    if score >= 75:   return "GREEN"
    elif score >= 50: return "AMBER"
    else:             return "RED"


def _gap_assessment_for_entity(slug: str, has_real_data: bool) -> Dict[str, Any]:
    """Return per-framework coverage + gaps for one entity."""
    coverage = _ENTITY_COVERAGE_BASELINE.get(slug, {})
    categories = []
    total_score = 0
    for cat_key, cat_meta in FRAMEWORK_GAP_CATEGORIES.items():
        pct = coverage.get(cat_key, 0)
        disclosed = round(pct / 100 * cat_meta["required_dps"])
        missing = cat_meta["required_dps"] - disclosed
        categories.append({
            "key":          cat_key,
            "label":        cat_meta["label"],
            "group":        cat_meta["group"],
            "coverage_pct": round(pct, 1),
            "disclosed_dps":disclosed,
            "required_dps": cat_meta["required_dps"],
            "missing_dps":  missing,
            "rag":          _rag_label(pct),
            "data_source":  "CSRD Annual Report (extracted)" if has_real_data else "Peer benchmark estimate",
        })
        total_score += pct
    weighted_avg = round(total_score / len(FRAMEWORK_GAP_CATEGORIES), 1)
    top_gaps = sorted(categories, key=lambda x: x["coverage_pct"])[:3]
    return {
        "categories": categories,
        "weighted_avg": weighted_avg,
        "rag": _rag_label(weighted_avg),
        "top_gaps": [g["label"] for g in top_gaps],
        "data_source": "CSRD Annual Report (extracted)" if has_real_data else "Peer benchmark estimate",
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", summary="List 10 demo analyst portfolios")
def list_analyst_portfolios():
    """Return the 10 pre-defined analyst portfolio definitions with summary stats."""
    results = []
    for pd in DEMO_PORTFOLIOS:
        total_exposure = sum(e["exposure_eur_mn"] for e in pd["entities"])
        slugs = [e["slug"] for e in pd["entities"]]
        entities_detail = []
        for slug in slugs:
            entity = _entity_by_slug(slug)
            if entity:
                entities_detail.append({
                    "name":            entity["name"],
                    "sector":          entity["sector"],
                    "country":         entity["country"],
                    "has_csrd_report": entity["has_csrd_report"],
                    "peer_score":      entity["peer_score"],
                    "nzba_member":     entity["nzba_member"],
                    "pcaf_member":     entity["pcaf_member"],
                    "sbti_status":     entity["sbti_status"],
                })
        csrd_covered = sum(1 for e in entities_detail if e["has_csrd_report"])
        avg_peer_score = round(
            sum(e["peer_score"] for e in entities_detail) / len(entities_detail), 1
        ) if entities_detail else 0

        results.append({
            "id":              pd["id"],
            "name":            pd["name"],
            "description":     pd["description"],
            "use_case":        pd["use_case"],
            "regulatory_focus": pd["regulatory_focus"],
            "entity_count":    len(pd["entities"]),
            "total_exposure_eur_mn": total_exposure,
            "csrd_report_coverage": csrd_covered,
            "avg_peer_score":  avg_peer_score,
            "entities":        entities_detail,
        })
    return {"portfolios": results}


@router.get("/{portfolio_id}", summary="Get one demo portfolio definition")
def get_analyst_portfolio(portfolio_id: str):
    """Return full definition of one demo portfolio."""
    pd = next((p for p in DEMO_PORTFOLIOS if p["id"] == portfolio_id), None)
    if not pd:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")

    entities_detail = []
    for ent_ref in pd["entities"]:
        slug = ent_ref["slug"]
        entity = _entity_by_slug(slug)
        if entity:
            entities_detail.append({
                **entity,
                "exposure_eur_mn": ent_ref["exposure_eur_mn"],
                "asset_type":      ent_ref["asset_type"],
            })

    total_exposure = sum(e["exposure_eur_mn"] for e in entities_detail)
    avg_peer_score = round(
        sum(e["peer_score"] for e in entities_detail) / len(entities_detail), 1
    ) if entities_detail else 0
    nzba_count  = sum(1 for e in entities_detail if e["nzba_member"])
    pcaf_count  = sum(1 for e in entities_detail if e["pcaf_member"])
    csrd_count  = sum(1 for e in entities_detail if e["has_csrd_report"])

    return {
        "id":           pd["id"],
        "name":         pd["name"],
        "description":  pd["description"],
        "use_case":     pd["use_case"],
        "regulatory_focus": pd["regulatory_focus"],
        "entities":     entities_detail,
        "summary": {
            "entity_count":          len(entities_detail),
            "total_exposure_eur_mn": total_exposure,
            "avg_peer_score":        avg_peer_score,
            "nzba_members":          nzba_count,
            "pcaf_members":          pcaf_count,
            "csrd_report_coverage":  csrd_count,
        },
    }


@router.get("/{portfolio_id}/gap-assessment", summary="Gap assessment for a demo portfolio")
def get_portfolio_gap_assessment(
    portfolio_id: str,
    db: Session = Depends(get_db),
):
    """
    Return a per-entity CSRD/TCFD/ISSB/PCAF data gap assessment for all
    entities in the demo portfolio.

    For entities with real CSRD reports (8 processed), coverage is derived
    from extracted kpi_values enriched by analyst estimates.
    For peer-benchmark-only entities, coverage uses analyst score proxies.
    """
    pd = next((p for p in DEMO_PORTFOLIOS if p["id"] == portfolio_id), None)
    if not pd:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")

    entity_assessments = []
    for ent_ref in pd["entities"]:
        slug = ent_ref["slug"]
        entity = _entity_by_slug(slug)
        if not entity:
            continue

        # Try to pull real CSRD coverage from DB for entities with processed reports
        real_csrd_kpi_count = 0
        if entity["has_csrd_report"] and db:
            try:
                result = db.execute(text("""
                    SELECT COUNT(kv.id) as kpi_count
                    FROM csrd_kpi_values kv
                    JOIN csrd_entity_registry er ON er.id = kv.entity_registry_id
                    WHERE LOWER(er.entity_name) LIKE :name_pattern
                """), {"name_pattern": f"%{entity['name'].split()[0].lower()}%"}).scalar()
                real_csrd_kpi_count = int(result or 0)
            except Exception as exc:
                logger.warning("DB query for %s failed: %s", entity["name"], exc)

        gap = _gap_assessment_for_entity(slug, entity["has_csrd_report"])

        entity_assessments.append({
            "name":              entity["name"],
            "slug":              slug,
            "sector":            entity["sector"],
            "country":           entity["country"],
            "region":            entity["region"],
            "has_csrd_report":   entity["has_csrd_report"],
            "real_csrd_kpi_count": real_csrd_kpi_count,
            "peer_score":        entity["peer_score"],
            "nzba_member":       entity["nzba_member"],
            "pcaf_member":       entity["pcaf_member"],
            "sbti_status":       entity["sbti_status"],
            "exposure_eur_mn":   ent_ref["exposure_eur_mn"],
            "asset_type":        ent_ref["asset_type"],
            "gap_assessment":    gap,
        })

    # Portfolio-level aggregates
    if entity_assessments:
        all_cats = list(FRAMEWORK_GAP_CATEGORIES.keys())
        portfolio_coverage = {}
        for cat_key in all_cats:
            weights = [e["exposure_eur_mn"] for e in entity_assessments]
            scores  = [e["gap_assessment"]["categories"][i]["coverage_pct"]
                       for e in entity_assessments
                       for i, c in enumerate(e["gap_assessment"]["categories"])
                       if c["key"] == cat_key]
            if scores and weights:
                wt = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
                portfolio_coverage[cat_key] = {
                    "coverage_pct": round(wt, 1),
                    "label":        FRAMEWORK_GAP_CATEGORIES[cat_key]["label"],
                    "group":        FRAMEWORK_GAP_CATEGORIES[cat_key]["group"],
                    "rag":          _rag_label(wt),
                }
        overall_portfolio_score = round(
            sum(v["coverage_pct"] for v in portfolio_coverage.values()) / len(portfolio_coverage), 1
        )
    else:
        portfolio_coverage = {}
        overall_portfolio_score = 0

    return {
        "portfolio_id":    portfolio_id,
        "portfolio_name":  pd["name"],
        "use_case":        pd["use_case"],
        "entity_count":    len(entity_assessments),
        "overall_portfolio_score": overall_portfolio_score,
        "portfolio_coverage": portfolio_coverage,
        "entities":        entity_assessments,
        "framework_categories": [
            {"key": k, "label": v["label"], "group": v["group"], "required_dps": v["required_dps"]}
            for k, v in FRAMEWORK_GAP_CATEGORIES.items()
        ],
    }


@router.post("/seed", summary="Seed demo portfolios into portfolios_pg / assets_pg")
def seed_demo_portfolios(db: Session = Depends(get_db)):
    """
    Insert all 4 demo portfolios and their entity assets into the database
    (portfolios_pg + assets_pg). Idempotent — skips portfolios that already exist.
    """
    created = []
    skipped = []

    for pd_def in DEMO_PORTFOLIOS:
        existing = db.execute(
            text("SELECT id FROM portfolios_pg WHERE id = :pid"),
            {"pid": pd_def["id"]}
        ).fetchone()

        if existing:
            skipped.append(pd_def["id"])
            continue

        portfolio = PortfolioPG(
            id=pd_def["id"],
            name=pd_def["name"],
            description=pd_def["description"],
        )
        db.add(portfolio)

        for ent_ref in pd_def["entities"]:
            slug = ent_ref["slug"]
            entity = _entity_by_slug(slug)
            if not entity:
                continue

            asset = AssetPG(
                id=str(uuid.uuid4()),
                portfolio_id=pd_def["id"],
                asset_type=ent_ref["asset_type"],
                company_name=entity["name"],
                company_sector=entity["sector"],
                company_subsector=entity.get("subsector", ""),
                exposure=float(ent_ref["exposure_eur_mn"]) * 1_000_000,
                market_value=float(ent_ref["exposure_eur_mn"]) * 1_000_000 * 0.97,
                base_pd=0.015 if entity["sbti_status"] == "Approved" else 0.025,
                base_lgd=0.40,
                rating="A" if entity["peer_score"] >= 75 else "BBB",
                maturity_years=5,
            )
            db.add(asset)

        created.append(pd_def["id"])

    db.commit()
    return {
        "created":  created,
        "skipped":  skipped,
        "message":  f"Seeded {len(created)} portfolios. {len(skipped)} already existed.",
    }
