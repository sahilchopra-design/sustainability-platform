"""
Blended Finance & DFI Instruments  —  E72 Routes
=================================================
Prefix: /api/v1/blended-finance
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.blended_finance_engine import (
    assess_blended_structure,
    analyse_dfi_standards,
    model_concessional_layers,
    calculate_mobilisation_metrics,
    generate_blended_portfolio,
    DFI_PROFILES,
    INSTRUMENT_CONFIGS,
    CONVERGENCE_BENCHMARKS,
    ODA_SECTOR_CODES,
)

router = APIRouter(prefix="/api/v1/blended-finance", tags=["E72 Blended Finance & DFI"])


# ── Pydantic Request Models ───────────────────────────────────────────────────

class BlendedStructureRequest(BaseModel):
    entity_id: str = Field(..., description="Entity identifier")
    instrument_type: str = Field(
        "guarantees",
        description="Instrument: guarantees/first_loss/concessional_loans/equity/technical_assistance",
    )
    project_size_usd: float = Field(..., gt=0)
    sector: str = Field("infrastructure")
    country: str = Field("Kenya")


class DFIStandardsRequest(BaseModel):
    entity_id: str
    dfi_partner: str = Field("IFC", description="DFI partner: IFC/MIGA/EBRD/ADB/AIIB/AfDB")
    project_category: str = Field("B", description="Project category A/B/C")


class ConcessionalLayersRequest(BaseModel):
    entity_id: str
    total_size_usd: float = Field(..., gt=0)
    sectors: list[str] = Field(default_factory=lambda: ["infrastructure"])


class MobilisationMetricsRequest(BaseModel):
    entity_id: str
    public_finance_usd: float = Field(..., gt=0)
    private_co_finance_usd: float = Field(..., ge=0)


class BlendedPortfolioRequest(BaseModel):
    entity_id: str
    instruments: list[dict] = Field(default_factory=list)


# ── POST Endpoints ────────────────────────────────────────────────────────────

@router.post("/structure", summary="Assess blended finance structure")
async def post_blended_structure(req: BlendedStructureRequest) -> dict[str, Any]:
    """
    Assess a blended finance structure for a project.

    Returns concessional layer sizing (10-40% of total), MDB partner match
    (IFC/MIGA/EBRD/ADB/AIIB/AfDB), IFC PS 1-8 compliance, mobilisation ratio
    vs Convergence 2023 benchmarks, OECD DAC ODA eligibility and SDG alignment.
    """
    try:
        return assess_blended_structure(
            entity_id=req.entity_id,
            instrument_type=req.instrument_type,
            project_size_usd=req.project_size_usd,
            sector=req.sector,
            country=req.country,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/dfi-standards", summary="Analyse DFI E&S standards compliance")
async def post_dfi_standards(req: DFIStandardsRequest) -> dict[str, Any]:
    """
    Analyse DFI Environmental & Social standards compliance.

    Scores all 8 IFC Performance Standards, determines E&S risk tier (A/B/C),
    evaluates EDGE green building criteria and disclosure requirements.
    """
    try:
        return analyse_dfi_standards(
            entity_id=req.entity_id,
            dfi_partner=req.dfi_partner,
            project_category=req.project_category,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/concessional-layers", summary="Model tranche waterfall")
async def post_concessional_layers(req: ConcessionalLayersRequest) -> dict[str, Any]:
    """
    Model tranche waterfall: senior / mezzanine / first-loss / grant.

    Returns return targets per tier, investor type mapping (institutional /
    DFI / philanthropic / government) and blended IRR.
    """
    try:
        return model_concessional_layers(
            entity_id=req.entity_id,
            total_size_usd=req.total_size_usd,
            sectors=req.sectors,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/mobilisation-metrics", summary="Calculate MDB mobilisation metrics")
async def post_mobilisation_metrics(req: MobilisationMetricsRequest) -> dict[str, Any]:
    """
    Calculate MDB leverage ratios, additionality scores and crowding assessment.

    Benchmarks from Convergence 2023 database; methodology per MDB
    Harmonised Framework for Additionality (2018).
    """
    try:
        return calculate_mobilisation_metrics(
            entity_id=req.entity_id,
            public_finance_usd=req.public_finance_usd,
            private_co_finance_usd=req.private_co_finance_usd,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/portfolio", summary="Generate blended portfolio analytics")
async def post_blended_portfolio(req: BlendedPortfolioRequest) -> dict[str, Any]:
    """
    Aggregate blended finance instruments into portfolio-level analytics.

    Returns risk-return frontier, SDG alignment (SDG 13/17), impact metrics
    (CO2 avoided, jobs, beneficiaries) and Convergence-style statistics.
    """
    try:
        return generate_blended_portfolio(
            entity_id=req.entity_id,
            instruments=req.instruments,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Reference GET Endpoints ───────────────────────────────────────────────────

@router.get("/ref/mdb-profiles", summary="Reference: MDB and DFI profiles")
async def get_mdb_profiles() -> dict[str, Any]:
    """Return profiles for IFC, MIGA, EBRD, ADB, AIIB and AfDB."""
    return {"mdb_profiles": DFI_PROFILES}


@router.get("/ref/instruments", summary="Reference: blended finance instrument types")
async def get_instruments() -> dict[str, Any]:
    """Return the 5 instrument type configurations with concessional share ranges."""
    return {
        "instruments": {
            k: {
                "description": v["description"],
                "concessional_share_pct_range": [round(x * 100, 1) for x in v["concessional_share_range"]],
                "oda_eligible": v["oda_eligible"],
                "risk_mitigant": v["risk_mitigant"],
            }
            for k, v in INSTRUMENT_CONFIGS.items()
        }
    }


@router.get("/ref/dac-sectors", summary="Reference: OECD DAC sector codes")
async def get_dac_sectors() -> dict[str, Any]:
    """Return OECD DAC 5-digit sector purpose codes for ODA reporting."""
    return {"dac_sector_codes": ODA_SECTOR_CODES}


@router.get("/ref/convergence-benchmarks", summary="Reference: Convergence 2023 benchmarks")
async def get_convergence_benchmarks() -> dict[str, Any]:
    """Return Convergence 2023 mobilisation ratio benchmarks by sector (mean, median, p25, p75)."""
    return {"convergence_benchmarks": CONVERGENCE_BENCHMARKS}


@router.get("/ref/ep-categories", summary="Reference: Equator Principles categories")
async def get_ep_categories() -> dict[str, Any]:
    """Return EP4 project categorisation A/B/C criteria."""
    return {
        "ep4_categories": {
            "A": "Significant adverse E&S impacts — diverse, irreversible or unprecedented",
            "B": "Limited adverse E&S impacts — few, site-specific, largely reversible",
            "C": "Minimal or no adverse E&S impacts",
        },
        "note": "EP4 applies to projects in OECD non-high-income countries and all Category A/B projects globally",
    }
