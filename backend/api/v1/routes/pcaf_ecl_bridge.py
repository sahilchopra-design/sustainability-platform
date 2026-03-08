"""
PCAF -> ECL Bridge API Routes
===============================
Endpoints that wire PCAF financed emissions into ECL climate overlays.

Provides:
  - POST /api/v1/pcaf-ecl/bridge            — Map investee profiles to ECL inputs
  - POST /api/v1/pcaf-ecl/bridge-portfolio   — Bridge entire portfolio from DB
  - GET  /api/v1/pcaf-ecl/scenario-weights   — Temperature-based scenario weights
  - GET  /api/v1/pcaf-ecl/transition-risk    — WACI to transition risk lookup
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from sqlalchemy.orm import Session
from db.base import get_db

from services.pcaf_ecl_bridge import (
    PCAFInvesteeProfile,
    map_investee_to_ecl_climate,
    bridge_portfolio,
    db_row_to_profile,
    TEMPERATURE_SCENARIO_WEIGHTS,
    WACI_TRANSITION_RISK_MAP,
    DQS_CONFIDENCE_WEIGHTS,
    _waci_to_transition_risk,
    _waci_to_transition_score,
    _carbon_price_sensitivity,
    _temperature_bucket,
)

router = APIRouter(
    prefix="/api/v1/pcaf-ecl",
    tags=["PCAF-ECL Bridge"],
)


# ---------------------------------------------------------------------------
#  Request / Response Models
# ---------------------------------------------------------------------------

class InvesteeProfileRequest(BaseModel):
    investee_name: str
    sector_gics: str = ""
    country_iso: str = ""
    financed_scope1_tco2e: float = 0.0
    financed_scope2_tco2e: float = 0.0
    financed_scope3_tco2e: float = 0.0
    revenue_intensity_tco2e_per_meur: float = 0.0
    outstanding_eur: float = 0.0
    pcaf_dq_composite: float = 3.0
    sbti_committed: bool = False
    net_zero_target_year: Optional[int] = None
    implied_temperature_c: float = 2.5
    attribution_factor: float = 0.0

    # Optional overrides for physical risk
    physical_risk_score: Optional[float] = Field(None, ge=0, le=100)
    collateral_flood_risk: str = "low"
    energy_rating: str = "C"


class SingleBridgeRequest(BaseModel):
    """Map a single investee to ECL climate inputs."""
    profile: InvesteeProfileRequest


class PortfolioBridgeRequest(BaseModel):
    """Map multiple investees to ECL climate inputs."""
    profiles: list[InvesteeProfileRequest]
    portfolio_temperature_c: float = Field(2.5, ge=0.5, le=6.0)
    physical_risk_overrides: Optional[dict[str, float]] = None


class DBPortfolioBridgeRequest(BaseModel):
    """Bridge a portfolio from PCAF DB tables."""
    portfolio_id: str
    portfolio_temperature_c: Optional[float] = None  # Auto-calculate if None


# ---------------------------------------------------------------------------
#  Endpoints
# ---------------------------------------------------------------------------

@router.post("/bridge")
def bridge_single_investee(req: SingleBridgeRequest):
    """Map a single PCAF investee profile to ECL climate risk inputs."""
    p = req.profile
    profile = PCAFInvesteeProfile(
        investee_name=p.investee_name,
        sector_gics=p.sector_gics,
        country_iso=p.country_iso,
        financed_scope1_tco2e=p.financed_scope1_tco2e,
        financed_scope2_tco2e=p.financed_scope2_tco2e,
        financed_scope3_tco2e=p.financed_scope3_tco2e,
        revenue_intensity_tco2e_per_meur=p.revenue_intensity_tco2e_per_meur,
        outstanding_eur=p.outstanding_eur,
        pcaf_dq_composite=p.pcaf_dq_composite,
        sbti_committed=p.sbti_committed,
        net_zero_target_year=p.net_zero_target_year,
        implied_temperature_c=p.implied_temperature_c,
        attribution_factor=p.attribution_factor,
    )

    from dataclasses import asdict
    climate_inputs = map_investee_to_ecl_climate(
        profile,
        physical_risk_override=p.physical_risk_score,
        collateral_flood_risk=p.collateral_flood_risk,
        energy_rating=p.energy_rating,
    )

    return {
        "investee_name": p.investee_name,
        "climate_inputs": asdict(climate_inputs),
        "mapping_summary": {
            "waci_input": p.revenue_intensity_tco2e_per_meur,
            "transition_risk_level": climate_inputs.sector_transition_risk,
            "transition_risk_score": climate_inputs.transition_risk_score,
            "carbon_price_sensitivity": climate_inputs.carbon_price_sensitivity,
            "sbti_discount_applied": climate_inputs.sbti_aligned,
            "net_zero_discount_applied": climate_inputs.net_zero_committed,
            "pcaf_confidence": climate_inputs.pcaf_confidence,
            "temperature_bucket": _temperature_bucket(p.implied_temperature_c),
        },
    }


@router.post("/bridge-portfolio")
def bridge_portfolio_endpoint(req: PortfolioBridgeRequest):
    """
    Map an entire portfolio of PCAF investees to ECL climate inputs.
    Returns per-investee ECL inputs + portfolio-level scenario weights.
    """
    profiles = []
    for p in req.profiles:
        profiles.append(PCAFInvesteeProfile(
            investee_name=p.investee_name,
            sector_gics=p.sector_gics,
            country_iso=p.country_iso,
            financed_scope1_tco2e=p.financed_scope1_tco2e,
            financed_scope2_tco2e=p.financed_scope2_tco2e,
            financed_scope3_tco2e=p.financed_scope3_tco2e,
            revenue_intensity_tco2e_per_meur=p.revenue_intensity_tco2e_per_meur,
            outstanding_eur=p.outstanding_eur,
            pcaf_dq_composite=p.pcaf_dq_composite,
            sbti_committed=p.sbti_committed,
            net_zero_target_year=p.net_zero_target_year,
            implied_temperature_c=p.implied_temperature_c,
            attribution_factor=p.attribution_factor,
        ))

    from dataclasses import asdict
    result = bridge_portfolio(
        profiles,
        portfolio_temperature_c=req.portfolio_temperature_c,
        physical_risk_overrides=req.physical_risk_overrides,
    )

    return asdict(result)


@router.post("/bridge-from-db")
def bridge_from_db(req: DBPortfolioBridgeRequest, db: Session = Depends(get_db)):
    """
    Bridge a portfolio by reading PCAF investee data from the database.
    Requires portfolio_id that matches pcaf_portfolios.id.
    """
    from sqlalchemy import text

    # Fetch investees
    rows = db.execute(
        text("""
            SELECT investee_name, sector_gics, country_iso,
                   outstanding_investment, enterprise_value, revenue,
                   attribution_factor,
                   scope1_tco2e, scope2_tco2e, scope3_tco2e,
                   financed_scope1_tco2e, financed_scope2_tco2e, financed_scope3_tco2e,
                   revenue_intensity_tco2e_per_mrevenue,
                   pcaf_dq_scope1, pcaf_dq_scope2,
                   sbti_committed, implied_temperature_c
            FROM pcaf_investees
            WHERE portfolio_id = :pid
        """),
        {"pid": req.portfolio_id},
    ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No PCAF investees found for portfolio {req.portfolio_id}",
        )

    profiles = [db_row_to_profile(dict(r)) for r in rows]

    # Portfolio temperature: use provided or fetch from pcaf_portfolios
    temp_c = req.portfolio_temperature_c
    if temp_c is None:
        port_row = db.execute(
            text("SELECT portfolio_temperature_c FROM pcaf_portfolios WHERE id = :pid"),
            {"pid": req.portfolio_id},
        ).mappings().first()
        temp_c = float(port_row["portfolio_temperature_c"]) if port_row and port_row.get("portfolio_temperature_c") else 2.5

    from dataclasses import asdict
    result = bridge_portfolio(profiles, portfolio_temperature_c=temp_c)
    return asdict(result)


@router.get("/scenario-weights")
def get_scenario_weights(temperature_c: float = 2.5):
    """
    Get NGFS scenario probability weights for a given portfolio temperature.
    Higher temperature = more weight on adverse/severe scenarios.
    """
    bucket = _temperature_bucket(temperature_c)
    weights_tuple = TEMPERATURE_SCENARIO_WEIGHTS.get(bucket, (0.20, 0.45, 0.25, 0.10))

    return {
        "temperature_c": temperature_c,
        "temperature_bucket": bucket,
        "scenario_weights": {
            "OPTIMISTIC": weights_tuple[0],
            "BASE": weights_tuple[1],
            "ADVERSE": weights_tuple[2],
            "SEVERE": weights_tuple[3],
        },
        "all_buckets": {
            k: {
                "OPTIMISTIC": v[0],
                "BASE": v[1],
                "ADVERSE": v[2],
                "SEVERE": v[3],
            }
            for k, v in TEMPERATURE_SCENARIO_WEIGHTS.items()
        },
    }


@router.get("/transition-risk")
def get_transition_risk(waci: float = 200.0, sector_gics: str = ""):
    """
    Look up transition risk level and score from WACI intensity.
    """
    return {
        "waci_tco2e_per_meur": waci,
        "sector_gics": sector_gics,
        "transition_risk_level": _waci_to_transition_risk(waci),
        "transition_risk_score": _waci_to_transition_score(waci),
        "carbon_price_sensitivity": _carbon_price_sensitivity(waci, sector_gics),
        "risk_thresholds": [
            {"max_waci": t, "level": l}
            for t, l in WACI_TRANSITION_RISK_MAP
            if t < float("inf")
        ],
    }


@router.get("/dqs-confidence")
def get_dqs_confidence():
    """
    Return the PCAF DQS -> confidence weight mapping.
    Shows how data quality affects the strength of climate overlays.
    """
    return {
        "description": "PCAF Data Quality Score to ECL overlay confidence weight",
        "methodology": "Higher DQS = lower data quality = less confidence in transition risk scoring",
        "weights": {
            f"DQS_{k}": {"weight": v, "label": label}
            for k, v, label in [
                (1, 1.00, "Verified data (audited emissions)"),
                (2, 0.90, "Reported data (company disclosures)"),
                (3, 0.70, "Physical activity data (production-based)"),
                (4, 0.50, "Estimated data (sector averages)"),
                (5, 0.30, "Estimated data (revenue proxy)"),
            ]
        },
    }
