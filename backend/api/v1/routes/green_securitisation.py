"""
API Routes: Green Securitisation & ESG Structured Finance Engine — E81
=======================================================================
POST /api/v1/green-securitisation/eu-gbs-compliance       — EU GBS Art 19 compliance
POST /api/v1/green-securitisation/climate-var-passthrough — Climate VaR for asset pool
POST /api/v1/green-securitisation/rmbs-epc-analysis       — RMBS EPC distribution + CRREM
POST /api/v1/green-securitisation/covered-bond-esv        — ECBC label + ESV scoring
POST /api/v1/green-securitisation/green-tranche-design    — Tranche structure optimisation
POST /api/v1/green-securitisation/full-assessment         — Complete green securitisation assessment
GET  /api/v1/green-securitisation/ref/structure-types     — Supported deal structures
GET  /api/v1/green-securitisation/ref/eu-gbs-requirements — Art 19 requirements checklist
GET  /api/v1/green-securitisation/ref/greenium-benchmarks — Greenium by deal type and rating
GET  /api/v1/green-securitisation/ref/climate-risk-profiles — Sector climate risk profiles

References:
  - Regulation (EU) 2023/2631 — EU Green Bond Standard
  - EU Covered Bond Directive 2019/2162 + ECBC Label Convention 2023
  - CRREM v2.0 (2023) — Carbon Risk Real Estate Monitor
  - NGFS Climate Scenarios v4.0 (Sep 2023)
  - EU STS Securitisation Regulation (EU) 2017/2402
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.green_securitisation_engine import GreenSecuritisationEngine

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/green-securitisation",
    tags=["Green Securitisation (E81)"],
)

engine = GreenSecuritisationEngine()


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------

class EUGBSComplianceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    deal_name: str
    total_issuance_m: float = Field(default=500.0, ge=0)
    structure_type: str = "ABS"
    taxonomy_alignment_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    has_framework: bool = False
    has_external_review: bool = False
    dnsh_evidence: bool = False
    min_safeguards_evidence: bool = False
    has_allocation_report: bool = False
    has_impact_report: bool = False
    esap_registered: bool = False
    external_reviewer_esma_registered: Optional[bool] = False


class PoolAssetItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    asset_type: str = "residential_mortgage"
    balance_m: float = Field(default=0.0, ge=0)
    base_pd: float = Field(default=0.02, ge=0.0, le=1.0)
    base_lgd: float = Field(default=0.35, ge=0.0, le=1.0)
    country: Optional[str] = None
    vintage_year: Optional[int] = None


class ClimateVaRPassthroughRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    deal_name: str
    pool_assets: List[PoolAssetItem] = Field(default_factory=list)
    ngfs_scenario: str = Field(
        default="below_2c",
        description="One of: net_zero_2050, below_2c, delayed_transition, current_policies",
    )
    time_horizon_years: int = Field(default=10, ge=1, le=30)


class RMBSEPCRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    deal_name: str
    mortgage_count: int = Field(default=1000, ge=1)
    total_balance_m: float = Field(default=500.0, ge=0)
    epc_distribution: Dict[str, float] = Field(
        default_factory=dict,
        description="EPC band A-G → percentage of pool (should sum to 100)",
    )
    country_code: str = Field(default="DE", description="ISO-2 country code")
    vintage_year: int = Field(default=2020)


class KPIItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    name: str
    unit: Optional[str] = None
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    target_year: Optional[int] = None
    has_baseline: bool = False
    has_target: bool = False
    third_party_verified: bool = False


class CoveredBondESVRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    bond_name: str
    issuer_type: str = Field(default="mortgage_bank",
                              description="e.g. mortgage_bank, savings_bank, commercial_bank")
    cover_pool_size_m: float = Field(default=1000.0, ge=0)
    ecbc_label_applied: bool = False
    kpis: List[KPIItem] = Field(default_factory=list)
    oc_level_pct: float = Field(default=10.0, ge=0)
    liquidity_buffer_days: int = Field(default=180, ge=0)
    dual_recourse_structure: bool = False
    cover_pool_high_quality: bool = False
    national_competent_authority_supervised: bool = False
    quarterly_investor_report: bool = False
    green_use_of_proceeds: bool = False
    esg_pool_disclosure_published: bool = False


class GreenPoolData(BaseModel):
    model_config = {"protected_namespaces": ()}

    deal_name: str = ""
    pool_size_m: float = Field(default=500.0, ge=0)
    structure_type: str = "ABS"
    sts_eligible: bool = True
    green_label: str = Field(default="EU_GBS", description="EU_GBS or ICMA_GBP")
    avg_loan_balance: float = Field(default=200000.0, ge=0)


class GreenTrancheDesignRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    deal_name: str
    pool_data: GreenPoolData = Field(default_factory=GreenPoolData)
    target_rating: str = Field(default="AAA", description="Target rating for senior/labelled tranche")
    green_target_pct: float = Field(default=80.0, ge=0.0, le=100.0)
    structure_type: str = "ABS"


class MortgagePoolData(BaseModel):
    model_config = {"protected_namespaces": ()}

    mortgage_count: int = Field(default=1000, ge=1)
    total_balance_m: float = Field(default=500.0, ge=0)
    epc_distribution: Dict[str, float] = Field(default_factory=dict)
    country_code: str = "DE"
    vintage_year: int = 2020


class CoveredBondSubData(BaseModel):
    model_config = {"protected_namespaces": ()}

    oc_level_pct: float = Field(default=10.0, ge=0)
    liquidity_buffer_days: int = Field(default=180, ge=0)
    dual_recourse_structure: bool = False
    cover_pool_high_quality: bool = False
    national_competent_authority_supervised: bool = False
    quarterly_investor_report: bool = False
    green_use_of_proceeds: bool = False
    esg_pool_disclosure_published: bool = False
    issuer_type: str = "mortgage_bank"


class SecuritisationFullAssessmentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    entity_id: str
    deal_name: str
    total_issuance_m: float = Field(default=500.0, ge=0)
    structure_type: str = "ABS"
    # EU GBS
    taxonomy_alignment_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    has_framework: bool = False
    has_external_review: bool = False
    dnsh_evidence: bool = False
    min_safeguards_evidence: bool = False
    has_allocation_report: bool = False
    has_impact_report: bool = False
    esap_registered: bool = False
    # Pool
    pool_assets: List[PoolAssetItem] = Field(default_factory=list)
    ngfs_scenario: str = "below_2c"
    time_horizon_years: int = Field(default=10, ge=1, le=30)
    # RMBS/CMBS
    mortgage_pool: Optional[MortgagePoolData] = None
    # Covered Bond
    covered_bond_data: Optional[CoveredBondSubData] = None
    # Tranche design
    pool_data: Optional[GreenPoolData] = None
    target_rating: str = "AAA"
    green_target_pct: float = Field(default=80.0, ge=0.0, le=100.0)


# ---------------------------------------------------------------------------
# POST Endpoints
# ---------------------------------------------------------------------------

@router.post("/eu-gbs-compliance", summary="EU GBS Art 19 Compliance Assessment")
def eu_gbs_compliance(req: EUGBSComplianceRequest):
    """
    Assess deal compliance with EU Green Bond Standard Regulation (EU) 2023/2631.

    Checks 4 Art 19 requirements:
      1. Taxonomy alignment (Art 4 + EU Taxonomy) — 40% weight
      2. Green Bond Framework publication (Art 6) — 25% weight
      3. Allocation and impact reporting (Art 9-11) — 20% weight
      4. External review by ESMA-registered reviewer (Art 14-20) — 15% weight

    Returns GBS score (0-100), EU GBS compliant flag, and gap list.
    """
    try:
        deal_data = req.model_dump()
        result = engine.assess_eu_gbs_compliance(deal_data)
        return {"status": "ok", "eu_gbs_assessment": result}
    except Exception as exc:
        logger.exception("eu_gbs_compliance failed deal=%s", req.deal_name)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/climate-var-passthrough", summary="Climate VaR for Asset Pool (NGFS)")
def climate_var_passthrough(req: ClimateVaRPassthroughRequest):
    """
    Compute climate VaR passthrough from pool assets to securitisation tranches.

    Uses NGFS Climate Scenarios v4.0 (net_zero_2050 / below_2c / delayed_transition / current_policies).
    Returns physical VaR, transition VaR, climate-adjusted weighted PD/LGD,
    pool expected climate loss, and credit enhancement uplift recommendation.
    """
    try:
        pool_assets = [a.model_dump() for a in req.pool_assets]
        result = engine.compute_climate_var_passthrough(
            pool_assets=pool_assets,
            ngfs_scenario=req.ngfs_scenario,
            time_horizon_years=req.time_horizon_years,
        )
        return {"status": "ok", "deal_name": req.deal_name, "climate_var_result": result}
    except Exception as exc:
        logger.exception("climate_var_passthrough failed deal=%s", req.deal_name)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/rmbs-epc-analysis", summary="RMBS EPC Distribution + CRREM Alignment")
def rmbs_epc_analysis(req: RMBSEPCRequest):
    """
    Assess RMBS pool energy performance certificate (EPC) distribution and CRREM alignment.

    Returns:
      - EPC A/B percentage and EPC E/F/G stranded asset risk %
      - CRREM alignment % (1.5°C pathway proxy)
      - Weighted energy intensity (kWh/m²/yr) vs Eurostat 2022 benchmark
      - Country-level physical hazard scores (flood, heat)
      - EU Taxonomy eligible balance (EPC A = taxonomy-aligned per Art 7 climate mitigation)

    References: CRREM v2.0 (2023) + EU Taxonomy Delegated Act (EU) 2021/4987.
    """
    try:
        pool_data = req.model_dump()
        result = engine.assess_rmbs_epc(pool_data)
        return {"status": "ok", "rmbs_epc_assessment": result}
    except Exception as exc:
        logger.exception("rmbs_epc_analysis failed deal=%s", req.deal_name)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/covered-bond-esv", summary="ECBC Covered Bond Label + ESV Scoring")
def covered_bond_esv(req: CoveredBondESVRequest):
    """
    Assess covered bond against ECBC Covered Bond Label requirements and ESV score.

    Checks all 8 ECBC Label criteria including mandatory (dual recourse, cover pool quality,
    OC ≥5%, 180-day liquidity buffer, NCA supervision, quarterly reporting) and optional
    (green use of proceeds, ESG pool disclosure).

    ESV score (0-100) rewards green pool quality, KPI alignment, and ESG transparency.
    References: EU CBD 2019/2162 + ECBC Label Convention 2023.
    """
    try:
        bond_data = req.model_dump()
        result = engine.assess_covered_bond_esv(bond_data)
        return {"status": "ok", "covered_bond_esv_assessment": result}
    except Exception as exc:
        logger.exception("covered_bond_esv failed bond=%s", req.bond_name)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/green-tranche-design", summary="Green Tranche Structure Optimisation")
def green_tranche_design(req: GreenTrancheDesignRequest):
    """
    Design green tranche structure with subordination levels and greenium estimate.

    Returns full tranche waterfall (AAA senior through equity piece) with:
      - Tranche sizes as % of pool
      - OC and CE requirements per TRANCHE_SUBORDINATION_STANDARDS
      - Greenium estimate in bps (EU GBS vs ICMA GBP benchmarks)
      - ESRS SPV disclosure obligations
      - STS Regulation (EU) 2017/2402 retention requirement flag

    Greenium source: BIS Working Paper 1015 (2023); Bloomberg BNEF Green Bond Premium Tracker.
    """
    try:
        pool_data_dict = req.pool_data.model_dump() if req.pool_data else {}
        pool_data_dict["deal_name"] = req.deal_name
        result = engine.design_green_tranche_structure(
            pool_data=pool_data_dict,
            target_rating=req.target_rating,
            green_target_pct=req.green_target_pct,
        )
        return {"status": "ok", "tranche_design": result}
    except Exception as exc:
        logger.exception("green_tranche_design failed deal=%s", req.deal_name)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/full-assessment", summary="Complete Green Securitisation Assessment")
def full_assessment(req: SecuritisationFullAssessmentRequest):
    """
    Run the complete Green Securitisation assessment orchestrating all 5 sub-modules.

    Score weights: EU GBS 35% + Climate VaR 25% + EPC/RMBS 20% + Covered Bond ESV 10% + Tranche 10%

    Deal tiers:
      Dark Green (≥80) — full EU GBS + taxonomy aligned + verified
      Green (65-79)     — partial EU GBS + credible green use of proceeds
      Light Green (50-64) — ESG labelled but gaps in taxonomy alignment or disclosure
      Amber (35-49)    — some ESG features but material non-compliance risks
      Red (<35)        — no credible green credentials; greenwashing risk
    """
    try:
        deal_data = req.model_dump()
        deal_data["pool_assets"] = [a.model_dump() for a in req.pool_assets]
        if req.mortgage_pool:
            deal_data["mortgage_pool"] = req.mortgage_pool.model_dump()
        if req.covered_bond_data:
            deal_data["covered_bond_data"] = req.covered_bond_data.model_dump()
        if req.pool_data:
            deal_data["pool_data"] = req.pool_data.model_dump()
            deal_data["pool_data"]["deal_name"] = req.deal_name

        result = engine.run_full_assessment(
            entity_id=req.entity_id,
            deal_data=deal_data,
        )
        return {"status": "ok", "green_securitisation_assessment": result}
    except Exception as exc:
        logger.exception("full_assessment failed entity=%s deal=%s", req.entity_id, req.deal_name)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET Reference Endpoints
# ---------------------------------------------------------------------------

@router.get("/ref/structure-types", summary="Supported Securitisation Deal Structures")
def ref_structure_types():
    """
    Return all supported securitisation deal structure types.

    Includes: ABS, RMBS, CMBS, CLO, CDO, COVERED_BOND, GREEN_ABS, SOCIAL_ABS,
    SUSTAINABILITY_LINKED_ABS. For each structure: EU GBS eligibility, typical
    maturity range, rating range, and SRT eligibility.
    """
    try:
        return {"status": "ok", "structure_types": engine.ref_structure_types()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/eu-gbs-requirements", summary="EU GBS Art 19 Requirements Checklist")
def ref_eu_gbs_requirements():
    """
    Return the 4 EU GBS Art 19 core requirement definitions with weights.

    Requirements: taxonomy alignment, green bond framework, reporting, external review.
    Includes sub-requirements, article references, and scoring weights.
    Source: Regulation (EU) 2023/2631 Official Journal.
    """
    try:
        return {
            "status": "ok",
            "eu_gbs_requirements": engine.ref_eu_gbs_requirements(),
            "regulation": "Regulation (EU) 2023/2631",
            "entry_into_force": "2024-12-21",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/greenium-benchmarks", summary="Greenium Benchmarks by Deal Type and Rating")
def ref_greenium_benchmarks():
    """
    Return greenium benchmarks (bps over vanilla equivalent) by deal type and credit rating.

    Covers: EU GBS compliant, ICMA GBP green bond, social bond, sustainability-linked,
    green covered bond, green RMBS.
    Sources: BIS Working Paper 1015 (2023); Bloomberg BNEF; ICMA market surveys.
    """
    try:
        return {
            "status": "ok",
            "greenium_benchmarks": engine.ref_greenium_benchmarks(),
            "unit": "basis points (bps) over vanilla equivalent bond",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/climate-risk-profiles", summary="Sector Climate Risk Profiles")
def ref_climate_risk_profiles():
    """
    Return physical and transition risk sensitivity profiles for 8 asset types.

    Includes: residential_mortgage, commercial_real_estate, auto_loans, solar_equipment,
    energy_efficiency_loans, corporate_loans_energy, corporate_loans_industrials, consumer_loans.

    Negative transition risk sensitivity indicates climate-beneficial assets (e.g. solar).
    Sources: NGFS v4.0; ECB climate stress test 2022; EBA ESG Pillar 3 GL/2022/03.
    """
    try:
        return {
            "status": "ok",
            "climate_risk_profiles": engine.ref_climate_risk_profiles(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/tranche-standards", summary="Tranche Subordination Standards")
def ref_tranche_standards():
    """
    Return standard tranche subordination levels (OC and CE) by rating target.

    Covers: AAA senior, AA/A/BBB mezzanine, BB junior, equity first-loss.
    Source: ESMA securitisation market data; Basel III CRR3 capital treatment.
    """
    try:
        return {
            "status": "ok",
            "tranche_subordination_standards": engine.ref_tranche_standards(),
            "retention_requirement": "5% minimum per Art 6 Reg (EU) 2017/2402 (STS)",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ref/ngfs-scenarios", summary="NGFS Climate Scenario Parameters")
def ref_ngfs_scenarios():
    """
    Return NGFS Climate Scenario v4.0 parameters used in climate VaR calculations.

    Scenarios: net_zero_2050, below_2c, delayed_transition, current_policies.
    Includes physical/transition risk multipliers, carbon price trajectories,
    and temperature outcomes.
    Source: NGFS Climate Scenarios Database v4.0 (Sep 2023).
    """
    try:
        return {
            "status": "ok",
            "ngfs_scenarios": engine.ref_ngfs_scenarios(),
            "version": "NGFS v4.0 (Sep 2023)",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
