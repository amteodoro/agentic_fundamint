"""
Pydantic schemas for watchlist endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class WatchlistItemCreate(BaseModel):
    """Schema for adding a stock to a watchlist."""
    ticker: str = Field(..., max_length=20, description="Stock ticker symbol")
    target_price: Optional[Decimal] = Field(None, ge=0, description="Target price for alerts")
    notes: Optional[str] = Field(None, description="Notes about this stock")


class WatchlistItemUpdate(BaseModel):
    """Schema for updating a watchlist item."""
    target_price: Optional[Decimal] = Field(None, ge=0, description="Target price for alerts")
    notes: Optional[str] = Field(None, description="Notes about this stock")


class WatchlistItemResponse(BaseModel):
    """Schema for watchlist item data in responses."""
    id: UUID
    ticker: str
    added_at: datetime
    target_price: Optional[Decimal]
    notes: Optional[str]

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    """Schema for creating a new watchlist."""
    name: str = Field(..., max_length=255, description="Watchlist name")


class WatchlistUpdate(BaseModel):
    """Schema for updating a watchlist."""
    name: Optional[str] = Field(None, max_length=255, description="Watchlist name")


class WatchlistResponse(BaseModel):
    """Schema for watchlist data in responses."""
    id: UUID
    name: str
    created_at: datetime
    items: List[WatchlistItemResponse] = []

    class Config:
        from_attributes = True


class WatchlistListResponse(BaseModel):
    """Schema for list of watchlists."""
    watchlists: List[WatchlistResponse]
    total: int
