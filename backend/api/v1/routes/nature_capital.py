"""
nature_capital.py — E77 Nature Capital Accounting Routes
SEEA EA 2021 | TNFD v1.0 | ENCORE 62 services | TEEB/IPBES monetary values
WAVES Adjusted Savings | CBD GBF Target 15 | CSRD ESRS E4
"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

from services.nature_capital_engine import (
    assess_natural_capital,
    valuate_ecosystem_services,
    calculate_dependency_score,
    score_natural_capital_disclosure,
    generate_nature_balance_sheet,
    SEEA_EA_ACCOUNT_TYPES,
    BIOME_UNIT_VALUES,
    ENCORE_ECOSYSTEM_SERVICES,
    TNFD_DISCLOSURE_TOPICS,
)

router = APIRouter(prefix="/api/v1/nature-capital", tags=["E77 Nature Capital Accounting"])


# ── Request Models ─────────────────────────────────────────────────────────────

class AssessNaturalCapitalRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    asset_name: str = Field(..., description="Name of the natural asset")
    ecosystem_type: str = Field(..., description="Type of ecosystem (tropical_forest, wetland_freshwater, mangrove, coral_reef, cropland, etc.)")
    extent_ha: float = Field(..., gt=0, description="Extent of ecosystem in hectares")
    location_country: str = Field(..., description="ISO 2-letter country code or country name")


class ValuateServicesRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    ecosystem_type: str = Field(..., description="Type of ecosystem")
    extent_ha: float = Field(..., gt=0, description="Extent in hectares")
    services_list: list[str] = Field(default_factory=list, description="Optional: specific ENCORE service IDs to valuate (ES-P01, ES-R01, etc.). Leave empty to valuate all applicable services.")


class DependencyScoreRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    sector: str = Field(..., description="Industry sector (agriculture, food_beverage, forestry, fishing, mining, energy, real_estate, pharmaceuticals, etc.)")
    operations_description: str = Field("", description="Description of business operations for dependency assessment")


class DisclosureScoreRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    reporting_standard: str = Field(..., description="Primary reporting standard (TNFD, CSRD_ESRS, GRI, SEEA_EA)")


class BalanceSheetRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    assets: list[dict[str, Any]] = Field(
        ...,
        description="List of natural assets with: asset_name, ecosystem_type, extent_ha. Optional: condition_score (0-1)."
    )


# ── POST Endpoints ─────────────────────────────────────────────────────────────

@router.post("/assess", summary="Natural Capital Assessment (SEEA EA 2021 / TNFD)")
async def assess_natural_capital_endpoint(req: AssessNaturalCapitalRequest) -> dict[str, Any]:
    """
    Assess natural capital for an ecosystem asset.
    Uses SEEA EA 2021 account types, TNFD v1.0 dependency/impact scoring,
    TEEB/IPBES monetary unit values, biodiversity condition scoring, and CBD GBF Target 15 alignment.
    """
    return assess_natural_capital(
        entity_id=req.entity_id,
        asset_name=req.asset_name,
        ecosystem_type=req.ecosystem_type,
        extent_ha=req.extent_ha,
        location_country=req.location_country,
    )


@router.post("/valuate-services", summary="Ecosystem Services Valuation (ENCORE / TEEB)")
async def valuate_services_endpoint(req: ValuateServicesRequest) -> dict[str, Any]:
    """
    Valuate ecosystem services using ENCORE 62-service classification and TEEB/IPBES biome unit values.
    Covers 10 provisioning, 9 regulating, and 3 cultural service categories.
    Returns annual flow values (USD/year) per service and WAVES NPV.
    """
    return valuate_ecosystem_services(
        entity_id=req.entity_id,
        ecosystem_type=req.ecosystem_type,
        extent_ha=req.extent_ha,
        services_list=req.services_list,
    )


@router.post("/dependency-score", summary="Nature Dependency Score (TNFD LEAP / ENCORE)")
async def dependency_score_endpoint(req: DependencyScoreRequest) -> dict[str, Any]:
    """
    Calculate sector nature dependency score using ENCORE 58-sector matrix.
    Performs TNFD LEAP Step A-D assessment, identifies critical dependencies,
    estimates revenue at risk from nature loss, and calculates substitutability.
    """
    return calculate_dependency_score(
        entity_id=req.entity_id,
        sector=req.sector,
        operations_description=req.operations_description,
    )


@router.post("/disclosure-score", summary="Natural Capital Disclosure Completeness")
async def disclosure_score_endpoint(req: DisclosureScoreRequest) -> dict[str, Any]:
    """
    Score natural capital disclosure completeness across:
    - TNFD v1.0 (14 recommended disclosures across 4 pillars)
    - SEEA EA adoption level (6 account types)
    - GRI 304 biodiversity (4 disclosures)
    - CSRD ESRS E4 (6 disclosures)
    - CBD GBF Target 15 sub-elements a-f
    """
    return score_natural_capital_disclosure(
        entity_id=req.entity_id,
        reporting_standard=req.reporting_standard,
    )


@router.post("/balance-sheet", summary="Natural Capital Balance Sheet (SEEA EA Table Structure)")
async def balance_sheet_endpoint(req: BalanceSheetRequest) -> dict[str, Any]:
    """
    Generate a SEEA EA 2021 natural capital balance sheet.
    Accounts for opening/closing stock, changes in extent and condition,
    ecosystem service flows, integrated P&L impact, and WAVES capitalisation.
    """
    return generate_nature_balance_sheet(
        entity_id=req.entity_id,
        assets=req.assets,
    )


# ── GET Reference Endpoints ────────────────────────────────────────────────────

@router.get("/ref/ecosystem-types", summary="Supported Ecosystem Types Reference")
async def get_ecosystem_types() -> dict[str, Any]:
    """
    Return all 19 supported ecosystem/biome types with TEEB monetary value ranges.
    """
    return {
        "framework": "SEEA EA 2021 / IPBES Global Assessment / TEEB",
        "ecosystem_count": len(BIOME_UNIT_VALUES),
        "ecosystems": [
            {
                "ecosystem_type": k,
                "total_value_usd_ha_yr": v["total_usd_ha_yr"],
                "provisioning_usd_ha_yr": v["provisioning"],
                "regulating_usd_ha_yr": v["regulating"],
                "cultural_usd_ha_yr": v["cultural"],
                "source": v["source"],
            }
            for k, v in BIOME_UNIT_VALUES.items()
        ],
    }


@router.get("/ref/seea-accounts", summary="SEEA EA 2021 Account Types")
async def get_seea_accounts() -> dict[str, Any]:
    """
    Return SEEA EA 2021 account type definitions (EA-1 to EA-6).
    """
    return {
        "framework": "System of Environmental-Economic Accounting Ecosystem Accounting (SEEA EA 2021)",
        "adopted_by_un": "United Nations Statistical Commission 2021",
        "accounts_count": len(SEEA_EA_ACCOUNT_TYPES),
        "accounts": SEEA_EA_ACCOUNT_TYPES,
    }


@router.get("/ref/encore-services", summary="ENCORE 62 Ecosystem Services Classification")
async def get_encore_services() -> dict[str, Any]:
    """
    Return complete ENCORE ecosystem services classification:
    20 provisioning services, 23 regulating/maintenance services, 6 cultural services (62 total).
    """
    provisioning_count = len(ENCORE_ECOSYSTEM_SERVICES["provisioning"])
    regulating_count = len(ENCORE_ECOSYSTEM_SERVICES["regulating_maintenance"])
    cultural_count = len(ENCORE_ECOSYSTEM_SERVICES["cultural"])
    return {
        "framework": "ENCORE (Exploring Natural Capital Opportunities, Risks and Exposure) — UNEP-WCMC",
        "version": "2023",
        "total_services": provisioning_count + regulating_count + cultural_count,
        "categories": {
            "provisioning": {
                "count": provisioning_count,
                "description": "Services that provision goods from nature (food, water, materials, energy, genetic resources)",
                "services": ENCORE_ECOSYSTEM_SERVICES["provisioning"],
            },
            "regulating_maintenance": {
                "count": regulating_count,
                "description": "Services that regulate and maintain ecosystem processes and conditions",
                "services": ENCORE_ECOSYSTEM_SERVICES["regulating_maintenance"],
            },
            "cultural": {
                "count": cultural_count,
                "description": "Non-material services with cultural and spiritual significance",
                "services": ENCORE_ECOSYSTEM_SERVICES["cultural"],
            },
        },
    }


@router.get("/ref/tnfd-disclosures", summary="TNFD v1.0 Recommended Disclosures")
async def get_tnfd_disclosures() -> dict[str, Any]:
    """
    Return TNFD v1.0 14 recommended disclosures across 4 pillars
    (Governance, Strategy, Risk Management, Metrics & Targets).
    Includes LEAP approach reference.
    """
    pillars = {}
    for d in TNFD_DISCLOSURE_TOPICS:
        p = d["pillar"]
        if p not in pillars:
            pillars[p] = []
        pillars[p].append({"id": d["id"], "topic": d["topic"]})

    return {
        "framework": "Taskforce on Nature-related Financial Disclosures (TNFD)",
        "version": "v1.0",
        "published": "September 2023",
        "total_disclosures": len(TNFD_DISCLOSURE_TOPICS),
        "pillars": pillars,
        "all_disclosures": TNFD_DISCLOSURE_TOPICS,
        "leap_approach": {
            "L": "Locate — Where does the organisation interface with nature?",
            "E": "Evaluate — What are the dependencies and impacts?",
            "A": "Assess — What are the nature-related risks and opportunities?",
            "P": "Prepare — What actions and resources are required?",
        },
    }


@router.get("/ref/biome-values", summary="TEEB / IPBES Biome Unit Values Reference")
async def get_biome_values() -> dict[str, Any]:
    """
    Return TEEB/Costanza et al. 2014 / IPBES monetary unit values per biome (USD/ha/year).
    Used as basis for natural capital monetary valuation via benefit transfer methodology.
    """
    return {
        "methodology": "Benefit transfer from primary studies — Costanza et al. (2014), TEEB (2010), IPBES (2019)",
        "price_year": 2023,
        "currency": "USD",
        "caveat": "Unit values are estimates based on meta-analysis; site-specific valuations require primary studies",
        "biome_count": len(BIOME_UNIT_VALUES),
        "biomes": [
            {
                "biome": k,
                "total_usd_ha_yr": v["total_usd_ha_yr"],
                "provisioning": v["provisioning"],
                "regulating": v["regulating"],
                "cultural": v["cultural"],
                "source": v["source"],
            }
            for k, v in sorted(BIOME_UNIT_VALUES.items(), key=lambda x: x[1]["total_usd_ha_yr"], reverse=True)
        ],
    }
