"""
Portfolio router for managing user investment portfolios.
"""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.user import User
from ..models.portfolio import Portfolio, PortfolioHolding
from ..schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    HoldingCreate,
    HoldingUpdate,
    HoldingResponse,
)
from ..dependencies import get_current_active_user

router = APIRouter(
    prefix="/portfolios",
    tags=["Portfolios"],
)


@router.get("", response_model=PortfolioListResponse)
async def list_portfolios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all portfolios for the current user.
    """
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
        .options(selectinload(Portfolio.holdings))
        .order_by(Portfolio.created_at.desc())
    )
    portfolios = result.scalars().all()
    
    return PortfolioListResponse(
        portfolios=[PortfolioResponse.model_validate(p) for p in portfolios],
        total=len(portfolios),
    )


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new portfolio for the current user.
    """
    new_portfolio = Portfolio(
        user_id=current_user.id,
        name=portfolio_data.name,
        description=portfolio_data.description,
    )
    
    db.add(new_portfolio)
    await db.commit()
    await db.refresh(new_portfolio)
    
    return PortfolioResponse.model_validate(new_portfolio)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific portfolio by ID.
    """
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
        .options(selectinload(Portfolio.holdings))
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    return PortfolioResponse.model_validate(portfolio)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    portfolio_data: PortfolioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a portfolio's name and/or description.
    """
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
        .options(selectinload(Portfolio.holdings))
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    if portfolio_data.name is not None:
        portfolio.name = portfolio_data.name
    if portfolio_data.description is not None:
        portfolio.description = portfolio_data.description
    
    await db.commit()
    await db.refresh(portfolio)
    
    return PortfolioResponse.model_validate(portfolio)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a portfolio and all its holdings.
    """
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    await db.delete(portfolio)
    await db.commit()
    
    return None


# ============ Portfolio Holdings Endpoints ============


@router.post("/{portfolio_id}/stocks", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def add_stock_to_portfolio(
    portfolio_id: UUID,
    holding_data: HoldingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a stock to a portfolio.
    """
    # Verify portfolio ownership
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    # Check if stock already exists in portfolio
    result = await db.execute(
        select(PortfolioHolding)
        .where(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.ticker == holding_data.ticker.upper()
        )
    )
    existing_holding = result.scalar_one_or_none()
    
    if existing_holding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock {holding_data.ticker.upper()} already exists in this portfolio",
        )
    
    # Create new holding
    new_holding = PortfolioHolding(
        portfolio_id=portfolio_id,
        ticker=holding_data.ticker.upper(),
        shares=holding_data.shares,
        average_cost=holding_data.average_cost,
        notes=holding_data.notes,
    )
    
    db.add(new_holding)
    await db.commit()
    await db.refresh(new_holding)
    
    return HoldingResponse.model_validate(new_holding)


@router.put("/{portfolio_id}/stocks/{ticker}", response_model=HoldingResponse)
async def update_stock_in_portfolio(
    portfolio_id: UUID,
    ticker: str,
    holding_data: HoldingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a stock holding in a portfolio.
    """
    # Verify portfolio ownership
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    # Get the holding
    result = await db.execute(
        select(PortfolioHolding)
        .where(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.ticker == ticker.upper()
        )
    )
    holding = result.scalar_one_or_none()
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {ticker.upper()} not found in this portfolio",
        )
    
    # Update fields
    if holding_data.shares is not None:
        holding.shares = holding_data.shares
    if holding_data.average_cost is not None:
        holding.average_cost = holding_data.average_cost
    if holding_data.notes is not None:
        holding.notes = holding_data.notes
    
    await db.commit()
    await db.refresh(holding)
    
    return HoldingResponse.model_validate(holding)


@router.delete("/{portfolio_id}/stocks/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_stock_from_portfolio(
    portfolio_id: UUID,
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Remove a stock from a portfolio.
    """
    # Verify portfolio ownership
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )
    
    # Get the holding
    result = await db.execute(
        select(PortfolioHolding)
        .where(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.ticker == ticker.upper()
        )
    )
    holding = result.scalar_one_or_none()
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {ticker.upper()} not found in this portfolio",
        )
    
    await db.delete(holding)
    await db.commit()
    
    return None
