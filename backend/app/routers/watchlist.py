"""
Watchlist router for managing user stock watchlists.
"""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.user import User
from ..models.watchlist import Watchlist, WatchlistItem
from ..schemas.watchlist import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistListResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
)
from ..dependencies import get_current_active_user

router = APIRouter(
    prefix="/watchlists",
    tags=["Watchlists"],
)


@router.get("", response_model=WatchlistListResponse)
async def list_watchlists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all watchlists for the current user.
    """
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == current_user.id)
        .options(selectinload(Watchlist.items))
        .order_by(Watchlist.created_at.desc())
    )
    watchlists = result.scalars().all()
    
    return WatchlistListResponse(
        watchlists=[WatchlistResponse.model_validate(w) for w in watchlists],
        total=len(watchlists),
    )


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new watchlist for the current user.
    """
    new_watchlist = Watchlist(
        user_id=current_user.id,
        name=watchlist_data.name,
    )
    
    db.add(new_watchlist)
    await db.commit()
    await db.refresh(new_watchlist)
    
    return WatchlistResponse.model_validate(new_watchlist)


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific watchlist by ID.
    """
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .options(selectinload(Watchlist.items))
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )
    
    return WatchlistResponse.model_validate(watchlist)


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: UUID,
    watchlist_data: WatchlistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a watchlist's name.
    """
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .options(selectinload(Watchlist.items))
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )
    
    if watchlist_data.name is not None:
        watchlist.name = watchlist_data.name
    
    await db.commit()
    await db.refresh(watchlist)
    
    return WatchlistResponse.model_validate(watchlist)


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a watchlist and all its items.
    """
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )
    
    await db.delete(watchlist)
    await db.commit()
    
    return None


# ============ Watchlist Items Endpoints ============


@router.post("/{watchlist_id}/stocks", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_stock_to_watchlist(
    watchlist_id: UUID,
    item_data: WatchlistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a stock to a watchlist.
    """
    # Verify watchlist ownership
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )
    
    # Check if stock already exists in watchlist
    result = await db.execute(
        select(WatchlistItem)
        .where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.ticker == item_data.ticker.upper()
        )
    )
    existing_item = result.scalar_one_or_none()
    
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock {item_data.ticker.upper()} already exists in this watchlist",
        )
    
    # Create new item
    new_item = WatchlistItem(
        watchlist_id=watchlist_id,
        ticker=item_data.ticker.upper(),
        target_price=item_data.target_price,
        notes=item_data.notes,
    )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    return WatchlistItemResponse.model_validate(new_item)


@router.put("/{watchlist_id}/stocks/{ticker}", response_model=WatchlistItemResponse)
async def update_stock_in_watchlist(
    watchlist_id: UUID,
    ticker: str,
    item_data: WatchlistItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a stock in a watchlist.
    """
    # Verify watchlist ownership
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )
    
    # Get the item
    result = await db.execute(
        select(WatchlistItem)
        .where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.ticker == ticker.upper()
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {ticker.upper()} not found in this watchlist",
        )
    
    # Update fields
    if item_data.target_price is not None:
        item.target_price = item_data.target_price
    if item_data.notes is not None:
        item.notes = item_data.notes
    
    await db.commit()
    await db.refresh(item)
    
    return WatchlistItemResponse.model_validate(item)


@router.delete("/{watchlist_id}/stocks/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_stock_from_watchlist(
    watchlist_id: UUID,
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Remove a stock from a watchlist.
    """
    # Verify watchlist ownership
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )
    
    # Get the item
    result = await db.execute(
        select(WatchlistItem)
        .where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.ticker == ticker.upper()
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {ticker.upper()} not found in this watchlist",
        )
    
    await db.delete(item)
    await db.commit()
    
    return None
