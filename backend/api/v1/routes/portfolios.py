"""Portfolio routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.v1.deps import get_db, PaginationParams
from api.v1.repositories import PortfolioRepository
from api.v1.schemas import (
    PortfolioCreate, PortfolioUpdate, PortfolioSummary, PortfolioDetail,
    HoldingCreate, HoldingResponse, PaginatedResponse, MessageResponse
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=PaginatedResponse)
def list_portfolios(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    List all portfolios with pagination.
    
    Returns paginated list of portfolios with basic metrics.
    """
    repo = PortfolioRepository(db)
    portfolios, total = repo.get_all(
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    items = []
    for portfolio in portfolios:
        metrics = repo.get_portfolio_metrics(portfolio.id)
        items.append(PortfolioSummary(
            id=portfolio.id,
            name=portfolio.name,
            description=portfolio.description,
            num_holdings=metrics["num_holdings"],
            total_exposure=metrics["total_exposure"],
            created_at=portfolio.created_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size
    )


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """
    Get portfolio details by ID.
    
    Returns portfolio information with calculated metrics.
    """
    repo = PortfolioRepository(db)
    portfolio = repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    metrics = repo.get_portfolio_metrics(portfolio_id)
    
    return PortfolioDetail(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        metrics=metrics
    )


@router.post("", response_model=PortfolioDetail, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new portfolio.
    
    Returns the created portfolio.
    """
    repo = PortfolioRepository(db)
    portfolio = repo.create(
        name=portfolio_data.name,
        description=portfolio_data.description
    )
    
    return PortfolioDetail(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        metrics={"num_holdings": 0, "total_exposure": 0}
    )


@router.patch("/{portfolio_id}", response_model=PortfolioDetail)
def update_portfolio(
    portfolio_id: str,
    portfolio_data: PortfolioUpdate,
    db: Session = Depends(get_db)
):
    """
    Update portfolio information.
    
    Only provided fields will be updated.
    """
    repo = PortfolioRepository(db)
    
    # Convert to dict and remove None values
    update_data = portfolio_data.model_dump(exclude_unset=True)
    
    portfolio = repo.update(portfolio_id, update_data)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    metrics = repo.get_portfolio_metrics(portfolio_id)
    
    return PortfolioDetail(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        metrics=metrics
    )


@router.delete("/{portfolio_id}", response_model=MessageResponse)
def delete_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a portfolio.
    
    This will cascade delete all holdings and associated analysis runs.
    """
    repo = PortfolioRepository(db)
    
    success = repo.delete(portfolio_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    return MessageResponse(
        message="Portfolio deleted successfully",
        detail={"portfolio_id": portfolio_id}
    )


@router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
def list_holdings(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all holdings for a portfolio.
    
    Returns list of assets/holdings with their details.
    """
    repo = PortfolioRepository(db)
    
    # Verify portfolio exists
    portfolio = repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    holdings = repo.get_holdings(portfolio_id)
    
    return [
        HoldingResponse(
            id=h.id,
            portfolio_id=h.portfolio_id,
            asset_type=h.asset_type.value,
            company_name=h.company_name,
            company_sector=h.company_sector.value,
            company_subsector=h.company_subsector,
            exposure=h.exposure,
            market_value=h.market_value,
            base_pd=h.base_pd,
            base_lgd=h.base_lgd,
            rating=h.rating,
            maturity_years=h.maturity_years
        )
        for h in holdings
    ]


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def add_holding(
    portfolio_id: str,
    holding_data: HoldingCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new holding to the portfolio.
    
    Returns the created holding.
    """
    repo = PortfolioRepository(db)
    
    # Verify portfolio exists
    portfolio = repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Convert enum values to their string representation
    holding_dict = holding_data.model_dump()
    
    holding = repo.add_holding(portfolio_id, holding_dict)
    
    return HoldingResponse(
        id=holding.id,
        portfolio_id=holding.portfolio_id,
        asset_type=holding.asset_type.value,
        company_name=holding.company_name,
        company_sector=holding.company_sector.value,
        company_subsector=holding.company_subsector,
        exposure=holding.exposure,
        market_value=holding.market_value,
        base_pd=holding.base_pd,
        base_lgd=holding.base_lgd,
        rating=holding.rating,
        maturity_years=holding.maturity_years
    )
