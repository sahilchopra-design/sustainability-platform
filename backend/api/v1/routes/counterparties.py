"""Counterparty routes"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.v1.deps import get_db, PaginationParams
from api.v1.repositories import PortfolioRepository
from api.v1.schemas import (
    CounterpartyCreate, CounterpartyUpdate, CounterpartyResponse,
    PaginatedResponse, MessageResponse
)

router = APIRouter(prefix="/counterparties", tags=["counterparties"])


@router.get("", response_model=PaginatedResponse)
def list_counterparties(
    search: Optional[str] = Query(None, description="Search by name"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    List all counterparties with optional search.
    
    Search is performed on counterparty name (case-insensitive).
    """
    repo = PortfolioRepository(db)
    
    # Note: Reusing Portfolio repository as counterparties share same structure
    # In a real implementation, you might have a separate Counterparty model
    counterparties, total = repo.get_all(
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    # Apply search filter if provided
    if search:
        counterparties = [
            c for c in counterparties
            if search.lower() in c.name.lower()
        ]
        total = len(counterparties)
    
    items = [
        CounterpartyResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in counterparties
    ]
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size
    )


@router.get("/{counterparty_id}", response_model=CounterpartyResponse)
def get_counterparty(
    counterparty_id: str,
    db: Session = Depends(get_db)
):
    """
    Get counterparty details by ID.
    """
    repo = PortfolioRepository(db)
    counterparty = repo.get_by_id(counterparty_id)
    
    if not counterparty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Counterparty {counterparty_id} not found"
        )
    
    return CounterpartyResponse(
        id=counterparty.id,
        name=counterparty.name,
        description=counterparty.description,
        created_at=counterparty.created_at,
        updated_at=counterparty.updated_at
    )


@router.post("", response_model=CounterpartyResponse, status_code=status.HTTP_201_CREATED)
def create_counterparty(
    counterparty_data: CounterpartyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new counterparty.
    """
    repo = PortfolioRepository(db)
    counterparty = repo.create(
        name=counterparty_data.name,
        description=counterparty_data.description
    )
    
    return CounterpartyResponse(
        id=counterparty.id,
        name=counterparty.name,
        description=counterparty.description,
        created_at=counterparty.created_at,
        updated_at=counterparty.updated_at
    )


@router.patch("/{counterparty_id}", response_model=CounterpartyResponse)
def update_counterparty(
    counterparty_id: str,
    counterparty_data: CounterpartyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update counterparty information.
    """
    repo = PortfolioRepository(db)
    update_data = counterparty_data.model_dump(exclude_unset=True)
    
    counterparty = repo.update(counterparty_id, update_data)
    
    if not counterparty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Counterparty {counterparty_id} not found"
        )
    
    return CounterpartyResponse(
        id=counterparty.id,
        name=counterparty.name,
        description=counterparty.description,
        created_at=counterparty.created_at,
        updated_at=counterparty.updated_at
    )


@router.delete("/{counterparty_id}", response_model=MessageResponse)
def delete_counterparty(
    counterparty_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a counterparty.
    """
    repo = PortfolioRepository(db)
    success = repo.delete(counterparty_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Counterparty {counterparty_id} not found"
        )
    
    return MessageResponse(
        message="Counterparty deleted successfully",
        detail={"counterparty_id": counterparty_id}
    )
