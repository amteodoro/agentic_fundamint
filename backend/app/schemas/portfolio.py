"""
Pydantic schemas for portfolio endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class HoldingCreate(BaseModel):
    """Schema for adding a stock to a portfolio."""
    ticker: str = Field(..., max_length=20, description="Stock ticker symbol")
    shares: Optional[Decimal] = Field(None, ge=0, description="Number of shares")
    average_cost: Optional[Decimal] = Field(None, ge=0, description="Average cost per share")
    notes: Optional[str] = Field(None, description="Notes about this position")


class HoldingUpdate(BaseModel):
    """Schema for updating a portfolio holding."""
    shares: Optional[Decimal] = Field(None, ge=0, description="Number of shares")
    average_cost: Optional[Decimal] = Field(None, ge=0, description="Average cost per share")
    notes: Optional[str] = Field(None, description="Notes about this position")


class HoldingResponse(BaseModel):
    """Schema for holding data in responses."""
    id: UUID
    ticker: str
    shares: Optional[Decimal]
    average_cost: Optional[Decimal]
    added_at: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True


class PortfolioCreate(BaseModel):
    """Schema for creating a new portfolio."""
    name: str = Field(..., max_length=255, description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = Field(None, max_length=255, description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")


class PortfolioResponse(BaseModel):
    """Schema for portfolio data in responses."""
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    holdings: List[HoldingResponse] = []

    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """Schema for list of portfolios."""
    portfolios: List[PortfolioResponse]
    total: int
