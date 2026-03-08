"""
Supply Chain Scope 3 Emissions Routes
Endpoints for Scope 3 calculation, SBTi target trajectory and emission factor lookup.
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
router = APIRouter(prefix="/api/v1", tags=["Supply Chain Scope 3"])


# ─────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────
class ValidationSummary(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    missing_fields: List[str] = []
    data_quality_score: float = Field(..., ge=0, le=1)


class ActivityEntry(BaseModel):
    description: Optional[str] = None
    quantity: float = Field(..., ge=0)
    unit: str
    emission_factor_kgco2e_per_unit: Optional[float] = Field(None, ge=0)
    supplier_country_iso: Optional[str] = None
    spend_gbp: Optional[float] = Field(None, ge=0)


class Scope3CalculateRequest(BaseModel):
    entity_id: str
    entity_name: Optional[str] = None
    reporting_year: int = Field(..., ge=2000, le=2100)
    activities_by_category: Dict[str, List[ActivityEntry]] = Field(
        ...,
        description=(
            "GHG Protocol Scope 3 category labels as keys, "
            "e.g. cat1_purchased_goods, cat4_upstream_transport"
        ),
    )
    include_hotspot_analysis: bool = True


class CategoryResult(BaseModel):
    category: str
    total_tco2e: float
    pct_of_total: float
    data_quality_score: float
    hotspot_flag: bool
    top_activities: List[Dict[str, Any]]


class HotspotEntry(BaseModel):
    category: str
    activity: str
    tco2e: float
    pct_of_total: float
    recommended_action: str


class Scope3CalculateResponse(BaseModel):
    entity_id: str
    reporting_year: int
    total_scope3_tco2e: float
    by_category: List[CategoryResult]
    hotspots: List[HotspotEntry]
    validation_summary: ValidationSummary
    assessment_id: Optional[str] = None


class SBTiTargetRequest(BaseModel):
    entity_id: str
    entity_name: Optional[str] = None
    base_year: int = Field(..., ge=2000, le=2030)
    base_year_emissions_tco2e: float = Field(..., gt=0)
    target_year: int = Field(..., ge=2025, le=2050)
    reduction_pct: float = Field(..., ge=0, le=100,
                                 description="Absolute reduction % from base year")
    sbti_pathway: str = Field("1.5C", description="1.5C | well-below-2C | 2C")


class MilestoneYear(BaseModel):
    year: int
    target_tco2e: float
    required_annual_reduction_pct: float
    on_track_indicator: str


class SBTiTargetResponse(BaseModel):
    entity_id: str
    base_year: int
    base_year_emissions_tco2e: float
    target_year: int
    reduction_pct: float
    sbti_pathway: str
    milestones: List[MilestoneYear]
    cagr_required_pct: float
    validation_summary: ValidationSummary
    target_id: Optional[str] = None


class EmissionFactor(BaseModel):
    factor_id: str
    sector: str
    category: str
    activity_description: str
    unit: str
    kgco2e_per_unit: float
    source: str
    year: int
    country_iso: Optional[str] = None


class EmissionFactorListResponse(BaseModel):
    total_count: int
    filters_applied: Dict[str, Optional[str]]
    factors: List[EmissionFactor]
    validation_summary: ValidationSummary


def _build_validation_summary(warnings: List[str], missing: List[str]) -> ValidationSummary:
    score = max(0.0, 1.0 - len(warnings) * 0.05 - len(missing) * 0.1)
    return ValidationSummary(
        is_valid=not missing, warnings=warnings,
        missing_fields=missing, data_quality_score=round(score, 3),
    )


# ─────────────────────────────────────────────────────────
# Default emission factors by category (kgCO2e per GBP spent)
# Source: UK DEFRA / BEIS 2023 conversion factors
# ─────────────────────────────────────────────────────────
_DEFAULT_SPEND_FACTORS = {
    "cat1_purchased_goods": 0.42,
    "cat2_capital_goods": 0.38,
    "cat3_fuel_energy": 0.52,
    "cat4_upstream_transport": 0.15,
    "cat5_waste": 0.21,
    "cat6_business_travel": 0.25,
    "cat7_employee_commuting": 0.12,
    "cat8_upstream_leased_assets": 0.30,
    "cat9_downstream_transport": 0.14,
    "cat10_processing": 0.35,
    "cat11_use_of_sold_products": 0.60,
    "cat12_end_of_life": 0.08,
    "cat13_downstream_leased_assets": 0.28,
    "cat14_franchises": 0.20,
    "cat15_investments": 0.45,
}

_HOTSPOT_ACTIONS = {
    "cat1_purchased_goods": "Engage top suppliers on emission reduction; switch to low-carbon alternatives",
    "cat2_capital_goods": "Prioritise low-embodied-carbon equipment in procurement policy",
    "cat3_fuel_energy": "Transition to renewable energy sources; electrify processes",
    "cat4_upstream_transport": "Optimise logistics routes; shift to rail/sea; use EVs",
    "cat5_waste": "Implement circular economy practices; increase recycling rates",
    "cat6_business_travel": "Reduce air travel; use virtual meetings; offset remaining travel",
    "cat7_employee_commuting": "Encourage remote work; provide EV incentives; subsidise public transport",
    "cat11_use_of_sold_products": "Improve product energy efficiency; extend product lifespan",
}

# Built-in emission factor library
_EMISSION_FACTOR_LIBRARY = [
    {"factor_id": "EF_001", "sector": "Energy", "category": "cat3_fuel_energy", "activity_description": "Natural gas combustion", "unit": "kgCO2e/kWh", "kgco2e_per_unit": 0.184, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_002", "sector": "Energy", "category": "cat3_fuel_energy", "activity_description": "Grid electricity (UK average)", "unit": "kgCO2e/kWh", "kgco2e_per_unit": 0.207, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_003", "sector": "Transport", "category": "cat4_upstream_transport", "activity_description": "HGV (average laden)", "unit": "kgCO2e/km", "kgco2e_per_unit": 0.876, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_004", "sector": "Transport", "category": "cat6_business_travel", "activity_description": "Short-haul flight (economy)", "unit": "kgCO2e/passenger-km", "kgco2e_per_unit": 0.156, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_005", "sector": "Transport", "category": "cat6_business_travel", "activity_description": "Long-haul flight (economy)", "unit": "kgCO2e/passenger-km", "kgco2e_per_unit": 0.102, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_006", "sector": "Materials", "category": "cat1_purchased_goods", "activity_description": "Steel (primary, BOF route)", "unit": "kgCO2e/kg", "kgco2e_per_unit": 2.1, "source": "World Steel 2023", "year": 2023},
    {"factor_id": "EF_007", "sector": "Materials", "category": "cat1_purchased_goods", "activity_description": "Aluminium (primary smelting)", "unit": "kgCO2e/kg", "kgco2e_per_unit": 8.6, "source": "IAI 2023", "year": 2023},
    {"factor_id": "EF_008", "sector": "Materials", "category": "cat1_purchased_goods", "activity_description": "Cement (OPC)", "unit": "kgCO2e/kg", "kgco2e_per_unit": 0.91, "source": "GCCA 2023", "year": 2023},
    {"factor_id": "EF_009", "sector": "Waste", "category": "cat5_waste", "activity_description": "Landfill (mixed municipal waste)", "unit": "kgCO2e/tonne", "kgco2e_per_unit": 587, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_010", "sector": "Waste", "category": "cat5_waste", "activity_description": "Recycling (mixed)", "unit": "kgCO2e/tonne", "kgco2e_per_unit": 21.4, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_011", "sector": "Transport", "category": "cat7_employee_commuting", "activity_description": "Average car (petrol)", "unit": "kgCO2e/km", "kgco2e_per_unit": 0.171, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_012", "sector": "Transport", "category": "cat7_employee_commuting", "activity_description": "Bus (average local)", "unit": "kgCO2e/passenger-km", "kgco2e_per_unit": 0.089, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
    {"factor_id": "EF_013", "sector": "Agriculture", "category": "cat1_purchased_goods", "activity_description": "Beef cattle", "unit": "kgCO2e/kg", "kgco2e_per_unit": 27.0, "source": "Poore & Nemecek 2018", "year": 2023},
    {"factor_id": "EF_014", "sector": "Agriculture", "category": "cat1_purchased_goods", "activity_description": "Dairy milk", "unit": "kgCO2e/litre", "kgco2e_per_unit": 3.2, "source": "Poore & Nemecek 2018", "year": 2023},
    {"factor_id": "EF_015", "sector": "Energy", "category": "cat3_fuel_energy", "activity_description": "Diesel", "unit": "kgCO2e/litre", "kgco2e_per_unit": 2.68, "source": "DEFRA 2023", "year": 2023, "country_iso": "GB"},
]

# SBTi minimum annual reduction rates by pathway
_SBTI_MIN_ANNUAL_REDUCTION = {
    "1.5C": 4.2,       # 4.2% per year absolute contraction
    "well-below-2C": 2.5,
    "2C": 1.23,
}

# ─────────────────────────────────────────────────────────
# Category key → DB column name mapping
# ─────────────────────────────────────────────────────────
_CAT_KEY_TO_DB_COL = {
    "cat1_purchased_goods": "cat1_purchased_goods_tco2e",
    "cat2_capital_goods": "cat2_capital_goods_tco2e",
    "cat3_fuel_energy": "cat3_fuel_energy_tco2e",
    "cat4_upstream_transport": "cat4_upstream_transport_tco2e",
    "cat5_waste": "cat5_waste_tco2e",
    "cat6_business_travel": "cat6_business_travel_tco2e",
    "cat7_employee_commuting": "cat7_employee_commuting_tco2e",
    "cat8_upstream_leased_assets": "cat8_upstream_leased_tco2e",
    "cat9_downstream_transport": "cat9_downstream_transport_tco2e",
    "cat10_processing": "cat10_processing_tco2e",
    "cat11_use_of_sold_products": "cat11_use_of_sold_products_tco2e",
    "cat12_end_of_life": "cat12_eol_treatment_tco2e",
    "cat13_downstream_leased_assets": "cat13_downstream_leased_tco2e",
    "cat14_franchises": "cat14_franchises_tco2e",
    "cat15_investments": "cat15_investments_tco2e",
}

_CAT_KEY_TO_NUMBER = {
    "cat1_purchased_goods": 1, "cat2_capital_goods": 2,
    "cat3_fuel_energy": 3, "cat4_upstream_transport": 4,
    "cat5_waste": 5, "cat6_business_travel": 6,
    "cat7_employee_commuting": 7, "cat8_upstream_leased_assets": 8,
    "cat9_downstream_transport": 9, "cat10_processing": 10,
    "cat11_use_of_sold_products": 11, "cat12_end_of_life": 12,
    "cat13_downstream_leased_assets": 13, "cat14_franchises": 14,
    "cat15_investments": 15,
}

_SBTI_PATHWAY_DB_MAP = {
    "1.5C": "1.5C_absolute",
    "well-below-2C": "well_below_2C",
    "2C": "2C_absolute",
}


# ─────────────────────────────────────────────────────────
# DB persist helpers (non-blocking)
# ─────────────────────────────────────────────────────────
def _persist_scope3_assessment(
    db: Session,
    entity_name: str,
    reporting_year: int,
    category_results: List[CategoryResult],
    total_scope3: float,
    hotspots: List[HotspotEntry],
    activities_raw: Dict[str, List[dict]],
    validation_json: dict,
) -> Optional[str]:
    """Insert into scope3_assessments + scope3_activities. Returns assessment_id."""
    try:
        # Build category column values
        cat_cols = {}
        for cr in category_results:
            db_col = _CAT_KEY_TO_DB_COL.get(cr.category)
            if db_col:
                cat_cols[db_col] = round(cr.total_tco2e, 4)

        # Determine approach
        approach = "activity_based"
        categories_included = sorted(
            [_CAT_KEY_TO_NUMBER[cr.category] for cr in category_results
             if cr.category in _CAT_KEY_TO_NUMBER]
        )

        hotspot_json = [
            {"category": h.category, "tco2e": h.tco2e,
             "pct_of_total": h.pct_of_total, "action": h.recommended_action}
            for h in hotspots
        ]

        # Build INSERT
        cols = (
            "entity_name, reporting_year, calculation_approach, "
            "total_scope3_tco2e, categories_included, "
            "hotspot_summary, validation_summary, status"
        )
        vals = (
            ":entity_name, :reporting_year, :approach, "
            ":total_scope3, CAST(:categories_included AS jsonb), "
            "CAST(:hotspot_summary AS jsonb), CAST(:validation_summary AS jsonb), 'draft'"
        )
        params: dict = {
            "entity_name": entity_name,
            "reporting_year": reporting_year,
            "approach": approach,
            "total_scope3": total_scope3,
            "categories_included": json.dumps(categories_included),
            "hotspot_summary": json.dumps(hotspot_json),
            "validation_summary": json.dumps(validation_json),
        }

        # Add per-category columns dynamically
        for col, val in cat_cols.items():
            cols += f", {col}"
            vals += f", :{col}"
            params[col] = val

        sql = f"INSERT INTO scope3_assessments ({cols}) VALUES ({vals}) RETURNING id::text"
        row = db.execute(text(sql), params).fetchone()
        assessment_id = row[0]

        # Insert activities
        for cat_key, acts in activities_raw.items():
            cat_num = _CAT_KEY_TO_NUMBER.get(cat_key)
            if cat_num is None:
                continue
            for act in acts:
                db.execute(text("""
                    INSERT INTO scope3_activities
                    (assessment_id, category_number, category_label,
                     activity_description, activity_quantity, activity_unit,
                     emission_factor_value, co2e_tco2e)
                    VALUES (:aid, :cat_num, :cat_label,
                            :desc, :qty, :unit, :ef_val, :co2e)
                """), {
                    "aid": assessment_id,
                    "cat_num": cat_num,
                    "cat_label": cat_key,
                    "desc": act.get("description", ""),
                    "qty": act.get("quantity", 0),
                    "unit": act.get("unit", ""),
                    "ef_val": act.get("emission_factor"),
                    "co2e": act.get("tco2e", 0),
                })

        db.commit()
        logger.info("Persisted scope3 assessment %s (%d activities)", assessment_id, sum(len(v) for v in activities_raw.values()))
        return assessment_id
    except Exception:
        db.rollback()
        logger.warning("Non-blocking: failed to persist scope3 assessment", exc_info=True)
        return None


def _persist_sbti_target(
    db: Session,
    entity_name: str,
    base_year: int,
    base_year_emissions: float,
    target_year: int,
    reduction_pct: float,
    pathway: str,
    cagr: float,
    milestones: List[MilestoneYear],
    validation_json: dict,
) -> Optional[str]:
    """Insert into sbti_targets + sbti_trajectories. Returns target_id."""
    try:
        db_pathway = _SBTI_PATHWAY_DB_MAP.get(pathway, pathway)
        target_emissions = base_year_emissions * (1 - reduction_pct / 100)

        row = db.execute(text("""
            INSERT INTO sbti_targets
            (entity_name, target_type, sbti_pathway,
             base_year, base_year_total_tco2e,
             near_term_target_year, near_term_reduction_pct,
             near_term_target_tco2e, near_term_annual_reduction_rate_pct,
             validation_summary, sbti_status)
            VALUES
            (:entity_name, 'near_term', :pathway,
             :base_year, :base_total,
             :target_year, :reduction_pct,
             :target_tco2e, :cagr,
             CAST(:validation AS jsonb), 'committed')
            RETURNING id::text
        """), {
            "entity_name": entity_name,
            "pathway": db_pathway,
            "base_year": base_year,
            "base_total": base_year_emissions,
            "target_year": target_year,
            "reduction_pct": reduction_pct,
            "target_tco2e": round(target_emissions, 4),
            "cagr": round(cagr, 4),
            "validation": json.dumps(validation_json),
        }).fetchone()
        target_id = row[0]

        # Insert trajectory milestones
        for ms in milestones:
            cum_red = 0.0
            if base_year_emissions > 0 and ms.year > base_year:
                cum_red = round((1 - ms.target_tco2e / base_year_emissions) * 100, 4)
            is_on_track = ms.on_track_indicator in ("on_track", "baseline")

            db.execute(text("""
                INSERT INTO sbti_trajectories
                (target_id, year, target_emissions_tco2e,
                 cumulative_reduction_pct, is_on_track)
                VALUES (:tid, :yr, :target, :cum_red, :on_track)
            """), {
                "tid": target_id,
                "yr": ms.year,
                "target": ms.target_tco2e,
                "cum_red": cum_red,
                "on_track": is_on_track,
            })

        db.commit()
        logger.info("Persisted SBTi target %s (%d milestones)", target_id, len(milestones))
        return target_id
    except Exception:
        db.rollback()
        logger.warning("Non-blocking: failed to persist SBTi target", exc_info=True)
        return None


# ─────────────────────────────────────────────────────────
# POST Routes (compute + persist)
# ─────────────────────────────────────────────────────────
@router.post("/supply-chain/scope3/calculate", response_model=Scope3CalculateResponse)
def calculate_scope3(request: Scope3CalculateRequest, db: Session = Depends(get_db)):
    """Calculate Scope 3 emissions by GHG Protocol category with optional hotspot analysis."""
    logger.info("Scope 3 calculation: entity=%s year=%d categories=%d",
                request.entity_id, request.reporting_year, len(request.activities_by_category))
    if not request.activities_by_category:
        raise HTTPException(status_code=400, detail="activities_by_category must not be empty.")
    try:
        warnings: List[str] = []
        category_results: List[CategoryResult] = []
        all_activities: List[dict] = []  # for hotspot ranking
        activities_raw: Dict[str, List[dict]] = {}  # for DB persist
        grand_total = 0.0

        for cat_key, activities in request.activities_by_category.items():
            cat_total = 0.0
            top_acts: List[Dict[str, Any]] = []
            raw_acts: List[dict] = []
            has_ef = 0

            for act in activities:
                ef = act.emission_factor_kgco2e_per_unit
                if ef is not None:
                    emissions_kg = act.quantity * ef
                    has_ef += 1
                elif act.spend_gbp:
                    # Spend-based estimation
                    spend_factor = _DEFAULT_SPEND_FACTORS.get(cat_key, 0.30)
                    emissions_kg = act.spend_gbp * spend_factor
                    ef = spend_factor  # record the imputed factor
                    warnings.append(f"{cat_key}: activity '{act.description or 'unnamed'}' estimated via spend-based method")
                else:
                    emissions_kg = 0
                    warnings.append(f"{cat_key}: activity '{act.description or 'unnamed'}' has no EF or spend; excluded")

                emissions_tco2e = emissions_kg / 1000
                cat_total += emissions_tco2e
                desc = act.description or f"{act.quantity} {act.unit}"
                top_acts.append({"description": desc, "tco2e": round(emissions_tco2e, 4)})
                all_activities.append({"category": cat_key, "description": desc, "tco2e": emissions_tco2e})
                raw_acts.append({
                    "description": desc,
                    "quantity": act.quantity,
                    "unit": act.unit,
                    "emission_factor": ef,
                    "tco2e": round(emissions_tco2e, 4),
                })

            # Sort activities within category
            top_acts.sort(key=lambda x: -x["tco2e"])
            dq = min(has_ef / len(activities), 1.0) if activities else 0.0
            activities_raw[cat_key] = raw_acts

            category_results.append(CategoryResult(
                category=cat_key,
                total_tco2e=round(cat_total, 4),
                pct_of_total=0.0,  # will fill after grand total
                data_quality_score=round(dq, 2),
                hotspot_flag=False,  # will fill after grand total
                top_activities=top_acts[:5],
            ))
            grand_total += cat_total

        # Fill pct_of_total and hotspot flag
        for cr in category_results:
            if grand_total > 0:
                pct = cr.total_tco2e / grand_total * 100
                cr.pct_of_total = round(pct, 2)
                cr.hotspot_flag = pct >= 20.0  # >20% = hotspot
            else:
                cr.pct_of_total = 0.0

        # Hotspot analysis
        hotspots: List[HotspotEntry] = []
        if request.include_hotspot_analysis and grand_total > 0:
            all_activities.sort(key=lambda x: -x["tco2e"])
            for act in all_activities[:10]:
                pct = act["tco2e"] / grand_total * 100
                if pct >= 5.0:  # Only flag activities >5% of total
                    action = _HOTSPOT_ACTIONS.get(
                        act["category"],
                        "Review and engage with relevant suppliers on reduction targets"
                    )
                    hotspots.append(HotspotEntry(
                        category=act["category"],
                        activity=act["description"],
                        tco2e=round(act["tco2e"], 4),
                        pct_of_total=round(pct, 2),
                        recommended_action=action,
                    ))

        val = _build_validation_summary(warnings, [])

        # ---- DB persist (non-blocking) ----
        entity_name = request.entity_name or request.entity_id
        assessment_id = _persist_scope3_assessment(
            db, entity_name, request.reporting_year,
            category_results, round(grand_total, 4),
            hotspots, activities_raw, val.model_dump(),
        )

        return Scope3CalculateResponse(
            entity_id=request.entity_id,
            reporting_year=request.reporting_year,
            total_scope3_tco2e=round(grand_total, 4),
            by_category=category_results,
            hotspots=hotspots,
            validation_summary=val,
            assessment_id=assessment_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Scope 3 engine error: entity=%s", request.entity_id)
        raise HTTPException(status_code=500, detail=f"Scope 3 engine error: {exc}") from exc


@router.post("/supply-chain/scope3/sbti-target", response_model=SBTiTargetResponse)
def calculate_sbti_target(request: SBTiTargetRequest, db: Session = Depends(get_db)):
    """Calculate SBTi-aligned Scope 3 reduction target trajectory with annual milestones."""
    logger.info("SBTi target: entity=%s base_year=%d target_year=%d pathway=%s",
                request.entity_id, request.base_year, request.target_year, request.sbti_pathway)
    try:
        warnings: List[str] = []
        years = request.target_year - request.base_year
        if years <= 0:
            raise HTTPException(status_code=400, detail="target_year must be after base_year")

        target_emissions = request.base_year_emissions_tco2e * (1 - request.reduction_pct / 100)

        # CAGR: compound annual growth rate of reduction
        ratio = target_emissions / request.base_year_emissions_tco2e
        cagr = (1 - ratio ** (1 / years)) * 100 if years > 0 else 0.0

        # Check against SBTi minimum
        min_rate = _SBTI_MIN_ANNUAL_REDUCTION.get(request.sbti_pathway, 2.5)
        if cagr < min_rate:
            warnings.append(
                f"CAGR {cagr:.1f}%/yr is below SBTi {request.sbti_pathway} minimum of {min_rate}%/yr"
            )

        # Generate annual milestones
        milestones: List[MilestoneYear] = []
        for yr_offset in range(years + 1):
            yr = request.base_year + yr_offset
            if yr_offset == 0:
                target_at_yr = request.base_year_emissions_tco2e
                annual_red = 0.0
            else:
                # Linear interpolation
                frac = yr_offset / years
                target_at_yr = request.base_year_emissions_tco2e * (1 - frac * request.reduction_pct / 100)
                # Required annual reduction from this point
                remaining_years = years - yr_offset
                if remaining_years > 0:
                    remaining_ratio = target_emissions / target_at_yr
                    annual_red = (1 - remaining_ratio ** (1 / remaining_years)) * 100
                else:
                    annual_red = 0.0

            # On-track indicator
            if yr_offset == 0:
                status = "baseline"
            elif cagr >= min_rate:
                status = "on_track"
            elif cagr >= min_rate * 0.7:
                status = "at_risk"
            else:
                status = "off_track"

            milestones.append(MilestoneYear(
                year=yr,
                target_tco2e=round(target_at_yr, 2),
                required_annual_reduction_pct=round(annual_red, 2),
                on_track_indicator=status,
            ))

        val = _build_validation_summary(warnings, [])

        # ---- DB persist (non-blocking) ----
        entity_name = request.entity_name or request.entity_id
        target_id = _persist_sbti_target(
            db, entity_name, request.base_year,
            request.base_year_emissions_tco2e, request.target_year,
            request.reduction_pct, request.sbti_pathway,
            round(cagr, 2), milestones, val.model_dump(),
        )

        return SBTiTargetResponse(
            entity_id=request.entity_id,
            base_year=request.base_year,
            base_year_emissions_tco2e=request.base_year_emissions_tco2e,
            target_year=request.target_year,
            reduction_pct=request.reduction_pct,
            sbti_pathway=request.sbti_pathway,
            milestones=milestones,
            cagr_required_pct=round(cagr, 2),
            validation_summary=val,
            target_id=target_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("SBTi target engine error: entity=%s", request.entity_id)
        raise HTTPException(status_code=500, detail=f"SBTi target engine error: {exc}") from exc


@router.get("/supply-chain/emission-factors", response_model=EmissionFactorListResponse)
def list_emission_factors(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    category: Optional[str] = Query(None, description="Filter by Scope 3 category"),
    country_iso: Optional[str] = Query(None, description="Filter by country ISO code"),
    year: Optional[int] = Query(None, description="Filter by reference year"),
    db: Session = Depends(get_db),
):
    """List available emission factors, optionally filtered by sector, category or country."""
    logger.info("Emission factor lookup: sector=%s category=%s country=%s year=%s",
                sector, category, country_iso, year)
    try:
        warnings: List[str] = []

        # Try DB first
        db_factors = _query_emission_factors_db(db, sector, category, country_iso, year)
        if db_factors:
            factors = db_factors
        else:
            # Fallback to built-in library
            filtered = _EMISSION_FACTOR_LIBRARY
            if sector:
                filtered = [f for f in filtered if f["sector"].lower() == sector.lower()]
            if category:
                filtered = [f for f in filtered if f["category"].lower() == category.lower()]
            if country_iso:
                filtered = [f for f in filtered if (f.get("country_iso") or "").upper() == country_iso.upper()]
            if year:
                filtered = [f for f in filtered if f["year"] == year]
            factors = [EmissionFactor(**f) for f in filtered]
            if not db_factors:
                warnings.append("Using built-in emission factor library (no DB factors loaded)")

        val = _build_validation_summary(warnings, [])
        return EmissionFactorListResponse(
            total_count=len(factors),
            filters_applied={
                "sector": sector, "category": category,
                "country_iso": country_iso, "year": str(year) if year else None,
            },
            factors=factors,
            validation_summary=val,
        )
    except Exception as exc:
        logger.exception("Emission factor listing engine error")
        raise HTTPException(status_code=500, detail=f"Emission factor engine error: {exc}") from exc


def _query_emission_factors_db(
    db: Session, sector: Optional[str], category: Optional[str],
    country_iso: Optional[str], year: Optional[int],
) -> List[EmissionFactor]:
    """Query emission_factor_library table. Returns empty list if table empty or error."""
    try:
        clauses = ["is_active = true"]
        params: dict = {}
        if sector:
            clauses.append("activity_type ILIKE :sector")
            params["sector"] = f"%{sector}%"
        if category:
            cat_num = _CAT_KEY_TO_NUMBER.get(category)
            if cat_num:
                clauses.append("category_number = :cat_num")
                params["cat_num"] = cat_num
        if country_iso:
            clauses.append("(country_iso = :country OR country_iso IS NULL)")
            params["country"] = country_iso.upper()
        if year:
            clauses.append("(valid_from_year <= :yr AND (valid_to_year >= :yr OR valid_to_year IS NULL))")
            params["yr"] = year

        where = " AND ".join(clauses)
        rows = db.execute(text(f"""
            SELECT id::text, activity_type, activity_sub_type,
                   category_number, factor_value, factor_unit,
                   source_name, valid_from_year, country_iso
            FROM emission_factor_library
            WHERE {where}
            ORDER BY activity_type, valid_from_year DESC
            LIMIT 100
        """), params).fetchall()

        if not rows:
            return []

        result = []
        for r in rows:
            cat_label = ""
            if r[3]:
                for k, v in _CAT_KEY_TO_NUMBER.items():
                    if v == r[3]:
                        cat_label = k
                        break
            result.append(EmissionFactor(
                factor_id=r[0][:8],
                sector=r[1] or "",
                category=cat_label,
                activity_description=r[2] or r[1] or "",
                unit=r[5] or "kgCO2e/unit",
                kgco2e_per_unit=float(r[4]) if r[4] else 0,
                source=r[6] or "",
                year=r[7] or 2023,
                country_iso=r[8],
            ))
        return result
    except Exception:
        logger.debug("emission_factor_library query failed, falling back to built-in", exc_info=True)
        return []


# ─────────────────────────────────────────────────────────
# GET Routes (retrieve persisted data)
# ─────────────────────────────────────────────────────────
@router.get("/supply-chain/scope3/assessments")
def list_scope3_assessments(
    status: Optional[str] = Query(None),
    reporting_year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """List persisted Scope 3 assessments."""
    try:
        clauses = ["1=1"]
        params: dict = {}
        if status:
            clauses.append("status = :status")
            params["status"] = status
        if reporting_year:
            clauses.append("reporting_year = :yr")
            params["yr"] = reporting_year

        where = " AND ".join(clauses)
        rows = db.execute(text(f"""
            SELECT id::text, entity_name, reporting_year,
                   total_scope3_tco2e, calculation_approach,
                   status, created_at
            FROM scope3_assessments
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT 50
        """), params).fetchall()

        return {
            "assessments": [
                {
                    "assessment_id": r[0], "entity_name": r[1],
                    "reporting_year": r[2],
                    "total_scope3_tco2e": float(r[3]) if r[3] else 0,
                    "calculation_approach": r[4], "status": r[5],
                    "created_at": str(r[6]) if r[6] else None,
                }
                for r in rows
            ],
            "total_count": len(rows),
        }
    except Exception as exc:
        logger.exception("Failed to list scope3 assessments")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/supply-chain/scope3/assessments/{assessment_id}")
def get_scope3_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Get a specific Scope 3 assessment with activity breakdown."""
    try:
        row = db.execute(text("""
            SELECT id::text, entity_name, reporting_year, calculation_approach,
                   cat1_purchased_goods_tco2e, cat2_capital_goods_tco2e,
                   cat3_fuel_energy_tco2e, cat4_upstream_transport_tco2e,
                   cat5_waste_tco2e, cat6_business_travel_tco2e,
                   cat7_employee_commuting_tco2e, cat8_upstream_leased_tco2e,
                   cat9_downstream_transport_tco2e, cat10_processing_tco2e,
                   cat11_use_of_sold_products_tco2e, cat12_eol_treatment_tco2e,
                   cat13_downstream_leased_tco2e, cat14_franchises_tco2e,
                   cat15_investments_tco2e,
                   total_scope3_tco2e, hotspot_summary,
                   validation_summary, status, created_at
            FROM scope3_assessments WHERE id = :aid
        """), {"aid": assessment_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Fetch activities
        acts = db.execute(text("""
            SELECT category_number, category_label, activity_description,
                   activity_quantity, activity_unit, emission_factor_value,
                   co2e_tco2e
            FROM scope3_activities WHERE assessment_id = :aid
            ORDER BY category_number, co2e_tco2e DESC
        """), {"aid": assessment_id}).fetchall()

        categories = {}
        cat_cols = list(row[4:19])  # cat1 through cat15
        cat_names = list(_CAT_KEY_TO_DB_COL.keys())
        for i, col_val in enumerate(cat_cols):
            if col_val and float(col_val) > 0:
                categories[cat_names[i]] = float(col_val)

        return {
            "assessment_id": row[0],
            "entity_name": row[1],
            "reporting_year": row[2],
            "calculation_approach": row[3],
            "categories": categories,
            "total_scope3_tco2e": float(row[19]) if row[19] else 0,
            "hotspot_summary": row[20],
            "validation_summary": row[21],
            "status": row[22],
            "created_at": str(row[23]) if row[23] else None,
            "activities": [
                {
                    "category_number": a[0], "category_label": a[1],
                    "description": a[2],
                    "quantity": float(a[3]) if a[3] else 0,
                    "unit": a[4],
                    "emission_factor": float(a[5]) if a[5] else None,
                    "co2e_tco2e": float(a[6]) if a[6] else 0,
                }
                for a in acts
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get scope3 assessment %s", assessment_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/supply-chain/scope3/sbti-targets")
def list_sbti_targets(
    status: Optional[str] = Query(None),
    pathway: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List persisted SBTi targets."""
    try:
        clauses = ["1=1"]
        params: dict = {}
        if status:
            clauses.append("sbti_status = :status")
            params["status"] = status
        if pathway:
            db_pathway = _SBTI_PATHWAY_DB_MAP.get(pathway, pathway)
            clauses.append("sbti_pathway = :pathway")
            params["pathway"] = db_pathway

        where = " AND ".join(clauses)
        rows = db.execute(text(f"""
            SELECT id::text, entity_name, target_type, sbti_pathway,
                   base_year, base_year_total_tco2e,
                   near_term_target_year, near_term_reduction_pct,
                   near_term_annual_reduction_rate_pct,
                   sbti_status, created_at
            FROM sbti_targets
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT 50
        """), params).fetchall()

        return {
            "targets": [
                {
                    "target_id": r[0], "entity_name": r[1],
                    "target_type": r[2], "sbti_pathway": r[3],
                    "base_year": r[4],
                    "base_year_total_tco2e": float(r[5]) if r[5] else 0,
                    "target_year": r[6],
                    "reduction_pct": float(r[7]) if r[7] else 0,
                    "annual_reduction_rate_pct": float(r[8]) if r[8] else 0,
                    "status": r[9],
                    "created_at": str(r[10]) if r[10] else None,
                }
                for r in rows
            ],
            "total_count": len(rows),
        }
    except Exception as exc:
        logger.exception("Failed to list SBTi targets")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/supply-chain/scope3/sbti-targets/{target_id}")
def get_sbti_target(target_id: str, db: Session = Depends(get_db)):
    """Get a specific SBTi target with trajectory milestones."""
    try:
        row = db.execute(text("""
            SELECT id::text, entity_name, target_type, sbti_pathway,
                   base_year, base_year_total_tco2e,
                   near_term_target_year, near_term_reduction_pct,
                   near_term_target_tco2e, near_term_annual_reduction_rate_pct,
                   validation_summary, sbti_status, created_at
            FROM sbti_targets WHERE id = :tid
        """), {"tid": target_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="SBTi target not found")

        trajectories = db.execute(text("""
            SELECT year, target_emissions_tco2e,
                   cumulative_reduction_pct, is_on_track
            FROM sbti_trajectories WHERE target_id = :tid
            ORDER BY year
        """), {"tid": target_id}).fetchall()

        return {
            "target_id": row[0],
            "entity_name": row[1],
            "target_type": row[2],
            "sbti_pathway": row[3],
            "base_year": row[4],
            "base_year_total_tco2e": float(row[5]) if row[5] else 0,
            "target_year": row[6],
            "reduction_pct": float(row[7]) if row[7] else 0,
            "target_tco2e": float(row[8]) if row[8] else 0,
            "annual_reduction_rate_pct": float(row[9]) if row[9] else 0,
            "validation_summary": row[10],
            "status": row[11],
            "created_at": str(row[12]) if row[12] else None,
            "trajectories": [
                {
                    "year": t[0],
                    "target_emissions_tco2e": float(t[1]) if t[1] else 0,
                    "cumulative_reduction_pct": float(t[2]) if t[2] else 0,
                    "is_on_track": t[3],
                }
                for t in trajectories
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get SBTi target %s", target_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
