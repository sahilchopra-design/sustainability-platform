"""
climate_finance.py — E78 Climate Finance Flows Routes
OECD CRS Rio Markers | UNFCCC Art 2.1(c) | CPI 2023
NCQG $300bn COP29 | MDB Joint Tracking | OECD TOSSD
"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional

from services.climate_finance_engine import (
    track_climate_finance,
    assess_article21c_alignment,
    calculate_ncqg_contribution,
    measure_mobilisation,
    generate_climate_finance_report,
    OECD_RIO_MARKERS,
    RECIPIENT_COUNTRIES,
    CPI_2023_DATA,
    MDB_INSTITUTIONS,
    NCQG_STRUCTURE,
    IPCC_PATHWAYS,
    MOBILISATION_MULTIPLIERS,
)

router = APIRouter(prefix="/api/v1/climate-finance", tags=["E78 Climate Finance Flows"])


# ── Request Models ─────────────────────────────────────────────────────────────

class TrackClimateFinanceRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    portfolio_name: str = Field(..., description="Name of the financial portfolio or programme")
    year: int = Field(..., ge=2000, le=2035, description="Reporting year")
    instruments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Financial instruments with: name, amount_usd, instrument_type (loan/grant/equity/guarantee), ccm_marker (0/1/2), cca_marker (0/1/2), sector, recipient_country"
    )


class Article21cAlignmentRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    portfolio: dict[str, Any] = Field(default_factory=dict, description="Portfolio profile")
    financial_flows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Financial flows with: amount_usd, climate_aligned (bool), fossil_fuel (bool), sector, country"
    )


class NcqgContributionRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    institution_type: str = Field(
        ...,
        description="Institution type: developed_country_dfi, annex_ii_party, oecd_member_mdb, voluntary_contributor, emerging_economy_mdb, sovereign_wealth_fund"
    )
    baseline_finance_usd: float = Field(..., gt=0, description="Current baseline climate finance in USD")


class MobilisationRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    public_finance_usd: float = Field(..., gt=0, description="Total public finance deployed in USD")
    instruments: list[dict[str, Any]] = Field(
        ...,
        description="Instruments used with: type (guarantees/equity/concessional_loans/grants/technical_assistance/risk_sharing), amount_usd"
    )


class ClimateFinanceReportRequest(BaseModel):
    entity_id: str = Field(..., description="Unique entity identifier")
    year: int = Field(..., ge=2015, le=2035, description="Reporting year")


# ── POST Endpoints ─────────────────────────────────────────────────────────────

@router.post("/track", summary="Track Climate Finance (OECD CRS / Rio Markers)")
async def track_endpoint(req: TrackClimateFinanceRequest) -> dict[str, Any]:
    """
    Track climate finance flows using OECD CRS Rio markers methodology.
    Applies CCM/CCA marker counting rules (principal=100%, significant=50%),
    calculates adaptation/mitigation split, CPI Global Landscape alignment,
    and Paris consistency assessment.
    """
    return track_climate_finance(
        entity_id=req.entity_id,
        portfolio_name=req.portfolio_name,
        year=req.year,
        instruments=req.instruments,
    )


@router.post("/article21c-alignment", summary="UNFCCC Article 2.1(c) Financial Flows Alignment")
async def article21c_endpoint(req: Article21cAlignmentRequest) -> dict[str, Any]:
    """
    Assess alignment of financial flows with UNFCCC Article 2.1(c) —
    making finance flows consistent with low GHG emission development and
    climate-resilient development. Scores portfolio against 4 IPCC-compatible
    pathways (1.5°C/well-below-2°C/2°C/NDC). References Paris Agreement Article 9.
    """
    return assess_article21c_alignment(
        entity_id=req.entity_id,
        portfolio=req.portfolio,
        financial_flows=req.financial_flows,
    )


@router.post("/ncqg-contribution", summary="NCQG $300bn Contribution Assessment (COP29 Baku)")
async def ncqg_endpoint(req: NcqgContributionRequest) -> dict[str, Any]:
    """
    Calculate institution's contribution to the New Collective Quantified Goal on Climate Finance
    (NCQG) — $300bn/year by 2035 agreed at COP29 Baku 2024.
    Determines goal layer (core/broader), MDB mobilisation multiplier,
    private finance mobilised, grant equivalent, and TOSSD eligibility.
    """
    return calculate_ncqg_contribution(
        entity_id=req.entity_id,
        institution_type=req.institution_type,
        baseline_finance_usd=req.baseline_finance_usd,
    )


@router.post("/mobilisation", summary="Private Finance Mobilisation Measurement (OECD DAC)")
async def mobilisation_endpoint(req: MobilisationRequest) -> dict[str, Any]:
    """
    Measure private finance mobilisation ratios per instrument type.
    Uses OECD DAC Converged Statistical Reporting methodology and Convergence
    blending finance benchmarks. Calculates OECD TOSSD (Total Official Support
    for Sustainable Development) from provider and recipient perspectives.
    """
    return measure_mobilisation(
        entity_id=req.entity_id,
        public_finance_usd=req.public_finance_usd,
        instruments=req.instruments,
    )


@router.post("/report", summary="Climate Finance Biennial Report (UNFCCC BFR)")
async def report_endpoint(req: ClimateFinanceReportRequest) -> dict[str, Any]:
    """
    Generate UNFCCC Biennial Finance Report structure.
    Covers: public/private climate finance flows, MDB joint tracking,
    $100bn developed country commitment tracking (2020-2025 achieved),
    NCQG gap analysis ($300bn by 2035), and CPI 2023 data benchmarking.
    """
    return generate_climate_finance_report(
        entity_id=req.entity_id,
        year=req.year,
    )


# ── GET Reference Endpoints ────────────────────────────────────────────────────

@router.get("/ref/oecd-markers", summary="OECD CRS Rio Markers Reference")
async def get_oecd_markers() -> dict[str, Any]:
    """
    Return all 12 OECD CRS policy markers including Rio markers for
    climate change mitigation (CCM) and adaptation (CCA), biodiversity,
    desertification, water, nutrition, and digital technology.
    """
    return {
        "framework": "OECD Development Assistance Committee (DAC) — Creditor Reporting System (CRS)",
        "methodology": "Rio Marker methodology — counting rules: principal objective = 100%, significant objective = 50%",
        "marker_values": {"0": "Not targeted", "1": "Significant objective", "2": "Principal objective"},
        "markers_count": len(OECD_RIO_MARKERS),
        "markers": OECD_RIO_MARKERS,
    }


@router.get("/ref/recipient-countries", summary="Climate Finance Recipient Countries")
async def get_recipient_countries() -> dict[str, Any]:
    """
    Return 40 climate finance recipient countries with income group classification,
    climate vulnerability status, and V20 (Vulnerable Twenty Group) membership.
    """
    income_groups = {}
    for c in RECIPIENT_COUNTRIES:
        ig = c["income_group"]
        income_groups[ig] = income_groups.get(ig, 0) + 1
    return {
        "total_countries": len(RECIPIENT_COUNTRIES),
        "income_group_breakdown": income_groups,
        "v20_members": sum(1 for c in RECIPIENT_COUNTRIES if c["v20"]),
        "climate_vulnerable": sum(1 for c in RECIPIENT_COUNTRIES if c["climate_vulnerable"]),
        "countries": RECIPIENT_COUNTRIES,
    }


@router.get("/ref/cpi-data", summary="CPI Global Landscape of Climate Finance 2023")
async def get_cpi_data() -> dict[str, Any]:
    """
    Return Climate Policy Initiative (CPI) Global Landscape of Climate Finance 2023 data:
    total $1.3T actual vs $4.3T needed, breakdown by instrument/geography/sector.
    """
    return {
        "source": "Climate Policy Initiative — Global Landscape of Climate Finance 2023",
        "data_year": 2023,
        "key_findings": {
            "total_climate_finance_usd_bn": CPI_2023_DATA["total_climate_finance_usd_bn"],
            "annual_need_2030_usd_bn": CPI_2023_DATA["annual_need_2030_usd_bn"],
            "annual_gap_usd_bn": CPI_2023_DATA["annual_gap_usd_bn"],
            "adaptation_underfunding": f"${CPI_2023_DATA['adaptation_usd_bn']}bn actual vs ~$400bn needed",
        },
        "data": CPI_2023_DATA,
        "ipcc_pathways": IPCC_PATHWAYS,
    }


@router.get("/ref/mdb-institutions", summary="Multilateral Development Bank Climate Finance")
async def get_mdb_institutions() -> dict[str, Any]:
    """
    Return 8 major MDB institutions with climate finance shares, adaptation targets,
    and Paris alignment commitments.
    """
    total_climate = sum(m["total_finance_usd_bn"] * m["climate_share_pct"] / 100 for m in MDB_INSTITUTIONS)
    return {
        "framework": "MDB Joint Report on Climate Finance 2023",
        "total_mdb_climate_finance_usd_bn": round(total_climate, 1),
        "institutions_count": len(MDB_INSTITUTIONS),
        "institutions": MDB_INSTITUTIONS,
        "mobilisation_multipliers": MOBILISATION_MULTIPLIERS,
    }


@router.get("/ref/ncqg-structure", summary="NCQG $300bn Structure (COP29 Baku 2024)")
async def get_ncqg_structure() -> dict[str, Any]:
    """
    Return New Collective Quantified Goal on Climate Finance (NCQG) structure:
    $300bn/year by 2035 core goal, broader $1.3T goal, instrument split,
    predecessor $100bn commitment tracking, and grant equivalent requirements.
    """
    return {
        "framework": "UNFCCC New Collective Quantified Goal on Climate Finance (NCQG)",
        "cop_decision": "COP29 Baku November 2024",
        "legal_basis": "UNFCCC Articles 4.3, 4.4, 9 and Paris Agreement Article 9",
        "structure": NCQG_STRUCTURE,
        "predecessor_100bn_tracking": {
            "2020_actual_usd_bn": 83.3,
            "2021_actual_usd_bn": 89.6,
            "2022_actual_usd_bn": 115.9,
            "2023_estimate_usd_bn": 130.0,
            "source": "OECD Climate Finance Report 2024",
            "first_achieved": 2022,
        },
    }
