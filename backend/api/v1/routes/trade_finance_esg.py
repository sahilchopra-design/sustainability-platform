"""
Sustainable Trade Finance ESG  —  E75 Routes
=============================================
Prefix: /api/v1/trade-finance-esg
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.trade_finance_engine import (
    assess_equator_principles,
    evaluate_eca_standards,
    score_supply_chain_esg,
    calculate_trade_flow_emissions,
    generate_green_instrument,
    EP4_CATEGORISATION,
    EP4_PRINCIPLES,
    OECD_ARRANGEMENT_SECTORS,
    ESG_TIERS,
    TRANSPORT_EMISSION_FACTORS,
    PRODUCT_GHG_INTENSITY,
    GREEN_INSTRUMENT_CRITERIA,
    ICC_STF_PRINCIPLES,
)

router = APIRouter(prefix="/api/v1/trade-finance-esg", tags=["E75 Sustainable Trade Finance"])


# ── Pydantic Request Models ───────────────────────────────────────────────────

class EquatorPrinciplesRequest(BaseModel):
    entity_id: str
    project_type: str = Field("infrastructure", description="Project type (e.g. mining, dam, manufacturing, renewable_energy)")
    project_cost_usd: float = Field(..., gt=0, description="Total project cost USD")
    country: str = Field("Kenya", description="Host country")
    sector: str = Field("infrastructure", description="Economic sector")


class ECAStandardsRequest(BaseModel):
    entity_id: str
    export_credit_type: str = Field("buyer_credit", description="ECA instrument type")
    oecd_sector: str = Field(
        "infrastructure",
        description="OECD Arrangement sector: coal_power/renewable_energy/nuclear/infrastructure/manufacturing/ships/aircraft",
    )


class SupplyChainESGRequest(BaseModel):
    entity_id: str
    suppliers: list[dict] = Field(
        default_factory=list,
        description="List of supplier dicts: supplier_id, supplier_name, country, annual_spend_usd, revenue_usd",
    )
    product_category: str = Field("manufacturing", description="Product category for Scope 3 Cat 1 GHG attribution")


class TradeFlowEmissionsRequest(BaseModel):
    entity_id: str
    trade_lanes: list[dict] = Field(
        default_factory=list,
        description="List of lane dicts: from_country, to_country, transport_mode, distance_km, volume_pct",
    )
    commodity_type: str = Field("manufacturing", description="Commodity type for lifecycle GHG intensity")
    volume_tonnes: float = Field(..., gt=0, description="Total trade volume in tonnes")


class GreenInstrumentRequest(BaseModel):
    entity_id: str
    instrument_type: str = Field(
        "green_lc",
        description="Instrument: green_lc / green_sblc / sustainability_linked_trade_loan / sustainable_supply_chain_finance",
    )
    use_of_proceeds: str = Field("renewable_energy", description="Use of proceeds / eligible sector")
    counterparty_country: str = Field("China", description="Counterparty country for OECD CRC assessment")


# ── POST Endpoints ────────────────────────────────────────────────────────────

@router.post("/equator-principles", summary="Assess Equator Principles v4 compliance")
async def post_equator_principles(req: EquatorPrinciplesRequest) -> dict[str, Any]:
    """
    Assess Equator Principles IV (2020) compliance for a project finance transaction.

    Returns EP categorisation (A/B/C), scores for all 10 EP principles,
    ESIA requirement, Independent Environmental & Social Consultant requirement,
    Grievance Mechanism assessment and IFC Performance Standard applicability.
    """
    try:
        return assess_equator_principles(
            entity_id=req.entity_id,
            project_type=req.project_type,
            project_cost_usd=req.project_cost_usd,
            country=req.country,
            sector=req.sector,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/eca-standards", summary="Evaluate ECA standards under OECD Arrangement")
async def post_eca_standards(req: ECAStandardsRequest) -> dict[str, Any]:
    """
    Evaluate export credit standards under the OECD Arrangement (2023 revision).

    Covers climate change sector understandings (coal exclusion from Jan 2022),
    OECD CRC 0-7 country risk classification, maximum repayment terms and
    premium calculation methodology.
    """
    try:
        return evaluate_eca_standards(
            entity_id=req.entity_id,
            export_credit_type=req.export_credit_type,
            oecd_sector=req.oecd_sector,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/supply-chain-esg", summary="Score supply chain ESG tiers and dynamic discounting")
async def post_supply_chain_esg(req: SupplyChainESGRequest) -> dict[str, Any]:
    """
    Score supplier ESG tiers (A-E) and model dynamic discounting ratchet.

    Returns per-supplier ESG score, dynamic discounting margin (0-300bps),
    Scope 3 Category 1 GHG attribution (PCAF-weighted), reverse factoring
    eligibility and ILO core labour standards compliance.
    """
    try:
        return score_supply_chain_esg(
            entity_id=req.entity_id,
            suppliers=req.suppliers,
            product_category=req.product_category,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/trade-flow-emissions", summary="Calculate trade flow GHG emissions (Scope 3 Cat 1/4)")
async def post_trade_flow_emissions(req: TradeFlowEmissionsRequest) -> dict[str, Any]:
    """
    Calculate GHG emissions for trade flows per the GHG Protocol Value Chain Standard.

    Returns Scope 3 Category 4 (upstream transportation & distribution) per
    transport mode (air/sea/road/rail) and Category 1 (purchased goods) per
    product lifecycle intensity. Identifies minimum-emission modal alternatives.
    """
    try:
        return calculate_trade_flow_emissions(
            entity_id=req.entity_id,
            trade_lanes=req.trade_lanes,
            commodity_type=req.commodity_type,
            volume_tonnes=req.volume_tonnes,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/green-instrument", summary="Generate green trade finance instrument")
async def post_green_instrument(req: GreenInstrumentRequest) -> dict[str, Any]:
    """
    Assess and generate a green trade finance instrument.

    Covers green LC, green SBLC, sustainability-linked trade loan and
    sustainable supply chain finance facility. Returns ICC STF Principles
    alignment score, ICMA GBS classification, documentation requirements
    and pricing benefit estimate (bps).
    """
    try:
        return generate_green_instrument(
            entity_id=req.entity_id,
            instrument_type=req.instrument_type,
            use_of_proceeds=req.use_of_proceeds,
            counterparty_country=req.counterparty_country,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Reference GET Endpoints ───────────────────────────────────────────────────

@router.get("/ref/ep4-categories", summary="Reference: Equator Principles v4 categories")
async def get_ep4_categories() -> dict[str, Any]:
    """Return EP4 (2020) project category criteria, ESIA and monitoring requirements."""
    return {
        "ep4_categories": EP4_CATEGORISATION,
        "ep4_principles": EP4_PRINCIPLES,
        "high_risk_country_count": 12,
        "note": "EP4 applies to project finance ≥$10M USD and specific export credit transactions",
    }


@router.get("/ref/oecd-arrangement", summary="Reference: OECD Arrangement on export credits")
async def get_oecd_arrangement() -> dict[str, Any]:
    """Return OECD Arrangement 2023 sector understandings, restrictions and max repayment terms."""
    return {
        "oecd_arrangement_sectors": OECD_ARRANGEMENT_SECTORS,
        "version": "2023 revision",
        "climate_key_events": {
            "coal_exclusion_date": "2022-01-01",
            "renewable_preferred_since": "2021-01-01",
        },
        "crc_scale": {
            "0": "Risk-free (OECD high income)",
            "1-2": "Low risk",
            "3-4": "Medium risk",
            "5-6": "High risk",
            "7": "Very high risk",
        },
    }


@router.get("/ref/esg-tiers", summary="Reference: supplier ESG tier definitions")
async def get_esg_tiers() -> dict[str, Any]:
    """Return supplier ESG tier A-E definitions, score ranges and dynamic discounting bands."""
    return {
        "esg_tiers": ESG_TIERS,
        "icc_stf_principles": ICC_STF_PRINCIPLES,
        "ilo_core_standards": [
            "Freedom of Association (C087, C098)",
            "Forced Labour (C029, C105)",
            "Child Labour (C138, C182)",
            "Non-Discrimination (C100, C111)",
        ],
    }


@router.get("/ref/emission-factors", summary="Reference: transport mode emission factors")
async def get_emission_factors() -> dict[str, Any]:
    """Return GHG Protocol-aligned transport emission factors (kgCO2e/tonne-km)."""
    return {
        "transport_emission_factors": TRANSPORT_EMISSION_FACTORS,
        "product_ghg_intensity_kgco2e_per_tonne": PRODUCT_GHG_INTENSITY,
        "scope3_categories": {
            "Cat1": "Purchased goods and services — product lifecycle emissions",
            "Cat4": "Upstream transportation and distribution",
        },
        "standard": "GHG Protocol Corporate Value Chain Standard 2011 + ISO 14083:2023",
    }


@router.get("/ref/green-instruments", summary="Reference: green trade finance instruments")
async def get_green_instruments() -> dict[str, Any]:
    """Return green LC, SBLC, sustainability-linked loan and SCF facility criteria."""
    return {
        "green_instruments": GREEN_INSTRUMENT_CRITERIA,
        "icc_stf_principles_2022": ICC_STF_PRINCIPLES,
        "icma_categories": {
            "Green": "Use-of-proceeds aligned to ICMA GBP eligible categories",
            "Sustainability-Linked": "KPI-based, not use-of-proceeds restricted",
            "Social": "Use-of-proceeds for social outcomes",
            "Sustainability": "Combined green + social use-of-proceeds",
        },
    }
