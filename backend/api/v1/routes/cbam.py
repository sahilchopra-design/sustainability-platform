"""
CBAM API — product categories, suppliers, emissions, cost projections, compliance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from db.base import get_db
from db.models.cbam import (
    CBAMProductCategory, CBAMSupplier, CBAMEmbeddedEmissions,
    CBAMCostProjection, CBAMComplianceReport, CBAMCountryRisk,
    CBAMCertificatePrice,
)
from services.cbam_service import (
    seed_cbam_data, calculate_cbam_cost, project_supplier_costs, get_cbam_dashboard,
    FREE_ALLOC_SCHEDULE, ETS_PRICE_SCENARIOS,
)

router = APIRouter(prefix="/api/v1/cbam", tags=["cbam"])


# ---- Schemas ----

class SupplierCreate(BaseModel):
    supplier_name: str
    country_code: str = Field(..., min_length=2, max_length=2)
    has_domestic_carbon_price: bool = False
    domestic_carbon_price: float = 0


class EmissionsCreate(BaseModel):
    supplier_id: str
    product_category_id: str
    reporting_year: int
    reporting_quarter: int = 1
    import_volume_tonnes: float = 0
    direct_emissions: float = 0
    indirect_emissions: float = 0
    specific_direct: Optional[float] = None
    specific_indirect: Optional[float] = None


class CostCalcRequest(BaseModel):
    emissions_tco2: float
    eu_ets_price: float
    domestic_carbon_price: float = 0
    free_allocation_pct: float = 0


# ---- Dashboard ----

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return get_cbam_dashboard(db)


@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    return seed_cbam_data(db)


# ---- Products ----

@router.get("/products")
def list_products(sector: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(CBAMProductCategory).filter(CBAMProductCategory.is_active.is_(True))
    if sector:
        q = q.filter(CBAMProductCategory.sector == sector)
    products = q.order_by(CBAMProductCategory.sector, CBAMProductCategory.product_name).all()
    return [_product_dict(p) for p in products]


@router.get("/products/{pid}")
def get_product(pid: str, db: Session = Depends(get_db)):
    p = db.get(CBAMProductCategory, pid)
    if not p:
        raise HTTPException(404, "Product not found")
    return _product_dict(p)


@router.get("/products/sectors/summary")
def product_sectors(db: Session = Depends(get_db)):
    from sqlalchemy import func
    rows = db.query(CBAMProductCategory.sector, func.count(), func.avg(CBAMProductCategory.default_total_emissions)
                    ).group_by(CBAMProductCategory.sector).all()
    return [{"sector": r[0], "product_count": r[1], "avg_emissions": round(r[2] or 0, 4)} for r in rows]


# ---- Suppliers ----

@router.get("/suppliers")
def list_suppliers(country: Optional[str] = None, risk: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(CBAMSupplier)
    if country:
        q = q.filter(CBAMSupplier.country_code == country.upper())
    if risk:
        q = q.filter(CBAMSupplier.risk_category == risk)
    return [_supplier_dict(s) for s in q.order_by(CBAMSupplier.supplier_name).all()]


@router.post("/suppliers", status_code=201)
def create_supplier(body: SupplierCreate, db: Session = Depends(get_db)):
    # Auto-assign risk from country
    country = db.query(CBAMCountryRisk).filter(CBAMCountryRisk.country_code == body.country_code.upper()).first()
    risk_score = country.overall_risk_score if country else 0.5
    risk_cat = country.risk_category if country else "Medium"

    s = CBAMSupplier(
        supplier_name=body.supplier_name, country_code=body.country_code.upper(),
        has_domestic_carbon_price=body.has_domestic_carbon_price,
        domestic_carbon_price=body.domestic_carbon_price or (country.carbon_price_eur if country else 0),
        risk_score=risk_score, risk_category=risk_cat,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _supplier_dict(s)


@router.get("/suppliers/{sid}")
def get_supplier(sid: str, db: Session = Depends(get_db)):
    s = db.get(CBAMSupplier, sid)
    if not s:
        raise HTTPException(404, "Supplier not found")
    return _supplier_dict(s)


@router.delete("/suppliers/{sid}", status_code=204)
def delete_supplier(sid: str, db: Session = Depends(get_db)):
    s = db.get(CBAMSupplier, sid)
    if not s:
        raise HTTPException(404)
    db.delete(s)
    db.commit()


@router.get("/suppliers/{sid}/projections")
def supplier_projections(sid: str, db: Session = Depends(get_db)):
    return project_supplier_costs(db, sid)


# ---- Emissions ----

@router.post("/emissions", status_code=201)
def record_emissions(body: EmissionsCreate, db: Session = Depends(get_db)):
    product = db.get(CBAMProductCategory, body.product_category_id)
    specific_total = (body.specific_direct or 0) + (body.specific_indirect or 0)
    if not specific_total and product:
        specific_total = product.default_total_emissions or 0
        uses_default = True
    else:
        uses_default = False

    e = CBAMEmbeddedEmissions(
        supplier_id=body.supplier_id, product_category_id=body.product_category_id,
        reporting_year=body.reporting_year, reporting_quarter=body.reporting_quarter,
        import_volume_tonnes=body.import_volume_tonnes,
        direct_emissions=body.direct_emissions, indirect_emissions=body.indirect_emissions,
        specific_direct=body.specific_direct, specific_indirect=body.specific_indirect,
        specific_total=specific_total, uses_default_values=uses_default,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id, "specific_total": e.specific_total, "uses_default_values": e.uses_default_values}


@router.get("/emissions")
def list_emissions(supplier_id: Optional[str] = None, year: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(CBAMEmbeddedEmissions)
    if supplier_id:
        q = q.filter(CBAMEmbeddedEmissions.supplier_id == supplier_id)
    if year:
        q = q.filter(CBAMEmbeddedEmissions.reporting_year == year)
    return [{
        "id": e.id, "supplier_id": e.supplier_id,
        "product_category_id": e.product_category_id,
        "reporting_year": e.reporting_year, "reporting_quarter": e.reporting_quarter,
        "import_volume_tonnes": e.import_volume_tonnes,
        "direct_emissions": e.direct_emissions, "indirect_emissions": e.indirect_emissions,
        "specific_total": e.specific_total, "is_verified": e.is_verified,
        "uses_default_values": e.uses_default_values,
    } for e in q.order_by(CBAMEmbeddedEmissions.reporting_year.desc()).all()]


# ---- Cost Calculation ----

@router.post("/calculate-cost")
def calc_cost(body: CostCalcRequest):
    return calculate_cbam_cost(body.emissions_tco2, body.eu_ets_price, body.domestic_carbon_price, body.free_allocation_pct)


@router.get("/free-allocation-schedule")
def free_alloc_schedule():
    return FREE_ALLOC_SCHEDULE


@router.get("/ets-price-scenarios")
def ets_scenarios():
    return ETS_PRICE_SCENARIOS


# ---- Country Risk ----

@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):
    countries = db.query(CBAMCountryRisk).order_by(CBAMCountryRisk.overall_risk_score.desc()).all()
    return [{
        "country_code": c.country_code, "country_name": c.country_name,
        "has_carbon_pricing": c.has_carbon_pricing, "carbon_price_eur": c.carbon_price_eur,
        "grid_emission_factor": c.grid_emission_factor,
        "risk_score": c.overall_risk_score, "risk_category": c.risk_category,
    } for c in countries]


# ---- Certificate Prices ----

@router.get("/certificate-prices")
def cert_prices(scenario: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(CBAMCertificatePrice)
    if scenario:
        q = q.filter(CBAMCertificatePrice.scenario_name == scenario)
    return [{
        "date": p.price_date, "ets_price": p.eu_ets_price_eur,
        "cbam_price": p.cbam_certificate_price_eur,
        "scenario": p.scenario_name, "is_projection": p.is_projection,
    } for p in q.order_by(CBAMCertificatePrice.price_date).all()]


# ---- Helpers ----

def _product_dict(p):
    return {
        "id": p.id, "cn_code": p.cn_code, "hs_code": p.hs_code,
        "sector": p.sector, "product_name": p.product_name,
        "default_direct_emissions": p.default_direct_emissions,
        "default_indirect_emissions": p.default_indirect_emissions,
        "default_total_emissions": p.default_total_emissions,
    }

def _supplier_dict(s):
    return {
        "id": s.id, "supplier_name": s.supplier_name, "country_code": s.country_code,
        "verification_status": s.verification_status,
        "has_domestic_carbon_price": s.has_domestic_carbon_price,
        "domestic_carbon_price": s.domestic_carbon_price,
        "risk_score": s.risk_score, "risk_category": s.risk_category,
    }
