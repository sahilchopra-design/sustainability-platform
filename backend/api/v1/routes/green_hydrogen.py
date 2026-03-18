"""
Green Hydrogen & RFNBO Compliance Routes  —  E98
=================================================
Prefix: /api/v1/green-hydrogen
Tags:   Green Hydrogen — E98

Standards:
  - EU Delegated Regulation (EU) 2023/1184 (RFNBO GHG methodology)
  - EU Delegated Regulation (EU) 2023/1185 (RFNBO additionality + correlations)
  - ISO 14040/14044 (LCA GHG intensity)
  - REPowerEU Plan COM(2022) 230 + EU Hydrogen Strategy COM(2020) 301
  - IEA Global Hydrogen Review 2023 (LCOH)
  - EU H2 Bank / H2 CfD framework
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.green_hydrogen_engine import (
    assess_green_hydrogen,
    calculate_rfnbo_compliance,
    calculate_lcoh,
    get_h2_benchmarks,
    RFNBO_CRITERIA,
    ELECTROLYSER_BENCHMARKS,
    COUNTRY_GRID_FACTORS,
    REPOWEREU_TARGETS,
    H2_CFD_FRAMEWORK,
)

router = APIRouter(prefix="/api/v1/green-hydrogen", tags=["Green Hydrogen — E98"])


# ── Pydantic Request Models ────────────────────────────────────────────────────

class FacilityAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    facility_name: str = Field(..., description="Name of the hydrogen production facility")
    country: str = Field(..., description="Country of facility location (e.g. 'Germany')")
    production_capacity_mw: float = Field(..., gt=0, description="Electrolyser capacity (MW electrical)")
    electrolyser_type: str = Field("PEM", description="Electrolyser type: PEM / ALK / SOEC / AEM")
    electricity_source: str = Field("wind_onshore", description="e.g. wind_onshore, solar_pv, grid, ppa")
    commissioning_year: int = Field(2024, ge=2020, le=2050)
    re_installation_year: int | None = Field(None, description="Year RE asset was commissioned (for ≤36-month rule)")
    has_ppa: bool = Field(False, description="Is electricity sourced via a PPA?")
    ppa_dedicated_new_asset: bool = Field(False, description="Is PPA linked to a dedicated new RE asset?")
    accounting_year: int = Field(2025, ge=2023, le=2040, description="Accounting year for temporal correlation")
    matching_granularity: str = Field("monthly", description="GO matching: hourly / monthly / annual")
    re_location_country: str | None = Field(None, description="Country of RE asset (if different from facility)")
    same_bidding_zone: bool = Field(True)
    adjacent_zone_congestion_free_pct: float | None = Field(None, ge=0, le=100)
    capex_usd_kw: float | None = Field(None, gt=0, description="Override CAPEX (USD/kW). Defaults to IEA mid estimate.")
    capacity_factor: float = Field(0.45, gt=0, le=1.0)
    discount_rate: float = Field(0.08, gt=0, le=0.30)
    lifetime_yr: int = Field(20, ge=5, le=40)
    electricity_price_usd_mwh: float | None = Field(None, gt=0, description="Override electricity price (USD/MWh)")
    certifications: list[str] | None = Field(None, description="Certifications held: REGreen, TÜV SÜD, DNV, etc.")
    projection_year: int = Field(2024, ge=2024, le=2050, description="Year for IEA CAPEX trajectory")


class RfnboComplianceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    electricity_source: str = Field(..., description="e.g. wind_onshore, solar_pv, grid, ppa")
    country: str = Field(..., description="Facility country")
    electrolyser_type: str = Field("PEM", description="PEM / ALK / SOEC / AEM")
    commissioning_year: int = Field(2024, ge=2020, le=2050)
    re_installation_year: int | None = Field(None, description="RE asset commissioning year")
    has_ppa: bool = Field(False)
    ppa_dedicated_new_asset: bool = Field(False)
    accounting_year: int = Field(2025, ge=2023, le=2040)
    matching_granularity: str = Field("monthly", description="hourly / monthly / annual")
    re_location_country: str | None = Field(None)
    same_bidding_zone: bool = Field(True)
    adjacent_zone_congestion_free_pct: float | None = Field(None, ge=0, le=100)
    include_compression: bool = Field(True)
    include_water_treatment: bool = Field(True)


class LcohRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    electrolyser_type: str = Field("PEM", description="PEM / ALK / SOEC / AEM")
    country: str = Field("Germany")
    capacity_mw: float = Field(..., gt=0, description="Electrolyser capacity (MW)")
    capex_usd_kw: float | None = Field(None, gt=0)
    capacity_factor: float = Field(0.45, gt=0, le=1.0)
    discount_rate: float = Field(0.08, gt=0, le=0.30)
    lifetime_yr: int = Field(20, ge=5, le=40)
    electricity_price_usd_mwh: float | None = Field(None, gt=0)
    opex_pct_capex: float | None = Field(None, gt=0, le=0.20)
    projection_year: int = Field(2024, ge=2024, le=2050)


# ── POST Routes ───────────────────────────────────────────────────────────────

@router.post("/assess", summary="Full green hydrogen facility assessment")
async def assess_facility(req: FacilityAssessmentRequest) -> dict[str, Any]:
    """
    Comprehensive facility assessment combining:
    - RFNBO compliance (all 4 EU criteria)
    - GHG intensity (ISO 14040/14044)
    - LCOH economics (IEA methodology)
    - H2 CfD eligibility + indicative support (EUR/kgH2)
    - Certification gap analysis
    - REPowerEU country context
    """
    try:
        return assess_green_hydrogen(
            facility_name=req.facility_name,
            country=req.country,
            production_capacity_mw=req.production_capacity_mw,
            electrolyser_type=req.electrolyser_type,
            electricity_source=req.electricity_source,
            commissioning_year=req.commissioning_year,
            re_installation_year=req.re_installation_year,
            has_ppa=req.has_ppa,
            ppa_dedicated_new_asset=req.ppa_dedicated_new_asset,
            accounting_year=req.accounting_year,
            matching_granularity=req.matching_granularity,
            re_location_country=req.re_location_country,
            same_bidding_zone=req.same_bidding_zone,
            adjacent_zone_congestion_free_pct=req.adjacent_zone_congestion_free_pct,
            capex_usd_kw=req.capex_usd_kw,
            capacity_factor=req.capacity_factor,
            discount_rate=req.discount_rate,
            lifetime_yr=req.lifetime_yr,
            electricity_price_usd_mwh=req.electricity_price_usd_mwh,
            certifications=req.certifications,
            projection_year=req.projection_year,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/rfnbo-compliance", summary="RFNBO 4-criteria compliance check")
async def rfnbo_compliance(req: RfnboComplianceRequest) -> dict[str, Any]:
    """
    Check all 4 RFNBO criteria per EU Delegated Regulations 2023/1184 + 2023/1185:
    - C1: GHG intensity < 3.38 kgCO2eq/kgH2 (lifecycle)
    - C2: Additionality of renewable electricity (3 routes)
    - C3: Temporal correlation — monthly (pre-2030) / hourly (2030+)
    - C4: Geographical correlation — same or adjacent bidding zone
    """
    try:
        return calculate_rfnbo_compliance(
            electricity_source=req.electricity_source,
            country=req.country,
            electrolyser_type=req.electrolyser_type,
            commissioning_year=req.commissioning_year,
            re_installation_year=req.re_installation_year,
            has_ppa=req.has_ppa,
            ppa_dedicated_new_asset=req.ppa_dedicated_new_asset,
            accounting_year=req.accounting_year,
            matching_granularity=req.matching_granularity,
            re_location_country=req.re_location_country,
            same_bidding_zone=req.same_bidding_zone,
            adjacent_zone_congestion_free_pct=req.adjacent_zone_congestion_free_pct,
            include_compression=req.include_compression,
            include_water_treatment=req.include_water_treatment,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/lcoh", summary="Levelised Cost of Hydrogen calculation")
async def lcoh_calculation(req: LcohRequest) -> dict[str, Any]:
    """
    Calculate LCOH (USD/kgH2) per IEA Global Hydrogen Review 2023 methodology.

    Components: CAPEX (via CRF) + OPEX + stack replacement + electricity cost.
    Outputs include IEA trajectory benchmarks and H2 CfD eligibility flag.
    """
    try:
        return calculate_lcoh(
            electrolyser_type=req.electrolyser_type,
            country=req.country,
            capacity_mw=req.capacity_mw,
            capex_usd_kw=req.capex_usd_kw,
            capacity_factor=req.capacity_factor,
            discount_rate=req.discount_rate,
            lifetime_yr=req.lifetime_yr,
            electricity_price_usd_mwh=req.electricity_price_usd_mwh,
            opex_pct_capex=req.opex_pct_capex,
            projection_year=req.projection_year,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ── GET Reference Routes ──────────────────────────────────────────────────────

@router.get("/ref/rfnbo-criteria", summary="RFNBO 4-criteria full descriptions")
async def ref_rfnbo_criteria() -> dict[str, Any]:
    """Return full legal descriptions and parameters for the 4 RFNBO criteria per EU 2023/1184+1185."""
    return {
        "source": "EU Delegated Regulations (EU) 2023/1184 and 2023/1185",
        "effective_date": "2023-06-20",
        "criteria": RFNBO_CRITERIA,
        "rfnbo_definition": (
            "Renewable Fuels of Non-Biological Origin: fuels whose energy content comes from "
            "renewable sources other than biomass (EU Renewable Energy Directive Art 2(36))."
        ),
        "green_hydrogen_classification": "Hydrogen produced by electrolysis using electricity meeting all 4 RFNBO criteria",
        "ghg_threshold_kg_co2_kgh2": 3.38,
        "counterfactual_method": (
            "GHG intensity calculated using marginal/counterfactual electricity method: "
            "emission factor of electricity actually consumed, not average grid factor."
        ),
    }


@router.get("/ref/electrolyser-benchmarks", summary="Electrolyser benchmarks — 4 types")
async def ref_electrolyser_benchmarks() -> dict[str, Any]:
    """
    Return benchmarks for PEM, ALK, SOEC, and AEM electrolysers including:
    CAPEX (2024/2030/2050), electricity consumption, efficiency, stack lifetime, ramp rate.
    """
    return {
        "source": "IEA Global Hydrogen Review 2023; IRENA Green Hydrogen Cost Reduction 2020",
        "benchmarks": ELECTROLYSER_BENCHMARKS,
        "notes": {
            "capex_currency": "USD/kW (system-level, excluding BOP)",
            "efficiency_basis": "LHV (Lower Heating Value)",
            "electricity_consumption": "kWh per kg H2 produced (at nameplate efficiency)",
            "stack_lifetime": "Operating hours before replacement required",
        },
    }


@router.get("/ref/country-grid-factors", summary="Country grid emission factors + RE share")
async def ref_country_grid_factors() -> dict[str, Any]:
    """
    Return grid emission factors (kgCO2eq/kWh), renewable energy share (%), bidding zones,
    and current/pipeline green H2 capacity for 20 countries.
    """
    return {
        "source": "ENTSO-E Transparency Platform 2023; IEA Electricity Market Report 2023",
        "countries": COUNTRY_GRID_FACTORS,
        "high_re_threshold_pct": 90.0,
        "high_re_eligible_countries": [
            c for c, d in COUNTRY_GRID_FACTORS.items()
            if d["re_share_pct"] >= 90.0
        ],
        "methodology": "Annual average emission factor; residual mix factors not applied",
        "note": "RE share >90% satisfies RFNBO additionality route (b) per 2023/1185 Art 4(1)(b)",
    }


@router.get("/ref/repowereu-targets", summary="REPowerEU national H2 targets")
async def ref_repowereu_targets() -> dict[str, Any]:
    """
    Return national hydrogen production targets under REPowerEU (COM(2022) 230):
    10 Mt domestic production + 10 Mt imports by 2030, with country-level breakdown.
    """
    return {
        "source": "REPowerEU Plan COM(2022) 230 final; EU Hydrogen Strategy COM(2020) 301 final",
        "targets": REPOWEREU_TARGETS,
        "repowereu_total_eu_target_mt_2030": 10.0,
        "eu_import_target_mt_2030": 10.0,
        "electrolysis_capacity_target_gw_2030": 40.0,
        "2024_installed_gw_estimate": 0.5,
        "gap_commentary": (
            "As of 2024, installed green H2 capacity is ~0.5 GW vs 40 GW target. "
            "Acceleration requires significant policy support, H2 CfD auctions, and infrastructure investment."
        ),
    }


@router.get("/ref/h2cfd-framework", summary="H2 Contract for Difference eligibility & mechanics")
async def ref_h2cfd_framework() -> dict[str, Any]:
    """
    Return H2 CfD framework details: EU H2 Bank auction mechanics, German H2Global model,
    eligibility criteria, certification recognition, and support parameters.
    """
    return {
        "source": "EU Innovation Fund H2 Bank Pilot Auction 2023; German AusH2 Regulation",
        "framework": H2_CFD_FRAMEWORK,
        "key_parameters": {
            "mechanism": "Strike price minus reference price; net support = max(strike - market, 0)",
            "reference_price_basis": "Natural gas parity (weekly TTF spot price equivalent)",
            "natural_gas_parity_eur_kgH2": H2_CFD_FRAMEWORK["auction_parameters"]["natural_gas_parity_eur_kgH2"],
            "support_duration_yr": f"{H2_CFD_FRAMEWORK['auction_parameters']['support_duration_yr_min']}–{H2_CFD_FRAMEWORK['auction_parameters']['support_duration_yr_max']}",
            "pilot_auction_budget_EUR_mn": H2_CFD_FRAMEWORK["auction_parameters"]["pilot_auction_budget_EUR"] / 1e6,
        },
        "eligibility_summary": [
            "RFNBO certified (all 4 criteria)",
            "Domestic EU production",
            "Minimum 5 MW electrolyser capacity",
            "Recognised certification body (REGreen / TÜV SÜD / DNV / Bureau Veritas)",
            "Commissioning by 2030",
        ],
    }
