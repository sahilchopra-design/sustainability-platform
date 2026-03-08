"""
PCAF, SFDR and EU Taxonomy Routes
Endpoints for financed emissions, SFDR PAI indicators and EU Taxonomy alignment.
Inline computation + PostgreSQL persistence via SQLAlchemy.
"""
import json
import logging
import math
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["PCAF / SFDR / EU Taxonomy"])


# -------------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------------
class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


class InvesteeEntry(BaseModel):
    investee_id: str
    name: Optional[str] = None
    sector: str
    country_iso: str
    investment_value_gbp: float = Field(..., gt=0)
    enterprise_value_gbp: Optional[float] = Field(None, gt=0)
    revenue_gbp: Optional[float] = Field(None, gt=0)
    scope1_tco2e: Optional[float] = Field(None, ge=0)
    scope2_tco2e: Optional[float] = Field(None, ge=0)
    scope3_tco2e: Optional[float] = Field(None, ge=0)
    pcaf_data_quality_score: Optional[int] = Field(None, ge=1, le=5)


class PCAFRequest(BaseModel):
    investees: List[InvesteeEntry]
    reporting_year: int = Field(..., ge=2000, le=2100)
    asset_class: str = Field(
        "listed_equity",
        description="listed_equity | corporate_bonds | loans | real_estate",
    )
    entity_name: Optional[str] = Field(None, description="Portfolio / entity name for DB storage")


class InvesteeEmissions(BaseModel):
    investee_id: str
    financed_emissions_tco2e: float
    attribution_factor: float
    pcaf_data_quality_score: int
    scope1_attributed: float
    scope2_attributed: float
    scope3_attributed: Optional[float] = None


class PCAFResponse(BaseModel):
    portfolio_id: Optional[str] = None
    reporting_year: int
    asset_class: str
    total_financed_emissions_tco2e: float
    waci_tco2e_per_mrevenue: float
    carbon_footprint_tco2e_per_minvested: float
    implied_temperature_rise_c: Optional[float] = None
    per_investee: List[InvesteeEmissions]
    validation_summary: ValidationSummary


class SFDRPAIRequest(BaseModel):
    investees: List[InvesteeEntry]
    reporting_year: int = Field(..., ge=2000, le=2100)
    reference_year: Optional[int] = None
    entity_name: Optional[str] = Field(None, description="Entity name for DB storage")
    sfdr_article: Optional[int] = Field(8, ge=6, le=9, description="SFDR Article 6/8/9")


class PAIIndicator(BaseModel):
    indicator_id: str
    indicator_name: str
    value: Optional[float] = None
    unit: str
    data_quality_score: float = Field(..., ge=0, le=1)
    coverage_pct: float = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class SFDRPAIResponse(BaseModel):
    disclosure_id: Optional[str] = None
    reporting_year: int
    mandatory_indicators: List[PAIIndicator]
    optional_indicators: List[PAIIndicator]
    overall_data_coverage_pct: float
    validation_summary: ValidationSummary


class ActivityBreakdown(BaseModel):
    activity_code: str
    activity_name: str
    turnover_pct: float = Field(..., ge=0, le=100)
    capex_pct: float = Field(..., ge=0, le=100)
    opex_pct: Optional[float] = Field(None, ge=0, le=100)
    substantial_contribution_objective: Optional[str] = None


class EntityTaxonomyEntry(BaseModel):
    entity_id: str
    name: Optional[str] = None
    sector: str
    country_iso: str
    activities: List[ActivityBreakdown]
    total_revenue_gbp: Optional[float] = None
    total_capex_gbp: Optional[float] = None


class TaxonomyAlignmentRequest(BaseModel):
    entities: List[EntityTaxonomyEntry]
    reporting_year: int = Field(..., ge=2000, le=2100)
    entity_name: Optional[str] = Field(None, description="Assessment entity name for DB storage")


class ObjectiveAlignment(BaseModel):
    objective: str
    eligible_turnover_pct: float
    aligned_turnover_pct: float
    eligible_capex_pct: float
    aligned_capex_pct: float
    dnsh_compliant: bool


class TaxonomyAlignmentResponse(BaseModel):
    assessment_id: Optional[str] = None
    reporting_year: int
    total_entities: int
    portfolio_eligible_turnover_pct: float
    portfolio_aligned_turnover_pct: float
    portfolio_eligible_capex_pct: float
    portfolio_aligned_capex_pct: float
    by_objective: List[ObjectiveAlignment]
    validation_summary: ValidationSummary


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


# -------------------------------------------------------------------------
# PCAF computation helpers
# -------------------------------------------------------------------------
_SECTOR_EMISSION_INTENSITY = {
    "Energy": 850, "Utilities": 620, "Materials": 480, "Industrials": 220,
    "Consumer Discretionary": 90, "Consumer Staples": 110, "Health Care": 55,
    "Financials": 25, "Information Technology": 40, "Communication Services": 35,
    "Real Estate": 75, "Default": 150,
}

_ASSET_CLASS_DB_MAP = {
    "listed_equity": "listed_equity",
    "corporate_bonds": "corporate_bonds",
    "loans": "business_loans",
    "real_estate": "commercial_re_loans",
}


def _estimate_emissions(investee: dict) -> tuple:
    s1 = investee.get("scope1_tco2e")
    s2 = investee.get("scope2_tco2e")
    s3 = investee.get("scope3_tco2e")
    revenue = investee.get("revenue_gbp") or investee.get("enterprise_value_gbp") or investee["investment_value_gbp"]
    sector = investee.get("sector", "Default")
    intensity = _SECTOR_EMISSION_INTENSITY.get(sector, _SECTOR_EMISSION_INTENSITY["Default"])
    estimated = False
    if s1 is None:
        s1 = (revenue / 1_000_000) * intensity * 0.6
        estimated = True
    if s2 is None:
        s2 = (revenue / 1_000_000) * intensity * 0.4
        estimated = True
    return s1, s2, s3, estimated


def _pcaf_data_quality(investee: dict, estimated: bool) -> int:
    if investee.get("pcaf_data_quality_score"):
        return investee["pcaf_data_quality_score"]
    if not estimated and investee.get("scope1_tco2e") is not None:
        return 2
    if investee.get("revenue_gbp"):
        return 3
    return 4


# -------------------------------------------------------------------------
# SFDR PAI helpers
# -------------------------------------------------------------------------
_MANDATORY_PAI = [
    ("PAI_1", "GHG emissions (Scope 1)", "tCO2e"),
    ("PAI_2", "GHG emissions (Scope 2)", "tCO2e"),
    ("PAI_3", "GHG emissions (Scope 3)", "tCO2e"),
    ("PAI_4", "Carbon footprint", "tCO2e per EUR M invested"),
    ("PAI_5", "GHG intensity of investee companies", "tCO2e per EUR M revenue"),
    ("PAI_6", "Exposure to fossil fuel sector", "%"),
    ("PAI_7", "Share of non-renewable energy consumption", "%"),
    ("PAI_8", "Energy consumption intensity per high impact sector", "GWh per EUR M revenue"),
    ("PAI_9", "Activities negatively affecting biodiversity", "%"),
    ("PAI_10", "Emissions to water", "tonnes"),
    ("PAI_11", "Hazardous waste ratio", "tonnes"),
    ("PAI_12", "Violations of UNGC / OECD Guidelines", "%"),
    ("PAI_13", "Gender pay gap", "%"),
    ("PAI_14", "Board gender diversity", "%"),
]

_FOSSIL_SECTORS = {"Energy", "Utilities", "Oil & Gas", "Coal", "Mining"}


# -------------------------------------------------------------------------
# EU Taxonomy helpers
# -------------------------------------------------------------------------
_EU_OBJECTIVES = [
    "Climate change mitigation",
    "Climate change adaptation",
    "Sustainable use of water and marine resources",
    "Transition to a circular economy",
    "Pollution prevention and control",
    "Protection of biodiversity and ecosystems",
]

_ACTIVITY_ELIGIBLE_OBJECTIVES = {
    "CCM": "Climate change mitigation",
    "CCA": "Climate change adaptation",
    "WTR": "Sustainable use of water and marine resources",
    "CE": "Transition to a circular economy",
    "PPC": "Pollution prevention and control",
    "BIO": "Protection of biodiversity and ecosystems",
}

_OBJECTIVE_INDEX = {obj: i + 1 for i, obj in enumerate(_EU_OBJECTIVES)}


# =========================================================================
# DB persistence helpers (non-blocking)
# =========================================================================
def _persist_pcaf_portfolio(db, entity_name, reporting_year, asset_class, response_data, per_investee_raw, validation_json):
    """Non-blocking persist of PCAF portfolio + investees."""
    try:
        portfolio_type = _ASSET_CLASS_DB_MAP.get(asset_class, "mixed")
        total_invested = sum(i["investment_value_gbp"] for i in per_investee_raw)
        total_revenue = sum((i.get("revenue_gbp") or i["investment_value_gbp"]) for i in per_investee_raw)

        row = db.execute(text("""
            INSERT INTO pcaf_portfolios (
                entity_name, reporting_year, portfolio_type,
                total_outstanding_gbp, total_revenue_gbp,
                total_financed_emissions_tco2e,
                waci_tco2e_per_mrevenue,
                carbon_footprint_tco2e_per_mgbp_invested,
                portfolio_temperature_c,
                portfolio_coverage_pct,
                validation_summary, status
            ) VALUES (
                :entity_name, :year, :ptype,
                :total_inv, :total_rev,
                :total_fe, :waci, :carbon_fp, :itr,
                100.0,
                :val_json, 'draft'
            ) RETURNING id
        """), {
            "entity_name": entity_name,
            "year": reporting_year,
            "ptype": portfolio_type,
            "total_inv": total_invested,
            "total_rev": total_revenue,
            "total_fe": response_data["total_financed_emissions_tco2e"],
            "waci": response_data["waci_tco2e_per_mrevenue"],
            "carbon_fp": response_data["carbon_footprint_tco2e_per_minvested"],
            "itr": response_data.get("implied_temperature_rise_c"),
            "val_json": validation_json,
        })
        portfolio_id = str(row.fetchone()[0])

        # Insert per-investee rows
        for inv, result in zip(per_investee_raw, response_data["per_investee"]):
            attr_method = "evic" if inv.get("enterprise_value_gbp") else "revenue"
            db.execute(text("""
                INSERT INTO pcaf_investees (
                    portfolio_id, investee_name, sector_gics, country_iso,
                    outstanding_investment_gbp, enterprise_value_gbp, revenue_gbp,
                    attribution_factor, scope1_tco2e, scope2_market_tco2e,
                    scope3_total_tco2e,
                    financed_scope1_tco2e, financed_scope2_tco2e, financed_scope3_tco2e,
                    total_financed_emissions_tco2e,
                    pcaf_dq_scope1, pcaf_dq_scope2,
                    attribution_method
                ) VALUES (
                    :pid::uuid, :name, :sector, :country,
                    :inv_val, :evic, :rev,
                    :attr, :s1, :s2, :s3,
                    :fs1, :fs2, :fs3, :total_fe,
                    :dq, :dq, :attr_method
                )
            """), {
                "pid": portfolio_id,
                "name": inv.get("name") or inv["investee_id"],
                "sector": inv.get("sector"),
                "country": inv.get("country_iso"),
                "inv_val": inv["investment_value_gbp"],
                "evic": inv.get("enterprise_value_gbp"),
                "rev": inv.get("revenue_gbp"),
                "attr": result["attribution_factor"],
                "s1": inv.get("scope1_tco2e"),
                "s2": inv.get("scope2_tco2e"),
                "s3": inv.get("scope3_tco2e"),
                "fs1": result["scope1_attributed"],
                "fs2": result["scope2_attributed"],
                "fs3": result.get("scope3_attributed"),
                "total_fe": result["financed_emissions_tco2e"],
                "dq": result["pcaf_data_quality_score"],
                "attr_method": attr_method,
            })

        db.commit()
        return portfolio_id
    except Exception as db_err:
        db.rollback()
        logger.warning("PCAF DB persist failed (non-blocking): %s", db_err)
        return None


def _persist_sfdr_pai(db, entity_name, reporting_year, sfdr_article, mandatory, optional, overall_coverage, validation_json):
    """Non-blocking persist of SFDR PAI disclosure."""
    try:
        period_start = date(reporting_year, 1, 1)
        period_end = date(reporting_year, 12, 31)

        mandatory_full = [m.model_dump() for m in mandatory]
        optional_full = [o.model_dump() for o in optional]

        # Extract individual PAI values from mandatory list
        pai_vals = {}
        for m in mandatory:
            pai_vals[m.indicator_id] = m.value

        row = db.execute(text("""
            INSERT INTO sfdr_pai_disclosures (
                entity_name, reporting_period_start, reporting_period_end,
                reference_date, sfdr_article,
                pai_1_scope1_scope2_tco2e,
                pai_2_carbon_footprint,
                pai_3_waci,
                pai_4_fossil_fuel_exposure_pct,
                pai_9_hazardous_waste_tonnes,
                pai_10_un_global_compact_violations_pct,
                mandatory_indicators_full,
                optional_indicators,
                weighted_avg_dq_score,
                validation_summary, status
            ) VALUES (
                :name, :start, :end, :ref_date, :article,
                :pai1, :pai2, :pai3, :pai4, :pai9, :pai10,
                :mandatory_json, :optional_json,
                3.0,
                :val_json, 'draft'
            ) RETURNING id
        """), {
            "name": entity_name,
            "start": period_start,
            "end": period_end,
            "ref_date": period_end,
            "article": sfdr_article,
            "pai1": (pai_vals.get("PAI_1", 0) or 0) + (pai_vals.get("PAI_2", 0) or 0),
            "pai2": pai_vals.get("PAI_4"),
            "pai3": pai_vals.get("PAI_5"),
            "pai4": pai_vals.get("PAI_6"),
            "pai9": pai_vals.get("PAI_11"),
            "pai10": pai_vals.get("PAI_12"),
            "mandatory_json": json.dumps(mandatory_full),
            "optional_json": json.dumps(optional_full),
            "val_json": validation_json,
        })
        disclosure_id = str(row.fetchone()[0])
        db.commit()
        return disclosure_id
    except Exception as db_err:
        db.rollback()
        logger.warning("SFDR PAI DB persist failed (non-blocking): %s", db_err)
        return None


def _persist_eu_taxonomy(db, entity_name, reporting_year, result_data, by_objective, validation_json):
    """Non-blocking persist of EU Taxonomy assessment + activities."""
    try:
        # Map objective names to column values
        obj_vals = {}
        for oa in by_objective:
            idx = _OBJECTIVE_INDEX.get(oa.objective, 0)
            obj_vals[f"obj{idx}"] = oa.aligned_turnover_pct

        dnsh_json = json.dumps({oa.objective: {"pass": oa.dnsh_compliant} for oa in by_objective})

        row = db.execute(text("""
            INSERT INTO eu_taxonomy_assessments (
                entity_name, reporting_year,
                taxonomy_eligible_turnover_pct, taxonomy_aligned_turnover_pct,
                taxonomy_eligible_capex_pct, taxonomy_aligned_capex_pct,
                obj1_climate_mitigation_aligned_pct,
                obj2_climate_adaptation_aligned_pct,
                obj3_water_marine_aligned_pct,
                obj4_circular_economy_aligned_pct,
                obj5_pollution_prevention_aligned_pct,
                obj6_biodiversity_aligned_pct,
                dnsh_compliance, validation_summary, status
            ) VALUES (
                :name, :year,
                :elig_turn, :align_turn,
                :elig_capex, :align_capex,
                :obj1, :obj2, :obj3, :obj4, :obj5, :obj6,
                :dnsh, :val_json, 'draft'
            ) RETURNING id
        """), {
            "name": entity_name,
            "year": reporting_year,
            "elig_turn": result_data["portfolio_eligible_turnover_pct"],
            "align_turn": result_data["portfolio_aligned_turnover_pct"],
            "elig_capex": result_data["portfolio_eligible_capex_pct"],
            "align_capex": result_data["portfolio_aligned_capex_pct"],
            "obj1": obj_vals.get("obj1", 0),
            "obj2": obj_vals.get("obj2", 0),
            "obj3": obj_vals.get("obj3", 0),
            "obj4": obj_vals.get("obj4", 0),
            "obj5": obj_vals.get("obj5", 0),
            "obj6": obj_vals.get("obj6", 0),
            "dnsh": dnsh_json,
            "val_json": validation_json,
        })
        assessment_id = str(row.fetchone()[0])
        db.commit()
        return assessment_id
    except Exception as db_err:
        db.rollback()
        logger.warning("EU Taxonomy DB persist failed (non-blocking): %s", db_err)
        return None


# =========================================================================
# POST Routes
# =========================================================================
@router.post("/pcaf/financed-emissions", response_model=PCAFResponse)
def calculate_financed_emissions(request: PCAFRequest, db: Session = Depends(get_db)):
    """Calculate PCAF-compliant financed emissions, WACI and carbon footprint for a portfolio."""
    logger.info("PCAF financed emissions: %d investees year=%d asset_class=%s",
                len(request.investees), request.reporting_year, request.asset_class)
    if not request.investees:
        raise HTTPException(status_code=400, detail="At least one investee is required.")
    try:
        warnings: List[str] = []
        per_investee: List[InvesteeEmissions] = []
        total_financed = 0.0
        total_invested = 0.0
        waci_numerator = 0.0
        total_revenue = 0.0

        for inv in request.investees:
            d = inv.model_dump()
            s1, s2, s3, estimated = _estimate_emissions(d)
            if estimated:
                warnings.append(f"{inv.investee_id}: emissions estimated from sector averages (DQ score lowered)")

            evic = inv.enterprise_value_gbp or (inv.revenue_gbp or inv.investment_value_gbp)
            attribution = min(inv.investment_value_gbp / evic, 1.0) if evic > 0 else 1.0

            s1_attr = s1 * attribution
            s2_attr = s2 * attribution
            s3_attr = (s3 * attribution) if s3 else None
            financed = s1_attr + s2_attr + (s3_attr or 0)
            dq = _pcaf_data_quality(d, estimated)

            per_investee.append(InvesteeEmissions(
                investee_id=inv.investee_id,
                financed_emissions_tco2e=round(financed, 2),
                attribution_factor=round(attribution, 4),
                pcaf_data_quality_score=dq,
                scope1_attributed=round(s1_attr, 2),
                scope2_attributed=round(s2_attr, 2),
                scope3_attributed=round(s3_attr, 2) if s3_attr is not None else None,
            ))

            total_financed += financed
            total_invested += inv.investment_value_gbp
            rev = inv.revenue_gbp or evic
            total_revenue += rev
            if rev > 0:
                weight = inv.investment_value_gbp
                intensity = (s1 + s2 + (s3 or 0)) / (rev / 1_000_000)
                waci_numerator += weight * intensity

        waci = waci_numerator / total_invested if total_invested > 0 else 0.0
        carbon_fp = total_financed / (total_invested / 1_000_000) if total_invested > 0 else 0.0

        itr = None
        if carbon_fp > 0:
            itr = round(1.5 + (carbon_fp / 100) * 0.3, 2)
            itr = min(itr, 6.0)

        val = _build_validation_summary(warnings, [])

        response = PCAFResponse(
            reporting_year=request.reporting_year,
            asset_class=request.asset_class,
            total_financed_emissions_tco2e=round(total_financed, 2),
            waci_tco2e_per_mrevenue=round(waci, 2),
            carbon_footprint_tco2e_per_minvested=round(carbon_fp, 2),
            implied_temperature_rise_c=itr,
            per_investee=per_investee,
            validation_summary=val,
        )

        # Non-blocking DB persist
        entity_name = request.entity_name or "Portfolio"
        investees_raw = [inv.model_dump() for inv in request.investees]
        resp_dict = response.model_dump()
        val_json = json.dumps(val.model_dump())
        portfolio_id = _persist_pcaf_portfolio(
            db, entity_name, request.reporting_year, request.asset_class,
            resp_dict, investees_raw, val_json,
        )
        response.portfolio_id = portfolio_id
        return response

    except Exception as exc:
        logger.exception("PCAF financed emissions engine error")
        raise HTTPException(status_code=500, detail=f"PCAF engine error: {exc}") from exc


@router.post("/sfdr/pai", response_model=SFDRPAIResponse)
def calculate_sfdr_pai(request: SFDRPAIRequest, db: Session = Depends(get_db)):
    """Calculate all 14 mandatory SFDR Principal Adverse Impact indicators for a portfolio."""
    logger.info("SFDR PAI: %d investees year=%d", len(request.investees), request.reporting_year)
    if not request.investees:
        raise HTTPException(status_code=400, detail="At least one investee is required.")
    try:
        warnings: List[str] = []
        investees = [i.model_dump() for i in request.investees]
        n = len(investees)

        total_invested = sum(i["investment_value_gbp"] for i in investees)
        total_revenue = sum((i.get("revenue_gbp") or i["investment_value_gbp"]) for i in investees)

        total_s1 = sum((i.get("scope1_tco2e") or 0) for i in investees)
        total_s2 = sum((i.get("scope2_tco2e") or 0) for i in investees)
        total_s3 = sum((i.get("scope3_tco2e") or 0) for i in investees)
        s1_coverage = sum(1 for i in investees if i.get("scope1_tco2e") is not None) / n * 100
        s2_coverage = sum(1 for i in investees if i.get("scope2_tco2e") is not None) / n * 100
        s3_coverage = sum(1 for i in investees if i.get("scope3_tco2e") is not None) / n * 100

        attr_s1 = sum(
            (i.get("scope1_tco2e") or 0) * min(i["investment_value_gbp"] / (i.get("enterprise_value_gbp") or i["investment_value_gbp"]), 1.0)
            for i in investees
        )
        attr_s2 = sum(
            (i.get("scope2_tco2e") or 0) * min(i["investment_value_gbp"] / (i.get("enterprise_value_gbp") or i["investment_value_gbp"]), 1.0)
            for i in investees
        )
        attr_s3 = sum(
            (i.get("scope3_tco2e") or 0) * min(i["investment_value_gbp"] / (i.get("enterprise_value_gbp") or i["investment_value_gbp"]), 1.0)
            for i in investees
        )

        carbon_fp = (attr_s1 + attr_s2) / (total_invested / 1_000_000) if total_invested > 0 else 0
        ghg_intensity = (total_s1 + total_s2) / (total_revenue / 1_000_000) if total_revenue > 0 else 0
        fossil_exposure = sum(1 for i in investees if i.get("sector") in _FOSSIL_SECTORS) / n * 100

        mandatory: List[PAIIndicator] = [
            PAIIndicator(indicator_id="PAI_1", indicator_name="GHG emissions (Scope 1)",
                         value=round(attr_s1, 2), unit="tCO2e", data_quality_score=round(s1_coverage / 100, 2),
                         coverage_pct=round(s1_coverage, 1)),
            PAIIndicator(indicator_id="PAI_2", indicator_name="GHG emissions (Scope 2)",
                         value=round(attr_s2, 2), unit="tCO2e", data_quality_score=round(s2_coverage / 100, 2),
                         coverage_pct=round(s2_coverage, 1)),
            PAIIndicator(indicator_id="PAI_3", indicator_name="GHG emissions (Scope 3)",
                         value=round(attr_s3, 2), unit="tCO2e", data_quality_score=round(s3_coverage / 100, 2),
                         coverage_pct=round(s3_coverage, 1)),
            PAIIndicator(indicator_id="PAI_4", indicator_name="Carbon footprint",
                         value=round(carbon_fp, 2), unit="tCO2e per GBP M invested",
                         data_quality_score=round(min(s1_coverage, s2_coverage) / 100, 2),
                         coverage_pct=round(min(s1_coverage, s2_coverage), 1)),
            PAIIndicator(indicator_id="PAI_5", indicator_name="GHG intensity of investee companies",
                         value=round(ghg_intensity, 2), unit="tCO2e per GBP M revenue",
                         data_quality_score=0.7, coverage_pct=round(min(s1_coverage, s2_coverage), 1)),
            PAIIndicator(indicator_id="PAI_6", indicator_name="Exposure to fossil fuel sector",
                         value=round(fossil_exposure, 1), unit="%", data_quality_score=1.0, coverage_pct=100.0),
            PAIIndicator(indicator_id="PAI_7", indicator_name="Share of non-renewable energy consumption",
                         value=None, unit="%", data_quality_score=0.0, coverage_pct=0.0,
                         notes="Energy mix data not available; requires company-level disclosure"),
            PAIIndicator(indicator_id="PAI_8", indicator_name="Energy consumption intensity per high impact sector",
                         value=None, unit="GWh per GBP M revenue", data_quality_score=0.0, coverage_pct=0.0,
                         notes="Energy consumption data not available"),
            PAIIndicator(indicator_id="PAI_9", indicator_name="Activities negatively affecting biodiversity",
                         value=0.0, unit="%", data_quality_score=0.3, coverage_pct=30.0,
                         notes="Estimated from sector classification"),
            PAIIndicator(indicator_id="PAI_10", indicator_name="Emissions to water",
                         value=None, unit="tonnes", data_quality_score=0.0, coverage_pct=0.0,
                         notes="Water emissions data not available"),
            PAIIndicator(indicator_id="PAI_11", indicator_name="Hazardous waste ratio",
                         value=None, unit="tonnes", data_quality_score=0.0, coverage_pct=0.0,
                         notes="Waste data not available"),
            PAIIndicator(indicator_id="PAI_12", indicator_name="Violations of UNGC / OECD Guidelines",
                         value=0.0, unit="%", data_quality_score=0.5, coverage_pct=50.0,
                         notes="No violation data in input; defaults to 0%"),
            PAIIndicator(indicator_id="PAI_13", indicator_name="Gender pay gap",
                         value=None, unit="%", data_quality_score=0.0, coverage_pct=0.0,
                         notes="Gender pay data not available"),
            PAIIndicator(indicator_id="PAI_14", indicator_name="Board gender diversity",
                         value=None, unit="%", data_quality_score=0.0, coverage_pct=0.0,
                         notes="Board composition data not available"),
        ]

        optional: List[PAIIndicator] = [
            PAIIndicator(indicator_id="PAI_OPT_1", indicator_name="Investments in companies without carbon reduction initiatives",
                         value=None, unit="%", data_quality_score=0.0, coverage_pct=0.0,
                         notes="Carbon initiative data not available"),
        ]

        avg_coverage = sum(m.coverage_pct for m in mandatory) / len(mandatory)
        val = _build_validation_summary(warnings, [])

        response = SFDRPAIResponse(
            reporting_year=request.reporting_year,
            mandatory_indicators=mandatory,
            optional_indicators=optional,
            overall_data_coverage_pct=round(avg_coverage, 1),
            validation_summary=val,
        )

        # Non-blocking DB persist
        entity_name = request.entity_name or "Portfolio"
        sfdr_article = request.sfdr_article or 8
        val_json = json.dumps(val.model_dump())
        disclosure_id = _persist_sfdr_pai(
            db, entity_name, request.reporting_year, sfdr_article,
            mandatory, optional, avg_coverage, val_json,
        )
        response.disclosure_id = disclosure_id
        return response

    except Exception as exc:
        logger.exception("SFDR PAI engine error")
        raise HTTPException(status_code=500, detail=f"SFDR PAI engine error: {exc}") from exc


@router.post("/eu-taxonomy/alignment", response_model=TaxonomyAlignmentResponse)
def assess_eu_taxonomy_alignment(request: TaxonomyAlignmentRequest, db: Session = Depends(get_db)):
    """Assess EU Taxonomy eligibility and alignment with DNSH compliance by objective."""
    logger.info("EU Taxonomy alignment: %d entities year=%d",
                len(request.entities), request.reporting_year)
    if not request.entities:
        raise HTTPException(status_code=400, detail="At least one entity is required.")
    try:
        warnings: List[str] = []

        total_turnover = 0.0
        total_capex = 0.0
        eligible_turnover = 0.0
        aligned_turnover = 0.0
        eligible_capex = 0.0
        aligned_capex = 0.0

        objective_data: Dict[str, dict] = {
            obj: {"elig_turn": 0.0, "align_turn": 0.0, "elig_capex": 0.0, "align_capex": 0.0, "dnsh": True}
            for obj in _EU_OBJECTIVES
        }

        for entity in request.entities:
            ent_revenue = entity.total_revenue_gbp or sum(a.turnover_pct for a in entity.activities) * 10_000
            ent_capex = entity.total_capex_gbp or ent_revenue * 0.15
            total_turnover += ent_revenue
            total_capex += ent_capex

            for act in entity.activities:
                code_prefix = act.activity_code.split("_")[0].upper() if act.activity_code else "CCM"
                objective = _ACTIVITY_ELIGIBLE_OBJECTIVES.get(code_prefix, "Climate change mitigation")

                act_turnover = ent_revenue * act.turnover_pct / 100
                act_capex = ent_capex * act.capex_pct / 100

                eligible_turnover += act_turnover
                eligible_capex += act_capex
                objective_data[objective]["elig_turn"] += act_turnover
                objective_data[objective]["elig_capex"] += act_capex

                if act.substantial_contribution_objective:
                    aligned_turnover += act_turnover * 0.85
                    aligned_capex += act_capex * 0.85
                    objective_data[objective]["align_turn"] += act_turnover * 0.85
                    objective_data[objective]["align_capex"] += act_capex * 0.85
                else:
                    aligned_turnover += act_turnover * 0.3
                    aligned_capex += act_capex * 0.3
                    objective_data[objective]["align_turn"] += act_turnover * 0.3
                    objective_data[objective]["align_capex"] += act_capex * 0.3

        by_objective: List[ObjectiveAlignment] = []
        for obj in _EU_OBJECTIVES:
            d = objective_data[obj]
            by_objective.append(ObjectiveAlignment(
                objective=obj,
                eligible_turnover_pct=round(d["elig_turn"] / total_turnover * 100, 2) if total_turnover > 0 else 0,
                aligned_turnover_pct=round(d["align_turn"] / total_turnover * 100, 2) if total_turnover > 0 else 0,
                eligible_capex_pct=round(d["elig_capex"] / total_capex * 100, 2) if total_capex > 0 else 0,
                aligned_capex_pct=round(d["align_capex"] / total_capex * 100, 2) if total_capex > 0 else 0,
                dnsh_compliant=d["dnsh"],
            ))

        val = _build_validation_summary(warnings, [])

        response = TaxonomyAlignmentResponse(
            reporting_year=request.reporting_year,
            total_entities=len(request.entities),
            portfolio_eligible_turnover_pct=round(eligible_turnover / total_turnover * 100, 2) if total_turnover > 0 else 0,
            portfolio_aligned_turnover_pct=round(aligned_turnover / total_turnover * 100, 2) if total_turnover > 0 else 0,
            portfolio_eligible_capex_pct=round(eligible_capex / total_capex * 100, 2) if total_capex > 0 else 0,
            portfolio_aligned_capex_pct=round(aligned_capex / total_capex * 100, 2) if total_capex > 0 else 0,
            by_objective=by_objective,
            validation_summary=val,
        )

        # Non-blocking DB persist
        entity_name = request.entity_name or (request.entities[0].name if request.entities[0].name else "Portfolio")
        val_json = json.dumps(val.model_dump())
        resp_dict = response.model_dump()
        assessment_id = _persist_eu_taxonomy(
            db, entity_name, request.reporting_year, resp_dict, by_objective, val_json,
        )
        response.assessment_id = assessment_id
        return response

    except Exception as exc:
        logger.exception("EU Taxonomy alignment engine error")
        raise HTTPException(status_code=500, detail=f"EU Taxonomy engine error: {exc}") from exc


# =========================================================================
# GET Routes (retrieve persisted data)
# =========================================================================
@router.get("/pcaf/portfolios")
def list_pcaf_portfolios(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    reporting_year: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List saved PCAF portfolio assessments."""
    clauses = []
    params: dict = {"lim": limit, "off": offset}
    if status:
        clauses.append("status = :status")
        params["status"] = status
    if reporting_year:
        clauses.append("reporting_year = :year")
        params["year"] = reporting_year
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = db.execute(text(f"""
        SELECT id, entity_name, reporting_year, portfolio_type,
               total_financed_emissions_tco2e, waci_tco2e_per_mrevenue,
               carbon_footprint_tco2e_per_mgbp_invested, portfolio_temperature_c,
               status, created_at
        FROM pcaf_portfolios {where}
        ORDER BY created_at DESC LIMIT :lim OFFSET :off
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/pcaf/portfolios/{portfolio_id}")
def get_pcaf_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Get a single PCAF portfolio with investee detail."""
    row = db.execute(text("""
        SELECT * FROM pcaf_portfolios WHERE id = :pid::uuid
    """), {"pid": portfolio_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="PCAF portfolio not found")
    portfolio = dict(row._mapping)
    investees = db.execute(text("""
        SELECT * FROM pcaf_investees WHERE portfolio_id = :pid::uuid
        ORDER BY total_financed_emissions_tco2e DESC NULLS LAST
    """), {"pid": portfolio_id}).fetchall()
    portfolio["investees"] = [dict(r._mapping) for r in investees]
    return portfolio


@router.get("/sfdr/pai-disclosures")
def list_sfdr_disclosures(
    db: Session = Depends(get_db),
    reporting_year: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List saved SFDR PAI disclosures."""
    clauses = []
    params: dict = {"lim": limit, "off": offset}
    if reporting_year:
        clauses.append("reporting_period_end >= :start AND reporting_period_start <= :end")
        params["start"] = date(reporting_year, 1, 1)
        params["end"] = date(reporting_year, 12, 31)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = db.execute(text(f"""
        SELECT id, entity_name, reporting_period_start, reporting_period_end,
               sfdr_article, pai_1_scope1_scope2_tco2e, pai_2_carbon_footprint,
               pai_4_fossil_fuel_exposure_pct, weighted_avg_dq_score,
               status, created_at
        FROM sfdr_pai_disclosures {where}
        ORDER BY created_at DESC LIMIT :lim OFFSET :off
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/sfdr/pai-disclosures/{disclosure_id}")
def get_sfdr_disclosure(disclosure_id: str, db: Session = Depends(get_db)):
    """Get a single SFDR PAI disclosure with full indicator detail."""
    row = db.execute(text("""
        SELECT * FROM sfdr_pai_disclosures WHERE id = :did::uuid
    """), {"did": disclosure_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="SFDR PAI disclosure not found")
    return dict(row._mapping)


@router.get("/eu-taxonomy/assessments")
def list_eu_taxonomy_assessments(
    db: Session = Depends(get_db),
    reporting_year: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List saved EU Taxonomy alignment assessments."""
    clauses = []
    params: dict = {"lim": limit, "off": offset}
    if reporting_year:
        clauses.append("reporting_year = :year")
        params["year"] = reporting_year
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = db.execute(text(f"""
        SELECT id, entity_name, reporting_year,
               taxonomy_eligible_turnover_pct, taxonomy_aligned_turnover_pct,
               taxonomy_eligible_capex_pct, taxonomy_aligned_capex_pct,
               status, created_at
        FROM eu_taxonomy_assessments {where}
        ORDER BY created_at DESC LIMIT :lim OFFSET :off
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/eu-taxonomy/assessments/{assessment_id}")
def get_eu_taxonomy_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Get a single EU Taxonomy assessment with activity detail."""
    row = db.execute(text("""
        SELECT * FROM eu_taxonomy_assessments WHERE id = :aid::uuid
    """), {"aid": assessment_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="EU Taxonomy assessment not found")
    assessment = dict(row._mapping)
    activities = db.execute(text("""
        SELECT * FROM eu_taxonomy_activities WHERE assessment_id = :aid::uuid
        ORDER BY activity_code
    """), {"aid": assessment_id}).fetchall()
    assessment["activities"] = [dict(r._mapping) for r in activities]
    return assessment
