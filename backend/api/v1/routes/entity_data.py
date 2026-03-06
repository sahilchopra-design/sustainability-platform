"""
CSRD Entity Data Bridge — API Routes
=====================================
Exposes the 8 seeded CSRD entities' data in module-ready formats so that
Carbon, ECL, Nature Risk, Stranded Asset, Sector Assessment, and Portfolio
modules can pre-fill their inputs from real database values instead of
requiring manual entry.

Endpoints
---------
GET  /api/v1/entity-data/entities
GET  /api/v1/entity-data/{entity_id}
GET  /api/v1/entity-data/{entity_id}/carbon
GET  /api/v1/entity-data/{entity_id}/ecl
GET  /api/v1/entity-data/{entity_id}/nature
GET  /api/v1/entity-data/{entity_id}/stranded
GET  /api/v1/entity-data/{entity_id}/sector
GET  /api/v1/entity-data/{entity_id}/portfolio-asset
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.base import get_db
from services.csrd_entity_service import (
    get_entity_list,
    get_entity_profile,
    get_carbon_inputs,
    get_ecl_inputs,
    get_nature_inputs,
    get_stranded_inputs,
    get_sector_inputs,
    get_portfolio_asset_spec,
)

router = APIRouter(prefix="/api/v1/entity-data", tags=["CSRD Entity Data Bridge"])


@router.get("/entities")
def list_entities(db: Session = Depends(get_db)):
    """
    Return summary rows for all 8 seeded CSRD entities.
    Includes top-level GHG, energy, workforce, and sector identifiers.
    """
    return {"entities": get_entity_list(db)}


@router.get("/{entity_id}")
def entity_profile(entity_id: str, db: Session = Depends(get_db)):
    """
    Full cross-module data profile for one CSRD entity.
    Includes all ESRS E1-E5, S1, G1 data plus sector-specific
    FI or energy operational data where applicable.
    """
    profile = get_entity_profile(entity_id, db)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return profile


@router.get("/{entity_id}/carbon")
def entity_carbon_inputs(entity_id: str, db: Session = Depends(get_db)):
    """
    Pre-filled Carbon Calculator inputs for this entity.
    Maps esrs_e1_ghg_emissions + esrs_e1_energy to scope 1/2/3 calculator format.
    """
    result = get_carbon_inputs(entity_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found or has no GHG data")
    return result


@router.get("/{entity_id}/ecl")
def entity_ecl_inputs(entity_id: str, db: Session = Depends(get_db)):
    """
    Pre-filled IFRS 9 ECL / Climate Credit Risk inputs for this entity.
    Only available for Financial Institution entities (ABN AMRO, BNP, ING, Rabobank).
    Maps fi_financials + fi_loan_books + fi_csrd_e1_climate to ECL calc format.
    """
    result = get_ecl_inputs(entity_id, db)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Entity '{entity_id}' not found or is not a Financial Institution entity"
        )
    return result


@router.get("/{entity_id}/nature")
def entity_nature_inputs(entity_id: str, db: Session = Depends(get_db)):
    """
    Pre-filled Nature Risk / TNFD LEAP inputs for this entity.
    Maps esrs_e4_biodiversity + esrs_e3_water to TNFD format.
    """
    result = get_nature_inputs(entity_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found or has no biodiversity data")
    return result


@router.get("/{entity_id}/stranded")
def entity_stranded_inputs(entity_id: str, db: Session = Depends(get_db)):
    """
    Pre-filled Stranded Asset Calculator inputs for this entity.
    Only available for Energy entities (EDP, ENGIE, Orsted, RWE).
    Maps energy_generation_mix + energy_stranded_assets_register to stranded calc format.
    """
    result = get_stranded_inputs(entity_id, db)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Entity '{entity_id}' not found or is not an Energy entity"
        )
    return result


@router.get("/{entity_id}/sector")
def entity_sector_inputs(entity_id: str, db: Session = Depends(get_db)):
    """
    Pre-filled Sector Assessment inputs for this entity.
    Maps operational energy/FI data to sector assessment format (power plant, data centre, CAT risk).
    """
    result = get_sector_inputs(entity_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return result


@router.get("/{entity_id}/portfolio-asset")
def entity_portfolio_asset(entity_id: str, db: Session = Depends(get_db)):
    """
    Return an assets_pg-compatible record spec for this CSRD entity.
    Useful for seeding or linking the entity as a portfolio holding.
    """
    result = get_portfolio_asset_spec(entity_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return result
