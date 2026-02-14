"""
CBAM Service — seed data, cost calculations, compliance reporting.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from db.models.cbam import (
    CBAMProductCategory, CBAMSupplier, CBAMEmbeddedEmissions,
    CBAMCostProjection, CBAMComplianceReport, CBAMCountryRisk,
    CBAMCertificatePrice, CBAMVerifier,
)

# EU ETS price projections by scenario (EUR/tCO2)
ETS_PRICE_SCENARIOS = {
    "Current Trend": {2025: 70, 2026: 75, 2027: 80, 2028: 85, 2030: 95, 2035: 120, 2040: 150, 2050: 200},
    "Ambitious": {2025: 80, 2026: 90, 2027: 105, 2028: 120, 2030: 160, 2035: 250, 2040: 350, 2050: 500},
    "Conservative": {2025: 65, 2026: 68, 2027: 70, 2028: 72, 2030: 78, 2035: 90, 2040: 105, 2050: 130},
}

PRODUCT_CATEGORIES = [
    # Cement
    {"cn_code": "25232100", "hs_code": "252321", "sector": "Cement", "product_name": "Portland cement", "default_direct": 0.525, "default_indirect": 0.060, "default_total": 0.585},
    {"cn_code": "25232900", "hs_code": "252329", "sector": "Cement", "product_name": "Other hydraulic cement", "default_direct": 0.498, "default_indirect": 0.055, "default_total": 0.553},
    {"cn_code": "25231000", "hs_code": "252310", "sector": "Cement", "product_name": "Cement clinker", "default_direct": 0.846, "default_indirect": 0.050, "default_total": 0.896},
    # Iron & Steel
    {"cn_code": "72061000", "hs_code": "720610", "sector": "Iron & Steel", "product_name": "Iron - ingots", "default_direct": 1.283, "default_indirect": 0.195, "default_total": 1.478},
    {"cn_code": "72071100", "hs_code": "720711", "sector": "Iron & Steel", "product_name": "Semi-finished iron/steel", "default_direct": 1.419, "default_indirect": 0.214, "default_total": 1.633},
    {"cn_code": "72083900", "hs_code": "720839", "sector": "Iron & Steel", "product_name": "Flat-rolled iron/steel", "default_direct": 1.535, "default_indirect": 0.232, "default_total": 1.767},
    {"cn_code": "72142000", "hs_code": "721420", "sector": "Iron & Steel", "product_name": "Bars and rods of iron", "default_direct": 1.320, "default_indirect": 0.200, "default_total": 1.520},
    # Aluminium
    {"cn_code": "76011000", "hs_code": "760110", "sector": "Aluminium", "product_name": "Unwrought aluminium, not alloyed", "default_direct": 1.514, "default_indirect": 6.800, "default_total": 8.314},
    {"cn_code": "76012000", "hs_code": "760120", "sector": "Aluminium", "product_name": "Aluminium alloys", "default_direct": 1.253, "default_indirect": 5.600, "default_total": 6.853},
    {"cn_code": "76061100", "hs_code": "760611", "sector": "Aluminium", "product_name": "Aluminium plates/sheets", "default_direct": 1.680, "default_indirect": 7.200, "default_total": 8.880},
    # Fertilizers
    {"cn_code": "28342100", "hs_code": "283421", "sector": "Fertilizers", "product_name": "Potassium nitrate", "default_direct": 2.694, "default_indirect": 0.200, "default_total": 2.894},
    {"cn_code": "31021000", "hs_code": "310210", "sector": "Fertilizers", "product_name": "Urea", "default_direct": 1.578, "default_indirect": 0.180, "default_total": 1.758},
    {"cn_code": "31051000", "hs_code": "310510", "sector": "Fertilizers", "product_name": "Mineral/chemical fertilizers with NPK", "default_direct": 1.200, "default_indirect": 0.150, "default_total": 1.350},
    # Electricity
    {"cn_code": "27160000", "hs_code": "271600", "sector": "Electricity", "product_name": "Electrical energy", "default_direct": 0.376, "default_indirect": 0.0, "default_total": 0.376},
    # Hydrogen
    {"cn_code": "28041000", "hs_code": "280410", "sector": "Hydrogen", "product_name": "Hydrogen", "default_direct": 9.000, "default_indirect": 2.500, "default_total": 11.500},
]

COUNTRY_RISK_DATA = [
    {"code": "CN", "name": "China", "carbon": True, "price": 12, "grid_ef": 0.555, "risk": 0.7, "cat": "High"},
    {"code": "IN", "name": "India", "carbon": False, "price": 0, "grid_ef": 0.708, "risk": 0.85, "cat": "Very High"},
    {"code": "RU", "name": "Russia", "carbon": False, "price": 0, "grid_ef": 0.337, "risk": 0.9, "cat": "Very High"},
    {"code": "TR", "name": "Turkey", "carbon": False, "price": 0, "grid_ef": 0.440, "risk": 0.75, "cat": "High"},
    {"code": "UA", "name": "Ukraine", "carbon": False, "price": 0, "grid_ef": 0.352, "risk": 0.8, "cat": "High"},
    {"code": "KR", "name": "South Korea", "carbon": True, "price": 18, "grid_ef": 0.415, "risk": 0.4, "cat": "Medium"},
    {"code": "JP", "name": "Japan", "carbon": True, "price": 3, "grid_ef": 0.470, "risk": 0.35, "cat": "Low"},
    {"code": "US", "name": "United States", "carbon": False, "price": 0, "grid_ef": 0.390, "risk": 0.5, "cat": "Medium"},
    {"code": "BR", "name": "Brazil", "carbon": False, "price": 0, "grid_ef": 0.074, "risk": 0.55, "cat": "Medium"},
    {"code": "ZA", "name": "South Africa", "carbon": True, "price": 9, "grid_ef": 0.928, "risk": 0.7, "cat": "High"},
    {"code": "EG", "name": "Egypt", "carbon": False, "price": 0, "grid_ef": 0.450, "risk": 0.65, "cat": "High"},
    {"code": "GB", "name": "United Kingdom", "carbon": True, "price": 55, "grid_ef": 0.207, "risk": 0.15, "cat": "Low"},
    {"code": "NO", "name": "Norway", "carbon": True, "price": 85, "grid_ef": 0.017, "risk": 0.05, "cat": "Low"},
    {"code": "CH", "name": "Switzerland", "carbon": True, "price": 120, "grid_ef": 0.015, "risk": 0.05, "cat": "Low"},
    {"code": "CA", "name": "Canada", "carbon": True, "price": 48, "grid_ef": 0.120, "risk": 0.25, "cat": "Low"},
    {"code": "AU", "name": "Australia", "carbon": False, "price": 0, "grid_ef": 0.656, "risk": 0.55, "cat": "Medium"},
    {"code": "MX", "name": "Mexico", "carbon": True, "price": 4, "grid_ef": 0.410, "risk": 0.6, "cat": "Medium"},
    {"code": "ID", "name": "Indonesia", "carbon": False, "price": 0, "grid_ef": 0.720, "risk": 0.75, "cat": "High"},
    {"code": "VN", "name": "Vietnam", "carbon": False, "price": 0, "grid_ef": 0.580, "risk": 0.7, "cat": "High"},
    {"code": "TH", "name": "Thailand", "carbon": False, "price": 0, "grid_ef": 0.470, "risk": 0.6, "cat": "Medium"},
]


def seed_cbam_data(db: Session) -> dict:
    """Seed product categories, country risk, and certificate prices."""
    # Products
    prod_count = 0
    for p in PRODUCT_CATEGORIES:
        existing = db.query(CBAMProductCategory).filter(CBAMProductCategory.cn_code == p["cn_code"]).first()
        if not existing:
            db.add(CBAMProductCategory(
                cn_code=p["cn_code"], hs_code=p["hs_code"], sector=p["sector"],
                product_name=p["product_name"], default_direct_emissions=p["default_direct"],
                default_indirect_emissions=p["default_indirect"], default_total_emissions=p["default_total"],
            ))
            prod_count += 1

    # Countries
    country_count = 0
    for c in COUNTRY_RISK_DATA:
        existing = db.query(CBAMCountryRisk).filter(CBAMCountryRisk.country_code == c["code"]).first()
        if not existing:
            db.add(CBAMCountryRisk(
                country_code=c["code"], country_name=c["name"],
                has_carbon_pricing=c["carbon"], carbon_price_eur=c["price"],
                grid_emission_factor=c["grid_ef"], overall_risk_score=c["risk"],
                risk_category=c["cat"],
            ))
            country_count += 1

    # Certificate prices
    price_count = 0
    for scenario, prices in ETS_PRICE_SCENARIOS.items():
        for year, price in prices.items():
            existing = db.query(CBAMCertificatePrice).filter(
                CBAMCertificatePrice.price_date == str(year),
                CBAMCertificatePrice.scenario_name == scenario,
            ).first()
            if not existing:
                db.add(CBAMCertificatePrice(
                    price_date=str(year), eu_ets_price_eur=price,
                    cbam_certificate_price_eur=price,  # CBAM certificate = weekly avg ETS price
                    scenario_name=scenario, is_projection=year > 2025,
                ))
                price_count += 1

    db.commit()
    return {"products": prod_count, "countries": country_count, "prices": price_count}


def calculate_cbam_cost(
    emissions_tco2: float,
    eu_ets_price: float,
    domestic_carbon_price: float = 0,
    free_allocation_pct: float = 0,  # EU free allowance phase-out
) -> dict:
    """Calculate net CBAM cost for a given emissions amount."""
    gross_cost = emissions_tco2 * eu_ets_price
    domestic_credit = emissions_tco2 * domestic_carbon_price
    free_reduction = gross_cost * (free_allocation_pct / 100)
    net_cost = max(0, gross_cost - domestic_credit - free_reduction)
    return {
        "gross_cost_eur": round(gross_cost, 2),
        "domestic_credit_eur": round(domestic_credit, 2),
        "free_allocation_reduction_eur": round(free_reduction, 2),
        "net_cbam_cost_eur": round(net_cost, 2),
    }


# CBAM free allocation phase-out schedule (EU)
FREE_ALLOC_SCHEDULE = {
    2026: 97.5, 2027: 95.0, 2028: 90.0, 2029: 77.5, 2030: 51.5,
    2031: 39.0, 2032: 26.5, 2033: 14.0, 2034: 0.0,
}


def project_supplier_costs(db: Session, supplier_id: str, scenarios: list = None) -> list:
    """Project CBAM costs for a supplier across years and scenarios."""
    supplier = db.get(CBAMSupplier, supplier_id)
    if not supplier:
        return []

    emissions = db.query(CBAMEmbeddedEmissions).filter(
        CBAMEmbeddedEmissions.supplier_id == supplier_id
    ).order_by(CBAMEmbeddedEmissions.reporting_year.desc()).first()

    if not emissions:
        return []

    # Use latest emissions as basis
    annual_volume = emissions.import_volume_tonnes or 0
    specific_emissions = emissions.specific_total or 0
    annual_emissions = annual_volume * specific_emissions if specific_emissions > 0 else (emissions.direct_emissions or 0)

    if not scenarios:
        scenarios = list(ETS_PRICE_SCENARIOS.keys())

    projections = []
    for scenario in scenarios:
        prices = ETS_PRICE_SCENARIOS.get(scenario, {})
        for year in sorted(prices.keys()):
            ets_price = prices[year]
            free_pct = FREE_ALLOC_SCHEDULE.get(year, 0 if year >= 2034 else 97.5)
            cost = calculate_cbam_cost(annual_emissions, ets_price, supplier.domestic_carbon_price or 0, free_pct)

            projections.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier.supplier_name,
                "year": year,
                "scenario": scenario,
                "import_volume_tonnes": round(annual_volume, 2),
                "embedded_emissions_tco2": round(annual_emissions, 2),
                "eu_ets_price_eur": ets_price,
                "free_allocation_pct": free_pct,
                **cost,
            })

    return projections


def get_cbam_dashboard(db: Session) -> dict:
    """Get CBAM dashboard overview."""
    suppliers = db.query(CBAMSupplier).count()
    products = db.query(CBAMProductCategory).filter(CBAMProductCategory.is_active.is_(True)).count()
    countries = db.query(CBAMCountryRisk).count()
    emissions_records = db.query(CBAMEmbeddedEmissions).count()

    # Risk breakdown
    high_risk = db.query(CBAMSupplier).filter(CBAMSupplier.risk_category.in_(["High", "Very High"])).count()

    # Sector breakdown
    sector_counts = db.query(
        CBAMProductCategory.sector, func.count(CBAMProductCategory.id)
    ).group_by(CBAMProductCategory.sector).all()

    # Total emissions
    total_emissions = db.query(func.sum(CBAMEmbeddedEmissions.direct_emissions)).scalar() or 0

    return {
        "total_suppliers": suppliers,
        "total_products": products,
        "total_countries": countries,
        "emissions_records": emissions_records,
        "high_risk_suppliers": high_risk,
        "total_embedded_emissions_tco2": round(total_emissions, 2),
        "sector_breakdown": {s: c for s, c in sector_counts},
    }
