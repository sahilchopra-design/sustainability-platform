"""
E100 — Multi-Regulatory Climate Stress Test Orchestrator Routes
===============================================================
GET  /api/v1/stress-test-orchestrator/ref/ngfs-phase4-scenarios   — NGFS Phase IV library
GET  /api/v1/stress-test-orchestrator/ref/regulatory-frameworks   — 6 framework profiles
GET  /api/v1/stress-test-orchestrator/ref/sector-risk-profiles    — 20 NACE risk profiles
GET  /api/v1/stress-test-orchestrator/ref/transmission-channels   — 5 transmission channels
POST /api/v1/stress-test-orchestrator/run                         — full stress test
POST /api/v1/stress-test-orchestrator/scenario-comparison         — all-scenario comparison
POST /api/v1/stress-test-orchestrator/pd-migration                — single sector PD migration
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.stress_test_orchestrator_engine import (
    SectorExposure,
    StressTestRequest,
    ScenarioComparisonRequest,
    NGFS_PHASE4_SCENARIOS,
    REGULATORY_FRAMEWORKS,
    NACE_SECTOR_RISK_PROFILES,
    TRANSMISSION_CHANNELS,
    run_stress_test,
    run_scenario_comparison,
    calculate_pd_migration,
    get_regulatory_submission_template,
    get_ngfs_phase4_scenarios,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/stress-test-orchestrator",
    tags=["E100 — Multi-Regulatory Climate Stress Test Orchestrator"],
)


# ---------------------------------------------------------------------------
# Additional request models for route-level validation
# ---------------------------------------------------------------------------

class PDMigrationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    sector: str = Field(..., description="NACE sector key from sector-risk-profiles")
    scenario_id: str = Field(..., description="NGFS Phase IV scenario ID")
    time_horizon_year: int = Field(2030, description="Target year: 2025 | 2030 | 2040 | 2050")


class SubmissionTemplateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    regulatory_framework: str = Field(
        ...,
        description="ECB_2022 | EBA_2023 | BoE_CBES_2021 | APRA_2022 | MAS_2022 | RBI_2022",
    )


# ---------------------------------------------------------------------------
# GET — Reference endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/ngfs-phase4-scenarios", summary="NGFS Phase IV Scenario Library (2024)")
async def get_ngfs_phase4_ref() -> Dict[str, Any]:
    """
    Return all 7 NGFS Phase IV (2024) scenario profiles including carbon price
    trajectories, GDP deviations, physical risk parameters and temperature outcomes.
    """
    try:
        return get_ngfs_phase4_scenarios()
    except Exception as exc:
        logger.exception("Error fetching NGFS Phase IV scenarios")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/regulatory-frameworks", summary="Regulatory Framework Profiles (6 frameworks)")
async def get_regulatory_frameworks_ref() -> Dict[str, Any]:
    """
    Return profiles for all 6 regulatory frameworks:
    ECB 2022, EBA 2023, BoE CBES 2021, APRA 2022, MAS 2022, RBI 2022.
    Includes CET1/Tier1 thresholds, submission template fields and scenario support matrix.
    """
    try:
        return {
            "frameworks": REGULATORY_FRAMEWORKS,
            "framework_count": len(REGULATORY_FRAMEWORKS),
            "framework_ids": list(REGULATORY_FRAMEWORKS.keys()),
            "jurisdictions_covered": [
                j
                for fw in REGULATORY_FRAMEWORKS.values()
                for j in fw.get("jurisdiction", [])
            ],
        }
    except Exception as exc:
        logger.exception("Error fetching regulatory frameworks")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/sector-risk-profiles", summary="20 NACE Sector Climate Risk Profiles")
async def get_sector_risk_profiles_ref() -> Dict[str, Any]:
    """
    Return climate risk parameters for all 20 NACE sectors including:
    - Baseline PD and LGD
    - PD uplift per NGFS scenario
    - LGD multiplier per NGFS scenario
    - Carbon intensity (kg CO2e / kEUR revenue)
    - Stranded asset exposure %
    - Revenue at risk %
    """
    try:
        return {
            "sectors": NACE_SECTOR_RISK_PROFILES,
            "sector_count": len(NACE_SECTOR_RISK_PROFILES),
            "sector_ids": list(NACE_SECTOR_RISK_PROFILES.keys()),
            "highest_carbon_intensity": max(
                NACE_SECTOR_RISK_PROFILES.items(),
                key=lambda x: x[1]["carbon_intensity_kg_keur"],
            )[0],
            "highest_stranded_asset_risk": max(
                NACE_SECTOR_RISK_PROFILES.items(),
                key=lambda x: x[1]["stranded_asset_pct"],
            )[0],
        }
    except Exception as exc:
        logger.exception("Error fetching sector risk profiles")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/transmission-channels", summary="5 Macro-Financial Transmission Channels")
async def get_transmission_channels_ref() -> Dict[str, Any]:
    """
    Return the 5 macro-financial climate risk transmission channels:
    1. Carbon Price Channel (transition → PD)
    2. Asset Stranding Channel (transition → LGD)
    3. Physical Damage Channel (physical → collateral → LGD)
    4. Macro GDP Channel (policy shock → credit cycle)
    5. Transition Technology Channel (green capex → liquidity → PD)
    """
    try:
        return {
            "channels": TRANSMISSION_CHANNELS,
            "channel_count": len(TRANSMISSION_CHANNELS),
            "channel_ids": list(TRANSMISSION_CHANNELS.keys()),
            "primary_risks": list({c["primary_risk"] for c in TRANSMISSION_CHANNELS.values()}),
        }
    except Exception as exc:
        logger.exception("Error fetching transmission channels")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# POST — Computation endpoints
# ---------------------------------------------------------------------------

@router.post("/run", summary="Run Full Multi-Regulatory Climate Stress Test")
async def run_full_stress_test(request: StressTestRequest) -> Dict[str, Any]:
    """
    Execute a comprehensive climate stress test across one or more NGFS Phase IV scenarios
    under a specified regulatory framework.

    **What it computes:**
    - Per-sector PD migration (baseline → stressed) via carbon price + GDP channels
    - Per-sector LGD uplift via stranded-asset + physical-damage channels
    - Portfolio expected credit loss (EL = Exposure × PD × LGD × sector risk weight)
    - CET1/Tier1 depletion (stressed CET1% = baseline% - EL/RWA × 100)
    - Regulatory pass/fail against framework threshold (ECB 4.5% / BoE 4.0% / APRA 7.0% etc.)
    - Submission-ready template with all required disclosure fields

    **Supported frameworks:** ECB_2022 | EBA_2023 | BoE_CBES_2021 | APRA_2022 | MAS_2022 | RBI_2022

    **Supported scenarios:** net_zero_2050 | below_2c | nationally_determined |
    delayed_transition | divergent_net_zero | current_policies | low_demand
    """
    try:
        result = run_stress_test(request)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Stress test run failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/scenario-comparison", summary="Compare All NGFS Phase IV Scenarios Side-by-Side")
async def compare_all_scenarios(request: ScenarioComparisonRequest) -> Dict[str, Any]:
    """
    Run all 7 NGFS Phase IV scenarios simultaneously and return a ranked comparison table.

    Output includes:
    - Per-scenario stressed CET1%, EL, physical/transition risk breakdown
    - Ranked table (worst-to-best CET1 depletion)
    - Orderly vs disorderly average depletion
    - Worst-case and best-case scenario identification

    Useful for board-level risk appetite setting and ICAAP/ORSA climate scenario selection.
    """
    try:
        result = run_scenario_comparison(request)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Scenario comparison failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pd-migration", summary="Single Sector PD Migration Calculation")
async def compute_pd_migration(request: PDMigrationRequest) -> Dict[str, Any]:
    """
    Compute the stressed probability of default (PD) for a single NACE sector under
    a specific NGFS Phase IV scenario at a given time horizon.

    Returns:
    - Baseline PD, PD uplift (pp), carbon channel contribution, physical channel contribution
    - Stressed PD and PD migration ratio
    - Carbon intensity (kg CO2e / kEUR) for the sector
    """
    if request.sector not in NACE_SECTOR_RISK_PROFILES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown sector '{request.sector}'. Valid sectors: {list(NACE_SECTOR_RISK_PROFILES.keys())}",
        )
    if request.scenario_id not in NGFS_PHASE4_SCENARIOS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown scenario '{request.scenario_id}'. Valid scenarios: {list(NGFS_PHASE4_SCENARIOS.keys())}",
        )
    if request.time_horizon_year not in [2025, 2030, 2040, 2050]:
        raise HTTPException(
            status_code=422,
            detail="time_horizon_year must be one of: 2025, 2030, 2040, 2050",
        )
    try:
        result = calculate_pd_migration(
            sector=request.sector,
            scenario_id=request.scenario_id,
            time_horizon_year=request.time_horizon_year,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("PD migration calculation failed")
        raise HTTPException(status_code=500, detail=str(exc))
