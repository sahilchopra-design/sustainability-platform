"""
Unified Portfolio API — PostgreSQL-backed (replaces MongoDB portfolio endpoints).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

from db.base import get_db
from db.models.portfolio_pg import PortfolioPG, AssetPG, AnalysisRunPG

router = APIRouter(prefix="/api/pg", tags=["portfolios-pg"])


# ---- Schemas ----

class AssetCreate(BaseModel):
    asset_type: str = "Bond"
    company_name: str
    company_sector: str = "Power Generation"
    company_subsector: Optional[str] = None
    exposure: float
    market_value: Optional[float] = None
    base_pd: float = 0.02
    base_lgd: float = 0.45
    rating: str = "BBB"
    maturity_years: int = 5


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    assets: List[AssetCreate] = []


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ---- Portfolio CRUD ----

@router.get("/portfolios")
def list_portfolios(db: Session = Depends(get_db)):
    portfolios = db.query(PortfolioPG).order_by(PortfolioPG.created_at.desc()).all()
    return {"portfolios": [{
        "id": p.id, "name": p.name, "description": p.description,
        "num_assets": len(p.assets), "total_exposure": sum(a.exposure for a in p.assets),
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    } for p in portfolios]}


@router.post("/portfolios", status_code=201)
def create_portfolio(body: PortfolioCreate, db: Session = Depends(get_db)):
    p = PortfolioPG(name=body.name, description=body.description)
    db.add(p)
    db.flush()

    for a in body.assets:
        db.add(AssetPG(
            portfolio_id=p.id, asset_type=a.asset_type,
            company_name=a.company_name, company_sector=a.company_sector,
            company_subsector=a.company_subsector, exposure=a.exposure,
            market_value=a.market_value or a.exposure, base_pd=a.base_pd,
            base_lgd=a.base_lgd, rating=a.rating, maturity_years=a.maturity_years,
        ))
    db.commit()
    db.refresh(p)

    return {
        "id": p.id, "name": p.name, "description": p.description,
        "num_assets": len(p.assets), "total_exposure": sum(a.exposure for a in p.assets),
    }


@router.get("/portfolios/{pid}")
def get_portfolio(pid: str, db: Session = Depends(get_db)):
    p = db.get(PortfolioPG, pid)
    if not p:
        raise HTTPException(404, "Portfolio not found")
    return {
        "id": p.id, "name": p.name, "description": p.description,
        "assets": [{
            "id": a.id, "asset_type": a.asset_type,
            "company": {"name": a.company_name, "sector": a.company_sector, "subsector": a.company_subsector},
            "exposure": a.exposure, "market_value": a.market_value,
            "base_pd": a.base_pd, "base_lgd": a.base_lgd,
            "rating": a.rating, "maturity_years": a.maturity_years,
        } for a in p.assets],
        "total_exposure": sum(a.exposure for a in p.assets),
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.put("/portfolios/{pid}")
def update_portfolio(pid: str, body: PortfolioUpdate, db: Session = Depends(get_db)):
    p = db.get(PortfolioPG, pid)
    if not p:
        raise HTTPException(404, "Portfolio not found")
    if body.name is not None:
        p.name = body.name
    if body.description is not None:
        p.description = body.description
    db.commit()
    return {"id": p.id, "name": p.name, "message": "Updated"}


@router.delete("/portfolios/{pid}", status_code=204)
def delete_portfolio(pid: str, db: Session = Depends(get_db)):
    p = db.get(PortfolioPG, pid)
    if not p:
        raise HTTPException(404, "Portfolio not found")
    db.delete(p)
    db.commit()


@router.post("/portfolios/{pid}/assets", status_code=201)
def add_asset(pid: str, body: AssetCreate, db: Session = Depends(get_db)):
    p = db.get(PortfolioPG, pid)
    if not p:
        raise HTTPException(404, "Portfolio not found")
    a = AssetPG(
        portfolio_id=pid, asset_type=body.asset_type,
        company_name=body.company_name, company_sector=body.company_sector,
        company_subsector=body.company_subsector, exposure=body.exposure,
        market_value=body.market_value or body.exposure, base_pd=body.base_pd,
        base_lgd=body.base_lgd, rating=body.rating, maturity_years=body.maturity_years,
    )
    db.add(a)
    db.commit()
    return {"id": a.id, "message": "Asset added"}


@router.delete("/portfolios/{pid}/assets/{aid}", status_code=204)
def remove_asset(pid: str, aid: str, db: Session = Depends(get_db)):
    a = db.get(AssetPG, aid)
    if not a or a.portfolio_id != pid:
        raise HTTPException(404, "Asset not found")
    db.delete(a)
    db.commit()


# ---- Seed sample data ----

@router.post("/portfolios/seed-sample")
def seed_sample_portfolio(db: Session = Depends(get_db)):
    """Create a sample portfolio in PostgreSQL."""
    existing = db.query(PortfolioPG).filter(PortfolioPG.name == "Sample Climate Risk Portfolio (PG)").first()
    if existing:
        return {"message": "Already exists", "id": existing.id}

    import random
    random.seed(42)
    companies = [
        ("MegaCoal Energy", "Power Generation", "Coal"),
        ("SolarWind Power", "Power Generation", "Renewables"),
        ("PetroGiant Inc", "Oil & Gas", "Integrated"),
        ("SteelWorks Global", "Metals & Mining", "Steel"),
        ("AutoFuture Motors", "Automotive", "ICE Vehicles"),
        ("ElectricDrive Co", "Automotive", "EV"),
        ("GlobalAir Airlines", "Airlines", "Passenger"),
        ("GreenBuildings REIT", "Real Estate", "Commercial"),
    ]
    p = PortfolioPG(name="Sample Climate Risk Portfolio (PG)",
                    description="Diversified portfolio across climate-sensitive sectors")
    db.add(p)
    db.flush()

    for name, sector, sub in companies:
        for i, atype in enumerate(["Bond", "Loan"]):
            pd_map = {"Power Generation": 0.02, "Oil & Gas": 0.025, "Metals & Mining": 0.03,
                      "Automotive": 0.02, "Airlines": 0.04, "Real Estate": 0.015}
            lgd_map = {"Bond": 0.45, "Loan": 0.40, "Equity": 0.90}
            base_pd = pd_map.get(sector, 0.02) * (0.5 if "Renewables" in sub or "EV" in sub else 1.0)
            rating = "A" if base_pd < 0.015 else ("BBB" if base_pd < 0.025 else "BB")
            exposure = round(random.uniform(1e6, 10e6), 2)
            db.add(AssetPG(
                portfolio_id=p.id, asset_type=atype,
                company_name=name, company_sector=sector, company_subsector=sub,
                exposure=exposure, market_value=exposure, base_pd=round(base_pd, 4),
                base_lgd=lgd_map.get(atype, 0.45), rating=rating, maturity_years=random.randint(3, 10),
            ))

    db.commit()
    return {"message": "Sample portfolio created", "id": p.id, "num_assets": 16}
